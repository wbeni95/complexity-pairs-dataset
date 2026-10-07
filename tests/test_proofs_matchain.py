"""Checks of the proofs in pairs/matrix-chain-recursion-vs-dp/PROOFS.md.

Runs the unchanged implementations with in-memory instrumentation only (a profiler hook, a trace hook, and a number
type that counts multiplications wrapped around the dimensions). Fixed seeds and stated ranges; deterministic.
"""
import importlib.util
import random
import sys
import unittest
from fractions import Fraction
from math import comb
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "matrix-chain-recursion-vs-dp"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, E / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


REC = _load("implementations/recursion.py", "proofs_mc_rec").matrix_chain_recursive
DP = _load("implementations/dp.py", "proofs_mc_dp").matrix_chain_dp


def trees(i, j):
    """Every parenthesisation of matrices i..j as nested tuples (leaves are matrix indices)."""
    if i == j:
        return [i]
    out = []
    for k in range(i, j):
        for left in trees(i, k):
            for right in trees(k + 1, j):
                out.append((left, right))
    return out


def tree_cost(t, dims):
    """(rows, cols, scalar multiplications) of the product described by the tree, by multiplying out the shapes."""
    if isinstance(t, int):
        return dims[t], dims[t + 1], 0
    r1, c1, x1 = tree_cost(t[0], dims)
    r2, c2, x2 = tree_cost(t[1], dims)
    assert c1 == r2
    return r1, c2, x1 + x2 + r1 * c1 * c2


class Mults:
    count = 0


class MInt:
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _o(o):
        return o.v if isinstance(o, MInt) else o

    def __mul__(self, o):
        Mults.count += 1
        return MInt(self.v * self._o(o))

    __rmul__ = __mul__

    def __add__(self, o):
        return MInt(self.v + self._o(o))

    __radd__ = __add__

    def __lt__(self, o):
        return self.v < self._o(o)

    def __gt__(self, o):
        return self.v > self._o(o)

    def __le__(self, o):
        return self.v <= self._o(o)

    def __ge__(self, o):
        return self.v >= self._o(o)

    def __eq__(self, o):
        return self.v == self._o(o)


def plain(x):
    return x.v if isinstance(x, MInt) else x


class MatrixChainProofs(unittest.TestCase):
    def test_correct_against_tree_enumeration(self):
        rng = random.Random(1)
        for n in range(10):
            ts = trees(0, n - 1) if n >= 1 else []
            if n >= 1:
                self.assertEqual(len(ts), comb(2 * n - 2, n - 1) // n)
            for _ in range(30):
                dims = tuple(rng.randint(1, 50) for _ in range(n + 1))
                want = min(tree_cost(t, dims)[2] for t in ts) if n >= 1 else 0
                self.assertEqual(REC(dims), want, dims)
                self.assertEqual(DP(dims), want, dims)

    def test_recursion_counts(self):
        rng = random.Random(2)
        rec_code = REC.__code__
        cost_code = next(c for c in rec_code.co_consts if hasattr(c, "co_name") and c.co_name == "cost")
        for n in range(0, 11):
            for _ in range(2):
                dims = tuple(MInt(rng.randint(1, 50)) for _ in range(n + 1))
                calls, depth, best = [0], [0], [0]

                def prof(frame, event, _arg):
                    if frame.f_code is cost_code:
                        if event == "call":
                            calls[0] += 1
                            depth[0] += 1
                            best[0] = max(best[0], depth[0])
                        elif event == "return":
                            depth[0] -= 1

                Mults.count = 0
                sys.setprofile(prof)
                try:
                    value = REC(dims)
                finally:
                    sys.setprofile(None)
                self.assertEqual(plain(value), DP(tuple(d.v for d in dims)))
                if n == 0:
                    self.assertEqual(calls[0], 0)
                    continue
                self.assertEqual(calls[0], 3 ** (n - 1), n)
                self.assertEqual(Mults.count, 3 ** (n - 1) - 1, n)
                self.assertEqual(best[0], n, n)

    def test_dp_counts(self):
        rng = random.Random(3)
        for n in range(61):
            dims = tuple(MInt(rng.randint(1, 50)) for _ in range(n + 1))
            shape = []

            def local(frame, event, _arg):
                if event == "return" and "m" in frame.f_locals:
                    m = frame.f_locals["m"]
                    shape.append((len(m), sorted({len(r) for r in m})))
                return local

            Mults.count = 0
            sys.settrace(lambda f, e, a: local if f.f_code is DP.__code__ else None)
            try:
                DP(dims)
            finally:
                sys.settrace(None)
            self.assertEqual(Mults.count, (n ** 3 - n) // 3, n)
            if n >= 1:
                self.assertEqual(shape, [(n, [n])], n)

    def test_catalan(self):
        P = [0, 1]
        for n in range(2, 61):
            P.append(sum(P[k] * P[n - k] for k in range(1, n)))
        for n in range(1, 61):
            self.assertEqual(P[n], comb(2 * n - 2, n - 1) // n)
            self.assertEqual(comb(2 * n - 2, n - 1) % n, 0)
            # -(1/2) binom(1/2, n) (-4)^n = C(2n-2, n-1)/n
            b = Fraction(1)
            for t in range(n):
                b *= Fraction(1, 2) - t
            for t in range(1, n + 1):
                b /= t
            self.assertEqual(-Fraction(1, 2) * b * (-4) ** n, Fraction(comb(2 * n - 2, n - 1), n))
        for n in range(2, 401):
            p = comb(2 * n - 2, n - 1) // n
            ratio = Fraction(p) ** 2 * Fraction(n) ** 3 / Fraction(16) ** n  # (P(n) n^(3/2) / 4^n)^2
            self.assertTrue(Fraction(1, 64) <= ratio <= Fraction(18, 100) ** 2, n)
        for k in range(1, 2001):
            c = comb(2 * k, k)
            # 4^k / sqrt(4k) <= c <= 4^k / sqrt(3k + 1), squared to stay in integers
            self.assertLessEqual(16 ** k, c * c * 4 * k)
            self.assertLessEqual(c * c * (3 * k + 1), 16 ** k)


class RecursionVsEnumeration(unittest.TestCase):
    def test_recursion_vs_enumeration(self):
        import math
        for n in range(1, 61):
            p = comb(2 * n - 2, n - 1) // n
            if n == 1:
                self.assertEqual(p, 1)
            elif n <= 17:
                self.assertGreater(3 ** (n - 1), p, n)
            else:
                self.assertLess(3 ** (n - 1), p, n)

        def g(n):
            return (4 / 3) ** (n - 1) / (2 * n * math.sqrt(n - 1))

        self.assertGreater(g(20), 1.35)
        for n in range(6, 401):
            self.assertGreater(g(n + 1) / g(n), 1, n)
        self.assertLess(g(6) / g(5), 1)


if __name__ == "__main__":
    unittest.main()
