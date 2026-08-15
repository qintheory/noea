"""
Real river discharge data in, TimeSeries out.

Two formats, two loaders — the rest of the pipeline (frameworks.py,
mapping.py) doesn't change either way, it only ever sees a TimeSeries.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path

from .models import TimeSeries

MISSING_VALUE = -999.0

# GRDC station number -> name, the four Rhine mainstem stations per Issue 6
RHINE_STATIONS = {
    "6235530": "Lustenau",
    "6935051": "Basel",
    "6335060": "Koeln",
    "6435060": "Lobith",
}

# station_id (in the combined Swiss CSV) -> name, the four alpine headwaters per Issue 6
ALPINE_STATIONS = {
    "2200": "Weisse Lütschine-Zweilütschinen",
    "2087": "Reuss-Andermatt",
    "2019": "Aare-Brienzwiler",
    "2030": "Aare-Thun",
}

DEFAULT_RHINE_DIR = Path(__file__).parent / "data" / "rhine"
DEFAULT_ALPINE_PATH = Path(__file__).parent / "data" / "alpine_headwaters.csv"


def load_grdc_station(path: str | Path, station_id: str | None = None) -> TimeSeries:
    """Parse one GRDC '..._Q_Day.Cmd.txt' file into a TimeSeries.

    GRDC files are fixed-format: a '#'-commented metadata header, a
    '# DATA' marker, then 'YYYY-MM-DD;hh:mm; Value' rows — encoded
    ISO-8859-1 (not UTF-8), CRLF line endings. Missing values are
    -999.000 and are dropped rather than kept as gaps.
    """
    path = Path(path)
    dates: list[date] = []
    values: list[float] = []
    in_data = False
    with open(path, encoding="latin-1", newline="") as f:
        for line in f:
            line = line.strip()
            if line.startswith("# DATA"):
                in_data = True
                continue
            if not in_data or not line or line.startswith("YYYY-MM-DD"):
                continue
            parts = line.split(";")
            if len(parts) < 3:
                continue
            value = float(parts[2].strip())
            if value == MISSING_VALUE:
                continue
            dates.append(date.fromisoformat(parts[0].strip()))
            values.append(value)

    grdc_no = path.stem.split("_")[0]
    name = station_id or RHINE_STATIONS.get(grdc_no, grdc_no)
    return TimeSeries(station_id=name, variable="discharge", unit="m3/s",
                       dates=dates, values=values)


def load_rhine_stations(dir_path: str | Path = DEFAULT_RHINE_DIR) -> dict[str, TimeSeries]:
    """Load the four canonical Rhine mainstem stations from a GRDC export directory."""
    dir_path = Path(dir_path)
    out = {}
    for grdc_no, name in RHINE_STATIONS.items():
        matches = list(dir_path.glob(f"{grdc_no}_Q_Day.Cmd.txt"))
        if not matches:
            raise FileNotFoundError(f"No file for station {grdc_no} ({name}) in {dir_path}")
        out[name] = load_grdc_station(matches[0], station_id=name)
    return out


def load_alpine_stations(path: str | Path = DEFAULT_ALPINE_PATH) -> dict[str, TimeSeries]:
    """Load the four alpine headwater stations from the combined Swiss CSV.

    Format: station_id,station_name,date,value (long form, many stations
    per file) — already pre-filtered down to just the four we need.
    """
    import csv

    buckets: dict[str, tuple[list[date], list[float]]] = {
        sid: ([], []) for sid in ALPINE_STATIONS
    }
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            sid = row["station_id"]
            if sid not in buckets:
                continue
            dates, values = buckets[sid]
            dates.append(date.fromisoformat(row["date"]))
            values.append(float(row["value"]))

    out = {}
    for sid, name in ALPINE_STATIONS.items():
        dates, values = buckets[sid]
        out[name] = TimeSeries(station_id=name, variable="discharge", unit="m3/s",
                                dates=dates, values=values)
    return out
