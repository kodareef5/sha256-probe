/*
 * mode_dp_pilot.c — Mode-DP pilot at N=4
 *
 * Instead of enumerating 2^{4N} message values, enumerate carry MODE
 * patterns for the critical additions. Each mode pattern determines
 * the message bits (via XOR/linear relationships). Count how many
 * mode patterns produce collisions.
 *
 * Key question: is the number of VALID mode patterns much less than
 * 2^{4N}? If so, the mode-DP gives a speedup.
 *
 * Approach for pilot:
 * 1. Run brute force at N=4 (65536 evaluations)
 * 2. For each evaluation, extract the carry modes for all 49 additions
 * 3. Count unique carry-mode patterns
 * 4. Among collisions: count unique carry-mode patterns
 * 5. Measure: |mode_patterns| / 2^{4N} = compression ratio
 *
 * Compile: gcc -O3 -march=native -o mode_dp_pilot mode_dp_pilot.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

#define N 4
#define MASK 0xF
#define MSB (1U << (N-1))
#define ROUNDS 7
#define ADDS_PER_ROUND 7
#define TOTAL_ADDS (ROUNDS * ADDS_PER_ROUND)

static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;
static uint32_t KN[64], IVN[8];

static int scale_rot(int k32) {
    int r = (int)rint((double)k32 * N / 32.0);
    return r < 1 ? 1 : r;
}
static inline uint32_t ror_n(uint32_t x, int k) { k %= N; return ((x >> k) | (x << (N - k))) & MASK; }
static inline uint32_t fnS0(uint32_t a) { return ror_n(a, rS0[0]) ^ ror_n(a, rS0[1]) ^ ror_n(a, rS0[2]); }
static inline uint32_t fnS1(uint32_t e) { return ror_n(e, rS1[0]) ^ ror_n(e, rS1[1]) ^ ror_n(e, rS1[2]); }
static inline uint32_t fns0(uint32_t x) { return ror_n(x, rs0[0]) ^ ror_n(x, rs0[1]) ^ ((x >> ss0) & MASK); }
static inline uint32_t fns1(uint32_t x) { return ror_n(x, rs1[0]) ^ ror_n(x, rs1[1]) ^ ((x >> ss1) & MASK); }
static inline uint32_t fnCh(uint32_t e, uint32_t f, uint32_t g) { return ((e & f) ^ ((~e) & g)) & MASK; }
static inline uint32_t fnMj(uint32_t a, uint32_t b, uint32_t c) { return ((a & b) ^ (a & c) ^ (b & c)) & MASK; }

static const uint32_t K32[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for (int i = 0; i < 16; i++) W[i] = M[i] & MASK;
    for (int i = 16; i < 57; i++)
        W[i] = (fns1(W[i-2]) + W[i-7] + fns0(W[i-15]) + W[i-16]) & MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for (int i = 0; i < 57; i++) {
        uint32_t T1 = (h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&MASK;
        uint32_t T2 = (fnS0(a)+fnMj(a,b,c))&MASK;
        h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;
    }
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&MASK;
    uint32_t T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&MASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;
    s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;
}

static inline uint32_t find_w2(const uint32_t s1[8], const uint32_t s2[8], int rnd, uint32_t w1) {
    uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&MASK;
    uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&MASK;
    uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&MASK;
    uint32_t T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&MASK;
    return (w1+r1-r2+T21-T22)&MASK;
}

/* Extract carry-out at each bit for addition a+b */
static void extract_carries(uint32_t a, uint32_t b, uint8_t carries[N]) {
    uint32_t c = 0;
    for (int k = 0; k < N; k++) {
        uint32_t ak = (a >> k) & 1;
        uint32_t bk = (b >> k) & 1;
        carries[k] = (ak & bk) | (ak & c) | (bk & c);
        c = carries[k];
    }
}

/* Hash table for mode patterns */
#define HT_BITS 20
#define HT_SIZE (1 << HT_BITS)
#define HT_MASK (HT_SIZE - 1)

typedef struct {
    uint8_t modes[TOTAL_ADDS * N]; /* 49 * N = 196 bits packed as bytes */
    int count;
    int is_collision;
    int next;
} HTEntry;

static HTEntry *ht_entries;
static int *ht_buckets;
static int ht_count, ht_cap;

static uint64_t hash_modes(const uint8_t *modes) {
    uint64_t h = 14695981039346656037ULL;
    for (int i = 0; i < TOTAL_ADDS * N; i++) {
        h ^= modes[i]; h *= 1099511628211ULL;
    }
    return h;
}

static void ht_init(void) {
    ht_cap = 1 << 18;
    ht_entries = calloc(ht_cap, sizeof(HTEntry));
    ht_buckets = malloc(HT_SIZE * sizeof(int));
    for (int i = 0; i < HT_SIZE; i++) ht_buckets[i] = -1;
    ht_count = 0;
}

static int ht_insert(const uint8_t *modes, int is_coll) {
    uint32_t h = hash_modes(modes) & HT_MASK;
    for (int i = ht_buckets[h]; i >= 0; i = ht_entries[i].next) {
        if (memcmp(ht_entries[i].modes, modes, TOTAL_ADDS * N) == 0) {
            ht_entries[i].count++;
            if (is_coll) ht_entries[i].is_collision = 1;
            return 0;
        }
    }
    if (ht_count >= ht_cap) { ht_cap *= 2; ht_entries = realloc(ht_entries, ht_cap * sizeof(HTEntry)); }
    int idx = ht_count++;
    memcpy(ht_entries[idx].modes, modes, TOTAL_ADDS * N);
    ht_entries[idx].count = 1;
    ht_entries[idx].is_collision = is_coll;
    ht_entries[idx].next = ht_buckets[h];
    ht_buckets[h] = idx;
    return 1;
}

int main(void) {
    setbuf(stdout, NULL);
    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for (int i=0;i<64;i++) KN[i]=K32[i]&MASK;
    for (int i=0;i<8;i++) IVN[i]=IV32[i]&MASK;

    /* Find candidate */
    uint32_t M1[16],M2[16],state1[8],state2[8],W1p[57],W2p[57];
    for (int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
    M1[0]=0; M2[0]=MSB; M2[9]=MASK^MSB;
    precompute(M1,state1,W1p); precompute(M2,state2,W2p);

    printf("=== Mode-DP Pilot at N=%d ===\n", N);
    printf("Search space: 2^%d = %d\n", 4*N, 1<<(4*N));
    printf("Mode bits: %d additions x %d bits = %d\n\n", TOTAL_ADDS, N, TOTAL_ADDS*N);

    ht_init();

    uint64_t total = 0, n_coll = 0;
    int SIZE = 1 << N;

    for (uint32_t w57=0; w57<SIZE; w57++) {
        uint32_t sa[8],sb[8]; memcpy(sa,state1,32);memcpy(sb,state2,32);
        uint32_t w57b=find_w2(sa,sb,57,w57);
        sha_round(sa,KN[57],w57);sha_round(sb,KN[57],w57b);

        for (uint32_t w58=0; w58<SIZE; w58++) {
            uint32_t s2a[8],s2b[8]; memcpy(s2a,sa,32);memcpy(s2b,sb,32);
            uint32_t w58b=find_w2(s2a,s2b,58,w58);
            sha_round(s2a,KN[58],w58);sha_round(s2b,KN[58],w58b);

            for (uint32_t w59=0; w59<SIZE; w59++) {
                uint32_t s3a[8],s3b[8]; memcpy(s3a,s2a,32);memcpy(s3b,s2b,32);
                uint32_t w59b=find_w2(s3a,s3b,59,w59);
                sha_round(s3a,KN[59],w59);sha_round(s3b,KN[59],w59b);
                uint32_t co60=find_w2(s3a,s3b,60,0);
                uint32_t cw61a=(fns1(w59)+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;
                uint32_t cw61b=(fns1(w59b)+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
                uint32_t sc62a=(W1p[55]+fns0(W1p[47])+W1p[46])&MASK;
                uint32_t sc62b=(W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
                uint32_t cw63a=(fns1(cw61a)+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;
                uint32_t cw63b=(fns1(cw61b)+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;

                for (uint32_t w60=0; w60<SIZE; w60++) {
                    uint32_t w60b=(w60+co60)&MASK;
                    uint32_t s4a[8],s4b[8];
                    memcpy(s4a,s3a,32);memcpy(s4b,s3b,32);
                    sha_round(s4a,KN[60],w60);sha_round(s4b,KN[60],w60b);

                    /* Extract carry modes for ALL additions, PATH 1 ONLY */
                    /* (We use path 1 modes; path 2 is determined by cascade) */
                    uint8_t all_modes[TOTAL_ADDS * N];
                    memset(all_modes, 0, sizeof(all_modes));

                    uint32_t ss[8]; memcpy(ss, state1, 32);
                    uint32_t Wvals[7] = {w57,w58,w59,w60,cw61a,
                        (fns1(w60)+sc62a)&MASK, cw63a};

                    for (int r = 0; r < ROUNDS; r++) {
                        uint32_t sig1e = fnS1(ss[4]);
                        uint32_t ch_efg = fnCh(ss[4],ss[5],ss[6]);
                        uint32_t sig0a = fnS0(ss[0]);
                        uint32_t maj_abc = fnMj(ss[0],ss[1],ss[2]);
                        uint32_t t0 = (ss[7]+sig1e)&MASK;
                        uint32_t t1 = (t0+ch_efg)&MASK;
                        uint32_t t2 = (t1+KN[57+r])&MASK;
                        uint32_t T1 = (t2+Wvals[r])&MASK;
                        uint32_t T2 = (sig0a+maj_abc)&MASK;

                        int base = r * ADDS_PER_ROUND;
                        uint8_t c[N];
                        extract_carries(ss[7], sig1e, c);
                        memcpy(&all_modes[(base+0)*N], c, N);
                        extract_carries(t0, ch_efg, c);
                        memcpy(&all_modes[(base+1)*N], c, N);
                        extract_carries(t1, KN[57+r], c);
                        memcpy(&all_modes[(base+2)*N], c, N);
                        extract_carries(t2, Wvals[r], c);
                        memcpy(&all_modes[(base+3)*N], c, N);
                        extract_carries(sig0a, maj_abc, c);
                        memcpy(&all_modes[(base+4)*N], c, N);
                        extract_carries(ss[3], T1, c);
                        memcpy(&all_modes[(base+5)*N], c, N);
                        extract_carries(T1, T2, c);
                        memcpy(&all_modes[(base+6)*N], c, N);

                        ss[7]=ss[6];ss[6]=ss[5];ss[5]=ss[4];ss[4]=(ss[3]+T1)&MASK;
                        ss[3]=ss[2];ss[2]=ss[1];ss[1]=ss[0];ss[0]=(T1+T2)&MASK;
                    }

                    /* Check collision */
                    uint32_t s5a[8],s5b[8];
                    memcpy(s5a,s4a,32);memcpy(s5b,s4b,32);
                    sha_round(s5a,KN[61],cw61a);sha_round(s5b,KN[61],cw61b);
                    uint32_t cw62a=(fns1(w60)+sc62a)&MASK;
                    uint32_t cw62b=(fns1(w60b)+sc62b)&MASK;
                    sha_round(s5a,KN[62],cw62a);sha_round(s5b,KN[62],cw62b);
                    sha_round(s5a,KN[63],cw63a);sha_round(s5b,KN[63],cw63b);
                    int coll = 1;
                    for (int r=0;r<8;r++) if(s5a[r]!=s5b[r]){coll=0;break;}

                    ht_insert(all_modes, coll);
                    total++;
                    if (coll) n_coll++;
                }
            }
        }
    }

    /* Analyze results */
    int unique_modes = ht_count;
    int coll_modes = 0;
    int multi_hit = 0;
    for (int i = 0; i < ht_count; i++) {
        if (ht_entries[i].is_collision) coll_modes++;
        if (ht_entries[i].count > 1) multi_hit++;
    }

    printf("Results:\n");
    printf("  Total inputs: %llu\n", (unsigned long long)total);
    printf("  Collisions: %llu\n", (unsigned long long)n_coll);
    printf("  Unique mode patterns: %d\n", unique_modes);
    printf("  Mode patterns with collisions: %d\n", coll_modes);
    printf("  Mode patterns appearing >1 time: %d\n", multi_hit);
    printf("  Compression: %llu / %d = %.2fx\n",
           (unsigned long long)total, unique_modes, (double)total / unique_modes);
    printf("  Collision mode concentration: %d patterns for %llu collisions\n",
           coll_modes, (unsigned long long)n_coll);

    if (unique_modes < (int)total) {
        printf("\n*** MODE DEDUP EXISTS: %d unique out of %llu = %.1f%% compression ***\n",
               unique_modes, (unsigned long long)total,
               100.0 * (1.0 - (double)unique_modes / total));
    } else {
        printf("\n  Mode patterns are injective — no dedup (same as carry DP)\n");
    }

    free(ht_entries); free(ht_buckets);
    return 0;
}
