import { applyTheme } from "../core/shell.js";
import { isSignedIn } from "../core/auth.js";

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

// theme
$("[data-theme-toggle]").addEventListener("click", () => {
  applyTheme(document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark");
});

// signed-in visitors go straight to their dashboard
if (isSignedIn()) {
  $$("[data-auth-hide]").forEach((n) => (n.hidden = true));
  $$("[data-auth-cta]").forEach((n) => {
    n.href = "pages/dashboard.html";
    const icon = n.querySelector(".bi");
    n.childNodes.forEach((c) => c.nodeType === 3 && c.textContent.trim() && (c.textContent = "Open dashboard"));
    if (!n.textContent.trim()) n.textContent = "Open dashboard";
    if (icon && icon.className.includes("rocket")) icon.className = "bi bi-grid-1x2";
  });
}

// mobile menu
const burger = $("#burger");
const links = $("#l-links");
const setMenu = (open) => {
  links.classList.toggle("is-open", open);
  burger.setAttribute("aria-expanded", String(open));
  burger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  burger.firstElementChild.className = `bi bi-${open ? "x-lg" : "list"}`;
};
burger.addEventListener("click", () => setMenu(!links.classList.contains("is-open")));
links.addEventListener("click", (e) => e.target.closest("a") && setMenu(false));
document.addEventListener("keydown", (e) => e.key === "Escape" && setMenu(false));

// nav shadow on scroll
const nav = $("#nav");
const onScroll = () => nav.classList.toggle("is-scrolled", window.scrollY > 8);
onScroll();
window.addEventListener("scroll", onScroll, { passive: true });

// gentle reveal-on-scroll (skipped for reduced motion)
if (!matchMedia("(prefers-reduced-motion: reduce)").matches && "IntersectionObserver" in window) {
  const targets = $$(".l-feature, .l-steps .card, .l-trust-list li, .l-cta-card");
  targets.forEach((t) => t.classList.add("reveal"));
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  targets.forEach((t) => io.observe(t));
}
