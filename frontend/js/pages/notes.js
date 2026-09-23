import { Api } from "../core/api.js";
import { mountShell } from "../core/shell.js";
import { renderMarkdown } from "../core/markdown.js";
import { $, $$, html, raw, render, copyText, downloadFile, readingTime, debounce, plural, slugify } from "../core/utils.js";
import { busyCard, confirmDialog, emptyState, errorState, noDocumentsState, noSubjectState, onAction, runGeneration, skeletonList, toast } from "../core/ui.js";

const shell = await mountShell({ page: "notes", title: "Notes", subjects: "required" });
const view = $("#view");
const actions = $("#notes-actions");

const state = { subject: shell.subject, notes: [], readyDocs: 0, query: "", generating: false };

const noteMarkdown = (n) => `## ${n.title}\n\n${n.content}${n.keywords?.length ? `\n\n**Keywords:** ${n.keywords.join(", ")}` : ""}\n`;
const allMarkdown = () => `# ${state.subject.name} — Notes\n\n${state.notes.map(noteMarkdown).join("\n")}`;

function matches(n) {
  const q = state.query.toLowerCase();
  return !q || `${n.title} ${n.content} ${(n.keywords || []).join(" ")}`.toLowerCase().includes(q);
}

function renderActions() {
  const has = state.notes.length > 0;
  render(actions, html`${has ? html`
      <button type="button" class="btn" data-action="toggle-all" aria-label="Expand all"><i class="bi bi-arrows-expand" aria-hidden="true"></i><span class="hide-xs">Expand all</span></button>
      <button type="button" class="btn" data-action="copy-all" aria-label="Copy all notes"><i class="bi bi-clipboard" aria-hidden="true"></i><span class="hide-xs">Copy all</span></button>
      <button type="button" class="btn" data-action="download-all" aria-label="Download all notes"><i class="bi bi-download" aria-hidden="true"></i><span class="hide-xs">Download</span></button>` : ""}
    ${state.readyDocs ? html`<button type="button" class="btn ${has ? "" : "btn-primary"}" id="generate" data-action="generate"><i class="bi bi-${has ? "arrow-repeat" : "stars"}" aria-hidden="true"></i>${has ? "Regenerate" : "Generate notes"}</button>` : ""}`);
}

function noteCard(n, i) {
  const minutes = readingTime(n.content);
  return html`<details class="card note" id="note-${i}" data-note="${i}" ${i === 0 ? "open" : ""}>
    <summary>
      <span class="note-num" aria-hidden="true">${i + 1}</span>
      <span class="grow"><span class="note-title">${n.title}</span>
        <span class="xs faint">${minutes} min read${n.keywords?.length ? ` · ${plural(n.keywords.length, "keyword")}` : ""}</span></span>
      <i class="bi bi-chevron-down note-chevron" aria-hidden="true"></i>
    </summary>
    <div class="note-body">
      <div class="prose">${raw(renderMarkdown(n.content))}</div>
      ${n.keywords?.length ? html`<div class="chips" style="margin-top:var(--sp-4)" aria-label="Keywords">${n.keywords.map((k) => html`<span class="chip"><i class="bi bi-tag" aria-hidden="true"></i>${k}</span>`)}</div>` : ""}
      <div class="note-actions">
        <button type="button" class="btn btn-sm btn-ghost" data-action="copy" data-i="${i}"><i class="bi bi-clipboard" aria-hidden="true"></i>Copy</button>
        <button type="button" class="btn btn-sm btn-ghost" data-action="download" data-i="${i}"><i class="bi bi-download" aria-hidden="true"></i>Download</button>
      </div>
    </div>
  </details>`;
}

function draw() {
  renderActions();
  if (!state.subject) return render(view, noSubjectState());
  if (!state.readyDocs && !state.notes.length) return render(view, noDocumentsState(state.subject.id));
  if (!state.notes.length) {
    return render(view, emptyState({
      icon: "journal-text",
      title: "No notes yet",
      text: `Generate structured revision notes from your ${plural(state.readyDocs, "ready document")}. It usually takes under a minute.`,
      actions: [{ action: "generate", label: "Generate notes", icon: "stars", primary: true }],
    }));
  }
  const visible = state.notes.map((n, i) => [n, i]).filter(([n]) => matches(n));
  render(
    view,
    html`<div class="notes-layout">
      <div class="stack">
        <div class="row-wrap"><div class="input-icon grow" style="max-width:420px"><i class="bi bi-search" aria-hidden="true"></i>
          <input class="input" id="note-search" type="search" placeholder="Search notes" aria-label="Search notes" value="${state.query}"></div>
          <span class="small muted">${state.query ? `${visible.length} of ${state.notes.length} sections` : plural(state.notes.length, "section")} · ${readingTime(state.notes.map((n) => n.content).join(" "))} min total</span></div>
        <div class="stack-sm" id="note-list">${visible.length ? visible.map(([n, i]) => noteCard(n, i)) : emptyState({ icon: "search", title: "No matching notes", text: "Try different keywords." })}</div>
      </div>
      <aside class="card toc" aria-label="Sections"><h2 class="card-title" style="margin-bottom:var(--sp-3)">Sections</h2>
        <ol>${state.notes.map((n, i) => html`<li><a href="#note-${i}" data-toc="${i}" class="${matches(n) ? "" : "faint"}">${n.title}</a></li>`)}</ol></aside>
    </div>`
  );
}

async function load() {
  render(actions, "");
  if (!state.subject) return draw();
  render(view, skeletonList(4));
  try {
    const [notes, docs] = await Promise.all([Api.notes(state.subject.id), Api.documents(state.subject.id)]);
    state.notes = notes;
    state.readyDocs = docs.filter((d) => d.status === "ready").length;
    draw();
  } catch (error) {
    render(view, errorState(error));
  }
}

async function generate(button) {
  if (state.generating) return;
  if (state.notes.length) {
    const ok = await confirmDialog({
      title: "Regenerate notes?",
      message: `This replaces your current ${plural(state.notes.length, "note section")} with freshly generated ones. If generation fails, your existing notes are kept.`,
      confirmLabel: "Regenerate",
    });
    if (!ok) return;
  }
  state.generating = true;
  const before = state.notes.length;
  const result = await runGeneration(button, () => Api.generateNotes(state.subject.id), {
    onStart: () => before === 0 && render(view, busyCard("Writing your notes…", "Reading your documents and structuring the key ideas. This can take up to a minute.")),
  });
  state.generating = false;
  if (result) {
    state.notes = await Api.notes(state.subject.id);
    toast.success(`Generated ${plural(result.generated, "note section")}.`);
  }
  draw();
}

const rebuildList = debounce(() => {
  const list = $("#note-list");
  if (!list) return;
  const visible = state.notes.map((n, i) => [n, i]).filter(([n]) => matches(n));
  list.innerHTML = (visible.length ? visible.map(([n, i]) => noteCard(n, i)) : emptyState({ icon: "search", title: "No matching notes", text: "Try different keywords." })).toString();
  $$(".toc a").forEach((a) => a.classList.toggle("faint", !matches(state.notes[Number(a.dataset.toc)])));
}, 120);
view.addEventListener("input", (event) => {
  if (event.target.id === "note-search") {
    state.query = event.target.value.trim();
    rebuildList();
  }
});

const handlers = {
  retry: load,
  generate,
  async copy(b) {
    toast((await copyText(noteMarkdown(state.notes[Number(b.dataset.i)]))) ? "Note copied." : "Couldn't copy to clipboard.", { type: "success", timeout: 2000 });
  },
  download(b) {
    const n = state.notes[Number(b.dataset.i)];
    downloadFile(`${slugify(n.title)}.md`, noteMarkdown(n));
  },
  async "copy-all"() {
    toast((await copyText(allMarkdown())) ? "All notes copied." : "Couldn't copy to clipboard.", { type: "success", timeout: 2000 });
  },
  "download-all"() {
    downloadFile(`${slugify(state.subject.name)}-notes.md`, allMarkdown());
  },
  "toggle-all"(button) {
    const items = $$("details.note");
    const open = items.some((d) => !d.open);
    items.forEach((d) => (d.open = open));
    button.querySelector("span").textContent = open ? "Collapse all" : "Expand all";
    button.setAttribute("aria-label", open ? "Collapse all" : "Expand all");
    button.querySelector("i").className = `bi bi-arrows-${open ? "collapse" : "expand"}`;
  },
};
onAction(view, handlers);
onAction(actions, handlers);
view.addEventListener("click", (event) => {
  const link = event.target.closest("[data-toc]");
  if (!link) return;
  const target = $(`#note-${link.dataset.toc}`);
  if (target) {
    event.preventDefault();
    target.open = true;
    target.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  }
});

shell.onSubjectChange((subject) => {
  state.subject = subject;
  state.query = "";
  load();
});
await load();
