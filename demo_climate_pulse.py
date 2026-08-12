"""
Climate Pulse — end-to-end demo, real HKO data, clustered moods.

Run:  python3 demo_climate_pulse.py

Loads Hong Kong's daily rainfall record (HKO, 1884-2025), builds the
climate diagnostic profile (R/RR/S/deviation/return-period per year), fits
year archetypes via k-means, proposes a mood per archetype, and maps every
year to XR parameters using those clustered moods. Writes the frames to
climate_pulse_output.json.

The cluster report below is the "supervise" step: check whether years you
recognise landed where you'd expect before trusting the proposed moods.
"""
import json

from climate_pulse import (
    build_profile, load_rainfall, map_series,
    fit_clusters, suggest_k, cluster_members, propose_moods,
)

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

    # --- fit: pick k by silhouette score, then cluster the years ---
    scores = suggest_k(profile)
    best_k = max(scores, key=scores.get)
    print("SILHOUETTE SCORES BY k")
    for k, s in scores.items():
        flag = "  <- best" if k == best_k else ""
        print(f"  k={k}: {s:.3f}{flag}")
    print()

    model = fit_clusters(profile, k=best_k)
    members = cluster_members(model)
    moods = propose_moods(model, profile)

    print(f"CLUSTERS (k={model.k}, silhouette={model.silhouette:.3f})")
    for c in range(model.k):
        years = members[c]
        v, a = moods[c]
        centroid = model.centroids_raw[c]
        flagged = [f"{y} ({KNOWN_YEARS[y]})" for y in years if y in KNOWN_YEARS]
        print(f"  cluster {c}  n={len(years)}  proposed valence={v:+.2f} arousal={a:.2f}")
        print(f"    centroid: R={centroid['r_value']:.0f}mm  dev={centroid['deviation_from_norm']:+.2f}  "
              f"stdev={centroid['stdev']:.1f}  return_period={centroid['return_period']:.1f}y")
        if flagged:
            print(f"    known years here: {', '.join(flagged)}")
    print()

    # --- classify: every year gets its cluster's proposed mood ---
    params = map_series(profile, cluster_labels=model.labels, cluster_moods=moods)
    payload = [p.as_dict() for p in params]
    with open("climate_pulse_output.json", "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {len(payload)} XR parameter frames to climate_pulse_output.json\n")

    print("KNOWN YEARS, CLUSTERED READING")
    for year, label in KNOWN_YEARS.items():
        yp = next((y for y in profile.years if y.year == year), None)
        if yp is None:
            continue
        d = next(p for p in params if p.timestamp == yp.r_date).as_dict()
        print(f"{year} — {label}  (cluster {model.labels[year]})")
        print(f"   diameter {d['diameter']:.2f}  arousal {d['arousal']:.2f}  "
              f"rhythm {d['pulse_rhythm']:.2f}  valence {d['valence']:+.2f}")


if __name__ == "__main__":
    main()
