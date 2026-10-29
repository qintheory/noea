"""
Noéa river pipeline — end-to-end demo, real GRDC/FOEN discharge data.

Run:  python3 demo_climate_pulse_river.py

Loads all eight real stations Issue 6 names (four Rhine mainstem: Lustenau,
Basel, Koeln, Lobith; four alpine headwaters: Weisse Luetschine, Reuss,
Aare-Brienzwiler, Aare-Thun), builds a diagnostic profile for each with the
existing, unchanged frameworks.py, and prints them side by side — the
"four organs" comparison from Issue 6, in table form. Then maps Lustenau's
daily record to XR parameters and writes xr_output.json, same as before.

Every station goes through the identical build_profile()/map_series() this
repo has used since the synthetic-data prototype — nothing about the
pipeline itself changed, only the data feeding it.
"""
import json

from noea.climate_pulse.river import (
    build_profile, build_yearly, fit_regime_model, year_vectors,
    load_alpine_stations, load_rhine_stations, map_series,
)


def print_comparison(label, stations):
    print(label)
    print(f"  {'station':<32}{'years':>7}{'mean':>10}{'Q10':>10}{'Q50':>10}"
          f"{'Q90':>10}{'fdc_slope':>11}{'recession_k':>13}")
    for name, ts in stations.items():
        profile = build_profile(ts)
        n_years = ts.dates[-1].year - ts.dates[0].year + 1
        print(f"  {name:<32}{n_years:>7}{profile.mean_flow:>10.1f}{profile.q10:>10.1f}"
              f"{profile.q50:>10.1f}{profile.q90:>10.1f}{profile.fdc_slope:>11.3f}"
              f"{profile.recession_k:>13.3f}")
    print()


def print_year_model(label, stations):
    """The learned component: one regime model per station, fit on its own years against its own typical year."""
    print(label)
    print(f"  {'station':<32}{'fit yrs':>8}{'variance':>10}   most unusual years (what departed most)")
    for name, ts in stations.items():
        model = fit_regime_model(year_vectors(ts), name)
        top = sorted(model.unusual, key=lambda y: (-model.unusual[y], y))[:3]
        print(f"  {name:<32}{model.n_fit:>8}{model.explained:>10.0%}   "
              + ", ".join(f"{yr} ({model.why(yr)[0]} {model.why(yr)[3]:+.1f} sd)" for yr in top))
    print()


def print_trend(stations):
    """The trend-aware baseline: mean deviation from the trailing 30-year norm."""
    decades = (1980, 1990, 2000, 2010, 2020)
    print("TREND-AWARE BASELINE — mean deviation from trailing 30-yr norm, by decade")
    print(f"  {'station':<12}" + "".join(f"{d}s".rjust(8) for d in decades))
    for name, ts in stations.items():
        years = build_yearly(ts)
        cells = []
        for d in decades:
            v = [y.deviation_from_norm for y in years if d <= y.year < d + 10]
            cells.append(f"{sum(v) / len(v):+.2f}".rjust(8) if v else "-".rjust(8))
        print(f"  {name:<12}" + "".join(cells))
    print("  (2020s = 2020 only for Lustenau/Basel/Lobith; their data ends Dec 2020)\n")


def main():
    rhine = load_rhine_stations()
    alpine = load_alpine_stations()

    print_comparison("RHINE MAINSTEM (m3/s) — the lowland/alpine transition", rhine)
    print_comparison("ALPINE HEADWATERS (m3/s) — where the body begins", alpine)

    print_year_model("YEAR-LEVEL MODEL — probabilistic PCA against each station's typical year, one per station", {**rhine, **alpine})
    print_trend(rhine)

    # daily XR mapping, now with each day given the context of its year
    lustenau = rhine["Lustenau"]
    profile = build_profile(lustenau)
    yearly = build_yearly(lustenau)
    params = map_series(profile, lustenau, yearly=yearly, anomaly=fit_regime_model(year_vectors(lustenau), "Lustenau"))
    payload = [p.as_dict() for p in params]
    with open("xr_output.json", "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {len(payload)} XR parameter frames for Lustenau to xr_output.json")


if __name__ == "__main__":
    main()
