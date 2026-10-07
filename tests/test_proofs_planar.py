"""Checks for pairs/planar-perfect-matchings-enumeration-vs-kasteleyn/PROOFS.md, sections 5-7 (the enumeration's
search tree, Kasteleyn's sign lemma on the a x b grid, the permanent remark, sizes of the numbers, space). The exact
counts (sections 1-4) are checked by the experiment scripts named in PROOFS.md.

The implementations are not modified: calls of the inner function `extend` are counted with sys.setprofile, and the
scan step `u += 1` with sys.settrace.

Run:  python -m unittest tests.test_proofs_planar   (a few seconds)
"""
import importlib.util
import inspect
import random
import sys
import tracemalloc
import unittest
from itertools import permutations
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "planar-perfect-matchings-enumeration-vs-kasteleyn"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "tpppm_harness")
EN_MOD = _load(ENTRY / "implementations" / "enumeration.py", "tpppm_enum")
KB_MOD = _load(ENTRY / "implementations" / "kasteleyn_bareiss.py", "tpppm_kast")
ENUM = EN_MOD.count_perfect_matchings_enumeration
KAST = KB_MOD.count_perfect_matchings_kasteleyn


def grid_edges(a, b):
    for r in range(a):
        for c in range(b):
            u = r * b + c
            if c + 1 < b:
                yield u, u + 1
            if r + 1 < a:
                yield u, u + b


def random_grid(a, b, rng, hi=3):
    return (a, b, H._matrix(a, b, lambda: rng.randint(0, hi)))


def perfect_matchings(a, b, W=None):
    """All perfect matchings (lists of edges) of the a x b grid, using only edges with W != 0 if W is given."""
    N = a * b
    adj = {u: [] for u in range(N)}
    for u, v in grid_edges(a, b):
        if W is None or W[u][v]:
            adj[u].append(v)
            adj[v].append(u)
    out = []
    matched = [False] * N

    def go(acc):
        u = next((x for x in range(N) if not matched[x]), None)
        if u is None:
            out.append(list(acc))
            return
        matched[u] = True
        for v in adj[u]:
            if not matched[v]:
                matched[v] = True
                acc.append((u, v))
                go(acc)
                acc.pop()
                matched[v] = False
        matched[u] = False

    go([])
    return out


def parity(perm):
    seen, sign = [False] * len(perm), 1
    for i in range(len(perm)):
        if not seen[i]:
            j, length = i, 0
            while not seen[j]:
                seen[j] = True
                j = perm[j]
                length += 1
            if length % 2 == 0:
                sign = -sign
    return sign


def colour_classes(a, b):
    N = a * b
    black = [u for u in range(N) if (u // b + u % b) % 2 == 0]
    white = [u for u in range(N) if (u // b + u % b) % 2 == 1]
    return black, white


class SignLemma(unittest.TestCase):
    def test_same_sign_for_every_matching_of_every_shape(self):
        shapes = 0
        for a in range(1, 17):
            for b in range(1, 17):
                N = a * b
                if N % 2 or N > 16:
                    continue
                black, white = colour_classes(a, b)
                bi = {x: i for i, x in enumerate(black)}
                wi = {y: j for j, y in enumerate(white)}
                signs = set()
                for M in perfect_matchings(a, b):
                    sigma = [None] * len(black)
                    eps = 1
                    for u, v in M:
                        x, y = (u, v) if u in bi else (v, u)
                        sigma[bi[x]] = wi[y]
                        rx, cx = divmod(x, b)
                        ry, cy = divmod(y, b)
                        if cx == cy and cx % 2 == 1:
                            eps = -eps
                    signs.add(parity(sigma) * eps)
                self.assertLessEqual(len(signs), 1, (a, b))
                shapes += 1
        self.assertGreaterEqual(shapes, 20)


class Permanent(unittest.TestCase):
    def test_permanent_of_black_white_matrix(self):
        for trial in range(60):
            rng = random.Random(f"tp-ppm-perm-{trial}")
            a, b = rng.choice([(a, b) for a in range(1, 7) for b in range(1, 7) if a * b % 2 == 0 and a * b <= 12])
            inst = random_grid(a, b, rng)
            W = inst[2]
            black, white = colour_classes(a, b)
            perm = 0
            for p in permutations(range(len(white))):
                prod = 1
                for i, j in enumerate(p):
                    prod *= W[black[i]][white[j]]
                    if not prod:
                        break
                perm += prod
            self.assertEqual(perm, KAST(inst))
            self.assertEqual(perm, ENUM(inst))
            self.assertEqual(perm, H.transfer_matrix_count(*inst))     # the harness oracle (PROOFS.md, section 8)


def profile_extend(inst):
    stats = {"calls": 0, "depth": 0, "max": 0}

    def prof(frame, event, arg):
        if frame.f_code.co_name != "extend":
            return
        if event == "call":
            stats["calls"] += 1
            stats["depth"] += 1
            stats["max"] = max(stats["max"], stats["depth"])
        elif event == "return":
            stats["depth"] -= 1

    sys.setprofile(prof)
    try:
        ENUM(inst)
    finally:
        sys.setprofile(None)
    return stats["calls"], stats["max"]


SRC_LINES, SRC_START = inspect.getsourcelines(EN_MOD.count_perfect_matchings_enumeration)
SCAN_LINE = SRC_START + next(i for i, line in enumerate(SRC_LINES) if line.strip() == "u += 1")


def scan_steps(inst):
    count = {"scan": 0, "calls": 0}

    def local(frame, event, arg):
        if event == "line" and frame.f_lineno == SCAN_LINE:
            count["scan"] += 1
        return local

    def tracer(frame, event, arg):
        if event == "call" and frame.f_code.co_name == "extend":
            count["calls"] += 1
            return local
        return None

    sys.settrace(tracer)
    try:
        ENUM(inst)
    finally:
        sys.settrace(None)
    return count["scan"], count["calls"]


class EnumerationTree(unittest.TestCase):
    def test_node_bound_and_depth(self):
        for trial in range(120):
            rng = random.Random(f"tp-ppm-tree-{trial}")
            a, b = rng.choice([(a, b) for a in range(1, 11) for b in range(1, 11) if 1 <= a * b <= 20])
            inst = random_grid(a, b, rng)
            N = a * b
            calls, depth = profile_extend(inst)
            leaves = len(perfect_matchings(a, b, inst[2])) if N % 2 == 0 else 0
            self.assertLess(calls, 2 ** (N // 2 + 1))
            self.assertGreaterEqual(calls, leaves)
            self.assertLessEqual(depth, N // 2 + 1)

    def test_prime_paths_are_linear(self):
        for N in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31):
            for a, b in ((1, N), (N, 1)):
                calls, _ = profile_extend((a, b, H._matrix(a, b, lambda: 1)))
                self.assertLessEqual(calls, N // 2 + 1)

    def test_ladder_scan_steps(self):
        for m in range(1, 21):
            steps, calls = scan_steps(H.ladder(m))
            self.assertLessEqual(steps, 2 * calls, m)


class Track:
    """Integer wrapper recording the largest absolute value of products/differences and of stored quotients."""
    big_mid = 0
    big_val = 0
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _x(o):
        return o.v if isinstance(o, Track) else o

    def _mid(self, r):
        Track.big_mid = max(Track.big_mid, abs(r))
        return Track(r)

    def __mul__(self, o):
        return self._mid(self.v * self._x(o))

    __rmul__ = __mul__

    def __sub__(self, o):
        return self._mid(self.v - self._x(o))

    def __rsub__(self, o):
        return self._mid(self._x(o) - self.v)

    def __floordiv__(self, o):
        r = self.v // self._x(o)
        Track.big_val = max(Track.big_val, abs(r))
        return Track(r)

    def __rfloordiv__(self, o):
        r = self._x(o) // self.v
        Track.big_val = max(Track.big_val, abs(r))
        return Track(r)

    def __neg__(self):
        return Track(-self.v)

    def __abs__(self):
        return Track(abs(self.v))

    def __eq__(self, o):
        return self.v == self._x(o)

    def __ne__(self, o):
        return self.v != self._x(o)

    def __bool__(self):
        return self.v != 0

    __hash__ = None


class NumberSizes(unittest.TestCase):
    def test_hadamard_bounds(self):
        for trial in range(60):
            rng = random.Random(f"tp-ppm-size-{trial}")
            a, b = rng.choice([(a, b) for a in range(2, 13) for b in range(2, 13) if a * b % 2 == 0 and a * b <= 36])
            hi = rng.choice((3, 10 ** 9))
            inst = random_grid(a, b, rng, hi)
            W = inst[2]
            wmax = max(max(r) for r in W)
            if wmax == 0:
                continue
            N = a * b
            Track.big_mid = Track.big_val = 0
            T = tuple(tuple(Track(x) for x in row) for row in W)
            out = KAST((a, b, T))
            self.assertEqual(out.v if isinstance(out, Track) else out, KAST(inst))
            self.assertLessEqual(Track.big_val, (2 * wmax) ** (N // 2))
            self.assertLessEqual(Track.big_mid, 2 * (2 * wmax) ** N)


class Space(unittest.TestCase):
    def test_kasteleyn_quadratic_peak(self):
        peaks = []
        for m in (16, 32, 64):
            inst = H.ladder(m)
            tracemalloc.start()
            KAST(inst)
            _, p = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            peaks.append(p)
        for x, y in zip(peaks, peaks[1:]):
            self.assertTrue(3.0 < y / x < 6.0, peaks)


if __name__ == "__main__":
    unittest.main()
