from PIL import Image
base = Image.open("cover_base.png").convert("RGB")
ecg = Image.open("ecg_row1.png").convert("RGBA").resize((1632, 211), Image.LANCZOS)
X, Y, FPS, DELAY, DRAW, HOLD = 144, 605, 30, 0.5, 7.0, 2.5
n = int((DELAY + DRAW + HOLD) * FPS)
for i in range(n):
    t = i / FPS
    p = min(1.0, max(0.0, (t - DELAY) / DRAW))
    f = base.copy()
    w = int(round(p * ecg.width))
    if w > 0:
        part = ecg.crop((0, 0, w, ecg.height))
        f.paste(part, (X, Y), part)
    f.save(f"frames/f{i:04d}.png")
print(n, "frames")
