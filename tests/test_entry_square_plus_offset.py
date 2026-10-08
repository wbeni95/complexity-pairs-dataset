"""Fast tests for pairs/square-plus-offset-count-enumeration-vs-intervals-vs-groups (about a second).

The three implementations agree with each other and with the independent check of the harness; check rejects wrong
outputs; the exact work counts equal the closed forms stated in entry.json; Lemma A holds against a brute force over
all roots; the structural facts used by the group algorithm hold (at most two roots reach above 2^n - 1, the number
of groups, the Newton step bound); the word sizes of PROOFS.md section 8 hold for every integer value of every
expression of the three implementations (instrumented copies). The proofs are in the entry's PROOFS.md; the longer
runs are in experiments/2026-10-07_square_plus_offset_checks.py.
"""
import ast
import importlib.util
import math
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "square-plus-offset-count-enumeration-vs-intervals-vs-groups"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "test_spo_harness")
A1 = _load(ENTRY / "implementations" / "enumeration.py", "test_spo_a1")
A2 = _load(ENTRY / "implementations" / "interval_sweep.py", "test_spo_a2").count_by_interval_sweep
G = _load(ENTRY / "implementations" / "groups.py", "test_spo_a3")


def f(k, x):
    return A1.representation_cost(k, x)


class _Instrument(ast.NodeTransformer):
    """Wrap every expression that can carry an integer in _rec_(...), which records it and returns it unchanged."""

    @staticmethod
    def _wrap(node):
        return ast.Call(func=ast.Name(id="_rec_", ctx=ast.Load()), args=[node], keywords=[])

    def visit_Name(self, node):
        return self._wrap(node) if isinstance(node.ctx, ast.Load) else node

    def visit_Constant(self, node):
        return self._wrap(node) if type(node.value) is int else node

    def _wrap_after_children(self, node):
        self.generic_visit(node)
        return self._wrap(node)

    visit_BinOp = visit_UnaryOp = visit_Call = _wrap_after_children

    def visit_Subscript(self, node):
        self.generic_visit(node)
        return self._wrap(node) if isinstance(node.ctx, ast.Load) else node

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        if isinstance(node.target, ast.Name):
            return [node, ast.Expr(self._wrap(ast.Name(id=node.target.id, ctx=ast.Load())))]
        return node


def _traced(path):
    box = [0]

    def _rec_(value):
        if type(value) is int:
            box[0] = max(box[0], abs(value))
        return value

    tree = _Instrument().visit(ast.parse(path.read_text(encoding="utf-8")))
    ast.fix_missing_locations(tree)
    ns = {"_rec_": _rec_, "__name__": "traced_" + path.stem}
    exec(compile(tree, str(path), "exec"), ns)
    return ns, box


class SquarePlusOffset(unittest.TestCase):
    def test_agree_and_check(self):
        for n in range(0, 15):
            outs = [A1.count_by_enumeration(n), A2(n), G.count_by_groups(n)]
            self.assertEqual(len({o[0] for o in outs}), 1, n)
            for o in outs:
                self.assertIs(H.check(n, o), True)
        for n in range(15, 31):
            b, c = A2(n), G.count_by_groups(n)
            self.assertEqual(b[0], c[0])
            self.assertIs(H.check(n, c), True)
        self.assertIsNone(H.check(64, G.count_by_groups(64)))

    def test_check_rejects_wrong_outputs(self):
        for n in (6, 9, 13, 20):
            cnt, work = G.count_by_groups(n)
            self.assertIs(H.check(n, (cnt + 1, work)), False)
            self.assertIs(H.check(n, (cnt - 1, work)), False)
            self.assertIs(H.check(n, cnt), False)
            self.assertIs(H.check(n, (float(cnt), work)), False)
            self.assertIs(H.check(n, (True, work)), False)

    def test_known_values(self):
        known = {5: 0, 6: 3, 7: 8, 10: 127, 13: 1104, 15: 4578, 26: 10216064, 29: 77512574, 39: 79393042353}
        for n, val in known.items():
            self.assertEqual(G.count_by_groups(n)[0], val, n)

    def test_exact_work_counts(self):
        for n in range(0, 15):
            self.assertEqual(A1.count_by_enumeration(n)[1], 3 * 2 ** n)
        for n in range(1, 31):
            self.assertEqual(A2(n)[1], math.isqrt(2 ** n - 1) + 2)
        for n in range(0, 31, 2):
            self.assertEqual(A2(n)[1], 2 ** (n // 2) + 1)
        for n in range(11, 301):
            self.assertEqual(G.count_by_groups(n)[1], n // 2 + 1)
        for n in range(11, 301):
            st = {}
            G.count_groups(n, st)
            self.assertEqual(st["isqrt_calls"], n + 2)

    def test_lemma_a_against_all_roots(self):
        for k in range(1 << 12):
            top = math.isqrt(k + (1 << A1.bit_length(k)) - 1)       # Lemma 0 window
            best = min(f(k, x) for x in range(top + 1))
            r = math.isqrt(k)
            self.assertEqual(best, min(f(k, 0), f(k, r), f(k, r + 1)), k)

    def test_examples(self):
        # k = 80: X = 7 is cheaper than X = r = 8, and the minimum is at r + 1 = 9
        self.assertEqual([f(80, x) for x in (0, 7, 8, 9)], [8, 8, 9, 6])
        # the two boundary cases of case (iii) (X = 1, k = 2^(2q+1), q = 1, 2)
        self.assertLessEqual(min(f(8, 2), f(8, 3)), f(8, 1))
        self.assertLessEqual(min(f(32, 5), f(32, 6)), f(32, 1))
        self.assertEqual(math.isqrt(8), 2)                          # r = 2^q at q = 1

    def test_group_structure(self):
        for n in range(5, 301):
            st = {}
            G.count_groups(n, st)
            self.assertLessEqual(st["above_range_roots"], 2, n)     # Lemma E(c)
            if n >= 6:                                              # word size of Theorem A3 (incl. Newton values)
                self.assertLessEqual(st["max_value_bits"], n + 2, n)

    def test_word_sizes_traced(self):
        # PROOFS.md section 8: for n >= 1 every integer value is below 2^(n+2) in absolute value; at n = 0 at most 5
        impl = ENTRY / "implementations"
        for fname, func, nmax in (("enumeration.py", "count_by_enumeration", 10),
                                  ("interval_sweep.py", "count_by_interval_sweep", 20),
                                  ("groups.py", "count_by_groups", 120)):
            ns, box = _traced(impl / fname)
            for n in range(0, nmax + 1):
                box[0] = 0
                ns[func](n)
                if n == 0:
                    self.assertLessEqual(box[0], 5, fname)
                else:
                    self.assertLess(box[0], 1 << (n + 2), (fname, n))
                    self.assertGreaterEqual(box[0], 1 << n, (fname, n))    # control: 2^n itself is formed

    def test_above_range_direct(self):
        # Lemma E(c) by a direct count that does not use groups.py: at most two roots X <= T reach 2^n. Inside a
        # group X^2 + s increases with X, so the roots that reach 2^n form a suffix of the group; scanning the last
        # four roots of every group therefore finds three of them whenever a group has three or more.
        for n in range(6, 301):
            v, T, cnt, l = n - 4, math.isqrt((1 << n) - 1) + 1, 0, 1
            while (0 if l == 1 else 1 << (l - 1)) <= T and v - l >= 1:
                a, b, s = (0 if l == 1 else 1 << (l - 1)), min((1 << l) - 1, T), (1 << (v - l)) - 1
                cnt += sum(1 for x in range(max(a, b - 3), b + 1) if x * x + s >= 1 << n)
                l += 1
            self.assertLessEqual(cnt, 2, n)

    def test_newton_isqrt(self):
        rng = random.Random("test-spo-newton")
        qs = list(range(1 << 12)) + [rng.getrandbits(rng.randint(1, 400)) for _ in range(3000)]
        for q in qs:
            st = {}
            self.assertEqual(G.isqrt_newton(q, st), math.isqrt(q))
            if q >= 1:
                t = 0                                           # floor(log2(2 + log2 q)) in exact integers
                while (1 << (t + 1)) - 2 <= q.bit_length() - 1:
                    t += 1
                self.assertLessEqual(st["newton_steps"], t + 2)


if __name__ == "__main__":
    unittest.main()
