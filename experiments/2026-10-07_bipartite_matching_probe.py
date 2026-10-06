"""Timing probe for pairs/bipartite-matching-kuhn-vs-hopcroft-karp on the adversarial family G_k
(generate_scaling, n = V = 4k^2 + k): choose n ranges and look at the fits before writing entry.json.
Also fits each algorithm against the other's claimed exponent, to see whether the timing alone separates
n^3 from n^2.5 (it is not expected to: the exponent gap is inside the 0.25 slope tolerance).

Run from the repository root:  python experiments/2026-10-07_bipartite_matching_probe.py

Outcome (2026-10-07, console): Kuhn over k = 3..10 (n = 39..410): alpha = 0.968 vs n^3, but also 1.168 vs
n^2.5 (inside the tolerance). Hopcroft-Karp over k = 4..14 (n = 68..798): alpha = 0.973 vs n^2.5, 1.221 vs
n^2 and 0.815 vs n^3 (all inside the tolerance). Measured exponents (alpha x claimed exponent): about 2.90
for Kuhn and 2.43 for Hopcroft-Karp. Conclusion: timing is consistent with the claims but cannot by itself
separate the exponents; the exact counts (2026-10-07_bipartite_matching_counts.py) carry that part.
entry.json extends the ranges by one k each (Kuhn to k = 11, Hopcroft-Karp to k = 15).
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("probe_helpers", ROOT / "experiments" / "2026-10-07_probe_helpers.py")
ph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph)

E = "bipartite-matching-kuhn-vs-hopcroft-karp"
ks = range(3, 11)
ns = [4 * k * k + k for k in ks]
a, t = ph.probe(E, "implementations/kuhn.py:matching_kuhn", "generate_scaling", "n**3", ns)
print("  local slopes:", [round(x, 3) for x in ph.local_slopes(ns, t, "n**3")])
ph.probe(E, "implementations/kuhn.py:matching_kuhn", "generate_scaling", "n**2.5", ns, label="Kuhn vs n**2.5")
ks = range(4, 15)
ns = [4 * k * k + k for k in ks]
a, t = ph.probe(E, "implementations/hopcroft_karp.py:matching_hopcroft_karp", "generate_scaling", "n**2.5", ns)
print("  local slopes:", [round(x, 3) for x in ph.local_slopes(ns, t, "n**2.5")])
ph.probe(E, "implementations/hopcroft_karp.py:matching_hopcroft_karp", "generate_scaling", "n**2", ns, label="HK vs n**2")
ph.probe(E, "implementations/hopcroft_karp.py:matching_hopcroft_karp", "generate_scaling", "n**3", ns, label="HK vs n**3")
