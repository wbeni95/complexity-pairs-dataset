# Rust flip-graph kernel: exact dead-end detection and escape, and a 4×4×4 statistic against RL-059

Date: 2026-10-06 (work 11:30-12:50 local time). Follows RL-052, RL-054, RL-059 and RL-061 item 1.
Author: delegated research agent (Claude), for the maintainer. Every number below comes from a run made here (script,
seed, budget, steps and time are given) or from a repository log whose file name is given. Nothing here is a new
result unless explicitly labelled, and nothing is claimed as a discovery.

## Summary

* **Design (section 1).** The kernel now records every failed candidate search as a proof that one factor of one
  term is unique. These proofs are stamped per (term, position) cell with an epoch that advances whenever the scheme
  changes. Once r of the 3r cells are stamped, one deterministic sweep settles the rest. The scheme is a dead end
  exactly when all 3r cells are stamped.
  * The test is **exact** (no false alarms, and every dead end is found); soundness and completeness are argued in
    section 1.2.
  * It is **deterministic**: it draws no random numbers.
  * It is **cheap**: an expected 157 step-equivalents to detect a rank-49 dead end, against the old 50 000-step
    plateau.

  On detection the walk applies the plateau rule at once (restart if above best + slack, otherwise a plus
  transition). `--dead-end 0` reproduces the old kernel exactly (17/17 step-limited cases identical).
* **Tests (section 2): all pass** (94/94 before the measurement; 110/110 at the end, including 16 tests added by
  another agent during the session).
  * The differential test runs every configuration with the escape on and off and asserts that the dead-end branch
    is exercised (`dead_ends` > 0), as restarts are.
  * A new differential test starts from Strassen ⊗ Strassen.
  * Two new tests check exactness: a brute-force pair check at every detection, and detection at Strassen's 2×2
    scheme.
* **Throughput (section 3).**
  * At a dead end (from S⊗S, 8 × 20 s): flips/s 1.91·10⁴ → 9.41·10⁵ (×49) and plus transitions/s 440 → 22 000 (×50),
    while steps/s falls by 30% because steps now do work.
  * Away from dead ends, on identical trajectories, the new kernel runs at about 95% of the old speed: off/before
    0.981, on/off 0.964 (medians over 7 seeds; machine drift not separated).
* **Measurement (section 4):** 24 new seeds (601-624) × 900 s with the escape on.
  * **4/24 reached rank 47** (95% CI 0.047-0.374; seeds 610, 617, 618, 622 at 890.5, 842.9, 209.8 and 796.1 s),
    against 0/24 in RL-059 (0-0.142; Fisher p = 0.109) and 1/28 pooled (p = 0.169).
  * 14/24 reached ≤ 49, against 20/24 (p = 0.111).
  * **The 4/24 is not an effect of the escape.** In all four walks, ranks 49, 48 and 47 came in one burst of
    481-17 109 steps. Re-run with `--dead-end 0` (the old kernel), all four give the same rank-47 scheme at the same
    step.
  * The 10 walks that sat at a rank-49 dead end made 22 times as many escapes as RL-059's (1.94·10⁸ in 8 298 s) and
    **none improved**: NULL for leaving rank-49 dead ends with this escape. A mirror diagnostic shows why: escapes
    keep returning to 2-11 distinct rank-49 dead ends.
* **Schemes (sections 4.5 and 5).**
  * 25 saved, all pass `verify`, `verify_explicit` and 200 random checks.
  * Five rank-47 schemes, including one from the old kernel, seed 707 of the throughput benchmark. They are **VERIFIED
    rediscoveries of the best known GF(2) rank**. They share one factor-rank invariant that differs from
    AlphaTensor's, Kauers-Moosbauer's and RL-054's, so they are provably inequivalent to those three.
  * **Nothing below 47**; rank 46 is NULL, with 860.7 s and 1.18·10¹⁰ steps walked after reaching 47.
* **Recommendation.** Keep the detection: it is exact and cheap, and it turns idle time at dead ends into about
  50 times more moves. But it does **not** by itself raise the chance of reaching 47. The evidence points to bursts
  out of rank 50 as the route to 47, and to a stronger escape or portfolio restarts as the next experiment
  (OPEN IDEAS 1-2).

## 1. Design

### 1.1 The obstacle (RL-059)

In RL-059, 19 of the 20 rank-49 endpoints of uncapped 4×4×4 walks had **no two terms sharing a factor in any
position**. At such a scheme no flip exists: every step draws a term i and a position p, scans the other terms for
the same factor, finds none, and does nothing. The old kernel left only through one plus transition per 50 000-step
plateau, measured here at 440 plus transitions/s from S⊗S (section 3). The walks that reached 49 early made only
about 0.1% flips among their steps (RL-059 table: 2.07-2.90·10⁷ flips in 2.36-2.42·10¹⁰ steps).

### 1.2 Detection (exact, cheap, deterministic)

The kernel already performs the expensive part of the test at every step: the candidate search for (i, p). A failed
search proves that factor p of term i is unique in the current scheme. The new code only records these proofs:

* **Cells and stamps.** Cell `3i+p` stands for (term i, position p). `stamp[cell] = epoch` records that a candidate
  search in the current epoch found no partner for that cell; `unmatched` counts the distinct stamped cells.
* **Epochs.** The epoch number increases whenever the scheme may have changed: after every successful flip (with its
  reduction), every restart and every successful plus transition. Old stamps then no longer equal the epoch, so they
  are discarded in O(1). A failed plus transition or a weight-rejected flip leaves the scheme and the epoch unchanged.
* **Completion sweep.** Waiting for random draws to hit all 3r cells is a coupon-collector process: 3r·H₃ᵣ = 818.9
  steps on average at rank 49 (`experiments/2026-10-06c_analysis.py`, analytic). Therefore, once r of the 3r cells
  are stamped in the current epoch, the kernel runs **one** sweep over the other cells in index order. It scans each
  unstamped cell for a partner, stamps it if there is none, and stops at the first cell that has a partner. There is
  at most one sweep per epoch, and it consumes no random numbers. At a rank-49 dead end the expected cost falls to
  59.4 steps plus 98 scans, about 157 step-equivalents (a step is also one scan of r terms).
* **Dead end** ⇔ `unmatched == 3r`.

**Exactness argument.**
1. *Soundness (no false alarms).* A cell is stamped only after a full scan in which no other term has the same factor
   in that position. The scheme does not change within an epoch, since every change advances the epoch, and stamps of
   earlier epochs are ignored. So when all 3r cells carry the current stamp, every factor of every term is unique in
   its position, which means that no pair of terms shares a factor and no flip exists. The epoch counter is a u64
   that only increases; it would need 1.8·10¹⁹ changes to wrap.
2. *Completeness (every dead end is detected).* At a dead end every candidate search fails and stamps a cell, so
   `unmatched` grows until it reaches r. The sweep then runs. It cannot stop early, because no cell has a partner,
   so it stamps every remaining cell. The dead end is therefore reported at the step that produces the r-th distinct
   stamp, unless the plateau fires first.
   This step comes after finitely many steps with probability 1: each step stamps a uniformly random cell, and the
   expected wait is 59.4 steps at rank 49.
3. *Determinism.* Detection reads the scheme and draws no random numbers. The escape uses the same random calls as
   at a plateau. The Python mirror performs the same operations in the same order (section 2).
4. *Scope.* "Dead end" means exactly "no two terms share a factor". A scheme whose shared-factor flips are all
   rejected by a weight cap is **not** reported, because weight rejections are not stamped. Such schemes still
   wait for the plateau, as before.

**Cost.** A failed search costs one comparison and one store more than before. A successful flip costs one
increment more. A sweep costs at most 3r scans, runs at most once per epoch, and runs only in epochs with at least r
distinct failed cells. Such epochs do not occur in the normal flipping regime, where 11-31% of steps flip (RL-059),
and occur only near or at dead ends. Memory: 3r u64 stamps.

### 1.3 Escape

When a dead end is detected, the kernel applies the plateau rule at once:
* if the current rank exceeds best + slack, it restarts from the best scheme;
* otherwise it attempts a plus transition. If the attempt fails (i = j, or the weight cap), the scheme is unchanged.
  The dead end is then still recorded and is reported again at the next step, so the escape is retried at once
  instead of after another 50 000 steps.

`since` is reset as after a plateau. A new counter, `dead_ends`, counts the steps at which a dead end was detected,
each followed by one restart or one plus attempt. It is printed in the STATS line.

### 1.4 Interface

* `flipwalk.rs --dead-end 1|0`. The default is 1, the new behaviour. With 0, the walk follows the old kernel's
  trajectory **exactly**: identical best scheme, steps, counters and improvement history in 17/17 step-limited test
  cases (section 3). STATS gains `dead_ends=<d>`.
* `search/rust_kernel.py`: `run(..., dead_end=True)`, `run_parallel(..., dead_end=...)`, CLI `--dead-end {0,1}`.
  The parameter is recorded in every log line (`params.dead_end`).
* `search/kernel_reference.py`: `walk(..., dead_end=True, on_dead_end=None)` mirrors the change line by line.
  `on_dead_end(terms, best_rank)` is a test-only hook called at every detection.

## 2. Tests

`./.venv/Scripts/python -m unittest discover -s tests`: **94 tests, all OK** (6.9 s), run before the measurement
started. The suite was run again at the end, with no search running: **110 tests, all OK** (10.7 s). The 16 extra
tests are in `tests/test_search_equivalence.py`, which appeared at 11:43 during this session. It was **not written
by this agent**: another agent was active in the repository at the same time. Its CPU use during the timing runs
was not monitored, beyond checking that exactly 8 `flipwalk` processes (ours) ran during the main run.
`tests/test_search_rust.py` alone: 8 tests OK.
Changes in `tests/test_search_rust.py`:

* **Differential test, extended.** Every configuration now runs twice, with the escape on and with it off. Rust and the
  mirror must agree on the best scheme, steps, flips, rejections, plus transitions, restarts, `dead_ends` and the
  improvement history. Three dead-end configurations were added: plateau 10⁹, so that only the dead-end branch can
  move the walk; 2×2×2 seeds 3 and 11, and 2×2×3 seed 2. The test asserts:
  * restarts > 0 with the escape on;
  * restarts > 0 with it off;
  * **`dead_ends` > 0 with it on** (the new branch is exercised);
  * `dead_ends` = 0 with it off.
* **New differential test from Strassen ⊗ Strassen** (4×4×4, rank 49, no pair shares a factor), seeds 1-2, 20 000
  steps, plateau 10⁹ and 5 000, both modes. With the escape on, `dead_ends` > 0. With it off and plateau 10⁹, the walk
  makes 0 flips and 0 plus transitions: the old kernel idles there.
* **Exactness, independently of the kernel's bookkeeping.** `DeadEndTests.test_detection_fires_only_at_true_dead_ends`
  runs the mirror with the `on_dead_end` hook on four configurations. At every detection, a brute-force check over
  all pairs and positions confirms that no two terms share a factor. The test also asserts that detections occurred.
* **Completeness on a known dead end.** `test_strassen_dead_end_is_left_without_waiting_for_the_plateau` starts from
  Strassen's 2×2 scheme, which admits no flip, with plateau 10⁹. Off: 0 flips, 0 plus transitions, 0 detections.
  On: detections > 0, plus transitions > 0, flips > 0. The best rank stays 7 and the scheme verifies.
* **Not asserted:** a dead end left through a *restart*. That requires a dead end above best + slack. It never
  occurred in the small-format walks tried: 2×2×2, 2×2×3, 2×3×3, 3×3×3 and 2×2×4 from the standard algorithm,
  seeds 1-30, 2·10⁵ steps each, slack 0, plateau 10⁹; and 3 formats × 3 plateaus × 3 slacks × 10 seeds × 4 000
  steps in the mirror (scratch probes, not kept). The restart lines (including the epoch reset) are shared with the
  plateau path and are covered there (restarts > 0 with the escape on).
* Warnings: `rustc -O --edition 2021 -D warnings` and a debug build with `-C debug-assertions=on -C overflow-checks=on`
  both compile cleanly.

## 3. Identity with the old kernel, and throughput

Script: `experiments/2026-10-06c_kernel_throughput.py` (11:40:49-11:44:17). Log: `search/runs/2026-10-06c_throughput.jsonl`,
console output: `search/runs/2026-10-06c_throughput.console.txt`. The "before" kernel is
`experiments/2026-10-06c_flipwalk_before.rs`, a verbatim copy of the pre-round source (SHA-256 `6f306293…ad644`).
That is the kernel recorded in the `kernel_sha256` field of all 24 RL-059 and all 4 RL-054 job-B log lines.
New kernel: SHA-256 `69837abe…0f550`.

**Identity: 17/17 step-limited cases identical** between "before" and the new kernel with `--dead-end 0`. The
cases were 2×2×2 (seeds 1-3, plateau 50 and 50 000, 2·10⁵ steps), 3×3×3 (seeds 1-2, plateau 500 and 50 000,
2·10⁶ steps), 4×4×4 standard (seeds 1-3, 3·10⁷ steps) and 4×4×4 from S⊗S (seeds 1-2, plateau 5 000 and 50 000,
5·10⁶ steps).

**Throughput.** 8 walk processes at once, seeds 701-708, below-normal priority, no cap, plateau 50 000, slack 3.
Medians over the 8 walks, with min-max in brackets for steps/s:

| start, budget | kernel | steps/s | flips/s | plus transitions/s | dead ends detected/s |
|---|---|---|---|---|---|
| standard 4×4×4, 45 s | before | 1.493·10⁷ (1.355-2.179) | 2.147·10⁶ | 290 | – |
| | new, off | 1.463·10⁷ (1.338-2.159) | 2.128·10⁶ | 284 | 0 |
| | new, on | 1.403·10⁷ (1.300-1.559) | 2.092·10⁶ | 272 | 0 (max 1.97·10⁴) |
| S⊗S (a dead end at step 1), 20 s | before | 2.243·10⁷ (2.221-2.258) | 1.907·10⁴ | 440 | – |
| | new, off | 2.276·10⁷ (2.257-2.290) | 1.928·10⁴ | 446 | 0 |
| | new, on | 1.575·10⁷ (1.565-1.617) | **9.405·10⁵** | **2.200·10⁴** | 2.244·10⁴ |

Reading:
* **Overhead of the bookkeeping: small but measurable.** A walk that never detects a dead end follows the same
  trajectory in all three kernels, so steps/s compares the same work. That held for 7 of the 8 standard-start seeds
  (702-708, 0 detections with the escape on). Per seed (`experiments/2026-10-06c_paired_overhead.py`):
  * "off" ran at 0.981 of "before" (median; range 0.975-0.988);
  * "on" ran at 0.964 of "off" (median; range 0.941-0.972).

  In total "on" is about 5% slower than "before" away from dead ends. The three groups ran one after the other
  (before, off, on), so a slow drift of the machine (e.g. temperature) is not separated from the overhead. On S⊗S,
  "off" was 1.5% *faster* than "before" in median steps/s.
* **At a dead end the useful work rises about 50-fold.** From S⊗S: flips/s ×49.3 and plus transitions/s ×50.0.
  Steps/s falls by 30%, because steps now do work (flip, reduce) instead of failing scans. Steps/s is therefore no
  longer a measure of useful work; flips/s is.
  Per escape at S⊗S: about 43 flips and 717 steps (seed 701: 1.885·10⁷ flips, 437 736 plus transitions,
  3.141·10⁸ steps in 20 s).
* **Paired seed 701 from the standard algorithm** (all three kernels reached 49 at 3.1-3.2 s, then sat at a dead
  end):
  * before: 19 177 plus transitions and 8.89·10⁶ flips in 45 s;
  * on: 869 800 plus transitions (×45), 886 217 detections and 4.52·10⁷ flips (×5.1).
* **Away from dead ends the walk is the same, only about 5% slower** (first bullet). 7 of the 8 standard walks never
  met a dead end within 45 s.
* **Seed 707:** the *old* kernel reached rank 47 at 43.6 s, and "off" at 43.97 s on the same trajectory. With the
  escape on, seed 707 detected **no** dead end either, so its trajectory was the same. At 1.372·10⁷ steps/s it had
  made only 6.17·10⁸ of the 6.29·10⁸ steps needed when its 45 s ran out, and it ended at 50.
  This is the overhead above, turned into a lost result at a hard time limit. The walk was reproduced with a step
  budget (section 4.4).

## 4. The 4×4×4 measurement

### 4.1 Setup

Script: `experiments/2026-10-06c_4x4_deadend_stats.py`. The design is the RL-059 design: 4×4×4 from the standard
algorithm, no weight cap, plateau 50 000, slack 3, target rank 0, 8 walk processes at a time at below-normal
priority, **900 s per walk**. The differences are the kernel (`--dead-end 1`, SHA-256 `69837abe…0f550`) and the
seeds: **601-624**, which no earlier 4×4 Rust walk used.
The run took 11:44:27-12:29:28 (2701 s wall clock, 3 rounds; 21 600 walk-seconds) and exited with 0; all 24 results
passed the exact verifier.
Log: `search/runs/2026-10-06c_4x4_deadend.jsonl`. Console output: `search/runs/2026-10-06c_4x4_deadend.console.txt`.
Numbers: `experiments/2026-10-06c_analysis.py` (console output `search/runs/2026-10-06c_analysis.console.txt`).
Baseline numbers are recomputed by the same script from `search/runs/2026-10-07b_4x4_nocap.jsonl` (RL-059) and
`search/runs/2026-10-07_rust_4x4_nocap.jsonl` (RL-054 job B, truncated at 900 s for pooling).

### 4.2 Every walk

First time (s) at which a rank ≤ r was reached; steps at ≤ 49. The 47 column also gives the step.

| seed | final | ≤52 | ≤50 | ≤49 (s; step) | ≤47 (s; step) | steps | steps/s | flips | plus | restarts | dead ends detected |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 601 | 49 | 3.0 | 3.2 | 3.2; 4.292·10⁷ | – | 1.4606·10¹⁰ | 1.623·10⁷ | 879 645 747 | 20 491 120 | 0 | 20 899 063 |
| 602 | 49 | 5.9 | 11.3 | 11.3; 1.627·10⁸ | – | 1.4606·10¹⁰ | 1.623·10⁷ | 885 149 130 | 20 237 128 | 0 | 20 637 263 |
| 603 | 49 | 3.1 | 6.6 | 6.6; 9.777·10⁷ | – | 1.4595·10¹⁰ | 1.622·10⁷ | 881 012 086 | 20 449 562 | 0 | 20 856 547 |
| 604 | 49 | 0.5 | 1.1 | 1.1; 1.819·10⁷ | – | 1.4591·10¹⁰ | 1.621·10⁷ | 869 722 434 | 20 298 481 | 0 | 20 700 441 |
| 605 | 49 | 2.5 | 2.6 | 2.6; 3.674·10⁷ | – | 1.4564·10¹⁰ | 1.618·10⁷ | 876 901 522 | 20 508 660 | 0 | 20 917 173 |
| 606 | 50 | 1.5 | 73.2 | – | – | 1.5890·10¹⁰ | 1.766·10⁷ | 1 283 188 312 | 309 498 | 0 | 0 |
| 607 | 49 | 1.3 | 656.5 | 656.5; 9.314·10⁹ | – | 1.3353·10¹⁰ | 1.484·10⁷ | 2 120 317 804 | 5 868 889 | 0 | 5 802 486 |
| 608 | 52 | 2.6 | – | – | – | 1.1123·10¹⁰ | 1.236·10⁷ | 3 302 376 820 | 214 317 | 0 | 0 |
| 609 | 50 | 7.5 | 17.3 | – | – | 1.7204·10¹⁰ | 1.912·10⁷ | 1 831 796 880 | 334 777 | 1 | 0 |
| **610** | **47** | 7.1 | 23.0 | 890.5; 1.6850·10¹⁰ | **890.5; 1.6850·10¹⁰** | 1.7004·10¹⁰ | 1.889·10⁷ | 1 817 911 800 | 1 153 553 | 0 | 843 815 |
| 611 | 52 | 1.8 | – | – | – | 1.5411·10¹⁰ | 1.712·10⁷ | 2 691 716 622 | 299 220 | 4 | 0 |
| 612 | 50 | 5.2 | 28.1 | – | – | 1.8061·10¹⁰ | 2.007·10⁷ | 1 536 550 541 | 352 096 | 1 | 0 |
| 613 | 50 | 6.6 | 687.2 | – | – | 1.5267·10¹⁰ | 1.696·10⁷ | 2 685 917 572 | 296 188 | 5 | 0 |
| 614 | 50 | 6.2 | 12.0 | – | – | 1.7126·10¹⁰ | 1.903·10⁷ | 1 829 270 093 | 333 030 | 0 | 0 |
| 615 | 49 | 4.0 | 5.9 | 11.5; 1.949·10⁸ | – | 1.6522·10¹⁰ | 1.836·10⁷ | 992 556 109 | 22 944 544 | 0 | 23 398 383 |
| 616 | 49 | 0.8 | 1.1 | 1.1; 1.333·10⁷ | – | 1.6454·10¹⁰ | 1.828·10⁷ | 979 006 890 | 22 880 111 | 0 | 23 332 963 |
| **617** | **47** | 3.4 | 605.3 | 842.9; 1.3250·10¹⁰ | **842.9; 1.3250·10¹⁰** | 1.4034·10¹⁰ | 1.559·10⁷ | 1 736 922 384 | 4 471 309 | 0 | 4 305 415 |
| **618** | **47** | 0.9 | 209.8 | 209.8; 3.6186·10⁹ | **209.8; 3.6186·10⁹** | 1.3069·10¹⁰ | 1.452·10⁷ | 667 565 769 | 50 712 539 | 0 | 51 741 652 |
| 619 | 50 | 4.5 | 314.6 | – | – | 1.4886·10¹⁰ | 1.654·10⁷ | 1 537 315 638 | 289 648 | 0 | 0 |
| 620 | 49 | 3.2 | 3.2 | 3.2; 4.625·10⁷ | – | 1.4502·10¹⁰ | 1.611·10⁷ | 874 114 806 | 20 263 852 | 0 | 20 668 049 |
| 621 | 49 | 4.3 | 4.7 | 4.7; 7.110·10⁷ | – | 1.4506·10¹⁰ | 1.612·10⁷ | 879 012 380 | 20 363 889 | 1 | 20 770 504 |
| **622** | **47** | 3.4 | 789.0 | 796.1; 1.2416·10¹⁰ | **796.1; 1.2416·10¹⁰** | 1.3843·10¹⁰ | 1.538·10⁷ | 1 586 906 457 | 7 890 877 | 0 | 7 815 682 |
| 623 | 50 | 7.4 | 285.5 | – | – | 1.5641·10¹⁰ | 1.738·10⁷ | 1 322 109 334 | 304 509 | 1 | 0 |
| 624 | 52 | 3.0 | – | – | – | 1.2017·10¹⁰ | 1.335·10⁷ | 2 949 237 869 | 232 235 | 3 | 0 |

Totals: 3.5887·10¹¹ steps, 3.7016·10¹⁰ flips, 2.6150·10⁸ plus transitions, 2.6269·10⁸ dead-end detections.
RL-059 had 5.1348·10¹¹ steps, 1.9049·10¹⁰ flips and 1.0038·10⁷ plus transitions in the same 21 600 walk-seconds.
Final ranks: 47 ×4, 49 ×10, 50 ×7, 52 ×3 (RL-059: 49 ×20, 50 ×1, 51 ×2, 52 ×1).

### 4.3 Comparison with RL-059

Exact two-sided 95% intervals (Clopper-Pearson), and two-sided Fisher exact tests of the difference:

| event within 900 s | this round (escape on) | RL-059 (old kernel) | Fisher p |
|---|---|---|---|
| rank ≤ 49 | 14/24 (0.366-0.779) | 20/24 (0.626-0.953) | 0.111 |
| rank ≤ 48 | **4/24 (0.047-0.374)** | 0/24 (0-0.142) | 0.109 |
| rank ≤ 47 | **4/24 (0.047-0.374)** | 0/24 (0-0.142) | 0.109 |
| rank ≤ 47, against RL-059 pooled with RL-054 job B | 4/24 | 1/28 (0.001-0.183) | 0.169 |

**Time to rank ≤ 49:**
* this round, 14/24 walks: 1.1, 1.1, 2.6, 3.2, 3.2, 4.7, 6.6, 11.3, 11.5, 209.8, 656.5, 796.1, 842.9 and 890.5 s;
  median 9.0 s among those 14;
* RL-059, 20/24 walks: median 13.8 s;
* Mann-Whitney, with walks that never reached 49 ranked last as ties: z = 1.94, p ≈ 0.052 (normal approximation).
  This round is slower, not faster, but not significantly at the 5% level.

None of these differences is significant at the 5% level. The point estimate for reaching 47 rose from 0/24 to 4/24,
but section 4.4 shows that this **cannot be credited to the escape**.

### 4.4 Attribution: did the escape produce the four rank-47 walks?

Dead-end detection draws no random numbers and changes nothing until it reports a dead end. Up to its first
detection, a walk with the escape on therefore follows the old kernel's trajectory for the same seed exactly.

* **10 of the 24 walks never detected a dead end** (606, 608, 609, 611, 612, 613, 614, 619, 623, 624; final ranks
  50 ×7, 52 ×3). They are old-kernel walks in all but speed. So the lower rate of reaching 49 (14/24 against 20/24)
  is a difference between seed sets, not an effect of the kernel.
* **In all four rank-47 walks, ranks 49, 48 and 47 were first reached within 481-17 109 steps of each other**:
  * seed 610: step 16 849 601 432 to 16 849 618 541;
  * seed 617: step 13 249 769 132 to 13 249 771 120;
  * seed 618: step 3 618 582 674 to 3 618 583 155;
  * seed 622: step 12 415 773 485 to 12 415 779 886.

  They came down from a rank-50 state to 47 in one short burst (618: 55 824 steps from 50 to 47), like RL-054 seed 8. None of them left a rank-49 dead end
  to get there.
* **Counterfactual check** (`experiments/2026-10-06c_counterfactual_old_kernel.py`): each of these seeds re-run
  with `--dead-end 0` (= the old kernel), step-limited to its last improvement.
  **Result (12:30:50-12:43:17): all four are identical.** The old kernel reaches rank 47 at exactly the same steps
  (16 849 618 541, 13 249 771 120, 3 618 583 155 and 12 415 779 886), with the same improvement history and the same
  rank-47 scheme. The two controls without dead ends (612, 614) are identical as well.
  So these walks met no dead end before rank 47, and **the escape contributed nothing to the four rank-47 results**.
  The old kernel would have produced 4/24 on these seeds too. The 0/24 → 4/24 difference to RL-059 is a difference
  between seed sets (Fisher p = 0.109), which fits a per-walk frequency somewhere in the overlap of the two intervals
  (0.047-0.142).
* **The 10 walks that reached a rank-49 dead end and stayed there never improved.** Together they spent 8 298 s at
  49 and made 1.94·10⁸ escapes (plus transitions), i.e. 22 times as many as the 20 RL-059 walks made in 15 946 s at
  49 (8.86·10⁶). This is a **NULL for leaving the rank-49 dead ends towards 48** with the escape as designed. All 10
  endpoints have the factor-rank invariant of Strassen ⊗ Strassen, and no pair of terms shares a factor.
* **Why** (`experiments/2026-10-06c_deadend_revisits.py`, Python mirror from S⊗S, seeds 1-4, 2·10⁵ steps each):
  * the 72-242 detections per walk fell on only 2-11 distinct dead ends, all of rank 49;
  * the most visited one was hit 34-56 times.

  One plus transition followed by greedy flipping mostly falls back into the same few dead ends.
* **Seed 707 of the throughput benchmark, old kernel** (`experiments/2026-10-06c_reproduce_before_seed707.py`,
  reproduced with a step budget): rank 47 at step 628 866 994, via 50 at step 542 643 415, 49 at 628 850 710 and 48 at
  628 850 779. The "before" binary and `--dead-end 0` gave the same improvement history and scheme. It is the same
  burst pattern, from the old kernel, within 45 s. It lies outside the 900-s design (other seeds, other budget), so it
  is not pooled into the table above.

### 4.5 The rank-47 schemes

Five new rank-47 schemes: seeds 610, 617, 618 and 622 of the main run, and seed 707 of the old kernel. All five:
* pass `verify`, `verify_explicit` and 200 random GF(2) matrix-pair checks;
* are not valid over Z (information only);
* admit no flip (0 pairs sharing a factor).

They share **one** factor-rank invariant: (1,1,1)×1, (1,1,2)×3, (1,1,3)×9, (1,2,3)×12, (1,3,3)×9, (2,2,2)×6,
(2,2,3)×6, (3,3,3)×1. It differs from the invariants of AlphaTensor's published GF(2) rank-47 scheme, of the
Kauers-Moosbauer `444-47-mod2` scheme (both downloaded by the analysis script and verified there) and of RL-054's
rank-47 scheme. So the five are **provably inequivalent to those three**. Whether the five are equivalent to each
other was not decided, since equal invariants prove nothing. Whether they are new among *all* published rank-47
schemes was not checked (RL-061 item 2).
These are **VERIFIED rediscoveries of the best known rank**, not new results.

## 5. Saved schemes and verification

`search/schemes/rust-2026-10-06c/` holds 25 files:
* the verified best scheme of each of the 24 walks (`4x4x4_rank<r>_seed<s>.json`);
* `4x4x4_rank47_before_seed707.json` (old kernel, provenance in the file).

The analysis script re-verified every file separately:
* `verify`, `verify_explicit` and 200 random checks (seed 20261006): **25/25 True**;
* `verify_over_integers`: 0/25 (information only).

Status labels: 5 × "matches best known", 20 × "above best known".
**No scheme is below the best known rank of 47**, so task item 3 (separate re-verification of a candidate) was not
triggered.

## 6. Near-misses

* **Rank 46: NULL.** Scope: the four rank-47 walks kept walking with the escape on after reaching 47: seed 610 for
  9.5 s (1.54·10⁸ steps), 617 for 57.1 s (7.84·10⁸), 618 for 690.2 s (9.45·10⁹) and 622 for 103.9 s (1.43·10⁹).
  That is 860.7 s and 1.18·10¹⁰ steps in total. The rank-47 schemes are dead ends themselves, so most of this time
  was escape cycles, e.g. 5.17·10⁷ detections for seed 618. A null result says nothing about whether rank 46 exists.
* **Seed 610 reached 47 at 890.5 s**, 9.5 s before its budget ran out. With an 880-s budget the count would have
  been 3/24.
* **Seed 707 (benchmark):** the escape-on walk lost a rank 47 only to the 45-s limit, at about 5% lower speed
  (section 3).
* **14/24 against 20/24 walks at ≤ 49** (p = 0.111): a seed-set difference (section 4.4), not a kernel effect.

## 7. Decision log

* **D1. How to detect: stamping failed candidate searches.** Alternatives considered:
  * (a) *"K consecutive failed searches"*: cheap, but not exact. It fires at near-dead ends and cannot tell them from
    dead ends.
  * (b) *A full pair check (O(r²), or a sort per position) after every change*: exact, but flips run at about
    2·10⁶/s, so a check after each flip would cost more than the walk itself.
  * (c) *An incremental hash multiset of factors per position*: exact, with an O(1) query. But it needs updates at
    every flip and inside `reduce`, including the index shifts, which means much more mirrored code, and every flip
    pays for it.

  Stamping is exact and reuses the scan the kernel already does. **Deciding evidence:** "off" against "before" is
  −2.0% / +1.5% in steps/s (section 3), i.e. no measurable cost.
* **D2. Completion sweep once r cells are stamped.** The first version only stamped. In a mirror probe from S⊗S
  (seeds 1-8, 20 000 steps, plateau 10⁹, slack 0; intermediate kernel, scratch script) it made 12-24 detections per
  walk, i.e. about 800-1 700 steps per escape cycle. That is consistent with the analytic 818.9-step coupon-collector
  latency dominating the cycle, since the descent back to a dead end took only 2-51 flips per cycle (45-626 flips
  per walk) in that probe.
  The sweep cuts the expected latency to about 157 step-equivalents. With the final kernel, one escape cycle at S⊗S
  takes about 717 steps in Rust (section 3), most of it now in the descent.
  The threshold r was chosen so that a sweep costs at most 2r scans and never runs in the normal flipping regime. It
  was **not tuned** (OPEN IDEAS).
* **D3. How to leave: the plateau rule, applied at once.** Alternatives:
  * always restart from best: pointless when the best scheme is the dead end itself, which is the RL-059 case;
  * several plus transitions in a row (a bigger "kick");
  * a random walk at rank + 1.

  The plateau rule keeps the move set of the old kernel. The comparison with RL-059 then isolates one change: leaving
  at once instead of after 50 000 steps.
* **D4. Default on, with an exact "off".** `--dead-end 0` reproduces the old trajectories (17/17), so RL-054 and
  RL-059 remain reproducible with the current source.
* **D5. Measurement design = the RL-059 design.** 24 seeds × 900 s, 8 processes at a time and the same kernel
  parameters, with new seeds 601-624. That takes 45 min, inside the 60-minute box. 32 walks (60 min) would have
  given slightly more power but would not have fitted the 90-minute overall box together with the code and tests.
* **D6. Throughput is reported as flips/s and plus transitions/s.** Steps/s falls when steps start doing work
  (section 3), so it no longer measures useful work.
* **D7. The old kernel's rank 47 in the throughput benchmark (seed 707) was reproduced and saved** with a step
  budget instead of being left as a counter-only log line (section 4.4).
* **D8. The 4/24 was attributed by a counterfactual, not credited to the escape by default.** The four rank-47 walks
  reached 49, 48 and 47 in one burst, so they might never have met a dead end. Re-running them step-limited with
  `--dead-end 0` (747 s, 6 processes) decided this exactly: identical. The alternative was to report "4/24 against
  0/24 after the change". That would have been true as a count but wrong as an attribution.

## 8. Open ideas

1. **A stronger escape for rank-49 dead ends.** One plus transition plus greedy flips falls back into the same 2-11
   dead ends (section 4.4). Candidates:
   * k plus transitions in a row (k = 2-5) before flipping resumes;
   * a short tabu that forbids returning to the last dead end, identified by a hash of the sorted terms (cheap: the
     detection already knows when the walk is at one);
   * a phase of flips without merges at rank + 1.

   Each needs its own mirrored test and an RL-059-style statistic.
2. **Make the walk faster where it matters.** Every 47 seen so far came from a burst out of rank 50 (five walks
   here, RL-054 seed 8). That favours *more walks at rank 50* over better handling of rank-49 dead ends. Options:
   * restart a walk that has sat at a rank-49 dead end for T seconds, from the standard algorithm with a fresh seed
     (portfolio restarts);
   * start from rank-50 states saved from the walks.
3. **Tune the sweep threshold** (now r cells). At a threshold of 0 the sweep would run at the first failure of every
   epoch. The cost model in section 1.2 suggests little gain, because the descent, not the detection, now dominates
   the cycle (about 717 steps per cycle at S⊗S).
4. **Recover the 5% overhead** away from dead ends. For example, stamp only after k consecutive failures. That stays
   exact, because stamps are still proofs, but detection would be delayed.
5. **Weight-cap dead ends.** Schemes where every shared-factor flip is rejected by the cap are not detected. Exact
   detection would need all candidates of a cell to be checked against the cap, not one random candidate.
6. **Statistics with power.** To detect a rise from 1/28 to 4/24 at 5% (two-sided) with 80% power needs about 83
   walks per arm (normal approximation, `experiments/2026-10-06c_analysis.py`); Fisher's exact test needs somewhat
   more. For a kernel comparison the arms should use the **same seeds**: walks without dead ends then coincide, and
   only the divergent part is compared.
7. **Equivalence of the five rank-47 schemes of section 4.5** with each other and with all published rank-47
   schemes (RL-061 item 2).

## 9. Files and reproduction

Changed (allowed scope):
* `search/kernel/flipwalk.rs`: detection, sweep, escape, `--dead-end`, `dead_ends` counter, header documentation;
* `search/kernel_reference.py`: mirror, plus the `on_dead_end` hook;
* `search/rust_kernel.py`: the `dead_end` parameter and the CLI flag;
* `tests/test_search_rust.py`: section 2.

New:
* `experiments/2026-10-06c_flipwalk_before.rs`: a verbatim copy of the old kernel, for before/after comparisons;
* scripts:
  * `experiments/2026-10-06c_kernel_throughput.py`
  * `experiments/2026-10-06c_paired_overhead.py`
  * `experiments/2026-10-06c_4x4_deadend_stats.py`
  * `experiments/2026-10-06c_analysis.py`
  * `experiments/2026-10-06c_reproduce_before_seed707.py`
  * `experiments/2026-10-06c_counterfactual_old_kernel.py`
  * `experiments/2026-10-06c_deadend_revisits.py`
  * `experiments/2026-10-06c_test_design_probes.py`
* logs: `search/runs/2026-10-06c_*.jsonl` and `search/runs/2026-10-06c_*.console.txt`;
* schemes: `search/schemes/rust-2026-10-06c/`.

Not touched: entries, tools/, schema/, README.md, CONTRIBUTING.md, START_HERE.txt, RESEARCH_LOG.md, index.json,
CITATION.cff, .zenodo.json. No git command was run.
Build products (`search/kernel/build/flipwalk.exe`, `flipwalk_before.exe`) are in the gitignored build directory.

Search compute used, all at most 8 kernel processes at once:
* throughput benchmark: 208 s wall;
* main run: 2701 s;
* afterwards: seed-707 reproduction (64 s, 1 process), counterfactual check (747 s, at most 6
  processes), and the probes (about 10 s).

The measurement itself (the main run) took 45 min, inside the 60-minute box. The follow-up runs above were
started after it, to explain its result.

Reproduce, from the repository root:
```
./.venv/Scripts/python -m unittest discover -s tests
./.venv/Scripts/python experiments/2026-10-06c_kernel_throughput.py      # timing: run on an idle machine
./.venv/Scripts/python experiments/2026-10-06c_4x4_deadend_stats.py      # 45 min, 8 processes
./.venv/Scripts/python experiments/2026-10-06c_reproduce_before_seed707.py
./.venv/Scripts/python experiments/2026-10-06c_counterfactual_old_kernel.py
./.venv/Scripts/python experiments/2026-10-06c_analysis.py
```
The best rank per seed is deterministic, apart from the time cut-off (RL-059). The counterfactual and the seed-707
reproduction are step-limited, so they are deterministic.
