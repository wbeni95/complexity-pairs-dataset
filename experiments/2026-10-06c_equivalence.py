"""Novelty audit, step 2 (research/2026-10-06c_novelty_audit.md): compare the project's own 4x4x4 rank-47 GF(2)
schemes with every published rank-47 scheme collected by experiments/2026-10-06c_collect.py.

Input:  <cache>/collected.json from 2026-10-06c_collect.py ($NOVELTY_CACHE, default <system temp>/cpd-2026-10-06c);
        every JSON file under search/schemes/ with format [4,4,4] and rank 47 (our schemes).
Method (search/equivalence.py; the group G = GL(4,2)^3 sandwiches x S3 x term permutations):
  1. re-verify our schemes (verify, verify_explicit) and group identical term sets;
  2. group the published schemes into identical term sets (exact duplicates);
  3. invariants, coarse to fine: factor-rank profile (RL-059), ordered factor-rank profile over S3, per-term
     label profile over S3, and (only where the cheaper ones coincide) Weisfeiler-Leman colour refinement with
     pair labels over S3. A difference in any of them PROVES inequivalence;
  4. for every published scheme that no invariant separates from one of ours, the exact test find_equivalence
     (complete search over the group, returns a checked certificate or proves that none exists);
  5. positive controls on real data: the exact test on the published pairs whose invariants coincide (e.g. the
     AlphaTensor scheme from two different sources), and on random group images of our scheme.
Prints a comparison table per source and a per-scheme summary; writes <cache>/equivalence_result.json.

Run from the repository root (after the collector):  ./.venv/Scripts/python experiments/2026-10-06c_equivalence.py
Deterministic: no randomness except the seeded positive-control group elements.

RESULT (run 2026-10-06, console copy search/runs/2026-10-06c_equivalence.console.txt): the 25 published term sets
form exactly 4 classes (AlphaTensor; Kauers-Moosbauer incl. arXiv:2210.04045; Zaru's FastMatrixF2; one file of
Kauers' directory). RL-054's scheme is EQUIVALENT to .../solutions/444/47/b0/jb050da4aa249f5a.exp (certificate
('cyc', P=49571, Q=65191, R=6073), re-checked independently). The five rank-47 schemes in
search/schemes/rust-2026-10-06c/ (another agent's run) are pairwise equivalent and inequivalent (factor-rank
profile) to RL-054 and to all four published classes. Details: research/2026-10-06c_novelty_audit.md, section 4.
"""
from __future__ import annotations

import glob
import json
import os
import random
import sys
import tempfile
import time
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import equivalence as eq  # noqa: E402
from search import gf2mm  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CACHE = Path(os.environ.get("NOVELTY_CACHE", Path(tempfile.gettempdir()) / "cpd-2026-10-06c"))
FMT = (4, 4, 4)
N = 4


def own_schemes():
    out = {}
    for path in sorted(glob.glob(str(ROOT / "search" / "schemes" / "**" / "*.json"), recursive=True)):
        try:
            fmt, terms, _ = gf2mm.load_scheme(path)
        except (KeyError, ValueError, json.JSONDecodeError):
            continue
        if fmt == FMT and len(terms) == 47:
            out[os.path.relpath(path, ROOT).replace("\\", "/")] = terms
    return out


def _m(x):
    """bitmask -> 4x4 list of lists (row r, column c = bit 4r+c); written without search/equivalence.py."""
    return [[(x >> (4 * r + c)) & 1 for c in range(4)] for r in range(4)]


def _b(M):
    return sum(M[r][c] << (4 * r + c) for r in range(4) for c in range(4))


def _mm(X, Y):
    return [[sum(X[r][t] * Y[t][c] for t in range(4)) % 2 for c in range(4)] for r in range(4)]


def _tp(X):
    return [[X[c][r] for c in range(4)] for r in range(4)]


def _inv_bruteforce(X):
    eye = [[int(r == c) for c in range(4)] for r in range(4)]
    for y in range(1 << 16):
        Y = _m(y)
        if _mm(X, Y) == eye:
            return Y
    return None


def independent_certificate_check(own_terms, pub_terms, cert):
    """Re-check an equivalence certificate (sigma, P, Q, R) with separately written arithmetic: matrices as lists,
    inverses by exhaustive search over all 2^16 matrices, sigma written out by hand. Also maps the standard
    algorithm with the same group element and verifies the result, which proves that this element fixes T."""
    name, P, Q, R = cert
    Pm, Qm, Rm = _m(P), _m(Q), _m(R)
    Pi, Qi, Ri = _inv_bruteforce(Pm), _inv_bruteforce(Qm), _inv_bruteforce(Rm)
    assert Pi and Qi and Ri, "certificate matrices must be invertible"
    sig = {"id": lambda a, b, c: (a, b, c), "cyc": lambda a, b, c: (b, c, a), "cyc2": lambda a, b, c: (c, a, b),
           "tr": lambda a, b, c: (_tp(c), _tp(b), _tp(a)), "tr.cyc": lambda a, b, c: (_tp(a), _tp(c), _tp(b)),
           "tr.cyc2": lambda a, b, c: (_tp(b), _tp(a), _tp(c))}[name]

    def g(terms):
        out = []
        for a, b, c in terms:
            a2, b2, c2 = sig(_m(a), _m(b), _m(c))
            out.append((_b(_mm(_mm(Pm, a2), Qi)), _b(_mm(_mm(Qm, b2), Ri)), _b(_mm(_mm(Rm, c2), Pi))))
        return out

    image_equal = Counter(g(own_terms)) == Counter(tuple(t) for t in pub_terms)
    std_image_valid = gf2mm.verify(FMT, g(gf2mm.standard_scheme(FMT)))
    own_valid = gf2mm.verify(FMT, own_terms) and gf2mm.verify_explicit(FMT, own_terms)
    pub_valid = gf2mm.verify(FMT, pub_terms) and gf2mm.verify_explicit(FMT, pub_terms)
    return {"image_equals_published_multiset": image_equal, "element_maps_standard_algorithm_to_valid_scheme":
            std_image_valid, "own_valid": own_valid, "published_valid": pub_valid,
            "P_rows": [format(_b([row] + [[0] * 4] * 3), "04b")[::-1] for row in Pm],
            "Q_rows": [format(_b([row] + [[0] * 4] * 3), "04b")[::-1] for row in Qm],
            "R_rows": [format(_b([row] + [[0] * 4] * 3), "04b")[::-1] for row in Rm]}


def ids_short(ids, k=3):
    """A long list of ids printed as its first k entries plus the total count."""
    ids = list(ids)
    return str(ids) if len(ids) <= k else f"{ids[:k]} + {len(ids) - k} more (total {len(ids)})"


def tier1(terms):
    return eq.invariants([tuple(t) for t in terms], N, wl=False)


def wl_inv(terms):
    return eq.s3_invariant([tuple(t) for t in terms], N, lambda s, nn: eq.wl_colours(s, nn)[1])


def short(inv_key):
    return {"factor_rank_profile": "I1 factor-rank profile", "ordered_rank_profile_S3": "I2 ordered rank profile/S3",
            "term_profile_S3": "I3 term-label profile/S3", "wl_S3": "I4 WL pair refinement/S3"}.get(inv_key, inv_key)


def main():
    t_start = time.time()
    collected = json.loads((CACHE / "collected.json").read_text(encoding="utf-8"))
    print(f"published schemes accepted by the collector: {len(collected)}")
    bad = [r["id"] for r in collected if not (r.get("verify") and r.get("verify_explicit"))]
    print(f"  of which failing verify or verify_explicit: {len(bad)} {bad[:5]}")
    pub = [r for r in collected if r.get("verify") and r.get("verify_explicit") and r["rank"] == 47]

    # ---- our schemes
    own = own_schemes()
    print(f"\nour 4x4x4 rank-47 files under search/schemes/: {len(own)}")
    own_groups = defaultdict(list)
    for name, terms in own.items():
        ok1, ok2 = gf2mm.verify(FMT, terms), gf2mm.verify_explicit(FMT, terms)
        print(f"  {name}: verify {ok1}, verify_explicit {ok2}")
        assert ok1 and ok2
        own_groups[eq.canonical_terms(terms)].append(name)
    print(f"  distinct term sets among our files: {len(own_groups)}")
    own_reps = {names[0]: list(ts) for ts, names in own_groups.items()}
    for ts, names in own_groups.items():
        print(f"    {names[0]} represents {len(names)} identical file(s)")

    # ---- published: exact duplicates
    groups = defaultdict(list)
    for r in pub:
        groups[eq.canonical_terms(map(tuple, r["terms"]))].append(r["id"])
    reps = [(ids[0], [list(t) for t in ts], ids) for ts, ids in groups.items()]
    reps.sort(key=lambda x: x[0])
    print(f"\npublished: {len(pub)} schemes, {len(reps)} distinct term sets")
    per_src = Counter(r["id"].split("/")[0] for r in pub)
    print(f"  per source (files): {dict(sorted(per_src.items()))}")
    cross = [ids for _, _, ids in reps if len({i.split('/')[0] for i in ids}) > 1]
    print(f"  term sets that occur in more than one source: {len(cross)}: {[ids_short(c) for c in cross]}")
    print("  distinct term sets with their number of files: " + "; ".join(
        f"{ids[0]}: {len(ids)}" for _, _, ids in sorted(reps, key=lambda x: -len(x[2]))))

    # ---- does any published term set equal one of ours?
    own_sets = set(own_groups)
    print(f"  published term sets identical to one of ours: "
          f"{sum(1 for _, ts, _ in reps if eq.canonical_terms(map(tuple, ts)) in own_sets)}")

    # ---- tier-1 invariants (parallel, 3 processes)
    t0 = time.time()
    with Pool(3) as pool:
        inv_pub = pool.map(tier1, [ts for _, ts, _ in reps], chunksize=32)
    inv_own = {k: tier1(v) for k, v in own_reps.items()}
    print(f"\ntier-1 invariants computed for {len(reps)} published + {len(own_reps)} own term sets "
          f"({time.time() - t0:.1f} s)")

    # distinct classes among the published schemes (a lower bound on the number of inequivalence classes)
    for key in ("factor_rank_profile", "ordered_rank_profile_S3", "term_profile_S3"):
        vals = Counter(json.dumps(i[key]) for i in inv_pub)
        print(f"  {short(key)}: {len(vals)} distinct values among {len(reps)} published term sets")

    # ---- comparison of each own scheme with each published term set
    result = {"own": {}, "published_count": len(pub), "published_distinct": len(reps)}
    for oname, oterms in own_reps.items():
        io = inv_own[oname]
        print(f"\n## {oname}")
        print(f"  factor-rank profile: {io['factor_rank_profile']}")
        decided = Counter()
        by_src = defaultdict(Counter)
        undistinguished = []
        for (rid, ts, ids), ip in zip(reps, inv_pub):
            k = eq.first_difference(io, ip)
            if k is None:
                undistinguished.append((rid, ts, ids))
                continue
            decided[k] += 1
            for i in ids:
                by_src[i.split("/")[0]][k] += 1
        print(f"  separated by tier-1 invariants: {sum(decided.values())} of {len(reps)} distinct published term "
              f"sets; coarsest separating invariant: " + ", ".join(f"{short(k)}: {v}" for k, v in sorted(decided.items())))
        for s, c in sorted(by_src.items()):
            print(f"    source {s}: " + ", ".join(f"{short(k)}: {v}" for k, v in sorted(c.items())))
        print(f"  not separated by tier-1 invariants: {len(undistinguished)}")
        exact = []
        if len(undistinguished) > 200:
            print(f"  (time box: exact tests only for the first 200 of {len(undistinguished)}; the rest stay "
                  f"UNDECIDED)")
        if undistinguished:
            wo = wl_inv(oterms)
            for rid, ts, ids in undistinguished[:200]:
                wp = wl_inv(ts)
                if wp != wo:
                    print(f"    {rid}: separated by {short('wl_S3')}")
                    exact.append((rid, "I4"))
                    continue
                t1 = time.time()
                cert = eq.find_equivalence([tuple(t) for t in oterms], [tuple(t) for t in ts], N)
                print(f"    {rid} (also {ids_short(ids[1:])}): exact test -> "
                      f"{'EQUIVALENT, certificate ' + str(cert) if cert else 'NOT equivalent (exhaustive search)'} "
                      f"({time.time() - t1:.1f} s)")
                entry = {"id": rid, "same_term_set_ids": ids, "result": "equivalent" if cert else "inequivalent"}
                if cert:
                    chk = independent_certificate_check([tuple(t) for t in oterms], [tuple(t) for t in ts], cert)
                    print(f"      independent re-check of the certificate: {chk}")
                    rec = next(r for r in pub if r["id"] == rid)
                    print(f"      published file: {rec['url']} (listed {rec.get('listed_date', '-')}, "
                          f"sha256 {rec['file_sha256']}); common terms with ours: "
                          f"{len(set(map(tuple, ts)) & set(map(tuple, oterms)))}")
                    entry.update({"certificate": list(cert), "recheck": chk, "url": rec["url"],
                                  "listed_date": rec.get("listed_date"), "file_sha256": rec["file_sha256"]})
                exact.append(entry)
        result["own"][oname] = {"separated_tier1": dict(decided), "by_source": {k: dict(v) for k, v in by_src.items()},
                                "undistinguished_tier1": [u[0] for u in undistinguished], "exact": exact}

    # ---- positive controls with real data
    print("\n## Positive controls on real data")
    # (a) random group images of our scheme are recognised as equivalent
    rng = random.Random(20261006)
    for oname, oterms in own_reps.items():
        for _ in range(3):
            imgs = eq.s3_images([tuple(t) for t in oterms], N)
            name = rng.choice(eq.S3_NAMES)
            P, Q, R = (eq.random_gl(N, rng) for _ in range(3))
            img = eq.apply_sandwich(imgs[name], P, Q, R, N)
            rng.shuffle(img)
            cert = eq.find_equivalence([tuple(t) for t in oterms], img, N)
            print(f"  {oname} vs a random image ({name}): certificate found: {cert is not None}; "
                  f"tier-1 invariants equal: {tier1(img) == inv_own[oname]}")
    # (b) published schemes whose tier-1 invariants coincide with another published scheme from a DIFFERENT source
    by_inv = defaultdict(list)
    for (rid, ts, ids), ip in zip(reps, inv_pub):
        by_inv[json.dumps(ip, sort_keys=True)].append((rid, ts, ids))
    multi = [v for v in by_inv.values() if len(v) > 1]
    print(f"  published tier-1 classes with more than one distinct term set: {len(multi)} "
          f"(sizes {sorted((len(v) for v in multi), reverse=True)[:15]})")
    named = [v for v in multi if any(not x[0].startswith("KW-") for x in v)]
    tested = 0
    for v in named + [v for v in multi if v not in named][:5]:
        a = v[0]
        for b in v[1:4]:
            t1 = time.time()
            cert = eq.find_equivalence([tuple(t) for t in a[1]], [tuple(t) for t in b[1]], N)
            print(f"  {a[0]} vs {b[0]}: {'EQUIVALENT ' + str(cert[0]) if cert else 'not equivalent'} "
                  f"({time.time() - t1:.1f} s)")
            tested += 1
    # the named published schemes against each other (AlphaTensor, KM github, KM note, FM, MMC)
    print("\n## Named published schemes against each other (identity, invariants, exact test where needed)")
    named_ids = [(rid, ts, ids) for rid, ts, ids in reps if any(not i.startswith("KW-") for i in ids)]
    for i in range(len(named_ids)):
        for j in range(i + 1, len(named_ids)):
            a, b = named_ids[i], named_ids[j]
            ia = inv_pub[reps.index(a)]
            ib = inv_pub[reps.index(b)]
            k = eq.first_difference(ia, ib)
            if k:
                print(f"  {ids_short(a[2])} vs {ids_short(b[2])}: inequivalent ({short(k)})")
            else:
                cert = eq.find_equivalence([tuple(t) for t in a[1]], [tuple(t) for t in b[1]], N)
                print(f"  {ids_short(a[2])} vs {ids_short(b[2])}: tier-1 equal; exact test: "
                      f"{'EQUIVALENT ' + str(cert) if cert else 'NOT equivalent'}")
    # which named schemes also occur (identically or equivalently) in the KW collection?
    print("\n## Named schemes inside the Kauers web collection")
    for rid, ts, ids in named_ids:
        same = [x for x in ids if x.startswith("KW-")]
        ia = inv_pub[reps.index((rid, ts, ids))]
        cands = [r for r, ip in zip(reps, inv_pub) if r[0].startswith("KW-") and r[0] != rid
                 and eq.first_difference(ia, ip) is None]
        eqv = []
        for c in cands[:20]:  # at most 20 exact tests per named scheme (time box)
            cert = eq.find_equivalence([tuple(t) for t in ts], [tuple(t) for t in c[1]], N)
            if cert:
                eqv.append(c[0])
        print(f"  {ids_short(ids)}: identical term set in KW: {ids_short(same)}; tier-1-equal KW sets: {len(cands)}; "
              f"exact tests run: {min(len(cands), 20)}; equivalent among them: {eqv}")
    # our own distinct schemes against each other
    print("\n## Our rank-47 term sets against each other")
    names = sorted(own_reps)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            k = eq.first_difference(inv_own[names[i]], inv_own[names[j]])
            if k:
                print(f"  {names[i]} vs {names[j]}: inequivalent ({short(k)})")
                continue
            cert = eq.find_equivalence(own_reps[names[i]], own_reps[names[j]], N)
            if cert:
                chk = independent_certificate_check(own_reps[names[i]], own_reps[names[j]], cert)
                ok = chk["image_equals_published_multiset"] and chk["element_maps_standard_algorithm_to_valid_scheme"]
                print(f"  {names[i]} vs {names[j]}: EQUIVALENT {cert} (independent re-check {ok})")
            else:
                print(f"  {names[i]} vs {names[j]}: tier-1 equal; exact test: NOT equivalent (exhaustive search)")
    (CACHE / "equivalence_result.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"\nwrote {CACHE / 'equivalence_result.json'}; total {time.time() - t_start:.1f} s")


if __name__ == "__main__":
    main()
