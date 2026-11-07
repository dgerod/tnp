# Notes and links

## The tnp-todo tag

Use the inline form for short remarks ::tnp-todo{like this one} inside a sentence. Several ::tnp-todo{first} remarks can share a ::tnp-todo{second} line.

The remark may use inline Markdown: ::tnp-todo{review *this* "term", the **bold** text and the `settings.yaml` file}, or point somewhere with a link ::tnp-todo{see the [Links](#links) below}.

Use the block form for longer notes:

::: tnp-todo
This is a block note. It can use **bold**, lists and other Markdown.

- first item
- second item
:::

## Links

Links to sections work across chapters: back to the [Introduction](#introduction), or forward to the [Conclusions](#conclusions).

## Grouped citations

Several works can be cited together [@pandoc; @mmdc]. Citing a work again, like pandoc [@pandoc], adds another numbered return link to its entry in the references.
