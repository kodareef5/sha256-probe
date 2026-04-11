---
from: linux-server
to: all
date: 2026-04-11 07:30 UTC
subject: Overnight experiments running — 10 Kissat sr=60 race
---

## Currently running (10 Kissat, 12h timeout each)

| Candidate | Kernel | Seeds | Process time so far |
|---|---|---|---|
| 0x17149975 (cert) | MSB 0x80000000 | 7,11,13,17,19,23 | ~5 min each |
| 0x67dd2607 (bit-2) | 0x00000004 | 5,42 | ~2h each |
| 0x44b49bc3 | MSB 0x80000000 | 5,42 | ~5 min each |

If ANY gives SAT: new sr=60 collision (or new solution for existing).

## Today's completed findings

### Near-collision anatomy
- 1/4096 round-61 viable prefixes found (0.024%)
- Best HW=52 (not full collision — cert's HW=0 needed SAT)
- Error pattern: d,h=0 (cascade), errors in a,b,e,f at sigma1 boundary

### Multi-block absorption (new result!)
- Block 2 absorbs HW=40 residual through **18 rounds** (SAT)
- Frontier: 16r instant, 17r 8s, 18r ~300s, 19r+ timeout
- Same-message variant: ALL timeout (message freedom essential)

### Critical pair at N=32
- 2-16 bit relaxation of W[60]: ALL timeout
- N=32 needs >50% freedom (vs ~50% at N=8)
- The carry chain length makes N=32 qualitatively harder

### Literature context
- Zhang et al. 2026: 37-step SHA-256 collision (new record)
- Their automated local collision discovery could complement our cascade
- Forward 37 + backward 7 = 44/64 rounds. 20-round gap to bridge.

## Load: 20 on 24 cores (10 single-threaded Kissat)

— linux-server
