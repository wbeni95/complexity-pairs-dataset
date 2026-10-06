"""Are the count-based V2 values identical across Python versions? (CI runs Python 3.12, local runs 3.14.)

Prints, for every algorithm of the eight count-based entries converted on 2026-10-07b, the exact counts that
tools/validate.run_v2 measures, and (informational) the closest-pair comparison counts, which include
comparisons made inside CPython's C code (sorted(), min()) and are deliberately NOT used for V2. Run it under
two interpreters and compare the outputs line by line:

    ./.venv/Scripts/python experiments/2026-10-07b_count_v2_cross_version.py > a.txt
    py -3.12 experiments/2026-10-07b_count_v2_cross_version.py > b.txt

The script needs only the standard library (run_v2 does not use jsonschema). Deterministic.

Outcome (run 2026-10-06 local date under Python 3.14.2 (project venv) and 3.12.10 (py -3.12)): all 17 V2 count
series are identical value for value (same sha256 26ea1a9e...d01c); the only differing lines are the version
and the informational closest-pair comparison counts: 39445, 87299, 191603, 418137, 904874, 1950644, 4179983
under 3.14.2 vs 39380, 87152, 191357, 417660, 903852, 1948580, 4175881 under 3.12.10. This is why the
closest-pair entry reports multiplications and not comparisons.
"""
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

_s = importlib.util.spec_from_file_location("cv2h", Path(__file__).resolve().parent / "2026-10-07b_count_v2_helpers.py")
H = importlib.util.module_from_spec(_s)
_s.loader.exec_module(H)

ENTRIES = [
    "sorting-insertion-vs-merge",
    "element-distinctness-pairs-vs-sorting",
    "bipartite-matching-kuhn-vs-hopcroft-karp",
    "inversion-counting-quadratic-vs-merge",
    "longest-increasing-subsequence",
    "closest-pair-brute-vs-divide-conquer",
    "all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall",
    "string-matching-naive-vs-kmp",
]

print("python", sys.version.split()[0])
allvals = []
for eid in ENTRIES:
    d = H.REPO / "pairs" / eid
    entry = json.loads((d / "entry.json").read_text(encoding="utf-8"))
    rec = {}
    errs = H.V.run_v2(entry, d, False, rec)
    for m in rec["v2"]:
        print(f"{eid} | {m['algorithm']} | alpha={m['alpha']:.6f} | {m['values']}")
        allvals.append(m["values"])
    if errs:
        print("ERRORS", errs)

# Informational: comparisons in closest-pair divide and conquer (include CPython's sorted()/min()).
EID = "closest-pair-brute-vs-divide-conquer"
edir, entry, h = H.entry_and_harness(EID)
fn = H.V.load_callable(edir, H.algorithm(entry, "Shamos-Hoey divide and conquer")["implementation"])
comps = []
for n in [1000, 2000, 4000, 8000, 16000, 32000, 64000]:
    inst = h.generate_scaling(n, random.Random(f"{EID}|v2|{n}"))
    fn(inst)
    comps.append(h._comparisons)
print("INFO closest-pair D&C comparisons:", comps)
print("sha256 of all V2 values:", hashlib.sha256(repr(allvals).encode()).hexdigest())
