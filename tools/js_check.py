#!/usr/bin/env python3
"""Proves the browser and the build agree on the money.

The reservation form recomputes prices in JavaScript from a base and a season
factor. Python does the same arithmetic when it writes the calendars. A
screenshot cannot tell you those two landed on the same ₼ -- this can.

It builds a temporary copy of rezervasiya.html with a harness appended, drives
the form in headless Chrome, and compares what the browser printed against what
hotel.py says. It also checks the two refusals the form has to make: too many
guests for the room, and a stay shorter than the season's minimum.

    python3 tools/js_check.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hotel  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CHROME = os.environ.get(
    "CHROME", "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe")

# (room, check-in, check-out) -- chosen to cross season boundaries, not to sit
# comfortably inside one.
PRICE_CASES = [
    ("benovse", "2027-01-10", "2027-01-13"),   # three quiet nights
    ("yaqut", "2027-03-19", "2027-03-23"),     # spring into Novruz
    ("gulabi", "2026-12-24", "2026-12-27"),    # quiet into New Year
    ("zumrud", "2026-09-01", "2026-09-02"),    # one autumn night
    ("firuze", "2027-06-28", "2027-07-05"),    # a week of summer
    ("kehreba", "2027-05-30", "2027-06-02"),   # spring into summer
]

# (room, in, out, guests, which error must fire, a word it must contain)
REFUSALS = [
    ("benovse", "2027-02-01", "2027-02-03", 3, "e-guests", "nəfərlikdir"),
    ("yaqut", "2027-03-21", "2027-03-22", 2, "e-out", "minimum"),
    ("zumrud", "2026-12-30", "2026-12-31", 2, "e-out", "minimum"),
]


def expected():
    out = []
    for slug, a, b in PRICE_CASES:
        r = hotel.ROOM_BY_SLUG[slug]
        d0, d1 = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
        nights = [d0 + dt.timedelta(days=i) for i in range((d1 - d0).days)]
        out.append({"slug": slug, "in": a, "out": b, "nights": len(nights),
                    "sum": sum(hotel.price(r, d) for d in nights),
                    "seasons": sorted({hotel.season_for(d).name for d in nights})})
    return out


HARNESS = """
<script>
window.addEventListener("load", function () {
  var P = %s, F = %s, res = {prices: [], refusals: []};
  function set(id, v) { document.getElementById(id).value = v; }
  function fire() {
    document.getElementById("res-form").dispatchEvent(new Event("input", {bubbles: true}));
  }
  P.forEach(function (c) {
    set("f-in", c["in"]); set("f-out", c.out); set("f-room", c.slug); fire();
    res.prices.push({slug: c.slug,
      nights: document.getElementById("t-nights").textContent,
      sum: document.getElementById("t-sum").textContent,
      season: document.getElementById("t-season").textContent});
  });
  F.forEach(function (c) {
    set("f-in", c["in"]); set("f-out", c.out); set("f-room", c.slug);
    set("f-guests", String(c.guests));
    set("f-name", "Test"); set("f-phone", "+994500000000");
    document.getElementById("f-ok").checked = true;
    fire();
    document.getElementById("res-form").dispatchEvent(
      new Event("submit", {bubbles: true, cancelable: true}));
    var el = document.getElementById(c.err);
    res.refusals.push({err: c.err, hidden: el.hidden, text: el.textContent});
  });
  var pre = document.createElement("pre");
  pre.id = "JSRESULT";
  pre.textContent = JSON.stringify(res);
  document.body.appendChild(pre);
});
</script>
"""


def main() -> int:
    exp = expected()
    page = (ROOT / "rezervasiya.html").read_text(encoding="utf-8")
    harness = HARNESS % (json.dumps(exp, ensure_ascii=False),
                         json.dumps([{"slug": s, "in": a, "out": b, "guests": g,
                                      "err": err} for s, a, b, g, err, _ in REFUSALS],
                                    ensure_ascii=False))
    tmp = ROOT / "_jscheck.html"
    tmp.write_text(page.replace("</body>", harness + "</body>"), encoding="utf-8")
    try:
        win = subprocess.run(["wslpath", "-w", str(tmp)], capture_output=True,
                             text=True).stdout.strip() or str(tmp)
        dom = subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--virtual-time-budget=5000",
             "--dump-dom", win],
            capture_output=True, text=True, timeout=90).stdout
    finally:
        tmp.unlink(missing_ok=True)

    m = re.search(r'<pre id="JSRESULT">(.*?)</pre>', dom, re.S)
    if not m:
        print("FAIL: the harness never ran -- did the page throw?")
        return 1
    got = json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&"))

    bad = 0
    for want, have in zip(exp, got["prices"]):
        want_sum = f"{want['sum']:,}".replace(",", " ") + " ₼"
        want_nights = f"{want['nights']} gecə"
        want_seasons = sorted(s.strip() for s in have["season"].split(","))
        ok = (have["sum"] == want_sum and have["nights"] == want_nights
              and want_seasons == want["seasons"])
        print(f"{'ok  ' if ok else 'FAIL'} {want['slug']:9} {want['in']}→{want['out']} "
              f"{have['nights']:>8} {have['sum']:>9}  ({have['season']})")
        if not ok:
            bad += 1
            print(f"      expected {want_nights} / {want_sum} / "
                  f"{', '.join(want['seasons'])}")

    for (slug, a, b, g, err, word), have in zip(REFUSALS, got["refusals"]):
        ok = (not have["hidden"]) and word in have["text"]
        print(f"{'ok  ' if ok else 'FAIL'} refusal {err:9} {slug:9} "
              f"{'shown' if not have['hidden'] else 'NOT SHOWN'}: {have['text'][:60]}")
        if not ok:
            bad += 1

    total = len(exp) + len(REFUSALS)
    print(f"\n{total - bad}/{total} checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
