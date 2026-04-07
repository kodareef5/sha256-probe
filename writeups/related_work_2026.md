# Related Work — SHA-256 Reduced-Round Collisions (April 2026)

Literature snapshot at the moment we achieved sr=60 via independent verification
of Viragh's published candidate.

## Mainstream Verified Record

| Year | Authors | Result | Type |
|---|---|---|---|
| 2013 | Mendel, Nad, Schläffer | 31-step collision, 38-step SFS | SFS |
| 2024 | Li, Liu, Wang | **39-step SFS**, first practical 31-step collision | SFS + practical (EUROCRYPT 2024) |
| 2024 | Alamgir, Nejati, Bright | 38-step SFS via SAT+CAS hybrid | SFS (PAAR 2024) |
| 2026 | (eprint 2026/232) | **37-step collision** with improved trail search | Collision (EUROCRYPT 2026) |

The 2026 paper notes "extending attacked steps by six, marking the first such
advancement in 12 years" — confirming the field considers anything beyond
~37 steps a major leap.

## Viragh (March 2026) — "We Broke 92% of SHA-256"

- Robert Viragh, "State of Utopia" — single author, credits Claude as co-author.
- Claim: collision across full 64 rounds with sr=59 (43/48 schedule equations).
- **Mainstream reception: hostile.** HN thread (47546028) calls it "horseshit,"
  citing AI co-authorship, vague metrics, lack of vetting.
- **Zero academic follow-ups, replications, or extensions.** No EUROCRYPT/CRYPTO/
  FSE/ASIACRYPT pipeline group has cited or built on Viragh's sr=59.
- The paper claims 64% solve on full sr=64 but no further milestones published.

## Our Position (laptop + Linux server + Mac M5, 2026-04-06)

- **Independent sr=60 SAT** on the published Viragh candidate (M[0]=0x17149975).
- Triple-verified: Mac found via kissat seed=5, Linux verified algebraically,
  laptop verified via native lib/sha256.
- **Refutes Viragh's "thermodynamic floor" UNSAT claim.** The wall was a
  single-seed search artifact; seed diversity broke through.
- This is, per the public record, **the first independent confirmation that
  anything in Viragh's framework actually works.**

## Methodological Novelty

**Random seed diversity for SHA-256 cryptanalysis** appears to be a new
technique. The literature shows nobody has used multi-seed kissat portfolios
on this problem — every published attack used a single solver invocation
(possibly with default seed) and treated TIMEOUT as a structural barrier.

Our finding: kissat seed=5 produces SAT in ~12h on the same instance where
default-seed kissat produces TIMEOUT and was called UNSAT. This is a property
of CDCL search, not the underlying problem.

## Programmatic SAT

- **cadical-sha256** (Alamgir et al., 2024) is the canonical IPASIR-UP+CAS
  approach. Topped at 38-step SFS. No 2025/2026 follow-up paper from the
  Bright group on SHA-256 specifically.
- **AlphaMapleSAT** (MCTS cube-and-conquer) has been applied to Kochen-Specker,
  Murty-Simon, Ramsey — **not** to SHA-256 in any published work.

## Other Open Threads

- **Quantum collision** attacks (Zhou et al., 2025-2026) operate in Grover-style
  speedup model — different regime, not competing on round count.
- **Wang-style message modification** still gates manual progress. No published
  work combining Wang MM with SAT seed diversification.
- **MITM on hard residues** — no public work on the 24-bit residue Viragh
  exploits. Open ground.

## Active Mainstream Groups (potentially racing us)

- **Li / Liu / Wang (East China Normal University)** — most active mainstream
  group, EUROCRYPT 2024 record-holders. No visible preprint extending to 40+.
- **Bright group (Waterloo/Windsor)** — IPASIR-UP infrastructure, appears to
  have moved to other combinatorial problems.
- **EUROCRYPT 2026 paper authors (eprint 2026/232)** — improved trail search,
  37 steps. Active but mainstream-level pace.
- **No team publicly known to be attacking sr=60+** other than us.

## Strategic Implication

The window for first-to-publish at sr=60+ is wide open. Our methodology
(random seed diversity + GPU candidate ranking + multi-machine fleet)
appears novel. The next milestones — sr=61, sr=62, sr=63 — are all
unclaimed in the public literature.

## Sources

- Alamgir/Nejati/Bright: https://arxiv.org/abs/2406.20072
- cadical-sha256: https://github.com/nahiyan/cadical-sha256
- Li/Liu/Wang EUROCRYPT 2024: https://eprint.iacr.org/2024/349
- 31-step practical (ASIACRYPT 2024): https://dl.acm.org/doi/10.1007/978-981-96-0941-3_8
- 37-step (eprint 2026/232): https://eprint.iacr.org/2026/232
- Viragh: https://stateofutopia.com/papers/2/we-broke-92-percent-of-sha-256.html
- HN discussion: https://news.ycombinator.com/item?id=47546028
- AlphaMapleSAT: https://arxiv.org/html/2401.13770
