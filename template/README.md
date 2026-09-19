# {{NAME}}

A content-repo: Typst sources, a stdlib-Python build orchestrator, and agent
skills. `build/` is generated output — never edit it by hand.

## Layout

- `content/posts` — dated posts, `YYYY-MM-DD-slug.typ`
- `content/links` — link blog entries, `YYYY-MM-DD-slug.typ`
- `content/papers` — paper reading notes, `YYYY-MM-DD-slug.typ`
- `content/pages` — standalone pages, `slug.typ`
- `assets/` — images and binaries, referenced by relative path
- `.agents/skills/` — build / new-content / publish skills (scripts included)
- `mise.toml` — pinned toolchain (typst)
- `netlify.toml` — Netlify build + publish config

## Build

Requires mise (or a typst on PATH) and python3:

  mise install
  python3 .agents/skills/build/scripts/build.py

Output lands in `build/` (gitignored). Verify the output is reproducible and
untampered:

  python3 .agents/skills/build/scripts/build.py --verify

## Lint

prek wires git hooks (typstyle format + typos spelling on `content/**/*.typ`):

  prek install
  prek run --all-files

## Deploy

Netlify, from the repo root: the command in `netlify.toml` bootstraps mise if
needed, installs the pinned typst, runs the build, and publishes `build/`.
