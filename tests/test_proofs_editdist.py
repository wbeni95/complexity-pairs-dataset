"""Checks of the proofs in pairs/edit-distance-brute-vs-dp/PROOFS.md.

Runs the unchanged implementations with in-memory instrumentation only (a profiler hook counts calls and depth, a
trace hook counts line executions and list lengths). Fixed seeds and stated ranges; deterministic.
"""
import importlib.util
import itertools
import math
import random
import sys
import unittest
from collections import deque
from decimal import Decimal, getcontext
from math import comb
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "edit-distance-brute-vs-dp"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, E / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BRUTE = _load("implementations/brute_force.py", "proofs_ed_brute").edit_distance_brute
DP = _load("implementations/wagner_fischer.py", "proofs_ed_dp").edit_distance_dp


def delannoy(u, v):
    return sum(comb(u, k) * comb(v, k) * 2 ** k for k in range(min(u, v) + 1))


def bfs_edit_distance(src, alphabet, radius):
    """Distances from src to every string within `radius` single operations (independent of both implementations)."""
    dist = {src: 0}
    queue = deque([src])
    while queue:
        z = queue.popleft()
        d = dist[z]
        if d == radius:
            continue
        nbrs = set()
        for p in range(len(z)):
            nbrs.add(z[:p] + z[p + 1:])
            for c in alphabet:
                nbrs.add(z[:p] + c + z[p + 1:])
        for p in range(len(z) + 1):
            for c in alphabet:
                nbrs.add(z[:p] + c + z[p:])
        for y in nbrs:
            if y not in dist:
                dist[y] = d + 1
                queue.append(y)
    return dist


def profile_calls(func, arg, code):
    """Run func(arg); return (result, list of (i, j) of every call of `code`, maximal nesting depth of `code`)."""
    calls, depth, best = [], [0], [0]

    def prof(frame, event, _arg):
        if frame.f_code is code:
            if event == "call":
                calls.append((frame.f_locals["i"], frame.f_locals["j"]))
                depth[0] += 1
                best[0] = max(best[0], depth[0])
            elif event == "return":
                depth[0] -= 1

    sys.setprofile(prof)
    try:
        result = func(arg)
    finally:
        sys.setprofile(None)
    return result, calls, best[0]


def inner_code(func, name):
    return next(c for c in func.__code__.co_consts if hasattr(c, "co_name") and c.co_name == name)


class EditDistanceProofs(unittest.TestCase):
    def test_correct_against_edit_script_search(self):
        alphabet = "ACGT"
        small = ["".join(t) for L in range(4) for t in itertools.product("ACG", repeat=L)]
        for x in small:
            dist = bfs_edit_distance(x, alphabet, 3)
            for y in small:
                want = dist[y]  # every pair here is within 3 operations (|x|, |y| <= 3)
                self.assertEqual(BRUTE((x, y)), want, (x, y))
                self.assertEqual(DP((x, y)), want, (x, y))
        rng = random.Random(1)
        for _ in range(60):
            x = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 4)))
            y = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 4)))
            want = bfs_edit_distance(x, alphabet, max(len(x), len(y)))[y]
            self.assertEqual(BRUTE((x, y)), want, (x, y))
            self.assertEqual(DP((x, y)), want, (x, y))

    def test_dp_unequal_lengths(self):
        rng = random.Random(2)
        for _ in range(300):
            x = "".join(rng.choice("ACGT") for _ in range(rng.randint(0, 7)))
            y = "".join(rng.choice("ACGT") for _ in range(rng.randint(0, 7)))
            self.assertEqual(BRUTE((x, y)), DP((x, y)), (x, y))

    def test_shortcut_variant(self):
        def shortcut(a, b):
            calls = [0]

            def d(i, j):
                calls[0] += 1
                if i == len(a):
                    return len(b) - j
                if j == len(b):
                    return len(a) - i
                if a[i] == b[j]:
                    return d(i + 1, j + 1)
                return min(d(i + 1, j) + 1, d(i, j + 1) + 1, d(i + 1, j + 1) + 1)

            return d(0, 0), calls[0]

        rng = random.Random(3)
        for _ in range(400):
            x = "".join(rng.choice("ACGT") for _ in range(rng.randint(0, 8)))
            y = "".join(rng.choice("ACGT") for _ in range(rng.randint(0, 8)))
            self.assertEqual(shortcut(x, y)[0], DP((x, y)), (x, y))
        for n in range(9):
            x = "".join(rng.choice("AC") for _ in range(n))
            self.assertEqual(shortcut(x, x), (0, n + 1))
            y = "".join(rng.choice("GT") for _ in range(n))
            self.assertEqual(shortcut(x, y)[1], (3 * delannoy(n, n) - 1) // 2)

    def test_recursion_calls_leaves_depth(self):
        code = inner_code(BRUTE, "d")
        rng = random.Random(4)
        for n in range(9):
            for _ in range(2):
                x = "".join(rng.choice("ACGT") for _ in range(n))
                y = "".join(rng.choice("ACGT") for _ in range(n))
                result, calls, depth = profile_calls(BRUTE, (x, y), code)
                self.assertEqual(result, DP((x, y)))
                dnn = delannoy(n, n)
                self.assertEqual(len(calls), (3 * dnn - 1) // 2, n)
                self.assertEqual(sum(1 for i, j in calls if i == n or j == n), dnn, n)
                self.assertEqual(depth, 2 * n if n else 1, n)
                self.assertEqual(set(calls), set(itertools.product(range(n + 1), repeat=2)), n)
                self.assertGreaterEqual(dnn, 2 ** n)

    def test_delannoy_closed_form(self):
        D = [[1] * 31 for _ in range(31)]
        for u in range(1, 31):
            for v in range(1, 31):
                D[u][v] = D[u - 1][v] + D[u][v - 1] + D[u - 1][v - 1]
        for u in range(31):
            for v in range(31):
                self.assertEqual(D[u][v], delannoy(u, v))

    def test_asymptotic_bounds(self):
        getcontext().prec = 60
        lam = Decimal(3) + 2 * Decimal(2).sqrt()
        for n in list(range(1, 401)) + [1000, 2000]:
            r = Decimal(delannoy(n, n)) * Decimal(n).sqrt() / lam ** n
            self.assertTrue(Decimal("3e-4") <= r <= 6, n)
            if n <= 15:
                self.assertTrue(Decimal("0.514") <= r <= Decimal("0.569"), (n, r))
            if n <= 8:
                self.assertLess(r, Decimal("0.57"))
        xs = 2 - math.sqrt(2)
        for n in range(1, 301):
            a = [comb(n, k) ** 2 * 2 ** k for k in range(n + 1)]
            km = math.ceil(xs * n - (math.sqrt(2) - 1))
            self.assertEqual(max(range(n + 1), key=lambda k: (a[k], -k)), km, n)
            self.assertLessEqual(abs(km - xs * n), 1)
        lnlam = math.log(3 + 2 * math.sqrt(2))

        def f(x):
            return 2 * (-x * math.log(x) - (1 - x) * math.log(1 - x)) + x * math.log(2)

        self.assertAlmostEqual(f(xs), lnlam, places=12)
        for n in range(16, 201):
            for k in range(1, n):
                x = k / n
                stirling = math.log(n / (2 * math.pi * k * (n - k))) + n * f(x)
                log_theta = math.log(comb(n, k) ** 2 * 2 ** k) - stirling
                self.assertTrue(-1 / 3 < log_theta < 1 / 6, (n, k))
                self.assertLessEqual(f(x), lnlam - 4 * (x - xs) ** 2 + 1e-12)
                if abs(x - xs) <= 0.25:
                    self.assertGreaterEqual(f(x), lnlam - 7.29 * (x - xs) ** 2 - 1e-12)

    def test_stirling_steps(self):
        getcontext().prec = 50

        def lnfact_step(m):  # d_m - d_(m+1) = (m + 1/2) ln(1 + 1/m) - 1
            m = Decimal(m)
            return (m + Decimal("0.5")) * (1 + 1 / m).ln() - 1

        for m in range(1, 3001):
            step = lnfact_step(m)
            lo = Decimal(1) / (12 * m + 1) - Decimal(1) / (12 * m + 13)
            hi = Decimal(1) / (12 * m) - Decimal(1) / (12 * m + 12)
            self.assertTrue(lo < step < hi, m)
        e = Decimal(1).exp()
        up = e ** (Decimal(1) / 6) * e ** (Decimal(-11) / 6)
        self.assertLess(Decimal("9.1") * up, Decimal("1.719"))
        self.assertLess(2 * up, Decimal("0.3778"))
        self.assertLess(Decimal("1.719") * (2 + Decimal(math.pi).sqrt() / 2), Decimal("4.97"))
        self.assertLess(Decimal("0.3778") * Decimal(6) ** Decimal("1.5") * e ** Decimal("-1.5"), Decimal("1.24"))
        self.assertGreaterEqual(-(Decimal(24) / 13 + Decimal(1) / 3 + Decimal("7.29")), Decimal("-9.4695"))
        self.assertGreater(4 * e ** Decimal("-9.4695"), Decimal("3.08e-4"))
        # the n >= 9 chain: first term < 0.01, second < 1.719 (2/3 + 0.887) < 2.68, third < 1.24, total < 6
        lam = Decimal(3) + 2 * Decimal(2).sqrt()
        self.assertLess(2 * Decimal(2) ** 9 * Decimal(9).sqrt() / lam ** 9, Decimal("0.01"))
        self.assertLessEqual(Decimal(math.pi).sqrt() / 2, Decimal("0.887"))
        self.assertLess(Decimal("1.719") * (Decimal(2) / 3 + Decimal("0.887")), Decimal("2.68"))
        # each term is strictly below its bound, so the total is strictly below their sum 3.93 < 6
        self.assertLessEqual(Decimal("0.01") + Decimal("2.68") + Decimal("1.24"), Decimal("3.93"))
        self.assertLess(Decimal("3.93"), 6)
        self.assertLessEqual(Decimal("0.69") + Decimal("4.97") + Decimal("1.24"), Decimal("6.9"))  # strict terms
        c = (2 * Decimal(math.pi)).sqrt().ln()
        self.assertTrue(Decimal(11) / 12 < c < Decimal(12) / 13)

    def test_dp_iterations_and_rows(self):
        import inspect
        src, start = inspect.getsourcelines(DP)
        body = start + next(t for t, s in enumerate(src) if "cur[j] = min(" in s)
        rng = random.Random(5)
        cases = [(la, lb) for la in range(13) for lb in range(13)] + [(50, 50), (100, 100)]
        for la, lb in cases:
            x = "".join(rng.choice("ACGT") for _ in range(la))
            y = "".join(rng.choice("ACGT") for _ in range(lb))
            count, peak = [0], [0]

            def local(frame, event, _arg):
                if event == "line":
                    if frame.f_lineno == body:
                        count[0] += 1
                    loc = frame.f_locals
                    peak[0] = max(peak[0], len(loc.get("prev", ())) + len(loc.get("cur", ())))
                return local

            def glob(frame, event, _arg):
                return local if frame.f_code is DP.__code__ else None

            sys.settrace(glob)
            try:
                result = DP((x, y))
            finally:
                sys.settrace(None)
            self.assertEqual(count[0], la * lb, (la, lb))
            self.assertEqual(peak[0], 2 * (lb + 1) if la else lb + 1, (la, lb))
            if la <= 7 and lb <= 7:
                self.assertEqual(result, BRUTE((x, y)))


if __name__ == "__main__":
    unittest.main()
