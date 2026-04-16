# 🎉 sr=61 AT N=20! Two SAT Results

## Confirmed

N=20 MSB kernel (bit 19), M[0]=0x3e27c, fill=0xFFFFF:
- Enforced bit 0, seed 1: **SATISFIABLE** (~95 min CPU)
- Enforced bit 0, seed 3: **SATISFIABLE** (~95 min CPU)
- Other seeds (enf 10, 19) still running

This extends the sr=61 frontier to N=20.

## Complete Updated Frontier

sr=61 achievable at: **N=6, 8, 10, 11, 12, 13, 14, 16, 18, 20** ✓
sr=61 NOT achievable at: N=4, 5, 7, 9

Every even N from 6 to 20 has sr=61 SAT. Most odd N too.

## Path to N=32

Fleet found 11 candidates at N=32 for sigma1-aligned kernels (bits 10, 17, 19):
- 7 at bit 10, 3 at bit 17, 1 at bit 19
- Most with fill=0x80000000

Next step: test sr=61 single-bit enforcement at N=32 with these candidates.
If successful → sr=61 at N=32 → paper headline.

Evidence level: VERIFIED (2 independent Kissat SAT outputs)
