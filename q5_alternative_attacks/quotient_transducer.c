/*
 * quotient_transducer.c — Quotient-State Collision Finder for N=8 mini-SHA
 *
 * Based on the PROVEN FACE architecture (face_n8.c verified at 260 collisions).
 * Adds quotient-state deduplication within the pool during symbolic processing.
 *
 * The p_add, p_ch, p_maj operations process bits 0→7. After processing the
 * first CHUNK=4 bits of each operation, we merge pool states with identical
 * quotient keys: (carry state, register affine forms, GF2 RREF).
 *
 * This implements the Myhill-Nerode quotient: two prefixes (mode-branching
 * paths through bits 0-3) that produce the same state at the chunk boundary
 * will behave identically for bits 4-7. So they are merged.
 *
 * Outer: concrete W1[57] x W1[58] (2^16)
 * Inner: symbolic R59 (both msgs) with pool-level chunk-boundary dedup
 * Then:  concrete W1[60] loop with de61=0 + Three-Filter collision check
 *
 * N=8, MSB kernel, M[0]=0x67, fill=0xff.
 * Expected: 260 collisions.
 *
 * Compile: gcc -O3 -march=native -o quotient_transducer quotient_transducer.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N 8
#define MASK ((1U<<N)-1)
#define MSB (1U<<(N-1))
#define NV 16
#define MAXPOOL (1<<18)
#define M0 0x67U
#define CHUNK 4   /* Dedup after bit 3 of each add/ch/maj operation */

typedef struct { uint16_t m; uint8_t c; } AF;
static inline AF af_c(int v)     { return (AF){0,(uint8_t)(v&1)}; }
static inline AF af_v(int i)     { return (AF){(uint16_t)(1U<<i),0}; }
static inline AF af_x(AF a,AF b) { return (AF){(uint16_t)(a.m^b.m),(uint8_t)(a.c^b.c)}; }
static inline int af_ic(AF f)    { return f.m==0; }
static inline int af_cv(AF f)    { return f.c; }

typedef struct { uint16_t rm[NV]; uint8_t rc[NV], has[NV]; int rank; } G2;
static void g2_init(G2*s) { memset(s,0,sizeof(G2)); }
static int g2_add(G2*s,AF f) {
    for(int i=NV-1;i>=0;i--) { if(!((f.m>>i)&1)) continue;
        if(s->has[i]) { f.m^=s->rm[i]; f.c^=s->rc[i]; }
        else { s->rm[i]=f.m; s->rc[i]=f.c; s->has[i]=1; s->rank++;
            for(int j=0;j<NV;j++) if(j!=i&&s->has[j]&&((s->rm[j]>>i)&1))
                { s->rm[j]^=f.m; s->rc[j]^=f.c; }
            return 1; }}
    return (f.c==0);
}
static AF g2_r(const G2*s,AF f) {
    for(int i=NV-1;i>=0;i--) if(((f.m>>i)&1)&&s->has[i]) { f.m^=s->rm[i]; f.c^=s->rc[i]; }
    return f;
}

static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;
static int SR(int k) { int r=(int)rint((double)k*N/32.0); return r<1?1:r; }
static inline uint32_t ror_n(uint32_t x,int k) { k%=N; return((x>>k)|(x<<(N-k)))&MASK; }
static inline uint32_t fnS0(uint32_t a)  { return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]); }
static inline uint32_t fnS1(uint32_t e)  { return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]); }
static inline uint32_t fns0(uint32_t x)  { return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&MASK); }
static inline uint32_t fns1(uint32_t x)  { return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&MASK); }
static inline uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g) { return((e&f)^((~e)&g))&MASK; }
static inline uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c) { return((a&b)^(a&c)^(b&c))&MASK; }

static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t KN[64],IVN[8],s1c[8],s2c[8],W1p[57],W2p[57];

static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]) {
    for(int i=0;i<16;i++) W[i]=M[i]&MASK;
    for(int i=16;i<57;i++) W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&MASK,T2=(fnS0(a)+fnMj(a,b,c))&MASK;
        h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}
static void bf_round(uint32_t s[8],uint32_t k,uint32_t w) {
    uint32_t T1=(s[7]+fnS1(s[4])+fnCh(s[4],s[5],s[6])+k+w)&MASK,T2=(fnS0(s[0])+fnMj(s[0],s[1],s[2]))&MASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;
}
static uint32_t cas_off(const uint32_t st1[8],const uint32_t st2[8],int rr) {
    return((st1[7]+fnS1(st1[4])+fnCh(st1[4],st1[5],st1[6])+KN[rr])
          -(st2[7]+fnS1(st2[4])+fnCh(st2[4],st2[5],st2[6])+KN[rr])
          +(fnS0(st1[0])+fnMj(st1[0],st1[1],st1[2]))
          -(fnS0(st2[0])+fnMj(st2[0],st2[1],st2[2])))&MASK;
}

/* Pool state */
typedef struct {
    G2 sys;
    AF r1[8][N],r2[8][N];
    AF ax[N],ay[N],az[N]; int ac;
    AF ch[N],maj[N],t1[N],t2[N],w[N];
} ST;

static ST*PA,*PB;
static uint64_t stat_br=0,stat_cx=0;

static void aS0(AF o[N],const AF a[N]) { for(int i=0;i<N;i++) o[i]=af_x(af_x(a[(i+rS0[0])%N],a[(i+rS0[1])%N]),a[(i+rS0[2])%N]); }
static void aS1(AF o[N],const AF e[N]) { for(int i=0;i<N;i++) o[i]=af_x(af_x(e[(i+rS1[0])%N],e[(i+rS1[1])%N]),e[(i+rS1[2])%N]); }

/* ================================================================
 * Quotient-state hash for pool dedup
 *
 * Two pool states are equivalent if they will produce the same
 * results for ALL remaining bit positions. This requires:
 * 1. Same carry-out (the `ac` field = carry into the next bit)
 * 2. Same GF2 system (same constraints on remaining variables)
 * 3. Same affine forms for all register bits at positions >= current
 *    (these determine future branching behavior)
 *
 * Simplified check: hash the full state fingerprint. Two states
 * that hash the same AND compare equal are merged.
 * ================================================================ */

#define DHT_BITS 20
#define DHT_SIZE (1U << DHT_BITS)
#define DHT_MASK (DHT_SIZE - 1)

typedef struct {
    uint64_t hash;
    int pool_idx;
    int occupied;
} DHTEntry;

static DHTEntry *dht;
static uint64_t dedup_total=0, dedup_merged=0;

static void dht_init(void) { dht = calloc(DHT_SIZE, sizeof(DHTEntry)); }
static void dht_reset(void) { memset(dht, 0, DHT_SIZE * sizeof(DHTEntry)); }
static void dht_free(void) { free(dht); }

/* Compute a fingerprint of pool state for dedup.
 * Includes: carry, GF2 RREF, and affine register forms for bits >= lo_bit.
 * This fingerprint determines behavior for remaining bits. */
static uint64_t pool_fingerprint(const ST *st, int lo_bit) {
    uint64_t h = 14695981039346656037ULL;
    /* Carry */
    h ^= (uint32_t)st->ac; h *= 1099511628211ULL;
    /* GF2 RREF */
    for(int i=0;i<NV;i++) {
        if(st->sys.has[i]) {
            h ^= st->sys.rm[i]; h *= 1099511628211ULL;
            h ^= st->sys.rc[i]; h *= 1099511628211ULL;
        }
    }
    /* Register affine forms for bits lo_bit..N-1 (both messages) */
    for(int r=0;r<8;r++) {
        for(int b=lo_bit;b<N;b++) {
            h ^= st->r1[r][b].m; h *= 1099511628211ULL;
            h ^= st->r1[r][b].c; h *= 1099511628211ULL;
            h ^= st->r2[r][b].m; h *= 1099511628211ULL;
            h ^= st->r2[r][b].c; h *= 1099511628211ULL;
        }
    }
    /* Workspace: ax, ay bits lo_bit..N-1 (determines remaining add behavior) */
    for(int b=lo_bit;b<N;b++) {
        h ^= st->ax[b].m; h *= 1099511628211ULL;
        h ^= st->ax[b].c; h *= 1099511628211ULL;
        h ^= st->ay[b].m; h *= 1099511628211ULL;
        h ^= st->ay[b].c; h *= 1099511628211ULL;
    }
    /* Also include already-computed az bits (for bits < lo_bit) */
    for(int b=0;b<lo_bit;b++) {
        h ^= st->az[b].m + 0x100; h *= 1099511628211ULL;
        h ^= st->az[b].c + 0x200; h *= 1099511628211ULL;
    }
    return h;
}

/* Full comparison of two pool states for dedup */
static int pool_state_eq(const ST *a, const ST *b, int lo_bit) {
    if(a->ac != b->ac) return 0;
    /* GF2 */
    for(int i=0;i<NV;i++) {
        if(a->sys.has[i] != b->sys.has[i]) return 0;
        if(a->sys.has[i]) {
            if(a->sys.rm[i]!=b->sys.rm[i] || a->sys.rc[i]!=b->sys.rc[i]) return 0;
        }
    }
    /* Registers */
    for(int r=0;r<8;r++) for(int bi=lo_bit;bi<N;bi++) {
        if(a->r1[r][bi].m!=b->r1[r][bi].m || a->r1[r][bi].c!=b->r1[r][bi].c) return 0;
        if(a->r2[r][bi].m!=b->r2[r][bi].m || a->r2[r][bi].c!=b->r2[r][bi].c) return 0;
    }
    /* Workspace */
    for(int bi=lo_bit;bi<N;bi++) {
        if(a->ax[bi].m!=b->ax[bi].m || a->ax[bi].c!=b->ax[bi].c) return 0;
        if(a->ay[bi].m!=b->ay[bi].m || a->ay[bi].c!=b->ay[bi].c) return 0;
    }
    for(int bi=0;bi<lo_bit;bi++) {
        if(a->az[bi].m!=b->az[bi].m || a->az[bi].c!=b->az[bi].c) return 0;
    }
    return 1;
}

/* Deduplicate pool PA[0..n-1]. Returns new size. */
static int dedup_pool(int n, int lo_bit) {
    if(n <= 1) return n;
    dht_reset();
    int no=0;
    for(int i=0;i<n;i++) {
        uint64_t h = pool_fingerprint(&PA[i], lo_bit);
        uint32_t slot = (uint32_t)(h & DHT_MASK);
        int found=0;
        for(int probe=0;probe<4096;probe++) {
            uint32_t idx = (slot+probe)&DHT_MASK;
            if(!dht[idx].occupied) {
                dht[idx].hash = h;
                dht[idx].pool_idx = no;
                dht[idx].occupied = 1;
                PB[no] = PA[i];
                no++;
                found=1;
                dedup_total++;
                break;
            }
            if(dht[idx].hash==h && pool_state_eq(&PA[i],&PB[dht[idx].pool_idx],lo_bit)) {
                /* Duplicate — merge (skip). The representative in PB already covers this. */
                dedup_merged++;
                dedup_total++;
                found=1;
                break;
            }
        }
        if(!found) { PB[no]=PA[i]; no++; dedup_total++; } /* hash full, keep */
    }
    ST*t=PA;PA=PB;PB=t;
    return no;
}

/* ================================================================
 * Pool operations with chunk-boundary dedup
 *
 * These are IDENTICAL to FACE operations except: after processing
 * bit CHUNK-1, we call dedup_pool() to merge equivalent states.
 * ================================================================ */

/* 3-mode N-bit pool addition with mid-stream dedup */
static int p_add(int n) {
    for(int bit=0;bit<N;bit++) {
        int no=0;
        for(int i=0;i<n&&no<MAXPOOL-3;i++) {
            AF xf=g2_r(&PA[i].sys,PA[i].ax[bit]),yf=g2_r(&PA[i].sys,PA[i].ay[bit]);
            int cin=PA[i].ac,xc=af_ic(xf),yc=af_ic(yf);
            if(xc&&yc) {
                int xv=af_cv(xf),yv=af_cv(yf);
                PB[no]=PA[i]; PB[no].az[bit]=af_c(xv^yv^cin);
                PB[no].ac=(xv&yv)|(xv&cin)|(yv&cin); no++; continue;
            }
            /* Mode 00 */
            {PB[no]=PA[i];int ok=1;
             if(!xc)ok=g2_add(&PB[no].sys,xf);else if(af_cv(xf))ok=0;
             if(ok){AF yr=g2_r(&PB[no].sys,PA[i].ay[bit]);if(!af_ic(yr))ok=g2_add(&PB[no].sys,yr);else if(af_cv(yr))ok=0;}
             if(ok){stat_br++;PB[no].az[bit]=af_c(cin);PB[no].ac=0;no++;}else stat_cx++;}
            /* Mode 01 */
            {PB[no]=PA[i];AF d=af_x(xf,yf);d.c^=1;
             int ok=af_ic(d)?(af_cv(d)==0):g2_add(&PB[no].sys,d);
             if(ok){stat_br++;PB[no].az[bit]=af_c(cin^1);PB[no].ac=cin;no++;}else stat_cx++;}
            /* Mode 11 */
            {PB[no]=PA[i];int ok=1;
             if(!xc){AF cx=xf;cx.c^=1;ok=g2_add(&PB[no].sys,cx);}else if(!af_cv(xf))ok=0;
             if(ok){AF yr=g2_r(&PB[no].sys,PA[i].ay[bit]);AF cy=yr;cy.c^=1;
                    if(!af_ic(yr))ok=g2_add(&PB[no].sys,cy);else if(!af_cv(yr))ok=0;}
             if(ok){stat_br++;PB[no].az[bit]=af_c(cin);PB[no].ac=1;no++;}else stat_cx++;}
        }
        ST*t=PA;PA=PB;PB=t;n=no;

        /* Chunk-boundary dedup */
        if(bit==CHUNK-1 && n>1) {
            n = dedup_pool(n, CHUNK);
        }
    }
    return n;
}

/* Pool Ch with dedup */
static int p_ch(int n,int m2) {
    for(int bit=0;bit<N;bit++) {
        int no=0;
        for(int i=0;i<n&&no<MAXPOOL-2;i++) {
            AF ef=g2_r(&PA[i].sys,PA[i].ax[bit]),ff=PA[i].ay[bit],gf=m2?PA[i].r2[6][bit]:PA[i].r1[6][bit];
            if(af_ic(ef)){PB[no]=PA[i];PB[no].az[bit]=af_cv(ef)?g2_r(&PB[no].sys,ff):g2_r(&PB[no].sys,gf);no++;}
            else{PB[no]=PA[i];if(g2_add(&PB[no].sys,ef)){stat_br++;PB[no].az[bit]=g2_r(&PB[no].sys,gf);no++;}else stat_cx++;
                 PB[no]=PA[i];{AF c=ef;c.c^=1;if(g2_add(&PB[no].sys,c)){stat_br++;PB[no].az[bit]=g2_r(&PB[no].sys,ff);no++;}else stat_cx++;}}
        }
        ST*t=PA;PA=PB;PB=t;n=no;
        if(bit==CHUNK-1 && n>1) n = dedup_pool(n, CHUNK);
    }
    return n;
}

/* Pool Maj with dedup */
static int p_maj(int n,int m2) {
    for(int bit=0;bit<N;bit++) {
        int no=0;
        for(int i=0;i<n&&no<MAXPOOL-4;i++) {
            AF a=g2_r(&PA[i].sys,PA[i].ax[bit]),b=g2_r(&PA[i].sys,PA[i].ay[bit]),
               c=g2_r(&PA[i].sys,m2?PA[i].r2[2][bit]:PA[i].r1[2][bit]);
            int ac_=af_ic(a),bc_=af_ic(b),cc_=af_ic(c);
            if(ac_&&bc_&&cc_){int av=af_cv(a),bv=af_cv(b),cv=af_cv(c);
                PB[no]=PA[i];PB[no].az[bit]=af_c((av&bv)^(av&cv)^(bv&cv));no++;}
            else if(bc_&&cc_){int bv=af_cv(b),cv=af_cv(c);
                PB[no]=PA[i];PB[no].az[bit]=(bv==cv)?af_c(bv):a;no++;}
            else if(ac_&&cc_){int av=af_cv(a),cv=af_cv(c);
                PB[no]=PA[i];PB[no].az[bit]=(av==cv)?af_c(av):b;no++;}
            else if(ac_&&bc_){int av=af_cv(a),bv=af_cv(b);
                PB[no]=PA[i];PB[no].az[bit]=(av==bv)?af_c(av):
                    g2_r(&PB[no].sys,m2?PA[i].r2[2][bit]:PA[i].r1[2][bit]);no++;}
            else{for(int av=0;av<=1;av++){if(no>=MAXPOOL)break;
                PB[no]=PA[i];int ok=1;
                if(!ac_){AF cn=a;cn.c^=av;ok=g2_add(&PB[no].sys,cn);}else if(af_cv(a)!=av)ok=0;
                if(!ok){stat_cx++;continue;}stat_br++;
                AF br=g2_r(&PB[no].sys,PA[i].ay[bit]);
                AF cr=g2_r(&PB[no].sys,m2?PA[i].r2[2][bit]:PA[i].r1[2][bit]);
                if(af_ic(br)&&af_ic(cr)){int bvv=af_cv(br),cvv=af_cv(cr);
                    PB[no].az[bit]=af_c((av&bvv)^(av&cvv)^(bvv&cvv));no++;}
                else if(af_ic(br)){PB[no].az[bit]=(af_cv(br)==av)?af_c(av):cr;no++;}
                else if(af_ic(cr)){PB[no].az[bit]=(af_cv(cr)==av)?af_c(av):br;no++;}
                else{ST sv=PB[no];int ad=0;for(int bv=0;bv<=1&&no<MAXPOOL;bv++){
                    if(ad)PB[no]=sv;
                    AF bc2=br;bc2.c^=bv;if(!g2_add(&PB[no].sys,bc2)){stat_cx++;ad=1;continue;}stat_br++;
                    AF cr2=g2_r(&PB[no].sys,m2?PA[i].r2[2][bit]:PA[i].r1[2][bit]);
                    if(af_ic(cr2)){int cv2=af_cv(cr2);PB[no].az[bit]=af_c((av&bv)^(av&cv2)^(bv&cv2));}
                    else PB[no].az[bit]=(av==bv)?af_c(av):cr2;no++;ad=1;}}}}
        }
        ST*t=PA;PA=PB;PB=t;n=no;
        if(bit==CHUNK-1 && n>1) n = dedup_pool(n, CHUNK);
    }
    return n;
}

/* One round for one message (FACE architecture) */
static int do_rnd(int n,int rnd,int m2) {
    #define R(s,r) (m2?(s)->r2[r]:(s)->r1[r])
    for(int i=0;i<n;i++){memcpy(PA[i].ax,R(&PA[i],4),N*sizeof(AF));memcpy(PA[i].ay,R(&PA[i],5),N*sizeof(AF));}
    n=p_ch(n,m2);for(int i=0;i<n;i++)memcpy(PA[i].ch,PA[i].az,N*sizeof(AF));
    for(int i=0;i<n;i++){memcpy(PA[i].ax,R(&PA[i],7),N*sizeof(AF));aS1(PA[i].ay,R(&PA[i],4));PA[i].ac=0;}
    n=p_add(n);for(int i=0;i<n;i++)memcpy(PA[i].t1,PA[i].az,N*sizeof(AF));
    for(int i=0;i<n;i++){memcpy(PA[i].ax,PA[i].t1,N*sizeof(AF));memcpy(PA[i].ay,PA[i].ch,N*sizeof(AF));PA[i].ac=0;}
    n=p_add(n);for(int i=0;i<n;i++)memcpy(PA[i].t1,PA[i].az,N*sizeof(AF));
    {int rr=57+rnd;for(int i=0;i<n;i++){for(int b=0;b<N;b++)PA[i].ax[b]=af_c((KN[rr]>>b)&1);memcpy(PA[i].ay,PA[i].w,N*sizeof(AF));PA[i].ac=0;}}
    n=p_add(n);for(int i=0;i<n;i++)memcpy(PA[i].t2,PA[i].az,N*sizeof(AF));
    for(int i=0;i<n;i++){memcpy(PA[i].ax,PA[i].t1,N*sizeof(AF));memcpy(PA[i].ay,PA[i].t2,N*sizeof(AF));PA[i].ac=0;}
    n=p_add(n);for(int i=0;i<n;i++)memcpy(PA[i].t1,PA[i].az,N*sizeof(AF));
    for(int i=0;i<n;i++){memcpy(PA[i].ax,R(&PA[i],0),N*sizeof(AF));memcpy(PA[i].ay,R(&PA[i],1),N*sizeof(AF));}
    n=p_maj(n,m2);for(int i=0;i<n;i++)memcpy(PA[i].maj,PA[i].az,N*sizeof(AF));
    for(int i=0;i<n;i++){aS0(PA[i].ax,R(&PA[i],0));memcpy(PA[i].ay,PA[i].maj,N*sizeof(AF));PA[i].ac=0;}
    n=p_add(n);for(int i=0;i<n;i++)memcpy(PA[i].t2,PA[i].az,N*sizeof(AF));
    for(int i=0;i<n;i++){memcpy(PA[i].ax,R(&PA[i],3),N*sizeof(AF));memcpy(PA[i].ay,PA[i].t1,N*sizeof(AF));PA[i].ac=0;}
    n=p_add(n);for(int i=0;i<n;i++)memcpy(PA[i].ch,PA[i].az,N*sizeof(AF));
    for(int i=0;i<n;i++){memcpy(PA[i].ax,PA[i].t1,N*sizeof(AF));memcpy(PA[i].ay,PA[i].t2,N*sizeof(AF));PA[i].ac=0;}
    n=p_add(n);
    for(int i=0;i<n;i++){AF na[N],ne[N];memcpy(na,PA[i].az,N*sizeof(AF));memcpy(ne,PA[i].ch,N*sizeof(AF));
        AF(*RR)[N]=m2?PA[i].r2:PA[i].r1;
        memcpy(RR[7],RR[6],N*sizeof(AF));memcpy(RR[6],RR[5],N*sizeof(AF));
        memcpy(RR[5],RR[4],N*sizeof(AF));memcpy(RR[4],ne,N*sizeof(AF));
        memcpy(RR[3],RR[2],N*sizeof(AF));memcpy(RR[2],RR[1],N*sizeof(AF));
        memcpy(RR[1],RR[0],N*sizeof(AF));memcpy(RR[0],na,N*sizeof(AF));}
    return n;
    #undef R
}

/* ================================================================ */
int main(int argc,char**argv) {
    setbuf(stdout,NULL);
    int skip_bf=(argc>1&&!strcmp(argv[1],"--skip-bf"));

    rS0[0]=SR(2);rS0[1]=SR(13);rS0[2]=SR(22);
    rS1[0]=SR(6);rS1[1]=SR(11);rS1[2]=SR(25);
    rs0[0]=SR(7);rs0[1]=SR(18);ss0=SR(3);
    rs1[0]=SR(17);rs1[1]=SR(19);ss1=SR(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;

    printf("=== Quotient Transducer (N=%d, chunk=%d) ===\n",N,CHUNK);
    printf("16 vars (W1[59..60]), outer W1[57]xW1[58]\n");
    printf("FACE + mid-operation chunk-boundary dedup\n\n");

    uint32_t M1[16],M2[16];for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
    M1[0]=M0;M2[0]=M0^MSB;M2[9]=MASK^MSB;
    precompute(M1,s1c,W1p);precompute(M2,s2c,W2p);
    if(s1c[0]!=s2c[0]){printf("da56!=0\n");return 1;}
    printf("M[0]=0x%02x fill=0xff da56=0\n",M0);
    printf("st1: %02x %02x %02x %02x %02x %02x %02x %02x\n",s1c[0],s1c[1],s1c[2],s1c[3],s1c[4],s1c[5],s1c[6],s1c[7]);
    printf("st2: %02x %02x %02x %02x %02x %02x %02x %02x\n\n",s2c[0],s2c[1],s2c[2],s2c[3],s2c[4],s2c[5],s2c[6],s2c[7]);

    /* Brute force */
    int bf_count=0;double bf_time=0;
    uint32_t(*bf_sols)[4]=malloc(512*sizeof(uint32_t[4]));
    if(!skip_bf){
        printf("--- Brute force ---\n");struct timespec t0,t1;clock_gettime(CLOCK_MONOTONIC,&t0);
        for(uint64_t x=0;x<(1ULL<<(4*N));x++){
            uint32_t w1[4]={(uint32_t)(x&MASK),(uint32_t)((x>>N)&MASK),(uint32_t)((x>>(2*N))&MASK),(uint32_t)((x>>(3*N))&MASK)};
            uint32_t sa[8],sb[8];memcpy(sa,s1c,32);memcpy(sb,s2c,32);
            uint32_t W1f[7],W2f[7];
            W1f[0]=w1[0];W1f[1]=w1[1];W1f[2]=w1[2];W1f[3]=w1[3];
            W1f[4]=(fns1(w1[2])+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;
            W1f[5]=(fns1(w1[3])+W1p[55]+fns0(W1p[47])+W1p[46])&MASK;
            W1f[6]=(fns1(W1f[4])+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;
            for(int r=0;r<4;r++){uint32_t off=cas_off(sa,sb,57+r);W2f[r]=(W1f[r]+off)&MASK;
                bf_round(sa,KN[57+r],W1f[r]);bf_round(sb,KN[57+r],W2f[r]);}
            W2f[4]=(fns1(W2f[2])+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
            W2f[5]=(fns1(W2f[3])+W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
            W2f[6]=(fns1(W2f[4])+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;
            for(int r=4;r<7;r++){bf_round(sa,KN[57+r],W1f[r]);bf_round(sb,KN[57+r],W2f[r]);}
            int ok=1;for(int r=0;r<8;r++)if(sa[r]!=sb[r]){ok=0;break;}
            if(ok&&bf_count<512){memcpy(bf_sols[bf_count],w1,16);bf_count++;}}
        clock_gettime(CLOCK_MONOTONIC,&t1);bf_time=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
        printf("BF: %d collisions, %.3fs\n\n",bf_count,bf_time);
    }else{bf_count=260;printf("BF skipped (expected %d)\n\n",bf_count);}

    /* Quotient Transducer */
    printf("--- Quotient Transducer ---\n");
    PA=calloc(MAXPOOL,sizeof(ST));PB=calloc(MAXPOOL,sizeof(ST));
    if(!PA||!PB){printf("OOM\n");return 1;}
    dht_init();

    struct timespec ts0,ts1;clock_gettime(CLOCK_MONOTONIC,&ts0);
    int total_coll=0;
    uint64_t total_br=0,total_cx=0;
    uint32_t(*qt_sols)[4]=malloc(512*sizeof(uint32_t[4]));

    for(uint32_t w57=0;w57<(1U<<N);w57++){
        uint32_t w2_57=(w57+cas_off(s1c,s2c,57))&MASK;
        uint32_t st57_1[8],st57_2[8];memcpy(st57_1,s1c,32);memcpy(st57_2,s2c,32);
        bf_round(st57_1,KN[57],w57);bf_round(st57_2,KN[57],w2_57);

        for(uint32_t w58=0;w58<(1U<<N);w58++){
            uint32_t w2_58=(w58+cas_off(st57_1,st57_2,58))&MASK;
            uint32_t st58_1[8],st58_2[8];memcpy(st58_1,st57_1,32);memcpy(st58_2,st57_2,32);
            bf_round(st58_1,KN[58],w58);bf_round(st58_2,KN[58],w2_58);

            stat_br=0;stat_cx=0;
            uint32_t cas59=cas_off(st58_1,st58_2,59);

            int sn=1;g2_init(&PA[0].sys);
            for(int r=0;r<8;r++)for(int b=0;b<N;b++){
                PA[0].r1[r][b]=af_c((st58_1[r]>>b)&1);PA[0].r2[r][b]=af_c((st58_2[r]>>b)&1);}

            /* R59 msg1: W1[59] = vars 0..7 */
            for(int i=0;i<sn;i++)for(int b=0;b<N;b++)PA[i].w[b]=af_v(b);
            sn=do_rnd(sn,2,0);
            if(sn==0)goto next;

            /* R59 msg2: W2[59] = W1[59]+cas59 (symbolic add) */
            for(int i=0;i<sn;i++){for(int b=0;b<N;b++){PA[i].ax[b]=af_v(b);PA[i].ay[b]=af_c((cas59>>b)&1);}PA[i].ac=0;}
            sn=p_add(sn);
            for(int i=0;i<sn;i++)memcpy(PA[i].w,PA[i].az,N*sizeof(AF));
            sn=do_rnd(sn,2,1);
            if(sn==0)goto next;

            /* Extract concrete W1[59] and do concrete W1[60] loop */
            for(int si=0;si<sn;si++){
                uint32_t w59v=0;
                for(int b=0;b<N;b++){AF f=g2_r(&PA[si].sys,af_v(b));if(af_ic(f))w59v|=(af_cv(f)<<b);}

                uint32_t s59_1[8],s59_2[8];
                memcpy(s59_1,st58_1,32);memcpy(s59_2,st58_2,32);
                uint32_t w2_59=(w59v+cas59)&MASK;
                bf_round(s59_1,KN[59],w59v);bf_round(s59_2,KN[59],w2_59);

                uint32_t c60=cas_off(s59_1,s59_2,60);
                uint32_t W1_61=(fns1(w59v)+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;
                uint32_t W2_61=(fns1(w2_59)+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
                uint32_t W1_63=(fns1(W1_61)+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;
                uint32_t W2_63=(fns1(W2_61)+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;

                for(uint32_t w60=0;w60<(1U<<N);w60++){
                    uint32_t w2_60=(w60+c60)&MASK;
                    uint32_t s60_1[8],s60_2[8];memcpy(s60_1,s59_1,32);memcpy(s60_2,s59_2,32);
                    bf_round(s60_1,KN[60],w60);bf_round(s60_2,KN[60],w2_60);
                    uint32_t s61_1[8],s61_2[8];memcpy(s61_1,s60_1,32);memcpy(s61_2,s60_2,32);
                    bf_round(s61_1,KN[61],W1_61);bf_round(s61_2,KN[61],W2_61);
                    if(((s61_1[4]-s61_2[4])&MASK)!=0)continue;
                    uint32_t W1_62=(fns1(w60)+W1p[55]+fns0(W1p[47])+W1p[46])&MASK;
                    uint32_t W2_62=(fns1(w2_60)+W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
                    bf_round(s61_1,KN[62],W1_62);bf_round(s61_2,KN[62],W2_62);
                    bf_round(s61_1,KN[63],W1_63);bf_round(s61_2,KN[63],W2_63);
                    int ok=1;for(int r=0;r<8;r++)if(s61_1[r]!=s61_2[r]){ok=0;break;}
                    if(ok){uint32_t ww[4]={w57,w58,w59v,w60};
                        if(total_coll<512)memcpy(qt_sols[total_coll],ww,16);
                        total_coll++;}
                }
            }

            next:
            total_br+=stat_br;total_cx+=stat_cx;
        }
        if((w57&0xF)==0xF){clock_gettime(CLOCK_MONOTONIC,&ts1);
            double el=(ts1.tv_sec-ts0.tv_sec)+(ts1.tv_nsec-ts0.tv_nsec)/1e9;
            printf("  [%3.0f%%] w57=%3u coll=%d dedup=%llu/%llu(%.1f%%) %.1fs\n",
                   100.0*(w57+1)/(1U<<N),w57,total_coll,
                   (unsigned long long)dedup_merged,(unsigned long long)dedup_total,
                   dedup_total?100.0*dedup_merged/dedup_total:0,el);}
    }
    clock_gettime(CLOCK_MONOTONIC,&ts1);
    double qt_time=(ts1.tv_sec-ts0.tv_sec)+(ts1.tv_nsec-ts0.tv_nsec)/1e9;

    /* Cross-validation */
    int matched=0,missed=0;
    if(!skip_bf){
        for(int i=0;i<total_coll&&i<512;i++)for(int j=0;j<bf_count;j++)
            if(!memcmp(qt_sols[i],bf_sols[j],16)){matched++;break;}
        for(int j=0;j<bf_count;j++){int f=0;
            for(int i=0;i<total_coll&&i<512;i++)if(!memcmp(qt_sols[i],bf_sols[j],16)){f=1;break;}
            if(!f){if(missed<5)printf("  MISSED: [%02x,%02x,%02x,%02x]\n",bf_sols[j][0],bf_sols[j][1],bf_sols[j][2],bf_sols[j][3]);missed++;}}
    }

    printf("\nFirst 10 solutions:\n");
    for(int i=0;i<total_coll&&i<10&&i<512;i++)
        printf("  #%d: W1=[%02x,%02x,%02x,%02x]\n",i+1,qt_sols[i][0],qt_sols[i][1],qt_sols[i][2],qt_sols[i][3]);

    printf("\n========================================\n");
    printf("  Quotient Transducer Results (N=%d)\n",N);
    printf("========================================\n");
    printf("Candidate:            M[0]=0x%02x fill=0xff\n",M0);
    if(!skip_bf)printf("Brute force:          %d collisions (%.3fs)\n",bf_count,bf_time);
    printf("\nQT Solver:\n");
    printf("  Collisions found:   %d\n",total_coll);
    if(!skip_bf){printf("  Matched BF:         %d / %d\n",matched,bf_count);printf("  Missed:             %d\n",missed);}
    printf("\nChunk-boundary dedup:\n");
    printf("  States processed:   %llu\n",(unsigned long long)dedup_total);
    printf("  States merged:      %llu\n",(unsigned long long)dedup_merged);
    if(dedup_total>0)printf("  Merge rate:         %.1f%%\n",100.0*dedup_merged/dedup_total);
    printf("\nBranch stats:\n");
    printf("  Branches:           %llu\n",(unsigned long long)total_br);
    printf("  Contradictions:     %llu\n",(unsigned long long)total_cx);
    printf("  BF evals:           %llu (2^%d)\n",1ULL<<(4*N),4*N);
    printf("\nTiming:\n");
    if(!skip_bf)printf("  BF time:            %.3fs\n",bf_time);
    printf("  QT time:            %.3fs\n",qt_time);
    if(!skip_bf&&qt_time>0.001)printf("  Speedup:            %.2fx\n",bf_time/qt_time);
    printf("\n");
    if(total_coll==bf_count&&missed==0)
        printf("*** ALL %d COLLISIONS FOUND AND VERIFIED ***\n",bf_count);
    else if(total_coll==260&&skip_bf)
        printf("*** ALL 260 COLLISIONS FOUND (BF skipped) ***\n");
    else printf("*** QT=%d BF=%d missed=%d ***\n",total_coll,bf_count,missed);

    free(PA);free(PB);free(bf_sols);free(qt_sols);dht_free();
    return 0;
}
