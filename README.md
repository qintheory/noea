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

**Watch the introduction video:** [youtu.be/JrARNkbITRQ](https://youtu.be/JrARNkbITRQ)

A technical guide to the pipeline is in [`docs/introduction.html`](docs/introduction.html)
(open it in a browser; arrow keys to move, N for notes).

**Try it:** [`docs/index.html`](docs/index.html) is the interactive page: a heart that beats once
for each year of Hong Kong's rainfall, with the analyses behind it, and two more prototypes
(the Rhine and alpine rivers, L'Aire in Geneva). It is built for GitHub Pages and embeds in a web page.

## In short

Noéa translates long hydrological records into something people can
experience. It reads a record — rainfall, river discharge — the way a
cardiologist reads an ECG, looking for rhythm, memory and shock. It then maps
what it finds to two affective values, **valence** (pleasant to unpleasant)
and **arousal** (calm to activated), following Russell's circumplex model of
affect (Russell, 1980; adopted in Noéa Issue 4), for an XR and sound
experience.

Two layers, kept deliberately apart: a **diagnostic layer** (plain science,
deterministic) and a **curatorial layer** (how a result should feel, designed).
Machine learning has one job so far: an unsupervised model learns what a
typical year looks like for each record and scores how unusual each year is.
For Hong Kong rainfall that score also feeds a second, learned reading of valence
and arousal (below); the river and L'Aire modules still use designed mappings.

How people respond to the result has not been tested. That is the research.

## Modules

Noéa is the umbrella. Two independent modules sit under **Climate Pulse**;
they share only the `TimeSeries` and `XRParameters` shapes in
[`noea/models.py`](noea/models.py).

- **`climate_pulse.rainfall`** (Atmosphere): Hong Kong daily rainfall, Hong Kong
  Observatory, 1884–2025: 135 years on record (1940–1946 are missing), 134 complete
  enough to fit.
- **`climate_pulse.river`** (Rivers): daily discharge at eight stations on the Rhine
  and in the Swiss Alps (GRDC and FOEN).

The method is designed to apply to any long record; these two are the
worked examples, not the scope.

The **Human-Water Interface** (`noea/human_water_interface/`) is the local
counterpart, in development; see below.

### Valence and arousal for Hong Kong, learned from the record

[`affect.py`](noea/climate_pulse/rainfall/affect.py) builds an emergent affect map from the record
itself. A varimax-rotated PCA on the six yearly features finds two factors, *intensity* (the peak day,
its rarity, how concentrated the rain was, its spread) and *wetness* (wet-day frequency and the year's
total against the previous 30 years). Then:

- **arousal** is the mean of the year's rank on intensity and on the anomaly score;
- **valence** is the mean of the year's rank on its departure from a normal year (intense, very wet or very
  dry) and on the anomaly score, reversed so the most unusual years read towards −1.

Both are ranks among the 134 fitted years, with equal weights and nothing tuned, so they are relative to
this record. Eight consistency checks were fixed in advance and are exported with the result; seven pass.
Valence and arousal correlate at −0.71, just past the 0.70 limit the checks set, so the two axes are not
fully independent. **This is a hypothesis, not a measurement: no participants have rated these years.**
The designed mapping in `mapping.py` (size, tempo, texture, and the earlier valence and arousal formulas)
is unchanged and is what produces the XR frames today.

## Human-Water Interface (in development)

Where Climate Pulse reads long records, the Human-Water Interface (HWI) works at
the scale of one river and the people beside it: short, fast records from a few
nearby sensors. The first site is **L'Aire, Geneva**. Three steps so far:

1. **Load and check.** Validated daily and hourly flow and rain are loaded,
   checked for gaps and bad values, and each gauge gets its own seasonal norm.
2. **Learn.** An unsupervised model learns what a usual day looks like at each
   gauge and scores how unusual each day is. It is fitted on 2014–2022 and tested
   on 2023–2025, years it never saw.
3. **Map.** The curatorial layer turns the seasonal norm and the learned score
   into valence and arousal, plus size, tempo and texture, one frame per day.

Data: the cantonal monitoring network, *Veille Hydro-météorologique du Canton de
Genève*, run for the Office cantonal de l'eau (OCEau). Only its validated history
export is used. The data is not stored in this repository: fetch it with
`python3 -m noea.human_water_interface.fetch`.

## Run

Needs Python with numpy, scipy and scikit-learn.

```bash
python3 demo_climate_pulse_rainfall.py   # Hong Kong rainfall
python3 demo_climate_pulse_river.py      # eight river stations
python3 demo.py                          # river, synthetic data
python3 demo_human_water_interface_replay.py   # L'Aire, after fetching the data
```

## Layout

```
noea/
├── models.py                    shared TimeSeries and XRParameters
├── climate_pulse/
│   ├── rainfall/                loaders, frameworks, anomaly, affect, mapping, data/
│   └── river/                   loaders, frameworks, yearly, anomaly, mapping, data/
└── human_water_interface/       loaders, quality, baselines, anomaly, mapping, fetch
demo_*.py                        one or more demos per module
docs/                            interactive page (index.html), introduction deck, and their sources
```

In each module, `frameworks.py` is the diagnostic layer (in the Human-Water
Interface, `quality.py` and `baselines.py`), `anomaly.py` is the learned model,
and `mapping.py` is the curatorial layer. Hong Kong's `affect.py` sits beside the anomaly
model: it is learned from the record and feeds the interactive page.

## References

- Meeting of Waters, Noéa project: https://www.meetingofwaters.org/noea
- Noéa Issue 3, "Hong Kong Heartbeat" (March 2025); Issue 4, "Affective
  Climate" (June 2025); Issue 6, "River Anatomy" (April 2026)
- Russell, J. A. (1980). A circumplex model of affect. *Journal of Personality
  and Social Psychology*, 39(6), 1161–1178.
- Data: Hong Kong Observatory (HKO); Global Runoff Data Centre (GRDC); Swiss
  Federal Office for the Environment (FOEN); Office cantonal de l'eau, Geneva
  (OCEau)
