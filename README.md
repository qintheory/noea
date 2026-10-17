# Noéa Pipeline

**Noéa** — "Affective AI for Water-Climate" — is a project by
[Meeting of Waters](https://www.meetingofwaters.org), an art-driven NGO
based in Geneva, Switzerland, active since 2022. Noéa reads
hydrometeorological data as an affective signal rather than a purely
technical one — treating a river's flow or a city's rainfall record as
something with its own rhythm, memory, and mood, alongside the scientific
rigor of the data itself.

Full project background, design essays, and the published Issue series live
at **[meetingofwaters.org/noea](https://www.meetingofwaters.org/noea)**.

## In short

Noéa translates long hydrological records into something people can
experience. It reads a record — rainfall, river discharge — the way a
cardiologist reads an ECG, looking for rhythm, memory and shock. It then maps
what it finds to six XR parameters, two of them affective — **valence** (how
pleasant or distressing) and **arousal** (how activated) — alongside four
physical readouts (size, glow, texture, tempo). These are designed to feed an
XR and sound experience; that output contract is still unconfirmed (see
below).

Two layers, kept deliberately apart. The **science layer** is plain
hydrology: for Hong Kong, over a century of daily rainfall from the
Observatory — annual peaks, the gaps between them, return periods; for the
Rhine and its alpine tributaries, eight stations of discharge — flow
duration, recession, the seasonal cycle. The **curatorial layer** decides what
a drought or a flood should feel like: how alarming, how heavy. It is kept
separate from the measurements, so the feeling can be redesigned without
changing any of the science.

Machine learning has one job so far: finding unusual years. For each record
an unsupervised model learns what a typical year looks like, then scores how
badly each year fails to fit it.

A seven-slide introduction is in [`docs/`](docs/) as a
[PDF](docs/noea-introduction.pdf) and an editable
[PowerPoint](docs/noea-introduction.pptx) with speaker notes.

The method is designed to apply to any long record. Hong Kong rainfall and
the Rhine and alpine discharge are the worked examples, not the scope.

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

## Designed to be universal

Noéa is a method, not a Hong Kong model or a Rhine model. Any long
hydrometeorological record can be run through the same load → diagnose → map
pipeline: write a loader that produces a `TimeSeries` and the rest takes
over. Hong Kong rainfall and the Rhine and alpine discharge records are the
two worked examples — the sample records the methods were built and tested
on — not the scope of the system.

What "universal" does and doesn't mean here:

- **The method transfers; the fitted model doesn't.** Every record fits its
  own model on its own history (one for the rainfall record, one per river
  station) and is judged against its own norm. A Hong Kong model is never
  applied to the Rhine, and nothing pretrained is shipped or reused.
- **It is a design goal tested on two records, not a demonstrated result.**
  No third site has been run through it yet.
- **A new kind of series needs its own diagnostics.** Rainfall and discharge
  each have their own science layer. Something like groundwater levels would
  need one too; what carries over is the shared contract and the per-record
  modelling approach.

What is currently tied to the two sample sites and would need revisiting for
a new region:

- **Rainfall season and wet-day definitions.** The dry season is November to
  April (Hong Kong's monsoon calendar) and a wet day is 0.1 mm or more (the
  Observatory's convention). A different climate regime needs its own.
- **Data-completeness cutoffs** (200 days for rainfall, 300 for river) were
  chosen by inspecting the gaps in these two datasets.
- **The curatorial weights** — how hard an extreme year pulls valence down —
  were set while checking Hong Kong and Rhine events. They are artistic
  judgements, and a new setting may call for its own.
- **The Gumbel return-period fit** assumes annual maxima follow an
  extreme-value distribution. That is standard, but worth checking per site.

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
period), then maps each year to `XRParameters`.

**The rainfall model** (`anomaly.py`; the river module has its own, below): a PCA reconstruction-
error model, fit once on every year's 6-feature vector, scoring how well
each year's *own* feature vector reconstructs from a compressed
representation of the whole record's shared structure — a year that
doesn't resemble the record's dominant patterns reconstructs poorly (high
error), and that error drives valence/arousal. This is genuinely fit and
scored (training + inference), not a hand-picked formula — see the
module's docstring for why PCA rather than a deep autoencoder (135
samples is too little data for that not to just memorize every point; a
linear autoencoder converges to PCA anyway) and why not k-means clustering
(an earlier archetype pass diluted exactly the outliers it was meant to
catch — a shock year's signal disappeared once averaged into a 40+ member
"wetter" cluster).

One data-quality fix this surfaced: 2025's 31-day partial year was
initially left in the fitting set and its degenerate reconstruction error
(a tiny denominator inflating peak-concentration) dominated the scale,
compressing every genuine year — including 1926, the actual record flood
— toward the bottom. Checking day-counts empirically (not guessing) found
55 of 135 years have 268–299 days (real, if incomplete, years) and only
2025 is truly degenerate at 26 — a large, unambiguous gap. Excluding only
years below 200 days from fitting (while still scoring them via inference)
fixed it without discarding ~40% of otherwise-real years the way a naive
threshold did.

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
curve, breath = seasonal cycle).

Validated against every named event in Issue 6, not just assumed correct:
- **1976 drought** and **1995 flood** — `mapping.py` originally read the
  real Jan 1995 flood (98% of Köln's all-time-max discharge) as valence
  +0.60, the *maximum possible positive* value, because "above the
  seasonal normal" was scored as mild abundance regardless of how extreme.
  Fixed with an all-time-extremity term (same class of fix already applied
  to rainfall's valence for 2023). Now reads -0.57.
- **1999–2002 "sustained fullness"** — confirmed: all four stations,
  every year, 107–139% of their own all-time mean.
- **Post-2010 "long-term drying"** — real but more nuanced than Issue 6's
  text implies. 1980s→2010s: every station declined (Lustenau -5%, Basel
  -9%, Köln -18%, Lobith -19%, stronger downstream). But three of four
  stations' data ends in 2020, and Köln — the only one with real 2020–2024
  coverage — shows a partial *rebound* (+3.5% vs. the 2010s), not
  continued decline. The multi-decade trend is real; "still worsening
  right now" isn't confirmed by what we can actually check.

### Year-level model and trend-aware baseline

The whole-record `DiagnosticProfile` can't say a decade is running dry
against its own recent past, and eight whole-record profiles are too few
rows to fit anything. `yearly.py` therefore computes one `YearlyFlow` per
station-year — reusing `frameworks.py`'s pulse / personality / memory
functions on one-year slices, so the physics stays in one place and
`frameworks.py` is untouched — including a deviation from the trailing
30-year mean. That baseline sees the decline the static profile couldn't:
Köln and Lobith average +0.13 in the 1980s against about −0.07 in the 2010s
(the 2020s column is a single year for Basel, Lustenau and Lobith, whose
data ends in 2020).

`anomaly.py` then fits one PCA reconstruction-error model per station on
its own years (six scale-free features; 62–208 years each; 56–73% of variance
retained in two components), the same technique as the rainfall module,
reimplemented rather than imported because the two modules are independent.
`map_series(..., yearly=, anomaly=)` gives each day the context of its year.
Both arguments are optional; omit them and a day is read on its own.

What it actually does, checked rather than assumed:
- **It flags documented floods.** The top-scoring years include Lustenau
  and Aare-Brienzwiler 2005 (each station's all-time maximum, 22–23 Aug),
  Aare-Thun 1999 (all-time maximum, 15 May) and Köln and Lobith 1993
  (24–25 Dec). Those dates match the
  [August 2005 Alpine floods](https://en.wikipedia.org/wiki/2005_European_floods),
  the [May 1999 Swiss floods](https://www.wsl.ch/en/natural-hazards/understanding-and-forecasting-floods/flood-and-landslide-damage-database/major-events/)
  (Thun, on the Aare) and the
  [Christmas 1993 Rhine flood](https://www.wetteronline.de/extremwetter/weihnachtshochwasser-am-rhein-evakuierungen-und-sachschaeden-1993-12-24-wh)
  (Köln's gauge peaked on Christmas Eve). The model was never given these
  events; it scored the years as unusual from the discharge record alone.
- **It does not flag droughts, or the 1995 flood at Köln.** 1976 ranks
  188th of 209 years at Köln, and 1995 ranks 102nd. PCA reconstruction
  error finds years whose *combination* of features is unusual, not years
  that are extreme *along* the main wet-to-dry axis, and a drought sits on
  that axis. Drought still reads through the day-level formulas and the
  trend-aware deviation; the learned model adds a signal, it does not
  replace those.
- **The year terms are centred on the station's typical year.** Applied
  raw, an always-positive term subtracted from every day and pushed the
  whole record about 15 points more negative; centred, it only
  redistributes.

A correction to my own earlier river valence fix: the all-time-extremity
term first measured distance from the median across the whole range, which
treated a routine seasonal high as a crisis. In the synthetic demo a normal
summer melt peak read −0.77, and 57% of every station's days read negative.
Spot checks on a flood, a drought and a typical day had all passed; a
whole-record distribution check caught it. Extremity now applies only in the
true tails (beyond Q10 or below Q90). Named events are unchanged (1995 flood
−0.57 at Köln, 1976 droughts −1.00) and the synthetic peak reads −0.27.

**Open calibration question**: about 50–56% of days still read negative
(mean −0.16 to −0.22), against a balanced rainfall record. That skew comes
from the original seasonal-ratio formula, which compares each day to the
monthly *mean*; daily flows are right-skewed, so most days sit below it and
are penalised steeply. It predates this work and is unchanged. Whether to
recalibrate it is a curatorial decision, not a bug fix.

No station's data reaches 2025 or 2026 (three end Dec 2020, Köln ends Dec
2024) — any claim about current conditions needs a data update to check.

**Not yet built**: Issue 6's multi-station "ribbon" / XR-body composite —
combining all eight stations into one continuous, position-aware form —
is a separate, bigger design step beyond the current one-profile-per-
station diagnostic layer, and is on hold pending the output contract
question below.

## The output contract

**Status: unconfirmed.** This shape was already present in the repo's
first commit, before any of the module work documented here — it has not
been separately confirmed with the XR/technical side (Dan). Everything in
both `mapping.py` modules is built against it, so treat it as provisional
scaffolding, not a settled spec, until that confirmation happens.

Every module ultimately produces the same `XRParameters` shape:

| field         | range   | drives (XR)        | drives (sound)       |
|---------------|---------|--------------------|----------------------|
| diameter      | 0..1    | body size           | —                    |
| luminosity    | 0..1    | emission glow        | —                    |
| texture       | 0..1    | surface roughness    | —                    |
| pulse_rhythm  | 0.4..1.6| animation tempo       | tempo                |
| valence       | -1..+1  | colour temperature    | major/minor, silence |
| arousal       | 0..1    | overall intensity     | sound intensity      |

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
    │   ├── anomaly.py                 — the model: PCA reconstruction-error, fit + inference
    │   ├── mapping.py                 — curatorial mapping (uses anomaly.py's score)
    │   └── data/rainfall.csv
    └── river/
        ├── models.py                  — DiagnosticProfile (re-exports TimeSeries/XRParameters)
        ├── loaders.py                 — GRDC/FOEN discharge files → TimeSeries
        ├── frameworks.py              — pulse/personality/memory/breath diagnostics
        ├── yearly.py                  — one record per station-year, trend-aware baseline
        ├── anomaly.py                 — per-station PCA reconstruction-error model
        ├── mapping.py                 — curatorial mapping (optional year context)
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
