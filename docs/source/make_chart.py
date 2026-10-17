"""Anomaly ribbon for the machine-learning slide.

Same visual language as the longitudinal ribbon in Noéa Issue 6 ("River's Biography"): four Rhine
stations stacked flush on a shared spine, one column per year, height = that year's mean
discharge relative to the station's own mean. Colour here is the learned anomaly score (PCA
reconstruction error, one model per station, fit on that station's whole record), so the ribbon
shows what the model found unusual, not how much water flowed.

Run from the repository root:  python3 docs/source/make_chart.py docs/source/assets
"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Rectangle
sys.path.insert(0, ".")
from noea.climate_pulse.river import build_yearly, fit_anomaly_model, load_rhine_stations

OUT = sys.argv[1]
DEEP, TEAL, INK, GREY, GRID = "#00526F", "#5390A2", "#111A20", "#5F6F78", "#EDF1F4"
REG = fm.FontProperties(fname="/Library/Fonts/Frutiger.ttf")
BOLD = fm.FontProperties(fname="/Library/Fonts/Frutiger_bold.ttf")
fm.fontManager.addfont("/Library/Fonts/Frutiger.ttf"); plt.rcParams["font.family"] = REG.get_name()
cmap = LinearSegmentedColormap.from_list("anom", ["#E3ECF0", "#9FBFCC", "#3D7F96", DEEP, "#003244"])

Y0, Y1 = 1951, 2020                                  # the Issue 6 ribbon's period
STATIONS = [("Lustenau", "Lustenau"), ("Basel", "Basel"), ("Koeln", "Köln"), ("Lobith", "Lobith")]   # bottom to top
data = {}
for key, ts in load_rhine_stations().items():
    yearly = build_yearly(ts); model = fit_anomaly_model(yearly)
    fit = {y.year for y in yearly if y.n_days >= 300}
    mean_all = sum(y.mean_flow for y in yearly if y.year in fit) / len(fit)
    data[key] = {y.year: (y.mean_flow / mean_all, model.normalized(y.year)) for y in yearly if Y0 <= y.year <= Y1 and y.year in fit}
top = {k: max(v, key=lambda yr: v[yr][1]) for k, v in data.items()}      # highest-scoring year in the window
print({k: (top[k], round(data[k][top[k]][1], 2)) for k in top})

years = list(range(Y0, Y1 + 1))
fig, ax = plt.subplots(figsize=(11.33, 3.0), dpi=220)
for yr in years:
    heights = [data[k][yr][0] if yr in data[k] else 0 for k, _ in STATIONS]
    base = -sum(heights) / 2                                       # centre on the spine
    for (k, _), h in zip(STATIONS, heights):
        if yr in data[k]:
            sc = data[k][yr][1]
            ax.add_patch(Rectangle((yr - 0.42, base), 0.84, h, facecolor=cmap(sc), edgecolor="white", linewidth=0.35))
            if top[k] == yr:
                ax.add_patch(Rectangle((yr - 0.42, base), 0.84, h, facecolor="none", edgecolor=INK, linewidth=1.3, zorder=5))
        base += h
ymax = max(sum(data[k][yr][0] for k, _ in STATIONS if yr in data[k]) for yr in years) / 2
ax.set_xlim(Y0 - 3, Y1 + 1.5); ax.set_ylim(-ymax - 0.2, ymax + 0.5)
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
ax.spines["bottom"].set_color("#B9C7CF")
ax.set_yticks([]); ax.set_xticks(range(1960, 2021, 10))
ax.tick_params(axis="x", colors=GREY, labelsize=10, length=3)
for t in ax.get_xticklabels(): t.set_fontproperties(REG)
# year labels above the outlined columns (once per year if two stations share it)
for yr in sorted(set(top.values())):
    ax.annotate(str(yr), xy=(yr, ymax + 0.05), ha="center", va="bottom", fontsize=11, color=INK, fontproperties=BOLD)
# station names at the left, at each layer's typical height
typ = [sum(data[k][yr][0] for k, _ in STATIONS[:i]) + data[STATIONS[i][0]][yr][0] / 2 for i in range(4)
       for yr in [1951]]
tot = sum(data[k][1951][0] for k, _ in STATIONS)
for i, (k, label) in enumerate(STATIONS):
    ax.text(Y0 - 1.2, typ[i] - tot / 2, label, ha="right", va="center", fontsize=10.5, color=DEEP, fontproperties=BOLD)
# colour key
cax = fig.add_axes([0.70, 0.925, 0.16, 0.04])
cb = fig.colorbar(ScalarMappable(norm=plt.Normalize(0, 1), cmap=cmap), cax=cax, orientation="horizontal")
cb.set_ticks([]); cb.outline.set_visible(False)
fig.text(0.695, 0.945, "typical year", ha="right", va="center", fontsize=10, color=GREY, fontproperties=REG)
fig.text(0.865, 0.945, "most unusual", ha="left", va="center", fontsize=10, color=GREY, fontproperties=REG)
fig.subplots_adjust(left=0.07, right=0.985, top=0.86, bottom=0.12)
fig.patch.set_facecolor("white")
fig.savefig(f"{OUT}/anomaly_ribbon.png", facecolor="white"); plt.close(fig)
print("ok")
