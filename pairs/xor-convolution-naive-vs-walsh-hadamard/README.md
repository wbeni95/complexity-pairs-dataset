# XOR convolution: all index pairs vs the fast Walsh–Hadamard transform

**Type:** T3 (poly → faster poly) · **Verification:** V2 (exact operation counts with rivals)

h[k] = Σ over i ⊕ j = k of a[i]·b[j], for two integer vectors of length N = 2ⁿ.

| Algorithm | Ring operations (counted, exact) | Time | Implementation |
|---|---|---|---|
| All index pairs | 2·4ⁿ | Θ(4ⁿ) = Θ(N²) | [naive.py](implementations/naive.py) |
| Fast Walsh–Hadamard transform | (3n + 2)·2ⁿ | Θ(n·2ⁿ) = Θ(N log N) | [fwht.py](implementations/fwht.py) |

**Why it's here.** The Walsh–Hadamard matrix W[x][y] = (−1)^(x·y) diagonalises XOR convolution, exactly as the
DFT diagonalises cyclic convolution: W(a∗b) = (Wa)·(Wb), and W·W = N·I. The FWHT applies W in n butterfly
stages, one per bit. The input has N = 2ⁿ entries, so both costs are polynomial in the input size (T3, not an
exponential pair).

**Quantum link, stated precisely.** W = 2^(n/2)·H^⊗n, the Hadamard transform of Deutsch–Jozsa, Bernstein–Vazirani
and Forrelation. One FWHT stage corresponds to one Hadamard gate. A classical machine pays 2ⁿ additions per stage
(this is how `lib/qsim.py` simulates H^⊗n); a quantum circuit pays one gate. That is **not** a quantum speed-up
for computing W·v: a quantum computer does not output the 2ⁿ transformed values, it only samples an index with
probability |amplitude|². The quantum advantages in those entries are in oracle queries. Forrelation's Φ(f, g) is
computed exactly classically by one FWHT once all 2N values have been read.

**Verification.** V1: both implementations agree for n = 0..8 and 11, and pass an independent oracle that checks
the convolution theorem character by character with popcount parities (all 2ⁿ characters for n ≤ 8, which
determines h uniquely; 48 random characters at n = 11). V2: an instrumented integer type counts every +, −, ×, //
of the unchanged implementations. The counts equal 2·4ⁿ and (3n + 2)·2ⁿ at every measured n. Fits at tolerance
0.05: naive α = 1.000 (rivals n·2ⁿ 1.587, n·4ⁿ 0.885: rejected); FWHT α = 0.987 against n·2ⁿ (rivals 2ⁿ 1.162,
n²·2ⁿ 0.858, 4ⁿ 0.581: rejected). See `experiments/2026-10-07b_xor_convolution_counts.py`.

**Sources.** Fino & Algazi, IEEE Trans. Computers C-25 (1976). Bernstein & Vazirani, SIAM J. Comput. 26 (1997),
for the quantum Hadamard step.
