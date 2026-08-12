"""
The mapping layer — Climate Pulse's curatorial translation from rainfall
rhythm to XR parameters.

frameworks.py only ever measures (R, RR, S, deviation, return period —
still just facts). This is the only file where those facts become a felt
quality: how urgent a year's rhythm feels, whether it reads as drought,
flood-shock, or calm.

diameter, pulse_rhythm, and texture are still hand-authored physical
readouts — they track size, speed, and roughness, not mood, so there's no
reason for them to be learned. valence and arousal can optionally come
from clustering.py's fitted archetypes instead (a `mood` override below):
that's how a storm-shock year gets its "this felt like a crisis" reading
even when its annual total looks unremarkable — see clustering.py's
docstring for why the single-axis formula couldn't do that alone.
"""
from __future__ import annotations

from noea.models import XRParameters
from .models import DiagnosticProfile, YearlyPulse

# how far a deviation ratio has to swing before valence bottoms out
VALENCE_DEVIATION_SPAN = 1.0


def _norm(value: float, lo: float, hi: float) -> float:
    """Clamp value into 0..1 given a low/high range. Safe if lo==hi."""
    if hi <= lo:
        return 0.5
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def map_year(
    profile: DiagnosticProfile,
    yp: YearlyPulse,
    mood: tuple[float, float] | None = None,
) -> XRParameters:
    """Turn one year's rainfall rhythm into XR parameters, using the
    station's own all-time range for context (what counts as extreme here).

    `mood`, if given, is a (valence, arousal) pair from a fitted cluster
    archetype (see clustering.py) — it overrides the deterministic formulas
    below for those two fields only.
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

    if mood is not None:
        p.valence, p.arousal = round(mood[0], 4), round(mood[1], 4)
    else:
        # --- arousal: magnitude of this year's peak + how tightly it followed the last ---
        magnitude = _norm(yp.r_value, profile.r_min, profile.r_max)
        urgency = (1.0 - _norm(yp.rr_days, profile.rr_min, profile.rr_max)
                   if yp.rr_days is not None else 0.5)
        p.arousal = round(0.6 * magnitude + 0.4 * urgency, 4)

        # --- valence: a tent centred on "normal" — drought AND flood both read negative ---
        # Issue 4: excess reads as anxiety/crisis (negative, high-arousal), deficit
        # reads as numbness (negative, low-arousal) — only near-normal years are calm.
        # NOTE: this single-axis version can't see a storm buried in an otherwise
        # ordinary year (2023) — that's exactly what clustering.py's `mood` fixes.
        dev_ratio = min(1.0, abs(yp.deviation_from_norm) / VALENCE_DEVIATION_SPAN)
        p.valence = round(0.6 - 1.6 * dev_ratio, 4)

    # --- texture: day-to-day variability this year, relative to all years ---
    p.texture = round(_norm(yp.stdev, profile.stdev_min, profile.stdev_max), 4)

    # --- luminosity: no temperature series in this dataset yet ---
    p.luminosity = 0.5

    return p


def map_series(
    profile: DiagnosticProfile,
    cluster_labels: dict[int, int] | None = None,
    cluster_moods: dict[int, tuple[float, float]] | None = None,
) -> list[XRParameters]:
    """Map every year in the profile to one XRParameters frame.

    Pass `cluster_labels` (year -> cluster id, from ClusterModel.labels) and
    `cluster_moods` (cluster id -> (valence, arousal), from propose_moods()
    or your own overrides) to use the clustered mood instead of the
    deterministic valence/arousal formulas.
    """
    def mood_for(yp: YearlyPulse) -> tuple[float, float] | None:
        if cluster_labels is None or cluster_moods is None:
            return None
        return cluster_moods.get(cluster_labels.get(yp.year))

    return [map_year(profile, yp, mood=mood_for(yp)) for yp in profile.years]
