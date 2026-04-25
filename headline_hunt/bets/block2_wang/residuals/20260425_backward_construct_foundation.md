# Existing trail-engine foundation: q5/backward_construct.c

## What I found

While surveying q5_alternative_attacks for unexplored tooling that could feed block2_wang, found `q5_alternative_attacks/backward_construct.c` — a **working backward-constructive collision finder** at N=8. Already compiled and runnable as `q5_alternative_attacks/backward_construct`.

## Working state (verified 2026-04-25)

```
=== Backward-Constructive Collision Finder, N=8 ===
M[0]=0x67, fill=0xff, MSB kernel

--- Phase 1: Brute force reference ---
Brute force: 260 collisions in 8.454s

--- Phase 2: Backward-constructive solver ---
OpenMP threads: 10
  Collisions found:     260
  de61=0 hits:          16,211,828 (pass rate: 1/265)
  Triples evaluated:    16,777,216 (2^24 = 16777216)
  Time:                 0.494s
  Speedup vs BF:        17.12x

--- Phase 3: Cross-validation ---
  Matched: 260 / 260
  BF missed by BC: 0
```

**Constructive approach validated**: 17× faster than brute force AND finds the SAME 260 collisions (cross-validated, no false positives or negatives).

## The algorithm (per the script's docstring)

For each (W57, W58, W59) triple [2^24 outer loop at N=8]:
1. Compute state59 for both paths via cascade-DP
2. Compute W[61], W[63] from message schedule (fixed by w59)
3. **Solve for W60 bit-by-bit from the de61=0 constraint**:
   - `dT1_61(W60) = dh60 + dSig1(e60) + dCh(e60,f60,g60) + dW61`
   - `de61 = dd60 + dT1_61` (must equal 0)
   - At each bit k: try W60[k]=0 and W60[k]=1
   - Compute partial round 60 + partial T1_61 up to bit k
   - Track carries through all additions
   - **Prune branches where de61[k] is already determined nonzero**
4. For each valid W60: verify full collision (rounds 62-63)

That's exactly the bit-by-bit constraint-solving with carry-chain reasoning that the propagator bet's "Path A" struggled with — but here it's done STATICALLY in a tight C loop, not as a CDCL propagator.

## Why this matters for block2_wang

The block2_wang bet's BET.yaml says:
> Path forward (one of):
>   B. Build the bitcondition/trail-search engine that works BACKWARD
>      from a target low-HW residual, finding compatible (W[57..60]).
>      This is the expensive human-time path GPT-5.5 originally flagged.

**This existing N=8 implementation is the seed of that engine.** It's not yet a Wang trail engine (which involves message MODIFICATION rather than enumeration), but the BIT-BY-BIT CONSTRAINT INVERSION machinery is exactly what Wang trails need.

## Extension to N=32: the scaling barrier

At N=32 the outer loop becomes 2^96 (W57, W58, W59 each 32-bit). That's hopeless via naive scaling. But:

1. **Combined with mitm_residue's structural picture (4 d.o.f. residual variety at r=63)**, the W-search space can be partitioned by predicted residual signature. Don't try every (W57, W58, W59) — only those whose forward map produces a low-HW residual.

2. **MITM-style split**: forward enumerate (W57, W58) → cache state59 by 32-bit signature. Backward enumerate (W59, W60) → match against cached signature. 2^64 + 2^64 ≈ 2^65 work for ~2^32 expected matches.

3. **Wang-style bit conditions**: instead of exact backward search, use the bit-condition algebra to identify a SPARSE subset of W's that are likely to lead to low-HW residuals. The structural picture's 4 d.o.f. tells us which subspace to search.

## Concrete next steps for a future worker

If a future worker picks up block2_wang's path B:

1. **Read `q5_alternative_attacks/backward_construct.c`** carefully. Understand the bit-by-bit pruning + carry-chain reasoning.
2. **Port the forward+backward state computation to N=32**. The main change is wider integer arithmetic (uint32_t → already uint32_t at N=8 actually; need MASK_32 = 0xffffffff and Sigma0/Maj/sigma operations at N=32). Probably ~200 LOC.
3. **Add MITM signature caching** keyed off the 4 d.o.f. residual variety from mitm_residue. ~150 LOC.
4. **Compare against Wang bit-condition algebra**: when does the constructive backward search fall back to brute force? Where does Wang give 2-bit conditions that prune the search?
5. **Pilot on the priority candidate** (m=0x17149975, fill=0xff..ff, bit=31) at N=32 with budget 1 hour.

Total estimated effort: 1-2 weeks focused implementation. Decision gate: speedup vs brute force at N=12 (where exhaustive collision counts are still tractable).

## What's NOT this

- Not a Wang TRAIL engine — it doesn't search differential characteristics, only finds W's compatible with the cascade-DP differential.
- Not a probabilistic xdp+ engine — uses exact constraint propagation.
- Not extensible to non-cascade-DP differential paths — hardcoded to the cascade structure.

But it's a STRONG starting point for the trail-engine bet. **block2_wang's path B is no longer "from scratch"; it's "extend this working N=8 prototype to N=32."**

## What this UN-STUCKS

The block2_wang bet was BLOCKED on "no trail engine exists." That status was based on the assumption that backward search had to be built from nothing. Finding `backward_construct.c` reduces the start cost significantly.

Updating block2_wang's BET.yaml status from "blocked" → "open" is appropriate — the foundation is real, even if the N=32 extension is multi-week.

## Recommended commit

This finding should propagate to:
- block2_wang/BET.yaml — change status, link to this writeup
- mechanisms.yaml — block2_wang_residual_absorption next_action: "Extend q5/backward_construct.c to N=32. Foundation exists at N=8 with 17x speedup over brute force."
- TARGETS.md — note that the path B foundation is no longer from-scratch

Done in the next commit.
