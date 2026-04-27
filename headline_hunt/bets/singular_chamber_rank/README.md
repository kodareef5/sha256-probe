# bet: singular_chamber_rank — lower-rank sr=61 defect chambers

## The bet

The cascade sr=61 barrier is usually modeled as a uniform 32-bit schedule
defect: the schedule-derived `W60` misses the cascade-required `W60` with
probability `2^-32`.

This bet asks a different question:

> Are there chambers of the SHA-256 Boolean/carry state space where that
> defect map has rank less than 32?

If the local image rank of the defect map drops from 32 to `r`, then the
expected sr=61 compatibility cost drops from `2^32` to about `2^r` inside
that chamber. A rank-20 chamber would be a 4096x structural reduction even
before SAT or GPU search.

## Object being measured

For a cascade-eligible N=32 candidate and free words `(W57,W58,W59)`, build
the normal cascade through rounds 57, 58, and 59:

- choose `W2[r] = W1[r] + cascade_offset(r)` for `r in {57,58,59}`;
- compute the schedule-derived `W1[60]` and `W2[60]` from `W[58]`;
- compute the cascade-required round-60 offset from the round-59 state.

Define:

```text
D(W57,W58,W59) =
    (W2_sched60 - W1_sched60) - cascade_required_offset60  mod 2^32
```

The usual sr=61 cascade compatibility event is `D=0`.

The first tool measures the GF(2) rank of the local Boolean derivative of
`D` with respect to the 96 input bits of `(W57,W58,W59)`.

The second-stage result decomposes the defect as:

```text
D(W57,W58,W59) = S(W57,W58) - R(W57,W58,W59)
```

For fixed `W57`, the schedule target is:

```text
S(W58) = C + sigma1(W58 + off58) - sigma1(W58)
```

This additive finite-difference map has a highly compressed image for many
`off58` values. The current best mechanism is not low local derivative rank,
but alignment between a compressed `S(W58)` plateau and a fat preimage bucket
of the round-required map `R(W59)`.

## Why this is not the same as de58/hardlock

`de58_size` and hardlock bits measure projection structure in the cascade
boundary state. They have already been shown search-irrelevant for CDCL.

This bet measures the actual sr=61 obstruction map. The target is not a
smaller projection; it is a lower-rank obstruction.

## What would be a hit

- Any reproducible N=32 candidate/sample with local defect rank below 32.
- A statistical enrichment of low-rank samples around a recognizable gate
  chamber, such as `f=g` in both paths for `Ch`, or `b=c` in both paths
  for `Maj`.
- A fill/kernel family where the minimum observed rank is consistently
  below the baseline across independent seeds.

## What would kill this first version

If all sampled candidates show rank 32 across broad random and structured
samples, then the simple local-Jacobian form of the singular-chamber idea is
not useful. The broader idea would remain open only through nonlinear
fiber-size measurements, nonzero gate-invisible trails, or block-2 chambers.

## Tools

Compile from repo root:

```bash
gcc -O3 -march=native -fopenmp -I. \
  headline_hunt/bets/singular_chamber_rank/tools/singular_defect_rank.c \
  lib/sha256.c -lm -o /tmp/singular_defect_rank
```

Local-rank probe:

```bash
/tmp/singular_defect_rank 2048 8
```

Boolean-Newton defect-correction probe:

```bash
/tmp/singular_defect_rank newton 1024 8 24
```

Reduced-N exact fiber counter:

```bash
gcc -O3 -march=native -fopenmp -I. \
  headline_hunt/bets/singular_chamber_rank/tools/defect_fiber_counter.c \
  lib/sha256.c -lm -o /tmp/defect_fiber_counter

/tmp/defect_fiber_counter 12 11 0xfff 0
/tmp/defect_fiber_counter single 12 11 0xfff 0x666
/tmp/defect_fiber_counter hits 12 11 0xfff 0x666 0x393
/tmp/defect_fiber_counter reqhist 12 11 0xfff 0x666 0x393
/tmp/defect_fiber_counter schedscan 12 11 0xfff 0x666
/tmp/defect_fiber_counter sigmadiff 16 0x8000
/tmp/singular_defect_rank off58hill 512 8 32
/tmp/singular_defect_rank schedsample 0 0x370fef5f 1000000 22
/tmp/singular_defect_rank defecthill58 3 0xe28da599 0x233e4216 2048 8 32
/tmp/singular_defect_rank tailpoint 3 0xe28da599 0xa3110717 0x1afa1270
/tmp/singular_defect_rank manifold61point 3 0xe28da599 0x5e06f0a7 0x28859825
/tmp/singular_defect_rank tailhill57 8 0xaf07f044 524288 8 64
/tmp/singular_defect_rank carryjump61point 0 0x370fef5f 0x0e4363c9 0xfe337af3
/tmp/singular_defect_rank kernel61linearpoint 8 0xaf07f044 0xe98d86d0 0xc778e588
/tmp/singular_defect_rank tailhill58 0 0x370fef5f 0x0e4363c9 65536 8 64
/tmp/singular_defect_rank surface61walk 8 0xaf07f044 0xe98d86d0 0xc778e588 32768 8 24 12
/tmp/singular_defect_rank surface61sample 8 0xaf07f044 65536 8 24
/tmp/singular_defect_rank surface61greedywalk 8 0xaf07f044 0xe98d86d0 0xc778e588 65536 8 80 24
/tmp/singular_defect_rank frontier61pool 8 262144 8 80 32 0xaf07f044 0xdd73a9d7 0x57046fad 0xaf07f044 0x464b2c4c 0xef7b2fae
/tmp/singular_defect_rank nearexact61point 8 0xaf07f044 0xdd73a9d7 0x57046fad 6
/tmp/singular_defect_rank ridge61walk 8 0xaf07f044 0xddf3a9d3 0x76046f0d 1048576 8 128 24 8
/tmp/singular_defect_rank capped61walk 8 0xaf07f044 0xdd55ab86 0x1d9ca68f 1048576 8 128 24 4
/tmp/singular_defect_rank pair61residualpoint 8 0xaf07f044 0xdd55ab86 0x1d9ca68f 4
/tmp/singular_defect_rank carrycmp61point 8 0xaf07f044 0xdd73a9d7 0x57046fad 0xaf07f044 0xfd772dd7 0xc30e0ff7
/tmp/singular_defect_rank bridge61point 8 0xaf07f044 0x1cbb355e 0xad34d2a3 0x7fc3124f 0xbf245aa1 1
```

Key result notes:

- `results/20260426_local_rank_probe.md`: local rank stayed full.
- `results/20260426_fiber_count_probe.md`: nonlinear fibers and carry
  signatures appeared at reduced N.
- `results/20260426_schedule_finite_difference_probe.md`: schedule-side
  finite-difference collapse and `S`/`R` target alignment.
- `results/20260426_fulln_sparse_offset_probe.md`: full-N sparse `off58`
  steering, sampled schedule collapse, R-side falsification, one-bit near
  misses, and an exact sr=61-compatible point whose tail fails again at
  round 61. Follow-up probes map the round-61 tangent/kernel geometry and
  show that sparse `off59` is reachable but not sufficient by itself; exact
  `defect60=0` reduces the round-61 required offset to `dh+dCh`, and failed
  Newton jumps are carry-chamber transitions. Local perturb/project walks
  return to the same exact-point attractor basin rather than moving freely on
  the surface; codimension-one kernel corrections exist linearly but require
  high-Hamming deltas that break the exact carry chamber. Greedy one-bit
  repair can cross exact basins; the current frontier is round-61 defect HW4
  and a separate checked 57..63 tail HW59 basin. Bridge enumeration shows the
  new basins are connected by thin carry transitions with one-bit `defect60`
  ridges nearby, not by broad local exact sheets. Radius-6/7 ridge enumeration
  is now a productive way to find non-exact low-D61 shelves that repair into
  new exact basins; weighted `ridge61walk` preserves low D61 during D60 repair
  and found an exact HW6 point from the radius-7 shelf. Capped-D61 walks now
  expose a discrete terrace: exact D60 is available at D61 HW5, but D61 cap 4
  bottoms at D60 HW4/D61 HW4, and D61 cap 3/2 bottoms at D60 HW7. Radius-7
  enumeration around the HW4/HW4 terrace checked 704M neighbors with no exact
  D60 point. A later M5 1B walk from the HW5 base found exact D61 HW4 on idx0.
  A linux 1B follow-up from that HW4 point found no HW3, but improved idx0's
  checked tail to HW66. Carry-coordinate comparison
  shows exact HW5/HW67 basin moves are round-61 Ch-only, while the cap-4
  terrace activates Sigma1 and T2 terms that exact D60 repair tends to remove.
  Cross-candidate walks show the mechanism is not unique to idx8: idx0 reaches
  exact D61 HW4, idx3 reaches exact D61 HW7, and idx8 tail improves to HW59.
  A 64-flip mixed-seed pool and residual-fiber enumeration did not repair the
  cap terrace back to exact D60 with a better D61 or tail. OpenCL GPU W57/off58
  scans are working; first chart tests show sparse off58 alone is not the
  ranking function, and macbook confirmed idx17 reaches HW4 even with the
  sparsest known `off58=0x00000001`. Deterministic `d60repairfiberseq` sweeps now exhaust full
  `2^32` D60 kernels for the HW2 shelf, cap-4 terrace, a local HW3 shelf, and
  the idx17 D60-HW7/D61-HW1 shelf; exact D60 landings exist, but none preserve
  the low-D61 caps. Additional GPU-found off58-HW1 charts on idx9/13/14/15
  did not beat the known exact-D61 frontier. W57-free beam/greedy probes found
  new exact-D60 landings and low-D60 terraces, but did not improve D61 HW4 or
  tail HW59. W57-free affine-fiber sampling and low-weight kernel enumeration
  reached D60-HW1, but found no exact D60 and no cap-preserving bridge.
  Schedule-constrained message-space guard repair now has corrected
  changed-vs-default counters: deterministic repair, randomized gauge repair,
  linearized guard-kernel projection, one-word repair, and adaptive chart
  repair all fail to find a changed exact `a57=0` guard fiber in the first
  probes. New GPU sparse-chamber scans found exact-D60 footholds on several
  macbook/F-series candidates plus off58-HW1 idx18 and bit17 chambers, but
  sparse `off58` still does not predict the D61 floor by itself.
- `results/20260426_m5_1B_deep_descent.md`: macbook M5 1B-trial walk that
  verified the HW5 round-61 and tail-HW68 frontiers.
- `results/20260426_m5_1B_from_HW5.md`: macbook M5 1B-trial walk from the HW5
  base; no D61 HW4/HW3 found, but checked tail improved to HW67.
- `results/20260426_m5_3cand_HW5_reproduces.md`: macbook M5 cross-candidate
  1B sweep; idx0 also reaches exact D61 HW5, while idx3 floors at HW6 in that
  raw-walk batch.
- `results/20260426_HW4_D61_breakthrough.md`: macbook M5 1B-trial walk from
  the idx0 HW5 base; first exact D61 HW4 point at full N.
- `results/20260426_HW4_idx17_third_cand.md`: macbook confirmation that HW4
  reproduces on idx17, the sparsest known off58 chamber (`0x00000001`).
- `results/20260426_cross_chamber_pool.md`: pooled exact-surface walks over
  idx8/idx0/idx3; later updates put the current best exact/tail frontiers at
  idx0 HW4/tail-HW66, idx8 HW5/tail-HW59, and idx3 HW7/tail-HW72.
- `results/20260426_linux_hw4_gpu_followup.md`: linux verification and
  follow-up after HW4, including no HW3 in a 1B HW4 walk, idx0 tail-HW66,
  residual-fiber negative checks, and first OpenCL GPU chart scans.
- `results/20260426_d60_fiber_exhaustion.md`: deterministic full-kernel
  D60 repair-fiber sweeps over the low-D61 shelves, including the idx17
  D61-HW1 shelf; no exact low-cap representative appears inside the
  D60-linear fibers. The same note records GPU-discovered off58-HW1 charts
  whose downstream D61 floors remain worse than the known frontier.
- `results/20260426_w57_free_operator_probe.md`: beam and greedy repair with
  W57 allowed to move; new exact-D60 landings appear, but the useful carry
  chart is not preserved and neither D61 nor tail improves.
- `results/20260426_w57_affine_fiber_probe.md`: 96-bit D60 affine-fiber
  sampling and low-weight kernel enumeration over W57/W58/W59; D60 can be
  reduced to HW1, but D61 rises sharply and no exact/cap-preserving bridge is
  found.
- `results/20260426_w57_free_chart_walk.md`: W57-free chart walks over the
  exact HW4 bases; 200M trials found more than 2.4M exact-D60 landings, but
  no exact D61 HW3. The HW3 shelves require large off58/off59 and round-61
  carry-chart changes.
- `results/20260426_f12_candidate_transfer.md`: cross-bet transfer probe for
  macbook's F12 residual-grid candidates. Their F12 min-W57 chambers do not
  directly match this bet's `off58`, but GPU scans found sparse singular
  charts; best downstream result is bit17 exact D61 HW6/tail-HW67.
- `results/20260427_message_space_guard_probe.md`: schedule-constrained
  message-space projection after the F14/F15 correction. The guarded map
  `(a57_xor, defect57..61)` has full local rank 192 over the 14 free message
  words; unguarded D57 hits can be false positives when `a57_xor != 0`.
  Corrected multi-axis walks reduce the guarded slot-57 prefix to HW7 but
  find no exact guarded cascade hit. Guard-fiber repair variants currently
  return to the default chart rather than a changed exact guard fiber.
- `results/20260427_gpu_sparse_chamber_scan.md`: RTX/OpenCL W57/off58 scans
  plus exact-D60 CPU follow-up on bit13/bit15/bit19/bit14/idx18 sparse
  chambers.
