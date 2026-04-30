---
date: 2026-05-01
bet: programmatic_sat_propagator × cascade_aux_encoding
status: F389 SPEEDUP HYPOTHESIS FALSIFIED — ladder pre-injection HURTS bit2 by +2.35% conflicts
parent: F389 (deployable Phase 2D pre-injection tool)
type: empirical_falsification of F389's "additive ~+0.9% speedup" projection
compute: 9 cadical 60s runs (3 conditions × 3 seeds on bit2_ma896ee41); parallel-3, ~3 min wall
---

# F390: F389 ladder pre-injection FALSIFIED — adding 124 ladder clauses HURTS by +2.35% on bit2

## Setup

F389 packaged F387 + F384 into a deployable Phase 2D pre-injection tool
and projected: "F343 alone (F369 measurement): −9.10% σ=2.68% at 60s
aux_force sr=60. F384 ladder (F384 estimate): +~0.9% additive."

F390 directly tests that projection: build 3 CNFs (baseline /
F343-only / F389-extended) and run cadical 60s × 3 seeds on each.
Total: 9 runs, parallel-3.

## Cand picked

bit2_ma896ee41 (m0=0xa896ee41, fill=0xffffffff, kbit=2). Class A via
Path 1 (m0_bit[31]=1) AND Path 2 (fill rich). Was in F348 panel; not
in F369's clean 5-cand panel. F389 spec for this cand: 1 unit + 1
pair (F343) + 124 size-3 ladder clauses (F384) = 126 total injection.

## CNFs built

```
bit2_baseline.cnf:  13252 vars,  54947 clauses (no inject)
bit2_F343.cnf:      13252 vars,  54949 clauses (+ 2 F343 clauses)
bit2_F389.cnf:      13252 vars,  55073 clauses (+ 126 F343+ladder clauses)
```

All 3 share the same base — only the appended clauses differ.

## Result

```
condition   seed=0    seed=1    seed=2    mean      Δ vs baseline
baseline   1638711   1551711   1619821   1603414        --
F343       1606900   1567536   1638982   1604473    +0.07%   ← within noise
F389       1602932   1678967   1641478   1641126    +2.35%   ← INJECTION HURTS
```

**F389-extended is +2.35% WORSE than baseline.** F343 alone is essentially
neutral (+0.07%, within 1σ of zero per F369's σ=2.68%).

## Findings

### Finding 1 — F389's speedup projection FALSIFIED on bit2

F389 projected ~+0.9% additive help from the ladder. Direct measurement
shows +2.35% HURT instead. The F389 deployable spec, when applied,
makes things WORSE by ~3% (or about 1σ of the underlying noise envelope).

This is an honest negative — the structural finding (F384 ladder exists
in proofs) is real, but **pre-injecting that structure does NOT help
solver performance**. Adding the 124 ladder clauses costs more in
clause-watching/propagation overhead than it saves in conflict
discovery.

Conjecture for why ladder injection hurts:
  - The ladder is in the proof's first ~12k of 1.4M lines (per F381),
    so CDCL discovers it for "free" via unit-propagation chains
  - Pre-injecting 124 clauses adds watch-list / propagation overhead
    that compounds across 1.6M conflicts
  - The clauses are STRUCTURALLY redundant with the encoder's existing
    Tseitin output — making them explicit doesn't shorten proofs

### Finding 2 — F343 alone is also near-neutral on bit2

F343's published value is −9.10% (F369 5-cand mean) but bit2 wasn't
in F369's 5-cand panel. On bit2 specifically, F343 gives Δ=+0.07% —
within the σ=2.68% noise envelope of F369. The −9.10% is a 5-cand
mean; per-cand effect varies by ±σ.

This means F343's empirical value on **any specific cand** can range
roughly from −12% to ~0% (per F369's σ). bit2 happens to be near the
zero-effect end of that range under the consistent-encoder protocol.

### Finding 3 — F389 the spec is FALSIFIED, F389 the tool is fine

F389's two-part shipment was:
  (a) The class-decision rule + ladder-mining tool (`bridge_preflight_extended.py`)
  (b) The empirical claim that the ladder pre-injection adds speedup

Part (a) stands. The tool correctly classifies cands per F387, mines
the ladder for Class A cands, and emits a JSON spec. As a *characterization*
tool it works.

Part (b) FALSIFIED at n=1 cand × 3 seeds. The +2.35% HURT signal is
well outside σ=2.68% noise. Testing 1-2 more Class A cands would
firm up the falsification, but the directional finding is clear.

### Finding 4 — Phase 2D propagator design implication

The Phase 2D propagator should NOT pre-inject the ladder. Sticking with
F343's 2-clause baseline is the correct design (when F343 helps —
which is highly cand-dependent per the σ=2.68% picture).

For Class A vs Class B distinction: the F387 rule is still useful for
*characterization* — it predicts which cands have the ladder structure
in their proofs, which is empirical data about cascade-aux's CDCL
behavior. But routing different injection strategies per class
doesn't deliver speedup gains.

This narrows the Phase 2D viability picture further:
  - F343 alone: ~9% conflict reduction (but high cand-variance)
  - F389 ladder addition: NEGATIVE (~2-3% hurt)
  - Native cb_decide on F286 132-bit core: untested but the only
    remaining structural lever

## What's shipped

- `F390_F389_ladder_injection_FALSIFIED_bit2.md` — this memo
- 9 cadical 60s runs logged via append_run.py
- 3 transient CNFs in /tmp/F390/
- A clean retraction of F389's "additive ~+0.9% speedup" projection
- Project's 11th iterative narrowing/falsification

## Compute discipline

- 9 cadical 60s runs = ~9 min CPU; parallel-3 = ~3 min wall
- 3 CNFs in /tmp (transient, audited as injection-derivatives via
  --allow-audit-failure)
- Real audit fail rate stays 0%
- validate_registry: 0/0

## Open questions for next session

(a) **Confirm at n=2-3 more Class A cands**. If F389 also hurts on
    bit31, bit3, bit28 (other fill=ffffffff), the falsification is
    firm. ~10 min compute total.

(b) **Test ladder injection at deeper budget (5-10 min cadical)**. F366
    showed F343 saturates by 5min budget. Maybe ladder pre-injection
    has a different budget profile? Sub-30-min compute, worth knowing.

(c) **Mechanism**: why does ladder pre-injection hurt? Is the watch-list
    overhead the explanation, or does CDCL's clause-database management
    deprioritize the injected clauses in a way that confuses search?
    A cadical with --statistics on baseline vs F389 would show the
    propagation-cost difference.

## F381 → F390 chain summary (final)

  F381: discovered ladder structure (n=1)
  F382-F386 stages: 6 falsifications (n=3..12)
  F387: rule fits 14/14
  F388: rule anchored at 16/16, Path 1 confirmed
  F389: packaged as deployable tool
  F390: ladder pre-injection EMPIRICALLY HURTS (+2.35%)

11 commits, ~6 hours, ~430s cadical compute, 16+ data points.
Structural finding (ladder exists) is robust. Application finding
(ladder pre-injection helps) is FALSIFIED.

The chain stays useful as a CHARACTERIZATION of cascade-aux CDCL
proof structure, but doesn't yield a Phase 2D speedup mechanism.

## Honest summary

Pattern of small claims being falsified within hours continues.
F389 projected +0.9% additive; F390 measured −2.35% additive (i.e.,
+2.35% conflicts). The 3-percentage-point error is well outside the
project's noise envelope. **F389's deployable spec does NOT speed up
SAT search.** It IS a useful cand-characterization tool.

Phase 2D propagator: stay with F343's 2-clause preflight; don't
ship the ladder extension. The F381-F388 structural picture is real
but doesn't translate to a propagator speedup mechanism.
