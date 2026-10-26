/* SOTIF Risk Course — quiz & numeric-exercise component.
   Usage:
   <div class="widget" data-quiz="lesson-0001"> <script type="application/json">{ "questions":[...] }</script> </div>
     question: { "prompt": "...", "options": ["..",".."], "answer": 2, "explain": "..." }
   <div class="widget" data-exercise="id" data-answer="299573" data-tol="0.03" data-unit="h"> ... <input> ... </div>
     Relative tolerance; feedback text from data-explain. */
(function () {
  function store(key, val) {
    try { if (val === undefined) return JSON.parse(localStorage.getItem(key) || "null"); localStorage.setItem(key, JSON.stringify(val)); } catch (e) { return null; }
  }

  function buildQuiz(root) {
    var cfg;
    try { cfg = JSON.parse(root.querySelector('script[type="application/json"]').textContent); } catch (e) { return; }
    var id = root.getAttribute("data-quiz");
    var answered = 0, correct = 0, total = cfg.questions.length;
    var scoreEl = document.createElement("p");
    scoreEl.className = "score";
    scoreEl.setAttribute("aria-live", "polite");

    cfg.questions.forEach(function (q, qi) {
      var box = document.createElement("fieldset");
      box.className = "q";
      box.style.border = "0"; box.style.padding = "0";
      var legend = document.createElement("legend");
      legend.className = "q-prompt";
      legend.innerHTML = (qi + 1) + ". " + q.prompt;
      box.appendChild(legend);
      var opts = document.createElement("div");
      opts.className = "q-opts";
      var fb = document.createElement("div");
      fb.className = "q-fb"; fb.setAttribute("aria-live", "polite");
      q.options.forEach(function (o, oi) {
        var lab = document.createElement("label");
        lab.className = "q-opt";
        var inp = document.createElement("input");
        inp.type = "radio"; inp.name = id + "-q" + qi; inp.id = id + "-q" + qi + "-o" + oi; inp.value = oi;
        var span = document.createElement("span"); span.innerHTML = o;
        lab.appendChild(inp); lab.appendChild(span);
        inp.addEventListener("change", function () {
          if (box.dataset.done) return;
          box.dataset.done = "1";
          answered++;
          var ok = oi === q.answer;
          if (ok) correct++;
          lab.classList.add(ok ? "right" : "wrong");
          if (!ok) opts.children[q.answer].classList.add("right");
          box.querySelectorAll("input").forEach(function (x) { x.disabled = true; });
          fb.innerHTML = '<span class="verdict ' + (ok ? "ok" : "no") + '">' + (ok ? "Correct." : "Not quite.") + "</span> " + q.explain;
          if (answered === total) {
            scoreEl.textContent = "Score: " + correct + " / " + total;
            var hist = store("sotif-course:" + id) || [];
            hist.push({ t: Date.now(), score: correct, of: total });
            store("sotif-course:" + id, hist);
          }
        });
        opts.appendChild(lab);
      });
      box.appendChild(opts); box.appendChild(fb);
      root.appendChild(box);
    });
    var prev = store("sotif-course:" + id);
    if (prev && prev.length) {
      var last = prev[prev.length - 1];
      var p = document.createElement("p"); p.className = "meta";
      p.textContent = "Last attempt: " + last.score + " / " + last.of + " on " + new Date(last.t).toLocaleDateString();
      root.appendChild(p);
    }
    root.appendChild(scoreEl);
  }

  function buildExercise(root) {
    var input = root.querySelector("input");
    var btn = root.querySelector("button");
    var fb = root.querySelector(".q-fb");
    var ans = parseFloat(root.getAttribute("data-answer"));
    var tol = parseFloat(root.getAttribute("data-tol") || "0.03");
    function check() {
      var raw = (input.value || "").replace(/\s/g, "").replace(",", ".");
      var v = parseFloat(raw);
      if (!isFinite(v)) { fb.innerHTML = '<span class="verdict no">Enter a number.</span> Scientific notation such as 3e5 works.'; return; }
      var ok = Math.abs(v - ans) / Math.abs(ans) <= tol;
      fb.innerHTML = '<span class="verdict ' + (ok ? "ok" : "no") + '">' + (ok ? "Correct." : "Not yet.") + "</span> " +
        (ok ? root.getAttribute("data-explain") : (root.getAttribute("data-hint") || "Check your units and the confidence factor."));
      if (!ok) {
        var tries = (+root.dataset.tries || 0) + 1; root.dataset.tries = tries;
        if (tries >= 2) fb.innerHTML += ' <details class="reveal"><summary>Show solution</summary>' + root.getAttribute("data-explain") + "</details>";
      }
    }
    btn.addEventListener("click", check);
    input.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); check(); } });
  }

  function init() {
    document.querySelectorAll("[data-quiz]").forEach(buildQuiz);
    document.querySelectorAll("[data-exercise]").forEach(buildExercise);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
