# Deutsch–Jozsa: 2ⁿ⁻¹+1 exact classical queries vs 1 exact quantum query

**Type:** T9 (quantum separation, query model) · **Verification:** V2 (query counts)

> **Read this first.** The exponential gap is against **exact** (zero-error) classical algorithms only.
> A classical randomized algorithm that may err with small probability needs only **O(1)** queries.
> Deutsch–Jozsa therefore does **not** separate bounded-error classical from quantum computation.

**Problem.** f: {0,1}ⁿ → {0,1} is promised to be constant or balanced (exactly half zeros). Decide which.

| Algorithm | Model | Queries | Error | Implementation |
|---|---|---|---|---|
| Scan until a difference or a majority | classical, deterministic | **2ⁿ⁻¹ + 1** worst case (optimal for exact algorithms); ≤ 3 on average over random balanced f (→ 3 as n grows) | none | [classical.py](implementations/classical.py) |
| K = 20 random queries | classical, randomized | **20** for every n (O(log 1/ε)) | one-sided, 2¹⁻ᴷ = 2⁻¹⁹ on balanced f | [randomized.py](implementations/randomized.py) |
| Deutsch–Jozsa (one-query form) | quantum | **1** | none | [quantum.py](implementations/quantum.py) |

**The exact lower bound (adversary argument).** Let any exact classical algorithm run, and answer 0 to each of its
first 2ⁿ⁻¹ distinct queries. Both the constant-0 function and the balanced function that is 1 exactly on the
unqueried points are consistent with those answers, so the algorithm cannot yet answer with certainty. It needs
2ⁿ⁻¹ + 1 queries. The same argument applies to every run of a zero-error randomized algorithm on a constant input.

**Why randomness removes the gap.** For a balanced f, each random query is a fair coin, so K random queries all
agree with probability 2¹⁻ᴷ. For a constant f they always agree. Checked empirically: error rates for k = 2, 3, 4, 6, 8
match 2¹⁻ᵏ with |z| ≤ 0.98 ([experiment](../../experiments/2026-10-07_deutsch_jozsa_checks.py)).

**Why one quantum query suffices.** After H⊗ⁿ, one phase query and H⊗ⁿ, the amplitude of |0…0⟩ is
(1/N)·Σₓ(−1)^f(x), which is ±1 for constant f and exactly 0 for balanced f.

**How it is verified.** Exact state-vector simulation ([lib/qsim.py](../../lib/qsim.py)) with a shared counting oracle.
V1 checks every answer against the full truth table. V2 fits query counts. The deterministic algorithm is measured on
the **worst-case inputs for its fixed query order 0, 1, 2, …**: the two constant functions and the two balanced
functions f(x) = c ⊕ (top bit of x). An exhaustive check over all promise inputs for n = 1..4 confirms that the
maximum is 2ⁿ⁻¹ + 1 and is attained on exactly these four inputs.

**Caveats.** This is a promise problem, and the separation is relative to an oracle. It is an exact-vs-exact separation.
It does not imply BQP ≠ BPP and does not even separate bounded-error query complexities.

**Sources.** Deutsch & Jozsa, *Rapid solution of problems by quantum computation*, Proc. R. Soc. A 1992.
Cleve, Ekert, Macchiavello & Mosca, *Quantum algorithms revisited*, Proc. R. Soc. A 1998 (the one-query form).
