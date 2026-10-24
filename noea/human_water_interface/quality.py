"""
Quality control for the HWI series. Reports, and removes only what is unambiguous.

The OCEau export is validated, so gross errors should be rare; this stage exists to prove
that rather than assume it, and to keep a station from silently failing later (a sensor
stuck on one value, a negative flow, a spike with no rain behind it). Anything doubtful is
reported, not removed: removing real floods would delete exactly what the model is for.
"""
from __future__ import annotations
import statistics

from noea.models import TimeSeries
from .models import IntradaySeries


def _longest_run(values: list[float]) -> int:
    best = run = 1
    for a, b in zip(values, values[1:]):
        run = run + 1 if a == b else 1
        best = max(best, run)
    return best if values else 0


def check(series: TimeSeries | IntradaySeries, spike_factor: float = 20.0, window: int = 15) -> dict:
    """Counts of the things that usually go wrong. `spike_factor`: a value this many times
    the median of its neighbours (a window each side) is listed for a human to look at."""
    v = series.values
    spikes = []
    for i in range(window, len(v) - window):
        med = statistics.median(v[i - window:i + window + 1])
        if med > 0 and v[i] > spike_factor * med:
            spikes.append((i, v[i], med))
    return {
        "n": len(v),
        "negative": sum(1 for x in v if x < 0),
        "zero": sum(1 for x in v if x == 0),
        "longest_identical_run": _longest_run(v),
        "spikes_listed": len(spikes),
        "first_spikes": [(s[0], round(s[1], 3), round(s[2], 3)) for s in spikes[:3]],
        "min": min(v) if v else None,
        "max": max(v) if v else None,
    }


def drop_negative(series: TimeSeries) -> TimeSeries:
    """A negative discharge or rainfall is not physical: drop it. Nothing else is removed."""
    pairs = [(d, x) for d, x in zip(series.dates, series.values) if x >= 0]
    return TimeSeries(series.station_id, series.variable, series.unit, [p[0] for p in pairs], [p[1] for p in pairs])
