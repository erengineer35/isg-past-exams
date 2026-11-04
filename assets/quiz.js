// Şık işaretlenince doğru cevabı gösterir; seçimler localStorage'da tutulur.
// Ders notu sayfası: haftalar açılır kapanır; linkle gelinen başlığın haftası açılır.
(function () {
  var weeks = Array.prototype.slice.call(document.querySelectorAll("details.wk"));
  if (!weeks.length) return;

  function openTarget() {
    var id = decodeURIComponent(location.hash.slice(1));
    var el = id && document.getElementById(id);
    if (!el) return;
    for (var p = el; p; p = p.parentElement) {
      if (p.tagName === "DETAILS") p.open = true;
    }
    el.scrollIntoView();
  }

  window.addEventListener("hashchange", openTarget);
  openTarget();

  document.querySelector(".open-all").addEventListener("click", function () {
    weeks.forEach(function (d) { d.open = true; });
  });
  document.querySelector(".close-all").addEventListener("click", function () {
    weeks.forEach(function (d) { d.open = false; });
  });
})();

(function () {
  var bar = document.querySelector(".bar[data-exam]");
  if (!bar) return;
  var examId = bar.dataset.exam;
  var storeKey = "isg:" + examId;
  var questions = Array.prototype.slice.call(document.querySelectorAll(".q"));
  var state = {};

  try {
    state = JSON.parse(localStorage.getItem(storeKey) || "{}") || {};
  } catch (e) {
    state = {};
  }

  function save() {
    try {
      localStorage.setItem(storeKey, JSON.stringify(state));
    } catch (e) {}
  }

  function reveal(q, chosen) {
    var answer = q.dataset.answer;
    q.querySelectorAll(".opt").forEach(function (opt) {
      var k = opt.dataset.k;
      var box = opt.querySelector("input");
      box.checked = k === chosen;
      opt.classList.toggle("correct", !!answer && k === answer);
      opt.classList.toggle("wrong", k === chosen && !!answer && k !== answer);
    });
    q.classList.add("revealed");
    q.querySelector(".feedback").hidden = false;
  }

  function clear(q) {
    q.querySelectorAll(".opt").forEach(function (opt) {
      opt.querySelector("input").checked = false;
      opt.classList.remove("correct", "wrong");
    });
    q.classList.remove("revealed");
    q.querySelector(".feedback").hidden = true;
  }

  function updateScore() {
    var answered = 0;
    var right = 0;
    questions.forEach(function (q) {
      var c = state[q.id];
      if (!c) return;
      answered++;
      if (c === q.dataset.answer) right++;
    });
    bar.querySelector(".score").textContent =
      answered + " / " + questions.length + " cevaplandı · " + right + " doğru";
  }

  questions.forEach(function (q) {
    q.querySelectorAll("input").forEach(function (box) {
      box.addEventListener("change", function () {
        if (box.checked) {
          state[q.id] = box.value;
          reveal(q, box.value);
        } else {
          delete state[q.id];
          clear(q);
        }
        save();
        updateScore();
      });
    });
    if (state[q.id]) reveal(q, state[q.id]);
  });

  bar.querySelector(".show-all").addEventListener("click", function () {
    questions.forEach(function (q) {
      reveal(q, state[q.id] || null);
    });
  });

  bar.querySelector(".reset").addEventListener("click", function () {
    state = {};
    save();
    questions.forEach(clear);
    updateScore();
  });

  updateScore();
})();
