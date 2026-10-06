"""Instances: n >= 2 points in the plane with integer coordinates, as a tuple of (x, y) tuples.

generate mixes three kinds: coordinates in [0, 10^6) (generic position), coordinates in [0, sqrt(n) + 2)
(many duplicate points, distance 0, collinear points), and all points on one vertical line (every point
falls in the dividing strip). generate_scaling uses coordinates in [0, 10^9).
"""


def generate(n, rng):
    kind = rng.randrange(3)
    if kind == 0:
        return tuple((rng.randrange(10 ** 6), rng.randrange(10 ** 6)) for _ in range(n))
    if kind == 1:
        r = int(n ** 0.5) + 2
        return tuple((rng.randrange(r), rng.randrange(r)) for _ in range(n))
    x = rng.randrange(1000)
    return tuple((x, rng.randrange(10 ** 6)) for _ in range(n))


def generate_scaling(n, rng):
    return tuple((rng.randrange(10 ** 9), rng.randrange(10 ** 9)) for _ in range(n))


def check(points, output):
    """Exact oracle independent of both implementations: a plane sweep with pruning along the coordinate
    of larger spread (O(n^2) in the worst case, fast on the harness instances)."""
    k = 0 if (max(p[0] for p in points) - min(p[0] for p in points)
              >= max(p[1] for p in points) - min(p[1] for p in points)) else 1
    pts = sorted(points, key=lambda p: p[k])
    best = None
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            gap = pts[j][k] - pts[i][k]
            if best is not None and gap * gap >= best:
                break
            d = (pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2
            if best is None or d < best:
                best = d
    return output == best
