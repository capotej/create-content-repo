---
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
