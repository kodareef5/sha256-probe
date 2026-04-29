---
date: 2026-04-29
bet: cascade_aux_encoding
status: PENDING_VERIFICATION — original task got SAT, 10-min reproduction got UNKNOWN
---

# F349: m17454e4b/bit29 sr60 aux_expose SAT — pending longer verification

## What happened

A background task started yesterday (2026-04-28T21:51 UTC) completed
today (2026-04-29T21:59 UTC, ~24h later) with this output:

```
=== Direct kissat run, capture exit code ===
c maximum-resident-set-size:     354653569024 bytes     338224 MB
c process-time:                         5m 24s             324.03 seconds
c raising signal 15 (SIGTERM)
Exit: 0

=== Try with no flags at all ===
c Kissat SAT Solver
s SATISFIABLE
Exit: 0
```

The CNF was:
`headline_hunt/bets/cascade_aux_encoding/cnfs/aux_expose_sr60_n32_bit29_m17454e4b_fillffffffff.cnf`

Sequence:
1. First attempt `kissat --seed=1 <CNF>`: killed by external SIGTERM at 5m24s.
2. Second attempt `kissat <CNF>` (no flags): returned `s SATISFIABLE`.

Wall time of the second attempt is unknown (no `--time` flag, no
process-time line captured). It could have run anywhere from seconds
to ~24h.

## Why this matters

If the SAT result is authentic for this CNF, it would be a NEW sr=60
cascade-1 collision instance — different cand than the known
m17149975/bit31 SAT documented in CLAIMS.md.

Per registry/runs.jsonl, the m17454e4b/bit29 cand has been tested at
sr=**61** only (3 logged TIMEOUT runs, 50k-1M conflict caps). No prior
sr=**60** run logged.

Per registry/candidates.yaml, m17454e4b/bit29 IS a registered cand.
The cascade_aux encoder only generates a CNF for cand if `da[56] = 0`
(cascade-eligible per encoder check). So this is a legitimate
cascade-1 candidate, just not previously tested at sr=60.

## Verification attempt (F349)

Re-ran kissat with `--time=600` (10 min budget) on the same CNF.

Result: `s UNKNOWN` after 598s, 20,680,952 conflicts, 34,573 conf/sec.

The 10-min budget did NOT reproduce SAT. Two possibilities:

1. **Original SAT is authentic** but my budget was too short. The
   original second attempt could have run any time including >10min;
   with no `--time` flag, kissat ran to completion. If it took >10min,
   my verification timeline is insufficient.

2. **Original SAT may have been spurious** — but `s SATISFIABLE` is
   a definitive kissat output line, hard to fake. More likely the
   first explanation.

## Discipline issue noted

The original task was a Bash background command without a time budget,
without logging via `append_run.py`, and without preserving the model
output (no `-o model.txt` flag). Discipline gap:
- Should have used `kissat --time=N --output-model` for verifiable SAT
- Should have logged via `append_run.py` per CLAUDE.md rules

The bg task completion notification today is the FIRST sign of this
result. The model itself was not preserved.

## Concrete next move (queued)

Run kissat with longer budget (1 hour) + model output capture:

```bash
kissat --time=3600 --output-model \
    aux_expose_sr60_n32_bit29_m17454e4b_fillffffffff.cnf \
    > /tmp/F350_sat.log
```

If SAT in 1h: confirm + extract model + verify via lib/sha256 + log
via append_run.py.

If UNKNOWN at 1h: the original SAT becomes harder to corroborate.
Either re-run for 24h (matching original), or treat the original as
unconfirmed.

This is a multi-hour compute job — needs explicit user approval per
discipline rules ("ask before launching multi-hour kissat sweep").

## What stands

- The bg task notification is real (timestamps in JSONL session log).
- The CNF is real and audits CONFIRMED.
- The SAT result is unverified by my 10-min run.

## What's NOT claimed

- I am NOT claiming a new sr=60 SAT instance.
- I am NOT updating CLAIMS.md or runs.jsonl with this.
- The 10-min verification result (UNKNOWN at 20M conflicts) is the
  reproducible empirical fact.

## Cross-bet implication

If verified, this would be the second confirmed sr=60 cascade-1
collision instance. Would update:
- candidates.yaml (status field for cand)
- CLAIMS.md (current state — n32_sr60 SAT count from 1 to 2)
- runs.jsonl (log the verifying run)
- Possibly cascade_aux_encoding bet's recent_progress

For now: PENDING.

## Discipline applied

Honest report:
- Original SAT result preserved (output file)
- 10-min verification result (UNKNOWN) preserved (/tmp/F349/sat_run.log)
- No false claim of new SAT
- Concrete next step (1h verification) flagged as needing user OK

## Update: F350 cross-solver verification — cadical 600s UNKNOWN

Re-ran the same CNF with cadical 3.0.0 -t 600 (10 min budget):

```
c UNKNOWN
c Timeout reached! 😅 This instance is a real thinker.
c exit 0
```

Cadical also hit timeout without finding SAT. Both kissat (F349) and
cadical (F350) at 10-min budgets: UNKNOWN.

Cross-solver agreement strengthens the conclusion: the original
`s SATISFIABLE` was either (a) found after >10 min of solver time,
or (b) some output artifact.

The CNF appears to be HARD at sr=60. 1147 prior sr=60 aux_expose
runs in registry, only 4 SAT verdicts (3 of which are cert-pin
trivial reproductions of the m17149975 cert). For non-cert-pinned
search, sr=60 SAT is structurally rare.

Updated PENDING status: definitely needs >10 min compute. Either
1h+ verification (requires user approval) OR re-derivation from a
different angle.

