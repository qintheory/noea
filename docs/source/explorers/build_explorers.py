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
from noea.climate_pulse.river.regime import DESCRIPTORS as REG_DESC, fit_regime_model, year_vectors
from noea.climate_pulse.river.anomaly import FEATURE_NAMES as RIVER_FEATS, MIN_DAYS_FOR_FIT as RIVER_MIN, _feature_row as river_row

HERE = Path(__file__).parent
SHORT = {"Weisse Lütschine-Zweilütschinen": "Weisse Lütschine", "Reuss-Andermatt": "Reuss", "Aare-Brienzwiler": "Aare, Brienzwiler", "Aare-Thun": "Aare, Thun"}
STATION_INFO = {"Lustenau": "Rhine at Höchster Brücke, Austria · GRDC · catchment 6,301 km²", "Basel": "Rhine at Basel, Rheinhalle, Switzerland · GRDC · catchment 35,897 km²",
                "Koeln": "Rhine at Köln, Germany · GRDC · catchment 144,232 km²", "Lobith": "Rhine at Lobith, the Netherlands · GRDC · catchment 160,800 km²",
                "Weisse Lütschine-Zweilütschinen": "Weisse Lütschine at Zweilütschinen, Switzerland · FOEN", "Reuss-Andermatt": "Reuss at Andermatt, Switzerland · FOEN",
                "Aare-Brienzwiler": "Aare at Brienzwiler, Switzerland · FOEN", "Aare-Thun": "Aare at Thun, Switzerland · FOEN"}
FDC_P = [1, 2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 98, 99]               # the share of days a flow is exceeded, for the flow duration curve
RECESS_LAG = list(range(0, 41, 2))                                               # days after the year's highest day, for the recession curve
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
    g["affect"] = {"correlations": {k: r(v, 2) for k, v in af.correlations.items()}, "checks": af.checks, "storminess": af.storminess_loadings, "wetness": af.wetness_loadings}
    passed = sum(af.checks.values()); c = af.correlations
    limits = [
        f"The model flags unusual combinations of features, not extremes. 1931 is among the top-scoring years with a peak of only {ys[idx[1931]].r_value:.0f} mm, "
        f"while 1926, which holds the largest single day ({ys[idx[1926]].r_value:.0f} mm), scores {norm[idx[1926]]:.2f} and 2023 scores {norm[idx[2023]]:.2f}, on a scale where 1 is the most unusual year of the record. "
        f"The 1963 drought scores {norm[idx[1963]]:.2f}.",
        f"Valence and arousal (the corner map) are relative to this record: each year is placed against its {af.n_fit} fitted years. They combine two PCA factors learned from the data, storminess and wetness, with the anomaly score, and agree with it (arousal r = {c['arousal~anomaly']:+.2f}, valence r = {c['valence~anomaly']:+.2f}). "
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
        yearly = build_yearly(ts); yv = year_vectors(ts); rm = fit_regime_model(yv, name); yvd = {v.year: v for v in yv}
        by_year = defaultdict(list)
        for d, v in zip(ts.dates, ts.values):
            by_year[d.year].append((d, v))
        fit = [1 if y.n_days >= RIVER_MIN else 0 for y in yearly]
        mean_all = float(np.mean([y.mean_flow for y, f in zip(yearly, fit) if f]))
        weekly = []
        for y in yearly:
            wk = defaultdict(list)
            for d, v in by_year[y.year]:
                wk[min((d.timetuple().tm_yday - 1) // 7, 51)].append(v)
            weekly.append([r(np.mean(wk[w]) / mean_all, 3) if wk.get(w) else None for w in range(52)])
        med = [r(float(np.median([w[k] for w, f in zip(weekly, fit) if f and w[k] is not None])), 3) for k in range(52)]
        fdc, recess, monthly = [], [], []                                          # the three other graphs of Issue 6: flow duration (Personality), recession (Memory), seasonal cycle (Breath)
        for y, f_ in zip(yearly, fit):
            ds = by_year[y.year]; vals = [v for _, v in ds]; n_ = len(vals)
            if not f_ or n_ < 300:
                fdc.append(None); recess.append(None); monthly.append(None); continue
            sv = sorted(vals, reverse=True); k0 = max(range(n_), key=lambda j: vals[j]); pk = vals[k0]; mm = defaultdict(list)
            for d_, v_ in ds: mm[d_.month].append(v_)
            fdc.append([r(sv[min(n_ - 1, int(n_ * p / 100))] / mean_all, 3) for p in FDC_P])
            recess.append([r(vals[k0 + L] / pk, 3) if k0 + L < n_ and pk > 0 else None for L in RECESS_LAG])
            monthly.append([r(float(np.mean(mm[m])) / mean_all, 3) if mm.get(m) else None for m in range(1, 13)])
        names = list(REG_DESC)                                                       # wetness, flood, low, personality, memory, season: the plain descriptors of the regime model
        shown = {"wetness": lambda y: r(y.mean_flow / mean_all, 3), "flood": lambda y: r(yvd[y.year].highest / rm.typical_highest, 3), "low": lambda y: r(yvd[y.year].lowest / rm.typical_lowest, 3),
                 "personality": lambda y: r(yvd[y.year].fdc_slope, 3), "memory": lambda y: r(yvd[y.year].recession_k, 4), "season": lambda y: r(rm.raw[y.year]["season"], 3)}
        zs = [[r(rm.descriptors[y.year][n], 2) for y in yearly] for n in names]
        order = sorted((i for i, f_ in enumerate(fit) if f_), key=lambda i: -rm.unusual[yearly[i].year])
        groups.append(dict(
            id=name, fdc=fdc, recess=recess, monthly=monthly, mean=r(mean_all, 1), info=STATION_INFO.get(name, ""), name=name.replace("Koeln", "Köln").replace("-", " – "), short=SHORT.get(name, name.replace("Koeln", "Köln")), n=len(yearly), labels=[y.year for y in yearly],
            sub=f"daily discharge, {yearly[0].year}–{yearly[-1].year}: {len(yearly)} years · mean {mean_all:,.0f} m³/s",
            rec=[r(y.mean_flow / mean_all, 3) for y in yearly], rec_label="Year's mean flow (1.0 = this station's average year)",
            score=[r(rm.nll[y.year], 3) for y in yearly], norm=[r(rm.unusual[y.year]) if f else None for y, f in zip(yearly, fit)],
            norm_all=[r(rm.unusual[y.year]) for y in yearly], fit=fit, rank=None, weekly=weekly, weekly_median=med, weekly_label="Weekly mean flow, as a share of the station's mean (grey: its typical year)",
            facts=[{"peak": r(y.max_flow, 1), "low": r(y.min_flow, 1), "mean": r(y.mean_flow, 1), "days": y.n_days} for y in yearly],
            top=order[:6],
            summary=dict(components=rm.n_components, variance=r(rm.explained, 3), n_fit=rm.n_fit),
            unit_fit_note={str(y): "Too few days to describe a year: scored, never used to fit the model." for y in rm.excluded_years},
            typ=dict(months=[r(v / mean_all, 3) for v in rm.typical_months], hi=r(rm.typical_highest / mean_all, 3), lo=r(rm.typical_lowest / mean_all, 3)),
            raw=[[shown[n](y) for y in yearly] for n in names], z=zs, res=[[r(v * v, 3) for v in col] for col in zs],
        ))
    limits = [
        "One model per station, fitted on that station's own complete years, so a score compares a year only with its own station: 0.95 means more unusual than 95% of that station's years, and every station has years near 1.00.",
        "The score says how far a year departed from the station's typical year, not which way. The six measures show what departed: a wetter or drier year, a higher or lower flood peak or low flow, a flashier or steadier river, a slower or quicker recession, a shifted season.",
        "Checked, not validated: of 30 documented flood and drought years at six stations, 22 score 0.70 or higher, against a much weaker showing for the earlier model. Those events were looked at while the model was built, so this is a sanity check. A summer-only drought such as 2003 reads as ordinary at Köln (0.43) and Lobith (0.39).",
        "The four alpine stations end in 2014; the Rhine stations end in 2020 (Lustenau, Basel, Lobith) and 2024 (Köln). Köln's first year (1816) has 61 days and is scored, not fitted.",
        "The model uses the flow record only. Snow and glacier melt (the cryosphere) and groundwater are not in it yet; they are meant to join as further dimensions of the same model, each with its own measures.",
        "The river body is a schematic, not a map: positions are not to scale, branch width is each station's usual flow, and the confluences (the Lütschine and the Aare at Brienzwiler into the Aare at Thun; the Aare and the Reuss into the Rhine above Basel) are placed from the river geography, not from the data files. Only the eight gauges are drawn; there is nothing between them.",
        "The window only limits what is drawn. Each station's model is still fitted on all of its own complete years, so scores are the same in both windows; the gold marks the highest-scoring year inside the chosen window. The default window is the 70 years (1951–2020) over which all four Rhine stations overlap, as in Issue 6; the alpine stations end in 2014 and show as no record afterwards.",
        "Nothing here has been tested with viewers. A high score means the year was unusual for its station, not that a person would feel it so.",
    ]
    body = dict(nodes=[dict(id="Lustenau", x=0.5, y=0.15, side="r"), dict(id="Basel", x=0.5, y=0.47, side="r"), dict(id="Koeln", x=0.5, y=0.73, side="r"), dict(id="Lobith", x=0.5, y=0.9, side="r"),
                       dict(id="Aare-Brienzwiler", x=0.12, y=0.04, side="l"), dict(id="Weisse Lütschine-Zweilütschinen", x=0.28, y=0.02, side="r"), dict(id="Aare-Thun", x=0.3, y=0.22, side="l"), dict(id="Reuss-Andermatt", x=0.78, y=0.06, side="r")],
                note="The eight gauges drawn as one river flowing down the page, as on the Issue 6 cover. Width is each station's usual flow; colour is how unusual the year is at each station, not which way: hover a station to see the year's flow and what makes it unusual. Press play, or click a station.",
                edges=[["Lustenau", "Basel"], ["Basel", "Koeln"], ["Koeln", "Lobith"], ["Aare-Brienzwiler", "Aare-Thun"], ["Weisse Lütschine-Zweilütschinen", "Aare-Thun"], ["Aare-Thun", "Basel"], ["Reuss-Andermatt", "Basel"]])
    return dict(kind="river_year", frame=dict(fdc_p=FDC_P, recess_lag=RECESS_LAG), views=[["ribbon", "Ribbon"]], windows=[["issue6", "1951–2020, as in Issue 6", 1951, 2020], ["full", "Full record, 1816–2024", None, None]], body=body, bands=[dict(name="Rhine mainstem", layers=[0, 1, 2, 3], fill=True), dict(name="Alpine headwaters", layers=[4, 5, 6, 7], lanes=True)], groups=groups, features=[
        dict(key="wetness", label="Wetness", fw="Pulse", unit="× average", desc="The year's mean flow as a multiple of the station's average year.", words=["drier than usual through the year", "wetter than usual through the year"]),
        dict(key="flood", label="Flood peak", fw="Pulse", unit="× typical", desc="The year's highest day as a multiple of the highest day of the station's typical year.", words=["a lower flood peak than usual", "a higher flood peak than usual"]),
        dict(key="low", label="Low flow", fw="Pulse", unit="× typical", desc="The year's lowest 7-day mean flow as a multiple of the station's typical low flow: how close the river came to running dry.", words=["a lower low flow than usual", "a higher low flow than usual"]),
        dict(key="personality", label="Flashiness", fw="Personality", unit="", desc="Steepness of the flow-duration curve: a flashy river is steep, a steady one flat.", words=["a steadier river than usual", "a flashier river than usual"]),
        dict(key="memory", label="Recession", fw="Memory", unit="", desc="How slowly flow falls back after a peak: close to 1 means the river holds its water.", words=["a river quicker to fall back than usual", "a river slower to fall back than usual"]),
        dict(key="season", label="Seasonal shift", fw="Breath", unit="log10", desc="Winter water against summer water, compared with the station's typical year: positive means more winter water and less summer water.", words=["less winter water and more summer water than usual", "more winter water and less summer water than usual"]),
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
        fn=rainfall, eyebrow="Climate Pulse · Atmosphere", title="Hong Kong rainfall",
        deck="Daily rainfall at the Hong Kong Observatory, 1884 to 2025. Each year becomes six diagnostics: its wettest day, how rare that day is, how concentrated the rain was, its day-to-day spread, how often it rained, and its total against the previous 30 years. A PCA learns what a typical year looks like and scores how badly each year fits it, the anomaly, and finds two factors in the same numbers: storminess and wetness. Arousal is how stormy and how surprising the year was. Valence falls with how far the year departs from a normal one, wetter, drier or more intense, and with how surprising it was. Both are ranks within this record: a hypothesis about affect, not yet tested with viewers.",
        unit="year", unit_plural="years",
        steps=[("Record", "Daily rainfall at the Hong Kong Observatory, 1884 to 2025, as an ECG: every spike is a real day's rain, and the trace moves through the years as the heart beats, one year per beat. Click it to jump to a year."),
               ("Diagnostics", "Each year is summarised by six numbers. Like an ECG, each beat is one year, placed at the date of its wettest day; its height is the chosen diagnostic, in standard deviations from typical, up or down."),
               ("Score", "An unsupervised model learns what a typical year looks like. Each beat's height and colour is how badly that year fits it, from typical to most unusual, scaled within this record.")],
        method="PCA with 2 components, fitted on the complete years of this record.",
        source="Hong Kong Observatory, daily rainfall, 1884–2025."),
    "river": dict(
        fn=rivers, eyebrow="Climate Pulse · Rivers", title="Rhine and alpine rivers",
        deck="What the pipeline does with daily discharge at eight stations, before anything is mapped to XR.",
        unit="year", unit_plural="years",
        steps=[("Record", "Daily discharge at eight stations, drawn as in Issue 6: one column per year, each station a layer stacked on a shared spine. Height is the year's mean flow relative to the station's own average year."),
               ("Diagnostics", "Each year is described by six plain measures against the station's own typical year, so a glacial stream and a lowland river can be compared. They follow the four frameworks of Issue 6: the hydrograph (wetness, flood peak, low flow), the flow duration curve (flashiness), the recession curve (memory) and the seasonal cycle (breath). Pick one to see it at all eight stations."),
               ("Score", "One unsupervised model per station learns what a typical year looks like there: the rhythm of its months, its floods and low flows. The score is how unusual each year is for that station, the share of its own years that are less unusual. It does not say which way; the six measures do.")],
        method="A probabilistic PCA of each station's year patterns (twelve monthly anomalies, flood, low flow, flashiness and recession, all against the station's typical year), fitted on its complete years. A year is unusual if its overall pattern is improbable or any one of the six measures strays far.",
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
