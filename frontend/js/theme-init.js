/* Runs synchronously in <head> so the correct theme is applied before first paint (no flash). */
(function () {
  try {
    var pref = localStorage.getItem("edurag_theme") || "system";
    var dark = pref === "dark" || (pref === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
    var root = document.documentElement;
    root.setAttribute("data-theme", dark ? "dark" : "light");
    root.setAttribute("data-theme-pref", pref);
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", dark ? "#0a0c18" : "#f5f6fb");
  } catch (e) {
    /* storage blocked - fall back to the light theme */
  }
})();
