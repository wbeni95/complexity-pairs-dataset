"""3XOR by testing all triples: Theta(n^3) in the worst case.

Input: (w, values), values a tuple of n integers in [0, 2^w). Output: indices (i, j, k) with i < j < k and
values[i] ^ values[j] ^ values[k] == 0, or None if there is no such triple.

For every pair i < j the target t = values[i] ^ values[j] is computed once, and the k > j are scanned for
values[k] == t. On an instance without a solution this makes exactly C(n, 2) XORs and C(n, 3) equality tests,
C(n + 1, 3) = (n^3 - n) / 6 word operations in total; with a solution it stops at the first hit.
"""


def three_xor_all_triples(instance):
    w, values = instance
    n = len(values)
    for i in range(n):
        for j in range(i + 1, n):
            t = values[i] ^ values[j]
            for k in range(j + 1, n):
                if values[k] == t:
                    return (i, j, k)
    return None
