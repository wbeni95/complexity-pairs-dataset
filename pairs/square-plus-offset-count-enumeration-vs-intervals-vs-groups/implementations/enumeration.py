"""Counting the n-bit integers with a cheap representation k = X^2 + C, by enumeration of all k (algorithm A1).

Definitions (as in entry.json). L(v) = number of binary digits of |v|, with L(0) = 1. The cost of writing k as
X^2 + C (X >= 0, C = k - X^2) is f_k(X) = L(X) + L(C) + [C < 0]. S_n = {0 <= k < 2^n : min over X of f_k(X) <= n - 4}.
Output: (|S_n|, number of cost evaluations f_k(X)).

Lemma A of the entry: min over all X >= 0 of f_k(X) = min(f_k(0), f_k(r), f_k(r + 1)) with r = isqrt(k). So each k
needs exactly three cost evaluations. r is kept incrementally (it grows by at most 1 from k to k + 1), so the whole
run makes exactly 3 * 2^n cost evaluations and Theta(2^n) word operations.
"""


def bit_length(v):
    """L(v): number of binary digits of |v|, with L(0) = 1."""
    v = -v if v < 0 else v
    return v.bit_length() if v else 1


def representation_cost(k, x):
    """f_k(x) = L(x) + L(C) + [C < 0] for C = k - x^2."""
    c = k - x * x
    return bit_length(x) + (bit_length(c) if c >= 0 else bit_length(c) + 1)


def count_by_enumeration(n):
    budget = n - 4
    covered = 0
    evaluations = 0
    r = 0
    for k in range(1 << n):
        while (r + 1) * (r + 1) <= k:      # r = isqrt(k), kept incrementally
            r += 1
        best = representation_cost(k, 0)
        for x in (r, r + 1):
            c = representation_cost(k, x)
            if c < best:
                best = c
        evaluations += 3
        if best <= budget:
            covered += 1
    return covered, evaluations
