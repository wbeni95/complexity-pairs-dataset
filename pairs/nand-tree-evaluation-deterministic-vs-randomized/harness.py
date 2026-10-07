"""Instances: the leaves of a complete binary NAND tree of height h = n, as a sequence of N = 2^n bits.

generate(n, rng): half the time uniformly random bits; half the time a "reluctant" input (every node of value 0
has two children of value 1; every node of value 1 has exactly one child of value 0, on a random side) with a
random root value. Reluctant inputs with root value 0 are the worst case of the randomized algorithm (PROOFS.md,
section 4).

V1 oracle (check): full bottom-up evaluation of every node, level by level (no short-circuiting, no recursion).

V2 (measure: "reported"): the cost is the number of LEAF READS (queries). generate_scaling(n, rng) returns the
right-zero reluctant input of height n with root value 1 (every value-1 node has its 0-child on the right) as a
CountingLeaves sequence, which counts every leaf read made by the UNCHANGED implementations; reported_cost returns
the count. This input is a worst case for the left-first algorithm, which reads all 2^n leaves. For the randomized
algorithm it is the worst case among inputs with root value 1 (expected R1(n) reads); the overall worst case is a
reluctant input with root value 0, with expected R0(n) = 2 R1(n-1) reads, larger by a factor between 1.03 and 1.37 and
of the same order ((1 + sqrt(33))/4)^n (PROOFS.md, section 4).
"""


def reluctant(h, value, side):
    """Leaves of a reluctant tree of height h with the given root value. side(h) -> 0 puts the 0-child of a
    value-1 node on the left, 1 on the right."""
    if h == 0:
        return [value]
    if value == 0:
        return reluctant(h - 1, 1, side) + reluctant(h - 1, 1, side)
    if side(h):
        return reluctant(h - 1, 1, side) + reluctant(h - 1, 0, side)
    return reluctant(h - 1, 0, side) + reluctant(h - 1, 1, side)


def generate(n, rng):
    if rng.random() < 0.5:
        return tuple(rng.randint(0, 1) for _ in range(1 << n))
    return tuple(reluctant(n, rng.randint(0, 1), lambda h: rng.randint(0, 1)))


def check(leaves, output):
    vals = [int(leaves[i]) for i in range(len(leaves))]
    while len(vals) > 1:
        vals = [1 - (vals[2 * i] & vals[2 * i + 1]) for i in range(len(vals) // 2)]
    return output == vals[0]


# --- Exact leaf-read counting for V2 ------------------------------------------------------------------

_reads = 0


class CountingLeaves:
    """A read-only sequence of bits that counts every element access (module counter _reads)."""
    __slots__ = ("bits",)

    def __init__(self, bits):
        self.bits = tuple(bits)

    def __len__(self):
        return len(self.bits)

    def __getitem__(self, i):
        global _reads
        _reads += 1
        return self.bits[i]

    def __eq__(self, other):
        return isinstance(other, CountingLeaves) and self.bits == other.bits

    def __hash__(self):
        return hash(self.bits)


def generate_scaling(n, rng):
    """Right-zero reluctant input of height n, root value 1, as CountingLeaves; resets the read counter."""
    global _reads
    leaves = CountingLeaves(reluctant(n, 1, lambda h: 1))
    _reads = 0
    return leaves


def reported_cost(output):
    """Leaf reads made since the scaling instance was generated."""
    return _reads
