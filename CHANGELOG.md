# Changelog

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

