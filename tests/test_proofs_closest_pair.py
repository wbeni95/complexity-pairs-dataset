"""Checks for pairs/closest-pair-brute-vs-divide-conquer/PROOFS.md, sections 3-6.

Correctness of both implementations on adversarial inputs (duplicates, coincident points split by the median line,
all points on one vertical line, lattices, clusters); the packing lemma (at most 8 examined pairs and at most 7 full
distance evaluations per strip point, counted per strip point from the running code with sys.settrace); the bounds
on the strip-filter sum S(n); the numbers and sizes of the sorted() and min() calls; and the space bounds. All inputs
come from fixed seeds. Runs in a few seconds.
"""
import importlib.util
import itertools
import math
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "closest-pair-brute-vs-divide-conquer"
sys.path.insert(0, str(REPO / "tests"))

from proof_space import peak_words  # noqa: E402


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = _load(E / "harness.py", "tp_cp_h")
BRUTE_FILE = E / "implementations" / "brute_force.py"
DC_FILE = E / "implementations" / "divide_conquer.py"
BRUTE = _load(BRUTE_FILE, "tp_cp_b").closest_pair_brute
DC_MOD = _load(DC_FILE, "tp_cp_dc")
DC = DC_MOD.closest_pair_dc


def _line_of(path, text):
    for k, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip() == text:
            return k
    raise AssertionError(f"line {text!r} not found in {path}")


def point_sets(tag, count):
    rng = random.Random(f"tp-cp|{tag}")
    for t in range(count):
        n = rng.randint(2, 70)
        kind = t % 7
        if kind == 0:
            pts = [(rng.randrange(10 ** 6), rng.randrange(10 ** 6)) for _ in range(n)]
        elif kind == 1:                                  # tiny grid: many duplicates
            r = int(math.isqrt(n)) + 1
            pts = [(rng.randrange(r), rng.randrange(r)) for _ in range(n)]
        elif kind == 2:                                  # one vertical line: every point in the strip
            x = rng.randrange(100)
            pts = [(x, rng.randrange(10 ** 4)) for _ in range(n)]
        elif kind == 3:                                  # square lattice with spacing 5
            side = int(math.isqrt(n)) + 1
            pts = [(5 * (i % side), 5 * (i // side)) for i in range(n)]
        elif kind == 4:                                  # two columns straddling the median, same rows
            pts = [(10 + (i % 2), 3 * (i // 2)) for i in range(n)]
        elif kind == 5:                                  # coincident pairs placed on the median line
            pts = [(rng.randrange(50), rng.randrange(10 ** 5)) for _ in range(n - 2)]
            xs = sorted(p[0] for p in pts)
            xm = xs[len(xs) // 2] if xs else 0
            y = rng.randrange(10 ** 5)
            pts += [(xm, y), (xm, y)]
        else:                                            # clusters with negative coordinates
            centres = [(rng.randint(-1000, 1000), rng.randint(-1000, 1000)) for _ in range(3)]
            pts = [(cx + rng.randint(-3, 3), cy + rng.randint(-3, 3))
                   for cx, cy in (rng.choice(centres) for _ in range(n))]
        rng.shuffle(pts)
        yield tuple(pts)


def strip_counts(points):
    """Run closest_pair_dc; return the list of (examined pairs, full evaluations) per strip point of every call."""
    examined_line = _line_of(DC_FILE, "dy = yb - ya")
    full_line = _line_of(DC_FILE, "dx = xb - xa")
    target = str(DC_FILE.resolve())
    counts = {}
    serials = {}          # id(frame) -> serial number of the call (ids can be reused after a frame dies)
    calls = itertools.count()

    def local(frame, event, arg):
        if event == "line" and frame.f_lineno in (examined_line, full_line):
            key = (serials[id(frame)], frame.f_locals["a"])
            e, f = counts.get(key, (0, 0))
            counts[key] = (e + 1, f) if frame.f_lineno == examined_line else (e, f + 1)
        return local

    def glob(frame, event, arg):
        if frame.f_code.co_name == "_solve" and str(Path(frame.f_code.co_filename).resolve()) == target:
            serials[id(frame)] = next(calls)
            return local
        return None

    sys.settrace(glob)
    try:
        result = DC(points)
    finally:
        sys.settrace(None)
    return result, list(counts.values())


def S(n, memo={}):
    if n <= 3:
        return 0
    if n not in memo:
        memo[n] = n + S(n // 2) + S(n - n // 2)
    return memo[n]


class ClosestPairProofChecks(unittest.TestCase):
    def test_correct_on_adversarial_inputs(self):
        for pts in point_sets("correct", 420):
            b, d = BRUTE(pts), DC(pts)
            self.assertEqual(b, d, pts)
            self.assertIs(H.check(pts, d), True, pts)
            self.assertEqual(d == 0, len(set(pts)) < len(pts))               # answer 0 iff two points coincide
        for bad in ((), ((1, 2),)):
            with self.assertRaises(ValueError):
                DC(bad)
            with self.assertRaises(ValueError):
                BRUTE(bad)

    def test_strip_packing(self):
        worst_e = worst_f = 0
        for pts in point_sets("packing", 280):
            result, per_point = strip_counts(pts)
            self.assertEqual(result, BRUTE(pts))
            for e, f in per_point:
                self.assertLessEqual(e, 8, pts)
                self.assertLessEqual(f, 7, pts)
                self.assertLessEqual(f, e)
                worst_e, worst_f = max(worst_e, e), max(worst_f, f)
        self.assertGreaterEqual(worst_e, 3)        # the scans are not trivially short on these inputs

    def test_strip_filter_sum_bounds(self):
        for n in range(4, 5001):
            lo = n * (n.bit_length() - 2)              # n (floor(log2 n) - 1)
            hi = n * (n - 1).bit_length()              # n ceil(log2 n)
            self.assertTrue(lo <= S(n) <= hi, (n, S(n), lo, hi))
        self.assertEqual(S(64000), 955392)

    def test_builtin_call_counts(self):
        """sorted() is called 1 + #leaves times (once on n points, otherwise on at most 3), min() 2 #leaves - 1 times
        (at most 3 values each). The calls are counted by wrappers placed in the module's globals; the code is
        unchanged."""
        def leaves(s):
            return 1 if s <= 3 else leaves(s // 2) + leaves(s - s // 2)

        calls = {"sorted": [], "min": []}

        def counting_sorted(it, *a, **k):
            out = sorted(it, *a, **k)
            calls["sorted"].append(len(out))
            return out

        def counting_min(*args):
            vals = list(args[0]) if len(args) == 1 else list(args)
            calls["min"].append(len(vals))
            return min(vals)

        DC_MOD.sorted, DC_MOD.min = counting_sorted, counting_min
        try:
            rng = random.Random("tp-cp|builtins")
            for n in list(range(2, 120)) + [1000]:
                pts = tuple((rng.randrange(10 ** 6), rng.randrange(10 ** 6)) for _ in range(n))
                calls["sorted"].clear()
                calls["min"].clear()
                self.assertEqual(DC(pts), BRUTE(pts))
                L = leaves(n)
                self.assertLessEqual(L, n / 2)
                self.assertEqual(len(calls["sorted"]), 1 + L, n)
                self.assertEqual(calls["sorted"][0], n)
                self.assertTrue(all(k <= 3 for k in calls["sorted"][1:]), n)
                self.assertEqual(len(calls["min"]), 2 * L - 1, n)
                self.assertTrue(all(k <= 3 for k in calls["min"]), n)
                if n == 1000:
                    self.assertEqual((1 + L, 2 * L - 1), (489, 975))
        finally:
            del DC_MOD.sorted, DC_MOD.min

    def test_space(self):
        for pts in point_sets("space", 56):
            n = len(pts)
            _, pb = peak_words(BRUTE, (pts,), BRUTE_FILE)
            self.assertEqual(pb, 0, n)
            _, pd = peak_words(DC, (pts,), DC_FILE)
            self.assertTrue(n <= pd <= 5 * n + (n - 1).bit_length() + 6, (n, pd))


if __name__ == "__main__":
    unittest.main()
