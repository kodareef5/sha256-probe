---
date: 2026-04-30
machine: macbook
status: hourly log (append-only)
---

# 2026-04-30 macbook hourly log

## ~03:30 EDT — close yale F378-F384 acknowledgement loop

Triaged the unanswered yale message
`comms/inbox/20260429_yale_to_macbook_F378_F384_bridge_clause_target.md`
(yale's W57[22:23] bridge-clause target, the seed of macbook's F339-F367
propagator chain). My F343 preflight tool, F347/F348 speedup measurements,
and F366 budget-dependence findings all trace back to that yale discovery
and had not been formally acknowledged. Wrote
`comms/inbox/20260430_macbook_to_yale_F367_chain_thanks_F378_enabled.md`
with: explicit thanks, the F347 → F366 budget-dependence correction
(13.7% single-seed → -8.4% multi-seed at 60s budget), F353 verification
caveat (F349 SAT not reproducible at 4h), F358 polarity-bug retraction
note, and the standing -0.79% number on the F235 basic-cascade CNF.

Concurrent corpus audit: re-ran `audit_cnf.py --json` across all 78 CNFs
in `cnfs_n32/`. All CONFIRMED, observed bounds match the 2026-04-28
fingerprint envelope exactly (no drift). cascade_aux/cnfs/ counts also
unchanged (60/28/32/32 expose-sr60/force-sr60/expose-sr61/force-sr61).
`validate_registry.py`: 0 errors, 0 warnings.
