/*
 * Script 81: Multi-Kernel Sweep
 *
 * Tests all 32 single-bit kernel positions (not just MSB).
 * For each kernel bit k: M2[0] = M1[0] ^ (1<<k), M2[9] = M1[9] ^ (1<<k)
 *
 * For each kernel, scan M[0] over 2^32 to find da[56]=0 candidates,
 * then run quick SA to measure thermodynamic floor.
 *
 * Compile: gcc -O3 -march=native -Xclang -fopenmp \
 *   -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp \
 *   -o kernel_sweep 81_kernel_sweep.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

#ifdef _OPENMP
#include <omp.h>
#endif

#define MASK 0xFFFFFFFFU

static inline uint32_t ror(uint32_t x, int n) { return (x>>n)|(x<<(32-n)); }
static inline uint32_t Ch(uint32_t e, uint32_t f, uint32_t g) { return (e&f)^(~e&g); }
static inline uint32_t Maj(uint32_t a, uint32_t b, uint32_t c) { return (a&b)^(a&c)^(b&c); }
static inline uint32_t S0(uint32_t a) { return ror(a,2)^ror(a,13)^ror(a,22); }
static inline uint32_t S1(uint32_t e) { return ror(e,6)^ror(e,11)^ror(e,25); }
static inline uint32_t s0(uint32_t x) { return ror(x,7)^ror(x,18)^(x>>3); }
static inline uint32_t s1(uint32_t x) { return ror(x,17)^ror(x,19)^(x>>10); }
static inline int hw32(uint32_t x) { return __builtin_popcount(x); }

static const uint32_t K[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};
static const uint32_t IV[8] = {
    0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
    0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
};

typedef struct { uint32_t state[8]; uint32_t W_pre[57]; } precomp_t;

static void precompute(const uint32_t M[16], precomp_t *out) {
    for (int i=0;i<16;i++) out->W_pre[i]=M[i];
    for (int i=16;i<57;i++)
        out->W_pre[i]=s1(out->W_pre[i-2])+out->W_pre[i-7]+s0(out->W_pre[i-15])+out->W_pre[i-16];
    uint32_t a=IV[0],b=IV[1],c=IV[2],d=IV[3],e=IV[4],f=IV[5],g=IV[6],h=IV[7];
    for (int i=0;i<57;i++){
        uint32_t T1=h+S1(e)+Ch(e,f,g)+K[i]+out->W_pre[i];
        uint32_t T2=S0(a)+Maj(a,b,c);
        h=g;g=f;f=e;e=d+T1;d=c;c=b;b=a;a=T1+T2;
    }
    out->state[0]=a;out->state[1]=b;out->state[2]=c;out->state[3]=d;
    out->state[4]=e;out->state[5]=f;out->state[6]=g;out->state[7]=h;
}

static int eval_hw63(const precomp_t *p1, const precomp_t *p2,
                     const uint32_t w1[4], const uint32_t w2[4]) {
    uint32_t W1[7], W2[7];
    for (int i=0;i<4;i++){W1[i]=w1[i];W2[i]=w2[i];}
    W1[4]=s1(W1[2])+p1->W_pre[54]+s0(p1->W_pre[46])+p1->W_pre[45];
    W2[4]=s1(W2[2])+p2->W_pre[54]+s0(p2->W_pre[46])+p2->W_pre[45];
    W1[5]=s1(W1[3])+p1->W_pre[55]+s0(p1->W_pre[47])+p1->W_pre[46];
    W2[5]=s1(W2[3])+p2->W_pre[55]+s0(p2->W_pre[47])+p2->W_pre[46];
    W1[6]=s1(W1[4])+p1->W_pre[56]+s0(p1->W_pre[48])+p1->W_pre[47];
    W2[6]=s1(W2[4])+p2->W_pre[56]+s0(p2->W_pre[48])+p2->W_pre[47];

    uint32_t a1=p1->state[0],b1=p1->state[1],c1=p1->state[2],d1=p1->state[3];
    uint32_t e1=p1->state[4],f1=p1->state[5],g1=p1->state[6],h1=p1->state[7];
    uint32_t a2=p2->state[0],b2=p2->state[1],c2=p2->state[2],d2=p2->state[3];
    uint32_t e2=p2->state[4],f2=p2->state[5],g2=p2->state[6],h2=p2->state[7];
    for (int i=0;i<7;i++){
        uint32_t T1a=h1+S1(e1)+Ch(e1,f1,g1)+K[57+i]+W1[i];
        uint32_t T2a=S0(a1)+Maj(a1,b1,c1);
        h1=g1;g1=f1;f1=e1;e1=d1+T1a;d1=c1;c1=b1;b1=a1;a1=T1a+T2a;
        uint32_t T1b=h2+S1(e2)+Ch(e2,f2,g2)+K[57+i]+W2[i];
        uint32_t T2b=S0(a2)+Maj(a2,b2,c2);
        h2=g2;g2=f2;f2=e2;e2=d2+T1b;d2=c2;c2=b2;b2=a2;a2=T1b+T2b;
    }
    return hw32(a1^a2)+hw32(b1^b2)+hw32(c1^c2)+hw32(d1^d2)+hw32(e1^e2)+hw32(f1^f2)+hw32(g1^g2)+hw32(h1^h2);
}

typedef struct { uint32_t s[4]; } rng_t;
static inline uint32_t rng_rotl(uint32_t x,int k){return(x<<k)|(x>>(32-k));}
static inline uint32_t rng_next(rng_t *r){
    uint32_t result=rng_rotl(r->s[1]*5,7)*9;
    uint32_t t=r->s[1]<<9;
    r->s[2]^=r->s[0];r->s[3]^=r->s[1];r->s[1]^=r->s[2];r->s[0]^=r->s[3];
    r->s[2]^=t;r->s[3]=rng_rotl(r->s[3],11);
    return result;
}
static void rng_seed(rng_t *r,uint64_t seed){
    r->s[0]=(uint32_t)seed;r->s[1]=(uint32_t)(seed>>32);
    r->s[2]=r->s[0]^0x9e3779b9;r->s[3]=r->s[1]^0x6a09e667;
    for(int i=0;i<8;i++)rng_next(r);
}

/* Quick SA: returns best HW found */
static int quick_sa(const precomp_t *p1, const precomp_t *p2,
                    int n_restarts, int steps, uint64_t seed_base) {
    int best = 256;
    #pragma omp parallel
    {
        int tid=0;
        #ifdef _OPENMP
        tid=omp_get_thread_num();
        #endif
        rng_t rng;
        rng_seed(&rng, seed_base ^ ((uint64_t)tid<<32));
        int local_best = 256;

        #pragma omp for schedule(dynamic,1)
        for (int r=0; r<n_restarts; r++) {
            uint32_t w1[4],w2[4];
            for(int i=0;i<4;i++){w1[i]=rng_next(&rng);w2[i]=rng_next(&rng);}
            int cur=eval_hw63(p1,p2,w1,w2);
            double T=20.0, cool=pow(0.001/20.0,1.0/steps);
            for(int s=0;s<steps;s++){
                uint32_t tw1[4],tw2[4];
                memcpy(tw1,w1,16);memcpy(tw2,w2,16);
                int nf=1+(rng_next(&rng)%3);
                for(int f=0;f<nf;f++){
                    uint32_t rv=rng_next(&rng);
                    int wi=rv&3,bit=(rv>>2)&31;
                    if((rv>>7)&1)tw1[wi]^=(1U<<bit); else tw2[wi]^=(1U<<bit);
                }
                int nh=eval_hw63(p1,p2,tw1,tw2);
                int d=nh-cur;
                if(d<=0||((double)rng_next(&rng)/4294967296.0)<exp(-d/T)){
                    memcpy(w1,tw1,16);memcpy(w2,tw2,16);cur=nh;
                }
                T*=cool;
                if(cur==0)continue;
            }
            if(cur<local_best)local_best=cur;
            if(cur==0)continue;
        }
        #pragma omp critical
        { if(local_best<best) best=local_best; }
    }
    return best;
}

int main(int argc, char *argv[]) {
    setbuf(stdout, NULL);

    uint32_t fill = 0xffffffff;
    int sa_restarts = 500;
    int sa_steps = 100000;
    int partial_scan = 0; /* 0 = full 2^32, else limit */

    if (argc > 1) fill = (uint32_t)strtoul(argv[1], NULL, 0);
    if (argc > 2) sa_restarts = atoi(argv[2]);
    if (argc > 3) sa_steps = atoi(argv[3]);
    if (argc > 4) partial_scan = atoi(argv[4]);

    printf("Multi-Kernel Sweep\n");
    printf("  Fill: 0x%08x, SA: %d restarts x %d steps\n", fill, sa_restarts, sa_steps);
    printf("  Scan range: %s\n\n", partial_scan ? "partial" : "full 2^32");
    printf("%-5s %8s %6s %8s %8s\n", "Bit", "M[0]", "hw56", "SA_best", "Rating");
    printf("----------------------------------------------\n");

    for (int kernel_bit = 31; kernel_bit >= 0; kernel_bit--) {
        uint32_t kernel_mask = 1U << kernel_bit;

        /* Scan for da[56]=0 candidate with this kernel */
        uint32_t best_m0 = 0;
        int best_hw56 = 999;
        int found = 0;

        uint64_t scan_limit = partial_scan ? (uint64_t)partial_scan : 0x100000000ULL;

        #pragma omp parallel
        {
            uint32_t M1[16], M2[16], s1l[8], s2l[8];
            for(int i=0;i<16;i++) M1[i]=fill;
            memcpy(M2,M1,sizeof(M1));

            #pragma omp for schedule(dynamic, 4096)
            for (uint64_t m0 = 0; m0 < scan_limit; m0++) {
                if (found) continue;
                M1[0] = (uint32_t)m0;
                M2[0] = M1[0] ^ kernel_mask;
                M2[9] = fill ^ kernel_mask;

                /* Inline 57-round compression */
                uint32_t W1[57], W2[57];
                for(int i=0;i<16;i++){W1[i]=M1[i];W2[i]=M2[i];}
                for(int i=16;i<57;i++){
                    W1[i]=s1(W1[i-2])+W1[i-7]+s0(W1[i-15])+W1[i-16];
                    W2[i]=s1(W2[i-2])+W2[i-7]+s0(W2[i-15])+W2[i-16];
                }
                uint32_t a1=IV[0],b1=IV[1],c1=IV[2],d1=IV[3],e1=IV[4],f1=IV[5],g1=IV[6],h1=IV[7];
                uint32_t a2=IV[0],b2=IV[1],c2=IV[2],d2=IV[3],e2=IV[4],f2=IV[5],g2=IV[6],h2=IV[7];
                for(int i=0;i<57;i++){
                    uint32_t T1a=h1+S1(e1)+Ch(e1,f1,g1)+K[i]+W1[i];
                    uint32_t T2a=S0(a1)+Maj(a1,b1,c1);
                    h1=g1;g1=f1;f1=e1;e1=d1+T1a;d1=c1;c1=b1;b1=a1;a1=T1a+T2a;
                    uint32_t T1b=h2+S1(e2)+Ch(e2,f2,g2)+K[i]+W2[i];
                    uint32_t T2b=S0(a2)+Maj(a2,b2,c2);
                    h2=g2;g2=f2;f2=e2;e2=d2+T1b;d2=c2;c2=b2;b2=a2;a2=T1b+T2b;
                }

                if (a1 == a2) {
                    s1l[0]=a1;s1l[1]=b1;s1l[2]=c1;s1l[3]=d1;s1l[4]=e1;s1l[5]=f1;s1l[6]=g1;s1l[7]=h1;
                    s2l[0]=a2;s2l[1]=b2;s2l[2]=c2;s2l[3]=d2;s2l[4]=e2;s2l[5]=f2;s2l[6]=g2;s2l[7]=h2;
                    int hw56=0;
                    for(int r=0;r<8;r++) hw56+=hw32(s1l[r]^s2l[r]);

                    #pragma omp critical
                    {
                        if (!found || hw56 < best_hw56) {
                            found = 1;
                            best_m0 = (uint32_t)m0;
                            best_hw56 = hw56;
                        }
                    }
                }
            }
        }

        if (!found) {
            printf("bit%02d %8s %6s %8s  no candidate\n", kernel_bit, "-", "-", "-");
            continue;
        }

        /* Run quick SA on this candidate */
        uint32_t M1[16], M2[16];
        for(int i=0;i<16;i++){M1[i]=fill;M2[i]=fill;}
        M1[0]=best_m0; M2[0]=best_m0^kernel_mask; M2[9]=fill^kernel_mask;

        precomp_t p1, p2;
        precompute(M1, &p1);
        precompute(M2, &p2);

        int sa_best = quick_sa(&p1, &p2, sa_restarts, sa_steps, time(NULL) ^ kernel_bit);

        const char *rating = "";
        if (sa_best < 50) rating = "*** PROMISING ***";
        else if (sa_best < 70) rating = "* interesting *";

        printf("bit%02d 0x%08x  %4d     %4d  %s\n", kernel_bit, best_m0, best_hw56, sa_best, rating);
    }

    return 0;
}
