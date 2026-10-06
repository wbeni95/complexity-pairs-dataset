"""Boundary map and property correlation for the 2026-10-06d mutation pilot (reads the records, computes nothing new).

Input:  mutations/records/2026-10-06d/*.jsonl (one record per mutant) and properties.jsonl (mechanical property table).
Output: markdown on stdout: outcome counts, the boundary map (subject x structure -> outcome), and for every fast
        algorithm the properties that separate its surviving structures from the others:
          necessary  = holds on every structure where the algorithm SURVIVED,
          exact      = holds exactly on the structures where it SURVIVED (among the tested ones).
        "Tested" excludes TRIVIAL, INCONCLUSIVE and structures without a property row.

Usage: python experiments/2026-10-06d_mut_boundary_map.py > results/2026-10-06d_boundary_map.md
"""
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REC = REPO / "mutations" / "records" / "2026-10-06d"
PROPS_USED = ["add_associative", "add_commutative", "add_identity", "add_idempotent", "add_selective",
              "add_inverse_exists", "mul_associative", "mul_commutative", "mul_power_associative_to_6",
              "distributive_left", "distributive_right", "absorptive_one_plus_a_is_one",
              "mul_inverse_exists_for_nonzero", "two_invertible", "one_plus_one_nonzero"]


def load():
    recs = []
    for p in sorted(REC.glob("*.jsonl")):
        if p.stem in ("properties", "literature", "literature_queries"):
            continue
        recs += [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    props = {}
    for x in (REC / "properties.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(x)
        row = {k: v["holds"] for k, v in r["properties"].items()}
        ch = r["properties"].get("characteristic", {}).get("witness")
        if ch is not None:
            row["one_plus_one_nonzero"] = ch != 2          # derived: characteristic is not 2
        props[r["structure"]] = row
    return recs, props


def prop_row(rec, props):
    s = rec.get("structure")
    if not s:
        return None
    b = rec.get("builder", "")
    order = [f"monoid:{s}", s] if b in ("zeta", "rmq") else ([f"magma:{s}", s] if b == "power" else [s])
    for k in order:
        if k in props:
            return k, props[k]
    return None


def _key(r):
    """(pair, subject, mode); APSP mutants are split by instance family (digraphs vs DAGs)."""
    op = r["operator"].split(":", 1)[1] if ":" in r["operator"] else r["operator"]
    fam = f" [{op.split('|')[1]} instances]" if "|" in op else ""
    return r["pair"], r["subject"] + fam, r["mode"]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    recs, props = load()
    c = Counter(r["status"] for r in recs)
    fam = Counter((r["family"], r["status"]) for r in recs)
    print(f"## Outcome counts\n\n{len(recs)} mutants: " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())))
    print(f"\nNEAR-MISS flags: {sum(1 for r in recs if r.get('near_miss'))}")
    tests = sum(r["tests"]["tests"] for r in recs)
    print(f"\nDifferential tests run: {tests}")
    for f in ("MIRROR", "OPSWAP"):
        print(f"- {f}: " + ", ".join(f"{s} {n}" for (ff, s), n in sorted(fam.items()) if ff == f))
    fits = [r for r in recs if r.get("cost_fit") and "alphas" in r["cost_fit"]]
    print(f"\nCost fits: {len(fits)}; claimed cost within tolerance: "
          f"{sum(1 for r in fits if r['cost_fit']['claimed_fits'])}; discriminating (only the claimed cost fits): "
          f"{sum(1 for r in fits if r['cost_fit']['discriminating'])}; rivals rejected: "
          f"{sum(len(r['cost_fit']['rejected_rivals']) for r in fits)}")

    # boundary map
    print("\n## Boundary map (subject x structure)\n")
    by_subject = defaultdict(dict)
    structs = []
    for r in recs:
        if r["family"] != "OPSWAP":
            continue
        key = _key(r)
        s = r["operator"].split(":", 1)[1].split("|")[0]
        if s not in structs:
            structs.append(s)
        tag = {"SURVIVED": "S", "KILLED": "K", "INVALID": "I", "TRIVIAL": "T", "INCONCLUSIVE": "?"}[r["status"]]
        if r.get("near_miss"):
            tag += "*"
        by_subject[key][s] = tag
    for key, row in by_subject.items():
        cells = " ".join(f"{s}={t}" for s, t in row.items())
        print(f"- **{key[1]}** [{key[2]}] ({key[0]}): {cells}")

    # property correlation for the fast algorithms
    print("\n## Property correlation (mechanical)\n")
    for key, row in by_subject.items():
        rows = []
        for r in recs:
            if r["family"] == "OPSWAP" and _key(r) == key \
                    and r["status"] in ("SURVIVED", "KILLED", "INVALID") and "+sub:=add" not in r["operator"]:
                pr = prop_row(r, props)
                if pr:
                    rows.append((r["operator"].split(":", 1)[1].split("|")[0], r["status"] == "SURVIVED", pr[1]))
        if len(rows) < 3 or all(y for _, y, _ in rows) or not any(y for _, y, _ in rows):
            continue
        surv = [s for s, y, _ in rows if y]
        nec = [p for p in PROPS_USED if all(pp.get(p) is True for _, y, pp in rows if y)]
        exact = [p for p in PROPS_USED if all((pp.get(p) is True) == y for _, y, pp in rows)]
        pairs = [f"{a} & {b}" for a, b in itertools.combinations(PROPS_USED, 2)
                 if all(((pp.get(a) is True) and (pp.get(b) is True)) == y for _, y, pp in rows)]
        print(f"- **{key[1]}** ({key[0]}, {key[2]}): survived on {surv} of {len(rows)} tested structures. "
              f"Necessary (holds on all survivors): {nec or 'none'}. Exact separator: {exact or 'none'}"
              + (f"; exact pairs: {pairs[:6]}" if not exact and pairs else ""))


if __name__ == "__main__":
    main()
