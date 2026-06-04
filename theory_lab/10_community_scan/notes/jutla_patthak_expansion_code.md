# Note — Jutla & Patthak: provably good code for SHA message expansion

**Citation (see `../papers.bib`):**
- C. S. Jutla, A. C. Patthak. *A Simple and Provably Good Code for SHA Message
  Expansion.* IACR ePrint [2005/247](https://eprint.iacr.org/2005/247), 2005. (Also
  circulated as *"Provably Good Codes for Hash Function Design."*)

## Technique

- **The message expansion is a linear code.** A round-reduced / linearized SHA message
  schedule maps the input words to the full sequence of expanded words via a linear
  generator matrix over `GF(2)`. A nonzero **schedule-compliant difference** is exactly a
  nonzero codeword; its **Hamming weight** is the number of active expanded words, which
  lower-bounds the cost of any differential collision through that schedule.
- **They built a computer-assisted MINIMUM-DISTANCE LOWER-BOUND tool.** The contribution
  is a technique to *prove* a lower bound on the minimum distance of such SHA-style
  expansion codes — not just observe weights, but bound them below with computer
  assistance. (The hard direction: upper-bounding min weight is "exhibit a light
  codeword"; *lower*-bounding it certifies that **no** light codeword exists.)
- **Concrete bounds (modified expansion).** For a disturbance-corrected/modified
  expansion they prove min distance **≥ 82** in the last 64 of the 80 expanded words,
  and **≥ 75** / **≥ 52** in the last 60 / 48 words respectively.
- **The SHA-1 slack they contrast against.** The ORIGINAL SHA-1 expansion code has min
  weight **≤ 44**, with only about **30** in the last 64 words — that sparsity is the
  gap the `2^69` SHA-1 differential attack exploited. The paper's point: closing that
  gap (provably) hardens the design.

## Relevance to lab

Grounds **ANGLE 2 (coding-theory min-distance bound on the schedule).** This is the
*most concretely falsifiable* adjacent angle in the catalog. Precise transfer: form
SHA-256's **linearized message-schedule generator matrix** (the 48 expansion equations
as `GF(2)`-linear recurrences, in the `sr` window of interest) and run a Jutla–Patthak-style
min-distance **lower bound** on it. The result directly bounds **how sparse any
schedule-compliant difference can be** in the last `k` words — i.e. it puts a provable
floor under the number of active words a single-block sr-attack must pay for, which is
exactly the quantity the project's `~2^{-2N}`-per-round wall is made of.

The SHA-256 object it maps to: the linearized schedule recurrence
`W[i] = σ1(W[i-2]) ⊕ W[i-7] ⊕ σ0(W[i-15]) ⊕ W[i-16]` as a generator matrix, restricted to
the enforced-`sr` rows.

**Skeptical framing:** a min-distance *lower bound* is a hardness statement — it most
plausibly **explains** the sr wall (proves no sparse compliant difference exists in the
enforced window) rather than enabling an attack; it could only *help* an attack if the
bound came out surprisingly **low** (a sparse compliant difference the trail-search line
hasn't been exploiting). Either way the computation is cheap and decisive, which is what
makes this a strong register candidate. Register-row gate / kill criterion: compute the
bound for SHA-256's schedule in the sr≈60–61 window; the angle is dead-as-an-attack (but
valuable-as-explanation) if the certified min distance is high, and live if it is
unexpectedly low.
