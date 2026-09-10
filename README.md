# Cape Institute for Safe AI

Static site for the Cape Institute for Safe AI, deployed via GitHub Pages
straight from the repo root. No build step: every `.html` file is served as-is.

## Structure

```
index.html              — landing page (hero, about, research, capacity
                           building, team, contact)
research.html           — worldview / research bets + research outputs table
capacity-building.html  — intro, featured programs, highlighted events,
                           co-working space, partners
programs.html           — all programs (card grid)
events.html             — highlighted events + full event archive table
team.html, workspace.html, get-involved.html, privacy.html
assets/css/style.css    — all styling
assets/js/main.js       — nav collapse/toggle, footer year, term popups
assets/fonts/           — Axion.otf (display font)
assets/images/          — logo, illustrations, team photos, partner logos,
                           programs/ and events/ imagery
content/                — structured data for programs, events, research
scripts/                — content renderer + asset-generation helpers
```

## Structured content (programs, events, research)

Program cards, event cards, the event archive table, and the research outputs
table are rendered from JSON rather than hand-edited:

```
content/programs.json
content/events.json
content/research.json
```

`scripts/build-content.mjs` renders these into the HTML files between marker
comments (`<!-- content:NAME:start -->` … `<!-- content:NAME:end -->`) in
`capacity-building.html`, `programs.html`, `events.html`, and `research.html`.
The rendered markup is committed, so Pages needs no build step.

To add or edit an entry, change the JSON and re-run:

```
node scripts/build-content.mjs          # rewrite the marked regions
node scripts/build-content.mjs --check  # exit 1 if committed HTML is stale
```

Requires Node 20+. Only the marked regions are touched; everything else in
those files is ordinary hand-edited HTML.

### Images

- Program images: `assets/images/programs/<slug>.webp`, referenced from
  `programs.json` (`image.url`).
- Event images: `assets/images/events/<slug>.webp` (card size) plus a 96px
  square thumbnail at `assets/images/events/thumbs/<slug>.webp` for the
  archive table. The renderer derives the thumbnail path from `image.url`, so
  both files need to exist. Events with `"image": null` fall back to the CISAI
  mark (`assets/images/mark.png` / `thumbs/fallback-mark.webp`).
- Thumbnails were produced with [sharp](https://sharp.pixelplumbing.com/):
  `resize(96, 96, { fit: "cover" }).webp({ quality: 78 })`. Any equivalent
  tool is fine.

The programs, events, and research data were carried over from the
predecessor organisation's site (AI Safety South Africa).

## Contact form

The "Reach out" form on `index.html` posts to Formspree (form ID `mvzjylbw`)
via `@formspree/ajax`, loaded from unpkg at the bottom of the page. Submissions
are emailed to the Formspree account that owns that form. No server-side code
in this repo is involved; to change the destination, update the form in the
Formspree dashboard or swap the ID in `index.html`.

## Local preview

No build step required — open any `.html` file in a browser, or serve the
folder with any static server, e.g.:

```
python3 -m http.server 8000
```
