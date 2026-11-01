"""포스터 HTML을 만들어 헤드리스 Chrome으로 PNG로 내보낸다.

python source/build.py   → banners/, posters/ 에 PNG 저장
"""
import asyncio
import base64
import re
from pathlib import Path

from PIL import Image
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source"
LIME = "#C8FF3D"

SPEAKERS = [
    dict(key="parkhs", name="박해선", time="13:10", verb="이해하고", word="이해", role="Google AI/Cloud GDE",
         sub="&lt;혼자 공부하는 머신러닝+딥러닝&gt; 저자",
         title="LR부터 Jev까지<br>텍스트 분류를 가로지르는<br>히치하이커를 위한 안내서",
         line="LR부터 Jev까지 텍스트 분류를 가로지르는 히치하이커를 위한 안내서"),
    dict(key="heos", name="허석", time="14:10", verb="부리고", word="부림", role="드림아이시스템 · 정보전략실 · 이사",
         sub="Microsoft MVP · Business Applications",
         title="데이터 분석가, 이제 안 뽑아도 되나요?<br>처음부터 끝까지 말로 하는<br>에이전틱 BI",
         line="데이터 분석가, 이제 안 뽑아도 되나요? 처음부터 끝까지 말로 하는 에이전틱 BI"),
    dict(key="leejs", name="이재석", time="15:40", verb="다스리기", word="다스림", role="프리랜서",
         sub="Microsoft MVP · Business Applications",
         title="당신의 에이전트는<br>안녕하신가요?",
         line="당신의 에이전트는 안녕하신가요?"),
]


def uri(path: Path) -> str:
    mime = "image/png" if path.suffix == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def cutout(key: str) -> str:
    """투명 여백을 잘라 인물 크기를 판형마다 맞추기 쉽게 한다."""
    out = SRC / "cutouts" / f"{key}-trim.png"
    if not out.exists():
        im = Image.open(SRC / "cutouts" / f"{key}.png").convert("RGBA")
        im.crop(im.getchannel("A").point(lambda v: 255 if v > 12 else 0).getbbox()).save(out)
    return uri(out)


CUT = {}
TECHIVE = GIST = ""

CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:#000}}
body{{font-family:'Pretendard Variable',Pretendard,sans-serif;word-break:keep-all;color:#fff;-webkit-font-smoothing:antialiased}}
.p{{position:relative;overflow:hidden;background:#0A0C07;}}
.p::before{{content:"";position:absolute;inset:0;background:radial-gradient(70% 60% at var(--gx,72%) var(--gy,48%),rgba(200,255,61,.30),rgba(200,255,61,0) 72%);}}
.noise{{position:absolute;inset:0;opacity:.16;mix-blend-mode:overlay;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");}}
.big{{position:absolute;font-weight:900;letter-spacing:-.05em;line-height:.8;white-space:nowrap;
  background:linear-gradient(180deg,#DCFF6B 0%,{LIME} 42%,#5E7F12 78%,rgba(40,56,8,.25) 100%);-webkit-background-clip:text;background-clip:text;color:transparent;}}
.ghost{{position:absolute;font-weight:900;letter-spacing:-.05em;line-height:.8;white-space:nowrap;color:transparent;-webkit-text-stroke:2px rgba(200,255,61,.28);}}
.fade{{position:absolute;left:0;right:0;background:linear-gradient(180deg,rgba(10,12,7,0),#0A0C07 78%);}}
.cut{{position:absolute;display:block;filter:contrast(1.05);-webkit-mask-image:linear-gradient(90deg,transparent 0,#000 12%,#000 88%,transparent 100%);mask-image:linear-gradient(90deg,transparent 0,#000 12%,#000 88%,transparent 100%);}}
h1{{font-weight:900;letter-spacing:-.045em;line-height:1.06;text-shadow:0 2px 24px rgba(0,0,0,.65)}}
h1 b{{color:{LIME};font-weight:900}}
.kick{{font-weight:700;letter-spacing:-.02em}}
.lab{{font-weight:800;letter-spacing:.14em;color:{LIME}}}
.date{{font-weight:900;letter-spacing:-.03em;line-height:1.05}}
.time{{font-weight:900;letter-spacing:-.03em;color:{LIME};line-height:1.1}}
.bar{{border-left:3px solid {LIME}}}
.foot{{position:absolute;left:0;right:0;bottom:0;display:flex;align-items:center;background:#080906;border-top:1px solid rgba(200,255,61,.28);}}
.foot small{{color:#8E9484;font-weight:500}}
.foot img{{display:block;object-fit:contain}}
.names{{position:absolute;display:grid;border-top:1px solid rgba(200,255,61,.45)}}
.names>div{{position:relative;text-align:center}}
.names>div::before{{content:"";position:absolute;top:0;left:50%;width:9px;height:9px;margin:-5px 0 0 -4.5px;border-radius:50%;background:{LIME};box-shadow:0 0 12px {LIME}}}
.names b{{display:block;font-weight:800;letter-spacing:-.02em}}
.names i{{display:block;font-style:normal;color:#B6BCA9;font-weight:500}}
.free{{display:inline-block;background:{LIME};color:#0A0C07;font-weight:900;border-radius:999px;letter-spacing:-.02em}}
"""


def foot(h, fs, pad, logo):
    return f"""<div class="foot" style="height:{h}px;padding:0 {pad}px;gap:{pad // 2}px;font-size:{fs}px">
<small>주최</small><img src="{TECHIVE}" style="height:{logo}px;width:{logo}px;border-radius:{logo // 6}px"><b style="font-weight:800">Techive</b>
<span style="width:1px;height:{logo}px;background:#343829"></span>
<small>후원</small><img src="{GIST}" style="height:{logo}px;width:{int(logo * 1.06)}px;background:#fff;border-radius:{logo // 6}px;padding:{logo // 10}px"><b style="font-weight:800">광주과학기술원</b>
<span style="margin-left:auto;color:{LIME};font-weight:900">무료 · 노트북 지참</span></div>"""


def names(style, fb, fi, pt):
    cells = "".join(f'<div style="padding-top:{pt}px"><b style="font-size:{fb}px">{s["name"]}</b>'
                    f'<i style="font-size:{fi}px;margin-top:{fi // 3}px">{s["time"]} · {s["verb"]}</i></div>' for s in SPEAKERS)
    return f'<div class="names" style="grid-template-columns:repeat(3,1fr);{style}">{cells}</div>'


def trio(left, bottom, width, each, gap=0):
    """가운데 인물을 앞으로 세운 3인 배치. width는 전체 폭, each는 인물 한 명 폭."""
    step = (width - each) / 2
    order = [(0, 1), (2, 1), (1, 2)]  # 양쪽 먼저, 가운데를 위에
    html = ""
    for i, z in order:
        k = SPEAKERS[i]["key"]
        html += f'<img class="cut" src="{CUT[k]}" style="left:{left + step * i:.0f}px;bottom:{bottom}px;width:{each}px;z-index:{z}">'
    return html


def info(fs_lab, fs_date, fs_time, fs_ven, gap, pad=22):
    return f"""<div class="bar" style="padding-left:{pad}px">
<div class="lab" style="font-size:{fs_lab}px">DATE</div>
<div class="date" style="font-size:{fs_date}px;margin-top:{gap // 2}px">2026. 11. 07. SAT</div>
<div class="time" style="font-size:{fs_time}px;margin-top:{gap // 3}px">13:00 – 17:30</div>
<div class="lab" style="font-size:{fs_lab}px;margin-top:{gap}px">VENUE</div>
<div style="font-size:{fs_ven}px;font-weight:800;margin-top:{gap // 2}px;letter-spacing:-.02em">GIST AI대학원 2층 테드홀</div>
<div style="font-size:{int(fs_ven * .72)}px;color:#A3A996;margin-top:{gap // 4}px">전남광주통합특별시 북구 첨단과기로 123</div>
</div>"""


def base(w, h, body, gx="72%", gy="48%"):
    return f'<div class="p" id="poster" style="width:{w}px;height:{h}px;--gx:{gx};--gy:{gy}">{body}<div class="noise"></div></div>'


TITLE = 'AI 에이전트를<br><b>이해하고 부리고</b><br><b>다스리기</b>'


def facebook():
    return base(1200, 630, f"""
<div class="ghost" style="right:-12px;top:44px;font-size:520px;transform:translate(-14px,-10px)">AI</div>
<div class="big" style="right:-12px;top:44px;font-size:520px">AI</div>
{trio(500, 118, 700, 300)}
<div class="fade" style="bottom:70px;height:110px;z-index:3"></div>
<div style="position:absolute;left:52px;top:44px;z-index:5;width:560px">
<div class="kick" style="font-size:22px">Techive 여덟 번째 발표</div>
<h1 style="font-size:60px;margin-top:12px">{TITLE}</h1>
<div style="margin-top:24px">{info(13, 38, 32, 21, 14)}</div>
</div>
<div style="z-index:5;position:absolute;inset:0">{names("left:560px;right:40px;bottom:74px;background:linear-gradient(180deg,rgba(10,12,7,.2),rgba(10,12,7,.9))", 24, 14, 12)}</div>
<div style="z-index:6;position:absolute;inset:0">{foot(58, 16, 40, 34)}</div>""", gx="76%", gy="48%")


def linkedin():
    return base(1200, 1200, f"""
<div class="ghost" style="left:50%;top:392px;font-size:780px;transform:translate(-52%,-14px)">AI</div>
<div class="big" style="left:50%;top:392px;font-size:780px;transform:translateX(-50%)">AI</div>
{trio(70, 186, 1060, 480)}
<div class="fade" style="bottom:100px;height:190px;z-index:3"></div>
<div style="position:absolute;left:64px;top:56px;z-index:5;width:1080px">
<div class="kick" style="font-size:32px">Techive 여덟 번째 발표</div>
<h1 style="font-size:92px;margin-top:14px">AI 에이전트를 <b>이해하고<br>부리고 다스리기</b></h1>
<div style="margin-top:22px;display:flex;gap:44px;align-items:baseline;font-size:34px;font-weight:800;letter-spacing:-.02em">
<span>2026. 11. 07. SAT</span><span style="color:{LIME}">13:00 – 17:30</span><span style="font-size:27px;font-weight:600;color:#D5DAC9">GIST AI대학원 테드홀</span></div>
</div>
<div style="z-index:5;position:absolute;inset:0">{names("left:64px;right:64px;bottom:106px;background:rgba(10,12,7,.65)", 36, 21, 16)}</div>
<div style="z-index:6;position:absolute;inset:0">{foot(88, 23, 60, 52)}</div>""", gx="50%", gy="62%")


def tall(w, h, big, top_big, cut_each, cut_bottom, tfs):
    return base(w, h, f"""
<div class="ghost" style="left:50%;top:{top_big}px;font-size:{big}px;transform:translate(-52%,-14px)">AI</div>
<div class="big" style="left:50%;top:{top_big}px;font-size:{big}px;transform:translateX(-50%)">AI</div>
{trio(30, cut_bottom, w - 60, cut_each)}
<div class="fade" style="bottom:100px;height:230px;z-index:3"></div>
<div style="position:absolute;left:60px;right:60px;top:64px;z-index:5">
<div class="kick" style="font-size:34px">Techive 여덟 번째 발표</div>
<h1 style="font-size:{tfs}px;margin-top:16px">{TITLE}</h1>
<div style="margin-top:26px;display:flex;flex-wrap:wrap;gap:6px 30px;align-items:baseline;font-size:36px;font-weight:800;letter-spacing:-.02em">
<span>2026. 11. 07. SAT</span><span style="color:{LIME}">13:00 – 17:30</span></div>
<div style="margin-top:6px;font-size:29px;font-weight:600;color:#D5DAC9">GIST AI대학원 2층 테드홀</div>
</div>
<div style="z-index:5;position:absolute;inset:0">{names("left:60px;right:60px;bottom:106px;background:rgba(10,12,7,.7)", 38, 22, 16)}</div>
<div style="z-index:6;position:absolute;inset:0">{foot(88, 22, 44, 52)}</div>""", gx="50%", gy="66%")


def speaker(s):
    big = 800
    return base(1080, 1350, f"""
<div class="ghost" style="left:50%;top:290px;font-size:{big}px;transform:translate(-52%,-14px)">AI</div>
<div class="big" style="left:50%;top:290px;font-size:{big}px;transform:translateX(-50%)">AI</div>
<img class="cut" src="{CUT[s['key']]}" style="left:50%;bottom:300px;height:830px;max-width:none;transform:translateX(-50%);z-index:2">
<div class="fade" style="bottom:300px;height:220px;z-index:3"></div>
<div style="position:absolute;left:0;right:0;bottom:88px;height:300px;background:#0A0C07;z-index:3"></div>
<div style="position:absolute;left:60px;right:60px;top:56px;z-index:5;display:flex;justify-content:space-between;align-items:flex-start">
<div><div class="kick" style="font-size:28px">Techive 여덟 번째 발표</div>
<h1 style="font-size:56px;margin-top:10px">AI 에이전트를 <b>{s['verb']}</b></h1></div>
<div style="text-align:right"><div class="lab" style="font-size:18px">SESSION</div><div class="time" style="font-size:64px;margin-top:4px">{s['time']}</div></div>
</div>
<div style="position:absolute;left:60px;right:60px;bottom:116px;z-index:5">
<div style="display:flex;align-items:baseline;gap:18px"><span style="font-size:68px;font-weight:900;letter-spacing:-.03em">{s['name']}</span>
<span style="font-size:25px;font-weight:700;color:{LIME}">{s['role']}</span></div>
<div style="font-size:22px;color:#B6BCA9;margin-top:4px">{s['sub']}</div>
<div style="font-size:36px;font-weight:800;line-height:1.28;letter-spacing:-.03em;margin-top:18px">{s['title']}</div>
<div style="font-size:23px;font-weight:700;margin-top:16px;color:#E8ECDD">2026. 11. 07. SAT 13:00 – 17:30 · GIST AI대학원 2층 테드홀</div>
</div>
<div style="z-index:6;position:absolute;inset:0">{foot(88, 22, 44, 52)}</div>""", gx="50%", gy="46%")


def group():
    rows = "".join(f"""<div style="display:grid;grid-template-columns:108px 1fr;gap:18px;padding:13px 0;border-top:1px solid rgba(200,255,61,.28)">
<div class="time" style="font-size:32px">{s['time']}</div><div><div style="font-size:27px;font-weight:800;letter-spacing:-.02em">{s['name']} <span style="font-size:18px;font-weight:600;color:{LIME};margin-left:6px">{s['verb']}</span></div>
<div style="font-size:21px;color:#CFD4C3;margin-top:3px;letter-spacing:-.02em">{s['line']}</div></div></div>""" for s in SPEAKERS)
    return base(1080, 1350, f"""
<div class="ghost" style="left:50%;top:270px;font-size:680px;transform:translate(-52%,-14px)">AI</div>
<div class="big" style="left:50%;top:270px;font-size:680px;transform:translateX(-50%)">AI</div>
{trio(10, 425, 1060, 480)}
<div class="fade" style="bottom:425px;height:170px;z-index:3"></div>
<div style="position:absolute;left:0;right:0;bottom:88px;height:337px;background:#0A0C07;z-index:3"></div>
<div style="position:absolute;left:60px;right:60px;top:52px;z-index:5">
<div class="kick" style="font-size:28px">Techive 여덟 번째 발표</div>
<h1 style="font-size:66px;margin-top:10px">AI 에이전트를 <b>이해하고<br>부리고 다스리기</b></h1>
</div>
<div style="position:absolute;left:60px;right:60px;bottom:108px;z-index:5">
<div style="font-size:30px;font-weight:800;letter-spacing:-.02em;margin-bottom:14px">2026. 11. 07. SAT <span style="color:{LIME}">13:00 – 17:30</span> <span style="font-size:23px;font-weight:600;color:#D5DAC9;margin-left:8px">GIST AI대학원 2층 테드홀</span></div>
{rows}</div>
<div style="z-index:6;position:absolute;inset:0">{foot(88, 22, 44, 52)}</div>""", gx="50%", gy="42%")


async def main():
    global TECHIVE, GIST
    TECHIVE = uri(SRC / "logos" / "techive.png")
    GIST = uri(SRC / "logos" / "gist.png")
    for s in SPEAKERS:
        CUT[s["key"]] = cutout(s["key"])
    jobs = {
        "banners/facebook-1200x630.png": facebook(),
        "banners/linkedin-1200x1200.png": linkedin(),
        "banners/instagram-1080x1350.png": tall(1080, 1350, 700, 500, 450, 186, 80),
        "banners/threads-1080x1440.png": tall(1080, 1440, 760, 540, 470, 186, 86),
        "posters/group-1080x1350.png": group(),
    }
    for s in SPEAKERS:
        jobs[f"posters/speaker-{s['key']}-1080x1350.png"] = speaker(s)
    head = ('<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">'
            f"<style>{CSS}</style>")
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome")
        for rel, html in jobs.items():
            out = ROOT / rel
            out.parent.mkdir(exist_ok=True)
            m = re.search(r"width:(\d+)px;height:(\d+)px", html)
            pg = await b.new_page(viewport={"width": int(m[1]), "height": int(m[2])})
            await pg.set_content(head + html, wait_until="networkidle")
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(400)
            await (await pg.query_selector("#poster")).screenshot(path=str(out))
            await pg.close()
            print(rel)
        await b.close()


asyncio.run(main())
