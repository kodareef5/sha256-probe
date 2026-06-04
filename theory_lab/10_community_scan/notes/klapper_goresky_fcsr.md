# Note — Klapper & Goresky: FCSRs, 2-adic span, rational approximation

**Citations (see `../papers.bib`):**
- A. Klapper, M. Goresky. *Feedback Shift Registers, 2-Adic Span, and Combiners with
  Memory.* Journal of Cryptology 10(2):111–147, 1997.
- A. Klapper, M. Goresky. *Cryptanalysis Based on 2-Adic Rational Approximation.*
  CRYPTO '95 (LNCS 963), pp. 262–273.

(Anchor for ANGLE 1, paired with `anashin_2adic.md` which supplies the analysis/ergodic
half of the same lens.)

## Technique

- **FCSR = arithmetic analog of the LFSR.** A Feedback-with-Carry Shift Register is an
  LFSR whose feedback adds *with carry* (a small memory register holds the carry). Its
  output sequence is exactly the bit-expansion of a **2-adic rational** `p/q`, just as
  an LFSR sequence is a linear-feedback / rational-over-`GF(2)` sequence.
- **2-adic span = a complexity measure.** The size of the smallest FCSR generating a
  given sequence is its **2-adic span** (governed by `|q|`), the carry-aware counterpart
  of linear complexity. Small 2-adic span ⇒ predictable/weak, even when linear
  complexity is large.
- **A synthesis algorithm exists (2-adic Berlekamp–Massey).** Given enough output, a
  *rational-approximation* algorithm reconstructs the smallest FCSR (the `p/q`)
  producing it — the exact analog of Berlekamp–Massey for LFSRs. This is what makes the
  span a *computable* attack surface, not just a definition.
- **Carry is the crux — explicitly.** The literature flags that when you **combine**
  rational approximations, the representation can grow in size *"due to the carry from
  addition of integers."* That sentence is the whole reason this lens is interesting for
  SHA-256: carry is precisely SHA's nonlinearity, and here it is named as the thing that
  inflates 2-adic complexity.

## Relevance to lab

Grounds **ANGLE 1 (2-adic / FCSR metric on the carry obstruction)** — the *complexity /
synthesis* half. Precise transfer: treat the cascade-induced internal sequences (e.g. the
per-round carry chain, or the message-schedule output stream) as candidate 2-adic
sequences and ask whether a **2-adic-span / rational-approximation** measure of the
schedule-compliance constraint is large — i.e. whether the carry obstruction is "2-adically
deep." A *large* span is the quantitative form of "carry resists," and would put a number
on the qualitative wall the project sees. SHA-256 object it maps to: the carry register
of the round-function adders and the message-expansion output sequence, read as 2-adic
rationals.

**Skeptical framing:** FCSR/2-adic-span theory is built to *measure predictability of a
keystream* and to synthesize a generator, not to *construct a collision*. The honest
expectation is again explanatory: a high 2-adic span would **quantify** why
schedule-compliant differences are hard to keep sparse, characterizing the wall rather
than passing through it. Register-row gate: a small-`N` computation where a 2-adic-span /
rational-approximation quantity tracks the measured per-round `2^{-2N}` cost.
