"""Optimal LZ77-style parsing with k repeat-offset slots by dynamic programming over (position, slot contents).

Instance (s, k, repmin) and token model as in enumeration.py; output (minimum total cost, number of relaxations).

Key fact: the costs are static, so whether a token is allowed at position i and what it costs depend only on i and
the current slot tuple R. Hence best[i][R], the cheapest cost of a token sequence from (0, (1, ..., 1)) that reaches
position i with slots R, satisfies the forward recurrence "best[i + len][succ(R, token)] = min(..., best[i][R] +
cost(token))", and the optimum is min over R of best[n][R]. Positions are processed left to right; every token has
length >= 1, so best[i] is final when position i is processed.

New matches from (i, R) lead to (d, R[0..k-2]) at a cost that does not depend on R[k-1]. So they are generated once
per distinct (k-1)-prefix R[0..k-2] at position i, from the cheapest state with that prefix ("prefix grouping");
this does not change any value.

A "relaxation" is one candidate value best[i][R] + cost(token) offered to a successor: one per state for the literal,
one per (slot, length) for the repeats, one per (prefix group, distance, length) for the new matches. This is the
operation counted for V2. Not counted: the Theta(n^2) match-length table, the lists of distances with a match of
length >= 2, the k slot tests per state and the dictionary updates. Proofs (correctness, bounds, the uncounted work):
PROOFS.md in the entry folder, sections 5, 6.2 and 6.3.
"""

LITERAL_COST = 9


def gamma_len(x):
    return 2 * (x.bit_length() - 1) + 1


def match_lengths(s):
    """ml[i][d] = largest L with i + L <= n and s[i+t] == s[i+t-d] for all t < L (1 <= d <= i <= n)."""
    n = len(s)
    ml = [[0] * (i + 1) for i in range(n + 1)]
    for i in range(n - 1, -1, -1):
        row, nxt = ml[i], ml[i + 1]
        for d in range(1, i + 1):
            if s[i] == s[i - d]:
                row[d] = 1 + nxt[d]
    return ml


def _offer(table, slots, value):
    old = table.get(slots)
    if old is None or value < old:
        table[slots] = value


def lz77_slots_dp(instance):
    s, k, repmin = instance
    n = len(s)
    ml = match_lengths(s)
    best = [dict() for _ in range(n + 1)]
    best[0][(1,) * k] = 0
    relaxations = 0
    for i in range(n):
        row = ml[i]
        distances = [d for d in range(1, i + 1) if row[d] >= 2]
        groups = {}
        for slots, cost in best[i].items():
            relaxations += 1                                       # literal
            _offer(best[i + 1], slots, cost + LITERAL_COST)
            for j in range(k):                                     # repeats
                r = slots[j]
                if r <= i and row[r] >= repmin:
                    moved = (r,) + slots[:j] + slots[j + 1:]
                    for length in range(repmin, row[r] + 1):
                        relaxations += 1
                        _offer(best[i + length], moved, cost + 3 + j + gamma_len(length))
            prefix = slots[:-1]
            if prefix not in groups or cost < groups[prefix]:
                groups[prefix] = cost
        for prefix, cost in groups.items():                        # new matches, once per prefix group
            for d in distances:
                pushed = (d,) + prefix
                for length in range(2, row[d] + 1):
                    relaxations += 1
                    _offer(best[i + length], pushed, cost + 2 + gamma_len(length - 1) + gamma_len(d))
    return min(best[n].values()), relaxations
