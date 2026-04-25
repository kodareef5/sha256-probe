# M16-MITM foundation: q5/mitm_cascade_sr60.py is the prototype
**2026-04-25 evening** — block2_wang Stage 3 / SCALING_PLAN.md M16-MITM milestone foundation discovery.

## What this maps to

`SCALING_PLAN.md` Stage 3 (revised) needs MITM implementation at N=16:
forward enumerator + backward enumerator + hash-join match phase.

`q5_alternative_attacks/mitm_cascade_sr60.py` IS this architecture, in Python at sr=60. It already implements the round-split MITM described in our SCALING_PLAN.

## What it does

```
1. FORWARD: enumerate (W[57], W[58], W[59]), compute state_59. Store: state_59 → (W57, W58, W59).
2. BACKWARD: enumerate W[60], derive what state_59 the de60=0 cascade-2 trigger needs.
3. MATCH: intersect forward state set with backward required set.
   Any intersection = full collision.
```

This is the M16-MITM design from our SCALING_PLAN — already implemented, in
Python, validated at sr=60 under restricted (W[58], W[59]) fixed-to-cert.

## Gap to M16-MITM target

The Python script:
- Operates at **N=32 sr=60** (proof-of-concept), not N=16 sr=63.
- Uses fixed W[58], W[59] = cert values (a 32-bit MITM, not a full one).
- No N parameterization; SHA-256 functions hardcoded.
- Storage in RAM (Python dict), not disk-backed.

To turn into M16-MITM:
1. Port to C with N parameterization (10 LOC change to a copy of backward_construct_n10.c).
2. Replace fixed W[58]/W[59] with full enumeration (2^16 × 2^16 = 2^32 forward at N=16).
3. Disk-backed storage of forward records (64 GB at N=16 spec).
4. Backward enumerator follows similar pattern to forward.
5. Hash-join in a separate program (read both files, merge by state_59 key).

Estimated effort: 2-3 days focused implementation. About the same as porting backward_construct.c was.

## Concrete next-implementer steps

If a future macbook session picks up M16-MITM:

1. **Read** `q5_alternative_attacks/mitm_cascade_sr60.py` carefully. The forward
   enumeration logic is clean Python; port loop-by-loop.
2. **Reuse** `backward_construct_n10.c`'s scaffolding (constants, primitives,
   round function, scaled rotations).
3. **Write** `m16_mitm_forward.c`: enumerate (W57, W58) at N=16, emit
   (state_59, W57, W58) records to disk. Expected size: 2^32 × ~24 bytes = 96 GB.

   *Optimization*: if state_59 has fewer effective bits than 16×8=128 (because
   cascade structure constrains da[57..59]=0), the keyed signature is shorter,
   reducing storage. Worth measuring at N=10 first via a quick Python pilot.
4. **Write** `m16_mitm_backward.c`: enumerate W59 + W60 backward from de61=0,
   emit (state_59_required, W59, W60) records.
5. **Write** `m16_mitm_match.cc`: hash-join the two files. Stream forward
   records into RAM-resident hash table keyed on state_59. Stream backward
   records, lookup each, emit matches. ~10 minutes wall.
6. **Verify** each match via independent forward run at N=16 (Phase-4-style).

## Why this matters for block2_wang's headline ETA

If M12 PASSES (in flight as of 2026-04-25 evening), then M16-MITM is the next
gate. It's the "does the architecture work?" check. Single-machine, ~25 min wall
+ 64 GB storage.

If M16-MITM passes, M32-MITM follows the same architecture but with **10 TB
storage** (per SCALING_PLAN Stage 4) and **multi-day fleet compute**. That's
where the bet either headline-hits or fails honestly.

## Caveats — UPDATED 2026-04-25 evening after sanity test

- The Python prototype has **never been validated** at the M16 use case.
  Its sr=60 validation used cert-fixed W[58]/W[59], so the math is not
  exercised at full enumeration.
- **CRITICAL**: a quick sanity test of `m16_mitm_forward_n10` (NAIVE port)
  showed full N=10 enumeration produces ~23 GB of records (2^30 × 22
  bytes). At N=16 this scales to 2^48 × 22 bytes = **6.6 PB**. Storage is
  the BLOCKING ISSUE, not compute.
- The naive design "emit every (W57, W58, W59) record" doesn't work for
  MITM because state_59 is too SPARSE in the signature space (8 × 16 = 128
  bits at N=16, 2^48 records means ~2^80 collision-free space — no MITM
  matches will fire by coincidence).
- Real MITM design must EMIT ONLY records SHARING A SHORT SIGNATURE.
  Concretely: keyed match must use a smaller state digest, e.g., the
  4-d.o.f. residual variety from mitm_residue (4 × 16 = 64 bits at N=16).
  At 2^48 forward records over 2^64 signature space, expected match-hits
  per backward record = 2^48/2^64 = 2^-16 — too sparse.
- For MATCHES to FIRE: forward records × backward records / signature
  space ≥ 1. Need forward × backward ~ 2^k where signature = k bits.
- **REVISED M16-MITM design needed**: signature width and enumeration
  scope must be co-designed. q5/mitm_cascade_sr60.py had this right at
  sr=60: the forward enumerated 2^32 W57 trials with cert-fixed
  W[58,59]; signature was state_59 of pair-1 (8 × 32 = 256 bits, but
  cascade-zeroed the a-path, so effective signature width was 4 × 32 =
  128 bits or so); backward enumerated 2^32 W60 trials.
  At 2^32 × 2^32 / 2^128 = 2^-64 → no MITM match at sr=60!
  The Python prototype was a **proof of concept on signal architecture**,
  not a winning algorithm yet.
- Re-design for M16: the M16-MITM proof requires either a SHORTER signature
  (using R63 modular relations to reduce key space) or a NARROWER
  enumeration scope. **This is the actual hard work** — not the
  C-port-from-Python which is straightforward.

## Realistic estimate

The M16-MITM milestone as originally framed in SCALING_PLAN ("MITM works
at N=16 for ~25 min wall + 64 GB storage") is over-optimistic without the
co-design above. Realistic: 1-2 weeks of design + implementation to make
the signature scheme produce match-hits at all.

This is now the active M16 design question. **No multi-machine compute
authorization needed** until the signature design produces a non-trivial
hit-rate prediction.

## Tracking

This file is a HANDOFF artifact. Next implementer:
- Update SCALING_PLAN Stage 3 with implementation start date.
- Update BET.yaml current_progress.
- Cross-link this file from `mechanisms.yaml` next_action.
