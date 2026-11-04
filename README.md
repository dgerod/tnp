# Technical Notes Publisher (tnp)

[![Tests](https://github.com/dgerod/tnp/actions/workflows/tests.yml/badge.svg)](https://github.com/dgerod/tnp/actions/workflows/tests.yml)

A toolkit for writing technical notes in Markdown: preview them in VS Code with Markdown Preview Enhanced (MPE) and build them into self-contained HTML reports and books with the CLI.

It requires Python 3.10+ and [pandoc](https://pandoc.org). Diagrams need extra tools only if your notes use them: [PlantUML](https://plantuml.com) (`plantuml.jar` and a Java runtime) and [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) (`mmdc`, installed with Node.js). 

Install a release with [pipx](https://pipx.pypa.io):

```sh
pipx install "git+https://github.com/dgerod/tnp.git@v0.1.1"
tnp --version
```

See the [user manual](docs/user-manual.md) for prerequisites, installing with pip and setting up a workspace, and the [troubleshooting guide](docs/troubleshooting.md) if something goes wrong.