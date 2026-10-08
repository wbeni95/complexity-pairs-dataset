# First-match prices need not be pairwise once three rules can match an item

> **Provenance: 🟡⏳ Undetermined (may be our own result).** This note proves Proposition 1, Theorem 2, the
> least-squares value and Remarks 1–2 in full. The sources read on ordering a first-match rule list (decision lists,
> lexicographic cue orders), credited in the pair entry — Yee, Dahan, Hauser and Orlin (2007); Schmitt and Martignon
> (2006); Chakravarthy et al. (2008) — contain special cases of the problem (0/1 and 0/w costs) and its subset
> dynamic program, but none of them states these results. One source that might contain them could not be read:
> Martignon and Hoffrage (2002), *Fast, frugal, and fit: Simple heuristics for paired comparison* (Theory and
> Decision 52, 29–71), for which no open-access copy was found. Whether it contains the result could not be
> checked, so this may be our own result. If you can tell us whether this source contains the result, please open
> an issue. What was read, and how it relates to this note, is in [Literature](#literature).

This note belongs to the pair
[first-match-rule-ordering-enumeration-vs-subset-dp](../../pairs/first-match-rule-ordering-enumeration-vs-subset-dp/).
It explains why the problem there is more general than the linear ordering problem as a price function: once an
item can be matched by three rules, the price of an order need not be a sum of pairwise terms (Theorem 2), although
it can be (Remark 1).

## Setting

There are k rules and m items. Rule r matches item i or not; M_i is the set of rules that match i. If r is the
first rule of the order π that matches i, item i pays cost[i][r]. An item that no rule matches pays a fixed
default. The price of π is the sum over the items. This is the price function of the pair entry, which minimises it
over the orders. The pair entry uses non-negative integer costs and defaults; here they may be any real numbers, and
the instance of Theorem 2 has non-negative integer costs, so it is an instance of the pair entry.

The price has the **pairwise form** if there are a constant C and weights w_xy (x ≠ y) such that

    price(π) = C + Σ_{x≠y} w_xy · [x before y in π]      for every order π of the k rules.          (W)

Since [y before x] = 1 − [x before y], the right sides of (W) are exactly the functions
C′ + Σ_{x<y} w′_xy [x before y]. With the signs s_xy = 2[x before y] − 1 = ±1 they are the functions
C″ + Σ_{x<y} α_xy s_xy.

**The 6 orders of three rules.** For the rules a, b, c, the map π ↦ (s_ab, s_ac, s_bc) is injective, and its image
consists of the 6 sign vectors other than (+, −, +) and (−, +, −). The two excluded vectors are the cyclic ones:
a before b and b before c force a before c, and b before a and c before b force c before a. Every other vector is
realised: abc (+,+,+), acb (+,+,−), bac (−,+,+), bca (−,−,+), cab (+,−,−), cba (−,−,−).

## Statement

**Proposition 1 (at most two matching rules).** If every item is matched by at most two rules, the price has the
pairwise form (W).

*Proof.* An item with M_i = ∅ pays its default, and an item with M_i = {u} pays cost[i][u], whatever the order.
An item with M_i = {u, v} pays cost[i][u]·[u before v] + cost[i][v]·[v before u] =
cost[i][v] + (cost[i][u] − cost[i][v])·[u before v]. The sum of these terms has the form (W). ∎

This is why the instances of the pair entry whose items match at most two rules are linear ordering instances. The
pair entry proves the same decomposition, and the converse reduction, in its PROOFS.md, section 8.

**Theorem 2.** Let k = 3 with rules a, b, c, and let one item be matched by all three, with costs
cost[a] = 1, cost[b] = 0, cost[c] = 0 (and no other items). Then price(π) = [a is first in π], and this price does
not have the pairwise form (W).

*Proof.* Suppose price(π) = C″ + α s_ab + β s_ac + γ s_bc for every order π.
- abc (+,+,+) and acb (+,+,−) differ only in s_bc. Both have price 1, so 2γ = 0.
- bac (−,+,+) and bca (−,−,+) differ only in s_ac. Both have price 0, so 2β = 0.
- cab (+,−,−) and cba (−,−,−) differ only in s_ab. Both have price 0, so 2α = 0.

Then the price is the constant C″. But it is 1 on abc and 0 on bac, a contradiction. ∎

**Least squares.** Over the 6 orders, the smallest value of Σ_π (price(π) − f(π))² over all functions f of the form
(W) is exactly **1/3**. It is attained by f = 1/3 + (s_ab + s_ac)/4 = −1/6 + ([a before b] + [a before c])/2,
whose values on abc, acb, bac, bca, cab, cba are 5/6, 5/6, 1/3, −1/6, 1/3, −1/6. *Proof:* the sum of squares is
a convex quadratic function of the coefficients, so it is minimal exactly where its gradient vanishes, that is, at
the solutions of the normal equations. In the basis 1, s_ab, s_ac, s_bc they are

    [ 6  0  0  0 ] [C″]   [2]
    [ 0  6  2 −2 ] [α ] = [2]
    [ 0  2  6  2 ] [β ]   [2]
    [ 0 −2  2  6 ] [γ ]   [0]

with the solution (C″, α, β, γ) = (1/3, 1/4, 1/4, 0). The residuals are 1/6, 1/6, −1/3, 1/6, −1/3, 1/6, and their
squares sum to 1/3. ∎ So no function of the form (W) comes closer to the price than this.

## Remarks

1. **Which costs on one item are pairwise.** For one item matched by a, b, c with costs x, y, z, the price
   x·[a first] + y·[b first] + z·[c first] has the pairwise form iff x = y = z. *Proof:* the three pairs of orders
   used in the proof of Theorem 2 have equal prices (x and x, y and y, z and z), so the same argument gives
   α = β = γ = 0, and the price is constant, so x = y = z. Conversely, a constant has the form (W). ∎
2. **Any k ≥ 3.** Add k − 3 rules that match no item to the instance of Theorem 2. If its price had the form (W)
   over all orders of the k rules, then restricting to the orders that place the new rules last, in a fixed order,
   would make every indicator that involves a new rule constant. That would give the form (W) on the orders of
   a, b, c, which Theorem 2 rules out. So for every k ≥ 3 there is an instance whose price is not pairwise.

## Scope

- The note is about representing the price function over all k! orders. It says nothing about the complexity of
  minimising the price, which the pair entry covers (a subset dynamic program, and NP-hardness through a reduction
  from FEEDBACK ARC SET, whose NP-completeness is background there).
- Theorem 2 needs only one item matched by three rules. The note does not characterise which instances with
  several such items happen to be pairwise; Remark 1 covers one item only.

## Literature

No source read states Theorem 2, the least-squares value or Remarks 1–2. The works named here are credited as the
literature on the problem and listed to document the search; none of them is used as evidence. What was read:
- **Decision-list and lexicographic ordering**, the literature on the problem of the pair entry: Chakravarthy et
  al. (2008, MaxDL), full text; Yee, Dahan, Hauser and Orlin (2007), §4, Algorithm 2 and the appendix proofs of
  Propositions 1–4; Yee's PhD thesis (2006): contents, Chapter 3 (hardness, by a reduction from set cover), §4.2 (its
  Lemma 2 is the property that only the set of preceding rules matters, which justifies the subset dynamic program)
  and a keyword scan; Schmitt and Martignon (2006), §1.4, §2.1–2.3 and §3. Schmitt and Martignon (§2.3,
  Proposition 1) compare cue orders with a pairwise preference over *objects* (the ranking problem of Cohen,
  Schapire and Singer), which is a different statement: it concerns which orders of objects a cue order can induce,
  not whether the cost over cue orders is a sum of pairwise terms. None of these says whether the price is a sum of
  pairwise terms.
- **The linear ordering problem** (Grötschel, Jünger and Reinelt 1984, abstract), which is the pairwise case
  (Proposition 1).
- **Packet-filter rule ordering** (abstracts of Hamed and Al-Shaer 2006, Fuchino et al. 2023 and others) and
  **min-sum ordering problems** (Happach, Hellerstein and Lidbetter, arXiv:2004.05954, abstract and §1). Both price
  an item by the position of its first match, not by the identity of the capturing rule.

The searches used generic keywords and published titles only. Not read: Martignon and Hoffrage (2002), the closest
work in this line (simple lexicographic heuristics for paired comparison), for which no open-access copy was found;
this is why the provenance is undetermined. The full texts of most packet-filter papers were not read either (their
abstracts price by position).

## Verification

```bash
python theorems/first-match-prices-not-pairwise/verify.py
```

The script uses exact rational arithmetic, the Python standard library only and fixed seeds, needs no network,
and runs in well under a second. It checks:
- the 6-order parametrisation;
- Theorem 2: the price vector, and that the linear system "price = (W)" over the 6 orders has no rational
  solution (rank test), together with the three order pairs used in the proof;
- the least-squares minimum 1/3, the coefficients and the fitted values;
- Remark 1 for all 64 cost triples in {0, …, 3}³;
- Remark 2 for k = 4 and 5 (rank test over all k! orders);
- Proposition 1: the weights of its proof reproduce the price on every order, for 300 seeded random instances with
  k = 2, …, 5 (11 896 pairs of instance and order).

It exits with code 0 only if every check passes.

## Sources

- M. Yee, E. Dahan, J. R. Hauser, J. Orlin (2007). *Greedoid-based noncompensatory inference*. Marketing Science
  26(4), 532–549. [doi:10.1287/mksc.1060.0213](https://doi.org/10.1287/mksc.1060.0213)
- M. Schmitt, L. Martignon (2006). *On the complexity of learning lexicographic strategies*. Journal of Machine
  Learning Research 7, 55–83. <https://www.jmlr.org/papers/v7/schmitt06a.html>
- V. Chakravarthy, S. Joshi, G. Ramakrishnan, S. Godbole, S. Balakrishnan (2008). *Learning decision lists with
  known rules for text mining*. IJCNLP 2008, Volume II. <https://aclanthology.org/I08-2118/>
- M. Yee (2006). *Inferring noncompensatory choice heuristics*. PhD thesis, Massachusetts Institute of Technology.
  <https://hdl.handle.net/1721.1/36226>. Read as stated above.
- L. Martignon, U. Hoffrage (2002). *Fast, frugal, and fit: Simple heuristics for paired comparison*. Theory and
  Decision 52, 29–71. [doi:10.1023/A:1015516217425](https://doi.org/10.1023/A:1015516217425). Not read (no open-access
  copy found); the source named in the provenance banner.
- M. Grötschel, M. Jünger, G. Reinelt (1984). *A cutting plane algorithm for the linear ordering problem*.
  Operations Research 32(6), 1195–1220. [doi:10.1287/opre.32.6.1195](https://doi.org/10.1287/opre.32.6.1195).
  Abstract only.
- F. Happach, L. Hellerstein, T. Lidbetter. *A general framework for approximating min sum ordering problems*.
  arXiv:2004.05954. Abstract and §1 only.
