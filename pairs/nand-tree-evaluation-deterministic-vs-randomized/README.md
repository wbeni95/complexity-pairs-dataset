# NAND-tree evaluation: deterministic vs randomized leaf reads

**Type:** T4 (randomized ↔ deterministic), secondary T3 · **Verification:** V2 (exact leaf-read counts)

Evaluate a complete binary NAND tree of height h (N = 2ʰ leaves). The cost is the number of leaf reads.
Answers must always be correct.

| Algorithm | Leaf reads, worst case | Lower bound in its model | Implementation |
|---|---|---|---|
| Deterministic left-first | 2ʰ = N | N (adversary argument, proved in the entry) | [left_first.py](implementations/left_first.py) |
| Randomized random order | Θ(λʰ) expected, λ = (1+√33)/4 ≈ 1.686, i.e. N^0.7537 (proved in the entry) | optimal among zero-error algorithms (Saks & Wigderson 1986; cited, background) | [random_order.py](implementations/random_order.py) |

**Why it's here.** Randomisation changes the exponent. Every deterministic algorithm must read all N leaves on some
input (proved in the entry), while the zero-error randomized algorithm here needs only Θ(N^0.7537) reads in
expectation, which is optimal for zero-error algorithms by the cited lower bound of Saks & Wigderson (1986; not proved
here). The tag follows RESEARCH_LOG RL-042: T4 primary, with T3 secondary because the
gap is polynomial to a smaller polynomial in N. The expected cost on the worst-case ("reluctant") inputs obeys
R0(h) = 2R1(h−1), R1(h) = R0(h−1) + R1(h−1)/2, whose dominant eigenvalue is λ. For h ≥ 1, R0(h) > R1(h): the worst case
is a reluctant input with root value 0.

**Verification.** V1: both agree with a full bottom-up evaluation on random and reluctant inputs. V2: an
instrumented leaf sequence counts reads on the right-zero reluctant input with root value 1. It is a worst case for
the left-first algorithm; for the randomized algorithm it is the worst case among inputs with root value 1 (expected
R1(h) reads), below the overall worst case R0(h) by a bounded factor, so the fitted exponent is the same.
- Left-first: exactly 2ʰ reads, α = 1.000.
- Randomized: means of 200 seeded runs per h give α = 0.995 against λʰ, at tolerance 0.05. The rival 2ʰ fits at
  0.750 and is rejected.
- Tolerance: the exact expectations give α = 0.998. Over 40 other seed sets, α ranged from 0.989 to 1.008.

See `experiments/2026-10-07b_nand_tree_counts.py`.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry except the cited randomized lower bound: the
exact count of the left-first algorithm, the correctness of both algorithms, the deterministic lower bound (adversary
argument), and the worst-case expected cost R0(h) = Θ(λʰ) of the randomized algorithm. It names the deterministic
checks of each ([tests/test_proofs_query.py](../../tests/test_proofs_query.py), the experiment and the count-check
scripts).

**Background (cited, not proved here).** In the Hamiltonian oracle model, a continuous-time quantum walk evaluates
the tree in time proportional to √N (Farhi, Goldstone & Gutmann, Theory of Computing 2008).

**Sources.** Saks & Wigderson, FOCS 1986, 29–38. The optimality statement was confirmed through secondary
summaries; the paper text was not read. Farhi, Goldstone & Gutmann, *A quantum algorithm for the Hamiltonian NAND
tree*, Theory of Computing 4 (2008), 169–190.
