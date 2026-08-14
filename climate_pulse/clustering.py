"""
Unsupervised year clustering — the objective grouping step behind Climate
Pulse's mood archetypes.

This groups years by similarity across their full R/RR/S/deviation/
variability signature (Issue 4's five-feature table, plus R itself). It
assigns no meaning — a cluster is just "these years behave alike." Naming
a cluster's mood and giving it a valence/arousal is a separate, human step:
propose_moods() below gives a data-driven starting guess, but you supervise
it by checking cluster_members() against years you know (droughts, storms)
and overriding where it disagrees with history.

This is why a hand-tuned single-axis formula (mapping.py's old valence,
driven only by annual deviation) missed 2023: a storm year can look
ordinary on annual totals while being extreme on R, return period, and
day-to-day variability. Clustering on all six features together catches
that a single axis can't.

Uses the fitted (not empirical) return period, log-transformed: fitted
return periods for genuine outliers can run into the thousands of years
while ordinary years sit near 1, and that skew would otherwise let a
single extreme year dominate the distance metric on its own.
"""
from __future__ import annotations
from dataclasses import dataclass, field

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from .models import DiagnosticProfile, YearlyPulse

FEATURE_NAMES = [
    "r_value", "stdev", "wet_day_frequency",
    "deviation_from_norm", "log_return_period", "peak_concentration",
]


def _peak_concentration(yp: YearlyPulse) -> float:
    """What fraction of the year's total rain fell in a single day.

    Distinct from deviation_from_norm on purpose: a year can have an
    unremarkable total (2023's dev=+0.14) while still being dominated by
    one extreme day — mean_intensity and deviation both just measure "how
    much total rain," so neither can see that. This can.
    """
    return yp.r_value / yp.annual_total if yp.annual_total > 0 else 0.0


def _feature_matrix(years: list[YearlyPulse]) -> np.ndarray:
    rows = []
    for yp in years:
        rows.append([
            yp.r_value, yp.stdev, yp.wet_day_frequency,
            yp.deviation_from_norm, np.log1p(yp.return_period_fitted),
            _peak_concentration(yp),
        ])
    return np.array(rows)


@dataclass
class ClusterModel:
    k: int
    labels: dict[int, int]                        # year -> cluster id
    centroids_raw: dict[int, dict[str, float]]     # cluster id -> {feature: mean}, real units
    silhouette: float


def suggest_k(profile: DiagnosticProfile, k_range=range(2, 9)) -> dict[int, float]:
    """Silhouette score per candidate k — inspect before committing to one."""
    X = StandardScaler().fit_transform(_feature_matrix(profile.years))
    scores = {}
    for k in k_range:
        labels = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(X)
        scores[k] = silhouette_score(X, labels)
    return scores


def fit_clusters(profile: DiagnosticProfile, k: int) -> ClusterModel:
    """Group years by their R/RR/S/deviation/variability signature."""
    years = profile.years
    X_raw = _feature_matrix(years)
    X = StandardScaler().fit_transform(X_raw)

    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(X)
    labels = {yp.year: int(c) for yp, c in zip(years, km.labels_)}

    centroids_raw: dict[int, dict[str, float]] = {}
    for c in range(k):
        rows = X_raw[km.labels_ == c]
        centroids_raw[c] = {f: float(v) for f, v in zip(FEATURE_NAMES, rows.mean(axis=0))}

    sil = silhouette_score(X, km.labels_) if k > 1 else 0.0
    return ClusterModel(k=k, labels=labels, centroids_raw=centroids_raw, silhouette=sil)


def cluster_members(model: ClusterModel) -> dict[int, list[int]]:
    """Which years fall in each cluster — what you actually review to name them."""
    out: dict[int, list[int]] = {c: [] for c in range(model.k)}
    for year, c in sorted(model.labels.items()):
        out[c].append(year)
    return out


def propose_moods(
    model: ClusterModel, profile: DiagnosticProfile
) -> dict[int, tuple[float, float]]:
    """A data-driven starting guess at (valence, arousal) per cluster.

    Not a final answer — a proposal to check against cluster_members()
    and override once you recognise which years landed where. Arousal
    tracks how extreme the cluster's centroid is on magnitude, day-to-day
    variability, and rarity. Valence starts from the same "normal is calm"
    tent as before, but now also gets pulled down by extremity — so a
    cluster of storm-shock years reads negative even if its average annual
    total looks unremarkable, which the old single-axis formula couldn't do.
    """
    r_vals = [yp.r_value for yp in profile.years]
    stdev_vals = [yp.stdev for yp in profile.years]
    log_rp_vals = [np.log1p(yp.return_period_fitted) for yp in profile.years]
    pc_vals = [_peak_concentration(yp) for yp in profile.years]
    r_lo, r_hi = min(r_vals), max(r_vals)
    sd_lo, sd_hi = min(stdev_vals), max(stdev_vals)
    rp_lo, rp_hi = min(log_rp_vals), max(log_rp_vals)
    pc_lo, pc_hi = min(pc_vals), max(pc_vals)

    def norm(v, lo, hi):
        return 0.5 if hi <= lo else max(0.0, min(1.0, (v - lo) / (hi - lo)))

    moods = {}
    for c, centroid in model.centroids_raw.items():
        magnitude = norm(centroid["r_value"], r_lo, r_hi)
        variability = norm(centroid["stdev"], sd_lo, sd_hi)
        rarity = norm(centroid["log_return_period"], rp_lo, rp_hi)
        concentration = norm(centroid["peak_concentration"], pc_lo, pc_hi)
        extremity = (magnitude + variability + rarity + concentration) / 4.0

        dev_ratio = min(1.0, abs(centroid["deviation_from_norm"]) / 1.0)
        valence = 0.6 - 1.6 * dev_ratio - 0.8 * extremity
        valence = max(-1.0, min(0.6, valence))
        arousal = round(extremity, 4)
        moods[c] = (round(valence, 4), arousal)
    return moods
