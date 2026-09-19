---
name: build
description: >-
  Build the site from content/*.typ into build/ via the deterministic python3
  orchestrator, verify the output, and extend the orchestrator when the build
  needs new capabilities. Use when the user wants to build, rebuild, preview,
  verify, or change the site build.
---

# Build

The build is a deterministic, stdlib-only Python script that invokes the pinned
typst compiler. Run it; never hand-write page HTML or edit build/ directly.

## Run the build

From the repo root (requires mise with typst installed — see Toolchain):

    mise install
    python3 .agents/skills/build/scripts/build.py

- The script routes typst through mise automatically (falls back to a typst on
  PATH), skips draft entries, validates that posts' meta.date matches the
  filename prefix, and fails loudly on any compile error.
- Output: build/ (gitignored) — dated post permalinks, /links/, /papers/,
  standalone pages, section indexes, /atom.xml, optional _redirects, assets/.

## Verify

Two layers:

    python3 .agents/skills/build/scripts/build.py --verify   # determinism check
    python3 -m http.server -d build 8001                     # eyeball check

`--verify` rebuilds into a temp dir and requires the result to be
byte-identical to the existing build/ — it catches both nondeterminism in
the pipeline and accidental hand-edits to build/ output. Run it after any
build.py change and before publishing.

Then spot-check the home page, one post, one links entry, and the atom feed.
For a targeted change, re-run the build and re-check only the affected route.

## Extend the orchestrator

When the build needs a new capability (new section, new meta field, sitemap,
tag pages), edit .agents/skills/build/scripts/build.py:

- python3 stdlib only — no third-party imports, no pip installs.
- Keep it deterministic: same inputs -> same build/ tree.
- Meta comes from 'typst eval' of the #context metadata((meta)) marker —
  add fields to the #let meta dict in content files and read them in the
  script; do not regex-parse Typst source.
- Add a content/*.typ fixture for the new behavior, rebuild, and verify.

## Deploy path

build/ is produced by Netlify on push (netlify.toml runs this same script).
Local builds are for verification before pushing.
