"""2-SAT entry (pairs/two-sat-brute-force-vs-scc): exact operation counts, closed forms, near-misses, V1 audit.

Questions and results (all from running this script; deterministic, no timing involved):

1. Brute force on the V2 family W_n (star (x1 OR x_j), j = 2..n; unsatisfiable core on x2, x3; chain
   x_1 -> ... -> x_n; m = 2n + 2). Hand derivation: the 2^(n-1) assignments with x1 true spend n - 1 literal
   evaluations on the star and on average 4 in the core (2, 4, 4, 6 for (x2, x3) = FF, FT, TF, TT); those with x1
   false fail at the first false x_j after 2 evaluations per star clause, total 2^(n+1) - 2n - 2, plus 2(n-1) + 6
   for the one assignment that reaches the core. Sum: (n + 7) 2^(n-1) + 2 literal evaluations. The implementation
   performs 6 counted operations per literal evaluation (abs, -1, >>, &1, >0, ==), so the count is
   3(n + 7) 2^n + 12. RESULT: equal to the measured count for every n = 3..16.
2. Aspvall-Plass-Tarjan on W_n. Graph construction costs 14 counted operations per 2-literal clause
   (5 per _node call, 2 per adj[x ^ 1]), i.e. 28n + 28. RESULT: the measured total is exactly 49(n + 2) for every
   n = 3..300 and for n = 500, 1000, ..., 32000 (the traversal part 21n + 70 is derived in
   pairs/two-sat-brute-force-vs-scc/PROOFS.md, section 2).
3. Fits with the validator's own eval_cost / fit_slope on the declared n_values. RESULT:
   brute force vs (n + 7) * 2**n alpha = 0.9998; rivals 2**n 1.0767, n**2 * 2**n 0.8621; the bare n * 2**n gives
   0.9577 (outside the 0.02 band because of the lower-order term at n <= 16). SCC vs n alpha = 0.9995; rivals
   n log n 0.8947, n**2 0.4997. Tolerance 0.02 separates all of them.
4. Near-miss (why W_n is needed). Brute force on unsatisfiable formulas made of 2n - 2 RANDOM 2-clauses followed by
   the same 4-clause core (m = 2n + 2, 5 seeds per n): the mean count per 2^n stays near a constant
   (36.15, 36.11, 35.56, 38.49, 35.91 operations per assignment for n = 8, 10, 12, 14, 16, i.e. about 6 literal
   evaluations), the fit against 2**n gives alpha = 1.0036 and against n * 2**n 0.8926. Early exit makes random
   padding Theta(2^n), not Theta(m 2^n). Placing the core FIRST gives exactly 24 * 2^n (4 literal evaluations
   per assignment) for n = 8, 12, 16: also Theta(2^n).
5. V1 audit (the validator's battery, same seeds: 15 sizes x 4 formulas = 60 instances). [SAT, UNSAT] per n:
   0: [3, 1], 1: [4, 0], 2: [3, 1], 3: [1, 3], 4: [3, 1], 5: [3, 1], 6: [1, 3], 7: [3, 1], 8: [1, 3], 10: [3, 1],
   12: [2, 2], 14: [1, 3], 50: [2, 2], 300: [1, 3], 3000: [2, 2] (33 SAT, 27 UNSAT). check() returned True for
   every output of both implementations and never None. The 27 UNSAT verdicts were proved by: an empty clause (1),
   exhaustive search, n <= 12 (16), the BFS pair of implication paths x ~> NOT x ~> x, n > 12 (10) (tallied in a
   console run with the same seeds). Negative controls (None for a satisfiable formula; the negated satisfying assignment
   when it is not satisfying; the all-true and all-false assignments for an unsatisfiable formula): 0 accepted.

Check lines start with [PASS] or [FAIL]: every n and the summary of 1, the mismatches and the construction probe
(12 counted operations per clause) of 2, the core-first lines of 4 (exactly 24 * 2^n), and the V1 audit of 5 (check()
returns True for every output of both implementations; every negative control rejected). The run ends with ALL CHECKS
PASSED (exit code 0) or lists the failed checks (exit code 1). The fits (3), the random-padding near-miss and the
SAT/UNSAT composition are reported, not checked.
"""
from __future__ import annotations

import importlib.util
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("count_v2_helpers", REPO / "experiments" / "2026-10-07b_count_v2_helpers.py")
Hlp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(Hlp)
V = Hlp.V

ENTRY = "two-sat-brute-force-vs-scc"
entry_dir, entry, H = Hlp.entry_and_harness(ENTRY)
A_NAME = "brute force over all assignments"
B_NAME = "Aspvall-Plass-Tarjan (implication graph + Tarjan SCC)"
A = V.load_callable(entry_dir, Hlp.algorithm(entry, A_NAME)["implementation"])
B = V.load_callable(entry_dir, Hlp.algorithm(entry, B_NAME)["implementation"])

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


def counting_instance(n, clauses):
    """Like harness.generate_scaling, but for arbitrary clauses: CountingLit literals, counter reset."""
    inst = (n, tuple(tuple(H.CountingLit(l) for l in cl) for cl in clauses))
    H._ops = 0
    return inst


def count(fn, inst_builder):
    inst = inst_builder()
    out = fn(inst)
    return H.reported_cost(out), out


def main():
    print("1. brute force on W_n: measured vs 3(n+7)2^n + 12")
    ok = True
    for n in range(3, 17):
        c, out = count(A, lambda: H.generate_scaling(n, None))
        line_ok = (c == 3 * (n + 7) * 2 ** n + 12) and out is None
        ok &= line_ok
        check_line(line_ok, f"   n={n:2d}: {c}  closed form {3 * (n + 7) * 2 ** n + 12}  "
                            f"{'=' if c == 3 * (n + 7) * 2 ** n + 12 else 'MISMATCH'}")
    check_line(ok, f"   all equal: {ok}")

    print("2. SCC on W_n: measured vs 49(n+2)")
    ns = list(range(3, 301)) + [500, 1000, 2000, 4000, 8000, 16000, 32000]
    bad = []
    for n in ns:
        c, out = count(B, lambda: H.generate_scaling(n, None))
        if c != 49 * (n + 2) or out is not None:
            bad.append((n, c))
    check_line(not bad, f"   checked {len(ns)} values of n; mismatches: {bad}")
    # construction part alone: 14 per clause
    n = 1000
    inst = H.generate_scaling(n, None)
    _, clauses = inst
    for cl in clauses:
        a = (abs(cl[0]) - 1) * 2 + (cl[0] < 0)
        b = (abs(cl[-1]) - 1) * 2 + (cl[-1] < 0)
        a ^ 1, b ^ 1
    check_line(H.reported_cost(None) == 12 * len(clauses),
               f"   construction-only probe (same operations as two_sat_scc's loop minus list indexing), n=1000:"
               f" {H.reported_cost(None)} ops for m = {len(clauses)} clauses (12 per clause; + 2 list indexings = 14)")

    print("3. fits on the declared n_values (validator functions)")
    for name in (A_NAME, B_NAME):
        sc = Hlp.algorithm(entry, name)["harness"]["scaling"]
        vals = Hlp.counts(ENTRY, name, sc["n_values"])
        Hlp.report(name, sc["n_values"], vals, sc["cost"], sc["rivals"], sc["tolerance"])
    sc = Hlp.algorithm(entry, A_NAME)["harness"]["scaling"]
    vals = Hlp.counts(ENTRY, A_NAME, sc["n_values"])
    print(f"   brute force vs bare n * 2**n: alpha = {Hlp.alpha(sc['n_values'], vals, 'n * 2**n'):.4f}")
    print(f"   brute force vs (2n+2) * 2**n (= m 2^n): alpha = {Hlp.alpha(sc['n_values'], vals, '(2*n + 2) * 2**n'):.4f}")

    print("4. near-misses for brute force")
    core = [(2, 3), (2, -3), (-2, 3), (-2, -3)]
    rnd_ns = [8, 10, 12, 14, 16]
    means = []
    for n in rnd_ns:
        cs = []
        for seed in range(5):
            rng = random.Random(f"two-sat-near-miss|{n}|{seed}")
            pad = []
            for _ in range(2 * n - 2):
                a, b = rng.sample(range(1, n + 1), 2)
                pad.append((a if rng.random() < 0.5 else -a, b if rng.random() < 0.5 else -b))
            c, out = count(A, lambda: counting_instance(n, pad + core))
            cs.append(c)
        means.append(sum(cs) / len(cs))
        print(f"   random padding + core last, n={n}: counts {cs}, mean per 2^n = {sum(cs) / len(cs) / 2 ** n:.2f}")
    print(f"   fit vs 2**n: {Hlp.alpha(rnd_ns, means, '2**n'):.4f}; vs n * 2**n: {Hlp.alpha(rnd_ns, means, 'n * 2**n'):.4f}")
    for n in (8, 12, 16):
        fam = H._family(n)
        star, chain = fam[:n - 1], fam[n + 3:]
        c, out = count(A, lambda: counting_instance(n, core + star + chain))
        check_line(c == 24 * 2 ** n, f"   core first (then star, chain), n={n}: {c} = {c / 2 ** n:g} * 2^n")

    print("5. V1 audit (validator seeds)")
    th = entry["test_harness"]
    a_max = Hlp.algorithm(entry, A_NAME)["harness"]["v1_max_n"]
    tally = {}
    none_verdicts = 0
    neg_fail = 0
    not_true = []
    for n in th["v1_sizes"]:
        for trial in range(th["trials"]):
            rng = random.Random(f"{ENTRY}|v1|{n}|{trial}")
            inst = H.generate(n, rng)
            outb = B(inst)
            outs = [outb] + ([A(inst)] if n <= a_max else [])
            for o in outs:
                v = H.check(inst, o)
                if v is None:
                    none_verdicts += 1
                if v is not True:
                    not_true.append((n, trial, v))
            sat = outb is not None
            t = tally.setdefault(n, [0, 0])
            t[0 if sat else 1] += 1
            # negative controls
            if sat:
                wrong = [None, tuple(not x for x in outb)]
                wrong = [w for w in wrong if w is None or not H._satisfies(inst[1], (None,) + w)]
            else:
                wrong = [tuple([True] * n), tuple([False] * n)]
            for w in wrong:
                if H.check(inst, w) is not False:
                    neg_fail += 1
    print(f"   per n [SAT, UNSAT]: {tally}")
    check_line(not not_true and neg_fail == 0,
               f"   check() returned None: {none_verdicts} times; negative controls not rejected: {neg_fail}"
               + (f" | FAIL: check() not True at (n, trial, verdict) {not_true[:5]}" if not_true else ""))


if __name__ == "__main__":
    sys.setrecursionlimit(1000)   # the SCC implementation is iterative; the default limit is kept
    main()
    finish_checks()
