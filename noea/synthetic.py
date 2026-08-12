"""
Synthetic data — a stand-in Léman-like river/outflow record so the whole
pipeline runs end-to-end before real CIPEL/OCEau data is wired in.

It fakes a plausible daily discharge series with:
  - a seasonal cycle (snowmelt-fed summer high, winter low)
  - year-to-year variation
  - one embedded drought year (to prove the valence/silence logic works)
  - a matching temperature series (warm summer surface, cold winter)

Replace this with a real loader (loaders.py) when you have the data — the
rest of the pipeline doesn't change at all.
"""

from __future__ import annotations
import math
import random
from datetime import date, timedelta

from .models import TimeSeries


def make_leman_like(
    station_id: str = "LEMAN-OUTFLOW",
    start_year: int = 2000,
    n_years: int = 20,
    seed: int = 42,
    drought_year_offset: int = 12,
) -> tuple[TimeSeries, TimeSeries]:
    """Return (discharge_ts, temperature_ts) for n_years of daily data."""
    rng = random.Random(seed)

    start = date(start_year, 1, 1)
    days = 365 * n_years
    dates: list[date] = [start + timedelta(days=i) for i in range(days)]

    discharge: list[float] = []
    temperature: list[float] = []

    # Rhône-at-Léman-ish baseline ~250 m3/s, summer melt peak.
    base_flow = 250.0
    seasonal_amp = 120.0     # summer swell
    temp_mean = 12.0
    temp_amp = 8.0           # surface temp swing across the year

    for d in dates:
        doy = d.timetuple().tm_yday
        year_idx = d.year - start_year

        # seasonal term: peak around day 210 (late July snowmelt)
        phase = 2 * math.pi * (doy - 210) / 365.0
        seasonal = math.cos(phase)

        flow = base_flow + seasonal_amp * seasonal
        flow += rng.gauss(0, 18)                 # daily noise
        flow += 15 * math.sin(year_idx)          # slow multi-year wobble

        # embedded drought year: suppress flow hard
        if year_idx == drought_year_offset:
            flow *= 0.45

        discharge.append(max(20.0, flow))

        # temperature: warm in summer, cold in winter, inverse-ish to melt
        t_phase = 2 * math.pi * (doy - 200) / 365.0
        temp = temp_mean + temp_amp * math.cos(t_phase) + rng.gauss(0, 0.6)
        temperature.append(round(temp, 2))

    dis_ts = TimeSeries(station_id, "discharge", "m3/s", dates, discharge)
    tmp_ts = TimeSeries(station_id, "water_temperature", "degC", dates, temperature)
    return dis_ts, tmp_ts
