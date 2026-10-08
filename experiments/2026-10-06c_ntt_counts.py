"""Exact multiplication counts for pairs/polynomial-multiplication-naive-vs-ntt (count-based V2, round 2026-10-06c).

What it tries:
  1. Whether the UNCHANGED implementations return the same coefficients on CountingCoeff inputs as on plain
     ints (scaling sizes and 200 random generate() instances, including non-powers of two).
  2. Which multiplications the instrumented type sees. A second, experiment-only type `Probe` counts the
     multiplications in which BOTH operands are input-derived separately from those with one plain-int
     operand, to show that the NTT butterfly products a[k + half] * w have a plain twiddle factor w.
  3. Whether the counts equal closed forms:
       schoolbook: n^2 (every a * b; `if a:` skips zero coefficients, and none of the scaling draws is 0);
       NTT on n = 2^m (size N = 2n, K = log2 N stages): forward transforms (K - 1) N / 2 each (stage 1 has a
       padding zero in every butterfly, so its product is plain int * plain int), pointwise N, inverse
       K N / 2 plus N scalings: total 3 n log2(n) + 5 n.
  4. Fits for the claims and rivals (validator's eval_cost / fit_slope).

Run from the repository root:  PYTHONIOENCODING=utf-8 ./.venv/Scripts/python experiments/2026-10-06c_ntt_counts.py
Deterministic.

Outcome (run 2026-10-06, Python 3.14.2; identical counts under 3.12.10, see 2026-10-06c_count_v2_summary.py):
  1. Identical coefficients on all 203 instances (200 random + 3 scaling), both algorithms.
  2. Schoolbook: all n^2 products have two input-derived operands. NTT: only the 2n pointwise products have
     two input-derived operands (16 / 1024 / 8192 at n = 8 / 512 / 4096); every other counted product has one
     plain-int operand, 96 / 15360 / 159744 of them: the butterfly products with the twiddle w (80 / 14336 /
     151552) and the 2n scalings by n_inv (16 / 1024 / 8192). Twiddle updates w * w_len are not seen.
  3. NTT count == 3 n log2 n + 5 n exactly for n = 2^3..2^15; schoolbook == n^2 for n = 2^3..2^10 and on the
     scaling n = 100..800 (no zero coefficient among the scaling draws).
  4. Schoolbook vs n**2: alpha 1.0000; rivals n*log(n) 1.6966, n**2*log(n) 0.9179, rejected at 0.03.
     NTT vs leading term n*log(n): alpha 0.9854 (|alpha - 1| = 0.0146, local slopes 0.980..0.989);
     NTT vs exact form n*(3*log2(n) + 5): alpha 1.0000; rivals n 1.1107, n*log(n)**2 0.8855, n**2 0.5553,
     all rejected. CHOSEN: the exact form (RL-062), because the leading term's deviation is about half the
     tolerance.

Check lines start with [PASS] or [FAIL]: 1; every probe line of 2 (schoolbook: all n^2 products with two
input-derived operands; NTT: exactly the 2n pointwise products, n a power of two); both lines of 3 (including that
no scaling draw is zero). The run ends with ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1).
The butterfly product counts and the fits (4) are reported, not checked.
"""
import importlib.util
import random
import sys
from pathlib import Path

_s = importlib.util.spec_from_file_location("cv2h", Path(__file__).resolve().parent / "2026-10-07b_count_v2_helpers.py")
H = importlib.util.module_from_spec(_s)
_s.loader.exec_module(H)

E = "polynomial-multiplication-naive-vs-ntt"
entry_dir, entry, harness = H.entry_and_harness(E)
naive = H.V.load_callable(entry_dir, "implementations/naive.py:polymul_naive")
ntt = H.V.load_callable(entry_dir, "implementations/ntt.py:polymul_ntt")
CC = harness.CountingCoeff

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


def unwrap(c):
    return [x.v if isinstance(x, CC) else x for x in c]


# 1. answers unchanged
rng = random.Random("ntt-eq")
differs = []
for t in range(200):
    n = rng.choice([1, 2, 3, 5, 8, 9, 16, 17, 31, 64, 100])
    A, B = harness.generate(n, rng)
    cA, cB = tuple(CC(x) for x in A), tuple(CC(x) for x in B)
    for fn in (naive, ntt):
        if unwrap(fn((cA, cB))) != fn((A, B)):
            differs.append((t, n, fn.__name__))
for n in [512, 1024, 2048]:
    A, B = harness.generate(n, random.Random(f"ntt-eq|{n}"))
    cA, cB = tuple(CC(x) for x in A), tuple(CC(x) for x in B)
    for fn in (naive, ntt):
        if unwrap(fn((cA, cB))) != fn((A, B)):
            differs.append((n, fn.__name__))
check_line(not differs, "answers on CountingCoeff inputs == answers on plain ints: "
           + ("OK" if not differs else f"DIFFER at {differs[:5]}") + " (200 random + n = 512, 1024, 2048)")


# 2. what is seen: both operands input-derived vs one plain operand
class Probe:
    both = 0
    one = 0
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _u(x):
        return x.v if isinstance(x, Probe) else x

    def __mul__(self, o):
        if isinstance(o, Probe):
            Probe.both += 1
        else:
            Probe.one += 1
        return Probe(self.v * self._u(o))

    __rmul__ = __mul__

    def __add__(self, o):
        return Probe(self.v + self._u(o))

    __radd__ = __add__

    def __sub__(self, o):
        return Probe(self.v - self._u(o))

    def __rsub__(self, o):
        return Probe(self._u(o) - self.v)

    def __mod__(self, o):
        return Probe(self.v % self._u(o))

    def __bool__(self):
        return bool(self.v)


for n in [8, 512, 4096]:
    A, B = harness.generate(n, random.Random(f"ntt-probe|{n}"))
    for name, fn in (("schoolbook", naive), ("NTT", ntt)):
        Probe.both = Probe.one = 0
        fn((tuple(Probe(x) for x in A), tuple(Probe(x) for x in B)))
        expected = (Probe.both == n * n and Probe.one == 0) if name == "schoolbook" else Probe.both == 2 * n
        check_line(expected, f"n={n:5d} {name:10s}: products with both operands input-derived = {Probe.both}, "
                             f"with one plain-int operand = {Probe.one}")

# 3. closed forms
bad = []
for n in [1 << m for m in range(3, 16)]:
    rng = random.Random(f"{E}|v2|{n}")
    inst = harness.generate_scaling(n, rng)
    zeros = sum(1 for c in inst[0] if c.v == 0)
    if zeros != 0:
        bad.append((n, "zero coefficient drawn"))
    c_ntt = harness.reported_cost(ntt(inst))
    m = n.bit_length() - 1
    if c_ntt != 3 * n * m + 5 * n:
        bad.append((n, "NTT", c_ntt))
    if n <= 1024:
        inst = harness.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
        if harness.reported_cost(naive(inst)) != n * n:
            bad.append((n, "schoolbook"))
check_line(not bad, "NTT count == 3 n log2 n + 5 n for n = 2^3..2^15; schoolbook count == n^2 for n = 2^3..2^10"
           + (f"; FAILS: {bad[:5]}" if bad else ""))
bad = []
for n in [100, 200, 300, 400, 600, 800]:
    inst = harness.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
    if harness.reported_cost(naive(inst)) != n * n:
        bad.append(n)
check_line(not bad, "schoolbook count == n^2 on the scaling n_values 100..800 (no zero coefficient drawn)"
           + (f"; FAILS at n = {bad}" if bad else ""))

# 4. fits
TOL = 0.03
ns = [100, 200, 300, 400, 600, 800]
vals = H.counts(E, "schoolbook convolution", ns)
H.report("schoolbook vs n**2", ns, vals, "n**2", ["n*log(n)", "n**2*log(n)"], TOL)
ns = [512, 1024, 2048, 4096, 8192, 16384]
vals = H.counts(E, "number-theoretic transform (Cooley-Tukey over Z_p)", ns)
H.report("NTT vs leading term", ns, vals, "n*log(n)", ["n", "n*log(n)**2", "n**2"], TOL)
H.report("NTT vs exact form", ns, vals, "n*(3*log2(n) + 5)", ["n", "n*log(n)**2", "n**2"], TOL)

finish_checks()
