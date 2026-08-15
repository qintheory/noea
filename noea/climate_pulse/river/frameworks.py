"""
The four diagnostic frameworks — Noéa's scientific layer.

    pulse       -> the hydrograph        (how much, how variable)
    personality -> the flow duration curve (temperament: flashy vs steady)
    memory      -> the recession curve    (how long it holds water)
    breath      -> the seasonal cycle     (the year's rhythm)

Pure functions, no side effects. Given a TimeSeries, each returns numbers.
Together they build a DiagnosticProfile — the station's fingerprint.

Only depends on the standard library + a little math, so it runs anywhere.
For heavier work you can swap in numpy later; kept dependency-free on purpose.
"""

from __future__ import annotations
import math
from collections import defaultdict

from .models import TimeSeries, DiagnosticProfile


def _percentile(sorted_vals: list[float], p: float) -> float:
    """p in [0,100]. Linear interpolation. Assumes sorted ascending."""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return sorted_vals[int(k)]
    return sorted_vals[lo] * (hi - k) + sorted_vals[hi] * (k - lo)


def pulse(ts: TimeSeries) -> dict:
    """The hydrograph reduced to its essentials: mean, max, min."""
    vals = ts.values
    if not vals:
        return {"mean_flow": 0.0, "max_flow": 0.0, "min_flow": 0.0}
    return {
        "mean_flow": sum(vals) / len(vals),
        "max_flow": max(vals),
        "min_flow": min(vals),
    }


def personality(ts: TimeSeries) -> dict:
    """Flow Duration Curve — exceedance probabilities.

    Q90 = the flow exceeded 90% of the time (a low-flow / drought floor).
    Q10 = the flow exceeded only 10% of the time (a high-flow marker).
    fdc_slope between Q10 and Q90, log scale = the classic 'flashiness' index.
    A steep slope means a reactive, spiky river; flat means groundwater-buffered.
    """
    vals = sorted(ts.values)
    if len(vals) < 2:
        return {"q10": 0.0, "q50": 0.0, "q90": 0.0, "fdc_slope": 0.0}

    # exceedance: Q90 is the LOW value (exceeded most of the time),
    # so exceedance probability p maps to percentile (100 - p).
    q10 = _percentile(vals, 90)   # exceeded 10% of time = high flow
    q50 = _percentile(vals, 50)
    q90 = _percentile(vals, 10)   # exceeded 90% of time = low flow

    # slope of the FDC on a log scale (guard against zero/neg)
    if q10 > 0 and q90 > 0:
        fdc_slope = (math.log10(q10) - math.log10(q90)) / (90 - 10)
        fdc_slope *= 100  # scale to a friendlier range
    else:
        fdc_slope = 0.0

    return {"q10": q10, "q50": q50, "q90": q90, "fdc_slope": fdc_slope}


def memory(ts: TimeSeries) -> dict:
    """Recession — how the river drains after a peak.

    We estimate a recession constant k from the average day-over-day decay
    during falling limbs (where today < yesterday). k closer to 1 means the
    basin releases water slowly (deep memory, groundwater-fed); lower k means
    it empties fast (flashy, little storage).
    """
    vals = ts.values
    ratios = []
    for i in range(1, len(vals)):
        prev, cur = vals[i - 1], vals[i]
        if prev > 0 and 0 < cur < prev:        # falling limb only
            ratios.append(cur / prev)
    k = sum(ratios) / len(ratios) if ratios else 0.0
    return {"recession_k": k}


def breath(ts: TimeSeries) -> dict:
    """Seasonal cycle — mean discharge per calendar month (Jan..Dec)."""
    buckets: dict[int, list[float]] = defaultdict(list)
    for d, v in zip(ts.dates, ts.values):
        buckets[d.month].append(v)
    monthly = []
    for m in range(1, 13):
        b = buckets.get(m, [])
        monthly.append(sum(b) / len(b) if b else 0.0)
    return {"monthly_means": monthly}


def build_profile(ts: TimeSeries) -> DiagnosticProfile:
    """Run all four frameworks and assemble the station's fingerprint."""
    ts = ts.clean()
    p = pulse(ts)
    per = personality(ts)
    mem = memory(ts)
    br = breath(ts)
    return DiagnosticProfile(
        station_id=ts.station_id,
        mean_flow=p["mean_flow"],
        max_flow=p["max_flow"],
        min_flow=p["min_flow"],
        q10=per["q10"],
        q50=per["q50"],
        q90=per["q90"],
        fdc_slope=per["fdc_slope"],
        recession_k=mem["recession_k"],
        monthly_means=br["monthly_means"],
    )
