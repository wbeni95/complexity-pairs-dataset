# Closest pair of points: brute force vs divide and conquer

**Type:** T3 (poly → faster poly) · **Verification:** V2

**Problem.** Given n ≥ 2 points with integer coordinates, return the minimum squared Euclidean distance
between two of them. Integers keep the answer exact.

| Algorithm | Time (n points) | Implementation |
|---|---|---|
| All pairs | Θ(n²) | [brute_force.py](implementations/brute_force.py) |
| Shamos–Hoey divide and conquer | Θ(n log n) | [divide_conquer.py](implementations/divide_conquer.py) |

**Why it's a pair.** After solving both halves, only points within δ of the dividing line can form a
closer pair, and in y order each one needs only a constant number of comparisons. The y-sorted lists are
merged on the way up rather than re-sorted, so the cost is n log n and not n log² n.

**Optimality.** Ω(n log n) in the algebraic computation-tree model (Ben-Or 1983, via element uniqueness).
Randomized grid hashing with the floor function gets expected O(n) (Rabin 1976; Khuller & Matias 1995).

**Verification.** V1: both agree with each other and with an independent plane-sweep oracle, including
duplicate points and points that all lie on one vertical line. V2: runtimes fit n² and n log n.

**Sources.** Shamos & Hoey 1975 (FOCS). Bentley & Shamos 1976 (STOC). Ben-Or 1983. Rabin 1976. Khuller & Matias 1995.
