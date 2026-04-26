# cnfs_n32/ — Full N=32 SHA-256 cascade-DP CNFs

**62 CNFs as of 2026-04-26** covering 51 cascade-eligible candidates.

## Naming convention

```
sr<level>_cascade_m<M0_HEX>_f<FILL_HEX>_bit<BIT>.cnf
```

Examples:
- `sr61_cascade_m17149975_fffffffff_bit31.cnf` — sr=61, m0=0x17149975, fill=0xffffffff, kernel-bit=31
- `sr61_cascade_m99bf552b_fffffffff_bit18.cnf` — bit=18 NEW candidate from 2026-04-26 sweep
- `sr61_cascade_ma2f498b1_fffffffff_bit25.cnf` — bit=25 NEW (2nd-most-compressed)

Older names use slightly different patterns (e.g., `sr61_n32_bit10_*_enf0.cnf`,
`TRUE_sr61_bit19_51ca.cnf`) — these are pre-pause artifacts. All audit CONFIRMED.

## Encoders

All CNFs in this directory use the **cascade_explicit** encoder (3 free schedule
words W[57..59], schedule-derived W[60..63], full 8-register collision at slot 64).

Generator: `encode_sr61_cascade.py` (and analogous `encode_sr60_cascade` etc.)

## Discipline rules

- **Every CNF must pass `headline_hunt/infra/audit_cnf.py` before any solver run.**
- **Every solver run must be logged via `headline_hunt/infra/append_run.py`.**
- See `headline_hunt/infra/cnf_fingerprints.yaml` for var/clause ranges per
  (sr-level, encoder).

If a CNF audits as CRITICAL_MISMATCH, it's a sr-level mislabel. **DO NOT USE.**
Investigate via the `bets/cascade_aux_encoding/results/20260426_audit_rot_fix.md`
pattern: encoder updates can shift fingerprint ranges; old CNFs may need
regeneration.

## Coverage breakdown

By kernel bit (post 2026-04-26 expansion sweep):
- bit-0:  4 cands across 3 fills
- bit-2:  3 cands at fill=0xff (NEW Σ0-aligned)
- bit-3:  2 cands at fill=0xff (NEW σ0-aligned)
- bit-4:  2 cands at fill=0xff (NEW non-aligned, m=0x39a03c2d 3rd-most-compressed)
- bit-6:  6 cands across 5 fills
- bit-10: 7 cands across 3 fills
- bit-11: 2 cands across 2 fills
- bit-13: 7 cands across 5 fills (1 NEW at fill=0x80)
- bit-17: 3 cands across 2 fills
- bit-18: 5 cands across 2 fills (NEW σ0-aligned)
- bit-19: 1 cand at fill=0x55 (most-compressed candidate, image=2^8)
- bit-25: 3 cands across 2 fills (1 registered + 2 NEW; NEW m=0xa2f498b1 2nd-most-compressed image=2^10)
- bit-31: 6 cands across 4 fills

**Total: 51 candidates covering 12 distinct kernel bit positions.**

## Sweep coverage status

See `headline_hunt/registry/notes/sweep_coverage.md` for per-(bit, fill)
exhaustive 2^32 m0 sweep results. As of 2026-04-26:
- 18+ cells exhaustively swept this session
- ~16 candidates in current registry came from those sweeps
- Σ1/σ1 alignment hypothesis FALSIFIED — eligibility is universally rate ~2^-31

## Generating new CNFs (from sweep)

```bash
# Run a sweep at uncovered (bit, fill):
./headline_hunt/registry/notes/cascade_eligibility_sweep <bit> <fill_hex>

# For each ELIGIBLE m0 found, generate the CNF:
python3 encode_sr61_cascade.py <m0_hex> <fill_hex> <bit>
mv /tmp/sr61_cascade_m<m0>_f<fill>_bit<bit>.cnf cnfs_n32/

# Audit:
python3 headline_hunt/infra/audit_cnf.py cnfs_n32/sr61_cascade_*.cnf

# Register in candidates.yaml + kernels.yaml + commit
```

## What this directory is NOT

- Not a workspace for solver outputs (those go in
  `headline_hunt/bets/<bet>/runs/` per bet).
- Not for derivative CNFs (cascade_aux variants live in
  `headline_hunt/bets/cascade_aux_encoding/cnfs/`).
- Not a graveyard — old/stale CNFs should be regenerated to current
  encoder, not kept as-is. See audit-rot fix memo.
