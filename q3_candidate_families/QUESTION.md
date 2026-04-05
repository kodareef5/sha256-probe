# Q3: Can We Find Better Candidates?

## The Question
The current candidate family (MSB kernel, all-ones padding, M[0]=0x17149975)
is dead at sr=60. Can we find families where the barrier is weaker or absent?

## What We Know
- Only 4 MSB-kernel candidates found across 4 padding fills (2^32 M[0] scan each)
- da[56]=0 is astronomically rare: ~2 per 2^32 for MSB kernel
- Non-MSB kernels: 0 candidates found in 100M M[0] scan (all 32 bit positions)
- All known candidates have similar thermodynamic properties (HW floor ~74-77)
- M[2..15] are almost entirely unexplored (fixed at uniform fills)

## Open Questions
1. Can padding freedom (M[14], M[15]) produce candidates with lower dW[61] constant?
2. Do multi-bit kernels (e.g., bits 31+30) produce da[56]=0 candidates?
3. Can we score candidates by MITM bottleneck metrics instead of generic HW?
4. Is there a candidate family where sr=60 is easy (not just possible)?

## Strategy (from ChatGPT review)
- Free M[14] and M[15] first, then M[13]
- Score by HW(dg60) + HW(dh60), not global state HW
- Score by carry-divergence richness in depth-1/depth-2 anchor registers
- Build Pareto-optimal selector: (da[56], dW[61]_C, MITM_residue)

## Key Tools
- `42_golden_scanner.c` (modified: configurable M[2..15] fill)
- `81_kernel_sweep.c` (all 32 single-bit kernel positions)
- `83_dw61_compatibility.py` (score by dW[61] constant)
- Scripts 71, 74 (MITM anchor metrics — needs migration to this folder)

## See Also
- Issue #3 on GitHub
