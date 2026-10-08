"""Tests for pairs/min-merge-cost-smaller-part-cubic-dp-vs-closed-form (under a minute).

Exhaustive small-n equality of the cubic DP, the closed form S - max s and an explicit enumeration of all merge
trees, with the closed form on every row and an endpoint minimiser in every row; check() accepts correct outputs and
rejects wrong ones; the exact comparison and arithmetic counts equal the closed forms of entry.json; the failures of
the mirrored rotation conditions; the table sizes, the state of the closed form and the size of the numbers
(PROOFS.md, sections 5 and 6); the endpoint DP; the split dependence; the counterexamples of the caveats.
"""
import importlib.util
import json
import itertools
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "min-merge-cost-smaller-part-cubic-dp-vs-closed-form"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "test_ms_harness")
CUBIC_MOD = _load(ENTRY / "implementations" / "cubic_dp.py", "test_ms_cubic")
CUBIC = CUBIC_MOD.merge_min_smaller_cubic
CLOSED = _load(ENTRY / "implementations" / "closed_form.py", "test_ms_closed").merge_min_smaller_closed_form


def exhaustive_vectors():
    """Every size vector with n = 0..4 and sizes 0..4, n = 5 and sizes 0..3, n = 6 and sizes 0..2."""
    for n, top in ((0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 3), (6, 2)):
        yield from itertools.product(range(top + 1), repeat=n + 1)


def table(sizes):
    """Full DP table c[(i, j)] and the set of minimising splits of every row (written for the tests)."""
    m = len(sizes)
    c, arg = {}, {}
    for i in range(m):
        c[(i, i)] = 0
    for d in range(1, m):
        for i in range(m - d):
            j = i + d
            vals = {k: min(sum(sizes[i:k]), sum(sizes[k:j + 1])) + c[(i, k - 1)] + c[(k, j)] for k in range(i + 1, j + 1)}
            c[(i, j)] = min(vals.values())
            arg[(i, j)] = {k for k, v in vals.items() if v == c[(i, j)]}
    return c, arg


def deltas_min(X, Y, Z, U):
    """Rotation changes Delta_R, Delta_L of w = min(L, R) at a block decomposition X, Y | Z, U (note, Lemma 10)."""
    f = min
    L, R = X + Y, Z + U
    return f(X, Y + R) + f(Y, R) - f(L, R) - f(X, Y), f(L + Z, U) + f(L, Z) - f(L, R) - f(Z, U)


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


TAG = "ms"
TABLE_FUNCTIONS = ((CUBIC, 40),)  # (implementation, largest n of the table test)
SPLIT_COSTS = (1, 0)  # merge costs of the splits k = 1, 2 of the row (1, 1, 0)

class MergeSmallerPart(unittest.TestCase):
    def test_exhaustive_equality_closed_form_and_endpoint_law(self):
        count = 0
        for sizes in exhaustive_vectors():
            a, b = CUBIC(sizes), CLOSED(sizes)
            self.assertEqual(a, b, sizes)
            self.assertEqual(a, H.brute_force(sizes), sizes)
            c, arg = table(sizes)
            for (i, j), v in c.items():
                self.assertEqual(v, sum(sizes[i:j + 1]) - max(sizes[i:j + 1]), (sizes, i, j))
                if j > i:
                    self.assertTrue(arg[(i, j)] & {i + 1, j}, (sizes, i, j))
            count += 1
        self.assertEqual(count, 3905 + 4096 + 2187)

    def test_every_caterpillar_from_a_largest_pile_attains_the_closed_form(self):
        """Proposition, upper bound: any caterpillar whose first merge involves a largest pile costs S - max s."""
        for sizes in exhaustive_vectors():
            m = len(sizes)
            if m > 6:
                continue
            S, M = sum(sizes), max(sizes)
            for t in H.merge_trees(m):
                if m == 1 or not all(k in (lo + 1, hi) for lo, k, hi in t):
                    continue
                first = [(lo, hi) for lo, k, hi in t if hi - lo == 1][0]
                if M in (sizes[first[0]], sizes[first[1]]):
                    cost = sum(min(sum(sizes[lo:k]), sum(sizes[k:hi + 1])) for lo, k, hi in t)
                    self.assertEqual(cost, S - M, (sizes, t))
            self.assertEqual(H.certificate(sizes)["upper"], S - M)

    def test_check_certifies_the_v1_battery(self):
        """check() returns True (certified, not None) for both outputs on every instance of the validator's V1 battery."""
        entry = json.loads((ENTRY / "entry.json").read_text(encoding="utf-8"))
        th = entry["test_harness"]
        runs = 0
        for n in th["v1_sizes"]:
            for trial in range(th["trials"]):
                inst = H.generate(n, random.Random(f"{entry['id']}|v1|{n}|{trial}"))
                for fn in (CUBIC, CLOSED):
                    self.assertIs(H.check(inst, fn(inst)), True, (n, trial))
                    runs += 1
        self.assertEqual(runs, 2 * len(th["v1_sizes"]) * th["trials"])

    def test_check_accepts_and_rejects(self):
        for n in list(range(0, 11)) + [12, 16, 25]:
            for t in range(4):
                inst = H.generate(n, random.Random(f"ms-test|{n}|{t}"))
                v = CLOSED(inst)
                self.assertEqual(v, CUBIC(inst))
                self.assertIs(H.check(inst, v), True)
                self.assertIs(H.check(inst, v + 1), False)
                self.assertIs(H.check(inst, v - 1), False)

    def test_certificate_matches_enumeration(self):
        rng = random.Random("ms-test|cert")
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
            inst = H.wrap_counting(H.instance_of(fam, n, random.Random(f"ms-count|{fam}|{n}")))
            H.reset_counters()
            fn(inst)
            seen.add(H.counters())
        self.assertEqual(len(seen), 1, (n, seen))
        return seen.pop()

    def test_comparison_and_arithmetic_counts(self):
        for n in range(0, 41):
            cmp_, ari = self._counts(CUBIC, n)
            self.assertEqual(cmp_, n * (n + 1) * (2 * n + 1) // 6, n)
            self.assertEqual(ari, (n + 1) + 2 * n * (n + 1) * (n + 2) // 3, n)
        for n in list(range(0, 200)) + [1000, 4096]:
            cmp_, ari = self._counts(CLOSED, n)
            self.assertEqual(cmp_, n, n)
            self.assertEqual(ari, n + 1, n)

    def test_counts_do_not_depend_on_the_family(self):
        for fam in H.SCALING_FAMILIES:
            for fn, formula in ((CUBIC, lambda n: n * (n + 1) * (2 * n + 1) // 6), (CLOSED, lambda n: n)):
                inst = H.wrap_counting(H.instance_of(fam, 13, random.Random(fam)))
                H.reset_counters()
                fn(inst)
                self.assertEqual(H.counters()[0], formula(13), fam)

    def test_candidate_only_counts(self):
        original = CUBIC_MOD.merge_cost
        calls = [0]

        def counted(left, right):
            calls[0] += 1
            return original(left, right)

        CUBIC_MOD.merge_cost = counted
        try:
            for n in range(0, 31):
                calls[0] = 0
                inst = H.generate_scaling(n, random.Random(n))
                CUBIC(inst)
                self.assertEqual(calls[0], n * (n + 1) * (n + 2) // 6, n)
                self.assertEqual(H.counters()[0] - calls[0], (n + 1) * n * (n - 1) // 6, n)
        finally:
            CUBIC_MOD.merge_cost = original

    def test_mirrored_rotation_conditions_fail(self):
        # the min form of Corollary 2 needs RS3 for -w: Delta_R + Delta_L <= 0 for w; it fails here
        self.assertEqual(deltas_min(0, 1, 1, 2), (0, 1))
        self.assertEqual(deltas_min(1, 1, 2, 4), (-1, 2))
        self.assertEqual(deltas_min(1, 9, 5, 15), (-1, 5))
        # the min form of Theorem 1 needs RS3w for -w: Delta_R >= 0 and Delta_L >= 0 imply Delta_R = 0; it fails here
        self.assertEqual(deltas_min(2, 1, 0, 1), (1, 0))
        # and the endpoint law still holds on these rows (closed form)
        for sizes in ((0, 1, 1, 2), (1, 1, 2, 4), (1, 9, 5, 15), (2, 1, 0, 1)):
            c, arg = table(sizes)
            self.assertTrue(arg[(0, 3)] & {1, 3})
            self.assertEqual(CUBIC(sizes), CLOSED(sizes))

    def test_negative_sizes_counterexample(self):
        sizes = (-1, 0, 0)
        self.assertEqual(CUBIC(sizes), -2)
        self.assertEqual(H.brute_force(sizes), -2)
        self.assertEqual(CLOSED(sizes), -1)
        self.assertIs(H.check(sizes, -1), False)

    def test_max_direction_control(self):
        """max sum of min(L, R) is a different problem: the endpoint rule is wrong on (1, 1, 1, 1)."""
        sizes = (1, 1, 1, 1)
        trees = H.merge_trees(4)
        vals = [sum(min(sum(sizes[lo:k]), sum(sizes[k:hi + 1])) for lo, k, hi in t) for t in trees]
        caterpillar = [all(k in (lo + 1, hi) for lo, k, hi in t) for t in trees]
        self.assertEqual(max(vals), 4)
        self.assertEqual(max(v for v, cat in zip(vals, caterpillar) if cat), 3)

    def test_hand_computed_tree_costs(self):
        """The tree costs quoted in the README's Limits section."""
        sizes = (-1, 0, 0)
        costs = sorted(sum(min(sum(sizes[lo:k]), sum(sizes[k:hi + 1])) for lo, k, hi in t) for t in H.merge_trees(3))
        self.assertEqual(costs, [-2, -1])
        sizes = (1, 1, 1, 1)
        for t in H.merge_trees(4):
            v = sum(min(sum(sizes[lo:k]), sum(sizes[k:hi + 1])) for lo, k, hi in t)
            self.assertEqual(v, 4 if t[0][1] == 2 else 3)

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

    def test_closed_form_state(self):
        """PROOFS.md section 5: the closed form keeps only sizes, total, largest and the loop variable."""
        for n in range(0, 50):
            inst = H.generate(n, random.Random(f"ms-state|{n}"))
            _, loc = locals_at_return(CLOSED, inst)
            self.assertEqual(set(loc), {"sizes", "total", "largest"} | ({"s"} if n >= 1 else set()), n)

    def test_endpoint_dp_is_exact(self):
        """README, 'The endpoint law': the endpoint DP (two end splits per row, written here) equals the cubic DP."""
        def endpoint(sizes):
            n = len(sizes) - 1
            pre = prefix_sums(sizes)
            c = [[0] * (n + 1) for _ in range(n + 1)]
            for length in range(1, n + 1):
                for i in range(n - length + 1):
                    j = i + length
                    c[i][j] = min(min(pre[k] - pre[i], pre[j + 1] - pre[k]) + c[i][k - 1] + c[k][j]
                                  for k in ((i + 1, j) if length >= 2 else (j,)))
            return c[0][n]

        count = 0
        for sizes in exhaustive_vectors():
            self.assertEqual(endpoint(sizes), CUBIC(sizes), sizes)
            count += 1
        self.assertEqual(count, 3905 + 4096 + 2187)

    def test_small_cases(self):
        self.assertEqual(CLOSED((7,)), 0)
        self.assertEqual(CUBIC((7,)), 0)
        self.assertEqual(CLOSED((2, 5)), 2)
        self.assertEqual(CUBIC((2, 5)), 2)
        self.assertEqual(CLOSED((3, 1, 4, 1, 5)), 9)
        self.assertEqual(CUBIC((3, 1, 4, 1, 5)), 9)


if __name__ == "__main__":
    unittest.main()
