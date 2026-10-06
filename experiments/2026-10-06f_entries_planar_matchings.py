"""Grid perfect-matchings entry (pairs/planar-perfect-matchings-enumeration-vs-kasteleyn): every number it cites.

Deterministic (fixed seeds, exact integer arithmetic); about 25 s. Run from the repo root:
    ./.venv/Scripts/python experiments/2026-10-06f_entries_planar_matchings.py
It lowers its own priority (search.machine.set_below_normal_priority).

What it shows (console, 2026-10-06, CPython 3.14.2; two runs gave identical output):

1. V1 battery with the validator's seeds (35 sizes n = 0..144, 8 trials): 280 instances, 240 enumeration runs
   (n <= 48), Kasteleyn == enumeration == harness.check on all, 0 failures. Kinds: empty 8, unit 63, subset 51,
   small 64, large 25, ladder 35, path 34. Answers 0: 143, 1: 42, > 1: 95. 201 shapes have both sides >= 2, 56 of
   them with odd N.
2. Extended battery: n = 0..48, 25 each: 1225 instances, all three agree, 0 failures; n = 49..144, 4 each: 384
   instances, Kasteleyn == check, 0 failures.
3. The oracle (transfer-matrix DP) against independent facts, 0 failures in each: unit ladders m x 2 and 2 x m are
   Fibonacci F(m+1), m = 1..40 (80); unit paths give [n even], n = 0..60 (122); brute force over (N/2)-edge
   subsets on all 35 shapes with N <= 12, weights 0..3 (350); invariance under transposition (200); the classical
   cosine product for unit a x b, a, b = 1..10 (100; 8 x 8 = 12988816, 10 x 10 = 258584046368); the permanent of
   the black x white weight matrix, even N <= 16 (112).
4. Signs of the implementation's Kasteleyn matrix (captured by wrapping _bareiss_det): all 3456 unit squares of
   the unit grids a, b = 2..12 (a*b even) have sign product -1; the non-zero pattern of K is exactly the grid edges.
5. Negative controls on 480 even-N instances (n = 2..48, 20 each): |det K| == answer on all. det K < 0 on 39; over
   109 shapes with a non-zero det, the sign never differs between instances of one shape (always negative:
   2x3, 2x7, 2x11, 2x15, 2x19, 2x23, 6x3, 6x7, 10x3, 14x3). |det| of the UNSIGNED matrix != answer on 286 (first:
   a 2x2 grid with answer 10, unsigned det 2); unit 2 x 2: [[1, 1], [1, 1]], det 0, answer 2; unit m x 2
   ladders m = 2..30: wrong for 29 of 29. A signing with -1 on every vertical edge (square products +1) is wrong
   on the same 286 and equals |unsigned det| on all 480 (it is gauge-equivalent to no signs).
6. Oracle control: check accepted 270 of 270 correct outputs and rejected all 1334 wrong ones: answer + 1 (270),
   answer - 1 (270), 2 x answer (102), float (270), bool (195), unit-weight count ignoring W (68), |det| of the
   unsigned matrix (72), det of the unsigned matrix (75), signed det K without abs where negative (12).
7. Exact counts (harness CountingInt, implementations unchanged):
   - enumeration on the (n/2) x 2 ladder: L(n/2+2) - 3 and answer F(n/2+1) for every even n = 2..60 (30/30);
     n = 16..52 step 4: 120, 319, 840, 2204, 5775, 15124, 39600, 103679, 271440, 710644;
   - enumeration on the 2 x m ladder: F(m+3) - 2 + ((m-1)F(m) + 2mF(m-1))/5 for m = 1..24 (24/24); m = 24:
     684816 vs 271440 for 24 x 2;
   - Kasteleyn on the (n/2) x 2 ladder: (n-2)n(n-1)/8 for every even n = 2..120 and n = 256 (61/61);
     n = 16, 32, 64, 128, 256: 420, 3720, 31248, 256032, 2072640;
   - Kasteleyn on 400 random draws: 297 non-zero answers, all with count (N-2)N(N-1)/8, 53 of them needed a row
     swap; 103 zero answers, all with count <= the closed form (e.g. 18x2: 867 of 5355).
8. Fits (validator eval_cost / fit_slope): enumeration vs L(n/2+2) - 3: alpha 1.0000; rivals 2^(n/2) 0.6956,
   n phi^(n/2) 0.8848, n^3 2.4642; bare phi^(n/2) 1.0019; diagnostic 0.9625 / 1.0404. Kasteleyn vs (n-2)n(n-1)/8:
   alpha 1.0000; rivals n^2 1.5321, n^4 0.7661, n^3 log n 0.9433; bare n^3 1.0214 (outside 0.02); diagnostic
   0.9249 / 1.0883.
9. Bit sizes vs the Hadamard bounds (2 w_max)^(N/2) (stored) and 2 (2 w_max)^N (before division): 0 violations on
   unit 8x8, 10x10, 12x12, 2x60, 1x64 and weights up to 10^9 on 8x8, 10x10, 6x12 (e.g. 10x10: 1475 bits stored,
   bound 1544.2; 2891 bits before division, bound 3089.5).

Notes from building it:
- The "-1 on every vertical edge" signing was meant as a second wrong signing; it turned out to be the unsigned
  matrix up to row and column signs, so it is not an independent control (kept, with the equality printed).
- In the first run, the oracle-control row for the signed determinant seemed to be missing; it was only cut off
  when the output was viewed with head/tail. The full output has it (12 presented, 0 accepted).
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import math
import random
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
ENTRY_ID = "planar-perfect-matchings-enumeration-vs-kasteleyn"
ENTRY = REPO / "pairs" / ENTRY_ID


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


V = _load(REPO / "tools" / "validate.py", "ppm_validate")
H = _load(ENTRY / "harness.py", "ppm_harness")
EN = _load(ENTRY / "implementations" / "enumeration.py", "ppm_enum")
KB = _load(ENTRY / "implementations" / "kasteleyn_bareiss.py", "ppm_kast")
enum_count = EN.count_perfect_matchings_enumeration
kasteleyn = KB.count_perfect_matchings_kasteleyn
oracle = H.transfer_matrix_count
ENTRY_JSON = json.loads((ENTRY / "entry.json").read_text(encoding="utf-8"))

FIB = [0, 1]
LUC = [2, 1]
for _ in range(200):
    FIB.append(FIB[-1] + FIB[-2])
    LUC.append(LUC[-1] + LUC[-2])


def section(title: str):
    print(f"\n=== {title} ===", flush=True)


def unit(a, b):
    return (a, b, H._matrix(a, b, lambda: 1))


def kasteleyn_closed_form(n: int) -> int:
    """(m-1) m (2m-1) / 2 with m = n/2, i.e. (n-2) n (n-1) / 8."""
    return (n - 2) * n * (n - 1) // 8


def enum_ladder_closed_form(n: int) -> int:
    """L(n/2 + 2) - 3 on the (n/2) x 2 ladder."""
    return LUC[n // 2 + 2] - 3


def enum_wide_ladder_closed_form(m: int) -> int:
    """2 x m ladder (row-major order): F(m+3) - 2 search-tree edges in row 0, plus one edge per horizontal
    domino of row 0 in every row-0 tiling (total number of parts 2 in compositions of m into 1s and 2s,
    ((m-1) F(m) + 2 m F(m-1)) / 5)."""
    twos = ((m - 1) * FIB[m] + 2 * m * FIB[m - 1]) // 5 if m >= 1 else 0
    return FIB[m + 3] - 2 + twos


# --------------------------------------------------------------------------------------------------
# Helpers independent of the implementations
# --------------------------------------------------------------------------------------------------

def colour_classes(a, b):
    N = a * b
    black = [u for u in range(N) if (u // b + u % b) % 2 == 0]
    white = [u for u in range(N) if (u // b + u % b) % 2 == 1]
    return black, white


def det_fraction(M) -> int:
    """Determinant by Gaussian elimination over the rationals (partial pivoting on non-zero)."""
    M = [[Fraction(x) for x in row] for row in M]
    m = len(M)
    det = Fraction(1)
    for c in range(m):
        r = next((r for r in range(c, m) if M[r][c] != 0), None)
        if r is None:
            return 0
        if r != c:
            M[c], M[r] = M[r], M[c]
            det = -det
        det *= M[c][c]
        for r in range(c + 1, m):
            f = M[r][c] / M[c][c]
            if f:
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    assert det.denominator == 1
    return int(det)


def unsigned_biadjacency(a, b, W):
    black, white = colour_classes(a, b)
    return [[W[x][y] for y in white] for x in black]


def all_vertical_negative(a, b, W):
    """A wrong signing: -1 on EVERY vertical edge (unit squares then have sign product +1)."""
    black, white = colour_classes(a, b)
    return [[(-W[x][y] if x % b == y % b and abs(x // b - y // b) == 1 else W[x][y]) for y in white]
            for x in black]


def permanent(B) -> int:
    """perm of a square matrix by expansion over the first row with memo on the used-column mask."""
    m = len(B)
    memo = {}

    def rec(i, used):
        if i == m:
            return 1
        key = (i, used)
        if key not in memo:
            memo[key] = sum(B[i][j] * rec(i + 1, used | (1 << j)) for j in range(m)
                            if not used >> j & 1 and B[i][j])
        return memo[key]

    return rec(0, 0)


def brute_force_edges(a, b, W) -> int:
    """Sum over all (N/2)-subsets of grid edges that form a perfect matching (tiny grids only)."""
    N = a * b
    if N == 0:
        return 1
    if N % 2:
        return 0
    edges = [(u, v) for u, v in H._grid_edges(a, b) if W[u][v]]
    total = 0
    for subset in itertools.combinations(edges, N // 2):
        covered = {x for e in subset for x in e}
        if len(covered) == N:
            p = 1
            for u, v in subset:
                p *= W[u][v]
            total += p
    return total


def transpose(a, b, W):
    """The b x a instance with vertex (c, r) <- (r, c)."""
    N = a * b
    idx = [0] * N  # new index of old vertex u
    for r in range(a):
        for c in range(b):
            idx[r * b + c] = c * a + r
    inv = [0] * N
    for u in range(N):
        inv[idx[u]] = u
    return (b, a, tuple(tuple(W[inv[i]][inv[j]] for j in range(N)) for i in range(N)) if N else ())


def cosine_product(a, b) -> float:
    """Product-of-cosines formula for the number of domino tilings of an a x b rectangle (unit weights); used here only
    as a numerical cross-check of the oracle, its source is not cited in the entry."""
    p = 1.0
    for j in range(1, (a + 1) // 2 + 1):
        for k in range(1, (b + 1) // 2 + 1):
            p *= 4 * math.cos(math.pi * j / (a + 1)) ** 2 + 4 * math.cos(math.pi * k / (b + 1)) ** 2
    return p


class capture_kasteleyn_matrix:
    """Context manager: records (a copy of) every matrix the unchanged implementation passes to _bareiss_det."""

    def __enter__(self):
        self.matrices = []
        self._orig = KB._bareiss_det

        def wrapper(M):
            self.matrices.append([list(row) for row in M])
            return self._orig(M)

        KB._bareiss_det = wrapper
        return self

    def __exit__(self, *exc):
        KB._bareiss_det = self._orig
        return False


def kasteleyn_matrix(inst):
    with capture_kasteleyn_matrix() as cap:
        kasteleyn(inst)
    return cap.matrices[0] if cap.matrices else None


def needs_row_swap(K) -> bool:
    """Bareiss without swaps has pivot k = leading (k+1) x (k+1) minor; a swap is needed iff one of the
    leading minors of order 1..m-1 is zero (checked by rational elimination without pivoting)."""
    M = [[Fraction(x) for x in row] for row in K]
    m = len(M)
    for c in range(m - 1):
        if M[c][c] == 0:
            return True
        for r in range(c + 1, m):
            f = M[r][c] / M[c][c]
            if f:
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return False


def describe(inst):
    a, b, W = inst
    return f"{a}x{b}"


# --------------------------------------------------------------------------------------------------
# Parts
# --------------------------------------------------------------------------------------------------

def part1_v1_battery():
    section("1. V1 battery with the validator's seeds (sizes and trials read from entry.json)")
    th = ENTRY_JSON["test_harness"]
    cap = ENTRY_JSON["algorithms"][0]["harness"]["v1_max_n"]
    sizes, trials = th["v1_sizes"], th["trials"]
    bad = instances = enum_runs = 0
    kinds, answers = {}, {"0": 0, "1": 0, ">1": 0}
    odd_nontrivial = proper = 0
    for n in sizes:
        row = []
        for t in range(trials):
            seed = f"{ENTRY_ID}|v1|{n}|{t}"
            kind = "empty" if n == 0 else random.Random(seed).choice(H.KINDS)
            kinds[kind] = kinds.get(kind, 0) + 1
            inst = H.generate(n, random.Random(seed))
            a, b, _ = inst
            k = kasteleyn(inst)
            ok = H.check(inst, k) is True
            if n <= cap:
                ok = ok and enum_count(inst) == k
                enum_runs += 1
            bad += not ok
            instances += 1
            answers["0" if k == 0 else "1" if k == 1 else ">1"] += 1
            proper += min(a, b) >= 2
            odd_nontrivial += (n % 2 == 1 and min(a, b) >= 2)
            row.append(f"{kind}:{a}x{b}={k if k < 10**6 else '~2^%d' % k.bit_length()}")
        print(f"n={n:3d}  " + "  ".join(row))
    print(f"instances: {instances}, enumeration runs: {enum_runs} (n <= {cap}), Kasteleyn runs: {instances}, "
          f"failures: {bad}")
    print(f"kinds: {kinds}")
    print(f"answers: {answers}; shapes with both sides >= 2: {proper}; odd N with both sides >= 2: {odd_nontrivial}")


def part2_extended():
    section("2. Extended battery")
    bad = total = 0
    for n in range(0, 49):
        for t in range(25):
            inst = H.generate(n, random.Random(f"ppm-extended|{n}|{t}"))
            k = kasteleyn(inst)
            ok = H.check(inst, k) is True and enum_count(inst) == k
            bad += not ok
            total += 1
    print(f"n = 0..48, 25 instances each: {total} instances, enumeration == Kasteleyn == check: failures {bad}")
    bad = total = 0
    for n in range(49, 145):
        for t in range(4):
            inst = H.generate(n, random.Random(f"ppm-extended|{n}|{t}"))
            ok = H.check(inst, kasteleyn(inst)) is True
            bad += not ok
            total += 1
    print(f"n = 49..144, 4 instances each: {total} instances, Kasteleyn == check: failures {bad}")


def part3_oracle_selfchecks():
    section("3. The oracle (transfer-matrix DP) against independent facts")
    bad = 0
    for m in range(1, 41):
        bad += oracle(*unit(m, 2)) != FIB[m + 1]
        bad += oracle(*unit(2, m)) != FIB[m + 1]
    print(f"(a) unit ladders m x 2 and 2 x m, m = 1..40: DP == F(m+1) (Fibonacci): failures {bad} of 80")
    bad = 0
    for n in range(0, 61):
        bad += oracle(*unit(1, n)) != (1 if n % 2 == 0 else 0)
        bad += oracle(*unit(n, 1)) != (1 if n % 2 == 0 else 0)
    print(f"    unit paths 1 x n and n x 1, n = 0..60: DP == [n even]: failures {bad} of 122")
    rng = random.Random("ppm-bruteforce")
    bad = total = 0
    shapes = [(a, b) for a in range(1, 13) for b in range(1, 13) if a * b <= 12]
    for a, b in shapes:
        for _ in range(10):
            inst = (a, b, H._matrix(a, b, lambda: rng.randint(0, 3)))
            bad += oracle(*inst) != brute_force_edges(*inst)
            total += 1
    print(f"(b) DP == brute force over (N/2)-edge subsets, all {len(shapes)} shapes with N <= 12, weights 0..3: "
          f"{total} instances, failures {bad}")
    bad = total = 0
    for t in range(200):
        n = rng.randint(1, 40)
        inst = H.generate(n, random.Random(f"ppm-transpose|{t}"))
        bad += oracle(*inst) != oracle(*transpose(*inst))
        total += 1
    print(f"(c) DP(instance) == DP(transposed instance): {total} instances, failures {bad}")
    bad = total = 0
    for a in range(1, 11):
        for b in range(1, 11):
            bad += oracle(*unit(a, b)) != round(cosine_product(a, b))
            total += 1
    print(f"(d) unit rectangles a, b = 1..10: DP == round(cosine product): failures {bad} of {total}; "
          f"8 x 8 = {oracle(*unit(8, 8))}, 10 x 10 = {oracle(*unit(10, 10))}")
    bad = total = 0
    for t in range(150):
        n = rng.choice([2, 4, 6, 8, 9, 10, 12, 14, 15, 16])
        inst = H.generate(n, random.Random(f"ppm-perm|{t}"))
        a, b, W = inst
        if (a * b) % 2:
            continue
        bad += permanent(unsigned_biadjacency(a, b, W)) != oracle(*inst)
        total += 1
    print(f"(e) permanent of the black x white weight matrix == DP (even N <= 16): {total} instances, failures {bad}")


def part4_signing():
    section("4. The implementation's Kasteleyn signs: every unit square has sign product -1")
    squares = bad = pattern_bad = 0
    for a in range(2, 13):
        for b in range(2, 13):
            if (a * b) % 2:
                continue
            inst = unit(a, b)
            K = kasteleyn_matrix(inst)
            black, white = colour_classes(a, b)
            bi = {x: i for i, x in enumerate(black)}
            wi = {y: j for j, y in enumerate(white)}

            def entry(u, v):
                x, y = (u, v) if u in bi else (v, u)
                return K[bi[x]][wi[y]]

            for r in range(a - 1):
                for c in range(b - 1):
                    u = r * b + c
                    p = entry(u, u + 1) * entry(u, u + b) * entry(u + 1, u + 1 + b) * entry(u + b, u + b + 1)
                    squares += 1
                    bad += p != -1
            edges = set(H._grid_edges(a, b))
            for x in black:
                for y in white:
                    on_edge = (min(x, y), max(x, y)) in edges
                    pattern_bad += (K[bi[x]][wi[y]] != 0) != on_edge
    print(f"unit grids a, b = 2..12 with a*b even: {squares} unit squares, sign product != -1: {bad}; "
          f"non-zero pattern of K != grid edges: {pattern_bad} entries")


def part5_negative_controls():
    section("5. Negative controls: the signs do real work")
    unsigned_bad = signed_neg = wrong_sign_bad = gauge_equal = total = 0
    first_unsigned = None
    signs_by_shape = {}
    for n in range(2, 49, 2):
        for t in range(20):
            inst = H.generate(n, random.Random(f"ppm-negative|{n}|{t}"))
            a, b, W = inst
            ans = oracle(*inst)
            K = kasteleyn_matrix(inst)
            dk = det_fraction(K)
            du = det_fraction(unsigned_biadjacency(a, b, W))
            dw = det_fraction(all_vertical_negative(a, b, W))
            total += 1
            signed_neg += dk < 0
            if dk:
                signs_by_shape.setdefault((a, b), set()).add(dk > 0)
            if abs(du) != ans:
                unsigned_bad += 1
                if first_unsigned is None:
                    first_unsigned = (describe(inst), ans, du)
            wrong_sign_bad += abs(dw) != ans
            gauge_equal += abs(dw) == abs(du)
            assert abs(dk) == ans
    print(f"{total} instances (even n = 2..48, 20 each): |det K| == answer in all")
    negative_shapes = sorted(s for s, v in signs_by_shape.items() if v == {False})
    mixed = sorted(s for s, v in signs_by_shape.items() if len(v) > 1)
    print(f"  det K < 0 (the absolute value is needed): {signed_neg}; shapes with a non-zero det: "
          f"{len(signs_by_shape)}, shapes whose sign differs between instances: {len(mixed)} {mixed}; "
          f"always-negative shapes: {negative_shapes}")
    print(f"  |det| of the UNSIGNED black x white matrix != answer: {unsigned_bad}; first: {first_unsigned}")
    print(f"  |det| with -1 on EVERY vertical edge (square products +1) != answer: {wrong_sign_bad}; "
          f"equal to |unsigned det| in {gauge_equal} of {total} (gauge-equivalent: scale black rows and white "
          f"columns of grid row r by (-1)^r)")
    B = unsigned_biadjacency(*unit(2, 2))
    print(f"  2 x 2 unit grid: unsigned matrix {B}, det {det_fraction(B)}, answer {oracle(*unit(2, 2))}")
    ladder_bad = sum(abs(det_fraction(unsigned_biadjacency(*unit(m, 2)))) != FIB[m + 1] for m in range(2, 31))
    print(f"  unit m x 2 ladders, m = 2..30: |unsigned det| != F(m+1) for {ladder_bad} of 29")


def part6_oracle_control():
    section("6. Oracle control: harness.check must reject wrong outputs and accept correct ones")
    tallies = {}

    def record(name, accepted, should):
        t = tallies.setdefault(name, [0, 0, 0])  # presented, accepted, wrong verdicts
        t[0] += 1
        t[1] += accepted
        t[2] += accepted != should

    for n in list(range(0, 41)) + [48, 64, 81, 100]:
        for t in range(6):
            inst = H.generate(n, random.Random(f"ppm-oracle-control|{n}|{t}"))
            a, b, W = inst
            ans = enum_count(inst) if n <= 40 else kasteleyn(inst)
            record("correct answer (int)", H.check(inst, ans) is True, True)
            record("answer + 1", H.check(inst, ans + 1) is True, False)
            record("answer - 1", H.check(inst, ans - 1) is True, False)
            if ans:
                record("2 * answer (answer > 0)", H.check(inst, 2 * ans) is True, False)
            record("float(answer)", H.check(inst, float(ans)) is True, False)
            if ans in (0, 1):
                record("bool(answer) (answer 0 or 1)", H.check(inst, bool(ans)) is True, False)
            if a * b and (a * b) % 2 == 0:
                dk = det_fraction(kasteleyn_matrix(inst))
                if dk != ans:
                    record("signed det K without abs (where != answer)", H.check(inst, dk) is True, False)
                du = det_fraction(unsigned_biadjacency(a, b, W))
                if abs(du) != ans:
                    record("|det| of the unsigned matrix (where != answer)", H.check(inst, abs(du)) is True, False)
                if du != ans:
                    record("det of the unsigned matrix (where != answer)", H.check(inst, du) is True, False)
            full = oracle(*unit(a, b))
            if full != ans:
                record("unit-weight count ignoring W (where != answer)", H.check(inst, full) is True, False)
    for name, (presented, accepted, wrong) in tallies.items():
        print(f"  {name:48s} presented {presented:4d}  accepted {accepted:4d}  wrong verdicts {wrong}")
    wrong_presented = sum(p for name, (p, _, _) in tallies.items() if not name.startswith("correct"))
    wrong_accepted = sum(acc for name, (_, acc, _) in tallies.items() if not name.startswith("correct"))
    print(f"total wrong outputs presented {wrong_presented}, accepted {wrong_accepted}; correct outputs "
          f"presented {tallies['correct answer (int)'][0]}, accepted {tallies['correct answer (int)'][1]}")


def part7_counts():
    section("7. Exact operation counts of the unchanged implementations (harness CountingInt)")
    bad = 0
    for n in range(2, 61, 2):
        inst = H.generate_scaling(n, None)
        r = enum_count(inst)
        bad += H.reported_cost(r) != enum_ladder_closed_form(n) or int(r) != FIB[n // 2 + 1]
    print(f"enumeration on the (n/2) x 2 ladder, n = 2..60 even: count == L(n/2+2) - 3 and answer == F(n/2+1): "
          f"failures {bad} of 30")
    print("  n=16..52 step 4: " + ", ".join(f"{n}: {enum_ladder_closed_form(n)}" for n in range(16, 53, 4)))
    bad = 0
    rows = []
    for m in range(1, 25):
        a, b, W = H.ladder(m)
        a, b, W = transpose(a, b, W)  # 2 x m
        H._ops = 0
        r = enum_count((a, b, tuple(tuple(H.CountingInt(x) for x in row) for row in W)))
        c = H.reported_cost(r)
        bad += c != enum_wide_ladder_closed_form(m)
        if m in (8, 12, 16, 20, 24):
            rows.append(f"m={m}: 2 x m {c} vs m x 2 {enum_ladder_closed_form(2 * m)}")
    print(f"enumeration on the 2 x m ladder (row-major), m = 1..24: count == F(m+3) - 2 + ((m-1)F(m) + 2mF(m-1))/5: "
          f"failures {bad} of 24")
    print("  " + "; ".join(rows))
    bad = 0
    for n in list(range(2, 121, 2)) + [256]:
        inst = H.generate_scaling(n, None)
        r = kasteleyn(inst)
        bad += H.reported_cost(r) != kasteleyn_closed_form(n) or int(r) != FIB[n // 2 + 1]
    print(f"Kasteleyn on the (n/2) x 2 ladder, n = 2..120 even and 256: count == (n-2)n(n-1)/8 and answer == "
          f"F(n/2+1): failures {bad} of 61")
    print("  n = 16, 32, 64, 128, 256: " + ", ".join(str(kasteleyn_closed_form(n)) for n in (16, 32, 64, 128, 256)))
    same = differ = swaps = zero = zero_le = 0
    zero_examples = []
    for t in range(400):
        n = random.Random(f"ppm-count-n|{t}").choice([4, 6, 8, 10, 12, 16, 18, 20, 24, 30, 36, 40, 48, 60, 64])
        inst = H.generate(n, random.Random(f"ppm-count|{t}"))
        a, b, W = inst
        if (a * b) % 2:
            continue
        K = kasteleyn_matrix(inst)
        H._ops = 0
        r = kasteleyn((a, b, tuple(tuple(H.CountingInt(x) for x in row) for row in W)))
        c = H.reported_cost(r)
        if int(r) != 0:
            if c == kasteleyn_closed_form(a * b):
                same += 1
            else:
                differ += 1
            swaps += needs_row_swap(K)
        else:
            zero += 1
            zero_le += c <= kasteleyn_closed_form(a * b)
            if len(zero_examples) < 4:
                zero_examples.append(f"{a}x{b}: {c} of {kasteleyn_closed_form(a * b)}")
    print(f"Kasteleyn on random even-N instances of all kinds and shapes (N <= 64): non-zero answers {same + differ}, "
          f"count == (N-2)N(N-1)/8 in {same}, different in {differ}; {swaps} of them needed a row swap")
    print(f"  zero answers: {zero}, count <= closed form in {zero_le}; e.g. {zero_examples}")


def part8_fits():
    section("8. Fits with the validator's eval_cost / fit_slope at the declared n_values")
    for alg in ENTRY_JSON["algorithms"]:
        sc = alg["harness"]["scaling"]
        ns = sc["n_values"]
        fn = load_fn(alg["implementation"])
        values = []
        for n in ns:
            inst = H.generate_scaling(n, None)
            values.append(H.reported_cost(fn(inst)))
        ys = [math.log(v) for v in values]

        def alpha(cost):
            return V.fit_slope([math.log(V.eval_cost(cost, n)) for n in ns], ys)

        print(f"{alg['name']}: n_values {ns}\n  counts {values}")
        print(f"  claim {sc['cost']}: alpha = {alpha(sc['cost']):.4f} (tolerance {sc['tolerance']})")
        for rv in sc.get("rivals", []):
            a_r = alpha(rv)
            print(f"  rival {rv}: alpha = {a_r:.4f} (|alpha-1| = {abs(a_r - 1):.4f})")
        extras = ["phi**(n/2)"] if "phi" in sc["cost"] else ["n**3"]
        for ex in extras:
            print(f"  (bare form, not a rival) {ex}: alpha = {alpha(ex):.4f}")
        up = V.fit_slope([math.log(V.eval_cost(sc["cost"], n)) + math.log(math.log(n)) for n in ns], ys)
        down = V.fit_slope([math.log(V.eval_cost(sc["cost"], n)) - math.log(math.log(n)) for n in ns], ys)
        print(f"  diagnostic: vs cost*log n {up:.4f}, vs cost/log n {down:.4f}")


def load_fn(spec):
    file_part, func = spec.rsplit(":", 1)
    return getattr(EN if "enumeration" in file_part else KB, func)


class BitTracker:
    """Records the largest absolute value created by * and - (before the exact division) and by //
    (values stored in the matrix)."""
    __slots__ = ("v",)
    max_stored = 0
    max_intermediate = 0

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, BitTracker) else x

    def _inter(self, v):
        BitTracker.max_intermediate = max(BitTracker.max_intermediate, abs(v))
        return BitTracker(v)

    def __mul__(self, o):
        return self._inter(self.v * self._val(o))

    __rmul__ = __mul__

    def __sub__(self, o):
        return self._inter(self.v - self._val(o))

    def __rsub__(self, o):
        return self._inter(self._val(o) - self.v)

    def __add__(self, o):
        return self._inter(self.v + self._val(o))

    __radd__ = __add__

    def __floordiv__(self, o):
        q = self.v // self._val(o)
        BitTracker.max_stored = max(BitTracker.max_stored, abs(q))
        return BitTracker(q)

    def __neg__(self):
        return BitTracker(-self.v)

    def __abs__(self):
        return BitTracker(abs(self.v))

    def __eq__(self, o):
        return self.v == self._val(o)

    def __ne__(self, o):
        return self.v != self._val(o)

    def __bool__(self):
        return self.v != 0

    def __int__(self):
        return int(self.v)

    __hash__ = None


def part9_bits():
    section("9. Bit sizes inside Bareiss vs the Hadamard bounds B = (2 w_max)^m and 2 B^2, m = N/2")
    rng = random.Random("ppm-bits")
    cases = [unit(8, 8), unit(10, 10), unit(12, 12), unit(2, 60), unit(1, 64)]
    for a, b in [(8, 8), (10, 10), (6, 12)]:
        cases.append((a, b, H._matrix(a, b, lambda: rng.randint(1, 10 ** 9))))
    violations = 0
    for inst in cases:
        a, b, W = inst
        wmax = max(max(row) for row in W)
        m = a * b // 2
        BitTracker.max_stored = BitTracker.max_intermediate = 0
        out = kasteleyn((a, b, tuple(tuple(BitTracker(x) for x in row) for row in W)))
        stored_bound = m * math.log2(2 * wmax)
        inter_bound = 1 + 2 * stored_bound
        sb = BitTracker.max_stored.bit_length()
        ib = BitTracker.max_intermediate.bit_length()
        violations += BitTracker.max_stored > (2 * wmax) ** m or BitTracker.max_intermediate > 2 * (2 * wmax) ** (2 * m)
        print(f"  {a}x{b} w_max={wmax}: answer {int(out).bit_length()} bits; stored max {sb} bits "
              f"(bound {stored_bound:.1f}); before division max {ib} bits (bound {inter_bound:.1f})")
    print(f"bound violations: {violations}")


def main():
    try:
        from search.machine import set_below_normal_priority
        print(f"below-normal priority: {set_below_normal_priority()}")
    except Exception as e:  # noqa: BLE001
        print(f"priority not lowered: {e}")
    part1_v1_battery()
    part2_extended()
    part3_oracle_selfchecks()
    part4_signing()
    part5_negative_controls()
    part6_oracle_control()
    part7_counts()
    part8_fits()
    part9_bits()


if __name__ == "__main__":
    main()
