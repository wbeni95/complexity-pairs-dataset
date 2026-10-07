"""First-match rule ordering by enumerating all k! orders.

Instance (k, match, cost, default): k rules, m = len(match) items; match[i][r] is 1 iff rule r matches item i;
cost[i][r] is paid if r is the first rule of the order that matches item i (ignored where match[i][r] is 0);
default[i] is paid if no rule matches item i. Output (minimum total cost, an order attaining it).

Every order is evaluated from scratch: each item scans the order until its first matching rule. On an order
the scan of item i stops at the first position holding a rule of M_i = {r : match[i][r] = 1}, so one order costs
between m and k*m match tests: O(k! * k * m) in total for k, m >= 1 (with the generator's documented O(k * k!)
total work, a machine-model assumption; PROOFS.md section 5.1), and Theta(k! * k * m) when every item matches at most a
bounded number of rules (an item with t >= 1 matching rules scans (k+1)/(t+1) positions on average over the
k! orders; PROOFS.md section 5.1).
"""
from itertools import permutations


def first_match_order_enumeration(instance):
    k, match, cost, default = instance
    m = len(match)
    best = None
    best_order = None
    for order in permutations(range(k)):
        total = 0
        for i in range(m):
            row = match[i]
            for r in order:
                if row[r]:
                    total = total + cost[i][r]
                    break
            else:                                # no rule matches item i
                total = total + default[i]
        if best is None or total < best:
            best, best_order = total, order
    return best, best_order
