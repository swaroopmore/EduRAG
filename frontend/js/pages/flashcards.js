import { Api } from "../core/api.js";
import { mountShell } from "../core/shell.js";
import { $, $$, html, raw, render, shuffled, plural, debounce } from "../core/utils.js";
import { busyCard, confirmDialog, emptyState, errorState, noDocumentsState, noSubjectState, onAction, progressBar, runGeneration, skeletonList, toast } from "../core/ui.js";

const shell = await mountShell({ page: "flashcards", title: "Flashcards", subjects: "required" });
const view = $("#view");
const actions = $("#cards-actions");

const state = {
  subject: shell.subject,
  cards: [],
  readyDocs: 0,
  deckIds: [], // snapshot of the cards being studied (in study order)
  idx: 0,
  flipped: false,
  hideMastered: false,
  mode: "study", // study | list
  query: "",
  generating: false,
};

const byId = (id) => state.cards.find((c) => c.id === id);
const mastered = () => state.cards.filter((c) => c.mastered).length;

function buildDeck({ shuffle = false, keepCurrent = false } = {}) {
  const current = keepCurrent ? state.deckIds[state.idx] : null;
  let ids = (shuffle ? shuffled(state.cards) : state.cards).map((c) => c.id);
  if (!shuffle && state.deckIds.length && keepCurrent) ids = state.deckIds.filter((id) => byId(id));
  if (state.hideMastered) ids = ids.filter((id) => !byId(id).mastered || id === current);
  state.deckIds = ids;
  state.idx = current ? Math.max(0, ids.indexOf(current)) : 0;
  state.flipped = false;
}

function renderActions() {
  const has = state.cards.length > 0;
  render(actions, html`${has ? html`
      <div class="segmented" role="group" aria-label="View"><button type="button" data-action="mode" data-mode="study" aria-pressed="${state.mode === "study"}"><i class="bi bi-layers" aria-hidden="true"></i> Study</button><button type="button" data-action="mode" data-mode="list" aria-pressed="${state.mode === "list"}"><i class="bi bi-list-ul" aria-hidden="true"></i> All cards</button></div>` : ""}
    ${state.readyDocs ? html`<button type="button" class="btn ${has ? "" : "btn-primary"}" data-action="generate"><i class="bi bi-${has ? "arrow-repeat" : "stars"}" aria-hidden="true"></i>${has ? "Regenerate" : "Generate flashcards"}</button>` : ""}`);
}

function progressHeader() {
  const total = state.cards.length;
  const done = mastered();
  return html`<div class="fc-progress"><div class="row-wrap" style="justify-content:space-between"><span class="small strong">${done} of ${total} mastered</span><span class="small muted tnum">${Math.round((done / total) * 100)}%</span></div>${progressBar((done / total) * 100, { thin: true, cls: "is-success", label: "Cards mastered" })}</div>`;
}

function studyView() {
  const deck = state.deckIds.map(byId);
  if (!deck.length) {
    return html`${progressHeader()}${emptyState({
      icon: "trophy",
      title: "Every card mastered",
      text: "Nice work! Turn off “Hide mastered” to review them again, or regenerate a fresh set.",
      actions: [{ action: "show-all", label: "Review all cards", icon: "arrow-counterclockwise", primary: true }],
    })}`;
  }
  const card = deck[Math.min(state.idx, deck.length - 1)];
  return html`${progressHeader()}
    <div class="fc-wrap">
      <div class="fc-meta"><span class="badge badge-primary tnum">Card ${state.idx + 1} of ${deck.length}</span>${card.mastered ? html`<span class="badge badge-success"><i class="bi bi-check-circle-fill" aria-hidden="true"></i>Mastered</span>` : ""}</div>
      <div class="fc-stage" id="stage">
        <button type="button" class="fc ${state.flipped ? "is-flipped" : ""}" id="fc" data-action="flip" aria-label="Flashcard. ${state.flipped ? "Showing the answer." : "Showing the question."} Press to flip.">
          <span class="fc-face fc-front" ${state.flipped ? raw('aria-hidden="true"') : ""}><span class="fc-tag">Question</span><span class="fc-text">${card.question}</span><span class="fc-hint xs faint"><i class="bi bi-hand-index" aria-hidden="true"></i> Tap to reveal</span></span>
          <span class="fc-face fc-back" ${state.flipped ? "" : raw('aria-hidden="true"')}><span class="fc-tag">Answer</span><span class="fc-text">${card.answer}</span></span>
        </button>
      </div>
      <div class="fc-controls">
        <button type="button" class="btn btn-icon" data-action="prev" aria-label="Previous card" ${state.idx === 0 ? "disabled" : ""}><i class="bi bi-chevron-left" aria-hidden="true"></i></button>
        <button type="button" class="btn ${card.mastered ? "btn-secondary" : ""} grow" data-action="master" aria-pressed="${card.mastered}"><i class="bi bi-${card.mastered ? "check-circle-fill" : "check-circle"}" aria-hidden="true"></i>${card.mastered ? "Mastered" : "Mark as mastered"}</button>
        <button type="button" class="btn btn-icon" data-action="next" aria-label="Next card" ${state.idx >= deck.length - 1 ? "disabled" : ""}><i class="bi bi-chevron-right" aria-hidden="true"></i></button>
      </div>
      <div class="row-wrap fc-tools">
        <button type="button" class="btn btn-sm btn-ghost" data-action="shuffle"><i class="bi bi-shuffle" aria-hidden="true"></i>Shuffle</button>
        <label class="check small"><input type="checkbox" data-action="hide-mastered" ${state.hideMastered ? "checked" : ""}> Hide mastered</label>
        <span class="spacer"></span>
        <span class="xs faint hide-touch"><kbd>←</kbd> <kbd>→</kbd> navigate · <kbd>Space</kbd> flip · <kbd>M</kbd> mastered</span>
      </div>
    </div>`;
}

function listView() {
  const q = state.query.toLowerCase();
  const cards = state.cards.filter((c) => !q || `${c.question} ${c.answer}`.toLowerCase().includes(q));
  return html`${progressHeader()}
    <div class="input-icon" style="max-width:420px"><i class="bi bi-search" aria-hidden="true"></i><input class="input" id="card-search" type="search" placeholder="Search cards" aria-label="Search cards" value="${state.query}"></div>
    <div class="stack-sm" id="card-list">${cards.length ? cards.map((c) => html`<article class="card card-row"><div class="grow"><h2 class="fc-q">${c.question}</h2><p class="muted small">${c.answer}</p></div>
      <button type="button" class="btn btn-sm ${c.mastered ? "btn-secondary" : ""}" data-action="master-id" data-id="${c.id}" aria-pressed="${c.mastered}" aria-label="Mastered"><i class="bi bi-${c.mastered ? "check-circle-fill" : "check-circle"}" aria-hidden="true"></i><span class="hide-xs">${c.mastered ? "Mastered" : "Master"}</span></button></article>`) : emptyState({ icon: "search", title: "No matching cards" })}</div>`;
}

function draw() {
  renderActions();
  if (!state.subject) return render(view, noSubjectState());
  if (!state.cards.length) {
    if (!state.readyDocs) return render(view, noDocumentsState(state.subject.id));
    return render(view, emptyState({
      icon: "stack",
      title: "No flashcards yet",
      text: `Generate a deck of question-and-answer cards from your ${plural(state.readyDocs, "ready document")}.`,
      actions: [{ action: "generate", label: "Generate flashcards", icon: "stars", primary: true }],
    }));
  }
  render(view, html`<div class="stack">${state.mode === "study" ? studyView() : listView()}</div>`);
}

async function load() {
  render(actions, "");
  if (!state.subject) return draw();
  render(view, skeletonList(3));
  try {
    const [cards, docs] = await Promise.all([Api.flashcards(state.subject.id), Api.documents(state.subject.id)]);
    state.cards = cards;
    state.readyDocs = docs.filter((d) => d.status === "ready").length;
    buildDeck();
    draw();
  } catch (error) {
    render(view, errorState(error));
  }
}

async function setMastered(card, value) {
  const previous = card.mastered;
  card.mastered = value;
  draw();
  try {
    await Api.setMastered(card.id, value);
    if (value && !state.hideMastered && state.mode === "study" && state.idx < state.deckIds.length - 1) {
      /* stay on the card so the learner sees the change; they navigate when ready */
    }
  } catch (error) {
    card.mastered = previous;
    draw();
    toast.error(error.message);
  }
}

const go = (delta) => {
  const next = state.idx + delta;
  if (next < 0 || next >= state.deckIds.length) return;
  state.idx = next;
  state.flipped = false;
  draw();
  $("#fc")?.focus({ preventScroll: true });
};
const flip = () => {
  state.flipped = !state.flipped;
  const fc = $("#fc");
  if (fc) {
    fc.classList.toggle("is-flipped", state.flipped);
    fc.setAttribute("aria-label", `Flashcard. ${state.flipped ? "Showing the answer." : "Showing the question."} Press to flip.`);
    $(".fc-front", fc).toggleAttribute("aria-hidden", false);
    $(".fc-back", fc).toggleAttribute("aria-hidden", false);
    (state.flipped ? $(".fc-front", fc) : $(".fc-back", fc)).setAttribute("aria-hidden", "true");
    (state.flipped ? $(".fc-back", fc) : $(".fc-front", fc)).removeAttribute("aria-hidden");
  }
};

async function generate(button) {
  if (state.generating) return;
  if (state.cards.length) {
    const ok = await confirmDialog({
      title: "Regenerate flashcards?",
      message: `This replaces your current ${plural(state.cards.length, "card")} and resets your mastered progress. If generation fails, your existing cards are kept.`,
      confirmLabel: "Regenerate",
    });
    if (!ok) return;
  }
  state.generating = true;
  const before = state.cards.length;
  const result = await runGeneration(button, () => Api.generateFlashcards(state.subject.id), {
    onStart: () => before === 0 && render(view, busyCard("Creating your flashcards…")),
  });
  state.generating = false;
  if (result) {
    state.cards = await Api.flashcards(state.subject.id);
    state.hideMastered = false;
    buildDeck();
    toast.success(`Generated ${plural(result.generated, "flashcard")}.`);
  }
  draw();
}

onAction(view, {
  retry: load,
  generate,
  flip,
  prev: () => go(-1),
  next: () => go(1),
  master: () => {
    const card = byId(state.deckIds[state.idx]);
    if (card) setMastered(card, !card.mastered);
  },
  "master-id": (b) => {
    const card = byId(b.dataset.id);
    if (card) setMastered(card, !card.mastered);
  },
  shuffle: () => {
    buildDeck({ shuffle: true });
    draw();
    toast("Deck shuffled.", { timeout: 1500 });
  },
  "show-all": () => {
    state.hideMastered = false;
    buildDeck();
    draw();
  },
});
onAction(actions, {
  generate,
  mode(b) {
    state.mode = b.dataset.mode;
    if (state.mode === "study") buildDeck({ keepCurrent: true });
    draw();
  },
});
view.addEventListener("change", (event) => {
  if (event.target.dataset.action === "hide-mastered") {
    state.hideMastered = event.target.checked;
    buildDeck({ keepCurrent: true });
    draw();
    $('[data-action="hide-mastered"]')?.focus();
  }
});
view.addEventListener("input", debounce((event) => {
  if (event.target.id === "card-search") {
    state.query = event.target.value.trim();
    const pos = event.target.selectionStart;
    draw();
    const input = $("#card-search");
    input.focus();
    input.setSelectionRange(pos, pos);
  }
}, 150));

// keyboard shortcuts (study mode only, never while typing)
document.addEventListener("keydown", (event) => {
  if (state.mode !== "study" || !state.cards.length || event.metaKey || event.ctrlKey || event.altKey) return;
  if (event.target.closest("input, textarea, select, dialog, .modal")) return;
  if (event.key === "ArrowRight") { event.preventDefault(); go(1); }
  else if (event.key === "ArrowLeft") { event.preventDefault(); go(-1); }
  else if (event.key === " " && event.target.id !== "fc" && !event.target.closest("button, a, summary")) { event.preventDefault(); flip(); }
  else if (event.key.toLowerCase() === "m" && !event.target.closest("button, a")) {
    const card = byId(state.deckIds[state.idx]);
    if (card) setMastered(card, !card.mastered);
  }
});

// swipe on touch devices
let touchX = null;
view.addEventListener("pointerdown", (event) => {
  if (event.pointerType === "touch" && event.target.closest("#stage")) touchX = event.clientX;
});
view.addEventListener("pointerup", (event) => {
  if (touchX === null) return;
  const dx = event.clientX - touchX;
  touchX = null;
  if (Math.abs(dx) > 60) go(dx < 0 ? 1 : -1);
});
view.addEventListener("pointercancel", () => (touchX = null));

shell.onSubjectChange((subject) => {
  state.subject = subject;
  state.idx = 0;
  state.query = "";
  state.hideMastered = false;
  state.mode = "study";
  load();
});
await load();
