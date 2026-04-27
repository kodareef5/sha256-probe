# F83: 2-block trail bundle validator + m17149975 sample bundle (v1 schema forcing function)
**2026-04-27 23:25 EDT**

Forcing function for the F82 SPEC: instantiate the v1 schema with the
m17149975 single-block collision and write a validator. Exposes spec
ambiguities immediately and gives yale a concrete template.

## Shipped

1. **`trails/sample_trail_bundles/m17149975_trivial_v1.json`** — the
   synthetic "block-2 is trivial" bundle for m17149975, instantiating
   every field of the v1 schema. Block-1 produces zero state diff
   (because m17149975 is a single-block collision); block-2 has zero
   W2_constraints because any block-2 message satisfies the all-zero
   target on a zero-input chain-state diff.

2. **`trails/validate_trail_bundle.py`** — schema validator. Checks:
   - schema_version == "2blockcertpin/v1"
   - block1: m0/fill/W1_57_60 are 32-bit hex, kernel_bit in [0,31],
     residual_state_diff has all 8 register entries (da63..dh63)
   - block2: W2_constraints elements have valid type
     (exact|exact_diff|modular_relation|bit_condition) and round in
     [0,63]; target_diff_at_round_N has all 8 register diffs
   - top-level required fields present (cand_id, witness_id, block1, block2)

   Exit 0 = valid, 1 = invalid, 2 = file/parse error.

## Self-test

Positive case: m17149975 sample bundle → **VALID** (exit 0).
Negative case: synthetic bundle with 17 deliberate errors (wrong
schema version, missing fields, invalid hex, out-of-range kernel_bit,
unknown constraint type, etc.) → **INVALID** (exit 1, 17 errors caught).

```
$ python3 validate_trail_bundle.py m17149975_trivial_v1.json
VALID: ...m17149975_trivial_v1.json
  schema:     2blockcertpin/v1
  cand:       cand_n32_msb_m17149975_fillffffffff
  witness:    m17149975_trivial_block2_sanity
  block-2 W2 constraints: 0
exit: 0
```

```
$ python3 validate_trail_bundle.py bad_bundle.json
INVALID: bad_bundle.json
  17 error(s):
    root.schema_version: expected '2blockcertpin/v1', got '2blockcertpin/v0'
    root: missing required field 'witness_id'
    block1: missing required field 'fill'
    block1.m0: expected 32-bit hex, got '0xZZZZ'
    block1.kernel_bit: expected int in [0,31], got 99
    block1.W1_57_60: expected list of 4 hex strings, got ['0x123', '0x456']
    block2.W2_constraints[0].type: expected one of [...], got 'bogus'
    block2.W2_constraints[0].round: expected int in [0,63], got 100
    block2.target_diff_at_round_N: missing 'diff_a' (collision target needs all 8 register diffs)
    ...
exit: 1
```

## What this validates about the SPEC v1

- The schema is **complete enough** to instantiate using known data
  (m17149975 collision certificate from `datasets/certificates/`).
  No fields had to be invented or made optional ad-hoc.
- The schema is **strict enough** that a malformed bundle is caught
  with specific actionable errors (not just "schema invalid").
- The validator is **fast** (<10ms on the sample bundle) and has zero
  external dependencies (stdlib only). Suitable for CI / pre-commit.

## Discipline

- No compute used. Pure schema/code work.
- Both files added to `headline_hunt/bets/block2_wang/trails/`.
- Validator self-tested against positive (valid) and negative
  (deliberately broken) cases before shipping.

## Concrete next moves

1. **Yale**: when drafting your block-2 trail, run
   `validate_trail_bundle.py` on each iteration. Catches schema bugs
   before they reach macbook's encoder.

2. **Macbook**: extend `cascade_aux_encoder.py` to read trail bundles
   and emit the corresponding 2-block CNF. ~150 LOC. Use the
   m17149975 sample as the regression test (should round-trip to a
   trivial-SAT CNF). This is the next 1-2 sessions of focused work.

3. **Fleet**: link this validator from `cascade_aux_encoding/encoders/
   build_certpin.py` so a future `build_2block_certpin.py` rejects
   malformed bundles at intake.

## What this does NOT do

- Does not build the actual 2-block CNF (encoder extension is the
  next step).
- Does not validate semantic correctness of yale's trail (e.g.,
  whether block-1 residual really does equal what yale claims). That
  requires running block-1 forward simulation and checking — out of
  scope for the schema validator.
- Does not validate that yale's trail is structurally satisfiable.
  That's what kissat's job is once the CNF is built.

EVIDENCE-level: VERIFIED. Validator passes on sample, catches all 17
deliberate errors on bad bundle. v1 schema is well-formed.
