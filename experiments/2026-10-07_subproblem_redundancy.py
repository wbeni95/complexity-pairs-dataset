#!/usr/bin/env python3
"""How redundant are the dataset's slow recursive algorithms? (pattern mining, 2026-10-07)

Question: the technique taxonomy in research/2026-10-07_patterns.md separates two kinds of slow recursive
algorithms:
  (a) recursion whose DISTINCT subproblems are polynomially many, so memoisation alone gives a polynomial
      algorithm (the classic T2 "memoise the recurrence" pattern), and
  (b) recursion whose distinct subproblems are still exponentially many under the natural memo key, so
      memoisation alone gives at best an exponential (T8-type) improvement, and the polynomial algorithm needs a
      different structural insight (an algebraic invariant for the determinant; dropping the visited set for
      shortest paths, which is valid because non-negative weights make optimal walks simple).
Is that separation visible in the actual implementations stored in the dataset?

Method: run each stored slow implementation UNCHANGED under sys.setprofile and, on every call of its recursive
function, record the arguments that determine the subproblem ("memo key"). Report total calls and the number
of distinct keys. For shortest paths a second, compressed key (the current vertex only) is also counted. Inputs
come from each entry's own harness.generate(n, rng) with rng = random.Random(f"subproblem|{entry}|{n}"), so the
output is deterministic. Nothing in pairs/ or synthetic/ is modified.

Result (run 2026-10-07, CPython 3.14.2; deterministic, so a rerun prints the same table):
  (a) fibonacci, linear-recurrence c1-1-1, edit distance and matrix chain: the distinct keys are exactly n+1, n+1,
      (n+1)^2 and n(n+1)/2 at every measured n, while the calls grow exponentially: fibonacci n = 22: 57,313
      calls (= 2F(23) - 1) on 23 keys; edit distance n = 8: 398,593 calls on 81 distinct (i, j); matrix chain
      n = 12: 177,147 = 3^11 calls on 78 distinct (i, j).
  (b) cofactor determinant: the distinct column sets are exactly 2^n at n = 3..8 (n = 8: 109,601 calls on 256
      sets), so memoising the expansion on its natural key gives an algorithm with ~2^n states, not a polynomial
      one. Shortest-path DFS: the distinct (vertex, visited set) states are n * 2^(n-3) + 1 at n = 4..9 (n = 9:
      27,400 calls on 577 states), still exponential; keyed on the vertex alone there are only n states, which is
      the compression that Dijkstra's algorithm (and Bellman's equation) relies on.
The table printed below is the evidence; the closed forms above were read off it, not proven here.
"""
from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def count_calls(fn, inst, filename: str, func_name: str, keyfuncs: dict):
    """Run fn(inst) and count calls of the function `func_name` defined in `filename`.

    keyfuncs maps a label to a function frame_locals -> hashable key. Returns (calls, {label: distinct keys}).
    """
    calls = 0
    seen = {label: set() for label in keyfuncs}

    def prof(frame, event, arg):
        nonlocal calls
        if event == "call" and frame.f_code.co_name == func_name and frame.f_code.co_filename == filename:
            calls += 1
            loc = frame.f_locals
            for label, kf in keyfuncs.items():
                seen[label].add(kf(loc))

    old = sys.getprofile()
    sys.setprofile(prof)
    try:
        fn(inst)
    finally:
        sys.setprofile(old)
    return calls, {label: len(s) for label, s in seen.items()}


CASES = [
    # (entry folder, implementation file, function to call, recursive function name, sizes, keys)
    ("pairs/fibonacci-naive-vs-dp", "implementations/naive.py", "fib_naive", "fib_naive",
     [10, 14, 18, 22], {"n": lambda L: L["n"]}),
    ("synthetic/linear-recurrence-c1-1-1", "implementations/naive.py", "solve", "solve",
     [10, 14, 18, 22], {"n": lambda L: L["n"]}),
    ("pairs/edit-distance-brute-vs-dp", "implementations/brute_force.py", "edit_distance_brute", "d",
     [2, 4, 6, 8], {"(i,j)": lambda L: (L["i"], L["j"])}),
    ("pairs/matrix-chain-recursion-vs-dp", "implementations/recursion.py", "matrix_chain_recursive", "cost",
     [4, 6, 8, 10, 12], {"(i,j)": lambda L: (L["i"], L["j"])}),
    ("pairs/determinant-cofactor-vs-gaussian", "implementations/cofactor.py", "det_cofactor", "_expand",
     [3, 4, 5, 6, 7, 8], {"column set": lambda L: tuple(L["cols"])}),
    ("pairs/shortest-path-enumeration-vs-dijkstra", "implementations/enumeration.py", "shortest_path_enumerate",
     "dfs", [4, 5, 6, 7, 8, 9],
     {"(vertex, visited)": lambda L: (L["u"], tuple(L["visited"])), "vertex only": lambda L: L["u"]}),
]


def main() -> int:
    print(__doc__.split("\n")[0])
    print("CPython", sys.version.split()[0])
    for folder, impl, entry_fn, rec_fn, sizes, keys in CASES:
        d = REPO / folder
        harness = load(d / "harness.py", "h_" + d.name.replace("-", "_"))
        mod_path = d / impl
        mod = load(mod_path, "m_" + d.name.replace("-", "_"))
        fn = getattr(mod, entry_fn)
        print(f"\n{folder}  ({impl}:{entry_fn}, recursive function '{rec_fn}')")
        header = f"  {'n':>3} {'calls':>12} " + " ".join(f"{'distinct ' + k:>26}" for k in keys) + "   calls/distinct"
        print(header)
        for n in sizes:
            rng = random.Random(f"subproblem|{d.name}|{n}")
            inst = harness.generate(n, rng)
            calls, distinct = count_calls(fn, inst, str(mod_path), rec_fn, keys)
            first = next(iter(keys))
            ratio = calls / distinct[first] if distinct[first] else float("nan")
            print(f"  {n:>3} {calls:>12,} " + " ".join(f"{distinct[k]:>26,}" for k in keys) + f"   {ratio:>14,.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
