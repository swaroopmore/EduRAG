import { Api } from "../core/api.js";
import { mountShell } from "../core/shell.js";
import { $, html, render, plural } from "../core/utils.js";
import { busyCard, confirmDialog, emptyState, errorState, noDocumentsState, noSubjectState, onAction, progressBar, runGeneration, skeletonList, toast } from "../core/ui.js";

const shell = await mountShell({ page: "planner", title: "Study Planner", subjects: "required" });
const view = $("#view");
const actions = $("#plan-actions");

const state = { subject: shell.subject, plan: [], readyDocs: 0, days: 7, filter: "all", generating: false };

const done = () => state.plan.filter((p) => p.completed).length;

function renderActions() {
  const has = state.plan.length > 0;
  render(actions, html`${state.readyDocs ? html`
    <div class="row"><label class="small strong muted" for="days">Length</label>
      <select class="select" id="days" style="width:auto;min-height:40px">${[3, 5, 7, 10, 14, 21, 30].map((d) => html`<option value="${d}" ${d === state.days ? "selected" : ""}>${d} days</option>`)}</select></div>
    <button type="button" class="btn ${has ? "" : "btn-primary"}" data-action="generate"><i class="bi bi-${has ? "arrow-repeat" : "stars"}" aria-hidden="true"></i>${has ? "Regenerate" : "Generate plan"}</button>` : ""}`);
}

function groupByDay(items) {
  const map = new Map();
  for (const item of items) {
    if (!map.has(item.day)) map.set(item.day, []);
    map.get(item.day).push(item);
  }
  return [...map.entries()].sort((a, b) => a[0] - b[0]);
}

function session(p) {
  return html`<li class="session ${p.completed ? "is-done" : ""}">
    <button type="button" class="check-btn" role="checkbox" aria-checked="${p.completed}" data-action="toggle" data-id="${p.id}" aria-label="Mark “${p.title}” as ${p.completed ? "not done" : "done"}"><i class="bi bi-check-lg" aria-hidden="true"></i></button>
    <div class="grow"><h2 class="session-title">${p.title}</h2><p class="small muted">${p.description}</p>
      <div class="chips" style="margin-top:var(--sp-2)">${p.time ? html`<span class="chip"><i class="bi bi-clock" aria-hidden="true"></i>${p.time}</span>` : ""}${p.duration ? html`<span class="chip"><i class="bi bi-hourglass-split" aria-hidden="true"></i>${p.duration}</span>` : ""}</div></div>
  </li>`;
}

function draw() {
  renderActions();
  if (!state.subject) return render(view, noSubjectState());
  if (!state.plan.length) {
    if (!state.readyDocs) return render(view, noDocumentsState(state.subject.id));
    return render(view, emptyState({
      icon: "calendar2-check",
      title: "No study plan yet",
      text: `Pick how many days you have, then generate a day-by-day plan from your ${plural(state.readyDocs, "ready document")}.`,
      actions: [{ action: "generate", label: "Generate plan", icon: "stars", primary: true }],
    }));
  }
  const total = state.plan.length;
  const completed = done();
  const quote = state.plan.find((p) => p.quote)?.quote;
  const items = state.filter === "todo" ? state.plan.filter((p) => !p.completed) : state.plan;
  const days = groupByDay(items);
  render(view, html`<div class="plan-layout">
    <section class="card plan-summary" aria-label="Progress">
      <div class="row-wrap" style="justify-content:space-between"><div><div class="stat-value tnum">${completed}<span class="muted" style="font-size:1rem">/${total}</span></div><div class="small muted">sessions completed</div></div>
        <span class="badge ${completed === total ? "badge-success" : "badge-primary"}">${completed === total ? "Plan complete" : `${Math.round((completed / total) * 100)}%`}</span></div>
      ${progressBar((completed / total) * 100, { cls: completed === total ? "is-success" : "", label: "Sessions completed" })}
      ${quote ? html`<blockquote class="plan-quote">“${quote}”</blockquote>` : ""}
      <div class="segmented" role="group" aria-label="Filter sessions"><button type="button" data-action="filter" data-f="all" aria-pressed="${state.filter === "all"}">All</button><button type="button" data-action="filter" data-f="todo" aria-pressed="${state.filter === "todo"}">Remaining ${total - completed}</button></div>
    </section>
    <ol class="plan-timeline">${days.length ? days.map(([day, list]) => html`<li class="plan-day"><div class="day-marker"><span>Day</span><strong>${day}</strong></div>
      <div class="card day-card"><ul class="stack-sm">${list.map(session)}</ul></div></li>`) : html`<li>${emptyState({ icon: "trophy", title: "All sessions done", text: "Everything on this plan is complete." })}</li>`}</ol>
  </div>`);
}

async function load() {
  render(actions, "");
  if (!state.subject) return draw();
  render(view, skeletonList(4));
  try {
    const [plan, docs] = await Promise.all([Api.plan(state.subject.id), Api.documents(state.subject.id)]);
    state.plan = plan;
    state.readyDocs = docs.filter((d) => d.status === "ready").length;
    if (plan.length) {
      const dayCount = new Set(plan.map((p) => p.day)).size;
      const allowed = [3, 5, 7, 10, 14, 21, 30];
      state.days = allowed.reduce((best, d) => (Math.abs(d - dayCount) < Math.abs(best - dayCount) ? d : best), 7);
    }
    draw();
  } catch (error) {
    render(view, errorState(error));
  }
}

async function generate(button) {
  if (state.generating) return;
  if (state.plan.length) {
    const ok = await confirmDialog({
      title: "Regenerate your plan?",
      message: `This replaces your current plan and resets completed sessions (${done()} of ${state.plan.length} done). If generation fails, your current plan is kept.`,
      confirmLabel: "Regenerate",
    });
    if (!ok) return;
  }
  state.generating = true;
  const before = state.plan.length;
  const result = await runGeneration(button, () => Api.generatePlan(state.subject.id, state.days), {
    onStart: () => before === 0 && render(view, busyCard("Building your study plan…")),
  });
  state.generating = false;
  if (result) {
    state.plan = await Api.plan(state.subject.id);
    state.filter = "all";
    toast.success(`Created a plan with ${plural(result.generated, "session")}.`);
  }
  draw();
}

const handlers = {
  retry: load,
  generate,
  filter: (b) => { state.filter = b.dataset.f; draw(); },
  async toggle(button) {
    const item = state.plan.find((p) => p.id === button.dataset.id);
    const previous = item.completed;
    item.completed = !previous;
    draw();
    try {
      await Api.setSessionDone(item.id, item.completed);
    } catch (error) {
      item.completed = previous;
      draw();
      toast.error(error.message);
    }
  },
};
onAction(view, handlers);
onAction(actions, handlers);
actions.addEventListener("change", (event) => {
  if (event.target.id === "days") state.days = Number(event.target.value);
});

shell.onSubjectChange((subject) => {
  state.subject = subject;
  state.filter = "all";
  load();
});
await load();
