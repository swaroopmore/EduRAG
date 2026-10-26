import { Api, token } from "../core/api.js";
import { redirectIfSignedIn } from "../core/auth.js";
import { applyTheme } from "../core/shell.js";
import { $ } from "../core/utils.js";

redirectIfSignedIn();

const form = $("#register-form");
const errorBox = $("#form-error");
const submit = $("#submit");
const meter = $("#strength");

function showError(message, field) {
  errorBox.querySelector(".alert-body").textContent = message;
  errorBox.hidden = false;
  if (field) {
    field.setAttribute("aria-invalid", "true");
    field.focus();
  }
}

function strength(password) {
  let score = 0;
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 1;
  if (/\d/.test(password) && /[^A-Za-z0-9]/.test(password)) score += 1;
  return password ? Math.max(1, score) : 0;
}
form.password.addEventListener("input", () => {
  meter.dataset.level = String(strength(form.password.value));
});

$("#toggle-password").addEventListener("click", (event) => {
  const show = form.password.type === "password";
  form.password.type = show ? "text" : "password";
  form.confirm.type = show ? "text" : "password";
  event.currentTarget.setAttribute("aria-pressed", String(show));
  event.currentTarget.setAttribute("aria-label", show ? "Hide password" : "Show password");
  event.currentTarget.firstElementChild.className = `bi bi-${show ? "eye-slash" : "eye"}`;
});
$("[data-theme-toggle]").addEventListener("click", () => {
  applyTheme(document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  for (const f of form.elements) f.removeAttribute?.("aria-invalid");

  const name = form.full_name.value.trim().replace(/\s+/g, " ");
  const email = form.email.value.trim();
  const password = form.password.value;

  if (!name) return showError("Please enter your name.", form.full_name);
  if (!/^\S+@\S+\.\S+$/.test(email)) return showError("Enter a valid email address.", form.email);
  if (password.length < 8) return showError("Your password must be at least 8 characters long.", form.password);
  if (new TextEncoder().encode(password).length > 72) return showError("That password is too long (72 bytes maximum).", form.password);
  if (password !== form.confirm.value) return showError("The two passwords don't match.", form.confirm);

  submit.classList.add("is-loading");
  submit.disabled = true;
  try {
    await Api.register(name, email, password);
    const data = await Api.login(email, password);
    token.set(data.access_token);
    location.replace("dashboard.html");
  } catch (error) {
    submit.classList.remove("is-loading");
    submit.disabled = false;
    showError(error.status === 409 ? "An account with that email already exists. Try signing in instead." : error.message, error.status === 409 ? form.email : null);
  }
});
