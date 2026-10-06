"""Boolean matrix multiplication, schoolbook: C[i][j] = OR over k of (A[i][k] AND B[k][j]).

Entries are 0/1 integers. Every one of the n^3 terms is evaluated (no early exit at the first true term), so the
method performs exactly n^3 AND operations and n^3 OR operations on every input.
"""


def bmm_naive(instance):
    A, B = instance
    n = len(A)
    Bt = list(zip(*B))  # columns of B
    C = []
    for i in range(n):
        row = []
        for j in range(n):
            c = 0
            for k in range(n):
                c = c | (A[i][k] & Bt[j][k])
            row.append(c)
        C.append(row)
    return C
