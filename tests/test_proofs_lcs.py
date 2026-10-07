"""Checks of the proofs in pairs/lcs-brute-vs-dp/PROOFS.md.

Runs the unchanged implementations with in-memory instrumentation only (trace hooks; a str subclass whose find()
counts the positions it examines and then delegates to str.find). Fixed seeds and stated ranges; deterministic.
"""
import importlib.util
import inspect
import itertools
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "lcs-brute-vs-dp"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, E / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BRUTE = _load("implementations/brute_force.py", "proofs_lcs_brute").lcs_brute
DP = _load("implementations/dp.py", "proofs_lcs_dp").lcs_dp


def subsequences(s):
    return {"".join(c) for r in range(len(s) + 1) for c in itertools.combinations(s, r)}


def lcs_oracle(x, y):
    return max(len(z) for z in subsequences(x) & subsequences(y))


def greedy(x, y):
    """The leftmost-match scan of Lemma 1, on plain strings."""
    j = 0
    for c in x:
        j = y.find(c, j)
        if j < 0:
            return False
        j += 1
    return True


def line_of(func, needle):
    src, start = inspect.getsourcelines(func)
    return start + next(t for t, s in enumerate(src) if needle in s)


class ScanCounter(str):
    examined = 0

    def find(self, c, j=0):
        p = str.find(self, c, j)
        ScanCounter.examined += (p - j + 1) if p >= 0 else max(0, len(self) - j)
        return p


class LCSProofs(unittest.TestCase):
    def test_correct(self):
        small = ["".join(t) for L in range(5) for t in itertools.product("ACG", repeat=L)]
        subs = {s: subsequences(s) for s in small}
        for x in small:
            for y in small:
                want = max(len(z) for z in subs[x] & subs[y])
                self.assertEqual(BRUTE((x, y)), want, (x, y))
                self.assertEqual(DP((x, y)), want, (x, y))
        rng = random.Random(1)
        for _ in range(200):
            x = "".join(rng.choice("ACGT") for _ in range(rng.randint(0, 9)))
            y = "".join(rng.choice("ACGT") for _ in range(rng.randint(0, 9)))
            want = lcs_oracle(x, y)
            self.assertEqual(BRUTE((x, y)), want)
            self.assertEqual(DP((x, y)), want)

        ys = ["".join(t) for L in range(7) for t in itertools.product("AC", repeat=L)]
        xs = ["".join(t) for L in range(5) for t in itertools.product("AC", repeat=L)]
        for y in ys:
            sy = subsequences(y)
            for x in xs:
                self.assertEqual(greedy(x, y), x in sy, (x, y))

    def test_enumeration_cost(self):
        body = line_of(BRUTE, "if mask >> i & 1:")
        top = line_of(BRUTE, "is_common = True")
        rng = random.Random(2)
        for n in range(11):
            for m in sorted({n, max(0, n - 3), n + 3}):
                x = "".join(rng.choice("AC") for _ in range(n))
                y = ScanCounter("".join(rng.choice("ACG") for _ in range(m)))
                per_mask = []  # (iterations, examined) for each mask
                state = {"it": 0, "ex": 0}

                def local(frame, event, _arg):
                    if event == "line":
                        if frame.f_lineno == top:
                            if state.get("open"):
                                per_mask.append((state["it"], ScanCounter.examined - state["ex"]))
                            state.update(open=True, it=0, ex=ScanCounter.examined)
                        elif frame.f_lineno == body:
                            state["it"] += 1
                    elif event == "return" and state.get("open"):
                        per_mask.append((state["it"], ScanCounter.examined - state["ex"]))
                    return local

                sys.settrace(lambda f, e, a: local if f.f_code is BRUTE.__code__ else None)
                try:
                    BRUTE((x, y))
                finally:
                    sys.settrace(None)
                self.assertEqual(len(per_mask), 2 ** n)
                for mask, (it, ex) in enumerate(per_mask):
                    sub = "".join(x[i] for i in range(n) if mask >> i & 1)
                    common = greedy(sub, str(y))  # Lemma 1, checked in test_correct
                    self.assertTrue(min(n, m) <= it + ex <= n + m, (n, m, mask, it, ex))
                    if common:
                        self.assertEqual(it, n)
        for n in range(1, 11):
            x = "".join(rng.choice("ACGT") for _ in range(n))
            count = [0]

            def local2(frame, event, _arg):
                if event == "line" and frame.f_lineno == body:
                    count[0] += 1
                return local2

            sys.settrace(lambda f, e, a: local2 if f.f_code is BRUTE.__code__ else None)
            try:
                self.assertEqual(BRUTE((x, x)), n)
            finally:
                sys.settrace(None)
            self.assertEqual(count[0], n * 2 ** n)

    def test_dp_cost(self):
        body = line_of(DP, "cur[j] = prev[j - 1] + 1 if ca == cb else")
        rng = random.Random(3)
        cases = [(la, lb) for la in range(13) for lb in range(13)] + [(50, 50), (100, 100)]
        for la, lb in cases:
            x = "".join(rng.choice("ACGT") for _ in range(la))
            y = "".join(rng.choice("ACGT") for _ in range(lb))
            count, peak = [0], [0]

            def local(frame, event, _arg):
                if event == "line":
                    if frame.f_lineno == body:
                        count[0] += 1
                    loc = frame.f_locals
                    peak[0] = max(peak[0], len(loc.get("prev", ())) + len(loc.get("cur", ())))
                return local

            sys.settrace(lambda f, e, a: local if f.f_code is DP.__code__ else None)
            try:
                DP((x, y))
            finally:
                sys.settrace(None)
            self.assertEqual(count[0], la * lb, (la, lb))
            self.assertEqual(peak[0], 2 * (lb + 1) if la else lb + 1, (la, lb))


if __name__ == "__main__":
    unittest.main()
