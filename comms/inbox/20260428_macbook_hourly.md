# macbook hourly notes — 2026-04-28

(Earlier hours of this multi-hour push are in 20260427_macbook_hourly.md;
this file starts as the calendar date rolled over.)

---

## 03:55 EDT — F96: bit28_md1acca79 corpus + top-10 multi-solver cert-pin (yale's primary cand)

Extends F95's top-10 audit to bit28_md1acca79 — yale's overall project
champion (per yale's online Pareto sampler). F95 covered 5 cands but
bit28 was notably absent. F96 closes that gap.

**Build**: `build_corpus.py --m0 0xd1acca79 --fill 0xffffffff
--kernel-bit 28 --samples 1M --w1-60 0x0a0627e6` (yale's HW=45/LM=637
W1[60]). 38s wall, 18,633 records ≤ HW=80, min HW=59.

**Cross-cand corpus (now 6 cands)**: bit28 has the most records
(18,633) but min HW=59 vs bit3's 55. Note: yale's deep exploration
found HW=33 because yale VARIES W1[60]; the corpus FIXES it.

**Cert-pin result**: 10/10 UNSAT, 3 solvers agree per witness.
Top-10 HW range: 59-63. Total wall ~0.3s.

**Combined cert-pin evidence corpus** (F70 + F71 + F94 + F95 + F96):
  - 132 distinct W-witnesses
  - 262 cross-solver cells
  - 0 SAT, 262 UNSAT, 100% near-residual

**Total bit28 cert-pin verifications**:
  F70 yale frontier: 5 W-witnesses
  F80 yale LM=637:   1 W-witness
  F96 corpus top-10: 10 W-witnesses
  ----- 16 W-witnesses on bit28, all UNSAT across 3 solvers

**Yale's bit28 single-block search has saturated empirically.** The
headline path IS the Wang block-2 absorption trail (per F82 SPEC).

10 runs logged via append_run.py. Registry total: 929 → **939**.

Memo: `headline_hunt/bets/block2_wang/results/20260428_F96_bit28_corpus_and_certpin.md`
Corpus: `headline_hunt/bets/block2_wang/residuals/by_candidate/corpus_bit28_md1acca79_fillffffffff.jsonl` (2.4 MB)
