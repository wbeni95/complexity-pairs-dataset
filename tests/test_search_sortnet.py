"""Tests for search/sortnet.py: the 0-1-principle verifier agrees with an exhaustive permutation check, rejects
broken networks, and the search returns verified networks.

Run:  python -m unittest discover -s tests
"""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search import sortnet  # noqa: E402

# A standard 5-comparator network for n = 4 and a 9-comparator network for n = 5 (insertion-style, verified below).
NET4 = [(0, 1), (2, 3), (0, 2), (1, 3), (1, 2)]
BUBBLE5 = [(i, i + 1) for k in range(4, 0, -1) for i in range(k)]   # bubble sort, 10 comparators


class Verifier(unittest.TestCase):
    def test_known_networks(self):
        self.assertTrue(sortnet.sorts(4, NET4))
        self.assertTrue(sortnet.sorts_permutations(4, NET4))
        self.assertTrue(sortnet.sorts(5, BUBBLE5))
        self.assertTrue(sortnet.sorts_permutations(5, BUBBLE5))
        self.assertTrue(sortnet.sorts(1, []))

    def test_every_single_deletion_of_net4_is_rejected(self):
        for k in range(len(NET4)):
            bad = NET4[:k] + NET4[k + 1:]
            self.assertFalse(sortnet.sorts(4, bad))
            self.assertFalse(sortnet.sorts_permutations(4, bad))

    def test_agrees_with_permutation_check_on_random_networks(self):
        rng = random.Random(2)
        agree = sorted_count = 0
        for _ in range(300):
            n = rng.randrange(2, 6)
            net = []
            for _ in range(rng.randrange(0, 12)):
                i = rng.randrange(n - 1)
                net.append((i, rng.randrange(i + 1, n)))
            a, b = sortnet.sorts(n, net), sortnet.sorts_permutations(n, net)
            self.assertEqual(a, b, (n, net))
            agree += 1
            sorted_count += a
        self.assertEqual(agree, 300)
        self.assertGreater(sorted_count, 0)   # the battery contains sorting networks too

    def test_bad_comparator_raises(self):
        with self.assertRaises(ValueError):
            sortnet.sorts(3, [(1, 0)])
        with self.assertRaises(ValueError):
            sortnet.sorts(3, [(0, 3)])


class Search(unittest.TestCase):
    def test_small_n_reach_information_theoretic_optimum(self):
        # ceil(log2 n!) = 1, 3, 5 for n = 2, 3, 4 is a lower bound, so these sizes are optimal
        for n, opt in ((2, 1), (3, 3), (4, 5)):
            net, stats = sortnet.search(n, seed=1, tries=20)
            self.assertTrue(sortnet.sorts(n, net))
            self.assertTrue(sortnet.sorts_permutations(n, net))
            self.assertEqual(len(net), opt)

    def test_search_n5_verified(self):
        net, _ = sortnet.search(5, seed=1, tries=10)
        self.assertTrue(sortnet.sorts_permutations(5, net))
        self.assertGreaterEqual(len(net), 9)   # 9 is the known optimum (cited, not proven here)


if __name__ == "__main__":
    unittest.main()
