(() => {
  'use strict';
  if (window.__anotador) return;
  window.__anotador = true;

  const PARAMS = (document.currentScript && document.currentScript.dataset) || {};
  const KEY = 'anotador:v1:' + location.pathname;
  const COLORS = { yellow: [255, 205, 0], green: [60, 200, 110], blue: [70, 150, 255], pink: [255, 90, 160] };
  const USER_KEY = 'anotador:v1:user';
  const CTX = 32;
  const SKIP = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEXTAREA', 'SELECT', 'OPTION', 'TEMPLATE']);

  let notes = load();
  let lastColor = 'yellow';
  let lastUser = loadUser();
  let pending = null;
  let editing = null;
  let host, toolbar, pop, who, ta, panel, list, empty, fab, fileInput, dlg, dlgText, dlgOk, dlgCancel;
  let dlgDone = null;
  let renderTimer, selTimer, pointerDown = false;
  const observer = new MutationObserver(() => {
    clearTimeout(renderTimer);
    renderTimer = setTimeout(renderAll, 120);
  });

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; }
  }
  function loadUser() {
    try { return localStorage.getItem(USER_KEY) || ''; } catch (e) { return ''; }
  }
  function saveUser(user) {
    lastUser = user;
    try { localStorage.setItem(USER_KEY, user); } catch (e) {}
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(notes)); } catch (e) {}
    refreshPanel();
  }

  function textMap() {
    const nodes = [];
    let text = '';
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(n) {
        for (let p = n.parentNode; p && p !== document.body; p = p.parentNode)
          if (SKIP.has(p.nodeName)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    for (let n; (n = walker.nextNode());) {
      nodes.push({ node: n, start: text.length, end: text.length + n.data.length });
      text += n.data;
    }
    return { text, nodes };
  }

  function describe(range) {
    const { text, nodes } = textMap();
    let start = -1, end = -1;
    for (const e of nodes) {
      if (!range.intersectsNode(e.node)) continue;
      if (start < 0) start = e.start + (e.node === range.startContainer ? range.startOffset : 0);
      end = e.start + (e.node === range.endContainer ? range.endOffset : e.node.data.length);
    }
    if (start < 0 || end <= start) return null;
    const exact = text.slice(start, end);
    if (!exact.trim()) return null;
    return { exact, prefix: text.slice(Math.max(0, start - CTX), start), suffix: text.slice(end, end + CTX) };
  }

  function locate(a, text) {
    let best = -1, bestScore = -1;
    for (let i = text.indexOf(a.exact); i >= 0; i = text.indexOf(a.exact, i + 1)) {
      const after = i + a.exact.length;
      const score = sameEnd(text.slice(Math.max(0, i - CTX), i), a.prefix || '') +
                    sameStart(text.slice(after, after + CTX), a.suffix || '');
      if (score > bestScore) { best = i; bestScore = score; }
    }
    return best;
  }
  function sameStart(x, y) { let k = 0; while (k < x.length && k < y.length && x[k] === y[k]) k++; return k; }
  function sameEnd(x, y) {
    let k = 0;
    while (k < x.length && k < y.length && x[x.length - 1 - k] === y[y.length - 1 - k]) k++;
    return k;
  }

  function marksOf(id) { return document.querySelectorAll('mark.anot-hl[data-anot="' + id + '"]'); }

  function paint(m, a) {
    const [r, g, b] = COLORS[a.color] || COLORS.yellow;
    m.style.backgroundColor = `rgba(${r}, ${g}, ${b}, .42)`;
    m.classList.toggle('anot-note', !!a.note);
  }
  function repaint(a) { marksOf(a.id).forEach(m => paint(m, a)); }

  function wrap(a, map, start) {
    const end = start + a.exact.length;
    for (const e of map.nodes) {
      if (e.end <= start || e.start >= end) continue;
      let node = e.node;
      const s = Math.max(start, e.start) - e.start, t = Math.min(end, e.end) - e.start;
      if (!node.data.slice(s, t).trim()) continue;
      if (t < node.data.length) node.splitText(t);
      if (s > 0) node = node.splitText(s);
      const m = document.createElement('mark');
      m.className = 'anot-hl';
      m.dataset.anot = a.id;
      paint(m, a);
      node.parentNode.insertBefore(m, node);
      m.appendChild(node);
    }
  }

  function unwrap(id) {
    observer.disconnect();
    marksOf(id).forEach(m => {
      const p = m.parentNode;
      while (m.firstChild) p.insertBefore(m.firstChild, m);
      p.removeChild(m);
      p.normalize();
    });
    observe();
  }

  function renderAll() {
    observer.disconnect();
    let map = null;
    for (const a of notes) {
      if (marksOf(a.id).length) continue;
      map = map || textMap();
      const i = locate(a, map.text);
      if (i >= 0) { wrap(a, map, i); map = null; }
    }
    observe();
    refreshPanel();
  }
  function observe() { observer.observe(document.body, { childList: true, subtree: true, characterData: true }); }

  function create(color, withNote) {
    if (!pending) return;
    lastColor = color;
    const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    notes.push({ id, color, note: '', user: lastUser, created: new Date().toISOString(), ...pending });
    pending = null;
    getSelection().removeAllRanges();
    toolbar.hidden = true;
    renderAll();
    save();
    if (withNote) openPop(id);
  }

  async function remove(a) {
    if (a.note && !await ask('Delete this highlight and its note?', 'Delete', true)) return;
    notes = notes.filter(n => n !== a);
    unwrap(a.id);
    if (editing === a) closePop();
    save();
  }

  async function clearAll() {
    if (!notes.length) return;
    const what = notes.length === 1 ? 'the only annotation' : 'all ' + count(notes.length);
    if (!await ask('Delete ' + what + ' on this page?\nExport first if you want a copy.', 'Delete all', true)) return;
    notes.forEach(a => unwrap(a.id));
    notes = [];
    closePop();
    save();
  }

  function goTo(a) {
    const m = marksOf(a.id)[0];
    if (!m) return;
    if (innerWidth < 720) panel.hidden = true;
    m.scrollIntoView({ behavior: 'smooth', block: 'center' });
    marksOf(a.id).forEach(x => x.classList.add('anot-flash'));
    setTimeout(() => marksOf(a.id).forEach(x => x.classList.remove('anot-flash')), 1400);
  }

  function docInfo() {
    return { title: document.title, did: PARAMS.did || '', version: PARAMS.version || '', date: PARAMS.date || '',
             tnw: PARAMS.tnw || '' };
  }

  function mismatch(theirs) {
    if (!theirs) return [];
    const ours = docInfo();
    return [['did', 'DID'], ['version', 'Version'], ['date', 'Date']]
      .filter(([k]) => theirs[k] && ours[k] && theirs[k] !== ours[k])
      .map(([k, label]) => label + ': ' + theirs[k] + ' (file) / ' + ours[k] + ' (this page)');
  }

  function exportJSON() {
    const data = { page: location.pathname, document: docInfo(), exported: new Date().toISOString(), annotations: notes };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = decodeURIComponent(location.pathname.split('/').pop() || 'page').replace(/\.html?$/i, '') + '.annotations.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  async function importJSON(file) {
    let data, incoming;
    try {
      data = JSON.parse(await file.text());
      incoming = (Array.isArray(data) ? data : data.annotations || []).filter(a => a && a.id && a.exact);
    } catch (e) {
      tell('Could not read the file. Is it a .json exported by the annotator?');
      return;
    }
    const diff = mismatch(data.document);
    if (diff.length && !await ask('These annotations were made on another document or version:\n\n' + diff.join('\n') +
        '\n\nHighlights whose text has changed will show as "Not visible now".', 'Import anyway')) return;
    for (const a of incoming) {
      const i = notes.findIndex(n => n.id === a.id);
      if (i >= 0) { unwrap(a.id); notes[i] = a; } else notes.push(a);
    }
    save();
    renderAll();
    tell('Imported ' + count(incoming.length) + '.');
  }

  function count(n) { return n + (n === 1 ? ' annotation' : ' annotations'); }

  function dialog(text, ok, cancel, danger) {
    if (dlgDone) dlgDone(false);
    setTheme();
    dlgText.textContent = text;
    dlgOk.textContent = ok;
    dlgOk.classList.toggle('danger', !!danger);
    dlgCancel.hidden = !cancel;
    dlg.hidden = false;
    dlgOk.focus();
    return new Promise(resolve => {
      dlgDone = v => { dlg.hidden = true; dlgDone = null; resolve(v); };
    });
  }
  function ask(text, ok, danger) { return dialog(text, ok, true, danger); }
  function tell(text) { return dialog(text, 'OK', false, false); }

  const CSS = `
    :host { --bg:#fff; --ink:#1c2233; --muted:#5d667d; --line:#d8dde8; --accent:#2f5bd3; --danger:#c62f3e;
      --shadow:0 8px 28px rgba(0,0,0,.18); font:15px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; color:var(--ink) }
    :host(.dark) { --bg:#1d2438; --ink:#e8ecf6; --muted:#a3acc3; --line:#33405f; --accent:#8aa8ff; --danger:#ff8591;
      --shadow:0 8px 28px rgba(0,0,0,.55) }
    * { box-sizing:border-box; font:inherit; color:inherit }
    [hidden] { display:none !important }
    button { cursor:pointer; border:1px solid var(--line); background:var(--bg); border-radius:8px; padding:6px 10px }
    button:hover { border-color:var(--accent) }
    button:focus-visible, input:focus-visible, textarea:focus-visible { outline:2px solid var(--accent); outline-offset:2px }
    .toolbar, .pop { position:fixed; background:var(--bg); border:1px solid var(--line); border-radius:12px;
      box-shadow:var(--shadow); padding:6px; display:flex; gap:6px; align-items:center }
    .pop { flex-direction:column; align-items:stretch; width:min(320px, calc(100vw - 16px)); padding:10px; gap:8px }
    .dots { display:flex; gap:6px }
    .dot { width:28px; height:28px; border-radius:50%; padding:0; background:var(--c); border:2px solid transparent }
    .dot[aria-pressed="true"] { border-color:var(--ink) }
    input.user { width:100%; border:1px solid var(--line); border-radius:8px; padding:6px 8px; background:transparent }
    textarea { width:100%; min-height:90px; resize:vertical; border:1px solid var(--line); border-radius:8px;
      padding:8px; background:transparent }
    .row { display:flex; justify-content:space-between; gap:8px }
    .danger { color:var(--danger) }
    .clear { margin-left:auto }
    .fab { position:fixed; right:16px; bottom:16px; border-radius:999px; padding:10px 14px; box-shadow:var(--shadow); font-weight:600 }
    .panel { position:fixed; top:0; right:0; bottom:0; width:min(360px, 100vw); background:var(--bg);
      border-left:1px solid var(--line); box-shadow:var(--shadow); display:flex; flex-direction:column }
    .panel header { display:flex; align-items:center; gap:8px; padding:14px 16px; border-bottom:1px solid var(--line) }
    .panel header strong { flex:1; font-size:17px }
    .actions { display:flex; gap:8px; padding:10px 16px; border-bottom:1px solid var(--line) }
    .list { list-style:none; margin:0; padding:12px 16px 24px; overflow-y:auto; flex:1; display:grid; gap:10px; align-content:start }
    .item { border:1px solid var(--line); border-left:6px solid var(--c); border-radius:8px; padding:8px 10px; cursor:pointer }
    .item:hover { border-color:var(--accent); border-left-color:var(--c) }
    .quote { font-style:italic }
    .note { margin-top:6px; white-space:pre-wrap }
    .item .user { margin-top:6px; color:var(--muted); font-size:13px }
    .lost { color:var(--muted); font-size:13px; margin-top:6px; display:flex; justify-content:space-between; align-items:center; gap:8px }
    .empty { color:var(--muted); padding:16px; margin:0 }
    .dlg-back { position:fixed; inset:0; background:rgba(0,0,0,.25); display:flex; align-items:center; justify-content:center; padding:16px }
    .dlg { max-width:28rem; padding:.75rem .9rem; background:var(--tnw-popup-bg, var(--bg)); color:var(--tnw-fg, var(--ink));
      border:1px solid var(--tnw-border, var(--line)); border-radius:6px; box-shadow:0 6px 20px rgba(0,0,0,.18);
      font:.9rem/1.45 "Helvetica Neue", Helvetica, Arial, system-ui, sans-serif }
    .dlg p { margin:0; white-space:pre-line }
    .dlg-btns { display:flex; justify-content:flex-end; gap:.5rem; margin-top:.6rem }
    .dlg button { padding:.25rem .75rem; border-radius:4px; font-size:.85rem; background:transparent; border:1px solid var(--tnw-border, var(--line)) }
    .dlg button:hover { border-color:var(--tnw-accent, var(--accent)) }
    .dlg .dlg-ok { background:var(--tnw-accent, var(--accent)); color:var(--tnw-on-accent, #fff); border-color:transparent }
    .dlg .dlg-ok:hover { filter:brightness(1.1); border-color:transparent }
    .dlg .dlg-ok.danger { background:transparent; color:var(--danger); border-color:var(--tnw-border, var(--line)) }
    .dlg .dlg-ok.danger:hover { filter:none; border-color:var(--tnw-accent, var(--accent)) }
  `;

  function dots() {
    return Object.entries(COLORS).map(([name, [r, g, b]]) =>
      `<button class="dot" data-color="${name}" style="--c:rgb(${r},${g},${b})" title="${name}" aria-label="Highlight in ${name}"></button>`
    ).join('');
  }

  function buildUI() {
    const style = document.createElement('style');
    style.textContent = `
      mark.anot-hl { color:inherit; padding:0; border-radius:2px; cursor:pointer;
        -webkit-box-decoration-break:clone; box-decoration-break:clone }
      mark.anot-hl.anot-note { border-bottom:2px dotted currentColor }
      mark.anot-hl.anot-flash { outline:2px solid currentColor; outline-offset:1px }
      @media print { .anot-host { display:none !important } }`;
    document.head.appendChild(style);

    host = document.createElement('div');
    host.className = 'anot-host';
    host.style.cssText = 'position:fixed; top:0; left:0; width:0; height:0; z-index:2147483647';
    const ui = host.attachShadow({ mode: 'open' });
    ui.innerHTML = `<style>${CSS}</style>
      <div class="toolbar" hidden><div class="dots">${dots()}</div><button data-act="note">+ Note</button></div>
      <button class="fab" title="Show annotations">\u270e <span>0</span></button>
      <aside class="panel" hidden aria-label="Annotations">
        <header><strong>Annotations</strong><button data-act="close-panel" aria-label="Close">\u2715</button></header>
        <div class="actions">
          <button data-act="export">Export</button><button data-act="import">Import</button>
          <button data-act="clear" class="danger clear">Clear</button>
          <input type="file" accept=".json,application/json" hidden>
        </div>
        <ol class="list"></ol>
        <p class="empty">Select text on the page to highlight it.</p>
      </aside>
      <div class="pop" hidden role="dialog" aria-label="Edit annotation">
        <div class="dots">${dots()}</div>
        <input class="user" type="text" placeholder="User (optional)" aria-label="User">
        <textarea placeholder="Write a note (optional)\u2026"></textarea>
        <div class="row"><button data-act="delete" class="danger">Delete</button><button data-act="done">Done</button></div>
      </div>
      <div class="dlg-back" hidden>
        <div class="dlg" role="alertdialog" aria-modal="true">
          <p></p>
          <div class="dlg-btns"><button data-act="cancel">Cancel</button><button data-act="ok" class="dlg-ok">OK</button></div>
        </div>
      </div>`;
    document.body.appendChild(host);

    toolbar = ui.querySelector('.toolbar');
    pop = ui.querySelector('.pop');
    dlg = ui.querySelector('.dlg-back');
    dlgText = dlg.querySelector('p');
    dlgOk = dlg.querySelector('[data-act=ok]');
    dlgCancel = dlg.querySelector('[data-act=cancel]');
    who = pop.querySelector('input.user');
    ta = pop.querySelector('textarea');
    panel = ui.querySelector('.panel');
    list = ui.querySelector('.list');
    empty = ui.querySelector('.empty');
    fab = ui.querySelector('.fab');
    fileInput = ui.querySelector('input[type=file]');

    toolbar.addEventListener('pointerdown', e => e.preventDefault());
    toolbar.addEventListener('mousedown', e => e.preventDefault());
    toolbar.addEventListener('click', e => {
      const b = e.target.closest('button');
      if (!b) return;
      if (b.dataset.color) create(b.dataset.color, false);
      else if (b.dataset.act === 'note') create(lastColor, true);
    });

    pop.addEventListener('click', e => {
      const b = e.target.closest('button');
      if (!b || !editing) return;
      if (b.dataset.color) { editing.color = lastColor = b.dataset.color; repaint(editing); markColor(); save(); }
      else if (b.dataset.act === 'delete') remove(editing);
      else if (b.dataset.act === 'done') closePop();
    });
    who.addEventListener('input', () => { if (editing) { editing.user = who.value.trim(); saveUser(editing.user); save(); } });
    ta.addEventListener('input', () => { if (editing) { editing.note = ta.value; repaint(editing); save(); } });

    fab.addEventListener('click', () => { panel.hidden = !panel.hidden; setTheme(); refreshPanel(); });
    panel.addEventListener('click', e => {
      const act = e.target.closest('button') && e.target.closest('button').dataset.act;
      if (act === 'close-panel') panel.hidden = true;
      else if (act === 'export') exportJSON();
      else if (act === 'import') fileInput.click();
      else if (act === 'clear') clearAll();
    });
    fileInput.addEventListener('change', () => { if (fileInput.files[0]) importJSON(fileInput.files[0]); fileInput.value = ''; });

    dlg.addEventListener('click', e => {
      const b = e.target.closest('button');
      if (b) dlgDone(b.dataset.act === 'ok');
      else if (e.target === dlg) dlgDone(false);
    });
    dlg.addEventListener('keydown', e => {
      if (e.key !== 'Escape') return;
      e.stopPropagation();
      dlgDone(false);
    });
  }

  function setTheme() {
    const t = document.documentElement.dataset.theme;
    const dark = t ? t === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    host.classList.toggle('dark', dark);
  }

  function place(el, rect) {
    el.hidden = false;
    const w = el.offsetWidth, h = el.offsetHeight;
    let top = rect.top - h - 8;
    if (top < 8) top = rect.bottom + 8;
    top = Math.max(8, Math.min(top, innerHeight - h - 8));
    const left = Math.max(8, Math.min(rect.left + rect.width / 2 - w / 2, innerWidth - w - 8));
    el.style.top = top + 'px';
    el.style.left = left + 'px';
  }

  function markColor() {
    pop.querySelectorAll('.dot').forEach(d => d.setAttribute('aria-pressed', String(d.dataset.color === editing.color)));
  }

  function openPop(id) {
    const a = notes.find(n => n.id === id);
    if (!a) return;
    editing = a;
    toolbar.hidden = true;
    setTheme();
    markColor();
    who.value = a.user || '';
    ta.value = a.note || '';
    const m = marksOf(id)[0];
    const c = { top: innerHeight / 2, bottom: innerHeight / 2, left: innerWidth / 2, width: 0 };
    place(pop, m ? m.getBoundingClientRect() : c);
    ta.focus({ preventScroll: true });
  }
  function closePop() { pop.hidden = true; editing = null; }

  function checkSelection() {
    const sel = getSelection();
    if (!sel.rangeCount || sel.isCollapsed) { toolbar.hidden = true; pending = null; return; }
    const range = sel.getRangeAt(0);
    if (!document.body.contains(range.commonAncestorContainer)) return;
    pending = describe(range);
    if (!pending) { toolbar.hidden = true; return; }
    setTheme();
    place(toolbar, range.getBoundingClientRect());
  }
  function scheduleCheck() { clearTimeout(selTimer); selTimer = setTimeout(checkSelection, 150); }

  function refreshPanel() {
    fab.querySelector('span').textContent = notes.length;
    if (panel.hidden) return;
    empty.hidden = notes.length > 0;
    list.textContent = '';
    const rows = notes.map(a => ({ a, m: marksOf(a.id)[0] }));
    rows.sort((x, y) => {
      if (!x.m || !y.m) return (x.m ? 0 : 1) - (y.m ? 0 : 1);
      return x.m.compareDocumentPosition(y.m) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
    });
    for (const { a, m } of rows) {
      const [r, g, b] = COLORS[a.color] || COLORS.yellow;
      const li = document.createElement('li');
      li.className = 'item';
      li.style.setProperty('--c', `rgb(${r},${g},${b})`);
      const q = document.createElement('div');
      q.className = 'quote';
      const t = a.exact.replace(/\s+/g, ' ').trim();
      q.textContent = '\u00ab' + (t.length > 160 ? t.slice(0, 157) + '\u2026' : t) + '\u00bb';
      li.appendChild(q);
      if (a.note) {
        const n = document.createElement('div');
        n.className = 'note';
        n.textContent = a.note;
        li.appendChild(n);
      }
      if (a.user) {
        const u = document.createElement('div');
        u.className = 'user';
        u.textContent = '\u2014 ' + a.user;
        li.appendChild(u);
      }
      if (m) li.addEventListener('click', () => goTo(a));
      else {
        const lost = document.createElement('div');
        lost.className = 'lost';
        lost.innerHTML = '<span>Not visible now (maybe in another section of the page).</span>';
        const del = document.createElement('button');
        del.className = 'danger';
        del.textContent = 'Delete';
        del.addEventListener('click', () => remove(a));
        lost.appendChild(del);
        li.appendChild(lost);
      }
      list.appendChild(li);
    }
  }

  function init() {
    buildUI();
    document.addEventListener('pointerdown', e => { if (e.target !== host) pointerDown = true; });
    document.addEventListener('pointerup', () => { pointerDown = false; scheduleCheck(); });
    document.addEventListener('pointercancel', () => { pointerDown = false; scheduleCheck(); });
    document.addEventListener('selectionchange', () => { if (!pointerDown) scheduleCheck(); });
    addEventListener('scroll', () => { toolbar.hidden = true; }, { passive: true });
    document.addEventListener('click', e => {
      if (e.target === host) return;
      const m = e.target.closest && e.target.closest('mark.anot-hl');
      if (m && getSelection().isCollapsed) openPop(m.dataset.anot);
      else if (!pop.hidden) closePop();
    });
    document.addEventListener('keydown', e => {
      if (e.key !== 'Escape') return;
      if (!pop.hidden) closePop();
      else if (!toolbar.hidden) toolbar.hidden = true;
      else panel.hidden = true;
    });
    renderAll();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
