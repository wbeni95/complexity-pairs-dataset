"""Sort, then for each i scan the rest with two pointers: Theta(n^2) time (sorting adds n log n)."""


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
