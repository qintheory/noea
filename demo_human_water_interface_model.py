"""
Human-Water Interface: a day-level anomaly model for L'Aire at Pont-Rouge, with a held-out test.

Run:  python3 -m noea.human_water_interface.fetch                          # daily history, once
      python3 -m noea.human_water_interface.fetch PR_ flow hourly 2014 2025   # hourly flow, once
      python3 demo_human_water_interface_model.py

Fits on 2014-2022 and scores 2023-2025, which the model has never seen. Climate Pulse could not do this
(its models are fitted on the whole record); an HWI record is short, but daily rows make it possible.
"""
import numpy as np

from noea.human_water_interface import load_daily, load_intraday
from noea.human_water_interface.anomaly import FEATURE_NAMES, fit_day_model
from noea.human_water_interface.quality import check

TRAIN = list(range(2014, 2023))


def main():
    flow_h = load_intraday("PR_", "flow", "hourly")
    flow_d = load_daily("PR_", "flow")
    rain = load_daily("BA_", "rain")

    print("Quality control (reported, nothing removed except negatives, of which there are none)")
    for name, s in (("flow, daily", flow_d), ("flow, hourly", flow_h), ("rain, daily", rain)):
        c = check(s)
        print(f"  {name:13s} n={c['n']:6d} negative={c['negative']} longest identical run={c['longest_identical_run']}")

    m = fit_day_model(flow_h, rain, TRAIN)
    print(f"\nModel: PCA, 3 components, {len(m.train_errors)} training days (2014-2022), "
          f"variance kept {sum(m.explained_variance_ratio):.0%}")
    print("Features:", ", ".join(FEATURE_NAMES))

    p95, p99 = np.percentile(m.train_errors, [95, 99])
    test = {d: s for d, s in m.scores.items() if d.year >= 2023}
    print(f"\nHeld-out 2023-2025 ({len(test)} days): {np.mean([s > p95 for s in test.values()]):.1%} above the training 95th "
          f"percentile (5% expected if nothing changed), {np.mean([s > p99 for s in test.values()]):.1%} above the 99th (1%)")

    qd, rd = dict(zip(flow_d.dates, flow_d.values)), dict(zip(rain.dates, rain.values))
    print("\nHighest-scoring held-out days:")
    for d, s in sorted(test.items(), key=lambda kv: -kv[1])[:8]:
        print(f"  {d}  score {s:5.1f}  (rank {m.percentile(s):.3f} of training days)  flow {qd.get(d, float('nan')):5.2f} m3/s  rain {rd.get(d, float('nan')):5.1f} mm")


if __name__ == "__main__":
    main()
