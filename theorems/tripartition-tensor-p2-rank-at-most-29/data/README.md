# Data of this note

| File | Content | SHA-256 | Licence |
|---|---|---|---|
| `P2_rank29.json` | the 29-term identity 4 · P₂ = Σ_r a_r ⊗ b_r ⊗ c_r of the note | `3a46395da0783d3b315509261ea69fb4bb511ce2418a05b432e4bd0bfea32351` | CC BY 4.0 ([LICENSE-DATA](../../../LICENSE-DATA)) |

This is the project's own data, published under the repository's data licence. `verify.py` checks the SHA-256
before it reads the file.

**Format.** One JSON object with exactly these keys:

- `"tensor": "T_2,2,2"`: the tensor T_{2,2,2} = P₂ of the note;
- `"scale": "1/4"`: P₂ equals 1/4 times the sum of the terms;
- `"rank": 29`: the number of terms;
- `"A"`, `"B"`, `"C"`: three lists of 15 rows with 29 integers each. Row i (counting from 0) belongs to the
  coordinate S_i, the i-th 2-subset of {1, …, 6} in increasing order of Σ_{e ∈ S} 2^(e−1) (the table in the
  note's README); entry r (counting from 0) of a row is the coefficient of that coordinate in term r + 1.

Term r + 1 is the rank-one tensor a ⊗ b ⊗ c with a = (A[i][r])_i, b = (B[j][r])_j, c = (C[k][r])_k, and the
identity is Σ_r A[i][r] B[j][r] C[k][r] = 4 · [S_i, S_j, S_k pairwise disjoint] for all i, j, k.
