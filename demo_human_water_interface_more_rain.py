"""
Human-Water Interface: does more rain data help? The Aire day model with and without the whole rain network.

Run (after python3 -m noea.human_water_interface.fetch, and hourly rain for BA_ and DD_):
      python3 demo_human_water_interface_more_rain.py

Baseline: seven features, one rain station per gauge. Extended: three more, built from all 15 rain stations of the
network (area mean, wettest station) and from the associated station's hourly rain (peak hour). Both are fitted on
2014-2022 and tested on 2023-2025. There is no label to optimise against; the checks are fixed in advance: the
held-out calibration, and where the documented storm of 9 June 2024 ranks among the held-out days.
"""
from datetime import date

import numpy as np

from noea.human_water_interface import RAIN_STATIONS, STATIONS, load_daily, load_intraday
from noea.human_water_interface.anomaly import EXTRA_FEATURE_NAMES, FEATURE_NAMES, fit_day_model

TRAIN = list(range(2014, 2023))
STORM = date(2024, 6, 9)


def main():
    area = {r: load_daily(r, "rain") for r in RAIN_STATIONS}
    print(f"{len(area)} rain stations: {', '.join(RAIN_STATIONS)}\n")
    for g in ("BS_", "CS_", "PR_"):
        meta = STATIONS[g]
        flow, rain, hourly = load_intraday(g, "flow", "hourly"), load_daily(meta["rain"], "rain"), load_intraday(meta["rain"], "rain", "hourly")
        print(f"{g} {meta['name']} (associated rain: {meta['rain']})")
        for label, kw in (("baseline (7 features)", {}), ("extended (10 features)", dict(area_rain=area, hourly_rain=hourly))):
            m = fit_day_model(flow, rain, TRAIN, **kw)
            test = {d: s for d, s in m.scores.items() if d.year >= 2023}
            order = sorted(test, key=test.get, reverse=True)
            p95, p99 = np.percentile(m.train_errors, [95, 99])
            print(f"  {label:24s} variance kept {sum(m.explained_variance_ratio):.0%} | held-out above train p95 {np.mean([s > p95 for s in test.values()]):.1%}, p99 {np.mean([s > p99 for s in test.values()]):.1%} "
                  f"| 9 June 2024 ranks {order.index(STORM) + 1} of {len(test)}")
        names = FEATURE_NAMES + EXTRA_FEATURE_NAMES
        print("  extended, strongest loadings on the first component:",
              ", ".join(f"{n} {c:+.2f}" for n, c in sorted(zip(names, m.pca.components_[0]), key=lambda t: -abs(t[1]))[:4]))


if __name__ == "__main__":
    main()
