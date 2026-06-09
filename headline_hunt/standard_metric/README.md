# standard_metric/ — the R-axis pivot workspace

Created 2026-06-09 (fable model test). This workspace exists because the Tier-0 re-pricing
analysis concluded the project should pivot from the Viragh **sr / schedule-compliance**
metric (which is orthogonal to the field's metric and does not transfer — see
`../reports/20260609_metric_bridge_lattice.md` and `../reports/20260609_structural_transfer_verdict.md`)
to the **standard step-reduced collision** metric, where all records and tooling live.

## What's here
- `setup_sat_cas.sh` — reproducibly builds the SOTA **SAT+CAS** engine
  (`nahiyan/cadical-sha256`, arXiv 2406.20072) + the Nejati collision encoder, and validates
  end-to-end. Includes the one-line upstream build fix (missing `1_bit/mendel_branch.hpp`
  include) needed to compile on clang/macOS. Both upstreams are MIT-licensed.
- `characteristics/` — the bundled published starting differential characteristics
  (Mendel 38-step, Nahiyan 28/38/39-step, Prokop 18-24-step, Saeed 25-step), copied from the
  Nejati encoder's `tables/` for reproducibility. These seed the encoder.
- `20260609_sat_cas_import.md` — the T1.3 import + validation report.

## Quick start
```bash
bash headline_hunt/standard_metric/setup_sat_cas.sh /tmp
cd /tmp/cryptanalysis/encoders/nejati-collision
./encoder -r 28 --diff_desc -d tables/28_nahiyan.txt > /tmp/c28.cnf 2>/dev/null
/tmp/cadical-sha256/build/cadical /tmp/c28.cnf          # CAS engine
```

## Status
The engine is imported and validated (21/24/28-step collisions solved; CAS is ~2.9× more
conflict-efficient than plain cadical at 28-step). The 38/39-step frontier instances are
genuinely hard (hours-to-days per the literature). Applying this engine to a repo-specific
object (e.g. the block-2 absorber) requires encoding that object in the Nejati differential
format — the natural next step for R-axis work.
