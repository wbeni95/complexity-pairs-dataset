"""Global minimum cut by the Stoer-Wagner algorithm (array version, no priority queue).

Input: an n x n symmetric matrix W of non-negative weights with zero diagonal. Output: the minimum cut weight,
or None for n < 2 (no partition into two non-empty sides exists).

Stoer & Wagner, "A simple min-cut algorithm", J. ACM 44(4), 1997. Each phase grows a set A from a start vertex,
always adding the remaining vertex most tightly connected to A (maximum-adjacency order). If s and t are the last
two vertices added, the "cut of the phase" (t against everything else, of weight w(A - t, t)) is a minimum s-t
cut. The global minimum cut either separates s and t (then it is at most the cut of the phase) or it does not
(then s and t can be merged). So the answer is the lightest cut of the phase over n - 1 phases, merging s and t
after each phase. A phase on k remaining vertices costs Theta(k^2) with plain arrays, Theta(n^3) in total.
"""


def min_cut_stoer_wagner(W):
    n = len(W)
    if n < 2:
        return None
    G = [list(row) for row in W]       # working copy; merged vertices accumulate their weights here
    active = list(range(n))            # current (super-)vertices
    best = None
    while len(active) > 1:
        # --- one phase: maximum-adjacency ordering of the active vertices, starting at active[0] ---
        a = active[0]
        rest = active[1:]
        key = {v: G[a][v] for v in rest}  # key[v] = total weight between v and the growing set A
        s, t = a, None
        while rest:
            sel = rest[0]
            for v in rest[1:]:            # pick the most tightly connected remaining vertex
                if key[v] > key[sel]:
                    sel = v
            rest.remove(sel)
            for v in rest:                # A grew by sel: update the remaining keys
                key[v] = key[v] + G[sel][v]
            s, t = (t if t is not None else a), sel
        cut_of_phase = key[t]             # weight between t and all other active vertices
        if best is None or cut_of_phase < best:
            best = cut_of_phase
        # --- merge t into s ---
        active.remove(t)
        for v in active:
            if v != s:
                G[s][v] = G[s][v] + G[t][v]
                G[v][s] = G[s][v]
    return best
