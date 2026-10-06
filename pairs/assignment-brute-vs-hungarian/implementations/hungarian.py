"""Hungarian method as successive shortest augmenting paths with potentials: O(n^3) time.

Rows are inserted one at a time. For each new row, a Dijkstra-like search over columns, run on
reduced costs c(i, j) - u[i] - v[j] >= 0 (array version, O(n) per step), finds a cheapest augmenting
path to a free column; the potentials u, v are then updated so that reduced costs stay non-negative
and are zero on the current matching. At most n search steps per row, O(n) each, n rows: O(n^3).

Indices are 1-based internally; column 0 is a sentinel that holds the row being inserted.
"""


def assignment_hungarian(C) -> int:
    n = len(C)
    if n == 0:
        return 0
    INF = float("inf")
    u = [0] * (n + 1)        # row potentials
    v = [0] * (n + 1)        # column potentials
    match = [0] * (n + 1)    # match[j] = row assigned to column j (0 = free)
    way = [0] * (n + 1)      # way[j] = previous column on the shortest alternating path to j
    for i in range(1, n + 1):
        match[0] = i
        j0 = 0
        minv = [INF] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = match[j0]
            row = C[i0 - 1]
            ui0 = u[i0]
            delta = INF
            j1 = 0
            for j in range(1, n + 1):
                if not used[j]:
                    cur = row[j - 1] - ui0 - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[match[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if match[j0] == 0:   # reached a free column: augment
                break
        while j0:
            j1 = way[j0]
            match[j0] = match[j1]
            j0 = j1
    return sum(C[match[j] - 1][j - 1] for j in range(1, n + 1))
