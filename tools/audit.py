#!/usr/bin/env python3
"""Runs our own client audit checklist against this site.

We tell hotels their H1 is a logo, their schema is half empty and their images
have no alt text. If the demo we show them fails the same checks, the report we
sell loses its standing. So the checklist runs here first.

    python3 tools/audit.py            # against the files in this folder
    python3 tools/audit.py --live     # against the deployed site

Exit code is the number of failures. `tools/audit_selftest.py` proves these
checks actually catch things.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hotel  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FAILS: list = []
CHECKS = 0


def fail(page: str, msg: str) -> None:
    FAILS.append(f"{page}: {msg}")


def check(fn):
    """Register a check so the summary can say how many ran."""
    def run(pages, css, assets):
        global CHECKS
        CHECKS += 1
        before = len(FAILS)
        fn(pages, css, assets)
        n = len(FAILS) - before
        print(f"  {'FAIL' if n else 'ok  '} {fn.__name__[6:].replace('_', ' '):28} "
              f"{('%d fault(s)' % n) if n else ''}")
    run.__name__ = fn.__name__
    return run


# --- the checks -------------------------------------------------------------

@check
def check_lang(pages, css, assets):
    for name, t in pages.items():
        if '<html lang="az">' not in t:
            fail(name, 'no <html lang="az"> — screen readers and translation get it wrong')


@check
def check_h1(pages, css, assets):
    for name, t in pages.items():
        h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", t, re.S)
        if len(h1s) != 1:
            fail(name, f"{len(h1s)} <h1> on the page, there must be exactly one")
            continue
        text = re.sub(r"<[^>]+>", "", h1s[0]).strip()
        if text.lower() in (hotel.BRAND.lower(), hotel.BRAND_FULL.lower()):
            fail(name, f"the <h1> is just the brand name ({text!r}), not the page subject")
        if len(text) < 8:
            fail(name, f"the <h1> is too short to say what the page is: {text!r}")


@check
def check_alt(pages, css, assets):
    for name, t in pages.items():
        for tag in re.findall(r"<img\b[^>]*>", t):
            m = re.search(r'alt="([^"]*)"', tag)
            if not m:
                fail(name, f"an <img> with no alt attribute at all: {tag[:70]}")
                continue
            if m.group(1).strip():
                if m.group(1).strip().lower() in ("şəkil", "image", "img", "foto"):
                    fail(name, f"a meaningless alt: {m.group(1)!r}")
                continue
            # An empty alt is only allowed on decoration, and the <img> itself has to
            # say so. Looking at nearby markup instead was too loose: an aria-hidden
            # icon in the button above the image let a real photo through.
            src = re.search(r'src="([^"]*)"', tag)
            if 'aria-hidden="true"' not in tag:
                fail(name, f"empty alt on an image that is not marked decorative: "
                           f"{src.group(1) if src else tag[:60]}")


@check
def check_titles_and_descriptions(pages, css, assets):
    seen_t, seen_d = {}, {}
    for name, t in pages.items():
        m = re.search(r"<title>(.*?)</title>", t, re.S)
        if not m or not m.group(1).strip():
            fail(name, "no <title>")
            continue
        title = m.group(1).strip()
        if len(title) < 15:
            fail(name, f"the <title> is only {len(title)} characters: {title!r}")
        if len(title) > 75:
            fail(name, f"the <title> is {len(title)} characters, it will be cut off")
        if title in seen_t:
            fail(name, f"the <title> is a copy of {seen_t[title]}'s")
        seen_t[title] = name

        d = re.search(r'<meta name="description" content="([^"]*)"', t)
        if not d or not d.group(1).strip():
            fail(name, "no meta description")
            continue
        desc = d.group(1).strip()
        if len(desc) < 60:
            fail(name, f"the meta description is only {len(desc)} characters")
        if desc in seen_d:
            fail(name, f"the meta description is a copy of {seen_d[desc]}'s")
        seen_d[desc] = name


@check
def check_og(pages, css, assets):
    need = ("og:title", "og:description", "og:url", "og:image", "og:type")
    for name, t in pages.items():
        for prop in need:
            if f'property="{prop}"' not in t:
                fail(name, f"no {prop} — a link pasted into WhatsApp shows a bare URL")
        m = re.search(r'<meta property="og:image" content="([^"]*)"', t)
        if m:
            rel = m.group(1).replace(hotel.SITE, "")
            if not (ROOT / rel).exists():
                fail(name, f"og:image points at a file that does not exist: {rel}")


@check
def check_jsonld(pages, css, assets):
    want = {"index.html": {"Hotel", "WebSite"},
            "restoran.html": {"Restaurant"},
            "qaydalar.html": {"FAQPage"},
            "otaqlar.html": {"ItemList"},
            "elaqe.html": {"Hotel"}}
    for name, t in pages.items():
        blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', t, re.S)
        if name != "404.html" and not blocks:
            fail(name, "no JSON-LD at all")
            continue
        types = set()
        for b in blocks:
            try:
                data = json.loads(b)
            except json.JSONDecodeError as ex:
                fail(name, f"JSON-LD does not parse: {ex}")
                continue
            types.add(data.get("@type"))
            _walk_ld(name, data)
        for need in want.get(name, set()):
            if need not in types:
                fail(name, f"JSON-LD is missing a {need} block")
        if name.startswith("otaq-"):
            if "HotelRoom" not in types:
                fail(name, "a room page with no HotelRoom in JSON-LD")
        if name.startswith("beledci-") and "Article" not in types:
            fail(name, "a guide page with no Article in JSON-LD")
        if name not in ("404.html",) and "BreadcrumbList" not in types \
                and name != "index.html":
            fail(name, "no BreadcrumbList — the crumb trail is on the page but not in schema")


def _walk_ld(name, node, path="") -> None:
    """Half-filled schema is the fault we charge clients to fix. Find it here."""
    if isinstance(node, dict):
        for k, v in node.items():
            if v is None or v == "" or v == [] or v == {}:
                fail(name, f"JSON-LD field is empty: {path}{k}")
            _walk_ld(name, v, f"{path}{k}.")
        t = node.get("@type")
        if t == "Offer" and "price" not in node:
            fail(name, f"an Offer with no price at {path}")
        if t == "AggregateRating":
            rv, rc = node.get("ratingValue"), node.get("reviewCount")
            if not rv or not rc:
                fail(name, f"an AggregateRating with no value or count at {path}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk_ld(name, v, f"{path}{i}.")


@check
def check_protocols(pages, css, assets):
    for name, t in pages.items():
        for href in re.findall(r'href="([^"]+)"', t):
            if "@" in href and not href.startswith(("mailto:", "http", "#")):
                fail(name, f"an e-mail address linked without mailto: {href}")
            if re.fullmatch(r"\+?[\d\s()-]{9,}", href):
                fail(name, f"a phone number linked without tel: {href}")
        if hotel.EMAIL in t and f'mailto:{hotel.EMAIL}' not in t:
            fail(name, "the e-mail address appears but is never a mailto: link")


@check
def check_internal_links(pages, css, assets):
    for name, t in pages.items():
        for href in re.findall(r'(?:href|src)="([^"]+)"', t):
            if href.startswith(("http", "mailto:", "tel:", "#", "data:")):
                continue
            target = href.split("#")[0].split("?")[0]
            if not target:
                continue
            if not (ROOT / target).exists():
                fail(name, f"link to something that is not there: {target}")


@check
def check_placeholders(pages, css, assets):
    bad = ("lorem ipsum", "todo", "fixme", "xxx", "your text here",
           "coming soon", "tbd", "placeholder", "[]", "{{")
    for name, t in pages.items():
        # Scan the words a visitor reads, not the markup: placeholder="" is a real
        # attribute and matching it was a false alarm on the reservation form.
        visible = re.sub(r"<[^>]+>", " ", re.sub(r"<script\b.*?</script>", "", t, flags=re.S))
        low = visible.lower()
        for b in bad:
            if b in low:
                fail(name, f"placeholder content left in the page: {b!r}")
        for href in re.findall(r'href="([^"]+)"', t):
            if "example.com" in href or "#TODO" in href:
                fail(name, f"a placeholder link left in the page: {href}")
        if re.search(r"<(p|h[1-4]|td|li)>\s*</(p|h[1-4]|td|li)>", t):
            fail(name, "an empty text element shipped")


@check
def check_sitemap_and_robots(pages, css, assets):
    sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    rb = (ROOT / "robots.txt").read_text(encoding="utf-8")
    if "Sitemap:" not in rb:
        fail("robots.txt", "does not point at the sitemap")
    listed = set(re.findall(r"<loc>(.*?)</loc>", sm))
    for name in pages:
        if name == "404.html":
            continue
        url = hotel.SITE + ("" if name == "index.html" else name)
        if url not in listed:
            fail("sitemap.xml", f"does not list {name}")
    for url in listed:
        rel = url.replace(hotel.SITE, "") or "index.html"
        if rel not in pages:
            fail("sitemap.xml", f"lists a page that does not exist: {rel}")


@check
def check_prices_match_the_model(pages, css, assets):
    """Every price printed anywhere has to be the price hotel.py computes.

    This is the whole promise of the site. Five places quote a number -- the card,
    the room page, the season matrix, the JSON-LD offer and the JS -- and this is
    what stops them drifting apart.
    """
    import datetime as dt
    for r in hotel.ROOMS:
        page = pages.get(f"otaq-{r.slug}.html")
        if not page:
            fail(f"otaq-{r.slug}.html", "the room has no page")
            continue
        # every day cell of the first published month
        y, m = hotel.calendar_months()[0]
        for day in range(1, 31):
            d = dt.date(y, m, day)
            want = hotel.price(r, d)
            cell = re.search(
                r'<span class="dd">%d</span><span class="pp">(\d+)</span>' % day, page)
            if not cell:
                fail(f"otaq-{r.slug}.html", f"{d:%d.%m.%Y} has no cell in the calendar")
            elif int(cell.group(1)) != want:
                fail(f"otaq-{r.slug}.html",
                     f"{d:%d.%m.%Y} prints {cell.group(1)} ₼ but the model says {want}")
        lo, hi = hotel.price_range(r)
        blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
        offers = [json.loads(b).get("offers") for b in blocks
                  if json.loads(b).get("@type") == "HotelRoom"]
        if not offers or offers[0].get("price") != lo:
            fail(f"otaq-{r.slug}.html",
                 f"the JSON-LD offer does not carry the lowest price ({lo})")
        card = pages["otaqlar.html"]
        if f"{lo} ₼" not in card and f"{lo:,}".replace(",", " ") + " ₼" not in card:
            fail("otaqlar.html", f"{r.name}'s lowest price ({lo}) is not on the card")


@check
def check_js_data_matches(pages, css, assets):
    """data.js has to describe the same seasons and bases as hotel.py."""
    js = (ROOT / "assets/js/data.js").read_text(encoding="utf-8")
    m = re.search(r"window\.QP = (\{.*\});", js, re.S)
    if not m:
        fail("data.js", "does not define window.QP")
        return
    data = json.loads(m.group(1))
    if data["start"] != hotel.SEASON_START.isoformat():
        fail("data.js", "the season window starts on a different day than hotel.py")
    if len(data["days"]) != 365:
        fail("data.js", f"the day map is {len(data['days'])} long, not 365")
    for slug, room in data["rooms"].items():
        if slug not in hotel.ROOM_BY_SLUG:
            fail("data.js", f"describes a room that does not exist: {slug}")
        elif room["base"] != hotel.ROOM_BY_SLUG[slug].base:
            fail("data.js", f"{slug} has base {room['base']}, hotel.py says "
                            f"{hotel.ROOM_BY_SLUG[slug].base}")
    for r in hotel.ROOMS:
        if r.slug not in data["rooms"]:
            fail("data.js", f"the reservation form cannot price {r.slug}")
    factors = sorted(s["factor"] for s in data["seasons"].values())
    if factors != sorted(s.factor for s in hotel.SEASONS):
        fail("data.js", "the season factors do not match hotel.py")


@check
def check_no_js(pages, css, assets):
    """With scripts gone, the substance has to still be there."""
    for name, t in pages.items():
        stripped = re.sub(r"<script\b.*?</script>", "", t, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", stripped)
        if len(text.split()) < 120:
            fail(name, "almost nothing left once the scripts are removed")
    for r in hotel.ROOMS:
        page = pages[f"otaq-{r.slug}.html"]
        if page.count('class="day ') < 360:
            fail(f"otaq-{r.slug}.html",
                 f"only {page.count('class=\"day ')} priced nights in the markup, "
                 "the calendar is being built by script")
    if "<noscript>" not in pages["rezervasiya.html"]:
        fail("rezervasiya.html", "no <noscript> fallback on the one page that needs script")
    for r in hotel.ROOMS:
        if f'href="otaq-{r.slug}.html"' not in pages["otaqlar.html"]:
            fail("otaqlar.html", f"{r.name} is not linked — the list needs script to build")


@check
def check_headings_in_order(pages, css, assets):
    for name, t in pages.items():
        levels = [int(x) for x in re.findall(r"<h([1-4])\b", t)]
        prev = 0
        for lv in levels:
            if prev and lv > prev + 1:
                fail(name, f"heading jumps from h{prev} to h{lv}")
            prev = lv


@check
def check_tables_are_readable(pages, css, assets):
    for name, t in pages.items():
        for tbl in re.findall(r"<table\b.*?</table>", t, re.S):
            if "<caption>" not in tbl:
                fail(name, "a table with no <caption>")
            ths = re.findall(r"<th\b([^>]*)>", tbl)
            for attrs in ths:
                if "scope=" not in attrs:
                    fail(name, "a <th> with no scope — the table is unreadable aloud")
                    break


@check
def check_links_have_text(pages, css, assets):
    for name, t in pages.items():
        for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", t, re.S):
            attrs, inner = m.group(1), m.group(2)
            if 'aria-hidden="true"' in attrs or "tabindex=\"-1\"" in attrs:
                continue
            text = re.sub(r"<[^>]+>", "", inner).strip()
            if not text and "aria-label" not in attrs:
                fail(name, f"a link with nothing to read: {m.group(0)[:80]}")


@check
def check_contrast(pages, css, assets):
    """Text colours against their backgrounds, in both schemes."""
    def tokens(block: str) -> dict:
        return dict(re.findall(r"--([a-z0-9-]+):\s*(#[0-9A-Fa-f]{6})", block))

    light = tokens(css.split("@media (prefers-color-scheme: dark)")[0])
    dark_block = css.split("@media (prefers-color-scheme: dark)")[1].split("\n}")[0]
    dark = {**light, **tokens(dark_block)}

    pairs = (("ink", "ground", 4.5), ("ink", "surface", 4.5), ("ink", "surface-2", 4.5),
             ("ink-2", "surface", 4.5), ("ink-2", "ground", 4.5),
             ("ink-3", "surface", 4.5), ("on-frame", "frame", 4.5),
             ("on-frame-2", "frame", 4.5), ("ink", "s-quiet", 4.5),
             ("ink", "s-spring", 4.5), ("ink", "s-summer", 4.5),
             ("ink", "s-autumn", 4.5), ("ink", "s-peak", 4.5),
             ("amber-ink", "surface", 4.5))
    for scheme, tok in (("light", light), ("dark", dark)):
        for fg, bg, need in pairs:
            if fg not in tok or bg not in tok:
                fail("style.css", f"{scheme}: token --{fg} or --{bg} is missing")
                continue
            c = hotel.contrast(tok[fg], tok[bg])
            if c < need:
                fail("style.css", f"{scheme}: --{fg} on --{bg} is {c:.2f}:1, "
                                  f"below {need}:1")


@check
def check_azerbaijani_text(pages, css, assets):
    """The letters that break on badly built sites: Ə ə Ğ ğ İ ı Ş ş and ₼."""
    for name, t in pages.items():
        if "�" in t:
            fail(name, "a replacement character — the encoding is broken somewhere")
        for wrong, right in (("Azerbaycan", "Azərbaycan"), ("Seki", "Şəki"),
                             ("otaq sayi", "otaq sayı")):
            if wrong in t:
                fail(name, f"{wrong!r} written without Azerbaijani letters ({right})")
    body = pages["index.html"]
    if "₼" not in body:
        fail("index.html", "no manat sign anywhere — prices are not in AZN")
    if 'charset="utf-8"' not in body:
        fail("index.html", "no utf-8 charset declared")


@check
def check_assets_exist(pages, css, assets):
    for r in hotel.ROOMS:
        for p in (f"assets/img/sebeke/{r.slug}.svg", f"assets/img/og/{r.slug}.png",
                  f"otaq-{r.slug}.html"):
            if not (ROOT / p).exists():
                fail("assets", f"missing for {r.name}: {p}")
    for p in ("assets/img/favicon.svg", "assets/img/og-cover.png",
              "assets/css/style.css", "assets/js/site.js", "assets/js/data.js",
              "robots.txt", "sitemap.xml"):
        if not (ROOT / p).exists():
            fail("assets", f"missing: {p}")
    for f in ("zillaslab-400-latin", "zillaslab-700-latinext",
              "plexsans-400-latinext", "plexsans-600-latin"):
        if not (ROOT / f"assets/fonts/{f}.woff2").exists():
            fail("assets", f"missing font: {f}.woff2")


ALL = [check_lang, check_h1, check_alt, check_titles_and_descriptions, check_og,
       check_jsonld, check_protocols, check_internal_links, check_placeholders,
       check_sitemap_and_robots, check_prices_match_the_model, check_js_data_matches,
       check_no_js, check_headings_in_order, check_tables_are_readable,
       check_links_have_text, check_contrast, check_azerbaijani_text,
       check_assets_exist]


def load_local() -> dict:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(ROOT.glob("*.html"))}


def load_live() -> dict:
    out = {}
    for p in sorted(ROOT.glob("*.html")):
        url = hotel.SITE + ("" if p.name == "index.html" else p.name)
        with urllib.request.urlopen(url, timeout=30) as r:
            out[p.name] = r.read().decode("utf-8")
        print(f"    fetched {p.name}")
    return out


def main() -> int:
    live = "--live" in sys.argv
    pages = load_live() if live else load_local()
    css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
    print(f"Auditing {len(pages)} pages ({'live' if live else 'local'})\n")
    for c in ALL:
        c(pages, css, None)
    print()
    if FAILS:
        for f in FAILS:
            print(f"  ✗ {f}")
        print(f"\n{len(FAILS)} fault(s) across {CHECKS} checks")
    else:
        print(f"{CHECKS} checks, no faults")
    return len(FAILS)


if __name__ == "__main__":
    raise SystemExit(main())
