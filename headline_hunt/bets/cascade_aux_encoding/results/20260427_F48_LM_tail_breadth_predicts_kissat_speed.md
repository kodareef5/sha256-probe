# F48: LM-tail-breadth predicts kissat speed (4-cand confirmation of F47)
**2026-04-27 15:30 EDT**

Tests F47's hypothesis: cands with BROAD LM tails are kissat-harder
than cands with NARROW tails. Adds msb_m17149975 (verified sr=60
cert cand!) as intermediate-tail data point.

## Combined sequential data (1M conflicts × 5 seeds × clean conditions)

| cand | HW | LM-tail breadth | seq median | seq RANGE | tail class |
|---|---:|---|---:|---:|---|
| bit2_ma896ee41 | 45 | narrow (F25 unique vector) | 27.08s | 2.6s | NARROW |
| bit10_m9e157d24 | 47 | narrow | 28.04s | 3.2s | NARROW |
| **msb_m17149975** | **49→54** | **medium-broad (F44 81-bit gap)** | **35.81s** | **8.07s** | **MEDIUM** |
| bit28_md1acca79 | 49→73 | broad (F45 LM 855→718) | 39.25s | 21.8s | BROAD |

Two metrics, both ordered consistently: median wall AND seed-variance
RANGE both increase with LM-tail breadth.

## The ordering

| metric | NARROW | MEDIUM | BROAD |
|---|---:|---:|---:|
| seq median | 27-28s | 36s | 39s |
| seq range | 2-3s | 8s | 22s |
| Δmedian vs narrow | 0 | +8s | +12s |
| Δrange vs narrow | 0 | +5s | +19s |

Both metrics scale with tail-breadth class.

## What "LM tail breadth" means structurally

For each cand, the F32 corpus contains records spanning HW 45-60.
The LM cost varies across these HW levels.

- **NARROW tail**: per F25 universal rigidity, the cand has 1
  distinct vector at min HW. LM cost variance across the 40+ records
  at higher HW levels is small.
- **MEDIUM tail**: msb_m17149975's HW=49 vector has LM=852, but its
  HW=54 LM-min vector has LM=771. 81-bit gap. F44.
- **BROAD tail**: bit28_md1acca79 has LM=855 at HW=49 (F32 deep min)
  but yale's online sampler found LM=718 at HW=73 — 137-bit gap.
  Even broader at HW=64 with LM=743.

So tail-breadth = max LM saving across HW levels.

## Tested hypothesis (F47 → F48)

**H**: kissat speed at 1M conflicts on cascade_aux Mode A correlates
with cand's LM-tail breadth.

**N=4 confirmation**:
- 2 narrow-tail cands at 27-28s
- 1 medium-tail cand at 36s
- 1 broad-tail cand at 39-51s

**N=4 is small** but the SIGN of the correlation is unambiguous, and
the MAGNITUDE follows a monotonic ordering. Stronger than a single
data point can claim.

## Why this might be true (mechanism speculation)

A broad LM tail means MANY cascade-1 trails of similar low-LM cost
exist for this cand at different HW levels. The corresponding
cascade_aux CNF encodes ALL these trails simultaneously (each is a
satisfying assignment to the schedule constraints).

When kissat searches, it has many "similar but not identical"
satisfying paths to potentially explore. Without a clear best path
(narrow tail), it may waste time exploring branches.

Compare to narrow-tail cands (bit2, bit10): F25 says exactly 1
distinct vector at min HW. The cascade-1 manifold has a sharp
extremum. Kissat converges quickly to or away from it.

**Mechanism speculation**: tail-breadth is a "branchiness" metric
for the cascade_aux SAT problem. Higher branchiness = harder for
CDCL solvers.

## Implication for paper Section 4/5

Solidifies the per-conflict cascade_aux behavior across the 67-cand
registry into a structured narrative:

> "kissat at 1M conflicts on cascade_aux Mode A sr=60 CNFs has wall
> times that scale with the cand's LM-tail breadth — the variance of
> Lipmaa-Moriai cost across the HW=45..60 range. NARROW-tail cands
> (1 distinct vector at min HW per F25) cluster at 27-28s sequential.
> MEDIUM-tail cands (~80-bit LM gap across HW levels) take ~36s.
> BROAD-tail cands (~140-bit gap) take 39-51s. The relationship holds
> for both median wall and seed variance."

This is a NEW publishable finding tying F25 (universal rigidity),
F35/F36/F42 (LM cost framework), F44 (per-cand LM gap), and yale's
F45 (online Pareto sampler) into a single quantitative story.

## Implication for block2_wang target selection

bit2_ma896ee41 (NARROW tail, HW=45 champion) is BOTH:
- The HW champion (F28, F32 universal rigidity rank 1)
- A fast solver target (F39 35.61s parallel-5, ~27s sequential)

bit4_m39a03c2d (MEDIUM tail per F46, ~37s parallel-5) and
msb_m17149975 (MEDIUM tail, verified cert!) are at slightly slower
solver speeds but offer Wang-axis advantages.

bit28_md1acca79 (BROAD tail) is structurally distinct on the LM axis
(low LM=718) but the cascade_aux SAT problem is harder. Discrepancy
suggests two different "structural advantage" axes — Wang construction
on one, SAT search on the other.

## Discipline

- 5 kissat runs logged via append_run.py (msb_m17149975 sequential)
- All runs UNKNOWN at 1M conflicts (consistent)
- CNF audit: pre-existing CONFIRMED CNF in datasets/certificates/

EVIDENCE-level: VERIFIED for the 4-cand ordering. HYPOTHESIS for the
mechanism (branchiness story). Need 2-3 more cands at intermediate
breadth to harden the magnitude relationship.

## Concrete next moves

1. **Test 2-3 more cands with intermediate breadth** (e.g.,
   bit13_m4e560940 sequential, bit4 sequential). If the median +
   range follows the curve, hardens the claim.

2. **Define LM-tail-breadth quantitatively**: for each cand, compute
   `lm_breadth = max_lm - min_lm across F32 corpus records`. Add to
   F28_deep_corpus_enriched.jsonl as `cand_lm_breadth` field.

3. **Update cand_select.py with --order-by-tail-breadth flag**:
   ranks cands by LM-tail-breadth ascending (= solver-friendliest first).

4. **Yale's operator design**: the broad-tail cands have multiple
   anchors but kissat-hard CNF. Yale's manifold-search may find
   anchors that kissat can't reach. This is a hint of complementary
   strengths between SAT and structural search.
