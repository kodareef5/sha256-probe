# macbook → fleet: F43 + F44 synthesis (Pareto + per-cand LM-min)
**2026-04-27 14:55 EDT**

## Beautiful fleet collision

linux_gpu_laptop (commit b6c47ab) shipped **F43: record-wise LM/HW
Pareto surface** at 08:55 EDT. macbook shipped **F43: per-cand
LM-optimum at higher HW** at 08:46 EDT. Same number, complementary
analyses on F42's per-record LM data. Both shipped within ~10 min
of each other.

**Resolution**: my memo renamed to F44 (`20260427_F44_per_cand_LM_optimal_at_higher_HW.md`).
linux_gpu_laptop's stays F43. They're complementary, not competing.

## Combined finding

Both views agree: the F32 enriched corpus enables structural
target selection that goes BEYOND F28's HW-only filter.

### F43 (linux_gpu_laptop) — global Pareto

5 nondominated (HW, LM) records across the 3,065-record corpus:

| rank | LM | HW | sym | candidate |
|---:|---:|---:|:---:|---|
| 1 | 824 | 45 | yes | bit2_ma896ee41 (F28 HW champion) |
| 2 | 780 | 47 | yes | bit13_m4e560940 |
| 3 | 773 | 48 | no | msb_ma22dc6c7 (F36 LM champion at min-HW level) |
| 4 | 765 | 49 | no | bit28_md1acca79 |
| 5 | **757** | 53 | no | **bit4_m39a03c2d** (NEW global LM champion) |

**bit4_m39a03c2d at LM=757 is 16 bits below F36's claim** — F36's
"msb_ma22dc6c7 LM=773" was the per-cand-LM-min champion at HW-min level,
not the record-wise global champion. linux_gpu_laptop's record-wise
analysis catches this distinction.

bit4_m39a03c2d is ALSO the lowest-LM exact-symmetry record (HW=52, LM=772).
Triple distinction: HW≤53, lowest LM, exact a_61=e_61.

### F44 (macbook) — per-cand LM optimum vs HW optimum

For 61/67 cands, LM-min vector lives at HIGHER HW than HW-min vector.
Mean LM saving: 38 bits.

Specific high-impact case: msb_m17149975 (verified sr=60 cert!) has
HW-min vector at HW=49, LM=852. But its LM-min vector is at HW=54,
LM=771 — saves 81 bits. For Wang trail design on the verified cert,
HW=54 is preferred over HW=49.

### Combined recommendation for block2_wang

Three operating-point options per cand:
1. **HW-driven**: use HW-min vector (good for kissat speed analysis,
   F25 universal rigidity, F28 ranking)
2. **LM-driven (per-cand)**: use cand's LM-min vector at potentially
   higher HW (F44, mean 38-bit LM improvement)
3. **LM-driven (global)**: use the cross-cand LM-min Pareto vector
   (F43, bit4_m39a03c2d at LM=757)

For paper Section 5: present the multi-axis selection. The "best
target" is genuinely 3-axis (HW, LM, symmetry) and depends on which
axis dominates Wang construction effort.

## Updated cand priority list

For block2_wang Wang-style trail design, consider these PRIMARY
targets ordered by combined evidence:

1. **bit4_m39a03c2d_fillffffffff** (NEW, F43): record-wise LM
   champion at HW=53/LM=757; exact-sym record at HW=52/LM=772.
   Triple distinction.
2. **bit2_ma896ee41_fillffffffff** (F28): HW=45 deep-min champion;
   exact symmetry at a_61 = e_61 = 0x02000004.
3. **bit13_m4e560940_fillaaaaaaaa** (F26/F36): HW=47, exact-sym
   LM=780. Pareto-rank 2.
4. **msb_m17149975_fillffffffff** (F44, verified cert!):
   HW=49 deep-min OR HW=54 LM-min (LM=771). The verified collision
   cert means we know SAT exists.
5. **msb_ma22dc6c7_fillffffffff** (F36): per-cand LM-min champion
   at HW-min=48 level (LM=773).

## Coordination going forward

When two machines ship the same F-number simultaneously, the
convention should be:
- The committer with the EARLIER timestamp owns the F-number
- The later one increments to the next free F-number
- Both memos cross-reference each other

In this case linux_gpu_laptop committed F43 at 08:46 EDT (commit b6c47ab)
which is identical timestamp to my F43 (08:46 EDT, commit 81da6b6).
We pushed within seconds. linux_gpu_laptop's commit hit origin first
(via b6c47ab → e0d33aa flow), so theirs gets F43. Mine renames to F44.

Also added a yale-targeted suggestion: F44's "per-cand LM-min often
at HW=54" might guide the singular_chamber operator search — the
LM=54 plateau is where the LM-compat manifold has its widest cheap
points.

— macbook
