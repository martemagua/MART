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

  // <input data-filter-items="#list">: hide [data-filter-item] elements that don't
  // contain the text, and [data-filter-group] blocks left without a visible item.
  document.querySelectorAll("[data-filter-items]").forEach(function (input) {
    var list = document.querySelector(input.getAttribute("data-filter-items"));
    if (!list) return;
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      list.querySelectorAll("[data-filter-item]").forEach(function (el) {
        el.hidden = q !== "" && el.textContent.toLowerCase().indexOf(q) === -1;
      });
      list.querySelectorAll("[data-filter-group]").forEach(function (g) {
        g.hidden = !g.querySelector("[data-filter-item]:not([hidden])");
      });
    });
  });

  // [data-keep-scroll="name"]: remember the scroll position of a side panel
  // across page loads (clicking a bundle reloads the page). Per browser tab only.
  document.querySelectorAll("[data-keep-scroll]").forEach(function (el) {
    var key = "mart-scroll-" + el.getAttribute("data-keep-scroll");
    try {
      var y = sessionStorage.getItem(key);
      if (y !== null) el.scrollTop = parseInt(y, 10);
      el.addEventListener("scroll", function () { sessionStorage.setItem(key, String(el.scrollTop)); });
    } catch (e) { /* storage blocked: nothing to remember */ }
    var sel = el.querySelector(".is-selected");
    if (sel) {
      var r = sel.getBoundingClientRect(), box = el.getBoundingClientRect();
      if (r.top < box.top || r.bottom > box.bottom) sel.scrollIntoView({ block: "center" });
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
})();
