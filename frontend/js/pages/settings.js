import { Api } from "../core/api.js";
import { API_URL } from "../config.js";
import { mountShell, applyTheme, themePref } from "../core/shell.js";
import { loadUser, signOut } from "../core/auth.js";
import { $, html, render, formatDate } from "../core/utils.js";
import { errorState, onAction, toast, withLoading } from "../core/ui.js";

await mountShell({ page: "settings", title: "Settings" });
const view = $("#view");
let user;

function draw() {
  const pref = themePref();
  render(view, html`<div class="settings-grid">
    <section class="card" aria-labelledby="profile-title">
      <h2 class="card-title" id="profile-title">Profile</h2>
      <p class="card-sub" style="margin-bottom:var(--sp-4)">Member since ${formatDate(user.created_at)}</p>
      <form id="profile-form" class="stack" novalidate>
        <div class="field"><label for="full_name">Full name</label><input class="input" id="full_name" name="full_name" maxlength="100" value="${user.full_name}" autocomplete="name" required></div>
        <div class="field"><label for="email">Email</label><input class="input" id="email" value="${user.email}" disabled><span class="field-hint">Your email is your sign-in and can't be changed here.</span></div>
        <div class="alert alert-danger" role="alert" data-error hidden><i class="bi bi-exclamation-octagon-fill" aria-hidden="true"></i><div class="alert-body"></div></div>
        <div><button class="btn btn-primary" type="submit">Save changes</button></div>
      </form>
    </section>

    <section class="card" aria-labelledby="theme-title">
      <h2 class="card-title" id="theme-title">Appearance</h2>
      <p class="card-sub" style="margin-bottom:var(--sp-4)">Choose how EduRAG looks. “System” follows your device.</p>
      <div class="theme-options" role="radiogroup" aria-label="Theme">${[["light", "sun", "Light"], ["dark", "moon-stars", "Dark"], ["system", "circle-half", "System"]].map(([value, icon, label]) => html`<label class="theme-option ${pref === value ? "is-selected" : ""}"><input type="radio" name="theme" value="${value}" ${pref === value ? "checked" : ""}><i class="bi bi-${icon}" aria-hidden="true"></i><span>${label}</span></label>`)}</div>
    </section>

    <section class="card" aria-labelledby="pw-title">
      <h2 class="card-title" id="pw-title">Change password</h2>
      <p class="card-sub" style="margin-bottom:var(--sp-4)">Use at least 8 characters.</p>
      <form id="password-form" class="stack" novalidate>
        <div class="field"><label for="current_password">Current password</label><input class="input" id="current_password" name="current_password" type="password" autocomplete="current-password" required></div>
        <div class="field"><label for="new_password">New password</label><input class="input" id="new_password" name="new_password" type="password" autocomplete="new-password" required></div>
        <div class="field"><label for="confirm_password">Confirm new password</label><input class="input" id="confirm_password" name="confirm_password" type="password" autocomplete="new-password" required></div>
        <div class="alert alert-danger" role="alert" data-error hidden><i class="bi bi-exclamation-octagon-fill" aria-hidden="true"></i><div class="alert-body"></div></div>
        <div><button class="btn btn-primary" type="submit">Update password</button></div>
      </form>
    </section>

    <section class="card" aria-labelledby="conn-title">
      <h2 class="card-title" id="conn-title">Connection</h2>
      <p class="card-sub" style="margin-bottom:var(--sp-4)">EduRAG talks to its server at <code>${new URL(API_URL).host}</code>.</p>
      <div class="row-wrap"><button type="button" class="btn" data-action="check"><i class="bi bi-activity" aria-hidden="true"></i>Check connection</button><span class="small" id="conn-status" role="status"></span></div>
      <hr>
      <h3 class="small strong" style="margin-bottom:var(--sp-2)">Session</h3>
      <button type="button" class="btn btn-danger-ghost" data-signout><i class="bi bi-box-arrow-right" aria-hidden="true"></i>Sign out of this device</button>
    </section>
  </div>`);
}

function showError(form, message) {
  const box = $("[data-error]", form);
  $(".alert-body", box).textContent = message;
  box.hidden = false;
}

view.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  $("[data-error]", form).hidden = true;
  const submit = $('button[type="submit"]', form);

  if (form.id === "profile-form") {
    const name = form.full_name.value.trim().replace(/\s+/g, " ");
    if (!name) return showError(form, "Please enter your name.");
    await withLoading(submit, async () => {
      try {
        user = await Api.updateMe(name);
        await loadUser({ force: true });
        document.querySelectorAll("[data-user-name]").forEach((n) => (n.textContent = user.full_name));
        toast.success("Profile updated.");
      } catch (error) {
        showError(form, error.message);
      }
    });
  } else if (form.id === "password-form") {
    const { current_password, new_password, confirm_password } = form;
    if (!current_password.value) return showError(form, "Enter your current password.");
    if (new_password.value.length < 8) return showError(form, "Your new password must be at least 8 characters long.");
    if (new TextEncoder().encode(new_password.value).length > 72) return showError(form, "That password is too long (72 bytes maximum).");
    if (new_password.value !== confirm_password.value) return showError(form, "The new passwords don't match.");
    await withLoading(submit, async () => {
      try {
        await Api.changePassword(current_password.value, new_password.value);
        form.reset();
        toast.success("Password updated.");
      } catch (error) {
        showError(form, error.status === 400 || error.status === 401 ? "Your current password isn't correct." : error.message);
      }
    });
  }
});

view.addEventListener("change", (event) => {
  if (event.target.name === "theme") {
    applyTheme(event.target.value);
    view.querySelectorAll(".theme-option").forEach((o) => o.classList.toggle("is-selected", $("input", o).checked));
    document.querySelector("[data-theme-icon]")?.setAttribute("class", `bi bi-${document.documentElement.getAttribute("data-theme") === "dark" ? "sun" : "moon-stars"}`);
  }
});

onAction(view, {
  retry: init,
  async check(button) {
    const status = $("#conn-status");
    await withLoading(button, async () => {
      const started = performance.now();
      try {
        await Api.health();
        status.textContent = `Connected · ${Math.round(performance.now() - started)} ms`;
        status.style.color = "var(--success)";
      } catch (error) {
        status.textContent = error.message;
        status.style.color = "var(--danger)";
      }
    });
  },
});

async function init() {
  render(view, html`<div class="skeleton" style="height:220px" aria-hidden="true"></div>`);
  try {
    user = await loadUser({ force: true });
    draw();
  } catch (error) {
    render(view, errorState(error));
  }
}
await init();
