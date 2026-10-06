"""Analysis (research/2026-10-07b_search_formats.md): statistics of the 2026-10-07b Rust flip-graph runs and a
separate re-verification of every scheme they saved.

Reads (no search is run here; deterministic given the log files):
  search/runs/2026-10-07b_4x4_nocap.jsonl        24 uncapped 4x4x4 walks, seeds 101-124, 900 s each
  search/runs/2026-10-07_rust_4x4_nocap.jsonl    RL-054 job B (seeds 5-8, 1800 s), for comparison only
  search/runs/2026-10-07b_small_*.jsonl          ten small formats, seeds 1-8
  search/runs/2026-10-07b_4x4_from47_p*.jsonl    8 walks from the RL-054 rank-47 scheme, 120 s each
  search/schemes/rust-2026-10-07b/*.json         saved schemes (every walk's verified best)

Prints:
  * per 4x4 walk: best rank, time and step at which ranks 52..46 were first reached, throughput, counters;
  * counts of walks reaching <= 49, <= 48, <= 47 within 900 s, with exact (Clopper-Pearson) 95% intervals;
  * the scope of the rank-46 attempt (steps and seconds walked after a walk had reached 47);
  * per small format: best rank of each seed, first time/step at the best known rank, throughput;
  * re-verification of every saved scheme: verify, verify_explicit, 200 random GF(2) matrix pairs, and
    verify_over_integers (information only). A rank below the best known is flagged as a CANDIDATE that needs
    independent checks, never a discovery;
  * a cheap equivalence invariant for the rank-47 schemes: the multiset, over the 47 terms, of the sorted triple
    of GF(2) matrix ranks of the three factors. It is preserved by the symmetry group of matrix multiplication
    schemes (factors multiplied by invertible matrices, cyclic permutation and transposition of the three
    factors), so DIFFERENT invariants prove that two schemes are inequivalent; equal ones prove nothing.
    The published rank-47 schemes of Kauers & Moosbauer (github.com/jakobmoosbauer/flips,
    solutions/444-47-mod2.exp) and of AlphaTensor (github.com/google-deepmind/alphatensor,
    algorithms/factorizations_f2.npz) are downloaded and included for comparison (network; skipped if unavailable).

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-07b_analysis.py
RESULT: see research/2026-10-07b_search_formats.md (numbers are copied from this script's output).
"""
import collections
import glob
import importlib.util
import json
import math
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import gf2mm  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BEST_KNOWN_GF2 = {(2, 2, 3): 11, (2, 2, 4): 14, (2, 3, 3): 15, (2, 3, 4): 20, (2, 4, 4): 26, (3, 3, 4): 29,
                  (3, 3, 5): 36, (3, 4, 4): 38, (3, 4, 5): 47, (4, 4, 4): 47, (4, 4, 5): 60}
SAVE_DIR = ROOT / "search" / "schemes" / "rust-2026-10-07b"


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def first_reach(improvements, rank):
    for r, step, secs in improvements:
        if r <= rank:
            return step, secs
    return None


def binom_cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def clopper_pearson(k, n, alpha=0.05):
    """Exact two-sided (1 - alpha) interval for a binomial proportion k/n."""
    lower = 0.0 if k == 0 else _bisect_increasing(lambda p: 1 - binom_cdf(k - 1, n, p), alpha / 2)
    upper = 1.0 if k == n else _bisect_decreasing(lambda p: binom_cdf(k, n, p), alpha / 2)
    return lower, upper


def _bisect_increasing(f, target):  # smallest p with f(p) >= target, f increasing in p
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if f(mid) < target:
            lo = mid
        else:
            hi = mid
    return hi


def _bisect_decreasing(f, target):  # largest p with f(p) >= target, f decreasing in p
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if f(mid) >= target:
            lo = mid
        else:
            hi = mid
    return lo


def gf2_rank(mask, rows, cols):
    vecs = [(mask >> (r * cols)) & ((1 << cols) - 1) for r in range(rows)]
    rank = 0
    for bit in range(cols):
        piv = next((i for i in range(rank, rows) if (vecs[i] >> bit) & 1), None)
        if piv is None:
            continue
        vecs[rank], vecs[piv] = vecs[piv], vecs[rank]
        for i in range(rows):
            if i != rank and (vecs[i] >> bit) & 1:
                vecs[i] ^= vecs[rank]
        rank += 1
    return rank


def rank_profile(fmt, terms):
    n, m, p = fmt
    prof = collections.Counter(tuple(sorted((gf2_rank(a, n, m), gf2_rank(b, m, p), gf2_rank(c, p, n))))
                               for a, b, c in terms)
    return tuple(sorted(prof.items()))


def report_4x4():
    print("## 4x4x4, uncapped, from the standard algorithm (this run: seeds 101-124, 900 s per walk)")
    rows = load(ROOT / "search/runs/2026-10-07b_4x4_nocap.jsonl")
    old = load(ROOT / "search/runs/2026-10-07_rust_4x4_nocap.jsonl")
    for label, data in (("2026-10-07b", rows), ("RL-054 job B (1800 s, 12 processes on the machine)", old)):
        print(f"\n### {label}: {len(data)} walks")
        print("seed | best | first <=52 (s) | <=50 (s) | <=49 (s, step) | <=48 (s, step) | <=47 (s, step) | "
              "steps | seconds | steps/s | flips | plus | restarts")
        for d in data:
            imp, st = d.get("improvements", []), d.get("stats", {})
            f = {r: first_reach(imp, r) for r in (52, 50, 49, 48, 47, 46)}
            fmt_t = lambda x: "-" if x is None else f"{x[1]:.1f}"  # noqa: E731
            fmt_ts = lambda x: "-" if x is None else f"{x[1]:.1f}, {x[0]:.3e}"  # noqa: E731
            print(f"{d['seed']} | {d.get('best_rank')} | {fmt_t(f[52])} | {fmt_t(f[50])} | {fmt_ts(f[49])} | "
                  f"{fmt_ts(f[48])} | {fmt_ts(f[47])} | {st.get('steps', 0):.3e} | {st.get('seconds', 0):.1f} | "
                  f"{st.get('steps', 0) / max(st.get('seconds', 1), 1e-9):.3e} | {int(st.get('flips', 0))} | "
                  f"{int(st.get('plus', 0))} | {int(st.get('restarts', 0))}  verified={d.get('verified')}")
    n = len(rows)
    if not n:
        return
    print("\n### counts within 900 s (this run)")
    for r in (49, 48, 47, 46):
        hits = [first_reach(d.get("improvements", []), r) for d in rows]
        hits = [h for h in hits if h is not None and h[1] <= 900.0]
        lo, hi = clopper_pearson(len(hits), n)
        times = sorted(h[1] for h in hits)
        steps = sorted(h[0] for h in hits)
        med = f"median {statistics.median(times):.1f} s, {statistics.median(steps):.3e} steps" if hits else "-"
        print(f"rank <= {r}: {len(hits)}/{n} walks (95% CI {lo:.3f}-{hi:.3f}); times {[round(t, 1) for t in times]}; {med}")
    pooled = rows + old
    hits47 = [first_reach(d.get("improvements", []), 47) for d in pooled]
    hits47 = [h for h in hits47 if h is not None and h[1] <= 900.0]
    lo, hi = clopper_pearson(len(hits47), len(pooled))
    print(f"pooled with RL-054 job B (its walks truncated at 900 s): rank <= 47 in {len(hits47)}/{len(pooled)} "
          f"(95% CI {lo:.3f}-{hi:.3f})")
    # scope of the rank-46 attempt: steps/seconds after first reaching 47
    s46 = t46 = 0.0
    k46 = 0
    for d in pooled:
        h = first_reach(d.get("improvements", []), 47)
        if h is None:
            continue
        k46 += 1
        st = d.get("stats", {})
        s46 += st.get("steps", 0) - h[0]
        t46 += st.get("seconds", 0) - h[1]
    print(f"rank-46 attempt scope: {k46} walks at 47, {s46:.3e} steps and {t46:.0f} s walked after reaching 47 "
          f"(this run and RL-054 seed 8 combined)")
    rates = [d["stats"]["steps"] / d["stats"]["seconds"] for d in rows if d.get("stats")]
    print(f"throughput (this run): steps/s per walk min {min(rates):.3e}, median {statistics.median(rates):.3e}, "
          f"max {max(rates):.3e}; total steps {sum(d['stats']['steps'] for d in rows):.3e}")
    best = collections.Counter(d.get("best_rank") for d in rows)
    print(f"distribution of final best ranks (this run): {dict(sorted(best.items()))}")


def report_small():
    print("\n## Small formats, seeds 1-8, from the standard algorithm")
    print("format | best known GF(2) | budget s | best rank per seed | seeds at best known | "
          "first at best known: min/median/max s (steps) | steps/s median")
    for path in sorted(glob.glob(str(ROOT / "search/runs/2026-10-07b_small_*.jsonl"))):
        data = load(path)
        if not data:
            continue
        fmt = tuple(data[0]["format"])
        bk = BEST_KNOWN_GF2[fmt]
        bests = [d.get("best_rank") for d in sorted(data, key=lambda d: d["seed"])]
        hits = [first_reach(d.get("improvements", []), bk) for d in data]
        hits = [h for h in hits if h is not None]
        rates = [d["stats"]["steps"] / d["stats"]["seconds"] for d in data if d.get("stats")]
        if hits:
            ts = sorted(h[1] for h in hits)
            ss = sorted(h[0] for h in hits)
            hit_s = (f"{ts[0]:.3f}/{statistics.median(ts):.3f}/{ts[-1]:.3f} s "
                     f"({ss[0]:.2e}/{statistics.median(ss):.2e}/{ss[-1]:.2e})")
        else:
            hit_s = "-"
        print(f"{fmt} | {bk} | {data[0]['params']['max_seconds']:.0f} | {bests} | {len(hits)}/{len(data)} | "
              f"{hit_s} | {statistics.median(rates):.3e}   all verified={all(d.get('verified') for d in data)}")


def report_from47():
    print()
    print("## 4x4x4 from the RL-054 rank-47 scheme, target 46 (seeds 1-8, 120 s; plateau 50 000 or 5 000)")
    data = [d for path in sorted(glob.glob(str(ROOT / "search/runs/2026-10-07b_4x4_from47*.jsonl")))
            for d in load(path)]
    tot_steps = tot_secs = 0.0
    for d in sorted(data, key=lambda d: d["seed"]):
        st = d.get("stats", {})
        tot_steps += st.get("steps", 0)
        tot_secs += st.get("seconds", 0)
        print(f"seed {d['seed']} (plateau {d['params']['plateau']}): best {d.get('best_rank')}  "
              f"improvements {d.get('improvements')}  "
              f"steps {st.get('steps', 0):.3e}  seconds {st.get('seconds', 0):.1f}  "
              f"steps/s {st.get('steps', 0) / max(st.get('seconds', 1), 1e-9):.3e}  flips {int(st.get('flips', 0))}  "
              f"plus {int(st.get('plus', 0))}  restarts {int(st.get('restarts', 0))}  verified={d.get('verified')}")
    if data:
        print(f"total: {len(data)} walks, {tot_steps:.3e} steps, {tot_secs:.0f} walk-seconds")
    _, start, _ = gf2mm.load_scheme(ROOT / "search/schemes/rust-2026-10-07/4x4x4_rank47_seed8.json")
    for path in sorted(glob.glob(str(SAVE_DIR / "from47" / "*.json"))):
        _, terms, _ = gf2mm.load_scheme(path)
        print(f"{os.path.basename(path)}: rank {len(terms)}, identical to the start scheme: "
              f"{sorted(terms) == sorted(start)}")


def reverify_saved():
    print("\n## Separate re-verification of every saved scheme in search/schemes/rust-2026-10-07b/")
    out = {}
    for path in sorted(glob.glob(str(SAVE_DIR / "**" / "*.json"), recursive=True)):
        fmt, terms, doc = gf2mm.load_scheme(path)
        bk = BEST_KNOWN_GF2.get(fmt)
        v1 = gf2mm.verify(fmt, terms)
        v2 = gf2mm.verify_explicit(fmt, terms)
        rc = gf2mm.random_check(fmt, terms, trials=200, seed=20261007)
        vz = gf2mm.verify_over_integers(fmt, terms)
        flag = ""
        if bk is not None and len(terms) < bk:
            flag = "  <<< BELOW best known -- CANDIDATE, needs independent checks (not a discovery)"
        print(f"{os.path.relpath(path, SAVE_DIR)}: rank {len(terms)} (best known {bk}) status '{doc.get('status')}' | "
              f"verify {v1} | verify_explicit {v2} | 200 random checks {rc} | over Z (info) {vz}{flag}")
        out[os.path.relpath(path, SAVE_DIR)] = (fmt, terms)
    return out


def equivalence_invariants(saved):
    print("\n## Rank-47 4x4x4 schemes: factor-rank profile (invariant under the symmetry group)")
    schemes = {k: v for k, v in saved.items() if v[0] == (4, 4, 4) and len(v[1]) == 47
               and not k.startswith("from47")}  # from47/ rank-47 files are the unchanged start scheme
    old = ROOT / "search/schemes/rust-2026-10-07/4x4x4_rank47_seed8.json"
    if old.exists():
        f, t, _ = gf2mm.load_scheme(old)
        schemes["RL-054 seed 8 (rust-2026-10-07)"] = (f, t)
    try:
        spec = importlib.util.spec_from_file_location("src07b", ROOT / "experiments/2026-10-07b_sources.py")
        src = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(src)
        km = src.to_gf2((4, 4, 4), src.parse_scheme(src.get(src.FLIPS + "444-47-mod2.exp")), False)
        if gf2mm.verify((4, 4, 4), km):
            schemes["Kauers-Moosbauer 444-47-mod2 (published)"] = ((4, 4, 4), km)
        at = src.alphatensor_scheme("4,4,4")
        if gf2mm.verify((4, 4, 4), at):
            schemes["AlphaTensor factorizations_f2 4,4,4 (published)"] = ((4, 4, 4), at)
    except Exception as e:  # noqa: BLE001
        print(f"(published schemes not included: {e})")
    profiles = {}
    for name, (fmt, terms) in sorted(schemes.items()):
        prof = rank_profile(fmt, terms)
        profiles.setdefault(prof, []).append(name)
        print(f"{name}: {prof}")
    print(f"{len(schemes)} rank-47 schemes, {len(profiles)} distinct invariants (distinct => provably inequivalent)")
    for prof, names in profiles.items():
        if len(names) > 1:
            print(f"  same invariant (equivalence NOT decided): {names}")


def flip_pairs(terms):
    """Number of unordered term pairs that share at least one factor (the pairs a flip can act on)."""
    t = list(terms)
    return sum(1 for i in range(len(t)) for j in range(i + 1, len(t))
               if t[i][0] == t[j][0] or t[i][1] == t[j][1] or t[i][2] == t[j][2])


def plateau_diagnostics(saved):
    print("\n## Endpoints of the 4x4x4 walks: invariant vs Strassen (x) Strassen, and number of flippable pairs")
    s = gf2mm.strassen_scheme()
    ss = gf2mm.kron_scheme((2, 2, 2), s, (2, 2, 2), s)
    if isinstance(ss, tuple) and len(ss) == 2 and isinstance(ss[1], list):
        ss = ss[1]  # kron_scheme returns (format, terms)
    assert gf2mm.verify((4, 4, 4), ss) and len(ss) == 49
    ss_prof = rank_profile((4, 4, 4), ss)
    print(f"Strassen (x) Strassen: rank 49, invariant {ss_prof}, flippable pairs {flip_pairs(ss)}")
    rows = collections.Counter()
    for name, (fmt, terms) in sorted(saved.items()):
        if fmt != (4, 4, 4) or name.startswith("from47"):
            continue
        same = rank_profile(fmt, terms) == ss_prof
        rows[(len(terms), same)] += 1
        print(f"{name}: rank {len(terms)}, invariant equal to Strassen (x) Strassen's: {same}, "
              f"flippable pairs {flip_pairs(terms)}")
    print(f"summary (rank, invariant equals S(x)S): {dict(sorted(rows.items()))}")
    for label, path in (("RL-054 seed 8 (rank 47)", "search/schemes/rust-2026-10-07/4x4x4_rank47_seed8.json"),):
        f, t, _ = gf2mm.load_scheme(ROOT / path)
        print(f"{label}: flippable pairs {flip_pairs(t)}")


if __name__ == "__main__":
    report_4x4()
    report_small()
    report_from47()
    saved = reverify_saved()
    equivalence_invariants(saved)
    plateau_diagnostics(saved)
