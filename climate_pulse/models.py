"""
Climate Pulse data models.

TimeSeries and XRParameters are reused as-is from noea.models — a daily
rainfall series is already exactly TimeSeries's shape, and Climate Pulse
targets the same XR/sound/fountain contract as the river module.

DiagnosticProfile here is shaped differently from river's: rainfall's
"personality" isn't a handful of station-wide scalars, it's a rhythm —
one R/RR/S/deviation/return-period record per year — because Issue 3/4's
climate "heartbeat" beats once per year, not once per day.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date


@dataclass
class YearlyPulse:
    """One year's climatic heartbeat — what frameworks.py computes and
    mapping.py interprets.
    """
    year: int
    r_value: float                  # max 24h rainfall this year, mm (the R-peak)
    r_date: date                    # when it fell
    rr_days: float | None           # days since the previous year's R event
    s_value: float                  # wettest dry-season (Nov-Apr) day this year, mm
    mean_intensity: float           # mean daily rainfall this year, mm
    stdev: float                    # day-to-day variability this year
    wet_day_frequency: float        # fraction of days with measurable rain
    deviation_from_norm: float      # vs. trailing 30yr mean; 0.0 = normal
    return_period: float            # empirical (Weibull) recurrence interval, in years
                                     # — bounded by sample size, can't exceed ~N years
    return_period_fitted: float     # Gumbel-fitted recurrence interval, in years
                                     # — extrapolates past the sample, matches how
                                     # agencies report "1-in-N-year" events
    annual_total: float             # total rainfall this year, mm


@dataclass
class DiagnosticProfile:
    """Hong Kong's rainfall fingerprint: the full annual record, plus the
    all-time ranges mapping.py needs to judge any single year in context.
    """
    station_id: str
    years: list[YearlyPulse] = field(default_factory=list)

    r_min: float = 0.0
    r_max: float = 0.0
    rr_min: float = 0.0
    rr_max: float = 0.0
    stdev_min: float = 0.0
    stdev_max: float = 0.0
