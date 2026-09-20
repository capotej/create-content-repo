# Changelog

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
