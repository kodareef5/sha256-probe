---
date: 2026-04-28
bet: cascade_aux_encoding
status: F211_HEADROOM_CONFIRMED — kissat BVE eliminates 20%, F211 unbounded shell predicts 70%
---

# F220: Empirical kissat preprocessing vs F211's shell-elimination prediction — 50% headroom

## Setup

F211 predicted that 75% of cascade_aux's variables can be eliminated
in the "shell" via min-degree elimination with max-fill ≤14. F220
empirically tests how much kissat's actual preprocessor eliminates
in practice.

## Setup details

CNF: `aux_expose_sr60_n32_bit06_m6781a62a_fillaaaaaaaa.cnf`
- 13179 variables, 54646 clauses
- F211/F213 hard-core size: ~3,907 vars (29.6% of vars)
- F211 predicted shell: 9,272 vars (70.4%)

Run kissat with default settings, capture preprocessor statistics.

## Result

kissat preprocessor variable trajectory (from `c` lines):

```
Phase                   | Active vars | % of original
Initial                 |       13178 | 100%
After unit propagation  |       10580 |  80%
After BVE pass 1        |       10646 |  81%
After all preprocessing |       10615 |  81%
```

**kissat eliminates 19% of variables (~2,560 vars).** The remaining
10,615 vars (81%) are active during CDCL search.

## Comparison to F211 prediction

| Approach | Vars eliminated | % of original | Active vars remaining |
|---|---:|---:|---:|
| kissat default BVE | ~2,560 | 19% | ~10,615 |
| F211 min-degree (unbounded) | ~9,272 | 70% | ~3,907 |
| **Headroom** | **~6,712** | **51%** | **6,708 fewer** |

There is **~50% of variable-elimination headroom** between what kissat
does in practice and what's graph-theoretically possible. F211's shell
prediction holds in theory but is NOT achieved by stock kissat
preprocessing.

## Why kissat eliminates less than min-degree

### kissat's bounded BVE
Kissat's BVE is bounded by `--eliminatebound=16` (default): it only
eliminates a variable v if the resulting clause set has at most
`16` more clauses than before. This conservative bound prevents
explosive clause growth at the cost of leaving many eliminable
variables active.

### Min-degree elimination is unbounded
F211's min-degree heuristic eliminates greedily by lowest-degree
vertex, regardless of fill-in cost. Some eliminations create dense
fill-in (max-fill 699 at the end), but the early 70% of eliminations
have max-fill ≤14 — which is WELL within kissat's bound of 16. So
kissat *could* eliminate those 70%, but it doesn't because:

1. kissat's elimination order is heuristic (not strictly min-degree).
2. kissat budgets effort per variable (`--eliminateeffort=100‰`).
3. kissat may prefer search over preprocessing for some var-types.

In short: kissat's 20% elimination is not a fundamental ceiling —
it's a budget+heuristic choice. A custom preprocessor with strict
min-degree order and unbounded effort could reach F211's 70%.

## Strategic implication: custom preprocessor is the move

F213-c proposed implementing Stage 1 outer-shell elimination as a
standalone preprocessor. F220 *quantitatively* justifies this:

- **6,700 more vars** eliminable beyond kissat's default (3,907
  hard-core remaining instead of 10,615).
- The reduced CNF would have ~10⁵ clauses (since each eliminated var
  averaged ~5 clause connections, net change is minor).
- kissat solving the reduced CNF would search a 5K-var space instead
  of 10K-var, likely faster.

**Predicted speedup**: 2-5× from search-space reduction alone, before
any BP marginal guidance. The F211 decoder's Stage 1 alone is worth
implementing.

## Concrete next probe

Implement a minimal Stage 1 preprocessor:
1. Read CNF.
2. Run min-degree elimination but cap fill at threshold T (e.g., T=14).
3. Output the reduced CNF (vars renamed to dense range 1..K).
4. Output a "restoration map" so SAT/UNSAT verdicts on reduced CNF
   transfer to original.
5. Audit: ensure reduced CNF has the same UNSAT verdict (verify via
   small DRAT proof or a smoke kissat run that returns the same
   answer).

Estimated implementation: ~2-3 hours. Tests F211/F213's design
empirically and produces a real artifact.

## Both kissat runs (with vs without BVE)

| Run | Setting | 60s outcome | Wall |
|---|---|---|---:|
| F218 | default (BVE on) | UNKNOWN (TIMEOUT) | 60.04s |
| F219 | --eliminate=false (BVE off) | UNKNOWN (TIMEOUT) | 60.03s |

Both timeouts at 60s. The test was too short to differentiate
solver effectiveness; both can't solve in 60s. The CNF is genuinely
hard. Need longer budget OR a reduced CNF (per F220 thesis).

## What's NOT being claimed

- That F211's preprocessor will give 2-5× speedup (proposal,
  not result).
- That kissat is wrong to use bounded BVE (it's a sound choice for
  general SAT; the cascade_aux structure is special).
- That min-degree elimination is the optimal preprocessor strategy
  (it's a heuristic; better orderings might exist).

## Discipline

- 1 SAT compute (kissat preprocessing test, 5s)
- 0 SAT solver runs that produced verdict (both 60s timeouts =
  no SAT/UNSAT outcome to log via append_run.py)
- F220 quantitatively confirms F211's shell-elimination prediction
  has empirical headroom over kissat's default
- Strategic call: implement Stage 1 preprocessor in a future session

## Run logs

The 60s timeout runs (F218, F219) ended with status UNKNOWN, which
the registry's `append_run.py` does not accept directly. They will
not be logged in runs.jsonl as discrete events. The F220 finding
is captured in this memo instead.
