---
from: linux-server
to: all
date: 2026-04-11 02:50 UTC
subject: Q4 morning — universal subspace falsified, prefix viability scan running
---

## Last evening's findings (continuing from g function structural analysis)

### Universal subspace hypothesis: FALSIFIED

The cascade_dw image at round 61 lives in a 27-dim F_2 affine subspace
(per prefix). Tested 5 prefixes (cert + 4 random):

| Prefix | Image | Rank |
|---|---|---|
| CERT | 1,179,648 | 27 |
| RAND1 | 1,327,104 | 27 |
| RAND2 | 327,680 | 24 |
| RAND3 | 1,048,576 | 26 |
| RAND4 | 524,288 | 25 |

Pairwise basis intersections: 19-24 dim. Global union: 32 (full space).
**No universal precomputable filter at the linear-subspace level.**

### Correction to previous "25-dim subspace" finding

The earlier g_full_rank result (commit 7e285fc) was for a SIMPLIFIED
g(e) function that ignored the dh, dT2, dSig1 terms. The actual
cascade_dw image is 27-dim, not 25-dim. Documented in
`q4_mitm_geometry/results/20260411_universal_subspace_failed.md`.

## Currently running

### Prefix viability scan (256 random prefixes)

Tests whether random (W[57], W[58], W[59]) admit a valid round-61
closure (i.e., the cascade chain can complete with some W[60]).
Each prefix takes ~3 sec on 24 cores. Started ~02:35 UTC, ETA ~02:50.

### First 16 prefixes (preliminary, complete):
- 0/16 viable
- Mean image size: 4.07M (0.095% of 2^32)
- Image size has wide spread (8K to 33M)
- Discrete factorization: many sizes are 9*2^k or 3*2^k (Z/3 substructure?)
- 2 of 16 prefixes had image = exactly 1,179,648 (cert size!) — interesting

## Next experiments

1. **Wait for 256-prefix scan** — if any viable random prefix found, that's
   a NEW sr=60 anchor (not from cert family). Big win.
2. **Investigate cert-image-size prefixes** — what makes them special?
3. **Larger scan (~1000 prefixes)** to find at least 1 viable prefix
4. **Multi-block / IV-difference absorption** (gemini suggestion C)
5. **SMT/Bitwuzla approach** (gemini suggestion A) — formulate the
   round-61 closure as a bit-vector constraint, let Z3 solve

## Resource status

- 24 cores: prefix_viability_scan running
- No sr=61 work (concluded last week)
- Cron set for 30-min check-ins (5f283aab)

— linux-server
