"""
Noéa data models — the shared vocabulary of the pipeline.

Everything flows through these structures:
    raw data  ->  TimeSeries  ->  diagnostic frameworks  ->  XRParameters (served)

Keeping these small and explicit means every downstream consumer
(sonification, fountain control, XR mesh) reads the same shape.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class TimeSeries:
    """A single hydrological variable over time, for one station/location.

    dates and values are parallel lists (index i in dates maps to index i
    in values). We keep it this simple deliberately — pandas can wrap it
    when needed, but the pipeline's contract is just 'dates + values'.
    """
    station_id: str
    variable: str            # e.g. "discharge", "water_temperature"
    unit: str                # e.g. "m3/s", "degC"
    dates: list[date]
    values: list[float]

    def __post_init__(self):
        if len(self.dates) != len(self.values):
            raise ValueError(
                f"{self.station_id}/{self.variable}: "
                f"{len(self.dates)} dates but {len(self.values)} values"
            )

    def __len__(self) -> int:
        return len(self.values)

    def clean(self) -> "TimeSeries":
        """Drop points where value is None or NaN. Returns a new TimeSeries."""
        pairs = [
            (d, v) for d, v in zip(self.dates, self.values)
            if v is not None and v == v  # v == v is False for NaN
        ]
        ds = [p[0] for p in pairs]
        vs = [p[1] for p in pairs]
        return TimeSeries(self.station_id, self.variable, self.unit, ds, vs)


@dataclass
class XRParameters:
    """The output contract of the pipeline — normalised 0..1 unless noted.

    These are exactly the values a downstream module reads:
      - XR mesh:      diameter, luminosity, texture, pulse_rhythm
      - sonification: valence, arousal, pulse_rhythm
      - fountain:     diameter (-> pump speed), pulse_rhythm (-> surge rate)

    timestamp lets the consumer scrub through time (a performance, a loop).
    """
    station_id: str
    timestamp: date

    diameter: float = 0.5          # normalised discharge (drives size / pump)
    luminosity: float = 0.5        # temperature anomaly (drives glow)
    texture: float = 0.0           # sediment / turbulence index
    pulse_rhythm: float = 1.0      # seasonal FDC position (drives tempo)

    valence: float = 0.0           # -1..+1 curatorial (drives colour/mood)
    arousal: float = 0.0           # 0..1 curatorial (drives intensity)

    def as_dict(self) -> dict:
        """Flat dict, JSON-ready — this is what the API/endpoint serves."""
        return {
            "station_id": self.station_id,
            "timestamp": self.timestamp.isoformat(),
            "diameter": round(self.diameter, 4),
            "luminosity": round(self.luminosity, 4),
            "texture": round(self.texture, 4),
            "pulse_rhythm": round(self.pulse_rhythm, 4),
            "valence": round(self.valence, 4),
            "arousal": round(self.arousal, 4),
        }


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
