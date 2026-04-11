/*
 * g_func_universality.c — test if g-function 2^20 compression is universal
 *
 * Server found: g(e) = Ch(e, f60_M1, g60_M1) - Ch(e, f60_M2, g60_M2)
 * has image size 1,179,648 = 2^20.2 for the cert round-60 state.
 *
 * This tool tests whether that 2^20 compression is:
 *   (a) a property of the CERT (specific (f60, g60) values)
 *   (b) UNIVERSAL for any random (f60, f60', g60, g60') with certain HW profiles
 *
 * Generates N_TRIALS random tuples with matching HW profiles and computes
 * each image size. Reports the distribution.
 *
 * Compile: gcc -O3 -march=native -fopenmp -o /tmp/gfu q4_mitm_geometry/g_func_universality.c
 * Run: /tmp/gfu [n_trials]
 */
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

/* Compute image size of g(e) = Ch(e, f1, g1) - Ch(e, f2, g2) over all 2^32 e */
long compute_image_size(uint32_t f1, uint32_t f2, uint32_t g1, uint32_t g2) {
    uint8_t *seen = calloc((1L << 32) / 8, 1);
    if (!seen) return -1;

    #pragma omp parallel for
    for (long e_l = 0; e_l < (1L << 32); e_l++) {
        uint32_t e = (uint32_t)e_l;
        uint32_t v = Ch(e, f1, g1) - Ch(e, f2, g2);
        long idx = (long)v >> 3;
        uint8_t bit = 1 << (v & 7);
        #pragma omp atomic
        seen[idx] |= bit;
    }

    long distinct = 0;
    for (long v_l = 0; v_l < (1L << 32); v_l++) {
        long idx = v_l >> 3;
        uint8_t bit = 1 << (v_l & 7);
        if (seen[idx] & bit) distinct++;
    }

    free(seen);
    return distinct;
}

int main(int argc, char **argv) {
    int n_trials = argc > 1 ? atoi(argv[1]) : 10;

    printf("=== g-function universality test ===\n");
    printf("Testing image size distribution for %d random (f1,f2,g1,g2) tuples\n", n_trials);
    printf("Reference: cert has image size 1,179,648 = 2^20.2\n\n");

    /* Cert values for reference */
    uint32_t cert_f1 = 0x04d3f862, cert_f2 = 0x8f843b05;
    uint32_t cert_g1 = 0xcffab9f4, cert_g2 = 0xc1ce1538;

    printf("[REF] cert  : f_xor hw=%d g_xor hw=%d\n",
           hw(cert_f1^cert_f2), hw(cert_g1^cert_g2));
    time_t tref = time(NULL);
    long cert_img = compute_image_size(cert_f1, cert_f2, cert_g1, cert_g2);
    printf("[REF] cert image: %ld (%.4f%%, 2^%.2f)  [%lds]\n\n",
           cert_img, 100.0*cert_img/(double)(1L<<32),
           cert_img > 0 ? __builtin_log2(cert_img) : 0.0, (long)(time(NULL)-tref));
    fflush(stdout);

    srand(42);
    long min_img = cert_img, max_img = cert_img;
    double sum_log = 0;
    int n_below_cert = 0;

    for (int trial = 0; trial < n_trials; trial++) {
        /* Random (f1, f2, g1, g2) */
        uint32_t f1 = (rand()&0xffff) | ((rand()&0xffff)<<16);
        uint32_t f2 = (rand()&0xffff) | ((rand()&0xffff)<<16);
        uint32_t g1 = (rand()&0xffff) | ((rand()&0xffff)<<16);
        uint32_t g2 = (rand()&0xffff) | ((rand()&0xffff)<<16);

        time_t t0 = time(NULL);
        long img = compute_image_size(f1, f2, g1, g2);
        time_t t1 = time(NULL);

        printf("[%3d] f_xor hw=%d g_xor hw=%d -> image=%ld (%.4f%%, 2^%.2f) [%lds]\n",
               trial, hw(f1^f2), hw(g1^g2), img,
               100.0*img/(double)(1L<<32),
               img > 0 ? __builtin_log2(img) : 0.0,
               (long)(t1-t0));
        fflush(stdout);

        if (img < min_img) min_img = img;
        if (img > max_img) max_img = img;
        sum_log += __builtin_log2(img);
        if (img < cert_img) n_below_cert++;
    }

    printf("\n=== Summary ===\n");
    printf("Cert image:   %ld (2^%.2f)\n", cert_img, __builtin_log2(cert_img));
    printf("Min image:    %ld (2^%.2f)\n", min_img, __builtin_log2(min_img));
    printf("Max image:    %ld (2^%.2f)\n", max_img, __builtin_log2(max_img));
    printf("Mean log2(img): %.2f\n", sum_log / n_trials);
    printf("Images below cert: %d of %d\n", n_below_cert, n_trials);
    printf("\nInterpretation:\n");
    printf("  If cert image is typical: compression is universal, not special\n");
    printf("  If cert image is small outlier: cert is specifically structured\n");

    return 0;
}
