/**
 * Minimal, safe Markdown renderer for AI output.
 *
 * Safety model: the source text is HTML-escaped FIRST; markup is then re-created
 * only from a fixed set of tags we generate ourselves. Raw HTML from the model can
 * never reach the DOM, and links are restricted to http(s)/mailto.
 */
import { escapeHtml } from "./utils.js";

const SAFE_URL = /^(https?:\/\/|mailto:)[^\s<>"']+$/i;

function inline(text, citations) {
  const stash = [];
  const hold = (htmlFragment) => `\u0000${stash.push(htmlFragment) - 1}\u0000`;

  // `code` first so its contents are left alone
  let out = text.replace(/`([^`\n]+)`/g, (_m, code) => hold(`<code>${code}</code>`));

  // [text](url)
  out = out.replace(/\[([^\]\n]+)\]\(([^)\s]+)\)/g, (match, label, url) => {
    const target = url.replace(/&amp;/g, "&");
    if (!SAFE_URL.test(target)) return label; // unsafe scheme -> plain text
    return hold(`<a href="${escapeHtml(target)}" target="_blank" rel="noopener noreferrer nofollow">${label}</a>`);
  });

  // [n] citation markers
  if (citations) {
    out = out.replace(/\[(\d{1,2})\]/g, (match, n) =>
      citations.has(Number(n))
        ? hold(`<a class="cite" href="#source-${n}" data-cite="${n}" role="button" aria-label="Source ${n}">${n}</a>`)
        : match
    );
  }

  out = out
    .replace(/\*\*([^*\n]+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^\w])__([^_\n]+?)__(?=[^\w]|$)/g, "$1<strong>$2</strong>")
    .replace(/(^|[^*\w])\*([^*\s][^*\n]*?)\*(?=[^*\w]|$)/g, "$1<em>$2</em>")
    .replace(/(^|[^\w])_([^_\s][^_\n]*?)_(?=[^\w]|$)/g, "$1<em>$2</em>")
    .replace(/~~([^~\n]+?)~~/g, "<del>$1</del>");

  return out.replace(/\u0000(\d+)\u0000/g, (_m, i) => stash[Number(i)]);
}

const isTableSeparator = (line) => /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(line);
const splitRow = (line) => line.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());

/**
 * @param {string} source
 * @param {{citations?: number[]}} [options]  refs that may be turned into [n] chips
 */
export function renderMarkdown(source, options = {}) {
  const citations = options.citations ? new Set(options.citations) : null;
  const codeBlocks = [];

  let text = String(source ?? "").replace(/\r\n?/g, "\n");
  // fenced code blocks
  text = text.replace(/```[\w+-]*\n([\s\S]*?)(?:```|$)/g, (_m, code) => {
    codeBlocks.push(`<pre><code>${escapeHtml(code.replace(/\n$/, ""))}</code></pre>`);
    return `\n\u0001${codeBlocks.length - 1}\u0001\n`;
  });

  const lines = escapeHtml(text).split("\n");
  const out = [];
  let paragraph = [];
  const flush = () => {
    if (paragraph.length) {
      out.push(`<p>${inline(paragraph.join("<br>"), citations)}</p>`);
      paragraph = [];
    }
  };

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) { flush(); continue; }

    const block = /^\u0001(\d+)\u0001$/.exec(trimmed);
    if (block) { flush(); out.push(codeBlocks[Number(block[1])]); continue; }

    const heading = /^(#{1,6})\s+(.*)$/.exec(trimmed);
    if (heading) {
      flush();
      const level = Math.min(heading[1].length + 1, 5); // keep h1 for the page title
      out.push(`<h${level}>${inline(heading[2], citations)}</h${level}>`);
      continue;
    }

    if (/^([-*_])(\s*\1){2,}$/.test(trimmed)) { flush(); out.push("<hr>"); continue; }

    if (/^&gt;\s?/.test(trimmed)) {
      flush();
      const quote = [];
      while (i < lines.length && /^\s*&gt;\s?/.test(lines[i])) {
        quote.push(lines[i].replace(/^\s*&gt;\s?/, ""));
        i += 1;
      }
      i -= 1;
      out.push(`<blockquote>${inline(quote.join("<br>"), citations)}</blockquote>`);
      continue;
    }

    // table
    if (trimmed.includes("|") && i + 1 < lines.length && isTableSeparator(lines[i + 1]) && trimmed.includes("|")) {
      flush();
      const head = splitRow(trimmed);
      i += 2;
      const rows = [];
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
        rows.push(splitRow(lines[i]));
        i += 1;
      }
      i -= 1;
      out.push(
        `<table><thead><tr>${head.map((c) => `<th>${inline(c, citations)}</th>`).join("")}</tr></thead><tbody>` +
          rows.map((r) => `<tr>${r.map((c) => `<td>${inline(c, citations)}</td>`).join("")}</tr>`).join("") +
          "</tbody></table>"
      );
      continue;
    }

    // lists (supports one level of nesting via indentation)
    const listItem = /^(\s*)([-*+]|\d+[.)])\s+(.*)$/.exec(line);
    if (listItem) {
      flush();
      const items = [];
      while (i < lines.length) {
        const m = /^(\s*)([-*+]|\d+[.)])\s+(.*)$/.exec(lines[i]);
        if (!m) break;
        items.push({ indent: m[1].replace(/\t/g, "  ").length, ordered: /\d/.test(m[2]), text: m[3] });
        i += 1;
      }
      i -= 1;
      out.push(buildList(items, citations));
      continue;
    }

    paragraph.push(trimmed);
  }
  flush();
  return out.join("\n");
}

function buildList(items, citations) {
  const baseIndent = Math.min(...items.map((it) => it.indent));
  let html = "";
  const stack = []; // open list tags
  let previousIndent = baseIndent;

  const open = (item) => {
    const tag = item.ordered ? "ol" : "ul";
    stack.push(tag);
    html += `<${tag}>`;
  };
  items.forEach((item, index) => {
    if (index === 0) open(item);
    else if (item.indent > previousIndent) open(item);
    else {
      html += "</li>";
      if (item.indent < previousIndent && stack.length > 1) {
        html += `</${stack.pop()}></li>`;
      }
    }
    html += `<li>${inline(item.text, citations)}`;
    previousIndent = item.indent;
  });
  html += "</li>";
  while (stack.length) html += `</${stack.pop()}>${stack.length ? "</li>" : ""}`;
  return html;
}

/** Plain text version (for copy / download of a rendered answer keeps original markdown, so this is only for search & reading time). */
export function stripMarkdown(source) {
  return String(source ?? "")
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/[`*_>#~-]+/g, " ")
    .replace(/\[(.*?)\]\((.*?)\)/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}
