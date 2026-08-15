"""
Climate Pulse: river data models.

TimeSeries is reused as-is from noea.models (re-exported below so
frameworks.py/mapping.py's existing `from .models import TimeSeries` keeps
resolving unchanged). DiagnosticProfile is river-specific: a station's
personality reduced to a handful of scalars — genuinely different in shape
from rainfall's per-year record (see climate_pulse/rainfall/models.py),
which is exactly why each module keeps its own.
"""

from __future__ import annotations
from dataclasses import dataclass, field

from noea.models import TimeSeries, XRParameters  # noqa: F401 — re-exported for `.models` imports

__all__ = ["TimeSeries", "XRParameters", "DiagnosticProfile"]


@dataclass
class DiagnosticProfile:
    """The 'personality' of a station, computed once from its full record.

    These are the four frameworks from the design plan, reduced to numbers
    the mapping layer can use. Think of it as the river's fingerprint.
    """
    station_id: str

    # pulse (hydrograph)
    mean_flow: float = 0.0
    max_flow: float = 0.0
    min_flow: float = 0.0

    # personality (flow duration curve)
    q10: float = 0.0               # high-flow exceedance
    q50: float = 0.0               # median
    q90: float = 0.0               # low-flow exceedance
    fdc_slope: float = 0.0         # steepness = flashiness

    # memory (recession)
    recession_k: float = 0.0       # decay constant (higher = holds water)

    # breath (seasonality)
    monthly_means: list[float] = field(default_factory=lambda: [0.0] * 12)

    def summary(self) -> str:
        character = "flashy" if self.fdc_slope > 1.0 else "steady"
        return (
            f"Station {self.station_id}: {character} "
            f"(mean {self.mean_flow:.1f}, Q90 {self.q90:.1f}, "
            f"Q10 {self.q10:.1f})"
        )
