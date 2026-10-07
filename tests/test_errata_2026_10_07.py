"""Regression tests for the errata of 2026-10-07: defects that the earlier tests did not catch."""
import importlib.util
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_index  # noqa: E402


def load(rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location("errata_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MatrixCheckTests(unittest.TestCase):
    """The V1 check must reject a wrong product at every size; before the fix it accepted anything at the sizes
    where its seeded 0/1 vector was all zeros (n = 1, 2, 3, 4, 6, 8, 10, ...)."""

    def test_rejects_every_single_entry_error(self):
        harness = load("pairs/matrix-multiplication-naive-vs-strassen/harness.py")
        naive = load("pairs/matrix-multiplication-naive-vs-strassen/implementations/naive.py")
        multiply = next(getattr(naive, k) for k in dir(naive) if callable(getattr(naive, k)) and not k.startswith("_"))
        rng = random.Random(20261007)
        for n in list(range(1, 11)) + [14, 17, 31]:
            inst = harness.generate(n, rng)
            good = [list(row) for row in multiply(inst)]
            self.assertTrue(harness.check(inst, good), n)
            for _ in range(5):
                bad = [row[:] for row in good]
                i, j = rng.randrange(n), rng.randrange(n)
                bad[i][j] += rng.choice((-1, 1))
                self.assertFalse(harness.check(inst, bad), (n, i, j))

    def test_rejects_wrong_shape(self):
        harness = load("pairs/matrix-multiplication-naive-vs-strassen/harness.py")
        inst = harness.generate(3, random.Random(1))
        self.assertFalse(harness.check(inst, [[0, 0, 0], [0, 0, 0]]))


class ThreeXorDeepTrieTests(unittest.TestCase):
    """The Patricia trie must not hit Python's recursion limit: w distinct powers of two give w - 1 branching levels."""

    def test_deep_tries(self):
        trie = load("pairs/three-xor-all-triples-vs-patricia-trie/implementations/patricia_trie.py")
        for w in (1024, 2048):
            self.assertIsNone(trie.three_xor_patricia_trie((w, tuple(1 << i for i in range(w)))))
        values = tuple(1 << i for i in range(1000)) + ((1 << 3) ^ (1 << 700),)
        self.assertEqual(trie.three_xor_patricia_trie((1000, values)), (3, 700, 1000))


class TableHeadlineTests(unittest.TestCase):
    """The README table shows the leading bound only; it must not end in a dangling sentence fragment."""

    def test_sentence_boundary(self):
        self.assertEqual(build_index.short_complexity("Theta(n^3 2^n). Exactly n(n-1)(n+2)2^(n-3)"), "Theta(n^3 2^n)")
        self.assertEqual(build_index.short_complexity("Theta(n! n^2) on every input. Exactly n! (n(n-1)/2 + 1) - 1"),
                         "Theta(n! n^2) on every input")
        self.assertEqual(build_index.short_complexity("O(V E^2): O(V E) augmentations"), "O(V E^2)")


class PrimalityOracleGuardTests(unittest.TestCase):
    """The deterministic Miller-Rabin oracle must refuse inputs at or above the smallest composite that passes its
    twelve bases; before the fix its guard admitted that composite and called it prime."""

    def test_guard(self):
        harness = load("pairs/primality-trial-vs-aks/harness.py")
        psi12 = 318665857834031151167461
        self.assertEqual(399165290221 * 798330580441, psi12)
        with self.assertRaises(ValueError):
            harness._is_prime_det(psi12)

    def test_agrees_with_trial_division_on_small_numbers(self):
        harness = load("pairs/primality-trial-vs-aks/harness.py")

        def trial(x):
            return x >= 2 and all(x % d for d in range(2, int(x ** 0.5) + 1))
        self.assertEqual([x for x in range(20000) if harness._is_prime_det(x)], [x for x in range(20000) if trial(x)])


if __name__ == "__main__":
    unittest.main()
