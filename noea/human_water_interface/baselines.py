"""
A station's own seasonal norm, fitted on the years it is allowed to see.

Climate Pulse compares a year with the trailing 30 years. HWI records are about a decade
long, so the norm is a seasonal one instead: for each calendar day, the median (and spread)
of log10 flow across the fitting years, pooling days within +/- `window` of it. It is fitted
on a stated set of years only, so the later years can serve as a genuine held-out test.
"""
from __future__ import annotations
import math
import statistics
from datetime import date

from noea.models import TimeSeries


def day_index(d: date) -> int:
    """Calendar-day index 1..366, the same for a given month and day in every year."""
    return date(2000, d.month, d.day).timetuple().tm_yday


class SeasonalBaseline:
    def __init__(self, window: int = 15):
        self.window = window
        self.median: dict[int, float] = {}
        self.spread: dict[int, float] = {}
        self.fit_years: list[int] = []

    def fit(self, ts: TimeSeries, years: range | list[int]) -> "SeasonalBaseline":
        self.fit_years = list(years)
        by_idx: dict[int, list[float]] = {i: [] for i in range(1, 367)}
        for d, v in zip(ts.dates, ts.values):
            if d.year in self.fit_years and v > 0:
                by_idx[day_index(d)].append(math.log10(v))
        for i in range(1, 367):
            pool = []
            for off in range(-self.window, self.window + 1):
                pool += by_idx[(i - 1 + off) % 366 + 1]
            self.median[i] = statistics.median(pool)
            self.spread[i] = max(statistics.pstdev(pool), 0.05)       # floor: a dull season is not infinitely sensitive
        return self

    def anomaly(self, d: date, value: float) -> float:
        """log10 distance from this calendar day's median: 0 = normal, +0.5 = about 3x normal."""
        return math.log10(max(value, 1e-6)) - self.median[day_index(d)]

    def z(self, d: date, value: float) -> float:
        """The same distance, in units of that season's spread."""
        return self.anomaly(d, value) / self.spread[day_index(d)]
