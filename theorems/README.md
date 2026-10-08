# Theorems

This folder holds mathematical results that are **not complexity pairs**: exact statements about algorithms and
objects related to the dataset, each with a complete proof. They are kept apart from `pairs/` and `staging/` because
they make no claim of the form "two algorithms with different asymptotic cost", and the validator does not process
them.

## What every note contains

Each note is a folder `theorems/<id>/` with three files, and, where the proof is checked against third-party
input files, a `data/` folder holding unmodified copies of them under their own licences (see `data/README.md`
in that note):

| File | Content |
|---|---|
| `README.md` | the precise statement with all definitions, a complete proof, the sources, the provenance label (below) and the exact scope: what the note does **not** claim |
| `meta.json` | machine-readable summary: `id`, `title`, `statement`, `provenance`, `sources`, `verify`; it must validate against [meta.schema.json](meta.schema.json) |
| `verify.py` | a deterministic script (fixed inputs and seeds, Python standard library only) that re-checks every computed fact the proof uses and exits with code 0 only if all checks pass |

A note whose proof is computer-assisted also ships the certificate files its `verify.py` checks (for example
`certificates.txt.gz`). A note may read the `data/` folder of another note by relative path instead of copying the
files.

The proof is the written argument in the README. `verify.py` is evidence: it checks the concrete numbers a proof
relies on (for example a certificate value) and runs exhaustive or seeded tests of the statement and its lemmas on a
stated finite scope. A computation alone never counts as a proof here.

## Provenance labels

Every note says where the result stands relative to the literature, in `meta.json` (`provenance`) and at the top
of its README.

| `class` | Meaning |
|---|---|
| `literature` | The result is in the literature, and the note re-proves it. The source is credited exactly (section, proposition), and the note says what it adds, if anything (an independent proof, independent verification code, explicit certificates). |
| `own-extension` | Our generalization of a cited base result. The note names the base and states exactly what goes beyond it. |
| `own` | No literature was found after a documented search. The note lists what was checked. This is a statement about that search, not a claim of priority. |
| `undetermined` | Probably our own result, but a source that might already contain it could not be read. Shown as **🟡⏳ Undetermined (may be our own result)**. Needs `pending: true`, a `pending_note`, and `missing_sources`, which lists each unread source exactly: `authors`, `year`, `title`, `venue`, a `doi` or `url`, `status` (why it could not be read) and `needed_for` (what reading it would decide). |

`bases` lists the cited results a label rests on. The flag **`pending: true`** marks a note where a source that could
not be read (or identified) might already cover the result; `pending_note` says which. A pending note never carries
an own label. If the result itself is in the literature and only a detail could not be verified, the note is
`literature` with the flag (⏳). If the result may be our own but a source that might contain it could not be
read, the note is `undetermined` (🟡⏳) and lists those sources exactly in `missing_sources`; its README says what
it proves beyond the sources that were read, and that whether the missing sources contain the result could not be
checked. The repository README lists every missing source under "Sources we could not read".

## The green check mark

A note whose every claim has its proof in the files listed in `proof.documents` (its own README and, where it
uses them, other notes' READMEs or an entry's PROOFS.md), re-checked by the scripts and tests in `proof.checks`,
carries the `proof` field in `meta.json` and shows **✅ Proved** in the tables. The criteria are the same as for entries
([CONTRIBUTING.md](../CONTRIBUTING.md#the-green-check-mark-proved)): our own written proof of every claim,
deterministic checks, and a logged audit. A citation in a note is credit, not part of the proof.

## Notes

| Note | Provenance | Statement (short) |
|---|---|---|
| [no-integral-form-z-half-schemes](no-integral-form-z-half-schemes/) | literature, **pending** | The ⟨2,4,5;32⟩ scheme of AlphaEvolve and the ⟨3,3,6;40⟩ scheme attributed to Smirnov, in the pinned files, both with coefficients in ℤ[1/2], have no equivalent form with integer coefficients. |
| [knuth-window-concave-length-weights](knuth-window-concave-length-weights/) | undetermined 🟡⏳ | Knuth's restricted root window is exact for the interval recurrence with concave nondecreasing length weights, under the largest and the smallest tie rule, with an explicit trajectory of chosen roots. |
| [endpoint-law-split-dependent-weights](endpoint-law-split-dependent-weights/) | own | For interval recurrences whose node weight depends on the split, a weak rotation condition makes one of the two end splits optimal on every interval, so a two-candidate DP is exact and some optimal tree is a path; for weights that depend on the interval only, the resulting condition RS is strictly weaker than monotonicity under inclusion. |
| [power-plus-offset-four-candidates](power-plus-offset-four-candidates/) | own | For k = X^d + C with d ≥ 3, the cheapest representation is attained at one of the roots 0, 1, ⌊k^(1/d)⌋, ⌊k^(1/d)⌋ + 1; the three candidates that suffice for squares fail only at powers of two, and they do fail for every d ≥ 3 (k = 2^(d+1)); for 3 ≤ d ≤ n, the number of k below 2ⁿ with a representation of at most n − 4 bits is computed with O((n²/d²)·log d) word operations. |
| [lz77-repeat-slots-exact-pruning](lz77-repeat-slots-exact-pruning/) | undetermined 🟡⏳ | For optimal LZ77-style parsing with k repeat-offset slots, static costs and minimum repeat length at least 2, deleting every state whose value exceeds that of one cheapest state by at least an explicit slot-dependent margin keeps the optimum; the margin is attained, and the hypotheses are needed. |
| [lz77-repeat-slots-state-bounds](lz77-repeat-slots-state-bounds/) | undetermined 🟡⏳ | The exact DP for this parsing problem holds at most 3 + Σ_{j≤n−2} j^k states and makes n^(k+2)/(k+2) + O(n^(k+1)) relaxations in the worst case; exact pruning keeps 2n − 2 states on aⁿ (n ≥ 3) but Θ(n^(k+1)) in the worst case over unbounded alphabets. |
| [max-flow-random-dense-trivial-min-cut](max-flow-random-dense-trivial-min-cut/) | undetermined 🟡⏳ | On the max-flow entry's random dense networks, an explicit cut condition forces a trivial minimum s–t cut, so both implementations return min(c_out(s), c_in(t)); the condition fails with probability < 1 for n ≥ 22, < 5.48·10⁻⁵ and ≤ 1/n for n ≥ 40; the winning trivial cut is asymptotically a fair coin. |
| [max-flow-random-dense-dinic-short-residual-paths](max-flow-random-dense-dinic-short-residual-paths/) | own extension (base: Motwani 1994) | On the same networks, for every n ≥ 21 793, with probability ≥ 1 − 2/n, every feasible flow has residual s–t distance ≤ 6 or none, so Dinic makes ≤ 7 breadth-first searches; with probability ≥ 1 − 3/n it makes between n(n − 1)/2 and 26n(n − 1) + 600(n − 1) reads. |
| [max-flow-random-dense-edmonds-karp-cubic-reads](max-flow-random-dense-edmonds-karp-cubic-reads/) | own | On the same networks, for every n ≥ 1000, with probability ≥ 1 − 3/n, Edmonds–Karp makes between 0.0049·n³ and 200·n³ reads. |
| [hungarian-exact-iteration-count](hungarian-exact-iteration-count/) | own extension (base: the O(n)-per-row bound) | The assignment entry's Hungarian code runs at most i iterations for row i on every input and exactly i on every integer or exact-rational matrix with non-decreasing rows, an exact worst-case family; exact counts for rectangular matrices. |
| [per-term-2-integrality-z-half-schemes](per-term-2-integrality-z-half-schemes/) | own extension (base: Moran–Schwartz–Yuan 2026) | For every subring of a field of characteristic 0 that maps to a field of characteristic 2 (ℤ included): no term of the pinned ⟨3,3,6;40⟩ ℤ[1/2] scheme can be made integral by an equivalent transformation, and at least 20 of the 32 terms of the pinned ⟨2,4,5;32⟩ scheme cannot; 20 is attained. |
| [binary-powering-exactness-in-magmas](binary-powering-exactness-in-magmas/) | own | Left-to-right binary powering of x in a magma is exact iff p_a·p_a = p_2a for all a; right-to-left iff p_a·p_(2^k) = p_(a+2^k) for all k ≥ 0 and 1 ≤ a ≤ 2^k (the mirrored variant: the mirrored condition); with eventually periodic powers each condition reduces to a finite check, with a tight bound for left-to-right; the conditions are pairwise independent. |
| [compressed-memo-keys-evaluation-orders](compressed-memo-keys-evaluation-orders/) | own | For an explicit family of memoized recurrences, dropping a flag from the memo key is exact for every input and every evaluation order (per-node orders, or all supported assignments) iff δ = 0 or the flag is a function of the node; with one global order the converse fails. Computer-assisted, with public certificates. |
| [first-match-prices-not-pairwise](first-match-prices-not-pairwise/) | undetermined 🟡⏳ | First-match prices are sums of pairwise terms when every item matches at most two rules; one item matched by three rules suffices to break this (least-squares distance 1/3). May be our own result; Martignon–Hoffrage (2002) could not be read. |
| [para-cayley-dickson-closed-form-powers](para-cayley-dickson-closed-form-powers/) | literature | In the real Cayley–Dickson algebras of every dimension 2^m, the left powers of the para-product x ∗ y = x̄ ȳ have the closed form p_(2j+1) = n(x)^j x and p_(2j+2) = n(x)^j x̄². Additions of the note: remarks on binary powering with this product (right at e = 2^j − 1 and 2^j − 2, first wrong at e = 4 exactly when x⁴ ≠ n(x) x̄²) and an explicit witness that (x ∗ y) ∗ x = n(x) y fails in every dimension ≥ 16. |

## Running the checks

From the repository root:

```bash
python theorems/no-integral-form-z-half-schemes/verify.py           # offline: the three pinned files in data/ (or: --download)
python theorems/knuth-window-concave-length-weights/verify.py       # offline, well under a minute
python theorems/endpoint-law-split-dependent-weights/verify.py  # offline
python theorems/power-plus-offset-four-candidates/verify.py  # offline
python theorems/lz77-repeat-slots-exact-pruning/verify.py  # offline
python theorems/lz77-repeat-slots-state-bounds/verify.py  # offline
python theorems/max-flow-random-dense-trivial-min-cut/verify.py  # offline (--full: the extended run)
python theorems/max-flow-random-dense-dinic-short-residual-paths/verify.py  # offline (--full: the extended run)
python theorems/max-flow-random-dense-edmonds-karp-cubic-reads/verify.py  # offline (--full: the extended run)
python theorems/hungarian-exact-iteration-count/verify.py  # offline (--full: the extended run)
python theorems/per-term-2-integrality-z-half-schemes/verify.py  # offline: reads the pinned files of no-integral-form-z-half-schemes/data/
python theorems/binary-powering-exactness-in-magmas/verify.py  # offline
python theorems/compressed-memo-keys-evaluation-orders/verify.py  # offline: checks certificates.txt.gz (--regenerate rebuilds and compares)
python theorems/first-match-prices-not-pairwise/verify.py  # offline
python theorems/para-cayley-dickson-closed-form-powers/verify.py  # offline
```

Each script prints one line per check and ends with `ALL CHECKS PASSED` (exit code 0) or a list of the failed
checks (exit code 1).

## License

As for the rest of the repository: the scripts (`verify.py`) are under the [Apache License 2.0](../LICENSE), and
the texts, metadata and certificate files (`README.md`, `meta.json`, `meta.schema.json`, `certificates.txt.gz`)
are under [CC BY 4.0](../LICENSE-DATA).
Corrections and independent re-verification are welcome. Please open an issue.
