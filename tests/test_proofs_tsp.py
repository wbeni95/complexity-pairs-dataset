"""Checks of the proofs in pairs/tsp-brute-vs-held-karp/PROOFS.md.

Runs the unchanged implementations with in-memory instrumentation only (trace hooks counting line executions and
reading the table at return). Fixed seeds and stated ranges; deterministic.
"""
import importlib.util
import inspect
import itertools
import math
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "tsp-brute-vs-held-karp"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, E / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BRUTE = _load("implementations/brute_force.py", "proofs_tsp_brute").tsp_brute
HK = _load("implementations/held_karp.py", "proofs_tsp_hk").tsp_held_karp
HARNESS = _load("harness.py", "proofs_tsp_harness")


def line_of(func, needle):
    src, start = inspect.getsourcelines(func)
    return start + next(t for t, s in enumerate(src) if needle in s)


def count_lines(func, arg, lines, on_return=None):
    counts = {ln: 0 for ln in lines}

    def local(frame, event, _arg):
        if event == "line" and frame.f_lineno in counts:
            counts[frame.f_lineno] += 1
        elif event == "return" and on_return is not None:
            on_return(frame.f_locals)
        return local

    sys.settrace(lambda f, e, a: local if f.f_code is func.__code__ else None)
    try:
        result = func(arg)
    finally:
        sys.settrace(None)
    return result, counts


def path_oracle(W):
    """Minimum tour length by an independent recursion over Hamiltonian paths from city 0."""
    n = len(W)
    if n <= 1:
        return 0
    best = [math.inf]

    def rec(last, seen, length):
        if len(seen) == n:
            best[0] = min(best[0], length + W[last][0])
            return
        for c in range(n):
            if c not in seen:
                rec(c, seen | {c}, length + W[last][c])

    rec(0, {0}, 0)
    return best[0]


def documented_permutations(m):
    """The documented equivalent code of itertools.permutations(range(m)), instrumented."""
    pool = tuple(range(m))
    n = r = m
    indices = list(range(n))
    cycles = list(range(n, n - r, -1))
    stats = {"dec": 0, "rot": 0, "maxstep": 0}
    out = [tuple(pool[i] for i in indices[:r])]
    while n:
        step = 0
        for i in reversed(range(r)):
            cycles[i] -= 1
            stats["dec"] += 1
            step += 1
            if cycles[i] == 0:
                indices[i:] = indices[i + 1:] + indices[i:i + 1]
                stats["rot"] += n - i
                step += n - i
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                out.append(tuple(pool[i] for i in indices[:r]))
                break
        else:
            stats["maxstep"] = max(stats["maxstep"], step)
            return out, stats
        stats["maxstep"] = max(stats["maxstep"], step)
    return out, stats


class TSPProofs(unittest.TestCase):
    def test_documented_permutations(self):
        for m in range(1, 9):
            out, st = documented_permutations(m)
            self.assertEqual(out, list(itertools.permutations(range(m))))
            total = sum(math.factorial(m) // math.factorial(t) for t in range(m))
            self.assertEqual(st["dec"], total)
            self.assertEqual(st["rot"], total)
            self.assertLess(total, math.e * math.factorial(m))
            self.assertEqual(st["maxstep"], m + m * (m + 1) // 2)

    def test_enumeration(self):
        inner = line_of(BRUTE, "cost += W[a][b]")
        body = line_of(BRUTE, "cost = W[0][perm[0]] + W[perm[-1]][0]")
        rng = random.Random(1)
        for n in range(2, 9):
            W = HARNESS.generate(n, rng)
            longest = [0]

            def on_ret(loc):
                longest[0] = len(loc.get("perm", ()))

            result, counts = count_lines(BRUTE, W, [inner, body], on_ret)
            self.assertEqual(counts[body], math.factorial(n - 1), n)
            self.assertEqual(counts[inner], math.factorial(n - 1) * (n - 2), n)
            self.assertEqual(longest[0], n - 1)
            self.assertEqual(result, HK(W))

    def test_held_karp(self):
        kline = line_of(HK, "if S >> k & 1:")
        jline = line_of(HK, "if not (S >> j & 1) or row[j] == math.inf:")
        rng = random.Random(2)
        for n in range(2, 10):
            W = HARNESS.generate(n, rng)
            m = n - 1
            shape = []

            def on_ret(loc):
                if "best" in loc:
                    shape.append((len(loc["best"]), {len(r) for r in loc["best"]}))

            result, counts = count_lines(HK, W, [kline, jline], on_ret)
            self.assertEqual(counts[kline], m * m * 2 ** (m - 1), n)
            self.assertEqual(counts[jline], m * (2 ** m - 1), n)
            self.assertEqual(shape, [(2 ** m, {m})], n)
            if n <= 8:
                self.assertEqual(result, BRUTE(W))
        rng = random.Random(3)
        for _ in range(200):
            n = rng.randint(2, 7)
            W = tuple(tuple(0 if i == j else rng.randint(0, 9) for j in range(n)) for i in range(n))
            want = path_oracle(W)
            self.assertEqual(HK(W), want)
            self.assertEqual(BRUTE(W), want)

    def test_reduction(self):
        for n in (2, 3, 4):
            pairs = [(u, v) for u in range(n) for v in range(n) if u != v]
            for bits in range(1 << len(pairs)):
                arcs = {pairs[t] for t in range(len(pairs)) if bits >> t & 1}
                W = tuple(tuple(0 if u == v else (1 if (u, v) in arcs else 2) for v in range(n)) for u in range(n))
                ham = any(all((c[t], c[(t + 1) % n]) in arcs for t in range(n))
                          for c in ((0,) + p for p in itertools.permutations(range(1, n))))
                self.assertEqual(HK(W) == n, ham, (n, arcs))


if __name__ == "__main__":
    unittest.main()
