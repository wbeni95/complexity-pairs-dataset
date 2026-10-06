"""Probe for pairs/longest-palindromic-substring.

Part 1 (deterministic): exact character-comparison counts of instrumented copies of the three algorithms
on the worst-case family a^n and on random strings over {a, b}, to check the stated cost formulas:
  brute force on a^n: sum_{L=1..n} (n - L + 1) floor(L/2) ~ n^3/12;
  expand around centers on a^n: ~ n^2/2;
  Manacher: <= 4n comparisons on every input (at most n successful + n failed per scan, two scans).
Part 2 (timing, console): validator-style timing fits on a^n to choose n ranges for entry.json.

Run from the repository root:  python experiments/2026-10-07_palindrome_probe.py

Outcome (2026-10-07). Part 1 is deterministic: on a^n the brute-force count equals the formula exactly
(95 / 5530 / 344520 / 2743440 for n = 10 / 40 / 160 / 320), expansion makes exactly n^2/2 + n/2
(55 / 820 / 12880 / 51360) and Manacher 2n - 3 (17 / 77 / 317 / 637). On one random {a, b} string per n:
brute force 58 / 1449 / 24494 / 100431 (about n^2), expansion 39 / 177 / 794 / 1596 (about 5n), Manacher
26 / 127 / 548 / 1095 (<= 4n). A first draft of Part 1 built the "random" string with a fresh Random per
character, which made it constant (identical counts to a^n); fixed before any number was used.
Part 2 (console): brute force alpha = 0.945 over n = 30..240 (local slopes 0.86..1.0), then 0.968 over
n = 40..320 (chosen); expansion alpha = 1.009 over n = 200..6400 (6400 takes 0.77 s, so entry.json stops at
3200); Manacher alpha = 1.004 on a^n and 0.960 on the mixed random strings of generate(), n = 3000..300000.
"""
import importlib.util
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("probe_helpers", ROOT / "experiments" / "2026-10-07_probe_helpers.py")
ph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph)


def brute_count(s):
    n, c = len(s), 0
    for i in range(n):
        for j in range(i, n):
            lo, hi = i, j
            while lo < hi:
                c += 1
                if s[lo] != s[hi]:
                    break
                lo += 1
                hi -= 1
    return c


def expand_count(s):
    n, c = len(s), 0
    for ctr in range(2 * n - 1):
        lo = ctr // 2
        hi = lo + (ctr % 2)
        while lo >= 0 and hi < n:
            c += 1
            if s[lo] != s[hi]:
                break
            lo -= 1
            hi += 1
    return c


def manacher_count(s):
    n, c = len(s), 0
    d1, l, r = [0] * n, 0, -1
    for i in range(n):
        k = 1 if i > r else min(d1[l + r - i], r - i + 1)
        while i - k >= 0 and i + k < n:
            c += 1
            if s[i - k] != s[i + k]:
                break
            k += 1
        d1[i] = k
        if i + k - 1 > r:
            l, r = i - k + 1, i + k - 1
    d2, l, r = [0] * n, 0, -1
    for i in range(n):
        k = 0 if i > r else min(d2[l + r - i + 1], r - i + 1)
        while i - k - 1 >= 0 and i + k < n:
            c += 1
            if s[i - k - 1] != s[i + k]:
                break
            k += 1
        d2[i] = k
        if i + k - 1 > r:
            l, r = i - k, i + k - 1
    return c


print("Part 1: comparison counts")
for n in (10, 40, 160, 320):
    a = "a" * n
    exact_brute = sum((n - L + 1) * (L // 2) for L in range(1, n + 1))
    rng = random.Random(f"pal|{n}")   # first draft re-created the Random per character -> constant string (bug, fixed)
    rnd = "".join(rng.choice("ab") for _ in range(n))
    print(f"  n={n}: a^n brute {brute_count(a)} (formula {exact_brute}, n^3/12 = {n ** 3 / 12:.0f}); "
          f"expand {expand_count(a)} (n^2/2 = {n * n / 2:.0f}); manacher {manacher_count(a)} (4n = {4 * n})")
    print(f"         random {{a,b}}: brute {brute_count(rnd)}, expand {expand_count(rnd)}, manacher {manacher_count(rnd)}")

print("Part 2: timing on a^n")
E = "longest-palindromic-substring"
ns = [40, 60, 80, 120, 160, 240, 320]   # first draft: 30..240 gave alpha 0.945, local slopes 0.86..1.0
a, t = ph.probe(E, "implementations/brute_force.py:lps_brute", "generate_scaling", "n**3", ns)
print("  local slopes:", [round(x, 3) for x in ph.local_slopes(ns, t, "n**3")])
ns = [200, 400, 800, 1600, 3200, 6400]
a, t = ph.probe(E, "implementations/expand_centers.py:lps_expand", "generate_scaling", "n**2", ns)
print("  local slopes:", [round(x, 3) for x in ph.local_slopes(ns, t, "n**2")])
ns = [3000, 10000, 30000, 100000, 300000]
a, t = ph.probe(E, "implementations/manacher.py:lps_manacher", "generate_scaling", "n", ns)
print("  local slopes:", [round(x, 3) for x in ph.local_slopes(ns, t, "n")])
ns = [3000, 10000, 30000, 100000, 300000]
a, t = ph.probe(E, "implementations/manacher.py:lps_manacher", "generate", "n", ns, label="manacher on mixed random strings")
