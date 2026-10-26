"""
OCEau (Geneva) monitoring-network export -> TimeSeries / IntradaySeries.

Source: "Veille Hydro-météorologique du Canton de Genève", run for the Office
cantonal de l'eau (OCEau). Each station page has a historical-export form (POST to
export_data.php). That form exports VALIDATED data only; newer, unvalidated values
are not available through it. Habits that follow from how the export behaves:

  * the timestamp is the END of the time step. A daily value labelled 2025-01-02T00:00
    is the mean over 2025-01-01. load_daily() shifts daily labels back one day so a
    date means "the day measured"; load_intraday() shifts back by the interval so a
    stamp means "start of the interval".
  * missing values are the text NAN, and the export returns a row for every step of
    the requested period, whether or not anything was measured there.
  * a long period can make the export fail; fetch_export() is meant to be called one
    year at a time.

The raw files are not committed (terms of use have not been confirmed); see fetch.py.
"""
from __future__ import annotations
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

from noea.models import TimeSeries
from .models import IntradaySeries

EXPORT_URL = "https://www.vhg.ch/xt_vh_718536/export_data.php"
USER_AGENT = "noea-pipeline (Meeting of Waters research; contact via github.com/qintheory/noea)"
DEFAULT_DATA_DIR = Path(__file__).parent / "data" / "oceau"

# parameter ("media") ids used by the export form
MEDIA = {"flow": 1016, "temperature": 1003, "rain": 1007}
INTERVALS = {"daily": 86400, "hourly": 3600, "15min": 900, "5min": 300}

# measurement_set_id (the number in station_view.php?measurement_set_id=...), read from the
# station lists on 24 Oct 2026. Aire gauges first; rain station is Pont-Rouge's associated one.
STATIONS = {
    "PR_": dict(id=130, name="Aire - Pont-Rouge", watercourse="Aire", media=["flow"], rain="BA_"),
    "CS_": dict(id=56, name="Aire - Centenaire", watercourse="Aire", media=["flow", "temperature"], rain="BA_"),
    "BS_": dict(id=37, name="Aire - Bossenailles", watercourse="Aire", media=["flow"], rain="DD_"),
    "AG_": dict(id=11, name="Aire, Confignon - Amont Galerie", watercourse="Aire", media=["flow"]),
    "LR_": dict(id=184, name="Laire - Racleret", watercourse="Laire (to confirm)", media=["flow", "temperature"]),
    "BA_": dict(id=26, name="Bachet-de-Pesay (rain)", watercourse=None, media=["rain"]),
    "DD_": dict(id=59, name="David-Dufour (rain)", watercourse=None, media=["rain"]),
    # the other rain stations of the network (OCEau and MeteoSwiss), all with complete validated daily records 2013-2025
    "AR_": dict(id=19, name="Aire (rain)", watercourse=None, media=["rain"]),
    "CE_": dict(id=43, name="Chevrier (rain)", watercourse=None, media=["rain"]),
    "CGI": dict(id=44, name="Changins, MeteoSwiss (rain)", watercourse=None, media=["rain"]),
    "CR_": dict(id=55, name="CERN (rain)", watercourse=None, media=["rain"]),
    "DOL": dict(id=167, name="Dole, MeteoSwiss (rain)", watercourse=None, media=["rain"]),
    "ER_": dict(id=63, name="Ermitage (rain)", watercourse=None, media=["rain"]),
    "ES_": dict(id=183, name="Essertines (rain)", watercourse=None, media=["rain"]),
    "FO_": dict(id=70, name="Maison de la Foret (rain)", watercourse=None, media=["rain"]),
    "GF_": dict(id=76, name="Grange-Falquet (rain)", watercourse=None, media=["rain"]),
    "GVE": dict(id=84, name="Geneve-Cointrin, MeteoSwiss (rain)", watercourse=None, media=["rain"]),
    "LA_": dict(id=90, name="Landecy (rain)", watercourse=None, media=["rain"]),
    "LC_": dict(id=91, name="Laconnex (rain)", watercourse=None, media=["rain"]),
    "SA_": dict(id=143, name="Sauverny (rain)", watercourse=None, media=["rain"]),
}
RAIN_STATIONS = [k for k, v in STATIONS.items() if v["media"] == ["rain"]]
# "rain" above is each gauge's associated rain station, as listed on its OCEau station page.
UNITS = {"flow": "m3/s", "temperature": "degC", "rain": "mm"}


def fetch_export(station: str, variable: str, start: date, end: date, interval: str = "daily",
                 timeout: int = 60) -> str:
    """POST the export form for one station/variable/period; return the CSV text."""
    form = urllib.parse.urlencode({
        "year_start": start.year, "month_start": start.month, "day_start": start.day,
        "year_end": end.year, "month_end": end.month, "day_end": end.day,
        "media": MEDIA[variable], "interval_duration": INTERVALS[interval],
        "export": "Exporter", "operation": "export_data_analyzed",
        "measurement_set_id": STATIONS[station]["id"],
    }).encode()
    req = urllib.request.Request(EXPORT_URL, data=form, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_export(text: str) -> tuple[str, list[tuple[datetime, float | None]]]:
    """Parse export CSV text -> (title, [(end_of_step_stamp, value or None)])."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = lines[0].strip('"') if lines else ""
    rows: list[tuple[datetime, float | None]] = []
    for l in lines:
        if not l[:2] in ("19", "20"):
            continue
        parts = l.split(";")
        stamp = datetime.fromisoformat(parts[0]).replace(tzinfo=None)   # local wall-clock time
        raw = parts[3].strip()
        rows.append((stamp, None if raw.upper() == "NAN" or raw == "" else float(raw)))
    return title, rows


def _read(station: str, variable: str, interval: str, data_dir: Path) -> list[tuple[datetime, float | None]]:
    rows: list[tuple[datetime, float | None]] = []
    for f in sorted(Path(data_dir).glob(f"{station}_{variable}_{interval}_*.csv")):
        rows.extend(parse_export(f.read_text(encoding="utf-8"))[1])
    # one row per step; files for adjacent years share a boundary stamp
    return sorted({s: v for s, v in rows}.items())


def load_daily(station: str, variable: str, data_dir: str | Path = DEFAULT_DATA_DIR) -> TimeSeries:
    """Daily validated series as a TimeSeries; missing days dropped, dates = the day measured."""
    pairs = _read(station, variable, "daily", Path(data_dir))
    dates = [(s - timedelta(days=1)).date() for s, v in pairs if v is not None]
    values = [v for s, v in pairs if v is not None]
    return TimeSeries(station_id=station, variable=variable, unit=UNITS[variable], dates=dates, values=values)


def load_intraday(station: str, variable: str, interval: str = "hourly",
                  data_dir: str | Path = DEFAULT_DATA_DIR) -> IntradaySeries:
    """Sub-daily validated series; stamps = start of each interval; missing steps dropped."""
    step = timedelta(seconds=INTERVALS[interval])
    pairs = _read(station, variable, interval, Path(data_dir))
    return IntradaySeries(station_id=station, variable=variable, unit=UNITS[variable],
                          interval_seconds=INTERVALS[interval],
                          stamps=[s - step for s, v in pairs if v is not None],
                          values=[v for s, v in pairs if v is not None])


def coverage(ts: TimeSeries) -> dict:
    """First and last valid day, count, and the gaps longer than a day."""
    if not ts.dates:
        return {"first": None, "last": None, "days": 0, "span_days": 0, "completeness": 0.0, "gaps": []}
    d = sorted(ts.dates)
    gaps = [(a, b, (b - a).days - 1) for a, b in zip(d, d[1:]) if (b - a).days > 1]
    span = (d[-1] - d[0]).days + 1
    return {"first": d[0], "last": d[-1], "days": len(d), "span_days": span,
            "completeness": len(d) / span, "gaps": gaps}
