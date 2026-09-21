/* Desk toasts — bottom-right, auto-dismiss ~4s, aria-live. Mock-safe. */
(function () {
  var DISMISS_MS = 4000;
  var MAX = 4;

  function ensureRoot() {
    var root = document.getElementById("desk-toasts");
    if (root) return root;
    root = document.createElement("div");
    root.id = "desk-toasts";
    root.className = "desk-toasts";
    root.setAttribute("data-desk-toasts", "1");
    root.setAttribute("aria-live", "polite");
    root.setAttribute("aria-relevant", "additions");
    document.body.appendChild(root);
    return root;
  }

  function deskToast(msg, kind) {
    kind = kind || "error";
    var root = ensureRoot();
    while (root.children.length >= MAX) {
      root.removeChild(root.firstChild);
    }
    var el = document.createElement("div");
    el.className = "desk-toast desk-toast-" + kind;
    el.setAttribute("role", kind === "error" ? "alert" : "status");
    el.setAttribute("data-toast-kind", kind);
    var text = document.createElement("span");
    text.className = "desk-toast-msg";
    text.textContent = String(msg || "Something went wrong");
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "desk-toast-close";
    btn.setAttribute("aria-label", "Dismiss");
    btn.textContent = "×";
    btn.addEventListener("click", function () {
      if (el.parentNode) el.parentNode.removeChild(el);
    });
    el.appendChild(text);
    el.appendChild(btn);
    root.appendChild(el);
    window.setTimeout(function () {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, DISMISS_MS);
    return el;
  }

  window.deskToast = deskToast;

  function showSkeleton(sel) {
    var nodes = typeof sel === "string" ? document.querySelectorAll(sel) : [sel];
    Array.prototype.forEach.call(nodes, function (n) {
      if (!n) return;
      n.hidden = false;
      n.setAttribute("aria-busy", "true");
      n.classList.add("is-loading");
    });
  }

  function hideSkeleton(sel) {
    var nodes = typeof sel === "string" ? document.querySelectorAll(sel) : [sel];
    Array.prototype.forEach.call(nodes, function (n) {
      if (!n) return;
      n.hidden = true;
      n.removeAttribute("aria-busy");
      n.classList.remove("is-loading");
    });
  }

  window.deskShowSkeleton = showSkeleton;
  window.deskHideSkeleton = hideSkeleton;

  function wireFormSkeleton(formSel, skeletonSel, busyLabel) {
    var form = document.querySelector(formSel);
    if (!form) return;
    form.addEventListener("submit", function () {
      showSkeleton(skeletonSel);
      var btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.classList.add("btn-busy");
        if (busyLabel) btn.textContent = busyLabel;
      }
    });
  }

  function boot() {
    // Triage board → risk cards / charts skeleton
    wireFormSkeleton('form[action="/run-triage"]', "[data-skeleton=\"triage-board\"]", "Running triage…");
    // Eval prerun → running
    wireFormSkeleton('form[action="/eval/run"]', "[data-skeleton=\"eval-running\"]", "Running eval…");
    // Drawer apply action
    document.querySelectorAll('form[action="/apply-action"], form[data-apply-action], button[data-apply-action]').forEach(function (el) {
      var handler = function () {
        showSkeleton("[data-skeleton=\"drawer-apply\"]");
      };
      if (el.tagName === "FORM") el.addEventListener("submit", handler);
      else el.addEventListener("click", handler);
    });

    // Surface server-rendered error flashes as toasts
    var flash = document.querySelector("[data-desk-error]");
    if (flash) {
      var msg = flash.getAttribute("data-desk-error") || flash.textContent || "Request failed";
      deskToast(msg.trim(), "error");
    }
    var ok = document.querySelector("[data-desk-success]");
    if (ok) {
      deskToast((ok.getAttribute("data-desk-success") || ok.textContent || "Done").trim(), "success");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
