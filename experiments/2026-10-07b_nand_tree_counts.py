#!/usr/bin/env python3
"""NAND-tree entry (pairs/nand-tree-evaluation-deterministic-vs-randomized): exact expectations, sampling noise, V2 design.

Questions:
 1. Left-first deterministic evaluation on the right-zero reluctant input: exactly 2^h leaf reads?
 2. Randomized (random child order) evaluation on reluctant inputs: exact expectation E1(h) and variance V1(h)
    from the recurrences (root value 1)
        E0(h) = 2 E1(h-1),            V0(h) = 2 V1(h-1)
        E1(h) = E0(h-1) + E1(h-1)/2,  V1(h) = V0(h-1) + V1(h-1)/2 + E1(h-1)^2 / 4,   E(0) = 1, V(0) = 0.
    Do sample means of the unchanged implementation agree with E1(h) within a few standard errors?
 3. alpha of the EXACT expectations against lambda^h, lambda = (1 + sqrt 33)/4, and against the rivals, over the
    chosen h values (lower-order term mu^h, mu = (1 - sqrt 33)/4 ~ -1.186, is not negligible at small h).
 4. Spread of alpha of the sample-mean fit over 40 alternative seed sets (same sample count as the entry), to
    justify the tolerance. The validator's own seeding is reproduced exactly too.

Deterministic (all seeds fixed). Outcome (console run 2026-10-07, CPython 3.14):
  - left-first reads exactly 2^h leaves for h = 0..16.
  - exact E1(h): 7.688 (h=4), 61.355 (8), 494.389 (12), 3993.106 (16); E1/lambda^h -> 0.9353; sd/mean -> 0.390.
  - exact-expectation alpha on h = 4..16 even: 0.9977 vs lambda^h; 0.7520 vs 2^h; 1.2855 vs 1.5^h; 1.5039 vs
    sqrt2^h; 0.8208 vs h lambda^h.
  - validator-seeded means (200 samples): 7.54, 21.98, 61.7, 177.47, 491.04, 1327.41, 4001.99; z-scores vs exact
    -0.76, 0.53, 0.21, 0.71, -0.25, -2.0, 0.08; alpha 0.9946 vs lambda^h, 0.7497 vs 2^h. The validator printed the
    same means, so the reproduction of its seeding is exact.
  - alpha over 40 alternative seed sets: mean 0.9972, sd 0.0047, min 0.9889, max 1.0078 -> tolerance 0.05 is
    about 10 sd; the 2^h rival stays 0.25 away.
"""
import importlib.util
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from validate import fit_slope  # noqa: E402

ENTRY = REPO / "pairs" / "nand-tree-evaluation-deterministic-vs-randomized"
ENTRY_ID = "nand-tree-evaluation-deterministic-vs-randomized"
RAND_NAME = "randomized random-order evaluation"
LAM = (1 + math.sqrt(33)) / 4


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "nand_harness")
LEFT = load(ENTRY / "implementations" / "left_first.py", "nand_left").nand_tree_left_first
RAND = load(ENTRY / "implementations" / "random_order.py", "nand_rand").nand_tree_random_order


def exact(hmax):
    E0, E1, V0, V1 = [1.0], [1.0], [0.0], [0.0]
    for h in range(1, hmax + 1):
        E0.append(2 * E1[h - 1])
        V0.append(2 * V1[h - 1])
        E1.append(E0[h - 1] + E1[h - 1] / 2)
        V1.append(V0[h - 1] + V1[h - 1] / 2 + E1[h - 1] ** 2 / 4)
    return E0, E1, V0, V1


def sample_mean(h, samples, prefix):
    total = 0
    for k in range(samples):
        inst = H.generate_scaling(h, random.Random(f"{prefix}|{h}" + (f"|{k}" if k else "")))
        random.seed(f"{prefix}|{h}|{k}|{RAND_NAME}")
        out = RAND(inst)
        total += H.reported_cost(out)
    return total / samples


def main():
    E0, E1, V0, V1 = exact(20)
    print("left-first reads on the right-zero reluctant input (root 1):")
    print("  ", [(h, H.reported_cost(LEFT(H.generate_scaling(h, None)))) for h in range(0, 13)])
    print("  all equal 2^h:", all(H.reported_cost(LEFT(H.generate_scaling(h, None))) == 2 ** h for h in range(0, 17)))

    print("exact E1(h), sd/mean, and E1(h)/lambda^h:")
    for h in range(0, 21, 2):
        print(f"  h={h:2d} E1={E1[h]:12.3f} sd/mean={math.sqrt(V1[h]) / E1[h]:.3f} ratio={E1[h] / LAM ** h:.4f}")

    hs = [4, 6, 8, 10, 12, 14, 16]
    ys = [math.log(E1[h]) for h in hs]
    for name, f in {"lambda^h (claim)": lambda h: LAM ** h, "2^h": lambda h: 2 ** h, "1.5^h": lambda h: 1.5 ** h,
                    "sqrt2^h": lambda h: 2 ** (h / 2), "h*lambda^h": lambda h: h * LAM ** h}.items():
        print(f"  exact-expectation alpha on {hs} vs {name}: {fit_slope([math.log(f(h)) for h in hs], ys):.4f}")

    samples = 200
    vals = [sample_mean(h, samples, f"{ENTRY_ID}|v2") for h in hs]
    print("validator-seeded sample means (200 samples):", [round(v, 2) for v in vals])
    print("  z-scores vs exact:", [round((v - E1[h]) / math.sqrt(V1[h] / samples), 2) for v, h in zip(vals, hs)])
    ys = [math.log(v) for v in vals]
    print("  alpha vs lambda^h:", round(fit_slope([h * math.log(LAM) for h in hs], ys), 4),
          " vs 2^h:", round(fit_slope([h * math.log(2) for h in hs], ys), 4))

    alphas = []
    for rep in range(40):
        vals = [sample_mean(h, samples, f"alt{rep}") for h in hs]
        alphas.append(fit_slope([h * math.log(LAM) for h in hs], [math.log(v) for v in vals]))
    m = sum(alphas) / len(alphas)
    sd = math.sqrt(sum((a - m) ** 2 for a in alphas) / (len(alphas) - 1))
    print(f"alpha over 40 alternative seed sets: mean {m:.4f}, sd {sd:.4f}, min {min(alphas):.4f}, max {max(alphas):.4f}")


if __name__ == "__main__":
    main()
