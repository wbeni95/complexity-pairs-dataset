#!/usr/bin/env python3
"""Rule hypotheses, near-miss metrics and repairs on FRESH seeds and held-out families (round 2026-10-06d).

Every test here uses generator seeds 2 and 3 (the mass screen used seed 1) or families that the mass screen did
not generate. Each section prints its numbers and writes them to results/2026-10-06d/hypotheses.json and
candidates/2026-10-06d/hypotheses.json.

  H-M1  magma_power: binary powering is exact iff the square condition p_a * p_a = p_(2a) holds (for all x);
        tested against associativity and power-associativity on seed 2 (m <= 5) and a held-out m = 6 set;
        fast_cycle (left-power cycle detection) exact on every magma.
  H-K1  knuth: per-instance confusion of Yao's conditions (QI, monotone) and root monotonicity vs exactness,
        including the held-out family subint_sep (QI holds, monotonicity may fail).
  H-K2  knuth: translation-invariant weights w(i, j) = h(j - i) make Knuth exact (suggested by concave_len,
        which violates QI on every instance yet was EXACT); held-out family random_len.
  H-G1  greedy: worst ratio over random weights >= rank quotient q; adversarial weights attain q; how often random
        weights detect a non-matroid; per-weight-distribution exact rates (robustness).
  H-C1  convolution: table-agreement score vs output-agreement (two nearness metrics); the repaired rule
        (transform + sparse correction) is exact on every table; cost threshold of the repair.
  H-T1  mitm: unique completion vs exactness; all-solutions repair exact on every interaction-free family;
        boundary conditioning exact on crossing interactions, and its cost vs |B|.
  H-B1  bilinear: fraction of random GF(2) maps with rank < support, by format and density; for rank = support,
        the best (support - 1)-term approximation never yields a gain after repair.
  H-R1  memo2d: the diagonal growth constant from min 1/(xy) vs the counting DP at n = 100..200.
  H-R2  compress1d: exact iff delta = 0, no flips, OR the flag is a function of n on the reachable states
        (refined precondition suggested by the 4 mass-screen candidates that were EXACT without the stated one).

Deterministic. Below-normal priority, single process, about a minute.
Usage: python experiments/2026-10-06d_rules_hypotheses.py
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from search.machine import set_below_normal_priority  # noqa: E402

from generators.rules import bilinear, convolution, greedy, knuth, magma_power, memo, mitm  # noqa: E402
from generators.rules.common import Ops, relabel_table, screen  # noqa: E402

OUT = {}


def h_m1():
    rows = []
    specs = magma_power.generate(2, 600)
    rng = random.Random("rules|H-M1|heldout")
    for _ in range(300):  # held-out: m = 6, families random/comm/idem/latin
        fam = rng.choice(["random", "comm", "idem", "idem_comm", "latin"])
        T = magma_power.make_table(fam, rng, 6)
        specs.append({"family": fam, "m": 6, "table": relabel_table(T, rng.sample(range(6), 6)), "heldout": True})
    for s in specs:
        c = magma_power.build(s)
        r = screen(c, do_scaling=False)
        # exhaustive check for all x and all e <= 4 m (covers pre-period + period twice)
        exact_all = all(c.slow((c.T, x, e), Ops()) == c.fast((c.T, x, e), Ops())
                        for x in range(c.m) for e in range(1, 4 * c.m + 8))
        cyc_all = all(c.slow((c.T, x, e), Ops()) == c.fast_cycle((c.T, x, e), Ops())
                      for x in range(c.m) for e in range(1, 4 * c.m + 8))
        p = r["predicates"]
        rows.append((s.get("heldout", False), p["associative"], p["power_assoc"], p["square_cond"], exact_all,
                     r["verdict"], cyc_all, r["exact_rate"]))
    res = {}
    for held in (False, True):
        sub = [x for x in rows if x[0] == held]
        tag = "heldout_m6" if held else "seed2"
        res[tag] = {
            "magmas": len(sub),
            "square_cond_iff_exact_all_e": sum(x[3] == x[4] for x in sub),
            "assoc": sum(x[1] for x in sub), "power_assoc": sum(x[2] for x in sub), "square_cond": sum(x[3] for x in sub),
            "exact_all_e": sum(x[4] for x in sub),
            "exact_not_assoc": sum(x[4] and not x[1] for x in sub),
            "exact_not_power_assoc": sum(x[4] and not x[2] for x in sub),
            "power_assoc_not_assoc": sum(x[2] and not x[1] for x in sub),
            "screen_exact_but_not_exact_all_e": sum(x[5] == "EXACT" and not x[4] for x in sub),
            "fast_cycle_exact": sum(x[6] for x in sub),
            "near_miss_exact_rates": sorted(round(x[7], 3) for x in sub if x[5] == "NEAR-MISS")[:5] + ["..."],
        }
    OUT["H-M1"] = res
    print("H-M1", json.dumps(res))


def h_k():
    fams = knuth.FAMILIES + knuth.HELD_OUT
    per = defaultdict(Counter)
    tot = Counter()
    for fam in fams:
        specs = knuth.generate(3, 40, families=[fam])
        for s in specs:
            c = knuth.build(s)
            for n in (6, 8, 10):
                for t in range(5):
                    prof = c.instance_profile(random.Random(f"H-K|{c.id}|{n}|{t}"), n)
                    qi, mono = prof["qi_viol"] == 0, prof["mono_viol"] == 0
                    key = (f"QI={'y' if qi else 'n'}", f"mono={'y' if mono else 'n'}",
                           f"rootmono={'y' if prof['root_monotone'] else 'n'}", f"exact={'y' if prof['exact'] else 'n'}")
                    per[fam]["|".join(key)] += 1
                    tot["|".join(key)] += 1
    # derived statements
    root_implies_exact = all(not (k.split("|")[2] == "rootmono=y" and k.split("|")[3] == "exact=n") for k in tot)
    yao_implies_exact = all(not (k.startswith("QI=y|mono=y") and k.endswith("exact=n")) for k in tot)
    qi_only = Counter()
    for k, v in tot.items():
        if k.startswith("QI=y|mono=n"):
            qi_only[k.split("|")[3]] += v
    OUT["H-K1"] = {"per_family": {f: dict(v) for f, v in per.items()}, "total": dict(tot),
                   "root_monotone_implies_exact": root_implies_exact, "yao_implies_exact": yao_implies_exact,
                   "qi_without_monotonicity_exact_vs_not": dict(qi_only)}
    rl = per["random_len"]
    OUT["H-K2"] = {"random_len": dict(rl),
                   "random_len_exact": sum(v for k, v in rl.items() if k.endswith("exact=y")),
                   "random_len_instances": sum(rl.values()),
                   "concave_len": dict(per["concave_len"])}
    print("H-K1", json.dumps({k: OUT["H-K1"][k] for k in ("total", "root_monotone_implies_exact", "yao_implies_exact",
                                                           "qi_without_monotonicity_exact_vs_not")}))
    print("H-K2", json.dumps(OUT["H-K2"]))


def h_g1():
    specs = greedy.generate(2, 400)
    rows = []
    for s in specs:
        c = greedy.build(s)
        an = c.predicates()
        worst = 1.0
        by_kind = defaultdict(lambda: [0, 0])
        rng = random.Random(f"H-G1|{c.id}")
        for t in range(200):
            g, w, _ = inst = c.instance(rng, 0)
            opt = c.slow(inst, Ops())
            gv = c.fast(inst, Ops())
            ratio = gv / opt if opt else 1.0
            worst = min(worst, ratio)
            kind = ("01" if max(w) <= 1 else "small" if max(w) <= 3 else "other")
            by_kind[kind][0] += 1
            by_kind[kind][1] += ratio == 1.0
        rows.append((an["matroid"], an["rank_quotient"], an["adversarial_ratio"], worst, dict(by_kind), s["family"]))
    nonm = [r for r in rows if not r[0]]
    res = {
        "systems": len(rows), "matroids": sum(r[0] for r in rows),
        "matroid_iff_rank_quotient_1": sum((r[0]) == (abs(r[1] - 1) < 1e-9) for r in rows),
        # q is stored rounded to 6 decimals (2/3 -> 0.666667), so compare with a 1e-6 margin; the first run of
        # this script used 1e-9 and reported 7 spurious "violations", all with q = 2/3 (a rounding artefact)
        "random_worst_ge_q_minus_1e-6": sum(r[3] >= r[1] - 1e-6 for r in rows),
        "random_worst_below_q_minus_1e-9_(rounding_artefacts)": sorted({r[1] for r in rows if r[3] < r[1] - 1e-9}),
        "adversarial_within_0.002_of_q": sum(abs(r[2] - r[1]) <= 0.002 for r in rows),
        "adversarial_minus_q_max": max(r[2] - r[1] for r in rows),
        "nonmatroids": len(nonm),
        "nonmatroids_detected_by_200_random_weights": sum(r[3] < 1 for r in nonm),
        "nonmatroids_random_worst_equals_q": sum(abs(r[3] - r[1]) < 1e-6 for r in nonm),
        "nonmatroid_rank_quotients": dict(Counter(round(r[1], 3) for r in nonm).most_common(8)),
        "undetected_nonmatroid_families": dict(Counter(r[5] for r in nonm if r[3] == 1.0)),
    }
    kinds = defaultdict(lambda: [0, 0])
    for r in nonm:
        for k, (a, b) in r[4].items():
            kinds[k][0] += a
            kinds[k][1] += b
    res["nonmatroid_exact_rate_by_weight_kind"] = {k: round(b / a, 4) for k, (a, b) in kinds.items()}
    OUT["H-G1"] = res
    print("H-G1", json.dumps(res))


def h_c1():
    specs = convolution.generate(2, 300)
    rows = []
    for s in specs:
        c = convolution.build(s)
        rng = random.Random(f"H-C1|{c.id}")
        agree, rep_ok = [], True
        cost_fast = cost_rep = cost_slow = 0
        for t in range(4):
            inst = c.instance(rng, c.N)
            o1, o2, o3 = Ops(), Ops(), Ops()
            a = c.slow(inst, o1)
            b = c.fast(inst, o2)
            r = c.fast_repaired(inst, o3)
            agree.append(sum(x == y for x, y in zip(a, b)) / c.N)
            rep_ok = rep_ok and r == a
            cost_slow, cost_fast, cost_rep = o1.n, o2.n, o3.n
        rows.append((s["family"], c.N, c.score_struct, sum(agree) / len(agree), rep_ok, len(c.D), cost_slow, cost_fast,
                     cost_rep))
    pert = [r for r in rows if r[0].startswith("perturbed")]
    nonstruct = [r for r in rows if r[2] < 1]

    def pearson(xs, ys):
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        sy = math.sqrt(sum((y - my) ** 2 for y in ys))
        return sxy / (sx * sy) if sx and sy else None
    res = {
        "tables": len(rows), "repaired_exact": sum(r[4] for r in rows),
        "non_structured": len(nonstruct),
        "pearson_table_score_vs_output_agreement_nonstructured": pearson([r[2] for r in nonstruct], [r[3] for r in nonstruct]),
        "perturbed": [{"t_mismatches": r[5], "table_score": round(r[2], 4), "output_agreement": round(r[3], 4),
                       "slow_ops": r[6], "repaired_ops": r[8]} for r in sorted(pert, key=lambda r: r[5])][:12],
        "repaired_cheaper_than_naive": sum(r[8] < r[6] for r in rows),
        "repaired_cheaper_than_naive_nonstructured": sum(r[8] < r[6] for r in nonstruct),
    }
    # threshold: largest |D| at which the repaired rule is still cheaper than naive, per N
    thr = {}
    for N in (4, 8, 16):
        k = N.bit_length() - 1
        for S in ("xor", "cyclic", "or"):
            o = Ops()
            convolution.ideal_conv(S, [1] * N, [1] * N, o)
            thr[f"{S}_N{N}"] = {"transform_ops": o.n, "naive_ops": 2 * N * N,
                                "max_mismatches_for_gain": max(0, (2 * N * N - o.n - 1) // 3)}
    res["repair_threshold"] = thr
    OUT["H-C1"] = res
    print("H-C1", json.dumps({k: v for k, v in res.items() if k != "perturbed"}))


def h_t1():
    specs = mitm.generate(2, 200)
    rows = []
    for s in specs:
        c = mitm.build(s)
        p = c.predicates()
        ok_plain = ok_all = ok_bnd = True
        for n in (8, 10, 12):
            for t in range(6):
                inst = c.instance(random.Random(f"H-T1|{c.id}|{n}|{t}"), n)
                a = c.slow(inst, Ops())
                ok_plain &= c.fast(inst, Ops()) == a
                ok_all &= c.fast_all(inst, Ops()) == a
                if s["family"].startswith("add") and s["family"] != "addsat":
                    ok_bnd &= c.fast_boundary(inst, Ops()) == a
        rows.append((s["family"], p["unique_completion"], p["group"], ok_plain, ok_all, ok_bnd))
    res = {
        "candidates": len(rows),
        "unique_completion_iff_plain_exact_(interaction_free)": sum(r[1] == r[3] for r in rows if not r[0].startswith("add_inter")),
        "interaction_free": sum(not r[0].startswith("add_inter") for r in rows),
        "all_solutions_exact_interaction_free": sum(r[4] for r in rows if not r[0].startswith("add_inter")),
        "boundary_exact_additive": sum(r[5] for r in rows if r[0].startswith("add") and r[0] != "addsat"),
        "additive": sum(r[0].startswith("add") and r[0] != "addsat" for r in rows),
        "plain_exact_by_family": {f: f"{sum(r[3] for r in rows if r[0] == f)}/{sum(r[0] == f for r in rows)}"
                                  for f in sorted({r[0] for r in rows})},
    }
    # cost of boundary conditioning vs |B| (n = 16, additive Z_31, crossing edges from the first |B| left items)
    costs = []
    c = mitm.build({"family": "add_inter", "M": 31, "density": 0.0})
    for bsize in range(0, 9):
        rng = random.Random(f"H-T1|B|{bsize}")
        n = 16
        vals = [rng.randrange(31) for _ in range(n)]
        edges = {(i, 8 + i) for i in range(bsize)}
        u = {e: rng.randrange(31) for e in edges}
        inst = (n, vals, rng.randrange(31), frozenset(edges), u)
        o_s, o_b = Ops(), Ops()
        a = c.slow(inst, o_s)
        b = c.fast_boundary(inst, o_b)
        costs.append({"B": bsize, "slow_ops": o_s.n, "boundary_ops": o_b.n, "exact": a == b})
    res["boundary_cost_vs_B_n16"] = costs
    OUT["H-T1"] = res
    print("H-T1", json.dumps(res))


def h_b1():
    specs = bilinear.generate(2, 400)
    by = defaultdict(lambda: [0, 0])
    repair_gain = 0
    nm = 0
    for s in specs:
        if s["family"] != "random":
            continue
        c = bilinear.build(s)
        if c.m <= 1:
            continue
        key = f"{'x'.join(map(str, c.fmt))}|d{s['density']}"
        by[key][0] += 1
        by[key][1] += c.r < c.m
        if c.r == c.m:
            nm += 1
            # repaired cost = (m - 1) + rank(residual); a gain would need this < m
            _, rank, _ = bilinear.rank_table(c.fmt)
            approx = 0
            for u, v, w in c.terms:
                for i in range(c.fmt[0]):
                    for j in range(c.fmt[1]):
                        for k in range(c.fmt[2]):
                            if u >> i & 1 and v >> j & 1 and w >> k & 1:
                                approx ^= bilinear.bit(*c.fmt, i, j, k)
            residual = approx ^ c.T
            repair_gain += (c.m - 1) + rank[residual] < c.m
    res = {"fraction_rank_below_support": {k: f"{b}/{a}" for k, (a, b) in sorted(by.items())},
           "rank_equals_support": nm, "repairs_with_gain": repair_gain}
    OUT["H-B1"] = res
    print("H-B1", json.dumps(res))


def h_r2():
    specs = [s for s in memo.generate(3, 1500) if s["family"] == "compress1d"]
    conf = Counter()
    for s in specs:
        c = memo.build(s)
        r = screen(c, do_scaling=False)
        pre = c.precondition()
        refined = pre or c.p_functional()
        conf[f"stated={'y' if pre else 'n'}|refined={'y' if refined else 'n'}|{r['verdict']}"] += 1
    OUT["H-R2"] = {"compress_candidates": len(specs), "confusion": dict(conf)}
    print("H-R2", json.dumps(OUT["H-R2"]))


def h_r1():
    specs = [s for s in memo.generate(2, 400) if s["family"] == "memo2d"]
    rows = []
    for s in specs:
        c = memo.build(s)
        if c.geometry()[0] != "interior" or c.degenerate():
            continue
        lam = memo.acsv_lambda(c.moves)
        lam2, rstar, corner = memo.growth_2d(c.moves)
        ratio = (c.spec_count(240) / c.spec_count(120)) ** (1 / 120)
        rows.append({"moves": s["moves"], "lambda_diagonal_only": round(lam, 6), "lambda_corrected": round(lam2, 6),
                     "r_star": round(rstar, 4), "at_corner": corner,
                     "lambda_dp_ratio_120_240": round(ratio, 6), "alpha_claim_n100_200": c.large_n_check()})
    uniq = {json.dumps(sorted(r["moves"])): r for r in rows}
    res = {"interior_move_sets": len(uniq),
           "max_rel_diff_diagonal_only_vs_dp": max(abs(r["lambda_diagonal_only"] / r["lambda_dp_ratio_120_240"] - 1)
                                                   for r in uniq.values()),
           "max_rel_diff_corrected_vs_dp": max(abs(r["lambda_corrected"] / r["lambda_dp_ratio_120_240"] - 1)
                                               for r in uniq.values()),
           "at_corner": sum(r["at_corner"] for r in uniq.values()),
           "alpha_range_n100_200": [min(r["alpha_claim_n100_200"] for r in uniq.values()),
                                    max(r["alpha_claim_n100_200"] for r in uniq.values())],
           "rows": list(uniq.values())}
    OUT["H-R1"] = res
    print("H-R1", json.dumps({k: v for k, v in res.items() if k != "rows"}))


def main() -> int:
    set_below_normal_priority()
    t0 = time.perf_counter()
    for f in (h_m1, h_k, h_g1, h_c1, h_t1, h_b1, h_r2, h_r1):
        t = time.perf_counter()
        f()
        print(f"  [{f.__name__}: {time.perf_counter() - t:.1f}s]", flush=True)
    OUT["wall_seconds"] = round(time.perf_counter() - t0, 1)
    for d in (REPO / "results" / "2026-10-06d", REPO / "candidates" / "2026-10-06d"):
        d.mkdir(parents=True, exist_ok=True)
        (d / "hypotheses.json").write_text(json.dumps(OUT, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print("wall", OUT["wall_seconds"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
