import { Api } from "../core/api.js";
import { mountShell } from "../core/shell.js";
import { loadUser } from "../core/auth.js";
import { $, html, render, greeting, timeAgo, formatBytes, plural, raw } from "../core/utils.js";
import { errorState, fileIcon, isInProgress, onAction, progressBar, ring, statusBadge, skeletonCards } from "../core/ui.js";
import { rememberSubject } from "../core/subjects.js";

const shell = await mountShell({ page: "dashboard", title: "Dashboard" });
const view = $("#view");
let pollTimer = null;

const ACTIVITY_ICONS = {
  document: "file-earmark-arrow-up",
  chat: "chat-square-text",
  quiz: "patch-check",
  notes: "journal-text",
  flashcards: "stack",
  quiz_generated: "patch-question",
  plan: "calendar2-check",
};

const subjectLink = (page, id) => `${page}?subject=${encodeURIComponent(id)}`;

function statCard({ icon, label, value, sub, tone = "primary", href }) {
  const body = html`<div class="stat-icon tone-${tone}"><i class="bi bi-${icon}" aria-hidden="true"></i></div>
    <div class="stat-body"><div class="stat-value tnum">${value}</div><div class="stat-label">${label}</div>${sub ? html`<div class="stat-sub">${sub}</div>` : ""}</div>`;
  return href ? html`<a class="card card-interactive stat" href="${href}">${body}</a>` : html`<div class="card stat">${body}</div>`;
}

function attention(d) {
  const items = [];
  if (d.documents_failed) {
    items.push({ tone: "danger", icon: "exclamation-octagon", text: `${plural(d.documents_failed, "document")} couldn't be processed.`, href: "documents.html?status=failed", cta: "Review" });
  }
  if (d.documents_in_progress) {
    items.push({ tone: "info", icon: "hourglass-split", text: `${plural(d.documents_in_progress, "document")} still being processed.`, href: "documents.html?status=processing", cta: "View progress" });
  }
  for (const s of d.subject_progress.filter((p) => p.documents === 0).slice(0, 2)) {
    items.push({ tone: "warning", icon: "cloud-arrow-up", text: `“${s.name}” has no documents yet.`, href: subjectLink("documents.html", s.id), cta: "Upload" });
  }
  if (!items.length) return "";
  return html`<section class="stack-sm" aria-label="Needs attention">
    ${items.map((i) => html`<div class="alert alert-${i.tone}"><i class="bi bi-${i.icon}" aria-hidden="true"></i><div class="alert-body">${i.text}</div><a class="btn btn-sm" href="${i.href}">${i.cta}</a></div>`)}
  </section>`;
}

function hero(d, name) {
  const top = d.subject_progress[0];
  if (!top) {
    return html`<section class="card hero-card rise">
      <div class="grow"><span class="badge badge-primary"><i class="bi bi-stars" aria-hidden="true"></i>Getting started</span>
        <h2>Create your first subject</h2>
        <p class="muted">Subjects keep your documents and study material together. Create one, upload a document, and EduRAG will turn it into answers, notes, flashcards and quizzes.</p>
        <div class="row-wrap" style="margin-top:var(--sp-4)"><a class="btn btn-primary" href="subjects.html?new=1"><i class="bi bi-plus-lg" aria-hidden="true"></i>Create a subject</a></div></div>
    </section>`;
  }
  const ready = top.documents_ready > 0;
  return html`<section class="card hero-card rise" aria-label="Continue learning">
    <div class="grow">
      <span class="badge badge-primary"><i class="bi bi-lightning-charge-fill" aria-hidden="true"></i>Continue learning</span>
      <h2>${top.name}</h2>
      <p class="muted">${top.last_activity ? `Last activity ${timeAgo(top.last_activity)}. ` : ""}${ready ? `${plural(top.documents_ready, "document")} ready to study from.` : "Upload a document to start studying this subject."}</p>
      <div class="row-wrap" style="margin-top:var(--sp-4)">
        ${ready
          ? html`<a class="btn btn-primary" href="${subjectLink("chat.html", top.id)}" data-subject="${top.id}" data-name="${top.name}"><i class="bi bi-chat-square-text" aria-hidden="true"></i>Ask a question</a>
                 <a class="btn" href="${subjectLink("flashcards.html", top.id)}"><i class="bi bi-stack" aria-hidden="true"></i>Flashcards</a>
                 <a class="btn" href="${subjectLink("quizes.html", top.id)}"><i class="bi bi-patch-question" aria-hidden="true"></i>Quiz</a>`
          : html`<a class="btn btn-primary" href="${subjectLink("documents.html", top.id)}"><i class="bi bi-cloud-arrow-up" aria-hidden="true"></i>Upload a document</a>`}
      </div>
    </div>
    <div class="hero-ring">${ring(top.progress, { size: 104 })}<span class="xs muted">${top.progress === null ? "No activity to measure yet" : "Subject progress"}</span></div>
  </section>`;
}

function subjectCards(list) {
  if (!list.length) return "";
  return html`<section aria-labelledby="sp-title">
    <div class="card-head"><h2 class="card-title" id="sp-title">Your subjects</h2><a class="btn btn-ghost btn-sm" href="subjects.html">Manage<i class="bi bi-arrow-right" aria-hidden="true"></i></a></div>
    <div class="grid grid-auto">${list.slice(0, 6).map((s) => html`
      <article class="card card-interactive subject-mini">
        <div class="row" style="align-items:flex-start"><div class="grow"><h3 class="truncate">${s.name}</h3>
          <p class="xs faint">${s.last_activity ? `Active ${timeAgo(s.last_activity)}` : ""}</p></div>${ring(s.progress, { size: 56 })}</div>
        <dl class="mini-stats">
          <div><dt>Docs</dt><dd>${s.documents_ready}/${s.documents}</dd></div>
          <div><dt>Cards</dt><dd>${s.flashcards ? `${s.flashcards_mastered}/${s.flashcards}` : "—"}</dd></div>
          <div><dt>Quiz</dt><dd>${s.best_quiz_accuracy === null ? "—" : `${s.best_quiz_accuracy}%`}</dd></div>
          <div><dt>Plan</dt><dd>${s.study_sessions ? `${s.study_sessions_completed}/${s.study_sessions}` : "—"}</dd></div>
        </dl>
        <div class="row-wrap">
          <a class="btn btn-sm btn-secondary" href="${subjectLink(s.documents_ready ? "chat.html" : "documents.html", s.id)}">${s.documents_ready ? "Open chat" : "Add documents"}</a>
          <a class="btn btn-sm btn-ghost" href="${subjectLink("notes.html", s.id)}">Notes</a>
        </div>
      </article>`)}</div>
  </section>`;
}

function recentDocuments(list) {
  return html`<section class="card" aria-labelledby="rd-title">
    <div class="card-head"><h2 class="card-title" id="rd-title">Recent documents</h2><a class="btn btn-ghost btn-sm" href="documents.html">All<i class="bi bi-arrow-right" aria-hidden="true"></i></a></div>
    ${list.length
      ? html`<ul class="stack-sm">${list.slice(0, 5).map((doc) => html`<li class="row list-row">
          <span class="file-badge ft-${doc.file_type}"><i class="bi bi-${fileIcon(doc.file_type)}" aria-hidden="true"></i></span>
          <div class="grow"><div class="truncate strong small" title="${doc.original_filename}">${doc.original_filename}</div><div class="xs faint truncate">${doc.subject_name || ""} · ${formatBytes(doc.file_size)}</div></div>
          ${statusBadge(doc.status)}</li>`)}</ul>`
      : html`<p class="muted small">No documents yet. Upload one to get started.</p>`}
  </section>`;
}

function recentActivity(list) {
  return html`<section class="card" aria-labelledby="ra-title">
    <div class="card-head"><h2 class="card-title" id="ra-title">Recent activity</h2></div>
    ${list.length
      ? html`<ol class="timeline">${list.map((a) => html`<li><span class="tl-dot"><i class="bi bi-${ACTIVITY_ICONS[a.type] || "circle"}" aria-hidden="true"></i></span>
          <div class="grow"><div class="small">${a.title}</div><div class="xs faint">${a.subject_name} · ${timeAgo(a.at)}</div></div></li>`)}</ol>`
      : html`<p class="muted small">Your activity will appear here as you study.</p>`}
  </section>`;
}

async function load({ initial = false } = {}) {
  if (initial) {
    render(view, html`<div class="grid grid-stats" aria-hidden="true">${Array.from({ length: 6 }, () => html`<div class="card"><div class="skeleton" style="height:64px"></div></div>`)}</div>${skeletonCards(3)}`);
  }
  let d;
  try {
    [d] = await Promise.all([Api.dashboard(), loadUser().catch(() => null)]);
  } catch (error) {
    if (initial) render(view, errorState(error));
    return;
  }
  const first = ((await loadUser().catch(() => null))?.full_name || "").split(" ")[0];
  $("#greeting").textContent = first ? `${greeting()}, ${first}` : greeting();

  if (!d.subjects) {
    render(view, html`<div class="stack">${hero(d)}
      <ol class="grid grid-stats steps-list" aria-label="How EduRAG works">
        <li class="card"><span class="step-num">1</span><h3>Create a subject</h3><p class="small muted">Group everything for a course or topic in one place.</p></li>
        <li class="card"><span class="step-num">2</span><h3>Upload documents</h3><p class="small muted">PDF, Word, PowerPoint or text. EduRAG reads and indexes them.</p></li>
        <li class="card"><span class="step-num">3</span><h3>Study smarter</h3><p class="small muted">Ask questions, then generate notes, flashcards, quizzes and a plan.</p></li>
      </ol></div>`);
    return;
  }

  render(
    view,
    html`<div class="stack">
      ${hero(d)}
      ${attention(d)}
      <section class="grid grid-stats" aria-label="Overview">
        ${statCard({ icon: "collection", label: "Subjects", value: d.subjects, href: "subjects.html" })}
        ${statCard({ icon: "folder2-open", label: "Documents", value: d.documents, sub: `${d.documents_ready} ready · ${d.storage_used > 0 ? formatBytes(Math.round(d.storage_used * 1024 * 1024)) : "< 10 KB"}`, tone: "info", href: "documents.html" })}
        ${statCard({ icon: "journal-text", label: "Notes", value: d.notes, tone: "accent", href: "notes.html" })}
        ${statCard({ icon: "stack", label: "Flashcards", value: d.flashcards, sub: d.flashcards ? `${d.flashcards_mastered} mastered` : "None yet", tone: "success", href: "flashcards.html" })}
        ${statCard({ icon: "patch-check", label: "Quiz accuracy", value: d.average_quiz_accuracy === null ? "—" : `${d.average_quiz_accuracy}%`, sub: d.quiz_attempts ? plural(d.quiz_attempts, "attempt") : "No attempts yet", tone: "warning", href: "quizes.html" })}
        ${statCard({ icon: "calendar2-check", label: "Study sessions", value: d.study_plans ? `${d.study_sessions_completed}/${d.study_plans}` : "—", sub: d.study_plans ? "completed" : "No plan yet", tone: "primary", href: "studyplanner.html" })}
      </section>
      <div class="grid grid-main-side">
        <div class="stack">${subjectCards(d.subject_progress)}</div>
        <div class="stack">${recentDocuments(d.recent_documents)}${recentActivity(d.recent_activity)}</div>
      </div>
    </div>`
  );

  // Poll only while something is being processed and the tab is visible.
  clearTimeout(pollTimer);
  const busy = d.documents_in_progress > 0 || d.recent_documents.some((doc) => isInProgress(doc.status));
  if (busy) pollTimer = setTimeout(() => !document.hidden && load(), 4000);
  else document.addEventListener("visibilitychange", onVisible, { once: true });
}
function onVisible() {
  if (!document.hidden) load();
}

// Remember the subject when jumping straight into a subject page from the hero.
view.addEventListener("click", (event) => {
  const link = event.target.closest("a[data-subject]");
  if (link) rememberSubject({ id: link.dataset.subject, name: link.dataset.name });
});
onAction(view, { retry: () => load({ initial: true }) });
load({ initial: true });
