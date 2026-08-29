#!/usr/bin/env python3
"""Proves audit.py actually catches things.

A checklist that only ever prints ticks is indistinguishable from a checklist
that does not run. This copies the site to a temporary directory, breaks one
thing at a time -- in the ways we have really found on client sites -- and
asserts the audit fails and says why.

    python3 tools/audit_selftest.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sub(path: str, old: str, new: str, count: int = 1):
    def apply(root: Path) -> None:
        f = root / path
        text = f.read_text(encoding="utf-8")
        if old not in text:
            raise AssertionError(f"self-test is stale: {old[:70]!r} not in {path}")
        f.write_text(text.replace(old, new, count), encoding="utf-8")
    return apply


def regex_sub(path: str, pattern: str, new: str, count: int = 1):
    def apply(root: Path) -> None:
        f = root / path
        text = f.read_text(encoding="utf-8")
        text2, n = re.subn(pattern, new, text, count=count, flags=re.S)
        if not n:
            raise AssertionError(f"self-test is stale: /{pattern}/ not in {path}")
        f.write_text(text2, encoding="utf-8")
    return apply


def remove_file(path: str):
    def apply(root: Path) -> None:
        f = root / path
        if not f.exists():
            raise AssertionError(f"self-test is stale: {path} was already gone")
        f.unlink()
    return apply


# (what we broke, how, a word the audit must say about it)
FAULTS = [
    ("no lang attribute",
     sub("otaqlar.html", '<html lang="az">', "<html>"), "lang"),

    ("the h1 is the brand name, wrapped round the logo",
     regex_sub("sebeke.html", r"<h1>.*?</h1>", "<h1>Qırx Pəncərə</h1>"), "brand name"),

    ("no h1 at all",
     regex_sub("qaydalar.html", r"<h1>.*?</h1>", ""), "<h1>"),

    ("empty alt on a room photo",
     regex_sub("otaq-yaqut.html", r'alt="Yaqut otağının şəbəkə[^"]*"', 'alt=""'),
     "empty alt"),

    ("a meaningless alt",
     regex_sub("otaq-firuze.html", r'alt="Firuzə otağının şəbəkə[^"]*"', 'alt="şəkil"'),
     "meaningless alt"),

    ("two pages sharing one title",
     regex_sub("mexfilik.html", r"<title>.*?</title>",
               "<title>Ev qaydaları və ləğv şərtləri | Qırx Pəncərə</title>"), "copy of"),

    ("og:image pointing at a file that was renamed",
     sub("index.html", "assets/img/og-cover.png", "assets/img/kohne-banner.png", 99),
     "does not exist"),

    ("JSON-LD that does not parse",
     sub("restoran.html", '"@type": "Restaurant"', '"@type": "Restaurant",,'),
     "does not parse"),

    ("schema shipped with an empty field",
     sub("elaqe.html", '"name": "Qırx Pəncərə Qonaq Evi"', '"name": ""'), "empty"),

    ("an Offer with no price",
     regex_sub("otaq-benovse.html", r'"price": 90, ', ""), "price"),

    ("an e-mail address written as plain text",
     sub("elaqe.html", f'href="mailto:salam@qirxpencere.example"',
         'href="salam@qirxpencere.example"'), "mailto"),

    ("a link to a page that was deleted",
     sub("index.html", 'href="restoran.html"', 'href="menyu.html"'), "not there"),

    ("lorem ipsum left in the copy",
     sub("haqqimizda.html", "<p>Bina 1920-ci illərdə", "<p>Lorem ipsum dolor sit amet. "),
     "lorem"),

    ("a page missing from the sitemap",
     regex_sub("sitemap.xml",
               r"  <url>\n    <loc>[^<]*qiymetler\.html</loc>.*?</url>\n", ""),
     "does not list"),

    ("a calendar cell that no longer matches the model",
     sub("otaq-zumrud.html", '<span class="dd">3</span><span class="pp">275</span>',
         '<span class="dd">3</span><span class="pp">240</span>'), "the model says"),

    ("data.js drifting from hotel.py",
     sub("assets/js/data.js", '"gulabi":{"name":"Gülabı","base":245',
         '"gulabi":{"name":"Gülabı","base":199'), "hotel.py says"),

    ("the calendar being built by script instead of shipped",
     regex_sub("otaq-lacivard.html", r'<div class="cal-grid">.*?</div></section>',
               '<div class="cal-grid" id="cal"></div></section>'), "built by script"),

    ("a table with no caption",
     sub("otaqlar.html", "<caption>Səkkiz otaq yan-yana", "<span>Səkkiz otaq yan-yana"),
     "no <caption>"),

    ("a heading level skipped",
     regex_sub("beledci-seki-halvasi.html", r"<h2>Qatın sayı fərq edir</h2>",
               "<h4>Qatın sayı fərq edir</h4>"), "jumps"),

    ("body text dropped below the contrast bar",
     sub("assets/css/style.css", "--ink-2: #4B534E;", "--ink-2: #9AA39C;"), "below"),

    ("a font file that never got uploaded",
     remove_file("assets/fonts/plexsans-600-latin.woff2"), "missing font"),

    ("the noscript fallback removed from the one page that needs it",
     regex_sub("rezervasiya.html", r"<noscript>.*?</noscript>", ""), "noscript"),
]


def run_audit(root: Path) -> str:
    r = subprocess.run([sys.executable, "tools/audit.py"], cwd=root,
                       capture_output=True, text=True, timeout=180)
    return r.stdout + r.stderr


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "site"
        shutil.copytree(ROOT, base, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", "*.pyc"))

        clean = run_audit(base)
        if "no faults" not in clean:
            print("The unmodified copy does not pass. Fix that first:\n")
            print(clean)
            return 1
        print("clean copy passes\n")

        caught = 0
        for label, mutate, word in FAULTS:
            work = Path(tmp) / "work"
            if work.exists():
                shutil.rmtree(work)
            shutil.copytree(base, work)
            mutate(work)
            out = run_audit(work)
            hit = word.lower() in out.lower() and "no faults" not in out
            print(f"{'ok  ' if hit else 'MISS'} {label}")
            if hit:
                caught += 1
            else:
                line = next((l for l in out.splitlines() if "✗" in l), "(nothing failed)")
                print(f"       expected the audit to say {word!r}; it said: {line.strip()}")

        print(f"\n{caught}/{len(FAULTS)} faults caught")
        return 0 if caught == len(FAULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
