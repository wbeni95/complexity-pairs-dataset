"""Deterministic checks for pairs/first-match-rule-ordering-enumeration-vs-subset-dp/PROOFS.md, section 11: the subset
DP with zeta-transformed gains (implementations/zeta_dp.py). A few seconds; the larger V2 range, the oracle and the
recorded control numbers are in experiments/2026-10-13_first_match_zeta_checks.py.

Ranges: correctness against brute force over all orders, k <= 6, and the identity with the subset DP's output, k <= 9
(11.4); the gain identity and the tables after every transform pass, read from the unchanged code, k <= 5 (11.2,
11.3); Theorem 11.5 on seeded instances, k <= 7, and Corollary 11.6, k = 0..12; the subset DP's counts per item in the
counting convention, k <= 7, the interval of the fixed-k speed-up, k <= 40, and its limit on a uniform family (11.8);
line-execution counts, k <= 8 (11.7); tracemalloc peaks, k = 8..14 (11.7); negative controls (modified copies of
zeta_dp.py, among them tables built from the plain 0).
"""
import importlib.util
import itertools
import random
import sys
import tracemalloc
import unittest
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "first-match-rule-ordering-enumeration-vs-subset-dp"
ZETA_PATH = ENTRY / "implementations" / "zeta_dp.py"


def _load(path, name, source=None):
    if source is None:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod
    mod = type(sys)(name)
    mod.__file__ = str(path)
    exec(compile(source, str(path), "exec"), mod.__dict__)
    return mod


H = _load(ENTRY / "harness.py", "proofs_fmz_harness")
DP = _load(ENTRY / "implementations" / "subset_dp.py", "proofs_fmz_dp").first_match_order_subset_dp
ZETA = _load(ZETA_PATH, "proofs_fmz_zeta").first_match_order_zeta_dp


def brute_opt(inst):
    k = inst[0]
    return min(H.order_cost(inst, order) for order in itertools.permutations(range(k)))


def instances(k_values, per_k, tag):
    for k in k_values:
        for t in range(per_k):
            yield H.generate(k, random.Random(f"{tag}|{k}|{t}"))


def counted(inst):
    k, match, cost, default = inst
    C = H.CountingInt
    return (k, tuple(tuple(C(x) for x in row) for row in match), tuple(tuple(C(x) for x in row) for row in cost),
            tuple(C(x) for x in default))


def masks_of(inst):
    k, match = inst[0], inst[1]
    return [sum(1 << r for r in range(k) if row[r]) for row in match]


def tables(inst):
    """a_r[U] of section 11.1, computed from the definition."""
    k, match, cost, default = inst
    a = [[0] * (1 << k) for _ in range(k)]
    for i, U in enumerate(masks_of(inst)):
        for r in range(k):
            if U >> r & 1:
                a[r][U] += cost[i][r]
    return a


def gain(inst, S, r):
    """gain(S, r) from its definition (section 4.1)."""
    k, match, cost, default = inst
    return sum(cost[i][r] for i, U in enumerate(masks_of(inst)) if U >> r & 1 and not U & S)


def line_numbers(path, *texts):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    out = []
    for text in texts:
        hits = [i + 1 for i, line in enumerate(lines) if line.strip() == text]
        assert len(hits) == 1, (text, hits)
        out.append(hits[0])
    return out


def run_traced(func, arg, on_line, lines, on_return=None):
    """Run func(arg) with a tracer that calls on_line(frame) before each listed line and on_return(frame) at return."""
    code = func.__code__

    def local(frame, event, a):
        if event == "line" and frame.f_lineno in lines:
            on_line(frame)
        elif event == "return" and on_return is not None:
            on_return(frame)
        return local

    def glob(frame, event, a):
        return local if frame.f_code is code else None

    sys.settrace(glob)
    try:
        return func(arg)
    finally:
        sys.settrace(None)


def all_rules_match(inst):
    k, match = inst[0], inst[1]
    return k >= 1 and all(any(row[r] for row in match) for r in range(k))


def closed_v2(k):
    """Corollary 11.6 (k >= 2)."""
    return k * k + 2 * k + 2 + (k * k + 2 * k - 2) * 2 ** (k - 1)


class Correctness(unittest.TestCase):
    def test_against_all_orders(self):
        for inst in instances(range(0, 7), 8, "proofs-fmz-corr"):
            opt = brute_opt(inst)
            value, order = ZETA(inst)
            self.assertEqual(value, opt)
            self.assertEqual(H.order_cost(inst, order), opt)               # the returned order attains it

    def test_same_output_as_subset_dp(self):
        # Theorem 11.4: the same values in the same steps with the same tie rule, hence the same pair
        for inst in instances(range(0, 10), 6, "proofs-fmz-same"):
            self.assertEqual(ZETA(inst), DP(inst))


class Transform(unittest.TestCase):
    def test_gain_identity_and_every_pass(self):
        # 11.3: before pass b, a[r][W] sums a_r[U] over U subset of W that agree with W on the bits >= b;
        # after the last pass it is zeta a_r[W]; 11.2: gain(S, r) = zeta a_r[complement of S].
        (pass_line,) = line_numbers(ZETA_PATH, "bit = 1 << b")
        for inst in instances(range(0, 6), 6, "proofs-fmz-passes"):
            k = inst[0]
            full = (1 << k) - 1
            a0 = tables(inst)
            states, final = [], {}
            run_traced(ZETA, inst, lambda f: states.append((f.f_locals["r"], f.f_locals["b"], list(f.f_locals["z"]))),
                       {pass_line}, lambda f: final.setdefault("a", [list(row) for row in f.f_locals["a"]]))
            self.assertEqual(len(states), k * k)
            for r, b, z in states:
                keep = full & ~((1 << b) - 1)                                 # the bits >= b
                for W in range(1 << k):
                    want = sum(a0[r][U] for U in range(1 << k) if U & ~W == 0 and U & keep == W & keep)
                    self.assertEqual(z[W], want, (k, r, b, W))
            for r in range(k):
                for W in range(1 << k):
                    self.assertEqual(final["a"][r][W], sum(a0[r][U] for U in range(1 << k) if U & ~W == 0))
                for S in range(1 << k):
                    if not S >> r & 1:
                        self.assertEqual(final["a"][r][full ^ S], gain(inst, S, r), (k, S, r))


class Counts(unittest.TestCase):
    def test_theorem_11_5(self):
        seen = set()
        for inst in instances(range(0, 8), 6, "proofs-fmz-thm"):
            k, match = inst[0], inst[1]
            m = len(match)
            L = sum(sum(row) for row in match)
            m0 = sum(1 for row in match if not any(row))
            H.reset_counter()
            ZETA(counted(inst))
            ops = H.counts_by_kind()
            if k >= 1 and m >= 1:
                seen.add("k, m >= 1")
                want = {"truth": k * m, "compare": k * 2 ** (k - 1) - 2 ** k + 1,
                        "add": L + m0 + k * k * 2 ** (k - 1) + k * 2 ** (k - 1) + 1, "bit": 0}
            elif m == 0:
                seen.add("m = 0")
                want = {"truth": 0, "compare": 0, "add": 0, "bit": 0}
            else:
                seen.add("k = 0")
                want = {"truth": 0, "compare": 0, "add": m + 1, "bit": 0}
            self.assertEqual(ops, want, (k, m))
        self.assertEqual(seen, {"k, m >= 1", "m = 0", "k = 0"})

    def test_corollary_11_6(self):
        for k in range(0, 13):
            ZETA(H.generate_scaling(k, random.Random(f"proofs-fmz-v2|{k}")))
            if k >= 2:
                self.assertEqual(H.reported_cost(None), closed_v2(k))
                self.assertEqual(H.counts_by_kind(), {"truth": k * k, "compare": k * 2 ** (k - 1) - 2 ** k + 1,
                                                      "add": 2 * k + 1 + (k * k + k) * 2 ** (k - 1), "bit": 0})
            else:
                self.assertEqual(H.reported_cost(None), (0, 5)[k])

    def test_v2_against_subset_dp(self):
        # 11.6: fewer counted operations than the subset DP for k = 2..5, more for every k >= 6
        for k in range(2, 41):
            dp = 3 * k * k + (7 * k - 2) * 2 ** (k - 1) + 2
            self.assertEqual(closed_v2(k) > dp, k >= 6, k)
            self.assertEqual(closed_v2(k) - dp, (k * k - 5 * k) * 2 ** (k - 1) - 2 * k * k + 2 * k)

    def test_subset_dp_per_item_counts(self):
        # 11.8(b): the subset DP in the counting convention, every entry a CountingInt, k >= 1
        exact = 0
        for inst in instances(range(1, 8), 6, "proofs-fmz-dpcount"):
            k, match = inst[0], inst[1]
            m = len(match)
            ts = [sum(row) for row in match]
            G = sum(t * 2 ** (k - t) for t in ts if t)
            m0 = ts.count(0)
            H.reset_counter()
            DP(counted(inst))
            ops = H.counts_by_kind()
            self.assertEqual(ops["truth"], k * m + m * 2 ** k)
            self.assertEqual(ops["bit"], k * m + m * 2 ** k)
            low, top = k * m + G + m0, k * m + G + m0 + k * 2 ** (k - 1) + 1
            if all_rules_match(inst):
                exact += 1
                self.assertEqual(ops["add"], top)
                self.assertEqual(ops["compare"], k * 2 ** (k - 1) - 2 ** k + 1)
            else:
                self.assertTrue(low <= ops["add"] <= top)
                self.assertLessEqual(ops["compare"], k * 2 ** (k - 1) - 2 ** k + 1)
        self.assertGreater(exact, 0)


class Comparison(unittest.TestCase):
    @staticmethod
    def f(k, t):
        if t == 0:
            return Fraction(3 * k + 2 ** (k + 1) + 1, k + 1)
        return Fraction(3 * k + 2 ** (k + 1) + t * 2 ** (k - t), k + t)

    def test_fixed_k_interval(self):
        for k in range(1, 41):
            lo, hi = Fraction(2 ** k, k) + Fraction(3, 2), Fraction(5 * 2 ** (k - 1), k) + 3
            for t in range(0, k + 1):
                self.assertTrue(lo <= self.f(k, t) <= hi, (k, t))

    def test_uniform_family_tends_to_f(self):
        # k = 6, every item matched by the two rules i, i + 1 (mod k): the counted totals are m d(2) + R1 and
        # m v(2) + R2 exactly (11.8(b)), and their quotient approaches f(6, 2) as m grows
        k, t = 6, 2
        target = self.f(k, t)
        r1 = k * 2 ** k - 2 ** k + 2
        r2 = k * k * 2 ** (k - 1) + k * 2 ** k - 2 ** k + 2
        gaps = []
        for m in (12, 192, 3072):
            rng = random.Random(f"proofs-fmz-uniform|{m}")
            match = [[1 if r in (i % k, (i + 1) % k) else 0 for r in range(k)] for i in range(m)]
            inst = H._freeze(k, match, [[rng.randint(0, 9) for _ in range(k)] for _ in range(m)], [1] * m)
            H.reset_counter()
            DP(counted(inst))
            dp_ops = H.reported_cost(None)
            H.reset_counter()
            ZETA(counted(inst))
            zeta_ops = H.reported_cost(None)
            self.assertEqual(dp_ops, m * (3 * k + 2 ** (k + 1) + t * 2 ** (k - t)) + r1)
            self.assertEqual(zeta_ops, m * (k + t) + r2)
            gaps.append(abs(Fraction(dp_ops, zeta_ops) - target))
        self.assertTrue(gaps[0] > gaps[1] > gaps[2], gaps)
        self.assertLess(gaps[2], target / 10)


class Work(unittest.TestCase):
    def test_line_counts(self):
        texts = ("a[r][u] = a[r][u] + cost[i][r]", "base = base + default[i]", "if w & bit:",
                 "z[w] = z[w] + z[w ^ bit]",
                 "value = best_s + a[r][rest]      # gain(s, r) = zeta a_r [complement of s]")
        lines = line_numbers(ZETA_PATH, *texts)
        for inst in instances(range(0, 9), 4, "proofs-fmz-lines"):
            k, match = inst[0], inst[1]
            counts = dict.fromkeys(lines, 0)

            def hit(frame):
                counts[frame.f_lineno] += 1

            run_traced(ZETA, inst, hit, set(lines))
            L = sum(sum(row) for row in match)
            m0 = sum(1 for row in match if not any(row))
            self.assertEqual([counts[x] for x in lines],
                             [L, m0, k * k * 2 ** k, k * k * 2 ** k // 2, k * 2 ** k // 2])


class WorkingMemory(unittest.TestCase):
    def test_peaks(self):
        for k in range(8, 15):
            rng = random.Random(k)
            inst = H._freeze(k, H.cyclic_items(k), [[rng.randint(1, 9) for _ in range(k)] for _ in range(k)], [1] * k)
            tracemalloc.start()
            tracemalloc.reset_peak()
            base = tracemalloc.get_traced_memory()[0]
            ZETA(inst)
            peak = tracemalloc.get_traced_memory()[1] - base
            tracemalloc.stop()
            self.assertTrue(8 * k * 2 ** k <= peak <= 16 * (k + 2) * 2 ** k, (k, peak))   # k tables, best, last


class NegativeControls(unittest.TestCase):
    @staticmethod
    def mutant(old, new):
        src = ZETA_PATH.read_text(encoding="utf-8")
        assert src.count(old) == 1
        return _load(ZETA_PATH, "proofs_fmz_mutant", src.replace(old, new)).first_match_order_zeta_dp

    def test_gain_at_s_instead_of_complement_is_caught(self):
        wrong = self.mutant("value = best_s + a[r][rest]", "value = best_s + a[r][s]")
        insts = list(instances(range(0, 7), 8, "proofs-fmz-corr"))
        self.assertTrue(any(wrong(inst)[0] != brute_opt(inst) for inst in insts))

    def test_extra_counted_operation_is_caught(self):
        extra = self.mutant("value = best_s + a[r][rest]", "value = (best_s + a[r][rest]) + 0")
        for k in range(2, 8):
            extra(H.generate_scaling(k, random.Random(k)))
            self.assertNotEqual(H.reported_cost(None), closed_v2(k))

    def test_uncounted_tables_are_caught(self):
        # the tables built from the plain 0: additions of two plain zeros go uncounted, and the V2 count drops
        plain = self.mutant("zero = type(cost[0][0])(0) if k and m else 0", "zero = 0")
        for k in range(2, 8):
            plain(H.generate_scaling(k, random.Random(k)))
            self.assertLess(H.reported_cost(None), closed_v2(k))


if __name__ == "__main__":
    unittest.main()
