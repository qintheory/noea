"""
The machinery of the rolling-window models, shared by the rainfall and the river modules.

A window of W days slides along a daily record one day at a time. Each window is described by a module's own measures
(rainfall/rolling.py, river/rolling.py), each measure is ranked among windows that end at the same time of year (plus or
minus 15 days) and turned into a bounded score (a probit, clipped at 3.5), so a winter month is compared with winters and
a measure that is nearly constant in a season cannot blow up. A PCA keeps the components that carry 80% of the variance.
A window is scored two ways: by its Mahalanobis distance inside the kept components (an extreme along the usual patterns)
and by its reconstruction error (an unusual combination of measures, as in the yearly models), and the score rule says
which of the two ranks to use.

Neighbouring windows share all but one day, so the windows are far from independent; the PCA describes the record, it is
not a significance test. Nothing is fitted to documented events: they are used only to check the result afterwards.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable

import numpy as np
from scipy.stats import norm, rankdata

SEASON_HALF_WIDTH = 15
VARIANCE_KEPT = 0.80


@dataclass(frozen=True)
class Event:
    label: str
    kind: str          # "wet" or "dry" (rainfall); "flood" or "drought" (rivers)
    start: date
    end: date
    scale: int         # days: the window length that suits the event
    group: str         # "tune" or "test": split in advance, so a setting chosen on one half is tested on the other
    station: str | None = None


@dataclass
class RollingModel:
    window: int
    measures: list[str]
    ends: list[date]                  # last day of each window
    raw: np.ndarray                   # windows x measures, as measured
    z: np.ndarray                     # windows x measures, ranked within the season (probit)
    mahalanobis: np.ndarray
    reconstruction: np.ndarray
    score: np.ndarray                 # 0..1 rank under the score rule
    n_components: int
    explained: float


def daily_array(series) -> tuple[np.ndarray, list[date]]:
    """The series on a continuous daily calendar; days with no record are NaN."""
    first, last = series.dates[0], series.dates[-1]
    x = np.full((last - first).days + 1, np.nan)
    for d, v in zip(series.dates, series.values):
        x[(d - first).days] = v
    return x, [first + timedelta(i) for i in range(len(x))]


def longest(flags) -> int:
    best = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        best = max(best, cur)
    return best


def seasonal_probit(ends: list[date], F: np.ndarray) -> np.ndarray:
    doy = np.array([d.timetuple().tm_yday for d in ends])
    Z = np.zeros_like(F)
    for k in range(1, 367):
        dist = np.minimum(np.abs(doy - k), 366 - np.abs(doy - k))
        near, here = np.where(dist <= SEASON_HALF_WIDTH)[0], np.where(doy == k)[0]
        if len(here) == 0 or len(near) < 30:
            continue
        at = np.searchsorted(near, here)
        for j in range(F.shape[1]):
            r = (rankdata(F[near, j]) - 0.5) / len(near)
            Z[here, j] = np.clip(norm.ppf(r[at]), -3.5, 3.5)
    return Z


def fit_windows(series, window: int, measures: list[str], measure_fn: Callable[[np.ndarray], list[float]], scoring: str) -> RollingModel:
    """Slide `window` days along the series; windows with a missing day (years with no record) are skipped.
    `scoring` is "both" (the larger of the two ranks) or "mahalanobis"."""
    x, dates = daily_array(series)
    ends, rows = [], []
    for e in range(window - 1, len(x)):
        w = x[e - window + 1:e + 1]
        if np.isnan(w).any():
            continue
        ends.append(dates[e])
        rows.append(measure_fn(w))
    F = np.array(rows)
    Z = seasonal_probit(ends, F)
    C = Z - Z.mean(0)
    _, S, Vt = np.linalg.svd(C, full_matrices=False)
    var = S ** 2 / len(C)
    k = int(np.searchsorted(np.cumsum(var) / var.sum(), VARIANCE_KEPT) + 1)
    scores = C @ Vt[:k].T
    maha = ((scores ** 2) / var[:k]).sum(1)
    recon = ((C - scores @ Vt[:k]) ** 2).sum(1)
    rank = lambda v: (rankdata(v) - 0.5) / len(v)
    score = rank(maha) if scoring == "mahalanobis" else np.maximum(rank(maha), rank(recon))
    return RollingModel(window, measures, ends, F, Z, maha, recon, score, k, float(var[:k].sum() / var.sum()))


def check_events(model: RollingModel, events: list[Event]) -> list[dict]:
    """For each documented event: how the model's highest score inside the event's span ranks against the highest scores
    of spans of the same length elsewhere in the record (1.0 = higher than every other span, 0.5 = chance)."""
    ends = np.array(model.ends, dtype="datetime64[D]")                # sorted, so a span is a slice
    out = []
    for ev in events:
        span = (ev.end - ev.start).days + 1
        lo, hi = np.searchsorted(ends, np.datetime64(ev.start)), np.searchsorted(ends, np.datetime64(ev.end), side="right")
        if hi <= lo:
            continue
        peak = model.score[lo:hi].max()
        a = np.arange(0, len(ends), 15)
        b = np.searchsorted(ends, ends[a] + np.timedelta64(span - 1, "D"), side="right")
        peers = np.array([model.score[i:j].max() for i, j in zip(a, b) if j - i > 0.8 * span])
        out.append(dict(event=ev.label, kind=ev.kind, scale=ev.scale, group=ev.group, station=ev.station, percentile=float((peers < peak).mean()),
                        peak_end=str(np.array(model.ends)[lo + int(np.argmax(model.score[lo:hi]))])))
    return out
