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
  // text, country, and renewal dates from / until (ISO, so they compare as text) — hide the bundles that
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
      f.addEventListener(f.getAttribute("data-f") === "text" ? "input" : "change", apply);
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
  // Edit mode's bar: "N selected"; its actions only once something is
  // ticked; the bulk proposal's premium rows only for the ticked renewals.
  document.querySelectorAll("[data-move-form]").forEach(function (f) {
    var count = f.querySelector("[data-pick-count]"), submits = f.querySelectorAll("[data-pick-submit]");
    if (!count || !f.id) return;
    var boxes = document.querySelectorAll('input[type=checkbox][form="' + f.id + '"]');
    var empty = count.getAttribute("data-pick-empty") || "Tick the renewals to move.";
    function sync() {
      var picked = Array.prototype.filter.call(boxes, function (b) { return b.checked; });
      var ids = picked.map(function (b) { return b.value; });
      count.textContent = picked.length ? picked.length + " selected" : empty;
      submits.forEach(function (s) { s.disabled = picked.length === 0; });
      f.querySelectorAll("[data-bulk-row]").forEach(function (row) {
        row.hidden = ids.indexOf(row.getAttribute("data-bulk-row")) < 0;
      });
    }
    boxes.forEach(function (b) { b.addEventListener("change", sync); });
    f.querySelectorAll("[data-check-all]").forEach(function (b) { b.addEventListener("click", sync); });
    sync();
  });
  // [data-move-form]: the bundle name is only asked for a new bundle.
  document.querySelectorAll("[data-move-form]").forEach(function (f) {
    var target = f.querySelector("[data-move-target]"), name = f.querySelector("[data-move-name]");
    if (!target || !name) return;
    // in the edit bar the form also carries other actions: never make them wait for a name
    var bulk = f.hasAttribute("data-bulk-form");
    function sync() { var isNew = target.value === "new"; name.hidden = !isNew; name.required = isNew && !bulk; }
    target.addEventListener("change", sync);
    sync();
  });
  // <form data-dropzone>: tracker files dropped on its [data-drop-area] go into
  // its file input and the form is sent (the preview comes next; nothing is
  // committed). Only .xlsx files are taken. A file dropped elsewhere on the
  // page is ignored instead of the browser opening it.
  document.querySelectorAll("form[data-dropzone]").forEach(function (form) {
    var area = form.querySelector("[data-drop-area]"), input = form.querySelector("input[type=file]");
    var status = form.querySelector("[data-drop-status]");
    if (!area || !input) return;
    function say(text, isError) {
      if (!status) return;
      status.hidden = false;
      status.textContent = text;
      status.classList.toggle("is-error", !!isError);
    }
    ["dragenter", "dragover"].forEach(function (t) {
      area.addEventListener(t, function (e) { e.preventDefault(); area.classList.add("is-over"); });
    });
    area.addEventListener("dragleave", function (e) {
      if (!area.contains(e.relatedTarget)) area.classList.remove("is-over");
    });
    area.addEventListener("drop", function (e) {
      e.preventDefault();
      e.stopPropagation();
      area.classList.remove("is-over");
      var files = Array.prototype.filter.call(e.dataTransfer.files || [], function (f) {
        return /\.xlsx$/i.test(f.name);
      });
      if (!files.length) { say("Only .xlsx tracker exports can be uploaded.", true); return; }
      try {
        var dt = new DataTransfer();
        files.forEach(function (f) { dt.items.add(f); });
        input.files = dt.files;
      } catch (err) { say("This browser can't take dropped files: please choose them.", true); return; }
      say("Uploading " + files.length + " file" + (files.length === 1 ? "" : "s") + "…");
      form.submit();
    });
    ["dragover", "drop"].forEach(function (t) {
      document.addEventListener(t, function (e) { e.preventDefault(); });
    });
  });
  // <select data-autosubmit>: choosing sends its form (the Insurers filters).
  document.querySelectorAll("select[data-autosubmit]").forEach(function (sel) {
    sel.addEventListener("change", function () { if (sel.form) sel.form.submit(); });
  });

  // <select data-shows="#id" data-shows-value="v">: #id is shown only while v is chosen.
  document.querySelectorAll("select[data-shows]").forEach(function (sel) {
    var target = document.querySelector(sel.getAttribute("data-shows"));
    if (!target) return;
    function sync() { target.hidden = sel.value !== sel.getAttribute("data-shows-value"); }
    sel.addEventListener("change", sync);
    sync();
  });
  // [data-focus-on-open] in a <details>: put the cursor there when it opens.
  document.querySelectorAll("details").forEach(function (d) {
    var field = d.querySelector("[data-focus-on-open]");
    if (!field) return;
    d.addEventListener("toggle", function () { if (d.open) field.focus(); });
  });
})();
