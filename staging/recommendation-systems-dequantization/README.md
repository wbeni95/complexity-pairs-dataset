<!-- generated from entry.json by tools/build_index.py; edit entry.json, not this file -->
# Recommendation systems: Kerenidis-Prakash quantum algorithm vs Tang's dequantization

**Type:** T5 (quantum → classical) · **Verification:** V0

**Problem.** Given an m x n preference matrix with a good rank-k approximation, stored in a data structure supporting the needed sampling access, output a sample from (approximately) the row of a low-rank approximation corresponding to a given user, i.e. a recommendation.

**Input.** m users, n products, target rank k, accuracy eps. Size: The matrix (mn entries) is preprocessed into a data structure; complexities count queries/time AFTER preprocessing.

| Algorithm | Model | Time | Space |
|---|---|---|---|
| Kerenidis-Prakash quantum recommendation algorithm | quantum | poly(k) polylog(mn) (for constant accuracy), given QRAM access | QRAM data structure of size Õ(mn) |
| Tang's quantum-inspired classical algorithm | classical-randomized | poly(k, 1/eps) polylog(mn), given sample-and-query access (a high-degree polynomial in the original analysis) | Data structure of size Õ(mn) |

**Relationship.** The claimed exponential quantum speedup disappears: with comparable input access (sample-and-query vs QRAM), a classical algorithm also runs in time polylogarithmic in mn. At most a polynomial quantum advantage remains.

**Caveats.** The comparison depends entirely on the input model: both algorithms assume a preprocessed data structure. Without it, reading the matrix already costs Theta(mn).

**Notes.** Key evidence for the classical-vs-quantum question: a case where a claimed exponential quantum advantage was dequantized. Contrast with integer-factoring and discrete-logarithm (no dequantization known).

**Verification.** Cited from the literature.

**Sources.**

- Kerenidis, I.; Prakash, A. (2017). *Quantum Recommendation Systems*. ITCS 2017, LIPIcs 67, 49:1-49:21. [doi:10.4230/LIPIcs.ITCS.2017.49](https://doi.org/10.4230/LIPIcs.ITCS.2017.49) [arXiv:1603.08675](https://arxiv.org/abs/1603.08675)
- Tang, E. (2019). *A quantum-inspired classical algorithm for recommendation systems*. STOC 2019. [doi:10.1145/3313276.3316310](https://doi.org/10.1145/3313276.3316310) [arXiv:1807.04271](https://arxiv.org/abs/1807.04271)
- Chia, N.-H.; Gilyén, A.; Li, T.; Lin, H.-H.; Tang, E.; Wang, C. (2022). *Sampling-based Sublinear Low-rank Matrix Arithmetic Framework for Dequantizing Quantum Machine Learning*. Journal of the ACM 69(5). [doi:10.1145/3549524](https://doi.org/10.1145/3549524) [arXiv:1910.06151](https://arxiv.org/abs/1910.06151)
