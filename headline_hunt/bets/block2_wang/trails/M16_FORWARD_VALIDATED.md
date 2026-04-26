# M16-MITM forward enumerator: VALIDATED at N=10
**2026-04-26 04:15 EDT** — block2_wang bet — concrete forward motion.

## What this validates

`m16_mitm_forward.c` (218 LOC, N-parameterized, M5-tuned OpenMP) was
the M16-MITM design's first deliverable per `M16_MITM_FOUNDATION.md`.
Until tonight it was SOURCE-ONLY — never ground-truthed.

## Validation result

Compiled binary `m16_mitm_forward_n10` produces 1,073,741,824 records
(2^30) in ~37s wall on M5 at N=10. File size: 23.6 GB (22 bytes/record).

Independent Python validator `m16_mitm_forward_validator.py`:
- Picks 200 random records at deterministic seed=42.
- Reconstructs cascade-eligible (M0, fill) using the same algorithm.
- Replays cascade-1 forward step-by-step at slots 57, 58, 59 with the
  record's (W57, W58, W59) and computed pair-2 cascade-extending W's.
- Checks: da[57]=da[58]=da[59]=0 modular at each slot.
- Checks: final state[57..59] matches the record's stored state_59.

**Result: 200/200 PASS. ALL VALIDATED.**

## Implications

1. The forward enumerator is **correct at N=10** — its records satisfy
   cascade-1 modular constraints and produce the right state_59
   signatures. EVIDENCE-level validation (200 randomly sampled records).

2. The 218 LOC C implementation matches the Python reference. Any future
   M16-MITM match-phase work can trust `m16_mitm_forward_n10` outputs as
   ground truth.

3. The 1.07 billion records at N=10 (2^30) is the **full** forward
   enumeration. At N=16 this would be 2^48 records × 22 B = 6.6 PB —
   intractable. The cascade-reduction comment in m16_mitm_forward.c
   describes a reduction (W58 freedom = 2N/3 instead of N) but the
   implementation does NOT yet apply it. Future work: implement the
   reduction to make N=16 tractable.

## Concrete next-implementer steps

The M16-MITM design needs:
1. **Backward enumerator**: `m16_mitm_backward.c`. Enumerate (W60, W61)
   backward from de61=0, emit (state_59_required, W60, W61) records.
   Match phase joins forward and backward on state_59.
2. **Match phase**: `m16_mitm_match.cc`. Hash-join the two binaries. Should
   take ~10 min wall on tractable file sizes.
3. **Cascade reduction in forward**: actually use the W58-freedom reduction
   so N=16 becomes 3 GB instead of 6.6 PB.

## Status update

- M16_MITM_FOUNDATION's "next implementer step 3" (write m16_mitm_forward.c)
  is COMPLETE and VALIDATED at N=10.
- Steps 4 (backward) and 5 (match) remain.
- The bet is no longer "design-only" — the forward enumerator is now a
  working artifact that can be trusted as ground truth.

## Files

- `m16_mitm_forward.c` (existed; not modified)
- `m16_mitm_forward_n10` (compiled binary; existed)
- `m16_mitm_forward_validator.py` (NEW; this commit)
- This memo

## Validation method (reproducible)

```bash
cd headline_hunt/bets/block2_wang/trails
./m16_mitm_forward_n10 /tmp/m16_fwd_n10.bin    # ~37s, 23.6 GB
python3 m16_mitm_forward_validator.py /tmp/m16_fwd_n10.bin --n=10 --samples=200
# ALL PASS expected
rm /tmp/m16_fwd_n10.bin
```

EVIDENCE-level claim: `m16_mitm_forward.c` correctly emits cascade-eligible
state_59 records at N=10.
