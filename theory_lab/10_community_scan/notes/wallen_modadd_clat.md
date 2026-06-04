# Note — Wallén: linear approximations of addition mod 2^n (the cLAT)

**Citations (see `../papers.bib`):**
- J. Wallén. *Linear Approximations of Addition Modulo 2^n.* FSE 2003 (LNCS 2887),
  pp. 261–273.
- Automatic ARX linear-hull search line: IACR ePrint
  [2019/1319](https://eprint.iacr.org/2019/1319) (applies Wallén's theory to SPECK /
  SPARX / Chaskey).

## Technique

- **Walsh/correlation theory of modular addition.** Wallén gives the exact correlation
  of an arbitrary *linear approximation* of `+ mod 2^n` (an input/output mask triple)
  using the Walsh–Hadamard transform of the addition function.
- **The combinational LAT (cLAT) is an automaton.** Because carry propagates low→high,
  the correlation factorizes bit-by-bit; Wallén packages this as a small finite-state
  machine (the cLAT) that reads the mask bits and emits the correlation magnitude
  (powers of `1/2`) — making correlations computable in **linear** time in the word
  width, and *enumerable* for trail search.
- **It plugs straight into automatic search.** The ePrint-2019/1319 line encodes the
  cLAT transitions into SAT/SMT/MILP to do automatic **linear-hull** search over ARX
  ciphers (SPECK, SPARX, Chaskey) — the linear-cryptanalysis analog of the MILP
  differential search used on SHA-2.

## Relevance to lab

Grounds **ANGLE 5 (Walsh / linear lens on the schedule + carry).** Precise transfer:
SHA-256's additions are `+ mod 2^32`; the cLAT gives, per adder, the correlation of any
linear mask through the carry — a per-bit *cost oracle* over the round function's modular
adders. In the lab this is at best a **trail-pruning / cost-estimation oracle**: a way to
score or prune candidate masks/difference templates by how well a *linear* relation
survives the carry, complementing the `xdp+` differential view (Lipmaa–Moriai).

The SHA-256 objects it maps to: the modular adders inside the round function
(`T1 = h + Σ1(e) + Ch + K + W`, `T2 = Σ0(a) + Maj`, and the state updates), as cLAT
automata.

## CAVEAT — construction vs. distinguishing (load-bearing, read this first)

**This machinery was built for key-recovery DISTINGUISHERS, not for CONSTRUCTING a single
collision.** Linear cryptanalysis turns a nonzero mask-correlation into an advantage that
is *amortized over many plaintext/ciphertext samples* — it tells you a bias exists across
a distribution. A collision is a **single witnessed pair** satisfying hard equalities; a
correlation of `2^{-c}` over the adder does not hand you a conforming pair, it only says a
*statistical* relation holds. So for this lab the cLAT can **rank/prune** difference or
mask templates (a cheap feasibility heuristic) but it **cannot, on its own, build or
certify a collision**, and any claim that "linear structure breaks the wall" would be a
category error. The honest expectation is, once more, explanatory-or-auxiliary: a useful
pruning oracle inside a trail search, not a standalone lever. Register-row gate: it earns
a row only as tooling *attached to* a concrete differential/structural angle, with a
kill criterion phrased as "cLAT-based pruning fails to change the feasible-template set."
