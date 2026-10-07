"""Checks of the proofs in pairs/two-sat-brute-force-vs-scc/PROOFS.md (sections 3 to 9).

Every check runs the unchanged implementations on fixed inputs (an exhaustive small family and seeded random
formulas): correctness of brute force and of Aspvall-Plass-Tarjan, the components computed by the iterative Tarjan
search (exactly the strongly connected components, numbered in reverse topological order), the linear work and
space of the search, the brute-force worst case for every m, the invariance of the brute-force count under renaming
and negation, and the probability 1/4 in the caveats. Runs in a few seconds.
"""
import importlib.util
import itertools
import random
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = "pairs/two-sat-brute-force-vs-scc/"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TR = _load("tests/_proof_trace.py", "tp_2sat_trace")


def node(l):
    return 2 * (abs(l) - 1) + (l < 0)


def satisfies(clauses, mask):
    return all(any(((mask >> (abs(l) - 1)) & 1) == (l > 0) for l in cl) for cl in clauses)


def graph(n, clauses):
    """Implication graph built independently: clause (a OR b) gives NOT a -> b and NOT b -> a; (a) is (a OR a)."""
    adj = [[] for _ in range(2 * n)]
    for cl in clauses:
        a, b = cl[0], cl[-1]
        adj[node(-a)].append(node(b))
        adj[node(-b)].append(node(a))
    return adj


def reach(adj):
    out = []
    for s in range(len(adj)):
        seen = {s}
        stack = [s]
        while stack:
            u = stack.pop()
            for w in adj[u]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        out.append(seen)
    return out


def random_2cnf(n, rng, empty_prob=0.0):
    clauses = []
    for _ in range(rng.randint(0, 3 * n + 1)):
        r = rng.random()
        if r < empty_prob:
            clauses.append(())
        elif r < 0.15:
            clauses.append((rng.choice((-1, 1)) * rng.randint(1, n),))
        else:
            clauses.append(tuple(rng.choice((-1, 1)) * rng.randint(1, n) for _ in range(2)))
    return n, tuple(clauses)


def small_family():
    """n = 3: every list of at most 3 distinct clauses from the 28 clauses with at most 2 literals (3683 formulas)."""
    lits = [1, -1, 2, -2, 3, -3]
    universe = [()] + [(l,) for l in lits] + [(a, b) for i, a in enumerate(lits) for b in lits[i:]]
    for k in range(4):
        for combo in itertools.combinations(universe, k):
            yield 3, combo


class TwoSatProofs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.H = _load(E + "harness.py", "tp_2sat_h")
        cls.brute = staticmethod(_load(E + "implementations/brute_force.py", "tp_2sat_b").two_sat_brute_force)
        cls.scc = staticmethod(_load(E + "implementations/aspvall_plass_tarjan.py", "tp_2sat_s").two_sat_scc)

    def formulas(self):
        yield from small_family()
        for i in range(800):
            rng = random.Random(f"tp-2sat|{i}")
            yield random_2cnf(rng.randint(1, 25), rng, empty_prob=0.01)

    def test_correctness_and_components(self):
        """Sections 3 to 6: outputs, the computed components and their numbering."""
        count = 0
        for n, clauses in self.formulas():
            t = TR.LineTrace(self.scc, snapshot="assignment = []")
            out = t.run((n, clauses))
            if n <= 10:
                sat = any(satisfies(clauses, mask) for mask in range(1 << n))
                b = self.brute((n, clauses))
                self.assertEqual(b is not None, sat)
                if b is not None:
                    self.assertTrue(satisfies(clauses, sum(1 << v for v in range(n) if b[v])))
            if any(len(cl) == 0 for cl in clauses):
                self.assertIsNone(out)
                continue
            adj = graph(n, clauses)
            r = reach(adj)
            comp = t.snapshot["comp"]
            same_ok = all((comp[u] == comp[v]) == (v in r[u] and u in r[v])     # components = SCCs
                          for u in range(2 * n) for v in range(2 * n))
            self.assertTrue(same_ok)
            self.assertTrue(all(comp[u] >= comp[v] for u in range(2 * n) for v in adj[u]))   # reverse topological
            self.assertEqual(sorted(set(comp)), list(range(len(set(comp)))))
            unsat_cert = any(node(-x) in r[node(x)] and node(x) in r[node(-x)] for x in range(1, n + 1))
            if out is None:
                self.assertTrue(unsat_cert)                         # x ~> NOT x ~> x: unsatisfiable
            else:
                self.assertFalse(unsat_cert)
                self.assertTrue(satisfies(clauses, sum(1 << v for v in range(n) if out[v])))
                self.assertEqual(out, tuple(comp[2 * v] < comp[2 * v + 1] for v in range(n)))
            if n <= 10:
                self.assertEqual(out is None, not sat)
            count += 1
        self.assertGreater(count, 3500)

    def test_search_work_and_space(self):
        """Section 7: every edge examined once, every node discovered, finished and popped once; peak sizes;
        executed lines linear in n + m; at least one counted operation per examined edge."""
        markers = {"edge": "w = edges[i]", "tree": "index[w] = low[w] = counter", "root": "index[root] = low[root]",
                   "finish": "work.pop()", "pop": "w = stack.pop()"}

        def sizes(loc):
            return {"stack": len(loc.get("stack") or ()), "work": len(loc.get("work") or ())}

        for i in range(500):
            rng = random.Random(f"tp-2sat-work|{i}")
            n, clauses = random_2cnf(rng.randint(1, 40), rng)
            m = len(clauses)
            t = TR.LineTrace(self.scc, markers, sizes, snapshot="assignment = []")
            t.run((n, clauses))
            self.assertEqual(t.counts["edge"], 2 * m)
            self.assertEqual(t.counts["tree"] + t.counts["root"], 2 * n)
            self.assertEqual(t.counts["finish"], 2 * n)
            self.assertEqual(t.counts["pop"], 2 * n)
            self.assertLessEqual(t.peak["stack"], 2 * n)
            self.assertLessEqual(t.peak["work"], 2 * n)
            self.assertEqual(sum(len(x) for x in t.snapshot["adj"]), 2 * m)
            self.assertGreaterEqual(t.total_lines, 2 * m)
            self.assertLessEqual(t.total_lines, 30 * m + 60 * n + 30)
            lits = tuple(tuple(self.H.CountingLit(l) for l in cl) for cl in clauses)
            self.H._ops = 0
            self.scc((n, lits))
            self.assertGreaterEqual(self.H._ops, 2 * m + 14 * m)          # 14 per clause in the build, 1 per edge

    def test_empty_clause_stops_the_build(self):
        """Section 7: an empty clause ends the build pass at once (so Theta(n + m) needs no empty clause)."""
        for k in (10, 100, 1000):
            clauses = ((),) + ((1, 2),) * k
            t = TR.LineTrace(self.scc, {"build": "a = _node(clause[0])"})
            self.assertIsNone(t.run((5, clauses)))
            self.assertEqual(t.counts["build"], 0)

    def test_brute_force_worst_case_every_m(self):
        """Section 8: m - 4 copies of (x1 OR x2) before the core: exactly (4m - 1) 2^(n-2) literal evaluations for
        m >= 5, 2^(n+2) for m = 4, and at least m 2^(n-2) (n = 3..9, m = 4..30); m - 1 copies of (x1) followed by
        (NOT x1): exactly (m + 1) 2^(n-1) evaluations (n = 1..7, m = 2..30)."""
        core = [(2, 3), (2, -3), (-2, 3), (-2, -3)]
        for n in range(3, 10):
            for m in range(4, 31):
                clauses = [(1, 2)] * (m - 4) + core
                cl = tuple(tuple(self.H.CountingLit(l) for l in c) for c in clauses)
                self.H._ops = 0
                self.assertIsNone(self.brute((n, cl)))
                ev, rest = divmod(self.H._ops, 6)
                self.assertEqual(rest, 0)
                self.assertEqual(ev, (4 * m - 1) * 2 ** (n - 2) if m >= 5 else 2 ** (n + 2))
                self.assertGreaterEqual(ev, m * 2 ** (n - 2))
                self.assertLessEqual(ev, 2 * m * 2 ** n)
        for n in range(1, 8):                      # Q_{n,m}: m - 1 copies of (x1), then (NOT x1)
            for m in range(2, 31):
                cl = tuple(tuple(self.H.CountingLit(l) for l in c) for c in [(1,)] * (m - 1) + [(-1,)])
                self.H._ops = 0
                self.assertIsNone(self.brute((n, cl)))
                self.assertEqual(self.H._ops, 6 * (m + 1) * 2 ** (n - 1))

    def test_renaming_invariance(self):
        """Section 8: renaming and negating variables does not change the brute-force count of an unsatisfiable
        formula; W_n under 5 random signed permutations (n = 3..10) and 300 random unsatisfiable formulas."""
        def count(n, clauses):
            cl = tuple(tuple(self.H.CountingLit(l) for l in c) for c in clauses)
            self.H._ops = 0
            self.brute((n, cl))
            return self.H._ops

        def rename(clauses, perm, signs):
            return tuple(tuple((1 if l > 0 else -1) * signs[abs(l) - 1] * perm[abs(l) - 1] for l in c) for c in clauses)

        for n in range(3, 11):
            fam = self.H._family(n)
            for s in range(5):
                rng = random.Random(f"tp-2sat-rename|{n}|{s}")
                perm = rng.sample(range(1, n + 1), n)
                signs = [rng.choice((-1, 1)) for _ in range(n)]
                self.assertEqual(count(n, rename(fam, perm, signs)), 3 * (n + 7) * 2 ** n + 12)
        done = 0
        for i in range(3000):
            rng = random.Random(f"tp-2sat-rename-rnd|{i}")
            n, clauses = random_2cnf(rng.randint(1, 7), rng)
            if any(satisfies(clauses, mask) for mask in range(1 << n)):
                continue
            perm = rng.sample(range(1, n + 1), n)
            signs = [rng.choice((-1, 1)) for _ in range(n)]
            self.assertEqual(count(n, rename(clauses, perm, signs)), count(n, clauses))
            done += 1
            if done == 300:
                break
        self.assertEqual(done, 300)

    def test_brute_force_space_and_distinct_clauses(self):
        """Section 8: besides the input, brute force keeps only integers (200 seeded formulas, n = 1..8); and at most
        4n distinct clauses of at most two literals (as tuples) contain the literal x1 (n = 1..6, by enumeration)."""
        for i in range(200):
            rng = random.Random(f"tp-2sat-space|{i}")
            f = random_2cnf(rng.randint(1, 8), rng, empty_prob=0.02)
            clauses = f[1]

            def extra(loc):
                return {"extra": sum(1 for v in loc.values() if not (isinstance(v, int) or v is f or v is clauses
                                                                      or any(v is c for c in clauses)))}
            t = TR.LineTrace(self.brute, sizes=extra)
            t.run(f)
            self.assertEqual(t.peak.get("extra", 0), 0)
        for n in range(1, 7):
            lits = [s * v for v in range(1, n + 1) for s in (1, -1)]
            tuples = [(l,) for l in lits] + [(a, b) for a in lits for b in lits]
            self.assertEqual(sum(1 for c in tuples if 1 in c), 4 * n)

    def test_random_clause_falsified_with_probability_quarter(self):
        """Caveat: a clause on two distinct variables is false under exactly 1/4 of all assignments (n = 2..6)."""
        for n in range(2, 7):
            for a, b in itertools.permutations(range(1, n + 1), 2):
                for sa, sb in itertools.product((-1, 1), repeat=2):
                    cl = (sa * a, sb * b)
                    false = sum(1 for mask in range(1 << n) if not satisfies((cl,), mask))
                    self.assertEqual(4 * false, 1 << n)


if __name__ == "__main__":
    unittest.main()
