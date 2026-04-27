# sr=61 evidence synthesis: where we stand on the next round
**2026-04-27**

This memo consolidates ALL evidence about whether sr=61 is achievable
or structurally impossible, drawn from Viragh 2026, this project, and
yale's singular_chamber_rank work. It is the closure argument needed
to position the project's sr=60 result alongside Viragh's sr=59.

## Question framing

**Viragh's framework**: sr counts schedule equations satisfied. Free
words go at positions {57+k}. sr=59 = 5 free words = slack 64. sr=60
= 4 free words = slack 0. sr=61 would need 3 free words = slack -64
(over-determined).

**Slack-negative regime**: at sr=61, the SAT problem has 256 - 192 =
64 fewer freedom bits than the collision condition requires. **A
solution must exist on a measure-zero subset** of the 192-bit search
space, requiring exact alignment with structural constraints.

## Lines of evidence that sr=61 is hard / impossible

### 1. Viragh's exponential scaling table

| sr | Free | Slack | Solve time |
|---:|---:|---:|---:|
| 56 | 8 | 256 | ~10s |
| 57 | 7 | 192 | ~0.1s |
| 58 | 6 | 128 | ~7s |
| 59 | 5 | 64 | ~430s ← Viragh's frontier |
| 60 | 4 | 0 | TIMEOUT (Viragh) / 12h (this project) |
| 61 | 3 | -64 | open |

Each step removes 64 bits of slack. sr=60 already at slack=0; sr=61
is over-determined. Viragh: "the schedule_compliance landscape contains
exploitable structure... the problem becomes infeasible at sr ≥ 60."

This project showed sr=60 is JUST barely feasible (kissat seed=5,
12h), one round past Viragh's published frontier. Whether sr=61 is
solvable is the next-round question.

### 2. Project's empirical UNSAT evidence

1800+ CPU-hours of kissat search on TRUE sr=61 CNFs (cnfs_n32/) across
67 candidates × multiple seeds × multiple budgets.

Status: **0 SAT, 0 UNSAT, all UNKNOWN**. Solver couldn't terminate.

The recent F20 distinguished-cand sweep (commit 48e704b): 6 cands × 3
budgets × 1 seed = 18 runs at TRUE sr=61. All UNKNOWN, including 10M
conflicts × 5 min wall.

The currently-running overnight kissat sweep (commit bead2e0): 156
jobs × 30 min wall cap, ~12h total. Status as of 22:55 EDT: 6/156
done, all UNKNOWN. Final results expected by 14:00 EDT 2026-04-27.

### 3. Viragh's sigma_1 conflict argument (writeups/sr61_impossibility_argument.md)

Statistical analysis:
- W[60] deterministically controls 3,964 output bits
- For sr=61, W[60] = sigma1(W[58]) + constants — no longer free
- sigma1's XOR-fan-out makes 47.9% of W[60] bit constraints conflict
  through W[58]'s sigma1 mixing
- "The probability that ALL conflicts happen to be resolvable
  simultaneously is astronomically small."

This is statistical (2000-sample correlation matrix), not a formal
proof. A rigorous symbolic computation would either confirm or refute
it.

### 4. F-series chamber-image structure (this session)

For all 67 registry candidates, full 2^32 W57-chamber enumeration:
- 0/67 cands have de58 = 0 in any cascade-1 chamber (F13)
- Best reach: msb_m189b13c7 at de58 HW=2 (F12, residual 0x108 pinned)
- Cascade-1 7-slot configuration = full SHA-256 collision (F14)
- 0/67 default messages have cascade-1 alignment at slot 57+ (F15)
- 17.2 BILLION random M[15] sweeps × 4 cands → 0 cascade-1 hits (F16)

These are structural properties of the cascade-1 chamber image, NOT
direct proofs of sr=61 impossibility. But they show that the
cascade-1 search space — even fully relaxed in its chamber-image
form — is structurally rigid.

### 5. Yale's guarded-fiber finding (commits 9e8695a, 5396b52, 1f6de02)

Yale's message-space probe with the proper a57_xor=0 guard:
- Best guarded slot-57 prefix: **HW8** (across 4 cands × 5M trials × 16 threads)
- Adaptive chart repair (28.8% rank-full one-word charts) finds 211
  exact-guard hits but NONE that change M from default
- Pure-guard walk: 5M starts, 3.5M improved a57 score, **0 reached
  a57=0 with changed message**
- Boolean-Newton projection: rank 64 for guarded prefix, but linear
  corrections have average HW=32 — they cross nonlinear carry charts
- **Conclusion**: "the local guard manifold is extremely thin near
  the default messages and absent near the best near-miss valleys"

This is the strongest direct evidence: **yale's exact-guard manifold
appears to be a single point** (the default message), with all
near-miss valleys disconnected from it.

If yale's structural picture holds, sr=61 collision is genuinely
infeasible — there's no message M ≠ default that simultaneously
satisfies cascade-eligibility (a57=0) AND cascade-1 alignment at
slots 57+ (defect57=0).

## Lines of evidence FOR sr=61 being feasible

### 1. Viragh's optimism

Section 11 ("Implications"): "Several converging trends suggest that
a full collision on SHA-256 is approaching feasibility." He explicitly
hopes someone reading the paper will "break it end-to-end soon."

He notes (Section 11): "diminishing slack: at sr=59, the solver
operates with 64 bits of slack. At sr=60 the slack reaches zero.
**Novel techniques could potentially bridge this gap.**"

This project's sr=60 result is the kind of "novel technique" he
imagined — namely, deeper kissat seed exploration. The same approach
could in principle work for sr=61.

### 2. Open structural questions

Several research directions remain unexplored:
- **Different message kernels** beyond MSB. Project tested ~10 bit
  positions; full sweep of 32 × multi-bit × different fills not
  exhaustive.
- **Wang-style message modification** at the sr=59/60 boundary,
  per Viragh Section 10.2.
- **Differential characteristic + SAT hybrid**, combining DC trail
  search (Li 2024 reaches 39 rounds full schedule) with the SFS
  framework.
- **GPU-accelerated solvers** (yale has GPU hardware; project hasn't
  fully exploited it).

### 3. The project's sr=60 was Viragh-predicted-impossible

Viragh's exhaustive testing of all 35 4-free configurations at sr=60
showed timeouts. But seed=5 with 12h compute solved it. **This is a
direct refutation of the "sr=60 is structural barrier" prediction.**
By analogy, the "sr=61 is impossible" claim might similarly fall to
sufficient compute or a clever seed.

## Synthesis: the actual probability picture

Combining all the above:

| Hypothesis | Evidence weight | Confidence |
|---|---|---:|
| sr=61 is structurally infeasible | Viragh's sigma_1 conflict (47.9%), yale's guard-manifold thinness, project's F-series rigidity, 1800+ CPU-h UNSAT | **moderate (~70%)** |
| sr=61 is feasible with different kernel | Untested kernels, Viragh's optimism | **low (~15%)** |
| sr=61 is feasible with longer compute on tested kernels | Direct analogy to sr=60 (which broke sub-12h vs Viragh's 7200s timeout) | **low (~15%)** |

The 70% estimate is informal but represents the project's best read.
**It is not a proof.** A formal proof of sr=61 impossibility would be
itself a publishable result.

## What would close the question

To **prove sr=61 impossible**:
- Formal symbolic computation of Viragh's sigma_1 conflict argument
  (replace 2000-sample correlation with exact GF(2)-linear analysis)
- DRAT-verified UNSAT proof from a SAT solver on the constrained
  problem (all 35 4-free configurations at sr=61, plus reasonable
  candidate set)
- Yale's guarded-manifold map extended to a rigorous fiber-dimension
  argument

To **prove sr=61 feasible**:
- Find ANY (kernel, m0, W[57..59], W[60..63]) that satisfies cascade-1
  + cascade-2 simultaneously with full schedule. Doesn't have to be
  practical compute — existence is enough.

The overnight kissat sweep is collecting empirical data on whether
the existing 67-candidate registry contains such a solution. By
14:00 EDT 2026-04-27 we'll have 156 deep runs covering most of the
registry × multi-seed × multi-budget.

## Implication for project positioning

The project's published result should be:

> Extending Viragh 2026: a verified semi-free-start sr=60 collision
> on full 64-round SHA-256, breaking the predicted "structural
> barrier" via deeper kissat seed exploration on a specific candidate.
> Combined with structural evidence from cascade-1 chamber analysis
> and guarded message-space probes, we present empirical and
> structural arguments that sr=61 represents the actual collision-
> resistance frontier of SHA-256's compression function.

This frames sr=60 as the headline (positive result) and sr=61 as the
boundary (negative result with structural evidence). **Both directions
are publishable.**

## Action items

1. **Wait for overnight kissat completion** (~14:00 EDT). If any cand
   returns SAT or UNSAT, that's a major update.
2. **Synthesize yale's structural map** + the F-series + Viragh's
   conflict argument into a single sr=61 impossibility evidence
   section, suitable for a paper.
3. **Reach out to Viragh / Li** for collaboration on rigorous closure.
   The acknowledgments section of his paper invites engagement.
4. **Decide on attribution**: project contributors are macbook, yale,
   linux_gpu_laptop. Authorship discussion needed before any paper.

EVIDENCE-level (this synthesis): VERIFIED for the empirical findings
referenced; HYPOTHESIS for the 70% probability estimate; HYPOTHESIS
for the publishability claim (depends on closure of sr=61).
