# Methodology note: AlphaDev and constant-factor improvements

**Not an entry.** START_HERE section 1 requires an *asymptotic* difference. For a fixed sequence
length k, both the human-written and the discovered routine are O(1), so this is out of scope as a
pair (decision of 2026-10, see CONTRIBUTING.md). It is recorded here because it is the closest
published example of the search pipeline described in START_HERE section 5.

## What was done

Mankowitz et al. (2023) framed assembly-program construction as a single-player game. A deep-RL
agent extended a program instruction by instruction and was rewarded for correctness on all inputs
and for low measured latency. For sort3, sort4 and sort5 (branchless sorting routines in LLVM libc++)
it found shorter instruction sequences than the human-optimised baseline. One example is sort3 in 17
instead of 18 instructions, using the "AlphaDev swap move". The routines were merged into libc++.
The paper reports up to 70% speedups for short sequences and about 1.7% for sequences of more than
250,000 elements in the library sort that calls them.

## Why it matters here

- **Exact verifier.** For fixed k, a candidate that is a network of compare-exchange (min/max) operations can be
  checked exhaustively: by the 0-1 principle (cited, not proved here) its correctness reduces to the 2^k inputs of
  0s and 1s. This is the property START_HERE section 5 asks for.
- **A proposer, not an oracle.** The learned agent proposes, and the exact check decides (START_HERE section 6).

## When fixed-size results *are* in scope

A fixed-size scheme enters the dataset when applying it recursively yields an asymptotic bound. For example, if
a rank-47 bilinear scheme for 4×4 matrix multiplication over GF(2) exists, as AlphaTensor reports (Fawzi et al.
2022, background), then ω ≤ log₄ 47 ≈ 2.7773 in characteristic 2 (see
`pairs/matrix-multiplication-naive-vs-strassen`).

## Source

Mankowitz, D. J.; Michi, A.; Zhernov, A.; et al. (2023). *Faster sorting algorithms discovered using deep
reinforcement learning*. Nature 618, 257–263. [doi:10.1038/s41586-023-06004-9](https://doi.org/10.1038/s41586-023-06004-9)
