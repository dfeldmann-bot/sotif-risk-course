/* SOTIF Risk Course — validation-target calculator component.
   Pure functions exposed on window.VT for reuse (later lessons, tests):
     VT.poissonCdf(k, lambda)
     VT.lambdaUpper(k, C)   -> λ with P(X ≤ k | λ) = 1 − C   (= χ²_{2(k+1)}(C) / 2)
     VT.tau(R, C, k)        -> exposure needed so that observing ≤ k events demonstrates rate ≤ R at confidence C
   Mount: <div class="widget" data-vtcalc></div> */
(function () {
  function poissonCdf(k, lam) {
    var term = Math.exp(-lam), sum = term;
    for (var i = 1; i <= k; i++) { term *= lam / i; sum += term; }
    return sum;
  }
  function lambdaUpper(k, C) {
    var target = 1 - C, lo = 0, hi = 10 + 10 * k;
    while (poissonCdf(k, hi) > target) hi *= 2;
    for (var i = 0; i < 200; i++) { var mid = (lo + hi) / 2; if (poissonCdf(k, mid) > target) lo = mid; else hi = mid; }
    return (lo + hi) / 2;
  }
  function tau(R, C, k) { return lambdaUpper(k || 0, C) / R; }
  window.VT = { poissonCdf: poissonCdf, lambdaUpper: lambdaUpper, tau: tau };

  function fmt(x) {
    if (!isFinite(x)) return "—";
    if (x === 0) return "0";
    var e = Math.floor(Math.log10(Math.abs(x)));
    if (e >= -2 && e < 6) return x.toLocaleString("en-US", { maximumSignificantDigits: 4 });
    var m = x / Math.pow(10, e);
    return m.toFixed(2) + " × 10" + sup(e);
  }
  function sup(n) {
    var map = { "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹" };
    return String(n).split("").map(function (c) { return map[c]; }).join("");
  }

  function mount(root) {
    root.innerHTML =
      '<p class="w-title">Validation-target calculator</p>' +
      '<div class="grid">' +
      field("vt-ah", "Acceptance criterion A<sub>H</sub> (harm per hour)", "1e-7") +
      field("vt-pe", "P(E | HB): exposure to the hazardous scenario", "0.1") +
      field("vt-pc", "P(C̄ | E): not controllable", "0.5") +
      field("vt-ps", "P(S | C̄): severity reached", "0.2") +
      '<div class="field"><label for="vt-c">Confidence C</label><select id="vt-c"><option>0.90</option><option selected>0.95</option><option>0.99</option></select></div>' +
      field("vt-k", "Events k allowed in the plan", "0") +
      field("vt-fleet", "Fleet size × hours per vehicle-year", "50 × 3000") +
      "</div>" +
      '<div class="out" aria-live="polite">' +
      out("vt-rhb", "R<sub>HB</sub> tolerable (per h)") +
      out("vt-lam", "Factor λ<sub>k</sub>(C)") +
      out("vt-tau", "τ test hours needed") +
      out("vt-yrs", "Calendar years for this fleet") +
      "</div>";
    function field(id, label, val) { return '<div class="field"><label for="' + id + '">' + label + '</label><input id="' + id + '" type="text" inputmode="decimal" value="' + val + '"></div>'; }
    function out(id, label) { return '<div><div class="k">' + label + '</div><div class="val" id="' + id + '">—</div></div>'; }
    function num(id) { return parseFloat(String(document.getElementById(id).value).replace(",", ".")); }
    function update() {
      var A = num("vt-ah"), pe = num("vt-pe"), pc = num("vt-pc"), ps = num("vt-ps"), C = parseFloat(document.getElementById("vt-c").value);
      var k = Math.max(0, Math.round(num("vt-k") || 0));
      var fleetTxt = document.getElementById("vt-fleet").value.split(/[x×*]/).map(function (s) { return parseFloat(s); });
      var perYear = (fleetTxt[0] || 0) * (fleetTxt[1] || 0);
      var R = A / (pe * pc * ps);
      var lam = lambdaUpper(k, C);
      var T = lam / R;
      document.getElementById("vt-rhb").textContent = fmt(R);
      document.getElementById("vt-lam").textContent = lam.toFixed(3);
      document.getElementById("vt-tau").textContent = fmt(T);
      document.getElementById("vt-yrs").textContent = perYear > 0 ? fmt(T / perYear) : "—";
    }
    root.querySelectorAll("input,select").forEach(function (el) { el.addEventListener("input", update); });
    update();
  }
  function init() { document.querySelectorAll("[data-vtcalc]").forEach(mount); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
