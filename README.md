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
This repository implements two of Noéa's prototypes described there:

- **Climate Pulse** (Prototype I, "Climate Heartbeat") — reads long-term
  precipitation records as a climatic rhythm, per Noéa Issue 3 "Hong Kong
  Heartbeat" (March 2025) and Issue 4 "Affective Climate" (June 2025) —
  both published at the link above.
- **Human-Water Interface** (Prototype II) — real-time river/lake signals
  (flow, temperature) for sonification and physical installation (fountain),
  per Issue 6. Currently a prototype against synthetic data; real-data
  integration is next.

Both are independent implementations of the same shared contract — see
below — so a downstream consumer (XR engine, sonification patch, fountain
controller) can read either one's output without knowing which module, or
which science, produced it.

## The shared contract: load → diagnose → map

```
raw data (rainfall, discharge, ...)
      │
      ▼
  TimeSeries            (noea/models.py — shared vocabulary)
      │
      ▼
  diagnostic framework   (*/frameworks.py — scientific layer, deterministic)
      │
      ▼
  DiagnosticProfile      (the station's fingerprint — shape differs per module)
      │
      ▼
  mapping layer          (*/mapping.py — curatorial: artistic decisions live here)
      │
      ▼
  XRParameters  →  output.json      (the contract every consumer reads)
```

`noea/` holds only the shared shapes (`TimeSeries`, `XRParameters`) — no
science, no art. `climate_pulse/` and `noea/` (river) each implement the
same load → diagnose → map shape independently, with entirely different
physics underneath. Neither module imports from the other.

## climate_pulse/ — Hong Kong rainfall

```bash
python3 demo_climate_pulse.py
```

Loads Hong Kong Observatory daily rainfall (1884–2025, `climate_pulse/data/rainfall.csv`),
computes an ECG-inspired diagnostic per year (R = annual peak rainfall, RR =
days between peaks, S = dry-season anomaly, plus deviation from a rolling
30-year norm and both an empirical and a Gumbel-fitted return period), then
maps each year to `XRParameters`. Includes a first k-means pass toward
learned mood archetypes (`clustering.py`) — **actively being tuned**; the
deterministic per-year formulas in `mapping.py` are the stable fallback.

**Known limitations, honestly**: the emotional mapping currently reads
extreme/shock years correctly (negative valence, high arousal) but doesn't
yet give drought years an equivalently negative reading — see commit
history and project notes for the ongoing diagnosis. Return periods are
capped by methodology (empirical: ~sample size; Gumbel-fitted: better, but
may still diverge from press-reported figures, likely a rolling-24h vs.
calendar-day data definition difference rather than a modeling error).

## noea/ — River (Human-Water Interface prototype)

```bash
python3 demo.py
```

Generates a synthetic Léman-like discharge record, builds a station
fingerprint (mean/max/min flow, flow-duration curve, recession constant,
seasonal means), maps every day to XR parameters, writes `xr_output.json`.
No dependencies required — pure standard library.

**Next**: a real loader for CIPEL / OCEau / hydrodata CSVs (`noea/loaders.py`,
not yet written) — the rest of the pipeline doesn't change.

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
separation is the whole point, and it holds independently in both modules.

## Files

- `noea/models.py`             — TimeSeries, XRParameters (shared shapes)
- `noea/frameworks.py`         — river's four diagnostic frameworks
- `noea/mapping.py`            — river's curatorial mapping
- `noea/synthetic.py`          — river test data generator
- `demo.py`                    — river end-to-end example
- `climate_pulse/models.py`    — YearlyPulse, DiagnosticProfile
- `climate_pulse/loaders.py`   — HKO rainfall CSV → TimeSeries
- `climate_pulse/frameworks.py`— R/RR/S/deviation/return-period diagnostics
- `climate_pulse/mapping.py`   — deterministic curatorial mapping
- `climate_pulse/clustering.py`— k-means mood archetypes (in progress)
- `demo_climate_pulse.py`      — Climate Pulse end-to-end example

## References

- Meeting of Waters — Noéa project: https://www.meetingofwaters.org/noea
- Noéa Issue 3, "Hong Kong Heartbeat" (March 2025)
- Noéa Issue 4, "Affective Climate" (June 2025)
- Noéa Issue 6 (river / Human-Water Interface prototype)
- Rainfall data: Hong Kong Observatory (HKO)
