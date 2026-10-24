"""
Day-level unsupervised anomaly scoring for one river gauge: PCA reconstruction error.

The same idea as Climate Pulse (learn what is usual for this station, score how badly a
day fits), at a different grain. Climate Pulse scores years, which needs decades; an HWI
record is about a decade, so a day is the unit: ~4,000 rows instead of ~12.

Each day becomes a vector of seven scale-free features, computed from the hourly flow,
the daily rain at the associated rain station, and the station's own seasonal baseline:

  flow_anom        log10 of the day's mean flow minus the seasonal median (above or below normal)
  dlog_flow        change in log10 daily flow from the day before (rising or falling)
  peak_ratio       highest hourly flow / the day's mean (how spiky the day was)
  max_rise         largest hour-to-hour rise in log10 flow within the day (how sudden)
  rain_day         log10(1 + rain that day, mm)
  rain_3day        log10(1 + rain over the day and the two before)
  rain_antecedent  log10(1 + rain over the 7 days before the day)

Fitted on the training years only; any other day is scored by inference. As in Climate Pulse,
the score is a reconstruction error from a small number of components: a day scores high when
its combination of features does not fit the station's dominant patterns.
"""
from __future__ import annotations
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from noea.models import TimeSeries
from .baselines import SeasonalBaseline
from .models import IntradaySeries

FEATURE_NAMES = ["flow_anom", "dlog_flow", "peak_ratio", "max_rise", "rain_day", "rain_3day", "rain_antecedent"]
MIN_HOURS = 20          # a day with fewer hourly values than this is not scored


def day_features(flow: IntradaySeries, rain: TimeSeries, base: SeasonalBaseline) -> dict[date, list[float]]:
    hours: dict[date, list[float]] = defaultdict(list)
    for s, v in zip(flow.stamps, flow.values):
        hours[s.date()].append(v)
    rain_d = dict(zip(rain.dates, rain.values))
    daily_mean = {d: sum(v) / len(v) for d, v in hours.items() if len(v) >= MIN_HOURS}

    out: dict[date, list[float]] = {}
    for d, vals in hours.items():
        prev = d - timedelta(days=1)
        if d not in daily_mean or prev not in daily_mean or d not in rain_d:
            continue
        mean = daily_mean[d]
        if mean <= 0 or daily_mean[prev] <= 0:
            continue
        logs = [math.log10(max(v, 1e-6)) for v in vals]
        rises = [b - a for a, b in zip(logs, logs[1:])]
        r = lambda k: rain_d.get(d - timedelta(days=k), 0.0)
        out[d] = [
            base.anomaly(d, mean),
            math.log10(mean) - math.log10(daily_mean[prev]),
            max(vals) / mean,
            max(rises) if rises else 0.0,
            math.log10(1 + r(0)),
            math.log10(1 + r(0) + r(1) + r(2)),
            math.log10(1 + sum(r(k) for k in range(1, 8))),
        ]
    return out


@dataclass
class DayModel:
    scaler: StandardScaler
    pca: PCA
    baseline: SeasonalBaseline
    train_years: list[int]
    train_errors: np.ndarray
    explained_variance_ratio: list[float]
    scores: dict[date, float] = field(default_factory=dict)

    def percentile(self, error: float) -> float:
        """Where an error sits among the training days' errors, 0..1 (1 = worse than all of them)."""
        return float((self.train_errors < error).mean())


def fit_day_model(flow: IntradaySeries, rain: TimeSeries, train_years: list[int], n_components: int = 3) -> DayModel:
    daily = defaultdict(list)
    for s, v in zip(flow.stamps, flow.values):
        daily[s.date()].append(v)
    flow_daily = TimeSeries(flow.station_id, "flow", flow.unit,
                            sorted(d for d, v in daily.items() if len(v) >= MIN_HOURS),
                            [sum(daily[d]) / len(daily[d]) for d in sorted(d for d, v in daily.items() if len(v) >= MIN_HOURS)])
    base = SeasonalBaseline().fit(flow_daily, train_years)
    feats = day_features(flow, rain, base)

    train = [d for d in feats if d.year in train_years]
    X_raw = np.array([feats[d] for d in train])
    scaler = StandardScaler().fit(X_raw)
    X = scaler.transform(X_raw)
    pca = PCA(n_components=n_components).fit(X)
    err = np.sum((X - pca.inverse_transform(pca.transform(X))) ** 2, axis=1)

    model = DayModel(scaler, pca, base, list(train_years), err, [float(v) for v in pca.explained_variance_ratio_])
    for d, row in feats.items():
        x = scaler.transform([row])
        model.scores[d] = float(np.sum((x - pca.inverse_transform(pca.transform(x))) ** 2))
    return model
