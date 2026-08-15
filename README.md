# Noéa Pipeline

**Noéa** — "Affective AI for Water-Climate" — is a project by
[Meeting of Waters](https://www.meetingofwaters.org), an art-driven NGO
founded by Charlotte Qin (Geneva, Switzerland, active since 2022), built in
collaboration with HKUST, GainForest, ETH Eawag, the Hong Kong Observatory,
and the World Meteorological Organization. Noéa reads hydrometeorological
data as an affective signal rather than a purely technical one — treating a
river's flow or a city's rainfall record as something with its own rhythm,
memory, and mood, alongside the scientific rigor of the data itself.

Full project background, design essays, and the published Issue series live
at **[meetingofwaters.org/noea](https://www.meetingofwaters.org/noea)**.

## Noéa is the umbrella

Noéa is the affective intelligence itself — the umbrella for every module
below it, present and future:

```
noea/                              (the umbrella — shared shapes only)
├── climate_pulse/                 the ECG-inspired diagnostic methodology
│   ├── rainfall/                  Issue 3/4 — Hong Kong rainfall
│   └── river/                     Issue 6 — Rhine/alpine discharge
└── hwi/                           Human-Water Interface — future,
                                    proximate sensing (pH, oxygen, flow,
                                    sound) + XR presence, not built yet
```

`climate_pulse.rainfall` and `climate_pulse.river` are **independent
implementations of the same methodology** (pulse/breath/personality/memory)
applied to different data — neither imports from the other, and each has
its own loaders, diagnostics, and curatorial decisions. What they share
is the contract below, and `noea/models.py`, which defines it.

## The shared contract: load → diagnose → map

```
raw data (rainfall, discharge, ...)
      │
      ▼
  TimeSeries            (noea/models.py — shared vocabulary)
      │
      ▼
  diagnostic framework   (frameworks.py — scientific layer, deterministic)
      │
      ▼
  DiagnosticProfile      (the station's fingerprint — shape differs per module)
      │
      ▼
  mapping layer          (mapping.py — curatorial: artistic decisions live here)
      │
      ▼
  XRParameters  →  output.json      (the contract every consumer reads)
```

`noea/models.py` holds only the shared shapes (`TimeSeries`, `XRParameters`)
— no science, no art. Every module implements load → diagnose → map on its
own, so a downstream consumer (XR engine, sonification patch, fountain
controller) can read any module's output without knowing which one, or
which science, produced it.

## climate_pulse.rainfall — Hong Kong rainfall

```bash
python3 demo_climate_pulse_rainfall.py
```

Loads Hong Kong Observatory daily rainfall (1884–2025,
`noea/climate_pulse/rainfall/data/rainfall.csv`), computes an ECG-inspired
diagnostic per year (R = annual peak rainfall, RR = days between peaks,
S = dry-season anomaly, plus deviation from a rolling 30-year norm,
peak-concentration, and both an empirical and a Gumbel-fitted return
period), then maps each year to `XRParameters`. `mapping.py` scores
valence and arousal continuously from each year's own features — no
clustering: an earlier k-means archetype pass diluted exactly the outlier
years it was meant to catch (a shock year's signal disappeared once
averaged into a 40+ member "wetter" cluster), so it was dropped in favour
of scoring every year independently.

**Known limitation, honestly**: Gumbel-fitted return periods are the
standard method for this kind of data and can extrapolate past the sample
size (unlike the empirical/Weibull version, capped at ~135 years), but may
still diverge from press-reported figures like "1-in-500-years" — likely a
rolling-24h vs. calendar-day data definition difference rather than a
modeling error.

## climate_pulse.river — Rhine and alpine discharge

```bash
python3 demo_climate_pulse_river.py    # real GRDC/FOEN data, 8 stations
python3 demo.py                        # synthetic Léman-like data
```

Real discharge data for the eight stations Issue 6 "River Anatomy" names:
four Rhine mainstem (Lustenau, Basel, Köln, Lobith — GRDC) and four alpine
headwaters (Weisse Lütschine, Reuss-Andermatt, Aare-Brienzwiler, Aare-Thun
— FOEN). `frameworks.py` computes the same four diagnostics as rainfall's
(pulse = hydrograph, personality = flow-duration curve, memory = recession
curve, breath = seasonal cycle), and its results — computed with code
originally tuned only against synthetic data — match Issue 6's own
narrative description of these rivers (downstream buffering in fdc_slope
and recession_k, Weisse Lütschine's flashy melt-driven fdc_slope), a real
validation the design held up on data it had never seen.

**Not yet built**: Issue 6's multi-station "ribbon" / XR-body composite —
combining all eight stations into one continuous, position-aware form —
is a separate, bigger design step beyond the current one-profile-per-
station diagnostic layer.

## The output contract

Every module ultimately produces the same `XRParameters` shape:

| field         | range   | drives (XR)        | drives (sound)       | drives (fountain)    |
|---------------|---------|--------------------|----------------------|----------------------|
| diameter      | 0..1    | body size           | —                    | pump speed / height  |
| luminosity    | 0..1    | emission glow        | —                    | (optional lighting)  |
| texture       | 0..1    | surface roughness    | —                    | —                    |
| pulse_rhythm  | 0.4..1.6| animation tempo       | tempo                | surge rate           |
| valence       | -1..+1  | colour temperature    | major/minor, silence | stillness vs motion  |
| arousal       | 0..1    | overall intensity     | sound intensity      | vigour               |

## Design principle

The **scientific layer** (`frameworks.py` in each module) is objective and
never changes for artistic reasons. The **curatorial layer** (`mapping.py`)
is where every artistic decision lives — how drought should feel, where
valence sits. Tune the art there without ever touching the science. That
separation is the whole point, and it holds independently in every module.

## Files

```
noea/
├── __init__.py, models.py             — TimeSeries, XRParameters (shared shapes only)
└── climate_pulse/
    ├── rainfall/
    │   ├── models.py                  — YearlyPulse, DiagnosticProfile
    │   ├── loaders.py                 — HKO rainfall CSV → TimeSeries
    │   ├── frameworks.py              — R/RR/S/deviation/return-period diagnostics
    │   ├── mapping.py                 — continuous curatorial mapping (no clustering)
    │   └── data/rainfall.csv
    └── river/
        ├── models.py                  — DiagnosticProfile (re-exports TimeSeries/XRParameters)
        ├── loaders.py                 — GRDC/FOEN discharge files → TimeSeries
        ├── frameworks.py              — pulse/personality/memory/breath diagnostics
        ├── mapping.py                 — curatorial mapping
        ├── synthetic.py               — synthetic Léman-like test data
        └── data/rhine/, alpine_headwaters.csv

demo.py                          — river, synthetic data
demo_climate_pulse_rainfall.py   — rainfall, real HKO data
demo_climate_pulse_river.py      — river, real GRDC/FOEN data (8 stations)
```

## References

- Meeting of Waters — Noéa project: https://www.meetingofwaters.org/noea
- Noéa Issue 3, "Hong Kong Heartbeat" (March 2025)
- Noéa Issue 4, "Affective Climate" (June 2025)
- Noéa Issue 6, "River Anatomy" (April 2026)
- Rainfall data: Hong Kong Observatory (HKO)
- River discharge data: Global Runoff Data Centre (GRDC); Swiss Federal
  Office for the Environment (FOEN)
