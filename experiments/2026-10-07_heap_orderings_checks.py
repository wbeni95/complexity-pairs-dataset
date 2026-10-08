#!/usr/bin/env python3
"""Checks for pairs/max-heap-orderings-dp-vs-knuth-window-vs-heap-formula (deterministic, about half a minute).

Every number quoted in the entry's README and verification field is printed here. The tree enumerations, the
linear-extension counts and the layout computations below are written independently of the implementations.

Sections:
  A  hook length formula: the number of heap orderings of every binary tree with N <= 7 nodes, counted over all N!
     labellings, equals N! / prod |T_v|; the binomial recurrence agrees for every tree with N <= 11 nodes.
  B  Theorem H: over all binary trees with N <= 13 nodes (explicit enumeration), the minimum hook product equals the
     hook product of the heap-shaped tree; maxima of the number of heap orderings.
  C  algorithms: DP = window = heap formula for N <= 300 and N = 600, window = heap formula for N <= 5000;
     = the minimum over all hook products (N <= 20) and = the explicit formula of Cleary-Fischer-St. John
     (N <= 5000, consistency check); L(d) is an optimal root split for every d <= 600; the window's choice is
     L(d) for d <= 5000; T(d) is contained in {L(d), R(d)} for d <= 600 (the hypothesis of the conditional remark in
     PROOFS.md section 10).
  D  Lemma H: L(d) against the array layout, L(d) - L(d-1) in {0, 1}, d - 1 - L(d) <= L(d), one root subtree is
     perfect (d <= 20000); the root subtrees of the layout are heap-shaped, and the layout is the complete tree
     (fully balanced tree with cherries added from the left), d < 600.
  E  exact counts with the harness's counting integer: DP N(N+1) and window 4N - 2 for N <= 300; heap formula
     2 * (distinct arguments >= 2), between 2 (floor(log2((N+1)/3)) + 1) and 4 floor(log2(N+1)) - 2 for
     N <= 20000, = 4k - 4 at N = 2^k (k = 2..20), = 4k - 2 at N = 3 * 2^(k-1) (k = 1..20), which equals the upper
     bound 4 floor(log2(N+1)) - 2 for k >= 2 (and at N = 2) but not at k = 1 (N = 3: 2 multiplications, bound 6).
  F  Lemma B: 2^((N-1)/2) <= H(N) < 2^(4N) for N <= 5000; H(d) <= H(d + 1) for d < 5000.
  G  values and memory: every value multiplied or compared by the three implementations is at most H(N) or a product
     H(t) H(t') with t + t' <= N - 1 (N <= 120), and has at most 4N bits (N <= 120 for all three, N <= 1000 for
     the window, N <= 2000 for the heap formula); the heap formula's memo has |A(N)| entries and its recursion depth
     is at most |A(N)| + 1 (N <= 20000); the DP's and the window's list has N + 1 entries (N <= 300).
  O  oracle control: deliberately wrong outputs are rejected, true outputs accepted.
Output: one [PASS] / [FAIL] line per check; the run ends with ALL CHECKS PASSED (exit code 0) or a list of the failed
checks (exit code 1). The section references are to the entry's PROOFS.md.
Usage (from the repository root): python experiments/2026-10-07_heap_orderings_checks.py
"""
import importlib.util
import itertools
import math
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "max-heap-orderings-dp-vs-knuth-window-vs-heap-formula"
FAIL = []


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "heap_orderings_harness")
DP = load(ENTRY / "implementations" / "dp.py", "heap_orderings_dp").min_hook_product_dp
WIN = load(ENTRY / "implementations" / "knuth_window.py", "heap_orderings_window").min_hook_product_window
HEAP = load(ENTRY / "implementations" / "heap_formula.py", "heap_orderings_heap").min_hook_product_heap


def report(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAIL.append(label)


# ------------------------------------------------------------------------------------------------ trees
def trees(n):
    """All binary trees with n nodes as nested tuples (left, right); () is the empty tree."""
    if n == 0:
        return [()]
    out = []
    for t in range(n):
        for a in trees(t):
            for b in trees(n - 1 - t):
                out.append((a, b))
    return out


def trees_iter(n):
    """All binary trees with n nodes, generated one by one as (left, right) tuples."""
    if n == 0:
        yield ()
        return
    for t in range(n):
        lefts = list(trees_iter(t))
        for b in trees_iter(n - 1 - t):
            for a in lefts:
                yield (a, b)


def size(T):
    return 0 if T == () else 1 + size(T[0]) + size(T[1])


def size_and_hook(T):
    if T == ():
        return 0, 1
    sa, ha = size_and_hook(T[0])
    sb, hb = size_and_hook(T[1])
    d = sa + sb + 1
    return d, d * ha * hb


def hook(T):
    if T == ():
        return 1
    return size(T) * hook(T[0]) * hook(T[1])


def canon(T):
    if T == ():
        return ()
    return tuple(sorted((canon(T[0]), canon(T[1]))))


def nodes_with_parent(T):
    """Label nodes 0..n-1 in preorder; return the parent array (root: -1)."""
    parent = []

    def walk(S, p):
        if S == ():
            return
        me = len(parent)
        parent.append(p)
        walk(S[0], me)
        walk(S[1], me)

    walk(T, -1)
    return parent


def count_heap_orderings_brute(T):
    parent = nodes_with_parent(T)
    n = len(parent)
    cnt = 0
    for lab in itertools.permutations(range(1, n + 1)):
        if all(parent[v] < 0 or lab[parent[v]] < lab[v] for v in range(n)):
            cnt += 1
    return cnt


def count_heap_orderings_rec(T):
    if T == ():
        return 1
    a, b = size(T[0]), size(T[1])
    return math.comb(a + b, a) * count_heap_orderings_rec(T[0]) * count_heap_orderings_rec(T[1])


def heap_tree(d):
    """The heap-shaped tree with d nodes (array layout 1..d, children 2v, 2v + 1) as nested tuples."""
    def build(v):
        if v > d:
            return ()
        return (build(2 * v), build(2 * v + 1))
    return build(1)


def layout_left(d):
    """Number of nodes in the subtree of array index 2 of the layout 1..d (counted level by level)."""
    cnt, start, width = 0, 2, 1
    while start <= d:
        cnt += min(d, start + width - 1) - start + 1
        start, width = 2 * start, 2 * width
    return cnt


heap_left = load(ENTRY / "implementations" / "heap_formula.py", "heap_orderings_heap_left").heap_left


# ------------------------------------------------------------------------------------------------ sections
def section_a():
    bad = tot = 0
    for n in range(0, 8):
        for T in trees(n):
            tot += 1
            bad += count_heap_orderings_brute(T) * hook(T) != math.factorial(n)
    report("A hook length formula by counting all labellings, every tree with N <= 7 nodes", bad == 0,
           f"{tot - bad}/{tot} trees")
    bad = tot = 0
    for n in range(0, 12):
        for T in trees(n):
            tot += 1
            bad += count_heap_orderings_rec(T) * hook(T) != math.factorial(n)
    report("A binomial recurrence = N!/prod|T_v|, every tree with N <= 11 nodes", bad == 0, f"{tot - bad}/{tot} trees")


def section_b():
    rows = []
    ok = True
    for n in range(1, 14):
        best = None
        count = 0
        # enumerate the hook products of all trees with n nodes explicitly, tree by tree (no value sets)
        for T in trees_iter(n):
            v = size_and_hook(T)[1]
            count += 1
            if best is None or v < best:
                best = v
        ok &= best == hook(heap_tree(n))
        rows.append((n, count, math.factorial(n) // best))
    report("B Theorem H: the minimum hook product over all binary trees with N nodes is that of the heap-shaped tree,"
           " N = 1..13", ok, f"{sum(r[1] for r in rows)} trees; (N, trees, max heap orderings) = " + str(rows))


def section_c():
    t = time.time()
    # own table of H(0..600) by the recurrence (one pass), for the optimal-split check below
    hd = [1]
    for d in range(1, 601):
        hd.append(d * min(hd[s] * hd[d - 1 - s] for s in range(d)))
    ns = list(range(0, 301)) + [600]
    report("C DP implementation = window = heap formula = own table of the recurrence for every N <= 300 and N = 600",
           all(DP((n, 1)) == WIN((n, 1)) == HEAP((n, 1)) == hd[n] for n in ns), f"{len(ns)} values of N")
    report("C window = heap formula for N <= 5000", all(WIN((n, 1)) == HEAP((n, 1)) for n in range(0, 5001)),
           "5001 values of N")
    report("C = minimum over the hook products of all trees, N <= 20",
           all(hd[n] == min(H._all_hook_products(n)) for n in range(0, 21)), "21 values of N")
    report("C = explicit formula of Cleary-Fischer-St. John (Corollary 18 with Theorem 17), N <= 5000 (consistency)",
           all(HEAP((n, 1)) == H.cfs_formula(n) for n in range(0, 5001)), "5001 values of N")
    # optimal root splits of the DP
    bad = bad_t = 0
    for d in range(1, 601):
        F = [hd[s] * hd[d - 1 - s] for s in range(d)]
        m = min(F)
        bad += F[heap_left(d)] != m
        T = {s for s in range(d) if F[s] == m}
        bad_t += not T <= {heap_left(d), d - 1 - heap_left(d)}
    report("C L(d) is an optimal root split (L(d) in T(d)) for every d <= 600", bad == 0, f"{600 - bad}/600 sizes")
    report("C T(d) is contained in {L(d), R(d)} for every d <= 600 (hypothesis of the conditional remark)",
           bad_t == 0, f"{600 - bad_t}/600 sizes")
    # window trajectory (re-run of the window rule with an explicit trajectory)
    hval, tau, bad = [1], -1, 0
    for d in range(1, 5001):
        lo, hi = max(tau, 0), min(tau + 1, d - 1)
        best = bt = None
        for s in range(lo, hi + 1):
            v = hval[s] * hval[d - 1 - s]
            if best is None or v <= best:
                best, bt = v, s
        hval.append(d * best)
        tau = bt
        bad += tau != heap_left(d)
    report("C window choice tau(d) = L(d) for every d <= 5000", bad == 0, f"{5000 - bad}/5000 sizes")
    print(f"   section C: {time.time() - t:.1f} s")


def section_d():
    N = 20000
    report("D L(d) formula = subtree size of index 2 in the layout, d <= 20000",
           all(heap_left(d) == layout_left(d) for d in range(1, N + 1)), f"{N} sizes")
    report("D L(d) - L(d-1) in {0, 1} for 2 <= d <= 20000",
           all(heap_left(d) - heap_left(d - 1) in (0, 1) for d in range(2, N + 1)), f"{N - 1} sizes")
    report("D d - 1 - L(d) <= L(d) for d <= 20000", all(d - 1 - heap_left(d) <= heap_left(d) for d in range(1, N + 1)),
           f"{N} sizes")

    def perfect(k):
        return k + 1 > 0 and (k + 1) & k == 0

    def big_h(k):
        return (k + 1).bit_length() - 1

    ok3 = True
    for d in range(1, N + 1):
        a, b = heap_left(d), d - 1 - heap_left(d)
        if not (perfect(a) or perfect(b)):
            ok3 = False
        for s_, o_ in ((a, b), (b, a)):
            if perfect(s_) and not perfect(o_) and big_h(o_) != big_h(d) - 1:
                ok3 = False
            if perfect(s_) and big_h(s_) > big_h(d):
                ok3 = False
    report("D one root subtree of the heap is perfect (2^j - 1 nodes, j <= H), and a non-perfect sibling has "
           "floor(log2(size + 1)) = H - 1, d <= 20000", ok3, f"{N} sizes")
    ok = True
    for d in range(1, 600):
        T = heap_tree(d)
        ok &= T[0] == heap_tree(heap_left(d)) and T[1] == heap_tree(d - 1 - heap_left(d))
    report("D the root subtrees of the layout are the heap-shaped trees with L(d) and d - 1 - L(d) nodes, d < 600", ok,
           "599 sizes")

    def complete_tree(leaves):
        """Fully balanced tree with 2^floor(log2 leaves) leaves, leftmost leaves replaced by cherries; internal
        nodes as (left, right), leaves as ()."""
        H = leaves.bit_length() - 1
        extra = [leaves - (1 << H)]

        def build(depth):
            if depth == H:
                if extra[0] > 0:
                    extra[0] -= 1
                    return ((), ())
                return ()
            left = build(depth + 1)
            return (left, build(depth + 1))

        return build(0)

    report("D the heap-shaped tree with d nodes is the complete tree with d + 1 leaves, d < 600",
           all(complete_tree(d + 1) == heap_tree(d) for d in range(1, 600)), "599 sizes")


def mb_hook(d):
    """Hook product of the maximally balanced tree (root splits as equal as possible, larger part left)."""
    return 1 if d <= 1 else d * mb_hook(d // 2) * mb_hook((d - 1) // 2)


def distinct_args(n):
    seen, stack = set(), [n]
    while stack:
        d = stack.pop()
        if d in seen:
            continue
        seen.add(d)
        if d >= 2:
            left = heap_left(d)
            stack += [left, d - 1 - left]
    return {d for d in seen if d >= 2}


def counted(fn, n):
    inst = H.generate_scaling(n, None)
    fn(inst)
    return H.counts_by_kind()


def section_e():
    bad = 0
    for n in range(0, 301):
        c = counted(DP, n)
        bad += (c["mul"], c["cmp"]) != (n * (n + 3) // 2, n * (n - 1) // 2)
    report("E DP: exactly N(N+3)/2 multiplications and N(N-1)/2 comparisons, N = 0..300", bad == 0,
           f"{301 - bad}/301 values of N")
    bad = 0
    for n in range(1, 301):
        c = counted(WIN, n)
        bad += (c["mul"], c["cmp"]) != (3 * n - 1, n - 1)
    report("E window: exactly 3N - 1 multiplications and N - 1 comparisons, N = 1..300 (N = 0: none)",
           bad == 0 and counted(WIN, 0) == {"mul": 0, "cmp": 0}, f"{301 - bad}/301 values of N")
    bad = worst = 0
    for n in range(0, 20001):
        c = counted(HEAP, n)
        da = len(distinct_args(n))
        hh = (n + 1).bit_length() - 1
        lower = 2 * ((n + 1) // 3).bit_length() if n >= 2 else 0   # 2 (floor(log2((N+1)/3)) + 1)
        bad += c["cmp"] != 0 or c["mul"] != 2 * da or (n >= 2 and not lower <= c["mul"] <= 4 * hh - 2)
        if n >= 2:
            worst = max(worst, c["mul"] - (4 * hh - 2))
    report("E heap formula: 2 multiplications per distinct argument >= 2, no comparisons, between "
           "2 (floor(log2((N+1)/3)) + 1) and 4 floor(log2(N+1)) - 2 multiplications, N <= 20000", bad == 0,
           f"{20001 - bad}/20001 values of N; max excess over the upper bound {worst}")
    rows = [(k, counted(HEAP, 2 ** k)["mul"]) for k in range(1, 21)]
    report("E heap formula: exactly 4k - 4 multiplications at N = 2^k, k = 2..20",
           all(m == 4 * k - 4 for k, m in rows if k >= 2), str(rows))
    rows = [(k, counted(HEAP, 3 * 2 ** (k - 1))["mul"]) for k in range(1, 21)]
    bound = lambda n: 4 * ((n + 1).bit_length() - 1) - 2  # noqa: E731
    report("E heap formula: exactly 4k - 2 multiplications at N = 3 * 2^(k-1), k = 1..20",
           all(m == 4 * k - 2 for k, m in rows), str(rows))
    report("E heap formula: the upper bound 4 floor(log2(N+1)) - 2 is attained at N = 3 * 2^(k-1) for k = 2..20 and at"
           " N = 2, and not at k = 1 (N = 3: 2 multiplications, bound 6)",
           all(m == bound(3 * 2 ** (k - 1)) for k, m in rows if k >= 2) and counted(HEAP, 2)["mul"] == bound(2) == 2
           and rows[0] == (1, 2) and bound(3) == 6, "19 values of k and N = 2, 3")
    v2 = {"dp": [(n, sum(counted(DP, n).values())) for n in (16, 32, 64, 128, 256)],
          "window": [(n, sum(counted(WIN, n).values())) for n in (64, 256, 1024, 4096, 16384)],
          "heap": [(n, sum(counted(HEAP, n).values())) for n in (8, 32, 128, 512, 2048, 8192, 32768, 131072)]}
    report("E V2 points equal the closed forms N(N+1), 4N - 2, 4 log2(N) - 4",
           all(c == n * (n + 1) for n, c in v2["dp"]) and all(c == 4 * n - 2 for n, c in v2["window"])
           and all(c == 4 * (n.bit_length() - 1) - 4 for n, c in v2["heap"]), str(v2))


def section_f():
    hv = [HEAP((n, 1)) for n in range(0, 5001)]
    report("F 2^((N-1)/2) <= H(N) < 2^(4N) for 1 <= N <= 5000",
           all(hv[n] ** 2 >= 2 ** (n - 1) and hv[n] < 2 ** (4 * n) for n in range(1, 5001)), "5000 values of N")
    report("F monotonicity H(d) <= H(d + 1) for 0 <= d < 5000", all(hv[d] <= hv[d + 1] for d in range(5000)),
           "5000 values of d")


class Rec:
    """An integer that records every value it takes part in when multiplied or compared (operands and results)."""
    __slots__ = ("v",)
    seen = []

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _v(x):
        return x.v if isinstance(x, Rec) else x

    def __mul__(self, o):
        r = self.v * self._v(o)
        Rec.seen.extend((self.v, self._v(o), r))
        return Rec(r)

    __rmul__ = __mul__

    def _cmp(self, o, f):
        Rec.seen.extend((self.v, self._v(o)))
        return f(self.v, self._v(o))

    def __lt__(self, o):
        return self._cmp(o, lambda a, b: a < b)

    def __le__(self, o):
        return self._cmp(o, lambda a, b: a <= b)


def section_g():
    hv = [HEAP((n, 1)) for n in range(0, 2001)]
    bad_form = bad_bits = runs = values = 0
    for fn, top in ((DP, 120), (WIN, 1000), (HEAP, 2000)):
        for n in range(1, top + 1):
            Rec.seen = []
            out = fn((n, Rec(1)))
            runs += 1
            values += len(Rec.seen)
            bad_bits += out.v != hv[n] or any(v.bit_length() > 4 * n for v in Rec.seen)
            if n <= 120:
                prods = {hv[t] * hv[u] for t in range(n) for u in range(n - t)}
                bad_form += any(not (v <= hv[n] or v in prods) for v in Rec.seen)
    report("G every value multiplied or compared is at most H(N) or a product H(t) H(t') with t + t' <= N - 1 "
           "(N <= 120, all three)", bad_form == 0, f"{360 - bad_form}/360 runs")
    report("G every value multiplied or compared has at most 4N bits (N <= 120 for the DP, N <= 1000 for the window, "
           "N <= 2000 for the heap formula)", bad_bits == 0, f"{runs - bad_bits}/{runs} runs, {values} recorded values")
    # memory: memo size and recursion depth of the heap formula, list length of the DP and the window
    code_heap = HEAP.__code__
    code_hook = next(c for c in code_heap.co_consts if getattr(c, "co_name", None) == "hook")
    bad = 0
    for n in range(0, 20001):
        state = {"depth": 0, "max": 0, "memo": None}

        def prof(frame, event, arg):
            if frame.f_code is code_hook:
                if event == "call":
                    state["depth"] += 1
                    state["max"] = max(state["max"], state["depth"])
                elif event == "return":
                    state["depth"] -= 1
            elif frame.f_code is code_heap and event == "return":
                state["memo"] = len(frame.f_locals["memo"])

        sys.setprofile(prof)
        try:
            HEAP((n, 1))
        finally:
            sys.setprofile(None)
        a = len(distinct_args(n))
        bad += state["memo"] != a or state["max"] > a + 1
    report("G heap formula: the memo has |A(N)| entries and the recursion depth of hook is at most |A(N)| + 1",
           bad == 0, f"N = 0..20000: {20001 - bad}/20001")
    bad = 0
    for fn in (DP, WIN):
        code = fn.__code__
        for n in range(0, 301):
            got = []

            def prof2(frame, event, arg):
                if frame.f_code is code and event == "return":
                    got.append(len(frame.f_locals["h"]))

            sys.setprofile(prof2)
            try:
                fn((n, 1))
            finally:
                sys.setprofile(None)
            bad += got != [n + 1]
    report("G the DP and the window keep a list of N + 1 values", bad == 0, f"N = 0..300: {602 - bad}/602 runs")


def section_o():
    rejected = presented = accepted = 0
    for n in list(range(0, 41)) + [64, 100, 255, 256, 1000, 4095, 5000]:
        true = HEAP((n, 1))
        accepted += H.check((n, 1), true) is True
        wrong = {true + 1, true - 1, 2 * true}
        if 2 <= n <= 300:
            wrong |= {math.factorial(n), mb_hook(n)}      # the path (caterpillar) and the maximally balanced tree
        wrong.discard(true)
        for w in wrong:
            presented += 1
            rejected += H.check((n, 1), w) is False
        presented += 2
        rejected += H.check((n, 1), str(true)) is False         # wrong types
        rejected += H.check((n, 1), [true]) is False
    report("O oracle: every wrong value rejected, every true value accepted", rejected == presented and accepted == 48,
           f"{rejected}/{presented} wrong rejected, {accepted}/48 true accepted")


def main():
    t0 = time.time()
    for fn in (section_a, section_b, section_c, section_d, section_e, section_f, section_g, section_o):
        fn()
    print(f"total {time.time() - t0:.1f} s")
    if FAIL:
        print(f"FAILED: {len(FAIL)} check(s): {FAIL}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
