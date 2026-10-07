"""Maximum-weight independent set on a k x n grid with diagonals, by trying all 2^(k n) vertex subsets.

Instance: (k, n, weights, diagonals). Vertices are (r, c) with row r in 0..k-1 and column c in 0..n-1;
weights[r][c] is a non-negative integer. Edges: (r, c)-(r, c+1), (r, c)-(r+1, c), and in the unit square with
top-left corner (r, c) (diagonals[r][c], r < k-1, c < n-1): code 1 adds the diagonal (r, c)-(r+1, c+1), code 2
adds (r, c+1)-(r+1, c), code 3 adds both, code 0 neither.

Every subset of the N = k n vertices is examined in full, with no early exit: its weight is summed over all its
members and its independence is tested at every member (neighbour bitmask AND subset). The heaviest independent
subset found first (in increasing bitmask order) is returned. Weight additions: exactly N 2^(N-1) (every vertex
lies in half of the subsets). Time Theta(N 2^N) on every input with N >= 1 (the final sorted() of at most N
vertices taken as O(N log N), see entry.json), space Theta(N).

Returns (maximum weight, sorted tuple of the chosen vertices (r, c)).
"""


def _edges(k, n, diagonals):
    for c in range(n):
        for r in range(k):
            if c + 1 < n:
                yield (r, c), (r, c + 1)
            if r + 1 < k:
                yield (r, c), (r + 1, c)
            if r + 1 < k and c + 1 < n:
                code = diagonals[r][c]
                if code & 1:
                    yield (r, c), (r + 1, c + 1)
                if code & 2:
                    yield (r, c + 1), (r + 1, c)


def mwis_brute_force(instance):
    k, n, weights, diagonals = instance
    vertices = [(r, c) for c in range(n) for r in range(k)]
    index = {v: i for i, v in enumerate(vertices)}
    count = len(vertices)
    neighbours = [0] * count                   # neighbours[i]: bitmask of the vertices adjacent to vertex i
    for u, v in _edges(k, n, diagonals):
        neighbours[index[u]] |= 1 << index[v]
        neighbours[index[v]] |= 1 << index[u]

    best_value = 0
    best_mask = 0
    for mask in range(1 << count):
        total = 0
        independent = True
        for i in range(count):
            if (mask >> i) & 1:
                r, c = vertices[i]
                total = total + weights[r][c]
                if neighbours[i] & mask:
                    independent = False
        if independent and total > best_value:
            best_value = total
            best_mask = mask
    chosen = tuple(sorted(vertices[i] for i in range(count) if (best_mask >> i) & 1))
    return best_value, chosen
