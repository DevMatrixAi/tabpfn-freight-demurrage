/* Wire data-coach / crib hints + ensure morning-digest marker after triage paint. */
(function () {
  var cribs = {
    "pack-selector": "Same engine — equipment, inland, air, stow-fit.",
    "plus": "Reads messy text — no NLP pipeline.",
    "thinking": "Follows each vessel over time.",
    "sample-n": "Small slice for live Thinking (saves API). Full table = mock or final numbers.",
    "run-triage": "Score late-fee risk on this messy table.",
    "histgbm-delta": "Lift vs a normal model on the same data.",
    "stream-rescore": "New event — score and move can change.",
    "thinking-timeline": "Vessel across time — story, not just a score."
  };
  function hint(el, id) {
    if (!el || el.querySelector('[data-coach-hint="'+id+'"]')) return;
    el.setAttribute("data-coach", id);
    var s = document.createElement("span");
    s.className = "coach-hint";
    s.setAttribute("data-coach-hint", id);
    s.textContent = cribs[id] || "";
    el.parentNode && el.parentNode.insertBefore(s, el);
  }
  function wire() {
    var pack = document.getElementById("pack");
    if (pack) { pack.setAttribute("data-coach", "pack-selector"); hint(pack, "pack-selector"); }
    var plus = document.querySelector('label[data-mode="plus"]');
    if (plus) plus.setAttribute("data-coach", "plus");
    var th = document.querySelector('label[data-mode="thinking"]');
    if (th) th.setAttribute("data-coach", "thinking");
    var effort = document.getElementById("effort-chip");
    if (effort) effort.setAttribute("data-coach", "thinking");
    var sn = document.getElementById("sample_n");
    if (sn) sn.setAttribute("data-coach", "sample-n");
    var btn = document.querySelector("form[action='/run-triage'] button[type='submit']");
    if (btn) {
      btn.setAttribute("data-coach", "run-triage");
      btn.id = btn.id || "run-triage-btn";
      hint(btn, "run-triage");
    }
    var js = document.querySelector(".judge-strip");
    if (js) {
      js.setAttribute("data-coach", "histgbm-delta");
      js.id = js.id || "histgbm-delta";
      hint(js, "histgbm-delta");
    }
    var stream = document.getElementById("btn-stream-rescore");
    if (stream) {
      stream.setAttribute("data-coach", "stream-rescore");
      hint(stream, "stream-rescore");
    }
    var tl = document.getElementById("thinking-timeline");
    if (tl) {
      tl.setAttribute("data-coach", "thinking-timeline");
      hint(tl, "thinking-timeline");
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wire);
  else wire();
})();
