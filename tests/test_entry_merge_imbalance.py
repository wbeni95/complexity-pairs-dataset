"""Tests for pairs/max-merge-imbalance-cubic-dp-vs-endpoint-dp (under a minute).

Exhaustive small-n equality of the cubic DP, the endpoint DP and an explicit enumeration of all merge trees; check()
accepts correct outputs and rejects wrong ones; the exact comparison and arithmetic counts equal the closed forms of
entry.json, and so do the candidate-only counts; the table sizes and the size of the numbers (PROOFS.md,
sections 5 and 6); the split dependence; the counterexamples of the caveats.
"""
import importlib.util
import json
import itertools
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "max-merge-imbalance-cubic-dp-vs-endpoint-dp"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "test_mi_harness")
CUBIC_MOD = _load(ENTRY / "implementations" / "cubic_dp.py", "test_mi_cubic")
END_MOD = _load(ENTRY / "implementations" / "endpoint_dp.py", "test_mi_endpoint")
CUBIC = CUBIC_MOD.merge_max_imbalance_cubic
END = END_MOD.merge_max_imbalance_endpoint


# The five merge trees of four piles, each as its merges (lo, k, hi) in the order used in the README:
# ((s0 s1)(s2 s3)), (((s0 s1) s2) s3), ((s0 (s1 s2)) s3), (s0 ((s1 s2) s3)), (s0 (s1 (s2 s3))).
FIVE_TREES = (((0, 1, 1), (2, 3, 3), (0, 2, 3)), ((0, 1, 1), (0, 2, 2), (0, 3, 3)), ((1, 2, 2), (0, 1, 2), (0, 3, 3)),
              ((1, 2, 2), (1, 3, 3), (0, 1, 3)), ((2, 3, 3), (1, 2, 3), (0, 1, 3)))


def merge_costs(sizes, f):
    """Per-merge costs of the five trees of four piles (README order)."""
    return [[f(sum(sizes[lo:k]), sum(sizes[k:hi + 1])) for lo, k, hi in t] for t in FIVE_TREES]


def exhaustive_vectors():
    """Every size vector with n = 0..4 and sizes 0..4, n = 5 and sizes 0..3, n = 6 and sizes 0..2."""
    for n, top in ((0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 3), (6, 2)):
        yield from itertools.product(range(top + 1), repeat=n + 1)


def tree_values(sizes, cost):
    """{last split k at the top: best total over merge trees with that last split}, by explicit enumeration."""
    out = {}
    for t in H.merge_trees(len(sizes)):
        v = sum(cost(sum(sizes[lo:k]), sum(sizes[k:hi + 1])) for lo, k, hi in t)
        k = t[0][1]
        out[k] = max(out.get(k, v), v)
    return out


def locals_at_return(fn, inst):
    """Run fn(inst) unchanged and return (output, a copy of fn's local variables at its return), via a profiler hook."""
    captured = {}
    code = fn.__code__

    def hook(frame, event, arg):
        if event == "return" and frame.f_code is code:
            captured.update(frame.f_locals)

    old = sys.getprofile()
    sys.setprofile(hook)
    try:
        out = fn(inst)
    finally:
        sys.setprofile(old)
    return out, captured


def prefix_sums(sizes):
    pre = [0]
    for x in sizes:
        pre.append(pre[-1] + x)
    return pre


TAG = "mi"
TABLE_FUNCTIONS = ((CUBIC, 40), (END, 80))  # (implementation, largest n of the table test)
SPLIT_COSTS = (0, 2)  # merge costs of the splits k = 1, 2 of the row (1, 1, 0)

class MergeImbalance(unittest.TestCase):
    def test_exhaustive_equality(self):
        count = 0
        for sizes in exhaustive_vectors():
            a, b = CUBIC(sizes), END(sizes)
            self.assertEqual(a, b, sizes)
            self.assertEqual(a, H.brute_force(sizes), sizes)
            count += 1
        self.assertEqual(count, 3905 + 4096 + 2187)

    def test_check_certifies_the_v1_battery(self):
        """check() returns True (certified, not None) for both outputs on every instance of the validator's V1 battery."""
        entry = json.loads((ENTRY / "entry.json").read_text(encoding="utf-8"))
        th = entry["test_harness"]
        runs = 0
        for n in th["v1_sizes"]:
            for trial in range(th["trials"]):
                inst = H.generate(n, random.Random(f"{entry['id']}|v1|{n}|{trial}"))
                for fn in (CUBIC, END):
                    self.assertIs(H.check(inst, fn(inst)), True, (n, trial))
                    runs += 1
        self.assertEqual(runs, 2 * len(th["v1_sizes"]) * th["trials"])

    def test_check_accepts_and_rejects(self):
        for n in list(range(0, 11)) + [12, 16, 25]:
            for t in range(4):
                inst = H.generate(n, random.Random(f"mi-test|{n}|{t}"))
                v = END(inst)
                self.assertEqual(v, CUBIC(inst))
                self.assertIs(H.check(inst, v), True)
                self.assertIs(H.check(inst, v + 1), False)
                self.assertIs(H.check(inst, v - 1), False)

    def test_certificate_matches_enumeration(self):
        rng = random.Random("mi-test|cert")
        for _ in range(60):
            n = rng.randint(1, 8)
            sizes = H.generate(n, rng)
            cert = H.certificate(sizes)
            self.assertTrue(cert["valid"])
            self.assertEqual(cert["lower"], cert["upper"])
            self.assertEqual(cert["lower"], H.brute_force(sizes))

    def _counts(self, fn, n):
        """(comparisons, additions + subtractions) of fn at n; the same for all 11 integer families (asserted)."""
        seen = set()
        for fam in H.SCALING_FAMILIES:
            inst = H.wrap_counting(H.instance_of(fam, n, random.Random(f"mi-count|{fam}|{n}")))
            H.reset_counters()
            fn(inst)
            seen.add(H.counters())
        self.assertEqual(len(seen), 1, (n, seen))
        return seen.pop()

    def test_comparison_and_arithmetic_counts(self):
        for n in range(0, 41):
            cmp_, ari = self._counts(CUBIC, n)
            self.assertEqual(cmp_, n * (n + 1) * (2 * n + 1) // 6, n)
            self.assertEqual(ari, (n + 1) + 5 * n * (n + 1) * (n + 2) // 6, n)
        for n in range(0, 81):
            cmp_, ari = self._counts(END, n)
            self.assertEqual(cmp_, n * (3 * n - 1) // 2, n)
            self.assertEqual(ari, (n + 1) + 5 * n * n, n)

    def test_counts_do_not_depend_on_the_family(self):
        for fam in H.SCALING_FAMILIES:
            for fn, formula in ((CUBIC, lambda n: n * (n + 1) * (2 * n + 1) // 6), (END, lambda n: n * (3 * n - 1) // 2)):
                inst = H.wrap_counting(H.instance_of(fam, 13, random.Random(fam)))
                H.reset_counters()
                fn(inst)
                self.assertEqual(H.counters()[0], formula(13), fam)

    def test_candidate_only_counts(self):
        """Total comparisons minus one per merge-cost evaluation = comparisons between candidate values."""
        for mod, fn, cand, evals in ((CUBIC_MOD, CUBIC, lambda n: (n + 1) * n * (n - 1) // 6,
                                      lambda n: n * (n + 1) * (n + 2) // 6),
                                     (END_MOD, END, lambda n: n * (n - 1) // 2, lambda n: n * n)):
            original = mod.merge_cost
            calls = [0]

            def counted(left, right, _orig=original):
                calls[0] += 1
                return _orig(left, right)

            mod.merge_cost = counted
            try:
                for n in range(0, 31):
                    calls[0] = 0
                    inst = H.generate_scaling(n, random.Random(n))
                    fn(inst)
                    self.assertEqual(calls[0], evals(n), n)
                    self.assertEqual(H.counters()[0] - calls[0], cand(n), n)
            finally:
                mod.merge_cost = original

    def test_negative_sizes_counterexample(self):
        sizes = (0, -1, 1, 0)
        self.assertEqual(CUBIC(sizes), 4)
        self.assertEqual(END(sizes), 3)
        self.assertEqual(H.brute_force(sizes), 4)
        tops = tree_values(sizes, lambda a, b: abs(a - b))
        self.assertEqual(max(tops.values()), 4)
        self.assertEqual([k for k, v in tops.items() if v == 4], [2])
        self.assertIs(H.check(sizes, 3), False)

    def test_min_direction_control(self):
        """min sum of |L - R|: the endpoint rule is wrong on (0, 1, 1, 0)."""
        sizes = (0, 1, 1, 0)
        trees = H.merge_trees(4)
        vals = [sum(abs(sum(sizes[lo:k]) - sum(sizes[k:hi + 1])) for lo, k, hi in t) for t in trees]
        caterpillar = [all(k in (lo + 1, hi) for lo, k, hi in t) for t in trees]
        self.assertEqual(min(vals), 2)
        self.assertEqual(min(v for v, cat in zip(vals, caterpillar) if cat), 3)

    def test_rs3_fails_but_the_law_holds(self):
        """Sizes (1, 0, 1, 2): the rotation sum at (i, a, k, b, j) = (0, 1, 2, 3, 3) is 2 + (-3) < 0, yet the
        endpoint DP is exact (Theorem 1 covers this weight; Corollary 2 does not)."""
        sizes = (1, 0, 1, 2)
        f = lambda a, b: abs(a - b)
        X, Y, Z, U = sizes
        L, R = X + Y, Z + U
        d_r = f(X, Y + R) + f(Y, R) - f(L, R) - f(X, Y)
        d_l = f(L + Z, U) + f(L, Z) - f(L, R) - f(Z, U)
        self.assertEqual((d_r, d_l), (2, -3))
        self.assertEqual(END(sizes), CUBIC(sizes))
        self.assertEqual(END(sizes), H.brute_force(sizes))

    def test_hand_computed_tree_costs(self):
        """The per-merge costs of the five trees quoted in the README's Limits section."""
        self.assertEqual(merge_costs((0, -1, 1, 0), lambda a, b: abs(a - b)), [[1, 1, 2], [1, 2, 0], [2, 0, 0], [2, 0, 0], [1, 2, 0]])
        self.assertEqual(merge_costs((0, 1, 1, 0), lambda a, b: abs(a - b)), [[1, 1, 0], [1, 0, 2], [0, 2, 2], [0, 2, 2], [1, 0, 2]])

    def test_time_and_space(self):
        """PROOFS.md section 5: at the return, the table c has n + 1 rows of length n + 1 and prefix has n + 2 entries."""
        runs = 0
        for fn, top in TABLE_FUNCTIONS:
            for n in range(0, top + 1):
                inst = H.generate(n, random.Random(f"{TAG}-space|{n}"))
                _, loc = locals_at_return(fn, inst)
                self.assertEqual(len(loc["c"]), n + 1, n)
                self.assertTrue(all(len(row) == n + 1 for row in loc["c"]), n)
                self.assertEqual(len(loc["prefix"]), n + 2, n)
                runs += 1
        self.assertEqual(runs, sum(top + 1 for _, top in TABLE_FUNCTIONS))

    def test_size_of_numbers(self):
        """PROOFS.md section 6: for sizes >= 0 every table entry c[i][j] lies in [0, (j - i) S(i, j)]."""
        rng = random.Random(f"{TAG}-size")
        runs = 0
        for _ in range(120):
            n = rng.randint(0, 40)
            sizes = H.generate(n, rng)
            pre = prefix_sums(sizes)
            for fn, _top in TABLE_FUNCTIONS:
                _, loc = locals_at_return(fn, sizes)
                c = loc["c"]
                for i in range(n + 1):
                    for j in range(i, n + 1):
                        self.assertTrue(0 <= c[i][j] <= (j - i) * (pre[j + 1] - pre[i]), (sizes, i, j))
                runs += 1
        self.assertEqual(runs, 120 * len(TABLE_FUNCTIONS))

    def test_split_dependence(self):
        """The merge cost depends on the split: sizes (1, 1, 0), row 0..2, splits k = 1 and k = 2."""
        sizes = (1, 1, 0)
        self.assertEqual([H.cost(sum(sizes[0:k]), sum(sizes[k:3])) for k in (1, 2)], list(SPLIT_COSTS))

    def test_small_cases(self):
        self.assertEqual(CUBIC((7,)), 0)
        self.assertEqual(END((7,)), 0)
        self.assertEqual(CUBIC((2, 5)), 3)
        self.assertEqual(END((2, 5)), 3)
        # (1, 1, 1): either order costs 0 + 1
        self.assertEqual(END((1, 1, 1)), 1)


if __name__ == "__main__":
    unittest.main()
