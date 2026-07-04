# Cape Institute for Safe AI

Static one-page site for the Cape Institute for Safe AI, deployed via GitHub Pages
straight from the repo root.

## Structure

```
index.html              — the entire one-pager (hero, about, research,
                           capacity-building, team, contact)
assets/css/style.css    — all styling
assets/js/main.js       — mobile nav toggle + footer year
assets/fonts/           — Axion.otf (display font), see fonts/README.md
assets/images/          — logo, hero illustration, team photos, partner logos
```

## Content status

This is a first-pass layout. Most body copy is placeholder **Lorem Ipsum** —
search `index.html` for it and swap in real copy for:

- Hero headline & subhead
- About section paragraphs + 3-item list
- Research card titles/descriptions + publication links
- Capacity Building intro, stats (`[N]`), and program cards
- Contact email address (marked `[email@capeinstituteforsafeai.org]`)

Team member names, titles, photos, and social links are real (carried over
from the predecessor org, AI Safety South Africa) — only their bio blurbs are
placeholder text.

The contact form is a **visual placeholder only** — it has no backend wired up
yet (see the note under the form).

## Local preview

No build step required — just open `index.html` in a browser, or serve the
folder with any static server, e.g.:

```
python3 -m http.server 8000
```
