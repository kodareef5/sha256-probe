# Free-Word Shaping + Meet-In-The-Middle

Date: 2026-05-17

Core idea: do not ask CDCL to discover the whole tail at once. Use the remaining
free words as a controllable interface, shape each side into a compact residue,
then match the residues.

This is the most direct form of:

> if the remaining free words can be solved or shaped, meet in the middle.

## What the free words buy

For the verified sr=60 certificate:

```text
free: W57, W58, W59, W60
fixed by schedule: W61, W62, W63
```

The apparent roles are:

```text
W57: start the a-register zeroing cascade
W58: shape state and schedule compatibility
W59: shape state and schedule compatibility
W60: start the e-register zeroing cascade
```

For true sr=61:

```text
free: W57, W58, W59
schedule-derived: W60, W61, W62, W63
```

So the key question becomes:

```text
Can W57,W58,W59 be shaped so that schedule-derived W60 equals the W60
the cascade/tail needs?
```

This is a meet-in-the-middle problem over the W60 defect.

## Primary MITM cut: W60 defect

Define:

```text
S(W58) = schedule-derived W60 differential
R(W57,W58,W59) = round-state-required W60 differential
D(W57,W58,W59) = S(W58) - R(W57,W58,W59) mod 2^32
```

sr=61 requires:

```text
D = 0
```

Instead of solving this as one 96-bit search, split it:

1. Enumerate or sample `(W57,W58)` chambers.
2. For each chamber, compute the schedule-side target image `S(W58)`.
3. Enumerate or solve `W59` completions that make `R` land in that image.
4. Store compact keys:
   - low bits / selected bits of `D`,
   - carry signature,
   - D61 residual,
   - final tail residual.

This turns "find the whole collision" into "find a chamber where the two W60
maps have an unusually fat intersection."

## Secondary MITM cut: tail closure

Even exact `D=0` may leave a round-61 or final-tail residual. Use a second
interface:

```text
forward side: W57,W58,W59 -> state at round 60/61
backward side: desired zero final state -> required state/residue at round 60/61
```

Possible match keys:

- `(g60,h60)` hard residue,
- D61 active-bit set,
- `dh + dCh` round-61 residual form,
- final tail HW bucket,
- carry chamber signature from rounds 60..63.

The existing `q4_mitm_geometry/cascade_mitm_full.py` recovers the sr=60
certificate. The next step is to replace "recover cert" with a real keyed table.

## Third MITM cut: sr64 message-space inverse

For sr=64, no tail words are free. The real message block must produce the
tail words:

```text
message words W0..W15 -> W57,W58,W59,W60
```

So keep a library of shaped tail tuples and meet it with schedule-derived
message-space tuples:

```text
tail side: shaped tuples with low residual
message side: real schedules near those tuples
```

This is not yet full sr=64, but it avoids treating schedule compliance as an
afterthought. It asks whether the shaped tail manifold intersects real message
space.

## Concrete experiments

### E1. Reduced-N exact MITM

Run at N=8,10,12 where ground truth is available.

Deliverable:

- `headline_hunt/bets/mitm_residue/results/free_word_mitm_reducedN.md`

Done when:

- MITM recovers known sr=60 collisions.
- MITM finds D=0 sr61-compatible points when they exist.
- Runtime and memory beat brute force or explain why they do not.

### E2. W60-defect table

Build a table keyed by partial `D` and carry signature:

```text
key = selected_bits(D) || carry_chamber_id || D61_bucket
value = compressed (W57,W58,W59) witness
```

Start with selected bits that existing analysis says are hard:

- D60 exact bits,
- D61 HW4/HW5 active bits,
- `(g60,h60)` residue bits,
- sigma1-aligned bits of W60.

Deliverable:

- `headline_hunt/bets/singular_chamber_rank/results/w60_defect_mitm_table.md`

Pass condition:

- Table shows fat buckets or repeated carry chambers that are not explained by
  random occupancy.

### E3. Shape-then-solve CNFs

Use MITM output to generate small assumption CNFs:

```text
candidate chamber + partial D bits + carry signature + low D61 target
```

Then run SAT only inside those shaped chambers.

Deliverable:

- `headline_hunt/bets/sr61_n32/results/shape_then_solve_sr61.md`

Pass condition:

- Shaped CNFs reduce conflicts or improve residuals versus unshaped sr61 CNFs.

### E4. Schedule inverse library

Given shaped tail tuples, try to find real message schedules near them.

Tasks:

- Build linear no-carry inverse from message bits to W57..W60.
- Add carry-aware repair moves.
- Score by distance to shaped tuple and preservation of cascade gates.

Deliverable:

- `headline_hunt/bets/math_principles/results/shaped_tail_schedule_inverse.md`

Pass condition:

- Real schedules land closer to shaped sr61/sr60 tail tuples than random.

## Warning signs

- If the match key is too large, MITM becomes disguised brute force.
- If the key is too small, matches will be false positives that SAT rejects.
- If reduced-N MITM does not beat brute force, do not scale to N=32.
- If `D=0` exact points always destroy tail closure, the right key is not D
  alone; include round-61/tail carry signatures.

## Best immediate build

1. Fork `q4_mitm_geometry/cascade_mitm_full.py`.
2. Replace certificate-only validation with a real hash table over a chosen
   reduced-N key.
3. Validate at N=8 against known collision counts.
4. Add `D`/D61/carry signature to the key.
5. Only then scale the table design toward N=32.

## 2026-05-17 first pilot

Implemented the first reduced-N W60-interface prototype:

```text
headline_hunt/bets/mitm_residue/prototypes/free_word_mitm_reducedn.c
```

Result memo:

```text
headline_hunt/bets/mitm_residue/results/20260517_free_word_mitm_reducedn.md
```

The pilot says `D60=0` is abundant but random-rate at N=8/N=10 and does not
close the tail by itself. The next MITM key should include `D60`, r61 residual
bucket, and tail carry chamber signature.
