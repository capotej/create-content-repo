#!/usr/bin/env python3
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
