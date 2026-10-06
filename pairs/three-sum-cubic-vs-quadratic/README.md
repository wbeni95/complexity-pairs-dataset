# 3SUM: all triples vs sort + two pointers

**Type:** T3 (poly → faster poly) · **Verification:** V2

| Algorithm | Time | Implementation |
|---|---|---|
| All triples | Θ(n³) worst case | [brute_force.py](implementations/brute_force.py) |
| Sort + two pointers | Θ(n²) | [sort_two_pointers.py](implementations/sort_two_pointers.py) |

**The boundary.** The 3SUM conjecture says no O(n^(2−ε)) algorithm exists, and many geometric problems
are "3SUM-hard" relative to it. Grønlund–Pettie (2014) shaved polylogarithmic factors off n², and linear
decision trees need only O(n log² n) comparisons (Kane–Lovett–Moran). The conjecture is therefore about
algorithms, not about information.

**Verification.** V1 against an independent hash-based oracle. V2 on worst-case (no-solution) inputs.

**Sources.** Gajentaan & Overmars 1995. Grønlund & Pettie, J. ACM 2018. Kane, Lovett & Moran, J. ACM 2019.
