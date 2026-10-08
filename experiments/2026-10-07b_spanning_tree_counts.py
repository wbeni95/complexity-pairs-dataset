"""Spanning-tree counting entry (pairs/spanning-tree-count-enumeration-vs-kirchhoff): every number the entry cites.

Deterministic (fixed seeds); about 30 s. Run from the repo root:  ./.venv/Scripts/python experiments/2026-10-07b_spanning_tree_counts.py

What was tried and what came out (console, 2026-10-07):

1. V1 battery coverage. The validator's own seeds (n = 1..8, 12, 20, 40; 8 trials) produce every graph kind; answers
   include 0 (disconnected), 1 (trees) and n^(n-2) (complete graphs); the oracle rule used is printed per n
   (all five rules occur: disconnected, tree, Cayley, deletion-contraction, rational cofactor). All 88 instances:
   enumeration == Kirchhoff == harness.check (enumeration for n <= 8 only); 0 failures.
2. Extended battery: 40 more instances per n, n = 1..8 (all three agree) and n = 9..40 (Kirchhoff == check):
   1600 instances, 0 failures.
3. The two oracle methods agree with each other: deletion-contraction == rational cofactor (vertex 0 deleted) on
   300 random graphs with n <= 9 and at most 24 edges: 300/300 agree.
4. Bareiss with pivoting on GENERAL integer matrices (entries in [-3, 3], half of them zero, N = 1..7, 600 matrices)
   against the Leibniz formula: 600/600 equal; 326 of them needed at least one row swap, 328 are singular.
5. Bareiss on REDUCED LAPLACIANS of 2000 random graphs (n = 2..12, connected and disconnected): zero row swaps,
   as the positive (semi)definiteness argument in entry.json predicts.
6. Exact multiplication + division counts of the unchanged Kirchhoff implementation (harness CountingInt): on K_n
   for every n = 1..70 and n = 128 the count is (n-2)(n-1)(2n-3)/2; random connected graphs (G(n, 0.3) plus a
   spanning path) at n = 16, 32, 64 give the same count; the same graphs with vertex 0 isolated give answer 0
   after 0 counted operations (zero first pivot, zero column: early exit).
   V2 points n = 16, 32, 64, 128: 3045, 28365, 244125, 2024253.
7. Fits with the validator's eval_cost/fit_slope over n = 16, 32, 64, 128: alpha vs (n-1)^3 = 1.0140 (chosen claim,
   tolerance 0.03); vs n^3 = 1.0412 (would need tolerance > 0.042, and then n^3 log n, alpha 0.956, would not be
   resolved); vs the exact closed form = 1.0000; rivals n^4 = 0.7809 and n^2 = 1.5618; diagnostic vs (n-1)^3 log n
   = 0.9326, vs (n-1)^3 / log n = 1.1108.
8. Bit sizes: the largest intermediate value (including products before the exact division) seen by Bareiss on K_n
   and on random graphs stays below the Hadamard-based bound 2 n^(2(n-1)), and every entry stored in the matrix
   stays below n^(n-1). The bounds are nearly tight on K_n: at n = 80, 494 bits stored (bound 500) and 976 bits
   intermediate (bound 1000); n = 5, 10, 20, 40 likewise.
9. Enumeration cost model on K_n, n = 4..8: subsets C(n(n-1)/2, n-1) = 20, 210, 3003, 54264, 1184040, of which
   16, 125, 1296, 16807, 262144 are trees. Noise-free alphas of the claim n C(n(n-1)/2, n-1) against other costs
   over n = 4..8 (what a perfect timing would give): n! 1.5731, 2^n 4.2206 (both rejected at 0.25),
   n^(n-2) 1.2026, C(n(n-1)/2, n-1) 1.0621 and n^n 1.0543 (NOT rejected at 0.25: a limit of timing at these n,
   not a problem with the claim).
   The validator's timing runs on the same n (console, 2026-10-07, other agents running; timings are not
   reproducible): run 1: 0.0173 ms, 0.124 ms, 2.34 ms, 47 ms, 1110 ms, alpha = 0.961, rivals n! 1.512 and 2^n
   4.051 rejected; run 2: 0.0115 ms, 0.124 ms, 2.21 ms, 46.7 ms, 1240 ms, alpha = 0.995, rivals 1.566 and 4.199
   rejected.

Failed / rejected options (kept for the record):
- Counting the enumeration's work with an instrumented type: it reads the adjacency entries only once (to list the
  edges, n(n-1)/2 truth tests) and then works on plain ints that it creates itself, so no instance-based number type
  can see the per-subset work. An edge-list input would let an instrumented edge type count edge reads, but then
  the Kirchhoff implementation would build its Laplacian from plain ints and its arithmetic would be invisible. A
  sys.setprofile hook installed by generate_scaling would count calls, but it relies on the validator calling
  generate_scaling immediately before the implementation; rejected as fragile. The enumeration is therefore timed.
- Claiming n^3 for Kirchhoff (alpha 1.041 over the same n) instead of (n-1)^3: works with tolerance 0.06, but then
  the log-factor diagnostic is not resolved. (n-1)^3 is the cube of the reduced matrix dimension, the natural size.

Check lines start with [PASS] or [FAIL]: the failure counts of 1 and 2, the agreement counts of 3 and 4, the row
swaps of 5, the K_n mismatches and every random-graph line of 6 (count equal to the closed form; answer 0 after 0
counted operations with vertex 0 isolated), every line and the total of 8. The run ends with ALL CHECKS PASSED (exit
code 0) or lists the failed checks (exit code 1); in 4 also the published 326 matrices with a row swap and 328
singular ones (so the swap path of Bareiss is exercised). The battery composition, the V2 points, the fits (7) and the enumeration model (9) are reported, not checked.
"""
from __future__ import annotations

import importlib.util
import itertools
import math
import random
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "spanning-tree-count-enumeration-vs-kirchhoff"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


V = _load(REPO / "tools" / "validate.py", "st_validate")
H = _load(ENTRY / "harness.py", "st_harness")
EN = _load(ENTRY / "implementations" / "enumeration.py", "st_enum")
KB = _load(ENTRY / "implementations" / "kirchhoff_bareiss.py", "st_kb")
enum_count = EN.count_spanning_trees_enumeration
kirchhoff = KB.count_spanning_trees_kirchhoff
ENTRY_ID = "spanning-tree-count-enumeration-vs-kirchhoff"


def closed_form(n: int) -> int:
    return (n - 2) * (n - 1) * (2 * n - 3) // 2 if n >= 2 else 0


def complete(n: int):
    return tuple(tuple(0 if i == j else 1 for j in range(n)) for i in range(n))


def oracle_rule(A) -> str:
    n = len(A)
    m = sum(A[u][v] for u in range(n) for v in range(u + 1, n))
    if not H._connected(A):
        return "disconnected"
    if m == n - 1:
        return "tree"
    if m == n * (n - 1) // 2:
        return "Cayley"
    return "del-contr" if m <= 24 else "fractions"


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


def section(title: str):
    print(f"\n=== {title} ===")


def part1_v1_battery():
    section("1. V1 battery with the validator's seeds")
    sizes, trials = [1, 2, 3, 4, 5, 6, 7, 8, 12, 20, 40], 8
    bad = 0
    for n in sizes:
        kinds, rules, answers = [], [], []
        for t in range(trials):
            seed = f"{ENTRY_ID}|v1|{n}|{t}"
            kinds.append(random.Random(seed).choice(H.KINDS))
            A = H.generate(n, random.Random(seed))
            b = kirchhoff(A)
            ok = H.check(A, b) is True
            if n <= 8:
                ok = ok and enum_count(A) == b
            bad += not ok
            rules.append(oracle_rule(A))
            answers.append(b)
        print(f"n={n:2d} kinds={kinds}\n     rules={rules}\n     answers={answers}")
    check_line(bad == 0, f"failures: {bad}")


def part2_extended():
    section("2. Extended battery (40 instances per n)")
    bad = total = 0
    for n in range(1, 41):
        for t in range(40):
            A = H.generate(n, random.Random(f"st-extended|{n}|{t}"))
            b = kirchhoff(A)
            ok = H.check(A, b) is True
            if n <= 8:
                ok = ok and enum_count(A) == b
            bad += not ok
            total += 1
    check_line(bad == 0, f"instances: {total}, failures: {bad}")


def part3_oracles_agree():
    section("3. Deletion-contraction vs rational cofactor (vertex 0 deleted)")
    rng = random.Random("st-oracles")
    agree = done = 0
    while done < 300:
        n = rng.randint(2, 9)
        p = rng.choice([0.3, 0.5, 0.7])
        W = [[0] * n for _ in range(n)]
        for u in range(n):
            for v in range(u + 1, n):
                if rng.random() < p:
                    W[u][v] = W[v][u] = 1
        A = tuple(map(tuple, W))
        edges = {(u, v): 1 for u in range(n) for v in range(u + 1, n) if A[u][v]}
        if len(edges) > 24:
            continue
        dc = H._deletion_contraction(frozenset(range(n)), edges)
        agree += dc == H._cofactor_fractions(A)
        done += 1
    check_line(agree == done, f"graphs: {done}, agree: {agree}")


class SwapSpy(list):
    """A list that records assignments to its own slots (Bareiss row swaps are M[k], M[r] = M[r], M[k])."""
    swaps = 0

    def __setitem__(self, i, value):
        SwapSpy.swaps += 1
        super().__setitem__(i, value)


def leibniz(M):
    N = len(M)
    total = 0
    for perm in itertools.permutations(range(N)):
        inv = sum(1 for i in range(N) for j in range(i + 1, N) if perm[i] > perm[j])
        prod = 1
        for i in range(N):
            prod *= M[i][perm[i]]
        total += -prod if inv % 2 else prod
    return total


def part4_general_matrices():
    section("4. Bareiss with pivoting on general integer matrices vs Leibniz")
    rng = random.Random("st-general")
    agree = with_swaps = singular = 0
    for _ in range(600):
        N = rng.randint(1, 7)
        M = [[0 if rng.random() < 0.5 else rng.randint(-3, 3) for _ in range(N)] for _ in range(N)]
        ref = leibniz(M)
        SwapSpy.swaps = 0
        spy = SwapSpy([row[:] for row in M])
        SwapSpy.swaps = 0
        d = KB._bareiss_det(spy)
        agree += d == ref
        with_swaps += SwapSpy.swaps > 0
        singular += ref == 0
    check_line(agree == 600 and (with_swaps, singular) == (326, 328),
               f"matrices: 600, agree: {agree}, with at least one row swap: {with_swaps}, singular: {singular}")


def reduced_laplacian(A):
    n = len(A)
    return [[sum(A[i]) if i == j else -A[i][j] for j in range(n - 1)] for i in range(n - 1)]


def part5_laplacians_never_swap():
    section("5. Row swaps on reduced Laplacians")
    rng = random.Random("st-laplacian-swaps")
    swaps = graphs = disconnected = 0
    for _ in range(2000):
        n = rng.randint(2, 12)
        A = H.generate(n, rng)
        SwapSpy.swaps = 0
        spy = SwapSpy(reduced_laplacian(A))
        SwapSpy.swaps = 0
        KB._bareiss_det(spy)
        swaps += SwapSpy.swaps
        graphs += 1
        disconnected += not H._connected(A)
    check_line(swaps == 0, f"graphs: {graphs} ({disconnected} disconnected), row swaps: {swaps}")


def counted(A_plain):
    """Run the unchanged implementation on CountingInt entries; return (answer, count)."""
    H._ops = 0
    A = tuple(tuple(H.CountingInt(x) for x in row) for row in A_plain)
    out = kirchhoff(A)
    return int(out), H._ops


def part6_counts():
    section("6. Exact multiplication + division counts (Kirchhoff)")
    mismatches = []
    for n in list(range(1, 71)) + [128]:
        ans, c = counted(complete(n))
        if c != closed_form(n) or ans != n ** max(n - 2, 0):
            mismatches.append(n)
    check_line(not mismatches,
               f"K_n, n = 1..70 and 128: count == (n-2)(n-1)(2n-3)/2 and answer == n^(n-2); mismatches: {mismatches}")
    for n in (16, 32, 64):
        rng = random.Random(f"st-connected|{n}")
        W = [[0] * n for _ in range(n)]
        for u in range(n):
            for v in range(u + 1, n):
                if rng.random() < 0.3 or v == u + 1:
                    W[u][v] = W[v][u] = 1
        ans, c = counted(tuple(map(tuple, W)))
        Wd = [row[:] for row in W]
        for v in range(n - 1):  # isolate vertex 0: disconnected
            Wd[0][v + 1] = Wd[v + 1][0] = 0
        ansd, cd = counted(tuple(map(tuple, Wd)))
        check_line(c == closed_form(n) and ansd == 0 and cd == 0,
                   f"n={n}: connected G(n,0.3)+path count {c} (closed form {closed_form(n)}), tau has "
                   f"{ans.bit_length()} bits; vertex 0 isolated: answer {ansd}, count {cd}")
    vals = [counted(complete(n))[1] for n in (16, 32, 64, 128)]
    print(f"V2 points n = 16, 32, 64, 128: {vals}")


def part7_fits():
    section("7. Fits over n = 16, 32, 64, 128 (validator eval_cost / fit_slope)")
    ns = [16, 32, 64, 128]
    ys = [math.log(closed_form(n)) for n in ns]

    def alpha(cost):
        return V.fit_slope([math.log(V.eval_cost(cost, n)) for n in ns], ys)

    for cost in ["(n-1)**3", "n**3", "(n-2)*(n-1)*(2*n-3)/2", "n**4", "n**2",
                 "(n-1)**3*log(n)", "(n-1)**3/log(n)", "n**3*log(n)", "n**3/log(n)"]:
        print(f"alpha vs {cost:24s} = {alpha(cost):.4f}")


class MaxTrack:
    """Integer wrapper recording the largest absolute value produced by any operation."""
    __slots__ = ("v",)
    biggest = 0
    stored = 0

    def __init__(self, v):
        self.v = v
        MaxTrack.biggest = max(MaxTrack.biggest, abs(v))

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, MaxTrack) else x

    def __mul__(self, o): return MaxTrack(self.v * self._val(o))
    __rmul__ = __mul__
    def __add__(self, o): return MaxTrack(self.v + self._val(o))
    __radd__ = __add__
    def __sub__(self, o): return MaxTrack(self.v - self._val(o))
    def __rsub__(self, o): return MaxTrack(self._val(o) - self.v)
    def __neg__(self): return MaxTrack(-self.v)

    def __floordiv__(self, o):
        q = self.v // self._val(o)
        MaxTrack.stored = max(MaxTrack.stored, abs(q))  # quotients are the entries written back
        return MaxTrack(q)

    def __eq__(self, o): return self.v == self._val(o)
    def __ne__(self, o): return self.v != self._val(o)
    def __bool__(self): return self.v != 0
    def __hash__(self): return hash(self.v)


def part8_bits():
    section("8. Bit sizes vs the Hadamard bounds")
    ok = True
    for n in (5, 10, 20, 40, 80):
        for label, A in [("K_n", complete(n)), ("generate()", H.generate(n, random.Random(f"st-bits|{n}")))]:
            MaxTrack.biggest = MaxTrack.stored = 0
            kirchhoff(tuple(tuple(MaxTrack(x) for x in row) for row in A))
            bound_entry, bound_any = n ** (n - 1), 2 * n ** (2 * (n - 1))
            good = MaxTrack.stored < bound_entry and MaxTrack.biggest < bound_any
            ok = ok and good
            check_line(good, f"n={n:3d} {label:10s}: largest entry {MaxTrack.stored.bit_length():5d} bits (bound n^(n-1): "
                             f"{bound_entry.bit_length()}), largest intermediate {MaxTrack.biggest.bit_length():5d} bits "
                             f"(bound 2n^(2(n-1)): {bound_any.bit_length()}) {'ok' if good else 'VIOLATED'}")
    check_line(ok, f"all within bounds: {ok}")


def part9_enumeration_model():
    section("9. Enumeration on K_n: subsets, trees, noise-free alphas over n = 4..8")
    ns = [4, 5, 6, 7, 8]
    print("subsets:", [math.comb(n * (n - 1) // 2, n - 1) for n in ns])
    print("trees:  ", [n ** (n - 2) for n in ns])
    claim = "n * factorial(n*(n-1)/2) / (factorial(n-1) * factorial(n*(n-1)/2 - n + 1))"
    ys = [math.log(V.eval_cost(claim, n)) for n in ns]
    for cost in ["factorial(n)", "2**n", "n**(n-2)", "factorial(n*(n-1)/2) / (factorial(n-1) * factorial(n*(n-1)/2 - n + 1))", "n**n"]:
        a = V.fit_slope([math.log(V.eval_cost(cost, n)) for n in ns], ys)
        print(f"alpha vs {cost[:40]:40s} = {a:.4f} -> {'rejected' if abs(a - 1) > 0.25 else 'NOT rejected'} at 0.25")


if __name__ == "__main__":
    part1_v1_battery()
    part2_extended()
    part3_oracles_agree()
    part4_general_matrices()
    part5_laplacians_never_swap()
    part6_counts()
    part7_fits()
    part8_bits()
    part9_enumeration_model()
    finish_checks()
