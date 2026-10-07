"""Checks of the proofs in pairs/range-minimum-queries-naive-vs-sparse-table/PROOFS.md (sections 3 to 7).

Every test runs the UNCHANGED implementations (or the entry's harness) on fixed inputs and seeds, over the ranges
stated in each test; the table invariant is read from the unchanged function's local variables at its return
(sys.settrace). The idempotent-operation remark concerns a generalisation of the algorithm, which the test writes
out with the operation as a parameter. The written proofs cover the general statements.
"""
import importlib.util
import math
import random
import sys
import tracemalloc
import unittest
from functools import reduce
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "range-minimum-queries-naive-vs-sparse-table"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load(ENTRY / "harness.py", "proofs_rmq_harness")
NAIVE = load(ENTRY / "implementations" / "naive_scan.py", "proofs_rmq_naive").rmq_naive
SPARSE = load(ENTRY / "implementations" / "sparse_table.py", "proofs_rmq_sparse").rmq_sparse_table


def locals_at_return(fn, arg):
    """Run fn(arg) and return (result, a copy of fn's local variables when its own frame returns)."""
    captured = {}

    def tracer(frame, event, _arg):
        if frame.f_code is fn.__code__:
            def local(fr, ev, a):
                if ev == "return":
                    captured.update(fr.f_locals)
                return local
            return local
        return None

    old = sys.gettrace()
    sys.settrace(tracer)
    try:
        out = fn(arg)
    finally:
        sys.settrace(old)
    return out, captured


def peak_bytes(fn, arg):
    tracemalloc.start()
    try:
        base = tracemalloc.get_traced_memory()[0]
        out = fn(arg)
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    del out
    return peak


class CorrectnessTests(unittest.TestCase):
    """PROOFS.md sections 3 and 4: both return min(values[l..r]) for every query; n = 1..60, 100, 257, 1000, with all
    O(n^2) queries for n <= 30 and the harness's mixed queries otherwise, values from [-1000, 1000] and [0, 4]."""

    def test_answers(self):
        for n in list(range(1, 61)) + [100, 257, 1000]:
            for lo, hi in ((-1000, 1000), (0, 4)):
                rng = random.Random(f"rmq-proofs|{n}|{hi}")
                values = tuple(rng.randint(lo, hi) for _ in range(n))
                if n <= 30:
                    queries = tuple((l, r) for l in range(n) for r in range(l, n))
                else:
                    queries = H.generate(n, rng)[1]
                want = tuple(min(values[l:r + 1]) for l, r in queries)
                self.assertEqual(NAIVE((values, queries)), want, n)
                self.assertEqual(SPARSE((values, queries)), want, n)


class TableInvariantTests(unittest.TestCase):
    """PROOFS.md sections 4 and 6: in the unchanged function, at its return, level j of `table` has n - 2^j + 1
    entries for j = 0..floor(log2 n) and entry i is min(values[i .. i + 2^j - 1]); log2[L] = floor(log2 L); the
    table holds (K + 1)(n + 1) - 2^(K+1) + 1 entries, K = floor(log2 n). n = 1..130, 1000, 1025."""

    def test_table(self):
        for n in list(range(1, 131)) + [1000, 1025]:
            rng = random.Random(f"rmq-table|{n}")
            values = tuple(rng.randint(-50, 50) for _ in range(n))
            _, loc = locals_at_return(SPARSE, (values, ((0, n - 1),)))
            table, log2 = loc["table"], loc["log2"]
            K = n.bit_length() - 1
            self.assertEqual(len(table), K + 1, n)
            for j, level in enumerate(table):
                self.assertEqual(len(level), n - (1 << j) + 1, (n, j))
                self.assertEqual(level, [min(values[i:i + (1 << j)]) for i in range(len(level))], (n, j))
            self.assertEqual(log2[1:], [L.bit_length() - 1 for L in range(1, n + 1)], n)
            self.assertEqual(sum(map(len, table)), (K + 1) * (n + 1) - 2 ** (K + 1) + 1, n)


class ScalingFamilyTests(unittest.TestCase):
    """PROOFS.md section 5: every query of the scaling family has length > n/2 (n = 1..400, the V2 seed scheme and
    3 more seeds); for 4 | n the exact expectation of r - l + 1 over the uniform choices of l and r is 3n/4 + 1
    (n = 4, 8, ..., 400, by enumerating all (l, r) pairs)."""

    def test_lengths(self):
        for n in range(1, 401):
            for seed in [f"range-minimum-queries-naive-vs-sparse-table|v2|{n}"] + [f"rmq-fam|{n}|{s}" for s in range(3)]:
                _, queries = H.generate_scaling(n, random.Random(seed))
                self.assertEqual(len(queries), n)
                self.assertTrue(all(0 <= l <= r < n and 2 * (r - l + 1) > n for l, r in queries), n)

    def test_expectation(self):
        from fractions import Fraction
        for n in range(4, 401, 4):
            ls, rs = range(0, n // 4), range(3 * n // 4, n)
            mean = Fraction(sum(r - l + 1 for l in ls for r in rs), len(ls) * len(rs))
            self.assertEqual(mean, Fraction(3 * n, 4) + 1, n)


class IdempotentOperationTests(unittest.TestCase):
    """PROOFS.md section 7: the sparse table with an associative and idempotent operation in place of min (max, gcd,
    bitwise and, bitwise or) answers every range query exactly (n = 1..40, all queries); with + it fails, e.g. on
    [1, 1, 1] and the query (0, 2) (4 instead of 3)."""

    @staticmethod
    def generic(op, values, queries):
        n = len(values)
        table = [list(values)]
        j = 1
        while (1 << j) <= n:
            prev, half = table[-1], 1 << (j - 1)
            table.append([op(prev[i], prev[i + half]) for i in range(n - (1 << j) + 1)])
            j += 1
        out = []
        for l, r in queries:
            k = (r - l + 1).bit_length() - 1
            out.append(op(table[k][l], table[k][r - (1 << k) + 1]))
        return out

    def test_operations(self):
        ops = (max, math.gcd, lambda x, y: x & y, lambda x, y: x | y)
        for n in range(1, 41):
            rng = random.Random(f"rmq-idem|{n}")
            values = [rng.randint(0, 255) for _ in range(n)]
            queries = [(l, r) for l in range(n) for r in range(l, n)]
            for op in ops:
                want = [reduce(op, values[l:r + 1]) for l, r in queries]
                self.assertEqual(self.generic(op, values, queries), want, n)

    def test_sum_fails(self):
        self.assertEqual(self.generic(lambda x, y: x + y, [1, 1, 1], [(0, 2)]), [4])


class SpaceTests(unittest.TestCase):
    """PROOFS.md section 6. Scan: the peak traced allocation is at most 24 q + 4096 bytes (the output list and its
    tuple copy, 8 bytes per query each, plus O(1)), n = 1000..16000 doubling. Sparse table: peak / (n log2 n) is at
    least 8, at most 200 and varies by a factor of at most 1.5 over n = 2000..32000 doubling (n alone would let it
    fall by a factor of 1.36 at most, so the written proof, not this check, excludes Theta(n); n^2 would vary by 16)."""

    def test_scan(self):
        for n in (1000, 2000, 4000, 8000, 16000):
            inst = H.generate(n, random.Random(f"rmq-space|{n}"))
            self.assertLessEqual(peak_bytes(NAIVE, inst), 24 * n + 4096, n)

    def test_sparse(self):
        per = []
        for n in (2000, 4000, 8000, 16000, 32000):
            inst = H.generate(n, random.Random(f"rmq-space|{n}"))
            per.append(peak_bytes(SPARSE, inst) / (n * math.log2(n)))
        self.assertGreaterEqual(min(per), 8)
        self.assertLessEqual(max(per), 200)
        self.assertLessEqual(max(per) / min(per), 1.5, per)


if __name__ == "__main__":
    unittest.main()
