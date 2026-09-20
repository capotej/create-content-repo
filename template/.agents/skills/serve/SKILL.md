---
name: serve
description: >-
  Serve build/ on localhost:3000 and rebuild automatically when content,
  assets, or the build script change — the local dev loop for the
  content-repo. Use when the user wants to preview, watch, or develop
  against the site locally.
---

# Serve / watch (dev loop)

`serve.py` builds once, serves `build/` on `http://127.0.0.1:3000`, and
rebuilds whenever anything under `content/`, `assets/`, or the build
script itself changes (mtime polling, ~0.5s latency, edit bursts
debounced until they settle).

    python3 .agents/skills/serve/scripts/serve.py               # :3000
    python3 .agents/skills/serve/scripts/serve.py --port 4000   # other port

## What it watches

- `content/**/*.typ` — created, edited, or deleted (drafts are still
  skipped by the build itself)
- `assets/**`
- `.agents/skills/build/scripts/build.py` — orchestrator edits trigger a
  rebuild too

## Behavior notes

- Rebuilds run the same build.py Netlify runs, in a fresh process — the
  dev loop exercises the production pipeline, never a parallel
  implementation. It never writes anywhere except `build/` (via the
  build).
- A rebuild wipes `build/` first, so in-flight requests may briefly 404;
  reload after the `serve: build ok` line.
- A failed compile prints the typst error and keeps serving — fix the
  file and save to retry.
- Linux + mise assumed; python3 stdlib only. Ctrl+C stops the server.
