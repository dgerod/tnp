# Technical Notes Writer (tnw)

Command-line tool that manages a workspace of technical notes written in Markdown and builds them to HTML with pandoc, rendering PlantUML and Mermaid diagrams.

See the [user manual](docs/user-manual.md) and, if something goes wrong, the [troubleshooting guide](docs/troubleshooting.md).

```sh
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python tnw-cli.py --version
python -m pytest
```
