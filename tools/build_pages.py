#!/usr/bin/env python3
"""Generates every page of the site from hotel.py through render.py.

    python3 tools/build_pages.py

Nothing here runs in the browser. The output is plain HTML that works from a
folder with no server, no build step and no network.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import hotel
import render as R
from hotel import (ARTICLES, BRAND, BRAND_FULL, EMAIL, FAQ, MENU, MENU_NOTE,
                   PHONE_HUMAN, PHONE_LINK, REVIEWS, ROOMS, SITE,
                   WHATSAPP_HUMAN, WHATSAPP_LINK)
from render import e, icon, money

ROOT = Path(__file__).resolve().parent.parent
PAGES: dict = {}


def w(path: str, text: str) -> None:
    PAGES[path] = text
    (ROOT / path).write_text(text, encoding="utf-8")


def sec(inner: str, cls: str = "sec") -> str:
    return f'<section class="{cls}"><div class="wrap">{inner}</div></section>'


def sec_head(eyebrow: str, title: str, para: str = "", level: str = "h2") -> str:
    p = f"<p>{para}</p>" if para else ""
    return (f'<div class="sec-head"><p class="eyebrow">{e(eyebrow)}</p>'
            f'<{level}>{title}</{level}>{p}</div>')


def cta_band() -> str:
    return sec(
        '<div class="panel" style="display:flex;flex-wrap:wrap;gap:24px;'
        'align-items:center;justify-content:space-between">'
        '<div style="max-width:52ch"><h2>Tarixi seçin, qiymət artıq ekrandadır</h2>'
        '<p class="mb-0" style="color:var(--ink-2);margin-top:10px">Rezervasiya forması '
        'gecə sayını və məbləği özü hesablayır, sonra WhatsApp və ya e-poçt üçün hazır '
        'mesaj mətni verir. Ödəniş yerində, nağd və ya kartla.</p></div>'
        f'<a class="btn btn-amber" href="rezervasiya.html">Rezervasiya et{icon("arrow")}</a>'
        '</div>', "sec")


# --- index ------------------------------------------------------------------

def build_index() -> None:
    lo = min(hotel.price_range(r)[0] for r in ROOMS)
    hero = (
        '<section class="hero"><div class="wrap hero-in">'
        '<div>'
        '<p class="eyebrow" style="color:var(--on-frame-2)">Şəki · Yuxarı Baş</p>'
        '<h1>Səkkiz otaq, 365 gecənin qiyməti açıq</h1>'
        '<p class="hero-lede">Xan Sarayından 900 metr aralıda, 1920-ci illərin '
        'evində. Hansı gecənin nə qədər olduğunu öyrənmək üçün heç kimə yazmağa '
        'ehtiyac yoxdur — bütün il təqvimdə görünür.</p>'
        '<div class="hero-acts">'
        f'<a class="btn btn-amber" href="otaqlar.html">Otaqlara bax{icon("arrow")}</a>'
        f'<a class="btn btn-quiet" href="qiymetler.html">{icon("calendar")}Qiymət təqvimi</a>'
        '</div>'
        '<dl class="hero-facts">'
        f'<div><dt>Otaq sayı</dt><dd>{len(ROOMS)}</dd></div>'
        f'<div><dt>Ən ucuz gecə</dt><dd>{money(lo)}</dd></div>'
        '<div><dt>Xan Sarayına</dt><dd>900 m</dd></div>'
        f'<div><dt>Qonaq rəyi</dt><dd>{str(hotel.RATING).replace(".", ",")} / 5</dd></div>'
        '</dl></div>'
        '<div class="hero-art"><img src="assets/img/sebeke/hero.svg" width="1120" '
        'height="840" alt="Evin şəbəkə pəncərəsindən bir hissə: qoz ağacından '
        'səkkizguşəli ulduz naxışı və qırmızı, çəhrayı, kəhrəba rəngli şüşələr"></div>'
        '</div></section>')

    why = sec(
        sec_head("Bizim qayda", "Qiyməti niyə gizlətmirik",
                 "Azərbaycanda otel saytlarının çoxunda qiymət yazılmır: “əlaqə saxlayın” "
                 "deyilir. Qonaq yazmır — gedib başqa yerdən baxır və otel həmin qonağa "
                 "görə komissiya ödəyir. Biz bunu etmirik və səbəbini gizlətmirik.")
        + '<div class="grid g-3">'
        '<article class="panel reveal"><h3>Ekranda gördüyünüz rəqəm</h3>'
        '<p class="mb-0" style="color:var(--ink-2)">Qiymətə ƏDV və səhər yeməyi daxildir. '
        'Şəhər vergisi, xidmət haqqı, “təmizlik haqqı” kimi əlavələr yoxdur. Qapıda '
        'ödəyəcəyiniz məbləğ təqvimdəki məbləğdir.</p></article>'
        '<article class="panel reveal"><h3>Mövsümün səbəbi yazılıb</h3>'
        '<p class="mb-0" style="color:var(--ink-2)">Qiymət ilin altı mövsümündə dəyişir. '
        'Hər mövsümün nə vaxt başladığı və niyə bahalaşdığı '
        '<a href="qiymetler.html">qiymət səhifəsində</a> açıq yazılıb.</p></article>'
        '<article class="panel reveal"><h3>Otağın ölçüsü də açıq</h3>'
        '<p class="mb-0" style="color:var(--ink-2)">Hər otağın kvadratmetri, qapısına '
        'neçə pillə olduğu, çarpayısının santimetri və miqyaslı planı səhifəsindədir. '
        'Gəlmədən bilmək lazım olan şeylər.</p></article>'
        '</div>', "sec sec-alt")

    rooms = sec(
        sec_head("Otaqlar", "Səkkiz otaq, hər biri öz şəbəkəsi ilə",
                 "Otaqlar evin pəncərələrindəki şüşə rənglərinin adını daşıyır. "
                 "Kartdakı rəng həmin otağın rəngidir — təqvimdə, planda və "
                 "səhifəsində eyni rəngi görəcəksiniz.")
        + '<div class="grid g-3">'
        + "".join(R.room_card(r) for r in ROOMS)
        + '</div>')

    rest = sec(
        '<div class="grid g-2" style="align-items:center">'
        '<div>' + sec_head("Restoran", "Piti üç saat bişir, ona görə günorta 12-yə "
                           "qədər sifariş olunur",
                           "Səhər yeməyi otaq qiymətinə daxildir və həyətdə verilir. "
                           "Axşam yeməyi menyusu kiçikdir: beş əsas yemək, üçü Şəki "
                           "mətbəxindən.")
        + f'<a class="btn btn-quiet" href="restoran.html">Menyuya bax{icon("arrow")}</a></div>'
        '<figure class="plan-fig" style="margin:0"><img '
        'src="assets/img/sebeke/kehreba.svg" width="720" height="480" loading="lazy" '
        'alt="Kəhrəba otağının şəbəkəsi: kəhrəba və narıncı şüşədən altıbucaqlı naxış">'
        '<figcaption>Kəhrəba otağının pəncərəsi — altıbucaqlı naxış, '
        'kəhrəba şüşə.</figcaption></figure>'
        '</div>', "sec sec-alt")

    guide = sec(
        sec_head("Şəki bələdçisi", "Gəlməzdən əvvəl oxumağa dəyən dörd yazı",
                 "Şəhəri satmaq üçün deyil — hansı saatda getmək, nəyə baxmaq və "
                 "nəyi almamaq lazım olduğunu yazdıq.")
        + '<div class="grid g-3">'
        + "".join(
            f'<article class="card reveal"><div class="card-spine" '
            f'style="--room:{ROOMS[i].hex_light}"></div><div class="card-body">'
            f'<h3><a href="beledci-{a.slug}.html">{e(a.title)}</a></h3>'
            f'<p>{e(a.lede)}</p>'
            f'<div class="card-foot"><p class="mb-0" style="font-size:14.5px;'
            f'color:var(--ink-3)">{a.minutes} dəqiqəlik oxu</p>'
            f'<a class="btn btn-quiet" href="beledci-{a.slug}.html">Oxu{icon("arrow")}</a>'
            f'</div></div></article>'
            for i, a in enumerate(ARTICLES[:3]))
        + '</div>')

    top = sorted(REVIEWS, key=lambda r: r.date.split(".")[::-1], reverse=True)[:3]
    revs = sec(
        '<div class="sec-head"><p class="eyebrow">Qonaq rəyləri</p>'
        f'<div class="rating-big"><strong>{str(hotel.RATING).replace(".", ",")}</strong>'
        f'<span>{R.stars(hotel.RATING)} {len(REVIEWS)} rəy əsasında</span></div></div>'
        '<div class="grid g-3">'
        + "".join(
            f'<article class="review reveal">{R.stars(rv.stars)}'
            f'<blockquote>{e(rv.text)}</blockquote>'
            f'<footer>{e(rv.author)}, {e(rv.city)} · '
            f'<a href="otaq-{rv.room}.html">{e(hotel.ROOM_BY_SLUG[rv.room].name)}</a> · '
            f'{e(rv.date)}</footer></article>' for rv in top)
        + '</div>', "sec sec-alt")

    body = hero + why + rooms + rest + guide + revs + cta_band()
    w("index.html", R.page(
        f"{BRAND_FULL} — Şəkidə səkkiz otaq, qiymətlər açıq",
        "Şəkinin Yuxarı Baş məhəlləsində səkkiz otaqlı qonaq evi. Bütün otaqların "
        "bir illik gecəlik qiyməti təqvimdə açıq göstərilir; qiymətə ƏDV və səhər "
        "yeməyi daxildir.",
        "index.html", body,
        jsonld=[R.hotel_ld(), R.website_ld()]))


# --- rooms ------------------------------------------------------------------

def build_rooms_index() -> None:
    head_cells = ("Otaq", "Növ", "Sahə", "Nəfər", "Mərtəbə", "Pillə", "Çarpayı",
                  "Vanna otağı", "Ən ucuz gecə")
    rows = "".join(
        f'<tr style="{R.room_style(r)}">'
        f'<th scope="row"><span class="room-dot"></span>'
        f'<a href="otaq-{r.slug}.html">{e(r.name)}</a></th>'
        f'<td style="text-align:start">{e(r.kind)}</td>'
        f'<td>{str(r.size_m2).replace(".", ",")} m²</td>'
        f'<td>{r.sleeps}</td>'
        f'<td>{"həyət" if r.floor == 0 else r.floor}</td>'
        f'<td>{r.steps}</td>'
        f'<td>{e(r.bed_cm)}</td>'
        f'<td style="text-align:start">{e(r.bathroom)}</td>'
        f'<td>{money(hotel.price_range(r)[0])}</td></tr>' for r in ROOMS)
    table = (
        '<p class="scroll-hint">Cədvəl enlidir — barmağınızla yana sürüşdürün.</p>'
        '<div class="matrix-scroll"><table class="matrix">'
        '<caption>Səkkiz otaq yan-yana — mərtəbə, pillə sayı və çarpayı ölçüsü '
        'daxil olmaqla</caption><thead><tr>'
        + "".join(f'<th scope="col"{" style=\"text-align:start\"" if i < 2 or i == 7 else ""}>'
                  f'{e(h)}</th>' for i, h in enumerate(head_cells))
        + f'</tr></thead><tbody>{rows}</tbody></table></div>')

    body = (
        R.crumbs(((("index.html"), "Ana səhifə"), (None, "Otaqlar")))
        + sec(
            sec_head("Otaqlar", "Səkkiz otaq və hər birinin dəqiq ölçüsü",
                     "Otaqlar bir-birindən yalnız qiymətlə deyil, mərtəbə, pillə sayı "
                     "və çarpayı ölçüsü ilə də fərqlənir. Aşağıdakı cədvəl hamısını "
                     "yan-yana qoyur; sonra hər otağın öz səhifəsində miqyaslı plan var.",
                     "h1")
            + table
            + '<div class="grid g-3" style="margin-top:32px">'
            + "".join(R.room_card(r, "h2") for r in ROOMS) + "</div>"))

    trail = (("index.html", "Ana səhifə"), (None, "Otaqlar"))
    item_list = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "Otaqlar", "numberOfItems": len(ROOMS),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "url": SITE + f"otaq-{r.slug}.html", "name": f"{r.name} otağı"}
            for i, r in enumerate(ROOMS)]}
    w("otaqlar.html", R.page(
        f"Otaqlar — sahə, mərtəbə və pillə sayı ilə | {BRAND}",
        "Səkkiz otağın hamısı yan-yana: kvadratmetr, neçə nəfərlik, mərtəbə, qapıya "
        "neçə pillə, çarpayı ölçüsü və ən ucuz gecə qiyməti.",
        "otaqlar.html", body,
        jsonld=[item_list, R.breadcrumb_ld(trail)]))


def build_room(r) -> None:
    lo, hi = hotel.price_range(r)
    passport_rows = (
        ("Otağın növü", r.kind),
        ("Döşəmə sahəsi", f"{str(r.size_m2).replace('.', ',')} m²"),
        ("Neçə nəfərlik", f"{r.sleeps} nəfər"),
        ("Mərtəbə", "həyət səviyyəsi" if r.floor == 0 else f"{r.floor}-ci mərtəbə"),
        ("Qapıya qədər pillə", f"{r.steps} pillə, lift yoxdur"),
        ("Çarpayı", f"{r.bed_cm} sm"),
        ("Pəncərə", r.aspect),
        ("Vanna otağı", r.bathroom),
        ("Şəbəkə naxışı", {"ulduz8": "səkkizguşəli ulduz və xaç",
                           "sekkizguse": "səkkizbucaq və kvadrat",
                           "carpaz": "çarpaz romb",
                           "altibucaq": "altıbucaq"}[r.pattern]),
        ("Ən ucuz gecə", f"{money(lo)} (sakit mövsüm)"),
        ("Ən bahalı gecə", f"{money(hi)} (Yeni il)"),
    )
    passport = (
        '<div class="passport"><table>'
        f'<caption>{e(r.name)} otağının pasportu</caption><tbody>'
        + "".join(f'<tr><th scope="row">{e(k)}</th><td>{e(v)}</td></tr>'
                  for k, v in passport_rows)
        + '</tbody></table></div>')

    dims = (f"{r.plan.w / 100:.2f} × {r.plan.h / 100:.2f}").replace(".", ",")
    plan = (
        '<figure class="plan-fig">' + R.plan_svg(r) +
        '<figcaption>Plan miqyaslıdır və pasportdakı eyni santimetrlərdən çəkilib: '
        f'{dims} m. Sarı xətlər pəncərə, kəsik xətlər mebel yeridir.'
        '</figcaption></figure>')

    room_revs = [rv for rv in REVIEWS if rv.room == r.slug]
    revs_html = "".join(
        f'<article class="review">{R.stars(rv.stars)}'
        f'<blockquote>{e(rv.text)}</blockquote>'
        f'<footer>{e(rv.author)}, {e(rv.city)} · {e(rv.date)}</footer></article>'
        for rv in room_revs)

    body = (
        R.crumbs((("index.html", "Ana səhifə"), ("otaqlar.html", "Otaqlar"),
                  (None, f"{r.name} otağı")))
        + f'<section class="sec" style="{R.room_style(r)}"><div class="wrap">'
        '<div class="grid g-2" style="align-items:start">'
        '<div>'
        f'<p class="eyebrow" style="color:{r.hex_light}">{e(r.kind)}</p>'
        f'<h1>{e(r.name)} otağı</h1>'
        f'<p class="lede" style="margin-top:14px">{e(r.lede)}</p>'
        + "".join(f"<p>{e(p)}</p>" for p in r.body)
        + '<ul class="facts" style="margin-top:20px">'
        + "".join(f'<li>{icon("check")}{e(f)}</li>' for f in r.features)
        + '</ul>'
        '<div class="card-foot" style="border:0;padding:0;margin-top:24px">'
        f'<p class="price mb-0">{money(lo)}<small>ən ucuz gecə · '
        f'ən bahası {money(hi)}</small></p>'
        f'<a class="btn btn-main" href="rezervasiya.html?otaq={r.slug}">'
        f'Bu otağı seç{icon("arrow")}</a></div>'
        '</div>'
        '<figure class="plan-fig" style="padding:0;overflow:hidden">'
        f'<img src="assets/img/sebeke/{r.slug}.svg" width="720" height="480" '
        f'alt="{e(r.name)} otağının şəbəkə pəncərəsi: '
        f'{e(r.glass)} rəngli şüşə və qoz ağacından naxış">'
        '</figure></div></div></section>'
        + sec('<div class="grid g-2" style="align-items:start">'
              f'{passport}{plan}</div>', "sec sec-alt")
        + sec(sec_head("Açıq təqvim", f"{e(r.name)} otağının bir illik gecəlik qiyməti",
                       "Hər xanadakı rəqəm həmin gecə üçün ödəyəcəyiniz məbləğdir — "
                       "ƏDV və səhər yeməyi daxil. Rəng mövsümü göstərir. "
                       f"Novruz və Yeni il tarixlərində minimum iki gecə."
                       )
              + R.room_calendar(r))
        + (sec(sec_head("Rəylər", f"{e(r.name)} otağında qalanlar")
               + f'<div class="grid g-3">{revs_html}</div>', "sec sec-alt")
           if revs_html else "")
        + cta_band())

    trail = (("index.html", "Ana səhifə"), ("otaqlar.html", "Otaqlar"),
             (None, f"{r.name} otağı"))
    ld = {
        "@context": "https://schema.org", "@type": "HotelRoom",
        "name": f"{r.name} otağı", "url": SITE + f"otaq-{r.slug}.html",
        "description": r.lede,
        "image": SITE + f"assets/img/og/{r.slug}.png",
        "bed": {"@type": "BedDetails", "typeOfBed": r.bed_cm.split(" və ")[0],
                "numberOfBeds": len(r.plan.bed)},
        "occupancy": {"@type": "QuantitativeValue", "maxValue": r.sleeps, "unitText": "nəfər"},
        "floorSize": {"@type": "QuantitativeValue", "value": r.size_m2, "unitCode": "MTK"},
        "amenityFeature": [{"@type": "LocationFeatureSpecification", "name": f,
                            "value": True} for f in r.features],
        "containedInPlace": {"@id": SITE + "#hotel"},
        "offers": {"@type": "Offer", "price": lo, "priceCurrency": "AZN",
                   "availability": "https://schema.org/InStock",
                   "priceValidUntil": hotel.SEASON_END.isoformat(),
                   "url": SITE + f"rezervasiya.html?otaq={r.slug}",
                   "priceSpecification": {
                       "@type": "PriceSpecification", "minPrice": lo, "maxPrice": hi,
                       "priceCurrency": "AZN", "valueAddedTaxIncluded": True}},
        "review": [R.review_ld(rv) for rv in room_revs],
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": round(sum(x.stars for x in room_revs) / len(room_revs), 1),
            "reviewCount": len(room_revs), "bestRating": 5, "worstRating": 1},
    }
    w(f"otaq-{r.slug}.html", R.page(
        f"{r.name} otağı — {r.kind.lower()}, {str(r.size_m2).replace('.', ',')} m² | {BRAND}",
        f"{r.lede} {str(r.size_m2).replace('.', ',')} m², {r.bed_cm} sm çarpayı, "
        f"{r.steps} pillə. Bir illik gecəlik qiymət təqvimi səhifədədir.",
        f"otaq-{r.slug}.html", body, og=f"assets/img/og/{r.slug}.png",
        jsonld=[ld, R.breadcrumb_ld(trail)]))


# --- prices -----------------------------------------------------------------

def build_prices() -> None:
    cols = "".join(
        f'<th scope="col">{e(s.name)}<br><span style="font-weight:400;color:var(--ink-3);'
        f'font-size:12.5px">×{str(s.factor).replace(".", ",")}</span></th>'
        for s in hotel.SEASONS)
    rows = ""
    for r in ROOMS:
        cells = ""
        for s in hotel.SEASONS:
            day = next(d for d in hotel.season_days() if hotel.season_for(d).key == s.key)
            cells += f"<td>{money(hotel.price(r, day))}</td>"
        rows += (f'<tr style="{R.room_style(r)}"><th scope="row">'
                 f'<span class="room-dot"></span>'
                 f'<a href="otaq-{r.slug}.html">{e(r.name)}</a></th>{cells}</tr>')
    matrix = (
        '<p class="scroll-hint">Cədvəl enlidir — barmağınızla yana sürüşdürün.</p>'
        '<div class="matrix-scroll"><table class="matrix">'
        '<caption>Gecəlik qiymət — otaq və mövsüm üzrə, ƏDV və səhər yeməyi '
        'daxil</caption>'
        f'<thead><tr><th scope="col" style="text-align:start">Otaq</th>{cols}</tr></thead>'
        f'<tbody>{rows}</tbody></table></div>')

    season_cards = "".join(
        f'<article class="panel reveal"><h3>{e(s.name)}</h3>'
        f'<p style="color:var(--ink-2)">{e(s.note)}</p>'
        f'<p class="mb-0"><span class="tag">{"".join(e(_span_text(sp)) for sp in s.spans[:1])}'
        f'</span>'
        + ("".join(f'<span class="tag">{e(_span_text(sp))}</span>' for sp in s.spans[1:]))
        + (f'<span class="tag tag-in">minimum {hotel.MIN_NIGHTS[s.key]} gecə</span>'
           if s.key in hotel.MIN_NIGHTS else "")
        + '</p></article>' for s in hotel.SEASONS)

    ref = ROOMS[1]
    body = (
        R.crumbs((("index.html", "Ana səhifə"), (None, "Qiymətlər")))
        + sec(sec_head("Açıq təqvim", "Bir illik qiymət, gizli xanası olmadan",
                       "Aşağıda hər otağın hər mövsümdəki gecəlik qiyməti var. Konkret "
                       "tarixin qiymətini görmək üçün otağın öz səhifəsindəki təqvimə "
                       "baxın — orada 365 gecənin hamısı ayrı-ayrı yazılıb.", "h1")
              + matrix
              + '<div class="note" style="margin-top:24px"><p><strong>Qiymətə daxildir:'
              '</strong> ƏDV, səhər yeməyi, Wi-Fi, çay və qəhvə, həyətdə parklanma.</p>'
              '<p class="mb-0"><strong>Daxil deyil:</strong> axşam yeməyi, ev heyvanı '
              'üçün gecəyə 10 ₼ təmizlik haqqı. Şəhər vergisi və xidmət haqqı '
              'yoxdur.</p></div>')
        + sec(sec_head("Mövsümlər", "Qiymət ilin altı mövsümündə dəyişir",
                       "Hər mövsümün nə vaxt olduğu və niyə bahalaşdığı burada yazılıb. "
                       "Rəqəmi dəyişdirən başqa bir şey yoxdur — həftə sonu əlavəsi, "
                       "son dəqiqə artımı və ya bayram “sürprizi” tətbiq etmirik.")
              + f'<div class="grid g-3">{season_cards}</div>', "sec sec-alt")
        + sec(sec_head("İl boyu", f"{ref.name} otağı üzərində bütün il",
                       "Nümunə olaraq bir otağın on iki ayı. Digər otaqların təqvimi "
                       "eyni formadadır və hər otağın öz səhifəsindədir.")
              + R.room_calendar(ref))
        + cta_band())

    trail = (("index.html", "Ana səhifə"), (None, "Qiymətlər"))
    w("qiymetler.html", R.page(
        f"Qiymətlər — bütün otaqlar, bütün mövsümlər | {BRAND}",
        "Səkkiz otağın altı mövsüm üzrə gecəlik qiyməti. ƏDV və səhər yeməyi daxil, "
        "gizli əlavə yoxdur. Konkret tarixlər üçün otaq təqvimləri.",
        "qiymetler.html", body, jsonld=[R.breadcrumb_ld(trail)]))


def _span_text(span) -> str:
    m1, d1, m2, d2 = span
    return f"{d1} {hotel.MONTHS_AZ[m1 - 1]} – {d2} {hotel.MONTHS_AZ[m2 - 1]}"


# --- reservation ------------------------------------------------------------

def build_reservation() -> None:
    opts = "".join(
        f'<option value="{r.slug}">{e(r.name)} — {e(r.kind.lower())}, '
        f'{r.sleeps} nəfər, {money(hotel.price_range(r)[0])}-dən</option>' for r in ROOMS)
    lo_table_rows = "".join(
        f'<tr><th scope="row" style="text-align:start">{e(r.name)}</th>'
        + "".join(
            f"<td>{money(hotel.price(r, next(d for d in hotel.season_days() if hotel.season_for(d).key == s.key)))}</td>"
            for s in hotel.SEASONS)
        + "</tr>" for r in ROOMS)

    form = (
        '<form class="form" id="res-form" novalidate>'
        '<div class="field-row">'
        '<div class="field"><label for="f-in">Gəliş tarixi</label>'
        f'<input type="date" id="f-in" name="in" required min="{hotel.SEASON_START}" '
        f'max="{hotel.SEASON_END}"><p class="hint">Yerləşmə saat {hotel.CHECKIN}-dan. Tarixi təqvimdən seçin</p>'
        '<p class="err" id="e-in" hidden></p></div>'
        '<div class="field"><label for="f-out">Çıxış tarixi</label>'
        f'<input type="date" id="f-out" name="out" required min="{hotel.SEASON_START}" '
        f'max="{hotel.SEASON_END + dt.timedelta(days=1)}">'
        f'<p class="hint">Çıxış saat {hotel.CHECKOUT}-yə qədər</p>'
        '<p class="err" id="e-out" hidden></p></div></div>'
        '<div class="field-row">'
        '<div class="field"><label for="f-room">Otaq</label>'
        f'<select id="f-room" name="room" required>{opts}</select>'
        '<p class="hint">Qiymət seçdiyiniz otağa görə hesablanır</p></div>'
        '<div class="field"><label for="f-guests">Neçə nəfər</label>'
        '<select id="f-guests" name="guests">'
        + "".join(f'<option value="{i}">{i} nəfər</option>' for i in range(1, 5))
        + '</select><p class="err" id="e-guests" hidden></p></div></div>'
        '<div class="field-row">'
        '<div class="field"><label for="f-name">Adınız və soyadınız</label>'
        '<input type="text" id="f-name" name="name" required autocomplete="name">'
        '<p class="err" id="e-name" hidden></p></div>'
        '<div class="field"><label for="f-phone">Telefon</label>'
        '<input type="tel" id="f-phone" name="phone" required autocomplete="tel" '
        'placeholder="+994 50 000 00 00" inputmode="tel">'
        '<p class="hint">Təsdiq üçün zəng edirik və ya WhatsApp yazırıq</p>'
        '<p class="err" id="e-phone" hidden></p></div></div>'
        '<div class="field"><label for="f-note">Əlavə qeyd (istəyə bağlı)</label>'
        '<textarea id="f-note" name="note" placeholder="Beşik lazımdır, gec gəlirik, '
        'ev heyvanı ilə gəlirik…"></textarea></div>'
        '<div class="check"><input type="checkbox" id="f-ok" required>'
        '<label for="f-ok">'
        '<a href="qaydalar.html">Ev qaydalarını və ləğv şərtlərini</a> oxudum</label></div>'
        '<p class="err" id="e-ok" hidden></p>'
        '<div class="total-box" id="res-total" aria-live="polite">'
        '<div class="total-line"><span>Gecə sayı</span><span id="t-nights">—</span></div>'
        '<div class="total-line"><span>Otaq</span><span id="t-room">—</span></div>'
        '<div class="total-line"><span>Mövsüm</span><span id="t-season">—</span></div>'
        '<div class="total-line is-sum"><span>Cəmi</span><span id="t-sum">—</span></div>'
        '<p class="hint mb-0" style="margin-top:10px">ƏDV və səhər yeməyi daxildir. '
        'Ödəniş yerində.</p></div>'
        '<div style="display:flex;flex-wrap:wrap;gap:12px">'
        f'<button class="btn btn-amber" type="submit" id="res-send">'
        f'{icon("chat")}WhatsApp üçün mesaj hazırla</button>'
        f'<button class="btn btn-quiet" type="button" id="res-mail">'
        f'{icon("mail")}E-poçt mətni hazırla</button></div>'
        '<p class="hint" style="margin:0">Düymə mesaj mətnini hazırlayır və WhatsApp-ı '
        'açır. Sayt heç bir məlumatı öz serverində saxlamır və ödəniş qəbul etmir.</p>'
        '</form>')

    noscript = (
        '<noscript><div class="note"><p><strong>Brauzerinizdə JavaScript söndürülüb.</strong> '
        'Hesablama işləmir, amma qiymətlər bu səhifədə və hər otağın səhifəsində '
        'yazılıb.</p><p class="mb-0">Rezervasiya üçün birbaşa yazın: '
        f'<a href="https://wa.me/{WHATSAPP_LINK.lstrip("+")}">WhatsApp {e(WHATSAPP_HUMAN)}</a>, '
        f'<a href="tel:{PHONE_LINK}">{e(PHONE_HUMAN)}</a> və ya '
        f'<a href="mailto:{EMAIL}">{e(EMAIL)}</a>. Yazarkən bunları göndərin: '
        'tarix aralığı, otağın adı, neçə nəfər, ad-soyad, telefon.</p></div></noscript>')

    side = (
        '<div class="stack">'
        '<div class="panel"><h2 class="mt-0" style="font-size:21px">Necə işləyir</h2>'
        '<ol style="color:var(--ink-2);margin-bottom:0">'
        '<li>Tarixi və otağı seçirsiniz, məbləğ ekranda çıxır.</li>'
        '<li>Düymə hazır mesaj mətni yaradır və WhatsApp-ı açır.</li>'
        '<li>Biz otağın boş olduğunu təsdiqləyirik.</li>'
        '<li>Ödəniş gəlişdə, nağd və ya kartla. Öncədən ödəniş yoxdur.</li>'
        '</ol></div>'
        '<div class="panel"><h2 class="mt-0" style="font-size:21px">Ləğv</h2>'
        '<p class="mb-0" style="color:var(--ink-2)">Gəlişdən 7 gün əvvəlinə qədər '
        'pulsuz. Sonra bir gecənin qiyməti tutulur. Novruz və Yeni il üçün müddət '
        '14 gündür.</p></div>'
        '<div class="panel"><h2 class="mt-0" style="font-size:21px">Ən ucuz tarixlər</h2>'
        '<p style="color:var(--ink-2)">Sakit mövsümdə bütün otaqlar baza qiymətindədir — '
        'ilin ən ucuz gecələri bunlardır:</p>'
        '<ul style="padding-inline-start:18px;margin-bottom:0;color:var(--ink-2)">'
        + "".join(f"<li>{e(_span_text(sp))}</li>"
                  for sp in hotel.SEASON_BY_KEY["sakit"].spans)
        + '</ul></div>'
        '<div class="panel"><h2 class="mt-0" style="font-size:21px">Birbaşa əlaqə</h2>'
        '<ul class="facts" style="flex-direction:column;align-items:flex-start;gap:12px">'
        f'<li>{icon("chat")}<a href="https://wa.me/{WHATSAPP_LINK.lstrip("+")}">'
        f'WhatsApp {e(WHATSAPP_HUMAN)}</a></li>'
        f'<li>{icon("phone")}<a href="tel:{PHONE_LINK}">{e(PHONE_HUMAN)}</a></li>'
        f'<li>{icon("mail")}<a href="mailto:{EMAIL}">{e(EMAIL)}</a></li></ul></div>'
        '</div>')

    price_table = (
        '<p class="scroll-hint">Cədvəl enlidir — barmağınızla yana sürüşdürün.</p>'
        '<div class="matrix-scroll"><table class="matrix">'
        '<caption>Gecəlik qiymət cədvəli — JavaScript olmadan da buradadır</caption>'
        '<thead><tr><th scope="col" style="text-align:start">Otaq</th>'
        + "".join(f'<th scope="col">{e(s.name)}</th>' for s in hotel.SEASONS)
        + f'</tr></thead><tbody>{lo_table_rows}</tbody></table></div>')

    body = (
        R.crumbs((("index.html", "Ana səhifə"), (None, "Rezervasiya")))
        + sec(sec_head("Rezervasiya", "Tarixi seçin, məbləği burada görün",
                       "Forma məbləği brauzerinizdə hesablayır və göndərmək üçün hazır "
                       "mesaj mətni verir. Heç bir məlumat serverə getmir, çünki bu "
                       "saytın serveri yoxdur.", "h1")
              + noscript
              + '<div class="grid g-2" style="align-items:start;gap:40px">'
              + form + side + '</div>')
        + sec(sec_head("Cədvəl", "Qiymətlər, tam siyahı") + price_table, "sec sec-alt"))

    trail = (("index.html", "Ana səhifə"), (None, "Rezervasiya"))
    w("rezervasiya.html", R.page(
        f"Rezervasiya — tarix seçin, məbləği dərhal görün | {BRAND}",
        "Gəliş və çıxış tarixini seçin, gecə sayı və ümumi məbləğ dərhal hesablansın. "
        "Öncədən ödəniş yoxdur, təsdiq WhatsApp və ya telefonla.",
        "rezervasiya.html", body, jsonld=[R.breadcrumb_ld(trail)],
        extra='<script src="assets/js/data.js" defer></script>\n'))


# --- restaurant -------------------------------------------------------------

def build_restaurant() -> None:
    sections = ""
    for title, dishes in MENU.items():
        rows = ""
        for d in dishes:
            tags = "".join(
                f'<span class="tag{" tag-in" if t == "qiymətə daxil" else ""}">{e(t)}</span>'
                for t in d.tags)
            price_txt = "daxil" if d.price == 0 else money(d.price)
            rows += (
                f'<div class="dish"><div class="dish-main"><h3>{e(d.name)}</h3>'
                f'<p>{e(d.desc)}</p>'
                + (f'<p style="margin-top:8px">{tags}</p>' if tags else "")
                + f'</div><div class="dish-price">{price_txt}</div></div>')
        sections += f'<div class="menu-sec"><h2>{e(title)}</h2>{rows}</div>'

    body = (
        R.crumbs((("index.html", "Ana səhifə"), (None, "Restoran")))
        + sec(sec_head("Restoran", "Kiçik menyu, Şəki mətbəxi",
                       "Otuz nəfərlik yeməkxana və həyətdə on iki yer. Qonaq evində "
                       "qalmayanlar da axşam yeməyinə gələ bilər, amma yer məhduddur — "
                       "zəng edin.", "h1")
              + '<div class="grid g-2" style="align-items:start;gap:40px">'
              + f'<div>{sections}</div>'
              + '<div class="stack">'
              '<div class="panel"><h3 class="mt-0">Saatlar</h3>'
              '<ul class="facts" style="flex-direction:column;align-items:flex-start;'
              f'gap:10px"><li>{icon("clock")}Səhər yeməyi 08:00–10:30</li>'
              f'<li>{icon("clock")}Axşam yeməyi 19:00–22:00</li>'
              f'<li>{icon("clock")}Piti üçün sifariş günorta 12:00-ə qədər</li></ul>'
              '<p class="mb-0" style="color:var(--ink-2);margin-top:14px">Səhər yeməyi '
              'havadan asılı olaraq həyətdə və ya yeməkxanada verilir.</p></div>'
              f'<div class="note"><p class="mb-0">{e(MENU_NOTE)}</p></div>'
              '<div class="panel"><h3 class="mt-0">Pəhriz və allergiya</h3>'
              '<p class="mb-0" style="color:var(--ink-2)">Vegetarian variantlar '
              'menyuda işarələnib. Qlutensiz və ya başqa məhdudiyyət varsa '
              'rezervasiya zamanı yazın — mətbəx kiçikdir, əvvəlcədən bilməsək '
              'yerində həll edə bilməyəcəyik.</p></div>'
              f'<a class="btn btn-main btn-block" href="tel:{PHONE_LINK}">'
              f'{icon("phone")}Masa üçün zəng edin</a>'
              '</div></div>'))

    trail = (("index.html", "Ana səhifə"), (None, "Restoran"))
    menu_ld = {
        "@context": "https://schema.org", "@type": "Restaurant",
        "name": f"{BRAND_FULL} restoranı", "url": SITE + "restoran.html",
        "servesCuisine": "Azərbaycan, Şəki mətbəxi",
        "priceRange": "5–16 ₼", "currenciesAccepted": "AZN",
        "telephone": PHONE_HUMAN,
        "address": {"@type": "PostalAddress", "streetAddress": "M. F. Axundzadə küçəsi 41",
                    "addressLocality": "Şəki", "addressCountry": "AZ"},
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "opens": "08:00", "closes": "10:30",
             "dayOfWeek": "https://schema.org/PublicHolidays"},
            {"@type": "OpeningHoursSpecification", "opens": "19:00", "closes": "22:00",
             "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                           "Saturday", "Sunday"]}],
        "hasMenu": {
            "@type": "Menu", "name": "Menyu", "inLanguage": "az",
            "hasMenuSection": [
                {"@type": "MenuSection", "name": title,
                 "hasMenuItem": [
                     {"@type": "MenuItem", "name": d.name, "description": d.desc,
                      "offers": {"@type": "Offer", "price": d.price,
                                 "priceCurrency": "AZN"}} for d in dishes]}
                for title, dishes in MENU.items()]},
        "isPartOf": {"@id": SITE + "#hotel"},
    }
    w("restoran.html", R.page(
        f"Restoran — Şəki mətbəxi, kiçik menyu | {BRAND}",
        "Səhər yeməyi otaq qiymətinə daxildir. Axşam menyusunda piti, sac içi, dolma "
        "və Şəki halvası. Piti üçün sifariş günorta 12-yə qədər verilir.",
        "restoran.html", body, jsonld=[menu_ld, R.breadcrumb_ld(trail)]))


# --- guide ------------------------------------------------------------------

def build_guide_index() -> None:
    cards = "".join(
        f'<article class="card reveal" style="--room:{ROOMS[i % len(ROOMS)].hex_light}">'
        '<div class="card-spine"></div><div class="card-body">'
        f'<h2 style="font-size:21px"><a href="beledci-{a.slug}.html">{e(a.title)}</a></h2>'
        f'<p>{e(a.lede)}</p>'
        '<div class="card-foot"><p class="mb-0" style="font-size:14.5px;'
        f'color:var(--ink-3)">{a.minutes} dəqiqə · {e(a.walk)}</p>'
        f'<a class="btn btn-quiet" href="beledci-{a.slug}.html">Oxu{icon("arrow")}</a>'
        '</div></div></article>' for i, a in enumerate(ARTICLES))
    body = (
        R.crumbs((("index.html", "Ana səhifə"), (None, "Şəki bələdçisi")))
        + sec(sec_head("Bələdçi", "Şəki haqqında dörd yazı",
                       "Turistik reklam deyil. Hansı saatda getmək lazım olduğu, nəyin "
                       "əslində baxmağa dəyməyəcəyi və hansı ayın niyə bahalı olduğu — "
                       "burada qaldığınız müddətdə işinizə yarayacaq şeylər.", "h1")
              + f'<div class="grid g-2">{cards}</div>'))
    trail = (("index.html", "Ana səhifə"), (None, "Şəki bələdçisi"))
    ld = {"@context": "https://schema.org", "@type": "ItemList",
          "name": "Şəki bələdçisi", "numberOfItems": len(ARTICLES),
          "itemListElement": [{"@type": "ListItem", "position": i + 1,
                               "url": SITE + f"beledci-{a.slug}.html", "name": a.title}
                              for i, a in enumerate(ARTICLES)]}
    w("beledci.html", R.page(
        f"Şəki bələdçisi — dörd praktik yazı | {BRAND}",
        "Xan Sarayı və şəbəkə, Şəki halvasını necə seçmək, Kiş kilsəsi və hansı ayda "
        "gəlmək. Qonaq evinin yazdığı praktik Şəki bələdçisi.",
        "beledci.html", body, jsonld=[ld, R.breadcrumb_ld(trail)]))


def build_article(a, i: int) -> None:
    blocks = ""
    for block in a.body:
        heading, paras = block[0], block[1:]
        blocks += f"<h2>{e(heading)}</h2>" + "".join(f"<p>{e(p)}</p>" for p in paras)
    facts = ("".join(
        f'<tr><th scope="row">{e(k)}</th><td>{e(v)}</td></tr>' for k, v in a.facts))
    other = [x for x in ARTICLES if x.slug != a.slug][:2]
    body = (
        R.crumbs((("index.html", "Ana səhifə"), ("beledci.html", "Şəki bələdçisi"),
                  (None, a.title)))
        + sec('<div class="grid g-2" style="align-items:start;gap:44px">'
              f'<article class="prose"><p class="eyebrow">Bələdçi · {a.minutes} dəqiqə</p>'
              f'<h1>{e(a.title)}</h1><p class="lede" style="margin:16px 0 24px">'
              f'{e(a.lede)}</p>{blocks}</article>'
              '<div class="stack">'
              + (f'<div class="passport"><table><caption>Qısa məlumat</caption>'
                 f'<tbody>{facts}</tbody></table></div>' if facts else "")
              + '<div class="panel"><h3 class="mt-0">Digər yazılar</h3><ul '
              'style="padding-inline-start:18px;margin-bottom:0">'
              + "".join(f'<li><a href="beledci-{x.slug}.html">{e(x.title)}</a></li>'
                        for x in other)
              + '</ul></div>'
              f'<a class="btn btn-main btn-block" href="otaqlar.html">'
              f'Otaqlara bax{icon("arrow")}</a>'
              '</div></div>'))
    trail = (("index.html", "Ana səhifə"), ("beledci.html", "Şəki bələdçisi"),
             (None, a.title))
    ld = {"@context": "https://schema.org", "@type": "Article",
          "headline": a.title, "description": a.lede, "inLanguage": "az",
          "url": SITE + f"beledci-{a.slug}.html",
          "image": SITE + "assets/img/og-cover.png",
          "author": {"@type": "Organization", "name": BRAND_FULL},
          "publisher": {"@id": SITE + "#hotel"},
          "datePublished": "2026-08-01", "dateModified": "2026-08-29",
          "articleSection": "Şəki bələdçisi",
          "wordCount": sum(len(p.split()) for b in a.body for p in b[1:])}
    w(f"beledci-{a.slug}.html", R.page(
        f"{a.title} | {BRAND}",
        a.lede,
        f"beledci-{a.slug}.html", body, jsonld=[ld, R.breadcrumb_ld(trail)]))


# --- sebeke, about, contact, rules, privacy, 404 ----------------------------

PATTERN_AZ = {"ulduz8": "səkkizguşəli ulduz və xaç", "sekkizguse": "səkkizbucaq və kvadrat",
              "carpaz": "çarpaz romb", "altibucaq": "altıbucaq"}


def build_sebeke_page() -> None:
    cards = "".join(
        f'<figure class="plan-fig reveal" style="padding:0;overflow:hidden">'
        f'<img src="assets/img/sebeke/{r.slug}.svg" width="720" height="480" '
        f'loading="lazy" alt="{e(r.name)} otağının şəbəkəsi: {e(PATTERN_AZ[r.pattern])} '
        f'naxışı, {e(r.glass)} rəngli şüşə">'
        f'<figcaption style="padding:16px 20px 20px;margin:0">'
        f'<strong>{e(r.name)}</strong> — {e(PATTERN_AZ[r.pattern])}, {e(r.glass)} şüşə. '
        f'<a href="otaq-{r.slug}.html">Otağa bax</a></figcaption></figure>'
        for r in ROOMS)
    body = (
        R.crumbs((("index.html", "Ana səhifə"), (None, "Evin pəncərələri")))
        + sec(sec_head("Şəbəkə", "Evin səkkiz pəncərəsi",
                       "Şəbəkə — taxta çubuqların bir-birinə oyulmuş yuvalarla "
                       "keçirilməsi ilə yığılan, mismarsız və yapışqansız pəncərədir. "
                       "Metal taxtadan fərqli genişləndiyi üçün mismar şüşəni sındırardı; "
                       "konstruksiya sökülüb yenidən yığıla bildiyi üçün bərpa mümkündür.",
                       "h1")
              + '<div class="note" style="margin-bottom:32px"><p class="mb-0">'
              'Bu şəkillər fotoşəkil deyil — hər otağın naxışı öz həndəsəsindən çəkilib. '
              'Səkkizinin hamısı birlikdə 32 kilobayt tutur, yəni bir fotoşəkilin '
              'onda biri. Sayt bu qədər yüngül olduğu üçün zəif internetdə də '
              'dərhal açılır.</p></div>'
              f'<div class="grid g-2">{cards}</div>')
        + sec(sec_head("Dörd naxış", "Otaqlar naxışa görə fərqlənir",
                       "Evdə dörd naxış ailəsi var. Eyni ailədən olan otaqlar sıxlıq və "
                       "rəngə görə ayrılır.")
              + '<p class="scroll-hint">Cədvəl enlidir — barmağınızla yana sürüşdürün.</p>'
        '<div class="matrix-scroll"><table class="matrix">'
              '<caption>Naxış, sıxlıq və şüşə rəngi</caption>'
              '<thead><tr><th scope="col" style="text-align:start">Otaq</th>'
              '<th scope="col" style="text-align:start">Naxış</th>'
              '<th scope="col">Sıxlıq</th>'
              '<th scope="col" style="text-align:start">Şüşə</th></tr></thead><tbody>'
              + "".join(
                  f'<tr style="{R.room_style(r)}"><th scope="row">'
                  f'<span class="room-dot"></span>'
                  f'<a href="otaq-{r.slug}.html">{e(r.name)}</a></th>'
                  f'<td style="text-align:start">{e(PATTERN_AZ[r.pattern])}</td>'
                  f'<td>{r.density}</td>'
                  f'<td style="text-align:start">{e(r.glass)}</td></tr>' for r in ROOMS)
              + '</tbody></table></div>', "sec sec-alt"))
    trail = (("index.html", "Ana səhifə"), (None, "Evin pəncərələri"))
    w("sebeke.html", R.page(
        f"Evin pəncərələri — səkkiz şəbəkə naxışı | {BRAND}",
        "Otaqların adı evin pəncərələrindəki şüşə rənglərindən gəlir. Dörd naxış "
        "ailəsi, səkkiz otaq və şəbəkənin niyə mismarsız yığıldığı.",
        "sebeke.html", body, jsonld=[R.breadcrumb_ld(trail)]))


def build_about() -> None:
    body = (
        R.crumbs((("index.html", "Ana səhifə"), (None, "Haqqımızda")))
        + sec('<div class="grid g-2" style="align-items:start;gap:44px">'
              '<div class="prose"><p class="eyebrow">Haqqımızda</p>'
              '<h1>Səkkiz otaqlıq bir ev, otel deyil</h1>'
              '<p>Bina 1920-ci illərdə tikilmiş yaşayış evidir. 2019-cu ildə qonaq '
              'evinə çevrildi: divarlar, tavan naxışları və dörd şəbəkə pəncərə '
              'saxlanıldı, su və istilik sistemi tam yeniləndi.</p>'
              '<h2>Nə edə bilmirik</h2>'
              '<p>Liftimiz yoxdur və köhnə evdə lift qurmaq mümkün deyil. Bir otağa '
              'çatmaq üçün 34 pillə qalxmaq lazımdır. Hər otağın səhifəsində pillə '
              'sayı yazılıb, çünki bunu gəldikdən sonra öyrənmək gec olur.</p>'
              '<p>Otaqların səs izolyasiyası yeni tikili səviyyəsində deyil. Küçəyə '
              'baxan otaqda səhər səs eşidilir və biz bunu həmin otağın səhifəsində '
              'yazmışıq. Bunu düzəltmək əvəzinə yazmağı seçdik.</p>'
              '<h2>Qiymət haqqında</h2>'
              '<p>Bütün 365 gecənin qiyməti saytdadır. Bunu qonaq üçün etmirik — '
              'özümüz üçün də edirik. Qiymət açıq olanda telefon zəngi qiymət soruşmaq '
              'üçün deyil, otaq saxlamaq üçün gəlir.</p>'
              '<p>Rezervasiya birbaşa bizə gələndə vasitəçiyə komissiya ödəmirik. '
              'Ona görə birbaşa yazan qonaq eyni otağı daha ucuz alır və biz də '
              'bundan qazanırıq. Bu, güzəşt deyil, arifmetikadır.</p>'
              '<h2>Bu sayt haqqında</h2>'
              '<p>Bu sayt bir nümunə işdir. Qırx Pəncərə Qonaq Evi uydurma bir '
              'müəssisədir — belə bir otel yoxdur, göstərilən qiymətlər, otaqlar və '
              'rəylər real deyil. Sayt Azərbaycanda kiçik otellərin saytlarının necə '
              'ola biləcəyini göstərmək üçün hazırlanıb.</p></div>'
              '<div class="stack">'
              '<div class="passport"><table><caption>Rəqəmlərlə</caption><tbody>'
              f'<tr><th scope="row">Otaq sayı</th><td>{len(ROOMS)}</td></tr>'
              '<tr><th scope="row">Binanın yaşı</th><td>1920-ci illər</td></tr>'
              '<tr><th scope="row">Qonaq evinə çevrilib</th><td>2019</td></tr>'
              '<tr><th scope="row">Orijinal şəbəkə pəncərə</th><td>4 ədəd</td></tr>'
              f'<tr><th scope="row">Xan Sarayına</th><td>900 m</td></tr>'
              f'<tr><th scope="row">Qonaq rəyi</th>'
              f'<td>{str(hotel.RATING).replace(".", ",")} / 5</td></tr>'
              '</tbody></table></div>'
              f'<a class="btn btn-main btn-block" href="otaqlar.html">'
              f'Otaqlara bax{icon("arrow")}</a>'
              f'<a class="btn btn-quiet btn-block" href="sebeke.html">'
              f'Evin pəncərələri{icon("arrow")}</a>'
              '</div></div>'))
    trail = (("index.html", "Ana səhifə"), (None, "Haqqımızda"))
    w("haqqimizda.html", R.page(
        f"Haqqımızda — 1920-ci illərin evi, səkkiz otaq | {BRAND}",
        "Bina 1920-ci illərdə tikilib, 2019-da qonaq evinə çevrilib. Liftimiz yoxdur, "
        "bunu gizlətmirik. Qiymətlərin niyə açıq olduğunu da izah edirik.",
        "haqqimizda.html", body, jsonld=[R.breadcrumb_ld(trail)]))


def build_contact() -> None:
    osm = f"https://www.openstreetmap.org/?mlat={hotel.LAT}&mlon={hotel.LON}#map=16/{hotel.LAT}/{hotel.LON}"
    body = (
        R.crumbs((("index.html", "Ana səhifə"), (None, "Əlaqə")))
        + sec(sec_head("Əlaqə", "Necə tapmaq və necə yazmaq",
                       "Ən sürətli yol WhatsApp-dır. Telefonu səhər 8-dən axşam 22-yə "
                       "qədər cavablandırırıq.", "h1")
              + '<div class="grid g-2" style="align-items:start;gap:40px">'
              '<div class="stack">'
              '<div class="panel"><h2 style="font-size:21px" class="mt-0">Birbaşa əlaqə</h2>'
              '<ul class="facts" style="flex-direction:column;align-items:flex-start;'
              'gap:14px;margin-bottom:0">'
              f'<li>{icon("chat")}<a href="https://wa.me/{WHATSAPP_LINK.lstrip("+")}">'
              f'WhatsApp — {e(WHATSAPP_HUMAN)}</a></li>'
              f'<li>{icon("phone")}<a href="tel:{PHONE_LINK}">{e(PHONE_HUMAN)}</a></li>'
              f'<li>{icon("mail")}<a href="mailto:{EMAIL}">{e(EMAIL)}</a></li>'
              f'<li>{icon("pin")}{e(hotel.ADDRESS)}</li>'
              f'<li>{icon("clock")}Yerləşmə {hotel.CHECKIN} · Çıxış {hotel.CHECKOUT}</li>'
              '</ul></div>'
              '<div class="panel"><h2 style="font-size:21px" class="mt-0">Necə gəlmək</h2>'
              '<p style="color:var(--ink-2)"><strong>Bakıdan:</strong> avtobus 5 saat, '
              'gecə qatarı 9 saat. Avtomobillə 300 km, təxminən 4 saat.</p>'
              '<p style="color:var(--ink-2)"><strong>Şəki avtovağzalından:</strong> '
              'taksi 5–7 ₼, 10 dəqiqə. Qarşılama xidmətimiz yoxdur.</p>'
              '<p class="mb-0" style="color:var(--ink-2)"><strong>Avtomobillə '
              'gəlirsinizsə:</strong> həyətdə üç yer var, pulsuz və növbə ilə. '
              'Dolu olanda 150 m aralıda küçə parklanması sərbəstdir.</p></div>'
              f'<a class="btn btn-quiet btn-block" href="{osm}" rel="noopener">'
              f'{icon("pin")}Xəritədə aç (OpenStreetMap)</a>'
              '</div>'
              '<div class="stack">'
              '<div class="note"><p class="mb-0">Rezervasiya üçün <a '
              'href="rezervasiya.html">rezervasiya səhifəsindəki</a> formadan istifadə '
              'etsəniz, tarix, otaq və məbləğ mesaja özü yazılır — bir gediş-gəliş '
              'az olur.</p></div>'
              '<div class="passport"><table><caption>Nə vaxt cavab veririk</caption>'
              '<tbody>'
              '<tr><th scope="row">WhatsApp</th><td>08:00–22:00, adətən 1 saat içində</td></tr>'
              '<tr><th scope="row">Telefon</th><td>08:00–22:00</td></tr>'
              '<tr><th scope="row">E-poçt</th><td>iş günü ərzində</td></tr>'
              '<tr><th scope="row">Gecə</th><td>22:00–08:00 arası cavab vermirik</td></tr>'
              '</tbody></table></div>'
              '</div></div>'))
    trail = (("index.html", "Ana səhifə"), (None, "Əlaqə"))
    w("elaqe.html", R.page(
        f"Əlaqə — WhatsApp, telefon və ünvan | {BRAND}",
        f"{hotel.ADDRESS}. WhatsApp və telefon 08:00–22:00. Bakıdan avtobusla 5 saat, "
        "Şəki avtovağzalından taksi ilə 10 dəqiqə.",
        "elaqe.html", body, jsonld=[R.hotel_ld(), R.breadcrumb_ld(trail)]))


def build_rules() -> None:
    items = "".join(
        f'<details><summary>{e(q)}</summary><div class="answer"><p>{e(a)}</p></div>'
        '</details>' for q, a in FAQ)
    body = (
        R.crumbs((("index.html", "Ana səhifə"), (None, "Ev qaydaları")))
        + sec(sec_head("Qaydalar", "Ev qaydaları və ləğv şərtləri",
                       "Hamısı bir səhifədə. Sürpriz olmaması üçün rezervasiyadan "
                       "əvvəl oxumağa dəyər.", "h1")
              + f'<div class="faq" style="max-width:76ch">{items}</div>'))
    trail = (("index.html", "Ana səhifə"), (None, "Ev qaydaları"))
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": "az",
          "mainEntity": [{"@type": "Question", "name": q,
                          "acceptedAnswer": {"@type": "Answer", "text": a}}
                         for q, a in FAQ]}
    w("qaydalar.html", R.page(
        f"Ev qaydaları və ləğv şərtləri | {BRAND}",
        "Yerləşmə və çıxış saatları, ləğv şərtləri, uşaqlar, ev heyvanı, parklanma və "
        "siqaret qaydaları — hamısı bir səhifədə.",
        "qaydalar.html", body, jsonld=[ld, R.breadcrumb_ld(trail)]))


def build_privacy() -> None:
    body = (
        R.crumbs((("index.html", "Ana səhifə"), (None, "Məxfilik")))
        + sec('<div class="prose"><p class="eyebrow">Məxfilik</p>'
              '<h1>Bu sayt sizin haqqınızda nə toplayır</h1>'
              '<p>Qısa cavab: heç nə. Uzun cavab aşağıdadır.</p>'
              '<h2>Formalar</h2>'
              '<p>Rezervasiya formasına yazdıqlarınız brauzerinizdən çıxmır. Forma '
              'məlumatı heç bir serverə göndərmir — düymə yalnız mesaj mətni hazırlayır '
              'və onu WhatsApp və ya e-poçt proqramınıza ötürür. Göndərib-göndərməmək '
              'sizin qərarınızdır.</p>'
              '<h2>Kuki və izləmə</h2>'
              '<p>Saytda kuki yoxdur. Analitika, reklam pikseli, sosyal şəbəkə düyməsi '
              'və üçüncü tərəf skripti yoxdur. Şrift və şəkillərin hamısı bu saytın '
              'özündən yüklənir, xarici serverdən deyil.</p>'
              '<h2>Server jurnalları</h2>'
              '<p>Sayt GitHub Pages üzərində yerləşir. Hər veb server kimi o da '
              'sorğuları qeyd edə bilər; bu jurnallara bizim çıxışımız yoxdur və '
              'onları istifadə etmirik.</p>'
              '<h2>WhatsApp və e-poçt</h2>'
              '<p>Bizə WhatsApp və ya e-poçtla yazsanız, mesajınız həmin xidmətin '
              'şərtləri altında saxlanılır. Rezervasiya yazışmasını qalış '
              'bitdikdən sonra 12 ay saxlayır, sonra silirik.</p>'
              '<h2>Bu sayt nümunədir</h2>'
              '<p>Qırx Pəncərə Qonaq Evi uydurma bir müəssisədir. Real bir otel deyil, '
              'real qiymət və rezervasiya qəbul etmir.</p></div>'))
    trail = (("index.html", "Ana səhifə"), (None, "Məxfilik"))
    w("mexfilik.html", R.page(
        f"Məxfilik — kuki yoxdur, izləmə yoxdur | {BRAND}",
        "Saytda kuki, analitika və üçüncü tərəf skripti yoxdur. Rezervasiya forması "
        "məlumatı heç bir serverə göndərmir.",
        "mexfilik.html", body, jsonld=[R.breadcrumb_ld(trail)]))


def build_404() -> None:
    body = sec(
        '<div class="prose"><p class="eyebrow">Səhifə tapılmadı</p>'
        '<h1>Bu ünvanda səhifə yoxdur</h1>'
        '<p class="lede">Link köhnə ola bilər və ya ünvanda hərf səhvi var. '
        'Axtardığınız çox güman ki, aşağıdakılardan biridir.</p>'
        '<ul style="font-size:18px">'
        '<li><a href="otaqlar.html">Otaqlar</a> — səkkiz otaq, ölçü və qiymətlə</li>'
        '<li><a href="qiymetler.html">Qiymətlər</a> — bir illik təqvim</li>'
        '<li><a href="rezervasiya.html">Rezervasiya</a></li>'
        '<li><a href="restoran.html">Restoran</a></li>'
        '<li><a href="beledci.html">Şəki bələdçisi</a></li>'
        f'<li><a href="elaqe.html">Əlaqə</a> — WhatsApp {e(WHATSAPP_HUMAN)}</li></ul>'
        f'<a class="btn btn-main" href="index.html">Ana səhifəyə qayıt{icon("arrow")}</a>'
        '</div>')
    w("404.html", R.page(
        f"Səhifə tapılmadı | {BRAND}",
        "Axtardığınız səhifə bu ünvanda yoxdur. Otaqlar, qiymətlər və rezervasiya "
        "səhifələrinə buradan keçə bilərsiniz.",
        "404.html", body))


# --- robots, sitemap --------------------------------------------------------

def build_meta_files() -> None:
    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        f"Sitemap: {SITE}sitemap.xml\n", encoding="utf-8")
    today = "2026-08-29"
    prio = {"index.html": "1.0", "otaqlar.html": "0.9", "qiymetler.html": "0.9",
            "rezervasiya.html": "0.9"}
    urls = ""
    for path in sorted(PAGES):
        if path == "404.html":
            continue
        loc = SITE + ("" if path == "index.html" else path)
        p = prio.get(path, "0.7" if path.startswith("otaq-") else "0.6")
        urls += (f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{today}</lastmod>\n"
                 f"    <priority>{p}</priority>\n  </url>\n")
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>\n", encoding="utf-8")


# --- data.js ----------------------------------------------------------------

def build_data_js() -> None:
    """The same numbers the HTML shows, for the reservation calculator.

    Not the 2920 prices: the base, the factor and one character per day. The
    browser recomputes with the same rounding, and audit.py checks a sample of
    what it produces against what the pages actually print.
    """
    code = {s.key: chr(ord("a") + i) for i, s in enumerate(hotel.SEASONS)}
    days = "".join(code[hotel.season_for(d).key] for d in hotel.season_days())
    assert len(set(days)) == len(hotel.SEASONS), "a season never appears in the window"
    data = {
        "start": hotel.SEASON_START.isoformat(),
        "end": hotel.SEASON_END.isoformat(),
        "days": days,
        "seasons": {code[s.key]: {"name": s.name, "factor": s.factor,
                                  "min": hotel.MIN_NIGHTS.get(s.key, 1)}
                    for s in hotel.SEASONS},
        "rooms": {r.slug: {"name": r.name, "base": r.base, "sleeps": r.sleeps,
                           "kind": r.kind} for r in ROOMS},
        "phone": hotel.WHATSAPP_LINK, "email": EMAIL,
    }
    (ROOT / "assets/js/data.js").write_text(
        "/* Generated by tools/build_pages.py -- do not edit by hand.\n"
        "   One character per night of the published season, plus the factors, so the\n"
        "   browser can recompute exactly the prices the pages print. */\n"
        "window.QP = " + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        + ";\n", encoding="utf-8")


def main() -> None:
    build_index()
    build_rooms_index()
    for r in ROOMS:
        build_room(r)
    build_prices()
    build_reservation()
    build_restaurant()
    build_guide_index()
    for i, a in enumerate(ARTICLES):
        build_article(a, i)
    build_sebeke_page()
    build_about()
    build_contact()
    build_rules()
    build_privacy()
    build_404()
    build_meta_files()
    build_data_js()
    total = sum(len(v.encode()) for v in PAGES.values())
    print(f"{len(PAGES)} pages, {total / 1024:.0f} KB of HTML")
    for p in sorted(PAGES, key=lambda k: -len(PAGES[k]))[:4]:
        print(f"  {p:26} {len(PAGES[p].encode()) / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
