"""Checks of the proofs in pairs/xor-sat-brute-force-vs-gaussian-elimination/PROOFS.md (sections 3 to 6).

Every check runs the unchanged implementations on fixed inputs (all small systems and seeded random ones): the count
0 or 2^(n - rank A), the echelon form after forward elimination, correctness of both algorithms, the brute-force count
on systems with independent rows and on repeated equations, the elimination bounds and the maximality of the row
operations on X_n. Runs in a few seconds.
"""
import importlib.util
import itertools
import random
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = "pairs/xor-sat-brute-force-vs-gaussian-elimination/"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TR = _load("tests/_proof_trace.py", "tp_xor_trace")


def rank(rows, n):
    """Rank over GF(2) of the A parts, by an XOR basis keyed by the highest set bit (independent of the code)."""
    basis = {}
    for row in rows:
        v = sum(row[j] << j for j in range(n))
        while v:
            h = v.bit_length() - 1
            if h not in basis:
                basis[h] = v
                break
            v ^= basis[h]
    return len(basis)


def solutions(n, rows):
    out = []
    for mask in range(1 << n):
        if all((sum(row[j] & ((mask >> j) & 1) for j in range(n)) + row[n]) % 2 == 0 for row in rows):
            out.append(mask)
    return out


def small_systems():
    """Every augmented matrix with (m, n) in {(0, 0), (0, 2), (1..3, 0..3), (4, 1), (4, 2)}: 9404 systems."""
    shapes = [(0, 0), (0, 2)] + [(m, n) for m in (1, 2, 3) for n in (0, 1, 2, 3)] + [(4, 1), (4, 2)]
    for m, n in shapes:
        for bits in itertools.product((0, 1), repeat=m * (n + 1)):
            yield n, tuple(tuple(bits[i * (n + 1):(i + 1) * (n + 1)]) for i in range(m))


def random_system(n, m, rng, independent=False):
    while True:
        rows = [tuple(rng.randint(0, 1) for _ in range(n + 1)) for _ in range(m)]
        if not independent or rank(rows, n) == m:
            return tuple(rows)


class XorSatProofs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.H = _load(E + "harness.py", "tp_xor_h")
        cls.brute = staticmethod(_load(E + "implementations/brute_force.py", "tp_xor_b").xor_sat_brute_force)
        cls.gauss = staticmethod(_load(E + "implementations/gaussian_elimination.py", "tp_xor_g").xor_sat_gauss)

    def systems(self):
        yield from small_systems()
        for i in range(600):
            rng = random.Random(f"tp-xor|{i}")
            n = rng.randint(0, 9)
            yield n, random_system(n, rng.randint(0, 12), rng)

    def test_correctness_count_and_echelon_form(self):
        """Sections 3 and 4: echelon form after forward elimination, count 0 or 2^(n - rank A), witnesses."""
        seen = 0
        for n, rows in self.systems():
            sols = solutions(n, rows)
            r = rank(rows, n)
            self.assertIn(len(sols), (0, 2 ** (n - r)))                       # problem statement
            c, w = self.brute((n, rows))
            self.assertEqual(c, len(sols))
            self.assertEqual(w, None if not sols else tuple((sols[0] >> j) & 1 for j in range(n)))
            t = TR.LineTrace(self.gauss, snapshot="rows r..m-1 are zero in the A part")
            c2, w2 = t.run((n, rows))
            self.assertEqual(c2, len(sols))
            if sols:
                self.assertIn(sum(b << j for j, b in enumerate(w2)), set(sols))
            else:
                self.assertIsNone(w2)
            if t.snapshot is not None:                                         # echelon form (section 5)
                M, piv, rr = t.snapshot["M"], t.snapshot["pivots"], t.snapshot["r"]
                self.assertEqual(rr, r)
                self.assertEqual(len(piv), rr)
                self.assertEqual(piv, sorted(set(piv)))
                for k, p in enumerate(piv):
                    self.assertEqual(M[k][p], 1)
                    self.assertTrue(all(M[k][j] == 0 for j in range(p)))
                for i in range(rr, len(rows)):
                    self.assertTrue(all(M[i][j] == 0 for j in range(n)))
            seen += 1
        self.assertEqual(seen, 9404 + 600)

    def _brute_ops(self, n, rows):
        self.H._ops = 0
        self.brute((n, tuple(tuple(self.H.CountingBit(b) for b in row) for row in rows)))
        return self.H._ops

    def test_brute_independent_rows(self):
        """Section 5: on m x n systems with independent rows, exactly (2n + 1)(2^(n+1) - 2^(n-m+1)) operations,
        below 2 (2n + 1) 2^n (n = 1..10, every m <= n, 4 seeded systems each)."""
        for n in range(1, 11):
            for m in range(1, n + 1):
                for s in range(4):
                    rows = random_system(n, m, random.Random(f"tp-xor-ind|{n}|{m}|{s}"), independent=True)
                    ops = self._brute_ops(n, rows)
                    self.assertEqual(ops, (2 * n + 1) * (2 ** (n + 1) - 2 ** (n - m + 1)))
                    self.assertLess(ops, 2 * (2 * n + 1) * 2 ** n)

    def test_brute_repeated_equation(self):
        """Section 5: m copies of x1 = 0 cost exactly (2n + 1)(m + 1) 2^(n-1) operations (n = 1..8, m = 1..12)."""
        for n in range(1, 9):
            for m in range(1, 13):
                rows = ((1,) + (0,) * n,) * m
                self.assertEqual(self._brute_ops(n, rows), (2 * n + 1) * (m + 1) * 2 ** (n - 1))

    def test_brute_upper_bound(self):
        """Section 5: at most 2^n m (2n + 1) operations on 400 seeded random systems (n = 0..9, m = 0..12)."""
        for i in range(400):
            rng = random.Random(f"tp-xor-ub|{i}")
            n, m = rng.randint(0, 9), rng.randint(0, 12)
            rows = random_system(n, m, rng)
            self.assertLessEqual(self._brute_ops(n, rows), (1 << n) * m * (2 * n + 1))

    def test_gauss_bounds_and_maximal_row_operations(self):
        """Section 6: elimination operation bounds on 600 seeded random systems; on the square ones at most n(n-1)/2
        row operations and (n - 1) n (2n + 5)/6 entry XORs, both attained exactly by X_n (n = 1..14)."""
        markers = {"rowop": "row = M[i]", "entry": "row[j] = row[j] ^ top[j]"}
        for i in range(600):
            rng = random.Random(f"tp-xor-gb|{i}")
            n = rng.randint(1, 14)
            m = n if i % 2 == 0 else rng.randint(1, 16)
            rows = random_system(n, m, rng)
            t = TR.LineTrace(self.gauss, markers)
            self.H._ops = 0
            t.run((n, tuple(tuple(self.H.CountingBit(b) for b in row) for row in rows)))
            k = min(m, n)
            self.assertLessEqual(self.H._ops, 2 * n * m + k * m * (n + 1) + 2 * k * n + m)
            if m == n:
                self.assertLessEqual(t.counts["rowop"], n * (n - 1) // 2)
                self.assertLessEqual(t.counts["entry"], (n - 1) * n * (2 * n + 5) // 6)
        for n in range(1, 15):
            fam = self.H._family(n)
            t = TR.LineTrace(self.gauss, markers)
            t.run((n, tuple(fam)))
            self.assertEqual(t.counts["rowop"], n * (n - 1) // 2)
            self.assertEqual(t.counts["entry"], (n - 1) * n * (2 * n + 5) // 6)

    def test_brute_force_space(self):
        """Section 5 (e): besides the input and the witness, brute force keeps only integers (and None for `first`
        before the first solution); 200 seeded systems."""
        for i in range(200):
            rng = random.Random(f"tp-xor-bsp|{i}")
            n, m = rng.randint(0, 9), rng.randint(0, 10)
            rows = random_system(n, m, rng)
            system = (n, rows)

            def extra(loc):
                return {"extra": sum(1 for k, v in loc.items()
                                     if not (isinstance(v, int) or v is None or v is system or v is rows
                                             or any(v is r for r in rows) or k == "witness"))}
            t = TR.LineTrace(self.brute, sizes=extra)
            t.run(system)
            self.assertEqual(t.peak.get("extra", 0), 0)

    def test_space(self):
        """Section 6: the working copy has m (n + 1) entries, the witness n, the pivot list at most min(m, n)."""
        for i in range(200):
            rng = random.Random(f"tp-xor-sp|{i}")
            n, m = rng.randint(0, 12), rng.randint(0, 12)
            rows = random_system(n, m, rng)
            t = TR.LineTrace(self.gauss, sizes=lambda loc: {
                "M": sum(len(r) for r in loc.get("M") or ()), "piv": len(loc.get("pivots") or ())})
            t.run((n, rows))
            self.assertLessEqual(t.peak.get("M", 0), m * (n + 1))
            self.assertLessEqual(t.peak.get("piv", 0), min(m, n))


if __name__ == "__main__":
    unittest.main()
