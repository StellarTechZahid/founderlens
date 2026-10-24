/* FoundersLens - small, dependency-free helpers */
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.documentElement.classList.remove("no-js");

  /* nav: border on scroll, mobile menu */
  var nav = document.getElementById("nav");
  function onScroll() { if (nav) nav.classList.toggle("scrolled", window.scrollY > 8); }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  var btn = document.getElementById("menuBtn"), links = document.getElementById("navLinks");
  if (btn && links) {
    btn.addEventListener("click", function () {
      var open = links.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* count-up numbers (used on the report score) */
  function countUp(el) {
    var target = parseFloat(el.getAttribute("data-count")) || 0;
    var decimals = parseInt(el.getAttribute("data-decimals") || "0", 10);
    if (reduce || !target) return;
    var start = null, dur = 1400;
    function tick(ts) {
      if (start === null) start = ts;
      var p = Math.min(1, (ts - start) / dur), eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (target * eased).toFixed(decimals);
      if (p < 1) requestAnimationFrame(tick); else el.textContent = target.toFixed(decimals);
    }
    el.textContent = (0).toFixed(decimals);
    requestAnimationFrame(tick);
  }
  document.querySelectorAll("[data-count]").forEach(countUp);

  /* generic tabs: [data-tabs] contains buttons[data-tab], panels are [data-panel="<id>"] */
  document.querySelectorAll("[data-tabs]").forEach(function (group) {
    var scope = document.querySelector(group.getAttribute("data-tabs")) || document;
    var buttons = group.querySelectorAll("[data-tab]");
    function show(id) {
      buttons.forEach(function (b) { b.setAttribute("aria-selected", b.getAttribute("data-tab") === id ? "true" : "false"); });
      scope.querySelectorAll("[data-panel]").forEach(function (p) { p.hidden = p.getAttribute("data-panel") !== id; });
    }
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        var id = b.getAttribute("data-tab");
        show(id);
        if (group.hasAttribute("data-hash")) history.replaceState(null, "", "#" + id);
      });
    });
    var initial = buttons[0] && buttons[0].getAttribute("data-tab");
    if (group.hasAttribute("data-hash") && location.hash) {
      var h = location.hash.slice(1);
      buttons.forEach(function (b) { if (b.getAttribute("data-tab") === h) initial = h; });
    }
    if (initial) show(initial);
  });

  /* hero lens: the circles drift together once, then follow the cursor */
  var hero = document.getElementById("heroLens");
  if (hero) {
    var cx = 300, cy = 250, r = 185;
    var pk = document.getElementById("hl-pk"), gl = document.getElementById("hl-gl");
    var lens = document.getElementById("hl-lens"), idea = document.getElementById("hl-idea");
    var lpk = document.getElementById("hl-lab-pk"), lgl = document.getElementById("hl-lab-gl");
    var d = reduce ? 214 : 360, target = 214, started = false;

    function render() {
      var half = d / 2;
      pk.setAttribute("cx", cx - half); gl.setAttribute("cx", cx + half);
      lpk.setAttribute("x", cx - half); lgl.setAttribute("x", cx + half);
      var overlap = 2 * r - d;
      if (overlap > 8) {
        var h = Math.sqrt(r * r - half * half);
        lens.setAttribute("d", "M" + cx + " " + (cy - h) + " A" + r + " " + r + " 0 0 1 " + cx + " " + (cy + h) +
                               " A" + r + " " + r + " 0 0 1 " + cx + " " + (cy - h) + " Z");
        lens.style.opacity = 1;
      } else { lens.style.opacity = 0; }
      idea.style.opacity = overlap > 110 ? 1 : 0;
    }
    function frame() {
      var ease = started ? 0.08 : 0.045;
      d += (target - d) * ease;
      render();
      if (Math.abs(target - d) > 0.2) requestAnimationFrame(frame); else { d = target; render(); running = false; }
    }
    var running = false;
    function go() { if (!running) { running = true; requestAnimationFrame(frame); } }
    render();
    if (!reduce) {
      setTimeout(function () { started = true; }, 1600);
      go();
      window.addEventListener("pointermove", function (e) {
        if (e.pointerType === "touch") return;
        var p = Math.max(0, Math.min(1, e.clientX / window.innerWidth));
        target = 168 + 112 * p;      /* closer = more overlap */
        go();
      }, { passive: true });
    }
  }
})();
