# Mouha 2010+ — ARX Differential Trail Frameworks

**Cite as**: Mouha, N. et al. *"Differential and Linear Cryptanalysis Using Mixed-Integer Linear Programming"* (Inscrypt 2011) and related work; *"The Differential Analysis of S-Functions"* (SAC 2010); *"Tools for Cryptanalysis of Hash Functions"* (PhD thesis, KU Leuven 2012).

**Read status**: STRUCTURAL_SUMMARY based on public knowledge of Mouha's
ARX-cryptanalysis line. Foundational for modern automated trail search
on ARX (Add-Rotate-XOR) primitives, including SHA-256.

## Position in the literature

Where Wang/Yin/Yu 2005 hand-constructed SHA-1 characteristics and de
Cannière/Rechberger 2006 first automated DC search, Mouha's line
(2010-2012) introduced **MILP-based** trail search that scales to
larger ARX primitives and produces **provably optimal** trails under
specific objective functions (probability, # active words, etc.).

Specifically Mouha-line contributions:

1. **MILP encoding of XOR-difference propagation through modular addition**
   (Mouha-Preneel 2013, *Towards Finding Optimal Differential Characteristics
   for ARX*). Each ARX component (modular add, rotation, XOR) becomes MILP
   constraints. Total trail probability is the objective.

2. **S-function framework** (Mouha-De Cannière-Preneel 2010, *Differential
   Analysis of S-Functions*). Generalizes "Wang condition checking" from
   per-bit to per-S-function (where an S-function is any computable
   function on bit-vectors with bounded internal state). For SHA-256,
   the modular adder is an S-function with carry as state.

3. **PhD thesis (Mouha 2012)**: comprehensive treatment of MILP-based
   automated cryptanalysis, including SHA-2-family applications. Sets
   the stage for Sun-Hu-Wang-Wang 2014 and follow-up work.

## Why this matters for block2_wang and the F-series

### For block2_wang trail design

The eventual Wang-style block2 trail is exactly an ARX differential
characteristic of SHA-256 starting from a non-zero residual (F32's
deep-min vectors) and ending at zero (collision). Mouha's MILP
formulation IS the engine for finding such trails optimally.

Specifically, given F32's bit2_ma896ee41 deep-min residual:
```
diff63 = (0xa1262506, 0xb0124c02, 0x02000004, 0,
          0x68c1c048, 0x5091d405, 0x02000004, 0)
```
Mouha-style MILP would model:
- **Variables**: each bit position of each (a, b, ..., h) at each round
  64..127 (i.e., second 64-round block from second-block message).
- **Constraints**: ARX propagation (Mouha 2013 formulas for modular
  addition XOR-difference probabilities).
- **Boundary**: input = `diff63`, output = `(0,0,0,0,0,0,0,0)`.
- **Objective**: maximize log-probability of the trail.

Solving this MILP would give the **optimal second-block trail** for
absorbing the bit2 residual.

### For the F-series structural data

F25/F26/F27/F28 found low-HW residuals with specific structural
properties (a_61 = e_61 symmetry, specific bit positions). Translating
to Mouha's framework:

- **Per-bit conditions**: which round-r register-i bits MUST be 0 vs 1
  vs free for the trail to hold with high probability.
- **Per-modular-add conditions**: which carry sequences dominate
  (Mouha S-function language).
- **Per-rotation conditions**: trivially handled by MILP variable
  permutation.

The 11 exact-symmetry cands from F32 form a natural class for **MILP
batch solving** — same propagation framework, different boundary
conditions.

## Methodology summary

### MILP formulation for SHA-256 modular addition

For 32-bit modular addition `Z = X + Y`, Mouha-Preneel 2013 gives a
6-constraint MILP per bit position to encode XOR-difference propagation.
Carry sequences become integer variables; constraint:

```
carry_in_bit_i + diff_x_i + diff_y_i = diff_z_i + 2*carry_in_bit_(i+1)
```

(simplified — actual constraints are more elaborate to handle the
mod-2^32 wraparound). The crucial property: this can be solved exactly
via MILP solvers (CPLEX, Gurobi) for trails up to ~50 rounds in seconds.

For SHA-256's 64-round structure, MILP scales to find optimal
characteristics in minutes-to-hours, depending on objective complexity.

### Application to SHA-256 (Sun et al. 2014, follow-ups)

Sun-Hu-Wang-Wang 2014 (Asiacrypt) used Mouha-style MILP to derive
improved differential characteristics for round-reduced SHA-256.
Mendel-Nad-Schläffer 2013 used SAT-based search (a different
formulation but similar spirit). Modern work (Niu-Sun et al. 2024,
Hou et al. 2025) uses both MILP and SAT in combination.

For block2_wang's eventual implementation, the choice between MILP
and SAT-based DC search is a tooling decision — Mouha's framework
provides the conceptual scaffold for either.

## Specific techniques worth borrowing

### 1. Per-modular-add probability accounting

Mouha's framework gives PER-COMPONENT probability bounds. For
SHA-256's σ functions:
- σ0 (XOR of three rotations of x): probability 1 (XOR-linear)
- σ1: probability 1
- Σ0, Σ1: probability 1
- Modular addition: probability < 1, depends on input differences

Total trail probability = product of per-add probabilities.

For F32's bit2 residual (HW=45) absorbing to 0 over 64 rounds: there
are ~32 modular adds in the trail. If each is "free" (prob = 1 with
the right input), trail is free. If each is "tight" (prob = 2^-1),
trail is 2^-32.

### 2. Active-S-box counting

Mouha's S-function framework reduces "trail probability" to "number
of active S-functions × per-S-function probability." For SHA-256,
the modular adder is the dominant S-function. Counting active adders
along a trail gives an immediate probability lower bound.

For F32's bit2 residual:
- 6 active registers at round 63 (a, b, c, e, f, g)
- 4 zero registers (d, h, plus the always-zero d=h pattern)
- Backward to round 60: cascade-2 zeros e (de60=0), so 5 active regs
- Further backward: cascade-1 zeros (b, c, d) at round 59
- Round 57 has the W-witness as the entry point

Active-adder count along the round-57..63 trail = 4-7 per round (for
T1 and T2 in each round). Total ~ 28-49 active adders. This gives a
trail-probability LOWER bound around 2^-28..2^-49 (each adder ~ 1 bit
of probability cost on average).

For block2 (rounds 64..127), the same accounting applies but
boundary-conditioned. Optimal MILP search would find the trail with
fewest active adders given the (start = bit2 residual, end = 0)
boundary.

### 3. Carry-state DP equivalence

Mouha's S-function = our project's "carry automaton." F-series found
the carry automaton has 42% invariance (kernel-independent
equivalence classes); see project_carry_automaton_verified memory.
Mouha's framework formalizes this: each S-function has an internal
state (here: carry), and the "differential effect" is a Markov chain
on (input_diff × state) → (output_diff × new_state).

For SHA-256's 32-bit modular adder, the state is the 32-bit carry
sequence. The Markov chain is sparse (most differences propagate
deterministically through carries). Project's bit-serial DP work
(see project_carry_dp_negative.md) is exactly the carry-state Markov
chain analysis.

The 42% kernel-independent invariance (project_carry_automaton_verified)
is a Mouha-style "S-function symmetry" — the modular adder's
differential behavior is independent of the kernel choice for these
classes. This is an EXPLOITABLE structure for MILP/SAT search:
build the trail once for the equivalence class, then specialize per
kernel.

## Action items for paper integration

1. **Section 2 (Background)**: cite Mouha-Preneel 2013 alongside Wang
   2005 and dCR 2006 as the third foundational pillar of automated
   ARX cryptanalysis. Note the three lines: hand-craft (Wang),
   guess-propagate (dCR), MILP-optimize (Mouha).

2. **Section 3 (Project's carry-automaton work)**: explicitly map
   our 42% invariance + bit-serial DP findings to Mouha's S-function
   formalism. Position the project's empirical findings as
   instantiations of Mouha's general framework.

3. **Section 5 (block2_wang)**: propose Mouha-style MILP formulation
   as the implementation path for trail search. F32's deep-min
   vectors (especially bit2_ma896ee41 HW=45) are concrete MILP
   inputs.

4. **Section 7 (Discussion)**: note that the project's WORK has been
   in the "S-function structure of SHA-256's adder" subspace of
   Mouha's framework. Future work would integrate F-series findings
   with off-the-shelf MILP solvers.

## Action items for the project (concrete)

1. **For block2_wang**: implement (or adapt) a Mouha-style MILP
   trail-search engine for SHA-256. Inputs: F32 deep-min residuals.
   Outputs: per-trail probability bounds + bitcondition lists.

2. **For carry_automaton work** (if ever resumed): translate the 42%
   invariance result into Mouha's S-function symmetry formalism.
   This positions empirical findings as theoretical contributions.

3. **For programmatic_sat_propagator bet**: Mouha's MILP framework
   is an alternative encoding worth comparing against SAT. A pilot
   would model SHA-256's last 7 rounds as MILP and compare solve
   time to current sr=60/61 kissat experiments.

## Connection to F-series and open questions

- **F25 universal rigidity**: each cand has 1 distinct vector at
  min HW. In Mouha's language: each cand's "minimum-probability
  trail at given S-function activity" is unique. This SHOULD be
  reproducible from MILP optimization.

- **F26/F27/F28 a_61 = e_61 symmetry**: 11/67 cands. In Mouha's
  language: these cands have a SHARED bitcondition between
  round-61's a-update and e-update modular adders. This is a
  STRUCTURAL constraint that should be derivable from MILP-symmetry
  detection.

- **Open question**: does MILP-derived optimal SHA-256 SFS-collision
  trail beat 2^109.7 (Viragh 2026 sr=59 bound) when extended to
  full schedule? If yes, this is publishable on its own.

## Status

- Read status: STRUCTURAL_SUMMARY based on public knowledge of Mouha's
  line. Direct PDF study of "Differential Analysis of S-Functions"
  (SAC 2010) and "Towards Finding Optimal Differential Characteristics
  for ARX" (FSE 2013) PENDING.
- This note unblocks the "Mouha ARX frameworks" item from
  literature.yaml should_read list (4th of 4 — all classical reads
  now structurally summarized).

EVIDENCE-level: HYPOTHESIS — based on indirect references and standard
ARX-cryptanalysis knowledge. Direct PDF study would harden specific
technical claims about MILP encoding details.
