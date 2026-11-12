#!/usr/bin/env python3
"""Render animated SVG cards for Ishaan-Rai09's GitHub profile.

Run: python scripts/render_profile.py
Static screenshot mode: STATIC=1 python scripts/render_profile.py
The script fetches GitHub's public contribution SVG; on network failure it uses
 data/contributions.json so local rendering remains deterministic.
"""
from __future__ import annotations
import json, os, re, urllib.request
from collections import defaultdict
from datetime import date
from html import escape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "cards"
DATA = ROOT / "data" / "contributions.json"
USER = "Ishaan-Rai09"
STATIC = os.getenv("STATIC") == "1"
BG, PAPER, INK, MUTED = "#f5f2eb", "#fffdf8", "#20252b", "#747b83"
BLUE, RED, GOLD, LINE = "#3478f6", "#e66a5b", "#e6b94f", "#dedbd3"

class ContributionParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.days=[]; self.current=None; self.in_title=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag == "rect" and a.get("data-date"):
            self.current={"date":a["data-date"],"level":int(a.get("data-level","0")),"count":0}
        elif tag == "title" and self.current is not None: self.in_title=True
    def handle_data(self, data):
        if self.in_title and self.current is not None:
            m=re.search(r"(\d+) contributions?", data)
            if m: self.current["count"]=int(m.group(1))
    def handle_endtag(self, tag):
        if tag=="title": self.in_title=False
        if tag=="rect" and self.current is not None:
            self.days.append(self.current); self.current=None

def load_data():
    DATA.parent.mkdir(parents=True, exist_ok=True)
    try:
        req=urllib.request.Request(f"https://github.com/users/{USER}/contributions",headers={"User-Agent":"profile-card-renderer"})
        with urllib.request.urlopen(req,timeout=20) as res: raw=res.read().decode("utf-8","ignore")
        p=ContributionParser(); p.feed(raw)
        if p.days:
            payload={"updated":date.today().isoformat(),"days":p.days}
            DATA.write_text(json.dumps(payload,indent=2),encoding="utf-8")
            return payload
    except Exception as exc:
        print(f"Contribution refresh unavailable; using cached data: {exc}")
    if DATA.exists(): return json.loads(DATA.read_text(encoding="utf-8"))
    return {"updated":date.today().isoformat(),"days":[]}

def svg_wrap(w,h,body,defs="",delay=0):
    anim="" if STATIC else f"""
    <style>
      .enter {{ opacity:0; animation: rise .75s cubic-bezier(.2,.8,.2,1) {delay}s forwards; }}
      .fade {{ opacity:0; animation: fade .8s ease {delay+.2}s forwards; }}
      .shine {{ animation: sweep 5s ease-in-out {delay+2}s infinite; }}
      @keyframes rise {{ from {{ opacity:0; transform:translateY(18px) }} to {{ opacity:1; transform:translateY(0) }} }}
      @keyframes fade {{ to {{ opacity:1 }} }}
      @keyframes sweep {{ 0%,65% {{ transform:translateX(-180px) }} 85%,100% {{ transform:translateX(260px) }} }}
      @media (prefers-reduced-motion:reduce) {{ * {{ animation:none!important; opacity:1!important; transform:none!important }} }}
    </style>"""
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{defs}{anim}{body}</svg>'

def card_bg(w,h):
    return f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="22" fill="{PAPER}" stroke="{LINE}"/>'

def write(name,content):
    OUT.mkdir(exist_ok=True); (OUT/name).write_text(content,encoding="utf-8")

def hero():
    body=card_bg(960,210)+f"""
    <g class="enter">
      <text x="42" y="52" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12" letter-spacing="3">HELLO, WORLD — I'M</text>
      <text x="40" y="126" fill="{INK}" font-family="Georgia,serif" font-size="68" letter-spacing="-2">Ishaan Rai</text>
      <rect x="42" y="151" width="7" height="7" rx="3.5" fill="{BLUE}"/>
      <text x="60" y="160" fill="{INK}" font-family="Arial,sans-serif" font-size="16">AI/ML Engineer · Full-Stack Developer · Product Builder</text>
      <text x="42" y="187" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12">Turning curious ideas into useful, intelligent products.</text>
    </g>
    <g transform="translate(760 42)" class="fade">
      <circle cx="75" cy="62" r="57" fill="#e9efff"/>
      <circle cx="75" cy="62" r="43" fill="none" stroke="{BLUE}" stroke-width="1.5" stroke-dasharray="5 7"/>
      <path d="M48 67 L68 87 L105 39" fill="none" stroke="{BLUE}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
      <text x="75" y="143" text-anchor="middle" fill="{MUTED}" font-family="Arial,sans-serif" font-size="10" letter-spacing="2">BUILD / LEARN / SHIP</text>
    </g>"""
    write("hero.svg",svg_wrap(960,210,body))

def tile(name,kicker,title,desc,color,index):
    w,h=310,154
    body=card_bg(w,h)+f"""
    <g class="enter">
      <rect x="22" y="22" width="34" height="4" rx="2" fill="{color}"/>
      <text x="22" y="52" fill="{MUTED}" font-family="Arial,sans-serif" font-size="10" letter-spacing="2">{kicker}</text>
      <text x="22" y="91" fill="{INK}" font-family="Georgia,serif" font-size="28">{title}</text>
      <text x="22" y="119" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12">{desc}</text>
      <text x="276" y="132" fill="{color}" font-family="Arial,sans-serif" font-size="22">↗</text>
    </g>"""
    write(name,svg_wrap(w,h,body,delay=index*.18))

def activity(data):
    days=data.get("days",[])
    monthly=defaultdict(lambda:{"active":0,"count":0})
    for d in days:
        month=d["date"][:7]
        if d.get("level",0)>0: monthly[month]["active"]+=1
        monthly[month]["count"]+=d.get("count",0)
    months=sorted(monthly)[-8:]
    vals=[monthly[m]["count"] for m in months]
    peak=max(vals or [0])
    body=card_bg(960,230)+f'<text x="34" y="43" fill="{INK}" font-family="Georgia,serif" font-size="27">A little progress, every day.</text>'
    body+=f'<text x="35" y="67" fill="{MUTED}" font-family="Arial,sans-serif" font-size="11">MONTHLY CONTRIBUTIONS · LAST {len(months)} AVAILABLE MONTHS</text>'
    if not months:
        body+=f'<text x="35" y="145" fill="{MUTED}" font-family="Arial,sans-serif" font-size="14">Contribution history will appear after the first successful refresh.</text>'
    else:
        for i,m in enumerate(months):
            x=48+i*108; v=vals[i]; bh=90*(v/peak) if peak else 2
            body+=f'<rect class="enter" style="animation-delay:{i*.07}s" x="{x}" y="{169-bh:.1f}" width="42" height="{bh:.1f}" rx="7" fill="{BLUE if v==peak and peak else "#c9d9ff"}"/>'
            body+=f'<text x="{x+21}" y="192" text-anchor="middle" fill="{MUTED}" font-family="Arial,sans-serif" font-size="10">{escape(m[5:])}</text>'
            body+=f'<text x="{x+21}" y="{157-bh:.1f}" text-anchor="middle" fill="{INK}" font-family="Arial,sans-serif" font-size="10">{v}</text>'
    total=sum(d.get("count",0) for d in days)
    active=sum(1 for d in days if d.get("level",0)>0)
    body+=f'<text x="835" y="104" fill="{BLUE}" font-family="Georgia,serif" font-size="31">{total}</text><text x="835" y="124" fill="{MUTED}" font-family="Arial,sans-serif" font-size="10">CONTRIBUTIONS</text>'
    body+=f'<text x="835" y="159" fill="{INK}" font-family="Georgia,serif" font-size="25">{active}</text><text x="835" y="178" fill="{MUTED}" font-family="Arial,sans-serif" font-size="10">ACTIVE DAYS</text>'
    write("activity.svg",svg_wrap(960,230,body,delay=.35))

def heatmap(data):
    days=data.get("days",[])
    body=card_bg(960,145)+f'<text x="32" y="37" fill="{INK}" font-family="Georgia,serif" font-size="24">The contribution trail</text>'
    body+=f'<text x="33" y="57" fill="{MUTED}" font-family="Arial,sans-serif" font-size="10">DAILY ACTIVITY · BLUE INK EDITION</text>'
    if not days:
        body+=f'<text x="33" y="100" fill="{MUTED}" font-family="Arial,sans-serif" font-size="13">Your contribution squares will populate here.</text>'
    else:
        start=days[0]["date"]
        for i,d in enumerate(days[-371:]):
            x=32+(i//7)*13; y=75+(i%7)*9
            level=d.get("level",0)
            fill=["#eeeae2","#d8e4ff","#9dbbff","#5d91fa","#245ed0"][max(0,min(4,level))]
            body+=f'<rect class="fade" style="animation-delay:{i*.002}s" x="{x}" y="{y}" width="9" height="6" rx="2" fill="{fill}"/>'
    write("contributions.svg",svg_wrap(960,145,body,delay=.6))

def repo(name,title,tagline,stack,color,idx):
    w,h=470,142
    body=card_bg(w,h)+f"""
    <g class="enter">
      <circle cx="31" cy="31" r="5" fill="{color}"/>
      <text x="48" y="36" fill="{MUTED}" font-family="Arial,sans-serif" font-size="10" letter-spacing="1.5">{stack}</text>
      <text x="25" y="79" fill="{INK}" font-family="Georgia,serif" font-size="25">{title}</text>
      <text x="25" y="106" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12">{tagline}</text>
      <text x="425" y="112" fill="{color}" font-family="Arial,sans-serif" font-size="21">↗</text>
    </g>"""
    write(name,svg_wrap(w,h,body,delay=.8+idx*.12))

def main():
    data=load_data()
    hero()
    tile("build.svg","01 / BUILD","Ship real things","From idea to working product",BLUE,0)
    tile("intelligence.svg","02 / INTELLIGENCE","Make it smarter","AI that solves real problems",RED,1)
    tile("learn.svg","03 / LEARN","Stay curious","Experiment. Improve. Repeat.",GOLD,2)
    activity(data); heatmap(data)
    repo("repo-nexanote.svg","NexaNote","A focused space for notes and ideas","WEB · JAVASCRIPT",BLUE,0)
    repo("repo-blind-assistant.svg","Blind Assistant","Assistive vision and navigation tools","PYTHON · COMPUTER VISION",RED,1)
    repo("repo-mathsclarity.svg","MathsClarity AI","Detecting misconceptions in math work","NEXT.JS · AI",GOLD,2)
    repo("repo-codecubical.svg","Code Cubical","Building and shipping community projects","WEB · PRODUCT",BLUE,3)
    print(f"Rendered SVG cards to {OUT} (STATIC={int(STATIC)})")
if __name__=="__main__": main()

# Initial render trigger: the scheduled workflow also refreshes this file's output daily.
