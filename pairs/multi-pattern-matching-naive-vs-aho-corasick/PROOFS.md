# Proofs: multi-pattern matching, naive vs KMP vs Aho–Corasick

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code)
about its problem and its three algorithms, from first principles, from the code in this folder and, for KMP, from
`pairs/string-matching-naive-vs-kmp/PROOFS.md`, which proves the identical KMP code. Sections 1 to 6 prove the exact
comparison counts and the bounds that the earlier text stated (per pattern, per lookup, the lower bound of
Aho–Corasick). Sections 7 to 11 prove the rest: the correctness of the three algorithms (for Aho–Corasick the trie,
the breadth-first failure links, the scan invariant and the accumulation), the worst case of the naive matcher,
Θ(P·N + L) for KMP per pattern, the construction bound and the space of Aho–Corasick, and the caveats. Each proof is
followed by the deterministic scripts or tests that check it and the ranges they check; a check covers only those
ranges, the proofs cover the general statements. Citations give credit; they are never part of a proof.

## Counting convention

`harness.py`, class `CountingChar`: `__eq__` and `__ne__` each add 1 to the module counter `_comparisons`
(`_comparisons += 1`) and then compare the wrapped characters (`_val` unwraps the other operand); `__hash__` is
`None`. No other operation counts. `generate_scaling` builds the text and every pattern as tuples of `CountingChar`
and sets `_comparisons = 0`; `reported_cost(output)` returns `_comparisons`. Every counted comparison in the code
compares two characters of these tuples, so Python calls the left operand's `__eq__` or `__ne__` once and each
comparison counts exactly 1: `text[i + j] == pattern[j]` in `count_occurrences_naive`; `pattern[q] != pattern[k]`
and `pattern[q] == pattern[k]` in `_failure`; `c != pattern[q]` and `c == pattern[q]` in
`count_occurrences_kmp_each`; `ch == c` in `_child`. Not counted: `len()`, iteration and indexing, the tests on
plain ints (`j < m`, `j == m`, `k > 0`, `q > 0`, `q == m`, `nxt < 0`, `w >= 0`, `u != 0`, `f == 0`, `state == 0`),
list and deque operations, and the visit counters and their accumulation in `count_occurrences_aho_corasick`.

Notation: N = length of the text, m = length of a pattern, P = number of patterns, L = total pattern length. A
*lookup* is one call `_child(children, node, c)`; it compares `c` with the characters of the entries of
`children[node]` in order until one is equal, so it costs the position of the hit, or the length of the list on a
miss.

**Scaling instance.** `generate_scaling(n, rng)` uses `scaling_strings(n)`: text a^N with N = n² and the n
patterns p_j = a^(j−1)b, j = 1..n (so L = n(n+1)/2); `rng` is unused. For n = 0 the text is empty and there are
no patterns.

## 1. Naive matching per pattern: n(n+1)(3n² − 2n + 2)/6

**Statement.** On every input, `count_occurrences_naive` makes at most max(N − m + 1, 0)·m comparisons for a
pattern of length m, that is at most (N − m + 1)m when m ≤ N + 1. On the text a^N it makes exactly j(N − j + 1)
comparisons for the pattern a^(j−1)b whenever N ≥ j − 1, so a list of such patterns attains the sum of the
per-pattern bounds. On the scaling instance it makes exactly Σ_{j=1..n} j(n² − j + 1) = n(n+1)(3n² − 2n + 2)/6
comparisons for every n ≥ 0.

**Proof of the bound.** For a pattern of length m the loop `for i in range(n - m + 1)` (here `n = len(text)`)
runs max(N − m + 1, 0) times, and in each alignment the `while` loop compares `text[i + j] == pattern[j]` only
while `j < m`, so at most m times.

**Proof of the exact counts.** The per-alignment count is given in `entry.json`, field
`algorithms[0].time_complexity` (each alignment of a^(j−1)b against a^N matches j − 1 characters and fails on the
b, j comparisons). The missing steps: for N ≥ j − 1 there are N − j + 1 ≥ 0 alignments, which gives j(N − j + 1).
On the scaling instance N = n² ≥ j − 1 for every j ≤ n, and
Σ_{j=1..n} j(n² + 1 − j) = (n² + 1)·n(n+1)/2 − n(n+1)(2n+1)/6 = n(n+1)(3n² − 2n + 2)/6; at n = 0 both sides
are 0. At the V2 size n = 8 this is 8·9·178/6 = 2136.

**Check.** At the V2 sizes n = 8, 12, 16, 24, 32: `experiments/2026-10-06i_aho_corasick.py` (section 1, which
checks n = 1..20, 24, 32, 40). `experiments/2026-10-07_closed_form_checks.py`, group `strings`, line
"multi naive n(n+1)(3n^2-2n+2)/6": n = 0..30, 32, 40, 48, 64. `experiments/2026-10-07_count_proof_checks.py`,
group `strings`, line "multi naive per pattern j(N-j+1) on a^N, a^(j-1)b": j = 1..25, N = j − 1..j + 40; line
"multi naive <= max(N-m+1,0)m per pattern": 12000 (text, pattern) pairs drawn by `generate` in `harness.py`
(n = 0..24, 40 seeds each); line "multi naive 0 comparisons when m >= N+2": the pairs among them with m ≥ N + 2.

## 2. KMP per pattern: at most 3(m − 1) and 3N

**Statement.** For every pattern of length m ≥ 1 and every text of length N, `_failure` makes at most 3(m − 1)
comparisons, and the scan loop of `count_occurrences_kmp_each` for that pattern makes at most 3N.

**Proof.** fail[j] ≤ j for every j: fail[0] = 0, and fail[q] is the value of k at the end of iteration q, where
k ≤ q − 1 at the start of iteration q (k starts at 0, rises by at most 1 per iteration, and `k = fail[k - 1]`
never raises it).

*Failure table.* In iteration q every true `while` test `pattern[q] != pattern[k]` is followed by
`k = fail[k - 1] ≤ k − 1`, at most one `while` test is false, and the `if` test runs once. Over the m − 1
iterations k rises by at most m − 1 in total and never goes below 0, so there are at most m − 1 true `while`
tests: at most 3(m − 1) comparisons.

*Scan.* q starts at 0. Per text character the `if` test runs once and at most one `while` test is false. Every
true `while` test is followed by `q = fail[q - 1] ≤ q − 1`. q rises only in the `if` branch, by at most 1 per
character, and the reset `q = fail[q - 1]` after a full match only lowers it, so over N characters there are at
most N true `while` tests: at most 3N comparisons.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `strings`, lines "multi KMP failure table
<= 3(m-1)" and "multi KMP scan <= 3N": the 12000 (text, pattern) pairs of section 1.

## 3. KMP per pattern on the scaling instance: 3n³ − 2n² − 5n + 6

**Statement.** On the text a^N: the pattern b costs N comparisons (failure table 0, scan N); the pattern ab
costs 2N for N ≥ 1 (failure table 1, scan 2N − 1); the pattern a^(j−1)b with j ≥ 3 costs
(3j − 6) + (3N − j) = 3N + 2j − 6 for N ≥ j − 1 (failure table 3j − 6, scan 3N − j). On the scaling instance
`count_occurrences_kmp_each` makes exactly 3n³ − 2n² − 5n + 6 comparisons for every n ≥ 2.

**Proof.** The failure table of a^(j−1)b is fail[q] = q for 0 ≤ q ≤ j − 2 (shown below).

*Pattern b (m = 1).* `_failure` has no iteration. Per character: q = 0, so the `while` test stops at `q > 0`
without a comparison; `c == pattern[0]` is a = b, false (1). q stays 0 and never equals m = 1. Total N.

*Pattern ab (m = 2).* `_failure`: iteration q = 1 has k = 0, so the `while` loop makes no comparison;
`pattern[1] == pattern[0]` is b = a, false (1); fail[1] = 0. Scan: the first character has q = 0 and compares
`c == pattern[0]`, a = a, true (1), q = 1. Every later character: `c != pattern[1]` is a ≠ b, true (1),
q = fail[0] = 0; the `while` loop stops at `q > 0`; `c == pattern[0]` is true (1); q = 1. q never reaches 2.
Total 1 + 1 + 2(N − 1) = 2N for N ≥ 1.

*Pattern a^(j−1)b, j ≥ 3: failure table.* By induction, after iteration q (1 ≤ q ≤ j − 2), k = q and
fail[q] = q. Iteration q = 1: k = 0, no `while` comparison; `pattern[1] == pattern[0]` is a = a (1); k = 1.
Iteration 2 ≤ q ≤ j − 2: k = q − 1 ≥ 1; `pattern[q] != pattern[k]` is false (1); `pattern[q] == pattern[k]` is true
(1); k = q. Iteration q = j − 1: k = j − 2 ≥ 1; each `while` test compares b with a, true (1), and sets
k = fail[k − 1] = k − 1; this happens for k = j − 2, …, 1, that is j − 2 times, and at k = 0 the test `k > 0`
stops the loop without a comparison; then `pattern[j-1] == pattern[0]` is b = a, false (1). Total
1 + 2(j − 3) + (j − 2) + 1 = 3j − 6.

*Pattern a^(j−1)b, j ≥ 3: scan.* Character 1: q = 0, no `while` comparison; `c == pattern[0]` is true (1); q = 1.
Characters t = 2, …, j − 1: q = t − 1 ∈ [1, j − 2]; `c != pattern[q]` is false (1); `c == pattern[q]` is true (1);
q = t. Every later character: q = j − 1; `c != pattern[j-1]` is a ≠ b, true (1), q = fail[j − 2] = j − 2 ≥ 1;
`c != pattern[j-2]` is false (1); `c == pattern[j-2]` is true (1); q = j − 1 again. q never reaches j. With
N ≥ j − 1 characters the total is 1 + 2(j − 2) + 3(N − j + 1) = 3N − j.

*Sum.* On the scaling instance N = n² ≥ n ≥ j for every pattern, so all three cases apply. For n ≥ 2:
N + 2N + Σ_{j=3..n} (3N + 2j − 6) = 3N(n − 1) + (n² + n − 6) − 6(n − 2) = 3n³ − 2n² − 5n + 6 (at n = 2 the sum
over j is empty and both sides are 12).

**Outside the domain** (the entry claims nothing there): at n = 0 there is no pattern (0 comparisons) and at
n = 1 the only pattern b costs N = 1, while the formula gives 6 and 2.

**Check.** At the V2 sizes n = 8, 16, 24, 32, 48, 64: `experiments/2026-10-06i_aho_corasick.py` (section 1, which
checks n = 2..20, 24, 32, 40, 48, 64, 70). `experiments/2026-10-07_closed_form_checks.py`, group `strings`, line
"multi KMP 3n^3-2n^2-5n+6": n = 0..30, 32, 40, 48, 64 (n = 0, 1 reported as outside the domain).
`experiments/2026-10-07_count_proof_checks.py`, group `strings`, line "multi KMP per pattern on a^N: b N, ab 2N
(N>=1), a^(j-1)b 3N+2j-6": j = 1..25, N = j − 1..j + 40; line "multi KMP failure table 0 (b), 1 (ab), 3j-6
(a^(j-1)b, j>=3)": j = 1..25; line "multi KMP scan 3N-j on a^N (j>=3, N>=j-1)": j = 3..25, N = j − 1..j + 40.

## 4. Aho–Corasick on any input: at most σ per lookup, at most 2N scan lookups, at least N + L − σ

**Statement.** Let σ be the size of an alphabet that contains every character of the patterns. On every input
(P non-empty patterns): every lookup makes at most σ comparisons; the scan loop makes at most 2N lookups; and, if
P ≥ 1, `count_occurrences_aho_corasick` makes at least N + L − σ comparisons in all. (With P = 0 the root has no
child, every lookup costs 0 and the count is 0, so the lower bound needs P ≥ 1 whenever N > σ.)

**Proof.** The bounds per lookup and on the total are given, with the outline of the lower bound, in `entry.json`,
field `algorithms[2].time_complexity`; the bound on scan lookups is argued in the docstring of
`implementations/aho_corasick.py`. The missing steps:

- *Child lists have distinct characters.* An entry `(c, nxt)` is appended to `children[node]` only after
  `_child(children, node, c)` returned −1, that is when no entry with the character c exists. So a list has at
  most σ entries and a lookup makes at most σ comparisons. In particular the root has at most σ children, so at
  most σ nodes have depth 1.
- *Failure links point to shallower nodes:* depth(fail[x]) < depth(x) for every node x other than the root, at all
  times. Initially every entry of `fail` is 0, the root. An assignment `fail[v] = w` for a child v of u ≠ 0 takes
  w as a child of some f reached from fail[u] by steps `f = fail[f]`; by induction each such f has
  depth < depth(u), so depth(w) ≤ depth(u) < depth(v). The assignment `fail[v] = 0` keeps the claim.
- *Scan lookups.* For each text character the loop makes one lookup plus one more after each `state = fail[state]`.
  That assignment lowers the depth of the state by at least 1; a successful lookup raises it by exactly 1 and ends
  the character. The depth starts at 0 and never goes below 0, so over N characters there are at most N moves along
  failure links: at most 2N lookups.
- *Lower bound, insertion.* Insertion makes exactly L lookups. A lookup in an empty list costs 0 but misses, and
  every miss creates a node, so at most T lookups (T = number of nodes created) cost 0 and the others cost at least
  1: at least L − T comparisons.
- *Lower bound, failure links.* The loop runs for every node v of depth ≥ 2 (children of u ≠ 0). Its last lookup is
  either a hit (at least 1 comparison) or a miss at f = 0, which compares with every child of the root, at least
  one since P ≥ 1. There are at least T − σ such nodes: at least T − σ comparisons.
- *Lower bound, scan.* The last lookup for each character is a hit or a miss at the root (non-empty for P ≥ 1):
  at least N comparisons.

Together: at least (L − T) + (T − σ) + N = N + L − σ.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `strings`, lines "AC comparisons per lookup
<= sigma", "AC scan lookups <= 2N" and "AC total >= N+L-sigma (P >= 1)": 1000 instances drawn by `generate` in
`harness.py` (n = 0..24, 40 seeds each), with σ = the number of distinct characters in the patterns; line "AC with
no patterns: 0 comparisons": the instances with P = 0 among them and the texts (ab)^N, N = 0..20.

## 5. Aho–Corasick on the scaling instance: 4n² − 3

**Statement.** On the scaling instance, `count_occurrences_aho_corasick` makes:
- (n − 1)² comparisons to build the trie, for every n ≥ 1; inserting p_j costs 0 for j = 1 and 2j − 3 for j ≥ 2;
- 3n − 5 for the failure links for n ≥ 2 (0 for n = 1): 1 for the b-child of every a^d, d = 1..n − 1, and 2 for
  the a-child of every a^d, d = 1..n − 2;
- 3n² − n + 1 for the scan for n ≥ 2 (1 for n = 1): 2 for each of the first n − 1 characters and 3 for each later
  one;
- so n² + n − 4 to build the automaton (trie and failure links) for n ≥ 2, and 4n² − 3 in all for every n ≥ 1
  (at n = 1: 0 + 0 + 1 = 1).

**Proof.** The per-step costs are given in `entry.json`, field `algorithms[2].time_complexity`. The missing steps
are the shape of the trie (the order of the child lists) and the failure links, which fix those costs.

*Trie.* Write a^d for the node of the string a^d (a^0 = root) and a^d b for its b-child. The b-child of a^d is
created by p_{d+1} and the a-child a^(d+1) by p_{d+2}, which is inserted later, so after all insertions the list
of a^d is [(b, a^d b), (a, a^(d+1))] for 0 ≤ d ≤ n − 2, the list of a^(n−1) is [(b, a^(n−1) b)], and the b-nodes
are leaves. Inserting p_1 = b: the root list is empty, 0 comparisons. Inserting p_2 = ab: the root list is
[(b)], the lookup for a misses (1) and creates a¹; the lookup for b in the new node costs 0. Inserting p_j,
j ≥ 3: at the root the lookup for a costs 2 (b ≠ a, a = a); at a^d, 1 ≤ d ≤ j − 3, the list is [(b), (a)] and
the lookup costs 2; at a^(j−2) the list is [(b)] (its a-child does not exist yet), the lookup misses (1) and
creates a^(j−1); the lookup for b there costs 0. Total 2 + 2(j − 3) + 1 = 2j − 3, also 1 = 2·2 − 3 for j = 2.
Σ_{j=2..n} (2j − 3) = (n − 1)² for n ≥ 1.

*Failure links.* The root's children b and a¹ keep fail = 0 and cost nothing (the loop skips u = 0). We show
fail[a^d] = a^(d−1) for 1 ≤ d ≤ n − 1: true for d = 1, and when u = a^d (1 ≤ d ≤ n − 2) is processed,
f = fail[u] = a^(d−1) has the list [(b), (a)], so the a-child a^(d+1) gets `_child(f, a)` = a^d with 2 comparisons
(b ≠ a, a = a). The b-child of u = a^d (1 ≤ d ≤ n − 1) gets `_child(a^(d−1), b)`, a hit at the first entry
(1 comparison). The b-nodes have no children. Total (n − 1)·1 + (n − 2)·2 = 3n − 5 for n ≥ 2; for n = 1 the
only node is the root's child b, and nothing is computed.

*Scan of a^N, n ≥ 2.* From the root and from a^d with d ≤ n − 2 the lookup for a costs 2 (b ≠ a, a = a) and
moves one node down, so characters 1, …, n − 1 cost 2 each and lead to a^(n−1). From a^(n−1): the lookup misses
on [(b)] (1), the state becomes fail[a^(n−1)] = a^(n−2) (the root when n = 2), whose list is [(b), (a)], and the
lookup costs 2 and returns to a^(n−1): 3 per character. As N = n² ≥ n − 1, the total is
2(n − 1) + 3(n² − n + 1) = 3n² − n + 1. For n = 1 the text is a and the root list is [(b)]: one miss (1), then
`state == 0` ends the loop: 1.

*Totals.* For n ≥ 2: (n − 1)² + (3n − 5) = n² + n − 4, and n² + n − 4 + 3n² − n + 1 = 4n² − 3. For n = 1:
0 + 0 + 1 = 1 = 4 − 3. At the V2 size n = 256 this is 262141.

**Outside the domain** (the entry claims nothing there): at n = 0 there is no pattern and no text character, so
the count is 0, not −3.

**Check.** At the V2 sizes n = 16, 32, 64, 128, 256: `experiments/2026-10-06i_aho_corasick.py` (section 1, which
checks the total at n = 1..20, 24, 32, 40, 48, 64, 70, 128, 256, 300, and the build and scan parts at n = 2, 5,
10, 50). `experiments/2026-10-07_closed_form_checks.py`, group `strings`, line "AC 4n^2-3": n = 0..30, 32, 40,
48, 64, 128, 256, 300 (n = 0 reported as outside the domain); lines "AC trie build (n-1)^2 (n>=1)": n = 1..30;
"AC failure links 3n-5 (n>=2)": n = 2..30 (it also prints the n = 1 parts 0, 0, 1); "AC scan 3n^2-n+1 (n>=2)":
n = 2..30. `experiments/2026-10-07_count_proof_checks.py`, group `strings`, line "AC per insertion: 0 (j=1),
2j-3 (j>=2), V2 family": n = 1..20, every j; line "AC failure links per node: 1 (a^d b), 2 (a^(d+1)), 0 at depth
1": n = 1..20, every node; line "AC scan per character: 2 for t <= n-1, 3 after (n>=2); 1 at n=1": n = 1..15,
every character; line "AC build (trie + links) n^2+n-4 (n>=2)": n = 2..20.

## 6. Aho–Corasick on a^N with the patterns a, aa, …, a^n: N + n(n+1)/2 − 1

**Statement.** On the text a^N with the patterns a, a², …, a^n (n ≥ 1, N ≥ 0), `count_occurrences_aho_corasick`
makes exactly n(n − 1)/2 comparisons for the trie, n − 1 for the failure links and N for the scan, so
N + L − 1 in all (L = n(n+1)/2): fewer than the N + L input characters, whatever the number of occurrences.
`README.md` states the case N = 1024, n = 32: 1024 + 528 − 1 = 1551 comparisons, while the returned counts sum to
Σ_{k=1..32} (1025 − k) = 32272 occurrences.

**Proof.** The trie is the chain root = a⁰, a¹, …, a^n. Before a^k is inserted, the earlier patterns have created
a¹, …, a^(k−1), and each of root, …, a^(k−2) has exactly one child (the next node of the chain) while a^(k−1) has
none. Inserting a^k walks root, a¹, …, a^(k−1): the first k − 1 lookups hit the only entry (1 comparison each)
and the lookup at a^(k−1) finds an empty list (0) and creates a^k: k − 1 comparisons, n(n − 1)/2 in all.
Failure links: a¹ keeps fail = 0. When a^d (1 ≤ d ≤ n − 1) is processed, its only child a^(d+1) looks up a in
f = fail[a^d] = a^(d−1) (true for d = 1, and then by induction), a hit at the only entry: 1 comparison, and
fail[a^(d+1)] = a^d. That is n − 1 comparisons. Scan: from a^d with d < n the lookup hits the only entry (1) and
moves down; at a^n the list is empty (0), the state becomes fail[a^n] = a^(n−1) (the root when n = 1), and the
lookup there hits (1) and returns to a^n. So every character costs exactly 1: N in all. Sum:
n(n − 1)/2 + (n − 1) + N = N + n(n+1)/2 − 1. The pattern a^k occurs 1024 − k + 1 times in a^1024.

**Check.** `experiments/2026-10-06i_aho_corasick.py`, section 3, prints this count for N = n², n = 4, 8, 16, 32
(it checks only that the count is at most 3(N + L)). `experiments/2026-10-07_count_proof_checks.py`, group
`strings`, line "AC on a^N, patterns a..a^n: trie n(n-1)/2, links n-1, scan N, total N+n(n+1)/2-1": n = 1..20,
N = 0..60, and N = 1024, n = 32 (1551 comparisons, 32272 occurrences).

## Conventions for sections 7 to 11

T is the text (length N); the patterns p₁, …, p_P are non-empty with lengths m₁, …, m_P and total L. An occurrence of
p *ends at* position t if T[t − m + 1 .. t] = p; occurrences correspond one to one to their start positions, so
counting end positions counts the positions of `problem_statement`, overlapping ones included. Pref is the set of all
prefixes of the patterns, including the empty string ε. For a trie node v, str(v) is the string spelled by the path
from the root.

Cost model: character comparisons as counted by `CountingChar`, and for time the unit-cost model with O(1) per executed
line (a lookup costs O(1) plus its comparisons) and O(k) to build a list of k entries; σ is the size of an alphabet
containing the pattern characters. O and Θ are the usual asymptotic bounds over the inputs: a bound may fail on at most
finitely many inputs, never on an infinite family; where a parameter can be 0 (N, L, P), a bound carries an explicit + 1
or a hypothesis (N ≥ 1, P ≥ 1), so that no infinite family of inputs violates it.

## 7. Naive matching per pattern: correctness and the worst case N·L

**Statement** (`algorithms[0].correctness`, `time_complexity`, `space_complexity`; `relationship`; `naive.py`
docstring). `count_occurrences_naive` returns the overlapping counts. On every input it makes at most N·L comparisons,
and N·L is attained for every N and L (L copies of the pattern a against a^N), so its worst case over the inputs with
given N and L is exactly N·L, Θ(N·L). It uses O(1) extra words besides the output.

**Proof.** For each pattern, every alignment i = 0, …, N − m is tried and counted iff all m characters agree. A pattern
of length m costs at most max(N − m + 1, 0)·m ≤ N·m comparisons (section 1), so all patterns cost at most N·L. With L
copies of the pattern a and the text a^N, every one of the N alignments of every copy makes exactly one comparison:
N·L. Besides the output tuple the function keeps n, m, `count`, i and j. ∎

**Check.** `tests/test_proofs_aho_corasick.py`, `test_correctness`: on every text over {a, b} of length at most 5 with
every list of at most two patterns over {a, b} of length 1..3 (211 lists × 63 texts) and on 600 seeded instances from
`harness.generate` (n = 0..12), the counts equal a direct count. `test_naive_worst_case_and_bound`: exactly N·L for L
copies of a against a^N (N = 0..30, L = 1..10) and at most N·L on the 600 seeded instances. `test_naive_space` (300
seeded instances): every local variable is an integer, part of the input, or the output list of at most P counts.

## 8. KMP per pattern: correctness, Θ(P·N + L), space

**Statement** (`algorithms[1].correctness`, `time_complexity`, `space_complexity`; `kmp_each.py` docstring;
`relationship`). `count_occurrences_kmp_each` returns the overlapping counts. On every input it makes between
P·N + L − P and 3P·N + 3(L − P) comparisons; for N ≥ 1 this is Θ(P·N + L) comparisons, and its time is Θ(P·N + L) on
every input with P ≥ 1 (Θ(1) for P = 0). For P ≥ 1 its working storage is Θ(max m) (the output aside).

**Proof.** `_failure` and the scan loop in `count_occurrences_kmp_each` are the same code as `_failure` and
`count_kmp` in `pairs/string-matching-naive-vs-kmp/implementations/kmp.py` (apart from comments and the loop over the
patterns around them), run once per pattern. So by `pairs/string-matching-naive-vs-kmp/PROOFS.md`, sections 6 and 7,
each count is correct, and by its section 8 each pattern costs between m − 1 and 3(m − 1) comparisons for its failure
table and between N and 3N for its scan. Summing over the patterns gives the two bounds. For N ≥ 1, P·N ≥ P and
L ≥ P, so P·N + L − P ≥ (P·N + L)/2. (For N = 0 and patterns of length 1 no comparison is made at all, so the lower
bound in comparisons needs N ≥ 1.) Time: per pattern O(1) plus building its failure table (m entries) plus O(1) per
comparison and loop iteration, Θ(N + m); summed, Θ(P·N + L + P) = Θ(P·N + L) since L ≥ P, for P ≥ 1. At most two
failure tables exist at a time (the previous one is still held by `fail` while `_failure` builds the next), each of at
most max m entries, and the table of a longest pattern has max m entries. ∎

**Check.** `test_correctness` (the instances of section 7): the counts equal a direct count. `test_kmp_code_identity`:
the source lines of `_failure` and of the scan loop are the same in both files. `test_kmp_each_bounds` (600 seeded
instances): between P·N + L − P and 3P·N + 3(L − P) comparisons. The per-pattern bounds 3(m − 1) and 3N: section 2 and
`tests/test_proofs_kmp.py`, `test_comparison_bounds`.

## 9. Aho–Corasick: correctness

**Statement** (`algorithms[2].correctness`, `idea`; `aho_corasick.py` docstring; `README.md` "Why it works").
`count_occurrences_aho_corasick` returns the overlapping counts: (a) the trie's nodes correspond one to one to Pref,
and child lists have distinct characters; (b) after the breadth-first pass, fail[v] is the node of the longest proper
suffix of str(v) that lies in Pref, for every non-root node v; (c) after the scan has read T[:t + 1], the state is the
node of the longest suffix of T[:t + 1] that lies in Pref; (d) a pattern ends at t iff its node lies on the failure
chain of that state; (e) the reverse breadth-first accumulation turns the visit counts into, for every node, the
number of visits in its subtree of the failure tree, which is the count of its pattern.

**Proof.** (a) Inserting a pattern walks from the root and creates a child exactly when the lookup misses; so every
node is a prefix of a pattern, every prefix gets a node, and an entry (c, ·) is added to a list only when no entry
with c exists (section 4). `ends[k]` is the node of p_k.

**Lemma 9.1 (suffix chain).** If fail[x] is correct (as in (b)) for all non-root nodes x of depth less than or equal
to depth(u), then the nodes whose strings are suffixes of str(u) and lie in Pref are exactly u, fail[u], fail[fail[u]],
…, the root.

*Proof.* Each listed node is a suffix of the previous one, hence of str(u). Conversely let s ∈ Pref be a suffix of
str(u) with s ≠ str(u). Then |s| ≤ |str(fail[u])|, as str(fail[u]) is the longest proper suffix in Pref; s and
str(fail[u]) are both suffixes of str(u), so s is a suffix of str(fail[u]), and by induction on the depth s lies on the
chain of fail[u]. ∎

(b) The queue starts with the root's children and processes nodes in non-decreasing depth (breadth-first order), and
`order` lists the non-root nodes in that order. The root's children keep fail = 0: the only proper suffix of a single
character is ε. Let v be the child of u ≠ 0 along character c, and assume (b) for all nodes of depth at most
depth(u) (they were set when their parents, of smaller depth, were processed). A proper suffix of str(v) = str(u)c
that lies in Pref is ε or has the form s·c with s a proper suffix of str(u); since Pref is closed under prefixes, s lies
in Pref, so by Lemma 9.1 s lies on the chain fail[u], fail[fail[u]], …, root. So the longest proper suffix of str(v) in
Pref is the c-child of the first node on that chain that has one, or ε if none has. The code walks this chain from
f = fail[u], in decreasing depth, takes `_child(children, f, c)` at the first f where it exists, and otherwise stops at
the root with fail[v] = 0. Hence fail[v] is correct, and depth(fail[v]) < depth(v).

(c) Before the first character the state is the root, ε. Let q be the state after T[:t], the longest suffix of T[:t]
in Pref, and c = T[t]. A suffix of T[:t + 1] in Pref is ε or s·c with s a suffix of T[:t] in Pref; such an s is a
suffix of str(q) (both are suffixes of T[:t], and str(q) is the longest), so by Lemma 9.1 s lies on the chain q,
fail[q], …, root. The scan loop walks exactly this chain from q, in decreasing depth, takes the c-child at the first node
that has one, and otherwise stops at the root (`state == 0`) with the state root. So the new state is the longest
suffix of T[:t + 1] in Pref.

(d) A pattern p ends at t iff p is a suffix of T[:t + 1]. As p ∈ Pref, this holds iff p is a suffix of str(state)
(str(state) is the longest suffix of T[:t + 1] in Pref, and both are suffixes of T[:t + 1]), iff ends[p] lies on the
failure chain of the state (Lemma 9.1). So count(p) is the number of t whose state has ends[p] on its failure chain.

(e) In the failure tree (parent of v = fail[v]) the failure chain of a node is its path to the root, so count(p) is
the sum of the original visit counts over the subtree of ends[p]. Every proper descendant of a node in this tree is
deeper (fail lowers the depth), so in reversed breadth-first order every node is processed after all its proper
descendants. By induction over this order, when v is processed, `visits[v]` already holds the sum over its subtree
(each of its children y added its complete subtree sum when y was processed, and nothing is added to `visits[v]`
later), and it adds that sum to its parent. The root is never processed but receives its children's sums. Patterns
are non-empty, so ends[p] is never the root, and the returned tuple lists the subtree sums of ends[p₁], …, ends[p_P]:
the overlapping counts, also for repeated patterns. With P = 0 the scan counts root visits and the result is (). ∎

The method is Aho and Corasick's (1975); the proof above is this project's.

**Check.** `test_correctness` (the instances of section 7): the counts equal a direct count.
`test_trie_failure_links_order_and_states` (600 seeded instances from `harness.generate`, read by a line tracer): the
trie's strings are exactly Pref, child lists have distinct characters, there are at most L + 1 nodes, `order` is
breadth-first and contains every non-root node once, fail[v] is the node of the longest proper suffix of str(v) in Pref
and comes before v in `order`, and after every text character the state is the node of the longest suffix of the text
read that lies in Pref.

## 10. Aho–Corasick: time, space and the uncounted operations

**Statement** (`algorithms[2].time_complexity`, `space_complexity`; `caveats`; docstring). (a) Insertion makes exactly
L lookups, the failure links at most 2Σ_k (m_k − 1) ≤ 2L, and the scan at most 2N; each lookup makes at most σ
comparisons. So the algorithm makes at most σ(2N + 3L) comparisons and runs in O(N + L) time for a fixed alphabet,
on every input, independently of the number of occurrences. With section 4 (at least N + L − σ comparisons when
P ≥ 1) this gives Θ(N + L) for P ≥ 1 and a fixed alphabet. (b) The trie has at most L + 1 nodes (fewer when patterns
share prefixes); the working storage is O(L) plus O(1) words. (c) The operations that are not character comparisons
(node allocation, the queue, the failure-link bookkeeping, the visit counters) number Θ(N + L).

**Proof.** (a) Insertion does one lookup per pattern character. Scan: section 4. Failure links: fix a pattern p with
nodes v₁, …, v_m along its path (v_k = the node of p[:k]), and let d_k = depth(fail[v_k]), so d₁ = 0. Computing
fail[v_{k+1}] (as the child of v_k) starts at f = fail[v_k], of depth d_k; each step `f = fail[f]` lowers the depth by
at least 1, and the result is a child of the last f or the root, so after s_{k+1} steps d_{k+1} ≤ d_k − s_{k+1} + 1, i.e.
s_{k+1} ≤ d_k − d_{k+1} + 1. The computation makes s_{k+1} + 1 lookups. Summing over k = 1, …, m − 1 gives at most
(d₁ − d_m) + 2(m − 1) ≤ 2(m − 1) lookups for the nodes of depth ≥ 2 on the path of p. Every node of depth ≥ 2 lies on
the path of some pattern and has its link computed once, so all failure links take at most 2Σ_k (m_k − 1) lookups
(nodes of depth 1 take none). Each lookup compares with at most σ list entries (section 4). The work besides the
lookups is O(1) per inserted character, per node (allocation, queue, `order`, accumulation) and per text character,
and the lists `fail` and `visits` have one entry per node: O(N + L) for fixed σ.

(b) Each inserted character creates at most one node, so there are at most L + 1 nodes, exactly |Pref|; the lists
`children`, `fail`, `visits`, `order`, the queue and `ends` have O(L + P) = O(L) entries.

(c) Upper bound: O(1) such operations per lookup, per node, per pattern and per text character, O(N + L) by (a) and
(b). Lower bound: the insertion loop executes `node = nxt` once per pattern character (L times) and the scan executes
`visits[state] += 1` once per text character (N times). ∎

**Check.** `test_lookup_counts` (600 seeded instances): exactly L insertion lookups, at most 2Σ(m − 1) failure-link
lookups and at most 2N scan lookups. `test_trie_failure_links_order_and_states`: at most L + 1 nodes.
`test_uncounted_work` (600 seeded instances): the executed lines of `count_occurrences_aho_corasick` (the lookup
function `_child`, whose work is the comparisons, is not traced) number between N + L and 12N + 26L + 6P + 30. The
per-lookup bound σ, the scan bound 2N and the lower bound N + L − σ: section 4 and its checks.

## 11. The relationship and the remaining claims

- *Relationship and notes.* Naive per pattern costs Θ(N·L) comparisons in the worst case (section 7), KMP per pattern
  Θ(P·N + L) on every input with N ≥ 1 (section 8), and Aho–Corasick Θ(N + L) on every input with P ≥ 1 for a fixed
  alphabet (sections 4 and 10). On the V2 family these are the exact counts of sections 1, 3 and 5. KMP per pattern
  runs the scan loop over the whole text once per pattern, P times; Aho–Corasick scans it once.
- *Caveat: random text.* On a uniformly random text over σ ≥ 2 letters, a pattern of length m whose letters lie in the
  alphabet costs the naive matcher on average exactly max(N − m + 1, 0)·Σ_{j<m} σ^(−j) ≤ 2·max(N − m + 1, 0)
  comparisons (the (j + 1)-st comparison of an alignment happens iff its first j characters match, probability
  σ^(−j)); so all patterns cost at most 2P·N on average, against Θ(N·L) in the worst case. Check:
  `test_naive_expected_cost_on_random_text` (exact averages over all texts: σ = 2, N = 0..7, patterns of length 1..4;
  σ = 3, N = 0..4, length 1..3).
- *Caveat: reporting occurrences.* A variant that reports every occurrence individually has an output with one item
  per occurrence, so it needs at least one step per occurrence; this implementation returns counts only, and its
  costs above do not depend on the number of occurrences.
- *Caveat: σ.* With child lists, a lookup costs up to σ comparisons, so the general bound is O(σ(N + L)) (section 10
  (a)).
- *a^N with the patterns a, …, a^n:* exactly N + n(n + 1)/2 − 1 comparisons, fewer than the N + L input characters
  (section 6); 1551 comparisons for N = 1024, n = 32, with 32272 occurrences.
- *The implementations use only `len()`, indexing, iteration and ==/!= on characters,* so every character comparison
  goes through `CountingChar` and none happens inside a CPython built-in (by inspection of the three files).
- *The V1 oracle (`harness.py`, `check`).* `_count_find` restarts `str.find` one position after each match, so it finds
  every start position of every pattern once, overlapping ones included.
- *Measured, not proved:* the fit values, the shape-block results, the V1 agreement, the 1500 extra instances and the
  oracle-control tallies (4556 wrong outputs rejected, 480 correct ones accepted) are results of the recorded runs
  (`tools/validate.py --scaling`, `experiments/2026-10-06i_aho_corasick.py`).
