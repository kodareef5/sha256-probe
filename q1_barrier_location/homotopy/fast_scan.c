/*
 * Script 87: Fast N-bit Candidate Scanner
 *
 * C implementation of candidate scanning for the precision homotopy.
 * Outputs M[0] and fill values for da[56]=0 candidates as CSV.
 *
 * Compile: gcc -O3 -march=native -o fast_scan 87_fast_candidate_scan.c -lm
 * Usage: ./fast_scan N [max_candidates]
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

static int N_BITS;
static uint32_t WMASK, MSB_BIT;

static int scale_rot(int k32, int N) {
    /* Use rint() for banker's rounding to match Python's round(). */
    int r = (int)rint((double)k32 * N / 32.0);
    return r < 1 ? 1 : r;
}

static int rS0[3], rS1[3], rs0_r[2], rs1_r[2], ss0, ss1;

static inline uint32_t ror_n(uint32_t x, int k) {
    k = k % N_BITS;
    return ((x >> k) | (x << (N_BITS - k))) & WMASK;
}

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

static uint32_t KN[64], IVN[8];

static uint32_t compress_a(const uint32_t M[16]) {
    uint32_t W[57];
    for (int i = 0; i < 16; i++) W[i] = M[i] & WMASK;
    for (int i = 16; i < 57; i++) {
        uint32_t x2 = W[i-2], x15 = W[i-15];
        W[i] = (ror_n(x2,rs1_r[0]) ^ ror_n(x2,rs1_r[1]) ^ ((x2>>ss1)&WMASK))
              + W[i-7]
              + (ror_n(x15,rs0_r[0]) ^ ror_n(x15,rs0_r[1]) ^ ((x15>>ss0)&WMASK))
              + W[i-16];
        W[i] &= WMASK;
    }
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t S1 = ror_n(e,rS1[0]) ^ ror_n(e,rS1[1]) ^ ror_n(e,rS1[2]);
        uint32_t ch = ((e&f)^((~e)&g)) & WMASK;
        uint32_t T1 = (h + S1 + ch + KN[i] + W[i]) & WMASK;
        uint32_t S0 = ror_n(a,rS0[0]) ^ ror_n(a,rS0[1]) ^ ror_n(a,rS0[2]);
        uint32_t T2 = (S0 + ((a&b)^(a&c)^(b&c))) & WMASK;
        h=g;g=f;f=e;e=(d+T1)&WMASK;d=c;c=b;b=a;a=(T1+T2)&WMASK;
    }
    return a;
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);
    N_BITS = argc > 1 ? atoi(argv[1]) : 19;
    int max_cand = argc > 2 ? atoi(argv[2]) : 20;

    WMASK = (1U << N_BITS) - 1;
    MSB_BIT = 1U << (N_BITS - 1);

    rS0[0]=scale_rot(2,N_BITS); rS0[1]=scale_rot(13,N_BITS); rS0[2]=scale_rot(22,N_BITS);
    rS1[0]=scale_rot(6,N_BITS); rS1[1]=scale_rot(11,N_BITS); rS1[2]=scale_rot(25,N_BITS);
    rs0_r[0]=scale_rot(7,N_BITS); rs0_r[1]=scale_rot(18,N_BITS); ss0=scale_rot(3,N_BITS);
    rs1_r[0]=scale_rot(17,N_BITS); rs1_r[1]=scale_rot(19,N_BITS); ss1=scale_rot(10,N_BITS);

    for (int i = 0; i < 64; i++) KN[i] = K32[i] & WMASK;
    for (int i = 0; i < 8; i++) IVN[i] = IV32[i] & WMASK;

    uint32_t fills[] = {WMASK, 0, WMASK>>1, MSB_BIT, 0x55&WMASK, 0xAA&WMASK,
                        0x33&WMASK, 0xCC&WMASK, 0x0F&WMASK, 0xF0&WMASK};
    int n_fills = 10;

    fprintf(stderr, "Fast scan: N=%d, max=%d candidates\n", N_BITS, max_cand);

    int found = 0;
    time_t t0 = time(NULL);

    /* Output CSV header */
    printf("m0,fill,a1\n");

    for (int fi = 0; fi < n_fills && found < max_cand; fi++) {
        uint32_t fill = fills[fi];
        uint32_t max_m0 = WMASK < (1U << 28) ? WMASK : (1U << 28) - 1;

        for (uint32_t m0 = 0; m0 <= max_m0 && found < max_cand; m0++) {
            uint32_t M1[16], M2[16];
            for (int i = 0; i < 16; i++) { M1[i] = fill; M2[i] = fill; }
            M1[0] = m0; M2[0] = m0 ^ MSB_BIT; M2[9] = fill ^ MSB_BIT;

            uint32_t a1 = compress_a(M1);
            uint32_t a2 = compress_a(M2);

            if (a1 == a2) {
                printf("%u,%u,%u\n", m0, fill, a1);
                found++;
                fprintf(stderr, "  [%d] M[0]=0x%x fill=0x%x\n", found, m0, fill);
            }
        }
    }

    time_t t1 = time(NULL);
    fprintf(stderr, "Done: %d candidates in %lds\n", found, (long)(t1-t0));
    return 0;
}
