/*
 * Step 4: Higher-Order Differential Scanner
 *
 * Systematically compute k-th order differentials of each output bit
 * for k = 1, 2, ..., 32, using both random and structured directions.
 *
 * A zero k-th order differential at k < expected_degree reveals hidden
 * algebraic structure that simple degree estimation misses.
 *
 * The k-th order differential:
 *   Δ_{d1,...,dk} f(x) = XOR over all subsets S of {d1,...,dk} of f(x + sum(S))
 *
 * For a degree-d polynomial, this is ZERO whenever k > d.
 *
 * Compile: gcc -O3 -march=native -o higher_order_diff higher_order_diff.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

#define N 8  /* word width */
#define MASK ((1U << N) - 1)
#define MSB (1U << (N - 1))
#define N_FREE (2 * 4 * N)  /* total free bits: 64 at N=8 */
#define N_OUT (8 * N)  /* total output bits: 64 at N=8 */

/* Scaled rotation amounts for N=8 */
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;
static inline uint32_t ror_n(uint32_t x, int k) { k=k%N; return ((x>>k)|(x<<(N-k)))&MASK; }
static inline uint32_t fn_S0(uint32_t a) { return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]); }
static inline uint32_t fn_S1(uint32_t e) { return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]); }
static inline uint32_t fn_s0(uint32_t x) { return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&MASK); }
static inline uint32_t fn_s1(uint32_t x) { return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&MASK); }
static inline uint32_t fn_Ch(uint32_t e, uint32_t f, uint32_t g) { return ((e&f)^((~e)&g))&MASK; }
static inline uint32_t fn_Maj(uint32_t a, uint32_t b, uint32_t c) { return ((a&b)^(a&c)^(b&c))&MASK; }

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
static uint32_t state1[8], state2[8], W1_pre[57], W2_pre[57];

static int scale_rot(int k32) {
    int r = (int)rint((double)k32 * N / 32.0);
    return r < 1 ? 1 : r;
}

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i=0;i<16;i++) W[i]=M[i]&MASK;
    for (int i=16;i<57;i++) W[i]=(fn_s1(W[i-2])+W[i-7]+fn_s0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i=0;i<57;i++) {
        uint32_t T1=(h+fn_S1(e)+fn_Ch(e,f,g)+KN[i]+W[i])&MASK;
        uint32_t T2=(fn_S0(a)+fn_Maj(a,b,c))&MASK;
        h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;
    }
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

/* Encode/decode free bits as a 64-bit vector */
typedef uint64_t input_t;

static inline void decode_input(input_t x, uint32_t w1[4], uint32_t w2[4]) {
    w1[0]=(x>>0)&MASK; w1[1]=(x>>(N))&MASK; w1[2]=(x>>(2*N))&MASK; w1[3]=(x>>(3*N))&MASK;
    w2[0]=(x>>(4*N))&MASK; w2[1]=(x>>(5*N))&MASK; w2[2]=(x>>(6*N))&MASK; w2[3]=(x>>(7*N))&MASK;
}

static uint64_t eval_diff(input_t x) {
    uint32_t w1[4], w2[4];
    decode_input(x, w1, w2);

    uint32_t W1[7], W2[7];
    for (int i=0;i<4;i++){W1[i]=w1[i];W2[i]=w2[i];}
    W1[4]=(fn_s1(W1[2])+W1_pre[54]+fn_s0(W1_pre[46])+W1_pre[45])&MASK;
    W2[4]=(fn_s1(W2[2])+W2_pre[54]+fn_s0(W2_pre[46])+W2_pre[45])&MASK;
    W1[5]=(fn_s1(W1[3])+W1_pre[55]+fn_s0(W1_pre[47])+W1_pre[46])&MASK;
    W2[5]=(fn_s1(W2[3])+W2_pre[55]+fn_s0(W2_pre[47])+W2_pre[46])&MASK;
    W1[6]=(fn_s1(W1[4])+W1_pre[56]+fn_s0(W1_pre[48])+W1_pre[47])&MASK;
    W2[6]=(fn_s1(W2[4])+W2_pre[56]+fn_s0(W2_pre[48])+W2_pre[47])&MASK;

    uint32_t a1=state1[0],b1=state1[1],c1=state1[2],d1=state1[3];
    uint32_t e1=state1[4],f1=state1[5],g1=state1[6],h1=state1[7];
    uint32_t a2=state2[0],b2=state2[1],c2=state2[2],d2=state2[3];
    uint32_t e2=state2[4],f2=state2[5],g2=state2[6],h2=state2[7];
    for (int i=0;i<7;i++) {
        uint32_t T1a=(h1+fn_S1(e1)+fn_Ch(e1,f1,g1)+KN[57+i]+W1[i])&MASK;
        uint32_t T2a=(fn_S0(a1)+fn_Maj(a1,b1,c1))&MASK;
        h1=g1;g1=f1;f1=e1;e1=(d1+T1a)&MASK;d1=c1;c1=b1;b1=a1;a1=(T1a+T2a)&MASK;
        uint32_t T1b=(h2+fn_S1(e2)+fn_Ch(e2,f2,g2)+KN[57+i]+W2[i])&MASK;
        uint32_t T2b=(fn_S0(a2)+fn_Maj(a2,b2,c2))&MASK;
        h2=g2;g2=f2;f2=e2;e2=(d2+T1b)&MASK;d2=c2;c2=b2;b2=a2;a2=(T1b+T2b)&MASK;
    }

    /* Pack 8 regs × N bits into uint64_t */
    uint64_t diff = 0;
    diff |= ((uint64_t)((a1^a2)&MASK))<<(0*N);
    diff |= ((uint64_t)((b1^b2)&MASK))<<(1*N);
    diff |= ((uint64_t)((c1^c2)&MASK))<<(2*N);
    diff |= ((uint64_t)((d1^d2)&MASK))<<(3*N);
    diff |= ((uint64_t)((e1^e2)&MASK))<<(4*N);
    diff |= ((uint64_t)((f1^f2)&MASK))<<(5*N);
    diff |= ((uint64_t)((g1^g2)&MASK))<<(6*N);
    diff |= ((uint64_t)((h1^h2)&MASK))<<(7*N);
    return diff;
}

/* xoshiro256** PRNG */
static uint64_t rng_s[4];
static inline uint64_t rng_rotl(uint64_t x, int k) { return (x<<k)|(x>>(64-k)); }
static inline uint64_t rng_next(void) {
    uint64_t result = rng_rotl(rng_s[1]*5,7)*9;
    uint64_t t = rng_s[1]<<17;
    rng_s[2]^=rng_s[0]; rng_s[3]^=rng_s[1]; rng_s[1]^=rng_s[2]; rng_s[0]^=rng_s[3];
    rng_s[2]^=t; rng_s[3]=rng_rotl(rng_s[3],45);
    return result;
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);

    int n_base_points = argc > 1 ? atoi(argv[1]) : 2000;
    int n_dir_sets = argc > 2 ? atoi(argv[2]) : 200;

    /* Init */
    rS0[0]=scale_rot(2); rS0[1]=scale_rot(13); rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6); rS1[1]=scale_rot(11); rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7); rs0[1]=scale_rot(18); ss0=scale_rot(3);
    rs1[0]=scale_rot(17); rs1[1]=scale_rot(19); ss1=scale_rot(10);
    for (int i=0;i<64;i++) KN[i]=K32[i]&MASK;
    for (int i=0;i<8;i++) IVN[i]=IV32[i]&MASK;

    /* Find candidate */
    int found = 0;
    for (uint32_t m0=0; m0<=MASK && !found; m0++) {
        uint32_t M1[16], M2[16];
        for (int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
        M1[0]=m0; M2[0]=m0^MSB; M2[9]=MASK^MSB;
        uint32_t s1[8],s2[8],w1[57],w2[57];
        precompute(M1,s1,w1); precompute(M2,s2,w2);
        if (s1[0]==s2[0]) {
            memcpy(state1,s1,32); memcpy(state2,s2,32);
            memcpy(W1_pre,w1,228); memcpy(W2_pre,w2,228);
            found=1;
            printf("Candidate: M[0]=0x%x (N=%d)\n", m0, N);
        }
    }
    if (!found) { printf("No candidate!\n"); return 1; }

    rng_s[0]=0x12345678; rng_s[1]=0xdeadbeef; rng_s[2]=0xcafebabe; rng_s[3]=0x42424242;

    printf("Higher-Order Differential Scanner (N=%d)\n", N);
    printf("Free bits: %d, Output bits: %d\n", N_FREE, N_OUT);
    printf("Base points: %d, Direction sets per (k, base): %d\n\n", n_base_points, n_dir_sets);

    /* For each order k */
    printf("%-4s", "k");
    for (int b = 0; b < N_OUT; b++) {
        if (b % N == 0) printf(" reg%c", "abcdefgh"[b/N]);
    }
    printf("  avg_zero%%\n");

    for (int k = 1; k <= N_FREE && k <= 32; k++) {
        /* For each output bit, count zero differentials */
        int zero_count[N_OUT];
        int total_count[N_OUT];
        memset(zero_count, 0, sizeof(zero_count));
        memset(total_count, 0, sizeof(total_count));

        for (int bp = 0; bp < n_base_points; bp++) {
            input_t base_x = rng_next() & ((1ULL << N_FREE) - 1);

            for (int ds = 0; ds < n_dir_sets; ds++) {
                /* Generate k random direction vectors */
                input_t dirs[32];
                for (int i = 0; i < k; i++) {
                    /* Each direction is a single random bit position */
                    int pos = rng_next() % N_FREE;
                    dirs[i] = 1ULL << pos;
                }

                /* Compute k-th order differential:
                 * XOR over all 2^k subsets of {d1,...,dk} of f(base + sum(S)) */
                uint64_t diff_accum = 0;
                for (uint32_t subset = 0; subset < (1U << k); subset++) {
                    input_t point = base_x;
                    for (int i = 0; i < k; i++) {
                        if ((subset >> i) & 1) point ^= dirs[i];
                    }
                    diff_accum ^= eval_diff(point);
                }

                /* Check each output bit */
                for (int b = 0; b < N_OUT; b++) {
                    total_count[b]++;
                    if (!((diff_accum >> b) & 1)) {
                        zero_count[b]++;
                    }
                }
            }
        }

        /* Print results for this k */
        double total_zero_pct = 0;
        printf("%-4d", k);
        for (int b = 0; b < N_OUT; b++) {
            double pct = 100.0 * zero_count[b] / total_count[b];
            total_zero_pct += pct;
            if (b % N == 0) {
                /* Print register average */
                double reg_avg = 0;
                for (int bb = b; bb < b + N && bb < N_OUT; bb++) {
                    reg_avg += 100.0 * zero_count[bb] / total_count[bb];
                }
                reg_avg /= N;
                printf(" %4.0f%%", reg_avg);
            }
        }
        total_zero_pct /= N_OUT;
        printf("  %5.1f%%", total_zero_pct);

        /* Flag if significantly above 50% (which would be random baseline) */
        if (total_zero_pct > 60 && k > 1) printf(" ← HIGH");
        if (total_zero_pct > 90) printf(" *** ZERO DIFFERENTIAL ***");
        printf("\n");

        /* Early termination: if all bits are at ~50%, degree > k for all */
        if (k > 4 && total_zero_pct < 52) {
            printf("  (all bits near 50%% at k=%d, degree > %d for all. Continuing...)\n", k, k);
        }

        /* If k > 20 and nothing interesting, we can stop for large k */
        if (k >= 20 && total_zero_pct < 55) {
            printf("  (stopping: no structure found up to k=%d)\n", k);
            break;
        }
    }

    printf("\nDone.\n");
    return 0;
}
