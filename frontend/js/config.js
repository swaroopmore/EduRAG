/**
 * Frontend runtime configuration.
 *
 * The API base URL is resolved in this order:
 *   1. BUILD_API_URL   - written at deploy time by `scripts/generate-config.mjs`
 *                        from the EDURAG_API_URL environment variable (Vercel).
 *   2. localhost dev   - http://localhost:8000 (override with
 *                        localStorage["edurag_api_url"] when developing).
 *   3. DEFAULT_API_URL - the existing production backend.
 */
const BUILD_API_URL = ""; // <- replaced by scripts/generate-config.mjs when EDURAG_API_URL is set
const DEFAULT_API_URL = "https://edurag-production-e7e9.up.railway.app";

const host = location.hostname;
const isLocal = host === "localhost" || host === "127.0.0.1" || host === "[::1]" || host.endsWith(".local");

function localOverride() {
  try {
    return localStorage.getItem("edurag_api_url") || "";
  } catch {
    return "";
  }
}

export const API_URL = (BUILD_API_URL || (isLocal ? localOverride() || "http://localhost:8000" : DEFAULT_API_URL)).replace(/\/+$/, "");

export const LIMITS = Object.freeze({
  // Mirrors the backend defaults (MAX_UPLOAD_MB / ALLOWED_FILE_TYPES / MAX_QUESTION_CHARS).
  // The server remains the source of truth and re-validates everything.
  maxUploadMb: 25,
  fileTypes: ["pdf", "txt", "docx", "pptx"],
  maxQuestionChars: 2000,
});
