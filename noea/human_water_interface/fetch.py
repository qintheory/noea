"""
Download validated OCEau history into noea/human_water_interface/data/oceau/ (not committed).

    python3 -m noea.human_water_interface.fetch                # daily, all Aire gauges + rain, 2013-2025
    python3 -m noea.human_water_interface.fetch PR_ flow hourly 2014 2025

One request per station, variable and year, a second apart, so the source is not hammered.
"""
from __future__ import annotations
import sys
import time
from datetime import date

from .loaders import DEFAULT_DATA_DIR, STATIONS, fetch_export


def fetch(station: str, variable: str, interval: str, y0: int, y1: int, pause: float = 1.0) -> None:
    DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for y in range(y0, y1 + 1):
        out = DEFAULT_DATA_DIR / f"{station}_{variable}_{interval}_{y}.csv"
        if out.exists():
            continue
        out.write_text(fetch_export(station, variable, date(y, 1, 1), date(y, 12, 31), interval), encoding="utf-8")
        print(f"  {out.name}")
        time.sleep(pause)


def main(argv: list[str]) -> None:
    if argv:
        st, var, interval, y0, y1 = argv
        fetch(st, var, interval, int(y0), int(y1))
        return
    for st, meta in STATIONS.items():
        for var in meta["media"]:
            print(st, var)
            fetch(st, var, "daily", 2013, 2025)


if __name__ == "__main__":
    main(sys.argv[1:])
