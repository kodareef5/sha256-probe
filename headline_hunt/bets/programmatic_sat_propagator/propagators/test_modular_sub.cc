// test_modular_sub.cc — standalone unit tests for partial-bit modular
// subtraction with borrow-chain reasoning.
//
// Build:  g++ -std=c++17 -O2 test_modular_sub.cc -o test_modular_sub
//
// This is the missing piece that unblocks partial-bit Rule 4 propagation.
// Function: given two PartialRegs a and b (each bit ∈ {-1, 0, 1}), compute
// the modular difference (a - b) mod 2^32 bit-by-bit, where:
//   - Bit i of (a-b) is determined when bits 0..i of BOTH a and b are
//     determined (so the borrow chain from low to high can propagate).
//   - If any earlier bit is undetermined, all higher bits are also undetermined.
//
// This is the FUNDAMENTAL helper for:
//   - dSigma0 modular: subtract two Sigma0 values with partial knowledge
//   - dMaj modular: same
//   - dT2_r = dSigma0 + dMaj: modular addition (analogous, with carries)
//   - Forcing dE[r] = dA[r] - dT2_r modular when dA, dT2 are partially known

#include <array>
#include <cstdio>
#include <cstdint>

struct PartialReg {
    std::array<int, 32> bits;  // -1 unassigned, 0 false, 1 true
    int n_decided;
    PartialReg() : n_decided(0) { bits.fill(-1); }
    static PartialReg from_value(uint32_t v) {
        PartialReg p;
        for (int b = 0; b < 32; b++) p.bits[b] = (v >> b) & 1;
        p.n_decided = 32;
        return p;
    }
    static PartialReg low_bits(uint32_t v, int n_low) {
        PartialReg p;
        for (int b = 0; b < n_low; b++) p.bits[b] = (v >> b) & 1;
        p.n_decided = n_low;
        return p;
    }
};

// Compute (a - b) mod 2^32 with bit-by-bit borrow chain.
//
// Returns a PartialReg `r` where:
//   r.bits[i] = -1 if any of {a.bits[0..i], b.bits[0..i]} is -1
//               (because the borrow chain can't propagate past unknowns)
//   r.bits[i] = 0 or 1 from the modular subtraction with borrow.
// r.n_decided = count of bits that are determined.
//
// Algorithm: iterate bit 0 → 31, maintaining borrow_in. At each bit i:
//   if a[i] == -1 or b[i] == -1: r[i] = -1; STOP (can't propagate further).
//   diff = a[i] - b[i] - borrow_in
//   if diff < 0: r[i] = diff + 2; borrow_out = 1
//   else:        r[i] = diff;     borrow_out = 0
PartialReg partial_modular_sub(const PartialReg& a, const PartialReg& b) {
    PartialReg r;
    int borrow = 0;
    for (int i = 0; i < 32; i++) {
        if (a.bits[i] == -1 || b.bits[i] == -1) {
            // Borrow chain breaks; all higher bits also unknown.
            break;
        }
        int diff = a.bits[i] - b.bits[i] - borrow;
        if (diff < 0) {
            r.bits[i] = diff + 2;
            borrow = 1;
        } else {
            r.bits[i] = diff;
            borrow = 0;
        }
        r.n_decided++;
    }
    return r;
}

// Inverse: given (a - b) mod 2^32 = c, with c partially decided, can we
// determine bits of a OR b given the other?
//
// Specifically: if we know c (e.g., dT2_r) AND a (e.g., dA[r]) bits 0..i,
// then we can compute bits 0..i of b = a - c modular. (Or more generally,
// subtraction with borrow.)
//
// This is the "force dE[r] from dA[r] and dT2_r" logic for Rule 4.
PartialReg partial_modular_sub_force_b(const PartialReg& a, const PartialReg& c) {
    // b = a - c modular (since c = a - b implies b = a - c).
    return partial_modular_sub(a, c);
}

// ---- Tests ----

int n_tests = 0, n_failed = 0;

#define ASSERT_EQ(actual, expected, msg) do { \
    n_tests++; \
    auto _a = (actual); \
    auto _e = (expected); \
    if (_a != _e) { \
        n_failed++; \
        printf("FAIL %s: got 0x%x, expected 0x%x\n", msg, (unsigned)_a, (unsigned)_e); \
    } else { \
        printf("PASS %s: 0x%x\n", msg, (unsigned)_a); \
    } \
} while (0)

#define ASSERT_PARTIAL(reg, expected_bits_decided, msg) do { \
    n_tests++; \
    if ((reg).n_decided != expected_bits_decided) { \
        n_failed++; \
        printf("FAIL %s: n_decided=%d, expected %d\n", \
               msg, (reg).n_decided, expected_bits_decided); \
    } else { \
        printf("PASS %s: n_decided=%d\n", msg, (reg).n_decided); \
    } \
} while (0)

uint32_t to_value(const PartialReg& p) {
    uint32_t v = 0;
    for (int i = 0; i < 32; i++) {
        if (p.bits[i] == 1) v |= (1u << i);
    }
    return v;
}

int main() {
    // --- Full inputs: should produce full output ---
    {
        PartialReg a = PartialReg::from_value(0x12345678);
        PartialReg b = PartialReg::from_value(0x00000001);
        PartialReg r = partial_modular_sub(a, b);
        ASSERT_PARTIAL(r, 32, "0x12345678 - 0x1: n_decided");
        ASSERT_EQ(to_value(r), 0x12345677u, "0x12345678 - 0x1 = 0x12345677");
    }

    // --- Borrow at bit 0 ---
    {
        PartialReg a = PartialReg::from_value(0x00000000);
        PartialReg b = PartialReg::from_value(0x00000001);
        PartialReg r = partial_modular_sub(a, b);
        ASSERT_PARTIAL(r, 32, "0 - 1: n_decided");
        ASSERT_EQ(to_value(r), 0xFFFFFFFFu, "0 - 1 = 0xFFFFFFFF (modular)");
    }

    // --- Borrow chain across multiple bits ---
    {
        PartialReg a = PartialReg::from_value(0x00010000);
        PartialReg b = PartialReg::from_value(0x00000001);
        PartialReg r = partial_modular_sub(a, b);
        ASSERT_PARTIAL(r, 32, "0x10000 - 0x1: n_decided");
        ASSERT_EQ(to_value(r), 0x0000FFFFu, "0x10000 - 0x1 = 0xFFFF");
    }

    // --- Partial input (only low 8 bits decided): output partial too ---
    {
        PartialReg a = PartialReg::low_bits(0x12345678, 8);  // 0x78 visible
        PartialReg b = PartialReg::low_bits(0x00000001, 8);  // 0x01 visible
        PartialReg r = partial_modular_sub(a, b);
        ASSERT_PARTIAL(r, 8, "partial 0x78 - 0x1: n_decided");
        // Low 8 bits of result = 0x77 = 0b0111_0111
        for (int i = 0; i < 8; i++) {
            int expected_bit = (0x77 >> i) & 1;
            if (r.bits[i] != expected_bit) {
                printf("  bit %d: got %d, expected %d\n", i, r.bits[i], expected_bit);
            }
        }
    }

    // --- Borrow chain BREAKS at unknown input ---
    {
        PartialReg a = PartialReg::from_value(0x12345678);
        PartialReg b = PartialReg::low_bits(0x12345678, 4);  // only low nibble
        PartialReg r = partial_modular_sub(a, b);
        ASSERT_PARTIAL(r, 4, "borrow chain breaks at bit 4: n_decided=4");
        // Low 4 bits: 0x8 - 0x8 = 0
        for (int i = 0; i < 4; i++) {
            int expected = 0;
            if (r.bits[i] != expected) {
                printf("  bit %d: got %d, expected %d\n", i, r.bits[i], expected);
            }
        }
    }

    // --- inverse: force b from a and c (where c = a - b modular) ---
    // a = 0x12345678, b = 0x12345677, c = a - b = 1
    // Force b: b = a - c = 0x12345678 - 1 = 0x12345677  ✓
    {
        PartialReg a = PartialReg::from_value(0x12345678);
        PartialReg c = PartialReg::from_value(0x00000001);
        PartialReg b_forced = partial_modular_sub_force_b(a, c);
        ASSERT_EQ(to_value(b_forced), 0x12345677u, "force b from (a, a-b)");
    }

    // --- Stress: random pairs ---
    {
        uint32_t test_a[] = {0xa1b2c3d4, 0xdeadbeef, 0xcafebabe, 0x12345678, 0xFFFFFFFF};
        uint32_t test_b[] = {0x12345678, 0xa1b2c3d4, 0x55555555, 0x12345678, 0x00000001};
        for (int i = 0; i < 5; i++) {
            uint32_t aa = test_a[i], bb = test_b[i];
            uint32_t expected = (aa - bb) & 0xFFFFFFFFu;
            PartialReg pa = PartialReg::from_value(aa);
            PartialReg pb = PartialReg::from_value(bb);
            PartialReg pr = partial_modular_sub(pa, pb);
            char msg[64];
            snprintf(msg, sizeof(msg), "0x%08x - 0x%08x", aa, bb);
            ASSERT_EQ(to_value(pr), expected, msg);
        }
    }

    printf("\nResults: %d passed, %d failed (%d tests)\n",
           n_tests - n_failed, n_failed, n_tests);
    return n_failed == 0 ? 0 : 1;
}
