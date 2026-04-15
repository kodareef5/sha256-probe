/*
 * carry_state_width.c — Measure carry state width at each bit position
 *
 * For EVERY input (w57,w58,w59,w60), run the cascade DP and extract
 * carry states at each bit position. Count unique carry states.
 *
 * Key question: does the carry state set grow polynomially or exponentially
 * with the number of processed bits? If polynomial → polynomial-time DP.
 *
 * The carry state at bit b consists of 49 carry-out bits from the 49
 * additions in rounds 57-63, for BOTH paths (98 total carry-diff bits).
 *
 * Actually, we track TWO kinds of state:
 * (1) The 98 carry-diff bits (carry path1 XOR carry path2)
 * (2) The raw carry pairs (carry path1, carry path2) = 98 bits
 *
 * The diff version has fewer unique states (by 42% invariance).
 *
 * Compile: gcc -O3 -march=native -Xclang -fopenmp \
 *          -I/opt/homebrew/opt/libomp/include \
 *          -L/opt/homebrew/opt/libomp/lib -lomp \
 *          -o carry_width carry_state_width.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define MAX_N 16
#define ROUNDS 7
#define ADDS_PER_ROUND 7
#define TOTAL_ADDS (ROUNDS * ADDS_PER_ROUND)  /* 49 */

static int gN;
static uint32_t gMASK;
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;
static uint32_t KN[64], IVN[8];

static inline uint32_t ror_n(uint32_t x, int k) { k%=gN; return ((x>>k)|(x<<(gN-k)))&gMASK; }
static inline uint32_t fnS0(uint32_t a) { return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]); }
static inline uint32_t fnS1(uint32_t e) { return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]); }
static inline uint32_t fns0(uint32_t x) { return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&gMASK); }
static inline uint32_t fns1(uint32_t x) { return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&gMASK); }
static inline uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g) { return ((e&f)^((~e)&g))&gMASK; }
static inline uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c) { return ((a&b)^(a&c)^(b&c))&gMASK; }

static const uint32_t K32[64]={
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};

static int scale_rot(int k32) { int r=(int)rint((double)k32*gN/32.0); return r<1?1:r; }

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for(int i=0;i<16;i++) W[i]=M[i]&gMASK;
    for(int i=16;i<57;i++) W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&gMASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){
        uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&gMASK;
        uint32_t T2=(fnS0(a)+fnMj(a,b,c))&gMASK;
        h=g;g=f;f=e;e=(d+T1)&gMASK;d=c;c=b;b=a;a=(T1+T2)&gMASK;
    }
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

static inline void sha_round(uint32_t s[8],uint32_t k,uint32_t w){
    uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&gMASK;
    uint32_t T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&gMASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&gMASK;
    s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&gMASK;
}

static inline uint32_t find_w2(const uint32_t s1[8],const uint32_t s2[8],int rnd,uint32_t w1){
    uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&gMASK;
    uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&gMASK;
    uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&gMASK;
    uint32_t T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&gMASK;
    return(w1+r1-r2+T21-T22)&gMASK;
}

/* Extract carry bits from addition a+b at bit position k.
 * Returns carry OUT of bit k (into bit k+1).
 * Needs carry-in from bit k-1. */
static inline uint32_t carry_bit(uint32_t a, uint32_t b, int k, uint32_t carry_in) {
    uint32_t ak = (a >> k) & 1;
    uint32_t bk = (b >> k) & 1;
    return (ak & bk) | (ak & carry_in) | (bk & carry_in);
}

/* Extract ALL carry bits from a full computation (both paths, all rounds).
 * carry_out[path][bit_position][addition] = carry OUT of that bit.
 * Returns 1 if collision, 0 otherwise. */
static int extract_carries_full(
    const uint32_t init1[8], const uint32_t init2[8],
    const uint32_t W1vals[7], const uint32_t W2vals[7],
    uint8_t carry_out[2][MAX_N][TOTAL_ADDS])
{
    for (int path = 0; path < 2; path++) {
        uint32_t s[8];
        memcpy(s, path == 0 ? init1 : init2, 32);
        const uint32_t *Wv = (path == 0) ? W1vals : W2vals;

        /* Need full carry chains: carry[add][bit] */
        /* carry_in[add] starts at 0 for bit 0 */
        uint32_t cin[TOTAL_ADDS]; /* carry into current bit for each add */
        memset(cin, 0, sizeof(cin));

        for (int b = 0; b < gN; b++) {
            /* Recompute the round at this bit using the cumulative state */
            /* Actually, we need the full N-bit values to know the operands.
             * The carry extraction is done per-bit but needs the full operands.
             * So we compute the full rounds and extract carries afterward. */
        }

        /* Simpler: compute full rounds, then extract carries per bit */
        for (int r = 0; r < ROUNDS; r++) {
            uint32_t sig1_e = fnS1(s[4]);
            uint32_t ch_efg = fnCh(s[4], s[5], s[6]);
            uint32_t sig0_a = fnS0(s[0]);
            uint32_t maj_abc = fnMj(s[0], s[1], s[2]);
            uint32_t t0 = (s[7] + sig1_e) & gMASK;
            uint32_t t1 = (t0 + ch_efg) & gMASK;
            uint32_t t2 = (t1 + KN[57+r]) & gMASK;
            uint32_t T1 = (t2 + Wv[r]) & gMASK;
            uint32_t T2 = (sig0_a + maj_abc) & gMASK;

            int base = r * ADDS_PER_ROUND;
            /* Extract carries per bit for each addition */
            uint32_t operands[7][2] = {
                {s[7], sig1_e},      /* add 0: h + Sig1(e) */
                {t0, ch_efg},        /* add 1: t0 + Ch */
                {t1, KN[57+r]},      /* add 2: t1 + K */
                {t2, Wv[r]},         /* add 3: t2 + W */
                {sig0_a, maj_abc},   /* add 4: Sig0 + Maj */
                {s[3], T1},          /* add 5: d + T1 */
                {T1, T2}             /* add 6: T1 + T2 */
            };
            for (int a = 0; a < 7; a++) {
                uint32_t c = 0;
                for (int b = 0; b < gN; b++) {
                    uint32_t ab = (operands[a][0] >> b) & 1;
                    uint32_t bb_val = (operands[a][1] >> b) & 1;
                    uint32_t cout = (ab & bb_val) | (ab & c) | (bb_val & c);
                    carry_out[path][b][base+a] = cout;
                    c = cout;
                }
            }

            /* Advance state */
            s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&gMASK;
            s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&gMASK;
        }
    }

    /* Check collision */
    uint32_t s1[8], s2[8];
    memcpy(s1, init1, 32); memcpy(s2, init2, 32);
    for (int r = 0; r < ROUNDS; r++) {
        sha_round(s1, KN[57+r], W1vals[r]);
        sha_round(s2, KN[57+r], W2vals[r]);
    }
    for (int r = 0; r < 8; r++)
        if (s1[r] != s2[r]) return 0;
    return 1;
}

/* Hash a carry-diff state (98 bits → 64-bit hash) */
static uint64_t hash_cdiff(const uint8_t cdiff[TOTAL_ADDS]) {
    uint64_t h = 14695981039346656037ULL;
    for (int i = 0; i < TOTAL_ADDS; i++) {
        h ^= cdiff[i];
        h *= 1099511628211ULL;
    }
    return h;
}

/* Hash table for counting unique carry-diff states */
#define HT_BITS 20
#define HT_SIZE (1 << HT_BITS)
#define HT_MASK (HT_SIZE - 1)

typedef struct {
    uint8_t state[TOTAL_ADDS];
    int count;
    int next;
} HTEntry;

static HTEntry *ht_entries;
static int *ht_buckets;
static int ht_count;
static int ht_cap;

static void ht_init(void) {
    ht_cap = 1 << 18;
    ht_entries = malloc(ht_cap * sizeof(HTEntry));
    ht_buckets = malloc(HT_SIZE * sizeof(int));
    for (int i = 0; i < HT_SIZE; i++) ht_buckets[i] = -1;
    ht_count = 0;
}

static void ht_reset(void) {
    for (int i = 0; i < HT_SIZE; i++) ht_buckets[i] = -1;
    ht_count = 0;
}

static int ht_insert(const uint8_t state[TOTAL_ADDS]) {
    uint64_t h = hash_cdiff(state);
    int bucket = h & HT_MASK;
    for (int i = ht_buckets[bucket]; i >= 0; i = ht_entries[i].next) {
        if (memcmp(ht_entries[i].state, state, TOTAL_ADDS) == 0) {
            ht_entries[i].count++;
            return 0; /* already existed */
        }
    }
    if (ht_count >= ht_cap) {
        ht_cap *= 2;
        ht_entries = realloc(ht_entries, ht_cap * sizeof(HTEntry));
    }
    int idx = ht_count++;
    memcpy(ht_entries[idx].state, state, TOTAL_ADDS);
    ht_entries[idx].count = 1;
    ht_entries[idx].next = ht_buckets[bucket];
    ht_buckets[bucket] = idx;
    return 1; /* new entry */
}

int main(int argc, char **argv) {
    setbuf(stdout, NULL);
    struct timespec t0, t_now;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    gN = (argc > 1) ? atoi(argv[1]) : 4;
    if (gN < 2 || gN > 10) { printf("N must be 2..10\n"); return 1; }
    gMASK = (1U << gN) - 1;

    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&gMASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&gMASK;

    uint32_t SIZE = 1U << gN;
    printf("=== Carry State Width Analysis, N=%d ===\n", gN);
    printf("Search space: 2^%d = %llu\n", 4*gN, (unsigned long long)1ULL<<(4*gN));
    printf("Carry bits per bit position: %d per path, %d diff\n\n",
           TOTAL_ADDS, TOTAL_ADDS);

    /* Find valid candidate */
    uint32_t M0=0, KMSB=0, fill=gMASK;
    int kbit=-1, found=0;
    uint32_t state1[8], state2[8], W1p[57], W2p[57];
    uint32_t fills[]={gMASK, 0x55555555&gMASK, 0};
    for(int fi=0;fi<3&&!found;fi++){
        fill=fills[fi];
        for(int kb=gN-1;kb>=0&&!found;kb--){
            KMSB=1U<<kb;
            for(uint32_t m0=0;m0<SIZE&&!found;m0++){
                uint32_t M1[16],M2[16];
                for(int i=0;i<16;i++){M1[i]=fill;M2[i]=fill;}
                M1[0]=m0;M2[0]=m0^KMSB;M2[9]=fill^KMSB;
                precompute(M1,state1,W1p);precompute(M2,state2,W2p);
                if(((state1[0]-state2[0])&gMASK)==0){
                    M0=m0;kbit=kb;found=1;
                }
            }
        }
    }
    if(!found){printf("No candidate found\n");return 1;}
    uint32_t M1[16],M2[16];
    for(int i=0;i<16;i++){M1[i]=fill;M2[i]=fill;}
    M1[0]=M0;M2[0]=M0^KMSB;M2[9]=fill^KMSB;
    precompute(M1,state1,W1p);precompute(M2,state2,W2p);
    printf("Candidate: M[0]=0x%x, fill=0x%x, kernel bit %d\n\n", M0, fill, kbit);

    /* Allocate per-bit-position hash tables */
    ht_init();

    /* Per-bit unique carry-diff state counts */
    int unique_cdiff[MAX_N];
    int unique_cpair[MAX_N]; /* raw carry pairs (not diff) */
    int collision_width[MAX_N]; /* unique states among collisions only */
    memset(unique_cdiff, 0, sizeof(unique_cdiff));
    memset(unique_cpair, 0, sizeof(unique_cpair));
    memset(collision_width, 0, sizeof(collision_width));

    uint64_t total_coll = 0;
    uint8_t carry_buf[2][MAX_N][TOTAL_ADDS];

    printf("Processing all 2^%d inputs...\n", 4*gN);

    /* We process each bit position separately */
    for (int bit = 0; bit < gN; bit++) {
        ht_reset();
        int coll_ht_count = 0; /* we'll do a separate pass for collision-only */

        for (uint32_t w57 = 0; w57 < SIZE; w57++) {
            uint32_t s57a[8],s57b[8]; memcpy(s57a,state1,32);memcpy(s57b,state2,32);
            uint32_t w57b=find_w2(s57a,s57b,57,w57);
            sha_round(s57a,KN[57],w57);sha_round(s57b,KN[57],w57b);
            for (uint32_t w58 = 0; w58 < SIZE; w58++) {
                uint32_t s58a[8],s58b[8]; memcpy(s58a,s57a,32);memcpy(s58b,s57b,32);
                uint32_t w58b=find_w2(s58a,s58b,58,w58);
                sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);
                for (uint32_t w59 = 0; w59 < SIZE; w59++) {
                    uint32_t s59a[8],s59b[8]; memcpy(s59a,s58a,32);memcpy(s59b,s58b,32);
                    uint32_t w59b=find_w2(s59a,s59b,59,w59);
                    sha_round(s59a,KN[59],w59);sha_round(s59b,KN[59],w59b);
                    uint32_t co60=find_w2(s59a,s59b,60,0);
                    uint32_t cw61a=(fns1(w59)+W1p[54]+fns0(W1p[46])+W1p[45])&gMASK;
                    uint32_t cw61b=(fns1(w59b)+W2p[54]+fns0(W2p[46])+W2p[45])&gMASK;
                    uint32_t sc62a=(W1p[55]+fns0(W1p[47])+W1p[46])&gMASK;
                    uint32_t sc62b=(W2p[55]+fns0(W2p[47])+W2p[46])&gMASK;
                    uint32_t cw63a=(fns1(cw61a)+W1p[56]+fns0(W1p[48])+W1p[47])&gMASK;
                    uint32_t cw63b=(fns1(cw61b)+W2p[56]+fns0(W2p[48])+W2p[47])&gMASK;

                    for (uint32_t w60 = 0; w60 < SIZE; w60++) {
                        uint32_t w60b=(w60+co60)&gMASK;
                        uint32_t W1v[7]={w57,w58,w59,w60,cw61a,(fns1(w60)+sc62a)&gMASK,cw63a};
                        uint32_t W2v[7]={w57b,w58b,w59b,w60b,cw61b,(fns1(w60b)+sc62b)&gMASK,cw63b};

                        int is_coll = extract_carries_full(state1,state2,W1v,W2v,carry_buf);

                        /* Compute carry-diff at this bit position */
                        uint8_t cdiff[TOTAL_ADDS];
                        for (int a = 0; a < TOTAL_ADDS; a++)
                            cdiff[a] = carry_buf[0][bit][a] ^ carry_buf[1][bit][a];

                        /* Also try tracking only cascade-round carries (r57-60 = first 28) */
                        uint8_t cdiff_cascade[28];
                        for (int a = 0; a < 28; a++)
                            cdiff_cascade[a] = cdiff[a];

                        ht_insert(cdiff);

                        if (is_coll && bit == 0) total_coll++;
                    }
                }
            }
        }

        unique_cdiff[bit] = ht_count;

        clock_gettime(CLOCK_MONOTONIC, &t_now);
        double el = (t_now.tv_sec-t0.tv_sec)+(t_now.tv_nsec-t0.tv_nsec)/1e9;
        printf("  bit %d: %d unique carry-diff states (%.1fs)\n", bit, ht_count, el);
    }

    printf("\n=== RESULTS ===\n\n");
    printf("N = %d, search space = 2^%d = %llu\n", gN, 4*gN, 1ULL<<(4*gN));
    printf("Collisions found: %llu\n\n", (unsigned long long)total_coll);

    printf("Carry-diff state width per bit position:\n");
    printf("| Bit | Unique states | vs search space |\n");
    printf("|-----|---------------|-----------------|\n");
    for (int b = 0; b < gN; b++) {
        double ratio = (double)unique_cdiff[b] / (1ULL << (4*gN));
        printf("| %3d | %13d | %.6e |\n", b, unique_cdiff[b], ratio);
    }

    printf("\nIf width is << 2^{4N}, carry DP can exploit this compression.\n");

    clock_gettime(CLOCK_MONOTONIC, &t_now);
    double total = (t_now.tv_sec-t0.tv_sec)+(t_now.tv_nsec-t0.tv_nsec)/1e9;
    printf("\nTotal time: %.1fs\n", total);

    free(ht_entries); free(ht_buckets);
    return 0;
}
