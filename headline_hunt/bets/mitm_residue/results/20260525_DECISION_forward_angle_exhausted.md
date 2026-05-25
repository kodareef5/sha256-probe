# 2026-05-25 DECISION: mitm_residue forward cascade angle exhausted — recommend de-prioritize

Author: kodareef5 (autonomous session). **Recommendation, not a unilateral kill**
(`mitm_hard_residue` owner = `macbook`). For the owner to action.

## TL;DR

A full day of reduced-N + N=32 probes resolved one sub-question and **refuted the
bet's headline hypothesis at the forward level**. The forward cascade free-word
angle has no remaining high-value, low-risk autonomous experiment. Recommend
**de-prioritizing `mitm_hard_residue`** (priority 5) or narrowing it to the single
unbuilt MITM-meet question (now low expected value).

## What was established (EVIDENCE, reduced-N N=8..24 + N=32; 16 commits)

1. **Schedule-realizable repair RESOLVED** (`20260525_schedule_realizable_repair.md`):
   the round-57..60 free-word interface fully admits the oracle via the prefix word
   `Wpre2[44]`; the obstacle reduces to the upstream `W44<->init2` coupling, which is
   tight + width-stable (~25-30% of round-57 state) and **is `block2_wang`'s dense
   schedule inverse**. The repair is orthogonal to gh60 (gh60 = f(w57,w58)), so
   tail-repair and residue-MITM are separable.

2. **Headline "~24-bit g60/h60 residue" REFUTED at the forward level**
   (`20260525_n32_residue_width_probe.md`): three probes agree —
   - single free word collides 1 round-63 register (dh63), the rest avalanche;
   - joint cascade (da=0 @57/58/59 + de60=0) collides 2 (dd63,dh63), 6 avalanche
     (~192-bit forward residual);
   - **gh60 distinct-count == samples to 2^22 (effective space >= ~2^34)** — gh60 is
     essentially injective in (w57,w58); no 24-bit ceiling.

## Why the forward angle is exhausted (structural)

In the cascade free-word model, once `W57,W58,W59,W60` are chosen, `W61..W63` are
schedule-determined — there is **no independent backward variable to meet on**. The
free-word freedom (~128 bits) is under-constrained against the ~192-bit post-cascade
residual, so this model **cannot reach a full sr=63 collision**, and the proposed
forward/backward MITM has no clean variable split here. The registry next-actions
(scale `cascade_mitm_full.py` forward enumeration; `gpu_mitm_prototype.py` N=8) only
exercise the forward half, which the distinct-count already shows is high-entropy —
scaling them would not produce the 24-bit residue.

## The one surviving question (low expected value)

The literal hypothesis is dead; only a **MITM-meet reading** survives — that a
forward gh60 distribution intersects a backward-required gh60 distribution in a
structured ~24-bit set. Given the measured high forward entropy (no concentration to
build on), this now looks unlikely. Settling it would require correctly building the
forward/backward match + post-meet residual (substantial, high bug-risk, needs the
cert as a validation gate) — a focused, owner-directed effort, not autonomous loop
work.

## Recommendation

- **De-prioritize / consider killing `mitm_hard_residue`.** The kill-criterion
  "effective-residue width at N=32 substantially larger than 24 bits" is *suggested*
  (forward gh60 >= ~34 bits) but not strictly met (it targets post-meet width), so
  this is a recommendation for the owner, not an auto-trip.
- If kept open, scope it to ONLY the MITM-meet measurement, owner-directed.
- The genuinely promising thread that absorbed this lead — the `W44<->init2`
  dense-schedule-inverse / neutral-set problem — lives in `block2_wang`.
