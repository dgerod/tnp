# Technical Notes Writer (tnw)

Command-line tool that manages a workspace of technical notes written in Markdown and builds them to HTML with pandoc, rendering PlantUML and Mermaid diagrams.

See `docs/` for the user manual, the design and the development process.

```sh
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python tnw-cli.py --version
python -m pytest
```
