"""Checks of the proofs in pairs/optimal-bst-recursion-vs-dp-vs-knuth/PROOFS.md, sections 6-8.

Runs the unchanged implementations with in-memory instrumentation only (profiler and trace hooks that read the
tables at return). The reference tables and the full sets of optimal roots are computed here by a separately
written interval DP. Fixed seeds and stated ranges; deterministic. The exact comparison and addition counts
(sections 1-5) are checked by the scripts named there.
"""
import importlib.util
import inspect
import itertools
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "optimal-bst-recursion-vs-dp-vs-knuth"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, E / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


REC = _load("implementations/recursion.py", "proofs_obst_rec").obst_recursive
CUB = _load("implementations/cubic_dp.py", "proofs_obst_cub").obst_cubic
KNU = _load("implementations/knuth.py", "proofs_obst_knu").obst_knuth
H = _load("harness.py", "proofs_obst_harness")


def weights(p, q):
    n = len(p)
    w = [[0] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        w[i][i] = q[i]
        for j in range(i + 1, n + 1):
            w[i][j] = w[i][j - 1] + p[j - 1] + q[j]
    return w


def reference(p, q):
    """(w, c, opt) with opt[(i, j)] the set of all optimal roots of (i, j)."""
    n = len(p)
    w = weights(p, q)
    c = [[0] * (n + 1) for _ in range(n + 1)]
    opt = {}
    for L in range(1, n + 1):
        for i in range(n - L + 1):
            j = i + L
            cand = {k: c[i][k - 1] + c[k][j] for k in range(i + 1, j + 1)}
            m = min(cand.values())
            c[i][j] = w[i][j] + m
            opt[(i, j)] = {k for k, v in cand.items() if v == m}
    return w, c, opt


def window_run(p, q, rule, rng=None):
    """Knuth's restricted run with an arbitrary tie rule among the minimisers in the range."""
    n = len(p)
    w = weights(p, q)
    c = [[0] * (n + 1) for _ in range(n + 1)]
    r = {}
    for i in range(n):
        c[i][i + 1] = w[i][i + 1]
        r[(i, i + 1)] = i + 1
    for L in range(2, n + 1):
        for i in range(n - L + 1):
            j = i + L
            lo, hi = r[(i, j - 1)], r[(i + 1, j)]
            assert lo <= hi
            cand = {k: c[i][k - 1] + c[k][j] for k in range(lo, hi + 1)}
            m = min(cand.values())
            mins = sorted(k for k, v in cand.items() if v == m)
            if rule == "largest":
                k = mins[-1]
            elif rule == "smallest":
                k = mins[0]
            elif rule == "random":
                k = rng.choice(mins)
            else:  # alternating
                k = mins[-1] if (i + j) % 2 == 0 else mins[0]
            c[i][j] = w[i][j] + m
            r[(i, j)] = k
    return c, r


def tie_heavy(rng, n):
    fam = rng.choice(["bits", "small", "zero", "constant", "gaps_only", "keys_only", "one_heavy", "heavy_ends"])
    return H._instance(n, rng, fam)


def tables_at_return(func, inst, names):
    got = {}

    def local(frame, event, _arg):
        if event == "return":
            got.update({k: frame.f_locals[k] for k in names if k in frame.f_locals})
        return local

    sys.settrace(lambda f, e, a: local if f.f_code is func.__code__ else None)
    try:
        result = func(inst)
    finally:
        sys.settrace(None)
    return result, got


class OptimalBSTProofs(unittest.TestCase):
    def test_cost_and_recurrence(self):
        rng = random.Random(1)
        for t in range(120):
            n = t % 8
            p, q = H._instance(n, rng, H.FAMILIES[t % len(H.FAMILIES)])
            S = sum(p) + sum(q)
            costs = []
            for keys, gaps in H._profiles(n):
                knuth = sum(pm * (lev + 1) for pm, lev in zip(p, keys)) + sum(qj * lev for qj, lev in zip(q, gaps))
                clrs = sum(pm * (lev + 1) for pm, lev in zip(p, keys)) + sum(qj * (lev + 1) for qj, lev in zip(q, gaps))
                self.assertEqual(clrs - knuth, sum(q))
                self.assertLessEqual(knuth, n * S)
                costs.append(knuth)
            best = min(costs)
            self.assertEqual(REC((p, q)), best)
            self.assertEqual(CUB((p, q)), best)
            self.assertEqual(KNU((p, q)), best)
        rng = random.Random(2)
        for n in range(61):
            p, q = H.generate(n, rng)
            S = sum(p) + sum(q)
            _, got = tables_at_return(CUB, (p, q), ("w", "c"))
            for row in got["w"] + got["c"]:
                for v in row:
                    if v is not None:
                        self.assertTrue(0 <= v <= max(n, 1) * S, (n, v))

    def test_weights_quadrangle(self):
        rng = random.Random(3)
        for _ in range(200):
            n = rng.randint(0, 8)
            p = [rng.randint(0, 9) for _ in range(n)]
            q = [rng.randint(0, 9) for _ in range(n + 1)]
            w = weights(p, q)
            for i, i2, j, j2 in itertools.combinations_with_replacement(range(n + 1), 4):
                self.assertEqual(w[i][j] + w[i2][j2], w[i2][j] + w[i][j2])
                self.assertLessEqual(w[i2][j], w[i][j2])

    def _check_qi(self, p, q):
        n = len(p)
        _, c, _ = reference(p, q)
        for i, i2, j, j2 in itertools.combinations_with_replacement(range(n + 1), 4):
            self.assertLessEqual(c[i][j] + c[i2][j2], c[i2][j] + c[i][j2], (p, q, i, i2, j, j2))

    def test_c_quadrangle(self):
        for n, vals in ((0, 3), (1, 3), (2, 3), (3, 3), (4, 2), (5, 2)):
            for t in itertools.product(range(vals), repeat=2 * n + 1):
                self._check_qi(t[:n], t[n:])
        rng = random.Random(4)
        for _ in range(300):
            n = rng.randint(0, 12)
            self._check_qi(*H.generate(n, rng))

    def test_any_tie_rule(self):
        rng = random.Random(5)
        for t in range(400):
            n = 2 + t % 9
            p, q = tie_heavy(rng, n)
            _, c, opt = reference(p, q)
            for rule in ("largest", "smallest", "random", "alternating"):
                c2, r = window_run(p, q, rule, rng)
                for (i, j), k in r.items():
                    self.assertEqual(c2[i][j], c[i][j])
                    self.assertIn(k, opt[(i, j)], (rule, p, q, i, j))
            value, got = tables_at_return(KNU, (p, q), ("c", "r"))
            self.assertEqual(value, c[0][n])
            for (i, j) in opt:
                self.assertEqual(got["c"][i][j], c[i][j])
                self.assertIn(got["r"][i][j], opt[(i, j)])

    def test_monotone_largest_roots(self):
        rng = random.Random(5)
        for t in range(400):
            n = 2 + t % 9
            p, q = tie_heavy(rng, n)
            _, _, opt = reference(p, q)
            K = {iv: max(s) for iv, s in opt.items()}
            for L in range(2, n + 1):
                for i in range(n - L + 1):
                    j = i + L
                    self.assertTrue(K[(i, j - 1)] <= K[(i, j)] <= K[(i + 1, j)], (p, q, i, j))

    def test_mixed_table_not_monotone(self):
        for n in range(3, 13):
            _, _, opt = reference([0] * n, [0] * (n + 1))
            mixed = {(i, j): (max(s) if i % 2 == 0 else min(s)) for (i, j), s in opt.items()}
            self.assertEqual(opt[(0, 3)], {1, 2, 3})
            self.assertGreater(mixed[(0, 3)], mixed[(1, 3)])

    def test_time_and_space(self):
        rec_cost = next(c for c in REC.__code__.co_consts if hasattr(c, "co_name") and c.co_name == "cost")
        rng = random.Random(6)
        for n in range(10):
            p, q = H.generate(n, rng)
            depth, best, lengths = [0], [0], [0]

            def prof(frame, event, _arg):
                if frame.f_code is rec_cost:
                    if event == "call":
                        depth[0] += 1
                        best[0] = max(best[0], depth[0])
                        lengths[0] += frame.f_locals["j"] - frame.f_locals["i"]
                    elif event == "return":
                        depth[0] -= 1

            sys.setprofile(prof)
            try:
                REC((p, q))
            finally:
                sys.setprofile(None)
            self.assertEqual(best[0], n + 1)
            self.assertEqual(lengths[0], (3 ** n - 1) // 2)
        src, start = inspect.getsourcelines(KNU)
        cand_line = start + next(t for t, s in enumerate(src) if "cand = c[i][k - 1] + c[k][j]" in s)
        for n in range(61):
            p, q = H.generate(n, rng)
            for func, names in ((CUB, ("w", "c")), (KNU, ("w", "c", "r"))):
                _, got = tables_at_return(func, (p, q), names)
                for name in names:
                    self.assertEqual(len(got[name]), n + 1)
                    self.assertEqual({len(row) for row in got[name]}, {n + 1})
            count = [0]

            def local(frame, event, _arg):
                if event == "line" and frame.f_lineno == cand_line:
                    count[0] += 1
                return local

            sys.settrace(lambda f, e, a: local if f.f_code is KNU.__code__ else None)
            try:
                KNU((p, q))
            finally:
                sys.settrace(None)
            self.assertTrue(n * (n - 1) // 2 <= count[0] <= max(0, (n - 1) * (3 * n - 2) // 2), (n, count[0]))


if __name__ == "__main__":
    unittest.main()
