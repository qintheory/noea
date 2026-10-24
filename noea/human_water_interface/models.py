"""HWI data models. TimeSeries (daily) is shared from noea.models; sub-daily needs its own."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime


@dataclass
class IntradaySeries:
    """A variable sampled more than once a day (hourly, 15-minute, 5-minute).

    TimeSeries holds calendar dates only, which is right for Climate Pulse's daily
    records and wrong here, so HWI keeps timestamps. `stamps` are the start of each
    interval, timezone-naive local (Europe/Zurich) time, as the source reports it.
    """
    station_id: str
    variable: str
    unit: str
    interval_seconds: int
    stamps: list[datetime]
    values: list[float]

    def __post_init__(self):
        if len(self.stamps) != len(self.values):
            raise ValueError(f"{self.station_id}/{self.variable}: {len(self.stamps)} stamps but {len(self.values)} values")

    def __len__(self) -> int:
        return len(self.values)
