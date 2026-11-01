// tnw HTML output: collapsible table of contents, active-section highlight
// and citation popups. Shared by tnw_report.html and tnw_book.html.
(function () {
  "use strict";

  // --- collapsible table of contents ---------------------------------------

  function setupToc() {
    var toc = document.querySelector(".tnw-toc");
    if (!toc) return;
    toc.querySelectorAll("li").forEach(function (item) {
      var sublist = item.querySelector(":scope > ul");
      if (!sublist) return;
      var button = document.createElement("button");
      button.type = "button";
      button.className = "tnw-toc-toggle";
      button.setAttribute("aria-expanded", "true");
      button.setAttribute("aria-label", "Fold or unfold this section");
      button.addEventListener("click", function () {
        var collapsed = item.classList.toggle("tnw-collapsed");
        button.setAttribute("aria-expanded", collapsed ? "false" : "true");
      });
      item.classList.add("tnw-has-toggle");
      item.insertBefore(button, item.firstChild);
    });
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
        if (current) current.classList.remove("tnw-active");
        current = link;
        current.classList.add("tnw-active");
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

  function init() {
    setupToc();
    setupActiveSection();
    setupCitationPopups();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
