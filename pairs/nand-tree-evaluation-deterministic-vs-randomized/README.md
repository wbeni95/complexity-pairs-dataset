# NAND-tree evaluation: deterministic vs randomized leaf reads

**Type:** T4 (randomized ↔ deterministic), secondary T3 · **Verification:** V2 (exact leaf-read counts)

Evaluate a complete binary NAND tree of height h (N = 2ʰ leaves). The cost is the number of leaf reads.
Answers must always be correct.

| Algorithm | Leaf reads, worst case | Lower bound in its model | Implementation |
|---|---|---|---|
| Deterministic left-first | 2ʰ = N | N (adversary argument, proved in the entry) | [left_first.py](implementations/left_first.py) |
| Randomized random order (Snir) | Θ(λʰ) expected, λ = (1+√33)/4 ≈ 1.686, i.e. N^0.7537 | Ω(λʰ) for zero-error algorithms (Saks & Wigderson 1986) | [random_order.py](implementations/random_order.py) |

**Why it's here.** Randomisation changes the exponent. Every deterministic algorithm must read all N leaves on some
input (proved in the entry), while the zero-error randomized algorithm here needs only Θ(N^0.7537) reads in
expectation, which is optimal for zero-error algorithms by the cited lower bound of Saks & Wigderson (1986; not proved
here). The tag follows RESEARCH_LOG RL-042: T4 primary, with T3 secondary because the
gap is polynomial to a smaller polynomial in N. The expected cost on the worst-case ("reluctant") inputs obeys
R0(h) = 2R1(h−1), R1(h) = R0(h−1) + R1(h−1)/2, whose dominant eigenvalue is λ.

**Verification.** V1: both agree with a full bottom-up evaluation on random and reluctant inputs. V2: an
instrumented leaf sequence counts reads on the right-zero reluctant input, which is worst case for both.
- Left-first: exactly 2ʰ reads, α = 1.000.
- Randomized: means of 200 seeded runs per h give α = 0.995 against λʰ, at tolerance 0.05. The rival 2ʰ fits at
  0.750 and is rejected.
- Tolerance: the exact expectations give α = 0.998. Over 40 other seed sets, α ranged from 0.989 to 1.008.

See `experiments/2026-10-07b_nand_tree_counts.py`.

**Sources.** Saks & Wigderson, FOCS 1986, 29–38. The optimality statement was confirmed through secondary
summaries; the paper text was not read.
