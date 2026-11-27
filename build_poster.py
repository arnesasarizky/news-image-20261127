#!/usr/bin/env python3
"""Build the news poster for news-image-20261127.

Draws the whole 1024x1024 broadsheet from scratch with Pillow:
37 stories (13 pictured cards + 24 briefs), region strip, six-number
strip, timeline, world-map panel with numbered pins, DATE CHECK box.
Deterministic: fixed seed, no clock, no network, no external assets.
Writes entry.png in the repo root.
"""
import math
import random
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = "entry.png"

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def F(path, size):
    return ImageFont.truetype(path, size)


# ---- palette ----
PAPER = (246, 241, 229)
INK = (22, 22, 34)
NAVY = (20, 32, 61)
NAVY2 = (28, 46, 88)
RED = (178, 35, 42)
GOLD = (201, 162, 39)
TEAL = (15, 118, 110)
CARD = (255, 253, 246)
MUTED = (90, 86, 76)
LINE = (180, 172, 152)

REGION_COLORS = {
    "MIDDLE EAST": (178, 35, 42),
    "EUROPE": (29, 78, 216),
    "NORTH AMERICA": (15, 118, 110),
    "ASIA": (180, 83, 9),
    "AFRICA": (77, 124, 15),
    "OCEANIA": (124, 58, 237),
    "LATIN AMERICA": (219, 39, 119),
}

# ---- text helpers ----
def wrap(text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.getlength(trial) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(d, x, y, text, font, color, max_w, lh=None, max_lines=None):
    lines = wrap(text, font, max_w)
    if max_lines:
        lines = lines[:max_lines]
    lh = lh or int(font.size * 1.18)
    for i, ln in enumerate(lines):
        d.text((x, y + i * lh), ln, font=font, fill=color)
    return y + len(lines) * lh


def text_w(text, font):
    return font.getlength(text)


# ---- drawing helpers ----
def vgrad(w, h, stops):
    """Vertical gradient through colour stops; returns RGB image."""
    base = Image.new("RGB", (1, 256))
    px = []
    n = len(stops) - 1
    for i in range(256):
        t = i / 255.0 * n
        k = min(int(t), n - 1)
        f = t - k
        a, b = stops[k], stops[k + 1]
        px.append(tuple(int(a[c] + (b[c] - a[c]) * f) for c in range(3)))
    base.putdata(px)
    return base.resize((w, h))


def hgrad(w, h, stops):
    return vgrad(h, w, stops).rotate(-90, expand=True).resize((w, h))


def noise_tile(seed=42, size=128, amp=14):
    rnd = random.Random(seed)
    img = Image.new("L", (size, size))
    img.putdata([rnd.randint(0, 255) for _ in range(size * size)])
    return img


def apply_noise(img, seed=42, alpha=0.12):
    """Blend a deterministic per-channel noise pattern for colour richness."""
    def channel(s):
        rnd = random.Random(s)
        t = Image.new("L", (128, 128))
        t.putdata([rnd.randint(0, 255) for _ in range(128 * 128)])
        layer = Image.new("L", img.size)
        for yy in range(0, img.size[1], 128):
            for xx in range(0, img.size[0], 128):
                layer.paste(t, (xx, yy))
        return layer
    noise_rgb = Image.merge("RGB", (channel(seed), channel(seed + 1), channel(seed + 2)))
    return Image.blend(img, noise_rgb, alpha)


def sun(d, cx, cy, r, core, halo):
    for i in range(3, 0, -1):
        d.ellipse([cx - r * i, cy - r * i, cx + r * i, cy + r * i], fill=halo)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=core)


def cloud(d, x, y, s, color, alpha_img=None):
    d.ellipse([x, y, x + 3 * s, y + 1.4 * s], fill=color)
    d.ellipse([x + 0.6 * s, y - 0.7 * s, x + 2.6 * s, y + 0.9 * s], fill=color)
    d.ellipse([x + 1.6 * s, y - 0.3 * s, x + 3.4 * s, y + 1.1 * s], fill=color)


def star(d, cx, cy, r, color):
    pts = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy - rr * math.sin(ang)))
    d.polygon(pts, fill=color)


def building(d, x, y0, w, h, color, win=(250, 220, 120)):
    d.rectangle([x, y0 - h, x + w, y0], fill=color)
    for wy in range(y0 - h + 6, y0 - 4, 12):
        for wx in range(x + 4, x + w - 5, 10):
            d.rectangle([wx, wy, wx + 5, wy + 7], fill=win)


def pine(d, x, y0, s, color):
    d.polygon([(x, y0 - 3.2 * s), (x - 1.1 * s, y0 - 0.6 * s), (x + 1.1 * s, y0 - 0.6 * s)], fill=color)
    d.polygon([(x, y0 - 2.4 * s), (x - 1.4 * s, y0 + 0.4 * s), (x + 1.4 * s, y0 + 0.4 * s)], fill=color)
    d.rectangle([x - 0.18 * s, y0 + 0.4 * s, x + 0.18 * s, y0 + 1.0 * s], fill=(90, 60, 30))

# ---- story data: (num, region, dateline, headline, deck, source, status, art) ----
# status: None, "REPORTED", "CONFIRMED", "CLAIM"
PICTURED = [
    (1, "MIDDLE EAST", "KUWAIT CITY", "DRONES KILL TWO ITALIANS AT KUWAIT AIR-DEFENCE SITE",
     "Rheinmetall technicians die as drones hit a radar station; Kuwait and Italy blame Iran. Tehran denies any role.",
     "REUTERS", "CLAIM", "kuwait"),
    (2, "NORTH AMERICA", "US EAST COAST", "THANKSGIVING STORM CUTS POWER TO 961,000 HOMES",
     "Gusts of 70 mph fell trees and lines from Virginia to New York; hundreds of flights cancelled or delayed.",
     "AP", "CONFIRMED", "storm"),
    (3, "MIDDLE EAST", "GAZA", "ISRAELI STRIKES KILL 10 IN GAZA; HAMAS WEIGHS REPLY",
     "Five strikes and a shooting overnight; a Hamas finance chief is among the dead. The ceasefire strains.",
     "REUTERS", "REPORTED", "gaza"),
    (4, "EUROPE", "KYIV", "ZELENSKYY: RUSSIA READIES A NEW MASSIVE GRID STRIKE",
     "President warns of a fresh assault on energy and logistics.",
     "UKRINFORM", "REPORTED", "kyiv"),
    (5, "EUROPE", "IBIZA", "TANKER CAPSIZES OFF IBIZA WITH 7,000 TONNES OF DIESEL",
     "Med Emre lies keel-up; one dead, 17 rescued. Spain acts on pollution.",
     "REUTERS", "CONFIRMED", "ibiza"),
    (6, "EUROPE", "LONDON", "UK NET MIGRATION FALLS TO 77,000, LOWEST SINCE 1997",
     "ONS: 738,000 arrived, 661,000 left in the year to June \u2014 down 90%.",
     "BBC", "CONFIRMED", "migration"),
    (7, "EUROPE", "PARIS", "DEPARDIEU ORDERED TO STAND TRIAL OVER 2018 RAPE",
     "Paris appeals court rejects the actor's bid; he denies the charge.",
     "AP", "REPORTED", "paris"),
    (8, "ASIA", "HONG KONG", "HONG KONG MOURNS 168 DEAD, A YEAR AFTER THE TOWER FIRE",
     "Flowers and prayers at Wang Fuk Court as officials warn of \u2018disorder\u2019.",
     "AP", "CONFIRMED", "hongkong"),
    (9, "EUROPE", "LONDON", "TUBE DRIVERS BEGIN EIGHT DAYS OF WINTER STRIKES",
     "First 24-hour walkout ends at noon; Piccadilly and Circle lines halt.",
     "REUTERS", "CONFIRMED", "tube"),
    (10, "EUROPE", "COLOGNE", "GERMANY ARRESTS TWO IRAQIS OVER SYNAGOGUE PLOT",
     "17 raids, 250 officers; pair linked to an Iran-backed cell.",
     "REUTERS", "CLAIM", "cologne"),
    (11, "EUROPE", "GENEVA", "GUKESH\u2013SINDAROV GAME 3 DRAWN; MATCH LEVEL 1.5\u20131.5",
     "A 60-move Berlin thriller; Sindarov makes move 40 with six seconds left.",
     "CHESS.COM", "CONFIRMED", "chess"),
    (12, "NORTH AMERICA", "UNITED STATES", "BLACK FRIDAY: SHOPPERS CHASE ESSENTIALS, NOT LUXURY",
     "Doors open at 6am; Target gives gift cards to its first 100 guests.",
     "AP", "REPORTED", "blackfriday"),
    (13, "NORTH AMERICA", "UNITED STATES", "MUSK PLEDGES TWO SPACEX SHARES FOR EVERY US CHILD",
     "A gift worth about $18bn, hours after approval for 1m AI satellites.",
     "REUTERS", "REPORTED", "spacex"),
]

BRIEFS = [
    (14, "EUROPE", "BRUSSELS", "EU split over \u20ac45bn Ukraine loan; decision deferred",
     "24 states back the loan; budget talks stall. Leaders return to it in December.", "EUROPEAN COUNCIL"),
    (15, "EUROPE", "LONDON", "Britain puts 100,000 reservists on standby",
     "Retired military personnel contacted as drone threats rise \u2014 a first since the Cold War.", "BBC"),
    (16, "EUROPE", "FRANKFURT", "Spain\u2019s ex-central bank chief to lead the ECB",
     "Leaders choose the former Banco de Espa\u00f1a governor as the next ECB president.", "AP"),
    (17, "EUROPE", "CANARY ISLANDS", "Nearly 2,000 migrants reach Canaries in one day",
     "A record single-day arrival as crossings surge.", "AP"),
    (18, "EUROPE", "BERLIN", "Boat dealer \u2018supplied Channel smuggling gangs\u2019",
     "BBC investigation names a German dealer accused of arming the crossings trade.", "BBC"),
    (19, "EUROPE", "MADRID", "Spain\u2019s young voters weigh housing before Sunday\u2019s vote",
     "Rents top the agenda as the country heads to the polls.", "BBC"),
    (20, "MIDDLE EAST", "RIYADH", "Strike on Saudi refinery kills one worker",
     "A Nepali worker dies in the Jazan attack as Gulf tensions spread.", "REUTERS"),
    (21, "MIDDLE EAST", "JENTA, LEBANON", "Israeli strikes hit Lebanon\u2019s Jenta town",
     "Raids raise questions over Hezbollah\u2019s rebuilding.", "AP"),
    (22, "NORTH AMERICA", "WASHINGTON", "Trump tells Putin to \u2018pull back\u2019 in Europe",
     "President says a Ukraine deal is possible if Russia eases its aggression.", "AP"),
    (23, "NORTH AMERICA", "WASHINGTON", "Trump calls GDP data \u2018fake\u2019, demands a probe",
     "Attack on revised figures follows midterm losses.", "AP"),
    (24, "ASIA", "NAYPYIDAW", "Myanmar rejects parts of ICJ Rohingya ruling",
     "Government refuses elements of the crimes-against-humanity judgment.", "AP"),
    (25, "ASIA", "PYONGYANG", "Kim vows more nuclear weapons, snubs Trump",
     "North Korea\u2019s leader ignores the latest US overture.", "AP"),
    (26, "ASIA", "JIUQUAN", "China launches Shenzhou 24 with three aboard",
     "Two Chinese and one Pakistani astronaut head for orbit.", "AP"),
    (27, "ASIA", "DHAKA", "Tear gas as Bangladesh garment workers march",
     "Police disperse fresh protests over pay.", "AP"),
    (28, "ASIA", "ISLAMABAD", "Pakistan to host Saudi\u2013Turkey defence talks",
     "Trilateral pact treats an attack on one as an attack on all three.", "AP"),
    (29, "AFRICA", "BISSAU", "Guinea-Bissau junta delays civilian rule to 2028",
     "Military leaders extend their rule by two more years.", "AP"),
    (30, "AFRICA", "KINSHASA", "Ebola in DR Congo passes 12,000 cases",
     "Violence forces responders to evacuate as the outbreak grows.", "AP"),
    (31, "AFRICA", "CAPE TOWN", "South Africa\u2019s Biovac to scale up vaccine output",
     "An EU loan backs a big jump in local production.", "AP"),
    (32, "OCEANIA", "PERTH", "Lyon set to be dropped for first NZ Test",
     "Australia\u2019s great spinner, 577 Test wickets, faces the axe in Perth.", "ESPNCRICINFO"),
    (33, "OCEANIA", "SYDNEY", "Qantas and Air NZ jets too close at Sydney",
     "Aborted landing under investigation; crews\u2019 \u2018mental models\u2019 to be examined.", "GUARDIAN"),
    (34, "OCEANIA", "WELLINGTON", "NZ coalition falls one seat short of a majority",
     "Final count leaves a centrist newcomer as the decider.", "AP"),
    (35, "LATIN AMERICA", "MEXICO CITY", "Mexico\u2019s president blasts DEA over tip lines",
     "Accuses the agency of not fighting fentanyl enough inside the US.", "AP"),
    (36, "LATIN AMERICA", "SAN JOS\u00c9", "Costa Rica bars UN Palestine rapporteur",
     "Entry refused to the UN special rapporteur on Palestinian territories.", "AP"),
    (37, "LATIN AMERICA", "BRAS\u00cdLIA", "Brazil weighs inviting Argentine rival to Lula event",
     "An official besides Milei may get the call.", "AP"),
]

REGIONS = [
    ("MIDDLE EAST", 4), ("EUROPE", 13), ("NORTH AMERICA", 5), ("ASIA", 6),
    ("AFRICA", 3), ("OCEANIA", 3), ("LATIN AMERICA", 3),
]

NUMBERS = [
    ("961,000", "HOMES WITHOUT POWER, US STORM"),
    ("7,000", "TONNES OF DIESEL OFF IBIZA"),
    ("77,000", "UK NET MIGRATION AT 29-YEAR LOW"),
    ("168", "LIVES REMEMBERED IN HONG KONG"),
    ("\u20ac45bn", "EU LOAN FOR UKRAINE, 24 BACK IT"),
    ("100,000", "UK RESERVISTS TOLD TO PREPARE"),
]

TIMELINE = [
    ("00:00", "EU summit ends; \u20ac45bn loan deferred to Dec"),
    ("02:56", "US outages peak: 908,000 homes dark"),
    ("06:55", "Spain demands Med Emre salvage plan from owner"),
    ("11:00", "Black Friday doors open in US stores (6am ET)"),
    ("12:00", "London Tube strike ends; lines restart"),
]

DATE_CHECK = [
    ("CAIRO TANKER FIRE, 31 DEAD", "25 NOV"),
    ("MACY\u2019S PARADE POSTPONEMENT ANNOUNCED", "25 NOV"),
    ("BANGKOK REFINERY BLAST, 9 HURT", "26 NOV"),
    ("TRUMP 25% TARIFF ON INDIA PROPOSED", "26 NOV"),
    ("CARGO SHIP HALIMA SINKS OFF CUBA, 1 DEAD", "26 NOV"),
    ("GUARDIAN: 349 RUSSIANS DEAD IN MALI", "PUBLISHED 24 NOV"),
]

# ---- assertions: date discipline ----
assert len(PICTURED) == 13 and len(BRIEFS) == 24
ALL = PICTURED + BRIEFS
TOTAL = len(ALL)
assert [s[0] for s in ALL] == list(range(1, TOTAL + 1)), "story numbers must run 1..N"
assert sum(c for _, c in REGIONS) == TOTAL, "region counts must sum to story total"
from collections import Counter
cnt = Counter(s[1] for s in ALL)
for name, c in REGIONS:
    assert cnt[name] == c, (name, cnt[name], c)
assert len(NUMBERS) == 6
assert len(DATE_CHECK) == 6

# ---- flat-scene painters: each draws one pictured-card illustration ----
def scene_base(w, h, sky_stops, ground_y, ground_color):
    img = vgrad(w, h, sky_stops)
    d = ImageDraw.Draw(img)
    d.rectangle([0, ground_y, w, h], fill=ground_color)
    return img, d


def scene_kuwait(w, h):
    img, d = scene_base(w, h, [(44, 24, 60), (120, 52, 70), (214, 110, 60)], int(h * 0.72), (52, 34, 30))
    sun(d, int(w * 0.78), int(h * 0.30), 16, (255, 214, 130), (255, 170, 80))
    # radar dish on a mast
    mx, my = int(w * 0.30), int(h * 0.72)
    d.rectangle([mx - 3, my - 46, mx + 3, my], fill=(30, 28, 34))
    d.pieslice([mx - 34, my - 96, mx + 34, my - 28], 200, 340, fill=(232, 230, 222), outline=(90, 88, 82))
    d.line([mx - 30, my - 62, mx + 30, my - 62], fill=(90, 88, 82), width=2)
    # buildings
    building(d, int(w * 0.55), int(h * 0.72), 26, 34, (38, 30, 44))
    building(d, int(w * 0.66), int(h * 0.72), 20, 24, (46, 36, 50))
    # explosion glow + drones
    d.ellipse([int(w * 0.82) - 22, int(h * 0.55) - 22, int(w * 0.82) + 22, int(h * 0.55) + 22], fill=(255, 150, 40))
    d.ellipse([int(w * 0.82) - 11, int(h * 0.55) - 11, int(w * 0.82) + 11, int(h * 0.55) + 11], fill=(255, 230, 150))
    for dx, dy in [(0.55, 0.22), (0.68, 0.16), (0.45, 0.30)]:
        cx, cy = int(w * dx), int(h * dy)
        d.ellipse([cx - 7, cy - 3, cx + 7, cy + 3], fill=(25, 22, 28))
        d.ellipse([cx - 12, cy - 1, cx - 8, cy + 1], fill=(25, 22, 28))
        d.ellipse([cx + 8, cy - 1, cx + 12, cy + 1], fill=(25, 22, 28))
    return img


def scene_storm(w, h):
    img, d = scene_base(w, h, [(30, 38, 58), (58, 66, 92), (96, 96, 118)], int(h * 0.70), (38, 44, 40))
    cloud(d, int(w * 0.08), int(h * 0.08), 12, (52, 58, 80))
    cloud(d, int(w * 0.55), int(h * 0.03), 14, (44, 50, 72))
    # bent tree
    tx = int(w * 0.16)
    d.line([tx, int(h * 0.70), tx + 26, int(h * 0.42)], fill=(28, 34, 26), width=5)
    pine(d, tx + 30, int(h * 0.44), 9, (24, 52, 34))
    # houses with lit windows
    for hx, hw, hh in [(0.42, 0.16, 0.30), (0.62, 0.18, 0.36), (0.82, 0.14, 0.26)]:
        x0 = int(w * hx)
        building(d, x0, int(h * 0.70), int(w * hw), int(h * hh), (52, 44, 52))
        d.polygon([(x0, int(h * 0.70) - int(h * hh)), (x0 + int(w * hw) // 2, int(h * 0.70) - int(h * hh) - 12),
                   (x0 + int(w * hw), int(h * 0.70) - int(h * hh))], fill=(40, 32, 40))
    # power lines, one sagging
    d.line([0, int(h * 0.30), w, int(h * 0.26)], fill=(20, 20, 26), width=2)
    d.arc([-20, int(h * 0.30), w + 20, int(h * 0.62)], 20, 160, fill=(20, 20, 26), width=2)
    # rain streaks
    rnd = random.Random(7)
    for _ in range(46):
        rx, ry = rnd.randint(0, w), rnd.randint(0, int(h * 0.66))
        d.line([rx, ry, rx - 4, ry + 12], fill=(180, 190, 210), width=1)
    return img


def scene_gaza(w, h):
    img, d = scene_base(w, h, [(16, 16, 34), (40, 26, 52), (96, 52, 44)], int(h * 0.74), (24, 20, 24))
    star(d, int(w * 0.85), int(h * 0.14), 5, (240, 230, 180))
    star(d, int(w * 0.68), int(h * 0.08), 4, (230, 220, 170))
    # smoke columns
    for sx in (0.30, 0.55, 0.78):
        cx = int(w * sx)
        for i, r in enumerate((16, 22, 28, 34)):
            d.ellipse([cx - r, int(h * 0.62) - i * 16 - r, cx + r, int(h * 0.62) - i * 16 + r], fill=(70, 66, 70))
    # skyline
    for bx, bw, bh in [(0.04, 0.13, 0.34), (0.20, 0.11, 0.46), (0.34, 0.15, 0.28), (0.52, 0.12, 0.40), (0.68, 0.14, 0.32), (0.85, 0.12, 0.44)]:
        building(d, int(w * bx), int(h * 0.74), int(w * bw), int(h * bh), (30, 26, 36), win=(255, 190, 90))
    # explosion glow
    d.ellipse([int(w * 0.47) - 18, int(h * 0.60) - 18, int(w * 0.47) + 18, int(h * 0.60) + 18], fill=(255, 140, 40))
    return img


def scene_kyiv(w, h):
    img, d = scene_base(w, h, [(18, 34, 66), (40, 66, 110), (120, 130, 160)], int(h * 0.70), (30, 34, 40))
    cloud(d, int(w * 0.10), int(h * 0.10), 11, (70, 88, 118))
    cloud(d, int(w * 0.58), int(h * 0.05), 13, (60, 78, 108))
    # skyline with a dome
    building(d, int(w * 0.05), int(h * 0.70), 24, 40, (24, 30, 44))
    d.ellipse([int(w * 0.05) + 2, int(h * 0.70) - 52, int(w * 0.05) + 22, int(h * 0.70) - 32], fill=(201, 162, 39))
    building(d, int(w * 0.20), int(h * 0.70), 20, 28, (28, 34, 48))
    building(d, int(w * 0.68), int(h * 0.70), 26, 36, (24, 30, 44))
    building(d, int(w * 0.82), int(h * 0.70), 20, 24, (28, 34, 48))
    # pylon with sparks
    px = int(w * 0.47)
    d.polygon([(px, int(h * 0.18)), (px - 16, int(h * 0.70)), (px + 16, int(h * 0.70))], outline=(200, 200, 200), width=2)
    d.line([px - 22, int(h * 0.34), px + 22, int(h * 0.34)], fill=(200, 200, 200), width=2)
    d.line([px - 16, int(h * 0.50), px + 16, int(h * 0.50)], fill=(200, 200, 200), width=2)
    star(d, px - 20, int(h * 0.30), 6, (255, 220, 80))
    star(d, px + 18, int(h * 0.44), 5, (255, 220, 80))
    # warning triangle
    tx, ty = int(w * 0.86), int(h * 0.62)
    d.polygon([(tx, ty - 14), (tx - 13, ty + 10), (tx + 13, ty + 10)], fill=(255, 200, 40), outline=(20, 20, 20))
    d.text((tx - 2, ty - 8), "!", font=F(SANS_B, 13), fill=(20, 20, 20))
    return img


def scene_ibiza(w, h):
    img, d = scene_base(w, h, [(250, 170, 90), (240, 120, 70), (90, 90, 140)], int(h * 0.62), (18, 60, 96))
    sun(d, int(w * 0.80), int(h * 0.22), 15, (255, 226, 150), (255, 180, 90))
    # sea bands
    for i, c in enumerate([(24, 80, 120), (18, 66, 104), (14, 54, 88)]):
        d.rectangle([0, int(h * (0.62 + i * 0.12)), w, int(h * (0.74 + i * 0.12))], fill=c)
    # capsized ship, keel up
    sx, sy = int(w * 0.30), int(h * 0.66)
    d.polygon([(sx - 52, sy), (sx + 52, sy), (sx + 34, sy - 16), (sx - 34, sy - 16)], fill=(150, 40, 36))
    d.rectangle([sx - 52, sy, sx + 52, sy + 8], fill=(90, 26, 24))
    d.rectangle([sx - 8, sy - 26, sx + 8, sy - 16], fill=(200, 200, 190))
    # rescue helicopter
    hx, hy = int(w * 0.72), int(h * 0.30)
    d.ellipse([hx - 16, hy - 6, hx + 16, hy + 6], fill=(220, 60, 40))
    d.line([hx - 26, hy - 8, hx + 26, hy - 8], fill=(40, 40, 40), width=3)
    d.line([hx + 16, hy, hx + 30, hy - 4], fill=(220, 60, 40), width=3)
    d.line([hx, hy + 6, hx + 4, hy + 26], fill=(60, 60, 60), width=2)
    d.rectangle([hx - 2, hy + 26, hx + 10, hy + 32], fill=(255, 200, 60))
    return img


def scene_migration(w, h):
    img, d = scene_base(w, h, [(140, 180, 220), (200, 215, 235), (240, 240, 235)], int(h * 0.68), (52, 66, 84))
    # plane
    px, py = int(w * 0.30), int(h * 0.30)
    d.ellipse([px - 34, py - 8, px + 34, py + 8], fill=(240, 244, 248))
    d.polygon([(px + 20, py - 6), (px + 52, py - 22), (px + 52, py - 6)], fill=(200, 210, 220))
    d.polygon([(px - 6, py + 6), (px + 10, py + 22), (px + 18, py + 6)], fill=(200, 210, 220))
    d.polygon([(px - 34, py - 2), (px - 52, py - 14), (px - 52, py + 2)], fill=(180, 190, 200))
    for wx in range(px - 24, px + 24, 9):
        d.rectangle([wx, py - 3, wx + 4, py + 1], fill=(29, 78, 216))
    # falling bar chart
    bx0, by0 = int(w * 0.58), int(h * 0.62)
    bars = [(0, 44, (29, 78, 216)), (1, 34, (29, 78, 216)), (2, 24, (29, 78, 216)), (3, 12, (178, 35, 42))]
    for i, bh, c in bars:
        d.rectangle([bx0 + i * 22, by0 - bh, bx0 + i * 22 + 15, by0], fill=c)
    d.line([bx0 - 6, by0 - 52, bx0 + 92, by0 - 6], fill=(178, 35, 42), width=3)
    d.polygon([(bx0 + 92, by0 - 6), (bx0 + 82, by0 - 12), (bx0 + 82, by0 - 2)], fill=(178, 35, 42))
    # runway
    d.rectangle([0, int(h * 0.68), w, h], fill=(52, 66, 84))
    d.rectangle([0, int(h * 0.80), w, int(h * 0.80) + 3], fill=(240, 240, 220))
    return img


def scene_paris(w, h):
    img, d = scene_base(w, h, [(210, 200, 170), (170, 160, 140), (120, 110, 100)], int(h * 0.72), (70, 64, 58))
    # courthouse: pediment + columns
    cx0, cx1 = int(w * 0.12), int(w * 0.88)
    d.polygon([(cx0, int(h * 0.30)), ((cx0 + cx1) // 2, int(h * 0.16)), (cx1, int(h * 0.30))], fill=(226, 214, 188))
    d.rectangle([cx0, int(h * 0.30), cx1, int(h * 0.36)], fill=(210, 196, 168))
    for i in range(5):
        x = cx0 + 8 + i * ((cx1 - cx0 - 16) // 4)
        d.rectangle([x, int(h * 0.36), x + 10, int(h * 0.72)], fill=(240, 230, 205))
    d.rectangle([cx0, int(h * 0.72), cx1, int(h * 0.76)], fill=(200, 186, 158))
    # scales of justice, small
    sx, sy = int(w * 0.50), int(h * 0.52)
    d.line([sx, sy - 14, sx, sy + 12], fill=(60, 52, 40), width=3)
    d.line([sx - 14, sy - 12, sx + 14, sy - 12], fill=(60, 52, 40), width=2)
    d.arc([sx - 20, sy - 12, sx - 8, sy + 2], 0, 180, fill=(60, 52, 40), width=2)
    d.arc([sx + 8, sy - 12, sx + 20, sy + 2], 0, 180, fill=(60, 52, 40), width=2)
    return img


def scene_hongkong(w, h):
    img, d = scene_base(w, h, [(52, 40, 70), (110, 62, 84), (214, 140, 90)], int(h * 0.70), (40, 34, 40))
    # tower blocks
    for bx, bw, bh, c in [(0.04, 0.16, 0.52, (34, 30, 44)), (0.24, 0.14, 0.62, (40, 34, 50)),
                          (0.42, 0.18, 0.46, (30, 28, 40)), (0.64, 0.15, 0.58, (38, 32, 48)),
                          (0.82, 0.14, 0.42, (32, 28, 42))]:
        building(d, int(w * bx), int(h * 0.70), int(w * bw), int(h * bh), c, win=(255, 190, 110))
    # flowers and candles at the base
    for fx, fc in [(0.10, (255, 255, 255)), (0.18, (255, 220, 230)), (0.30, (255, 255, 255)),
                   (0.55, (255, 230, 180)), (0.72, (255, 255, 255)), (0.88, (255, 220, 230))]:
        x = int(w * fx)
        d.ellipse([x - 5, int(h * 0.74) - 5, x + 5, int(h * 0.74) + 5], fill=fc)
        d.ellipse([x - 3, int(h * 0.74) - 9, x + 3, int(h * 0.74) - 3], fill=fc)
    for cx in (0.24, 0.48, 0.66, 0.80):
        x = int(w * cx)
        d.rectangle([x - 2, int(h * 0.76), x + 2, int(h * 0.84)], fill=(255, 240, 200))
        d.ellipse([x - 3, int(h * 0.72), x + 3, int(h * 0.76)], fill=(255, 200, 60))
    return img


def scene_tube(w, h):
    img, d = scene_base(w, h, [(24, 40, 72), (40, 60, 100), (90, 90, 110)], int(h * 0.72), (30, 30, 36))
    # roundel-like sign in our own colours (generic circle + bar, no trademark)
    cx, cy = int(w * 0.50), int(h * 0.34)
    d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], outline=(255, 255, 255), width=6)
    d.rectangle([cx - 44, cy - 8, cx + 44, cy + 8], fill=(178, 35, 42))
    d.text((cx - 30, cy - 6), "TUBE", font=F(SANS_B, 12), fill=(255, 255, 255))
    # train front
    tx0, ty0 = int(w * 0.14), int(h * 0.56)
    d.rounded_rectangle([tx0, ty0, tx0 + int(w * 0.72), ty0 + int(h * 0.20)], radius=8, fill=(178, 35, 42))
    d.rectangle([tx0 + 8, ty0 + 6, tx0 + int(w * 0.30), ty0 + int(h * 0.12)], fill=(200, 220, 235))
    d.rectangle([tx0 + int(w * 0.38), ty0 + 6, tx0 + int(w * 0.60), ty0 + int(h * 0.12)], fill=(200, 220, 235))
    d.ellipse([tx0 + 12, ty0 + int(h * 0.15), tx0 + 22, ty0 + int(h * 0.15) + 10], fill=(255, 240, 150))
    d.ellipse([tx0 + int(w * 0.72) - 22, ty0 + int(h * 0.15), tx0 + int(w * 0.72) - 12, ty0 + int(h * 0.15) + 10], fill=(255, 240, 150))
    # picket signs
    for sx in (0.06, 0.88):
        x = int(w * sx)
        d.line([x, int(h * 0.62), x, int(h * 0.74)], fill=(220, 210, 190), width=2)
        d.rectangle([x - 12, int(h * 0.50), x + 12, int(h * 0.62)], fill=(255, 253, 246))
    return img


def scene_cologne(w, h):
    img, d = scene_base(w, h, [(60, 70, 110), (110, 110, 140), (180, 170, 150)], int(h * 0.70), (44, 42, 48))
    # synagogue: dome + arched windows
    cx = int(w * 0.42)
    d.rectangle([cx - 34, int(h * 0.38), cx + 34, int(h * 0.70)], fill=(226, 214, 188))
    d.pieslice([cx - 34, int(h * 0.18), cx + 34, int(h * 0.44)], 180, 360, fill=(120, 130, 150))
    d.rectangle([cx - 3, int(h * 0.10), cx + 3, int(h * 0.20)], fill=(201, 162, 39))
    for wx in (-20, 0, 20):
        d.pieslice([cx + wx - 7, int(h * 0.48), cx + wx + 7, int(h * 0.66)], 180, 360, fill=(90, 100, 130))
        d.rectangle([cx + wx - 7, int(h * 0.57), cx + wx + 7, int(h * 0.66)], fill=(90, 100, 130))
    # shield / police tape
    d.polygon([(int(w * 0.82), int(h * 0.30)), (int(w * 0.94), int(h * 0.30)), (int(w * 0.88), int(h * 0.52))],
              fill=(29, 78, 216))
    d.text((int(w * 0.845), int(h * 0.33)), "!", font=F(SANS_B, 18), fill=(255, 255, 255))
    d.rectangle([0, int(h * 0.78), w, int(h * 0.78) + 10], fill=(255, 200, 40))
    d.rectangle([0, int(h * 0.86), w, int(h * 0.86) + 6], fill=(255, 200, 40))
    return img


def scene_chess(w, h):
    img, d = scene_base(w, h, [(30, 44, 66), (60, 70, 100), (140, 130, 110)], int(h * 0.74), (44, 40, 34))
    # chessboard
    bx0, by0, cs = int(w * 0.16), int(h * 0.14), int(w * 0.085)
    for r in range(4):
        for c in range(4):
            col = (240, 232, 210) if (r + c) % 2 == 0 else (52, 48, 44)
            d.rectangle([bx0 + c * cs, by0 + r * cs, bx0 + (c + 1) * cs, by0 + (r + 1) * cs], fill=col)
    d.rectangle([bx0, by0, bx0 + 4 * cs, by0 + 4 * cs], outline=(20, 18, 16), width=2)
    # king and queen pieces (simple silhouettes)
    kx, ky = bx0 + int(1.5 * cs), by0 + int(3.4 * cs)
    d.ellipse([kx - 9, ky - 26, kx + 9, ky - 8], fill=(250, 244, 230))
    d.rectangle([kx - 11, ky - 8, kx + 11, ky + 2], fill=(250, 244, 230))
    d.line([kx - 4, ky - 32, kx + 4, ky - 32], fill=(250, 244, 230), width=3)
    qx, qy = bx0 + int(2.5 * cs), by0 + int(3.4 * cs)
    d.ellipse([qx - 8, qy - 22, qx + 8, qy - 6], fill=(30, 26, 24))
    d.rectangle([qx - 10, qy - 6, qx + 10, qy + 2], fill=(30, 26, 24))
    # clock
    cx, cy = int(w * 0.80), int(h * 0.30)
    d.rounded_rectangle([cx - 26, cy - 20, cx + 26, cy + 20], radius=6, fill=(40, 36, 32))
    d.rectangle([cx - 18, cy - 12, cx + 18, cy + 12], fill=(240, 235, 210))
    d.line([cx, cy, cx, cy - 10], fill=(178, 35, 42), width=2)
    d.line([cx, cy, cx + 9, cy + 4], fill=(20, 20, 20), width=2)
    return img


def scene_blackfriday(w, h):
    img, d = scene_base(w, h, [(178, 35, 42), (200, 60, 50), (240, 190, 90)], int(h * 0.66), (60, 44, 40))
    # storefront awning
    d.rectangle([0, int(h * 0.30), w, int(h * 0.38)], fill=(255, 253, 246))
    for i in range(8):
        d.rectangle([i * (w // 8), int(h * 0.30), (i + 1) * (w // 8), int(h * 0.38)],
                    fill=(178, 35, 42) if i % 2 == 0 else (255, 253, 246))
    d.rectangle([int(w * 0.08), int(h * 0.38), int(w * 0.92), int(h * 0.66)], fill=(120, 30, 34))
    d.rectangle([int(w * 0.14), int(h * 0.44), int(w * 0.42), int(h * 0.66)], fill=(255, 220, 120))
    d.rectangle([int(w * 0.58), int(h * 0.44), int(w * 0.86), int(h * 0.66)], fill=(255, 220, 120))
    # queue of shoppers
    for i, sx in enumerate((0.16, 0.34, 0.52, 0.70, 0.86)):
        x, y = int(w * sx), int(h * 0.78)
        d.ellipse([x - 7, y - 26, x + 7, y - 12], fill=(240, 210, 170))
        d.rectangle([x - 9, y - 12, x + 9, y + 8], fill=[(29, 78, 216), (15, 118, 110), (180, 83, 9), (124, 58, 237), (77, 124, 15)][i])
    # 50% tag
    d.polygon([(int(w * 0.66), int(h * 0.06)), (int(w * 0.96), int(h * 0.06)), (int(w * 0.96), int(h * 0.20)), (int(w * 0.66), int(h * 0.20))],
              fill=(255, 200, 40))
    d.text((int(w * 0.69), int(h * 0.08)), "50% OFF", font=F(SANS_B, 11), fill=(120, 20, 20))
    return img


def scene_spacex(w, h):
    img, d = scene_base(w, h, [(8, 12, 34), (18, 28, 64), (60, 60, 110)], int(h * 0.78), (24, 26, 40))
    rnd = random.Random(11)
    for _ in range(26):
        star(d, rnd.randint(4, w - 4), rnd.randint(4, int(h * 0.55)), rnd.randint(2, 4), (240, 240, 220))
    # rocket
    rx, ry = int(w * 0.46), int(h * 0.42)
    d.polygon([(rx, ry - 34), (rx - 12, ry - 8), (rx + 12, ry - 8)], fill=(220, 60, 40))
    d.rectangle([rx - 12, ry - 8, rx + 12, ry + 22], fill=(240, 244, 248))
    d.polygon([(rx - 12, ry + 22), (rx - 22, ry + 34), (rx - 12, ry + 26)], fill=(220, 60, 40))
    d.polygon([(rx + 12, ry + 22), (rx + 22, ry + 34), (rx + 12, ry + 26)], fill=(220, 60, 40))
    d.ellipse([rx - 5, ry - 2, rx + 5, ry + 8], fill=(120, 180, 230))
    # flame
    d.polygon([(rx - 7, ry + 34), (rx + 7, ry + 34), (rx, ry + 52)], fill=(255, 180, 60))
    d.polygon([(rx - 4, ry + 34), (rx + 4, ry + 34), (rx, ry + 46)], fill=(255, 240, 150))
    # orbit ring + satellite
    d.ellipse([int(w * 0.55), int(h * 0.10), int(w * 0.98), int(h * 0.42)], outline=(160, 180, 220), width=2)
    d.rectangle([int(w * 0.88), int(h * 0.14), int(w * 0.96), int(h * 0.18)], fill=(200, 210, 230))
    # coins for children
    for cx in (0.14, 0.26, 0.38):
        x = int(w * cx)
        d.ellipse([x - 9, int(h * 0.62) - 9, x + 9, int(h * 0.62) + 9], fill=(201, 162, 39), outline=(140, 105, 20))
        d.text((x - 4, int(h * 0.62) - 7), "$", font=F(SANS_B, 11), fill=(120, 85, 10))
    return img


SCENES = {
    "kuwait": scene_kuwait, "storm": scene_storm, "gaza": scene_gaza,
    "kyiv": scene_kyiv, "ibiza": scene_ibiza, "migration": scene_migration,
    "paris": scene_paris, "hongkong": scene_hongkong, "tube": scene_tube,
    "cologne": scene_cologne, "chess": scene_chess, "blackfriday": scene_blackfriday,
    "spacex": scene_spacex,
}

# ---- world map (hand-drawn simplified continents, lon/lat polygons) ----
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 68), (-95, 70), (-85, 66), (-80, 73), (-65, 60), (-55, 47),
     (-70, 42), (-75, 35), (-80, 26), (-84, 30), (-90, 21), (-97, 16), (-105, 20), (-110, 24), (-117, 33),
     (-125, 40), (-124, 48), (-135, 58), (-155, 58), (-165, 60)],
    [(-80, 10), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18), (-70, -23), (-70, -30), (-72, -37),
     (-73, -44), (-70, -52), (-66, -55), (-68, -50), (-62, -41), (-57, -38), (-48, -28), (-40, -22), (-35, -9),
     (-40, -3), (-44, 2), (-52, 5), (-60, 8), (-70, 11)],
    [(-10, 36), (-9, 43), (-2, 44), (-2, 48), (-4, 48), (0, 50), (3, 51), (5, 53), (8, 55), (8, 57),
     (10, 59), (5, 60), (5, 62), (12, 64), (18, 66), (21, 65), (25, 66), (30, 70), (40, 68), (44, 66),
     (40, 60), (32, 60), (30, 60), (28, 58), (24, 58), (21, 55), (19, 54), (14, 54), (12, 55), (8, 57),
     (3, 58), (-5, 60), (-8, 58), (-10, 54), (-10, 50), (-9, 44), (-9, 38), (-6, 36)],
    [(-6, 35), (10, 37), (20, 32), (32, 31), (35, 28), (34, 22), (38, 18), (40, 15), (44, 11), (48, 11),
     (51, 10), (51, 2), (48, -2), (42, -8), (40, -15), (36, -20), (32, -26), (28, -33), (20, -35), (16, -28),
     (12, -18), (9, -1), (4, 6), (-8, 5), (-13, 8), (-16, 12), (-17, 15), (-16, 20), (-16, 25), (-10, 31)],
    [(40, 68), (50, 70), (60, 69), (70, 72), (80, 73), (90, 75), (100, 77), (110, 76), (120, 73), (130, 72),
     (140, 72), (150, 70), (160, 66), (162, 60), (158, 52), (142, 50), (140, 44), (135, 43), (130, 40),
     (127, 35), (122, 32), (120, 28), (115, 23), (110, 20), (108, 15), (105, 10), (103, 7), (100, 8),
     (97, 15), (94, 17), (92, 21), (88, 22), (85, 19), (80, 15), (77, 8), (75, 12), (72, 20), (66, 25),
     (62, 25), (58, 26), (55, 26), (52, 25), (50, 29), (48, 30), (44, 29), (42, 28), (40, 22), (38, 20),
     (36, 18), (35, 16), (35, 15), (38, 12), (40, 10), (43, 12), (45, 13), (48, 14), (50, 16), (52, 18),
     (55, 20), (57, 22), (59, 23), (57, 26), (52, 27), (50, 29)],
    [(113, -22), (114, -30), (115, -33), (118, -35), (124, -33), (130, -32), (134, -33), (137, -35), (140, -38),
     (145, -38), (150, -37), (153, -32), (153, -27), (150, -23), (146, -19), (142, -15), (142, -11),
     (137, -12), (135, -12), (132, -11), (130, -13), (126, -14), (122, -17), (118, -20)],
]

PIN_LONLAT = {
    1: (47.9, 29.3), 2: (-77, 39), 3: (34.5, 31.5), 4: (30.5, 50.4), 5: (1.4, 38.9),
    6: (-0.1, 51.5), 7: (2.35, 48.85), 8: (114.2, 22.3), 9: (-0.1, 51.5), 10: (6.95, 50.9),
    11: (6.1, 46.2), 12: (-95, 39), 13: (-97, 29),
}
# pixel offsets to fan out the crowded western-Europe cluster
PIN_OFFSET = {4: (14, -10), 6: (-22, 12), 7: (18, -16), 9: (24, 10), 10: (30, -6), 11: (12, 16)}


def draw_map(d, mx, my, mw, mh):
    d.rectangle([mx, my, mx + mw, my + mh], fill=(178, 214, 232))
    d.rectangle([mx, my, mx + mw, my + mh], outline=LINE, width=1)
    def proj(lon, lat):
        return (mx + (lon + 170) / 360.0 * mw, my + (72 - lat) / 128.0 * mh)
    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        d.polygon(pts, fill=(196, 178, 138), outline=(140, 124, 88))
    for n, (lon, lat) in PIN_LONLAT.items():
        px, py = proj(lon, lat)
        ox, oy = PIN_OFFSET.get(n, (0, 0))
        qx, qy = px + ox, py + oy
        if (ox, oy) != (0, 0):
            d.line([px, py, qx, qy], fill=(178, 35, 42), width=1)
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(178, 35, 42))
        d.ellipse([qx - 7, qy - 7, qx + 7, qy + 7], fill=RED, outline=(255, 255, 255), width=1)
        f = F(SANS_B, 8)
        tw = f.getlength(str(n))
        d.text((qx - tw / 2, qy - 6), str(n), font=f, fill=(255, 255, 255))


# ---- card drawing ----
def status_chip(d, right_x, y, status):
    """Right-aligned status chip ending at right_x."""
    if not status:
        return
    colors = {"REPORTED": (29, 78, 216), "CONFIRMED": (15, 118, 110), "CLAIM": (178, 35, 42)}
    f = F(SANS_B, 8)
    w = int(f.getlength(status)) + 10
    x = right_x - w
    d.rounded_rectangle([x, y, x + w, y + 12], radius=3, fill=colors[status])
    d.text((x + 5, y + 1), status, font=f, fill=(255, 255, 255))


def draw_lead(img, d, x, y, w, h, story):
    n, region, dateline, headline, deck, source, status, art = story
    rc = REGION_COLORS[region]
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=INK, width=1)
    d.rectangle([x, y, x + w, y + 5], fill=rc)
    art_img = SCENES[art](w, 88)
    img.paste(art_img, (x, y + 5))
    # number badge
    d.ellipse([x + 6, y + 11, x + 30, y + 35], fill=RED, outline=(255, 255, 255), width=2)
    fnum = F(SANS_B, 14)
    tw = fnum.getlength(str(n))
    d.text((x + 18 - tw / 2, y + 14), str(n), font=fnum, fill=(255, 255, 255))
    # dateline kicker
    fk = F(SANS_B, 9)
    d.text((x + 8, y + 97), dateline, font=fk, fill=rc)
    draw_wrapped(d, x + 8, y + 109, headline, F(SERIF_B, 15), INK, w - 16, lh=18, max_lines=2)
    draw_wrapped(d, x + 8, y + 147, deck, F(SANS, 10), (60, 58, 52), w - 16, lh=12, max_lines=2)
    fs = F(SANS_B, 9)
    d.text((x + 8, y + h - 14), source, font=fs, fill=MUTED)
    status_chip(d, x + w - 6, y + h - 17, status)


def draw_feature(img, d, x, y, w, h, story):
    n, region, dateline, headline, deck, source, status, art = story
    rc = REGION_COLORS[region]
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=INK, width=1)
    d.rectangle([x, y, x + w, y + 4], fill=rc)
    art_img = SCENES[art](w, 56)
    img.paste(art_img, (x, y + 4))
    d.ellipse([x + 4, y + 8, x + 22, y + 26], fill=RED, outline=(255, 255, 255), width=1)
    fnum = F(SANS_B, 10)
    tw = fnum.getlength(str(n))
    d.text((x + 13 - tw / 2, y + 10), str(n), font=fnum, fill=(255, 255, 255))
    fk = F(SANS_B, 8)
    d.text((x + 6, y + 63), dateline, font=fk, fill=rc)
    draw_wrapped(d, x + 6, y + 75, headline, F(SERIF_B, 11), INK, w - 12, lh=13, max_lines=2)
    draw_wrapped(d, x + 6, y + 102, deck, F(SANS, 9), (60, 58, 52), w - 12, lh=11, max_lines=2)
    fs = F(SANS_B, 8)
    d.text((x + 6, y + h - 11), source, font=fs, fill=MUTED)
    status_chip(d, x + w - 5, y + h - 13, status)


# ---- build the poster ----
def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # masthead 0-62
    d.rectangle([0, 0, W, 62], fill=NAVY)
    d.rectangle([0, 62, W, 64], fill=GOLD)
    d.text((14, 8), "THE FRIDAY WORLD", font=F(SERIF_B, 34), fill=(246, 241, 229))
    d.text((W - 14 - F(SANS_B, 14).getlength("FRIDAY 27 NOVEMBER 2026"), 12),
           "FRIDAY 27 NOVEMBER 2026", font=F(SANS_B, 14), fill=(255, 214, 130))
    d.text((W - 14 - F(SANS, 10).getlength("ONE DAY \u00b7 ONE PAGE \u00b7 EVERY STORY DATED"), 32),
           "ONE DAY \u00b7 ONE PAGE \u00b7 EVERY STORY DATED", font=F(SANS, 10), fill=(200, 205, 220))
    d.text((14, 44), "Drones over the Gulf \u00b7 a storm darkens Thanksgiving \u00b7 ten dead in Gaza \u2014 the whole world in one page.",
           font=F(SERIF, 12), fill=(220, 222, 232))

    # claim band 64-82
    d.rectangle([0, 64, W, 82], fill=RED)
    claim = "37 STORIES  \u00b7  7 REGIONS  \u00b7  EVERY ONE DATED FRIDAY 27 NOVEMBER 2026"
    fc = F(SANS_B, 12)
    d.text(((W - fc.getlength(claim)) / 2, 68), claim, font=fc, fill=(255, 255, 255))

    # leads 86-272
    for i, s in enumerate(PICTURED[:3]):
        draw_lead(img, d, 8 + i * 336, 86, 328, 186, s)

    # features rows 276-412, 416-552
    for r in range(2):
        for c in range(5):
            s = PICTURED[3 + r * 5 + c]
            draw_feature(img, d, 8 + c * 203, 276 + r * 140, 195, 136, s)

    # numbers strip 556-606 (red header tab overlaps the top edge)
    d.rectangle([8, 556, 1016, 606], fill=(255, 253, 246), outline=INK, width=1)
    d.rectangle([8, 552, 196, 566], fill=RED)
    ftab = F(SANS_B, 10)
    d.text((8 + (188 - ftab.getlength("THE DAY IN NUMBERS")) / 2, 554), "THE DAY IN NUMBERS", font=ftab, fill=(255, 255, 255))
    for i, (num, label) in enumerate(NUMBERS):
        x0 = 8 + i * 168
        if i:
            d.line([x0, 572, x0, 602], fill=LINE, width=1)
        fn = F(SERIF_B, 19)
        d.text((x0 + (168 - fn.getlength(num)) / 2, 570), num, font=fn, fill=NAVY)
        fl = F(SANS, 8)
        d.text((x0 + (168 - fl.getlength(label)) / 2, 592), label, font=fl, fill=MUTED)

    # region strip 610-632
    d.rectangle([8, 610, 1016, 632], fill=NAVY2)
    rx = 16
    fr = F(SANS_B, 10)
    for name, c in REGIONS:
        col = REGION_COLORS[name]
        d.ellipse([rx, 616, rx + 10, 626], fill=col, outline=(255, 255, 255), width=1)
        txt = "%s %d" % (name, c)
        d.text((rx + 14, 616), txt, font=fr, fill=(255, 255, 255))
        rx += 14 + int(fr.getlength(txt)) + 16
    d.text((rx + 6, 616), "TOTAL 37", font=fr, fill=(255, 214, 130))

    # timeline 634-660
    d.text((10, 636), "THE DAY IN TIME (UTC)", font=F(SANS_B, 10), fill=RED)
    tx = 172
    for t, ev in TIMELINE:
        d.text((tx, 636), t, font=F(SANS_B, 10), fill=RED)
        draw_wrapped(d, tx + 42, 637, ev, F(SANS, 9), INK, 118, lh=11, max_lines=2)
        tx += 166

    # map + date check 664-784
    d.rectangle([8, 664, 648, 784], fill=CARD, outline=INK, width=1)
    d.text((16, 670), "WHERE IT HAPPENED \u2014 PINS 1\u201313 MATCH THE PICTURED STORIES", font=F(SANS_B, 10), fill=NAVY)
    draw_map(d, 16, 686, 624, 92)

    d.rectangle([656, 664, 1016, 784], fill=(255, 248, 240), outline=RED, width=1)
    d.text((666, 670), "DATE CHECK \u2014 LEFT OUT ON PURPOSE", font=F(SANS_B, 10), fill=RED)
    fy = 688
    for title, date in DATE_CHECK:
        d.text((666, fy), "\u2717  " + title, font=F(SANS, 9), fill=INK)
        fd = F(SANS_B, 9)
        d.text((1016 - 8 - fd.getlength(date), fy), date, font=fd, fill=RED)
        fy += 14
    d.text((666, fy + 2), "Big stories, wrong day. They do not count.",
           font=F(SANS, 9), fill=MUTED)

    # briefs heading 788-806
    d.text((10, 788), "ALSO ON FRIDAY 27 NOVEMBER \u2014 24 MORE STORIES", font=F(SANS_B, 12), fill=NAVY)
    d.line([10, 806, 1014, 806], fill=RED, width=2)

    # briefs 810-994: 3 columns x 8 rows
    for i, s in enumerate(BRIEFS):
        n, region, dateline, headline, deck, source = s
        col, row = i % 3, i // 3
        x0 = 10 + col * 338
        y0 = 810 + row * 23
        rc = REGION_COLORS[region]
        d.ellipse([x0, y0, x0 + 14, y0 + 14], fill=rc)
        fn = F(SANS_B, 8)
        tw = fn.getlength(str(n))
        d.text((x0 + 7 - tw / 2, y0 + 2), str(n), font=fn, fill=(255, 255, 255))
        fh = F(SANS_B, 10)
        if fh.getlength(headline) > 306:
            fh = F(SANS_B, 9)
        d.text((x0 + 18, y0 + 1), headline, font=fh, fill=INK)
        d.text((x0 + 18, y0 + 13), dateline + "  \u00b7  " + source, font=F(SANS, 8), fill=MUTED)

    # footer 998-1022
    d.line([10, 998, 1014, 998], fill=LINE, width=1)
    d.text((10, 1002), "Every story here happened, or was first reported, on 27 November 2026 (in any time zone).",
           font=F(SANS_B, 9), fill=INK)
    d.text((10, 1013), "Sources: Reuters \u00b7 AP \u00b7 AFP \u00b7 BBC \u00b7 Guardian \u00b7 Ukrinform \u00b7 Chess.com \u00b7 ESPNcricinfo  |  REPORTED = as reported  \u00b7  CONFIRMED = confirmed by officials  \u00b7  CLAIM = one side\u2019s claim, disputed  |  Original drawings.",
           font=F(SANS, 8), fill=MUTED)

    img = apply_noise(img, seed=42, alpha=0.02)
    img.save(OUT, optimize=True, compress_level=9)
    return img


if __name__ == "__main__":
    build()
    print("wrote", OUT)
