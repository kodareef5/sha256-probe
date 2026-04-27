# F69: cert-pin BUG FIX + re-verification — F65/F66/F67 conclusions stand
**2026-04-27 14:48 EDT**

Critical honest correction. While building the `certpin_verify.py`
fleet-coordination utility (F69 original goal), discovered that
`build_certpin.py` (used in F65/F66/F67) was pinning the WRONG
variables — `aux_W` (W1⊕W2 XOR-diff aux vars) instead of actual W1
bit variables.

After the fix: F65/F66/F67's UNSAT conclusions are correct, but the
pre-fix wall times are misleading.

## The bug

`cascade_aux_encoder.py` line 183:
```python
aux_W[r] = [cnf.xor2(w1r[i], w2r[i]) for i in range(32)]
```

`aux_W` exposed in the varmap is the XOR-DIFF auxiliary (W1⊕W2),
NOT the primary W1 bits. Pinning aux_W to a specific value forces
W1⊕W2 = (specific value), which is a STRONGER constraint than
pinning W1 alone.

For m17149975 verified collision:
- True W1[57]=0x9ccfa55e (cert), W2[57]=W1[57]+cw1 (auto via cascade)
- True W1[57]⊕W2[57] = some specific value derived from cw1
- My buggy tool pinned aux_W[57] = 0x9ccfa55e (WRONG — that's W1, not W1⊕W2)
- → Forced UNSAT for ANY W1, W2 satisfying that wrong XOR-diff

## The fix

Encoder allocates `w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]`
FIRST. Then `w2_free` (4 words). These are the primary W bit vars,
matching the existing m17149975 cert-pin layout (var 2..129 for W1).

`build_certpin.py` updated to hardcode primary W1 bit positions:
- W1[57] = vars 2..33
- W1[58] = vars 34..65
- W1[59] = vars 66..97
- W1[60] = vars 98..129

This matches the existing m17149975 certpin (commit pre-2026-04 era).

## Re-verification with FIXED tool

| cand | HW | pre-fix wall | post-fix wall | status |
|---|---:|---:|---:|---|
| **m17149975** | 0 (collision!) | UNSAT 0.142s | **SAT 0.044s** | ✓ FIX VERIFIED |
| bit2 | 45 | UNSAT 0.28s | UNSAT 0.018s | ✓ correct |
| bit10 | 47 | UNSAT 0.14s | UNSAT 0.018s | ✓ correct |
| bit13_m4e | 47 | UNSAT 0.18s | UNSAT 0.019s | ✓ correct |
| bit17 | 48 | UNSAT 3.22s | UNSAT 0.02s | ✓ correct (160× faster!) |
| bit25 | 46 | UNSAT 0.06s | UNSAT 0.019s | ✓ correct |
| bit28 HW=36 | 36 | UNSAT 0.19s | UNSAT 0.019s | ✓ correct |
| bit28 HW=33 | 33 | UNSAT 0.19s | UNSAT 0.041s | ✓ correct |

## What this means

**Good news**: F65/F66/F67's STRUCTURAL CONCLUSIONS stand. All 7
near-residuals correctly identified as UNSAT under the fixed tool.
F32 deep-min vectors ARE universally near-residuals. The
mechanism speculation (kissat penalty for cohort C → bit17 slow
even on cert-pin) was MIS-ATTRIBUTED to cohort behavior — actually
just bug-driven inefficient resolution.

**Bad news**: pre-fix wall numbers in F65/F66/F67 are misleading.
The "bit17 cert-pin slow at 3.22s" interpretation as cohort-C
structural was wrong — the buggy tool was forcing wrong constraints
that took longer to resolve. Post-fix, all near-residuals UNSAT
in 0.018-0.041s (uniform speed across cohorts).

**m17149975 SAT recovered**: the fixed tool now correctly identifies
the verified collision certificate. Sanity check passed.

## What survives from F65/F66/F67

- ✅ Cert-pin technique correctly distinguishes near-residuals (UNSAT)
  from verified collisions (SAT)
- ✅ All 7 tested F32 deep-min + yale W-witnesses are near-residuals
  (UNSAT regardless of bug, conclusion robust)
- ❌ "Cohort-C kissat penalty extends to cert-pin verification" claim
  (was bug-driven, not structural)
- ❌ Specific wall-time interpretations (use fixed-tool times instead)

## Lesson learned

When using a SAT solver as a verification tool, the FIRST sanity
check should be the verified positive case (m17149975 SAT). I built
F65 → F67 without running this sanity check on the fresh-build path.
The existing m17149975 certpin was a different toolchain (encoder
variant from earlier), so it gave correct results — masking the bug
in my new build_certpin.py.

**Discipline rule**: always verify a tool against the KNOWN POSITIVE
case before claiming negative results from it.

This is the 4th honest correction of today (after F39, F49, F55).
The pattern persists: F-series rapid iteration produces small-N
overclaims that need careful follow-up validation.

## What F69 enables (post-fix)

`certpin_verify.py` is now CORRECTLY working as a fleet-coordination
utility:

```
Usage:
  python3 headline_hunt/bets/cascade_aux_encoding/encoders/certpin_verify.py \\
      --m0 0xd1acca79 --fill 0xffffffff --kernel-bit 28 \\
      --w57 0x... --w58 0x... --w59 0x... --w60 0x...
  
  Or batch mode for sweeps over yale's online sampler outputs.
```

For yale: when the online sampler discovers a (cand, W-witness),
run certpin_verify.py — it returns SAT (HEADLINE COLLISION DISCOVERED)
or UNSAT (near-residual, design block-2 trail) in <1s.

The pipeline is now ACTUALLY validated:
1. yale online sampler → low-HW residual + W-witness
2. macbook certpin_verify.py → SAT/UNSAT in <1s
3. yale block-2 trail design (if UNSAT, the typical case)
4. macbook 2-block certpin → if SAT = HEADLINE collision

## Discipline

- 7 kissat re-verification runs (logged retroactively as F69)
- 1 sanity SAT verification of m17149975 (CONFIRMS fix)
- build_certpin.py fix shipped (4-line diff)
- certpin_verify.py shipped (utility wrapper)

EVIDENCE-level: VERIFIED. Fix is empirically validated via SAT recovery
on m17149975 + UNSAT preservation on all 7 known near-residuals.

## Concrete next moves

1. **Run F69 re-verifications via append_run.py** to update the
   runs.jsonl record (the F65/F66/F67 entries had pre-fix wall times).

2. **Coordinate with yale**: certpin_verify.py is now working. Yale
   can verify their continued online-sampler outputs in <1s per
   W-witness.

3. **Ship F69 commit** with honest retraction of pre-fix wall
   interpretations + tool fix + verification.

4. **For paper Section 4/5**: F65/F66/F67 conclusions stand (near-
   residual identification is correct). Pre-fix wall times retracted;
   use post-fix uniform 0.018-0.041s as the technique baseline.
