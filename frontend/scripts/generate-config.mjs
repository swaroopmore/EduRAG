#!/usr/bin/env node
/**
 * Vercel build step: bakes the API URL into js/config.js from the EDURAG_API_URL
 * environment variable. Without the variable the file is left untouched and the
 * built-in default (the existing Railway backend) is used.
 *
 *   EDURAG_API_URL=https://your-backend.up.railway.app node scripts/generate-config.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const target = join(dirname(fileURLToPath(import.meta.url)), "..", "js", "config.js");
const raw = (process.env.EDURAG_API_URL || "").trim();

if (!raw) {
  console.log("EDURAG_API_URL not set - keeping the default API URL in js/config.js");
  process.exit(0);
}

let url;
try {
  url = new URL(raw);
} catch {
  console.error(`EDURAG_API_URL is not a valid URL: ${raw}`);
  process.exit(1);
}
const local = ["localhost", "127.0.0.1"].includes(url.hostname);
if (url.protocol !== "https:" && !local) {
  console.error("EDURAG_API_URL must use https:// (http:// is only allowed for localhost).");
  process.exit(1);
}

const value = url.origin; // strips paths, credentials and trailing slashes
const source = readFileSync(target, "utf8");
const pattern = /const BUILD_API_URL = ".*?";/;
if (!pattern.test(source)) {
  console.error("Could not find the BUILD_API_URL line in js/config.js");
  process.exit(1);
}
writeFileSync(target, source.replace(pattern, `const BUILD_API_URL = ${JSON.stringify(value)};`));
console.log(`API URL set to ${value}`);
