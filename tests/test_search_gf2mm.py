"""Tests for search/gf2mm.py: the exact verifiers must accept correct schemes and reject corrupted ones.

Run:  python -m unittest discover -s tests
"""
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search import gf2mm  # noqa: E402
from search.gf2mm import (kron_scheme, mm_tensor, residual, standard_scheme, strassen_scheme,  # noqa: E402
                          verify, verify_explicit, verify_over_integers)

FORMATS = [(1, 1, 1), (2, 2, 2), (2, 3, 4), (3, 2, 1), (1, 4, 2), (3, 3, 3)]


class TensorAndStandardScheme(unittest.TestCase):
    def test_tensor_has_nmp_ones(self):
        for fmt in FORMATS:
            n, m, p = fmt
            ones = sum(bin(s).count("1") for s in mm_tensor(fmt))
            self.assertEqual(ones, n * m * p, fmt)

    def test_tensor_entries_explicit_2x2(self):
        # coefficient of a_ij b_j'k c_k'i' is 1 iff j == j', k == k', i == i'
        n = m = p = 2
        T = mm_tensor((n, m, p))
        for i in range(n):
            for j in range(m):
                for j2 in range(m):
                    for k in range(p):
                        for k2 in range(p):
                            for i2 in range(n):
                                bit = (T[i * m + j] >> ((j2 * p + k) * (p * n) + (k2 * n + i2))) & 1
                                self.assertEqual(bit, int(j == j2 and k == k2 and i == i2))

    def test_standard_scheme_is_correct(self):
        for fmt in FORMATS:
            s = standard_scheme(fmt)
            self.assertEqual(len(s), fmt[0] * fmt[1] * fmt[2])
            self.assertTrue(verify(fmt, s), fmt)
            self.assertTrue(verify_explicit(fmt, s), fmt)
            self.assertTrue(verify_over_integers(fmt, s), fmt)

    def test_standard_scheme_computes_products(self):
        self.assertTrue(gf2mm.random_check((2, 3, 4), standard_scheme((2, 3, 4)), trials=20, seed=1))


class KnownSchemes(unittest.TestCase):
    def test_strassen_rank7_over_gf2(self):
        s = strassen_scheme()
        self.assertEqual(len(s), 7)
        self.assertTrue(verify((2, 2, 2), s))
        self.assertTrue(verify_explicit((2, 2, 2), s))
        # functional check on all 256 pairs of 2x2 0/1 matrices
        for x in range(16):
            for y in range(16):
                A = [[(x >> 0) & 1, (x >> 1) & 1], [(x >> 2) & 1, (x >> 3) & 1]]
                B = [[(y >> 0) & 1, (y >> 1) & 1], [(y >> 2) & 1, (y >> 3) & 1]]
                self.assertEqual(gf2mm.evaluate((2, 2, 2), s, A, B), gf2mm.matmul(A, B))

    def test_strassen_without_signs_is_not_valid_over_z(self):
        self.assertFalse(verify_over_integers((2, 2, 2), strassen_scheme()))

    def test_strassen_squared_is_rank49_for_4x4(self):
        fmt, s = kron_scheme((2, 2, 2), strassen_scheme(), (2, 2, 2), strassen_scheme())
        self.assertEqual(fmt, (4, 4, 4))
        self.assertEqual(len(s), 49)
        self.assertTrue(verify(fmt, s))

    def test_kron_of_rectangular_standard_schemes(self):
        fmt, s = kron_scheme((1, 2, 3), standard_scheme((1, 2, 3)), (2, 1, 2), standard_scheme((2, 1, 2)))
        self.assertEqual(fmt, (2, 2, 6))
        self.assertTrue(verify(fmt, s))


class VerifierRejectsCorruption(unittest.TestCase):
    def test_every_single_bit_flip_of_strassen_is_rejected(self):
        s = strassen_scheme()
        na, nb, nc = gf2mm.dims((2, 2, 2))
        count = 0
        for t in range(len(s)):
            for pos, size in enumerate((na, nb, nc)):
                for bit in range(size):
                    bad = [list(x) for x in s]
                    bad[t][pos] ^= 1 << bit
                    bad = [tuple(x) for x in bad]
                    self.assertGreater(residual((2, 2, 2), bad), 0)
                    self.assertFalse(verify_explicit((2, 2, 2), bad))
                    count += 1
        self.assertEqual(count, 7 * 12)

    def test_random_corruptions_of_3x3_standard_are_rejected(self):
        rng = random.Random(7)
        base = standard_scheme((3, 3, 3))
        for _ in range(50):
            bad = [list(x) for x in base]
            t = rng.randrange(len(bad))
            pos = rng.randrange(3)
            bad[t][pos] ^= 1 << rng.randrange(9)
            bad = [tuple(x) for x in bad]
            self.assertFalse(verify((3, 3, 3), bad))
            self.assertFalse(verify_explicit((3, 3, 3), bad))

    def test_dropped_and_duplicated_terms_are_rejected(self):
        s = strassen_scheme()
        self.assertFalse(verify((2, 2, 2), s[1:]))
        self.assertFalse(verify((2, 2, 2), s + [s[0]]))
        self.assertTrue(verify((2, 2, 2), s + [s[0], s[0]]))  # a pair of equal terms cancels over GF(2)

    def test_out_of_range_factor_raises(self):
        s = strassen_scheme()
        with self.assertRaises(ValueError):
            verify((2, 2, 2), s + [(1 << 4, 1, 1)])
        with self.assertRaises(ValueError):
            verify((2, 2, 2), s + [(-1, 1, 1)])

    def test_scheme_of_other_format_is_rejected(self):
        self.assertFalse(verify((2, 2, 2), standard_scheme((2, 2, 1)) + [(1, 1, 1)]))


class JsonRoundTrip(unittest.TestCase):
    def test_save_load_and_refuse_invalid(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "s.json"
            gf2mm.save_scheme(path, (2, 2, 2), strassen_scheme(), status="test")
            fmt, terms, doc = gf2mm.load_scheme(path)
            self.assertEqual(fmt, (2, 2, 2))
            self.assertEqual(sorted(terms), sorted(strassen_scheme()))
            self.assertEqual(doc["rank"], 7)
            self.assertEqual(len(doc["products"]), 7)
            json.loads(path.read_text(encoding="utf-8"))
            with self.assertRaises(ValueError):
                gf2mm.save_scheme(Path(d) / "bad.json", (2, 2, 2), strassen_scheme()[1:])
            self.assertFalse((Path(d) / "bad.json").exists())


if __name__ == "__main__":
    unittest.main()
