# Changelog

## [0.18.0] - 2026-10-27

### Summary

Page heads gain the last legacy capotej.com parity items: a favicon
(inline-SVG data-URI with an emoji, matching legacy), the
`apple-mobile-web-app-capable` / `mobile-web-app-capable` standalone-app
metas, and `viewport-fit=cover` on the viewport. The favicon is a
`FAVICON` constant in build.py — any `<link rel="icon">` href works, so
a site can point it at `/assets/favicon.svg` or swap the emoji without
touching the shell.

### Changes

- ccdd8d4 feat(head): favicon (configurable FAVICON constant), mobile-web-app metas, viewport-fit=cover

## [0.17.0] - 2026-10-27

### Summary

Links and papers listings paginate at 15 entries per page (matching
legacy capotej.com/links), while the home listing and tag pages keep
their 5-per-page split. A fresh scaffold with a handful of entries is
unaffected — the page-size difference only shows as a listing grows.

### Changes

- 475bec5 feat(pagination): links/papers at 15 per page (legacy parity), ported from capotej.com

## [0.16.0] - 2026-10-27

### Summary

Papers become a pure link-log: the index renders entries exactly like
the links index — outbound `pdf_url` title link with the external-link
glyph, a citation line carrying the URL, arXiv id, and date, and the
note body beneath. The per-paper detail pages (`/papers/<slug>/`) are
gone; `pdf_url` is now required and the build fails loud when missing.
The papers index paginates like every other listing.

### Changes

- 453e443 feat(papers): link-log index, no detail pages, ported from capotej.com

## [0.15.0] - 2026-10-27

### Summary

Links-index entries gain a citation line and an external-link glyph:
the outbound title link now ends in a small arrow-box icon (inline
SVG, inherits the link color, no JS), and a muted citation line
beneath shows the clickable URL followed by the date — matching the
legacy capotej.com/links entry chrome.

### Changes

- 104a0dd feat(links): citation line (clickable url + date) and external-link glyph on index entries

## [0.14.0] - 2026-10-27

### Summary

The links index now renders like the post index: each entry is an
outbound title link with a muted date beneath and the note body under
that (matching legacy capotej.com/links) — replacing the bare
`date — title` list rows. Entries paginate like every other listing;
the local `/links/<slug>/` archive pages are unchanged.

### Changes

- 7f7c40b feat(links): post-index-style entries on the links index, ported from capotej.com

## [0.13.0] - 2026-10-26

### Summary

Pagination now covers every listing: the links page and tag pages
paginate exactly like the home listing (5 per page, numbered pager +
Prev/Next, page 1 canonical, `/page/1/` 301s to the base, rel=prev/next
head links) via one shared emitter. Tag pages over five posts split into
`/t/<tag>/page/N/`; the links index into `/links/page/N/`. The papers
index stays single-page.

### Changes

- 3c6115a feat(pagination): generalize to links + tag pages (shared emit_paginated)

## [0.12.0] - 2026-10-26

### Summary

The home listing now paginates: 5 posts per page with a numbered pager
and Prev/Next links (legacy capotej.com parity), on static `/page/N/`
URLs — a static host can't route `?page=N` query strings. Page 1 stays
canonical `/`, deeper pages get `Home — page N` titles plus
`rel=prev`/`rel=next` head links, and `/page/1/` 301s to `/` so the
first page has exactly one URL. Sites with five or fewer posts emit no
pager at all.

### Changes

- 378e11e feat(pagination): 5 posts/page home listing with /page/N/ URLs

## [0.11.1] - 2026-10-26

### Summary

Chrome polish batch ported from capotej.com: the blog-title link,
listing titles, and read-more links lose their underlines (fixing a
broken selector shipped in 0.11.0); nav links drop their pipe
separators; the header/footer rules go full-bleed in a faint line
color; and post listings (home + tag pages, now sharing one renderer)
show bigger title links with a muted date beneath, tag pills and
read-more on one line, and a faint separator between posts.

### Changes

- d9caff8 feat(theme): chrome polish batch, ported from capotej.com (0.11.1)

## [0.11.0] - 2026-10-26

### Summary

Every generated page now opens with a site-name header — the site name
as a linked `<h1>` above the nav (`<a href="/"><h1>My Blog</h1></a>`),
matching the legacy capotej.com shape. It is the single h1 per page:
listing, tag, and 404 headings demote to h2. Home-listing entries now
order excerpt → tag pills → "Read more →".

### Changes

- 69544c4 feat(shell): site-name header (linked h1, single-h1 pages), ported from capotej.com

## [0.10.0] - 2026-10-26

### Summary

Generated sites gain the full site shell capotej.com has: a footer, page
titles like `Post | Site Name`, a styled 404 page, the post date under
each post title, "Read more →" links on the home listing, and a richer
Atom feed (full `<content>` per entry, absolute URLs, feed id and
self-link). Sites identify via `SITE_NAME`/`BASE_URL` constants in
build.py — substituted from the scaffold name, editable before launch.
A fresh `npx @capotej/create-content-repo my-blog` ships all of it.

### Changes

- fbc31be feat(shell): full site-shell parity, ported from capotej.com
- c16e9da docs(tags): document tag schema in the template AGENTS.md contract

## [0.9.1] - 2026-10-22

### Summary

Republish of 0.9.0 — the v0.9.0 release workflow failed on a transient
npm registry 503 during the publish PUT (provenance was signed; the
version never landed). No code changes; same content as 0.9.0.

### Changes

- ec0f808 release v0.9.0 (publish failed: registry 503; never on npm)

## [0.9.0] - 2026-10-22

### Summary

Posts are now taggable end-to-end: the `tags` meta field each post already
declared finally does something. The build validates tag values as URL
slugs (failing loud on anything else), emits a `/t/<tag>/` index page per
tag (newest first, with excerpts and pills), and renders `# tag` pills on
the home listing, on tag pages, and at the bottom of every post page —
matching the legacy Abbey site. The sample post ships two tags so a fresh
`npx @capotej/create-content-repo my-blog` scaffold demonstrates the tag
pages out of the box.

### Changes

- 1b2edc8 feat(tags): /t/<tag>/ pages + tag pills, ported from capotej.com

## [0.8.0] - 2026-10-12

### Summary

Generated repos now emit a proper Atom feed with stable entry ids. Feed
entries carry `sha256(title + created)` ids, second-precision
`<published>`/`<updated>` timestamps, and an html `<summary>`; posts gain
optional `created`/`updated` meta (for imports from another system, so
subscriber state carries over) and an optional `#let excerpt = [...]`
content block, rendered under the post on the home listing and into the
feed summary. Every page head ships a `<link rel="alternate">` feed
autodiscovery tag.

### Changes

- feat(feed): sha256 entry ids, published/updated timestamps, html
  summaries; `created`/`updated` post meta (default date 00:00:00)
- feat(listing): optional `#let excerpt` block rendered on the home page
  under each post (.excerpt styles in theme.css)
- feat(head): atom feed autodiscovery link in the page shell
- build.py: `compile_excerpt()` renders a post's excerpt via a stdin
  typst driver importing the `#let excerpt` block; posts sorted by
  `created`
- docs: schema + new-content skill cover created/updated and excerpt
- example post demonstrates the excerpt block

### Commits

- a138174 feat: feed entry ids, timestamps, summaries + front-page excerpts
- 414dda3 fix: keep entry-id scheme byte-compatible with the legacy feed

## [0.7.0] - 2026-10-11

### Summary

Generated repos now ship a theme system. Code blocks are colored by the
typst compiler itself: every page compiles through `theme/wrapper.typ`,
which applies a vendored syntect palette (`theme/catppuccin.tmTheme`) at
build time — no CSS classes, no JS, content files untouched. Page chrome
lives in `theme/style.css` with the font/size/measure knobs as `:root`
variables up top, and the site follows the OS light/dark preference with
zero JavaScript: latte and mocha halves via `prefers-color-scheme`, plus
an attribute-selector remap that flips the baked dark code colors to
their light counterparts. `build.py` fails loud if a compiled page
contains a code color the stylesheet doesn't remap, so a palette swap
can't silently ship a broken light mode. The dev server watches `theme/`
too, and the sample post now includes a code block so a fresh scaffold
shows the theme immediately.

    npx @capotej/create-content-repo my-blog
    cd my-blog && python3 .agents/skills/build/scripts/build.py
    # edit theme/style.css :root knobs (fonts, size, column width); save

### Changes

- 37a989d feat: hybrid theme system — typst compile-time code colors + no-JS light/dark

## [0.6.0] - 2026-09-27

### Summary

Generated repos now build through a reviewable `./build.sh` entrypoint
instead of an inline shell one-liner in `netlify.toml`: it installs a
pinned, sha256-verified mise (v2026.9.6) when Netlify's image lacks it,
then runs the ordinary build. The dev server honors `build/_redirects`,
so legacy paths (`/p/about`, old `/blog/…` URLs) 301 on `localhost:3000`
exactly like production, and reloads the redirect table after every
watched rebuild. typos no longer chokes on binary images (`.png/.jpg`):
the prek hook passes `--force-exclude` and `.typos.toml` excludes them
explicitly. Also fixes the scaffolder dropping executable bits —
`build.sh` arrives ready to run.

    npx @capotej/create-content-repo my-blog
    cd my-blog && ./build.sh          # what Netlify runs
    python3 .agents/skills/serve/scripts/serve.py   # /p/* now 301s locally

### Changes

- 89fdf79 feat: port build.sh entrypoint, serve _redirects, typos image excludes

## [0.5.0] - 2026-09-27

### Summary

The first real-world use of the scaffolder — importing 68 pages of
capotej.com — surfaced four gaps that had to be hand-patched downstream;
they are now part of the templates. `build.py` reads meta with
`--features html`, so content using `#html.elem` (raw HTML iframes,
`/assets/` images) no longer fails the build with `unknown variable:
html`; and `pages` now honor `redirect_from` exactly like posts, so a
scaffolded site replacing an older one can carry legacy paths (e.g.
`/p/about` → `/about/`) in `_redirects`. AGENTS.md and the new-content
skill document both. Repos scaffolded before this release need the
two `build.py` lines back-ported.

    npx @capotej/create-content-repo my-blog
    # content/pages/about.typ
    #let meta = (title: "About", redirect_from: "/p/about")

### Changes

- c878543 fix: port capotej.com import patches into templates

## [0.4.0] - 2026-09-20

### Summary

Generated repos now ship a dev loop: a new `serve` skill whose stdlib-only
`serve.py` builds once, serves `build/` on `http://127.0.0.1:3000`, and
rebuilds automatically whenever anything under `content/`, `assets/`, or the
build script itself changes — so the natural workflow is to point your agent
harness at the repo, ask for a post, and watch it appear. Rebuilds re-run the
ordinary `build.py` in a fresh process, meaning the dev loop exercises the
exact pipeline Netlify runs; failed compiles print the error and keep serving
(fix and save to retry). CI now proves the watch→rebuild path end-to-end.

    npx @capotej/create-content-repo my-blog
    python3 .agents/skills/serve/scripts/serve.py   # :3000 + rebuild-on-change

### Changes

- 0e2b558 feat: serve skill — dev server on :3000 with rebuild-on-change
- fa042b5 docs: AGENTS.md + README match current repo state

## [0.3.0] - 2026-09-19

### Summary

Generated repos now start as real git repos: when `git` is on PATH the
scaffolder runs `git init -b main` and makes the initial `init content-repo`
commit itself, so prek's hooks have a repo to install into (previously the
scaffolded tree wasn't even a git repo, and npm packaging silently stripped
the template's `.gitignore` — it now ships as `template/gitignore` and is
written under its real name). Bare containers/CI get a repo-local identity
fallback; environments without git keep the manual step in the next-steps
output, which now also includes `prek install`.

    npx @capotej/create-content-repo my-blog
    cd my-blog && git log --oneline   # init content-repo — already there

### Changes

- 6a3b241 feat: scaffold git init + initial commit when git is available
- 2c6f133 chore: oxfmt CHANGELOG trailing newline

## [0.2.0] - 2026-09-19

### Summary

Templates move from embedded strings to real files under `template/` (copied
with `{{NAME}}`/`{{TYPST_VERSION}}`/`{{DATE}}` substitution), generated repos
gain a prek lint stack (typstyle format + typos spelling on `.typ` content,
all tools pinned via mise), and the build orchestrator gains `--verify` — a
rebuild-into-temp-dir comparison that fails unless `build/` is byte-identical,
catching both pipeline nondeterminism and hand-edited output.

    npx @capotej/create-content-repo my-blog
    cd my-blog && mise install
    python3 .agents/skills/build/scripts/build.py --verify

### Changes

- 0c6da5b refactor: template/ files replace embedded template strings
- 847df5d fix: anchor .gitignore build/ pattern to repo root
- 915f499 feat: prek lint stack + build determinism verify in generated repos

## [0.1.0] - 2026-09-19

### Summary

Initial release: zero-dependency npx scaffolder for typst content-repos —
`.typ` content sections with examples, agent skills (build / new-content /
publish), stdlib-Python build orchestrator, mise-pinned toolchain, Netlify
deploy config.

- 5ba689b init: @capotej/create-content-repo — zero-dep npx scaffolder for typst content-repos
- 4628c58 ci: fix setup-node steps — actions/ not pnpm/, inputs under with:
