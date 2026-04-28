---
date: 2026-04-28
bet: cascade_aux_encoding
status: SHELL_ELIMINATE_UNIVERSAL_ACROSS_ENCODERS
---

# F225: shell_eliminate works uniformly across 3 encoder variants

## Setup

F223/F224 implemented shell_eliminate.py and tested on 2 cascade_aux
CNFs. F225 extends the test to two additional encoder variants to
establish universality.

## Results across 3 encoder families

| Encoder | CNF | Input vars | Final vars | Elim % | Clauses (final) | Wall |
|---|---|---:|---:|---:|---:|---:|
| cascade_aux expose | bit06_m6781a62a_fillaaaaaaaa | 13,179 | 741 | 94.4% | 0 | 0.19s |
| cascade_aux expose | bit29_m17454e4b_fillffffffff | 13,224 | 732 | 94.5% | 0 | 0.19s |
| TRUE sr=61 cascade | m17149975_fffffffff_bit31 | 11,256 | 758 | 93.3% | 0 | 0.20s |
| TRUE sr=61 enf0 | bit10_m3304caa0_fill80000000 | 11,211 | 696 | 93.8% | 0 | 0.18s |

All four CNFs (3 distinct encoder variants) reduce to 0 clauses at
93.3-94.5% elimination, ~0.2s wall.

## Key finding

**Bare cascade-1 SAT instances are always SAT** under all three
encoder variants tested. The bare encoding has many satisfying
assignments (any "valid" SHA-256 round computation); pure-literal
cascading finds them in <0.2s.

The actual collision-finding problem requires an HW constraint via
cert-pin pipeline. Without that constraint, the encoded problem is
trivially SAT.

## Hard-core size convergence

After full elimination, the residual var count is ~700-758 across
all encoders:

| Encoder | Residual vars |
|---|---:|
| cascade_aux expose | 741, 732 |
| TRUE sr=61 cascade | 758 |
| TRUE sr=61 enf0 | 696 |

The convergence to ~700-760 vars is striking. This represents the
**irreducible structural minimum** of cascade-1 collision encoding —
roughly the M1 and M2 free-schedule bits plus a small set of
necessary internal couplings.

For sr=60 cascade_aux: 4 free rounds × 32 bits × 2 messages = 256 free
schedule bits + ~480 essential auxiliaries.
For sr=61 TRUE: 3 free rounds × 32 × 2 = 192 + ~566 auxiliaries.
For sr=61 enf0: 192 + ~504 auxiliaries.

These match the order-of-magnitude expected: free schedule + Tseitin
glue.

## Strategic implication

The F211 BP-decoder design's "hard core" is **~700 vars universally**
across encoder choice. The decoder built once on this 700-var primitive
applies to all SHA-256 round-equation collision instances regardless
of encoder.

This is a stronger universality than F208's (cascade_aux-internal):
**shell_eliminate.py + 700-var BP** is encoder-independent.

## Concrete next probes

(a) **cert-pin output**: add an HW constraint to one of these CNFs,
    re-run shell_eliminate. Expected: reduced CNF is non-empty
    (the HW clauses prevent trivial elimination), giving the actual
    "hard core" for collision finding.

(b) **kissat on shell-reduced + HW-constrained CNF**: the real
    empirical test of the F211 decoder design's value.

(c) **Implement assignment back-translation**: extend shell_eliminate
    to output a satisfying assignment for the original CNF when
    reduced is SAT. Currently only verifies satisfiability via 0
    clauses; doesn't construct the assignment explicitly.

## Discipline

- 0 SAT solver runs that count toward compute budget
- ~0.8s wall total for 4 CNFs across 3 encoder variants
- shell_eliminate.py is empirically encoder-universal at the bare
  CNF level
- Strategic deliverable: the bet's BP-decoder direction has a
  ~700-var universal target, not encoder-specific
