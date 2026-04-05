/*
 * sha256.c — Parametric N-bit SHA-256 implementation
 */

#include "sha256.h"


/* Global state */
int sha256_N;
uint32_t sha256_MASK;
uint32_t sha256_MSB;
uint32_t sha256_K[64];
uint32_t sha256_IV[8];
int sha256_rS0[3], sha256_rS1[3];
int sha256_rs0[2], sha256_rs1[2];
int sha256_ss0, sha256_ss1;

static const uint32_t K32[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

static const uint32_t IV32[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};

static int scale_rot(int k32, int N) {
    int r = (int)(0.5 + (double)k32 * N / 32.0);
    return r < 1 ? 1 : r;
}

void sha256_init(int N) {
    sha256_N = N;
    sha256_MASK = (N >= 32) ? 0xFFFFFFFFU : ((1U << N) - 1);
    sha256_MSB = 1U << (N - 1);

    sha256_rS0[0] = scale_rot(2, N);
    sha256_rS0[1] = scale_rot(13, N);
    sha256_rS0[2] = scale_rot(22, N);
    sha256_rS1[0] = scale_rot(6, N);
    sha256_rS1[1] = scale_rot(11, N);
    sha256_rS1[2] = scale_rot(25, N);
    sha256_rs0[0] = scale_rot(7, N);
    sha256_rs0[1] = scale_rot(18, N);
    sha256_ss0 = scale_rot(3, N);
    sha256_rs1[0] = scale_rot(17, N);
    sha256_rs1[1] = scale_rot(19, N);
    sha256_ss1 = scale_rot(10, N);

    for (int i = 0; i < 64; i++) sha256_K[i] = K32[i] & sha256_MASK;
    for (int i = 0; i < 8; i++) sha256_IV[i] = IV32[i] & sha256_MASK;
}

void sha256_precompute(const uint32_t M[16], sha256_precomp_t *out) {
    uint32_t MK = sha256_MASK;
    for (int i = 0; i < 16; i++) out->W[i] = M[i] & MK;
    for (int i = 16; i < 57; i++)
        out->W[i] = (sha256_sigma1(out->W[i-2]) + out->W[i-7] +
                      sha256_sigma0(out->W[i-15]) + out->W[i-16]) & MK;

    uint32_t a=sha256_IV[0], b=sha256_IV[1], c=sha256_IV[2], d=sha256_IV[3];
    uint32_t e=sha256_IV[4], f=sha256_IV[5], g=sha256_IV[6], h=sha256_IV[7];

    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h + sha256_Sigma1(e) + sha256_Ch(e,f,g) + sha256_K[i] + out->W[i]) & MK;
        uint32_t T2 = (sha256_Sigma0(a) + sha256_Maj(a,b,c)) & MK;
        h=g; g=f; f=e; e=(d+T1)&MK; d=c; c=b; b=a; a=(T1+T2)&MK;
    }

    out->state[0]=a; out->state[1]=b; out->state[2]=c; out->state[3]=d;
    out->state[4]=e; out->state[5]=f; out->state[6]=g; out->state[7]=h;
}

int sha256_eval_tail(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                     const uint32_t w1[4], const uint32_t w2[4]) {
    uint32_t MK = sha256_MASK;
    uint32_t W1[7], W2[7];

    for (int i = 0; i < 4; i++) { W1[i] = w1[i] & MK; W2[i] = w2[i] & MK; }

    /* W[61..63] from schedule rule */
    W1[4] = (sha256_sigma1(W1[2]) + p1->W[54] + sha256_sigma0(p1->W[46]) + p1->W[45]) & MK;
    W2[4] = (sha256_sigma1(W2[2]) + p2->W[54] + sha256_sigma0(p2->W[46]) + p2->W[45]) & MK;
    W1[5] = (sha256_sigma1(W1[3]) + p1->W[55] + sha256_sigma0(p1->W[47]) + p1->W[46]) & MK;
    W2[5] = (sha256_sigma1(W2[3]) + p2->W[55] + sha256_sigma0(p2->W[47]) + p2->W[46]) & MK;
    W1[6] = (sha256_sigma1(W1[4]) + p1->W[56] + sha256_sigma0(p1->W[48]) + p1->W[47]) & MK;
    W2[6] = (sha256_sigma1(W2[4]) + p2->W[56] + sha256_sigma0(p2->W[48]) + p2->W[47]) & MK;

    uint32_t a1=p1->state[0],b1=p1->state[1],c1=p1->state[2],d1=p1->state[3];
    uint32_t e1=p1->state[4],f1=p1->state[5],g1=p1->state[6],h1=p1->state[7];
    uint32_t a2=p2->state[0],b2=p2->state[1],c2=p2->state[2],d2=p2->state[3];
    uint32_t e2=p2->state[4],f2=p2->state[5],g2=p2->state[6],h2=p2->state[7];

    for (int i = 0; i < 7; i++) {
        uint32_t T1a = (h1+sha256_Sigma1(e1)+sha256_Ch(e1,f1,g1)+sha256_K[57+i]+W1[i]) & MK;
        uint32_t T2a = (sha256_Sigma0(a1)+sha256_Maj(a1,b1,c1)) & MK;
        h1=g1;g1=f1;f1=e1;e1=(d1+T1a)&MK;d1=c1;c1=b1;b1=a1;a1=(T1a+T2a)&MK;

        uint32_t T1b = (h2+sha256_Sigma1(e2)+sha256_Ch(e2,f2,g2)+sha256_K[57+i]+W2[i]) & MK;
        uint32_t T2b = (sha256_Sigma0(a2)+sha256_Maj(a2,b2,c2)) & MK;
        h2=g2;g2=f2;f2=e2;e2=(d2+T1b)&MK;d2=c2;c2=b2;b2=a2;a2=(T1b+T2b)&MK;
    }

    return sha256_hw(a1^a2) + sha256_hw(b1^b2) + sha256_hw(c1^c2) + sha256_hw(d1^d2) +
           sha256_hw(e1^e2) + sha256_hw(f1^f2) + sha256_hw(g1^g2) + sha256_hw(h1^h2);
}
