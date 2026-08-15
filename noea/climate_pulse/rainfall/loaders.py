"""
Climate Pulse loaders — real HKO data in, TimeSeries out.

Kept thin on purpose: the rest of the pipeline never needs to know whether
the data came from a CSV export or, later, a live HKO API pull.
"""
from __future__ import annotations
import csv
from datetime import date
from pathlib import Path

from noea.models import TimeSeries

DEFAULT_DATA_PATH = Path(__file__).parent / "data" / "rainfall.csv"


def load_rainfall(path: str | Path = DEFAULT_DATA_PATH, station_id: str = "HKO") -> TimeSeries:
    """Read a Date,Year,Rainfall_mm daily CSV (HKO export) into a TimeSeries.

    Year is dropped — it's derivable from Date and TimeSeries doesn't carry it.
    """
    dates: list[date] = []
    values: list[float] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            dates.append(date.fromisoformat(row["Date"]))
            values.append(float(row["Rainfall_mm"]))
    return TimeSeries(
        station_id=station_id,
        variable="precipitation",
        unit="mm",
        dates=dates,
        values=values,
    )
