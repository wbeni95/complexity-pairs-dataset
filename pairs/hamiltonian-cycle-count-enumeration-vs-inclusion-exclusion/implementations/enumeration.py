"""Count directed Hamiltonian cycles by enumerating all (n-1)! vertex orders.

Input: an n x n 0/1 adjacency matrix (tuple of tuples); adj[u][v] = 1 means there is an arc u -> v. The diagonal
is ignored. An undirected graph is a symmetric matrix.

Output: the number of directed Hamiltonian cycles, each cycle counted once (not once per start vertex).
Conventions: n <= 1 gives 0; n = 2 gives 1 if both arcs 0 -> 1 and 1 -> 0 exist, else 0.

Every directed Hamiltonian cycle passes through vertex 0, so it can be written in exactly one way as
0 -> v_1 -> ... -> v_{n-1} -> 0. The function enumerates all (n-1)! orders (v_1, ..., v_{n-1}) of the other
vertices and tests the n arcs of each order, stopping at the first missing arc. On the complete digraph no test
fails, so exactly n * (n-1)! = n! arc tests are made; on every input at least (n-1)! orders are generated.
Time Theta(n!) arc tests in the worst case, space Theta(n).
"""
from itertools import permutations


def count_hamiltonian_cycles_enumeration(adj):
    n = len(adj)
    if n <= 1:
        return 0
    count = 0
    for order in permutations(range(1, n)):
        prev = 0
        complete = True
        for v in order:
            if not adj[prev][v]:               # arc test
                complete = False
                break
            prev = v
        if complete and adj[prev][0]:          # arc test for the closing arc back to 0
            count += 1
    return count
