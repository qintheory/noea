"""
Climate Pulse: river — the same four-diagnostic methodology
(pulse/breath/personality/memory) applied to discharge instead of
rainfall. See Issue 6 "River Anatomy".

Public API:
    from noea.climate_pulse.river import build_profile, map_series

    # optional year-level context (trend-aware baseline + how unusual each year was):
    yearly = build_yearly(ts)
    regime = fit_regime_model(year_vectors(ts))      # the river-specific model (regime.py); fit_anomaly_model is the earlier one
    map_series(profile, ts, yearly=yearly, anomaly=regime)
"""
from .models import TimeSeries, XRParameters, DiagnosticProfile, YearlyFlow
from .frameworks import build_profile
from .mapping import map_series, map_timestep
from .loaders import load_grdc_station, load_rhine_stations, load_alpine_stations
from .synthetic import make_leman_like
from .yearly import build_yearly
from .anomaly import RiverAnomalyModel, fit_anomaly_model
from .regime import RegimeModel, fit_regime_model, year_vectors

__all__ = [
    "TimeSeries",
    "XRParameters",
    "DiagnosticProfile",
    "YearlyFlow",
    "build_profile",
    "map_series",
    "map_timestep",
    "load_grdc_station",
    "load_rhine_stations",
    "load_alpine_stations",
    "make_leman_like",
    "build_yearly",
    "RiverAnomalyModel",
    "fit_anomaly_model",
    "RegimeModel",
    "fit_regime_model",
    "year_vectors",
]
