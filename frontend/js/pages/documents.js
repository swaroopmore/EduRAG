import { Api } from "../core/api.js";
import { LIMITS } from "../config.js";
import { mountShell } from "../core/shell.js";
import { $, $$, html, raw, render, formatBytes, formatDateTime, plural, debounce, queryParam, fileExtension, el } from "../core/utils.js";
import { confirmDialog, emptyState, errorState, fileIcon, isInProgress, noSubjectState, onAction, progressBar, skeletonList, statusBadge, toast } from "../core/ui.js";
import { pickSubject, rememberSubject } from "../core/subjects.js";

await mountShell({ page: "documents", title: "Documents" });
const view = $("#view");

const state = {
  subjects: [],
  docs: [],
  loaded: false,
  filterSubject: queryParam("subject") || "all",
  filterStatus: queryParam("status") || "all",
  query: "",
  uploads: [], // client-side upload queue: {id, name, size, percent, error, subjectId}
  uploadSubject: null,
};
let pollTimer = null;
let uid = 0;

const STEPS = [
  { label: "Uploaded" },
  { label: "Reading" },
  { label: "Splitting" },
  { label: "Indexing" },
  { label: "Ready" },
];
function stepIndex(doc) {
  if (doc.status === "ready") return 5;
  if (doc.status === "indexing" || doc.stage === "embedding" || doc.stage === "storing") return 3;
  if (doc.stage === "chunking") return 2;
  return 1; // queued or extracting
}
function stepper(doc) {
  const active = stepIndex(doc);
  return html`<div class="stepper" role="img" aria-label="Processing: ${STEPS[Math.min(active, 4)].label}">${STEPS.map((s, i) => {
    const cls = i < active ? "is-done" : i === active ? "is-active" : "";
    return html`<div class="step ${cls}"><span class="node">${i < active ? html`<i class="bi bi-check-lg" aria-hidden="true"></i>` : ""}</span>${s.label}</div>`;
  })}</div>`;
}

// ---------------------------------------------------------------- rendering
function visibleDocs() {
  const q = state.query.toLowerCase();
  return state.docs.filter((d) => {
    if (state.filterSubject !== "all" && d.subject_id !== state.filterSubject) return false;
    if (state.filterStatus === "ready" && d.status !== "ready") return false;
    if (state.filterStatus === "processing" && !isInProgress(d.status)) return false;
    if (state.filterStatus === "failed" && d.status !== "failed") return false;
    if (q && !d.original_filename.toLowerCase().includes(q)) return false;
    return true;
  });
}

function docRow(d) {
  const meta = [formatBytes(d.file_size), d.page_count ? plural(d.page_count, d.file_type === "pptx" ? "slide" : "page") : null, d.chunk_count ? plural(d.chunk_count, "passage") : null].filter(Boolean).join(" · ");
  return html`<article class="card doc-card" data-doc="${d.id}">
    <div class="row" style="align-items:flex-start">
      <span class="file-badge ft-${d.file_type}"><i class="bi bi-${fileIcon(d.file_type)}" aria-hidden="true"></i></span>
      <div class="grow">
        <h3 class="doc-name" title="${d.original_filename}">${d.original_filename}</h3>
        <p class="xs faint doc-meta"><a href="documents.html?subject=${encodeURIComponent(d.subject_id)}" data-filter-subject="${d.subject_id}">${d.subject_name || "Subject"}</a> · ${meta} · ${formatDateTime(d.created_at)}</p>
      </div>
      ${statusBadge(d.status)}
    </div>
    ${isInProgress(d.status) ? stepper(d) : ""}
    ${d.status === "failed" ? html`<div class="alert alert-danger"><i class="bi bi-exclamation-octagon-fill" aria-hidden="true"></i><div class="alert-body"><strong>Couldn't process this document</strong>${d.error_message || "Something went wrong while reading it."}</div></div>` : ""}
    <div class="doc-actions">
      ${d.status === "ready" ? html`<a class="btn btn-sm btn-secondary" href="chat.html?subject=${encodeURIComponent(d.subject_id)}&document=${encodeURIComponent(d.id)}"><i class="bi bi-chat-square-text" aria-hidden="true"></i>Ask about this</a>` : ""}
      <button type="button" class="btn btn-sm" data-action="open" data-id="${d.id}" ${d.status === "uploaded" ? "disabled" : ""}><i class="bi bi-box-arrow-up-right" aria-hidden="true"></i>Open</button>
      ${d.status === "ready" || d.status === "failed" ? html`<button type="button" class="btn btn-sm btn-ghost" data-action="reindex" data-id="${d.id}"><i class="bi bi-arrow-repeat" aria-hidden="true"></i>${d.status === "failed" ? "Retry" : "Re-index"}</button>` : ""}
      <span class="spacer"></span>
      <button type="button" class="btn btn-sm btn-danger-ghost" data-action="delete" data-id="${d.id}" aria-label="Delete ${d.original_filename}"><i class="bi bi-trash3" aria-hidden="true"></i><span class="hide-xs">Delete</span></button>
    </div>
  </article>`;
}

function uploadRow(u) {
  return html`<div class="card upload-item ${u.error ? "has-error" : ""}" data-upload="${u.id}">
    <div class="row"><span class="file-badge ft-${fileExtension(u.name)}"><i class="bi bi-${fileIcon(fileExtension(u.name))}" aria-hidden="true"></i></span>
      <div class="grow"><div class="truncate strong small" title="${u.name}">${u.name}</div>
        <div class="xs ${u.error ? "" : "faint"}" ${u.error ? raw('style="color:var(--danger)"') : ""}>${u.error ? u.error : u.percent >= 100 ? "Uploaded — starting to process…" : `Uploading ${u.percent}% · ${formatBytes(u.size)}`}</div></div>
      ${u.error ? html`<button type="button" class="btn btn-sm btn-ghost btn-icon" data-action="dismiss-upload" data-id="${u.id}" aria-label="Dismiss"><i class="bi bi-x-lg" aria-hidden="true"></i></button>` : ""}
    </div>
    ${u.error ? "" : progressBar(u.percent, { thin: true, cls: u.percent >= 100 ? "is-indeterminate" : "" })}
  </div>`;
}

function uploader() {
  const opts = state.subjects.map((s) => html`<option value="${s.id}" ${s.id === state.uploadSubject ? "selected" : ""}>${s.name}</option>`);
  return html`<section class="card upload-card" aria-labelledby="up-title">
    <div class="row-wrap" style="justify-content:space-between;margin-bottom:var(--sp-3)">
      <h2 class="card-title" id="up-title">Upload documents</h2>
      <div class="row"><label class="small strong muted" for="upload-subject">To subject</label><select class="select" id="upload-subject" style="width:auto;min-width:180px">${opts}</select></div>
    </div>
    <div class="dropzone" id="dropzone" tabindex="0" role="button" aria-label="Choose files to upload, or drop them here">
      <i class="bi bi-cloud-arrow-up" aria-hidden="true"></i>
      <strong>Drag &amp; drop files here</strong>
      <span class="muted small">or <u>browse your device</u></span>
      <span class="xs faint">${LIMITS.fileTypes.map((t) => t.toUpperCase()).join(", ")} · up to ${LIMITS.maxUploadMb} MB each</span>
      <input type="file" id="file-input" multiple hidden accept="${LIMITS.fileTypes.map((t) => `.${t}`).join(",")}">
    </div>
    <div class="stack-sm" id="upload-queue" style="margin-top:var(--sp-3)" aria-live="polite">${state.uploads.map(uploadRow)}</div>
  </section>`;
}

function filters() {
  const count = (fn) => state.docs.filter(fn).length;
  const seg = [["all", "All", state.docs.length], ["ready", "Ready", count((d) => d.status === "ready")], ["processing", "Processing", count((d) => isInProgress(d.status))], ["failed", "Failed", count((d) => d.status === "failed")]];
  return html`<div class="row-wrap filters">
    <div class="input-icon grow" style="min-width:180px;max-width:360px"><i class="bi bi-search" aria-hidden="true"></i><input class="input" id="doc-search" type="search" placeholder="Search documents" aria-label="Search documents" value="${state.query}"></div>
    <select class="select" id="filter-subject" aria-label="Filter by subject" style="width:auto;min-width:170px"><option value="all">All subjects</option>${state.subjects.map((s) => html`<option value="${s.id}" ${s.id === state.filterSubject ? "selected" : ""}>${s.name}</option>`)}</select>
    <div class="segmented" role="group" aria-label="Filter by status">${seg.map(([key, label, n]) => html`<button type="button" data-status="${key}" aria-pressed="${state.filterStatus === key}">${label} <span class="faint">${n}</span></button>`)}</div>
  </div>`;
}

function list() {
  const docs = visibleDocs();
  if (!state.docs.length) {
    return emptyState({ icon: "file-earmark-arrow-up", title: "No documents yet", text: "Upload your first document above. It'll be ready to chat with in a moment." });
  }
  if (!docs.length) return emptyState({ icon: "funnel", title: "No documents match", text: "Try a different filter or search." });
  return html`<div class="doc-list">${docs.map(docRow)}</div>`;
}

let searchHadFocus = false;
function draw({ keepFocus = true } = {}) {
  searchHadFocus = keepFocus && document.activeElement?.id === "doc-search";
  const caret = searchHadFocus ? $("#doc-search").selectionStart : 0;
  if (!state.subjects.length) return render(view, noSubjectState());
  render(view, html`<div class="stack">${uploader()}<section class="stack" aria-label="Your documents">${filters()}<div id="doc-list">${list()}</div></section></div>`);
  if (searchHadFocus) {
    const input = $("#doc-search");
    input.focus();
    input.setSelectionRange(caret, caret);
  }
}

/** Re-render just the list/queue so an open dropdown or focused input isn't destroyed by polling. */
function drawList() {
  if (!$("#doc-list")) return draw();
  $("#doc-list").innerHTML = list().toString();
  $("#upload-queue").innerHTML = state.uploads.map(uploadRow).map(String).join("");
  const seg = $(".segmented");
  if (seg) {
    const fresh = filters().toString();
    const tmp = el("div");
    tmp.innerHTML = fresh;
    seg.innerHTML = $(".segmented", tmp).innerHTML;
  }
}

// ------------------------------------------------------------------ polling
function schedulePoll() {
  clearTimeout(pollTimer);
  if (!state.docs.some((d) => isInProgress(d.status))) return;
  pollTimer = setTimeout(async () => {
    if (document.hidden) return schedulePoll();
    try {
      state.docs = await Api.documents();
      drawList();
    } catch {
      /* transient - try again on the next tick */
    }
    schedulePoll();
  }, 1800);
}
document.addEventListener("visibilitychange", () => !document.hidden && schedulePoll());

async function load(initial = false) {
  if (initial) render(view, skeletonList(4));
  try {
    const [subjects, docs] = await Promise.all([Api.subjects(), Api.documents()]);
    state.subjects = subjects;
    state.docs = docs;
    state.loaded = true;
    const preferred = pickSubject(subjects);
    if (!state.uploadSubject || !subjects.some((s) => s.id === state.uploadSubject)) {
      state.uploadSubject = subjects.some((s) => s.id === state.filterSubject) ? state.filterSubject : preferred?.id;
    }
    if (state.filterSubject !== "all" && !subjects.some((s) => s.id === state.filterSubject)) state.filterSubject = "all";
    draw();
    schedulePoll();
  } catch (error) {
    render(view, errorState(error));
  }
}

// ------------------------------------------------------------------ uploads
function validate(file) {
  const ext = fileExtension(file.name);
  if (!LIMITS.fileTypes.includes(ext)) return `“${file.name}” isn't supported. Use ${LIMITS.fileTypes.map((t) => t.toUpperCase()).join(", ")}.`;
  if (file.size === 0) return `“${file.name}” is empty.`;
  if (file.size > LIMITS.maxUploadMb * 1024 * 1024) return `“${file.name}” is larger than ${LIMITS.maxUploadMb} MB.`;
  return null;
}

async function uploadFiles(files) {
  const subjectId = state.uploadSubject;
  if (!subjectId) return toast.error("Choose a subject first.");
  rememberSubject(state.subjects.find((s) => s.id === subjectId));
  for (const file of files) {
    const problem = validate(file);
    if (problem) {
      toast.error(problem);
      continue;
    }
    const item = { id: ++uid, name: file.name, size: file.size, percent: 0, error: null, subjectId };
    state.uploads.push(item);
    drawList();
    try {
      const doc = await Api.uploadDocument(subjectId, file, {
        onProgress: (percent) => {
          item.percent = percent;
          const node = $(`[data-upload="${item.id}"]`);
          if (node) node.outerHTML = uploadRow(item).toString();
        },
      });
      state.uploads = state.uploads.filter((u) => u !== item);
      doc.subject_name = state.subjects.find((s) => s.id === doc.subject_id)?.name;
      state.docs = [doc, ...state.docs.filter((d) => d.id !== doc.id)];
      toast.success(`“${file.name}” uploaded. Processing has started.`);
    } catch (error) {
      item.error = error.message;
    }
    drawList();
    schedulePoll();
  }
}

// ------------------------------------------------------------------ actions
view.addEventListener("change", (event) => {
  if (event.target.id === "upload-subject") state.uploadSubject = event.target.value;
  if (event.target.id === "filter-subject") {
    state.filterSubject = event.target.value;
    const url = new URL(location.href);
    state.filterSubject === "all" ? url.searchParams.delete("subject") : url.searchParams.set("subject", state.filterSubject);
    history.replaceState(null, "", url);
    if (state.filterSubject !== "all") {
      state.uploadSubject = state.filterSubject;
      $("#upload-subject").value = state.uploadSubject;
    }
    drawList();
  }
  if (event.target.id === "file-input") {
    uploadFiles(Array.from(event.target.files));
    event.target.value = "";
  }
});
view.addEventListener("input", debounce((event) => {
  if (event.target.id === "doc-search") {
    state.query = event.target.value.trim();
    $("#doc-list").innerHTML = list().toString();
  }
}, 120));
view.addEventListener("click", (event) => {
  const status = event.target.closest("[data-status]");
  if (status) {
    state.filterStatus = status.dataset.status;
    drawList();
    return;
  }
  const dz = event.target.closest("#dropzone");
  if (dz) $("#file-input").click();
});
view.addEventListener("keydown", (event) => {
  if ((event.key === "Enter" || event.key === " ") && event.target.id === "dropzone") {
    event.preventDefault();
    $("#file-input").click();
  }
});
for (const type of ["dragenter", "dragover"]) {
  view.addEventListener(type, (event) => {
    const dz = event.target.closest?.("#dropzone");
    if (dz) { event.preventDefault(); dz.classList.add("is-over"); }
  });
}
for (const type of ["dragleave", "drop"]) {
  view.addEventListener(type, (event) => {
    const dz = event.target.closest?.("#dropzone");
    if (!dz) return;
    event.preventDefault();
    dz.classList.remove("is-over");
    if (type === "drop") uploadFiles(Array.from(event.dataTransfer?.files || []));
  });
}
// A file dropped anywhere else on the page must not navigate the browser away.
window.addEventListener("dragover", (e) => e.preventDefault());
window.addEventListener("drop", (e) => e.preventDefault());

const find = (id) => state.docs.find((d) => d.id === id);
onAction(view, {
  retry: () => load(true),
  "dismiss-upload": (button) => {
    state.uploads = state.uploads.filter((u) => String(u.id) !== button.dataset.id);
    drawList();
  },
  async open(button) {
    const doc = find(button.dataset.id);
    button.classList.add("is-loading");
    try {
      const blob = await Api.documentFile(doc.id);
      const url = URL.createObjectURL(blob);
      const opened = window.open(url, "_blank", "noopener");
      if (!opened) {
        const a = el("a", { href: url, download: doc.original_filename });
        document.body.append(a);
        a.click();
        a.remove();
      }
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (error) {
      toast.error(error.status === 404 ? "The original file is no longer stored on the server. Re-upload it to open it." : error.message);
    } finally {
      button.classList.remove("is-loading");
    }
  },
  async reindex(button) {
    const doc = find(button.dataset.id);
    button.classList.add("is-loading");
    try {
      const updated = await Api.reindexDocument(doc.id);
      updated.subject_name = doc.subject_name;
      state.docs = state.docs.map((d) => (d.id === doc.id ? updated : d));
      toast.success("Re-indexing started.");
      drawList();
      schedulePoll();
    } catch (error) {
      button.classList.remove("is-loading");
      toast.error(error.message);
    }
  },
  async delete(button) {
    const doc = find(button.dataset.id);
    const ok = await confirmDialog({
      title: "Delete this document?",
      message: html`“${doc.original_filename}” will be removed from your library and from what EduRAG can answer from. Notes, flashcards and quizzes already generated from it are kept until you regenerate them.`,
      confirmLabel: "Delete document",
      danger: true,
    });
    if (!ok) return;
    try {
      await Api.deleteDocument(doc.id);
      state.docs = state.docs.filter((d) => d.id !== doc.id);
      toast.success("Document deleted.");
      drawList();
    } catch (error) {
      toast.error(error.message);
    }
  },
});

await load(true);
