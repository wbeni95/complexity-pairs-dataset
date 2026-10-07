"""Checks for pairs/assignment-brute-vs-hungarian/PROOFS.md.

Enumeration: exactly n! permutations and n * n! matrix reads; the documented equivalent code of
itertools.permutations yields the same tuples with sum_{k<n} n!/k! loop iterations and rotated entries. Hungarian
method: at most i iterations for row i, at most n(n + 1)/2 iterations and n(n + 1)(2n + 1)/6 reduced-cost
evaluations in all; the potentials satisfy the invariants (J1)-(J3) before every row and certify optimality at the
end (read from the running frame with sys.settrace; the code is unchanged); optimality against an independent subset
DP; the maximisation reduction; and the space bounds. Only upper bounds are checked for the counts. All inputs come
from fixed seeds. Runs in a few seconds.
"""
import importlib.util
import itertools
import math
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "assignment-brute-vs-hungarian"
sys.path.insert(0, str(REPO / "tests"))

from proof_space import peak_words  # noqa: E402


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = _load(E / "harness.py", "tp_asg_h")
BRUTE_FILE = E / "implementations" / "brute_force.py"
HUNG_FILE = E / "implementations" / "hungarian.py"
BRUTE = _load(BRUTE_FILE, "tp_asg_b").assignment_brute
HUNG = _load(HUNG_FILE, "tp_asg_hu").assignment_hungarian


class CountingRows(tuple):
    """An outer matrix tuple that records the index of every row read."""
    def __new__(cls, rows, log, inner_log):
        obj = super().__new__(cls, tuple(CountingRow(r, inner_log) for r in rows))
        obj.log = log
        return obj

    def __getitem__(self, i):
        self.log.append(i)
        return tuple.__getitem__(self, i)


class CountingRow(tuple):
    """A matrix row that counts every entry read."""
    def __new__(cls, row, log):
        obj = super().__new__(cls, row)
        obj.log = log
        return obj

    def __getitem__(self, j):
        self.log[0] += 1
        return tuple.__getitem__(self, j)


def counted(C):
    outer, inner = [], [0]
    return CountingRows(C, outer, inner), outer, inner


def mixed_instances(n_values, seeds, tag):
    for n in n_values:
        for t in range(seeds):
            yield n, t, H.generate(n, random.Random(f"tp-asg|{tag}|{n}|{t}"))
        for t in range(seeds):
            rng = random.Random(f"tp-asg|{tag}|u|{n}|{t}")
            yield n, ("u", t), tuple(tuple(rng.randint(-50, 50) for _ in range(n)) for _ in range(n))


def documented_permutations(n):
    """The 'roughly equivalent' code of itertools.permutations from the Python documentation (r = n), with counters:
    returns (tuples, for-loop iterations, rotated entries, largest rotated entries in one pass, largest iterations in
    one pass)."""
    pool = tuple(range(n))
    r = n
    out, iters, rotated, max_rot, max_it = [], 0, 0, 0, 0
    indices = list(range(n))
    cycles = list(range(n, n - r, -1))
    out.append(tuple(pool[i] for i in indices[:r]))
    while n:
        pass_rot = pass_it = 0
        for i in reversed(range(r)):
            iters += 1
            pass_it += 1
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i + 1:] + indices[i:i + 1]
                rotated += n - i
                pass_rot += n - i
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                out.append(tuple(pool[i] for i in indices[:r]))      # the documented code yields here
                break
        else:                                                         # the documented code returns here
            max_rot, max_it = max(max_rot, pass_rot), max(max_it, pass_it)
            break
        max_rot, max_it = max(max_rot, pass_rot), max(max_it, pass_it)
    return out, iters, rotated, max_rot, max_it


def _line_of(path, text):
    for k, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip() == text:
            return k
    raise AssertionError(f"line {text!r} not found in {path}")


class AssignmentProofChecks(unittest.TestCase):
    def test_enumeration_counts(self):
        for n in range(0, 9):
            rng = random.Random(f"tp-asg|enum|{n}")
            C = tuple(tuple(rng.randint(-9, 9) for _ in range(n)) for _ in range(n))
            CC, outer, inner = counted(C)
            self.assertEqual(BRUTE(CC), H._subset_dp(C) if n else 0)
            self.assertEqual(len(outer), n * math.factorial(n))
            self.assertEqual(inner[0], n * math.factorial(n))
            perms = list(itertools.permutations(range(n)))
            self.assertEqual(len(perms), math.factorial(n))
            self.assertEqual(len(set(perms)), math.factorial(n))

    def test_documented_permutations_code(self):
        for n in range(0, 9):
            out, iters, rotated, max_rot, max_it = documented_permutations(n)
            self.assertEqual(out, list(itertools.permutations(range(n))), n)
            total = sum(math.factorial(n) // math.factorial(k) for k in range(n))      # sum_{k<n} n!/k!
            self.assertEqual(iters, total, n)
            self.assertEqual(rotated, total, n)
            self.assertLessEqual(total, math.e * math.factorial(n))
            self.assertEqual(max_rot, n * (n + 1) // 2, n)
            self.assertEqual(max_it, n, n)

    def test_hungarian_iteration_and_evaluation_bounds(self):
        for n, t, C in mixed_instances(list(range(0, 31)) + [40, 60], 3, "bounds"):
            CC, outer, inner = counted(C)
            HUNG(CC)
            if n == 0:
                self.assertEqual(outer, [])
                continue
            reads = outer[:-n]                       # the last n row reads belong to the final sum
            self.assertEqual(inner[0] - n >= 0, True)
            evaluations = inner[0] - n               # entry reads in the search loops = reduced-cost evaluations
            self.assertLessEqual(len(reads), n * (n + 1) // 2, (n, t))
            self.assertLessEqual(evaluations, n * (n + 1) * (2 * n + 1) // 6, (n, t))
            # per row: the search for row i (0-based r = i - 1) reads row r first, then only rows < r
            per_row, current = {}, -1
            for r in reads:
                if r > current:
                    current = r
                    self.assertEqual(r, len(per_row), (n, t))
                per_row[current] = per_row.get(current, 0) + 1
            self.assertEqual(sorted(per_row), list(range(n)), (n, t))
            for r, iters in per_row.items():
                self.assertLessEqual(iters, r + 1, (n, t, r))

    def test_hungarian_invariants_and_certificate(self):
        start_line = _line_of(HUNG_FILE, "match[0] = i")
        target = str(HUNG_FILE.resolve())
        checked = 0
        for n, t, C in mixed_instances(list(range(1, 13)) + [20, 30], 2, "inv"):
            states, final = [], {}

            def local(frame, event, arg):
                if event == "line" and frame.f_lineno == start_line:
                    loc = frame.f_locals
                    states.append((loc["i"], list(loc["u"]), list(loc["v"]), list(loc["match"])))
                elif event == "return":
                    loc = frame.f_locals
                    final.update(u=list(loc["u"]), v=list(loc["v"]), match=list(loc["match"]), value=arg)
                return local

            def glob(frame, event, arg):
                if frame.f_code.co_name == "assignment_hungarian" and \
                        str(Path(frame.f_code.co_filename).resolve()) == target:
                    return local
                return None

            sys.settrace(glob)
            try:
                HUNG(C)
            finally:
                sys.settrace(None)
            self.assertEqual(len(states), n)
            for i, u, v, match in states:
                rows_matched = sorted(match[j] for j in range(1, n + 1) if match[j])
                self.assertEqual(rows_matched, list(range(1, i)), (n, t, i))           # (J3)
                self.assertTrue(all(u[x] == 0 for x in range(i, n + 1)), (n, t, i))      # (J3)
                for x in range(1, i):                                                    # (J1)
                    for y in range(1, n + 1):
                        self.assertGreaterEqual(C[x - 1][y - 1] - u[x] - v[y], 0, (n, t, i, x, y))
                for y in range(1, n + 1):                                                # (J2)
                    if match[y]:
                        self.assertEqual(C[match[y] - 1][y - 1] - u[match[y]] - v[y], 0, (n, t, i, y))
            u, v, match = final["u"], final["v"], final["match"]
            self.assertEqual(sorted(match[1:]), list(range(1, n + 1)))
            for x in range(1, n + 1):
                for y in range(1, n + 1):
                    self.assertGreaterEqual(C[x - 1][y - 1] - u[x] - v[y], 0)
            self.assertEqual(final["value"], sum(u[1:]) + sum(v[1:]))                    # weak-duality certificate
            checked += 1
        self.assertGreater(checked, 50)

    def test_hungarian_optimal(self):
        for n, t, C in mixed_instances(range(0, 10), 4, "opt"):
            self.assertEqual(HUNG(C), H._subset_dp(C) if n else 0, (n, t))

    def test_maximisation_by_negation(self):
        for n in range(0, 8):
            for t in range(4):
                rng = random.Random(f"tp-asg|max|{n}|{t}")
                C = tuple(tuple(rng.randint(-20, 20) for _ in range(n)) for _ in range(n))
                best = max((sum(C[i][p[i]] for i in range(n)) for p in itertools.permutations(range(n))))
                neg = tuple(tuple(-x for x in row) for row in C)
                self.assertEqual(best, -HUNG(neg), (n, t))

    def test_space(self):
        for n in range(0, 7):
            C = H.generate(n, random.Random(f"tp-asg|space|{n}"))
            _, peak_b = peak_words(BRUTE, (C,), BRUTE_FILE)
            self.assertEqual(peak_b, n, n)                       # the current permutation tuple
        for n in list(range(0, 17)) + [24]:
            C = H.generate(n, random.Random(f"tp-asg|space|{n}"))
            _, peak_h = peak_words(HUNG, (C,), HUNG_FILE)
            self.assertEqual(peak_h, 6 * (n + 1) if n else 0, n)  # u, v, match, way, minv, used


if __name__ == "__main__":
    unittest.main()
