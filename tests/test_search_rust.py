"""Tests for the Rust flip-graph kernel (search/kernel/flipwalk.rs) and its Python wrapper.

The kernel is treated as untrusted: these tests check that it builds, that it behaves exactly like the
line-by-line Python mirror (differential test: identical seeds give identical results), that its results
pass the exact verifier, and that bad input and corrupted results are rejected. Skipped without rustc.

Run:  python -m unittest tests.test_search_rust
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from search import gf2mm, kernel_reference, rust_kernel  # noqa: E402


class PlusTransitionTests(unittest.TestCase):
    """Regression test for RL-052: the first plus transition was undone at once by the merge rule."""

    def test_plus_transition_preserves_tensor_and_raises_rank(self):
        for fmt in ((2, 2, 2), (3, 3, 3)):
            terms = [list(t) for t in gf2mm.standard_scheme(fmt)]
            rng = kernel_reference.SplitMix64(9)
            done = 0
            while done < 50:
                done += kernel_reference.plus_transition(terms, rng, 0)
            self.assertGreater(len(terms), len(gf2mm.standard_scheme(fmt)))
            self.assertTrue(gf2mm.verify(fmt, [tuple(t) for t in terms]))


def shares_a_factor(terms) -> bool:
    """Brute force, independent of the kernel's bookkeeping: do two terms share a factor in some position?"""
    return any(terms[i][p] == terms[j][p] for i in range(len(terms)) for j in range(i) for p in range(3))


class DeadEndTests(unittest.TestCase):
    """Dead-end detection (research/2026-10-06c_kernel_deadends.md) must be exact in both directions: it fires only
    at schemes where no two terms share a factor, and it does fire at such a scheme (here Strassen's)."""

    def test_detection_fires_only_at_true_dead_ends(self):
        seen = []

        def check(terms, best_rank):
            seen.append((len(terms), best_rank))
            self.assertFalse(shares_a_factor(terms), "dead end reported at a scheme that still admits a flip")

        for fmt, seed, plateau, slack in (((2, 2, 2), 3, 10**9, 3), ((2, 2, 2), 11, 10**9, 0),
                                          ((3, 3, 3), 5, 300, 3), ((2, 2, 3), 2, 10**9, 3)):
            res = kernel_reference.walk(gf2mm.standard_scheme(fmt), seed, 6000, plateau=plateau, slack=slack,
                                        on_dead_end=check)
            self.assertTrue(gf2mm.verify(fmt, res["best"]))
        self.assertGreater(len(seen), 0, "the dead-end branch must be exercised")

    def test_strassen_dead_end_is_left_without_waiting_for_the_plateau(self):
        start = gf2mm.strassen_scheme()
        self.assertFalse(shares_a_factor(start))  # Strassen's scheme admits no flip
        old = kernel_reference.walk(start, 1, 3000, plateau=10**9, dead_end=False)
        self.assertEqual((old["flips"], old["plus"], old["restarts"], old["dead_ends"]), (0, 0, 0, 0))
        new = kernel_reference.walk(start, 1, 3000, plateau=10**9, dead_end=True)
        self.assertGreater(new["dead_ends"], 0)
        self.assertGreater(new["plus"], 0)
        self.assertGreater(new["flips"], 0)
        self.assertEqual(len(new["best"]), 7)  # a walk never loses its best rank
        self.assertTrue(gf2mm.verify((2, 2, 2), new["best"]))


@unittest.skipUnless(rust_kernel.rustc_available(), "rustc not installed")
class RustKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build_info = rust_kernel.build()

    def test_differential_against_python_mirror(self):
        cases = [
            ((2, 2, 2), 1, 2000, 300, 0),
            ((2, 2, 2), 7, 2000, 50, 0),     # small plateau: exercises plus transitions and restarts
            ((3, 3, 3), 2, 4000, 400, 0),
            ((3, 3, 3), 3, 4000, 100, 3),    # weight cap: exercises the rejection path
        ]
        restart_cases = [((2, 2, 2), 5, 3000, 20, 0), ((3, 3, 3), 4, 3000, 15, 0)]  # slack 0: exercises restarts
        # Large plateau: only the dead-end branch can move the walk off Strassen-like dead ends (2x2 reaches 7).
        dead_end_cases = [((2, 2, 2), 3, 6000, 10**9, 0), ((2, 2, 3), 2, 6000, 10**9, 0)]
        configs = [c + (3,) for c in cases] + [c + (0,) for c in restart_cases]
        configs += [c + (3,) for c in dead_end_cases] + [((2, 2, 2), 11, 6000, 10**9, 0, 0)]
        # The restart and the plus transition after a dead end run through the same code block as after a plateau,
        # so the restart assertion below (with the escape on) covers that block. A dead end above best + slack, the
        # only case in which a dead end leads to a restart, never occurred in the small-format walks we tried
        # (research/2026-10-06c_kernel_deadends.md), so it is not asserted separately.
        restarts_seen = {True: 0, False: 0}
        dead_ends_seen = {True: 0, False: 0}
        for fmt, seed, steps, plateau, cap, slack in configs:
            start = gf2mm.standard_scheme(fmt)
            for dead_end in (True, False):
                ref = kernel_reference.walk(start, seed, steps, plateau=plateau, slack=slack, max_weight=cap,
                                            dead_end=dead_end)
                restarts_seen[dead_end] += ref["restarts"]
                dead_ends_seen[dead_end] += ref["dead_ends"]
                got = rust_kernel.run(fmt, start, seed=seed, max_steps=steps, max_seconds=1e9, plateau=plateau,
                                      slack=slack, max_weight=cap, dead_end=dead_end)
                with self.subTest(fmt=fmt, seed=seed, plateau=plateau, cap=cap, slack=slack, dead_end=dead_end):
                    self.assertEqual([tuple(t) for t in got["best"]], [tuple(t) for t in ref["best"]])
                    self.assertEqual(int(got["stats"]["steps"]), ref["steps"])
                    for key in ("flips", "rejected_weight", "plus", "restarts", "dead_ends"):
                        self.assertEqual(int(got["stats"][key]), ref[key], key)
                    self.assertEqual([(r, s) for r, s, _ in got["improvements"]], ref["improvements"])
        self.assertGreater(restarts_seen[True], 0, "the restart branch must be exercised (dead-end escape on)")
        self.assertGreater(restarts_seen[False], 0, "the restart branch must be exercised (dead-end escape off)")
        self.assertGreater(dead_ends_seen[True], 0, "the dead-end branch must be exercised by the differential test")
        self.assertEqual(dead_ends_seen[False], 0, "with the escape off, no dead end may be reported")

    def test_differential_from_strassen_squared(self):
        """4x4x4 from Strassen (x) Strassen (rank 49, no two terms share a factor, RL-059): the measured dead end."""
        fmt, start = gf2mm.kron_scheme((2, 2, 2), gf2mm.strassen_scheme(), (2, 2, 2), gf2mm.strassen_scheme())
        self.assertFalse(shares_a_factor(start))
        for seed, plateau in ((1, 10**9), (2, 5000)):
            for dead_end in (True, False):
                ref = kernel_reference.walk(start, seed, 20000, plateau=plateau, dead_end=dead_end)
                got = rust_kernel.run(fmt, start, seed=seed, max_steps=20000, max_seconds=1e9, plateau=plateau,
                                      dead_end=dead_end)
                with self.subTest(seed=seed, plateau=plateau, dead_end=dead_end):
                    self.assertEqual([tuple(t) for t in got["best"]], [tuple(t) for t in ref["best"]])
                    for key in ("steps", "flips", "rejected_weight", "plus", "restarts", "dead_ends"):
                        self.assertEqual(int(got["stats"][key]), ref[key], key)
                    if dead_end:
                        self.assertGreater(ref["dead_ends"], 0)
                    else:
                        self.assertEqual(ref["dead_ends"], 0)
                        if plateau == 10**9:
                            self.assertEqual(ref["flips"] + ref["plus"], 0)  # the old kernel idles here

    def test_differential_full_reduce(self):
        """--full-reduce 1 (linear-dependence reduction, research/2026-10-06d_exotic_formats.md): Rust and the mirror
        agree exactly; the new branch, plus transitions and restarts are all exercised; with the flag off the
        counter stays 0 and the trajectories equal the earlier kernel's (covered by the tests above)."""
        from tests.test_search_blocks import _dependent_triple_scheme
        configs = [((2, 2, 2), 1, 3000, 300, 0, 3), ((2, 2, 3), 2, 4000, 100, 0, 3), ((3, 3, 3), 3, 4000, 400, 0, 3),
                   ((3, 3, 3), 4, 3000, 15, 0, 0), ((3, 3, 3), 5, 3000, 100, 3, 3), ((2, 3, 4), 6, 4000, 50, 0, 1)]
        seen = {"dep_reductions": 0, "plus": 0, "restarts": 0, "dead_ends": 0}
        starts = [(c, gf2mm.standard_scheme(c[0])) for c in configs]
        fmt9, start9 = _dependent_triple_scheme(0)
        starts += [(((2, 2, 2), s, 2000, 500, 0, 3), start9) for s in (1, 2, 3)]
        for (fmt, seed, steps, plateau, cap, slack), start in starts:
            for full in (True, False):
                ref = kernel_reference.walk(start, seed, steps, plateau=plateau, slack=slack, max_weight=cap,
                                            full_reduce=full)
                got = rust_kernel.run(fmt, start, seed=seed, max_steps=steps, max_seconds=1e9, plateau=plateau,
                                      slack=slack, max_weight=cap, full_reduce=full)
                with self.subTest(fmt=fmt, seed=seed, plateau=plateau, cap=cap, slack=slack, full=full):
                    self.assertEqual([tuple(t) for t in got["best"]], [tuple(t) for t in ref["best"]])
                    for key in ("steps", "flips", "rejected_weight", "plus", "restarts", "dead_ends",
                                "dep_reductions"):
                        self.assertEqual(int(got["stats"][key]), ref[key], key)
                    self.assertEqual([(r, s) for r, s, _ in got["improvements"]], ref["improvements"])
                    if full:
                        for key in seen:
                            seen[key] += ref[key]
                    else:
                        self.assertEqual(ref["dep_reductions"], 0)
        for key, val in seen.items():
            self.assertGreater(val, 0, f"{key} must be exercised with --full-reduce 1")

    def test_reaches_strassen_rank_on_2x2(self):
        res = rust_kernel.run((2, 2, 2), gf2mm.standard_scheme((2, 2, 2)), seed=1, max_steps=2_000_000,
                              max_seconds=30, plateau=2000, target_rank=7)
        self.assertEqual(len(res["best"]), 7)
        self.assertTrue(res["verified"])
        self.assertTrue(gf2mm.verify_explicit((2, 2, 2), res["best"]))  # the second, independent verifier

    def test_bad_input_is_rejected_cleanly(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as f:
            f.write("3\n1 2 3\n4 5\n")  # malformed: second term has two factors, third term missing
        try:
            proc = subprocess.run([str(rust_kernel.BIN), "--input", path, "--max-steps", "10"],
                                  capture_output=True, text=True)
        finally:
            os.unlink(path)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("flipwalk:", proc.stderr)

    def test_corrupted_result_is_never_accepted(self):
        scheme = gf2mm.strassen_scheme()
        a, b, c = scheme[0]
        corrupted = [(a ^ 1, b, c)] + scheme[1:]
        with self.assertRaises(rust_kernel.KernelResultError):
            rust_kernel.check_result((2, 2, 2), corrupted, seed=1)


if __name__ == "__main__":
    unittest.main()
