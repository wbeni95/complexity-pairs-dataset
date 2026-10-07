<!-- generated from entry.json by tools/build_index.py; edit entry.json, not this file -->
# Linear programming: simplex vs ellipsoid / interior-point methods

**Type:** T1, T6 (exp → poly) · **Verification:** V0

**Problem.** Given A in Q^(m x n), b in Q^m, c in Q^n, maximise c^T x subject to Ax <= b, x >= 0 (or report infeasible / unbounded).

**Input.** n variables, m constraints; L = total bit length of (A, b, c). Size: L bits.

| Algorithm | Model | Time | Space |
|---|---|---|---|
| simplex method (Dantzig's pivot rule) | classical-deterministic | exponential in the worst case: 2^n - 1 pivots on the Klee-Minty cube | O(mn) numbers |
| ellipsoid method | classical-deterministic | polynomial in n and L: O(n^2 L) iterations of O(n^2) arithmetic operations | O(n^2) numbers of O(L) bits |
| interior-point method (Karmarkar) | classical-deterministic | O(n^3.5 L) arithmetic operations | O(mn) numbers |

**Relationship.** Simplex with Dantzig's pivot rule takes 2^n - 1 pivots on the Klee-Minty cube, so it is exponential in the worst case (cited); worst-case constructions for other pivot rules are not cited here. Ellipsoid and interior-point methods are polynomial in the input bit length L (cited).

**Caveats.** Ellipsoid and interior-point methods are WEAKLY polynomial (polynomial in L, not only in n and m). Whether LP has a STRONGLY polynomial algorithm is open (Smale's 9th problem), hence secondary tag T6. Whether some simplex pivot rule is polynomial is also open. In practice simplex is fast; smoothed analysis (Spielman-Teng) explains part of this.

**Notes.** Not implemented; the costs are as stated in the cited sources.

**Verification.** Cited from the literature; not independently implemented.

**Sources.**

- Dantzig, G. B. (1951). *Maximization of a linear function of variables subject to linear inequalities*. Activity Analysis of Production and Allocation (T. C. Koopmans, ed.), Wiley, 339-347.
- Klee, V.; Minty, G. J. (1972). *How good is the simplex algorithm?*. Inequalities III (O. Shisha, ed.), Academic Press, 159-175.
- Khachiyan, L. G. (1979). *A polynomial algorithm in linear programming*. Doklady Akademii Nauk SSSR 244(5), 1093-1096 (English: Soviet Mathematics Doklady 20, 191-194).
- Karmarkar, N. (1984). *A new polynomial-time algorithm for linear programming*. Combinatorica 4(4), 373-395. [doi:10.1007/BF02579150](https://doi.org/10.1007/BF02579150)
- Spielman, D. A.; Teng, S.-H. (2004). *Smoothed analysis of algorithms: Why the simplex algorithm usually takes polynomial time*. Journal of the ACM 51(3), 385-463. [doi:10.1145/990308.990310](https://doi.org/10.1145/990308.990310)
