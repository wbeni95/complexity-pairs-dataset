"""Deterministic check of Lemma 0.1 in pairs/permanent-naive-vs-ryser/PROOFS.md: the costs of the documented
"roughly equivalent" Python code of itertools.permutations (used by the enumerations of permanent-naive-vs-ryser,
first-match-rule-ordering-enumeration-vs-subset-dp, linear-ordering-enumeration-vs-subset-dp and
hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion).

For n = 0..8: the documented code yields exactly the tuples of itertools.permutations(range(n)) in the same order;
its for-loop body runs sum_{k=0..n-1} n!/k! times and its rotations move as many entries in total (both <= e n!);
the largest rotation work between two yields is n(n-1)/2 (n >= 2), and n(n+1)/2 in the final pass; its state is
three lists of n entries. The C implementation is not measured: that it has the same costs is the machine-model
assumption listed in the entries' background.
"""
import itertools
import math
import unittest


def documented_permutations(n, stats):
    """The documented code of itertools.permutations(range(n)) (r = n), instrumented with counters."""
    pool = tuple(range(n))
    r = n
    indices = list(range(n))
    cycles = list(range(n, n - r, -1))
    stats["state"] = max(stats["state"], len(pool) + len(indices) + len(cycles))
    yield tuple(pool[i] for i in indices[:r])
    while n:
        moved = 0
        for i in reversed(range(r)):
            stats["iterations"] += 1
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i + 1:] + indices[i:i + 1]
                stats["rotated"] += n - i
                moved += n - i
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                stats["max_between_yields"] = max(stats["max_between_yields"], moved)
                yield tuple(pool[i] for i in indices[:r])
                break
        else:
            stats["final_pass"] = moved
            return


class DocumentedPermutations(unittest.TestCase):
    def test_lemma(self):
        for n in range(0, 9):
            stats = {"iterations": 0, "rotated": 0, "max_between_yields": 0, "final_pass": None, "state": 0}
            out = list(documented_permutations(n, stats))
            self.assertEqual(out, list(itertools.permutations(range(n))))
            self.assertEqual(len(out), math.factorial(n))
            total = sum(math.factorial(n) // math.factorial(k) for k in range(n))
            self.assertEqual(stats["iterations"], total)
            self.assertEqual(stats["rotated"], total)
            self.assertLessEqual(total, math.e * math.factorial(n))
            self.assertEqual(stats["state"], 3 * n)
            if n >= 2:
                self.assertEqual(stats["max_between_yields"], n * (n - 1) // 2)
            if n >= 1:
                self.assertEqual(stats["final_pass"], n * (n + 1) // 2)


if __name__ == "__main__":
    unittest.main()
