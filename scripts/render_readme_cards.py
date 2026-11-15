#!/usr/bin/env python3
"""Render animated SVG cards for the profile README into cards/.
STATIC=1 -> final frame, no animation (for screenshots)."""
import base64, json, os, datetime as dt
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cards"; OUT.mkdir(exist_ok=True)
STATIC = os.environ.get("STATIC") == "1"

PAPER, CARD, INK = "#f6f1e7", "#fffdf7", "#14110f"
BLUE, RED, YELLOW = "#1f4fff", "#e5393b", "#f5b700"
MUTED, LINE = "#6b645a", "#e2dac8"
HEAT = ["#ebe5d6", "#c3cffd", "#8aa3ff", "#4a73ff", BLUE]

SERIF = "'EmbSerif','Instrument Serif',Georgia,'Times New Roman',serif"
SANS = "'EmbSans','Geist',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"


def font_css():
    css = ""
    for fam, fn in (("EmbSerif", "serif.woff"), ("EmbSans", "sans.woff")):
        p = ROOT / "fonts" / fn
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode()
            css += f"@font-face{{font-family:'{fam}';src:url(data:font/woff;base64,{b64})}}"
    return css


KEYS = """
@keyframes rise{from{opacity:0;transform:translateY(22px)}}
@keyframes pop{from{opacity:0;transform:scale(0)}}
@keyframes grow{from{transform:scaleY(0)}}
@keyframes sweep{from{transform:scaleX(0)}}
@keyframes fade{from{opacity:0}}
@keyframes swing{0%{opacity:0;transform:translateY(60px) rotate(-6deg)}70%{transform:translateY(-6px) rotate(1deg)}}
@keyframes nudge{50%{transform:translateX(5px)}}
@keyframes pulse{50%{opacity:.3}}
.r{animation:rise .8s cubic-bezier(.2,.8,.2,1) backwards}
.f{animation:fade .6s ease-out backwards}
.p{transform-box:fill-box;transform-origin:center;animation:pop .35s ease-out backwards}
.g{transform-box:fill-box;transform-origin:bottom;animation:grow .7s cubic-bezier(.2,.8,.2,1) backwards}
.s{transform-box:fill-box;transform-origin:left;animation:sweep .7s ease-out backwards}
.sw{transform-box:fill-box;transform-origin:center;animation:swing .9s cubic-bezier(.2,.8,.2,1) backwards}
.n{animation:nudge 1.8s ease-in-out infinite}
.pl{animation:pulse 1.6s ease-in-out infinite}
"""
CALM = "*{animation:none!important}" if STATIC else "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img"><style>{font_css()}{KEYS}{CALM}</style>{body}</svg>')


def d(sec):
    return f'style="animation-delay:{sec:.2f}s"'


def save(name, content):
    (OUT / name).write_text(content, encoding="utf-8")


# ---------- data ----------
raw = json.loads((ROOT / "data" / "contributions.json").read_text())
days = [(dt.date.fromisoformat(x["date"]), x["count"]) for x in raw["days"]]
days.sort()
days = days[-371:]
last = days[-1][0]
year = [x for x in days if x[0] > last - dt.timedelta(days=365)]
total = sum(c for _, c in year)
active = sum(1 for _, c in year if c > 0)
best_day = max(year, key=lambda x: x[1])

streak = 0
for i, (_, c) in enumerate(reversed(days)):
    if c == 0 and i == 0:
        continue  # today may not be done yet
    if c == 0:
        break
    streak += 1

months = []
y, m = last.year, last.month
for _ in range(12):
    months.append((y, m))
    m -= 1
    if m == 0:
        y, m = y - 1, 12
months.reverse()
mtotals = [sum(c for dd, c in year if (dd.year, dd.month) == ym) for ym in months]
mnames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ---------- hero ----------
def hero():
    body = f"""
<rect width="900" height="250" rx="18" fill="{PAPER}" stroke="{INK}" stroke-width="1.5"/>
<g class="f" {d(.1)}><circle class="pl" cx="62" cy="52" r="5" fill="{BLUE}"/>
<text x="76" y="57" font-family="{SANS}" font-size="14" letter-spacing="2" fill="{BLUE}">HELLO, I'M</text></g>
<g class="r" {d(.3)}><text x="56" y="150" font-family="{SERIF}" font-size="98" fill="{INK}">Ishaan <tspan fill="{BLUE}">Rai</tspan></text></g>
<rect class="s" {d(1.0)} x="58" y="166" width="150" height="4" fill="{BLUE}"/>
<g class="r" {d(.7)}><text x="58" y="205" font-family="{SANS}" font-size="19" fill="{INK}">AI full-stack developer · B.Tech CSE @ Chitkara University</text>
<text x="58" y="230" font-family="{SANS}" font-size="15" fill="{MUTED}">Freelancing since Jan 2026 · building voice-first, fintech &amp; AI products</text></g>
<g class="p" {d(1.2)}><circle cx="820" cy="60" r="26" fill="{YELLOW}"/></g>
<g class="p" {d(1.35)}><circle cx="852" cy="92" r="14" fill="{RED}"/></g>
<g class="p" {d(1.5)}><circle cx="800" cy="104" r="9" fill="{BLUE}"/></g>"""
    save("hero.svg", svg(900, 250, body))


# ---------- blue contribution graph ----------
def heatmap():
    nz = sorted(c for _, c in days if c > 0)
    q = [nz[len(nz) * k // 4] for k in (1, 2, 3)] if nz else [1, 2, 3]

    def lvl(c):
        if c == 0:
            return 0
        return 1 + sum(c > t for t in q) if c > q[0] else 1

    off = (days[0][0].weekday() + 1) % 7
    cells = ""
    for i, (dd, c) in enumerate(days):
        col, row = (off + i) // 7, (off + i) % 7
        cells += (f'<rect class="p" {d(.2 + col * .018)} x="{52 + col * 15}" y="{58 + row * 15}" '
                  f'width="12" height="12" rx="3" fill="{HEAT[min(lvl(c), 4)]}"/>')
    body = f"""
<rect width="900" height="190" rx="18" fill="{PAPER}" stroke="{INK}" stroke-width="1.5"/>
<text x="52" y="38" font-family="{SERIF}" font-size="24" fill="{INK}">{total:,} contributions <tspan fill="{MUTED}" font-family="{SANS}" font-size="14">in the last year</tspan></text>
{cells}"""
    save("heatmap.svg", svg(900, 190, body))


# ---------- monthly bars + stats ----------
def activity():
    stats = [(f"{total:,}", "contributions"), (f"{streak}d", "current streak"),
             (f"{active}", "active days"),
             (f"{best_day[1]}", f"busiest · {mnames[best_day[0].month - 1]} {best_day[0].day}")]
    st = ""
    for i, (v, lab) in enumerate(stats):
        x = 56 + i * 210
        st += (f'<g class="r" {d(.2 + i * .12)}><text x="{x}" y="86" font-family="{SERIF}" font-size="46" fill="{INK}">{escape(v)}</text>'
               f'<text x="{x}" y="110" font-family="{SANS}" font-size="13" fill="{MUTED}">{escape(lab)}</text></g>')
    mx = max(mtotals) or 1
    bi = mtotals.index(max(mtotals))
    bars = ""
    for i, v in enumerate(mtotals):
        x, h = 60 + i * 65, max(3, 150 * v / mx)
        col = BLUE if i == bi else "#cfc7b4"
        bars += (f'<rect class="g" {d(.9 + i * .06)} x="{x}" y="{290 - h:.1f}" width="38" height="{h:.1f}" rx="5" fill="{col}"/>'
                 f'<text x="{x + 19}" y="314" text-anchor="middle" font-family="{SANS}" font-size="12" fill="{MUTED}">{mnames[months[i][1] - 1]}</text>')
        if i == bi:
            bars += (f'<text class="p" {d(1.8)} x="{x + 19}" y="{290 - h - 10:.1f}" text-anchor="middle" '
                     f'font-family="{SERIF}" font-size="22" fill="{BLUE}">{v}</text>')
    body = f"""
<rect width="900" height="340" rx="18" fill="{PAPER}" stroke="{INK}" stroke-width="1.5"/>
{st}<line x1="52" y1="290" x2="848" y2="290" stroke="{LINE}" stroke-width="2"/>{bars}"""
    save("activity.svg", svg(900, 340, body))


# ---------- three project tiles ----------
TILES = [
    ("BUILD", BLUE, "Mandi-Relay", ["Voice-first agricultural", "marketplace for India."], "Next.js · Supabase · Voice AI"),
    ("SCREEN", RED, "Gnani-AI-Challenge", ["AI unknown-caller screening,", "built for the Gnani AI challenge."], "TypeScript · Gnani AI"),
    ("TOOLS", YELLOW, "OpenSource-Tools", ["Open-source tools and", "AI-powered workflows."], "TypeScript · AI · Telegram"),
]


def tiles():
    for i, (label, col, title, desc, tags) in enumerate(TILES):
        t = 1.6 + i * .25
        lines = "".join(f'<text x="28" y="{108 + j * 22}" font-family="{SANS}" font-size="14.5" fill="{INK}">{escape(s)}</text>'
                        for j, s in enumerate(desc))
        body = f"""
<g class="sw" {d(t)}>
<rect x="2" y="2" width="296" height="206" rx="18" fill="{CARD}" stroke="{INK}" stroke-width="1.5"/>
<rect x="28" y="28" width="36" height="6" rx="3" fill="{col}"/>
<text x="28" y="56" font-family="{SANS}" font-size="12" letter-spacing="2" fill="{INK}">{label}</text>
<text x="28" y="88" font-family="{SERIF}" font-size="25" fill="{INK}">{escape(title)}</text>
{lines}
<text x="28" y="182" font-family="{SANS}" font-size="12" fill="{MUTED}">{escape(tags)}</text>
<g class="n" transform="translate(250 176)"><path d="M0 0H22M14 -6L22 0L14 6" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></g>
<circle class="pl" cx="268" cy="32" r="8" fill="{col}"/>
</g>"""
        save(f"tile-{i + 1}.svg", svg(300, 210, body))


for fn in (hero, heatmap, activity, tiles):
    fn()
print("rendered", sorted(p.name for p in OUT.glob("*.svg")))
