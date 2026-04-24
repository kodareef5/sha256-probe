# cascade_aux_encoding — design + initial encoder shipped

**Date**: 2026-04-24
**Machine**: macbook
**Session outcome**: design phase complete, encoder implemented, smoke-tested on 4 representative configurations. Ready for compute-side validation by the next worker.

## What's built

### `encoders/SPEC.md`
Design document grounded in Theorems 1-4 and 6 of `writeups/sr60_sr61_boundary_proof.md`.
Two modes:
- **Mode A (`--expose-cascade`)**: adds auxiliary variables `dX[r]` (per register per round) and `dW[r]` (per schedule word per round), plus XOR tying clauses. Solution set unchanged.
- **Mode B (`--force-cascade`)**: adds Mode A plus hard constraints encoding the cascade diagonal (Theorem 1), de60=0 (Theorem 2), da=de at r=61 (Theorem 4), and the three-filter dE[61..63]=0 (Theorem 3). Restricts to cascade-DP solutions. Omits the redundant 8-register collision constraint in this mode.

### `encoders/cascade_aux_encoder.py`
Additive wrapper over `lib.cnf_encoder.CNFBuilder`. Does NOT modify upstream code.

Usage:
```
python3 cascade_aux_encoder.py --sr 60 --m0 0x17149975 --fill 0xffffffff \
  --kernel-bit 31 --mode expose --out aux_expose_sr60.cnf
```

### `encoders/test_encoder.py`
Fast smoke test (~1s). Runs 4 encoder invocations, validates DIMACS syntax, confirms audit verdict CONFIRMED on each.

### CNF size measurements (N=32, this encoder)

| Configuration | Vars | Clauses | Notes |
|---|---:|---:|---|
| Baseline standard (from existing `cnfs_n32/sr61_n32_bit10_*_enf0.cnf`) | 11211 | 46873 | pre-aux |
| aux expose sr=60 (M[0]=0x17149975, MSB) | 12620 | 52783 | +12.6% vars, +12.6% clauses |
| aux force sr=60 | 12620 | 52783 | same total (force clauses replace collision constraint) |
| aux expose sr=61 (M[0]=0x3304caa0, bit-10) | 12816 | 53698 | +14.3% vars, +14.6% clauses |
| aux force sr=61 | 12816 | 53698 | same total |

Substantially less overhead than the derived encoding (which worsened treewidth).

### Fingerprint registry entries
Added 4 entries to `headline_hunt/infra/cnf_fingerprints.yaml` covering sr=60 aux expose, sr=60 aux force, sr=61 aux expose, sr=61 aux force. Tight ranges so sr=60 and sr=61 don't cross-match (caught an initial overlap bug during verification — the audit flagged it, ranges were tightened).

`headline_hunt/infra/audit_cnf.py` filename patterns also extended: files named `aux_expose_sr60*`, `aux_force_sr60*`, `aux_expose_sr61*`, `aux_force_sr61*` now parse correctly and audit as CONFIRMED.

## What's open (next worker picks up)

See `encoders/SPEC.md` § "Test plan" for the full sequence. Bullet summary:

1. **Generate matched-pair CNFs** at N ∈ {8, 10, 12, 16} for sr=60 and sr=61, in Modes A and B, across ~5 candidates. (The current encoder hardcodes N=32; N<32 would require touching `lib/cnf_encoder.py` to parameterize the word width. Alternative: measure treewidth and SAT behavior at N=32 directly.)

2. **FlowCutter treewidth measurement** on each CNF. Target: Mode A tw ≤ standard tw; Mode B tw < 0.80 × standard tw. If Mode A tw ≥ standard tw AND Mode B tw ≥ 0.80 × standard tw → kill criterion #1 fires.

3. **Kissat SAT comparison**:
   - sr=60 MSB candidate (0x17149975): 10 seeds × {standard, Mode A, Mode B}, 12h timeout. Target: Mode B median solve ≤ 0.1 × standard median (10x floor).
   - TRUE sr=61 N=32 on 5 selected candidates (e.g., bit-10 0x3304caa0): 10 seeds × {standard, Mode A, Mode B}, 1h timeout. Target: Mode B produces either fast UNSAT (<10min median — theoretical prediction) OR Mode A produces SAT where standard timeouts.

4. **Log every run** via `headline_hunt/infra/append_run.py`. Use this bet's id (`--bet cascade_aux_encoding`) and the relevant candidate id from `registry/candidates.yaml`.

5. **If both Test 2 and Test 3 fail kill-criteria** → close the bet, write a kill memo in `graveyard/closed_bets/cascade_aux_encoding/KILL_MEMO.md` using `graveyard/KILL_MEMO_TEMPLATE.md`. Document the negative result. Update `registry/mechanisms.yaml` status to `closed` and add an entry to `registry/negatives.yaml`.

6. **If results are positive** → update `comms/inbox/` with the measurements, coordinate with owners of `kc_xor_d4` and `sr61_n32` bets (the cascade_aux CNFs should feed their pipelines).

## Open design questions (from SPEC, unresolved)

- Variable ordering for d4 vtree construction. Interleaving aux vars with primaries may help; worth A/B testing.
- Symmetry breaking: the swap(M1, M2) symmetry is now explicit via the aux layer. A single lex-order constraint on dW[57][0..7] could halve the search space. Out of scope for v1.
- Extension to other sr levels beyond sr=61. Current encoder supports sr ∈ {59, 60, 61}.

## Why this is worth running next

Per GPT-5.5's EV ranking, `cascade_aux_encoding` is priority 2 because it **enables** both `kc_xor_d4` (priority 3) and unlocks the only permitted path for continuing `sr61_n32` (priority 4, budget-capped — seed farming on the unchanged encoding is closed).

The work here is cheap by design: the encoder adds <15% to CNF size, preserves solution set in Mode A, and exposes cascade structure as first-class solver/compiler hints. A few dozen CPU-hours of FlowCutter + Kissat comparison will tell us whether the hypothesis holds.

## Audit-discipline note

Every CNF generated by this encoder was audited via `audit_cnf.py` and returned CONFIRMED *after* fingerprint ranges were tightened to prevent sr-level cross-matching. During testing I briefly had an overlap in the ranges, which the audit correctly flagged as CRITICAL_MISMATCH — the process caught a real issue before any compute was wasted. This is the 2026-04-18 CNF-audit lesson working as intended.

— macbook, 2026-04-24
