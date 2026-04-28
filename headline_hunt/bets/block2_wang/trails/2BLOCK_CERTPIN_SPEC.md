# 2-Block Cert-Pin SPEC — interface contract for yale's block-2 trail → macbook's verification

**Status**: DRAFT v1, 2026-04-27 22:55 EDT
**Owner**: macbook (verification side); yale (trail-design side)
**Purpose**: Define the data contract yale ships and the CNF construction
macbook builds, so that when yale finishes a Wang-style block-2
absorption trail, the verification pipeline can ingest it without
reformatting.

---

## Why this spec exists

F71 + F80 establish: every cascade-1 single-block W-witness yale's
online sampler produces is a near-residual (UNSAT under cert-pin).
The Wang block-2 absorption pattern is the only known route to
convert a near-residual into a verified collision.

Today's pipeline (`certpin_verify.py`) handles **single-block** cert-pin:
given (m0, fill, kernel-bit, W1[57..60]), kissat decides whether the
cascade-1 CNF is SAT.

The **2-block** verifier hasn't been built. Yale's eventual block-2
trail will specify how a *second* message block absorbs the residual
left by block 1. Until the spec is locked, yale risks designing in a
format macbook can't ingest, or macbook risks building against the
wrong contract.

This document is the contract.

---

## What yale ships (the trail bundle)

A single JSON file, `block2_trail_<cand_id>_<witness_id>.json`, with:

```json
{
  "schema_version": "2blockcertpin/v1",
  "cand_id": "cand_n32_bit28_md1acca79_fillffffffff",
  "witness_id": "yale_F77_bit28_HW45_LM637_EXACT",

  "block1": {
    "m0": "0xd1acca79",
    "fill": "0xffffffff",
    "kernel_bit": 28,
    "W1_57_60": ["0xce9b8db6", "0xb26e4c72", "0x4b04cbc4", "0x0a0627e6"],
    "W2_57_60": ["0x...", "0x...", "0x...", "0x..."],
    "expected_status": "near_residual_unsat",
    "residual_state_diff": {
      "a63":"0x...","b63":"0x...","c63":"0x...","d63":"0x...",
      "e63":"0x...","f63":"0x...","g63":"0x...","h63":"0x..."
    },
    "residual_hw": 45,
    "residual_lm_cost": 637,
    "comment": "Block-1 produces this state diff at round 63. Block-2 must absorb it."
  },

  "block2": {
    "absorption_pattern": "wang_local_collision_v1",
    "modified_message_words": [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
    "W2_constraints": [
      { "round": 0, "type": "exact", "value": "0x..." },
      { "round": 1, "type": "exact", "value": "0x..." },
      { "round": 5, "type": "exact_diff", "diff": "0x...",
        "comment": "second-block dW differential at round 5" },
      { "round": 16, "type": "modular_relation",
        "constraint": "W2[16] = W2[0] + sigma1(W2[14]) + W2[9] + sigma0(W2[1])",
        "comment": "schedule consistency, redundant with SHA-256 spec but sometimes useful as a hint" }
    ],
    "chain_state_input": {
      "comment": "block-2 starts from H = block-1's chaining output. The diff at the start of block-2 EQUALS block-1's residual_state_diff above (mod IV addition)."
    },
    "target_diff_at_round_N": {
      "round": 63,
      "diff_a": "0x00000000",
      "diff_b": "0x00000000",
      "diff_c": "0x00000000",
      "diff_d": "0x00000000",
      "diff_e": "0x00000000",
      "diff_f": "0x00000000",
      "diff_g": "0x00000000",
      "diff_h": "0x00000000",
      "comment": "ALL ZERO at round 63 of block-2 = full SHA-256 collision."
    },
    "expected_status": "sat_if_trail_correct",
    "expected_modular_paths": [
      { "round": 5, "path": "...", "lm_cost": 12 },
      { "round": 6, "path": "...", "lm_cost": 8 }
    ],
    "predicted_lm_cost_block2": 84
  },

  "metadata": {
    "designer": "yale",
    "design_date": "2026-04-XX",
    "design_method": "manual_wang_extension | automated_search_<tool>",
    "confidence": "exploratory | high | verified_at_smaller_N",
    "compat_with_block1_witness": true,
    "smaller_N_validation": {
      "N": 10,
      "block2_sat": true,
      "wall_seconds": 14.2,
      "verifying_solver": "kissat 4.0.4"
    }
  }
}
```

### Required fields (minimum to attempt verification)

- `block1.{m0, fill, kernel_bit, W1_57_60}` — needed to rebuild block-1 CNF
- `block1.W2_57_60` — RECOMMENDED for forward simulation (cascade-1
  picks W2[57..60] specifically; without this, simulator falls back
  to natural-schedule W2 which produces a different residual). Yale's
  online sampler computes both via cascade offsets, so include both
  in shipped bundles.
- `block1.residual_state_diff` — yale's claim about what block-1 produces
- `block2.W2_constraints` — yale's trail (each constraint becomes CNF clauses)
- `block2.target_diff_at_round_N` — collision target (zeros = full collision)

Everything else is optional/diagnostic.

---

## What macbook builds (the verifier)

A new tool `headline_hunt/bets/block2_wang/encoders/build_2block_certpin.py`:

```
python3 build_2block_certpin.py \
    --trail block2_trail_bit28_yale_F77.json \
    --out 2block_pinned.cnf
```

### CNF structure

The output CNF encodes BOTH blocks of SHA-256 with the differential
relationship pinned end-to-end:

```
[block-1 differential cascade-aux CNF]   (existing cascade_aux_encoder Mode A)
  + W1[57..60] unit clauses               (existing build_certpin.py logic)
  + chain-state output of block-1 = aux state-1 vars (already in encoder)

[block-2 differential CNF]                (NEW — encoder extension needed)
  + chain-state input of block-2 wired = chain-state output of block-1
  + W2[r] constraints from yale's trail   (translated to clauses)
  + state diff at round 63 of block-2 = ALL ZERO   (collision target)
```

### Verification semantics

| Outcome | Meaning |
|---|---|
| **SAT** | Yale's block-2 trail is **correct**. Solver returns concrete (m0, m1, m1') = a verified SHA-256 collision. **HEADLINE.** |
| **UNSAT** | Trail incompatible — either block-1 residual ≠ yale's predicted residual, or block-2 trail clauses contradict, or end-to-end zero target unreachable. Yale's design has a bug or the chosen residual is structurally wrong. |
| **UNKNOWN @ budget** | Indeterminate. Increase conflict budget, try other solvers, or relax non-essential trail constraints. |

A SAT outcome on a 2-block cert-pin CNF with all-zero target diff at
round 63 is, by construction, a full SHA-256 collision certificate.

---

## Encoder gap to close (macbook's TODO)

`cascade_aux_encoder.py` currently emits **block-1 only** (single
SHA-256 message-block compression). To support 2-block:

1. **Two independent message-block CNFs**, sharing chaining state.
   Each block has its own message-schedule vars W1, W2. Each block's
   round-63 chain-state output feeds the next block's chain-state input.

2. **Block-1 chaining output → block-2 chaining input wiring.**
   In differential terms: `dH_after_block1 = dA[63]+dB[63]+...+dH[63]`
   (the modular state-XOR-diff at end of block-1) becomes block-2's
   starting chain-state diff. Encoder needs to expose `aux_chain_diff`
   vars that are equality-tied across the boundary.

3. **W2 constraint translation.** Yale's `W2_constraints` array maps to:
   - `exact`: 32 unit clauses pinning W2[r]
   - `exact_diff`: 32 unit clauses pinning dW2[r] = W2[r] XOR W2'[r]
   - `modular_relation`: redundant SHA-256 schedule clauses (already
     in encoder for r ≥ 16)
   - `bit_condition`: e.g., `W2[r] bit 17 = W2[r] bit 5` → equality clause

4. **Block-2 round-63 zero target.** 8 × 32 unit clauses pinning
   `dA[63]_block2 = dB[63]_block2 = ... = dH[63]_block2 = 0`.

Estimated encoder extension: ~150 LOC new wrapper around existing
`cascade_aux_encoder.py`, no changes to `lib/cnf_encoder.py`.

---

## What we cannot specify yet (yale's domain)

- **Specific Wang-extension absorption pattern** for SHA-256.
  Wang's MD5/SHA-1 patterns rely on round-specific message-modification
  tricks that don't transfer 1:1 to SHA-256's expansion. Yale's structural
  work is to find a SHA-2-compatible analog.

- **Which block-1 residual to absorb.** Yale's frontier (HW=33, 39, 45,
  78) gives a Pareto surface; yale will choose which one to design
  block-2 absorption *for*. The trail bundle declares this choice via
  `block1.residual_state_diff`.

- **Whether such a trail EXISTS at sr=60 cascade-1.** Possibly no
  Wang-style block-2 trail with low enough LM cost is achievable;
  in that case yale's structural negative becomes the closing memo
  for the bet.

---

## Sanity check: what a correct 2-block cert-pin would look like

For the sr=60 m17149975 verified collision (single-block, already in
`headline_hunt/datasets/certificates/sr60_n32_m17149975.yaml`), a
trivial 2-block extension is: block-2 has W2 = ANY message, pins
chain-state diff = 0 at end of block-1 (trivially — m17149975 is a
single-block collision), block-2 runs as a normal SHA-256 round on
zero-diff chain state, output diff stays zero. The 2-block cert-pin
should return SAT trivially.

Once `build_2block_certpin.py` exists, this round-trips as a sanity
test before yale's real block-2 design lands.

---

## Concrete next moves

1. **macbook**: extend `cascade_aux_encoder.py` to emit 2-block CNF
   with chaining-state wiring. ~150 LOC. Estimated 1-2 sessions.

2. **macbook**: build `build_2block_certpin.py` — JSON trail bundle
   in, CNF out. ~100 LOC. Trivial after #1.

3. **macbook**: implement the m17149975 sanity round-trip as a
   regression test. Confirms the 2-block pipeline doesn't have an
   off-by-one or wiring bug.

4. **yale**: start designing block-2 trail in this JSON schema. Even
   a partial trail (with only some constraints filled in) can be tested
   for under-constrained-SAT to see if there's freedom in the design.

5. **fleet**: when yale ships first trail bundle, macbook runs
   `build_2block_certpin.py` + `kissat`. Result is one of:
   - **SAT** → HEADLINE: full SHA-256 sr=60 cascade-1 + block-2 collision.
   - **UNSAT** → yale's design has a bug or the residual choice
     was structurally infeasible. Yale iterates.
   - **UNKNOWN** → increase budget, try other solvers, or simplify the
     trail with relaxations to localize the hard sub-problem.

---

## Schema versioning

- `schema_version: 2blockcertpin/v1` — this document.
- Future revisions (multi-residual support, partial-collision targets,
  etc.) bump the `vN` suffix. Verifier rejects unknown schema versions
  to prevent silent format drift.

---

## What this spec does NOT cover

- The actual block-2 design (yale's structural domain).
- Multi-block (>2) extensions (out of scope; sr=60 + 1 absorption block = sufficient).
- Probabilistic differential paths (this is exact-clause CNF; no probability annotations).
- Solver-side performance tuning (assumed: standard kissat 4.0.4 + cadical 3.0.0).

---

## Open questions for yale

1. **Schedule consistency**: does your block-2 design rely on exact W2
   values, on differential constraints (dW2), or on bit-conditions?
   The schema supports all three but the relative weights matter for
   how tight the resulting CNF is.

2. **Smaller-N validation**: do you have a working block-2 trail at
   N=8 or N=10 first? An N-scaling validation (N=8 SAT → N=10 SAT →
   N=32 SAT?) would let macbook regression-test the encoder before
   the full N=32 push.

3. **Trail width**: how many message-modification rounds does the
   pattern span? Wang's SHA-1 patterns are ~10 rounds wide. If yours
   spans more, the CNF gets bigger but kissat handles it fine up to
   ~10^6 clauses.

4. **Residual choice**: which of (HW=33, 39, 45 EXACT-sym, HW=78 pair8)
   is your design targeting? The structural absorption math depends on
   the residual's modular shape.

---

## Discipline

- This is a SPEC, not a tool. No compute used.
- Will be referenced by macbook's encoder extension and yale's trail
  design from this commit forward.
- Schema lives at this path; if revised, bump `schema_version` and
  preserve the v1 in this file as a historical reference.

End of spec v1.
