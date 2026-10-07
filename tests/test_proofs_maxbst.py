"""Checks of PROOFS.md section 5 of pairs/max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp.

The triangulation correspondence, the characterisation of BST weights as separable tables, the size of the numbers,
and the time and space bounds. Runs the unchanged implementations with in-memory instrumentation only (profiler and
trace hooks). Fixed seeds and stated ranges; deterministic. The theorems of the README and the exact counts are
checked by tests/test_entry_max_cost_bst.py and experiments/2026-10-07_max_cost_bst_checks.py.
"""
import importlib.util
import itertools
import random
import sys
import unittest
from math import comb
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, E / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


REC = _load("implementations/recursion.py", "proofs_mcb_rec").maxbst_recursive
CUB = _load("implementations/cubic_dp.py", "proofs_mcb_cub").maxbst_cubic
END = _load("implementations/endpoint_dp.py", "proofs_mcb_end").maxbst_endpoint
H = _load("harness.py", "proofs_mcb_harness")


def trees(lo, hi):
    """Binary trees on nodes lo+1..hi as nested tuples (root, left, right); None is the empty tree."""
    if lo == hi:
        return [None]
    return [(k, left, right) for k in range(lo + 1, hi + 1) for left in trees(lo, k - 1) for right in trees(k, hi)]


def intervals(t, lo, hi, out):
    """Record (node, (lo, hi)) for every node of t, a tree on (lo, hi)."""
    if t is None:
        return out
    k, left, right = t
    out.append((k, (lo, hi)))
    intervals(left, lo, k - 1, out)
    intervals(right, k, hi, out)
    return out


def diagonals(t, n):
    """The triangulation of v_0..v_(n+1) of tree t: its set of diagonals {a, b} (a < b)."""
    return frozenset((lo, hi + 1) for _, (lo, hi) in intervals(t, 0, n, []) if (lo, hi) != (0, n))


def triangulations(a, b):
    """All triangulations of the convex polygon v_a..v_b as sets of diagonals strictly inside it (separate code)."""
    if b - a < 2:
        return [frozenset()]
    out = []
    for k in range(a + 1, b):
        for left in triangulations(a, k):
            for right in triangulations(k, b):
                extra = set()
                if k - a >= 2:
                    extra.add((a, k))
                if b - k >= 2:
                    extra.add((k, b))
                out.append(left | right | frozenset(extra))
    return out


class MaxCostBSTSection5(unittest.TestCase):
    def test_triangulation_correspondence(self):
        rng = random.Random(1)
        for n in range(8):
            ts = trees(0, n)
            self.assertEqual(len(ts), comb(2 * n, n) // (n + 1))
            diags = [diagonals(t, n) for t in ts]
            self.assertEqual(len(set(diags)), len(ts))
            self.assertEqual(set(diags), set(triangulations(0, n + 1)))
            omega = {(a, b): rng.randint(-9, 9) for a in range(n + 2) for b in range(a + 1, n + 2)}
            for t, dg in zip(ts, diags):
                self.assertEqual(len(dg), max(n - 1, 0))
                val = sum(omega[(lo, hi + 1)] for _, (lo, hi) in intervals(t, 0, n, []))
                self.assertEqual(val, sum(omega[d] for d in dg) + (omega[(0, n + 1)] if n >= 1 else 0))
                for rot, (lo, hi, k, kl) in self._rotations(t, n):
                    after = diagonals(rot, n)
                    self.assertEqual(dg - after, {(lo, k)})
                    self.assertEqual(after - dg, {(kl, hi + 1)})

    def _rotations(self, t, n):
        """Every right rotation of t: (rotated tree, (lo, hi, k, kL)) for each node k spanning (lo, hi) whose left
        subtree (root kL) is non-empty."""
        def rec(t, lo, hi):
            if t is None:
                return
            k, left, right = t
            if left is not None:
                kl, a, b = left
                yield (kl, a, (k, b, right)), (lo, hi, k, kl)
            for sub, info in rec(left, lo, k - 1):
                yield (k, sub, right), info
            for sub, info in rec(right, k, hi):
                yield (k, left, sub), info
        yield from rec(t, 0, n)

    def test_separable_tables(self):
        rng = random.Random(2)
        for _ in range(300):
            n = rng.randint(0, 9)
            F = {j: rng.randint(-20, 20) for j in range(1, n + 1)}
            G = {i: rng.randint(-20, 20) for i in range(n)}
            if n == 0:
                continue
            q = [-G[0]] + [F[i] - G[i] for i in range(1, n)] + [0]
            p = [F[1] - q[1]] + [F[j] - F[j - 1] - q[j] for j in range(2, n + 1)]
            w = H.bst_weights(p, q)
            for i in range(n):
                for j in range(i + 1, n + 1):
                    self.assertEqual(w[i][j], F[j] - G[i])

        def four_point(w, n):
            return all(w[a][c] + w[b][d] == w[a][d] + w[b][c]
                       for a, b, c, d in itertools.combinations(range(n + 1), 4))

        def has_FG(w, n):
            if n == 0:
                return True
            G = {0: 0}
            for i in range(n - 1):
                diffs = {w[i][j] - w[i + 1][j] for j in range(i + 2, n + 1)}
                if len(diffs) != 1:
                    return False
                G[i + 1] = G[i] + diffs.pop()
            F = {}
            for j in range(1, n + 1):
                vals = {w[i][j] + G[i] for i in range(j)}
                if len(vals) != 1:
                    return False
            return True

        rng = random.Random(3)
        for _ in range(300):
            n = rng.randint(0, 7)
            if rng.random() < 0.5:
                p = [rng.randint(-5, 5) for _ in range(n)]
                q = [rng.randint(-5, 5) for _ in range(n + 1)]
                w = H.bst_weights(p, q)
                self.assertTrue(four_point(w, n))
                self.assertTrue(has_FG(w, n))
            else:
                w = [[None] * (n + 1) for _ in range(n + 1)]
                for i in range(n + 1):
                    for j in range(i + 1, n + 1):
                        w[i][j] = rng.randint(0, 3)
                self.assertEqual(four_point(w, n), has_FG(w, n))

    def test_size_of_numbers(self):
        rng = random.Random(4)
        for t in range(200):
            n = 1 + t % 40
            p, q = H._instance(n, rng, H.FAMILIES[t % len(H.FAMILIES)])
            S = sum(p) + sum(q)
            got = {}

            def local(frame, event, _arg):
                if event == "return" and "c" in frame.f_locals:
                    got["c"] = frame.f_locals["c"]
                return local

            sys.settrace(lambda f, e, a: local if f.f_code is CUB.__code__ else None)
            try:
                CUB((p, q))
            finally:
                sys.settrace(None)
            for row in got["c"]:
                for v in row:
                    if v is not None:
                        self.assertTrue(0 <= v <= n * S)
            if n <= 7:
                self.assertLessEqual(H.brute_force_max(p, q), n * S)

    def test_time_and_space(self):
        cost = next(c for c in REC.__code__.co_consts if hasattr(c, "co_name") and c.co_name == "cost")
        rng = random.Random(5)
        for n in range(10):
            inst = H.generate(n, rng)
            depth, best, lengths = [0], [0], [0]

            def prof(frame, event, _arg):
                if frame.f_code is cost:
                    if event == "call":
                        depth[0] += 1
                        best[0] = max(best[0], depth[0])
                        lengths[0] += frame.f_locals["j"] - frame.f_locals["i"]
                    elif event == "return":
                        depth[0] -= 1

            sys.setprofile(prof)
            try:
                REC(inst)
            finally:
                sys.setprofile(None)
            self.assertEqual(best[0], n + 1)
            self.assertEqual(lengths[0], (3 ** n - 1) // 2)
        for n in range(41):
            for inst in (H._instance(n, rng, "small"), H.instance_of("g_submax", n, rng)):
                for func in (CUB, END):
                    got = {}

                    def local(frame, event, _arg):
                        if event == "return":
                            got.update({k: frame.f_locals[k] for k in ("c", "w") if k in frame.f_locals})
                        return local

                    sys.settrace(lambda f, e, a: local if f.f_code is func.__code__ else None)
                    try:
                        func(inst)
                    finally:
                        sys.settrace(None)
                    self.assertEqual(len(got["c"]), n + 1)
                    self.assertEqual({len(r) for r in got["c"]}, {n + 1})
                    self.assertEqual(len(got["w"]), n + 1)


if __name__ == "__main__":
    unittest.main()
