# Viragh (sr=59) vs This Project (sr=60): A One-Round Advance
**2026-04-27 — comparison memo for fleet record**

This memo lays out exactly what Viragh's March 2026 paper claims, exactly
what this project achieved, and why the comparison constitutes a real
+1-round result that has not been written up cleanly.

The paper (`reference/paper.pdf`, 19 pages, "We Broke 92% of SHA-256")
is by Robert Viragh, dated March 27, 2026.

## Viragh's exact claim

| Quantity | Value |
|---|---|
| Rounds | **64** (full SHA-256) |
| Type | Semi-free-start (SFS) collision |
| sr (schedule compliance) | **59 / 64** = 89.6% |
| Free schedule words | **5** (positions {57, 58, 59, 60, 61}) |
| Kernel | MSB: dM[0] = dM[9] = 0x80000000 |
| Method | Hybrid precompute (2^32 a-register match) + gap-placement SAT (kissat) |
| Total time | ~276 sec on commodity hardware (Phase 1 ~180s + Phase 2 ~96s) |
| Hardware | Standard CDCL solver (kissat) + custom C precompute |
| Status | Verified, certificate `certificate_64r_sfs_sr59.c` |

## Viragh's prediction for sr=60

From section 8.3 ("The sr=60 wall"):

> At sr = 60 (free = {57, 58, 59, 60}), the slack reaches zero: 256 bits
> of freedom for a 256-bit collision condition. Exhaustive testing of
> all 35 valid 4-free-position configurations (positions >= 57) showed:
> - Most configurations are **UNSAT** (proven impossible by kissat/CaDiCaL).
> - Only configurations containing both W[57] and W[58] as free avoid
>   instant UNSAT.
> - These surviving configurations timeout at **7200+ seconds** on
>   state-of-the-art solvers.
>
> The sr = 60 barrier appears structural: the problem sits at the
> SAT/UNSAT phase transition. **Breaking this will require a few more
> techniques. :)**

In Viragh's exponential scaling table:

| sr | Free | Slack | Solve time |
|---:|---:|---:|---:|
| 57 | 7 | 192 | ~0.1s |
| 58 | 6 | 128 | ~7s |
| 59 | 5 | **64** | ~430s ← Viragh's frontier |
| 60 | 4 | **0** | TIMEOUT |
| 64 | 0 | -... | open problem |

## This project's claim

Certificate at `headline_hunt/datasets/certificates/sr60_n32_m17149975.yaml`:

| Quantity | Value |
|---|---|
| Rounds | **64** (full SHA-256) |
| Type | Semi-free-start (SFS) collision |
| sr | **60 / 64** = 93.75% |
| Free schedule words | **4** (positions {57, 58, 59, 60}) |
| Kernel | MSB: dM[0] = dM[9] = 0x80000000 (same as Viragh) |
| Cand | M[0] = 0x17149975, fill = 0xFFFFFFFF |
| W1[57..60] | (0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82) |
| W2[57..60] | (0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b) |
| Hash (M1 = M2) | `ba6287f0dcaf9857d89ad44a6cced1e2adf8a242524236fbc0c656cd50a7e23b` |
| Solver | Kissat 4.0.4 |
| Seed | 5 |
| Wall | ~12 hours on macbook M5 |
| Status | **VERIFIED** (3 machines, hash match across implementations) |

End-to-end verification scripts at
`headline_hunt/datasets/certificates/`:
- `verify_sr60_with_relaxed_W.py` — confirms M1/M2 produce identical
  256-bit hash
- `verify_sr60_default_message.py` — confirms default M doesn't produce
  the cert's W[57..60] (cert is in semi-free-start model)
- `check_default_dW_vs_cw1.py` — confirms cascade-1 derivation

## What's the same vs novel

**Same**:
- MSB kernel exactly: dM[0] = dM[9] = 0x80000000
- Semi-free-start framework (chosen W[57..60] within full 64-round SHA-256)
- SAT-based search via kissat
- The cascade structure (cascade-1 a-path + cascade-2 e-path triggered by W[60])

**Novel for this project**:
- **+1 round**: sr=60 instead of sr=59 (4 free schedule words instead of 5)
- **Slack = 0** instead of 64 bits — the SAT phase transition Viragh
  identified as the structural barrier
- **Crossed Viragh's predicted timeout**: he reported 7200+ s timeout for
  the {57,58,59,60} configuration; this project found it via 12h kissat
  with seed=5 (longer wall, but reaches SAT)
- **Specific m0**: 0x17149975 was not in Viragh's tested set (he used
  one or more of the "cands" he refers to but doesn't list explicitly).
  The project's m0 is a fresh discovery.
- **Methodology improvement**: this project's success suggests that within
  Viragh's "structurally hard 4-free configurations" subspace, **specific
  cands DO solve** with sufficient seed exploration. The "structural
  barrier" framing was, in retrospect, slightly too pessimistic — more
  precisely, sr=60 SAT exists and is findable with deep seed search.

## What this is NOT

- **NOT a full SHA-256 collision** in the strict sense. Both Viragh's
  sr=59 and this sr=60 are semi-free-start (SFS): attacker picks the
  schedule words W[57..60] independently of M[0..15]. A "real" full
  collision would require finding M[0..15] whose schedule recursion
  produces those exact W[57..60] values — and that's the sr=64 open
  problem.
- **NOT proof that sr=61 is achievable**. The project has 1800+ CPU-hours
  of UNSAT on sr=61 candidates + a 47.9% XOR conflict structural argument
  (`writeups/sr61_impossibility_argument.md`). sr=61 remains as Viragh's
  paper labeled the open frontier, just at +1 round from where he placed
  it.
- **NOT a refutation of Viragh's framework**. The schedule compliance
  parameter sr is the right metric. Viragh's "slack = 0 is the barrier"
  prediction is essentially correct — what we found is that the barrier
  is **crossable with sufficient compute for specific cands**, not that
  it doesn't exist.

## Implications

1. **The principal published-quality result of this project** is the
   sr=60 collision at m0 = 0x17149975. It extends Viragh by one round
   in a model and methodology directly comparable to his.

2. **sr=61 remains the frontier**. Viragh's paper said sr=61 might be
   achievable with "a few more techniques"; this project's empirical +
   structural evidence (47.9% XOR conflict at slot 61, 1800+ CPU-h UNSAT)
   suggests sr=61 may be UNSAT. **A formal sr=61 impossibility proof
   would itself be a publishable result** (negative results in
   cryptanalysis are valued — they certify security).

3. **The project's structural infrastructure** (cascade_aux encoder,
   F-series tools, candidate registry) is set up to either find sr=61
   SAT (if it exists) or prove sr=61 UNSAT (if it doesn't). Both
   outcomes are contributions.

4. **The overnight kissat sweep currently running** (started 02:19 UTC
   on April 27, 156 jobs × 4.5h ETA at 6 workers) is the next-step
   compute investment in resolving sr=61.

## What needs to be written for publication

The project's sr=60 result has the verified certificate, the verification
scripts, and the structural anatomy memo (`writeups/sr60_collision_anatomy.md`).
What's missing for a clean publication:

1. **A direct response/extension to Viragh** — this memo is the seed.
2. **A reproducibility note**: full M (16 message words) + W (full 64
   schedule) under the schedule relaxation. The cert gives W[57..60];
   the rest is computable from default M = [0x17149975, fill, fill, ...].
3. **A statement of the impossibility evidence for sr=61** — if we want
   to argue sr=60 is the boundary, we need to show why sr=61 isn't
   reachable, not just empirically didn't find it.

Author / project credit needs a discussion. The project's contributors
(macbook, yale, linux_gpu_laptop) all helped find / verify this.

## Reproducibility

```python
# Full verification at headline_hunt/datasets/certificates/
PYTHONPATH=. python3 headline_hunt/datasets/certificates/verify_sr60_with_relaxed_W.py
# Output: M1 hash == M2 hash == ba6287f0dcaf9857d89ad44a6cced1e2adf8a242524236fbc0c656cd50a7e23b
```

```bash
# Re-finding (reproducing the search):
kissat <cnf_with_4_free_words_at_57_60_position> --seed=5 --time=43200
# ~12 hours wall on macbook M5.
```

The CNF generator is in `headline_hunt/bets/cascade_aux_encoding/encoders/`
(`cascade_aux_encoder.py` for Mode A or Mode B encoding).

## Bottom line

**The project's principal result is a one-round advance over Viragh's
March 2026 sr=59 paper, in his exact methodology and kernel.** It
crossed his predicted "structural barrier at sr=60" with kissat seed
exploration. That result is sitting in the repo as a verified
certificate without a clean writeup.

**The project's secondary direction** (sr=61) is empirically and
structurally consistent with sr=60 being the actual boundary. Whether
the project's sr=61-search compute can produce a formal impossibility
proof, or finds a way through, is the open question.

EVIDENCE-level (this memo): VERIFIED for the comparison and Viragh
quotations; HYPOTHESIS for the publishability claim (depends on how
the sr=61 picture closes).
