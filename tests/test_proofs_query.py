"""Checks of the proofs in the PROOFS.md files of the query-model entries (2026-10-07).

Entries: grover-search, bernstein-vazirani, deutsch-jozsa, simon, collision-problem (all "-classical-vs-quantum"),
minimum-finding-classical-vs-quantum and nand-tree-evaluation-deterministic-vs-randomized. Each test class re-runs the
computable facts of one entry's proofs on stated finite ranges; the proofs cover the general statements, and each
PROOFS.md names the test that checks each step.

Three kinds of checks:
  - exhaustive minimax over all deterministic adaptive query strategies on small explicit input families (the
    lower bounds), with QueryGame below;
  - the UNCHANGED implementations run with their random choices replaced by every possible outcome in turn (the
    module's `random` is swapped for a stand-in while the test runs; no file is modified), giving exact
    distributions and expectations;
  - the lib/qsim.py operators against the closed forms of the proofs (the simulation), and the formulas of the
    proofs evaluated on stated ranges.
All inputs come from fixed seeds or are enumerated, so every run is deterministic.

Run:  python -m unittest tests.test_proofs_query     (or discover -s tests)
"""
from __future__ import annotations

import decimal
import functools
import inspect
import itertools
import math
import random
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib import qsearch  # noqa: E402
from lib.qsim import Oracle, State  # noqa: E402
from tools.validate import load_callable, load_module  # noqa: E402

PAIRS = ROOT / "pairs"
GROVER = PAIRS / "grover-search-classical-vs-quantum"
BV = PAIRS / "bernstein-vazirani-classical-vs-quantum"
DJ = PAIRS / "deutsch-jozsa-classical-vs-quantum"
SIMON = PAIRS / "simon-classical-vs-quantum"
COLL = PAIRS / "collision-problem-classical-vs-quantum"
MINF = PAIRS / "minimum-finding-classical-vs-quantum"
NAND = PAIRS / "nand-tree-evaluation-deterministic-vs-randomized"


# ------------------------------------------------------------------------------------------------------------------
# Shared tools
# ------------------------------------------------------------------------------------------------------------------

class QueryGame:
    """Deterministic adaptive query strategies on an explicit finite family of inputs (tuples of values).

    correct(i) is the set of acceptable outputs for input i. A strategy queries positions; the state is the set of
    inputs consistent with the answers so far. Querying a position on which all consistent inputs agree gives no
    information, so only informative positions are tried (this loses nothing)."""

    def __init__(self, inputs, correct):
        self.inputs = [tuple(x) for x in inputs]
        self.correct = [frozenset(correct(i)) for i in range(len(self.inputs))]
        self.outputs = sorted(set().union(*self.correct), key=repr)
        self.npos = len(self.inputs[0]) if self.inputs else 0
        self._count, self._depth, self._total = {}, {}, {}

    def _split(self, S, pos):
        parts = {}
        for i in S:
            parts.setdefault(self.inputs[i][pos], []).append(i)
        return [frozenset(p) for p in parts.values()]

    def _informative(self, S):
        for pos in range(self.npos):
            if len({self.inputs[i][pos] for i in S}) > 1:
                yield pos

    def _stop_count(self, S):
        return max(sum(1 for i in S if o in self.correct[i]) for o in self.outputs)

    def best_count(self, S, q):
        """Largest number of inputs of S answered correctly by a strategy with at most q more queries."""
        key = (S, q)
        if key not in self._count:
            best = self._stop_count(S)
            if q > 0 and best < len(S):
                for pos in self._informative(S):
                    best = max(best, sum(self.best_count(P, q - 1) for P in self._split(S, pos)))
            self._count[key] = best
        return self._count[key]

    def certain(self, S):
        return any(all(o in self.correct[i] for i in S) for o in self.outputs)

    def worst_depth(self, S):
        """Smallest worst-case number of queries of a strategy that is always correct on S."""
        if S not in self._depth:
            if self.certain(S):
                self._depth[S] = 0
            else:
                self._depth[S] = min(1 + max(self.worst_depth(P) for P in self._split(S, pos))
                                     for pos in self._informative(S))
        return self._depth[S]

    def min_total(self, S):
        """Smallest total number of queries over the inputs of S of an always-correct strategy."""
        if S not in self._total:
            if self.certain(S):
                self._total[S] = 0
            else:
                self._total[S] = min(len(S) + sum(self.min_total(P) for P in self._split(S, pos))
                                     for pos in self._informative(S))
        return self._total[S]

    def all(self):
        return frozenset(range(len(self.inputs)))


class _PermStub:
    """Stand-in for the `random` module of an implementation: shuffle() writes a prescribed permutation."""

    def __init__(self, perm):
        self.perm = perm

    def shuffle(self, lst):
        lst[:] = [lst[i] for i in self.perm]


class _SeqStub:
    """Stand-in for `random`: randrange() and getrandbits() return prescribed values in order."""

    class NeedMore(Exception):
        pass

    def __init__(self, values):
        self.values = list(values)
        self.used = 0

    def _next(self):
        if self.used >= len(self.values):
            raise _SeqStub.NeedMore
        v = self.values[self.used]
        self.used += 1
        return v

    def randrange(self, *args):
        return self._next()

    def getrandbits(self, k):
        return self._next()


class swapped:
    """Temporarily replace names in a function's module globals."""

    def __init__(self, fn, **names):
        self.g, self.names, self.saved = fn.__globals__, names, {}

    def __enter__(self):
        for k, v in self.names.items():
            self.saved[k] = self.g[k]
            self.g[k] = v

    def __exit__(self, *exc):
        self.g.update(self.saved)


def locals_at_return(fn, call):
    """Run call() and return the local variables of fn's frame at its (last) return."""
    code, seen = fn.__code__, {}

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is code:
            seen.update(frame.f_locals)

    old = sys.getprofile()
    sys.setprofile(prof)
    try:
        out = call()
    finally:
        sys.setprofile(old)
    return out, seen


def max_depth(code_name, call):
    """Largest number of simultaneously active frames of functions named code_name during call()."""
    state = {"d": 0, "m": 0}

    def prof(frame, event, arg):
        if frame.f_code.co_name == code_name:
            if event == "call":
                state["d"] += 1
                state["m"] = max(state["m"], state["d"])
            elif event == "return":
                state["d"] -= 1

    old = sys.getprofile()
    sys.setprofile(prof)
    try:
        call()
    finally:
        sys.setprofile(old)
    return state["m"]


def qubits_created(fn, call):
    """Numbers of qubits of every State created through fn's module name `State` during call()."""
    sizes = []

    class Recording(State):
        def __init__(self, num_qubits, basis=0):
            sizes.append(num_qubits)
            super().__init__(num_qubits, basis)

    with swapped(fn, State=Recording):
        call()
    return sizes


def parity(v):
    return bin(v).count("1") & 1


def perfect_matchings(points):
    if not points:
        yield ()
        return
    a, rest = points[0], points[1:]
    for i, b in enumerate(rest):
        for m in perfect_matchings(rest[:i] + rest[i + 1:]):
            yield ((a, b),) + m


def partner_array(matching, N):
    p = [None] * N
    for a, b in matching:
        p[a], p[b] = b, a
    return tuple(p)


# k = floor(pi sqrt(N)/4) minus the Grover code's floating-point k, for n = 110..139 (0 for n <= 109).
CODE_K_GAPS = (1, 1, 2, 2, 4, 5, 8, 10, 17, 20, 35, 41, 70, 83, 141, 167, 282, 334, 564, 669, 1129, 1339, 2259,
               2678, 4518, 5357, 9036, 10715, 18072, 21431)


def _negligible(term):
    return term == 0 or term.adjusted() < -decimal.getcontext().prec - 5


def hp_pi():
    """pi by Machin's formula, 16 atan(1/5) - 4 atan(1/239), in the current decimal precision."""
    def atan_inv(m):
        x = decimal.Decimal(1) / m
        total, power, k = decimal.Decimal(0), x, 0
        while True:
            term = power / (2 * k + 1)
            if _negligible(term):
                return total
            total += -term if k % 2 else term
            power *= x * x
            k += 1
    return 16 * atan_inv(5) - 4 * atan_inv(239)


def hp_sin(x):
    total, term, k = decimal.Decimal(0), x, 0
    while not _negligible(term):
        total += term
        k += 1
        term = -term * x * x / ((2 * k) * (2 * k + 1))
    return total


def hp_asin(x):
    """arcsin by its Taylor series (|x| <= 1/sqrt 2 here)."""
    total, coeff, power, k = decimal.Decimal(0), decimal.Decimal(1), x, 0
    while True:
        term = coeff * power / (2 * k + 1)
        if _negligible(term):
            return total
        total += term
        coeff = coeff * (2 * k + 1) / (2 * k + 2)
        power *= x * x
        k += 1


# ------------------------------------------------------------------------------------------------------------------
# Grover (pairs/grover-search-classical-vs-quantum/PROOFS.md)
# ------------------------------------------------------------------------------------------------------------------

class GroverProofChecks(unittest.TestCase):
    """PROOFS.md §2-§7 of the Grover entry."""

    @classmethod
    def setUpClass(cls):
        cls.classical = staticmethod(load_callable(GROVER, "implementations/classical.py:search_classical"))
        cls.grover = staticmethod(load_callable(GROVER, "implementations/grover.py:search_grover"))

    def test_classical_query_count_is_uniform(self):
        for n in range(0, 4):
            N = 1 << n
            for marked in range(N):
                table = tuple(1 if x == marked else 0 for x in range(N))
                counts = {}
                for perm in itertools.permutations(range(N)):
                    with swapped(self.classical, random=_PermStub(perm)):
                        x, q = self.classical((n, table))
                    self.assertEqual(x, marked)
                    counts[q] = counts.get(q, 0) + 1
                self.assertEqual(counts, {j: math.factorial(N - 1) for j in range(1, N + 1)})

    def test_simulated_state_matches_lemma_g(self):
        rng = random.Random(1)
        for n in range(0, 11):
            N = 1 << n
            for t in sorted({1, 2, 3, N // 4}):
                if not 1 <= t <= N:
                    continue
                marked = set(rng.sample(range(N), t))
                oracle = Oracle(tuple(1 if x in marked else 0 for x in range(N)))
                theta = math.asin(math.sqrt(t / N))
                state = State(n)
                state.h_all()
                for j in range(9):
                    s_amp = math.sin((2 * j + 1) * theta) / math.sqrt(t)
                    c_amp = math.cos((2 * j + 1) * theta) / math.sqrt(N - t) if t < N else 0.0
                    for x in range(N):
                        want = s_amp if x in marked else c_amp
                        self.assertAlmostEqual(state.amp[x].real, want, delta=1e-9)
                        self.assertAlmostEqual(state.amp[x].imag, 0.0, delta=1e-9)
                    oracle.apply_phase(state)
                    state.reflect_about_uniform()
        # the success probability after the code's k iterations (t = 1)
        for n in range(0, 11):
            N = 1 << n
            k = math.floor(math.pi / 4 * math.sqrt(N))
            oracle = Oracle(tuple(1 if x == 0 else 0 for x in range(N)))
            state = State(n)
            state.h_all()
            for _ in range(k):
                oracle.apply_phase(state)
                state.reflect_about_uniform()
            p = math.sin((2 * k + 1) * math.asin(1 / math.sqrt(N))) ** 2
            self.assertAlmostEqual(abs(state.amp[0]) ** 2, p, delta=1e-9)

    def test_known_count_corollary(self):
        for n in range(1, 13):
            N = 1 << n
            for t in range(1, N + 1):
                theta = math.asin(math.sqrt(t / N))
                m = math.floor(math.pi / (4 * theta) + 1e-12)
                delta = (2 * m + 1) * theta - math.pi / 2
                self.assertGreater(delta, -theta - 1e-12)
                self.assertLessEqual(delta, theta + 1e-12)
                self.assertLessEqual(math.cos((2 * m + 1) * theta) ** 2, t / N + 1e-12)

    def test_success_probability_and_expectation(self):
        """PROOFS §4 (c), (d) in 120-digit decimal arithmetic, k = floor(pi sqrt(N)/4) exactly, n = 0..200.

        Double precision is not enough here: 1 - p is below 1e-16 from n = 53 on. pi comes from Machin's formula,
        arcsin and sin from their Taylor series, k from an integer square root with pi enclosed between two
        rationals; the code's floating-point k is compared with the exact one: equal for n <= 109, and below it by
        exactly CODE_K_GAPS for n = 110..139."""
        D = decimal.Decimal
        PI_LO, PI_DEN = 314159265358979323846264338327950288419716939937510, 10 ** 50
        with decimal.localcontext() as lc:
            lc.prec = 120
            pi = hp_pi()
            for n in range(0, 201):
                N = 1 << n
                k = math.isqrt(PI_LO ** 2 * N // (16 * PI_DEN ** 2))
                self.assertEqual(k, math.isqrt((PI_LO + 1) ** 2 * N // (16 * PI_DEN ** 2)))  # floor determined
                code_k = math.floor(math.pi / 4 * math.sqrt(N))
                if n <= 109:
                    self.assertEqual(code_k, k)
                elif n <= 139:
                    self.assertEqual(k - code_k, CODE_K_GAPS[n - 110], n)
                s = D(N).sqrt()
                theta = pi / 2 if N == 1 else hp_asin(1 / s)
                delta = (2 * k + 1) * theta - pi / 2
                fail = hp_sin(delta) ** 2  # 1 - p = cos^2((2k+1) theta) = sin^2(delta)
                p = 1 - fail
                if N >= 2:
                    self.assertLessEqual(fail, (1 + pi / (4 * D(N - 1).sqrt())) ** 2 / (N - 1))
                if N >= 16:
                    self.assertLessEqual(fail, D("1.4468") / (N - 1))
                self.assertGreaterEqual(p, D("0.5") - D(10) ** -100)
                e = (k + 1) / p
                base = pi * s / 4
                self.assertGreater(e, base)
                self.assertLess(e, base + (D("1.45") if n >= 4 else D("2.9")))
                self.assertLess(e - k, D("3.9"))
            self.assertLess((1 + pi / (4 * D(15).sqrt())) ** 2, D("1.4468"))
            self.assertLess((pi + 1) / 15, D("0.2762"))
            self.assertLess(D("0.2762") * D("1.4468") / D("0.9") + 1, D("1.45"))

    def test_classical_lower_bound_by_exhaustion(self):
        for N in range(1, 7):
            game = QueryGame([tuple(1 if x == m else 0 for x in range(N)) for m in range(N)],
                             lambda i: {i})
            for q in range(0, N + 1):
                self.assertEqual(game.best_count(game.all(), q), min(N, q + 1))
            self.assertEqual(game.min_total(game.all()), sum(range(1, N)) + N - 1)

    def test_hybrid_inequality(self):
        rng = random.Random(20261007)

        def rand_unitary(d):
            cols = []
            for _ in range(d):
                v = [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(d)]
                for c in cols:
                    ip = sum(a.conjugate() * b for a, b in zip(c, v))
                    v = [b - ip * a for a, b in zip(c, v)]
                nrm = math.sqrt(sum(abs(b) ** 2 for b in v))
                cols.append([b / nrm for b in v])
            return [[cols[j][i] for j in range(d)] for i in range(d)]

        def matvec(M, v):
            return [sum(a * b for a, b in zip(row, v)) for row in M]

        W = 2
        for N in (4, 8):
            d = N * W
            for T in (1, 2, 3):
                for _ in range(20):
                    Us = [rand_unitary(d) for _ in range(T + 1)]
                    V = [rand_unitary(W), rand_unitary(W)]

                    def oracle(F, v):
                        out = []
                        for i in range(N):
                            out += matvec(V[F[i]], v[i * W:(i + 1) * W])
                        return out

                    def run(F):
                        v = [1 + 0j] + [0j] * (d - 1)
                        v = matvec(Us[0], v)
                        for s in range(1, T + 1):
                            v = matvec(Us[s], oracle(F, v))
                        return v

                    ref = run([0] * N)
                    total = 0.0
                    for x in range(N):
                        psi = run([1 if i == x else 0 for i in range(N)])
                        total += math.sqrt(sum(abs(a - b) ** 2 for a, b in zip(psi, ref)))
                    self.assertLessEqual(total, 2 * T * math.sqrt(N) + 1e-9)
        # Grover's own iterations, reference oracle = identity (all-zero table): psi_ref = u.
        for n in range(2, 9):
            N = 1 << n
            k = math.floor(math.pi / 4 * math.sqrt(N))
            total = 0.0
            for x in range(N):
                st = State.uniform(n)
                o = Oracle(tuple(1 if y == x else 0 for y in range(N)))
                for _ in range(k):
                    o.apply_phase(st)
                    st.reflect_about_uniform()
                u = 1 / math.sqrt(N)
                total += math.sqrt(sum(abs(a - u) ** 2 for a in st.amp))
            self.assertLessEqual(total, 2 * k * math.sqrt(N) + 1e-9)

    def test_space(self):
        for n in range(1, 9):
            N = 1 << n
            table = tuple(1 if x == N - 1 else 0 for x in range(N))
            random.seed(n)
            sizes = qubits_created(self.grover, lambda: self.grover((n, table)))
            self.assertTrue(sizes and all(s == n for s in sizes))
        for n in range(0, 11):
            N = 1 << n
            table = tuple(1 if x == 0 else 0 for x in range(N))
            random.seed(n)
            _, loc = locals_at_return(self.classical, lambda: self.classical((n, table)))
            self.assertEqual(len(loc["order"]), N)


# ------------------------------------------------------------------------------------------------------------------
# Bernstein-Vazirani
# ------------------------------------------------------------------------------------------------------------------

class BernsteinVaziraniProofChecks(unittest.TestCase):
    """PROOFS.md §3-§5 of the Bernstein-Vazirani entry."""

    @classmethod
    def setUpClass(cls):
        cls.classical = staticmethod(load_callable(BV, "implementations/classical.py:bv_classical"))
        cls.quantum = staticmethod(load_callable(BV, "implementations/quantum.py:bv_quantum"))

    def test_quantum_state_is_exactly_s(self):
        for n in range(0, 9):
            N = 1 << n
            for s in range(N):
                table = tuple(parity(s & x) for x in range(N))
                st = State(n)
                st.h_all()
                Oracle(table).apply_phase(st)
                st.h_all()
                self.assertAlmostEqual(abs(st.amp[s]) ** 2, 1.0, delta=1e-12)

    def test_classical_lower_bound_by_exhaustion(self):
        for n in range(1, 4):
            N = 1 << n
            game = QueryGame([tuple(parity(s & x) for x in range(N)) for s in range(N)], lambda i: {i})
            for q in range(0, n + 1):
                self.assertEqual(game.best_count(game.all(), q), 1 << q)

    def test_space(self):
        for n in range(0, 9):
            N = 1 << n
            table = tuple(parity((N - 1) & x) for x in range(N))
            sizes = qubits_created(self.quantum, lambda: self.quantum((n, table)))
            self.assertEqual(sizes, [n])
        for n in range(0, 13):
            N = 1 << n
            s = (0b1011011011011 % N) if N > 1 else 0
            table = tuple(parity(s & x) for x in range(N))
            out, _ = self.classical((n, table))
            self.assertEqual(out, s)
            self.assertLess(out, N)


# ------------------------------------------------------------------------------------------------------------------
# Deutsch-Jozsa
# ------------------------------------------------------------------------------------------------------------------

def promise_inputs(n):
    N = 1 << n
    out = [tuple([0] * N), tuple([1] * N)]
    for ones in itertools.combinations(range(N), N // 2):
        s = set(ones)
        out.append(tuple(1 if x in s else 0 for x in range(N)))
    return out


class DeutschJozsaProofChecks(unittest.TestCase):
    """PROOFS.md §4-§7 of the Deutsch-Jozsa entry."""

    @classmethod
    def setUpClass(cls):
        cls.det = staticmethod(load_callable(DJ, "implementations/classical.py:dj_classical"))
        cls.rnd = staticmethod(load_callable(DJ, "implementations/randomized.py:dj_randomized"))
        cls.qu = staticmethod(load_callable(DJ, "implementations/quantum.py:dj_quantum"))

    def _p0(self, n, table):
        st = State(n)
        st.h_all()
        Oracle(table).apply_phase(st)
        st.h_all()
        return abs(st.amp[0]) ** 2

    def test_quantum_is_exact(self):
        for n in range(1, 4):
            for table in promise_inputs(n):
                want = 1.0 if len(set(table)) == 1 else 0.0
                self.assertAlmostEqual(self._p0(n, table), want, delta=1e-12)
        rng = random.Random(5)
        for n in range(4, 9):
            N = 1 << n
            for _ in range(20):
                vals = [0] * (N // 2) + [1] * (N // 2)
                rng.shuffle(vals)
                self.assertAlmostEqual(self._p0(n, tuple(vals)), 0.0, delta=1e-12)

    def test_randomized_error_exact(self):
        for n, kmax in ((2, 4), (3, 3)):
            N = 1 << n
            for table in promise_inputs(n):
                constant = len(set(table)) == 1
                for k in range(1, kmax + 1):
                    wrong = 0
                    for pts in itertools.product(range(N), repeat=k):
                        with swapped(self.rnd, random=_SeqStub(pts), K=k):
                            ans, q = self.rnd((n, table))
                        self.assertEqual(q, k)
                        wrong += ans != ("constant" if constant else "balanced")
                    rate = F(wrong, N ** k)
                    self.assertEqual(rate, 0 if constant else F(2, 2 ** k))

    def test_average_on_balanced_inputs(self):
        for n in range(1, 5):
            N = 1 << n
            total = cnt = 0
            for table in promise_inputs(n)[2:]:
                ans, q = self.det((n, table))
                self.assertEqual(ans, "balanced")
                total += q
                cnt += 1
            self.assertEqual(F(total, cnt), 3 - F(4, N + 2))
        for n in range(1, 13):
            N = 1 << n
            e = 1
            for j in range(1, N // 2 + 1):
                pr = 2 * math.prod(F(N // 2 - i, N - i) for i in range(j))
                self.assertLessEqual(pr, F(2, 2 ** j))
                e += pr
            self.assertEqual(e, 3 - F(4, N + 2))

    def test_exact_lower_bound_by_exhaustion(self):
        for n in range(1, 4):
            N = 1 << n
            inputs = promise_inputs(n)
            game = QueryGame(inputs, lambda i: {"constant" if len(set(inputs[i])) == 1 else "balanced"})
            self.assertEqual(game.worst_depth(game.all()), (1 << (n - 1)) + 1)
            smallest = min(len(Q) for r in range(N + 1) for Q in itertools.combinations(range(N), r)
                           if not any(len({t[x] for x in Q}) <= 1 for t in inputs[2:]))
            self.assertEqual(smallest, (1 << (n - 1)) + 1)

    def test_space(self):
        for n in range(1, 9):
            N = 1 << n
            sizes = qubits_created(self.qu, lambda: self.qu((n, tuple([0] * N))))
            self.assertEqual(sizes, [n])


# ------------------------------------------------------------------------------------------------------------------
# Simon
# ------------------------------------------------------------------------------------------------------------------

def simon_table(n, s, labels):
    return tuple(labels[min(x, x ^ s)] for x in range(1 << n))


def birthday_law(N, q):
    return math.prod(F(N - 2 * i, N - i) for i in range(q))


class SimonProofChecks(unittest.TestCase):
    """PROOFS.md §2-§6 of the Simon entry."""

    @classmethod
    def setUpClass(cls):
        cls.classical = staticmethod(load_callable(SIMON, "implementations/classical.py:simon_classical"))
        cls.quantum = staticmethod(load_callable(SIMON, "implementations/quantum.py:simon_quantum"))

    def test_classical_law_by_enumeration(self):
        for n in range(1, 4):
            N = 1 << n
            for s in (range(1, N) if n <= 2 else (1, 6)):
                table = simon_table(n, s, list(range(N)))
                counts = {}
                perms = list(itertools.permutations(range(N)))
                for perm in perms:
                    with swapped(self.classical, random=_PermStub(perm)):
                        ans, q = self.classical((n, table))
                    self.assertEqual(ans, s)
                    counts[q] = counts.get(q, 0) + 1
                for q in range(0, N // 2 + 2):
                    tail = F(sum(c for qq, c in counts.items() if qq > q), len(perms))
                    self.assertEqual(tail, birthday_law(N, q))

    def test_round_distribution_in_simulation(self):
        rng = random.Random(11)
        for n in range(1, 7):
            N = 1 << n
            for s in range(1, N):
                for _ in range(3):
                    labels = list(range(N))
                    rng.shuffle(labels)
                    oracle = Oracle(simon_table(n, s, labels))
                    st = State(n)
                    st.h_all()
                    st, _v = oracle.apply_xor_and_measure_output(st, rng)
                    st.h_all()
                    for y in range(N):
                        want = 2 / N if parity(y & s) == 0 else 0.0
                        self.assertAlmostEqual(abs(st.amp[y]) ** 2, want, delta=1e-12)

    def test_post_processing(self):
        fn = self.quantum
        src, start = inspect.getsourcelines(fn)
        xor_lines = {start + i for i, line in enumerate(src) if "^= row" in line or "rows[q] ^= y" in line}
        self.assertEqual(len(xor_lines), 2)
        rng = random.Random(3)

        for n in range(1, 7):
            N = 1 << n
            for s in range(1, N):
                perp = [y for y in range(N) if parity(y & s) == 0]
                for _ in range(30):
                    seq = [rng.choice(perp) for _ in range(200)]
                    feed = iter(seq)
                    created = []

                    class FakeState:
                        def __init__(self, num_qubits, basis=0):
                            created.append(num_qubits)

                        def h_all(self):
                            pass

                        def measure_all(self, rng_):
                            return next(feed)

                    class FakeOracle:
                        def __init__(self, table):
                            self.queries = 0

                        def apply_xor_and_measure_output(self, state, rng_):
                            self.queries += 1
                            return state, 0

                    xors = {"n": 0}
                    code = fn.__code__

                    def tracer(frame, event, arg):
                        if frame.f_code is code:
                            def local(fr, ev, a):
                                if ev == "line" and fr.f_lineno in xor_lines:
                                    xors["n"] += 1
                                return local
                            return local
                        return None

                    with swapped(fn, State=FakeState, Oracle=FakeOracle):
                        old = sys.gettrace()
                        sys.settrace(tracer)
                        try:
                            ans, q = fn((n, None))
                        finally:
                            sys.settrace(old)
                    self.assertEqual(ans, s)
                    # rounds = first index at which the prefix of seq has rank n - 1
                    basis, rank, need = {}, 0, 0
                    for i, y in enumerate(seq):
                        if rank == n - 1:
                            break
                        for b in sorted(basis, reverse=True):
                            if y >> b & 1:
                                y ^= basis[b]
                        if y:
                            basis[y.bit_length() - 1] = y
                            rank += 1
                        need = i + 1
                    if n == 1:
                        need = 0
                    self.assertEqual(q, need)
                    self.assertEqual(len(created), need)
                    self.assertLessEqual(xors["n"], 2 * (n - 1) * max(need, 1))

    def test_expected_rounds(self):
        # every subspace V of s-perp: P(uniform y in s-perp lies outside V) = 1 - 2^(dim V - n + 1)
        for n in range(1, 6):
            N = 1 << n
            for s in range(1, N):
                perp = [y for y in range(N) if parity(y & s) == 0]
                spaces, frontier = {frozenset([0])}, [frozenset([0])]
                while frontier:
                    nxt = []
                    for V in frontier:
                        for y in perp:
                            if y not in V:
                                W = frozenset(V | {v ^ y for v in V})
                                if W not in spaces:
                                    spaces.add(W)
                                    nxt.append(W)
                    frontier = nxt
                for V in spaces:
                    r = len(V).bit_length() - 1
                    outside = F(sum(1 for y in perp if y not in V), len(perp))
                    self.assertEqual(outside, 1 - F(2 ** r, 2 ** (n - 1)))
        for n in range(1, 31):
            e = sum(1 / (1 - F(1, 2 ** j)) for j in range(1, n))
            self.assertEqual(e, n - 1 + sum(F(1, 2 ** j - 1) for j in range(1, n)))
        tail_bound = sum(F(1, 2 ** j - 1) for j in range(1, 41)) + F(1, 2 ** 39)
        self.assertLess(tail_bound, F(16067, 10000))
        for n in range(1, 65):
            e = n - 1 + sum(F(1, 2 ** j - 1) for j in range(1, n))
            self.assertLess(e, n + F(6067, 10000))

    def test_posterior_lemma_by_enumeration(self):
        n, N = 2, 4
        funcs = []
        for s in range(1, N):
            reps = sorted({min(x, x ^ s) for x in range(N)})
            for labels in itertools.permutations(range(N), len(reps)):
                lab = dict(zip(reps, labels))
                funcs.append((s, tuple(lab[min(x, x ^ s)] for x in range(N))))
        self.assertEqual(len(funcs), 36)
        for r in range(0, 4):
            for pts in itertools.permutations(range(N), r):
                groups = {}
                for s, f in funcs:
                    groups.setdefault(tuple(f[x] for x in pts), []).append(s)
                D = {a ^ b for a, b in itertools.combinations(pts, 2)}
                S = [s for s in range(1, N) if s not in D]
                for answers, ss in groups.items():
                    if len(set(answers)) < len(answers):
                        continue
                    hist = {s: ss.count(s) for s in set(ss)}
                    self.assertEqual(set(hist), set(S))
                    self.assertEqual(len(set(hist.values())), 1)
                    for x in range(N):
                        if x in pts:
                            continue
                        hit = sum(1 for s in S if any(x ^ a == s for a in pts))
                        coll = sum(1 for s, f in funcs if tuple(f[y] for y in pts) == answers
                                   and f[x] in answers)
                        self.assertEqual(F(coll, len(ss)), F(hit, len(S)))

    def _pattern_optimum(self, n, q):
        N, M = 1 << n, (1 << n) - 1
        memo = {}

        def S_of(Q):
            D = {a ^ b for a, b in itertools.combinations(Q, 2)}
            return frozenset(s for s in range(1, N) if s not in D)

        def V(Q, q):
            key = (Q, q)
            if key in memo:
                return memo[key]
            S = S_of(Q)
            best = 1 if S else 0
            if q > 0:
                for x in range(N):
                    if x in Q:
                        continue
                    hits = sum(1 for a in Q if (x ^ a) in S)
                    best = max(best, hits + V(Q | {x}, q - 1))
            memo[key] = best
            return best

        return F(V(frozenset(), q), M)

    def test_lower_bound_by_exhaustion(self):
        # n = 2, full model: all 36 functions, every adaptive strategy that sees the values
        n, N = 2, 4
        inputs, ss = [], []
        for s in range(1, N):
            reps = sorted({min(x, x ^ s) for x in range(N)})
            for labels in itertools.permutations(range(N), len(reps)):
                lab = dict(zip(reps, labels))
                inputs.append(tuple(lab[min(x, x ^ s)] for x in range(N)))
                ss.append(s)
        game = QueryGame(inputs, lambda i: {ss[i]})
        for q in range(0, 4):
            full = F(game.best_count(game.all(), q), len(inputs))
            self.assertEqual(full, self._pattern_optimum(2, q))
        for n in (2, 3, 4):
            M = (1 << n) - 1
            q = 0
            while q * (q - 1) // 2 < M:
                C = q * (q - 1) // 2
                self.assertLessEqual(self._pattern_optimum(n, q), F(C + 1, M - C))
                q += 1


# ------------------------------------------------------------------------------------------------------------------
# Collision problem
# ------------------------------------------------------------------------------------------------------------------

class CollisionProofChecks(unittest.TestCase):
    """PROOFS.md §4-§7 of the collision entry."""

    @classmethod
    def setUpClass(cls):
        cls.classical = staticmethod(load_callable(COLL, "implementations/classical.py:collision_classical"))
        cls.bht_mod = load_module(COLL / "implementations" / "bht.py")
        cls.harness = load_module(COLL / "harness.py")

    def test_classical_law_by_enumeration(self):
        rng = random.Random(8)
        for n in (1, 2, 3):
            N = 1 << n
            inst = self.harness.generate(n, rng)
            table = inst[1]
            counts = {}
            perms = list(itertools.permutations(range(N)))
            for idx, perm in enumerate(perms):
                with swapped(self.classical, random=_PermStub(perm)):
                    if N <= 4 or idx % 20 == 0:
                        out, loc = locals_at_return(self.classical, lambda: self.classical(inst))
                        ans, q = out
                        self.assertEqual(len(loc["seen"]), q - 1)
                    else:
                        ans, q = self.classical(inst)
                a, b = ans
                self.assertTrue(a < b and table[a] == table[b])
                counts[q] = counts.get(q, 0) + 1
            for q in range(0, N // 2 + 2):
                tail = F(sum(c for qq, c in counts.items() if qq > q), len(perms))
                self.assertEqual(tail, birthday_law(N, q))

    def test_classical_expectation_formula(self):
        for n in range(1, 11):
            N = 1 << n
            e = sum(birthday_law(N, q) for q in range(0, N // 2 + 1))
            self.assertEqual(e, F(2 ** N, math.comb(N, N // 2)))
            ef = float(e)
            self.assertGreater(ef, math.sqrt(math.pi * N / 2))
            self.assertLess(ef, math.sqrt(math.pi * N / 2) * math.exp(1 / (3 * N)))

    def test_bht_marked_set_and_success_probability(self):
        rng = random.Random(12)
        for n in range(1, 9):
            N = 1 << n
            k = self.bht_mod.subset_size(n)
            self.assertTrue(1 <= k <= N // 2)
            for _ in range(5):
                inst = self.harness.generate(n, rng)
                table = inst[1]
                for K in (list(range(k)), rng.sample(range(N), k)):
                    vals = [table[x] for x in K]
                    if len(set(vals)) < k:
                        continue
                    L = {table[x]: x for x in K}

                    def pred(x, fx):
                        return fx in L and L[fx] != x  # the predicate of bht.py

                    marked = {x for x in range(N) if pred(x, table[x])}
                    partners = {y for x in K for y in range(N) if y != x and table[y] == table[x]}
                    self.assertEqual(marked, partners)
                    self.assertEqual(len(marked), k)
                    m = qsearch.known_count_iterations(N, k)
                    st = State.uniform(n)
                    o = Oracle(table)
                    for _ in range(m):
                        qsearch.grover_iteration(st, lambda s: o.apply_phase_where(s, pred))
                    p = sum(abs(st.amp[x]) ** 2 for x in marked)
                    theta = math.asin(math.sqrt(k / N))
                    self.assertAlmostEqual(p, math.sin((2 * m + 1) * theta) ** 2, delta=1e-9)
                    self.assertGreaterEqual(p, 1 - k / N - 1e-9)

    def test_pnc_by_enumeration(self):
        for N in (8, 10):
            ms = [partner_array(m, N) for m in perfect_matchings(tuple(range(N)))]
            self.assertEqual(len(ms), math.prod(range(N - 1, 0, -2)))
            for k in range(1, 6):
                free = sum(1 for p in ms if all(p[x] >= k for x in range(k)))
                self.assertEqual(F(free, len(ms)), math.prod(F(N - 2 * i, N - i) for i in range(1, k)))

    def _pnc(self, N, k):
        p = 1.0
        for i in range(1, k):
            p *= (N - 2 * i) / (N - i)
        return p

    def test_bht_constants(self):
        sub = self.bht_mod.subset_size
        known, expo = {}, {}
        for n in range(1, 31):
            N, k = 1 << n, sub(n)
            x = 2 ** (n / 3)
            self.assertTrue(x / 2 < k < 1.5 * x)
            ek = k + self._pnc(N, k) * qsearch.expected_cost_known(N, k, 2, 1)
            ee = k + self._pnc(N, k) * qsearch.expected_cost_exponential(N, k, 2, 1)
            known[n], expo[n] = ek / x, ee / x
            self.assertGreaterEqual(ek, k)
            self.assertLessEqual(ek, (1.5 + math.pi * math.sqrt(2)) * x + 2)
            self.assertGreaterEqual(ee, k)
            self.assertLessEqual(ee, (1.5 + 18 * math.sqrt(2)) * x + math.log(math.sqrt(N), 1.2) + 5)
        for n in range(15, 31, 3):
            self.assertTrue(2.564 <= known[n] <= 2.572, (n, known[n]))
        for n in range(15, 31):
            self.assertTrue(2.536 <= known[n] <= 2.572, (n, known[n]))
        for n in range(18, 31):
            self.assertTrue(3.844 <= expo[n] <= 3.897, (n, expo[n]))

    def test_birthday_lemma_by_enumeration(self):
        N = 8
        ms = [partner_array(m, N) for m in perfect_matchings(tuple(range(N)))]
        for i in range(0, 5):
            for zs in itertools.permutations(range(N), i):
                cons = [p for p in ms if all(p[a] not in zs for a in zs)]
                for x in range(N):
                    if x in zs:
                        continue
                    hit = sum(1 for p in cons if p[x] in zs)
                    self.assertEqual(F(hit, len(cons)), F(i, N - i))
                if i >= 1 and N - i - 1 >= 1:
                    z = zs[0]
                    b = next(y for y in range(N) if y not in zs)
                    self.assertEqual(F(sum(1 for p in cons if p[z] == b), len(cons)), F(1, N - i))
                    u = [y for y in range(N) if y not in zs]
                    if len(u) >= 2:
                        a, b = u[0], u[1]
                        self.assertEqual(F(sum(1 for p in cons if p[a] == b), len(cons)),
                                         F(N - 2 * i, (N - i) * (N - i - 1)))

    def test_lower_bounds_by_exhaustion(self):
        for N in (4, 8):
            ms = [partner_array(m, N) for m in perfect_matchings(tuple(range(N)))]
            memo_c, memo_d = {}, {}

            def split(Q, S, x):
                parts = {}
                for i in S:
                    a = ms[i][x] if ms[i][x] in Q else None
                    parts.setdefault(a, []).append(i)
                return [frozenset(p) for p in parts.values()]

            def stop_count(S):
                return max(sum(1 for i in S if ms[i][a] == b) for a in range(N) for b in range(a + 1, N))

            def best(Q, S, q):
                key = (Q, S, q)
                if key not in memo_c:
                    v = stop_count(S)
                    if q > 0 and v < len(S):
                        for x in range(N):
                            if x not in Q:
                                v = max(v, sum(best(Q | {x}, P, q - 1) for P in split(Q, S, x)))
                    memo_c[key] = v
                return memo_c[key]

            def depth(Q, S):
                key = (Q, S)
                if key not in memo_d:
                    if stop_count(S) == len(S):
                        memo_d[key] = 0
                    else:
                        memo_d[key] = min(1 + max(depth(Q | {x}, P) for P in split(Q, S, x))
                                          for x in range(N) if x not in Q)
                return memo_d[key]

            allS = frozenset(range(len(ms)))
            for q in range(0, N - 1):
                opt = F(best(frozenset(), allS, q), len(ms))
                bound = F(q * (q - 1), 2 * (N - q + 1)) + F(1, N - q - 1)
                self.assertLessEqual(opt, bound, (N, q))
            self.assertEqual(depth(frozenset(), allS), N // 2 + 1)


# ------------------------------------------------------------------------------------------------------------------
# Minimum finding
# ------------------------------------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=None)
def exp_search_series(N, t, lam=1.2):
    """Expected iterations I and rounds R of the BBHT exponential search, by the series of Theorem E (own code)."""
    theta = math.asin(math.sqrt(t / N))
    root = math.sqrt(N)
    m, reach, I, R = 1.0, 1.0, 0.0, 0.0
    while True:
        M = math.ceil(m)
        p = sum(math.sin((2 * j + 1) * theta) ** 2 for j in range(M)) / M
        if m >= root:  # all later rounds identical: geometric tail
            return I + reach * (M - 1) / 2 / p, R + reach / p
        I += reach * (M - 1) / 2
        R += reach
        reach *= 1 - p
        m = min(lam * m, root)


def m0_of(N, t):
    return N / (2 * math.sqrt(t * (N - t)))


class MinimumFindingProofChecks(unittest.TestCase):
    """PROOFS.md §3-§6 of the minimum-finding entry."""

    def test_exact_lower_bound_by_exhaustion(self):
        for N in (2, 3, 4):
            tables = list(itertools.permutations(range(N + 1), N))
            game = QueryGame(tables, lambda i: {min(range(N), key=lambda x: tables[i][x])})
            self.assertEqual(game.worst_depth(game.all()), N)
            perms = list(itertools.permutations(range(N)))
            game2 = QueryGame(perms, lambda i: {perms[i].index(0)})
            self.assertEqual(game2.worst_depth(game2.all()), N - 1)

    def test_exponential_search_theorem(self):
        for n in range(1, 17):
            N = 1 << n
            ts = range(1, N) if n <= 11 else sorted(set(range(1, 201)) | set(range(N - 200, N))
                                                     | set(range(1, N, max(1, N // 200))))
            for t in ts:
                I, R = exp_search_series(N, t)
                m0 = m0_of(N, t)
                self.assertLess(I, 9 * m0, (N, t))
                self.assertLess(R, math.log(m0, 1.2) + 5, (N, t))
                if n <= 11 and t % 7 == 1:
                    self.assertAlmostEqual(I, qsearch.expected_cost_exponential(N, t, 1, 0), delta=1e-6 * (1 + I))
        for n in range(1, 7):
            N = 1 << n
            for t in range(1, N):
                theta = math.asin(math.sqrt(t / N))
                for M in range(1, 41):
                    direct = sum(math.sin((2 * j + 1) * theta) ** 2 for j in range(M)) / M
                    closed = 0.5 - math.sin(4 * M * theta) / (4 * M * math.sin(2 * theta))
                    self.assertAlmostEqual(direct, closed, delta=1e-12)
                    if M >= m0_of(N, t):
                        self.assertGreaterEqual(direct, 0.25 - 1e-12)

    def test_lemma1_exact(self):
        for N in range(2, 65):
            dist = [F(1, N)] * (N + 1)
            dist[0] = F(0)
            visited = [F(0)] * (N + 1)
            while any(dist):  # ranks strictly decrease, so each rank is visited at most once
                for r in range(1, N + 1):
                    visited[r] += dist[r]
                new = [F(0)] * (N + 1)
                for r in range(2, N + 1):
                    if dist[r]:
                        for r2 in range(1, r):
                            new[r2] += dist[r] / (r - 1)
                dist = new
            for r in range(1, N + 1):
                self.assertEqual(visited[r], F(1, r))

    def test_lemma2_bound(self):
        K = 10_000
        S = sum(1 / ((t + 1) * math.sqrt(t)) for t in range(1, K + 1)) + 2 / math.sqrt(K)
        self.assertLess(S, 1.861)

        def mdh(n):
            return 11.25 * math.sqrt(1 << n) + 0.7 * n * n

        worst = 0.0
        for n in range(1, 11):
            N = 1 << n
            A = sum(m0_of(N, t) / (t + 1) for t in range(1, N))
            H = sum(1 / r for r in range(2, N + 1))
            self.assertLess(H, 0.6932 * n)
            self.assertLess(A, 1.861 / 2 * math.sqrt(N) + 2.586)
            bound = n * H + 9 * A
            if n <= 6:
                self.assertLess(bound, 0.95 * mdh(n))
                worst = max(worst, bound / mdh(n))
            exact = sum((1 / r) * (n + exp_search_series(N, r - 1)[0]) for r in range(2, N + 1))
            self.assertLess(exact, bound)
            self.assertLess(exact, 0.95 * mdh(n))
        self.assertLess(worst, 0.77)
        self.assertLess(9 * (2 - math.sqrt(2) + 2), 23.28)
        for n in range(7, 201):
            self.assertGreater(0.95 * mdh(n) - (0.6932 * n * n + 9 * 1.861 / 2 * math.sqrt(2.0 ** n) + 23.28), 0)


# ------------------------------------------------------------------------------------------------------------------
# NAND tree
# ------------------------------------------------------------------------------------------------------------------

class _CountingBits:
    def __init__(self, bits):
        self.bits, self.reads = tuple(bits), 0

    def __len__(self):
        return len(self.bits)

    def __getitem__(self, i):
        self.reads += 1
        return self.bits[i]


def nand_value(bits):
    vals = list(bits)
    while len(vals) > 1:
        vals = [1 - (vals[2 * i] & vals[2 * i + 1]) for i in range(len(vals) // 2)]
    return vals[0]


def nand_formula(bits):
    """(value, exact expected reads, reluctant?) of the randomized algorithm by the case formulas of §4."""
    if len(bits) == 1:
        return bits[0], F(1), True
    h = len(bits) // 2
    va, ea, ra = nand_formula(bits[:h])
    vb, eb, rb = nand_formula(bits[h:])
    if va == 1 and vb == 1:
        return 0, ea + eb, ra and rb
    if va == 0 and vb == 0:
        return 1, (ea + eb) / 2, False
    e0, e1 = (ea, eb) if va == 0 else (eb, ea)
    return 1, e0 + e1 / 2, ra and rb


def R01(h):
    R0, R1 = [F(1)], [F(1)]
    for i in range(1, h + 1):
        R0.append(2 * R1[i - 1])
        R1.append(R0[i - 1] + R1[i - 1] / 2)
    return R0, R1


class NandTreeProofChecks(unittest.TestCase):
    """PROOFS.md §2-§5 of the NAND-tree entry."""

    @classmethod
    def setUpClass(cls):
        cls.left = staticmethod(load_callable(NAND, "implementations/left_first.py:nand_tree_left_first"))
        cls.rnd = staticmethod(load_callable(NAND, "implementations/random_order.py:nand_tree_random_order"))
        cls.harness = load_module(NAND / "harness.py")

    def exact_expectation(self, bits):
        """Exact expected reads of the unchanged randomized implementation: every coin sequence, in turn."""
        total, answers = F(0), set()
        stack = [()]
        while stack:
            prefix = stack.pop()
            leaves = _CountingBits(bits)
            stub = _SeqStub(prefix)
            try:
                with swapped(self.rnd, random=stub):
                    ans = self.rnd(leaves)
            except _SeqStub.NeedMore:
                stack += [prefix + (0,), prefix + (1,)]
                continue
            self.assertEqual(stub.used, len(prefix))
            total += F(leaves.reads, 2 ** len(prefix))
            answers.add(ans)
        return total, answers

    def test_deterministic_lower_bound_by_exhaustion(self):
        for h in range(0, 4):
            N = 1 << h
            inputs = list(itertools.product((0, 1), repeat=N))
            game = QueryGame(inputs, lambda i: {nand_value(inputs[i])})
            self.assertEqual(game.worst_depth(game.all()), N)

    def test_randomized_exact_expectations(self):
        for h in range(0, 4):
            R0, R1 = R01(h)
            worst = F(0)
            for bits in itertools.product((0, 1), repeat=1 << h):
                e, answers = self.exact_expectation(bits)
                v, ef, reluctant = nand_formula(bits)
                self.assertEqual(answers, {v})
                self.assertEqual(e, ef)
                cap = R0[h] if v == 0 else R1[h]
                self.assertLessEqual(e, cap)
                self.assertEqual(e == cap, reluctant)
                worst = max(worst, e)
            self.assertEqual(worst, R0[h])

    def test_closed_form(self):
        lam, mu = (1 + math.sqrt(33)) / 4, (1 - math.sqrt(33)) / 4
        a, b = 0.5 + 5 * math.sqrt(33) / 66, 0.5 - 5 * math.sqrt(33) / 66
        R0, R1 = R01(60)
        for h in range(0, 61):
            r1 = float(R1[h])
            self.assertAlmostEqual(r1 / (a * lam ** h + b * mu ** h), 1.0, delta=1e-12)
            self.assertGreater(r1 / lam ** h, 0.8703)
            self.assertLessEqual(r1 / lam ** h, 1.0 + 1e-12)
            if h >= 1:
                self.assertLess(r1 / lam ** h, 1.0)
                r0 = float(R0[h])
                self.assertGreater(r0 / lam ** h, 1.0324)
                self.assertLess(r0 / lam ** h, 1.1862)
                self.assertGreater(R0[h], R1[h])
                self.assertTrue(1.03 < r0 / r1 < 1.37)
        self.assertAlmostEqual(math.log2(lam), 0.75372, delta=5e-6)

    def test_space(self):
        for h in range(0, 13):
            bits = self.harness.reluctant(h, 1, lambda _h: 1)
            self.assertEqual(max_depth("evaluate", lambda: self.left(bits)), h + 1)
            random.seed(h)
            self.assertEqual(max_depth("evaluate", lambda: self.rnd(bits)), h + 1)


if __name__ == "__main__":
    unittest.main()
