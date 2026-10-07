"""Sort, then for each i scan the rest with two pointers.

Theta(n^2) time in the worst case, assuming the built-in sort runs in O(n log n): the scan makes at most
(n - 1)(n - 2)/2 pointer steps (n >= 1), exactly that many when there is no solution, and the sort adds O(n log n)
under that assumption (see PROOFS.md, section 2).
"""


def three_sum_quadratic(values) -> bool:
    a = sorted(values)
    n = len(a)
    for i in range(n - 2):
        j, k = i + 1, n - 1
        while j < k:
            s = a[i] + a[j] + a[k]
            if s == 0:
                return True
            if s < 0:
                j += 1
            else:
                k -= 1
    return False
