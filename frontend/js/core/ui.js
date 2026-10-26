/* Shared UI building blocks: toasts, dialogs, empty/error states, status badges. */
import { $, $$, el, html, render, escapeHtml, raw } from "./utils.js";

// ------------------------------------------------------------------- toasts
function toastRoot() {
  let root = $("#toasts");
  if (!root) {
    root = el("div", { id: "toasts", class: "toasts", "aria-live": "polite", "aria-atomic": "false" });
    document.body.append(root);
  }
  return root;
}

const TOAST_ICONS = { success: "check-circle-fill", error: "exclamation-octagon-fill", warning: "exclamation-triangle-fill", info: "info-circle-fill" };

export function toast(message, { type = "info", timeout = 4500 } = {}) {
  const node = el(
    "div",
    { class: `toast is-${type}`, role: type === "error" ? "alert" : "status" },
    el("i", { class: `bi bi-${TOAST_ICONS[type] || TOAST_ICONS.info}`, "aria-hidden": "true" }),
    el("div", { class: "grow", text: message }),
    el("button", { class: "toast-close", type: "button", "aria-label": "Dismiss", onclick: () => close() }, el("i", { class: "bi bi-x-lg", "aria-hidden": "true" }))
  );
  let closed = false;
  function close() {
    if (closed) return;
    closed = true;
    node.classList.add("is-leaving");
    setTimeout(() => node.remove(), 220);
  }
  toastRoot().append(node);
  if (timeout) setTimeout(close, timeout);
  return close;
}
toast.success = (m, o) => toast(m, { ...o, type: "success" });
toast.error = (m, o) => toast(m, { ...o, type: "error", timeout: 7000, ...o });
toast.warning = (m, o) => toast(m, { ...o, type: "warning" });

// ------------------------------------------------------------------ dialogs
const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function openDialog(build, { dismissible = true } = {}) {
  const previous = document.activeElement;
  const backdrop = el("div", { class: "modal-backdrop" });
  const dialog = el("div", { class: "modal", role: "dialog", "aria-modal": "true", tabindex: "-1" });
  backdrop.append(dialog);
  document.body.append(backdrop);
  document.body.style.overflow = "hidden";

  let resolveFn;
  const promise = new Promise((resolve) => (resolveFn = resolve));
  let done = false;
  const close = (value) => {
    if (done) return;
    done = true;
    document.removeEventListener("keydown", onKey, true);
    backdrop.remove();
    document.body.style.overflow = "";
    if (previous && previous.focus) previous.focus();
    resolveFn(value);
  };
  const onKey = (event) => {
    if (event.key === "Escape" && dismissible) {
      event.stopPropagation();
      close(undefined);
    } else if (event.key === "Tab") {
      const nodes = $$(FOCUSABLE, dialog).filter((n) => n.offsetParent !== null);
      if (!nodes.length) return;
      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  };
  document.addEventListener("keydown", onKey, true);
  backdrop.addEventListener("mousedown", (event) => {
    if (event.target === backdrop && dismissible) close(undefined);
  });

  build(dialog, close);
  const target = $("[data-autofocus]", dialog) || $(FOCUSABLE, dialog) || dialog;
  requestAnimationFrame(() => target.focus());
  return promise;
}

/** Resolves true when the user confirms. */
export function confirmDialog({ title, message, confirmLabel = "Confirm", cancelLabel = "Cancel", danger = false }) {
  return openDialog((dialog, close) => {
    const titleId = `dlg-${Math.random().toString(36).slice(2)}`;
    dialog.setAttribute("aria-labelledby", titleId);
    render(
      dialog,
      html`<h2 id="${titleId}">${title}</h2>
        <div class="modal-body">${message}</div>
        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" data-act="cancel">${cancelLabel}</button>
          <button type="button" class="btn ${danger ? "btn-danger" : "btn-primary"}" data-act="ok" data-autofocus>${confirmLabel}</button>
        </div>`
    );
    $('[data-act="cancel"]', dialog).addEventListener("click", () => close(false));
    $('[data-act="ok"]', dialog).addEventListener("click", () => close(true));
  }).then((value) => value === true);
}

/**
 * Form dialog. `onSubmit(values)` may throw to show an inline error; resolves with
 * the result of onSubmit or undefined when cancelled.
 */
export function formDialog({ title, description = "", fields, submitLabel = "Save", onSubmit }) {
  return openDialog((dialog, close) => {
    const titleId = `dlg-${Math.random().toString(36).slice(2)}`;
    dialog.setAttribute("aria-labelledby", titleId);
    render(
      dialog,
      html`<h2 id="${titleId}">${title}</h2>
        ${description ? html`<p class="modal-body" style="margin-bottom:var(--sp-4)">${description}</p>` : ""}
        <form novalidate class="stack">
          ${fields.map((f, i) => {
            const id = `${titleId}-${f.name}`;
            const control = f.type === "textarea"
              ? html`<textarea class="textarea" id="${id}" name="${f.name}" maxlength="${f.maxlength || 500}" placeholder="${f.placeholder || ""}" rows="3" ${f.required ? "required" : ""} ${i === 0 ? "data-autofocus" : ""}></textarea>`
              : html`<input class="input" id="${id}" name="${f.name}" type="${f.type || "text"}" maxlength="${f.maxlength || 200}" placeholder="${f.placeholder || ""}" autocomplete="off" ${f.required ? "required" : ""} ${i === 0 ? "data-autofocus" : ""}>`;
            return html`<div class="field"><label for="${id}">${f.label}${f.required ? raw(' <span class="faint">*</span>') : ""}</label>${control}${f.hint ? html`<span class="field-hint">${f.hint}</span>` : ""}</div>`;
          })}
          <div class="alert alert-danger" role="alert" data-error hidden><i class="bi bi-exclamation-octagon-fill" aria-hidden="true"></i><div class="alert-body" data-error-text></div></div>
          <div class="modal-actions">
            <button type="button" class="btn btn-ghost" data-act="cancel">Cancel</button>
            <button type="submit" class="btn btn-primary" data-act="ok">${submitLabel}</button>
          </div>
        </form>`
    );
    const form = $("form", dialog);
    fields.forEach((f) => {
      const control = form.elements[f.name];
      if (control && f.value != null) control.value = f.value;
    });
    const errorBox = $("[data-error]", dialog);
    $('[data-act="cancel"]', dialog).addEventListener("click", () => close(undefined));
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(fields.map((f) => [f.name, form.elements[f.name].value.trim()]));
      const missing = fields.find((f) => f.required && !values[f.name]);
      errorBox.hidden = true;
      if (missing) {
        $("[data-error-text]", dialog).textContent = `${missing.label} is required.`;
        errorBox.hidden = false;
        form.elements[missing.name].focus();
        return;
      }
      const submit = $('[data-act="ok"]', dialog);
      submit.classList.add("is-loading");
      try {
        close(await onSubmit(values));
      } catch (error) {
        submit.classList.remove("is-loading");
        $("[data-error-text]", dialog).textContent = error.message || "Something went wrong.";
        errorBox.hidden = false;
      }
    });
  });
}

// ------------------------------------------------------------ async helpers
/** Disable a button and show its spinner while `task` runs. */
export async function withLoading(button, task) {
  if (!button) return task();
  button.classList.add("is-loading");
  button.disabled = true;
  try {
    return await task();
  } finally {
    button.classList.remove("is-loading");
    button.disabled = false;
  }
}

// ---------------------------------------------------------- state templates
export const skeletonCards = (count = 3, height = 130) =>
  html`<div class="grid grid-auto" aria-hidden="true">${Array.from({ length: count }, () => html`<div class="card"><div class="skeleton sk-title"></div><div class="skeleton sk-line"></div><div class="skeleton sk-line" style="width:70%"></div><div class="skeleton" style="height:${height - 80}px;margin-top:12px"></div></div>`)}</div>`;

export const skeletonList = (rows = 4) =>
  html`<div class="stack-sm" aria-hidden="true">${Array.from({ length: rows }, () => html`<div class="skeleton" style="height:64px"></div>`)}</div>`;

export function emptyState({ icon = "inbox", title, text = "", actions = [] }) {
  return html`<div class="empty">
    <div class="empty-icon"><i class="bi bi-${icon}" aria-hidden="true"></i></div>
    <h3>${title}</h3>
    ${text ? html`<p>${text}</p>` : ""}
    ${actions.length ? html`<div class="row-wrap">${actions.map((a) => a.href
      ? html`<a class="btn ${a.primary ? "btn-primary" : ""}" href="${a.href}"><i class="bi bi-${a.icon || "arrow-right"}" aria-hidden="true"></i>${a.label}</a>`
      : html`<button type="button" class="btn ${a.primary ? "btn-primary" : ""}" data-action="${a.action}"><i class="bi bi-${a.icon || "arrow-right"}" aria-hidden="true"></i>${a.label}</button>`)}</div>` : ""}
  </div>`;
}

export function errorState(error, { retry = true } = {}) {
  const message = error?.message || "Something went wrong.";
  return html`<div class="empty" role="alert">
    <div class="empty-icon" style="color:var(--danger)"><i class="bi bi-cloud-slash" aria-hidden="true"></i></div>
    <h3>We couldn't load this</h3>
    <p>${message}</p>
    ${retry ? html`<div class="row-wrap"><button type="button" class="btn btn-primary" data-action="retry"><i class="bi bi-arrow-clockwise" aria-hidden="true"></i>Try again</button></div>` : ""}
  </div>`;
}

export const noSubjectState = () =>
  emptyState({
    icon: "folder-plus",
    title: "Create a subject to get started",
    text: "Subjects keep your documents, chats, notes, flashcards and quizzes organised. Create one, then upload your study material.",
    actions: [{ href: "subjects.html?new=1", label: "Create a subject", icon: "plus-lg", primary: true }],
  });

export const noDocumentsState = (subjectId) =>
  emptyState({
    icon: "file-earmark-arrow-up",
    title: "Upload study material first",
    text: "This works from your own documents. Upload a PDF, Word, PowerPoint or text file and wait for it to finish processing.",
    actions: [{ href: `documents.html?subject=${encodeURIComponent(subjectId)}`, label: "Go to Documents", icon: "cloud-upload", primary: true }],
  });

// --------------------------------------------------------- domain snippets
export const FILE_ICONS = { pdf: "file-earmark-pdf", docx: "file-earmark-word", pptx: "file-earmark-slides", txt: "file-earmark-text" };
export const fileIcon = (type) => FILE_ICONS[String(type || "").toLowerCase()] || "file-earmark";

const STATUS = {
  uploaded: { label: "Queued", cls: "badge-info", pulse: true },
  processing: { label: "Reading", cls: "badge-info", pulse: true },
  indexing: { label: "Indexing", cls: "badge-primary", pulse: true },
  ready: { label: "Ready", cls: "badge-success" },
  failed: { label: "Failed", cls: "badge-danger" },
};
export function statusBadge(status) {
  const s = STATUS[status] || { label: status || "Unknown", cls: "" };
  return html`<span class="badge ${s.cls}"><span class="dot ${s.pulse ? "pulse" : ""}"></span>${s.label}</span>`;
}
export const isInProgress = (status) => status === "uploaded" || status === "processing" || status === "indexing";

/** Circular progress. Needs the #ringGrad gradient injected by the shell. */
export function ring(percent, { size = 72, label } = {}) {
  const r = 42;
  const c = 2 * Math.PI * r;
  const value = percent === null || percent === undefined ? null : Math.max(0, Math.min(100, percent));
  const offset = value === null ? c : c * (1 - value / 100);
  return html`<div class="ring" style="--size:${size}px" role="img" aria-label="${label || (value === null ? "No progress yet" : `${value} percent`)}">
    <svg viewBox="0 0 100 100" aria-hidden="true"><circle class="ring-bg" cx="50" cy="50" r="${r}"/><circle class="ring-fg" cx="50" cy="50" r="${r}" stroke-dasharray="${c.toFixed(2)}" stroke-dashoffset="${offset.toFixed(2)}"/></svg>
    <div class="ring-label">${value === null ? html`<small>—</small>` : html`${value}<small>%</small>`}</div>
  </div>`;
}

export const progressBar = (percent, { thin = false, cls = "", label = "Progress" } = {}) =>
  html`<div class="progress ${thin ? "is-thin" : ""} ${cls}" role="progressbar" aria-label="${label}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(percent)}"><span style="width:${Math.max(0, Math.min(100, percent))}%"></span></div>`;

/** Wire data-action="retry" style buttons inside a container. */
export function onAction(container, handlers) {
  container.addEventListener("click", (event) => {
    const target = event.target.closest("[data-action]");
    if (!target || !container.contains(target)) return;
    const handler = handlers[target.dataset.action];
    if (handler) handler(target, event);
  });
}

export { escapeHtml };

/** Card shown while an AI generation is running (they take from a few seconds up to ~a minute). */
export const busyCard = (text, hint = "This can take up to a minute. You can keep this tab open.") =>
  html`<div class="empty busy" role="status" aria-live="polite"><div class="spinner spinner-lg" aria-hidden="true"></div><h3>${text}</h3><p>${hint}</p></div>`;

/**
 * Run an AI generation with consistent feedback. Resolves with the result, or null when it failed
 * (the error toast has already been shown - previous content is untouched by the server).
 */
export async function runGeneration(button, task, { onStart, onFinish } = {}) {
  button?.classList.add("is-loading");
  if (button) button.disabled = true;
  onStart?.();
  try {
    return await task();
  } catch (error) {
    toast.error(error.message || "Generation failed. Please try again.");
    return null;
  } finally {
    button?.classList.remove("is-loading");
    if (button) button.disabled = false;
    onFinish?.();
  }
}
