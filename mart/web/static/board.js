// MART — the board's drag and drop (board.html). Plain JavaScript, no
// libraries. Dropping a card ([data-card]) on another column ([data-col-drop])
// moves it there at once and opens the dialog for an optional reason; Move
// sends it, Cancel or Esc puts the card back. Without this script every card
// still moves with its "⇄" menu.
(function () {
  "use strict";
  var board = document.querySelector("[data-board]");
  var dialog = board && document.querySelector(board.getAttribute("data-dialog"));
  if (!board || !dialog || typeof dialog.showModal !== "function") return;
  var form = dialog.querySelector("form");
  var dragged = null, origin = null, next = null, sent = false;

  function field(name) { return form.querySelector('[name="' + name + '"]'); }
  function counts() {
    board.querySelectorAll("[data-filter-col]").forEach(function (col) {
      var n = col.querySelector("[data-filter-count]");
      if (n) n.textContent = col.querySelectorAll("[data-filter-item]:not([hidden])").length;
    });
  }
  function putBack() {
    if (dragged && origin) origin.insertBefore(dragged, next);
    dragged = null;
    counts();
  }

  board.addEventListener("dragstart", function (e) {
    var card = e.target.closest ? e.target.closest("[data-card]") : null;
    if (!card) return;
    dragged = card;
    origin = card.parentNode;
    next = card.nextSibling;
    e.dataTransfer.effectAllowed = "move";
    try { e.dataTransfer.setData("text/plain", card.getAttribute("data-name")); } catch (err) { /* ignore */ }
    card.classList.add("is-dragging");
  });
  board.addEventListener("dragend", function () {
    board.querySelectorAll(".is-dragging, .is-over").forEach(function (el) {
      el.classList.remove("is-dragging", "is-over");
    });
  });
  board.querySelectorAll("[data-col-drop]").forEach(function (col) {
    var list = col.querySelector("[data-col-cards]");
    col.addEventListener("dragover", function (e) {
      if (!dragged) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      col.classList.add("is-over");
    });
    col.addEventListener("dragleave", function (e) {
      if (!col.contains(e.relatedTarget)) col.classList.remove("is-over");
    });
    col.addEventListener("drop", function (e) {
      if (!dragged) return;
      e.preventDefault();
      col.classList.remove("is-over");
      var stage = col.getAttribute("data-col-drop");
      if (stage === dragged.getAttribute("data-col")) { dragged = null; return; }
      list.insertBefore(dragged, list.firstChild);
      counts();
      field("key").value = dragged.getAttribute("data-key");
      field("stage").value = stage;
      field("reason").value = "";
      dialog.querySelector("[data-move-what]").textContent = dragged.getAttribute("data-name");
      dialog.querySelector("[data-move-to]").textContent = col.querySelector(".board-col-title").firstChild.textContent.trim();
      var open = parseInt(dragged.getAttribute("data-open") || "0", 10);
      var box = dialog.querySelector("[data-move-complete]");
      box.hidden = !(stage === "done" && open > 0);
      field("complete").checked = false;
      dialog.querySelector("[data-move-open]").textContent = String(open);
      dialog.querySelector("[data-move-bm]").hidden = stage !== dragged.getAttribute("data-bm");
      sent = false;
      dialog.showModal();
      field("reason").focus();
    });
  });
  form.addEventListener("submit", function () { sent = true; });
  dialog.querySelector("[data-move-cancel]").addEventListener("click", function () { dialog.close(); });
  dialog.addEventListener("close", function () { if (!sent) putBack(); });
})();
