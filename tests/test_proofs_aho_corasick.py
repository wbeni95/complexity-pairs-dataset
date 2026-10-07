"""Checks of the proofs in pairs/multi-pattern-matching-naive-vs-aho-corasick/PROOFS.md (sections 7 to 11).

Every check runs the unchanged implementations on fixed inputs (an exhaustive small family and seeded random
instances): correctness of the three algorithms; the trie, the failure links and the breadth-first order built by
Aho-Corasick, and the state after every text character; the lookup counts of the construction and the scan; the
bounds of KMP per pattern; the naive worst case N L and its exact expectation on random text; the trie size and the
uncounted work. Runs in a few seconds.
"""
import importlib.util
import itertools
import random
import sys
import unittest
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = "pairs/multi-pattern-matching-naive-vs-aho-corasick/"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TR = _load("tests/_proof_trace.py", "tp_ac_trace")


def direct_counts(text, patterns):
    return tuple(sum(1 for i in range(len(text) - len(p) + 1) if text[i:i + len(p)] == p) for p in patterns)


def exhaustive_instances():
    """Texts over {a, b} of length <= 5 with every list of at most 2 patterns over {a, b} of length 1..3."""
    pats = ["".join(w) for k in range(1, 4) for w in itertools.product("ab", repeat=k)]
    texts = ["".join(w) for k in range(6) for w in itertools.product("ab", repeat=k)]
    for k in range(3):
        for plist in itertools.product(pats, repeat=k):
            for t in texts:
                yield t, tuple(plist)


class AhoCorasickProofs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.H = _load(E + "harness.py", "tp_ac_h")
        cls.naive = staticmethod(_load(E + "implementations/naive.py", "tp_ac_n").count_occurrences_naive)
        cls.kmp = staticmethod(_load(E + "implementations/kmp_each.py", "tp_ac_k").count_occurrences_kmp_each)
        cls.ac = staticmethod(_load(E + "implementations/aho_corasick.py", "tp_ac_a").count_occurrences_aho_corasick)

    def random_instances(self, count, tag):
        for i in range(count):
            rng = random.Random(f"tp-ac|{tag}|{i}")
            yield self.H.generate(rng.randint(0, 12), rng)

    def counted(self, f, text, patterns):
        C = self.H.CountingChar
        self.H._comparisons = 0
        f((tuple(C(c) for c in text), tuple(tuple(C(c) for c in p) for p in patterns)))
        return self.H._comparisons

    def test_correctness(self):
        """Sections 7, 8 and 9: all three algorithms return the overlapping counts (exhaustive family: 211 pattern
        lists x 63 texts; plus 600 seeded instances from harness.generate, n = 0..12)."""
        cases = 0
        for text, pats in itertools.chain(exhaustive_instances(), self.random_instances(600, "corr")):
            want = direct_counts(text, pats)
            self.assertEqual(self.naive((text, pats)), want)
            self.assertEqual(self.kmp((text, pats)), want)
            self.assertEqual(self.ac((text, pats)), want)
            cases += 1
        self.assertEqual(cases, 211 * 63 + 600)

    def test_trie_failure_links_order_and_states(self):
        """Section 9: the trie holds exactly the prefixes of the patterns, fail[v] is the longest proper suffix of
        v's string that is a prefix, the order is breadth-first and every node comes after its failure target, and
        the state after each text character is the longest suffix of the text read that is a prefix (600 seeded
        instances)."""
        for text, pats in self.random_instances(600, "trie"):
            t = TR.LineTrace(self.ac, snapshot="visits = [0] * len(children)")
            states = []
            code = self.ac.__code__
            src, start = __import__("inspect").getsourcelines(self.ac)
            vis_line = start + next(i for i, s in enumerate(src) if "visits[state] += 1" in s)

            def local(frame, event, arg):
                if event == "line":
                    t._local(frame, event, arg)
                    if frame.f_lineno == vis_line:
                        states.append(frame.f_locals["state"])
                return local

            def glob(frame, event, arg):
                return local if frame.f_code is code else None
            old = sys.gettrace()
            sys.settrace(glob)
            try:
                self.ac((text, pats))
            finally:
                sys.settrace(old)
            snap = t.snapshot
            children, fail, order = snap["children"], snap["fail"], snap["order"]
            word = {0: ""}
            stack = [0]
            while stack:
                u = stack.pop()
                for ch, v in children[u]:
                    self.assertNotIn(v, word)
                    word[v] = word[u] + ch
                    stack.append(v)
                self.assertEqual(len({ch for ch, _ in children[u]}), len(children[u]))   # distinct characters
            prefixes = {""} | {p[:k] for p in pats for k in range(len(p) + 1)}
            self.assertEqual(sorted(word.values()), sorted(prefixes))
            self.assertEqual(len(word), len(children))
            node_of = {w: v for v, w in word.items()}
            self.assertLessEqual(len(children), sum(len(p) for p in pats) + 1)
            depths = [len(word[v]) for v in order]
            self.assertEqual(depths, sorted(depths))
            self.assertEqual(sorted(order), sorted(v for v in word if v != 0))
            pos = {v: i for i, v in enumerate(order)}
            for v in order:
                w = word[v]
                longest = max((w[k:] for k in range(1, len(w) + 1) if w[k:] in prefixes), key=len)
                self.assertEqual(fail[v], node_of[longest])
                if fail[v] != 0:
                    self.assertLess(pos[fail[v]], pos[v])
            self.assertEqual(len(states), len(text))
            for k, s in enumerate(states):
                read = text[:k + 1]
                longest = max((read[i:] for i in range(len(read) + 1) if read[i:] in prefixes), key=len)
                self.assertEqual(s, node_of[longest])

    def test_lookup_counts(self):
        """Sections 4 and 10: insertion makes exactly L lookups, the failure links at most 2 sum(m - 1), the scan at
        most 2N (600 seeded instances)."""
        markers = {"ins": "nxt = _child(children, node, c)", "link": "w = _child(children, f, ch)",
                   "scan": "w = _child(children, state, c)"}
        for text, pats in self.random_instances(600, "look"):
            t = TR.LineTrace(self.ac, markers)
            t.run((text, pats))
            L = sum(len(p) for p in pats)
            self.assertEqual(t.counts["ins"], L)
            self.assertLessEqual(t.counts["link"], 2 * sum(len(p) - 1 for p in pats))
            self.assertLessEqual(t.counts["scan"], 2 * len(text))

    def test_uncounted_work(self):
        """Caveat (section 10): the executed lines of count_occurrences_aho_corasick (the lookup function _child, whose
        work is the counted comparisons, is not traced) number between N + L and 12 N + 26 L + 6 P + 30 (600 seeded
        instances)."""
        for text, pats in self.random_instances(600, "unc"):
            t = TR.LineTrace(self.ac)
            t.run((text, pats))
            N, L, P = len(text), sum(len(p) for p in pats), len(pats)
            self.assertGreaterEqual(t.total_lines, N + L)
            self.assertLessEqual(t.total_lines, 12 * N + 26 * L + 6 * P + 30)

    def test_kmp_code_identity(self):
        """Section 8: _failure and the scan loop of kmp_each.py are line for line the code of
        pairs/string-matching-naive-vs-kmp/implementations/kmp.py (comments aside), whose correctness is proved there."""
        import inspect
        K1 = _load(E + "implementations/kmp_each.py", "tp_ac_k2")
        K2 = _load("pairs/string-matching-naive-vs-kmp/implementations/kmp.py", "tp_ac_k3")
        self.assertEqual(inspect.getsource(K1._failure), inspect.getsource(K2._failure))

        def scan(f):
            lines = [s.split("#")[0].strip() for s in inspect.getsource(f).splitlines()]   # code without comments
            i = lines.index("for c in text:")
            return lines[i:i + 8]
        self.assertEqual(scan(K1.count_occurrences_kmp_each), scan(K2.count_kmp))
        self.assertEqual(scan(K2.count_kmp)[-1], "q = fail[q - 1]")

    def test_kmp_each_bounds(self):
        """Section 8: P N + L - P <= comparisons <= 3 P N + 3 (L - P) for KMP per pattern (600 seeded instances)."""
        for text, pats in self.random_instances(600, "kmp"):
            c = self.counted(self.kmp, text, pats)
            N, L, P = len(text), sum(len(p) for p in pats), len(pats)
            self.assertGreaterEqual(c, P * N + L - P)
            self.assertLessEqual(c, 3 * P * N + 3 * (L - P))

    def test_naive_worst_case_and_bound(self):
        """Section 7: L patterns 'a' against a^N cost exactly N L comparisons (N = 0..30, L = 1..10), and every input
        costs at most N L (600 seeded instances)."""
        for N in range(31):
            for L in range(1, 11):
                self.assertEqual(self.counted(self.naive, "a" * N, ("a",) * L), N * L)
        for text, pats in self.random_instances(600, "naive"):
            self.assertLessEqual(self.counted(self.naive, text, pats), len(text) * sum(len(p) for p in pats))

    def test_naive_space(self):
        """Section 7: besides the input, the naive matcher keeps integers and the output list of at most P counts
        (300 seeded instances)."""
        for text, pats in self.random_instances(300, "nsp"):
            inst = (text, pats)

            def extra(loc):
                out = loc.get("counts")
                return {"extra": sum(1 for k, v in loc.items() if not (isinstance(v, int) or v is inst or v is text
                                                                        or v is pats or any(v is p for p in pats)
                                                                        or k == "counts")),
                        "counts": len(out) if out is not None else 0}
            t = TR.LineTrace(self.naive, sizes=extra)
            t.run(inst)
            self.assertEqual(t.peak.get("extra", 0), 0)
            self.assertLessEqual(t.peak.get("counts", 0), len(pats))

    def test_naive_expected_cost_on_random_text(self):
        """Caveat (section 11): over all texts of length N over sigma letters, a pattern of length m whose letters
        are in the alphabet costs on average exactly max(N - m + 1, 0) sum_{j<m} sigma^(-j) comparisons, at most
        2 max(N - m + 1, 0) (sigma = 2: N = 0..7, every pattern of length 1..4; sigma = 3: N = 0..4, length 1..3)."""
        for sigma, Nmax, Mmax in ((2, 7, 4), (3, 4, 3)):
            alpha = "abc"[:sigma]
            for m in range(1, Mmax + 1):
                for pat in itertools.product(alpha, repeat=m):
                    pat = "".join(pat)
                    for N in range(Nmax + 1):
                        total = sum(self.counted(self.naive, "".join(w), (pat,))
                                    for w in itertools.product(alpha, repeat=N))
                        avg = Fraction(total, sigma ** N)
                        want = max(N - m + 1, 0) * sum(Fraction(1, sigma ** j) for j in range(m))
                        self.assertEqual(avg, want)
                        self.assertLessEqual(avg, 2 * max(N - m + 1, 0))


if __name__ == "__main__":
    unittest.main()
