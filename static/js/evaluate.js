/* Multi-step intake form: validation per step, draft autosave, example filler, background submit */
(function () {
  "use strict";
  var form = document.getElementById("intake");
  if (!form) return;
  var steps = Array.prototype.slice.call(form.querySelectorAll(".step"));
  var segs = form.querySelectorAll(".segments i");
  var nextBtn = document.getElementById("nextBtn"), backBtn = document.getElementById("backBtn");
  var count = document.getElementById("wizCount"), formError = document.getElementById("formError");
  var KEY = "founderslens_draft_v2";
  var current = 0, submitting = false;

  /* ---------- reading / writing answers ---------- */
  function readAll() {
    var out = {};
    form.querySelectorAll(".field").forEach(function (f) {
      var key = f.getAttribute("data-key"), type = f.getAttribute("data-type");
      if (type === "checkbox_group") {
        out[key] = Array.prototype.map.call(f.querySelectorAll("input:checked"), function (i) { return i.value; });
      } else if (type === "select") {
        var c = f.querySelector("input:checked"); out[key] = c ? c.value : "";
      } else {
        out[key] = f.querySelector("input,textarea").value;
      }
    });
    return out;
  }
  function fillAll(data) {
    form.querySelectorAll(".field").forEach(function (f) {
      var key = f.getAttribute("data-key"), type = f.getAttribute("data-type"), v = data[key];
      if (v === undefined || v === null) return;
      if (type === "checkbox_group") {
        var arr = Array.isArray(v) ? v : String(v).split(",").map(function (s) { return s.trim(); });
        f.querySelectorAll("input").forEach(function (i) { i.checked = arr.indexOf(i.value) !== -1; });
      } else if (type === "select") {
        f.querySelectorAll("input").forEach(function (i) { i.checked = i.value === v; });
      } else {
        f.querySelector("input,textarea").value = v;
      }
    });
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify({ data: readAll(), step: current })); } catch (e) { /* storage may be blocked */ }
  }
  function clearDraft() { try { localStorage.removeItem(KEY); } catch (e) { /* ignore */ } }

  /* ---------- validation ---------- */
  function fieldValue(f) {
    var type = f.getAttribute("data-type");
    if (type === "checkbox_group") return f.querySelectorAll("input:checked").length ? "ok" : "";
    if (type === "select") return f.querySelector("input:checked") ? "ok" : "";
    return f.querySelector("input,textarea").value.trim();
  }
  function checkField(f) {
    var type = f.getAttribute("data-type"), required = f.hasAttribute("data-required");
    var v = fieldValue(f), msg = "";
    if (required && !v) msg = (type === "select" || type === "checkbox_group") ? "Choose an option to continue." : "This answer is required.";
    else if (type === "email" && v && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v)) msg = "Enter a valid email address.";
    else if (type === "textarea" && required && v && v.length < 8) msg = "Add a little more detail (at least 8 characters).";
    setError(f, msg);
    return !msg;
  }
  function setError(f, msg) {
    f.classList.toggle("invalid", !!msg);
    f.querySelector(".err").textContent = msg || "";
  }
  function checkStep(i) {
    var first = null;
    steps[i].querySelectorAll(".field").forEach(function (f) {
      if (!checkField(f) && !first) first = f;
    });
    if (first) {
      var target = first.querySelector("input,textarea");
      first.scrollIntoView({ behavior: "smooth", block: "center" });
      if (target && target.type !== "radio" && target.type !== "checkbox") target.focus({ preventScroll: true });
      return false;
    }
    return true;
  }

  /* ---------- navigation ---------- */
  function show(i) {
    current = Math.max(0, Math.min(steps.length - 1, i));
    steps.forEach(function (s, n) { s.hidden = n !== current; });
    segs.forEach(function (s, n) { s.classList.toggle("on", n <= current); });
    count.textContent = "Step " + (current + 1) + " of " + steps.length;
    backBtn.hidden = current === 0;
    nextBtn.textContent = current === steps.length - 1 ? "Run the evaluation" : "Continue";
    window.scrollTo({ top: 0, behavior: "smooth" });
    save();
  }
  nextBtn.addEventListener("click", function () {
    formError.hidden = true;
    if (!checkStep(current)) return;
    if (current < steps.length - 1) show(current + 1); else submit();
  });
  backBtn.addEventListener("click", function () { show(current - 1); });
  form.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && e.target.tagName === "INPUT" && e.target.type !== "radio" && e.target.type !== "checkbox") {
      e.preventDefault(); nextBtn.click();
    }
  });
  form.addEventListener("input", function (e) {
    var f = e.target.closest(".field"); if (f && f.classList.contains("invalid")) checkField(f);
    save();
  });
  form.addEventListener("change", function (e) {
    var f = e.target.closest(".field"); if (f && f.classList.contains("invalid")) checkField(f);
    save();
  });

  /* ---------- submit ---------- */
  function submit() {
    if (submitting) return;
    for (var i = 0; i < steps.length; i++) {           /* re-check everything before sending */
      if (!checkStep(i)) { show(i); return; }
    }
    submitting = true; nextBtn.disabled = true; nextBtn.textContent = "Starting the agents";
    var body = new FormData(form);
    fetch("/api/submit", { method: "POST", body: body })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (res.ok && res.j.ok) { clearDraft(); window.location.href = "/processing/" + res.j.job_id; return; }
        var errs = (res.j && res.j.errors) || [], firstStep = null;
        errs.forEach(function (er) {
          var f = form.querySelector('.field[data-key="' + er.key + '"]');
          if (f) { setError(f, er.message); var s = steps.indexOf(f.closest(".step")); if (firstStep === null || s < firstStep) firstStep = s; }
        });
        if (firstStep !== null) show(firstStep);
        formError.textContent = errs.length ? "Some answers need fixing before we can run the evaluation." : "The server could not start the evaluation. Please try again.";
        formError.hidden = false; resetButton();
      })
      .catch(function () {
        formError.textContent = "Could not reach the server. Check that the site is still running, then try again.";
        formError.hidden = false; resetButton();
      });
  }
  function resetButton() { submitting = false; nextBtn.disabled = false; nextBtn.textContent = current === steps.length - 1 ? "Run the evaluation" : "Continue"; }

  /* ---------- example + draft ---------- */
  document.getElementById("exampleBtn").addEventListener("click", function () {
    if (window.FL_EXAMPLE) { fillAll(window.FL_EXAMPLE); form.querySelectorAll(".field").forEach(function (f) { setError(f, ""); }); save(); show(0); }
  });
  try {
    var saved = JSON.parse(localStorage.getItem(KEY) || "null");
    if (saved && saved.data) { fillAll(saved.data); show(saved.step || 0); } else { show(0); }
  } catch (e) { show(0); }
})();
