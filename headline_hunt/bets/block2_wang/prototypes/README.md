# block2_wang prototypes

Fast probes for turning the block-2 Wang idea into measurable experiments.

## `block2_absorber_probe.c`

Purpose: test whether known block-1 residuals have an absorption gradient in a
free second block before investing in a full Wang bitcondition engine.

It reads the existing residual JSONL corpus, extracts each `diff63` vector,
treats it as an XOR IV difference for a second compression block, keeps `M1`
fixed at zero, mutates `M2[0..15]`, and hill-climbs the state-difference
Hamming weight after a chosen number of SHA-256 rounds.

Rows may also contain `block1_diff63` and `absorber_m2`. In that case the
probe starts from the supplied `M2` mask and polishes it, which lets F518-style
absorber profile seeds drive a longer follow-up run.

Build:

```bash
gcc -O3 -march=native -Wall -Wextra \
  headline_hunt/bets/block2_wang/prototypes/block2_absorber_probe.c \
  -o /tmp/block2_absorber_probe
```

Smoke test:

```bash
/tmp/block2_absorber_probe \
  headline_hunt/bets/block2_wang/residuals/F28_deep_corpus.jsonl \
  12 20000 0x1234 5
```

Overnight shape:

```bash
/tmp/block2_absorber_probe \
  headline_hunt/bets/block2_wang/residuals/F28_deep_corpus.jsonl \
  16 5000000 0x20260428 200 \
  > headline_hunt/bets/block2_wang/prototypes/absorber_r16_5M_top200.csv
```

Seeded polish shape:

```bash
/tmp/block2_absorber_probe \
  headline_hunt/bets/block2_wang/results/search_artifacts/20260502_absorber_matrix_overnight/F518_absorber_m2_late_round_seeds.jsonl \
  24 5000000 0x20260542 22 \
  > headline_hunt/bets/block2_wang/results/search_artifacts/20260502_F519_absorber_m2_polish_r24_5M.csv
```

Interpretation:

- Large positive `improvement` means the residual has an easy second-block
  local gradient under this crude XOR-IV model.
- Low `best_hw` candidates are the next inputs for a real bitcondition/trail
  engine.
- This does not produce certificates; it ranks residuals and round budgets.
