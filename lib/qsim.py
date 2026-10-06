"""A tiny, exact state-vector simulator for the query-model (T9) entries. Pure Python.

Conventions: a State over q qubits holds 2^q complex amplitudes, and qubit k is bit k of the basis-state
index. Simulating q qubits classically costs Theta(2^q) memory and time per gate. That cost belongs to the
simulation, not to the quantum algorithm. The dataset's claims about quantum algorithms concern ORACLE
QUERIES, which the Oracle class counts. Classical and quantum algorithms use the same Oracle, so their
query counts are directly comparable.
"""
from __future__ import annotations

import math


class State:
    def __init__(self, num_qubits: int, basis: int = 0):
        self.num_qubits = num_qubits
        self.amp = [0j] * (1 << num_qubits)
        self.amp[basis] = 1 + 0j

    @classmethod
    def uniform(cls, num_qubits: int) -> "State":
        """The uniform superposition H^n |0> = sum_x |x> / sqrt(2^n), written down directly.

        Added 2026-10-07. Same state as State(n) followed by h_all() (tests/test_qsim.py checks this), built in
        O(2^n) instead of O(n 2^n). Involves no oracle query.
        """
        state = cls(num_qubits)
        a = 1 / math.sqrt(1 << num_qubits) + 0j
        state.amp = [a] * (1 << num_qubits)
        return state

    def h(self, k: int) -> None:
        """Hadamard on qubit k."""
        s = 1 / math.sqrt(2)
        bit = 1 << k
        a = self.amp
        for i in range(len(a)):
            if not i & bit:
                x, y = a[i], a[i | bit]
                a[i], a[i | bit] = (x + y) * s, (x - y) * s

    def h_all(self) -> None:
        for k in range(self.num_qubits):
            self.h(k)

    def reflect_about_uniform(self) -> None:
        """The Grover diffusion operator H^n (2|0><0| - I) H^n = 2|u><u| - I, with |u> the uniform superposition.

        Applied directly as a -> 2*mean(a) - a, which is the same linear map. This is a simulation
        shortcut (O(2^n) instead of O(n 2^n)) and involves no oracle query.
        """
        mean = sum(self.amp) / len(self.amp)
        self.amp = [2 * mean - x for x in self.amp]

    def probabilities(self) -> list[float]:
        return [abs(x) ** 2 for x in self.amp]

    def measure_all(self, rng) -> int:
        """Measure every qubit in the computational basis; collapse; return the outcome index."""
        r = rng.random()
        acc = 0.0
        probs = self.probabilities()
        outcome = len(probs) - 1
        for i, p in enumerate(probs):
            acc += p
            if r < acc:
                outcome = i
                break
        self.amp = [0j] * len(self.amp)
        self.amp[outcome] = 1 + 0j
        return outcome


class Oracle:
    """Black-box access to f: {0, ..., 2^n - 1} -> integers, counting queries.

    A classical query is oracle(x). A quantum query is one call of an apply_* method. Each call counts
    once, whatever superposition it acts on.
    """

    def __init__(self, table):
        self._table = table
        self.queries = 0

    def __call__(self, x: int) -> int:
        self.queries += 1
        return self._table[x]

    def apply_phase(self, state: State) -> None:
        """One query: |x> -> (-1)^f(x) |x> for a Boolean f, acting on all qubits of `state`."""
        self.queries += 1
        a = state.amp
        for x, fx in enumerate(self._table):
            if fx & 1:
                a[x] = -a[x]

    def apply_phase_where(self, state: State, predicate) -> None:
        """TWO queries: |x> -> (-1)^[predicate(x, f(x))] |x>, for a predicate of the input and the oracle VALUE.

        Added 2026-10-07 for searches over a property derived from a non-Boolean f (e.g. "f(x) < f(y)" in
        minimum finding, "f(x) is in the table L" in collision finding). On a quantum computer this takes U_f to
        compute f(x) into an ancilla register, a query-free phase flip conditioned on predicate(x, f(x)), and U_f
        again to uncompute the ancilla, which must be returned to |0> for the branches to interfere. That is two
        queries per application (Boyer, Brassard, Hoyer & Tapp 1998, sections 3.1 and 7: one Grover iteration
        "requires two table look-ups (including one for uncomputation purposes)"). The ancilla is not
        materialised: after uncomputation it is |0> in every branch, so only the phase remains. Contrast
        apply_phase, which is ONE query because there f is itself Boolean (phase kickback).
        """
        self.queries += 2
        a = state.amp
        for x, fx in enumerate(self._table):
            if predicate(x, fx):
                a[x] = -a[x]

    def apply_xor_and_measure_output(self, state: State, rng) -> tuple[State, int]:
        """One query, U_f |x>|0> = |x>|f(x)>, immediately followed by measuring the output register.

        `state` is the input register. The output register is never materialised: the outcome v has
        probability sum over {x : f(x) = v} of |a_x|^2, and the input register collapses to the
        renormalised amplitudes on f^-1(v). This is exact whenever the algorithm does not act on the
        output register again (principle of deferred measurement). Returns (collapsed input state, v).
        """
        self.queries += 1
        weight: dict[int, float] = {}
        for x, ax in enumerate(state.amp):
            p = abs(ax) ** 2
            if p:
                weight[self._table[x]] = weight.get(self._table[x], 0.0) + p
        r, acc = rng.random(), 0.0
        values = sorted(weight)
        v = values[-1]
        for value in values:
            acc += weight[value]
            if r < acc:
                v = value
                break
        norm = math.sqrt(weight[v])
        out = State(state.num_qubits)
        out.amp = [ax / norm if self._table[x] == v else 0j for x, ax in enumerate(state.amp)]
        return out, v
