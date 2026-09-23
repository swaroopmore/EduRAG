import { Api, ApiError } from "../core/api.js";
import { LIMITS } from "../config.js";
import { mountShell } from "../core/shell.js";
import { renderMarkdown } from "../core/markdown.js";
import { $, $$, html, raw, render, copyText, queryParam, plural, timeAgo, el } from "../core/utils.js";
import { confirmDialog, errorState, noDocumentsState, noSubjectState, onAction, toast } from "../core/ui.js";

const shell = await mountShell({ page: "chat", title: "AI Chat", subjects: "required", fillHeight: true });
const root = $("#chat");

const state = {
  subject: shell.subject,
  docs: [],
  readyDocs: [],
  scope: queryParam("document") || "all",
  exchanges: [], // {id, question, answer, citations, grounded, cached, status: done|streaming|error, error, openRef, at}
  busy: false,
  abort: null,
};

const SUGGESTIONS = (docs) => {
  const list = ["Summarize the key ideas in my material", "What are the most important terms I should know?", "Explain the main concept as if I'm a beginner"];
  if (docs[0]) list.unshift(`Give me a short summary of ${docs[0].original_filename}`);
  return list.slice(0, 4);
};

// ------------------------------------------------------------------ templates
const answerHtml = (ex) => raw(renderMarkdown(ex.answer, { citations: ex.citations.map((c) => c.ref) }));

function sourcesBlock(ex, index) {
  if (!ex.citations.length) return "";
  const open = ex.citations.find((c) => c.ref === ex.openRef);
  return html`<div class="sources"><span class="xs strong faint">Sources</span>
    <div class="chips">${ex.citations.map((c) => html`<button type="button" class="chip source-chip" data-action="source" data-ex="${index}" data-ref="${c.ref}" aria-expanded="${c.ref === ex.openRef}" id="source-${index}-${c.ref}">
      <b>${c.ref}</b><span class="truncate" style="max-width:190px">${c.document || "Document"}${c.page ? ` · ${c.unit === "slide" ? "slide" : "p."} ${c.page}` : ""}</span></button>`)}</div>
    ${open ? html`<blockquote class="source-detail">${open.snippet || "No preview available."}</blockquote>` : ""}
  </div>`;
}

function exchangeHtml(ex, index) {
  const last = index === state.exchanges.length - 1;
  let body;
  if (ex.status === "error") {
    body = html`<div class="alert alert-danger" role="alert"><i class="bi bi-exclamation-octagon-fill" aria-hidden="true"></i><div class="alert-body"><strong>That didn't work</strong>${ex.error}</div>
      <button type="button" class="btn btn-sm" data-action="retry-ex" data-ex="${index}"><i class="bi bi-arrow-clockwise" aria-hidden="true"></i>Retry</button></div>`;
  } else if (ex.status === "streaming" && !ex.answer) {
    body = html`<div class="typing" role="status" aria-label="EduRAG is thinking"><span></span><span></span><span></span></div>`;
  } else {
    body = html`<div class="prose ai-answer ${ex.grounded === false ? "not-found" : ""}" data-answer="${index}">${answerHtml(ex)}</div>`;
  }
  const done = ex.status === "done";
  return html`<div class="msg msg-user"><div class="bubble">${ex.question}</div></div>
    <div class="msg msg-ai" data-msg="${index}">
      <span class="ai-avatar" aria-hidden="true"><i class="bi bi-stars"></i></span>
      <div class="ai-body">
        ${body}
        ${done && ex.grounded === false ? html`<p class="xs faint" style="margin-top:var(--sp-2)"><i class="bi bi-info-circle" aria-hidden="true"></i> Not found in your documents. Try rephrasing, pick a different document, or upload material that covers it.</p>` : ""}
        ${done ? sourcesBlock(ex, index) : ""}
        ${done ? html`<div class="msg-actions">
          <button type="button" class="btn btn-sm btn-ghost" data-action="copy" data-ex="${index}"><i class="bi bi-clipboard" aria-hidden="true"></i>Copy</button>
          ${last ? html`<button type="button" class="btn btn-sm btn-ghost" data-action="regenerate" data-ex="${index}" ${state.busy ? "disabled" : ""}><i class="bi bi-arrow-repeat" aria-hidden="true"></i>Regenerate</button>` : ""}
          ${ex.cached ? html`<span class="badge"><i class="bi bi-lightning-charge" aria-hidden="true"></i>Saved answer</span>` : ""}
          ${ex.at ? html`<span class="xs faint">${timeAgo(ex.at)}</span>` : ""}
        </div>` : ""}
      </div>
    </div>`;
}

function welcome() {
  return html`<div class="chat-welcome">
    <span class="ai-avatar big" aria-hidden="true"><i class="bi bi-stars"></i></span>
    <h2>Ask anything about ${state.subject.name}</h2>
    <p class="muted">Answers come only from your uploaded documents, with sources you can check.</p>
    <div class="suggestions">${SUGGESTIONS(state.readyDocs).map((s) => html`<button type="button" class="chip suggestion" data-action="suggest" data-text="${s}"><i class="bi bi-lightbulb" aria-hidden="true"></i>${s}</button>`)}</div>
  </div>`;
}

function shellHtml() {
  return html`<div class="chat-toolbar">
      <div class="row" style="min-width:0"><label class="xs strong muted nowrap" for="scope">Search in</label>
        <select class="select" id="scope" style="min-width:0;max-width:340px"><option value="all">All documents (${state.readyDocs.length})</option>${state.readyDocs.map((d) => html`<option value="${d.id}" ${d.id === state.scope ? "selected" : ""}>${d.original_filename}</option>`)}</select></div>
      <span class="spacer"></span>
      <button type="button" class="btn btn-sm btn-ghost" data-action="clear" aria-label="Clear chat" ${state.exchanges.length ? "" : "disabled"}><i class="bi bi-trash3" aria-hidden="true"></i><span class="hide-xs">Clear chat</span></button>
    </div>
    <div class="chat-scroll" id="scroll" tabindex="0" role="log" aria-label="Conversation" aria-live="polite">
      <div class="chat-inner" id="thread">${state.exchanges.length ? state.exchanges.map(exchangeHtml) : welcome()}</div>
    </div>
    <button type="button" class="btn btn-sm to-latest" id="to-latest" data-action="latest" hidden><i class="bi bi-arrow-down" aria-hidden="true"></i>Latest</button>
    <form class="composer" id="composer" novalidate>
      <label for="question" class="sr-only">Your question</label>
      <textarea id="question" class="composer-input" rows="1" maxlength="${LIMITS.maxQuestionChars}" placeholder="Ask a question about your documents…" enterkeyhint="send"></textarea>
      <span class="composer-count xs faint" id="count" hidden></span>
      <button type="submit" class="btn btn-primary btn-icon send-btn" id="send" aria-label="Send question"><i class="bi bi-arrow-up" aria-hidden="true"></i></button>
    </form>
    <p class="xs faint center composer-note">AI can make mistakes. Check the sources for anything important.</p>`;
}

// -------------------------------------------------------------------- render
function drawAll({ keepDraft = true } = {}) {
  const draft = keepDraft ? $("#question")?.value || "" : "";
  render(root, shellHtml());
  const input = $("#question");
  input.value = draft;
  autosize();
  syncComposer();
  scrollToBottom(true);
}

function drawThread() {
  $("#thread").innerHTML = (state.exchanges.length ? state.exchanges.map(exchangeHtml) : welcome()).toString();
  $('[data-action="clear"]')?.toggleAttribute("disabled", !state.exchanges.length);
}

function nearBottom() {
  const s = $("#scroll");
  return s.scrollHeight - s.scrollTop - s.clientHeight < 120;
}
function scrollToBottom(force = false) {
  const s = $("#scroll");
  if (!s) return;
  if (force || nearBottom()) s.scrollTop = s.scrollHeight;
}

function autosize() {
  const t = $("#question");
  t.style.height = "auto";
  t.style.height = `${Math.min(t.scrollHeight, 168)}px`;
  const count = $("#count");
  const len = t.value.length;
  count.hidden = len < LIMITS.maxQuestionChars * 0.8;
  count.textContent = `${len}/${LIMITS.maxQuestionChars}`;
}

function syncComposer() {
  const send = $("#send");
  const input = $("#question");
  const hasDocs = state.readyDocs.length > 0;
  input.disabled = !hasDocs;
  if (!hasDocs) input.placeholder = "Upload and process a document to start chatting";
  if (state.busy) {
    send.className = "btn btn-danger btn-icon send-btn";
    send.innerHTML = '<i class="bi bi-stop-fill" aria-hidden="true"></i>';
    send.setAttribute("aria-label", "Stop generating");
    send.dataset.mode = "stop";
  } else {
    send.className = "btn btn-primary btn-icon send-btn";
    send.innerHTML = '<i class="bi bi-arrow-up" aria-hidden="true"></i>';
    send.setAttribute("aria-label", "Send question");
    send.dataset.mode = "send";
    send.disabled = !hasDocs;
  }
}

// ------------------------------------------------------------------- sending
let frame = 0;
function paintStreaming(ex, index) {
  cancelAnimationFrame(frame);
  frame = requestAnimationFrame(() => {
    const node = $(`[data-answer="${index}"]`);
    if (!node) return drawThread();
    node.innerHTML = renderMarkdown(ex.answer);
    scrollToBottom();
  });
}

async function send(question, { regenerateIndex = null } = {}) {
  if (state.busy || !state.readyDocs.length) return;
  question = question.trim();
  if (!question) return;

  let index;
  if (regenerateIndex !== null) {
    index = regenerateIndex;
    Object.assign(state.exchanges[index], { answer: "", citations: [], status: "streaming", error: null, grounded: true, cached: false });
  } else {
    state.exchanges.push({ question, answer: "", citations: [], grounded: true, cached: false, status: "streaming", error: null, openRef: null });
    index = state.exchanges.length - 1;
  }
  const ex = state.exchanges[index];
  state.busy = true;
  state.abort = new AbortController();
  drawThread();
  syncComposer();
  scrollToBottom(true);

  const body = { subject_id: state.subject.id, question, document_id: state.scope !== "all" ? state.scope : null, regenerate: regenerateIndex !== null };
  try {
    await Api.askStream(body, {
      signal: state.abort.signal,
      onEvent(name, data) {
        if (name === "token") {
          ex.answer += data.t;
          paintStreaming(ex, index);
        } else if (name === "done") {
          Object.assign(ex, { answer: data.answer, citations: data.citations || [], grounded: data.grounded !== false, cached: Boolean(data.cached), id: data.id, status: "done", at: new Date().toISOString() });
        } else if (name === "error") {
          ex.status = "error";
          ex.error = data.detail || "Something went wrong while answering.";
        }
      },
    });
    if (ex.status === "streaming") {
      // Stream closed without a terminal event.
      ex.status = ex.answer ? "done" : "error";
      ex.error = ex.answer ? null : "The connection closed before an answer arrived.";
    }
  } catch (error) {
    if (state.abort?.signal.aborted) {
      ex.status = ex.answer ? "done" : "error";
      ex.error = "Stopped. Nothing was saved for this question.";
      if (ex.answer) ex.answer += "\n\n*(stopped)*";
    } else if (error instanceof ApiError && error.code === "no_stream") {
      try {
        const data = await Api.ask(body);
        Object.assign(ex, { answer: data.answer, citations: data.citations || [], grounded: data.grounded !== false, cached: Boolean(data.cached), id: data.id, status: "done", at: new Date().toISOString() });
      } catch (fallbackError) {
        ex.status = "error";
        ex.error = fallbackError.message;
      }
    } else {
      ex.status = "error";
      ex.error = error.message || "Something went wrong.";
    }
  } finally {
    state.busy = false;
    state.abort = null;
    cancelAnimationFrame(frame);
    drawThread();
    syncComposer();
    scrollToBottom(true);
    if (window.matchMedia("(pointer: fine)").matches) $("#question")?.focus();
  }
}

// -------------------------------------------------------------------- events
root.addEventListener("submit", (event) => {
  event.preventDefault();
  if ($("#send").dataset.mode === "stop") return state.abort?.abort();
  const input = $("#question");
  const text = input.value;
  if (!text.trim()) return;
  input.value = "";
  autosize();
  send(text);
});
root.addEventListener("keydown", (event) => {
  if (event.target.id === "question" && event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    $("#composer").requestSubmit();
  }
});
root.addEventListener("input", (event) => event.target.id === "question" && autosize());
root.addEventListener("change", (event) => {
  if (event.target.id === "scope") {
    state.scope = event.target.value;
    const url = new URL(location.href);
    state.scope === "all" ? url.searchParams.delete("document") : url.searchParams.set("document", state.scope);
    history.replaceState(null, "", url);
  }
});
root.addEventListener("scroll", (event) => {
  if (event.target.id === "scroll") $("#to-latest").hidden = nearBottom();
}, true);

function openSource(index, ref) {
  const ex = state.exchanges[index];
  ex.openRef = ex.openRef === ref ? null : ref;
  const msg = $(`[data-msg="${index}"]`);
  const fresh = el("div");
  fresh.innerHTML = exchangeHtml(ex, index).toString();
  const replacement = $(".msg-ai", fresh);
  msg.replaceWith(replacement);
  $(`#source-${index}-${ref}`)?.focus();
}

onAction(root, {
  retry: () => load(),
  suggest: (b) => send(b.dataset.text),
  latest: () => scrollToBottom(true),
  source: (b) => openSource(Number(b.dataset.ex), Number(b.dataset.ref)),
  async copy(b) {
    const ex = state.exchanges[Number(b.dataset.ex)];
    toast((await copyText(ex.answer)) ? "Answer copied to clipboard." : "Couldn't copy. Select the text and copy it manually.", { type: "success", timeout: 2200 });
  },
  regenerate: (b) => {
    const i = Number(b.dataset.ex);
    send(state.exchanges[i].question, { regenerateIndex: i });
  },
  "retry-ex": (b) => {
    const i = Number(b.dataset.ex);
    send(state.exchanges[i].question, { regenerateIndex: i });
  },
  async clear() {
    const ok = await confirmDialog({
      title: "Clear this conversation?",
      message: `This deletes ${plural(state.exchanges.length, "saved question")} for “${state.subject.name}”. Your documents aren't affected.`,
      confirmLabel: "Clear chat",
      danger: true,
    });
    if (!ok) return;
    try {
      await Api.clearHistory(state.subject.id);
      state.exchanges = [];
      drawThread();
      toast.success("Conversation cleared.");
    } catch (error) {
      toast.error(error.message);
    }
  },
});
// In-text [n] chips
root.addEventListener("click", (event) => {
  const cite = event.target.closest("a.cite");
  if (!cite) return;
  event.preventDefault();
  const index = Number(cite.closest("[data-msg]")?.dataset.msg);
  if (!Number.isNaN(index)) openSource(index, Number(cite.dataset.cite));
});

// ---------------------------------------------------------------------- load
async function load() {
  state.exchanges = [];
  if (!state.subject) return render(root, noSubjectState());
  render(root, html`<div class="chat-inner" aria-hidden="true"><div class="skeleton" style="height:56px;width:60%;margin-left:auto"></div><div class="skeleton" style="height:120px;margin-top:16px"></div></div>`);
  try {
    const [docs, history] = await Promise.all([Api.documents(state.subject.id), Api.history(state.subject.id)]);
    state.docs = docs;
    state.readyDocs = docs.filter((d) => d.status === "ready");
    if (state.scope !== "all" && !state.readyDocs.some((d) => d.id === state.scope)) state.scope = "all";
    state.exchanges = history.map((h) => ({ id: h.id, question: h.question, answer: h.answer, citations: h.citations || [], grounded: true, cached: false, status: "done", at: h.created_at, openRef: null }));
    if (!state.readyDocs.length) {
      const busy = docs.filter((d) => d.status !== "failed").length;
      return render(root, html`<div class="chat-inner">${noDocumentsState(state.subject.id)}${busy ? html`<p class="center muted small" style="margin-top:var(--sp-3)">${plural(busy, "document")} still processing — check back in a moment.</p>` : ""}</div>`);
    }
    drawAll({ keepDraft: false });
  } catch (error) {
    render(root, errorState(error));
  }
}

shell.onSubjectChange((subject) => {
  state.abort?.abort();
  state.subject = subject;
  state.scope = "all";
  load();
});
await load();
const prefill = queryParam("q");
if (prefill && state.readyDocs.length) send(prefill);
