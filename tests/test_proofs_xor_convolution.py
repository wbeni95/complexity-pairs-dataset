"""Checks of the proofs in pairs/xor-convolution-naive-vs-walsh-hadamard/PROOFS.md (sections 3 to 9).

Every test runs the UNCHANGED implementations (and, for the quantum remark, lib/qsim.py) on fixed inputs and seeds,
over the ranges stated in each test. The written proofs cover the general statements; these tests re-run their
computable facts.
"""
import importlib.util
import random
import tracemalloc
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "xor-convolution-naive-vs-walsh-hadamard"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NAIVE = load(ENTRY / "implementations" / "naive.py", "proofs_xorc_naive").xor_convolution_naive
FW = load(ENTRY / "implementations" / "fwht.py", "proofs_xorc_fwht")
FAST = FW.xor_convolution_fwht
QSIM = load(ROOT / "lib" / "qsim.py", "proofs_xorc_qsim")


def chi(s, x):
    return -1 if bin(s & x).count("1") & 1 else 1


def walsh(n):
    size = 1 << n
    return [[chi(x, y) for y in range(size)] for x in range(size)]


def definition(a, b):
    size = len(a)
    h = [0] * size
    for i in range(size):
        for j in range(size):
            h[i ^ j] += a[i] * b[j]
    return h


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


class MaxInt:
    """An integer that records the largest absolute value of every sum, difference and product it produces."""
    __slots__ = ("v",)
    top = 0

    def __init__(self, v):
        self.v = v
        if abs(v) > MaxInt.top:
            MaxInt.top = abs(v)

    @staticmethod
    def _v(x):
        return x.v if isinstance(x, MaxInt) else x

    def __add__(self, o):
        return MaxInt(self.v + self._v(o))

    __radd__ = __add__

    def __sub__(self, o):
        return MaxInt(self.v - self._v(o))

    def __rsub__(self, o):
        return MaxInt(self._v(o) - self.v)

    def __mul__(self, o):
        return MaxInt(self.v * self._v(o))

    __rmul__ = __mul__


class TransformTests(unittest.TestCase):
    """PROOFS.md section 4: characters are multiplicative (exhaustive, n = 0..6); _fwht computes W (on every unit
    vector, a complete check of the linear map, n = 0..7); W W = N I (n = 0..7); W is the Kronecker power of
    [[1, 1], [1, -1]] (n = 1..5)."""

    def test_characters_multiplicative(self):
        for n in range(7):
            size = 1 << n
            for s in range(size):
                for i in range(size):
                    for j in range(size):
                        self.assertEqual(chi(s, i ^ j), chi(s, i) * chi(s, j))

    def test_fwht_is_w_and_ww_is_n_i(self):
        for n in range(8):
            size = 1 << n
            w = walsh(n)
            for y in range(size):
                e = [int(i == y) for i in range(size)]
                col = FW._fwht(e)
                self.assertEqual(col, [w[x][y] for x in range(size)], (n, y))
                self.assertEqual(FW._fwht(col), [size * v for v in e], (n, y))

    def test_kronecker(self):
        h1 = [[1, 1], [1, -1]]
        for n in range(1, 6):
            m = [[1]]
            for _ in range(n):
                m = [[x * y for x in ra for y in rb] for ra in h1 for rb in m]
            self.assertEqual(m, walsh(n), n)


class CorrectnessTests(unittest.TestCase):
    """PROOFS.md sections 3 and 4. Both implementations are bilinear in (a, b) over the integers (the FWHT's final
    division is exact), so agreeing with the definition on every pair of unit vectors is a complete check (n = 0..4).
    Seeded random inputs: n = 0..9, 3 per n."""

    def test_unit_pairs_complete(self):
        for n in range(5):
            size = 1 << n
            for i in range(size):
                for j in range(size):
                    a = tuple(int(x == i) for x in range(size))
                    b = tuple(int(x == j) for x in range(size))
                    want = [int(k == i ^ j) for k in range(size)]
                    self.assertEqual(NAIVE((a, b)), want, (n, i, j))
                    self.assertEqual(FAST((a, b)), want, (n, i, j))

    def test_random(self):
        for n in range(10):
            for seed in range(3):
                rng = random.Random(f"xorc-proofs|{n}|{seed}")
                a = tuple(rng.randint(-9, 9) for _ in range(1 << n))
                b = tuple(rng.randint(-9, 9) for _ in range(1 << n))
                want = definition(a, b)
                self.assertEqual(NAIVE((a, b)), want, n)
                self.assertEqual(FAST((a, b)), want, n)


class BitGrowthTests(unittest.TestCase):
    """PROOFS.md section 7: with entries of absolute value below 2^B, the forward transforms stay below 2^(B + n),
    the pointwise products below 2^(2B + 2n), the inverse transform below 2^(2B + 3n). n = 0..12, B = 4 and 10,
    on the constant input 2^B - 1 (which attains 2^n (2^B - 1) in the forward transform) and on 2 seeded inputs."""

    def test_bounds(self):
        for n in range(13):
            size = 1 << n
            for bits in (4, 10):
                top = (1 << bits) - 1
                rng = random.Random(f"xorc-bits|{n}|{bits}")
                cases = [([top] * size, [top] * size), ([top] * size, [-top] * size)]
                cases += [([rng.randint(-top, top) for _ in range(size)],
                           [rng.randint(-top, top) for _ in range(size)]) for _ in range(2)]
                for a, b in cases:
                    MaxInt.top = 0
                    fa = FW._fwht([MaxInt(x) for x in a])
                    fb = FW._fwht([MaxInt(x) for x in b])
                    self.assertLess(MaxInt.top, 1 << (bits + n))
                    prod = [x * y for x, y in zip(fa, fb)]
                    self.assertLess(max(abs(p.v) for p in prod), 1 << (2 * bits + 2 * n))
                    MaxInt.top = 0
                    h = FW._fwht(prod)
                    self.assertLess(MaxInt.top, 1 << (2 * bits + 3 * n))
                    self.assertEqual([x.v // size for x in h], FAST((tuple(a), tuple(b))))
                self.assertEqual(FW._fwht([top] * size)[0], size * top)


class ModTwoTests(unittest.TestCase):
    """PROOFS.md section 8: over Z_2 the transform has rank 1 for n >= 1 (all entries of W are 1 mod 2), so W h mod 2
    does not determine h: e_0 and e_1 have the same transform mod 2 (n = 1..8). Over Z_4 (N a zero divisor, c = 2):
    the transform of 2 * ones is 0 mod 4, and 2 * ones is the XOR convolution of (2 * ones, e_0) (n = 1..8)."""

    def test_rank_one(self):
        for n in range(1, 9):
            size = 1 << n
            t0 = [x % 2 for x in FW._fwht([int(i == 0) for i in range(size)])]
            t1 = [x % 2 for x in FW._fwht([int(i == 1) for i in range(size)])]
            self.assertEqual(t0, t1)
            self.assertEqual(t0, [1] * size)

    def test_zero_divisor_mod_four(self):
        for n in range(1, 9):
            size = 1 << n
            ones2 = [2] * size
            self.assertEqual([x % 4 for x in FW._fwht(ones2)], [0] * size)
            e0 = tuple(int(i == 0) for i in range(size))
            self.assertEqual(FAST((tuple(ones2), e0)), ones2)


class QuantumRemarkTests(unittest.TestCase):
    """PROOFS.md section 9: W = 2^(n/2) H^(x)n, with lib/qsim.py's h_all (one Hadamard gate per qubit, applied as one
    butterfly stage per qubit) as H^(x)n (n = 0..6, every basis state); the Forrelation quantity
    N^(-3/2) sum_y (W f)[y] g[y] equals the double sum N^(-3/2) sum_{x,y} f(x) (-1)^(x.y) g(y) (n = 0..7, seeded)."""

    def test_hadamard(self):
        for n in range(7):
            size = 1 << n
            w = walsh(n)
            for y in range(size):
                st = QSIM.State(n, y)
                st.h_all()
                for x in range(size):
                    self.assertAlmostEqual(st.amp[x].real * 2 ** (n / 2), w[x][y], places=9)
                    self.assertAlmostEqual(st.amp[x].imag, 0.0, places=12)

    def test_forrelation_quantity(self):
        for n in range(8):
            size = 1 << n
            rng = random.Random(f"xorc-forr|{n}")
            f = [rng.choice((-1, 1)) for _ in range(size)]
            g = [rng.choice((-1, 1)) for _ in range(size)]
            one = sum(x * y for x, y in zip(FW._fwht(f), g))
            two = sum(f[x] * chi(x, y) * g[y] for x in range(size) for y in range(size))
            self.assertEqual(one, two, n)


class SpaceTests(unittest.TestCase):
    """PROOFS.md section 6: Theta(2^n) space. Bytes are not words: an int object grows with its bit length, so the upper
    bound is derived for CPython and grows with the integer sizes (valid for every n): with b(bits) the size of an int
    object of that many bits rounded up to 16 bytes, the peak traced allocation during the call (instance built before
    tracing) is at least 8 * 2^n and at most 2^n * (6 * 9 + 5 * b(8 + 3n)) + 4096 bytes for the FWHT (five lists plus
    one transient copy while a list grows, at most 9 bytes per slot, at most five int objects per entry) and at most
    2^n * (9 + b(7 + n)) + 4096 bytes for the naive method; naive n = 4..10, FWHT n = 4..15."""

    @staticmethod
    def int_bytes(bits):
        digits = max(1, -(-bits // 30))
        return 16 * -(-(24 + 4 * digits) // 16)

    def _check(self, fn, ns, bound):
        for n in ns:
            rng = random.Random(f"xorc-space|{n}")
            inst = (tuple(rng.randint(-9, 9) for _ in range(1 << n)), tuple(rng.randint(-9, 9) for _ in range(1 << n)))
            peak = peak_bytes(fn, inst)
            self.assertGreaterEqual(peak, 8 * (1 << n), n)
            self.assertLessEqual(peak, bound(n), n)

    def test_naive(self):
        self._check(NAIVE, range(4, 11), lambda n: (1 << n) * (9 + self.int_bytes(7 + n)) + 4096)

    def test_fast(self):
        self._check(FAST, range(4, 16), lambda n: (1 << n) * (6 * 9 + 5 * self.int_bytes(8 + 3 * n)) + 4096)


if __name__ == "__main__":
    unittest.main()
