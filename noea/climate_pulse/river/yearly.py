"""
Per-year river diagnostics — the same four organs, one station-year at a time.

frameworks.py computes pulse / personality / memory / breath once over a
station's entire record. That is the right shape for a station's fingerprint
but the wrong shape for two things this module needs:

  1. A trend-aware baseline. A whole-record mean can't say a decade is
     running dry against its own recent past (Issue 6's post-2010 "gradual
     thinning"). A per-year record compared with a trailing 30-year mean can.
  2. Enough rows to fit a model. Eight whole-record profiles are eight rows;
     one station's years are 60-200.

This file reuses frameworks.py's pure functions on one-year slices instead of
reimplementing them, so the physics stays in exactly one place.
"""
from __future__ import annotations
from collections import defaultdict
import math

from .frameworks import memory, personality, pulse
from .models import TimeSeries, YearlyFlow

NORM_WINDOW_YEARS = 30         # WMO-style trailing climatological normal, same as rainfall
MIN_DAYS_FOR_BASELINE = 300    # a year this short is a partial record, not a year
MIN_DAYS_PER_MONTH = 15        # a month needs this much data to count toward seasonal amplitude


def _seasonal_amplitude(dates, values) -> float:
    """(max - min) of monthly means, over months with enough data, / annual mean.

    Months with too little data are skipped rather than counted as zero,
    which would fake a deep seasonal trough.
    """
    buckets: dict[int, list[float]] = defaultdict(list)
    for d, v in zip(dates, values):
        buckets[d.month].append(v)
    means = [sum(b) / len(b) for b in buckets.values() if len(b) >= MIN_DAYS_PER_MONTH]
    annual = sum(values) / len(values)
    if len(means) < 2 or annual <= 0:
        return 0.0
    return (max(means) - min(means)) / annual


def build_yearly(ts: TimeSeries) -> list[YearlyFlow]:
    """One YearlyFlow per year on record, oldest first."""
    ts = ts.clean()
    by_year: dict[int, tuple[list, list]] = defaultdict(lambda: ([], []))
    for d, v in zip(ts.dates, ts.values):
        by_year[d.year][0].append(d)
        by_year[d.year][1].append(v)

    years = sorted(by_year)
    annual_mean = {y: sum(by_year[y][1]) / len(by_year[y][1]) for y in years}
    complete = [y for y in years if len(by_year[y][1]) >= MIN_DAYS_FOR_BASELINE]

    out: list[YearlyFlow] = []
    for y in years:
        dates, values = by_year[y]
        slice_ts = TimeSeries(ts.station_id, ts.variable, ts.unit, dates, values)
        p, per, mem = pulse(slice_ts), personality(slice_ts), memory(slice_ts)

        # trailing baseline: complete years strictly before this one
        trailing = [annual_mean[c] for c in complete if c < y][-NORM_WINDOW_YEARS:]
        norm = sum(trailing) / len(trailing) if trailing else 0.0
        deviation = (annual_mean[y] - norm) / norm if norm > 0 else 0.0

        mean = p["mean_flow"]
        out.append(YearlyFlow(
            station_id=ts.station_id,
            year=y,
            n_days=len(values),
            mean_flow=mean,
            max_flow=p["max_flow"],
            min_flow=p["min_flow"],
            fdc_slope=per["fdc_slope"],
            recession_k=mem["recession_k"],
            seasonal_amplitude=_seasonal_amplitude(dates, values),
            peak_ratio=p["max_flow"] / mean if mean > 0 else 0.0,
            low_flow_ratio=p["min_flow"] / mean if mean > 0 else 0.0,
            deviation_from_norm=deviation,
        ))
    return out
