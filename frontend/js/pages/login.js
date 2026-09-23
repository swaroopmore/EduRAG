import { Api, token } from "../core/api.js";
import { redirectIfSignedIn, takeFlash } from "../core/auth.js";
import { applyTheme } from "../core/shell.js";
import { $, queryParam, safeNext } from "../core/utils.js";

redirectIfSignedIn();

const form = $("#login-form");
const errorBox = $("#form-error");
const submit = $("#submit");

const flashMessage = takeFlash();
if (flashMessage) showMessage(flashMessage, "info");

function showMessage(message, kind = "danger") {
  errorBox.className = `alert alert-${kind}`;
  errorBox.querySelector(".alert-body").textContent = message;
  errorBox.querySelector(".bi").className = `bi bi-${kind === "info" ? "info-circle-fill" : "exclamation-octagon-fill"}`;
  errorBox.hidden = false;
}

$("#toggle-password").addEventListener("click", (event) => {
  const input = $("#password");
  const show = input.type === "password";
  input.type = show ? "text" : "password";
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
  const email = form.email.value.trim();
  const password = form.password.value;

  form.email.removeAttribute("aria-invalid");
  form.password.removeAttribute("aria-invalid");
  if (!email || !/^\S+@\S+\.\S+$/.test(email)) {
    form.email.setAttribute("aria-invalid", "true");
    form.email.focus();
    return showMessage("Enter a valid email address.");
  }
  if (!password) {
    form.password.setAttribute("aria-invalid", "true");
    form.password.focus();
    return showMessage("Enter your password.");
  }

  submit.classList.add("is-loading");
  submit.disabled = true;
  try {
    const data = await Api.login(email, password);
    token.set(data.access_token);
    location.replace(safeNext(queryParam("next")));
  } catch (error) {
    submit.classList.remove("is-loading");
    submit.disabled = false;
    showMessage(error.status === 401 || error.status === 400 ? "That email and password don't match. Please try again." : error.message);
  }
});
