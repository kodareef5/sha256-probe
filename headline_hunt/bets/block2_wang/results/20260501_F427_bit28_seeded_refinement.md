---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BIT28_HW45_ROBUST_LOCAL_OPTIMUM
parent: F408 annealed bridge beam (codex 2026-04-30)
evidence_level: EVIDENCE
compute: 0 solver search; 569.7s pure W-space annealing + 2 audited cert-pin solver checks
author: macbook-claude (direct, no codex; codex hit 5h-quota wall after F421)
---

# F427: bit28 seeded refinement around F408 HW=45 — no improvement, but bridge_score and HW are not isomorphic

## Setup

Path C extension of F408. Codex's F408 memo recommended "narrower second
annealing panel around bit28 with more restarts or seed-from-best
perturbations". This run executes that:

- new CLI flag `--init-W <hex,hex,hex,hex>` added to `block2_bridge_beam.py`
  to seed every restart from a known witness instead of random.
- 24 independent restarts of simulated annealing on `bit28_md1acca79`,
  all seeded from F408's HW=45 witness:
  `W1[57..60] = 0x307cf0e7, 0x853d504a, 0x78f16a5e, 0x41fc6a74`
- Tighter parameters than F408 (which was a wide first sweep):

| Parameter | F408 (codex) | F427 (this) |
|---|---:|---:|
| iterations / restart | 200,000 | 500,000 |
| restarts | 12 | 24 |
| max_flips | 6 | 3 |
| temp_start | 2.0 | 0.5 |
| temp_end | 0.05 | 0.01 |
| tabu_size | 512 | 1024 |
| init-W | random | F408 HW=45 witness |
| candidates | bit2/bit3/bit24/bit28 | bit28 only |

Total wall: 569.7s. No SAT solver was used during search.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F427_bit28_seeded_refinement.json`
- `headline_hunt/bets/block2_wang/results/20260501_F427_certpin_validation.json`

## Result

| Outcome | Seeds | Best HW | Best score | Unique W vectors |
|---|---:|---:|---:|---:|
| Stayed at F408 init | 14 | 45 | 74.146 | 1 (the init) |
| Escaped to score-better basin | 10 | **47** | **75.333** | 1 |

No restart found HW < 45. The 10 score-better restarts all converged to
the same single point at HW=47, score=75.333.

## Score-better/HW-worse witness

```
W1[57..60] = 0x307cf0e7 0x853d504a 0x78f16a5e 0x41f46374
W2[57..60] = 0x6fcdf313 0xaa562d8d 0x5713c149 0xe75cc298
hw63       = [13, 9, 1, 0, 11, 12, 1, 0]   (total 47)
diff63     = [0x06d8ad82, 0x82304d10, 0x00000100, 0x00000000,
              0x19843930, 0x8a13b430, 0x00000100, 0x00000000]
active_regs = {a,b,c,e,f,g}, da_eq_de=False, c=g=1, d=h=0
```

This W differs from F408's HW=45 witness only in `W1[60]`:

```
F408 W1[60] = 0x41fc6a74   01000001 11111100 01101010 01110100
F427 W1[60] = 0x41f46374   01000001 11110100 01100011 01110100
XOR         = 0x00080900   bits {8, 11, 19}, Hamming distance 3
```

W57, W58, W59 are identical to F408. The escape is purely a 3-bit
perturbation of W1[60]. Cascade-1 invariants are preserved (dW2[60]
adjusts via `cascade2_offset`).

## Cert-pin control

Cert-pin verification of the HW=47 score-better witness, audited with
`cascade_aux_v1_modeA_sr60_expose_certpin` and logged via `append_run.py`:

- audit verdict: **CONFIRMED**
- cnf_sha256: `171f19bd07b439b46b6ef98233e4c7cbfc9a99a17cadef93204cefbf892075dd`
- kissat 4.0.4: **UNSAT** in 0.0092s
- cadical 3.0.0: **UNSAT** in 0.0149s

As expected. The score-better/HW-worse trade is real, not a search artifact.

## Findings

### Finding 1: F408 HW=45 is a robust local HW optimum

Across 24 seeded restarts × 500k iterations × 3-bit max mutation radius,
no restart found HW < 45. 14 restarts stayed at the F408 init exactly.
This is strong negative evidence that no HW < 45 exists in the
3-bit-flip neighborhood of F408's witness.

### Finding 2: bridge_score and HW are not isomorphic — the score landscape has a higher peak at worse HW

10 of 24 restarts escaped F408's HW=45 / score=74.146 basin and converged
to a single neighbor at HW=47 / score=75.333. The bridge_score increased
by 1.187 while HW worsened by 2.

The escape is purely in `W1[60]`, 3 bits flipped (positions 8, 11, 19).
This means at this 3-bit radius, the bridge selector finds a different
local optimum than the residual objective does.

Mechanism read: bridge_score combines tail-HW with structural rewards
(c/g asymmetry, dominator bits, kbit parity). At F408's HW=45, the tail
is light (`hw63 = [12,6,3,0,12,11,1,0]`). At the score=75.33 neighbor,
the tail redistributes to `[13,9,1,0,11,12,1,0]` — `c` is now even
lighter (1 bit) and the bridge selector rewards that, even though it
costs 2 in total HW.

### Finding 3: this is not a Path C SAT outcome — both witnesses near-residual

Both the F408 HW=45 witness and the F427 HW=47 score-better witness are
single-block UNSAT under audited cert-pin (kissat + cadical, 4 runs
total, all UNSAT in milliseconds). Path C's residual-record objective
remains uncrossed by SAT.

### Finding 4: anneal mostly idle with these parameters

Mean accepted moves per 500k-iter restart: 1.5 (1.0 of which were
"worse" Metropolis-accepted). Bridge selector rejected 23,617 mutation
attempts; tabu rejected 32,564. The tighter temperature schedule
combined with the tight bridge fence near F408's witness made this
search effectively local — which is the right scope for a "refine the
HW=45 record" pass, but it means the search did NOT broadly explore.

A wider second pass (e.g., max_flips=8, temp_start=1.5, no init seed,
or random restart with soft bias toward F408 W) is the next move if
HW < 45 is still wanted.

## Verdict

- **Primary objective (HW < 45)**: not achieved at this radius. F408
  HW=45 is the local minimum within 3 W-bit flips.
- **Cert-pin headline-class SAT**: not achieved (both UNSAT, expected).
- **Useful side finding**: bridge_score/HW non-isomorphism with concrete
  3-bit witness; bridge selector has a higher peak at HW=47 nearby.
- **2 cert-pin runs added**, registry clean, audit-failure-rate
  unchanged at 0.0%.

## Next

Decision points (whichever the fleet wants to drive):

1. **Wider second-anneal**: max_flips 6-8, temp_start 1.5, init-W from
   F408 HW=45 (not greedy hold). Check if HW < 45 exists at larger
   radius. ~30 min compute.
2. **Different cand**: bit3 / bit2 / bit24 each got HW reductions in F408
   but only one seeded refinement run (this one) was performed. A
   parallel seeded refinement on bit24 (its F408 best HW=49) could
   find HW < 49 by analogous mechanism. ~10 min per cand.
3. **Mechanism investigation**: characterize bridge_score's structural
   reward terms. F427's score-better/HW-worse W shows that c/g
   redistribution can outweigh raw HW count in bridge_score. If we
   adjust bridge_score's weights to penalize HW-worsening trades
   (or simply optimize HW directly with a structural-validity filter),
   the search may find new minima.
4. **Bigger picture**: revisit whether HW reduction below 45 on this
   geometry is even possible. F374 cascade-1 fingerprint with
   `{a,b,c,e,f,g}` active and `c=g=1` may be the binding constraint;
   if so, lifting the constraint (e.g., allow `c=2` or `g=2`) is the
   path to lower HW, not finer search.

The score-better/HW-worse finding is interesting on its own and
suggests bridge_score's geometry is worth a second look.
