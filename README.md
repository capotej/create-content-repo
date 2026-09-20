# @capotej/create-content-repo

Scaffold a content-repo: Typst (`.typ`) content, agent skills with a
stdlib-Python build orchestrator, a mise-pinned toolchain, and Netlify
deploy. Run via `npx @capotej/create-content-repo <name>`.

## Usage

```
npx @capotej/create-content-repo my-blog
```

That's the whole setup. If `git` is on PATH the scaffolder already ran
`git init` (branch `main`) and made the initial commit; otherwise it prints
the manual step in its next-steps output.

From there, **point your agent harness at the generated repo** — the skills
inside it are the interface. The repo's `AGENTS.md` contract plus
`.agents/skills/{build,new-content,serve,publish}/` tell the agent how to
create content, build and verify, run the dev loop, and publish; no raw
python or typst commands needed. A typical first session: ask for a new
post (new-content), watch it locally (serve on :3000), then publish.

The generated repo:

- `content/{posts,links,papers,pages}/` — one `.typ` example each
  (`#let meta` dict + `#context metadata((meta))` marker)
- `.agents/skills/{build,new-content,serve,publish}/` — the agent
  interface: build orchestrator at `.agents/skills/build/scripts/build.py`
  (python3 stdlib only, invokes the pinned typst for HTML; `--verify`
  checks build/ is byte-identical on rebuild), dev server + watch at
  `.agents/skills/serve/scripts/serve.py` (:3000, rebuild-on-change)
- `.pre-commit-config.yaml` + `.typos.toml` — prek hooks (typstyle format +
  typos spelling on `.typ` content), all tools pinned via mise
- `AGENTS.md` — the content contract for agents
- `mise.toml` — pinned typst, typstyle, typos, prek
- `netlify.toml` — self-bootstrapping build (mise if present, else
  mise.run) → publish `build/`

Options: `--typst-version <ver>` (default 0.15.1), `--force`.

## Architecture

Zero-dependency TypeScript CLI (`tsc`-compiled). No subcommands, no runtime
deps — argv parsing only, like create-react-app. Template file bodies are
real files under `template/`, shipped in the npm package
(`files: ["dist", "template"]`).

- Entry point: `src/cli.ts` → `dist/cli.js` (the `bin` target)
- `src/scaffold.ts` copies `template/` into `./<name>`, substituting
  `{{NAME}}` / `{{TYPST_VERSION}}` / `{{DATE}}` and renaming `DATE-*.typ`
  example files to today's date; `template/gitignore` ships dotless (npm
  strips a root `.gitignore`) and is written as real `.gitignore`
- `template/` holds every generated file body

### Adding to the scaffold

1. Edit files under `template/` — that's the entire generated repo.
2. `pnpm build && node dist/cli.js test-repo` and inspect the tree.
3. Run the generated repo's build to prove the templates compile:
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
