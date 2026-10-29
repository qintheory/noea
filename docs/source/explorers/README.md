# Interactive explorers and the combined page

One explorer per implementation (Hong Kong rainfall, Rhine and alpine rivers, L'Aire). Each shows the record, the diagnostics
drawn from it and the learned anomaly score, and stops before the XR mapping. Everything is generated from the pipeline.

| File | What it is |
| --- | --- |
| `build_explorers.py` | Computes each implementation's data and writes standalone pages and `data/*.json` |
| `build_site.py` | Builds the combined page into `docs/` (`index.html`, `explore/`): introduction, three chapters, documentation lightbox |
| `engine.js`, `engine.css`, `fragment.html` | The shared explorer |
| `site.html`, `site.js`, `site.css` | The combined page |

Rebuild, from the repository root:

```bash
python3 docs/source/explorers/build_site.py
```

## Publishing

GitHub Pages: Settings, Pages, deploy from branch `main`, folder `/docs`. The page is then at `https://qintheory.github.io/noea/`
(`#atmosphere`, `#rivers`, `#laire` open a chapter directly).

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
