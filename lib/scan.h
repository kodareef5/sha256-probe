/*
 * scan.h — Fast candidate scanner for da[56]=0
 *
 * Finds M[0] values where the MSB kernel produces da[56]=0
 * at the configured word width. Tests multiple fill patterns.
 */

#ifndef SCAN_H
#define SCAN_H

#include "sha256.h"

typedef struct {
    uint32_t m0;
    uint32_t fill;
    sha256_precomp_t p1;
    sha256_precomp_t p2;
} scan_candidate_t;

/*
 * Find up to max_candidates da[56]=0 candidates.
 * Tests multiple fill patterns and scans M[0] up to min(2^N, 2^20).
 * Returns number found.
 */
int scan_find_candidates(scan_candidate_t *out, int max_candidates);

#endif /* SCAN_H */
