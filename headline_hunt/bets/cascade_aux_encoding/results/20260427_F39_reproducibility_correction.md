# F39: REPRODUCIBILITY CORRECTION — bit2's "26.51s advantage" was system-load artifact
**2026-04-27 12:57 EDT**

Critical correction. F30/F37/F38 reported a "9-10 second cliff" between
bit2_ma896ee41 (26.51s) and other cands (35-36s). Re-verification under
identical conditions reveals: **bit2 has the SAME wall as the others
(~35.6s). The cliff was a measurement artifact.**

## What happened

F30 measured bit2 at median 26.51s when ONLY bit2 was running on the
system. F37 measured msb_ma22dc6c7 at median 35.99s under same parallel
setup but at a different time. F38 re-measured 4 more cands under
"current" conditions (each batch of 5 simultaneous kissat runs).

In F38 I assumed bit2's 26.51s was comparable to F38's measurements.
Wrong. Under F38's actual conditions, bit2 also runs ~35s.

## Re-verification (this F39 run)

| cand | symmetry | HW | F30/F37/F38 | F39 (this) |
|---|---|---:|---:|---:|
| **bit2_ma896ee41** | EXACT | **45** | F30: 26.51s | **35.61s** |
| msb_ma22dc6c7 | (no) | 48 | F37: 35.99s | (not re-run) |
| **bit13_m4e560940** | EXACT | **47** | (no prior) | **35.94s** |
| bit10_m9e157d24 | (no) | 47 | F38: 34.28s | (not re-run) |

**bit2 is 35.61s — INDISTINGUISHABLE from bit13 at 35.94s and
msb_ma22dc6c7 at 35.99s. There is no cliff.**

## Implications

1. **F38's "HW=45 cliff" is VOID.** The 7.77s gap between F30's bit2
   and F38's HW=47 cands was not from HW=45 having structural
   advantage — it was different system load between F30 and F38.

2. **F37's "LM-min hypothesis falsified" remains valid** because the
   comparison was msb_ma22dc6c7 (35.99s) vs bit2 (claimed 26.51s).
   With bit2 corrected to 35.61s, both are ~36s. F37 is now: "LM-min
   doesn't make solving FASTER" — true but trivial since BOTH are at
   the same plateau.

3. **F30's message-modification claim** (bit2 might find SAT faster
   at deep budgets) needs re-examination. The advantage at 1M
   conflicts is non-existent.

4. **For paper Section 5**: the "bit2 NEW CHAMPION" claim survives
   on STRUCTURAL grounds (HW=45 lowest, exact symmetry), NOT on
   solver-speed grounds. We must NOT claim bit2 solves faster on
   kissat — F39 contradicts that.

## Per-conflict equivalence reaffirmed

The proper interpretation:
**ALL distinguished cands have median wall ~35-36s at 1M conflicts under
parallel measurement.** This includes:
- HW=45 EXACT-sym (bit2): 35.61s
- HW=47 EXACT-sym (bit13): 35.94s
- HW=47 non-sym (bit10): 34.28s
- HW=48 (msb_ma22dc6c7): 35.99s
- HW=49-51 (multiple): 34-36s

The per-conflict heuristic in kissat does NOT distinguish among these
cands at 1M conflicts. Cand selection at the SOLVER level is mostly
irrelevant; cand selection at the STRUCTURAL level (HW, LM, symmetry)
matters for Wang construction.

## What DOES the bit2 structural advantage buy us?

If kissat at 1M conflicts can't see the advantage, where does it show?

Hypothesis (untested): at DEEP budgets (>1B conflicts), the structural
property might enable kissat to find SAT on bit2 faster than on other
cands. This is the original F30 deferred-test claim.

To test: 12-hour kissat × multiple seeds × bit2 cascade_aux Mode A.
Big compute (4 cores × 12 hours = 48 CPU-h). Out of scope for this
hour without explicit authorization.

## What this hour's findings (F35-F39) ACTUALLY established

Filtering through to verified claims only:

✓ **F34**: All 67 cands have EXACTLY 43 active modular adders
   (universal cascade-1 invariant).

✓ **F35**: LM cost varies across cands (780-870 for 11 exact-sym,
   773-890 for all 67). Real metric.

✓ **F36**: All 67 cascade-1 trails are LM-COMPATIBLE (zero violators).
   Universal cascade structural property.

✓ **F36**: Global LM champion is msb_ma22dc6c7 at 773 (NOT exact-
   symmetry — F28's HW+sym filter missed it).

✗ **F37 + F38 cliff hypotheses**: VOIDED by F39. bit2 has same wall
   as plateau cands.

✓ **F39**: per-conflict kissat equivalence reaffirmed at ~35-36s
   across all measured cands. Cand selection isn't a solver-speedup
   axis at 1M conflicts.

## Discipline lessons

1. **Always re-measure baseline under same conditions**: F30 vs F38
   compared apples to oranges. Not a methodology error per se but a
   comparability one.

2. **Parallelism artifacts are real**: 5 simultaneous kissat processes
   compete for shared resources. Same N=5 measurement under different
   system loads gives different walls.

3. **F30's 26.51s should be marked "ad-hoc baseline, not reproducible
   under high-load condition"**.

10 kissat runs logged via append_run.py: 5 bit2 re-verification + 5
bit13 discriminator.

EVIDENCE-level: VERIFIED for the correction. F39 supersedes F30/F37/F38
on kissat-speed claims for bit2 vs HW≥47 cands.

## Concrete next moves

1. **Re-measure msb_m17149975 baseline** under F39 conditions to
   establish proper apples-to-apples plateau wall.
2. **Sequential (non-parallel) kissat measurement** on bit2 — see if
   it's faster without contention. Would establish "single-thread
   advantage" vs "parallel-equivalent."
3. **DEEP budget test on bit2** (~12h kissat) — if structural
   advantage exists, this is where it shows. Big compute, needs
   authorization.
4. **Update F30/F37/F38 memos with retraction note** referencing F39.
   (Memos stand as historical record but readers should follow the
   F39 correction.)
