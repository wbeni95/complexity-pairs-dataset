"""Maximum-weight independent set on a k x n grid with diagonals, by dynamic programming over the columns.

Instance: (k, n, weights, diagonals), as in brute_force.py: vertices (r, c), r in 0..k-1, c in 0..n-1, weights
weights[r][c] >= 0; edges between horizontal and vertical neighbours, plus per unit square (diagonals[r][c]):
1 = (r, c)-(r+1, c+1), 2 = (r, c+1)-(r+1, c), 3 = both, 0 = neither.

Path decomposition: the bags B_c = column c + column c+1 (c = 0..n-2) cover every edge, because every edge joins
two vertices in the same column or in adjacent columns, so the decomposition has width 2k - 1. Consecutive bags
share one column, and column c separates the columns left of it from those right of it. The programme therefore
keeps, for every column c and every subset s of column c that is independent inside the column (no two
vertically adjacent rows: s & (s >> 1) == 0), the best weight of an independent set of columns 0..c whose
intersection with column c is s:
    best_0(s) = w_0(s)
    best_c(s) = w_c(s) + max over states t of column c-1 compatible with s of best_{c-1}(t)
where w_c(s) is the weight of s, and t, s are compatible if no horizontal or diagonal edge joins them. The
answer is the maximum of best_{n-1}; an optimal set is recovered from the stored arg-max choices.

The number of column states is F_{k+2} (Fibonacci: 2, 3, 5, 8, 13, 21 for k = 1..6). Per column the programme
tests all F_{k+2}^2 state pairs for compatibility (O(1) word operations each) and sums the column weights
(at most k additions per state). Time Theta(F_{k+2}^2 n) = Theta(phi^(2k) n) word operations: linear in n for
every fixed k, exponential in k. Weight additions: exactly n P_k + (n - 1) F_{k+2} when all weights are positive,
where P_k is the total number of rows over all column states (P_3 = 5, F_5 = 5: 10n - 5 for k = 3). Space
Theta(F_{k+2} n) for the arg-max table.

Returns (maximum weight, sorted tuple of the chosen vertices (r, c)).
"""


def mwis_column_dp(instance):
    k, n, weights, diagonals = instance
    if n == 0:
        return 0, ()
    states = [s for s in range(1 << k) if s & (s >> 1) == 0]

    def column_weight(c, s):
        total = 0
        for r in range(k):
            if (s >> r) & 1:
                total = total + weights[r][c]
        return total

    best = [column_weight(0, s) for s in states]
    back = []                                  # back[c-1][j]: best state index of column c-1 for state j of column c
    for c in range(1, n):
        down = 0                               # bit r: square (r, c-1) has the diagonal (r, c-1)-(r+1, c)
        up = 0                                 # bit r: square (r, c-1) has the diagonal (r, c)-(r+1, c-1)
        for r in range(k - 1):
            code = diagonals[r][c - 1]
            if code & 1:
                down |= 1 << r
            if code & 2:
                up |= 1 << r
        new_best = []
        choice = []
        for s in states:
            m = None
            arg = -1
            for j, t in enumerate(states):
                if t & s:                      # horizontal edge (r, c-1)-(r, c)
                    continue
                if ((t & down) << 1) & s:      # diagonal (r, c-1)-(r+1, c)
                    continue
                if ((s & up) << 1) & t:        # diagonal (r, c)-(r+1, c-1)
                    continue
                if m is None or best[j] > m:
                    m = best[j]
                    arg = j
            new_best.append(column_weight(c, s) + m)
            choice.append(arg)
        best = new_best
        back.append(choice)

    j = 0
    for i in range(1, len(states)):
        if best[i] > best[j]:
            j = i
    value = best[j]
    chosen = []
    for c in range(n - 1, -1, -1):
        s = states[j]
        chosen.extend((r, c) for r in range(k) if (s >> r) & 1)
        if c > 0:
            j = back[c - 1][j]
    return value, tuple(sorted(chosen))
