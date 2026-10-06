"""Shamos-Hoey divide and conquer: Theta(n log n) time.

Sort the points by x once. Recursively solve the left and right halves; each call also returns its
points sorted by y, obtained by merging the two halves' y-sorted lists in linear time (no re-sorting,
so the recurrence is T(n) = 2 T(n/2) + Theta(n), not n log^2 n). With delta^2 = the better of the two
halves, only points within horizontal distance delta of the dividing line can form a closer cross pair,
and in y order each of them needs to be compared only with the next few (at most 7) strip points.

Distances are squared and coordinates are integers, so all comparisons are exact.
"""


def closest_pair_dc(points) -> int:
    if len(points) < 2:
        raise ValueError("need at least two points")
    px = sorted(points)  # by x (ties by y)
    best, _ = _solve(px, 0, len(px))
    return best


def _dist2(p, q):
    dx = p[0] - q[0]
    dy = p[1] - q[1]
    return dx * dx + dy * dy


def _solve(px, lo, hi):
    """(min squared distance among px[lo:hi], those points sorted by y); requires hi - lo >= 2."""
    if hi - lo <= 3:
        best = min(_dist2(px[i], px[j]) for i in range(lo, hi) for j in range(i + 1, hi))
        return best, sorted(px[lo:hi], key=lambda p: p[1])
    mid = (lo + hi) // 2
    xm = px[mid][0]  # left half has x <= xm, right half has x >= xm
    best_l, left = _solve(px, lo, mid)
    best_r, right = _solve(px, mid, hi)
    best = min(best_l, best_r)

    # Merge the two y-sorted lists: Theta(n).
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i][1] <= right[j][1]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])

    # Strip around the dividing line, in y order.
    strip = [p for p in merged if (p[0] - xm) ** 2 < best]
    for a in range(len(strip)):
        xa, ya = strip[a]
        for b in range(a + 1, len(strip)):
            xb, yb = strip[b]
            dy = yb - ya
            if dy * dy >= best:
                break  # every later strip point is even farther away in y
            dx = xb - xa
            d = dx * dx + dy * dy
            if d < best:
                best = d
    return best, merged
