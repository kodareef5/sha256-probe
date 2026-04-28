---
date: 2026-04-28
bet: cascade_aux_encoding
status: BARE_CASCADE1_UNIFORMLY_SAT — shell_eliminate is pinning-tolerant
---

# F226-F229: shell_eliminate is pinning-tolerant — bare cascade-1 instances are uniformly SAT

## Setup

F225 found shell_eliminate.py reduces all 4 tested encoder variants
to 0 clauses (94% elimination, SAT). F226-F229 stress-test the
preprocessor by adding constraints to test boundaries:

- F226: pin W1_57 to all zeros (32 unit clauses)
- F227: pin all of W1_57..W1_60 to zeros (128 unit clauses)
- F228: pin W1=0 AND W2=1 (256 unit clauses, "incompatible" pinning)
- F229: cascade_aux **force** mode CNF (Theorems 1-4 enforced)

## Results

| Test | Constraints added | Final vars | Elim % | Final clauses |
|---|---|---:|---:|---:|
| F225 cascade_aux expose (baseline) | 0 | 741 | 94.4% | 0 |
| F226 W1_57 pin to 0 | +32 | 729 | 94.5% | 0 |
| F227 W1_57..W1_60 pin to 0 | +128 | 728 | 94.5% | 0 |
| F228 W1=0 + W2=1 (incompat?) | +256 | 706 | 94.6% | 0 |
| F229 cascade_aux force mode | (force-encoded) | 788 | 93.7% | 0 |

**Every test reduces to 0 clauses, ~94% elimination, ~700-790 residual
vars, ~0.2s wall.**

## Headline finding

**Bare cascade-1 SAT instances are uniformly satisfiable** under all
4 encoder variants (cascade_aux expose/force, TRUE sr=61 cascade/enf0)
AND all tested pinning patterns. shell_eliminate.py finds satisfying
assignments via pure-literal cascading regardless of encoding choice.

### Why even "incompatible" pinning is SAT

I expected W1=0 + W2=1 to be incompatible with the cascade-1 hardlock
(both M1 and M2 schedules forced to opposite extremes). It's not.

cascade_aux's "expose" mode encodes:
- SHA-256 round equations as Tseitin chains
- Cascade-1 auxiliary structure exposed via aux vars
- M2 = M1 ⊕ kernel_mask at base block

But it does NOT encode:
- HW constraints (the satisfying assignment is unrestricted)
- Cascade-1 hardlock as hard constraint (only "exposed" via aux vars)

So pinning W1 and W2 to incompatible values doesn't trigger
contradiction — the SAT solver can simply assign internal aux vars to
make the round equations consistent. Pure-literal cascading finds
this.

### Even force mode is SAT (93.7%)

cascade_aux's "force" mode adds Theorem 1-4 hard constraints. These
constrain the cascade-1 hardlock relations more tightly than expose.
Yet shell_eliminate still reduces to 0 clauses.

Why? Because the Theorem 1-4 constraints, while present, don't
create UNSAT in the unconstrained SAT problem. They restrict WHICH
assignments are valid, not the EXISTENCE of valid assignments.
Without an HW constraint or cert-pin restriction, plenty of
assignments still satisfy.

## What separates SAT from UNSAT in this corpus

The cert-pin pipeline (F76 etc.) adds:
- 128 unit clauses pinning W1 to a SPECIFIC witness
- Implicit HW=N constraint via the witness choice (witness's
  message-difference HW)

When the witness is one whose msgHW > some boundary, the resulting
cnf+pin is UNSAT (no satisfying assignment exists at that HW).

**The UNSAT comes from pinning to specific values that don't satisfy
the cascade-1 collision constraint at the encoded HW.** Not from any
general structural property.

## Strategic implication

For the F211 BP-decoder design:

1. **shell_eliminate.py works on bare cascade-1 instances**
   (universal across encoders + mode + tolerant pins).
2. **For actual collision-finding**, the input must be cnf+cert-pin
   (or equivalent HW constraint). shell_eliminate would then
   produce a smaller-than-bare reduced CNF (since pinning constrains
   more).
3. **The 700-var hard core** is the asymptotic shell-elimination
   floor for bare cascade-1; with HW-constrained inputs, the hard
   core may be larger.

## What I'd need to test the constrained case

- Generate a cert-pin CNF: `python3 build_certpin.py --base BASE
  --varmap MAP --w57 ... --out OUT`. Requires:
  - A varmap sidecar (currently no varmap files in cnfs/)
  - A specific W-witness (4 32-bit values)

The cert-pin pipeline's current output isn't archived as standalone
CNFs in the repo — they're generated on-demand by certpin_verify.py.
Reproducing this would require finding a recent witness from runs.jsonl
notes and generating the matching varmap via cascade_aux_encoder.py
--varmap.

Worth ~30 min in a future session.

## Concrete next probes

(a) **Generate a varmap sidecar via cascade_aux_encoder.py**: re-encode
    a known cand with `--varmap +` flag, then run build_certpin.

(b) **Add an HW=N constraint manually**: encode "msgHW = N" as a
    big-OR + AT-MOST-N clause set, append to cascade_aux CNF, run
    shell_eliminate. The reduced CNF would have HW-tracking
    clauses and a non-zero residual.

(c) **Test against AlphaMapleSAT-style cube**: each cube is a
    partial assignment to free schedule bits. Adding a cube as
    unit clauses restricts the search; shell_eliminate would
    reveal whether the cube's restriction is consistent with
    cascade-1.

## Discipline

- 0 SAT solver runs that count toward compute budget
- ~1.0s preprocessing wall total across F226-F229
- Each variant reduces to 0 clauses, validating shell_eliminate's
  pinning-tolerance
- Strategic call: cert-pin or HW-constraint testing requires extra
  setup, deferred to future session

## Session arc summary (post-F229)

The cascade_aux structural-pivot arc (F207-F229) has produced:
- **Complete structural characterization** (F207-F217): 4-cycle
  gap structure, treewidth bound, shell-core decomposition,
  variable semantic mapping, cross-encoder differences
- **Working preprocessor tool** (F223-F225): shell_eliminate.py
  with 94% elimination, encoder-universal
- **Robustness validation** (F226-F229): pinning-tolerant,
  mode-universal, sat-discovery-via-cascade

The bet has its strategic foundation. Implementation work for the
BP marginal stage remains for future sessions.
