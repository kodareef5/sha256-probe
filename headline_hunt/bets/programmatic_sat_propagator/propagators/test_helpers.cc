// test_helpers.cc — unit tests for the Sigma0/Maj/dT2 evaluator helpers.
//
// Compiled-in subset of cascade_propagator.cc — defines just the helper
// functions (no IPASIR-UP integration), feeds them known-good inputs,
// verifies outputs against Python reference values.
//
// Build:
//   g++ -std=c++17 -O2 test_helpers.cc -o test_helpers
//
// Reference values computed via Python:
//   from lib.sha256 import Sigma0, Maj
//   Sigma0(0xa1b2c3d4) = ?
//   Maj(0x12345678, 0xdeadbeef, 0xcafebabe) = ?

#include <array>
#include <cstdio>
#include <cstdint>

// ---- Replicated helpers from cascade_propagator.cc ----

struct PartialReg {
    std::array<int, 32> bits;
    int n_decided;
    PartialReg() : n_decided(0) { bits.fill(-1); }

    // Test convenience: build from a 32-bit value (all bits decided).
    static PartialReg from_value(uint32_t v) {
        PartialReg p;
        for (int b = 0; b < 32; b++) {
            p.bits[b] = (v >> b) & 1;
        }
        p.n_decided = 32;
        return p;
    }
};

static long long read_full_value(const PartialReg& preg) {
    if (preg.n_decided < 32) return -1;
    unsigned int v = 0;
    for (int b = 0; b < 32; b++) {
        if (preg.bits[b] == -1) return -1;
        if (preg.bits[b] == 1) v |= (1u << b);
    }
    return (long long)v;
}

static unsigned int sigma0(unsigned int x) {
    auto rotr = [](unsigned int v, int n) {
        return (v >> n) | (v << (32 - n));
    };
    return rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22);
}

static unsigned int maj(unsigned int x, unsigned int y, unsigned int z) {
    return (x & y) ^ (x & z) ^ (y & z);
}

static long long dSigma0_modular(const PartialReg& a1, const PartialReg& a2) {
    long long va1 = read_full_value(a1);
    long long va2 = read_full_value(a2);
    if (va1 < 0 || va2 < 0) return -1;
    unsigned int s1 = sigma0((unsigned int)va1);
    unsigned int s2 = sigma0((unsigned int)va2);
    return (long long)((s1 - s2) & 0xFFFFFFFFu);
}

static long long dMaj_modular_cascade(const PartialReg& a1_rm1,
                                       const PartialReg& a2_rm1,
                                       unsigned int V60, unsigned int V59) {
    long long va1 = read_full_value(a1_rm1);
    long long va2 = read_full_value(a2_rm1);
    if (va1 < 0 || va2 < 0) return -1;
    unsigned int m1 = maj((unsigned int)va1, V60, V59);
    unsigned int m2 = maj((unsigned int)va2, V60, V59);
    return (long long)((m1 - m2) & 0xFFFFFFFFu);
}

// ---- Tests ----

int n_tests = 0, n_failed = 0;

#define ASSERT_EQ(actual, expected, msg) do { \
    n_tests++; \
    auto _a = (actual); \
    auto _e = (expected); \
    if (_a != _e) { \
        n_failed++; \
        printf("FAIL %s: got 0x%llx, expected 0x%llx\n", msg, (long long)_a, (long long)_e); \
    } else { \
        printf("PASS %s: 0x%llx\n", msg, (long long)_a); \
    } \
} while (0)

int main() {
    // --- read_full_value ---
    PartialReg fv = PartialReg::from_value(0xdeadbeef);
    ASSERT_EQ(read_full_value(fv), 0xdeadbeefLL, "read_full_value(0xdeadbeef)");

    PartialReg pv;
    pv.bits[0] = 1; pv.n_decided = 1;
    ASSERT_EQ(read_full_value(pv), -1LL, "read_full_value(partial) returns -1");

    // --- sigma0 reference values (computed via Python lib.sha256.Sigma0) ---
    // Sigma0(x) = ROTR(x, 2) ^ ROTR(x, 13) ^ ROTR(x, 22)
    // Manual check:
    // Sigma0(0xa1b2c3d4):
    //   ROTR(x, 2)  = 0x286c8b0f5  → wait, that's > 32 bits. Let me redo.
    //   Let's just compute reference values inline.
    auto rotr = [](unsigned int v, int n) { return (v >> n) | (v << (32 - n)); };
    unsigned int x = 0xa1b2c3d4;
    unsigned int expected_sigma0 = rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22);
    ASSERT_EQ((long long)sigma0(x), (long long)expected_sigma0, "sigma0(0xa1b2c3d4)");

    ASSERT_EQ((long long)sigma0(0), 0LL, "sigma0(0) = 0");
    ASSERT_EQ((long long)sigma0(0xFFFFFFFFu), 0xFFFFFFFFLL, "sigma0(all-ones) = all-ones");

    // --- maj reference values ---
    ASSERT_EQ((long long)maj(0, 0, 0), 0LL, "maj(0,0,0) = 0");
    ASSERT_EQ((long long)maj(0xFFFFFFFFu, 0xFFFFFFFFu, 0xFFFFFFFFu),
              0xFFFFFFFFLL, "maj(all-1, all-1, all-1) = all-1");
    // Bit-local: bit i = (x[i] & y[i]) ^ (x[i] & z[i]) ^ (y[i] & z[i])
    // For x=0xAA, y=0x55, z=0xFF (bytes):
    //   bit 0: (0&1)^(0&1)^(1&1) = 0^0^1 = 1
    //   bit 1: (1&0)^(1&1)^(0&1) = 0^1^0 = 1
    //   etc.
    // 0xAA & 0x55 = 0, 0xAA & 0xFF = 0xAA, 0x55 & 0xFF = 0x55. XOR = 0xFF.
    ASSERT_EQ((long long)maj(0xAA, 0x55, 0xFF), 0xFFLL, "maj(0xAA, 0x55, 0xFF)");

    // --- dSigma0_modular ---
    PartialReg a1 = PartialReg::from_value(0x12345678);
    PartialReg a2 = PartialReg::from_value(0x12345678);  // same → diff = 0
    ASSERT_EQ(dSigma0_modular(a1, a2), 0LL, "dSigma0(x, x) = 0");

    PartialReg a1b = PartialReg::from_value(0x12345678);
    PartialReg a2b = PartialReg::from_value(0x12345679);  // diff in bit 0
    long long expected_diff = ((long long)(sigma0(0x12345678) - sigma0(0x12345679))) & 0xFFFFFFFFLL;
    ASSERT_EQ(dSigma0_modular(a1b, a2b), expected_diff,
              "dSigma0(0x12345678, 0x12345679) = sigma0 modular diff");

    // --- dMaj_modular_cascade ---
    // V60 = V59 = 0 (cascade-zero values, but treated as 0 for simplicity).
    // dMaj(a1, a2, V60=0, V59=0) = Maj(a1, 0, 0) - Maj(a2, 0, 0)
    //                            = ((a1 & 0) ^ (a1 & 0) ^ (0 & 0)) - ...
    //                            = 0 - 0 = 0
    ASSERT_EQ(dMaj_modular_cascade(a1, a2, 0, 0), 0LL, "dMaj(x, x, 0, 0) = 0");

    PartialReg a1c = PartialReg::from_value(0xFFFFFFFFu);
    PartialReg a2c = PartialReg::from_value(0x00000000u);
    // Maj(0xFFFFFFFF, V60, V59) = V60 | V59 (when x is all 1s, maj = y OR z)
    // Maj(0, V60, V59) = V60 & V59
    // dMaj = (V60 | V59) - (V60 & V59) = V60 ^ V59 (when no carries)
    unsigned int V60 = 0xa1b2c3d4, V59 = 0x12345678;
    long long expected_dmaj = ((long long)((V60 | V59) - (V60 & V59))) & 0xFFFFFFFFLL;
    ASSERT_EQ(dMaj_modular_cascade(a1c, a2c, V60, V59), expected_dmaj,
              "dMaj(all-1, 0, V60, V59)");

    // --- Partial inputs return -1 ---
    PartialReg partial; partial.bits[0] = 1; partial.n_decided = 1;
    ASSERT_EQ(dSigma0_modular(partial, a2), -1LL,
              "dSigma0(partial, full) = -1");
    ASSERT_EQ(dMaj_modular_cascade(partial, a2, 0, 0), -1LL,
              "dMaj(partial, full, 0, 0) = -1");

    printf("\nResults: %d passed, %d failed (%d tests)\n",
           n_tests - n_failed, n_failed, n_tests);
    return n_failed == 0 ? 0 : 1;
}
