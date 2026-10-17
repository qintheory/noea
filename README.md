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

How people respond to the result has not been tested. That is the research.

## Modules

Noéa is the umbrella. Two independent modules sit under **Climate Pulse**;
they share only the `TimeSeries` and `XRParameters` shapes in
[`noea/models.py`](noea/models.py).

- **`climate_pulse.rainfall`**: Hong Kong daily rainfall, Hong Kong
  Observatory, 1884–2025.
- **`climate_pulse.river`**: daily discharge at eight stations on the Rhine
  and in the Swiss Alps (GRDC and FOEN).

The method is designed to apply to any long record; these two are the
worked examples, not the scope. A Human-Water Interface module is planned.

## Run

Needs Python with numpy, scipy and scikit-learn.

```bash
python3 demo_climate_pulse_rainfall.py   # Hong Kong rainfall
python3 demo_climate_pulse_river.py      # eight river stations
python3 demo.py                          # river, synthetic data
```

## Layout

```
noea/
├── models.py                  shared TimeSeries and XRParameters
└── climate_pulse/
    ├── rainfall/              loaders, frameworks, anomaly, mapping, data/
    └── river/                 loaders, frameworks, yearly, anomaly, mapping, data/
docs/                          introduction and its source
```

Each module's `frameworks.py` is the diagnostic layer; its `mapping.py` is the
curatorial layer; `anomaly.py` is the learned model.

## References

- Meeting of Waters, Noéa project: https://www.meetingofwaters.org/noea
- Noéa Issue 3, "Hong Kong Heartbeat" (March 2025); Issue 4, "Affective
  Climate" (June 2025); Issue 6, "River Anatomy" (April 2026)
- Russell, J. A. (1980). A circumplex model of affect. *Journal of Personality
  and Social Psychology*, 39(6), 1161–1178.
- Data: Hong Kong Observatory (HKO); Global Runoff Data Centre (GRDC); Swiss
  Federal Office for the Environment (FOEN)
