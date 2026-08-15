"""
Noéa data models — the shared vocabulary across the whole system.

Noéa is the umbrella (the affective intelligence); Climate Pulse (rainfall
and river) and, in future, Human-Water Interface are independent modules
underneath it. These two shapes are the only things they all share:

    raw data  ->  TimeSeries  ->  diagnostic framework  ->  XRParameters (served)

Each module defines its own DiagnosticProfile in its own models.py — that
shape genuinely differs (rainfall's is a per-year record, river's is a
handful of station-wide scalars) and doesn't belong here. Keeping this
file to just the two shared shapes means every downstream consumer
(sonification, fountain control, XR mesh) reads the same contract
regardless of which module, or which science, produced a given frame.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date


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
