"""Which operations can an instrumented INPUT value observe? Fibonacci fast doubling and chromatic number (round 2026-10-06c).

Question (RL-061 items 3-4, deviation finding F4): can exact operation counts for
  pairs/fibonacci-naive-vs-dp            (fast doubling, Theta(log n)), and
  pairs/chromatic-number-subset-dp-vs-inclusion-exclusion  (inclusion-exclusion, (2 chi + 2) 2^n operations)
be obtained by harness instrumentation alone, i.e. by passing instrumented values in through the instance,
with the implementations unchanged?

Part A (the method actually allowed). `Tracer` is an int-like type that propagates through every arithmetic,
bitwise and shift operator, returns plain ints from __index__/__int__, and logs every dunder call it
receives. The instance's integers (n; and the edge endpoints for the graph) are replaced by Tracers, the
UNCHANGED implementation is run, and the log shows every operation that touches an input-derived value.
Also checked: whether bin() on an int SUBCLASS calls an overridden __index__ (it would be the only hook in
fast doubling).

Part B (a prototype of a DIFFERENT method, not adopted; see the report's decision log). sys.monitoring
(CPython >= 3.12) counts executions of one source line of the unchanged implementation: the loop body of fast
doubling, the multiplication `x = p[S] * a[S]` of inclusion-exclusion and the submask step
`T = (T - 1) & S` of the subset DP. These counts are compared with bit_length(n), chi(G) 2^n and
3^n - 2^n, and fitted for information only.

Run from the repository root:  PYTHONIOENCODING=utf-8 ./.venv/Scripts/python experiments/2026-10-06c_value_reach_probe.py
Deterministic (seeded instances as tools/validate.py seeds them).

Outcome (run 2026-10-06, Python 3.14.2):
  Part A, Fibonacci. Fast doubling on an instrumented n: the whole log is {'__index__': 1} for n = 2^8, 2^16,
    2^32, 2^64, 2^128 and 12345 (results unchanged), although the loop runs bit_length(n) = 9 .. 129 times.
    Bottom-up DP, n = 1000: {'__index__': 1}. bin() of an int subclass with an overridden __index__ makes 0
    calls to it, and so does fast doubling. => nothing instance-derived scales with the work: NOT convertible.
  Part A, chromatic number (validator-seeded G(n, 0.8) instances; results unchanged in every run).
    Inclusion-exclusion, n = 8 / 10 / 12 / 14 (chi = 4 / 6 / 7 / 8): total logged 964 / 3358 / 12719 / 49768, of
    which __invert__ and __rand__ are 2^n - 1 each (the tabulation masks), __index__ 357 / 1171 / 4316 / 16697
    (mostly the a[...] lookups of the tabulation), the rest O(n^2) setup (__or__, __ror__, __rlshift__) plus one
    __add__, one __mod__ and two __eq__. For comparison chi 2^n = 1024 / 6144 / 28672 / 131072 round
    multiplications, none of which appears in the log.
    Subset DP, n = 8 / 10 / 12: __gt__ = 2^n - 1 (the first `c < best` per S, while best is still the instrumented
    n), __and__ = __bool__ = 44 / 75 / 113, __index__ 98 / 142 / 214; against 3^n - 2^n = 6305 / 58025 / 527345
    submask steps, none logged. => NOT convertible by value instrumentation.
  Part B (prototype, not adopted). Line-execution counts are exact: fast doubling's loop body runs
    bit_length(n) times (9, 17, 33, 65, 129); inclusion-exclusion's `x = p[S] * a[S]` runs exactly chi(G) 2^n times
    on n = 10..18 (chi = 6, 7, 7, 8, 8, 8, 8, 9, 10); the subset DP's submask step runs exactly 3^n - 2^n times on
    n = 7..10. Fits (information only, tolerance 0.03): fast doubling vs log(n) + log(2): alpha 1.0000, rivals
    log(n)**2 0.4809 and sqrt(n) 0.0585. IE multiplications chi 2^n vs n 2^n: alpha 0.9714 (inside 0.03 by 0.0014),
    rivals 2^n 1.0737, n^2 2^n 0.8869, 3^n 0.6774 rejected; diagnostic 0.9371 / 1.0084 NOT resolved; local slopes
    0.889 .. 1.076. The implementation's docstring total (2 chi + 2) 2^n (a formula evaluated with the measured
    chi, not a measured count) gives alpha 0.9638 vs n 2^n, which would FAIL at 0.03, and 1.0652 vs 2^n.
"""
import importlib.util
import math
import operator
import random
import sys
from collections import Counter
from pathlib import Path

_s = importlib.util.spec_from_file_location("cv2h", Path(__file__).resolve().parent / "2026-10-07b_count_v2_helpers.py")
H = importlib.util.module_from_spec(_s)
_s.loader.exec_module(H)
V = H.V
REPO = H.REPO


class Tracer:
    log = Counter()
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v


def _binop(name, op, reflected):
    def f(self, other):
        if isinstance(other, Tracer):
            o = other.v
        elif isinstance(other, int):
            o = other
        else:
            return NotImplemented      # e.g. list * Tracer falls back to sequence repetition via __index__
        Tracer.log[name] += 1
        return Tracer(op(o, self.v) if reflected else op(self.v, o))
    return f


for _nm, _op in [("add", operator.add), ("sub", operator.sub), ("mul", operator.mul), ("mod", operator.mod),
                 ("floordiv", operator.floordiv), ("lshift", operator.lshift), ("rshift", operator.rshift),
                 ("and", operator.and_), ("or", operator.or_), ("xor", operator.xor), ("pow", operator.pow)]:
    setattr(Tracer, f"__{_nm}__", _binop(f"__{_nm}__", _op, False))
    setattr(Tracer, f"__r{_nm}__", _binop(f"__r{_nm}__", _op, True))


def _unop(name, op):
    def f(self):
        Tracer.log[name] += 1
        return Tracer(op(self.v))
    return f


for _nm, _op in [("neg", operator.neg), ("invert", operator.invert), ("pos", operator.pos), ("abs", abs)]:
    setattr(Tracer, f"__{_nm}__", _unop(f"__{_nm}__", _op))


def _cmp(name, op):
    def f(self, other):
        Tracer.log[name] += 1
        return op(self.v, other.v if isinstance(other, Tracer) else other)
    return f


for _nm, _op in [("lt", operator.lt), ("le", operator.le), ("gt", operator.gt), ("ge", operator.ge),
                 ("eq", operator.eq), ("ne", operator.ne)]:
    setattr(Tracer, f"__{_nm}__", _cmp(f"__{_nm}__", _op))


def _index(self):
    Tracer.log["__index__"] += 1
    return self.v


def _bool(self):
    Tracer.log["__bool__"] += 1
    return bool(self.v)


def _hash(self):
    Tracer.log["__hash__"] += 1
    return hash(self.v)


Tracer.__index__ = _index
Tracer.__int__ = _index
Tracer.__bool__ = _bool
Tracer.__hash__ = _hash


def plain(x):
    return x.v if isinstance(x, Tracer) else x


# ---------------------------------------------------------------- Part A: Fibonacci
fib_dir = REPO / "pairs" / "fibonacci-naive-vs-dp"
fast = V.load_callable(fib_dir, "implementations/fast_doubling.py:fib_fast_doubling")
dp = V.load_callable(fib_dir, "implementations/dp.py:fib_dp")
print("Part A, Fibonacci fast doubling: operations on the instrumented input n")
for n in [256, 65536, 2 ** 32, 2 ** 64, 2 ** 128, 12345]:
    Tracer.log.clear()
    out = fast(Tracer(n))
    assert plain(out) == fast(n)
    print(f"  n = {n}: result unchanged; log = {dict(Tracer.log)}; loop iterations (bit_length) = {n.bit_length()}")
Tracer.log.clear()
assert plain(dp(Tracer(1000))) == dp(1000)
print(f"  (bottom-up DP, n = 1000: log = {dict(Tracer.log)})")


class IntSub(int):
    calls = 0

    def __index__(self):
        IntSub.calls += 1
        return int(self)


s = bin(IntSub(65536))
print(f"  bin() of an int subclass with overridden __index__: {IntSub.calls} __index__ calls (result {s[:6]}...)")
IntSub.calls = 0
fast(IntSub(65536))
print(f"  fast doubling on that int subclass: {IntSub.calls} __index__ calls")

# ---------------------------------------------------------------- Part A: chromatic number
chr_dir = REPO / "pairs" / "chromatic-number-subset-dp-vs-inclusion-exclusion"
E_CHR = "chromatic-number-subset-dp-vs-inclusion-exclusion"
_, _, chr_h = H.entry_and_harness(E_CHR)
ie = V.load_callable(chr_dir, "implementations/inclusion_exclusion.py:chromatic_inclusion_exclusion")
sdp = V.load_callable(chr_dir, "implementations/subset_dp.py:chromatic_subset_dp")


def scaling_graph(n):
    return chr_h.generate_scaling(n, random.Random(f"{E_CHR}|v2|{n}"))


def traced(graph):
    n, edges = graph
    return Tracer(n), tuple((Tracer(u), Tracer(v)) for u, v in edges)


print("\nPart A, chromatic number: operations on instrumented n and edge endpoints (G(n, 0.8) scaling instances)")
for n in [8, 10, 12, 14]:
    g = scaling_graph(n)
    chi = ie(g)
    for name, fn in (("inclusion-exclusion", ie), ("subset DP", sdp)):
        if name == "subset DP" and n > 12:
            continue
        Tracer.log.clear()
        out = fn(traced(g))
        assert plain(out) == chi
        print(f"  n={n:2d} chi={chi:2d} {name:20s}: total logged = {sum(Tracer.log.values()):7d}  {dict(sorted(Tracer.log.items()))}")
    print(f"         for comparison: 2^n = {2 ** n}, chi*2^n = {chi * 2 ** n}, (2chi+2)*2^n = {(2 * chi + 2) * 2 ** n}, "
          f"3^n - 2^n = {3 ** n - 2 ** n}")

# ---------------------------------------------------------------- Part B: line-execution counts (prototype only)
print("\nPart B (prototype of a different method, NOT adopted): sys.monitoring line-execution counts")
mon = getattr(sys, "monitoring", None)
if mon is None:
    print("  sys.monitoring not available in this Python; Part B skipped")
    sys.exit(0)


def line_of(path, text):
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip().startswith(text):
            return i
    raise ValueError(text)


def count_line(func, lineno, *args):
    tool = 4
    mon.use_tool_id(tool, "count-line-probe")
    hits = 0
    code = func.__code__

    def on_line(c, line):
        nonlocal hits
        if c is code and line == lineno:
            hits += 1
            return None
        return mon.DISABLE

    mon.register_callback(tool, mon.events.LINE, on_line)
    mon.set_local_events(tool, code, mon.events.LINE)
    try:
        func(*args)
    finally:
        mon.set_local_events(tool, code, 0)
        mon.register_callback(tool, mon.events.LINE, None)
        mon.free_tool_id(tool)
        mon.restart_events()
    return hits


L_FAST = line_of(fib_dir / "implementations" / "fast_doubling.py", "c = (a * ((2 * b - a) & MASK)) & MASK")
L_IE = line_of(chr_dir / "implementations" / "inclusion_exclusion.py", "x = p[S] * a[S]")
L_DP = line_of(chr_dir / "implementations" / "subset_dp.py", "T = (T - 1) & S")
fast_ns = [256, 65536, 2 ** 32, 2 ** 64, 2 ** 128]
fast_counts = []
for n in fast_ns:
    c = count_line(fast, L_FAST, n)
    assert c == n.bit_length()
    fast_counts.append(c)
print(f"  fast doubling loop body (line {L_FAST}): {fast_counts} on n = 2^8, 2^16, 2^32, 2^64, 2^128; == bit_length(n)")
H.report("fast doubling line count vs log(n)+log(2)", fast_ns, fast_counts, "log(n) + log(2)", ["log(n)**2", "sqrt(n)"], 0.03)

ie_ns = list(range(10, 19))
ie_counts, chis = [], []
for n in ie_ns:
    g = scaling_graph(n)
    chi = ie(g)
    c = count_line(ie, L_IE, g)
    assert c == chi * 2 ** n, (n, c, chi)
    ie_counts.append(c)
    chis.append(chi)
print(f"  inclusion-exclusion multiplications (line {L_IE}) == chi * 2^n on n = 10..18; chi = {chis}")
ops = [(2 * x + 2) * 2 ** n for x, n in zip(chis, ie_ns)]
H.report("IE multiplications chi*2^n vs n*2**n", ie_ns, ie_counts, "n * 2**n", ["2**n", "n**2 * 2**n", "3**n"], 0.03)
H.report("IE total (2chi+2)*2^n (formula) vs n*2**n", ie_ns, ops, "n * 2**n", ["2**n", "n**2 * 2**n", "3**n"], 0.03)
for n in [7, 8, 9, 10]:
    c = count_line(sdp, L_DP, scaling_graph(n))
    assert c == 3 ** n - 2 ** n, (n, c)
print(f"  subset DP submask steps (line {L_DP}) == 3^n - 2^n on n = 7..10")
