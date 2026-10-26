/* Session handling: guards, current user, sign-out. */
import { Api, token, setUnauthorizedHandler } from "./api.js";
import { safeNext, queryParam } from "./utils.js";

const USER_KEY = "edurag_user";
const FLASH_KEY = "edurag_flash";

const loginUrl = (next) => {
  const here = location.pathname.split("/").pop() || "dashboard.html";
  const target = next ?? (here === "login.html" ? "" : here + location.search);
  return "login.html" + (target ? `?next=${encodeURIComponent(target)}` : "");
};

export function flash(message) {
  try {
    sessionStorage.setItem(FLASH_KEY, message);
  } catch {
    /* ignore */
  }
}
export function takeFlash() {
  try {
    const value = sessionStorage.getItem(FLASH_KEY);
    sessionStorage.removeItem(FLASH_KEY);
    return value;
  } catch {
    return null;
  }
}

export function clearSession() {
  token.clear();
  try {
    sessionStorage.removeItem(USER_KEY);
    localStorage.removeItem("current_subject_id");
    localStorage.removeItem("current_subject_name");
  } catch {
    /* ignore */
  }
}

let redirecting = false;
setUnauthorizedHandler(() => {
  if (redirecting) return;
  redirecting = true;
  clearSession();
  flash("Your session expired. Please sign in again.");
  location.replace(loginUrl());
});

export function isSignedIn() {
  return Boolean(token.get());
}

/** Protect a page: redirect to the login screen when there is no token. */
export function requireAuth() {
  if (!isSignedIn()) {
    redirecting = true;
    location.replace(loginUrl());
    return false;
  }
  return true;
}

export function redirectIfSignedIn() {
  if (isSignedIn()) location.replace(safeNext(queryParam("next")));
}

export function cachedUser() {
  try {
    return JSON.parse(sessionStorage.getItem(USER_KEY) || "null");
  } catch {
    return null;
  }
}

export async function loadUser({ force = false } = {}) {
  const cached = cachedUser();
  if (cached && !force) return cached;
  const user = await Api.me();
  try {
    sessionStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch {
    /* ignore */
  }
  return user;
}

export function signOut() {
  redirecting = true;
  clearSession();
  location.replace("login.html");
}
