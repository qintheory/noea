"""
An emergent affect map for Hong Kong rainfall: valence and arousal from two PCA factors and the anomaly score.

There are no participants and no measured affect behind this, so it does not "learn emotion". It builds a hypothesis
about affect from the data, and checks the hypothesis for consistency. Three ingredients, all learned from the record:

  storminess how stormy a year was. Factor 1 of a varimax-rotated PCA on the six yearly features; it loads on the
             peak day, the rarity of the peak, how concentrated the rain was, and the spread (0.76 to 0.97).
  wetness    wet or dry compared with a normal year. Factor 2; it loads on wet-day frequency and on the year's total
             against the mean of the 30 years before (about 0.8).
  surprise   the anomaly score of anomaly.py: how badly the year fits the record's usual combinations of features.
             It is out of the PCA plane, so it adds what storminess and wetness cannot see.

  arousal = the mean of the year's percentile rank on storminess and on surprise.
  valence = 1 - 2 x the percentile rank of (the mean of the rank of its departure from a normal year, and of its surprise),
            where departure = sqrt(max(storminess, 0)^2 + wetness^2): intense, very wet or very dry all read as unpleasant,
            a quiet year does not.

Both are RELATIVE to this record (a rank among its fitted years, 0 to 1 for arousal, -1 to +1 for valence), and the
weights are equal, not tuned. The anomaly score is the guideline for judging the result, not an answer key: the map
should agree with it clearly without being a copy of it. CHECKS are fixed in advance and exported with the result.
Nothing here has been tested with viewers.
"""
from __future__ import annotations
from dataclasses import dataclass, field

import numpy as np
from scipy.stats import rankdata

from .anomaly import FEATURE_NAMES, MIN_DAYS_FOR_FIT, AnomalyModel, _feature_row
from .models import DiagnosticProfile

REFERENCE_EVENTS = {1926: "flood", 2023: "storm", 1963: "drought"}     # documented events used only to CHECK the map, never to fit it


def _varimax(L: np.ndarray, iterations: int = 200) -> np.ndarray:
    p, k = L.shape
    R, d = np.eye(k), 0.0
    for _ in range(iterations):
        Lr = L @ R
        u, s, vt = np.linalg.svd(L.T @ (Lr ** 3 - Lr @ np.diag((Lr ** 2).sum(0)) / p))
        R = u @ vt
        if s.sum() < d * (1 + 1e-9):
            break
        d = s.sum()
    return R


@dataclass
class AffectModel:
    valence: dict[int, float]
    arousal: dict[int, float]
    storminess_loadings: dict[str, float]
    wetness_loadings: dict[str, float]
    correlations: dict[str, float]
    checks: dict[str, bool]
    n_fit: int
    notes: list[str] = field(default_factory=list)


def fit_affect_model(profile: DiagnosticProfile, anomaly: AnomalyModel) -> AffectModel:
    years = [y for y in profile.years if y.n_days >= MIN_DAYS_FOR_FIT]            # the fitted years; the partial one is not scored here
    n = len(years)
    X = np.array([_feature_row(y) for y in years])
    Z = (X - X.mean(0)) / X.std(0)
    _, S, Vt = np.linalg.svd(Z, full_matrices=False)
    L = Vt[:2].T * S[:2] / np.sqrt(n)
    R = _varimax(L)
    F = (Z @ Vt[:2].T) / (S[:2] / np.sqrt(n)) @ R                                  # rotated factor scores, unit variance
    Lr = L @ R
    r_val, wet_i = FEATURE_NAMES.index("r_value"), FEATURE_NAMES.index("wet_day_frequency")
    k_int = int(np.argmax(np.abs(Lr[r_val]))); k_wet = 1 - k_int
    s_int, s_wet = np.sign(Lr[r_val, k_int]), np.sign(Lr[wet_i, k_wet])           # signs fixed by meaning: more intense is +, wetter is +
    storminess, wetness = F[:, k_int] * s_int, F[:, k_wet] * s_wet

    pct = lambda v: (rankdata(v) - 0.5) / n
    surprise = np.array([anomaly.normalized(y.year) for y in years])
    departure = np.sqrt(np.maximum(storminess, 0) ** 2 + wetness ** 2)
    arousal = (pct(storminess) + pct(surprise)) / 2
    valence = 1 - 2 * pct((pct(departure) + pct(surprise)) / 2)

    idx = {y.year: i for i, y in enumerate(years)}
    corr = lambda a, b: float(np.corrcoef(a, b)[0, 1])
    top = np.argsort(-surprise)[:10]
    ordinary = np.argsort(departure + surprise)[:5]
    checks = {
        "arousal agrees with the anomaly (r >= 0.4)": corr(arousal, surprise) >= 0.4,
        "valence agrees with the anomaly (r <= -0.4)": corr(valence, surprise) <= -0.4,
        "valence and arousal are two dimensions (|r| <= 0.7)": abs(corr(valence, arousal)) <= 0.7,
        "8 of the 10 most anomalous years are unpleasant and activated": int(np.sum((valence[top] < 0) & (arousal[top] > 0.5))) >= 8,
        "1926 flood: unpleasant, activated": valence[idx[1926]] < 0 and arousal[idx[1926]] > 0.5,
        "2023 storm: unpleasant, activated": valence[idx[2023]] < 0 and arousal[idx[2023]] > 0.5,
        "1963 drought: unpleasant, calm": valence[idx[1963]] < 0 and arousal[idx[1963]] < 0.5,
        "the 5 most ordinary years are pleasant": bool(np.all(valence[ordinary] > 0)),
    }
    checks = {k: bool(v) for k, v in checks.items()}
    load = lambda k, s: {f: round(float(Lr[i, k] * s), 2) for i, f in enumerate(FEATURE_NAMES)}
    return AffectModel(
        valence={y.year: float(v) for y, v in zip(years, valence)}, arousal={y.year: float(a) for y, a in zip(years, arousal)},
        storminess_loadings=load(k_int, s_int), wetness_loadings=load(k_wet, s_wet),
        correlations={"arousal~anomaly": corr(arousal, surprise), "valence~anomaly": corr(valence, surprise), "valence~arousal": corr(valence, arousal)},
        checks=checks, n_fit=n)
