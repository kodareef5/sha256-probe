/*
 * Script 08: Multi-Candidate Scanner
 *
 * Scans M[1] over 2^32 values (with M[0] fixed at 0x17149975, M[2..15]=0xffffffff)
 * to find additional da[56]=0 candidates with different round-56 states.
 *
 * For each hit, records the full round-56 state and properties:
 *   - Total state diff Hamming weight
 *   - Individual register diff Hamming weights
 *   - M[1] value
 *
 * Can also scan other words by changing SCAN_WORD_IDX.
 *
 * Compile: gcc -O3 -march=native -fopenmp -o scan_multi 08_multi_candidate_scan.c -lm
 * Run:     ./scan_multi [word_idx]   (default: scan M[1])
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

static inline uint32_t ROR(uint32_t x, int n) {
    return (x >> n) | (x << (32 - n));
}

static inline uint32_t Ch(uint32_t e, uint32_t f, uint32_t g) {
    return (e & f) ^ (~e & g);
}

static inline uint32_t Maj(uint32_t a, uint32_t b, uint32_t c) {
    return (a & b) ^ (a & c) ^ (b & c);
}

static inline uint32_t Sigma0(uint32_t a) {
    return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22);
}

static inline uint32_t Sigma1(uint32_t e) {
    return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25);
}

static inline uint32_t sigma0(uint32_t x) {
    return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3);
}

static inline uint32_t sigma1(uint32_t x) {
    return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10);
}

static inline int popcount32(uint32_t x) {
    return __builtin_popcount(x);
}

static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

static const uint32_t IV[8] = {
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
};

typedef struct {
    uint32_t m_val;       /* Value of the scanned word */
    int scan_word;        /* Which word index was scanned */
    uint32_t da, db, dc, dd, de, df, dg, dh; /* State diffs */
    int total_hw;         /* Total Hamming weight of state diff */
} candidate_t;

/* Run 57 rounds and return the state */
static void compress_57(const uint32_t M[16], uint32_t state[8]) {
    uint32_t W[57];
    int i;

    for (i = 0; i < 16; i++) W[i] = M[i];
    for (i = 16; i < 57; i++)
        W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16];

    uint32_t a = IV[0], b = IV[1], c = IV[2], d = IV[3];
    uint32_t e = IV[4], f = IV[5], g = IV[6], h = IV[7];

    for (i = 0; i < 57; i++) {
        uint32_t T1 = h + Sigma1(e) + Ch(e, f, g) + K[i] + W[i];
        uint32_t T2 = Sigma0(a) + Maj(a, b, c);
        h = g; g = f; f = e; e = d + T1;
        d = c; c = b; b = a; a = T1 + T2;
    }

    state[0] = a; state[1] = b; state[2] = c; state[3] = d;
    state[4] = e; state[5] = f; state[6] = g; state[7] = h;
}

int main(int argc, char *argv[]) {
    int scan_word = 1; /* Default: scan M[1] */
    if (argc > 1) scan_word = atoi(argv[1]);

    /* Validate scan word (skip 0 and 9, those are kernel-constrained) */
    if (scan_word == 0 || scan_word == 9 || scan_word < 0 || scan_word > 15) {
        fprintf(stderr, "Invalid scan word %d (must be 1-8 or 10-15, not 0 or 9)\n", scan_word);
        return 1;
    }

    printf("Scanning M[%d] over 2^32 values\n", scan_word);
    printf("M[0] = 0x17149975 (fixed), M[other] = 0xffffffff\n");
    printf("Looking for da[56] = 0 candidates with diverse state properties\n\n");

    candidate_t *candidates = malloc(256 * sizeof(candidate_t));
    int n_candidates = 0;
    int max_candidates = 256;

    time_t start = time(NULL);
    uint64_t count = 0;

    #pragma omp parallel
    {
        uint32_t M1[16], M2[16];
        uint32_t s1[8], s2[8];

        /* Initialize base message */
        M1[0] = 0x17149975;
        for (int i = 1; i < 16; i++) M1[i] = 0xffffffff;

        /* M2 = M1 with MSB kernel */
        memcpy(M2, M1, sizeof(M1));
        M2[0] ^= 0x80000000;
        M2[9] ^= 0x80000000;

        #pragma omp for schedule(dynamic, 1024)
        for (uint64_t val = 0; val < 0x100000000ULL; val++) {
            M1[scan_word] = (uint32_t)val;
            M2[scan_word] = (uint32_t)val;
            /* If scan_word == 9, M2[9] would also need kernel XOR,
               but we excluded 9 above */

            compress_57(M1, s1);
            compress_57(M2, s2);

            if (s1[0] == s2[0]) { /* da[56] = 0 */
                int hw = 0;
                for (int r = 0; r < 8; r++)
                    hw += popcount32(s1[r] ^ s2[r]);

                #pragma omp critical
                {
                    if (n_candidates < max_candidates) {
                        candidate_t *c = &candidates[n_candidates];
                        c->m_val = (uint32_t)val;
                        c->scan_word = scan_word;
                        c->da = s1[0] ^ s2[0];
                        c->db = s1[1] ^ s2[1];
                        c->dc = s1[2] ^ s2[2];
                        c->dd = s1[3] ^ s2[3];
                        c->de = s1[4] ^ s2[4];
                        c->df = s1[5] ^ s2[5];
                        c->dg = s1[6] ^ s2[6];
                        c->dh = s1[7] ^ s2[7];
                        c->total_hw = hw;
                        n_candidates++;

                        printf("  FOUND: M[%d]=0x%08x  total_hw=%d  "
                               "db=%08x dc=%08x dd=%08x de=%08x df=%08x dg=%08x dh=%08x\n",
                               scan_word, (uint32_t)val, hw,
                               c->db, c->dc, c->dd, c->de, c->df, c->dg, c->dh);
                    }
                }
            }

            #pragma omp atomic
            count++;

            /* Progress report every ~500M */
            if (val % 500000000 == 0 && val > 0) {
                #pragma omp critical
                {
                    time_t now = time(NULL);
                    double elapsed = difftime(now, start);
                    double rate = count / elapsed / 1e6;
                    double pct = val * 100.0 / 0x100000000ULL;
                    printf("  Progress: %.0f%% (%lu evals, %.1fM/s, %d found)\n",
                           pct, (unsigned long)count, rate, n_candidates);
                }
            }
        }
    }

    time_t end = time(NULL);
    double elapsed = difftime(end, start);

    printf("\n======================================================================\n");
    printf("RESULTS: Scanning M[%d]\n", scan_word);
    printf("======================================================================\n");
    printf("Total candidates: %d (from 2^32 = 4294967296 evaluations)\n", n_candidates);
    printf("Time: %.0f seconds (%.1fM evals/sec)\n", elapsed, 4294967296.0 / elapsed / 1e6);

    if (n_candidates > 0) {
        /* Sort by total_hw */
        for (int i = 0; i < n_candidates - 1; i++) {
            for (int j = i + 1; j < n_candidates; j++) {
                if (candidates[j].total_hw < candidates[i].total_hw) {
                    candidate_t tmp = candidates[i];
                    candidates[i] = candidates[j];
                    candidates[j] = tmp;
                }
            }
        }

        printf("\nCandidates sorted by total_hw (lower = better for sr=60):\n");
        printf("%-12s %-8s %-8s %-8s %-8s %-8s %-8s %-8s %-8s %s\n",
               "M_val", "hw", "db", "dc", "dd", "de", "df", "dg", "dh", "notes");
        printf("------------------------------------------------------------------------------------\n");
        for (int i = 0; i < n_candidates; i++) {
            candidate_t *c = &candidates[i];
            const char *note = "";
            if (c->total_hw < 80) note = " <-- LOW HW!";
            else if (c->m_val == 0xffffffff) note = " (paper default)";
            printf("0x%08x  %3d    %08x %08x %08x %08x %08x %08x %08x%s\n",
                   c->m_val, c->total_hw,
                   c->db, c->dc, c->dd, c->de, c->df, c->dg, c->dh, note);
        }

        /* Summary statistics */
        int min_hw = candidates[0].total_hw;
        int max_hw = candidates[n_candidates-1].total_hw;
        int sum_hw = 0;
        for (int i = 0; i < n_candidates; i++) sum_hw += candidates[i].total_hw;
        printf("\nHW stats: min=%d, max=%d, mean=%.1f (paper baseline=104)\n",
               min_hw, max_hw, (double)sum_hw / n_candidates);
    }

    free(candidates);
    return 0;
}
