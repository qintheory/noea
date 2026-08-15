"""
Climate Pulse — Noéa's ECG-inspired diagnostic methodology
(pulse/breath/personality/memory), applied independently to two data
sources: rainfall (climate_pulse.rainfall) and river discharge
(climate_pulse.river). See Issue 3/4 (rainfall) and Issue 6 (river).

Deliberately no re-exports here — rainfall and river are independent
implementations of the same shared contract (noea.models), not a blended
module. Import from whichever one you need:

    from noea.climate_pulse.rainfall import build_profile, map_series
    from noea.climate_pulse.river import build_profile, map_series
"""
