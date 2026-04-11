/* Deep analysis of newly discovered viable prefix:
 *   W[57] = 0xab307a5a
 *   W[58] = 0xdf6fcc2e
 *   W[59] = 0x5acbd836
 *   (8192 W[60] values give round-61 closure)
 *
 * Tests:
 * 1. Verify round-61 closure (independent check via slow scanner)
 * 2. For each of 8192 round-61 matches, test round-62 and round-63 closure
 * 3. Compute the image basis structure
 * 4. Compute the W[59] free-bit family (like cert's 8 bits)
 * 5. Check XOR distance from cert
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef _OPENMP
#include <omp.h>
#endif
#define MASK 0xFFFFFFFFU
static inline uint32_t ROR(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }
static inline uint32_t Ch(uint32_t e, uint32_t f, uint32_t g) { return (e & f) ^ (~e & g); }
static inline uint32_t Maj(uint32_t a, uint32_t b, uint32_t c) { return (a & b) ^ (a & c) ^ (b & c); }
static inline uint32_t Sigma0(uint32_t a) { return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22); }
static inline uint32_t Sigma1(uint32_t e) { return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25); }
static inline uint32_t sigma0(uint32_t x) { return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3); }
static inline uint32_t sigma1(uint32_t x) { return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10); }
static inline int hw(uint32_t x) { return __builtin_popcount(x); }
static const uint32_t K[64] = {0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV[8] = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};

static void compute_state(const uint32_t M[16], uint32_t state[8], uint32_t W[64]) {
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < 64; i++) W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16];
    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = h + Sigma1(e) + Ch(e,f,g) + K[i] + W[i];
        uint32_t T2 = Sigma0(a) + Maj(a,b,c);
        h=g; g=f; f=e; e=d+T1; d=c; c=b; b=a; a=T1+T2;
    }
    state[0]=a; state[1]=b; state[2]=c; state[3]=d;
    state[4]=e; state[5]=f; state[6]=g; state[7]=h;
}
static uint32_t cascade_dw(const uint32_t s1[8], const uint32_t s2[8]) {
    uint32_t dh = s1[7] - s2[7];
    uint32_t dSig1 = Sigma1(s1[4]) - Sigma1(s2[4]);
    uint32_t dCh = Ch(s1[4],s1[5],s1[6]) - Ch(s2[4],s2[5],s2[6]);
    uint32_t T2_1 = Sigma0(s1[0]) + Maj(s1[0],s1[1],s1[2]);
    uint32_t T2_2 = Sigma0(s2[0]) + Maj(s2[0],s2[1],s2[2]);
    return dh + dSig1 + dCh + T2_1 - T2_2;
}
static void one_round(uint32_t out[8], const uint32_t in[8], uint32_t w, int round_idx) {
    uint32_t T1 = in[7] + Sigma1(in[4]) + Ch(in[4],in[5],in[6]) + K[round_idx] + w;
    uint32_t T2 = Sigma0(in[0]) + Maj(in[0],in[1],in[2]);
    out[0] = T1 + T2; out[1] = in[0]; out[2] = in[1]; out[3] = in[2];
    out[4] = in[3] + T1; out[5] = in[4]; out[6] = in[5]; out[7] = in[6];
}

int main() {
    uint32_t M1[16] = {0x17149975,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff};
    uint32_t M2[16];
    memcpy(M2, M1, sizeof(M2));
    M2[0] ^= 0x80000000; M2[9] ^= 0x80000000;
    uint32_t s1[8], s2[8], W1_pre[64], W2_pre[64];
    compute_state(M1, s1, W1_pre);
    compute_state(M2, s2, W2_pre);
    uint32_t C57 = cascade_dw(s1, s2);

    uint32_t cert_w1_57 = 0x9ccfa55e, cert_w1_58 = 0xd9d64416, cert_w1_59 = 0x9e3ffb08, cert_w1_60 = 0xb6befe82;
    uint32_t new_w1_57 = 0xab307a5a, new_w1_58 = 0xdf6fcc2e, new_w1_59 = 0x5acbd836;

    fprintf(stderr, "=== NEW PREFIX vs CERT ===\n");
    fprintf(stderr, "Cert:  W57=0x%08x  W58=0x%08x  W59=0x%08x  W60=0x%08x\n",
            cert_w1_57, cert_w1_58, cert_w1_59, cert_w1_60);
    fprintf(stderr, "New:   W57=0x%08x  W58=0x%08x  W59=0x%08x  W60=??? (8192 valid)\n",
            new_w1_57, new_w1_58, new_w1_59);
    fprintf(stderr, "XOR:   W57=0x%08x(hw=%d)  W58=0x%08x(hw=%d)  W59=0x%08x(hw=%d)  total HW=%d\n\n",
            cert_w1_57^new_w1_57, hw(cert_w1_57^new_w1_57),
            cert_w1_58^new_w1_58, hw(cert_w1_58^new_w1_58),
            cert_w1_59^new_w1_59, hw(cert_w1_59^new_w1_59),
            hw(cert_w1_57^new_w1_57) + hw(cert_w1_58^new_w1_58) + hw(cert_w1_59^new_w1_59));

    /* Build round-60 state for new prefix */
    uint32_t s1a[8], s2a[8];
    one_round(s1a, s1, new_w1_57, 57);
    one_round(s2a, s2, new_w1_57 + C57, 57);
    uint32_t C58 = cascade_dw(s1a, s2a);
    uint32_t s1b[8], s2b[8];
    one_round(s1b, s1a, new_w1_58, 58);
    one_round(s2b, s2a, new_w1_58 + C58, 58);
    uint32_t C59 = cascade_dw(s1b, s2b);
    uint32_t s1c[8], s2c[8];
    one_round(s1c, s1b, new_w1_59, 59);
    one_round(s2c, s2b, new_w1_59 + C59, 59);
    uint32_t C60 = cascade_dw(s1c, s2c);
    uint32_t target_dW61 = sigma1(new_w1_59 + C59) - sigma1(new_w1_59)
                          + (W2_pre[54] + sigma0(W2_pre[46]) + W2_pre[45])
                          - (W1_pre[54] + sigma0(W1_pre[46]) + W1_pre[45]);

    fprintf(stderr, "Cascade chain values for NEW prefix:\n");
    fprintf(stderr, "  C57=0x%08x C58=0x%08x C59=0x%08x C60=0x%08x\n", C57, C58, C59, C60);
    fprintf(stderr, "  target_dW61=0x%08x\n\n", target_dW61);

    fprintf(stderr, "Round-60 state diffs:\n");
    fprintf(stderr, "  de60=0x%08x(hw=%d)  df60=0x%08x(hw=%d)  dg60=0x%08x(hw=%d)  dh60=0x%08x(hw=%d)\n\n",
            s1c[4]^s2c[4], hw(s1c[4]^s2c[4]),
            s1c[5]^s2c[5], hw(s1c[5]^s2c[5]),
            s1c[6]^s2c[6], hw(s1c[6]^s2c[6]),
            s1c[7]^s2c[7], hw(s1c[7]^s2c[7]));

    /* Find ALL W[60] satisfying round-61, then test 62/63 for each */
    fprintf(stderr, "=== Finding all round-61 matches ===\n");
    uint32_t *matches_w60 = malloc(20000 * sizeof(uint32_t));
    int n_matches = 0;
    #pragma omp parallel
    {
        uint32_t local[20000];
        int local_n = 0;
        #pragma omp for schedule(static)
        for (long w_l = 0; w_l < (1L << 32); w_l++) {
            uint32_t w1_60 = (uint32_t)w_l;
            uint32_t s1d[8], s2d[8];
            one_round(s1d, s1c, w1_60, 60);
            one_round(s2d, s2c, w1_60 + C60, 60);
            if (cascade_dw(s1d, s2d) == target_dW61) {
                if (local_n < 20000) local[local_n++] = w1_60;
            }
        }
        #pragma omp critical
        {
            for (int i = 0; i < local_n && n_matches < 20000; i++) {
                matches_w60[n_matches++] = local[i];
            }
        }
    }
    fprintf(stderr, "Found %d round-61 matches\n\n", n_matches);

    /* For each match, test round-62 and round-63 closure */
    fprintf(stderr, "=== Testing round-62 and round-63 closure ===\n");
    int n_round62 = 0, n_round63 = 0;
    int round62_examples[10], round63_examples[10];
    int n_r62_ex = 0, n_r63_ex = 0;

    for (int i = 0; i < n_matches; i++) {
        uint32_t w1_60 = matches_w60[i];
        uint32_t s1d[8], s2d[8];
        one_round(s1d, s1c, w1_60, 60);
        one_round(s2d, s2c, w1_60 + C60, 60);

        /* Round 61: state = s1e */
        uint32_t w1_61 = sigma1(new_w1_59) + W1_pre[54] + sigma0(W1_pre[46]) + W1_pre[45];
        uint32_t w2_61 = sigma1(new_w1_59 + C59) + W2_pre[54] + sigma0(W2_pre[46]) + W2_pre[45];
        uint32_t s1e[8], s2e[8];
        one_round(s1e, s1d, w1_61, 61);
        one_round(s2e, s2d, w2_61, 61);

        /* Round-62 closure: cascade_dw at round 62 should equal scheduled dW62 */
        uint32_t w1_62 = sigma1(w1_61) + W1_pre[55] + sigma0(W1_pre[47]) + W1_pre[46];
        uint32_t w2_62 = sigma1(w2_61) + W2_pre[55] + sigma0(W2_pre[47]) + W2_pre[46];
        uint32_t target_dW62 = w2_62 - w1_62;
        if (cascade_dw(s1e, s2e) == target_dW62) {
            n_round62++;
            if (n_r62_ex < 10) round62_examples[n_r62_ex++] = i;

            /* Test round-63 too */
            uint32_t s1f[8], s2f[8];
            one_round(s1f, s1e, w1_62, 62);
            one_round(s2f, s2e, w2_62, 62);
            uint32_t w1_63 = sigma1(w1_62) + W1_pre[56] + sigma0(W1_pre[48]) + W1_pre[47];
            uint32_t w2_63 = sigma1(w2_62) + W2_pre[55+1] + sigma0(W2_pre[48]) + W2_pre[47];
            uint32_t target_dW63 = w2_63 - w1_63;
            if (cascade_dw(s1f, s2f) == target_dW63) {
                n_round63++;
                if (n_r63_ex < 10) round63_examples[n_r63_ex++] = i;
            }
        }
    }

    fprintf(stderr, "Round-61 matches:  %d (expected 8192)\n", n_matches);
    fprintf(stderr, "Round-62 also OK:  %d  (cert: 1)\n", n_round62);
    fprintf(stderr, "Round-63 also OK:  %d  (cert: 1)\n\n", n_round63);

    if (n_round62 > 0) {
        fprintf(stderr, "*** Round-62 viable W[60] examples: ***\n");
        for (int i = 0; i < n_r62_ex; i++) {
            fprintf(stderr, "  W[60] = 0x%08x\n", matches_w60[round62_examples[i]]);
        }
        fprintf(stderr, "\n");
    }
    if (n_round63 > 0) {
        fprintf(stderr, "*** !! FULL CLOSURE !! Round-63 viable W[60]: ***\n");
        for (int i = 0; i < n_r63_ex; i++) {
            fprintf(stderr, "  W[60] = 0x%08x  <-- THIS IS A SECOND CERT!\n",
                    matches_w60[round63_examples[i]]);
        }
        fprintf(stderr, "\n");
    } else {
        fprintf(stderr, "No round-63 closure for this prefix.\n");
        fprintf(stderr, "Round-61 viable but doesn't extend to full cert quality.\n");
    }

    free(matches_w60);
    return 0;
}
