#!/usr/bin/env python3
"""Screenshots pages at a true phone viewport.

Windows headless Chrome will not go below roughly 500px wide, so a --window-size
of 390 does not give you a 390px page. This nests the pages in 390px iframes on a
wide canvas instead, which does.

    python3 tools/phone_shot.py out.png index.html otaq-yaqut.html [--offset 2400]

The harness file lives in the site root for the length of the run, because that is
where the relative asset paths resolve from, and is deleted afterwards -- a stray
one gets picked up by audit.py, which is how this tool came to exist.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROME = os.environ.get(
    "CHROME", "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe")
HEIGHT = 2300


def win(p) -> str:
    r = subprocess.run(["wslpath", "-w", str(p)], capture_output=True, text=True)
    return r.stdout.strip() or str(p)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    offset = 0
    for a in sys.argv[1:]:
        if a.startswith("--offset="):
            offset = int(a.split("=", 1)[1])
    if len(args) < 2:
        print(__doc__)
        return 2
    out, pages = Path(args[0]), args[1:]

    frames = "".join(
        f'<div class="w"><iframe src="{p}" style="top:{-offset}px"></iframe></div>'
        for p in pages)
    harness = (
        '<!doctype html><meta charset="utf-8"><title>phone harness</title><style>'
        'body{margin:0;background:#8A8A8A;display:flex;gap:10px;align-items:flex-start}'
        f'.w{{width:390px;height:{HEIGHT}px;overflow:hidden;position:relative;'
        'background:#fff}'
        '.w iframe{position:absolute;left:0;width:390px;height:8000px;border:0}'
        '</style>' + frames)
    tmp = ROOT / "_phone_harness.html"
    tmp.write_text(harness, encoding="utf-8")
    try:
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
             "--blink-settings=preferredColorScheme=1",
             f"--window-size={len(pages) * 400 + 20},{HEIGHT}",
             "--default-background-color=8A8A8A", "--virtual-time-budget=5000",
             f"--screenshot={win(out)}", win(tmp)],
            capture_output=True, timeout=120)
    finally:
        tmp.unlink(missing_ok=True)
    print(f"{out} — {len(pages)} page(s) at 390px, offset {offset}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
