"""Sparse table: precompute the minimum of every range whose length is a power of two, then answer each
query with two overlapping blocks.

table[j][i] = min(values[i .. i + 2^j - 1]) for j = 0..floor(log2 n), built level by level from
table[j][i] = min(table[j-1][i], table[j-1][i + 2^(j-1)]): Theta(n log n) time and space.
A query (l, r) with k = floor(log2(r - l + 1)) is covered by the two blocks [l, l + 2^k) and
(r - 2^k, r], so its answer is min(table[k][l], table[k][r - 2^k + 1]): O(1) per query using a
precomputed table of floor(log2) values.

Total Theta(n log n + q): Theta(n log n) for q = n queries.

Instance: (values, queries) as in the naive implementation; returns the tuple of minima.
"""


def rmq_sparse_table(instance):
    values, queries = instance
    n = len(values)
    if n == 0:
        return ()
    log2 = [0] * (n + 1)                 # log2[L] = floor(log2 L) for L >= 1
    for L in range(2, n + 1):
        log2[L] = log2[L // 2] + 1
    table = [list(values)]
    j = 1
    while (1 << j) <= n:
        prev = table[-1]
        half = 1 << (j - 1)
        table.append([min(prev[i], prev[i + half]) for i in range(n - (1 << j) + 1)])
        j += 1
    out = []
    for l, r in queries:
        k = log2[r - l + 1]
        row = table[k]
        a, b = row[l], row[r - (1 << k) + 1]
        out.append(a if a <= b else b)
    return tuple(out)
