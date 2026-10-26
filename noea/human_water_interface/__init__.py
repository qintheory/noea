"""
Human-Water Interface (HWI): the local counterpart to Climate Pulse.

Climate Pulse reads long records (decades to centuries) of one variable at a
time. HWI works at the scale of one river and the people beside it: short,
fast, multi-variable records from a handful of nearby sensors. First site:
L'Aire, Geneva, with the cantonal monitoring network run for OCEau.

Independent of the Climate Pulse modules: it shares only TimeSeries and
XRParameters from noea.models.
"""
from .loaders import (
    STATIONS, RAIN_STATIONS, MEDIA, fetch_export, parse_export, load_daily, load_intraday, coverage,
)
from .models import IntradaySeries

__all__ = ["STATIONS", "RAIN_STATIONS", "MEDIA", "fetch_export", "parse_export", "load_daily",
           "load_intraday", "coverage", "IntradaySeries"]
