/* Compute exact F_2 rank of the entire g image (XOR-translated to start at 0). */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef _OPENMP
#include <omp.h>
#endif
#define MASK 0xFFFFFFFFU
static inline uint32_t Ch(uint32_t e, uint32_t f, uint32_t g) { return (e & f) ^ (~e & g); }
static inline int hw(uint32_t x) { return __builtin_popcount(x); }

int main() {
    uint32_t f60_M1 = 0x04d3f862, f60_M2 = 0x8f843b05;
    uint32_t g60_M1 = 0xcffab9f4, g60_M2 = 0xc1ce1538;

    uint8_t *seen = calloc((1L << 32) / 8, 1);
    if (!seen) return 1;

    fprintf(stderr, "Computing g image bitmap...\n");
    #pragma omp parallel for
    for (long e_l = 0; e_l < (1L << 32); e_l++) {
        uint32_t e = (uint32_t)e_l;
        uint32_t v = Ch(e, f60_M1, g60_M1) - Ch(e, f60_M2, g60_M2);
        long idx = (long)v >> 3;
        uint8_t bit = 1 << (v & 7);
        #pragma omp atomic
        seen[idx] |= bit;
    }

    /* Find first value */
    uint32_t v0 = 0;
    for (long i = 0; i < (1L << 32); i++) {
        long idx = i >> 3;
        uint8_t bit = 1 << (i & 7);
        if (seen[idx] & bit) { v0 = (uint32_t)i; break; }
    }

    /* Compute F_2 rank of (image XOR v0) by walking through ALL values */
    uint32_t basis[33] = {0};
    int rank = 0;
    long count = 0;

    for (long i = 0; i < (1L << 32); i++) {
        long idx = i >> 3;
        uint8_t bit = 1 << (i & 7);
        if (seen[idx] & bit) {
            count++;
            uint32_t v = (uint32_t)i ^ v0;
            if (v == 0) continue;
            uint32_t r = v;
            for (int b = 31; b >= 0; b--) {
                if ((r >> b) & 1) {
                    if (basis[b] == 0) {
                        basis[b] = r;
                        rank++;
                        break;
                    }
                    r ^= basis[b];
                }
            }
        }
    }

    fprintf(stderr, "Image size: %ld\n", count);
    fprintf(stderr, "F_2 rank of (image XOR v0): %d\n", rank);
    fprintf(stderr, "2^rank = %ld\n", 1L << rank);
    fprintf(stderr, "ratio: %.4f\n", (double)count / (1L << rank));
    
    if (count == (1L << rank)) {
        fprintf(stderr, "*** image is a LINEAR SUBSPACE of dimension %d ***\n", rank);
    } else if ((double)count / (1L << rank) > 0.4 && (double)count / (1L << rank) < 0.6) {
        fprintf(stderr, "*** image is ~half a subspace (1 of 2 cosets?) ***\n");
    } else if ((double)count / (1L << rank) > 0.3 && (double)count / (1L << rank) < 0.4) {
        fprintf(stderr, "*** image is ~1/3 of a subspace (1 of 3 cosets?) ***\n");
    }

    /* Print the basis */
    fprintf(stderr, "\nBasis vectors (in echelon form):\n");
    for (int b = 31; b >= 0; b--) {
        if (basis[b]) fprintf(stderr, "  bit %2d: 0x%08x  hw=%d\n", b, basis[b], hw(basis[b]));
    }

    free(seen);
    return 0;
}
