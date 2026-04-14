/*
 * face_solver.c — FACE: Frontier Automaton via Carry Elimination
 *
 * Branch on addition MODES (00/01/11) instead of bit values. Each mode
 * linearizes the circuit over GF(2). The overconstrained system prunes
 * branches by detecting contradictions.
 *
 * Architecture: pool-based, round-serial. 16 free variables (W1[57..60] bits).
 * W2 derived from W1 via cascade offset (concrete per state).
 * 3-mode branching for all additions. Collision constraints applied after
 * each round pair. Cascade 'a'-register constraint used for early pruning.
 *
 * N=4, MSB kernel, M[0]=0x0, fill=0xf.
 * Compile: gcc -O3 -march=native -o face_solver face_solver.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define N 4
#define MASK ((1U<<N)-1)
#define MSB (1U<<(N-1))
#define NV (4*N)

typedef struct { uint32_t m; uint8_t c; } AF;
static inline AF af_c(int v)    { return (AF){0,(uint8_t)(v&1)}; }
static inline AF af_v(int i)    { return (AF){1U<<i,0}; }
static inline AF af_x(AF a,AF b){ return (AF){a.m^b.m,(uint8_t)(a.c^b.c)}; }
static inline int af_ic(AF f)   { return f.m==0; }
static inline int af_cv(AF f)   { return f.c; }

typedef struct { AF rows[NV]; uint8_t has[NV]; int rank; } G2;
static void g2_init(G2*s){memset(s,0,sizeof(G2));}

static int g2_add(G2*s,AF f){
    for(int i=NV-1;i>=0;i--){if(!((f.m>>i)&1))continue;
        if(s->has[i])f=af_x(f,s->rows[i]);
        else{s->rows[i]=f;s->has[i]=1;s->rank++;
            for(int j=0;j<NV;j++)if(j!=i&&s->has[j]&&((s->rows[j].m>>i)&1))
                s->rows[j]=af_x(s->rows[j],f);return 1;}}
    return(f.c==0);}

static AF g2_r(const G2*s,AF f){
    for(int i=NV-1;i>=0;i--)if(((f.m>>i)&1)&&s->has[i])f=af_x(f,s->rows[i]);return f;}

static int rS0[3],rS1[3],rs0[2],rs1[2],ss0,ss1;
static uint32_t KN[64],IVN[8],s1c[8],s2c[8],W1p[57],W2p[57];

static int SR(int k){int r=(int)rint((double)k*N/32.0);return r<1?1:r;}
static inline uint32_t ror_n(uint32_t x,int k){k%=N;return((x>>k)|(x<<(N-k)))&MASK;}
static inline uint32_t fn_S0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static inline uint32_t fn_S1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static inline uint32_t fn_s0(uint32_t x){return ror_n(x,rs0[0])^ror_n(x,rs0[1])^((x>>ss0)&MASK);}
static inline uint32_t fn_s1(uint32_t x){return ror_n(x,rs1[0])^ror_n(x,rs1[1])^((x>>ss1)&MASK);}
static inline uint32_t fn_Ch(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&MASK;}
static inline uint32_t fn_Maj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&MASK;}

static void precompute(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&MASK;
    for(int i=16;i<57;i++)W[i]=(fn_s1(W[i-2])+W[i-7]+fn_s0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+fn_S1(e)+fn_Ch(e,f,g)+KN[i]+W[i])&MASK,T2=(fn_S0(a)+fn_Maj(a,b,c))&MASK;
        h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;}

static void bf_round(uint32_t s[8],uint32_t k,uint32_t w){
    uint32_t T1=(s[7]+fn_S1(s[4])+fn_Ch(s[4],s[5],s[6])+k+w)&MASK,T2=(fn_S0(s[0])+fn_Maj(s[0],s[1],s[2]))&MASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;}

static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};

static uint64_t stat_br=0,stat_cx=0;

typedef struct {
    G2 sys;
    AF r1[8][N],r2[8][N];
    AF ax[N],ay[N],az[N]; int ac;
    AF ch[N],maj[N],t1[N],t2[N],w[N];
} ST;

#define MAXPOOL (1<<20)
static ST*PA,*PB;

static void aS0(AF o[N],const AF a[N]){for(int i=0;i<N;i++)o[i]=af_x(af_x(a[(i+rS0[0])%N],a[(i+rS0[1])%N]),a[(i+rS0[2])%N]);}
static void aS1(AF o[N],const AF e[N]){for(int i=0;i<N;i++)o[i]=af_x(af_x(e[(i+rS1[0])%N],e[(i+rS1[1])%N]),e[(i+rS1[2])%N]);}

/* 3-mode pool addition */
static int p_add(int n){
    for(int bit=0;bit<N;bit++){int no=0;
        for(int i=0;i<n&&no<MAXPOOL-3;i++){
            AF xf=g2_r(&PA[i].sys,PA[i].ax[bit]),yf=g2_r(&PA[i].sys,PA[i].ay[bit]);
            int cin=PA[i].ac,xc=af_ic(xf),yc=af_ic(yf);
            if(xc&&yc){int xv=af_cv(xf),yv=af_cv(yf);PB[no]=PA[i];
                PB[no].az[bit]=af_c(xv^yv^cin);PB[no].ac=(xv&yv)|(xv&cin)|(yv&cin);no++;continue;}
            {PB[no]=PA[i];int ok=1;
              if(!xc)ok=g2_add(&PB[no].sys,xf);else if(af_cv(xf))ok=0;
              if(ok){AF yr=g2_r(&PB[no].sys,PA[i].ay[bit]);
                if(!af_ic(yr))ok=g2_add(&PB[no].sys,yr);else if(af_cv(yr))ok=0;}
              if(ok){stat_br++;PB[no].az[bit]=af_c(cin);PB[no].ac=0;no++;}else stat_cx++;}
            {PB[no]=PA[i];AF d=af_x(xf,yf);d.c^=1;
              int ok=af_ic(d)?(af_cv(d)==0):g2_add(&PB[no].sys,d);
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
            AF ef=g2_r(&PA[i].sys,PA[i].ax[bit]),ff=PA[i].ay[bit];
            AF gf=m2?PA[i].r2[6][bit]:PA[i].r1[6][bit];
            if(af_ic(ef)){PB[no]=PA[i];PB[no].az[bit]=af_cv(ef)?g2_r(&PB[no].sys,ff):g2_r(&PB[no].sys,gf);no++;}
            else{PB[no]=PA[i];if(g2_add(&PB[no].sys,ef)){stat_br++;PB[no].az[bit]=g2_r(&PB[no].sys,gf);no++;}else stat_cx++;
                 PB[no]=PA[i];{AF c=ef;c.c^=1;if(g2_add(&PB[no].sys,c)){stat_br++;PB[no].az[bit]=g2_r(&PB[no].sys,ff);no++;}else stat_cx++;}}}
        ST*t=PA;PA=PB;PB=t;n=no;}return n;}

/* Pool Maj */
static int p_maj(int n,int m2){
    for(int bit=0;bit<N;bit++){int no=0;
        for(int i=0;i<n&&no<MAXPOOL-4;i++){
            AF af=g2_r(&PA[i].sys,PA[i].ax[bit]),bf=g2_r(&PA[i].sys,PA[i].ay[bit]);
            AF cf=g2_r(&PA[i].sys,m2?PA[i].r2[2][bit]:PA[i].r1[2][bit]);
            int ac=af_ic(af),bc=af_ic(bf),cc=af_ic(cf);
            if(ac&&bc&&cc){PB[no]=PA[i];int av=af_cv(af),bv=af_cv(bf),cv=af_cv(cf);
                PB[no].az[bit]=af_c((av&bv)^(av&cv)^(bv&cv));no++;}
            else if(bc&&cc){int bv=af_cv(bf),cv=af_cv(cf);PB[no]=PA[i];
                PB[no].az[bit]=(bv==cv)?af_c(bv):af;no++;}
            else if(ac&&cc){int av=af_cv(af),cv=af_cv(cf);PB[no]=PA[i];
                PB[no].az[bit]=(av==cv)?af_c(av):bf;no++;}
            else if(ac&&bc){int av=af_cv(af),bv=af_cv(bf);PB[no]=PA[i];
                PB[no].az[bit]=(av==bv)?af_c(av):cf;no++;}
            else{for(int av=0;av<=1;av++){if(no>=MAXPOOL)break;PB[no]=PA[i];int ok=1;
                if(!ac){AF c=af;c.c^=av;ok=g2_add(&PB[no].sys,c);}else if(af_cv(af)!=av)ok=0;
                if(!ok){stat_cx++;continue;}stat_br++;
                AF br=g2_r(&PB[no].sys,PA[i].ay[bit]),cr=g2_r(&PB[no].sys,m2?PA[i].r2[2][bit]:PA[i].r1[2][bit]);
                int brc=af_ic(br),crc=af_ic(cr);
                if(brc&&crc){int bv=af_cv(br),cv=af_cv(cr);PB[no].az[bit]=af_c((av&bv)^(av&cv)^(bv&cv));no++;}
                else if(brc){PB[no].az[bit]=(af_cv(br)==av)?af_c(av):cr;no++;}
                else if(crc){PB[no].az[bit]=(af_cv(cr)==av)?af_c(av):br;no++;}
                else{ST sv=PB[no];int ad=0;for(int bv=0;bv<=1&&no<MAXPOOL;bv++){
                    if(ad)PB[no]=sv;AF bc2=br;bc2.c^=bv;
                    if(!g2_add(&PB[no].sys,bc2)){stat_cx++;continue;}stat_br++;
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

static uint32_t cas_off(const uint32_t s1[8],const uint32_t s2[8],int rr){
    uint32_t r1=(s1[7]+fn_S1(s1[4])+fn_Ch(s1[4],s1[5],s1[6])+KN[rr])&MASK;
    uint32_t r2=(s2[7]+fn_S1(s2[4])+fn_Ch(s2[4],s2[5],s2[6])+KN[rr])&MASK;
    uint32_t T21=(fn_S0(s1[0])+fn_Maj(s1[0],s1[1],s1[2]))&MASK;
    uint32_t T22=(fn_S0(s2[0])+fn_Maj(s2[0],s2[1],s2[2]))&MASK;
    return(r1-r2+T21-T22)&MASK;}

static void sw1(const uint32_t w[4],uint32_t o[7]){o[0]=w[0];o[1]=w[1];o[2]=w[2];o[3]=w[3];
    o[4]=(fn_s1(w[2])+W1p[54]+fn_s0(W1p[46])+W1p[45])&MASK;
    o[5]=(fn_s1(w[3])+W1p[55]+fn_s0(W1p[47])+W1p[46])&MASK;
    o[6]=(fn_s1(o[4])+W1p[56]+fn_s0(W1p[48])+W1p[47])&MASK;}
static void sw2(const uint32_t w[4],uint32_t o[7]){o[0]=w[0];o[1]=w[1];o[2]=w[2];o[3]=w[3];
    o[4]=(fn_s1(w[2])+W2p[54]+fn_s0(W2p[46])+W2p[45])&MASK;
    o[5]=(fn_s1(w[3])+W2p[55]+fn_s0(W2p[47])+W2p[46])&MASK;
    o[6]=(fn_s1(o[4])+W2p[56]+fn_s0(W2p[48])+W2p[47])&MASK;}

static int exw1(const ST*s,uint32_t w[4]){
    for(int d=0;d<4;d++){w[d]=0;for(int b=0;b<N;b++){
        AF f=g2_r(&s->sys,af_v(d*N+b));if(!af_ic(f))return 0;w[d]|=(af_cv(f)<<b);}}return 1;}

int main(void){
    setbuf(stdout,NULL);struct timespec ts,te;clock_gettime(CLOCK_MONOTONIC,&ts);
    rS0[0]=SR(2);rS0[1]=SR(13);rS0[2]=SR(22);rS1[0]=SR(6);rS1[1]=SR(11);rS1[2]=SR(25);
    rs0[0]=SR(7);rs0[1]=SR(18);ss0=SR(3);rs1[0]=SR(17);rs1[1]=SR(19);ss1=SR(10);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;
    uint32_t M1[16],M2[16];for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
    M1[0]=0;M2[0]=MSB;M2[9]=MASK^MSB;
    precompute(M1,s1c,W1p);precompute(M2,s2c,W2p);

    printf("=== FACE Solver: Frontier Automaton via Carry Elimination ===\n");
    printf("N=%d, %d free variables (bits of W1[57..60])\n",N,NV);
    printf("MSB kernel, M[0]=0x0, fill=0xf\n");
    printf("State56 m1: %x %x %x %x %x %x %x %x\n",s1c[0],s1c[1],s1c[2],s1c[3],s1c[4],s1c[5],s1c[6],s1c[7]);
    printf("State56 m2: %x %x %x %x %x %x %x %x\n\n",s2c[0],s2c[1],s2c[2],s2c[3],s2c[4],s2c[5],s2c[6],s2c[7]);

    /* Brute force */
    printf("--- Brute force ---\n");
    int bfn=0;uint32_t bfs[256][4];
    for(uint32_t x=0;x<(1U<<NV);x++){
        uint32_t w1[4]={x&MASK,(x>>N)&MASK,(x>>(2*N))&MASK,(x>>(3*N))&MASK};
        uint32_t sa[8],sb[8];memcpy(sa,s1c,32);memcpy(sb,s2c,32);
        uint32_t W1f[7],W2f[7];sw1(w1,W1f);
        for(int r=0;r<4;r++){uint32_t o=cas_off(sa,sb,57+r);W2f[r]=(W1f[r]+o)&MASK;
            bf_round(sa,KN[57+r],W1f[r]);bf_round(sb,KN[57+r],W2f[r]);}
        sw2(W2f,W2f);for(int r=4;r<7;r++){bf_round(sa,KN[57+r],W1f[r]);bf_round(sb,KN[57+r],W2f[r]);}
        int ok=1;for(int r=0;r<8;r++)if(sa[r]!=sb[r]){ok=0;break;}
        if(ok&&bfn<256){memcpy(bfs[bfn],w1,16);bfn++;}}
    printf("Brute force: %d collisions in %d evals\n\n",bfn,1<<NV);

    printf("--- FACE solver (3-mode branching, cascade W2, a-constraint) ---\n\n");
    PA=calloc(MAXPOOL,sizeof(ST));PB=calloc(MAXPOOL,sizeof(ST));
    if(!PA||!PB){printf("OOM\n");return 1;}
    int sn=1;g2_init(&PA[0].sys);
    for(int r=0;r<8;r++)for(int b=0;b<N;b++){
        PA[0].r1[r][b]=af_c((s1c[r]>>b)&1);PA[0].r2[r][b]=af_c((s2c[r]>>b)&1);}

    for(int rnd=0;rnd<7;rnd++){
        int rr=57+rnd,is_free=(rnd<4);

        /* Set W1 */
        if(is_free){for(int i=0;i<sn;i++)for(int b=0;b<N;b++)PA[i].w[b]=af_v(rnd*N+b);}
        else{for(int i=0;i<sn;i++){uint32_t ww[4]={0};
            for(int d=0;d<4;d++)for(int b=0;b<N;b++){AF f=g2_r(&PA[i].sys,af_v(d*N+b));
                if(af_ic(f))ww[d]|=(af_cv(f)<<b);}
            uint32_t ws;
            if(rr==61)ws=(fn_s1(ww[2])+W1p[54]+fn_s0(W1p[46])+W1p[45])&MASK;
            else if(rr==62)ws=(fn_s1(ww[3])+W1p[55]+fn_s0(W1p[47])+W1p[46])&MASK;
            else{uint32_t w61=(fn_s1(ww[2])+W1p[54]+fn_s0(W1p[46])+W1p[45])&MASK;
                 ws=(fn_s1(w61)+W1p[56]+fn_s0(W1p[48])+W1p[47])&MASK;}
            for(int b=0;b<N;b++)PA[i].w[b]=af_c((ws>>b)&1);}}

        /* msg1 round */
        sn=do_rnd(sn,rnd,0);

        /* Compute W2 via cascade (concrete per state) */
        for(int i=0;i<sn;i++){
            uint32_t ww1[4]={0};
            for(int d=0;d<4;d++)for(int b=0;b<N;b++){
                AF f=g2_r(&PA[i].sys,af_v(d*N+b));
                if(af_ic(f))ww1[d]|=(af_cv(f)<<b);}

            /* Replay previous rounds to get pre-round state for cascade */
            uint32_t ms1[8],ms2[8];memcpy(ms1,s1c,32);memcpy(ms2,s2c,32);
            uint32_t W1r[7],W2r[7];sw1(ww1,W1r);
            for(int pr=0;pr<rnd;pr++){
                uint32_t o=cas_off(ms1,ms2,57+pr);W2r[pr]=(W1r[pr]+o)&MASK;
                bf_round(ms1,KN[57+pr],W1r[pr]);bf_round(ms2,KN[57+pr],W2r[pr]);}

            uint32_t w2val;
            if(is_free){
                uint32_t o=cas_off(ms1,ms2,rr);w2val=(W1r[rnd]+o)&MASK;
            } else {
                /* For schedule rounds: compute W2 from W2[57..60] */
                for(int pr=rnd;pr<4;pr++){
                    uint32_t o=cas_off(ms1,ms2,57+pr);W2r[pr]=(W1r[pr]+o)&MASK;
                    bf_round(ms1,KN[57+pr],W1r[pr]);bf_round(ms2,KN[57+pr],W2r[pr]);}
                sw2(W2r,W2r);w2val=W2r[rnd];
            }
            for(int b=0;b<N;b++)PA[i].w[b]=af_c((w2val>>b)&1);
        }

        /* msg2 round */
        sn=do_rnd(sn,rnd,1);

        /* Cascade constraint: register 'a' must match */
        {int no=0;
        for(int i=0;i<sn;i++){PB[no]=PA[i];int ok=1;
            for(int b=0;b<N&&ok;b++){AF d=af_x(PA[i].r1[0][b],PA[i].r2[0][b]);
                AF rd=g2_r(&PB[no].sys,d);if(af_ic(rd)){if(af_cv(rd))ok=0;}
                else{if(!g2_add(&PB[no].sys,rd))ok=0;}}
            if(ok)no++;else stat_cx++;}
        ST*t=PA;PA=PB;PB=t;sn=no;}

        printf("  Round %d: %d states (branches=%llu, contradictions=%llu)\n",
               rr,sn,(unsigned long long)stat_br,(unsigned long long)stat_cx);
        if(sn==0){printf("  DEAD\n");break;}
    }

    /* Final prune: all 8 registers */
    if(sn>0){printf("\nFinal collision prune...\n");int no=0;
        for(int i=0;i<sn;i++){PB[no]=PA[i];int ok=1;
            for(int r=0;r<8&&ok;r++)for(int b=0;b<N&&ok;b++){
                AF d=af_x(PA[i].r1[r][b],PA[i].r2[r][b]);AF rd=g2_r(&PB[no].sys,d);
                if(af_ic(rd)){if(af_cv(rd))ok=0;}else{if(!g2_add(&PB[no].sys,rd))ok=0;}}
            if(ok)no++;}
        ST*t=PA;PA=PB;PB=t;sn=no;printf("After prune: %d\n",sn);}

    /* Verify */
    printf("\n--- Verification ---\n");int nv=0,nm=0;
    for(int i=0;i<sn;i++){uint32_t w1[4];
        if(!exw1(&PA[i],w1)){printf("  State %d: underdetermined\n",i);continue;}
        uint32_t sa[8],sb[8];memcpy(sa,s1c,32);memcpy(sb,s2c,32);
        uint32_t W1r[7],W2r[7];sw1(w1,W1r);
        for(int r=0;r<4;r++){uint32_t o=cas_off(sa,sb,57+r);W2r[r]=(W1r[r]+o)&MASK;
            bf_round(sa,KN[57+r],W1r[r]);bf_round(sb,KN[57+r],W2r[r]);}
        sw2(W2r,W2r);for(int r=4;r<7;r++){bf_round(sa,KN[57+r],W1r[r]);bf_round(sb,KN[57+r],W2r[r]);}
        int ok=1;for(int r=0;r<8;r++)if(sa[r]!=sb[r]){ok=0;break;}
        if(ok){nv++;for(int j=0;j<bfn;j++)if(!memcmp(w1,bfs[j],16)){nm++;break;}}
        if(i<10)printf("  W1=[%x,%x,%x,%x] %s\n",w1[0],w1[1],w1[2],w1[3],ok?"VERIFIED":"BUG");}

    clock_gettime(CLOCK_MONOTONIC,&te);
    double el=(te.tv_sec-ts.tv_sec)+(te.tv_nsec-ts.tv_nsec)/1e9;

    printf("\n========== FACE Solver Results ==========\n");
    printf("Brute force:             %d collisions (in %d = 2^%d evals)\n",bfn,1<<NV,NV);
    printf("FACE solver:             %d states\n",sn);
    printf("Verified collisions:     %d\n",nv);
    printf("Match brute force:       %d/%d\n",nm,bfn);
    printf("\nBranch evaluations:      %llu\n",(unsigned long long)stat_br);
    printf("Contradictions detected: %llu\n",(unsigned long long)stat_cx);
    printf("Solutions found:         %d\n",nv);
    if(nv>0)printf("Evals per collision:     %.1f\n",(double)stat_br/nv);
    printf("Brute force evals:       %d\n",1<<NV);
    if(stat_br>0)printf("Speedup vs brute force:  %.1fx\n",(double)(1<<NV)/stat_br);
    printf("Time: %.3f s\n",el);
    if(nv==bfn)printf("\n*** ALL %d COLLISIONS FOUND AND VERIFIED ***\n",bfn);
    else printf("\n*** MISSING %d COLLISIONS (%d/%d) ***\n",bfn-nv,nv,bfn);
    free(PA);free(PB);return 0;
}
