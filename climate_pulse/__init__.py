"""
Climate Pulse — Hong Kong rainfall's climatic heartbeat.

Public API:
    from climate_pulse import load_rainfall, build_profile, map_series
"""
from .loaders import load_rainfall
from .frameworks import build_profile
from .mapping import map_series, map_year
from .models import YearlyPulse, DiagnosticProfile

__all__ = [
    "load_rainfall",
    "build_profile",
    "map_series",
    "map_year",
    "YearlyPulse",
    "DiagnosticProfile",
]
