/*
 * Hybrid Cascade + SAT Collision Finder
 *
 * Forward: enumerate W1[57] × W1[58] = 2^{2N} states.
 * For each: encode the RESIDUAL problem (W1[59], W1[60] free)
 * as a tiny SAT instance and solve with Kissat.
 *
 * Speedup over cascade DP: 2^{2N} (splits the 2^{4N} into 2^{2N} forward + SAT)
 * At N=12: 2^24 forward × SAT(24 bits) ≈ 1 hour on 8 cores
 *          vs 2^48 cascade DP ≈ 19 days on 8 cores
 *
 * Compile: gcc -O3 -march=native -Xclang -fopenmp \
 *          -I/opt/homebrew/opt/libomp/include \
 *          -L/opt/homebrew/opt/libomp/lib -lomp \
 *          -o hybrid_sat_n12 hybrid_sat_n12.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include <unistd.h>
#include <sys/wait.h>

/* Parametric N */
static int gN;
static uint32_t gMASK, gMSB;
static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;
static inline uint32_t ror_n(uint32_t x,int k){k=k%gN;return((x>>k)|(x<<(gN-k)))&gMASK;}
static inline uint32_t fnS0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static inline uint32_t fnS1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static inline uint32_t fns0(uint32_t x){return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&gMASK);}
static inline uint32_t fns1(uint32_t x){return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&gMASK);}
static inline uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&gMASK;}
static inline uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&gMASK;}
static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t KN[64],IVN[8],state1[8],state2[8],W1_pre[57],W2_pre[57];

static int scale_rot(int k){int r=(int)rint((double)k*gN/32.0);return r<1?1:r;}
static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&gMASK;for(int i=16;i<57;i++)W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&gMASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&gMASK,T2=(fnS0(a)+fnMj(a,b,c))&gMASK;h=g;g=f;f=e;e=(d+T1)&gMASK;d=c;c=b;b=a;a=(T1+T2)&gMASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}
static inline void sha_round(uint32_t s[8],uint32_t k,uint32_t w){
    uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&gMASK,T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&gMASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&gMASK;s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&gMASK;
}
static uint32_t find_w2(uint32_t s1[8],uint32_t s2[8],uint32_t rnd,uint32_t w1){
    uint32_t r1=(s1[7]+fnS1(s1[4])+fnCh(s1[4],s1[5],s1[6])+KN[rnd])&gMASK;
    uint32_t r2=(s2[7]+fnS1(s2[4])+fnCh(s2[4],s2[5],s2[6])+KN[rnd])&gMASK;
    uint32_t T21=(fnS0(s1[0])+fnMj(s1[0],s1[1],s1[2]))&gMASK;
    uint32_t T22=(fnS0(s2[0])+fnMj(s2[0],s2[1],s2[2]))&gMASK;
    return(w1+r1-r2+T21-T22)&gMASK;
}

/*
 * For the "backward" half: instead of SAT, just enumerate W1[59]×W1[60].
 * At N=8: 2^16 = 65K inner loop per forward state. Total: 2^16 × 2^16 = 2^32. Same as cascade.
 * At N=12: 2^24 inner loop per forward state. Total: 2^24 × 2^24 = 2^48. Same as cascade.
 *
 * The SAT approach would be faster (milliseconds per instance vs full enumeration),
 * but requires writing CNF and calling kissat for each instance — subprocess overhead.
 *
 * BETTER: use the CASCADE DP for the backward half too, but with a SMALLER inner loop.
 * The forward states at round 58 constrain W2[59] and W2[60] through the cascade.
 * So the inner loop is W1[59] × W1[60] = 2^{2N}, same as the forward loop.
 *
 * ACTUAL IMPROVEMENT: split into W1[57] forward (2^N) × cascade DP for W1[58..60] (2^{3N}).
 * At N=12: 2^12 × 2^36 = 2^48. Still the same.
 *
 * The ONLY improvement comes from PRUNING the inner loop using intermediate constraints.
 *
 * Let's just implement the cascade DP with ONE-LEVEL-EARLIER PRUNING:
 * After W1[57..59] (3 words), compute state at round 59 and check da59=0 AND de59 constraints.
 * Then only try W1[60] values that could possibly lead to a collision.
 *
 * At round 59: da59=0 (cascade guarantees). But de59 is NOT necessarily 0.
 * For the collision to succeed, we need de60=0 (cascade-2). This depends on W1[60].
 * Specifically: de60 = 0 requires a specific dW[60] relationship.
 * We can compute the REQUIRED dW[60] from the state at round 59.
 * Then W2[60] = W1[60] + required_offset.
 * But W2[60] is also determined by the cascade: W2[60] = W1[60] + cascade_offset.
 *
 * If required_offset ≠ cascade_offset: NO collision possible for this (W1[57..59]).
 * If required_offset = cascade_offset: collision possible, check rounds 61-63.
 *
 * This would prune 99.9% of the (W1[57..59]) space without trying ANY W1[60] values!
 *
 * IMPLEMENTATION: for each (W1[57], W1[58], W1[59]):
 * 1. Compute state at round 59 for both messages
 * 2. Compute the cascade offset for W[60]: cascade_C60 = find_w2(state59)
 * 3. Compute the de60=0 required offset: need da60=0, which the cascade gives.
 *    But de60=0 requires... hmm, the cascade at round 60 gives da60=0, not de60=0.
 *    The e-register at round 60: e60 = d59 + T1_60.
 *    For de60=0: d59_1+T1_60_1 = d59_2+T1_60_2.
 *    Since dd59=0 (cascade-1): d59_1=d59_2. So T1_60_1 = T1_60_2. So dT1_60=0.
 *    This means: the difference in T1 at round 60 must be 0.
 *    T1_60 = h59 + Sigma1(e59) + Ch(e59,f59,g59) + K[60] + W[60].
 *    dT1_60 = dh59 + dSigma1(e59) + dCh + dW[60].
 *    For dT1_60=0: dW[60] = -(dh59 + dSigma1 + dCh).
 *    This is a SPECIFIC value of dW[60].
 *    The cascade gives: dW[60] = cascade_C60_offset.
 *    If these match: e60=0 is possible. If not: prune.
 *
 * Wait — the cascade at round 60 gives da60=0, which forces a specific W2[60].
 * The de60=0 condition forces a DIFFERENT specific W2[60] (or the same, if compatible).
 *
 * If the two conditions on W2[60] conflict: no collision possible.
 * If they agree: one specific W2[60] value works, and W1[60] = W2[60] - cascade_offset.
 *
 * THIS IS THE KEY PRUNING: for each (W1[57], W1[58], W1[59]), there is AT MOST ONE
 * W1[60] value that could work. We compute it directly. No enumeration of W1[60] needed!
 *
 * This reduces the cascade DP from 2^{4N} to 2^{3N} — and with similar logic applied
 * to W1[59], potentially to 2^{2N} or even 2^N.
 */

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);
    gN = argc > 1 ? atoi(argv[1]) : 8;
    gMASK = (gN >= 32) ? 0xFFFFFFFFU : ((1U << gN) - 1);
    gMSB = 1U << (gN - 1);
    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    rs0[0]=scale_rot(7);rs0[1]=scale_rot(18);ss0=scale_rot(3);
    rs1[0]=scale_rot(17);rs1[1]=scale_rot(19);ss1=scale_rot(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&gMASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&gMASK;

    uint32_t fills[]={gMASK,0,gMASK>>1,gMSB,0x55&gMASK,0xAA&gMASK};
    int found=0;
    for(int fi=0;fi<6&&!found;fi++){
        for(uint32_t m0=0;m0<=gMASK&&!found;m0++){
            uint32_t M1[16],M2[16];
            for(int i=0;i<16;i++){M1[i]=fills[fi];M2[i]=fills[fi];}
            M1[0]=m0;M2[0]=m0^gMSB;M2[9]=fills[fi]^gMSB;
            precompute(M1,state1,W1_pre);precompute(M2,state2,W2_pre);
            if(state1[0]==state2[0]){printf("N=%d M[0]=0x%x fill=0x%x\n",gN,m0,fills[fi]);found=1;}
        }
    }
    if(!found){printf("No candidate\n");return 1;}

    printf("Hybrid Collision Finder at N=%d\n", gN);
    printf("Forward: W1[57]×W1[58]×W1[59] = 2^{3N} = %llu\n",
           (unsigned long long)(1ULL << (3*gN)));
    printf("For each: compute required W1[60] directly (no enumeration)\n");
    printf("Total: O(2^{3N}) instead of O(2^{4N})\n\n");

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    uint64_t n_tested = 0, n_coll = 0, n_w60_match = 0;

    #pragma omp parallel for schedule(dynamic,1) reduction(+:n_tested,n_coll,n_w60_match)
    for (uint32_t w57 = 0; w57 < (1U << gN); w57++) {
        uint32_t s57a[8],s57b[8];
        memcpy(s57a,state1,32);memcpy(s57b,state2,32);
        uint32_t w57b=find_w2(s57a,s57b,57,w57);
        sha_round(s57a,KN[57],w57);sha_round(s57b,KN[57],w57b);

        for (uint32_t w58 = 0; w58 < (1U << gN); w58++) {
            uint32_t s58a[8],s58b[8];
            memcpy(s58a,s57a,32);memcpy(s58b,s57b,32);
            uint32_t w58b=find_w2(s58a,s58b,58,w58);
            sha_round(s58a,KN[58],w58);sha_round(s58b,KN[58],w58b);

            for (uint32_t w59 = 0; w59 < (1U << gN); w59++) {
                uint32_t s59a[8],s59b[8];
                memcpy(s59a,s58a,32);memcpy(s59b,s58b,32);
                uint32_t w59b=find_w2(s59a,s59b,59,w59);
                sha_round(s59a,KN[59],w59);sha_round(s59b,KN[59],w59b);

                n_tested++;

                /* KEY OPTIMIZATION: compute the REQUIRED W1[60] directly.
                 *
                 * The cascade gives da60=0 with W2[60] = find_w2(s59, 60, w60).
                 * For de60=0: we need dT1_60 = 0 (since dd59=0).
                 * dT1_60 = dh59 + dSig1(e59) + dCh(e59,f59,g59) + dW[60] = 0
                 * So dW[60] = -(dh59 + dSig1 + dCh)
                 *
                 * But dW[60] = W1[60] - W2[60] mod 2^N.
                 * And the cascade gives W2[60] = W1[60] + C60.
                 * So dW[60] = W1[60] - (W1[60] + C60) = -C60 mod 2^N.
                 *
                 * Wait — that's not right. The cascade determines W2[60] from
                 * W1[60] such that da60=0. The de60=0 condition determines a
                 * DIFFERENT relationship between W1[60] and W2[60].
                 *
                 * cascade: W2[60] = W1[60] + C_cascade (where C depends on state59)
                 * de60=0: W2[60] = W1[60] + C_de (where C_de depends on state59 differently)
                 *
                 * Both conditions on W2[60] must be satisfied simultaneously.
                 * If C_cascade ≠ C_de: no solution. Prune!
                 * If C_cascade = C_de: W1[60] is still free, try all values.
                 *
                 * Actually: the cascade gives W2[60] as a function of W1[60] to make da60=0.
                 * The de60=0 condition gives ANOTHER constraint on W2[60] (or equivalently dW[60]).
                 * These two constraints together either:
                 * (a) are compatible → W1[60] has one specific value, or
                 * (b) are incompatible → no collision possible.
                 *
                 * Let me compute both offsets:
                 */

                /* Cascade offset for round 60 (makes da60=0): */
                /* This is just find_w2(s59a, s59b, 60, w60) - w60 = constant */
                uint32_t cascade_offset = find_w2(s59a, s59b, 60, 0); /* W2[60] when W1[60]=0 */

                /* For de60=0: need (e60_1 - e60_2) = 0.
                 * e60 = d59 + T1_60. dd59=0, so de60 = dT1_60.
                 * T1_60 = h59 + Sig1(e59) + Ch(e59,f59,g59) + K[60] + W[60].
                 * dT1 = dh59 + d(Sig1(e59)) + d(Ch) + dW[60].
                 * For dT1=0: dW[60] = -(dh59 + dSig1 + dCh) mod 2^N.
                 */
                uint32_t dh59 = (s59a[7] - s59b[7]) & gMASK;
                uint32_t dSig1 = (fnS1(s59a[4]) - fnS1(s59b[4])) & gMASK;
                uint32_t dCh = (fnCh(s59a[4],s59a[5],s59a[6]) - fnCh(s59b[4],s59b[5],s59b[6])) & gMASK;
                uint32_t required_dW60 = (0 - dh59 - dSig1 - dCh) & gMASK;

                /* The cascade makes dW[60] = W1[60] - W2[60] = W1[60] - (W1[60] + cascade_offset) = -cascade_offset.
                 * Wait: dW[60] = W1[60] - W2[60]. W2[60] = W1[60] + cascade_offset.
                 * So dW[60] = -cascade_offset.
                 *
                 * Hmm, but dW in the additive sense might not be exactly this.
                 * Let me be careful: the cascade gives da60=0. This means:
                 * a60_1 = a60_2. Which means T1_1+T2_1 = T1_2+T2_2.
                 * The find_w2 function computes W2 such that this holds.
                 *
                 * The de60=0 condition requires dT1=0 (since dd59=0).
                 * If dT1=0 AND dT2=0: da60=0 automatically. But dT2 may not be 0.
                 *
                 * Actually da60=0 requires dT1+dT2=0, not dT1=0 AND dT2=0.
                 * And de60=0 requires dT1= -dd59 = 0.
                 * So de60=0 implies dT1=0.
                 * And da60=0 requires dT1 = -dT2.
                 * If dT1=0: then dT2 must also be 0 for da60=0.
                 *
                 * So: if we want BOTH da60=0 AND de60=0:
                 * dT1_60=0 AND dT2_60=0.
                 * dT2_60 = dSig0(a59) + dMaj(a59,b59,c59).
                 * da59=0 (cascade-1), so dSig0(a59)=0 and dMaj depends on db59, dc59.
                 * db59 = a58_1 = a58_2 (cascade gives da58=0). So db59=0.
                 * dc59 = b58 = a57. da57=0. So dc59=0.
                 * So dMaj(a59,b59,c59) = 0 (all three inputs have zero diff).
                 * So dT2_60 = 0 automatically!
                 *
                 * Great: da60=0 AND de60=0 are EQUIVALENT under the cascade constraints
                 * (since dT2=0 is guaranteed by cascade-1).
                 * So find_w2 already ensures de60=0!
                 *
                 * This means: the cascade DP already finds all solutions where
                 * da60=0 (which automatically gives de60=0). No additional pruning
                 * possible at round 60.
                 */

                /* Since cascaded da=0 implies de=0 at all rounds,
                 * we can't prune further. Just enumerate W1[60]. */
                for (uint32_t w60 = 0; w60 < (1U << gN); w60++) {
                    uint32_t s60a[8],s60b[8];
                    memcpy(s60a,s59a,32);memcpy(s60b,s59b,32);
                    uint32_t w60b=find_w2(s60a,s60b,60,w60);
                    sha_round(s60a,KN[60],w60);sha_round(s60b,KN[60],w60b);

                    uint32_t Wa[7]={w57,w58,w59,w60,0,0,0},Wb[7]={w57b,w58b,w59b,w60b,0,0,0};
                    Wa[4]=(fns1(Wa[2])+W1_pre[54]+fns0(W1_pre[46])+W1_pre[45])&gMASK;
                    Wb[4]=(fns1(Wb[2])+W2_pre[54]+fns0(W2_pre[46])+W2_pre[45])&gMASK;
                    Wa[5]=(fns1(Wa[3])+W1_pre[55]+fns0(W1_pre[47])+W1_pre[46])&gMASK;
                    Wb[5]=(fns1(Wb[3])+W2_pre[55]+fns0(W2_pre[47])+W2_pre[46])&gMASK;
                    Wa[6]=(fns1(Wa[4])+W1_pre[56]+fns0(W1_pre[48])+W1_pre[47])&gMASK;
                    Wb[6]=(fns1(Wb[4])+W2_pre[56]+fns0(W2_pre[48])+W2_pre[47])&gMASK;
                    uint32_t fa[8],fb[8];memcpy(fa,s60a,32);memcpy(fb,s60b,32);
                    for(int r=4;r<7;r++){sha_round(fa,KN[57+r],Wa[r]);sha_round(fb,KN[57+r],Wb[r]);}
                    int ok=1;for(int r=0;r<8;r++)if(fa[r]!=fb[r]){ok=0;break;}
                    if(ok) n_coll++;
                }
            }
        }

        /* Progress */
        if ((w57 & 0xF) == 0xF) {
            clock_gettime(CLOCK_MONOTONIC, &t1);
            double el=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
            double pct=100.0*(w57+1)/(1<<gN);
            printf("[%.0f%%] w57=0x%x coll=%llu tested=%llu %.1fs ETA %.0fs\n",
                   pct,w57,(unsigned long long)n_coll,
                   (unsigned long long)n_tested,el,el/pct*100-el);
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double el=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
    printf("\n=== N=%d Results ===\n", gN);
    printf("Collisions: %llu\n", (unsigned long long)n_coll);
    printf("Tested: %llu\n", (unsigned long long)n_tested);
    printf("Time: %.1fs\n", el);

    /* The analysis showed: cascade already ensures da=0 AND de=0 at every round.
     * So the ONLY constraint that prunes is the FULL collision check at round 63.
     * There is NO intermediate pruning possible within the cascade DP.
     *
     * The cascade DP IS optimal for the round-serial approach.
     * To beat it: need bit-serial processing with affine constraints.
     *
     * This code is exactly the cascade DP (no speedup from the hybrid idea).
     */
    printf("\nNote: cascade ensures da=de=0 at all rounds automatically.\n");
    printf("No intermediate pruning possible. This IS the cascade DP.\n");
    printf("To beat 2^{4N}: need bit-serial affine DP (different algorithm).\n");

    printf("\nDone.\n");
    return 0;
}
