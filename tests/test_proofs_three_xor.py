"""Checks for pairs/three-xor-all-triples-vs-patricia-trie/PROOFS.md, sections 3-7.

All triples returns the lexicographically first solution; the Patricia-trie algorithm returns a valid triple exactly
when one exists, also on the three kinds of solution separately; the counted operations of the trie algorithm obey
the explicit O(n^2 + n w) bound on every input checked; on no-instances of n distinct nonzero values it makes exactly
n^2 XORs; the trie of any input is a full binary tree whose leaves are the distinct nonzero values in ascending order;
and the space bounds, including inputs where the trie is n levels deep. All inputs come from fixed seeds. Runs in a
few seconds.
"""
import importlib.util
import itertools
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "three-xor-all-triples-vs-patricia-trie"
sys.path.insert(0, str(REPO / "tests"))

from proof_space import peak_words  # noqa: E402


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = _load(E / "harness.py", "tp_3x_h")
AT_FILE = E / "implementations" / "all_triples.py"
PT_FILE = E / "implementations" / "patricia_trie.py"
AT = _load(AT_FILE, "tp_3x_at").three_xor_all_triples
PT_MOD = _load(PT_FILE, "tp_3x_pt")
PT = PT_MOD.three_xor_patricia_trie


def first_solution(values):
    n = len(values)
    for i, j, k in itertools.combinations(range(n), 3):
        if values[i] ^ values[j] ^ values[k] == 0:
            return (i, j, k)
    return None


def instances(tag, count, max_n=40):
    rng = random.Random(f"tp-3x|{tag}")
    for t in range(count):
        yield H.generate(rng.randint(0, max_n), rng)


def distinct_odd_weight(n, w, rng):
    return (w, tuple(H._odd_pool(n, w, rng)))


def leaves_of(node, out):
    if isinstance(node, int):
        out.append(node)
    else:
        leaves_of(node[1], out)
        leaves_of(node[2], out)
    return out


class ThreeXorProofChecks(unittest.TestCase):
    def test_all_triples_lexicographically_first(self):
        yes = 0
        for inst in instances("lex", 500, max_n=30):
            out = AT(inst)
            self.assertEqual(out, first_solution(inst[1]), inst)
            yes += out is not None
        self.assertGreater(yes, 100)

    def test_trie_correct_and_kinds(self):
        kinds = {"zeros3": 0, "xx0": 0, "distinct": 0, "none": 0}
        for inst in instances("trie", 800, max_n=48):
            w, values = inst
            out = PT(inst)
            truth = H.has_solution(values)
            self.assertEqual(out is not None, truth, inst)
            self.assertIs(H.check(inst, out), True, inst)
            if out is None:
                kinds["none"] += 1
            else:
                trip = sorted(values[x] for x in out)
                kinds["zeros3" if trip == [0, 0, 0] else "xx0" if trip[0] == 0 else "distinct"] += 1
        self.assertTrue(all(v > 20 for v in kinds.values()), kinds)

    def test_trie_shape_and_leaf_order(self):
        for inst in itertools.chain(instances("shape", 300, max_n=60),
                                    ((w, tuple(1 << b for b in range(w))) for w in range(1, 40))):
            w, values = inst
            nonzero = [i for i, v in enumerate(values) if v != 0]
            if not nonzero:
                continue
            leaves = []
            root = PT_MOD._build(values, nonzero, w - 1, leaves)
            reps = leaves_of(root, [])
            self.assertEqual(reps, [g[0] for g in leaves])                         # leaves left to right
            dvals = [values[r] for r in reps]
            self.assertEqual(dvals, sorted(set(values[i] for i in nonzero)))       # distinct values, ascending
            for g in leaves:
                self.assertEqual(len({values[i] for i in g}), 1)                  # a leaf holds equal values
            self.assertEqual(sorted(i for g in leaves for i in g), nonzero)        # leaves partition the indices
            for a in dvals:
                xs = PT_MOD._xor_ascending(root, a, values)
                self.assertEqual([c for c, _ in xs], sorted(a ^ d for d in dvals))  # walk: ascending a XOR x

    def test_trie_operation_bound(self):
        for inst in itertools.chain(instances("ops", 300, max_n=60),
                                    ((w, tuple(1 << b for b in range(w))) for w in (1, 5, 17, 40, 64))):
            w, values = inst
            n = len(values)
            counted = (w, tuple(H.CountingInt(v) for v in values))
            H.reset_counter()
            out = PT(counted)
            self.assertEqual(out is not None, H.has_solution(values))
            self.assertLessEqual(H.reported_cost(None), n + 2 * n * w + 7 * n * n, inst)

    def test_trie_quadratic_on_distinct_odd_weight(self):
        rng = random.Random("tp-3x|quad")
        for n in range(1, 70):
            for w in sorted({n.bit_length(), n.bit_length() + 1, n.bit_length() + 3, 64}):
                if (1 << (w - 1)) < n:
                    continue
                w_, values = distinct_odd_weight(n, w, rng)
                counted = (w_, tuple(H.CountingInt(v) for v in values))
                H.reset_counter()
                self.assertIsNone(PT(counted))
                self.assertEqual(H.counts()["xor"], n * n, (n, w))

    def test_space(self):
        cases = list(instances("space", 20, max_n=30))
        cases += [(w, tuple(1 << b for b in range(w))) for w in (8, 16, 32)]        # the trie is w levels deep
        cases += [H.generate_scaling(n, random.Random(n)) for n in (1, 2, 8, 32)]
        for inst in cases:
            if inst[1] and isinstance(inst[1][0], H.CountingInt):
                inst = (inst[0], tuple(v.v for v in inst[1]))
            n = len(inst[1])
            _, pa = peak_words(AT, (inst,), AT_FILE)
            self.assertLessEqual(pa, 3)                  # only the returned triple
            _, pt = peak_words(PT, (inst,), PT_FILE)
            self.assertTrue(n <= pt <= 15 * n + 3, (n, inst[0], pt))


if __name__ == "__main__":
    unittest.main()
