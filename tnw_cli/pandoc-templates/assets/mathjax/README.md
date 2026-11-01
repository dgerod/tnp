# MathJax (vendored)

`tex-svg-full.js` is MathJax 3.2.2 (`es5/tex-svg-full.js` from the `mathjax` npm package), licensed under the Apache License 2.0 (see `LICENSE`).

It is embedded into every generated HTML document that contains math, so the output renders formulas without network access. The SVG output is used because it carries its fonts inside the script; the `-full` bundle preloads every TeX extension instead of fetching them on demand. MathJax 4 is not used because it loads its fonts as separate files.
