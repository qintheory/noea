"""
Unsupervised anomaly scoring — Climate Pulse's actual model.

PCA-based reconstruction error: fit once on every year's feature vector,
then score each year by how poorly it reconstructs from a compressed
(lower-dimensional) representation of the whole record's shared structure.
A year that looks like most other years reconstructs well (low error); a
year that doesn't resemble the record's dominant patterns reconstructs
poorly (high error) — that error is the learned anomaly signal mapping.py
uses to drive valence and arousal.

This is Issue 4's own proposed methodology ("autoencoders... to train
deviation sensitivity models," PCA named alongside it), sized honestly for
the data: 135 years, 6 features is too little for a deep autoencoder to
learn from without just memorizing every point — a linear autoencoder
converges to PCA anyway, so this is the same idea without the overfitting
risk.

Deliberately not clustering (see project history: an earlier k-means pass
averaged years into archetype buckets, diluting exactly the outliers it
was meant to catch — 2023's shock signal vanished once folded into a
40+ member cluster). Reconstruction error never averages points together:
every year is scored individually against the model fit on everyone, so
an outlier stays visible no matter how few other years resemble it.
"""
from __future__ import annotations
from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from .models import DiagnosticProfile, YearlyPulse

FEATURE_NAMES = [
    "r_value", "stdev", "wet_day_frequency",
    "deviation_from_norm", "log_return_period_fitted", "peak_concentration",
]

# a year needs at least this many days of data to be trusted in the fit.
# Checked empirically rather than guessed: 55 of 135 years have 268-299
# days (scattered missing dates through the historical record, still a
# meaningful full-year sample) and only one, 2025, is truly degenerate at
# 26 days -- a huge, unambiguous gap from the next-lowest (268). 200 sits
# safely in that gap: it excludes only the genuinely broken year instead
# of also discarding ~40% of otherwise-real years, which a naive 300
# threshold did.
MIN_DAYS_FOR_FIT = 200


def _feature_row(yp: YearlyPulse) -> list[float]:
    concentration = yp.r_value / yp.annual_total if yp.annual_total > 0 else 0.0
    return [
        yp.r_value,
        yp.stdev,
        yp.wet_day_frequency,
        yp.deviation_from_norm,
        float(np.log10(yp.return_period_fitted)),
        concentration,
    ]


@dataclass
class AnomalyModel:
    """A fitted PCA reconstruction model plus every year's raw anomaly score."""
    scaler: StandardScaler
    pca: PCA
    scores: dict[int, float]      # year -> reconstruction error (raw, unbounded)
    score_min: float
    score_max: float
    explained_variance_ratio: list[float]

    def normalized(self, year: int) -> float:
        """0..1 anomaly score for a year already in the fitted record."""
        s = self.scores.get(year, self.score_min)
        span = self.score_max - self.score_min
        if span <= 0:
            return 0.0
        return max(0.0, min(1.0, (s - self.score_min) / span))

    def score_new(self, yp: YearlyPulse) -> float:
        """0..1 anomaly score for a year NOT in the fitted record (inference
        on new/incoming data) — the same model, applied to a fresh point.
        """
        x = self.scaler.transform([_feature_row(yp)])
        reduced = self.pca.transform(x)
        reconstructed = self.pca.inverse_transform(reduced)
        error = float(np.sum((x - reconstructed) ** 2))
        span = self.score_max - self.score_min
        if span <= 0:
            return 0.0
        return max(0.0, min(1.0, (error - self.score_min) / span))


def fit_anomaly_model(profile: DiagnosticProfile, n_components: int = 2) -> AnomalyModel:
    """Fit PCA on every complete year's feature vector; score every year
    (complete or not) by reconstruction error.

    n_components=2 keeps the model deliberately small relative to 135
    samples / 6 features — enough to capture the record's dominant shared
    structure, compressed enough that a genuinely unusual year can't be
    reconstructed from it, which is the whole mechanism.

    Incomplete years (n_days < MIN_DAYS_FOR_FIT) are excluded from fitting
    but still scored via score_new() below — a 31-day partial year has
    degenerate feature values (e.g. an artificially huge peak_concentration
    from dividing by a tiny annual_total) that would otherwise dominate the
    error distribution and compress every genuine year's score toward the
    bottom of the scale, which is exactly what happened before this fix:
    2025's raw error (7.19) dwarfed 1926's (2.37, the actual record flood).
    """
    complete_years = [yp for yp in profile.years if yp.n_days >= MIN_DAYS_FOR_FIT]
    incomplete_years = [yp for yp in profile.years if yp.n_days < MIN_DAYS_FOR_FIT]

    X_raw = np.array([_feature_row(yp) for yp in complete_years])

    scaler = StandardScaler().fit(X_raw)
    X = scaler.transform(X_raw)

    pca = PCA(n_components=n_components).fit(X)
    X_reconstructed = pca.inverse_transform(pca.transform(X))
    errors = np.sum((X - X_reconstructed) ** 2, axis=1)

    scores = {yp.year: float(e) for yp, e in zip(complete_years, errors)}
    model = AnomalyModel(
        scaler=scaler,
        pca=pca,
        scores=scores,
        score_min=float(errors.min()),
        score_max=float(errors.max()),
        explained_variance_ratio=[float(v) for v in pca.explained_variance_ratio_],
    )

    # score incomplete years too (via inference on the fitted model), so
    # every year still gets a reading -- they just didn't shape the model
    for yp in incomplete_years:
        x = scaler.transform([_feature_row(yp)])
        reconstructed = pca.inverse_transform(pca.transform(x))
        model.scores[yp.year] = float(np.sum((x - reconstructed) ** 2))

    return model
