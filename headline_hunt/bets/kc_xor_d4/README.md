# bet: kc_xor_d4 — d4 with XOR-preserving preprocessing

**Priority 3** per GPT-5.5.

## The bet

`d4 on N=8 standard CNF: >67h, no completion (treewidth ~110 barrier).` That's the
closed result. But d4 was never tried with **XOR-preserving preprocessing** that
preserves the linear structure inside the cascade encoding.

If the cascade has more linear (XOR) structure than the standard CNF expression
exposes, a Bosphorus-style XOR recovery pass could produce a CNF that decomposes
better — possibly enough to push d4 through the ceiling at N=16.

## Hypothesis

The polynomial BDD result (O(N^4.8)) implies a polynomial d-DNNF representation
exists. d4's failure to find it is a *vtree/decomposition* failure, not a
representation failure. XOR preprocessing changes the decomposition.

## Headline if it works

> "Constructive d-DNNF compilation of N=16+ collision object — first non-search
> route to a SHA-256 collision-class object."

That would settle the polynomial-BDD-paradox in the constructive direction.

## What's built / TODO

- [ ] Build Bosphorus or wire CryptoMiniSat's XOR recovery to standard CNF.
- [ ] Run XOR preprocessor on N=8 standard cascade CNF; measure clause/variable change.
- [ ] Feed XOR-recovered CNF to d4 with FlowCutter tree decomposition.
- [ ] Measure component-cache hit rate as the early signal (if cache hits stay flat
  through the run, no decomposition improvement is happening).
- [ ] If N=8 completes, push to N=12 and N=16.

## How to join

1. Set `d4_xor_preprocessing.owner` in `mechanisms.yaml`.
2. Coordinate with `cascade_aux_encoding` owner — try BOTH the standard CNF + XOR
   prep AND the cascade-aux CNF + XOR prep. Two encodings × XOR = 4 d4 conditions.
3. Use existing d4 build in `infra/drat-trim/` adjacent toolchain (per CLAUDE.md).

## Related

- Pairs with `cascade_aux_encoding` (different encoding inputs).
- Tests the `bottom_up_sdd_blowup` reopen criterion.
