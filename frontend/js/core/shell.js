/* Builds the app chrome (sidebar, top bar, drawer, bottom nav, subject picker) around <main id="main">. */
import { $, $$, el, html, raw, render, initials } from "./utils.js";
import { requireAuth, loadUser, cachedUser, signOut, takeFlash } from "./auth.js";
import { loadSubjects, pickSubject, rememberSubject } from "./subjects.js";
import { toast } from "./ui.js";

export const NAV = [
  { id: "dashboard", label: "Dashboard", icon: "grid-1x2", href: "dashboard.html", group: "Learn" },
  { id: "subjects", label: "Subjects", icon: "collection", href: "subjects.html", group: "Learn" },
  { id: "documents", label: "Documents", icon: "folder2-open", href: "documents.html", group: "Learn" },
  { id: "chat", label: "AI Chat", icon: "chat-square-text", href: "chat.html", group: "Study" },
  { id: "notes", label: "Notes", icon: "journal-text", href: "notes.html", group: "Study" },
  { id: "flashcards", label: "Flashcards", icon: "stack", href: "flashcards.html", group: "Study" },
  { id: "quiz", label: "Quiz", icon: "patch-question", href: "quizes.html", group: "Study" },
  { id: "planner", label: "Study Planner", icon: "calendar2-check", href: "studyplanner.html", group: "Study" },
  { id: "settings", label: "Settings", icon: "gear", href: "settings.html", group: "Account" },
];
const CURRENT = raw('aria-current="page"');
const BOTTOM = ["dashboard", "subjects", "documents", "chat"];

export function applyTheme(pref) {
  try {
    localStorage.setItem("edurag_theme", pref);
  } catch {
    /* ignore */
  }
  const dark = pref === "dark" || (pref === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
  const root = document.documentElement;
  root.setAttribute("data-theme", dark ? "dark" : "light");
  root.setAttribute("data-theme-pref", pref);
  $('meta[name="theme-color"]')?.setAttribute("content", dark ? "#0a0c18" : "#f5f6fb");
}
export const themePref = () => document.documentElement.getAttribute("data-theme-pref") || "system";

// Follow OS changes while the preference is "system".
matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", () => {
  if (themePref() === "system") applyTheme("system");
});

const SVG_DEFS = `<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>
  <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#5b5df0"/><stop offset="55%" stop-color="#8b5cf6"/><stop offset="100%" stop-color="#06b6d4"/></linearGradient>
</defs></svg>`;

const navLink = (item, current) =>
  html`<a href="${item.href}" ${item.id === current ? CURRENT : ""}><i class="bi bi-${item.icon}" aria-hidden="true"></i><span>${item.label}</span></a>`;

/**
 * @param {{page: string, title: string, subjects?: "none"|"required", fillHeight?: boolean}} options
 */
export async function mountShell({ page, title, subjects = "none", fillHeight = false }) {
  if (!requireAuth()) return new Promise(() => {}); // redirecting; never resolve
  const main = $("#main");
  const user = cachedUser();
  if (fillHeight) document.body.classList.add("fill-height");

  const groups = [...new Set(NAV.map((n) => n.group))];
  const app = el("div", { class: "app" });
  const sidebar = el("aside", { class: "sidebar", id: "sidebar", "aria-label": "Primary" });
  render(
    sidebar,
    html`<button type="button" class="btn btn-ghost btn-icon drawer-close" data-drawer-close aria-label="Close menu"><i class="bi bi-x-lg" aria-hidden="true"></i></button>
      <a class="brand" href="dashboard.html" aria-label="EduRAG home"><span class="brand-mark"><i class="bi bi-mortarboard-fill" aria-hidden="true"></i></span>EduRAG</a>
      <nav aria-label="Main">
        ${groups.map((g) => html`<div class="nav-label">${g}</div><div class="nav">${NAV.filter((n) => n.group === g).map((n) => navLink(n, page))}</div>`)}
      </nav>
      <div class="sidebar-foot">
        <div class="user-chip"><span class="avatar" data-user-initials aria-hidden="true">${initials(user?.full_name)}</span>
          <div class="meta truncate"><strong class="truncate" data-user-name>${user?.full_name || "Your account"}</strong><span class="truncate" data-user-email>${user?.email || ""}</span></div></div>
        <button type="button" class="btn btn-ghost btn-block" data-signout style="justify-content:flex-start;margin-top:var(--sp-2)"><i class="bi bi-box-arrow-right" aria-hidden="true"></i>Sign out</button>
      </div>`
  );

  const topbar = el("header", { class: "topbar" });
  render(
    topbar,
    html`<button type="button" class="btn btn-ghost btn-icon menu-btn" data-drawer-open aria-label="Open menu" aria-controls="sidebar" aria-expanded="false"><i class="bi bi-list" style="font-size:1.4rem" aria-hidden="true"></i></button>
      <a class="brand brand-mobile topbar-title" href="dashboard.html" aria-label="EduRAG home"><span class="brand-mark"><i class="bi bi-mortarboard-fill" aria-hidden="true"></i></span></a>
      <h1 class="topbar-page">${title}</h1>
      <div class="topbar-actions">
        <button type="button" class="btn btn-ghost btn-icon" data-theme-toggle aria-label="Toggle dark mode"><i class="bi bi-moon-stars" data-theme-icon aria-hidden="true"></i></button>
        <div class="user-menu-wrap">
          <button type="button" class="user-btn" data-user-menu aria-haspopup="menu" aria-expanded="false" aria-label="Account menu"><span class="avatar" data-user-initials>${initials(user?.full_name)}</span><span class="user-name small strong truncate" style="max-width:140px" data-user-name>${user?.full_name || ""}</span><i class="bi bi-chevron-down xs faint" aria-hidden="true"></i></button>
        </div>
      </div>`
  );

  const content = el("div", { class: "app-main" });
  const bottom = el("nav", { class: "bottomnav", "aria-label": "Quick navigation" });
  render(
    bottom,
    html`${BOTTOM.map((id) => {
      const item = NAV.find((n) => n.id === id);
      return html`<a href="${item.href}" ${id === page ? CURRENT : ""}><i class="bi bi-${item.icon}" aria-hidden="true"></i><span>${item.label === "AI Chat" ? "Chat" : item.label}</span></a>`;
    })}
      <button type="button" data-drawer-open aria-label="More"><i class="bi bi-three-dots" aria-hidden="true"></i><span>More</span></button>`
  );
  const backdrop = el("div", { class: "drawer-backdrop", hidden: true });

  // Build the DOM: move the page's <main> into the shell.
  main.classList.add("page");
  main.setAttribute("tabindex", "-1");
  content.append(topbar, main);
  app.append(sidebar, content);
  document.body.prepend(bottom);
  document.body.prepend(backdrop);
  document.body.prepend(app);
  document.body.prepend(el("a", { class: "skip-link", href: "#main", text: "Skip to content" }));
  document.body.insertAdjacentHTML("beforeend", SVG_DEFS);

  // ---- drawer
  let lastFocus = null;
  const setDrawer = (open) => {
    sidebar.classList.toggle("is-open", open);
    backdrop.hidden = !open;
    document.body.style.overflow = open ? "hidden" : "";
    $$("[data-drawer-open]").forEach((b) => b.setAttribute("aria-expanded", String(open)));
    if (open) {
      lastFocus = document.activeElement;
      $("a[aria-current], .nav a", sidebar)?.focus();
    } else if (lastFocus) lastFocus.focus?.();
  };
  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-drawer-open]")) setDrawer(true);
    else if (event.target.closest("[data-drawer-close]") || event.target === backdrop) setDrawer(false);
    else if (event.target.closest(".sidebar a")) setDrawer(false);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") { setDrawer(false); closeUserMenu(); }
  });
  matchMedia("(min-width: 1024px)").addEventListener?.("change", (e) => e.matches && setDrawer(false));

  // ---- theme toggle
  const themeIcon = $("[data-theme-icon]", topbar);
  const refreshThemeIcon = () => {
    const dark = document.documentElement.getAttribute("data-theme") === "dark";
    themeIcon.className = `bi bi-${dark ? "sun" : "moon-stars"}`;
    $("[data-theme-toggle]", topbar).setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
  };
  $("[data-theme-toggle]", topbar).addEventListener("click", () => {
    applyTheme(document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark");
    refreshThemeIcon();
  });
  refreshThemeIcon();

  // ---- user menu
  let menu = null;
  function closeUserMenu() {
    if (!menu) return;
    menu.remove();
    menu = null;
    $("[data-user-menu]", topbar).setAttribute("aria-expanded", "false");
  }
  $("[data-user-menu]", topbar).addEventListener("click", (event) => {
    event.stopPropagation();
    if (menu) return closeUserMenu();
    const u = cachedUser();
    menu = el("div", { class: "menu", role: "menu" });
    render(
      menu,
      html`<div style="padding:var(--sp-2) var(--sp-3)"><strong class="small">${u?.full_name || "Account"}</strong><div class="xs faint truncate">${u?.email || ""}</div></div><hr>
        <a href="settings.html" role="menuitem"><i class="bi bi-gear" aria-hidden="true"></i>Settings</a>
        <button type="button" role="menuitem" data-signout><i class="bi bi-box-arrow-right" aria-hidden="true"></i>Sign out</button>`
    );
    $(".user-menu-wrap", topbar).append(menu);
    $("[data-user-menu]", topbar).setAttribute("aria-expanded", "true");
    $("a, button", menu).focus();
  });
  document.addEventListener("click", (event) => {
    if (menu && !event.target.closest(".user-menu-wrap")) closeUserMenu();
    if (event.target.closest("[data-signout]")) signOut();
  });

  // ---- keep name/initials fresh (validates the token too)
  loadUser({ force: true })
    .then((u) => {
      $$("[data-user-name]").forEach((n) => (n.textContent = u.full_name));
      $$("[data-user-initials]").forEach((n) => (n.textContent = initials(u.full_name)));
      const email = $("[data-user-email]");
      if (email) email.textContent = u.email;
    })
    .catch(() => {});

  const flashMessage = takeFlash();
  if (flashMessage) toast.success(flashMessage);

  // ---- subject bar
  const controller = { main, subject: null, subjects: [], listeners: [] };
  controller.onSubjectChange = (fn) => controller.listeners.push(fn);

  if (subjects !== "none") {
    const bar = el("div", { class: "subject-bar", id: "subject-bar" });
    main.prepend(bar);
    try {
      controller.subjects = await loadSubjects();
    } catch (error) {
      controller.error = error;
    }
    controller.subject = pickSubject(controller.subjects);
    rememberSubject(controller.subject);

    const draw = () => {
      if (!controller.subjects.length) {
        bar.hidden = true;
        return;
      }
      bar.hidden = false;
      render(
        bar,
        html`<label for="subject-select"><i class="bi bi-folder2" aria-hidden="true"></i>Subject</label>
          <select id="subject-select" class="select" aria-label="Current subject">${controller.subjects.map((s) => html`<option value="${s.id}" ${s.id === controller.subject?.id ? "selected" : ""}>${s.name}</option>`)}</select>`
      );
      $("#subject-select", bar).addEventListener("change", (event) => {
        controller.subject = controller.subjects.find((s) => s.id === event.target.value);
        rememberSubject(controller.subject);
        const url = new URL(location.href);
        url.searchParams.set("subject", controller.subject.id);
        history.replaceState(null, "", url);
        controller.listeners.forEach((fn) => fn(controller.subject));
      });
    };
    draw();
    controller.redraw = draw;
  }
  return controller;
}
