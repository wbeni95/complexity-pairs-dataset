// Experiment (RESEARCH_LOG RL-051): compile-time probe for single-file rustc. Results: rustc -O 0.87 s cold,
// 0.22 s / 0.25 s warm; -C opt-level=1 0.21 s. The toy walk degenerates (stops at 16 terms), so its
// speed is NOT representative; see RL-052 for real kernel throughput.
// Compile-time probe: a dependency-free, kernel-sized program (xorshift RNG + bitmask random walk),
// roughly the shape of a flip-graph inner loop. Build with:  rustc -O kernel.rs
use std::env;

struct Rng(u64);
impl Rng {
    fn next(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.0 = x;
        x
    }
    fn below(&mut self, n: usize) -> usize {
        (self.next() % n as u64) as usize
    }
}

#[derive(Clone, Copy)]
struct Term {
    a: u32,
    b: u32,
    c: u32,
}

fn walk(terms: &mut Vec<Term>, steps: u64, rng: &mut Rng) -> usize {
    let mut best = terms.len();
    for _ in 0..steps {
        let n = terms.len();
        if n < 2 {
            break;
        }
        let i = rng.below(n);
        let j = rng.below(n);
        if i == j {
            continue;
        }
        let (ti, tj) = (terms[i], terms[j]);
        if ti.a == tj.a {
            // flip: a(x)b(x)c + a(x)b'(x)c' = a(x)(b+b')(x)c + a(x)b'(x)(c+c') over GF(2)
            terms[i].b = ti.b ^ tj.b;
            terms[j].c = tj.c ^ ti.c;
            if terms[i].b == 0 || terms[j].c == 0 {
                let k = if terms[i].b == 0 { i } else { j };
                terms.swap_remove(k);
                best = best.min(terms.len());
            }
        }
    }
    best
}

fn main() {
    let steps: u64 = env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(10_000_000);
    let mut rng = Rng(0x9E3779B97F4A7C15);
    let mut terms: Vec<Term> = (0..64)
        .map(|k| Term { a: 1 << (k % 16), b: 1 << ((k / 4) % 16), c: 1 << ((k * 7) % 16) })
        .collect();
    let best = walk(&mut terms, steps, &mut rng);
    println!("steps={} best={} remaining={}", steps, best, terms.len());
}
