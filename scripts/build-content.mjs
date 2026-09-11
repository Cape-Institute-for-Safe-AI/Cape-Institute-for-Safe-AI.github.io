#!/usr/bin/env node
// Cape Institute for Safe AI — structured content renderer
//
// The programs, events, and research pages (and the abbreviated sections on
// capacity-building.html) are rendered from ./content/*.json. GitHub Pages
// serves this repo with no build step, so the rendered markup is committed
// into the HTML files between marker comments:
//
//   <!-- content:NAME:start -->
//   ...generated...
//   <!-- content:NAME:end -->
//
// Edit content/*.json, then run:
//
//   node scripts/build-content.mjs          # rewrite the marked regions
//   node scripts/build-content.mjs --check  # exit 1 if committed HTML is stale
//
// Event table thumbnails live in assets/images/events/thumbs/ (96px webp) and
// program cards use 800px variants from assets/images/programs/800/; see
// README.md for how they were produced.
//
// Rendering rules (not data edits): archive rows with attendance below
// MIN_ARCHIVE_ATTENDANCE are omitted; the archive shows ARCHIVE_PAGE_SIZE
// rows and reveals the same number again per click (assets/js/main.js).

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const CHECK = process.argv.includes("--check");

const load = (name) =>
  JSON.parse(readFileSync(join(ROOT, "content", `${name}.json`), "utf8"));

const programs = load("programs");
const research = load("research");

const MIN_ARCHIVE_ATTENDANCE = 5;
const ARCHIVE_PAGE_SIZE = 10;
const HIGHLIGHT_COUNT = 3;

// Events with a recorded attendance under the threshold are dropped from the
// rendered pages; unknown attendance (null) is kept.
const events = load("events").filter(
  (event) => event.attendanceCount == null || event.attendanceCount >= MIN_ARCHIVE_ATTENDANCE,
);

// --------------------------------------------------------------- helpers

const escape = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

const titleCase = (value) =>
  String(value ?? "")
    .split("_")
    .filter(Boolean)
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Matches date-fns "MMM d, yyyy" for the date-only ISO strings in the data.
function formatDate(iso) {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso ?? "");
  if (!match) return null;
  return `${MONTHS[Number(match[2]) - 1]} ${Number(match[3])}, ${match[1]}`;
}

// Program card images: 800px variant for cards, full-size for the featured
// slot on wide screens.
function programImage(program, { eager = false, sizes }) {
  const full = program.image.url;
  const small = full.replace("assets/images/programs/", "assets/images/programs/800/");
  return `<img src="${escape(small)}" srcset="${escape(small)} 800w, ${escape(full)} 1600w" sizes="${sizes}" alt="${escape(program.image.alt || program.name)}"${eager ? ' fetchpriority="high"' : ' loading="lazy"'} decoding="async" />`;
}

const plural = (count, word) => `${count.toLocaleString("en-ZA")} ${word}${count === 1 ? "" : "s"}`;

const isHttp = (url) => /^https?:\/\//.test(url ?? "");

// Lucide icon paths, inlined so pages stay dependency-free.
const ICONS = {
  calendar:
    '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
  pin: '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
  users:
    '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><path d="M16 3.128a4 4 0 0 1 0 7.744"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><circle cx="9" cy="7" r="4"/>',
  external:
    '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
};

const icon = (name) =>
  `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name]}</svg>`;

const fact = (name, text) => `<li class="fact">${icon(name)}<span>${escape(text)}</span></li>`;

const badge = (value) => `<span class="tag-badge">${escape(titleCase(value))}</span>`;

const EVENT_FALLBACK = "assets/images/mark.png";
const EVENT_THUMB_FALLBACK = "assets/images/events/thumbs/fallback-mark.webp";
const thumbFor = (image) =>
  image?.url ? image.url.replace("assets/images/events/", "assets/images/events/thumbs/") : EVENT_THUMB_FALLBACK;

// --------------------------------------------------------------- programs

// Mirrors the legacy AISSA ProgramCard: image header, type badge, title,
// clamped description, participants count, optional "Visit website" button.
function programCard(program, { variant = "grid", eager = false, text = true } = {}) {
  const featured = variant === "featured";
  const description = String(program.description ?? "").trim();
  const sizes = featured
    ? "(max-width: 900px) 100vw, 60vw"
    : variant === "row"
      ? "(max-width: 700px) 100vw, 20vw"
      : "(max-width: 700px) 100vw, (max-width: 900px) 50vw, 33vw";
  const website = isHttp(program.websiteUrl) ? program.websiteUrl : null;
  const logo =
    featured && program.slug === "cai-research-fellowship-2026"
      ? `<a class="card__logo" href="${escape(website)}" target="_blank" rel="noopener" aria-label="Cooperative AI Research Fellowship website"><img src="assets/images/partners/cairf-logo.webp" alt="Cooperative AI Research Fellowship logo" loading="lazy" /></a>`
      : "";

  return `<article class="card card--media${featured ? " card--featured" : ""}${variant === "row" ? " card--row" : ""}">
  <div class="card__media">
    ${programImage(program, { eager, sizes })}${logo}
  </div>
  <div class="card__body">
    ${badge(program.type)}
    <h3 class="card__title">${escape(program.name)}</h3>
    ${text ? `<p class="card__text card__text--clamp">${escape(description)}</p>
    <button type="button" class="card__more" data-card-more hidden aria-expanded="false">Read more <span class="arrow">&darr;</span></button>` : ""}
    <div class="card__footer">
      <ul class="facts">${program.totalParticipants ? fact("users", plural(program.totalParticipants, "participant")) : ""}</ul>
      ${website ? `<a class="btn btn--small" href="${escape(website)}" target="_blank" rel="noopener">Visit website ${icon("external")}</a>` : ""}
    </div>
  </div>
</article>`;
}

// Legacy AISSA ProgramsSection: first program large, up to three more
// stacked beside it as horizontal cards. Used on capacity-building.html
// (the home page links out to this instead of embedding cards).
function programsFeatured({ text = true } = {}) {
  const [featured, ...rest] = programs.slice(0, 4);
  return `<div class="featured-grid">
${programCard(featured, { variant: "featured", eager: true, text })}
  <div class="featured-grid__stack">
${rest.map((program) => programCard(program, { variant: "row", text })).join("\n")}
  </div>
</div>`;
}

const programsGrid = () =>
  `<div class="card-grid card-grid--media">\n${programs.map((program) => programCard(program)).join("\n")}\n</div>`;

// --------------------------------------------------------------- events

// Mirrors the legacy AISSA EventCard: image header (falls back to the mark),
// type badge, name, date / location / attendance facts.
function eventCard(event) {
  const src = event.image?.url ?? EVENT_FALLBACK;
  const fallback = !event.image?.url;
  const date = formatDate(event.eventDate);
  return `<article class="card card--media">
  <div class="card__media${fallback ? " card__media--fallback" : ""}">
    <img src="${escape(src)}" alt="${escape(event.image?.alt || event.name)}" loading="lazy" decoding="async" />
  </div>
  <div class="card__body">
    ${badge(event.type)}
    <h3 class="card__title">${escape(event.name)}</h3>
    <ul class="facts">
      ${date ? fact("calendar", date) : ""}
      ${event.location ? fact("pin", event.location) : ""}
      ${event.attendanceCount ? fact("users", plural(event.attendanceCount, "attendee")) : ""}
    </ul>
  </div>
</article>`;
}

const eventsHighlighted = () =>
  `<div class="card-grid card-grid--media">\n${events.slice(0, HIGHLIGHT_COUNT).map(eventCard).join("\n")}\n</div>`;

// Mirrors the legacy AISSA EventTable for everything after the highlights.
function eventsTable() {
  const archive = events.slice(HIGHLIGHT_COUNT);
  const rows = archive
    .map(
      (event, index) => `    <tr${index >= ARCHIVE_PAGE_SIZE ? ' class="archive-row is-hidden"' : ' class="archive-row"'}>
      <td>
        <div class="table-title">
          <img class="table-thumb" src="${escape(thumbFor(event.image))}" alt="" loading="lazy" />
          <span>${escape(event.name)}</span>
        </div>
      </td>
      <td class="nowrap">${badge(event.type)}</td>
      <td class="nowrap">${escape(formatDate(event.eventDate) ?? "TBD")}</td>
      <td>${escape(event.location || "TBD")}</td>
    </tr>`,
    )
    .join("\n");

  return `<div class="table-shell">
  <table class="data-table">
    <thead>
      <tr>
        <th>Event</th>
        <th>Type</th>
        <th>Date</th>
        <th>Location</th>
      </tr>
    </thead>
    <tbody>
${rows}
    </tbody>
  </table>
</div>
${archive.length > ARCHIVE_PAGE_SIZE ? `<div class="archive-more">
  <button type="button" class="btn is-secondary" data-archive-more data-archive-step="${ARCHIVE_PAGE_SIZE}">Show ${ARCHIVE_PAGE_SIZE} more <span class="arrow">&darr;</span></button>
  <span class="mono-label" data-archive-count>${ARCHIVE_PAGE_SIZE} of ${archive.length}</span>
</div>` : ""}`;
}

// --------------------------------------------------------------- research

// Mirrors the legacy AISSA ResearchTable.
function researchTable() {
  const rows = research
    .map((item) => {
      const url = isHttp(item.arxivLink)
        ? item.arxivLink
        : item.doi
          ? `https://doi.org/${item.doi}`
          : null;
      const venue = item.acceptedVenue || titleCase(item.venueType) || "-";
      const authors = item.authors.filter(Boolean).join(", ") || "-";
      const items = item.items?.length
        ? `<ul class="table-sublist">${item.items.map((t) => `<li>${escape(t)}</li>`).join("")}</ul>`
        : "";
      return `    <tr>
      <td><span class="table-title">${escape(item.title)}</span>${items}</td>
      <td class="nowrap">${badge(item.status)}</td>
      <td>${escape(authors)}</td>
      <td>${escape(venue)}</td>
      <td class="num">${url ? `<a class="table-link" href="${escape(url)}" target="_blank" rel="noopener">Open ${icon("external")}</a>` : "-"}</td>
    </tr>`;
    })
    .join("\n");

  return `<div class="table-shell">
  <table class="data-table">
    <thead>
      <tr>
        <th>Research</th>
        <th>Status</th>
        <th>Authors</th>
        <th>Venue</th>
        <th class="num">Link</th>
      </tr>
    </thead>
    <tbody>
${rows}
    </tbody>
  </table>
</div>`;
}

// --------------------------------------------------------------- apply

const REGIONS = {
  "capacity-building.html": {
    "programs-featured": programsFeatured,
    "events-highlighted": eventsHighlighted,
  },
  "programs.html": { "programs-grid": programsGrid },
  "events.html": { "events-highlighted": eventsHighlighted, "events-table": eventsTable },
  "research.html": { "research-table": researchTable },
};

let stale = [];

for (const [file, regions] of Object.entries(REGIONS)) {
  const path = join(ROOT, file);
  const original = readFileSync(path, "utf8");
  let updated = original;

  for (const [name, render] of Object.entries(regions)) {
    const pattern = new RegExp(
      `(<!-- content:${name}:start -->)[\\s\\S]*?(<!-- content:${name}:end -->)`,
    );
    if (!pattern.test(updated)) {
      console.error(`${file}: missing markers for region "${name}"`);
      process.exit(1);
    }
    updated = updated.replace(pattern, (_, start, end) => `${start}\n${render()}\n${end}`);
  }

  if (updated !== original) {
    stale.push(file);
    if (!CHECK) {
      writeFileSync(path, updated);
      console.log(`updated ${file}`);
    }
  }
}

if (CHECK) {
  if (stale.length) {
    console.error(`stale: ${stale.join(", ")} — run node scripts/build-content.mjs`);
    process.exit(1);
  }
  console.log("content regions are up to date");
} else if (!stale.length) {
  console.log("nothing to update");
}
