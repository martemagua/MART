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
})();
