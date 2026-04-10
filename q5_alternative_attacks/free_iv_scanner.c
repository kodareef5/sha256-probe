/*
 * free_iv_scanner.c — Joint (IV, M[0]) scanner for free-IV sr=60.
 *
 * For each random IV, scan M[0] values for da[56]=0 candidates and
 * record the state HW. Look for (IV, M[0]) pairs with HW < 80 (default
 * IV gives 104).
 *
 * Compile: gcc -O3 -march=native -fopenmp -o /tmp/free_iv_scan q5_alternative_attacks/free_iv_scanner.c
 * Run: /tmp/free_iv_scan [n_ivs] [m0_per_iv]
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
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

static const uint32_t K[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

/* Compute state at round 56 with given IV and message. */
static void compress_to_56(const uint32_t M[16], const uint32_t IV[8], uint32_t state[8]) {
    uint32_t W[57];
    for (int i = 0; i < 16; i++) W[i] = M[i];
    for (int i = 16; i < 57; i++)
        W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16];

    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = h + Sigma1(e) + Ch(e,f,g) + K[i] + W[i];
        uint32_t T2 = Sigma0(a) + Maj(a,b,c);
        h=g; g=f; f=e; e=d+T1; d=c; c=b; b=a; a=T1+T2;
    }
    state[0]=a; state[1]=b; state[2]=c; state[3]=d;
    state[4]=e; state[5]=f; state[6]=g; state[7]=h;
}

static uint64_t xorshift_state = 0x123456789abcdef0ULL;
static uint64_t xorshift64(uint64_t *s) {
    *s ^= *s << 13;
    *s ^= *s >> 7;
    *s ^= *s << 17;
    return *s;
}

int main(int argc, char **argv) {
    long n_ivs = argc > 1 ? atol(argv[1]) : 100;
    long m0_per_iv = argc > 2 ? atol(argv[2]) : 1000000L;
    uint32_t fill = argc > 3 ? (uint32_t)strtoul(argv[3], NULL, 16) : 0xffffffff;

    fprintf(stderr, "Free-IV joint scanner\n");
    fprintf(stderr, "IVs: %ld, M[0] per IV: %ld\n", n_ivs, m0_per_iv);
    fprintf(stderr, "Fill: 0x%08x\n", fill);
    fprintf(stderr, "Total: %ld pairs\n\n", n_ivs * m0_per_iv);

    /* Default SHA-256 IV for comparison */
    const uint32_t default_IV[8] = {
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    };
    fprintf(stderr, "Default IV state HW for known cert: should be 104\n\n");

    long total_hits = 0;
    int best_hw = 256;
    uint32_t best_iv[8] = {0};
    uint32_t best_m0 = 0;

    time_t t0 = time(NULL);

    #pragma omp parallel for reduction(+:total_hits)
    for (long iv_idx = 0; iv_idx < n_ivs; iv_idx++) {
        /* Generate a unique IV per iteration */
        uint64_t seed = (uint64_t)iv_idx * 0x9E3779B97F4A7C15ULL + 0xDEADBEEFCAFEBABEULL;
        uint32_t IV[8];
        for (int j = 0; j < 8; j++) {
            seed ^= seed << 13; seed ^= seed >> 7; seed ^= seed << 17;
            IV[j] = (uint32_t)(seed & MASK);
        }

        for (long m0v = 0; m0v < m0_per_iv; m0v++) {
            uint32_t m0 = (uint32_t)m0v;
            uint32_t M1[16], M2[16];
            M1[0] = m0;
            for (int i = 1; i < 16; i++) M1[i] = fill;
            memcpy(M2, M1, sizeof(M2));
            M2[0] ^= 0x80000000;
            M2[9] ^= 0x80000000;

            uint32_t s1[8], s2[8];
            compress_to_56(M1, IV, s1);
            compress_to_56(M2, IV, s2);

            if (s1[0] != s2[0]) continue;

            int hw_total = 0;
            for (int r = 0; r < 8; r++) hw_total += hw(s1[r] ^ s2[r]);
            total_hits++;

            if (hw_total < best_hw) {
                #pragma omp critical
                {
                    if (hw_total < best_hw) {
                        best_hw = hw_total;
                        memcpy(best_iv, IV, sizeof(IV));
                        best_m0 = m0;
                        time_t now = time(NULL);
                        fprintf(stderr, "[iv %ld, m0 0x%08x, %lds] NEW BEST HW=%d\n",
                                iv_idx, m0, (long)(now-t0), hw_total);
                        fprintf(stderr, "  IV = ");
                        for (int j = 0; j < 8; j++) fprintf(stderr, "%08x ", IV[j]);
                        fprintf(stderr, "\n");
                    }
                }
            }
        }
    }

    time_t t1 = time(NULL);
    fprintf(stderr, "\nDone in %lds\n", (long)(t1 - t0));
    fprintf(stderr, "Total da[56]=0 hits: %ld\n", total_hits);
    fprintf(stderr, "Best HW: %d (vs default IV 104)\n", best_hw);
    if (best_hw < 256) {
        printf("BEST_IV: ");
        for (int j = 0; j < 8; j++) printf("%08x ", best_iv[j]);
        printf("\nBEST_M0: 0x%08x\nBEST_HW: %d\n", best_m0, best_hw);
    }

    return 0;
}
