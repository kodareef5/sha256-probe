/* dw_xor_kernel.c — compute XOR differential schedule for a kernel.
 *
 * For SHA-256, the schedule W[k] for k>=16 is:
 *   W[k] = sigma1(W[k-2]) + W[k-7] + sigma0(W[k-15]) + W[k-16]
 *
 * Modular addition makes this NONLINEAR in W. But XOR differentials
 * are LINEAR over GF(2):
 *   dW^XOR[k] = sigma1(dW^XOR[k-2]) XOR dW^XOR[k-7]
 *               XOR sigma0(dW^XOR[k-15]) XOR dW^XOR[k-16]
 * (because sigma0 and sigma1 are XOR of rotations + shift = GF(2)-linear)
 *
 * For a kernel with dM[0]=mask, dM[9]=mask, dM[others]=0:
 *   dW^XOR[0..15] is the kernel difference vector.
 *   dW^XOR[16..63] is computed by the linear recurrence.
 *
 * This is a LOWER BOUND on the modular dW: modular dW XOR = XOR dW
 * (so the same bits MUST differ). Modular dW may also have additional
 * carry-induced bits.
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

typedef uint32_t u32;

static inline u32 ROR(u32 x, int n) { return (x >> n) | (x << (32 - n)); }
static inline u32 sigma0_(u32 x) { return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3); }
static inline u32 sigma1_(u32 x) { return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10); }

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s kernel_bit\n", argv[0]);
        return 1;
    }
    int bit = atoi(argv[1]);
    u32 mask = (u32)1 << bit;

    u32 dW[64];
    for (int i = 0; i < 16; i++) dW[i] = 0;
    dW[0] = mask;
    dW[9] = mask;

    for (int k = 16; k < 64; k++) {
        dW[k] = sigma1_(dW[k-2]) ^ dW[k-7] ^ sigma0_(dW[k-15]) ^ dW[k-16];
    }

    printf("=== Kernel bit=%d (dM[0]=dM[9]=0x%08x) ===\n", bit, mask);
    printf("dW^XOR schedule (k=0..63):\n");
    for (int k = 0; k < 64; k++) {
        int hw = __builtin_popcount(dW[k]);
        printf("  dW[%2d] = 0x%08x  HW=%d%s\n", k, dW[k], hw,
               (k >= 57 && k <= 63) ? "  <-- cascade-1 target slot" : "");
    }

    /* Summary HW for cascade-target slots */
    int total_hw = 0;
    for (int k = 57; k <= 63; k++) total_hw += __builtin_popcount(dW[k]);
    printf("\nTotal HW across slots 57..63: %d (max possible 7*32=224)\n", total_hw);
    return 0;
}
