# {{NAME}} — content-repo contract

This repo is a content-repo: Typst sources under `content/`, deterministic
Python (stdlib-only) orchestration in `.agents/skills/build/scripts/build.py`,
deployed as static HTML from `build/` via Netlify. The agent is the CMS and
the maintainer of the pipeline — never the renderer.

## Toolchain

- `mise.toml` is the single source of truth for tool versions. Current: typst
  {{TYPST_VERSION}}. Do not install tools globally; use mise (`mise install`,
  `mise exec -- <cmd>`). `build.py` already routes typst through mise when
  mise is available and falls back to a typst on PATH otherwise.
- python3 (stdlib only — no pip dependencies, ever) drives the build.

## Hard rules

1. **Never edit `build/`** — it is generated output, gitignored, rebuilt whole.
2. **Never render content with the LLM.** All HTML comes from
   `build.py` invoking the pinned typst compiler. The agent edits `.typ`
   sources and the build script; it does not hand-write page HTML.
3. **Plain semantic HTML.** This version ships no CSS, no classes, no framework.
   Do not port styles or add a stylesheet unless asked.
4. **python3 stdlib only** in `build.py` — no third-party imports, no
   virtualenvs, no pip installs. It must run on a bare python3.
5. **Set a meaningful git commit message** for every content change; git history
   is the audit log.

## Content schema

Every `.typ` file opens with a `#let meta = (...)` dictionary followed by a
`#context metadata((meta))` marker line — `build.py` reads meta via typst
eval of that marker. Fields by section:

- `content/posts/YYYY-MM-DD-slug.typ` — title (str), date (str `YYYY-MM-DD`,
  must match the filename prefix), tags (array of str), draft (bool). Permalink:
  `/{y}/{m}/{d}/{slug}/`. Optional `redirect_from` (str or array of str,
  legacy paths starting with `/`) emits lines into `_redirects`.
- `content/links/YYYY-MM-DD-slug.typ` — title, date, url (str), note body.
  Permalink: `/links/{slug}/`.
- `content/papers/YYYY-MM-DD-slug.typ` — title, date, arxiv_id (str),
  pdf_url (str), note body. Permalink: `/papers/{slug}/`.
- `content/pages/slug.typ` — title. Permalink: `/{slug}/`.

Body is authored in Typst markup (headings `= ` / `==`, `*bold*`,
`_emph_`, links `#url("...")` or `#link(...)`). Output is typst's HTML
export (`--features html`), wrapped in a minimal page shell by `build.py`.

Drafts (`draft: true`) are skipped by the build.

## Assets

Images/binaries live in `assets/` and are referenced relatively
(`../assets/foo.png` style paths depend on page depth — prefer typst's
`#image` with a root-relative …/ calculation, or keep assets near the
referring page's depth). `build.py` copies `assets/` to `build/assets/`
verbatim.

## Skills

- `.agents/skills/build/` — build `build/`, verify output, extend the script.
- `.agents/skills/new-content/` — create a new post/link/paper/page stub.
- `.agents/skills/publish/` — commit, push, let Netlify deploy.

## Deploy

Push to the main branch; Netlify runs the `netlify.toml` command (bootstraps
mise if missing, `mise install`, `python3 .agents/skills/build/scripts/build.py`)
and publishes `build/`. Verify deploys in the Netlify UI.
