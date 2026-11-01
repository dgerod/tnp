# Introduction

This is an example **book** built with `tnw`. A book is several Markdown chapters listed in `book.yaml`; its title, author and the metadata shown under the title (DID, version, date and keywords) come from that file, not from the chapters.

`tnw` converts the chapters with pandoc [@pandoc] and adds a few things on top:

- PlantUML and Mermaid diagrams rendered to images (see [Figures and diagrams](#figures-and-diagrams)).
- Mathematics rendered with MathJax (see [Mathematics](#mathematics)).
- The `tnw-todo` tag to highlight pending work (see [Notes and links](#notes-and-links)).
- Citations with return links from the [References](#references).

## How to build it

From anywhere inside a `tnw` workspace:

```sh
tnw build_book html examples/book/book.yaml
```

The result is written to `build/example-book.html` at the workspace root.
::tnw-todo{Add a screenshot of the generated book here.}
