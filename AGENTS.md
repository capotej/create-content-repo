# @capotej/create-content-repo — generator contract

Zero-dependency npx scaffolder for content-repos: tsc, pnpm, exact pins,
mise, oxlint/oxfmt, OIDC npm publishing.

## Hard rules

1. **Zero runtime dependencies** — `package.json` `dependencies` stays `{}`.
   The CLI parses argv itself; do not add a command framework.
2. **Templates are real files** under `template/`, shipped in the npm
   package (`files: ["dist", "template"]`). `src/scaffold.ts` copies the
   tree substituting `{{NAME}}` / `{{TYPST_VERSION}}` / `{{DATE}}`.
   `template/gitignore` is deliberately dotless — npm strips a root
   `.gitignore` from packages; the scaffolder writes it as `.gitignore`.
3. **The generated repo's guardrail holds here too**: the scaffold's
   `build.py` (and `serve.py`) are stdlib-only and invoke the pinned
   typst — never ship a template change that would make generated content
   depend on the LLM to render.
4. **Every template change is user-visible** (it changes what `npx` emits)
   → minor version per the release skill.

## Layout

- `src/cli.ts` — argv parsing, --help/--version, dispatch
- `src/scaffold.ts` — copies `template/` into `./<name>` with placeholder
  substitution and `DATE-*.typ` filename renames; fixes up the dotless
  gitignore; and, when `git` is on PATH, runs `git init -b main` + the
  initial `init content-repo` commit (with a repo-local identity fallback
  for bare containers) so prek has a repo to install into
- `template/` — every generated file body (mise.toml, netlify.toml,
  AGENTS.md, README, skills incl. build.py and serve.py, .typ examples)

## Toolchain

`mise.toml` is the single source of truth (node, typst for local E2E).
Use `mise install` / `mise exec -- <cmd>`; never global installs.

## Verify before pushing

```bash
eval "$(mise activate bash)"
pnpm build && pnpm lint && pnpm typecheck && pnpm format:check
node dist/cli.js test-repo && cd test-repo
mise install
python3 .agents/skills/build/scripts/build.py --verify
prek run --all-files
python3 .agents/skills/serve/scripts/serve.py &  curl -fsS http://127.0.0.1:3000/; kill %1
```

(CI runs the same E2E — see `.github/workflows/ci.yml`.) The generated blog
must build green before any push — template breakage ships to every new
npx user.

## Package manager

pnpm (via `packageManager` field). Exact pins only; 7-day cooldown from
`pnpm-workspace.yaml`. Do not use npm or yarn.

## Releases

Tag-driven OIDC publish (release.yml + the release skill at
`.agents/skills/release/SKILL.md`). Never `npm publish` manually; never
`npm version` (edit `package.json` by hand).
