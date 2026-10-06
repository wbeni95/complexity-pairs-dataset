"""Tests for search/driver.py and search/lowrank.py: walks are reproducible, end in verified schemes, and the
exhaustive rank test agrees with an independent brute-force rank computation.

Run:  python -m unittest discover -s tests
"""
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search import lowrank  # noqa: E402
from search.driver import WalkConfig, run_walk  # noqa: E402
from search.gf2mm import dims, mm_tensor, standard_scheme, verify, verify_explicit  # noqa: E402


class Walks(unittest.TestCase):
    def test_2x2_reaches_rank_7_and_is_reproducible(self):
        cfg = dict(fmt=(2, 2, 2), seed=1, max_flips=100_000, plateau=2_000, target_rank=7, verify_every=4096)
        r1 = run_walk(WalkConfig(**cfg))
        r2 = run_walk(WalkConfig(**cfg))
        self.assertEqual(r1["best_rank"], 7)
        self.assertEqual(r1["stopped_by"], "target")
        self.assertTrue(verify((2, 2, 2), r1["best_scheme"]))
        self.assertTrue(verify_explicit((2, 2, 2), r1["best_scheme"]))
        self.assertEqual(r1["trajectory"][-1][:2], r2["trajectory"][-1][:2])
        self.assertEqual(sorted(r1["best_scheme"]), sorted(r2["best_scheme"]))

    def test_3x3_short_walk_with_log(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "run.jsonl"
            res = run_walk(WalkConfig(fmt=(3, 3, 3), seed=1, max_flips=150_000, plateau=20_000,
                                      verify_every=8192, log_every=8192, keep_ranks_upto=25), logfile=str(log))
            events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(events[0]["event"], "start")
        self.assertEqual(events[-1]["event"], "end")
        self.assertLessEqual(res["best_rank"], 25)
        self.assertTrue(verify((3, 3, 3), res["best_scheme"]))
        for r, (flips, secs, scheme) in res["first_at_rank"].items():
            self.assertEqual(len(scheme), r)
            self.assertTrue(verify((3, 3, 3), scheme))
        self.assertGreater(res["full_verifications_passed"], 5)

    def test_escape_variants_run_and_stay_correct(self):
        for escape in ("plus", "restart", "none"):
            res = run_walk(WalkConfig(fmt=(2, 3, 3), seed=3, max_flips=30_000, plateau=1_000, escape=escape,
                                      verify_every=4096))
            self.assertTrue(verify((2, 3, 3), res["best_scheme"]), escape)
            self.assertLessEqual(res["best_rank"], 18)

    def test_dead_end_start_escapes_with_plus_transitions(self):
        # Strassen's rank-7 scheme has no shared factor: no flip is available, so the first step must escape
        from search.gf2mm import strassen_scheme
        for k in (1, 3):
            res = run_walk(WalkConfig(fmt=(2, 2, 2), seed=1, max_flips=1, plateau=10, slack=3, plus_per_escape=k),
                           start=strassen_scheme())
            self.assertEqual(res["no_flip_available_events"], 1)
            self.assertEqual(res["plus_transitions"], k)
            self.assertEqual(res["best_rank"], 7)
            self.assertTrue(verify((2, 2, 2), res["best_scheme"]))

    def test_invalid_start_rejected(self):
        bad = standard_scheme((2, 2, 2))[1:]
        with self.assertRaises(ValueError):
            run_walk(WalkConfig(fmt=(2, 2, 2), seed=1, max_flips=10), start=bad)


def bfs_ranks(shape):
    """Exact GF(2) rank of every tensor of the given shape by breadth-first sumset expansion (independent of
    search.lowrank). Tensors are ints with bit (x * nb + y) * nc + z."""
    na, nb, nc = shape
    ones = []
    for a in range(1, 1 << na):
        for b in range(1, 1 << nb):
            for c in range(1, 1 << nc):
                t = 0
                for x in range(na):
                    if (a >> x) & 1:
                        for y in range(nb):
                            if (b >> y) & 1:
                                for z in range(nc):
                                    if (c >> z) & 1:
                                        t ^= 1 << ((x * nb + y) * nc + z)
                ones.append(t)
    rank = {0: 0}
    frontier = [0]
    r = 0
    while frontier:
        r += 1
        nxt = []
        for t in frontier:
            for o in ones:
                u = t ^ o
                if u not in rank:
                    rank[u] = r
                    nxt.append(u)
        frontier = nxt
    return rank


class ExhaustiveRank(unittest.TestCase):
    def test_agrees_with_bfs_on_all_2x2x3_tensors(self):
        na, nb, nc = 2, 2, 3
        ranks = bfs_ranks((na, nb, nc))
        self.assertEqual(len(ranks), 1 << (na * nb * nc))
        for t, r in ranks.items():
            slices = [(t >> (x * nb * nc)) & ((1 << (nb * nc)) - 1) for x in range(na)]
            self.assertTrue(lowrank.rank_at_most(slices, nb, nc, r)[0], (t, r))
            if r > 0:
                self.assertFalse(lowrank.rank_at_most(slices, nb, nc, r - 1)[0], (t, r))

    def test_mm_2x2x2_has_no_rank_6_scheme_over_gf2(self):
        ans, _, stats = lowrank.mm_rank_at_most((2, 2, 2), 6)
        self.assertFalse(ans)
        self.assertEqual(stats["dim_S"], 4)

    def test_mm_2x2x2_rank_7_witness_is_a_valid_scheme(self):
        ans, witness, _ = lowrank.mm_rank_at_most((2, 2, 2), 7)
        self.assertTrue(ans)
        terms = lowrank.decomposition_from_witness(mm_tensor((2, 2, 2)), witness, dims((2, 2, 2))[2])
        self.assertLessEqual(len(terms), 7)
        self.assertTrue(verify((2, 2, 2), terms))

    def test_matrix_vector_formats(self):
        self.assertFalse(lowrank.mm_rank_at_most((1, 2, 2), 3)[0])
        self.assertTrue(lowrank.mm_rank_at_most((1, 2, 2), 4)[0])

    def test_random_low_rank_tensors_detected(self):
        rng = random.Random(4)
        nb, nc = 3, 3
        for _ in range(20):
            r = rng.randrange(1, 4)
            terms = [(rng.randrange(1, 4), rng.randrange(1, 8), rng.randrange(1, 8)) for _ in range(r)]
            slices = [0, 0]
            for a, b, c in terms:
                M = lowrank._outer_bc(b, c, nc)
                for x in range(2):
                    if (a >> x) & 1:
                        slices[x] ^= M
            self.assertTrue(lowrank.rank_at_most(slices, nb, nc, r)[0])


if __name__ == "__main__":
    unittest.main()
