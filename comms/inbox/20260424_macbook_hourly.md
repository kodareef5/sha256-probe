# macbook hourly progress — 2026-04-24

Append-only. One short entry per hour of work shipped (or honestly idle, with reason).

## 17:55 EDT — CNF inventory audit + fingerprint expansion

Shipped:
- Audited all 42 CNFs in `cnfs_n32/`. Pre-expansion: 37 CONFIRMED + 5 INFERRED. Post-expansion: **42/42 CONFIRMED**.
- Added 2 new fingerprint variants to `infra/cnf_fingerprints.yaml`: `sr61_n32_full` (the bit25 m09990bd2 outlier) and `sr61_n32_true_explicit` (4 TRUE_sr61_*.cnf files).
- Tightened the existing `sr61_n32_enf0` and `sr61_cascade_n32` ranges from the original speculative bounds to observed-data tight: `[11150, 11320]` / `[46700, 47200]` for cascade_enf0 (was `[10000, 12500]` / `[44000, 50000]`), and `[11150, 11290]` / `[47300, 47720]` for cascade_explicit. Each fingerprint now records `observed_n`, `observed_vars`, `observed_clauses` so future workers can verify ranges aren't drifting.
- Generated `datasets/hashes/cnfs_n32_audit_20260424.md` — full audit snapshot table (file × verdict × variant × matches × vars × clauses × sha256-12) of the 42-CNF inventory at this commit. This is what the fleet sees when it pulls; future deltas have a baseline to compare against.

Why this matters: every fleet solver run on these CNFs now gets a CONFIRMED verdict instead of INFERRED. INFERRED is what trains people to ignore the audit — eliminating it tightens the discipline.

`validate_registry.py` clean (0 errors, 0 warnings).

## 18:00 EDT — q4_mitm_geometry audit + mitm_residue unblock

Shipped:
- Audited 30+ scripts in `q4_mitm_geometry/`. Wrote `bets/mitm_residue/prototypes/audit_summary.md` (the file the BET README pointed at as next_action).
- Smoke-tested `q4_mitm_geometry/cascade_mitm_full.py` — verified working: recovers sr=60 cert, ~86k W[57] samples/s on macbook.
- Promoted `mitm_residue` from `blocked` → `open` in both BET.yaml and mechanisms.yaml. The bet was never actually blocked — tools were just dormant. Updated `current_progress` and `next_action` with five concrete scale-up items, ranked by leverage.
- GPU box should pick up `gpu_mitm_prototype.py` at N=8 (validates against the known 260 collisions). Macbook will pair on the table-structure work (~100 LOC Python).

validate_registry: 0 errors, 0 warnings.

## 18:22 EDT — encoder swept across all 35 candidates

Shipped:
- New driver: `bets/cascade_aux_encoding/encoders/generate_all.py`. Reads candidates.yaml, generates aux CNFs in both modes for each, audits each, writes a baseline manifest.
- Generated 70 CNFs (35 candidates × 2 modes). **All 70 CONFIRMED**. Encoder handles every candidate cleanly — no edge cases (expected one or two to error on cascade-eligibility check, but the existing candidates.yaml is well-curated).
- Manifest written to `bets/cascade_aux_encoding/results/aux_encoder_manifest.md` — baseline so any encoder drift becomes a visible diff.
- Caught a self-bug: my initial filename scheme didn't match audit_cnf.py patterns, so all 70 audited UNKNOWN. Fixed inline (added `aux_{mode}_sr{sr}_` prefix) and re-ran. Process value: writing the audit step into the driver caught the regression in seconds.

Now anyone running a kissat sweep across the cascade_aux candidates can either:
  - run `generate_all.py --keep-cnfs <dir>` to materialize the CNFs, or
  - call cascade_aux_encoder.py per-candidate.

## 18:35 EDT — forward MITM table builder + first residue distribution

Shipped:
- New prototype: `bets/mitm_residue/prototypes/forward_table_builder.py`. Extends cascade_mitm_full to round 63, dumps round-63 register-difference distribution as JSONL.
- Hit a real bug while writing it: original draft fixed cascade offsets to cert values, which only worked for the cert (1/50,000 random samples held). Fix: compute cascade offsets dynamically per-round from current state. After fix: 50,000/50,000 cascade-held.
- First empirical result on the residue distribution: HW(da||db||dc||dd) at round 63 over 50k random (W[57], W[58], W[59]) triples — **mean 48, median 48, min 28, max 70 out of 128 possible**. Distribution concentrated around 48, visibly skewed left compared to uniform-random. Consistent with cascade structure pulling HW down.
- Result writeup: `bets/mitm_residue/results/20260424_forward_residue_distribution.md`. Includes histogram, implications for the bet hypothesis, and three concrete <30min next-actions for the next worker (cross-candidate sweep, W[60] sweep, hard-residue bit identification).

Speed: 24k samples/s single-threaded Python on macbook. Means scaling to 50M samples (the 'where's the next collision' question) is ~30 min CPU.

## 18:38 EDT — cross-candidate sweep: candidate-independence CONFIRMED

Shipped:
- Ran forward_table_builder across 7 candidates (kernel bits 0, 6, 10, 13, 17, 19, 31). 20k samples each, ~5s total CPU.
- **Result: residue distribution is candidate-independent**. Median exactly 48 for every candidate. Mean 48.0-48.1 (range 0.1). Min HW 26-31. Max HW 65-72.
- This validates the bet's key memory-budget assumption: forward-table MITM built for one candidate re-keyable for others. ~256GB at N=32 doesn't multiply by candidate count.
- Writeup: `bets/mitm_residue/results/20260424_cross_candidate_sweep.md`. Full table + 3 next-actions ranked by leverage.

This addresses item #4 from audit_summary directly — the bet is now substantially more confident in its core assumption.

## 18:45 EDT — hard-residue bits empirically identified

Shipped:
- New analyzer: `bets/mitm_residue/prototypes/hard_residue_analyzer.py` — measures per-bit bias at rounds 60 and 63 over a large sample.
- Ran 1M samples on the MSB candidate. **Round 60 result: ~228 structurally-determined bits + ~28 truly-uniform bits**. Bet hypothesis (232 free + 24 hard) refined and substantially confirmed.
- The hard residue is **localized to register g** at round 60: ~18 uniform bits in g, ~4 in f, ~4 in h. Total ~26 hard bits.
- Memory implication for the bet: forward table is **2^26 entries (~17 GB)**, not 2^32 (~256 GB). Bet economics improve dramatically.
- Round-60 vs round-63 distinction sharply confirmed: at round 63 only dd and dh are zero (64 bits); the rest are uniform. **Round 60 is the right MITM meeting point.**
- Writeup: `bets/mitm_residue/results/20260424_hard_residue_findings.md` with specific hard-bit positions in g/f/h and three concrete next-actions (cross-candidate hard-bit positions, W[60] sweep, backward analyzer).

## 18:55 EDT — cross-candidate hard-bit positions: refuted amortization, confirmed size

Shipped:
- Ran hard_residue_analyzer across 6 candidates × 200k samples each (~5 min CPU).
- **Key finding**: hard-residue *size* is ~24 bits/candidate (range 17-28, mean 24.5) — empirically validates bet's prediction. But hard-residue *positions* differ across candidates: pairwise Jaccard 0.08-0.47, **zero bits uniform across all 6 candidates**.
- Implication: forward-table MITM is **per-candidate** (~17GB each), NOT amortizable across candidates. Multi-candidate sweep budget = 17GB × N. Single-candidate MITM remains strongly viable.
- g60 dominance is universal: 12-21 of the uniform bits live in g60, every candidate. f60 and h60 contribute 3-4 and 2-5 bits respectively. The register identity is invariant; only the within-register positions vary.
- Open question raised: are hard-bit positions algebraically predictable from (m0, fill, kernel_bit)? If yes, the amortization problem dissolves. Worth investigating next.
- Writeup: `bets/mitm_residue/results/20260424_cross_candidate_hard_bit_positions.md` with full Jaccard matrix, register-by-register decomposition, three concrete next-actions.
