"""Experiment (research/2026-10-06f_new_entries.md): Horn-SAT entry, pairs/horn-sat-brute-force-vs-unit-propagation.

What it checks (deterministic; no timing):
  1. Brute-force counts on the V2 family H_n equal 6 * E(n) with E(n) = (2n + 13) 2^(n-2) - 2n - 4 literal
     evaluations, for every n = 3..16 (E(n) is derived by hand in entry.json).
  2. Unit-propagation counts on H_n equal 12n - 7 for every n = 3..300 and at the V2 sizes 1000..32000
     (derived by inspection in entry.json).
  3. Naive forward chaining (the oracle's method) needs exactly n full passes on H_n, i.e. Theta(n^2) clause visits,
     so the family separates linear propagation from the quadratic naive method.
  4. Oracle control: on 1040 seeded V1-style instances (n = 0..12, 80 per size), check() accepts the correct
     output and rejects every deliberately wrong output of each applicable type:
       flip    - one bit of the least model flipped (a non-model, or a model that is not least);
       larger  - a strictly larger model (least model plus one variable, if that is still a model);
       none    - None returned for a satisfiable formula;
       allfalse- the all-false assignment returned for an unsatisfiable formula;
       short   - a tuple of the wrong length.
  5. Fits (validator formula, tolerance 0.02): the claims and every declared rival, plus the bare leading term.

Run from the repository root:  .venv/Scripts/python.exe experiments/2026-10-06f_entries_horn_sat.py
RESULT (2026-10-06): all closed forms hold; oracle control accepts all correct outputs and rejects all wrong ones
(tallies printed); see the report for the numbers.
"""
import importlib.util
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "horn-sat-brute-force-vs-unit-propagation"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "horn_harness")
B = load(ENTRY / "implementations" / "brute_force.py", "horn_brute")
U = load(ENTRY / "implementations" / "unit_propagation.py", "horn_up")


def fit_slope(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


def alpha(cost, ns, vals):
    return fit_slope([math.log(cost(n)) for n in ns], [math.log(v) for v in vals])


def count(fn, n):
    inst = H.generate_scaling(n, None)
    fn(inst)
    return H.reported_cost(None)


def main():
    # 1. brute-force closed form
    E = lambda n: (2 * n + 13) * 2 ** (n - 2) - 2 * n - 4  # noqa: E731
    brute = {n: count(B.horn_sat_brute_force, n) for n in range(3, 17)}
    print("1. brute force = 6 E(n) for n = 3..16:", all(brute[n] == 6 * E(n) for n in brute))
    print("   counts at V2 sizes:", {n: brute[n] for n in (8, 10, 12, 14, 16)})

    # 2. unit propagation closed form
    ns_up = list(range(3, 301)) + [1000, 2000, 4000, 8000, 16000, 32000]
    up = {n: count(U.horn_sat_unit_propagation, n) for n in ns_up}
    print("2. unit propagation = 12n - 7 for n = 3..300 and V2 sizes:", all(up[n] == 12 * n - 7 for n in ns_up))
    print("   counts at V2 sizes:", {n: up[n] for n in (1000, 2000, 4000, 8000, 16000, 32000)})

    # 3. naive chaining passes on H_n (plain integers)
    def passes(n):
        clauses = H._family(n)
        true = [False] * (n + 1)
        p = 0
        changed = True
        while changed:
            changed = False
            p += 1
            for cl in clauses:
                heads = [l for l in cl if l > 0]
                if heads and all(true[-l] for l in cl if l < 0) and not true[heads[0]]:
                    true[heads[0]] = True
                    changed = True
        return p
    print("3. naive chaining passes on H_n (n: passes):", {n: passes(n) for n in (5, 10, 50, 200)},
          "== n for n = 3..200:", all(passes(n) == n for n in range(3, 201)))

    # 4. oracle control
    tally = {k: [0, 0] for k in ("correct", "flip", "larger", "none", "allfalse", "short")}  # [tested, rejected]
    for n in range(0, 13):
        for t in range(80):
            inst = H.generate(n, random.Random(f"horn-control|{n}|{t}"))
            out = U.horn_sat_unit_propagation(inst)
            assert out == B.horn_sat_brute_force(inst)
            tally["correct"][0] += 1
            tally["correct"][1] += H.check(inst, out) is not True
            nn, clauses = inst
            wrongs = []
            if out is not None:
                if nn:
                    i = random.Random(f"flip|{n}|{t}").randrange(nn)
                    wrongs.append(("flip", tuple((not x) if j == i else x for j, x in enumerate(out))))
                    for v in range(nn):
                        if not out[v]:
                            bigger = tuple(True if j == v else x for j, x in enumerate(out))
                            if H._satisfies(clauses, (None,) + bigger):
                                wrongs.append(("larger", bigger))
                                break
                wrongs.append(("none", None))
                wrongs.append(("short", out[:-1] if nn else (False,)))
            else:
                wrongs.append(("allfalse", (False,) * nn))
                wrongs.append(("short", (False,) * (nn + 1)))
            for kind, w in wrongs:
                tally[kind][0] += 1
                tally[kind][1] += H.check(inst, w) is False
    print("4. oracle control [tested, rejected]:", tally)
    print("   correct outputs all accepted:", tally["correct"][1] == 0,
          "| every wrong output rejected:", all(t[0] == t[1] for k, t in tally.items() if k != "correct"))

    # 5. fits
    nb = [8, 10, 12, 14, 16]
    vb = [brute[n] for n in nb]
    print("5. brute force fits:")
    for name, c in [("(2n+13) 2^n - 8n - 16 (claim)", lambda n: (2 * n + 13) * 2 ** n - 8 * n - 16),
                    ("2^n (rival)", lambda n: 2 ** n), ("n^2 2^n (rival)", lambda n: n * n * 2 ** n),
                    ("n 2^n (bare leading term, info)", lambda n: n * 2 ** n)]:
        print(f"   {name}: alpha = {alpha(c, nb, vb):.4f}")
    nu = [1000, 2000, 4000, 8000, 16000, 32000]
    vu = [up[n] for n in nu]
    print("   unit propagation fits:")
    for name, c in [("12n - 7 (claim)", lambda n: 12 * n - 7), ("n log n (rival)", lambda n: n * math.log(n)),
                    ("n^2 (rival)", lambda n: n * n), ("n (bare, info)", lambda n: n)]:
        print(f"   {name}: alpha = {alpha(c, nu, vu):.4f}")


if __name__ == "__main__":
    main()
