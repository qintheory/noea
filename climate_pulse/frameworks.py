"""
The Climate Pulse diagnostic framework — Hong Kong's rainfall ECG.

Rainfall's analogue to a hydrograph isn't a smooth curve, it's a beat: one
extreme event per year functions like an R-peak on an ECG. These functions
extract that annual rhythm from a daily precipitation TimeSeries — pure,
deterministic, no curatorial judgment. mapping.py is the only place these
facts become a felt quality.

Metric definitions follow Noéa Issue 3 (the ECG analogy) and Issue 4 (the
five-feature emotional-translation table):
    R                    -> max 24h rainfall in a year (the R-peak)
    RR                   -> days between consecutive R events
    S                    -> max dry-season (Nov-Apr) rainfall, an off-cycle anomaly
    return period        -> recurrence interval of a year's R value
    deviation_from_norm  -> this year's total rainfall vs. a trailing 30yr mean
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date
import statistics

from scipy.stats import gumbel_r

from noea.models import TimeSeries
from .models import YearlyPulse, DiagnosticProfile

DRY_SEASON_MONTHS = {11, 12, 1, 2, 3, 4}   # Nov-Apr, per Issue 3
WET_DAY_THRESHOLD_MM = 0.1                  # HKO's "rain day" convention
NORM_WINDOW_YEARS = 30                      # WMO-style rolling climatological normal


def annual_extremes(ts: TimeSeries) -> dict[int, tuple[float, date]]:
    """R per year: the year's single highest daily rainfall, and when it fell."""
    best: dict[int, tuple[float, date]] = {}
    for d, v in zip(ts.dates, ts.values):
        cur = best.get(d.year)
        if cur is None or v > cur[0]:
            best[d.year] = (v, d)
    return best


def r_intervals(extremes: dict[int, tuple[float, date]]) -> dict[int, float | None]:
    """RR per year: days since the previous year's R event. First year is None."""
    years = sorted(extremes)
    out: dict[int, float | None] = {years[0]: None} if years else {}
    for prev_y, y in zip(years, years[1:]):
        out[y] = float((extremes[y][1] - extremes[prev_y][1]).days)
    return out


def dry_season_anomaly(ts: TimeSeries) -> dict[int, float]:
    """S per year: the wettest dry-season day, kept within its own calendar year.

    Dry season (Nov-Apr) spans a year boundary; we attach S to whichever
    calendar year its Nov/Dec or Jan/Apr days fall in rather than stitching
    across the boundary, so every year's record stays self-contained.
    """
    best: dict[int, float] = defaultdict(float)
    for d, v in zip(ts.dates, ts.values):
        if d.month in DRY_SEASON_MONTHS:
            best[d.year] = max(best[d.year], v)
    return dict(best)


def annual_features(ts: TimeSeries) -> dict[int, dict]:
    """Per-year mean intensity, day-to-day variability, and wet-day frequency."""
    buckets: dict[int, list[float]] = defaultdict(list)
    for d, v in zip(ts.dates, ts.values):
        buckets[d.year].append(v)
    out = {}
    for y, vals in buckets.items():
        wet_days = sum(1 for v in vals if v >= WET_DAY_THRESHOLD_MM)
        out[y] = {
            "mean_intensity": sum(vals) / len(vals),
            "stdev": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
            "wet_day_frequency": wet_days / len(vals),
            "annual_total": sum(vals),
        }
    return out


def deviation_from_norm(features: dict[int, dict], window: int = NORM_WINDOW_YEARS) -> dict[int, float]:
    """This year's total rainfall vs. the trailing N-year mean (expanding early on).

    Ratio, not difference: 0.0 = exactly normal, -0.5 = half of normal,
    +0.5 = half again as much as normal.
    """
    years = sorted(features)
    totals = [features[y]["annual_total"] for y in years]
    out = {}
    for i, y in enumerate(years):
        trailing = totals[max(0, i - window):i]  # years strictly before y
        if not trailing:
            out[y] = 0.0
            continue
        norm = sum(trailing) / len(trailing)
        out[y] = (totals[i] - norm) / norm if norm > 0 else 0.0
    return out


def return_periods(extremes: dict[int, tuple[float, date]]) -> dict[int, float]:
    """Weibull plotting-position return period (years) for each year's R value.

    Empirical and simple, but structurally capped at ~N years (N = sample
    size) — the most extreme year on record can never score higher than
    that, no matter how extreme it actually was. See return_periods_fitted
    for the version that can exceed the sample.
    """
    n = len(extremes)
    ranked = sorted(extremes.items(), key=lambda kv: kv[1][0], reverse=True)
    return {y: (n + 1) / rank for rank, (y, _) in enumerate(ranked, start=1)}


def return_periods_fitted(extremes: dict[int, tuple[float, date]]) -> dict[int, float]:
    """Gumbel-fitted return period (years) for each year's R value.

    Fits a Gumbel (Extreme Value Type I) distribution to the full annual-
    maxima series — the standard method for this exact kind of data in
    hydrological frequency analysis — then reads each year's return period
    off the fitted survival function. Unlike the empirical version, this
    can extrapolate past the sample size, which is how official reporting
    arrives at figures like "1-in-500-years" from a ~135-year record.
    """
    r_vals = [r for r, _ in extremes.values()]
    loc, scale = gumbel_r.fit(r_vals)
    out = {}
    for y, (r, _) in extremes.items():
        exceedance_prob = gumbel_r.sf(r, loc=loc, scale=scale)  # P(R' >= r)
        out[y] = min(1.0 / exceedance_prob, 1e5) if exceedance_prob > 0 else 1e5
    return out


def build_profile(ts: TimeSeries) -> DiagnosticProfile:
    """Run all five diagnostics and assemble one YearlyPulse per year on record."""
    ts = ts.clean()
    extremes = annual_extremes(ts)
    rr = r_intervals(extremes)
    s = dry_season_anomaly(ts)
    feat = annual_features(ts)
    dev = deviation_from_norm(feat)
    rp = return_periods(extremes)
    rp_fit = return_periods_fitted(extremes)

    years = []
    for y in sorted(extremes):
        r_value, r_date = extremes[y]
        years.append(YearlyPulse(
            year=y,
            r_value=r_value,
            r_date=r_date,
            rr_days=rr.get(y),
            s_value=s.get(y, 0.0),
            mean_intensity=feat[y]["mean_intensity"],
            stdev=feat[y]["stdev"],
            wet_day_frequency=feat[y]["wet_day_frequency"],
            deviation_from_norm=dev[y],
            return_period=rp[y],
            return_period_fitted=rp_fit[y],
            annual_total=feat[y]["annual_total"],
        ))

    r_vals = [yp.r_value for yp in years]
    rr_vals = [yp.rr_days for yp in years if yp.rr_days is not None]
    stdev_vals = [yp.stdev for yp in years]

    return DiagnosticProfile(
        station_id=ts.station_id,
        years=years,
        r_min=min(r_vals) if r_vals else 0.0,
        r_max=max(r_vals) if r_vals else 0.0,
        rr_min=min(rr_vals) if rr_vals else 0.0,
        rr_max=max(rr_vals) if rr_vals else 0.0,
        stdev_min=min(stdev_vals) if stdev_vals else 0.0,
        stdev_max=max(stdev_vals) if stdev_vals else 0.0,
    )
