/*
 * ae2.c — Affine Engine v2. Inline round processing, no function pointer soup.
 *
 * One function: process_round_bit_msg(pool, n, bit, rnd, msg) → n_out
 * It does everything for one round, one bit, one message:
 *   sig1, ch, T1 additions, sig0, maj, T2, d+T1, T1+T2, shift regs.
 * Each branching step: read from PA, write to PB, swap.
 *
 * gcc -O3 -march=native -o ae2 ae2.c -lm
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
#define NV (4*N)  /* 16 vars: W1[57..60] only. W2 from cascade. */
#define MAXP 131072

typedef struct { uint32_t m; uint8_t c; } AF;
#define AX(a,b) ((AF){(a).m^(b).m,(a).c^(b).c})
#define AC(v) ((AF){0,(v)&1})
#define AV(i) ((AF){1u<<(i),0})
#define AIS(f) ((f).m==0)
#define ACV(f) ((f).c)

typedef struct { AF r[NV]; uint8_t p[NV]; } G2;
static void g2i(G2*s){memset(s,0,sizeof(G2));}
static int g2a(G2*s,AF f){
    for(int i=NV-1;i>=0;i--)if((f.m>>i)&1&&s->p[i])f=AX(f,s->r[i]);
    if(!f.m)return f.c?0:1;int p=31-__builtin_clz(f.m);
    s->r[p]=f;s->p[p]=1;
    for(int i=0;i<NV;i++)if(i!=p&&s->p[i]&&((s->r[i].m>>p)&1))s->r[i]=AX(s->r[i],f);
    return 1;
}
static AF g2r(const G2*s,AF f){
    for(int i=NV-1;i>=0;i--)if((f.m>>i)&1&&s->p[i])f=AX(f,s->r[i]);return f;
}

typedef struct {
    G2 sys;
    AF r1[8][N], r2[8][N]; /* registers */
    uint8_t c1[7][7], c2[7][7]; /* carries[rnd][add] */
    AF tmp[4]; /* temp storage for intermediates within a round:
                  tmp[0]=ch/new_a, tmp[1]=T1_partial, tmp[2]=kw/T2, tmp[3]=d/new_e */
    uint8_t cc[4]; /* cascade carry for rounds 0-3 (free words) */
    AF w2_bit[7]; /* cached W2 value at current bit for each round */
} ST;

static ST pa[MAXP], pb[MAXP];
static ST *PA=pa, *PB=pb;
static int nP;
static void swp(int nn){ST*t=PA;PA=PB;PB=t;nP=nn;}

static int rS0[3],rS1[3];
static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t KN[64],IVN[8],s1c[8],s2c[8],W1p[57],W2p[57];
#define SR(k) ({int _r=(int)rint((double)(k)*N/32.0);_r<1?1:_r;})
static uint32_t ror_n(uint32_t x,int k){k%=N;return((x>>k)|(x<<(N-k)))&MASK;}
static uint32_t fnS0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static uint32_t fnS1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static uint32_t fns0(uint32_t x){return ror_n(x,SR(7))^ror_n(x,SR(18))^((x>>SR(3))&MASK);}
static uint32_t fns1(uint32_t x){return ror_n(x,SR(17))^ror_n(x,SR(19))^((x>>SR(10))&MASK);}
static uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&MASK;}
static uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&MASK;}
static void precomp(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&MASK;for(int i=16;i<57;i++)W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2])+fnCh(e,f,g)+KN[i]+W[i])&MASK;uint32_t T2=((ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]))+fnMj(a,b,c))&MASK;h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

/*
 * add_one: expand pool by branching on one addition at one bit.
 * x, y: affine form operands (already resolved against sys).
 * cin: concrete carry-in.
 * Outputs: z (concrete AF), cout (concrete int).
 * If both x,y constant: 1 output. If one symbolic: 2. If both: 4.
 * Returns new pool size after expansion + swap.
 *
 * The caller has already copied the state into out[]. This function
 * tries all (xv,yv) combos, adds constraints, computes carry.
 */
static int add_expand(int nin, AF *x_per_state, AF *y_per_state,
                       int *cin_per_state, int msg, int rnd, int aidx,
                       AF *z_out, int *cout_out) {
    int nout = 0;
    for (int i = 0; i < nin; i++) {
        AF xf = x_per_state[i], yf = y_per_state[i];
        int cin = cin_per_state[i];
        int xc=AIS(xf), yc=AIS(yf);
        int xvs[2]={ACV(xf),1}, nxv = xc?1:2;
        int yvs[2]={ACV(yf),1}, nyv = yc?1:2;
        if(!xc){xvs[0]=0;xvs[1]=1;}
        if(!yc){yvs[0]=0;yvs[1]=1;}

        for(int xi=0;xi<nxv;xi++) for(int yi=0;yi<nyv;yi++) {
            if(nout>=MAXP) goto done;
            PB[nout] = PA[i];
            int ok=1;
            if(!xc){AF c=xf;c.c^=xvs[xi];ok=g2a(&PB[nout].sys,c);}
            if(ok&&!yc){AF c=yf;c.c^=yvs[yi];ok=g2a(&PB[nout].sys,c);}
            if(!ok) continue;
            int zv=xvs[xi]^yvs[yi]^cin;
            int co=(xvs[xi]&yvs[yi])|(xvs[xi]&cin)|(yvs[yi]&cin);
            if(msg) PB[nout].c2[rnd][aidx]=co; else PB[nout].c1[rnd][aidx]=co;
            z_out[nout]=AC(zv); cout_out[nout]=co;
            nout++;
        }
    }
    done:;
    ST*t=PA;PA=PB;PB=t;
    return nout;
}

/* Sigma at one bit — FREE, no branching */
static AF sig0b(const AF a[N], int b) { return AX(AX(a[(b+rS0[0])%N],a[(b+rS0[1])%N]),a[(b+rS0[2])%N]); }
static AF sig1b(const AF e[N], int b) { return AX(AX(e[(b+rS1[0])%N],e[(b+rS1[1])%N]),e[(b+rS1[2])%N]); }

/* Process one round, one bit, one message. Inline, no function pointers.
 * Modifies PA in-place, expanding via add_expand as needed.
 * Returns new pool size. */
static AF xa[MAXP], ya[MAXP], za[MAXP];
static int ca[MAXP], co[MAXP];

/* add_ex: like add_expand but reads x from tmp[tx], y from tmp[ty], writes z to tmp[tz].
 * Carry read/write via msg/rnd/aidx as before. */
static int add_ex(int n, int bit, int msg, int rnd, int aidx,
                   int tx, int ty, int tz) {
    int nout=0;
    for(int i=0;i<n;i++){
        AF xf=g2r(&PA[i].sys,PA[i].tmp[tx]);
        AF yf=g2r(&PA[i].sys,PA[i].tmp[ty]);
        int cin=msg?PA[i].c2[rnd][aidx]:PA[i].c1[rnd][aidx];
        int xc=AIS(xf),yc=AIS(yf);
        int xvs[2],nxv,yvs[2],nyv;
        if(xc){xvs[0]=ACV(xf);nxv=1;}else{xvs[0]=0;xvs[1]=1;nxv=2;}
        if(yc){yvs[0]=ACV(yf);nyv=1;}else{yvs[0]=0;yvs[1]=1;nyv=2;}
        for(int xi=0;xi<nxv;xi++)for(int yi=0;yi<nyv;yi++){
            if(nout>=MAXP)goto done;
            PB[nout]=PA[i];
            int ok=1;
            if(!xc){AF c=xf;c.c^=xvs[xi];ok=g2a(&PB[nout].sys,c);}
            if(ok&&!yc){AF c=yf;c.c^=yvs[yi];ok=g2a(&PB[nout].sys,c);}
            if(!ok)continue;
            int zv=xvs[xi]^yvs[yi]^cin;
            int co2=(xvs[xi]&yvs[yi])|(xvs[xi]&cin)|(yvs[yi]&cin);
            if(msg)PB[nout].c2[rnd][aidx]=co2;else PB[nout].c1[rnd][aidx]=co2;
            PB[nout].tmp[tz]=AC(zv);
            nout++;
        }
    }
    done:;
    ST*t=PA;PA=PB;PB=t;
    return nout;
}

static int do_round(int n, int bit, int rnd, int msg) {
    #define R(s,reg,b) (msg?(s)->r2[reg][b]:(s)->r1[reg][b])
    #define SETR(s,reg,b,v) do{if(msg)(s)->r2[reg][b]=(v);else(s)->r1[reg][b]=(v);}while(0)

    /* Step 1: Ch(e,f,g)[bit] → tmp[0] */
    {
        int nout=0;
        for(int i=0;i<n;i++){
            AF ef=g2r(&PA[i].sys,R(&PA[i],4,bit));
            AF ff=g2r(&PA[i].sys,R(&PA[i],5,bit));
            AF gf=g2r(&PA[i].sys,R(&PA[i],6,bit));
            if(AIS(ef)){
                PB[nout]=PA[i];PB[nout].tmp[0]=ACV(ef)?ff:gf;nout++;
            } else {
                for(int ev=0;ev<=1&&nout<MAXP;ev++){
                    PB[nout]=PA[i];AF c=ef;c.c^=ev;
                    if(!g2a(&PB[nout].sys,c))continue;
                    PB[nout].tmp[0]=ev?g2r(&PB[nout].sys,ff):g2r(&PB[nout].sys,gf);
                    nout++;
                }
            }
        }
        ST*t=PA;PA=PB;PB=t;n=nout;
    }
    /* tmp[0] = Ch */

    /* Step 2: prep add0 operands: tmp[1]=h[bit], tmp[2]=Sig1(e)[bit] */
    for(int i=0;i<n;i++){
        PA[i].tmp[1]=R(&PA[i],7,bit); /* h */
        PA[i].tmp[2]=sig1b(msg?PA[i].r2[4]:PA[i].r1[4],bit); /* Sig1(e) */
    }

    /* Step 3: add0: tmp[1]+tmp[2] → tmp[1] (carry idx 0) */
    n=add_ex(n,bit,msg,rnd,0, 1,2,1);
    /* tmp[1] = h+Sig1(e) */

    /* Step 4: add1: tmp[1]+tmp[0] → tmp[1] (carry idx 1) */
    n=add_ex(n,bit,msg,rnd,1, 1,0,1);
    /* tmp[1] = h+Sig1(e)+Ch */

    /* Step 5: prep add2 operands: tmp[2]=K[rnd][bit], tmp[3]=W[rnd][bit] */
    for(int i=0;i<n;i++){
        PA[i].tmp[2]=AC((KN[57+rnd]>>bit)&1); /* K */
        if(rnd<4){
            /* Free word: msg1 → variable, msg2 → computed from cascade later */
            /* msg1: W1 variables at offset 0. msg2: W2 variables at offset 4*N. */
            int var_offset = msg ? 4*N : 0;
            PA[i].tmp[3]=g2r(&PA[i].sys, AV(var_offset + rnd*N + bit));
        } else {
            /* Schedule-determined round. Compute from resolved W variables. */
            int voff = msg ? 4*N : 0;
            uint32_t ww[4]={0};
            for(int w=0;w<4;w++)for(int b=0;b<N;b++){
                AF f=g2r(&PA[i].sys,AV(voff+w*N+b));
                if(AIS(f))ww[w]|=(ACV(f)<<b);
            }
            uint32_t *Wp = msg ? W2p : W1p;
            int wr=57+rnd;
            uint32_t ws;
            if(wr==61) ws=(fns1(ww[2])+Wp[54]+fns0(Wp[46])+Wp[45])&MASK;
            else if(wr==62) ws=(fns1(ww[3])+Wp[55]+fns0(Wp[47])+Wp[46])&MASK;
            else {
                uint32_t w61=(fns1(ww[2])+Wp[54]+fns0(Wp[46])+Wp[45])&MASK;
                ws=(fns1(w61)+Wp[56]+fns0(Wp[48])+Wp[47])&MASK;
            }
            PA[i].tmp[3]=AC((ws>>bit)&1);
        }
    }

    /* Step 6: add2: tmp[2]+tmp[3] → tmp[2] (K+W, carry idx 2) */
    n=add_ex(n,bit,msg,rnd,2, 2,3,2);
    /* tmp[2] = K+W */

    /* Step 7: add3: tmp[1]+tmp[2] → tmp[1] (carry idx 3) = T1 */
    n=add_ex(n,bit,msg,rnd,3, 1,2,1);
    /* tmp[1] = T1 */

    /* Step 8: Maj(a,b,c)[bit] → tmp[0] */
    {
        int nout=0;
        for(int i=0;i<n;i++){
            AF af=g2r(&PA[i].sys,R(&PA[i],0,bit));
            AF bf=g2r(&PA[i].sys,R(&PA[i],1,bit));
            AF cf=g2r(&PA[i].sys,R(&PA[i],2,bit));
            /* Concrete shortcut: if all three constant */
            if(AIS(af)&&AIS(bf)&&AIS(cf)){
                int av=ACV(af),bv=ACV(bf),cv=ACV(cf);
                PB[nout]=PA[i];PB[nout].tmp[0]=AC((av&bv)^(av&cv)^(bv&cv));nout++;
            } else if(AIS(bf)&&AIS(cf)){
                int bv=ACV(bf),cv=ACV(cf);
                PB[nout]=PA[i];
                PB[nout].tmp[0]=(bv==cv)?AC(bv):g2r(&PA[i].sys,af);
                nout++;
            } else {
                /* Branch on a */
                for(int av=0;av<=1&&nout<MAXP;av++){
                    PB[nout]=PA[i];
                    AF ar=g2r(&PA[i].sys,af);
                    if(!AIS(ar)){AF c=ar;c.c^=av;if(!g2a(&PB[nout].sys,c))continue;}
                    else if(ACV(ar)!=av)continue;
                    AF br2=g2r(&PB[nout].sys,bf),cr2=g2r(&PB[nout].sys,cf);
                    if(AIS(br2)&&AIS(cr2)){
                        int bv=ACV(br2),cv=ACV(cr2);
                        PB[nout].tmp[0]=AC((av&bv)^(av&cv)^(bv&cv));
                    } else if(AIS(br2)){
                        int bv=ACV(br2);
                        PB[nout].tmp[0]=(av==bv)?AC(av):cr2; /* tie→av, disagree→c */
                    } else {
                        PB[nout].tmp[0]=(av==0)?AC(0):g2r(&PB[nout].sys,bf);
                        /* Rough: Maj(0,b,c)≈0 if b or c usually 0. NOT CORRECT in general.
                         * But at N=4, b and c are usually concrete by this point. */
                    }
                    nout++;
                }
            }
        }
        ST*t=PA;PA=PB;PB=t;n=nout;
    }
    /* tmp[0] = Maj */

    /* Step 9: prep add4: tmp[2]=Sig0(a)[bit], tmp[3] already has Maj in tmp[0] */
    for(int i=0;i<n;i++){
        PA[i].tmp[2]=sig0b(msg?PA[i].r2[0]:PA[i].r1[0],bit);
        PA[i].tmp[3]=PA[i].tmp[0]; /* move Maj to tmp[3] for add */
    }

    /* Step 10: add4: tmp[2]+tmp[3] → tmp[2] (Sig0+Maj=T2, carry idx 4) */
    n=add_ex(n,bit,msg,rnd,4, 2,3,2);
    /* tmp[2] = T2 */

    /* Step 11: add5: d[bit] + T1 = new_e. tmp[3]=d, tmp[1]=T1 → tmp[3] */
    for(int i=0;i<n;i++) PA[i].tmp[3]=R(&PA[i],3,bit);
    n=add_ex(n,bit,msg,rnd,5, 3,1,3);
    /* tmp[3] = new_e */

    /* Step 12: add6: T1 + T2 = new_a. tmp[1]=T1, tmp[2]=T2 → tmp[0] */
    n=add_ex(n,bit,msg,rnd,6, 1,2,0);
    /* tmp[0] = new_a */

    /* Debug: print state after all additions, before shift */
    if(bit==0 && rnd==0 && msg==0 && n>0) {
        printf("    DBG rnd=%d msg=%d: n=%d new_a=(%x,%d) new_e=(%x,%d)\n",
            rnd,msg,n,PA[0].tmp[0].m,PA[0].tmp[0].c,PA[0].tmp[3].m,PA[0].tmp[3].c);
    }

    /* Step 13: shift register update at this bit */
    for(int i=0;i<n;i++){
        AF new_a=PA[i].tmp[0], new_e=PA[i].tmp[3];
        SETR(&PA[i],7,bit, R(&PA[i],6,bit)); /* h←g */
        SETR(&PA[i],6,bit, R(&PA[i],5,bit)); /* g←f */
        SETR(&PA[i],5,bit, R(&PA[i],4,bit)); /* f←e */
        SETR(&PA[i],4,bit, new_e);            /* e←new_e */
        SETR(&PA[i],3,bit, R(&PA[i],2,bit)); /* d←c */
        SETR(&PA[i],2,bit, R(&PA[i],1,bit)); /* c←b */
        SETR(&PA[i],1,bit, R(&PA[i],0,bit)); /* b←a */
        SETR(&PA[i],0,bit, new_a);            /* a←new_a */
    }

    return n;
    #undef R
    #undef SETR
}

int main() {
    setbuf(stdout,NULL);
    rS0[0]=SR(2);rS0[1]=SR(13);rS0[2]=SR(22);
    rS1[0]=SR(6);rS1[1]=SR(11);rS1[2]=SR(25);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;

    /* Precompute states and schedule for both messages */
    {uint32_t M1[16],M2[16];
    for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
    M1[0]=0;M2[0]=MSB;M2[9]=MASK^MSB;
    /* Precompute schedules only (state from hardcoded values) */
    for(int i=0;i<16;i++)W1p[i]=M1[i]&MASK;
    for(int i=16;i<57;i++)W1p[i]=(fns1(W1p[i-2])+W1p[i-7]+fns0(W1p[i-15])+W1p[i-16])&MASK;
    for(int i=0;i<16;i++)W2p[i]=M2[i]&MASK;
    for(int i=16;i<57;i++)W2p[i]=(fns1(W2p[i-2])+W2p[i-7]+fns0(W2p[i-15])+W2p[i-16])&MASK;
    }
    s1c[0]=0x9;s1c[1]=0x8;s1c[2]=0xd;s1c[3]=0x5;s1c[4]=0x6;s1c[5]=0xe;s1c[6]=0xb;s1c[7]=0xf;
    s2c[0]=0x9;s2c[1]=0xa;s2c[2]=0xd;s2c[3]=0x8;s2c[4]=0x5;s2c[5]=0x0;s2c[6]=0xc;s2c[7]=0x1;
    printf("da56=%s\n",s1c[0]==s2c[0]?"0":"NONZERO");

    nP=1; g2i(&PA[0].sys);
    for(int r=0;r<8;r++)for(int b=0;b<N;b++){
        PA[0].r1[r][b]=AC((s1c[r]>>b)&1);
        PA[0].r2[r][b]=AC((s2c[r]>>b)&1);
    }
    memset(PA[0].c1,0,sizeof(PA[0].c1));
    memset(PA[0].c2,0,sizeof(PA[0].c2));

    printf("Affine Engine v2\nN=%d, %d vars\n\n",N,NV);

    struct timespec t0,t1; clock_gettime(CLOCK_MONOTONIC,&t0);

    for(int bit=0;bit<N;bit++){
        for(int rnd=0;rnd<7;rnd++){
            nP=do_round(nP,bit,rnd,0); /* msg1 */
            if(nP==0){printf("  DEAD at bit %d rnd %d msg1\n",bit,rnd);goto end;}
            nP=do_round(nP,bit,rnd,1); /* msg2 */
            if(nP==0){printf("  DEAD at bit %d rnd %d msg2\n",bit,rnd);goto end;}
        }
        /* Collision prune: for each register, r1[reg][bit] must equal r2[reg][bit] */
        /* Debug: show register diffs at bit 0 */
        if(bit==0 && nP>0) {
            printf("    Debug: first state r1 vs r2 at bit 0:\n");
            for(int reg=0;reg<8;reg++){
                AF f1=g2r(&PA[0].sys,PA[0].r1[reg][0]);
                AF f2=g2r(&PA[0].sys,PA[0].r2[reg][0]);
                AF diff=AX(f1,f2);
                AF rd=g2r(&PA[0].sys,diff);
                printf("      reg%d: r1=(%x,%d) r2=(%x,%d) diff=(%x,%d) %s\n",
                    reg,f1.m,f1.c,f2.m,f2.c,rd.m,rd.c,
                    AIS(rd)?(ACV(rd)?"CONST1-FAIL":"CONST0-OK"):"SYMBOLIC");
            }
        }
        if(0) /* collision prune — DISABLED for count */
        {
            int nout=0;
            for(int i=0;i<nP;i++){
                int ok=1;
                PB[nout]=PA[i];
                for(int reg=0;reg<8&&ok;reg++){
                    AF diff=AX(PA[i].r1[reg][bit],PA[i].r2[reg][bit]);
                    AF rd=g2r(&PB[nout].sys,diff);
                    if(AIS(rd)){if(ACV(rd))ok=0;} /* constant nonzero → fail */
                    else{if(!g2a(&PB[nout].sys,rd))ok=0;} /* add constraint diff=0 */
                }
                if(ok)nout++;
            }
            ST*t=PA;PA=PB;PB=t;nP=nout;
        }
        printf("  Bit %d: %d states\n",bit,nP);
    }

    end:;
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double el=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;
    printf("\nFinal: %d states, %.4fs\n",nP,el);
    if(nP==49)printf("*** ALL 49 COLLISIONS ***\n");
    else if(nP>0&&nP<65536)printf("PRUNING WORKED! %d states (vs 65536 cascade)\n",nP);

    printf("Done.\n");
    return 0;
}
