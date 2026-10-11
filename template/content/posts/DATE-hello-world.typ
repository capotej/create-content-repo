#let meta = (
  title: "Hello, world",
  date: "{{DATE}}",
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
- Code blocks are syntax-highlighted and themed by the repo's theme
  (colors baked in at compile time; light/dark follows the OS setting):

```typst
#let meta = (title: "Hello, world", date: "2026-01-15")
#context metadata((meta))
= A heading
Some *bold* text and _emphasis_.
```

Edit or delete this file; then rebuild.
