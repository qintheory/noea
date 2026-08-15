"""
Climate Pulse — end-to-end demo, real HKO data.

Run:  python3 demo_climate_pulse_rainfall.py

Loads Hong Kong's daily rainfall record (HKO, 1884-2025), builds the
climate diagnostic profile (R/RR/S/deviation/return-period/peak-
concentration per year), fits the PCA anomaly model on the full record,
maps every year to XR parameters, and writes the frames to
climate_pulse_output.json.

No clustering — the anomaly score comes from a fitted unsupervised model
(anomaly.py) scored per year individually, never averaged into a group
(see mapping.py for why the earlier archetype/clustering approach was
dropped).
"""
import json

from noea.climate_pulse.rainfall import build_profile, fit_anomaly_model, load_rainfall, map_series

KNOWN_YEARS = {
    1926: "single overwhelming pulse (Issue 4)",
    1963: "the great HK drought",
    2023: "record Sept storm, ~500yr event by press reporting",
    2025: "partial year — data cuts off Jan 31, ignore its reading",
}


def main():
    ts = load_rainfall()
    print(f"Loaded {len(ts)} days for {ts.station_id} "
          f"({ts.dates[0]} to {ts.dates[-1]})\n")

    profile = build_profile(ts)
    print(f"DIAGNOSTIC PROFILE — {len(profile.years)} years on record")
    print(f"  R range  : {profile.r_min:.1f} - {profile.r_max:.1f} mm")
    print(f"  RR range : {profile.rr_min:.0f} - {profile.rr_max:.0f} days")
    print()

    anomaly = fit_anomaly_model(profile)
    print(f"ANOMALY MODEL — PCA, {anomaly.pca.n_components_} components, "
          f"explained variance {sum(anomaly.explained_variance_ratio):.1%}")
    print()

    params = map_series(profile)
    payload = [p.as_dict() for p in params]
    with open("climate_pulse_output.json", "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {len(payload)} XR parameter frames to climate_pulse_output.json\n")

    print("KNOWN YEARS")
    for year, label in KNOWN_YEARS.items():
        yp = next((y for y in profile.years if y.year == year), None)
        if yp is None:
            continue
        d = next(p for p in params if p.timestamp == yp.r_date).as_dict()
        print(f"{year} — {label}")
        print(f"   R={yp.r_value:.1f}mm  dev={yp.deviation_from_norm:+.2f}  "
              f"return_period(fitted)={yp.return_period_fitted:.1f}y  "
              f"concentration={yp.peak_concentration:.2f}  "
              f"anomaly={anomaly.normalized(year):.2f}")
        print(f"   diameter {d['diameter']:.2f}  arousal {d['arousal']:.2f}  "
              f"rhythm {d['pulse_rhythm']:.2f}  valence {d['valence']:+.2f}")


if __name__ == "__main__":
    main()
