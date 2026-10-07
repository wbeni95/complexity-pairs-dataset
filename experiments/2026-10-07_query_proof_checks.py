"""Checks of the query-model proofs that take longer than a unit test (2026-10-07).

The fast checks of the same proofs are in tests/test_proofs_query.py; the PROOFS.md files of the entries name
both. This script runs three groups:

  simon    pairs/simon-classical-vs-quantum/PROOFS.md §6 (the posterior lemma of the classical lower bound):
           n = 3, all 7 x 1680 = 11760 functions of the distribution (s uniform nonzero, injective labels of the
           cosets); for every ordered sequence of up to 3 distinct points and every answer sequence with distinct
           values, the conditional distribution of s is uniform on {s != 0 : s not in D}, D the XORs of queried pairs.
  minimum  pairs/minimum-finding-classical-vs-quantum/PROOFS.md §5 (Theorem 1, the coupling): for n = 2..6 and 60
           seeds per n, the unchanged durr_hoyer_run with the paper's time-out returns the minimum in every run in
           which the infinite run (budget None, same seed) reaches the minimum at a time T_min below the time-out;
           the empirical failure rate is below 1/2. (Expected queries) for n = 1..8 and 20 seeds per n, every run
           satisfies time <= B, time = n * searches + I, I <= B, searches <= B/n and queries = 1 + 2I + M, and the
           mean count is below (4 + 1/n) B + 4.
  nand     pairs/nand-tree-evaluation-deterministic-vs-randomized/PROOFS.md §4: height 4, every one of the 65536
           inputs, exact expectations from the case formulas (at most R0(4) or R1(4) by root value, equality exactly
           on the reluctant inputs, maximum R0(4)); and the exact expectation of the unchanged randomized
           implementation, every coin sequence enumerated, on the two right-zero reluctant inputs and on 6 seeded
           random reluctant inputs of height 4, equal to R0(4) or R1(4).

Every check runs the UNCHANGED implementation (random choices replaced in memory by enumerated or seeded values;
no file is modified). Deterministic.

Usage (repository root):  python experiments/2026-10-07_query_proof_checks.py [group ...]   (default: all)
Output: one line per check, "[PASS] group: label: range" or "[FAIL] ..."; exit code 0 iff no [FAIL].
"""
from __future__ import annotations

import itertools
import random
import sys
import time
from fractions import Fraction as F
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from search.machine import set_below_normal_priority  # noqa: E402
from tools.validate import load_callable, load_module  # noqa: E402

PAIRS = REPO / "pairs"
RESULTS = []


def report(group, label, ok, rng_text, detail=""):
    tag = "[PASS]" if ok else "[FAIL]"
    print(f"{tag} {group}: {label}: {rng_text}" + (f" | {detail}" if detail else ""), flush=True)
    RESULTS.append(ok)


# ------------------------------------------------------------------------------------------------------------------

def group_simon():
    n, N = 3, 8
    funcs = []
    for s in range(1, N):
        reps = sorted({min(x, x ^ s) for x in range(N)})
        for labels in itertools.permutations(range(N), len(reps)):
            lab = dict(zip(reps, labels))
            funcs.append((s, tuple(lab[min(x, x ^ s)] for x in range(N))))
    ok, histories = len(funcs) == 11760, 0
    for r in range(0, 4):
        for pts in itertools.permutations(range(N), r):
            D = {a ^ b for a, b in itertools.combinations(pts, 2)}
            S = {s for s in range(1, N) if s not in D}
            groups = {}
            for s, f in funcs:
                key = tuple(f[x] for x in pts)
                if len(set(key)) == len(key):
                    groups.setdefault(key, {}).setdefault(s, 0)
                    groups[key][s] += 1
            for hist in groups.values():
                histories += 1
                if set(hist) != S or len(set(hist.values())) != 1:
                    ok = False
    report("simon", "posterior of s is uniform on {s != 0 : s not in D} after collision-free histories", ok,
           f"n = 3, all 11760 functions, all sequences of up to 3 distinct points ({histories} histories)")


def group_minimum():
    E = PAIRS / "minimum-finding-classical-vs-quantum"
    dh = load_module(E / "implementations" / "durr_hoyer.py")
    harness = load_module(E / "harness.py")
    coupled_ok, runs, fails, below = True, 0, 0, 0
    for n in range(2, 7):
        budget = dh.durr_hoyer_budget(n)
        for seed in range(60):
            inst = harness.generate(n, random.Random(f"dh-coupling|{n}|{seed}"))
            table = inst[1]
            target = table.index(0)
            inf = dh.durr_hoyer_run(inst, random.Random(f"dh-run|{n}|{seed}"), budget=None, stop_value=0)
            out = dh.durr_hoyer_run(inst, random.Random(f"dh-run|{n}|{seed}"), budget="paper")
            runs += 1
            fails += out["index"] != target
            if inf["time"] < budget:
                below += 1
                if out["index"] != target:
                    coupled_ok = False
    report("minimum", "budgeted run returns the minimum whenever the infinite run has T_min < time-out",
           coupled_ok, f"n = 2..6, 60 seeds per n ({below} of {runs} runs with T_min < time-out)")
    report("minimum", "empirical failure rate below 1/2", fails / runs < 0.5, f"{fails} failures in {runs} runs")

    # Per-run facts behind E[queries] <= (4 + 1/n) B + 4 (PROOFS.md section 5, "Expected queries"): on every run,
    # time <= B, time = n * searches + I, I <= B, searches <= B / n, queries = 1 + 2 I + M. I and the number of
    # searches are counted by pass-through wrappers of lib.qsearch.grover_iteration and exponential_search.
    from lib import qsearch
    orig_iter, orig_search = qsearch.grover_iteration, qsearch.exponential_search
    tally = {"I": 0, "S": 0}

    def iter_wrap(state, phase):
        tally["I"] += 1
        return orig_iter(state, phase)

    def search_wrap(*args, **kwargs):
        tally["S"] += 1
        return orig_search(*args, **kwargs)

    facts_ok, mean_ok, runs2, worst = True, True, 0, []
    qsearch.grover_iteration, qsearch.exponential_search = iter_wrap, search_wrap
    try:
        for n in range(1, 9):
            budget = dh.durr_hoyer_budget(n)
            total = 0
            for seed in range(20):
                inst = harness.generate(n, random.Random(f"dh-facts|{n}|{seed}"))
                tally["I"] = tally["S"] = 0
                out = dh.durr_hoyer_run(inst, random.Random(f"dh-facts-run|{n}|{seed}"), budget="paper")
                I, S = tally["I"], tally["S"]
                runs2 += 1
                total += out["queries"]
                if not (out["time"] <= budget and out["time"] == n * S + I and I <= budget
                        and S <= budget / n and out["queries"] == 1 + 2 * I + out["measurements"]):
                    facts_ok = False
            mean, cap = total / 20, (4 + 1 / n) * budget + 4
            worst.append(round(mean / cap, 3))
            mean_ok = mean_ok and mean <= cap
    finally:
        qsearch.grover_iteration, qsearch.exponential_search = orig_iter, orig_search
    report("minimum", "per-run facts: time <= B, time = n*searches + I, I <= B, searches <= B/n, "
           "queries = 1 + 2I + M", facts_ok, f"n = 1..8, 20 seeds per n ({runs2} runs)")
    report("minimum", "mean queries below (4 + 1/n) B + 4", mean_ok,
           f"n = 1..8, 20 seeds per n (mean / bound = {worst})")


def group_nand():
    E = PAIRS / "nand-tree-evaluation-deterministic-vs-randomized"
    rnd = load_callable(E, "implementations/random_order.py:nand_tree_random_order")
    harness = load_module(E / "harness.py")

    def formula(bits):
        if len(bits) == 1:
            return bits[0], F(1), True
        h = len(bits) // 2
        va, ea, ra = formula(bits[:h])
        vb, eb, rb = formula(bits[h:])
        if va == 1 and vb == 1:
            return 0, ea + eb, ra and rb
        if va == 0 and vb == 0:
            return 1, (ea + eb) / 2, False
        e0, e1 = (ea, eb) if va == 0 else (eb, ea)
        return 1, e0 + e1 / 2, ra and rb

    R0, R1 = [F(1)], [F(1)]
    for i in range(1, 5):
        R0.append(2 * R1[i - 1])
        R1.append(R0[i - 1] + R1[i - 1] / 2)
    ok, worst = True, F(0)
    for bits in itertools.product((0, 1), repeat=16):
        v, e, rel = formula(bits)
        cap = R0[4] if v == 0 else R1[4]
        if e > cap or (e == cap) != rel:
            ok = False
        worst = max(worst, e)
    report("nand", "case formulas: E <= R_v(4), equality iff reluctant, maximum R0(4)", ok and worst == R0[4],
           f"h = 4, all 65536 inputs (R0(4) = {R0[4]}, R1(4) = {R1[4]})")

    class Bits:
        def __init__(self, b):
            self.b, self.reads = tuple(b), 0

        def __len__(self):
            return len(self.b)

        def __getitem__(self, i):
            self.reads += 1
            return self.b[i]

    class Need(Exception):
        pass

    class Coins:
        def __init__(self, prefix):
            self.prefix, self.used = prefix, 0

        def getrandbits(self, k):
            if self.used >= len(self.prefix):
                raise Need
            self.used += 1
            return self.prefix[self.used - 1]

    def exact(bits):
        g = rnd.__globals__
        saved = g["random"]
        total, seqs, stack = F(0), 0, [()]
        try:
            while stack:
                prefix = stack.pop()
                leaves, coins = Bits(bits), Coins(prefix)
                g["random"] = coins
                try:
                    rnd(leaves)
                except Need:
                    stack += [prefix + (0,), prefix + (1,)]
                    continue
                total += F(leaves.reads, 2 ** len(prefix))
                seqs += 1
        finally:
            g["random"] = saved
        return total, seqs

    rng = random.Random("nand-reluctant-h4")
    inputs = [(0, harness.reluctant(4, 0, lambda h: 1)), (1, harness.reluctant(4, 1, lambda h: 1))]
    for _ in range(6):
        root = rng.randint(0, 1)
        inputs.append((root, harness.reluctant(4, root, lambda h: rng.randint(0, 1))))
    ok, seq_total = True, 0
    for root, bits in inputs:
        e, seqs = exact(bits)
        seq_total += seqs
        if e != (R0[4] if root == 0 else R1[4]):
            ok = False
    report("nand", "unchanged randomized implementation: exact expectation R_v(4) on reluctant inputs", ok,
           f"h = 4, 8 reluctant inputs, every coin sequence ({seq_total} sequences)")


GROUPS = {"simon": group_simon, "minimum": group_minimum, "nand": group_nand}


def main(argv):
    set_below_normal_priority()
    names = argv or list(GROUPS)
    for name in names:
        t0 = time.time()
        GROUPS[name]()
        print(f"  ({name}: {time.time() - t0:.1f} s)", flush=True)
    passed = sum(RESULTS)
    print(f"summary: {passed} [PASS], {len(RESULTS) - passed} [FAIL]")
    return 0 if all(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
