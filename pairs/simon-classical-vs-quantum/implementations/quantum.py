"""Simon's quantum algorithm: O(n) queries.

Each round is H^n, one query U_f with the output register measured, then H^n and a measurement.
The outcome y is uniform over {y : y.s = 0 mod 2}. Collect y's until they span an (n-1)-dimensional
subspace of GF(2)^n; s is then the unique nonzero vector orthogonal to all of them. Expected
rounds: n - 1 + O(1). Simulated exactly with lib.qsim.
"""
import random

from lib.qsim import Oracle, State


def simon_quantum(instance):
    n, table = instance
    oracle = Oracle(table)
    rows = {}  # pivot bit -> row, kept fully reduced (each pivot bit appears in exactly one row)
    while len(rows) < n - 1:
        state = State(n)
        state.h_all()
        state, _ = oracle.apply_xor_and_measure_output(state, random)
        state.h_all()
        y = state.measure_all(random)
        for p, row in rows.items():
            if y >> p & 1:
                y ^= row
        if y:
            p = y.bit_length() - 1
            for q in rows:
                if rows[q] >> p & 1:
                    rows[q] ^= y
            rows[p] = y
    # Exactly one bit is not a pivot: the free variable. Set it to 1 and solve each row for its pivot.
    free = next(b for b in range(n) if b not in rows)
    s = 1 << free
    for p, row in rows.items():
        if row >> free & 1:
            s |= 1 << p
    return s, oracle.queries
