/*
 * scan.c — Fast candidate scanner implementation
 */

#include "scan.h"
#include <string.h>

int scan_find_candidates(scan_candidate_t *out, int max_candidates) {
    uint32_t MK = sha256_MASK;
    uint32_t MSB = sha256_MSB;

    uint32_t fills[] = {MK, 0, MK>>1, MSB, 0x55&MK, 0xAA&MK,
                        0x33&MK, 0xCC&MK, 0x0F&MK, 0xF0&MK};
    int n_fills = 10;
    int found = 0;

    for (int fi = 0; fi < n_fills && found < max_candidates; fi++) {
        uint32_t fill = fills[fi];
        uint32_t max_m0 = MK < (1U << 20) ? MK : (1U << 20) - 1;

        for (uint32_t m0 = 0; m0 <= max_m0 && found < max_candidates; m0++) {
            uint32_t M1[16], M2[16];
            for (int i = 0; i < 16; i++) { M1[i] = fill; M2[i] = fill; }
            M1[0] = m0;
            M2[0] = m0 ^ MSB;
            M2[9] = (fill ^ MSB) & MK;

            sha256_precomp_t p1, p2;
            sha256_precompute(M1, &p1);
            sha256_precompute(M2, &p2);

            if (p1.state[0] == p2.state[0]) {
                out[found].m0 = m0;
                out[found].fill = fill;
                out[found].p1 = p1;
                out[found].p2 = p2;
                found++;
            }
        }
    }
    return found;
}
