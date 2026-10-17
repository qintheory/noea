"""
Unsupervised anomaly scoring for river stations — PCA reconstruction error.

One model per station, fit on that station's own years: a year scores high
when its combination of flow features doesn't reconstruct well from the
station's dominant patterns of variation. Same technique as the rainfall
module's anomaly.py, deliberately re-implemented here rather than imported,
because the two modules are independent implementations of one contract —
neither imports from the other.

Why per station, not pooled: a 6 m3/s glacial stream and a 2000 m3/s lowland
river have different regimes, and the project's rule is that everything is
judged against the station's OWN record. The features are all scale-free
(ratios, slopes, a recession constant) so scores are comparable in meaning
even though each model is fit separately.

Why PCA and not a deep autoencoder: 62-209 rows per station is far too few
for a neural network not to memorise every point; a linear autoencoder
converges to PCA anyway. Why not clustering: see rainfall/mapping.py — it
averaged outlier years into large groups and erased the events the system is
meant to register. Reconstruction error scores every year individually.
"""
from __future__ import annotations
from dataclasses import dataclass, field

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from .models import YearlyFlow

FEATURE_NAMES = [
    "deviation_from_norm", "log10_peak_ratio", "low_flow_ratio",
    "fdc_slope", "recession_k", "seasonal_amplitude",
]

# GRDC/FOEN daily files here are complete except one 61-day first year
# (Koeln 1816) -- checked empirically, not assumed. That year's stats are
# real but describe two winter months, so it is scored but not fit on.
MIN_DAYS_FOR_FIT = 300


def _feature_row(y: YearlyFlow) -> list[float]:
    return [
        y.deviation_from_norm,
        float(np.log10(max(y.peak_ratio, 1e-9))),
        y.low_flow_ratio,
        y.fdc_slope,
        y.recession_k,
        y.seasonal_amplitude,
    ]


@dataclass
class RiverAnomalyModel:
    """A fitted per-station PCA model plus every year's raw reconstruction error."""
    station_id: str
    scaler: StandardScaler
    pca: PCA
    scores: dict[int, float]
    score_min: float
    score_max: float
    explained_variance_ratio: list[float]
    n_fit: int
    excluded_years: list[int] = field(default_factory=list)

    def normalized(self, year: int) -> float:
        """0..1 anomaly for a year on record, relative to this station's fit."""
        s = self.scores.get(year, self.score_min)
        span = self.score_max - self.score_min
        if span <= 0:
            return 0.0
        return max(0.0, min(1.0, (s - self.score_min) / span))


def fit_anomaly_model(yearly: list[YearlyFlow], n_components: int = 2) -> RiverAnomalyModel:
    """Fit on one station's complete years; score every year by inference."""
    fit_years = [y for y in yearly if y.n_days >= MIN_DAYS_FOR_FIT]
    skipped = [y for y in yearly if y.n_days < MIN_DAYS_FOR_FIT]

    X_raw = np.array([_feature_row(y) for y in fit_years])
    scaler = StandardScaler().fit(X_raw)
    X = scaler.transform(X_raw)

    pca = PCA(n_components=n_components).fit(X)
    errors = np.sum((X - pca.inverse_transform(pca.transform(X))) ** 2, axis=1)

    scores = {y.year: float(e) for y, e in zip(fit_years, errors)}
    for y in skipped:  # scored by inference, never allowed to shape the fit
        x = scaler.transform([_feature_row(y)])
        scores[y.year] = float(np.sum((x - pca.inverse_transform(pca.transform(x))) ** 2))

    return RiverAnomalyModel(
        station_id=yearly[0].station_id,
        scaler=scaler,
        pca=pca,
        scores=scores,
        score_min=float(errors.min()),
        score_max=float(errors.max()),
        explained_variance_ratio=[float(v) for v in pca.explained_variance_ratio_],
        n_fit=len(fit_years),
        excluded_years=[y.year for y in skipped],
    )
