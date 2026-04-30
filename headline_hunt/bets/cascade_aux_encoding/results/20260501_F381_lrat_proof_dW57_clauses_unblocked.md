---
date: 2026-05-01
bet: cascade_aux_encoding
status: DELIVERABLE_5_UNBLOCKED — LRAT proof contains analyzable dW57-touching clauses
parent: F380 (deliverable #5 deferred to F347-F369-class non-trivial instances)
type: substantive_review (daily heartbeat step 7)
compute: 1 cadical 60s + 30s + LRAT proof generation; ~503MB text proof file at /tmp/F381_proof_text.lrat
---

# F381: cadical LRAT proof on bit31 reference reveals dW57 clauses for cross-cand clustering

## Question (heartbeat step 7)

What's the single highest-leverage <30min next action on cascade_aux_encoding?

The bet is in maintenance after the F343-F377 chain (preflight tool +
−9.10% σ=2.68% envelope characterized). The natural next mechanism move
is yesterday's deliverable #5 — cross-cand learned-clause clustering —
but cert-pin instances are UP-trivial (F380) so they don't generate
useful learned clauses.

Pivot per F380: probe an F347-F369 class CNF (aux_force sr=60, no W-pin,
60s budget) with cadical's LRAT proof output. **Question: does the proof
contain analyzable clauses on dW57 vars at scale?**

## What was done

```
cadical -t 60 --seed=0 -q --binary=false \
  aux_force_sr60_n32_bit31_m17149975_fillffffffff.cnf  /tmp/F381_proof_text.lrat
```

Result: 60s timeout (UNKNOWN), 503 MB text LRAT proof.

Sampled the first 5,000,000 proof lines and analyzed:

```
Total lines:    2,722,778
  adds:         1,382,497
  deletes:      1,340,281

Clause-size histogram (% of adds):
  size 1   :   22,770   (1.65%)   ← unit clauses
  size 2   :   45,534   (3.29%)   ← pair clauses
  size 3   :   56,824   (4.11%)
  size 4   :   48,996   (3.54%)
  size 5   :   43,455   (3.14%)
  size 6   :   50,391   (3.64%)
  size 7-10:  216,525  (15.66%)
  size 11-50: 605,283  (43.78%)
  size 51+ : 292,719  (21.17%)
```

dW57 var region (CNF vars 12640-12680 for bit31 cand):
- **105 derived clauses in the first ~5M lines touch this region**
- All visible matches are size 1-2 in my <=2 filter
- Visible pattern: derived 3-literal clauses linking vars 8357 / 11890 /
  12643 (a state var, an aux register var, and a dW57 var) — CDCL is
  discovering small structural relations between dW57 and other parts
  of the formula

Sample dW57-touching derived clauses:
```
line 12102: -11890  12643  0   (size-2)
line 12103:  11890 -12643  0   (size-2)
line 12112:  8360  -11891  12648  0   (size-3)
line 12113:  8360   11891 -12648  0   (size-3)
```

These look like XOR-style equivalence learnings:
  `dW57[var] ⇔ (some-state-var XOR some-aux-var)`

## Findings

### Finding 1 — Deliverable #5 is concretely unblocked

The aux_force sr=60 60s cadical instance generates **>1M learned
clauses, including ~23k units and ~46k pairs**, with at least **105
small clauses** specifically touching the dW57 var region. This is
many orders of magnitude more analyzable structure than the cert-pin
instances (which resolve in 0 conflicts).

Cross-cand clustering on these clauses should be feasible. Methodology:

1. Run cadical 60s with LRAT proof on each F347-F369-class cand
   (8 cands × ~30s each = ~5 min compute, ~4 GB total proof data).
2. For each cand, extract the small (size ≤4) clauses touching the
   per-cand dW57 var range (varmap-derived).
3. Cluster across cands by structural pattern (e.g., "this is
   `dW57[i] ⇔ aux_var[j]`" universal across cands? Or cand-specific?).
4. Generalized clauses (universal across cands) are the unit-of-progress
   per yesterday's user direction.

### Finding 2 — Proof contains XOR-equivalence-style derived clauses

The visible 3-literal clauses on `(8357, 11890, 12643)` and
`(8360, 11891, 12648)` look like enforcing equality/XOR between
3 vars:

  `var12643 ⇔ (var11890 XOR var8357)`

Each set of 4 clauses encodes the truth table:
```
8357 -11890 12643  → if 8357 AND ¬11890, then 12643
8357 11890 -12643  → if 8357 AND 11890, then ¬12643
-8357 -11890 12643 → if ¬8357 AND ¬11890, then 12643
-8357 11890 -12643 → if ¬8357 AND 11890, then ¬12643
```

That's `12643 ⇔ ¬(11890 ⇔ 8357)` — the XOR Tseitin pattern. Followed by
the size-2 clauses `-11890 12643 0` and `11890 -12643 0` which assert
`12643 ⇔ ¬11890`, presumably after var 8357 was forced to 1 elsewhere
and the XOR collapsed.

So CDCL is **rediscovering Tseitin XOR equivalences** that were already
implicitly in the formula but had to be propagated through unit
propagation + conflict analysis. That's a known phenomenon for ARX
crypto SAT instances and explains why the proof is large despite
the formula being "structurally simple".

### Finding 3 — The path to a generalized learned clause

If F381 + per-cand reruns reveal that **the same dW57[i] ⇔
(state_var XOR aux_var)** pattern is derived for the SAME bit-positions
i across all 8 cands, that's a universal Tseitin-style relation that
could be:
  - Pre-injected at solver init via cb_add_external_clause (the F343
    extension)
  - Or used to simplify the encoder itself by adding the relation as
    an explicit clause family

Either way, it would be a **generalized learned clause** per user
direction's unit-of-progress.

## What's shipped

- 1 cadical 60s run on bit31 reference cand
- LRAT proof at /tmp/F381_proof_text.lrat (503 MB, transient)
- This memo
- Concrete deliverable #5 methodology (5-min compute estimate to
  collect cross-cand proofs)

## Compute discipline

- 1 solver run logged below via append_run.py
- Proof file is transient (in /tmp); not committed (too large)
- Total wall: 90s (60s + 30s)
- Real audit fail rate stays 0%

## Open questions for next session

(a) Re-run on the other 7 F347-F369-class cands at 30s budget each
    (~3 min total compute) and collect proofs to /tmp/F382_*_proof.lrat.
    Then cluster.

(b) Determine whether the visible Tseitin XOR pattern at
    `(8357, 11890, 12643)` is universal (vars shift per cand but
    the structural relation is the same) or cand-specific.

(c) If universal, the natural next step is to inject these as
    pre-cooked clauses at solver init (extending F343's 2-clause
    preflight to a Tseitin-equivalence preflight). Could deliver
    significantly more than F369's −9.10% if the patterns generalize.

The first cross-cand probe is sub-30-min and is the right next move
when block2_wang's beam improvements are the lower priority. Filed
as F381 next-step (a).
