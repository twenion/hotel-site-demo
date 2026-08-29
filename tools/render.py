#!/usr/bin/env python3
"""The shell and every shared component.

One <head> builder, one header, one footer, one room card, one month grid, one
floor plan. A nav link exists in exactly one place rather than in twenty-four
files, which is how a dead internal link stops being possible.

This is a development aid, not a runtime dependency -- what ships is plain HTML.
"""

from __future__ import annotations

import calendar
import datetime as dt
import html
import json

import hotel
from hotel import BRAND, BRAND_FULL, EMAIL, PHONE_HUMAN, PHONE_LINK, SITE

e = html.escape


def money(v) -> str:
    return f"{int(round(v)):,}".replace(",", " ") + " ₼"


# --- Icons. Inline SVG, never emoji: emoji render differently on every platform
#     and screen readers say their unicode name out loud. --------------------
_ICONS = {
    "ruler": '<path d="M3 9h18v6H3z"/><path d="M7 9v3M11 9v4M15 9v3M19 9v4"/>',
    "person": '<circle cx="12" cy="7.5" r="3.2"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>',
    "stairs": '<path d="M3 20h4v-4h4v-4h4V8h5"/>',
    "bed": '<path d="M3 18v-9M3 13h18v5M21 18v-5a3 3 0 0 0-3-3h-7v3"/>'
           '<circle cx="7" cy="11.5" r="1.8"/>',
    "window": '<rect x="4" y="3" width="16" height="18" rx="1.5"/><path d="M12 3v18M4 12h16"/>',
    "bath": '<path d="M3 12h18v3a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4z"/><path d="M6 12V6a2 2 0 0 1 4 0"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "phone": '<path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 12l5 2v4a2 2 0 0 1-2.2 2A16.5 16.5 0 0 1 3 5.2 2 2 0 0 1 5 3z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6.5L12 13l8.5-6.5"/>',
    "pin": '<path d="M12 21s7-6.3 7-11a7 7 0 1 0-14 0c0 4.7 7 11 7 11z"/><circle cx="12" cy="10" r="2.6"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "arrow": '<path d="M4 12h15M13 6l6 6-6 6"/>',
    "check": '<path d="M4.5 12.5l5 5 10-11"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5.4l3.4 2"/>',
    "leaf": '<path d="M20 4C10 4 4 9 4 16c0 2 1 4 1 4s2-8 15-11c0 0-4 3-7 4-3.5 1.2-6 3-7 7 8 1 14-4 14-16z"/>',
    "chat": '<path d="M4 5h16v11H9l-5 4z"/>',
    "star": '<path d="M12 3.5l2.6 5.6 6 .8-4.4 4.2 1.1 6-5.3-2.9-5.3 2.9 1.1-6L3.4 9.9l6-.8z" '
            'fill="currentColor" stroke="none"/>',
    "star_half": '<path d="M12 3.5l2.6 5.6 6 .8-4.4 4.2 1.1 6-5.3-2.9-5.3 2.9 1.1-6L3.4 9.9l6-.8z"/>'
                 '<path d="M12 3.5V18.2l-5.3 2.9 1.1-6L3.4 9.9l6-.8z" fill="currentColor" stroke="none"/>',
    "plan": '<rect x="3" y="3" width="18" height="18" rx="1.5"/><path d="M3 14h8V3M11 14h10M11 9h4"/>',
}


def icon(name: str, cls: str = "i") -> str:
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true">{_ICONS[name]}</svg>')


def stars(n: float) -> str:
    full = int(n)
    half = (n - full) >= 0.4
    out = "".join(icon("star", "") for _ in range(full))
    if half:
        out += icon("star_half", "")
    return f'<span class="stars" aria-hidden="true">{out}</span>'


# --- Navigation. One list; every page's header and footer read from it. -----

NAV = (
    ("otaqlar.html", "Otaqlar"),
    ("qiymetler.html", "Qiymətlər"),
    ("restoran.html", "Restoran"),
    ("beledci.html", "Şəki bələdçisi"),
    ("haqqimizda.html", "Haqqımızda"),
    ("elaqe.html", "Əlaqə"),
)

FOOT_MORE = (
    ("sebeke.html", "Evin pəncərələri"),
    ("qaydalar.html", "Ev qaydaları"),
    ("mexfilik.html", "Məxfilik"),
)


def _brand_mark() -> str:
    from sebeke import favicon
    return favicon().replace('<svg xmlns="http://www.w3.org/2000/svg" ',
                             '<svg aria-hidden="true" ')


def head(title: str, desc: str, path: str, og: str = "assets/img/og-cover.png",
         jsonld: list | None = None, extra: str = "") -> str:
    url = SITE + ("" if path == "index.html" else path)
    blocks = "".join(
        f'<script type="application/ld+json">{json.dumps(b, ensure_ascii=False)}</script>'
        for b in (jsonld or []))
    return (
        '<!doctype html>\n<html lang="az">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{e(title)}</title>\n'
        f'<meta name="description" content="{e(desc)}">\n'
        f'<link rel="canonical" href="{e(url)}">\n'
        '<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">\n'
        '<meta name="theme-color" content="#2D2320">\n'
        f'<meta property="og:type" content="website">\n'
        f'<meta property="og:site_name" content="{e(BRAND_FULL)}">\n'
        f'<meta property="og:locale" content="az_AZ">\n'
        f'<meta property="og:title" content="{e(title)}">\n'
        f'<meta property="og:description" content="{e(desc)}">\n'
        f'<meta property="og:url" content="{e(url)}">\n'
        f'<meta property="og:image" content="{e(SITE + og)}">\n'
        f'<meta property="og:image:alt" content="{e(title)}">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:title" content="{e(title)}">\n'
        f'<meta name="twitter:description" content="{e(desc)}">\n'
        f'<meta name="twitter:image" content="{e(SITE + og)}">\n'
        '<link rel="preload" href="assets/fonts/zillaslab-700-latinext.woff2" as="font" '
        'type="font/woff2" crossorigin>\n'
        '<link rel="preload" href="assets/fonts/plexsans-400-latinext.woff2" as="font" '
        'type="font/woff2" crossorigin>\n'
        '<link rel="stylesheet" href="assets/css/style.css">\n'
        f'{extra}{blocks}\n</head>\n')


def header(current: str) -> str:
    links = "".join(
        f'<a href="{h}"{" aria-current=\"page\"" if h == current else ""}>{e(t)}</a>'
        for h, t in NAV)
    cur_res = ' aria-current="page"' if current == "rezervasiya.html" else ""
    return (
        '<a class="skip" href="#main">Əsas məzmuna keç</a>\n'
        '<header class="site-head">\n<div class="wrap head-in">\n'
        f'<a class="brand" href="index.html">{_brand_mark()}'
        f'<span>{e(BRAND)}<small>Şəki qonaq evi</small></span></a>\n'
        '<button class="nav-toggle" type="button" aria-expanded="false" '
        f'aria-controls="nav">{icon("menu")}<span>Menyu</span></button>\n'
        f'<nav class="nav" id="nav" aria-label="Əsas menyu">{links}'
        f'<a class="head-cta" href="rezervasiya.html"{cur_res}>Rezervasiya</a></nav>\n'
        '</div>\n</header>\n<div class="frieze" role="presentation"></div>\n')


def footer() -> str:
    nav_li = "".join(f'<li><a href="{h}">{e(t)}</a></li>' for h, t in NAV)
    more_li = "".join(f'<li><a href="{h}">{e(t)}</a></li>' for h, t in FOOT_MORE)
    rooms_li = "".join(
        f'<li><a href="otaq-{r.slug}.html">{e(r.name)}</a></li>' for r in hotel.ROOMS[:5])
    return (
        '<footer class="site-foot">\n<div class="wrap">\n<div class="foot-in">\n'
        f'<div><h2>{e(BRAND_FULL)}</h2><ul>'
        f'<li>{e(hotel.ADDRESS)}</li>'
        f'<li><a href="tel:{PHONE_LINK}">{e(PHONE_HUMAN)}</a></li>'
        f'<li><a href="mailto:{EMAIL}">{e(EMAIL)}</a></li>'
        f'<li>Yerləşmə {hotel.CHECKIN} · Çıxış {hotel.CHECKOUT}</li></ul></div>\n'
        f'<div><h2>Səhifələr</h2><ul>{nav_li}</ul></div>\n'
        f'<div><h2>Otaqlar</h2><ul>{rooms_li}'
        '<li><a href="otaqlar.html">Bütün otaqlar</a></li></ul></div>\n'
        f'<div><h2>Digər</h2><ul>{more_li}</ul></div>\n'
        '</div>\n<div class="foot-note">'
        '<p><strong>Bu sayt nümunədir.</strong> Qırx Pəncərə Qonaq Evi uydurma bir '
        'müəssisədir: belə bir otel yoxdur, göstərilən qiymətlər, otaqlar, rəylər və '
        'əlaqə məlumatları real deyil. Sayt heç bir ödəniş qəbul etmir və heç bir şəxsi '
        'məlumat toplamır — rezervasiya forması yalnız hazır mesaj mətni yaradır.</p>'
        f'<p>© 2026 · nümunə iş</p>'
        '</div>\n</div>\n</footer>\n')


def page(title: str, desc: str, path: str, body: str, og: str = "assets/img/og-cover.png",
         jsonld: list | None = None, extra: str = "") -> str:
    return (head(title, desc, path, og, jsonld, extra)
            + '<body>\n' + header(path) + f'<main id="main">\n{body}\n</main>\n'
            + footer()
            + '<script src="assets/js/site.js" defer></script>\n</body>\n</html>\n')


def crumbs(trail) -> str:
    """trail: ((href|None, label), ...) -- the last item is the current page."""
    items = []
    for href, label in trail:
        inner = f'<a href="{href}">{e(label)}</a>' if href else f'<span>{e(label)}</span>'
        items.append(f"<li>{inner}</li>")
    return ('<nav class="crumbs" aria-label="Səhifə yolu"><div class="wrap"><ol>'
            + "".join(items) + "</ol></div></nav>")


def breadcrumb_ld(trail) -> dict:
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": label,
                 **({"item": SITE + href} if href else {})}
                for i, (href, label) in enumerate(trail)]}


# --- Room components --------------------------------------------------------

def room_style(r) -> str:
    return f'--room:{r.hex_light};--room-ink:{r.hex_light}'


def room_facts(r) -> str:
    return (
        '<ul class="facts">'
        f'<li>{icon("ruler")}{r.size_m2:.1f} m²'.replace(".", ",") + '</li>'
        f'<li>{icon("person")}{r.sleeps} nəfər</li>'
        f'<li>{icon("stairs")}{r.steps} pillə</li>'
        f'<li>{icon("bed")}{e(r.bed_cm)} sm</li>'
        '</ul>')


def room_card(r, heading: str = "h3") -> str:
    lo, hi = hotel.price_range(r)
    return (
        f'<article class="card reveal" style="{room_style(r)}">'
        '<div class="card-spine"></div>'
        f'<a class="card-art" href="otaq-{r.slug}.html" tabindex="-1" aria-hidden="true">'
        f'<img src="assets/img/sebeke/{r.slug}.svg" width="720" height="480" loading="lazy" '
        f'alt="" aria-hidden="true"></a>'
        '<div class="card-body">'
        f'<{heading}><a href="otaq-{r.slug}.html">{e(r.name)} otağı</a></{heading}>'
        f'<p class="card-kind">{e(r.kind)}</p>'
        f'{room_facts(r)}'
        f'<p>{e(r.lede)}</p>'
        '<div class="card-foot">'
        f'<p class="price mb-0">{money(lo)}<small>ən ucuz gecə · {money(hi)}-dək</small></p>'
        f'<a class="btn btn-quiet" href="otaq-{r.slug}.html">Bax{icon("arrow")}</a>'
        '</div></div></article>')


# --- The open calendar ------------------------------------------------------

SEASON_TONE = {"quiet": "s-quiet", "spring": "s-spring", "summer": "s-summer",
               "autumn": "s-autumn", "peak": "s-peak"}


def month_table(room, year: int, month: int) -> str:
    """One month of one room's real nightly price. A table, with numbers in it."""
    cal = calendar.Calendar(firstweekday=0)
    head_cells = "".join(f'<th scope="col"><abbr title="{full}">{short}</abbr></th>'
                         for short, full in zip(
                             hotel.WEEKDAYS_AZ,
                             ("bazar ertəsi", "çərşənbə axşamı", "çərşənbə",
                              "cümə axşamı", "cümə", "şənbə", "bazar")))
    rows = []
    for week in cal.monthdayscalendar(year, month):
        cells = []
        for d in week:
            if d == 0:
                cells.append('<td><div class="day-empty"></div></td>')
                continue
            day = dt.date(year, month, d)
            s = hotel.season_for(day)
            p = hotel.price(room, day)
            cells.append(
                f'<td><div class="day {SEASON_TONE[s.tone]}">'
                f'<span class="dd">{d}</span>'
                f'<span class="pp">{p}</span></div></td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    name = hotel.MONTHS_AZ_CAP[month - 1]
    return (
        '<div class="month"><table>'
        f'<caption>{name} {year}</caption>'
        f'<thead><tr>{head_cells}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>')


def season_legend() -> str:
    seen, items = set(), []
    for s in hotel.SEASONS:
        if s.tone in seen:
            continue
        seen.add(s.tone)
        names = ", ".join(x.name for x in hotel.SEASONS if x.tone == s.tone)
        items.append(f'<li><span class="swatch {SEASON_TONE[s.tone]}"></span>{e(names)}</li>')
    return f'<ul class="cal-legend">{"".join(items)}</ul>'


def room_calendar(room) -> str:
    months = "".join(month_table(room, y, m) for y, m in hotel.calendar_months())
    return (
        f'{season_legend()}'
        f'<div class="cal-grid">{months}</div>')


# --- The floor plan ---------------------------------------------------------

def plan_svg(r) -> str:
    """The room drawn to scale from the same centimetres the passport quotes."""
    p = r.plan
    pad = 46
    # A balcony hangs outside the wall, so the drawing is measured from every
    # shape rather than from the room -- otherwise its label gets clipped.
    xs = [0, p.w] + [x for x, y, w, h, _ in p.extras] + [x + w for x, y, w, h, _ in p.extras]
    ys = [0, p.h] + [y for x, y, w, h, _ in p.extras] + [y + h for x, y, w, h, _ in p.extras]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    scale = 560 / max(x1 - x0, y1 - y0)
    W, H = p.w * scale, p.h * scale
    off_x, off_y = -x0 * scale, -y0 * scale
    pad_x, pad_y = pad + off_x, pad + off_y
    vb_w = (x1 - x0) * scale + pad * 2
    vb_h = (y1 - y0) * scale + pad * 2

    def rect(x, y, w, h, **kw):
        a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
        return (f'<rect x="{pad_x + x * scale:.1f}" y="{pad_y + y * scale:.1f}" '
                f'width="{w * scale:.1f}" height="{h * scale:.1f}" {a}/>')

    def label(x, y, text, size=13, anchor="middle", cls="pl-lab"):
        return (f'<text x="{pad_x + x * scale:.1f}" y="{pad_y + y * scale:.1f}" '
                f'font-size="{size}" text-anchor="{anchor}" class="{cls}">{e(text)}</text>')

    parts = [rect(0, 0, p.w, p.h, fill="var(--surface-2)", stroke="var(--ink)",
                  stroke_width="3")]
    if p.bath:
        bx, by, bw, bh = p.bath
        parts.append(rect(bx, by, bw, bh, fill="var(--surface)", stroke="var(--ink-3)",
                          stroke_width="1.6"))
        parts.append(label(bx + bw / 2, by + bh / 2 + 5, "vanna otağı", 12.5))
    for x, y, w, h, name in p.extras:
        parts.append(rect(x, y, w, h, fill="none", stroke="var(--ink-3)",
                          stroke_width="1.4", stroke_dasharray="5 4"))
        parts.append(label(x + w / 2, y + h / 2 + 5, name, 12.5))
    for bx, by, bw, bh in p.bed:
        parts.append(rect(bx, by, bw, bh, fill=r.hex_light, opacity=".92", rx="3"))
        parts.append(rect(bx + 6, by + 6, bw - 12, bh * 0.22, fill="var(--surface)",
                          opacity=".85", rx="2"))
        parts.append(f'<text x="{pad_x + (bx + bw / 2) * scale:.1f}" '
                     f'y="{pad_y + (by + bh * 0.62) * scale:.1f}" font-size="12.5" '
                     f'text-anchor="middle" fill="#fff" class="pl-bed">'
                     f'{bw}×{bh}</text>')
    for x, y, w, h in p.windows:
        parts.append(rect(x, y, w, h, fill="#D9A441"))
    if p.door:
        dx, dy, dw, dh = p.door
        parts.append(rect(dx, dy, dw, dh, fill="var(--ground)"))
        cx = dx + (dw if dx < p.w / 2 else 0)
        arc_r = max(dh, dw)
        parts.append(
            f'<path d="M {pad_x + cx * scale:.1f} {pad_y + dy * scale:.1f} '
            f'a {arc_r * scale:.1f} {arc_r * scale:.1f} 0 0 1 '
            f'{arc_r * scale * (1 if dx < p.w / 2 else -1):.1f} {arc_r * scale:.1f}" '
            'fill="none" stroke="var(--ink-3)" stroke-width="1.3" stroke-dasharray="4 4"/>')

    # Dimensions along the top and the left.
    parts.append(f'<line x1="{pad_x:.1f}" y1="{pad_y - 16:.1f}" x2="{pad_x + W:.1f}" '
                 f'y2="{pad_y - 16:.1f}" stroke="var(--ink-3)" stroke-width="1.2"/>')
    parts.append(label(p.w / 2, -24 / scale, f"{p.w / 100:.2f} m".replace(".", ","), 13))
    parts.append(f'<line x1="{pad_x - 16:.1f}" y1="{pad_y:.1f}" x2="{pad_x - 16:.1f}" '
                 f'y2="{pad_y + H:.1f}" stroke="var(--ink-3)" stroke-width="1.2"/>')
    parts.append(f'<text x="{pad_x - 22:.1f}" y="{pad_y + H / 2:.1f}" font-size="13" '
                 f'text-anchor="middle" class="pl-lab" transform="rotate(-90 '
                 f'{pad_x - 22:.1f} {pad_y + H / 2:.1f})">'
                 f'{e(f"{p.h / 100:.2f} m".replace(".", ","))}</text>')

    return (
        f'<svg viewBox="0 0 {vb_w:.0f} {vb_h:.0f}" role="img" '
        f'aria-label="{e(r.name)} otağının miqyaslı planı: {p.w / 100:.2f} × '
        f'{p.h / 100:.2f} metr, çarpayı {e(r.bed_cm)} sm, vanna otağı və pəncərə yerləri">'
        '<style>.pl-lab{fill:var(--ink-2);font-family:"Plex",sans-serif}'
        '.pl-bed{font-family:"Plex",sans-serif;font-weight:600}</style>'
        + "".join(parts) + "</svg>")


# --- Shared JSON-LD ---------------------------------------------------------

def hotel_ld() -> dict:
    lo = min(hotel.price_range(r)[0] for r in hotel.ROOMS)
    hi = max(hotel.price_range(r)[1] for r in hotel.ROOMS)
    return {
        "@context": "https://schema.org", "@type": "Hotel",
        "@id": SITE + "#hotel", "name": BRAND_FULL, "url": SITE,
        "description": ("Şəkinin Yuxarı Baş məhəlləsində səkkiz otaqlı qonaq evi. "
                        "Bütün otaqların bir illik gecəlik qiyməti saytda açıq "
                        "göstərilir."),
        "image": SITE + "assets/img/og-cover.png",
        "telephone": PHONE_HUMAN, "email": EMAIL,
        "address": {"@type": "PostalAddress", "streetAddress": "M. F. Axundzadə küçəsi 41",
                    "addressLocality": "Şəki", "postalCode": "AZ5500",
                    "addressCountry": "AZ"},
        "geo": {"@type": "GeoCoordinates", "latitude": hotel.LAT, "longitude": hotel.LON},
        "numberOfRooms": len(hotel.ROOMS),
        "checkinTime": hotel.CHECKIN, "checkoutTime": hotel.CHECKOUT,
        "priceRange": f"{lo}–{hi} ₼",
        "currenciesAccepted": "AZN", "paymentAccepted": "Nağd, kart",
        "petsAllowed": True,
        "amenityFeature": [
            {"@type": "LocationFeatureSpecification", "name": n, "value": True}
            for n in ("Pulsuz Wi-Fi", "Səhər yeməyi qiymətə daxil", "Həyətdə parklanma",
                      "Mərkəzi qızdırma", "Restoran")],
        "aggregateRating": {"@type": "AggregateRating", "ratingValue": hotel.RATING,
                            "reviewCount": len(hotel.REVIEWS), "bestRating": 5,
                            "worstRating": 1},
    }


def website_ld() -> dict:
    return {"@context": "https://schema.org", "@type": "WebSite", "@id": SITE + "#site",
            "url": SITE, "name": BRAND_FULL, "inLanguage": "az",
            "publisher": {"@id": SITE + "#hotel"}}


def review_ld(rv) -> dict:
    return {"@type": "Review",
            "author": {"@type": "Person", "name": rv.author},
            "datePublished": dt.datetime.strptime(rv.date, "%d.%m.%Y").strftime("%Y-%m-%d"),
            "reviewRating": {"@type": "Rating", "ratingValue": rv.stars,
                             "bestRating": 5, "worstRating": 1},
            "reviewBody": rv.text}
