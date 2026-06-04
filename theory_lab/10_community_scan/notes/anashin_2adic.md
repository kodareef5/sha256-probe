# Note — Anashin: non-Archimedean analysis, T-functions, 2-adic ergodic theory

**Citations (see `../papers.bib`):**
- V. Anashin. *Non-Archimedean Analysis, T-Functions, and Cryptography.*
  [arXiv:cs/0612038](https://arxiv.org/abs/cs/0612038) (2006).
- V. Anashin. *Non-Archimedean Ergodic Theory and Pseudorandom Generators.*
  [arXiv:0710.1418](https://arxiv.org/abs/0710.1418) (2007).

(Anchor for ANGLE 1, paired with the Klapper–Goresky FCSR note `klapper_goresky_fcsr.md`,
which supplies the complexity-measure / synthesis half of the same lens.)

## Technique

- **The carrier object is `Z_2`, the ring of 2-adic integers.** A machine word, and
  more usefully an *unbounded* bitstream, is a 2-adic integer; the 2-adic metric makes
  two integers "close" when they agree on many **low-order** bits. This is the natural
  metric for carry, which propagates low→high.
- **Processor ops are continuous on `Z_2`.** Addition, multiplication, XOR, AND, OR,
  and (with care) rotation/shift are all **1-Lipschitz** (non-expanding) maps on `Z_2`:
  the `k` low output bits depend only on the `k` low input bits. So an ARX round map is
  a continuous self-map of `Z_2` (or `Z_2^m`).
- **T-functions are exactly the triangular (carry-causal) maps.** A T-function's bit
  `i` of the output depends only on input bits `0..i` — i.e. it is 1-Lipschitz, and the
  whole SHA-style round function (ADD/ROT/XOR/maj/ch) is a T-function on `Z_2`.
- **Van der Put series + explicit ergodicity criteria.** Anashin expresses 1-Lipschitz
  maps in the van der Put (and Mahler) bases and gives *explicit, checkable* conditions
  on those coefficients for a map to be **measure-preserving** (bijective on residues
  at every depth) or **ergodic** (single-orbit transitive). This converts "does this
  carry map mix the state" into a coefficient computation rather than a simulation.
- **Why carry is the whole story here.** All the *linear* parts (XOR, rotation, shift)
  are isometries/affine on `Z_2`; the only thing that creates genuine non-Archimedean
  structure — the only source of cross-bit coupling — is **carry from addition**. The
  framework puts that coupling, and nothing else, under a microscope.

## Relevance to lab

Grounds **ANGLE 1 (2-adic / FCSR metric on the carry obstruction).** Precise transfer:
model SHA-256's compression/round map as a 1-Lipschitz T-function on `Z_2^8` (the eight
state words, or a chosen reduction), and use the van der Put / measure-preservation
machinery to ask whether the **cascade / schedule-compliance wall** is a
measure-preservation or ergodicity obstruction — i.e. whether the carry map's structure
*forces* the `~2^{-2N}` per-round cost the project measures, rather than it being a
search artifact. The SHA-256 objects it maps to: the round function as a self-map of
`Z_2^8`, and the message-schedule recurrence as a 1-Lipschitz map on the expanded-word
stream.

**Skeptical framing (load-bearing):** this is a *characterization* lens, not an attack.
The most likely outcome is that it gives a clean reason the wall holds (the carry map is
measure-preserving / ergodic at the relevant depth), which would *strengthen*, not break,
the sr=60 ceiling. It earns a register row only if a cheap small-`N` probe can compute a
van der Put / measure-preservation quantity that is **predictive** of the observed
per-round difficulty — that is the kill criterion to write.
