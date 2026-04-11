/* For a list of prefixes from prefix_viability_scan output, extract the
 * round-60 differential features (df60, dg60, de60, dh60, etc.) and
 * correlate with image size.
 *
 * Goal: find a CHEAP predictor of image size from prefix structure alone,
 * without computing the full 2^32 enumeration.
 *
 * Reads stdin in format:
 *   "[N] W=0xWWWW,0xWWWW,0xWWWW  image=NNN matches=N ..."
 *
 * For each prefix, computes:
 *   - hw(df60), hw(dg60), hw(de60), hw(dh60)
 *   - hw(C60)  (the cascade constant at round 60)
 *   - Predicts image_size category based on these features
 *
 * Output: feature → image_size table for analysis.
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
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

    fprintf(stdout, "# w57 w58 w59 image hw_de60 hw_df60 hw_dg60 hw_dh60 hw_C60 hw_T1diff matches\n");

    char line[1024];
    while (fgets(line, sizeof(line), stdin)) {
        if (line[0] != '[') continue;
        unsigned int w57, w58, w59;
        long image, matches;
        char *p = strchr(line, '=');
        if (!p) continue;
        if (sscanf(p, "=0x%x,0x%x,0x%x  image=%ld matches=%ld",
                   &w57, &w58, &w59, &image, &matches) != 5) continue;

        uint32_t s1a[8], s2a[8];
        one_round(s1a, s1, w57, 57);
        one_round(s2a, s2, w57 + C57, 57);
        uint32_t C58 = cascade_dw(s1a, s2a);
        uint32_t s1b[8], s2b[8];
        one_round(s1b, s1a, w58, 58);
        one_round(s2b, s2a, w58 + C58, 58);
        uint32_t C59 = cascade_dw(s1b, s2b);
        uint32_t s1c[8], s2c[8];
        one_round(s1c, s1b, w59, 59);
        one_round(s2c, s2b, w59 + C59, 59);
        uint32_t C60 = cascade_dw(s1c, s2c);

        uint32_t de60 = s1c[4] ^ s2c[4];
        uint32_t df60 = s1c[5] ^ s2c[5];
        uint32_t dg60 = s1c[6] ^ s2c[6];
        uint32_t dh60 = s1c[7] ^ s2c[7];

        /* T1 base difference at round 60 (no W[60] contribution) */
        uint32_t T1_base_M1 = s1c[7] + Sigma1(s1c[4]) + Ch(s1c[4], s1c[5], s1c[6]) + K[60];
        uint32_t T1_base_M2 = s2c[7] + Sigma1(s2c[4]) + Ch(s2c[4], s2c[5], s2c[6]) + K[60];
        uint32_t T1_diff = T1_base_M1 - T1_base_M2;

        fprintf(stdout, "0x%08x 0x%08x 0x%08x %ld %d %d %d %d %d %d %ld\n",
                w57, w58, w59, image,
                hw(de60), hw(df60), hw(dg60), hw(dh60), hw(C60), hw(T1_diff), matches);
    }
    return 0;
}
