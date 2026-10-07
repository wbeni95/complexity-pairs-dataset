"""Deterministic checks for pairs/linear-ordering-enumeration-vs-subset-dp/PROOFS.md, sections 3-9 (a few seconds;
the exact counts of sections 1-2 are checked by the scripts named there).

Ranges: problem-statement equivalences, n <= 6 (3); both algorithms against brute force over all orders, n <= 7
(4, 5); the running-row-sum variant, n <= 12 (7); the uncounted loop tests by line-execution counts, n <= 10 (8);
the oracle facts, n <= 8 (9); tracemalloc peaks (6).
"""
import importlib.util
import itertools
import random
import sys
import tracemalloc
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "linear-ordering-enumeration-vs-subset-dp"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "proofs_lop_harness")
EN = _load(ENTRY / "implementations" / "enumeration.py", "proofs_lop_enum").linear_ordering_enumeration
DP_MOD = _load(ENTRY / "implementations" / "subset_dp.py", "proofs_lop_dp")
DP = DP_MOD.linear_ordering_subset_dp


def forward(w, order):
    n = len(w)
    return sum(w[order[p]][order[q]] for p in range(n) for q in range(p + 1, n))


def brute_max(w):
    return max(forward(w, o) for o in itertools.permutations(range(len(w))))


def row_sum_variant(w):
    """The variant of PROOFS.md section 7: out[v][U] = sum of W[v][u] over u in U, u != v, tabulated for all U;
    then the DP reads each gain in O(1). Returns (optimum, number of additions, number of table entries)."""
    n = len(w)
    size = 1 << n
    adds = 0
    out = [[0] * size for _ in range(n)]
    for v in range(n):
        row = out[v]
        for U in range(1, size):
            low = U & -U
            u0 = low.bit_length() - 1
            if u0 != v:
                row[U] = row[U ^ low] + w[v][u0]
                adds += 1
            else:
                row[U] = row[U ^ low]
    full = size - 1
    best = [None] * size
    best[0] = 0
    for s in range(size):
        for v in range(n):
            if s >> v & 1:
                continue
            t = s | (1 << v)
            value = best[s] + out[v][full ^ t]
            adds += 1
            if best[t] is None or value > best[t]:
                best[t] = value
    return best[full], adds, n * size


class ProblemStatement(unittest.TestCase):
    def test_backward_is_constant_minus_forward(self):
        for n in range(0, 7):
            w = H.generate(n, random.Random(f"proofs-lop-bf|{n}"))
            const = sum(w[a][b] for a in range(n) for b in range(n) if a != b)
            for o in itertools.permutations(range(n)):
                back = sum(w[o[q]][o[p]] for p in range(n) for q in range(p + 1, n))
                self.assertEqual(back + forward(w, o), const)

    def test_zero_one_matrix_is_feedback_arc_set(self):
        for n in range(1, 7):
            for t in range(4):
                rng = random.Random(f"proofs-lop-fas|{n}|{t}")
                arcs = [(a, b) for a in range(n) for b in range(n) if a != b and rng.random() < 0.4]
                w = tuple(tuple(1 if (a, b) in arcs else rng.randint(0, 1) * (a == b) for b in range(n)) for a in range(n))
                min_back = len(arcs) - DP(w)[0]
                fas = None
                for size in range(len(arcs) + 1):
                    for F in itertools.combinations(arcs, size):
                        rest = [x for x in arcs if x not in F]
                        if any(all(o.index(a) < o.index(b) for a, b in rest) for o in itertools.permutations(range(n))):
                            fas = size
                            break
                    if fas is not None:
                        break
                self.assertEqual(min_back, fas)


class Correctness(unittest.TestCase):
    def test_against_all_orders(self):
        for n in range(0, 8):
            for t in range(5):
                w = H.generate(n, random.Random(f"proofs-lop|{n}|{t}"))
                opt = brute_max(w)
                for fn in (EN, DP):
                    value, order = fn(w)
                    self.assertEqual(value, opt)
                    self.assertEqual(H.order_value(w, order), opt)


class RowSumVariant(unittest.TestCase):
    def test_variant_equals_dp_and_costs_theta_n_2n(self):
        for n in range(0, 13):
            w = H.generate(n, random.Random(f"proofs-lop-var|{n}"))
            opt, adds, cells = row_sum_variant(w)
            self.assertEqual(opt, DP(w)[0])
            self.assertEqual(cells, n * 2 ** n)
            self.assertEqual(adds, (n - 1) * (2 ** n - 1) + n * 2 ** (n - 1) if n else 0)


class UncountedWork(unittest.TestCase):
    def test_inner_loop_tests_are_same_order(self):
        lines = Path(DP_MOD.__file__).read_text(encoding="utf-8").splitlines()
        target = [i + 1 for i, l in enumerate(lines) if l.strip() == "if u != v and not (t >> u) & 1:"]
        self.assertEqual(len(target), 1)
        counts = [0]
        code = DP.__code__

        def local(frame, event, arg):
            if event == "line" and frame.f_lineno == target[0]:
                counts[0] += 1
            return local

        for n in range(1, 11):
            w = H.generate(n, random.Random(f"proofs-lop-unc|{n}"))
            counts[0] = 0
            sys.settrace(lambda f, e, a: local if f.f_code is code else None)
            try:
                DP(w)
            finally:
                sys.settrace(None)
            self.assertEqual(counts[0], n * n * 2 ** (n - 1))
            counted = 2 ** (n - 2) * (n + 4) * (n - 1) + 1 if n >= 2 else 0
            if n >= 2:
                self.assertTrue(1 <= counts[0] / counted <= 4, n)
        # PROOFS.md section 8: the two inequalities for n = 2..200; n = 1 is the exception (counted total 0,
        # 2n^2 + 12n - 16 = -2).
        for n in range(2, 201):
            self.assertGreaterEqual(2 ** (n - 2) * (n * n - 3 * n + 4), 1)
            self.assertGreaterEqual(2 * n * n + 12 * n - 16, 0)
        self.assertEqual(2 * 1 + 12 * 1 - 16, -2)
        H_counter = H.CountingInt
        w = tuple(tuple(H_counter(x) for x in row) for row in H.generate(1, random.Random(1)))
        H.reset_counter()
        DP(w)
        self.assertEqual(sum(H.counts_by_kind().values()), 0)


class Oracle(unittest.TestCase):
    def test_upper_bound_and_branch_and_bound(self):
        for n in range(0, 9):
            for t in range(4):
                w = H.generate(n, random.Random(f"proofs-lop-oracle|{n}|{t}"))
                opt = DP(w)[0]
                self.assertGreaterEqual(H.upper_bound(w), opt)
                self.assertEqual(H.branch_and_bound(w), opt)


class WorkingMemory(unittest.TestCase):
    @staticmethod
    def _peak(fn, arg):
        tracemalloc.start()
        tracemalloc.reset_peak()
        base = tracemalloc.get_traced_memory()[0]
        fn(arg)
        peak = tracemalloc.get_traced_memory()[1] - base
        tracemalloc.stop()
        return peak

    def test_peaks(self):
        for n in range(8, 16):
            w = H.generate(n, random.Random(f"proofs-lop-mem|{n}"))
            per = self._peak(DP, w) / 2 ** n
            self.assertTrue(16 <= per <= 160, (n, per))            # best and last: two 2^n tables
        for n in range(2, 9):
            w = H.generate(n, random.Random(f"proofs-lop-mem|{n}"))
            self.assertLessEqual(self._peak(EN, w), 4096 + 64 * n)  # no growth with n!


if __name__ == "__main__":
    unittest.main()
