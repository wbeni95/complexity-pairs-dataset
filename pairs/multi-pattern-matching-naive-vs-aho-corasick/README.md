# Multi-pattern string matching: naive per pattern vs KMP per pattern vs Aho–Corasick

**Type:** T3 (poly → faster poly) · **Verification:** V2 (exact character-comparison counts, with rivals)

**Problem.** Given a text of length N and P non-empty patterns of total length L, count for every pattern how often
it occurs in the text. Overlapping occurrences all count, and the counts come back in the order of the patterns.

| Algorithm | Comparisons | V2 family (text a^(n²), patterns a^(j−1)b, j = 1..n) | Implementation |
|---|---|---|---|
| Naive matching per pattern | O(N·L) | exactly n(n+1)(3n²−2n+2)/6 = Θ(n⁴) | [naive.py](implementations/naive.py) |
| KMP per pattern | Θ(P·N + L) (N ≥ 1) | exactly 3n³−2n²−5n+6 = Θ(n³) (n ≥ 2) | [kmp_each.py](implementations/kmp_each.py) |
| Aho–Corasick | Θ(N + L) (fixed alphabet, P ≥ 1) | exactly 4n²−3 = Θ(n²) (n ≥ 1) | [aho_corasick.py](implementations/aho_corasick.py) |

The input of the V2 family has s = Θ(n²) characters, so the chain is Θ(s²) → Θ(s^1.5) → Θ(s).

**Why it works.** Aho–Corasick builds one automaton for all patterns: the trie of the patterns plus failure links.
The failure link of a node points to the longest proper suffix of its string that is also in the trie. After each
text character, the current state is the longest suffix of the text read so far that is a trie node. A pattern ends
at that position exactly when its node lies on the state's chain of failure links. Counting visits per state and
summing them up the failure tree, in reverse breadth-first order, gives every pattern's count. The work does not
depend on the number of occurrences: the text a^1024 with patterns a, …, a^32 has 32 272 occurrences, yet costs 1551
comparisons.

**Verification.**
- *V1:* the validator runs P = 0..6, 8, 12, 20 and 40 patterns, 8 instances per size. The texts are random or
  periodic over 2–3 letters. The patterns include substrings, prefixes and suffixes of one another, duplicates, and
  patterns longer than the text. The oracle counts every pattern with `str.find`, stepping one past each match.
- *Experiment* ([2026-10-06i_aho_corasick.py](../../experiments/2026-10-06i_aho_corasick.py)):
  - 1500 extra instances, 0 failures;
  - an oracle control: 4556 deliberately wrong outputs rejected and 480 correct ones accepted. The wrong outputs
    include an off-by-one count, non-overlapping counts, reversed order, counts of reversed patterns, and wrong types
    or lengths;
  - the closed forms checked up to n = 40, 70 and 300;
  - Aho–Corasick's build cost (n² + n − 4) and scan cost (3n² − n + 1), both for n ≥ 2, checked separately.
- *V2:* CountingChar counts every == and != between characters, and the implementations are unchanged.

  | Algorithm | Fitted on | Rivals |
  |---|---|---|
  | Naive | n = 8..32 | n³, n⁵ |
  | KMP per pattern | n = 8..64 | n², n⁴ |
  | Aho–Corasick | n = 16..256 | n³, n² log n, n |

  Shape blocks on consecutive grids check the exact polynomial degree.

**Caveats.** Only character comparisons are counted. Aho–Corasick keeps each node's children in a list, which costs
up to σ comparisons per lookup, so its bound is Θ(N + L) for a fixed alphabet and P ≥ 1 (with no patterns it compares
nothing) and O(σ(N + L)) in general. Reporting each occurrence individually needs at least one step per occurrence;
this implementation returns counts only.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: the exact comparison counts for all sizes of
their domains, the correctness of the three algorithms (for Aho–Corasick the trie, the failure links, the scan
invariant and the accumulation; for KMP by reference to the identical code proved in
[string-matching-naive-vs-kmp](../string-matching-naive-vs-kmp/PROOFS.md)), the naive worst case N·L, Θ(P·N + L) for
KMP per pattern, the bounds and space of Aho–Corasick and the caveats. It names the checks: the count-check scripts
and [tests/test_proofs_aho_corasick.py](../../tests/test_proofs_aho_corasick.py).

**Sources.** Aho & Corasick, CACM 1975. Knuth, Morris & Pratt, SIAM J. Comput. 1977.
