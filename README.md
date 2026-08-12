# Noéa Pipeline

Data → XR-ready parameters. The shared spine for both Noéa modules
(Climate Pulse XR + Human–Water Interface sonification / fountain).

## What it does

```
raw hydrological data
      │
      ▼
  TimeSeries            (models.py     — shared vocabulary)
      │
      ▼
  four frameworks       (frameworks.py — scientific layer, deterministic)
      │   pulse · personality · memory · breath
      ▼
  DiagnosticProfile     (the station's fingerprint)
      │
      ▼
  mapping layer         (mapping.py    — curatorial: artistic decisions live here)
      │
      ▼
  XRParameters  →  xr_output.json      (the contract every module reads)
```

## Run it

```bash
python3 demo.py
```

Generates a synthetic Léman-like record, builds the profile, maps every day
to XR parameters, writes `xr_output.json`, and prints sample days.

No dependencies required — pure standard library. (numpy/pandas optional later.)

## The output contract

Each frame in `xr_output.json`:

| field         | range   | drives (XR)        | drives (sound)       | drives (fountain)    |
|---------------|---------|--------------------|----------------------|----------------------|
| diameter      | 0..1    | river body size    | —                    | pump speed / height  |
| luminosity    | 0..1    | emission glow      | —                    | (optional lighting)  |
| texture       | 0..1    | surface roughness  | —                    | —                    |
| pulse_rhythm  | 0.4..1.6| animation tempo    | tempo                | surge rate           |
| valence       | -1..+1  | colour temperature | major/minor, silence | stillness vs motion  |
| arousal       | 0..1    | overall intensity  | sound intensity      | vigour               |

## Design principle

The **scientific layer** (`frameworks.py`) is objective and never changes for
artistic reasons. The **curatorial layer** (`mapping.py`) is where every
artistic decision lives — how drought should feel, where valence sits. Tune
the art there without ever touching the science. That separation is the whole
point.

## Next steps

1. **Real Léman data** — write `loaders.py` to read CIPEL / OCEau / hydrodata
   CSVs into a `TimeSeries`. The rest of the pipeline doesn't change.
2. **Serve it live** — wrap `xr_output.json` in a small FastAPI endpoint so
   Unity / the fountain / the sonification patch can pull frames by date.
3. **Sonification** — a consumer that reads frames and drives sound
   (valence → major/minor, arousal → intensity, drought → silence).
4. **Fountain (Level 1)** — a consumer that reads `diameter` → pump PWM.

## Files

- `noea/models.py`      — TimeSeries, XRParameters, DiagnosticProfile
- `noea/frameworks.py`  — the four diagnostic frameworks
- `noea/mapping.py`     — science → XR parameters (curatorial layer)
- `noea/synthetic.py`   — test data generator (replace with real loaders)
- `demo.py`             — end-to-end runnable example
