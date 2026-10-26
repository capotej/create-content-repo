# Changelog

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
