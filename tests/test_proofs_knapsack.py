"""Checks of the proofs in pairs/knapsack-01-brute-vs-dp/PROOFS.md.

Runs the unchanged implementations with in-memory instrumentation only (trace hooks, an instrumented number type
wrapped around the weights, and a counting wrapper around the module's bisect_right). Fixed seeds; deterministic.
"""
import importlib.util
import inspect
import random
import sys
import unittest
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "knapsack-01-brute-vs-dp"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, E / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BRUTE = _load("implementations/brute_force.py", "proofs_ks_brute").knapsack_brute
MITM_MOD = _load("implementations/meet_in_the_middle.py", "proofs_ks_mitm")
MITM = MITM_MOD.knapsack_mitm
DP = _load("implementations/dp.py", "proofs_ks_dp").knapsack_dp
HARNESS = _load("harness.py", "proofs_ks_harness")


def oracle(weights, values, cap):
    """Independent: include/exclude recursion over the items."""
    def rec(i, room):
        if i == len(weights):
            return 0
        best = rec(i + 1, room)
        if weights[i] <= room:
            best = max(best, values[i] + rec(i + 1, room - weights[i]))
        return best
    return rec(0, cap)


def line_of(func, needle):
    src, start = inspect.getsourcelines(func)
    return start + next(t for t, s in enumerate(src) if needle in s)


def count_line(func, arg, line, types=None):
    count, kinds = [0], set()

    def local(frame, event, _arg):
        if event == "line":
            if frame.f_lineno == line:
                count[0] += 1
            if types is not None:
                for name, v in frame.f_locals.items():
                    if name not in ("instance", "weights", "values"):
                        kinds.add(type(v).__name__)
        return local

    sys.settrace(lambda f, e, a: local if f.f_code is func.__code__ else None)
    try:
        result = func(arg)
    finally:
        sys.settrace(None)
    return result, count[0], kinds


def random_instance(rng, n, cap=None):
    w = tuple(rng.randint(1, 20) for _ in range(n))
    v = tuple(rng.randint(1, 30) for _ in range(n))
    return w, v, rng.randint(0, sum(w)) if cap is None else cap


class Counter:
    lt = 0


class CInt:
    """Integer that counts its '<' evaluations (either operand position)."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _o(o):
        return o.v if isinstance(o, CInt) else o

    def __add__(self, o):
        return CInt(self.v + self._o(o))

    __radd__ = __add__

    def __sub__(self, o):
        return CInt(self.v - self._o(o))

    def __rsub__(self, o):
        return CInt(self._o(o) - self.v)

    def __lt__(self, o):
        Counter.lt += 1
        return self.v < self._o(o)

    def __gt__(self, o):
        Counter.lt += 1
        return self.v > self._o(o)

    def __le__(self, o):
        return self.v <= self._o(o)

    def __ge__(self, o):
        return self.v >= self._o(o)

    def __eq__(self, o):
        return self.v == self._o(o)

    def __hash__(self):
        return hash(self.v)


class KnapsackProofs(unittest.TestCase):
    def test_enumeration(self):
        line = line_of(BRUTE, "if mask >> i & 1:")
        rng = random.Random(1)
        for n in range(13):
            inst = random_instance(rng, n)
            _, count, kinds = count_line(BRUTE, inst, line, types=True)
            self.assertEqual(count, n * 2 ** n)
            self.assertTrue(kinds <= {"int"}, kinds)
        for _ in range(300):
            inst = random_instance(rng, rng.randint(0, 12))
            self.assertEqual(BRUTE(inst), oracle(*inst))

    def test_mitm(self):
        rng = random.Random(2)
        for _ in range(300):
            inst = random_instance(rng, rng.randint(0, 14))
            self.assertEqual(MITM(inst), BRUTE(inst))
        rng = random.Random(3)
        original = MITM_MOD.bisect_right
        inside = [0]

        def counting_bisect(a, x):
            before = Counter.lt
            r = original(a, x)
            inside[0] += Counter.lt - before
            return r

        sizes = {}

        def tracer(frame, event, _arg):
            if event == "return" and frame.f_code is MITM.__code__:
                loc = frame.f_locals
                sizes.update({k: len(loc[k]) for k in ("left", "right", "right_weights", "best_value_up_to")})
            return tracer if frame.f_code is MITM.__code__ else None

        for n in range(2, 21):
            w = [rng.randint(1, 20) for _ in range(n)]
            v = tuple(rng.randint(1, 30) for _ in range(n))
            inst = (tuple(CInt(x) for x in w), v, sum(w))
            h, m = n // 2, 2 ** (n - n // 2)
            inside[0] = 0
            Counter.lt = 0
            MITM_MOD.bisect_right = counting_bisect
            sys.settrace(tracer)
            try:
                MITM(inst)
            finally:
                sys.settrace(None)
                MITM_MOD.bisect_right = original
            k = n - h
            self.assertTrue(2 ** h * k <= inside[0] <= 2 ** h * (k + 1), (n, inside[0]))
            self.assertEqual(sizes, {"left": 2 ** h, "right": m, "right_weights": m, "best_value_up_to": m})
            # the sort: '<' evaluations outside bisect_right (sorting and the 'w <= capacity' tests use other ops)
            self.assertLessEqual(Counter.lt - inside[0], m * k, n)

    def test_dp(self):
        line = line_of(DP, "if best[c - w] + v > best[c]:")
        rng = random.Random(4)
        for _ in range(300):
            n = rng.randint(0, 12)
            w = tuple(rng.randint(1, 20) for _ in range(n))
            v = tuple(rng.randint(1, 30) for _ in range(n))
            cap = rng.randint(0, sum(w) + 5)
            result, count, _ = count_line(DP, (w, v, cap), line)
            self.assertEqual(count, sum(max(0, cap - x + 1) for x in w))
            self.assertEqual(result, BRUTE((w, v, cap)))
        rng = random.Random(5)
        for _ in range(200):
            n = rng.randint(1, 10)
            w = [rng.randint(1, 20) for _ in range(n)]
            W = rng.randint(max(w), 500)
            I = lambda c: sum(max(0, c - x + 1) for x in w)
            S = sum(w)
            self.assertEqual(Fraction(I(2 * W), I(W)), 2 + Fraction(S - n, n * W + n - S))
            self.assertTrue(2 <= Fraction(I(2 * W), I(W)) <= 2 + Fraction(max(w) - 1, W + 1 - max(w)))
        rng = random.Random(6)
        for n in range(40, 401, 20):
            w, v, cap = HARNESS.generate(n, rng)
            _, count, _ = count_line(DP, (w, v, cap), line)
            self.assertTrue((n - 2) * (n // 2) <= count <= n * (10 * n + 1), n)
        sizes = []

        def local(frame, event, _arg):
            if event == "return":
                sizes.append(len(frame.f_locals["best"]))
            return local

        sys.settrace(lambda f, e, a: local if f.f_code is DP.__code__ else None)
        try:
            DP(((3, 4), (1, 2), 17))
        finally:
            sys.settrace(None)
        self.assertEqual(sizes, [18])


if __name__ == "__main__":
    unittest.main()
