// Templates for the generated content-repo. Everything is inlined as strings so
// the compiled dist/ is self-contained (no template file copying at build time).
//
// NOTE: template literals below must not contain "${" or backticks inside the
// *generated file bodies* (Python/Typst/TOML never need them), so they read
// literally. Assert this in tests.

export const miseToml = (typstVersion: string): string =>
  ["[tools]", `typst = "${typstVersion}"`, ""].join("\n");

export const netlifyToml = `# Netlify build config. The build image does not officially ship mise, but a
# self-bootstrapping command works either way: use mise if present, install it
# otherwise, then install the pinned typst from mise.toml and run the build.
# mise.toml stays the single source of truth for tool versions.
[build]
  command = "command -v mise >/dev/null 2>&1 || curl -fsSL https://mise.run | sh; export PATH=\\"$HOME/.local/bin:$PATH\\"; mise install; python3 .agents/skills/build/scripts/build.py"
  publish = "build"

[build.environment]
  MISE_YES = "1"
`;

export const gitignore = `build/
.netlify/
`;

export const readmeMd = (name: string): string => `# ${name}

A content-repo: Typst sources, a stdlib-Python build orchestrator, and agent
skills. \`build/\` is generated output — never edit it by hand.

## Layout

- \`content/posts\` — dated posts, \`YYYY-MM-DD-slug.typ\`
- \`content/links\` — link blog entries, \`YYYY-MM-DD-slug.typ\`
- \`content/papers\` — paper reading notes, \`YYYY-MM-DD-slug.typ\`
- \`content/pages\` — standalone pages, \`slug.typ\`
- \`assets/\` — images and binaries, referenced by relative path
- \`.agents/skills/\` — build / new-content / publish skills (scripts included)
- \`mise.toml\` — pinned toolchain (typst)
- \`netlify.toml\` — Netlify build + publish config

## Build

Requires mise (or a typst on PATH) and python3:

  mise install
  python3 .agents/skills/build/scripts/build.py

Output lands in \`build/\` (gitignored).

## Deploy

Netlify, from the repo root: the command in \`netlify.toml\` bootstraps mise if
needed, installs the pinned typst, runs the build, and publishes \`build/\`.
`;

export const agentsMd = (
  name: string,
  typstVersion: string,
): string => `# ${name} — content-repo contract

This repo is a content-repo: Typst sources under \`content/\`, deterministic
Python (stdlib-only) orchestration in \`.agents/skills/build/scripts/build.py\`,
deployed as static HTML from \`build/\` via Netlify. The agent is the CMS and
the maintainer of the pipeline — never the renderer.

## Toolchain

- \`mise.toml\` is the single source of truth for tool versions. Current: typst
  ${typstVersion}. Do not install tools globally; use mise (\`mise install\`,
  \`mise exec -- <cmd>\`). \`build.py\` already routes typst through mise when
  mise is available and falls back to a typst on PATH otherwise.
- python3 (stdlib only — no pip dependencies, ever) drives the build.

## Hard rules

1. **Never edit \`build/\`** — it is generated output, gitignored, rebuilt whole.
2. **Never render content with the LLM.** All HTML comes from
   \`build.py\` invoking the pinned typst compiler. The agent edits \`.typ\`
   sources and the build script; it does not hand-write page HTML.
3. **Plain semantic HTML.** This version ships no CSS, no classes, no framework.
   Do not port styles or add a stylesheet unless asked.
4. **python3 stdlib only** in \`build.py\` — no third-party imports, no
   virtualenvs, no pip installs. It must run on a bare python3.
5. **Set a meaningful git commit message** for every content change; git history
   is the audit log.

## Content schema

Every \`.typ\` file opens with a \`#let meta = (...)\` dictionary followed by a
\`#context metadata((meta))\` marker line — \`build.py\` reads meta via typst
eval of that marker. Fields by section:

- \`content/posts/YYYY-MM-DD-slug.typ\` — title (str), date (str \`YYYY-MM-DD\`,
  must match the filename prefix), tags (array of str), draft (bool). Permalink:
  \`/{y}/{m}/{d}/{slug}/\`. Optional \`redirect_from\` (str or array of str,
  legacy paths starting with \`/\`) emits lines into \`_redirects\`.
- \`content/links/YYYY-MM-DD-slug.typ\` — title, date, url (str), note body.
  Permalink: \`/links/{slug}/\`.
- \`content/papers/YYYY-MM-DD-slug.typ\` — title, date, arxiv_id (str),
  pdf_url (str), note body. Permalink: \`/papers/{slug}/\`.
- \`content/pages/slug.typ\` — title. Permalink: \`/{slug}/\`.

Body is authored in Typst markup (headings \`= \` / \`==\`, \`*bold*\`,
\`_emph_\`, links \`#url("...")\` or \`#link(...)\`). Output is typst's HTML
export (\`--features html\`), wrapped in a minimal page shell by \`build.py\`.

Drafts (\`draft: true\`) are skipped by the build.

## Assets

Images/binaries live in \`assets/\` and are referenced relatively
(\`../assets/foo.png\` style paths depend on page depth — prefer typst's
\`#image\` with a root-relative …/ calculation, or keep assets near the
referring page's depth). \`build.py\` copies \`assets/\` to \`build/assets/\`
verbatim.

## Skills

- \`.agents/skills/build/\` — build \`build/\`, verify output, extend the script.
- \`.agents/skills/new-content/\` — create a new post/link/paper/page stub.
- \`.agents/skills/publish/\` — commit, push, let Netlify deploy.

## Deploy

Push to the main branch; Netlify runs the \`netlify.toml\` command (bootstraps
mise if missing, \`mise install\`, \`python3 .agents/skills/build/scripts/build.py\`)
and publishes \`build/\`. Verify deploys in the Netlify UI.
`;

export const buildPy = String.raw`#!/usr/bin/env python3
"""Deterministic build orchestrator for the content-repo.

Stdlib only. Walks content/, reads per-file meta via typst eval, compiles
each .typ to an HTML fragment via the pinned typst compiler, wraps it in a
minimal page shell, emits index pages, an Atom feed, _redirects, and copies
assets/ into build/.

Usage: python3 .agents/skills/build/scripts/build.py   (from repo root)
"""

import json
import os
import re
import shutil
import subprocess
import sys
from html import escape as h
from pathlib import Path
from xml.sax.saxutils import escape as xescape

REPO = Path(__file__).resolve().parents[4]
CONTENT = REPO / "content"
ASSETS = REPO / "assets"
BUILD = REPO / "build"

META_EXPR = "query(metadata).map(it => it.value)"

SECTIONS = ("posts", "links", "papers", "pages")

NAV = (
    '<nav><a href="/">Home</a> | <a href="/links/">Links</a> | '
    '<a href="/papers/">Papers</a> | <a href="/about/">About</a></nav>'
)

SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
</head>
<body>
{nav}
<main>
{body}
</main>
</body>
</html>
"""

ATOM_ENTRY = """<entry>
<title>{title}</title>
<link href="{link}"/>
<id>{link}</id>
<updated>{date}T00:00:00Z</updated>
<summary>{summary}</summary>
</entry>
"""

ATOM_FEED = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>{title}</title>
<id>{base}</id>
<link href="{base}"/>
<updated>{updated}T00:00:00Z</updated>
{entries}
</feed>
"""


def die(msg):
    print("build: ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def typst_cmd():
    """Prefer mise-managed typst; fall back to typst on PATH."""
    env = dict(os.environ)
    env.setdefault("MISE_YES", "1")
    if shutil.which("mise"):
        return ["mise", "exec", "--", "typst"], env
    if shutil.which("typst"):
        return ["typst"], env
    die("no typst found: install mise (https://mise.run) and run mise install")


def run(cmd, env, what):
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if p.returncode != 0:
        die(what + " failed:\n" + (p.stderr or p.stdout))
    return p.stdout


def read_meta(path, cmd, env):
    out = run(cmd + ["eval", META_EXPR, "--in", str(path)], env,
              "reading meta from " + str(path))
    try:
        items = json.loads(out)
    except json.JSONDecodeError:
        die("meta eval did not return JSON for " + str(path))
    if not items:
        die("no meta found in " + str(path) +
            " (need '#context metadata((meta))' after the '#let meta' dict)")
    return items[0]


def compile_body(path, cmd, env):
    out = run(cmd + ["compile", str(path), "--features", "html",
                     "--format", "html", "-"], env,
              "compiling " + str(path))
    m = re.search(r"<body>(.*)</body>", out, re.DOTALL)
    if not m:
        die("no <body> in typst output for " + str(path))
    return m.group(1).strip()


DATE_PREFIX = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)$")


def split_dated(stem, rel):
    m = DATE_PREFIX.match(stem)
    if not m:
        die("filename must be YYYY-MM-DD-slug.typ: " + rel)
    return m.group(1), m.group(2), m.group(3), m.group(4)


def page(path, title, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(SHELL.format(title=h(title), nav=NAV, body=body), "utf-8")


def collect():
    entries = {}
    for section in SECTIONS:
        sec_dir = CONTENT / section
        items = []
        if sec_dir.is_dir():
            for f in sorted(sec_dir.glob("*.typ")):
                items.append(f)
        entries[section] = items
    return entries


def main():
    if not CONTENT.is_dir():
        die("no content/ dir at " + str(REPO))
    cmd, env = typst_cmd()
    version = run(cmd + ["--version"], env, "checking typst").strip()
    print("toolchain: " + version)

    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)

    files = collect()
    redirects = []
    published = {"posts": [], "links": [], "papers": []}

    for section in SECTIONS:
        for f in files[section]:
            rel = f.relative_to(REPO)
            meta = read_meta(f, cmd, env)
            if meta.get("draft") is True:
                print("skip (draft): " + str(rel))
                continue
            title = str(meta.get("title", f.stem))
            body = compile_body(f, cmd, env)

            if section == "posts":
                y, m, d, slug = split_dated(f.stem, rel)
                if str(meta.get("date", "")) != "-".join((y, m, d)):
                    die("meta.date does not match filename prefix: " + str(rel))
                url = "/{}/{}/{}/{}/".format(y, m, d, slug)
                rf = meta.get("redirect_from")
                if rf:
                    olds = [rf] if isinstance(rf, str) else list(rf)
                    redirects += ["{}    {}".format(o, url) for o in olds]
                published["posts"].append((meta.get("date", ""), title, url))
            elif section == "links":
                y, m, d, slug = split_dated(f.stem, rel)
                url = "/links/{}/".format(slug)
                out_url = str(meta.get("url", ""))
                link_line = ('<p><a href="' + h(out_url) + '">' + h(title)
                             + "</a></p>")
                published["links"].append((meta.get("date", ""), title, url))
            elif section == "papers":
                y, m, d, slug = split_dated(f.stem, rel)
                url = "/papers/{}/".format(slug)
                arxiv = str(meta.get("arxiv_id", ""))
                pdf = str(meta.get("pdf_url", ""))
                link_line = ('<p><a href="' + h(pdf) + '">pdf'
                             + (" (arXiv:" + h(arxiv) + ")" if arxiv else "")
                             + "</a></p>")
                published["papers"].append((meta.get("date", ""), title, url))
            else:  # pages
                url = "/{}/".format(f.stem)
                link_line = ""

            out = BUILD / url.lstrip("/") / "index.html"
            extra = link_line if section in ("links", "papers") else ""
            page(out, title, body + extra)
            print("ok: " + url + "  <- " + str(rel))

    # Index pages -----------------------------------------------------------
    def listing(items, header):
        rows = ['<h1>' + h(header) + "</h1>", "<ul>"]
        for date, title, url in sorted(items, reverse=True):
            rows.append("<li>{} — <a href=\"{}\">{}</a></li>".format(
                h(str(date)), h(url), h(title)))
        rows.append("</ul>")
        return "\n".join(rows)

    page(BUILD / "index.html", "Home",
         listing(published["posts"], "Posts"))
    page(BUILD / "links" / "index.html", "Links",
         listing(published["links"], "Links"))
    page(BUILD / "papers" / "index.html", "Papers",
         listing(published["papers"], "Papers"))

    # Atom feed (posts) -----------------------------------------------------
    posts = sorted(published["posts"], reverse=True)
    if posts:
        entries = "".join(
            ATOM_ENTRY.format(
                title=xescape(t), link=xescape(u),
                date=xescape(d),
                summary=xescape(""),
            ) for d, t, u in posts)
        (BUILD / "atom.xml").write_text(
            ATOM_FEED.format(title="Posts", base=".", updated=posts[0][0],
                             entries=entries), "utf-8")
        print("ok: /atom.xml")

    # _redirects ------------------------------------------------------------
    if redirects:
        (BUILD / "_redirects").write_text("\n".join(redirects) + "\n", "utf-8")
        print("ok: _redirects ({} lines)".format(len(redirects)))

    # Assets ----------------------------------------------------------------
    if ASSETS.is_dir():
        shutil.copytree(ASSETS, BUILD / "assets")
        print("ok: assets/ -> build/assets/")

    n = sum(len(v) for v in published.values()) + len(files["pages"])
    print("done: {} pages + indexes + feed -> build/".format(n))


if __name__ == "__main__":
    main()
`;

export const buildSkill = `---
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

After building:

    python3 -m http.server -d build 8001

Spot-check the home page, one post, one links entry, and the atom feed. For a
targeted change, re-run the build and re-check only the affected route.

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
`;

export const newContentSkill = `---
name: new-content
description: >-
  Create a new content entry (post, link, paper, or page) as a .typ stub with
  the correct filename and meta dictionary. Use when the user wants to write,
  start, or draft a new piece of content.
---

# New content (post / link / paper / page)

## Create the stub

Pick the section and slug, then create the file with today's date:

- Post:   content/posts/YYYY-MM-DD-slug.typ
- Link:   content/links/YYYY-MM-DD-slug.typ
- Paper:  content/papers/YYYY-MM-DD-slug.typ
- Page:   content/pages/slug.typ   (no date prefix)

Stub template (posts):

    #let meta = (
      title: "Working title",
      date: "YYYY-MM-DD",
      tags: (),
      draft: true,
    )
    #context metadata((meta))

    = Working title

Body in Typst markup.

Section-specific meta fields:

- posts: title, date (must equal the filename prefix), tags (array), draft.
  Optional redirect_from (str or array) for legacy paths.
- links: title, date, url (the external link). Body = the note.
- papers: title, date, arxiv_id, pdf_url. Body = reading notes.
- pages: title only.

Get today's date with 'date +%F' — do not guess.

## After writing

1. Set draft: false only when it is ready to publish.
2. Build and verify (see the build skill) — a compile error fails the build,
   which is the cheapest possible review.
3. Commit with a message naming the piece (see the publish skill).

## Authoring notes

- Typst markup, not Markdown: '= heading', '== subheading', '*bold*',
  '_emph_', lists with '- '.
- Meta values are Typst: strings in double quotes, arrays '(a, b)', booleans
  true/false. Dates are plain strings 'YYYY-MM-DD'.
- One H1 ('=') per page, matching the title.
`;

export const publishSkill = `---
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
`;

export const examplePost = (date: string): string => `#let meta = (
  title: "Hello, world",
  date: "${date}",
  tags: ("meta",),
  draft: false,
)
#context metadata((meta))

= Hello, world

This is the first post in a fresh content-repo. The body is authored in
*Typst* markup and rendered to plain semantic HTML by the pinned typst
compiler — no CSS, no framework, just a page shell.

== How this renders

- Headings become h2/h3 elements.
- *Bold* and _emphasis_ map to strong/em.
- Links look like #link("https://typst.app")[typst.app].

Edit or delete this file; then rebuild.
`;

export const exampleLink = (date: string): string => `#let meta = (
  title: "Typst",
  date: "${date}",
  url: "https://typst.app",
)
#context metadata((meta))

= Typst

The typst homepage — a markup-based typesetting system that compiles this
site's content to HTML. Replace this entry with a real link and note.
`;

export const examplePaper = (date: string): string => `#let meta = (
  title: "Typst: a scriptable, incremental, and typesettable document processor",
  date: "${date}",
  arxiv_id: "2508.02374",
  pdf_url: "https://arxiv.org/pdf/2508.02374",
)
#context metadata((meta))

= Typst paper

Reading notes go here. Replace this entry with a real paper and notes.
`;

export const exampleAbout = `#let meta = (
  title: "About",
)
#context metadata((meta))

= About

This site is a content-repo: Typst sources, a stdlib-Python build script, and
an agent as CMS. Edit content/pages/about.typ to say something real.
`;
