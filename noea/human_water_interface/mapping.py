"""
The curatorial layer for L'Aire: from a gauge's day to XRParameters.

Everything here is a judgement about how the river should feel, kept apart from the measurements
(quality.py, baselines.py) and from the learned score (anomaly.py). The weights below are not fitted to
data and were not tuned to hit any event; they were checked afterwards against the whole distribution of
days (demo_human_water_interface_replay.py), the check that caught the river module's early flaw.

Two signals feed valence and arousal, deliberately, because the model alone is not enough: it flags days
whose combination of features is unusual (rain with no flow response, a very flashy day), and it is much
less sensitive to a high flow that is simply high. The seasonal tails cover that.

  extremity   how far the day's flow is from its season's norm, in the tails only:
              zero within one seasonal spread of normal, 1 at three spreads (flood OR drought)
  shock       the learned score: zero up to the 90th percentile of the training days' errors,
              rising to 1 at the worst training day (and held at 1 beyond it)

  diameter        flow on a log scale, between the training days' 1st and 99.9th percentile
  pulse_rhythm    where the calendar day sits in the station's seasonal cycle, 0.4 (low) to 1.6 (high)
  texture         flashiness: how spiky and how sudden the day's hourly flow was, against training days
  luminosity      0.5: no temperature series, as in Climate Pulse
  arousal         0.35 diameter + 0.25 suddenness + 0.40 shock
  valence         0.4 - 1.4 extremity - 1.0 shock, floored at -1: an ordinary day reads gently positive,
                  and an exceptional day of either kind reads negative
"""
from __future__ import annotations
from datetime import date

import numpy as np

from noea.models import XRParameters
from .anomaly import DayModel
from .baselines import day_index

EXTREMITY_START, EXTREMITY_FULL = 1.0, 3.0      # seasonal spreads from normal
SHOCK_START = 0.90                               # training-error percentile where the learned score starts to count
VALENCE_CALM = 0.4
EXTREMITY_WEIGHT, SHOCK_VALENCE_WEIGHT = 1.4, 1.0
AROUSAL_LEVEL, AROUSAL_SUDDEN, AROUSAL_SHOCK = 0.35, 0.25, 0.40


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _pct(train: np.ndarray, x: float) -> float:
    return float((train < x).mean())


def map_day(model: DayModel, d: date, station_id: str) -> XRParameters | None:
    feats = model.features.get(d)
    if feats is None:
        return None
    flow_anom, _, peak_ratio, max_rise = feats[0], feats[1], feats[2], feats[3]
    base = model.baseline
    idx = day_index(d)
    log_flow = flow_anom + base.median[idx]

    lo, hi = np.percentile(model.train_logflow, [1, 99.9])
    diameter = _clip01((log_flow - lo) / (hi - lo))

    z = flow_anom / base.spread[idx]
    extremity = _clip01((abs(z) - EXTREMITY_START) / (EXTREMITY_FULL - EXTREMITY_START))
    shock = _clip01((model.percentile(model.scores[d]) - SHOCK_START) / (1 - SHOCK_START))

    med = np.array([base.median[i] for i in range(1, 367)])
    season = (base.median[idx] - med.min()) / (med.max() - med.min())

    suddenness = _pct(model.train_features[:, 3], max_rise)
    spikiness = _pct(model.train_features[:, 2], peak_ratio)

    return XRParameters(
        station_id=station_id, timestamp=d,
        diameter=round(diameter, 4),
        luminosity=0.5,
        texture=round((suddenness + spikiness) / 2, 4),
        pulse_rhythm=round(0.4 + 1.2 * season, 4),
        valence=round(max(-1.0, VALENCE_CALM - EXTREMITY_WEIGHT * extremity - SHOCK_VALENCE_WEIGHT * shock), 4),
        arousal=round(AROUSAL_LEVEL * diameter + AROUSAL_SUDDEN * suddenness + AROUSAL_SHOCK * shock, 4),
    )


def map_series(model: DayModel, station_id: str) -> list[XRParameters]:
    """One XRParameters per scored day, in date order."""
    frames = (map_day(model, d, station_id) for d in sorted(model.features))
    return [f for f in frames if f is not None]
