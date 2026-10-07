"""Checks of the proofs in pairs/horn-sat-brute-force-vs-unit-propagation/PROOFS.md (sections 4 to 9).

Every check runs the unchanged implementations on fixed inputs (exhaustive small families and seeded random formulas)
and compares them with the statements proved there: closure of Horn models under intersection and the least model,
correctness of brute force and unit propagation, the linear bounds and work counts of unit propagation, the
brute-force bounds, the worst case for every L, dual-Horn formulas, and the 'no facts' caveat. Runs in a few seconds.
"""
import importlib.util
import itertools
import random
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = "pairs/horn-sat-brute-force-vs-unit-propagation/"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TR = _load("tests/_proof_trace.py", "tp_horn_trace")


class CountingClause(tuple):
    """A clause that counts how often it is scanned (iter() calls)."""
    scans = 0

    def __iter__(self):
        CountingClause.scans += 1
        return super().__iter__()


def models(n, clauses):
    out = []
    for mask in range(1 << n):
        if all(any(((mask >> (abs(l) - 1)) & 1) == (l > 0) for l in cl) for cl in clauses):
            out.append(mask)
    return out


def as_tuple(n, mask):
    return tuple(bool((mask >> v) & 1) for v in range(n))


def random_horn(n, rng, empty_prob=0.05):
    """A random Horn formula: widths 1..4, a head with probability 0.6, sometimes a tautology (NOT v OR v) or a
    repeated negative literal, and an empty clause with probability empty_prob per clause."""
    clauses = []
    for _ in range(rng.randint(0, 3 * n + 2)):
        if rng.random() < empty_prob:
            clauses.append(())
            continue
        width = rng.randint(1, 4)
        lits = [-rng.randint(1, n) for _ in range(width)]
        if rng.random() < 0.6:
            lits[rng.randrange(width)] *= -1
        heads = [l for l in lits if l > 0]
        if rng.random() < 0.15:
            if heads:
                lits += [-heads[0], heads[0]]                 # tautology on the head variable
            elif rng.random() < 0.5:
                v = rng.randint(1, n)
                lits += [-v, v]                               # tautology; v becomes the head
            else:
                lits += [lits[0], lits[0]]                    # repeated negative literal
        rng.shuffle(lits)
        clauses.append(tuple(lits))
    return n, tuple(clauses)


def is_horn(clauses):
    return all(len({l for l in cl if l > 0}) <= 1 for cl in clauses)


class HornProofs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.H = _load(E + "harness.py", "tp_horn_h")
        cls.brute = staticmethod(_load(E + "implementations/brute_force.py", "tp_horn_b").horn_sat_brute_force)
        cls.up = staticmethod(_load(E + "implementations/unit_propagation.py", "tp_horn_u").horn_sat_unit_propagation)

    def formulas(self):
        """Exhaustive: n = 3, every list of at most 2 distinct Horn clause types (32 types); plus 1500 seeded random
        Horn formulas (n = 1..6) with repeated literals, tautologies and empty clauses."""
        n = 3
        types = []
        for neg in itertools.product((0, 1), repeat=n):
            body = tuple(-(v + 1) for v in range(n) if neg[v])
            for head in range(n + 1):
                types.append(body + ((head,) if head else ()))
        for k in range(3):
            for combo in itertools.combinations(types, k):
                yield n, combo
        for i in range(1500):
            rng = random.Random(f"tp-horn|{i}")
            f = random_horn(rng.randint(1, 6), rng)
            if is_horn(f[1]):
                yield f

    def test_closure_least_model_and_correctness(self):
        seen = 0
        for n, clauses in self.formulas():
            ms = models(n, clauses)
            sms = set(ms)
            for a in ms:                                   # closure under intersection (PROOFS.md section 4)
                for b in ms:
                    self.assertIn(a & b, sms)
            want = None
            if ms:
                least = (1 << n) - 1
                for a in ms:
                    least &= a
                self.assertIn(least, sms)                  # the intersection of all models is a model
                self.assertEqual(least, min(ms))           # and has the smallest mask (section 5)
                want = as_tuple(n, least)
            self.assertEqual(self.brute((n, clauses)), want)
            self.assertEqual(self.up((n, clauses)), want)  # section 6
            seen += 1
        self.assertGreater(seen, 1500)

    def test_unit_propagation_work_and_space(self):
        """Section 7: literal reads, decrements, pushes, pops and peak sizes, on 1500 seeded formulas (n = 1..60)."""
        markers = {"lit": "if lit > 0:", "dec": "counter[c] -= 1", "pop": "v = queue.pop()",
                   "set": "value[v] = True"}

        def sizes(loc):
            q = loc.get("queue")
            occ = loc.get("occurs")
            return {"queue": len(q) if q is not None else 0,
                    "occurs": sum(len(x) for x in occ) if occ is not None else 0,
                    "head": len(loc.get("head") or ())}

        for i in range(1500):
            rng = random.Random(f"tp-horn-work|{i}")
            n = rng.randint(1, 60)
            f = random_horn(n, rng, empty_prob=0.02 if i % 3 == 0 else 0.0)
            if not is_horn(f[1]):
                continue
            clauses = f[1]
            first_empty = next((j for j, cl in enumerate(clauses) if len(cl) == 0), None)
            read = clauses if first_empty is None else clauses[:first_empty + 1]
            L_read = sum(len(cl) for cl in read)
            neg_read = sum(1 for cl in read for l in cl if l < 0)
            t = TR.LineTrace(self.up, markers, sizes)
            t.run(f)
            m_read = len(read)
            # the build loop reads exactly the literals of the clauses up to the first empty clause
            self.assertEqual(t.counts["lit"], L_read)
            self.assertLessEqual(t.counts["dec"], neg_read)        # each negative occurrence decremented at most once
            self.assertLessEqual(t.counts["set"], n)               # each variable set true at most once
            self.assertLessEqual(t.counts["pop"], m_read)          # pushes <= facts + firings <= clauses read
            self.assertLessEqual(t.peak.get("queue", 0), m_read)
            self.assertLessEqual(t.peak.get("occurs", 0), neg_read)
            self.assertLessEqual(t.peak.get("head", 0), m_read)
            # at most 15 line events per clause read (build, its pop), 11 per literal read (build, decrement),
            # 2 per variable (the inlined comprehension that builds occurs) and 14 more
            self.assertLessEqual(t.total_lines, 15 * m_read + 11 * L_read + 2 * n + 14)
            self.assertGreaterEqual(t.total_lines, L_read)

    def test_brute_force_bounds(self):
        """Section 8: at most 2^n L literal evaluations and 2^n (L + 1) clause scans, on 600 seeded formulas."""
        for i in range(600):
            rng = random.Random(f"tp-horn-brute|{i}")
            n, clauses = random_horn(rng.randint(1, 8), rng, empty_prob=0.03)
            if not is_horn(clauses):
                continue
            L = sum(len(cl) for cl in clauses)
            cl = tuple(CountingClause(tuple(self.H.CountingLit(l) for l in c)) for c in clauses)
            self.H._ops = 0
            CountingClause.scans = 0
            self.brute((n, cl))
            self.assertEqual(self.H._ops % 6, 0)
            self.assertLessEqual(self.H._ops // 6, (1 << n) * L)
            self.assertLessEqual(CountingClause.scans, (1 << n) * (L + 1))

    def test_worst_case_for_every_L(self):
        """Section 8: H_n with k copies of (NOT x1) before (x1): L = 3n - 2 + k, exactly (2n + 2k + 13) 2^(n-2) - 4n - 5
        literal evaluations for k >= 1, and at least 2^n L / 6 for every k >= 0 (n = 3..10, k = 0..30)."""
        for n in range(3, 11):
            base = self.H._family(n)
            for k in range(31):
                clauses = base[:n - 2] + [(-1,)] * k + base[n - 2:]
                L = sum(len(c) for c in clauses)
                self.assertEqual(L, 3 * n - 2 + k)
                cl = tuple(tuple(self.H.CountingLit(l) for l in c) for c in clauses)
                self.H._ops = 0
                self.assertIsNone(self.brute((n, cl)))
                ev = self.H._ops // 6
                if k == 0:
                    self.assertEqual(ev, (2 * n + 13) * 2 ** (n - 2) - 2 * n - 4)
                else:
                    self.assertEqual(ev, (2 * n + 2 * k + 13) * 2 ** (n - 2) - 4 * n - 5)
                self.assertGreaterEqual(6 * ev, (1 << n) * L)

    def test_brute_force_space(self):
        """Section 8 (d): besides the input, brute force keeps only integers (the mask and loop values); 200 seeded
        formulas (n = 1..8)."""
        for i in range(200):
            rng = random.Random(f"tp-horn-space|{i}")
            f = random_horn(rng.randint(1, 8), rng, empty_prob=0.03)
            clauses = f[1]

            def extra(loc):
                return {"extra": sum(1 for v in loc.values() if not (isinstance(v, int) or v is f or v is clauses
                                                                      or any(v is c for c in clauses)))}
            t = TR.LineTrace(self.brute, sizes=extra)
            t.run(f)
            self.assertEqual(t.peak.get("extra", 0), 0)

    def test_dual_horn_by_negation(self):
        """Section 9: negating every variable turns a dual-Horn formula into a Horn formula; 800 seeded formulas."""
        for i in range(800):
            rng = random.Random(f"tp-horn-dual|{i}")
            n, horn = random_horn(rng.randint(1, 8), rng, empty_prob=0.03)
            if not is_horn(horn):
                continue
            dual = tuple(tuple(-l for l in cl) for cl in horn)        # at most one negative literal per clause
            out = self.up((n, horn))
            ms = models(n, dual)
            if out is None:
                self.assertEqual(ms, [])
            else:
                comp = tuple(not b for b in out)
                mask = sum(1 << v for v in range(n) if comp[v])
                self.assertIn(mask, set(ms))
                self.assertEqual(mask, max(ms))                       # the greatest model of the dual-Horn formula

    def test_no_facts_mask_zero(self):
        """Caveat: without facts and empty clauses, mask 0 is a model and brute force scans each clause once."""
        for i in range(500):
            rng = random.Random(f"tp-horn-nofacts|{i}")
            n, clauses = random_horn(rng.randint(1, 10), rng, empty_prob=0.0)
            clauses = tuple(c for c in clauses if any(l < 0 for l in c))
            if not is_horn(clauses):
                continue
            CountingClause.scans = 0
            out = self.brute((n, tuple(CountingClause(c) for c in clauses)))
            self.assertEqual(out, (False,) * n)
            self.assertEqual(CountingClause.scans, len(clauses))


if __name__ == "__main__":
    unittest.main()
