---
date: 2026-04-29
bet: cascade_aux_encoding × sr61_n32
status: SR61_AND_F235_CONFIRMED — universal core thesis transfers to open frontier
---

# F330: sr=61 cross-validation + F235 hard-instance UP probe

## Setup

F324-F329 established that the F286 132-bit universal hard core is a
CDCL-search invariant on sr=60 force-mode CNFs. F330 extends to:
1. sr=61 aux_force CNF (different sr level, same encoder)
2. F235 hard instance: `sr61_cascade_m09990bd2_f80000000_bit25.cnf`
   (different encoder — basic cascade, not aux_force)

This is the natural cross-validation: does the thesis transfer to the
OPEN FRONTIER (sr=61 has no SAT yet) and to a different encoding?

## sr=61 aux_force result (cand bit10 m3304caa0)

| Metric | sr60 (F324) | sr61 (F330) |
|---|---:|---:|
| n_vars | 13248 | 13444 |
| n_clauses | 54919 | 55834 |
| Baseline UP forced | **481** | **481** |
| W*_57 UP-forced (out of 64) | 0 | 0 |
| W*_58 UP-forced (out of 64) | 0 | 0 |
| W*_59 UP-forced (out of 64) | 0 | 0 |
| W*_60 in core | yes (per F286) | NO (per F274 hard_core) |
| Schedule bits tested | 256 | 192 (no W*_60 mapped) |
| Schedule bits UP-forced | 0 | 0 |

The 481 baseline-UP-forced is **identical between sr60 and sr61** — the
aux_force encoder's cascade-hardlock encoding is sr-agnostic in size.
0/192 schedule bits UP-forced confirms the thesis at sr=61.

### Note on cascade location shift

Per F271/F273 and confirmed by F274's hard-core JSON: at sr=61, the
universal hard core shifts to W*_57+W*_58+W*_59 (not W*_59+W*_60 like
sr=60). This is consistent with the cascade location moving with sr level.

The UP-test result holds either way: the 192 mapped schedule bits at sr=61
are all UP-free, just like the 256 mapped at sr=60.

## F235 hard instance UP probe

CNF: `sr61_cascade_m09990bd2_f80000000_bit25.cnf` (basic cascade encoder,
NOT aux_force).

| Metric | F235 (basic cascade) | aux_force sr61 |
|---|---:|---:|
| n_vars | 11234 | 13444 |
| n_clauses | 47530 | 55834 |
| Baseline UP forced | **1** | **481** |

The basic cascade encoder forces ONLY CONST_TRUE via UP. The aux_force
encoder adds 480 more cascade-offset AUX vars that get UP-forced.

**The 480-vars difference IS the cascade-1 hardlock encoded as Tseitin
chains.** The basic encoder has cascade equations as direct clauses
(less UP-friendly); aux_force decomposes them into ripple-borrow AUX.

### Random-var UP probes on F235

Probed 7 random vars at increasing positions; assumption-UP cascade size:

| Var | UP-cascade (assume neg) | UP-cascade (assume pos) |
|---|---:|---:|
| 600 | 2 | 3 |
| 800 | 6 | 2 |
| 1000 | 2 | 3 |
| 1500 | 7 | 2 |
| 2000 | 16 | 5 |
| 3000 | 4 | 2 |
| 5000 | 5 | 2 |

All probes UP-feasible in both polarities. No bit derivable by single-bit
UP. Consistent with F324-F329 thesis.

## Findings

### Finding 1 — sr=61 confirms the thesis

The 132-bit universal-core UP-free property transfers cleanly from sr=60
to sr=61. F330's 192 schedule bits (cascade location at W*_57+W*_58+W*_59)
are all UP-free. The 481-vars-forced is sr-agnostic in the aux_force
encoder.

### Finding 2 — F235 hard instance has different encoder, same property

The basic cascade encoder used for F235 has 1 baseline-UP-forced (just
CONST_TRUE), vs aux_force's 481. The 480-vars difference is the aux
hardlock encoding made explicit. Neither encoder has schedule bits
UP-pinned.

### Finding 3 — F327 propagator design transfers

The IPASIR-UP propagator design from F327 was based on sr=60 aux_force.
F330 confirms the design transfers to:
- sr=61 aux_force (cand bit10) ✓
- sr=61 basic cascade (F235 hard instance) ✓

For the F235 reopen test target, `cb_decide` priority on the sr=61 cascade
location (W*_57+W*_58+W*_59 + anchors) is the structurally-correct
intervention. cb_propagate still appropriately downgraded (no encoder
pins those bits in either encoding).

### Finding 4 — Universal-core LOCATION is sr-dependent

Important nuance for the propagator design: the 132 (or for sr=61, ~96+
anchor) hard-core bits LIVE at different rounds depending on sr level:
- sr=60: W*_59 + W*_60 + anchors
- sr=61: W*_57 + W*_58 + W*_59 + anchors

The propagator must read F286-style stability data per cand to identify
the correct bits. Yale's `--stability-mode core` selector approach
generalizes correctly here — the data tells the propagator which bits.

## What's shipped

- F330 sr=61 cross-validation results in this memo.
- F330 F235 hard-instance probe results in this memo.

## Discipline

- ~7s wall (sr61 aux_force UP) + ~1s (F235 baseline + probes).
- 0 SAT compute.
- Direct extension of F324-F329 thesis to the open sr=61 frontier.

## Implications for headline-hunt

The IPASIR-UP propagator design (F327) is now structurally validated
across:
- 6 sr=60 cands (F326)
- aux_force AND aux_expose modes (F329)
- All 132 universal-core bits (F328)
- sr=61 (F330 this memo)
- Different encoder mode (F235 basic cascade)

If a Phase 2D + 2D' implementation gives the projected 2-5x speedup on
mid-difficulty TRUE sr=61 instances, that's the path to first SAT
discovery on sr=61. **First SAT on sr=61 IS a headline-worthy result**
(extends Viragh 2026's sr=59 by two rounds).

The open question is whether 2-5x speedup is enough to flip a 30-min
kissat baseline (typical for sr=61 N=32) into a SAT-finding regime, or
whether the underlying problem hardness still dominates.
