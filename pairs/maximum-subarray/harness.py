"""Instances: a list of n >= 1 integers drawn uniformly from [-100, 100] (negatives included).

The oracle is the CLRS (section 4.1) divide-and-conquer algorithm, Theta(n log n), which shares no code
or idea with the three implementations under test (it combines the best left half, right half and
crossing subarray).
"""


def generate(n, rng):
    if n < 1:
        raise ValueError("the problem is defined for n >= 1 (non-empty subarray)")
    r = rng.random()
    if r < 0.1:
        return [rng.randint(-100, -1) for _ in range(n)]   # all negative: answer is the max element
    if r < 0.2:
        return [rng.randint(0, 100) for _ in range(n)]     # all non-negative: answer is the total
    return [rng.randint(-100, 100) for _ in range(n)]


def _divide_and_conquer(a, lo, hi):
    """Best non-empty subarray sum of a[lo:hi], hi - lo >= 1."""
    if hi - lo == 1:
        return a[lo]
    mid = (lo + hi) // 2
    s, left = 0, None
    for i in range(mid - 1, lo - 1, -1):     # best crossing sum: best suffix of the left half ...
        s += a[i]
        left = s if left is None or s > left else left
    s, right = 0, None
    for j in range(mid, hi):                 # ... plus best prefix of the right half
        s += a[j]
        right = s if right is None or s > right else right
    return max(_divide_and_conquer(a, lo, mid), _divide_and_conquer(a, mid, hi), left + right)


def check(instance, output):
    return output == _divide_and_conquer(instance, 0, len(instance))
