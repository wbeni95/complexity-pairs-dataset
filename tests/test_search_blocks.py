"""Tests for search/blocks.py (start schemes from smaller verified schemes) and for the linear-dependence reduction
of the flip-graph kernel mirror (search/kernel_reference.py, --full-reduce). research/2026-10-06d_exotic_formats.md.

Run:  python -m unittest tests.test_search_blocks
"""
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from search import blocks, gf2mm, kernel_reference  # noqa: E402


class FormatMapTests(unittest.TestCase):
    def test_six_images_are_valid_schemes_of_the_permuted_formats(self):
        for fmt in ((2, 3, 4), (1, 2, 3), (2, 2, 3)):
            terms = gf2mm.standard_scheme(fmt)
            imgs = blocks.images(fmt, terms)
            self.assertEqual(sorted(f for f, _ in imgs), sorted(blocks.all_permutations(fmt) * (6 // len(set(blocks.all_permutations(fmt))))))
            for f, t in imgs:
                self.assertTrue(gf2mm.verify(f, t), f)

    def test_strassen_images_and_to_format(self):
        s = gf2mm.strassen_scheme()
        for f, t in blocks.images((2, 2, 2), s):
            self.assertTrue(gf2mm.verify(f, t))
        fmt, terms = gf2mm.kron_scheme((2, 2, 2), s, (1, 2, 3), gf2mm.standard_scheme((1, 2, 3)))
        self.assertTrue(gf2mm.verify(fmt, terms))  # (2, 4, 6), rank 42
        for target in blocks.all_permutations(fmt):
            self.assertTrue(gf2mm.verify(target, blocks.to_format(fmt, terms, target)))
        with self.assertRaises(ValueError):
            blocks.to_format(fmt, terms, (2, 4, 5))

    def test_transpose_is_an_involution(self):
        fmt, terms = (2, 3, 4), gf2mm.standard_scheme((2, 3, 4))
        f2, t2 = blocks.transpose(*blocks.transpose(fmt, terms))
        self.assertEqual((f2, sorted(t2)), (fmt, sorted(terms)))


class DirectSumTests(unittest.TestCase):
    def test_direct_sums_along_each_axis(self):
        s = gf2mm.strassen_scheme()
        for axis in range(3):
            f2 = [2, 2, 2]
            f2[axis] = 1
            big, terms = blocks.direct_sum(axis, ((2, 2, 2), s), (tuple(f2), gf2mm.standard_scheme(tuple(f2))))
            self.assertEqual(big[axis], 3)
            self.assertEqual(len(terms), 7 + 4)
            self.assertTrue(gf2mm.verify(big, terms))
            self.assertTrue(gf2mm.verify_explicit(big, terms))

    def test_wrong_sum_is_rejected_by_the_verifier(self):
        s = gf2mm.strassen_scheme()
        big, terms = blocks.direct_sum(2, ((2, 2, 2), s), ((2, 2, 1), gf2mm.standard_scheme((2, 2, 1))))
        self.assertFalse(gf2mm.verify(big, terms[:-1]))
        with self.assertRaises(ValueError):
            blocks.direct_sum(0, ((2, 2, 2), s), ((1, 2, 3), gf2mm.standard_scheme((1, 2, 3))))

    def test_best_block_start_uses_the_library(self):
        lib = blocks.strassen_entry()
        rank, desc, terms = blocks.best_block_start(lib, (2, 2, 3))
        self.assertEqual(rank, 7 + 4)  # (2,2,2) Strassen + (2,2,1) standard
        self.assertTrue(gf2mm.verify((2, 2, 3), terms))
        rank4, _, terms4 = blocks.best_block_start(lib, (4, 2, 2))
        self.assertEqual(rank4, 14)
        self.assertTrue(gf2mm.verify((4, 2, 2), terms4))


def _dependent_triple_scheme(seed=0):
    """A valid 2x2x2 scheme of rank 9 with a dependent triple sharing one factor that no pairwise merge removes:
    from the standard algorithm's terms (a, b1, u), (a, b2, w) with a = A11, write u = c1 + c3, w = c2 + c3:
    a(x)b1(x)(u+c3) + a(x)b2(x)(w+c3) + a(x)(b1+b2)(x)c3 = a(x)b1(x)u + a(x)b2(x)w."""
    fmt = (2, 2, 2)
    std = [list(t) for t in gf2mm.standard_scheme(fmt)]
    a = 1  # A11
    pair = [t for t in std if t[0] == a]
    assert len(pair) == 2
    (_, b1, u), (_, b2, w) = pair
    rng = random.Random(seed)
    while True:
        c3 = rng.randrange(1, 16)
        new = [[a, b1, u ^ c3], [a, b2, w ^ c3], [a, b1 ^ b2, c3]]
        if c3 not in (u, w) and all(x[2] for x in new) and len({x[2] for x in new}) == 3:
            break
    rest = [t for t in std if t[0] != a]
    terms = rest + new
    assert gf2mm.verify(fmt, terms)
    return fmt, terms


class DependencyReductionTests(unittest.TestCase):
    def test_dependent_triple_is_removed_only_with_full_reduction(self):
        for seed in range(5):
            fmt, terms = _dependent_triple_scheme(seed)
            last = len(terms) - 1
            plain = [list(t) for t in terms]
            self.assertEqual(kernel_reference.reduce(plain, [last], full=False), 0)
            self.assertEqual(len(plain), 9)  # the pairwise merge rule sees nothing
            full = [list(t) for t in terms]
            deps = kernel_reference.reduce(full, [last], full=True)
            self.assertEqual(deps, 1)
            self.assertEqual(len(full), 8)
            self.assertTrue(gf2mm.verify(fmt, [tuple(t) for t in full]))

    def test_walks_with_full_reduction_stay_valid_and_use_it(self):
        used = 0
        for fmt, seed in (((2, 2, 2), 1), ((2, 2, 3), 2), ((3, 3, 3), 3)):
            res = kernel_reference.walk(gf2mm.standard_scheme(fmt), seed, 4000, plateau=200, full_reduce=True)
            self.assertTrue(gf2mm.verify(fmt, res["best"]))
            used += res["dep_reductions"]
        self.assertGreater(used, 0, "the linear-dependence branch must be exercised")

    def test_full_reduce_off_is_the_default_and_never_counts(self):
        res = kernel_reference.walk(gf2mm.standard_scheme((3, 3, 3)), 3, 3000, plateau=200)
        self.assertEqual(res["dep_reductions"], 0)


if __name__ == "__main__":
    unittest.main()
