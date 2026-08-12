"""
Noéa pipeline — data to XR-ready parameters.

Public API:
    from noea import TimeSeries, build_profile, map_series
"""
from .models import TimeSeries, XRParameters, DiagnosticProfile
from .frameworks import build_profile
from .mapping import map_series, map_timestep

__all__ = [
    "TimeSeries",
    "XRParameters",
    "DiagnosticProfile",
    "build_profile",
    "map_series",
    "map_timestep",
]
