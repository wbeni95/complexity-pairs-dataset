"""Checks of the proofs in pairs/string-matching-naive-vs-kmp/PROOFS.md (sections 5 to 10).

Every check runs the unchanged implementations on fixed inputs (exhaustive small families and seeded random pairs):
the failure function against the longest proper border, correctness of both matchers, the KMP state after every text
character, the KMP comparison bounds (upper and lower) per part, the adversary argument behind the optimality caveat,
and the exact expected cost of the naive matcher on random text. Runs in a few seconds.
"""
import importlib.util
import itertools
import random
import unittest
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = "pairs/string-matching-naive-vs-kmp/"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TR = _load("tests/_proof_trace.py", "tp_kmp_trace")


def longest_border(s):
    return max(k for k in range(len(s)) if s[:k] == s[len(s) - k:])


def direct_count(text, pattern):
    return sum(1 for i in range(len(text) - len(pattern) + 1) if text[i:i + len(pattern)] == pattern)


def words(alpha, lo, hi):
    for k in range(lo, hi + 1):
        for w in itertools.product(alpha, repeat=k):
            yield "".join(w)


class KmpProofs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.H = _load(E + "harness.py", "tp_kmp_h")
        cls.naive = staticmethod(_load(E + "implementations/naive.py", "tp_kmp_n").count_naive)
        K = _load(E + "implementations/kmp.py", "tp_kmp_k")
        cls.kmp = staticmethod(K.count_kmp)
        cls.failure = staticmethod(K._failure)

    def counted(self, f, *args):
        C = self.H.CountingChar
        args = tuple(tuple(C(c) for c in a) for a in args)
        self.H._comparisons = 0
        f(args if len(args) > 1 else args[0])
        return self.H._comparisons

    def test_failure_function(self):
        """Section 6: fail[q] is the length of the longest proper border of P[:q+1] (all patterns over {a, b} of
        length <= 10 and over {a, b, c} of length <= 6)."""
        for p in itertools.chain(words("ab", 1, 10), words("abc", 1, 6)):
            self.assertEqual(self.failure(p), [longest_border(p[:q + 1]) for q in range(len(p))])

    def test_correctness(self):
        """Sections 5 and 7: both matchers count the overlapping occurrences (all texts over {a, b} of length <= 8
        with all patterns of length 1..4: 511 x 30 pairs; 1000 seeded random pairs over {a, b, c})."""
        cases = 0
        for t in words("ab", 0, 8):
            for p in words("ab", 1, 4):
                want = direct_count(t, p)
                self.assertEqual(self.kmp((t, p)), want)
                self.assertEqual(self.naive((t, p)), want)
                cases += 1
        for i in range(1000):
            rng = random.Random(f"tp-kmp|{i}")
            t = "".join(rng.choice("abc") for _ in range(rng.randint(0, 40)))
            p = "".join(rng.choice("abc") for _ in range(rng.randint(1, 6)))
            self.assertEqual(self.kmp((t, p)), direct_count(t, p))
            self.assertEqual(self.naive((t, p)), direct_count(t, p))
        self.assertEqual(cases, 511 * 30)

    def test_scan_state(self):
        """Section 7: after the if test for character t, q is the largest l <= m such that P[:l] is a suffix of
        T[:t+1] (all texts over {a, b} of length <= 7 with all patterns of length 1..4)."""
        code = self.kmp.__code__
        src, start = __import__("inspect").getsourcelines(self.kmp)
        line = start + next(i for i, s in enumerate(src) if "if q == m:" in s)
        for t in words("ab", 0, 7):
            for p in words("ab", 1, 4):
                seen = []

                def local(frame, event, arg):
                    if event == "line" and frame.f_lineno == line:
                        seen.append(frame.f_locals["q"])
                    return local

                def glob(frame, event, arg):
                    return local if frame.f_code is code else None
                import sys
                old = sys.gettrace()
                sys.settrace(glob)
                try:
                    self.kmp((t, p))
                finally:
                    sys.settrace(old)
                self.assertEqual(len(seen), len(t))
                for k, q in enumerate(seen):
                    read = t[:k + 1]
                    self.assertEqual(q, max(l for l in range(len(p) + 1) if read.endswith(p[:l])))

    def test_comparison_bounds(self):
        """Section 8: m - 1 <= failure-table comparisons <= 3(m - 1) and n <= scan comparisons <= 3n (all pairs over
        {a, b} with n <= 8 and m <= 6; 1000 seeded random pairs over {a, b, c}, n <= 60, m <= 12)."""
        pairs = [(t, p) for t in words("ab", 0, 8) for p in words("ab", 1, 6)]
        for i in range(1000):
            rng = random.Random(f"tp-kmp-b|{i}")
            pairs.append(("".join(rng.choice("abc") for _ in range(rng.randint(0, 60))),
                          "".join(rng.choice("abc") for _ in range(rng.randint(1, 12)))))
        for t, p in pairs:
            n, m = len(t), len(p)
            fail = self.counted(self.failure, p)
            total = self.counted(self.kmp, t, p)
            scan = total - fail
            self.assertGreaterEqual(fail, m - 1)
            self.assertLessEqual(fail, 3 * (m - 1))
            self.assertGreaterEqual(scan, n)
            self.assertLessEqual(scan, 3 * n)

    def test_adversary(self):
        """Section 9: for P = a^m and T = a^n (1 <= m <= n <= 12), changing any single text character lowers the
        count, so a correct algorithm must read every text character."""
        for n in range(1, 13):
            for m in range(1, n + 1):
                base = direct_count("a" * n, "a" * m)
                self.assertEqual(base, n - m + 1)
                for i in range(n):
                    changed = "a" * i + "b" + "a" * (n - i - 1)
                    self.assertLess(direct_count(changed, "a" * m), base)
                    self.assertEqual(self.kmp((changed, "a" * m)), direct_count(changed, "a" * m))

    def test_naive_expected_cost(self):
        """Section 10: over all texts of length n over sigma letters, a pattern of length m whose letters lie in the
        alphabet costs on average exactly max(n - m + 1, 0) sum_{j<m} sigma^(-j) comparisons, at most 2n (sigma = 2:
        n = 0..8, patterns of length 1..4; sigma = 3: n = 0..5, length 1..3)."""
        for sigma, nmax, mmax in ((2, 8, 4), (3, 5, 3)):
            alpha = "abc"[:sigma]
            for p in words(alpha, 1, mmax):
                for n in range(nmax + 1):
                    total = sum(self.counted(self.naive, t, p) for t in words(alpha, n, n))
                    avg = Fraction(total, sigma ** n)
                    want = max(n - len(p) + 1, 0) * sum(Fraction(1, sigma ** j) for j in range(len(p)))
                    self.assertEqual(avg, want)
                    self.assertLessEqual(avg, 2 * n)

    def test_naive_space(self):
        """Section 5: besides the input, the naive matcher keeps only integers (all pairs over {a, b}, n <= 6, m <= 3)."""
        for t in words("ab", 0, 6):
            for p in words("ab", 1, 3):
                inst = (t, p)
                tr = TR.LineTrace(self.naive, sizes=lambda loc: {"extra": sum(
                    1 for v in loc.values() if not (isinstance(v, int) or v is inst or v is t or v is p))})
                tr.run(inst)
                self.assertEqual(tr.peak.get("extra", 0), 0)

    def test_space(self):
        """Section 8: the failure table has m entries (all patterns over {a, b} of length 1..8)."""
        for p in words("ab", 1, 8):
            t = TR.LineTrace(self.kmp, sizes=lambda loc: {"fail": len(loc.get("fail") or ())})
            t.run(("ab" * 4, p))
            self.assertEqual(t.peak["fail"], len(p))


if __name__ == "__main__":
    unittest.main()
