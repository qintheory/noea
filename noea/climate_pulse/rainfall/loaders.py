"""
Climate Pulse loaders — real HKO data in, TimeSeries out.

Kept thin on purpose: the rest of the pipeline never needs to know whether
the data came from a CSV export or, later, a live HKO API pull.
"""
from __future__ import annotations
import csv
from datetime import date, timedelta
from pathlib import Path

from noea.models import TimeSeries

DEFAULT_DATA_PATH = Path(__file__).parent / "data" / "rainfall.csv"


def load_rainfall(path: str | Path = DEFAULT_DATA_PATH, station_id: str = "HKO", fill_dry_gaps: bool = True) -> TimeSeries:
    """Read a Date,Year,Rainfall_mm daily CSV (HKO export) into a TimeSeries.

    Year is dropped — it's derivable from Date and TimeSeries doesn't carry it.

    The export lists every day up to 1916, then leaves out about 67 days a year (270 to 310 rows a year, in runs of one
    to four days). The left-out days are dry days: annual totals (about 2,100 to 2,400 mm) and wet-day counts (about 140
    to 155 a year) are the same on both sides of 1917. Features that divide by the days present (wet-day frequency) or
    take a spread over them would read a fifth too wet from 1917 on, so with fill_dry_gaps the missing calendar days
    inside each year on record are added as 0 mm. Years wholly absent (1940 to 1946) stay absent.
    """
    dates: list[date] = []
    values: list[float] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            dates.append(date.fromisoformat(row["Date"]))
            values.append(float(row["Rainfall_mm"]))
    if fill_dry_gaps and dates:
        have = set(dates)
        first, last = min(dates), max(dates)
        for y in sorted({d.year for d in dates}):
            d, end = max(date(y, 1, 1), first), min(date(y, 12, 31), last)
            while d <= end:
                if d not in have:
                    dates.append(d)
                    values.append(0.0)
                d += timedelta(days=1)
        order = sorted(range(len(dates)), key=dates.__getitem__)
        dates, values = [dates[i] for i in order], [values[i] for i in order]
    return TimeSeries(
        station_id=station_id,
        variable="precipitation",
        unit="mm",
        dates=dates,
        values=values,
    )
