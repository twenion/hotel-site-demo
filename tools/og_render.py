#!/usr/bin/env python3
"""Share cards, rendered in a real browser.

A room link pasted into WhatsApp has to show the room, its size and its price.
Chat apps do not preview SVG, so the şəbəkə panels cannot be the og:image --
these PNGs are drawn from the same panels and the same numbers.

    python3 tools/og_render.py        (needs Chrome; set CHROME to override)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hotel  # noqa: E402
from render import money  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/img/og"
CHROME = os.environ.get(
    "CHROME", "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe")
W, H = 1200, 630


def win(p: Path) -> str:
    r = subprocess.run(["wslpath", "-w", str(p)], capture_output=True, text=True)
    return r.stdout.strip() or str(p)


CARD_CSS = """
@font-face{font-family:Z;src:url('../fonts/zillaslab-700-latin.woff2') format('woff2');
  unicode-range:U+0000-00FF,U+0131,U+0152-0153;}
@font-face{font-family:Z;src:url('../fonts/zillaslab-700-latinext.woff2') format('woff2');
  unicode-range:U+0100-02BA,U+1E00-1E9F,U+20A0-20AB,U+20AD-20C0;}
@font-face{font-family:P;src:url('../fonts/plexsans-400-latin.woff2') format('woff2');
  unicode-range:U+0000-00FF,U+0131,U+0152-0153;}
@font-face{font-family:P;src:url('../fonts/plexsans-400-latinext.woff2') format('woff2');
  unicode-range:U+0100-02BA,U+1E00-1E9F,U+20A0-20AB,U+20AD-20C0;}
@font-face{font-family:P6;src:url('../fonts/plexsans-600-latin.woff2') format('woff2');
  unicode-range:U+0000-00FF,U+0131,U+0152-0153;}
@font-face{font-family:P6;src:url('../fonts/plexsans-600-latinext.woff2') format('woff2');
  unicode-range:U+0100-02BA,U+1E00-1E9F,U+20A0-20AB,U+20AD-20C0;}
*{margin:0;padding:0;box-sizing:border-box}
body{width:1200px;height:630px;overflow:hidden;background:#2D2320;color:#F2EDE6;
  font-family:P,sans-serif;display:flex}
.side{flex:0 0 430px;border-left:10px solid #4A3A31;background:#4A3A31}
.side img{width:100%;height:100%;object-fit:cover;display:block}
.main{flex:1;padding:62px 56px;display:flex;flex-direction:column;justify-content:space-between}
.brand{font-family:P6;font-size:19px;letter-spacing:.16em;text-transform:uppercase;
  color:#C9BBAE}
.kind{font-family:P6;font-size:24px;letter-spacing:.02em;margin-bottom:14px}
h1{font-family:Z,serif;font-size:74px;line-height:1.02;letter-spacing:-.02em}
h1.small{font-size:56px}
.facts{display:flex;gap:34px;margin-top:26px;font-size:24px;color:#C9BBAE}
.price{font-family:Z,serif;font-size:46px}
.price span{font-family:P;font-size:22px;color:#C9BBAE;display:block;margin-top:4px}
.rule{height:8px;background:#D9A441;width:120px;margin-bottom:26px}
.lede{font-size:27px;line-height:1.4;color:#C9BBAE;margin-top:22px;max-width:22ch}
"""


def room_card(r) -> str:
    lo = hotel.price_range(r)[0]
    size = f"{r.size_m2:.1f}".replace(".", ",")
    return f"""<!doctype html><meta charset="utf-8"><title>og</title>
<style>{CARD_CSS}</style>
<div class="main">
  <div><div class="rule" style="background:{r.hex_light}"></div>
    <div class="brand">Qırx Pəncərə · Şəki</div></div>
  <div><div class="kind" style="color:{r.hex_light}">{r.kind}</div>
    <h1{' class="small"' if len(r.name) > 8 else ''}>{r.name} otağı</h1>
    <div class="facts"><span>{size} m²</span><span>{r.sleeps} nəfər</span>
      <span>{r.steps} pillə</span></div></div>
  <div class="price">{money(lo)}<span>ən ucuz gecə · ƏDV və səhər yeməyi daxil</span></div>
</div>
<div class="side"><img src="../img/sebeke/{r.slug}.svg" alt=""></div>
"""


def cover() -> str:
    lo = min(hotel.price_range(r)[0] for r in hotel.ROOMS)
    return f"""<!doctype html><meta charset="utf-8"><title>og</title>
<style>{CARD_CSS}</style>
<div class="main">
  <div><div class="rule"></div><div class="brand">Şəki · Yuxarı Baş</div></div>
  <div><h1 class="small">Səkkiz otaq,<br>365 gecənin qiyməti açıq</h1>
    <div class="lede">Qiymətə ƏDV və səhər yeməyi daxil. Gizli əlavə yoxdur.</div></div>
  <div class="price">{money(lo)}<span>ən ucuz gecə</span></div>
</div>
<div class="side"><img src="../img/sebeke/hero.svg" alt=""></div>
"""


def shoot(html: str, out: Path) -> None:
    tmp = ROOT / "assets/css/_og.html"          # next to the fonts it references
    tmp.write_text(html, encoding="utf-8")
    try:
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
             "--blink-settings=preferredColorScheme=1",
             f"--window-size={W},{H}", "--default-background-color=2D2320",
             "--virtual-time-budget=3000", f"--screenshot={win(out)}", win(tmp)],
            capture_output=True, timeout=90)
    finally:
        tmp.unlink(missing_ok=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    shoot(cover(), ROOT / "assets/img/og-cover.png")
    for r in hotel.ROOMS:
        shoot(room_card(r), OUT / f"{r.slug}.png")
    made = [ROOT / "assets/img/og-cover.png"] + [OUT / f"{r.slug}.png" for r in hotel.ROOMS]
    missing = [p.name for p in made if not p.exists()]
    if missing:
        raise SystemExit(f"not rendered: {', '.join(missing)}")
    kb = sum(p.stat().st_size for p in made) / 1024
    print(f"{len(made)} share cards, {kb:.0f} KB")


if __name__ == "__main__":
    main()
