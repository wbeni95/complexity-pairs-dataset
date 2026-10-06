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
        restarts_seen = 0
        for fmt, seed, steps, plateau, cap, slack in [c + (3,) for c in cases] + [c + (0,) for c in restart_cases]:
            start = gf2mm.standard_scheme(fmt)
            ref = kernel_reference.walk(start, seed, steps, plateau=plateau, slack=slack, max_weight=cap)
            restarts_seen += ref["restarts"]
            got = rust_kernel.run(fmt, start, seed=seed, max_steps=steps, max_seconds=1e9, plateau=plateau,
                                  slack=slack, max_weight=cap)
            with self.subTest(fmt=fmt, seed=seed, plateau=plateau, cap=cap):
                self.assertEqual([tuple(t) for t in got["best"]], [tuple(t) for t in ref["best"]])
                self.assertEqual(int(got["stats"]["steps"]), ref["steps"])
                for key in ("flips", "rejected_weight", "plus", "restarts"):
                    self.assertEqual(int(got["stats"][key]), ref[key], key)
                self.assertEqual([(r, s) for r, s, _ in got["improvements"]], ref["improvements"])
        self.assertGreater(restarts_seen, 0, "the restart branch must be exercised by the differential test")

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
