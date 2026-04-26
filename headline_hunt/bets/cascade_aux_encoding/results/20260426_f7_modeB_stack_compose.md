# F7: Mode B + de58+de59 stack — they compose, modest extra (~6%)
**2026-04-26 19:38 EDT**

Tested whether Mode B (force-side cascade-2 enforcement) and the
de58+de59 stack hints (commit 7be3536) compose. Single-cand sanity
on bit19 (m0=0x51ca0b34, fill=0x55555555, bit=19, W57=0x4f9409ff),
3 seeds, 50k kissat budget.

## Result

| variant | median (s) | speedup over A_base | status |
|---|---:|---:|---|
| Mode A (A_base) | 2.461 | 1.00× | UNKNOWN |
| Mode A + stack (A_stack) | 1.572 | **1.57×** | UNKNOWN |
| Mode B (B_base) | 1.201 | **2.05×** | UNKNOWN |
| Mode B + stack (B_stack) | 1.132 | **2.17×** | UNKNOWN |

Status note: B_stack returns UNKNOWN, NOT UNSAT. So the stack hints
(injecting de58=0x7eb55389 + de59=0xf9f7f920 as 64 unit clauses) do
NOT immediately contradict Mode B's force-side constraints. The two
mechanisms operate on different propagation paths — Mode B forces
cascade-2 via Tseitin clauses on the round-58 outputs; the stack
hints constrain the auxiliary `e`-slot variables. They share variable
roots but the encoder doesn't reduce them to a contradiction.

## Composition gain (B_stack vs B_base alone): 1.06×

Modest. Mode B's force-side mechanism is already capturing most of
the search-space restriction the stack hints would provide. The
extra 6% comes from the residual unit-propagation acceleration on
non-cascade clauses.

This is consistent with the F3 finding that the Mode A wall predictor
weakens as hints get stronger — once a strong baseline restriction
is in place (Mode B), additional hint information has diminishing
returns.

## Decision: don't ship as a default

The wrapper currently defaults to Mode A + de58-de59-stack. Adding a
Mode B + stack option would give 1.06× over Mode B (which is ~1.50×
over Mode A by project measurements; here single-cand it was 2.05×),
but Mode B has its own deployment caveats (force semantic restricts
the solution set, not just propagation). The 6% gain doesn't justify
adding another wrapper variant.

If a future caller knows they want Mode B AND wants to add the stack
hints, the wrapper supports that workflow already (`--mode force
--hint-mode de58-de59-stack`).

## What this confirms

- **Mode B and stack are independent propagation mechanisms.** They
  compose without contradiction even though both encode information
  about cascade-2 / cascade-1 differences.
- **The wrapper's `--mode force --hint-mode de58-de59-stack`
  combination is valid.** No code change needed; just calling
  convention.
- **Diminishing returns are real.** Past 2× speedup, marginal hints
  add ~5% rather than scaling.

EVIDENCE-level: SANITY (n=1 cand, 3 seeds). n=18 not pursued because
the single-cand 6% gain is below n=18 noise floor and below the
deployment-risk threshold for adding another wrapper variant.
