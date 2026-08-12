"""
Noéa pipeline — end-to-end demo.

Run:  python demo.py

It generates a synthetic Léman-like record, builds the diagnostic profile,
maps every day to XR parameters, and writes them to xr_output.json.
Then it prints a few sample days — including a drought day — so you can
see the parameters respond.
"""

import json
from datetime import date

from noea import build_profile, map_series
from noea.synthetic import make_leman_like


def main():
    # 1. get data (swap this line for a real loader later)
    discharge_ts, temperature_ts = make_leman_like()
    print(f"Loaded {len(discharge_ts)} days for {discharge_ts.station_id}\n")

    # 2. scientific layer — the station's fingerprint
    profile = build_profile(discharge_ts)
    print("DIAGNOSTIC PROFILE")
    print(" ", profile.summary())
    print(f"  recession k : {profile.recession_k:.3f}  "
          f"(1.0 = holds water, low = flashy)")
    print(f"  FDC slope   : {profile.fdc_slope:.3f}  "
          f"(steep = reactive)")
    print(f"  Q10/Q50/Q90 : {profile.q10:.0f} / {profile.q50:.0f} / {profile.q90:.0f} m3/s")
    print()

    # 3. mapping layer — every day becomes XR parameters
    params = map_series(profile, discharge_ts, temperature_ts)

    # 4. serve — write JSON (this is what the API/endpoint will hand out)
    payload = [p.as_dict() for p in params]
    with open("xr_output.json", "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {len(payload)} XR parameter frames to xr_output.json\n")

    # 5. show a few illustrative days
    def show(label: str, target: date):
        match = min(params, key=lambda p: abs((p.timestamp - target).days))
        d = match.as_dict()
        print(f"{label}  ({d['timestamp']})")
        print(f"   diameter {d['diameter']:.2f}  "
              f"arousal {d['arousal']:.2f}  "
              f"rhythm {d['pulse_rhythm']:.2f}  "
              f"valence {d['valence']:+.2f}  "
              f"lumin {d['luminosity']:.2f}")

    print("SAMPLE DAYS")
    show("Winter low  ", date(2001, 1, 15))
    show("Summer melt ", date(2001, 7, 20))
    show("Drought year", date(2012, 8, 1))   # the suppressed year
    print()
    print("Notice: the drought day should show low diameter and negative valence.")


if __name__ == "__main__":
    main()
