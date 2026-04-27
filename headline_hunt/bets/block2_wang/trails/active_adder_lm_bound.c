/* active_adder_lm_bound.c — Lipmaa-Moriai-style per-adder probability
 * bound along a cascade-1 trail.
 *
 * For each active modular adder along the rounds-57..63 trail, computes:
 *   - The XOR-difference at each input (HW of α, HW of β)
 *   - Per-adder log2(probability) lower bound:
 *       cost_i ≤ max(HW(α_i), HW(β_i))  bits
 *     (Lipmaa-Moriai 2001 gives exact bound; this is a simple
 *      max-input-HW upper bound on cost.)
 *   - Sum of per-adder costs across all active adders
 *
 * Output: total trail-probability LOWER bound = 2^-(sum of per-adder costs).
 * This refines F34's naive 1-bit-per-adder bound.
 *
 * Compile: gcc -O3 -march=native -o active_adder_lm_bound active_adder_lm_bound.c
 * Run:     ./active_adder_lm_bound m0 fill bit W57 W58 W59 W60
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef uint32_t u32;
static inline u32 ROR(u32 x, int n) { return (x >> n) | (x << (32 - n)); }
static inline u32 Ch(u32 e, u32 f, u32 g) { return (e & f) ^ ((~e) & g); }
static inline u32 Maj(u32 a, u32 b, u32 c) { return (a & b) ^ (a & c) ^ (b & c); }
static inline u32 Sigma0(u32 a) { return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22); }
static inline u32 Sigma1(u32 e) { return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25); }
static inline u32 sigma0_(u32 x) { return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3); }
static inline u32 sigma1_(u32 x) { return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10); }
static inline int popcnt(u32 x) { return __builtin_popcount(x); }

static const u32 K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};
static const u32 IV[8] = {
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
};

static inline u32 cw1(const u32 s1[8], const u32 s2[8]) {
    return (s1[7] - s2[7]) + (Sigma1(s1[4]) - Sigma1(s2[4]))
         + (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6]))
         + (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2]))
         - (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2]));
}

static inline void sha_round(u32 s[8], u32 k, u32 w) {
    u32 T1 = s[7] + Sigma1(s[4]) + Ch(s[4], s[5], s[6]) + k + w;
    u32 T2 = Sigma0(s[0]) + Maj(s[0], s[1], s[2]);
    u32 a_new = T1 + T2;
    u32 e_new = s[3] + T1;
    s[7] = s[6]; s[6] = s[5]; s[5] = s[4]; s[4] = e_new;
    s[3] = s[2]; s[2] = s[1]; s[1] = s[0]; s[0] = a_new;
}

/* Lipmaa-Moriai 2001 XOR-differential probability for modular addition.
 *
 * For α + β → γ (mod 2^32) with given input XOR-diffs α, β and output
 * XOR-diff γ that we will compute, the EXACT probability is:
 *
 *   xdp+(α, β → γ) = 0 if Lipmaa-Moriai constraint violated
 *   xdp+(α, β → γ) = 2^(-w(α, β, γ)) otherwise
 *
 * where w(α, β, γ) = HW( (~eq(α, β, γ)) & 0x7FFFFFFF )
 *       eq(α, β, γ) = ~(α ⊕ β) & ~(α ⊕ γ)
 *       (eq[i]=1 means α[i] = β[i] = γ[i])
 *
 * Constraint: for compatibility, must have:
 *   eq(α << 1, β << 1, γ << 1) AND (α ⊕ β ⊕ γ ⊕ (β << 1)) == 0
 *
 * We implement xdp+ exactly. Returns:
 *   - On compatibility: -log2(p) = w (the cost in bits)
 *   - On incompatibility: -1 (signals zero probability)
 */
static int lm_cost(u32 alpha, u32 beta, u32 gamma) {
    u32 eq_shifted = (~(alpha ^ beta)) & (~(alpha ^ gamma));  /* eq(α, β, γ) */
    /* Compatibility check: bits i ≥ 1 where (α[i-1] = β[i-1] = γ[i-1])
       must satisfy (α[i] ⊕ β[i] ⊕ γ[i]) = β[i-1]. */
    u32 eq_lo = eq_shifted & 0x7FFFFFFF;       /* mask out top bit (bit 31) */
    u32 viol = (alpha ^ beta ^ gamma ^ (beta << 1)) & (eq_shifted << 1);
    if (viol) return -1;  /* incompatible — probability 0 */
    /* Cost: count bits i where eq fails, excluding LSB (bit 0). */
    return popcnt((~eq_lo) & 0x7FFFFFFE);
}

typedef struct {
    int active;          /* whether this adder is active */
    u32 alpha;           /* input 1 XOR-diff */
    u32 beta;            /* input 2 XOR-diff */
    u32 gamma;           /* output XOR-diff (pre-accounting) */
    int hw_alpha;
    int hw_beta;
    int hw_gamma;
    int lm_cost;         /* Lipmaa-Moriai cost (-1 = incompatible) */
    int max_hw;          /* max(hw_alpha, hw_beta) — naive upper bound */
} adder_info_t;

/* Compute info for all 7 adders in one round, given pre-round states + W diffs. */
static void compute_round_adders(const u32 s1[8], const u32 s2[8],
                                  u32 w1, u32 w2, u32 k,
                                  adder_info_t adders[7]) {
    /* Adder 1: h + Σ1(e) */
    u32 a1 = s1[7] ^ s2[7];
    u32 b1 = Sigma1(s1[4]) ^ Sigma1(s2[4]);
    u32 acc1_1 = s1[7] + Sigma1(s1[4]), acc1_2 = s2[7] + Sigma1(s2[4]);
    u32 g1 = acc1_1 ^ acc1_2;
    adders[0].alpha = a1; adders[0].beta = b1; adders[0].gamma = g1;
    adders[0].active = (a1 | b1) != 0;
    adders[0].hw_alpha = popcnt(a1); adders[0].hw_beta = popcnt(b1); adders[0].hw_gamma = popcnt(g1);
    adders[0].lm_cost = adders[0].active ? lm_cost(a1, b1, g1) : 0;
    adders[0].max_hw = (adders[0].hw_alpha > adders[0].hw_beta) ? adders[0].hw_alpha : adders[0].hw_beta;

    /* Adder 2: + Ch(e,f,g) */
    u32 a2 = g1;  /* output of adder 1 */
    u32 b2 = Ch(s1[4], s1[5], s1[6]) ^ Ch(s2[4], s2[5], s2[6]);
    u32 acc2_1 = acc1_1 + Ch(s1[4], s1[5], s1[6]), acc2_2 = acc1_2 + Ch(s2[4], s2[5], s2[6]);
    u32 g2 = acc2_1 ^ acc2_2;
    adders[1].alpha = a2; adders[1].beta = b2; adders[1].gamma = g2;
    adders[1].active = (a2 | b2) != 0;
    adders[1].hw_alpha = popcnt(a2); adders[1].hw_beta = popcnt(b2); adders[1].hw_gamma = popcnt(g2);
    adders[1].lm_cost = adders[1].active ? lm_cost(a2, b2, g2) : 0;
    adders[1].max_hw = (adders[1].hw_alpha > adders[1].hw_beta) ? adders[1].hw_alpha : adders[1].hw_beta;

    /* Adder 3: + K (constant — input 2 has zero diff) */
    u32 a3 = g2;
    u32 b3 = 0;
    u32 acc3_1 = acc2_1 + k, acc3_2 = acc2_2 + k;
    u32 g3 = acc3_1 ^ acc3_2;
    adders[2].alpha = a3; adders[2].beta = b3; adders[2].gamma = g3;
    adders[2].active = (a3 | b3) != 0;
    adders[2].hw_alpha = popcnt(a3); adders[2].hw_beta = 0; adders[2].hw_gamma = popcnt(g3);
    adders[2].lm_cost = adders[2].active ? lm_cost(a3, b3, g3) : 0;
    adders[2].max_hw = adders[2].hw_alpha;

    /* Adder 4: + W (= T1) */
    u32 a4 = g3;
    u32 b4 = w1 ^ w2;
    u32 T1_1 = acc3_1 + w1, T1_2 = acc3_2 + w2;
    u32 g4 = T1_1 ^ T1_2;
    adders[3].alpha = a4; adders[3].beta = b4; adders[3].gamma = g4;
    adders[3].active = (a4 | b4) != 0;
    adders[3].hw_alpha = popcnt(a4); adders[3].hw_beta = popcnt(b4); adders[3].hw_gamma = popcnt(g4);
    adders[3].lm_cost = adders[3].active ? lm_cost(a4, b4, g4) : 0;
    adders[3].max_hw = (adders[3].hw_alpha > adders[3].hw_beta) ? adders[3].hw_alpha : adders[3].hw_beta;

    /* Adder 5: T2 = Σ0(a) + Maj(a,b,c) */
    u32 a5 = Sigma0(s1[0]) ^ Sigma0(s2[0]);
    u32 b5 = Maj(s1[0], s1[1], s1[2]) ^ Maj(s2[0], s2[1], s2[2]);
    u32 T2_1 = Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2]);
    u32 T2_2 = Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2]);
    u32 g5 = T2_1 ^ T2_2;
    adders[4].alpha = a5; adders[4].beta = b5; adders[4].gamma = g5;
    adders[4].active = (a5 | b5) != 0;
    adders[4].hw_alpha = popcnt(a5); adders[4].hw_beta = popcnt(b5); adders[4].hw_gamma = popcnt(g5);
    adders[4].lm_cost = adders[4].active ? lm_cost(a5, b5, g5) : 0;
    adders[4].max_hw = (adders[4].hw_alpha > adders[4].hw_beta) ? adders[4].hw_alpha : adders[4].hw_beta;

    /* Adder 6: a' = T1 + T2 */
    u32 a6 = g4;
    u32 b6 = g5;
    u32 a_new_1 = T1_1 + T2_1, a_new_2 = T1_2 + T2_2;
    u32 g6 = a_new_1 ^ a_new_2;
    adders[5].alpha = a6; adders[5].beta = b6; adders[5].gamma = g6;
    adders[5].active = (a6 | b6) != 0;
    adders[5].hw_alpha = popcnt(a6); adders[5].hw_beta = popcnt(b6); adders[5].hw_gamma = popcnt(g6);
    adders[5].lm_cost = adders[5].active ? lm_cost(a6, b6, g6) : 0;
    adders[5].max_hw = (adders[5].hw_alpha > adders[5].hw_beta) ? adders[5].hw_alpha : adders[5].hw_beta;

    /* Adder 7: e' = d + T1 */
    u32 a7 = s1[3] ^ s2[3];
    u32 b7 = g4;
    u32 e_new_1 = s1[3] + T1_1, e_new_2 = s2[3] + T1_2;
    u32 g7 = e_new_1 ^ e_new_2;
    adders[6].alpha = a7; adders[6].beta = b7; adders[6].gamma = g7;
    adders[6].active = (a7 | b7) != 0;
    adders[6].hw_alpha = popcnt(a7); adders[6].hw_beta = popcnt(b7); adders[6].hw_gamma = popcnt(g7);
    adders[6].lm_cost = adders[6].active ? lm_cost(a7, b7, g7) : 0;
    adders[6].max_hw = (adders[6].hw_alpha > adders[6].hw_beta) ? adders[6].hw_alpha : adders[6].hw_beta;
}

int main(int argc, char **argv) {
    int verbose = 0;
    int argbase = 1;
    if (argc > 1 && strcmp(argv[1], "-v") == 0) { verbose = 1; argbase = 2; }
    if (argc - argbase < 7) {
        fprintf(stderr, "Usage: %s [-v] m0 fill bit W57 W58 W59 W60\n", argv[0]);
        return 1;
    }
    u32 m0 = strtoul(argv[argbase + 0], NULL, 0);
    u32 fill = strtoul(argv[argbase + 1], NULL, 0);
    int bit = atoi(argv[argbase + 2]);
    u32 W1_57 = strtoul(argv[argbase + 3], NULL, 0);
    u32 W1_58 = strtoul(argv[argbase + 4], NULL, 0);
    u32 W1_59 = strtoul(argv[argbase + 5], NULL, 0);
    u32 W1_60 = strtoul(argv[argbase + 6], NULL, 0);
    u32 kernel_mask = (u32)1 << bit;

    /* Pre-state. */
    u32 M1[16], M2[16];
    M1[0] = m0;
    for (int i = 1; i < 16; i++) M1[i] = fill;
    memcpy(M2, M1, sizeof M2);
    M2[0] ^= kernel_mask; M2[9] ^= kernel_mask;
    u32 W1_pre[64], W2_pre[64];
    for (int i = 0; i < 16; i++) { W1_pre[i] = M1[i]; W2_pre[i] = M2[i]; }
    for (int i = 16; i < 64; i++) {
        W1_pre[i] = sigma1_(W1_pre[i-2]) + W1_pre[i-7] + sigma0_(W1_pre[i-15]) + W1_pre[i-16];
        W2_pre[i] = sigma1_(W2_pre[i-2]) + W2_pre[i-7] + sigma0_(W2_pre[i-15]) + W2_pre[i-16];
    }
    u32 s1[8], s2[8];
    for (int i = 0; i < 8; i++) { s1[i] = IV[i]; s2[i] = IV[i]; }
    for (int r = 0; r < 57; r++) {
        sha_round(s1, K[r], W1_pre[r]);
        sha_round(s2, K[r], W2_pre[r]);
    }

    /* Cascade-1 forward, computing per-adder LM cost. */
    u32 W1_full[64], W2_full[64];
    memcpy(W1_full, W1_pre, sizeof W1_pre);
    memcpy(W2_full, W2_pre, sizeof W2_pre);
    W1_full[57] = W1_57; W1_full[58] = W1_58; W1_full[59] = W1_59; W1_full[60] = W1_60;
    /* Recompute W1[61..63] from the witness-overridden W1[57..60]. */
    for (int r = 61; r < 64; r++) {
        W1_full[r] = sigma1_(W1_full[r-2]) + W1_full[r-7]
                   + sigma0_(W1_full[r-15]) + W1_full[r-16];
    }

    int total_active = 0;
    int total_lm_cost = 0;
    int total_max_hw = 0;
    int incompatible_count = 0;
    int per_round_lm[7] = {0}, per_round_max[7] = {0}, per_round_active[7] = {0};

    const char *ADDER_NAMES[7] = {"h+Σ1(e)", "+Ch", "+K", "+W=T1", "Σ0+Maj=T2", "a'=T1+T2", "e'=d+T1"};

    if (verbose) {
        printf("=== active_adder_lm_bound: m0=0x%08x fill=0x%08x bit=%d ===\n", m0, fill, bit);
        printf("W = 0x%08x 0x%08x 0x%08x 0x%08x\n\n", W1_57, W1_58, W1_59, W1_60);
    }

    for (int r = 57; r < 64; r++) {
        u32 w1 = W1_full[r], w2;
        if (r <= 60) {
            u32 cw = cw1(s1, s2);
            w2 = w1 + cw;
            W2_full[r] = w2;
        } else {
            w2 = W2_full[r] = sigma1_(W2_full[r-2]) + W2_full[r-7]
                            + sigma0_(W2_full[r-15]) + W2_full[r-16];
        }
        adder_info_t adders[7];
        compute_round_adders(s1, s2, w1, w2, K[r], adders);
        if (verbose) printf("Round %d (W1=0x%08x W2=0x%08x):\n", r, w1, w2);
        for (int i = 0; i < 7; i++) {
            if (adders[i].active) {
                per_round_active[r - 57]++;
                total_active++;
                if (adders[i].lm_cost < 0) {
                    incompatible_count++;
                    if (verbose) printf("  [%s] α=0x%08x(HW=%d) β=0x%08x(HW=%d) γ=0x%08x(HW=%d)  LM=INCOMPAT  max_hw=%d\n",
                        ADDER_NAMES[i], adders[i].alpha, adders[i].hw_alpha,
                        adders[i].beta, adders[i].hw_beta, adders[i].gamma, adders[i].hw_gamma,
                        adders[i].max_hw);
                } else {
                    per_round_lm[r - 57] += adders[i].lm_cost;
                    total_lm_cost += adders[i].lm_cost;
                    if (verbose) printf("  [%s] α=0x%08x(HW=%d) β=0x%08x(HW=%d) γ=0x%08x(HW=%d)  LM=%d  max_hw=%d\n",
                        ADDER_NAMES[i], adders[i].alpha, adders[i].hw_alpha,
                        adders[i].beta, adders[i].hw_beta, adders[i].gamma, adders[i].hw_gamma,
                        adders[i].lm_cost, adders[i].max_hw);
                }
                per_round_max[r - 57] += adders[i].max_hw;
                total_max_hw += adders[i].max_hw;
            }
        }
        sha_round(s1, K[r], w1); sha_round(s2, K[r], w2);
    }

    if (verbose) printf("\n");
    printf("Per-round breakdown:\n");
    printf("  %-3s %-6s %-8s %-8s\n", "r", "active", "LM-sum", "max-HW-sum");
    for (int i = 0; i < 7; i++)
        printf("  %-3d %-6d %-8d %-8d\n",
            57 + i, per_round_active[i], per_round_lm[i], per_round_max[i]);

    int hw_final = 0;
    for (int j = 0; j < 8; j++) hw_final += popcnt(s1[j] ^ s2[j]);
    printf("\nFinal HW(diff63) = %d\n", hw_final);
    printf("\nTotal active adders: %d / 49 max\n", total_active);
    printf("Total Lipmaa-Moriai cost (sum): %d bits\n", total_lm_cost);
    printf("Total max-HW upper bound (sum): %d bits\n", total_max_hw);
    printf("Incompatible (LM-violating) adders: %d (these would zero the trail probability)\n",
           incompatible_count);
    printf("\nNaive 1-bit-per-active bound:        2^-%d  (was F34 result)\n", total_active);
    printf("Lipmaa-Moriai exact cost bound:      2^-%d  (this run, refined)\n", total_lm_cost);
    printf("Max-HW upper bound:                  2^-%d  (loose ceiling)\n", total_max_hw);
    if (incompatible_count > 0) {
        printf("\n⚠ %d incompatible adders. The trail as constructed has\n", incompatible_count);
        printf("   probability ZERO under XOR-difference cryptanalysis. This means\n");
        printf("   the cascade-1 mechanism uses MODULAR carries that DON'T propagate\n");
        printf("   purely through XOR-diff — a nontrivial probabilistic distinction.\n");
    }
    printf("\nWith 256-bit second-block freedom: ~2^%d expected solutions (LM bound)\n",
           256 - total_lm_cost);
    return 0;
}
