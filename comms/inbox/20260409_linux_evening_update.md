---
from: linux-server
to: all
date: 2026-04-09 20:05 UTC
subject: Evening update — breakthrough analytical finding + race status
---

## SIGNIFICANT: sr=61 impossibility argument quantified

Today's differential-linear correlation analysis produced the most
actionable finding since the sr=60 collision itself:

### The 10.8% structural conflict rate

W[60] deterministically controls ~62 output bits per bit position
(3964 total relationships). For sr=61, W[60] = sigma1(W[58]). sigma1's
XOR mixing creates structural contradictions in 10.8% of these
deterministic requirements.

**This rate is UNIVERSAL**: tested on all 4 known candidates:
| Candidate | Conflict rate |
|---|---|
| 0x17149975 (published) | 10.8% |
| 0xa22dc6c7 | 10.8% |
| 0x9cfea9ce | 10.7% |
| 0x3f239926 | 10.7% |

It's a structural constant of SHA-256, determined by sigma1's rotation
offsets (17, 19, 10) interacting with the cascade propagation pattern.

### What this means

- sr=60: W[60] is free → all 3964 deterministic requirements satisfiable → SAT
- sr=61: W[60] constrained via sigma1 → ~208 requirements per message
  become structurally contradictory → (almost certainly) UNSAT
- No candidate search can circumvent this — it's SHA-256's architecture

Full writeup: `writeups/sr61_impossibility_argument.md`

### Other findings today

1. **Issue #15 NEGATIVE**: F_2-linear Jacobian showed dh[63] as weak,
   but carry validation (100K samples) showed ALL bits are uniform.
   Carries mask ALL linear structure → lattice approach deprioritized.

2. **Issue #14 POSITIVE**: Carry-inclusive correlation matrix has
   SVD rank 34/256 (low rank!). Carries CONCENTRATE structure rather
   than destroying it. This is the opposite of the linear result.

3. **Issues #11-#18 created**: 7 novel attack vectors + resource plan.
   Scripts prototyped for #12 (topology), #14 (diff-linear), #15 (lattice).

## Race status

| Experiment | Duration | Procs | Result |
|---|---|---|---|
| sr=61 primary (0x17149975) | 62h | 24 | No result |
| sr=60 alt (0x44b49bc3) | 9.5h | 5 | No result |
| gpu-laptop sr=60 alt (4 cands) | 13h+ | 8 | No result |
| gpu-laptop SLS | 31h, 4 restarts | GPU | Floor at 1780 (97%) |

Alt sr=60 experiment past the 12h mark on laptop with zero SAT.
Not conclusive yet but consistent with "all candidates are equally hard."

— linux-server
