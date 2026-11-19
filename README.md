# Technical Notes Publisher (tnp)

[![Tests](https://github.com/dgerod/tnp/actions/workflows/tests.yml/badge.svg)](https://github.com/dgerod/tnp/actions/workflows/tests.yml)

A toolkit for writing technical notes in Markdown: preview them in VS Code with Markdown Preview Enhanced (MPE) and build them into self-contained HTML reports and books with the CLI.

- **Reports and books:** build a single note, or a book of several chapters described by a `book.yaml`, with metadata (DID, version, date, keywords) in a sidebar and a table of contents.
- **Diagrams:** [PlantUML](https://plantuml.com) and [Mermaid](https://mermaid.js.org) blocks, written inline or imported from a file (`::tnp-puml{...}`, `::tnp-mmd{...}`), rendered and embedded as images.
- **Mathematics:** LaTeX formulas rendered with MathJax.
- **Citations:** BibTeX bibliographies, with numbered references that link back to where they are cited.
- **Annotations:** `::tnp-todo{...}` and `::: tnp-todo` highlight remarks and pending work in the text.
- **Reader comments:** in the built HTML, readers can highlight text and add notes, list them in a side panel, and export or import them as a `.annotations.json` file to share them.
- **Self-contained output:** styles, images, diagrams and MathJax are embedded, so the HTML opens without network access and prints to PDF from the browser.

It requires Python 3.10+ and [pandoc](https://pandoc.org). Diagrams need extra tools only if your notes use them: [PlantUML](https://plantuml.com) (`plantuml.jar` and a Java runtime) and [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) (`mmdc`, installed with Node.js). 

Install a release with [pipx](https://pipx.pypa.io):

```sh
pipx install "git+https://github.com/dgerod/tnp.git@v0.1.3"
tnp --version
```

See the [user manual](docs/user-manual.md) for prerequisites, installing with pip and setting up a workspace, and the [troubleshooting guide](docs/troubleshooting.md) if something goes wrong.