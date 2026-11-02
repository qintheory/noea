"""
Rolling-window model for Hong Kong rainfall: a continuous reading of the record instead of one number per year.

The yearly model (anomaly.py) describes each calendar year by six numbers. This one slides a window of W days along the
daily record, one day at a time, and describes every window by ten local measures, in the spirit of heart-rate
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

The ranking, the PCA and the scoring are shared with the river module (../windows.py): each measure is ranked among
windows that end at the same time of year, a PCA keeps 80% of the variance, and a window is scored by its Mahalanobis
distance inside the kept components or by its reconstruction error (an unusual combination, as in the yearly model). Which of the
two the score uses depends on the window length, and was chosen on the "tune" half of the documented events only
(events.py): at 30 days the larger of the two ranks (tune 0.88, test 0.81); at 365 days the Mahalanobis rank alone
(tune 0.75, test 0.87), since reconstruction error is mostly noise over a whole year. Those are the mean percentiles
of the events, where 0.5 is chance. Other lengths use the larger of the two ranks, untested.

Nothing here is fitted to the documented events (events.py): they are used only to check the result afterwards.
"""
from __future__ import annotations

import numpy as np

from ..windows import Event, RollingModel, check_events as _check, fit_windows, longest

MEASURES = ["total", "wet", "heaviest", "spread", "change", "slow_fast", "dry_run", "wet_run", "top3", "settling"]
WEEK = 7
SCORING = {365: "mahalanobis"}        # window length -> score rule ("both" otherwise); chosen on the tune events


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
            weeks.std() / daily_sd if daily_sd > 0 else 0.0, longest(~wet) / W, longest(wet) / W,
            np.sort(w)[-3:].sum() / total if total > 0 else 0.0, _settling(w) / W]


def fit_rolling_model(series, window: int = 30, scoring: str | None = None) -> RollingModel:
    """Slide `window` days along the series, one day at a time. `scoring` is "both" or "mahalanobis"; by default it follows SCORING."""
    return fit_windows(series, window, MEASURES, _measures, scoring or SCORING.get(window, "both"))


def check_events(model: RollingModel, events: list[Event]) -> list[dict]:
    return _check(model, events)
