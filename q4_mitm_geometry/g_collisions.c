/* For each g value, count how many e values map to it. Histogram of preimage sizes. */
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

int main() {
    uint32_t f60_M1 = 0x04d3f862, f60_M2 = 0x8f843b05;
    uint32_t g60_M1 = 0xcffab9f4, g60_M2 = 0xc1ce1538;

    /* Use a hash counter — but 2^32 entries is too many.
     * Instead, sort g(e) values and count runs. */
    /* That's also memory-heavy. Use the bitmap approach + a separate counter. */
    
    /* Better: directly compute preimage size distribution by sorting */
    fprintf(stderr, "Computing g(e) preimage sizes via sort...\n");
    fprintf(stderr, "Allocating 16GB array for g values...\n");
    uint32_t *vals = malloc((1L << 32) * sizeof(uint32_t));
    if (!vals) { fprintf(stderr, "alloc failed\n"); return 1; }
    
    time_t t0 = time(NULL);
    #pragma omp parallel for
    for (long e_l = 0; e_l < (1L << 32); e_l++) {
        uint32_t e = (uint32_t)e_l;
        vals[e] = Ch(e, f60_M1, g60_M1) - Ch(e, f60_M2, g60_M2);
    }
    fprintf(stderr, "Computed in %lds\n", (long)(time(NULL)-t0));

    /* Sort */
    fprintf(stderr, "Sorting...\n");
    t0 = time(NULL);
    /* Naive qsort would be 2^32 * log2(2^32) = ~10^11 ops, too slow.
     * Use counting sort via bitmap-then-walk. */
    
    /* Actually we don't need sort. We need preimage size histogram.
     * Compute via 2-pass: first pass marks values seen, second pass counts.
     * For preimage histogram, we need to count frequency.
     * Use an array of 32-bit counters indexed by hash. */
    
    /* Skip sort approach; build distribution histogram by hash buckets */
    long *bucket = calloc(1L << 24, sizeof(long));  /* hash to 24-bit buckets */
    if (!bucket) { fprintf(stderr, "bucket alloc failed\n"); free(vals); return 1; }
    
    /* Count frequency in 24-bit hash buckets (lossy but informative) */
    for (long i = 0; i < (1L << 32); i++) {
        bucket[vals[i] & 0xffffff]++;
    }
    fprintf(stderr, "Bucketing done in %lds\n", (long)(time(NULL)-t0));
    
    /* Histogram of bucket counts */
    long max_bucket = 0;
    long bucket_sum = 0;
    long nonzero_buckets = 0;
    for (long i = 0; i < (1L << 24); i++) {
        if (bucket[i] > 0) {
            bucket_sum += bucket[i];
            nonzero_buckets++;
            if (bucket[i] > max_bucket) max_bucket = bucket[i];
        }
    }
    fprintf(stderr, "\nNon-empty 24-bit hash buckets: %ld\n", nonzero_buckets);
    fprintf(stderr, "Average preimages per bucket: %.1f\n", (double)bucket_sum / nonzero_buckets);
    fprintf(stderr, "Max preimages per bucket: %ld\n", max_bucket);

    /* Histogram of bucket sizes */
    long size_hist[100] = {0};
    for (long i = 0; i < (1L << 24); i++) {
        long b = bucket[i];
        if (b < 100) size_hist[b]++;
    }
    fprintf(stderr, "\nHistogram of bucket sizes (count of buckets at each size):\n");
    for (int s = 0; s < 50; s++) {
        if (size_hist[s] > 0) fprintf(stderr, "  %d: %ld\n", s, size_hist[s]);
    }

    free(bucket);
    free(vals);
    return 0;
}
