# Proofs: regular-expression matching, backtracking vs memoised vs Thompson

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code)
about its problem and its three matchers, from first principles and from the code in this folder. Sections 1 to 3
prove the exact comparison counts on P_n, for every size of their domains. Sections 4 to 9 prove the rest: the
correctness of the three matchers (for Thompson's simulation with the corrected invariant), their call, evaluation,
time and space bounds, the uncounted work, and the caveats (including the backreference example). Each proof is
followed by the deterministic scripts or tests that check it and the ranges they check; a check covers only those
ranges, the proofs cover the general statements. Citations give credit; they are never part of a proof.

## Counting convention

`harness.py`, class `CountingChar`: `__eq__` adds 1 to the module counter `_cmps` (`_cmps += 1`) and then compares
the wrapped character with the other operand. No other operation counts. `generate_scaling(n, rng)` returns the
pattern `"a?" * n + "a" * n` as a plain string and the text aⁿ as a tuple of n `CountingChar("a")`, and sets
`_cmps = 0`; `reported_cost(output)` returns `_cmps`.

The only comparison that involves a text character is `c == text[j]` (in `char_ok` of `match_backtracking` and of
`match_memoized`) and `c == x` with `x = text[j]` (in `match_thompson`), where `c` is a one-character `str`.
`str.__eq__` returns `NotImplemented` for a `CountingChar` operand, so Python calls the reflected
`CountingChar.__eq__` once: each such comparison counts exactly 1. The test `c == "."` compares two strings and is
not counted; it runs first and is false for c = "a", so `c == text[j]` always runs after it. Not counted:
`parse`, the dictionary operations on keys (i, j) of plain ints, the epsilon-closure, and all tests on plain ints
(`i == m`, `j == n`, `j < n`, `s == m`, `m in current`).

**Scaling instance.** `parse` turns the pattern into m = 2n atoms: ('a', '?') for 0 ≤ i < n and ('a', '') for
n ≤ i < 2n. The text has length n. So `char_ok(c, j)` is called only when j < n, compares 'a' with 'a' (one
counted comparison) and returns true.

## 1. Backtracking: (n + 2)·2^(n−1) − 1

**Statement.** On P_n, `match_backtracking` makes exactly (n + 2)·2^(n−1) − 1 comparisons, for every n ≥ 0:
2ⁿ − 1 in the calls on the optional atoms and n·2^(n−1) in the calls on the plain atoms. It returns true.

**Proof.** Given in `entry.json`, field `algorithms[0].correctness` (one comparison per internal node of the full
binary tree of the n optional atoms, 2ⁿ − 1; the branch that consumed j characters then makes n − j comparisons on
the plain atoms; Σ_j C(n, j)(n − j) = n·2^(n−1)). At n = 0 the tree is the single call `match(0, 0)`, which
returns true at once: 0 = (0 + 2)·2^(−1) − 1. At the V2 size n = 16 the count is 18·2^15 − 1 = 589823.

**Check.** At the V2 sizes n = 4, 6, 8, 10, 12, 14, 16: `experiments/2026-10-07b_regex_counts.py` (n = 0..16).
`experiments/2026-10-07_closed_form_checks.py`, group `strings`, line "regex backtracking (n+2)2^(n-1)-1":
n = 0..18. `experiments/2026-10-07_count_proof_checks.py`, group `strings`, line "regex backtracking split: 2^n-1
in the optional atoms, n2^(n-1) in the plain atoms": n = 0..14.

## 2. Memoised backtracking: n(n + 1)

**Statement.** On P_n, `match_memoized` makes exactly n(n + 1) comparisons, for every n ≥ 0: n(n + 1)/2 in calls
with i < n and n(n + 1)/2 in calls with i ≥ n. It returns true.

**Proof.** Given in `entry.json`, field `algorithms[1].correctness`. The missing steps are why exactly these states
are evaluated and why each costs one comparison:

- A call whose key (i, j) is already in `memo` returns before any comparison. A key is evaluated at most once: the
  calls made while evaluating (i, j) have a larger i + j, so (i, j) is stored before it can be requested again.
  An evaluated state with i < 2n and j < n makes exactly one comparison (`char_ok`); a state with j = n or i = 2n
  makes none.
- *Optional atoms.* An evaluated state (i, j) with i < n has j ≤ i < n. It compares, then calls (i + 1, j + 1).
  That call returns false: from it the remaining atoms include all n plain atoms, which need n characters, and only
  n − j − 1 < n are left. So the `or` also calls (i + 1, j). From (0, 0), by induction on i, the evaluated states
  with i ≤ n are exactly the (i, j) with 0 ≤ j ≤ i ≤ n. Those with i < n cost Σ_{i=0..n−1} (i + 1) = n(n + 1)/2.
- *Plain atoms.* A state (i, j) with n ≤ i < 2n and j < n compares and calls only (i + 1, j + 1); with j = n it
  returns false without a comparison. So from (n, j), 0 ≤ j ≤ n, the evaluated states are (n + s, j + s) for
  0 ≤ s ≤ n − j, and those with j + s < n, that is n − j of them, cost 1 each; the chain ends at (2n − j, n)
  (at (2n, n), where `i == m` returns true, when j = 0). Chains with different j lie on different diagonals
  i − j = n − j, so they share no state. Total Σ_{j=0..n} (n − j) = n(n + 1)/2.

Together n(n + 1); at n = 0 the single call returns at once, 0 comparisons. At the V2 size n = 128 the count is
16512.

**Check.** At the V2 sizes n = 8, 16, 32, 64: `experiments/2026-10-07b_regex_counts.py` (n = 0..16, 24, 32, 48,
64; it does not run n = 128). `experiments/2026-10-07_closed_form_checks.py`, group `strings`, line "regex
memoised n(n+1)": n = 0..40, 48, 64, 100, 128 (all V2 sizes 8, 16, 32, 64, 128).
`experiments/2026-10-07_count_proof_checks.py`, group `strings`, line "regex memoised split: n(n+1)/2 with i < n,
n(n+1)/2 with i >= n": n = 0..40.

## 3. Thompson's NFA simulation: n(n + 1)

**Statement.** On P_n, `match_thompson` makes exactly n(n + 1) comparisons, n + 1 for each text character, for
every n ≥ 0. It returns true.

**Proof.** Given in `entry.json`, field `algorithms[2].correctness`. The missing step is the invariant itself:
before character j (0 ≤ j ≤ n − 1) the list `current` is {j, j + 1, …, n + j}. For j = 0: `closure([0])` marks
0, 1, …, n (atoms 0..n − 1 are optional; atom n is plain, or n = m when n = 0, and the walk stops there). Step:
every state s of {j, …, n + j} has s ≤ 2n − 1 < m, so `s == m` is false; its atom is ('a', '?') or ('a', ''), so
`c == "."` is false and `c == x` compares 'a' with 'a' (1 comparison, true) and appends s + 1. Hence
`nxt` = {j + 1, …, n + j + 1}; the closure adds only states in [j + 1, n], which are already present (j + 1 ≤ n),
so `current` = {j + 1, …, n + j + 1}. It is never empty, so the loop never returns early. Each of the n characters
costs n + 1 comparisons. After the last character `current` = {n, …, 2n} contains m = 2n, so the answer is true.
At n = 0 the loop does not run: 0 comparisons.

**Check.** At the V2 sizes n = 8, 16, 32, 64: `experiments/2026-10-07b_regex_counts.py` (n = 0..16, 24, 32, 48,
64; it does not run n = 128). `experiments/2026-10-07_closed_form_checks.py`, group `strings`, line "regex
Thompson n(n+1)": n = 0..40, 48, 64, 100, 128 (all V2 sizes 8, 16, 32, 64, 128).
`experiments/2026-10-07_count_proof_checks.py`, group `strings`, line "regex Thompson: n+1 comparisons per text
character": n = 0..40.

## Conventions for sections 4 to 9

*Semantics* (the dialect of `problem_statement`). For an atom a, L(a) is the set of texts it matches: L(c) = {c} for
a letter c, L(.) = the 26 letters, L(c?) = {ε} ∪ L(c), L(c*) = L(c)* (all concatenations of zero or more words of
L(c)). A pattern a₀ … a_{m−1} fully matches a text t iff t ∈ L(a₀)L(a₁)⋯L(a_{m−1}) (concatenation of languages). Write
R_i = L(a_i)⋯L(a_{m−1}) (R_m = {ε}), P_i = L(a₀)⋯L(a_{i−1}) (P₀ = {ε}), and X_i = L(a_i) if atom i is starred and
X_i = {ε} otherwise (also for i = m). ε ∈ L(a) iff a is optional ('?' or '*'). Texts are over a–z, n = |t|, and t[j:]
is the suffix from position j. That Python's `re.fullmatch` has the same semantics on this dialect is a tested
statement (V1 and the checks below compare with it), not part of any proof.

*Cost model.* Unit cost per executed line with O(1)-size operands, one step per dictionary operation (as
`algorithms[1].time_complexity` states), O(k) to build a list of k entries. O and Θ are the usual asymptotic bounds over
the inputs: a bound may fail on at most finitely many inputs, never on an infinite family; where a parameter can be 0
(m, |t|), the bounds carry an explicit + 1, so that no infinite family of inputs violates them (for example, the empty
pattern against a long text costs O(1)).

## 4. The semantics of one atom

**Lemma 4.1.** For i < m: if atom i is a plain c, R_i = L(c)R_{i+1}; if it is c?, R_i = R_{i+1} ∪ L(c)R_{i+1}; if it is
c*, R_i = R_{i+1} ∪ L(c)R_i. In `char_ok(c, j)` (and in Thompson's `c == "." or c == x`) the test is true iff
t[j] ∈ L(c).

**Proof.** The first two are the definitions of L(c) and L(c?). For c*: L(c)* = {ε} ∪ L(c)L(c)*, so
R_i = L(c)*R_{i+1} = R_{i+1} ∪ L(c)L(c)*R_{i+1} = R_{i+1} ∪ L(c)R_i. The test `c == "." or c == t[j]` is true iff c is
'.' (which matches every letter) or c is the letter t[j]. ∎

## 5. Backtracking: correctness, calls, depth and space

**Statement** (`algorithms[0].correctness`, `time_complexity`, `space_complexity`; `backtracking.py` docstring).
`match(i, j)` returns True iff t[j:] ∈ R_i, so `match_backtracking` decides full matching. Every call makes at most
two recursive calls, each with a larger i + j, so the recursion depth is at most m + n + 1, there are at most
2^(m+n+1) − 1 calls, and the time is O(2^(m+|t|)) (plus O(m + 1) to parse); on P_n it is exponential (section 1). The
space is O(m + |t|).

**Proof.** j never exceeds n, since `match(·, j + 1)` is called only after `j < n`. Each recursive call
(`match(i + 1, j + 1)`, `match(i + 1, j)` or `match(i, j + 1)`) increases i + j by at least 1, and i + j ≤ m + n, so a
chain of nested calls has at most m + n + 1 calls; with at most two calls per call there are at most
2^(m+n+1) − 1 calls. By induction on (m − i) + (n − j): for i = m the function returns `j == n`, i.e. t[j:] ∈ {ε}.
For i < m, by Lemma 4.1 and the induction hypothesis, the plain case returns `j < n and t[j] ∈ L(c) and
t[j+1:] ∈ R_{i+1}`, which is t[j:] ∈ L(c)R_{i+1}; the case c? returns that or t[j:] ∈ R_{i+1}; the case c* returns
`(j < n and t[j] ∈ L(c) and t[j+1:] ∈ R_i) or t[j:] ∈ R_{i+1}`, which is t[j:] ∈ L(c)R_i ∪ R_{i+1} = R_i. The values
are booleans (`and`/`or` of booleans). The answer is `match(0, 0)`, i.e. t ∈ R₀. Each call does O(1) work besides
its recursive calls, which gives the time bound. Space: the parsed atoms (O(m)) and at most m + n + 1 frames of O(1)
words. ∎

**Check.** `tests/test_proofs_regex.py`, `test_correctness_and_thompson_invariant`: for every pattern of at most 3
atoms over {a, b, .} with quantifiers '', '?', '*' (820 patterns) and every text over {a, b} of length at most 4 (31
texts), the answer equals a direct transcription of the definition (the sets F[i] = {j : t[:j] ∈ P_i}) and Python's
`re.fullmatch`. `test_call_bounds` (every 13th of these cases): at most 2^(m+n+1) − 1 calls and depth at most
m + n + 1. Also the validator's V1 battery and the experiment's battery of 3300 instances.

## 6. Memoised backtracking: correctness, evaluations and space

**Statement** (`algorithms[1].correctness`, `time_complexity`, `space_complexity`; `memoized.py` docstring). The
memoised matcher returns the same answers. It evaluates each key (i, j) at most once, so at most (m + 1)(n + 1) keys,
with at most 1 + 2(m + 1)(n + 1) calls, each with O(1) work and O(1) dictionary operations: O((m + 1)(|t| + 1)) time,
O(n²) for the stated size parameter n. The space is O((m + 1)(|t| + 1)): at most (m + 1)(n + 1) memo entries and
recursion depth at most m + n + 1.

**Proof.** The body computes `result` by the same expressions as section 5, so by induction on (m − i) + (n − j) it
stores and returns [t[j:] ∈ R_i]; a key found in `memo` returns the stored value. The calls made while evaluating
(i, j) have a larger i + j (section 5), so (i, j) is not requested again before it is stored, and afterwards it is
answered from `memo`: each key is evaluated at most once. Keys satisfy 0 ≤ i ≤ m and 0 ≤ j ≤ n. Each evaluation makes
at most two calls, and every call other than the first is made by an evaluation. Depth: as in section 5. With
m ≤ 2n and |t| ≤ 2n for the size parameter n, (m + 1)(|t| + 1) = O(n²). ∎

**Check.** `test_correctness_and_thompson_invariant` (the cases of section 5): same answers. `test_call_bounds`
(every 13th case): at most (m + 1)(n + 1) evaluations, at most 1 + 2·(evaluations) calls, depth at most m + n + 1.
`test_distinct_evaluations` (every 13th case, shifted): no key is evaluated twice.

## 7. Thompson's simulation: correctness (the corrected invariant), time and space

**Statement** (`algorithms[2].correctness`, `time_complexity`, `space_complexity`; `thompson.py` docstring). Let S_j
be the list `current` before text character j is read (j = 0, …, n − 1) and after the last one (j = n). Then
S_j = {i : 0 ≤ i ≤ m, t[:j] ∈ P_i·X_i}, listed in increasing order: the atom positions i such that t[:j] fully matches
atoms[:i] followed by c* when atom i is a starred atom c*, and atoms[:i] alone otherwise. This set is closed under
skipping optional atoms. The function returns True iff m ∈ S_n, i.e. iff t matches. It runs in O((m + 1)(|t| + 1))
time with at most m + 1 active states, and its working storage is O(m + 1).

**Lemma 7.1 (closure).** `closure(states)` returns, in increasing order and without repetition, the set of all s′
such that s ≤ s′ for some s in `states` and the atoms s, …, s′ − 1 are all optional; it runs in O(m + 1 + |states|).

*Proof.* The walk started at s marks s, s + 1, … and stops after marking a state that is m or has a non-optional
atom, or before a state that is already marked. Every marked state is in the stated set. After each walk the marked
set is closed forward (a marked s′ < m with an optional atom has s′ + 1 marked): the walk's last marked state either
has no obligation or is followed by an already marked state, and earlier marked states satisfied the property before.
So at the end the marked set contains `states` and is closed forward, hence contains the stated set. Each state is
marked at most once, each walk stops after O(1) steps beyond its marks, and the final list costs O(m + 1). ∎

**Proof of the statement.** *Closed under skipping.* If t[:j] ∈ P_i X_i and atom i is optional, then
t[:j] ∈ P_{i+1}X_{i+1} = P_i L(a_i) X_{i+1}: for c?, X_i = {ε} and ε ∈ L(a_i), ε ∈ X_{i+1}; for c*, X_i = L(a_i).

*j = 0.* ε ∈ P_i X_i iff ε ∈ P_i iff atoms 0, …, i − 1 are optional, which is `closure([0])` by Lemma 7.1.

*Step.* Let x = t[j]. The loop builds `nxt` = {i + 1 : i ∈ S_j, i < m, atom i is c or c? with x ∈ L(c)} ∪
{i : i ∈ S_j, atom i is c* with x ∈ L(c)}, and S_{j+1}′ = `closure(nxt)`. We show S_{j+1}′ = S_{j+1}.
(⊆) As S_{j+1} is closed under skipping, it suffices that `nxt` ⊆ S_{j+1}. If i ∈ S_j has atom c or c? and x ∈ L(c),
then t[:j] ∈ P_i (X_i = {ε}), so t[:j+1] ∈ P_i L(a_i) = P_{i+1} ⊆ P_{i+1}X_{i+1}. If i ∈ S_j has atom c* and x ∈ L(c),
then t[:j+1] ∈ P_i L(c)* L(c) ⊆ P_i L(c)* = P_i X_i.
(⊇) Let t[:j+1] ∈ P_{i′}X_{i′}: t[:j+1] = u₀⋯u_{i′−1}v with u_k ∈ L(a_k), v ∈ X_{i′}. If v ≠ ε, atom i′ is c* and
v = v′x with v′ ∈ L(c)*, x ∈ L(c); then t[:j] ∈ P_{i′}L(c)* = P_{i′}X_{i′}, so i′ ∈ S_j and i′ ∈ `nxt`. If v = ε, let k
be the last index with u_k ≠ ε (it exists, as t[:j+1] ≠ ε); the atoms k + 1, …, i′ − 1 are optional (their words are
ε), and u_k ends with x. If atom k is c or c?, then u_k = x with x ∈ L(c) and t[:j] = u₀⋯u_{k−1} ∈ P_k = P_kX_k, so
k ∈ S_j and k + 1 ∈ `nxt`, and i′ is reached from k + 1 by skipping optional atoms. If atom k is c*, u_k = u′x with
u′ ∈ L(c)*, x ∈ L(c), so t[:j] ∈ P_k L(c)* = P_kX_k, k ∈ S_j and k ∈ `nxt`; atom k is optional, so i′ is reached from k
by skipping. In both cases i′ ∈ `closure(nxt)` (Lemma 7.1).

*Answer.* t matches iff t ∈ P_m = P_m X_m iff m ∈ S_n. If some S_{j+1} is empty, the function returns False at once;
this is correct, because then every later state set is empty too (`closure([])` = ∅) and m ∉ S_n. State m has no
transition (`if s == m: continue`).

*Time and space.* Each step loops over at most m + 1 states with O(1) work each and calls `closure` on at most
m + 1 states, O(m + 1) by Lemma 7.1; the initial closure is O(m + 1). Total O((m + 1)(n + 1)).
`current`, `nxt` and `seen` have at most m + 1 entries. ∎

The method is Thompson's (1968); the invariant and its proof above are this project's. (The invariant first stated in
the entry, "t[:j] fully matches atoms[:i]", was false for starred atoms: pattern a*, text a gives S₁ = {0, 1}; it was
corrected in RESEARCH_LOG RL-102, and the corrected form is the one proved here.)

**Check.** `test_correctness_and_thompson_invariant`: on the 820 × 31 cases of section 5 the answer equals the
definition; on all cases with texts of length at most 3 and a third of those of length 4, every state set `current`
(read by a line tracer before each character and at the end) equals {i : j ∈ Q[i]}, where Q[i] = {j : t[:j] ∈ P_iX_i}
is computed directly from the definition, and after an early return the next set is empty and the text does not
match. `test_thompson_state_sets_and_steps` (every 11th case): at most m + 1 entries in `current` and `nxt`, and at most
n(14(m + 1) + 10) + 8(m + 1) + 12 executed lines (constants read off the code).

## 8. The uncounted work (caveat)

**Statement** (`caveats`). The counts are symbol–character comparisons; loop control, the epsilon-closure and the
dictionary operations are not counted. On P_n this uncounted work is O(1) per counted comparison (n ≥ 1), so the exact
counts give the asymptotic costs there: backtracking makes exactly (n + 4)2^(n−1) − 1 calls for
(n + 2)2^(n−1) − 1 comparisons; the memoised matcher evaluates exactly (n + 1)² states for n(n + 1) comparisons; and
Thompson's simulation does O(m) = O(n) work per character for n + 1 comparisons. The general bounds of sections 5 to
7 count calls, evaluations or states, so they include the uncounted work. (In general, comparisons alone do not bound
the work: an atom '.' is matched without a counted comparison.)

**Proof.** *Backtracking on P_n.* The calls on the optional atoms form a full binary tree with 2ⁿ − 1 calls at i < n,
each with j ≤ i < n (section 1), and 2ⁿ calls at i = n, one for each subset of consumed characters; the call that
reaches the plain atoms with j consumed characters continues with the calls (n + s, j + s), s = 0, …, n − j, that is
n − j + 1 calls. Total 2ⁿ − 1 + Σ_j C(n, j)(n − j + 1) = 2ⁿ − 1 + n2^(n−1) + 2ⁿ = (n + 4)2^(n−1) − 1, which is at most
2((n + 2)2^(n−1) − 1) + 1. Each call does O(1) uncounted work.
*Memoised on P_n.* The evaluated states are (i, j) with 0 ≤ j ≤ i < n, n(n + 1)/2 of them, and the chains
(n + s, j + s), 0 ≤ s ≤ n − j, for j = 0, …, n, (n + 1)(n + 2)/2 of them (section 2): (n + 1)² in all, at most
2n(n + 1) for n ≥ 1; calls are at most 1 + 2(n + 1)².
*Thompson on P_n.* m = 2n; each character costs O(m) = O(n) besides its n + 1 comparisons (section 7).
*'.' atoms.* `c == "."` is true and short-circuits `c == x`, so no comparison is counted. ∎

**Check.** `test_uncounted_work_on_P_n` (n = 0..12): exactly (n + 4)2^(n−1) − 1 backtracking calls (counted by a line
tracer), exactly (n + 1)² memoised evaluations, at most 30n(n + 1) + 30 executed lines in Thompson's simulation, and
the comparison counts of sections 1 to 3 (with the harness's `CountingChar`).

## 9. The remaining claims

- *Relationship.* On P_n, (n + 2)2^(n−1) − 1 comparisons against n(n + 1) (sections 1 to 3). The blow-up comes from
  re-exploring subproblems: backtracking makes (n + 4)2^(n−1) − 1 calls (section 8) but there are at most
  (2n + 1)(n + 1) distinct keys (i, j), so some key is evaluated exponentially often; memoising (i, j) gives the
  polynomial bound of section 6, and Thompson's simulation reaches O((m + 1)(|t| + 1)) with neither recursion nor a table
  (section 7), reading the text once from left to right.
- *Caveat: backreferences.* A backreference \1 matches again the text matched by the first group. With it, the
  pattern (a*)b\1 matches exactly the texts aᵏbaᵏ (k ≥ 0), and this language L is not regular: if a finite automaton
  with p states accepted L, two of the prefixes a⁰, …, a^p, say aⁱ and aʲ with i < j, would lead to the same state, so
  with aⁱbaⁱ ∈ L it would also accept aʲbaⁱ ∉ L. So backreferences can make the language non-regular. They are outside
  the dialect: `parse` rejects parentheses and backslashes, so neither the NFA simulation nor the other matchers handle
  them. Check: `test_backreference_example` (Python's `re`: (a*)b\1 matches exactly aᵏbaᵏ among the texts over {a, b}
  of length at most 9; aⁱbaⁱ is matched and aʲbaⁱ is not for i ≠ j ≤ 8; `parse` raises `ValueError` on (a*)b\1, (a),
  a|b and a\1).
- *Caveat: the exponential cost is a worst case.* Section 1 shows it on P_n; it is not claimed for other patterns.
- *Python's re* is used only in `harness.check` (V1) and in the checks; it is never timed and no proof uses it.
- *Measured, not proved:* the fit values α and the log-factor diagnostics, the V1 agreement with `re.fullmatch`, and
  the experiment's battery (0 disagreements in 3300 instances) are results of the recorded runs
  (`tools/validate.py --scaling`, `experiments/2026-10-07b_regex_counts.py`).
