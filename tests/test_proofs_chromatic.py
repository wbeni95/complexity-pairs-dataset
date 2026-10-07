"""Deterministic checks for pairs/chromatic-number-subset-dp-vs-inclusion-exclusion/PROOFS.md (a few seconds).

Ranges: both algorithms on every graph with n <= 5 vertices and on seeded graphs up to n = 10 (sections 1, 2, 4);
the cover identity c_k = #covers for every graph with n <= 4 and k <= 3 (2.2, 2.3); the recurrence for a(S) on
seeded graphs n <= 8 (2.1); line-execution counts of the unchanged code: DP inner iterations n = 0..9 (1.4) and
inclusion-exclusion arithmetic operations n = 0..10 (2.5); bit lengths of the table entries and running sums
n = 1..12 (2.6); the chromatic numbers of the V2 timing instances n = 6..18 and the bit length of their largest table
entry n = 13..18 (section 5); tracemalloc peaks n = 6..14 (1.5, 2.7).
"""
import importlib.util
import itertools
import random
import sys
import tracemalloc
import unittest
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "chromatic-number-subset-dp-vs-inclusion-exclusion"
ENTRY_ID = "chromatic-number-subset-dp-vs-inclusion-exclusion"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "proofs_chrom_harness")
DP_MOD = _load(ENTRY / "implementations" / "subset_dp.py", "proofs_chrom_dp")
IE_MOD = _load(ENTRY / "implementations" / "inclusion_exclusion.py", "proofs_chrom_ie")
DP = DP_MOD.chromatic_subset_dp
IE = IE_MOD.chromatic_inclusion_exclusion


def chi_oracle(graph):
    n, edges = graph
    if n == 0:
        return 0
    return next(k for k in range(1, n + 1) if H._colourable(n, edges, k))


def independent(S, edges):
    return not any((S >> u) & 1 and (S >> v) & 1 for u, v in edges)


def a_brute(S, edges):
    """Number of non-empty independent subsets of S."""
    count, T = 0, S
    while T:
        count += independent(T, edges)
        T = (T - 1) & S
    return count


def line_numbers(module, *texts):
    lines = Path(module.__file__).read_text(encoding="utf-8").splitlines()
    out = []
    for text in texts:
        hits = [i + 1 for i, line in enumerate(lines) if line.strip() == text]
        assert len(hits) == 1, (text, hits)
        out.append(hits[0])
    return out


class LineTracer:
    """Counts executions of the given lines of one function's code object; optionally inspects locals."""

    def __init__(self, func, lines, inspect=None):
        self.code = func.__code__
        self.lines = set(lines)
        self.counts = {line: 0 for line in lines}
        self.inspect = inspect

    def _local(self, frame, event, arg):
        if event == "line":
            if frame.f_lineno in self.lines:
                self.counts[frame.f_lineno] += 1
            if self.inspect is not None:
                self.inspect(frame.f_locals)
        return self._local

    def _global(self, frame, event, arg):
        if frame.f_code is self.code:
            return self._local
        return None

    def run(self, func, arg):
        sys.settrace(self._global)
        try:
            return func(arg)
        finally:
            sys.settrace(None)


def all_graphs(n):
    pairs = list(itertools.combinations(range(n), 2))
    for bits in range(1 << len(pairs)):
        yield n, tuple(p for i, p in enumerate(pairs) if bits >> i & 1)


def seeded_graphs(n_values, per_n, tag):
    for n in n_values:
        for t in range(per_n):
            yield H.generate(n, random.Random(f"{tag}|{n}|{t}"))
        yield n, ()
        yield n, tuple(itertools.combinations(range(n), 2))


class Correctness(unittest.TestCase):
    def test_every_small_graph(self):
        for n in range(0, 6):
            for g in all_graphs(n):
                c = chi_oracle(g)
                self.assertEqual(DP(g), c, g)
                self.assertEqual(IE(g), c, g)

    def test_seeded_graphs(self):
        for g in seeded_graphs(range(6, 11), 6, "proofs-chrom"):
            c = chi_oracle(g)
            self.assertEqual(DP(g), c)
            self.assertEqual(IE(g), c)

    def test_harness_families(self):
        # PROOFS.md section 4: cycles 2 or 3, empty graph 1, complete graph n, disjoint triangles 3.
        for n in range(1, 11):
            empty = (n, ())
            complete = (n, tuple(itertools.combinations(range(n), 2)))
            self.assertEqual(IE(empty), 1)
            self.assertEqual(IE(complete), n)
            if n >= 3:
                cyc = (n, tuple(sorted((min(i, (i + 1) % n), max(i, (i + 1) % n)) for i in range(n))))
                self.assertEqual(IE(cyc), 3 if n % 2 else 2)
                tri = (n, tuple(sorted(e for t in range(n // 3)
                                       for e in ((3 * t, 3 * t + 1), (3 * t + 1, 3 * t + 2), (3 * t, 3 * t + 2)))))
                self.assertEqual(DP(tri), 3)


class CoverIdentity(unittest.TestCase):
    def test_c_k_counts_covers(self):
        for n in range(1, 5):
            full = (1 << n) - 1
            for g in all_graphs(n):
                edges = g[1]
                ind = [S for S in range(1, 1 << n) if independent(S, edges)]
                a = [a_brute(S, edges) for S in range(1 << n)]
                chi = chi_oracle(g)
                for k in range(1, 4):
                    c = sum((-1) ** (n - bin(S).count("1")) * a[S] ** k for S in range(1 << n))
                    covers = 0
                    for tup in itertools.product(ind, repeat=k):
                        u = 0
                        for S in tup:
                            u |= S
                        covers += u == full
                    self.assertEqual(c, covers, (g, k))
                    self.assertEqual(c > 0, chi <= k, (g, k))

    def test_a_recurrence(self):
        for g in seeded_graphs(range(1, 9), 4, "proofs-chrom-a"):
            n, edges = g
            nbr = [0] * n
            for u, v in edges:
                nbr[u] |= 1 << v
                nbr[v] |= 1 << u
            for S in range(1, 1 << n):
                for v in range(n):
                    if S >> v & 1:
                        rest = S & ~(1 << v)
                        self.assertEqual(a_brute(S, edges), a_brute(rest, edges) + a_brute(rest & ~nbr[v], edges) + 1)


class LineCounts(unittest.TestCase):
    def test_dp_inner_iterations(self):
        (tab, inner) = line_numbers(DP_MOD, "independent[S] = independent[rest] and not (adj[v] & rest)",
                                    "if independent[T]:")
        for g in seeded_graphs(range(0, 10), 2, "proofs-chrom-dp"):
            n = g[0]
            tr = LineTracer(DP, [tab, inner])
            tr.run(DP, g)
            self.assertEqual(tr.counts[inner], 3 ** n - 2 ** n)
            self.assertEqual(tr.counts[tab], 2 ** n - 1)

    def test_ie_arithmetic_operations(self):
        tab, mul, add, sub = line_numbers(IE_MOD, "a[S] = a[S ^ low] + a[S & ~closed[v]] + 1", "x = p[S] * a[S]",
                                          "total += x", "total -= x")
        for g in seeded_graphs(range(0, 11), 3, "proofs-chrom-ie"):
            n = g[0]
            tr = LineTracer(IE, [tab, mul, add, sub])
            chi = tr.run(IE, g)
            c = tr.counts
            self.assertEqual(c[tab], 2 ** n - 1 if n else 0)
            self.assertEqual(c[mul], chi * 2 ** n)
            self.assertEqual(c[add] + c[sub], chi * 2 ** n)
            self.assertEqual(2 * c[tab] + c[mul] + c[add] + c[sub], (2 * chi + 2) * 2 ** n - 2)

    def test_bit_lengths(self):
        graphs = list(seeded_graphs(range(1, 10), 2, "proofs-chrom-bits"))
        graphs += [H.generate_scaling(n, random.Random(f"{ENTRY_ID}|v2|{n}")) for n in (10, 11, 12)]
        for g in graphs:
            n = g[0]
            seen = {"x": 0, "total": 0}

            def inspect(loc):
                x = loc.get("x")
                t = loc.get("total")
                if isinstance(x, int):
                    seen["x"] = max(seen["x"], x.bit_length())
                if isinstance(t, int):
                    seen["total"] = max(seen["total"], abs(t).bit_length())

            chi = LineTracer(IE, [], inspect).run(IE, g)
            self.assertLessEqual(seen["x"], n * chi)
            self.assertLessEqual(seen["total"], n * (chi + 1))


class TimingInstances(unittest.TestCase):
    def test_chi_over_n(self):
        # PROOFS.md section 5: chi/n of the seeded V2 timing instances lies in [1/2, 5/7] for n = 6..18.
        expected = {6: 4, 7: 5, 8: 4, 9: 6, 10: 6, 11: 7, 12: 7, 13: 8, 14: 8, 15: 8, 16: 8, 17: 9, 18: 10}
        ratios = []
        for n, chi in expected.items():
            g = H.generate_scaling(n, random.Random(f"{ENTRY_ID}|v2|{n}"))
            self.assertEqual(IE(g), chi, n)
            ratios.append(Fraction(chi, n))
        self.assertEqual((min(ratios), max(ratios)), (Fraction(1, 2), Fraction(5, 7)))

    def test_largest_table_entry_bits(self):
        # PROOFS.md section 5: the largest table entry is a(V)^chi; its bit length on the V2 instances n = 13..18.
        expected_bits = {}
        for n in range(13, 19):
            n_, edges = H.generate_scaling(n, random.Random(f"{ENTRY_ID}|v2|{n}"))
            nbr = [0] * n
            for u, v in edges:
                nbr[u] |= 1 << v
                nbr[v] |= 1 << u
            ind = [False] * (1 << n)
            ind[0] = True
            for S in range(1, 1 << n):
                low = S & -S
                v = low.bit_length() - 1
                ind[S] = ind[S ^ low] and not (nbr[v] & S)
            a_full = sum(ind) - 1
            chi = IE((n, edges))
            expected_bits[n] = (a_full ** chi).bit_length()
            self.assertLessEqual(expected_bits[n], n * chi)
        self.assertEqual(expected_bits[18], 57)


class WorkingMemory(unittest.TestCase):
    @staticmethod
    def _peak(fn, arg):
        tracemalloc.start()
        tracemalloc.reset_peak()
        base = tracemalloc.get_traced_memory()[0]
        fn(arg)
        peak = tracemalloc.get_traced_memory()[1] - base
        tracemalloc.stop()
        return peak

    def test_tables_are_theta_two_to_the_n(self):
        for n in range(6, 15):
            g = H.generate_scaling(n, random.Random(f"proofs-chrom-mem|{n}"))
            ie = self._peak(IE, g) / 2 ** n
            dp = self._peak(DP, g) / 2 ** n
            self.assertTrue(8 <= ie <= 128, (n, ie))
            self.assertTrue(8 <= dp <= 32, (n, dp))


if __name__ == "__main__":
    unittest.main()
