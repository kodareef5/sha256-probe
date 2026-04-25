# Multi-residual analysis — only de58 varies; rest are candidate-fixed constants

## What I expected vs what I found

**Expected**: bit-19's de58 compression (24 bits) might extend to other residual variables, giving multi-axis compression for cascade-DP search.

**Found**: at round 60 (the cascade boundary), the ONLY varying residual is de58 (and its shift-register equivalent dg60). All others are CANDIDATE-FIXED CONSTANTS:

| Residual var | What it shifts to | Image size |
|---|---|---:|
| de57 | dh60 (shift -3) | **1** (constant per candidate) |
| de58 | dg60 (shift -2) | **256–258k** (varies, candidate-dependent) |
| de59 | df60 (shift -1) | **1** (constant per candidate) |
| dh60 | (= de57)         | **1** (constant) |
| dg60 | (= de58)         | image matches de58 |
| df60 | (= de59)         | **1** (constant) |

## What this means

**The cascade-DP residual at round 60 has only ONE varying degree of freedom: de58 / dg60.** Everything else is determined by the candidate alone.

Why? Cascade-1 forces `da[57..60] = 0` modular. The W2-offsets at each round are functions of pair-1 state + a constant. So:
- `de_57` = dd_56 + dT1_57 = (c_56 diff, candidate-fixed) + dT1_57. T1_57 depends on W57, but dW57 = -cw57 is candidate-fixed (cascade-1 offset). So dT1_57 is candidate-fixed → de_57 candidate-fixed.
- `de_59` similarly: cascade extends through round 59, forcing dW58, dW59 to candidate-fixed offsets. dT1_58, dT1_59 candidate-fixed → de_58, de_59 candidate-fixed... wait.

Wait — de_58 is NOT candidate-fixed empirically. It DOES vary with W57 (image 256-258k). Let me re-examine.

At cascade through r=58: `da[58] = 0` modular. cw58 = some function of state57. state57 = round_step(state56, W57). Different W57 → different state57 → different cw58 → different W2[58].

But "different W2[58]" means dW58 is W57-dependent. So dT1_58 = ... + dW58 IS W57-dependent. Hence de58 = dd_57 + dT1_58 = (b_57 cascade-zero) + dT1_58 IS W57-dependent.

Vs de57: dT1_57 depends on dW57 = -cw57. cw57 is computed from state56 (NOT from state57). So cw57 is candidate-fixed. So dT1_57 is candidate-fixed. de57 candidate-fixed.

The key distinction: **the cascade chain's first link (cw57) is computed from state56 alone, but cw58 depends on state57 (which depends on W57)**. So as you walk the cascade, dependency on W57 enters at round 58 onward.

But then why is de_59 candidate-fixed? Same reason should apply: cw59 depends on state58 which depends on (W57, W58). So de59 should depend on W57, W58.

In my script, I fix W1[58] = 0. So de58 depends only on (W57, fixed W1[58]=0) = effectively just W57. And then de59 depends on (W57, W58=0, fixed cascade-extending W59) — the cascade-extending W59 depends on state58 which depends on W57. So de59 depends on W57 via state58.

But empirically de59 image = 1. That means even though de59 depends on W57 via cascade-extending W59, the TRANSFORMATION yields a FIXED de59 value across all W57.

Algebraically: de59 = dd_58 + dT1_59 = (c_58 cascade-zero diff = 0 modular) + dT1_59 = dT1_59. dT1_59 = dh_58 + dSigma1(e_58) + dCh(e_58, f_58, g_58) + dW59. With cascade extending: dW59 chosen to zero da_59. So dW59 = -(dh_58 + dSigma1 + dCh + dT2_58 [where dT2_58 = dSigma0(a_58) + dMaj(a_58, b_58, c_58)]). Cascade extending: dT2_58 = 0 (cascade gives a, b, c at r=58 zero diff). So dW59 = -(dh_58 + dSigma1(e_58) + dCh(e_58, f_58, g_58)).

Then dT1_59 = dh_58 + dSigma1(e_58) + dCh(...) + dW59 = dh_58 + dSig1 + dCh - (dh_58 + dSig1 + dCh) = 0!

So dT1_59 = 0 by cascade construction. And de59 = dd_58 + 0 = dd_58 = c_57 (shift) = 0 (cascade-zero at r=57). So de59 = 0!

That explains image=1 — and the value is 0 (zero diff). Same logic for de57 (de57 = h_56 [candidate-fixed]).

Hmm — actually de57 = d_56_diff + dT1_57. d_56 is candidate state, but its DIFFERENCE between pair-1 and pair-2 is c_55 = candidate-fixed. dT1_57 — cascade-1 forces da_57 = 0 modular = (dT1_57 + dT2_56) modular. dT2_56 is candidate-fixed. So dT1_57 = -dT2_56 candidate-fixed. de57 = dd_56 + dT1_57 = candidate-fixed + candidate-fixed = candidate-fixed. ✓

So de57, de59 are candidate-fixed by cascade construction. de58 is the unique varying one because the cascade chain lets it depend on W57 transiently (between cascade-1 holding and cascade-2 starting).

## This sharpens the structural picture

The cascade-DP at round 60 has structure:
```
Active registers:
  da57..60 = 0           (cascade-1)
  de60 = 0               (cascade-2)
  de57 = candidate-fixed (constant)
  de58 = de58(W57)       (the ONLY varying residual)
  de59 = 0               (cascade-extending forcing)
  dh60 = de57            (shift register)
  dg60 = de58            (shift register, varies)
  df60 = de59            (shift register, constant 0)
```

**Round 60 residual is essentially 1-dimensional** (just de58). Per candidate, the de58 image determines the entire cascade-DP r=60 search topology.

## Implication for headline-hunt

The earlier mitm_residue analysis identified 4 modular d.o.f. at r=63. That's accurate at r=63 (after rounds 61-63 expand the residual). But **at r=60** (the cascade boundary), the residual is only 1-dimensional.

Going r=60 → r=61 adds dT1_61's contribution (dh_60 + dSigma1(e_60) + dCh + dW_61). e_60 has zero diff (cascade-2). f_60 = e_59 (constant). g_60 = e_58 (varies — image = de58 image). dCh involves e_60 (zero diff) so dCh = 0. dW_61 is determined by message schedule.

So dT1_61 = dh_60 + dSig1(0) + dCh(0,...) + dW_61 = dh_60 + dW_61.
- dh_60 = de_57 (constant)
- dW_61 depends on candidate W's (pre-existing stuff).

Hmm dT1_61 is candidate-fixed too.

So da_61 = dT1_61 + dT2_61. dT2_61 = dSigma0(a_60) + dMaj(a_60, b_60, c_60). Cascade gives a, b, c at r=60 zero diff. So dT2_61 = 0. da_61 = dT1_61 candidate-fixed!

And de_61 = dd_60 + dT1_61 = c_59 (cascade-zero = 0) + dT1_61 = dT1_61 candidate-fixed. Same value as da_61. (Theorem 4 r=61: da_61 = de_61 modular. Now even more concrete: BOTH equal dT1_61 which is candidate-fixed.)

So at round 61, da_61 = de_61 = dT1_61(candidate-fixed). The 4 d.o.f. at r=63 must come entirely from W[61] schedule contributions (which are candidate-fixed!) plus W[62]... wait, W[62] is the message-expansion-derived word, also candidate-fixed.

Actually all the W[r] for r>60 are computed deterministically from W[44..60] via the schedule. Pair-2 uses W2[r] = W2-extension. dW[r] for r>60 depends on dW[57..60] which the cascade construction fixes (relative to W1[57..60]). So dW[r] r>60 IS W1-DEPENDENT (depends on which W1 values we picked).

OK so for r>60, dT1_r contribution involves dW[r] which depends on W1 choices. So da_61, de_61, etc. for r>60 vary with W1.

Let me re-examine the earlier 4-d.o.f. claim at r=63. Maybe the dimensions aren't all WHAT I thought.

Actually this is getting deep. Let me just ship the finding: at r=60, the cascade boundary has ONE varying d.o.f. (de58). At r=61+, the residual expands.

Maybe the right statement is: **the cascade-DP search at r=60 has 1 d.o.f. with image size ranging 2^8 to 2^18 across candidates.** That's 10 bits of variation. The 4 d.o.f. at r=63 emerges from 1 d.o.f. at r=60 + 3 more from W[61..63] schedule contributions.

Actually wait — earlier I found 4 d.o.f. at r=63. That's after running cascade-aware sampling (with specific W's at r=58, 59, 60 chosen freely). My current measurement fixes W1[58]=0 etc. So the dimensionality count differs.

This is a clean theory question that needs more thought. Let me just ship the empirical finding without over-claiming.
