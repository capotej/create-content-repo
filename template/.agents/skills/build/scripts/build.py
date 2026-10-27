#!/usr/bin/env python3
"""Deterministic build orchestrator for the content-repo.

Stdlib only. Walks content/, reads per-file meta via typst eval, compiles
each .typ to an HTML fragment via the pinned typst compiler, wraps it in a
minimal page shell, emits index pages, an Atom feed, _redirects, and copies
assets/ into build/.

Usage: python3 .agents/skills/build/scripts/build.py   (from repo root)
"""

import hashlib
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
THEME = REPO / "theme"
WRAPPER = THEME / "wrapper.typ"
STYLE = THEME / "style.css"

META_EXPR = "query(metadata).map(it => it.value)"

# Inline code-token colors look like: style="color: #cba6f7"
SPAN_COLOR = re.compile(r'style="color: (#[0-9a-fA-F]{6})"')
# Remap selectors in theme/style.css look like: span[style*="#cba6f7"]
CSS_REMAP = re.compile(r'span\[style\*="(#[0-9a-fA-F]{6})"\]')

SECTIONS = ("posts", "links", "papers", "pages")

# Site identity — the scaffolder substitutes {{NAME}} / {{YEAR}} here;
# BASE_URL should be edited to the deployed origin before launch (it
# feeds absolute Atom links + the feed id).
SITE_NAME = "{{NAME}}"
BASE_URL = "https://{{NAME}}.netlify.app"

# Home listing pagination (legacy Abbey parity: 5 posts/page, path-based
# /page/N/ URLs — a static host cannot route ?page=N query strings).
PER_PAGE = 5

NAV = (
    '<nav><a href="/">Home</a> <a href="/links/">Links</a> '
    '<a href="/papers/">Papers</a> <a href="/about/">About</a></nav>'
)

FOOTER = (
    '<footer><p>© {{YEAR}} {}. All rights reserved.</p></footer>'
    .format(SITE_NAME)
)

SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="alternate" type="application/atom+xml" title="ATOM" href="/atom.xml">
{head}
<style>
{style}
</style>
</head>
<body>
<header>
<a href="/"><h1>{site_name}</h1></a>
{nav}
</header>
<main>
{body}
</main>
{footer}
</body>
</html>
"""

# SPIKE tier-2 theme: typst owns code colors at compile time (theme/wrapper.typ
# + theme/catppuccin.tmTheme via #set raw(theme:...)); theme/style.css owns the
# page chrome typst's semantic HTML export cannot express (fonts, bg, spacing)
# and the light-mode remap of the baked code colors. Loaded in main().

ATOM_ENTRY = """<entry>
<title>{title}</title>
<link href="{link}"/>
<id>{id}</id>
<published>{published}</published>
<updated>{updated}</updated>
<summary type="html">{summary}</summary>
<content type="html">{content}</content>
</entry>
"""

ATOM_FEED = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en">
<title>{title}</title>
<id>{id}</id>
<link href="{base}"/>
<link rel="self" type="application/atom+xml" href="{self_url}"/>
<updated>{updated}</updated>
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


def run(cmd, env, what, stdin=None):
    p = subprocess.run(cmd, capture_output=True, text=True, env=env,
                       input=stdin)
    if p.returncode != 0:
        die(what + " failed:\n" + (p.stderr or p.stdout))
    return p.stdout


def compile_excerpt(path, cmd, env):
    """Compile a post's `#let excerpt` content block (if declared) to an
    HTML fragment via a stdin driver that imports it. Returns "" when the
    post declares no excerpt."""
    text = path.read_text("utf-8")
    if not re.search(r"^#let excerpt\b", text, re.M):
        return ""
    rel = "/" + str(path.relative_to(REPO))
    out = run(cmd + ["compile", "-", "--root", str(REPO),
                     "--features", "html", "--format", "html", "-"], env,
              "compiling excerpt of " + str(path),
              stdin='#import "' + rel + '": excerpt\n#excerpt\n')
    m = re.search(r"<body>(.*)</body>", out, re.DOTALL)
    if not m:
        die("no <body> in typst output for excerpt of " + str(path))
    return m.group(1).strip()


def read_meta(path, cmd, env):
    out = run(cmd + ["eval", "--features", "html", META_EXPR,
                     "--in", str(path)], env,
              "reading meta from " + str(path))
    try:
        items = json.loads(out)
    except json.JSONDecodeError:
        die("meta eval did not return JSON for " + str(path))
    if not items:
        die("no meta found in " + str(path) +
            " (need '#context metadata((meta))' after the '#let meta' dict)")
    return items[0]


def check_code_colors(body, rel, remapped):
    """Every inline code-token color must have a light-mode remap entry in
    theme/style.css — otherwise light mode silently shows dark-mode code.
    The css selectors are the single source of truth (parsed in main)."""
    for color in SPAN_COLOR.findall(body):
        if color.lower() not in remapped:
            die("code color " + color + " has no light-mode remap in "
                + str(STYLE) + " (source: " + str(rel) + ")")


def compile_body(path, cmd, env):
    # SPIKE tier-2: compile through theme/wrapper.typ so its #set rules (code
    # theme) apply; --input passes the target; --root keeps root-absolute
    # content paths and /assets refs resolving.
    rel = "/" + str(path.relative_to(REPO))
    out = run(cmd + ["compile", str(WRAPPER), "--root", str(REPO),
                     "--input", "target=" + rel,
                     "--features", "html", "--format", "html", "-"], env,
              "compiling " + str(path))
    m = re.search(r"<body>(.*)</body>", out, re.DOTALL)
    if not m:
        die("no <body> in typst output for " + str(path))
    return m.group(1).strip()


DATE_PREFIX = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)$")

# Tag values must be URL slugs (they become /t/<tag>/ pages): lowercase
# alphanumerics with single interior hyphens.
TAG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def insert_time(body, date):
    """Post pages show the date under the title: a <time> element inserted
    after the first <h2> (the post title heading, exported by typst)."""
    i = body.find("<h2>")
    if i == -1:
        return body
    j = i + len("<h2>")
    k = body.find("</h2>", j)
    if k == -1:
        return body
    return (body[:k + len("</h2>")]
            + '\n<time>' + h(date) + "</time>"
            + body[k + len("</h2>"):])


def tag_pills(tags):
    """Legacy Abbey tag pills: '# tag' links to the /t/<tag>/ page."""
    if not tags:
        return ""
    lis = "".join(
        '<li><a href="/t/{}/"># {}</a></li>'.format(h(t), h(t))
        for t in tags)
    return '<ul class="tags">' + lis + "</ul>"


def split_dated(stem, rel):
    m = DATE_PREFIX.match(stem)
    if not m:
        die("filename must be YYYY-MM-DD-slug.typ: " + rel)
    return m.group(1), m.group(2), m.group(3), m.group(4)


def page(path, title, body, style, head=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        SHELL.format(title=h(title + " | " + SITE_NAME)
                     if title != "Home" else h(SITE_NAME),
                     site_name=h(SITE_NAME),
                     nav=NAV, body=body, style=style, footer=FOOTER,
                     head=head),
        "utf-8")


NOT_FOUND = """<h2>The page you were looking for doesn't exist.</h2>
<p>You may have mistyped the address or the page may have moved.</p>
<p><a href="/">Back to the home page</a></p>
"""


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
    if not WRAPPER.is_file():
        die("missing theme wrapper: " + str(WRAPPER))
    if not STYLE.is_file():
        die("missing theme stylesheet: " + str(STYLE))
    style = STYLE.read_text("utf-8")
    remapped = set(c.lower() for c in CSS_REMAP.findall(style))
    if not remapped:
        die("no code-color remap selectors (span[style*=...]) found in "
            + str(STYLE))
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
            check_code_colors(body, rel, remapped)
            pills = ""

            if section == "posts":
                y, m, d, slug = split_dated(f.stem, rel)
                if str(meta.get("date", "")) != "-".join((y, m, d)):
                    die("meta.date does not match filename prefix: " + str(rel))
                feed_content = body
                body = insert_time(body, meta.get("date", ""))
                url = "/{}/{}/{}/{}/".format(y, m, d, slug)
                rf = meta.get("redirect_from")
                if rf:
                    olds = [rf] if isinstance(rf, str) else list(rf)
                    redirects += ["{}    {}".format(o, url) for o in olds]
                tags = meta.get("tags", ())
                if isinstance(tags, str):
                    tags = (tags,)
                tags = [str(t) for t in tags]
                for t in tags:
                    if not TAG_RE.match(t):
                        die("tag is not a slug (lowercase alphanumerics, "
                            "single interior hyphens): " + repr(t)
                            + " in " + str(rel))
                pills = tag_pills(tags)
                published["posts"].append({
                    "date": meta.get("date", ""),
                    "title": title,
                    "url": url,
                    "tags": tags,
                    "content": feed_content,
                    "excerpt": compile_excerpt(f, cmd, env),
                    # second-precision timestamps; default to date 00:00:00
                    "created": str(meta.get("created",
                                             meta.get("date", "") + " 00:00:00")),
                    "updated": str(meta.get("updated",
                                             meta.get("date", "") + " 00:00:00")),
                })
            elif section == "links":
                y, m, d, slug = split_dated(f.stem, rel)
                url = "/links/{}/".format(slug)
                out_url = str(meta.get("url", ""))
                link_line = ('<p><a href="' + h(out_url) + '">' + h(title)
                             + "</a></p>")
                published["links"].append({
                    "date": meta.get("date", ""),
                    "title": title,
                    "url": url,            # local /links/<slug>/ page
                    "out_url": out_url,
                    "body": body,
                })
            elif section == "papers":
                y, m, d, slug = split_dated(f.stem, rel)
                arxiv = str(meta.get("arxiv_id", ""))
                pdf = str(meta.get("pdf_url", ""))
                if not pdf:
                    die("papers need a pdf_url (external pdf link): "
                        + str(rel))
                published["papers"].append({
                    "date": meta.get("date", ""),
                    "title": title,
                    "out_url": pdf,
                    "arxiv": arxiv,
                    "body": body,
                })
                continue
            else:  # pages
                url = "/{}/".format(f.stem)
                link_line = ""
                rf = meta.get("redirect_from")
                if rf:
                    olds = [rf] if isinstance(rf, str) else list(rf)
                    redirects += ["{}    {}".format(o, url) for o in olds]

            out = BUILD / url.lstrip("/") / "index.html"
            extra = link_line if section in ("links", "papers") else ""
            page(out, title, body + pills + extra, style)
            print("ok: " + url + "  <- " + str(rel))

    # Index pages -----------------------------------------------------------
    def listing(items, header):
        rows = ['<h2>' + h(header) + "</h2>", "<ul>"]
        for date, title, url in sorted(items, reverse=True):
            rows.append("<li>{} — <a href=\"{}\">{}</a></li>".format(
                h(str(date)), h(url), h(title)))
        rows.append("</ul>")
        return "\n".join(rows)

    def link_entry(l):
        """One links-index entry, post-index style: outbound title link
        with an external-link glyph, a citation line (url · date), and
        the note body beneath (legacy /links parity). The note body opens
        with an '= title' heading that would duplicate the title link —
        strip it."""
        body = l["body"]
        if body.startswith("<h2>"):
            end = body.find("</h2>")
            if end != -1:
                body = body[end + len("</h2>"):].lstrip()
        cite = ('<a href="{url}">{url}</a> <time>{date}</time>').format(
            url=h(l["out_url"]), date=h(l["date"]))
        return """<li><a class="post-title" href="{url}">{title}<svg class="icon-external" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg></a>
<p class="cite">{cite}</p>
{body}
</li>""".format(url=h(l["out_url"]), title=h(l["title"]), cite=cite,
               body=body)

    def paper_entry(p):
        """One papers-index entry, links-index style: outbound pdf title
        link with the external-link glyph, citation line (url [arXiv:id] ·
        date), note body beneath. Leading title heading stripped."""
        body = p["body"]
        if body.startswith("<h2>"):
            end = body.find("</h2>")
            if end != -1:
                body = body[end + len("</h2>"):].lstrip()
        cite = ('<a href="{url}">{url}</a>{arxiv} <time>{date}</time>').format(
            url=h(p["out_url"]),
            arxiv=(" arXiv:" + h(p["arxiv"])) if p["arxiv"] else "",
            date=h(p["date"]))
        return """<li><a class="post-title" href="{url}">{title}<svg class="icon-external" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg></a>
<p class="cite">{cite}</p>
{body}
</li>""".format(url=h(p["out_url"]), title=h(p["title"]), cite=cite,
               body=body)

    def paper_listing(items, header):
        """Papers index: ul.posts entries styled like the links index."""
        rows = ['<h2>' + h(header) + "</h2>", '<ul class="posts">']
        for p in items:
            rows.append(paper_entry(p))
        rows.append("</ul>")
        return "\n".join(rows)

    def post_entry(p):
        """One listing entry: title, muted date, excerpt, pills + read-more
        (shared by the home page and tag pages)."""
        rows = ['<li><a class="post-title" href="{}">{}</a>'.format(
            h(p["url"]), h(p["title"]))]
        rows.append("<time>" + h(p["date"]) + "</time>")
        if p["excerpt"]:
            rows.append('<div class="excerpt">' + p["excerpt"] + "</div>")
        rows.append(tag_pills(p["tags"]))
        rows.append('<p class="more"><a href="{}">Read more →</a></p>'
                    .format(h(p["url"])))
        rows.append("</li>")
        return "\n".join(rows)

    def link_listing(items, header):
        """Links index: ul.posts entries styled like the home listing."""
        rows = ['<h2>' + h(header) + "</h2>", '<ul class="posts">']
        for l in items:
            rows.append(link_entry(l))
        rows.append("</ul>")
        return "\n".join(rows)

    def post_listing(items, header):
        """Post listings (home + tag pages): entries styled by ul.posts."""
        rows = ['<h2>' + h(header) + "</h2>", '<ul class="posts">']
        for p in sorted(items, key=lambda p: p["created"], reverse=True):
            rows.append(post_entry(p))
        rows.append("</ul>")
        return "\n".join(rows)

    # Paginated listings (home, tag pages, links) ---------------------------
    # Page 1 is the canonical <base>/ URL; pages 2+ live at <base>/page/N/.
    # <base>/page/1/ redirects so there is exactly one URL for page 1.
    def pager(href_for, current, n_pages):
        """Numbered links + Prev/Next, legacy Abbey style."""
        if n_pages <= 1:
            return ""
        out = ['<nav class="pager">']
        for n in range(1, n_pages + 1):
            if n == current:
                out.append('<span aria-current="page">{}</span>'.format(n))
            else:
                out.append('<a href="{}">{}</a>'.format(href_for(n), n))
        if current > 1:
            out.append('<a rel="prev" href="{}">‹ Prev</a>'
                       .format(href_for(current - 1)))
        if current < n_pages:
            out.append('<a rel="next" href="{}">Next ›</a>'
                       .format(href_for(current + 1)))
        out.append("</nav>")
        return "".join(out)

    def emit_paginated(url_base, title, items, body_for, per_page=PER_PAGE):
        """Write <url_base>/ plus <url_base>/page/N/ for a listing.
        body_for(chunk) renders one page's entries; items arrive sorted."""
        def href_for(n):
            return url_base + "/" if n == 1 else url_base + "/page/{}/".format(n)

        dir_base = BUILD / url_base.lstrip("/")
        n_pages = max(1, -(-len(items) // per_page))
        for cur in range(1, n_pages + 1):
            chunk = items[(cur - 1) * per_page:cur * per_page]
            nav_html = pager(href_for, cur, n_pages)
            if cur == 1:
                head = ('<link rel="next" href="{}">'.format(href_for(2))
                        if n_pages > 1 else "")
                page(dir_base / "index.html", title,
                     body_for(chunk) + nav_html, style, head=head)
            else:
                head = '<link rel="prev" href="{}">'.format(href_for(cur - 1))
                if cur < n_pages:
                    head += '<link rel="next" href="{}">'.format(
                        href_for(cur + 1))
                page(dir_base / "page" / str(cur) / "index.html",
                     title + " — page {}".format(cur),
                     body_for(chunk) + nav_html, style, head=head)
            print("ok: {}  ({} entries{})".format(
                href_for(cur), len(chunk),
                ", {} pages".format(n_pages) if cur == 1 and n_pages > 1
                else ""))
        if n_pages > 1:
            redirects.append("{}    {}    301".format(
                href_for(1) + "page/1/", href_for(1)))

    posts = sorted(published["posts"], key=lambda p: p["created"],
                   reverse=True)
    emit_paginated("", "Home", posts,
                   lambda chunk: post_listing(chunk, "Posts"))
    # Legacy parity: links/papers paginate at 15/page; home + tag pages at 5.
    LINKS_PER_PAGE = 15
    emit_paginated("/links", "Links",
                   sorted(published["links"],
                          key=lambda l: l["date"], reverse=True),
                   lambda chunk: link_listing(chunk, "Links"),
                   per_page=LINKS_PER_PAGE)
    emit_paginated("/papers", "Papers",
                   sorted(published["papers"],
                          key=lambda p: p["date"], reverse=True),
                   lambda chunk: paper_listing(chunk, "Papers"),
                   per_page=LINKS_PER_PAGE)

    # Tag pages (/t/<tag>/) — parity with legacy Abbey -----------------------
    # Entry shape mirrors the tag page of the legacy site: title link, date,
    # excerpt, tag pills. No global /tags/ index (legacy 404s on it).
    tagmap = {}
    for p in published["posts"]:
        for t in p["tags"]:
            tagmap.setdefault(t, []).append(p)
    for t in sorted(tagmap):
        entries = sorted(tagmap[t], key=lambda p: p["created"], reverse=True)
        emit_paginated("/t/" + t, "#" + t, entries,
                       lambda chunk, t=t: post_listing(
                           chunk, 'Posts tagged with "#{}"'.format(t)))

    # Atom feed (posts) -----------------------------------------------------
    def iso(ts):
        return ts.replace(" ", "T") + "Z"

    def entry_id(p):
        """Stable entry id: sha256(title + created). The trailing " UTC"
        mirrors the legacy Rails scheme (Time#to_s on a UTC timestamp) —
        posts imported with their original `created` keep byte-compatible
        feed ids across the migration."""
        return hashlib.sha256(
            (p["title"] + p["created"] + " UTC").encode("utf-8")
        ).hexdigest()

    posts = sorted(published["posts"], key=lambda p: p["created"],
                   reverse=True)
    if posts:
        entries = "".join(
            ATOM_ENTRY.format(
                title=xescape(p["title"]), link=xescape(BASE_URL + p["url"]),
                id=entry_id(p),
                published=iso(p["created"]), updated=iso(p["updated"]),
                summary=xescape(p["excerpt"]),
                content=xescape(p["content"]),
            ) for p in posts)
        feed_updated = max(iso(p["updated"]) for p in posts)
        (BUILD / "atom.xml").write_text(
            ATOM_FEED.format(title=SITE_NAME + " - Feed",
                             id="tag:{{NAME}},2005:/feed",
                             base=BASE_URL,
                             self_url=BASE_URL + "/atom.xml",
                             updated=feed_updated,
                             entries=entries), "utf-8")
        print("ok: /atom.xml")

    # _redirects ------------------------------------------------------------
    if redirects:
        (BUILD / "_redirects").write_text("\n".join(redirects) + "\n", "utf-8")
        print("ok: _redirects ({} lines)".format(len(redirects)))

    # 404 ----------------------------------------------------------------------
    page(BUILD / "404.html", "Not Found", NOT_FOUND, style)
    print("ok: 404.html")

    # Assets ----------------------------------------------------------------
    if ASSETS.is_dir():
        shutil.copytree(ASSETS, BUILD / "assets")
        print("ok: assets/ -> build/assets/")

    n = sum(len(v) for v in published.values()) + len(files["pages"])
    print("done: {} pages + indexes + feed -> build/".format(n))


def verify():
    """Rebuild into a temp dir and require byte-identical output vs the
    existing build/. Catches accidental hand-edits to build/ and any
    nondeterminism in the pipeline. Exit non-zero on any difference."""
    import tempfile

    global BUILD
    problems = []

    if not real_build_root().is_dir():
        print("verify: no existing build/ — run a plain build first",
              file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        BUILD = Path(tmp) / "build"
        main()

        existing = real_build_root()
        for old in existing.rglob("*"):
            rel = old.relative_to(existing)
            new = BUILD / rel
            if not new.exists():
                problems.append("missing on rebuild: " + str(rel))
            elif old.is_file():
                if not new.is_file():
                    problems.append("type mismatch: " + str(rel))
                elif old.read_bytes() != new.read_bytes():
                    problems.append("content differs: " + str(rel))
        for new in BUILD.rglob("*"):
            rel = new.relative_to(BUILD)
            if not (existing / rel).exists():
                problems.append("extra on rebuild: " + str(rel))

    if problems:
        print("verify: FAILED — build/ differs from a fresh rebuild:",
              file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        sys.exit(1)
    print("verify: ok — build/ is byte-identical on rebuild")


def real_build_root():
    return REPO / "build"


if __name__ == "__main__":
    if "--verify" in sys.argv[1:]:
        verify()
    else:
        main()
