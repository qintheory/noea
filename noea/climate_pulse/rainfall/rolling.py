"""
Rolling-window model for Hong Kong rainfall: a continuous reading of the record instead of one number per year.

The yearly model (anomaly.py) describes each calendar year by six numbers. This one slides a window of W days along the
daily record, one day at a time, and describes every window by eight local measures, in the spirit of heart-rate
variability: the level and the variability of the signal inside a window, not a label for a year.

  total      log of the window's rain (mm)
  wet        share of days with at least 0.1 mm
  heaviest   log of the heaviest day
  spread     standard deviation of the daily values (log scale)
  change     root mean square of the day-to-day change (log scale), the rainfall counterpart of RMSSD
  slow/fast  variability of the weekly totals over the variability of the days: whether the rain comes in bursts or in
             long wet and dry stretches
  dry, wet   the longest dry and wet runs, as a share of the window
  top3       share of the window's rain that fell on its three wettest days
  settling   days from the heaviest day until three days in a row below 1 mm, as a share of the window: how fast the
             record settles back after its peak (cut short where the window ends)

Each measure is ranked among windows that end at the same time of year (plus or minus 15 days) and turned into a bounded
score (a probit, clipped at 3.5), so a winter month is compared with winters and a summer month with summers, and a
measure that is nearly constant in a season cannot blow up. A PCA keeps the components that carry 80% of the variance.
A window is scored two ways: by its Mahalanobis distance inside the kept components (an extreme along the usual
patterns) and by its reconstruction error (an unusual combination of measures, as in the yearly model). Which of the
two the score uses depends on the window length, and was chosen on the "tune" half of the documented events only
(events.py): at 30 days the larger of the two ranks (tune 0.88, test 0.81); at 365 days the Mahalanobis rank alone
(tune 0.75, test 0.87), since reconstruction error is mostly noise over a whole year. Those are the mean percentiles
of the events, where 0.5 is chance. Other lengths use the larger of the two ranks, untested.

Neighbouring windows share all but one day, so the 49,000 windows are far from independent; the PCA is a description of
the record, not a significance test. Nothing here is fitted to the documented events (events.py): they are used only
to check the result afterwards.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
from scipy.stats import norm, rankdata

from .events import Event

MEASURES = ["total", "wet", "heaviest", "spread", "change", "slow_fast", "dry_run", "wet_run", "top3", "settling"]
SEASON_HALF_WIDTH = 15
VARIANCE_KEPT = 0.80
WEEK = 7
SCORING = {365: "mahalanobis"}        # window length -> score rule ("both" otherwise); chosen on the tune events


@dataclass
class RollingModel:
    window: int
    ends: list[date]                  # last day of each window
    raw: np.ndarray                   # windows x measures, as measured
    z: np.ndarray                     # windows x measures, ranked within the season (probit)
    mahalanobis: np.ndarray
    reconstruction: np.ndarray
    score: np.ndarray                 # 0..1 rank of the larger of the two ranks
    n_components: int
    explained: float


def _daily_array(series) -> tuple[np.ndarray, list[date]]:
    first, last = series.dates[0], series.dates[-1]
    n = (last - first).days + 1
    x = np.full(n, np.nan)
    for d, v in zip(series.dates, series.values):
        x[(d - first).days] = v
    return x, [first + timedelta(i) for i in range(n)]


def _longest(flags) -> int:
    best = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        best = max(best, cur)
    return best


def _settling(w: np.ndarray) -> int:
    k = int(np.argmax(w))
    run = 0
    for j in range(k + 1, len(w)):
        run = run + 1 if w[j] < 1.0 else 0
        if run == 3:
            return j - 2 - k
    return len(w) - 1 - k


def _measures(w: np.ndarray) -> list[float]:
    W = len(w)
    wet = w >= 0.1
    lg = np.log1p(w)
    weeks = np.log1p(w[:W // WEEK * WEEK].reshape(-1, WEEK).sum(1)) if W >= 2 * WEEK else lg
    daily_sd = lg.std()
    total = w.sum()
    return [np.log1p(total), wet.mean(), lg.max(), daily_sd, np.sqrt(np.mean(np.diff(lg) ** 2)),
            weeks.std() / daily_sd if daily_sd > 0 else 0.0, _longest(~wet) / W, _longest(wet) / W,
            np.sort(w)[-3:].sum() / total if total > 0 else 0.0, _settling(w) / W]


def _seasonal_probit(ends: list[date], F: np.ndarray) -> np.ndarray:
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


def fit_rolling_model(series, window: int = 30, scoring: str | None = None) -> RollingModel:
    """Slide `window` days along the series, one day at a time; windows with a missing day (the years with no record) are skipped.
    `scoring` is "both" (the larger of the two ranks) or "mahalanobis"; by default it follows SCORING."""
    x, dates = _daily_array(series)
    ends, rows = [], []
    for e in range(window - 1, len(x)):
        w = x[e - window + 1:e + 1]
        if np.isnan(w).any():
            continue
        ends.append(dates[e])
        rows.append(_measures(w))
    F = np.array(rows)
    Z = _seasonal_probit(ends, F)
    C = Z - Z.mean(0)
    _, S, Vt = np.linalg.svd(C, full_matrices=False)
    var = S ** 2 / len(C)
    k = int(np.searchsorted(np.cumsum(var) / var.sum(), VARIANCE_KEPT) + 1)
    scores = C @ Vt[:k].T
    maha = ((scores ** 2) / var[:k]).sum(1)
    recon = ((C - scores @ Vt[:k]) ** 2).sum(1)
    rank = lambda v: (rankdata(v) - 0.5) / len(v)
    rule = scoring or SCORING.get(window, "both")
    score = rank(maha) if rule == "mahalanobis" else np.maximum(rank(maha), rank(recon))
    return RollingModel(window, ends, F, Z, maha, recon, score, k, float(var[:k].sum() / var.sum()))


def check_events(model: RollingModel, events: list[Event]) -> list[dict]:
    """For each documented event: how the model's highest score inside the event's span ranks against the highest scores
    of spans of the same length elsewhere in the record (1.0 = higher than every other span, 0.5 = chance)."""
    ends = np.array(model.ends, dtype="datetime64[D]")
    peers_start = np.arange(0, len(ends), 15)
    out = []
    for ev in events:
        span = (ev.end - ev.start).days + 1
        inside = (ends >= np.datetime64(ev.start)) & (ends <= np.datetime64(ev.end))
        if not inside.any():
            continue
        peak = model.score[inside].max()
        peers = []
        for s in peers_start:
            lo = ends[s]
            sel = (ends >= lo) & (ends <= lo + np.timedelta64(span - 1, "D"))
            if sel.sum() > 0.8 * span:
                peers.append(model.score[sel].max())
        out.append(dict(event=ev.label, kind=ev.kind, scale=ev.scale, percentile=float((np.array(peers) < peak).mean()),
                        peak_end=str(np.array(model.ends)[inside][int(np.argmax(model.score[inside]))])))
    return out
