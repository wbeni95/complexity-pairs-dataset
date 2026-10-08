"""Experiment: entry pairs/three-xor-all-triples-vs-patricia-trie (3XOR, all triples vs Patricia trie).

What it checks (deterministic; no timing; standard library only, so it runs under any CPython >= 3.8):
  a. Exact counts on the V2 family (generate_scaling, validator seeding) against the hand-derived closed forms:
     all triples (n^3 - n)/6 for n = 1, 2, 4, ..., 512 and the Patricia trie 7n^2 + 2n log2(n) - 3n for
     n = 1, 2, 4, ..., 2048, both in total and per kind of operation (XOR, AND, comparison, truth test); the counts
     do not depend on the shuffle (three other seeds per n up to 256); the trie of the V2 family has n leaves and
     n - 1 branching nodes; source-line events per counted operation (sys.settrace) at n = 16, 32, 64 measure the
     uncounted bookkeeping.
  b. Agreement of both implementations with each other and with harness.check on 525 extra instances (n = 0..12,
     16, 20, 24, 32, 48, 64, 100, 150; 25 seeds each) plus the trie alone on 20 instances (n = 300, 600), with the
     yes/no split; and the yes/no split of the validator's own V1 battery (its seeds, per size).
  c. Oracle control: deliberately wrong outputs must be rejected by harness.check (nonzero XOR; a repeated index
     whose XOR is 0; unsorted indices; negative indices that alias a real solution through Python's negative
     indexing; out of range; wrong arity, including a list; bool, float, str entries, including (False, True, k)
     on instances where values[0] ^ values[1] ^ values[k] == 0; None on a yes-instance; a triple on a
     no-instance), and the outputs of both implementations must be accepted.
  d. Cross-version print: every count series of the entry's V2 claims and shape grids (validator seeding) and one
     SHA-256 over them, to compare interpreters:
         .venv/Scripts/python.exe experiments/2026-10-06i_three_xor.py
         py -3.12 experiments/2026-10-06i_three_xor.py

Run from anywhere. RESULT (2026-10-06, CPython 3.14.2 and 3.12.10, identical output apart from the version line):
  a. every count equals its closed form, in total and per kind (all triples n = 1..512, trie n = 1..2048); three
     other shuffles give identical counts; the trie has n leaves and n - 1 branching nodes; line events per counted
     operation at n = 16, 32, 64: all triples 2.229, 2.103, 2.049; trie 3.246, 3.112, 3.050 (rerun 2026-10-08
     under both interpreters with the current, iterative trie; the earlier recursive trie gave 3.089, 3.031, 3.009).
  b. 525 instances (248 yes, 277 no): 0 disagreements, 0 check failures; trie alone at n = 300, 600: 20 instances
     (14 yes), 0 failures; validator V1 battery: 160 instances, 79 yes, 81 no, both answers at 15 of 20 sizes.
  c. 2977 wrong outputs on 360 instances: 2977 rejected, 0 accepted, 0 undecided; 720 correct outputs: 720 accepted.
  d. SHA-256 d38397740dfacbacb07d2e12ffba034a4ed2b6b3f1bdcdf411e23343080ef9cb under both interpreters; fits against
     the closed forms alpha = 1.000000; bare leading terms n**3: 1.000311 (all triples), n**2: 0.996615 (trie).

Check lines start with [PASS] or [FAIL]: the closed-form, shuffle and tree-shape lines of a, the two agreement lines
of b and the V1 battery split (160 instances, 79 yes, 81 no, both answers at 15 of the 17 sizes n >= 3, not at
n = 4 and n = 300), every kind of c (exactly the 13 kinds), and its total (2977 wrong outputs on 360 instances, all
rejected). The run ends with ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1). The counts at
the V2 sizes, the bookkeeping ratios and part d (series, fits, SHA-256) are reported, not checked.
"""
import hashlib
import importlib.util
import json
import math
import platform
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "three-xor-all-triples-vs-patricia-trie"
EID = ENTRY.name
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "txor_harness")
A = load(ENTRY / "implementations" / "all_triples.py", "txor_all")
P = load(ENTRY / "implementations" / "patricia_trie.py", "txor_trie")
SPEC = json.loads((ENTRY / "entry.json").read_text(encoding="utf-8"))
IMPL = {"all": A.three_xor_all_triples, "trie": P.three_xor_patricia_trie}
NAMES = {alg["implementation"].rsplit(":", 1)[1]: alg for alg in SPEC["algorithms"]}
ALG = {"all": NAMES["three_xor_all_triples"], "trie": NAMES["three_xor_patricia_trie"]}


def closed_all(n):
    return (n ** 3 - n) // 6


def closed_trie(n):
    return 7 * n * n + 2 * n * (n.bit_length() - 1) - 3 * n


def kinds_all(n):
    return {"xor": n * (n - 1) // 2, "and_or": 0, "shift": 0, "compare": closed_all(n) - n * (n - 1) // 2, "truth": 0}


def kinds_trie(n):
    lg = n.bit_length() - 1
    return {"xor": n * n, "and_or": n * lg + n * (n - 1), "shift": 0, "compare": n + n * (4 * n - 2),
            "truth": n * lg + n * (n - 1)}


CLOSED = {"all": closed_all, "trie": closed_trie}

FAILED = []


def check_line(ok, *parts):
    """Print one check line with a [PASS] or [FAIL] prefix and remember the failures."""
    print("[PASS]" if ok else "[FAIL]", *parts, flush=True)
    if not ok:
        FAILED.append(" ".join(str(p) for p in parts).strip())
    return ok


def finish_checks():
    """End of the run: ALL CHECKS PASSED (exit code 0), or the failed checks and exit code 1."""
    if FAILED:
        print(f"FAILED: {len(FAILED)} check(s):")
        for label in FAILED:
            print(f"  {label}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


def count(key, n, inst_seed, alg_seed):
    """One count with the validator's seeding scheme; returns (total, per-kind counts, output)."""
    inst = H.generate_scaling(n, random.Random(inst_seed))
    random.seed(alg_seed)
    out = IMPL[key](inst)
    return H.reported_cost(out), H.counts(), out


def v2_count(key, n):
    name = ALG[key]["name"]
    return count(key, n, f"{EID}|v2|{n}", f"{EID}|v2|{n}|0|{name}")


def powers(lo, hi):
    out, n = [], lo
    while n <= hi:
        out.append(n)
        n *= 2
    return out


# ------------------------------------------------------------------------------------------------------------
def part_a(series):
    print("a. closed forms on the V2 family")
    for key, hi, closed, kinds in (("all", 512, closed_all, kinds_all), ("trie", 2048, closed_trie, kinds_trie)):
        ok_total = ok_kinds = ok_out = True
        for n in powers(1, hi):
            total, per, out = v2_count(key, n)
            series[(key, n)] = total
            ok_total &= total == closed(n)
            ok_kinds &= per == kinds(n)
            ok_out &= out is None
        check_line(ok_total and ok_kinds and ok_out,
                   f"   {key}: n = 1..{hi} (powers of two): total == closed form: {ok_total}; per kind: {ok_kinds}; "
                   f"answer None: {ok_out}")
        same = all(count(key, n, f"txor-shuffle|{n}|{s}", f"txor-shuffle|{n}|{s}|alg")[0] == series[(key, n)]
                   for n in powers(1, 256) for s in range(3))
        check_line(same, f"   {key}: identical counts for 3 other shuffles at every n = 1..256: {same}")
    print("   trie at V2 sizes:", {n: series[("trie", n)] for n in ALG["trie"]["harness"]["scaling"]["n_values"]})
    print("   all  at V2 sizes:", {n: series[("all", n)] for n in ALG["all"]["harness"]["scaling"]["n_values"]})

    shape_ok = True
    for n in powers(1, 1024):
        w, values = H.generate_scaling(n, random.Random(f"txor-tree|{n}"))
        leaves = []
        root = P._build(values, list(range(n)), w - 1, leaves)
        stack, branching, leaf_count = [root], 0, 0
        while stack:
            node = stack.pop()
            if isinstance(node, int):
                leaf_count += 1
            else:
                branching += 1
                stack.extend(node[1:])
        shape_ok &= (leaf_count, branching, len(leaves)) == (n, n - 1, n)
    check_line(shape_ok, f"   trie of the V2 family has n leaves and n - 1 branching nodes for n = 1..1024: {shape_ok}")

    files = {str(ENTRY / "implementations" / "all_triples.py"), str(ENTRY / "implementations" / "patricia_trie.py")}
    for key in ("all", "trie"):
        parts = []
        for n in (16, 32, 64):
            inst = H.generate_scaling(n, random.Random(f"txor-lines|{n}"))
            lines = [0]

            def tracer(frame, event, arg):
                if frame.f_code.co_filename in files:
                    if event == "line":
                        lines[0] += 1
                    return tracer
                return None

            sys.settrace(tracer)
            try:
                IMPL[key](inst)
            finally:
                sys.settrace(None)
            c = H.reported_cost(None)
            parts.append(f"n={n}: {lines[0]} line events / {c} counted = {lines[0] / c:.3f}")
        print(f"   uncounted bookkeeping, {key}: " + "; ".join(parts))


# ------------------------------------------------------------------------------------------------------------
def part_b():
    print("b. agreement with each other and with check")
    sizes = list(range(0, 13)) + [16, 20, 24, 32, 48, 64, 100, 150]
    inst_count = yes = disagree = fail = 0
    for n in sizes:
        for t in range(25):
            inst = H.generate(n, random.Random(f"txor-exp|{n}|{t}"))
            a, b = A.three_xor_all_triples(inst), P.three_xor_patricia_trie(inst)
            inst_count += 1
            yes += a is not None
            disagree += not H.equal(a, b)
            fail += (H.check(inst, a) is not True) + (H.check(inst, b) is not True)
    check_line(disagree == 0 and fail == 0, f"   both implementations: {inst_count} instances ({yes} yes, "
                                            f"{inst_count - yes} no): {disagree} disagreements, {fail} check failures")
    big = big_yes = big_fail = 0
    for n in (300, 600):
        for t in range(10):
            inst = H.generate(n, random.Random(f"txor-exp-big|{n}|{t}"))
            b = P.three_xor_patricia_trie(inst)
            big += 1
            big_yes += b is not None
            big_fail += H.check(inst, b) is not True
    check_line(big_fail == 0, f"   Patricia trie alone, n = 300, 600: {big} instances ({big_yes} yes): {big_fail} check "
                              f"failures")

    th = SPEC["test_harness"]
    split, kinds_seen = {}, {}
    for n in th["v1_sizes"]:
        y = 0
        for trial in range(th["trials"]):
            w, values = H.generate(n, random.Random(f"{EID}|v1|{n}|{trial}"))
            y += H.has_solution(values)
        split[n] = (y, th["trials"] - y)
    total_yes = sum(s[0] for s in split.values())
    total = sum(s[0] + s[1] for s in split.values())
    both = [n for n, (y, no) in split.items() if y and no]
    from_three = [n for n in th["v1_sizes"] if n >= 3]
    check_line((total, total_yes) == (160, 79) and len(from_three) == 17
               and both == [n for n in from_three if n not in (4, 300)],
               f"   validator V1 battery: {total} instances, {total_yes} yes, {total - total_yes} no; "
               f"(yes, no) per n: {split}; both answers at n = {both}")


# ------------------------------------------------------------------------------------------------------------
def part_c():
    print("c. oracle control")
    tally = {}

    def present(kind, inst, out, expect):
        r = H.check(inst, out)
        t = tally.setdefault(kind, {"presented": 0, "rejected": 0, "accepted": 0, "undecided": 0, "as_expected": 0})
        t["presented"] += 1
        t["rejected" if r is False else "accepted" if r is True else "undecided"] += 1
        t["as_expected"] += r is expect

    instances = []
    for n in list(range(0, 13)) + [16, 24, 32, 64]:
        for t in range(20):
            instances.append(H.generate(n, random.Random(f"txor-control|{n}|{t}")))
    for t in range(20):                               # bool trap: values[0] ^ values[1] ^ values[k] == 0
        rng = random.Random(f"txor-control-bool|{t}")
        n = rng.randint(3, 12)
        w = rng.randint(2, 16)
        vals = [rng.randrange(1 << w) for _ in range(n)]
        k = rng.randrange(2, n)
        vals[k] = vals[0] ^ vals[1]
        instances.append((w, tuple(vals)))

    for inst in instances:
        w, values = inst
        n = len(values)
        outs = [A.three_xor_all_triples(inst), P.three_xor_patricia_trie(inst)]
        for out in outs:
            present("correct", inst, out, True)
        sol = outs[0]
        if sol is None:
            if n >= 3:
                present("triple_on_no_instance", inst, (0, 1, 2), False)
        else:
            i, j, k = sol
            present("none_on_yes_instance", inst, None, False)
            present("unsorted", inst, (j, i, k), False)
            present("unsorted", inst, (k, j, i), False)
            present("negative_alias", inst, (i - n, j - n, k - n), False)
            present("wrong_arity", inst, [i, j, k], False)
            present("float", inst, (float(i), float(j), float(k)), False)
            present("str", inst, (str(i), str(j), str(k)), False)
        if n >= 3:
            rng = random.Random(f"txor-control-nz|{n}|{values}")
            for _ in range(60):
                i, j, k = sorted(rng.sample(range(n), 3))
                if values[i] ^ values[j] ^ values[k]:
                    present("nonzero_xor", inst, (i, j, k), False)
                    break
            for k in range(2, n):
                if values[0] ^ values[1] ^ values[k] == 0:
                    present("bool_trap", inst, (False, True, k), False)
                    break
            else:
                present("bool", inst, (False, True, 2), False)
        if n >= 2:
            z = next((p for p in range(n) if values[p] == 0), None)
            if z is not None:
                i = 0 if z != 0 else 1
                present("repeated_index_zero_xor", inst, (i, i, z) if i < z else (z, i, i), False)
            present("out_of_range", inst, (n - 2, n - 1, n), False)
            present("wrong_arity", inst, (0, 1), False)
        if n >= 4:
            present("wrong_arity", inst, (0, 1, 2, 3), False)
    total_wrong = {"presented": 0, "rejected": 0, "accepted": 0, "undecided": 0}
    kinds = {"bool", "bool_trap", "correct", "float", "negative_alias", "none_on_yes_instance", "nonzero_xor",
             "out_of_range", "repeated_index_zero_xor", "str", "triple_on_no_instance", "unsorted", "wrong_arity"}
    check_line(set(tally) == kinds, f"   kinds presented: {len(tally)} (expected the 13 kinds {sorted(kinds)})")
    for kind, t in sorted(tally.items()):
        check_line(t["as_expected"] == t["presented"],
                   f"   {kind}: presented {t['presented']}, rejected {t['rejected']}, accepted {t['accepted']}, "
                   f"undecided {t['undecided']}, as expected {t['as_expected']}")
        if kind != "correct":
            for key in total_wrong:
                total_wrong[key] += t[key]
    check_line(total_wrong["rejected"] == total_wrong["presented"] == 2977 and len(instances) == 360,
               f"   wrong outputs in total: {total_wrong} on {len(instances)} instances")


# ------------------------------------------------------------------------------------------------------------
def part_d(series):
    print("d. cross-version series (validator seeding)")
    digest = hashlib.sha256()
    for key in ("all", "trie"):
        sc = ALG[key]["harness"]["scaling"]
        lo, hi = sc["shape"]["n_range"]
        for label, ns in (("v2", sc["n_values"]), ("shape", powers(lo, hi))):
            vals = [series[(key, n)] if (key, n) in series else v2_count(key, n)[0] for n in ns]
            line = f"{EID} | {ALG[key]['name']} | {label} | {ns} | {vals}"
            digest.update(line.encode("utf-8"))
            print("   " + line)
            if label == "v2":
                lead, lead_name = (lambda n: n ** 3, "n**3") if key == "all" else (lambda n: n ** 2, "n**2")
                print(f"      fit against the closed form ({sc['cost']}): alpha = {fit(CLOSED[key], ns, vals):.6f}; "
                      f"against the bare leading term {lead_name} (information only): "
                      f"alpha = {fit(lead, ns, vals):.6f}")
    print(f"   python {platform.python_version()} sha256 {digest.hexdigest()}")


def fit(cost, ns, vals):
    """The validator's slope: log(count) against log(cost(n))."""
    xs = [math.log(cost(n)) for n in ns]
    ys = [math.log(v) for v in vals]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


def main():
    print("python", platform.python_version(), platform.python_implementation())
    series = {}
    part_a(series)
    part_b()
    part_c()
    part_d(series)
    finish_checks()


if __name__ == "__main__":
    main()
