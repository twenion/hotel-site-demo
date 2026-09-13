#!/usr/bin/env python3
"""The single source of truth: rooms, seasons, prices, menu, guide, reviews.

Everything the site says about a room -- its price in September, the size of its
bed, the colour that marks it in the calendar -- comes from here. Five places on
the site quote a price; they quote this one.

The module validates itself on import. A season table with a gap in it, a floor
plan whose rectangles do not add up to the square metres we advertise, or a glass
colour that fails contrast will stop the build rather than ship.

    python3 tools/hotel.py     # prints the numbers and exits non-zero on a fault
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field

# --- Identity ---------------------------------------------------------------

BRAND = "Qırx Pəncərə"
BRAND_FULL = "Qırx Pəncərə Qonaq Evi"
CITY = "Şəki"
SITE = "https://twenion.github.io/hotel-site-demo/"
ADDRESS = "M. F. Axundzadə küçəsi 41, Yuxarı Baş, Şəki AZ5500"
PHONE_HUMAN = "+994 24 000 00 00"
PHONE_LINK = "+99424000000"
WHATSAPP_LINK = "+994500000000"
WHATSAPP_HUMAN = "+994 50 000 00 00"
EMAIL = "salam@qirxpencere.example"
LAT, LON = 41.1975, 47.1972

CHECKIN, CHECKOUT = "14:00", "12:00"
VAT_RATE = 0.18          # ƏDV, already inside every published price
ROOM_COUNT = 8

# The calendar the site publishes. Fixed window, so every page agrees.
SEASON_START = dt.date(2026, 9, 1)
SEASON_END = dt.date(2027, 8, 31)

MONTHS_AZ = ["yanvar", "fevral", "mart", "aprel", "may", "iyun",
             "iyul", "avqust", "sentyabr", "oktyabr", "noyabr", "dekabr"]
MONTHS_AZ_CAP = [m.capitalize() for m in MONTHS_AZ]
WEEKDAYS_AZ = ["B.e", "Ç.a", "Ç", "C.a", "C", "Ş", "B"]      # Monday first


# --- Colour helpers ---------------------------------------------------------

def _srgb_to_lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (0.2126 * _srgb_to_lin(r) + 0.7152 * _srgb_to_lin(g)
            + 0.0722 * _srgb_to_lin(b))


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


SURFACE_LIGHT = "#FFFFFF"
SURFACE_DARK = "#1D211D"


# --- Seasons ----------------------------------------------------------------

@dataclass(frozen=True)
class Season:
    key: str
    name: str          # shown to the guest
    note: str          # why the price moves -- the guest deserves the reason
    factor: float
    spans: tuple       # ((month, day, month, day), ...) inclusive, may wrap the year
    tone: str          # colour token used in the calendar


SEASONS = (
    Season("sakit", "Sakit mövsüm",
           "Şəhər boş, qiymət ən aşağı həddə. Qarlı Şəkini görmək istəyənlər üçün.",
           1.00, ((1, 7, 2, 28), (11, 10, 12, 24)), "quiet"),
    Season("yaz", "Yaz",
           "Bağlar çiçək açır, hava 15-22 dərəcə. Gəzinti üçün ən rahat aylar.",
           1.20, ((3, 1, 3, 19), (3, 25, 5, 31)), "spring"),
    Season("novruz", "Novruz",
           "Beş gün. Şəhər dolur, otaqlar adətən fevralda bitir.",
           1.55, ((3, 20, 3, 24),), "peak"),
    Season("yay", "Yay",
           "Bakıdan sərinliyə qaçanların mövsümü. İyul-avqustda həyət axşamlar doludur.",
           1.40, ((6, 1, 8, 31),), "summer"),
    Season("payiz", "Payız rəngləri",
           "Çinar yarpaqları saralır. Fotoqraflar bu iki ayı seçir.",
           1.30, ((9, 1, 11, 9),), "autumn"),
    Season("yenil", "Yeni il",
           "25 dekabr - 6 yanvar. Ən yüksək qiymət, minimum iki gecə.",
           1.65, ((12, 25, 12, 31), (1, 1, 1, 6)), "peak"),
)

SEASON_BY_KEY = {s.key: s for s in SEASONS}


def season_for(day: dt.date) -> Season:
    for s in SEASONS:
        for m1, d1, m2, d2 in s.spans:
            if (m1, d1) <= (day.month, day.day) <= (m2, d2):
                return s
    raise KeyError(f"no season covers {day:%d.%m}")


MIN_NIGHTS = {"novruz": 2, "yenil": 2}


def min_nights(day: dt.date) -> int:
    return MIN_NIGHTS.get(season_for(day).key, 1)


# --- Rooms ------------------------------------------------------------------

@dataclass(frozen=True)
class Plan:
    """The room drawn to scale, in centimetres, origin top-left.

    Rectangles are (x, y, w, h). They are what the floor plan draws and what the
    square metres are checked against -- a plan that disagrees with the headline
    number is how a hotel loses trust before check-in.
    """
    w: int
    h: int
    bath: tuple = ()          # (x, y, w, h) or empty for a shared bathroom
    bed: tuple = ()           # ((x, y, w, h), ...)
    windows: tuple = ()       # ((x, y, w, h), ...) drawn on the wall
    door: tuple = ()          # (x, y, w, h)
    extras: tuple = ()        # ((x, y, w, h, label), ...)

    @property
    def area_m2(self) -> float:
        return round(self.w * self.h / 10_000, 1)


@dataclass(frozen=True)
class Room:
    slug: str
    name: str
    kind: str                 # shown as the room type
    glass: str                # colour name, Azerbaijani
    hex_light: str
    hex_dark: str
    base: int                 # ₼ per night in the quiet season, all in
    sleeps: int
    size_m2: float
    floor: int                # 0 = ground
    steps: int                # steps from the courtyard gate to the room door
    bed_cm: str
    aspect: str               # what the window faces
    bathroom: str
    lift: bool
    pattern: str              # şəbəkə family
    density: int              # lattice cells across the tile
    lede: str
    body: tuple               # paragraphs
    features: tuple           # short factual bullets
    plan: Plan
    tint_note: str = ""


ROOMS = (
    Room(
        slug="benovse", name="Bənövşə", kind="Tək nəfərlik otaq", glass="bənövşəyi",
        hex_light="#6B3F9E", hex_dark="#BFA0EE", base=90, sleeps=1, size_m2=14.4,
        floor=1, steps=17, bed_cm="120 × 200", aspect="həyətə, şimal-qərb",
        bathroom="Duş, vanna yoxdur", lift=False, pattern="ulduz8", density=5,
        lede="Evin ən kiçik otağı, tək gələnlər üçün. Pəncərəsi həyətdəki tut ağacına baxır.",
        body=(
            "Yuxarı mərtəbədə, dəhlizin sonunda. Küçəyə baxmır, ona görə səhər tezdən "
            "keçən avtomobil səsi eşidilmir. Yataq 120 sm-lik tək çarpayıdır, iki nəfər "
            "üçün nəzərdə tutulmayıb.",
            "Şəbəkə pəncərəsi 1998-ci ildə Şəkidə, Xan Sarayının bərpasında işləmiş "
            "ustanın emalatxanasında yığılıb. Bənövşəyi şüşə otağa günorta saatlarında "
            "divara düşən rəngli ləkə verir.",
        ),
        features=("14,4 m² döşəmə sahəsi", "İş masası və oturacaq",
                  "Duş kabin, vanna yoxdur", "Pəncərə həyətə baxır"),
        plan=Plan(w=320, h=450,
                  bath=(0, 300, 150, 150),
                  bed=((165, 40, 120, 200),),
                  windows=((110, 0, 120, 8),),
                  door=(0, 240, 8, 80),
                  extras=((165, 300, 130, 60, "masa"), (0, 40, 60, 120, "şkaf"))),
    ),
    Room(
        slug="lacivard", name="Lacivərd", kind="İki nəfərlik otaq", glass="lacivərd",
        hex_light="#1B4FA0", hex_dark="#8FB4F0", base=120, sleeps=2, size_m2=20.2,
        floor=0, steps=3, bed_cm="160 × 200", aspect="həyətə, şərq",
        bathroom="Duş", lift=False, pattern="carpaz", density=6,
        lede="Zirzəmi mərtəbəsində deyil, həyət səviyyəsində — qapıya üç pillə var.",
        body=(
            "Dizlə problemi olan qonaqlar üçün ən rahat otaq: qapıya üç pillə, sonra "
            "düz döşəmə. Vanna otağının qapısı 80 sm enindədir.",
            "Şərqə baxdığı üçün səhər günəşi birbaşa düşür. Yayda saat 7-dən sonra "
            "otaq işıqlanır; pərdə qatlıdır, tam qaranlıq lazım olanda çəkilir.",
        ),
        features=("20,2 m² döşəmə sahəsi", "Həyət səviyyəsi, cəmi 3 pillə",
                  "160 sm ikinəfərlik çarpayı", "Vanna otağı qapısı 80 sm"),
        plan=Plan(w=380, h=530,
                  bath=(0, 370, 170, 160),
                  bed=((190, 50, 160, 200),),
                  windows=((372, 120, 8, 160),),
                  door=(0, 260, 8, 90),
                  extras=((190, 330, 150, 60, "komod"), (0, 40, 70, 130, "şkaf"))),
    ),
    Room(
        slug="kehreba", name="Kəhrəba", kind="İki çarpayılı otaq", glass="kəhrəba",
        hex_light="#9A5C05", hex_dark="#E0A64A", base=130, sleeps=2, size_m2=22.1,
        floor=1, steps=17, bed_cm="2 × (90 × 200)", aspect="küçəyə, cənub",
        bathroom="Duş", lift=False, pattern="altibucaq", density=5,
        lede="İki ayrı çarpayı. Dost və ya iş yoldaşı ilə gələnlərin seçdiyi otaq.",
        body=(
            "Çarpayılar arasında 70 sm məsafə var, birləşdirilmir. Cənuba baxır, gün "
            "ərzində ən işıqlı otaqdır.",
            "Pəncərəsi küçəyə açılır. Küçə dar və piyada axını azdır, amma səhər "
            "saat 8-dən sonra qonşu çörək sexinin səsi eşidilə bilər — bunu əvvəlcədən "
            "deyirik ki, sonra sürpriz olmasın.",
        ),
        features=("22,1 m² döşəmə sahəsi", "İki ayrı 90 sm çarpayı",
                  "Cənuba baxan iki pəncərə", "Səhər küçə səsi eşidilir"),
        plan=Plan(w=400, h=550,
                  bath=(0, 390, 175, 160),
                  bed=((60, 60, 90, 200), (220, 60, 90, 200)),
                  windows=((80, 0, 110, 8), (240, 0, 110, 8)),
                  door=(0, 250, 8, 90),
                  extras=((200, 350, 160, 55, "masa"),)),
    ),
    Room(
        slug="firuze", name="Firuzə", kind="Şüşəbəndli iki nəfərlik", glass="firuzəyi",
        hex_light="#0E7186", hex_dark="#63BFD4", base=155, sleeps=2, size_m2=24.6,
        floor=1, steps=17, bed_cm="160 × 200", aspect="həyətə, şüşəbənd",
        bathroom="Duş", lift=False, pattern="ulduz8", density=7,
        lede="Otağın həyətə baxan tərəfi şüşəbənddir — çay içmək üçün ayrıca oturacaq.",
        body=(
            "Şüşəbənd, Şəki evlərinin şüşə ilə örtülmüş eyvanıdır. Burada 4,1 m²-lik "
            "hissə ondan ibarətdir: iki kreslo, alçaq masa, üç tərəfi pəncərə.",
            "Şüşəbənd qışda da istifadə olunur, radiator oraya da çəkilib. Yayda "
            "axşamlar orada oturmaq otaqdan sərin olur.",
        ),
        features=("24,6 m² — 4,1 m²-i şüşəbənd", "Şüşəbənddə iki kreslo və masa",
                  "160 sm çarpayı", "Şüşəbənd qışda da isidilir"),
        plan=Plan(w=420, h=585,
                  bath=(0, 425, 180, 160),
                  bed=((60, 60, 160, 200),),
                  windows=((412, 90, 8, 260), (150, 0, 120, 8)),
                  door=(0, 300, 8, 90),
                  extras=((290, 60, 130, 315, "şüşəbənd"), (230, 430, 150, 60, "masa"))),
    ),
    Room(
        slug="zeytun", name="Zeytun", kind="Çardaq otağı", glass="zeytunu",
        hex_light="#5C7A15", hex_dark="#A8C765", base=125, sleeps=2, size_m2=21.0,
        floor=2, steps=34, bed_cm="140 × 200", aspect="dama və dağlara, qərb",
        bathroom="Duş", lift=False, pattern="carpaz", density=8,
        lede="Ən yuxarı mərtəbə, mailli tavan. Qərbə baxır, günbatımı pəncərədən görünür.",
        body=(
            "Tavan çarpayının baş tərəfində 2,4 m, pəncərə tərəfində 1,7 m-ə enir. "
            "Uzun boylu qonaqlar üçün bunu ayrıca qeyd edirik.",
            "34 pillə var və lift yoxdur. Bunun əvəzində şəhərin damlarına və "
            "arxadakı dağ silsiləsinə açılan mənzərə bu evdə yalnız buradan görünür.",
        ),
        features=("21,0 m² döşəmə sahəsi", "Mailli tavan: 2,4 m-dən 1,7 m-ə",
                  "34 pillə, lift yoxdur", "Qərbə baxan mənzərə"),
        plan=Plan(w=350, h=600,
                  bath=(0, 440, 160, 160),
                  bed=((175, 60, 140, 200),),
                  windows=((342, 200, 8, 140), (120, 0, 120, 8)),
                  door=(0, 280, 8, 85),
                  extras=((175, 300, 150, 60, "masa"), (0, 60, 65, 140, "şkaf"))),
    ),
    Room(
        slug="yaqut", name="Yaqut", kind="Balkonlu iki nəfərlik", glass="yaqut",
        hex_light="#B0243C", hex_dark="#F0899C", base=170, sleeps=2, size_m2=26.4,
        floor=1, steps=17, bed_cm="180 × 200", aspect="həyətə, balkon",
        bathroom="Vanna və duş", lift=False, pattern="sekkizguse", density=6,
        lede="Evin ən böyük ikinəfərlik otağı. Yeganə vannalı otaq və 180 sm çarpayı.",
        body=(
            "Vanna otağında həm oturma vannası, həm ayrıca duş var — evdə vannası olan "
            "tək otaqdır. Çarpayı 180 sm, digər otaqlardakından 20 sm genişdir.",
            "Balkon 3,2 m² və həyətə baxır. Səhər yeməyini otağa gətirmək istəsəniz "
            "əlavə ödəniş yoxdur, sadəcə axşamdan deyin.",
        ),
        features=("26,4 m² — üstəgəl 3,2 m² balkon", "Evdə yeganə vannalı otaq",
                  "180 sm çarpayı", "Səhər yeməyi otağa gətirilir"),
        plan=Plan(w=440, h=600,
                  bath=(0, 410, 200, 190),
                  bed=((220, 60, 180, 200),),
                  windows=((432, 130, 8, 170),),
                  door=(0, 270, 8, 90),
                  extras=((215, 330, 170, 60, "komod"), (0, 60, 80, 150, "şkaf"),
                          (230, 600, 190, 55, "balkon"))),
    ),
    Room(
        slug="zumrud", name="Zümrüd", kind="Ailə otağı", glass="zümrüd",
        hex_light="#1D7A5A", hex_dark="#63C39D", base=210, sleeps=4, size_m2=34.2,
        floor=0, steps=3, bed_cm="160 × 200 və 2 × (90 × 190)", aspect="həyətə, şərq",
        bathroom="Duş, əlavə əl yuyucusu", lift=False, pattern="altibucaq", density=6,
        lede="Dörd nəfər üçün. Uşaq çarpayıları alçaq arakəsmə ilə ayrılıb.",
        body=(
            "Otaq bir mərtəbədədir, iki hissəyə bölünüb: valideynlər üçün 160 sm "
            "çarpayı, 120 sm hündürlüyündə taxta arakəsmədən sonra iki uşaq çarpayısı. "
            "Qapı yoxdur, arakəsmə səs keçirir — bunu bilərək seçin.",
            "Vanna otağında böyüklər üçün duş və uşaqlar üçün alçaq əl yuyucusu var. "
            "Beşik pulsuzdur, əvvəlcədən deyin.",
        ),
        features=("34,2 m² döşəmə sahəsi", "Arakəsmə 120 sm — qapı deyil",
                  "Beşik pulsuz, əvvəlcədən sifariş", "Həyət səviyyəsi, 3 pillə"),
        plan=Plan(w=520, h=660,
                  bath=(0, 480, 210, 180),
                  bed=((260, 60, 160, 200), (60, 60, 90, 190), (165, 60, 90, 190)),
                  windows=((512, 150, 8, 180), (512, 400, 8, 120)),
                  door=(0, 300, 8, 95),
                  extras=((0, 290, 250, 12, "arakəsmə"), (260, 320, 180, 60, "komod"))),
    ),
    Room(
        slug="gulabi", name="Gülabı", kind="Kiçik lyuks", glass="gülabı",
        hex_light="#A83A6E", hex_dark="#EE94BD", base=245, sleeps=2, size_m2=38.5,
        floor=1, steps=17, bed_cm="180 × 200", aspect="həyətə və küçəyə, iki tərəf",
        bathroom="Vanna, ayrıca duş", lift=False, pattern="sekkizguse", density=8,
        lede="İki pəncərəli künc otağı, ayrıca oturma hissəsi ilə. Evin ən böyük otağı.",
        body=(
            "Künc otağıdır: bir pəncərə həyətə, biri küçəyə baxır. Oturma hissəsi "
            "divanla ayrılıb, iş üçün ayrıca masa var.",
            "Otağın şəbəkə pəncərəsi evdəki ən böyüyüdür — 1,4 × 1,8 m, 412 şüşə "
            "parçasından ibarətdir. Onu saymaq bizim işimiz oldu, sizin yox.",
        ),
        features=("38,5 m² döşəmə sahəsi", "İki tərəfi pəncərə, künc otağı",
                  "Ayrıca oturma hissəsi və divan", "Evdəki ən böyük şəbəkə pəncərə"),
        plan=Plan(w=550, h=700,
                  bath=(0, 500, 230, 200),
                  bed=((290, 60, 180, 200),),
                  windows=((542, 140, 8, 190), (180, 0, 190, 8)),
                  door=(0, 320, 8, 95),
                  extras=((60, 430, 190, 70, "divan"), (290, 330, 180, 60, "masa"),
                          (0, 60, 80, 160, "şkaf"))),
    ),
)

ROOM_BY_SLUG = {r.slug: r for r in ROOMS}


def price(room: Room, day: dt.date) -> int:
    """All in: ƏDV and breakfast included. Rounded to the nearest 5 ₼.

    math.floor(x + 0.5) rather than round(), because round() is banker's rounding
    and JavaScript's Math.round is not. The reservation form recomputes this number
    in the browser and the two have to land on the same ₼.
    """
    raw = room.base * season_for(day).factor
    return int(math.floor(raw / 5.0 + 0.5) * 5)


def price_range(room: Room) -> tuple:
    vals = [price(room, d) for d in season_days()]
    return min(vals), max(vals)


def season_days():
    d = SEASON_START
    while d <= SEASON_END:
        yield d
        d += dt.timedelta(days=1)


def calendar_months() -> list:
    """The twelve (year, month) pairs the published calendar covers."""
    out, y, m = [], SEASON_START.year, SEASON_START.month
    for _ in range(12):
        out.append((y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


# --- Restaurant -------------------------------------------------------------

@dataclass(frozen=True)
class Dish:
    name: str
    price: int
    desc: str
    tags: tuple = ()


MENU = {
    "Səhər yeməyi": (
        Dish("Şəki qayğanağı", 0,
             "Kənd yumurtası, quyruq yağı, təzə göyərti. Otaq qiymətinə daxildir.",
             ("qiymətə daxil",)),
        Dish("Ev pendiri və bal", 0,
             "Qaymaq, ev pendiri, dağ balı, təndir çörəyi. Otaq qiymətinə daxildir.",
             ("qiymətə daxil", "vegetarian")),
        Dish("Sıyıq", 0, "Süddə darı sıyığı, üstünə qoz. Otaq qiymətinə daxildir.",
             ("qiymətə daxil", "vegetarian")),
    ),
    "Əsas yeməklər": (
        Dish("Piti", 14, "Quzu, noxud, alça, quyruq. Fərdi saxsı qabda, 3 saat bişir. "
                         "Axşam üçün günorta saat 12-yə qədər sifariş olunmalıdır.",
             ("sifarişlə",)),
        Dish("Sac içi", 16, "Quzu əti, kartof, bibər, pomidor — sacda, həyətdə bişirilir."),
        Dish("Dolma", 12, "Üç növ: yarpaq, bibər, badımcan. Yay aylarında təzə yarpaqla."),
        Dish("Qarnıyarıq", 11, "Badımcan, qiymə, pomidor sousu."),
        Dish("Göy kükü", 9, "Yaşıl göyərti və yumurta. Ət yoxdur.", ("vegetarian",)),
    ),
    "Şirniyyat": (
        Dish("Şəki halvası", 6, "Düyü unu, qoz, şəkər şərbəti, zəfəran. Şəhərdəki "
                                "emalatxanadan gündəlik gətirilir.", ("yerli",)),
        Dish("Peşməkli çay", 7, "Peşmək və dağ otları çayı, armud stəkanda.",
             ("vegetarian",)),
        Dish("Qoz mürəbbəsi", 5, "Yaşıl qozdan, evdə bişirilib.", ("vegetarian",)),
    ),
}

MENU_NOTE = ("Qiymətlərə ƏDV daxildir. Səhər yeməyi otaq qiymətinə daxildir və "
             "08:00-10:30 arası həyətdə, hava pis olanda yeməkxanada verilir.")


# --- Guide (the tourism leg) ------------------------------------------------

@dataclass(frozen=True)
class Article:
    slug: str
    title: str
    lede: str
    minutes: int
    walk: str            # distance from the guesthouse
    body: tuple          # (heading, paragraph, paragraph, ...) blocks
    facts: tuple = ()    # (label, value) pairs


ARTICLES = (
    Article(
        slug="xan-sarayi",
        title="Şəki Xan Sarayı və şəbəkə pəncərənin necə yığıldığı",
        lede="Mismarsız, yapışqansız, 5000-dən çox taxta və şüşə parçası. Sarayı "
             "görməzdən əvvəl nəyə baxacağınızı bilmək işə yarayır.",
        minutes=6, walk="Qonaq evindən 900 m, piyada 12 dəqiqə",
        body=(
            ("Nə üçün mismarsız",
             "Şəbəkə taxta çubuqların bir-birinə oyulmuş yuvalarla keçirilməsi ilə "
             "yığılır. Metal istidə və soyuqda taxtadan fərqli genişləndiyi üçün "
             "mismar şüşəni sındırardı. Konstruksiya sökülüb yenidən yığıla bilir — "
             "bərpa işlərinin mümkün olmasının səbəbi budur.",
             "Bir kvadratmetr şəbəkəyə orta hesabla 5000-ə yaxın ayrıca hissə düşür. "
             "Usta hissələri əvvəlcə quru yığır, ölçünü yoxlayır, sonra şüşəni salır."),
            ("Rəngli şüşə haradan gəlir",
             "Tarixən şüşə Venesiyadan gətirilib. Bu gün bərpada istifadə olunan şüşənin "
             "böyük hissəsi Rusiya və Türkiyə istehsalıdır; rəng palitrası orijinala "
             "uyğunlaşdırılır, amma eyni deyil.",
             "Sarayın ikinci mərtəbəsində günorta saat 13-14 arası işıq şəbəkədən "
             "keçib divara düşür. Turist qrupları adətən səhər gəlir; bu saatı seçsəniz "
             "həm sakit olur, həm rəng görünür."),
            ("Praktik məlumat",
             "Saray 1762-ci ildə tikilib, 2019-cu ildə Şəkinin tarixi mərkəzi ilə "
             "birlikdə UNESCO Dünya İrsi siyahısına salınıb. Daxildə foto çəkilişi "
             "məhduddur, həyətdə sərbəstdir."),
        ),
        facts=(("Tikildiyi il", "1762"), ("UNESCO siyahısı", "2019"),
               ("Qonaq evindən", "900 m, 12 dəqiqə piyada"),
               ("Ən yaxşı saat", "13:00-14:00, işıq üçün")),
    ),
    Article(
        slug="seki-halvasi",
        title="Şəki halvası: on iki qat, bir tava, iki nəfər",
        lede="Şəhərdə onlarla emalatxana var və hamısı eyni halvanı bişirmir. Fərqi "
             "nədə axtarmaq lazımdır.",
        minutes=5, walk="Yuxarı Baş bazarı, qonaq evindən 600 m",
        body=(
            ("Qatın sayı fərq edir",
             "Şəki halvası düyü unundan hazırlanan nazik rişdə qatlarından yığılır. "
             "Ənənəvi resept 8-12 qat tələb edir. Ucuz variantlarda qat sayı 5-6-ya "
             "düşür və halva quru olur — kəsikdən baxanda qatları saymaq mümkündür.",
             "Şərbət zəfəranla rənglənir. Parlaq narıncı rəng adətən zəfəran deyil, "
             "qida boyasıdır; zəfəranın rəngi daha solğun və qeyri-bərabər olur."),
            ("Nə vaxt almaq lazımdır",
             "Halva bişdiyi gün ən yaxşısıdır. Emalatxanalar səhər 9-11 arası bişirir. "
             "Günorta gedəndə axşamdan qalan tavadan kəsilə bilər.",
             "Bir kiloqram 2-3 nəfər üçün çoxdur. 300-400 qram istəmək normaldır və "
             "heç kim təəccüblənmir."),
            ("Qonaq evində",
             "Halvanı biz bişirmirik — Yuxarı Başdakı emalatxanadan gündəlik alırıq. "
             "Səhər yeməyində bir dilim verilir; artıq istəsəniz menyudadır."),
        ),
        facts=(("Ənənəvi qat sayı", "8-12"), ("Bişmə saatı", "səhər 09:00-11:00"),
               ("Ağlabatan porsiya", "300-400 q"), ("Qonaq evindən", "600 m")),
    ),
    Article(
        slug="kis-kilsesi",
        title="Kiş kilsəsi: qazıntı çuxurunun üstündəki şüşə niyə vacibdir",
        lede="Qafqazın ən qədim kilsə binalarından biri. Ən maraqlı hissəsi divarlar "
             "deyil, döşəmədəki çuxurlardır.",
        minutes=5, walk="Qonaq evindən 5,5 km, avtomobil və ya taksi ilə 12 dəqiqə",
        body=(
            ("Döşəmədəki şüşə",
             "Kilsənin içində döşəmənin bir hissəsi şüşə ilə örtülüb. Altında Norveç "
             "arxeoloqu Turbyorn Bilyerinin 2000-2003-cü illərdə apardığı qazıntılarda "
             "tapılmış dəfnlər var.",
             "Sümüklərin bəziləri bina tikilməmişdən əvvəlki dövrə aiddir. Yəni yer "
             "kilsədən əvvəl də müqəddəs sayılırdı — bina köhnə ibadət yerinin üstünə "
             "qoyulub."),
            ("Nə vaxt getmək",
             "Kənd yolu dardır, iki avtobus qarşılaşanda gözləmək lazım gəlir. Səhər "
             "10-a qədər və ya günorta 15-dən sonra sərnişin axını azalır.",
             "Kilsənin özü kiçikdir, içəridə 20 dəqiqə bəs edir. Amma kəndin özündə "
             "gəzmək üçün bir saat ayırmağa dəyər."),
        ),
        facts=(("Qazıntı illəri", "2000-2003"), ("Qonaq evindən", "5,5 km"),
               ("Daxildə vaxt", "təxminən 20 dəqiqə"),
               ("Sakit saat", "10:00-a qədər və ya 15:00-dan sonra")),
    ),
    Article(
        slug="dord-movsum",
        title="Şəkiyə hansı ayda gəlmək: dörd mövsümün dürüst müqayisəsi",
        lede="Hər ayın öz problemi var. Qiymət təqvimimizdəki fərqin səbəbi də budur.",
        minutes=7, walk="—",
        body=(
            ("Qış: yanvar-fevral",
             "Ən ucuz aylar. Şəhər boş olur, Xan Sarayında növbə yoxdur. Qar yağır və "
             "dağ yolları bəzən bağlanır — Kiş və yaylaq planlarını qışa qurmayın.",
             "Evdə mərkəzi qızdırma var, amma köhnə binadır: pəncərələr qalın deyil. "
             "Çardaq otağı (Zeytun) qışda digərlərindən sərin olur."),
            ("Yaz: mart-may",
             "Novruz beş gün şəhəri doldurur, qiymət ən yüksək həddə çıxır və otaqlar "
             "adətən fevralda bitir. Novruzdan sonra aprel-may ilin ən rahat aylarıdır: "
             "15-22 dərəcə, bağlar çiçəkdə, turist axını orta.",
             "Aprel yağışlıdır. Bir gün gəzinti planlaşdırırsınızsa iki gün ayırın."),
            ("Yay: iyun-avqust",
             "Bakıdan sərinliyə qaçanların mövsümü. Şəkidə temperatur Bakıdan 6-8 dərəcə "
             "aşağı olur. Həyət axşamlar dolu olur, sakitlik axtaranlar üçün ideal deyil.",
             "İyul-avqustda həftə sonları üçün ən azı üç həftə əvvəldən yer saxlamaq "
             "lazımdır."),
            ("Payız: sentyabr-noyabr",
             "Bizim fikrimizcə ilin ən yaxşı vaxtı. Sentyabr hələ istidir, oktyabrda "
             "çinarlar saralır, turist sayı yayın yarısına düşür.",
             "Noyabrın ortasından sonra hava dəyişkən olur və qiymət sakit mövsümə "
             "düşür."),
        ),
        facts=(("Ən ucuz", "yanvar-fevral"), ("Ən bahalı", "Novruz və Yeni il"),
               ("Ən rahat hava", "aprel-may, sentyabr-oktyabr"),
               ("Ən çox dolu", "iyul-avqust həftə sonları")),
    ),
)

ARTICLE_BY_SLUG = {a.slug: a for a in ARTICLES}


# --- Reviews ----------------------------------------------------------------

@dataclass(frozen=True)
class Review:
    author: str
    city: str
    stars: int
    date: str            # dd.MM.yyyy
    room: str            # slug
    text: str


REVIEWS = (
    Review("Nərmin Ə.", "Bakı", 5, "12.10.2026", "yaqut",
           "Saytda yazılan qiymət nə isə, qapıda ödədiyimiz də o oldu. Əlavə heç nə "
           "çıxmadı. Bunun nə qədər nadir olduğunu bilirsinizmi."),
    Review("Rəşad M.", "Gəncə", 5, "03.10.2026", "kehreba",
           "Otağın küçəyə baxdığını və səhər səs olacağını əvvəlcədən yazmışdılar. "
           "Səs oldu, amma xəbərim vardı deyə problem olmadı."),
    Review("Aygün S.", "Bakı", 4, "28.09.2026", "zeytun",
           "Mənzərə əladır, amma 34 pillə zarafat deyil. Saytda yazılıb, oxumamışam — "
           "öz günahım."),
    Review("Tural H.", "Sumqayıt", 5, "19.09.2026", "zumrud",
           "İki uşaqla gəldik. Arakəsmənin qapı olmadığı yazılmışdı, elə də idi. "
           "Beşik pulsuz gətirdilər."),
    Review("Leyla Q.", "Bakı", 5, "07.09.2026", "firuze",
           "Şüşəbənddə səhər çayı içmək üçün gəlməyə dəyər. Axşamlar sərin olur."),
    Review("Emin V.", "Bakı", 4, "22.08.2026", "lacivard",
           "Anam üçün üç pilləli otağı seçdik, doğru qərar oldu. Kaş liftli otel "
           "olaydı, amma köhnə evdə lift gözləmək düzgün deyil."),
    Review("Səbinə R.", "Şəki", 5, "14.08.2026", "gulabi",
           "Şəkidənəm, qonaqlarımı burada yerləşdirdim. Şəbəkə pəncərəsinə görə "
           "seçdim, düz seçmişəm."),
    Review("Kamran İ.", "Bakı", 5, "30.07.2026", "benovse",
           "Tək gəldim, kiçik otaq kifayət etdi. Qiymət təqvimi olduğu üçün ucuz "
           "həftəni seçib gəldim."),
    Review("Günel A.", "Bakı", 4, "11.07.2026", "yaqut",
           "Vanna otağı əla. Səhər yeməyi 10:30-da bitir, bir az gec olsa yaxşı olardı."),
    Review("Orxan T.", "Mingəçevir", 5, "26.06.2026", "kehreba",
           "Piti günorta 12-yə qədər sifariş olunmalıdır — bunu bilmirdim, xəbərdarlıq "
           "etdilər, ertəsi gün yedik. Dəyərdi."),
    Review("Sevinc B.", "Bakı", 5, "08.06.2026", "firuze",
           "Otaq pasportu deyilən hissə — m², pillə sayı, çarpayı ölçüsü — heç bir "
           "otelin saytında görməmişdim. Çox faydalıdır."),
    Review("Vüqar N.", "Bakı", 4, "21.05.2026", "zeytun",
           "Tavan alçalır, 1,90 boyum var, bir-iki dəfə vurdum. Yazılıb, oxumaq lazımdır."),
)

RATING = round(sum(r.stars for r in REVIEWS) / len(REVIEWS), 1)


# --- House rules / FAQ ------------------------------------------------------

FAQ = (
    ("Neçədə yerləşmək və çıxmaq olar",
     f"Yerləşmə {CHECKIN}-dan, çıxış {CHECKOUT}-yə qədər. Erkən gəlirsinizsə "
     "çamadanınızı saxlayırıq, əlavə ödəniş yoxdur. Gec çıxış boş otaq olanda "
     "mümkündür, günorta saat 10-a qədər soruşun."),
    ("Ləğv şərtləri nədir",
     "Gəlişdən 7 gün əvvəlinə qədər ləğv pulsuzdur. 7 gündən az qalıbsa bir gecənin "
     "qiyməti tutulur. Novruz və Yeni il tarixlərində ləğv 14 gün əvvəl pulsuzdur."),
    ("Ödənişi necə etmək lazımdır",
     "Nağd və ya kartla, yerində. Əvvəlcədən ödəniş və depozit tələb etmirik. "
     "Sayt ödəniş qəbul etmir."),
    ("Qiymətə nə daxildir",
     "ƏDV, səhər yeməyi, Wi-Fi, çay-qəhvə. Şəhər vergisi yoxdur. Saytda gördüyünüz "
     "rəqəm ödəyəcəyiniz rəqəmdir."),
    ("Uşaqlar üçün nə var",
     "6 yaşa qədər uşaqlar valideynlərin otağında pulsuz qalır. Beşik pulsuzdur, "
     "əvvəlcədən sifariş edin. Ailə otağı (Zümrüd) dörd nəfərlikdir."),
    ("Heyvanla gəlmək olarmı",
     "Kiçik ev heyvanları ilə qəbul edirik, gecəyə 10 ₼ təmizlik haqqı ilə. "
     "Rezervasiya zamanı qeyd edin — bütün otaqlar uyğun deyil."),
    ("Avtomobil saxlamaq üçün yer varmı",
     "Həyətdə üç avtomobillik yer var, pulsuz və növbə ilə. Dolu olanda 150 m "
     "aralıda küçə parklanması sərbəstdir."),
    ("Siqaret çəkmək olarmı",
     "Otaqların içində yox. Həyətdə və şüşəbənddə pəncərə açıq olmaqla mümkündür."),
    ("Liftiniz varmı",
     "Yoxdur. Bina 1920-ci illərin evidir. Hər otağın səhifəsində qapıya neçə pillə "
     "olduğu yazılıb — Lacivərd və Zümrüd üçün cəmi üç pillədir."),
    ("Aeroport və ya avtovağzaldan necə gəlmək olar",
     "Şəki avtovağzalından qonaq evinə taksi 5-7 ₼. Bakıdan avtobus 5 saat, qatar "
     "gecə reysi ilə 9 saat. Qarşılama xidmətimiz yoxdur."),
)


# --- Self-validation --------------------------------------------------------

def _check() -> None:
    # Seasons cover every day of both calendar years exactly once.
    for year in (2026, 2027):
        d = dt.date(year, 1, 1)
        while d.year == year:
            hits = [s.key for s in SEASONS
                    for m1, d1, m2, d2 in s.spans
                    if (m1, d1) <= (d.month, d.day) <= (m2, d2)]
            assert len(hits) == 1, f"{d:%d.%m.%Y} is covered by {hits or 'nothing'}"
            d += dt.timedelta(days=1)

    # Rooms: unique slugs, unique colours, plan agrees with the advertised size.
    assert len({r.slug for r in ROOMS}) == len(ROOMS), "duplicate room slug"
    assert len({r.hex_light for r in ROOMS}) == len(ROOMS), "duplicate glass colour"
    assert len(ROOMS) == ROOM_COUNT, f"ROOM_COUNT says {ROOM_COUNT}"
    for r in ROOMS:
        drawn = r.plan.area_m2
        assert abs(drawn - r.size_m2) <= 0.35, (
            f"{r.name}: plan draws {drawn} m² but the page advertises {r.size_m2} m²")
        # The bed has to fit inside the room, with its stated dimensions.
        for bx, by, bw, bh in r.plan.bed:
            assert 0 <= bx and bx + bw <= r.plan.w and 0 <= by and by + bh <= r.plan.h, \
                f"{r.name}: a bed hangs outside the walls"
        # The bathroom must not sit on top of a bed.
        if r.plan.bath:
            ax, ay, aw, ah = r.plan.bath
            for bx, by, bw, bh in r.plan.bed:
                overlap = (ax < bx + bw and bx < ax + aw
                           and ay < by + bh and by < ay + ah)
                assert not overlap, f"{r.name}: bathroom overlaps a bed"
        # Colour has to be readable, in both schemes.
        cl = contrast(r.hex_light, SURFACE_LIGHT)
        cd = contrast(r.hex_dark, SURFACE_DARK)
        assert cl >= 4.5, f"{r.name}: {r.hex_light} on white is only {cl:.2f}:1"
        assert cd >= 4.5, f"{r.name}: {r.hex_dark} on dark is only {cd:.2f}:1"

    # Every review points at a room that exists, and the average is what we publish.
    for rv in REVIEWS:
        assert rv.room in ROOM_BY_SLUG, f"review by {rv.author} names no real room"
        assert 1 <= rv.stars <= 5
    assert abs(RATING - sum(r.stars for r in REVIEWS) / len(REVIEWS)) < 0.05

    # Every room has at least one review, so no room page shows an empty section.
    reviewed = {rv.room for rv in REVIEWS}
    missing = [r.slug for r in ROOMS if r.slug not in reviewed]
    assert not missing, f"no review for: {', '.join(missing)}"

    # The published window is exactly twelve months.
    assert len(calendar_months()) == 12
    assert (SEASON_END - SEASON_START).days + 1 == 365

    # Menu prices: only the breakfast dishes are free.
    for section, dishes in MENU.items():
        for d in dishes:
            if d.price == 0:
                assert "qiymətə daxil" in d.tags, f"{d.name} is free but not marked"
            else:
                assert d.price > 0

    # Articles: unique slugs, every block has a heading and at least one paragraph.
    assert len({a.slug for a in ARTICLES}) == len(ARTICLES)
    for a in ARTICLES:
        for block in a.body:
            assert len(block) >= 2, f"{a.slug}: a block with no paragraph"


_check()


if __name__ == "__main__":
    lo_all = min(price_range(r)[0] for r in ROOMS)
    hi_all = max(price_range(r)[1] for r in ROOMS)
    print(f"{BRAND_FULL} — {len(ROOMS)} rooms, {lo_all}-{hi_all} ₼")
    print(f"{'room':10} {'m²':>6} {'plan':>6} {'floor':>5} {'steps':>5} "
          f"{'base':>5} {'low':>5} {'high':>5}")
    for r in ROOMS:
        lo, hi = price_range(r)
        print(f"{r.slug:10} {r.size_m2:6.1f} {r.plan.area_m2:6.1f} {r.floor:5} "
              f"{r.steps:5} {r.base:5} {lo:5} {hi:5}")
    print()
    for s in SEASONS:
        n = sum(1 for d in season_days() if season_for(d).key == s.key)
        print(f"{s.name:18} ×{s.factor:.2f}  {n:3} gecə")
    print(f"\nrating {RATING} from {len(REVIEWS)} reviews; "
          f"{sum(len(v) for v in MENU.values())} dishes; {len(ARTICLES)} articles")
