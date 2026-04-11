/* Compute g(e60) image with proper bitmap. */
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
    /* Cert prefix state at round 60 */
    uint32_t f60_M1 = 0x04d3f862, f60_M2 = 0x8f843b05;
    uint32_t g60_M1 = 0xcffab9f4, g60_M2 = 0xc1ce1538;
    /* From cert dh59, dT2: these add a constant offset that doesn't affect image structure */

    fprintf(stderr, "Cert state60 reg values:\n");
    fprintf(stderr, "  f60_M1 = 0x%08x  f60_M2 = 0x%08x  diff: 0x%08x\n", f60_M1, f60_M2, f60_M1^f60_M2);
    fprintf(stderr, "  g60_M1 = 0x%08x  g60_M2 = 0x%08x  diff: 0x%08x\n\n", g60_M1, g60_M2, g60_M1^g60_M2);

    uint8_t *seen = calloc((1L << 32) / 8, 1);
    if (!seen) { fprintf(stderr, "calloc failed\n"); return 1; }

    fprintf(stderr, "Computing image of g(e) = Ch(e, f1, g1) - Ch(e, f2, g2) over 2^32...\n");
    time_t t0 = time(NULL);

    #pragma omp parallel for
    for (long e_l = 0; e_l < (1L << 32); e_l++) {
        uint32_t e = (uint32_t)e_l;
        uint32_t v = Ch(e, f60_M1, g60_M1) - Ch(e, f60_M2, g60_M2);
        long idx = (long)v >> 3;
        uint8_t bit = 1 << (v & 7);
        #pragma omp atomic
        seen[idx] |= bit;
    }

    time_t t1 = time(NULL);
    fprintf(stderr, "Computed in %lds\n", (long)(t1-t0));

    /* Count distinct */
    long distinct = 0;
    uint32_t and_mask = MASK, or_mask = 0;
    for (long v_l = 0; v_l < (1L << 32); v_l++) {
        long idx = v_l >> 3;
        uint8_t bit = 1 << (v_l & 7);
        if (seen[idx] & bit) {
            distinct++;
            and_mask &= (uint32_t)v_l;
            or_mask |= (uint32_t)v_l;
        }
    }

    fprintf(stderr, "\nDistinct g(e) values: %ld\n", distinct);
    fprintf(stderr, "Image fraction: %.4f%% of 2^32\n", 100.0 * distinct / (double)(1L << 32));
    fprintf(stderr, "AND mask: 0x%08x  (%d bits always 1)\n", and_mask, hw(and_mask));
    fprintf(stderr, "OR mask:  0x%08x  (%d bits always 0)\n", or_mask, hw(~or_mask & MASK));

    /* Bit positions where Ch differs from Ch */
    /* dCh = (e & f1) - (e & f2) + (~e & g1) - (~e & g2)
     *     = e & (f1 - f2) + ~e & (g1 - g2)  [if no carries, but there are]
     * Actually integer differences are complicated. */
    fprintf(stderr, "\nf1 XOR f2: 0x%08x (hw=%d)\n", f60_M1 ^ f60_M2, hw(f60_M1 ^ f60_M2));
    fprintf(stderr, "g1 XOR g2: 0x%08x (hw=%d)\n", g60_M1 ^ g60_M2, hw(g60_M1 ^ g60_M2));

    free(seen);
    return 0;
}
