# Fibonacci numbers: naive recursion vs DP vs fast doubling

**Type:** T2 (naive-exp → poly) · **Verification:** V2

**Problem.** Given n ≥ 0, compute F(n) mod 2^64.

| Algorithm | Time (in the value n) | Implementation |
|---|---|---|
| Naive recursion | Θ(φⁿ), φ ≈ 1.618 | [naive.py](implementations/naive.py) |
| Bottom-up DP | Θ(n) | [dp.py](implementations/dp.py) |
| Fast doubling (matrix power) | Θ(log n) | [fast_doubling.py](implementations/fast_doubling.py) |

**Why it's a pair.** The naive recursion recomputes the same subproblems over and over. Keeping each
value once (DP) removes the exponential blow-up, and the matrix identity removes another level.

**Caveat (input size).** n is a *value*. Its binary encoding has b = log₂ n bits, so in terms of the input
length the costs are Θ(φ^(2^b)), Θ(2^b) and Θ(b). The DP is polynomial in n but exponential in b.
Only fast doubling is polynomial in the input size.

**Verification.** V1: the three implementations agree with each other and with OEIS A000045.
V2: measured runtimes fit φⁿ, n and log n respectively (`python tools/validate.py --scaling -v pairs/fibonacci-naive-vs-dp`).
Exact operation counts were examined (round 2026-10-06c) and cannot be obtained by harness
instrumentation with the implementation unchanged. Fast doubling touches its input only through `bin(n)`:
one `__index__` call on an instrumented value, and none on an int subclass. It then loops over the
characters of a C-built string, and its arithmetic runs on values that start from the literals 0 and 1.
So the timing fit stays.

**Sources.** CLRS (3rd ed.), Problem 31-3 and ch. 15. Knuth, TAOCP Vol. 1, §1.2.8.
