"""Mutant definitions for the 2026-10-06d pilot: MIRROR and OPSWAP (semiring / monoid substitution).

Every subject and oracle is an in-memory copy of a repository implementation (rewrite.load_copy), run either
unchanged on transformed inputs (mode "io"), unchanged on injected element types (mode "inject"), or after a
targeted AST rewrite (mode "ast" / "ast+inject"). Nothing under pairs/ is modified.
"""
from __future__ import annotations

import functools
import math
from fractions import Fraction

from . import algebra as A
from . import oracles
from .engine import Mutant, simplify_matrix, simplify_pair, simplify_vector
from .rewrite import load_copy

P = "pairs/"
INF = math.inf

LIT = {  # literature keys (see mutations/literature.py)
    "strassen": "strassen1969", "fischer_meyer": "fischer-meyer1971", "munro": "munro1971", "yuval": "yuval1976",
    "warshall": "warshall1962", "floyd": "floyd1962", "lehmann": "lehmann1977", "pollack": "pollack1960",
    "vwy": "vassilevska-williams-yuster2007", "duan_pettie": "duan-pettie2009", "dijkstra": "dijkstra1959",
    "camerini": "camerini1978", "edmonds": "edmonds1971", "karp": "karp1972", "valiant": "valiant1979",
    "kuhn": "kuhn1955", "pollard": "pollard1971", "cooley": "cooley-tukey1965", "bellman_tsp": "bellman1962",
    "held_karp": "held-karp1962", "knuth_obst": "knuth1971", "yao": "yao1980", "bender": "bender-farach-colton2000",
    "mohri": "mohri2002", "williams": "williams2018", "shamos": "shamos-hoey1975", "gondran": "gondran-minoux2008",
}

STRUCT = A.semirings()
MONO = A.monoids()
MAG = A.mul_magmas()


# --------------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------------

def _m(rel, transforms=None, extra=None, func=None):
    mod = load_copy(rel, transforms, extra)
    return getattr(mod, func), mod.__mutation__


def canon_ring(S):
    def c(x):
        if hasattr(x, "v") and type(x).__name__ == "RE":
            return S.canon(x.v)
        if isinstance(x, bool) or not isinstance(x, int):
            if isinstance(x, (list, tuple)):
                return [c(y) for y in x]
            return S.canon(x) if not isinstance(x, (list, tuple)) else x
        return S.canon(S.lift(x))
    return c


def canon_trop(S):
    def c(x):
        if hasattr(x, "v") and type(x).__name__ == "TE":
            return x.v
        if x is None:
            return None
        if isinstance(x, (list, tuple)):
            return [c(y) for y in x]
        if isinstance(x, float) and math.isinf(x):
            return S.zero
        if isinstance(x, int) and not isinstance(x, bool) and x == 0:
            return S.one
        return x
    return c


def nested_wrap(x, f):
    if isinstance(x, tuple):
        return tuple(nested_wrap(y, f) for y in x)
    if isinstance(x, list):
        return [nested_wrap(y, f) for y in x]
    return f(x)


def ring_runner(fn, S, sub_fallback=None, counter=None):
    RE = A.make_ring_elem(S, counter, sub_fallback)
    can = canon_ring(S)

    def run(inst):
        return can(fn(nested_wrap(inst, RE)))
    return run


def trop_runner(fn, S, sense="min", counter=None, wrap_pred=None, out_fix=None):
    TE = A.make_tropical_elem(S, sense, counter)
    can = canon_trop(S)

    def wrap(v):
        if v is None:
            return None
        return TE(v)

    def run(inst):
        w = wrap_pred(inst, TE) if wrap_pred else nested_wrap(inst, wrap)
        A.CURRENT_TE[0] = TE
        out = can(fn(w))
        return out_fix(out) if out_fix else out
    return run


def struct_props_key(S):
    return S.name


def gen_matrix_pair(S):
    def g(n, rng):
        mat = lambda: tuple(tuple(S.sample(rng) for _ in range(n)) for _ in range(n))  # noqa: E731
        return mat(), mat()
    return g


def counting_cost(make_run, gen_scaling, n_values, measure, claimed, library=None, tol=0.03):
    def run(n):
        cnt = A.new_counter()
        f = make_run(cnt)
        f(gen_scaling(n))
        return dict(cnt)
    d = {"run": run, "n_values": n_values, "measure": measure, "claimed": claimed, "tolerance": tol}
    if library:
        d["library"] = library
    return d


import random as _random  # noqa: E402


def _seeded(tag, n):
    return _random.Random(f"2026-10-06d|scaling|{tag}|{n}")


# --------------------------------------------------------------------------------------------------
# OPSWAP 1: matrix multiplication, schoolbook vs Strassen
# --------------------------------------------------------------------------------------------------

MM = P + "matrix-multiplication-naive-vs-strassen/implementations/"


def opswap_matmul():
    out = []
    naive, prov_n = _m(MM + "naive.py", func="matmul_naive")
    strassen, prov_s = _m(MM + "strassen.py", func="matmul_strassen")
    strassen1, prov_s1 = _m(MM + "strassen.py", [("const", {"CUTOFF": 1})], func="matmul_strassen")
    names = ["Z", "Z7", "GF2", "MinPlus", "MaxPlus", "MaxMin", "Bool", "MinMax", "Viterbi", "MaxTimesZ"]
    for sname in names:
        S = STRUCT[sname]
        lit = [LIT["strassen"]]
        for subj, prov, tag, sizes in ((strassen1, prov_s1, "Strassen (copy, CUTOFF=1)", [1, 2, 3, 4, 5, 6, 8]),
                                       (strassen, prov_s, "Strassen (unchanged copy, CUTOFF=16)", [17, 24])):
            fallbacks = [None] if S.has_neg else [None, "add"]
            for fb in fallbacks:
                cost = None
                if S.has_neg and tag.startswith("Strassen (unchanged"):
                    cost = counting_cost(lambda cnt, S=S: ring_runner(strassen, S, counter=cnt),
                                         lambda n, S=S: gen_matrix_pair(S)(n, _seeded("mm" + S.name, n)),
                                         [32, 64, 128], "mul", "n**log2(7)")
                out.append(Mutant(
                    pair="matrix-multiplication-naive-vs-strassen", family="OPSWAP",
                    operator=f"semiring:{sname}" + ("" if fb is None else "+sub:=add"), mode="inject",
                    structure=sname, subject_name=tag, oracle_name="schoolbook (unchanged copy, injected)",
                    description=f"matrix product over {S.label}; Python +,*,- in an unchanged copy act as ⊕,⊗,"
                                + ("additive inverse" if fb is None else " ⊕ (signs dropped: sign-forgetting probe)"),
                    subject=ring_runner(subj, S, fb), oracle=ring_runner(naive, S),
                    gen=gen_matrix_pair(S), sizes=sizes, trials=6 if sizes[0] > 16 else 12,
                    simplify=simplify_pair(simplify_matrix(_pool(S), keep_diag=False),
                                           simplify_matrix(_pool(S), keep_diag=False)),
                    cost=cost, literature=lit, provenance={"subject": prov, "oracle": prov_n}))
    # mode io: ring embeddings that rescue the killed semirings
    out += _matmul_embeddings(naive, strassen, prov_n, prov_s)
    return out


def _pool(S):
    if S.finite_carrier:
        return list(S.finite_carrier)
    return [x for x in (S.zero, S.one, 0, 1, -1, 2) if x is not None]


def _matmul_embeddings(naive, strassen, prov_n, prov_s):
    out = []
    B = STRUCT["Bool"]

    def bool_subject(inst):
        X, Y = inst
        C = strassen((tuple(tuple(int(v) for v in r) for r in X), tuple(tuple(int(v) for v in r) for r in Y)))
        return [[c > 0 for c in row] for row in C]
    out.append(Mutant(
        pair="matrix-multiplication-naive-vs-strassen", family="OPSWAP", operator="semiring:Bool", mode="io",
        structure="Bool", subject_name="Strassen over Z on 0/1 inputs, then threshold > 0",
        oracle_name="schoolbook (unchanged copy, injected Bool)",
        description="Boolean matrix product by embedding {False,True} -> {0,1} ⊂ Z, integer Strassen, entry > 0",
        subject=bool_subject, oracle=ring_runner(naive, B), gen=gen_matrix_pair(B), sizes=[1, 4, 17, 24], trials=8,
        literature=[LIT["fischer_meyer"], LIT["munro"]], provenance={"subject": prov_s, "oracle": prov_n},
        cost=counting_cost(lambda cnt: _counting_int_strassen(strassen, cnt, bool_inputs=True),
                           lambda n: gen_matrix_pair(B)(n, _seeded("mmBool", n)), [32, 64, 128], "mul",
                           "n**log2(7)")))
    MP = STRUCT["MinPlus"]

    def yuval_subject(inst):
        X, Y = inst
        n = len(X)
        M = max([v for r in X + Y for v in r if v != INF] + [0])
        base = n + 1

        def enc(a):
            return 0 if a == INF else base ** (M - a)
        C = strassen((tuple(tuple(enc(v) for v in r) for r in X), tuple(tuple(enc(v) for v in r) for r in Y)))

        def dec(c):
            if c == 0:
                return INF
            d = 0
            while c >= base:
                c //= base
                d += 1
            return 2 * M - d
        return [[dec(c) for c in row] for row in C]
    out.append(Mutant(
        pair="matrix-multiplication-naive-vs-strassen", family="OPSWAP", operator="semiring:MinPlus", mode="io",
        structure="MinPlus", subject_name="Strassen over Z on base-(n+1) exponent encoding (Yuval)",
        oracle_name="schoolbook (unchanged copy, injected MinPlus)",
        description="(min,+) product of non-negative integer matrices: a -> (n+1)^(M-a), integer Strassen, "
                    "min = 2M - (index of the leading base-(n+1) digit). Entries have Theta(M log n) bits.",
        subject=yuval_subject, oracle=ring_runner(naive, MP), gen=gen_matrix_pair(MP), sizes=[1, 3, 17, 24],
        trials=8, literature=[LIT["yuval"]], provenance={"subject": prov_s, "oracle": prov_n},
        notes="Operation count is Strassen's, but each operation acts on integers of Theta(M log n) bits, where M is "
              "the largest weight: pseudo-polynomial in the weights."))
    MM_ = STRUCT["MaxMin"]

    def threshold_subject(inst):
        X, Y = inst
        n = len(X)
        vals = sorted({v for r in X + Y for v in r if v != -INF})
        C = [[-INF] * n for _ in range(n)]
        for t in vals:
            Xt = tuple(tuple(1 if v >= t else 0 for v in r) for r in X)
            Yt = tuple(tuple(1 if v >= t else 0 for v in r) for r in Y)
            Pt = strassen((Xt, Yt))
            for i in range(n):
                for j in range(n):
                    if Pt[i][j] > 0:
                        C[i][j] = t
        return C
    out.append(Mutant(
        pair="matrix-multiplication-naive-vs-strassen", family="OPSWAP", operator="semiring:MaxMin", mode="io",
        structure="MaxMin", subject_name="threshold decomposition + integer Strassen per distinct value",
        oracle_name="schoolbook (unchanged copy, injected MaxMin)",
        description="(max,min) product: for each distinct value t, Boolean product of [X >= t] and [Y >= t] by "
                    "integer Strassen; C[i][j] = largest t with a witness. Cost: (#distinct values) x Strassen.",
        subject=threshold_subject, oracle=ring_runner(naive, MM_), gen=gen_matrix_pair(MM_), sizes=[1, 3, 17],
        trials=6, literature=[LIT["vwy"], LIT["duan_pettie"]], provenance={"subject": prov_s, "oracle": prov_n},
        notes="Pseudo-polynomial: the number of Strassen calls equals the number of distinct values (<= 21 here)."))
    return out


def _counting_int_strassen(strassen, cnt, bool_inputs=False):
    RE = A.make_ring_elem(STRUCT["Z"], cnt)

    def run(inst):
        X, Y = inst
        f = (lambda v: RE(int(v))) if bool_inputs else RE
        return strassen((tuple(tuple(f(v) for v in r) for r in X), tuple(tuple(f(v) for v in r) for r in Y)))
    return run


# --------------------------------------------------------------------------------------------------
# OPSWAP 2: all-pairs paths, Floyd-Warshall and Bellman-Ford
# --------------------------------------------------------------------------------------------------

AP = P + "all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall/implementations/"


def gen_digraph(S, dag=False):
    def g(n, rng):
        density = rng.choice((0.3, 0.6, 1.0))
        return tuple(tuple(0 if i == j else (S.sample(rng) if ((not dag or i < j) and rng.random() < density)
                                             else None) for j in range(n)) for i in range(n))
    return g


def _wrap_digraph(inst, TE):
    return tuple(tuple(v if (i == j or v is None) else TE(v) for j, v in enumerate(row)) for i, row in enumerate(inst))


def opswap_apsp():
    out = []
    fw, prov_fw = _m(AP + "floyd_warshall.py", func="apsp_floyd_warshall")
    bf, prov_bf = _m(AP + "bellman_ford.py", func="apsp_bellman_ford")
    fw_acc, prov_fwa = _m(AP + "floyd_warshall.py", [("relax_accumulate", ["d < Di[j]"])], func="apsp_floyd_warshall")
    bf_acc, prov_bfa = _m(AP + "bellman_ford.py", [("relax_accumulate", ["d < dist[v]"])], func="apsp_bellman_ford")
    names = ["MinPlus", "MaxPlus", "MaxMin", "MinMax", "Bool", "Viterbi", "MinTimesPos", "MinPlusZ", "Z", "Z7", "GF2"]
    for sname in names:
        S = STRUCT[sname]
        oracle = functools.partial(_apsp_oracle, S=S)
        for dag in (False, True):
            fam = "DAG" if dag else "digraph"
            for subj, prov, name, mode in ((fw, prov_fw, "Floyd-Warshall (unchanged copy)", "inject"),
                                           (bf, prov_bf, "Bellman-Ford (unchanged copy)", "inject"),
                                           (fw_acc, prov_fwa, "Floyd-Warshall (relaxation -> ⊕-accumulation)", "ast+inject"),
                                           (bf_acc, prov_bfa, "Bellman-Ford (relaxation -> ⊕-accumulation)", "ast+inject")):
                cost = None
                if name.startswith("Floyd-Warshall (unchanged") and not dag and sname in ("MaxMin", "Bool", "MinPlus"):
                    cost = counting_cost(lambda cnt, S=S: trop_runner(fw, S, "min", cnt, wrap_pred=_wrap_digraph),
                                         lambda n, S=S: gen_digraph(S)(n, _seeded("fw" + S.name, n)),
                                         [16, 32, 64, 128], "mul", "n**3", tol=0.03)
                out.append(Mutant(
                    pair="all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall", family="OPSWAP",
                    operator=f"semiring:{sname}|{fam}", mode=mode, structure=sname, subject_name=name,
                    oracle_name="⊕ over all simple paths of ⊗ weights (mutations/oracles.py)",
                    description=f"algebraic path problem over {S.label} on random {fam}s (min-origin code: + is ⊗, "
                                "'<' is the ⊕-order)",
                    subject=trop_runner(subj, S, "min", wrap_pred=_wrap_digraph), oracle=oracle,
                    gen=gen_digraph(S, dag), sizes=[1, 2, 3, 4, 5, 6], trials=25,
                    simplify=_simplify_digraph(S, dag), cost=cost,
                    literature=[LIT["floyd"], LIT["warshall"], LIT["lehmann"], LIT["mohri"]],
                    provenance={"subject": prov, "oracle": "mutations/oracles.py:simple_paths_all_pairs"}))
    return out


def _apsp_oracle(inst, S):
    W = tuple(tuple(None if (i == j or v is None) else v for j, v in enumerate(r)) for i, r in enumerate(inst))
    return [list(r) for r in oracles.simple_paths_all_pairs(W, S)]


def _simplify_digraph(S, dag=False):
    pool = [x for x in (None, S.one, 0, 1, 2) if x is None or x != S.zero]

    def simp(M):
        n = len(M)
        rows = [list(r) for r in M]
        for i in range(n):
            for j in range(n):
                if i == j or (dag and i > j):      # keep DAG instances acyclic while shrinking
                    continue
                for c in pool:
                    if c != rows[i][j] and (c is None or rows[i][j] is None or _lt_abs(c, rows[i][j])):
                        y = [r[:] for r in rows]
                        y[i][j] = c
                        yield tuple(tuple(r) for r in y)
    return simp


def _lt_abs(c, v):
    try:
        return abs(c) < abs(v)
    except TypeError:
        return True


# --------------------------------------------------------------------------------------------------
# OPSWAP 3: single-pair paths, Dijkstra vs simple-path enumeration
# --------------------------------------------------------------------------------------------------

SP = P + "shortest-path-enumeration-vs-dijkstra/implementations/"


def gen_complete_digraph(S, nonzero=True):
    def g(n, rng):
        def w():
            while True:
                x = S.sample(rng)
                if not nonzero or x != S.zero:
                    return x
        return tuple(tuple(0 if i == j else w() for j in range(n)) for i in range(n))
    return g


def _wrap_offdiag(inst, TE):
    return tuple(tuple(v if i == j else TE(v) for j, v in enumerate(row)) for i, row in enumerate(inst))


def opswap_dijkstra():
    out = []
    dij, prov_d = _m(SP + "dijkstra.py", func="shortest_path_dijkstra")
    enum, prov_e = _m(SP + "enumeration.py", func="shortest_path_enumerate")
    enum_acc, prov_ea = _m(SP + "enumeration.py", [("call", ["min(best, cost)"], "__oplus__")],
                           func="shortest_path_enumerate")
    for sname in ["MinPlus", "MaxPlus", "MaxMin", "MinMax", "Bool", "Viterbi", "MinTimesPos", "MinPlusZ",
                  "MaxTimesZ", "Z", "Z7"]:
        S = STRUCT[sname]
        oracle = trop_runner(enum_acc, S, "min", wrap_pred=_wrap_offdiag)
        cost = None
        if sname in ("MaxMin", "Viterbi"):
            cost = counting_cost(lambda cnt, S=S: trop_runner(dij, S, "min", cnt, wrap_pred=_wrap_offdiag),
                                 lambda n, S=S: gen_complete_digraph(S)(n, _seeded("dij" + S.name, n)),
                                 [32, 64, 128, 256], "mul", "n**2", tol=0.05)
        out.append(Mutant(
            pair="shortest-path-enumeration-vs-dijkstra", family="OPSWAP", operator=f"semiring:{sname}",
            mode="inject", structure=sname, subject_name="Dijkstra (unchanged copy)",
            oracle_name="simple-path enumeration (copy; min(best, cost) -> ⊕)",
            description=f"best 0 -> n-1 path value over {S.label} on complete digraphs (no zero-weight edges)",
            subject=trop_runner(dij, S, "min", wrap_pred=_wrap_offdiag), oracle=oracle,
            gen=gen_complete_digraph(S), sizes=[2, 3, 4, 5, 6, 7], trials=25,
            simplify=simplify_matrix(_pool_nz(S)), cost=cost,
            literature=[LIT["dijkstra"], LIT["pollack"], LIT["mohri"]],
            provenance={"subject": prov_d, "oracle": prov_ea}))
    # cross-check: the unchanged enumeration under injection agrees with the ⊕-rewritten one on selective S
    for sname in ["MaxMin", "MaxPlus"]:
        S = STRUCT[sname]
        out.append(Mutant(
            pair="shortest-path-enumeration-vs-dijkstra", family="OPSWAP", operator=f"semiring:{sname}",
            mode="inject", structure=sname, subject_name="simple-path enumeration (unchanged copy)",
            oracle_name="simple-path enumeration (copy; min(best, cost) -> ⊕)",
            description="control: the brute side survives under injection on a selective ⊕",
            subject=trop_runner(enum, S, "min", wrap_pred=_wrap_offdiag),
            oracle=trop_runner(enum_acc, S, "min", wrap_pred=_wrap_offdiag),
            gen=gen_complete_digraph(S), sizes=[2, 3, 4, 5, 6], trials=15, trivial="control: brute side vs itself",
            provenance={"subject": prov_e, "oracle": prov_ea}))
    return out


def _pool_nz(S):
    return [x for x in _pool(S) if x != S.zero]


# --------------------------------------------------------------------------------------------------
# OPSWAP 4: maximum subarray (Kadane), max-origin code
# --------------------------------------------------------------------------------------------------

MS = P + "maximum-subarray/implementations/"


def gen_vector(S, nonzero=False):
    def g(n, rng):
        vals = []
        while len(vals) < n:
            x = S.sample(rng)
            if not nonzero or x != S.zero:
                vals.append(x)
        return vals
    return g


def opswap_max_subarray():
    out = []
    brute, pb = _m(MS + "brute_force.py", func="max_subarray_brute")
    brute_acc, pba = _m(MS + "brute_force.py", [("relax_accumulate", ["s > best"])], func="max_subarray_brute")
    kad, pk = _m(MS + "kadane.py", func="max_subarray_kadane")
    kad_acc, pka = _m(MS + "kadane.py", [("ifexp_oplus", ["x if ending_here < 0 else ending_here + x"]),
                                         ("relax_accumulate", ["ending_here > best"])], func="max_subarray_kadane")
    STRUCT_LOCAL = dict(STRUCT)
    STRUCT_LOCAL["MaxPlusZ"] = A.MaxPlus(lo=-10, hi=10, name="MaxPlusZ")
    for sname in ["MaxPlusZ", "MinPlusZ", "MaxMin", "MinMax", "Bool", "Viterbi", "MinTimesPos", "MaxTimesZ",
                  "Z", "Z7", "GF2"]:
        S = STRUCT_LOCAL[sname]
        for subj, prov, name, mode in ((kad, pk, "Kadane (unchanged copy)", "inject"),
                                       (kad_acc, pka, "Kadane (selection -> ⊕)", "ast+inject")):
            cost = None
            if mode == "ast+inject" and sname in ("Z", "Z7"):
                cost = counting_cost(lambda cnt, S=S: trop_runner(kad_acc, S, "max", cnt),
                                     lambda n, S=S: gen_vector(S)(n, _seeded("kad" + S.name, n)),
                                     [64, 256, 1024, 4096], "total", "n")
            out.append(Mutant(
                pair="maximum-subarray", family="OPSWAP", operator=f"semiring:{sname}", mode=mode, structure=sname,
                subject_name=name, oracle_name="⊕ over subarrays of ⊗-products (mutations/oracles.py)",
                description=f"⊕ over non-empty subarrays of the ⊗-product of their entries, over {S.label}",
                subject=trop_runner(subj, S, "max"), oracle=functools.partial(_subarray_oracle, S=S),
                gen=gen_vector(S), sizes=[1, 2, 3, 4, 5, 6, 8], trials=30, simplify=simplify_vector(_pool(S)),
                cost=cost, literature=["bentley1984"],
                provenance={"subject": prov, "oracle": "mutations/oracles.py:subarray_sum_product"}))
        # brute side as a subject: unchanged (selective only) and relaxation -> accumulation
        for subj, prov, name, mode in ((brute, pb, "brute force (unchanged copy)", "inject"),
                                       (brute_acc, pba, "brute force (relaxation -> ⊕)", "ast+inject")):
            out.append(Mutant(
                pair="maximum-subarray", family="OPSWAP", operator=f"semiring:{sname}", mode=mode, structure=sname,
                subject_name=name, oracle_name="⊕ over subarrays of ⊗-products (mutations/oracles.py)",
                description="control: does the brute side survive?",
                subject=trop_runner(subj, S, "max"), oracle=functools.partial(_subarray_oracle, S=S),
                gen=gen_vector(S), sizes=[1, 2, 3, 4, 5, 6], trials=20, simplify=simplify_vector(_pool(S)),
                provenance={"subject": prov, "oracle": "mutations/oracles.py:subarray_sum_product"}))
    return out


def _subarray_oracle(a, S):
    return oracles.subarray_sum_product(list(a), S)


# --------------------------------------------------------------------------------------------------
# OPSWAP 5: zeta transform (Yates) under ⊕-monoid substitution
# --------------------------------------------------------------------------------------------------

ZT = P + "subset-sum-zeta-transform-naive-vs-yates/implementations/"


def opswap_zeta():
    out = []
    naive, pn = _m(ZT + "naive.py", func="zeta_naive")
    yates, py = _m(ZT + "yates.py", func="zeta_yates")
    structs = list(MONO.values()) + [STRUCT["Z7"], STRUCT["GF2"], STRUCT["Bool"], STRUCT["MinPlus"]]
    for S in structs:
        g = lambda n, rng, S=S: tuple(S.sample(rng) for _ in range(1 << n))  # noqa: E731
        cost = None
        if S.name in ("Min", "Gcd", "Or"):
            cost = counting_cost(lambda cnt, S=S: ring_runner(yates, S, counter=cnt),
                                 lambda n, S=S, g=g: g(n, _seeded("zeta" + S.name, n)), [6, 8, 10, 12], "add",
                                 "n * 2**n", library=["2**n", "n * 2**n", "n**2 * 2**n", "3**n"])
        out.append(Mutant(
            pair="subset-sum-zeta-transform-naive-vs-yates", family="OPSWAP", operator=f"monoid:{S.name}",
            mode="inject", structure=S.name, subject_name="Yates (unchanged copy)",
            oracle_name="submask enumeration (unchanged copy)",
            description=f"zeta transform with ⊕ = {S.label}", subject=ring_runner(yates, S),
            oracle=ring_runner(naive, S), gen=g, sizes=[0, 1, 2, 3, 4, 5], trials=20,
            simplify=simplify_vector(_pool(S) if S.kind == "semiring" else S.domain[:4]), cost=cost,
            literature=["yates1937"], provenance={"subject": py, "oracle": pn}))
    return out


# --------------------------------------------------------------------------------------------------
# OPSWAP 6: XOR convolution (FWHT)
# --------------------------------------------------------------------------------------------------

XC = P + "xor-convolution-naive-vs-walsh-hadamard/implementations/"


def opswap_xorconv():
    out = []
    naive, pn = _m(XC + "naive.py", func="xor_convolution_naive")
    fwht, pf = _m(XC + "fwht.py", func="xor_convolution_fwht")
    for sname in ["Z", "Z7", "GF2", "MinPlus", "MaxPlus", "MaxMin", "Bool"]:
        S = STRUCT[sname]
        g = lambda n, rng, S=S: (tuple(S.sample(rng) for _ in range(1 << n)),  # noqa: E731
                                 tuple(S.sample(rng) for _ in range(1 << n)))
        cost = None
        if sname in ("Z", "Z7"):
            cost = counting_cost(lambda cnt, S=S: ring_runner(fwht, S, counter=cnt),
                                 lambda n, S=S, g=g: g(n, _seeded("xc" + S.name, n)), [6, 8, 10, 12], "total",
                                 "n * 2**n", library=["2**n", "n * 2**n", "n**2 * 2**n", "4**n"])
        out.append(Mutant(
            pair="xor-convolution-naive-vs-walsh-hadamard", family="OPSWAP", operator=f"semiring:{sname}",
            mode="inject", structure=sname, subject_name="FWHT (unchanged copy)",
            oracle_name="naive XOR convolution (unchanged copy)",
            description=f"h[k] = ⊕_(i xor j = k) a[i] ⊗ b[j] over {S.label}; FWHT needs u - v and x // 2^n",
            subject=ring_runner(fwht, S), oracle=ring_runner(naive, S), gen=g, sizes=[0, 1, 2, 3, 4], trials=20,
            simplify=simplify_pair(simplify_vector(_pool(S)), simplify_vector(_pool(S))), cost=cost,
            provenance={"subject": pf, "oracle": pn}))
    return out


# --------------------------------------------------------------------------------------------------
# OPSWAP 7: polynomial multiplication, NTT (root-of-unity requirement)
# --------------------------------------------------------------------------------------------------

PM = P + "polynomial-multiplication-naive-vs-ntt/implementations/"


def primitive_root_mod(p):
    """Smallest generator of Z_p^* (p prime), by checking g^((p-1)/q) != 1 for every prime q | p-1."""
    m, qs, d = p - 1, [], 2
    while d * d <= m:
        if m % d == 0:
            qs.append(d)
            while m % d == 0:
                m //= d
        d += 1
    if m > 1:
        qs.append(m)
    for g in range(2, p):
        if all(pow(g, (p - 1) // q, p) != 1 for q in qs):
            return g
    return None


def opswap_ntt():
    out = []
    for p in (998244353, 7681, 97, 17, 1000003):
        S = A.Zp(p)
        g = primitive_root_mod(p)
        naive, pn = _m(PM + "naive.py", [("const", {"P": p})], func="polymul_naive")
        ntt_c, pc = _m(PM + "ntt.py", [("const", {"P": p, "G": g})], func="polymul_ntt")
        v2 = ((p - 1) & -(p - 1)).bit_length() - 1
        gen = lambda n, rng, p=p: (tuple(rng.randrange(p) for _ in range(n)), tuple(rng.randrange(p) for _ in range(n)))  # noqa: E731
        cost = None
        if p == 7681:
            cost = counting_cost(lambda cnt, S=S, f=ntt_c: ring_runner(f, S, counter=cnt),
                                 lambda n, p=p, gen=gen: gen(n, _seeded(f"ntt{p}", n)), [16, 32, 64, 128, 256], "mul",
                                 "3 * n * log2(n) + 5 * n",
                                 library=["n", "n * log(n)", "n**2", "n**log2(3)"])
        out.append(Mutant(
            pair="polynomial-multiplication-naive-vs-ntt", family="OPSWAP", operator=f"ring:Z{p}", mode="ast",
            structure=f"Z{p}", subject_name=f"NTT (copy, P={p}, G={g} = least primitive root)",
            oracle_name=f"schoolbook (copy, P={p})",
            description=f"polynomial product over Z_{p}; p-1 = 2^{v2} * {(p - 1) >> v2}, so primitive 2^k-th roots of "
                        f"unity exist exactly for k <= {v2}",
            subject=ntt_c, oracle=naive, gen=gen, sizes=[1, 2, 3, 4, 5, 8, 9, 12, 16, 17, 33], trials=10,
            simplify=simplify_pair(simplify_vector([0, 1]), simplify_vector([0, 1])), cost=cost,
            literature=[LIT["pollard"], LIT["cooley"]], provenance={"subject": pc, "oracle": pn},
            notes=f"2-adic valuation of p-1: {v2}; the NTT pads to size 2^ceil(log2(2n-1))"))
    # unchanged copy (P = 998244353, G = 3 hard-wired) injected with other coefficient rings
    ntt, pu = _m(PM + "ntt.py", func="polymul_ntt")
    naive_u, pnu = _m(PM + "naive.py", func="polymul_naive")
    for sname, S in (("Z7681", A.Zp(7681)), ("Z", STRUCT["Z"]), ("GF2", STRUCT["GF2"]), ("MinPlus", STRUCT["MinPlus"])):
        g = lambda n, rng, S=S: (tuple(S.sample(rng) for _ in range(n)), tuple(S.sample(rng) for _ in range(n)))  # noqa: E731
        out.append(Mutant(
            pair="polynomial-multiplication-naive-vs-ntt", family="OPSWAP", operator=f"ring:{sname}", mode="inject",
            structure=sname, subject_name="NTT (unchanged copy, roots of Z_998244353 hard-wired)",
            oracle_name="schoolbook (unchanged copy, injected)",
            description=f"coefficients in {S.label}; the twiddle factors are plain ints computed mod 998244353 and "
                        "lifted into the structure", subject=ring_runner(ntt, S), oracle=ring_runner(naive_u, S),
            gen=g, sizes=[1, 2, 3, 4, 5, 8], trials=10,
            simplify=simplify_pair(simplify_vector(_pool(S)), simplify_vector(_pool(S))),
            literature=[LIT["pollard"]], provenance={"subject": pu, "oracle": pnu}))
    return out


# --------------------------------------------------------------------------------------------------
# OPSWAP 8: polynomial Karatsuba (closely related; see related_karatsuba.py)
# --------------------------------------------------------------------------------------------------

def opswap_karatsuba():
    out = []
    kara, pk = _m("mutations/related_karatsuba.py", func="polymul_karatsuba")
    naive, pn = _m(PM + "naive.py", func="polymul_naive")
    for sname in ["Z", "Z7", "GF2", "MinPlus", "MaxPlus", "MaxMin", "Bool"]:
        S = STRUCT[sname]
        g = lambda n, rng, S=S: (tuple(S.sample(rng) for _ in range(n)), tuple(S.sample(rng) for _ in range(n)))  # noqa: E731
        for fb in ([None] if S.has_neg else [None, "add"]):
            cost = None
            if sname in ("Z7", "GF2"):
                cost = counting_cost(lambda cnt, S=S: ring_runner(kara, S, counter=cnt),
                                     lambda n, S=S, g=g: g(n, _seeded("kara" + S.name, n)), [16, 32, 64, 128, 256], "mul",
                                     "n**log2(3)", library=["n", "n * log(n)", "n**2", "n**log2(3)", "n**log2(7)"])
            out.append(Mutant(
                pair="integer-multiplication-schoolbook-vs-karatsuba", family="OPSWAP",
                operator=f"semiring:{sname}" + ("" if fb is None else "+sub:=add"), mode="inject", structure=sname,
                subject_name="polynomial Karatsuba (mutations/related_karatsuba.py)",
                oracle_name="schoolbook polynomial product (copy of the NTT entry's naive.py, injected)",
                description=f"polynomial product over {S.label} (closely related problem: polynomial, not integer, "
                            "Karatsuba)", subject=ring_runner(kara, S, fb), oracle=ring_runner(naive, S), gen=g,
                sizes=[1, 2, 3, 4, 5, 8], trials=15,
                simplify=simplify_pair(simplify_vector(_pool(S)), simplify_vector(_pool(S))), cost=cost,
                literature=["karatsuba-ofman1962"], provenance={"subject": pk, "oracle": pn}))
    return out


# --------------------------------------------------------------------------------------------------
# OPSWAP 9: permanent, naive vs Ryser (+ cross-pair links)
# --------------------------------------------------------------------------------------------------

PR = P + "permanent-naive-vs-ryser/implementations/"


def opswap_permanent():
    out = []
    naive, pn = _m(PR + "naive.py", func="permanent_naive")
    ryser, pr = _m(PR + "ryser.py", func="permanent_ryser")
    for sname in ["Z", "Z7", "GF2", "MinPlus", "MaxPlus", "MaxMin", "Bool", "MinMax"]:
        S = STRUCT[sname]
        g = lambda n, rng, S=S: tuple(tuple(S.sample(rng) for _ in range(n)) for _ in range(n))  # noqa: E731
        for fb in ([None] if S.has_neg else [None, "add"]):
            cost = None
            if sname == "Z7":
                cost = counting_cost(lambda cnt, S=S: ring_runner(ryser, S, counter=cnt),
                                     lambda n, S=S, g=g: g(n, _seeded("ryser" + S.name, n)), [6, 8, 10, 12], "total",
                                     "n * 2**n", library=["2**n", "n * 2**n", "n**2 * 2**n", "factorial(n)"])
            out.append(Mutant(
                pair="permanent-naive-vs-ryser", family="OPSWAP",
                operator=f"semiring:{sname}" + ("" if fb is None else "+sub:=add"), mode="inject", structure=sname,
                subject_name="Ryser (unchanged copy)", oracle_name="sum over permutations (unchanged copy)",
                description=f"permanent over {S.label} (under (min,+) it is the assignment problem)",
                subject=ring_runner(ryser, S, fb), oracle=ring_runner(naive, S), gen=g, sizes=[0, 1, 2, 3, 4, 5, 6],
                trials=15, simplify=simplify_matrix(_pool(S), keep_diag=False), cost=cost,
                literature=["ryser1963", LIT["valiant"]], provenance={"subject": pr, "oracle": pn}))
    # cross-pair links: the semiring images of the permanent are other entries' problems
    hung, ph = _m(P + "assignment-brute-vs-hungarian/implementations/hungarian.py", func="assignment_hungarian")
    MP = STRUCT["MinPlus"]
    gfin = lambda n, rng: tuple(tuple(rng.randint(0, 20) for _ in range(n)) for _ in range(n))  # noqa: E731
    out.append(Mutant(
        pair="permanent-naive-vs-ryser", family="OPSWAP", operator="semiring:MinPlus", mode="io",
        structure="MinPlus", subject_name="Hungarian method (unchanged copy, assignment entry)",
        oracle_name="sum over permutations (unchanged copy, injected MinPlus)",
        description="cross-pair link: the (min,+) permanent of a finite matrix is the assignment problem",
        subject=hung, oracle=lambda M: ring_runner(naive, MP)(M), gen=gfin, sizes=[1, 2, 3, 4, 5, 6], trials=15,
        trivial="known identity: tropical permanent = min-cost assignment (the assignment entry's problem)",
        literature=[LIT["kuhn"]], provenance={"subject": ph, "oracle": pn},
        cost=counting_cost(lambda cnt: _hung_counting(hung, cnt), lambda n: gfin(n, _seeded("hung", n)),
                           [16, 32, 64, 128], "add", "n**3",
                           library=["n**2", "n**2 * log(n)", "n**3", "n**4", "factorial(n)"], tol=0.1)))
    gauss2, pg = _m(P + "determinant-cofactor-vs-gaussian/implementations/gaussian.py", [("const", {"P": 2})],
                    func="det_gaussian")
    G2 = STRUCT["GF2"]
    g2 = lambda n, rng: tuple(tuple(rng.randint(0, 1) for _ in range(n)) for _ in range(n))  # noqa: E731
    out.append(Mutant(
        pair="permanent-naive-vs-ryser", family="OPSWAP", operator="semiring:GF2", mode="ast", structure="GF2",
        subject_name="Gaussian elimination (copy of the determinant entry, P = 2)",
        oracle_name="sum over permutations (unchanged copy, injected GF2)",
        description="cross-pair link: over GF(2), permanent = determinant (signs vanish), so Gaussian elimination works",
        subject=gauss2, oracle=lambda M: ring_runner(naive, G2)(M), gen=g2, sizes=[0, 1, 2, 3, 4, 5, 6], trials=20,
        trivial="known identity: perm = det in characteristic 2", literature=[LIT["valiant"]],
        provenance={"subject": pg, "oracle": pn}))
    return out


class _CountAdd(int):
    pass


def _hung_counting(hung, cnt):
    """Count additions/subtractions/comparisons on input-derived values in the unchanged Hungarian copy."""
    class CW:
        __slots__ = ("v",)

        def __init__(self, v): self.v = v
        @staticmethod
        def _x(o): return o.v if isinstance(o, CW) else o
        def __add__(self, o): cnt["add"] += 1; return CW(self.v + CW._x(o))  # noqa: E702
        def __radd__(self, o): cnt["add"] += 1; return CW(CW._x(o) + self.v)  # noqa: E702
        def __sub__(self, o): cnt["add"] += 1; return CW(self.v - CW._x(o))  # noqa: E702
        def __rsub__(self, o): cnt["add"] += 1; return CW(CW._x(o) - self.v)  # noqa: E702
        def __lt__(self, o): cnt["cmp"] += 1; return self.v < CW._x(o)  # noqa: E702
        def __gt__(self, o): cnt["cmp"] += 1; return self.v > CW._x(o)  # noqa: E702
        def __eq__(self, o): return self.v == CW._x(o)
        def __hash__(self): return hash(self.v)

    def run(M):
        return hung(tuple(tuple(CW(v) for v in r) for r in M))
    return run


# --------------------------------------------------------------------------------------------------
# OPSWAP 10: spanning trees (MST brute force / Prim / Kruskal / Kirchhoff)
# --------------------------------------------------------------------------------------------------

MST = P + "minimum-spanning-tree-brute-vs-kruskal/implementations/"
STC = P + "spanning-tree-count-enumeration-vs-kirchhoff/implementations/"


def gen_sym(S, nonzero=True):
    def g(n, rng):
        W = [[0] * n for _ in range(n)]
        for u in range(n):
            for v in range(u + 1, n):
                while True:
                    x = S.sample(rng)
                    if not nonzero or x != S.zero:
                        break
                W[u][v] = W[v][u] = x
        return tuple(tuple(r) for r in W)
    return g


def opswap_spanning():
    out = []
    prim, pp = _m(MST + "prim.py", func="mst_prim")
    krus, pk = _m(MST + "kruskal.py", func="mst_kruskal")
    brute, pb = _m(MST + "brute_force.py", func="mst_brute")
    kirch, pkh = _m(STC + "kirchhoff_bareiss.py", func="count_spanning_trees_kirchhoff")
    for sname in ["MinPlus", "MaxPlus", "MaxMin", "MinMax", "Bool", "Viterbi", "MinTimesPos", "MaxTimesZ",
                  "MinPlusZ", "Z", "Z7", "GF2"]:
        S = STRUCT[sname]
        oracle = functools.partial(_tree_oracle, S=S)
        subjects = [(prim, pp, "Prim (unchanged copy)", trop_runner(prim, S, "min", wrap_pred=_wrap_offdiag)),
                    (krus, pk, "Kruskal (unchanged copy)", trop_runner(krus, S, "min", wrap_pred=_wrap_offdiag)),
                    (brute, pb, "MST enumeration (unchanged copy)", trop_runner(brute, S, "min", wrap_pred=_wrap_offdiag))]
        if S.kind == "semiring" and S.has_neg or sname in ("MinPlus", "Bool", "MaxMin"):
            subjects.append((kirch, pkh, "Kirchhoff + Bareiss (unchanged copy, weighted Laplacian)",
                             _zero_diag_runner(ring_runner(kirch, S), S)))
        for _, prov, name, run in subjects:
            cost = None
            if name.startswith("Prim") and sname in ("MaxMin", "MinMax"):
                cost = counting_cost(lambda cnt, S=S: trop_runner(prim, S, "min", cnt, wrap_pred=_wrap_offdiag),
                                     lambda n, S=S: gen_sym(S)(n, _seeded("prim" + S.name, n)), [32, 64, 128, 256],
                                     "cmp", "n**2")
            if name.startswith("Kirchhoff") and sname == "Z7":
                cost = counting_cost(lambda cnt, S=S: ring_runner(kirch, S, counter=cnt),
                                     lambda n, S=S: gen_sym(S)(n, _seeded("kir" + S.name, n)), [16, 32, 64],
                                     "mul", "(n - 2) * (n - 1) * (2 * n - 3) / 3",
                                     library=["n**2", "n**2 * log(n)", "n**3", "n**4"])
            out.append(Mutant(
                pair="minimum-spanning-tree-brute-vs-kruskal" if "Kirchhoff" not in name else
                "spanning-tree-count-enumeration-vs-kirchhoff", family="OPSWAP", operator=f"semiring:{sname}",
                mode="inject", structure=sname, subject_name=name,
                oracle_name="⊕ over spanning trees of ⊗ weights (mutations/oracles.py)",
                description=f"spanning-tree sum-product over {S.label} on K_n (no zero-weight edges)",
                subject=run, oracle=oracle, gen=gen_sym(S), sizes=[1, 2, 3, 4, 5, 6], trials=20,
                simplify=simplify_matrix(_pool_nz(S), symmetric=True), cost=cost,
                literature=["kruskal1956", "prim1957", LIT["camerini"], "kirchhoff1847"],
                provenance={"subject": prov, "oracle": "mutations/oracles.py:spanning_trees"}))
    return out


def _zero_diag_runner(run, S):
    """The instance diagonal holds the literal 0 (no self-loop); in ring-origin code it must be S's zero."""
    def r(W):
        return run(tuple(tuple(S.zero if i == j else v for j, v in enumerate(row)) for i, row in enumerate(W)))
    return r


def _tree_oracle(inst, S):
    return oracles.spanning_trees(inst, S)


# --------------------------------------------------------------------------------------------------
# OPSWAP 11: TSP, Held-Karp
# --------------------------------------------------------------------------------------------------

TS = P + "tsp-brute-vs-held-karp/implementations/"


def _oplus_reduce(it):
    return functools.reduce(A.oplus, it)


def opswap_tsp():
    out = []
    hk, ph = _m(TS + "held_karp.py", func="tsp_held_karp")
    hk_acc, pha = _m(TS + "held_karp.py", [("relax_accumulate", ["c < best[T][k]"]),
                                           ("call", ["min(best[full][j] + W[j + 1][0] for j in range(m))"],
                                            "__oplus_reduce__")], extra={"__oplus_reduce__": _oplus_reduce},
                     func="tsp_held_karp")
    br_acc, pba = _m(TS + "brute_force.py", [("relax_accumulate", ["best is None or cost < best"])],
                     func="tsp_brute")
    for sname in ["MinPlus", "MaxPlus", "MaxMin", "MinMax", "Bool", "Viterbi", "MaxTimesZ", "Z", "Z7", "GF2"]:
        S = STRUCT[sname]
        for subj, prov, name, mode in ((hk, ph, "Held-Karp (unchanged copy)", "inject"),
                                       (hk_acc, pha, "Held-Karp (relaxation -> ⊕-accumulation)", "ast+inject")):
            cost = None
            if mode == "ast+inject" and sname in ("Z", "MaxMin"):
                cost = counting_cost(lambda cnt, S=S: trop_runner(hk_acc, S, "min", cnt, wrap_pred=_wrap_offdiag),
                                     lambda n, S=S: gen_complete_digraph(S)(n, _seeded("hk" + S.name, n)),
                                     [6, 8, 10, 12], "mul", "(n - 1) * (n - 2) * 2**(n - 3) + n - 1",
                                     library=["n * 2**n", "n**2 * 2**n", "n**3 * 2**n", "3**n", "factorial(n)"])
            out.append(Mutant(
                pair="tsp-brute-vs-held-karp", family="OPSWAP", operator=f"semiring:{sname}", mode=mode,
                structure=sname, subject_name=name,
                oracle_name="permutation enumeration (copy; relaxation -> ⊕)",
                description=f"⊕ over Hamiltonian cycles through 0 of the ⊗-product of arc weights, over {S.label}",
                subject=trop_runner(subj, S, "min", wrap_pred=_wrap_offdiag),
                oracle=trop_runner(br_acc, S, "min", wrap_pred=_wrap_offdiag),
                gen=gen_complete_digraph(S), sizes=[2, 3, 4, 5, 6, 7], trials=15,
                simplify=simplify_matrix(_pool_nz(S)), cost=cost,
                literature=[LIT["held_karp"], LIT["bellman_tsp"]], provenance={"subject": prov, "oracle": pba}))
    return out


# --------------------------------------------------------------------------------------------------
# OPSWAP 12: optimal BST (DP recurrence; Knuth's speed-up)
# --------------------------------------------------------------------------------------------------

OB = P + "optimal-bst-recursion-vs-dp-vs-knuth/implementations/"


def opswap_obst():
    out = []
    rec_acc, pr = _m(OB + "recursion.py", [("relax_accumulate", ["best is None or cand < best"])],
                     func="obst_recursive")
    cub, pc = _m(OB + "cubic_dp.py", func="obst_cubic")
    cub_acc, pca = _m(OB + "cubic_dp.py", [("relax_accumulate", ["best is None or cand < best"])], func="obst_cubic")
    knuth, pk = _m(OB + "knuth.py", func="obst_knuth")

    def gen(S):
        def g(n, rng):
            return (tuple(S.sample(rng) for _ in range(n)), tuple(S.sample(rng) for _ in range(n + 1)))
        return g

    for sname in ["MinPlus", "MaxPlus", "MaxMin", "MinMax", "Viterbi", "MinTimesPos", "Z", "Z7"]:
        S = STRUCT[sname]
        for subj, prov, name, mode in ((cub, pc, "cubic DP (unchanged copy)", "inject"),
                                       (cub_acc, pca, "cubic DP (relaxation -> ⊕)", "ast+inject"),
                                       (knuth, pk, "Knuth's quadratic DP (unchanged copy)", "inject")):
            out.append(Mutant(
                pair="optimal-bst-recursion-vs-dp-vs-knuth", family="OPSWAP", operator=f"semiring:{sname}",
                mode=mode, structure=sname, subject_name=name, oracle_name="plain recursion (copy; relaxation -> ⊕)",
                description=f"c(i,j) = w(i,j) ⊗ ⊕_k c(i,k-1) ⊗ c(k,j) with w = ⊗ of the frequencies, over {S.label}",
                subject=trop_runner(subj, S, "min"), oracle=trop_runner(rec_acc, S, "min"), gen=gen(S),
                sizes=[0, 1, 2, 3, 4, 5, 6, 7], trials=20,
                simplify=simplify_pair(simplify_vector(_pool(S)), simplify_vector(_pool(S))),
                trivial=("identical recurrence: the cubic DP memoises the same expression DAG as the recursion"
                         if "cubic" in name else None),
                literature=[LIT["knuth_obst"], LIT["yao"]], provenance={"subject": prov, "oracle": pr}))
    return out


# --------------------------------------------------------------------------------------------------
# OPSWAP 13: range queries, sparse table (idempotence)
# --------------------------------------------------------------------------------------------------

RQ = P + "range-minimum-queries-naive-vs-sparse-table/implementations/"


def _rmq_gen(S):
    def g(n, rng):
        vals = tuple(S.sample(rng) for _ in range(n))
        qs = []
        for _ in range(n):
            l, r = sorted((rng.randrange(n), rng.randrange(n)))
            qs.append((l, r))
        return vals, tuple(qs)
    return g


def _wrap_rmq(inst, TE):
    vals, qs = inst
    return tuple(TE(v) for v in vals), qs


def opswap_rmq():
    out = []
    naive_acc, pn = _m(RQ + "naive_scan.py", [("relax_accumulate", ["x < m"])], func="rmq_naive")
    sp_acc, ps = _m(RQ + "sparse_table.py", [("call", ["min(prev[i], prev[i + half])"], "__oplus__"),
                                             ("ifexp_oplus", ["a if a <= b else b"])], func="rmq_sparse_table")
    for S in MONO.values():
        cost = None
        if S.name in ("Gcd", "Max"):
            cost = counting_cost(lambda cnt, S=S: trop_runner(sp_acc, S, "min", cnt, wrap_pred=_wrap_rmq),
                                 lambda n, S=S: _rmq_gen(S)(n, _seeded("rmq" + S.name, n)), [64, 256, 1024, 4096],
                                 "add", "n * log(n)", library=["n", "n * log(n)", "n**2"])
        out.append(Mutant(
            pair="range-minimum-queries-naive-vs-sparse-table", family="OPSWAP", operator=f"monoid:{S.name}",
            mode="ast+inject", structure=S.name, subject_name="sparse table (min -> ⊕ in the copy)",
            oracle_name="scan each range (copy; relaxation -> ⊕)",
            description=f"range ⊕-queries with ⊕ = {S.label}; the O(1) query combines two OVERLAPPING blocks",
            subject=trop_runner(sp_acc, S, "min", wrap_pred=_wrap_rmq),
            oracle=trop_runner(naive_acc, S, "min", wrap_pred=_wrap_rmq), gen=_rmq_gen(S),
            sizes=[1, 2, 3, 4, 5, 8, 12], trials=20,
            simplify=simplify_pair(simplify_vector(S.domain[:4]), lambda q: iter(())),
            trivial="control: the original operation" if S.name == "Min" else None, cost=cost,
            literature=[LIT["bender"]], provenance={"subject": ps, "oracle": pn}))
    return out


# --------------------------------------------------------------------------------------------------
# OPSWAP 14: exponentiation by squaring (⊗-magma substitution)
# --------------------------------------------------------------------------------------------------

ME = P + "modular-exponentiation-repeated-vs-square-multiply/implementations/"


def opswap_power():
    out = []
    rep, pr = _m(ME + "repeated.py", func="modpow_repeated")
    sqm, ps = _m(ME + "square_multiply.py", func="modpow_square_multiply")

    def gen(S):
        def g(n, rng):
            return (S.sample(rng), rng.randrange(1 << max(n - 1, 0), 1 << n) if n else 0, 1009)
        return g

    def runner(fn, S, cnt=None):
        RE = A.make_ring_elem(S, cnt)

        def run(inst):
            a, e, m = inst
            r = fn((RE(a), e, m))
            return r.v if isinstance(r, RE) else S.lift(r)
        return run

    for S in MAG.values():
        cost = None
        if S.name in ("Mat2", "Octonion"):
            cost = counting_cost(lambda cnt, S=S: runner(sqm, S, cnt),
                                 lambda n, S=S: (S.sample(_seeded("pow" + S.name, n)), (1 << n) - 1, 1009),
                                 [8, 16, 32, 64, 128], "mul", "n", library=["n", "n * log(n)", "n**2", "2**n"])
        out.append(Mutant(
            pair="modular-exponentiation-repeated-vs-square-multiply", family="OPSWAP", operator=f"magma:{S.name}",
            mode="inject", structure=S.name, subject_name="square-and-multiply (unchanged copy)",
            oracle_name="repeated multiplication = left fold (unchanged copy)",
            description=f"a^e with ⊗ = {S.label}; '% m' is the identity on injected elements, literal 1 -> identity",
            subject=runner(sqm, S), oracle=runner(rep, S), gen=gen(S), sizes=[0, 1, 2, 3, 4, 5, 6, 8], trials=25,
            trivial="control: the original operation" if S.name == "MulMod" else None, cost=cost,
            literature=["knuth-taocp2"], provenance={"subject": ps, "oracle": pr}))
    return out


# --------------------------------------------------------------------------------------------------
# MIRROR family
# --------------------------------------------------------------------------------------------------

def _rev_wrap(inst):
    return nested_wrap(inst, lambda v: A.Rev(v) if isinstance(v, int) and not isinstance(v, bool) else v)


def _rev_wrap_offdiag(W):
    return tuple(tuple(v if i == j else A.Rev(v) for j, v in enumerate(r)) for i, r in enumerate(W))


def _neg(x):
    return nested_wrap(x, lambda v: -v if isinstance(v, (int, float)) and not isinstance(v, bool) else v)


def mirror_all():
    out = []
    TRIV_NEG = "objective flip by negation: max f(x) = -min(-f(x)) is a known trivial reparametrisation"
    TRIV_REV = "comparison flip = running on the order dual; equivalent to negating the weights (trivial)"
    # --- MST -> maximum spanning tree
    prim, pp = _m(MST + "prim.py", func="mst_prim")
    krus, pk = _m(MST + "kruskal.py", func="mst_kruskal")
    brute, pb = _m(MST + "brute_force.py", func="mst_brute")
    prim_f, ppf = _m(MST + "prim.py", [("flip", ["best[v] < best[u]", "row[v] < best[v]"])], func="mst_prim")
    krus_f, pkf = _m(MST + "kruskal.py", [("sorted_reverse", ["sorted(W[u][v] * nn + u * n + v for u in range(n) "
                                                              "for v in range(u + 1, n))"])], func="mst_kruskal")
    brute_f, pbf = _m(MST + "brute_force.py", [("flip", ["total < best"])], func="mst_brute")
    g_mst = lambda n, rng: tuple(tuple(r) for r in _symm(n, rng, 1, 30))  # noqa: E731
    oracle = lambda W: A.unwrap(brute(_rev_wrap_offdiag(W)))  # noqa: E731
    for name, subj, mode, prov, triv in (
            ("Kruskal: -kruskal(-W)", lambda W: -krus(_neg(W)), "io", pk, TRIV_NEG),
            ("Prim: -prim(-W)", lambda W: -prim(_neg(W)), "io", pp, TRIV_NEG),
            ("Kruskal on Rev-ordered weights", lambda W: A.unwrap(krus(_rev_wrap_offdiag(W))), "inject", pk, TRIV_REV),
            ("Prim on Rev-ordered weights", lambda W: A.unwrap(prim(_rev_wrap_offdiag(W))), "inject", pp, TRIV_REV),
            ("Kruskal, sorted(..., reverse=True)", krus_f, "ast", pkf, TRIV_REV),
            ("Prim, both value comparisons flipped", prim_f, "ast", ppf, TRIV_REV),
            ("MST enumeration, 'total < best' flipped", brute_f, "ast", pbf, TRIV_REV)):
        out.append(Mutant(pair="minimum-spanning-tree-brute-vs-kruskal", family="MIRROR", operator="min->max",
                          mode=mode, subject_name=name, oracle_name="MST enumeration on Rev-ordered weights",
                          description="maximum spanning tree weight", subject=subj, oracle=oracle, gen=g_mst,
                          sizes=[1, 2, 3, 4, 5, 6], trials=20, trivial=triv,
                          simplify=simplify_matrix([1, 2], symmetric=True),
                          literature=["kruskal1956"], provenance={"subject": prov, "oracle": pb}))
    # reciprocal weights: min sum of 1/w -- greedy depends only on the order, so the max spanning tree of w is optimal
    def recip_subject(W):
        n = len(W)
        if n <= 1:
            return Fraction(0)
        Wr = tuple(tuple(Fraction(1, v) if i != j else 0 for j, v in enumerate(r)) for i, r in enumerate(W))
        return prim(Wr)
    out.append(Mutant(pair="minimum-spanning-tree-brute-vs-kruskal", family="MIRROR", operator="reciprocal",
                      mode="io", subject_name="Prim (unchanged copy) on 1/w (Fractions)",
                      oracle_name="MST enumeration (unchanged copy) on 1/w",
                      description="minimum spanning tree under reciprocal weights 1/w",
                      subject=recip_subject,
                      oracle=lambda W: brute(tuple(tuple(Fraction(1, v) if i != j else 0 for j, v in enumerate(r))
                                                   for i, r in enumerate(W))),
                      gen=g_mst, sizes=[1, 2, 3, 4, 5, 6], trials=20,
                      trivial="reciprocal weights are just another positive weight function: same problem class",
                      literature=[LIT["edmonds"]], provenance={"subject": pp, "oracle": pb}))
    # --- shortest path -> longest simple path
    dij, pd = _m(SP + "dijkstra.py", func="shortest_path_dijkstra")
    enum, pe = _m(SP + "enumeration.py", func="shortest_path_enumerate")
    g_sp = lambda n, rng: tuple(tuple(0 if i == j else rng.randint(1, 30) for j in range(n)) for i in range(n))  # noqa: E731
    dij_f, pdf = _m(SP + "dijkstra.py", [("replace", {"math.inf": "-math.inf"}),
                                         ("call", ["min((d, v) for v, d in enumerate(dist) if not done[v])"], "max"),
                                         ("flip", ["dist[u] + row[v] < dist[v]"])], func="shortest_path_dijkstra")
    lp_oracle = oracles.longest_simple_path
    for name, subj, mode in (("Dijkstra: -dijkstra(-W)", lambda W: -dij(_neg(W)), "io"),
                             ("Dijkstra on Rev-ordered weights (sentinel math.inf not flipped)",
                              lambda W: A.unwrap(dij(_rev_wrap_offdiag(W))), "inject"),
                             ("Dijkstra, min -> max selection, relaxation flipped, sentinel -inf", dij_f, "ast")):
        out.append(Mutant(pair="shortest-path-enumeration-vs-dijkstra", family="MIRROR", operator="min->max",
                          mode=mode, subject_name=name, oracle_name="longest simple path by enumeration (mutations/oracles.py)",
                          description="longest simple 0 -> n-1 path", subject=subj, oracle=lp_oracle, gen=g_sp,
                          sizes=[2, 3, 4, 5, 6, 7], trials=20, simplify=simplify_matrix([1, 2]),
                          literature=[LIT["dijkstra"], "garey-johnson1979"],
                          provenance={"subject": pdf if mode == "ast" else pd,
                                      "oracle": "mutations/oracles.py:longest_simple_path"}))
    out.append(Mutant(pair="shortest-path-enumeration-vs-dijkstra", family="MIRROR", operator="reciprocal",
                      mode="io", subject_name="Dijkstra (unchanged copy) on 1/w", oracle_name="enumeration on 1/w",
                      description="shortest path under reciprocal weights",
                      subject=lambda W: dij(_recip(W)), oracle=lambda W: enum(_recip(W)), gen=g_sp,
                      sizes=[2, 3, 4, 5, 6], trials=15,
                      trivial="reciprocal weights are just another positive weight function: same problem class",
                      provenance={"subject": pd, "oracle": pe}))
    # --- maximum subarray -> minimum subarray
    kad, pk2 = _m(MS + "kadane.py", func="max_subarray_kadane")
    bru, pb2 = _m(MS + "brute_force.py", func="max_subarray_brute")
    kad_f, pkf2 = _m(MS + "kadane.py", [("flip", ["ending_here < 0", "ending_here > best"])], func="max_subarray_kadane")
    bru_f, pbf2 = _m(MS + "brute_force.py", [("flip", ["s > best"])], func="max_subarray_brute")
    g_ms = lambda n, rng: [rng.randint(-20, 20) for _ in range(n)]  # noqa: E731
    for name, subj, mode, triv in (("Kadane: -kadane(-a)", lambda a: -kad(_neg(a)), "io", TRIV_NEG),
                                   ("Kadane on Rev values", lambda a: A.unwrap(kad(_rev_wrap(a))), "inject", TRIV_REV),
                                   ("Kadane, both comparisons flipped", kad_f, "ast", TRIV_REV)):
        out.append(Mutant(pair="maximum-subarray", family="MIRROR", operator="max->min", mode=mode, subject_name=name,
                          oracle_name="brute force, 's > best' flipped", description="minimum subarray sum",
                          subject=subj, oracle=bru_f, gen=g_ms, sizes=[1, 2, 3, 4, 6, 8], trials=30, trivial=triv,
                          simplify=simplify_vector([0, 1, -1]), provenance={"subject": pk2, "oracle": pbf2}))
    # --- closest pair -> farthest pair
    CP = P + "closest-pair-brute-vs-divide-conquer/implementations/"
    cpb_f, pcb = _m(CP + "brute_force.py", [("flip", ["d < best"])], func="closest_pair_brute")
    cpd_f, pcd = _m(CP + "divide_conquer.py",
                    [("call", ["min(_dist2(px[i], px[j]) for i in range(lo, hi) for j in range(i + 1, hi))",
                               "min(best_l, best_r)"], "max"),
                     ("flip", ["(p[0] - xm) ** 2 < best", "dy * dy >= best", "d < best"])], func="closest_pair_dc")
    g_cp = lambda n, rng: tuple((rng.randrange(20), rng.randrange(20)) for _ in range(n))  # noqa: E731
    out.append(Mutant(pair="closest-pair-brute-vs-divide-conquer", family="MIRROR", operator="min->max", mode="ast",
                      subject_name="divide and conquer, min -> max and distance comparisons flipped",
                      oracle_name="all pairs, 'd < best' flipped", description="farthest pair (diameter, squared)",
                      subject=cpd_f, oracle=cpb_f, gen=g_cp, sizes=[2, 3, 4, 5, 6, 8, 12, 16], trials=25,
                      simplify=_simplify_points, literature=[LIT["shamos"], "preparata-shamos1985"],
                      provenance={"subject": pcd, "oracle": pcb}))
    # --- global min cut -> max cut
    GC = P + "global-min-cut-brute-vs-stoer-wagner/implementations/"
    sw, psw = _m(GC + "stoer_wagner.py", func="min_cut_stoer_wagner")
    sw_f, pswf = _m(GC + "stoer_wagner.py", [("flip", ["key[v] > key[sel]", "cut_of_phase < best"])],
                    func="min_cut_stoer_wagner")
    g_gc = lambda n, rng: tuple(tuple(r) for r in _symm(n, rng, 0, 9))  # noqa: E731
    for name, subj, mode in (("Stoer-Wagner: -sw(-W)", lambda W: -sw(_neg(W)), "io"),
                             ("Stoer-Wagner, both comparisons flipped", sw_f, "ast")):
        out.append(Mutant(pair="global-min-cut-brute-vs-stoer-wagner", family="MIRROR", operator="min->max",
                          mode=mode, subject_name=name, oracle_name="max cut by enumerating bipartitions",
                          description="global maximum cut", subject=subj, oracle=oracles.max_cut_brute, gen=g_gc,
                          sizes=[2, 3, 4, 5, 6, 7], trials=25, simplify=simplify_matrix([0, 1], symmetric=True),
                          literature=[LIT["karp"]], provenance={"subject": psw if mode == "io" else pswf,
                                                                 "oracle": "mutations/oracles.py:max_cut_brute"}))
    # complement (cut <-> uncut) for min cut has no instance transformation: cut_(c-w)(S) = c|S||T| - cut_w(S)
    # depends on |S| (decision log). The complement operator is applied to MST instead (affine, trivial).
    def mst_complement(W):
        n = len(W)
        if n <= 1:
            return 0
        c = max(v for r in W for v in r) + 1
        Wc = tuple(tuple(0 if i == j else c - v for j, v in enumerate(r)) for i, r in enumerate(W))
        return (n - 1) * c - krus(Wc)
    out.append(Mutant(pair="minimum-spanning-tree-brute-vs-kruskal", family="MIRROR", operator="complement",
                      mode="io", subject_name="Kruskal on complement weights c - w, result (n-1)c - value",
                      oracle_name="MST enumeration on Rev-ordered weights", description="maximum spanning tree weight",
                      subject=mst_complement, oracle=oracle, gen=g_mst, sizes=[1, 2, 3, 4, 5, 6], trials=20,
                      trivial="affine reparametrisation w -> c - w (every spanning tree has n-1 edges)",
                      literature=["kruskal1956"], provenance={"subject": pk, "oracle": pb}))
    # --- assignment -> maximum-weight assignment
    AS = P + "assignment-brute-vs-hungarian/implementations/"
    hung, ph = _m(AS + "hungarian.py", func="assignment_hungarian")
    ab, pab = _m(AS + "brute_force.py", func="assignment_brute")
    g_as = lambda n, rng: tuple(tuple(rng.randint(0, 30) for _ in range(n)) for _ in range(n))  # noqa: E731
    as_oracle = lambda C: A.unwrap(ab(_rev_wrap(C)))  # noqa: E731
    for name, subj, mode, triv in (("Hungarian: -hungarian(-C)", lambda C: -hung(_neg(C)), "io", TRIV_NEG),
                                   ("Hungarian on Rev values", lambda C: A.unwrap(hung(_rev_wrap(C))), "inject", None)):
        out.append(Mutant(pair="assignment-brute-vs-hungarian", family="MIRROR", operator="min->max", mode=mode,
                          subject_name=name, oracle_name="permutation enumeration on Rev values",
                          description="maximum-weight perfect assignment", subject=subj, oracle=as_oracle, gen=g_as,
                          sizes=[1, 2, 3, 4, 5, 6], trials=20, trivial=triv, simplify=simplify_matrix([0, 1], keep_diag=False),
                          literature=[LIT["kuhn"]], provenance={"subject": ph, "oracle": pab}))
    # --- TSP -> max TSP
    hk, phk = _m(TS + "held_karp.py", func="tsp_held_karp")
    tb, ptb = _m(TS + "brute_force.py", func="tsp_brute")
    g_t = lambda n, rng: tuple(tuple(0 if i == j else rng.randint(1, 30) for j in range(n)) for i in range(n))  # noqa: E731
    t_oracle = lambda W: A.unwrap(tb(_rev_wrap_offdiag(W)))  # noqa: E731
    hk_f, phkf = _m(TS + "held_karp.py", [("replace", {"math.inf": "-math.inf"}), ("flip", ["c < best[T][k]"]),
                                          ("call", ["min(best[full][j] + W[j + 1][0] for j in range(m))"], "max")],
                    func="tsp_held_karp")
    for name, subj, mode, triv in (("Held-Karp: -hk(-W)", lambda W: -hk(_neg(W)), "io", TRIV_NEG),
                                   ("Held-Karp on Rev weights (sentinel math.inf not flipped)",
                                    lambda W: A.unwrap(hk(_rev_wrap_offdiag(W))), "inject", None),
                                   ("Held-Karp, relaxation flipped, min -> max, sentinel -inf", hk_f, "ast",
                                    "exact DP over (set, last city): valid for any objective; max-TSP by the same DP")):
        out.append(Mutant(pair="tsp-brute-vs-held-karp", family="MIRROR", operator="min->max", mode=mode,
                          subject_name=name, oracle_name="permutation enumeration on Rev weights",
                          description="maximum-weight Hamiltonian cycle", subject=subj, oracle=t_oracle, gen=g_t,
                          sizes=[2, 3, 4, 5, 6, 7], trials=15, trivial=triv, simplify=simplify_matrix([1, 2]),
                          literature=[LIT["held_karp"]], provenance={"subject": phk, "oracle": ptb}))
    # --- LIS -> longest decreasing subsequence; inversions -> non-inversions; RMQ -> range max
    LI = P + "longest-increasing-subsequence/implementations/"
    pat, ppat = _m(LI + "patience.py", func="lis_patience")
    sub, psub = _m(LI + "subset_enumeration.py", func="lis_subsets")
    g_l = lambda n, rng: [rng.randint(-5, 5) for _ in range(n)]  # noqa: E731
    out.append(Mutant(pair="longest-increasing-subsequence", family="MIRROR", operator="comparison-flip",
                      mode="inject", subject_name="patience sorting on Rev values",
                      oracle_name="subset enumeration on Rev values", description="longest strictly decreasing subsequence",
                      subject=lambda a: pat(_rev_wrap(a)), oracle=lambda a: sub(_rev_wrap(a)), gen=g_l,
                      sizes=[0, 1, 2, 3, 5, 8, 10], trials=25, trivial=TRIV_REV, simplify=simplify_vector([0, 1, -1]),
                      provenance={"subject": ppat, "oracle": psub}))
    IV = P + "inversion-counting-quadratic-vs-merge/implementations/"
    im, pim = _m(IV + "merge_count.py", func="inversions_merge")
    iq, piq = _m(IV + "pairs_scan.py", func="inversions_quadratic")
    out.append(Mutant(pair="inversion-counting-quadratic-vs-merge", family="MIRROR", operator="comparison-flip",
                      mode="inject", subject_name="merge-sort counting on Rev values",
                      oracle_name="all pairs on Rev values", description="count pairs i < j with a[i] < a[j]",
                      subject=lambda a: im(_rev_wrap(a)), oracle=lambda a: iq(_rev_wrap(a)), gen=g_l,
                      sizes=[0, 1, 2, 3, 5, 8, 16], trials=25, trivial=TRIV_REV, simplify=simplify_vector([0, 1, -1]),
                      provenance={"subject": pim, "oracle": piq}))
    rn, prn = _m(RQ + "naive_scan.py", func="rmq_naive")
    rs, prs = _m(RQ + "sparse_table.py", func="rmq_sparse_table")
    g_r = lambda n, rng: (tuple(rng.randint(-9, 9) for _ in range(n)),  # noqa: E731
                          tuple(tuple(sorted((rng.randrange(n), rng.randrange(n)))) for _ in range(n)))
    out.append(Mutant(pair="range-minimum-queries-naive-vs-sparse-table", family="MIRROR", operator="comparison-flip",
                      mode="inject", subject_name="sparse table on Rev values", oracle_name="scan on Rev values",
                      description="range maximum queries",
                      subject=lambda inst: A.unwrap(rs((_rev_wrap(inst[0]), inst[1]))),
                      oracle=lambda inst: A.unwrap(rn((_rev_wrap(inst[0]), inst[1]))), gen=g_r,
                      sizes=[1, 2, 3, 5, 8, 13], trials=20, trivial=TRIV_REV,
                      provenance={"subject": prs, "oracle": prn}))
    return out


def _symm(n, rng, lo, hi):
    W = [[0] * n for _ in range(n)]
    for u in range(n):
        for v in range(u + 1, n):
            W[u][v] = W[v][u] = rng.randint(lo, hi)
    return W


def _recip(W):
    return tuple(tuple(0 if i == j else Fraction(1, v) for j, v in enumerate(r)) for i, r in enumerate(W))


def _simplify_points(pts):
    pts = list(pts)
    for i in range(len(pts)):
        if len(pts) > 2:
            yield tuple(pts[:i] + pts[i + 1:])
    for i, (x, y) in enumerate(pts):
        for nx, ny in ((x // 2, y), (x, y // 2), (0, y), (x, 0)):
            if (nx, ny) != (x, y):
                q = pts[:]
                q[i] = (nx, ny)
                yield tuple(q)


OPSWAP_BUILDERS = {
    "matmul": opswap_matmul, "apsp": opswap_apsp, "dijkstra": opswap_dijkstra, "maxsubarray": opswap_max_subarray,
    "zeta": opswap_zeta, "xorconv": opswap_xorconv, "ntt": opswap_ntt, "karatsuba": opswap_karatsuba,
    "permanent": opswap_permanent, "spanning": opswap_spanning, "tsp": opswap_tsp, "obst": opswap_obst,
    "rmq": opswap_rmq, "power": opswap_power,
}
MIRROR_BUILDERS = {"mirror": mirror_all}


def structures_for_properties():
    out = dict(STRUCT)
    out["MaxPlusZ"] = A.MaxPlus(lo=-10, hi=10, name="MaxPlusZ")
    for p in (998244353, 7681, 97, 17, 1000003):
        out[f"Z{p}"] = A.Zp(p)
    out.update({f"monoid:{k}": v for k, v in MONO.items()})
    out.update({f"magma:{k}": v for k, v in MAG.items()})
    return out
