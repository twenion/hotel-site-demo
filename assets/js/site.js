/* Qırx Pəncərə — the only script on the site.
   Everything here is an enhancement. With JavaScript off the pages still list every
   room, print every price of every night, and show how to reach the house; the form
   falls back to a <noscript> block with the phone, WhatsApp and e-mail on it.
   No cookies, no storage, no network calls, no third party. */
(function () {
  "use strict";
  document.documentElement.classList.add("js");

  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  };

  /* --- Menu ---------------------------------------------------------------- */
  var toggle = $(".nav-toggle"), nav = $("#nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && nav.classList.contains("is-open")) {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }

  /* --- Reveal on scroll ---------------------------------------------------- */
  var reveals = $$(".reveal");
  if (reveals.length) {
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce || !("IntersectionObserver" in window)) {
      reveals.forEach(function (el) { el.classList.add("is-in"); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });
      reveals.forEach(function (el) { io.observe(el); });
    }
  }

  /* --- Reservation --------------------------------------------------------- */
  var form = $("#res-form");
  if (!form || typeof window.QP === "undefined") { return; }
  var QP = window.QP;

  var DAY = 86400000;
  function toUTC(s) {
    var p = String(s).split("-");
    if (p.length !== 3) { return null; }
    var d = Date.UTC(+p[0], +p[1] - 1, +p[2]);
    return isNaN(d) ? null : d;
  }
  var START = toUTC(QP.start), END = toUTC(QP.end);

  function fmtDate(ms) {
    var d = new Date(ms);
    function pad(n) { return n < 10 ? "0" + n : String(n); }
    return pad(d.getUTCDate()) + "." + pad(d.getUTCMonth() + 1) + "." + d.getUTCFullYear();
  }
  function money(v) {
    return String(v).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₼";
  }
  /* The same arithmetic as tools/hotel.py, including the rounding: floor(x + .5),
     because Python's round() is banker's rounding and Math.round is not. */
  function nightPrice(slug, ms) {
    var room = QP.rooms[slug];
    var code = QP.days.charAt(Math.round((ms - START) / DAY));
    var s = QP.seasons[code];
    if (!room || !s) { return null; }
    return Math.floor(room.base * s.factor / 5 + 0.5) * 5;
  }
  function seasonAt(ms) {
    return QP.seasons[QP.days.charAt(Math.round((ms - START) / DAY))];
  }

  var fIn = $("#f-in"), fOut = $("#f-out"), fRoom = $("#f-room"), fGuests = $("#f-guests");
  var fName = $("#f-name"), fPhone = $("#f-phone"), fNote = $("#f-note"), fOk = $("#f-ok");

  /* A room page links here with ?otaq=slug. Nothing else is read from the URL. */
  try {
    var want = new URLSearchParams(window.location.search).get("otaq");
    if (want && QP.rooms[want]) { fRoom.value = want; }
  } catch (err) { /* older browser: the default selection stands */ }

  function nightsBetween() {
    var a = toUTC(fIn.value), b = toUTC(fOut.value);
    if (a === null || b === null || b <= a) { return null; }
    var out = [];
    for (var t = a; t < b; t += DAY) { out.push(t); }
    return out;
  }

  function quote() {
    var nights = nightsBetween();
    var t = { nights: $("#t-nights"), room: $("#t-room"), season: $("#t-season"), sum: $("#t-sum") };
    var slug = fRoom.value, room = QP.rooms[slug];
    t.room.textContent = room ? room.name + " — " + room.kind.toLowerCase() : "—";
    if (!nights || !room) {
      t.nights.textContent = "—"; t.season.textContent = "—"; t.sum.textContent = "—";
      return null;
    }
    var sum = 0, names = [], minNeeded = 1;
    for (var i = 0; i < nights.length; i++) {
      var p = nightPrice(slug, nights[i]);
      if (p === null) { t.sum.textContent = "—"; return null; }
      sum += p;
      var s = seasonAt(nights[i]);
      if (names.indexOf(s.name) === -1) { names.push(s.name); }
      if (s.min > minNeeded) { minNeeded = s.min; }
    }
    t.nights.textContent = nights.length + " gecə";
    t.season.textContent = names.join(", ");
    t.sum.textContent = money(sum);
    return { nights: nights, sum: sum, room: room, slug: slug, minNeeded: minNeeded };
  }

  function setError(fieldId, errId, message) {
    var err = $(errId), field = $(fieldId).closest(".field");
    if (message) {
      err.textContent = message; err.hidden = false;
      if (field) { field.classList.add("is-bad"); }
      $(fieldId).setAttribute("aria-invalid", "true");
    } else {
      err.hidden = true;
      if (field) { field.classList.remove("is-bad"); }
      $(fieldId).removeAttribute("aria-invalid");
    }
    return !message;
  }

  function validate() {
    var ok = true, q = quote();
    var a = toUTC(fIn.value), b = toUTC(fOut.value);

    if (a === null) { ok = setError("#f-in", "#e-in", "Gəliş tarixini seçin.") && ok; }
    else if (a < START || a > END) {
      ok = setError("#f-in", "#e-in",
        "Təqvim " + fmtDate(START) + " – " + fmtDate(END) + " aralığını əhatə edir.") && ok;
    } else { setError("#f-in", "#e-in", ""); }

    if (b === null) { ok = setError("#f-out", "#e-out", "Çıxış tarixini seçin.") && ok; }
    else if (a !== null && b <= a) {
      ok = setError("#f-out", "#e-out", "Çıxış tarixi gəlişdən sonra olmalıdır.") && ok;
    } else if (q && q.nights.length < q.minNeeded) {
      ok = setError("#f-out", "#e-out",
        "Bu tarixlərdə minimum " + q.minNeeded + " gecə qalmaq lazımdır.") && ok;
    } else { setError("#f-out", "#e-out", ""); }

    var guests = parseInt(fGuests.value, 10);
    var room = QP.rooms[fRoom.value];
    if (room && guests > room.sleeps) {
      ok = setError("#f-guests", "#e-guests",
        room.name + " otağı " + room.sleeps + " nəfərlikdir. Başqa otaq seçin.") && ok;
    } else { setError("#f-guests", "#e-guests", ""); }

    if (!fName.value.trim()) {
      ok = setError("#f-name", "#e-name", "Adınızı yazın.") && ok;
    } else { setError("#f-name", "#e-name", ""); }

    var digits = fPhone.value.replace(/\D/g, "");
    if (digits.length < 9) {
      ok = setError("#f-phone", "#e-phone", "Telefon nömrəsini tam yazın.") && ok;
    } else { setError("#f-phone", "#e-phone", ""); }

    var eok = $("#e-ok");
    if (!fOk.checked) {
      eok.textContent = "Davam etmək üçün qaydaları oxuduğunuzu təsdiqləyin.";
      eok.hidden = false; ok = false;
    } else { eok.hidden = true; }

    return ok ? q : null;
  }

  function message(q) {
    var lines = [
      "Salam! Qırx Pəncərə üçün rezervasiya istəyirəm.",
      "",
      "Tarix: " + fmtDate(q.nights[0]) + " – " +
        fmtDate(q.nights[q.nights.length - 1] + DAY) + " (" + q.nights.length + " gecə)",
      "Otaq: " + q.room.name,
      "Nəfər: " + fGuests.value,
      "Cəmi: " + money(q.sum) + " (ƏDV və səhər yeməyi daxil)",
      "",
      "Ad, soyad: " + fName.value.trim(),
      "Telefon: " + fPhone.value.trim()
    ];
    if (fNote.value.trim()) { lines.push("", "Qeyd: " + fNote.value.trim()); }
    return lines.join("\n");
  }

  ["change", "input"].forEach(function (ev) {
    form.addEventListener(ev, function () { quote(); });
  });
  quote();

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var q = validate();
    if (!q) { var bad = $(".is-bad input, .is-bad select"); if (bad) { bad.focus(); } return; }
    window.open("https://wa.me/" + QP.phone.replace(/\D/g, "") +
      "?text=" + encodeURIComponent(message(q)), "_blank", "noopener");
  });

  var mailBtn = $("#res-mail");
  if (mailBtn) {
    mailBtn.addEventListener("click", function () {
      var q = validate();
      if (!q) { var bad = $(".is-bad input, .is-bad select"); if (bad) { bad.focus(); } return; }
      var subject = "Rezervasiya — " + q.room.name + ", " + fmtDate(q.nights[0]);
      window.location.href = "mailto:" + QP.email +
        "?subject=" + encodeURIComponent(subject) +
        "&body=" + encodeURIComponent(message(q));
    });
  }
})();
