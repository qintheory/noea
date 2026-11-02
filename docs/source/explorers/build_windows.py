"""Compute the rolling-window traces for the Atmosphere and Rivers chapters and write docs/explore/data/windows.json.

    python3 docs/source/explorers/build_windows.py            # run from the repository root; a few minutes (one model per station and window length)

For each record (Hong Kong, then each river station) and each window length (30, 90, 365 days) the file holds the score of
the model of noea/climate_pulse/windows.py, one value per week: the highest score of any window ending that week, so a
single storm day is not averaged away. A score is a rank among the record's windows (0 to 1); it is stored as how rare it is,
u = -log10(1 - rank) times 100, so 100 means "one window in ten is this unusual", 200 one in a hundred, 300 one in a thousand. Windows that would need a day with no record are null. The documented events
(rainfall/events.py, river/events.py) go in beside the traces with where the model ranks them, so the page can mark them.
Kept apart from build_explorers.py because it is slow; build_site.py reads the file it writes.
"""
from __future__ import annotations
import json
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, ".")
from noea.climate_pulse.rainfall import load_rainfall
from noea.climate_pulse.rainfall.events import EVENTS as RAIN_EVENTS
from noea.climate_pulse.rainfall.rolling import check_events as rain_check, fit_rolling_model as rain_fit
from noea.climate_pulse.river import load_alpine_stations, load_rhine_stations
from noea.climate_pulse.river.events import EVENTS as RIVER_EVENTS
from noea.climate_pulse.river.rolling import check_events as river_check, fit_rolling_model as river_fit

OUT = Path("docs/explore/data/windows.json")
LENGTHS = (30, 90, 365)
STEP = 7


def weekly(model) -> dict:
    """The highest score per 7-day block, from the first window's end date, as 100 x -log10(1 - rank); null where no window could be formed."""
    d0 = model.ends[0]
    n = (model.ends[-1] - d0).days // STEP + 1
    v = np.full(n, -1)
    for e, s in zip(model.ends, model.score):
        k = (e - d0).days // STEP
        v[k] = max(v[k], int(round(-np.log10(1 - float(s)) * 100)))
    return {"s": d0.isoformat(), "v": [None if x < 0 else int(x) for x in v]}


def one_record(fit, check, series, events) -> dict:
    out = {}
    for W in LENGTHS:
        m = fit(series, W)
        out[str(W)] = dict(weekly(m), k=m.n_components, n=len(m.ends))
        ev = [e for e in events if e.scale == W]
        out[str(W)]["events"] = [dict(label=r["event"], kind=r["kind"], pct=round(r["percentile"], 2), peak=r["peak_end"], group=r["group"],
                                       start=next(e.start for e in ev if e.label == r["event"]).isoformat(), end=next(e.end for e in ev if e.label == r["event"]).isoformat())
                                  for r in check(m, ev)] if ev else []
    return out


def main():
    data = {"step": STEP, "lengths": list(LENGTHS), "atmosphere": {}, "rivers": {}}
    data["atmosphere"]["hk"] = one_record(rain_fit, rain_check, load_rainfall(), RAIN_EVENTS)
    print("Hong Kong done", flush=True)
    stations = dict(load_rhine_stations()); stations.update(load_alpine_stations())
    for name, ts in stations.items():
        evs = [e for e in RIVER_EVENTS if e.station == name]
        data["rivers"][name] = one_record(river_fit, river_check, ts, evs)
        print(name, "done", flush=True)
    OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
