# macbook: sr=61 attack refined, keep hunting SAT

Reallocated macbook's 10 cores:
- Killed seeds 6, 7 brute (diminishing returns) + 0xa22dc6c7 sr=60 fluke test (13h no crack)
- Kept seeds 1-5 brute on published candidate (sr=60 fell to seed=5, so seed=5 stays!)
- Added 4 GPU-refined W1[57] prefixes from gpu-laptop's sub-cube refinement:
  * 0x03a3e566 × 2 seeds (min_hw=77, best region)
  * 0x5d24aca2 × 1 seed
  * 0x0d44b378 × 1 seed
  * 0x0d44c6bb × 1 seed

Status:
- Brute seeds 1-5: 5.4h CPU (matching sr=60's seed=5 that cracked at 12h)
- GPU-refined 0x03a3e566: 1.6h CPU
- New prefixes 5d24/0d44: just launched

The server reports strong EVIDENCE of sr=61 UNSAT at the boundary
but macbook is staying on SAT hunt. If the GPU-refined prefixes
crack it, we validate both sr=61 SAT AND the GPU pre-screening
methodology in one result.

caffeinate still alive. ELAPSED ≈ TIME from here on.
