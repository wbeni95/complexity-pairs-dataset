"""Brassard-Hoyer-Tapp (BHT) collision finding: Theta(N^(1/3)) queries for 2-to-1 functions.

Collision(F, k) (BHT arXiv note 1997, section 2):
  1. Query a set K of k ~ N^(1/3) points classically (k queries); build the table L: value -> point.
  2. If two points of K collide, output them.
  3. Otherwise exactly t = k points outside K are partners of points in K (F is 2-to-1). Grover-search the
     whole domain for x with H(x) = 1, where H(x) = 1 iff F(x) is in L and x is not the point stored there.
  4. Output {L[F(x)], x}.

Query accounting (stricter than the paper's): every Grover iteration evaluates H in superposition, which
needs U_F to compute F(x), a comparison with L, and U_F again to uncompute: 2 queries
(lib.qsim.Oracle.apply_phase_where; Boyer, Brassard, Hoyer & Tapp 1998, sections 3.1 and 7). BHT's proof
counts one evaluation of F per evaluation of H. The constant factor does not affect Theta(N^(1/3)).
Every measured candidate is checked with one classical query, which also yields F(x) for step 4.

Two versions:
  collision_bht              K = {0, ..., k-1} (BHT: "an arbitrary subset") and Grover with the KNOWN number
                             t = k of marked points, floor(pi / (4 theta)) iterations, repeated on failure
                             (lib.qsearch.search_known_count). This is what BHT prescribe for r-to-1 functions.
  collision_bht_exponential  K uniformly random and the BBHT exponential search, which does not use t
                             (lib.qsearch.exponential_search). BHT prescribe this "fully generalized" search
                             (with random K) for arbitrary functions with |X| >= r|Y| that are not r-to-1.
Both are Las Vegas: the output is always a correct collision; the number of queries is random.
"""
import random

from lib import qsearch
from lib.qsim import Oracle


def subset_size(n):
    return max(1, round(2 ** (n / 3)))  # k = N^(1/3), rounded


def _collision(instance, K, search):
    n, table = instance
    oracle = Oracle(table)
    pairs = [(x, oracle(x)) for x in K]  # step 1: all k classical queries first, as in BHT
    L = {}
    for x, fx in pairs:  # steps 2-3: look for a collision inside K
        if fx in L:
            a, b = sorted((L[fx], x))
            return (a, b), oracle.queries
        L[fx] = x
    # (A first version stopped querying K at the first collision inside K. That saves queries but is not
    # BHT's step order, and its counts fell below the exact expectation; see
    # experiments/2026-10-07_collision_expected_queries.py, docstring.)

    def phase(state):  # H(x) = 1 iff F(x) in L and x is not the point stored for F(x); 2 queries
        oracle.apply_phase_where(state, lambda x, fx: fx in L and L[fx] != x)

    last = {}

    def check(x):  # one classical query per measured candidate
        last["value"] = fx = oracle(x)
        return fx in L and L[fx] != x

    x1 = search(n, phase, check, len(K))
    a, b = sorted((L[last["value"]], x1))
    return (a, b), oracle.queries


def collision_bht(instance):
    n, _ = instance
    k = subset_size(n)
    return _collision(instance, range(k),
                      lambda n, phase, check, t: qsearch.search_known_count(n, phase, check, t, random)[0])


def collision_bht_exponential(instance):
    n, _ = instance
    k = subset_size(n)
    K = random.sample(range(1 << n), k)
    return _collision(instance, K,
                      lambda n, phase, check, t: qsearch.exponential_search(n, phase, check, random)[0])
