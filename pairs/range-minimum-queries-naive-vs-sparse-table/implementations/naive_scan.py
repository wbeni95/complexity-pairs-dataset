"""Answer each range-minimum query by scanning its range: Theta(r - l + 1) per query.

Total cost Theta(q + sum of the query lengths): Theta(n q) when the queries have length Theta(n), i.e.
Theta(n^2) for q = n such queries (the timing family uses ranges of length >= n/2). No preprocessing.

Instance: (values, queries), values a tuple of n numbers and queries a tuple of pairs (l, r), 0 <= l <= r < n.
Returns the tuple of minima min(values[l..r]), one per query.
"""


def rmq_naive(instance):
    values, queries = instance
    out = []
    for l, r in queries:
        m = values[l]
        for i in range(l + 1, r + 1):
            x = values[i]
            if x < m:
                m = x
        out.append(m)
    return tuple(out)
