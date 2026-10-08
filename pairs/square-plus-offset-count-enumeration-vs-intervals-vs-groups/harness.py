"""Harness for counting the n-bit integers with a cheap representation k = X^2 + C.

Problem (entry.json). L(v) = number of binary digits of |v|, with L(0) = 1. Writing k >= 0 as X^2 + C (X >= 0,
C = k - X^2) costs f_k(X) = L(X) + L(C) + [C < 0] bits. S_n = {0 <= k < 2^n : some X >= 0 has f_k(X) <= n - 4}.
The instance is n itself; every implementation returns (|S_n|, work), where work is the count it reports for V2:
  enumeration      cost evaluations f_k(X)        exactly 3 * 2^n
  interval sweep   roots X = 0..isqrt(2^n - 1)+1  exactly isqrt(2^n - 1) + 2  (= 2^(n/2) + 1 for even n)
  groups           root groups                    exactly floor(n/2) + 1 for n >= 11
`equal` compares the counts |S_n| only; `reported_cost` returns the work.

check(n, output) is independent of the three implementations (separate code):
  - n <= BRUTE_MAX: brute force over ALL roots. For each k < 2^n it takes the minimum of f_k(X) over every X with
    X^2 < k + 2^L(k) (Lemma 0 of the entry: a larger X costs more than X = 0), so it uses neither Lemma A nor
    Lemma B;
  - n <= UNION_MAX: the union of the clipped intervals of Lemma B, built for X = 0..isqrt(2^n - 1)+1, sorted and
    merged (no monotonicity of the left ends and no grouping is used);
  - larger n: None (undecided).
Both reference values are cached per n.
"""
from math import isqrt

BRUTE_MAX = 12
UNION_MAX = 34
_cache = {}


def generate(n, rng):
    return n


def _L(v):
    v = -v if v < 0 else v
    return v.bit_length() if v else 1


def _cost(k, x):
    c = k - x * x
    return _L(x) + (_L(c) if c >= 0 else _L(c) + 1)


def brute_force_count(n):
    """|S_n| from the minimum over all roots in the window X^2 < k + 2^L(k) (Lemma 0), for every k < 2^n."""
    budget = n - 4
    covered = 0
    for k in range(1 << n):
        top = isqrt(k + (1 << _L(k)) - 1)            # largest X with X^2 < k + 2^L(k)
        if min(_cost(k, x) for x in range(top + 1)) <= budget:
            covered += 1
    return covered


def sorted_union_count(n):
    """|S_n| as the size of the union of the clipped intervals of Lemma B (sorted, then merged)."""
    B = (1 << n) - 1
    v = n - 4
    intervals = []
    for x in range(isqrt(B) + 2):
        w = v - _L(x)
        if w >= 1:
            m = (1 << (w - 1)) - 1 if w >= 2 else 0
            lo, hi = max(0, x * x - m), min(x * x + (1 << w) - 1, B)
            if lo <= hi:
                intervals.append((lo, hi))
    intervals.sort()
    total, cur_lo, cur_hi = 0, None, None
    for lo, hi in intervals:
        if cur_lo is None:
            cur_lo, cur_hi = lo, hi
        elif lo <= cur_hi + 1:
            cur_hi = max(cur_hi, hi)
        else:
            total += cur_hi - cur_lo + 1
            cur_lo, cur_hi = lo, hi
    if cur_lo is not None:
        total += cur_hi - cur_lo + 1
    return total


def reference_count(n):
    if n not in _cache:
        if n <= BRUTE_MAX:
            _cache[n] = brute_force_count(n)
        elif n <= UNION_MAX:
            _cache[n] = sorted_union_count(n)
        else:
            _cache[n] = None
    return _cache[n]


def check(instance, output):
    n = instance
    if not (isinstance(output, tuple) and len(output) == 2):
        return False
    count, work = output
    if any(isinstance(t, bool) or not isinstance(t, int) for t in (count, work)):
        return False
    if not 0 <= count <= (1 << n):
        return False
    ref = reference_count(n)
    if ref is None:
        return None
    return count == ref


def equal(a, b):
    return a[0] == b[0]


def reported_cost(output):
    return output[1]
