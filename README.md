# @capotej/create-content-repo

Scaffold a content-repo: Typst (`.typ`) content, agent skills with a
stdlib-Python build orchestrator, a mise-pinned toolchain, and Netlify
deploy. Run via `npx @capotej/create-content-repo <name>`.

## Usage

```
npx @capotej/create-content-repo my-blog
cd my-blog
mise install
prek install
python3 .agents/skills/build/scripts/build.py
python3 -m http.server -d build 8001
```

If `git` is on PATH, the scaffolder already ran `git init` (branch `main`) and
made the initial commit; otherwise it prints the manual step in its next-steps
output.

The generated repo:

- `content/{posts,links,papers,pages}/` — one `.typ` example each
  (`#let meta` dict + `#context metadata((meta))` marker)
- `.agents/skills/{build,new-content,publish}/` — skills; the build
  orchestrator lives at `.agents/skills/build/scripts/build.py`
  (python3 stdlib only, invokes the pinned typst for HTML; `--verify`
  checks build/ is byte-identical on rebuild)
- `.pre-commit-config.yaml` + `.typos.toml` — prek hooks (typstyle format +
  typos spelling on `.typ` content), all tools pinned via mise
- `AGENTS.md` — the content contract for agents
- `mise.toml` — pinned typst, typstyle, typos, prek
- `netlify.toml` — self-bootstrapping build (mise if present, else
  mise.run) → publish `build/`

Options: `--typst-version <ver>` (default 0.15.1), `--force`.

## Architecture

Zero-dependency TypeScript CLI (`tsc`-compiled). No subcommands, no runtime
deps — argv parsing only, like create-react-app. All template file bodies are
inlined as strings in `src/templates.ts`, so the compiled `dist/` is
self-contained and ships via `files: ["dist"]`.

- Entry point: `src/cli.ts` → `dist/cli.js` (the `bin` target)
- `src/scaffold.ts` writes the template tree into `./<name>`
- `src/templates.ts` holds every generated file body

### Adding to the scaffold

1. Edit `src/templates.ts` — add or change a template string.
2. Wire it into the `files` map in `src/scaffold.ts` if it is a new file.
3. `pnpm build && node dist/cli.js test-repo` and verify the generated tree.
4. Run the generated repo's build to prove the templates compile:
   `cd test-repo && mise install && python3 .agents/skills/build/scripts/build.py`

## Package Manager

This project uses **pnpm**, declared via the `packageManager` field in
`package.json`. Do not use npm or yarn.

All dependencies are pinned to exact versions — no floating ranges (`^`, `~`).
pnpm enforces a 7-day release cooldown via `minimumReleaseAge: 7` in
`pnpm-workspace.yaml` as a supply-chain guard.

## Tool Versions

This project uses `mise.toml` as the single source of truth for all tool and
language versions. Do not install tools globally or via ad-hoc commands —
use mise instead.

## Formatting / Linting

oxfmt formats, oxlint lints. CI runs lint,
typecheck, format:check, build, and an E2E scaffold+build step.

## Releases

OIDC trusted publishing — pushing a `v*` tag triggers
`.github/workflows/release.yml` which publishes to npm. No npm token.
See `.agents/skills/release/SKILL.md` for the full release procedure.
