# @capotej/create-content-repo — generator contract

Zero-dependency npx scaffolder for content-repos. Mirrors @capotej/tools
conventions: tsc, pnpm, exact pins, mise, oxlint/oxfmt, OIDC npm publishing.

## Hard rules

1. **Zero runtime dependencies** — `package.json` `dependencies` stays `{}`.
   The CLI parses argv itself; do not add a command framework.
2. **Templates are inlined strings** in `src/templates.ts` — the compiled
   `dist/` must be self-contained (`files: ["dist"]`), no file copying at
   pack time. Template literals must not contain backticks or `${` inside
   generated bodies.
3. **The generated repo's guardrail holds here too**: the scaffold's
   `build.py` is stdlib-only and invokes the pinned typst — never ship a
   template change that would make generated content depend on the LLM to
   render.
4. **Every template change is user-visible** (it changes what `npx` emits)
   → minor version per the release skill.

## Layout

- `src/cli.ts` — argv parsing, --help/--version, dispatch
- `src/scaffold.ts` — writes the tree into `./<name>`
- `src/templates.ts` — all generated file bodies (mise.toml, netlify.toml,
  AGENTS.md, README, skills, build.py, .typ examples)

## Toolchain

`mise.toml` is the single source of truth (node, typst for local E2E).
Use `mise install` / `mise exec -- <cmd>`; never global installs.

## Verify before pushing

```bash
eval "$(mise activate bash)"
pnpm build && pnpm lint && pnpm typecheck && pnpm format:check
node dist/cli.js test-repo && cd test-repo
mise install && python3 .agents/skills/build/scripts/build.py
```

The generated blog must build green before any push — template breakage
ships to every new npx user.

## Package manager

pnpm (via `packageManager` field). Exact pins only; 7-day cooldown from
`pnpm-workspace.yaml`. Do not use npm or yarn.

## Releases

Tag-driven OIDC publish (release.yml + the release skill at
`.agents/skills/release/SKILL.md`). Never `npm publish` manually; never
`npm version` (edit `package.json` by hand).
