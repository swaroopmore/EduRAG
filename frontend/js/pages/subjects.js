import { Api } from "../core/api.js";
import { mountShell } from "../core/shell.js";
import { $, html, render, formatDate, plural, debounce, queryParam } from "../core/utils.js";
import { confirmDialog, emptyState, errorState, formDialog, onAction, skeletonCards, toast } from "../core/ui.js";
import { rememberSubject, storedSubjectId } from "../core/subjects.js";

await mountShell({ page: "subjects", title: "Subjects" });
const view = $("#view");
const search = $("#subject-search");
const tools = $("#subject-tools");
let subjects = [];

const link = (page, id) => `${page}?subject=${encodeURIComponent(id)}`;

function card(s) {
  const hasDocs = s.ready_document_count > 0;
  return html`<article class="card card-interactive subject-card" data-id="${s.id}">
    <div class="sc-head"><span class="sc-icon"><i class="bi bi-journal-bookmark-fill" aria-hidden="true"></i></span>
      <div class="grow"><h2>${s.name}</h2><p class="xs faint">Created ${formatDate(s.created_at)}</p></div></div>
    <p class="sc-desc small muted clamp-2">${s.description || "No description yet."}</p>
    <div class="chips">
      <span class="chip"><i class="bi bi-folder2-open" aria-hidden="true"></i>${plural(s.document_count, "document")}${s.document_count !== s.ready_document_count ? ` (${s.ready_document_count} ready)` : ""}</span>
      <span class="chip"><i class="bi bi-journal-text" aria-hidden="true"></i>${plural(s.note_count, "note")}</span>
      <span class="chip"><i class="bi bi-stack" aria-hidden="true"></i>${plural(s.flashcard_count, "card")}</span>
      <span class="chip"><i class="bi bi-patch-question" aria-hidden="true"></i>${plural(s.quiz_question_count, "question")}</span>
    </div>
    <div class="sc-actions">
      ${hasDocs
        ? html`<a class="btn btn-secondary" href="${link("chat.html", s.id)}" data-open="${s.id}"><i class="bi bi-chat-square-text" aria-hidden="true"></i>Study</a>`
        : html`<a class="btn btn-primary" href="${link("documents.html", s.id)}" data-open="${s.id}"><i class="bi bi-cloud-arrow-up" aria-hidden="true"></i>Add documents</a>`}
      <button type="button" class="btn btn-ghost btn-icon" data-action="edit" data-id="${s.id}" aria-label="Edit ${s.name}"><i class="bi bi-pencil" aria-hidden="true"></i></button>
      <button type="button" class="btn btn-danger-ghost btn-icon" data-action="delete" data-id="${s.id}" aria-label="Delete ${s.name}"><i class="bi bi-trash3" aria-hidden="true"></i></button>
    </div>
  </article>`;
}

function draw() {
  const q = search.value.trim().toLowerCase();
  const list = q ? subjects.filter((s) => `${s.name} ${s.description || ""}`.toLowerCase().includes(q)) : subjects;
  tools.hidden = subjects.length < 4;
  if (!subjects.length) {
    render(view, emptyState({
      icon: "journal-plus",
      title: "No subjects yet",
      text: "Create a subject for each course or topic you're studying. You'll upload documents to it next.",
      actions: [{ action: "new", label: "Create your first subject", icon: "plus-lg", primary: true }],
    }));
  } else if (!list.length) {
    render(view, emptyState({ icon: "search", title: "No matching subjects", text: `Nothing matches “${search.value.trim()}”.` }));
  } else {
    render(view, html`<div class="grid grid-auto rise">${list.map(card)}</div>`);
  }
}

async function load(initial = false) {
  if (initial) render(view, skeletonCards(3));
  try {
    subjects = await Api.subjects();
    draw();
  } catch (error) {
    render(view, errorState(error));
  }
}

function subjectForm(subject) {
  return formDialog({
    title: subject ? "Edit subject" : "New subject",
    description: subject ? "" : "Give it a name you'll recognise, like “Organic Chemistry” or “World History”.",
    submitLabel: subject ? "Save changes" : "Create subject",
    fields: [
      { name: "name", label: "Name", required: true, maxlength: 100, value: subject?.name || "", placeholder: "e.g. Biology 101" },
      { name: "description", label: "Description", type: "textarea", maxlength: 500, value: subject?.description || "", placeholder: "Optional — what is this subject about?" },
    ],
    onSubmit: (v) => (subject ? Api.updateSubject(subject.id, v.name, v.description) : Api.createSubject(v.name, v.description)),
  });
}

async function create() {
  const created = await subjectForm(null);
  if (!created) return;
  toast.success(`“${created.name}” created. Upload your first document next.`);
  rememberSubject(created);
  await load();
}

onAction(view, {
  retry: () => load(true),
  new: create,
  async edit(button) {
    const subject = subjects.find((s) => s.id === button.dataset.id);
    if (await subjectForm(subject)) {
      toast.success("Subject updated.");
      await load();
    }
  },
  async delete(button) {
    const subject = subjects.find((s) => s.id === button.dataset.id);
    const ok = await confirmDialog({
      title: `Delete “${subject.name}”?`,
      message: html`This permanently deletes the subject and everything in it: ${plural(subject.document_count, "document")}, ${plural(subject.note_count, "note")}, ${plural(subject.flashcard_count, "flashcard")}, ${plural(subject.quiz_question_count, "quiz question")}, the chat history and the study plan. This can't be undone.`,
      confirmLabel: "Delete subject",
      danger: true,
    });
    if (!ok) return;
    try {
      await Api.deleteSubject(subject.id);
      if (storedSubjectId() === subject.id) rememberSubject(null);
      toast.success("Subject deleted.");
      await load();
    } catch (error) {
      toast.error(error.message);
    }
  },
});
view.addEventListener("click", (event) => {
  const open = event.target.closest("[data-open]");
  if (open) rememberSubject(subjects.find((s) => s.id === open.dataset.open));
});
$("#new-subject").addEventListener("click", create);
search.addEventListener("input", debounce(draw, 120));

await load(true);
if (queryParam("new") === "1") {
  history.replaceState(null, "", location.pathname);
  create();
}
