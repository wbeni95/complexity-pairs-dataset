"""Worst-case total imbalance of merging adjacent piles (merge cost |L - R|): the endpoint DP, Theta(n^2).

Instance as in cubic_dp.py: a tuple of n + 1 non-negative pile sizes s_0..s_n. REQUIRED: every size is >= 0.
Only the two end splits are tried, i.e. the last merge of the row i..j joins a single end pile to the rest:

    c(i, i) = 0,   c(i, i+1) = |s_i - s_(i+1)|,
    c(i, j) = max( |s_i - S(i+1, j)| + c(i+1, j),  |S(i, j-1) - s_j| + c(i, j-1) )      (j - i >= 2).

Correctness: Theorem 1 with Lemma 11 (theorems/endpoint-law-split-dependent-weights): for non-negative sizes the
merge cost |L - R| satisfies the weak rotation condition RS3w, so every row has a maximising split at one of its two
ends. (It does not satisfy RS3 in general, so Corollary 2 alone does not apply.) Without the precondition the
restriction can be wrong (entry README, Limits).

Work: n rows of length 1 with one merge-cost comparison each, and n(n-1)/2 rows of length >= 2 with two merge-cost
comparisons and one candidate comparison each: n(3n-1)/2 comparisons in all, on every input.
"""


def merge_cost(left, right):
    """Cost of merging two adjacent blocks of sizes left and right: |left - right| (one comparison)."""
    return left - right if left >= right else right - left


def merge_max_imbalance_endpoint(sizes):
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
