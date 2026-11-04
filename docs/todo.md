---
title: To-do
subtitle: Technical Notes Publisher (tnp)
---

# To-do

This is a list of missing functionality and potential improvements of the tool:

- [ ] Create a video explaining what TNP is and how to use it.
- [ ] Test the diagram filters against the real PlantUML and Mermaid CLI on Linux and Windows, and add a CI job that does it (`mmdc` may need a puppeteer configuration with `--no-sandbox` on Linux).
- [ ] Create a `version` module in `common` that does the functionality related to versions in addition to compatibility.
- [ ] Review `workspace` in `common` and split it into several functionalities if possible.
- [ ] Support formatting (emphasis, code, links) inside an inline `::tnp-todo{...}`; today the tag only works with plain text and is otherwise left as is.
- [ ] Center diagrams like figures (they are plain image paragraphs today).
- [ ] Limit the on-screen height of images to 30% of the window height, so they do not break the flow of reading the document.
- [x] Migrate pandoc filters using `pandocfilters` to `panflute`.
- [x] Make it work on GNU/Linux (cross-platform).
- [x] Make the generated HTML independent of the network (MathJax embedded).
