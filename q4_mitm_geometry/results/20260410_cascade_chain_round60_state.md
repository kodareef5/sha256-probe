# Cascade Chain Achieves 5/8 Zeros at Round 60

## Setup

The 4-level cascade chain forces da=0 at rounds 57, 58, 59, 60 via the
shift register. Combined with the discovery that the dW[60] for da60=0
ALSO zeros de60 (because dT2_60 = 0 when cascade 1 holds), the chain
gives us:

| Round | Zero registers | New zero |
|---|---|---|
| 56 (init) | da | da (candidate property) |
| 57 | da, db | db = a56 = 0 (shift) |
| 58 | da, db, dc | dc = b57 = 0 |
| 59 | da, db, dc, dd | dd = c58 = 0 |
| 60 | **da, db, dc, dd, de** | de = 0 (W[60] chosen for both da60=0 and de60=0) |

**5 of 8 register diffs are zero at round 60** for ANY 4-level cascade
chain tuple.

## The remaining problem

After round 60, W[61..63] become schedule-determined:
- W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
- W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
- W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]

These schedule-derived W values are NOT chosen to maintain the cascade.
Random cascade-chain tuples produce HW at round 63:

```
After round 56: da= 0 db=17 dc=13 dd=11 de=16 df=19 dg=14 dh=14  total=104
After round 57: da= 0 db= 0 dc=17 dd=13 de= 9 df=16 dg=19 dh=14  total=88
After round 58: da= 0 db= 0 dc= 0 dd=17 de=14 df= 9 dg=16 dh=19  total=75
After round 59: da= 0 db= 0 dc= 0 dd= 0 de=19 df=14 dg= 9 dh=16  total=58
After round 60: da= 0 db= 0 dc= 0 dd= 0 de= 0 df=19 dg=14 dh= 9  total=42  <- 5/8 zero
After round 61: da=18 db= 0 dc= 0 dd= 0 de=17 df= 0 dg=19 dh=14  total=68  <- starts breaking
After round 62: da=16 db=18 dc= 0 dd= 0 de=17 df=17 dg= 0 dh=19  total=87
After round 63: da=13 db=16 dc=18 dd= 0 de=17 df=17 dg=17 dh= 0  total=98
```

The cert achieves 0 at round 63 by choosing W[57..60] such that the
schedule-derived W[61..63] CONTINUE the cascade (specifically, they
must zero da61, da62, da63 and de61=df60=0 propagation).

## What we need

To extend the cascade chain past round 60, we need to **constrain
W[57..59] such that the schedule-derived W[61..63] satisfy specific
conditions on the round-61, 62, 63 states.**

This is no longer a free-word problem — W[61..63] are functions of
W[57..60] via sigma1. The constraints become:
- da61 = 0: depends on W[61] = sigma1(W[59]) + const
- da62 = 0: depends on W[62] = sigma1(W[60]) + const
- da63 = 0: depends on W[63] = sigma1(W[61]) + const

Each of these is a constraint on W[57..60] via the schedule arithmetic.

## Potential constructive approach

Use the cascade chain for rounds 57-60 (4 free W1 words deterministically
producing W2). Then for rounds 61-63, COMPUTE which (W1[57..60]) tuples
satisfy the schedule-derived conditions. This is a constraint propagation
problem on the 128-bit input space.

If the constraints on W[61..63] are independent of W[57..60], we'd find
~2^96 solutions. But the schedule rules couple them, so the actual
number is much smaller.

The cert is ONE solution. If we can characterize the solution set
algebraically, we have a constructive collision finder.

## Evidence level

**EVIDENCE**: Direct measurement of state at every round for cascade-chain
tuples. The 5/8 zero at round 60 is mechanical and verified. The 5/8 → 0/8
break at round 61 is also verified. The cert achieves a different
trajectory by choosing W[57..60] specifically.
