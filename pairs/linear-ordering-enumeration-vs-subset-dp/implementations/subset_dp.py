"""Linear ordering problem by dynamic programming over subsets.

Instance and output as in enumeration.py. If the set S of elements placed first is known, placing v next adds
W[v][u] for every element u placed later, i.e. for every u outside S + {v}, independently of the order inside S. So
    best[{}] = 0,   best[S + {v}] = max over v of best[S] + sum of W[v][u] over u not in S + {v},
and best[all] is the optimum. Per subset S and element v outside it the gain is summed in n - |S| - 1 additions:
Theta(n^2 2^n) time on every input, Theta(2^n) memory.
"""


def linear_ordering_subset_dp(w):
    n = len(w)
    size = 1 << n
    best = [None] * size
    last = [-1] * size
    best[0] = 0
    for s in range(size):
        best_s = best[s]
        for v in range(n):
            bit = 1 << v
            if s & bit:
                continue
            t = s | bit
            gain = 0
            row = w[v]
            for u in range(n):
                if u != v and not (t >> u) & 1:
                    gain = gain + row[u]
            value = best_s + gain
            if best[t] is None or value > best[t]:
                best[t] = value
                last[t] = v
    order = []
    s = size - 1
    while s:
        v = last[s]
        order.append(v)
        s ^= 1 << v
    order.reverse()
    return best[size - 1], tuple(order)
