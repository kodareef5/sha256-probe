/*
 * sha256.h — Parametric N-bit SHA-256 primitives
 *
 * Supports both full 32-bit SHA-256 and reduced-width mini-SHA-256
 * for precision homotopy experiments.
 *
 * Usage:
 *   sha256_init(32);  // or sha256_init(16) for mini-SHA
 *   Then all functions use the configured word width.
 */

#ifndef SHA256_H
#define SHA256_H

#include <stdint.h>

/* Global configuration — set by sha256_init() */
extern int sha256_N;
extern uint32_t sha256_MASK;
extern uint32_t sha256_MSB;
extern uint32_t sha256_K[64];
extern uint32_t sha256_IV[8];

/* Rotation amounts (scaled for N-bit) */
extern int sha256_rS0[3], sha256_rS1[3];
extern int sha256_rs0[2], sha256_rs1[2];
extern int sha256_ss0, sha256_ss1;

/* Initialize for N-bit word width. Must call before any other function. */
void sha256_init(int N);

/* Primitives */
static inline uint32_t sha256_ror(uint32_t x, int k) {
    k = k % sha256_N;
    return ((x >> k) | (x << (sha256_N - k))) & sha256_MASK;
}

static inline uint32_t sha256_Sigma0(uint32_t a) {
    return sha256_ror(a, sha256_rS0[0]) ^ sha256_ror(a, sha256_rS0[1]) ^ sha256_ror(a, sha256_rS0[2]);
}

static inline uint32_t sha256_Sigma1(uint32_t e) {
    return sha256_ror(e, sha256_rS1[0]) ^ sha256_ror(e, sha256_rS1[1]) ^ sha256_ror(e, sha256_rS1[2]);
}

static inline uint32_t sha256_sigma0(uint32_t x) {
    return sha256_ror(x, sha256_rs0[0]) ^ sha256_ror(x, sha256_rs0[1]) ^ ((x >> sha256_ss0) & sha256_MASK);
}

static inline uint32_t sha256_sigma1(uint32_t x) {
    return sha256_ror(x, sha256_rs1[0]) ^ sha256_ror(x, sha256_rs1[1]) ^ ((x >> sha256_ss1) & sha256_MASK);
}

static inline uint32_t sha256_Ch(uint32_t e, uint32_t f, uint32_t g) {
    return ((e & f) ^ ((~e) & g)) & sha256_MASK;
}

static inline uint32_t sha256_Maj(uint32_t a, uint32_t b, uint32_t c) {
    return ((a & b) ^ (a & c) ^ (b & c)) & sha256_MASK;
}

static inline int sha256_hw(uint32_t x) {
    return __builtin_popcount(x & sha256_MASK);
}

/* State after 57 rounds */
typedef struct {
    uint32_t state[8];  /* a,b,c,d,e,f,g,h after round 56 */
    uint32_t W[57];     /* schedule words 0..56 */
} sha256_precomp_t;

/* Precompute: run 57 rounds on message M (16 words) */
void sha256_precompute(const uint32_t M[16], sha256_precomp_t *out);

/* Run tail rounds (57..63) given free words. Returns total state diff HW. */
int sha256_eval_tail(const sha256_precomp_t *p1, const sha256_precomp_t *p2,
                     const uint32_t w1_free[4], const uint32_t w2_free[4]);

#endif /* SHA256_H */
