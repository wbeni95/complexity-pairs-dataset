# Below the best known rank in less-explored formats? Records, target choice, calibration and a targeted search

Date: 2026-10-06 (work about 14:05-16:40 local time). Follows RL-036, RL-052, RL-054, RL-059, RL-070-RL-074.
Author: delegated research agent (Claude), for the maintainer. Every number below comes from a script or command
recorded here, or from a source whose identifier or content was checked (labels as in research/2026-10-07_patterns.md:
[DOI OK], [arXiv id OK], [recalled]). A rediscovery of a known rank is a pipeline check, nothing more.

## Summary

* **Nothing below a best known rank was found.** Calibrated NULL over GF(2) for (2,4,5) at 32, (3,3,6) at ≤ 41,
  (2,5,6) at ≤ 46 and (4,4,5) at ≤ 59, in 160 walks, 3.89·10¹¹ steps and 24 000 walk-seconds over the round's calibration, target and follow-up arms (per format: (2,4,5) 32 walks, 3.96·10¹⁰ steps; (3,3,6) 28, 1.08·10¹¹; (2,5,6) 20, 6.46·10¹⁰; (4,4,5) 32, 1.09·10¹¹; (3,4,5) 48, 6.76·10¹⁰; the best rank reached in each format equals its GF(2) record or is above it) (scope per arm in section 5). No contact, no publication, no novelty
  claim.
* **Records table (section 2)** for all 35 formats 2 ≤ n ≤ m ≤ p ≤ 6, over GF(2) and over general rings, with sources:
  372 published scheme files (Kauers-Moosbauer 37, Kauers' meta-flip-graph repository 309, Arai-Ichikawa-Hukushima 2,
  Moosbauer-Poole 4, AlphaTensor 20) were parsed and **all verify over GF(2)** with our exact verifiers; catalogue values
  (Sedoglavic, MMC, Perminov) are listed as claims. GF(2) is ahead of the general rings in (4,4,4) 47/48, (4,4,5) 60/61
  and (4,5,5) 73/76, and behind in **(2,4,5) 33/32**, **(3,3,6) 42/40** and (3,6,6) 82/80. The general-ring records of
  (2,4,5) and (3,3,6) verify over Q but have denominators 2 and 8 and do **not** reduce to GF(2) as they stand (2.3).
* **Targets (section 3):** (3,3,6) → ≤ 41 (rank 41 would give ω = 2.7929 < log₂7), (2,4,5) → 32 (a format record only;
  r* = 31), (2,5,6) → 46 (ω = 2.8053), (4,4,5) → 59 (ω = 2.7915). None would beat log₄47 = 2.7773 in characteristic 2. *(Maintainer correction, RL-083: three exponents written by hand were recomputed as 3·ln r / ln(nmp): 2.8020 → 2.8053, 2.7917 → 2.7915, 2.8186 → 2.8185; no conclusion changes.)*
* **Our own gap (section 4):** two method changes, both mirrored in `search/kernel_reference.py` or tested directly
  (differential tests, planted-dependency tests, 14/14 identity with the pre-round kernel):
  * **block starts** (direct sums of verified smaller schemes): **(4,4,5) went from 0/8 walks at the record (RL-059,
    best 64) to 6/24 walks reaching the record 60** (2/16 in the 180-s calibration, 4/8 in the 240-s target arm). The six
    rank-60 schemes are VERIFIED rediscoveries (both exact verifiers, 200 random checks; not valid over Z as they stand);
    their factor-rank profiles differ from each other and from Kauers-Moosbauer's published file, so they are pairwise
    inequivalent under the symmetry group. (3,4,5): record 47 in 1/8 walks before and 0/24 with block starts, but
    record + 1 in 23/24 against 12/24 from the standard start (Fisher p = 0.0007).
  * **linear-dependence reduction** (`--full-reduce`, default off): exact and tested, but no measurable benefit and
    0.46-0.81 of the plain kernel's speed; not used for the targets.
* **Measured obstacle:** for (2,5,6) the default walk policy (plateau 50 000, slack 3) never improved on the standard
  algorithm (60) or the block start (50); the pre-round kernel behaves identically. With plateau 2 000 and slack 1 the
  walks improve at once (section 6), but the 300-s follow-ups with that policy still ended far above the records ((2,5,6): best 51; (3,3,6): best 44).
* Search compute: about 106 minutes (14:38-16:26, sequential jobs, plus about 4 minutes of single-process identity checks) of wall clock, never more than 4 walk processes, all at below-normal priority.

## 1. Setup

* Machine: Windows 11, 16 logical CPUs, CPython 3.14.2, rustc (single-file builds). Shared with three other agents;
  at most 4 walk processes at a time, all at below-normal priority (search/rust_kernel.py), every search job in the
  background with a time budget, no job longer than 20 minutes.
* Kernel at the start of the round: `search/kernel/flipwalk.rs`, SHA-256 `69837abe…0f550` (the kernel of RL-072),
  copied verbatim to `experiments/2026-10-06d_flipwalk_before.rs`. Kernel after this round: SHA-256 `6933efaf…6e00` (an intermediate version
  `8e31926b…257d` ran the first four (3,4,5) calibration arms; section 8, item 2).
* Network, 19 requests in all: GitHub API 7 (repository metadata, latest commit of five repositories, one tree), 4
  archive downloads, 4 raw files and 2 raw requests that returned 404 (section 8); fmm.univ-lille.fr 1; solven.eu 1.
  AlphaTensor's file was copied from the RL-071 cache (same SHA-256), not downloaded again. No request to the Linz server (algebra.uni-linz.ac.at) and no arXiv or Crossref request
  in this round. Cache outside the repository (`$FMT_CACHE`, here `<scratchpad>/c6d`), keyed by sha1(URL); one
  connection, at least 1.5 s between requests, User-Agent "complexity-pairs-dataset research agent
  (https://github.com/wbeni95/complexity-pairs-dataset)". No third-party scheme file was added to the repository.

## 2. Records table

Script: `experiments/2026-10-06d_fmt_records.py` (console copy `search/runs/2026-10-06d_records.console.txt`, all data
`search/runs/2026-10-06d_records.json`), plus `experiments/2026-10-06d_fmt_char0_records.py` (section 2.3; console
`search/runs/2026-10-06d_char0_records.console.txt`). Scope: all 35 formats 2 ≤ n ≤ m ≤ p ≤ 6 (every one fits the
kernel's u64 factors: nm, mp, pn ≤ 36). Rank is invariant under permuting (n, m, p), so one row covers all six
orderings.

### 2.1 Sources and what was checked

| Id | Source (pinned version) | What was done here |
|---|---|---|
| KM | Kauers & Moosbauer, flip graphs (ISSAC 2023, doi:10.1145/3597066.3597120 [DOI OK in RL-059]); data github.com/jakobmoosbauer/flips @ `e31a0a0f` (2025-12-09), archive SHA-256 `36c64abe…` | all 37 in-range `solutions/*.exp` parsed; **37/37 verify over GF(2)** (`gf2mm.verify`, plus `verify_explicit` when nmp ≤ 100); mod0 files also verified exactly over Q |
| KW | Kauers (and Wood), meta flip graphs, github.com/mkauers/matrix-multiplication @ `12c26b29` (2026-05-29), archive SHA-256 `44f701c0…` | the 309 in-range files (formats 346, 446, 456, 466, 556, 566) parsed; **309/309 reduce to valid GF(2) schemes**; 91 are also valid over Q, 218 are valid only in characteristic 2 (they fail the exact check over Q) |
| AIH | Arai, Ichikawa & Hukushima, adaptive flip graphs (arXiv:2312.16960 [arXiv id OK in RL-059]); github.com/Yamato-Arai/adap @ `fe7b2040` | `455_73.m`, `555_94.m`: **2/2 verify over GF(2)** |
| MP | Moosbauer & Poole, flip graphs with symmetry (arXiv:2502.04514 [arXiv id OK]); github.com/jakobmoosbauer/symmetric-flips @ `3e2d4dd8` | `555m93`, `666m153` and their lifted versions: **4/4 verify over GF(2)**; the lifted ones also over Q |
| AT | AlphaTensor (doi:10.1038/s41586-022-05172-4 [DOI OK]), `factorizations_f2.npz` @ `1949163d`, SHA-256 `70f09f34…` (from the RL-071 cache) | all 20 GF(2) factorizations (all in range) verify (parser of `experiments/2026-10-07b_sources.py`) |
| CAT | Sedoglavic's catalogue, https://fmm.univ-lille.fr/ (downloaded 2026-10-06 14:26, SHA-256 `d16e4a79…`) | best rank and cited reference per format (31 of 35 formats have a row; (2,2,3)-(2,2,6) have none); general rings |
| MMC | Matrix Multiplication Catalog, https://solven.eu/matmulcatalog/catalog.json (14:26, SHA-256 `475c05d2…`, identical to the RL-071 copy) | minimum rank per field (F2, Z, Q) over non-commutative schemes; claims, not re-verified |
| PER | Perminov, github.com/dronperminov/FastMatrixMultiplication @ `64f58a5e` (2026-10-02), `schemes/status.json`, SHA-256 `c7fbeb5e…` | best ZT / Z / Q rank per format; claims, not re-verified. Integer (Z, ZT) schemes are valid over every commutative ring, so they are also GF(2) upper bounds |
| AE | AlphaEvolve's (2,5,6) rank-47 scheme as collected by PER (`schemes/known/alpha_evolve/2x5x6_m47_mod0.json`, SHA-256 `d8b8e9b5…`) | valid over Q, integer coefficients; reduced mod 2 it **verifies over GF(2)** (both verifiers), section 2.3 |

Lower bounds: the flattening bound max(nm, mp, pn) holds over every field and is computed. Better bounds are listed
only where recalled and are labelled [recalled]: 7 for (2,2,2) (Winograd 1971; Hopcroft-Kerr 1971; over GF(2) also our
exhaustive check, RL-036), 11 for (2,2,3) (Alekseyev 1985), 14 for (2,2,4) (Alekseev-Smirnov 2013), 19 for (3,3,3)
(Bläser 2003, doi:10.1016/S0885-064X(02)00007-9 [DOI OK in research/2026-10-07_patterns.md]) and (5/2)n² − 3n for
n×n (Bläser 1999, doi:10.1109/SFFCS.1999.814576 [title OK there], lower-order term recalled): 28, 48, 72 for n = 4, 5, 6.
In addition, the Crossref abstract of Hopcroft & Kerr 1971 (doi:10.1137/0120004 [DOI OK], quoted in
research/2026-10-07_search_flipgraph.md) states that their algorithm for p×2 by 2×n is minimal for p ≤ 2 and for
p = n = 3, which would make (2,2,n) (ranks 11, 14, 18, 21) and (2,3,3) (rank 15) optimal; the abstract does not name the
ground ring, so this is not claimed for GF(2). For every target format of section 3 the gap between the best known
rank and the best lower bound we have is large (flattening bound 18-30 against ranks 33-60).

### 2.2 The table

Columns: **GF(2) best** = the lowest rank of a scheme valid over GF(2) in the sources (verified files, the MMC's F2
minimum, and integer-coefficient schemes of PER/MMC, which reduce mod 2). **verified here** = lowest rank among the
files verified over GF(2) in this round. **general best** = lowest rank over any ring in CAT, PER, MMC or the files
verified over Q. **r*** = the largest rank whose exponent 3·ln r / ln(nmp) is below log₂7 = 2.80735, i.e. the rank a
scheme must reach to beat Strassen's exponent when used recursively (through the symmetrisation
(n,m,p)⊗(m,p,n)⊗(p,n,m), an nmp × nmp scheme of rank r³). **ω(GF(2) best)** = 3·ln r / ln(nmp) at the GF(2) best rank.

| format | naive | GF(2) best | verified here (sources) | MMC F2 | general best | CAT (cited) | PER Q/Z/ZT | lower bound: flattening; better | r* | ω(GF(2) best) |
|---|---|---|---|---|---|---|---|---|---|---|
| (2,2,2) | 8 | **7** | 7 (AT) | 7 | **7** | 7 (Strassen 1969) | 7/7/7 | 4; 7 [recalled] | 6 | 2.8074 |
| (2,2,3) | 12 | **11** | 11 (AT, KM) | 11 | **11** | no row | 11/11/11 | 6; 11 [recalled] | 10 | 2.8950 |
| (2,2,4) | 16 | **14** | 14 (AT, KM) | 14 | **14** | no row | 14/14/14 | 8; 14 [recalled] | 13 | 2.8555 |
| (2,2,5) | 20 | **18** | 18 (AT, KM) | 18 | **18** | no row | 18/18/18 | 10 | 16 | 2.8945 |
| (2,2,6) | 24 | **21** | 21 (KM) | 21 | **21** | no row | 21/21/21 | 12 | 19 | 2.8739 |
| (2,3,3) | 18 | **15** | 15 (AT, KM) | 15 | **15** | 15 (Hopcroft and Kerr 1971) | 15/15/15 | 9 | 14 | 2.8108 |
| (2,3,4) | 24 | **20** | 20 (AT, KM) | 20 | **20** | 20 (Hopcroft and Kerr 1971) | 20/20/20 | 12 | 19 | 2.8279 |
| (2,3,5) | 30 | **25** | 25 (AT, KM) | 25 | **25** | 25 (Hopcroft and Kerr 1971) | 25/25/25 | 15 | 24 | 2.8392 |
| (2,3,6) | 36 | **30** | 30 (KM) | 30 | **30** | 30 (<1×1×2:2> ⊗ <2×3×3:15>) | 30/30/30 | 18 | 28 | 2.8474 |
| (2,4,4) | 32 | **26** | 26 (AT, KM) | 26 | **26** | 26 (Hopcroft and Kerr 1971) | 26/26/26 | 16 | 25 | 2.8203 |
| (2,4,5) | 40 | **33** | 33 (AT, KM) | 33 | **32** | 32 (AlphaEvolve 2025) | 32/33/33 | 20 | 31 | 2.8436 |
| (2,4,6) | 48 | **39** | 39 (KM) | 39 | **39** | 39 (Hopcroft and Kerr 1971) | 39/39/39 | 24 | 37 | 2.8391 |
| (2,5,5) | 50 | **40** | 40 (AT, KM) | 40 | **40** | 40 (Hopcroft and Kerr 1971) | 40/40/40 | 25 | 38 | 2.8289 |
| (2,5,6) | 60 | **47** | 47 (AE, section 2.3); 48 (KM) | 47 | **47** | 47 (AlphaEvolve 2025) | 47/47/47 | 30 | 46 | 2.8211 |
| (2,6,6) | 72 | **56** | 56 (KM) | 56 | **56** | 56 (Kauers and Moosbauer 2023) | 56/56/56 | 36 | 54 | 2.8237 |
| (3,3,3) | 27 | **23** | 23 (AT) | 23 | **23** | 23 (Laderman 1976) | 23/23/23 | 9; 19 [recalled] | 21 | 2.8540 |
| (3,3,4) | 36 | **29** | 29 (AT, KM) | 29 | **29** | 29 (Smirnov 2013) | 29/29/29 | 12 | 28 | 2.8190 |
| (3,3,5) | 45 | **36** | 36 (AT, KM) | 36 | **36** | 36 (Smirnov 2013) | 36/36/36 | 15 | 35 | 2.8241 |
| (3,3,6) | 54 | **42** | 42 (KM) | 42 | **40** | 40 (Smirnov 2013) | 40/42/42 | 18 | 41 | 2.8110 |
| (3,4,4) | 48 | **38** | 38 (AT, KM) | 38 | **38** | 38 (Smirnov 2013) | 38/38/38 | 16 | 37 | 2.8190 |
| (3,4,5) | 60 | **47** | 47 (AT, KM) | 47 | **47** | 47 (Fawzi et al. 2022) | 47/47/47 | 20 | 46 | 2.8211 |
| (3,4,6) | 72 | **54** | 54 (KW) | 54 | **54** | 54 (AlphaEvolve 2025) | 54/54/54 | 24 | 54 | 2.7982 |
| (3,5,5) | 75 | **58** | 58 (AT, KM) | 58 | **58** | 58 (Sedoglavic and Smirnov 2021) | 58/58/58 | 25 | 56 | 2.8214 |
| (3,5,6) | 90 | **68** | 71 (KM) | 68 | **68** | 68 (AlphaEvolve 2025) | 68/68/68 | 30 | 67 | 2.8131 |
| (3,6,6) | 108 | **82** | 86 (KM) | 82 | **80** | 80 (<1×2×1:2> ⊗ <3×3×6:40>) | 80/82/82 | 36 | 79 | 2.8235 |
| (4,4,4) | 64 | **47** | 47 (AT, KM) | 47 | **48** | 48 (AlphaEvolve 2025) | 48/49/49 | 16; 28 [recalled] | 48 | 2.7773 |
| (4,4,5) | 80 | **60** | 60 (KM) | 60 | **61** | 61 (AlphaEvolve 2025) | 61/61/61 | 20 | 60 | 2.8030 |
| (4,4,6) | 96 | **73** | 73 (KW) | 73 | **73** | 73 (Smirnov 2023) | 73/73/73 | 24 | 71 | 2.8200 |
| (4,5,5) | 100 | **73** | 73 (AIH) | 76 | **76** | 76 (Fawzi et al. 2022) | 76/76/76 | 25 | 74 | 2.7950 |
| (4,5,6) | 120 | **90** | 90 (KW) | 90 | **90** | 90 (Kauers and Wood 2025) | 90/90/90 | 30 | 88 | 2.8197 |
| (4,6,6) | 144 | **105** | 106 (KW) | 105 | **105** | 105 (<2×2×2:7> ⊗ <2×3×3:15>) | 105/105/105 | 36 | 104 | 2.8093 |
| (5,5,5) | 125 | **93** | 93 (MP) | 93 | **93** | 93 (Moosbauer and Poole 2025) | 93/93/93 | 25; 48 [recalled] | 91 | 2.8163 |
| (5,5,6) | 150 | **110** | 110 (KW) | 110 | **110** | 110 (Kauers and Wood 2025) | 110/110/110 | 30 | 108 | 2.8143 |
| (5,6,6) | 180 | **130** | 130 (KW) | 130 | **130** | 130 (Kauers and Wood 2025) | 130/130/130 | 36 | 128 | 2.8120 |
| (6,6,6) | 216 | **153** | 153 (MP) | 153 | **153** | 153 (Moosbauer and Poole 2025) | 153/153/153 | 36; 72 [recalled] | 152 | 2.8075 |
Observations (all from the script output):
* **GF(2) below the general rings** in three formats: (4,4,4) 47 vs 48, (4,4,5) 60 vs 61, (4,5,5) 73 vs 76. These are
  the formats on which the characteristic-2 work concentrated (AlphaTensor, KM, AIH).
* **General rings below GF(2)** in three formats: **(2,4,5)** 32 vs 33, **(3,3,6)** 40 vs 42 and (3,6,6) 80 vs 82. The
  (3,6,6) value 80 is CAT's construction ⟨1×2×1:2⟩ ⊗ ⟨3×3×6:40⟩, so it rests on the (3,3,6) record.
* **Our verified GF(2) files lag the GF(2) best** in (2,5,6) (48 vs 47; closed by AE, section 2.3), (3,5,6) (71 vs 68;
  AlphaEvolve's 68 is an integer scheme per PER and the MMC, not re-verified here), (3,6,6) (86 vs 82) and (4,6,6) (106 vs
  105; 105 = Strassen ⊗ (2,3,3) rank 15, constructed and verified in section 2.3).
* Already beating Strassen's exponent at the GF(2) best (ω < 2.80735): (4,4,4) 2.7773, (4,5,5) 2.7950, (3,4,6) 2.7982,
  (4,4,5) 2.8030. (6,6,6) at 153 gives 2.8075, just above.
* Source oddity: KM's file `366-85-mod2.exp` contains **86** distinct terms (it verifies over GF(2) at rank 86); the
  rank 85 in its name is not what the file holds. The MMC's F2 minimum for (4,5,5) is 76, so the MMC does not hold
  AIH's 73.
* Nothing in these sources is below the values of RL-059 for the 11 formats checked there.

### 2.3 Are the general-ring records usable over GF(2) as they stand?

`experiments/2026-10-06d_fmt_char0_records.py`, on the files PER names as the sources of its records:
* **(2,4,5) rank 32** (CAT cites AlphaEvolve 2025): valid over Q; denominators {1, 2}; **not 2-integral as it stands**
  (after rescaling each factor by a power of 2, some term keeps a negative 2-adic valuation), so it gives no GF(2) scheme.
* **(3,3,6) rank 40** (CAT cites Smirnov 2013, doi:10.1134/S0965542513120129 [DOI OK in RL-059]): valid over Q;
  denominators {1, 8}; **not 2-integral as it stands**.
* **(2,5,6) rank 47** (AlphaEvolve): valid over Q, integer coefficients; reduced mod 2 it is a valid GF(2) scheme of rank
  47 (`verify` and `verify_explicit`).
* Constructions: Strassen ⊗ our (2,3,3) rank-15 scheme = (4,6,6) rank 105, and ⟨1,1,2:2⟩ ⊗ (2,3,3):15 = (2,3,6) rank 30;
  both verify over GF(2).

"Not 2-integral as it stands" does not exclude an equivalent scheme (another basis) that is 2-integral, and says
nothing about whether a GF(2) scheme of that rank exists. It does say that these general-ring records do not transfer
to GF(2) by reduction mod 2, so over GF(2) the two formats are open at ranks 32 and 40-41 as far as these sources go.

## 3. Target selection

### 3.1 Criteria and ranking

A target is worth search time here if (i) its GF(2) record is plausibly not exhausted, (ii) it sits in the kernel's
size range (records reached from scratch so far: rank ≤ 47, nmp ≤ 60, RL-059), and (iii) the gap to the lower bound
leaves room (true for every format in the table). Asymptotic value is reported separately (column r*).

| rank | format | GF(2) best → target | why (evidence) | size | asymptotic value of the target |
|---|---|---|---|---|---|
| 1 | **(3,3,6)** | 42 → ≤ 41 | the largest GF(2)-vs-Q gap among the small formats (Q 40, Smirnov 2013; not 2-integral as it stands, section 2.3); GF(2) searched by KM (their 42 is a characteristic-2 file) but not reported by later GF(2) work in the sources | rank 42, nmp 54: sweet spot | 41 = r*: rank 41 gives ω = 2.7929 < log₂7 (beats Strassen in characteristic 2; not log₄47 = 2.7773) |
| 2 | **(2,4,5)** | 33 → 32 | Q record 32 (AlphaEvolve 2025) has denominators 2 (section 2.3); GF(2) 33 from AlphaTensor and KM, both before 2025 | rank 33, nmp 40: very cheap | record only: r* = 31; 32 gives ω = 2.8185 |
| 3 | **(2,5,6)** | 47 → 46 | GF(2) flip-graph file (KM) 48; the 47 came from AlphaEvolve (characteristic 0, integer); GF(2) searches before 2025 did not reach 47 | rank 47, nmp 60: sweet spot | 46 = r*: ω = 2.8053 < log₂7 |
| 4 | (4,4,5) | 60 → 59 | calibration format of this round; GF(2) record by KM, characteristic 2 only | rank 60, nmp 80: above the sweet spot (our best from scratch: 64) | 59: ω = 2.7915 (60 already beats log₂7) |
| – | (3,6,6) | 82 → 81 | Q 80 rests on (3,3,6):40; a GF(2) (3,3,6) of rank ≤ 41 gives (3,6,6) ≤ 82 via ⟨1,2,1:2⟩⊗ only, so (3,6,6) is covered by target 1 only at rank 40 | rank 82: too large | 79 = r* |
| – | (4,4,4), (4,5,5), (5,5,5), (6,6,6) | – | the most intensely searched characteristic-2 formats (AlphaTensor, KM, AIH, MP, the 99 129-file collection of RL-071) | large | (4,4,4) 46 would give ω = 2.7618 |
| – | (2,2,n), (2,3,3) | – | optimal by the Hopcroft-Kerr abstract (ground ring not named) | | |

### 3.2 Decision log for the target choice

* **D1 – Formats where a general-ring record does not transfer to GF(2) come first.** Alternatives: formats where GF(2)
  is already ahead ((4,4,4), (4,4,5), (4,5,5)), or the largest formats. Evidence: section 2.3 shows that the Q records of
  (2,4,5) and (3,3,6) need denominators 2 and 8; nobody's GF(2) collection in the sources reaches them. The GF(2)-ahead
  formats are exactly those where characteristic-2 search has been concentrated (AlphaTensor, KM, AIH, MP).
* **D2 – Stay in the kernel's size range.** Alternatives: (3,6,6), (4,6,6), (5,6,6) (ranks 82-130), which are "exotic"
  in the sense of the suggestion. Evidence: from scratch the kernel reached the record in 1/8 walks for (3,4,5) (rank 47)
  and never for (4,4,5) (rank 60) in RL-059; a target at rank ≥ 80 cannot be calibrated in this round.
* **D3 – (2,5,6) as the third target**, although its record (47) is a characteristic-0 result that happens to be integral.
  Evidence: KM's GF(2) flip-graph file has 48 (verified here), so the published GF(2) flip-graph search stopped above
  the record there; 46 would beat Strassen's exponent.
* **D4 – (4,4,5) only as calibration plus one arm from the published 60.** Its record is a characteristic-2 flip-graph
  result, and our kernel could not reach 63 from scratch before this round.

## 4. Closing our own gap: two method changes and their calibration

### 4.1 What was changed, and why these two

**Diagnosis from the earlier rounds.** RL-059 and RL-072 showed two failure modes. In (4,4,4) most walks sink into
rank-49 dead ends of the Strassen ⊗ Strassen type and never leave (RL-059, RL-072). In the larger rectangular formats
the walks are still descending when the budget ends: (4,4,5) was at 64-66 after 180 s, (3,4,5) at 47-51 (RL-059
section 3.1). For the second mode two cheap levers were open: start lower, and stop missing reductions that are
already available.

**(a) Linear-dependence reduction (`flipwalk.rs --full-reduce 1`, default 0).** The kernel reduced only when two
terms share two factors. Kauers and Moosbauer's notion of a reduction is more general [recalled; their ISSAC 2023
paper, doi:10.1145/3597066.3597120, was not re-read in this round]: if the terms sharing a factor f in one position
have linearly dependent factors in a second position, x_g = Σ_{s∈S} x_s, then f⊗x_g⊗y_g = Σ_s f⊗x_s⊗y_g, and term g can
be removed after adding y_g to the third factor of every term s ∈ S. Over GF(2) two vectors are dependent only if they
are equal, so this adds something only for groups of three or more terms. The walk could find such a reduction by
a specific flip, but only if it draws that flip before other flips destroy the dependence. Implementation
(`dependency_reduction` in the kernel, line-by-line in `search/kernel_reference.py`): for every term the merge rule
leaves alone, each position p and each second position q, the group of terms sharing factor p is tested by Gaussian
elimination over GF(2) in index order (u64 vectors with a mask of the members combined); the first member whose vector
reduces to zero is removed. Deterministic, no random numbers; counter `dep_reductions` in the STATS line.

**(b) Block starts (`search/blocks.py`, `search/campaign.py`).** The best single split of one dimension into two smaller
formats, each realised by a verified scheme from the earlier rounds (our own rediscoveries in
`search/schemes/rust-2026-10-07b/`, `rust-2026-10-06c/`, `rust-2026-10-07/`, Strassen, and the standard algorithm where one
dimension is 1). Splitting n or p gives two independent products, splitting m gives C = A₁B₁ + A₂B₂; in all three
cases the index cube is partitioned, and every start is verified with both exact verifiers before use and saved in
`search/schemes/rust-2026-10-06d/starts/`. Format permutations use the cyclic map (a,b,c) → (b,c,a), whose bit
layouts already agree, and the transpose (a,b,c) → (bᵀ, aᵀ, cᵀ) for (n,m,p) → (p,m,n). Starts used: (3,4,5) rank 49 =
(3,4,2) + (3,4,3) (20 + 29); (4,4,5) rank 63 = (4,4,1) + (4,4,4) (16 + 47); (3,3,6) rank 44 = (3,3,2) + (3,3,4) (15 + 29);
(2,4,5) rank 34 = (2,4,1) + (2,4,4) (8 + 26); (2,5,6) rank 50 = (2,5,3) + (2,5,3) (25 + 25, after the library step).

Options considered and not taken (decision D5): Kronecker starts (none of the targets has a useful factorisation:
(3,3,6) = (3,3,3)⊗(1,1,2) gives 46 > 44; (4,4,5) has the prime factor 5); a symmetry-restricted walk (Moosbauer-Poole)
needs a different move set and its own mirror, too large for this round; changing the plus-transition or restart
policy (RL-072 measured that the escape policy is not the bottleneck for reaching 47 in (4,4,4)); longer plateaus
(RL-059 D10: changing the plateau ten-fold changed nothing visible).

### 4.2 Safety and tests

* **Mirror and differential tests.** `tests/test_search_rust.py::test_differential_full_reduce`: Rust and the mirror give
  identical best schemes, step counts, all counters (including `dep_reductions`) and improvement histories on 9
  configurations × 2 settings of the flag, covering (2,2,2), (2,2,3), (3,3,3), (2,3,4), a weight cap, slack 0 and a
  start with a planted dependent triple. The test asserts that `dep_reductions`, plus transitions, restarts and dead-end
  escapes are all exercised (> 0) with the flag on, and that `dep_reductions` = 0 with it off.
* **Invariant tests** (`tests/test_search_blocks.py`, 9 tests): a planted dependent triple (a 2×2×2 scheme of rank 9 in
  which no two terms share two factors) is removed only with the flag on, leaving a scheme of rank 8 that verifies;
  mirror walks with the flag stay valid and use the branch; the six format images, direct sums along each axis and
  block starts verify, a truncated direct sum is rejected by the verifier.
* **Identity with the pre-round kernel** (`experiments/2026-10-06d_fmt_identity.py`, console
  `search/runs/2026-10-06d_identity.console.txt`): with `--full-reduce 0` the new kernel's output equals the pre-round
  binary's (`experiments/2026-10-06d_flipwalk_before.rs`) in **14/14** step-limited cases ((2,2,2), (3,3,3), (3,4,5),
  (4,4,4); up to 3·10⁷ steps), apart from the extra `dep_reductions=0` field. So every earlier result stays
  reproducible with the current source.
* **Builds:** `rustc -O --edition 2021 -D warnings` and a debug build with `-C debug-assertions=on -C overflow-checks=on`
  both compile cleanly (scratch binaries, not kept).
* **Verification of results is unchanged:** every walk result passes `gf2mm.verify` and an 8-trial random check in
  `search/rust_kernel.py` before it is logged; `gf2mm.save_scheme` refuses unverified schemes.


### 4.3 Calibration: rate of reaching the best known rank, before and after

Script `experiments/2026-10-06d_fmt_calibrate.py` (plans 345, 345v2, 445); logs `search/runs/2026-10-06d_cal_3x4x5.jsonl`
and `…_cal_4x4x5.jsonl`; console copies `search/runs/2026-10-06d_cal_*.console.txt`; numbers recomputed by
`experiments/2026-10-06d_fmt_analysis.py` (console `search/runs/2026-10-06d_analysis.console.txt`). Same seeds 1-8 in
every arm, 4 walks at a time, no weight cap, plateau 50 000, slack 3, dead-end escape on. Intervals are exact
two-sided 95% Clopper-Pearson intervals.

**(3,4,5), best known GF(2) rank 47, 8 walks × 120 s per arm** (14:38:41-15:05:59):

| arm | start | full reduce | best rank per seed 1-8 | reached 47 | reached ≤ 48 (first times, s) | steps (all walks) | median flips/s |
|---|---|---|---|---|---|---|---|
| std_off (= before) | standard, 60 | off | 48, 48, 51, 51, 49, 48, **47**, 48 | **1/8** (0.003-0.527), at 81.4 s | 5/8 (22.1-110.3) | 1.80·10¹⁰ | 3.79·10⁶ |
| std_full | standard | on (first version) | 48, 48, 49, 50, 48, 53, 53, 52 | 0/8 (0-0.369) | 3/8 | 5.68·10⁹ | 1.21·10⁶ |
| std_full_v2 | standard | on (allocation-free) | 48, 48, 49, 49, 48, 52, 48, 51 | 0/8 (0-0.369) | 4/8 | 9.20·10⁹ | 1.76·10⁶ |
| blk_off | block, 49 | off | 48 × 8 | 0/8 (0-0.369) | **8/8** (7.0-53.7) | 1.58·10¹⁰ | 3.43·10⁶ |
| blk_full | block | on (first version) | 49, 48 × 7 | 0/8 (0-0.369) | 7/8 | 6.62·10⁹ | 1.29·10⁶ |
| blk_full_v2 | block | on (allocation-free) | 48 × 8 | 0/8 (0-0.369) | **8/8** (2.9-60.1) | 1.24·10¹⁰ | 2.44·10⁶ |

* The baseline reproduces RL-059 exactly: seeds 1-8 end at 48, 48, 51, 51, 49, 48, 47, 48 in both (another kernel
  version and machine load; the trajectories are deterministic per seed, RL-059).
* **Reaching the record: no improvement** (1/8 before; 0/40 in the five changed arms). The data cannot exclude a
  modest effect either way.
* **Reaching record + 1: block starts help.** ≤ 48 in 23/24 block-start walks against 12/24 standard-start walks
  (all three settings of the reduction pooled; two-sided Fisher exact test p = 0.0007 from `fmt_analysis.py`; the test
  function reproduces RL-072's p = 0.109 for 4/24 vs 0/24). The 8 rank-48 endpoints of `blk_off` have 8 different
  factor-rank profiles, so they are pairwise inequivalent (the format has three different dimensions, so its symmetry
  group consists of sandwiches and term permutations, which preserve each factor's rank): the walks do not fall into
  one basin, they spread over a plateau at 48 from which 47 is rare.
* **The linear-dependence reduction costs throughput and bought nothing measurable.** It fired 1.5-3.2·10⁴ times per
  arm (about one removal per 5·10⁴ flips). The first version allocated a vector on every group scan and ran at 0.33-0.46
  of the plain kernel's median steps/s; the allocation-free version (identical trajectories, section 8) still runs at
  0.46-0.81 of it on (3,4,5) and 0.60 on (4,4,5).

**(4,4,5), best known GF(2) rank 60, 8 walks × 180 s per arm** (15:05:59-15:18:01), block start of rank 63:

| arm | full reduce | best rank per seed 1-8 | reached 60 | reached ≤ 62 | steps | median flips/s |
|---|---|---|---|---|---|---|
| before: RL-059 (standard start, 180 s, kernel `6f306293…`) | off | 64, 64, 65, 66, 65, 64, 66, 66 | 0/8 (0-0.369) | 0/8 | – | – |
| blk_off | off | **60**, 63, 62, 62, 63, 62, 62, 63 | **1/8** (0.003-0.527), at 160.3 s | 5/8 | 2.40·10¹⁰ | 1.94·10⁶ |
| blk_full | on (allocation-free) | 62, 63, 63, 62, 62, 63, **60**, 63 | **1/8** (0.003-0.527), at 148.8 s | 4/8 | 1.43·10¹⁰ | 1.16·10⁶ |

* **Before → after: 0/8 → 2/16** walks reach the best known GF(2) rank 60 (pooled after: 0.016-0.384). The baseline is
  RL-059's run (another kernel version and another day's load, so the comparison is indicative, not a paired test).
  The block start alone (63) is already one below everything the kernel reached from scratch before (64).
* Both rank-60 walks came down 62 → 61 → 60 in one burst (seed 1 of blk_off: 61 at step 2 708 734 626, 60 at step
  2 708 797 727; seed 7 of blk_full: 61 → 60 within 4.4·10⁴ steps), the pattern RL-072 saw for 4×4×4 rank 47.
* **The two rank-60 schemes are VERIFIED rediscoveries of the best known GF(2) rank** (Kauers-Moosbauer 2023), not new
  records: `search/schemes/rust-2026-10-06d/cal/4x4x5_rank60_blk_off_seed1.json` and `…_blk_full_seed7.json` pass
  `verify`, `verify_explicit` and 200 random GF(2) matrix checks; neither is valid over Z as it stands. Their factor-rank
  profiles (multiset of sorted rank triples, invariant under sandwiches, term permutations and the symmetry
  (a,b,c) → (aᵀ, cᵀ, bᵀ) of (4,4,5)) differ from each other and from KM's published `445-60-mod2.exp`, so the three
  are pairwise inequivalent under that group. No other published rank-60 (4,4,5) GF(2) scheme was compared.

**Calibration summary.** Before: (3,4,5) 1/8, (4,4,5) 0/8 at the record. After (block starts): (3,4,5) 0/24 at the
record but 23/24 at record + 1; (4,4,5) 2/16 at the record. So the block start closes our (4,4,5) gap within 180 s
walks, while (3,4,5) shows that the last step to the record remains rare.

## 5. Targeted search

Script `experiments/2026-10-06d_fmt_targets.py` (plans 245, 336, 256, 445, after `library`); logs
`search/runs/2026-10-06d_tgt_<fmt>.jsonl`, console copies `…_tgt_<fmt>.console.txt`; kernel `6933efaf…`, plain mode
(`--full-reduce 0`, decision D7), no weight cap, plateau 50 000, slack 3, dead-end escape on, 4 walks at a time. Seeds
1001+, 2001+ and 3001+ for the first, second and third arm of each format, in the order of the table (so for (4,4,5)
the block-start walks have seeds 1001-1008); follow-ups 6001-6004.

**Library step (15:18:01-15:18:15):** 4 walks × ≤ 30 s each for (2,2,5), (2,3,5), (2,2,6), (2,3,6) with the target set to
the best known rank: **16/16 reached it** (18, 25, 21, 30) within 6.8 s (rediscoveries, pipeline checks); saved in
`search/schemes/rust-2026-10-06d/library/` and used for the (2,5,6) block start.

| format (GF(2) best → target) | arm | walks × s | start rank | best rank per walk | reached the record | below the record | steps | window |
|---|---|---|---|---|---|---|---|---|
| (2,4,5) (33 → 32) | std | 8 × 60 | 40 | 33 ×6, 39, 37 | 6/8 (0.349-0.968), 1.6-49.9 s | **0** | 7.89·10⁹ | 15:18:51-15:20:51 |
| | blk | 8 × 60 | 34 | 33 ×8 | 8/8 (0.631-1), ≤ 0.1 s | **0** | 1.07·10¹⁰ | 15:20:51-15:22:52 |
| | pub (KM `245-33-mod0`) | 16 × 60 | 33 | 33 ×16 | (start) | **0** | 2.10·10¹⁰ | 15:22:52-15:26:52 |
| (3,3,6) (42 → ≤ 41) | std | 8 × 180 | 54 | 43, 45 ×7 | 0/8 (0-0.369) | **0** | 2.25·10¹⁰ | 15:26:52-15:32:53 |
| | blk | 8 × 180 | 44 | 43 ×8 | 0/8 (0-0.369) | **0** | 3.01·10¹⁰ | 15:32:53-15:38:53 |
| | pub (KM `336-42-mod2`) | 8 × 180 | 42 | 42 ×8 | (start) | **0** | 3.65·10¹⁰ | 15:38:53-15:44:53 |
| (2,5,6) (47 → 46) | std | 4 × 180 | 60 | 60 ×4 (no improvement) | 0/4 (0-0.602) | **0** | 7.83·10⁹ | 15:44:54-15:47:54 |
| | blk | 4 × 180 | 50 | 50 ×4 (no improvement) | 0/4 (0-0.602) | **0** | 9.05·10⁹ | 15:47:54-15:50:54 |
| | pub (AlphaEvolve 47 mod 2) | 8 × 180 | 47 | 47 ×8 | (start) | **0** | 3.33·10¹⁰ | 15:50:54-15:56:55 |
| (4,4,5) (60 → 59) | blk | 8 × 240 | 63 | 60 ×4, 62 ×4 | **4/8** (0.157-0.843), 8.5-175.7 s | **0** | 3.07·10¹⁰ | 15:56:55-16:04:55 |
| | pub (KM `445-60-mod2`) | 4 × 240 | 60 | 60 ×4 | (start) | **0** | 1.87·10¹⁰ | 16:04:56-16:08:56 |
| | own60 (our calibration 60) | 4 × 240 | 60 | 60 ×4 | (start) | **0** | 2.15·10¹⁰ | 16:08:56-16:12:56 |
| (2,5,6) follow-up | std, plateau 2 000, slack 1 | 4 × 300 | 60 | 57, 51, 52, 59 | 0/4 (0-0.602) | **0** | 1.45·10¹⁰ | 16:15:57-16:20:57 |
| (3,3,6) follow-up | std, plateau 2 000, slack 1 | 4 × 300 | 54 | 44, 45, 45, 45 | 0/4 (0-0.602) | **0** | 1.87·10¹⁰ | 16:20:57-16:25:58 |

**Result: nothing below a best known rank. NULL** in this scope for (2,4,5) at 32, (3,3,6) at ≤ 41, (2,5,6) at ≤ 46 and
(4,4,5) at ≤ 59 (walks, steps and times in the table; in total 160 walks, 3.89·10¹¹ steps and 24 000 walk-seconds over the round's calibration, target and follow-up arms (per format: (2,4,5) 32 walks, 3.96·10¹⁰ steps; (3,3,6) 28, 1.08·10¹¹; (2,5,6) 20, 6.46·10¹⁰; (4,4,5) 32, 1.09·10¹¹; (3,4,5) 48, 6.76·10¹⁰; the best rank reached in each format equals its GF(2) record or is above it)). A null result says nothing about whether such
schemes exist (START_HERE section 6). Step 5 of the brief (full verification, Z test, Hensel lifting) was therefore not
triggered.

Per format:
* **(2,4,5).** The record 33 is easy for the kernel: 14/16 walks from our own starts reached it (the block start in
  ≤ 0.1 s), so the pipeline works here; 32 walks spent 1 920 walk-seconds (3.96·10¹⁰ steps) at or near 33 without
  finding 32. Two standard-start walks stayed at 39 and 37 with no restart for 40-50 s (a plateau trap; IDEA 5 in
  section 10).
* **(3,3,6).** Our own starts end one above the GF(2) record: 9/16 walks at **43** (all 8 block-start walks and one
  standard-start walk); the other 7 standard-start walks stopped at 45 within 11 s and stayed there for 170 s. The
  record 42 was not rediscovered from our own starts in this budget, and the walks from KM's 42 did not go below it.
* **(2,5,6).** The kernel made **no improvement at all** from the standard algorithm (60) or from the block start (50) in
  4 × 180 s each, although it flipped constantly (6.3·10⁸ flips per standard-start walk) and the block-start walks
  restarted 2 201 times. Walks from AlphaEvolve's 47 stayed at 47; that scheme admits few flips (1.5% of steps were
  flips, against 32% from the standard start). This is a measured obstacle of the walk, not a property of the format
  (KM's GF(2) search reached 48, and 47 exists); a diagnostic is in section 6.
* **(4,4,5).** The block start reproduced and strengthened the calibration: **4/8 walks reached the record 60**
  (first at 8.5, 107.8, 108.4 and 175.7 s; three of them within 180 s). In four of the six rank-60 walks of the round the
  step 61 → 60 took at most 6.3·10⁴ steps (a burst, as in RL-072); in walks 1005 and 1008 it took 1.8·10⁸ and 4.8·10⁸
  steps (11.0 and 29.5 s; `search/runs/2026-10-06d_tgt_4x4x5.jsonl`). With
  the calibration that is **6/24 block-start walks at the record**. The six rank-60 schemes and KM's published one have 7
  different factor-rank profiles, so all seven are pairwise inequivalent (`fmt_analysis.py`). The walks kept going
  after reaching 60 (up to 231 s each) and the 8 walks from the two rank-60 starts walked at 60 for 240 s each: none
  found 59.
* **Follow-ups with plateau 2 000, slack 1 (decision D12).** (2,5,6) from the standard algorithm now descends (57, 51, 52,
  59 after 300 s) but stays far above 47; (3,3,6) ends at 44, 45, 45, 45, no better than the default policy.

## 6. Near-misses and a measured obstacle

* **(3,3,6): 9 walks ended at 43, one above the GF(2) record 42** (all 8 block-start walks, one standard-start walk);
  the 9 rank-43 schemes have 9 different factor-rank profiles, so they are pairwise inequivalent. Our own starts never
  reached 42 in this budget.
* **(3,4,5): 23/24 block-start walks at 48, one above 47** (calibration); the rank-48 endpoints of each block-start arm
  have 8 different profiles out of 8. (The `blk_full` and `blk_full_v2` arms end at identical rank-48 schemes for
  seeds 2-8, as they must: identical trajectories, the faster version only walks further.)
* **(4,4,5):** of the 24 block-start walks (calibration and target arms), 6 reached the record 60, 11 ended at 62 and 7
  at 63; every walk that reached 61 went on to 60.
* **(2,5,6), measured obstacle of the walk policy, not of this round's change** (`experiments/2026-10-06d_fmt_256_probe.py`,
  console `search/runs/2026-10-06d_256_probe.console.txt`):
  * with the default policy (plateau 50 000, slack 3) the walks from the standard algorithm never went below 60 in
    2·10⁹ steps (target arm) — and the pre-round kernel behaves identically (2/2 step-limited runs of 2·10⁸ steps give
    identical output, 0 improvements, about 3 850 plus transitions each);
  * the same in the other orientation (6,2,5): 4/4 walks × 30 s stay at 60;
  * with **plateau 2 000 and slack 1**, 4/4 walks × 30 s improved at once (first improvement after 0.06-0.33 s) and
    ended at 58, 55, 56, 59.
  
  So for (2,5,6) the default plateau/slack lets the walk drift at ranks 60-63 without ever returning below the start;
  the follow-up with the tighter policy is in section 5: it descends (best 51 after 300 s) but stays far above 47.


## 7. Decision log (continued from section 3.2)

* **D5 – Two method changes: block starts and the linear-dependence reduction.** Alternatives: Kronecker starts, a
  symmetry-restricted walk, new plus-transition or restart policies, longer plateaus (section 4.1). Evidence: the
  RL-059 small-format table shows that walks in (3,4,5) and (4,4,5) are still descending when time runs out, so a lower
  start and missed reductions were the two levers that act on that failure mode; RL-072 had already shown that the
  escape policy is not what limits reaching 47 in (4,4,4).
* **D6 – Calibration formats (3,4,5) and (4,4,5), seeds 1-8, 4 arms × 8 × 120 s and 2 arms × 8 × 180 s.** (3,4,5) is the
  largest format whose record the kernel had reached (1/8 in RL-059), (4,4,5) the one it had not (best 64). The seeds of
  RL-059 were reused so that the baseline arm doubles as a reproduction (it matched exactly). 120 s instead of RL-059's
  180 s for (3,4,5) so that four arms fit in 16 minutes; RL-059's (3,4,5) walks gave the same best ranks at 180 s.
  Alternative: 16 seeds per arm (more power), rejected for the 2-hour search budget.
* **D7 – The linear-dependence reduction stays off for the targeted search.** Evidence: 0/40 at the record in the five
  changed (3,4,5) arms against 1/8 before, no gain at record + 1 attributable to it (blk_off 8/8, blk_full_v2 8/8),
  1/8 vs 1/8 on (4,4,5), and 0.46-0.81 of the plain kernel's steps/s. It stays in the kernel as an exact, tested option
  (default off, `--full-reduce 0` reproduces the pre-round kernel exactly).
* **D8 – Re-run the full-reduce arms after the throughput fix** (plan 345v2) rather than report only the handicapped
  first version. Evidence: the first version made 3.2·10⁸-1.2·10⁹ steps per walk against 1.7-2.7·10⁹ for the plain kernel;
  the fix gives identical trajectories (4/4 step-limited comparisons, section 8), so only speed changed.
* **D9 – The (4,4,5) targeted plan was changed after the calibration** from 8 walks from the published rank-60 scheme to
  8 block-start walks + 4 from the published 60 + 4 from our own calibration 60, 240 s each. Evidence: block starts
  reached 60 in 2/16 calibration walks, and the walks continue after reaching the record, so more block-start walks are
  both a replication of the calibration and more attempts at 59.
* **D10 – Each target gets three arms: standard start, block start, published record scheme.** The first two make any
  record-level result a rediscovery; the third is Kauers-Moosbauer's own protocol (walk at rank r, look for r − 1) and is
  the only arm that spends all its time at the record. Published starts are read from the cache at run time and never
  copied into the repository (as RL-059 D8); their walks' schemes are saved only if below the record.
* **D11 – No contact, no publication, no novelty wording.** Nothing went below a record (section 5), so step 5 of the brief
  was not triggered; the six (4,4,5) rank-60 schemes are reported as rediscoveries that are inequivalent to the one
  published file compared.
* **D12 – A short follow-up with plateau 2 000 and slack 1** ((2,5,6) and (3,3,6), 4 walks × 300 s each), added after the
  (2,5,6) diagnostic (section 6) showed that this policy makes the (2,5,6) walk descend while the default never did.
  Alternative: re-run every target with the new policy, rejected for the 2-hour budget.

## 8. Failures and bugs made and fixed (by this agent)

1. **Records parser, first run:** 19 KM files and 2 MP files failed to parse (single-variable factors written without
   parentheses, e.g. `(a11+a22)*b11*c12`, and lines of the form `-(a25*(…)*(…))`). Fixed in
   `experiments/2026-10-06d_fmt_records.py` (`_split_groups`, nested unwrapping); the final run parses and verifies all
   372 files. The first run's table was not used.
2. **First version of the linear-dependence reduction was slow:** it collected each group into a freshly allocated
   vector on every scan, so walks with the flag on ran at 0.33-0.46 of the plain kernel's median steps/s (arms std_full,
   blk_full, kernel `8e31926b…`). Fix: count first without allocation, then fill a stack array (kernel `6933efaf…`).
   Check: the old and new binaries give identical output on (3,4,5) seeds 1-2 × flag on/off, 10⁸ steps each (4/4
   identical; seed 2 with the flag on 45.3 s → 12.9 s; scratch comparison, the command is in section 11). The tests were
   re-run on the final source and the two arms were re-run (D8).
3. **Two wasted requests** (GitHub, 404): `mkauers/matrix-multiplication/main/README.md` (the repository has no README) and
   `FastMatrixMultiplication/…/schemes/status/ZT/2x5x6_m47_ZT.json` (the `status/` paths named in `status.json` are not in
   the repository; the `source` paths are).
4. **Shell quoting:** backticks inside a double-quoted shell string were executed and blanked a word in a draft of this
   report; caught on re-reading and fixed. No data or code was affected.
5. **Two counts written from memory instead of from the script output**, caught by a recount from
   `search/runs/2026-10-06d_records.json` before hand-in: the draft said that 211 of Kauers' 309 files are valid over Q
   and 98 only in characteristic 2 (correct: 91 and 218), and that 19 AlphaTensor factorizations are in range (correct:
   all 20). Both are fixed in section 2.1; neither entered the records table, which is generated by the script.

## 9. Open ideas

1. **A pool at record + 1 for (3,4,5).** Block starts give 48 in 23/24 walks within 61 s, at pairwise inequivalent
   schemes. Many short walks from a pool of such rank-48 schemes (Kauers-Moosbauer's protocol) would measure whether 47
   is reachable from most 48s or only from a few.
2. **(4,4,5) block starts from all four rank-47 classes of RL-071** (AlphaTensor, KM, Zaru, our class): different 63-starts
   may lead to different rank-60 schemes and, possibly, to 59. Cheap: the starts are one direct sum each.
3. **Equivalence testing for non-square formats** (extend `search/equivalence.py` to GL(n)×GL(m)×GL(p) sandwiches plus the
   format-preserving permutations) to classify the rank-60 (4,4,5) schemes exactly, and to compare them with Kauers'
   collections if more (4,4,5) files become available.
4. **A cheaper full reduction**, e.g. run the dependency test only after flips that create a group of three or more equal
   factors, or only at plateaus; only worth it if a benefit shows up in a larger sample.
5. **(2,4,5) at rank 32 over GF(2) by an exact method.** The format is small (factors of 8, 20 and 10 bits); a SAT
   encoding of the Brent equations at rank 32 with symmetry breaking might be within reach and would give a definite
   answer where walks only give a NULL (cf. the exhaustive 2×2 check of RL-036).
6. **Hensel lifting of the six rank-60 (4,4,5) schemes** to Z/4: Kauers and Moosbauer report that none of their
   characteristic-2 (4,4,4) rank-47 schemes lift [quoted in the RL-071 audit]; whether (4,4,5) rank 60 lifts is a
   separate question (over Z the best known is 61 per CAT/PER).



## 10. Draft RESEARCH_LOG entries (DRAFT; for the maintainer to consolidate; numbers are agent report)

**DRAFT · VERIFIED · Records table for the 35 formats 2 ≤ n ≤ m ≤ p ≤ 6 over GF(2) and general rings.**
Sources: Kauers-Moosbauer flips @ e31a0a0f (37 files), Kauers' meta-flip-graph repository @ 12c26b29 (309 files),
Arai-Ichikawa-Hukushima @ fe7b2040 (2), Moosbauer-Poole @ 3e2d4dd8 (4), AlphaTensor F2 (20), all parsed and verified over
GF(2) by both exact verifiers where nmp ≤ 100 (`verify` alone above); plus Sedoglavic's catalogue, the MMC and Perminov's
status.json as claims. GF(2) best: (4,4,4) 47, (4,4,5) 60, (4,5,5) 73 are below the general-ring bests (48, 61, 76);
(2,4,5) 33, (3,3,6) 42, (3,6,6) 82 are above them (32, 40, 80). KM's file `366-85-mod2.exp` holds 86 terms.
Experiment `experiments/2026-10-06d_fmt_records.py`; report research/2026-10-06d_exotic_formats.md section 2.

**DRAFT · VERIFIED · The Q records of (2,4,5) (rank 32) and (3,3,6) (rank 40) do not reduce to GF(2) as they stand.**
Both verify exactly over Q; their denominators are {1, 2} and {1, 8}, and after per-factor rescaling a term keeps a
negative 2-adic valuation. AlphaEvolve's (2,5,6) rank-47 scheme has integer coefficients and verifies over GF(2) after
reduction. Experiment `experiments/2026-10-06d_fmt_char0_records.py`. This does not exclude an equivalent 2-integral
scheme.

**DRAFT · DECISION · Target formats: (3,3,6) → ≤ 41, (2,4,5) → 32, (2,5,6) → 46, (4,4,5) → 59.**
Rationale: a general-ring record that does not transfer to GF(2) ((3,3,6), (2,4,5)), a GF(2) flip-graph result above the
characteristic-0 record ((2,5,6): KM 48 vs AlphaEvolve 47), all within the kernel's size range; (4,4,5) as the
calibration format. Asymptotic value: (3,3,6) at 41, (2,5,6) at 46 and (4,4,5) at 59 would each give an exponent below
log₂7 (2.7929, 2.8053, 2.7915), none below log₄47 = 2.7773; (2,4,5) at 32 would be a format record only (2.8185).

**DRAFT · VERIFIED (exactness) and NULL (benefit) · Linear-dependence reduction in the Rust kernel (`--full-reduce`).**
Removes a term when the terms sharing one of its factors have linearly dependent factors in a second position.
Mirrored in `search/kernel_reference.py`; differential test (9 configurations × 2, all counters identical, branch,
plus transitions, restarts and dead ends exercised) and planted-dependency tests pass; `--full-reduce 0` is identical
to the pre-round kernel in 14/14 step-limited cases. Benefit: (3,4,5) 0/32 at rank 47 with it (16 walks with each of the two
versions), (4,4,5) 1/8 at 60 with it vs 1/8 without; 0.46-0.81 of the plain
kernel's steps/s. Default off.

**DRAFT · VERIFIED (calibration) · Block starts close the (4,4,5) gap: 6/24 walks reach the best known GF(2) rank 60.**
Start (4,4,1) + (4,4,4) = 16 + 47 = 63 (`search/blocks.py`). Before (RL-059, standard start, 180 s): 0/8, best 64. After:
180 s, 1/8 with the plain kernel and 1/8 with the full reduction; 240 s (target arm, other seeds), 4/8. All six rank-60
schemes pass `verify`, `verify_explicit` and 200 random checks, are not valid over Z as they stand, and are pairwise
inequivalent and inequivalent to KM's published `445-60-mod2.exp` by the factor-rank profile. VERIFIED rediscoveries of the best known
rank, not records. (3,4,5): block starts reach 48 in 23/24 walks against 12/24 from the standard start (Fisher p = 0.0007),
but 47 in 0/24 (standard start 1/8, an exact reproduction of RL-059's seeds 1-8).

**DRAFT · CORRECTED · The first version of the linear-dependence reduction allocated on every group scan.**
Old state: walks with the flag ran at 0.33-0.46 of the plain kernel's median steps/s (kernel 8e31926b). Fix: count, then
fill a stack array (kernel 6933efaf); identical output in 4/4 step-limited comparisons; the two affected arms were
re-run.

**DRAFT · NULL · Targeted search below the best known GF(2) ranks.** (2,4,5) at 32: 32 walks × 60 s; (3,3,6) at ≤ 41:
28 walks × 180-300 s; (2,5,6) at ≤ 46: 20 walks × 180-300 s; (4,4,5) at ≤ 59: 32 walks × 180-240 s (calibration
included); in total 160 walks, 3.89·10¹¹ steps, 24 000 walk-seconds, with standard, block and published starts.
Nothing below a record; nothing claimed. Experiments `experiments/2026-10-06d_fmt_targets.py`, `…_calibrate.py`.

**DRAFT · NEAR-MISS · One above the record.** (3,3,6): 9 walks at 43 (record 42), 9 pairwise inequivalent schemes;
(3,4,5): 23/24 block-start walks at 48 (record 47); (4,4,5): walks from two rank-60 starts stayed at 60 for 8 × 240 s.

**DRAFT · NULL and a measured obstacle · (2,5,6) under the default walk policy.** From the standard algorithm (60) and
the block start (50) the walks never improved (4 + 4 walks × 180 s; the pre-round kernel is identical on 2 × 2·10⁸
steps). With plateau 2 000 and slack 1 they descend at once (58, 55, 56, 59 within 30 s; 57, 51, 52, 59 within 300 s).
The default plateau/slack is therefore format-dependent in its effect. Experiment `experiments/2026-10-06d_fmt_256_probe.py`.

**DRAFT · IDEA · Next steps.** (1) A pool of rank-48 (3,4,5) schemes and many short walks from it; (2) (4,4,5) block
starts from all four rank-47 classes; (3) equivalence testing for non-square formats; (4) an exact (SAT) attack on
(2,4,5) at rank 32 over GF(2); (5) portfolio restarts for walks that sit far above the record with no restarts
((2,4,5) seeds 1004 and 1006 stayed at 39 and 37 for 40-50 s).



## 11. Reproduction

From the repository root, with `PYTHONIOENCODING=utf-8` and `FMT_CACHE=<a directory outside the repository>`
(downloads are cached there; a rerun re-downloads into an empty cache, politely):

```
./.venv/Scripts/python -m unittest discover -s tests                      # all tests
./.venv/Scripts/python experiments/2026-10-06d_fmt_records.py             # section 2 (network on first run)
./.venv/Scripts/python experiments/2026-10-06d_fmt_char0_records.py       # section 2.3
./.venv/Scripts/python experiments/2026-10-06d_fmt_identity.py            # section 4.2: --full-reduce 0 == pre-round kernel
./.venv/Scripts/python experiments/2026-10-06d_fmt_calibrate.py 345       # 16 min, 4 walks at a time
./.venv/Scripts/python experiments/2026-10-06d_fmt_calibrate.py 345v2     # 8 min
./.venv/Scripts/python experiments/2026-10-06d_fmt_calibrate.py 445       # 12 min
./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py library     # under 1 min
./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py 245         # 8 min
./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py 336         # 18 min
./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py 256         # 12 min
./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py 445         # 16 min
./.venv/Scripts/python experiments/2026-10-06d_fmt_256_probe.py           # section 6, about 2 min
./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py 256b        # 5 min (plateau 2 000, slack 1)
./.venv/Scripts/python experiments/2026-10-06d_fmt_targets.py 336b        # 5 min
./.venv/Scripts/python experiments/2026-10-06d_fmt_analysis.py            # sections 4-6, re-verifies every saved scheme;
                                                                          # the KM comparison needs FMT_CACHE
```

Walks are deterministic per seed and kernel (RL-059; reconfirmed here by the std_off arm), but the budgets are in
seconds, so the end point of a rerun can differ under another machine load. The scratch comparison of the two
full-reduce versions (section 8, item 2) ran the binaries built from `8e31926b…` and `6933efaf…` with
`--input <(3,4,5) standard> --seed 1|2 --max-steps 100000000 --max-seconds 1e9 --full-reduce 1|0` and compared the
outputs without timings; `8e31926b…` can be rebuilt by reverting the allocation-free change in `dependency_reduction`.


## 12. Files created or changed

Changed (search/ and the kernel tests, owned this round):
* `search/kernel/flipwalk.rs`: `--full-reduce` (linear-dependence reduction, default off), counter `dep_reductions`;
  SHA-256 69837abe… → 6933efaf….
* `search/kernel_reference.py`: line-by-line mirror (`dependency_reduction`, `reduce(..., full)`, `walk(..., full_reduce)`).
* `search/rust_kernel.py`: `full_reduce` parameter and `--full-reduce` CLI flag (default 0).
* `tests/test_search_rust.py`: `test_differential_full_reduce`.

Created:
* `search/blocks.py` (format maps, direct sums, block starts), `search/campaign.py` (arms, logging, Clopper-Pearson).
* `tests/test_search_blocks.py` (9 tests).
* `experiments/2026-10-06d_fmt_records.py`, `…_fmt_char0_records.py`, `…_fmt_identity.py`, `…_fmt_calibrate.py`,
  `…_fmt_targets.py`, `…_fmt_256_probe.py`, `…_fmt_analysis.py`, and `experiments/2026-10-06d_flipwalk_before.rs`
  (verbatim copy of the pre-round kernel, needed by the identity check and the probe).
* Logs in `search/runs/`: `2026-10-06d_records.json`, `_records.console.txt`, `_char0_records.console.txt`,
  `_identity.console.txt`, `_cal_3x4x5.jsonl`, `_cal_3x4x5.console.txt`, `_cal_3x4x5_v2.console.txt`, `_cal_4x4x5.jsonl`,
  `_cal_4x4x5.console.txt`, `_library.jsonl`, `_library.console.txt`, `_tgt_2x4x5.{jsonl,console.txt}`,
  `_tgt_3x3x6.{jsonl,console.txt}`, `_tgt_3x3x6b.console.txt`, `_tgt_2x5x6.{jsonl,console.txt}`, `_tgt_2x5x6b.console.txt`,
  `_tgt_4x4x5.{jsonl,console.txt}`, `_256_probe.console.txt`, `_analysis.console.txt` (no local paths in any of them).
* Schemes in `search/schemes/rust-2026-10-06d/` (141 files, all re-verified by `fmt_analysis.py`: `verify`,
  `verify_explicit`, 200 random checks): `starts/` (5 block starts), `library/` (16 small rediscoveries), `cal/` (64),
  `targets/` (56; walks from published starts were saved only if below the record, which never happened). None is below
  a best known rank; the only files valid over Z are the four (2,5,6) "best" files that never left the standard algorithm.
* This report, `research/2026-10-06d_exotic_formats.md`.

Not touched: RESEARCH_LOG.md, README.md, index.json, tools/, schema/, lib/, the entries, `search/machine.py`, and the
other agents' directories. No git command was run, nothing was installed. Build products (`flipwalk.exe`,
`flipwalk_before6d.exe`) are in the gitignored `search/kernel/build/`.

Final checks (after all searches): `python -m unittest discover -s tests`: **178 tests OK** (13.9 s);
`python tools/validate.py`: **62/62 entries OK**.
