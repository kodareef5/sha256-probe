# Inspiration v6 Synthesis: The Missing Object

Date: 2026-04-14 21:30 UTC

## What Both Reviewers Said (independently converging)

### Gemini 3.1 Pro: "CONSTRUCT, don't search"
The differential path is FIXED (Single DOF theorem). Stop searching for paths.
Construct message pairs directly using De Cannière-Rechberger bit conditions.
The cascade pre-solves most conditions. Only dT1_61=0 remains.

### GPT-5.4: "COMPILE, don't interpret"  
"You keep trying to prune a concrete search over W1[57..60]. 
That will never give the big win."

The right approach:
1. Search over NONLINEAR CONTROL VARIABLES (adder modes, Ch/Maj selectors)
2. Reconstruct message bits by GF(2) linear algebra
3. Build a COMPILER (chunk transition table), not an interpreter (per-branch RREF)

## The Missing Object: Quotient Transducer State

NOT raw carries. NOT register diffs. NOT de filters.

The constructive automaton state is:
```
StateKey = {boundary carries} + {canonical residual linear context (RREF)}
```

Two partial computations are EQUIVALENT iff they have the same:
- outgoing carries, AND
- same residual frontier linear system

This is the Myhill-Nerode quotient. It's why:
- Register-diff filtering maxes at 3x (wrong observable)
- Backward from de values is vacuous (deterministic under cascade)
- Raw carry automaton can't be constructed (not Markov on carries alone)
- FACE has right theory but wrong implementation (interpreter not compiler)

## Three Fundamental Mistakes We Made

1. **Thinking "filter a search"** — caps at pedestrian speedups
   Fix: construction over mode variables, linear reconstruction of messages

2. **Thinking the automaton is on carries** — it's on carries + linear context
   Fix: hash-consed RREF at chunk boundaries for state deduplication

3. **Over-focusing on e-path** — it's deterministic, not where the action is
   Fix: the hard part is the schedule-coupled T1/a-path residue

## What We're Building Tonight

`chunk_mode_dp.c`: 4-bit chunked mode-branching DP with boundary state
deduplication. Measures the quotient-state count at N=8. If it finds
260 collisions with far fewer states than 2^32, we have the breakthrough.

## Key Pseudocode from GPT-5.4

The algorithm: memoized suffix DP over StateKey = (carries, lin_id).
Within each chunk: bit-by-bit mode branching with incremental GF(2).
At chunk boundary: project, canonicalize, hash-cons, deduplicate.

This is the tool that answers all open questions simultaneously.
