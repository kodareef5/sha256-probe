/*
 * Near-Collision Enumeration at N=4: find ALL inputs where a-g match (h free)
 *
 * Exhaustive 2^32 search in C. For each input, evaluate 7-round tail for
 * both messages, check if registers a-g match. If yes, record dh.
 *
 * This characterizes the "residual" after relaxing register h.
 *
 * Compile: gcc -O3 -march=native -o near_collision_enum_n4 near_collision_enum_n4.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

#define N 4
#define MASK ((1U << N) - 1)
#define MSB (1U << (N - 1))

static int r_Sig0[3], r_Sig1[3], r_sig0[2], r_sig1[2], s_sig0, s_sig1;
static inline uint32_t ror_n(uint32_t x, int k) { k=k%N; return ((x>>k)|(x<<(N-k)))&MASK; }
static inline uint32_t fn_S0(uint32_t a) { return ror_n(a,r_Sig0[0])^ror_n(a,r_Sig0[1])^ror_n(a,r_Sig0[2]); }
static inline uint32_t fn_S1(uint32_t e) { return ror_n(e,r_Sig1[0])^ror_n(e,r_Sig1[1])^ror_n(e,r_Sig1[2]); }
static inline uint32_t fn_s0(uint32_t x) { return ror_n(x,r_sig0[0])^ror_n(x,r_sig0[1])^((x>>s_sig0)&MASK); }
static inline uint32_t fn_s1(uint32_t x) { return ror_n(x,r_sig1[0])^ror_n(x,r_sig1[1])^((x>>s_sig1)&MASK); }
static inline uint32_t fn_Ch(uint32_t e, uint32_t f, uint32_t g) { return ((e&f)^((~e)&g))&MASK; }
static inline uint32_t fn_Maj(uint32_t a, uint32_t b, uint32_t c) { return ((a&b)^(a&c)^(b&c))&MASK; }

static const uint32_t K32[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};
static const uint32_t IV32[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};

static uint32_t KN[64], IVN[8];
static uint32_t state1[8], state2[8], W1_pre[57], W2_pre[57];

static int scale_rot(int k32) { int r=(int)rint((double)k32*N/32.0); return r<1?1:r; }

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for(int i=0;i<16;i++) W[i]=M[i]&MASK;
    for(int i=16;i<57;i++) W[i]=(fn_s1(W[i-2])+W[i-7]+fn_s0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){
        uint32_t T1=(h+fn_S1(e)+fn_Ch(e,f,g)+KN[i]+W[i])&MASK;
        uint32_t T2=(fn_S0(a)+fn_Maj(a,b,c))&MASK;
        h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;
    }
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

int main() {
    setbuf(stdout, NULL);
    r_Sig0[0]=scale_rot(2);r_Sig0[1]=scale_rot(13);r_Sig0[2]=scale_rot(22);
    r_Sig1[0]=scale_rot(6);r_Sig1[1]=scale_rot(11);r_Sig1[2]=scale_rot(25);
    r_sig0[0]=scale_rot(7);r_sig0[1]=scale_rot(18);s_sig0=scale_rot(3);
    r_sig1[0]=scale_rot(17);r_sig1[1]=scale_rot(19);s_sig1=scale_rot(10);
    for(int i=0;i<64;i++) KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++) IVN[i]=IV32[i]&MASK;

    /* Find candidate */
    int found=0;
    for(uint32_t m0=0;m0<=MASK&&!found;m0++){
        uint32_t M1[16],M2[16];
        for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
        M1[0]=m0;M2[0]=m0^MSB;M2[9]=MASK^MSB;
        precompute(M1,state1,W1_pre);precompute(M2,state2,W2_pre);
        if(state1[0]==state2[0]){printf("Candidate: M[0]=0x%x\n",m0);found=1;}
    }
    if(!found){printf("No candidate\n");return 1;}

    printf("Near-Collision Enumeration at N=%d\n", N);
    printf("Finding all inputs where registers a-g match (h free)\n\n");

    uint64_t n_near = 0, n_full = 0;
    uint32_t dh_counts[1<<N]; /* count of each dh_xor value */
    memset(dh_counts, 0, sizeof(dh_counts));

    time_t t0 = time(NULL);

    for(uint64_t inp=0; inp < (1ULL<<(2*4*N)); inp++){
        uint32_t w1[4], w2[4];
        w1[0]=(inp>>0)&MASK; w1[1]=(inp>>4)&MASK; w1[2]=(inp>>8)&MASK; w1[3]=(inp>>12)&MASK;
        w2[0]=(inp>>16)&MASK; w2[1]=(inp>>20)&MASK; w2[2]=(inp>>24)&MASK; w2[3]=(inp>>28)&MASK;

        uint32_t W1[7],W2[7];
        for(int i=0;i<4;i++){W1[i]=w1[i];W2[i]=w2[i];}
        W1[4]=(fn_s1(W1[2])+W1_pre[54]+fn_s0(W1_pre[46])+W1_pre[45])&MASK;
        W2[4]=(fn_s1(W2[2])+W2_pre[54]+fn_s0(W2_pre[46])+W2_pre[45])&MASK;
        W1[5]=(fn_s1(W1[3])+W1_pre[55]+fn_s0(W1_pre[47])+W1_pre[46])&MASK;
        W2[5]=(fn_s1(W2[3])+W2_pre[55]+fn_s0(W2_pre[47])+W2_pre[46])&MASK;
        W1[6]=(fn_s1(W1[4])+W1_pre[56]+fn_s0(W1_pre[48])+W1_pre[47])&MASK;
        W2[6]=(fn_s1(W2[4])+W2_pre[56]+fn_s0(W2_pre[48])+W2_pre[47])&MASK;

        uint32_t a1=state1[0],b1=state1[1],c1=state1[2],d1=state1[3];
        uint32_t e1=state1[4],f1=state1[5],g1=state1[6],h1=state1[7];
        uint32_t a2=state2[0],b2=state2[1],c2=state2[2],d2=state2[3];
        uint32_t e2=state2[4],f2=state2[5],g2=state2[6],h2=state2[7];

        for(int i=0;i<7;i++){
            uint32_t T1a=(h1+fn_S1(e1)+fn_Ch(e1,f1,g1)+KN[57+i]+W1[i])&MASK;
            uint32_t T2a=(fn_S0(a1)+fn_Maj(a1,b1,c1))&MASK;
            h1=g1;g1=f1;f1=e1;e1=(d1+T1a)&MASK;d1=c1;c1=b1;b1=a1;a1=(T1a+T2a)&MASK;
            uint32_t T1b=(h2+fn_S1(e2)+fn_Ch(e2,f2,g2)+KN[57+i]+W2[i])&MASK;
            uint32_t T2b=(fn_S0(a2)+fn_Maj(a2,b2,c2))&MASK;
            h2=g2;g2=f2;f2=e2;e2=(d2+T1b)&MASK;d2=c2;c2=b2;b2=a2;a2=(T1b+T2b)&MASK;
        }

        /* Check a-g match */
        if(a1==a2 && b1==b2 && c1==c2 && d1==d2 && e1==e2 && f1==f2 && g1==g2){
            uint32_t dh = (h1^h2)&MASK;
            dh_counts[dh]++;
            n_near++;
            if(dh==0) n_full++;
        }

        if((inp & 0x0FFFFFFF)==0 && inp>0){
            time_t now=time(NULL);
            printf("  [%llu/%llu] %llu%% near=%llu full=%llu (%lds)\n",
                   (unsigned long long)inp,(unsigned long long)(1ULL<<32),
                   (unsigned long long)(100*inp/(1ULL<<32)),
                   (unsigned long long)n_near,(unsigned long long)n_full,
                   now-t0);
        }
    }

    time_t elapsed = time(NULL) - t0;
    printf("\n=== Results ===\n");
    printf("Total inputs: 2^32 = 4294967296\n");
    printf("Near-collisions (a-g match): %llu\n", (unsigned long long)n_near);
    printf("Full collisions (all match): %llu\n", (unsigned long long)n_full);
    printf("NC/full ratio: %.1f\n", n_near>0?(double)n_near/n_full:0);
    printf("NC density: 1 per %llu inputs\n", n_near>0?(unsigned long long)((1ULL<<32)/n_near):0);
    printf("Time: %lds\n", elapsed);

    printf("\n=== dh XOR Distribution ===\n");
    printf("  dh_xor  count  (of %llu near-collisions)\n", (unsigned long long)n_near);
    for(int d=0; d<(1<<N); d++){
        if(dh_counts[d]>0){
            int hw=__builtin_popcount(d);
            printf("  0x%x (hw=%d): %u  (%.1f%%)\n", d, hw, dh_counts[d],
                   100.0*dh_counts[d]/n_near);
        }
    }

    /* Check if dh is confined to a subspace */
    int rank=0;
    uint32_t basis[N];
    memset(basis,0,sizeof(basis));
    for(int d=0;d<(1<<N);d++){
        if(dh_counts[d]==0) continue;
        uint32_t v=d;
        for(int i=0;i<rank;i++) if((v>>i)&1) v^=basis[i];
        if(v){
            /* New basis vector */
            int pos=0; while(!((v>>pos)&1)) pos++;
            basis[rank]=v;
            rank++;
        }
    }
    printf("\n=== dh Subspace ===\n");
    printf("  GF(2) rank of dh values: %d/%d\n", rank, N);
    if(rank < N)
        printf("  *** dh confined to %d-dim subspace! %d bits DETERMINED ***\n", rank, N-rank);
    else
        printf("  dh spans full %d-bit space\n", N);

    printf("\nDone.\n");
    return 0;
}
