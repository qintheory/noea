"""Bake the slide-2 decorative panel, so every renderer (PowerPoint, Keynote, PDF, browser) shows the same thing.

  slide2_decor.jpg   river close-up, a 5.13 x 7.5 in panel for the right edge of slide 2, wall flat-fielded to white (no gradient, no visible edge)

Run from the repository root:  python3 docs/source/make_background.py docs/source/assets
"""
import sys
import numpy as np
from PIL import Image

OUT = sys.argv[1]

# ---- slide 2: river panel ----
# The left part of the close-up (its left edge only clips fine branch tips), flat-fielded so the wall becomes pure white:
# the wall is divided out per colour channel (a blurred local maximum), so the panel has no visible edge on a white slide.
from scipy import ndimage as ndi
riv = Image.open(f"{OUT}/river_closeup.jpg").convert("RGB")
w, h = riv.size
pw = round(h * 5.13 / 7.5)                                             # panel is 5.13 x 7.5 in
a = np.asarray(riv.crop((0, 0, pw, h))).astype(float)
wall = np.stack([ndi.gaussian_filter(ndi.maximum_filter(a[..., c], size=71), 35) for c in range(3)], axis=2)
out = np.clip(a / np.maximum(wall, 1) * 255 * 1.06, 0, 255)
Image.fromarray(out.astype("uint8")).save(f"{OUT}/slide2_decor.jpg", quality=92)
print("ok")
