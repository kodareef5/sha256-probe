# GF(2) Rank Analysis of Carry-Diff Matrix

## N=8 (260 collisions, MSB kernel)

Full carry-diff matrix: 260 rows × 392 columns (= 7 rounds × 7 additions × 8 bits)

| Category | Count | Fraction |
|----------|-------|----------|
| Invariant (constant) | 165 | 42.1% |
| Free | 227 | 57.9% |
| GF(2) rank of free | 224 | — |
| Null space dimension | 3 | — |

### Interpretation

- **165 invariant carry-diff bits**: constant across all collisions. Can be fixed as known constants.
- **3 GF(2)-linear constraints**: additional linear equations satisfied by ALL collision carry-diffs.
  These reduce the search space from 2^227 to 2^224.
- **224-dimensional nonlinear selection**: the 260 collisions are specific points in a 2^224 affine
  subspace. The selection is governed by carry propagation nonlinearity.

### +W carry-diff subspace (56 bits)

- Invariant: 2/56
- GF(2) rank: 54/54 (full rank within the free subspace)
- The +W carries are nearly independent — the GF(2) structure doesn't help with +W pruning.

### Comparison with collision count

- log2(260) = 8.0
- GF(2)-known constraints: 165 + 3 = 168
- Free DOF: 224
- Collision density in free space: 260 / 2^224 ≈ 2^{-216}

The collision manifold is an 8-dimensional nonlinear variety (log2(C) = 8) embedded in a
224-dimensional GF(2) affine subspace. The GF(2) linear structure provides 168 constraints
(43% of total bits), but the remaining 224 dimensions require nonlinear reasoning.

Evidence level: VERIFIED (exact computation from 260 exhaustively-found collisions)
