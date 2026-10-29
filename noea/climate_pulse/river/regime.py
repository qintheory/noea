"""
A river year, read the way a river is read: its rhythm, its extremes and its memory, against the station's own typical year.

The earlier river model (anomaly.py) summarised a year by six ratios, several of them divided by the year's own mean flow,
and scored it by PCA reconstruction error. That measures one thing only: how badly the year's combination of ratios fails
to reconstruct from the two main directions. A year that is extreme ALONG those directions, a very dry or very wet year
with every ratio shifting together, reconstructs well and scores as ordinary. Köln 1976 (mean flow 0.62 of average) scored
as one of the more typical years of its record.

This model starts from the river. For each station it learns the TYPICAL YEAR: the median flow of each month and the median
annual highest and lowest day. Each year is then described by how far it departed from that typical year, never from the
year's own mean, so a dry year with an ordinary peak is not mistaken for a flood:

    flow dimension
      12 monthly anomalies   log10(the month's mean flow / the typical flow for that month)
      flood                  log10(the year's highest day / the typical highest day)
      low                    log10(the year's lowest 7-day mean flow / the typical one)
      flow-duration slope    how flashy the year was (Personality, Issue 6)
      recession constant     how slowly the river fell back after a peak (Memory, Issue 6)

The 16 numbers are standardised and a probabilistic PCA (sklearn PCA.score_samples) learns what the station's years usually
look like: a few main patterns plus a little noise. Its negative log-likelihood counts both kinds of departure, far along the
main patterns (a drought) and off them (a flood in an ordinary year).

Six plain DESCRIPTORS say what kind of departure a year was, each in standard deviations of the station's own years and
signed: wetness, flood, low (the three of Pulse), personality (flashiness), memory (recession) and season (Breath: winter
water against summer water). A year is UNUSUAL if its overall pattern is improbable under the learned model OR if any one
of the six descriptors strays far; the two are combined, then reported as the share of the station's own fitted years that
are less unusual (0.95 reads "more unusual than 95% of this station's years").

It is unsupervised: no event is told to the model. It is relative to the station's own record, and it does not claim to be
a measure of damage or of how a person would feel it.

DIMENSIONS. The flow dimension is the only one built so far. The cryosphere (snow, glacier melt) and groundwater are meant
to join as further dimensions: each is a Dimension with a year-by-year feature row and its own descriptors (for example
snow-cover duration or melt timing, a groundwater level against its typical year). Dimensions are standardised and weighted
so each carries the same total variance however many columns it has, and the descriptors of every dimension feed the same
"why". A year missing from a dimension counts as typical for it. Nothing else in the module changes when one is added.

Scale-free and per station, like the rest of Climate Pulse. Pure numpy and scikit-learn.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from types import SimpleNamespace

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from .frameworks import memory, personality
from .models import TimeSeries

MIN_DAYS_FOR_FIT = 300           # a year with fewer days is scored, never used to fit (Köln 1816 has 61)
MIN_DAYS_PER_MONTH = 15          # a month needs this much data to count
VARIANCE_KEPT = 0.80             # the main patterns keep this share of the variance (2 to 5 of them)
LOG_CLIP = 2.0                   # a log10 ratio is held to a factor of 100 either way, so a dry-out to zero is not a 10-sd artefact
WINTER = [11, 12, 1, 2, 3, 4]    # November to April; the rest is summer, when alpine snowmelt arrives

# The six descriptors of the flow dimension, in the order of the page: name, framework of Issue 6, words for its two signs.
DESCRIPTORS = {
    "wetness": ("Pulse", "drier than usual through the year", "wetter than usual through the year"),
    "flood": ("Pulse", "a lower flood peak than usual", "a higher flood peak than usual"),
    "low": ("Pulse", "a lower low flow than usual", "a higher low flow than usual"),
    "personality": ("Personality", "a steadier river than usual", "a flashier river than usual"),
    "memory": ("Memory", "a river quicker to fall back than usual", "a river slower to fall back than usual"),
    "season": ("Breath", "less winter water and more summer water than usual", "more winter water and less summer water than usual"),
}


@dataclass
class YearVector:
    year: int
    n_days: int
    months: list                    # monthly mean flow, None when the month has too little data
    highest: float                  # the year's highest day
    lowest: float                   # the year's lowest 7-day mean flow
    fdc_slope: float
    recession_k: float


@dataclass
class Dimension:
    """A further dimension of the river (the cryosphere, groundwater): a feature row for each year it covers, and descriptors."""
    name: str
    columns: list
    rows: dict                      # year -> list of numbers, one per column
    descriptors: dict = field(default_factory=dict)    # name -> (framework, negative wording, positive wording, function(row) -> number)


def year_vectors(ts: TimeSeries) -> list:
    ts = ts.clean()
    by_year: dict = defaultdict(lambda: ([], []))
    for d, v in zip(ts.dates, ts.values):
        by_year[d.year][0].append(d)
        by_year[d.year][1].append(v)
    out = []
    for y in sorted(by_year):
        dates, vals = by_year[y]
        buckets: dict = defaultdict(list)
        for d, v in zip(dates, vals):
            buckets[d.month].append(v)
        months = [float(np.mean(buckets[m])) if len(buckets.get(m, [])) >= MIN_DAYS_PER_MONTH else None for m in range(1, 13)]
        slice_ = SimpleNamespace(values=vals)
        low7 = min(float(np.mean(vals[i:i + 7])) for i in range(max(1, len(vals) - 6)))          # the lowest 7-day mean: a stable low flow, not one odd day or a zero reading
        out.append(YearVector(y, len(vals), months, max(vals), low7, personality(slice_)["fdc_slope"], memory(slice_)["recession_k"]))
    return out


@dataclass
class RegimeModel:
    station_id: str
    unusual: dict                   # year -> 0..1: the share of this station's fitted years that are less unusual
    nll: dict                       # year -> the negative log-likelihood under the learned model
    descriptors: dict               # year -> {descriptor: standard deviations from this station's typical year, signed}
    raw: dict                       # year -> {descriptor: the departure in its own units, before standardising}
    typical_months: list            # the typical year: the median flow of each month
    typical_highest: float
    typical_lowest: float
    n_components: int
    explained: float
    n_fit: int
    excluded_years: list = field(default_factory=list)

    def normalized(self, year: int) -> float:
        """0..1 unusualness of a year, so this model can stand wherever the XR mapping expects an anomaly model."""
        return self.unusual.get(year, 0.0)

    def why(self, year: int):
        """The descriptor that departs most in this year: (name, framework, wording, standard deviations), or None."""
        d = self.descriptors.get(year)
        if not d:
            return None
        k = max(d, key=lambda n: abs(d[n]))
        fw, neg, pos = DESCRIPTORS[k] if k in DESCRIPTORS else (k, k, k)
        return k, fw, pos if d[k] >= 0 else neg, d[k]


def _lr(v: float, typ: float) -> float:
    return float(np.clip(np.log10(max(v, 1e-9) / max(typ, 1e-9)), -LOG_CLIP, LOG_CLIP))


def _row(yv: YearVector, typ_months, typ_hi: float, typ_lo: float, typ_fdc: float, typ_rec: float) -> np.ndarray:
    mon = [0.0 if v is None else _lr(v, t) for v, t in zip(yv.months, typ_months)]
    return np.array(mon + [_lr(yv.highest, typ_hi), _lr(yv.lowest, typ_lo), yv.fdc_slope, yv.recession_k])


def _flow_descriptors(r: np.ndarray) -> dict:
    mon = r[:12]
    win = [mon[m - 1] for m in WINTER]
    sumr = [mon[m - 1] for m in range(1, 13) if m not in WINTER]
    return {"wetness": float(np.mean(mon)), "flood": float(r[12]), "low": float(r[13]),
            "personality": float(r[14]), "memory": float(r[15]), "season": float(np.mean(win) - np.mean(sumr))}


def fit_regime_model(years: list, station_id: str = "", dimensions=None) -> RegimeModel:
    dimensions = list(dimensions or [])
    fit_years = [y for y in years if y.n_days >= MIN_DAYS_FOR_FIT]
    skipped = [y for y in years if y.n_days < MIN_DAYS_FOR_FIT]
    typ_months = np.array([np.median([y.months[m] for y in fit_years if y.months[m] is not None]) for m in range(12)])
    typ_hi = float(np.median([y.highest for y in fit_years]))
    typ_lo = float(np.median([y.lowest for y in fit_years]))
    typ_fdc = float(np.median([y.fdc_slope for y in fit_years]))
    typ_rec = float(np.median([y.recession_k for y in fit_years]))

    def blocks(y: YearVector):
        b = [_row(y, typ_months, typ_hi, typ_lo, typ_fdc, typ_rec)]
        for dm in dimensions:
            b.append(np.array(dm.rows[y.year], dtype=float) if y.year in dm.rows else np.full(len(dm.columns), np.nan))
        return b

    fit_blocks = [blocks(y) for y in fit_years]
    scalers, weights = [], []
    for bi in range(1 + len(dimensions)):
        M = np.array([fb[bi] for fb in fit_blocks])
        mu = np.nanmean(M, axis=0)
        sd = np.nanstd(M, axis=0)
        sd[sd == 0] = 1.0
        scalers.append((mu, sd))
        weights.append(1.0 / np.sqrt(M.shape[1]))               # each dimension carries the same total variance

    def vector(bl):
        parts = []
        for bi, b in enumerate(bl):
            mu, sd = scalers[bi]
            z = (b - mu) / sd
            parts.append(np.nan_to_num(z, nan=0.0) * weights[bi])      # a year missing from a dimension counts as typical for it
        return np.concatenate(parts)

    X = np.array([vector(bl) for bl in fit_blocks])
    full = PCA().fit(X)
    k = int(np.clip(np.searchsorted(np.cumsum(full.explained_variance_ratio_), VARIANCE_KEPT) + 1, 2, 5))
    pca = PCA(n_components=k).fit(X)
    nll_fit = -pca.score_samples(X)                              # probabilistic PCA: the negative log-likelihood of each year

    def descs(bl):
        d = _flow_descriptors(bl[0])
        for dm, b in zip(dimensions, bl[1:]):
            if not np.isnan(b).all():
                for n, (_, _, _, fn) in dm.descriptors.items():
                    d[n] = float(fn(b))
        return d
    raw_fit = [descs(bl) for bl in fit_blocks]
    names = list(raw_fit[0])
    mu = {n: float(np.mean([r[n] for r in raw_fit])) for n in names}
    sd = {n: (float(np.std([r[n] for r in raw_fit])) or 1.0) for n in names}
    D_fit = np.array([[abs((r[n] - mu[n]) / sd[n]) for n in names] for r in raw_fit]).max(axis=1)     # the largest plain departure of each year

    def pct(sorted_vals, v):
        return float(np.searchsorted(sorted_vals, v, side="left") / max(1, len(sorted_vals) - 1))
    s_nll, s_D = np.sort(nll_fit), np.sort(D_fit)
    comb_fit = np.array([max(pct(s_nll, a), pct(s_D, b)) for a, b in zip(nll_fit, D_fit)])    # unusual if EITHER reading says so
    s_comb = np.sort(comb_fit)

    unusual, nll, desc, raw = {}, {}, {}, {}
    for y, bl in zip(fit_years, fit_blocks):
        r = descs(bl)
        raw[y.year] = r
        desc[y.year] = {n: (r[n] - mu[n]) / sd[n] for n in names}
    for y, e, c in zip(fit_years, nll_fit, comb_fit):
        nll[y.year] = float(e)
        unusual[y.year] = min(1.0, pct(s_comb, c))
    for y in skipped:                                            # scored by inference, never allowed to shape the fit
        bl = blocks(y)
        e = float(-pca.score_samples(vector(bl)[None, :])[0])
        r = descs(bl)
        d = {n: (r[n] - mu[n]) / sd[n] for n in names}
        raw[y.year], desc[y.year], nll[y.year] = r, d, e
        c = max(pct(s_nll, e), pct(s_D, max(abs(v) for v in d.values())))
        unusual[y.year] = min(1.0, pct(s_comb, c))
    return RegimeModel(
        station_id=station_id, unusual=unusual, nll=nll, descriptors=desc, raw=raw,
        typical_months=[float(v) for v in typ_months], typical_highest=typ_hi, typical_lowest=typ_lo,
        n_components=k, explained=float(np.sum(pca.explained_variance_ratio_)), n_fit=len(fit_years),
        excluded_years=[y.year for y in skipped])
