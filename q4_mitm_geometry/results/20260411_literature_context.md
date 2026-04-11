# Literature Context: Our sr=60 Work vs State of the Art

## Current SHA-256 Attack Records (as of April 2026)

| Attack type | Rounds | Reference |
|---|---|---|
| Full collision | **37** | Zhang et al., Shandong, eprint 2026/232 |
| Semi-free-start collision | **39** | Li et al., EUROCRYPT 2024 |
| Programmatic SAT SFS | **38** | Bright et al., arXiv 2406.20072 |
| Practical collision | **31** | Mendel et al., EUROCRYPT 2013 |

## Our Work: sr=60 (rounds 57-63)

Our approach is fundamentally different from the above:
- Standard attacks work **forward** from round 0, using message modification
  in early rounds (0-16) where message words are free
- Our approach works **backward** from round 63, using a cascade chain in
  the TAIL (rounds 57-63) with 4 free schedule words

**Key distinction**: Standard attacks achieve collisions for REDUCED-round
SHA-256 (first N rounds). We achieve collisions for FULL 64-round SHA-256
with SCHEDULE VIOLATIONS (4 equations not satisfied). These are different
problems.

## How They Connect

The 37-step attack (Zhang et al. 2026) uses:
1. Automated local collision discovery in message expansion
2. MILP/SAT for differential trail search
3. Message modification for rounds 0-~20

Our cascade chain approach could COMPLEMENT this:
- Their attack covers rounds 0-37 (forward from message)
- Our cascade covers rounds 57-63 (backward from tail)
- GAP: rounds 38-56 (~19 rounds)

If we could bridge the gap, a combined attack would cover all 64 rounds.

## The Multi-Block Connection

Our finding today: block 2 absorbs HW=40 through 18/64 rounds.
The 37-step attack absorbs through 37/64 rounds from the start.

If the 37-step differential trail could be adapted for block 2
(starting with our HW=40 IV difference), it might extend absorption
significantly beyond our 18-round frontier.

## Key Technical Insights from Literature

1. **Message modification works for rounds 0-16** (free message words)
   and can be extended to ~20-25 via neutral bits and boomerang tricks

2. **Local collisions in message expansion** are critical — the 37-step
   result found NEW local collisions that previous manual search missed

3. **MILP + SAT combination** is the dominant approach for trail search

4. **The bottleneck** is accurate bit condition modeling for IF and MAJ
   Boolean functions — Wang's original technique needed refinement

## Relevance to Our Programmatic SAT

The Bright et al. (2024) Programmatic SAT paper is EXACTLY the
CaDiCaL-SHA256 tool we already have in /tmp/cadical-sha256/.
They achieved 38-step SFS — but our CaDiCaL test showed it's 6.8x
slower than Kissat on our specific encoding. Their encoding format
is different (Nejati's) and optimized for their propagator.

## Actionable Next Steps from Literature

1. **Fetch Zhang et al. 2026 paper** — their automated local collision
   tool could find differential paths relevant to our cascade tail

2. **Adapt Li et al. EUROCRYPT 2024 approach** — their 39-step SFS
   uses MILP for characteristic search, applicable to our problem

3. **Combine forward+backward** — their 37 rounds forward + our 7
   rounds backward = 44 rounds. Only 20-round gap to bridge.
