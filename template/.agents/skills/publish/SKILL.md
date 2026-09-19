---
name: publish
description: >-
  Publish content: flip drafts, build to verify, commit with a meaningful
  message, and push so Netlify deploys. Use when the user wants to publish,
  ship, or deploy the site.
---

# Publish

## Steps

1. Confirm what is being published: 'git status' and 'git diff --stat'.
   Anything with draft: true in meta is NOT in the build — flip it to false
   only if it should go out.
2. Build and verify locally (see the build skill). The build must pass before
   pushing; Netlify will run the same script.
3. Stage and commit content changes with a message that names the piece:

       git add content/ assets/
       git commit -m "post: <slug> — <one line on what it says>"

   Small pipeline fixes (build.py, skills, config) get their own commit:
   'build: ...', 'skill: ...', 'config: ...'.
4. Push to the main branch:

       git push origin main

   Netlify builds from netlify.toml (bootstraps mise, installs the pinned
   typst, runs the same build script) and publishes build/.
5. Verify the deploy in the Netlify UI (deploy log + preview URL). Spot-check
   the new URL after it goes green.

## Rules

- Never commit build/ — it is generated (and gitignored).
- Never force-push main.
- If the Netlify deploy fails, the deploy log names the failing step; fix the
  cause (usually a .typ compile error or a meta mismatch) in a follow-up
  commit rather than retrying blind.
