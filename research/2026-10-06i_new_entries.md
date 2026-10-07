Author: delegated research agent (Claude), for the maintainer.

# Round 2026-10-06i: three known pairs added as entries

Date: 2026-10-06. Environment: Windows 11 Pro 10.0.26200, CPython 3.14.2 (project venv, jsonschema only). The
cross-version checks also used CPython 3.12.10. One sub-agent (Claude) wrote the 3XOR entry to a fixed design; its
validator checks, experiment and tests were re-run by the agent that directed it. Every V2 in this round uses exact
counts.

## 1. Summary

| Entry (pairs/…) | Tags | V2 α per algorithm (exact counts, tol 0.02) | Rivals, all rejected (α) | Shape |
|---|---|---|---|---|
| multi-pattern-matching-naive-vs-aho-corasick | T3 | naive 1.000; KMP per pattern 1.000; Aho–Corasick 1.000 | n³ 1.326, n⁵ 0.796; n² 1.523, n⁴ 0.762; n³ 0.667, n² log n 0.890, n 2.001 | 3 × MATCH: n⁴, n³, n² |
| linear-ordering-enumeration-vs-subset-dp | T6 + T8 | enumeration 1.000; subset DP 1.000 | n!·n 1.089, n!·n³ 0.932, n²2ⁿ 2.129; n2ⁿ 1.108, n³2ⁿ 0.877, 3ⁿ 0.804, n! 0.377 | DP: MATCH n²·2ⁿ (n = 2..15); enumeration: no block (factorial) |
| three-xor-all-triples-vs-patricia-trie (*sub-agent*, re-run) | T3 | all triples 1.000; Patricia trie 1.000 | n² 1.500, n³ log n 0.929, n⁴ 0.750; n³ 0.664, n² log n 0.911, n log n 1.678 | 2 × MATCH: n³ (doubling n = 1..512), n² (doubling n = 1..2048) |

All α values come from `tools/validate.py --scaling -v pairs/<id>`.
- **V2:** 7 fits, all α = 1.000, because every cost expression is the exact closed form of the count (RL-062).
- **Rivals:** 20 declared, 20 rejected; the closest per entry are |α − 1| = 0.110, 0.068 and 0.071. The log-factor
  diagnostic is resolved in all 7 fits.
- **Shape diagnostic:** 6 MATCH, 0 MISMATCH, 0 UNDETERMINED. The linear-ordering enumeration series has no block,
  because factorial growth is outside the diagnostic's family.
- **Oracle controls:** 9993 deliberately wrong outputs rejected, 0 accepted (4556 + 2460 + 2977; per entry in sections 2–4).
- **Cross-version:** the count series of all three entries are identical under CPython 3.12.10 and 3.14.2 (section 6).
- **Citations:** 8 sources, 10 identifiers, 0 problems (section 5).

## 2. Multi-pattern matching: multi-pattern matching, naive vs KMP per pattern vs Aho–Corasick

**Problem.** Count the overlapping occurrences of every pattern in a text; the output is a tuple. n = number of
patterns.

**Choice of cost parameter and family.** Text a^(n²), patterns a^(j−1)b for j = 1..n. Then N = n² and
L = n(n+1)/2, so the input has s = Θ(n²) characters. This family is the naive matcher's worst case for every pattern,
and text length and total pattern length grow together. The gap is Θ(n⁴) → Θ(n³) → Θ(n²), i.e. Θ(s²) → Θ(s^1.5) →
Θ(s). KMP per pattern is included as the strongest per-pattern rival: it is linear per pattern but reads the text P
times.

**Unit.** Character comparisons (== and !=) through CountingChar tuples, with the implementations unchanged.
Aho–Corasick stores children as (character, node) lists scanned linearly, so its lookups are character comparisons as
well. A dict-based trie would have made the count depend on CPython's hashing.

**Exact counts:**
- **Naive:** Σ_j j(n² − j + 1) = n(n+1)(3n² − 2n + 2)/6, for n = 1..20 and up to n = 40.
- **KMP per pattern:** 3n³ − 2n² − 5n + 6 for n ≥ 2 (checked up to n = 70). Pattern b costs N, pattern ab costs 2N,
  and for j ≥ 3 the failure table costs 3j − 6 and the scan 3N − j. These per-pattern forms were derived by hand from
  the loop structure; at n = 1 the count is 1, not 2.
- **Aho–Corasick:** 4n² − 3 for n = 1..20 and up to n = 300.
  - Building costs (n−1)² + (3n − 5) = n² + n − 4, measured with an empty text at n = 2, 5, 10, 50. Inserting
    a^(j−1)b costs 2(j−2) + 1; each a^d costs 1 comparison for its b-child and 2 for its a-child.
  - Scanning costs 3n² − n + 1: 2 comparisons per character down the a-chain, then 3 per character, because the
    b-only node a^(n−1) fails and its failure link has the a-child second.

**Many occurrences** (experiment §3). Text a^1024 with patterns a, …, a^32 has 32 272 occurrences, yet Aho–Corasick
makes 1551 comparisons (0.999 per input character). The counts are accumulated along failure links, not reported one
by one.

**V1, agreement and oracle control:**
- V1: 88 instances, 264 runs.
- Agreement: 1500 extra instances (1379 with an occurrence), 4500 runs, 0 failures.
- The oracle uses str.find in a loop, stepping one past each match.
- **Oracle control:** 480 correct outputs accepted; 4556 wrong outputs rejected and 0 accepted. The wrong outputs:
  count + 1 on one pattern; non-overlapping counts from str.count (224); reversed tuple; counts of the reversed
  patterns; the total count; a missing or extra entry; a list; bool or float entries; None.

**V2 fits:** naive on n = 8..32, KMP per pattern on n = 8..64, Aho–Corasick on n = 16..256; rivals in section 1.
**Shape:** MATCH n⁴ (consecutive n = 1..16), n³ (n = 2..15), n² (n = 1..12).
**Citations:** Aho & Corasick 1975 (DOI checked, CACM 18(6) 333–340); KMP 1977.

## 3. Linear ordering problem: enumeration vs subset DP

**Problem.** Maximise Σ_{a before b} W[a][b], in the form of Grötschel, Jünger & Reinelt; the diagonal is ignored.

**Algorithms.**
- Enumeration: Θ(n!·n²), exactly n!(n(n−1)/2 + 1) − 1, checked for n = 2..8.
- Subset DP with gains recomputed from scratch: Θ(n²·2ⁿ), exactly 2^(n−2)(n+4)(n−1) + 1, checked for n = 2..15.
  The terms are n(n−1)2^(n−2) gain additions, n·2^(n−1) value additions and n·2^(n−1) − 2^n + 1 comparisons.
- Both counts were the same on 3 random matrices per n.
- The running-row-sum Θ(n·2ⁿ) variant is not implemented. The caveat says so, and the rival n·2ⁿ is rejected
  (α = 1.108).

**Oracle.** The upper bound Σ_{a<b} max(W[a][b], W[b][a]) rejects or certifies; otherwise a branch and bound runs,
exact for n ≤ 8 and with a budget above that.

**V1, agreement and oracle control:**
- V1: 55 instances, 100 runs. The kinds are signed and non-negative random matrices, tournaments, hidden acyclic
  instances, zero matrices and large entries, with junk on the diagonal.
- Agreement: 436 extra runs, 0 failures.
- **Oracle control:** 212 correct outputs accepted; 2460 wrong outputs rejected and 0 accepted. The wrong outputs:
  value ± 1; a worse order with honest or optimal value; the value of the reversed order; the diagonal added; a
  repeated or missing element; wrong types.

**V2 fits:** enumeration on n = 4..8, DP on n = 6..14. **Shape:** the DP on n = 2..15 gives MATCH n²·2ⁿ, C-finite of
order 4 with characteristic polynomial (x−2)³(x−1).

**Tags.** T6 + T8: the GJR abstract states that the problem is NP-hard. **Citations:** GJR 1984, Karp 1972,
Held–Karp 1962, Bodlaender et al. 2012.

## 4. 3XOR, all triples vs a Patricia trie (sub-agent, re-run by me)

**Problem.** (w, values): find indices i < j < k with XOR zero, or return None. `equal` compares existence, and
`check` verifies the triple; for None it decides with an O(n²) Counter-based pair check.

**Algorithms.**
- **All triples:** Θ(n³). On a no-instance, exactly C(n, 2) XORs + C(n, 3) equality tests = (n³ − n)/6.
- **Patricia trie:** a deterministic O(n² + n·w) algorithm, following the idea in the abstract of Dietzfelbinger,
  Schlag & Walzer: "a version of the Patricia trie for X, which makes it possible to traverse the set a ⊕ X in
  ascending order for arbitrary a … in linear time".
  - Zero and duplicate cases are handled first. The proof that a solution has either three distinct nonzero values or
    the form (x, x, 0) is in entry.json.
  - No sorted(), min(), max(), dict or set is used on input values, so the count involves no CPython built-in.

**V2 family.** All w-bit odd-weight words, with n = 2^(w−1), shuffled. It is a no-instance, and the merge interleaves
maximally, because {a ⊕ x} consists of even-weight words.
- Exact count of the trie: 7n² + 2n·log₂n − 3n (n = 1..2048), made of n² XORs, n·log₂n + n(n−1) ANDs and as many
  truth tests, and 4n² − n comparisons.
- The count is independent of the shuffle (three other shuffles, n = 1..256; *sub-agent*).
- The bare leading terms would also fit (n³: 1.000311; n²: 0.996615; *sub-agent*), but the exact forms are used.

**Results, reproduced by me:**
- Validator V2: α = 1.000 for both fits, rivals as in section 1, shape MATCH ×2.
- V1: 160 instances, 312 runs (79 yes, 81 no). At n = 4 all 8 instances are no and at n = 300 all 8 are yes; seeds
  were not changed to force a mix, and the entry says so.
- Extra agreement: 525 instances (248 yes), 0 failures.
- Oracle control: 720 correct outputs accepted; 2977 wrong outputs rejected and 0 accepted. Among them are the
  repeated-index trap (126), a negative-index alias (174) and a bool trap (94).
- Cross-version SHA-256 `d38397740dfacbacb07d2e12ffba034a4ed2b6b3f1bdcdf411e23343080ef9cb` under both versions.
- Its 4 unit tests pass.

**Abstract checks** (arXiv API, section 7):
- DSW: the abstract states the O(n² log n) easy bound, the O(n²) bound with hashing or a deterministic dictionary,
  and the deterministic quadratic Patricia-trie algorithm.
- Jafargholi–Viola: the abstract states that the reductions are re-executed "for the variant 3XOR of 3SUM".
- No conjectured lower bound is recorded in the entry: `lower_bounds` is left out.

## 5. Citation checks

Script: [experiments/2026-10-06i_sources.py](../experiments/2026-10-06i_sources.py). It reads the sources straight
from the three entry.json files and uses tools/check_sources.py's matching rules. **Result: 8 sources, 10 identifiers,
0 problems.**

| Source | Registered (Crossref / DataCite / arXiv) |
|---|---|
| Karp 1972 | Complexity of Computer Computations, 85–103 |
| Grötschel, Jünger & Reinelt 1984 | Oper. Res. 32(6) 1195–1220 |
| Held & Karp 1962 | J. SIAM 10(1) 196–210 |
| Bodlaender et al. 2012 | Theory Comput. Syst. 50(3) 420–432 |
| Aho & Corasick 1975 | CACM 18(6) 333–340 |
| Knuth, Morris & Pratt 1977 | SIAM J. Comput. 6(2) 323–350 |
| Dietzfelbinger, Schlag & Walzer 2018 | DataCite DOI 10.4230/LIPIcs.MFCS.2018.59, plus arXiv 1804.11086 |
| Jafargholi & Viola 2016 | Algorithmica 74(1) 326–343, plus arXiv 1305.3827 |

**Content claims beyond bibliographic data, and what they rest on:**

| Claim | Basis |
|---|---|
| LOP is NP-hard | GJR abstract |
| DSW Patricia trie | abstract |
| Jafargholi–Viola on 3XOR | abstract |
| Karp 1972, NP-completeness of FEEDBACK ARC SET | unchecked source text; standard, and used in earlier entries |
| Held–Karp and Bodlaender et al. for the (set, next) recurrence | unchecked source text, title-level support |
| Aho & Corasick and KMP for their algorithms | unchecked source text, title-level support |

## 6. Cross-version check of the exact counts

Each experiment's count-series section prints a SHA-256 of its series; each was run under CPython 3.14.2 and 3.12.10.

| Entry | Series | Hash (3.14.2 and 3.12.10) |
|---|---|---|
| Aho–Corasick | 52 values | `917cdb39…8f30cf7cb` |
| Linear ordering | 21 values | `f12e9a7b…c7c6fa3d4` |
| 3XOR | full experiment | `d3839774…3080ef9cb` |

None of the counts passes through sorted, min or max (RL-069), so no shape block sets `python_version_dependent`.

## 7. Decision log

| # | Decision | Alternatives considered | Evidence that settled it |
|---|---|---|---|
| D6 | Aho–Corasick children as linearly scanned lists | dict children | Lookups become character comparisons (the same unit as naive and KMP) and the count is free of CPython hashing |
| D7 | Multi-pattern family with n patterns and text n² | n = text length with √n patterns | Integer closed forms for all three algorithms, and L and N grow together |
| D8 | Third algorithm (KMP per pattern) in the multi-pattern entry | two algorithms | It rules out the explanation that any linear matcher suffices: Θ(PN + L) is rejected for Aho–Corasick (n³ rival, α = 0.667) |
| D9 | Counts, not reported occurrences, for Aho–Corasick | report every occurrence | Θ(N + L) independent of the occurrences (32 272 occurrences vs 1551 comparisons); stated in the caveats |
| D10 | LOP entry with the recompute-gain DP, Θ(n²2ⁿ) | running row sums, Θ(n·2ⁿ) | Time budget. Stated in the caveat; the n·2ⁿ rival is declared and rejected, so the claim matches this implementation |
| D11 | 3XOR fast method: deterministic Patricia trie (DSW) | hashing (count depends on CPython's hash internals); sort + binary search, Θ(n² log n) | Exact count, deterministic, version-independent (identical hashes). The n² log n rival is rejected (α = 0.911) |
| D12 | 3XOR delegated to one sub-agent with a fixed design; all network and citation work kept with me | all entries myself | Time; one network checker keeps the rate limits simple. The CPU rule was kept: at most one process per agent |

## 8. Failures, bugs fixed, near-misses

- **F2 (control bug, fixed).** In the Aho–Corasick control, "counts reversed" equals the correct tuple when the tuple
  is a palindrome, e.g. (1, 2, 1). 14 were accepted. The mutation is now applied only when reversal changes the
  tuple; rerun 4556/0.
- **F3 (tooling, fixed).** A Python string-replace script run through a Bash heredoc did not match, because of `\n`
  escaping, and silently left the file unchanged. Found by grep and redone with the Edit tool. The same heredoc
  collapse of `\\n` into a newline broke three f-strings in the generated sources script (SyntaxError). They were
  repaired, and all experiments were then parsed with `ast` (syntax OK).
- **F5 (sub-agent, fixed by it).** Functions stored as class attributes became bound methods in its tests
  (TypeError), fixed with staticmethod. It also replaced an `eval()` of the cost expression in its experiment by the
  closed-form functions.
- **NEAR-MISS N1.** At two V1 sizes of the 3XOR entry only one answer occurs (n = 4: no only; n = 300: yes only);
  documented in the entry.

## 9. Reproduction

From the repository root, with `export PYTHONIOENCODING=utf-8`:

```
.venv/Scripts/python.exe experiments/2026-10-06i_sources.py                      # network, ~30 s
.venv/Scripts/python.exe experiments/2026-10-06i_aho_corasick.py                 # ~2 s
.venv/Scripts/python.exe experiments/2026-10-06i_linear_ordering.py              # ~7 s
.venv/Scripts/python.exe experiments/2026-10-06i_three_xor.py                    # ~23 s
py -3.12 experiments/2026-10-06i_aho_corasick.py 5
py -3.12 experiments/2026-10-06i_linear_ordering.py 4
py -3.12 experiments/2026-10-06i_three_xor.py
for e in multi-pattern-matching-naive-vs-aho-corasick linear-ordering-enumeration-vs-subset-dp          three-xor-all-triples-vs-patricia-trie; do
  .venv/Scripts/python.exe tools/validate.py --scaling -v pairs/$e
done
```

## 10. Files created

- `pairs/multi-pattern-matching-naive-vs-aho-corasick/`: entry.json, README.md, harness.py, implementations/naive.py,
  implementations/kmp_each.py, implementations/aho_corasick.py
- `pairs/linear-ordering-enumeration-vs-subset-dp/`: entry.json, README.md, harness.py, implementations/enumeration.py,
  implementations/subset_dp.py
- `pairs/three-xor-all-triples-vs-patricia-trie/` (sub-agent): entry.json, README.md, harness.py,
  implementations/all_triples.py, implementations/patricia_trie.py
- `experiments/2026-10-06i_{sources,aho_corasick,linear_ordering,three_xor}.py`
- `tests/test_entries_2026_10_06i_{aho_corasick,linear_ordering,three_xor}.py`
