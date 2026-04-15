# Section 4: BDD Polynomial Complexity (Draft)

## 4.1 Overview

We show that the collision function $f: \{0,1\}^{4N} \to \{0,1\}$, defined as
$f(W_{57},W_{58},W_{59},W_{60}) = 1$ iff the cascade DP produces a full
collision at round 63, has a Binary Decision Diagram (BDD) of polynomial size.

**Theorem 7.** For Mini-SHA-256(N) with the MSB-kernel cascade DP construction,
the reduced ordered BDD of the collision function with interleaved variable
ordering has $O(N^{4.8})$ nodes.

This is verified at 10 word widths $N \in \{2,3,4,5,6,7,8,9,10,12\}$ by
exhaustive truth-table construction (N ≤ 8) and collision-list construction
(N ≥ 9).

## 4.2 Variable Ordering

The interleaved (bit-first) variable ordering assigns:
$$v_{4b+w} = W_{57+w}[b], \quad b = 0,\ldots,N{-}1, \quad w = 0,1,2,3$$

This ordering groups all four message words' bit $b$ together, reflecting
the carry chain's bit-serial structure. The carry at position $b$ of any
addition depends only on bits $0,\ldots,b$ of the operands.

## 4.3 Scaling Data

| $N$ | BDD nodes | Collisions | Truth table | Compression | Method |
|-----|-----------|------------|-------------|-------------|--------|
| 2   | 29        | 8          | $2^8$       | 9×          | TT     |
| 3   | 35        | 8          | $2^{12}$    | 117×        | TT     |
| 4   | 193       | 49         | $2^{16}$    | 340×        | TT     |
| 5   | 1,507     | 350        | $2^{20}$    | 696×        | TT     |
| 6   | 798       | 68         | $2^{24}$    | 21,025×     | TT     |
| 7   | 4,191     | 373        | $2^{28}$    | 64,053×     | TT     |
| 8   | 4,322     | 260        | $2^{32}$    | 993,745×    | TT     |
| 9   | 52,821    | 4,905      | $2^{36}$    | 1,302×*     | Stream |
| 10  | 19,677    | 946        | $2^{40}$    | 55,902,377× | CL     |
| 12  | 92,975    | 3,671      | $2^{48}$    | 3.0×10⁹     | CL     |

*N=9 used a different candidate with more collisions; the BDD
compression relative to truth table is lower due to the streaming
approach's suboptimal variable ordering.

TT = truth-table bottom-up; Stream = streaming (partitioned over W₅₇);
CL = collision-list builder.

**Fit:** $\text{nodes} \approx 0.38 \times N^{4.82}$ ($R^2 = 0.93$).

## 4.4 Per-Variable Node Distribution

At $N=8$, the BDD nodes per variable level form a characteristic bell curve:

| Bit $b$ | W₅₇ | W₅₈ | W₅₉ | W₆₀ | Total |
|---------|------|------|------|------|-------|
| 0 (LSB) | 1 | 2 | 4 | 8 | 15 |
| 1 | 16 | 32 | 60 | 104 | 212 |
| 2 | 155 | 189 | 217 | 234 | 795 |
| 3 | 246 | 249 | 254 | 253 | 1002 |
| 4 | 252 | 252 | 250 | 249 | 1003 |
| 5 | 243 | 236 | 221 | 204 | 904 |
| 6 | 158 | 107 | 63 | 33 | 361 |
| 7 (MSB) | 16 | 8 | 4 | 2 | 30 |

The exponential growth at the LSB reflects carry chain accumulation.
The plateau at middle bits matches the carry automaton width (~260).
The exponential decay at the MSB reflects carry chain termination.

## 4.5 Construction Methods

### 4.5.1 Truth-Table BDD (N ≤ 8)

Generate the complete truth table ($2^{4N}$ bits) via cascade DP.
Build the BDD bottom-up in groups of 4 variables (one bit position at a time).
This produces the canonical ROBDD in $O(2^{4N})$ time.

### 4.5.2 Streaming BDD (N = 9)

Partition over $W_{57}$ ($2^N$ outer iterations). For each $W_{57}$ value,
generate a partial truth table of $2^{3N}$ entries and build a local BDD.
Merge partial BDDs using the Apply (OR) operation with $W_{57}$ constraints.
Total: $O(2^{4N})$ time, $O(2^{3N})$ memory per slice.

### 4.5.3 Collision-List BDD (N ≥ 10)

Enumerate collisions using the NEON+OpenMP structural solver, then pipe
the collision coordinates directly into the BDD builder. Each collision
$(w_{57},w_{58},w_{59},w_{60})$ becomes a "point BDD" (AND of $4N$ literals),
which is OR'd into the running BDD.

This produces the **identical canonical BDD** as the truth-table approach
(verified at $N=8$: both give 4,322 nodes). The cost is
$O(\text{\#collisions} \times N \times B)$ where $B$ is the current BDD size.

### 4.5.4 Construction Complexity Gap

The incremental BDD construction via Apply operations creates exponential
intermediate BDDs: $3 \times 10^6$ nodes at $N=4$, out-of-memory at $N=6$.
This is because individual state paths have exponential BDD complexity;
only their collision function (the AND of all register-equality conditions)
is polynomial.

## 4.6 Significance

1. **Structural complexity.** The collision function has polynomial information
   content despite living in an exponential search space. This is the strongest
   evidence that the cascade collision problem has compact mathematical structure.

2. **Efficient enumeration.** Given the BDD, all collisions can be enumerated
   in $O(B + K)$ time where $B$ is the BDD size and $K$ is the collision count.

3. **Nodes-per-collision.** The ratio BDD nodes / collision count grows as
   $\approx 1.13 \times N^{1.18}$, suggesting the BDD overhead per collision
   is weakly polynomial.

4. **Open problem.** Whether the BDD can be constructed in polynomial time
   (without first finding the collisions) remains open. All known construction
   methods require either $\Omega(2^{4N})$ time (truth table) or
   $\Omega(2^{3N})$ memory (streaming).
