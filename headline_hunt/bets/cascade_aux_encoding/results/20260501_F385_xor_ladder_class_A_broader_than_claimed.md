---
date: 2026-05-01
bet: cascade_aux_encoding
status: F384 NARROWED — Class A includes fill=0xaaaaaaaa cands; tentative new rule is fill_bit[kbit]=1 with one outlier
parent: F384 (claimed Class A = fill=0xffffffff specifically)
type: deliverable_5_progress + iterative_refinement
compute: 3 cadical 30s LRAT runs (bit6_m024723f3 fill=7fffffff, msb_m3f239926 fill=aaaaaaaa, bit13_m4e560940 fill=aaaaaaaa)
---

# F385: F384's Class A is broader than claimed — 0xaaaaaaaa cands also ladder

## What changed

F384 claimed (n=8) that Class A is fill=0xffffffff specifically. F385
extends with 3 more data points spanning the fill-density axis:

  - fill=0x7fffffff (HW=31, 1 bit off from ffffffff): bit6_m024723f3
  - fill=0xaaaaaaaa (HW=16): msb_m3f239926, bit13_m4e560940

Plus reuse of F381-F384 proofs.

## Result — 11-cand fingerprint

```
cand                          fill          fill_HW kbit  ladder_len
bit31_m17149975               0xffffffff      32/32   31          31
bit2_ma896ee41                0xffffffff      32/32    2          31
bit3_m33ec77ca                0xffffffff      32/32    3          31
bit28_md1acca79               0xffffffff      32/32   28          31
msb_m3f239926                 0xaaaaaaaa      16/32   31          31  ← NEW Class A
bit13_m4e560940               0xaaaaaaaa      16/32   13          31  ← NEW Class A
bit6_m024723f3                0x7fffffff      31/32    6           1  ← NEAR ffffffff but NO ladder
bit11_m45b0a5f6               0x00000000       0/32   11           1
bit13_m4d9f691c               0x55555555      16/32   13           1
bit10_m3304caa0               0x80000000       1/32   10           1
bit17_m427c281d               0x80000000       1/32   17           1
```

Grouped:

| fill | fill_HW | n | ladder distribution |
|------|--------:|--:|---|
| 0xffffffff | 32 | 4 | 4×31 |
| 0xaaaaaaaa | 16 | 2 | 2×31 |
| 0x7fffffff | 31 | 1 | 1×1 |
| 0x55555555 | 16 | 1 | 1×1 |
| 0x80000000 | 1  | 2 | 2×1 |
| 0x00000000 | 0  | 1 | 1×1 |

## Findings

### Finding 1 — F384's "fill=0xffffffff specifically" axis is FALSIFIED

F384 claimed Class A is exactly fill=0xffffffff (31 of 67 cands). F385's
2 0xaaaaaaaa cands BOTH show ladder_run=31 (Class A behavior). They are
NOT in F384's claimed Class A.

So Class A is broader than F384 claimed. Project's 8th refinement of
the Class A boundary in 4 hours.

### Finding 2 — Tentative new rule: fill_bit[kbit] = 1, with one outlier

Inspecting fill_bit[kbit] for each cand:

| cand | fill | kbit | fill_bit[kbit] | ladder |
|------|------|-----:|:-:|---:|
| bit31_m17149975 | ffffffff | 31 | 1 | 31 |
| bit2_ma896ee41 | ffffffff | 2 | 1 | 31 |
| bit3_m33ec77ca | ffffffff | 3 | 1 | 31 |
| bit28_md1acca79 | ffffffff | 28 | 1 | 31 |
| msb_m3f239926 | aaaaaaaa | 31 | 1 (aaaa: bit i = 1 iff i odd) | 31 |
| bit13_m4e560940 | aaaaaaaa | 13 | 1 | 31 |
| **bit6_m024723f3** | **7fffffff** | **6** | **1** | **1 ← outlier** |
| bit11_m45b0a5f6 | 00000000 | 11 | 0 | 1 |
| bit13_m4d9f691c | 55555555 | 13 | 0 (5555: bit i = 1 iff i even, 13 is odd) | 1 |
| bit10_m3304caa0 | 80000000 | 10 | 0 | 1 |
| bit17_m427c281d | 80000000 | 17 | 0 | 1 |

10/11 cands fit the rule **`ladder iff fill_bit[kbit] = 1`**. The lone
outlier is bit6_m024723f3 (fill=0x7fffffff, kbit=6). bit 6 of 0x7fffffff
IS set (only bit 31 is cleared in 0x7fffffff), so the rule predicts
ladder, but no ladder appears.

### Finding 3 — The 0x7fffffff outlier needs explanation

bit6_m024723f3 has fill=0x7fffffff = ffffffff with bit 31 cleared. Its
kbit=6, and fill bit 6 = 1. Per fill_bit[kbit] rule it should ladder.
But the proof shows no ladder.

Possible explanations:
  - The rule isn't quite right; perhaps it depends on fill_bit[kbit] AND
    fill_bit[31] (or fill_bit at the SHA-256 round-function-coupled position).
  - It depends on some combination of fill_bit[kbit] AND m0 structure.
  - It's a CDCL search-trajectory accident: the ladder is in the proof
    but at vars I'm not looking at (different aux range).
  - bit6_m024723f3 has some structural property that suppresses the
    ladder formation (e.g., specific m0 interaction with fill).

The third explanation is plausible — my classifier searches for
contiguous arithmetic-progression triples starting at (b-a > 100) and
(c-b == 2). If bit6's ladder uses a different arithmetic step, my
classifier misses it. Worth a follow-up: compute the size-3 XOR triple
distribution for bit6 explicitly.

### Finding 4 — Phase 2D pre-injection design (re-corrected)

Class A spans more cands than F384's "fill=0xffffffff specifically"
estimate. With the tentative fill_bit[kbit]=1 rule:

  Approximation: cands with fill_bit[kbit] = 1
    (fill=0xffffffff: 31 cands, all kbits → 31 in Class A)
    (fill=0xaaaaaaaa: 6 cands, kbits ∈ {odd} → maybe 3 in Class A)
    (fill=0x55555555: 6 cands, kbits ∈ {even} → maybe 3 in Class A)
    (fill=0x80000000: 11 cands, only kbit=31 → 1 in Class A; 10 in B)
    (fill=0x7fffffff: 3 cands, kbits ∉ {31} → 3 in Class A by rule;
       but bit6 is outlier so unclear)
    (fill=0x00000000: 10 cands, no kbit → 0 in Class A; 10 in B)

If the rule holds: Class A ≈ 31 + 3 + 3 + 1 + 3 + 0 = 41 of 67 (61%).
Substantially broader than F384's 46%.

Less certain due to the bit6 outlier. The full registry sweep would
nail it down.

## What's shipped

- 3 cadical 30s runs logged via append_run.py
- 11-cand fingerprint table extending F384
- F385 falsifies F384's "fill=0xffffffff specifically" claim
- Tentative new rule: ladder iff fill_bit[kbit] = 1 (10/11 fit, 1 outlier)
- Class A may be 41 of 67 cands (61%), not 31 of 67 (46%) per F384

## Compute discipline

- 3 cadical runs logged (all UNKNOWN at 30s)
- Proofs transient in /tmp; not committed
- Real audit fail rate stays 0%
- Total session F381→F385 cadical compute: ~210s

## Open questions for next session

(a) **Investigate bit6_m024723f3 outlier**: what's structurally different?
    - Run my XOR-triple classifier with relaxed shape constraints
    - Inspect 5 more 0x7fffffff cands (only 3 in registry, so ~2 unique
      besides bit6) to see if the no-ladder is universal for this fill
    - Test with relaxed step sizes in case bit6 ladders at a different
      step

(b) **Run all 67 cands** systematically. ~33 minutes of cadical 30s
    runs. Definitive cross-cand picture. Might be worth it for next
    session.

(c) **Algebraically derive the ladder condition** from cascade-aux
    encoder source. The encoder's symmetry analysis should predict
    when the ladder forms.

## Honest summary of F381 → F385

  F381 (n=1): discovered XOR clauses
  F382 (n=3): claimed fill-bit-31 axis — falsified by F383
  F383 (n=6): corrected to fill=0xffffffff axis — provisional
  F384 (n=8): claimed sharp confirmation of fill=0xffffffff — narrowed by F385
  F385 (n=11): Class A is broader (includes some 0xaaaaaaaa cands);
               tentative rule is fill_bit[kbit]=1 with 1 outlier;
               more data needed.

8 retraction-or-narrowing iterations in 4 hours, 220s of cadical compute.
The picture sharpens incrementally. **The structural information IS
there** — that's the F381 finding holding firm. The exact axis
boundary is what keeps refining.
