# GPU Kernel Sweep — N=8 Validated + Candidate-Dependence Finding

Date: 2026-04-12 22:30 UTC
Device: NVIDIA GeForce RTX 4070 Laptop GPU (CUDA via PyTorch)

## Full N=8 sweep (best-of-all candidates)

| Bit | Best M[0] | Fill | Collisions | log2 | Macbook | Match? |
|-----|---------|------|-----------|------|---------|--------|
| 0 | 0x3d | 0x7f | 180 | 7.49 | 180 | YES |
| 1 | 0x9a | 0xff | **479** | 8.90 | 479 | YES |
| 2 | 0x7a | 0x00 | 307 | 8.26 | 307 | YES |
| 3 | 0xfc | 0xff | 133 | 7.06 | 133 | YES |
| 4 | 0x80 | 0xff | 221 | 7.79 | 221 | YES |
| 5 | 0xa9 | 0xff | 324 | 8.34 | 324 | YES |
| **6** | **0x12** | **0xff** | **1644** | **10.68** | **1644** | **YES** |
| 7 | 0x67 | 0xff | 260 | 8.02 | 260 | YES |

**All 8 bits cross-validated with macbook. 100% match.**

## Candidate-dependence discovery

Collision count varies dramatically by candidate WITHIN the same kernel bit:

| Bit | #Candidates | Best | Worst | Ratio |
|-----|------------|------|-------|-------|
| 1 | 2 | 479 | 299 | 1.6x |
| 4 | 6 | 221 | 10 | **22x** |
| 6 | 6 | 1644 | ? | TBD |

**Bit 4 detail (all 6 candidates):**
| M[0] | Fill | Collisions |
|------|------|-----------|
| 0x32 | 0xff | 10 |
| 0x80 | 0xff | **221** |
| 0x8d | 0xff | 204 |
| 0xe4 | 0xff | 188 |
| 0x70 | 0x00 | 188 |
| 0x43 | 0x7f | 169 |

## Implication

1. **Candidate selection matters enormously** — first-found can be 22x worse than optimal
2. **Must sweep all candidates** to get true collision count per kernel bit
3. **Bit 6 confirmed as universal best** at N=8 (6.3x over MSB)
4. The scaling law should use best-of-all-candidates, not first-found

## GPU performance

- PyTorch cascade DP: 42M eval/s on RTX 4070 (21x slower than NEON)
- Full N=8 sweep (first-found): 14 min total
- Multi-candidate bit-4 sweep: 10 min (6 candidates)
- Validation + multi-candidate: 30 min total
