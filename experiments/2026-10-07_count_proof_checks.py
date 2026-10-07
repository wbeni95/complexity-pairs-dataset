"""Exact operation counts: checks of the steps that the proofs in pairs/*/PROOFS.md use.

Every count-based entry with a PROOFS.md proves its exact operation counts there, for all sizes of their domains.
This script checks, on stated finite ranges, the statements of those proofs that the V2 measurements and
experiments/2026-10-07_closed_form_checks.py do not cover: forms stated for a general parameter (not only on the
scaling family), bounds stated for every input, splits of a count into components or operation kinds, counts on
other inputs than the seeded scaling instances, and uncounted loop work that an entry states exactly. A check never
replaces a proof; it covers only the sizes it prints.

Every check runs the UNCHANGED implementation with the entry's own harness counter. Component checks attribute counted
operations to a source line or calling function at run time (wrappers installed in memory around the harness counter
methods, or sys.settrace line events); no file is modified. All inputs come from fixed seeds, so the output is
deterministic.

Usage (repository root):  python experiments/2026-10-07_count_proof_checks.py [group ...]
        groups: strings algebra subsets sat graphs bst query   (default: all)
Output: one line per check, "[group] OK|MISMATCH label: checked range"; then a summary. Exit code 0 iff no mismatch.
Each PROOFS.md cites its checks by group and label.
"""
from __future__ import annotations

import bisect  # noqa: F401  (used by some groups)
import inspect  # noqa: F401
import json
import math  # noqa: F401
import random
import sys
import time
from fractions import Fraction  # noqa: F401
from fractions import Fraction as F  # noqa: F401
from math import comb  # noqa: F401
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from search.machine import set_below_normal_priority  # noqa: E402
from tools.validate import load_callable, load_module, resolve_in_repo  # noqa: E402

PAIRS = REPO / "pairs"


def entry_of(eid):
    return json.loads((PAIRS / eid / "entry.json").read_text(encoding="utf-8"))


def harness_of(eid):
    return load_module(resolve_in_repo(PAIRS / eid, entry_of(eid)["test_harness"]["module"]))


def impl_of(eid, spec):
    return load_callable(PAIRS / eid, spec)


RESULTS = []


def make_record(group):
    def record(label, sizes, mismatches):
        status = "OK" if not mismatches else "MISMATCH"
        shown = "; ".join(f"{c}: counted {a} vs {e}" for c, a, e in mismatches[:6])
        print(f"[{group}] {status:8s} {label}: {sizes}" + (f" | {shown}" if mismatches else ""), flush=True)
        RESULTS.append((group, label, status))
    return record



# --------------------------------------------------------------------------------------------------------------
# group strings: model
# --------------------------------------------------------------------------------------------------------------

def _make_model():
    import sys


    E = "string-matching-naive-vs-kmp"


    def run(record):
        h = harness_of(E)
        naive = impl_of(E, "implementations/naive.py:count_naive")
        kmp_mod = load_module(resolve_in_repo(PAIRS / E, "implementations/kmp.py"))

        def wrap(s):
            return tuple(h.CountingChar(c) for c in s)

        # exact forms on T = a^n, P = a^(m-1) b for general m
        mn, mf, ms = [], [], []
        for m in range(1, 31):
            for n in range(max(m - 1, 0), m + 41):
                T, P = wrap("a" * n), wrap("a" * (m - 1) + "b")
                h._comparisons = 0
                naive((T, P))
                if h._comparisons != (n - m + 1) * m:
                    mn.append(((n, m), h._comparisons, (n - m + 1) * m))
                if m >= 3 and n >= 1:
                    h._comparisons = 0
                    kmp_mod._failure(P)
                    f = h._comparisons
                    if f != 3 * m - 6:
                        mf.append(((n, m), f, 3 * m - 6))
                    h._comparisons = 0
                    kmp_mod.count_kmp((T, P))
                    if h._comparisons - f != 3 * n - m:
                        ms.append(((n, m), h._comparisons - f, 3 * n - m))
        record("naive (n-m+1)m on a^n, a^(m-1)b", "m = 1..30, n = m-1..m+40", mn)
        record("KMP failure table 3m-6 on a^(m-1)b", "m = 3..30", mf)
        record("KMP scan 3n-m on a^n, a^(m-1)b", "m = 3..30, n = m-1..m+40", ms)

        # upper bounds on random inputs
        rng = random.Random("string-matching-bounds")
        bn, bf, bs = [], [], []
        for t in range(3000):
            n = rng.randint(0, 60)
            m = rng.randint(1, 12)
            alpha = rng.choice(["ab", "abc", "a"])
            T = wrap("".join(rng.choice(alpha) for _ in range(n)))
            P = wrap("".join(rng.choice(alpha) for _ in range(m)))
            h._comparisons = 0
            naive((T, P))
            if n >= m and h._comparisons > (n - m + 1) * m:
                bn.append(((n, m), h._comparisons, (n - m + 1) * m))
            h._comparisons = 0
            kmp_mod._failure(P)
            f = h._comparisons
            if f > 3 * (m - 1):
                bf.append(((n, m), f, 3 * (m - 1)))
            h._comparisons = 0
            kmp_mod.count_kmp((T, P))
            if h._comparisons - f > 3 * n:
                bs.append(((n, m), h._comparisons - f, 3 * n))
        record("naive <= (n-m+1)m (n >= m)", "3000 random pairs, n = 0..60, m = 1..12, alphabets a/ab/abc", bn)
        record("KMP failure table <= 3(m-1)", "same 3000 random pairs", bf)
        record("KMP scan <= 3n", "same 3000 random pairs", bs)
    return run


# --------------------------------------------------------------------------------------------------------------
# group strings: strings
# --------------------------------------------------------------------------------------------------------------

def _make_strings():
    import bisect
    import inspect
    import sys
    from math import comb


    MP = "multi-pattern-matching-naive-vs-aho-corasick"
    RX = "regex-matching-backtracking-vs-thompson"
    LIS = "longest-increasing-subsequence"
    SRT = "sorting-insertion-vs-merge"
    INV = "inversion-counting-quadratic-vs-merge"
    ED = "element-distinctness-pairs-vs-sorting"


    def mod_of(eid, rel):
        return load_module(resolve_in_repo(PAIRS / eid, rel))


    def line_of(fn, marker):
        src, start = inspect.getsourcelines(fn)
        return start + next(i for i, s in enumerate(src) if marker in s)


    class Profile:
        """sys.setprofile for the duration of a with-block; handler(frame, event) sees Python calls and returns."""

        def __init__(self, handler):
            self.handler = handler

        def __enter__(self):
            h = self.handler

            def prof(frame, event, arg):
                if event in ("call", "return"):
                    h(frame, event)
            sys.setprofile(prof)

        def __exit__(self, *exc):
            sys.setprofile(None)


    def count_lines(fn, call, lines):
        """Run call() and count the line events of fn's code object at each line number in `lines`."""
        code = fn.__code__
        hits = dict.fromkeys(lines, 0)

        def local(frame, event, arg):
            if event == "line" and frame.f_lineno in hits:
                hits[frame.f_lineno] += 1
            return local

        def glob(frame, event, arg):
            return local if frame.f_code is code else None
        sys.settrace(glob)
        try:
            call()
        finally:
            sys.settrace(None)
        return hits


    def ilog2(n):
        return n.bit_length() - 1


    def clog2(n):
        return (n - 1).bit_length()       # ceil(log2 n) for n >= 1


    def topdown_bounds(n):
        if n <= 1:
            return 0, 0
        l, r = n // 2, n - n // 2
        a1, b1 = topdown_bounds(l)
        a2, b2 = topdown_bounds(r)
        return a1 + a2 + l, b1 + b2 + n - 1


    def bottomup_bounds(n):
        lo = hi = 0
        w = 1
        while w < n:
            for s in range(0, n, 2 * w):
                l, r = min(w, n - s), min(w, max(n - s - w, 0))
                if r:
                    lo += min(l, r)
                    hi += l + r - 1
            w *= 2
        return lo, hi


    def int_inputs(n, rng):
        """Integer lists of length n: random with many ties, strictly increasing, strictly decreasing, constant."""
        return [[rng.randint(-2, 2) for _ in range(n)], list(range(n)), list(range(n, 0, -1)), [5] * n,
                [rng.randint(-n, n) for _ in range(n)]]


    # ------------------------------------------------------------------------------------------------------------
    def check_multi(record):
        h = harness_of(MP)
        naive = impl_of(MP, "implementations/naive.py:count_occurrences_naive")
        kmp_mod = mod_of(MP, "implementations/kmp_each.py")
        ac_mod = mod_of(MP, "implementations/aho_corasick.py")
        ac = ac_mod.count_occurrences_aho_corasick

        def wrap(s):
            return tuple(h.CountingChar(c) for c in s)

        def run(fn, text, patterns):
            inst = (wrap(text), tuple(wrap(p) for p in patterns))
            h._comparisons = 0
            out = fn(inst)
            return h._comparisons, out

        # naive and KMP per pattern on text a^N, pattern a^(j-1) b (general N)
        mn, mk, mf, ms = [], [], [], []
        for j in range(1, 26):
            p = "a" * (j - 1) + "b"
            for N in range(max(j - 1, 0), j + 41):
                c, _ = run(naive, "a" * N, (p,))
                if c != j * (N - j + 1):
                    mn.append(((N, j), c, j * (N - j + 1)))
                c, _ = run(kmp_mod.count_occurrences_kmp_each, "a" * N, (p,))
                h._comparisons = 0
                kmp_mod._failure(wrap(p))
                f = h._comparisons
                if j == 1:
                    exp, ef = N, 0
                elif j == 2:
                    exp, ef = (2 * N, 1) if N >= 1 else (1, 1)
                else:
                    exp, ef = 3 * N + 2 * j - 6, 3 * j - 6
                if c != exp:
                    mk.append(((N, j), c, exp))
                if f != ef:
                    mf.append(((N, j), f, ef))
                if j >= 3 and c - f != 3 * N - j:
                    ms.append(((N, j), c - f, 3 * N - j))
        record("multi naive per pattern j(N-j+1) on a^N, a^(j-1)b", "j = 1..25, N = j-1..j+40", mn)
        record("multi KMP per pattern on a^N: b N, ab 2N (N>=1), a^(j-1)b 3N+2j-6", "j = 1..25, N = j-1..j+40", mk)
        record("multi KMP failure table 0 (b), 1 (ab), 3j-6 (a^(j-1)b, j>=3)", "j = 1..25", mf)
        record("multi KMP scan 3N-j on a^N (j>=3, N>=j-1)", "j = 3..25, N = j-1..j+40", ms)

        # bounds on random V1-style instances (harness.generate), every pattern run on its own
        bn, bz, bf, bs = [], [], [], []
        cases = 0
        for n in range(0, 25):
            for t in range(40):
                text, pats = h.generate(n, random.Random(f"strings-extra|multi|{n}|{t}"))
                N = len(text)
                for p in pats:
                    m = len(p)
                    cases += 1
                    c, _ = run(naive, text, (p,))
                    if c > max(N - m + 1, 0) * m:
                        bn.append(((text, p), c, max(N - m + 1, 0) * m))
                    if m >= N + 2 and c != 0:
                        bz.append(((text, p), c, 0))
                    h._comparisons = 0
                    kmp_mod._failure(wrap(p))
                    f = h._comparisons
                    c, _ = run(kmp_mod.count_occurrences_kmp_each, text, (p,))
                    if f > 3 * (m - 1):
                        bf.append(((text, p), f, 3 * (m - 1)))
                    if c - f > 3 * N:
                        bs.append(((text, p), c - f, 3 * N))
        record("multi naive <= max(N-m+1,0)m per pattern", f"{cases} (text, pattern) pairs from harness.generate, n = 0..24, 40 seeds each", bn)
        record("multi naive 0 comparisons when m >= N+2", "same pairs, those with m >= N+2", bz)
        record("multi KMP failure table <= 3(m-1)", "same pairs", bf)
        record("multi KMP scan <= 3N", "same pairs", bs)

        # Aho-Corasick on the V2 family: per-insertion, per-child failure-link and per-character scan costs
        line_fail = line_of(ac, "fail = [0] * len(children)")
        line_scan = line_of(ac, "visits = [0] * len(children)")
        eq_code, ac_code = h.CountingChar.__eq__.__code__, ac.__code__

        def ac_trace(text, patterns):
            rec = {"ins": {}, "fail": {}, "scan": {}, "children": None}

            def handler(frame, event):
                if event == "call" and frame.f_code is eq_code:
                    top = frame.f_back.f_back
                    if top is None or top.f_code is not ac_code:
                        return
                    ln, loc = top.f_lineno, top.f_locals
                    if ln < line_fail:
                        k = len(loc["ends"]) + 1
                        rec["ins"][k] = rec["ins"].get(k, 0) + 1
                    elif ln < line_scan:
                        k = (loc["u"], loc["ch"].c)
                        rec["fail"][k] = rec["fail"].get(k, 0) + 1
                    else:
                        k = sum(loc["visits"]) + 1
                        rec["scan"][k] = rec["scan"].get(k, 0) + 1
                elif event == "return" and frame.f_code is ac_code:
                    rec["children"] = frame.f_locals["children"]
            inst = (wrap(text), tuple(wrap(p) for p in patterns))
            h._comparisons = 0
            with Profile(handler):
                out = ac(inst)
            rec["total"] = h._comparisons
            rec["out"] = out
            return rec

        def node_strings(children):
            s = {0: ""}
            stack = [0]
            while stack:
                u = stack.pop()
                for ch, v in children[u]:
                    s[v] = s[u] + ch.c
                    stack.append(v)
            return s

        mi, ml, msc, mb = [], [], [], []
        for n in range(1, 21):
            text, pats = h.scaling_strings(n)
            rec = ac_trace(text, pats)
            for j in range(1, n + 1):
                exp = 0 if j == 1 else 2 * j - 3
                if rec["ins"].get(j, 0) != exp:
                    mi.append(((n, j), rec["ins"].get(j, 0), exp))
            s = node_strings(rec["children"])
            cost = {}
            for (u, c), v in rec["fail"].items():
                cost[s[u] + c] = cost.get(s[u] + c, 0) + v
            for v_str in s.values():
                if len(v_str) <= 1:
                    exp = 0
                else:
                    exp = 1 if v_str.endswith("b") else 2
                if cost.get(v_str, 0) != exp:
                    ml.append(((n, v_str), cost.get(v_str, 0), exp))
            if n <= 15:
                for t in range(1, n * n + 1):
                    exp = 1 if n == 1 else (2 if t <= n - 1 else 3)
                    if rec["scan"].get(t, 0) != exp:
                        msc.append(((n, t), rec["scan"].get(t, 0), exp))
            if n >= 2:
                b = sum(rec["ins"].values()) + sum(rec["fail"].values())
                if b != n * n + n - 4:
                    mb.append((n, b, n * n + n - 4))
        record("AC per insertion: 0 (j=1), 2j-3 (j>=2), V2 family", "n = 1..20, every j = 1..n", mi)
        record("AC failure links per node: 1 (a^d b), 2 (a^(d+1)), 0 at depth 1", "n = 1..20, every node", ml)
        record("AC scan per character: 2 for t <= n-1, 3 after (n>=2); 1 at n=1", "n = 1..15, every t = 1..n^2", msc)
        record("AC build (trie + links) n^2+n-4 (n>=2)", "n = 2..20", mb)

        # Aho-Corasick on text a^N with patterns a, aa, ..., a^n (README: N = 1024, n = 32 gives 1551)
        mc = []
        for n in list(range(1, 21)) + [32]:
            Ns = [1024] if n == 32 else range(0, 61)
            for N in Ns:
                pats = tuple("a" * k for k in range(1, n + 1))
                rec = ac_trace("a" * N, pats)
                tri, lk, sc = sum(rec["ins"].values()), sum(rec["fail"].values()), sum(rec["scan"].values())
                exp = (n * (n - 1) // 2, n - 1, N)
                if (tri, lk, sc) != exp or rec["total"] != N + n * (n + 1) // 2 - 1:
                    mc.append(((N, n), (tri, lk, sc, rec["total"]), exp))
                if (N, n) == (1024, 32) and (rec["total"] != 1551 or sum(rec["out"]) != 32272):
                    mc.append(((N, n), (rec["total"], sum(rec["out"])), (1551, 32272)))
        record("AC on a^N, patterns a..a^n: trie n(n-1)/2, links n-1, scan N, total N+n(n+1)/2-1",
               "n = 1..20, N = 0..60; and N = 1024, n = 32 (1551 comparisons, 32272 occurrences)", mc)

        # Aho-Corasick general bounds on random instances: per lookup <= sigma, scan lookups <= 2N,
        # total >= N + L - sigma (P >= 1); sigma = number of distinct characters in the patterns
        child_code = ac_mod._child.__code__
        m1, m2, m3, m0 = [], [], [], []
        cases = 0
        for n in range(0, 25):
            for t in range(40):
                text, pats = h.generate(n, random.Random(f"strings-extra|ac-bounds|{n}|{t}"))
                st = {"stack": [], "max": 0, "scan": 0}

                def handler(frame, event, st=st):
                    if frame.f_code is not child_code:
                        return
                    if event == "call":
                        st["stack"].append(h._comparisons)
                    else:
                        d = h._comparisons - st["stack"].pop()
                        st["max"] = max(st["max"], d)
                        if frame.f_back.f_lineno > line_scan:
                            st["scan"] += 1
                inst = (wrap(text), tuple(wrap(p) for p in pats))
                h._comparisons = 0
                with Profile(handler):
                    ac(inst)
                total = h._comparisons
                N, L = len(text), sum(len(p) for p in pats)
                sigma = len(set("".join(pats)))
                cases += 1
                if st["max"] > sigma:
                    m1.append(((text, pats), st["max"], sigma))
                if st["scan"] > 2 * N:
                    m2.append(((text, pats), st["scan"], 2 * N))
                if pats and total < N + L - sigma:
                    m3.append(((text, pats), total, N + L - sigma))
                if not pats and total != 0:
                    m0.append(((text, pats), total, 0))
        record("AC comparisons per lookup <= sigma", f"{cases} instances from harness.generate, n = 0..24, 40 seeds each", m1)
        record("AC scan lookups <= 2N", "same instances", m2)
        record("AC total >= N+L-sigma (P >= 1)", "same instances, those with P >= 1", m3)
        m0b = []
        for N in range(0, 21):
            c, _ = run(ac, "ab" * N, ())
            if c != 0:
                m0b.append((N, c, 0))
        record("AC with no patterns: 0 comparisons", "P = 0: the same instances with n = 0, and text (ab)^N, N = 0..20", m0 + m0b)


    # ------------------------------------------------------------------------------------------------------------
    def check_regex(record):
        h = harness_of(RX)
        bt = impl_of(RX, "implementations/backtracking.py:match_backtracking")
        memo = impl_of(RX, "implementations/memoized.py:match_memoized")
        th = impl_of(RX, "implementations/thompson.py:match_thompson")
        eq_code = h.CountingChar.__eq__.__code__

        def split(fn, n, key):
            tally = {}

            def handler(frame, event):
                if event == "call" and frame.f_code is eq_code:
                    k = key(frame)
                    tally[k] = tally.get(k, 0) + 1
            inst = h.generate_scaling(n, random.Random(0))
            with Profile(handler):
                out = fn(inst)
            return tally, h._cmps, out

        mb, mm, mt = [], [], []
        for n in range(0, 15):
            tally, total, out = split(bt, n, lambda f: f.f_back.f_back.f_locals["i"] < n)
            got = (tally.get(True, 0), tally.get(False, 0))
            exp = (2 ** n - 1, n * 2 ** n // 2)
            if got != exp or out is not True:
                mb.append((n, got, exp))
        record("regex backtracking split: 2^n-1 in the optional atoms, n2^(n-1) in the plain atoms", "n = 0..14", mb)
        for n in range(0, 41):
            tally, total, out = split(memo, n, lambda f: f.f_back.f_back.f_locals["i"] < n)
            got = (tally.get(True, 0), tally.get(False, 0))
            exp = (n * (n + 1) // 2, n * (n + 1) // 2)
            if got != exp or out is not True:
                mm.append((n, got, exp))
        record("regex memoised split: n(n+1)/2 with i < n, n(n+1)/2 with i >= n", "n = 0..40", mm)
        for n in range(0, 41):
            tally, total, out = split(th, n, lambda f: f.f_back.f_locals["j"])
            if any(tally.get(j, 0) != n + 1 for j in range(n)) or len(tally) != n or out is not True:
                mt.append((n, tally, f"{n + 1} at each j < {n}"))
        record("regex Thompson: n+1 comparisons per text character", "n = 0..40", mt)


    # ------------------------------------------------------------------------------------------------------------
    def check_lis(record):
        h = harness_of(LIS)
        subs_mod = mod_of(LIS, "implementations/subset_enumeration.py")
        dp = impl_of(LIS, "implementations/quadratic_dp.py:lis_quadratic")
        pat = impl_of(LIS, "implementations/patience.py:lis_patience")

        def run(fn, vals):
            a = [h.CountingKey(v) for v in vals]
            h._comparisons = 0
            fn(a)
            return h._comparisons

        rng = random.Random("strings-extra|lis")
        m1, m2 = [], []
        for n in range(0, 13):
            for vals in int_inputs(n, rng):
                c = run(subs_mod.lis_subsets, vals)
                exp = n * 2 ** n // 2 - 2 ** n + 1
                if c != exp:
                    m1.append(((n, vals), c, exp))
        record("LIS subsets n2^(n-1)-2^n+1 on other inputs", "n = 0..12, 5 inputs each (ties, increasing, decreasing, constant, random)", m1)
        ln = line_of(subs_mod.lis_subsets, "if mask >> i & 1:")
        for n in range(0, 11):
            vals = [rng.randint(-3, 3) for _ in range(n)]
            a = [h.CountingKey(v) for v in vals]
            hits = count_lines(subs_mod.lis_subsets, lambda: subs_mod.lis_subsets(a), [ln])
            if hits[ln] != 2 ** n * n:
                m2.append((n, hits[ln], 2 ** n * n))
        record("LIS subsets inner steps 2^n n (line count)", "n = 0..10", m2)
        m3 = []
        for n in range(0, 61):
            for vals in int_inputs(n, rng):
                c = run(dp, vals)
                if c != n * (n - 1) // 2:
                    m3.append(((n, vals[:5]), c, n * (n - 1) // 2))
        record("LIS DP n(n-1)/2 on other inputs", "n = 0..60, 5 inputs each", m3)
        m4 = []
        for n in range(0, 301):
            S = sum(ilog2(j) for j in range(2, n + 1))
            for gaps in ((1, 1), (1, 10), (1000, 10 ** 6)):
                x, vals = -rng.randint(0, 10 ** 6), []
                for _ in range(n):
                    x += rng.randint(*gaps)
                    vals.append(x)
                c = run(pat, vals)
                if c != S:
                    m4.append(((n, gaps), c, S))
        record("LIS patience sum floor(log2 j) on other strictly increasing inputs", "n = 0..300, 3 gap ranges each", m4)
        m5 = []
        listed = {10000: 113631, 30000: 387248, 100000: 1468946, 300000: 4875732}
        for n in list(range(1, 2001)) + list(listed):
            K = ilog2(n)
            S = (n + 1) * K - 2 ** (K + 1) + 2
            direct = sum(ilog2(j) for j in range(2, n + 1))
            if S != direct or (n in listed and S != listed[n]):
                m5.append((n, direct, S))
        record("LIS identity sum_{j<=n} floor(log2 j) = (n+1)K-2^(K+1)+2, and listed V2 values",
               "n = 1..2000 and 10000, 30000, 100000, 300000", m5)


    # ------------------------------------------------------------------------------------------------------------
    def g_values(vals):
        """g_i = number of earlier elements strictly larger than vals[i]."""
        srt, g = [], []
        for i, x in enumerate(vals):
            g.append(i - bisect.bisect_right(srt, x))
            bisect.insort(srt, x)
        return g


    def check_sorting(record):
        h = harness_of(SRT)
        ins_mod = mod_of(SRT, "implementations/insertion_sort.py")
        ms_mod = mod_of(SRT, "implementations/merge_sort.py")
        ins = ins_mod.insertion_sort

        def run(fn, vals):
            a = [h.CountingKey(v) for v in vals]
            h._comparisons = 0
            fn(a)
            return h._comparisons

        rng = random.Random("strings-extra|sorting")
        m1, m2 = [], []
        for n in range(0, 61):
            for vals in int_inputs(n, rng):
                g = g_values(vals)
                exp = sum(g[i] + (1 if g[i] < i else 0) for i in range(1, n))
                c = run(ins, vals)
                if c != exp:
                    m1.append(((n, vals[:5]), c, exp))
                if vals == list(range(n, 0, -1)) and c != n * (n - 1) // 2:
                    m1.append(((n, "decreasing"), c, n * (n - 1) // 2))
        record("insertion sort sum_i g_i+[g_i<i] on other inputs (n(n-1)/2 on strictly decreasing)",
               "n = 0..60, 5 inputs each (ties, increasing, decreasing, constant, random)", m1)
        l_shift = line_of(ins, "a[j + 1] = a[j]")
        l_outer = line_of(ins, "key = a[i]")
        for n in range(1, 41):
            for vals in int_inputs(n, rng):
                a = [h.CountingKey(v) for v in vals]
                h._comparisons = 0
                hits = count_lines(ins, lambda: ins(a), [l_shift, l_outer])
                I = sum(g_values(vals))
                zero_runs = sum(1 for i, gi in enumerate(g_values(vals)) if i >= 1 and gi == i)
                exp = (I, n - 1, n - 1 + I - zero_runs)
                got = (hits[l_shift], hits[l_outer], h._comparisons)
                if got != exp:
                    m2.append(((n, vals[:5]), got, exp))
        record("insertion sort: shifts = I, outer iterations n-1, comparisons n-1+I-#{i: g_i = i}",
               "n = 1..40, 5 inputs each (line counts)", m2)
        m3 = []
        listed = {250: 15574.67, 500: 63461.67, 1000: 250154.67, 2000: 999716.33, 4000: 3990076}
        for n, v in listed.items():
            tot = 0
            for k in range(3):
                vals = h.generate(n, random.Random(f"{SRT}|v2|{n}" + (f"|{k}" if k else "")))
                g = g_values(vals)
                tot += sum(g[i] + (1 if g[i] < i else 0) for i in range(1, n))
            if abs(tot / 3 - v) >= 0.005:
                m3.append((n, round(tot / 3, 2), v))
        record("insertion sort listed V2 means = mean of the instance formula over the 3 seeded instances",
               "n = 250, 500, 1000, 2000, 4000", m3)
        m4 = []
        code = ms_mod.merge_sort.__code__
        for n in list(range(1, 301)) + [511, 512, 513, 1000, 1024]:
            st = {"depth": -1, "touched": {}}

            def handler(frame, event, st=st):
                if frame.f_code is not code:
                    return
                if event == "call":
                    st["depth"] += 1
                    L = len(frame.f_locals["xs"])
                    if L >= 2:
                        st["touched"][st["depth"]] = st["touched"].get(st["depth"], 0) + L
                else:
                    st["depth"] -= 1
            vals = [h.CountingKey(rng.randint(-n, n)) for _ in range(n)]
            with Profile(handler):
                ms_mod.merge_sort(vals)
            levels = len(st["touched"])
            pow2 = n & (n - 1) == 0
            ok = (levels == clog2(n) and sorted(st["touched"]) == list(range(levels))
                  and all(t <= n for t in st["touched"].values())
                  and (all(t == n for t in st["touched"].values()) == (pow2 or n == 1)))
            if not ok:
                m4.append((n, (levels, st["touched"]), clog2(n)))
        record("merge sort: ceil(log2 n) merge levels; each element in at most one merge per level, in exactly one on every level iff n is a power of two",
               "n = 1..300, 511, 512, 513, 1000, 1024", m4)


    # ------------------------------------------------------------------------------------------------------------
    def check_inversions(record):
        h = harness_of(INV)
        allp = impl_of(INV, "implementations/pairs_scan.py:inversions_quadratic")
        mc = impl_of(INV, "implementations/merge_count.py:inversions_merge")

        def run(fn, vals):
            a = tuple(h.CountingKey(v) for v in vals)
            h._comparisons = 0
            fn(a)
            return h._comparisons

        rng = random.Random("strings-extra|inversions")
        m1, m2 = [], []
        for n in range(0, 101):
            lo, hi = topdown_bounds(n)
            for vals in int_inputs(n, rng):
                if n <= 60:
                    c = run(allp, vals)
                    if c != n * (n - 1) // 2:
                        m1.append(((n, vals[:5]), c, n * (n - 1) // 2))
                c = run(mc, vals)
                if not lo <= c <= hi:
                    m2.append(((n, vals[:5]), c, (lo, hi)))
        record("inversions all pairs n(n-1)/2 on other inputs", "n = 0..60, 5 inputs each", m1)
        record("inversions merge bounds on other inputs", "n = 0..100, 5 inputs each", m2)
        m3 = []
        listed = {2000: 19421, 4000: 42827, 8000: 93679, 16000: 203327, 32000: 438368, 64000: 941126}
        for n, v in listed.items():
            lo, hi = topdown_bounds(n)
            inst = h.generate_scaling(n, random.Random(f"{INV}|v2|{n}"))
            mc(inst)
            if not (lo <= v <= hi and h.reported_cost(None) == v):
                m3.append((n, h.reported_cost(None), (v, lo, hi)))
        record("inversions listed V2 values: reproduced (sample 0) and within the merge bounds",
               "n = 2000, 4000, 8000, 16000, 32000, 64000", m3)


    # ------------------------------------------------------------------------------------------------------------
    def check_distinctness(record):
        h = harness_of(ED)
        allp = impl_of(ED, "implementations/all_pairs.py:distinct_all_pairs")
        sa_mod = mod_of(ED, "implementations/sort_adjacent.py")

        def run(fn, vals):
            a = tuple(h.CountingKey(v) for v in vals)
            h._comparisons = 0
            out = fn(a)
            return h._comparisons, out

        rng = random.Random("strings-extra|distinctness")
        m1, m2 = [], []
        for n in range(0, 61):
            for vals in (list(range(n)), list(range(n, 0, -1)), rng.sample(range(-10 ** 9, 10 ** 9), n)):
                c, out = run(allp, vals)
                if c != n * (n - 1) // 2 or out is not True:
                    m1.append(((n, vals[:4]), c, n * (n - 1) // 2))
        record("distinctness all pairs n(n-1)/2 on other distinct inputs", "n = 0..60, 3 inputs each", m1)
        for n in range(2, 41):
            for t in range(12):
                vals = rng.sample(range(10 * n), n)
                if t < 4:
                    i, j = n - 2, n - 1          # only equal pair is the last pair in scan order
                else:
                    i, j = sorted(rng.sample(range(n), 2))
                vals[j] = vals[i]
                first = next((p, q) for p in range(n) for q in range(p + 1, n) if vals[p] == vals[q])
                exp = sum(n - 1 - p for p in range(first[0])) + (first[1] - first[0])
                c, out = run(allp, vals)
                if c != exp or out is not False or (c == n * (n - 1) // 2) != (first == (n - 2, n - 1)):
                    m2.append(((n, first), c, exp))
        record("distinctness all pairs on no-instances: index of the first equal pair in scan order (= n(n-1)/2 iff it is (n-2, n-1))",
               "n = 2..40, 12 inputs each (4 with the last pair equal)", m2)
        m3, m4 = [], []
        for n in range(0, 121):
            lo, hi = bottomup_bounds(n)
            inputs = int_inputs(n, rng) + [rng.sample(range(-10 ** 9, 10 ** 9), n)]
            for vals in inputs:
                a = tuple(h.CountingKey(v) for v in vals)
                h._comparisons = 0
                sa_mod._merge_sort(a)
                cm = h._comparisons
                if not lo <= cm <= hi:
                    m3.append(((n, vals[:4]), cm, (lo, hi)))
                if len(set(vals)) == n:
                    c, out = run(sa_mod.distinct_by_sorting, vals)
                    if c - cm != max(n - 1, 0) or out is not True:
                        m4.append(((n, vals[:4]), c - cm, max(n - 1, 0)))
        record("distinctness bottom-up merge part within run-length bounds on every input", "n = 0..120, 6 inputs each (with and without ties)", m3)
        record("distinctness neighbour tests n-1 on distinct inputs (n >= 1; 0 at n = 0)", "n = 0..120, the distinct inputs among them", m4)
        m5 = []
        lw = line_of(sa_mod._merge_sort, "width *= 2")
        for n in list(range(0, 130)) + [255, 256, 257, 1000]:
            a = [h.CountingKey(v) for v in rng.sample(range(10 * n + 1), n)]
            hits = count_lines(sa_mod._merge_sort, lambda: sa_mod._merge_sort(a), [lw])
            exp = clog2(n) if n >= 1 else 0
            if hits[lw] != exp:
                m5.append((n, hits[lw], exp))
        record("distinctness merge passes ceil(log2 n) (line count)", "n = 0..129, 255, 256, 257, 1000", m5)
        m6 = []
        listed = {1000: 9710, 2000: 21426, 4000: 46876, 8000: 101729, 16000: 219403, 32000: 471108, 64000: 1006063,
                  128000: 2140632}
        for n, v in listed.items():
            lo, hi = bottomup_bounds(n)
            inst = h.generate_scaling(n, random.Random(f"{ED}|v2|{n}"))
            random.seed(f"{ED}|v2|{n}|0|sort, then compare neighbours")
            sa_mod.distinct_by_sorting(inst)
            got = h.reported_cost(None)
            if not (lo <= v - (n - 1) <= hi and got == v):
                m6.append((n, got, (v, lo + n - 1, hi + n - 1)))
        record("distinctness listed V2 values: reproduced (sample 0), merge part within the bounds",
               "n = 1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000", m6)


    def run(record):
        check_multi(record)
        check_regex(record)
        check_lis(record)
        check_sorting(record)
        check_inversions(record)
        check_distinctness(record)
    return run


# --------------------------------------------------------------------------------------------------------------
# group algebra: algebra
# --------------------------------------------------------------------------------------------------------------

def _make_algebra():
    import inspect
    import sys



    def line_of(func, needle):
        src, start = inspect.getsourcelines(func)
        hits = [start + i for i, s in enumerate(src) if needle in s]
        assert len(hits) == 1, (needle, hits)
        return hits[0]


    def closest_pair(record):
        E = "closest-pair-brute-vs-divide-conquer"
        h = harness_of(E)
        dc = load_module(resolve_in_repo(PAIRS / E, "implementations/divide_conquer.py"))
        l_test = line_of(dc._solve, "if dy * dy >= best")
        l_d = line_of(dc._solve, "d = dx * dx + dy * dy")
        l_dx = line_of(dc._solve, "dx = xb - xa")
        l_dy = line_of(dc._solve, "dy = yb - ya")
        orig_mul, orig_pow = h.CountingInt.__mul__, h.CountingInt.__pow__
        tally = {}

        def mul(self, other):
            f = sys._getframe(1)
            key = ("dist2" if f.f_code.co_name == "_dist2" else
                   "test" if f.f_lineno == l_test else "d" if f.f_lineno == l_d else "other")
            tally[key] = tally.get(key, 0) + 1
            return orig_mul(self, other)

        def pw(self, e):
            tally["pow"] = tally.get("pow", 0) + 1
            return orig_pow(self, e)

        lines = {"dx": 0, "dy": 0}

        def tracer(frame, event, arg):
            if frame.f_code is dc._solve.__code__:
                def local(fr, ev, a):
                    if ev == "line":
                        if fr.f_lineno == l_dx:
                            lines["dx"] += 1
                        elif fr.f_lineno == l_dy:
                            lines["dy"] += 1
                    return local
                return local
            return None

        mism = []
        h.CountingInt.__mul__, h.CountingInt.__rmul__, h.CountingInt.__pow__ = mul, mul, pw
        try:
            for n in list(range(2, 61)) + [1000, 4000]:
                tally.clear()
                lines["dx"] = lines["dy"] = 0
                inst = h.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
                sys.settrace(tracer)
                try:
                    dc.closest_pair_dc(inst)
                finally:
                    sys.settrace(None)
                examined, completed = lines["dy"], lines["dx"]
                ok = (tally.get("test", 0) == examined and tally.get("d", 0) == 2 * completed
                      and tally.get("other", 0) == 0
                      and h._mults == tally.get("pow", 0) + tally.get("dist2", 0) + examined + 2 * completed)
                if not ok:
                    mism.append((n, dict(tally), (examined, completed)))
        finally:
            h.CountingInt.__mul__, h.CountingInt.__rmul__, h.CountingInt.__pow__ = orig_mul, orig_mul, orig_pow
        record("closest pair D&C strip scan = examined pairs + 2 x non-breaking pairs",
               "n = 2..60 and n = 1000, 4000 (V2 seeds)", mism)


    def strassen_17(record):
        mism = []
        for E, spec, counter in (("matrix-multiplication-naive-vs-strassen", "implementations/strassen.py", "_mults"),
                                 ("boolean-matrix-multiplication-naive-vs-strassen",
                                  "implementations/strassen_over_integers.py", "_products")):
            h = harness_of(E)
            mod = load_module(resolve_in_repo(PAIRS / E, spec))
            fn = mod.matmul_strassen if hasattr(mod, "matmul_strassen") else mod.bmm_strassen
            orig_naive = mod._naive
            performed = [0]

            def naive(X, Y, _orig=orig_naive):
                performed[0] += len(X) * len(Y) * (len(Y[0]) if Y else 0)
                return _orig(X, Y)
            mod._naive = naive
            try:
                for seed in [f"{E}|v2|17"] + [f"pad17-{s}" for s in range(5)]:
                    performed[0] = 0
                    inst = h.generate_scaling(17, random.Random(seed))
                    fn(inst)
                    got = (getattr(h, counter), performed[0])
                    if got != (24832, 28672):
                        mism.append((f"{E[:6]} {seed}", got, (24832, 28672)))
            finally:
                mod._naive = orig_naive
        record("Strassen n = 17: 24832 counted of 28672 performed (matmul, boolean)",
               "n = 17, the V2 seed and 5 further seeds, both entries", mism)


    def boolean_or_lines(record):
        E = "boolean-matrix-multiplication-naive-vs-strassen"
        h = harness_of(E)
        mod = load_module(resolve_in_repo(PAIRS / E, "implementations/naive.py"))
        l_or = line_of(mod.bmm_naive, "c = c | (A[i][k] & Bt[j][k])")
        cnt = [0]

        def tracer(frame, event, arg):
            if frame.f_code is mod.bmm_naive.__code__:
                def local(fr, ev, a):
                    if ev == "line" and fr.f_lineno == l_or:
                        cnt[0] += 1
                    return local
                return local
            return None
        mism = []
        for n in range(0, 21):
            cnt[0] = 0
            inst = h.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
            sys.settrace(tracer)
            try:
                mod.bmm_naive(inst)
            finally:
                sys.settrace(None)
            if cnt[0] != n ** 3 or h._products != n ** 3:
                mism.append((n, (cnt[0], h._products), n ** 3))
        record("boolean schoolbook: n^3 executions of the OR line", "n = 0..20 (V2 seeds)", mism)


    def karatsuba_equal_halves(record):
        """Planted equal halves; the expected count comes from an independent recursion on Python ints:
        1024 per leaf, except the leaves below the z1 child of a node with x1 = x0 and y1 = y0, which count 0."""
        E = "integer-multiplication-schoolbook-vs-karatsuba"
        h = harness_of(E)
        kar = impl_of(E, "implementations/karatsuba.py:multiply_karatsuba")
        B = 1 << 15

        def expected(x, y, dead):
            L = len(x)
            if L <= 32:
                return 0 if dead else L * L
            m = L // 2
            x0, x1, y0, y1 = x[:m], x[m:], y[:m], y[m:]

            def val(d):
                return sum(v << (15 * i) for i, v in enumerate(d))

            def digits(v, k):
                return [(v >> (15 * i)) & (B - 1) for i in range(k)]
            bad = x1 == x0 and y1 == y0
            dx = digits(abs(val(x1) - val(x0)), m)
            dy = digits(abs(val(y1) - val(y0)), m)
            return (expected(x0, y0, dead) + expected(x1, y1, dead) + expected(dx, dy, dead or bad))

        def build(L, rng):
            if L <= 32:
                return [rng.randrange(1, B // 4) for _ in range(L)], [rng.randrange(1, B // 4) for _ in range(L)]
            x0, y0 = build(L // 2, rng)
            x1, y1 = build(L // 2, rng)
            mode = rng.choice(("rand", "both", "x", "y"))
            if mode == "both":
                x1, y1 = list(x0), list(y0)
            elif mode in ("x", "y"):
                w, _ = build(L // 2, rng)
                if L // 2 > 32 and rng.random() < 0.5:
                    w = w[: L // 4] * 2                  # w with equal halves: plants a bad node inside z1
                if mode == "x":
                    x1, y1 = list(x0), [a + b for a, b in zip(y0, w)]
                else:
                    y1, x1 = list(y0), [a + b for a, b in zip(x0, w)]
            return x0 + x1, y0 + y1

        mism, below = [], 0
        rng = random.Random("karatsuba-equal-halves")
        for t in range(60):
            n = (64, 128, 256)[t % 3]
            x, y = build(n, rng)
            assert all(0 <= d < B for d in x + y)
            h._mults = 0
            kar((tuple(h.CountingDigit(d) for d in x), tuple(h.CountingDigit(d) for d in y)))
            e = expected(x, y, False)
            closed = 3 ** {64: 1, 128: 2, 256: 3}[n] * 1024
            below += e < closed
            if h._mults != e:
                mism.append((f"t={t} n={n}", h._mults, e))
        h._mults = 0
        kar((tuple(h.CountingDigit(7) for _ in range(64)), tuple(h.CountingDigit(7) for _ in range(64))))
        if h._mults != 2048:
            mism.append(("constant digits n=64", h._mults, 2048))
        record("Karatsuba: count = closed form iff no node has equal halves in both factors",
               f"n = 64, 128, 256 on 60 seeded inputs with planted equal halves ({below} below the closed form), "
               "and constant digits at n = 64 (2048)", mism)


    def poly(record):
        E = "polynomial-multiplication-naive-vs-ntt"
        h = harness_of(E)
        naive = impl_of(E, "implementations/naive.py:polymul_naive")
        ntt = load_module(resolve_in_repo(PAIRS / E, "implementations/ntt.py"))
        # schoolbook with planted zero coefficients in A
        mism = []
        for n in range(1, 41):
            for s in range(3):
                rng = random.Random(f"poly-zeros-{n}-{s}")
                A = [rng.randrange(h.P) for _ in range(n)]
                for i in rng.sample(range(n), rng.randrange(n + 1)):
                    A[i] = 0
                B = [rng.randrange(h.P) for _ in range(n)]
                h._mults = 0
                naive((tuple(h.CountingCoeff(c) for c in A), tuple(h.CountingCoeff(c) for c in B)))
                e = sum(1 for c in A if c) * n
                if h._mults != e:
                    mism.append(((n, s), h._mults, e))
        record("poly schoolbook nnz(A) * n with planted zero coefficients", "n = 1..40, 3 seeded inputs per n", mism)

        l_bf = line_of(ntt._ntt, "v = a[k + half] * w % P")
        l_sc = line_of(ntt._ntt, "a[i] = a[i] * n_inv % P")
        orig = h.CountingCoeff.__mul__
        tally = {}

        def mul(self, other):
            f = sys._getframe(1)
            if f.f_code.co_name == "_ntt":
                part = "inv" if f.f_locals["invert"] else "fwd"
                kind = "bfly" if f.f_lineno == l_bf else "scale" if f.f_lineno == l_sc else "?"
                if kind == "bfly" and isinstance(other, h.CountingCoeff):
                    kind = "bfly-two-counting"
                key = (part, kind)
            else:
                name = "polymul_ntt" if f.f_code.co_name in ("polymul_ntt", "<listcomp>") else f.f_code.co_name
                key = ("pointwise" if isinstance(other, h.CountingCoeff) else "pointwise-plain", name)
            tally[key] = tally.get(key, 0) + 1
            return orig(self, other)
        mism = []
        h.CountingCoeff.__mul__ = h.CountingCoeff.__rmul__ = mul
        try:
            for k in range(1, 13):
                n = 1 << k
                tally.clear()
                inst = h.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
                ntt.polymul_ntt(inst)
                want = {("fwd", "bfly"): 2 * n * k, ("pointwise", "polymul_ntt"): 2 * n,
                        ("inv", "bfly"): (k + 1) * n, ("inv", "scale"): 2 * n}
                if tally != want:
                    mism.append((n, dict(tally), want))
        finally:
            h.CountingCoeff.__mul__ = h.CountingCoeff.__rmul__ = orig
        record("NTT split: forward n log2 n each, pointwise 2n, inverse (log2 n + 1) n + 2n; butterfly twiddles plain",
               "n = 2, 4, ..., 4096 (V2 seeds)", mism)


    def run(record):
        closest_pair(record)
        strassen_17(record)
        boolean_or_lines(record)
        karatsuba_equal_halves(record)
        poly(record)
    return run


# --------------------------------------------------------------------------------------------------------------
# group subsets: subsets
# --------------------------------------------------------------------------------------------------------------

def _make_subsets():
    import sys



    def per_kind(h, kinds):
        """Wrap the counting methods of h.CountingInt so that every call is also tallied by kind."""
        tally = {}
        saved = {}
        for name, kind in kinds.items():
            orig = getattr(h.CountingInt, name)
            saved[name] = orig

            def wrapped(self, other, _orig=orig, _kind=kind):
                tally[_kind] = tally.get(_kind, 0) + 1
                return _orig(self, other)
            setattr(h.CountingInt, name, wrapped)
        return tally, saved


    def restore(h, saved):
        for name, orig in saved.items():
            setattr(h.CountingInt, name, orig)


    def transforms(record):
        mism = []
        cases = [
            ("or-convolution-naive-vs-zeta-mobius", "implementations/naive.py:or_convolution_naive", range(0, 10),
             lambda n: {"add": 4 ** n, "mul": 4 ** n}),
            ("or-convolution-naive-vs-zeta-mobius", "implementations/zeta_mobius.py:or_convolution_zeta_mobius",
             range(0, 13), lambda n: {k: v for k, v in (("add", n * 2 ** n), ("sub", n * 2 ** n // 2),
                                                         ("mul", 2 ** n)) if v}),
            ("xor-convolution-naive-vs-walsh-hadamard", "implementations/naive.py:xor_convolution_naive", range(0, 10),
             lambda n: {"add": 4 ** n, "mul": 4 ** n}),
            ("xor-convolution-naive-vs-walsh-hadamard", "implementations/fwht.py:xor_convolution_fwht", range(0, 13),
             lambda n: {k: v for k, v in (("add", 3 * n * 2 ** n // 2), ("sub", 3 * n * 2 ** n // 2),
                                          ("mul", 2 ** n), ("div", 2 ** n)) if v}),
            ("subset-sum-zeta-transform-naive-vs-yates", "implementations/naive.py:zeta_naive", range(0, 12),
             lambda n: {"add": 3 ** n}),
            ("subset-sum-zeta-transform-naive-vs-yates", "implementations/yates.py:zeta_yates", range(0, 13),
             lambda n: {"add": n * 2 ** n // 2} if n else {}),
        ]
        for E, spec, ns, want in cases:
            h = harness_of(E)
            kinds = {"__add__": "add", "__radd__": "add", "__sub__": "sub", "__rsub__": "sub"}
            if hasattr(h.CountingInt, "__mul__"):
                kinds.update({"__mul__": "mul", "__rmul__": "mul"})
            if hasattr(h.CountingInt, "__floordiv__"):
                kinds["__floordiv__"] = "div"
            fn = impl_of(E, spec)
            tally, saved = per_kind(h, kinds)
            try:
                for n in ns:
                    tally.clear()
                    inst = h.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
                    fn(inst)
                    if tally != want(n) or h._ops != sum(want(n).values()):
                        mism.append((f"{spec.split(':')[1]} n={n}", dict(tally), want(n)))
            finally:
                restore(h, saved)
        record("OR and XOR convolution, zeta: counts per operation kind",
               "naive OR/XOR n = 0..9, zeta-Moebius and FWHT n = 0..12, zeta naive n = 0..11, Yates n = 0..12 (V2 seeds)",
               mism)


    def ham_enumeration(record):
        E = "hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion"
        h = harness_of(E)
        import inspect
        pass
        mod = load_module(resolve_in_repo(PAIRS / E, "implementations/enumeration.py"))
        src, start = inspect.getsourcelines(mod.count_hamiltonian_cycles_enumeration)
        l_order = start + next(i for i, s in enumerate(src) if "prev = 0" in s)
        cnt = [0]

        def tracer(frame, event, arg):
            if frame.f_code is mod.count_hamiltonian_cycles_enumeration.__code__:
                def local(fr, ev, a):
                    if ev == "line" and fr.f_lineno == l_order:
                        cnt[0] += 1
                    return local
                return local
            return None
        import math
        mism = []
        for n in range(2, 9):
            for seed in range(3):
                rng = random.Random(f"ham-enum-{n}-{seed}")
                p = rng.choice((0.3, 0.6, 0.9))
                adj = tuple(tuple(h.CountingInt(int(rng.random() < p)) for v in range(n)) for u in range(n))
                h.reset_counter()
                cnt[0] = 0
                sys.settrace(tracer)
                try:
                    mod.count_hamiltonian_cycles_enumeration(adj)
                finally:
                    sys.settrace(None)
                ops = dict(h._ops)
                ok = (cnt[0] == math.factorial(n - 1) and ops["compare"] == ops["mul"] == ops["add"] == 0
                      and ops["truth"] <= math.factorial(n))
                if not ok:
                    mism.append(((n, seed), (cnt[0], ops), math.factorial(n - 1)))
        record("Hamiltonian enumeration: (n-1)! orders on random digraphs, truth tests only",
               "n = 2..8, 3 seeded random digraphs per n (densities 0.3/0.6/0.9)", mism)


    def linear_ordering(record):
        import inspect
        import math
        pass
        E = "linear-ordering-enumeration-vs-subset-dp"
        h = harness_of(E)
        enum = impl_of(E, "implementations/enumeration.py:linear_ordering_enumeration")
        dpm = load_module(resolve_in_repo(PAIRS / E, "implementations/subset_dp.py"))
        src, start = inspect.getsourcelines(dpm.linear_ordering_subset_dp)
        l_gain = start + next(i for i, s in enumerate(src) if "gain = gain + row[u]" in s)
        l_val = start + next(i for i, s in enumerate(src) if "value = best_s + gain" in s)
        orig_add = h.CountingInt._add
        where = {}

        def add(self, value):
            ln = sys._getframe(2).f_lineno
            key = "gain" if ln == l_gain else "value" if ln == l_val else "other"
            where[key] = where.get(key, 0) + 1
            return orig_add(self, value)
        mism = []
        for n in range(0, 9):
            for seed in range(3):
                rng = random.Random(f"lo-other-{n}-{seed}")
                w = tuple(tuple(h.CountingInt(rng.randint(-9, 9)) for _ in range(n)) for _ in range(n))
                h.reset_counter()
                enum(w)
                want = {"add": math.factorial(n) * n * (n - 1) // 2, "compare": math.factorial(n) - 1}
                if h.counts_by_kind() != want:
                    mism.append((f"enum n={n} s={seed}", h.counts_by_kind(), want))
        h.CountingInt._add = add
        try:
            for n in range(0, 13):
                for seed in range(3):
                    rng = random.Random(f"lo-other-{n}-{seed}")
                    w = tuple(tuple(h.CountingInt(rng.randint(-9, 9)) for _ in range(n)) for _ in range(n))
                    h.reset_counter()
                    where.clear()
                    dpm.linear_ordering_subset_dp(w)
                    if n >= 2:
                        want = {"gain": n * (n - 1) * 2 ** (n - 2), "value": n * 2 ** (n - 1)}
                        wc = n * 2 ** (n - 1) - 2 ** n + 1
                    else:
                        want, wc = {}, 0
                    if where != want or h.counts_by_kind()["compare"] != wc:
                        mism.append((f"dp n={n} s={seed}", (dict(where), h.counts_by_kind()), (want, wc)))
        finally:
            h.CountingInt._add = orig_add
        record("linear ordering: counts per kind on other matrices",
               "enumeration n = 0..8, DP n = 0..12, 3 seeded matrices per n, entries -9..9; DP gain and value additions "
               "separated", mism)


    def first_match_dp(record):
        import inspect
        pass
        E = "first-match-rule-ordering-enumeration-vs-subset-dp"
        h = harness_of(E)
        dpm = load_module(resolve_in_repo(PAIRS / E, "implementations/subset_dp.py"))
        src, start = inspect.getsourcelines(dpm.first_match_order_subset_dp)

        def ln(needle):
            hits = [start + i for i, s in enumerate(src) if needle in s]
            assert len(hits) == 1, needle
            return hits[0]
        L = {ln("rules = [[r for r in range(k) if match[i][r]]"): "build-rules",
             ln("masks = [sum(match[i][r] << r"): "build-masks",
             ln("if not (masks[i] & s):"): "capture",
             ln("gain[r] = gain[r] + cost[i][r]"): "gain",
             ln("value = best_s + gain[r]"): "transition",
             ln("if best[t] is None or value < best[t]:"): "compare",
             ln("return best[size - 1] + base"): "final"}
        tally = {}
        orig_op, orig_cmp, orig_bool = h.CountingInt._op, h.CountingInt._cmp, h.CountingInt.__bool__

        def note(depth, kind):
            key = (L.get(sys._getframe(depth).f_lineno, "other"), kind)
            tally[key] = tally.get(key, 0) + 1

        def op(self, kind, value):
            note(3, kind)
            return orig_op(self, kind, value)

        def cmp(self, result):
            note(3, "compare")
            return orig_cmp(self, result)

        def bl(self):
            note(2, "truth")
            return orig_bool(self)
        mism = []
        h.CountingInt._op, h.CountingInt._cmp, h.CountingInt.__bool__ = op, cmp, bl
        try:
            for k in range(1, 13):
                tally.clear()
                inst = h.generate_scaling(k, random.Random(f"{E}|v2|{k}"))
                dpm.first_match_order_subset_dp(inst)
                P = 2 ** k
                want = {("build-rules", "truth"): k * k, ("build-masks", "bit"): k * k, ("build-masks", "add"): k * k,
                        ("capture", "bit"): k * P, ("capture", "truth"): k * P, ("gain", "add"): k * P // 2,
                        ("transition", "add"): k * P // 2, ("final", "add"): 1}
                c = k * P // 2 - P + 1
                if c:
                    want[("compare", "compare")] = c
                if tally != want:
                    mism.append((k, dict(tally), want))
        finally:
            h.CountingInt._op, h.CountingInt._cmp, h.CountingInt.__bool__ = orig_op, orig_cmp, orig_bool
        record("first match DP: components (build, capture, gain, transition, final)", "k = 1..12 (V2 seeds)", mism)


    def run(record):
        transforms(record)
        ham_enumeration(record)
        linear_ordering(record)
        first_match_dp(record)
    return run


# --------------------------------------------------------------------------------------------------------------
# group sat: sat
# --------------------------------------------------------------------------------------------------------------

def _make_sat():
    import sys
    from fractions import Fraction



    def min_cut_sparse(record):
        E = "global-min-cut-brute-vs-stoer-wagner"
        h = harness_of(E)
        bf = impl_of(E, "implementations/brute_force.py:min_cut_brute_force")
        sw = impl_of(E, "implementations/stoer_wagner.py:min_cut_stoer_wagner")
        mism = []
        for n in range(2, 13):
            for seed in range(3):
                rng = random.Random(f"mincut-sparse-{n}-{seed}")
                W = [[0] * n for _ in range(n)]
                for u in range(n):
                    for v in range(u + 1, n):
                        if rng.random() < 0.3:
                            W[u][v] = W[v][u] = rng.randint(1, 9)
                inst = tuple(tuple(h.CountingWeight(x) for x in row) for row in W)
                h._adds = h._cmps = 0
                bf(inst)
                want = (n * (n - 1) * 2 ** n // 8, 2 ** (n - 1) - 2)
                if h.counters() != want:
                    mism.append((f"brute n={n} s={seed}", h.counters(), want))
                h._adds = h._cmps = 0
                sw(inst)
                want = (Fraction((n - 1) * (n - 2) * (n + 3), 6), Fraction(n * (n - 1) * (n - 2), 6) + n - 2)
                if h.counters() != want:
                    mism.append((f"SW n={n} s={seed}", h.counters(), want))
        record("min cut: counts on sparse matrices with zero weights", "n = 2..12, 3 seeded matrices per n (density 0.3)",
               mism)


    def line_no(func, needle):
        import inspect
        src, start = inspect.getsourcelines(func)
        hits = [start + i for i, s in enumerate(src) if needle in s]
        assert len(hits) == 1, (needle, hits)
        return hits[0]


    def horn(record):
        pass
        E = "horn-sat-brute-force-vs-unit-propagation"
        h = harness_of(E)
        bf = load_module(resolve_in_repo(PAIRS / E, "implementations/brute_force.py")).horn_sat_brute_force
        up = load_module(resolve_in_repo(PAIRS / E, "implementations/unit_propagation.py")).horn_sat_unit_propagation
        l_eval = line_no(bf, "if ((mask >> (abs(lit) - 1)) & 1) == (lit > 0):")
        ev = {"x1false": 0, "x1true": 0}

        def tr_bf(frame, event, arg):
            if frame.f_code is bf.__code__:
                def local(fr, e, a):
                    if e == "line" and fr.f_lineno == l_eval:
                        ev["x1true" if fr.f_locals["mask"] & 1 else "x1false"] += 1
                    return local
                return local
            return None
        mism = []
        for n in range(3, 15):
            inst = h.generate_scaling(n, random.Random(0))
            ev["x1false"] = ev["x1true"] = 0
            sys.settrace(tr_bf)
            try:
                bf(inst)
            finally:
                sys.settrace(None)
            total = (2 * n + 13) * 2 ** (n - 2) - 2 * n - 4
            if ev["x1false"] != (n - 1) * 2 ** (n - 1) or ev["x1false"] + ev["x1true"] != total or h._ops != 6 * total:
                mism.append((n, (dict(ev), h._ops), ((n - 1) * 2 ** (n - 1), total, 6 * total)))
        record("Horn brute: evaluations in the x1-false half (n-1)2^(n-1), 6 operations each", "n = 3..14", mism)

        l_while = line_no(up, "while queue:")
        snap = {}

        def tr_up(frame, event, arg):
            if frame.f_code is up.__code__:
                def local(fr, e, a):
                    if e == "line" and fr.f_lineno == l_while and "build" not in snap:
                        snap["build"] = h._ops
                    return local
                return local
            return None
        mism = []
        for n in range(3, 201):
            inst = h.generate_scaling(n, random.Random(0))
            snap.clear()
            sys.settrace(tr_up)
            try:
                up(inst)
            finally:
                sys.settrace(None)
            if snap.get("build") != 7 * n - 5 or h._ops - snap["build"] != 5 * n - 2:
                mism.append((n, (snap.get("build"), h._ops), (7 * n - 5, 12 * n - 7)))
        record("Horn unit propagation: building 7n-5, propagation 5n-2", "n = 3..200", mism)


    def two_sat(record):
        pass
        E = "two-sat-brute-force-vs-scc"
        h = harness_of(E)
        bfm = load_module(resolve_in_repo(PAIRS / E, "implementations/brute_force.py"))
        aptm = load_module(resolve_in_repo(PAIRS / E, "implementations/aspvall_plass_tarjan.py"))
        # brute force: evaluations split into the x1-true half and the x1-false half
        bf = bfm.two_sat_brute_force
        l_eval = line_no(bf, "if ((mask >> (abs(lit) - 1)) & 1) == (lit > 0):")
        ev = {"t": 0, "f": 0}

        def tr(frame, event, arg):
            if frame.f_code is bf.__code__:
                def local(fr, e, a):
                    if e == "line" and fr.f_lineno == l_eval:
                        ev["t" if fr.f_locals["mask"] & 1 else "f"] += 1
                    return local
                return local
            return None
        mism = []
        for n in range(3, 15):
            inst = h.generate_scaling(n, random.Random(0))
            ev["t"] = ev["f"] = 0
            sys.settrace(tr)
            try:
                bf(inst)
            finally:
                sys.settrace(None)
            want_t = (n - 1) * 2 ** (n - 1) + 2 ** (n + 1)
            want_f = 2 ** (n + 1) + 2
            if (ev["t"], ev["f"]) != (want_t, want_f) or h._ops != 6 * (want_t + want_f):
                mism.append((n, (dict(ev), h._ops), (want_t, want_f)))
        record("2-SAT brute: x1 true (n-1)2^(n-1) + 2^(n+1), x1 false 2^(n+1) + 2 evaluations, 6 operations each",
               "n = 3..14", mism)

        # APT: every counted operation attributed to the source line that caused it
        scc = aptm.two_sat_scc
        L = {}
        for needle, key in (("edges = adj[v]", "adj reads"), ("if index[w] == -1:", "index tests"),
                            ("index[w] = low[w] = counter", "tree updates"), ("on_stack[w] = True", "tree updates"),
                            ("elif on_stack[w]:", "on-stack tests"), ("low[v] = min(low[v], index[w])", "low into stack"),
                            ("low[u] = min(low[u], low[v])", "low of parent"), ("if low[v] == index[v]:", "root tests"),
                            ("on_stack[w] = False", "pops"), ("comp[w] = num_comps", "pops"), ("if w == v:", "pops"),
                            ("a = _node(clause[0])", "build"), ("b = _node(clause[-1])", "build"),
                            ("adj[a ^ 1].append(b)", "build"), ("adj[b ^ 1].append(a)", "build")):
            L[line_no(scc, needle)] = key
        tally = {}
        orig_arith, orig_cmp, orig_index = h.CountingLit._arith, h.CountingLit._cmp, h.CountingLit.__index__

        def note():
            f = sys._getframe(2)
            while f is not None and f.f_code is not scc.__code__:
                f = f.f_back
            key = L.get(f.f_lineno, f"line {f.f_lineno}") if f is not None else "outside"
            tally[key] = tally.get(key, 0) + 1

        def arith(self, fn, other=None):
            note()
            return orig_arith(self, fn, other)

        def cmp(self, fn, other):
            note()
            return orig_cmp(self, fn, other)

        def index(self):
            note()
            return orig_index(self)
        mism = []
        h.CountingLit._arith, h.CountingLit._cmp = arith, cmp
        h.CountingLit.__index__ = h.CountingLit.__int__ = index
        try:
            for n in range(3, 120):
                tally.clear()
                inst = h.generate_scaling(n, random.Random(0))
                scc(inst)
                want = {"build": 28 * n + 28, "adj reads": 3 * n + 11, "index tests": 4 * n + 4,
                        "tree updates": 3 * n + 6, "on-stack tests": 3 * n + 2, "low into stack": 33,
                        "low of parent": 3 * n + 4, "root tests": 2 * n + 4, "pops": 3 * n + 6}
                if tally != want or h._ops != 49 * (n + 2):
                    mism.append((n, dict(tally), want))
        finally:
            h.CountingLit._arith, h.CountingLit._cmp = orig_arith, orig_cmp
            h.CountingLit.__index__ = h.CountingLit.__int__ = orig_index
        record("2-SAT Aspvall-Plass-Tarjan: build 28n+28 and the eight Tarjan categories (sum 21n+70)", "n = 3..119",
               mism)


    def xor_sat_gauss(record):
        pass
        E = "xor-sat-brute-force-vs-gaussian-elimination"
        h = harness_of(E)
        g = load_module(resolve_in_repo(PAIRS / E, "implementations/gaussian_elimination.py")).xor_sat_gauss
        l_back = line_no(g, "for k in range(r - 1, -1, -1):")
        snap = {}

        def tr(frame, event, arg):
            if frame.f_code is g.__code__:
                def local(fr, e, a):
                    if e == "line" and fr.f_lineno == l_back and "fwd" not in snap:
                        snap["fwd"] = h._ops
                    return local
                return local
            return None
        orig_bool, orig_xor = h.CountingBit.__bool__, h.CountingBit.__xor__
        kinds = {"bool": 0, "xor": 0}

        def bl(self):
            kinds["bool"] += 1
            return orig_bool(self)

        def xr(self, o):
            kinds["xor"] += 1
            return orig_xor(self, o)
        mism = []
        h.CountingBit.__bool__ = bl
        h.CountingBit.__xor__ = h.CountingBit.__rxor__ = xr
        try:
            for n in range(1, 61):
                inst = h.generate_scaling(n, random.Random(0))
                snap.clear()
                kinds["bool"] = kinds["xor"] = 0
                sys.settrace(tr)
                try:
                    g(inst)
                finally:
                    sys.settrace(None)
                fwd = snap.get("fwd")
                back = h._ops - fwd
                tests_fwd = kinds["bool"]
                xor_total = kinds["xor"]
                want = (n * (n + 1) // 2, (n - 1) * n * (2 * n + 5) // 6, n * (n - 1))
                got = (tests_fwd, fwd - tests_fwd, back)
                if got != want or xor_total != want[1] + want[2] // 2:
                    mism.append((n, got, want))
        finally:
            h.CountingBit.__bool__ = orig_bool
            h.CountingBit.__xor__ = h.CountingBit.__rxor__ = orig_xor
        record("XOR-SAT Gauss: tests n(n+1)/2, XORs (n-1)n(2n+5)/6, back substitution n(n-1)", "n = 1..60", mism)


    def fib(k):
        a, b = 0, 1
        for _ in range(k):
            a, b = b, a + b
        return a


    def mis(record):
        pass
        E = "max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp"
        h = harness_of(E)
        bf = impl_of(E, "implementations/brute_force.py:mwis_brute_force")
        dpm = load_module(resolve_in_repo(PAIRS / E, "implementations/column_dp.py"))
        dp = dpm.mwis_column_dp

        def inst(k, n, rng, wmin):
            w = tuple(tuple(h.CountingInt(rng.randint(wmin, 9)) for _ in range(n)) for _ in range(k))
            d = tuple(tuple(rng.randint(0, 3) for _ in range(max(n - 1, 0))) for _ in range(k - 1))
            return k, n, w, d
        mism = []
        rng = random.Random("mis-brute-random")
        done = 0
        while done < 40:
            k, n = rng.randint(1, 4), rng.randint(0, 4)
            if k * n > 12:
                continue
            x = inst(k, n, rng, 0)
            h.reset_counters()
            bf(x)
            N = k * n
            want = N * 2 ** (N - 1) if N else 0
            if h._ops["add"] != want:
                mism.append(((k, n), h._ops["add"], want))
            done += 1
        record("MIS exhaustive N2^(N-1) on random instances (any k, diagonals, zero weights)",
               "40 seeded instances, k = 1..4, n = 0..4, N <= 12", mism)
        mism = []
        for k in range(1, 7):
            states = [s for s in range(1 << k) if s & (s >> 1) == 0]
            Pk = sum(bin(s).count("1") for s in states)
            for n in range(1, 13):
                for s in range(2):
                    x = inst(k, n, random.Random(f"mis-dp-{k}-{n}-{s}"), 1)
                    h.reset_counters()
                    dp(x)
                    want = n * Pk + (n - 1) * fib(k + 2)
                    if h._ops["add"] != want or len(states) != fib(k + 2):
                        mism.append(((k, n, s), h._ops["add"], want))
        record("MIS DP nP_k+(n-1)F_{k+2} on random diagonal patterns, positive weights",
               "k = 1..6, n = 1..12, 2 seeded instances each", mism)
        l_t = line_no(dp, "if t & s:")
        cnt = [0]

        def tr(frame, event, arg):
            if frame.f_code is dp.__code__:
                def local(fr, e, a):
                    if e == "line" and fr.f_lineno == l_t:
                        cnt[0] += 1
                    return local
                return local
            return None
        mism = []
        for k in range(1, 9):
            cnt[0] = 0
            x = h.king_instance(k, 20, random.Random(f"k{k}n20"))
            sys.settrace(tr)
            try:
                dp(x)
            finally:
                sys.settrace(None)
            if cnt[0] != 19 * fib(k + 2) ** 2:
                mism.append((k, cnt[0], 19 * fib(k + 2) ** 2))
        record("MIS DP compatibility tests (n-1)F_{k+2}^2 at n = 20, k = 1..8", "k = 1..8, n = 20", mism)


    def run(record):
        min_cut_sparse(record)
        horn(record)
        two_sat(record)
        xor_sat_gauss(record)
        mis(record)
    return run


# --------------------------------------------------------------------------------------------------------------
# group graphs: graphs
# --------------------------------------------------------------------------------------------------------------

def _make_graphs():
    import inspect
    import sys



    def line_no(func, needle):
        src, start = inspect.getsourcelines(func)
        hits = [start + i for i, s in enumerate(src) if needle in s]
        assert len(hits) == 1, (needle, hits)
        return hits[0]


    def count_lines(func, args, needle):
        target = line_no(func, needle)
        cnt = [0]

        def tr(frame, event, arg):
            if frame.f_code is func.__code__:
                def local(fr, e, a):
                    if e == "line" and fr.f_lineno == target:
                        cnt[0] += 1
                    return local
                return local
            return None
        sys.settrace(tr)
        try:
            out = func(*args)
        finally:
            sys.settrace(None)
        return cnt[0], out


    def apsp(record):
        E = "all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall"
        bf = load_module(resolve_in_repo(PAIRS / E, "implementations/bellman_ford.py")).apsp_bellman_ford
        fw = load_module(resolve_in_repo(PAIRS / E, "implementations/floyd_warshall.py")).apsp_floyd_warshall
        mism = []
        for n in range(0, 15):
            for seed in range(3):
                rng = random.Random(f"apsp-{n}-{seed}")
                p = (0.1, 0.5, 1.0)[seed]
                W = tuple(tuple(None if (i == j or rng.random() >= p) else rng.randint(0, 20) for j in range(n))
                          for i in range(n))
                m = sum(1 for i in range(n) for j in range(n) if i != j and W[i][j] is not None)
                c1, _ = count_lines(bf, (W,), "d = dist[u] + w")
                c2, _ = count_lines(fw, (W,), "d = dik + Dk[j]")
                if c1 != n * (n - 1) * m or c2 != n ** 3:
                    mism.append(((n, seed), (c1, c2), (n * (n - 1) * m, n ** 3)))
        record("APSP relaxation steps: Bellman-Ford n(n-1)m, Floyd-Warshall n^3 on random digraphs",
               "n = 0..14, 3 seeded digraphs per n (densities 0.1, 0.5, 1.0, weights 0..20)", mism)


    def fib(k):
        a, b = 0, 1
        for _ in range(k):
            a, b = b, a + b
        return a


    def planar(record):
        E = "planar-perfect-matchings-enumeration-vs-kasteleyn"
        h = harness_of(E)
        en = impl_of(E, "implementations/enumeration.py:count_perfect_matchings_enumeration")
        ka = impl_of(E, "implementations/kasteleyn_bareiss.py:count_perfect_matchings_kasteleyn")
        mism = []
        for m in range(1, 31):
            a, b, W = h.ladder(m)
            got = en((a, b, W))
            if got != fib(m + 1) or not h.check((a, b, W), got):
                mism.append((f"ladder m={m}", got, fib(m + 1)))
        for a in (2, 4, 6):
            for b in (2, 4, 6):
                W = h._matrix(a, b, lambda: 1)
                got = ka((a, b, W))
                if got < 2 ** (a * b // 4) or not h.check((a, b, W), got):
                    mism.append((f"grid {a}x{b}", got, 2 ** (a * b // 4)))
        record("ladder answers: F(m+1) matchings on the m x 2 ladder, >= 2^(N/4) on even grids",
               "m = 1..30; unit a x b grids with a, b in {2, 4, 6}", mism)
        mism = []
        rng = random.Random("kasteleyn-random")
        nonzero = zero = 0
        for t in range(300):
            while True:
                a, b = rng.randint(1, 8), rng.randint(1, 8)
                if (a * b) % 2 == 0 and a * b <= 64:
                    break
            W = h._matrix(a, b, lambda: rng.randint(0, 3))
            Wc = tuple(tuple(h.CountingInt(x) for x in row) for row in W)
            h._ops = 0
            out = ka((a, b, Wc))
            val = out.v if isinstance(out, h.CountingInt) else out
            m = a * b // 2
            form = (m - 1) * m * (2 * m - 1) // 2
            truth = h.transfer_matrix_count(a, b, W)
            if val != truth:
                mism.append((f"{a}x{b} t={t}", ("answer", val), truth))
            elif truth != 0:
                nonzero += 1
                if h._ops != form:
                    mism.append((f"{a}x{b} t={t}", h._ops, form))
            else:
                zero += 1
                if h._ops > form:
                    mism.append((f"{a}x{b} t={t} (answer 0)", h._ops, form))
        record("Kasteleyn count on random grids: = form if answer != 0, <= form if 0",
               f"300 seeded random weighted grids with even N <= 64, weights 0..3 ({nonzero} non-zero, {zero} zero answers)",
               mism)


    def kirchhoff(record):
        import math
        E = "spanning-tree-count-enumeration-vs-kirchhoff"
        h = harness_of(E)
        enm = load_module(resolve_in_repo(PAIRS / E, "implementations/enumeration.py"))
        km = load_module(resolve_in_repo(PAIRS / E, "implementations/kirchhoff_bareiss.py"))
        mism = []
        for n in range(1, 9):
            graphs = [tuple(tuple(0 if i == j else 1 for j in range(n)) for i in range(n))]
            for seed in range(3):
                rng = random.Random(f"st-enum-{n}-{seed}")
                A = [[0] * n for _ in range(n)]
                for u in range(n):
                    for v in range(u + 1, n):
                        if rng.random() < 0.5:
                            A[u][v] = A[v][u] = 1
                graphs.append(tuple(tuple(r) for r in A))
            for A in graphs:
                m = sum(A[u][v] for u in range(n) for v in range(u + 1, n))
                c, _ = count_lines(enm.count_spanning_trees_enumeration, (A,), "parent = list(range(n))")
                if c != math.comb(m, n - 1):
                    mism.append((n, c, math.comb(m, n - 1)))
        record("spanning-tree enumeration: C(m, n-1) subsets examined", "n = 1..8, K_n and 3 seeded random graphs per n",
               mism)
        mism = []
        orig = km._bareiss_det
        swaps = [0]

        def wrapped(M):
            # count row swaps by watching the zero-pivot branch: compare rows before and after (in-place algorithm)
            return orig(M)
        for n in range(2, 31):
            for seed in range(6):
                rng = random.Random(f"st-k-{n}-{seed}")
                A = [[0] * n for _ in range(n)]
                if seed < 3:                          # connected: random tree plus random edges
                    for v in range(1, n):
                        u = rng.randrange(v)
                        A[u][v] = A[v][u] = 1
                    p = 0.3
                else:                                 # disconnected: two parts with no edge between them
                    p = 0.5
                cut = rng.randint(1, n - 1)
                for u in range(n):
                    for v in range(u + 1, n):
                        same_side = (u < cut) == (v < cut)
                        if rng.random() < p and (seed < 3 or same_side):
                            A[u][v] = A[v][u] = 1
                Ac = tuple(tuple(h.CountingInt(x) for x in row) for row in A)
                l_swap = line_no(orig, "M[k], M[swap] = M[swap], M[k]")
                cnt = [0]

                def tr(frame, event, arg):
                    if frame.f_code is orig.__code__:
                        def local(fr, e, a):
                            if e == "line" and fr.f_lineno == l_swap:
                                cnt[0] += 1
                            return local
                        return local
                    return None
                h._ops = 0
                sys.settrace(tr)
                try:
                    km.count_spanning_trees_kirchhoff(Ac)
                finally:
                    sys.settrace(None)
                form = (n - 2) * (n - 1) * (2 * n - 3) // 2
                if seed < 3 and (h._ops != form or cnt[0]):
                    mism.append((f"connected n={n} s={seed}", (h._ops, cnt[0]), form))
                if seed >= 3 and h._ops > form:
                    mism.append((f"disconnected n={n} s={seed}", h._ops, form))
        record("Kirchhoff: no swap and the exact count on random connected graphs, at most the count on disconnected ones",
               "n = 2..30, 3 seeded connected and 3 seeded disconnected graphs per n", mism)


    def mst(record):
        import math
        E = "minimum-spanning-tree-brute-vs-kruskal"
        h = harness_of(E)
        brute = impl_of(E, "implementations/brute_force.py:mst_brute")
        prim = impl_of(E, "implementations/prim.py:mst_prim")
        kinds = {"add": 0, "cmp": 0, "other": 0}
        saved = {}
        for name, kind in (("__add__", "add"), ("__radd__", "add"), ("__lt__", "cmp"), ("__le__", "cmp"),
                           ("__gt__", "cmp"), ("__ge__", "cmp"), ("__eq__", "cmp"), ("__ne__", "cmp"),
                           ("__mul__", "other"), ("__rmul__", "other"), ("__divmod__", "other")):
            orig = getattr(h.CountingWeight, name)
            saved[name] = orig

            def w(self, o, _orig=orig, _k=kind):
                kinds[_k] += 1
                return _orig(self, o)
            setattr(h.CountingWeight, name, w)
        mism = []
        try:
            for fn, ns, want in ((brute, range(1, 8), lambda n: {"add": (n - 1) * math.comb(n * (n - 1) // 2, n - 1),
                                                                 "cmp": (n ** (n - 2) if n >= 2 else 1) - 1, "other": 0}),
                                 (prim, range(1, 61), lambda n: {"add": n - 1, "cmp": (n - 1) * (n - 2), "other": 0})):
                for n in ns:
                    for seed in range(2):
                        inst = h.generate_scaling(n, random.Random(f"mst-kinds-{n}-{seed}"))
                        for k in kinds:
                            kinds[k] = 0
                        fn(inst)
                        if kinds != want(n):
                            mism.append((f"{fn.__name__} n={n} s={seed}", dict(kinds), want(n)))
        finally:
            for name, orig in saved.items():
                setattr(h.CountingWeight, name, orig)
        record("MST enumeration and Prim: additions and comparisons separately",
               "enumeration n = 1..7, Prim n = 1..60, 2 seeded weight draws per n", mism)


    def three_xor(record):
        import math
        E = "three-xor-all-triples-vs-patricia-trie"
        h = harness_of(E)
        at = impl_of(E, "implementations/all_triples.py:three_xor_all_triples")
        pm = load_module(resolve_in_repo(PAIRS / E, "implementations/patricia_trie.py"))
        l_pop = line_no(pm._xor_ascending, "node = stack.pop()")
        l_step = line_no(pm.three_xor_patricia_trie, "c = xs[i][0]")
        cnt = {"pop": 0, "step": 0}

        def tr(frame, event, arg):
            code = frame.f_code
            if code is pm._xor_ascending.__code__ or code is pm.three_xor_patricia_trie.__code__:
                def local(fr, e, a):
                    if e == "line":
                        if fr.f_code is pm._xor_ascending.__code__ and fr.f_lineno == l_pop:
                            cnt["pop"] += 1
                        elif fr.f_code is pm.three_xor_patricia_trie.__code__ and fr.f_lineno == l_step:
                            cnt["step"] += 1
                    return local
                return local
            return None
        mism = []
        for w in range(1, 10):
            n = 1 << (w - 1)
            for seed in range(3):
                inst = h.generate_scaling(n, random.Random(f"3xor-other-{n}-{seed}"))
                at(inst)
                want = {"xor": math.comb(n, 2), "and_or": 0, "shift": 0, "compare": math.comb(n, 3), "truth": 0}
                if h.counts() != want:
                    mism.append((f"triples n={n} s={seed}", h.counts(), want))
                h.reset_counter()
                cnt["pop"] = cnt["step"] = 0
                sys.settrace(tr)
                try:
                    pm.three_xor_patricia_trie(inst)
                finally:
                    sys.settrace(None)
                lg = w - 1
                want = {"xor": n * n, "and_or": n * lg + n * (n - 1), "shift": 0, "compare": 4 * n * n - n,
                        "truth": n * lg + n * (n - 1)}
                if h.counts() != want or cnt != {"pop": n * (2 * n - 1), "step": n * (2 * n - 1)}:
                    mism.append((f"trie n={n} s={seed}", (h.counts(), dict(cnt)), want))
                h.reset_counter()
        record("3XOR: counts on other shuffles, per kind, and per-round node visits and merge steps",
               "n = 1, 2, 4, ..., 256, 3 other shuffles each", mism)


    def run(record):
        apsp(record)
        planar(record)
        kirchhoff(record)
        mst(record)
        three_xor(record)
    return run


# --------------------------------------------------------------------------------------------------------------
# group bst: bst
# --------------------------------------------------------------------------------------------------------------

def _make_bst():
    import inspect
    import sys


    OB = "optimal-bst-recursion-vs-dp-vs-knuth"
    MC = "max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp"


    # ------------------------------------------------------------------------------------------------------------------
    # Tracing helpers (sys.setprofile / sys.settrace; no file is modified)
    # ------------------------------------------------------------------------------------------------------------------

    def run_profiled(thunk, call_code=None, return_code=None, names=()):
        """Run thunk(); count calls of call_code and snapshot the locals `names` of return_code at its return."""
        calls, snap = [0], {}

        def prof(frame, event, arg):
            if event == "call" and frame.f_code is call_code:
                calls[0] += 1
            elif event == "return" and frame.f_code is return_code:
                loc = frame.f_locals
                for nm in names:
                    snap[nm] = loc[nm]
        sys.setprofile(prof)
        try:
            thunk()
        finally:
            sys.setprofile(None)
        return calls[0], snap


    def line_of(fn, marker):
        src, start = inspect.getsourcelines(fn)
        hits = [start + i for i, s in enumerate(src) if marker in s]
        assert len(hits) == 1, (marker, hits)
        return hits[0]


    def line_hits(fn, marker, thunk, key=None):
        """Executions of the unique line of fn containing `marker` during thunk(); with `key`, a dict keyed by the
        value of that local variable at each execution."""
        target, code = line_of(fn, marker), fn.__code__
        out = {}

        def tracer(frame, event, arg):
            if frame.f_code is code:
                def local(fr, ev, a):
                    if ev == "line" and fr.f_lineno == target:
                        k = fr.f_locals[key] if key else None
                        out[k] = out.get(k, 0) + 1
                    return local
                return local
            return None
        sys.settrace(tracer)
        try:
            thunk()
        finally:
            sys.settrace(None)
        return out if key else out.get(None, 0)


    def wrap_pq(h, p, q):
        return tuple(h.CountingInt(x) for x in p), tuple(h.CountingInt(x) for x in q)


    def V(x):
        return x.v if hasattr(x, "v") else x


    # ------------------------------------------------------------------------------------------------------------------
    # Optimal BST
    # ------------------------------------------------------------------------------------------------------------------

    def obst_inputs(h, n, seed):
        """The ten V1 families of the entry, plus two signed kinds (any integer values: the counts do not use signs)."""
        out = []
        for fam in h.FAMILIES:
            p, q = h._instance(n, random.Random(f"bst-extra|{fam}|{n}|{seed}"), fam)
            out.append((fam, p, q))
        rng = random.Random(f"bst-extra|signed|{n}|{seed}")
        out.append(("signed", [rng.randint(-20, 20) for _ in range(n)], [rng.randint(-20, 20) for _ in range(n + 1)]))
        out.append(("wide-signed", [rng.randint(-10 ** 6, 10 ** 6) for _ in range(n)],
                    [rng.randint(-10 ** 6, 10 ** 6) for _ in range(n + 1)]))
        return out


    def obst_recursion(record):
        h = harness_of(OB)
        mod = load_module(resolve_in_repo(PAIRS / OB, "implementations/recursion.py"))
        fn = mod.obst_recursive
        cost_code = next(c for c in fn.__code__.co_consts if hasattr(c, "co_name") and c.co_name == "cost")
        mc, ma = [], []
        for n in range(0, 10):
            for fam, p, q in obst_inputs(h, n, 0):
                inst = wrap_pq(h, p, q)
                h.reset_counters()
                calls, _ = run_profiled(lambda: fn(inst), call_code=cost_code)
                cmp_, add = h.counters()
                want_c = (3 ** (n - 1) - 1) // 2 if n >= 1 else 0
                if calls != 3 ** n or cmp_ != want_c:
                    mc.append(((n, fam), (calls, cmp_), (3 ** n, want_c)))
                if n >= 2 and 2 * add != 35 * 3 ** (n - 2) - 3:
                    ma.append(((n, fam), add, (35 * 3 ** (n - 2) - 3) / 2))
                if n == 1 and add != 4:
                    ma.append(((n, fam), add, 4))
        record("OBST recursion: 3^n calls, (3^(n-1)-1)/2 comparisons (n>=1, 0 at n=0) on every family and signed values",
               "n = 0..9, the ten V1 families + 2 signed kinds, 1 instance each", mc)
        record("OBST recursion additions (35*3^(n-2)-3)/2 (n>=2; 4 at n=1)",
               "same runs (n = 1..9)", ma)


    def obst_cubic(record):
        h = harness_of(OB)
        fn = impl_of(OB, "implementations/cubic_dp.py:obst_cubic")
        m = []
        for n in range(0, 31):
            for fam, p, q in obst_inputs(h, n, 0):
                inst = wrap_pq(h, p, q)
                h.reset_counters()
                cand = line_hits(fn, "cand = c[i][k - 1] + c[k][j]", lambda: fn(inst))
                cmp_, add = h.counters()
                want = ((n + 1) * n * (n - 1) // 6, n * (n + 1) * (n + 2) // 6 + 3 * n * (n + 1) // 2 - n,
                        n * (n + 1) * (n + 2) // 6)
                if (cmp_, add, cand) != want:
                    m.append(((n, fam), (cmp_, add, cand), want))
        record("OBST cubic DP: comparisons (n+1)n(n-1)/6, additions n(n+1)(n+2)/6+3n(n+1)/2-n, "
               "candidate roots n(n+1)(n+2)/6", "n = 0..30, the ten V1 families + 2 signed kinds", m)


    def knuth_tables(h, kn_mod, inst):
        fn = kn_mod.obst_knuth
        h.reset_counters()
        _, snap = run_profiled(lambda: fn(inst), return_code=fn.__code__, names=("r", "c", "w"))
        cmp_, add = h.counters()
        return cmp_, add, snap["r"], snap["c"], snap["w"]


    def obst_knuth_every_input(record):
        h = harness_of(OB)
        kn_mod = load_module(resolve_in_repo(PAIRS / OB, "implementations/knuth.py"))
        fn = kn_mod.obst_knuth
        m_prop, m_id, m_bound, m_add, m_len = [], [], [], [], []
        worst = {}
        for n in range(0, 41):
            for seed in range(3):
                for fam, p, q in obst_inputs(h, n, seed):
                    inst = wrap_pq(h, p, q)
                    cmp_, add, r, c, w = knuth_tables(h, kn_mod, inst)
                    # the property of the implementation's own root table used by the bound
                    ok = all(r[i][i + 1] == i + 1 for i in range(n))
                    for L in range(2, n + 1):
                        for i in range(n - L + 1):
                            j = i + L
                            ok = ok and r[i][j - 1] <= r[i][j] <= r[i + 1][j] and i + 1 <= r[i][j] <= j
                    if not ok:
                        m_prop.append(((n, fam, seed), "root table", "r[i][j-1] <= r[i][j] <= r[i+1][j], i < r <= j"))
                    tele = sum(r[n - L + 1][n] - r[0][L - 1] for L in range(2, n + 1))
                    if cmp_ != tele:
                        m_id.append(((n, fam, seed), cmp_, tele))
                    if n >= 1 and cmp_ > (n - 1) ** 2:
                        m_bound.append(((n, fam, seed), cmp_, (n - 1) ** 2))
                    if add != cmp_ + 2 * n * n:
                        m_add.append(((n, fam, seed), add, cmp_ + 2 * n * n))
                    if fam != "heavy_ends" and n == 40:
                        worst[fam] = max(worst.get(fam, 0), cmp_)
                    if n <= 25 and seed == 0:
                        per_len = line_hits(fn, "cand = c[i][k - 1] + c[k][j]", lambda: fn(wrap_pq(h, p, q)), key="length")
                        for L in range(2, n + 1):
                            want = (n - L + 1) + r[n - L + 1][n] - r[0][L - 1]
                            if per_len.get(L, 0) != want or want > 2 * n - L:
                                m_len.append(((n, fam, L), per_len.get(L, 0), f"{want} (<= {2 * n - L})"))
        sizes = "n = 0..40, 3 seeds, the ten V1 families + 2 signed kinds (1476 runs)"
        record("Knuth root table: r[i][i+1] = i+1, i < r[i][j] <= j, r[i][j-1] <= r[i][j] <= r[i+1][j] (implementation's table)",
               sizes, m_prop)
        record("Knuth comparisons = sum_{L=2..n} (r[n-L+1][n] - r[0][L-1]) with the implementation's own r", sizes, m_id)
        record("Knuth comparisons <= (n-1)^2 on every input (n >= 1)", sizes + f"; max at n=40 over the other kinds: "
               f"{max(worst.values())} (bound {39 ** 2})", m_bound)
        record("Knuth additions = comparisons + 2n^2", sizes, m_add)
        record("Knuth candidates of length L: (n-L+1) + r[n-L+1][n] - r[0][L-1] <= 2n - L",
               "n = 0..25, seed 0, the ten V1 families + 2 signed kinds, every L = 2..n", m_len)


    def full_minimisers(p, q):
        """Independent cubic DP on plain ints: optimal values and the SET of optimal roots of every interval."""
        n = len(p)
        c = [[0] * (n + 1) for _ in range(n + 1)]
        roots = {}
        for L in range(1, n + 1):
            for i in range(n - L + 1):
                j = i + L
                wij = sum(q[i:j + 1]) + sum(p[i:j])
                vals = {k: c[i][k - 1] + c[k][j] for k in range(i + 1, j + 1)}
                best = min(vals.values())
                roots[(i, j)] = {k for k, v in vals.items() if v == best}
                c[i][j] = wij + best
        return c, roots


    def obst_heavy_ends(record):
        h = harness_of(OB)
        kn_mod = load_module(resolve_in_repo(PAIRS / OB, "implementations/knuth.py"))
        m_cnt, m_root, m_uniq, m_lemma = [], [], [], []
        for n in range(0, 41):
            for seed in range(5):
                pp, qq = h._heavy_ends(n, random.Random(f"bst-extra|heavy|{n}|{seed}"), int)
                inst = wrap_pq(h, pp, qq)
                cmp_, add, r, c, w = knuth_tables(h, kn_mod, inst)
                if n >= 1 and cmp_ != (n - 1) ** 2:
                    m_cnt.append(((n, seed), cmp_, (n - 1) ** 2))
                if n == 0 and cmp_ != 0:
                    m_cnt.append(((n, seed), cmp_, 0))
                bad = [m for m in range(1, n) if r[0][m] != 1 or r[m][n] != n]
                if bad:
                    m_root.append(((n, seed), bad[:3], "r[0][m] = 1, r[m][n] = n"))
                # implementation's own values: w(i, j) <= c[i][j] <= (j - i) w(i, j)
                for i in range(n + 1):
                    for j in range(i + 1, n + 1):
                        if not (V(w[i][j]) <= V(c[i][j]) <= (j - i) * V(w[i][j])):
                            m_lemma.append(((n, seed, i, j), V(c[i][j]), "w <= c <= (j-i) w"))
                # uniqueness of the optimal roots (independent DP, all minimisers)
                if n >= 1:
                    _, roots = full_minimisers(pp, qq)
                    badu = [m for m in range(1, n) if roots[(0, m)] != {1} or roots[(m, n)] != {n}]
                    if badu:
                        m_uniq.append(((n, seed), badu[:3], "unique roots 1 and n"))
        sizes = "n = 0..40, 5 seeds per n (heavy-ends family, harness _heavy_ends)"
        record("heavy ends: Knuth comparisons (n-1)^2 (n >= 1; 0 at n = 0)", sizes, m_cnt)
        record("heavy ends: implementation picks r[0][m] = 1 and r[m][n] = n (1 <= m <= n-1)", sizes, m_root)
        record("heavy ends: w(i,j) <= c[i][j] <= (j-i) w(i,j) for the implementation's c", sizes, m_lemma)
        record("heavy ends: root 1 (n) is the unique optimal root of every (0, m) ((m, n)), 1 <= m <= n-1", sizes, m_uniq)


    # ------------------------------------------------------------------------------------------------------------------
    # Max-cost BST / interval DP with inclusion-monotone weights
    # ------------------------------------------------------------------------------------------------------------------

    def mc_inputs(h, n, seed):
        """Inputs outside the 32 families: arbitrary values, both senses, and the families with the sense flipped."""
        rng = random.Random(f"bst-extra|mc|{n}|{seed}")
        out = []
        for sense in ("max", "min"):
            w = [[None] * (n + 1) for _ in range(n + 1)]
            for i in range(n + 1):
                for j in range(i + 1, n + 1):
                    w[i][j] = rng.randint(-50, 50)
            out.append((f"iid-{sense}", (sense, tuple(tuple(row) for row in w))))
        out.append(("bst-signed", (tuple(rng.randint(-20, 20) for _ in range(n)),
                                   tuple(rng.randint(-20, 20) for _ in range(n + 1)))))
        g = h.instance_of("g_submax", n, random.Random(f"bst-extra|mc-g|{n}|{seed}"))
        out.append(("monotone-under-min", ("min", g[1])))
        a = h.instance_of("a_neg_submax", n, random.Random(f"bst-extra|mc-a|{n}|{seed}"))
        out.append(("anti-monotone-under-max", ("max", a[1])))
        return out


    def mc_closed(alg, n, bst):
        extra = n * (n + 1) if bst else 0
        if alg == "rec":
            cmp_ = (3 ** (n - 1) - 1) // 2 if n >= 1 else 0
            add = (11 * 3 ** (n - 2) - 1) // 2 if n >= 2 else n
            return cmp_, add + extra
        if alg == "cubic":
            return (n + 1) * n * (n - 1) // 6, n * (n + 1) * (n + 2) // 6 - n + n * (n + 1) // 2 + extra
        return n * (n - 1) // 2, 3 * n * (n - 1) // 2 + extra


    def mc_every_input(record):
        h = harness_of(MC)
        rec_mod = load_module(resolve_in_repo(PAIRS / MC, "implementations/recursion.py"))
        fns = {"rec": rec_mod.maxbst_recursive,
               "cubic": impl_of(MC, "implementations/cubic_dp.py:maxbst_cubic"),
               "end": impl_of(MC, "implementations/endpoint_dp.py:maxbst_endpoint")}
        cost_code = next(c for c in rec_mod.maxbst_recursive.__code__.co_consts
                         if hasattr(c, "co_name") and c.co_name == "cost")
        plan = {"rec": range(0, 10), "cubic": range(0, 31), "end": range(0, 61)}
        m, mcalls = [], []
        for alg, ns in plan.items():
            for n in ns:
                for seed in range(2):
                    for kind, raw in mc_inputs(h, n, seed):
                        bst = not h.is_table_form(raw)
                        inst = h.wrap_counting(raw)
                        h.reset_counters()
                        if alg == "rec":
                            calls, _ = run_profiled(lambda: fns[alg](inst), call_code=cost_code)
                            if calls != 3 ** n:
                                mcalls.append(((n, kind, seed), calls, 3 ** n))
                        else:
                            fns[alg](inst)
                        got = h.counters()
                        if got != mc_closed(alg, n, bst):
                            m.append(((alg, n, kind, seed), got, mc_closed(alg, n, bst)))
        sizes = ("recursion n = 0..9, cubic n = 0..30, endpoint n = 0..60; 2 seeds; iid tables in [-50, 50] under max and "
                 "min, signed BST frequencies in [-20, 20], monotone tables under min, anti-monotone tables under max")
        record("max-cost: comparisons and additions (table form; BST form + n(n+1)) on inputs outside the precondition",
               sizes, m)
        record("max-cost recursion: 3^n calls on inputs outside the precondition", "same inputs, n = 0..9", mcalls)


    def mc_candidates_and_split(record):
        h = harness_of(MC)
        cub_mod = load_module(resolve_in_repo(PAIRS / MC, "implementations/cubic_dp.py"))
        end_mod = load_module(resolve_in_repo(PAIRS / MC, "implementations/endpoint_dp.py"))
        rec_mod = load_module(resolve_in_repo(PAIRS / MC, "implementations/recursion.py"))
        m_cub, m_end, m_split = [], [], []
        marker = "cand = c[i][k - 1] + c[k][j]"
        for n in range(0, 17):
            for fam in h.ALL_FAMILIES:
                raw = h.instance_of(fam, n, random.Random(f"bst-extra|cand|{fam}|{n}"))
                inst = h.wrap_counting(raw)
                got = line_hits(cub_mod.maxbst_cubic, marker, lambda: cub_mod.maxbst_cubic(inst))
                if got != n * (n + 1) * (n + 2) // 6:
                    m_cub.append(((n, fam), got, n * (n + 1) * (n + 2) // 6))
                per_len = line_hits(end_mod.maxbst_endpoint, marker, lambda: end_mod.maxbst_endpoint(inst), key="length")
                want = {L: 2 * (n - L + 1) for L in range(2, n + 1)}
                if per_len != want:
                    m_end.append(((n, fam), per_len, want))
        # additions made inside _interval_weights (tabulating w) vs in the DP, per implementation and form
        saved = h.CountingInt.__add__
        tally = {}

        def counted_add(self, other):
            name = sys._getframe(1).f_code.co_name
            tally[name] = tally.get(name, 0) + 1
            return saved(self, other)
        h.CountingInt.__add__ = counted_add
        h.CountingInt.__radd__ = counted_add
        try:
            for n in range(0, 21):
                for fam in h.ALL_FAMILIES:
                    raw = h.instance_of(fam, n, random.Random(f"bst-extra|split|{fam}|{n}"))
                    bst = not h.is_table_form(raw)
                    for alg, fn in (("cubic", cub_mod.maxbst_cubic), ("end", end_mod.maxbst_endpoint),
                                    ("rec", rec_mod.maxbst_recursive)):
                        if alg == "rec" and n > 8:
                            continue
                        inst = h.wrap_counting(raw)
                        tally.clear()
                        h.reset_counters()
                        fn(inst)
                        tab = tally.get("_interval_weights", 0)
                        dp = sum(v for k, v in tally.items() if k != "_interval_weights")
                        want_tab = n * (n + 1) if bst else 0
                        want_dp = mc_closed(alg, n, False)[1]
                        if (tab, dp) != (want_tab, want_dp) or h._additions != tab + dp:
                            m_split.append(((alg, n, fam), (tab, dp), (want_tab, want_dp)))
        finally:
            h.CountingInt.__add__ = saved
            h.CountingInt.__radd__ = saved
        record("max-cost cubic DP candidate roots n(n+1)(n+2)/6 (uncounted)", "n = 0..16, all 32 families", m_cub)
        record("max-cost endpoint DP: exactly 2 candidates per interval of length L >= 2 (uncounted)",
               "n = 0..16, all 32 families, every L", m_end)
        record("max-cost additions split: _interval_weights n(n+1) (BST form) / 0 (table form), DP part = table-form "
               "closed form", "n = 0..20 (recursion 0..8), all 32 families", m_split)


    def run(record):
        obst_recursion(record)
        obst_cubic(record)
        obst_knuth_every_input(record)
        obst_heavy_ends(record)
        mc_every_input(record)
        mc_candidates_and_split(record)
    return run


# --------------------------------------------------------------------------------------------------------------
# group query: query
# --------------------------------------------------------------------------------------------------------------

def _make_query():
    import inspect
    import itertools
    import math
    import sys
    from decimal import Decimal, getcontext


    import lib.qsearch as qsearch  # noqa: E402  (extra_common has put the worktree first on sys.path)
    import lib.qsim as qsim  # noqa: E402


    # ---------------------------------------------------------------------------------------------------------------
    # helpers
    # ---------------------------------------------------------------------------------------------------------------

    def line_no(func, needle, nxt=None):
        """Line number of the unique source line of func whose stripped text is `needle` (and, if given, whose next
        line's stripped text is `nxt`)."""
        src, start = inspect.getsourcelines(func)
        hits = [start + i for i, s in enumerate(src)
                if s.strip() == needle and (nxt is None or (i + 1 < len(src) and src[i + 1].strip() == nxt))]
        assert len(hits) == 1, (needle, hits)
        return hits[0]


    def traced(code, marks, call, snap=lambda: None):
        """Run call() with a line tracer on the frames of `code`; return (result, events) where events is the list of
        (label, snap()) recorded each time a line in `marks` (lineno -> label) is about to run."""
        events = []

        def local(frame, event, arg):
            if event == "line":
                lab = marks.get(frame.f_lineno)
                if lab is not None:
                    events.append((lab, snap()))
            return local

        def tracer(frame, event, arg):
            return local if frame.f_code is code else None

        sys.settrace(tracer)
        try:
            out = call()
        finally:
            sys.settrace(None)
        return out, events


    class Counted:
        """Temporarily replace obj.name by a pass-through wrapper that counts calls."""

        def __init__(self, obj, name):
            self.obj, self.name, self.calls = obj, name, 0

        def __enter__(self):
            self.orig = getattr(self.obj, self.name)
            orig = self.orig

            def wrapper(*a, **kw):
                self.calls += 1
                return orig(*a, **kw)
            setattr(self.obj, self.name, wrapper)
            return self

        def __exit__(self, *exc):
            setattr(self.obj, self.name, self.orig)
            return False


    def decimal_pi():
        """pi to about 70 digits by Machin's formula (exact Decimal arithmetic at precision 80)."""
        getcontext().prec = 80
        eps = Decimal(10) ** -78

        def arctan_inv(x):
            x = Decimal(x)
            power = 1 / x
            total, sign, i = power, -1, 1
            while True:
                power /= x * x
                term = power / (2 * i + 1)
                if term < eps:
                    return total
                total += sign * term
                sign, i = -sign, i + 1
        pi = 4 * (4 * arctan_inv(5) - arctan_inv(239))
        assert abs(pi - Decimal(math.pi)) < Decimal("1e-15")
        return pi


    def decimal_sin(x):
        getcontext().prec = 80
        eps = Decimal(10) ** -78
        term, total, i = x, x, 1
        while abs(term) > eps:
            term = -term * x * x / ((2 * i) * (2 * i + 1))
            total += term
            i += 1
        return total


    # ---------------------------------------------------------------------------------------------------------------
    # Deutsch-Jozsa
    # ---------------------------------------------------------------------------------------------------------------

    def deutsch_jozsa(record):
        E = "deutsch-jozsa-classical-vs-quantum"
        h = harness_of(E)
        det = impl_of(E, "implementations/classical.py:dj_classical")
        rnd = impl_of(E, "implementations/randomized.py:dj_randomized")
        qu = impl_of(E, "implementations/quantum.py:dj_quantum")

        def worst4(n):
            N = 1 << n
            return ({tuple([c] * N) for c in (0, 1)}
                    | {tuple(c ^ (x >> (n - 1)) for x in range(N)) for c in (0, 1)})

        def expected(n, t):
            N = 1 << n
            if len(set(t)) == 1:
                return N // 2 + 1
            return 1 + next(x for x in range(1, N) if t[x] != t[0])  # 1 + G

        mism = []
        count = 0
        for n in range(1, 5):  # every promise input
            N = 1 << n
            W = worst4(n)
            tables = [tuple([c] * N) for c in (0, 1)] + [
                tuple(1 if x in S else 0 for x in range(N)) for S in map(set, itertools.combinations(range(N), N // 2))]
            for t in tables:
                count += 1
                q = det((n, t))[1]
                e = expected(n, t)
                if q != e or q > N // 2 + 1 or (q == N // 2 + 1) != (t in W):
                    mism.append((f"n={n} t={t}", q, e))
        rng = random.Random("dj-deterministic-every-input")
        for n in range(5, 15):
            N = 1 << n
            W = worst4(n)
            tables = list(W)
            for i in range(60):
                if i < 20:
                    tables.append(h.generate(n, rng)[1])
                else:  # balanced, equal to c on a prefix of random length p (1 <= p <= N/2), random afterwards
                    c, p = rng.randrange(2), rng.randint(1, N // 2)
                    rest = [c] * (N // 2 - p) + [1 - c] * (N // 2)
                    rng.shuffle(rest)
                    tables.append(tuple([c] * p + rest))
            for t in tables:
                count += 1
                q = det((n, t))[1]
                e = expected(n, t)
                if q != e or q > N // 2 + 1 or (q == N // 2 + 1) != (t in W):
                    mism.append((f"n={n}", q, e))
        for n in (15, 16):
            for t in worst4(n):
                count += 1
                q = det((n, t))[1]
                if q != (1 << (n - 1)) + 1:
                    mism.append((f"n={n}", q, (1 << (n - 1)) + 1))
        record("DJ deterministic: 1 + G (balanced), 2^(n-1)+1 (constant); maximum exactly on the four functions",
               f"every promise input for n = 1..4; for n = 5..14 the four functions + 60 seeded promise inputs per n "
               f"(20 from generate, 40 balanced with an equal prefix of random length); the four functions at n = 15, 16 "
               f"({count} inputs)", mism)

        mism = []
        rng = random.Random("dj-randomized-quantum-every-input")
        for n in range(0, 15):
            for i in range(20):
                t = tuple([i % 2] * (1 << n)) if n == 0 else h.generate(n, rng)[1]
                random.seed(f"dj-randomized|{n}|{i}")
                q = rnd((n, t))[1]
                if q != 20:
                    mism.append((f"n={n} i={i}", q, 20))
        record("DJ randomized exactly 20 on every input", "n = 0..14, 20 seeded inputs per n (n >= 1 from generate)", mism)

        mism = []
        for n in range(0, 11):
            for i in range(10):
                t = tuple([i % 2] * (1 << n)) if n == 0 else h.generate(n, rng)[1]
                random.seed(f"dj-quantum|{n}|{i}")
                q = qu((n, t))[1]
                if q != 1:
                    mism.append((f"n={n} i={i}", q, 1))
        record("DJ quantum exactly 1 on every input", "n = 0..10, 10 seeded inputs per n (n >= 1 from generate)", mism)


    # ---------------------------------------------------------------------------------------------------------------
    # Bernstein-Vazirani
    # ---------------------------------------------------------------------------------------------------------------

    def bernstein_vazirani(record):
        E = "bernstein-vazirani-classical-vs-quantum"
        cl = impl_of(E, "implementations/classical.py:bv_classical")
        qu = impl_of(E, "implementations/quantum.py:bv_quantum")

        def table(n, s):
            return tuple(bin(s & x).count("1") & 1 for x in range(1 << n))

        mc, mq = [], []
        rng = random.Random("bv-every-s")
        for n in range(0, 17):
            ss = range(1 << n) if n <= 8 else [rng.getrandbits(n) for _ in range(10)]
            for s in ss:
                t = table(n, s)
                q = cl((n, t))[1]
                if q != n:
                    mc.append((f"n={n} s={s}", q, n))
                if n <= 8 or (n <= 10 and s in ss[:5]):
                    random.seed(f"bv-quantum|{n}|{s}")
                    q = qu((n, t))[1]
                    if q != 1:
                        mq.append((f"n={n} s={s}", q, 1))
        record("BV classical exactly n on every s", "every s for n = 0..8; 10 seeded s per n for n = 9..16", mc)
        record("BV quantum exactly 1 on every s", "every s for n = 0..8; 5 seeded s per n for n = 9, 10", mq)


    # ---------------------------------------------------------------------------------------------------------------
    # Minimum finding
    # ---------------------------------------------------------------------------------------------------------------

    def minimum_finding(record):
        E = "minimum-finding-classical-vs-quantum"
        h = harness_of(E)
        scan = impl_of(E, "implementations/classical.py:minimum_scan")
        l_cmp = line_no(scan, "if v < best_value:")
        mism = []
        rng = random.Random("minimum-scan")
        for n in range(0, 13):
            N = 1 << n
            for i in range(5):
                inst = h.generate(n, rng)
                out, ev = traced(scan.__code__, {l_cmp: "cmp"}, lambda: scan(inst))
                got = (out[1], len(ev))
                if got != (N, N - 1):
                    mism.append((f"n={n} i={i}", got, (N, N - 1)))
        record("minimum scan: N queries, N-1 comparisons",
               "n = 0..12, 5 seeded permutations per n", mism)

        dh = load_module(resolve_in_repo(PAIRS / E, "implementations/durr_hoyer.py"))
        mism = []
        runs = 0
        for n in list(range(1, 9)) + [10, 12]:
            for i in range(12 if n <= 8 else 3):
                r = random.Random(f"durr-hoyer|{n}|{i}")
                inst = h.generate(n, r)
                with Counted(qsearch, "grover_iteration") as g:
                    out = dh.durr_hoyer_run(inst, r)
                runs += 1
                want = 2 * g.calls + out["measurements"] + 1
                if out["queries"] != want:
                    mism.append((f"n={n} i={i}", out["queries"], want))
        record("Durr-Hoyer: queries = 2 x iterations + candidates + 1",
               f"n = 1..8 (12 seeded runs per n) and n = 10, 12 (3 per n), with the paper's time-out ({runs} runs)", mism)


    # ---------------------------------------------------------------------------------------------------------------
    # NAND tree
    # ---------------------------------------------------------------------------------------------------------------

    def nand_tree(record):
        E = "nand-tree-evaluation-deterministic-vs-randomized"
        h = harness_of(E)
        lf = impl_of(E, "implementations/left_first.py:nand_tree_left_first")

        def reads(bits):
            leaves = h.CountingLeaves(bits)
            h._reads = 0
            lf(leaves)
            return h._reads

        mism = []
        count = 0
        for hh in range(0, 5):
            N = 1 << hh
            full = {tuple(h.reluctant(hh, r, lambda _h: 1)) for r in (0, 1)}
            for bits in itertools.product((0, 1), repeat=N):
                count += 1
                c = reads(bits)
                if c > N or (c == N) != (bits in full):
                    mism.append((f"h={hh} {bits}", c, N))
        record("NAND left-first: <= 2^h, = 2^h exactly on the right-zero reluctant inputs",
               f"every input for h = 0..4 ({count} inputs)", mism)
        mism = []
        for hh in range(0, 17):
            for r in (0, 1):
                c = reads(h.reluctant(hh, r, lambda _h: 1))
                if c != 1 << hh:
                    mism.append((f"h={hh} root={r}", c, 1 << hh))
        record("NAND left-first: 2^h on the right-zero reluctant inputs (root 0 and root 1)",
               "h = 0..16", mism)


    # ---------------------------------------------------------------------------------------------------------------
    # Bipartite matching
    # ---------------------------------------------------------------------------------------------------------------

    BM = "bipartite-matching-kuhn-vs-hopcroft-karp"


    def kuhn_formula(k):
        return (7 * k ** 6 + 9 * k ** 4 + 11 * k ** 2 - 3 * k) // 6


    def hk_formula(k):
        return (24 * k ** 5 + 9 * k ** 4 + 4 * k ** 3 + 24 * k ** 2 - 25 * k + 12) // 6


    def bipartite(record):
        h = harness_of(BM)
        kuhn = load_module(resolve_in_repo(PAIRS / BM, "implementations/kuhn.py")).matching_kuhn
        hk = load_module(resolve_in_repo(PAIRS / BM, "implementations/hopcroft_karp.py")).matching_hopcroft_karp

        def scaling(k):
            n = 4 * k * k + k
            return h.generate_scaling(n, random.Random(f"{BM}|v2|{n}"))

        # totals on G_k (the validator's seeding; G_k does not depend on the seed)
        mk = []
        for k in range(1, 13):
            inst = scaling(k)
            random.seed(f"{BM}|v2|{4 * k * k + k}|0|Kuhn")
            kuhn(inst)
            if h._scans != kuhn_formula(k):
                mk.append((f"k={k}", h._scans, kuhn_formula(k)))
            assert (7 * k ** 6 + 9 * k ** 4 + 11 * k ** 2 - 3 * k) % 6 == 0
        record("Kuhn on G_k: (7k^6+9k^4+11k^2-3k)/6", "k = 1..12", mk)
        mh = []
        for k in range(1, 17):
            inst = scaling(k)
            hk(inst)
            if h._scans != hk_formula(k):
                mh.append((f"k={k}", h._scans, hk_formula(k)))
            assert (24 * k ** 5 + 9 * k ** 4 + 4 * k ** 3 + 24 * k ** 2 - 25 * k + 12) % 6 == 0
        record("Hopcroft-Karp on G_k: (24k^5+9k^4+4k^3+24k^2-25k+12)/6", "k = 1..16", mh)

        # Kuhn per root on G_k
        l_root = line_no(kuhn, "seen = [False] * n_right")
        mism = []
        for k in range(1, 8):
            a = k * k
            inst = scaling(k)
            _, ev = traced(kuhn.__code__, {l_root: "root"}, lambda: kuhn(inst), lambda: h._scans)
            marks = [s for _, s in ev] + [h._scans]
            got = [marks[i + 1] - marks[i] for i in range(len(marks) - 1)]
            want = [(u + 1) * (u + 2) // 2 for u in range(a)] + [a * (a + 1)] * a
            for j in range(1, k + 1):
                want += [1] * (j - 1) + [2 * j - 1]
            if got != want:
                if len(got) != len(want):
                    mism.append((f"k={k} number of roots", len(got), len(want)))
                else:
                    bad = next(i for i in range(len(got)) if got[i] != want[i])
                    mism.append((f"k={k} root {bad}", got[bad], want[bad]))
        record("Kuhn on G_k: scans per search",
               "k = 1..7, every root", mism)

        # Hopcroft-Karp per phase on G_k
        l_phase = line_no(hk, "dist = [INF] * n_left")
        l_bfs_end = line_no(hk, "if target == INF:", nxt="return size")
        mism = []
        for k in range(1, 10):
            a, Eg = k * k, 2 * k ** 4 + k * k
            inst = scaling(k)
            _, ev = traced(hk.__code__, {l_phase: "P", l_bfs_end: "B"}, lambda: hk(inst), lambda: h._scans)
            labels = [lab for lab, _ in ev]
            if labels != ["P", "B"] * (k + 1):
                mism.append((f"k={k} phase structure", labels.count("P"), k + 1))
                continue
            s = [v for _, v in ev] + [h._scans]
            got = []
            for p in range(k + 1):
                bfs = s[2 * p + 1] - s[2 * p]
                dfs = s[2 * p + 2] - s[2 * p + 1]
                got.append((bfs, dfs))
            want = [(Eg, a * (a + 1) // 2 + a * a + k * (k + 1) // 2)]
            for t in range(2, k + 1):
                want.append((2 * a * a + (k - t + 1) * (2 * t - 1), 2 * a * a + (2 * t - 1) + (k - t) * (2 * t + 1)))
            want.append((2 * a * a, 0))
            if got != want:
                bad = next(i for i in range(len(got)) if got[i] != want[i])
                mism.append((f"k={k} phase {bad + 1} (BFS, DFS)", got[bad], want[bad]))
        record("Hopcroft-Karp on G_k: BFS and DFS scans per phase", "k = 1..9", mism)

        # bounds on other inputs
        mk, mh = [], []
        graphs = 0
        for n in range(0, 61):
            for seed in range(4):
                nl, nr, adj = h.generate(n, random.Random(f"bm-bounds|{n}|{seed}"))
                E = sum(len(x) for x in adj)
                inst = (nl, nr, tuple(h.CountingNeighbours(x) for x in adj))
                graphs += 1
                h._scans = 0
                _, ev = traced(kuhn.__code__, {l_root: "root"}, lambda: kuhn(inst), lambda: h._scans)
                marks = [v for _, v in ev] + [h._scans]
                per = [marks[i + 1] - marks[i] for i in range(len(marks) - 1)]
                if h._scans > nl * E or (per and max(per) > E):
                    mk.append((f"n={n} seed={seed}", (h._scans, max(per) if per else 0), (nl * E, E)))
                h._scans = 0
                _, ev = traced(hk.__code__, {l_phase: "P", l_bfs_end: "B"}, lambda: hk(inst), lambda: h._scans)
                s = [v for _, v in ev] + [h._scans]
                parts = [s[i + 1] - s[i] for i in range(len(s) - 1)]  # BFS, DFS, BFS, DFS, ..., final BFS
                if parts and max(parts) > E:
                    mh.append((f"n={n} seed={seed}", max(parts), E))
        record("Kuhn: <= E per search, <= n_left E in total",
               f"harness.generate graphs, n = 0..60, 4 seeds per n ({graphs} graphs)", mk)
        record("Hopcroft-Karp: <= E per BFS and per DFS pass",
               f"the same {graphs} graphs", mh)


    # ---------------------------------------------------------------------------------------------------------------
    # Grover
    # ---------------------------------------------------------------------------------------------------------------

    def grover(record):
        E = "grover-search-classical-vs-quantum"
        h = harness_of(E)
        gr = impl_of(E, "implementations/grover.py:search_grover")
        l_att = line_no(gr, "state = State(n)")
        mism = []
        rng = random.Random("grover-attempts")
        attempts = {}
        for n in range(0, 13):
            k = math.floor(math.pi / 4 * math.sqrt(1 << n))
            for i in range(12):
                inst = h.generate(n, rng)
                random.seed(f"grover|{n}|{i}")
                out, ev = traced(gr.__code__, {l_att: "attempt"}, lambda: gr(inst))
                A = len(ev)
                attempts[A] = attempts.get(A, 0) + 1
                if out[1] != A * (k + 1):
                    mism.append((f"n={n} i={i} A={A}", out[1], A * (k + 1)))
        record("Grover: queries = A(k+1)",
               "n = 0..12, 12 seeded instances per n (attempts seen: "
               + ", ".join(f"{a}: {c} runs" for a, c in sorted(attempts.items())) + ")", mism)

        # the code's k equals floor(pi sqrt(N) / 4), checked with exact integers and pi to 50 decimals (+-1 unit)
        pi = decimal_pi()
        D = 50
        P = int(pi * Decimal(10) ** D)
        lo, hi = P - 1, P + 1
        mism = []
        for n in range(0, 65):
            N = 1 << n
            k = math.floor(math.pi / 4 * math.sqrt(N))
            ok_low = 16 * k * k * 10 ** (2 * D) <= lo * lo * N          # 4k <= pi sqrt N
            ok_high = hi * hi * N < 16 * (k + 1) ** 2 * 10 ** (2 * D)   # pi sqrt N < 4(k + 1)
            if not (ok_low and ok_high):
                mism.append((f"n={n}", k, "floor(pi sqrt(N)/4)"))
        record("Grover: code's k = floor(pi sqrt(N)/4)",
               "n = 0..64 (exact integer comparison)", mism)


    # ---------------------------------------------------------------------------------------------------------------
    # Simon
    # ---------------------------------------------------------------------------------------------------------------

    def simon(record):
        E = "simon-classical-vs-quantum"
        h = harness_of(E)
        qu = impl_of(E, "implementations/quantum.py:simon_quantum")
        l_round = line_no(qu, "state = State(n)")
        mism = []
        rng = random.Random("simon-rounds")
        for n in range(1, 11):
            for i in range(12):
                inst = h.generate(n, rng)
                random.seed(f"simon|{n}|{i}")
                out, ev = traced(qu.__code__, {l_round: "round"}, lambda: qu(inst))
                if out[1] != len(ev):
                    mism.append((f"n={n} i={i}", out[1], len(ev)))
        record("Simon quantum: queries = rounds",
               "n = 1..10, 12 seeded instances per n", mism)


    # ---------------------------------------------------------------------------------------------------------------
    # Collision
    # ---------------------------------------------------------------------------------------------------------------

    def collision(record):
        E = "collision-problem-classical-vs-quantum"
        h = harness_of(E)
        cl = impl_of(E, "implementations/classical.py:collision_classical")
        mism = []
        rng = random.Random("collision-classical")
        worst = {}
        for n in range(1, 15):
            N = 1 << n
            for i in range(30):
                inst = h.generate(n, rng)
                random.seed(f"collision-classical|{n}|{i}")
                q = cl(inst)[1]
                worst[n] = max(worst.get(n, 0), q)
                if q > N // 2 + 1:
                    mism.append((f"n={n} i={i}", q, N // 2 + 1))
        record("collision classical: <= N/2+1", "n = 1..14, 30 seeded runs per n", mism)

        bht = load_module(resolve_in_repo(PAIRS / E, "implementations/bht.py"))
        mism = []
        runs = coll = 0
        for version in ("collision_bht", "collision_bht_exponential"):
            fn = getattr(bht, version)
            for n in list(range(1, 13)) + [15]:
                N = 1 << n
                k = max(1, round(2 ** (n / 3)))
                m = qsearch.known_count_iterations(N, k)
                for i in range(10 if n <= 12 else 3):
                    inst = h.generate(n, rng)
                    random.seed(f"bht|{version}|{n}|{i}")
                    state = random.getstate()
                    K = list(range(k)) if version == "collision_bht" else random.sample(range(N), k)
                    random.setstate(state)
                    has = len({inst[1][x] for x in K}) < k
                    with Counted(qsearch, "grover_iteration") as g, Counted(qsim.State, "measure_all") as c:
                        out = fn(inst)
                    runs += 1
                    coll += has
                    want = k + 2 * g.calls + c.calls
                    if out[1] != want or (has and out[1] != k):
                        mism.append((f"{version} n={n} i={i}", out[1], want))
                    if version == "collision_bht" and not has and g.calls != m * c.calls:
                        mism.append((f"{version} n={n} i={i} iterations", g.calls, m * c.calls))
        record("BHT: queries = k + 2 x iterations + candidates",
               f"n = 1..12 (10 seeded runs per n and version) and n = 15 (3 per version) ({runs} runs, {coll} with a collision inside K)", mism)

        mism = [(f"n={n}", bht.subset_size(n), 2 ** (n // 3)) for n in range(3, 61, 3)
                if bht.subset_size(n) != 2 ** (n // 3)]
        record("BHT: k = 2^(n/3) when 3 divides n", "n = 3, 6, ..., 60", mism)

        # m = known_count_iterations(N, k) equals floor(pi / (4 theta)), sin^2 theta = k / N
        pi = decimal_pi()
        mism = []
        for n in range(1, 41):
            N = 1 << n
            k = max(1, round(2 ** (n / 3)))
            m = qsearch.known_count_iterations(N, k)
            r = Decimal(k) / Decimal(N)
            if 2 * k == N:   # theta = pi/4 exactly, pi/(4 theta) = 1
                ok = m == 1
            else:
                upper = decimal_sin(pi / (4 * m)) ** 2          # need k/N < sin^2(pi/(4m))  (strict: k/N != 1/2)
                lower = decimal_sin(pi / (4 * (m + 1))) ** 2    # need sin^2(pi/(4(m+1))) < k/N
                ok = m >= 1 and r - lower > Decimal("1e-60") and upper - r > Decimal("1e-60")
            if not ok:
                mism.append((f"n={n} k={k}", m, "floor(pi/(4 theta))"))
        record("BHT: code's m = floor(pi/(4 theta))",
               "n = 1..40 (pi and sin to 70 digits; n = 1, 2 have k = N/2, theta = pi/4, m = 1)", mism)


    def run(record):
        deutsch_jozsa(record)
        bernstein_vazirani(record)
        minimum_finding(record)
        nand_tree(record)
        bipartite(record)
        grover(record)
        simon(record)
        collision(record)
    return run



GROUP_MAKERS = {
    "strings": [_make_model, _make_strings],
    "algebra": [_make_algebra],
    "subsets": [_make_subsets],
    "sat": [_make_sat],
    "graphs": [_make_graphs],
    "bst": [_make_bst],
    "query": [_make_query],
}


def main(argv):
    print(f"Python {sys.version.split()[0]}; below-normal priority: {set_below_normal_priority()}", flush=True)
    chosen = argv or list(GROUP_MAKERS)
    t0 = time.perf_counter()
    for name in chosen:
        t = time.perf_counter()
        record = make_record(name)
        for maker in GROUP_MAKERS[name]:
            maker()(record)
        print(f"--- group {name}: {time.perf_counter() - t:.1f} s", flush=True)
    bad = [r for r in RESULTS if r[2] != "OK"]
    print(f"\nSUMMARY: {len(RESULTS)} checks, {len(RESULTS) - len(bad)} OK, {len(bad)} with mismatches; "
          f"{time.perf_counter() - t0:.1f} s")
    for g, label, _ in bad:
        print(f"  MISMATCH: [{g}] {label}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
