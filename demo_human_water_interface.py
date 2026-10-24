"""
Human-Water Interface: what the Geneva (OCEau) export gives us for L'Aire.

Run:  python3 -m noea.human_water_interface.fetch      (once; downloads validated daily history)
      python3 demo_human_water_interface.py

Prints, per station and variable, how much validated data there is, so the design of the
diagnostics and the learned model can follow the data rather than guess at it.
"""
from noea.human_water_interface import STATIONS, coverage, load_daily, load_intraday


def main():
    print(f"{'station':6s} {'variable':12s} {'first':11s} {'last':11s} {'days':>5s} {'complete':>8s}  gaps > 1 day")
    for st, meta in STATIONS.items():
        for var in meta["media"]:
            try:
                ts = load_daily(st, var)
            except FileNotFoundError:
                continue
            c = coverage(ts)
            if not c["days"]:
                print(f"{st:6s} {var:12s} no validated data in the files")
                continue
            big = sorted(c["gaps"], key=lambda g: -g[2])[:2]
            print(f"{st:6s} {var:12s} {c['first']}  {c['last']}  {c['days']:5d} {c['completeness']:8.0%}  "
                  f"{len(c['gaps'])} gaps" + (f", longest {big[0][2]} days ({big[0][0]} to {big[0][1]})" if big else ""))
    try:
        h = load_intraday("PR_", "flow", "hourly")
        print(f"\nPR_ hourly flow: {len(h)} values, {h.stamps[0]} to {h.stamps[-1]}")
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    main()
