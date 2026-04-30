---
date: 2026-05-01
bet: programmatic_sat_propagator × cascade_aux_encoding
status: F397 PRIORITIES VS F394 MECHANISM — different abstraction levels, mechanism-aligned in spirit
parent: F397 (yale priority specs) + F394 (macbook mechanism finding)
type: cross-check + analysis
compute: 0 cadical (analytical comparison of yale F397 spec + macbook F394 finding)
---

# F398: F397 priority specs cross-checked vs F394 mechanism story

## Question macbook asked yale

The F396_F397_thanks message asked: "Confirm if F397 priority sets
include dW57[0] + W57[22:23] (the F343-constrained vars)? If yes,
F397 directly supports F394 mechanism."

## Answer (from F397 JSON inspection)

**F397 priorities do NOT directly include the dW57-level vars.**

Inspecting F397's `f286_132_conservative` priority list for bit10:
  - 132 vars total, range [2, 257]
  - by_category: W1_57 (1) + W1_59 (32) + W1_60 (32) + W2_57 (1)
                 + W2_58 (2) + W2_59 (32) + W2_60 (32) = 132
  - dW57[0] for bit10 = var 12317. NOT in priority set.
  - W57[22] for bit10 = var 12339. NOT in priority set.
  - W57[23] for bit10 = var 12340. NOT in priority set.

F397 targets the **schedule-word vars directly** (W1_57[0..31],
W1_59[0..31], etc.) — vars 2-257. The F343-constrained vars are
**XOR-difference aux vars** (dW57[i] = W1[i] XOR W2[i]) — vars 12317+.

## But F397 IS mechanism-aligned in spirit

F397 priorities include W1_57[0] (var 2) AND W2_57[0] (var 130).
These are the **parents of dW57[0]** via the encoder's Tseitin XOR
encoding: dW57[0] is defined by `dW57[0] ⇔ W1_57[0] XOR W2_57[0]`.

When cadical's VSIDS branches on W1_57[0] AND W2_57[0] early (per
F397 priority), it implicitly decides dW57[0] via UP through the
Tseitin XOR clauses. The F343 unit clause on dW57[0] would then
propagate immediately after the parents are decided.

So F397 addresses the F394 mechanism story at a **higher abstraction
level** — branching on the schedule-word (parent) vars, which then
forces the diff (child) vars via UP.

This is actually *stronger* than the F394 proposal:
  - F394 proposed: branch on dW57[0]/W57[22:23] (3 vars)
  - F397 proposes: branch on W1_57[0..31], W2_57[0..31], W1_58[bits],
    W1_59[0..31], W2_59[0..31], W1_60[0..31], W2_60[0..31] (132 vars)

F397's 132-var priority covers the entire F286 universal hard core;
the F343-target dW57[0] gets implicitly addressed via its parents.

## Detailed mapping

```
F343 target               F397 corresponding parents          relationship
dW57[0] (var 12317)       W1_57[0]=2, W2_57[0]=130              Tseitin XOR: child ⇔ parents XOR
W57[22] (var 12339)       (in W1[57]/W2[57] vars 0..63 range)   schedule word bit
W57[23] (var 12340)       (in W1[57]/W2[57] vars 0..63 range)   schedule word bit
```

The W57[22] and W57[23] vars are W1[57]_b22 and W2[57]_b22 etc. — not
in F397's priority set per the by_category breakdown (only W1_57 b0
and W2_57 b0 are flagged in F286 universal core; per-bit indices 22
and 23 of W*_57 aren't there).

**Slight mismatch**: F397 prioritizes only W1_57[0] / W2_57[0], not
W1_57[22..23] / W2_57[22..23]. The F343 W57[22:23] pair clause's
parents may NOT be in F397's priority set unless they happen to
correspond to other F286 categories (W*_58 b14, b26 are flagged but
not b22, b23).

## Implications

### Finding 1 — F397 + F343 are complementary, not redundant

F397's 132-var schedule-word priorities and F343's 2-clause aux-var
constraints operate at different abstraction levels:
  - F397 forces VSIDS to branch on the SCHEDULE words at rounds 57-60
  - F343 constrains the DIFF aux vars (dW57[0], W57[22:23] specifically)

When combined, the propagator should:
  - At solver init: cb_add_external_clause(F343 baseline)
  - During search: cb_decide(F397 priority list)

Both operate at same time, complementary. F397 doesn't subsume F343;
F343 doesn't subsume F397.

### Finding 2 — Possible enhancement: extend F397 to include dW57[0..31]

F397's f286_132 already has 32 vars per W*_59 round and 32 per W*_60.
Adding 32 dW57 vars (vars 12317-12348 for bit10) would extend the
priority list to 164 vars. This would directly address F394's mechanism
story at the diff-var level.

Question for yale: is there a reason F397 stays at the schedule-word
level rather than including the dW57 row? F286 universal core is
defined at W*_59/W*_60 + 4 anchors at W*_57/W*_58. The dW57 row isn't
in F286 by definition. So F397 is correctly aligned with F286, but
F394 mechanism story might benefit from adding dW57 vars as a
secondary priority arm.

### Finding 3 — F399 matrix plan needs missing CNFs/varmaps

F399's dry_run identifies 5 cands missing CNF/varmap on yale's side:
  - bit11_m45b0a5f6, bit13_m4d9f691c, bit0_m8299b36f, bit17_m427c281d,
    bit18_m347b0144

Macbook has all 5 CNFs locally (per F394 + earlier work) but `.gitignore`
excludes `*.cnf` and `*.cnf.varmap.json` so they're not in git.

The cascade_aux_encoder.py is deterministic — yale can regenerate
each in ~5s wall:

```
python3 cascade_aux_encoder.py --sr 60 --m0 0x... --fill 0x... \
    --kernel-bit N --mode force --quiet \
    --out aux_force_sr60_n32_bitN_mNNN_fillNNN.cnf --varmap auto
```

Will note this in the cross-machine ack message.

## What's shipped

- This memo with F397 vs F394 cross-check
- Concrete finding: F397 priorities operate at schedule-word level
  (parents); F343 at diff-var level (children). Complementary.
- Concrete enhancement proposal: extend F397 to include dW57 row
  if direct diff-var priority is desired
- F399 missing-CNF note: yale can regenerate locally via
  cascade_aux_encoder.py

## Compute discipline

- 0 cadical runs
- audit_required: not applicable

## Next action for yale (cross-machine)

Cross-machine ack message planned with:
  - This F397 vs F394 cross-check
  - Suggestion: F397 might want a dW57-row arm (164 vars total)
  - Note: F399's "missing inputs" are regeneratable locally

Until Phase 2D C++ build happens (10-14h), F397 priorities are a
deployable spec waiting for implementation. Macbook side cannot run
the F399 matrix without that build.

## Cross-machine state

  Yale:
    F396 (manifest) + F397 (priority specs) + F398 (cb_decide wiring) +
    F399 (matrix plan) shipped 17:20-17:34 EDT.
    Yale's spec is ready for cb_decide implementation.

  Macbook:
    F381-F395 chain done (16 memos, structural rule + falsifications +
    mechanism understanding).
    F398 (this) cross-checks F397 vs F394.
    Awaits Phase 2D C++ build (10-14h, gates on user direction).
