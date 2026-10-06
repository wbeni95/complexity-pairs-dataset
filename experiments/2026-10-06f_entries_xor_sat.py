"""Experiment (research/2026-10-06f_new_entries.md): XOR-SAT / #XOR-SAT entry,
pairs/xor-sat-brute-force-vs-gaussian-elimination.

What it checks (deterministic; no timing):
  1. Brute-force counts on the V2 family X_n equal (2n + 1)(2^(n+1) - 2) for every n = 1..16.
  2. Gaussian-elimination counts on X_n equal n (n^2 + 6n - 4) / 3 for every n = 1..200 and at the V2 sizes.
  3. Oracle control, on seeded V1-style instances, split into n <= 10 (where check() also counts exhaustively) and
     n = 11..40 (where only the certificates decide): check() accepts the correct output and rejects each
     applicable wrong output:
       plus1    - count + 1;
       double   - count * 2 (the right count for a system of rank one less);
       half     - count / 2 (rank one more), when count >= 2;
       zero     - (0, None) for a consistent system;
       claimsat - (1, all-zero tuple) for an inconsistent system;
       badwit   - the correct count with a witness that violates some row (one bit flipped, kept only if the
                  flipped assignment is really not a solution);
       nowit    - the correct positive count with witness None.
  4. Fits (validator formula, tolerance 0.02): the claims, every declared rival, and the bare leading terms.

Run from the repository root:  .venv/Scripts/python.exe experiments/2026-10-06f_entries_xor_sat.py
RESULT (2026-10-06): both closed forms hold; every correct output accepted and every wrong output rejected in both
size ranges (tallies printed and copied into the report).
"""
import importlib.util
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "xor-sat-brute-force-vs-gaussian-elimination"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "xor_harness")
B = load(ENTRY / "implementations" / "brute_force.py", "xor_brute")
G = load(ENTRY / "implementations" / "gaussian_elimination.py", "xor_gauss")


def fit_slope(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


def alpha(cost, ns, vals):
    return fit_slope([math.log(cost(n)) for n in ns], [math.log(v) for v in vals])


def count(fn, n):
    inst = H.generate_scaling(n, None)
    fn(inst)
    return H.reported_cost(None)


def is_solution(rows, n, x):
    return all(H._apply(r[:n], x) == r[n] for r in rows)


def control(ns, label, per_size):
    kinds = ("correct", "plus1", "double", "half", "zero", "claimsat", "badwit", "nowit")
    tally = {k: [0, 0] for k in kinds}                        # [tested, rejected (correct: accepted)]
    for n in ns:
        for t in range(per_size):
            inst = H.generate(n, random.Random(f"xor-control|{n}|{t}"))
            out = G.xor_sat_gauss(inst)
            if n <= 12:
                assert H.equal(out, B.xor_sat_brute_force(inst))
            nn, rows = inst
            tally["correct"][0] += 1
            tally["correct"][1] += H.check(inst, out) is True
            c, w = out
            wrongs = [("plus1", (c + 1, w if w is not None else (0,) * nn))]
            if c > 0:
                wrongs += [("double", (2 * c, w)), ("zero", (0, None)), ("nowit", (c, None))]
                if c >= 2:
                    wrongs.append(("half", (c // 2, w)))
                for i in range(nn):
                    flipped = tuple(b ^ (j == i) for j, b in enumerate(w))
                    if not is_solution(rows, nn, flipped):
                        wrongs.append(("badwit", (c, flipped)))
                        break
            else:
                wrongs.append(("claimsat", (1, (0,) * nn)))
            for kind, wout in wrongs:
                tally[kind][0] += 1
                tally[kind][1] += H.check(inst, wout) is False
    ok = tally["correct"][0] == tally["correct"][1] and all(t[0] == t[1] for k, t in tally.items() if k != "correct")
    print(f"3. oracle control, {label} [tested, rejected; for 'correct': tested, accepted]: {tally}  -> all as expected: {ok}")


def main():
    brute = {n: count(B.xor_sat_brute_force, n) for n in range(1, 17)}
    print("1. brute force = (2n+1)(2^(n+1)-2) for n = 1..16:",
          all(brute[n] == (2 * n + 1) * (2 ** (n + 1) - 2) for n in brute))
    print("   counts at V2 sizes:", {n: brute[n] for n in (8, 10, 12, 14, 16)})
    ng = list(range(1, 201)) + [256]
    gauss = {n: count(G.xor_sat_gauss, n) for n in ng}
    print("2. Gaussian elimination = n(n^2+6n-4)/3 for n = 1..200 and 256:",
          all(3 * gauss[n] == n * (n * n + 6 * n - 4) for n in ng))
    print("   counts at V2 sizes:", {n: gauss[n] for n in (16, 24, 32, 48, 64, 96, 128)})

    control(range(0, 11), "n = 0..10 (exhaustive count active)", 60)
    control(range(11, 41), "n = 11..40 (certificates only)", 12)

    nb = [8, 10, 12, 14, 16]
    vb = [brute[n] for n in nb]
    print("4. brute force fits:")
    for name, c in [("(2n+1)(2^(n+1)-2) (claim)", lambda n: (2 * n + 1) * (2 ** (n + 1) - 2)),
                    ("2^n (rival)", lambda n: 2 ** n), ("n^2 2^n (rival)", lambda n: n * n * 2 ** n),
                    ("n 2^n (bare, info)", lambda n: n * 2 ** n)]:
        print(f"   {name}: alpha = {alpha(c, nb, vb):.4f}")
    nG = [16, 24, 32, 48, 64, 96, 128]
    vG = [gauss[n] for n in nG]
    print("   Gaussian elimination fits:")
    for name, c in [("n(n^2+6n-4) (claim)", lambda n: n * (n * n + 6 * n - 4)), ("n^2 (rival)", lambda n: n * n),
                    ("n^4 (rival)", lambda n: n ** 4), ("n^3 (bare, info)", lambda n: n ** 3)]:
        print(f"   {name}: alpha = {alpha(c, nG, vG):.4f}")


if __name__ == "__main__":
    main()
