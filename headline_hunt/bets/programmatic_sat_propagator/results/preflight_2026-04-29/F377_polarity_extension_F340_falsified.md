---
date: 2026-04-30
bet: programmatic_sat_propagator × cascade_aux_encoding
status: F340 HYPOTHESIS FALSIFIED — W57[22:23] forbidden polarity is NOT tied to bit-31-of-fill
parent: F375 (generated bit2/bit13_m4e/bit28 aux variants)
---

# F377: F343 preflight on F375 cands → F340 polarity hypothesis FALSIFIED

## Setup

F340 (2026-04-29) tested W57[22:23] CDCL UNSAT polarity across 6 cands
and proposed: **"bit-31-of-fill SET → forbidden=(0,1); bit-31-of-fill
CLEAR → forbidden=(0,0)"**. F348/F368/F369 used this as a per-cand
polarity-aware injection rule.

F375 generated aux_force_sr60 CNFs for 3 new cands (bit2_ma896ee41,
bit13_m4e560940, bit28_md1acca79). All 3 have **fill bit-31 SET**, so
F340 predicts forbidden=(0,1) for each.

F377 runs F343 preflight on each of the 3 new cands to test the
prediction.

## Result

```
F377 NEW (3 cands, all fill bit-31 SET):
  cand                          fill         b31  kbit  dW57[0]  W57[22:23]
  bit2_ma896ee41_fillffffffff   0xffffffff    1     2     1        (0, 0)
  bit13_m4e560940_fillaaaaaaaa  0xaaaaaaaa    1    13     1        (0, 0)
  bit28_md1acca79_fillffffffff  0xffffffff    1    28     0        (0, 0)
```

**All 3 give forbidden=(0,0). F340 predicted (0,1) for all 3.**

## F340 hypothesis FALSIFIED

The bit-31-of-fill rule does not predict the polarity. Combining F340's
6 cands with F377's 3 = 9-cand panel (bit13_m4d9f691c and bit13_m4e560940
both give (0,0), so they're treated as one kbit data point):

```
kbit   cands                                       polarity     fill bit-31
-----  ------------------------------------------- -----------  -----------
   0   bit0_m8299b36f_fill80000000                  (0, 1)        SET
   2   bit2_ma896ee41_fillffffffff      [F377]      (0, 0)        SET
  10   bit10_m3304caa0_fill80000000                 (0, 1)        SET
  11   bit11_m45b0a5f6_fill00000000                 (0, 0)        CLEAR
  13   bit13_m4d9f691c_fill55555555                 (0, 0)        CLEAR
  13   bit13_m4e560940_fillaaaaaaaa     [F377]      (0, 0)        SET
  17   bit17_m427c281d_fill80000000                 (0, 1)        SET
  28   bit28_md1acca79_fillffffffff     [F377]      (0, 0)        SET
  31   bit31_m17149975_fillffffffff                 (0, 1)        SET
```

**Polarity by kbit:**

| polarity | kbit set                | n |
|----------|-------------------------|--:|
| (0, 1)   | {0, 10, 17, 31}         | 4 |
| (0, 0)   | {2, 11, 13, 28}         | 4 (5 cands, 2 bit13 variants) |

The polarity is **kbit-dependent**, not fill-dependent. fill bit-31
varies independently of the polarity outcome (bit11 has fill bit-31
CLEAR, bit13_m4d9f691c has fill bit-31 CLEAR, but bit13_m4e560940 has
fill bit-31 SET — all give (0,0) because they share kbit ∈ {11, 13}).

## What was actually empirically true in F340

Looking at F340's 6-cand panel in retrospect:
  - 4 cands had kbit ∈ {0, 10, 17, 31} AND fill bit-31 SET
  - 2 cands had kbit ∈ {11, 13} AND fill bit-31 CLEAR
F340 saw the (kbit set, fill bit-31) correlation but couldn't disambiguate
which was the load-bearing variable. F377 disambiguates: **kbit is the
load-bearing variable**.

This makes structural sense: the W57[22:23] CDCL UNSAT pair is derived
from the cascade-1 hardlock at round 60, which propagates back through
the schedule recurrence to round 57. The kernel-bit determines WHICH
bit-position is the active difference; the fill determines the
non-diff-bit values. Polarity at round 57 should depend on the round-60
cascade structure, which is parameterized by the kernel position
(kbit), NOT by the message fill (which is identical across W1/W2 except
at the kbit position).

## Pattern in {0, 10, 17, 31} vs {2, 11, 13, 28}

The (0,1) kbit set: {0, 10, 17, 31}
The (0,0) kbit set: {2, 11, 13, 28}

Looking at HW of kbit (5-bit binary):
  0  = 00000  HW=0
  10 = 01010  HW=2
  17 = 10001  HW=2
  31 = 11111  HW=5
  2  = 00010  HW=1
  11 = 01011  HW=3
  13 = 01101  HW=3
  28 = 11100  HW=3

(0,0) cands: HWs all ODD (1, 3, 3, 3).
(0,1) cands: HWs are 0, 2, 2, 5 — three EVEN, one ODD (kbit=31).

Near-pattern: HW(kbit) ODD → (0,0). The (0,1) set has an outlier at
kbit=31 (HW=5, odd) but otherwise matches HW(kbit) EVEN. **Tentative
hypothesis: polarity is determined by parity of HW(kbit) for kbit ≠ 31;
kbit=31 (full 5-bit-set) is structurally exceptional.**

This is testable — adding more cands at kbits we haven't probed yet
(kbits 1, 3, 4, 5, 6, 7, 8, 9, 12, 14, 15, 16, 18..27, 29, 30) would
either confirm or break the parity rule.

## Implications

### F348/F368/F369 conflict-reduction numbers stand

The F377 finding doesn't invalidate any of F348/F368/F369's conflict-
reduction measurements. Those measured speedup of injection ON THE
SAME CAND it was mined from, with per-cand polarity from per-cand
mining. The numbers (mean −9.10% σ=2.68% at 60s, F369) are
empirically valid regardless of WHY each cand has its specific polarity.

### F340's narrative needs softening

F340 was titled "W57[22:23] CDCL UNSAT is universal-with-flip across
cands" with the bit-31-of-fill flip rule. The "universal" part stands
(W57[22:23] is forbidden in all probed cands). The "flip rule" is
falsified — the flip is by kbit, not by fill bit-31.

I won't retract F340 since the broader UNSAT-with-flip claim holds.
But the F340 memo should get a soft revision pointing to F377.

### Phase 2D propagator design unchanged

Per F356 (mining is mode-invariant) + F354/F355 (sr-invariant), the
Phase 2D propagator's per-cand F343 mining at solver init produces
the right polarity automatically. **Nothing changes** in the propagator
design — the F377 falsification only affects the explanatory narrative,
not the operational rule.

### Concrete next moves

(a) **Test the HW(kbit) parity hypothesis**: run F343 preflight on
    cands at unprobed kbits (especially HW=4, 5 to disambiguate kbit=31).
    Currently 0 cands have HW(kbit) = 4 in the probed set. ~20s × N
    cands compute per probe.

(b) **Algebraically derive polarity from cascade-1 round-60 structure**.
    F377 frames it as a kbit-dependent property; the natural follow-up
    is "given kbit, what's the algebraic formula for the W57[22:23]
    polarity at round 57?" That's a paper-shaped derivation, not
    compute work.

(c) **Update F340 memo** with a soft revision pointing to F377.

## What's shipped

- This memo
- 3 preflight JSONs in `/tmp/F377_*_preflight.json`
- `F377_polarity_extension.json` aggregate in
  `bets/programmatic_sat_propagator/results/preflight_2026-04-29/`
- A 9-cand kbit-dependent polarity table that future per-cand mining
  can cross-reference
- A falsified F340 hypothesis with a tentative replacement (HW(kbit)
  parity) that's testable

## Compute discipline

- 3 F343 preflight runs × ~20s = ~60s total wall
- Each preflight ran cadical 5s × 5 probes = 25s probe budget per cand
- 0 runs.jsonl entries (preflight runs are short probes, the F343 tool
  doesn't log via append_run.py, matching F343-F356 historical pattern)

## Cross-machine implication

For yale: F340's "polarity from fill" was a load-bearing claim in the
acknowledgement message I sent yesterday
(`comms/inbox/20260430_macbook_to_yale_F367_chain_thanks_F378_enabled.md`).
That message's "F340: cross-cand sweep of the W57[22:23] pair... fill
bit-31 SET → (0,1)" line is now superseded by F377's kbit-dependent
finding. The W57[22:23] bridge-clause target yale isolated in F384 still
stands; the cross-cand polarity attribution in my message needs a
correction-line in the next yale comms.
