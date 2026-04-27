# Wang / Yin / Yu 2005 — Finding Collisions in the Full SHA-1

**Cite as**: Wang, X., Yin, Y.L., Yu, H. *"Finding Collisions in the Full SHA-1."*
CRYPTO 2005. DOI: 10.1007/11535218_2.

**Read status**: structural-summary from public knowledge + Viragh 2026
literature table reference. Foundational paper for hash-function
cryptanalysis — paradigm-defining work. Full PDF read pending.

## Position in the literature

Wang/Yin/Yu 2005 is **THE foundational paper** for differential
cryptanalysis of hash functions in the modern era. Together with
Wang/Yu 2005 ("How to Break MD5 and Other Hash Functions" — same
group, different paper) and Wang's 2004 work on MD5/HAVAL/RIPEMD, it
established:

1. **The two-message message-modification (MM) framework**: instead of
   searching one message at random, the attacker maintains TWO messages
   M₁ and M₂ with a chosen difference δM, then iteratively modifies M₁
   to satisfy "bitconditions" implied by a chosen DIFFERENTIAL
   CHARACTERISTIC.

2. **The single-block + multi-block attack distinction**: for SHA-1,
   Wang's attack used 2 blocks (each 512 bits). The first block
   produces an intermediate residual; the second block absorbs it via
   its own differential trail.

3. **The differential characteristic + message modification combo**:
   characteristic specifies "WHICH bits differ between M₁ and M₂ at
   each round"; message modification fixes M₁ to satisfy the
   characteristic's bitconditions. This is the core technique block2_wang
   inherits.

For SHA-1 specifically, Wang/Yin/Yu 2005 reduced the collision
complexity from 2^80 (birthday) to ≈ 2^69. Subsequent work
(Manuel 2008, Stevens 2017) reduced further; Stevens et al. 2017
"The First Collision for Full SHA-1" (CRYPTO 2017) achieved an
explicit collision via shattered.io.

## Why this is foundational for block2_wang

The block2_wang bet is named after Wang's 2-block attack. Specifically:

- **Block 1**: produces a low-HW residual at the end of round 63 (the
  state difference between M₁ and M₂'s compression-function outputs).
  In our project's framework, this is the F17/F25 residual analysis.
- **Block 2**: absorbs the residual via a SECOND differential trail
  on a SECOND 512-bit block. The second-block message words are
  modified to cancel the residual.

Wang's key insight: the second block's differential trail can be
chosen to specifically cancel the first block's residual structure.
This is what F26's "a_61 = e_61 symmetry" enables for bit13_m4e560940
— the residual has structure that may admit shorter second-block
absorption.

## Methodology summary (from public references)

### Bitconditions and characteristics

A "differential characteristic" specifies, for each round r, the
CHANGE pattern between M₁ and M₂ at the level of:
- State register diffs (a, b, c, d, e, f, g, h)
- Schedule word diffs (W[r])

A characteristic at round r is denoted by signed bits {+, −, x, ?, …}
where:
- '+' means M₁ has 0, M₂ has 1
- '−' means M₁ has 1, M₂ has 0
- 'x' means free / either
- '?' means determined-yet-unknown

### Message modification

For rounds 0..15, the attacker has 16 free message words (512 bits).
Each round's bitconditions constrain some bits. Modification proceeds
iteratively:
- Pick a target bit-condition violated by current M₁
- Find a small set of M₁ bits to flip that propagates correctly
  through earlier rounds and resolves the violation
- Iterate until all early-round bitconditions are satisfied

For rounds 16+, the schedule recurrence determines W[r] from W[r-2],
W[r-7], W[r-15], W[r-16]. Modification at this stage must respect
the schedule constraint — analogous to Viragh's "schedule compliance"
metric in 2026.

### Multi-block strategy

Block 1: differential trail leaves a state-difference at output. The
trail is chosen so that the residual has STRUCTURE (low HW, specific
bit positions).

Block 2: a SECOND differential trail starts from the residual and
ends at zero. The second-block trail is "absorbed" by the second-
block message words.

Total cost: probability of trail × difficulty of message modification.

## Connection to this project's sr=60 result

Viragh 2026 + this project use a DIFFERENT framework:
- Wang/Yin/Yu: REDUCED-ROUND attacks with FULL schedule
- Viragh + this project: FULL ROUNDS with REDUCED schedule

Both are SFS (semi-free-start) collisions. But the relaxation axis is
different. Wang's approach scales to full SHA-1 (80 rounds) at 2^69
complexity; this project's approach extends to sr=60 / 64 rounds.

The sr=61 frontier we're hunting is the schedule-axis equivalent of
Stevens 2017's "first SHA-1 collision" — reducing the relaxation in a
known-effective attack to zero.

## Specific techniques worth borrowing

For block2_wang's eventual implementation:

1. **Bitcondition formalism**: encode the F-series residual structure
   in Wang's bitcondition vocabulary. Each min-HW residual position
   (a_61, e_61, etc.) becomes a bitcondition.

2. **Two-trail composition**: design a second-block trail starting
   from a F25/F26 residual and ending at zero. The F26 a_61=e_61
   symmetry suggests a shared-bit cancellation strategy.

3. **Probability bounds**: each absorbed bit has a probability cost.
   For HW=47 (bit13), a naive Wang bound is ~2^-47. Our 256-bit
   freedom in second-block message words = 2^-47 / 2^-256 = 2^209
   expected solutions. Plenty IF the trail is achievable.

4. **Validity / conditions on M_2**: Wang's modification framework
   handles the message-modification cost. block2_wang would need
   a similar engine for SHA-256.

## Action items for paper integration

1. **Section 2 (Background)**: cite Wang/Yin/Yu 2005 as the origin of
   the message-modification methodology. block2_wang inherits this
   directly.

2. **Section 5.5 (yale's guarded fiber)**: cite Wang's bitcondition
   formalism — yale's "guarded message-space probe" is a modern
   reformulation of Wang's "satisfy bitconditions via M modifications."

3. **Section 7 (Discussion)**: note the framework duality:
   - Wang line: reduced-round full schedule
   - Viragh line: full rounds reduced schedule
   - **Both converge to sr=64, R=64 = full SHA-256 collision** (open).

## Action items for the project (concrete)

1. **For block2_wang**: implement a bit-pattern absorption engine
   for SHA-256's second block. Input: F25 residual (e.g., bit13's
   HW=47 specific pattern). Output: Wang-style bitcondition set + M₂
   message modifications.

2. **For yale's guarded probe**: translate findings into bitcondition
   notation. yale's HW=8 "guarded prefix" is a Wang-style
   bitcondition cost — quantitatively comparable to Wang 2005's
   ~80-condition characteristic costs.

3. **Cross-reference**: enumerate the project's 9 exact-symmetry cands
   (F27) under Wang's bitcondition framework. Compare to known
   SHA-256-like differential characteristics.

## Status

- Read status: STRUCTURAL_SUMMARY based on public-knowledge of Wang's
  2005 work and the project's existing references. Full PDF read
  PENDING.
- This note unblocks the "Wang/Yin/Yu" item from literature.yaml
  should_read list.

EVIDENCE-level: HYPOTHESIS — based on indirect references and standard
cryptanalysis knowledge. Direct PDF study would harden specific
technical claims about the 2005 SHA-1 attack methodology.
