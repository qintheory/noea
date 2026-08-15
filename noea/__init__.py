"""
Noéa — the affective intelligence. The umbrella for every module below it:

    noea.climate_pulse.rainfall   — Issue 3/4, Hong Kong rainfall
    noea.climate_pulse.river      — Issue 6, Rhine/alpine discharge
    noea.hwi                      — Human-Water Interface (future)

This top-level package holds only what every module shares: the input and
output shapes (TimeSeries, XRParameters). No science, no art — modules
implement those independently. See each module's own __init__.py for its
public API.
"""
from .models import TimeSeries, XRParameters

__all__ = [
    "TimeSeries",
    "XRParameters",
]
