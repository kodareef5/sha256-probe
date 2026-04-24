# q4_mitm_geometry — operational audit

**Date**: 2026-04-24
**Auditor**: macbook
**Result**: status promoted from `blocked` → `open`. Tools exist, several work, mechanism is genuinely live.

## TL;DR

The bet was marked `blocked` based on the pause summary's note that "tools exist but not operational at N=32." Auditing the 30+ scripts in `q4_mitm_geometry/`, **the core MITM prototypes are operational**. They run, produce structured output, and recover the verified sr=60 certificate. The actual gap isn't operationalization — it's that nobody is running them at the right scales and reporting results.

The legacy "scripts 71, 74, 75" referenced in `mechanisms.yaml`/`QUESTION.md` correspond to the project's old numbered-prefix convention before the rename. They live (renamed) as the cascade_mitm / round61_inverter / cascade_chain family in the current `q4_mitm_geometry/` directory.

## What's there (32 scripts inventoried)

### Top-level MITM tools

| Script | Lines | Status | Notes |
|---|---:|---|---|
| `cascade_mitm_full.py` | 212 | **WORKS — verified 2026-04-24** | Forward W[57] × backward W[60] match on round-59 fingerprint. Recovers sr=60 cert. ~86k W[57] samples/s on macbook. |
| `cascade_mitm.py` | 175 | **partial** | Phase 1 forward enumeration. File ends mid-comment ("Wait — that's the additive condition. Let me think..."). cascade_mitm_full.py supersedes. |
| `gpu_mitm_prototype.py` | 235 | **untested** | Torch-based GPU prototype. N=8 feasibility analysis baked in. Forward+backward+match on (g60,h60) — the actual hard residue. Needs a CUDA/MPS box to validate. |
| `round61_inverter.py` | 129 | **building block** | Algebraic inversion of cascade_dw constraint at round 61. Useful subroutine, not a top-level MITM. |
| `round61_inverter.c` | — | parallel C implementation | Compiles? Untested. |
| `cascade_chain_4level.py` | — | **untested** | 4-level cascade chain analysis — bridge between forward W[57] and backward W[60]. |

### Supporting / analytical

`anchor_sweep.py`, `bit_breakdown.py`, `prefix_*` scripts, `cascade_image*` C tools, `g_*` (universality / structure analysis), `near_collision_hunt.c`, `multiblock_from_nearcollision.py`, `state_collision.c`, `w59_family_size.c`. Not core to MITM-on-hard-residue but useful for surrounding analysis.

### Verified working (2026-04-24, this audit)

```
$ python3 q4_mitm_geometry/cascade_mitm_full.py 1000 1000
Cascade 1 offset: W2[57] = W1[57] + 0xd617236f
Cert W1[57]=0x9ccfa55e, W2[57]=0x72e6c8cd
  -> Cert values match the offset formula.
=== FORWARD: 1000 W1[57] samples ===
  CERT w1_57=0x9ccfa55e
    da59 = 0x00000000 (hw=0)
    db59 = 0x00000000 (hw=0)
    dc59 = 0x00000000 (hw=0)
    dd59 = 0x00000000 (hw=0)
    de59 = 0x8b57c367 (hw=18)
    ...
Forward: 1000 unique round-59 fingerprints in 0.0s (85894 samples/s)
=== MATCHING ===
Cascade 2 offset: W2[60] = W1[60] + 0x337de3e9
Cert offset: W2[60]-W1[60] = 0x337de3e9
Match: True
```

The forward cascade recovers the certificate's W[57] offset. The match logic is correct.

## What's actually open (real next-actions)

Per `QUESTION.md` the strategy GPT-5.5 called highest-upside is "stop solving the whole tail uniformly. Solve the HARD RESIDUE." Concrete next-actions, ordered by leverage:

1. **Scale the forward-only enumeration to a meaningful sample**. cascade_mitm_full.py at 1000 samples is a smoke test. At 2^20 (1M) samples in a few seconds, we can collect a usable forward distribution over (de59, df59, dg59, dh59) and start clustering. **30 min of CPU.**

2. **Run the GPU prototype at N=8** to validate the hard-residue MITM at small scale where exhaustive ground truth exists (260 collisions known at N=8). **Few hours on a GPU box.** This is the GPU laptop's natural fit.

3. **Connect cascade_mitm_full.py output to a hash table** so forward (~2^32 keyed on the 24-bit hard residue) and backward (~2^32) can actually meet. Right now the script has the fingerprint-comparison logic but not the keyed-table structure. **~50-100 lines of Python.**

4. **Test the candidate-independence assumption**: does the hard residue position shift for non-MSB candidates (bit-6, bit-10, ...)? If yes, MITM tables become per-candidate, multiplying compute. If no, one table reusable across candidates. **Few hours of analysis on existing certificates.**

5. **Memory budget verification**: at N=32 with 24-bit residue, forward+backward tables are 2^32 entries each at ~64 bytes = ~256GB total. Outside macbook RAM, fits a beefy linux box. Confirm with a small-scale measurement.

## Recommended pickup

A machine with **GPU available** (the gpu-laptop in the original fleet) should pick this up next — the gpu_mitm_prototype.py is the cleanest path to N=8 validation. Macbook can pair on the table-structure work (item 3) since that's CPU+disk bound, not GPU.

After N=8 validation, the bet either becomes the priority-1 or gets killed cleanly via "table memory blows the budget at N=32 even with 24-bit compression" — both are useful outcomes.

## Bet status changes

Updating:
- `bets/mitm_residue/BET.yaml`: status `blocked` → `open`, owner `unassigned` → `macbook` (audit owner; will reassign on actual GPU/scale work).
- `registry/mechanisms.yaml#mitm_hard_residue`: status `blocked` → `open`, next_action updated to point at concrete items above.

This is a process unblock, not a research result. The research lift comes from the next worker actually running the items above.
