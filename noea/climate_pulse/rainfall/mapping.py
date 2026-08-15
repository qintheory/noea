"""
The mapping layer — Climate Pulse's curatorial translation from rainfall
rhythm to XR parameters.

frameworks.py only ever measures (R, RR, S, deviation, return period —
still just facts). This is the only file where those facts become a felt
quality: how urgent a year's rhythm feels, whether it reads as drought,
flood-shock, or calm.

No clustering here. An earlier version fit k-means archetypes and read
valence/arousal off each year's cluster centroid — dropped, because
averaging years into buckets diluted exactly the outliers it was meant to
catch (2023's shock reading disappeared once folded into a 44-member
"wetter" cluster; see project history).

The "how extreme was this year" signal now comes from anomaly.py's fitted
PCA reconstruction model — a genuine unsupervised model (fit once on the
full historical record, scored per year via inference), not a hand-picked
formula. Every year is still scored individually, never averaged into a
group, so an outlier can't be diluted the way clustering diluted it.
"""
from __future__ import annotations

from noea.models import XRParameters
from .anomaly import AnomalyModel, fit_anomaly_model
from .models import DiagnosticProfile, YearlyPulse

# how far a deviation ratio has to swing before valence's "normal" component bottoms out
VALENCE_DEVIATION_SPAN = 1.0
# how much the learned anomaly score can additionally pull valence down, beyond deviation alone
SHOCK_VALENCE_WEIGHT = 1.2


def _norm(value: float, lo: float, hi: float) -> float:
    """Clamp value into 0..1 given a low/high range. Safe if lo==hi."""
    if hi <= lo:
        return 0.5
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def map_year(profile: DiagnosticProfile, yp: YearlyPulse, anomaly: AnomalyModel) -> XRParameters:
    """Turn one year's rainfall rhythm into XR parameters, using the
    station's own all-time range for context (what counts as extreme here).

    `anomaly` is the model fit once (in map_series) on the whole record —
    this is what catches a storm buried in an otherwise ordinary year
    (2023: mild annual deviation, +0.14, but 425mm fell in one day) without
    needing deviation itself to be extreme.
    """
    p = XRParameters(station_id=profile.station_id, timestamp=yp.r_date)

    # --- diameter: how big was this year's peak event, all-time? ---
    p.diameter = round(_norm(yp.r_value, profile.r_min, profile.r_max), 4)

    # --- pulse_rhythm: RR interval, HRV-style — short gap = fast rhythm ---
    # inverted: a short interval since the last extreme reads fast (up to 1.6),
    # a long settled gap reads slow (down to 0.4) — same span river uses.
    if yp.rr_days is not None:
        rr_pos = _norm(yp.rr_days, profile.rr_min, profile.rr_max)
        p.pulse_rhythm = round(1.6 - rr_pos * 1.2, 4)
    else:
        p.pulse_rhythm = 1.0

    shock = anomaly.normalized(yp.year)

    # --- arousal: this year's own peak/rhythm urgency, plus the learned
    # anomaly score (how much this year's whole feature profile stands out) ---
    magnitude = _norm(yp.r_value, profile.r_min, profile.r_max)
    urgency = (1.0 - _norm(yp.rr_days, profile.rr_min, profile.rr_max)
               if yp.rr_days is not None else 0.5)
    p.arousal = round(0.3 * magnitude + 0.2 * urgency + 0.5 * shock, 4)

    # --- valence: a tent centred on "normal" (drought AND flood read negative
    # from deviation alone), pulled further down by shock on top of that ---
    # Issue 4: excess reads as anxiety/crisis, deficit reads as numbness —
    # only near-normal years are calm. The shock term is what lets a year
    # with an unremarkable annual total still read as crisis if one day was
    # extreme enough (2023), without needing deviation itself to be extreme.
    dev_ratio = min(1.0, abs(yp.deviation_from_norm) / VALENCE_DEVIATION_SPAN)
    base = 0.6 - 1.6 * dev_ratio
    p.valence = round(max(-1.0, base - SHOCK_VALENCE_WEIGHT * shock), 4)

    # --- texture: day-to-day variability this year, relative to all years ---
    p.texture = round(_norm(yp.stdev, profile.stdev_min, profile.stdev_max), 4)

    # --- luminosity: no temperature series in this dataset yet ---
    p.luminosity = 0.5

    return p


def map_series(profile: DiagnosticProfile) -> list[XRParameters]:
    """Fit the anomaly model once on the full record, then map every year."""
    anomaly = fit_anomaly_model(profile)
    return [map_year(profile, yp, anomaly) for yp in profile.years]
