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
