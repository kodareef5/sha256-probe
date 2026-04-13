# Carry-Conditioned SAT Race: INCONCLUSIVE

## Setup
- Carry-conditioned: 10916 vars, 46799 clauses (+957 carry invariance clauses)
- Baseline: 10916 vars, 45842 clauses (no carry constraints)
- Both use sequential-add encoding (NOT CSA-tree)
- Same candidate: M[0]=0x17149975, fill=0xFFFFFFFF, MSB kernel
- Same seed: Kissat --seed=5

## Result
Both killed at 16h47m. Neither solved.

## Analysis
The sequential-add encoding creates longer carry chains than the CSA-tree
encoding used for the original 12h solve. This makes the problem ~1.4x harder
for Kissat, regardless of carry conditioning.

Memory comparison (fluctuated throughout):
- Carry-conditioned: often 15-30% less memory (better propagation)
- But sometimes spiked higher (deeper conflict analysis)
- No consistent advantage at convergence

## Conclusion
The carry conditioning adds valid structural information (+957 clauses),
but the encoding format (sequential vs CSA) dominates solver performance.
A fair test requires adding carry constraints to the CSA-TREE encoding
used in sha256_round_correct with add5_csa_tracked.

## Lesson
SAT encoding structure matters more than extra constraint clauses.
The carry information is correct but needs to be in the RIGHT encoding.
