"""Checks of the proofs in pairs/inversion-counting-quadratic-vs-merge/PROOFS.md, sections 3-5.

Runs the unchanged implementations with in-memory instrumentation only (profiler and trace hooks). Fixed seeds and
stated ranges; deterministic. The exact comparison counts (sections 1-2) are checked by the scripts named there.
"""
import importlib.util
import itertools
import math
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "inversion-counting-quadratic-vs-merge"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, E / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


QUAD = _load("implementations/pairs_scan.py", "proofs_inv_quad").inversions_quadratic
MERGE_MOD = _load("implementations/merge_count.py", "proofs_inv_merge")
MERGE = MERGE_MOD.inversions_merge
SORT_COUNT = MERGE_MOD._sort_count


def inv(s):
    return sum(1 for i in range(len(s)) for j in range(i + 1, len(s)) if s[i] > s[j])


def lo_hi(N):
    lo, hi = [0] * (N + 1), [0] * (N + 1)
    for n in range(2, N + 1):
        a, b = n // 2, n - n // 2
        lo[n] = lo[a] + lo[b] + a
        hi[n] = hi[a] + hi[b] + n - 1
    return lo, hi


def clog2(n):
    return (n - 1).bit_length() if n >= 1 else 0


class InversionProofs(unittest.TestCase):
    def test_correct_exhaustive(self):
        seqs = [s for L in range(8) for s in itertools.product(range(3), repeat=L)]
        self.assertEqual(len(seqs), 3280)
        rng = random.Random(1)
        for _ in range(300):
            n = rng.randint(0, 60)
            seqs.append(tuple(rng.randint(0, n // 3) for _ in range(n)))
        for s in seqs:
            want = inv(s)
            self.assertEqual(QUAD(s), want, s)
            self.assertEqual(MERGE(s), want, s)
            merged, count = SORT_COUNT(list(s))
            self.assertEqual(merged, sorted(s))
            self.assertEqual(count, want)

    def test_level_bounds(self):
        lo, hi = lo_hi(5000)
        for n in range(2, 5001):
            self.assertLessEqual(n * (n.bit_length() - 1), 3 * lo[n], n)  # (n/3) floor(log2 n) <= lo(n)
            self.assertLessEqual(hi[n], n * clog2(n), n)

    def test_call_lengths(self):
        code = SORT_COUNT.__code__
        for n in range(1, 301):
            depth, rows = [0], []

            def prof(frame, event, _arg):
                if frame.f_code is code:
                    if event == "call":
                        rows.append((depth[0], len(frame.f_locals["a"])))
                        depth[0] += 1
                    elif event == "return":
                        depth[0] -= 1

            sys.setprofile(prof)
            try:
                MERGE(tuple(range(n, 0, -1)))
            finally:
                sys.setprofile(None)
            self.assertEqual(len(rows), 2 * n - 1, n)
            for d, L in rows:
                self.assertIn(L, (n >> d, -(-n // (1 << d))), (n, d, L))

    def test_space(self):
        code = SORT_COUNT.__code__
        rng = random.Random(2)
        for n in list(range(65)) + [100, 500, 1000]:
            values = tuple(rng.randint(0, n) for _ in range(n))
            frames, peak, depth, best = [], [0], [0], [0]

            def local(frame, event, _arg):
                if event == "line":
                    total = 0
                    for f in frames:
                        loc = f.f_locals
                        for name in ("a", "left", "right", "merged"):
                            v = loc.get(name)
                            if isinstance(v, list):
                                total += len(v)
                    peak[0] = max(peak[0], total)
                elif event == "return":
                    frames.pop()
                    depth[0] -= 1
                return local

            def glob(frame, event, _arg):
                if frame.f_code is code:
                    frames.append(frame)
                    depth[0] += 1
                    best[0] = max(best[0], depth[0])
                    return local
                return None

            sys.settrace(glob)
            try:
                MERGE(values)
            finally:
                sys.settrace(None)
            self.assertGreaterEqual(peak[0], n)
            self.assertLessEqual(peak[0], 6 * n + 3 * clog2(n) + 3, n)
            self.assertEqual(best[0], clog2(n) + 1 if n >= 1 else 1, n)
        # all pairs: no list among the locals other than the input
        seen = set()

        def local_q(frame, event, _arg):
            if event == "line":
                for name, v in frame.f_locals.items():
                    if name != "values":
                        seen.add(type(v).__name__)
            return local_q

        sys.settrace(lambda f, e, a: local_q if f.f_code is QUAD.__code__ else None)
        try:
            QUAD(tuple(rng.randint(0, 50) for _ in range(50)))
        finally:
            sys.settrace(None)
        self.assertTrue(seen <= {"int"}, seen)


if __name__ == "__main__":
    unittest.main()
