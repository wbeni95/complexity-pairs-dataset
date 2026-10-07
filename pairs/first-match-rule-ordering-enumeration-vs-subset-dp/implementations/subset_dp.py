"""First-match rule ordering by dynamic programming over subsets of rules.

Instance (k, match, cost, default) as in enumeration.py; output (minimum total cost, an order attaining it).

Key fact: if the set S of rules already placed is known, placing rule r next captures exactly the items i with
r in M_i and M_i disjoint from S (every other item of r is already captured by an earlier rule), so the cost of
that step, gain(S, r) = sum of cost[i][r] over those items, does not depend on the order inside S. Hence
    best[{}] = 0,   best[S + {r}] = min over r in S + {r} of best[S] + gain(S, r),
and the answer is best[all rules] plus the defaults of the items that match no rule.

For each S the gains of all rules are collected in one pass over the items: an item not yet captured by S
(mask_i & S = 0) adds cost[i][r] to gain[r] for each r in M_i. Work per S: m capture tests, the additions of
the uncaptured items, and k - |S| transitions. Summed over S, an item with |M_i| = t >= 1 is uncaptured for
2^(k-t) sets and then adds t costs, and t * 2^(k-t) <= 2^(k-1); so the total is Theta(2^k (k + m)) on every
input, with Theta(2^k) memory.
"""


def first_match_order_subset_dp(instance):
    k, match, cost, default = instance
    m = len(match)
    rules = [[r for r in range(k) if match[i][r]] for i in range(m)]
    masks = [sum(match[i][r] << r for r in range(k)) for i in range(m)]
    size = 1 << k
    best = [None] * size
    last = [-1] * size
    best[0] = 0
    for s in range(size):                        # increasing integers: every subset comes before its supersets
        best_s = best[s]
        gain = [0] * k
        for i in range(m):
            if not (masks[i] & s):               # item i is not captured by the rules in s
                for r in rules[i]:
                    gain[r] = gain[r] + cost[i][r]
        for r in range(k):
            bit = 1 << r
            if not s & bit:
                t = s | bit
                value = best_s + gain[r]
                if best[t] is None or value < best[t]:
                    best[t] = value
                    last[t] = r
    base = 0
    for i in range(m):
        if not rules[i]:
            base = base + default[i]
    order = []
    s = size - 1
    while s:
        r = last[s]
        order.append(r)
        s ^= 1 << r
    order.reverse()
    return best[size - 1] + base, tuple(order)
