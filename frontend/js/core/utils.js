/* Small dependency-free helpers shared by every page. */

// ---------------------------------------------------------------- safe HTML
// `html` is a tagged template that HTML-escapes every interpolated value unless
// it is already marked safe (nested html`` results). Use it for ALL dynamic markup.
class SafeHtml {
  constructor(value) {
    this.value = value;
  }
  toString() {
    return this.value;
  }
}

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
export const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ESCAPES[c]);

function renderValue(value) {
  if (value === null || value === undefined) return "";
  // Booleans render as "true"/"false" so ARIA attributes (aria-pressed="${flag}") work.
  // Use a ternary (cond ? html`..` : "") for conditional markup - never `cond && html`..``.
  if (typeof value === "boolean") return String(value);
  if (value instanceof SafeHtml) return value.value;
  if (Array.isArray(value)) return value.map(renderValue).join("");
  return escapeHtml(value);
}

export function html(strings, ...values) {
  let out = strings[0];
  for (let i = 0; i < values.length; i += 1) out += renderValue(values[i]) + strings[i + 1];
  return new SafeHtml(out);
}
/** Mark a string as already-safe HTML (only for output of our own sanitising renderers). */
export const raw = (value) => new SafeHtml(String(value ?? ""));
/** Render a safe template into an element. */
export function render(el, safe) {
  el.innerHTML = safe instanceof SafeHtml ? safe.value : escapeHtml(safe);
  return el;
}

// --------------------------------------------------------------------- DOM
export const $ = (selector, root = document) => root.querySelector(selector);
export const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

// -------------------------------------------------------------------- misc
export const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
export const clamp = (n, min, max) => Math.min(max, Math.max(min, n));

export function debounce(fn, wait = 200) {
  let timer;
  const wrapped = (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
  wrapped.cancel = () => clearTimeout(timer);
  return wrapped;
}

export function shuffled(list) {
  const copy = [...list];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;

export function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes < 0) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(bytes < 10240 ? 1 : 0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const dateFmt = new Intl.DateTimeFormat(undefined, { year: "numeric", month: "short", day: "numeric" });
const dateTimeFmt = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
export const formatDate = (value) => (value ? dateFmt.format(new Date(value)) : "—");
export const formatDateTime = (value) => (value ? dateTimeFmt.format(new Date(value)) : "—");

export function timeAgo(value) {
  if (!value) return "";
  const seconds = Math.round((Date.now() - new Date(value).getTime()) / 1000);
  if (seconds < 45) return "just now";
  const units = [
    [60, "minute"],
    [3600, "hour"],
    [86400, "day"],
    [604800, "week"],
  ];
  if (seconds < 3600) return `${Math.round(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)} h ago`;
  if (seconds < 604800 * 2) return `${Math.round(seconds / 86400)} d ago`;
  void units;
  return formatDate(value);
}

export function readingTime(text) {
  const words = String(text || "").trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / 200));
}

export function greeting(date = new Date()) {
  const h = date.getHours();
  if (h < 5) return "Burning the midnight oil";
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

export function initials(name) {
  const parts = String(name || "").trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  return (parts[0][0] + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase();
}

export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback for insecure contexts / older Safari.
    const area = el("textarea", { "aria-hidden": "true", style: "position:fixed;opacity:0;top:0;left:0" });
    area.value = text;
    document.body.append(area);
    area.select();
    let ok = false;
    try {
      ok = document.execCommand("copy");
    } catch {
      ok = false;
    }
    area.remove();
    return ok;
  }
}

export function downloadFile(filename, content, type = "text/markdown;charset=utf-8") {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = el("a", { href: url, download: filename.replace(/[\\/:*?"<>|]+/g, "_") });
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function slugify(text) {
  return String(text || "file").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || "file";
}

export function fileExtension(name) {
  const m = /\.([a-z0-9]+)$/i.exec(name || "");
  return m ? m[1].toLowerCase() : "";
}

/** Read a query-string parameter. */
export const queryParam = (name) => new URLSearchParams(location.search).get(name);

/** Only same-site relative paths are allowed as post-login redirects (no open redirect). */
export function safeNext(value, fallback = "dashboard.html") {
  if (!value) return fallback;
  return /^[a-z0-9_-]+\.html(\?[\w=&.%-]*)?$/i.test(value) ? value : fallback;
}
