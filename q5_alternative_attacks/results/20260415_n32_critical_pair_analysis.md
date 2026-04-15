# N=32 sr=61 Critical Pair Analysis

Using the known sr=60 collision certificate.

## Schedule vs Cascade Mismatch at W[60]

| Quantity | Value |
|----------|-------|
| Schedule W1[60] | 0x7d4ed9a5 |
| Actual W1[60] | 0xb6befe82 |
| Schedule W2[60] | 0xb088acba |
| Cascade W2[60] | 0xea3ce26b |
| **Mismatch** | **0x5ab44ed1 (hw=16)** |

16 of 32 bits conflict between the schedule-determined and cascade-required
W2[60] values. The mismatch is roughly uniformly distributed across the word.

## Implication for sr=61

At N=8: freeing 2 bits (pair (4,5)) was enough to repair the cascade.
At N=32: 16 conflicting bits means ~8+ bits would need to be freed.
Freeing 2 bits can repair at most ~4 bits of mismatch (direct + carry).

This quantitatively confirms: sr=61 is much harder at N=32 than at N=8.
The critical pair analysis predicts that no 2-bit pair can repair the
16-bit mismatch at N=32 — sr=61 requires fundamentally more freedom.

Evidence level: VERIFIED (from known sr=60 collision certificate)
