# Interactive explorers and the combined page

One explorer per implementation (Hong Kong rainfall, Rhine and alpine rivers, L'Aire). Each shows the record, the diagnostics
drawn from it and the learned anomaly score, and stops before the XR mapping. Everything is generated from the pipeline.

For Hong Kong the page also shows a heart: one beat per year. **Colour is valence** (two colours and the gradient between them),
**beat intensity is arousal**, **beat pace is the days since the previous annual peak**, and the shape is the year's rain round a
circle, January at the top. Valence and arousal come from `noea/climate_pulse/rainfall/affect.py`, a learned map relative to the
record that has not been tested with viewers. The heart has three views of the same stage, **Flat**, **3D** and **Map** (every
year as a dot on valence against arousal, the current year moving).

The Rhine and alpine rivers chapter is laid out the same way. The result is on top: the eight gauges drawn as one branching river that flows down the page, coloured by the chosen year's anomaly score, with a year slider and play. Below it are the analysis steps and the **Ribbon** (Issue 6's stacked ribbon) with a station chip for each gauge. A window switch limits what is drawn to 1951–2020 (the 70 years all four Rhine stations share, as in Issue 6) or the full record; the models are still fitted on each station's whole record, so scores and ranks do not change. The river is a schematic, not a map: width is each station's usual flow, and the confluences are placed from the river geography, not from the data files. The rivers are scored by `noea/climate_pulse/river/regime.py`: each year is described against the station's own typical year (twelve monthly anomalies, flood peak, low flow, flashiness, recession), a probabilistic PCA learns what the station's years look like, and the score is the share of its own years that are less unusual. Six plain measures, one for each framework of Issue 6, say what departed. The model is built in dimensions so that the cryosphere and groundwater can be added later.

| File | What it is |
| --- | --- |
| `build_explorers.py` | Computes each implementation's data and writes standalone pages and `data/*.json` |
| `build_site.py` | Builds the combined page into `docs/` (`index.html`, `explore/`): introduction, three chapters, documentation lightbox |
| `engine.js`, `engine.css`, `fragment.html` | The shared explorer |
| `heart.js` | The heart (flat, 3D and map views), used by the explorer and by the stage of the combined page |
| `site.html`, `site.js`, `site.css` | The combined page |

Rebuild, from the repository root:

```bash
python3 docs/source/explorers/build_site.py            # recomputes the data (slow: it refits the Human-Water Interface model)
python3 docs/source/explorers/build_site.py --assets   # only the page, scripts and styles, from the data already written
```

## Publishing

GitHub Pages is on: deploy from branch `main`, folder `/docs`. The page is live at **https://qintheory.github.io/noea/**
(`#atmosphere`, `#rivers`, `#laire` open a chapter directly), and it updates a minute or two after each push to `main`.
It sends no `X-Frame-Options` header, so it can be framed from meetingofwaters.org.

Webflow: one Embed element holding a full-bleed iframe, the same way as the Hong Kong Heartbeat page.

```html
<iframe src="https://qintheory.github.io/noea/" title="Noéa" loading="lazy" allow="fullscreen"
        style="position:absolute;top:0;left:0;right:0;bottom:0;width:100%;height:100%;border:0"></iframe>
```

The page's ground is the same `#E0ECF8` as that Webflow page. If the iframe should grow with the content instead of
filling the viewport, the page posts `{ source: "noea", type: "height", height }` to its parent.

## Fonts

The page loads the same Adobe Fonts kit as meetingofwaters.org (`https://use.typekit.net/pwm6lyt.css`): Athelas for reading text,
Frutiger (`neue-frutiger-world`) for titles, labels and navigation, uppercase and tracked as on the site. Page views therefore
count against that Adobe Fonts kit. Where the kit does not load, the page falls back to Georgia and Arial.

## The L'Aire data

`docs/explore/data/hwi.json` is derived from the OCEau validated export and is git-ignored. Without it the page builds and the
chapter says it is not published yet. Remove the line from `.gitignore` once the data may be republished.
