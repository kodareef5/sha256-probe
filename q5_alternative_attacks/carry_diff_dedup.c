/*
 * carry_diff_dedup.c — Measure carry-DIFF deduplication at chunk boundary
 *
 * For each of 2^32 configs: extract carry-out diffs (path1 XOR path2) at bit 3.
 * Count unique carry-diff fingerprints using a hash table.
 * Compare with 260 collision carry-diffs (from carry automaton: width=260).
 *
 * This tests whether carry-DIFFS compress better than raw carries
 * (which showed 0% deduplication).
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N 8
#define MASK 0xFF
#define MSB 0x80

static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;
static int SR(int k){int r=(int)rint((double)k*N/32.0);return r<1?1:r;}
static uint32_t KN[64],IVN[8];
static inline uint32_t ror_n(uint32_t x,int k){k%=N;return((x>>k)|(x<<(N-k)))&MASK;}
static inline uint32_t fnS0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static inline uint32_t fnS1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static inline uint32_t fns0(uint32_t x){return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&MASK);}
static inline uint32_t fns1(uint32_t x){return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&MASK);}
static inline uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&MASK;}
static inline uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&MASK;}
static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t W1p[57],W2p[57],state1[8],state2[8];
static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&MASK;for(int i=16;i<57;i++)W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&MASK,T2=(fnS0(a)+fnMj(a,b,c))&MASK;h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}
static inline void sha_round(uint32_t s[8],uint32_t k,uint32_t w){
    uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&MASK,T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&MASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;
}
static inline uint32_t find_w2(const uint32_t s1[8],const uint32_t s2[8],int rnd,uint32_t w1){
    uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&MASK;
    uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&MASK;
    uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&MASK;
    uint32_t T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&MASK;
    return(w1+r1-r2+T21-T22)&MASK;
}

/* Extract carry at bit 3 from addition a+b */
static inline uint32_t carry_at_bit3(uint32_t a, uint32_t b) {
    /* Carry out of bit 3 = bit 4 of (a + b) differs from bit 4 of (a XOR b) */
    uint32_t low4_sum = (a & 0xF) + (b & 0xF);
    return (low4_sum >> 4) & 1;
}

/* Hash table for carry-diff fingerprints */
#define HT_BITS 22
#define HT_SIZE (1U << HT_BITS)
#define HT_MASK (HT_SIZE - 1)
static uint64_t *ht_keys;
static uint32_t *ht_counts;
static uint64_t ht_unique = 0;

static void ht_init(void) {
    ht_keys = calloc(HT_SIZE, sizeof(uint64_t));
    ht_counts = calloc(HT_SIZE, sizeof(uint32_t));
}

static int ht_insert(uint64_t key) {
    uint32_t h = (uint32_t)(key * 0x9E3779B97F4A7C15ULL >> 42) & HT_MASK;
    for (int i = 0; i < 64; i++) {
        uint32_t idx = (h + i) & HT_MASK;
        if (ht_counts[idx] == 0) {
            ht_keys[idx] = key;
            ht_counts[idx] = 1;
            ht_unique++;
            return 1; /* new */
        }
        if (ht_keys[idx] == key) {
            ht_counts[idx]++;
            return 0; /* duplicate */
        }
    }
    return -1; /* full */
}

int main() {
    setbuf(stdout, NULL);
    rS0[0]=SR(2);rS0[1]=SR(13);rS0[2]=SR(22);
    rS1[0]=SR(6);rS1[1]=SR(11);rS1[2]=SR(25);
    rs0[0]=SR(7);rs0[1]=SR(18);ss0=SR(3);
    rs1[0]=SR(17);rs1[1]=SR(19);ss1=SR(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;

    uint32_t M1[16],M2[16];
    for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
    M1[0]=0x67;M2[0]=0x67^MSB;M2[9]=MASK^MSB;
    precompute(M1,state1,W1p);precompute(M2,state2,W2p);
    printf("N=8, M[0]=0x67, MSB kernel\n");
    printf("Measuring carry-DIFF deduplication at bit-4 boundary\n\n");

    ht_init();
    struct timespec t0; clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t n_total = 0, n_coll = 0;

    for (uint32_t w57 = 0; w57 < 256; w57++) {
        uint32_t s57a[8],s57b[8];
        memcpy(s57a,state1,32);memcpy(s57b,state2,32);
        uint32_t w57b=find_w2(s57a,s57b,57,w57);
        sha_round(s57a,KN[57],w57);sha_round(s57b,KN[57],w57b);

        for (uint32_t w58 = 0; w58 < 256; w58++) {
            uint32_t s58a[8],s58b[8];
            memcpy(s58a,s57a,32);memcpy(s58b,s57b,32);
            uint32_t w58b=find_w2(s58a,s58b,58,w58);
            sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);

            for (uint32_t w59 = 0; w59 < 256; w59++) {
                uint32_t s59a[8],s59b[8];
                memcpy(s59a,s58a,32);memcpy(s59b,s58b,32);
                uint32_t w59b=find_w2(s59a,s59b,59,w59);
                sha_round(s59a,KN[59],w59);sha_round(s59b,KN[59],w59b);

                for (uint32_t w60 = 0; w60 < 256; w60++) {
                    n_total++;
                    uint32_t s60a[8],s60b[8];
                    memcpy(s60a,s59a,32);memcpy(s60b,s59b,32);
                    uint32_t w60b=find_w2(s60a,s60b,60,w60);
                    sha_round(s60a,KN[60],w60);sha_round(s60b,KN[60],w60b);

                    /* Extract register-DIFF fingerprint at state60 */
                    /* Use modular diff of all 8 registers, pack into 64 bits */
                    uint64_t diff_fp = 0;
                    for (int r = 0; r < 8; r++) {
                        diff_fp |= (uint64_t)((s60a[r] - s60b[r]) & MASK) << (r * 8);
                    }
                    ht_insert(diff_fp);

                    /* Check collision */
                    uint32_t W1[7]={w57,w58,w59,w60,0,0,0},W2[7]={w57b,w58b,w59b,w60b,0,0,0};
                    W1[4]=(fns1(W1[2])+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;
                    W2[4]=(fns1(W2[2])+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
                    W1[5]=(fns1(W1[3])+W1p[55]+fns0(W1p[47])+W1p[46])&MASK;
                    W2[5]=(fns1(W2[3])+W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
                    W1[6]=(fns1(W1[4])+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;
                    W2[6]=(fns1(W2[4])+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;
                    uint32_t fa[8],fb[8]; memcpy(fa,s60a,32);memcpy(fb,s60b,32);
                    for(int r=4;r<7;r++){sha_round(fa,KN[57+r],W1[r]);sha_round(fb,KN[57+r],W2[r]);}
                    int ok=1;for(int r=0;r<8;r++)if(fa[r]!=fb[r]){ok=0;break;}
                    if(ok) n_coll++;
                }
            }
        }
        struct timespec t1; clock_gettime(CLOCK_MONOTONIC,&t1);
        double el=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
        if ((w57&0xF)==0xF)
            printf("[%5.1f%%] w57=%02x total=%llu unique_diffs=%llu coll=%llu %.1fs\n",
                   100.0*(w57+1)/256, w57, (unsigned long long)n_total,
                   (unsigned long long)ht_unique, (unsigned long long)n_coll, el);
    }

    struct timespec t1; clock_gettime(CLOCK_MONOTONIC,&t1);
    double el=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;

    printf("\n=== RESULTS ===\n");
    printf("Total configs:        %llu\n", (unsigned long long)n_total);
    printf("Unique state60 diffs: %llu\n", (unsigned long long)ht_unique);
    printf("Collisions:           %llu\n", (unsigned long long)n_coll);
    printf("Deduplication ratio:  %.1fx\n", (double)n_total / ht_unique);
    printf("Time: %.1fs\n", el);

    if (ht_unique < n_total / 10)
        printf("\n*** MASSIVE DEDUPLICATION: %.0fx compression! ***\n",
               (double)n_total / ht_unique);
    else
        printf("\n(Minimal deduplication — diffs are mostly unique)\n");

    free(ht_keys); free(ht_counts);
    return 0;
}
