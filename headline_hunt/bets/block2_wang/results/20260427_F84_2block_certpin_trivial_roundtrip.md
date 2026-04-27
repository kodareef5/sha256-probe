# F84: build_2block_certpin.py shipped — end-to-end SAT round-trip on m17149975 trivial bundle
**2026-04-27 23:25 EDT**

Operationalizes F82 + F83: the 2-block cert-pin pipeline now runs
end-to-end for the trivial round-trip case. Yale's eventual real
trail bundles will plug into the same entrypoint.

## Shipped

`headline_hunt/bets/block2_wang/encoders/build_2block_certpin.py`

Staged delivery:
- **TRIVIAL CASE** (block1.residual all zero + block2.target all zero +
  W2_constraints empty): delegates to existing single-block cert-pin
  pipeline (`certpin_verify.py`). Returns SAT for known single-block
  collisions. **WORKS TODAY.**
- **NON-TRIVIAL CASE** (anything else): exits 3 with a precise
  diagnostic pointing to the SPEC's "Encoder gap to close" section.
  Will be implemented after `cascade_aux_encoder.py` is extended to
  emit 2-block CNFs with chaining-state wiring.

## End-to-end test

```
$ python3 build_2block_certpin.py \
    headline_hunt/bets/block2_wang/trails/sample_trail_bundles/m17149975_trivial_v1.json

=== 2-block cert-pin verification ===
Bundle:     .../m17149975_trivial_v1.json
Cand:       cand_n32_msb_m17149975_fillffffffff
Witness:    m17149975_trivial_block2_sanity
Block-1 residual: ZERO
Block-2 target:   ZERO
Block-2 W2 constraints: 0

TRIVIAL CASE detected. Delegating to single-block cert-pin
(reduces to verifying block-1 alone is SAT).

Status:  SAT
Wall:    0.01s
Verdict: verified collision

🎉 HEADLINE-CLASS DISCOVERY: verified collision certificate!
   This is a sr=60 cascade-1 SAT solution at the given W-witness.
```

m17149975 is, of course, an ALREADY-VERIFIED single-block sr=60
collision. The "headline" banner is the existing certpin_verify
behavior — the new claim is **the 2-block pipeline successfully
re-verifies it via a 2blockcertpin/v1 trail bundle**.

## Non-trivial branch test (synthetic)

```
$ python3 build_2block_certpin.py /tmp/nontrivial_bundle.json
NON-TRIVIAL bundle. Encoder extension required.
  trivial_residual = False
  trivial_target   = True
  no_w2_constraints = False

See SPEC: headline_hunt/bets/block2_wang/trails/2BLOCK_CERTPIN_SPEC.md
Section: 'Encoder gap to close (macbook's TODO)'.
This branch will be implemented after cascade_aux_encoder.py is
extended to emit 2-block CNFs with chaining-state wiring.

exit 3
```

When yale ships a real trail (non-empty W2_constraints + non-zero
residual), they get this exact message — actionable and pointed.

## Discipline

- Bundle goes through `validate_trail_bundle.py` BEFORE encoder
  dispatch. Malformed bundles caught at intake (exit 2).
- Trivial round-trip kissat run logged via `append_run.py`
  (run_20260427_232428_block2_wang_kissat_seed1_73493577).
  CNF: `aux_expose_sr60_n32_bit31_m17149975_fillffffffff_certpin.cnf`,
  status SAT, wall 0.01s.
- Registry total: 879 logged runs.

## What this validates about the architecture

The full chain works **today** for the trivial case:

```
JSON trail bundle
  → validate_trail_bundle.py (schema check)
  → build_2block_certpin.py (dispatch)
  → certpin_verify.py (single-block delegate)
  → cascade_aux_encoder.py (CNF gen)
  → build_certpin.py (W1 pinning)
  → kissat 4.0.4 (SAT solver)
  → SAT verdict, 0.01s
```

5 separate tools chained, end-to-end SAT, sub-second wall. Yale
can iterate on trail bundles *now* and catch validator/dispatch
errors immediately — without waiting for the encoder extension.

## What's next (macbook side)

1. **Extend `cascade_aux_encoder.py` to emit 2-block CNF** (~150 LOC).
   The hard part: wiring block-1 round-63 chain-state output diff
   to block-2 chain-state input diff, with the modular IV-add
   handled correctly.

2. **Replace the NotImplementedError branch** in
   `build_2block_certpin.py` with a call into the extended encoder.
   ~50 LOC. Trivial after #1.

3. **Add `m17149975_trivial_v1.json` round-trip as a CI/regression
   test**. If a future encoder change breaks the trivial case, we
   notice immediately.

Estimated session count: 2-3 focused sessions (~6-9 hours wall).
No big-compute authorization needed — encoder work is pure CNF
emission, no solving until the regression test runs.

## What's next (yale side)

1. Use `validate_trail_bundle.py` on each block-2 trail draft.
2. Use `build_2block_certpin.py` on completed drafts: get either
   "encoder extension required" (expected, until macbook ships
   the extension) or eventually a real SAT/UNSAT verdict.
3. Open questions from SPEC v1 still pending (constraint type mix,
   smaller-N validation, trail width, residual choice).

## File inventory (post-F84)

```
headline_hunt/bets/block2_wang/
├── trails/
│   ├── 2BLOCK_CERTPIN_SPEC.md                    [F82]
│   ├── validate_trail_bundle.py                  [F83]
│   ├── sample_trail_bundles/
│   │   └── m17149975_trivial_v1.json             [F83]
│   └── 20260427_F83_trail_bundle_validator_and_sample.md
├── encoders/
│   └── build_2block_certpin.py                   [F84, this commit]
└── results/
    └── 20260427_F84_2block_certpin_trivial_roundtrip.md  [this file]
```

EVIDENCE-level: VERIFIED. End-to-end pipeline runs SAT in 0.01s on
the m17149975 trivial bundle. Both branches (trivial dispatch +
non-trivial NotImplementedError) tested and behave correctly.
Registry run logged.
