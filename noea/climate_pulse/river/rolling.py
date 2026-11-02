"""
Rolling-window model for the Rhine and alpine rivers: a continuous reading of a station's discharge instead of one number
per year.

The yearly model (regime.py) reads each year against the station's typical year. This one slides a window of W days along
the daily discharge, one day at a time, and describes every window by ten local measures, the river counterparts of the
rainfall measures (../rainfall/rolling.py) and of heart-rate variability: the level and the variability of the flow inside
a window.

  level      log10 of the window's mean flow
  peak       log10 of the highest day
  low        log10 of the lowest day
  spread     standard deviation of log10 flow
  change     root mean square of the day-to-day change in log10 flow: how flashy the river was (Personality, Issue 6)
  slow/fast  variability of the weekly means over the variability of the days: bursts against long swells
  trend      log10 of the last week's mean over the first week's: rising or falling through the window
  recession  how fast the flow fell in the week after its highest day, per day in log10 (Memory, Issue 6); 0 if the peak is at the end
  top3       share of the window's volume carried on its three highest days
  settling   days from the highest day until the flow is back below the window's mean, as a share of the window

One model per station, on that station's own history: each measure is ranked among windows that end at the same time of
year, a PCA keeps 80% of the variance, and a window is scored by its Mahalanobis distance inside the kept components or by
its reconstruction error (../windows.py). The score rule was chosen on the "tune" half of the documented events
(events.py), pooled across stations: the Mahalanobis rank alone wins at 30 days (tune 0.98, test 0.87) and at 90 days
(tune 0.75, test 0.79, two events in each half), and at 365 days the three rules tie within 0.04 on a single tune event,
so the same rule is used for every length. Those are mean percentiles of the events, where 0.5 is chance. A score says
how unusual a window was for its station and season, not which way. Nothing is fitted to the events; they only check the
result afterwards.
"""
from __future__ import annotations

import numpy as np

from ..windows import Event, RollingModel, check_events as _check, fit_windows

MEASURES = ["level", "peak", "low", "spread", "change", "slow_fast", "trend", "recession", "top3", "settling"]
WEEK = 7
SCORING: dict[int, str] = {}          # window length -> score rule ("mahalanobis" otherwise); chosen on the tune events


def _measures(w: np.ndarray) -> list[float]:
    W = len(w)
    lq = np.log10(np.maximum(w, 1e-3))
    weeks = np.log10(np.maximum(w[:W // WEEK * WEEK].reshape(-1, WEEK).mean(1), 1e-3)) if W >= 2 * WEEK else lq
    sd = lq.std()
    k = int(np.argmax(w))
    after = min(k + WEEK, W - 1)
    below = np.where(w[k:] <= w.mean())[0]
    return [np.log10(max(w.mean(), 1e-3)), lq.max(), lq.min(), sd, np.sqrt(np.mean(np.diff(lq) ** 2)),
            weeks.std() / sd if sd > 0 else 0.0, np.log10(max(w[-WEEK:].mean(), 1e-3)) - np.log10(max(w[:WEEK].mean(), 1e-3)),
            (lq[k] - lq[after]) / (after - k) if after > k else 0.0, np.sort(w)[-3:].sum() / w.sum() if w.sum() > 0 else 0.0,
            (below[0] if len(below) else W - k) / W]


def fit_rolling_model(series, window: int = 30, scoring: str | None = None) -> RollingModel:
    """Slide `window` days along one station's daily discharge, one day at a time. `scoring` is "mahalanobis" or "both" (the larger of the two ranks); by default it follows SCORING."""
    return fit_windows(series.clean(), window, MEASURES, _measures, scoring or SCORING.get(window, "mahalanobis"))


def check_events(model: RollingModel, events: list[Event]) -> list[dict]:
    return _check(model, events)
