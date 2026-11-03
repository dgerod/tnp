// tnw HTML output: collapsible table of contents, active-section highlight,
// citation popups and image viewer. Shared by tnw_report.html and tnw_book.html.
(function () {
  "use strict";

  // --- collapsible table of contents ---------------------------------------
  // The sections start folded, opening one folds its siblings, and the
  // section being read unfolds by itself.

  var tocItems = [];
  var tocAllButton = null;

  function setCollapsed(item, collapsed) {
    item.classList.toggle("tnw-collapsed", collapsed);
    item.querySelector(":scope > .tnw-toc-toggle")
      .setAttribute("aria-expanded", collapsed ? "false" : "true");
  }

  function allCollapsed() {
    return tocItems.every(function (item) { return item.classList.contains("tnw-collapsed"); });
  }

  function updateAllButton() {
    if (!tocAllButton) return;
    var label = allCollapsed() ? "Expand all" : "Collapse all";
    tocAllButton.textContent = label;
    tocAllButton.setAttribute("aria-label", label + " sections");
  }

  // Unfold `item` and fold the other sections at its level.
  function openItem(item) {
    Array.prototype.forEach.call(item.parentNode.children, function (sibling) {
      if (sibling !== item && sibling.classList.contains("tnw-has-toggle")) setCollapsed(sibling, true);
    });
    setCollapsed(item, false);
  }

  // Unfold the section of `link` and the sections containing it, leaving the
  // others as they are.
  function revealTocLink(link) {
    for (var item = link.closest("li"); item; item = item.parentNode.closest(".tnw-toc li")) {
      if (item.classList.contains("tnw-has-toggle")) setCollapsed(item, false);
    }
    updateAllButton();
    // Keep the link visible in the sticky sidebar, without scrolling the page.
    var sidebar = document.getElementById("tnw-sidebar");
    if (!sidebar || sidebar.scrollHeight <= sidebar.clientHeight) return;
    var box = sidebar.getBoundingClientRect();
    var rect = link.getBoundingClientRect();
    if (rect.top < box.top) sidebar.scrollTop -= box.top - rect.top + 8;
    else if (rect.bottom > box.bottom) sidebar.scrollTop += rect.bottom - box.bottom + 8;
  }

  function setupToc() {
    var toc = document.querySelector(".tnw-toc");
    if (!toc) return;
    toc.querySelectorAll("li").forEach(function (item) {
      var sublist = item.querySelector(":scope > ul");
      if (!sublist) return;
      var button = document.createElement("button");
      button.type = "button";
      button.className = "tnw-toc-toggle";
      button.setAttribute("aria-label", "Fold or unfold this section");
      button.addEventListener("click", function () {
        if (item.classList.contains("tnw-collapsed")) openItem(item);
        else setCollapsed(item, true);
        updateAllButton();
      });
      item.classList.add("tnw-has-toggle");
      item.insertBefore(button, item.firstChild);
      setCollapsed(item, true);
      tocItems.push(item);
    });

    // A button next to the heading folds the whole table, or unfolds it when
    // every section is already folded.
    var heading = toc.querySelector("h2");
    if (!heading || !tocItems.length) return;
    tocAllButton = document.createElement("button");
    tocAllButton.type = "button";
    tocAllButton.className = "tnw-toc-all";
    tocAllButton.addEventListener("click", function () {
      var collapse = !allCollapsed();
      tocItems.forEach(function (item) { setCollapsed(item, collapse); });
      updateAllButton();
    });
    heading.appendChild(tocAllButton);
    updateAllButton();
  }

  // --- highlight the section being read ------------------------------------

  function setupActiveSection() {
    if (!("IntersectionObserver" in window)) return;
    var links = {};
    document.querySelectorAll(".tnw-toc a[href^='#']").forEach(function (link) {
      links[decodeURIComponent(link.getAttribute("href").slice(1))] = link;
    });
    var headings = Array.prototype.filter.call(
      document.querySelectorAll("#tnw-content h1[id], #tnw-content h2[id], #tnw-content h3[id], " +
                                "#tnw-content section[id] > :is(h1, h2, h3)"),
      function (heading) { return links[heading.id || heading.parentNode.id]; });
    if (!headings.length) return;
    var current = null;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var link = links[entry.target.id || entry.target.parentNode.id];
        if (link === current) return;
        if (current) current.classList.remove("tnw-active");
        current = link;
        current.classList.add("tnw-active");
        revealTocLink(current);
      });
    }, { rootMargin: "0px 0px -70% 0px" });
    headings.forEach(function (heading) { observer.observe(heading); });
  }

  // --- citation popups -------------------------------------------------------

  var popup = null;
  var hideTimer = null;

  function hidePopup() {
    if (popup) {
      popup.remove();
      popup = null;
    }
  }

  function scheduleHide() {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(hidePopup, 250);
  }

  function showPopup(link) {
    var id = decodeURIComponent(link.getAttribute("href").slice(1));
    var entry = document.getElementById(id);
    if (!entry) return;
    clearTimeout(hideTimer);
    hidePopup();

    popup = document.createElement("div");
    popup.className = "tnw-cite-popup";
    popup.setAttribute("role", "tooltip");
    var content = entry.cloneNode(true);
    content.removeAttribute("id");
    content.querySelectorAll("[id]").forEach(function (node) { node.removeAttribute("id"); });
    content.querySelectorAll(".citation-backref").forEach(function (node) { node.remove(); });
    popup.appendChild(content);

    var full = document.createElement("a");
    full.className = "tnw-cite-popup-link";
    full.href = "#" + id;
    full.textContent = "See full reference";
    full.addEventListener("click", hidePopup);
    popup.appendChild(full);

    popup.addEventListener("mouseenter", function () { clearTimeout(hideTimer); });
    popup.addEventListener("mouseleave", scheduleHide);
    document.body.appendChild(popup);

    var rect = link.getBoundingClientRect();
    var left = Math.min(rect.left + window.scrollX,
                        window.scrollX + document.documentElement.clientWidth - popup.offsetWidth - 8);
    popup.style.left = Math.max(window.scrollX + 8, left) + "px";
    popup.style.top = (rect.bottom + window.scrollY + 6) + "px";
  }

  // Light up the reference or citation that a link leads to; the highlight
  // fades away by itself and plays again on every click, even on the same link.
  function flashTarget(id) {
    var target = document.getElementById(id);
    if (!target || !target.matches("div.csl-entry, .citation-anchor")) return;
    target.classList.remove("tnw-flash");
    void target.offsetWidth;  // restart the animation
    target.classList.add("tnw-flash");
  }

  function setupTargetFlash() {
    document.addEventListener("click", function (event) {
      var link = event.target.closest("a[href^='#']");
      if (link) flashTarget(decodeURIComponent(link.getAttribute("href").slice(1)));
    });
    document.addEventListener("animationend", function (event) {
      if (event.animationName === "tnw-flash") event.target.classList.remove("tnw-flash");
    });
    window.addEventListener("hashchange", function () {
      flashTarget(decodeURIComponent(location.hash.slice(1)));
    });
    if (location.hash) flashTarget(decodeURIComponent(location.hash.slice(1)));
  }

  function setupCitationPopups() {
    document.querySelectorAll("#tnw-content a[href^='#ref-']").forEach(function (link) {
      if (link.closest(".csl-entry")) return;
      link.addEventListener("mouseenter", function () { showPopup(link); });
      link.addEventListener("mouseleave", scheduleHide);
      link.addEventListener("focus", function () { showPopup(link); });
      link.addEventListener("blur", scheduleHide);
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") hidePopup();
    });
  }

  // --- image viewer ------------------------------------------------------------
  // Click an image to open it full screen: wheel or +/- to zoom, drag to move,
  // double click or 0 to center it again, Escape to close.

  var MIN_SCALE = 0.1;
  var MAX_SCALE = 20;
  var ZOOM_STEP = 1.25;

  var viewer = null;

  function clampScale(scale) {
    return Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale));
  }

  function applyTransform() {
    viewer.image.style.transform =
      "translate(" + viewer.x + "px, " + viewer.y + "px) scale(" + viewer.scale + ")";
  }

  // Fit the image in the stage (enlarging small diagrams too) and center it.
  function centerImage() {
    var stage = viewer.stage.getBoundingClientRect();
    var width = viewer.width;
    var height = viewer.height;
    viewer.scale = clampScale(Math.min(stage.width * 0.95 / width, stage.height * 0.95 / height));
    viewer.x = (stage.width - width * viewer.scale) / 2;
    viewer.y = (stage.height - height * viewer.scale) / 2;
    applyTransform();
  }

  // Zoom by `factor` keeping the stage point (px, py) still.
  function zoomAt(factor, px, py) {
    var scale = clampScale(viewer.scale * factor);
    factor = scale / viewer.scale;
    viewer.x = px - (px - viewer.x) * factor;
    viewer.y = py - (py - viewer.y) * factor;
    viewer.scale = scale;
    applyTransform();
  }

  function zoomAtCenter(factor) {
    var stage = viewer.stage.getBoundingClientRect();
    zoomAt(factor, stage.width / 2, stage.height / 2);
  }

  function closeViewer() {
    if (!viewer) return;
    viewer.overlay.remove();
    document.removeEventListener("keydown", onViewerKey);
    document.body.classList.remove("tnw-viewer-open");
    if (viewer.source) viewer.source.focus();
    viewer = null;
  }

  function onViewerKey(event) {
    if (event.key === "Escape") closeViewer();
    else if (event.key === "+" || event.key === "=") zoomAtCenter(ZOOM_STEP);
    else if (event.key === "-") zoomAtCenter(1 / ZOOM_STEP);
    else if (event.key === "0") centerImage();
    else return;
    event.preventDefault();
  }

  function toolButton(label, title, action) {
    var button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.title = title;
    button.setAttribute("aria-label", title);
    button.addEventListener("click", action);
    return button;
  }

  function setupDrag(stage) {
    var drag = null;
    stage.addEventListener("pointerdown", function (event) {
      if (event.button !== 0) return;
      drag = { id: event.pointerId, x: event.clientX - viewer.x, y: event.clientY - viewer.y };
      stage.setPointerCapture(event.pointerId);
      stage.classList.add("tnw-dragging");
      event.preventDefault();
    });
    stage.addEventListener("pointermove", function (event) {
      if (!drag || event.pointerId !== drag.id) return;
      viewer.x = event.clientX - drag.x;
      viewer.y = event.clientY - drag.y;
      applyTransform();
    });
    function endDrag(event) {
      if (!drag || event.pointerId !== drag.id) return;
      drag = null;
      stage.classList.remove("tnw-dragging");
    }
    stage.addEventListener("pointerup", endDrag);
    stage.addEventListener("pointercancel", endDrag);
  }

  function openViewer(source) {
    closeViewer();
    var overlay = document.createElement("div");
    overlay.className = "tnw-viewer";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", source.alt || "Image viewer");

    var stage = document.createElement("div");
    stage.className = "tnw-viewer-stage";
    var image = document.createElement("img");
    image.src = source.currentSrc || source.src;
    image.alt = source.alt;
    image.draggable = false;
    stage.appendChild(image);

    var toolbar = document.createElement("div");
    toolbar.className = "tnw-viewer-toolbar";
    toolbar.appendChild(toolButton("+", "Zoom in (+)", function () { zoomAtCenter(ZOOM_STEP); }));
    toolbar.appendChild(toolButton("−", "Zoom out (-)", function () { zoomAtCenter(1 / ZOOM_STEP); }));
    toolbar.appendChild(toolButton("⤢", "Center (0)", centerImage));
    var close = toolButton("×", "Close (Esc)", closeViewer);
    toolbar.appendChild(close);

    overlay.appendChild(stage);
    overlay.appendChild(toolbar);
    document.body.appendChild(overlay);
    document.body.classList.add("tnw-viewer-open");

    // SVGs without a width have no natural size; fall back to the page size.
    var rect = source.getBoundingClientRect();
    viewer = {
      overlay: overlay, stage: stage, image: image, source: source,
      width: source.naturalWidth || rect.width || 300,
      height: source.naturalHeight || rect.height || 150,
      scale: 1, x: 0, y: 0
    };
    image.style.width = viewer.width + "px";
    image.style.height = viewer.height + "px";
    centerImage();

    stage.addEventListener("wheel", function (event) {
      event.preventDefault();
      var box = stage.getBoundingClientRect();
      zoomAt(event.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP,
             event.clientX - box.left, event.clientY - box.top);
    }, { passive: false });
    stage.addEventListener("dblclick", centerImage);
    setupDrag(stage);
    document.addEventListener("keydown", onViewerKey);
    close.focus();
  }

  function setupImageViewer() {
    document.querySelectorAll("#tnw-content img").forEach(function (image) {
      if (image.closest("a")) return;  // a linked image keeps its link
      image.classList.add("tnw-zoomable");
      image.tabIndex = 0;
      image.addEventListener("click", function () { openViewer(image); });
      image.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openViewer(image);
        }
      });
    });
  }

  function init() {
    setupToc();
    setupActiveSection();
    setupCitationPopups();
    setupTargetFlash();
    setupImageViewer();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
