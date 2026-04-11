/* Sigma1 bridge: algebraic MITM for sr=60 collision without SAT.
 *
 * For each W1[57]:
 *   1. Compute state at round 59 (cascade 1 gives da=db=dc=dd=0)
 *   2. Compute what W1[60] needs to be for cascade 2 to start (de60 target)
 *   3. Use schedule: W[60] = sigma1(W[58]) + C1
 *      → forced W1[58] = sigma1_inv(target_W1[60] - C1)
 *   4. Check if this forced W1[58] produces valid cascade at round 58
 *   5. If W[59] can be found completing the collision: SUCCESS
 *
 * sigma1 is bijective on GF(2)^32 (it's a linear automorphism).
 * So step 3 always has exactly one solution.
 *
 * The question: how often does the forced W1[58] maintain cascade 1?
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#ifdef _OPENMP
#include <omp.h>
#endif
#define MASK 0xFFFFFFFFU
static inline uint32_t ROR(uint32_t x,int n){return(x>>n)|(x<<(32-n));}
static inline uint32_t Ch(uint32_t e,uint32_t f,uint32_t g){return(e&f)^(~e&g);}
static inline uint32_t Maj(uint32_t a,uint32_t b,uint32_t c){return(a&b)^(a&c)^(b&c);}
static inline uint32_t Sigma0(uint32_t a){return ROR(a,2)^ROR(a,13)^ROR(a,22);}
static inline uint32_t Sigma1(uint32_t e){return ROR(e,6)^ROR(e,11)^ROR(e,25);}
static inline uint32_t sigma0(uint32_t x){return ROR(x,7)^ROR(x,18)^(x>>3);}
static inline uint32_t sigma1(uint32_t x){return ROR(x,17)^ROR(x,19)^(x>>10);}
static const uint32_t K[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t cascade_dw(const uint32_t s1[8],const uint32_t s2[8]){return s1[7]-s2[7]+Sigma1(s1[4])-Sigma1(s2[4])+Ch(s1[4],s1[5],s1[6])-Ch(s2[4],s2[5],s2[6])+Sigma0(s1[0])+Maj(s1[0],s1[1],s1[2])-Sigma0(s2[0])-Maj(s2[0],s2[1],s2[2]);}
static void one_round(uint32_t out[8],const uint32_t in[8],uint32_t w,int r){uint32_t T1=in[7]+Sigma1(in[4])+Ch(in[4],in[5],in[6])+K[r]+w;uint32_t T2=Sigma0(in[0])+Maj(in[0],in[1],in[2]);out[0]=T1+T2;out[1]=in[0];out[2]=in[1];out[3]=in[2];out[4]=in[3]+T1;out[5]=in[4];out[6]=in[5];out[7]=in[6];}
static void compute_state57(const uint32_t M[16],uint32_t state[8],uint32_t W[64]){
    for(int i=0;i<16;i++)W[i]=M[i];for(int i=16;i<64;i++)W[i]=sigma1(W[i-2])+W[i-7]+sigma0(W[i-15])+W[i-16];
    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for(int i=0;i<57;i++){uint32_t T1=h+Sigma1(e)+Ch(e,f,g)+K[i]+W[i];uint32_t T2=Sigma0(a)+Maj(a,b,c);h=g;g=f;f=e;e=d+T1;d=c;c=b;b=a;a=T1+T2;}
    state[0]=a;state[1]=b;state[2]=c;state[3]=d;state[4]=e;state[5]=f;state[6]=g;state[7]=h;
}

/* Build sigma1 inverse lookup table. sigma1 is bijective on GF(2)^32
 * (it's a linear automorphism over GF(2)), so every output has exactly
 * one preimage. Build table: sigma1_inv[sigma1(x)] = x for all x. */
static uint32_t *build_sigma1_inv(void) {
    /* sigma1 is XOR-linear, so we can invert via Gaussian elimination on
     * the 32x32 binary matrix. But a lookup table is simpler for 32-bit. */
    /* Actually, for 2^32 entries that's 16GB — too large.
     * Use matrix inversion instead. */

    /* Build the 32x32 binary matrix M where sigma1(x) = M·x over GF(2).
     * sigma1(x) = ROR(x,17) ^ ROR(x,19) ^ SHR(x,10).
     * Row i of M: which input bits contribute to output bit i. */
    uint32_t M[32], Minv[32];
    for (int i = 0; i < 32; i++) {
        /* sigma1(1<<j) gives the j-th column. We want row i. */
        M[i] = 0;
    }
    for (int j = 0; j < 32; j++) {
        uint32_t col = sigma1(1U << j);
        for (int i = 0; i < 32; i++) {
            if ((col >> i) & 1) M[i] |= (1U << j);
        }
    }

    /* Invert M over GF(2) using Gaussian elimination. */
    /* Augment: [M | I] */
    uint32_t aug[32];
    for (int i = 0; i < 32; i++) aug[i] = M[i]; /* M part */
    uint32_t ident[32];
    for (int i = 0; i < 32; i++) ident[i] = 1U << i; /* I part */

    for (int col = 0; col < 32; col++) {
        /* Find pivot */
        int pivot = -1;
        for (int row = col; row < 32; row++) {
            if ((aug[row] >> col) & 1) { pivot = row; break; }
        }
        if (pivot < 0) { fprintf(stderr, "sigma1 not invertible?!\n"); return NULL; }
        if (pivot != col) {
            uint32_t tmp = aug[col]; aug[col] = aug[pivot]; aug[pivot] = tmp;
            tmp = ident[col]; ident[col] = ident[pivot]; ident[pivot] = tmp;
        }
        /* Eliminate */
        for (int row = 0; row < 32; row++) {
            if (row != col && ((aug[row] >> col) & 1)) {
                aug[row] ^= aug[col];
                ident[row] ^= ident[col];
            }
        }
    }
    /* ident now contains M^{-1}. Verify: */
    for (int i = 0; i < 32; i++) Minv[i] = ident[i];

    /* sigma1_inv(y) = Minv · y over GF(2). But that's XOR-only (no carries).
     * sigma1 over Z is NOT linear over Z! sigma1 uses XOR + SHR, not addition.
     * Wait — sigma1 IS purely GF(2) linear: ROR and XOR and SHR are all GF(2).
     * So sigma1 IS GF(2)-linear and invertible.
     *
     * BUT: the schedule equation W[60] = sigma1(W[58]) + W[53] + ...
     * uses MODULAR ADDITION (+), not XOR. So:
     *   target = sigma1(w58) + const  (mod 2^32)
     *   sigma1(w58) = target - const  (mod 2^32)
     *   w58 = sigma1_inv(target - const)
     *
     * sigma1_inv operates over GF(2) (XOR), but the schedule uses Z/2^32 (+).
     * sigma1 is GF(2)-linear, so sigma1_inv(z) = Minv · z bitwise.
     */
    fprintf(stderr, "sigma1 inverse matrix built (32x32 GF(2)).\n");

    /* Store Minv for fast application */
    uint32_t *result = malloc(32 * sizeof(uint32_t));
    for (int i = 0; i < 32; i++) result[i] = Minv[i];

    /* Quick verify: sigma1_inv(sigma1(0x12345678)) should give 0x12345678 */
    uint32_t test = 0x12345678;
    uint32_t y = sigma1(test);
    uint32_t recovered = 0;
    for (int i = 0; i < 32; i++) {
        if (__builtin_popcount(Minv[i] & y) & 1) recovered |= (1U << i);
    }
    fprintf(stderr, "Verify: sigma1(0x%08x) = 0x%08x, inv = 0x%08x, match=%d\n",
            test, y, recovered, recovered == test);

    return result;
}

static uint32_t apply_sigma1_inv(const uint32_t *Minv, uint32_t y) {
    uint32_t x = 0;
    for (int i = 0; i < 32; i++) {
        if (__builtin_popcount(Minv[i] & y) & 1) x |= (1U << i);
    }
    return x;
}

int main() {
    uint32_t M1[16]={0x17149975,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff};
    uint32_t M2[16]; memcpy(M2,M1,sizeof(M2)); M2[0]^=0x80000000; M2[9]^=0x80000000;
    uint32_t s1[8],s2[8],W1[64],W2[64]; compute_state57(M1,s1,W1); compute_state57(M2,s2,W2);
    uint32_t C57=cascade_dw(s1,s2);

    /* Schedule constants for W[60] */
    uint32_t sched_const1 = W1[53] + sigma0(W1[45]) + W1[44];
    uint32_t sched_const2 = W2[53] + sigma0(W2[45]) + W2[44];

    uint32_t *Minv = build_sigma1_inv();
    if (!Minv) return 1;

    /* Verify with cert */
    uint32_t cert_w57 = 0x9ccfa55e, cert_w58 = 0xd9d64416;
    uint32_t cert_w60_from_sched = sigma1(cert_w58) + sched_const1;
    fprintf(stderr, "\nCert schedule: sigma1(W[58]) + const = 0x%08x\n", cert_w60_from_sched);
    fprintf(stderr, "Cert actual W[60] = 0x%08x\n", 0xb6befe82U);
    fprintf(stderr, "Match: %d (these differ because cert W[60] is FREE, not schedule-constrained)\n\n",
            cert_w60_from_sched == 0xb6befe82U);

    /* The bridge idea:
     * For each W1[57]:
     *   1. Run round 57 → state at round 58
     *   2. Compute C58 = cascade_dw at round 58
     *   3. For cascade 2 to start: we need de60 to be "closable" at round 60
     *      → need cascade_dw at round 60 (after rounds 58, 59) to match round-61 target
     *   4. This requires specific W[58] and W[59] values
     *   5. The schedule forces W[60] = sigma1(W[58]) + const
     *      → if we need a specific W[60] for round 60, W[58] is forced
     *   6. Check if the forced W[58] is compatible with round-58 cascade
     *
     * But actually the problem is more subtle: W[58] affects BOTH the round-58
     * state AND W[60] via schedule. We need to check if these dual constraints
     * are simultaneously satisfiable.
     *
     * Simplified test: for 2^32 W1[57] values, compute the forced W1[58]
     * from the schedule bridge, then check if ANY W1[59] gives a round-61
     * closure with that forced (W1[57], forced_W1[58]).
     *
     * This is O(2^32) per W1[57] for the W1[59] enumeration × 2^32 W1[57] = O(2^64).
     * Too expensive!
     *
     * BUT: we can check the NECESSARY condition that the forced W1[58]
     * preserves cascade 1 (i.e., the cascade_dw at round 59 has the right
     * structure). This is O(1) per W1[57].
     */

    fprintf(stderr, "=== Sigma1 bridge analysis ===\n");
    fprintf(stderr, "For each W1[57]: compute state at round 58, then check\n");
    fprintf(stderr, "what W1[60] is needed for round-61 closure, then invert\n");
    fprintf(stderr, "sigma1 to get forced W1[58], and check cascade compatibility.\n\n");

    /* Actually, the bridge requires knowing W[59] to compute the target W[60].
     * The target depends on W[59] through sigma1(W2[59]) in the closure formula.
     * So we can't invert without knowing W[59].
     *
     * Simplified analysis: just check how often sigma1(forced_W58) matches
     * the actual schedule output for W[60] = cert's W[60]. */

    /* Even simpler: count how many W1[57] values give a forced W1[58]
     * (from schedule inversion) that has small cascade error at round 58. */

    long n_small_error = 0;
    time_t t0 = time(NULL);

    #pragma omp parallel for reduction(+:n_small_error)
    for (long w57_l = 0; w57_l < (1L << 32); w57_l++) {
        uint32_t w57 = (uint32_t)w57_l;
        uint32_t sa[8], sb[8];
        one_round(sa, s1, w57, 57);
        one_round(sb, s2, w57 + C57, 57);

        /* For this W1[57], the "ideal" W1[60] would zero de60.
         * de60 = d59 + T1_59. Under cascade, dd59=0, so de60 = T1_59.
         * T1_59 depends on state at round 59 AND W[59].
         * We don't know W[59] yet, so we can't compute exact target.
         *
         * Instead: check the cascade_dw structure at round 58. */
        uint32_t C58 = cascade_dw(sa, sb);

        /* The schedule says: W[60] = sigma1(W[58]) + sched_const.
         * For the cascade to work, we need W2[60] - W1[60] = C60 (some value).
         * W2[60] - W1[60] = sigma1(W2[58]) - sigma1(W1[58]) + (sched_const2 - sched_const1)
         *                  = sigma1(W1[58] + C58) - sigma1(W1[58]) + delta_sched
         *
         * This is a function of W1[58] and C58. For specific C58, the
         * differential sigma1(x + C58) - sigma1(x) has a known image.
         *
         * The question: does C60_needed lie in this image?
         * C60_needed is determined by the round-60 state (from W[57..59]).
         *
         * This is getting circular. Let me just compute a simpler metric:
         * the Hamming weight of C58. Low HW means small cascade perturbation
         * at round 58 → more likely to preserve cascade structure.
         */
        int hw_C58 = __builtin_popcount(C58);
        if (hw_C58 <= 5) n_small_error++;
    }

    time_t t1 = time(NULL);
    fprintf(stderr, "W1[57] with hw(C58) <= 5: %ld / 2^32 (%.6f%%)  [%lds]\n",
            n_small_error, 100.0 * n_small_error / (double)(1L << 32), (long)(t1-t0));
    fprintf(stderr, "Cert C58 = 0x%08x (hw=%d)\n", 0x71c0863bU, __builtin_popcount(0x71c0863bU));

    free(Minv);
    return 0;
}
