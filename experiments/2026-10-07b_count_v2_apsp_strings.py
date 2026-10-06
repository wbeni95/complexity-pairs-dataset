"""Count-based V2 for pairs/all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall and
pairs/string-matching-naive-vs-kmp: exact counts, closed forms, fits and rivals.

APSP: the harness wraps the off-diagonal weights of the complete digraph in CountingWeight, which counts
additions (one per relaxation step). Expected: Bellman-Ford x n exactly n^2 (n-1)^2 (every addition
dist[u] + w involves an input weight); Floyd-Warshall n^3 - n (the n steps with i = j = k add the
implementation's own diagonal zeros and are invisible). The instrumentation must not change the answers:
the outputs on the counting instance (unwrapped) are compared with the outputs on the plain instance.

String matching: the harness passes T = a^n and P = a^(m-1) b (m = n // 2) as tuples of CountingChar.
Expected: naive (n - m + 1) m; KMP: failure function 3m - 6 (m >= 3: one comparison at q = 1, two at each of
q = 2..m-2, then m - 2 failing ones plus one final test at the 'b'), scan 1 + 2(m - 2) + 3(n - m + 1)
(three per text character once q has reached m - 1), total 3n + 2m - 6, i.e. 4n - 6 for even n.
The answers on the tuple instance are compared with the answers on the str instance.

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-07b_count_v2_apsp_strings.py
Deterministic (validator seeds).

Outcome (run 2026-10-06 local date, Python 3.14.2; deterministic, identical on rerun):
  * APSP: answers with counting weights equal answers with plain ints (n = 5, 12, 20, both algorithms).
    Bellman-Ford x n exactly n^2 (n-1)^2 at n = 8..40, alpha 1.0000, rival n^3 1.3769 (rejected).
    Floyd-Warshall exactly n^3 - n at n = 16..128 and n = 32..200; on 32..200 alpha 1.0002, rival
    n^2 (n-1)^2 0.7449, n^2.5 1.2002, n^3 log n 0.9288 (all rejected).
  * strings: tuple answers equal str answers (scaling instances and 200 random small pairs, both algorithms).
    Naive exactly (n - m + 1) m at n = 200..3200, alpha 0.9984; rivals n 1.9968, n log n 1.7340,
    n^2 log n 0.9281. KMP exactly 3n + 2m - 6 (= 4n - 6 here) at n = 3000..300000, alpha 1.0001; rivals
    n log n 0.9105, n^2 0.5000, n / log n 1.1091.
  Written to entry.json: the existing n_values, tolerance 0.03.
"""
import importlib.util
import random
from pathlib import Path

_s = importlib.util.spec_from_file_location("cv2h", Path(__file__).resolve().parent / "2026-10-07b_count_v2_helpers.py")
H = importlib.util.module_from_spec(_s)
_s.loader.exec_module(H)

AP = "all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall"
SM = "string-matching-naive-vs-kmp"
BF, FW = "Bellman-Ford from every source", "Floyd-Warshall"
NA, KMP = "naive matching", "Knuth-Morris-Pratt"

ap_dir, ap_entry, ap_h = H.entry_and_harness(AP)
names = [a["name"] for a in ap_entry["algorithms"]]
print("APSP algorithm names:", names)
BF = next(x for x in names if x.lower().startswith("bellman"))
FW = next(x for x in names if x.lower().startswith("floyd"))


def unwrap(x):
    if isinstance(x, tuple):
        return tuple(unwrap(y) for y in x)
    return x.v if hasattr(x, "v") else x


print("\n== APSP: answers unchanged by the instrumentation ==")
for name in (BF, FW):
    fn = H.V.load_callable(ap_dir, H.algorithm(ap_entry, name)["implementation"])
    for n in (5, 12, 20):
        inst = ap_h.generate_scaling(n, random.Random(f"check|{n}"))
        plain = tuple(tuple(unwrap(w) for w in row) for row in inst)
        print(f"  {name}, n={n}: equal = {unwrap(fn(inst)) == fn(plain)}")

print("\n== APSP: Bellman-Ford x n (claim n**2 * (n-1)**2) ==")
ns = [8, 10, 13, 16, 20, 25, 32, 40]
v = H.counts(AP, BF, ns, 1)
print("  exactly n^2 (n-1)^2:", all(int(c) == n * n * (n - 1) ** 2 for n, c in zip(ns, v)))
H.report("tol=0.03", ns, v, "n**2 * (n-1)**2", ["n**3", "n**4*log(n)"], 0.03)

print("\n== APSP: Floyd-Warshall (claim n**3) ==")
for ns in ([16, 32, 48, 64, 96, 128], [32, 48, 64, 96, 128, 160, 200]):
    v = H.counts(AP, FW, ns, 1)
    print("  exactly n^3 - n:", all(int(c) == n ** 3 - n for n, c in zip(ns, v)))
    H.report("tol=0.03", ns, v, "n**3", ["n**2 * (n-1)**2", "n**2.5", "n**3*log(n)"], 0.03)

sm_dir, sm_entry, sm_h = H.entry_and_harness(SM)
print("\n== strings: answers unchanged by the instrumentation ==")
for name in (NA, KMP):
    fn = H.V.load_callable(sm_dir, H.algorithm(sm_entry, name)["implementation"])
    for n in (6, 50, 301):
        t, p = sm_h.generate_scaling(n, random.Random(0))
        ts, ps = "".join(c.c for c in t), "".join(c.c for c in p)
        print(f"  {name}, n={n}: tuple answer {fn((t, p))}, str answer {fn((ts, ps))}")
    rng = random.Random(7)
    agree = True
    for trial in range(200):
        n = rng.randint(0, 40)
        ts = "".join(rng.choice("ab") for _ in range(n))
        ps = "".join(rng.choice("ab") for _ in range(rng.randint(1, 5)))
        agree &= fn((tuple(sm_h.CountingChar(c) for c in ts), tuple(sm_h.CountingChar(c) for c in ps))) == fn((ts, ps))
    print(f"  {name}: 200 random small (text, pattern) pairs, tuple answers == str answers: {agree}")

print("\n== strings: naive (claim n**2) ==")
ns = [200, 400, 800, 1600, 3200]
v = H.counts(SM, NA, ns, 1)
print("  exactly (n - m + 1) m:", all(int(c) == (n - n // 2 + 1) * (n // 2) for n, c in zip(ns, v)))
H.report("tol=0.03", ns, v, "n**2", ["n", "n*log(n)", "n**2*log(n)"], 0.03)

print("\n== strings: KMP (claim n) ==")
ns = [3000, 10000, 30000, 100000, 300000]
v = H.counts(SM, KMP, ns, 1)
print("  exactly 3n + 2m - 6:", all(int(c) == 3 * n + 2 * (n // 2) - 6 for n, c in zip(ns, v)), [int(c) for c in v])
H.report("tol=0.03", ns, v, "n", ["n*log(n)", "n**2", "n/log(n)"], 0.03)

