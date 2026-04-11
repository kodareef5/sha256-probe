/* Search for (W[57], W[58]) pairs producing the same state at round 59 as cert.
 * If we find one, it has the SAME round-61 constraint as cert and likely
 * has cert-like W[59], W[60] families. */
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
static const uint32_t K[64] = {0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV[8] = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};

static void compute_state(const uint32_t M[16], uint32_t state[8], uint32_t W[64]) {
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < 57; i++) W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16];
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

    /* Cert state at round 59 (target) */
    uint32_t cert_w1_57 = 0x9ccfa55e;
    uint32_t cert_w1_58 = 0xd9d64416;
    uint32_t cert_w1_59 = 0x9e3ffb08;
    uint32_t cert_w2_57 = cert_w1_57 + C57;
    uint32_t cs1a[8], cs2a[8];
    one_round(cs1a, s1, cert_w1_57, 57);
    one_round(cs2a, s2, cert_w2_57, 57);
    uint32_t cert_C58 = cascade_dw(cs1a, cs2a);
    uint32_t cs1b[8], cs2b[8];
    one_round(cs1b, cs1a, cert_w1_58, 58);
    one_round(cs2b, cs2a, cert_w1_58 + cert_C58, 58);
    uint32_t cert_C59 = cascade_dw(cs1b, cs2b);
    uint32_t cs1c[8], cs2c[8];
    one_round(cs1c, cs1b, cert_w1_59, 59);
    one_round(cs2c, cs2b, cert_w1_59 + cert_C59, 59);

    fprintf(stderr, "Cert state at round 59 (M1):\n");
    for (int r = 0; r < 8; r++) fprintf(stderr, "  reg[%d] = 0x%08x\n", r, cs1c[r]);
    fprintf(stderr, "\nWill search 2^32 (W[57]) values exhausting all W[58]=cert and W[59]=cert,\n");
    fprintf(stderr, "looking for any state at round 59 matching cert's e/f/g/h registers (the round-61-relevant ones).\n\n");

    /* Search all 2^32 W1[57] values. For each, compute state at round 57.
     * Then continue with cert W1[58], cert W1[59] to get round-59 state.
     * Compare e,f,g,h registers to cert's. */
    long matches_efgh = 0;
    long matches_full = 0;
    time_t t0 = time(NULL);

    #pragma omp parallel for reduction(+:matches_efgh,matches_full)
    for (long w_l = 0; w_l < (1L << 32); w_l++) {
        uint32_t w1_57 = (uint32_t)w_l;
        if (w1_57 == cert_w1_57) continue;
        uint32_t w2_57 = w1_57 + C57;
        uint32_t s1a[8], s2a[8];
        one_round(s1a, s1, w1_57, 57);
        one_round(s2a, s2, w2_57, 57);
        uint32_t C58 = cascade_dw(s1a, s2a);
        uint32_t s1b[8], s2b[8];
        one_round(s1b, s1a, cert_w1_58, 58);
        one_round(s2b, s2a, cert_w1_58 + C58, 58);
        uint32_t C59 = cascade_dw(s1b, s2b);
        uint32_t s1c[8], s2c[8];
        one_round(s1c, s1b, cert_w1_59, 59);
        one_round(s2c, s2b, cert_w1_59 + C59, 59);

        /* Compare e,f,g,h to cert (these are the round-61 relevant registers) */
        if (s1c[4] == cs1c[4] && s1c[5] == cs1c[5] &&
            s1c[6] == cs1c[6] && s1c[7] == cs1c[7] &&
            s2c[4] == cs2c[4] && s2c[5] == cs2c[5] &&
            s2c[6] == cs2c[6] && s2c[7] == cs2c[7]) {
            matches_efgh++;
            #pragma omp critical
            {
                if (matches_efgh <= 5) fprintf(stderr, "  MATCH efgh: w1_57=0x%08x\n", w1_57);
            }
        }
        /* Full state match */
        int full = 1;
        for (int r = 0; r < 8 && full; r++) {
            if (s1c[r] != cs1c[r] || s2c[r] != cs2c[r]) full = 0;
        }
        if (full) matches_full++;
    }

    time_t t1 = time(NULL);
    fprintf(stderr, "\nDone in %lds\n", (long)(t1-t0));
    fprintf(stderr, "Matches (e/f/g/h equal): %ld\n", matches_efgh);
    fprintf(stderr, "Matches (full state): %ld\n", matches_full);
    return 0;
}
