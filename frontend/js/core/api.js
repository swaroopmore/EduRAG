/* API client: one place for base URL, auth header, errors, uploads and streaming. */
import { API_URL } from "../config.js";

const TOKEN_KEY = "access_token"; // same key the previous frontend used, so existing sessions survive

export const token = {
  get() {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(value) {
    try {
      localStorage.setItem(TOKEN_KEY, value);
    } catch {
      /* storage unavailable: the session lasts until the page closes */
      memoryToken = value;
    }
  },
  clear() {
    memoryToken = null;
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* ignore */
    }
  },
};
let memoryToken = null;
const currentToken = () => token.get() || memoryToken;

export class ApiError extends Error {
  constructor(message, { status = 0, code = "error", requestId = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

const NETWORK_MESSAGE = "We couldn't reach the server. Check your connection and try again.";

/** Called when the API says the session is no longer valid. Set by auth.js. */
let onUnauthorized = () => {};
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn;
};

async function toApiError(response) {
  let body = null;
  try {
    body = await response.json();
  } catch {
    /* non-JSON error body */
  }
  let message = typeof body?.detail === "string" ? body.detail : "";
  if (!message) {
    message =
      response.status === 404 ? "We couldn't find that." :
      response.status === 413 ? "That file is too large." :
      response.status === 429 ? "You're doing that too quickly. Please wait a moment." :
      response.status >= 500 ? "Something went wrong on our side. Please try again." :
      "The request couldn't be completed.";
  }
  return new ApiError(message, { status: response.status, code: body?.code || "error", requestId: body?.request_id || null });
}

function buildUrl(path, query) {
  const url = new URL(API_URL + path);
  for (const [key, value] of Object.entries(query || {})) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
  }
  return url.toString();
}

export async function request(method, path, { json, query, signal, auth = true, timeoutMs = 60000, parse = "json" } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new DOMException("timeout", "TimeoutError")), timeoutMs);
  if (signal) {
    if (signal.aborted) controller.abort(signal.reason);
    else signal.addEventListener("abort", () => controller.abort(signal.reason), { once: true });
  }

  const headers = { Accept: "application/json" };
  if (json !== undefined) headers["Content-Type"] = "application/json";
  if (auth && currentToken()) headers.Authorization = `Bearer ${currentToken()}`;

  let response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      headers,
      body: json !== undefined ? JSON.stringify(json) : undefined,
      signal: controller.signal,
    });
  } catch (error) {
    if (signal?.aborted) throw error; // caller cancelled on purpose
    if (error?.name === "TimeoutError" || controller.signal.reason?.name === "TimeoutError") {
      throw new ApiError("That took too long. Please try again.", { code: "timeout" });
    }
    throw new ApiError(NETWORK_MESSAGE, { code: "network" });
  } finally {
    clearTimeout(timer);
  }

  if (response.status === 401 && auth) {
    onUnauthorized();
    throw new ApiError("Your session has expired. Please sign in again.", { status: 401, code: "unauthorized" });
  }
  if (!response.ok) throw await toApiError(response);
  if (response.status === 204) return null;
  if (parse === "blob") return response.blob();
  try {
    return await response.json();
  } catch {
    return null;
  }
}

/** Upload with progress events (fetch cannot report upload progress). */
export function upload(path, file, { onProgress, signal } = {}) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", API_URL + path);
    if (currentToken()) xhr.setRequestHeader("Authorization", `Bearer ${currentToken()}`);
    xhr.setRequestHeader("Accept", "application/json");
    xhr.timeout = 10 * 60 * 1000;

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) onProgress(Math.round((event.loaded / event.total) * 100));
    };
    xhr.onerror = () => reject(new ApiError(NETWORK_MESSAGE, { code: "network" }));
    xhr.ontimeout = () => reject(new ApiError("The upload took too long. Please try again.", { code: "timeout" }));
    xhr.onabort = () => reject(new DOMException("Aborted", "AbortError"));
    xhr.onload = () => {
      let body = null;
      try {
        body = JSON.parse(xhr.responseText);
      } catch {
        /* ignore */
      }
      if (xhr.status === 401) {
        onUnauthorized();
        return reject(new ApiError("Your session has expired. Please sign in again.", { status: 401, code: "unauthorized" }));
      }
      if (xhr.status >= 200 && xhr.status < 300) return resolve(body);
      const message = typeof body?.detail === "string" ? body.detail : "The upload couldn't be completed.";
      reject(new ApiError(message, { status: xhr.status, code: body?.code || "error" }));
    };
    if (signal) signal.addEventListener("abort", () => xhr.abort(), { once: true });

    const form = new FormData();
    form.append("file", file, file.name);
    xhr.send(form);
  });
}

/**
 * POST and read a text/event-stream response. `onEvent(name, data)` fires for each SSE event.
 * Resolves when the stream ends.
 */
export async function stream(path, json, { onEvent, signal } = {}) {
  let response;
  try {
    response = await fetch(buildUrl(path), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream", Authorization: `Bearer ${currentToken()}` },
      body: JSON.stringify(json),
      signal,
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError(NETWORK_MESSAGE, { code: "network" });
  }
  if (response.status === 401) {
    onUnauthorized();
    throw new ApiError("Your session has expired. Please sign in again.", { status: 401, code: "unauthorized" });
  }
  if (!response.ok) throw await toApiError(response);
  if (!response.body) throw new ApiError("Streaming isn't supported by this browser.", { code: "no_stream" });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const dispatch = (frame) => {
    let name = "message";
    const data = [];
    for (const line of frame.split("\n")) {
      if (line.startsWith("event:")) name = line.slice(6).trim();
      else if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /, ""));
    }
    if (!data.length) return;
    try {
      onEvent?.(name, JSON.parse(data.join("\n")));
    } catch {
      /* ignore malformed frame */
    }
  };
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    let index;
    while ((index = buffer.indexOf("\n\n")) !== -1) {
      dispatch(buffer.slice(0, index));
      buffer = buffer.slice(index + 2);
    }
  }
  if (buffer.trim()) dispatch(buffer);
}

const GENERATION_TIMEOUT = 180000;

export const Api = {
  // auth
  login: (email, password) => request("POST", "/auth/login", { json: { email, password }, auth: false }),
  register: (full_name, email, password) => request("POST", "/auth/register", { json: { full_name, email, password }, auth: false }),
  me: () => request("GET", "/auth/me"),
  updateMe: (full_name) => request("PATCH", "/auth/me", { json: { full_name } }),
  changePassword: (current_password, new_password) => request("POST", "/auth/change-password", { json: { current_password, new_password } }),

  // subjects
  subjects: () => request("GET", "/subjects"),
  createSubject: (name, description) => request("POST", "/subjects", { json: { name, description: description || null } }),
  updateSubject: (id, name, description) => request("PUT", `/subjects/${id}`, { json: { name, description: description || null } }),
  deleteSubject: (id) => request("DELETE", `/subjects/${id}`),

  // documents
  documents: (subjectId) => request("GET", subjectId ? `/documents/${subjectId}` : "/documents"),
  document: (id) => request("GET", `/documents/${id}/status`),
  uploadDocument: (subjectId, file, opts) => upload(`/documents/upload/${subjectId}`, file, opts),
  reindexDocument: (id) => request("POST", `/documents/${id}/reindex`),
  deleteDocument: (id) => request("DELETE", `/documents/${id}`),
  documentFile: (id) => request("GET", `/documents/${id}/file`, { parse: "blob", timeoutMs: 120000 }),

  // chat
  ask: (body, opts) => request("POST", "/chat/ask", { json: body, timeoutMs: GENERATION_TIMEOUT, ...opts }),
  askStream: (body, opts) => stream("/chat/stream", body, opts),
  history: (subjectId, limit = 100) => request("GET", `/chat/history/${subjectId}`, { query: { limit } }),
  clearHistory: (subjectId) => request("DELETE", `/chat/history/${subjectId}`),

  // generated study material
  notes: (id) => request("GET", `/notes/${id}`),
  generateNotes: (id) => request("POST", `/notes/generate/${id}`, { timeoutMs: GENERATION_TIMEOUT }),
  flashcards: (id) => request("GET", `/flashcards/${id}`),
  generateFlashcards: (id) => request("POST", `/flashcards/generate/${id}`, { timeoutMs: GENERATION_TIMEOUT }),
  setMastered: (cardId, mastered) => request("PATCH", `/flashcards/item/${cardId}`, { json: { mastered } }),
  quiz: (id) => request("GET", `/quiz/${id}`),
  generateQuiz: (id) => request("POST", `/quiz/generate/${id}`, { timeoutMs: GENERATION_TIMEOUT }),
  submitQuiz: (id, answers) => request("POST", `/quiz/${id}/attempts`, { json: { answers } }),
  quizAttempts: (id) => request("GET", `/quiz/${id}/attempts`),
  plan: (id) => request("GET", `/study-plans/${id}`),
  generatePlan: (id, days) => request("POST", `/study-plans/generate/${id}`, { query: { days }, timeoutMs: GENERATION_TIMEOUT }),
  setSessionDone: (planId, completed) => request("PATCH", `/study-plans/item/${planId}`, { json: { completed } }),

  dashboard: () => request("GET", "/dashboard"),
  health: () => request("GET", "/health", { auth: false, timeoutMs: 15000 }),
};
