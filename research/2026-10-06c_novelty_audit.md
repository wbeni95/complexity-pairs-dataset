# Novelty audit of RL-054's rank-47 scheme for 4×4×4 matrix multiplication over GF(2)

Date: 2026-10-06 (local), work session 11:30–12:45. Follows RL-054, RL-059 and RL-061 (idea 2).
Author: delegated research agent (Claude), for the maintainer.

Every claim below comes from a script run in this session (`experiments/2026-10-06c_collect.py`,
`experiments/2026-10-06c_equivalence.py`, unit tests `tests/test_search_equivalence.py`) or from a source whose
text was read here (quoted where used). DOIs were checked with `tools/check_sources.lookup_doi`.

## Summary

* **RL-054's scheme is not new.** `search/schemes/rust-2026-10-07/4x4x4_rank47_seed8.json` is **equivalent** under
  the symmetry group G (section 2) to a scheme that Kauers and Moosbauer have published since October 2022:
  `http://www.algebra.uni-linz.ac.at/people/mkauers/matrix-mult/solutions/444/47/b0/jb050da4aa249f5a.exp`
  (directory listing date 2022-10-27 17:52; SHA-256 `aad16937…6b40067`).
  * Certificate: σ = cyclic shift (a, b, c) ↦ (b, c, a), then the sandwich (P, Q, R) with rows
    P = 1100/0101/1000/0011, Q = 1110/0101/0111/1111, R = 1001/1101/1110/1000 (row r lists entries (r,0..3)).
    It maps our 47 terms exactly onto the 47 published terms.
  * The certificate was re-checked with separately written arithmetic (matrices as lists, inverses by
    exhaustive search over all 2¹⁶ matrices). The same group element maps the standard algorithm to a valid
    scheme, which proves that this element fixes the tensor.
  * The two schemes share **no** term, so the identity cannot be seen without the equivalence test.
  * No other published scheme is in this class; the exact test was needed for this one file only.
* **Status change for RL-054 / RL-059:** "rediscovery of the best known rank" becomes **rediscovery of a published
  scheme, up to equivalence**. RL-059's statement stays true, but it is superseded: the scheme is inequivalent
  to AlphaTensor's and to the flips repository's file, but it is equivalent to another published Kauers–Moosbauer
  scheme.
* **Collected: 99,129 publicly available 4×4×4 rank-47 GF(2) scheme files** from six places (section 1):
  * all pass `verify` and `verify_explicit` in the project's convention;
  * they are only **25 distinct term sets** (most files in Kauers' directory repeat a scheme with its products
    in a different order);
  * they fall into exactly **4 equivalence classes** under G, decided exactly: invariants between the classes,
    checked certificates inside them.

  | Class | Members |
  |---|---|
  | A | AlphaTensor |
  | B | Kauers–Moosbauer: the flips file and the scheme of arXiv:2210.04045 (equivalent to each other) |
  | C | Zaru's FastMatrixF2 scheme |
  | D | one file of Kauers' directory, the RL-054 class |
* **The other saved rank-47 schemes.** Five files appeared in `search/schemes/rust-2026-10-06c/` at 12:29–12:30
  during this session, from another agent's current runs: seeds 610, 617, 618, 622 and `before_seed707`.
  * They are pairwise **equivalent** (one class, checked certificates).
  * The factor-rank profile (I1) **proves** them inequivalent to RL-054 and to all 25 published term sets, i.e.
    to all four published classes.
  * For that class the strongest allowed statement holds: *inequivalent to all 99,129 published rank-47 schemes
    we could obtain (classes A–D)*. That is not "new" in an absolute sense (section 5).
* **The network-free code is tested:** 16 unit tests cover the group action, the invariance of every invariant
  under random group elements, separation of known inequivalent schemes, and the exact test (it finds
  certificates for equivalent schemes and none for inequivalent ones).

## 1. Collected schemes and their provenance

Collector: `experiments/2026-10-06c_collect.py`. The numbers in this section come from its console output (`search/runs/2026-10-06c_collect.console.txt`). Downloads are
cached outside the repository (`$NOVELTY_CACHE`, default `<temp>/cpd-2026-10-06c`). No third-party file was added to
the repository; rerunning the collector re-downloads everything. The git sources are pinned to the commit current
on 2026-10-06.

| Id | Source | Where (re-download) | License stated | 4×4×4 rank-47 files | Third factor as published | verify / verify_explicit |
|---|---|---|---|---|---|---|
| AT | AlphaTensor, Fawzi et al. 2022 (doi:10.1038/s41586-022-05172-4) | github.com/google-deepmind/alphatensor @ `1949163d`, `algorithms/factorizations_f2.npz`, key `4,4,4` (SHA-256 `70f09f34…`) | CC BY 4.0 for data (README) | 1 | (k,i), as stored | pass / pass |
| KMg | Kauers & Moosbauer, Flip Graphs for Matrix Multiplication, ISSAC 2023 (doi:10.1145/3597066.3597120) | github.com/jakobmoosbauer/flips @ `e31a0a0f`, `solutions/444-47-mod2.exp` (SHA-256 `3f7d141d…`) | none for data (program GPL-3) | 1 | (k,i) | pass / pass |
| KMn | Kauers & Moosbauer, arXiv:2210.04045 ("another non-equivalent solution for 4×4") | `…/people/mkauers/matrix-mult/s47.exp` (SHA-256 `8b58b975…`; URL printed in the note) | none | 1 | (k,i) | pass / pass |
| KW | Kauers' web directory (no paper cites it as far as we saw) | `http://www.algebra.uni-linz.ac.at/people/mkauers/matrix-mult/solutions/444/47/*/` (19 files) and `…/444/x47/*/` (99,101 files); file and folder dates in the listings 2022-10-06 to 2022-11-04; manifest SHA-256 `92b418c0…a7db63` (URL and file hash of every file) | none | 99,120 | (k,i) | all 99,120 pass / pass |
| FM | N. F. Zaru, FastMatrixF2 (doi:10.5281/zenodo.22823115) | github.com/big-brain-zaru/FastMatrixF2 @ `5fd32f68`, `results/{alphatensor_444,gamma_scratch,group_sat_inc,n1_probe}_rank47.json`, `results/records/gamma47_B_rank47.json` | MIT | 5 | (k,i) (its README states a (i,j), b (j,k), c (k,i)) | pass / pass |
| MMC | Matrix Multiplication Catalog | `https://solven.eu/matmulcatalog/catalog.json` (SHA-256 `475c05d2…`), entry `known/section4/4x4x4-r47-alphatensor_F2-258e5b7.json` | not stated | 1 | C entries c_ik converted to our (k,i) on import | pass / pass |

**Convention handling.** The project's tensor is Σ a_ij ⊗ b_jk ⊗ c_ki, with the third factor indexed (k, i)
(`search/gf2mm.py`). Every imported scheme was tried with its third factor read as given and read transposed. It
was accepted only if **exactly one** reading passes `verify`; it then also had to pass `verify_explicit`. For
every file exactly one reading passed, always the (k, i) reading of the data as published. The Kauers–Moosbauer
note prints c_{i,j} = Σ γ_{i,j} m_k, but its electronic file verifies only as c_{k,i}.
The MMC entry lists output formulas "c11 = m1 + …", which were read as entries (i, k) of C = AB and converted.
The parsers for the .exp format and for AlphaTensor's .npz (read without numpy) are those of
`experiments/2026-10-07b_sources.py`, already tested on the 13 + 20 files of RL-059.

**Identical copies.**
* AT, MMC/AlphaTensor and three FM files (`alphatensor_444`, `group_sat_inc`, `n1_probe`) are the same term set.
* FM `gamma_scratch` and `records/gamma47_B` are the same term set (Zaru's "second" scheme).
* KMn's `s47.exp` and KW `47/1b/j1b8560e020060ab4.exp-s1` are the same term set.
* **Kauers' directory is mostly copies.** 99,120 files, 23 distinct term sets.
  * The 99,101 files of `x47/` are only **4 term sets**, repeated 52,319 (identical to the flips-repository file
    KMg), 26,413, 18,601 and 1,768 times.
  * Files with the same term set contain the same multiset of lines, so they differ only in the order of the
    products (checked over all 99,120 files).
  * The 19 files of `47/` are 19 distinct term sets; one of them (`-s1`) is identical to KMn.

**Places searched without a 4×4×4 rank-47 GF(2) scheme (dead ends, documented):**
* AlphaTensor: `factorizations_r.npz` has 4,4,4 at rank 49 (standard arithmetic). `nonequivalence/` holds
  14,236 factorizations of shape (14236, 49, 3, 16), i.e. rank 49 in standard arithmetic (README: "nonequivalent
  algorithms … multiplying 4x4 matrices"; the notebook says rank-49, standard arithmetic). No second rank-47 file.
* Kauers–Moosbauer, flips repository: only `444-47-mod2.exp` for 4×4×4 rank 47. The paper (read on ar5iv) says:
  "none of our more than 100000 schemes of rank 47 for (n,m,p)=(4,4,4) … can be lifted from Z2 to Z4" and "One
  scheme for each format and the implementation of the search procedure are available at
  https://github.com/jakobmoosbauer/flips.git. The other schemes are available upon request."
  The web directory KW (99,116 + 4 files) appears to be that collection, but no text we found says so.
* Moosbauer–Poole, github.com/jakobmoosbauer/symmetric-flips @ `3e2d4dd8`: only 5×5×5 and 6×6×6.
* Arai, Ichikawa & Hukushima (arXiv:2312.16960; HTML v2 read). Table 1 reports that 47 was reproduced for
  (4,4,4), but "the schemes we found for (4,5,5) and (5,5,5) … are explicitly shown in
  https://github.com/Yamato-Arai/adap". That repository @ `fe7b2040` has only `455_73.m` and `555_94.m`.
* Sedoglavic's catalogue (fmm.univ-lille.fr, page `4x4x4.html`): rank 48 (Dumas–Pernet–Sedoglavic, rational;
  AlphaEvolve). No characteristic-2 entry; the index page has no "Z/2", "F2", "GF(2)" or "characteristic" string.
* MMC: exactly one 4×4×4 F2 rank-47 entry (AlphaTensor; included above).
* Repositories linked from Sedoglavic's catalogue or found by search:
  * dronperminov/FastMatrixMultiplication @ `64f58a5e`: 4×4×4 only at rank 49 (ZT); it copies AlphaTensor's
    `factorizations_f2.npz`, a duplicate of AT.
  * FastMatrixMultiplicationOld, FlipGraphGPU and ternary_flip_graph: no 4×4×4 file.
  * khoruzhii/flip-cpd @ `9eeb17f4`: general 4×4×4 only at rank 49; the rank-47 files are other (structured)
    tensors.
  * khoruzhii/flip-graph, khoruzhii/lita and MerlijnW70/fmm-schemes: no 4×4×4 file.
* Web searches for further rank-47 4×4 GF(2) schemes (2023–2026): AlphaEvolve and Dumas–Pernet–Sedoglavic are
  rank 48, not characteristic 2. The cp4space post of 2022-10-06 mentions only AlphaTensor's.

## 2. The equivalence group

We use the group G generated by the transformations of Kauers & Moosbauer, ISSAC 2023, section 2 (text read on
ar5iv, arXiv:2212.01175):
* "exchanging each rank-one tensor A ⊗ B ⊗ Γ by Bᵀ ⊗ Aᵀ ⊗ Γᵀ";
* "replace every rank-one tensor A ⊗ B ⊗ Γ by B ⊗ Γ ⊗ A";
* "if U ∈ K^{m×m} is invertible … replacing every rank-one tensor A ⊗ B ⊗ Γ by AU ⊗ U⁻¹B ⊗ Γ";
* "These transformations generate the symmetry group of M_{n,m,p}. For more details on this group see [6, 13]";
* "call two schemes equivalent if they belong to the same orbit."

Their reference [6] is de Groote 1978, Part II, doi:10.1016/0304-3975(78)90045-2 (DOI checked; the isotropy
group itself is in Part I, doi:10.1016/0304-3975(78)90038-5, DOI checked). Their [13] is Kauers–Moosbauer, A
normal form for matrix multiplication schemes, CAI 2022, doi:10.1007/978-3-031-19685-0_11 (DOI checked). We did
not read de Groote's papers, so we do not claim that G is the *full* isotropy group; we use G by definition.
AlphaTensor's nonequivalence notebook uses the same sandwich action (u ↦ A u B⁻¹, v ↦ B v C⁻¹, w ↦ C w A⁻¹).

In the project's convention (`search/equivalence.py`), G = (GL(4,2)³ ⋊ S₃) acting on the multiset of terms by:
* sandwich (P, Q, R): (a, b, c) ↦ (P a Q⁻¹, Q b R⁻¹, R c P⁻¹);
* cyclic: (a, b, c) ↦ (b, c, a);
* transpose: (a, b, c) ↦ (cᵀ, bᵀ, aᵀ);
* any permutation of the terms.

KM's transposition is ours composed with a cyclic shift, and their U-move is the sandwich (I, U⁻¹, I), so both
generate the same group. Over GF(2) there are no non-trivial scalings of a term.

**Why these maps preserve the tensor.** A scheme is valid iff Σ_r ⟨a_r,X⟩⟨b_r,Y⟩⟨c_r,Z⟩ = tr(XYZ) for all X, Y, Z
(⟨a,X⟩ = Σ a_xy X_xy).
* ⟨PaQ⁻¹, X⟩ = ⟨a, PᵀXQ⁻ᵀ⟩, so a sandwich gives tr(PᵀXYZP⁻ᵀ) = tr(XYZ).
* The cyclic map gives tr(ZXY) = tr(XYZ).
* The transpose gives tr(ZᵀYᵀXᵀ) = tr(XYZ).

Checked in code: random group elements keep the standard algorithm, Strassen, Strassen ⊗ Strassen and RL-054
valid. A non-symmetry (a ↦ Pa alone) is rejected (unit tests).

## 3. Invariants and the exact test

F(S) below is invariant under sandwiches and term permutations. Its **S₃-symmetrised** form is the sorted tuple of
F(σS) over the six σ ∈ S₃. If S′ = g σ₀ S, then {σS′} = {g′ σ σ₀ S}, because S₃ normalises the sandwich group,
so the multisets {F(σS′)} and {F(τS)} coincide. Different invariants therefore **prove** inequivalence; equal
invariants prove nothing.

| Name | Definition | Why it is preserved |
|---|---|---|
| I1 factor-rank profile (RL-059) | multiset of sorted (rank a, rank b, rank c) | rank(PaQ⁻¹) = rank a; transposition keeps rank; S₃ permutes the triple |
| I2 ordered rank profile / S₃ | multiset of ordered triples, S₃-symmetrised | sandwich keeps each rank; S₃ handled by symmetrisation |
| I3 term-label profile / S₃ | per term: ranks of a, b, c, ab, bc, ca, abc, bca, cab and the characteristic polynomial of abc; multiset, S₃-symmetrised | ab ↦ P ab R⁻¹, bc ↦ Q bc P⁻¹, ca ↦ R ca Q⁻¹ (ranks kept); abc ↦ P abc P⁻¹ (a similarity: rank and characteristic polynomial kept); charpoly(abc) = charpoly(bca) = charpoly(cab) |
| I4 WL refinement / S₃ | 3 rounds of colour refinement on the complete graph of terms: vertex colours = I3 labels; ordered-pair colours = ranks of a_r+a_s, b_r+b_s, c_r+c_s, a_r b_s, b_r c_s, c_r a_s, ranks of [a_r \| a_s] and [a_r ; a_s] (likewise b, c), traces of a_r b_s c_r, a_r b_r c_s, a_s b_r c_r | each pair quantity is a rank or a trace of a sandwich- or similarity-transformed matrix; refinement depends only on these multisets, not on the term order |

Colours are named by SHA-256 hashes of sorted tuples. A hash collision could only hide a difference, never invent
one, so the direction of the proof is unaffected.

**Exact test** (`search.equivalence.find_equivalence`). For each σ ∈ S₃ it searches a sandwich g with
g(σS₁) = S₂. "g maps term t to term u" is the linear system u_a Q = P t_a, u_b R = Q t_b, u_c P = R t_c in the 48
entries of (P, Q, R) over GF(2).
1. Backtrack over the images of the terms, rarest I4 colour class first; colours are sandwich-invariant, so only
   same-coloured images can occur.
2. Intersect the solution spaces along the way.
3. Once a solution space has dimension ≤ 14, enumerate it completely, keep the invertible (P, Q, R) and apply each
   one to the whole scheme.

Completeness: every element of G that maps S₁ to S₂ maps the first base term to some same-coloured term of S₂.
That branch is tried, and the solution space containing g is enumerated in full. "None" is therefore a proof of
inequivalence under G. A returned certificate is checked by applying it.

## 4. Comparison

Script: `experiments/2026-10-06c_equivalence.py`; console copy `search/runs/2026-10-06c_equivalence.console.txt`
(total run time 28.9 s on the cached collection).

Our 4×4×4 rank-47 files under `search/schemes/**` at run time: 14 files, all passing `verify` and
`verify_explicit`, forming **6 distinct term sets**:
* RL-054 seed 8, plus eight identical copies in `rust-2026-10-07b/from47/`;
* five files in `rust-2026-10-06c/` (another agent's run, files written 12:29–12:30). Four come from
  `search/kernel/flipwalk.rs` with kernel SHA-256 `69837abe…`; `before_seed707` comes from
  `experiments/2026-10-06c_flipwalk_before.rs` with SHA-256 `6f306293…`.

**Published term sets and their classes** (25 distinct term sets from 99,129 files):

| Class | Term sets (files) | I1 factor-rank profile shared by the class |
|---|---|---|
| A: AlphaTensor | AT = FM×3 = MMC (5 files); KW-47 `j1c3432…`, `j2811c1…`, `j2e624b…`, `j55c22f…`, `j721607…`; KW-x47 `j00baf1…` (26,413 files), `j00379b…` (1,768 files): 8 term sets | AT's (RL-059) |
| B: Kauers–Moosbauer | KMg = 52,319 KW-x47 files; KMn = KW-47 `…-s1`; KW-47 `j05133b…`, `j1ac63e…`, `j1b8560…` (+`-s2`, `-w1`, `-w2`), `j4ad1a9…`, `j54a64f…`, `j5aaedf…`, `j6c3a25…`, `j6f7c55…`, `ja4257b…`; KW-x47 `j019fb8…` (18,601 files): 15 term sets | KMg's (RL-059) |
| C: Zaru (FastMatrixF2) | `gamma_scratch` = `records/gamma47_B` (2 files): 1 term set | its own |
| D: RL-054 class | KW-47 `b0/jb050da4aa249f5a` (1 file): 1 term set | RL-054's |

How the classes were decided:
* Inside A, AT was exactly tested against each of the other 7 term sets: all equivalent, certificates found.
* Inside B, KMg was tested against KMn and KMn against the other 13: all equivalent.
* The four classes have four different I1 profiles, so they are pairwise inequivalent. I2 and I3 also take
  exactly 4 values on the 25 sets.

**Our term sets against the published ones:**

| Our scheme | vs class A | vs class B | vs class C | vs class D |
|---|---|---|---|---|
| RL-054 seed 8 (+ 8 copies) | inequivalent (I1), all 8 term sets | inequivalent (I1), all 15 | inequivalent (I1) | **EQUIVALENT** (exact test, certificate re-checked independently) |
| rust-2026-10-06c class (5 term sets, pairwise equivalent by certificates) | inequivalent (I1), all 8 | inequivalent (I1), all 15 | inequivalent (I1) | inequivalent (I1) |

RL-054 vs the rust-2026-10-06c class: inequivalent (I1).

Pairs not separated by any invariant: only RL-054 vs KW-47 `jb050da4aa249f5a`. The exact test decided it (equivalent),
so **no pair is left undecided**.

Positive controls in the same run:
* random group elements applied to each of our 6 term sets were recognised (certificate found, invariants equal,
  18/18);
* the AT and KMg/KMn identities above are exact certificates on real third-party data;
* `tests/test_search_equivalence.py`: 16 tests OK in about 5 s.

## 5. Conclusion

1. **RL-054's rank-47 scheme is equivalent** under G = GL(4,2)³ ⋊ S₃ (with term permutations) to the published
   scheme `solutions/444/47/b0/jb050da4aa249f5a.exp` in Manuel Kauers' web directory (listing date 2022-10-27).
   This is a constructive proof: a certificate (σ, P, Q, R), re-checked by independent code. An equivalence
   certificate stays valid under any larger notion of equivalence. **RL-054 is therefore a rediscovery of a
   published scheme (up to symmetry), not a new scheme.** It remains a correct, verified rank-47 scheme.
2. **The rust-2026-10-06c class** (five schemes, pairwise equivalent) is inequivalent to all 99,129 published
   4×4×4 rank-47 GF(2) schemes we could obtain. Those are 25 distinct term sets in 4 classes: AlphaTensor
   (Fawzi et al. 2022), Kauers–Moosbauer (flips repository; arXiv:2210.04045; Kauers' directory), Zaru
   (FastMatrixF2, 2026), and the Kauers-directory class that contains RL-054. The proof is a different
   factor-rank profile, which G preserves.
   * This is relative to G as defined in section 2, the notion used by Kauers–Moosbauer and AlphaTensor.
   * It does **not** mean "new" in an absolute sense. Kauers and Moosbauer report "more than 100000" rank-47
     schemes, and the directory holds only 23 distinct term sets; their full set may contain more classes.
   * Unpublished or overlooked schemes may exist, and catalogues we did not find may hold others.
   * The files are another agent's in-progress output.
3. RL-059's "inequivalent to the AlphaTensor and the Kauers–Moosbauer files" remains true for RL-054, but the
   novelty question raised in RL-061 is now answered negatively for RL-054.

## 6. Near-misses

* **RL-054 looked new against the two files RL-059 checked, and against 99,128 of the 99,129 published files.**
  The only match was one file in a 19-file folder that no paper we read cites.
* **The matching published scheme shares 0 of its 47 terms with ours.** Identical-term checks, or "zero terms in
  common", say nothing about equivalence. FastMatrixF2's inequivalence argument rests on the factor-rank
  signature, not on its "0 terms in common" remark.
* **Kauers' `x47/` folder looked like 99,101 schemes but holds only 4 distinct term sets**, all in classes A
  and B. The paper's "more than 100000 schemes" may count walks or files rather than distinct schemes; we could
  not determine which.
* **The rust-2026-10-06c class** is separated from every published class by the coarsest invariant (I1), so its
  inequivalence does not hinge on any fine invariant. Whether it occurs among Kauers–Moosbauer's unpublished
  schemes is unknown.

## 7. Decision log

* **D1: download the whole Kauers web collection (99,120 files), not a sample.** Alternatives: a sample (cheaper
  for the server and for us), or only the 19-file `444/47/` folder. A sample cannot support "inequivalent to all
  N published schemes", and the folder alone would miss any class that exists only in `x47/`.
  * Deciding evidence: the directory listings (273 pages) showed 99,116 + 4 files, which matches the paper's
    "more than 100000 schemes" kept "available upon request".
  * Cost: one request per file, 4 parallel connections, cached, never repeated; the crawl stage took 925 s on
    the final run.
  * Process note: the first full run was stopped at 55,586 downloads to include the four variant files
    (`-s1`, `-s2`, `-w1`, `-w2`). The cache kept every completed download, so nothing was fetched twice.
* **D2: define equivalence by the group KM list, not by the full isotropy group.** We did not read de Groote, so
  we do not claim fullness.
  * An *equivalence* certificate holds under any larger group.
  * An *inequivalence* result is relative to G, which is the notion KM and AlphaTensor use.
* **D3: accept a converted scheme only if exactly one reading of the third factor verifies.** Alternative: trust
  each source's stated convention. Rejected, because the KM note prints c_{i,j} = Σ γ_{i,j} m_k while its file
  verifies only as c_{k,i}. Every one of the 99,129 files was decided by the verifier, never by a guess.
* **D4: tiered invariants (I1–I3 on everything, I4 and the exact test only where needed).** Alternative: run the
  exact test on all pairs. That is unnecessary where a cheap invariant already proves inequivalence, and too slow
  for 99k schemes (about 1 s per pair with WL).
* **D5: exact test by linear algebra plus backtracking instead of a canonical form.** A canonical form under
  GL(4,2)³ ⋊ S₃ would be faster for classifying 99k schemes, but harder to get provably right in the time box.
  For pairwise questions the backtracking test is complete and gives a checkable certificate.
* **D6: certificates are re-checked by separately written code.** The check uses list arithmetic and brute-force
  inverses, with no use of `search/equivalence.py`. It also verifies that the same group element maps the standard
  algorithm to a valid scheme. This guards against a bug in `apply_sandwich` that could make two schemes look
  equivalent.
* **D7: run `verify_explicit` on every one of the 99,129 schemes** (about 15 min on 3 processes), not on a sample,
  so that "passes both exact verifiers" holds for each scheme. Three processes kept the load moderate next to the
  other agent's searches.
* **D9: include the five rank-47 files that appeared in `search/schemes/rust-2026-10-06c/` during the session.**
  The task covers "every other saved 4×4×4 rank-47 scheme in `search/schemes/`". The analysis script picks up
  whatever is present at run time, and its console lists the files it saw. These files belong to another agent;
  this audit only classifies them.
* **D8: no third-party data in the repository.** All downloads go to a cache outside the repository; the
  collector re-downloads them. The flips repository and the Kauers directory state no license for their data.

## 8. Open ideas

*Forward-looking content is not published (RL-086).*

## 9. Reproduction

```
export NOVELTY_CACHE=<a directory outside the repository>
./.venv/Scripts/python experiments/2026-10-06c_collect.py       # downloads (cached), converts, verifies
./.venv/Scripts/python experiments/2026-10-06c_equivalence.py   # invariants, exact tests, controls
./.venv/Scripts/python -m unittest tests.test_search_equivalence
```

Console copies of this session's runs: `search/runs/2026-10-06c_collect.console.txt`, `search/runs/2026-10-06c_equivalence.console.txt`.
