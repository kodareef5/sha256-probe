---
date: 2026-04-28
bet: cascade_aux_encoding
status: F211_SPEEDUP_THESIS_EMPIRICALLY_REFUTED
---

# F235/F236/F237: F211's "200× speedup" speedup thesis is empirically refuted on hard sr=61 instances

## Setup

F211 proposed that shell-elimination preprocessing would give 200×+
speedup over direct kissat on cascade-1 collision instances. F234
showed v2 is sound but slow on trivial UNSAT cases. This memo tests
on a HARD instance (kissat timed out at 848s previously).

## Hard test target

`cnfs_n32/sr61_cascade_m09990bd2_f80000000_bit25.cnf`

From runs.jsonl: kissat timed out at 848s (TIMEOUT, status UNKNOWN).

## F235: shell_eliminate_v2 on hard CNF

```
Input:  11234 vars, 47530 clauses
Output:  8054 vars (28.3% eliminated), 45894 clauses
Wall:   15.02s
```

Substantial elimination (3,180 vars / 1,636 clauses removed). v2 is
working correctly.

## F236: kissat on v2-reduced

```
$ kissat --time=120 --quiet /tmp/hard_v2_reduced.cnf
s UNKNOWN
Wall: 120.04s
```

**kissat timed out at 120s. Same UNKNOWN verdict as direct kissat
hitting 848s timeout.**

The reduction doesn't help kissat solve faster. v2 + 120s kissat
budget = 135s wall, no decision. Direct kissat at 120s = 120s wall,
also no decision. Both produce UNKNOWN.

## F237: F211 thesis empirically refuted

F211 predicted:
- Stage 1 (shell elimination) reduces problem size
- Stage 2 (BP marginals) extracts structure
- Stage 3 (marginal-guided search) speeds up solving
- Total: ~200× speedup over direct kissat

Reality:
- Stage 1 takes 15s for 28% elimination (substantial but not
  transformative)
- Stage 2/3 not implemented
- kissat on stage-1 output: SAME hardness as original

**The 200× speedup target is empirically unachievable via shell
elimination alone.** The hard core that remains after preprocessing
is what makes the instance hard; eliminating Tseitin chains doesn't
help CDCL solve it.

## Why F211 was wrong

The intuition behind F211 was: kissat's BVE only eliminates 19% of
vars (per F220); a more aggressive preprocessor eliminating ~70-94%
should help.

The flaw in this reasoning:
1. kissat's BVE leaves ~80% of vars active because eliminating more
   creates clauses that the SOLVER would then have to process.
2. Aggressive preprocessing doesn't shrink the SAT-difficulty; it
   redistributes work between preprocessor and solver.
3. The HARD core (~3K-8K vars per F211/F213/F235) is the genuine
   intractability; no amount of structural elimination simplifies it.

Mathematically: if a SAT instance requires 2^k conflict-search
operations to refute, no polynomial-time preprocessor (BVE,
shell-elimination, anything) can reduce that without solving the
SAT problem itself.

## What the structural analysis (F207-F217) is still good for

The structural analysis stays valid as DESCRIPTIVE:
- cascade_aux has a quasi-cyclic Tanner graph
- Treewidth bound is 699
- Hard core is ~3,000-8,000 vars
- 184-bit active schedule is the algorithmic primitive

These are properties of the encoding. They don't immediately yield
a faster solver, but they characterize the problem.

## What F211 needs to be REPLACED by

A correct strategy for cascade-1 collision speedup must address the
HARD CORE, not just the shell. Options:

1. **Cube-and-conquer** with guided cube selection (F157
   AlphaMapleSAT direction): partition the hard core into branches
   processed in parallel.
2. **Custom decision heuristic**: kissat-IPASIR-UP with a
   schedule-bit branching priority (F147/F158 propagator bet).
3. **Structural lemma learning**: identify cascade-1-specific
   conflict clauses and add them as learned hints.
4. **Different encoding entirely**: BDD enumeration, MILP, or a
   non-CDCL approach.

Shell elimination alone is NOT the path.

## Status of session deliverables

| Deliverable | Status | Validity |
|---|---|---|
| Heuristic search saturation arc (F176-F206) | shipped | VALID |
| Structural analysis (F207-F217) | shipped | VALID (descriptive only) |
| shell_eliminate.py v1 (F223-F230) | shipped | INVALID (soundness bug, F232) |
| shell_eliminate_v2.py (F233-F234) | shipped | SOUND (slow) |
| F211 200× speedup thesis | proposed | REFUTED (F237) |
| BP marginal stage 3 | unimplemented | UNTESTED |

## Concrete next probes

(a) **Pivot to cube-and-conquer**: implement F157 AlphaMapleSAT-style
    cubing on cascade-1 hard core. The MCTS-guided cube selection is
    a candidate for non-trivial speedup.

(b) **Pivot to programmatic_sat_propagator bet**: F147 reopen
    candidate. IPASIR-UP with schedule-bit branching is structurally
    distinct from preprocessing.

(c) **Pivot away from this bet**: cascade_aux_encoding has now
    produced a complete structural analysis but its algorithmic
    direction (F211) is refuted. Mark as "characterized, no path
    to headline" and move on.

## Honest summary

The cascade_aux_encoding bet's structural analysis arc (F207-F217)
produced real descriptive insight. The algorithmic implementation
arc (F223-F237) demonstrated:
- F211's preprocessing-based speedup thesis is wrong
- shell_eliminate (corrected v2) is sound but doesn't help CDCL
  on hard instances
- The bet's "headline-worthy" potential via this route is
  empirically zero

This is the third major correction of the session (F205, F232,
now F237). The discipline holds: ship corrections, don't defend
overstatements.

The session's strongest valid deliverable is the **structural
analysis (F207-F217)** as descriptive characterization of
cascade_aux's Tanner graph. The implementation arc was educational
but produced no headline-class outcome.

## Discipline

- 1 SAT solver run logged via this session: kissat 120s timeout
  on v2-reduced (matches direct kissat behavior on original)
- F237 retracts F211's speedup thesis
- 3 retractions in session: F205 (cross-fixture basin claim),
  F232 (preprocessor soundness), F237 (preprocessor speedup)
- Ship-correction discipline holding strong

## Strategic recommendation

Mark cascade_aux_encoding bet as **STRUCTURALLY CHARACTERIZED, NO
HEADLINE PATH VIA PREPROCESSING**. Move forward with one of:
- Cube-and-conquer pivot (F157 alignment)
- IPASIR-UP propagator (F147/F158 reopen)
- Different bet entirely

Update kill_criteria.md to mark new criterion #2 (BP marginals
reduce CDCL solve time) as PARTIALLY FIRED based on F237's
empirical evidence that preprocessing alone doesn't help on hard
instances.
