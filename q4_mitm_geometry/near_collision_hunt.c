/* Hunt for prefixes giving the BEST near-collision (lowest HW) among
 * round-61-viable prefixes.
 *
 * For each random prefix:
 *   1. Check round-61 closure (fast: just count matches)
 *   2. If viable: compute full hash for EACH of 8192 valid W[60]
 *   3. Report the minimum HW across all valid W[60]
 *
 * Strategy: scan many prefixes, report those with HW < threshold.
 *
 * The cert has HW=0 (perfect collision). Our best random is HW=40.
 * If we find HW < 20, it might be encodable as a tiny SAT problem.
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
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

static void sha256_compress_override(const uint32_t M[16],uint32_t hash[8],
    uint32_t w57,uint32_t w58,uint32_t w59,uint32_t w60){
    uint32_t W[64];
    for(int i=0;i<16;i++)W[i]=M[i];
    for(int i=16;i<64;i++)W[i]=sigma1(W[i-2])+W[i-7]+sigma0(W[i-15])+W[i-16];
    W[57]=w57;W[58]=w58;W[59]=w59;W[60]=w60;
    for(int i=61;i<64;i++)W[i]=sigma1(W[i-2])+W[i-7]+sigma0(W[i-15])+W[i-16];
    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for(int i=0;i<64;i++){uint32_t T1=h+Sigma1(e)+Ch(e,f,g)+K[i]+W[i];uint32_t T2=Sigma0(a)+Maj(a,b,c);h=g;g=f;f=e;e=d+T1;d=c;c=b;b=a;a=T1+T2;}
    hash[0]=IV[0]+a;hash[1]=IV[1]+b;hash[2]=IV[2]+c;hash[3]=IV[3]+d;
    hash[4]=IV[4]+e;hash[5]=IV[5]+f;hash[6]=IV[6]+g;hash[7]=IV[7]+h;
}
static uint32_t cascade_dw(const uint32_t s1[8],const uint32_t s2[8]){return s1[7]-s2[7]+Sigma1(s1[4])-Sigma1(s2[4])+Ch(s1[4],s1[5],s1[6])-Ch(s2[4],s2[5],s2[6])+Sigma0(s1[0])+Maj(s1[0],s1[1],s1[2])-Sigma0(s2[0])-Maj(s2[0],s2[1],s2[2]);}
static void one_round(uint32_t out[8],const uint32_t in[8],uint32_t w,int r){uint32_t T1=in[7]+Sigma1(in[4])+Ch(in[4],in[5],in[6])+K[r]+w;uint32_t T2=Sigma0(in[0])+Maj(in[0],in[1],in[2]);out[0]=T1+T2;out[1]=in[0];out[2]=in[1];out[3]=in[2];out[4]=in[3]+T1;out[5]=in[4];out[6]=in[5];out[7]=in[6];}
static void compute_state57(const uint32_t M[16],uint32_t state[8],uint32_t W[64]){
    for(int i=0;i<16;i++)W[i]=M[i];for(int i=16;i<64;i++)W[i]=sigma1(W[i-2])+W[i-7]+sigma0(W[i-15])+W[i-16];
    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for(int i=0;i<57;i++){uint32_t T1=h+Sigma1(e)+Ch(e,f,g)+K[i]+W[i];uint32_t T2=Sigma0(a)+Maj(a,b,c);h=g;g=f;f=e;e=d+T1;d=c;c=b;b=a;a=T1+T2;}
    state[0]=a;state[1]=b;state[2]=c;state[3]=d;state[4]=e;state[5]=f;state[6]=g;state[7]=h;
}
static uint64_t xs(uint64_t *s){*s^=*s<<13;*s^=*s>>7;*s^=*s<<17;return *s;}

int main(int argc, char **argv){
    int n_prefixes = argc>1 ? atoi(argv[1]) : 4096;
    uint64_t seed_base = argc>2 ? strtoull(argv[2],NULL,0) : 0xdead;

    uint32_t M1[16]={0x17149975,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff,0xffffffff};
    uint32_t M2[16]; memcpy(M2,M1,sizeof(M2)); M2[0]^=0x80000000; M2[9]^=0x80000000;
    uint32_t s1[8],s2[8],W1[64],W2[64]; compute_state57(M1,s1,W1); compute_state57(M2,s2,W2);
    uint32_t C57=cascade_dw(s1,s2);
    uint32_t sched1_61=W1[54]+sigma0(W1[46])+W1[45];
    uint32_t sched2_61=W2[54]+sigma0(W2[46])+W2[45];

    fprintf(stderr,"Scanning %d prefixes (seed=0x%lx)\n",n_prefixes,(long)seed_base);
    fprintf(stderr,"Reporting any with HW < 40 (cert has HW=0)\n\n");

    uint64_t rng=seed_base;
    int global_best_hw=256;
    time_t t0=time(NULL);
    int n_viable=0;

    for(int p=0;p<n_prefixes;p++){
        uint32_t w57=(uint32_t)xs(&rng), w58=(uint32_t)xs(&rng), w59=(uint32_t)xs(&rng);
        /* Quick round-61 check: just count matches */
        uint32_t sa[8],sb[8]; one_round(sa,s1,w57,57); one_round(sb,s2,w57+C57,57);
        uint32_t C58=cascade_dw(sa,sb);
        uint32_t sc[8],sd[8]; one_round(sc,sa,w58,58); one_round(sd,sb,w58+C58,58);
        uint32_t C59=cascade_dw(sc,sd);
        uint32_t se[8],sf[8]; one_round(se,sc,w59,59); one_round(sf,sd,w59+C59,59);
        uint32_t C60=cascade_dw(se,sf);
        uint32_t target=sigma1(w59+C59)-sigma1(w59)+sched2_61-sched1_61;

        /* Find matching W[60] and compute full hash */
        int best_hw=256;
        uint32_t best_w60=0;
        int found_any=0;
        #pragma omp parallel for schedule(static) reduction(min:best_hw)
        for(long w_l=0;w_l<(1L<<32);w_l++){
            uint32_t w60=(uint32_t)w_l;
            uint32_t sg2[8],sh2[8];
            one_round(sg2,se,w60,60);
            one_round(sh2,sf,w60+C60,60);
            if(cascade_dw(sg2,sh2)!=target) continue;
            /* Round-61 match! Compute full hash */
            uint32_t h1[8],h2[8];
            sha256_compress_override(M1,h1,w57,w58,w59,w60);
            sha256_compress_override(M2,h2,w57+C57,w58+C58,w59+C59,w60+C60);
            int hw=0;
            for(int i=0;i<8;i++) hw+=__builtin_popcount(h1[i]^h2[i]);
            if(hw<best_hw){
                best_hw=hw;
                #pragma omp critical
                { best_w60=w60; }
            }
        }

        if(best_hw<256){
            found_any=1;
            n_viable++;
            if(best_hw<global_best_hw) global_best_hw=best_hw;
            if(best_hw<40){
                fprintf(stderr,"[%4d] *** HW=%d *** W=0x%08x,0x%08x,0x%08x w60=0x%08x [%lds]\n",
                    p,best_hw,w57,w58,w59,best_w60,(long)(time(NULL)-t0));
                if(best_hw==0){
                    fprintf(stderr,"  !!! COLLISION FOUND !!!\n");
                }
            }
        }
        if(p%8==0){
            fprintf(stderr,"[%4d] scanned, viable=%d, best_hw=%d [%lds]\n",
                p,n_viable,global_best_hw,(long)(time(NULL)-t0));
        }
    }
    fprintf(stderr,"\n=== Summary ===\n");
    fprintf(stderr,"Scanned: %d, Viable: %d (%.3f%%), Best HW: %d\n",
        n_prefixes,n_viable,100.0*n_viable/n_prefixes,global_best_hw);
    return 0;
}
