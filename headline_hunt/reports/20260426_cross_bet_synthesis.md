# Cross-bet synthesis: B1 + C1 + D2 findings restructure 3 bets
**2026-04-26 14:35 EDT**

Three cheap probes from this afternoon's task list connect findings
across `singular_chamber_rank`, `cascade_aux_encoding`,
`mitm_residue`, and `negatives.yaml`. This memo synthesizes the
implications.

## The three findings

### B1 — bit=19 floors at HW5, NOT HW4 (commit b760423)

1B-trial walk on idx=1 (`bit19_m51ca0b34_55`, de58_size=256 — the
extreme-compression cand mitm_residue named "priority MITM target")
reached only D61=HW5. Other cands floor at HW4. **bit=19 is HARDER
under random-flip walks, not easier.**

### C1 — cascade_aux Mode B speedup highest at singular_chamber W57s (commit 0605195)

W57-fixed cascade_aux Mode A/B sr=61 CNFs at the 3 HW4-frontier W57
chambers gave Mode B speedups of 2.82-3.18× at 50k conflicts —
clustering at the **top quartile** of the 16-cand cascade_aux
distribution (median ~2.0×). **The structurally-chosen W57 chambers
maximize Mode B preprocessing value.**

### D2 — bit=19 marginals strongly non-uniform (commit 505859b)

bit=19's de58 image at 1M samples: 13 fully locked bits + 5
partial-locked (marginals 0.125/0.25/0.75/0.875) = **18 of 32 bits
structurally non-uniform**. The original `bdd_marginals_uniform`
negative was tested on generic cands and missed structurally
distinguished ones. **Negative reopened with refined scope.**

## What changes for each bet

### `singular_chamber_rank` — operator family is the gate

Before: the bet was about finding lower-rank chambers in the sr=61
defect map.

After (post B1 + C1 + D2 + the morning's 11-walk campaign):
- The **structural floor under random-flip greedy walks is HW4 D61**,
  reproduced across 3 distinct cands at distinct sparse-off58 chambers.
- bit=19's "extreme compression" doesn't translate to lower D61 floor
  (counterintuitively HIGHER at HW5).
- **Mode A wall is the empirical ranking function** for which W57
  chambers are productive (high Mode A → high Mode B preprocessing
  value, high search budget needed).

Implication: the bet's next layer must change OPERATOR family. Yale's
carry-aware repair (in flight on linux_gpu_laptop) is the structural
track. M5 complement: tasks E1 (carry-aware perturbation), E2 (pair-
bit flips). Without an operator change, more raw depth on greedy-flip
is at the information limit.

### `cascade_aux_encoding` — predictor extends to chosen-chamber CNFs

Before: the morning's n=16 sweep established Mode A wall predicts
Mode B speedup (ρ=+0.976 at 3-seed median) on randomly-distributed
cands.

After (post C1):
- Predictor **extends to chosen-chamber CNFs** (W57 fixed at
  singular_chamber HW4 chambers) — same Mode A → speedup relationship.
- The chosen W57 chambers happen to be at the **HIGH end** of the
  predictor distribution: Mode A baseline 3.0-3.2s vs population
  median 2.0s, Mode B speedup 2.8-3.2× vs median 2.0×.
- **Cross-bet leverage validated**: structurally identifying high-A
  W57 chambers via singular_chamber → automatic high-Mode-B targets.

Implication: the cascade_aux bet's Mode B has a clean targeting story
now. **For maximum Mode B preprocessing speedup, generate CNFs at
W57 values from singular_chamber HW4 frontier**, not at random W57.
Adds the Mode A wall predictor as an actionable tool for the
cascade_aux cands list.

### `mitm_residue` — priority-target framing invalidated

Before: the bet's BET.yaml current_progress declared `bit=19
m=0x51ca0b34` as the "PRIORITY MITM TARGET" with arguments:
- de58_size=256 (forward table built)
- 17 hard bits at round 60
- 3 bits below next-best on hard-bit predictor

After (post B1 + D2):
- bit=19 has the **highest D61 floor** under random-flip walks (HW5
  vs HW4 elsewhere). The "compression → search advantage" hypothesis
  is the wrong framing.
- bit=19 marginals ARE non-uniform (D2 confirms 18 of 32 bits
  structurally distinguished) — so the "priority target" framing was
  pointing at REAL structure, but the structure doesn't help random-
  flip walks.
- **The structure helps SAT branching heuristics that exploit it,
  not greedy-flip walks.** Untested whether kissat with custom
  branching priority on bit=19's locked bits would solve faster.

Implication: mitm_residue's BET.yaml current_progress should note
the framing correction. The forward-table apparatus is still valid,
but its "priority MITM target" argument was based on metrics
(de58_size, hard-bit predictor) that 20260425 validation matrix and
B1 both showed are search-irrelevant. **The real next move is
locked-bit-priority kissat decisions**, not more forward-table work.

### `negatives.yaml/bdd_marginals_uniform` — reopened with scope

Before: closed 2026-04-15 with EVIDENCE level. Tested on generic
cands at N=8/10/12.

After (post D2): reopened with refined scope:
- **Holds for generic cands** (de58_size near population median).
- **Falsified on structurally distinguished cands** (e.g., bit=19
  with de58_size=256 << median).

The `would_change_my_mind` criterion ("non-uniform marginals on a
structurally distinguished candidate") fired. Action items:
1. Test conditional marginals (given partial assignment).
2. Test custom kissat branching that prefers locked-bit decisions.

## Synthesized rec — what should the fleet build next?

Three productive directions emerge from the synthesis:

1. **Carry-aware perturbation operator (E1/E2)** — the singular_chamber
   work has done all the structural mapping; what's missing is an
   operator that moves DIFFERENTLY than greedy-flip. E1 + E2 are
   the natural M5 complement to yale's structural track.

2. **Locked-bit-priority kissat** (newly motivated by D2) — D2 shows
   bit=19 has 13 binary-locked + 5 partial-locked bits in its de58
   image. A kissat run that decides on these bits FIRST would test
   whether the predictor closure (validation matrix) was wrong about
   structure-aware branching. Cheap experiment: ~30 min implementation
   if kissat exposes a phase-saving / decision-priority knob; ~30 min
   compute. **High info-per-CPU-hour** if it works.

3. **Mode B at singular_chamber W57 chambers as high-leverage
   deployment** — C1 shows these chambers are top-quartile Mode B
   speedup. cascade_aux's productive deployment is at structurally-
   chosen W57s, not random ones. Update cascade_aux's targeting
   strategy.

## Run inventory through this synthesis

Today's M5 + linux_gpu_laptop campaign:
- **15 1B-trial M5 walks** + **6 GPU OpenCL chart scans** + **multiple
  yale structural enumerations** (radius-7, kernel-rep, bridge,
  pooled frontier, fiber exhaustion).
- **5 commits today on cross-bet leverage**: b760423 (B1), 0605195
  (C1), 505859b (D2), fb6771b (registry fix), this synthesis G1.
- **Frontier**: D61 HW4 (3 cands) / tail HW59 (idx=8). Stable across
  5 convergent attack vectors.

## What still hasn't been done

- E1: carry-aware perturbation operator (M5 prototype)
- E2: pair-bit flip operator
- Locked-bit-priority kissat experiment (newly motivated by D2)
- D1: N-scaling probe of S/R compression
- F1: HW1 chart discovery on cands 4-17 (marginal value)
- G2: final campaign-wrap (after E1/E2 ship)

## Closing

The three findings together restructure how to think about
sr=61 cascade attacks:
- **The objective HAS structure** (D2 confirms — locked bits exist).
- **The CURRENT operators don't exploit it** (B1 confirms — random-
  flip walks don't improve on bit=19's structure).
- **Predictor models extend cleanly across structurally-related CNFs**
  (C1 confirms — Mode B preprocessing scales the same way at
  chosen-chamber W57s).

The next bet needs to bridge structure-aware branching (or perturb-
ation) with the existing predictor models. That's not a new bet —
it's a sharpened version of `cascade_aux_encoding` + `singular_chamber_rank`
combined. Mode A wall ranking + locked-bit branching priority +
carry-aware perturbations — three knobs that current vanilla kissat
+ greedy-flip don't touch.
