---
date: 2026-05-01
bet: cascade_aux_encoding
status: CROSS_CAND_PATTERN_FOUND — fill-bit-31 distinguishes structural Tseitin XOR ladder
parent: F381 (deliverable #5 unblock test on bit31)
type: deliverable_5_progress
compute: 2 cadical 30s runs (bit11 + bit2); 1 reuse of bit31 from F381
---

# F382: cross-cand Tseitin XOR analysis on cadical LRAT proofs — fill-bit-31 distinguishes the ladder

## Setup

F381 found 105+ small clauses on dW57 vars in cadical's bit31 60s LRAT
proof. F382 extends to 2 more cands to test universality:

  - bit11_m45b0a5f6 (kbit=11, fill=0x00000000, fill bit-31=0)
  - bit2_ma896ee41  (kbit=2,  fill=0xffffffff, fill bit-31=1)

Plus the F381 bit31_m17149975 (kbit=31, fill=0xffffffff, fill bit-31=1).
Each: cadical 30s with `--binary=false` LRAT proof. Parsed first 5M
proof lines; extracted size-3 derived clauses with all 4 polarity-tuples
of one of the two XOR/XNOR sets (full Tseitin XOR triples).

## Result — fill-bit-31 distinguishes 2 structural classes

| cand                          | fill       | bit31 | total XOR triples | dW57-touching | structure |
|-------------------------------|------------|-------|------------------:|--------------:|-----------|
| bit31_m17149975 (kbit=31)     | 0xffffffff | **1** | 877               | 63            | **regular ladder** |
| bit2_ma896ee41  (kbit=2)      | 0xffffffff | **1** | 884               | 65            | **regular ladder** |
| bit11_m45b0a5f6 (kbit=11)     | 0x00000000 | **0** | 854               | 26            | scattered |

### "Regular ladder" structure (bit31, bit2)

```
bit31 dW57 XOR triples (sample):
  (11886, 12622, 12624) EVEN
  (11887, 12627, 12629) EVEN
  (11888, 12632, 12634) EVEN
  ...continuing in step-5 increments

bit2 dW57 XOR triples (sample):
  (11890, 12626, 12628) EVEN
  (11891, 12631, 12633) EVEN
  (11892, 12636, 12638) EVEN
  ...same step-5 pattern
```

Pattern: triples of the form `(aux_i, dW57_a, dW57_a+2)`, where:
  - aux var i increments by 1 per triple
  - dW57 var-pair (a, a+2) increments by 5 per triple
  - All triples are EVEN polarity (encoding c = a XOR b at this position)
  - 63-65 such triples per cand in the proof (extending across the
    full dW57 row)

Plus 8+ size-2 derived clauses per cand with the form
`aux_i ⇔ dW57_(a+1)` — the middle dW57 var of each XOR triple is
equivalent to the corresponding aux var. This is a Tseitin-equivalence
chain that CDCL is rediscovering.

### "Scattered" structure (bit11)

```
bit11 dW57 XOR triples (sample):
  (710, 805, 12530)   ODD
  (5020, 5145, 12657) ODD
  (6548, 6673, 12721) ODD
  (469, 494, 12868)   EVEN
  (2029, 2355, 12906) ODD
  ...
```

No regular ladder. Triples scattered across var ranges, no consistent
arithmetic step. Mix of EVEN and ODD patterns. Only 26 dW57-touching
triples vs 63-65 for the other 2 cands.

## Findings

### Finding 1 — fill-bit-31 axis distinguishes cascade-aux structural-proof patterns

The 2 fill-bit-31=1 cands (bit31, bit2) both produce the same regular
aux-dW57 XOR ladder despite having different kbits (31 vs 2) and very
different F377 forbidden-polarity outcomes (bit31 → (0,1); bit2 → (0,0)).

The fill-bit-31=0 cand (bit11) does NOT produce the ladder, even though
its kbit (11) is in the same F377 polarity class as bit2.

This is a **DIFFERENT structural axis from F377**:
  - F377: W57[22:23] forbidden polarity is **kbit-dependent**
  - F382: aux-dW57 XOR ladder structure is **fill-bit-31-dependent**

Both real. Both axes contribute to cascade-aux's CDCL proof shape but
via independent mechanisms. F377 captured the dW57[0]/W57[22:23]
relation; F382 captures the broader aux↔dW57 ladder.

### Finding 2 — Cross-cand generalization works for fill-bit-31=1 class

For the fill-bit-31=1 cands, the XOR ladder is universal in structure:
  - Same arithmetic relations (aux_i ↔ dW57_a-pair-with-step-5)
  - Same EVEN polarity
  - Same number of triples (63-65 each)

Because var IDs differ between cands (encoder-deterministic), the
clauses themselves aren't textually identical, but their structure is.
**Pre-injection at solver init via cb_add_external_clause** could
deliver the entire 63-triple ladder for any new fill-bit-31=1 cand.

That's a Tseitin-class extension of F343's 2-clause preflight. The
expected speedup is bounded by how much CDCL spends rediscovering the
ladder; F381 noted that this happens within the first ~12k proof
lines (out of 1.4M total), so the upper bound on speedup from
ladder pre-injection is roughly 12k/1.4M ≈ 0.9% conflict reduction —
much smaller than F343's −9.10% but additive.

### Finding 3 — bit11's scattered structure is the open question

For fill-bit-31=0 cands, the ladder doesn't appear. Why? Either:
  - The ladder genuinely isn't in the encoder's Tseitin output for
    fill-bit-31=0 cands (encoder asymmetry)
  - It IS in the encoder's output but CDCL doesn't find it within 30s
    on this cand (search-trajectory accident)
  - It exists but at different var ranges I haven't located

Worth one more test: run cadical on bit13_m4d9f691c (fill=0x55555555,
fill bit-31=0, F377 (0,0) class) — does it scatter like bit11 or
ladder like bit2? That's the 4th data point that disambiguates
"fill bit-31" vs "kbit class" vs other axes.

### Finding 4 — Implications for Phase 2D propagator + F343 preflight

If F382's class structure holds:

  - For **fill-bit-31=1 cands**: extend F343 preflight to inject the
    63-triple ladder. Expected ~+0.9% additive on top of F343's −9.10%.
  - For **fill-bit-31=0 cands**: the ladder isn't there. F343 preflight
    is the right intervention.
  - The propagator's `cb_add_external_clause` should call
    `bridge_score`'s F377 polarity check (kbit-dependent) AND a new
    F382 ladder-class check (fill-bit-31-dependent). Two structural
    axes, distinct constants.

## What's shipped

- 2 cadical 30s runs (bit11 + bit2) with LRAT proof output
- 3 proofs analyzed cross-cand (bit31 from F381 + bit11 + bit2 from F382)
- This memo with the 3-cand structural fingerprint table
- One concrete next-test: bit13 fill=0x55555555 to disambiguate fill axis

## Compute discipline

- 2 cadical 30s runs (bit11, bit2), both UNKNOWN at 30s budget — logged
  via append_run.py below
- Proof files transient in /tmp (bit31: 503MB, bit11: 487MB, bit2: 514MB)
- audit_required: not applicable (proof analysis, no cnfs touched)

## Open questions for next session

(a) **Confirm with bit13_m4d9f691c**: 30s + parse, 1 min total. Either
    confirms F382's fill-bit-31 axis or exposes a different axis.

(b) **Extract the FULL ladder var-mapping for bit31 + bit2**: write a
    pre-injection clause spec that the F343 preflight tool could ship
    as an extension.

(c) **Run all 8 F347-F369 cands**: 4 min compute, gives 8 data points
    spanning F377's polarity classes × fill-bit-31 axis. Definitive
    cross-cand picture.

This is real progress on user direction's "generalized learned clause"
unit-of-progress: not a single clause that generalizes, but a
**structural CLASS** of clauses (the aux-dW57 XOR ladder) that
generalizes across fill-bit-31=1 cands.

The classification is more valuable than a single clause: it tells the
propagator HOW to mine per-cand, parameterized by fill-bit-31.
