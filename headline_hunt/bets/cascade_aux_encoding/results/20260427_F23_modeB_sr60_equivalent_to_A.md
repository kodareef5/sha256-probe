# F23: Mode B sr=60 sanity test — wall-equivalent to Mode A
**2026-04-27 02:15 EDT**

Tests whether Mode B's "force semantics" gives a measurable advantage
on sr=60 reproducibility (vs Mode A's "expose" relaxation). Per the
F4b finding, Mode B is ~1.5× faster than Mode A at sr=61. Question:
does the same hold at sr=60?

## Setup

- CNFs: cascade_aux Mode A and Mode B, both sr=60, msb_m17149975
  - Mode A: 13248 vars, 54919 clauses (audit CONFIRMED)
  - Mode B: 13248 vars, 54919 clauses (audit CONFIRMED, different
    clauses though same count — diff size 1594 lines)
- 5 seeds × 1M conflicts × 60s wall cap

## Result

| seed | Mode A wall (F21) | Mode B wall (this) | speedup |
|---:|---:|---:|---:|
| 1 | 27.38 s | 26.13 s | 1.05× |
| 2 | 27.09 s | 24.82 s | 1.09× |
| 3 | 27.46 s | 26.59 s | 1.03× |
| **5** | 26.73 s | 26.06 s | 1.03× |
| 7 | 26.18 s | 25.57 s | 1.02× |
| **median** | **27.09 s** | **26.06 s** | **1.04×** |

**Both modes UNKNOWN. Mode B is 4% faster at this budget — within noise.**

## Comparison to F4b sr=61 finding

F4b (sr=61, n=18 cands × 3 seeds): Mode B is ~1.50× faster than Mode A.
F23 (sr=60, 1 cand × 5 seeds): Mode B ~1.04× faster than Mode A.

**Mode B's advantage is sr=61-specific, not sr=60.**

## Interpretation

At sr=60:
- 4 free schedule words (W[57..60]) give the solver enough freedom to
  satisfy cascade-1 + cascade-2 directly via the auxiliary variables
- Mode A's "exposed" auxiliaries are functionally equivalent to Mode B's
  "forced" auxiliaries — both encode the same constraints
- Solver wall is dominated by the search itself, not the encoding's
  preprocessing

At sr=61:
- 3 free schedule words = over-determined system (Viragh's slack=-64)
- Mode B's force clauses prune the search space immediately (UNSAT-side
  propagation cuts more)
- Mode A's exposed semantics let the solver explore more before pruning
- Mode B is structurally faster at recognizing the over-determination

## Implication

For the publication's Section 4, this is one more dimension of
reproducibility: **switching encoder mode (A→B) does NOT meaningfully
change sr=60 solve time at moderate budgets**. The 12h seed=5 finding
was specific to deep budget at this cand, regardless of encoding mode.

For deep-budget reproduction attempts: Mode A and Mode B should be
approximately equivalent for finding sr=60 SAT. No reason to prefer
one over the other.

## Discipline

5 Mode B kissat runs to be logged via append_run.py. CNF audit
CONFIRMED (different fingerprint hash than Mode A).

EVIDENCE-level: VERIFIED at the budget tested.
