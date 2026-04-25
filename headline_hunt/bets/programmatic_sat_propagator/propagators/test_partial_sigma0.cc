// test_partial_sigma0.cc — partial-bit Sigma0 + dSigma0 evaluator with tests.
//
// Build:  g++ -std=c++17 -O2 test_partial_sigma0.cc -o test_partial_sigma0
//
// Combines:
//   1. Bit-local Sigma0 evaluation (XOR of 3 rotations is bit-local; each
//      output bit needs 3 specific input bits decided).
//   2. Modular subtraction with borrow chain (from test_modular_sub.cc) to
//      compute dSigma0 = Sigma0(a1) - Sigma0(a2) mod 2^32.

#include <array>
#include <cstdio>
#include <cstdint>

struct PartialReg {
    std::array<int, 32> bits;
    int n_decided;
    PartialReg() : n_decided(0) { bits.fill(-1); }
    static PartialReg from_value(uint32_t v) {
        PartialReg p;
        for (int b = 0; b < 32; b++) p.bits[b] = (v >> b) & 1;
        p.n_decided = 32;
        return p;
    }
};

uint32_t to_value(const PartialReg& p) {
    uint32_t v = 0;
    for (int i = 0; i < 32; i++) {
        if (p.bits[i] == 1) v |= (1u << i);
    }
    return v;
}

// Bit-local Sigma0 evaluation. Returns a PartialReg where output bit i is
// determined iff input bits (i+2)%32, (i+13)%32, (i+22)%32 are all decided.
//
// Sigma0(x) = ROTR(x, 2) ^ ROTR(x, 13) ^ ROTR(x, 22)
// Bit i of Sigma0(x) = x[(i+2)%32] ^ x[(i+13)%32] ^ x[(i+22)%32]
PartialReg partial_sigma0(const PartialReg& a) {
    PartialReg r;
    for (int i = 0; i < 32; i++) {
        int b1 = a.bits[(i + 2) % 32];
        int b2 = a.bits[(i + 13) % 32];
        int b3 = a.bits[(i + 22) % 32];
        if (b1 == -1 || b2 == -1 || b3 == -1) continue;
        r.bits[i] = b1 ^ b2 ^ b3;
        r.n_decided++;
    }
    return r;
}

// Bit-local Maj(a, b, c) = (a & b) ^ (a & c) ^ (b & c).
// Each output bit depends only on the SAME bit position of all 3 inputs.
PartialReg partial_maj(const PartialReg& a, const PartialReg& b, const PartialReg& c) {
    PartialReg r;
    for (int i = 0; i < 32; i++) {
        int ai = a.bits[i], bi = b.bits[i], ci = c.bits[i];
        if (ai == -1 || bi == -1 || ci == -1) continue;
        r.bits[i] = (ai & bi) ^ (ai & ci) ^ (bi & ci);
        r.n_decided++;
    }
    return r;
}

// Partial-bit modular subtraction with borrow chain (from test_modular_sub.cc).
// Bit i is determined iff bits 0..i of BOTH a and b are determined.
PartialReg partial_modular_sub(const PartialReg& a, const PartialReg& b) {
    PartialReg r;
    int borrow = 0;
    for (int i = 0; i < 32; i++) {
        if (a.bits[i] == -1 || b.bits[i] == -1) break;
        int diff = a.bits[i] - b.bits[i] - borrow;
        if (diff < 0) { r.bits[i] = diff + 2; borrow = 1; }
        else          { r.bits[i] = diff;     borrow = 0; }
        r.n_decided++;
    }
    return r;
}

// dSigma0 modular = Sigma0(a1) - Sigma0(a2) mod 2^32, partial-bit aware.
// A bit of the result requires:
//   - Bits {0..i} of Sigma0(a1) determined (each requiring 3 input bits of a1)
//   - Same for Sigma0(a2)
PartialReg partial_dSigma0_modular(const PartialReg& a1, const PartialReg& a2) {
    return partial_modular_sub(partial_sigma0(a1), partial_sigma0(a2));
}

// dMaj modular cascade — pair-2 inputs (V60, V59) are CASCADE-EQUAL to pair-1.
// Treats V60, V59 as fully-known constants (cascade has been established).
PartialReg partial_dMaj_modular_cascade(const PartialReg& a1_rm1,
                                         const PartialReg& a2_rm1,
                                         const PartialReg& V60,
                                         const PartialReg& V59) {
    PartialReg maj1 = partial_maj(a1_rm1, V60, V59);
    PartialReg maj2 = partial_maj(a2_rm1, V60, V59);
    return partial_modular_sub(maj1, maj2);
}

// ---- Tests ----

int n_tests = 0, n_failed = 0;

#define ASSERT_EQ(actual, expected, msg) do { \
    n_tests++; \
    auto _a = (actual); auto _e = (expected); \
    if (_a != _e) { \
        n_failed++; \
        printf("FAIL %s: got 0x%x, expected 0x%x\n", msg, (unsigned)_a, (unsigned)_e); \
    } else { printf("PASS %s: 0x%x\n", msg, (unsigned)_a); } \
} while (0)

#define ASSERT_PARTIAL(reg, expected_n, msg) do { \
    n_tests++; \
    if ((reg).n_decided != expected_n) { \
        n_failed++; \
        printf("FAIL %s: n_decided=%d, expected %d\n", msg, (reg).n_decided, expected_n); \
    } else { printf("PASS %s: n_decided=%d\n", msg, (reg).n_decided); } \
} while (0)

uint32_t reference_sigma0(uint32_t x) {
    auto rotr = [](uint32_t v, int n) { return (v >> n) | (v << (32 - n)); };
    return rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22);
}

int main() {
    // partial_sigma0 full input → full output
    {
        uint32_t x = 0xa1b2c3d4;
        PartialReg pr = partial_sigma0(PartialReg::from_value(x));
        ASSERT_PARTIAL(pr, 32, "Sigma0 full input: n_decided");
        ASSERT_EQ(to_value(pr), reference_sigma0(x), "Sigma0(0xa1b2c3d4)");
    }

    // partial_sigma0 single bit decided → 0 output bits decided
    // (because each output bit needs 3 input bits, none of which are likely
    //  to coincidentally only depend on the one decided input).
    {
        PartialReg a;
        a.bits[0] = 1; a.n_decided = 1;
        PartialReg pr = partial_sigma0(a);
        ASSERT_PARTIAL(pr, 0, "Sigma0 with only bit 0 decided: n_decided=0");
    }

    // partial_sigma0 with the 3 bits needed for output bit 0 decided
    // Output bit 0 of Sigma0(x) = x[2] ^ x[13] ^ x[22]
    {
        PartialReg a;
        a.bits[2] = 1; a.bits[13] = 0; a.bits[22] = 1;
        a.n_decided = 3;
        PartialReg pr = partial_sigma0(a);
        ASSERT_PARTIAL(pr, 1, "Sigma0 with 3 bits decided (2,13,22): n_decided=1");
        // Expected output bit 0 = 1 ^ 0 ^ 1 = 0
        if (pr.bits[0] != 0) {
            printf("  FAIL: bit 0 = %d, expected 0\n", pr.bits[0]);
            n_failed++;
        } else {
            printf("PASS Sigma0 bit 0 with min input: 0\n");
            n_tests++;
        }
    }

    // partial_dSigma0_modular full inputs
    {
        uint32_t a = 0x12345678, b = 0x12345679;
        PartialReg pr = partial_dSigma0_modular(
            PartialReg::from_value(a), PartialReg::from_value(b));
        uint32_t expected = (reference_sigma0(a) - reference_sigma0(b)) & 0xFFFFFFFFu;
        ASSERT_EQ(to_value(pr), expected, "dSigma0 modular full input");
        ASSERT_PARTIAL(pr, 32, "dSigma0 modular full: n_decided=32");
    }

    // partial_dSigma0_modular when a1 == a2 (full input): dSigma0 = 0
    {
        PartialReg same = PartialReg::from_value(0xdeadbeef);
        PartialReg pr = partial_dSigma0_modular(same, same);
        ASSERT_EQ(to_value(pr), 0u, "dSigma0(x, x) = 0");
        ASSERT_PARTIAL(pr, 32, "dSigma0(x, x) full: n_decided=32");
    }

    // partial_maj — fully decided inputs
    {
        uint32_t x = 0xAA, y = 0x55, z = 0xFF;
        PartialReg pr = partial_maj(
            PartialReg::from_value(x), PartialReg::from_value(y),
            PartialReg::from_value(z));
        // Reference: (0xAA & 0x55) ^ (0xAA & 0xFF) ^ (0x55 & 0xFF) = 0 ^ 0xAA ^ 0x55 = 0xFF
        ASSERT_EQ(to_value(pr), 0xFFu, "Maj(0xAA, 0x55, 0xFF) = 0xFF");
    }

    // partial_dMaj_modular_cascade with cascade-equal V60, V59
    {
        PartialReg a1 = PartialReg::from_value(0xFFFFFFFFu);
        PartialReg a2 = PartialReg::from_value(0x00000000u);
        PartialReg V60 = PartialReg::from_value(0xa1b2c3d4);
        PartialReg V59 = PartialReg::from_value(0x12345678);
        PartialReg pr = partial_dMaj_modular_cascade(a1, a2, V60, V59);
        // Maj(all-1, V60, V59) = V60 | V59
        // Maj(0, V60, V59) = V60 & V59
        // dMaj = (V60 | V59) - (V60 & V59)
        uint32_t expected = ((to_value(V60) | to_value(V59)) - (to_value(V60) & to_value(V59))) & 0xFFFFFFFFu;
        ASSERT_EQ(to_value(pr), expected, "dMaj_cascade(all-1, 0, V60, V59)");
    }

    // Partial-bit dSigma0: low 4 input bits → output partial
    // Bit 0 of Sigma0 needs bits 2, 13, 22 — only have bits 0..3
    // → no output bit determined
    {
        PartialReg a1, a2;
        for (int i = 0; i < 4; i++) {
            a1.bits[i] = 1;  a2.bits[i] = 0;
        }
        a1.n_decided = 4;  a2.n_decided = 4;
        PartialReg pr = partial_dSigma0_modular(a1, a2);
        ASSERT_PARTIAL(pr, 0, "dSigma0 with only bits 0..3 of inputs: n_decided=0");
    }

    printf("\nResults: %d passed, %d failed (%d tests)\n",
           n_tests - n_failed, n_failed, n_tests);
    return n_failed == 0 ? 0 : 1;
}
