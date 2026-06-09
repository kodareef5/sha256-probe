# Reopen candidate forward_propagator.cpp — EVALUATED, does not reopen (2026-06-09)

Resolves the open reopen-candidate `REOPEN_CANDIDATE_forward_propagator.md` (2026-04-25),
which had specced the evaluation but explicitly NOT run it ("needs a focused test bench...
estimated effort 1-2 days").

## What was done (Direction B)

1. **Built** `q5_alternative_attacks/forward_propagator.cpp` against the installed CaDiCaL
   3.0.0 (`/opt/homebrew`, full IPASIR-UP API present; signatures match — old-style
   `notify_assignment(const vector<int>&)`). Compiles clean.
2. **Fixed the test harness**: the original used `alarm(timeout)` with no SIGALRM handler, so
   the process was SIGKILLed before the `Stats:` line printed — which is why it had never
   produced a measurement. Added a CaDiCaL `limit("conflicts", N)` budget (default 500k, the
   reopen threshold) so `solve()` returns gracefully and reports firing stats.
3. **Wired the varmap**: the current `cascade_aux_encoder` sidecar schema
   (aux_reg/aux_W/actual_p*) does not carry the `W1_57..W2_60` free-word keys the propagator
   parses. Wrote `encoders/fwdprop_varmap.py` to recover the free-word var IDs from
   `CNFBuilder.free_var_names` and emit the expected format + the matching sr=60 CNF.
4. **Ran** on the sr=60 m17149975 cascade CNF (13248 vars) at 200k and 1,000,000 conflict
   budgets.

## Result — confirmed negative (does NOT meet reopen criterion)

```
fwd_prop, 1,000,000-conflict budget:  Result UNKNOWN, 30s
Stats: 0 forward runs, 0 propagated
vanilla cadical, -c 1000000, same CNF: UNKNOWN, 27.5s
```

**The propagator fires 0 times over 1M conflicts** (2x the 500k reopen threshold). Its
trigger condition — all 32 bits of a single free schedule word simultaneously assigned —
is essentially never met during conflict-driven search: CDCL assigns/backtracks individual
diff-aux bits, never atomically completing a whole free word. With 0 firings it provides 0
propagation and adds ~9% wall overhead (30s vs 27.5s) for no benefit.

## Why this is the SAME failure as the killed Rule-4 propagator

The kill memo's core finding was "CDCL on cascade-DP CNF is DIFF-AUX-FOCUSED ... rules
depending on actual register values fire heavily during preprocessing, go SILENT during deep
search." The forward_propagator was the hoped-for fix because it watches the **free-word**
variables (which CDCL *does* decide bit-by-bit). But the **complete-word trigger** re-creates
the same silence: CDCL never completes a word atomically in deep search. The reopen criterion
("≥2× speedup over Mode B at 500k+ conflicts") is not just unmet — the mechanism cannot fire
at all.

## Status

- Reopen criterion: **NOT met.** programmatic_sat_propagator stays **closed**.
- Remaining theoretical variant: a *non-lazy* propagator firing on PARTIAL word assignments
  (interval/bound reasoning over incomplete words). That is a different, unbuilt design and
  would need sound partial-forward bounds; not pursued. Would-change-my-mind: a propagator
  that fires >0 times per 100k conflicts in deep search AND yields measurable conflict
  reduction.

## Reproduce
```
g++ -O3 -std=c++17 -I/opt/homebrew/include q5_alternative_attacks/forward_propagator.cpp \
    /opt/homebrew/lib/libcadical.a -o /tmp/fwd_prop
python3 headline_hunt/bets/cascade_aux_encoding/encoders/fwdprop_varmap.py \
    --m0 0x17149975 --fill 0xffffffff --kernel-bit 31 --mode expose \
    --out-cnf /tmp/s.cnf --out-varmap /tmp/s.varmap.json
/tmp/fwd_prop /tmp/s.cnf /tmp/s.varmap.json 600 1000000   # -> 0 forward runs
```
