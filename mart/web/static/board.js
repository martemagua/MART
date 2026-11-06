// MART — the board's drag and drop and its pop-up (board.html). Plain
// JavaScript, no libraries. Dropping a card ([data-card]) on another column ([data-col-drop])
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
      var hint = col.querySelector(".board-col-hint");
      dialog.querySelector("[data-move-hint]").textContent = hint ? hint.textContent : "";
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

  // -- the pop-up: a card opens its bundle over the board -------------------------
  // A click on a card (not on its ⇄ menu; Ctrl/⌘-click still opens a new tab)
  // shows the bundle page in a frame. A click outside, × or Esc shrinks it back
  // into its card; if anything was sent from inside, the board is refreshed
  // first, so the card already shows the change (and its new column).
  var pop = document.querySelector("#board-pop");
  var frame = pop && pop.querySelector("[data-pop-iframe]");
  if (!pop || !frame) return;
  var openKey = null, changed = false, closing = false;
  var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function cardOf(key) {
    var found = null;
    board.querySelectorAll("[data-card]").forEach(function (c) {
      if (c.getAttribute("data-key") === key) found = c;
    });
    return found && !found.hidden ? found : null;
  }
  // from the card's box to the pop-up's (and back, with `back`)
  function zoom(card, back) {
    var box = pop.querySelector(".board-pop-frame");
    if (still || !card || !box.animate) return Promise.resolve();
    var a = card.getBoundingClientRect(), b = box.getBoundingClientRect();
    var shrunk = "translate(" + (a.left - b.left) + "px," + (a.top - b.top) + "px) scale(" +
      (a.width / b.width) + "," + (a.height / b.height) + ")";
    var frames = [{ transform: shrunk, opacity: 0.4 }, { transform: "none", opacity: 1 }];
    var anim = box.animate(back ? frames.reverse() : frames,
                           { duration: 200, easing: "ease-out", fill: back ? "forwards" : "none" });
    return anim.finished.then(function () { if (back) anim.cancel(); }, function () {});
  }
  function refresh() {
    return fetch(location.pathname, { credentials: "same-origin" }).then(function (res) {
      return res.ok ? res.text() : Promise.reject(res.status);
    }).then(function (html) {
      var fresh = new DOMParser().parseFromString(html, "text/html");
      board.querySelectorAll("[data-col-drop]").forEach(function (col) {
        var other = fresh.querySelector('[data-col-drop="' + col.getAttribute("data-col-drop") + '"] [data-col-cards]');
        if (other) col.querySelector("[data-col-cards]").innerHTML = other.innerHTML;
      });
      var sum = document.querySelector("[data-board-summary]"), sum2 = fresh.querySelector("[data-board-summary]");
      if (sum && sum2) sum.innerHTML = sum2.innerHTML;
      // the filters again (they also recount the columns)
      var text = document.querySelector('[data-bundle-filters] [data-f="text"]');
      if (text) text.dispatchEvent(new Event("input"));
      counts();
    });
  }
  function openCard(card, href) {
    openKey = card.getAttribute("data-key");
    changed = false;
    pop.querySelector("[data-pop-title]").textContent = card.getAttribute("data-name");
    pop.querySelector("[data-pop-full]").href = href;
    frame.src = href;
    pop.showModal();
    zoom(card, false);
  }
  function closeCard() {
    if (closing || !pop.open) return;
    closing = true;
    var after = changed ? refresh().catch(function () { location.reload(); }) : Promise.resolve();
    after.then(function () { return zoom(cardOf(openKey), true); }).then(function () {
      pop.close();
      frame.src = "about:blank";
      closing = false;
    });
  }

  board.addEventListener("click", function (e) {
    if (e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    var card = e.target.closest ? e.target.closest("[data-card]") : null;
    if (!card || e.target.closest("details, form")) return;
    var link = card.querySelector(".bc-name");
    if (!link) return;
    e.preventDefault();
    openCard(card, link.href);
  });
  // a click on the dimmed board around it (the dialog itself, not its frame)
  pop.addEventListener("click", function (e) { if (e.target === pop) closeCard(); });
  pop.addEventListener("cancel", function (e) { e.preventDefault(); closeCard(); });
  pop.querySelector("[data-pop-close]").addEventListener("click", closeCard);
  // "Open the full page" follows the page shown inside (a renewal, edit mode…)
  frame.addEventListener("load", function () {
    try {
      var here = frame.contentWindow.location;
      if (here.protocol !== "about:") pop.querySelector("[data-pop-full]").href = here.pathname + here.search;
    } catch (err) { /* not ours */ }
  });
  // from the page inside (mart.js): something was sent / Esc or "Board" there
  document.addEventListener("mart-pop-changed", function () { changed = true; });
  document.addEventListener("mart-pop-close", closeCard);
})();
