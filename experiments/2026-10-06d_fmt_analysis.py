#!/usr/bin/env python3
"""Analysis (research/2026-10-06d_exotic_formats.md, sections 4-6): numbers from the round's logs, and a separate
re-verification of every saved scheme.

Reads search/runs/2026-10-06d_cal_*.jsonl, 2026-10-06d_tgt_*.jsonl and 2026-10-06d_library.jsonl. Prints per arm:
walks, best ranks, how many reached <= record and <= record + 1 (exact 95% Clopper-Pearson intervals), the first time
each walk reached those ranks, total steps / flips / walk-seconds, median steps/s and flips/s, and the
linear-dependence reductions. Then re-verifies every file in search/schemes/rust-2026-10-06d/ with gf2mm.verify,
gf2mm.verify_explicit, 200 random GF(2) matrix checks (seed 20261006) and, for information, verify_over_integers.
Also checks that the rank-48 (3,4,5) endpoints are pairwise inequivalent by the factor-rank profile (the format has
three different dimensions, so its symmetry group is GL(3,2) x GL(4,2) x GL(5,2) acting by sandwiches together with
term permutations, which preserve each factor's rank).

Run from the repository root: ./.venv/Scripts/python experiments/2026-10-06d_fmt_analysis.py
RESULT: printed; console copy search/runs/2026-10-06d_analysis.console.txt.
"""
import collections
import glob
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import gf2mm  # noqa: E402
from search.campaign import clopper_pearson  # noqa: E402

RECORD = {(3, 4, 5): 47, (4, 4, 5): 60, (2, 4, 5): 33, (3, 3, 6): 42, (2, 5, 6): 47}


def first_time(walk, rank):
    ts = [(t, st) for r, st, t in walk.get("improvements", []) if r <= rank]
    return min(ts) if ts else None


def arm_table(path):
    walks = [json.loads(line) for line in open(path, encoding="utf-8")]
    arms = collections.OrderedDict()
    for w in walks:
        arms.setdefault((w["arm"], tuple(w["format"])), []).append(w)
    for (arm, fmt), ws in arms.items():
        rec = RECORD.get(fmt, ws[0].get("best_known"))
        ranks = [w["best_rank"] for w in ws]
        line = [f"{'x'.join(map(str, fmt))} {arm}: {len(ws)} walks, start rank {ws[0]['start_rank']} ({ws[0]['start'][:60]})"]
        line.append(f"   best ranks {ranks}")
        for target in (rec - 1, rec, rec + 1):
            k = sum(1 for r in ranks if r <= target)
            lo, hi = clopper_pearson(k, len(ranks))
            times = sorted(round(first_time(w, target)[0], 1) for w in ws if first_time(w, target))
            line.append(f"   <= {target}: {k}/{len(ranks)} (95% CI {lo:.3f}-{hi:.3f}); first reached (s) {times}")
        st = [w["stats"] for w in ws]
        secs = [s["seconds"] for s in st]
        line.append(f"   steps {sum(s['steps'] for s in st):.4g}, flips {sum(s['flips'] for s in st):.4g}, "
                    f"walk-seconds {sum(secs):.0f}; median steps/s {statistics.median(s['steps'] / s['seconds'] for s in st):.3g}, "
                    f"median flips/s {statistics.median(s['flips'] / s['seconds'] for s in st):.3g}; "
                    f"plus {sum(s['plus'] for s in st):.0f}, restarts {sum(s['restarts'] for s in st):.0f}, "
                    f"dead ends {sum(s['dead_ends'] for s in st):.0f}, dep_reductions {sum(s.get('dep_reductions', 0) for s in st):.0f}; "
                    f"window {ws[0]['window'][0]}-{ws[-1]['window'][1]}; kernel {ws[0]['environment']['kernel_sha256'][:8]}")
        print("\n".join(line))


def rank_gf2(x, rows, cols):
    basis = []
    for r in range(rows):
        v = (x >> (r * cols)) & ((1 << cols) - 1)
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def fisher_two_sided(a, b, c, d):
    """Exact two-sided Fisher test for [[a, b], [c, d]]: sum of the hypergeometric probabilities <= the observed one."""
    import math
    n1, n2, k = a + b, c + d, a + c
    def prob(x):
        return math.comb(n1, x) * math.comb(n2, k - x) / math.comb(n1 + n2, k)
    p_obs = prob(a)
    return sum(prob(x) for x in range(max(0, k - n2), min(k, n1) + 1) if prob(x) <= p_obs * (1 + 1e-9))


def calibration_contrasts():
    walks = [json.loads(line) for line in open(ROOT / "search" / "runs" / "2026-10-06d_cal_3x4x5.jsonl", encoding="utf-8")]
    blk = [w["best_rank"] for w in walks if w["arm"].startswith("blk")]
    std = [w["best_rank"] for w in walks if w["arm"].startswith("std")]
    a, c = sum(r <= 48 for r in blk), sum(r <= 48 for r in std)
    print(f"\n## (3,4,5): reached <= 48, block starts {a}/{len(blk)} vs standard starts {c}/{len(std)}; two-sided Fisher "
          f"p = {fisher_two_sided(a, len(blk) - a, c, len(std) - c):.2g}")
    med = {}
    for w in walks:
        med.setdefault(w["arm"], []).append(w["stats"]["steps"] / w["stats"]["seconds"])
    med = {k: statistics.median(v) for k, v in med.items()}
    for arm in ("std_full", "std_full_v2", "blk_full", "blk_full_v2"):
        base = med["std_off" if arm.startswith("std") else "blk_off"]
        print(f"   median steps/s {arm} / {'std_off' if arm.startswith('std') else 'blk_off'} = {med[arm] / base:.2f}")
    w445 = [json.loads(line) for line in open(ROOT / "search" / "runs" / "2026-10-06d_cal_4x4x5.jsonl", encoding="utf-8")]
    m = {}
    for w in w445:
        m.setdefault(w["arm"], []).append(w["stats"]["steps"] / w["stats"]["seconds"])
    print(f"   (4,4,5) median steps/s blk_full / blk_off = "
          f"{statistics.median(m['blk_full']) / statistics.median(m['blk_off']):.2f}")


def main():
    for path in sorted(glob.glob(str(ROOT / "search" / "runs" / "2026-10-06d_*.jsonl"))):
        print(f"\n## {Path(path).name}")
        arm_table(path)
    calibration_contrasts()
    print("\n## Re-verification of every saved scheme (search/schemes/rust-2026-10-06d/)")
    files = sorted(glob.glob(str(ROOT / "search" / "schemes" / "rust-2026-10-06d" / "**" / "*.json"), recursive=True))
    ok = 0
    below = []
    z_valid = 0
    for f in files:
        fmt, terms, doc = gf2mm.load_scheme(f)
        good = gf2mm.verify(fmt, terms) and gf2mm.verify_explicit(fmt, terms) and \
            gf2mm.random_check(fmt, terms, trials=200, seed=20261006)
        ok += good
        z_valid += gf2mm.verify_over_integers(fmt, terms)
        rec = RECORD.get(tuple(fmt))
        if rec is not None and len(terms) < rec and "start" not in Path(f).name:
            below.append(Path(f).name)
        if not good:
            print(f"   FAILED: {f}")
    print(f"   {ok}/{len(files)} pass verify, verify_explicit and 200 random checks; valid over Z as they stand: "
          f"{z_valid}; below the record: {below if below else 'none'}")
    # Factor-rank profiles: the multiset of sorted (rank a, rank b, rank c) triples is invariant under sandwiches, term
    # permutations and the format-preserving transpositions, so different profiles prove inequivalence.
    for pattern in ("cal/3x4x5_rank48_*.json", "targets/3x3x6_rank43_*.json", "cal/4x4x5_rank60_*.json",
                    "targets/4x4x5_rank60_*.json", "targets/2x5x6_rank47_*.json", "targets/2x4x5_rank33_*.json"):
        profs = {}
        for f in sorted(glob.glob(str(ROOT / "search" / "schemes" / "rust-2026-10-06d" / pattern))):
            fmt, terms, _ = gf2mm.load_scheme(f)
            n, m, p = fmt
            profs[Path(f).name] = tuple(sorted(collections.Counter(
                tuple(sorted((rank_gf2(a, n, m), rank_gf2(b, m, p), rank_gf2(c, p, n)))) for a, b, c in terms).items()))
        if profs:
            print(f"\n## {pattern}: {len(profs)} files, {len(set(profs.values()))} distinct factor-rank profiles "
                  f"(distinct profile => inequivalent)")
    # All rank-60 (4,4,5) schemes of the round together with Kauers-Moosbauer's published 445-60-mod2 (needs the cache
    # of 2026-10-06d_fmt_records.py, $FMT_CACHE; skipped if it cannot be read).
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("tgt", ROOT / "experiments" / "2026-10-06d_fmt_targets.py")
        tgt = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tgt)
        km, _ = tgt.published_start(tgt.PLANS["445"])
        def prof(ts):
            return tuple(sorted(collections.Counter(tuple(sorted((rank_gf2(a, 4, 4), rank_gf2(b, 4, 5), rank_gf2(c, 5, 4))))
                                                    for a, b, c in ts).items()))
        P = {"KM 445-60-mod2": prof(km)}
        for f in sorted(glob.glob(str(ROOT / "search" / "schemes" / "rust-2026-10-06d" / "*" / "4x4x5_rank60_*.json"))):
            P[Path(f).name] = prof(gf2mm.load_scheme(f)[1])
        print(f"\n## all (4,4,5) rank-60 schemes of this round + KM's published file: {len(P)} schemes, "
              f"{len(set(P.values()))} distinct factor-rank profiles; {sorted(P)}")
    except Exception as e:  # noqa: BLE001
        print(f"\n## KM comparison skipped ({e})")


if __name__ == "__main__":
    main()
