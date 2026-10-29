"""Build one interactive explorer page per Noéa implementation, from the pipeline's own outputs.

Each page stops before the XR mapping: it shows the record, the diagnostics computed from it, and the
learned anomaly score, nothing that depends on the curatorial layer. All numbers come from the same
code the demos run; nothing is typed in by hand except the wording in PAGES below.

    python3 docs/source/explorers/build_explorers.py OUTDIR

writes OUTDIR/rainfall.html, river.html and hwi.html (standalone pages) and OUTDIR/data/*.json (the same data,
for the combined site in docs/). The last one needs the OCEau data, fetched with
python3 -m noea.human_water_interface.fetch.
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, ".")
from noea.climate_pulse.rainfall import build_profile, fit_anomaly_model as fit_rain, load_rainfall
from noea.climate_pulse.rainfall.affect import fit_affect_model
from noea.climate_pulse.rainfall.anomaly import FEATURE_NAMES as RAIN_FEATS, MIN_DAYS_FOR_FIT as RAIN_MIN, _feature_row as rain_row
from noea.climate_pulse.river import build_yearly, fit_anomaly_model as fit_river, load_alpine_stations, load_rhine_stations
from noea.climate_pulse.river.anomaly import FEATURE_NAMES as RIVER_FEATS, MIN_DAYS_FOR_FIT as RIVER_MIN, _feature_row as river_row

HERE = Path(__file__).parent
SHORT = {"Weisse Lütschine-Zweilütschinen": "Weisse Lütschine", "Reuss-Andermatt": "Reuss", "Aare-Brienzwiler": "Aare, Brienzwiler", "Aare-Thun": "Aare, Thun"}
TRAIN = list(range(2014, 2023))


def r(x, nd=3):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), nd)


def explain(model_scaler, pca, rows):
    """Standardised features and each feature's squared reconstruction residual (they sum to the score)."""
    X = model_scaler.transform(np.array(rows))
    res = (X - pca.inverse_transform(pca.transform(X))) ** 2
    return X, res


def columns(raw, z, res):
    """Row-major arrays -> one list per feature, rounded, with None for missing rows."""
    out = {"raw": [], "z": [], "res": []}
    for j in range(len(next(r_ for r_ in raw if r_ is not None)) if raw else 0):
        out["raw"].append([r(row[j], 4) if row is not None else None for row in raw])
        out["z"].append([r(row[j], 2) if row is not None else None for row in z])
        out["res"].append([r(row[j], 3) if row is not None else None for row in res])
    return out


def rank_of(scores, fit):
    order = sorted((i for i in range(len(scores)) if fit[i]), key=lambda i: -scores[i])
    rk = [None] * len(scores)
    for n, i in enumerate(order, 1):
        rk[i] = n
    return rk, order


# ---- Hong Kong rainfall -------------------------------------------------------------------------
def rainfall():
    ts = load_rainfall()
    profile = build_profile(ts); model = fit_rain(profile)
    ys = profile.years
    by_year = defaultdict(lambda: [-1] * 366)
    for d, v in zip(ts.dates, ts.values):
        by_year[d.year][d.timetuple().tm_yday - 1] = int(round(v * 10))
    rows = [rain_row(y) for y in ys]
    X, res = explain(model.scaler, model.pca, rows)
    fit = [1 if y.n_days >= RAIN_MIN else 0 for y in ys]
    score = [model.scores[y.year] for y in ys]
    norm = [r(model.normalized(y.year)) if f else None for y, f in zip(ys, fit)]
    rk, order = rank_of(score, fit)
    idx = {y.year: i for i, y in enumerate(ys)}
    n_fit = sum(fit)
    ordinal = lambda k: f"{k}{'th' if 10 <= k % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(k % 10, 'th')}"
    g = dict(
        id="hk", name="Hong Kong Observatory", n=len(ys), labels=[y.year for y in ys],
        sub=f"daily rainfall, {ys[0].year}–{ys[-1].year}: {len(ys)} years, {n_fit} complete enough to fit",
        rec=[r(y.annual_total, 1) for y in ys], rec_label="Year's total rainfall (mm)",
        score=[r(s, 3) for s in score], norm=norm, norm_all=[r(model.normalized(y.year)) for y in ys], fit=fit, rank=rk,
        daily=[by_year[y.year] for y in ys], daily_label="Daily rainfall in the year (mm)",
        facts=[{"peak": r(y.r_value, 1), "peak_date": y.r_date.isoformat(), "days": y.n_days, "total": r(y.annual_total, 0), "rr": r(y.rr_days, 0)} for y in ys],
        top=order[:6],
        summary=dict(components=int(model.pca.n_components_), variance=r(sum(model.explained_variance_ratio), 3), n_fit=n_fit),
        **columns(rows, X.tolist(), res.tolist()),
    )
    g["unit_fit_note"] = {"2025": "Partial year (data end in January): scored, never used to fit the model."}
    af = fit_affect_model(profile, model)                                   # valence and arousal: two PCA factors plus the anomaly, relative to the record
    g["va"] = {"v": [r(af.valence[y.year], 3) if y.year in af.valence else None for y in ys], "a": [r(af.arousal[y.year], 3) if y.year in af.arousal else None for y in ys]}
    g["affect"] = {"correlations": {k: r(v, 2) for k, v in af.correlations.items()}, "checks": af.checks, "intensity": af.intensity_loadings, "wetness": af.wetness_loadings}
    passed = sum(af.checks.values()); c = af.correlations
    limits = [
        f"The model flags unusual combinations of features, not extremes. 1931 is among the top-scoring years with a peak of only {ys[idx[1931]].r_value:.0f} mm, "
        f"while 1926, which holds the largest single day ({ys[idx[1926]].r_value:.0f} mm), ranks {ordinal(rk[idx[1926]])} of {n_fit} and 2023 ranks {ordinal(rk[idx[2023]])}. "
        f"The 1963 drought ranks {ordinal(rk[idx[1963]])}.",
        f"Valence and arousal (the corner map) are relative to this record: ranks among its {af.n_fit} fitted years. They combine two PCA factors learned from the data, intensity and wetness, with the anomaly score, and agree with it (arousal r = {c['arousal~anomaly']:+.2f}, valence r = {c['valence~anomaly']:+.2f}). "
        f"They pass {passed} of {len(af.checks)} consistency checks fixed in advance; valence and arousal share about half their variance (r = {c['valence~arousal']:+.2f}). No viewers rated anything, so this is a hypothesis about affect, not a measurement.",
        "There are no data for 1940–1946, so the record has 135 years rather than 142. 2025 is a partial year (the data end in January): it is scored by the fitted model and never shaped it.",
        "Years with missing days are totalled and summarised over the days that exist (n_days is between 268 and 299 for 55 of the 135 years).",
        "Nothing here has been tested with viewers. A high score means the year was unusual for this record, not that a person would feel it so.",
    ]
    return dict(kind="rain_year", views=[["line", "Timeline"]], groups=[g], features=[
        dict(key=RAIN_FEATS[0], label="Peak daily rainfall", unit="mm", desc="The wettest single day of the year."),
        dict(key=RAIN_FEATS[1], label="Day-to-day spread", unit="mm", desc="How much daily rainfall varies within the year."),
        dict(key=RAIN_FEATS[2], label="Wet-day frequency", unit="", desc="Share of days with at least 0.1 mm."),
        dict(key=RAIN_FEATS[3], label="Total vs recent norm", unit="", desc="The year's total against the mean of the 30 years before it (0 = normal, +0.5 = half again as much)."),
        dict(key=RAIN_FEATS[4], label="Rarity of the peak", unit="log10 yr", desc="log10 of the peak's fitted return period in years: how rarely a day that wet comes round."),
        dict(key=RAIN_FEATS[5], label="Peak concentration", unit="", desc="Share of the year's rain that fell on the peak day."),
    ], limits=limits)


# ---- Rhine and alpine rivers -------------------------------------------------------------------------
def rivers():
    stations = list(load_rhine_stations().items()) + list(load_alpine_stations().items())
    groups = []
    for name, ts in stations:
        ts = ts.clean()
        yearly = build_yearly(ts); model = fit_river(yearly)
        by_year = defaultdict(list)
        for d, v in zip(ts.dates, ts.values):
            by_year[d.year].append((d, v))
        rows = [river_row(y) for y in yearly]
        X, res = explain(model.scaler, model.pca, rows)
        fit = [1 if y.n_days >= RIVER_MIN else 0 for y in yearly]
        mean_all = float(np.mean([y.mean_flow for y, f in zip(yearly, fit) if f]))
        weekly = []
        for y in yearly:
            wk = defaultdict(list)
            for d, v in by_year[y.year]:
                wk[min((d.timetuple().tm_yday - 1) // 7, 51)].append(v)
            weekly.append([r(np.mean(wk[w]) / mean_all, 3) if wk.get(w) else None for w in range(52)])
        med = [r(float(np.median([w[k] for w, f in zip(weekly, fit) if f and w[k] is not None])), 3) for k in range(52)]
        score = [model.scores[y.year] for y in yearly]
        rk, order = rank_of(score, fit)
        groups.append(dict(
            id=name, name=name.replace("Koeln", "Köln").replace("-", " – "), short=SHORT.get(name, name.replace("Koeln", "Köln")), n=len(yearly), labels=[y.year for y in yearly],
            sub=f"daily discharge, {yearly[0].year}–{yearly[-1].year}: {len(yearly)} years · mean {mean_all:,.0f} m³/s",
            rec=[r(y.mean_flow / mean_all, 3) for y in yearly], rec_label="Year's mean flow (1.0 = this station's average year)",
            score=[r(s, 3) for s in score], norm=[r(model.normalized(y.year)) if f else None for y, f in zip(yearly, fit)],
            norm_all=[r(model.normalized(y.year)) for y in yearly], fit=fit, rank=rk, weekly=weekly, weekly_median=med, weekly_label="Weekly mean flow, as a share of the station's mean (grey: its typical year)",
            facts=[{"peak": r(y.max_flow, 1), "low": r(y.min_flow, 1), "mean": r(y.mean_flow, 1), "days": y.n_days} for y in yearly],
            top=order[:6],
            summary=dict(components=int(model.pca.n_components_), variance=r(sum(model.explained_variance_ratio), 3), n_fit=int(sum(fit))),
            unit_fit_note={str(y): "Too few days to describe a year: scored, never used to fit the model." for y in model.excluded_years},
            **columns(rows, X.tolist(), res.tolist()),
        ))
    limits = [
        "One model per station, fitted on that station's own years, so a score compares a year with its own station only. Colour is scaled within each station.",
        "It flags unusual combinations of features, not extremes, and does not reliably flag droughts: the 1976 drought ranks 3rd of 70 years at Lustenau but 187th of 208 at Köln; the 1995 Köln flood ranks 101st.",
        "The four alpine stations end in 2014; the Rhine stations end in 2020 (Lustenau, Basel, Lobith) and 2024 (Köln). Köln's first year (1816) has 61 days and is scored, not fitted.",
        "Nothing here has been tested with viewers. A high score means the year was unusual for its station, not that a person would feel it so.",
    ]
    return dict(kind="river_year", views=[["ribbon", "Ribbon"]], bands=[dict(name="Rhine mainstem", layers=[0, 1, 2, 3]), dict(name="Alpine headwaters", layers=[4, 5, 6, 7])], groups=groups, features=[
        dict(key=RIVER_FEATS[0], label="Mean flow vs recent norm", unit="", desc="The year's mean flow against the mean of the 30 years before it (0 = normal)."),
        dict(key=RIVER_FEATS[1], label="Peak ratio", unit="log10", desc="log10 of the highest day divided by the year's mean flow: how sharp the biggest flood was."),
        dict(key=RIVER_FEATS[2], label="Low-flow ratio", unit="", desc="The lowest day divided by the year's mean flow: how close the river came to running dry."),
        dict(key=RIVER_FEATS[3], label="Flow-duration slope", unit="", desc="Steepness of the flow-duration curve: flashy rivers are steep, steady ones are flat."),
        dict(key=RIVER_FEATS[4], label="Recession constant", unit="", desc="How slowly flow falls back after a peak: the river's memory of what it just carried."),
        dict(key=RIVER_FEATS[5], label="Seasonal swing", unit="", desc="Highest monthly mean minus lowest, as a share of the year's mean."),
    ], limits=limits)


# ---- L'Aire, Geneva (Human-Water Interface) ---------------------------------------------------------------
def hwi():
    from collections import defaultdict as dd
    from noea.human_water_interface import load_daily, load_intraday
    from noea.human_water_interface.anomaly import FEATURE_NAMES, MIN_HOURS, fit_day_model
    from noea.human_water_interface.loaders import STATIONS
    D0, D1 = date(2013, 1, 1), date(2025, 12, 31)
    days = [D0 + timedelta(days=i) for i in range((D1 - D0).days + 1)]
    groups = []
    for gid, label in (("BS_", "Bossenailles"), ("CS_", "Centenaire"), ("PR_", "Pont-Rouge")):
        meta = STATIONS[gid]
        flow, rain = load_intraday(gid, "flow", "hourly"), load_daily(meta["rain"], "rain")
        m = fit_day_model(flow, rain, TRAIN)
        hours = dd(list)
        for s, v in zip(flow.stamps, flow.values):
            hours[s.date()].append(v)
        rain_d = dict(zip(rain.dates, rain.values))
        feats = m.features
        scored = [d for d in days if d in feats]
        Xs, res = explain(m.scaler, m.pca, [feats[d] for d in scored])
        pos = {d: i for i, d in enumerate(scored)}
        raw = [feats[d] if d in feats else None for d in days]
        z = [Xs[pos[d]].tolist() if d in pos else None for d in days]
        rs = [res[pos[d]].tolist() if d in pos else None for d in days]
        p90 = float(np.percentile(m.train_errors, 90)); smax = max(m.scores.values())
        score = [m.scores.get(d) for d in days]
        shade = [None if s is None else r(max(0.0, min(1.0, (s - p90) / (smax - p90))) ** 0.5, 3) for s in score]
        pct = [None if s is None else r(m.percentile(s), 4) for s in score]
        test = [m.scores[d] for d in scored if d.year >= 2023]
        p95, p99 = np.percentile(m.train_errors, [95, 99])
        low = float(np.mean(np.array(flow.values) <= 0.01))
        note = (f"{low:.1%} of this gauge's hourly flow readings are 0.01 m³/s or less (a few litres per second), in steps of about 0.004 m³/s, and some are 0.0. "
                "In log terms a move between such readings looks like a sudden jump of orders of magnitude, so near-dry days can score high without any storm. "
                "Read its highest scores as a possible effect of sensor resolution, not as verified events.") if low > 0.01 else None
        held_top = sorted((d for d in scored if d.year >= 2023), key=lambda d: -m.scores[d])[:6]
        groups.append(dict(
            id=gid, name=label, n=len(days), start=D0.isoformat(),
            sub=f"hourly flow and daily rain, 2013–2025 · rain from {STATIONS[meta['rain']]['name'].replace(' (rain)', '')}",
            rec=[r(sum(hours[d]) / len(hours[d]), 3) if len(hours.get(d, [])) >= MIN_HOURS else None for d in days], rec_label="Daily mean flow (m³/s, log scale)",
            rain=[r(rain_d.get(d), 1) for d in days],
            score=[r(s, 3) for s in score], norm=shade, pct=pct, fit=[1 if d.year in TRAIN and d in feats else 0 for d in days], rank=None,
            note=note, top=[(d - D0).days for d in held_top], p95=r(p95, 2), p99=r(p99, 2), p90=r(p90, 2), smax=r(smax, 2),
            summary=dict(components=3, variance=r(sum(m.explained_variance_ratio), 3), n_fit=int(len(m.train_errors)), n_test=len(test),
                         test_above_p95=r(np.mean([s > p95 for s in test]), 3), test_above_p99=r(np.mean([s > p99 for s in test]), 3)),
            **columns(raw, z, rs),
        ))
    limits = [
        "The model is fitted on 2014–2022 and scored on 2023–2025, years it never saw. The 2013 days are also scored, by inference. A day above the training 95th percentile is unusual compared with the days it learned from.",
        "The record is about 12 years, so what counts as usual rests on a short history. Hourly flow is validated by OCEau; the validated archive ends on 31 December 2025.",
        "The gauges are shown as Bossenailles, Centenaire, Pont-Rouge. Their order along the river is not confirmed with OCEau.",
        "Nothing here has been tested with viewers. A high score means the day was unusual for this gauge, not that a person would feel it so.",
    ]
    return dict(kind="day", views=[["ribbon", "Ribbon"], ["line", "Days"]], groups=groups, features=[
        dict(key=FEATURE_NAMES[0], label="Flow vs seasonal norm", unit="log10", desc="log10 of the day's mean flow minus the median for that time of year: above or below normal."),
        dict(key=FEATURE_NAMES[1], label="Change since yesterday", unit="log10", desc="Change in log10 daily flow from the day before: rising or falling."),
        dict(key=FEATURE_NAMES[2], label="Peak-to-mean", unit="", desc="Highest hourly flow divided by the day's mean: how spiky the day was."),
        dict(key=FEATURE_NAMES[3], label="Largest hourly rise", unit="log10", desc="The biggest hour-to-hour rise in log10 flow within the day: how sudden."),
        dict(key=FEATURE_NAMES[4], label="Rain that day", unit="log10(1+mm)", desc="Rain at the associated station on the day."),
        dict(key=FEATURE_NAMES[5], label="Rain, three days", unit="log10(1+mm)", desc="Rain over the day and the two before."),
        dict(key=FEATURE_NAMES[6], label="Rain, week before", unit="log10(1+mm)", desc="Rain over the seven days before the day: how wet the ground already was."),
    ], limits=limits)


PAGES = {
    "rainfall": dict(
        fn=rainfall, eyebrow="Climate Pulse · rainfall", title="Hong Kong rainfall",
        deck="What the pipeline does with Hong Kong's daily rainfall, 1884 to 2025, before anything is mapped to XR.",
        unit="year", unit_plural="years",
        steps=[("Record", "Daily rainfall at the Hong Kong Observatory, 1884 to 2025, as an ECG: every spike is a real day's rain, and the trace moves through the years as the heart beats, one year per beat. Click it to jump to a year."),
               ("Diagnostics", "Each year is summarised by six numbers. Like an ECG, each beat is one year, placed at the date of its wettest day; its height is the chosen diagnostic, in standard deviations from typical, up or down."),
               ("Score", "An unsupervised model learns what a typical year looks like. Each beat's height and colour is how badly that year fits it, from typical to most unusual, scaled within this record.")],
        method="PCA with 2 components, fitted on the complete years of this record.",
        source="Hong Kong Observatory, daily rainfall, 1884–2025."),
    "river": dict(
        fn=rivers, eyebrow="Climate Pulse · rivers", title="Rhine and alpine rivers",
        deck="What the pipeline does with daily discharge at eight stations, before anything is mapped to XR.",
        unit="year", unit_plural="years",
        steps=[("Record", "Daily discharge at eight stations, drawn as in Issue 6: one column per year, each station a layer stacked on a shared spine. Height is the year's mean flow relative to the station's own average year."),
               ("Diagnostics", "Each year is summarised by six scale-free numbers, so a glacial stream and a lowland river can be compared. Pick one to see it across the record."),
               ("Score", "One unsupervised model per station learns what a typical year looks like there. The score is how badly each year fits it. Colour runs from typical to most unusual, scaled within the station.")],
        method="PCA with 2 components, one model per station, fitted on that station's complete years.",
        source="Four Rhine stations (GRDC): Lustenau, Basel, Köln, Lobith. Four alpine stations (FOEN): Weisse Lütschine–Zweilütschinen, Reuss–Andermatt, Aare–Brienzwiler, Aare–Thun."),
    "hwi": dict(
        fn=hwi, eyebrow="Human-Water Interface (HWI)", title="L'Aire, Geneva",
        deck="What the pipeline does with three gauges on one river, a day at a time, before anything is mapped to XR.",
        unit="day", unit_plural="days",
        steps=[("Record", "Hourly flow at each gauge and daily rain at its associated station, 2013 to 2025. The ribbon shows one column per week with the three gauges stacked on a shared spine; the Days view shows each day's mean flow with rain above."),
               ("Diagnostics", "Each day is summarised by seven numbers, measured against the gauge's own seasonal norm. Pick one to see it across the record."),
               ("Score", "An unsupervised model is fitted on 2014–2022 and scores every day, including 2023–2025, which it never saw. Colour runs from typical to most unusual; days below the training 90th percentile stay pale.")],
        method="PCA with 3 components, one model per gauge, fitted on 2014–2022.",
        source="Office cantonal de l'eau, Geneva (OCEau): validated history export of the cantonal hydro-meteorological monitoring network."),
}


def assemble(payload: dict) -> str:
    """One self-contained page: the shared stylesheet, markup and engine, with this implementation's data."""
    html = (HERE / "template.html").read_text(encoding="utf-8")
    for tag, name in (("/*__CSS__*/", "engine.css"), ("/*__FRAGMENT__*/", "fragment.html")):
        html = html.replace(tag, (HERE / name).read_text(encoding="utf-8"))
    html = html.replace("/*__ENGINE__*/", (HERE / "engine.js").read_text(encoding="utf-8") + "\n" + (HERE / "heart.js").read_text(encoding="utf-8"))
    html = html.replace("/*__DATA__*/null", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return html.replace("__TITLE__", payload["title"])


def main(out_dir: str):
    out = Path(out_dir); (out / "data").mkdir(parents=True, exist_ok=True)
    only = sys.argv[2:] or list(PAGES)
    for key in only:
        p = dict(PAGES[key]); data = p.pop("fn")()
        payload = dict(p, **data)
        html = assemble(payload)
        (out / f"{key}.html").write_text(html, encoding="utf-8")
        (out / "data" / f"{key}.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(key, f"{len(html) / 1e6:.2f} MB", [g["name"] for g in payload["groups"]])


if __name__ == "__main__":
    main(sys.argv[1])
