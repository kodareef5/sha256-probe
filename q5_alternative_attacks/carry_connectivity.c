/*
 * carry_connectivity.c — Map carry-state connectivity across bit positions
 *
 * For each collision, the carry automaton builder showed that transitions
 * are deterministic (carry_state[k] -> carry_state[k+1] is 1-to-1).
 *
 * This tool goes deeper: for EACH carry bit (specific round, addition, bit),
 * it measures how many collisions have carry=0 vs carry=1 at that position.
 * This gives us the MARGINAL distribution of each carry bit.
 *
 * If a carry bit is 0 in ALL collisions or 1 in ALL collisions, it's
 * fully determined (invariant). We can fix it as a constant.
 *
 * If a carry bit is 0 in some and 1 in others, it's a branching variable.
 * The ratio tells us the branching probability.
 *
 * The number of truly FREE carry bits (those with 0<p<1) is the
 * effective dimensionality of the collision manifold in carry space.
 *
 * Also computes: which carry bits are CORRELATED (always equal/opposite)
 * to reduce the effective DOF further via carry-pair implications.
 *
 * Reads collision data from file. Uses carry_automaton_builder logic.
 *
 * Compile: gcc -O3 -march=native -o carry_connectivity carry_connectivity.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

#define MAX_COLL 4096
#define MAX_N 16
#define ROUNDS 7
#define ADDS_PER_ROUND 7
#define TOTAL_ADDS (ROUNDS * ADDS_PER_ROUND)

static int gN;
static uint32_t gMASK;
static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;
static uint32_t KN[64],IVN[8];
static inline uint32_t ror_n(uint32_t x,int k){k%=gN;return((x>>k)|(x<<(gN-k)))&gMASK;}
static inline uint32_t fnS0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static inline uint32_t fnS1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static inline uint32_t fns0(uint32_t x){return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&gMASK);}
static inline uint32_t fns1(uint32_t x){return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&gMASK);}
static inline uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&gMASK;}
static inline uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&gMASK;}
static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static int scale_rot(int k32){int r=(int)rint((double)k32*gN/32.0);return r<1?1:r;}

static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&gMASK;
    for(int i=16;i<57;i++)W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&gMASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&gMASK,T2=(fnS0(a)+fnMj(a,b,c))&gMASK;h=g;g=f;f=e;e=(d+T1)&gMASK;d=c;c=b;b=a;a=(T1+T2)&gMASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}
static inline void sha_round(uint32_t s[8],uint32_t k,uint32_t w){
    uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&gMASK,T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&gMASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&gMASK;s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&gMASK;
}
static inline uint32_t find_w2(const uint32_t s1[8],const uint32_t s2[8],int rnd,uint32_t w1){
    uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&gMASK;
    uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&gMASK;
    uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&gMASK;
    uint32_t T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&gMASK;
    return(w1+r1-r2+T21-T22)&gMASK;
}

/* Storage for carry-diff bits: [collision][flat_index] where flat = round*7*N + add*N + bit */
static uint8_t cdiff[MAX_COLL][TOTAL_ADDS * MAX_N];
static int n_coll;
static int n_flat; /* TOTAL_ADDS * gN */

static void extract_carries(uint32_t a, uint32_t b, uint32_t *carries) {
    uint32_t c = 0;
    for (int k = 0; k < gN; k++) {
        uint32_t s = ((a>>k)&1) + ((b>>k)&1) + c;
        carries[k] = s >> 1;
        c = carries[k];
    }
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);
    if (argc < 3) { fprintf(stderr, "Usage: %s N collision_file\n", argv[0]); return 1; }
    gN = atoi(argv[1]);
    gMASK = (1U << gN) - 1;
    n_flat = TOTAL_ADDS * gN;

    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&gMASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&gMASK;

    /* Read collisions (COLL format) */
    FILE *f = fopen(argv[2], "r");
    if (!f) { perror("fopen"); return 1; }
    n_coll = 0;
    uint32_t cw1[MAX_COLL][4];
    char line[256];
    while (fgets(line, sizeof(line), f) && n_coll < MAX_COLL) {
        uint32_t a[4], b[4];
        if (sscanf(line, "COLL %x %x %x %x", &a[0],&a[1],&a[2],&a[3]) == 4) {
            memcpy(cw1[n_coll], a, 16); n_coll++;
        } else if (sscanf(line, "%x %x %x %x | %x %x %x %x",
                          &a[0],&a[1],&a[2],&a[3],&b[0],&b[1],&b[2],&b[3]) == 8) {
            memcpy(cw1[n_coll], a, 16); n_coll++;
        }
    }
    fclose(f);
    printf("Loaded %d collisions at N=%d\n", n_coll, gN);

    /* Find candidate */
    uint32_t fills[]={gMASK,0,gMASK>>1,1U<<(gN-1)};
    uint32_t state1[8],state2[8],W1pre[57],W2pre[57];
    int found=0;
    for(int kbit=gN-1;kbit>=0&&!found;kbit--){
        uint32_t delta=1U<<kbit;
        for(int fi=0;fi<4&&!found;fi++){
            for(uint32_t m0=0;m0<=gMASK&&!found;m0++){
                uint32_t M1[16],M2[16];
                for(int i=0;i<16;i++){M1[i]=fills[fi];M2[i]=fills[fi];}
                M1[0]=m0;M2[0]=m0^delta;M2[9]=fills[fi]^delta;
                precompute(M1,state1,W1pre);precompute(M2,state2,W2pre);
                if(state1[0]!=state2[0])continue;
                /* Verify against first collision */
                uint32_t s1[8],s2[8];memcpy(s1,state1,32);memcpy(s2,state2,32);
                uint32_t W1[7],W2[7];
                for(int r=0;r<4;r++){W1[r]=cw1[0][r];W2[r]=find_w2(s1,s2,57+r,W1[r]);sha_round(s1,KN[57+r],W1[r]);sha_round(s2,KN[57+r],W2[r]);}
                W1[4]=(fns1(W1[2])+W1pre[54]+fns0(W1pre[46])+W1pre[45])&gMASK;
                W2[4]=(fns1(W2[2])+W2pre[54]+fns0(W2pre[46])+W2pre[45])&gMASK;
                W1[5]=(fns1(W1[3])+W1pre[55]+fns0(W1pre[47])+W1pre[46])&gMASK;
                W2[5]=(fns1(W2[3])+W2pre[55]+fns0(W2pre[47])+W2pre[46])&gMASK;
                W1[6]=(fns1(W1[4])+W1pre[56]+fns0(W1pre[48])+W1pre[47])&gMASK;
                W2[6]=(fns1(W2[4])+W2pre[56]+fns0(W2pre[48])+W2pre[47])&gMASK;
                for(int r=4;r<7;r++){sha_round(s1,KN[57+r],W1[r]);sha_round(s2,KN[57+r],W2[r]);}
                int ok=1;for(int r=0;r<8;r++)if(s1[r]!=s2[r]){ok=0;break;}
                if(ok){printf("Candidate: M[0]=0x%x fill=0x%x bit-%d\n",m0,fills[fi],kbit);found=1;}
            }
        }
    }
    if(!found){printf("Cannot find candidate\n");return 1;}

    /* Extract carry-diff bits for all collisions */
    const char *add_names[ADDS_PER_ROUND]={"h+S1","+Ch","+K","+W","S0M","d+T1","T1T2"};
    for (int c = 0; c < n_coll; c++) {
        uint32_t s1[8],s2[8]; memcpy(s1,state1,32); memcpy(s2,state2,32);
        uint32_t W1[4],W2[4];
        memcpy(W1, cw1[c], 16);
        for(int r=0;r<4;r++){W2[r]=find_w2(s1,s2,57+r,W1[r]);sha_round(s1,KN[57+r],W1[r]);sha_round(s2,KN[57+r],W2[r]);}

        /* Re-run with carry extraction */
        memcpy(s1,state1,32);memcpy(s2,state2,32);
        for(int r=0;r<4;r++)W2[r]=find_w2(s1,s2,57+r,W1[r]);

        /* Extract per-round */
        uint32_t sa[8],sb[8]; memcpy(sa,state1,32); memcpy(sb,state2,32);
        for (int r = 0; r < ROUNDS; r++) {
            uint32_t sig1a=fnS1(sa[4]),sig1b=fnS1(sb[4]);
            uint32_t cha=fnCh(sa[4],sa[5],sa[6]),chb=fnCh(sb[4],sb[5],sb[6]);
            uint32_t sig0a=fnS0(sa[0]),sig0b=fnS0(sb[0]);
            uint32_t maja=fnMj(sa[0],sa[1],sa[2]),majb=fnMj(sb[0],sb[1],sb[2]);

            uint32_t t0a=(sa[7]+sig1a)&gMASK,t0b=(sb[7]+sig1b)&gMASK;
            uint32_t t1a=(t0a+cha)&gMASK,t1b=(t0b+chb)&gMASK;
            uint32_t t2a=(t1a+KN[57+r])&gMASK,t2b=(t1b+KN[57+r])&gMASK;

            uint32_t Wra, Wrb;
            if (r < 4) { Wra = W1[r]; Wrb = W2[r]; }
            else {
                uint32_t _W1[7]={cw1[c][0],cw1[c][1],cw1[c][2],cw1[c][3],0,0,0};
                uint32_t ts1[8],ts2[8]; memcpy(ts1,state1,32); memcpy(ts2,state2,32);
                uint32_t _W2[4]; for(int i=0;i<4;i++){_W2[i]=find_w2(ts1,ts2,57+i,_W1[i]);sha_round(ts1,KN[57+i],_W1[i]);sha_round(ts2,KN[57+i],_W2[i]);}
                _W1[4]=(fns1(_W1[2])+W1pre[54]+fns0(W1pre[46])+W1pre[45])&gMASK;
                uint32_t _W2_4=(fns1(_W2[2])+W2pre[54]+fns0(W2pre[46])+W2pre[45])&gMASK;
                _W1[5]=(fns1(_W1[3])+W1pre[55]+fns0(W1pre[47])+W1pre[46])&gMASK;
                uint32_t _W2_5=(fns1(_W2[3])+W2pre[55]+fns0(W2pre[47])+W2pre[46])&gMASK;
                _W1[6]=(fns1(_W1[4])+W1pre[56]+fns0(W1pre[48])+W1pre[47])&gMASK;
                uint32_t _W2_6=(fns1(_W2_4)+W2pre[56]+fns0(W2pre[48])+W2pre[47])&gMASK;
                if(r==4){Wra=_W1[4];Wrb=_W2_4;}
                else if(r==5){Wra=_W1[5];Wrb=_W2_5;}
                else{Wra=_W1[6];Wrb=_W2_6;}
            }

            uint32_t T1a=(t2a+Wra)&gMASK,T1b=(t2b+Wrb)&gMASK;
            uint32_t T2a=(sig0a+maja)&gMASK,T2b=(sig0b+majb)&gMASK;

            /* Extract carries and compute diffs */
            uint32_t c1[MAX_N],c2[MAX_N];
            int base = r * ADDS_PER_ROUND * gN;

            extract_carries(sa[7],sig1a,c1);extract_carries(sb[7],sig1b,c2);
            for(int k=0;k<gN;k++)cdiff[c][base+0*gN+k]=c1[k]^c2[k];

            extract_carries(t0a,cha,c1);extract_carries(t0b,chb,c2);
            for(int k=0;k<gN;k++)cdiff[c][base+1*gN+k]=c1[k]^c2[k];

            extract_carries(t1a,KN[57+r],c1);extract_carries(t1b,KN[57+r],c2);
            for(int k=0;k<gN;k++)cdiff[c][base+2*gN+k]=c1[k]^c2[k];

            extract_carries(t2a,Wra,c1);extract_carries(t2b,Wrb,c2);
            for(int k=0;k<gN;k++)cdiff[c][base+3*gN+k]=c1[k]^c2[k];

            extract_carries(sig0a,maja,c1);extract_carries(sig0b,majb,c2);
            for(int k=0;k<gN;k++)cdiff[c][base+4*gN+k]=c1[k]^c2[k];

            extract_carries(sa[3],T1a,c1);extract_carries(sb[3],T1b,c2);
            for(int k=0;k<gN;k++)cdiff[c][base+5*gN+k]=c1[k]^c2[k];

            extract_carries(T1a,T2a,c1);extract_carries(T1b,T2b,c2);
            for(int k=0;k<gN;k++)cdiff[c][base+6*gN+k]=c1[k]^c2[k];

            /* Advance state */
            sa[7]=sa[6];sa[6]=sa[5];sa[5]=sa[4];sa[4]=(sa[3]+T1a)&gMASK;
            sa[3]=sa[2];sa[2]=sa[1];sa[1]=sa[0];sa[0]=(T1a+T2a)&gMASK;
            sb[7]=sb[6];sb[6]=sb[5];sb[5]=sb[4];sb[4]=(sb[3]+T1b)&gMASK;
            sb[3]=sb[2];sb[2]=sb[1];sb[1]=sb[0];sb[0]=(T1b+T2b)&gMASK;
        }
    }

    /* === Analysis 1: Marginal distribution of each carry-diff bit === */
    printf("\n=== Carry-Diff Marginal Distribution ===\n");
    int n_invariant_0 = 0, n_invariant_1 = 0, n_free = 0;

    for (int i = 0; i < n_flat; i++) {
        int count_1 = 0;
        for (int c = 0; c < n_coll; c++) count_1 += cdiff[c][i];
        if (count_1 == 0) n_invariant_0++;
        else if (count_1 == n_coll) n_invariant_1++;
        else n_free++;
    }

    printf("Total carry-diff bits: %d\n", n_flat);
    printf("Invariant (all 0): %d (%.1f%%)\n", n_invariant_0, 100.0*n_invariant_0/n_flat);
    printf("Invariant (all 1): %d (%.1f%%)\n", n_invariant_1, 100.0*n_invariant_1/n_flat);
    printf("Free (mixed): %d (%.1f%%)\n", n_free, 100.0*n_free/n_flat);
    printf("Total invariant: %d (%.1f%%)\n", n_invariant_0+n_invariant_1,
           100.0*(n_invariant_0+n_invariant_1)/n_flat);

    /* === Analysis 2: Entropy of free carry-diff bits === */
    printf("\n=== Entropy Analysis ===\n");
    double total_entropy = 0;
    for (int i = 0; i < n_flat; i++) {
        int c1 = 0;
        for (int c = 0; c < n_coll; c++) c1 += cdiff[c][i];
        if (c1 == 0 || c1 == n_coll) continue;
        double p = (double)c1 / n_coll;
        total_entropy += -p*log2(p) - (1-p)*log2(1-p);
    }
    printf("Total binary entropy of free bits: %.1f bits\n", total_entropy);
    printf("Effective independent DOF: %.1f\n", total_entropy);
    printf("log2(collisions) = %.1f\n", log2(n_coll));
    printf("Ratio DOF/log2(C) = %.2f\n", total_entropy / log2(n_coll));

    /* === Analysis 3: Pairwise correlations among free bits === */
    printf("\n=== Pairwise Correlation Summary ===\n");

    /* Find indices of free bits */
    int free_idx[1024]; int n_fi = 0;
    for (int i = 0; i < n_flat && n_fi < 1024; i++) {
        int c1 = 0;
        for (int c = 0; c < n_coll; c++) c1 += cdiff[c][i];
        if (c1 > 0 && c1 < n_coll) free_idx[n_fi++] = i;
    }

    /* Count perfectly correlated pairs (XOR = constant across all collisions) */
    int n_equal_pairs = 0, n_opposite_pairs = 0;
    for (int i = 0; i < n_fi && i < 200; i++) {
        for (int j = i+1; j < n_fi && j < 200; j++) {
            int xor_count = 0;
            for (int c = 0; c < n_coll; c++)
                xor_count += cdiff[c][free_idx[i]] ^ cdiff[c][free_idx[j]];
            if (xor_count == 0) n_equal_pairs++;
            if (xor_count == n_coll) n_opposite_pairs++;
        }
    }

    int n_tested = (n_fi < 200 ? n_fi : 200);
    int n_possible = n_tested * (n_tested - 1) / 2;
    printf("Free bits tested: %d (of %d)\n", n_tested, n_fi);
    printf("Perfectly correlated pairs (equal): %d / %d\n", n_equal_pairs, n_possible);
    printf("Perfectly anti-correlated (opposite): %d / %d\n", n_opposite_pairs, n_possible);
    printf("Total determined pairs: %d (%.1f%%)\n",
           n_equal_pairs + n_opposite_pairs,
           100.0*(n_equal_pairs+n_opposite_pairs)/n_possible);

    /* Effective DOF after pair reduction */
    /* Each equal pair reduces DOF by 1. Each opposite pair reduces by 1. */
    /* This is an upper bound — the actual reduction from a GF(2) system could be more. */
    int dof_reduction = n_equal_pairs + n_opposite_pairs;
    printf("\nEffective DOF (free bits - pair reductions): %d - %d = %d\n",
           n_fi, dof_reduction, n_fi - dof_reduction);
    printf("log2(collisions) = %.1f\n", log2(n_coll));

    printf("\n=== Done ===\n");
    return 0;
}
