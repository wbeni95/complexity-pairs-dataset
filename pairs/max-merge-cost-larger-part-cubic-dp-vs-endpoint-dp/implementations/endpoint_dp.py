"""Worst-case merging of adjacent piles, merge cost = larger part: the endpoint DP, Theta(n^2).

Instance as in cubic_dp.py: a tuple of n + 1 non-negative pile sizes s_0..s_n. REQUIRED: every size is >= 0.
Only the two end splits are tried, i.e. the last merge of the row i..j joins a single end pile to the rest:

    c(i, i) = 0,   c(i, i+1) = max(s_i, s_(i+1)),
    c(i, j) = max( max(s_i, S(i+1, j)) + c(i+1, j),  max(S(i, j-1), s_j) + c(i, j-1) )      (j - i >= 2).

Correctness: Corollary 2 with Lemma 10 (theorems/endpoint-law-split-dependent-weights): for non-negative sizes the
merge cost max(L, R) satisfies the rotation condition RS3, so every row has a maximising split at one of its two
ends. Without the precondition the restriction can be wrong (entry README, Limits).

Work: n rows of length 1 with one merge-cost comparison each, and n(n-1)/2 rows of length >= 2 with two merge-cost
comparisons and one candidate comparison each: n(3n-1)/2 comparisons in all, on every input.
"""


def merge_cost(left, right):
    """Cost of merging two adjacent blocks of sizes left and right: the larger one (one comparison)."""
    return left if left >= right else right


def merge_max_larger_endpoint(sizes):
    n = len(sizes) - 1
    prefix = [0]  # prefix[t] = s_0 + ... + s_(t-1)
    for s in sizes:
        prefix.append(prefix[-1] + s)
    c = [[0] * (n + 1) for _ in range(n + 1)]
    for length in range(1, n + 1):
        for i in range(n - length + 1):
            j = i + length
            best = None
            for k in ((i + 1, j) if length >= 2 else (j,)):  # only the two end splits
                cand = merge_cost(prefix[k] - prefix[i], prefix[j + 1] - prefix[k]) + c[i][k - 1] + c[k][j]
                if best is None or cand > best:
                    best = cand
            c[i][j] = best
    return c[0][n]
