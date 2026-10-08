#!/usr/bin/env python3
"""Worked example for README.md: what replacing the cubic interval DP by the endpoint DP could save.

This is an illustration with stated assumptions, not a measured saving. It multiplies two things:
  - the exact comparison counts proved in pairs/max-merge-cost-larger-part-cubic-dp-vs-endpoint-dp/PROOFS.md,
    n(n+1)(2n+1)/6 for the cubic DP and n(3n-1)/2 for the endpoint DP;
  - the measured time per comparison of each algorithm at the largest n of the recorded run
    ledger/runs/<make_charts.LEDGER_RUN>.json (one core, CPython).
For other n the time is extrapolated from that rate. Power, price and water use are assumptions you can change.

  python tools/savings_scenario.py                                  # the example printed in README.md
  python tools/savings_scenario.py --n 5000 --runs-per-day 100 --watts 10 --price 0.30 --water 0
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_charts  # noqa: E402

CUBIC = "cubic interval DP (every split)"
ENDPOINT = "endpoint DP (two candidate splits per row)"


def rates() -> tuple[float, float, int, int]:
    """Seconds per comparison of the cubic and the endpoint DP, and the n at which each rate was measured."""
    led = make_charts.load_ledger()[make_charts.MERGE_LARGER]
    c, e = led[CUBIC], led[ENDPOINT]
    return (c["timing"]["values"][-1] / c["values"][-1], e["timing"]["values"][-1] / e["values"][-1],
            c["n_values"][-1], e["n_values"][-1])


def scenario(n: int, runs_per_day: float, watts: float, price: float, water: float) -> dict:
    s_cubic, s_endpoint, n_cubic, n_endpoint = rates()
    old, new = make_charts.cubic(n), make_charts.endpoint(n)
    t_old, t_new = old * s_cubic, new * s_endpoint
    core_hours = (t_old - t_new) * runs_per_day / 3600
    kwh = core_hours * watts / 1000
    return {"n": n, "comparisons_old": old, "comparisons_new": new, "ratio": old / new,
            "ns_per_comparison_old": s_cubic * 1e9, "ns_per_comparison_new": s_endpoint * 1e9,
            "rate_measured_at_n": (n_cubic, n_endpoint),
            "seconds_old": t_old, "seconds_new": t_new, "core_hours_per_day": core_hours,
            "kwh_per_day": kwh, "cost_per_day": kwh * price, "water_l_per_day": kwh * water}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=1000, help="number of merges; the row has n + 1 piles (default 1000)")
    ap.add_argument("--runs-per-day", type=float, default=10_000, help="runs per day (default 10000)")
    ap.add_argument("--watts", type=float, default=15.0, help="assumed power per busy core in W (default 15)")
    ap.add_argument("--price", type=float, default=0.15, help="assumed electricity price per kWh (default 0.15)")
    ap.add_argument("--water", type=float, default=1.8, help="assumed cooling water in L per kWh (default 1.8)")
    a = ap.parse_args(argv)
    if a.n < 1:
        ap.error("--n must be at least 1")
    r = scenario(a.n, a.runs_per_day, a.watts, a.price, a.water)
    print(f"n = {r['n']} merges ({r['n'] + 1} piles), {a.runs_per_day:,.0f} runs a day (an illustration with stated assumptions)")
    print(f"  comparisons per run   cubic DP {r['comparisons_old']:,}   endpoint DP {r['comparisons_new']:,}"
          f"   ratio {r['ratio']:,.1f}  (exact, PROOFS.md)")
    print(f"  time per comparison   {r['ns_per_comparison_old']:.0f} ns and {r['ns_per_comparison_new']:.0f} ns"
          f"  (recorded run {make_charts.LEDGER_RUN}, measured at n = {r['rate_measured_at_n'][0]} and"
          f" {r['rate_measured_at_n'][1]})")
    print(f"  time per run          {r['seconds_old']:,.1f} s and {r['seconds_new']:,.2f} s"
          f"  (counts times measured rate)")
    print(f"  assumptions           {a.watts:g} W per core, {a.price:g} per kWh, {a.water:g} L of water per kWh")
    print(f"  per day               {r['core_hours_per_day']:,.0f} core-hours, {r['kwh_per_day']:,.1f} kWh,"
          f" cost {r['cost_per_day']:,.2f}, water {r['water_l_per_day']:,.0f} L")
    print(f"  per year (365 days)   {r['core_hours_per_day'] * 365:,.0f} core-hours, {r['kwh_per_day'] * 365:,.0f} kWh,"
          f" cost {r['cost_per_day'] * 365:,.0f}, water {r['water_l_per_day'] * 365:,.0f} L")
    return 0


if __name__ == "__main__":
    sys.exit(main())
