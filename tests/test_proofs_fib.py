"""Checks of the proofs in pairs/fibonacci-naive-vs-dp/PROOFS.md.

Runs the unchanged implementations with in-memory instrumentation only (profiler and trace hooks). Exact Fibonacci
numbers are computed here with unbounded integers, independently of the three implementations. Deterministic.
"""
import importlib.util
import inspect
import math
import random
import sys
import unittest
from decimal import Decimal, getcontext
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "fibonacci-naive-vs-dp"
MASK = (1 << 64) - 1


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, E / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


NAIVE = _load("implementations/naive.py", "proofs_fib_naive").fib_naive
DP = _load("implementations/dp.py", "proofs_fib_dp").fib_dp
FAST = _load("implementations/fast_doubling.py", "proofs_fib_fast").fib_fast_doubling

FIB = [0, 1]
while len(FIB) < 10 ** 4 + 2:
    FIB.append(FIB[-1] + FIB[-2])


def FIB_BIG(n):
    """Exact F(n) (unbounded integers), n <= 10^4."""
    return FIB[n]


def fib_mod(n):
    """F(n) mod 2^64 by right-to-left powering of [[1, 1], [1, 0]] (a method that none of the implementations uses)."""
    def mul(x, y):
        return ((x[0] * y[0] + x[1] * y[2]) % (1 << 64), (x[0] * y[1] + x[1] * y[3]) % (1 << 64),
                (x[2] * y[0] + x[3] * y[2]) % (1 << 64), (x[2] * y[1] + x[3] * y[3]) % (1 << 64))
    result, base = (1, 0, 0, 1), (1, 1, 1, 0)
    while n:
        if n & 1:
            result = mul(result, base)
        base = mul(base, base)
        n >>= 1
    return result[1]


def line_of(func, needle):
    src, start = inspect.getsourcelines(func)
    return start + next(t for t, s in enumerate(src) if needle in s)


def trace_lines(func, arg, line, watch=()):
    """Run func(arg); return (result, executions of `line`, max over line events of the watched locals)."""
    count, peak = [0], [0]

    def local(frame, event, _arg):
        if event == "line":
            if frame.f_lineno == line:
                count[0] += 1
            for name in watch:
                v = frame.f_locals.get(name)
                if isinstance(v, int):
                    peak[0] = max(peak[0], v)
        return local

    def glob(frame, event, _arg):
        return local if frame.f_code is func.__code__ else None

    sys.settrace(glob)
    try:
        result = func(arg)
    finally:
        sys.settrace(None)
    return result, count[0], peak[0]


class FibonacciProofs(unittest.TestCase):
    def test_naive(self):
        for n in range(23):
            calls, args, depth, best = [0], set(), [0], [0]

            def prof(frame, event, _arg):
                if frame.f_code is NAIVE.__code__:
                    if event == "call":
                        calls[0] += 1
                        args.add(frame.f_locals["n"])
                        depth[0] += 1
                        best[0] = max(best[0], depth[0])
                    elif event == "return":
                        depth[0] -= 1

            sys.setprofile(prof)
            try:
                value = NAIVE(n)
            finally:
                sys.setprofile(None)
            self.assertEqual(value, FIB[n] & MASK)
            self.assertEqual(calls[0], 2 * FIB[n + 1] - 1, n)
            self.assertEqual(best[0], max(n, 1), n)
            self.assertTrue(args <= set(range(n + 1)), n)
            if n != 1:
                self.assertEqual(args, set(range(n + 1)), n)

    def test_phi_bounds(self):
        getcontext().prec = 60
        phi = (1 + Decimal(5).sqrt()) / 2
        for n in range(1, 301):
            self.assertTrue(phi ** (n - 2) <= FIB[n] <= phi ** (n - 1), n)

    def test_dp(self):
        line = line_of(DP, "a, b = b, (a + b) & MASK")
        for n in list(range(301)) + [2000, 10 ** 4]:
            value, count, peak = trace_lines(DP, n, line, ("a", "b"))
            self.assertEqual(count, n)
            self.assertEqual(value, FIB_BIG(n) & MASK)
            self.assertLess(peak, 1 << 64)

    def test_fast_doubling(self):
        line = line_of(FAST, "c = (a * ((2 * b - a) & MASK)) & MASK")
        rng = random.Random(1)
        ns = list(range(1025)) + [2 ** 8, 2 ** 16, 2 ** 32, 2 ** 64, 2 ** 128] + [rng.randrange(2 ** 200) for _ in range(50)]
        for n in ns:
            value, count, _ = trace_lines(FAST, n, line)
            self.assertEqual(count, max(n.bit_length(), 1), n)
            self.assertEqual(value, FIB_BIG(n) & MASK if n <= 10 ** 4 else fib_mod(n), n)
        # every product of two residues stays below 2^129
        a, b = MASK, MASK
        self.assertLess(a * ((2 * b - a) & MASK), 1 << 128)
        self.assertLess(a * a + b * b, 1 << 129)

    def test_bit_length(self):
        lp = math.log2((1 + math.sqrt(5)) / 2)
        for n in range(1, 5001):
            bl = FIB[n].bit_length()
            self.assertTrue((n - 2) * lp < bl <= (n - 1) * lp + 1 + 1e-9, n)

    def test_input_observes_one_operation(self):
        log = []
        ops = ["__add__", "__radd__", "__sub__", "__rsub__", "__mul__", "__rmul__", "__and__", "__rand__",
               "__or__", "__ror__", "__lshift__", "__rshift__", "__lt__", "__le__", "__gt__", "__ge__", "__eq__",
               "__ne__", "__bool__", "__int__", "__float__", "__floordiv__", "__mod__", "__neg__", "__hash__"]

        class Tracer:
            def __init__(self, v):
                self.v = v

            def __index__(self):
                log.append("__index__")
                return self.v

        def make(name):
            def op(self, *args):
                log.append(name)
                other = [a.v if isinstance(a, Tracer) else a for a in args]
                return getattr(int, name)(self.v, *other)
            return op

        for name in ops:
            setattr(Tracer, name, make(name))

        for n in (2 ** 8, 2 ** 16, 2 ** 32, 2 ** 64, 2 ** 128, 12345):
            log.clear()
            self.assertEqual(FAST(Tracer(n)), FAST(n))
            self.assertEqual(log, ["__index__"], n)
        log.clear()
        self.assertEqual(DP(Tracer(1000)), DP(1000))
        self.assertEqual(log, ["__index__"])

        class Sub(int):
            def __index__(self):
                log.append("sub __index__")
                return int(self)

        log.clear()
        self.assertEqual(FAST(Sub(12345)), FAST(12345))
        self.assertEqual(log, [])


if __name__ == "__main__":
    unittest.main()
