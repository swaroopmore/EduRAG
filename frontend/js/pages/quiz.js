import { Api } from "../core/api.js";
import { mountShell } from "../core/shell.js";
import { $, $$, html, raw, render, plural, formatDateTime, timeAgo } from "../core/utils.js";
import { busyCard, confirmDialog, emptyState, errorState, noDocumentsState, noSubjectState, onAction, progressBar, ring, runGeneration, skeletonList, toast } from "../core/ui.js";

const shell = await mountShell({ page: "quiz", title: "Quiz", subjects: "required" });
const view = $("#view");
const actions = $("#quiz-actions");
const LETTERS = ["A", "B", "C", "D"];

const state = {
  subject: shell.subject,
  questions: [],
  attempts: [],
  readyDocs: 0,
  phase: "intro", // intro | taking | results
  idx: 0,
  answers: {}, // question id -> letter
  result: null,
  reviewFilter: "all",
  generating: false,
  submitting: false,
};

const optionText = (q, letter) => q[`option_${letter.toLowerCase()}`];

function renderActions() {
  const has = state.questions.length > 0;
  render(actions, html`${state.readyDocs && state.phase !== "taking" ? html`<button type="button" class="btn ${has ? "" : "btn-primary"}" data-action="generate"><i class="bi bi-${has ? "arrow-repeat" : "stars"}" aria-hidden="true"></i>${has ? "New questions" : "Generate quiz"}</button>` : ""}`);
}

// ------------------------------------------------------------------- intro
function attemptsList() {
  if (!state.attempts.length) return "";
  return html`<section class="card" aria-labelledby="att-title"><h2 class="card-title" id="att-title" style="margin-bottom:var(--sp-3)">Your attempts</h2>
    <ul class="stack-sm">${state.attempts.slice(0, 6).map((a) => html`<li class="row list-row"><span class="badge ${a.accuracy >= 70 ? "badge-success" : a.accuracy >= 40 ? "badge-warning" : "badge-danger"} tnum">${a.accuracy}%</span>
      <div class="grow small"><strong class="tnum">${a.score}/${a.total}</strong> correct</div><span class="xs faint">${timeAgo(a.created_at)}</span></li>`)}</ul></section>`;
}

function intro() {
  const best = state.attempts.length ? Math.max(...state.attempts.map((a) => a.accuracy)) : null;
  return html`<div class="grid grid-main-side"><section class="card quiz-intro">
      <span class="badge badge-primary"><i class="bi bi-patch-question" aria-hidden="true"></i>Multiple choice</span>
      <h2>${plural(state.questions.length, "question")} on ${state.subject.name}</h2>
      <p class="muted">Answer at your own pace. You'll see the correct answers and explanations only after you submit.</p>
      ${best !== null ? html`<p class="small">Best score so far: <strong>${best}%</strong> · ${plural(state.attempts.length, "attempt")}</p>` : ""}
      <div class="row-wrap" style="margin-top:var(--sp-4)"><button type="button" class="btn btn-primary btn-lg" data-action="start"><i class="bi bi-play-fill" aria-hidden="true"></i>${state.attempts.length ? "Take the quiz again" : "Start quiz"}</button></div>
    </section>${attemptsList()}</div>`;
}

// ------------------------------------------------------------------ taking
function taking() {
  const q = state.questions[state.idx];
  const answered = Object.keys(state.answers).length;
  const last = state.idx === state.questions.length - 1;
  const selected = state.answers[q.id];
  return html`<div class="quiz-wrap">
    <div class="quiz-top"><span class="small strong tnum">Question ${state.idx + 1} of ${state.questions.length}</span><span class="small muted tnum">${answered} answered</span></div>
    ${progressBar(((state.idx + 1) / state.questions.length) * 100, { thin: true })}
    <section class="card quiz-card" aria-labelledby="q-text">
      <h2 id="q-text" class="quiz-q">${q.question}</h2>
      <div class="options" role="radiogroup" aria-labelledby="q-text">${LETTERS.map((L) => html`<label class="option ${selected === L ? "is-selected" : ""}"><input type="radio" name="answer" value="${L}" ${selected === L ? "checked" : ""}><span class="opt-letter" aria-hidden="true">${L}</span><span class="opt-text">${optionText(q, L)}</span></label>`)}</div>
    </section>
    <nav class="quiz-nav" aria-label="Question navigation">${state.questions.map((item, i) => html`<button type="button" class="qdot ${i === state.idx ? "is-current" : ""} ${state.answers[item.id] ? "is-answered" : ""}" data-action="goto" data-i="${i}" aria-label="Question ${i + 1}${state.answers[item.id] ? ", answered" : ""}" ${i === state.idx ? raw('aria-current="step"') : ""}>${i + 1}</button>`)}</nav>
    <div class="row quiz-buttons">
      <button type="button" class="btn" data-action="prev" ${state.idx === 0 ? "disabled" : ""}><i class="bi bi-arrow-left" aria-hidden="true"></i>Previous</button>
      <span class="spacer"></span>
      <button type="button" class="btn btn-ghost" data-action="quit">Quit</button>
      ${last
        ? html`<button type="button" class="btn btn-primary" data-action="submit" id="submit-quiz"><i class="bi bi-check2-all" aria-hidden="true"></i>Submit</button>`
        : html`<button type="button" class="btn btn-primary" data-action="next">Next<i class="bi bi-arrow-right" aria-hidden="true"></i></button>`}
    </div>
  </div>`;
}

// ----------------------------------------------------------------- results
function verdict(pct) {
  if (pct >= 90) return ["Outstanding!", "You clearly know this material."];
  if (pct >= 70) return ["Great job", "Solid understanding — review the few you missed."];
  if (pct >= 40) return ["Getting there", "Go through the explanations below and try again."];
  return ["Keep practising", "Re-read your notes, then retry. It gets easier."];
}

function results() {
  const r = state.result;
  const [title, text] = verdict(r.accuracy);
  const items = r.results.filter((x) => state.reviewFilter === "all" || !x.is_correct);
  return html`<div class="stack quiz-results">
    <section class="card result-hero">${ring(r.accuracy, { size: 120, label: `${r.accuracy} percent` })}
      <div class="grow"><h2>${title}</h2><p class="muted">${text}</p><p class="strong tnum" style="margin-top:var(--sp-2)">${r.score} of ${r.total} correct</p>
        <div class="row-wrap" style="margin-top:var(--sp-4)"><button type="button" class="btn btn-primary" data-action="retry-quiz"><i class="bi bi-arrow-counterclockwise" aria-hidden="true"></i>Try again</button>
          <button type="button" class="btn" data-action="back">Back to quiz home</button></div></div></section>
    <section aria-labelledby="rev-title"><div class="card-head"><h2 class="card-title" id="rev-title">Review</h2>
      <div class="segmented" role="group" aria-label="Filter review"><button type="button" data-action="filter" data-f="all" aria-pressed="${state.reviewFilter === "all"}">All ${r.total}</button><button type="button" data-action="filter" data-f="wrong" aria-pressed="${state.reviewFilter === "wrong"}">Incorrect ${r.total - r.score}</button></div></div>
      <div class="stack-sm">${items.length ? items.map((x, i) => html`<article class="card review ${x.is_correct ? "is-correct" : "is-wrong"}">
        <div class="row" style="align-items:flex-start"><span class="review-mark" aria-hidden="true"><i class="bi bi-${x.is_correct ? "check-lg" : "x-lg"}"></i></span>
          <div class="grow"><h3 class="review-q">${x.question}</h3>
            <ul class="review-options">${LETTERS.map((L) => html`<li class="${L === x.correct_answer ? "is-answer" : ""} ${L === x.selected && !x.is_correct ? "is-picked-wrong" : ""}"><span class="opt-letter">${L}</span><span class="grow">${x.options[L]}</span>
              ${L === x.correct_answer ? html`<span class="badge badge-success">Correct</span>` : L === x.selected ? html`<span class="badge badge-danger">Your answer</span>` : ""}</li>`)}</ul>
            ${x.selected ? "" : html`<p class="xs" style="color:var(--warning);margin-top:var(--sp-2)">You didn't answer this one.</p>`}
            ${x.explanation ? html`<p class="explain small"><i class="bi bi-lightbulb" aria-hidden="true"></i> ${x.explanation}</p>` : ""}</div></div></article>`) : emptyState({ icon: "emoji-smile", title: "Nothing to review here", text: "You got everything right!" })}</div></section>
  </div>`;
}

// -------------------------------------------------------------------- draw
function draw() {
  renderActions();
  if (!state.subject) return render(view, noSubjectState());
  if (!state.questions.length) {
    if (!state.readyDocs) return render(view, noDocumentsState(state.subject.id));
    return render(view, emptyState({
      icon: "patch-question",
      title: "No quiz yet",
      text: `Generate multiple-choice questions from your ${plural(state.readyDocs, "ready document")}.`,
      actions: [{ action: "generate", label: "Generate quiz", icon: "stars", primary: true }],
    }));
  }
  render(view, state.phase === "taking" ? taking() : state.phase === "results" ? results() : intro());
}

async function load() {
  render(actions, "");
  if (!state.subject) return draw();
  render(view, skeletonList(3));
  try {
    const [questions, attempts, docs] = await Promise.all([Api.quiz(state.subject.id), Api.quizAttempts(state.subject.id), Api.documents(state.subject.id)]);
    Object.assign(state, { questions, attempts, phase: "intro", idx: 0, answers: {}, result: null, readyDocs: docs.filter((d) => d.status === "ready").length });
    draw();
  } catch (error) {
    render(view, errorState(error));
  }
}

async function generate(button) {
  if (state.generating) return;
  if (state.questions.length) {
    const ok = await confirmDialog({
      title: "Generate new questions?",
      message: `This replaces the current ${plural(state.questions.length, "question")}. Your past attempts stay in your history. If generation fails, your current quiz is kept.`,
      confirmLabel: "Generate",
    });
    if (!ok) return;
  }
  state.generating = true;
  const before = state.questions.length;
  const result = await runGeneration(button, () => Api.generateQuiz(state.subject.id), {
    onStart: () => before === 0 && render(view, busyCard("Writing your quiz…")),
  });
  state.generating = false;
  if (result) {
    state.questions = await Api.quiz(state.subject.id);
    Object.assign(state, { phase: "intro", idx: 0, answers: {}, result: null });
    toast.success(`Generated ${plural(result.generated, "question")}.`);
  }
  draw();
}

const start = () => {
  Object.assign(state, { phase: "taking", idx: 0, answers: {}, result: null, reviewFilter: "all" });
  draw();
  $("#q-text")?.scrollIntoView({ block: "nearest" });
};
const focusQuestion = () => {
  draw();
  $(".option.is-selected input, .option input")?.focus({ preventScroll: true });
};

async function submit() {
  if (state.submitting) return;
  const unanswered = state.questions.length - Object.keys(state.answers).length;
  if (unanswered > 0) {
    const ok = await confirmDialog({
      title: "Submit with unanswered questions?",
      message: `${plural(unanswered, "question")} ${unanswered === 1 ? "is" : "are"} unanswered and will be marked incorrect.`,
      confirmLabel: "Submit anyway",
      cancelLabel: "Keep answering",
    });
    if (!ok) return;
  }
  state.submitting = true;
  const button = $("#submit-quiz");
  button?.classList.add("is-loading");
  try {
    state.result = await Api.submitQuiz(state.subject.id, state.answers);
    state.attempts = await Api.quizAttempts(state.subject.id);
    state.phase = "results";
    state.reviewFilter = "all";
    draw();
    window.scrollTo({ top: 0, behavior: "auto" });
  } catch (error) {
    button?.classList.remove("is-loading");
    toast.error(error.message);
  } finally {
    state.submitting = false;
  }
}

onAction(view, {
  retry: load,
  generate,
  start,
  "retry-quiz": start,
  back: () => {
    state.phase = "intro";
    draw();
  },
  prev: () => { state.idx = Math.max(0, state.idx - 1); focusQuestion(); },
  next: () => { state.idx = Math.min(state.questions.length - 1, state.idx + 1); focusQuestion(); },
  goto: (b) => { state.idx = Number(b.dataset.i); focusQuestion(); },
  submit,
  filter: (b) => { state.reviewFilter = b.dataset.f; draw(); },
  async quit() {
    const ok = await confirmDialog({ title: "Leave this quiz?", message: "Your answers so far won't be saved.", confirmLabel: "Leave quiz", cancelLabel: "Keep going", danger: true });
    if (ok) {
      state.phase = "intro";
      draw();
    }
  },
});
onAction(actions, { generate });

view.addEventListener("change", (event) => {
  if (event.target.name !== "answer") return;
  const q = state.questions[state.idx];
  state.answers[q.id] = event.target.value;
  $$(".option", view).forEach((o) => o.classList.toggle("is-selected", $("input", o).checked));
  $$(".qdot", view)[state.idx]?.classList.add("is-answered");
  const answered = Object.keys(state.answers).length;
  $(".quiz-top span:last-child", view).textContent = `${answered} answered`;
});
document.addEventListener("keydown", (event) => {
  if (state.phase !== "taking" || event.metaKey || event.ctrlKey || event.altKey || event.target.closest(".modal")) return;
  const key = event.key.toUpperCase();
  const map = { "1": "A", "2": "B", "3": "C", "4": "D" };
  const letter = LETTERS.includes(key) ? key : map[key];
  if (letter && !event.target.closest("input[type=text], textarea")) {
    const input = $(`input[name="answer"][value="${letter}"]`, view);
    if (input) { input.checked = true; input.dispatchEvent(new Event("change", { bubbles: true })); }
  }
});

shell.onSubjectChange((subject) => {
  state.subject = subject;
  load();
});
await load();
