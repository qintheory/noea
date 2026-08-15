"""
Climate Pulse: river — the same four-diagnostic methodology
(pulse/breath/personality/memory) applied to discharge instead of
rainfall. See Issue 6 "River Anatomy".

Public API:
    from noea.climate_pulse.river import build_profile, map_series
"""
from .models import TimeSeries, XRParameters, DiagnosticProfile
from .frameworks import build_profile
from .mapping import map_series, map_timestep
from .loaders import load_grdc_station, load_rhine_stations, load_alpine_stations
from .synthetic import make_leman_like

__all__ = [
    "TimeSeries",
    "XRParameters",
    "DiagnosticProfile",
    "build_profile",
    "map_series",
    "map_timestep",
    "load_grdc_station",
    "load_rhine_stations",
    "load_alpine_stations",
    "make_leman_like",
]
