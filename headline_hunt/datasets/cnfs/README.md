# CNFs

The existing TRUE sr=61 CNFs live at the repository root in `../../../cnfs_n32/`.
Do NOT move them — too many references would break.

This directory is for **new** CNFs produced after the 2nd-wind pivot, especially:
- cascade-auxiliary encoding output
- XOR-preprocessed variants
- per-bet experimental CNFs

Naming convention: `<bet_id>_<encoder>_<candidate_id>.cnf`

Every new CNF must pass `infra/audit_cnf.py` before being queued.
