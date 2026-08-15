"""
Climate Pulse: rainfall — Hong Kong rainfall's climatic heartbeat.

Public API:
    from noea.climate_pulse.rainfall import load_rainfall, build_profile, map_series
"""
from .loaders import load_rainfall
from .frameworks import build_profile
from .mapping import map_series, map_year
from .models import YearlyPulse, DiagnosticProfile
from .anomaly import AnomalyModel, fit_anomaly_model

__all__ = [
    "load_rainfall",
    "build_profile",
    "map_series",
    "map_year",
    "YearlyPulse",
    "DiagnosticProfile",
    "AnomalyModel",
    "fit_anomaly_model",
]
