"""First-match rule ordering by dynamic programming over subsets of rules, with the gains read from zeta transforms.

Instance (k, match, cost, default) as in enumeration.py; output (minimum total cost, an order attaining it).

The recurrence is that of subset_dp.py: best[{}] = 0, best[S + {r}] = min over r of best[S] + gain(S, r), where
gain(S, r) is the sum of cost[i][r] over the items i with r in M_i and M_i disjoint from S. Here the gains are not
collected by a pass over the items for every S. Group the items by their match set instead:
a_r[U] = sum of cost[i][r] over the items with M_i = U, for every rule r in U (and a_r[U] = 0 if r is not in U).
Item i contributes to gain(S, r) exactly when r is in M_i and M_i is a subset of the complement of S, so
    gain(S, r) = zeta a_r [complement of S],   where zeta a_r [W] = sum of a_r[U] over the subsets U of W.
Yates' method computes zeta a_r at all 2^k sets with one pass per bit, k 2^(k-1) additions per rule.

Work: k m match tests, one addition per matching (item, rule) pair and one per unmatched item to build the tables,
k^2 2^(k-1) transform additions and k 2^(k-1) transitions, so Theta(k^2 2^k + k m) on every input for k >= 1
(the k m term is reading the match flags), with Theta(k 2^k) table entries. subset_dp.py takes Theta(2^k (k + m)):
as k -> infinity this version is faster exactly when m/k^2 -> infinity and slower exactly when m/k^2 -> 0, and for
bounded k both are Theta(m) (PROOFS.md section 11.8). The technique, a transform over the subset lattice feeding a
dynamic program over the sets of elements placed so far, is that of Koivisto & Sood 2004 (sections 4 and 5), who
call the transform the Moebius transform.
"""


def first_match_order_zeta_dp(instance):
    k, match, cost, default = instance
    m = len(match)
    rules = [[r for r in range(k) if match[i][r]] for i in range(m)]
    size = 1 << k
    full = size - 1
    zero = type(cost[0][0])(0) if k and m else 0  # 0 in the number type of the costs, so that every table entry
    a = [[zero] * size for _ in range(k)]        # is a value of that type; a[r][U]: sum of cost[i][r] over the
                                                 # items with match set U
    base = 0
    for i in range(m):
        if rules[i]:
            u = 0
            for r in rules[i]:
                u |= 1 << r                      # the match set of item i as a bit mask (plain integers)
            for r in rules[i]:
                a[r][u] = a[r][u] + cost[i][r]
        else:                                    # no rule matches item i
            base = base + default[i]
    for r in range(k):                           # Yates' method, one pass per bit: afterwards
        z = a[r]                                 # a[r][W] = sum of the old a[r][U] over the subsets U of W
        for b in range(k):
            bit = 1 << b
            for w in range(size):
                if w & bit:
                    z[w] = z[w] + z[w ^ bit]
    best = [None] * size
    last = [-1] * size
    best[0] = 0
    for s in range(size):                        # increasing integers: every subset comes before its supersets
        best_s = best[s]
        rest = full ^ s                          # the rules not in s
        for r in range(k):
            bit = 1 << r
            if not s & bit:
                t = s | bit
                value = best_s + a[r][rest]      # gain(s, r) = zeta a_r [complement of s]
                if best[t] is None or value < best[t]:
                    best[t] = value
                    last[t] = r
    order = []
    s = full
    while s:
        r = last[s]
        order.append(r)
        s ^= 1 << r
    order.reverse()
    return best[full] + base, tuple(order)
