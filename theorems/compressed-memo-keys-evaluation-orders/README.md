# Compressed memo keys: when is dropping a flag from the key exact for every evaluation order?

> **Provenance: own result.** The literature search described under [Literature search](#literature-search) found
> no source that states these results. This is a statement about that search, not a claim of priority. Part of the
> proof is computer-assisted: the certificates are public ([certificates.txt.gz](certificates.txt.gz)) and
> [verify.py](verify.py) checks all of them.

A memoized recursion over states (m, p) is sometimes run with a **compressed key**: the table is indexed by m only,
and the flag p is dropped. Each m is then evaluated once, with the flag of one of its requests, so the result can
depend on the evaluation order. This note answers, for an explicit family of recurrences, exactly
when such a run is correct for every input and every evaluation order.

## Setting

**The family F.** A *spec* consists of
- an ordered list of k ∈ {2, 3} moves (d_i, f_i), i = 0, …, k − 1, with offsets d_i ∈ {1, 2, 3, 4} and flips
  f_i ∈ {0, 1}; the base is b = max d_i;
- δ ∈ {0, 1, 2}, a combine mode (sum, min or max) and coefficients c_i ∈ {1, …, 9}.

Moves are written as pairs, for example "(3,0),(3,0),(4,1)". The input is a data vector in {0, …, 9}^17, with
D[m] = data[m mod 17]. Let P = 1 000 003, a prime (verify.py checks it by trial division). For m ≥ 0 and
p ∈ {0, 1}:

    leaves (m < b):   V(m, p) = D[m] + δp
    sum:              V(m, p) = D[m](1 + δp) + Σ_i c_i V(m − d_i, p ⊕ f_i)          (mod P)
    min / max:        V(m, p) = opt_i [ V(m − d_i, p ⊕ f_i) + w_i(m)(1 + δp) ],     w_i(m) = (c_i D[m] + i) mod 10

where opt is min or max. The value to compute is V(n, 0). Nodes m ≥ b are *internal*.

**Reachable states.** R(n) is the set of states reachable from (n, 0) by moves from internal states, and M(n) the
set of their nodes m. A node m ∈ M(n) is *ambiguous* if both (m, 0) and (m, 1) are in R(n).
- **PF** (the flag is functional at n): no node of M(n) is ambiguous.
- **VF** (the value is constant on fibres at n, for given data): V(m, 0) = V(m, 1) for every ambiguous node m.
- The **lattice criterion** of a spec: with g = gcd(d_i), there is c ∈ {0, 1} with f_i ≡ c·d_i/g (mod 2) for all i.

**Compressed runs.** A *flag assignment* is a map p: M(n) → {0, 1}. Its compressed values are computed bottom-up:
memo_p[m] = D[m] + δp_m for leaves, and for internal m the recurrence above with the flag p_m and the children's
values memo_p[m − d_i] in place of V(m − d_i, ·). The run is *exact* if memo_p[n] = V(n, 0).

**Evaluation orders.** The *explicit-stack procedure* is top-down memoization keyed by m only. It starts with the
stack [(n, 0)] and repeats: let (m, p) be the top entry; if m is already evaluated, pop it; if m is a leaf,
evaluate it with flag p and pop it; if some children m − d_i are not evaluated, push the entries
(m − d_i, p ⊕ f_i) for those i, in some order; otherwise evaluate m with flag p from its children and pop it. The
flags with which the nodes are evaluated form its *induced assignment*. Three models of "every evaluation order":
- **Model G:** the push order is one fixed permutation of the move indices, the same at every step (k! orders).
- **Model D:** the push order may be chosen anew at every step.
- **Model S:** every *supported* assignment: p_n = 0, and every m ∈ M(n) other than n has an internal parent
  m′ = m + d_i ∈ M(n) with p_m = p_m′ ⊕ f_i.

**The orders O(π, R).** For a sequence π of move indices (the *descent*) and a permutation R of the move indices,
O(π, R) is the following recursive depth-first search from (n, 0). Visiting (m, p) does nothing if m is marked;
otherwise it marks m with flag p and, if m is internal, visits (m − d_i, p ⊕ f_i) for the move indices i in the
node's visit order. The descent nodes x_0 = n, x_t = x_(t−1) − d_(π_t) (as long as they are internal) visit their
descent child first and then the others in the order R; every other node visits its children in the order R. By
the stack lemma below, O(π, R) is a model-D order, and O(∅, R) are exactly the model-G orders.

## Statement

**Theorem 1 (sufficiency, any order).** If VF holds at n for a data vector, then every supported assignment is
exact for that data vector. Consequently, if δ = 0 or PF holds at n, the compressed run is exact for every data
vector and every evaluation order of models G, D and S.

**Proposition 2 (lattice criterion).** (a) If a spec satisfies the lattice criterion, PF holds at every n.
(b) If it does not, there is an integer vector z with Σ z_i d_i = 0 and Σ z_i f_i odd, and PF fails at every
n ≥ b + D, where D = Σ_{z_i > 0} z_i d_i. In the family F one can take D ≤ 12.

**Proposition 3 (one order is not enough).** For the spec (1,0),(1,1), δ = 2, max, c = (4, 4) and n = 1, the
order that evaluates node 0 with flag 1 (the explicit-stack procedure pushing in move order) is exact for every
data vector, although node 0 is ambiguous, δ > 0, and VF fails for every data vector. So exactness under one fixed
order implies neither PF nor VF.

The natural converse of Theorem 1 asks: **if δ > 0 and PF fails at n, is there an evaluation order and a data
vector for which the compressed run is wrong?** The answer depends on the model.

**Theorem 4 (model G: no).** For the spec (1,1),(3,0),(3,1), δ = 1, sum, c = (1, 1, 1) and n = 4, PF fails, but
each of the 6 global orders is exact for every data vector. A model-D order is wrong for every data vector.

**Theorem 5 (model S, sum mode: yes).** For every spec of F in sum mode with δ > 0 and every n at which PF fails,
there are data in {0, 1}^17 and a supported assignment whose compressed result differs from V(n, 0).

**Theorem 6 (model D, min and max: yes; computer-assisted).** For every spec of F in min or max mode with δ > 0
and every n at which PF fails, there are a model-D order and data in {0, …, 9}^17 for which the compressed result
differs from V(n, 0).

**Theorem 7 (model D, sum mode: yes; computer-assisted).** The same holds in sum mode, with data in {0, 1}^17.

**Corollary 8.** For every spec of F and every n, in model D and in model S:

    the compressed run is exact for every data vector and every evaluation order  ⟺  δ = 0 or PF holds at n.

In model G the direction "⟹" fails (Theorem 4).

*Proof of Corollary 8.* "⟸" is Theorem 1. For "⟹", let δ > 0 and let PF fail at n. By Proposition 2(a) the spec
fails the lattice criterion. Theorems 6 and 7 give a model-D order and data with a wrong result. By the stack lemma
the induced assignment of that order is supported and gives the same result, so model S fails too. ∎

## Proofs

### Orders and assignments

**Stack lemma.** (i) In a run of the explicit-stack procedure, each node is evaluated exactly once, from its
children's values; the induced assignment p is supported, and the run returns memo_p[n]. Hence G ⊆ D ⊆ S as sets
of induced assignments. (ii) The model-D runs induce exactly the assignments of the recursive depth-first searches
with an arbitrary visit order at every node (marking a node at its first visit and skipping marked nodes); in
particular O(π, R) is a model-D order, and with a fixed push order σ the procedure induces the assignment of
O(∅, reverse of σ).

*Proof.* (i) When an entry (m, p) is expanded, every entry pushed above it is a child or a descendant of m, so its
node is smaller than m. Hence no other entry with node m can be evaluated before (m, p) is on top again, and then
m is evaluated with flag p. An entry is pushed only by an expanded parent (m′, p′), as (m′ − d_i, p′ ⊕ f_i), and
that parent is later evaluated with flag p′. So every evaluated flag is p_m′ ⊕ f_i for an internal parent m′ in
M(n), which is supportedness; p_n = 0 because the root entry is (n, 0). Each node is evaluated once, from its
children's values with its own flag, so the result is memo_p[n]. (ii) By (i) each node is expanded with a nonempty
set of missing children at most once, so choosing a push order at every step is the same as choosing one visit
order per node (the reverse of the push order). The children are processed in reverse push order; an entry whose
node a sibling's subtree has evaluated in the meantime is popped without effect, which is "skip if marked". Marking
at the first visit instead of at evaluation changes nothing, because a node cannot be requested while it is being
processed (requests go to smaller nodes). Two moves with the same offset and different flips give two entries for
the same node; the one processed first wins, which a visit order of move indices also expresses. ∎

*Proof of Theorem 1.* Let p be supported. Top-down, every (m, p_m) lies in R(n): (n, 0) does, and
p_m = p_m′ ⊕ f_i for an internal parent m′ with (m′, p_m′) ∈ R(n). Bottom-up, memo_p[m] = V(m, p_m): for leaves by
definition; for internal m, both (m − d_i, p_(m−d_i)) and (m − d_i, p_m ⊕ f_i) lie in R(n), so by VF
memo_p[m − d_i] = V(m − d_i, p_(m−d_i)) = V(m − d_i, p_m ⊕ f_i), and the recurrence gives V(m, p_m). At the root,
memo_p[n] = V(n, 0). If PF holds, VF holds trivially. If δ = 0, p enters the recurrence only through δp, so
V(m, 0) = V(m, 1) for every m. The last sentence follows with the stack lemma. ∎

*Proof of Proposition 2.* (a) A move sequence from n to m has total n − m = Σ_i t_i d_i (t_i = number of uses of
move i) and ends with flag Σ_i t_i f_i ≡ c Σ_i t_i d_i/g = c(n − m)/g (mod 2), which depends on m only. (b) The map
z ↦ Σ z_i f_i mod 2 on ℤ^k does not vanish on Λ = {z : Σ z_i d_i = 0}: if it did, it would factor through
ℤ^k/Λ ≅ gℤ ≅ ℤ, z ↦ Σ z_i d_i/g, so f_i ≡ c d_i/g for c = the image of 1, which is the criterion. Take z ∈ Λ with
Σ z_i f_i odd, write z = z⁺ − z⁻, and D = Σ z⁺_i d_i = Σ z⁻_i d_i. For n ≥ b + D, the moves of z⁺ (in any order)
and the moves of z⁻ both lead from n to n − D through nodes > n − D ≥ b, which are internal, with flags of
different parity. So n − D is ambiguous. verify.py finds such a z with D ≤ 12 for each of the 96 move multisets
that fail the criterion. ∎

*Proof of Proposition 3.* Here b = 1, and the root 1 has the two children (0, 0) and (0, 1), so node 0 is
ambiguous. V(0, 0) = D[0] and V(0, 1) = D[0] + 2, so VF fails for every data vector. With w = w_0(1) =
(4 D[1]) mod 10, which is even, w_1(1) = w + 1. The truth is max(D[0] + w, D[0] + 2 + w + 1) = D[0] + w + 3. With
node 0 evaluated with flag 1, memo[0] = D[0] + 2 and the result is max(D[0] + 2 + w, D[0] + 2 + w + 1) =
D[0] + w + 3, exact. With flag 0 the result is D[0] + w + 1, off by −2. Pushing in move order puts (0, 1) on top,
so node 0 is evaluated with flag 1. verify.py checks all 100 values of (D[0], D[1]), the only entries read. ∎

### Sum mode: the error formula

**Error lemma.** In sum mode, for any assignment p: M(n) → {0, 1},

    memo_p[n] − V(n, 0) ≡ δ Σ_{m ∈ M(n)} D̃_m · (p_m N(m) − N_1(m))      (mod P),

where N_q(m) is the sum, over the paths of the call tree from (n, 0) to (m, q), of the product of the coefficients
used, N(m) = N_0(m) + N_1(m), and D̃_m = D[m] for internal m and 1 for leaves.

*Proof.* Write loc(m, q) = D[m](1 + δq) for internal m and D[m] + δq for leaves; loc(m, q) = loc(m, 0) + δq·D̃_m.
Unrolling the linear recurrence, V(n, 0) = Σ_(m,q) N_q(m)·loc(m, q). The compressed recurrence unrolls along the
DAG of nodes: memo_p[n] = Σ_m Ñ(m)·loc(m, p_m), where Ñ(m) is the sum over move sequences from n to m of the
products of coefficients. Every such sequence reaches (m, its parity) in the call tree, so Ñ(m) = N(m).
Subtracting gives the formula. ∎

*Proof of Theorem 4.* Here b = 3. From (4, 0) the moves give (3, 1), (1, 0), (1, 1); from (3, 1) they give
(2, 0), (0, 1), (0, 0). Nodes 1 and 0 are ambiguous, so PF fails. For the assignments of global and model-D
orders, which are supported (stack lemma) and so use only flags of R(n) (proof of Theorem 1), a non-ambiguous node
contributes 0 in the error lemma (if its only reachable flag is q, then N_(1−q) = 0 and p_m = q). Node 1 (a leaf) has
N_0(1) = c_1 = 1 and N_1(1) = c_2 = 1, node 0 has N_1(0) = c_0c_1 = 1 and N_0(0) = c_0c_2 = 1, so the error is
2δ(p_0 + p_1 − 1), whatever the data. Node 1 is
requested only by the root, through moves 1 (flag 0) and 2 (flag 1); node 0 is requested only by node 3, which has
flag 1, through moves 1 (flag 1) and 2 (flag 0). Under a global order with visit order R, p_1 = 0 and p_0 = 1 if
move 1 precedes move 2 in R, and p_1 = 1, p_0 = 0 otherwise. So p_0 + p_1 = 1 and every global order is exact for
every data vector. The model-D order that visits move 1 before move 2 at the root and move 2 before move 1 at node
3 gives p_0 = p_1 = 0 and the error −2δ ≠ 0 for every data vector. verify.py checks this by exact affine
evaluation. ∎

**Remark (model S is larger than model D).** For the moves (1,0),(2,0),(2,1) and n = 4, the assignment
{4: 0, 3: 0, 2: 1, 1: 0, 0: 0} is supported, but no choice of visit orders realises it (verify.py tries all 6^5
tables). So a statement for model S does not imply the one for model D, and Theorems 6–7 prove model D directly.

### Theorem 5 (model S, sum mode)

Let δ > 0, let PF fail at n, and let m* be the largest ambiguous node.

1. *Forced flags.* A non-ambiguous node m has the same flag t_m in every supported assignment, because a supported
   assignment uses only flags of R(n) (proof of Theorem 1).
2. *Two assignments.* The parents of m* are larger, hence non-ambiguous, so under every supported assignment m*
   is requested with both flags. Build p⁰ and p¹ together on M(n), in decreasing m: p⁰_n = p¹_n = 0, p⁰_m* = 0 and
   p¹_m* = 1; for every other m ∈ M(n), which has at least one internal parent in M(n), let Q⁰ and Q¹ be the sets
   of flags requested by m's parents under p⁰ and p¹; use a common element of Q⁰ ∩ Q¹
   for both if there is one; otherwise Q⁰ and Q¹ are disjoint one-element sets, and p⁰_m and p¹_m are their
   elements. Both assignments are supported. Let Δ = {m : p⁰_m ≠ p¹_m}.
3. *Δ lies below m\*.* Nodes larger than m* are non-ambiguous, so their flags agree (by induction from the top).
   If c ∈ Δ and c ≠ m*, then Q⁰ ∩ Q¹ = ∅, so every parent of c changes flag, that is, lies in Δ. Walking back
   from c along any root path stays in Δ until it reaches m*, because the root is not in Δ and nodes above m* are
   not. So every root path to c passes through m*: Δ ⊆ {m*} ∪ Dom(m*), where Dom(m*) is the set of nodes all of
   whose root paths pass through m*.
4. *The difference.* By the error lemma, E(p⁰) − E(p¹) = δ Σ_{m ∈ Δ} D̃_m (p⁰_m − p¹_m) N(m), where E(p) = memo_p[n] −
   V(n, 0).
   - If m* is a leaf, Dom(m*) = ∅ and the difference is the constant −δN(m*).
   - If m* is internal, the coefficient of data[m* mod 17] is −δN(m*) plus terms of internal c ∈ Δ with
     c ≡ m* (mod 17) and c < m*, so n − c ≥ 17. There are no such terms. If all offsets are equal (to d), the flips
     differ (otherwise PF holds), so every node c below the root has the single parent c + d, which requests both
     flags whatever its own flag is; a common flag is chosen, and Δ = {m*}. Otherwise the domination lemma below
     shows c ∉ Dom(m*).
5. *Nonzero.* 1 ≤ N(m*) < P by the finite fact below, P is prime and δ ∈ {1, 2}, so −δN(m*) ≢ 0 (mod P). Hence
   E(p⁰) and E(p¹) are different affine functions of the data, and one of them is not identically 0. A nonzero affine
   function mod P is nonzero at data = 0 (if its constant term is nonzero) or at a unit vector. ∎

**Domination lemma.** If the spec has two distinct offsets, c ∈ M(n) is internal and n − c ≥ 17, then for every m
with c < m < n some root path to c avoids m.
*Proof.* Reordering: a multiset of positive integers with at least two distinct values, total T, has for every
0 < s < T an ordering whose prefix sums avoid s. Take an ordering that hits s at position j. The first j and the
remaining elements are not both constant with the same value, so we may pick x ≠ x′ from the two parts, rearrange
each part so that x is at position j and x′ at position j + 1 (prefix sums below j stay below s, those after j + 1
stay above s), and swap them: the prefix sum at j becomes s − x + x′ ≠ s. Substitution: if all moves of a path to c
have the same offset u, take another offset v of the spec and replace v copies of u by u copies of v; this needs
L = (n − c)/u copies, and L > v since n − c ≥ 17 (L ≥ 5 > 3 if u = 4, L ≥ 6 > 4 if u ≤ 3), so the new multiset
still contains u and has two distinct values. Every intermediate node of any ordering exceeds c ≥ b, so every
ordering is a valid path. Apply reordering with s = n − m. ∎

**Finite fact: N(m\*) < P for every n.** N(m*) is a polynomial in the coefficients with nonnegative integer
coefficients, so it is largest when all c_i = 9; call that value N9. *Depth-translation lemma:* if n, n′ ≥ b + j,
node n − j (from (n, 0)) and node n′ − j (from (n′, 0)) have the same reachable flags and the same N_q, because a
root path of total j has all its proper intermediate nodes above n − j ≥ b, so the same move sequences are valid
from n′. *Closure:* for a spec satisfying the criterion PF always holds (Proposition 2(a)). For each of the 96 move
multisets that fail it, verify.py finds an ambiguous node of depth ≤ 12 at n = b + 12. By the depth-translation lemma
the ambiguity of every node of depth ≤ 12 is the same for all n ≥ b + 12, so m* has the same depth and the same N(m*)
for all n ≥ b + 12. So the maximum over all n equals the maximum over b ≤ n ≤ b + 12, which verify.py computes:
**N9(m*) ≤ 105 705 < P**, attained by (3,0),(3,0),(4,1) at n = 13, m* = 1. N(m*), PF and ambiguity do not depend on
the order of the moves, so the multisets cover all ordered lists. ∎

### Theorem 6 (model D, min and max)

**Zero data.** With data = 0, w_i(m) = i for every coefficient vector (i ≤ 2 < 10), and leaves are worth δp. The
coefficients occur nowhere else in min/max mode, so a wrong result with zero data is wrong for all 9^k coefficient
vectors at once.

**Notation for an order O(π, R).** Sg is the set of totals of move sequences (the monoid generated by the
offsets), g = gcd(d_i), F the largest multiple of g not in Sg (−1 if there is none), sub(x) the set of nodes
reachable from x through internal nodes (including x). For an internal node u ≤ x, u ∈ sub(x) iff x − u ∈ Sg.
Further: J = Σ_t d_(π_t), y = n − J, φ the flag of y along the descent, e = d_(R[0]) and f_e = f_(R[0]),
Ap = {s ∈ Sg : s < e or s − e ∉ Sg}, A = max Ap, M0 = b + A + 4, K = J + F + 1 and
N0 = max(K + M0 + 2e + 7, J + F + 4 + b). The proofs use N0 through three consequences:
(a) N0 − K ≥ M0 + 2e + 7; (b) y ≥ F + 4 + b; (c) every level used below is ≥ N0 − K ≥ M0.

*Apéry facts.* Every x ∈ Sg is uniquely x = je + s with j ≥ 0 and s ∈ Ap: take j maximal with x − je ∈ Sg; if
je + s = j′e + s′ with j < j′, then s − e ∈ Sg, a contradiction. For s ∈ Ap with s ≥ e, s − e ∉ Sg and
s − e ≡ 0 (mod g), so s ≤ F + e; hence A ≤ F + e.

**Fresh-subtree lemma.** If no node of sub(x) is marked when x is first visited, the visit of x marks exactly
sub(x), and the marks depend only on x's flag and the visit orders inside sub(x): the recursion from x reaches and
tests only nodes of sub(x).

**Descent lemma.** If y ≥ b, the descent nodes x_0, …, x_(L−1) are internal (they exceed y), each visits its
descent child first, and when x_(t+1) is visited only x_0, …, x_t are marked. So y is first visited with flag φ,
nothing below y is marked, and by the fresh-subtree lemma sub(y) is processed as by the search from y with visit order
R everywhere.

**Chain lemma.** Consider the search from z with visit order R and nothing below z marked, and the chain
z_0 = z, z_(j+1) = z_j − e (while z_j ≥ b). Each z_j visits z_(j+1) first, and then only z_0, …, z_j are marked;
after that visit returns, exactly sub(z_(j+1)) has been added (fresh-subtree lemma). The remaining children of z_j
then mark N_j = sub(z_j) ∖ ({z_j} ∪ sub(z_(j+1))). If z_j ≥ M0, every node of N_j is internal and lies in [z_j − A,
z_j): inductively, a newly marked u′ has a parent in N_j ∪ {z_j}, so u′ ≥ z_j − A − 4 ≥ b; then u′ ∉ sub(z_(j+1))
means z_j − u′ ∈ Ap, so u′ ≥ z_j − A. The tests made in phase j ("u ∈ sub(z_(j+1))?", i.e. z_(j+1) − u ∈ Sg, and
"marked earlier in this phase?") are relative to z_j, so phase j is the same computation in the coordinates s = z_j −
u for every j with z_j ≥ M0, and it gives flag(u) = flag(z_j) ⊕ τ(s) for a fixed function τ. Consequently, for
u ∈ sub(z) with u ≥ M0 and z − u = je + s (s ∈ Ap): z_j − u = s ∈ Sg and z_(j+1) − u ∉ Sg, so u is marked in phase j
(or u = z_j), and

    flag(u) = φ_z ⊕ j·f_e ⊕ τ(s),

which depends only on z − u and is periodic in z − u with period 2e.

**Self-similarity lemma.** For z′ = z + 2et (t ≥ 0), the search from z′ (rule R, same flag) runs down its chain to
z, through internal nodes, and reaches z with the flag φ_z ⊕ 2t·f_e = φ_z while only chain nodes above z are
marked. By the fresh-subtree lemma it gives the same flags on sub(z) as the search from z.

**Window lemma.** Let n ≥ N0. (i) M(n) ∖ sub(y) ⊆ [y − F, n]: an internal u ∈ M(n) has y − u ∈ gℤ, and
y − u > F implies y − u ∈ Sg, so u ∈ sub(y); a leaf of M(n) has an internal parent x ≤ b + 3 < y − F, which lies
in sub(y) by the same argument, using (b). (ii) After the visit of y returns, newly marked nodes lie in
M(n) ∖ sub(y), so they are internal and ≥ y − F ≥ b + 4, and their children are ≥ b. Every test made then is "a
descent node?" (a fixed offset from n) or "∈ sub(y)?" (relative to y = n − J) or "marked earlier in this phase?".
So this phase is the same computation relative to n for every n ≥ N0.

**Structure corollary.** Let n ≥ N0 with n ≡ c (mod 2e), and p⁽ⁿ⁾ the assignment of O(π, R) at n.
1. p⁽ⁿ⁾(n − j) = Top(j) for 0 ≤ j < K, with Top independent of n: the nodes of the window [y − F, n] are descent
   nodes, nodes of sub(y) above M0 (flags by the chain lemma with z = y, relative to y), or nodes of the phase of
   the window lemma (ii).
2. M(n) ∩ [0, n − K] and p⁽ⁿ⁾ on it are the same for all such n; call this sequence A_c. The nodes ≤ n − K =
   y − F − 1 of M(n) lie in sub(y) by the window lemma (i), so their flags come from the search from y; for n′ = n +
   2et the search from y′ = y + 2et reaches y as in the self-similarity lemma and gives the same flags on sub(y), and
   M(n′) ∩ [0, n − K] = M(n) ∩ [0, n − K] by the membership rule of the window lemma (i).
3. A_c(u + 2e) = A_c(u) for M0 ≤ u ≤ u + 2e ≤ n − K: if y − u = je + s, then j ≥ 2 (otherwise
   y − u ≤ e + F + e < 2e + F + 1 ≤ y − u), so y − (u + 2e) = (j − 2)e + s and the chain lemma gives the same flag.
   Membership in M(n) is u ≡ n (mod g) there, and g divides 2e.

**Certificate theorem (cycle certificates).** Fix a case (move list, δ, min or max), an order O(π, R) and a class c
mod 2e, with zero data. Run the compressed recurrence with the flags A_c and the true recurrence for both flags over
the levels u ≥ 0, giving μ(u) and V(u, q) (unreachable levels are skipped; reachable levels never read them). Let W(u)
be the reachable levels among u − b + 1, …, u, r(u) the smallest of them, and

    S(u) = ( (x − u, μ(x) − μ(r), V(x, 0) − V(r, 0), V(x, 1) − V(r, 0)) for x ∈ W(u) ),    Δ(u) = V(r, 0) − μ(r).

Call u a sample level if u ≡ c − K (mod 2e), and let e(m) = memo[m + K] − V(m + K, 0) be the actual error of the
order at n = m + K. Suppose that
1. S(m₁) = S(m₂) for sample levels N0 − K ≤ m₁ < m₂; put T = m₂ − m₁ and drift = Δ(m₂) − Δ(m₁);
2. e(m) ≠ 0 for every sample level m ∈ [N0 − K, m₁), except for a finite list X₁ of values n = m + K;
3. for every sample level m ∈ [m₁, m₂) and integer t ≥ 0, e(m) − t·drift ≠ 0, except for a finite list X₂ (the
   values n = m + K + tT with t = e(m)/drift ≥ 0 an integer);
4. every element of X₁ ∪ X₂ is ≤ b + 80.

Then for every n ≥ N0 with n ≡ c (mod 2e) and n ∉ X₁ ∪ X₂, the order O(π, R) at n returns a wrong result with
zero data.

*Proof.* Level u + 1 reads only the levels u + 1 − d_i, which lie in W(u) or are unreachable. The weights are
constant (i·(1 + δ·flag)), and min/max-plus recurrences commute with adding a constant to all inputs. So the
normalised values at level u + 1, and the increment Δ(u + 1) − Δ(u), are functions of S(u), of the flag A_c(u + 1)
and of the reachability of u + 1; for u ≥ M0 these depend only on (u + 1) mod 2e (item 3 of the structure corollary).
Since m₁ ≡ m₂ (mod 2e) and m₁ ≥ M0, induction gives S(m + T) = S(m) and Δ(m + T) = Δ(m) + drift for all m ≥ m₁. For
n ≥ N0 in the class and m = n − K, the structure corollary gives memo⁽ⁿ⁾[u] = μ(u) for u ≤ m and the flags Top above
m, so by the same commutation memo⁽ⁿ⁾[n] − V(n, 0) = ẽ(S(m)) − Δ(m), where ẽ is the window computation from the
normalised values. So e(m + tT) = e(m) − t·drift for m ≥ m₁. Every sample level ≥ N0 − K lies in [N0 − K, m₁) or is
m′ + tT with m′ ∈ [m₁, m₂) a sample level and t ≥ 0; hypotheses 2 and 3 give a nonzero error outside
X₁ ∪ X₂. ∎

*Proof of Theorem 6.* A spec satisfying the criterion has PF at every n, so let it fail the criterion; there are
416 such ordered move lists, so 1 664 cases with δ ∈ {1, 2} and min or max. For each case the certificate file
lists cycle certificates (π, R, c) whose classes cover all 24 residues of n mod 24 (2e divides 24). For each,
verify.py computes A_c and Top from the assignment of O(π, R) at a representative n_rep ≥ max(N0, 150) of the class
(extending A_c by item 3 of the structure corollary), checks items 1–3 of the structure corollary between n_rep
and n_rep + 2e, recomputes the cycle,
the drift and all window errors, and checks hypotheses 1–4 and N0 ≤ b + 81. So for n ≥ b + 81 the certified order is
wrong with zero data, for every coefficient vector. For b ≤ n ≤ b + 80 with PF failing, the file gives either a
model-D order that is wrong with zero data, or, for each of the 9^k coefficient vectors, a data vector and a
per-node visit-order table that is wrong; verify.py evaluates every one of them and checks that every instance is
covered. ∎

### Theorem 7 (model D, sum mode)

**Pair lemma (a pair of orders suffices).** Let p⁰ and p¹ be the assignments of two model-D orders, Δ the set where
they differ, and c ∈ Δ *isolated*: if c is internal, no other internal node of Δ is ≡ c (mod 17); if c is a leaf,
no other leaf is in Δ. If N9(c) < P, then for every coefficient vector and δ ∈ {1, 2} one of the two orders is
wrong for some data vector in {0, 1}^17.
*Proof.* By the error lemma, E(p⁰) − E(p¹) = δ Σ_{m ∈ Δ} D̃_m (p⁰_m − p¹_m) N(m). Leaves contribute only to the
constant term. So the coefficient of data[c mod 17] (c internal), or the constant term (c a leaf), is ±δN(c), with
1 ≤ N(c) ≤ N9(c) < P (c is reachable). It is nonzero mod P, and the end of the proof of Theorem 5 applies. ∎

**Translation lemma.** Let O(π⁰, R) and O(π¹, R) have descents of equal total J and equal flag parity, and let
n ≥ n_T = J + F + 4 + b. Both orders reach y = n − J with the same flag and process sub(y) identically (descent and
fresh-subtree lemmas), so Δ ⊆ M(n) ∖ sub(y) ⊆ [y − F, n] (window lemma (i)). On that window both assignments come
from the descents and from the phase of the window lemma (ii), which are relative to n, and for an internal node c,
N(c) counts move sequences of total n − c through internal nodes, so it depends only on n − c. Hence Δ, the isolation
of a node and N9 at the same depth are the same for every n ≥ n_T.

**Relabelling.** In sum mode, permuting the moves together with their coefficients does not change the recurrence
(it is a sum over the moves). Mapping a visit order of move indices along the permutation gives a visit order that
visits the same (offset, flip) pairs in the same sequence, hence induces the same assignment. PF and the criterion
do not depend on the order of the moves. So certificates for one ordering of a move multiset serve all its
orderings, for every coefficient vector.

*Proof of Theorem 7.* For each of the 96 move multisets that fail the criterion, the certificate file gives a pair
O(π⁰, R), O(π¹, R) with equal descent total and parity; verify.py checks that at n_T ≤ b + 81 it has an isolated
node with N9 < P (largest value 105 705), which by the translation lemma covers every n ≥ n_T. For b ≤ n ≤ b + 80
with PF failing (7 614 instances) the file gives a pair of orders with an isolated node (largest N9: 897 480 < P).
The pair lemma and relabelling finish the proof. ∎

## Scope

- The theorems are about the family F as defined: k ∈ {2, 3}, offsets 1–4, the stated weight function, data in
  {0, …, 9}^17 and the modulus P. Other families need their own proofs.
- Theorem 1 holds for every data vector and every supported assignment; Theorems 5–7 produce one bad pair of order
  and data, and say nothing about how many there are.
- "Evaluation order" means the three models above. Model G is the order of the explicit-stack procedure with a
  fixed push order; models D and S are the generalisations defined above.

## Literature search

The class `own` records that no source stating Theorem 1 in this form, Propositions 2–3 or Theorems 4–7 was found.
What was checked: Crossref, OpenAlex and arXiv queries with generic keywords on memoization keys and their
compression, state merging, exact state aggregation in dynamic programming and the soundness of memoization (six
queries). Nothing found addresses dropping a flag from the key, the role of the evaluation order, or a converse.
The principle behind Theorem 1, that a memo key must determine the value, is the soundness principle of selective
memoization (Acar, Blelloch and Harper; abstract only), and it is related to exact state aggregation (Givan, Dean
and Greig 2003; title only). These two works are credited for the principle, not used as evidence.

## Verification

```bash
python theorems/compressed-memo-keys-evaluation-orders/verify.py               # all checks, under half a minute
python theorems/compressed-memo-keys-evaluation-orders/verify.py --regenerate  # also re-runs the certificate search
```

The script uses the Python standard library only, is deterministic and needs no network. It exits with code 0
only if every check passes. It checks:
- that **P = 1 000 003 is prime**, by trial division by every d ≤ 1 000;
- **Theorem 1** on 3 000 seeded random instances of F with 4 random supported assignments each (every assignment on
  an instance with VF is exact), and δ = 0 ⇒ V(m, 0) = V(m, 1) for every m ∈ M(n), on all 576 ordered move lists
  for b ≤ n ≤ b + 10, in all three modes, with 3 seeded (coefficient, data) pairs each;
- the **stack lemma** on 2 000 seeded random instances with random visit orders (the explicit-stack procedure and the
  per-node search give the same flags; the assignment is supported), and the **error lemma** on the same instances,
  for the induced assignment and for a random one;
- **Proposition 2** on all 156 move multisets for b ≤ n ≤ b + 60, with the vector z and D ≤ 12;
- **Proposition 3** for all 100 relevant data values, and **Theorem 4** by exact affine evaluation of all global
  orders and all model-D assignments; the remark on model S with all 6^5 visit-order tables;
- **Theorem 5:** the finite fact (105 705 < P), the closure at n = b + 12 (and its consistency up to b + 60), the
  domination lemma for b + 17 ≤ n ≤ b + 30, and the construction of the proof on all 2 238 instances with
  n ≤ b + 24;
- **Theorems 6 and 7:** it reads [certificates.txt.gz](certificates.txt.gz) (SHA-256 of the content recorded in
  the script) and checks every certificate and the coverage of every case, class and instance listed in the
  proofs: 9 800 cycle certificates for 1 664 cases; 132 576 small-n instances (131 497 with a zero-data order and
  1 079 with one certificate for each of their 728 919 coefficient vectors); 96 large-n and 7 614 small-n
  sum-mode pairs. As further consistency checks, it compares each cycle certificate's prediction with a direct
  evaluation at one n ≥ b + 81, the translation lemma over 40 further values of n, the relabelling, and a sample of
  end-to-end evaluations mod P.

With `--regenerate`, the deterministic search that produced the certificate file runs again (about 1.5 minutes)
and must reproduce it exactly.

**Certificate file format** (gzip-compressed text, tab-separated; move lists as in "30,30,41" for
(3,0),(3,0),(4,1); a descent or rule is a string of move indices, "-" for the empty descent; the comment lines at
the top of the file call a descent "path"):
- `C list δ comb descent rule class`: a cycle certificate; class is the residue of n mod 2e, e = d_(rule[0]).
- `Z list δ comb tokens`: 81 tokens for n = b, …, b + 80: `.` (PF holds), `descent:rule` (an order wrong with zero
  data), or `*` (see the next three line types).
- `T list δ comb n id table`: a visit-order table; digit m is the index of node m's visit order in the
  lexicographic list of permutations of the move indices.
- `R list δ comb n tokens`: one 2-character token per coefficient vector, in lexicographic order of
  (c_0, …, c_(k−1)) ∈ {1, …, 9}^k: a digit v (constant data v) or `x` (the data vector of the X line), followed by
  the id of a table whose order is wrong.
- `X list δ comb n coefficients data id`: an explicit data vector for one coefficient vector.
- `S multiset descent0 descent1 rule` and `s multiset n descent0:rule0 descent1:rule1`: the sum-mode pairs for
  large and for small n.

## Sources

- U. A. Acar, G. E. Blelloch, R. Harper. *Selective memoization*. arXiv:1106.0447. Abstract only; credited for
  the general soundness principle behind Theorem 1.
- R. Givan, T. Dean, M. Greig (2003). *Equivalence notions and model minimization in Markov decision processes*.
  Artificial Intelligence. [doi:10.1016/S0004-3702(02)00376-4](https://doi.org/10.1016/S0004-3702(02)00376-4).
  Title only; listed as part of the literature search.
