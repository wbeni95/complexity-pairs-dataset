"""Chromatic number by inclusion-exclusion (Bjorklund, Husfeldt & Koivisto 2009).

Let a(S) = the number of non-empty independent sets contained in the vertex set S. By inclusion-exclusion,
    c_k = sum over S subset of V of (-1)^(n - |S|) a(S)^k
counts the k-tuples (I_1, ..., I_k) of non-empty independent sets whose union is V. Such a cover exists iff
chi(G) <= k (give each vertex the colour of the first set containing it), so chi(G) is the least k >= 1 with
c_k > 0 (for n >= 1).

Step 1 tabulates a over all 2^n subsets with the recurrence a(S) = a(S - v) + a(S - N[v]) + 1 for any
v in S (independent sets avoiding v; and {v} plus an independent subset of S minus v's closed
neighbourhood), a(empty) = 0: 2^n - 1 steps of two additions.
Step 2 tries k = 1, 2, ... and stops at the first k with c_k > 0, i.e. after chi(G) rounds. Round k updates
p(S) = a(S)^k by one multiplication p(S) * a(S) and adds +-p(S) to the sum: two arithmetic operations per
subset. All numbers are exact integers: the table entries have at most n * chi(G) bits (a(S) < 2^n), the
running sum at most n * (chi(G) + 1) bits (PROOFS.md section 2.6).

Total: (2 chi(G) + 2) 2^n - 2 arithmetic operations, O(n 2^n) in the unit-cost model since chi(G) <= n;
Theta(2^n) space for the tables.

The graph is (n, edges) with vertices 0..n-1 and edges a tuple of pairs (u, v), u < v.
"""


def chromatic_inclusion_exclusion(graph) -> int:
    n, edges = graph
    if n == 0:
        return 0
    closed = [1 << v for v in range(n)]          # closed neighbourhoods N[v] as bit masks
    for u, v in edges:
        closed[u] |= 1 << v
        closed[v] |= 1 << u
    size = 1 << n
    a = [0] * size
    even = [n % 2 == 0] * size                    # even[S]: n - |S| is even, i.e. the sign is +1
    for S in range(1, size):
        low = S & -S
        v = low.bit_length() - 1
        a[S] = a[S ^ low] + a[S & ~closed[v]] + 1
        even[S] = not even[S ^ low]               # adding one vertex flips the parity of n - |S|
    p = [1] * size
    for k in range(1, n + 1):
        total = 0
        for S in range(size):
            x = p[S] * a[S]
            p[S] = x
            if even[S]:
                total += x
            else:
                total -= x
        if total > 0:
            return k
    raise AssertionError("unreachable: n colours always suffice")
