"""Stand-in for `java -jar plantuml.jar -pipe -t<ext>`: source on stdin, image on stdout.

Exits with status 1 when the source contains FAIL, to exercise error handling.
"""
import sys

source = sys.stdin.read()
if "FAIL" in source:
    sys.stderr.write("fake plantuml: failure requested\n")
    sys.exit(1)
sys.stdout.write('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="40">'
                 '<text x="10" y="25">fake plantuml %d lines</text></svg>'
                 % len(source.splitlines()))
