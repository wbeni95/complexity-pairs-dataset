"""Unit tests for lib/qsim.py (the state-vector simulator behind the T9 entries) and lib/qsearch.py.

Added 2026-10-07. The simulator is the measuring instrument of every quantum query count in the dataset, so
it is tested directly: unitarity (norm preservation), the Hadamard involution, the diffusion operator against
its definition, oracle query counting, the deferred-measurement collapse, and the search subroutines against
the closed forms of Boyer, Brassard, Hoyer & Tapp (1998).

Run:  python -m unittest discover -s tests
"""
import math
import random
import statistics
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib import qsearch  # noqa: E402
from lib.qsim import Oracle, State  # noqa: E402


def norm2(state):
    return sum(abs(a) ** 2 for a in state.amp)


def random_state(n, rng):
    s = State(n)
    s.amp = [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(1 << n)]
    z = math.sqrt(norm2(s))
    s.amp = [a / z for a in s.amp]
    return s


def assert_states_close(test, a, b, places=12):
    test.assertEqual(len(a.amp), len(b.amp))
    for x, y in zip(a.amp, b.amp):
        test.assertAlmostEqual(x.real, y.real, places=places)
        test.assertAlmostEqual(x.imag, y.imag, places=places)


class StateTests(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(20261007)

    def test_hadamard_preserves_norm(self):
        for n in range(1, 7):
            s = random_state(n, self.rng)
            for k in range(n):
                s.h(k)
                self.assertAlmostEqual(norm2(s), 1.0, places=12)

    def test_hadamard_is_an_involution(self):
        for n in range(1, 7):
            s = random_state(n, self.rng)
            original = State(n)
            original.amp = list(s.amp)
            for k in range(n):
                s.h(k)
                s.h(k)
                assert_states_close(self, s, original)
            s.h_all()
            s.h_all()
            assert_states_close(self, s, original)

    def test_uniform_equals_hadamard_on_zero(self):
        for n in range(0, 8):
            a = State(n)
            a.h_all()
            assert_states_close(self, a, State.uniform(n), places=14)

    def test_diffusion_matches_definition(self):
        """reflect_about_uniform must equal H^n (2|0><0| - I) H^n, applied literally."""
        for n in range(1, 6):
            s = random_state(n, self.rng)
            literal = State(n)
            literal.amp = list(s.amp)
            literal.h_all()
            literal.amp = [(a if x == 0 else -a) for x, a in enumerate(literal.amp)]  # 2|0><0| - I
            literal.h_all()
            s.reflect_about_uniform()
            assert_states_close(self, s, literal)
            self.assertAlmostEqual(norm2(s), 1.0, places=12)

    def test_measure_all_collapses(self):
        s = State(3, basis=5)
        self.assertEqual(s.measure_all(self.rng), 5)
        s = State.uniform(4)
        x = s.measure_all(self.rng)
        self.assertEqual(s.amp[x], 1)
        self.assertAlmostEqual(norm2(s), 1.0, places=14)

    def test_measure_all_statistics(self):
        """Uniform superposition on 2 qubits: each outcome close to 1/4 over 8000 shots (4.5 s.e. band)."""
        counts = [0] * 4
        shots = 8000
        for _ in range(shots):
            counts[State.uniform(2).measure_all(self.rng)] += 1
        se = math.sqrt(0.25 * 0.75 / shots)
        for c in counts:
            self.assertLess(abs(c / shots - 0.25), 4.5 * se)


class OracleTests(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(7)

    def test_query_counting(self):
        table = (0, 1, 1, 0, 1, 0, 0, 0)
        o = Oracle(table)
        self.assertEqual(o.queries, 0)
        o(3)
        self.assertEqual(o.queries, 1)
        s = State.uniform(3)
        o.apply_phase(s)
        self.assertEqual(o.queries, 2)
        o.apply_phase_where(s, lambda x, fx: fx == 1)
        self.assertEqual(o.queries, 4, "a phase on a derived predicate costs two queries (compute + uncompute)")
        o.apply_xor_and_measure_output(State.uniform(3), self.rng)
        self.assertEqual(o.queries, 5)

    def test_phase_oracles_preserve_norm_and_agree(self):
        table = tuple(self.rng.randrange(2) for _ in range(16))
        a, b = random_state(4, self.rng), State(4)
        b.amp = list(a.amp)
        Oracle(table).apply_phase(a)
        Oracle(table).apply_phase_where(b, lambda x, fx: fx & 1)
        assert_states_close(self, a, b)
        self.assertAlmostEqual(norm2(a), 1.0, places=12)

    def test_phase_where_sees_input_and_value(self):
        table = (5, 3, 9, 1)
        s = State.uniform(2)
        Oracle(table).apply_phase_where(s, lambda x, fx: fx < 5 and x != 3)  # marks only x = 1
        self.assertEqual([round(a.real * 2) for a in s.amp], [1, -1, 1, 1])

    def test_deferred_measurement_collapse(self):
        """U_f then measuring the output register: P(v) = sum over f^-1(v) of |a_x|^2, and the input register
        collapses to the renormalised amplitudes on f^-1(v)."""
        table = (4, 7, 4, 2, 7, 2, 9, 9)  # 2-to-1
        for trial in range(200):
            s = random_state(3, self.rng)
            before = list(s.amp)
            o = Oracle(table)
            out, v = o.apply_xor_and_measure_output(s, self.rng)
            self.assertIn(v, set(table))
            weight = sum(abs(before[x]) ** 2 for x in range(8) if table[x] == v)
            for x in range(8):
                expected = before[x] / math.sqrt(weight) if table[x] == v else 0
                self.assertAlmostEqual(out.amp[x].real, complex(expected).real, places=12)
                self.assertAlmostEqual(out.amp[x].imag, complex(expected).imag, places=12)
            self.assertAlmostEqual(norm2(out), 1.0, places=12)

    def test_deferred_measurement_statistics(self):
        """On the uniform superposition of a 2-to-1 function each output value has probability 2/N."""
        table = (0, 1, 2, 3, 0, 1, 2, 3)
        counts = {}
        shots = 8000
        for _ in range(shots):
            _, v = Oracle(table).apply_xor_and_measure_output(State.uniform(3), self.rng)
            counts[v] = counts.get(v, 0) + 1
        se = math.sqrt(0.25 * 0.75 / shots)
        for v in range(4):
            self.assertLess(abs(counts[v] / shots - 0.25), 4.5 * se)

    def test_bernstein_vazirani_is_exact(self):
        for n in range(1, 7):
            for s in range(1 << n):
                table = tuple(bin(s & x).count("1") & 1 for x in range(1 << n))
                st = State(n)
                st.h_all()
                Oracle(table).apply_phase(st)
                st.h_all()
                self.assertAlmostEqual(abs(st.amp[s]) ** 2, 1.0, places=12)


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(42)

    def test_grover_amplitudes_match_closed_form(self):
        """After j iterations the success probability is sin^2((2j+1) theta) (BBHT eq. 3)."""
        for n in (3, 5):
            N = 1 << n
            for t in (1, 2, 3, N // 4):
                marked = set(range(t))
                o = Oracle(tuple(1 if x in marked else 0 for x in range(N)))
                s = State.uniform(n)
                for j in range(0, 8):
                    p = sum(abs(s.amp[x]) ** 2 for x in marked)
                    self.assertAlmostEqual(p, qsearch.success_probability(N, t, j), places=10)
                    qsearch.grover_iteration(s, o.apply_phase)
                    self.assertAlmostEqual(norm2(s), 1.0, places=10)

    def test_lemma2_closed_form(self):
        for N in (8, 64, 1000):
            for t in (1, 3, N // 5, N // 2, N - 1):
                for M in range(1, 40):
                    direct = sum(qsearch.success_probability(N, t, j) for j in range(M)) / M
                    self.assertAlmostEqual(direct, qsearch.bbht_lemma2(N, t, M), places=10)

    def test_known_count_failure_bound(self):
        """BBHT section 3: failure probability after floor(pi/4theta) iterations is at most t/N."""
        for N in (4, 16, 64, 1024, 4096):
            for t in range(1, N):
                if t > 40 and t % 37:
                    continue
                m = qsearch.known_count_iterations(N, t)
                self.assertLessEqual(1 - qsearch.success_probability(N, t, m), t / N + 1e-12)

    def test_exponential_expectation_respects_theorem3(self):
        for N in (16, 64, 256, 1024, 2 ** 14):
            for t in sorted({1, 2, 3, 5, N // 16, N // 4, (3 * N) // 4}):
                if t < 1:
                    continue
                e = qsearch.expected_cost_exponential(N, t, 1, 0)
                self.assertLessEqual(e, qsearch.bbht_theorem3_bound(N, t))
                self.assertGreaterEqual(e, 0)

    def test_simulated_costs_match_exact_expectations(self):
        """Mean simulated queries of both searches agree with the exact expectations (|z| < 4)."""
        n, t = 6, 3
        N = 1 << n
        marked = set(self.rng.sample(range(N), t))
        table = tuple(self.rng.randrange(100) for _ in range(N))

        def run(kind):
            o = Oracle(table)
            phase = lambda st: o.apply_phase_where(st, lambda x, fx: x in marked)  # noqa: E731
            check = lambda x: (o(x), x in marked)[1]  # noqa: E731
            if kind == "known":
                x, _ = qsearch.search_known_count(n, phase, check, t, self.rng)
            else:
                x, _, interrupted = qsearch.exponential_search(n, phase, check, self.rng)
                self.assertFalse(interrupted)
            self.assertIn(x, marked)
            return o.queries

        for kind, exact in (("known", qsearch.expected_cost_known(N, t, 2, 1)),
                            ("exponential", qsearch.expected_cost_exponential(N, t, 2, 1))):
            samples = [run(kind) for _ in range(3000)]
            se = statistics.stdev(samples) / math.sqrt(len(samples))
            z = (statistics.fmean(samples) - exact) / se
            self.assertLess(abs(z), 4, f"{kind}: mean {statistics.fmean(samples):.3f} vs exact {exact:.3f}")

    def test_budget_interrupts(self):
        n = 5
        o = Oracle(tuple(range(32)))
        phase = lambda st: o.apply_phase_where(st, lambda x, fx: False)  # noqa: E731
        x, iterations, interrupted = qsearch.exponential_search(n, phase, lambda x: False, self.rng, budget=17)
        self.assertIsNone(x)
        self.assertTrue(interrupted)
        self.assertLessEqual(iterations, 17)
        self.assertEqual(o.queries, 2 * iterations)


if __name__ == "__main__":
    unittest.main()
