//! Flip-graph random walk over GF(2) matrix-multiplication schemes. Single file, standard library only.
//!
//! Build (about 0.2-0.9 s, see RESEARCH_LOG RL-051):   rustc -O --edition 2021 flipwalk.rs
//! Normally built and run through search/rust_kernel.py, which caches the binary and RE-VERIFIES every
//! result with the exact Python verifiers (search/gf2mm.py) before anything is saved or claimed.
//!
//! The kernel never needs the matrix multiplication tensor: flips and reductions preserve
//! sum_r a_r (x) b_r (x) c_r exactly, whatever the convention of the input scheme.
//! search/kernel_reference.py is a line-by-line Python mirror used for differential tests
//! (identical seeds must give identical results).
//!
//! Dead ends (--dead-end 1, the default; research/2026-10-06c_kernel_deadends.md): a scheme in which no two
//! terms share a factor in any position admits no flip. The walk detects this exactly and cheaply (failed
//! candidate searches are recorded per term and position; once r of the 3r cells are known to be unmatched, one
//! sweep settles the rest), and leaves at once (restart or plus transition, by the same rule as at a plateau)
//! instead of idling until the plateau. --dead-end 0 reproduces the earlier kernel's trajectories exactly.
//!
//! Full reduction (--full-reduce 1; default 0 = the earlier kernel, research/2026-10-06d_exotic_formats.md): besides
//! merging two terms that share two factors, the reduction also removes a term whenever the terms sharing one
//! factor with it have linearly dependent factors in a second position (Kauers-Moosbauer's general reduction):
//! f(x)x_g(x)y_g with x_g = sum_{s in S} x_s equals sum_s f(x)x_s(x)y_g, which is absorbed into the terms s.
//!
//! Input file (--input): first line r, then r lines "a b c" (decimal u64 bitmasks).
//! Output (stdout): "IMPROVED <rank> <step> <seconds>" lines, then
//!                  "STATS steps=<s> seconds=<t> flips=<f> rejected_weight=<w> plus=<p> restarts=<q>
//!                   dead_ends=<d> dep_reductions=<e>" (one line),
//!                  "BEST <r>", then r lines "a b c".
//! Exit codes: 0 ok, 2 bad arguments or input. A panic (e.g. an out-of-range index) exits with 101 and
//! never writes memory out of bounds: safe Rust checks every index.

use std::env;
use std::fs;
use std::process;
use std::time::Instant;

type Term = [u64; 3];

struct SplitMix64 {
    state: u64,
}

impl SplitMix64 {
    fn next(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.state;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
    fn below(&mut self, n: usize) -> usize {
        (self.next() % (n as u64)) as usize
    }
}

struct Params {
    seed: u64,
    max_steps: u64,
    max_seconds: f64,
    plateau: u64,
    slack: usize,
    max_weight: u32,
    target_rank: usize,
    dead_end: bool,
    full_reduce: bool,
}

#[derive(Default)]
struct Counters {
    flips: u64,
    rejected_weight: u64,
    plus: u64,
    restarts: u64,
    dead_ends: u64, // steps at which a dead end was detected (each triggers one restart or plus attempt)
    dep_reductions: u64, // terms removed by the linear-dependence reduction (--full-reduce 1)
}

fn has_zero(t: &Term) -> bool {
    t[0] == 0 || t[1] == 0 || t[2] == 0
}

fn weight_ok(t: &Term, cap: u32) -> bool {
    cap == 0 || (t[0].count_ones() <= cap && t[1].count_ones() <= cap && t[2].count_ones() <= cap)
}

/// Flip terms i and j, which share factor p. Over GF(2):
///   p = 0: a(x)b(x)c + a(x)b'(x)c'  ->  a(x)(b+b')(x)c + a(x)b'(x)(c'+c)
///   p = 1: a(x)b(x)c + a'(x)b(x)c'  ->  (a+a')(x)b(x)c + a'(x)b(x)(c'+c)
///   p = 2: a(x)b(x)c + a'(x)b'(x)c  ->  (a+a')(x)b(x)c + a'(x)(b'+b)(x)c
/// Returns false and changes nothing if the weight cap would be exceeded.
fn flip(terms: &mut [Term], i: usize, j: usize, p: usize, cap: u32) -> bool {
    let (ti, tj) = (terms[i], terms[j]);
    let (mut ni, mut nj) = (ti, tj);
    match p {
        0 => {
            ni[1] ^= tj[1];
            nj[2] ^= ti[2];
        }
        1 => {
            ni[0] ^= tj[0];
            nj[2] ^= ti[2];
        }
        _ => {
            ni[0] ^= tj[0];
            nj[1] ^= ti[1];
        }
    }
    if !weight_ok(&ni, cap) || !weight_ok(&nj, cap) {
        return false;
    }
    terms[i] = ni;
    terms[j] = nj;
    true
}

fn shift_after_remove(work: &mut [usize], removed: usize) {
    for w in work.iter_mut() {
        if *w == removed {
            *w = usize::MAX;
        } else if *w != usize::MAX && *w > removed {
            *w -= 1;
        }
    }
}

/// Linear-dependence reduction at term t (--full-reduce 1). For each position p (0, 1, 2) and each other position
/// q = p+1, p+2 (mod 3): the terms sharing factor p with term t (t included, in index order) are tested for a linear
/// dependence of their factors at q over GF(2), by elimination in index order. If the vector of member g reduces to
/// zero, x_g = sum_{s in S} x_s, so f(x)x_g(x)y_g = sum_s f(x)x_s(x)y_g: y_g is added to the factor at the remaining
/// position o of every s in S (in index order) and term g is removed. Returns (removed, changed) or None.
/// Groups of fewer than 3 terms are skipped (two vectors are dependent only if equal, which the merge rule covers).
fn dependency_reduction(terms: &mut Vec<Term>, t: usize) -> Option<(usize, Vec<usize>)> {
    let r = terms.len();
    for p in 0..3 {
        let key = terms[t][p];
        // Count first (no allocation): most groups have fewer than 3 members and are skipped at once.
        let size = terms.iter().filter(|t| t[p] == key).count();
        if size < 3 || size > 64 {
            continue;
        }
        let mut members = [0usize; 64];
        let mut len = 0;
        for q in 0..r {
            if terms[q][p] == key {
                members[len] = q;
                len += 1;
            }
        }
        let group = &members[..len];
        for d in 1..3 {
            let q = (p + d) % 3;
            let o = (p + 3 - d) % 3;
            let mut basis: [(u64, u64); 64] = [(0, 0); 64]; // indexed by pivot bit: (vector, mask of members)
            for (g, &idx) in group.iter().enumerate() {
                let mut v = terms[idx][q];
                let mut mask: u64 = 1u64 << g;
                let mut inserted = false;
                for bit in (0..64).rev() {
                    if (v >> bit) & 1 == 0 {
                        continue;
                    }
                    if basis[bit].0 == 0 {
                        basis[bit] = (v, mask);
                        inserted = true;
                        break;
                    }
                    v ^= basis[bit].0;
                    mask ^= basis[bit].1;
                }
                if !inserted {
                    let y = terms[idx][o];
                    let mut changed: Vec<usize> = Vec::new();
                    for (h, &other) in group.iter().enumerate() {
                        if h != g && (mask >> h) & 1 == 1 {
                            terms[other][o] ^= y;
                            changed.push(other);
                        }
                    }
                    terms.remove(idx);
                    return Some((idx, changed));
                }
            }
        }
    }
    None
}

/// Remove zero terms and merge terms sharing two factors, starting from the touched indices; with `full`, also
/// apply the linear-dependence reduction to every term that has no merge partner.
/// Deterministic LIFO worklist (mirrored exactly by kernel_reference.reduce). Returns the number of terms removed
/// by the linear-dependence reduction.
fn reduce(terms: &mut Vec<Term>, touched: &[usize], full: bool) -> u64 {
    let mut work: Vec<usize> = touched.to_vec();
    let mut deps: u64 = 0;
    while let Some(t) = work.pop() {
        if t >= terms.len() {
            continue;
        }
        if has_zero(&terms[t]) {
            terms.remove(t);
            shift_after_remove(&mut work, t);
            continue;
        }
        let mut merged = false;
        for q in 0..terms.len() {
            if q == t {
                continue;
            }
            let (a, b) = (terms[t], terms[q]);
            let k = if a[0] == b[0] && a[1] == b[1] {
                2
            } else if a[0] == b[0] && a[2] == b[2] {
                1
            } else if a[1] == b[1] && a[2] == b[2] {
                0
            } else {
                continue;
            };
            terms[q][k] ^= a[k]; // q absorbs t: two factors equal, the third ones add
            terms.remove(t);
            shift_after_remove(&mut work, t);
            work.push(if q > t { q - 1 } else { q });
            merged = true;
            break;
        }
        if full && !merged {
            if let Some((removed, changed)) = dependency_reduction(terms, t) {
                deps += 1;
                shift_after_remove(&mut work, removed);
                if t != removed && !changed.contains(&t) {
                    work.push(if t > removed { t - 1 } else { t });
                }
                for c in changed {
                    work.push(if c > removed { c - 1 } else { c });
                }
            }
        }
    }
    deps
}

/// Rank-increasing move to leave a plateau (over GF(2)):
///   a(x)b(x)c + a'(x)b'(x)c'  ->  (a+a')(x)b(x)c + a'(x)(b+b')(x)c' + a'(x)b(x)(c+c')
/// (the cross terms a'(x)b(x)c and a'(x)b(x)c' each appear twice and cancel). Requires a != a', b != b',
/// c != c', so that no new term is zero and no two of the three share two factors; otherwise the
/// reduction would merge them straight back (RESEARCH_LOG RL-052: the first version did exactly that).
fn plus_transition(terms: &mut Vec<Term>, rng: &mut SplitMix64, cap: u32, full: bool, cnt: &mut Counters) -> bool {
    let r = terms.len();
    if r < 2 {
        return false;
    }
    let i = rng.below(r);
    let j = rng.below(r);
    if i == j {
        return false;
    }
    let (ti, tj) = (terms[i], terms[j]);
    if ti[0] == tj[0] || ti[1] == tj[1] || ti[2] == tj[2] {
        return false;
    }
    let t1 = [ti[0] ^ tj[0], ti[1], ti[2]];
    let t2 = [tj[0], ti[1] ^ tj[1], tj[2]];
    let t3 = [tj[0], ti[1], ti[2] ^ tj[2]];
    if !weight_ok(&t1, cap) || !weight_ok(&t2, cap) || !weight_ok(&t3, cap) {
        return false;
    }
    terms[i] = t1;
    terms[j] = t2;
    terms.push(t3);
    let last = terms.len() - 1;
    cnt.dep_reductions += reduce(terms, &[i, j, last], full);
    true
}

fn walk(start: Vec<Term>, prm: &Params, out: &mut String) -> (Vec<Term>, u64, f64, Counters) {
    let mut rng = SplitMix64 { state: prm.seed };
    let mut terms = start;
    let mut best = terms.clone();
    let mut since: u64 = 0;
    let mut cnt = Counters::default();
    let mut cands: Vec<usize> = Vec::with_capacity(256);
    // Exact dead-end detection. Cell 3*i+p means "term i, factor position p". stamp[cell] == epoch records that
    // a candidate search in the current epoch found no other term with the same factor p as term i. The epoch
    // advances whenever the scheme may have changed (successful flip, restart, successful plus transition), so
    // every stamp of the current epoch is a true statement about the current scheme. When all 3r cells carry
    // it (unmatched == 3r), no two terms share a factor in any position: no flip exists.
    let mut stamp: Vec<u64> = vec![0; 3 * terms.len()];
    let mut epoch: u64 = 1;
    let mut unmatched: usize = 0;
    let mut swept: u64 = 0; // epoch of the last completion sweep
    let t0 = Instant::now();
    let mut step: u64 = 0;
    while step < prm.max_steps && best.len() > prm.target_rank {
        step += 1;
        if step & 0xFFFF == 0 && t0.elapsed().as_secs_f64() > prm.max_seconds {
            break;
        }
        let r = terms.len();
        let mut dead_end = false;
        if r >= 2 {
            let i = rng.below(r);
            let p = rng.below(3);
            let key = terms[i][p];
            cands.clear();
            for q in 0..r {
                if q != i && terms[q][p] == key {
                    cands.push(q);
                }
            }
            if !cands.is_empty() {
                let j = cands[rng.below(cands.len())];
                if flip(&mut terms, i, j, p, prm.max_weight) {
                    cnt.flips += 1;
                    cnt.dep_reductions += reduce(&mut terms, &[i, j], prm.full_reduce);
                    epoch += 1;
                    unmatched = 0;
                } else {
                    cnt.rejected_weight += 1;
                }
            } else if prm.dead_end {
                if stamp.len() < 3 * r {
                    stamp.resize(3 * r, 0);
                }
                let cell = 3 * i + p;
                if stamp[cell] != epoch {
                    stamp[cell] = epoch;
                    unmatched += 1;
                }
                // Once r of the 3r cells are known to be unmatched, settle the question with one deterministic
                // sweep over the other cells, in index order, stopping at the first cell that has a partner.
                // At most one sweep per epoch; it consumes no random numbers.
                if unmatched >= r && swept != epoch {
                    swept = epoch;
                    for c in 0..3 * r {
                        if stamp[c] == epoch {
                            continue;
                        }
                        let (ti, tp) = (c / 3, c % 3);
                        let key = terms[ti][tp];
                        if (0..r).any(|q| q != ti && terms[q][tp] == key) {
                            break;
                        }
                        stamp[c] = epoch;
                        unmatched += 1;
                    }
                }
                dead_end = unmatched == 3 * r;
            }
        }
        if terms.len() < best.len() {
            best = terms.clone();
            since = 0;
            out.push_str(&format!("IMPROVED {} {} {:.3}\n", best.len(), step, t0.elapsed().as_secs_f64()));
        } else {
            since += 1;
        }
        if since >= prm.plateau || dead_end {
            if dead_end {
                cnt.dead_ends += 1;
            }
            if terms.len() > best.len() + prm.slack {
                terms = best.clone();
                cnt.restarts += 1;
                epoch += 1;
                unmatched = 0;
            } else if plus_transition(&mut terms, &mut rng, prm.max_weight, prm.full_reduce, &mut cnt) {
                cnt.plus += 1;
                epoch += 1;
                unmatched = 0;
            }
            since = 0;
        }
    }
    (best, step, t0.elapsed().as_secs_f64(), cnt)
}

fn fail(msg: &str) -> ! {
    eprintln!("flipwalk: {}", msg);
    process::exit(2);
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut input: Option<String> = None;
    let mut prm = Params { seed: 1, max_steps: 1_000_000, max_seconds: 60.0, plateau: 50_000, slack: 3,
                           max_weight: 0, target_rank: 0, dead_end: true, full_reduce: false };
    let mut k = 1;
    while k < args.len() {
        let val = args.get(k + 1).unwrap_or_else(|| fail("missing value after flag"));
        match args[k].as_str() {
            "--input" => input = Some(val.clone()),
            "--seed" => prm.seed = val.parse().unwrap_or_else(|_| fail("bad --seed")),
            "--max-steps" => prm.max_steps = val.parse().unwrap_or_else(|_| fail("bad --max-steps")),
            "--max-seconds" => prm.max_seconds = val.parse().unwrap_or_else(|_| fail("bad --max-seconds")),
            "--plateau" => prm.plateau = val.parse().unwrap_or_else(|_| fail("bad --plateau")),
            "--slack" => prm.slack = val.parse().unwrap_or_else(|_| fail("bad --slack")),
            "--max-weight" => prm.max_weight = val.parse().unwrap_or_else(|_| fail("bad --max-weight")),
            "--target-rank" => prm.target_rank = val.parse().unwrap_or_else(|_| fail("bad --target-rank")),
            "--dead-end" => {
                prm.dead_end = match val.as_str() {
                    "0" => false,
                    "1" => true,
                    _ => fail("bad --dead-end (0 or 1)"),
                }
            }
            "--full-reduce" => {
                prm.full_reduce = match val.as_str() {
                    "0" => false,
                    "1" => true,
                    _ => fail("bad --full-reduce (0 or 1)"),
                }
            }
            other => fail(&format!("unknown flag {}", other)),
        }
        k += 2;
    }
    if prm.plateau == 0 {
        fail("--plateau must be positive");
    }
    let path = input.unwrap_or_else(|| fail("--input is required"));
    let text = fs::read_to_string(&path).unwrap_or_else(|_| fail("cannot read input file"));
    let mut lines = text.lines().filter(|l| !l.trim().is_empty());
    let r: usize = lines.next().and_then(|l| l.trim().parse().ok()).unwrap_or_else(|| fail("bad rank line"));
    let mut start: Vec<Term> = Vec::with_capacity(r);
    for _ in 0..r {
        let line = lines.next().unwrap_or_else(|| fail("fewer terms than the rank line says"));
        let v: Vec<u64> = line.split_whitespace().map(|x| x.parse().unwrap_or_else(|_| fail("bad factor"))).collect();
        if v.len() != 3 {
            fail("each term needs exactly three factors");
        }
        start.push([v[0], v[1], v[2]]);
    }
    if lines.next().is_some() {
        fail("more terms than the rank line says");
    }
    let mut out = String::new();
    let (best, steps, secs, cnt) = walk(start, &prm, &mut out);
    out.push_str(&format!("STATS steps={} seconds={:.3} flips={} rejected_weight={} plus={} restarts={} dead_ends={} dep_reductions={}\n",
                          steps, secs, cnt.flips, cnt.rejected_weight, cnt.plus, cnt.restarts, cnt.dead_ends,
                          cnt.dep_reductions));
    out.push_str(&format!("BEST {}\n", best.len()));
    for t in &best {
        out.push_str(&format!("{} {} {}\n", t[0], t[1], t[2]));
    }
    print!("{}", out);
}
