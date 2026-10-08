"""Fast tests for pairs/max-heap-orderings-dp-vs-knuth-window-vs-heap-formula (a few seconds).

The three implementations agree with each other and with check(); check() rejects deliberately wrong outputs; the
exact V2 counts equal the closed forms stated in entry.json; the window follows the heap's left subtree size; the
layout formula for L(d) matches the array layout; the hook length formula holds for every tree with N <= 6 nodes.
"""
import importlib.util
import itertools
import math
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "max-heap-orderings-dp-vs-knuth-window-vs-heap-formula"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "test_ho_harness")
DP = _load(ENTRY / "implementations" / "dp.py", "test_ho_dp").min_hook_product_dp
WIN = _load(ENTRY / "implementations" / "knuth_window.py", "test_ho_window").min_hook_product_window
_HEAP = _load(ENTRY / "implementations" / "heap_formula.py", "test_ho_heap")
HEAP, HEAP_LEFT = _HEAP.min_hook_product_heap, _HEAP.heap_left


def _trees(n):
    if n == 0:
        return [()]
    return [(a, b) for t in range(n) for a in _trees(t) for b in _trees(n - 1 - t)]


def _size(T):
    return 0 if T == () else 1 + _size(T[0]) + _size(T[1])


def _hook(T):
    return 1 if T == () else _size(T) * _hook(T[0]) * _hook(T[1])


def _heap_orderings_brute(T):
    parent = []

    def walk(S, p):
        if S != ():
            me = len(parent)
            parent.append(p)
            walk(S[0], me)
            walk(S[1], me)

    walk(T, -1)
    n = len(parent)
    return sum(1 for lab in itertools.permutations(range(n))
               if all(parent[v] < 0 or lab[parent[v]] < lab[v] for v in range(n)))


def _counted(fn, n):
    inst = H.generate_scaling(n, random.Random(n))
    fn(inst)
    return H.counts_by_kind()


class HeapOrderings(unittest.TestCase):
    def test_agree_and_check(self):
        for n in list(range(0, 41)) + [63, 64, 65, 200, 511]:
            inst = H.generate(n, random.Random(n))
            a, b, c = DP(inst), WIN(inst), HEAP(inst)
            self.assertEqual(a, b)
            self.assertEqual(b, c)
            self.assertIs(H.check(inst, a), True)
            self.assertIs(H.check(inst, a + 1), False)
            if a > 1:
                self.assertIs(H.check(inst, a - 1), False)
            self.assertIs(H.check(inst, str(a)), False)

    def test_window_and_heap_large(self):
        for n in (1000, 2047, 2048, 4999):
            inst = (n, 1)
            v = HEAP(inst)
            self.assertEqual(WIN(inst), v)
            self.assertIs(H.check(inst, v), True)

    def test_maximum_heap_orderings(self):
        expected = [1, 1, 2, 3, 8, 20, 80, 210, 896, 3360, 19200, 79200, 506880]
        self.assertEqual([math.factorial(n) // HEAP((n, 1)) for n in range(1, 14)], expected)

    def test_hook_length_formula(self):
        for n in range(0, 7):
            for T in _trees(n):
                self.assertEqual(_heap_orderings_brute(T) * _hook(T), math.factorial(n))

    def test_heap_left_against_layout(self):
        for d in range(1, 3000):
            cnt, start, width = 0, 2, 1
            while start <= d:
                cnt += min(d, start + width - 1) - start + 1
                start, width = 2 * start, 2 * width
            self.assertEqual(HEAP_LEFT(d), cnt)

    def test_window_trajectory_is_heap_left(self):
        h, tau = [1], -1
        for d in range(1, 1500):
            lo, hi = max(tau, 0), min(tau + 1, d - 1)
            best = bt = None
            for t in range(lo, hi + 1):
                v = h[t] * h[d - 1 - t]
                if best is None or v <= best:
                    best, bt = v, t
            h.append(d * best)
            tau = bt
            self.assertEqual(tau, HEAP_LEFT(d))

    def test_closed_form_counts(self):
        for n in range(0, 80):
            c = _counted(DP, n)
            self.assertEqual((c["mul"], c["cmp"]), (n * (n + 3) // 2, n * (n - 1) // 2))
            c = _counted(WIN, n)
            self.assertEqual((c["mul"], c["cmp"]), (3 * n - 1, n - 1) if n else (0, 0))
        for k in range(2, 16):
            c = _counted(HEAP, 2 ** k)
            self.assertEqual((c["mul"], c["cmp"]), (4 * k - 4, 0))
        for n in range(2, 3000):
            c = _counted(HEAP, n)
            self.assertLessEqual(c["mul"], 4 * ((n + 1).bit_length() - 1) - 2)
            self.assertGreaterEqual(c["mul"], 2 * ((n + 1) // 3).bit_length())
        self.assertEqual(H.reported_cost(None), sum(H.counts_by_kind().values()))


if __name__ == "__main__":
    unittest.main()
