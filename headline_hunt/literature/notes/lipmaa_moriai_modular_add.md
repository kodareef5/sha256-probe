# Lipmaa & Moriai — Modular addition differential analysis (FSE 2001)

**Paper**: H. Lipmaa & S. Moriai, "Efficient Algorithms for Computing Differential Properties of Addition," FSE 2001.

**Why we care**: foundational for differential analysis of ARX (Add-Rotate-XOR) primitives. SHA-256 is ARX. Our unified Theorem 4 (`da_r − de_r ≡ dT2_r mod 2^32`) is a *modular*-domain differential statement — Lipmaa-Moriai is the rosetta stone for converting between modular differences and XOR differences, and for computing the probability of differential transitions through modular addition.

## Core definitions

For 32-bit words with modular addition:

- **Modular difference**: `dx = (x1 − x2) mod 2^32`
- **XOR difference**: `Δx = x1 ⊕ x2`

These are NOT equivalent. They're related through carry propagation:

```
x1 + y1 = (x1 ⊕ y1) + 2·carry(x1, y1)   (mod 2^32)
```

Where `carry(x1, y1)` is the carry chain that the modular adder produces.

## Key results (paraphrased)

### `xdp+(α, β → γ)` — XOR-differential probability through modular add

Given input differences α, β and output difference γ (all XOR), the probability that `(x ⊕ α) + (y ⊕ β) = (x + y) ⊕ γ` over uniformly-random `x, y` is:

```
xdp+(α, β → γ) = 2^{-w(eq(α<<1, β<<1, γ<<1) ∧ (α ⊕ β ⊕ γ ⊕ (β<<1)))}
```

(Hamming weight of a specific bitwise mask — see Theorem 2 in the paper.)

The condition for `xdp+ > 0` (compatibility):
- `eq(α<<1, β<<1, γ<<1) ∧ (α ⊕ β ⊕ γ ⊕ (β<<1)) = 0`

This gives a DAG of feasible XOR transitions through modular adders. Used in differential characteristic search (Wang-style).

### Modular differences are SIMPLER

For modular-domain analysis, the relation through addition is trivial: `(x1+y1) − (x2+y2) ≡ dx + dy (mod 2^32)`. Linear. No probability formula needed — it's deterministic.

This is why our unified Theorem 4 holds 100% in the modular domain: modular-add propagation is always linear, so the chain `T1 + T2`, `d + T1`, etc. propagates differences additively without carry-loss.

In the XOR domain (where the cascade_aux Mode B encoder lives), the same relation only holds approximately, and only with probability `xdp+`-style decay.

## Connection to our structural results

1. **Theorem 4 in the boundary-proof writeup states `dA[61] = dE[61]`**. The modular form (which holds 100% empirically) is `dA[61] − dE[61] ≡ 0 (mod 2^32)`. The XOR form (`Δa_61 = Δe_61`) holds only ~0.04% of the time — consistent with Lipmaa-Moriai: at r=61 the modular sum `dT1 + dT2` is zero, but the XOR pattern depends on the carry chain through the round function's modular adders.

2. **Unified Theorem 4 (`dA[r] − dE[r] = dT2_r` for r ∈ {61, 62, 63})**: this is a clean modular identity, not a probabilistic XOR transition. The Lipmaa-Moriai analysis says modular identities of this form are "free" — they reflect linear structure of mod-2^32 addition and incur no probability loss.

3. **Why the cascade_aux Mode B encoder works**: Mode B forces `dE[60] = 0` and `dE[61..63] = 0` AS XOR equalities (`eq_bits` clauses on each of 32 positions). At the cert (where dA[r]=dE[r]=0 always), modular-zero ⇒ XOR-zero trivially, so the encoding is sound. For non-collision pre-images, the XOR encoding is over-restrictive — but we don't care, because Mode B's purpose is to find collisions only.

4. **For the propagator (programmatic_sat_propagator bet)**: Rule 4 (unified Thm4 at r=62, r=63) needs to enforce a 32-bit modular identity. The reason clause connecting two register diffs through a modular sum requires Lipmaa-Moriai-style carry-chain reasoning, OR (cheaper) using the explicit aux variables for `dSigma0`, `dMaj`, `dT2_r` if exposed. Our varmap currently exposes register-diff vars but not these intermediate sums — could be a Phase 2C extension.

## Practical algorithms in the paper

- **`xdp+` evaluation**: O(n) bitwise computation for n-bit words (n=32 here).
- **Maximum xdp+**: given α, find γ maximizing `xdp+(α, α → γ)` — useful for trail design (Wang would care).
- **All compatible γ**: enumerate `{γ : xdp+(α, β → γ) > 0}` — useful for trail expansion.

These algorithms run in time linear in `2^{wt(α ∨ β)}` (Hamming weight of the union mask). For dense α, β this is exponential; for sparse (low-HW) it's fast. Wang-style trails specifically aim for low-HW input differences to keep this tractable.

## What this DOES NOT solve for us

- Lipmaa-Moriai is for SINGLE modular-add operations. SHA-256's compression function chains MANY (T1 = h + Sigma1(e) + Ch + K + W is a 5-input add, etc.). Each adder contributes its own xdp+ probability factor, and the trail's overall probability is the product. For ~64 rounds × multiple adders/round = ~256+ adders to thread.
- The modular-vs-XOR domain mismatch is exactly why Wang's SHA-1 trails work but generalize poorly to SHA-256: SHA-256 has more nonlinear ARX operations (Sigma0/Sigma1/Maj/Ch) than SHA-1's bitwise-Boolean f-functions.

## Action items
- [x] Confirm modular formulation of Theorem 4 is the natural form (done in our verification).
- [ ] **Future propagator work**: implement xdp+ computation in C++ alongside the cascade rules. Allows the propagator to refute trail extensions probabilistically without enumerating them.
- [ ] **Block2_wang trail-design**: when picking residual targets, use xdp+ to estimate cost-per-active-bit. The 4-d.o.f. residual variety has 128 free bits; xdp+ scoring would rank residual templates by trail-feasibility.
- [ ] Cite this paper in any writeup that talks about modular-vs-XOR distinction (currently: `bets/mitm_residue/results/20260425_*.md` writeups).

## Key takeaway (one sentence)

**Modular-domain differential analysis is linear and deterministic; XOR-domain analysis is probabilistic via `xdp+`. Our unified Theorem 4 lives in the modular domain by design — that's why it holds 100% — and translating it to XOR for CNF encoding requires careful soundness analysis (Mode B is sound for collision-finding, possibly over-restrictive for general queries).**
