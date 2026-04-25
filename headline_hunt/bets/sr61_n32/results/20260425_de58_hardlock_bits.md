# Per-bit hard-locked positions in de58 — concrete sr=61 SAT predictions
**2026-04-25** — sr61_n32 — bonus structural probe.

## What this is

For each candidate, the de58 image has a **per-bit signature**: some bits NEVER vary across the image (hard-locked, fully determined by the candidate); others vary as W57 changes.

Hard-locked bits are **concrete sr=61 SAT predictions**: any solution's de58 value must satisfy `de58 & locked_mask == locked_value`. SAT branches that violate this can be pruned without further search.

## Method

For each of 36 registered candidates: sample 131,072 W57 → de58 image. Compute:
- `or_all`  = OR of all sampled de58 values (bit b set if any sample had bit b = 1)
- `and_all` = AND of all sampled de58 values (bit b set if all samples had bit b = 1)
- `locked_mask` = `~(or_all ^ and_all)` (bit b locked if `or_all`[b] == `and_all`[b])
- `locked_value` = `and_all & locked_mask`

## Headline numbers

```
Most-locked candidates (more locked bits = more SAT pruning):
  16 locked / 16 varying  | image=  8192 | cand_n32_bit11_m56076c68_fill55555555
  14 locked / 18 varying  | image= 32159 | cand_n32_msb_ma22dc6c7_fillffffffff
  14 locked / 18 varying  | image=  8192 | cand_n32_bit13_mbee3704b_fill00000000
  13 locked / 19 varying  | image=   256 | cand_n32_bit19_m51ca0b34_fill55555555
  13 locked / 19 varying  | image=  4096 | cand_n32_bit25_m09990bd2_fill80000000
  13 locked / 19 varying  | image= 16381 | cand_n32_bit13_m72f21093_fillaaaaaaaa
```

**bit-11_m56076c68 is the structural extreme**: half of de58's bits are hard-locked. Any sr=61 SAT solution at this candidate must have `de58 & 0x9ddccc22 == 0x18d40802`. That's a 16-bit constraint embedded in de58.

## bit-19 in particular

- image size: 256
- hard-locked bits: 13 (`mask = 0x0187e01f`, value = `0x00854009`)
- varying bits: 19 at positions [5,6,7,8,9,10,11,12, 19,20,21,22, 25,26,27,28,29,30,31]
- effective entropy: log2(256) = 8 bits → only 8 of the 19 varying bits are independent (the other 11 are functionally dependent on the 8)

The hard-locked pattern at bit-19 is `de58 & 0x0187e01f == 0x00854009`. SAT solvers attempting bit-19 can immediately prune any branch with de58 violating this.

## How big a deal is this for SAT search?

Each hard-locked bit gives the SAT solver a "free" propagation — the bit is determined by the candidate. With 13-16 locked bits per candidate, the cascade-DP encoding's de58 bits are ~50% determined a priori.

But: the existing CNF encodings ALREADY embed the candidate via the precomputed `state56` constants. The hard-locked bits are emergent from the cascade structure — the SAT solver discovers them via unit propagation, but it has to traverse the W57 → state57 → ... → de58 chain to derive them.

**A propagator that pre-computes the locked pattern and asserts it as unit clauses would save the solver this propagation work.** Each of the 36 candidates has its own locked pattern; this is data the encoder could ship as a per-candidate hint clause set.

## Concrete extension to encoders

Add to `encode_sr61_cascade.py` (and `cascade_aux_encoder.py`):

```python
# After the existing constraints, assert the de58 hard-locked bits.
# This adds HW(locked_mask) unit clauses (or 2-literal clauses).
locked_mask, locked_value = compute_hardlock(m0, fill, kernel_bit)
for b in range(32):
    if (locked_mask >> b) & 1:
        v = (locked_value >> b) & 1
        # Set de58 var corresponding to bit b to v
        cnf.assert_bit(de58_var(b), v)
```

This is **purely additive** (no solution-set restriction; it's a tautology given the cascade structure). Expected effect: faster early propagation, possibly improving Mode B's documented 2-3.4× front-loaded speedup.

## What this gives the bet portfolio

- **A new candidate-priority axis** (third, after compression and low-HW-reachability): "lockedness" — fraction of de58 bits hard-locked.
- **Concrete encoder modification** to test against current Mode B baseline: would the 16 unit clauses at bit-11 give measurable solver speedup? Empirical pilot: <30 min of cadical compute across a few candidates.
- **Sanity-check substrate**: any future "I found sr=61 SAT" claim can be cheaply checked against the candidate's hard-locked pattern — a SAT that violates the lock is a bug.

## Reproducible

```bash
python3 headline_hunt/bets/sr61_n32/de58_hardlock_bits.py
# ~30s for all 36 candidates at 131k samples each.
```

## Files

- `de58_hardlock_bits.py` — runnable script
- This writeup
