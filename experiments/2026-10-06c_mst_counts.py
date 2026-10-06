"""Exact operation counts for pairs/minimum-spanning-tree-brute-vs-kruskal (count-based V2, round 2026-10-06c).

Question (RL-018, RL-061 item 3): Kruskal packs each edge into one integer key w*n^2 + u*n + v and sorts the
keys with the C built-in sorted(). Can the sort's comparisons be counted by harness instrumentation alone?

What it tries:
  1. Whether the packed key stays instrumented: with a CountingWeight w, w*nn + u*n + v is computed by
     CountingWeight.__mul__/__add__, so the key is a CountingWeight and sorted() calls its __lt__.
  2. Whether the UNCHANGED implementations return the same MST weight on CountingWeight matrices as on plain
     ints (scaling instances, and 200 random generate() instances, ties included).
  3. A breakdown of Kruskal's count with an experiment-only type that counts comparisons, additions,
     multiplications and divmods separately, cross-checked against (a) sorted() applied by this script to
     the same packed keys wrapped in a comparison-counting key and (b) the number of keys Kruskal scans,
     replayed on plain ints. Expected: total = 3m + sort comparisons + scanned keys, m = n(n-1)/2.
  4. Closed forms for the other two algorithms (they share generate_scaling): Prim (n-1)(n-2) comparisons +
     (n-1) additions = (n-1)^2; enumeration (n-1) C(m, n-1) additions + (n^(n-2) - 1) comparisons.
  5. Fits for candidate n ranges, claims and rivals (validator's eval_cost / fit_slope).

Run from the repository root:  PYTHONIOENCODING=utf-8 ./.venv/Scripts/python experiments/2026-10-06c_mst_counts.py
Deterministic. (Sort comparison counts are exact for a given CPython sort implementation; the cross-version
check is in experiments/2026-10-06c_count_v2_summary.py.)

Outcome (run 2026-10-06 under Python 3.14.2, and repeated under 3.12.10):
  1. The packed key is a CountingWeight (value equal to the plain key).
  2. Identical MST weights on all 200 random instances (3 algorithms each) and 4 scaling instances (Kruskal, Prim).
  3. Kruskal breakdown, n = 50 / 100 / 200 / 400 / 800, Python 3.14.2: total 14811 / 69526 / 319007 / 1438399 /
     6400007 = sort comparisons 11056 / 54453 / 258696 / 1197374 / 5437640 (equal to sorted() on the same keys)
     + 3m packing operations + scanned keys 80 / 223 / 611 / 1625 / 3567; total / (m log2 m) = 1.179 .. 1.095.
     Under 3.12.10 only the sort comparisons differ: 11011 / 54273 / 257991 / 1194571 / 5426551
     (totals 14766 / 69346 / 318302 / 1435596 / 6388918); the independent sorted() replay agrees in each version.
  4. Prim == (n-1)^2 exactly; enumeration == (n-1) C(m, n-1) + n^(n-2) - 1 exactly for n = 2..7
     (75 / 964 / 16310 / 342390 for n = 4..7).
  5. Kruskal vs n**2*log(n): alpha 0.9980 on n = 50..800 (0.9979 on 100..1200); rivals n**2 1.0941,
     n**2*log(n)**2 0.9173, n**3 0.7294, all rejected at 0.03. Prim vs n**2: 1.0066 (vs (n-1)**2: 1.0000); rivals
     n**2*log(n) 0.9181, n**3 0.6710 rejected. Enumeration vs n*C: 0.9954 (vs exact form 1.0000); rivals C 1.0652,
     n**2*C 0.9340, n**(n-2) 1.2104 rejected. CHOSEN: unchanged n_values and the existing leading-term cost
     expressions for all three.
"""
import importlib.util
import math
import random
from pathlib import Path

_s = importlib.util.spec_from_file_location("cv2h", Path(__file__).resolve().parent / "2026-10-07b_count_v2_helpers.py")
H = importlib.util.module_from_spec(_s)
_s.loader.exec_module(H)

E = "minimum-spanning-tree-brute-vs-kruskal"
entry_dir, entry, harness = H.entry_and_harness(E)
brute = H.V.load_callable(entry_dir, "implementations/brute_force.py:mst_brute")
kruskal = H.V.load_callable(entry_dir, "implementations/kruskal.py:mst_kruskal")
prim = H.V.load_callable(entry_dir, "implementations/prim.py:mst_prim")
CW = harness.CountingWeight


def plain(x):
    return x.v if isinstance(x, CW) else x


def wrap(W):
    return tuple(tuple(w if u == v else CW(w) for v, w in enumerate(row)) for u, row in enumerate(W))


# 1. the packed key is a CountingWeight
W = harness._scaling_draws(5, random.Random("mst-key"))
cw = wrap(W)
key = cw[1][3] * 25 + 1 * 5 + 3
print("type of the packed key built from a CountingWeight:", type(key).__name__, "value", key.v,
      "== plain", W[1][3] * 25 + 1 * 5 + 3)

# 2. answers unchanged
rng = random.Random("mst-eq")
for t in range(200):
    n = rng.randrange(1, 8)
    Wg = harness.generate(n, rng)
    for fn in (brute, kruskal, prim):
        assert plain(fn(wrap(Wg))) == fn(Wg), (t, n, fn.__name__)
for n in [20, 50, 100, 200]:
    Ws = harness._scaling_draws(n, random.Random(f"mst-eq|{n}"))
    for fn in (kruskal, prim):
        assert plain(fn(wrap(Ws))) == fn(Ws), (n, fn.__name__)
print("MST weights on CountingWeight matrices == on plain ints: OK (200 random n <= 7, 4 scaling n = 20..200)")


# 3. Kruskal breakdown
class Probe:
    cnt = {"cmp": 0, "add": 0, "mul": 0, "divmod": 0}
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _u(x):
        return x.v if isinstance(x, Probe) else x

    def __add__(self, o):
        Probe.cnt["add"] += 1
        return Probe(self.v + self._u(o))

    __radd__ = __add__

    def __mul__(self, o):
        Probe.cnt["mul"] += 1
        return Probe(self.v * self._u(o))

    __rmul__ = __mul__

    def __divmod__(self, o):
        Probe.cnt["divmod"] += 1
        return divmod(self.v, self._u(o))

    def __lt__(self, o):
        Probe.cnt["cmp"] += 1
        return self.v < self._u(o)


class SortKey:
    c = 0
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __lt__(self, o):
        SortKey.c += 1
        return self.v < o.v


def scanned_keys(Wp):
    """Replay of Kruskal's scan on plain ints: number of keys read before n - 1 edges are taken."""
    n = len(Wp)
    nn = n * n
    keys = sorted(Wp[u][v] * nn + u * n + v for u in range(n) for v in range(u + 1, n))
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    taken = scanned = 0
    for key in keys:
        if taken == n - 1:
            break
        scanned += 1
        rest = key % nn
        ru, rv = find(rest // n), find(rest % n)
        if ru != rv:
            parent[rv] = ru
            taken += 1
    return scanned


print("\nKruskal breakdown on the validator's scaling instances:")
print(f"{'n':>5} {'m':>7} {'total':>9} {'cmp':>9} {'add':>7} {'mul':>7} {'divmod':>6} {'sortcmp(indep)':>14} {'scanned':>7} {'total/(m log2 m)':>16}")
for n in [50, 100, 200, 400, 800]:
    Wp = harness._scaling_draws(n, random.Random(f"{E}|v2|{n}"))
    m = n * (n - 1) // 2
    inst = harness.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
    total = harness.reported_cost(kruskal(inst))
    for k in Probe.cnt:
        Probe.cnt[k] = 0
    kruskal(tuple(tuple(w if u == v else Probe(w) for v, w in enumerate(row)) for u, row in enumerate(Wp)))
    c = dict(Probe.cnt)
    nn = n * n
    SortKey.c = 0
    sorted(SortKey(Wp[u][v] * nn + u * n + v) for u in range(n) for v in range(u + 1, n))
    s = scanned_keys(Wp)
    assert c["add"] == 2 * m and c["mul"] == m and c["cmp"] == SortKey.c and c["divmod"] == s
    assert total == sum(c.values()) == 3 * m + SortKey.c + s
    print(f"{n:5d} {m:7d} {total:9d} {c['cmp']:9d} {c['add']:7d} {c['mul']:7d} {c['divmod']:6d} {SortKey.c:14d} {s:7d} "
          f"{total / (m * math.log2(m)):16.4f}")
print("Kruskal total == 3m + sort comparisons + scanned keys: OK")

# 4. Prim and enumeration closed forms
for n in [2, 3, 10, 50, 100, 200, 400, 800]:
    inst = harness.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
    assert harness.reported_cost(prim(inst)) == (n - 1) ** 2, n
print("Prim count == (n-1)^2 for n = 2, 3, 10, 50..800")
for n in [2, 3, 4, 5, 6, 7]:
    m = n * (n - 1) // 2
    inst = harness.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
    c = harness.reported_cost(brute(inst))
    assert c == (n - 1) * math.comb(m, n - 1) + n ** (n - 2) - 1, (n, c)
    print(f"  enumeration n={n}: count {c} = (n-1) C(m, n-1) + n^(n-2) - 1 = {n - 1}*{math.comb(m, n - 1)} + {n ** (n - 2)} - 1")

# 5. fits
TOL = 0.03
C = "factorial(n*(n-1)/2) / (factorial(n-1) * factorial(n*(n-1)/2 - n + 1))"
for ns in ([50, 100, 200, 400, 800], [100, 200, 400, 800, 1200]):
    vals = H.counts(E, "Kruskal with union-find", ns)
    H.report("Kruskal vs n**2*log(n)", ns, vals, "n**2*log(n)", ["n**2", "n**2*log(n)**2", "n**3"], TOL)
ns = [50, 100, 200, 400, 800]
vals = H.counts(E, "Prim, array version", ns)
H.report("Prim vs (n-1)**2", ns, vals, "(n-1)**2", ["n**2*log(n)", "n*log(n)", "n**3"], TOL)
H.report("Prim vs n**2", ns, vals, "n**2", ["n**2*log(n)"], TOL)
for ns in ([4, 5, 6, 7],):
    vals = H.counts(E, "enumeration of all (n-1)-edge subsets", ns)
    H.report("enumeration vs exact form", ns, vals, f"(n-1) * {C} + n**(n-2) - 1",
             [C, f"n**2 * {C}", "n**(n-2)"], TOL)
    H.report("enumeration vs n*C", ns, vals, f"n * {C}", [C, f"n**2 * {C}"], TOL)
