# Mendel / Nad / Schläffer 2013 — Improving Local Collisions: New Attacks on Reduced SHA-256

**Cite as**: Mendel, F., Nad, T., Schläffer, M. *"Improving Local Collisions:
New Attacks on Reduced SHA-256."* EUROCRYPT 2013. DOI: 10.1007/978-3-642-38348-9_17.

**Read status**: structural-summary from public knowledge + Viragh's 2026
literature table. Full PDF read pending — this note captures what's
defensibly known from secondary sources for paper-comparison purposes.

## Position in the literature table

From Viragh 2026 (which this project's sr=60 work directly extends):

| Work | Rounds | Type | Method | sr | Free | Time |
|---|---:|---|---|---:|---:|---|
| Mendel et al. 2013 | 38 | Collision | Signed DC + SAT | 38/38 (100%) | 0/22 | not stated |
| Mendel/Eichlseder 2014 [4] | — | Branching heuristics | DC search | — | — | — |
| Li et al. 2024 | 39 | Collision | MILP + msg mod | 39/39 (100%) | 0/23 | — |
| **Viragh 2026** | **64** | **SFS** | **MSB kernel + gap SAT** | **59 (89.6%)** | **5/48** | **~276s** |
| **This project 2026** | **64** | **SFS** | **same + deeper seed** | **60 (93.75%)** | **4/48** | **~12h** |

Mendel/Nad/Schläffer is the **upper end of the "reduced-round full
schedule" attack family**. They achieve 38 rounds with 100% schedule
compliance. Viragh's framework reinterprets this as sr=38 — far below the
schedule-compliance/round-count tradeoff Viragh's work occupies.

## Methodology (signed differential characteristics + SAT)

The 2013 paper's approach is a refinement of Wang-style differential
collision search:

1. **Signed differential characteristics**: instead of binary 0/1 bit
   conditions on internal state, use signed conditions {+, −, x, ?, …}
   (per de Cannière-Rechberger 2006) that capture WHICH WAY each bit
   changes between the two messages. This expresses propagation through
   modular addition more precisely than XOR-only differentials.

2. **MILP / SAT-based characteristic search**: search for valid signed
   characteristics that propagate through the chosen number of rounds.
   The probability of each step is bounded by Sigma_0/Sigma_1/Maj/Ch
   transition tables.

3. **Message modification**: Wang-style local correction of message bits
   to satisfy the bitconditions implied by the signed characteristic.

4. **Result**: a characteristic + message-modification recipe that
   produces collision pairs in the reduced-round target.

## Why this matters for the project

### Direct prior art for block2_wang bet

The block2_wang bet (priority 1 per the GPT-5.5 strategic read) is built
on Wang-style message modification. Mendel/Nad/Schläffer's signed-DC
methodology is the SHA-256-specific instantiation of this idea. Any
serious block2_wang work needs to cite this paper as foundational
prior art and acknowledge the technique.

### Comparison axis vs this project

- **Their attack model**: full schedule (sr=R), reduced rounds (R<64)
- **This project's attack model**: full rounds (R=64), relaxed schedule
  (sr<R)
- **Both are SFS** (semi-free-start) collisions; they differ in which
  parameter is reduced.

These attack models are NOT directly comparable; they parameterize
different "reduced versions" of SHA-256. The schedule-compliance metric
Viragh introduced bridges them as a unified continuous parameter.

### Gap to full collision

| Attack family | Best public | Gap to full SHA-256 |
|---|---|---|
| Reduced-round full schedule | 39 rounds (Li 2024) | 25+ rounds gap |
| Full rounds reduced schedule | sr=60 (this project) | 4 schedule equations gap |

Both gaps are large. The schedule-compliance axis (this project +
Viragh) is the more recent direction; the round-count axis is the
classical direction (Wang/Mendel/Li lineage).

## Specific techniques worth borrowing

The Mendel/Nad/Schläffer paper introduces "local collisions" — small
collision-producing differential patterns within a few rounds — that
combine to produce the global collision. **This is structurally analogous
to the cascade-1 / cascade-2 mechanism in Viragh's MSB kernel** (a
local-collision-like cancellation pattern using MSB carry-free additions).

Their signed-DC framework gives a vocabulary for describing the cascade-
1 chamber dynamics that this project's F-series characterizes. Specifically:
- The F12 finding "per-chamber de58_size = 1" can be reformulated in
  signed-DC terms as "the slot-58 differential has fixed sign pattern
  per chamber."
- The HW=2 / HW=3 / HW=4 minimum-residual results from F12 / F17 can
  be reframed as the sign-density of the local cascade-1 trail.

A future cross-bet contribution: **translate the F-series structural
findings into signed-DC notation**, allowing direct comparison with
Mendel/Nad/Schläffer's 2013 results.

## Action items for paper integration

1. **Section 5.5 of paper outline** (yale's guarded fiber finding)
   should reference Mendel/Nad/Schläffer 2013 as the prior-art for
   "the manifold of valid differential paths is structurally thin
   away from default messages." Yale's empirical finding extends
   their qualitative observation into a quantitative one.

2. **Section 6 (synthesis)** should note that the project's gap-to-
   full-SHA-256 is 4 rounds (in sr-axis) vs Mendel et al.'s 26 rounds
   (in round-count axis). Both are large but the project's is closer
   in the metric where the attack is defined.

3. **Section 8 (reproduction)** doesn't need to integrate Mendel's
   tooling — different attack model.

## Status

- Read status: STRUCTURAL_SUMMARY (from Viragh's table + general
  cryptanalysis knowledge). Full PDF read PENDING.
- Action items above feed into the paper draft.
- This note unblocks the "Mendel/Nad/Schläffer comparison" item from
  the paper outline's missing-pieces list.

EVIDENCE-level: HYPOTHESIS — based on indirect references. A full PDF
read would harden the specific technical claims about their methodology.
For the paper's prior-art comparison the structural summary is sufficient
at first pass; deeper integration requires direct study.
