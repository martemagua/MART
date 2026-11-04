// MART — small page helpers. Plain JavaScript, no libraries, no network.
// Everything here only makes a page quicker to use; every page works without it.
(function () {
  "use strict";

  // <input data-filter-rows="#tbody-id">: hide table rows that don't contain the text.
  document.querySelectorAll("[data-filter-rows]").forEach(function (input) {
    var body = document.querySelector(input.getAttribute("data-filter-rows"));
    if (!body) return;
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      body.querySelectorAll("tr").forEach(function (tr) {
        tr.hidden = q !== "" && tr.textContent.toLowerCase().indexOf(q) === -1;
      });
    });
    // Enter in the filter must not submit the surrounding form.
    input.addEventListener("keydown", function (e) { if (e.key === "Enter") e.preventDefault(); });
  });

  // [data-bundle-filters="<client id>"]: the explorer's side panel filters —
  // text, country, and renewal months from / until — hide the bundles that
  // don't match, and the groups left empty. They are remembered per client
  // in this browser tab (clicking a bundle reloads the page); [data-fresh]
  // (the client opened from the list) starts without them.
  document.querySelectorAll("[data-bundle-filters]").forEach(function (box) {
    var list = document.querySelector(box.getAttribute("data-list"));
    if (!list) return;
    var key = "mart-filters-" + box.getAttribute("data-bundle-filters");
    var fields = box.querySelectorAll("[data-f]");
    var summary = box.querySelector("[data-f-summary]"), count = box.querySelector("[data-f-count]");
    function val(name) {
      var el = box.querySelector('[data-f="' + name + '"]');
      return el ? el.value.trim() : "";
    }
    function apply() {
      var q = val("text").toLowerCase(), country = val("country"), from = val("from"), until = val("until");
      var shown = 0, total = 0, saved = {};
      list.querySelectorAll("[data-filter-item]").forEach(function (el) {
        var first = el.getAttribute("data-first"), last = el.getAttribute("data-last");
        var ok = (!q || el.textContent.toLowerCase().indexOf(q) !== -1)
          && (!country || el.getAttribute("data-country") === country)
          && (!from || (last !== "" && last >= from))
          && (!until || (first !== "" && first <= until));
        el.hidden = !ok;
        total += 1;
        if (ok) shown += 1;
      });
      list.querySelectorAll("[data-filter-group]").forEach(function (g) {
        g.hidden = !g.querySelector("[data-filter-item]:not([hidden])");
      });
      fields.forEach(function (f) { saved[f.getAttribute("data-f")] = f.value; });
      if (summary) {
        summary.hidden = !(q || country || from || until);
        count.textContent = shown + " of " + total + " bundle" + (total === 1 ? "" : "s");
      }
      try { sessionStorage.setItem(key, JSON.stringify(saved)); } catch (e) { /* not remembered */ }
    }
    try {
      if (box.hasAttribute("data-fresh")) sessionStorage.removeItem(key);
      var saved = JSON.parse(sessionStorage.getItem(key) || "{}");
      fields.forEach(function (f) {
        var v = saved[f.getAttribute("data-f")];
        if (v && (f.tagName !== "SELECT" || f.querySelector('option[value="' + CSS.escape(v) + '"]'))) f.value = v;
      });
    } catch (e) { /* storage blocked: start without filters */ }
    fields.forEach(function (f) {
      f.addEventListener(f.tagName === "SELECT" ? "change" : "input", apply);
      // Enter in the text filter must not submit anything.
      f.addEventListener("keydown", function (e) { if (e.key === "Enter") e.preventDefault(); });
    });
    var clear = box.querySelector("[data-f-clear]");
    if (clear) clear.addEventListener("click", function () {
      fields.forEach(function (f) { f.value = ""; });
      apply();
    });
    apply();
  });

  // [data-keep-scroll="name"]: remember the scroll position of a side panel
  // across page loads (clicking a bundle reloads the page). Per browser tab
  // only; [data-fresh] starts at the top. Only the PANEL scrolls to bring the
  // selected item into view, never the page.
  document.querySelectorAll("[data-keep-scroll]").forEach(function (el) {
    var key = "mart-scroll-" + el.getAttribute("data-keep-scroll");
    var fresh = el.hasAttribute("data-fresh");
    try {
      if (fresh) sessionStorage.removeItem(key);
      var y = sessionStorage.getItem(key);
      if (y !== null) el.scrollTop = parseInt(y, 10);
      el.addEventListener("scroll", function () { sessionStorage.setItem(key, String(el.scrollTop)); });
    } catch (e) { /* storage blocked: nothing to remember */ }
    var sel = el.querySelector(".is-selected");
    if (sel && !fresh && !sel.hidden) {
      var r = sel.getBoundingClientRect(), box = el.getBoundingClientRect();
      if (r.top < box.top || r.bottom > box.bottom) el.scrollTop += r.top - box.top - (box.height - r.height) / 2;
    }
  });

  // <button data-check-all="name" data-value="on|off">: tick / untick the visible boxes.
  document.querySelectorAll("[data-check-all]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var name = btn.getAttribute("data-check-all");
      var on = btn.getAttribute("data-value") === "on";
      document.querySelectorAll('input[type=checkbox][name="' + name + '"]').forEach(function (box) {
        var row = box.closest("tr");
        if (!row || !row.hidden) box.checked = on;
      });
    });
  });
  // <details class="menu"> / class="arrange": one open at a time; an outside
  // click or Esc closes it.
  function closeMenus(except) {
    document.querySelectorAll("details.menu[open], details.arrange[open]").forEach(function (m) {
      if (m !== except) m.removeAttribute("open");
    });
  }
  document.addEventListener("click", function (e) {
    closeMenus(e.target.closest ? e.target.closest("details.menu, details.arrange") : null);
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeMenus(null); });
  // <form data-confirm="Question?">: ask before submitting (deletes).
  document.querySelectorAll("form[data-confirm]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      if (!window.confirm(f.getAttribute("data-confirm"))) e.preventDefault();
    });
  });
  // [data-move-form]: the bundle name is only asked for a new bundle.
  document.querySelectorAll("[data-move-form]").forEach(function (f) {
    var target = f.querySelector("[data-move-target]"), name = f.querySelector("[data-move-name]");
    if (!target || !name) return;
    function sync() { var isNew = target.value === "new"; name.hidden = !isNew; name.required = isNew; }
    target.addEventListener("change", sync);
    sync();
  });
  // [data-focus-on-open] in a <details>: put the cursor there when it opens.
  document.querySelectorAll("details").forEach(function (d) {
    var field = d.querySelector("[data-focus-on-open]");
    if (!field) return;
    d.addEventListener("toggle", function () { if (d.open) field.focus(); });
  });
})();
