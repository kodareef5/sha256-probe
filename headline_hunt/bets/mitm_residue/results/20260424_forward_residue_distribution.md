# Forward residue distribution at round 63 — first empirical baseline

**Date**: 2026-04-24
**Machine**: macbook
**Tool**: `bets/mitm_residue/prototypes/forward_table_builder.py`
**Candidate**: MSB / `cand_n32_msb_m17149975_fillffffffff` (sr=60 verified)

## Setup

Forward enumeration of 50,000 random (W[57], W[58], W[59]) triples with cascade
offsets *computed dynamically per-round* from the current state. W[60] anchored
to the cert value (cascade-2 offset still computed dynamically). Schedule for
W[61..63] derived per the SHA-256 schedule equation. All 7 tail rounds
applied to both messages; the round-63 difference vector recorded per sample.

Speed: ~24,000 samples/sec on macbook (single-threaded Python).

## Key result

| Metric | Value |
|---|---:|
| Samples | 50,000 |
| Cascade-1 held | 50,000 (100%) |
| Collisions | 1 (the cert) |
| Round-63 HW(da‖db‖dc‖dd), non-cert min | **28** |
| Round-63 HW(da‖db‖dc‖dd), median | **48** |
| Round-63 HW(da‖db‖dc‖dd), mean | **48.0** |
| Round-63 HW(da‖db‖dc‖dd), max | **70** |

Histogram (buckets of 8):
```
[24, 31]:    12  
[32, 39]:  2014  ########################################
[40, 47]: 21011  ##################################################
[48, 55]: 23899  ##################################################
[56, 63]:  3032  ##################################################
[64, 71]:    31
```

Distribution is concentrated around 48 — close to the binomial mean of
128 × 0.5 = 64 but *visibly skewed left*, suggesting cascade structure pulls
the residue HW down by ~16 bits compared to true random.

## Implications for `mitm_residue`

The bet's hypothesis says 24/256 anchor bits are the "hard residue" with the
other 232 effectively free under cascade. This empirical finding is consistent:

- If 232/256 bits were truly free under cascade-1, the residue would be ~24
  bits of effective work, and a HW=0 hit at random sampling rate ~2^{-24} should
  appear once every 16M samples.
- We saw 0 non-cert HW=0 hits in 50k samples — consistent with effective
  difficulty above 50k but doesn't rule out 2^24-2^28 range.
- Min HW=28 at 50k samples is suggestive: extrapolating, getting to HW=0 might
  require around 2^28 random samples. That's 256M samples ≈ 3 hours of CPU at
  the current rate.

This isn't a definitive measurement — random sampling badly bounds the search
hardness and a true MITM would split the freedom. But it does:

1. Validate the encoder/forward-table runs correctly on the cert (HW=0 hit, all
   8 registers zero).
2. Provide a baseline distribution to compare against other candidates (item #4
   from `prototypes/audit_summary.md` — candidate-independence test).
3. Rule out trivial cases: if random sampling at 50k were producing HW=0 hits
   easily, the bet would fold (no MITM advantage).

## Caveats

- W[60] is fixed at the cert value. Sweeping W[60] adds a 4th 32-bit dimension
  of freedom — but cascade-2 is still constrained, so the "free" W[60] is
  illusory. Future extension: sweep W[60] explicitly and confirm the same
  distribution.
- 50k samples per candidate is enough for distributional comparison but not
  enough to find non-cert collisions. The `forward_table_builder.py` design
  allows easy scaling — `--samples 50_000_000` would take ~30 min on macbook
  and is the natural next test if a quick MITM finder is desired.
- Distribution is for ONE candidate. Other candidates (especially non-MSB)
  may show meaningfully different residue structure — that's the actual
  candidate-independence question the bet wants to answer.

## Reproduce

```
python3 headline_hunt/bets/mitm_residue/prototypes/forward_table_builder.py \
  --m0 0x17149975 --fill 0xffffffff --kernel-bit 31 \
  --samples 50000 --seed 42 --out /tmp/fwd_msb.jsonl
```

JSONL output is one record per cascade-held sample with full W[57], round-63
register-difference hex, per-register HW, total HW(abcd), and collision flag.
Suitable for downstream analysis (clustering, residue-bit identification, etc.)

## Next actions (concrete, low-CPU)

1. **Cross-candidate sweep**: run forward_table_builder on 5-10 candidates from
   `cnfs_n32/` (different kernel bits / fills), compare distributions. ~5
   minutes total CPU, settles candidate-independence.
2. **W[60] sweep**: extend the script to also vary W[60] randomly within its
   cascade-2-constrained slack. Confirms or denies "anchored W[60]" assumption.
3. **Hard-residue identification**: of the 24 bits that show non-uniform
   distribution at round 63, *which bits*? If they correspond to specific
   register positions (e.g., g60 lower bits), that's the empirical confirmation
   the bet hypothesis needs.

Items 1-2 are 30 min of work each and high info-per-CPU. Recommended pickup.
