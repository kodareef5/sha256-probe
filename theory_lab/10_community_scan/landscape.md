# The 2026 SHA-2 collision frontier — and where this project cuts differently

_Community scan for the SHA-256 Theory Lab. Bibliographic facts cross-checked against
the working repo's curated registry (`../../sha256_review/headline_hunt/registry/literature.yaml`)
where the two overlap; per-paper detail lives in `notes/`. Full keys in `papers.bib`._

## Where the records stand

Full SHA-256 remains **unbroken** against both collision and preimage attacks. All
recent progress is on **reduced-round** variants, and the relevant axis for the
mainstream is *how many of the 64 round-steps* an attack can cover.

- **Practical full collisions: 31 steps.** Li, Liu, Wang, Dong and Sun gave the
  *first practical* (real colliding message pair, not just a characteristic)
  31-step SHA-256 collision at ASIACRYPT 2024 (best paper), via a memory-efficient
  full-collision search on top of the EUROCRYPT 2024 machinery
  ([Li–Liu–Wang, ePrint 2024/349](https://eprint.iacr.org/2024/349)).
- **Semi-free-start (SFS) collisions: 39 steps.** The same EUROCRYPT 2024 work
  pushed SFS — where the attacker also controls the chaining input — to 39 steps,
  beating the 38-step SFS record that Mendel–Nad–Schläffer had held since 2013.
- **Reduced-round practical frontier: ~37 steps.** Zhang, Li, Gao and Wang
  ([ePrint 2026/232](https://eprint.iacr.org/2026/232)) extend the practical line to
  37 steps by *automating* the discovery of high-quality local collisions in the
  message expansion — historically the manual bottleneck of the Mendel–Nad–Schläffer
  approach.

These broke records that had stood for roughly a decade. The throughline is a single
**toolchain**.

## The dominant toolchain: MILP + SAT/SMT + CAS + message modification

Modern SHA-2 collision search is an automated-reasoning pipeline:

1. **Differential-characteristic search**, classically via generalized/signed bit
   conditions (De Cannière–Rechberger automated search; Mendel–Nad–Schläffer's
   signed-DC specialization to SHA-256), now front-ended by **MILP** to escape the
   heuristic plateau that stalled longer trails ([Li–Liu–Wang 2024](https://eprint.iacr.org/2024/349)).
2. **SAT/SMT back-end** to realize the characteristic and find conforming messages.
3. **Computer-algebra augmentation (SAT+CAS).** Alamgir, Nejati and Bright
   ([arXiv:2406.20072](https://arxiv.org/abs/2406.20072)) drive a CDCL solver with a
   computer-algebra system through the **IPASIR-UP** user-propagator interface
   (CaDiCaL), letting the CAS spot inconsistencies the solver would miss; they reach a
   38-step modified-IV collision where pure SAT reaches only 28. *(Worth flagging
   internally: the working repo already built and evaluated a cascade-aware
   IPASIR-UP propagator and closed it as marginal vs. a clean Mode-B CNF encoding —
   so "add a propagator" is not, by itself, the lever here.)*
4. **Message modification** (Wang-style local correction) to satisfy the bit
   conditions implied by the characteristic.

The ARX-probability substrate underneath all of this is classical: Lipmaa–Moriai's
`xdp+` for differential probability through modular addition, and Mouha et al.'s
S-function framework that made ARX trails MILP-encodable.

## The quantum sub-line (new)

A distinct 2025/2026 thread asks what *quantum* search buys over reduced rounds. Zhou,
Sun, Zhang et al., *"Quantum collision attacks on reduced SHA-256"* (Quantum
Information Processing, vol. 25, art. 2, 2026;
[DOI 10.1007/s11128-025-05024-w](https://doi.org/10.1007/s11128-025-05024-w)), take the
classical 39-step SFS collision and convert it into a **two-block full collision** via
a quantum framework, reporting time `t = 2^124/√S` on a size-`S` quantum machine. This
is still a reduced-round result riding on the classical characteristic; it is new to
this lab's catalog and worth tracking, but it does not change the unbroken status of
full SHA-256.

## How this project cuts differently: the schedule-compliance (sr) axis

The mainstream parameterizes "reduced SHA-256" by **round count** `R < 64` at *full*
message-schedule compliance. This project (following Viragh 2026,
`../../sha256_review/reference/paper.pdf`) parameterizes the *orthogonal* knob:
**keep all 64 rounds**, but progressively enforce the 48 message-expansion equations,
counting how many hold (the **`sr` level**). Viragh reached **sr=59**; this project
independently reproduced sr=59 and pushed to a verified **sr=60** full-width
semi-free-start certificate; **sr=61 is the open wall**.

The two axes are not directly comparable — they reduce different things — but the gap
framing is stark in each metric: the round-count line sits ~23–25 steps short of 64,
while the sr line sits **4 schedule equations** short of full compliance at 64 rounds.
The project's own analysis argues each further enforced round costs `~2^{-2N}` (two
independent N-bit conditions), making single-block sr=61 effectively unreachable and
motivating the multi-block (Wang-style absorption) pivot in `headline_hunt/`. The point
for *this lab* is methodological: the sr axis isolates the **message-schedule /
carry obstruction** as the thing that resists, rather than burying it inside a
round-count trade-off — which is exactly the seam the adjacent-field angles try to pry.

## Gaps the mainstream is NOT working

The entire frontier above lives inside one paradigm: *signed-differential trail search,
MILP-pruned, SAT/CAS-realized, message-modified.* Several adjacent-field lenses are, as
far as this scan found, **untouched** against SHA-256's schedule/carry structure:

- **No 2-adic metric on the carry obstruction.** Carry is universally acknowledged as
  the crux — Klapper–Goresky even pin FCSR-complexity growth on "the carry from
  addition of integers" — yet nobody puts Anashin's 1-Lipschitz / van der Put
  machinery on `Z_2` onto SHA-256's round map to ask whether the cascade wall is a
  *measure-preservation* obstruction. (Most plausible outcome: it **explains** the
  wall, doesn't break it. Worth knowing which.)
- **No expansion-code min-distance bound computed for SHA-256 specifically.**
  Jutla–Patthak built the computer-assisted tool that lower-bounds the minimum distance
  of SHA-style linear expansion codes (and used it on SHA-1, whose slack — min weight
  ≤44 — enabled the `2^69` attack). Pointing that exact tool at SHA-256's linearized
  schedule generator matrix would lower-bound how *sparse* any schedule-compliant
  difference can be — directly relevant to the sr wall — but the scan found no such
  computation published.
- **Lattice carry-lifting is unexplored.** Treating the carry/schedule constraints as
  a lattice problem (Hensel/2-adic lifting of mod-`2^k` solutions) to search or bound
  schedule-compliant differences appears entirely absent for SHA-256.

These gaps are *reframings*, not attacks. The honest prior is that each one most
plausibly **characterizes why the wall holds**; the value is that none has been ruled
out yet, and each maps to a concrete SHA-256 object (the round map on `Z_2`, the
expansion generator matrix, the carry lattice) that a cheap probe could test.
