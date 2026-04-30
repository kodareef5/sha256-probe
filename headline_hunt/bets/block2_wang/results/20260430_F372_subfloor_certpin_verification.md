---
date: 2026-04-30
bet: block2_wang
status: F371 BLIND_SPOT EMPIRICALLY CLOSED — 4 sub-floor W-witnesses all UNSAT (near-residuals)
parent: F371 F100 blind-spot discovery
follow_up_to_f100: yes — extends the 54-cand cert-pin coverage by 4 cands at sub-floor HW
---

# F372: cert-pin verification of F371's 4 sub-floor W-witnesses → all UNSAT

## Setup

F371 (this same date, ~07:50 EDT) discovered F100's cert-pin sweep
covered 54 cands rather than the documented 67, and that 4 cands had
W-witnesses BELOW F100's covered min_hw=61 floor:

  bit3_m33ec77ca_fillffffffff:  HW=55  ← lowest in entire dataset
  bit2_ma896ee41_fillffffffff:  HW=57
  bit28_md1acca79_fillffffffff: HW=59
  bit13_m4e560940_fillaaaaaaaa: HW=61

F372 closes F371 empirically: cert-pin verify each, with full discipline
(persisted CNFs, per-run `append_run.py` logging).

## Method

Per-cand pipeline:
1. Build base cascade-aux CNF (sr=60, mode=expose) via `cascade_aux_encoder.py`,
   emit varmap sidecar.
2. Pin W57..W60 via `build_certpin.py` (128 unit pins per CNF).
3. Run kissat 4.0.4 + cadical 3.0.0 at 5s budget (each instance is
   either UP-derivable UNSAT in <1s or fast SAT — 5s is over-allocated).
4. Log every run via `append_run.py` (8 entries: 4 cands × 2 solvers).

Persisted CNFs: `/tmp/F372_<short>_certpin.cnf` (sizes 54865-55075 clauses,
~13200 vars per cand).

## Result

```
cand                          kissat        cadical       verdict
bit3_m33ec77ca (HW=55)        UNSAT 0.01s   UNSAT 0.01s   near-residual
bit2_ma896ee41 (HW=57)        UNSAT 0.01s   UNSAT 0.01s   near-residual
bit28_md1acca79 (HW=59)       UNSAT 0.01s   UNSAT 0.01s   near-residual
bit13_m4e560940 (HW=61)       UNSAT 0.01s   UNSAT 0.01s   near-residual
```

**Total: 8/8 UNSAT, 2-solver agreement on all 4 cands. 0 SAT. Total
wall: ~0.1s + ~30s for CNF building.**

## Findings

### Finding 1 — F371's blind-spot lead does NOT contain a single-block sr=60 collision

The bit3_m33ec77ca HW=55 W-witness — the strongest single lead in the
project's residual corpus, lower than F100's covered min_hw=61 floor —
is **a near-residual, not a collision**. Same outcome for the other 3
sub-floor witnesses. F100's conclusion stands.

### Finding 2 — Cert-pin instances are UP-derivable UNSAT in <0.01s

Both kissat and cadical resolve each cert-pin instance in under 10ms.
That's consistent with F100's pattern: cert-pin pins W57..W60 to
specific values, which propagates down through the round-57..63
constraints quickly. There's no deep search needed — the constraint
network either trivially admits a model (SAT, collision) or unit
propagation derives a contradiction (UNSAT, near-residual).

### Finding 3 — F100's "67-cand" scope statement now corrected via 54 + 4 = 58 directly cert-pin verified cands

After F372, the cert-pin coverage state is:

  - 54 cands directly cert-pin verified per F100 (per-cand corpora)
  - 4 cands directly cert-pin verified per F372 (sub-floor witnesses
    from the F371 blind spot)
  - 9 cands from F371's blind spot remain untested (HW≥62, within
    F100's covered HW range; lower priority than the 4 sub-floor)
  - 20 cands "covered" via the older shared `F32_deep_corpus_enriched.jsonl`
    (per F100's notes; not per-cand cert-pin runs)

Direct cert-pin coverage: **58 of 67 registered cands** = 86.6%. The
remaining 9 untested-but-in-blind-spot cands are queued for the next
cert-pin sweep iteration if/when block2_wang activity restarts.

### Finding 4 — bit3_m33ec77ca's HW=55 W-witness is structurally interesting but solver-trivial

The W-witness:
  w1_57=0x3d7df981  w1_58=0xae13c3a4  w1_59=0x49c834bd  w1_60=0x7619ac16
  w2_57=0x36ed80fa  w2_58=0x8a9db1fa  w2_59=0x5c63c09d  w2_60=0x0a66d006

per-register hw63: a=11, b=7, c=8, e=12, f=8, g=9 (d=h=0)
da_eq_de: false  (does NOT satisfy F26/F27 a_61 == e_61 symmetry)

The active-register HW distribution is unusually flat (no register
dominates), and the pair fails the a_61=e_61 symmetry. UNSAT verdict
suggests the cert-pin's local constraint geometry is incompatible
with the cascade-1 hardlock (W*_57..60 must be a cascade-DP solution
AND satisfy round-60..63 closure simultaneously; a near-residual at
HW=55 means the W-witness solves enough of the closure to come
within HW=55 of zero diff at round 63 but not all of it).

## Negatives.yaml update

Already updated in F371 commit (7ae2fad): the
`single_block_cascade1_sat_at_compute_scale` entry now includes the
F371 caveat in `why_closed` and a new `would_change_my_mind` trigger
naming the 4 sub-floor cands. F372's empirical result fires NO
would_change_my_mind triggers (all 4 UNSAT, conclusion stands).

The F371 trigger ("An existing-registry cand whose corpus contains a
W-witness below F100's covered min_hw floor (61) admits single-block
SAT under cert-pin") could be marked NOT_FIRED at the lowest 4 sub-floor
witnesses. The trigger remains ACTIVE for the 9 still-untested
blind-spot cands at HW≥62.

## Compute discipline

- Total wall: ~30s for CNF generation + ~0.1s for solver runs
- Total CPU: ~30s
- 8 runs.jsonl entries logged via `append_run.py` (with
  --allow-audit-failure since /tmp/F372_*_certpin.cnf paths don't
  match a fingerprint bucket)
- All 8 runs are direct cert-pin verifications, status UNSAT, kissat
  + cadical agreement
- Audit-failure rate of these 8 entries: 100% (intentional, --allow-audit-failure)
- sr61_n32 bet's 0/83 audit failures unaffected; kill criterion not
  tripped

## What's shipped

- `20260430_F372_subfloor_certpin_verification.json` (raw stats)
- This memo
- 8 entries in `headline_hunt/registry/runs.jsonl`
- 4 cert-pin CNFs in `/tmp/F372_*_certpin.cnf` (transient; not committed)

## Cumulative F371 + F372 outcome

F371 surfaced the strongest single lead the project's residual corpus
had hiding (bit3 HW=55, below F100's covered floor). F372 verified it
within minutes: **near-residual, not a collision**. F100's "single-block
sr=60 cascade-1 collisions are unreachable at our compute scale"
conclusion now extends to 58/67 cands (was 54/67 effective per F100).

The remaining 9 blind-spot cands have HW≥62 within F100's covered range.
Lower priority than the 4 sub-floor witnesses, but worth verifying in
a future block2_wang iteration to bring direct cert-pin coverage to
67/67 = 100%.

## Next moves

(a) **Already shipped this session**: F371 + F372 close the F100
    blind spot for the most important 4 cands. Direct cert-pin
    coverage now 58/67 (86.6%).

(b) **Optional**: extend F372 to cover the 9 remaining blind-spot
    cands. Compute: same pipeline × 9 = ~3 min wall, 18 runs.jsonl
    entries. Brings direct cert-pin coverage to 67/67 = 100%. Defer
    to next pulse for go-ahead since this exits "follow F371's lead"
    territory and enters "exhaustive sweep" territory (still small
    compute but worth flagging).

(c) **Real next-headline move**: continue investigating the
    cluster-analysis follow-up named in `extract_top_residuals.py`:
    `--hw-max 60 --top-k 1000` → ~thousand sub-60 records → cluster
    by structural features (per-register HW, da_eq_de, active set) to
    look for non-uniform patterns that random sampling missed. This
    is an analysis move with no compute cost — pure data exploration
    on the existing 47 corpora.
