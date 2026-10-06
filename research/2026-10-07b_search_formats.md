# Flip-graph search, round 2: best known ranks of small formats, small-format runs and 4×4×4 statistics

Date: 2026-10-06 (runs 09:56-10:55 local time). Follows RL-036, RL-052 and RL-054.
Author: delegated research agent (Claude), for the maintainer. Every number below comes from a run made here
(script, seed, budget, time, steps are given) or from a source whose identifier or content was checked
(section 2). Nothing here is a new result unless explicitly labelled, and nothing is claimed as a discovery.

## Summary

* **Best known ranks (section 2).** Over GF(2): (2,2,3) 11, (2,2,4) 14, (2,3,3) 15, (2,3,4) 20, (2,4,4) 26,
  (3,3,4) 29, (3,3,5) 36, (3,4,4) 38, (3,4,5) 47, (4,4,4) **47**, (4,4,5) **60**. Over general rings the values
  are the same except (4,4,4) **48** and (4,4,5) **61**. Every GF(2) value is backed by a published scheme file
  that we downloaded and verified with both exact verifiers (AlphaTensor's 20 GF(2) factorizations and 13
  Kauers-Moosbauer files), plus two catalogues. **47 is still the best known 4×4×4 rank over GF(2)** in every
  source consulted (residual risks listed in section 2).
* **Small formats (section 3), 8 seeds each, from the standard algorithm, 30-180 s per walk:** the best known
  GF(2) rank was reached by 8/8 seeds for (2,2,3), (2,2,4), (2,3,3), (2,3,4), (2,4,4), (3,3,4), (3,3,5); by 6/8 for
  (3,4,4); by 1/8 for (3,4,5) (rank 47 at 97.2 s, step 1.56·10⁹); by 0/8 for (4,4,5) (best 64 against 60).
  These are **VERIFIED rediscoveries** of known ranks, not new results. No walk went below a best known rank.
* **4×4×4 statistics (section 4):** 24 fresh uncapped walks × 900 s: **0/24 reached 48 or 47** (exact 95% interval
  for the frequency of reaching 47 within 900 s: 0-0.142; pooled with RL-054: 1/28, interval 0.001-0.183). 20/24
  stalled at 49 (median 13.8 s to get there). 19 of those 20 endpoints have no pair of terms sharing a factor, so
  no flip is possible there; 18 have the factor-rank invariant of Strassen ⊗ Strassen. RL-054's rank 47 in 726.7 s
  was not typical of this kernel and setting.
* **Rank 46 (sections 3-4): NULL.** Scope: RL-054 seed 8 after reaching 47 (1073 s, 2.42·10¹⁰ steps) plus
  8 walks × 120 s from that rank-47 scheme (2.83·10¹⁰ steps; plateau 50 000 for 4 walks, 5 000 for 4). A null
  result proves nothing about the existence of rank 46.
* **Candidates below the best known: none.** All 112 saved schemes pass `verify`, `verify_explicit` and 200
  random GF(2) matrix checks; none is valid over Z as it stands (information only).
* **Equivalence:** AlphaTensor's, Kauers-Moosbauer's and RL-054's rank-47 schemes have pairwise different
  factor-rank invariants, so they are pairwise **inequivalent** (proved by the invariant).
* **Search budget used:** 2701 s + 722 s + 120 s = 3543 s (59.1 min) of wall clock, never more than 8 walk processes.
  The kernel was not changed (task item 4 not done; decision D5).

## 1. Setup

* Kernel: `search/kernel/flipwalk.rs`, **unchanged** (SHA-256 `6f306293…ad644`, the same kernel as RL-054,
  checked against the `kernel_sha256` field of the RL-054 logs). `search/kernel_reference.py` and the tests were
  not touched; the optional throughput work (task item 4) was not done (decision D5).
* Driver: `python -m search.rust_kernel` (one process per walk, below-normal priority). Every walk's best scheme
  was re-verified by the exact Python verifier (`gf2mm.verify` plus an 8-trial random-matrix check) before it was
  logged or saved; `experiments/2026-10-07b_analysis.py` then re-verified every saved file separately (section 5).
* Machine: Windows 11, 16 logical CPUs, Python 3.14.2; at most 8 walk processes ran at any time.
* Kernel parameters: no weight cap, plateau 50 000 steps, slack 3 (as RL-054 job B) in all runs, except seeds 5-8
  of the rank-46 attempt (plateau 5 000; decision D10). A "step" is one
  proposed flip (a random term and factor position, then a random partner sharing that factor if one exists).
* Search wall clock: 4×4 statistics 2701 s (09:56:20-10:41:21), small formats 722 s (10:41:25-10:53:28),
  rank-46 attempt 120 s (10:53:29-10:55:29); total 3543 s = 59.1 min.

## 2. Best known ranks (verified sources)

Script: `experiments/2026-10-07b_sources.py` (console copy: `search/runs/2026-10-07b_sources.console.txt`).
"Best known" means: the lowest rank found in the sources below as consulted on 2026-10-06. It is not a full
literature survey (residual risks at the end of this section).

| Format (n,m,p) | naive | best known over **GF(2)** | best known over **general rings** (bilinear, non-commutative) |
|---|---|---|---|
| (2,2,3) | 12 | **11** [KM-v, AT-v, MMC] | **11** [KM-v(Z), HK] |
| (2,2,4) | 16 | **14** [KM-v, AT-v, MMC] | **14** [KM-v(Z), HK] |
| (2,3,3) | 18 | **15** [KM-v, AT-v, MMC] | **15** [KM-v(Z), Cat: Hopcroft & Kerr 1971] |
| (2,3,4) | 24 | **20** [KM-v, AT-v, MMC] | **20** [KM-v(Z), Cat: Hopcroft & Kerr 1971] |
| (2,4,4) | 32 | **26** [KM-v, AT-v, MMC] | **26** [KM-v(Z), Cat: Hopcroft & Kerr 1971] |
| (3,3,4) | 36 | **29** [KM-v, AT-v, MMC] | **29** [KM-v(Z), Cat: Smirnov 2013] |
| (3,3,5) | 45 | **36** [KM-v, AT-v, MMC] | **36** [KM-v(Z), Cat: Smirnov 2013] |
| (3,4,4) | 48 | **38** [KM-v, AT-v, MMC] | **38** [KM-v(Z), Cat: Smirnov 2013] |
| (3,4,5) | 60 | **47** [KM-v, AT-v, MMC] | **47** [KM-v(Z), Cat: Fawzi et al. 2022] |
| (4,4,4) | 64 | **47** [AT-v and KM-v (both GF(2) only), MMC: AlphaTensor, DPS] | **48** [Cat: AlphaEvolve 2025 (complex), DPS (rational, any ring except characteristic 2), MMC Q]; over Z we verified 49 [KM-v(Z)] |
| (4,4,5) | 80 | **60** [KM-v (GF(2) only), MMC: Kauers-Moosbauer 2023]; AlphaTensor's own: 63 [AT-v] | **61** [Cat: AlphaEvolve 2025; MMC Q and Z; primary source not read]; over Z we verified 62 [KM-v(Z)] |
| context: (2,2,2) | 8 | 7 | 7 [Cat: Strassen 1969] |
| context: (3,3,3) | 27 | 23 | 23 [Cat: Laderman 1976] |

Legend and what exactly was checked:

* **KM-v** = we downloaded the published scheme file of Kauers & Moosbauer, *Flip Graphs for Matrix
  Multiplication* (ISSAC 2023, doi:10.1145/3597066.3597120; data repository github.com/jakobmoosbauer/flips,
  `solutions/<nmp>-<rank>-mod<0|2>.exp`, where mod2 means characteristic two and mod0 arbitrary fields), parsed it
  and verified it **ourselves**: over GF(2) with both exact verifiers (`verify`, `verify_explicit`), after reducing
  the coefficients mod 2 and dropping zero terms (no term vanished in any file), and, marked **(Z)**, over the
  integers with an exact integer Brent-equation check written in the script. All 13 files verified in the
  convention c_ki (the repository's convention). Results: 11 mod0 files at the ranks in the table verify over GF(2)
  and over Z; `444-47-mod2` and `445-60-mod2` verify over GF(2) and **not** over Z, as their names say.
  A verified file proves that a scheme of that rank exists; it does not say that nothing better is known.
* **Cat** = Sedoglavic's catalogue, https://fmm.univ-lille.fr/ (5426 algorithms; HTML table rows parsed by the
  script, rank and cited reference copied). The page has no row of its own for (2,2,3) and (2,2,4), and contains
  no "Z/2Z", "GF(2)" or "characteristic" annotation, so it is used for general rings only.
* **MMC** = the Matrix Multiplication Catalog (https://solven.eu/matmulcatalog, `catalog.json`, 9627 stored
  schemes, each with the list of fields in which it is valid, including F2). The script takes the minimum rank
  per format and field. Its Z minima for (2,2,3), (2,2,4), (3,3,3), (3,3,4), (3,3,5), (4,4,4) are lower (10, 13,
  21, 27, 33, 46) but those entries are flagged `commutative: true` (Waksman 1970, Rosowski 2019): commutative
  algorithms, not bilinear schemes, unusable recursively, and excluded here. Its `cited-bounds.json` (claims
  without factor matrices) has no non-commutative claim below the table for these formats.
* **HK** = Hopcroft & Kerr 1971 (doi:10.1137/0120004). Their formula ⌈(3pn + max(n,p))/2⌉ for p×2 by 2×n
  gives 11 for (2,2,3) and 14 for (2,2,4); the Crossref abstract (quoted in research/2026-10-07_search_flipgraph.md)
  says it is minimal for p = 1 or 2. The abstract does not name the ground ring, so we do not claim optimality
  over GF(2).
* **DPS** = Dumas, Pernet & Sedoglavic, arXiv:2506.13242 (abstract read via the arXiv API): the 4×4 count "was
  reduced in [Fawzi et al. 2022] from 49 … to 47 in characteristic 2, and more recently to 48 in [AlphaEvolve]
  over the complex numbers"; their own 48-multiplication algorithm uses rational coefficients and is "valid over
  any ring except those of characteristic 2".
* **AlphaEvolve** = Novikov et al., arXiv:2506.13131 (abstract read): 4×4 complex-valued matrices with 48 scalar
  multiplications.
* **AT-v** = AlphaTensor (Fawzi et al. 2022, Nature 610, doi:10.1038/s41586-022-05172-4, DOI checked): we
  downloaded its published GF(2) factorizations (github.com/google-deepmind/alphatensor,
  `algorithms/factorizations_f2.npz`, 20 formats), read them without numpy (hand-parsed .npy; object arrays through
  a restricted unpickler that only accepts numpy's array and dtype reconstructors) and verified all 20 with both
  exact verifiers (convention c_ki). Ranks: (2,2,2) 7, (2,2,3) 11, (2,2,4) 14, (2,2,5) 18, (2,3,3) 15, (2,3,4) 20,
  (2,3,5) 25, (2,4,4) 26, (2,4,5) 33, (2,5,5) 40, (3,3,3) 23, (3,3,4) 29, (3,3,5) 36, (3,4,4) 38, (3,4,5) 47,
  (3,5,5) 58, (4,4,4) **47**, (4,4,5) 63, (4,5,5) 76, (5,5,5) 96. We did not read the paper's table.
* DOIs checked with `tools/check_sources.lookup_doi` (title and year returned, all 6 OK): 10.1038/s41586-022-05172-4,
  10.1145/3597066.3597120, 10.1137/0120004, 10.1134/S0965542513120129 (Smirnov 2013, *The bilinear complexity and
  practical algorithms for matrix multiplication*; DOI taken from the catalogue's bibliography; paper not read),
  10.1007/BF02165411, 10.1090/S0002-9904-1976-13988-2.
* arXiv API: two calls (one batch of 6 ids, one of 2). Abstract facts used: Kauers & Moosbauer (2212.01175)
  reduced (4,4,5) and (5,5,5) "both in characteristic two and for arbitrary ground fields"; Arai, Ichikawa &
  Hukushima (2312.16960) 4×5×5 from 76 to 73 and 5×5×5 from 95 to 94, "obtained in characteristic two" (outside
  our table); Kauers & Wood (2510.19787) "improved rank bounds for about thirty matrix formats" (formats not
  checked); Perminov 2511.20317 ("30 rank improvements in the binary field", formats not checked), 2603.02398 and
  2606.02480 (rank improvements, mostly larger formats; not checked individually).

**Is 47 still the best known 4×4×4 rank over GF(2)?** Yes, as far as these sources go: the MMC's F2 minimum is 47
(AlphaTensor), DPS (abstract, v7) still describes 47 as the characteristic-2 state of the art, the MMC's
cited-bounds file (4 non-commutative claims for these formats, the lowest for 4×4×4 being 49) and the
papers' abstracts contain no lower claim, and both published characteristic-2
schemes (AlphaTensor's and Kauers-Moosbauer's) have rank 47 and verify here. **Residual risk:** the binary-field improvements of Perminov (2511.20317) and
the formats of Kauers & Wood were not checked one by one, and the MMC may not hold every characteristic-2 scheme
(e.g. it lists 76 for (4,5,5) in F2, while Arai et al. report 73 in characteristic two). A rank-46 claim would
therefore need a literature check by the maintainer in any case.

## 3. Runs

All runs: kernel SHA-256 `6f306293…ad644`, no weight cap, slack 3, below-normal priority, 8 walk processes at a
time, from the standard algorithm unless stated. Every walk used its full time budget (none reached its target
rank). Numbers from `experiments/2026-10-07b_analysis.py` (console copy `search/runs/2026-10-07b_analysis.console.txt`).

### 3.1 Small formats (`experiments/2026-10-07b_small_formats.py`, seeds 1-8 per format, target = best known − 1)

| Format | best known GF(2) | s per walk | best rank per seed (seeds 1-8) | seeds at best known | first reached best known: min / median / max s (steps) | steps/s (median) |
|---|---|---|---|---|---|---|
| (2,2,3) | 11 | 30 | 11 ×8 | 8/8 | 0.000 / 0.000 / 0.001 s (1.99·10³ / 3.22·10³ / 1.03·10⁴) | 3.04·10⁷ |
| (2,2,4) | 14 | 30 | 14 ×8 | 8/8 | 0.001 / 0.002 / 0.005 s (1.29·10⁴ / 3.53·10⁴ / 1.14·10⁵) | 2.76·10⁷ |
| (2,3,3) | 15 | 30 | 15 ×8 | 8/8 | 0.000 / 0.002 / 0.008 s (1.16·10⁴ / 5.03·10⁴ / 2.31·10⁵) | 5.63·10⁷ |
| (2,3,4) | 20 | 30 | 20 ×8 | 8/8 | 0.022 / 0.052 / 0.272 s (4.98·10⁵ / 1.16·10⁶ / 6.78·10⁶) | 3.13·10⁷ |
| (2,4,4) | 26 | 60 | 26 ×8 | 8/8 | 0.068 / 0.748 / 3.666 s (1.88·10⁶ / 1.52·10⁷ / 8.72·10⁷) | 3.54·10⁷ |
| (3,3,4) | 29 | 60 | 29 ×8 | 8/8 | 0.211 / 1.013 / 4.968 s (5.23·10⁶ / 2.46·10⁷ / 1.20·10⁸) | 3.25·10⁷ |
| (3,3,5) | 36 | 60 | 36 ×8 | 8/8 | 1.483 / 5.804 / 20.808 s (2.85·10⁷ / 1.03·10⁸ / 3.59·10⁸) | 2.62·10⁷ |
| (3,4,4) | 38 | 60 | 38, 38, 38, **39**, 38, 38, 38, **39** | 6/8 | 0.992 / 8.809 / 53.993 s (1.69·10⁷ / 1.91·10⁸ / 1.19·10⁹) | 2.26·10⁷ |
| (3,4,5) | 47 | 180 | 48, 48, 51, 51, 49, 48, **47**, 48 | 1/8 | 97.162 s (1.56·10⁹), seed 7 | 1.65·10⁷ |
| (4,4,5) | 60 | 180 | 64, 64, 65, 66, 65, 64, 66, 66 | 0/8 | – | 1.45·10⁷ |

Wall clock 722 s (each format 30.2-180.3 s). All 80 results passed the exact verifier.
**Status:** for the first nine formats, the best known GF(2) rank was reached (VERIFIED rediscovery; for the seven
smallest formats, every seed got there in at most 21 s). **NULL below the best known rank** for all ten formats
within these budgets (8 walks each, 30-180 s). For (4,4,5) even AlphaTensor's 63 was not reached (best 64).

### 3.2 4×4×4 statistics (`experiments/2026-10-07b_4x4_nocap_stats.py`)

24 seeds (101-124) × 900 s, plateau 50 000; details in section 4. Best rank 49 (20 walks); NULL for rank ≤ 48.

### 3.3 Rank-46 attempt from a rank-47 scheme (`experiments/2026-10-07b_4x4_from47.py`)

Start: `search/schemes/rust-2026-10-07/4x4x4_rank47_seed8.json` (RL-054), target 46, 120 s per walk, 10:53:29-10:55:29.

| Seeds | plateau | best rank (each walk) | steps per walk | steps/s | flips per walk | plus transitions per walk | restarts |
|---|---|---|---|---|---|---|---|
| 1-4 | 50 000 | 47, 47, 47, 47 (no improvement) | 3.52-3.56·10⁹ | 2.93-2.97·10⁷ | 243 386-256 130 | 68 911-69 652 | 0 |
| 5-8 | 5 000 | 47, 47, 47, 47 (no improvement) | 3.50-3.54·10⁹ | 2.92-2.95·10⁷ | 2 495 290-2 515 254 | 684 750-693 565 | 0 |

Total 2.825·10¹⁰ steps in 960 walk-seconds. **NULL for rank 46** in this scope. Each plus transition was followed by
only 3.5-3.7 flips on average (e.g. 256 130 flips / 68 911 plus transitions for seed 1), and no walk ever drifted more than 3
above 47 (0 restarts), which is consistent with the walk falling back into a dead end each time. The ten-fold plateau reduction multiplied the
flips by ten and changed nothing else visible. The 8 saved files are identical to the start scheme (checked by the
analysis script), so they are **not** new rediscoveries.

## 4. 4×4×4 statistics (uncapped walks from the standard algorithm)

Run: `experiments/2026-10-07b_4x4_nocap_stats.py`, 24 seeds (101-124) × 900 s, 8 walk processes at a time,
09:56:20-10:41:21 (2701 s wall clock), log `search/runs/2026-10-07b_4x4_nocap.jsonl`. Numbers from
`experiments/2026-10-07b_analysis.py`.

**Result: no walk reached 48 or 47. NULL for rank ≤ 48 in this run** (24 walks, 5.135·10¹¹ steps in total,
21 600 walk-seconds). Final best ranks: 49 in 20 walks, 50 in 1, 51 in 2, 52 in 1.

| Event within 900 s | walks | exact 95% interval (Clopper-Pearson) | times first reached (s) |
|---|---|---|---|
| rank ≤ 49 | 20/24 | 0.626-0.953 | 0.3, 0.4, 0.8, 0.9, 2.0, 2.2, 2.5, 3.4, 4.0, 13.3, 14.3, 19.2, 27.5, 35.2, 45.6, 75.4, 84.2, 325.7, 622.8, 774.6 (median 13.8 s, 1.93·10⁸ steps) |
| rank ≤ 48 | 0/24 | 0-0.142 | – |
| rank ≤ 47 | 0/24 | 0-0.142 | – |
| rank ≤ 47, pooled with RL-054 job B truncated at 900 s | 1/28 | 0.001-0.183 | 726.7 (RL-054 seed 8) |

The pooled line mixes two machine loads (12 processes in RL-054, 8 here); in steps, RL-054 seed 8 reached 47 at
step 1.230·10¹⁰, which is within the step range of the walks here (1.23·10¹⁰ to 2.42·10¹⁰ steps per walk).
So the frequency of reaching 47 within about 900 s (or about 1.2-2.4·10¹⁰ steps) is low: the point estimate
is 1/28 ≈ 0.036, and the data exclude frequencies above 0.183 at 95% confidence. **RL-054's hit was not typical.**

Per walk (first time a rank ≤ r was reached; steps/s over the whole walk):

| seed | final | ≤52 (s) | ≤50 (s) | ≤49 (s; step) | steps | steps/s | flips | plus transitions | restarts |
|---|---|---|---|---|---|---|---|---|---|
| 101 | 49 | 1.2 | 1.5 | 2.5; 4.19·10⁷ | 2.381·10¹⁰ | 2.646·10⁷ | 25 622 648 | 466 597 | 0 |
| 102 | 49 | 20.9 | 84.2 | 84.2; 1.576·10⁹ | 2.317·10¹⁰ | 2.574·10⁷ | 213 512 184 | 453 491 | 2 |
| 103 | 51 | 2.3 | – | – | 1.758·10¹⁰ | 1.953·10⁷ | 1 908 742 224 | 341 885 | 1 |
| 104 | 49 | 1.5 | 325.7 | 325.7; 5.151·10⁹ | 2.031·10¹⁰ | 2.256·10⁷ | 1 134 351 950 | 396 610 | 3 |
| 105 | 49 | 1.7 | 19.1 | 19.2; 3.070·10⁸ | 2.348·10¹⁰ | 2.608·10⁷ | 79 308 671 | 459 844 | 0 |
| 106 | 49 | 0.8 | 0.8 | 0.8; 1.022·10⁷ | 2.362·10¹⁰ | 2.625·10⁷ | 22 273 255 | 462 645 | 0 |
| 107 | 49 | 1.1 | 768.9 | 774.6; 1.178·10¹⁰ | 1.503·10¹⁰ | 1.670·10⁷ | 2 381 607 742 | 292 015 | 0 |
| 108 | 49 | 4.4 | 35.2 | 35.2; 5.963·10⁸ | 2.341·10¹⁰ | 2.601·10⁷ | 118 086 273 | 458 375 | 2 |
| 109 | 49 | 0.3 | 0.3 | 0.3; 3.127·10⁶ | 2.389·10¹⁰ | 2.654·10⁷ | 20 745 639 | 467 983 | 0 |
| 110 | 49 | 0.5 | 3.9 | 4.0; 5.823·10⁷ | 2.385·10¹⁰ | 2.650·10⁷ | 28 970 813 | 467 268 | 0 |
| 111 | 51 | 18.9 | – | – | 1.228·10¹⁰ | 1.364·10⁷ | 3 790 080 541 | 235 993 | 1 |
| 112 | 49 | 1.5 | 2.0 | 2.0; 2.515·10⁷ | 2.379·10¹⁰ | 2.643·10⁷ | 24 341 291 | 466 303 | 0 |
| 113 | 49 | 2.4 | 3.3 | 3.4; 4.406·10⁷ | 2.372·10¹⁰ | 2.636·10⁷ | 28 101 454 | 464 947 | 0 |
| 114 | 49 | 0.9 | 0.9 | 0.9; 9.969·10⁶ | 2.388·10¹⁰ | 2.654·10⁷ | 21 969 964 | 467 934 | 0 |
| 115 | 49 | 10.4 | 14.3 | 14.3; 1.989·10⁸ | 2.367·10¹⁰ | 2.630·10⁷ | 56 758 114 | 463 896 | 2 |
| 116 | 49 | 3.7 | 13.3 | 13.3; 1.877·10⁸ | 2.354·10¹⁰ | 2.615·10⁷ | 53 963 052 | 461 202 | 1 |
| 117 | 50 | 2.1 | 612.2 | – | 1.622·10¹⁰ | 1.803·10⁷ | 2 522 049 790 | 315 095 | 0 |
| 118 | 49 | 0.4 | 0.4 | 0.4; 4.820·10⁶ | 2.415·10¹⁰ | 2.683·10⁷ | 21 727 862 | 473 044 | 0 |
| 119 | 49 | 5.7 | 44.1 | 45.6; 7.125·10⁸ | 2.364·10¹⁰ | 2.627·10⁷ | 166 776 584 | 462 932 | 1 |
| 120 | 49 | 20.3 | 27.5 | 27.5; 4.342·10⁸ | 2.104·10¹⁰ | 2.338·10⁷ | 1 067 686 210 | 410 391 | 2 |
| 121 | 52 | 4.4 | – | – | 1.450·10¹⁰ | 1.611·10⁷ | 2 860 531 355 | 281 284 | 1 |
| 122 | 49 | 1.1 | 622.8 | 622.8; 1.019·10¹⁰ | 1.752·10¹⁰ | 1.947·10⁷ | 2 206 652 404 | 340 741 | 1 |
| 123 | 49 | 1.5 | 74.8 | 75.4; 1.193·10⁹ | 2.342·10¹⁰ | 2.602·10⁷ | 269 154 523 | 458 495 | 0 |
| 124 | 49 | 1.1 | 2.2 | 2.2; 3.681·10⁷ | 2.396·10¹⁰ | 2.662·10⁷ | 26 128 409 | 469 272 | 0 |

Every walk used its full 900.0 s; all 24 results passed the exact verifier.

**Why the walks stall at 49 (diagnostic, measured on the saved endpoints):** 18 of the 20 rank-49 endpoints have
exactly the factor-rank invariant of Strassen ⊗ Strassen (36 terms with factor ranks (1,1,1), 12 with (2,2,2),
1 with (4,4,4)), and 19 of the 20 have **no pair of terms sharing a factor** ("0 flippable pairs"; Strassen ⊗
Strassen itself also has 0). Equal invariants do not prove equivalence to Strassen ⊗ Strassen, but the
consequence is the same: at such a scheme no flip is possible, every step fails to find a partner, and the walk
moves only through one plus transition per 50 000-step plateau (about 4.6·10⁵ per walk here); none of the 20 walks
improved after reaching 49. The counters show it: the nine walks that reached 49 within 5 s (seeds 101, 106, 109,
110, 112, 113, 114, 118, 124) made 2.07-2.90·10⁷ flips each in 2.36-2.42·10¹⁰ steps (about 0.1% of the steps),
while the four walks that never reached 49 made 1.91-3.79·10⁹ flips in 1.23-1.76·10¹⁰ steps (11-31%). Their higher steps/s (2.6·10⁷ against 1.4-2.0·10⁷) is idle scanning, not useful work.
The exceptions: seed 120's endpoint has 5 flippable pairs and a different invariant; seed 107's has a different
invariant but 0 flippable pairs. RL-054's rank-47 scheme (seed 8) also has 0 flippable pairs. RL-054 seed 8 went
from 50 directly to 47 at a single step (1.230·10¹⁰), without passing through a rank-49 dead end.

Throughput (this run): 1.364-2.683·10⁷ steps/s per walk (median 2.612·10⁷) with 8 walks on 16 logical CPUs;
RL-054 job B measured 1.486-2.153·10⁷ steps/s with 12 walks. Steps per second mostly reflects how often a walk is
at a dead end (see above), so flips per second is the better measure of useful work.

## 5. Saved schemes and status labels

Every walk's verified best scheme was saved by `search/rust_kernel.py` (status label computed against the
`--best-known` value given in each launcher, which equals the GF(2) value of section 2). The analysis script then
re-verified all **112** files separately: `verify` (bit-sliced Brent equations), `verify_explicit` (one coefficient
at a time), 200 random GF(2) matrix pairs (seed 20261007) and, for information, `verify_over_integers`.
**All 112 pass the three GF(2) checks; none is valid over Z as it stands; none is below the best known rank.**

| Folder | Files | Status label | Note |
|---|---|---|---|
| `search/schemes/rust-2026-10-07b/` | 2x2x3 rank 11 (×8), 2x2x4 rank 14 (×8), 2x3x3 rank 15 (×8), 2x3x4 rank 20 (×8), 2x4x4 rank 26 (×8), 3x3x4 rank 29 (×8), 3x3x5 rank 36 (×8), 3x4x4 rank 38 (seeds 1-3, 5-7), 3x4x5 rank 47 (seed 7) | matches best known (63 files) | VERIFIED rediscoveries of known ranks |
| same | 3x4x4 rank 39 (seeds 4, 8); 3x4x5 rank 48 (seeds 1, 2, 6, 8), 49 (seed 5), 51 (seeds 3, 4); 4x4x5 rank 64 (seeds 1, 2, 6), 65 (3, 5), 66 (4, 7, 8); 4x4x4 rank 49 (20 seeds), 50 (117), 51 (103, 111), 52 (121) | above best known (41 files) | kept for the record (near-misses, section 6) |
| `search/schemes/rust-2026-10-07b/from47/` | 4x4x4 rank 47, seeds 1-8 | the CLI labels them "matches best known" | identical copies of the RL-054 start scheme; **not** rediscoveries |

Equivalence: the three rank-47 4×4×4 schemes available (AlphaTensor's published one, Kauers-Moosbauer's published
one, RL-054 seed 8) have pairwise different factor-rank invariants and are therefore pairwise inequivalent. No new
rank-47 4×4×4 scheme was found in this round. The new (3,4,5) rank-47 scheme was not compared with the published
ones (not needed for any claim).

## 6. Near-misses

* **(3,4,5):** four of eight walks ended at 48, one above the best known 47, after 180 s; one reached 47 (97.2 s).
* **(3,4,4):** two of eight walks ended at 39, one above 38, after 60 s (the other six reached 38 in 1.0-54.0 s).
* **(4,4,5):** best 64 (seeds 1, 2, 6), four above the GF(2) best known 60 and one above AlphaTensor's 63, after 180 s.
* **4×4×4 from the standard algorithm:** 20 of 24 walks ended at 49, two above 47; no walk reached 48. The
  diagnostic of section 4 (dead ends with 0 flippable pairs, Strassen ⊗ Strassen-like invariant) explains much of
  the stall, but is not a proof that those walks could never have left.
* **4×4×4 from rank 47:** no walk went below 47 in 2.825·10¹⁰ steps; the walks never got more than 3 above it.

## 7. Decision log

* **D1 – 4×4 budget: 24 fresh seeds × 900 s, 8 at a time (3 rounds, 45 min).** Alternatives: 16 × 1800 s (RL-054's
  walk length; 60 min, the whole budget, nothing left for the other formats); 48 × 450 s (more samples, but the only
  known hit, RL-054 seed 8, needed 726.7 s, so most 450 s walks would be censored before the interesting time);
  8 × 2700 s (no statistic). Deciding evidence: the single RL-054 hit at 726.7 s and the 60-minute cap.
* **D2 – fresh seeds (101-124), no replay of RL-054 seed 8.** A replay tests determinism, not frequency, and
  would cost at least 727 s of one slot. Mixing it in would also bias the count.
* **D3 – no weight cap for 4×4.** RL-054: all four cap-4 walks stuck at 52, while uncapped walks reached 49, 49, 50
  and 47.
* **D4 – target rank 0 for the 4×4 statistic.** A walk that reaches 47 keeps walking, so the same run measures the
  time to 47 and is also the main rank-46 attempt. Alternative: stop at 47 and restart new seeds (more samples per
  minute), rejected because the 46 attempt then needs separate budget.
* **D5 – the optional kernel throughput work (task item 4) was not done.** `rust_kernel.build()` rebuilds the
  binary whenever `flipwalk.rs` changes, so editing the kernel during the campaign would have rebuilt it under
  running walks (on Windows the overwrite of a running .exe fails, so the next job would have crashed) or mixed two
  kernels in one statistic. Benchmarking it would also need walk processes beyond the cap of 8. Ideas are in
  section 8.
* **D6 – how the GF(2) best-known ranks were established.** A catalogue value alone does not say whether a
  scheme is valid in characteristic 2 (Sedoglavic's page does not mark it). So: (a) published scheme files were
  downloaded and verified with our own verifiers, which proves existence at that rank over GF(2) and over Z;
  (b) the MMC, which lists fields per scheme, gave the F2 minima; (c) the general-ring values come from the
  catalogue, cross-checked against the MMC and, for 4×4, against two abstracts.
* **D7 – small formats: target rank = best known − 1, 8 seeds, 30/60/180 s.** Every walk then uses its full
  budget and keeps trying to go below the best known rank. The first time it reached the best known rank is in
  the kernel's IMPROVED lines, so no separate run was needed. Budgets were scaled with the format size so that the
  ten formats fit in about 12 minutes.
* **D8 – the dedicated rank-46 attempt starts from our own rank-47 scheme (RL-054 seed 8), not from the published
  Kauers-Moosbauer scheme.** It is a file whose provenance is in the repository. The flips repository carries a
  GPL-3 notice for its program and states no license for its data, so no third-party scheme file was copied into
  the repository; the published file is only downloaded at run time for verification and for the invariant
  comparison (section 5).
* **D9 – time budgets, not step budgets.** This keeps the runs comparable with RL-054. Throughput depends on machine
  load, so steps are reported next to seconds; steps are the machine-independent measure.
* **D10 – the rank-46 attempt was redesigned before launch, on evidence from the 4×4 run.** The first version used
  plateau 50 000 for all 8 walks. The endpoint diagnostics (section 4) then showed that the start scheme, like the
  stalled rank-49 endpoints, has 0 flippable pairs, so with plateau 50 000 almost every step is idle. The launcher
  was changed (before it ran) to 4 walks with plateau 50 000 (comparable with everything else) and 4 with plateau
  5 000 (ten times more plus transitions). Alternative considered: all 8 at plateau 5 000 (more search, but no
  comparison). The kernel was not changed, only a command-line parameter.

## 8. Open ideas

1. **Kernel throughput (task item 4, not done here; D5).** Every step scans all r terms for partners sharing the
   chosen factor (`cands`), and draws two random numbers with a `%` (an integer division). Untested candidates:
   (a) structure-of-arrays storage plus a count-then-select scan (count the matches in one branch-free pass; only
   if the count is non-zero, draw an index and find that match). This keeps the exact same random draws and
   candidate order, so the trajectories stay bit-identical and the differential test needs no new semantics;
   (b) a hash index from factor value to term indices, which avoids the O(r) scan but must be kept consistent
   under removals and index shifts, so it is riskier; (c) Lemire's multiply-shift instead of `%`, which changes
   every trajectory and must be mirrored in `search/kernel_reference.py`. Each needs a benchmark on an idle machine
   and the branch-coverage check of RL-052.
2. **Dead-end handling (the strongest lead from this round).** 19 of 20 stalled 4×4 walks sat at a rank-49 scheme
   with 0 flippable pairs, where about 99.9% of the steps do nothing (section 4). Two cheap changes: (a) detect a
   dead end (no term pair shares a factor; checkable in O(r²) once, or by counting failed proposals) and do a plus
   transition or a restart at once instead of waiting 50 000 steps; (b) restart from the standard algorithm (or
   from a random point of a rank-52-55 plateau) when a walk is stuck at a Strassen ⊗ Strassen-like dead end,
   since reaching 49 takes a median of 13.8 s but leaving it never happened in 20 walks × up to 900 s. Both change
   the trajectories, so they need the mirror in `search/kernel_reference.py`, the differential test and a coverage
   check (RL-052). The from-47 comparison of plateau 50 000 vs 5 000 (section 3) is a first, parameter-only probe.
3. **Rank 46 from many rank-47 starts.** Walks from the three mutually inequivalent rank-47 schemes now verified
   (AlphaTensor's, Kauers-Moosbauer's, RL-054 seed 8), with longer budgets than the 8 × 120 s tried here, and with
   the dead-end handling of idea 2 (the RL-054 scheme is itself a dead end with 0 flippable pairs). A walk cannot prove that 46 is impossible; the null result
   stays a statement about the search.
4. **Full equivalence test for rank-47 schemes.** The factor-rank invariant separates some schemes; a canonical
   form under GL(4,2)³ ⋊ S₃ would decide equivalence completely and tell whether the walks keep finding the same
   few classes.
5. **(4,4,5) over GF(2).** The best known rank is 60 (Kauers & Moosbauer); 180 s walks from the standard algorithm
   reached 64. Starting from AlphaTensor's verified rank-63 scheme, or from a rank-47 (4,4,4) scheme plus the 16
   products of a (4,4,1) block (rank 63), is a cheaper start than the standard algorithm.
6. **Dataset (unchanged from RL-054):** a characteristic-2 entry "Strassen recursion vs recursive rank-47 4×4
   scheme", V2 on exact multiplication counts, now backed by three pairwise inequivalent verified rank-47 schemes
   (AlphaTensor's and Kauers-Moosbauer's published ones, re-verified here, and RL-054's).

## 9. Reproduction

From the repository root (`./.venv/Scripts/python` on this machine):

```
python experiments/2026-10-07b_sources.py          # section 2 (network: Crossref, GitHub raw, the two catalogues)
python experiments/2026-10-07b_4x4_nocap_stats.py  # 24 walks x 900 s, 8 at a time (about 45 min)
python experiments/2026-10-07b_small_formats.py    # 10 formats x 8 seeds (about 12 min)
python experiments/2026-10-07b_4x4_from47.py       # 8 walks x 120 s from the RL-054 rank-47 scheme
python experiments/2026-10-07b_analysis.py         # sections 3-5 from the logs; re-verifies every saved scheme
```

Logs: `search/runs/2026-10-07b_4x4_nocap.jsonl`, `search/runs/2026-10-07b_small_<n>x<m>x<p>.jsonl`,
`search/runs/2026-10-07b_4x4_from47.jsonl`, plus the console copies `search/runs/2026-10-07b_*.console.txt`.
Schemes: `search/schemes/rust-2026-10-07b/` (from the standard algorithm) and `search/schemes/rust-2026-10-07b/from47/`.
Walks are deterministic in steps for a given seed and kernel; because the budgets are in seconds, the end point of a
rerun (and therefore the last improvements of a walk) can differ.
