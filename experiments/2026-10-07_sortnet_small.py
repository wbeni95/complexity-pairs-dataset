"""Experiment (research/2026-10-07_search_flipgraph.md, run group G4): second, cheap validation target --
minimum-size sorting networks for n = 2..8 by randomized greedy construction + pruning (search/sortnet.py).

Fixed-size results: pipeline validation only, never dataset pairs (notes/constant-factor-alphadev.md).
Reference sizes (best known, proven optimal for n <= 8): 1, 3, 5, 9, 12, 16, 19 for n = 2..8, as tabulated in
Knuth, TAOCP Vol. 3, Section 5.3.4 (book; not machine-checked here) and used as the baseline by Codish,
Cruz-Filipe, Frank & Schneider-Kamp 2014 (doi:10.1109/ICTAI.2014.36, which proves 25 for n = 9 and 29 for n = 10).
For n <= 4 the information-theoretic bound ceil(log2 n!) = 1, 3, 5 already proves optimality.

Budget: seed 1 for every n; tries = 200 for n <= 6, 1000 for n = 7, 2000 for n = 8; explore = 0.1.
Every best network is checked by the 0-1 principle verifier AND by all n! permutations, and saved to
search/schemes/sortnet_n<n>_size<s>.json. Deterministic.

Run from the repository root:  python experiments/2026-10-07_sortnet_small.py
"""
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import sortnet  # noqa: E402
from search.machine import CpuMeter, environment, set_below_normal_priority  # noqa: E402

KNOWN = {2: 1, 3: 3, 4: 5, 5: 9, 6: 12, 7: 16, 8: 19}
TRIES = {2: 200, 3: 200, 4: 200, 5: 200, 6: 200, 7: 1000, 8: 2000}

print("below-normal priority:", set_below_normal_priority())
print("environment:", json.dumps(environment()))
total = CpuMeter().start()
out_dir = ROOT / "search" / "schemes"
out_dir.mkdir(parents=True, exist_ok=True)
for n in range(2, 9):
    meter = CpuMeter().start()
    net, stats = sortnet.search(n, seed=1, tries=TRIES[n], explore=0.1)
    load = meter.stop()
    ok01 = sortnet.sorts(n, net)
    okperm = sortnet.sorts_permutations(n, net)
    known = KNOWN[n]
    status = "matches best known" if len(net) == known else (
        "above best known" if len(net) > known else "BELOW best known -- impossible for n <= 8, would indicate a bug")
    it_bound = math.ceil(math.log2(math.factorial(n)))
    print(f"n={n}: best size {len(net)} (known optimum {known}; ceil(log2 n!) = {it_bound}) [{status}]; "
          f"first reached at try {stats['first_reached_at_try']} of {stats['tries']}; sizes over tries "
          f"{stats['min']}..{stats['max']}; 0-1 verifier {ok01}, all {math.factorial(n)} permutations {okperm}; "
          f"{load['wall_seconds']} s, system CPU {load['system_cpu_utilisation']}")
    if ok01 and okperm:
        with open(out_dir / f"sortnet_n{n}_size{len(net)}.json", "w", encoding="utf-8") as f:
            json.dump({"object": "sorting network", "n": n, "size": len(net), "comparators": net,
                       "status": status, "best_known_size": known,
                       "verified": {"zero_one_principle": ok01, "all_permutations": okperm},
                       "provenance": {"script": "experiments/2026-10-07_sortnet_small.py", "seed": 1,
                                      "tries": stats["tries"], "first_reached_at_try": stats["first_reached_at_try"],
                                      "explore": 0.1}}, f, indent=1)
            f.write("\n")
    print(f"    {net}")
print("machine:", total.stop())
