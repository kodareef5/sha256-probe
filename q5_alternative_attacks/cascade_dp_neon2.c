/*
 * cascade_dp_neon2.c — Schedule-diff pruned NEON cascade DP
 *
 * KEY OPTIMIZATION: g63 = f62 = e61 = d60 + T1_61. Since dd60=0 (cascade),
 * de61 = dT1_61 = dW[61] (since all state60 diffs are 0).
 * For collision: dg63=0 requires dW[61]=0.
 * Similarly: c63 = b62 = a61, dc63 = da61 = dW[61].
 *
 * This ELIMINATES ~(1-1/2^N) of W1[59] values at no cost!
 * Search: O(2^{3N}) instead of O(2^{4N}).
 * At N=12: 2^36 instead of 2^48. ~4096x speedup.
 *
 * Compile (Apple Silicon):
 *   gcc -O3 -march=native -Xclang -fopenmp \
 *       -I/opt/homebrew/opt/libomp/include \
 *       -L/opt/homebrew/opt/libomp/lib -lomp \
 *       -o cascade_dp_neon2 cascade_dp_neon2.c -lm
 *
 * Usage: ./cascade_dp_neon2 [N] [num_threads]
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <arm_neon.h>

static int gN;
static uint32_t gMASK, gMSB;
static int rS0[3], rS1[3], rs0[2], rs1[2], ss0, ss1;

static inline uint32_t ror_n(uint32_t x, int k) {
    k = k % gN; return ((x >> k) | (x << (gN - k))) & gMASK;
}
static inline uint32_t fnS0(uint32_t a) { return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]); }
static inline uint32_t fnS1(uint32_t e) { return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]); }
static inline uint32_t fns0(uint32_t x) { return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&gMASK); }
static inline uint32_t fns1(uint32_t x) { return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&gMASK); }
static inline uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g) { return((e&f)^((~e)&g))&gMASK; }
static inline uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c) { return((a&b)^(a&c)^(b&c))&gMASK; }

static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t KN[64], IVN[8], state1[8], state2[8], W1p[57], W2p[57];

static int scale_rot(int k) { int r=(int)rint((double)k*gN/32.0); return r<1?1:r; }

static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for(int i=0;i<16;i++) W[i]=M[i]&gMASK;
    for(int i=16;i<57;i++) W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&gMASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){
        uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&gMASK,T2=(fnS0(a)+fnMj(a,b,c))&gMASK;
        h=g;g=f;f=e;e=(d+T1)&gMASK;d=c;c=b;b=a;a=(T1+T2)&gMASK;
    }
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}
static inline void sha_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&gMASK;
    uint32_t T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&gMASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&gMASK;
    s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&gMASK;
}
static inline uint32_t find_w2(const uint32_t s1[8], const uint32_t s2[8], int rnd, uint32_t w1) {
    uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&gMASK;
    uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&gMASK;
    uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&gMASK;
    uint32_t T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&gMASK;
    return(w1+r1-r2+T21-T22)&gMASK;
}

/* ---- NEON ---- */
static int16x8_t rot_neg[16], rot_pos[16];
static uint16x8_t mask_vec;
static void init_neon(void) {
    mask_vec = vdupq_n_u16((uint16_t)gMASK);
    for(int k=0;k<16;k++){
        int kk=k%gN;
        rot_neg[k]=vdupq_n_s16((int16_t)(-kk));
        rot_pos[k]=vdupq_n_s16((int16_t)(gN-kk));
    }
}
static inline uint16x8_t nror(uint16x8_t x, int k) {
    return vandq_u16(vorrq_u16(vshlq_u16(x,rot_neg[k]),vshlq_u16(x,rot_pos[k])),mask_vec);
}
static inline uint16x8_t nS0(uint16x8_t a) { return veorq_u16(veorq_u16(nror(a,rS0[0]),nror(a,rS0[1])),nror(a,rS0[2])); }
static inline uint16x8_t nS1(uint16x8_t e) { return veorq_u16(veorq_u16(nror(e,rS1[0]),nror(e,rS1[1])),nror(e,rS1[2])); }
static inline uint16x8_t ns1(uint16x8_t x) {
    int16x8_t neg_ss1=vdupq_n_s16((int16_t)(-ss1));
    return veorq_u16(veorq_u16(nror(x,rs1[0]),nror(x,rs1[1])),vandq_u16(vshlq_u16(x,neg_ss1),mask_vec));
}
static inline uint16x8_t nCh(uint16x8_t e,uint16x8_t f,uint16x8_t g) { return veorq_u16(vandq_u16(e,f),vbicq_u16(g,e)); }
static inline uint16x8_t nMj(uint16x8_t a,uint16x8_t b,uint16x8_t c) { return veorq_u16(veorq_u16(vandq_u16(a,b),vandq_u16(a,c)),vandq_u16(b,c)); }

static inline void nsha_round(uint16x8_t s[8], uint16x8_t k, uint16x8_t w) {
    uint16x8_t T1=vandq_u16(vaddq_u16(vaddq_u16(vaddq_u16(s[7],nS1(s[4])),nCh(s[4],s[5],s[6])),vaddq_u16(k,w)),mask_vec);
    uint16x8_t T2=vandq_u16(vaddq_u16(nS0(s[0]),nMj(s[0],s[1],s[2])),mask_vec);
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=vandq_u16(vaddq_u16(s[3],T1),mask_vec);
    s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=vandq_u16(vaddq_u16(T1,T2),mask_vec);
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);
    gN = argc>1 ? atoi(argv[1]) : 12;
    int nthreads = argc>2 ? atoi(argv[2]) : 8;
    if(gN>16){printf("N<=16 required\n");return 1;}

    gMASK=(1U<<gN)-1; gMSB=1U<<(gN-1);
    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&gMASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&gMASK;
    init_neon();

    /* Find candidate */
    uint32_t fills[]={gMASK,0,gMASK>>1,gMSB,0x55&gMASK,0xAA&gMASK};
    int found=0;
    for(int fi=0;fi<6&&!found;fi++){
        for(uint32_t m0=0;m0<=gMASK&&!found;m0++){
            uint32_t M1[16],M2[16];
            for(int i=0;i<16;i++){M1[i]=fills[fi];M2[i]=fills[fi];}
            M1[0]=m0;M2[0]=m0^gMSB;M2[9]=fills[fi]^gMSB;
            precompute(M1,state1,W1p);precompute(M2,state2,W2p);
            if(state1[0]==state2[0]){printf("N=%d M[0]=0x%x fill=0x%x\n",gN,m0,fills[fi]);found=1;}
        }
    }
    if(!found){printf("No candidate\n");return 1;}

    /* Schedule-diff constants for pruning */
    uint32_t sched61_const1 = (W1p[54]+fns0(W1p[46])+W1p[45]) & gMASK;
    uint32_t sched61_const2 = (W2p[54]+fns0(W2p[46])+W2p[45]) & gMASK;

    printf("Schedule-diff pruned NEON cascade DP at N=%d\n", gN);
    printf("Pruning: dW[61]=0 necessary (g63=e61, de61=dW[61])\n");
    printf("Search: O(2^{3N}) = O(2^%d) = %llu\n", 3*gN, (unsigned long long)(1ULL<<(3*gN)));
    printf("vs brute: O(2^{4N}) = O(2^%d) — speedup: %dx\n", 4*gN, 1<<gN);
    printf("OpenMP: %d threads, NEON: 8x vectorized\n\n", nthreads);

    struct timespec t0; clock_gettime(CLOCK_MONOTONIC, &t0);
    uint64_t n_coll_global = 0;
    uint64_t n_w59_survive = 0; /* count how many W1[59] pass the dW[61] check */

    #pragma omp parallel num_threads(nthreads) reduction(+:n_coll_global,n_w59_survive)
    {
        uint64_t local_coll = 0;

        #pragma omp for schedule(dynamic, 1)
        for(uint32_t w57=0; w57<(1U<<gN); w57++){
            uint32_t s57a[8],s57b[8];
            memcpy(s57a,state1,32); memcpy(s57b,state2,32);
            uint32_t w57b = find_w2(s57a,s57b,57,w57);
            sha_round(s57a,KN[57],w57); sha_round(s57b,KN[57],w57b);

            for(uint32_t w58=0; w58<(1U<<gN); w58++){
                uint32_t s58a[8],s58b[8];
                memcpy(s58a,s57a,32); memcpy(s58b,s57b,32);
                uint32_t w58b = find_w2(s58a,s58b,58,w58);
                sha_round(s58a,KN[58],w58); sha_round(s58b,KN[58],w58b);

                for(uint32_t w59=0; w59<(1U<<gN); w59++){
                    /* PRUNE: check dW[61] = 0 */
                    uint32_t w59b = find_w2(s58a,s58b,59,w59);
                    uint32_t W1_61 = (fns1(w59) + sched61_const1) & gMASK;
                    uint32_t W2_61 = (fns1(w59b) + sched61_const2) & gMASK;
                    if(W1_61 != W2_61) continue; /* dW[61] != 0 → no collision possible */

                    n_w59_survive++;

                    /* Compute state59 (only for survivors) */
                    uint32_t s59a[8],s59b[8];
                    memcpy(s59a,s58a,32); memcpy(s59b,s58b,32);
                    sha_round(s59a,KN[59],w59); sha_round(s59b,KN[59],w59b);

                    /* Precompute schedule and cascade for inner loop */
                    uint32_t cas_off60 = find_w2(s59a,s59b,60,0);
                    uint32_t W1_63 = (fns1(W1_61)+W1p[56]+fns0(W1p[48])+W1p[47])&gMASK;
                    uint32_t W2_63 = (fns1(W2_61)+W2p[56]+fns0(W2p[48])+W2p[47])&gMASK;
                    uint32_t sc62c1 = (W1p[55]+fns0(W1p[47])+W1p[46])&gMASK;
                    uint32_t sc62c2 = (W2p[55]+fns0(W2p[47])+W2p[46])&gMASK;

                    uint16x8_t k60v=vdupq_n_u16((uint16_t)KN[60]);
                    uint16x8_t k61v=vdupq_n_u16((uint16_t)KN[61]);
                    uint16x8_t k62v=vdupq_n_u16((uint16_t)KN[62]);
                    uint16x8_t k63v=vdupq_n_u16((uint16_t)KN[63]);
                    uint16x8_t w1_61v=vdupq_n_u16((uint16_t)W1_61);
                    uint16x8_t w2_61v=vdupq_n_u16((uint16_t)W2_61);
                    uint16x8_t w1_63v=vdupq_n_u16((uint16_t)W1_63);
                    uint16x8_t w2_63v=vdupq_n_u16((uint16_t)W2_63);
                    uint16x8_t cas_v=vdupq_n_u16((uint16_t)cas_off60);
                    uint16x8_t sc62v1=vdupq_n_u16((uint16_t)sc62c1);
                    uint16x8_t sc62v2=vdupq_n_u16((uint16_t)sc62c2);

                    uint16x8_t base1[8], base2[8];
                    for(int r=0;r<8;r++){
                        base1[r]=vdupq_n_u16((uint16_t)s59a[r]);
                        base2[r]=vdupq_n_u16((uint16_t)s59b[r]);
                    }

                    /* NEON inner loop over W1[60] */
                    for(uint32_t w60b=0; w60b<(1U<<gN); w60b+=8){
                        uint16_t w60v[8];
                        for(int i=0;i<8;i++) w60v[i]=(uint16_t)((w60b+i)&gMASK);
                        uint16x8_t w1_60=vld1q_u16(w60v);
                        uint16x8_t w2_60=vandq_u16(vaddq_u16(w1_60,cas_v),mask_vec);

                        uint16x8_t s1[8],s2[8];
                        for(int r=0;r<8;r++){s1[r]=base1[r];s2[r]=base2[r];}
                        nsha_round(s1,k60v,w1_60);
                        nsha_round(s2,k60v,w2_60);

                        uint16x8_t w1_62=vandq_u16(vaddq_u16(ns1(w1_60),sc62v1),mask_vec);
                        uint16x8_t w2_62=vandq_u16(vaddq_u16(ns1(w2_60),sc62v2),mask_vec);

                        nsha_round(s1,k61v,w1_61v);
                        nsha_round(s2,k61v,w2_61v);
                        nsha_round(s1,k62v,w1_62);
                        nsha_round(s2,k62v,w2_62);
                        nsha_round(s1,k63v,w1_63v);
                        nsha_round(s2,k63v,w2_63v);

                        /* Check collision with early termination */
                        uint16x8_t match=vceqq_u16(s1[0],s2[0]);
                        if(!vmaxvq_u16(match)) continue;
                        for(int r=1;r<8;r++){
                            match=vandq_u16(match,vceqq_u16(s1[r],s2[r]));
                            if(!vmaxvq_u16(match)) goto next_w60;
                        }
                        {
                            uint16_t m[8]; vst1q_u16(m,match);
                            for(int lane=0;lane<8;lane++){
                                if(!m[lane]) continue;
                                uint32_t w60=w60b+lane;
                                /* Scalar verify */
                                uint32_t va[8],vb[8];
                                memcpy(va,state1,32);memcpy(vb,state2,32);
                                uint32_t Ws1[7]={w57,w58,w59,w60,W1_61,0,W1_63};
                                uint32_t Ws2[7]={w57b,w58b,w59b,(w60+cas_off60)&gMASK,W2_61,0,W2_63};
                                Ws1[5]=(fns1(w60)+sc62c1)&gMASK;
                                Ws2[5]=(fns1(Ws2[3])+sc62c2)&gMASK;
                                for(int rr=0;rr<7;rr++){sha_round(va,KN[57+rr],Ws1[rr]);sha_round(vb,KN[57+rr],Ws2[rr]);}
                                int ok=1;for(int rr=0;rr<8;rr++)if(va[rr]!=vb[rr]){ok=0;break;}
                                if(ok) local_coll++;
                            }
                        }
                        next_w60:;
                    }
                }
            }

            if((w57&0xF)==0xF || w57==(uint32_t)((1U<<gN)-1)){
                struct timespec t1; clock_gettime(CLOCK_MONOTONIC,&t1);
                double el=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
                double pct=100.0*(w57+1)/(1U<<gN);
                #pragma omp critical
                printf("[%.1f%%] w57=0x%x coll=%llu survive=%llu %.2fs\n",
                       pct,w57,(unsigned long long)local_coll,
                       (unsigned long long)n_w59_survive,el);
            }
        }

        n_coll_global += local_coll;
    }

    struct timespec t1; clock_gettime(CLOCK_MONOTONIC,&t1);
    double el=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
    printf("\n=== N=%d Schedule-Diff Pruned Results ===\n",gN);
    printf("Collisions: %llu\n",(unsigned long long)n_coll_global);
    printf("W1[59] survivors: %llu (of %llu tested)\n",
           (unsigned long long)n_w59_survive,
           (unsigned long long)(1ULL<<(3*gN)));
    printf("Prune ratio: %.4f%% survived\n",
           100.0*n_w59_survive/(1ULL<<(3*gN)));
    printf("Time: %.2fs\n",el);
    printf("Done.\n");
    return 0;
}
