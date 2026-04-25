# Rule 4 firing — the modular-vs-XOR translation issue

## What I learned implementing the firing mechanism

Phase 2C primitives are all in place and tested:
- `partial_modular_sub` (14/14 tests)
- `partial_sigma0`, `partial_maj`, `partial_dSigma0_modular`, `partial_dMaj_modular_cascade` (12/12 tests)
- 1:many SAT-var lookup fix (44 partial-bit fires per 50k conflicts, max 30 bits)

The next step — **actually FORCING bits of dE[62] in the CNF** — runs into a fundamental domain mismatch between the propagator's reasoning and the encoder's aux variables.

## The mismatch

Theorem 4 (unified) is in the **MODULAR** domain:
```
da_r − de_r ≡ dT2_r  (mod 2^32)
```

The encoder's `aux_reg[(reg, r)]` variables are **XOR diffs**:
```
aux_reg[(e, 62)][i] = e1[62][i] XOR e2[62][i]
```

These two encodings differ by carry propagation:
```
modular_diff = sum over i of (xor_diff[i] * 2^i) - 2 * sum over i of carry[i] * 2^i
```

A propagator that computes "bit i of modular dE[62] = X" CANNOT directly force `aux_reg[(e, 62)][i] = X` — that would be unsound (the XOR bit might differ from the modular bit due to a carry from lower positions).

## What it would take to force soundly

Three options, increasing in complexity:

### Option A: Force actual register-value bits

The propagator's PartialReg state already tracks bit-level values of `e1[62]` and `e2[62]` (alongside `a1[62]`, `a2[62]`). When the partial-bit logic determines modular `dE[62] = N`, the propagator could force:

```
e1[62] = e2[62] + N (mod 2^32)
```

at the bit level — with carry-chain propagation through the actual SAT vars representing `e1[62]` and `e2[62]`. Each bit of one register's value is forced based on partial knowledge of the other + N's bits + carry chain.

**Reason clause** for forced bit i of e1[62]: all partial inputs that contributed to N's first i+1 bits + all bits 0..i of e2[62]. Could be 50-100 lits per forced bit.

This is **THE soundest, hardest implementation**. ~250 LOC. Equivalent to running a 32-bit adder/subtractor as a CDCL propagator.

### Option B: Force aux_reg XOR diffs ONLY in trivial cases

When modular `dE[62] = 0` (a special case), the XOR diff is also 0 (both register values equal). In that case, forcing `aux_reg[(e, 62)][i] = 0` for all i is sound.

When modular `dE[62]` has a known non-zero pattern, XOR diffs may differ due to carries — UNSOUND to force.

So Option B fires only when modular dE[62] = 0 (entire 32 bits). That's basically the same as Theorem 3's `dE[62] = 0` enforcement, which Mode B already does as unit clauses. **No new value over Mode B.**

### Option C: Modify the encoder to emit modular-diff aux variables

Add aux variables `mod_diff_e_62[i]` representing bit i of `(e1[62] - e2[62]) mod 2^32`, with ripple-carry adder clauses tying them to `e1[62][i]` and `e2[62][i]`.

Then the propagator can force `mod_diff_e_62[i] = N[i]` directly when partial logic determines the modular bit.

**Cost**: ~32 aux vars + ~96 ripple-carry clauses per (reg, round) pair × 4 (a, b, c, e at r=61, 62, 63 etc.). Total ~150 aux vars and ~450 clauses ADDED to the CNF.

**Benefit**: trivial propagator forcing. Reason clause is just the input + the new aux relationship.

## Recommendation

**Option A is the right end-state but is multi-day.** The propagator becomes a real modular-arithmetic CDCL aid.

**Option C is the engineering shortcut** — modify the encoder once to expose modular-diff aux. Each propagator firing is then a simple unit forcing on the new aux. Total complexity is balanced between encoder and propagator.

**Option B is empirically equivalent to Mode B** and adds no new value.

For the bet's value-add hypothesis (≥10× conflict reduction), either A or C is needed. C is faster to ship (~50 LOC encoder change + ~80 LOC propagator change ≈ 130 LOC total). A is more elegant but ~250+ LOC.

## What this hour's commits actually shipped

The breakthrough (commit `e814b3d`) is real: partial-bit Rule 4 r=62 firing IS feasible at scale. The diagnostic shows when and where the math primitives could fire.

The implementation gap is the FORCING mechanism — bridging modular-domain reasoning to XOR-domain CNF aux. This document captures the design choice for the next session.

## Decision deferred

Picking between Options A and C is a real architectural decision. Should be made by the implementer of the next phase (could be macbook or fleet worker). Both are valid; A is more general but slower; C is more pragmatic but requires encoder coupling.

**Recommendation: Option C (~130 LOC total)** for first ship. Then evaluate. If the modular aux approach gives 10× conflict reduction → Phase 2C-Rule4 ships. If not, Option A (more general) might still help, OR the bet's value-add hypothesis needs revisiting.

## Phase 2C-Rule4@r62/63 status (updated)

```
Substrate (bit tracking + backtrack)         ✓ shipped
Helpers (full-input evaluators)               ✓ shipped
Helper unit tests (14/14)                     ✓ shipped
Modular subtraction primitive (14/14)         ✓ shipped
Partial-bit evaluators (12/12)                ✓ shipped
1:many SAT-var lookup fix                     ✓ shipped
Partial-bit firing diagnostic (validates 44×) ✓ shipped
─────────────────────────────────────────────
DESIGN ISSUE (this doc): modular vs XOR forcing
NEXT: Option C — encoder emits modular-diff aux vars (~50 LOC encoder)
NEXT-NEXT: propagator forces those aux vars (~80 LOC)
```

The math primitives are done. The remaining ~130 LOC is encoder + propagator changes that are now well-specified.
