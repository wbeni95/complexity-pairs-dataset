"""Compare every pair of points: n(n-1)/2 squared distances, Theta(n^2) time."""


def closest_pair_brute(points) -> int:
    n = len(points)
    if n < 2:
        raise ValueError("need at least two points")
    best = None
    for i in range(n):
        xi, yi = points[i]
        for j in range(i + 1, n):
            xj, yj = points[j]
            dx = xi - xj
            dy = yi - yj
            d = dx * dx + dy * dy
            if best is None or d < best:
                best = d
    return best
