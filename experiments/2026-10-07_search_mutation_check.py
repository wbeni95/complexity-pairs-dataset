"""Experiment (research/2026-10-07_search_flipgraph.md, section Tests): mutation check of the search tests.

Question: do tests/test_search_flipgraph.py and tests/test_search_driver.py FAIL when the moves are broken?
Two mutations are injected by monkeypatching (the source files are not modified):
  1. a flip that applies only its first half (term i updated, term j not);
  2. a merge (reduction) that drops a term without adding its factor to the partner terms.
Expected: failures/errors > 0 for both mutations, 0 for the unmutated code. Deterministic (the tests use fixed seeds).

Run from the repository root:  python experiments/2026-10-07_search_mutation_check.py
"""
import sys, unittest, io
sys.path.insert(0, '.')
sys.path.insert(0, 'tests')
import search.flipgraph as fg

orig_flip = fg.FlipGraphState.flip
orig_reduce_src = fg.FlipGraphState.reduce


def bad_flip(self):
    # mutation 1: second half of the flip omitted
    shared = self.shared
    if not shared:
        return False
    p, v = shared[self.rng.randrange(len(shared))]
    g = self.groups[p][v]
    i, j = g[0], g[1]
    q, r = fg._OTHER[p]
    ti, tj = self.t[i], self.t[j]
    self._set(i, q, ti[q] ^ tj[q])
    self.reduce()
    return True


def run(label):
    import test_search_flipgraph, test_search_driver, importlib
    importlib.reload(test_search_flipgraph); importlib.reload(test_search_driver)
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_search_flipgraph))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_search_driver))
    res = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
    print(f"{label}: ran {res.testsRun}, failures {len(res.failures)}, errors {len(res.errors)}")

fg.FlipGraphState.flip = bad_flip
run("mutation 1 (half flip)")
fg.FlipGraphState.flip = orig_flip

# mutation 2: merge without adding the removed term's third factor
orig_set = fg.FlipGraphState._set
def reduce_bad(self):
    start = len(self.t)
    while self.dirty:
        p, v = self.dirty.pop()
        g = self.groups[p].get(v)
        if g is None or len(g) < 2:
            continue
        members = list(g)
        for q in fg._OTHER[p]:
            vals = [self.t[x][q] for x in members]
            comb = fg.find_dependency(vals)
            if comb is None:
                continue
            subset = [members[i] for i in range(len(members)) if (comb >> i) & 1]
            self._remove(subset[0])   # dropped without compensation
            self.dirty.append((p, v))
            break
    return start - len(self.t)
fg.FlipGraphState.reduce = reduce_bad
run("mutation 2 (merge drops a term)")
fg.FlipGraphState.reduce = orig_reduce_src
run("unmutated")
