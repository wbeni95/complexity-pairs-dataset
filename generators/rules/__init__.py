"""Rule mining (round 2026-10-06d): speed-up rules as executable templates, family generators and screening.

One module per rule (each exports CATALOGUE, generate(seed, count), build(spec)):
  memo         R1  memoisation of overlapping subproblems (+ R1c state compression)
  convolution  R2  transform-based convolution over an index structure (FWHT, NTT, zeta, prefix sums, lifting)
  magma_power  R3  repeated squaring for an associative operation
  greedy       R4  greedy on matroids
  knuth        R5  monotone split points (Knuth-Yao quadrangle inequality)
  bilinear     R6  bilinear algorithms with fewer multiplications (GF(2) tensor rank)
  mitm         R7  meet in the middle
common = screening harness; runner = batch screening, dedup, clustering and summaries; __main__ = CLI.

Output of these generators is mechanical (T7 at most, generators/README.md); a match with a named problem is a
pipeline check, never a novelty claim.
"""
import importlib

RULES = ("memo", "convolution", "magma_power", "greedy", "knuth", "bilinear", "mitm")


def load(name: str):
    if name not in RULES:
        raise ValueError(f"unknown rule {name!r}; choose from {RULES}")
    return importlib.import_module(f"{__name__}.{name}")
