# Technical Notes Publisher (tnp)

[![Tests](https://github.com/dgerod/tnp/actions/workflows/tests.yml/badge.svg)](https://github.com/dgerod/tnp/actions/workflows/tests.yml)

A toolkit for writing technical notes in Markdown: preview them in VS Code with Markdown Preview Enhanced (MPE) and build them into self-contained HTML reports and books with the CLI.

It requires Python 3.10+ and [pandoc](https://pandoc.org). Diagrams need extra tools only if your notes use them: [PlantUML](https://plantuml.com) (`plantuml.jar` and a Java runtime) and [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) (`mmdc`, installed with Node.js).

See the [user manual](docs/user-manual.md) and, if something goes wrong, the [troubleshooting guide](docs/troubleshooting.md).

```sh
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python tnp-cli.py --version
python -m pytest
```
