"""Checks of the proofs in pairs/longest-palindromic-substring/PROOFS.md.

Every test runs the UNCHANGED implementations on fixed inputs and seeds, or on all strings of the stated small sizes.
Character comparisons are counted (and attributed to positions) by passing a list of instrumented characters: the
implementations only use len(), indexing and ==. Manacher's radius arrays are read from the unchanged function's local
variables at its return (sys.settrace). The written proofs cover the general statements; these tests re-run their
computable facts.
"""
import importlib.util
import itertools
import random
import sys
import tracemalloc
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "longest-palindromic-substring"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load(ENTRY / "harness.py", "proofs_pal_harness")
BRUTE = load(ENTRY / "implementations" / "brute_force.py", "proofs_pal_brute").lps_brute
EXPAND = load(ENTRY / "implementations" / "expand_centers.py", "proofs_pal_expand").lps_expand
MANACHER = load(ENTRY / "implementations" / "manacher.py", "proofs_pal_manacher").lps_manacher


class Ch:
    """A character that logs every == it takes part in as (position, position, outcome)."""
    __slots__ = ("c", "p")
    log = []

    def __init__(self, c, p):
        self.c, self.p = c, p

    def __eq__(self, other):
        r = self.c == other.c
        Ch.log.append((self.p, other.p, r))
        return r

    __hash__ = None


def run(fn, s):
    Ch.log = []
    out = fn([Ch(c, i) for i, c in enumerate(s)])
    return out, Ch.log


def is_pal(w):
    return w == w[::-1]


def oracle(s):
    n = len(s)
    for L in range(n, 0, -1):
        for i in range(n - L + 1):
            if is_pal(s[i:i + L]):
                return L, i
    return 0, 0


def radii(s):
    """d1[i] = number of odd palindromes centred at i; d2[i] = number of even palindromes centred before i."""
    n = len(s)
    d1 = [max(k for k in range(1, n + 1) if i - k + 1 >= 0 and i + k - 1 < n and is_pal(s[i - k + 1:i + k]))
          for i in range(n)]
    d2 = [max(k for k in range(0, n + 1) if i - k >= 0 and i + k - 1 < n and is_pal(s[i - k:i + k])) for i in range(n)]
    return d1, d2


def radii_fast(s):
    """The same radii by direct expansion at every centre (O(n^2); independent code, used for n up to 1000)."""
    n = len(s)
    d1, d2 = [], []
    for i in range(n):
        k = 1
        while i - k >= 0 and i + k < n and s[i - k] == s[i + k]:
            k += 1
        d1.append(k)
        k = 0
        while i - k - 1 >= 0 and i + k < n and s[i - k - 1] == s[i + k]:
            k += 1
        d2.append(k)
    return d1, d2


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


def all_strings(alphabet, nmax):
    for n in range(nmax + 1):
        for t in itertools.product(alphabet, repeat=n):
            yield "".join(t)


class CorrectnessTests(unittest.TestCase):
    """PROOFS.md sections 4 and 6: all three return (L, leftmost start) on every string over {a, b} of length <= 12 and
    over {a, b, c} of length <= 8, and on seeded harness strings up to n = 400 (brute force up to 80)."""

    def test_exhaustive(self):
        for s in itertools.chain(all_strings("ab", 12), all_strings("abc", 8)):
            want = oracle(s)
            self.assertEqual(BRUTE(s), want, s)
            self.assertEqual(EXPAND(s), want, s)
            self.assertEqual(MANACHER(s), want, s)

    def test_random(self):
        for n in (20, 40, 80, 150, 400):
            for seed in range(6):
                s = H.generate(n, random.Random(f"pal-proofs|{n}|{seed}"))
                want = oracle(s)
                if n <= 80:
                    self.assertEqual(BRUTE(s), want, n)
                self.assertEqual(EXPAND(s), want, n)
                self.assertEqual(MANACHER(s), want, n)


class WorstCaseCountTests(unittest.TestCase):
    """PROOFS.md sections 1, 2 and 5: on a^n, brute force makes sum_{L=1..n} (n - L + 1) floor(L/2) comparisons
    (n = 0..60), expansion n(n + 1)/2 (n = 0..300), Manacher 2n - 3 for n >= 2 and 0 for n <= 1 (n = 0..2000), every
    comparison succeeding; Manacher's odd scan makes n - 2 and its even scan n - 1 (n >= 2)."""

    def test_counts(self):
        for n in range(61):
            _, log = run(BRUTE, "a" * n)
            self.assertEqual(len(log), sum((n - L + 1) * (L // 2) for L in range(1, n + 1)), n)
        for n in range(301):
            _, log = run(EXPAND, "a" * n)
            self.assertEqual(len(log), n * (n + 1) // 2, n)
        for n in range(2001):
            _, log = run(MANACHER, "a" * n)
            self.assertTrue(all(r for _, _, r in log))
            odd = sum(1 for p, q, _ in log if (p + q) % 2 == 0)
            if n >= 2:
                self.assertEqual((len(log), odd, len(log) - odd), (2 * n - 3, n - 2, n - 1), n)
            else:
                self.assertEqual(len(log), 0, n)


class EveryInputBoundTests(unittest.TestCase):
    """PROOFS.md sections 1, 2, 5: on every string over {a, b} of length <= 11 and over {a, b, c} of length <= 7, and on
    seeded harness strings (n = 100, 400, 1000; Manacher also n = 5000): brute force makes at least n(n - 1)/2
    comparisons (n <= 100); expansion compares every pair (lo, hi) at most once, makes between n + R and 3n - 1 + R
    comparisons (R the sum of the radii, from the definition for n <= 12 and by direct expansion in the test above) and
    at most n(n + 1)/2 (n <= 1000); in each Manacher scan at most n comparisons succeed and at most n fail."""

    def _check(self, s, brute=True, expand=True):
        n = len(s)
        if brute:
            _, log = run(BRUTE, s)
            self.assertGreaterEqual(len(log), n * (n - 1) // 2, s)
        if expand:
            _, log = run(EXPAND, s)
            pairs = [(min(p, q), max(p, q)) for p, q, _ in log]
            self.assertEqual(len(pairs), len(set(pairs)), s)
            self.assertLessEqual(len(log), n * (n + 1) // 2)
        if expand:
            d1, d2 = radii(s) if n <= 12 else radii_fast(s)
            R = sum(d - 1 for d in d1) + sum(d2)
            self.assertTrue(n + R <= len(log) <= max(3 * n - 1, 0) + R, s)
        _, log = run(MANACHER, s)
        for parity in (0, 1):
            outcomes = [r for p, q, r in log if (p + q) % 2 == parity]
            self.assertLessEqual(sum(outcomes), n, s)
            self.assertLessEqual(len(outcomes) - sum(outcomes), n, s)

    def test_exhaustive(self):
        for s in itertools.chain(all_strings("ab", 11), all_strings("abc", 7)):
            self._check(s)

    def test_random(self):
        for n in (100, 400, 1000, 5000):
            for seed in range(6):
                self._check(H.generate(n, random.Random(f"pal-every|{n}|{seed}")), brute=n <= 100, expand=n <= 1000)


class ExpectationTests(unittest.TestCase):
    """PROOFS.md sections 1 and 2: exact expectations over uniformly random strings, by enumerating all strings: the
    expansion's expected count lies in [n, 5n - 2] for n = 1..14 over {a, b} and n = 1..9 over {a, b, c}; brute force's
    expected count lies in [n(n - 1)/2, n(n - 1)] for n = 1..10 over {a, b} and n = 1..7 over {a, b, c}."""

    def test_expand(self):
        for alphabet, nmax in (("ab", 14), ("abc", 9)):
            for n in range(1, nmax + 1):
                total = sum(len(run(EXPAND, "".join(t))[1]) for t in itertools.product(alphabet, repeat=n))
                mean = Fraction(total, len(alphabet) ** n)
                self.assertTrue(n <= mean <= 5 * n - 2, (alphabet, n, mean))

    def test_brute(self):
        for alphabet, nmax in (("ab", 10), ("abc", 7)):
            for n in range(1, nmax + 1):
                total = sum(len(run(BRUTE, "".join(t))[1]) for t in itertools.product(alphabet, repeat=n))
                mean = Fraction(total, len(alphabet) ** n)
                self.assertTrue(Fraction(n * (n - 1), 2) <= mean <= n * (n - 1), (alphabet, n, mean))


class ManacherRadiusTests(unittest.TestCase):
    """PROOFS.md sections 3 and 7: the unchanged function's d1 and d2 (read at its return) equal the maximal radii
    computed from the definition, and sum(d1) + sum(d2) equals the number of palindromic substrings (occurrences);
    every string over {a, b} of length 1..10 and over {a, b, c} of length 1..6, and seeded harness strings n = 50."""

    def _check(self, s):
        _, loc = locals_at_return(MANACHER, s)
        d1, d2 = radii(s)
        self.assertEqual(loc["d1"], d1, s)
        self.assertEqual(loc["d2"], d2, s)
        n = len(s)
        count = sum(1 for i in range(n) for j in range(i + 1, n + 1) if is_pal(s[i:j]))
        self.assertEqual(sum(loc["d1"]) + sum(loc["d2"]), count, s)

    def test_exhaustive(self):
        for s in itertools.chain(all_strings("ab", 10), all_strings("abc", 6)):
            if s:
                self._check(s)

    def test_random(self):
        for seed in range(12):
            self._check(H.generate(50, random.Random(f"pal-radii|{seed}")))


class LowerBoundTests(unittest.TestCase):
    """PROOFS.md section 8: for n = 1..150, changing one character of a^n to b changes the answer (n, 0) exactly when
    the position is not the middle one (n odd, position (n - 1)/2); so a correct algorithm must read n - 1 (n odd) or n
    (n even) characters of a^n. The oracle trimming lemma (section 9): every palindrome over {a, b} of length M <= 14
    contains, for every L < M, a palindrome of length L + 1 or L + 2."""

    def test_adversary(self):
        for n in range(1, 151):
            base = MANACHER("a" * n)
            self.assertEqual(base, (n, 0))
            for p in range(n):
                s = "a" * p + "b" + "a" * (n - p - 1)
                changed = MANACHER(s) != base
                self.assertEqual(changed, not (n % 2 == 1 and p == (n - 1) // 2), (n, p))

    def test_trimming(self):
        for w in all_strings("ab", 14):
            if w and is_pal(w):
                M = len(w)
                for L in range(M):
                    t = (M - (L + 1)) // 2
                    inner = w[t:M - t]
                    self.assertIn(len(inner), (L + 1, L + 2))
                    self.assertTrue(is_pal(inner))


class SpaceTests(unittest.TestCase):
    """PROOFS.md section 10: brute force and expansion use O(1) words (peak traced allocation at most 2048 bytes:
    brute force n = 20, 40, 80, expansion n = 250..2000 doubling, seeded harness strings); Manacher Theta(n) (peak
    between 16 n and 80 n + 4096 bytes, n = 10^4, 2 * 10^4, 4 * 10^4, on a^n and on seeded strings)."""

    def test_constant_space(self):
        for n in (20, 40, 80):
            s = H.generate(n, random.Random(f"pal-space|{n}"))
            self.assertLessEqual(peak_bytes(BRUTE, s), 2048, n)
        for n in (250, 500, 1000, 2000):
            s = H.generate(n, random.Random(f"pal-space|{n}"))
            self.assertLessEqual(peak_bytes(EXPAND, s), 2048, n)

    def test_manacher(self):
        for n in (10000, 20000, 40000):
            for s in ("a" * n, H.generate(n, random.Random(f"pal-space|{n}"))):
                peak = peak_bytes(MANACHER, s)
                self.assertTrue(16 * n <= peak <= 80 * n + 4096, (n, peak))


if __name__ == "__main__":
    unittest.main()
