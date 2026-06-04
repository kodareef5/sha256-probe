# Working around the sr=60→61 barrier — a 3-probe investigation (post-sweep)

After the 185-card sweep left `2^-2N` (two independent conditions, g1=0 ∧ h=0) as the one real barrier, we
tried to *work around* it. Three probes, one clean (negative) theorem.

## The barrier, precisely
sr=60→61 forces the last free word W[60] onto its schedule value: two conditions —
**g1 = w60 − sched1[60] = 0** (a per-**message**, absolute value match) AND **h = 0** (an inter-**message**,
differential compatibility). Independent (ratio ≈1.00) → `2^-2N`. The idea: *decouple* them and pay each from
a different freedom — free g1 with message neutral bits / a tunnel, leaving only h's `2^-N`.

## The arc
1. **`sr61_decouple_probe.py` (gap_rows.csv):** g1 = f(w58,w60); **h = f(w57,w58,w59), independent of w60.**
   Separate control supports DO exist — but the collision constraint (de61=0) pins the 4 free words to a
   ~`2^N` set, so within a cascade (g1,h) is a `2^-2N` joint target.
2. **`neutral_bit_probe.py`:** rank 0 over the FULL-collision-preserving subspace (free words held fixed).
   But surfaced **2 N=8 seeds** — common-mode weight-≤3 message perturbations that preserve da56=0 AND hold
   h EXACTLY while moving sched1[60], failing only the r63 output collision (incomplete "tunnels").
3. **`tunnel_probe.py` (the decisive one):** the reframing was right — the free words w57–60 are the
   collision's *solution*, not fixed inputs, so they must be **re-solved**. Over the (da56=0 ∧ h-exact)
   subspace with the tail words *released*, **corrected rank{Δsched1[60]} > 0** (4/4 @N=4, ≥4/8 @N=8) —
   sched1[60] IS freely movable. The neutral-bit "rank 0" was a search-shape artifact.

## The theorem (small-N, exhaustive @N=4 / weight-bounded @N=8; honest caveats below)
**The tunnels do NOT complete, and the reason is structural:**
moving sched1[60] (g1's target) by any amount injects a **full-width, multi-register** disturbance into the
differential at r63 (de61=da61≠0 plus 4–5 registers, magnitudes up to 242/256). The **only** differential
freedom available to reabsorb it is the **de58 channel**, which is `hw(db56) ≤ N` bits wide. The disturbance
**structurally exceeds the repair budget at every kernel width** — and crucially, **it does NOT scale with
`hw(db56)`**: widening de58 (the exotic-kernel hope) cannot help, because a single channel can never absorb a
multi-register disturbance. COMPLETION-A (re-solve free words, N=4 exhaustive) and COMPLETION-B (compensating
bits, N=8 all seeds) both give **0 g1-bits**; g1 and h reach 0 individually but never jointly.

> **Single-block sr=61 is de58-bounded, and the bound is structurally unbeatable single-block:** any lever on
> g1's absolute target creates a multi-register differential disturbance larger than the lone de58 repair
> channel can swallow, at any kernel. (This is the *quantified* form of the sweep's "the hardness IS the
> carry nonlinearity.")

**Caveats:** exhaustive only at N=4; N=8 is seeds/rank/COMPLETION-B at weight≤3; COMPLETION-A is N=4-only
(exhaustive re-solve at N≥8 is solver territory — no SAT here); compensating search ≤2 bits; MSB-kernel
cascade-DP construction. A high-weight tunnel or a different construction is not 100% excluded — but the
"multi-register disturbance vs single-channel repair" mechanism is structural and width-independent.

## Multi-block (4th probe, `multiblock_cv_probe.py`): tested — SAME WALL
The natural escape: block-1's chaining value CV (8N bits, all 8 registers) is the multi-register repair budget
single-block lacked. **The budget is real** — block-1's message reaches CV at full 8N rank, and CV steers
block-2's h over its ENTIRE range (CV→h rank = N: 8/8 @N=8, 10/10 @N=10). **But it does not rescue sr=61.**
CV's control of h is **orthogonal** to the h-vs-collision (de61=0) coupling: over hundreds of real
Davies-Meyer block-1 outputs, `h=0` and `de61=0` are INDEPENDENT 2^-N events (#(h=0 ∧ de61=0)=0 vs 0.01 exp.).
Block-2 inherits the single-block 2^-2N verbatim — it just *relocates* (g1=0, h=0, collision = three
independent 2^-N events). So the de58-overflow is a property of the **SHA-256 round function, not a
single-block artifact**: multi-block has the budget but it is the WRONG KIND of freedom (orthogonal to the
coupling, not a repair channel for it). *(Adversarial self-correction, load-bearing: a first pass spuriously
read "2^-N reachable" by feeding block-1 a FULL collision — already a hash collision — as block-2's input;
fixing to a faithful near-collision (residual HW 13–39) flipped it to SAME WALL, mirroring the repo's own
feed-forward fix.)* This **independently corroborates the repo's `block2_wang` result** (walls at ~18 rounds
over a dense post-FF residual) from the orthogonal sr=60/61 angle.

## Relaxation point (5th probe, `relaxation_point_probe.py`): round 60 is OPTIMAL — every step is 2^-2N
Could the sr-boundary sit at a cheaper round? Swept the marginal cost of forcing each free word W[57..60]
(steps 60→61, 61→62, 62→63, 63→64), N=8 and N=10, MSB + exotic kernels, intrinsic (unconditional) g1⊥h:
- **W[60] (→sr61) and W[59] (→sr62): both 2^-2N, independence ratio EXACTLY 1.0000** — no round is cheaper than 2^-2N.
- **W[58] (→sr63): 2^-2N OR impossible** — h(58) lives in a restricted image (~half the codomain, fed by the
  constant de57); 0-reachability is kernel-dependent (impossible for 7/11 kernels @N=10). de58's freedom makes
  h(58) *lumpy*, never *cheap* (ratio still 1.0000 when reachable).
- **W[57] (→sr64): the ONLY perfectly-coupled round — and a brick wall.** h(57) is a per-(kernel,M0) CONSTANT.
  Had it been 0, this would be a 2^-N seam (g1=0 ⇒ g2=0 free) — but h(57) ≠ 0 at all 24 cascade-eligible kernels
  tested. The coupling exists but lands unfavorably; round 57 is the WORST boundary (and the wrong step anyway).

So no relocation helps: **round 60 is the optimal boundary.** Two byproducts: (i) the sr-step costs are now SETTLED
by direct measurement — every reachable step is 2^-2N (ratio 1.0000), so **sr=62 = 2^-4N, sr=63 = 2^-6N**
(resolving the WE1 dissent for good); (ii) the deeper steps (W[58], W[57]) are restricted/impossible, so the
single-block cascade can't even *reach* sr=64 — **stronger than the repo's 2^-8N estimate.** (Methodological catch:
de61-conditioned ratios looked sub-1 = a false "coupling"; the *unconditional* measurement is exactly 1.0000.)

## Bottom line (5 probes, every cheap-probe stone now turned)
**Round 60 is the optimal boundary, and its `2^-2N` is structurally protected by the carry nonlinearity** at the
level of the g1 / h / collision INDEPENDENCE — single-block (de58 too narrow to repair the disturbance), multi-block
(CV has the budget but it is orthogonal to the coupling), and across all relaxation points (every reachable step is
two genuinely independent conditions). Freedom does not compose into a repair budget because the conditions are
independent. That is the precise "why" behind the difficulty; it matches the repo's own ~18-round multi-block wall
from an independent direction. The cheap (no-SAT) avenues are now exhausted; the only one they cannot close is the
**asymmetric-difference (M1≠M2) Wang-style multi-block trail — the repo's active, SAT-heavy bet.**

Files: `sr61_decouple_probe.py`, `neutral_bit_probe.py`+`neutral_bit_RESULT.md`, `tunnel_probe.py`+`tunnel_RESULT.md`, `multiblock_cv_probe.py`+`multiblock_cv_RESULT.md`, `relaxation_point_probe.py`+`relaxation_point_RESULT.md` (+`relax_gap.c`, `uncond_indep.c`, `h57_scan.c`, `h58_scan.c`).
