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
"wetter" cluster; see project history). Every year is scored directly from
its own feature values instead, continuously — there's no bucket for an
outlier to hide inside.
"""
from __future__ import annotations
import math

from noea.models import XRParameters
from .models import DiagnosticProfile, YearlyPulse

# how far a deviation ratio has to swing before valence's "normal" component bottoms out
VALENCE_DEVIATION_SPAN = 1.0
# how much a single-event shock can additionally pull valence down, beyond deviation alone
SHOCK_VALENCE_WEIGHT = 1.2


def _norm(value: float, lo: float, hi: float) -> float:
    """Clamp value into 0..1 given a low/high range. Safe if lo==hi."""
    if hi <= lo:
        return 0.5
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def _shock(profile: DiagnosticProfile, yp: YearlyPulse) -> float:
    """How much a single event dominated this year, 0..1.

    This is what catches a storm buried in an otherwise ordinary year —
    2023 had a mild annual deviation (+0.14) but 425mm fell in one day.
    Three independent readings of "how extreme," averaged: the peak's raw
    size, its statistical rarity (Gumbel-fitted, so genuinely rare events
    register even past the sample size), and what fraction of the whole
    year's rain landed in that single day.

    Rarity is log-scaled before normalising: return periods span 1 to
    ~244 years and that top end (1926) is itself a huge outlier, so a
    plain linear scale crushes everything else into "moderate" — 2023's
    genuinely rare 49-year return period read as only 0.2 on a linear
    0..244y scale. log10 keeps the ordering but stops one outlier from
    setting the scale for everyone else.
    """
    magnitude = _norm(yp.r_value, profile.r_min, profile.r_max)
    rarity = _norm(math.log10(yp.return_period_fitted),
                    math.log10(profile.return_period_fitted_min),
                    math.log10(profile.return_period_fitted_max))
    concentration = _norm(yp.peak_concentration,
                           profile.concentration_min, profile.concentration_max)
    return (magnitude + rarity + concentration) / 3.0


def map_year(profile: DiagnosticProfile, yp: YearlyPulse) -> XRParameters:
    """Turn one year's rainfall rhythm into XR parameters, using the
    station's own all-time range for context (what counts as extreme here).
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

    shock = _shock(profile, yp)

    # --- arousal: this year's own peak/rhythm urgency, plus how much a
    # single event dominated it ---
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
    """Map every year in the profile to one XRParameters frame."""
    return [map_year(profile, yp) for yp in profile.years]
