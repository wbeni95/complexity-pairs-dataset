"""Tests for search/equivalence.py: the symmetry group preserves validity, the invariants are unchanged under random
group elements, they differ for known inequivalent schemes, and the exact equivalence test finds a certificate
for equivalent schemes and none for inequivalent ones.

Run:  python -m unittest tests.test_search_equivalence
"""
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import equivalence as eq  # noqa: E402
from search import gf2mm  # noqa: E402

RL054 = ROOT / "search" / "schemes" / "rust-2026-10-07" / "4x4x4_rank47_seed8.json"
R49_SS = ROOT / "search" / "schemes" / "rust-2026-10-07b" / "4x4x4_rank49_seed101.json"   # S(x)S-like invariant
R49_OTHER = ROOT / "search" / "schemes" / "rust-2026-10-07b" / "4x4x4_rank49_seed120.json"  # different invariant


def strassen_squared():
    s = gf2mm.strassen_scheme()
    _, t = gf2mm.kron_scheme((2, 2, 2), s, (2, 2, 2), s)
    return t


def split_strassen():
    """A valid rank-8 scheme for <2,2,2>: Strassen's first product (A11+A22)(B11+B22) -> C11, C22 split into
    two products with the same left and right factors and one C entry each."""
    s = gf2mm.strassen_scheme()
    a, b, c = s[0]
    low = c & -c
    out = [(a, b, low), (a, b, c ^ low)] + s[1:]
    assert gf2mm.verify((2, 2, 2), out) and len(out) == 8
    return out


def random_element(terms, n, rng):
    """A random element of G applied to the scheme: S3 part, sandwich, then a random term order."""
    imgs = eq.s3_images(terms, n)
    name = rng.choice(eq.S3_NAMES)
    P, Q, R = (eq.random_gl(n, rng) for _ in range(3))
    out = eq.apply_sandwich(imgs[name], P, Q, R, n)
    rng.shuffle(out)
    return out


class MatrixHelpers(unittest.TestCase):
    def test_inverse_and_mul(self):
        rng = random.Random(1)
        for n in (2, 3, 4):
            for _ in range(50):
                x = eq.random_gl(n, rng)
                xi = eq.inverse(x, n)
                self.assertEqual(eq.mul(x, xi, n), eq.identity(n))
                self.assertEqual(eq.mul(xi, x, n), eq.identity(n))
            self.assertIsNone(eq.inverse(0, n))

    def test_charpoly(self):
        self.assertEqual(eq.charpoly(0, 4), 1 << 4)                    # t^4
        self.assertEqual(eq.charpoly(eq.identity(4), 4), (1 << 4) | 1)  # (t+1)^4 = t^4 + 1 in GF(2)[t]
        rng = random.Random(2)
        for _ in range(100):
            m = rng.getrandbits(16)
            g = eq.random_gl(4, rng)
            self.assertEqual(eq.charpoly(m, 4), eq.charpoly(eq.mul(eq.mul(g, m, 4), eq.inverse(g, 4), 4), 4))

    def test_charpoly_of_product_is_cyclic(self):
        rng = random.Random(3)
        for _ in range(100):
            a, b, c = (rng.getrandbits(16) for _ in range(3))
            abc = eq.mul(eq.mul(a, b, 4), c, 4)
            bca = eq.mul(eq.mul(b, c, 4), a, 4)
            self.assertEqual(eq.charpoly(abc, 4), eq.charpoly(bca, 4))


class GroupPreservesValidity(unittest.TestCase):
    def test_each_generator_is_a_symmetry(self):
        rng = random.Random(4)
        t = strassen_squared()
        self.assertTrue(gf2mm.verify((4, 4, 4), eq.cyclic(t)))
        self.assertTrue(gf2mm.verify((4, 4, 4), eq.transposed(t, 4)))
        P, Q, R = (eq.random_gl(4, rng) for _ in range(3))
        self.assertTrue(gf2mm.verify((4, 4, 4), eq.apply_sandwich(t, P, Q, R, 4)))

    def test_random_elements_keep_schemes_valid(self):
        rng = random.Random(5)
        cases = [((2, 2, 2), gf2mm.strassen_scheme()), ((3, 3, 3), gf2mm.standard_scheme((3, 3, 3))),
                 ((4, 4, 4), strassen_squared())]
        if RL054.exists():
            cases.append(((4, 4, 4), gf2mm.load_scheme(RL054)[1]))
        for fmt, terms in cases:
            for _ in range(5):
                self.assertTrue(gf2mm.verify(fmt, random_element(terms, fmt[0], rng)), fmt)

    def test_wrong_action_is_not_a_symmetry(self):
        # control: (a, b, c) -> (P a, b, c) with P != I is NOT a symmetry, so the verifier must reject it
        t = strassen_squared()
        P = eq.from_rows([0b0011, 0b0010, 0b0100, 0b1000], 4)
        bad = [(eq.mul(P, a, 4), b, c) for a, b, c in t]
        self.assertFalse(gf2mm.verify((4, 4, 4), bad))


class InvariantsAreInvariant(unittest.TestCase):
    def check(self, terms, n, seeds):
        inv = eq.invariants(terms, n, wl=True)
        for s in seeds:
            self.assertEqual(eq.invariants(random_element(terms, n, random.Random(s)), n, wl=True), inv, s)

    def test_small_formats(self):
        self.check(gf2mm.strassen_scheme(), 2, range(10, 20))
        self.check(split_strassen(), 2, range(20, 30))
        self.check(gf2mm.standard_scheme((3, 3, 3)), 3, range(30, 33))

    def test_strassen_squared(self):
        self.check(strassen_squared(), 4, range(40, 43))

    def test_rl054_scheme(self):
        if not RL054.exists():
            self.skipTest("RL-054 scheme not present")
        self.check(gf2mm.load_scheme(RL054)[1], 4, range(50, 53))


class InvariantsSeparate(unittest.TestCase):
    def test_rank8_schemes(self):
        # standard algorithm (all factors rank 1) vs split Strassen (has rank-2 factors): inequivalent
        i1 = eq.invariants(gf2mm.standard_scheme((2, 2, 2)), 2, wl=True)
        i2 = eq.invariants(split_strassen(), 2, wl=True)
        for k in i1:
            self.assertNotEqual(i1[k], i2[k], k)

    def test_saved_rank49_schemes(self):
        if not (R49_SS.exists() and R49_OTHER.exists()):
            self.skipTest("saved rank-49 schemes not present")
        t1, t2 = gf2mm.load_scheme(R49_SS)[1], gf2mm.load_scheme(R49_OTHER)[1]
        i1, i2 = eq.invariants(t1, 4), eq.invariants(t2, 4)
        for k in i1:
            self.assertNotEqual(i1[k], i2[k], k)
        self.assertEqual(eq.first_difference(i1, i2), "factor_rank_profile")


class ExactTest(unittest.TestCase):
    def test_certificate_for_equivalent_schemes(self):
        rng = random.Random(6)
        for fmt, terms in (((2, 2, 2), gf2mm.strassen_scheme()), ((2, 2, 2), split_strassen()),
                           ((4, 4, 4), strassen_squared())):
            n = fmt[0]
            img = random_element(terms, n, rng)
            cert = eq.find_equivalence(terms, img, n)
            self.assertIsNotNone(cert)
            name, P, Q, R = cert
            mapped = eq.apply_sandwich(eq.s3_images(terms, n)[name], P, Q, R, n)
            self.assertEqual(eq.canonical_terms(mapped), eq.canonical_terms(img))

    def test_rl054_equivalent_to_its_images(self):
        if not RL054.exists():
            self.skipTest("RL-054 scheme not present")
        t = gf2mm.load_scheme(RL054)[1]
        for s in (7, 8):
            self.assertIsNotNone(eq.find_equivalence(t, random_element(t, 4, random.Random(s)), 4))

    def test_no_certificate_for_inequivalent(self):
        self.assertIsNone(eq.find_equivalence(gf2mm.standard_scheme((2, 2, 2)), split_strassen(), 2))

    def test_no_certificate_after_one_changed_term(self):
        if not RL054.exists():
            self.skipTest("RL-054 scheme not present")
        t = gf2mm.load_scheme(RL054)[1]
        img = random_element(t, 4, random.Random(9))
        a, b, c = img[0]
        img[0] = (a, b, c ^ 1)
        self.assertIsNone(eq.find_equivalence(t, img, 4))

    def test_find_sandwich_exhaustive_on_strassen(self):
        # Strassen's stabiliser in GL(2,2)^3 is non-trivial; every sandwich image must be found again
        s = gf2mm.strassen_scheme()
        rng = random.Random(10)
        for _ in range(10):
            P, Q, R = (eq.random_gl(2, rng) for _ in range(3))
            self.assertIsNotNone(eq.find_sandwich(s, eq.apply_sandwich(s, P, Q, R, 2), 2))


if __name__ == "__main__":
    unittest.main()
