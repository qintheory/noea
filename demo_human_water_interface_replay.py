"""
Human-Water Interface: replay L'Aire through the curatorial layer, three gauges.

Run (after the fetches described in demo_human_water_interface_model.py, plus hourly flow for CS_ and BS_):
      python3 demo_human_water_interface_replay.py

Fits a day-level model per gauge on 2014-2022, maps every day it can score to XRParameters, checks the whole
distribution (not just the days we expect to be interesting), and writes the frames to
noea/human_water_interface/data/aire_replay.json (not committed: derived from OCEau data).
"""
import json
from datetime import date

import numpy as np

from noea.human_water_interface import load_daily, load_intraday
from noea.human_water_interface.anomaly import fit_day_model
from noea.human_water_interface.loaders import DEFAULT_DATA_DIR, STATIONS
from noea.human_water_interface.mapping import map_series

TRAIN = list(range(2014, 2023))
GAUGES = ["BS_", "CS_", "PR_"]
CHECK_DAYS = [date(2024, 6, 9), date(2023, 12, 1), date(2022, 8, 10), date(2023, 7, 24)]


def main():
    out = {}
    for g in GAUGES:
        meta = STATIONS[g]
        flow, rain = load_intraday(g, "flow", "hourly"), load_daily(meta["rain"], "rain")
        m = fit_day_model(flow, rain, TRAIN)
        frames = map_series(m, g)
        out[g] = [f.as_dict() for f in frames]
        v = np.array([f.valence for f in frames]); a = np.array([f.arousal for f in frames])
        p95 = np.percentile(m.train_errors, 95)
        test = [s for d, s in m.scores.items() if d.year >= 2023]
        print(f"\n{g} {meta['name']}  rain: {meta['rain']}  days mapped {len(frames)}  "
              f"variance kept {sum(m.explained_variance_ratio):.0%}  held-out above train p95: {np.mean([s > p95 for s in test]):.1%}")
        print(f"   valence: mean {v.mean():+.2f}, {np.mean(v < 0):.0%} of days negative, {np.mean(v <= -0.99):.1%} at the floor | "
              f"arousal: mean {a.mean():.2f}, p95 {np.percentile(a, 95):.2f}")
        by = {f.timestamp: f for f in frames}
        for d in CHECK_DAYS:
            if d in by:
                f = by[d]
                print(f"   {d}: valence {f.valence:+.2f}  arousal {f.arousal:.2f}  diameter {f.diameter:.2f}  texture {f.texture:.2f}")
        top = sorted(frames, key=lambda f: f.valence)[:3]
        print("   most negative days:", [(f.timestamp.isoformat(), f.valence) for f in top])
    path = DEFAULT_DATA_DIR.parent / "aire_replay.json"
    path.write_text(json.dumps(out))
    print(f"\nwrote {path.name}: {sum(len(v) for v in out.values())} frames")


if __name__ == "__main__":
    main()
