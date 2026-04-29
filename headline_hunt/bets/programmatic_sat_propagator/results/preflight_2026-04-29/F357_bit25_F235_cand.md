---
date: 2026-04-29
bet: programmatic_sat_propagator × sr61_n32
status: F235_PREFLIGHT — F343 mining on F235 reopen-target cand
---

# F357: F343 preflight on F235 hard-instance cand m09990bd2/bit25 sr=61

## Setup

F235 is the programmatic_sat_propagator bet's reopen-target hard instance:
sr=61 cascade encoder, cand m09990bd2/bit25/fill=0x80000000, kissat 562s
and cadical 848s timeouts. F343 preflight on this cand at sr=61 force-mode
gives the clause library that injection should pre-load.

## Result

```
=== F343 preflight on aux_force_sr61_n32 m09990bd2/bit25/fill=0x80000000 ===
n_vars=13494, clauses=56002
wall: 20.17s

dW57[0] forced=0 (inject lit -12643)         ← Class 1a-univ, opposite polarity
(dW57[22], dW57[23]) forbidden=(0, 0)         ← Class 2
inject [12665, 12666]
```

## Combined cross-cand cross-sr cross-mode table (F354+F355+F356+F357)

| Cand    | M[0]      | fill        | kernel-bit | dW57[0] forced | W57[22:23] forbidden |
|---------|-----------|-------------|:---:|:---:|---|
| bit0    | 8299b36f  | 0x80000000  | 0  | 0 | (0, 1) |
| bit10   | 3304caa0  | 0x80000000  | 10 | 0 | (0, 1) |
| bit11   | 45b0a5f6  | 0x00000000  | 11 | 1 | (0, 0) |
| bit13   | 4d9f691c  | 0x55555555  | 13 | 0 | (0, 0) |
| bit17   | 427c281d  | 0x80000000  | 17 | 1 | (0, 1) |
| **bit25** | **09990bd2** | **0x80000000** | **25** | **0** | **(0, 0)** |
| bit29   | 17454e4b  | 0xffffffff  | 29 | 1 | (0, 0) |
| bit31   | 17149975  | 0xffffffff  | 31 | 1 | (0, 1) |

## Findings

### Finding 1 — F340 hypothesis "fill bit-31 → polarity" is REFUTED

F340 proposed: fill bit-31 SET → forbidden=(0, 1); UNSET → (0, 0).

Counter-examples from F357 + F356:
- bit25 fill=0x80000000 (bit-31 SET) → forbidden=(0, 0) — should be (0,1) per F340
- bit29 fill=0xffffffff (bit-31 SET) → forbidden=(0, 0) — should be (0,1) per F340

Per kernel-bit position:
- forbidden=(0, 1): kernel-bits {0, 10, 17, 31}
- forbidden=(0, 0): kernel-bits {11, 13, 25, 29}

Possible refined hypothesis: kernel-bit determines polarity. Kernel-bits
{0, 10, 17, 31} vs {11, 13, 25, 29} — no obvious arithmetic pattern
(the {11,13,25,29} set has odd parity at... hmm, 11+13+25+29 = 78; 0+10+17+31=58; both don't have a clean modular property).

Refined Refined hypothesis: polarity is a non-trivial function of
(M[0], fill, kernel-bit) jointly. F340's simpler hypothesis was wrong.

### Finding 2 — F357 confirms F235 cand has same constraint structure

bit25 m09990bd2 has Class 1a-univ + Class 2 like all 7 other cands.
F343 preflight gives 2 mined clauses for F235's cand. These are
ready for IPASIR-UP injection on F235.

### Finding 3 — Phase 2D propagator design unchanged but more empirically grounded

The 8-cand table now spans:
- 8 distinct cands
- 4 distinct kernel-bit positions ({0, 10, 11, 13, 17, 25, 29, 31})
- 4 distinct fill values ({0x00000000, 0x55555555, 0x80000000, 0xffffffff})

The F343 mining works for ALL of them. Phase 2D propagator can ingest
any cand's mined clauses uniformly.

### Finding 4 — F235 reopen criterion path

For F235 hard instance specifically:
- F343 preflight: 20s, 2 mined clauses extracted (this memo).
- F352-style injection test on F235 itself (basic cascade encoder, not
  aux_force): would need to map var IDs from aux_force preflight to
  F235's basic cascade var IDs. Non-trivial.
- Alternative: re-mine on F235 directly using a custom probe. ~30 min
  setup work + 20s mining.

If F235 injection gives ~10% conflict reduction, that translates to
~85s saved on cadical's 848s baseline, possibly flipping it to UNSAT
discovery within budget.

## Compute

- 20.17s wall (5 cadical 5s probes).
- 0 long compute.

## What's shipped

- F357 preflight JSON for m09990bd2/bit25 sr=61 force-mode.
- This memo.

## Concrete next moves

(a) **Re-mine F343 directly on F235's basic-cascade CNF**: requires
    deriving dW57 var IDs from F235 CNF structure (no varmap available).
    ~30 min work.

(b) **Phase 2D propagator C++ implementation**: 10-14 hr build window.
    Would integrate the F343 preflight + cb_add_external_clause hook +
    test on F235 + measure speedup.

(c) **Sweep more sr=61 cands with F353-style 4h kissat**: extend
    F353's bit29 sr=60 verification methodology to sr=61. If any sr=61
    SAT exists, headline-worthy. (Requires user approval per
    multi-hour-compute rule.)

The F357 preflight clauses are now in `preflight_2026-04-29/` for any
future propagator implementation to use.
