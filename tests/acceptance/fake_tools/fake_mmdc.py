"""Stand-in for `mmdc -i <source> -o <image>`.

Exits with status 1 when the source contains FAIL, to exercise error handling.
"""
import sys

source_path = sys.argv[sys.argv.index("-i") + 1]
image_path = sys.argv[sys.argv.index("-o") + 1]
with open(source_path, encoding="utf-8") as source_file:
    source = source_file.read()
if "FAIL" in source:
    sys.stderr.write("fake mmdc: failure requested\n")
    sys.exit(1)
with open(image_path, "w", encoding="utf-8") as image:
    image.write('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="40">'
                '<text x="10" y="25">fake mermaid %d lines</text></svg>'
                % len(source.splitlines()))
