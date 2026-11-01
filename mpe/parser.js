// Markdown Preview Enhanced parser hooks for tnw.
// JavaScript counterpart of the pandoc filters: keep the regexes in sync with
// tnw_cli/pandoc-filters/todo_tag.py so the preview matches the HTML output.
(function () {
  var CODE_FENCE = /^\s*(```|~~~)/;

  // Rewrite every line outside fenced code with rewriteLine(line), which
  // returns the replacement line (or an array of lines).
  function rewriteOutsideCode(markdown, rewriteLine) {
    var output = [];
    var fence = null;
    markdown.split("\n").forEach(function (line) {
      var fenceMatch = line.match(CODE_FENCE);
      if (fenceMatch) {
        if (fence === null) {
          fence = fenceMatch[1];
        } else if (fenceMatch[1] === fence) {
          fence = null;
        }
        output.push(line);
        return;
      }
      if (fence !== null) {
        output.push(line);
        return;
      }
      var rewritten = rewriteLine(line);
      if (Array.isArray(rewritten)) {
        output.push.apply(output, rewritten);
      } else {
        output.push(rewritten);
      }
    });
    return output.join("\n");
  }

  // The tnw-todo tag: inline `::tnw-todo{...}` becomes a span and the block
  // `::: tnw-todo ... :::` a div, both with class "todo" (styled in
  // style.less). The deprecated `todo` spelling is still accepted.
  function renderTnwTodo(markdown) {
    var INLINE_TODO = /::(?:tnw-todo|todo)\{([^}]*)\}/g;
    var BLOCK_TODO_OPEN = /^:::\s*(?:tnw-todo|todo)\s*$/;
    var DIV_OPEN = /^:::+\s*\S/;
    var DIV_CLOSE = /^:::+\s*$/;
    var divStack = []; // true for a tnw-todo div, false for any other div

    return rewriteOutsideCode(markdown, function (line) {
      if (BLOCK_TODO_OPEN.test(line)) {
        divStack.push(true);
        return ['<div class="todo">', ""];
      }
      if (DIV_CLOSE.test(line) && divStack.length > 0) {
        if (divStack.pop()) {
          return ["", "</div>"];
        }
      } else if (DIV_OPEN.test(line)) {
        divStack.push(false);
      }
      return line.replace(INLINE_TODO, function (_match, content) {
        return '<span class="todo">' + content + "</span>";
      });
    });
  }

  // The diagram import tags `::tnw-mmd{file}` / `::tnw-puml{file}`, alone on
  // their line, become MPE's native `@import "file"`.
  function renderImportTags(markdown) {
    var IMPORT_TAG = /^\s*::tnw-(?:mmd|puml)\{([^}]+)\}\s*$/;

    return rewriteOutsideCode(markdown, function (line) {
      var importMatch = line.match(IMPORT_TAG);
      return importMatch ? '@import "' + importMatch[1].trim() + '"' : line;
    });
  }

  return {
    onWillParseMarkdown: async function (markdown) {
      return renderImportTags(renderTnwTodo(markdown));
    },

    onDidParseMarkdown: async function (html) {
      return html;
    },
  };
})()
