"""Tests for search/flipgraph.py: flips, reductions and plus transitions preserve the tensor exactly, reductions
lower the rank correctly, and the bookkeeping stays consistent.

Run:  python -m unittest discover -s tests
"""
import random
import sys
import unittest
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search.flipgraph import FlipGraphState, find_dependency  # noqa: E402
from search.gf2mm import scheme_tensor, standard_scheme, verify  # noqa: E402

BIG = (4, 4, 4)  # 16-bit factors; scheme_tensor works for arbitrary terms, not only correct schemes


def tensor(terms, fmt=BIG):
    return scheme_tensor(fmt, terms)


def no_reduction_available(state):
    """Brute force: no group of terms sharing a factor has linearly dependent factors in another position."""
    for p in range(3):
        for v, g in state.groups[p].items():
            for q in range(3):
                if q == p:
                    continue
                vals = [state.t[x][q] for x in g]
                if state.linear:
                    for k in range(2, len(vals) + 1):
                        for sub in combinations(vals, k):
                            acc = 0
                            for x in sub:
                                acc ^= x
                            if acc == 0:
                                return False
                elif len(set(vals)) < len(vals):
                    return False
    return True


class FindDependency(unittest.TestCase):
    def test_against_brute_force(self):
        rng = random.Random(3)
        for _ in range(400):
            vals = [rng.randrange(1, 16) for _ in range(rng.randrange(1, 6))]
            comb = find_dependency(vals)
            brute = any(
                not __import__("functools").reduce(lambda a, b: a ^ b, sub, 0)
                for k in range(1, len(vals) + 1) for sub in combinations(vals, k))
            self.assertEqual(comb is not None, brute, vals)
            if comb is not None:
                acc = 0
                for i, v in enumerate(vals):
                    if (comb >> i) & 1:
                        acc ^= v
                self.assertEqual(acc, 0)
                self.assertNotEqual(comb, 0)


class FlipsPreserveTensor(unittest.TestCase):
    def test_flip_identity_all_positions(self):
        # two terms sharing the factor in position p; one flip must keep the sum
        rng = random.Random(11)
        for p in range(3):
            for _ in range(30):
                shared = rng.randrange(1, 1 << 16)
                t1 = [rng.randrange(1, 1 << 16) for _ in range(3)]
                t2 = [rng.randrange(1, 1 << 16) for _ in range(3)]
                t1[p] = t2[p] = shared
                before = tensor([t1, t2])
                st = FlipGraphState([t1, t2], random.Random(rng.random()), "pair")
                if st.rank < 2:      # the random pair happened to be reducible
                    self.assertEqual(tensor(st.scheme()), before)
                    continue
                self.assertTrue(st.flip())
                self.assertEqual(tensor(st.scheme()), before)

    def test_many_flips_on_3x3_keep_a_correct_scheme(self):
        st = FlipGraphState(standard_scheme((3, 3, 3)), random.Random(5))
        for step in range(3000):
            st.flip()
            self.assertTrue(verify((3, 3, 3), st.scheme()), f"step {step}")
            if step % 500 == 0:
                st.check_invariants()
        st.check_invariants()
        self.assertLess(st.rank, 27)  # some reduction happened (seed 5)

    def test_flips_on_rectangular_format(self):
        fmt = (2, 3, 4)
        for reduction in ("linear", "pair"):
            st = FlipGraphState(standard_scheme(fmt), random.Random(9), reduction)
            for _ in range(2000):
                st.flip()
            self.assertTrue(verify(fmt, st.scheme()))
            st.check_invariants()

    def test_random_tensors_invariant_under_all_moves(self):
        rng = random.Random(21)
        for trial in range(20):
            terms = [[rng.randrange(1, 1 << 4) for _ in range(3)] for _ in range(12)]
            before = tensor(terms)
            st = FlipGraphState(terms, random.Random(trial), "linear" if trial % 2 else "pair")
            self.assertEqual(tensor(st.scheme()), before)
            for k in range(300):
                if k % 37 == 0:
                    st.plus()
                else:
                    st.flip()
                self.assertEqual(tensor(st.scheme()), before)
            st.check_invariants()
            self.assertTrue(no_reduction_available(st))


class Reductions(unittest.TestCase):
    def test_r2_merge_two_shared_factors(self):
        a, b, c, c2 = 0b1, 0b10, 0b100, 0b1000
        for pos in range(3):  # the unshared factor may be in any position
            t1, t2 = [a, b, a | b], [a, b, a | b]
            t1[pos], t2[pos] = c, c2
            st = FlipGraphState([t1, t2, [7, 7, 7]], random.Random(0), "pair")
            self.assertEqual(st.rank, 2)
            merged = [t1[:], [7, 7, 7]]
            merged[0][pos] = c ^ c2
            self.assertEqual(sorted(st.scheme()), sorted(tuple(x) for x in merged))

    def test_r1_r2_cancel_to_zero(self):
        st = FlipGraphState([[1, 2, 3], [1, 2, 3], [5, 6, 7]], random.Random(0), "pair")
        self.assertEqual(st.scheme(), [(5, 6, 7)])

    def test_zero_factor_terms_dropped(self):
        st = FlipGraphState([[1, 0, 3], [5, 6, 7]], random.Random(0))
        self.assertEqual(st.scheme(), [(5, 6, 7)])

    def test_r3_linear_dependence(self):
        a = 0b1
        terms = [[a, 0b01, 0b001], [a, 0b10, 0b010], [a, 0b11, 0b100]]  # b3 = b1 + b2
        before = tensor(terms)
        lin = FlipGraphState(terms, random.Random(0), "linear")
        self.assertEqual(lin.rank, 2)
        self.assertEqual(tensor(lin.scheme()), before)
        pair = FlipGraphState(terms, random.Random(0), "pair")
        self.assertEqual(pair.rank, 3)  # R3 is not a pair reduction

    def test_reduction_after_flip_lowers_rank_and_keeps_tensor(self):
        # standard 2x2: reductions reach rank 7 quickly; every rank decrease keeps a correct scheme
        st = FlipGraphState(standard_scheme((2, 2, 2)), random.Random(1))
        ranks = {st.rank}
        for _ in range(5000):
            if not st.flip():
                break
            ranks.add(st.rank)
            self.assertTrue(verify((2, 2, 2), st.scheme()))
        self.assertIn(7, ranks)
        self.assertTrue(no_reduction_available(st))


class Lookahead(unittest.TestCase):
    """reducing_flips() must return exactly the flips after which the rank drops (brute force over all flips)."""

    def brute(self, st):
        hits = set()
        terms = {tid: list(x) for tid, x in st.t.items()}
        for p in range(3):
            for v, g in st.groups[p].items():
                for i in g:
                    for j in g:
                        if i == j:
                            continue
                        for q in range(3):
                            if q == p:
                                continue
                            r = 3 - p - q
                            new = {k: list(x) for k, x in terms.items()}
                            new[i][q] ^= terms[j][q]
                            new[j][r] ^= terms[i][r]
                            fresh = FlipGraphState(list(new.values()), random.Random(0), st.linear and "linear" or "pair")
                            if fresh.rank < st.rank:
                                hits.add((i, j, p, q, r))
        return hits

    def test_matches_brute_force(self):
        # random terms with 4-bit factors: coincidences are frequent, so most states have reducing flips
        # (matmul states from short walks almost never do, which would make the test vacuous)
        rng = random.Random(1)
        checked = nonempty = 0
        for reduction in ("linear", "pair"):
            for trial in range(25):
                terms = [[rng.randrange(1, 16) for _ in range(3)] for _ in range(12)]
                st = FlipGraphState(terms, random.Random(trial), reduction)
                before_tensor = tensor(st.scheme())
                for _ in range(2):
                    got = set(st.reducing_flips())
                    self.assertEqual(got, self.brute(st), (reduction, trial))
                    checked += 1
                    nonempty += bool(got)
                    before = st.rank
                    if got:
                        st.apply_flip(*sorted(got)[0])
                        self.assertLess(st.rank, before)
                        self.assertEqual(tensor(st.scheme()), before_tensor)
                    else:
                        st.flip()
        self.assertEqual(checked, 100)
        self.assertGreater(nonempty, 50)

    def test_lookahead_on_matmul_state_is_consistent(self):
        st = FlipGraphState(standard_scheme((3, 3, 3)), random.Random(2))
        for _ in range(300):
            st.flip()
        self.assertEqual(set(st.reducing_flips()), self.brute(st))


class WeightCap(unittest.TestCase):
    def test_cap_respected_and_tensor_kept(self):
        st = FlipGraphState(standard_scheme((3, 3, 3)), random.Random(8), "linear", max_weight=3)
        for _ in range(5000):
            st.flip()
        self.assertTrue(verify((3, 3, 3), st.scheme()))
        self.assertGreater(st.n_rejected, 0)
        # factors created by flips respect the cap; reductions (sums of factors) may exceed it
        self.assertGreater(st.n_flips, 0)
        st.check_invariants()

    def test_cap_zero_is_identical_to_no_cap(self):
        a = FlipGraphState(standard_scheme((3, 3, 3)), random.Random(4))
        b = FlipGraphState(standard_scheme((3, 3, 3)), random.Random(4), "linear", max_weight=0)
        for _ in range(3000):
            a.flip()
            b.flip()
        self.assertEqual(sorted(a.scheme()), sorted(b.scheme()))


class PlusTransition(unittest.TestCase):
    def test_plus_raises_rank_by_one_and_keeps_tensor(self):
        terms = [[0b0001, 0b0010, 0b0100], [0b1000, 0b0011, 0b0110]]  # no shared factor
        before = tensor(terms)
        for seed in range(12):
            st = FlipGraphState(terms, random.Random(seed))
            self.assertTrue(st.plus())
            self.assertEqual(st.rank, 3)
            self.assertEqual(tensor(st.scheme()), before)
            st.check_invariants()

    def test_plus_needs_a_pair_without_common_factor(self):
        st = FlipGraphState([[1, 2, 4], [1, 8, 16]], random.Random(0))
        self.assertFalse(st.plus())


class Determinism(unittest.TestCase):
    def test_same_seed_same_scheme(self):
        out = []
        for _ in range(2):
            st = FlipGraphState(standard_scheme((3, 3, 3)), random.Random(42))
            for k in range(5000):
                st.flip()
                if k % 1000 == 999:
                    st.plus()
            out.append(sorted(st.scheme()))
        self.assertEqual(out[0], out[1])


if __name__ == "__main__":
    unittest.main()
