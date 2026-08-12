"""
The mapping layer — from science to the XR-ready parameters.

This is the hinge of the whole system. The scientific layer (frameworks.py)
is deterministic and objective. The *curatorial* decisions — how a drought
should feel, where the valence axis sits — live here, isolated, so an artist
can tune them without touching the science.

For each timestep we produce one XRParameters object:

    discharge (vs the station's own range)   -> diameter, arousal
    seasonal position (this month vs the year)-> pulse_rhythm
    temperature anomaly (if available)        -> luminosity
    low-flow proximity (near Q90?)            -> valence (drought = negative)

Everything is normalised against the station's OWN profile, so a small alpine
stream and a great lake are each expressed on their own terms.
"""

from __future__ import annotations
from datetime import date

from .models import TimeSeries, DiagnosticProfile, XRParameters


def _norm(value: float, lo: float, hi: float) -> float:
    """Clamp value into 0..1 given a low/high range. Safe if lo==hi."""
    if hi <= lo:
        return 0.5
    t = (value - lo) / (hi - lo)
    return max(0.0, min(1.0, t))


def map_timestep(
    profile: DiagnosticProfile,
    when: date,
    discharge: float,
    temperature: float | None = None,
    temp_baseline: float | None = None,
) -> XRParameters:
    """Turn one moment's readings into XR parameters, using the profile
    for context (what counts as high/low for THIS station).
    """
    p = XRParameters(station_id=profile.station_id, timestamp=when)

    # --- diameter: discharge against the station's observed span ---
    p.diameter = _norm(discharge, profile.min_flow, profile.max_flow)

    # --- arousal: how energetic is the river right now? ---
    # high flow = high arousal; also spikes above the median lift it.
    above_median = _norm(discharge, profile.q50, profile.max_flow)
    p.arousal = round(0.35 * p.diameter + 0.65 * above_median, 4)

    # --- pulse_rhythm: seasonal position, 0.4 (slow) .. 1.6 (fast) ---
    month = when.month
    m_val = profile.monthly_means[month - 1]
    yr_lo = min(profile.monthly_means)
    yr_hi = max(profile.monthly_means)
    season = _norm(m_val, yr_lo, yr_hi)          # 0 in low season, 1 in high
    p.pulse_rhythm = round(0.4 + season * 1.2, 4)

    # --- valence: how does today compare to what THIS SEASON expects? ---
    # A summer at half its usual flow is a drought and reads negative, even
    # if the absolute number sits above the all-time Q90. Winter low water is
    # normal and stays neutral. This seasonal-relative reading is what makes
    # drought *felt* rather than merely measured.
    expected = profile.monthly_means[month - 1]   # normal flow for this month
    if expected > 0:
        ratio = discharge / expected              # 1.0 = a normal day
        if ratio < 1.0:
            # below seasonal normal -> negative valence, steeper the drier.
            # ratio 1.0 -> 0 ; ratio 0.4 -> about -1 (severe drought)
            p.valence = round(max(-1.0, (ratio - 1.0) / 0.6), 4)
        else:
            # above seasonal normal -> mild positive (abundance), capped.
            p.valence = round(min(0.6, (ratio - 1.0) * 0.8), 4)
    else:
        p.valence = 0.0

    # --- luminosity: temperature anomaly, if we have it ---
    if temperature is not None and temp_baseline is not None:
        # +/- 6 degC window around baseline mapped to 0..1
        p.luminosity = _norm(temperature - temp_baseline, -6.0, 6.0)
    else:
        p.luminosity = 0.5

    # --- texture: use flashiness as a stand-in until sediment data exists ---
    p.texture = round(min(1.0, profile.fdc_slope / 3.0), 4)

    return p


def map_series(
    profile: DiagnosticProfile,
    discharge_ts: TimeSeries,
    temperature_ts: TimeSeries | None = None,
) -> list[XRParameters]:
    """Map a whole discharge series to a list of XRParameters (one per day).

    Optional temperature series is matched by date where present.
    """
    temp_lookup: dict[date, float] = {}
    temp_baseline = None
    if temperature_ts is not None:
        tclean = temperature_ts.clean()
        temp_lookup = dict(zip(tclean.dates, tclean.values))
        if tclean.values:
            temp_baseline = sum(tclean.values) / len(tclean.values)

    out: list[XRParameters] = []
    dts = discharge_ts.clean()
    for d, v in zip(dts.dates, dts.values):
        out.append(
            map_timestep(
                profile,
                when=d,
                discharge=v,
                temperature=temp_lookup.get(d),
                temp_baseline=temp_baseline,
            )
        )
    return out
