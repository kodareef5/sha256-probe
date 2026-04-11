/* Investigate the 3-fold structure of g's image.
 * Hypothesis: 49152 = 3 × 2^14 means image partitions into 3 cosets of a 2^14 subspace,
 * OR has 14-bit linear part + 1 bit + 1 trit (yes/no/maybe).
 *
 * Test:
 * 1. Compute the XOR closure of g's image (smallest XOR-closed set containing it)
 * 2. If image is XOR-closed, it's a linear subspace -> dimension log2(size)
 * 3. If image / image (XOR) gives 3 elements, it's a 3-coset structure
 * 4. Compute differences and see if they form a smaller subspace */
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

    /* Compute g image as bitmap */
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

    /* Test: pick first value v0 in image. For each other value v in image,
     * compute v XOR v0 (this gives the "difference set" centered at v0).
     * If image is a coset of a linear subspace, the differences form a subspace. */
    
    /* Find first nonzero value */
    uint32_t v0 = 0;
    int found = 0;
    for (long i = 0; i < (1L << 32) && !found; i++) {
        long idx = i >> 3;
        uint8_t bit = 1 << (i & 7);
        if (seen[idx] & bit) {
            v0 = (uint32_t)i;
            found = 1;
        }
    }
    fprintf(stderr, "Reference value v0 = 0x%08x\n\n", v0);

    /* Now compute the differences set (image XOR v0) */
    uint8_t *diff_set = calloc((1L << 32) / 8, 1);
    if (!diff_set) { free(seen); return 1; }

    long count = 0;
    for (long i = 0; i < (1L << 32); i++) {
        long idx = i >> 3;
        uint8_t bit = 1 << (i & 7);
        if (seen[idx] & bit) {
            uint32_t d = (uint32_t)i ^ v0;
            long didx = (long)d >> 3;
            uint8_t dbit = 1 << (d & 7);
            diff_set[didx] |= dbit;
            count++;
        }
    }
    fprintf(stderr, "Image size: %ld\n", count);

    /* Test: compute the F_2 rank of the difference set.
     * If it's a linear subspace, rank = log2(set size).
     * Pick a "basis" by greedy: walk through set, add elements that aren't in span. */
    
    /* For 49152 = 3 × 2^14, expected rank is 14 if subspace, or 15 if 3-coset of 2^14 subspace */
    
    /* Quick test: collect first 100 nonzero diffs and check span */
    uint32_t diffs[100];
    int n_diffs = 0;
    for (long i = 1; i < (1L << 32) && n_diffs < 100; i++) {
        long idx = i >> 3;
        uint8_t bit = 1 << (i & 7);
        if (diff_set[idx] & bit) {
            diffs[n_diffs++] = (uint32_t)i;
        }
    }
    fprintf(stderr, "\nFirst 20 differences from v0:\n");
    for (int i = 0; i < 20 && i < n_diffs; i++) {
        fprintf(stderr, "  0x%08x  hw=%d\n", diffs[i], hw(diffs[i]));
    }

    /* Compute F_2 rank of these diffs */
    uint32_t basis[32] = {0};
    int rank = 0;
    for (int i = 0; i < n_diffs; i++) {
        uint32_t v = diffs[i];
        for (int b = 31; b >= 0; b--) {
            if ((v >> b) & 1) {
                if (basis[b] == 0) {
                    basis[b] = v;
                    rank++;
                    break;
                }
                v ^= basis[b];
            }
        }
    }
    fprintf(stderr, "\nF_2 rank of first %d differences: %d\n", n_diffs, rank);

    /* Sample 10000 differences and recompute rank */
    n_diffs = 0;
    long stride = 5;
    for (long i = 1; i < (1L << 32) && n_diffs < 10000; i += stride) {
        long idx = i >> 3;
        uint8_t bit = 1 << (i & 7);
        if (diff_set[idx] & bit) {
            uint32_t v = (uint32_t)i;
            n_diffs++;
            for (int b = 31; b >= 0; b--) {
                if ((v >> b) & 1) {
                    if (basis[b] == 0) {
                        basis[b] = v;
                        rank++;
                        break;
                    }
                    v ^= basis[b];
                }
            }
            if (rank == 32) break;
        }
    }
    fprintf(stderr, "F_2 rank with %d sampled differences: %d\n", n_diffs, rank);

    /* If rank < 32, the set lives in a subspace.
     * 49152 = 3 × 2^14 -> if linear it's rank 14 (size 16384) which doesn't match
     * Actually if rank=14 then size = 16384, but we have 49152 = 3*16384.
     * So image is union of 3 cosets of a 14-dim subspace. */

    free(seen);
    free(diff_set);
    return 0;
}
