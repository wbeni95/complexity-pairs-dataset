# Longest palindromic substring: brute force vs expanding around centers vs Manacher

**Type:** T3 (poly → faster poly) · **Verification:** V2

**Problem.** Given a string of length n, return the length of its longest palindromic substring and the
leftmost position where one starts.

| Algorithm | Time (worst case) | Implementation |
|---|---|---|
| Brute force (test every substring) | Θ(n³) | [brute_force.py](implementations/brute_force.py) |
| Expand around the 2n − 1 centers | Θ(n²) | [expand_centers.py](implementations/expand_centers.py) |
| Manacher (1975) | Θ(n) | [manacher.py](implementations/manacher.py) |

**Why it's a chain of pairs.** Palindromes that share a center are nested, so one expansion per center
replaces testing every substring. Manacher then reuses the radius of the mirrored center inside the
rightmost palindrome found so far. Every successful comparison pushes that palindrome's right end
forward, so the total work is linear.

**Worst case matters.** On random strings the cubic and quadratic algorithms are far below their bounds
(Θ(n²) and Θ(n) in expectation), so V2 times all three on aⁿ. There every substring is a palindrome.
The probe counts comparisons exactly on aⁿ: Σ(n−L+1)⌊L/2⌋ ≈ n³/12 for brute force, n²/2 + n/2 for
expansion and 2n − 3 for Manacher (for every n ≥ 2: n − 2 in the odd-length scan and n − 1 in the even-length
scan; proof sketch in `entry.json`).

**Verification.** V1: the three agree with each other and with an independent oracle that verifies the
answer directly (the reported substring is a palindrome, no window one or two characters longer is, and
no equally long palindrome starts earlier). V2: runtimes on aⁿ fit n³, n² and n.

**Sources.** Manacher, J. ACM 22(3), 1975. The paper's stated application is the smallest initial
palindrome. Apostolico, Breslauer & Galil, TCS 141, 1995 (all maximal palindromes). The attribution
of the "all maximal palindromes" observation to them comes from a secondary source.
