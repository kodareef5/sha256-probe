# Collision lists

Enumerated collision sets (one row per collision, JSONL format).

Used by:
- BDD construction (collision-list builder, ~0.02s pipe to BDD)
- block2_wang residual corpus (filter collisions by HW/register concentration)
- chunk_mode_dp validation (must enumerate the same set as DP)

Naming: `collisions_n<N>_<kernel_id>.jsonl`
