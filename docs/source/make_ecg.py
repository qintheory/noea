"""Re-draw the Hong Kong Heartbeat ECG (qintheory/hkheartbeat, ecg-ui.js) as slide assets.

Same waveform as the published D3 code: a Gaussian R-peak per year (height = R value),
beat spacing from RR days (capped at 500, compressed 0.6x from 1960), and the sinusoidal
'organic' baseline. Rows wrap like the original. Scaled down to sit on a slide.
The published code reads S_Value, which its CSV doesn't have (the column is
Max_Dry_Season_Rainfall), so it never actually draws S dips; neither does this.
"""
import csv, math, random, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

CSV, OUT = sys.argv[1], sys.argv[2]
DEEP = "#00526F"
SCALE_X, SCALE_Y, NOISE = 0.13, 0.28, 0.5       # SCALE_Y / NOISE reduced from 0.3 / 1.0 to fit a slide
WRAP, IMG_W, IMG_H, BASE = 10**9, 1850, 240, 50   # ONE row: no wrapping; the whole series is squeezed to fit
IN_PER_PX = 11.333 / IMG_W

rows_csv = list(csv.DictReader(open(CSV)))
random.seed(7)
rows, cur, x = [], [], 0.0
for i, d in enumerate(rows_csv):
    r = float(d["R_Value"]); raw = float(d["RR_Days"]) if d["RR_Days"] else 0.0
    yr = int(d["Date"][:4]); tsf = 1 if yr < 1960 else 0.6
    spacing = min(raw, 500) * SCALE_X * tsf
    amp = r * SCALE_Y; chaos = 0.8 + random.random() * 0.6
    for j in range(int(math.ceil(spacing))):
        sin1 = math.sin(j * 0.2 + i * 0.2) * 12 * chaos
        sin2 = math.sin(j * 0.5 + i) * 6 * chaos
        perlin = math.sin(j * 0.03 + i * 0.1) * 20 * chaos
        drift = math.sin(j * 0.005 + i) * 15 * chaos
        rpeak = amp * math.exp(-((j - spacing / 2) / 10) ** 2)      # up
        cur.append((x + j, NOISE * (sin1 + sin2 + perlin + drift) + rpeak))
    x += spacing
    if x > WRAP:
        rows.append(cur); cur = []; x = 0.0
if cur: rows.append(cur)
FIT = 1780.0 / max(p[0] for p in rows[0])
rows = [[(px * FIT, py) for px, py in rows[0]]]
print("squeeze factor", round(FIT, 3))
print("rows:", len(rows), "points:", [len(r) for r in rows], "max x:", max(p[0] for r in rows for p in r))

def render_row(pts, scale=2, path=None):
    fig = plt.figure(figsize=(IMG_W * IN_PER_PX, IMG_H * IN_PER_PX), dpi=100 * scale / (IN_PER_PX * 100) if False else 220)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=DEEP, lw=1.0, solid_joinstyle="round")
    ax.set_xlim(0, IMG_W); ax.set_ylim(-BASE, IMG_H - BASE)
    fig.patch.set_alpha(0)
    fig.savefig(path, transparent=True); plt.close(fig)

paths = []
for k, pts in enumerate(rows, 1):
    p = f"{OUT}/ecg_row{k}.png"; render_row(pts, path=p); paths.append(p)
print(Image.open(paths[0]).size)

# ---- animated GIF: rows drawn one after another, left to right ----
GW = 1400
imgs = [Image.open(p).convert("RGBA") for p in paths]
iw, ih = imgs[0].size
sc = GW / iw; rh = int(ih * sc)
imgs = [im.resize((GW, rh), Image.LANCZOS) for im in imgs]
PITCH = rh
H = PITCH * (len(imgs) - 1) + rh + 20
FPS, SEC_PER_ROW, HOLD = 15, 7.0, 2.5
frames = []
def compose(done, partial_idx, frac):
    canvas = Image.new("RGBA", (GW, H), (255, 255, 255, 255))
    for k, im in enumerate(imgs):
        y = 10 + k * PITCH
        if k < done: canvas.alpha_composite(im, (0, y))
        elif k == partial_idx and frac > 0:
            w = max(1, int(GW * frac)); canvas.alpha_composite(im.crop((0, 0, w, rh)), (0, y))
    return canvas.convert("RGB")
n = int(FPS * SEC_PER_ROW)
for k in range(len(imgs)):
    for f in range(1, n + 1): frames.append(compose(k, k, f / n))
for _ in range(int(FPS * HOLD)): frames.append(compose(len(imgs), -1, 0))
ref = frames[len(imgs) * n].convert("P", palette=Image.ADAPTIVE, colors=24)   # fully drawn frame -> ONE shared palette
pal = [f.quantize(palette=ref, dither=Image.NONE) for f in frames]
pal[0].save(f"{OUT}/hk-heartbeat.gif", save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0, optimize=True, disposal=1)
import os; print("gif", len(frames), "frames", round(os.path.getsize(f"{OUT}/hk-heartbeat.gif") / 1e6, 2), "MB", frames[0].size)
