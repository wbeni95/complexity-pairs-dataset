"""Global minimum cut (pairs/global-min-cut-brute-vs-stoer-wagner): exact operation counts, closed forms, alphas.

Questions:
 1. Do the exact weight-operation counts (additions + order comparisons, counted by the harness's CountingWeight
    in the UNCHANGED implementations) equal the closed forms derived below, at every n used?
 2. Which tolerance and rivals discriminate at the chosen V2 n_values (alphas computed with the validator's own
    eval_cost / fit_slope)?
 3. Does the V1 battery (the validator's seeds) contain every generator family, minimum cuts equal to 0 and
    zero-weight entries? Do the two oracle methods (n - 1 max flows; subset enumeration) agree with each other
    and with both implementations on extra random instances?

Closed forms (proven; derivation in the entry README):
  brute force, n >= 2:  additions   A_B(n) = sum_{k=1}^{n-1} C(n-1,k) k (n-k) = n (n-1) 2^(n-3)
                        comparisons C_B(n) = 2^(n-1) - 2        (one per bipartition after the first)
                        total       2^(n-3) (n^2 - n + 4) - 2
  Stoer-Wagner, n >= 2: phase on k vertices: (k-1)(k-2)/2 key additions + (k-2) merge additions,
                        (k-1)(k-2)/2 selection comparisons, + 1 comparison with the best cut (all phases but the first)
                        additions   A_SW(n) = (n-1)(n-2)(n+3)/6
                        comparisons C_SW(n) = n(n-1)(n-2)/6 + n - 2
                        total       (n-2)(2n^2 + n + 3)/6

Result (console run 2026-10-07, CPython, Windows 11; every number is an exact count, deterministic; ~5 s):
 Q1  brute force: measured additions and comparisons equal the closed forms for every n = 2..14; Stoer-Wagner for
     every n = 2..40 and 48, 64, 96, 128, 192, 256. Counts do not depend on the weights (spot-checked).
 Q2  (tolerance 0.03 was chosen after this table; no attempt failed)
     brute force, n = 6, 8, 10, 12, 14 (CHOSEN): counts 270, 1918, 12030, 69630, 380926; alpha vs n^2 2^n = 1.0018;
       rivals n^3 2.8380, 2^n 1.3053, n 2^n 1.1338, n^3 2^n 0.8971 (all rejected); log diagnostic 0.9513 / 1.0578
       (resolved); local slopes 0.9995, 1.0019, 1.0028, 1.0028.
     brute force, n = 8..14: alpha 1.0025, closest rival n^3 2^n 0.9064; n = 10..16: alpha 1.0028 (n = 16 needs 2.0M
       counted operations, slower, not needed).
     Stoer-Wagner, n = 32, 64, 128, 256 (CHOSEN): counts 10415, 85343, 690879, 5559679; alpha vs n^3 = 1.0066;
       rivals n^2 2^n 0.0369, n^4 0.7549, n^2 1.5099, n^2 log^3 n 1.1277 (all rejected); log diagnostic
       0.9362 / 1.0884 (resolved); local slopes 1.0115, 1.0057, 1.0028.
     Stoer-Wagner, n = 16..128: alpha 1.0135 (lower-order terms larger at n = 16), rival n^2 log^3 n 1.0832;
       n = 24..192: alpha 1.0088, rival n^2 log^3 n 1.1103.
     The deviation |alpha - 1| comes only from lower-order terms of the exact closed forms (0.0018 and 0.0066 at the
     chosen n); the tolerance 0.03 is 4.5x above the larger one and below every rival gap (smallest: 0.1029 for
     n^3 2^n) and below both log-diagnostic gaps (smallest: 0.0487).
     Note: the pattern report's timing analysis gave rho = 1.050 for n^3 vs n^2 log^3 n (Karger-Stein), i.e.
     NOT resolvable by timing at tolerance 0.25. With exact counts, this implementation's counts reject an
     n^2 log^3 n cost (alpha 1.128). This says nothing about Karger-Stein itself, which is not implemented.
 Q3  V1 battery (validator seeds, 16 sizes x 6 trials = 96 instances): family counts {dense 0..9: 16, sparse: 11,
     two components: 27, planted light cut: 16, weak vertex: 12, all-zero: 14}; among the 84 instances with n >= 2,
     the minimum cut is 0 in 47 and 79 contain a zero off-diagonal entry. 300/300 extra random instances
     (n = 2..10): brute = Stoer-Wagner = max-flow oracle = subset oracle. Stoer-Wagner = max-flow oracle on 3
     instances each at n = 30 and 40.
 Q4  negative controls on the 84 battery instances with n >= 2: check() rejects "answer + 1" on 84/84, "minimum
     weighted degree" (only single-vertex cuts) on 28/84, "Stoer-Wagner first phase only" on 34/84.

Check lines start with [PASS] or [FAIL]: Q1 (closed forms, reported cost = additions + comparisons, weight
independence, and the per-phase formulas of Stoer-Wagner: in the phase on k vertices (k-1)(k-2)/2 key additions,
k - 2 merge additions, (k-1)(k-2)/2 selection comparisons and 1 comparison with the best cut except in the first
phase, every counted operation attributed to its source line), the Q3 battery numbers and oracle cross-checks, and
the Q4 rejection counts (84/84, 28/84, 34/84). The run ends with ALL CHECKS PASSED (exit code 0) or lists the failed
checks (exit code 1). The Q2 fits are reported, not checked.
"""
from __future__ import annotations

import importlib.util
import inspect
import random
import sys
from math import comb
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("cpairs_count_helpers", REPO / "experiments" / "2026-10-07b_count_v2_helpers.py")
H = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(H)

ENTRY = "global-min-cut-brute-vs-stoer-wagner"
entry_dir, entry, harness = H.entry_and_harness(ENTRY)
brute = H.V.load_callable(entry_dir, "implementations/brute_force.py:min_cut_brute_force")
sw = H.V.load_callable(entry_dir, "implementations/stoer_wagner.py:min_cut_stoer_wagner")

FAILED = []


def check_line(ok, *parts):
    """Print one check line with a [PASS] or [FAIL] prefix and remember the failures."""
    print("[PASS]" if ok else "[FAIL]", *parts, flush=True)
    if not ok:
        FAILED.append(" ".join(str(p) for p in parts).strip())
    return ok


def finish_checks():
    """End of the run: ALL CHECKS PASSED (exit code 0), or the failed checks and exit code 1."""
    if FAILED:
        print(f"FAILED: {len(FAILED)} check(s):")
        for label in FAILED:
            print(f"  {label}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


def brute_forms(n):
    """(additions, comparisons, whether the sum equals its closed form n (n-1) 2^(n-3))."""
    adds = sum(comb(n - 1, k) * k * (n - k) for k in range(1, n))
    identity = adds == n * (n - 1) * 2 ** (n - 3) if n >= 3 else adds * 2 == n * (n - 1) * 2 ** (n - 2)
    return adds, 2 ** (n - 1) - 2, identity


def sw_forms(n):
    """(additions, comparisons, whether both numerators are divisible by 6)."""
    divisible = (n - 1) * (n - 2) * (n + 3) % 6 == 0 and n * (n - 1) * (n - 2) % 6 == 0
    return (n - 1) * (n - 2) * (n + 3) // 6, n * (n - 1) * (n - 2) // 6 + n - 2, divisible


REPORTED_BAD = []   # runs where reported_cost differs from additions + comparisons


def measured(fn, n, seed):
    inst = harness.generate_scaling(n, random.Random(seed))
    out = fn(inst)
    adds, cmps = harness.counters()
    if harness.reported_cost(out) != adds + cmps:
        REPORTED_BAD.append((fn.__name__, n, seed))
    plain = tuple(tuple(int(x) for x in r) for r in inst)
    return adds, cmps, int(out), plain


print("Q1: exact counts vs closed forms")
bad = []
for n in range(2, 15):
    a, c, out, plain = measured(brute, n, f"q1|{n}")
    fa, fc, identity = brute_forms(n)
    if not ((a, c) == (fa, fc) and identity and fa + fc == ((n * n - n + 4) * 2 ** n - 16) // 8
            and harness.check(plain, out)):
        bad.append((n, a, c, fa, fc))
check_line(not bad, "  brute force: additions and comparisons equal the closed forms for n = 2..14"
           + (f"; FAILS at (n, adds, cmps, formula adds, formula cmps) = {bad[:5]}" if bad else ""))
bad = []
for n in list(range(2, 41)) + [48, 64, 96, 128, 192, 256]:
    a, c, out, plain = measured(sw, n, f"q1|{n}")
    fa, fc, divisible = sw_forms(n)
    if not ((a, c) == (fa, fc) and divisible and fa + fc == (n - 2) * (2 * n * n + n + 3) // 6
            and (n > 24 or harness.check(plain, out))):
        bad.append((n, a, c, fa, fc))
check_line(not bad, "  Stoer-Wagner: additions and comparisons equal the closed forms for n = 2..40, 48, 64, 96, 128, "
           "192, 256" + (f"; FAILS at (n, adds, cmps, formula adds, formula cmps) = {bad[:5]}" if bad else ""))
# weight-independence of the counts: different weights, same n -> same counts
bad = []
for n in (5, 9, 12):
    s1 = measured(brute, n, "w1")[:2]
    s2 = measured(brute, n, "w2")[:2]
    t1 = measured(sw, 3 * n, "w1")[:2]
    t2 = measured(sw, 3 * n, "w2")[:2]
    if not (s1 == s2 and t1 == t2):
        bad.append(n)
check_line(not bad, "  counts do not depend on the weights (checked at brute n = 5, 9, 12 and SW n = 15, 27, 36)"
           + (f"; FAILS at n = {bad}" if bad else ""))
check_line(not REPORTED_BAD, f"  reported cost == additions + comparisons on every run above: {not REPORTED_BAD}"
           + (f" {REPORTED_BAD[:5]}" if REPORTED_BAD else ""))

# Per-phase formulas: every counted operation of the unchanged Stoer-Wagner code is attributed, at run time, to its
# source line (key update, merge, selection, best-cut comparison) and to the phase, identified by k = the number of
# active vertices (t is already removed when the merge runs, so k = len(active) + 1 there).
_src, _start = inspect.getsourcelines(sw)


def _line_of(marker):
    hits = [_start + i for i, s in enumerate(_src) if marker in s]
    if len(hits) != 1:
        raise RuntimeError(f"source marker {marker!r} found {len(hits)} times")
    return hits[0]


L_KEY, L_MERGE = _line_of("key[v] = key[v] + G[sel][v]"), _line_of("G[s][v] = G[s][v] + G[t][v]")
L_SEL, L_BEST = _line_of("if key[v] > key[sel]:"), _line_of("cut_of_phase < best")
CW = harness.CountingWeight
_orig = {name: CW.__dict__[name] for name in ("__add__", "__radd__", "__lt__", "__le__", "__gt__", "__ge__")}
_tally = {}


def _attributed(name):
    orig = _orig[name]

    def wrapper(self, other):
        f = sys._getframe(1)
        k = len(f.f_locals["active"]) if f.f_code is sw.__code__ else None
        line = f.f_lineno if k is not None else None
        if line == L_MERGE:
            k += 1
        key = (line, k)
        _tally[key] = _tally.get(key, 0) + 1
        return orig(self, other)
    return wrapper


bad = []
for name in _orig:
    setattr(CW, name, _attributed(name))
try:
    for n in list(range(2, 41)) + [48, 64, 96, 128, 192, 256]:
        _tally.clear()
        sw(harness.generate_scaling(n, random.Random(f"q1|{n}")))
        want = {}
        for k in range(2, n + 1):
            for line, cnt in ((L_KEY, (k - 1) * (k - 2) // 2), (L_MERGE, k - 2), (L_SEL, (k - 1) * (k - 2) // 2),
                              (L_BEST, 0 if k == n else 1)):
                if cnt:
                    want[(line, k)] = cnt
        if _tally != want:
            bad.append(n)
finally:
    for name, f in _orig.items():
        setattr(CW, name, f)
check_line(not bad, "  Stoer-Wagner per phase on k vertices: (k-1)(k-2)/2 key additions, k-2 merge additions, "
           "(k-1)(k-2)/2 selection comparisons, 1 best-cut comparison (none in the first phase); no other counted "
           "operation; n = 2..40, 48, 64, 96, 128, 192, 256" + (f"; FAILS at n = {bad}" if bad else ""))

print("\nQ2: alphas at candidate n_values (validator seeds, validator fit)")
TOL = 0.03
cands = {
    "brute force": (brute, [[6, 8, 10, 12, 14], [8, 10, 12, 14], [10, 12, 14, 16]],
                    "n**2 * 2**n", ["n**3", "2**n", "n * 2**n", "n**3 * 2**n"]),
    "Stoer-Wagner (array)": (sw, [[16, 32, 64, 128], [32, 64, 128, 256], [24, 48, 96, 192]],
                             "n**3", ["n**2 * 2**n", "n**4", "n**2", "n**2 * log(n)**3"]),
}
for name, (fn, nsets, cost, rivals) in cands.items():
    for ns in nsets:
        vals = H.counts(ENTRY, name, ns)
        H.report(name, ns, vals, cost, rivals, TOL)

print("\nQ3: V1 battery composition (validator seeds) and oracle cross-checks")
th = entry["test_harness"]
fam_seen = {}
zero_cut = zero_entries = total = with_two = 0
for n in th["v1_sizes"]:
    for trial in range(th.get("trials", 3)):
        rng = random.Random(f"{ENTRY}|v1|{n}|{trial}")
        fam = random.Random(f"{ENTRY}|v1|{n}|{trial}").randrange(6)
        inst = harness.generate(n, rng)
        total += 1
        fam_seen[fam] = fam_seen.get(fam, 0) + 1
        if n >= 2:
            with_two += 1
            ans = sw(inst)
            zero_cut += ans == 0
            zero_entries += any(inst[u][v] == 0 for u in range(n) for v in range(u + 1, n))
check_line((total, dict(sorted(fam_seen.items())), with_two, zero_cut, zero_entries)
           == (96, {0: 16, 1: 11, 2: 27, 3: 16, 4: 12, 5: 14}, 84, 47, 79),
           f"  {total} instances; family counts {dict(sorted(fam_seen.items()))}; "
           f"min cut 0 in {zero_cut}; some off-diagonal zero entry in {zero_entries} (instances with n >= 2: "
           f"{with_two}; published: 96 instances, families 16/11/27/16/12/14, min cut 0 in 47 of 84, 79)")
rng = random.Random("q3-extra")
agree = 0
for i in range(300):
    n = rng.randint(2, 10)
    inst = harness.generate(n, rng)
    b, s = brute(inst), sw(inst)
    f, e = harness._min_cut_by_flows([list(r) for r in inst]), harness._min_cut_by_subsets([list(r) for r in inst])
    agree += b == s == f == e
check_line(agree == 300,
           f"  extra: {agree}/300 random instances (n = 2..10): brute = Stoer-Wagner = max-flow oracle = subset oracle")
bad = []
for n in (30, 40):
    for k in range(3):
        inst = harness.generate(n, random.Random(f"q3-large|{n}|{k}"))
        if sw(inst) != harness._min_cut_by_flows([list(r) for r in inst]):
            bad.append((n, k))
check_line(not bad, "  extra: Stoer-Wagner = max-flow oracle on 3 instances each at n = 30, 40"
           + (f"; FAILS at (n, k) = {bad}" if bad else ""))

print("\nQ4: negative controls on the V1 battery instances with n >= 2 (does check() reject wrong answers?)")


def min_degree(W):                      # wrong in general: only the single-vertex cuts
    return min(sum(r) for r in W) if len(W) >= 2 else None


def first_phase_only(W):                # wrong: Stoer-Wagner's first cut of the phase, no merging
    n = len(W)
    if n < 2:
        return None
    rest, key, order = list(range(1, n)), {v: W[0][v] for v in range(1, n)}, [0]
    while rest:
        sel = max(rest, key=lambda v: key[v])
        rest.remove(sel)
        order.append(sel)
        for v in rest:
            key[v] += W[sel][v]
    return key[order[-1]]


mutants = {"answer + 1": lambda W: sw(W) + 1, "min weighted degree": min_degree, "first phase only": first_phase_only}
battery = []
for n in th["v1_sizes"]:
    if n >= 2:
        for trial in range(th.get("trials", 3)):
            battery.append(harness.generate(n, random.Random(f"{ENTRY}|v1|{n}|{trial}")))
for name, fn in mutants.items():
    caught = sum(harness.check(W, fn(W)) is False for W in battery)
    line = f"  mutant '{name}': rejected by check() on {caught}/{len(battery)} battery instances"
    published = {"answer + 1": 84, "min weighted degree": 28, "first phase only": 34}[name]
    # "answer + 1" is wrong on every instance by construction; the published counts are 84/84, 28/84, 34/84
    check_line(len(battery) == 84 and caught == published, line + f" (published: {published}/84)")

finish_checks()
