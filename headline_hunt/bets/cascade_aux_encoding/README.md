# bet: cascade_aux_encoding — local-offset auxiliary encoding

**Priority 2** per GPT-5.5. Pairs with `kc_xor_d4` and `true_sr61_n32` — a successful
new encoding could change behavior for both d4 compilation and SAT solve time.

## The bet

Two facts in tension:
1. Standard CNF has treewidth ~110 at N=8 (d4 ceiling).
2. The "derived encoding" (full W2 substitution) made it WORSE — treewidth 181.

The derived encoding's substitution adds global cross-constraints. A different shape
— **local-offset auxiliaries that mirror cascade-diagonal constraints** — should give
the solver explicit structural hooks without producing the global substitution penalty.

## Hypothesis

Adding auxiliary variables for cascade-relevant local offsets (specific within-round
relationships between W, a, e at rounds 56-60) drops treewidth meaningfully without
the cost the derived encoding paid.

## Headline if it works

Not directly headline-worthy, but **enables** the headlines for:
- `true_sr61_n32` (encoding change is the only allowed restart for sr=61 per its kill criteria).
- `kc_xor_d4` (lower treewidth could push d4 through the compilation ceiling).

A solo headline could be "constructive d-DNNF compilation of N=16+ collision object" if
the encoding lets d4 actually finish.

## What's built / TODO

- [ ] **Spec the auxiliary variable set.** Which cascade offsets, which rounds. Document
  in `encoders/SPEC.md` with rationale (mirrored to mechanisms.yaml).
- [ ] **Encoder variant.** Extend `lib/cnf_encoder.py` with `--cascade-aux` flag. Do NOT
  modify existing encoding paths — additive only.
- [ ] **Treewidth measurement.** Run FlowCutter on N=8, N=10, N=12 with and without
  auxiliaries. Output: `comparisons/treewidth.md`.
- [ ] **SAT comparison.** TRUE sr=61 N=10 instance solved with both encodings; compare
  conflicts, restarts, wall time across multiple seeds.
- [ ] **Decision gate.** Treewidth must drop measurably at N=8 OR SAT robustness must
  improve on N=10/N=12 — else kill.

## How to join

Cheap to start. One person can do the encoder spec + implementation in 1-2 days.

1. Set `cascade_auxiliary_encoding.owner` in `mechanisms.yaml`.
2. Read `lib/cnf_encoder.py` to understand the existing encoding structure.
3. Read `writeups/sr60_collision_anatomy.md` for the cascade-diagonal structure the
   auxiliaries should mirror.
4. Write the spec FIRST in `encoders/SPEC.md` before coding — get it reviewed in
   `comms/inbox/` if other machines are active.

## Related

- Enables: `true_sr61_n32`, `kc_xor_d4`.
- Closed by failure of: itself only.
- Reopens if: new theoretical insight on cascade structure suggests a different
  auxiliary basis.
