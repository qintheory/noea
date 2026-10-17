# Source of the introduction deck

The seven-slide introduction in `docs/` is generated. **All of its text lives in
[`content.py`](content.py)**: slide copy, speaker notes and references. The PowerPoint, the
PDF and the HTML are built from that one file, so they cannot disagree. To change a word,
edit `content.py` and rebuild; do not edit the generated files.

`content.py` opens with the rules the copy follows (claim only what the code or a cited
source supports; one term per concept; slides carry the written claim, notes carry the
spoken version) and closes with the facts that were checked against the data, and when.
Re-check those when the data or models change.

## Rebuild

From the repository root:

```bash
python3 docs/source/build_pptx.py docs/noea-introduction.pptx                     # static, with speaker notes
ANIMATE=1 python3 docs/source/build_pptx.py docs/noea-introduction-animated.pptx  # cover ECG wipes in
python3 docs/source/build_html.py docs/introduction.html                     # single file, ECG animates
```

The PDF is a render of the static PowerPoint. Layout scripts need `python-pptx`, `Pillow`
and the Athelas and Frutiger fonts installed (the HTML loads them from the same Adobe
Fonts kit as meetingofwaters.org).

## Files

| path | what |
|---|---|
| `content.py` | every word of the deck, plus references and checked facts |
| `build_pptx.py`, `build_html.py` | layout only; no copy |
| `assets/` | logo, noéa wordmark, anomaly ribbon, Hong Kong ECG strip, and decorative images: the river close-up (`river_closeup.jpg`, baked into `slide2_decor.jpg` by `make_background.py`) and the blue atmosphere piece (`atmosphere.jpg`) |
| `data/r_rr_s_by_year.csv` | Hong Kong annual peak rainfall and peak spacing, from [hkheartbeat](https://github.com/qintheory/hkheartbeat) |
| `make_chart.py` | redraws the anomaly ribbon (slide 6) from the pipeline, in the visual language of Issue 6's ribbon but coloured by anomaly score (`python3 docs/source/make_chart.py docs/source/assets`) |
| `make_ecg.py` | redraws the ECG strip and GIF from the CSV |
| `recording/` | working copies of the scripts that composite the cover frames and encode the MP4 (macOS, Swift); they expect a 1920×1080 render of the cover without the ECG |
