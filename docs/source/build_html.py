"""Single-file HTML version of the Noéa introduction deck. Same content and layout as the PowerPoint
(1920x1080 stage, 144 px per inch), with the Hong Kong ECG drawn as SVG paths that animate row by row."""
import base64, csv, html, math, random, sys

import os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content as T
CSV, DECK, OUT = HERE + "/data/r_rr_s_by_year.csv", HERE + "/assets", sys.argv[1]
def b64(p): return base64.b64encode(open(p, "rb").read()).decode()
LOGO, CHART = b64(f"{DECK}/logo.png"), b64(f"{DECK}/anomaly_ribbon.png")
DECOR, DECOR7 = b64(f"{DECK}/{T.GAP_DECOR}"), b64(f"{DECK}/{T.END_DECOR}")
WORDMARK = b64(f"{DECK}/noea_wordmark_web.png")

# ---- ECG rows: identical algorithm and seed to ecg_render.py (the hkheartbeat waveform) ----
SCALE_X, SCALE_Y, NOISE, WRAP, IMG_W, IMG_H, BASE = 0.13, 0.28, 0.5, 10**9, 1850, 240, 50
rows_csv = list(csv.DictReader(open(CSV)))
random.seed(7)
rows, cur, x = [], [], 0.0
for i, d in enumerate(rows_csv):
    r = float(d["R_Value"]); raw = float(d["RR_Days"]) if d["RR_Days"] else 0.0
    yr = int(d["Date"][:4]); tsf = 1 if yr < 1960 else 0.6
    spacing = min(raw, 500) * SCALE_X * tsf
    amp = r * SCALE_Y; chaos = 0.8 + random.random() * 0.6
    for j in range(int(math.ceil(spacing))):
        s1 = math.sin(j * 0.2 + i * 0.2) * 12 * chaos; s2 = math.sin(j * 0.5 + i) * 6 * chaos
        pl = math.sin(j * 0.03 + i * 0.1) * 20 * chaos; dr = math.sin(j * 0.005 + i) * 15 * chaos
        rp = amp * math.exp(-((j - spacing / 2) / 10) ** 2)
        cur.append((x + j, NOISE * (s1 + s2 + pl + dr) + rp))
    x += spacing
    if x > WRAP: rows.append(cur); cur = []; x = 0.0
if cur: rows.append(cur)
FIT = 1780.0 / max(p[0] for p in rows[0])
rows = [[(px * FIT, py) for px, py in rows[0]]]
BASELINE = IMG_H - BASE
def path(pts): return "M" + " ".join(f"{px:.1f},{BASELINE - py:.1f}" for px, py in pts)
ecg_svgs = (f'<svg class="ecg" style="top:605px" viewBox="0 0 {IMG_W} {IMG_H}" aria-hidden="true">'
            f'<path class="ecg-line" style="--delay:0.5s;--dur:7s" pathLength="1" d="{path(rows[0])}"/></svg>')

E = html.escape
def EI(t): return E(t).replace("Noéa", "<i>Noéa</i>")      # the name is always italic
def slide(n, body, notes, footer=True, num=True, logo_right=False):
    f = ""
    if footer:
        f = f'<img class="logo{" logo-r" if logo_right else ""}" alt="Meeting of Waters" src="data:image/png;base64,{LOGO}">'
        if num: f += f'<div class="num">{n}</div>'
    return f'<section class="slide" data-notes="{E(notes, quote=True)}">{body}{f}</section>\n'

S = []
# 1 cover
S.append(slide(1, f'''
<img class="abs" alt="noéa" src="data:image/png;base64,{WORDMARK}" style="left:144px;top:122px;height:166px">
<div class="abs" style="left:144px;top:346px;width:1632px;font:italic 400 50px/1.1 var(--head);color:var(--deep)">{EI(T.COVER_TAGLINE)}</div>
<div class="abs" style="left:144px;top:439px;width:1632px;font:400 27px/1.2 var(--body);color:var(--grey)">{EI(T.COVER_SUBTITLE)}</div>
{ecg_svgs}
<div class="abs" style="left:144px;top:929px;width:1632px;font:400 20px/1.2 var(--body);color:var(--grey)">{EI(T.COVER_CAPTION)}</div>
''', T.SPEAKER_NOTES[1], num=False, logo_right=True))
# 2 gap
S.append(slide(2, f'''
<img class="abs" alt="" src="data:image/jpeg;base64,{DECOR}" style="left:{(13.333 - 5.13) * 144:.0f}px;top:0;width:{5.13 * 144:.0f}px;height:1080px">
<div class="abs" style="left:144px;top:317px;width:1632px;font:400 77px/1.1 var(--head);color:var(--ink)">{"<br>".join(EI(t) for t in T.GAP_TITLE)}</div>
<div class="abs rule-short" style="left:144px;top:662px"></div>
<div class="abs" style="left:144px;top:698px;width:1632px;font:italic 400 37px/1.15 var(--head);color:var(--deep)">{EI(T.GAP_LINE)}</div>
''', T.SPEAKER_NOTES[2]))
# 3 how it reads
cols = ""
for i, (n, h, body, hot) in enumerate(T.READ_STEPS):
    left = 144 + i * 419
    cols += (f'<div class="abs {"rule-hot" if hot else "rule"}" style="left:{left}px;top:396px;width:374px"></div>'
             f'<div class="abs lab" style="left:{left}px;top:432px;color:var({"--deep" if hot else "--teal"})">{n}</div>'
             f'<div class="abs" style="left:{left}px;top:497px;width:374px;font:400 38.6px/1.0 var(--head)">{EI(h)}</div>'
             f'<div class="abs" style="left:{left}px;top:619px;width:369px;font:400 24.4px/1.12 var(--body);color:var({"--ink" if hot else "--grey"})">'
             + "".join(f'<p style="margin:0 0 14px">{EI(t)}</p>' for t in body) + '</div>')
cols += f'<div class="abs" style="left:144px;top:907px;width:1632px;font:400 20px/1.2 var(--body);color:var(--grey)">{EI(T.READ_SOURCE)}</div>'
S.append(slide(3, f'<div class="abs" style="left:144px;top:108px;width:1632px;font:400 60.5px/1.05 var(--head)">{EI(T.READ_TITLE)}</div>' + cols,
    T.SPEAKER_NOTES[3]))
# 4 universal
rowhtml = ""
for i, (name, detail, dim) in enumerate(T.UNIV_ROWS):
    y = 518 + i * 115
    rowhtml += (f'<div class="abs rule" style="left:144px;top:{y}px;width:1632px"></div>'
                f'<div class="abs" style="left:144px;top:{y + 29}px;width:605px;font:400 35.3px/1.1 var(--head);color:var({"--grey" if dim else "--ink"})">{EI(name)}</div>'
                f'<div class="abs" style="left:778px;top:{y + 39}px;width:998px;font:400 23.5px/1.2 var(--body);color:var(--grey)">{EI(detail)}</div>')
S.append(slide(4, f'<div class="abs" style="left:144px;top:108px;width:1632px;font:400 67px/1.05 var(--head)">{EI(T.UNIV_TITLE)}</div>'
    f'<div class="abs" style="left:144px;top:324px;width:1632px;font:400 45.4px/1.15 var(--head)">{EI(T.UNIV_LINE)}</div>' + rowhtml,
    T.SPEAKER_NOTES[4]))
# 5 layers
def layer(x, head, tag, tagcolor, bullets):
    return (f'<div class="abs" style="left:{x}px;top:367px;width:749px;font:400 53.8px/1.1 var(--head)">{EI(head)}</div>'
            f'<div class="abs lab" style="left:{x}px;top:461px;color:var({tagcolor})">{EI(tag)}</div>'
            f'<div class="abs" style="left:{x}px;top:547px;width:749px;font:400 27.7px/1.12 var(--body)">'
            + "".join(f'<p style="margin:0 0 24px">{EI(b)}</p>' for b in bullets) + '</div>')
S.append(slide(5, f'<div class="abs" style="left:144px;top:108px;width:1632px;font:400 67px/1.05 var(--head)">{EI(T.LAYERS_TITLE)}</div>'
    + layer(144, *T.LAYER_SCIENCE[:2], "--grey", T.LAYER_SCIENCE[2])
    + '<div class="abs" style="left:960px;top:374px;width:2px;height:562px;background:var(--rule)"></div>'
    + layer(1027, *T.LAYER_CURATORIAL[:2], "--deep", T.LAYER_CURATORIAL[2]),
    T.SPEAKER_NOTES[5]))
# 6 machine learning
S.append(slide(6, f'''<div class="abs" style="left:144px;top:108px;width:1632px;font:400 67px/1.05 var(--head)">{EI(T.ML_TITLE)}</div>
<div class="abs" style="left:144px;top:230px;width:1632px;font:400 26.9px/1.2 var(--body);color:var(--grey);white-space:nowrap">{EI(T.ML_SUBTITLE)}</div>
<img class="abs" alt="{E(T.ML_CHART_ALT)}" src="data:image/png;base64,{CHART}" style="left:144px;top:338px;width:1632px">
<div class="abs" style="left:144px;top:806px;width:1632px;font:400 25.2px/1.2 var(--body)"><b>{EI(T.ML_CALLOUT_BOLD)}</b> {EI(T.ML_CALLOUT_REST)}</div>
<div class="abs" style="left:144px;top:878px;width:1632px;font:400 20px/1.08 var(--body);color:var(--grey)"><p style="margin:0 0 6px;white-space:nowrap">{EI(T.ML_METHOD)}</p><p style="margin:0;white-space:nowrap">{EI(T.ML_LIMIT)}</p></div>''',
    T.SPEAKER_NOTES[6]))
# 7 end
S.append(slide(7, f'''<img class="abs" alt="" src="data:image/jpeg;base64,{DECOR7}" style="left:{7.9 * 144:.0f}px;top:{-0.6 * 144:.0f}px;width:{9 * 144}px;height:{9 * 144}px">
<div class="abs" style="left:144px;top:108px;width:1632px;font:400 67px/1.05 var(--head)">{E(T.END_TITLE)}</div>
<div class="abs" style="left:144px;top:374px;width:1240px;font:400 43.7px/1.15 var(--head)">{EI(T.END_LINE)}</div>
<div class="abs rule-short" style="left:144px;top:598px"></div>
<div class="abs" style="left:144px;top:634px;width:1240px;font:italic 400 37px/1.15 var(--head);color:var(--deep)">{EI(T.END_RESEARCH)}</div>
<a class="abs link" href="{T.END_URL}" style="right:259px;top:994px">{E(T.END_URL_TEXT)}</a>''',
    T.SPEAKER_NOTES[7]))

PAGE = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Noéa — an introduction</title>
<link rel="preconnect" href="https://use.typekit.net" crossorigin>
<link rel="stylesheet" href="https://use.typekit.net/pwm6lyt.css">
<style>
:root {{ --ink:#111A20; --deep:#00526F; --teal:#5390A2; --grey:#5F6F78; --rule:#D3DDE2;
  /* the same Adobe Fonts kit the meetingofwaters.org Webflow site uses (athelas, neue-frutiger-world);
     installed copies and common fallbacks follow it */
  --head: athelas, Athelas, "Iowan Old Style", Georgia, serif;
  --body: neue-frutiger-world, "Neue Frutiger World", Frutiger, "Helvetica Neue", Arial, sans-serif; }}
* {{ box-sizing:border-box }}
html, body {{ margin:0; height:100%; background:#fff; overflow:hidden }}
.stage {{ position:absolute; left:50%; top:50%; width:1920px; height:1080px; transform:translate(-50%,-50%) scale(var(--s,1)); transform-origin:center; background:#fff; box-shadow:0 0 0 1px #eef2f5 }}
.slide {{ position:absolute; inset:0; display:none; background:#fff; overflow:hidden }}
.slide.active {{ display:block }}
.abs {{ position:absolute }}
.rule {{ height:2.5px; background:var(--rule) }}
.rule-hot {{ height:6px; background:var(--deep) }}
.rule-short {{ width:173px; height:6px; background:var(--deep) }}
.lab {{ font:700 21px/1 var(--body); letter-spacing:2.6px; text-transform:uppercase }}
.logo {{ position:absolute; left:144px; top:982px; height:46px }}
.logo-r {{ left:auto; right:144px; top:137px }}
.num {{ position:absolute; right:144px; top:994px; font:400 20px/1 var(--body); color:var(--grey) }}
.link {{ font:700 20px/1 var(--body); color:var(--deep); text-decoration:none }}
b {{ font-weight:700 }}
.ecg {{ position:absolute; left:144px; width:1632px; height:211.7px; overflow:visible }}
.ecg-line {{ fill:none; stroke:var(--deep); stroke-width:2.27; stroke-linejoin:round; stroke-dasharray:1; stroke-dashoffset:1 }}
.slide.play .ecg-line {{ animation: draw var(--dur,7s) linear var(--delay) forwards }}
@keyframes draw {{ to {{ stroke-dashoffset:0 }} }}
.notes {{ position:fixed; left:0; right:0; bottom:0; padding:14px 24px; background:rgba(17,26,32,.94); color:#fff; font:400 16px/1.45 var(--body); display:none; z-index:5 }}
.notes.on {{ display:block }}
.hint {{ position:fixed; right:14px; bottom:10px; font:400 12px var(--body); color:#9aa8b0; z-index:4 }}
@media (prefers-reduced-motion: reduce) {{ .ecg-line {{ stroke-dashoffset:0 !important; animation:none !important }} }}
@media print {{
  @page {{ size:1920px 1080px; margin:0 }}
  html, body {{ overflow:visible; height:auto }}
  .stage {{ position:static; transform:none; width:1920px; height:auto; box-shadow:none }}
  .slide {{ display:block; position:relative; height:1080px; page-break-after:always }}
  .ecg-line {{ stroke-dashoffset:0 !important; animation:none !important }}
  .notes, .hint {{ display:none !important }}
}}
</style></head>
<body>
<div class="stage" id="stage">
{"".join(S)}</div>
<div class="notes" id="notes"></div>
<div class="hint">← → to move · N notes · R replay · F fullscreen</div>
<script>
(function () {{
  var stage = document.getElementById('stage'), slides = [].slice.call(document.querySelectorAll('.slide')),
      notes = document.getElementById('notes'), i = 0;
  function fit() {{ stage.style.setProperty('--s', Math.min(innerWidth / 1920, innerHeight / 1080)); }}
  function play(el) {{ el.classList.remove('play'); void el.offsetWidth; el.classList.add('play'); }}
  function show(n) {{
    i = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach(function (s, k) {{ s.classList.toggle('active', k === i); }});
    notes.textContent = slides[i].getAttribute('data-notes') || '';
    if (i === 0) play(slides[0]); else slides[0].classList.remove('play');
    try {{ history.replaceState(null, '', '#' + (i + 1)); }} catch (e) {{}}
  }}
  addEventListener('resize', fit);
  addEventListener('keydown', function (e) {{
    var k = e.key;
    if (k === 'ArrowRight' || k === 'PageDown' || k === ' ' || k === 'Enter') {{ show(i + 1); e.preventDefault(); }}
    else if (k === 'ArrowLeft' || k === 'PageUp' || k === 'Backspace') {{ show(i - 1); e.preventDefault(); }}
    else if (k === 'Home') show(0); else if (k === 'End') show(slides.length - 1);
    else if (k === 'n' || k === 'N') notes.classList.toggle('on');
    else if (k === 'r' || k === 'R') {{ if (i === 0) play(slides[0]); }}
    else if (k === 'f' || k === 'F') {{ if (!document.fullscreenElement) document.documentElement.requestFullscreen && document.documentElement.requestFullscreen(); else document.exitFullscreen(); }}
  }});
  stage.addEventListener('click', function (e) {{
    if (e.target.closest('a')) return;
    var r = stage.getBoundingClientRect(); show(e.clientX - r.left > r.width * 0.3 ? i + 1 : i - 1);
  }});
  var tx = null;
  addEventListener('touchstart', function (e) {{ tx = e.touches[0].clientX; }}, {{ passive: true }});
  addEventListener('touchend', function (e) {{ if (tx === null) return; var d = e.changedTouches[0].clientX - tx; if (Math.abs(d) > 40) show(i + (d < 0 ? 1 : -1)); tx = null; }});
  fit(); show((parseInt((location.hash || '#1').slice(1), 10) || 1) - 1);
}})();
</script></body></html>
'''
open(OUT, "w", encoding="utf-8").write(PAGE)
import os; print("wrote", OUT, round(os.path.getsize(OUT) / 1024), "KB |", len(rows), "ECG rows,", sum(len(r) for r in rows), "points")
