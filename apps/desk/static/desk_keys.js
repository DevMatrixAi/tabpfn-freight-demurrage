/* Desk keyboard shortcuts — ignore when typing in form fields. Esc closes drawer (see polish_drawer). */
(function () {
  var SHORTCUTS = [
    { key: "t", label: "Triage", detail: "Jump to Run triage panel" },
    { key: "e", label: "Eval", detail: "Open /eval compare dashboard" },
    { key: "/", label: "Search", detail: "Focus board filter / search" },
    { key: "?", label: "Help", detail: "Open this cheat sheet" },
    { key: "Esc", label: "Close", detail: "Close action drawer / cheat sheet" }
  ];

  function typingTarget(el) {
    if (!el) return false;
    var tag = (el.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "select") return true;
    if (el.isContentEditable) return true;
    return false;
  }

  function ensureCheatSheet() {
    var existing = document.getElementById("desk-keys-cheatsheet");
    if (existing) return existing;
    var modal = document.createElement("div");
    modal.id = "desk-keys-cheatsheet";
    modal.className = "desk-keys-modal";
    modal.setAttribute("data-desk-keys-cheatsheet", "1");
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-label", "Keyboard shortcuts");
    modal.hidden = true;
    var rows = SHORTCUTS.map(function (s) {
      return "<tr><th><kbd>" + s.key + "</kbd></th><td><strong>" + s.label + "</strong> — " + s.detail + "</td></tr>";
    }).join("");
    modal.innerHTML =
      '<div class="desk-keys-card">' +
      "<h3>Keyboard shortcuts</h3>" +
      '<p class="muted">Ignored while typing in inputs. Press <kbd>?</kbd> anytime.</p>' +
      "<table><tbody>" + rows + "</tbody></table>" +
      '<button type="button" class="desk-keys-close" data-desk-keys-close="1">Close (Esc)</button>' +
      "</div>";
    modal.addEventListener("click", function (ev) {
      if (ev.target === modal || (ev.target && ev.target.getAttribute("data-desk-keys-close"))) {
        closeCheatSheet();
      }
    });
    document.body.appendChild(modal);
    return modal;
  }

  function openCheatSheet() {
    var m = ensureCheatSheet();
    m.hidden = false;
    m.classList.add("open");
  }

  function closeCheatSheet() {
    var m = document.getElementById("desk-keys-cheatsheet");
    if (!m) return;
    m.hidden = true;
    m.classList.remove("open");
  }

  function focusFilter() {
    var el =
      document.getElementById("board-filter") ||
      document.getElementById("desk-search") ||
      document.querySelector("[data-desk-filter]") ||
      document.querySelector('input[type="search"]');
    if (el) {
      el.focus();
      if (typeof el.select === "function") el.select();
      return true;
    }
    return false;
  }

  function goTriage() {
    var panel = document.getElementById("triage-panel") || document.getElementById("run-triage-btn");
    if (panel && panel.scrollIntoView) panel.scrollIntoView({ behavior: "smooth", block: "start" });
    var btn = document.getElementById("run-triage-btn");
    if (btn && btn.focus) btn.focus();
    if (!panel && !btn) window.location.href = "/desk#triage-panel";
  }

  function goEval() {
    var link = document.getElementById("eval-link") || document.querySelector('a[href="/eval"]');
    if (link && link.href) {
      window.location.href = link.href;
      return;
    }
    window.location.href = "/eval";
  }

  document.addEventListener("keydown", function (e) {
    if (typingTarget(e.target)) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;

    if (e.key === "Escape") {
      var sheet = document.getElementById("desk-keys-cheatsheet");
      if (sheet && !sheet.hidden) {
        e.preventDefault();
        closeCheatSheet();
      }
      return; /* drawer Esc handled in polish_drawer.html */
    }

    if (e.key === "?" || (e.key === "/" && e.shiftKey)) {
      e.preventDefault();
      openCheatSheet();
      return;
    }
    if (e.key === "/" && !e.shiftKey) {
      e.preventDefault();
      if (!focusFilter()) openCheatSheet();
      return;
    }
    if (e.key === "t" || e.key === "T") {
      e.preventDefault();
      goTriage();
      return;
    }
    if (e.key === "e" || e.key === "E") {
      e.preventDefault();
      goEval();
      return;
    }
  });

  /* expose for tests / console */
  window.__deskKeys = {
    shortcuts: SHORTCUTS,
    openCheatSheet: openCheatSheet,
    closeCheatSheet: closeCheatSheet,
    focusFilter: focusFilter
  };

  function wireBoardFilter() {
    var input = document.getElementById("board-filter");
    if (!input || input.getAttribute("data-filter-wired")) return;
    input.setAttribute("data-filter-wired", "1");
    input.addEventListener("input", function () {
      var q = (input.value || "").toLowerCase().trim();
      var cards = document.querySelectorAll("#risk-board .risk-card");
      cards.forEach(function (card) {
        var hay = (
          (card.getAttribute("data-row-id") || "") + " " +
          (card.getAttribute("data-action") || "") + " " +
          (card.getAttribute("data-action-label") || "") + " " +
          (card.getAttribute("data-tier") || "") + " " +
          (card.getAttribute("data-subtitle") || "") + " " +
          (card.textContent || "")
        ).toLowerCase();
        card.style.display = !q || hay.indexOf(q) !== -1 ? "" : "none";
      });
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wireBoardFilter);
  else wireBoardFilter();

})();
