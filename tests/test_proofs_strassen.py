"""Checks of the proofs in pairs/matrix-multiplication-naive-vs-strassen/PROOFS.md and
pairs/boolean-matrix-multiplication-naive-vs-strassen/PROOFS.md (the sections after the exact counts).

Every test runs the UNCHANGED implementations on fixed inputs and seeds, over the ranges stated in each test; the
symbolic tests run them on symbolic entries. The written proofs cover the general statements; these tests re-run
their computable facts.
"""
import importlib.util
import random
import tracemalloc
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MM = ROOT / "pairs" / "matrix-multiplication-naive-vs-strassen"
BMM = ROOT / "pairs" / "boolean-matrix-multiplication-naive-vs-strassen"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MM_NAIVE = load(MM / "implementations" / "naive.py", "proofs_mm_naive").matmul_naive
MM_ST = load(MM / "implementations" / "strassen.py", "proofs_mm_strassen")
BMM_NAIVE = load(BMM / "implementations" / "naive.py", "proofs_bmm_naive").bmm_naive
BMM_ST = load(BMM / "implementations" / "strassen_over_integers.py", "proofs_bmm_strassen")
BMM_HARNESS = load(BMM / "harness.py", "proofs_bmm_harness")


def peak_bytes(fn, arg):
    tracemalloc.start()
    try:
        base = tracemalloc.get_traced_memory()[0]
        out = fn(arg)
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    del out
    return peak


def rand_matrix(rng, n, lo, hi):
    return tuple(tuple(rng.randint(lo, hi) for _ in range(n)) for _ in range(n))


def product(A, B):
    n = len(A)
    return [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)] for i in range(n)]


# --- symbolic entries: linear forms in the a's, linear forms in the b's, bilinear forms (a-symbol left) --------

class Lin:
    """A linear form sum c * symbol over symbols of one side ('a' or 'b')."""
    __slots__ = ("side", "t")

    def __init__(self, side, t):
        self.side, self.t = side, t

    def _comb(self, other, sign):
        if isinstance(other, int) and other == 0:
            return self
        assert isinstance(other, Lin) and other.side == self.side
        t = dict(self.t)
        for k, c in other.t.items():
            t[k] = t.get(k, 0) + sign * c
            if t[k] == 0:
                del t[k]
        return Lin(self.side, t)

    def __add__(self, other):
        return self._comb(other, 1)

    __radd__ = __add__

    def __sub__(self, other):
        return self._comb(other, -1)

    def __rsub__(self, other):
        assert isinstance(other, int) and other == 0
        return Lin(self.side, {k: -c for k, c in self.t.items()})

    def __mul__(self, other):
        # The left factor must be an a-form and the right factor a b-form: the products keep the order A ... B,
        # so the expansion never commutes two factors (valid in every ring).
        assert self.side == "a" and isinstance(other, Lin) and other.side == "b"
        out = {}
        for ka, ca in self.t.items():
            for kb, cb in other.t.items():
                out[(ka, kb)] = out.get((ka, kb), 0) + ca * cb
        return Bil({k: c for k, c in out.items() if c})


class Bil:
    __slots__ = ("t",)

    def __init__(self, t):
        self.t = t

    def _comb(self, other, sign):
        if isinstance(other, int) and other == 0:
            return self
        t = dict(self.t)
        for k, c in other.t.items():
            t[k] = t.get(k, 0) + sign * c
            if t[k] == 0:
                del t[k]
        return Bil(t)

    def __add__(self, other):
        return self._comb(other, 1)

    __radd__ = __add__

    def __sub__(self, other):
        return self._comb(other, -1)


class StrassenIdentityTests(unittest.TestCase):
    """mm PROOFS.md section 4 (a): the seven products and the four combinations, expanded as bilinear forms in the
    block symbols with the A-block always left of the B-block (so no commutativity is used), give exactly
    C11 = A11 B11 + A12 B21, C12 = A11 B12 + A12 B22, C21 = A21 B11 + A22 B21, C22 = A21 B12 + A22 B22.
    (1) Independent transcription of the block formulas; (2) the unchanged code of both entries run once above the
    cutoff (n = 32) on symbolic entries, whose output must be the bilinear form sum_k a[i][k] b[k][j] exactly."""

    def test_block_formulas(self):
        def a(*names):  # linear form in A blocks, e.g. a("11", "+22")
            return Lin("a", {nm.lstrip("+-"): (-1 if nm.startswith("-") else 1) for nm in names})

        def b(*names):
            return Lin("b", {nm.lstrip("+-"): (-1 if nm.startswith("-") else 1) for nm in names})

        M1 = a("11", "22") * b("11", "22")
        M2 = a("21", "22") * b("11")
        M3 = a("11") * b("12", "-22")
        M4 = a("22") * b("21", "-11")
        M5 = a("11", "12") * b("22")
        M6 = a("21", "-11") * b("11", "12")
        M7 = a("12", "-22") * b("21", "22")
        C11 = M1 + M4 - M5 + M7
        C12 = M3 + M5
        C21 = M2 + M4
        C22 = M1 - M2 + M3 + M6

        def want(i, j):
            return {(f"{i}{k}", f"{k}{j}"): 1 for k in (1, 2)}

        self.assertEqual(C11.t, want(1, 1))
        self.assertEqual(C12.t, want(1, 2))
        self.assertEqual(C21.t, want(2, 1))
        self.assertEqual(C22.t, want(2, 2))

    def _symbolic_run(self, strassen_fn, n):
        A = tuple(tuple(Lin("a", {(i, k): 1}) for k in range(n)) for i in range(n))
        B = tuple(tuple(Lin("b", {(k, j): 1}) for j in range(n)) for k in range(n))
        return strassen_fn(A, B)

    def test_code_on_symbols(self):
        n = 32
        for fn in (MM_ST._strassen, BMM_ST._strassen):
            C = self._symbolic_run(fn, n)
            for i in range(n):
                for j in range(n):
                    self.assertEqual(C[i][j].t, {((i, k), (k, j)): 1 for k in range(n)}, (i, j))


class CorrectnessTests(unittest.TestCase):
    """mm PROOFS.md section 4, bmm PROOFS.md section 4: seeded random inputs, including sizes that force padding
    (mm entries in [-9, 9]; bmm 0/1 entries at densities 0.05..0.9), n = 0..12, 15, 16, 17, 31, 32, 33, 48, 64, 65."""

    SIZES = list(range(13)) + [15, 16, 17, 31, 32, 33, 48, 64, 65]

    def test_mm(self):
        for n in self.SIZES:
            rng = random.Random(f"mm-proofs|{n}")
            A, B = rand_matrix(rng, n, -9, 9), rand_matrix(rng, n, -9, 9)
            want = product(A, B)
            self.assertEqual(MM_NAIVE((A, B)), want, n)
            self.assertEqual(MM_ST.matmul_strassen((A, B)), want, n)

    def test_bmm(self):
        for n in self.SIZES:
            for p in (0.05, 0.5, 0.9):
                rng = random.Random(f"bmm-proofs|{n}|{p}")
                A = tuple(tuple(int(rng.random() < p) for _ in range(n)) for _ in range(n))
                B = tuple(tuple(int(rng.random() < p) for _ in range(n)) for _ in range(n))
                want = [[int(any(A[i][k] and B[k][j] for k in range(n))) for j in range(n)] for i in range(n)]
                self.assertEqual(BMM_NAIVE((A, B)), want, n)
                self.assertEqual(BMM_ST.bmm_strassen((A, B)), want, n)
                self.assertTrue(BMM_HARNESS.check((A, B), want))


class AdditionCountTests(unittest.TestCase):
    """bmm PROOFS.md section 6: for n = 16 * 2^k the Strassen code performs exactly 5632 * 7^k - 1536 * 4^k additions
    and subtractions (k = 0..3), and the multiplications 4096 * 7^k; n = 16..128, both entries' code."""

    class AddCount:
        __slots__ = ("v",)
        adds = 0
        mults = 0

        def __init__(self, v):
            self.v = v

        @staticmethod
        def _v(x):
            return x.v if isinstance(x, AdditionCountTests.AddCount) else x

        def __add__(self, o):
            AdditionCountTests.AddCount.adds += 1
            return AdditionCountTests.AddCount(self.v + self._v(o))

        __radd__ = __add__

        def __sub__(self, o):
            AdditionCountTests.AddCount.adds += 1
            return AdditionCountTests.AddCount(self.v - self._v(o))

        def __rsub__(self, o):
            AdditionCountTests.AddCount.adds += 1
            return AdditionCountTests.AddCount(self._v(o) - self.v)

        def __mul__(self, o):
            AdditionCountTests.AddCount.mults += 1
            return AdditionCountTests.AddCount(self.v * self._v(o))

        __rmul__ = __mul__

        def __gt__(self, o):
            return self.v > self._v(o)

    def test_counts(self):
        C = self.AddCount
        for k in range(4):
            n = 16 << k
            rng = random.Random(f"strassen-adds|{n}")
            for fn in (MM_ST.matmul_strassen, BMM_ST.bmm_strassen):
                A = tuple(tuple(C(rng.randint(0, 1)) for _ in range(n)) for _ in range(n))
                B = tuple(tuple(C(rng.randint(0, 1)) for _ in range(n)) for _ in range(n))
                C.adds = C.mults = 0
                fn((A, B))
                self.assertEqual(C.adds, 5632 * 7 ** k - 1536 * 4 ** k, (n, fn.__name__))
                self.assertEqual(C.mults, 4096 * 7 ** k, (n, fn.__name__))


class MagnitudeTests(unittest.TestCase):
    """bmm PROOFS.md section 5 (and mm section 7): every value produced by +, - or * inside the Strassen code is at most
    s^2 / 2 in absolute value for 0/1 inputs, and at most 81 s^2 / 2 for entries in [-9, 9], where s is the padded size;
    n = 16, 17, 32, 40, 64, 128 on all-ones (resp. all-9) inputs and on seeded random inputs."""

    class MaxInt:
        __slots__ = ("v",)
        top = 0

        def __init__(self, v):
            self.v = v
            if abs(v) > MagnitudeTests.MaxInt.top:
                MagnitudeTests.MaxInt.top = abs(v)

        @staticmethod
        def _v(x):
            return x.v if isinstance(x, MagnitudeTests.MaxInt) else x

        def __add__(self, o):
            return MagnitudeTests.MaxInt(self.v + self._v(o))

        __radd__ = __add__

        def __sub__(self, o):
            return MagnitudeTests.MaxInt(self.v - self._v(o))

        def __rsub__(self, o):
            return MagnitudeTests.MaxInt(self._v(o) - self.v)

        def __mul__(self, o):
            return MagnitudeTests.MaxInt(self.v * self._v(o))

        __rmul__ = __mul__

        def __gt__(self, o):
            return self.v > self._v(o)

    def test_bounds(self):
        M = self.MaxInt
        for n in (16, 17, 32, 40, 64, 128):
            s = 1
            while s < n:
                s *= 2
            rng = random.Random(f"strassen-mag|{n}")
            cases = [(BMM_ST.bmm_strassen, 1, [[1] * n] * n, [[1] * n] * n),
                     (BMM_ST.bmm_strassen, 1, rand_matrix(rng, n, 0, 1), rand_matrix(rng, n, 0, 1)),
                     (MM_ST.matmul_strassen, 81, [[9] * n] * n, [[-9] * n] * n),
                     (MM_ST.matmul_strassen, 81, rand_matrix(rng, n, -9, 9), rand_matrix(rng, n, -9, 9))]
            for fn, scale, A, B in cases:
                M.top = 0
                fn((tuple(tuple(map(M, r)) for r in A), tuple(tuple(map(M, r)) for r in B)))
                self.assertLessEqual(2 * M.top, scale * s * s, (n, fn.__name__))


class EarlyExitVariantTests(unittest.TestCase):
    """bmm PROOFS.md section 7: a schoolbook variant that stops each entry at its first true term makes exactly n^3
    ANDs on all-zero factors and n^2 on all-one factors (n = 0..40); the entry's own schoolbook makes n^3 on both."""

    @staticmethod
    def early_exit_ands(A, B):
        n, ands = len(A), 0
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    ands += 1
                    if A[i][k] & B[k][j]:
                        break
        return ands

    def test_counts(self):
        for n in range(41):
            zero = tuple(tuple(0 for _ in range(n)) for _ in range(n))
            ones = tuple(tuple(1 for _ in range(n)) for _ in range(n))
            self.assertEqual(self.early_exit_ands(zero, zero), n ** 3)
            self.assertEqual(self.early_exit_ands(ones, ones), n ** 2)


class SpaceTests(unittest.TestCase):
    """mm PROOFS.md section 6, bmm PROOFS.md section 8: Theta(n^2) space. For n = 32, 64, 128 the peak traced
    allocation during the call (instance built before tracing) divided by n^2 is at least 8 (one list slot per output
    entry), at most 400, and varies by a factor of at most 1.5 across the three sizes (a cost growing like n^2.807
    would vary by a factor of 3.06); schoolbook and Strassen, both entries."""

    def test_peaks(self):
        for label, fn, lo, hi in (("mm naive", MM_NAIVE, -9, 9), ("mm strassen", MM_ST.matmul_strassen, -9, 9),
                                  ("bmm naive", BMM_NAIVE, 0, 1), ("bmm strassen", BMM_ST.bmm_strassen, 0, 1)):
            per = []
            for n in (32, 64, 128):
                rng = random.Random(f"strassen-space|{n}")
                inst = (rand_matrix(rng, n, lo, hi), rand_matrix(rng, n, lo, hi))
                per.append(peak_bytes(fn, inst) / (n * n))
            self.assertGreaterEqual(min(per), 8, label)
            self.assertLessEqual(max(per), 400, label)
            self.assertLessEqual(max(per) / min(per), 1.5, (label, per))


class SchemeRecursionTests(unittest.TestCase):
    """mm PROOFS.md section 8: a bilinear scheme for k x k matrices with r products, valid over GF(2), applied
    recursively to blocks multiplies n = k^L matrices over GF(2) with exactly r^L scalar products. Schemes: Strassen's
    (k = 2, r = 7; n = 2, 4, 8, 16) and its Kronecker square (k = 4, r = 49; n = 4, 16), both from search/gf2mm.py and
    both passing its exact verifier; 3 seeded 0/1 matrix pairs per n. Also: log_4 47 rounds to 2.7773."""

    @staticmethod
    def apply(k, terms, A, B, counter):
        n = len(A)
        if n == 1:
            counter[0] += 1
            return [[(A[0][0] * B[0][0]) % 2]]
        m = n // k

        def block(M, i, j):
            return [row[j * m:(j + 1) * m] for row in M[i * m:(i + 1) * m]]

        def add(X, Y):
            return [[(x + y) % 2 for x, y in zip(rx, ry)] for rx, ry in zip(X, Y)]

        zero = [[0] * m for _ in range(m)]
        C = [[zero for _ in range(k)] for _ in range(k)]
        for a, b, c in terms:
            left, right = zero, zero
            for i in range(k):
                for j in range(k):
                    if (a >> (i * k + j)) & 1:
                        left = add(left, block(A, i, j))
                    if (b >> (i * k + j)) & 1:
                        right = add(right, block(B, i, j))
            prod = SchemeRecursionTests.apply(k, terms, left, right, counter)
            for l in range(k):
                for i in range(k):
                    if (c >> (l * k + i)) & 1:
                        C[i][l] = add(C[i][l], prod)
        return [sum((C[i][l][r] for l in range(k)), []) for i in range(k) for r in range(m)]

    def test_recursion(self):
        import math
        import sys
        sys.path.insert(0, str(ROOT))
        from search import gf2mm
        st = gf2mm.strassen_scheme()
        fmt4, st2 = gf2mm.kron_scheme((2, 2, 2), st, (2, 2, 2), st)
        self.assertTrue(gf2mm.verify((2, 2, 2), st))
        self.assertTrue(gf2mm.verify(fmt4, st2))
        self.assertEqual((len(st), tuple(fmt4), len(st2)), (7, (4, 4, 4), 49))
        for k, terms, sizes in ((2, st, (2, 4, 8, 16)), (4, st2, (4, 16))):
            r = len(terms)
            for n in sizes:
                L = round(math.log(n, k))
                for seed in range(3):
                    rng = random.Random(f"scheme-rec|{k}|{n}|{seed}")
                    A = [[rng.randint(0, 1) for _ in range(n)] for _ in range(n)]
                    B = [[rng.randint(0, 1) for _ in range(n)] for _ in range(n)]
                    counter = [0]
                    C = self.apply(k, terms, A, B, counter)
                    want = [[sum(A[i][t] * B[t][j] for t in range(n)) % 2 for j in range(n)] for i in range(n)]
                    self.assertEqual(C, want, (k, n, seed))
                    self.assertEqual(counter[0], r ** L, (k, n))
        self.assertEqual(round(math.log(47) / math.log(4), 4), 2.7773)


if __name__ == "__main__":
    unittest.main()
