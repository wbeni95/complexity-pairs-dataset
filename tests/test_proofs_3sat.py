"""Deterministic checks for pairs/3sat-brute-force-vs-schoening/PROOFS.md (a few seconds).

Each test names the PROOFS.md section whose computable facts it re-runs, and the range it covers:
  - brute force examines all 2^n assignments on unsatisfiable formulas (section 1), n = 3..10;
  - Schoening: one-sided error and the exact number of clause scans, flips and random draws on unsatisfiable
    formulas (sections 2.2 and 4), n = 3..8;
  - the coupling lemma (section 2.4): exact success probability of one try, from every start, on 140 seeded
    satisfiable formulas with n = 1..7 (including 1- and 2-literal clauses and repeated literals);
  - the restart budget (section 2.6): the implementation's T(n) against the exact ceiling for n = 0..373, and the
    OverflowError for n >= 374 (n = 374, 375, 400, 1000);
  - the explicit constants of section 3, exactly in rational arithmetic, j = 0..600 and n = 0..300;
  - the computed values quoted in the entry (section 3.5) and the V1 battery counts (section 2.7);
  - working memory (section 4): tracemalloc peaks, n = 4..12;
  - the DPLL oracle and the instance sizes (section 5): n = 0..10 and n = 0..40.
"""
import importlib.util
import itertools
import math
import random
import sys
import tracemalloc
import unittest
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "3sat-brute-force-vs-schoening"
ENTRY_ID = "3sat-brute-force-vs-schoening"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "proofs_3sat_harness")
BF = _load(ENTRY / "implementations" / "brute_force.py", "proofs_3sat_bf")
SCH = _load(ENTRY / "implementations" / "schoening.py", "proofs_3sat_sch")

getcontext().prec = 60
# ln(10^6), correctly rounded to 60 digits by decimal, then raised by 10^-50: a strict upper bound.
LN_1E6_UP = Fraction(Decimal(10 ** 6).ln()) + Fraction(1, 10 ** 50)
getcontext().prec = 90
LN_1E6_LO = Fraction(Decimal(10 ** 6).ln()) - Fraction(1, 10 ** 80)    # enclosure of width < 10^-70
LN_1E6_HI = Fraction(Decimal(10 ** 6).ln()) + Fraction(1, 10 ** 80)
getcontext().prec = 60


def p_exact(n):
    """p(n) = sum_j C(n, j) 2^-n C(3j, j) (1/3)^(2j) (2/3)^j as an exact rational."""
    return Fraction(sum(math.comb(n, j) * math.comb(3 * j, j) * 2 ** j * 27 ** (n - j) for j in range(n + 1)),
                    2 ** n * 27 ** n)


def q_exact(j):
    """q_j = C(3j, j) (1/3)^(2j) (2/3)^j."""
    return Fraction(math.comb(3 * j, j) * 2 ** j, 27 ** j)


class CountingTuple(tuple):
    """A tuple that counts how often it is iterated (the implementations iterate the clause list once per scan)."""
    iterations = 0

    def __iter__(self):
        CountingTuple.iterations += 1
        return tuple.__iter__(self)


def satisfies(assignment, clauses):
    """assignment: tuple of n bools (x_1..x_n)."""
    return all(any(assignment[abs(l) - 1] == (l > 0) for l in c) for c in clauses)


def first_falsified(assignment, clauses):
    for c in clauses:
        if not any(assignment[abs(l) - 1] == (l > 0) for l in c):
            return c
    return None


def try_success_probabilities(n, clauses):
    """Exact probability that one try of sat_schoening succeeds, for every start assignment.

    Follows the implementation: checks before each of the 3n flips and after the last; a flip takes the first
    falsified clause in input order and flips the variable of a uniformly chosen literal position."""
    states = list(itertools.product((False, True), repeat=n))
    f = {a: Fraction(1) if satisfies(a, clauses) else Fraction(0) for a in states}   # 0 flips left
    for _ in range(3 * n):
        g = {}
        for a in states:
            c = first_falsified(a, clauses)
            if c is None:
                g[a] = Fraction(1)
                continue
            total = Fraction(0)
            for lit in c:
                b = list(a)
                b[abs(lit) - 1] = not b[abs(lit) - 1]
                total += f[tuple(b)]
            g[a] = total / len(c)
        f = g
    return f


def small_satisfiable_formulas():
    """140 seeded satisfiable formulas, n = 1..7: harness instances, planted unique-solution formulas and
    mixed-width formulas with repeated literals."""
    out = []
    for n in range(1, 8):
        rng = random.Random(f"proofs-3sat-coupling|{n}")
        kinds = 0
        while kinds < 20:
            pick = kinds % 4
            if pick == 0:
                inst = H.generate(n, rng)
                clauses = inst[1]
            elif pick == 1 and n >= 3:
                star = tuple(rng.random() < 0.5 for _ in range(n))
                clauses = []
                for c in itertools.combinations(range(1, n + 1), 3):
                    for signs in itertools.product((1, -1), repeat=3):
                        cl = tuple(s * v for s, v in zip(signs, c))
                        if any(star[abs(l) - 1] == (l > 0) for l in cl) and rng.random() < 0.6:
                            clauses.append(cl)
                clauses = tuple(clauses)
            else:
                clauses = []
                for _ in range(rng.randint(1, 3 * n)):
                    width = rng.choice((1, 2, 3, 3))
                    cl = tuple(rng.choice((1, -1)) * rng.randint(1, n) for _ in range(width))   # repeats allowed
                    clauses.append(cl)
                clauses = tuple(clauses)
            sols = [a for a in itertools.product((False, True), repeat=n) if satisfies(a, clauses)]
            if sols:
                out.append((n, clauses, sols))
                kinds += 1
    return out


class BruteForce(unittest.TestCase):
    def test_all_assignments_examined_on_unsatisfiable_formulas(self):
        # PROOFS.md section 1.2: on an unsatisfiable formula all 2^n assignments are examined.
        for n in range(3, 11):
            n_, clauses = H.generate_scaling(n, random.Random(f"proofs-3sat-bf|{n}"))
            wrapped = CountingTuple(clauses)
            CountingTuple.iterations = 0
            self.assertIs(BF.sat_brute_force((n, wrapped)), False)
            self.assertEqual(CountingTuple.iterations, 2 ** n)

    def test_clause_checks_between_one_and_m_per_assignment(self):
        for n in range(3, 10):
            n_, clauses = H.generate_scaling(n, random.Random(f"proofs-3sat-bf2|{n}"))
            counter = [0]

            class Clause(tuple):
                def __iter__(self):
                    counter[0] += 1
                    return tuple.__iter__(self)

            formula = (n, tuple(Clause(c) for c in clauses))
            self.assertIs(BF.sat_brute_force(formula), False)
            self.assertGreaterEqual(counter[0], 2 ** n)
            self.assertLessEqual(counter[0], 2 ** n * len(clauses))


class SchoeningCounts(unittest.TestCase):
    def test_unsatisfiable_scans_flips_draws(self):
        # PROOFS.md sections 2.2 and 4: False on unsatisfiable formulas, after exactly T(n)(3n + 1) scans,
        # 3n T(n) flips (random.choice calls) and n T(n) start draws (random.random calls).
        for n in range(3, 9):
            n_, clauses = H.generate_scaling(n, random.Random(f"proofs-3sat-sch|{n}"))
            wrapped = CountingTuple(clauses)
            CountingTuple.iterations = 0
            random.seed(f"proofs-3sat-sch-run|{n}")
            with mock.patch.object(random, "choice", wraps=random.choice) as ch, \
                    mock.patch.object(random, "random", wraps=random.random) as rr:
                self.assertIs(SCH.sat_schoening((n, wrapped)), False)
            T = SCH.tries_needed(n)
            self.assertEqual(CountingTuple.iterations, 1 + T * (3 * n + 1))   # 1 = the empty-clause test
            self.assertEqual(ch.call_count, 3 * n * T)
            self.assertEqual(rr.call_count, n * T)

    def test_true_only_with_a_satisfying_assignment(self):
        # PROOFS.md section 2.2: True implies satisfiable; unsatisfiable formulas give False.
        for n in range(0, 9):
            for t in range(8):
                inst = H.generate(n, random.Random(f"proofs-3sat-1sided|{n}|{t}"))
                random.seed(f"proofs-3sat-1sided-run|{n}|{t}")
                out = SCH.sat_schoening(inst)
                truth = H._dpll(inst[1], {})
                if out:
                    self.assertTrue(truth)
                if not truth:
                    self.assertIs(out, False)


class Coupling(unittest.TestCase):
    def test_exact_try_success_dominates_q_and_p(self):
        # PROOFS.md section 2.4 (per start, against every solution) and 2.5 (average >= p(n)).
        formulas = small_satisfiable_formulas()
        self.assertEqual(len(formulas), 140)
        for n, clauses, sols in formulas:
            probs = try_success_probabilities(n, clauses)
            for a, pa in probs.items():
                bound = max(q_exact(sum(x != y for x, y in zip(a, s))) for s in sols)
                self.assertGreaterEqual(pa, bound, (n, clauses, a))
            avg = sum(probs.values()) / 2 ** n
            self.assertGreaterEqual(avg, p_exact(n), (n, clauses))

    def test_single_solution_one_literal_flip_probability(self):
        # PROOFS.md section 2.3: a flip in a falsified clause of width <= 3 hits a variable on which the
        # assignment and a fixed solution differ with probability >= 1/3.
        for n, clauses, sols in small_satisfiable_formulas()[:60]:
            for a in itertools.product((False, True), repeat=n):
                c = first_falsified(a, clauses)
                if c is None:
                    continue
                for s in sols:
                    good = sum(1 for lit in c if a[abs(lit) - 1] != s[abs(lit) - 1])
                    self.assertGreaterEqual(Fraction(good, len(c)), Fraction(1, 3))


class RestartBudget(unittest.TestCase):
    def test_implementation_budget_meets_the_error_bound(self):
        # PROOFS.md section 2.6: the implementation's T(n) is at least the exact ceiling ceil(ln(10^6) / p(n)),
        # equal to it for n <= 88 and larger by a relative 10^-12 at most for n <= 373.
        for n in range(374):
            p = p_exact(n)
            lo, hi = math.ceil(LN_1E6_LO / p), math.ceil(LN_1E6_HI / p)
            self.assertEqual(lo, hi, n)                            # the enclosure determines the ceiling
            T = SCH.tries_needed(n)
            self.assertGreaterEqual(T, lo, n)
            self.assertGreaterEqual(p * T, LN_1E6_UP, n)
            self.assertLessEqual(Fraction(T - lo, lo), Fraction(1, 10 ** 12), n)
            if n <= 88:
                self.assertEqual(T, lo, n)

    def test_overflow_boundary(self):
        # PROOFS.md section 2.6: C(3j, j) is float-convertible for j = 373 and not for j = 374, so every n >= 374
        # raises; a formula with an empty clause is answered before T(n) is computed.
        float(math.comb(3 * 373, 373))
        with self.assertRaises(OverflowError):
            float(math.comb(3 * 374, 374))
        for j in range(1, 400):
            self.assertGreater(math.comb(3 * j + 3, j + 1), math.comb(3 * j, j))
        for n in (374, 375, 400, 1000):
            with self.assertRaises(OverflowError):
                SCH.tries_needed(n)
        with self.assertRaises(OverflowError):
            SCH.sat_schoening((400, ((1, 2, 3),)))
        self.assertIs(SCH.sat_schoening((400, ((1, 2, 3), ()))), False)


class Asymptotics(unittest.TestCase):
    def test_g_j_constants(self):
        # PROOFS.md section 3.1: 0.431 <= g_j = q_j 2^j sqrt(j + 1) <= 1, compared through squares.
        lo2 = Fraction(431, 1000) ** 2
        for j in range(601):
            g2 = q_exact(j) ** 2 * 4 ** j * (j + 1)
            self.assertGreaterEqual(g2, lo2, j)
            self.assertLessEqual(g2, 1, j)

    def test_binomial_reciprocal_identity(self):
        # PROOFS.md section 3.3: E[1/(J + 1)] = 3 (1 - (2/3)^(n+1)) / (n + 1) for J ~ Binomial(n, 1/3).
        for n in range(0, 61):
            e = sum(Fraction(math.comb(n, j) * 2 ** (n - j), 3 ** n) / (j + 1) for j in range(n + 1))
            self.assertEqual(e, 3 * (1 - Fraction(2, 3) ** (n + 1)) / (n + 1))

    def test_p_bounds(self):
        # PROOFS.md section 3.4: 0.431 (3/4)^n sqrt(3/(n+3)) <= p(n) <= (3/4)^n sqrt(3/(n+1)), via squares.
        for n in range(301):
            p2 = p_exact(n) ** 2
            base = Fraction(9, 16) ** n
            self.assertLessEqual(p2, base * Fraction(3, n + 1), n)
            self.assertGreaterEqual(p2, Fraction(431, 1000) ** 2 * base * Fraction(3, n + 3), n)


class ComputedValues(unittest.TestCase):
    def test_ratio_and_budget_values(self):
        # PROOFS.md section 3.5 (values quoted in entry.json, README and schoening.py).
        for n in range(14, 21):
            r = float(p_exact(n) * Fraction(4, 3) ** n) * math.sqrt(n)
            self.assertTrue(0.87 <= r <= 0.89, (n, r))
        self.assertEqual([SCH.tries_needed(n) for n in (6, 12, 20)], [196, 1682, 22371])

    def test_v1_battery_composition(self):
        # PROOFS.md section 2.7: the validator's V1 battery has 53 satisfiable and 31 unsatisfiable formulas.
        import json
        entry = json.loads((ENTRY / "entry.json").read_text(encoding="utf-8"))
        th = entry["test_harness"]
        answers = []
        for n in th["v1_sizes"]:
            for trial in range(th["trials"]):
                inst = H.generate(n, random.Random(f"{ENTRY_ID}|v1|{n}|{trial}"))
                answers.append(H._dpll(inst[1], {}))
        self.assertEqual((answers.count(True), answers.count(False)), (53, 31))


class Oracle(unittest.TestCase):
    def test_dpll_against_exhaustive_search(self):
        # PROOFS.md section 5.
        for n in range(0, 11):
            for t in range(10):
                rng = random.Random(f"proofs-3sat-oracle|{n}|{t}")
                if t < 5 or n == 0:
                    clauses = H.generate(n, rng)[1]
                else:
                    clauses = tuple(tuple(rng.choice((1, -1)) * rng.randint(1, n) for _ in range(rng.choice((1, 2, 3))))
                                    for _ in range(rng.randint(1, 4 * n)))
                truth = any(satisfies(a, clauses) for a in itertools.product((False, True), repeat=n))
                self.assertEqual(H._dpll(clauses, {}), truth, (n, clauses))
        for n in range(3, 11):
            clauses = H.generate_scaling(n, random.Random(f"proofs-3sat-oracle-s|{n}"))[1]
            self.assertFalse(any(satisfies(a, clauses) for a in itertools.product((False, True), repeat=n)))

    def test_instance_sizes(self):
        # PROOFS.md section 5: m <= 6n + 8, and 2n <= m for n >= 3.
        for n in range(0, 41):
            sizes = [len(H.generate(n, random.Random(f"proofs-3sat-size|{n}|{t}"))[1]) for t in range(25)]
            if n >= 3:
                sizes.append(len(H.generate_scaling(n, random.Random(f"proofs-3sat-size-s|{n}"))[1]))
            for m in sizes:
                self.assertLessEqual(m, 6 * n + 8, n)
                if n >= 3:
                    self.assertGreaterEqual(m, 2 * n, n)


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

    def test_no_growth_with_the_number_of_assignments(self):
        # PROOFS.md sections 1.3 and 4: O(n + m) memory. The peak above the input stays below 4 KB plus
        # 64 bytes per variable on unsatisfiable formulas n = 4..12 (brute force) and n = 4..8 (Schoening),
        # while the number of assignments grows 2^n-fold.
        for n in range(4, 13):
            f = H.generate_scaling(n, random.Random(f"proofs-3sat-mem|{n}"))
            self.assertLess(self._peak(BF.sat_brute_force, f), 4096 + 64 * n, n)
        for n in range(4, 9):
            f = H.generate_scaling(n, random.Random(f"proofs-3sat-mem|{n}"))
            random.seed(n)
            self.assertLess(self._peak(SCH.sat_schoening, f), 4096 + 64 * n, n)


if __name__ == "__main__":
    unittest.main()
