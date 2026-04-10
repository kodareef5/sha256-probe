# Cascade-Constrained Forward Scan Results

## Setup

`cascade_forward_scan.py` samples (W[57], W[58], W[59], W[60]) for sr=60
with cascade constraints applied:
- W[57] chosen so da57=0 (cascade 1 trigger), W2[57] = W1[57] + 0xd617236f
- W[60] chosen so de60=0 (cascade 2 trigger), W2[60] = W1[60] + C_w60 (state-dependent)
- W[58], W[59] fully random per message

500,000 samples. Candidate: M[0]=0x17149975, fill=0xffffffff.

## Results

### Minimum HW progression
| Trial | Total HW | Per-register [a..h] |
|---|---|---|
| 0 | 107 | [15, 15, 16, 15, 18, 16, 12, 0] |
| 12 | 101 | [13, 15, 15, 14, 13, 17, 14, 0] |
| 131 | 93 | [16, 10, 15, 12, 16, 12, 12, 0] |
| 492 | 86 | [11, 14, 10, 14, 10, 7, 20, 0] |
| 3,782 | 83 | [16, 15, 8, 9, 13, 9, 13, 0] |
| 30,703 | 80 | [15, 11, 10, 13, 12, 11, 8, 0] |
| 46,983 | 79 | [10, 12, 9, 13, 14, 14, 7, 0] |
| 221,618 | 77 | [8, 11, 14, 10, 11, 9, 14, 0] |
| 464,995 | **75** | [8, 14, 11, 9, 10, 9, 14, 0] |

### Distribution
- Mean: 113 (vs 128 expected for fully random)
- Mode: 112 (26,790 samples)
- Spread: 75 to 145
- Gaussian-like centered on 113

### Observation: dh63 = 0 universally
Every sample has dh63 = 0 because cascade 2 (de60=0) propagates through
the shift register: de60 → df61 → dg62 → dh63. This is built into the
constraint — not a lucky finding.

The other 7 registers are NOT zeroed by cascade alone. W[61..63] are
schedule-determined and do NOT maintain da-path zeros that cascade 1
temporarily established.

## Comparison with fleet results

| Approach | Samples | Min HW | Samples per HW reduction |
|---|---|---|---|
| GPU brute force (gpu-laptop) | 110 billion | 76 | ~1.4B per bit |
| Cascade constrained (this) | 500,000 | 75 | ~6K per bit |
| sr=61 schedule extension (yale) | 65,000 perturbation | 93 | — |

**The cascade constraints are ~220,000x more sample-efficient than
pure brute force.** Yet they still don't reach a collision (HW=0).
The minimum HW from cascade-constrained search appears to plateau
around 75-80 — similar to what pure brute force achieves at 2^37
samples.

## Interpretation

The cascade decomposition reduces the search from 2^128 to 2^64 (the
space of free W[58], W[59] for both messages). 2^64 >> 500K, so we've
barely scratched this space. But the distribution suggests the minimum
achievable HW in the full 2^64 space may still be in the 50-70 range
without additional structure — not zero.

This is consistent with the sigma1 conflict argument: ~208 per-message
sigma1 conflicts mean cascade+schedule alone can't reach collision.
Additional constraints on W[58]/W[59] are needed.

## Next steps

1. **Scale up**: run 100M samples (~1 hour on server) to see if HW < 50
2. **Gradient-guided search**: instead of random, use the best-so-far
   W[58], W[59] and perturb to reduce HW locally
3. **Decomposed search**: instead of sampling all 64 bits of W[58], W[59],
   fix some bits and enumerate the rest exhaustively

## Evidence level

**EVIDENCE**: 500K-sample scan, reproducible from `cascade_forward_scan.py`.
The minimum HW, distribution, and cascade-preservation are directly measured.
The "cascade efficient but insufficient" conclusion is consistent with
both brute-force and analytical findings.
