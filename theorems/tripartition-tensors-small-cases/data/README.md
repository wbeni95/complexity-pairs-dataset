# Data of this note

| File | Content | SHA-256 | Licence |
|---|---|---|---|
| `T112_rank7.json` | 4 · T_{1,1,2} as a sum of 7 rank-one terms | `3abe699cf9167c78c1e32172343ccd18cc61fe0d0d26c9df672792afb1b99eda` | CC BY 4.0 ([LICENSE-DATA](../../../LICENSE-DATA)) |
| `T113_rank11.json` | 4 · T_{1,1,3} as a sum of 11 rank-one terms | `5d4274b46b0f4182362ecaa5b005d8fc46b3d63a3d7ff7dc17a99a0b5af8f011` | CC BY 4.0 |
| `T122_rank14.json` | 4 · T_{1,2,2} as a sum of 14 rank-one terms | `2a30f2bdbfbb4ea99bd8d28f6c93da0016a0dfb905300ab5c479a6d0d692b635` | CC BY 4.0 |

These are the project's own data, published under the repository's data licence. `verify.py` checks each SHA-256
before it reads the file.

**Format.** One JSON object per file with exactly the keys `"tensor"` (`"T_a,b,c"`), `"scale"` (`"1/4"`: the tensor
is 1/4 times the sum of the terms), `"rank"` (the number of terms) and `"A"`, `"B"`, `"C"`. These are lists of rows,
one row per coordinate of the first, second and third factor of T_{a,b,c}, each row with one integer per term.
Row i (counting from 0) of a factor of size m belongs to the i-th m-subset of [a + b + c] in increasing order of
Σ_{e ∈ S} 2^(e−1). Term r + 1 is a ⊗ b ⊗ c with a = (A[i][r])_i, b = (B[j][r])_j, c = (C[k][r])_k.
