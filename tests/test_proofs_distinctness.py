"""Checks for pairs/element-distinctness-pairs-vs-sorting/PROOFS.md, sections 3-6.

Merge sort: the pass invariant (after the pass of width w every block of length 2w is sorted), read from the running
code with sys.settrace, and the sorted-permutation output; both implementations against an oracle on inputs with and
without ties; the comparison lower bound: the Stirling inequality and, for n <= 4, the exact minimum worst-case
number of three-way comparisons of any comparison tree deciding distinctness (exhaustive minimax over weak orders);
and the space bounds. All inputs come from fixed seeds. Runs in a few seconds.
"""
import importlib.util
import itertools
import math
import random
import sys
import unittest
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "element-distinctness-pairs-vs-sorting"
sys.path.insert(0, str(REPO / "tests"))

from proof_space import peak_words  # noqa: E402


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = _load(E / "harness.py", "tp_ed_h")
AP_FILE = E / "implementations" / "all_pairs.py"
SORT_FILE = E / "implementations" / "sort_adjacent.py"
AP = _load(AP_FILE, "tp_ed_ap").distinct_all_pairs
SORT_MOD = _load(SORT_FILE, "tp_ed_s")
SORT = SORT_MOD.distinct_by_sorting


def _line_of(path, text):
    for k, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip() == text:
            return k
    raise AssertionError(f"line {text!r} not found in {path}")


def inputs(tag, count):
    rng = random.Random(f"tp-ed|{tag}")
    for t in range(count):
        n = rng.randint(0, 130)
        kind = t % 4
        if kind == 0:
            yield tuple(rng.sample(range(-10 ** 6, 10 ** 6), n))
        elif kind == 1:
            yield tuple(rng.randrange(max(1, n // 3)) for _ in range(n))
        elif kind == 2:
            vals = rng.sample(range(10 ** 6), n)
            if n >= 2:
                vals[-1] = vals[-2]
            yield tuple(vals)
        else:
            yield tuple(sorted(rng.sample(range(10 ** 6), n), reverse=rng.random() < 0.5))


def weak_orders(n):
    """All patterns of n values up to order-isomorphism, as tuples of ranks 0..k-1 (ties allowed)."""
    out = set()
    for vals in itertools.product(range(n), repeat=n):
        ranks = {v: i for i, v in enumerate(sorted(set(vals)))}
        out.add(tuple(ranks[v] for v in vals))
    return sorted(out)


def min_depth_distinctness(n):
    """Minimum worst-case number of three-way comparisons of a comparison tree deciding distinctness of n values."""
    orders = weak_orders(n)
    pairs = list(itertools.combinations(range(n), 2))

    @lru_cache(maxsize=None)
    def depth(state):
        answers = {len(set(orders[s])) == n for s in state}
        if len(answers) <= 1:
            return 0
        best = math.inf
        for i, j in pairs:
            parts = {}
            for s in state:
                o = orders[s]
                parts.setdefault((o[i] > o[j]) - (o[i] < o[j]), []).append(s)
            if len(parts) == 1:
                continue
            best = min(best, 1 + max(depth(frozenset(p)) for p in parts.values()))
        return best

    return depth(frozenset(range(len(orders))))


class DistinctnessProofChecks(unittest.TestCase):
    def test_merge_sort_pass_invariant_and_output(self):
        line = _line_of(SORT_FILE, "width *= 2")
        target = str(SORT_FILE.resolve())
        for vals in inputs("merge", 200):
            n = len(vals)
            seen_widths = []

            def local(frame, event, arg):
                if event == "line" and frame.f_lineno == line:
                    a, w = frame.f_locals["a"], frame.f_locals["width"]
                    seen_widths.append(w)
                    for lo in range(0, n, 2 * w):
                        block = a[lo:lo + 2 * w]
                        self.assertEqual(block, sorted(block), (vals, w, lo))
                return local

            def glob(frame, event, arg):
                if frame.f_code.co_name == "_merge_sort" and str(Path(frame.f_code.co_filename).resolve()) == target:
                    return local
                return None

            sys.settrace(glob)
            try:
                out = SORT_MOD._merge_sort(vals)
            finally:
                sys.settrace(None)
            self.assertEqual(out, sorted(vals))
            self.assertEqual(seen_widths, [1 << k for k in range((n - 1).bit_length())] if n else [])

    def test_both_correct(self):
        yes = no = 0
        for vals in inputs("correct", 400):
            truth = len(set(vals)) == len(vals)
            self.assertEqual(AP(vals), truth)
            self.assertEqual(SORT(vals), truth)
            yes += truth
            no += not truth
        self.assertGreater(yes, 100)
        self.assertGreater(no, 100)

    def test_comparison_lower_bound(self):
        for n in range(1, 3001):
            log2_fact = math.lgamma(n + 1) / math.log(2)
            self.assertGreaterEqual(log2_fact + 1e-9, n * math.log2(n) - n * math.log2(math.e))
        for n in range(1, 5):
            d = min_depth_distinctness(n)
            self.assertGreaterEqual(d, math.ceil(math.log2(math.factorial(n))), n)
        # the implementations' worst cases respect the bound: all pairs n(n-1)/2, sorting <= n ceil(log2 n) + n - 1
        for n in range(1, 200):
            lb = math.ceil(math.lgamma(n + 1) / math.log(2) - 1e-9)
            self.assertGreaterEqual(n * (n - 1) // 2, lb)
            self.assertGreaterEqual(n * (n - 1).bit_length() + n - 1, lb)

    def test_space(self):
        for vals in inputs("space", 20):
            n = len(vals)
            _, pa = peak_words(AP, (vals,), AP_FILE)
            self.assertEqual(pa, 0, n)
            _, ps = peak_words(SORT, (vals,), SORT_FILE)
            self.assertEqual(ps, 2 * n, n)


if __name__ == "__main__":
    unittest.main()
