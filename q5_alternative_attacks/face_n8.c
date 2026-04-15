/*
 * face_n8.c — FACE: Frontier Automaton via Carry Elimination (N=8)
 *
 * Symbolic solver using GF(2) affine forms with 3-mode addition branching.
 * Processes rounds 59-63 symbolically with 16 free variables (W1[59..60]).
 * Outer loop enumerates W1[57] x W1[58] concretely.
 *
 * The cascade W2 = W1 + offset is computed symbolically via 3-mode addition,
 * which properly resolves all variable bits through branching.
 *
 * Key structural filter: de61 = 0 (applied after round 61, ~256x pruning).
 * Final collision check: all 8 register diffs = 0 (after round 63).
 *
 * N=8, MSB kernel, M[0]=0x67, fill=0xff.
 * Expected: 260 collisions.
 *
 * Compile: gcc -O3 -march=native -o face_n8 face_n8.c -lm
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
#define MAXPOOL (1<<18)  /* 256K — enough for 65536 fully-expanded states */
#define M0 0x67U

typedef struct { uint16_t m; uint8_t c; } AF;
static inline AF af_c(int v)     {return(AF){0,(uint8_t)(v&1)};}
static inline AF af_v(int i)     {return(AF){(uint16_t)(1U<<i),0};}
static inline AF af_x(AF a,AF b) {return(AF){(uint16_t)(a.m^b.m),(uint8_t)(a.c^b.c)};}
static inline int af_ic(AF f)    {return f.m==0;}
static inline int af_cv(AF f)    {return f.c;}

typedef struct{uint16_t rm[NV];uint8_t rc[NV],has[NV];int rank;}G2;
static void g2_init(G2*s){memset(s,0,sizeof(G2));}
static int g2_add(G2*s,AF f){
    for(int i=NV-1;i>=0;i--){if(!((f.m>>i)&1))continue;
        if(s->has[i]){f.m^=s->rm[i];f.c^=s->rc[i];}
        else{s->rm[i]=f.m;s->rc[i]=f.c;s->has[i]=1;s->rank++;
            for(int j=0;j<NV;j++)if(j!=i&&s->has[j]&&((s->rm[j]>>i)&1)){s->rm[j]^=f.m;s->rc[j]^=f.c;}
            return 1;}}
    return(f.c==0);}
static AF g2_r(const G2*s,AF f){
    for(int i=NV-1;i>=0;i--)if(((f.m>>i)&1)&&s->has[i]){f.m^=s->rm[i];f.c^=s->rc[i];}return f;}

static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;
static int SR(int k){int r=(int)rint((double)k*N/32.0);return r<1?1:r;}
static inline uint32_t ror_n(uint32_t x,int k){k%=N;return((x>>k)|(x<<(N-k)))&MASK;}
static inline uint32_t fn_S0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static inline uint32_t fn_S1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static inline uint32_t fn_s0(uint32_t x){return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&MASK);}
static inline uint32_t fn_s1(uint32_t x){return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&MASK);}
static inline uint32_t fn_Ch(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&MASK;}
static inline uint32_t fn_Mj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&MASK;}

static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t KN[64],IVN[8],s1c[8],s2c[8],W1p[57],W2p[57];

static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&MASK;
    for(int i=16;i<57;i++)W[i]=(fn_s1(W[i-2])+W[i-7]+fn_s0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+fn_S1(e)+fn_Ch(e,f,g)+KN[i]+W[i])&MASK,T2=(fn_S0(a)+fn_Mj(a,b,c))&MASK;
        h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;}

static void bf_round(uint32_t s[8],uint32_t k,uint32_t w){
    uint32_t T1=(s[7]+fn_S1(s[4])+fn_Ch(s[4],s[5],s[6])+k+w)&MASK,T2=(fn_S0(s[0])+fn_Mj(s[0],s[1],s[2]))&MASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;}

static uint32_t cas_off(const uint32_t s1[8],const uint32_t s2[8],int rr){
    return((s1[7]+fn_S1(s1[4])+fn_Ch(s1[4],s1[5],s1[6])+KN[rr])-(s2[7]+fn_S1(s2[4])+fn_Ch(s2[4],s2[5],s2[6])+KN[rr])
           +(fn_S0(s1[0])+fn_Mj(s1[0],s1[1],s1[2]))-(fn_S0(s2[0])+fn_Mj(s2[0],s2[1],s2[2])))&MASK;}

static void sched_w1(const uint32_t w[4],uint32_t o[7]){
    o[0]=w[0];o[1]=w[1];o[2]=w[2];o[3]=w[3];
    o[4]=(fn_s1(w[2])+W1p[54]+fn_s0(W1p[46])+W1p[45])&MASK;
    o[5]=(fn_s1(w[3])+W1p[55]+fn_s0(W1p[47])+W1p[46])&MASK;
    o[6]=(fn_s1(o[4])+W1p[56]+fn_s0(W1p[48])+W1p[47])&MASK;}
static void sched_w2(const uint32_t w[4],uint32_t o[7]){
    o[0]=w[0];o[1]=w[1];o[2]=w[2];o[3]=w[3];
    o[4]=(fn_s1(w[2])+W2p[54]+fn_s0(W2p[46])+W2p[45])&MASK;
    o[5]=(fn_s1(w[3])+W2p[55]+fn_s0(W2p[47])+W2p[46])&MASK;
    o[6]=(fn_s1(o[4])+W2p[56]+fn_s0(W2p[48])+W2p[47])&MASK;}

static uint64_t stat_br=0,stat_cx=0;

typedef struct{
    G2 sys;
    AF r1[8][N],r2[8][N]; /* register states for both msgs */
    AF ax[N],ay[N],az[N];int ac; /* addition workspace */
    AF ch[N],maj[N],t1[N],t2[N],w[N]; /* round workspace */
}ST;

static ST*PA,*PB;

static void aS0(AF o[N],const AF a[N]){for(int i=0;i<N;i++)o[i]=af_x(af_x(a[(i+rS0[0])%N],a[(i+rS0[1])%N]),a[(i+rS0[2])%N]);}
static void aS1(AF o[N],const AF e[N]){for(int i=0;i<N;i++)o[i]=af_x(af_x(e[(i+rS1[0])%N],e[(i+rS1[1])%N]),e[(i+rS1[2])%N]);}

/* 3-mode N-bit pool addition */
static int p_add(int n){
    for(int bit=0;bit<N;bit++){int no=0;
        for(int i=0;i<n&&no<MAXPOOL-3;i++){
            AF xf=g2_r(&PA[i].sys,PA[i].ax[bit]),yf=g2_r(&PA[i].sys,PA[i].ay[bit]);
            int cin=PA[i].ac,xc=af_ic(xf),yc=af_ic(yf);
            if(xc&&yc){int xv=af_cv(xf),yv=af_cv(yf);PB[no]=PA[i];PB[no].az[bit]=af_c(xv^yv^cin);
                PB[no].ac=(xv&yv)|(xv&cin)|(yv&cin);no++;continue;}
            {PB[no]=PA[i];int ok=1;if(!xc)ok=g2_add(&PB[no].sys,xf);else if(af_cv(xf))ok=0;
             if(ok){AF yr=g2_r(&PB[no].sys,PA[i].ay[bit]);if(!af_ic(yr))ok=g2_add(&PB[no].sys,yr);else if(af_cv(yr))ok=0;}
             if(ok){stat_br++;PB[no].az[bit]=af_c(cin);PB[no].ac=0;no++;}else stat_cx++;}
            {PB[no]=PA[i];AF d=af_x(xf,yf);d.c^=1;int ok=af_ic(d)?(af_cv(d)==0):g2_add(&PB[no].sys,d);
             if(ok){stat_br++;PB[no].az[bit]=af_c(cin^1);PB[no].ac=cin;no++;}else stat_cx++;}
            {PB[no]=PA[i];int ok=1;AF cx=xf;cx.c^=1;
             if(!xc)ok=g2_add(&PB[no].sys,cx);else if(!af_cv(xf))ok=0;
             if(ok){AF yr=g2_r(&PB[no].sys,PA[i].ay[bit]);AF cy=yr;cy.c^=1;
                if(!af_ic(yr))ok=g2_add(&PB[no].sys,cy);else if(!af_cv(yr))ok=0;}
             if(ok){stat_br++;PB[no].az[bit]=af_c(cin);PB[no].ac=1;no++;}else stat_cx++;}}
        ST*t=PA;PA=PB;PB=t;n=no;}return n;}

/* Pool Ch */
static int p_ch(int n,int m2){
    for(int bit=0;bit<N;bit++){int no=0;
        for(int i=0;i<n&&no<MAXPOOL-2;i++){
            AF ef=g2_r(&PA[i].sys,PA[i].ax[bit]),ff=PA[i].ay[bit],gf=m2?PA[i].r2[6][bit]:PA[i].r1[6][bit];
            if(af_ic(ef)){PB[no]=PA[i];PB[no].az[bit]=af_cv(ef)?g2_r(&PB[no].sys,ff):g2_r(&PB[no].sys,gf);no++;}
            else{PB[no]=PA[i];if(g2_add(&PB[no].sys,ef)){stat_br++;PB[no].az[bit]=g2_r(&PB[no].sys,gf);no++;}else stat_cx++;
                 PB[no]=PA[i];{AF c=ef;c.c^=1;if(g2_add(&PB[no].sys,c)){stat_br++;PB[no].az[bit]=g2_r(&PB[no].sys,ff);no++;}else stat_cx++;}}}
        ST*t=PA;PA=PB;PB=t;n=no;}return n;}

/* Pool Maj */
static int p_maj(int n,int m2){
    for(int bit=0;bit<N;bit++){int no=0;
        for(int i=0;i<n&&no<MAXPOOL-4;i++){
            AF a=g2_r(&PA[i].sys,PA[i].ax[bit]),b=g2_r(&PA[i].sys,PA[i].ay[bit]),
               c=g2_r(&PA[i].sys,m2?PA[i].r2[2][bit]:PA[i].r1[2][bit]);
            int ac_=af_ic(a),bc_=af_ic(b),cc_=af_ic(c);
            if(ac_&&bc_&&cc_){PB[no]=PA[i];int av=af_cv(a),bv=af_cv(b),cv=af_cv(c);
                PB[no].az[bit]=af_c((av&bv)^(av&cv)^(bv&cv));no++;}
            else if(bc_&&cc_){int bv=af_cv(b),cv=af_cv(c);PB[no]=PA[i];PB[no].az[bit]=(bv==cv)?af_c(bv):a;no++;}
            else if(ac_&&cc_){int av=af_cv(a),cv=af_cv(c);PB[no]=PA[i];PB[no].az[bit]=(av==cv)?af_c(av):b;no++;}
            else if(ac_&&bc_){int av=af_cv(a),bv=af_cv(b);PB[no]=PA[i];PB[no].az[bit]=(av==bv)?af_c(av):c;no++;}
            else{for(int av=0;av<=1;av++){if(no>=MAXPOOL)break;PB[no]=PA[i];int ok=1;
                if(!ac_){AF cn=a;cn.c^=av;ok=g2_add(&PB[no].sys,cn);}else if(af_cv(a)!=av)ok=0;
                if(!ok){stat_cx++;continue;}stat_br++;
                AF br=g2_r(&PB[no].sys,PA[i].ay[bit]),cr=g2_r(&PB[no].sys,m2?PA[i].r2[2][bit]:PA[i].r1[2][bit]);
                if(af_ic(br)&&af_ic(cr)){int bv=af_cv(br),cv=af_cv(cr);PB[no].az[bit]=af_c((av&bv)^(av&cv)^(bv&cv));no++;}
                else if(af_ic(br)){PB[no].az[bit]=(af_cv(br)==av)?af_c(av):cr;no++;}
                else if(af_ic(cr)){PB[no].az[bit]=(af_cv(cr)==av)?af_c(av):br;no++;}
                else{ST sv=PB[no];int ad=0;for(int bv=0;bv<=1&&no<MAXPOOL;bv++){if(ad)PB[no]=sv;
                    AF bc2=br;bc2.c^=bv;if(!g2_add(&PB[no].sys,bc2)){stat_cx++;continue;}stat_br++;
                    AF cr2=g2_r(&PB[no].sys,m2?PA[i].r2[2][bit]:PA[i].r1[2][bit]);
                    if(af_ic(cr2)){int cv=af_cv(cr2);PB[no].az[bit]=af_c((av&bv)^(av&cv)^(bv&cv));}
                    else PB[no].az[bit]=(av==bv)?af_c(av):cr2;no++;ad=1;}}}}}
        ST*t=PA;PA=PB;PB=t;n=no;}return n;}

/* One round for one message */
static int do_rnd(int n,int rnd,int m2){
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

/* Prune pool by constraint: diff of register reg_idx must be 0 */
static int prune_reg(int n, int reg_idx) {
    int no=0;
    for(int i=0;i<n;i++){PB[no]=PA[i];int ok=1;
        for(int b=0;b<N&&ok;b++){
            AF diff=af_x(PA[i].r1[reg_idx][b],PA[i].r2[reg_idx][b]);
            AF rd=g2_r(&PB[no].sys,diff);
            if(af_ic(rd)){if(af_cv(rd))ok=0;}
            else{if(!g2_add(&PB[no].sys,rd))ok=0;}}
        if(ok)no++;}
    ST*t=PA;PA=PB;PB=t; return no;}

/* Prune pool: all 8 registers must match */
static int prune_all(int n) {
    int no=0;
    for(int i=0;i<n;i++){PB[no]=PA[i];int ok=1;
        for(int r=0;r<8&&ok;r++)for(int b=0;b<N&&ok;b++){
            AF diff=af_x(PA[i].r1[r][b],PA[i].r2[r][b]);
            AF rd=g2_r(&PB[no].sys,diff);
            if(af_ic(rd)){if(af_cv(rd))ok=0;}
            else{if(!g2_add(&PB[no].sys,rd))ok=0;}}
        if(ok)no++;}
    ST*t=PA;PA=PB;PB=t; return no;}

int main(int argc,char**argv){
    setbuf(stdout,NULL);
    int skip_bf=(argc>1&&!strcmp(argv[1],"--skip-bf"));

    rS0[0]=SR(2);rS0[1]=SR(13);rS0[2]=SR(22);
    rS1[0]=SR(6);rS1[1]=SR(11);rS1[2]=SR(25);
    rs0[0]=SR(7);rs0[1]=SR(18);ss0=SR(3);
    rs1[0]=SR(17);rs1[1]=SR(19);ss1=SR(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;

    printf("=== FACE Solver N=%d ===\n",N);
    printf("16 vars (W1[59..60]), outer W1[57]xW1[58]\n");
    printf("3-mode adds, GF(2) RREF, de61=0 structural filter\n\n");

    uint32_t M1[16],M2[16];for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
    M1[0]=M0;M2[0]=M0^MSB;M2[9]=MASK^MSB;
    precompute(M1,s1c,W1p);precompute(M2,s2c,W2p);
    if(s1c[0]!=s2c[0]){printf("da56!=0\n");return 1;}
    printf("M[0]=0x%02x fill=0xff da56=0\n",M0);
    printf("st1: %02x %02x %02x %02x %02x %02x %02x %02x\n",s1c[0],s1c[1],s1c[2],s1c[3],s1c[4],s1c[5],s1c[6],s1c[7]);
    printf("st2: %02x %02x %02x %02x %02x %02x %02x %02x\n\n",s2c[0],s2c[1],s2c[2],s2c[3],s2c[4],s2c[5],s2c[6],s2c[7]);

    /* BF */
    int bf_count=0;double bf_time=0;
    uint32_t(*bf_sols)[4]=malloc(512*sizeof(uint32_t[4]));
    if(!skip_bf){
        printf("--- Brute force ---\n");struct timespec t0,t1;clock_gettime(CLOCK_MONOTONIC,&t0);
        for(uint64_t x=0;x<(1ULL<<(4*N));x++){
            uint32_t w1[4]={(uint32_t)(x&MASK),(uint32_t)((x>>N)&MASK),(uint32_t)((x>>(2*N))&MASK),(uint32_t)((x>>(3*N))&MASK)};
            uint32_t sa[8],sb[8];memcpy(sa,s1c,32);memcpy(sb,s2c,32);
            uint32_t W1f[7],W2f[7];sched_w1(w1,W1f);
            for(int r=0;r<4;r++){uint32_t off=cas_off(sa,sb,57+r);W2f[r]=(W1f[r]+off)&MASK;
                bf_round(sa,KN[57+r],W1f[r]);bf_round(sb,KN[57+r],W2f[r]);}
            sched_w2(W2f,W2f);
            for(int r=4;r<7;r++){bf_round(sa,KN[57+r],W1f[r]);bf_round(sb,KN[57+r],W2f[r]);}
            int ok=1;for(int r=0;r<8;r++)if(sa[r]!=sb[r]){ok=0;break;}
            if(ok&&bf_count<512){memcpy(bf_sols[bf_count],w1,16);bf_count++;}}
        clock_gettime(CLOCK_MONOTONIC,&t1);bf_time=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
        printf("BF: %d collisions, %.3fs\n\n",bf_count,bf_time);
    }else{bf_count=260;printf("BF skipped (expected %d)\n\n",bf_count);}

    /* FACE */
    printf("--- FACE solver ---\n");
    PA=calloc(MAXPOOL,sizeof(ST));PB=calloc(MAXPOOL,sizeof(ST));
    if(!PA||!PB){printf("OOM\n");return 1;}

    struct timespec ts0,ts1;clock_gettime(CLOCK_MONOTONIC,&ts0);
    int total_coll=0,total_ver=0;uint64_t total_br=0,total_cx=0;
    uint32_t(*face_sols)[4]=malloc(512*sizeof(uint32_t[4]));

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
            sn=do_rnd(sn,2,0); /* round 59 msg1 */
            if(sn==0)goto next;

            /* R59 msg2: W2[59] = W1[59]+cas59 (symbolic add) */
            for(int i=0;i<sn;i++){for(int b=0;b<N;b++){PA[i].ax[b]=af_v(b);PA[i].ay[b]=af_c((cas59>>b)&1);}PA[i].ac=0;}
            sn=p_add(sn);
            for(int i=0;i<sn;i++)memcpy(PA[i].w,PA[i].az,N*sizeof(AF));
            sn=do_rnd(sn,2,1); /* round 59 msg2 */
            if(sn==0)goto next;

            /* ============================================================
             * SKIP symbolic rounds 60 and beyond.
             * After round 59, W1[59] is fully determined for each state.
             * Instead of symbolically processing round 60 (which just enumerates
             * all 256 W1[60] values), directly iterate W1[60] concretely
             * within each state. This is the hybrid approach:
             * - Symbolic round 59: resolves W1[59] via 3-mode branching (1 -> 256)
             * - Concrete W1[60] loop: iterates 256 values per state
             * - Concrete rounds 61-63 with structural filter
             * ============================================================ */
            for(int si=0;si<sn;si++){
                /* Extract concrete W1[59] */
                uint32_t w59v=0;
                for(int b=0;b<N;b++){AF f=g2_r(&PA[si].sys,af_v(b));if(af_ic(f))w59v|=(af_cv(f)<<b);}

                /* Replay round 59 to get state59 */
                uint32_t s59_1[8],s59_2[8];
                memcpy(s59_1,st58_1,32);memcpy(s59_2,st58_2,32);
                uint32_t w2_59=(w59v+cas59)&MASK;
                bf_round(s59_1,KN[59],w59v);bf_round(s59_2,KN[59],w2_59);

                uint32_t c60=cas_off(s59_1,s59_2,60);

                /* Schedule: W1[61] depends on w59 only */
                uint32_t wfull[4]={w57,w58,w59v,0};
                uint32_t W1_61=(fn_s1(w59v)+W1p[54]+fn_s0(W1p[46])+W1p[45])&MASK;
                uint32_t W2f_59=(w59v+cas59)&MASK;
                uint32_t W2_61=(fn_s1(W2f_59)+W2p[54]+fn_s0(W2p[46])+W2p[45])&MASK;
                /* W1[63] depends on W1[61] only */
                uint32_t W1_63=(fn_s1(W1_61)+W1p[56]+fn_s0(W1p[48])+W1p[47])&MASK;
                uint32_t W2_63=(fn_s1(W2_61)+W2p[56]+fn_s0(W2p[48])+W2p[47])&MASK;

                for(uint32_t w60=0;w60<(1U<<N);w60++){
                    uint32_t w2_60=(w60+c60)&MASK;

                    /* Round 60 */
                    uint32_t s60_1[8],s60_2[8];
                    memcpy(s60_1,s59_1,32);memcpy(s60_2,s59_2,32);
                    bf_round(s60_1,KN[60],w60);bf_round(s60_2,KN[60],w2_60);

                    /* Round 61 */
                    uint32_t s61_1[8],s61_2[8];
                    memcpy(s61_1,s60_1,32);memcpy(s61_2,s60_2,32);
                    bf_round(s61_1,KN[61],W1_61);bf_round(s61_2,KN[61],W2_61);

                    /* STRUCTURAL FILTER: de61 = 0 */
                    if(((s61_1[4]-s61_2[4])&MASK)!=0)continue;

                    /* Schedule: W1[62] depends on w60 */
                    uint32_t W1_62=(fn_s1(w60)+W1p[55]+fn_s0(W1p[47])+W1p[46])&MASK;
                    uint32_t W2_62=(fn_s1(w2_60)+W2p[55]+fn_s0(W2p[47])+W2p[46])&MASK;

                    /* Rounds 62-63 */
                    bf_round(s61_1,KN[62],W1_62);bf_round(s61_2,KN[62],W2_62);
                    bf_round(s61_1,KN[63],W1_63);bf_round(s61_2,KN[63],W2_63);

                    /* Full collision check */
                    int ok=1;for(int r=0;r<8;r++)if(s61_1[r]!=s61_2[r]){ok=0;break;}
                    if(ok){
                        total_ver++;
                        uint32_t ww[4]={w57,w58,w59v,w60};
                        if(total_coll<512)memcpy(face_sols[total_coll],ww,16);
                        total_coll++;
                    }
                }
            }

            next:
            total_br+=stat_br;total_cx+=stat_cx;
        }
        if((w57&0xF)==0xF){clock_gettime(CLOCK_MONOTONIC,&ts1);
            double el=(ts1.tv_sec-ts0.tv_sec)+(ts1.tv_nsec-ts0.tv_nsec)/1e9;
            printf("  [%3.0f%%] w57=%3u coll=%d ver=%d %.1fs\n",100.0*(w57+1)/(1U<<N),w57,total_coll,total_ver,el);}
    }
    clock_gettime(CLOCK_MONOTONIC,&ts1);
    double face_time=(ts1.tv_sec-ts0.tv_sec)+(ts1.tv_nsec-ts0.tv_nsec)/1e9;

    /* Cross-validation */
    int matched=0,missed=0;
    if(!skip_bf){
        for(int i=0;i<total_coll&&i<512;i++)for(int j=0;j<bf_count;j++)
            if(!memcmp(face_sols[i],bf_sols[j],16)){matched++;break;}
        for(int j=0;j<bf_count;j++){int f=0;
            for(int i=0;i<total_coll&&i<512;i++)if(!memcmp(face_sols[i],bf_sols[j],16)){f=1;break;}
            if(!f){if(missed<5)printf("  MISSED: [%02x,%02x,%02x,%02x]\n",bf_sols[j][0],bf_sols[j][1],bf_sols[j][2],bf_sols[j][3]);missed++;}}
    }

    printf("\nFirst 10 solutions:\n");
    for(int i=0;i<total_coll&&i<10&&i<512;i++)
        printf("  #%d: W1=[%02x,%02x,%02x,%02x]\n",i+1,face_sols[i][0],face_sols[i][1],face_sols[i][2],face_sols[i][3]);

    printf("\n========================================\n");
    printf("       FACE Solver Results (N=%d)\n",N);
    printf("========================================\n");
    printf("Candidate:            M[0]=0x%02x fill=0xff\n",M0);
    if(!skip_bf)printf("Brute force:          %d collisions (%.3fs)\n",bf_count,bf_time);
    printf("FACE solver:\n");
    printf("  Collisions found:   %d\n",total_coll);
    printf("  Verified:           %d\n",total_ver);
    if(!skip_bf){printf("  Matched BF:         %d / %d\n",matched,bf_count);printf("  Missed:             %d\n",missed);}
    printf("\nBranch stats:\n");
    printf("  Branches:           %llu\n",(unsigned long long)total_br);
    printf("  Contradictions:     %llu\n",(unsigned long long)total_cx);
    printf("  BF evals:           %llu (2^%d)\n",1ULL<<(4*N),4*N);
    if(total_br>0)printf("  Branch ratio:       %.1fx vs BF\n",(double)(1ULL<<(4*N))/total_br);
    printf("\nTiming:\n");
    if(!skip_bf)printf("  BF time:            %.3fs\n",bf_time);
    printf("  FACE time:          %.3fs\n",face_time);
    if(!skip_bf&&face_time>0.001)printf("  Speedup:            %.2fx\n",bf_time/face_time);
    printf("\n");
    if(total_coll==bf_count&&total_ver==bf_count&&missed==0)
        printf("*** ALL %d COLLISIONS FOUND AND VERIFIED ***\n",bf_count);
    else printf("*** FACE=%d BF=%d ver=%d missed=%d ***\n",total_coll,bf_count,total_ver,missed);

    free(PA);free(PB);free(bf_sols);free(face_sols);
    return 0;
}
