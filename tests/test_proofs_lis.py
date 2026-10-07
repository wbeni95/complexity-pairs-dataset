"""Checks of the proofs in pairs/longest-increasing-subsequence/PROOFS.md (sections 4 to 9).

Every test runs the UNCHANGED implementations (or the entry's harness) on fixed inputs and seeds, or on all inputs of
the stated small sizes. The patience invariant is read from the unchanged function's local variables at its return
(sys.settrace). The written proofs cover the general statements; these tests re-run their computable facts.
"""
import importlib.util
import itertools
import math
import random
import sys
import tracemalloc
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "longest-increasing-subsequence"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load(ENTRY / "harness.py", "proofs_lis_harness")
SUBSETS = load(ENTRY / "implementations" / "subset_enumeration.py", "proofs_lis_sub").lis_subsets
DP = load(ENTRY / "implementations" / "quadratic_dp.py", "proofs_lis_dp").lis_quadratic
PATIENCE = load(ENTRY / "implementations" / "patience.py", "proofs_lis_pat").lis_patience


def lis_brute(a):
    """Longest strictly increasing subsequence by trying index subsets from the largest size down (independent code)."""
    n = len(a)
    for k in range(n, 0, -1):
        for idx in itertools.combinations(range(n), k):
            if all(a[idx[t]] < a[idx[t + 1]] for t in range(k - 1)):
                return k
    return 0


def lcs(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b, 1):
            cur[j] = prev[j - 1] + 1 if x == y else max(prev[j], cur[j - 1])
        prev = cur
    return prev[-1]


def locals_at_return(fn, arg):
    captured = {}

    def tracer(frame, event, _arg):
        if frame.f_code is fn.__code__:
            def local(fr, ev, a):
                if ev == "return":
                    captured.update(fr.f_locals)
                return local
            return local
        return None

    old = sys.gettrace()
    sys.settrace(tracer)
    try:
        out = fn(arg)
    finally:
        sys.settrace(old)
    return out, captured


def count(fn, xs):
    keys = [H.CountingKey(x) for x in xs]
    H._comparisons = 0
    out = fn(keys)
    return H._comparisons, out


def peak_bytes(fn, arg):
    tracemalloc.start()
    try:
        base = tracemalloc.get_traced_memory()[0]
        out = fn(arg)
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    del out
    return peak


class CorrectnessTests(unittest.TestCase):
    """PROOFS.md sections 4 to 6: all three agree with an independent brute force on every list of length <= 7 over
    {0, 1, 2, 3} (subset enumeration up to length 6), and the DP and patience sorting agree on seeded lists up to
    n = 2000; the LCS reduction of the V1 oracle (section 8) holds on the same exhaustive range."""

    def test_exhaustive(self):
        for n in range(8):
            for a in itertools.product(range(4), repeat=n):
                want = lis_brute(a)
                self.assertEqual(DP(a), want, a)
                self.assertEqual(PATIENCE(a), want, a)
                self.assertEqual(lcs(a, sorted(set(a))), want, a)
                if n <= 6:
                    self.assertEqual(SUBSETS(a), want, a)

    def test_random(self):
        for n in (50, 100, 500, 2000):
            for seed in range(3):
                a = H.generate(n, random.Random(f"lis-proofs|{n}|{seed}"))
                self.assertEqual(PATIENCE(a), DP(a), n)


class PatienceInvariantTests(unittest.TestCase):
    """PROOFS.md section 6: after every prefix, the list `tails` of the unchanged function (read at its return) is
    strictly increasing and tails[k] is the least last element of a strictly increasing subsequence of length k + 1
    of the prefix (computed independently from the lengths L[i] of the best subsequences ending at i). Every prefix
    of 3 seeded lists for each n = 1..60, values with many ties."""

    def test_invariant(self):
        for n in range(1, 61):
            for seed in range(3):
                rng = random.Random(f"lis-inv|{n}|{seed}")
                a = [rng.randint(0, max(1, n // 3)) for _ in range(n)]
                for m in range(1, n + 1):
                    prefix = a[:m]
                    _, loc = locals_at_return(PATIENCE, prefix)
                    tails = loc["tails"]
                    L = []
                    for i, x in enumerate(prefix):
                        L.append(1 + max([L[j] for j in range(i) if prefix[j] < x], default=0))
                    want = [min(x for x, l in zip(prefix, L) if l >= k + 1) for k in range(max(L))]
                    self.assertEqual(tails, want, (n, seed, m))
                    self.assertTrue(all(tails[k] < tails[k + 1] for k in range(len(tails) - 1)))


class PatienceCostTests(unittest.TestCase):
    """PROOFS.md section 7: (a) on every input, patience sorting makes at most n (1 + log2 L) comparisons (seeded
    harness inputs, n = 1..300 and 1000, 5000); (b) the cost is not Theta(n log L) on every input: a decreasing run of
    n - L elements followed by L larger increasing ones has answer L + 1 and costs exactly
    (n - L - 1) + sum_{j=2..L+1} floor(log2 j) comparisons, below n log2 L / 3 for n = 10000, 40000 with L = floor(sqrt n);
    (c) the listed constants c = (n log2 n - count) / n of the increasing input are 1.9246, 1.9644, 1.9202, 1.9422 at
    n = 10000, 30000, 100000, 300000 (from the exact count, PROOFS.md section 3)."""

    def test_upper_bound(self):
        for n in list(range(1, 301)) + [1000, 5000]:
            a = H.generate(n, random.Random(f"lis-cost|{n}"))
            c, L = count(PATIENCE, a)
            self.assertLessEqual(c, n * (1 + math.log2(L)) + 1e-9, n)

    def test_not_theta_n_log_l(self):
        for n in (10000, 40000):
            L = math.isqrt(n)
            m = n - L
            a = list(range(m, 0, -1)) + list(range(m + 1, m + L + 1))
            c, ans = count(PATIENCE, a)
            self.assertEqual(ans, L + 1)
            self.assertEqual(c, (m - 1) + sum(int(math.log2(j)) for j in range(2, L + 2)))
            self.assertLess(c, n * math.log2(L) / 3)

    def test_listed_constants(self):
        def exact(n):
            K = n.bit_length() - 1
            return (n + 1) * K - 2 ** (K + 1) + 2
        for n, c in ((10000, 1.9246), (30000, 1.9644), (100000, 1.9202), (300000, 1.9422)):
            self.assertEqual(round((n * math.log2(n) - exact(n)) / n, 4), c)


class SpaceTests(unittest.TestCase):
    """PROOFS.md section 9. Subset enumeration: peak traced allocation at most 2048 bytes for n = 6..14. DP: between
    8 n and 40 n + 4096 bytes (one list slot per position, plus at most one int object per position for lengths above
    the small-int cache), n = 200..3200 doubling, 3 seeded inputs each. Patience: between 8 L and 16 L + 4096 bytes on
    increasing input (L = n = 10^4..8 * 10^4; the list grows by appends), and at most 2048 bytes on a constant input of
    length 10^5 (L = 1)."""

    def test_subsets(self):
        for n in range(6, 15):
            a = H.generate(n, random.Random(f"lis-space|{n}"))
            self.assertLessEqual(peak_bytes(SUBSETS, a), 2048, n)

    def test_dp(self):
        for n in (200, 400, 800, 1600, 3200):
            for seed in range(3):
                a = H.generate(n, random.Random(f"lis-space|{n}|{seed}"))
                peak = peak_bytes(DP, a)
                self.assertTrue(8 * n <= peak <= 40 * n + 4096, (n, seed, peak))

    def test_patience(self):
        for n in (10000, 20000, 40000, 80000):
            peak = peak_bytes(PATIENCE, list(range(n)))
            self.assertTrue(8 * n <= peak <= 16 * n + 4096, (n, peak))
        self.assertLessEqual(peak_bytes(PATIENCE, [7] * 100000), 2048)


if __name__ == "__main__":
    unittest.main()
