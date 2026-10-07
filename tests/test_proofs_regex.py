"""Checks of the proofs in pairs/regex-matching-backtracking-vs-thompson/PROOFS.md (sections 4 to 9).

Every check runs the unchanged matchers on fixed inputs: all patterns of at most 3 atoms over {a, b, .} with the
quantifiers '', '?', '*' against all texts over {a, b} of length at most 4, compared with a direct transcription of the
definition of full matching (and with Python's re as a second opinion); the state sets of Thompson's simulation
against the corrected invariant; the call, evaluation and depth bounds; the exact numbers of calls and evaluated
states on P_n (the uncounted work); and the backreference example. Runs in a few seconds.
"""
import importlib.util
import itertools
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = "pairs/regex-matching-backtracking-vs-thompson/"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TR = _load("tests/_proof_trace.py", "tp_regex_trace")
ATOMS = [(c, q) for c in "ab." for q in ("", "?", "*")]


def prefix_sets(atoms, text):
    """Direct transcription of the definition of concatenation: F[i] = {j : text[:j] in L(atom 0) ... L(atom i-1)},
    where L(c) holds the one character c (any character for '.'), L(c?) = {empty} + L(c) and L(c*) = L(c)*; and
    Q[i] = {j : text[:j] in L(atom 0) ... L(atom i-1) X_i}, X_i = L(atom i) for a starred atom i, {empty} otherwise."""
    def ok(c, w):
        return all(c == "." or c == x for x in w)

    def extend(starts, atom):
        c, q = atom
        out = set()
        for j in starts:
            lengths = (1,) if q == "" else (0, 1) if q == "?" else range(len(text) - j + 1)
            out.update(j + k for k in lengths if j + k <= len(text) and ok(c, text[j:j + k]))
        return out
    F = [{0}]
    for atom in atoms:
        F.append(extend(F[-1], atom))
    Q = [extend(F[i], atoms[i]) if i < len(atoms) and atoms[i][1] == "*" else F[i] for i in range(len(atoms) + 1)]
    return F, Q


def pattern_of(atoms):
    return "".join(c + q for c, q in atoms)


def thompson_states(match_thompson, instance):
    """The list `current` before each text character and at the end (None after an early return)."""
    code = match_thompson.__code__
    src, start = __import__("inspect").getsourcelines(match_thompson)
    lines = {start + i: tag for i, s in enumerate(src) for tag, mk in (("char", "x = text[j]"),
                                                                      ("end", "return m in current")) if mk in s}
    seen = []

    def local(frame, event, arg):
        if event == "line" and frame.f_lineno in lines:
            seen.append(list(frame.f_locals["current"]))
        return local

    def glob(frame, event, arg):
        return local if frame.f_code is code else None

    old = sys.gettrace()
    sys.settrace(glob)
    try:
        out = match_thompson(instance)
    finally:
        sys.settrace(old)
    return out, seen


class RegexProofs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.H = _load(E + "harness.py", "tp_regex_h")
        cls.back = staticmethod(_load(E + "implementations/backtracking.py", "tp_regex_b").match_backtracking)
        cls.memo = staticmethod(_load(E + "implementations/memoized.py", "tp_regex_m").match_memoized)
        cls.thom = staticmethod(_load(E + "implementations/thompson.py", "tp_regex_t").match_thompson)

    def cases(self):
        texts = ["".join(p) for k in range(5) for p in itertools.product("ab", repeat=k)]
        for k in range(4):
            for atoms in itertools.product(ATOMS, repeat=k):
                for t in texts:
                    yield atoms, t

    def test_correctness_and_thompson_invariant(self):
        """Sections 4, 5 and 6: all three matchers decide the definition (all 820 x 31 cases); Thompson's state set
        before character j is {i : t[:j] in L(atoms[:i]) X_i}, X_i = L(c*) for a starred atom i and {empty} otherwise
        (all texts up to length 3 and a third of those of length 4)."""
        count = 0
        for atoms, t in self.cases():
            F, Q = prefix_sets(atoms, t)
            want = len(t) in F[-1]
            p = pattern_of(atoms)
            self.assertEqual(want, re.fullmatch(p, t) is not None)
            self.assertEqual(self.back((p, t)), want)
            self.assertEqual(self.memo((p, t)), want)
            if len(t) == 4 and count % 3:                  # state sets: all texts up to length 3, a third of length 4
                self.assertEqual(self.thom((p, t)), want)
                count += 1
                continue
            out, states = thompson_states(self.thom, (p, t))
            self.assertEqual(out, want)
            m = len(atoms)

            def invariant(j):
                return [i for i in range(m + 1) if j in Q[i]]
            for j, cur in enumerate(states):               # states[j] = the state set before character j (or at the end)
                self.assertEqual(cur, invariant(j))
            if len(states) <= len(t):                      # early return after character len(states) - 1: empty set
                self.assertEqual(invariant(len(states)), [])
                self.assertFalse(want)
            count += 1
        self.assertEqual(count, 820 * 31)

    def test_call_bounds(self):
        """Sections 5 and 7: backtracking makes at most 2^(m+n+1) - 1 calls with depth <= m + n + 1; the memoised
        matcher evaluates each key once, at most (m + 1)(n + 1) keys, with at most 1 + 2 (evaluations) calls."""
        for atoms, t in itertools.islice(self.cases(), 0, None, 13):
            p, m, n = pattern_of(atoms), len(atoms), len(t)
            tb = TR.LineTrace(self.back, {"call": "if i == m:"}, nested="match")
            tb.run((p, t))
            self.assertLessEqual(tb.counts["call"], 2 ** (m + n + 1) - 1)
            self.assertLessEqual(tb.max_depth, m + n + 1)
            tm = TR.LineTrace(self.memo, {"call": "key = (i, j)", "eval": "memo[key] = result"}, nested="match")
            tm.run((p, t))
            self.assertLessEqual(tm.counts["eval"], (m + 1) * (n + 1))
            self.assertLessEqual(tm.counts["call"], 1 + 2 * tm.counts["eval"])
            self.assertLessEqual(tm.max_depth, m + n + 1)

    def test_distinct_evaluations(self):
        """Section 7: no key is evaluated twice by the memoised matcher (every 13th case)."""
        for atoms, t in itertools.islice(self.cases(), 3, None, 13):
            p = pattern_of(atoms)
            keys = []
            tm = TR.LineTrace(self.memo, sizes=None, nested="match", snapshot=None)
            code = tm.nested_code

            def local(frame, event, arg, keys=keys):
                if event == "return" and frame.f_code is code and frame.f_locals.get("result") is not None:
                    keys.append(frame.f_locals["key"])
                return local

            def glob(frame, event, arg):
                return local if frame.f_code is code else None
            old = sys.gettrace()
            sys.settrace(glob)
            try:
                self.memo((p, t))
            finally:
                sys.settrace(old)
            self.assertEqual(len(keys), len(set(keys)))

    def test_thompson_state_sets_and_steps(self):
        """Section 8: at most m + 1 active states, and O(m) executed lines per text character (at most
        14 (m + 1) + 10 per character plus 8 (m + 1) + 12)."""
        for atoms, t in itertools.islice(self.cases(), 1, None, 11):
            p, m, n = pattern_of(atoms), len(atoms), len(t)
            tt = TR.LineTrace(self.thom, sizes=lambda loc: {"cur": len(loc.get("current") or ()),
                                                            "nxt": len(loc.get("nxt") or ())}, nested="closure")
            tt.run((p, t))
            self.assertLessEqual(tt.peak.get("cur", 0), m + 1)
            self.assertLessEqual(tt.peak.get("nxt", 0), m + 1)
            self.assertLessEqual(tt.total_lines, n * (14 * (m + 1) + 10) + 8 * (m + 1) + 12)

    def test_uncounted_work_on_P_n(self):
        """Caveat (section 9): on P_n backtracking makes exactly (n + 4) 2^(n-1) - 1 calls (comparisons
        (n + 2) 2^(n-1) - 1), the memoised matcher evaluates exactly (n + 1)^2 states (comparisons n(n + 1)), and
        Thompson's simulation executes at most 30 lines per comparison plus 30 (n = 0..12)."""
        for n in range(0, 13):
            inst = ("a?" * n + "a" * n, "a" * n)
            tb = TR.LineTrace(self.back, {"call": "if i == m:"}, nested="match")
            self.assertTrue(tb.run(inst))
            self.assertEqual(2 * tb.counts["call"], (n + 4) * 2 ** n - 2)
            tm = TR.LineTrace(self.memo, {"eval": "memo[key] = result"}, nested="match")
            self.assertTrue(tm.run(inst))
            self.assertEqual(tm.counts["eval"], (n + 1) ** 2)
            tt = TR.LineTrace(self.thom, nested="closure")
            self.assertTrue(tt.run(inst))
            self.assertLessEqual(tt.total_lines, 30 * n * (n + 1) + 30)
            for f, want in ((self.back, (n + 2) * 2 ** n // 2 - 1 if n else 0), (self.memo, n * (n + 1)),
                            (self.thom, n * (n + 1))):
                inst2 = self.H.generate_scaling(n, None)
                f(inst2)
                self.assertEqual(self.H.reported_cost(None), want)

    def test_backreference_example(self):
        """Caveat (section 9): with Python's backreference semantics, (a*)b\\1 matches exactly a^k b a^k (texts over
        {a, b} up to length 9), and the suffix b a^i separates a^i from a^j for i != j <= 8; the dialect's parser
        rejects parentheses and backslashes."""
        for k in range(10):
            for w in itertools.product("ab", repeat=k):
                s = "".join(w)
                want = any(s == "a" * i + "b" + "a" * i for i in range(5))
                self.assertEqual(re.fullmatch(r"(a*)b\1", s) is not None, want)
        for i in range(9):
            for j in range(9):
                if i != j:
                    self.assertTrue(re.fullmatch(r"(a*)b\1", "a" * i + "b" + "a" * i))
                    self.assertFalse(re.fullmatch(r"(a*)b\1", "a" * j + "b" + "a" * i))
        parse = _load(E + "implementations/thompson.py", "tp_regex_t2").parse
        for bad in ("(a*)b\\1", "(a)", "a|b", "a\\1"):
            with self.assertRaises(ValueError):
                parse(bad)


if __name__ == "__main__":
    unittest.main()
