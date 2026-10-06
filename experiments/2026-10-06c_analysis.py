"""Analysis (research/2026-10-06c_kernel_deadends.md): statistics of the 2026-10-06c runs of the Rust flip-graph kernel
with dead-end escape, the comparison with the RL-059 baseline, and a separate re-verification of every saved scheme.

Reads (no search is run here; deterministic given the files):
  search/runs/2026-10-06c_throughput.jsonl     throughput benchmark (experiments/2026-10-06c_kernel_throughput.py)
  search/runs/2026-10-06c_4x4_deadend.jsonl    24 uncapped 4x4x4 walks with dead-end escape, seeds 601-624, 900 s
  search/runs/2026-10-07b_4x4_nocap.jsonl      RL-059 baseline: 24 walks without it, seeds 101-124, 900 s
  search/runs/2026-10-07_rust_4x4_nocap.jsonl  RL-054 job B (seeds 5-8, 1800 s), truncated at 900 s for pooling
  search/schemes/rust-2026-10-06c/*.json       saved schemes of this round (every walk's verified best)

Prints:
  * throughput per start and kernel (median and range over 8 walks of steps/s, flips/s, plus transitions/s,
    dead-end detections/s);
  * per 4x4 walk of this round: final rank, first time and step at ranks <= 52, 50, 49, 48, 47, counters;
  * counts of walks reaching <= 49, <= 48, <= 47 within 900 s, for this round and the baseline, with exact
    (Clopper-Pearson) 95% intervals and two-sided Fisher exact p-values for the difference;
  * time to rank 49: every value, medians, and a Mann-Whitney rank-sum comparison (walks that never reached 49 are
    ranked last, as ties; normal approximation with tie correction, so the p-value is approximate);
  * endpoint diagnostics: number of term pairs sharing a factor (0 = no flip possible) and whether the factor-rank
    invariant equals that of Strassen (x) Strassen;
  * re-verification of every saved scheme: verify, verify_explicit, 200 random GF(2) matrix pairs, and
    verify_over_integers (information only). A rank below the best known (47) is flagged as a CANDIDATE that
    needs independent checks, never a discovery.

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-06c_analysis.py
RESULT: see research/2026-10-06c_kernel_deadends.md (numbers are copied from this script's output).
"""
import collections
import glob
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

BEST_KNOWN_4X4_GF2 = 47
SAVE_DIR = ROOT / "search" / "schemes" / "rust-2026-10-06c"
BUDGET = 900.0


def load(path):
    path = ROOT / path
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def binom_cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def clopper_pearson(k, n, alpha=0.05):
    def bisect(f, target, increasing):
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2
            if (f(mid) >= target) == increasing:
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2
    lower = 0.0 if k == 0 else bisect(lambda p: 1 - binom_cdf(k - 1, n, p), alpha / 2, True)
    upper = 1.0 if k == n else bisect(lambda p: binom_cdf(k, n, p), alpha / 2, False)
    return lower, upper


def fisher_two_sided(k1, n1, k2, n2):
    """Two-sided Fisher exact test for a 2x2 table (sum of probabilities <= that of the observed table)."""
    K, N = k1 + k2, n1 + n2

    def prob(x):
        return math.comb(n1, x) * math.comb(n2, K - x) / math.comb(N, K)
    obs = prob(k1)
    return min(1.0, sum(prob(x) for x in range(max(0, K - n2), min(K, n1) + 1) if prob(x) <= obs * (1 + 1e-9)))


def mann_whitney(x, y):
    """U statistic of x versus y and a two-sided p-value from the normal approximation with tie correction."""
    allv = sorted((v, g) for g, vs in ((0, x), (1, y)) for v in vs)
    ranks, i = {}, 0
    vals = [v for v, _ in allv]
    rank_of = []
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[j + 1] == vals[i]:
            j += 1
        rank_of.extend([(i + j) / 2 + 1] * (j - i + 1))
        i = j + 1
    r1 = sum(r for r, (_, g) in zip(rank_of, allv) if g == 0)
    n1, n2 = len(x), len(y)
    u1 = r1 - n1 * (n1 + 1) / 2
    ties = collections.Counter(vals)
    n = n1 + n2
    var = n1 * n2 / 12 * ((n + 1) - sum(t ** 3 - t for t in ties.values()) / (n * (n - 1)))
    z = (u1 - n1 * n2 / 2) / math.sqrt(var) if var > 0 else 0.0
    p = math.erfc(abs(z) / math.sqrt(2))
    return u1, z, p


def first_reach(improvements, rank):
    for r, step, secs in improvements:
        if r <= rank:
            return step, secs
    return None


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


def flip_pairs(terms):
    t = list(terms)
    return sum(1 for i in range(len(t)) for j in range(i + 1, len(t))
               if t[i][0] == t[j][0] or t[i][1] == t[j][1] or t[i][2] == t[j][2])


def fmt_rng(vals):
    return f"{statistics.median(vals):.3e} ({min(vals):.3e}-{max(vals):.3e})"


def report_throughput():
    rows = load("search/runs/2026-10-06c_throughput.jsonl")
    print("## Throughput (experiments/2026-10-06c_kernel_throughput.py; 8 walks at once, seeds 701-708)")
    print("median (min-max) over the 8 walks")
    groups = collections.defaultdict(list)
    for r in rows:
        groups[(r["start"], r["kernel"], r["max_seconds"])].append(r)
    for (start, kernel, secs), rs in groups.items():
        print(f"{start:17s} {kernel:6s} {secs:.0f} s: steps/s {fmt_rng([r['steps_per_s'] for r in rs])} | "
              f"flips/s {fmt_rng([r['flips_per_s'] for r in rs])} | plus/s {fmt_rng([r['plus_per_s'] for r in rs])} | "
              f"dead-ends/s {fmt_rng([r['dead_ends_per_s'] for r in rs])} | "
              f"flips/step {statistics.median(r['stats']['flips'] / r['stats']['steps'] for r in rs):.4f} | "
              f"best {sorted(r['best_rank'] for r in rs)} | first 49 (s) "
              f"{[None if r['first_49_seconds'] is None else round(r['first_49_seconds'], 1) for r in rs]}")


def per_walk_table(label, rows):
    print(f"\n## {label}: per walk")
    print("seed | final | <=52 s | <=50 s | <=49 s; step | <=48 s; step | <=47 s; step | steps | steps/s | flips | "
          "plus | restarts | dead_ends | wall s | verified")
    for d in sorted(rows, key=lambda e: e["seed"]):
        st = d.get("stats") or {}
        imp = d.get("improvements", [])
        cells = []
        for r in (52, 50):
            fr = first_reach(imp, r)
            cells.append("-" if fr is None else f"{fr[1]:.1f}")
        for r in (49, 48, 47):
            fr = first_reach(imp, r)
            cells.append("-" if fr is None else f"{fr[1]:.1f}; {fr[0]:.3e}")
        print(f"{d['seed']} | {d.get('best_rank')} | " + " | ".join(cells) +
              f" | {st.get('steps', 0):.4e} | {st.get('steps', 0) / st['seconds']:.3e} | {int(st.get('flips', 0))} | "
              f"{int(st.get('plus', 0))} | {int(st.get('restarts', 0))} | {int(st.get('dead_ends', 0))} | "
              f"{d.get('wall_seconds')} | {d.get('verified')}")


def counts(rows, rank, budget=BUDGET):
    return sum(1 for d in rows if (fr := first_reach(d.get("improvements", []), rank)) and fr[1] <= budget)


def times_to(rows, rank):
    out = []
    for d in rows:
        fr = first_reach(d.get("improvements", []), rank)
        out.append(None if fr is None or fr[1] > BUDGET else fr[1])
    return out


def report_comparison(new, base, rl054):
    print("\n## Comparison with the RL-059 baseline (within 900 s per walk)")
    for rank in (49, 48, 47):
        kn, nn = counts(new, rank), len(new)
        kb, nb = counts(base, rank), len(base)
        lo_n, hi_n = clopper_pearson(kn, nn)
        lo_b, hi_b = clopper_pearson(kb, nb)
        print(f"rank <= {rank}: this round {kn}/{nn} (95% CI {lo_n:.3f}-{hi_n:.3f}) | baseline {kb}/{nb} "
              f"(95% CI {lo_b:.3f}-{hi_b:.3f}) | Fisher two-sided p = {fisher_two_sided(kn, nn, kb, nb):.4f}")
    kp = counts(base, 47) + counts(rl054, 47)
    npool = len(base) + len(rl054)
    lo, hi = clopper_pearson(kp, npool)
    kn = counts(new, 47)
    print(f"rank <= 47, baseline pooled with RL-054 job B truncated at 900 s: {kp}/{npool} (95% CI {lo:.3f}-{hi:.3f}) | "
          f"this round {kn}/{len(new)} | Fisher two-sided p = {fisher_two_sided(kn, len(new), kp, npool):.4f}")
    kpool48 = counts(base, 48) + counts(rl054, 48)
    print(f"rank <= 48, pooled baseline: {kpool48}/{npool} (95% CI "
          f"{clopper_pearson(kpool48, npool)[0]:.3f}-{clopper_pearson(kpool48, npool)[1]:.3f})")
    kall47 = counts(new, 47) + kp
    print(f"rank <= 47, all three runs pooled (old and new kernel mixed, information only): {kall47}/{len(new) + npool}")
    tn, tb = times_to(new, 49), times_to(base, 49)
    rn = sorted(t for t in tn if t is not None)
    rb = sorted(t for t in tb if t is not None)
    print(f"\ntime to rank <= 49 (s), this round ({len(rn)}/{len(tn)} reached it): {[round(t, 1) for t in rn]}")
    print(f"  median over walks that reached it {statistics.median(rn) if rn else None}; "
          f"median over all walks (never = 900+) {statistics.median([t if t is not None else math.inf for t in tn])}")
    print(f"time to rank <= 49 (s), baseline ({len(rb)}/{len(tb)}): {[round(t, 1) for t in rb]}")
    print(f"  median over walks that reached it {statistics.median(rb) if rb else None}; "
          f"median over all walks (never = 900+) {statistics.median([t if t is not None else math.inf for t in tb])}")
    big = 10 * BUDGET
    u, z, p = mann_whitney([t if t is not None else big for t in tn], [t if t is not None else big for t in tb])
    print(f"Mann-Whitney (never reached = tied last): U(this round vs baseline) = {u:.1f} of {len(tn) * len(tb)}, "
          f"z = {z:.2f}, two-sided p ~= {p:.3f} (normal approximation)")
    for label, rows in (("this round", new), ("baseline", base)):
        steps = sum(d["stats"]["steps"] for d in rows)
        flips = sum(d["stats"]["flips"] for d in rows)
        plus = sum(d["stats"]["plus"] for d in rows)
        secs = sum(d["stats"]["seconds"] for d in rows)
        de = sum(d["stats"].get("dead_ends", 0) for d in rows)
        print(f"{label}: {len(rows)} walks, {steps:.4e} steps, {flips:.4e} flips, {plus:.4e} plus transitions, "
              f"{de:.4e} dead-end detections, {secs:.0f} walk-seconds; final ranks "
              f"{dict(sorted(collections.Counter(d.get('best_rank') for d in rows).items()))}")


def report_dead_end_phase(new, base):
    """Where did the rank-47 walks come from, and what happened to walks that sat at a rank-49 dead end?"""
    print("\n## Paths to 47 and the rank-49 dead-end phase")
    for label, rows in (("this round", new), ("baseline", base)):
        direct, sat = [], []
        for d in rows:
            imp = d.get("improvements", [])
            f49, f47 = first_reach(imp, 49), first_reach(imp, 47)
            if f47 is not None:
                direct.append((d["seed"], f49[0], f47[0], f47[0] - f49[0]))
            elif d.get("best_rank") == 49:
                sat.append(d)
        print(f"{label}: walks reaching 47: {len(direct)}; (seed, step first <= 49, step first 47, difference): {direct}")
        if sat:
            plus = sum(d["stats"]["plus"] for d in sat)
            de = sum(d["stats"].get("dead_ends", 0) for d in sat)
            secs = sum(BUDGET - first_reach(d["improvements"], 49)[1] for d in sat)
            print(f"  walks that ended at 49 (sat at 49 after reaching it): {len(sat)}, none improved; time at 49 in total "
                  f"{secs:.0f} s; plus transitions in those walks {plus:.4e}; dead-end detections {de:.4e}")
    after = [(d["seed"], d["stats"]["steps"] - first_reach(d["improvements"], 47)[0],
              d["stats"]["seconds"] - first_reach(d["improvements"], 47)[1]) for d in new
             if first_reach(d.get("improvements", []), 47)]
    if after:
        print(f"rank-46 attempt scope (walking after reaching 47, escape on): (seed, steps, seconds) {after}; total "
              f"{sum(a[1] for a in after):.4e} steps, {sum(a[2] for a in after):.1f} s")
    zero = [d["seed"] for d in new if d["stats"].get("dead_ends", 0) == 0]
    print(f"this round, walks with no dead end at all in 900 s (trajectory identical to the old kernel's): {len(zero)} "
          f"{zero}; their final ranks {sorted(d['best_rank'] for d in new if d['seed'] in zero)}")


def reverify_and_diagnose():
    print(f"\n## Separate re-verification of every saved scheme in {os.path.relpath(SAVE_DIR, ROOT)}")
    s = gf2mm.strassen_scheme()
    _, ss = gf2mm.kron_scheme((2, 2, 2), s, (2, 2, 2), s)
    ss_prof = rank_profile((4, 4, 4), ss)
    summary = collections.Counter()
    for path in sorted(glob.glob(str(SAVE_DIR / "*.json"))):
        fmt, terms, doc = gf2mm.load_scheme(path)
        v1 = gf2mm.verify(fmt, terms)
        v2 = gf2mm.verify_explicit(fmt, terms)
        rc = gf2mm.random_check(fmt, terms, trials=200, seed=20261006)
        vz = gf2mm.verify_over_integers(fmt, terms)
        fp = flip_pairs(terms)
        same = rank_profile(fmt, terms) == ss_prof
        summary[(len(terms), fp == 0, same)] += 1
        flag = ""
        if len(terms) < BEST_KNOWN_4X4_GF2:
            flag = "  <<< BELOW best known 47 -- CANDIDATE, needs independent checks (not a discovery)"
        print(f"{os.path.basename(path)}: rank {len(terms)} status '{doc.get('status')}' | verify {v1} | "
              f"verify_explicit {v2} | 200 random checks {rc} | over Z (info) {vz} | pairs sharing a factor {fp} | "
              f"invariant = S(x)S {same}{flag}")
    print(f"summary (rank, no flip possible, invariant equals S(x)S): {dict(sorted(summary.items()))}")


def rank47_invariants():
    """Factor-rank profiles of every rank-47 scheme saved this round, RL-054's, and the published AlphaTensor and
    Kauers-Moosbauer ones (downloaded with the loader of experiments/2026-10-07b_sources.py; skipped offline).
    Different profiles prove inequivalence; equal ones decide nothing."""
    import importlib.util
    schemes = {}
    for path in sorted(glob.glob(str(SAVE_DIR / "*.json"))):
        fmt, terms, _ = gf2mm.load_scheme(path)
        if len(terms) <= 47:
            schemes[os.path.basename(path)] = (fmt, terms)
    if not schemes:
        print("\n## Rank-47 invariants: no rank <= 47 scheme saved this round")
        return
    print("\n## Rank <= 47 schemes: factor-rank profile (invariant under the symmetry group)")
    f, t, _ = gf2mm.load_scheme(ROOT / "search/schemes/rust-2026-10-07/4x4x4_rank47_seed8.json")
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
        print(f"{name}: rank {len(terms)}, pairs sharing a factor {flip_pairs(terms)}, profile {prof}")
    print(f"{len(schemes)} schemes, {len(profiles)} distinct invariants (distinct => provably inequivalent)")
    for prof, names in profiles.items():
        if len(names) > 1:
            print(f"  same invariant (equivalence NOT decided): {names}")


def detection_latency(r=49):
    """Expected cost of detecting a dead end of rank r once the walk is in it (every candidate search fails and
    marks a uniformly random cell among n = 3r). Pure stamping: n*H_n steps (coupon collector). With the completion
    sweep at r distinct cells: n*(H_n - H_{n-r}) steps to collect r distinct cells, then n - r scans of r terms each,
    i.e. about n - r step-equivalents (a step also scans r terms)."""
    n = 3 * r
    h = lambda k: sum(1.0 / i for i in range(1, k + 1))  # noqa: E731
    pure = n * h(n)
    collect = n * (h(n) - h(n - r))
    print(f"\n## Detection latency at a rank-{r} dead end (expected, analytic)")
    print(f"stamping only: {pure:.1f} steps | with the sweep: {collect:.1f} steps + {n - r} scans = "
          f"{collect + n - r:.1f} step-equivalents | plateau of the old kernel: 50000 steps")


def sample_size(p1=1 / 28, p2=4 / 24, z_a=1.959964, z_b=0.841621):
    """Walks per arm to detect p1 -> p2 (two-sided alpha 0.05, power 0.8), normal approximation for two proportions."""
    pb = (p1 + p2) / 2
    n = (z_a * math.sqrt(2 * pb * (1 - pb)) + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / (p1 - p2) ** 2
    print(f"\n## Planning: walks per arm to detect {p1:.4f} -> {p2:.4f} (alpha 0.05 two-sided, power 0.8, normal "
          f"approximation): {math.ceil(n)}")


if __name__ == "__main__":
    detection_latency()
    sample_size()
    report_throughput()
    new = load("search/runs/2026-10-06c_4x4_deadend.jsonl")
    base = load("search/runs/2026-10-07b_4x4_nocap.jsonl")
    rl054 = load("search/runs/2026-10-07_rust_4x4_nocap.jsonl")
    if new:
        per_walk_table("4x4x4 with dead-end escape (seeds 601-624, 900 s)", new)
        report_comparison(new, base, rl054)
        report_dead_end_phase(new, base)
        reverify_and_diagnose()
        rank47_invariants()
    else:
        print("\nno log of the main run yet")
