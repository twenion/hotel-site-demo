# Qırx Pəncərə — demo hotel site

A static site for a boutique guesthouse in Şəki, Azerbaijan, built as a portfolio
piece and a sales demo. **The guesthouse is fictional** — no real business's name,
branding, rooms, prices or photography are used, the form takes nothing and sends
nothing, and the site says so in its own footer.

**Live:** https://twenion.github.io/hotel-site-demo/

8 rooms · 24 pages · 365 published nightly prices · no framework · no build step
at runtime · no CDN · no cookies

## The three demos

Three sales demos for Azerbaijani small businesses, deliberately different in
sector, palette **and shape** — a service site, a catalogue and a booking site —
so they read as three pieces of work rather than one template three times. Each
is a fictional business, holds itself to the same audit checklist, and ships as
static files with no framework and no CDN.

| | | |
| --- | --- | --- |
| [`cargo-site-demo`](https://github.com/twenion/cargo-site-demo) | Xəzər Ekspres — Courier | Tracking, tariffs and an order form — a dark, service-shaped site · [live](https://twenion.github.io/cargo-site-demo/) |
| [`ecommerce-site-demo`](https://github.com/twenion/ecommerce-site-demo) | Zərrə — Skincare retail | 24 products, cart and checkout — a light, catalogue-shaped site · [live](https://twenion.github.io/ecommerce-site-demo/) |
| `hotel-site-demo` **← you are here** | Qırx Pəncərə — Şəki guesthouse | 365 published nightly prices and a booking form — a calendar-shaped site |

## Why it exists

I audit small-business websites in Azerbaijan. On hotel sites one fault outranks all
the others, and it is not technical: **the price is not on the page.** You get
"qiymət üçün əlaqə saxlayın". Almost nobody writes. They go to Booking.com and book
the same room there — and the hotel pays 15–18% commission on a guest who had
already found their own website.

Everything else follows from that first refusal. If you are not publishing prices you
are not publishing a season calendar, so there is nothing to put structured data on,
so the site never appears in a search result with a price attached, so the only
channel that works is the one taking the commission.

This site is the argument for the opposite, built out.

## The signature: the open calendar

Every room publishes its real nightly price for **all 365 nights** of the coming
season, as a static table you can read with JavaScript off. 90–405 ₼, VAT and
breakfast already inside the number, no city tax, no service charge, no weekend
surcharge. The colour of a cell is the season, and the page says in plain Azerbaijani
why each season costs what it costs.

One `SEASONS` table in `tools/hotel.py` feeds five places: the room card, the room
page calendar, the season matrix, the JSON-LD `Offer`, and the live total in the
browser. `tools/audit.py` fails the build if any of them disagree.

## The second signature: the room passport

Every room publishes what people actually want to know and hotel sites never print:
floor area to a decimal, which floor, **how many steps from the gate to the door**,
bed size in centimetres, which way the window faces, bath or shower, courtyard or
street side. Under it sits a floor plan drawn to scale — and `hotel.py` refuses to
build if the plan's rectangles do not add up to the square metres the page
advertises. That check caught a room advertising 24,6 m² over a plan drawing 20,1.

The rooms also say the unflattering things: the attic room is 34 steps up with no
lift and the ceiling drops to 1,7 m; the twin room hears the bakery from 8am; the
family room's partition is 120 cm of wood and not a door.

## The third signature: şəbəkə, generated

There is no photography. The imagery is the Şəki lattice window the house is named
after, built as SVG from real geometry — star-and-cross, octagon-and-square, diagonal
and hexagonal tilings, one per room, tinted from that room's own glass colour. All
ten panels and the favicon come to 32 KB, about a tenth of one unoptimised JPEG, and
the repository stays licence-clean.

The colours are not decorative. A room's glass colour marks that room everywhere it
appears — its card spine, its calendar, its floor plan, its row in every table.

## What is in it

- **8 rooms, each its own static URL** with `HotelRoom` structured data: occupancy,
  floor size, bed, reviews, and an `offers` block carrying the real lowest price with
  `valueAddedTaxIncluded`. Nothing is routed by script.
- **A reservation form with no back end.** It computes nights, season and total in the
  browser, then hands you a finished WhatsApp or e-mail message. No payment, no
  account, no data leaves the page. With JavaScript off, a `<noscript>` block gives
  the phone, WhatsApp, e-mail and the full price table.
- **A restaurant menu** with `Restaurant` + `Menu` schema, and a **Şəki guide** of four
  articles written to be useful rather than promotional — which hour to visit the Xan
  Sarayı for the light, how to tell real saffron from food colouring in the halva,
  which month is cheap and why.
- **A share card per room** — 1200×630 PNG showing the room, its size, its steps and
  its cheapest night, because room links get pasted into WhatsApp and chat apps do not
  preview SVG.
- **Light and dark**, both measured against WCAG AA.

## How it is built

Static HTML, CSS and vanilla JavaScript. It runs from a folder — no server, no build
step, no CDN, no third-party request of any kind — because that is how it gets handed
to a client.

`tools/` is a development aid, not a runtime dependency:

| | |
| --- | --- |
| `hotel.py` | Rooms, seasons, prices, menu, guide, reviews. Validates itself on import. |
| `sebeke.py` | The lattice generator: four tilings, one panel per room. |
| `render.py` | The shell and every shared component — one header, one card, one calendar. |
| `build_pages.py` | Writes all 24 pages, `sitemap.xml`, `robots.txt` and `data.js`. |
| `og_render.py` | The share cards, shot in headless Chrome. |
| `audit.py` | Our client audit checklist, run against this site. |
| `audit_selftest.py` | Breaks the site 22 ways and asserts the audit notices. |
| `js_check.py` | Drives the real form in a browser; compares its totals to `hotel.py`. |
| `phone_shot.py` | Screenshots pages at a true 390px viewport. |

```
python3 tools/build_pages.py      # regenerate the site
python3 tools/audit.py            # 19 checks, 0 faults
python3 tools/audit_selftest.py   # 22/22 injected faults caught
python3 tools/js_check.py         # 9/9 browser-vs-model checks
```

## Verification, not assertion

Three claims on this page are checkable rather than assertable, and each has a script
that fails loudly:

- **The prices agree everywhere.** `js_check.py` drives the real form in headless
  Chrome across six date ranges chosen to cross season boundaries, and compares what
  the browser prints to what `hotel.py` computes. It also asserts the two refusals the
  form has to make. This is why `hotel.py` rounds with `floor(x + 0.5)` rather than
  `round()` — Python rounds half to even and `Math.round` does not, and the two would
  have disagreed by 5 ₼ on some dates.
- **The audit catches things.** `audit_selftest.py` copies the site, injects 22 faults
  we have really found on client sites — an `<h1>` wrapped round a logo, an empty
  `alt`, schema with a blank field, a page missing from the sitemap, a font that never
  got uploaded — and asserts each one is reported.
- **The plans are honest.** `hotel.py` will not import if a floor plan's rectangles
  disagree with the advertised square metres, if a bathroom overlaps a bed, if the
  seasons leave a gap in the year, or if a glass colour falls below 4.5:1 in either
  scheme.

## Language

Every user-facing string is Azerbaijani, with the letters that break on badly built
sites — Ə ə Ç ç Ş ş Ğ ğ I ı İ i Ö ö Ü ü X x — and the manat sign ₼. Both typefaces
were chosen by rendering candidates with a deliberate fallback wired in and checking
the fallback never appeared. Code, identifiers, comments and commits are English.

## Licence

Code MIT. The content is written for a fictional business and is not for reuse as a
real hotel's copy.
