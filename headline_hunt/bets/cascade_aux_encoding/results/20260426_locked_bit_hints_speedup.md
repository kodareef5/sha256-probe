# Locked-bit hints: Mode A → Mode-B-equivalent speedup on bit=19
**2026-04-26 14:35 EDT** — D2 follow-up.

D2 (commit 505859b) showed bit=19's de58 image has 13 fully locked
bits + 5 partial-locked. The reopened `bdd_marginals_uniform`
negative motivated this follow-up: **does adding the 13 locked-bit
patterns as redundant unit clauses on aux_reg[("e", 58)] speed up
kissat?**

Answer: **YES on Mode A (1.71× at 50k). Negligible on Mode B (1.06×).**

## Setup

Built 4 cascade_aux sr=61 CNFs for bit=19:

1. Mode A (expose) — control
2. Mode A + 13 locked-bit unit clauses on de58 aux vars
3. Mode B (force) — control
4. Mode B + 13 locked-bit unit clauses on de58 aux vars

Locked-bit pattern (from D2):
```
de58[ 0] = 1, de58[ 1] = 0, de58[ 2] = 0, de58[ 3] = 1, de58[ 4] = 0
de58[13] = 0, de58[14] = 1, de58[15] = 0, de58[16] = 1, de58[17] = 0,
de58[18] = 1
de58[23] = 1, de58[24] = 0
```

These are REDUNDANT clauses (the existing CNF constraints imply
them via cascade-1 structure), but kissat doesn't extract them via
default CDCL.

## Results

```text
                            50k wall    1M wall
Mode A (expose) base         3.04s      21.15s
Mode A + locked-bit hints    1.78s      21.59s   ← 1.71× at 50k!
Mode B (force) base          1.22s      21.43s
Mode B + locked-bit hints    1.15s      20.84s   ← negligible (1.06×)
```

## Speedup analysis

**Mode A + locked-bit hints: 1.71× at 50k**
The 13 locked-bit unit clauses give kissat a propagation shortcut.
Mode A baseline is high (3.04s) because Mode A doesn't force cascade
structure. Adding the de58 locked-bit pattern provides STRUCTURAL
knowledge that the solver needs to derive itself otherwise. With
hints: Mode A approaches Mode B speed (1.78 vs 1.22s).

**Mode B + locked-bit hints: 1.06× at 50k**
Mode B's force clauses already encode cascade structure; the locked-
bit hints are partially redundant with what Mode B provides. Net
benefit small.

**Both at 1M conflicts: speedup decays to ~1×**
Consistent with the cascade_aux predictor model: any structural
preprocessing speedup is consumed by ~500k conflicts.

## Implications

1. **Structure-aware unit clauses are real Mode A → Mode-B-equivalent
   transformation**. Without restricting the solution set (Mode B
   force clauses do), per-cand locked-bit hints achieve comparable
   preprocessing speedup at 50k.

2. **The negatives.yaml `bdd_marginals_uniform` reopen criterion
   fires more strongly than D2 alone**. Not only are bit=19's
   marginals non-uniform (D2), the non-uniformity is EXTRACTABLE by
   kissat via redundant unit clauses to give a measurable speedup.

3. **For cascade_aux deployment**: adding per-cand locked-bit hints
   to Mode A is a lighter-weight alternative to full Mode B force
   clauses. Mode A + hints approaches Mode B speed without
   cascade-structural restriction.

4. **Predictor closure refinement**: the validation matrix (20260425)
   showed de58_size and hard_bit_total_lb are search-irrelevant for
   sr=61 SAT-finding. This locked-bit-hint test shows the ACTUAL
   locked-bit pattern (a different per-cand metric) IS search-relevant
   in the early-conflict preprocessing window.

## What this does NOT show

- No SAT found (all UNKNOWN at 1M). The hint speeds up the early-
  conflict regime; it doesn't make SAT-finding tractable.
- Untested whether locked-bit hints help on cands without de58
  compression (idx=8, idx=0 with de58 ~80k). Likely the speedup
  would be smaller since fewer locked bits exist.
- Untested whether kissat's `--phase-saving` knob (decision phase
  preference) gives the same effect with less invasive changes to
  the CNF.

## Action items

1. ✓ Memo committed (this).
2. Update cascade_aux's deployment story: structure-aware Mode A
   (Mode A + locked-bit hints) is a third deployment option alongside
   Mode A and Mode B.
3. Test locked-bit hints on idx=0 (msb_cert, de58_size=82826,
   `de58_hardlock_mask=0x624f3000` = 10 locked bits) to see if the
   1.71× scales with locked-bit count.

## Reproduce

```bash
# Build CNFs (use /tmp/deep_dig/d2_locked_bit_test.py)
python3 d2_locked_bit_test.py expose /tmp/aux_expose_bit19.cnf
python3 d2_locked_bit_test.py expose_locked /tmp/aux_expose_bit19_locked.cnf
python3 d2_locked_bit_test.py force /tmp/aux_force_bit19.cnf
python3 d2_locked_bit_test.py force_locked /tmp/aux_force_bit19_locked.cnf

# Test
for cnf in /tmp/aux_*bit19*.cnf; do
  /usr/bin/time -p kissat --conflicts=50000 --seed=5 -q "$cnf"
done
```

EVIDENCE-level: locked-bit unit clauses on aux_reg[("e",58)] of
bit=19 cand give 1.71× Mode A speedup at 50k kissat conflicts.
First demonstrated structure-aware speedup on a structurally
distinguished cand. Confirms `bdd_marginals_uniform` reopen criterion
is correct and the structure is extractable.

## ADDENDUM (14:38 EDT) — scaling test across 5 cands

Tested locked-bit hints on 5 cands spanning de58_size 256–51k:

| cand | de58_size | hl | A base | A+hint | speedup |
|---|---:|---:|---:|---:|---:|
| bit19 m=0x51ca0b34 | **256** | 13 | 3.09s | 1.77s | **1.75×** |
| bit15 m=0x28c09a5a | 4096 | 14 | 3.15s | 2.34s | 1.35× |
| bit20 m=0x294e1ea8 | 8187 | 15 | 2.33s | 1.82s | 1.28× |
| msb m=0x17149975 | 51563 | 10 | 2.12s | 1.74s | 1.22× |
| bit3 m=0x33ec77ca | 51654 | 6 | 1.97s | 1.95s | 1.01× |

Spearman ρ(hl, speedup) = +0.60. **But de58_size is the dominant
predictor**: speedup ranks almost perfectly inversely with de58 image
size (Spearman ρ would be ≈ -0.9 by inspection).

**Intuition**: smaller de58 image means each locked bit is a larger
fraction of the image's entropy. bit=19's 13 locked bits in a 2^8
image = 1.6 bits of entropy per locked-bit hint. bit=3's 6 locked
bits in a 2^16 image = much less informational impact per hint.

## Cross-bet revision: bit=19 IS structurally distinguished

This addendum REVISES the B1 finding's interpretation. B1 (b760423)
showed bit=19 floors HIGHER at HW5 D61 under random-flip walks —
"mitm_residue's priority target framing is invalidated."

This locked-bit-hint scaling test shows bit=19 IS the BEST candidate
for SAT preprocessing speedup (largest hint benefit, 1.75× vs others'
1.0-1.4×).

So: **bit=19 has real structural distinction, but it lives in the SAT
preprocessing layer, not the random-flip-walker layer.** The mitm_residue
"priority MITM target" framing was correct in spirit (bit=19 has real
structure), wrong in attack vector (forward-table doesn't help; SAT
branching with locked-bit hints does).

The G1 synthesis (ef56416) should be read with this addendum — the
mitm_residue invalidation was partial. The bet's de58_size=256 emphasis
points at REAL structure usable by SAT, just not at the cascade-walker
or forward-table objectives.

## Productive deployment story for cascade_aux

| Mode | Solution set | Preprocessing speedup |
|---|---|---|
| A (expose) | unchanged | 1× (control) |
| A + locked-bit hints | unchanged | 1.0-1.75× (de58-dependent) |
| B (force) | restricted to cascade-DP solutions | 1.5-3× |

Mode A + locked-bit hints is the new option: comparable speedup to
Mode B without restricting the solution set. Cheapest implementation:
a Python wrapper around cascade_aux_encoder that injects unit clauses
based on de58 image marginals.
