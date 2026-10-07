# Input files of this note

Byte-for-byte copies of the three public files the proof is checked against. `verify.py` reads them from here by
default and checks each SHA-256; `verify.py --download` fetches the same files from the pinned URLs instead.

| File | Upstream (pinned commit) | SHA-256 | Licence |
|---|---|---|---|
| `2x4x5_tensor.mpl` | [dronperminov/FastMatrixMultiplication](https://github.com/dronperminov/FastMatrixMultiplication) `64f58a5e40806bc47847b11dd8aceec043fa895d`, `schemes/known/tensor/2x4x5_tensor.mpl` | `e03c7743a60f53ae21a3413af4a5f019600a12befc8ed22ffdf2baa8b0f7dd4b` | MIT, [LICENSE.FastMatrixMultiplication](LICENSE.FastMatrixMultiplication) |
| `3x3x6_tensor.mpl` | same repository and commit, `schemes/known/tensor/3x3x6_tensor.mpl` | `3e79357c5d2540e5c54c2a5f484f17009f70799b10bd45ed8e4bf893b5e223ab` | MIT, [LICENSE.FastMatrixMultiplication](LICENSE.FastMatrixMultiplication) |
| `mathematical_results.ipynb` | [google-deepmind/alphaevolve_results](https://github.com/google-deepmind/alphaevolve_results) `4226acbf237ff9ad10ba7673a2af127a2d8a5971` | `2cce2543e48c89aa3e91614272a698a0147dd2548ea11cf92f1292b7435d38ff` | software Apache-2.0 ([LICENSE.alphaevolve_results](LICENSE.alphaevolve_results)); all other materials CC BY 4.0, per the repository's README |

The files are unmodified. The licence files are copied from the same commits. The alphaevolve_results README at that
commit states: software under Apache 2.0, all other materials under CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/legalcode); copyright 2025 Google LLC. These files are not covered by the
repository's own licences; their own licences above apply.
