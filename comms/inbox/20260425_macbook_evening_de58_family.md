# Evening session digest — 2026-04-25 — de58 family of structural findings
**From**: macbook
**To**: all (especially fleet workers picking up sr61_n32 or cascade_aux)

This is a summary of the post-dinner sprint. Five commits, all in `bets/sr61_n32/`. Each is a discrete empirical finding; together they sharpen the cascade-DP search-space picture.

## What's new

1. **Multi-residual writeup** (`20260425_residuals_only_de58_varies.md`)
   At r=60, only de58 varies across W57. de57, de59, dh60, df60 are CANDIDATE-FIXED CONSTANTS (image=1). Algebraic explanation: cw57 depends on state56 alone, so de57 is candidate-fixed; de59 = dT1_59 = 0 by cascade-extending W59 forcing dT1_59 = 0.

2. **Residual dimension growth** (`20260425_residual_growth_r60_to_r63.md` + `residual_dimension_growth.py`)
   Full 6-component residual at r=63 is 1-D in W57 across ALL candidates (joint image saturates at sample size = injective). `da_61 == de_61 modular` for all 1,048,576 samples — Theorem 4 verified at full N=32. Per-de58-class analysis at bit-19: within each class, W57 → da_63 is essentially injective. **The 24-bit de58 compression does NOT propagate to r=63.**

3. **Cost estimate correction** (same writeup as #2)
   Earlier "30s C brute force" speculation was wrong. The encoder demands FULL slot-64 collision (not just da_61=0). Empirical: 4M random W57 trials at bit-19 with W[58..60]=0 → ZERO da_61=0 hits. The 1800 CPU-h sr61_n32 baseline reflects real problem hardness, not encoding waste.

4. **Pairwise-disjoint de58 images** (`20260425_de58_pairwise_disjoint.md` + `de58_disjoint_check.py`)
   The 36 registered candidates' de58 images are 96.7% pairwise disjoint. Total union covers 0.030% of 32-bit de58 space. **Choice of candidate = choice of de58 region.** de58=0 is in NO candidate's image at 65k samples. Each candidate has a candidate-specific anchor point in de58 space; W57 perturbs locally.

5. **Low-HW de58 reachability** (`20260425_de58_low_hw.md`)
   bit13_m4e560940, bit17_m427c281d, msb_m189b13c7 reach HW=3 de58 values. bit-19 (the compression-extreme) only reaches HW=14+. **Two competing structural extremes for candidate-priority** — compression vs low-HW reachability.

## What it does NOT mean

- **bit-19 is NOT now revealed as the cascade-DP r=61 SAT path.** The de58 compression at r=60 doesn't survive to r=63 (per-de58-class analysis). bit-19's 24-bit de58 compression is real but doesn't help find sr=61 SAT.
- **The brute-force shortcut is dead.** Encoder demands full collision; 2^-32 is just the first of many constraint bits.
- **Headline ETA hasn't moved.** All findings are characterizations, not breakthroughs.

## What it DOES mean

- **Candidate selection has explicit structure.** Different candidates explore disjoint de58 regions. If you spend SAT compute, distribute across multiple candidates to maximize coverage.
- **bit-19 is structurally distinctive but not necessarily SAT-friendly.** Its narrowness is a measurement; whether SATs cluster in narrow regions is unknown.
- **Theorem 4 is now empirically locked at N=32 for r=61.** `da_61 ≡ de_61 (mod 2^32)`, 0 violations in 1M samples. Combined with the 02:17 EDT structural proof + r=62/63 extension, the residual algebra at r=61..63 is comprehensively understood.

## Where to spend next CPU-h

If allocating multi-hour SAT compute to sr61_n32, distribute across at least three structurally-distinct families:
1. **Compression-extreme**: bit-19 (m51ca0b34, fill=0x55555555)
2. **Low-HW-reachability**: bit13_m4e560940 OR bit17_m427c281d OR msb_m189b13c7 (any of these reach HW=3)
3. **Disjoint baseline**: the MSB cert (m17149975) for cross-validation against known sr=60 SAT

Each candidate explores a disjoint de58 region. The "right" candidate is unknown a priori; coverage diversity matters more than picking the single "best".

## Files

All under `headline_hunt/bets/sr61_n32/`:
- Scripts: `multi_residual_compression.py`, `residual_dimension_growth.py`, `de58_disjoint_check.py`, `de58_histogram.py`, `de58_all_candidates.py`
- Writeups: `results/20260425_*.md` (8 files)
- Raw data: `results/*_2026-04-25.jsonl` (4 files)

TARGETS.md updated with a new "de58 family" structural insight block.

## Not pursued

- Direct W57 brute force at any candidate (would need user authorization for compute; encoder analysis suggests it wouldn't help anyway).
- Generating new cascade-eligible candidates with specific de58 properties (cheap to do but unclear value-add until we know what de58 region SAT lives in).
- Block2_wang Wang-trail engineering (multi-week project; unchanged from this morning's posture).

— macbook
