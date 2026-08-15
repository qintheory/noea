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
    build_profile, load_alpine_stations, load_rhine_stations, map_series,
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


def main():
    rhine = load_rhine_stations()
    alpine = load_alpine_stations()

    print_comparison("RHINE MAINSTEM (m3/s) — the lowland/alpine transition", rhine)
    print_comparison("ALPINE HEADWATERS (m3/s) — where the body begins", alpine)

    # daily XR mapping, same shape as the original synthetic demo
    lustenau = rhine["Lustenau"]
    profile = build_profile(lustenau)
    params = map_series(profile, lustenau)
    payload = [p.as_dict() for p in params]
    with open("xr_output.json", "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {len(payload)} XR parameter frames for Lustenau to xr_output.json")


if __name__ == "__main__":
    main()
