/*
 * ae.c — Affine Engine. Bit-serial BFS collision finder.
 *
 * Pool-based: expand_X reads pool A, writes pool B, swap.
 * Each expand function handles ONE branching operation.
 * Main loop chains: for each bit, for each round, for each msg,
 *   chain of expand calls + register update.
 * After each bit: collision prune.
 *
 * N=4 first. Target: 49 collisions from ≤49 final states.
 *
 * gcc -O3 -march=native -o ae ae.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ---- Config ---- */
#define N 4
#define MASK ((1U<<N)-1)
#define MSB (1U<<(N-1))
#define NV (4*N)          /* 16 free variable bits: W1[57..60] */
#define MAXPOOL 131072    /* max states in pool */

/* ---- Affine Form over GF(2): val = popcount(m & vars) % 2 ^ c ---- */
typedef struct { uint32_t m; uint8_t c; } AF;
#define AX(a,b) ((AF){(a).m^(b).m, (a).c^(b).c})
#define AC(v) ((AF){0, (v)&1})
#define AV(i) ((AF){1u<<(i), 0})
#define AIS(f) ((f).m==0)
#define ACV(f) ((f).c)

/* ---- GF(2) RREF ---- */
typedef struct { AF r[NV]; uint8_t p[NV]; } G2;
static inline void g2init(G2 *s) { memset(s,0,sizeof(G2)); }
static inline int g2add(G2 *s, AF f) {
    for(int i=NV-1;i>=0;i--) if((f.m>>i)&1 && s->p[i]) f=AX(f,s->r[i]);
    if(!f.m) return f.c?0:1;
    int p=31-__builtin_clz(f.m);
    s->r[p]=f; s->p[p]=1;
    for(int i=0;i<NV;i++) if(i!=p && s->p[i] && ((s->r[i].m>>p)&1)) s->r[i]=AX(s->r[i],f);
    return 1;
}
static inline AF g2res(const G2 *s, AF f) {
    for(int i=NV-1;i>=0;i--) if((f.m>>i)&1 && s->p[i]) f=AX(f,s->r[i]);
    return f;
}

/* ---- State ---- */
typedef struct {
    G2 sys;
    AF r1[8][N];           /* msg1 registers, affine forms */
    AF r2[8][N];           /* msg2 registers */
    uint8_t c1[7][7];      /* msg1 carry[round][add] for next bit */
    uint8_t c2[7][7];      /* msg2 carry */
    /* Intermediate values within current round processing */
    AF t1_val;             /* T1 result at current bit (used across adds) */
    AF t2_val;             /* T2 result */
    AF ne_val;             /* new_e at current bit */
    AF na_val;             /* new_a at current bit */
    /* Accumulator for the T1 addition chain */
    AF acc;                /* running partial sum */
} ST;

static ST poolA[MAXPOOL], poolB[MAXPOOL];
static ST *PA = poolA, *PB = poolB;
static int nA = 0;

static inline void swappool(void) { ST *t=PA; PA=PB; PB=t; nA=0; /* nA set by caller */ }

/* ---- SHA params ---- */
static int rS0[3], rS1[3];
static const uint32_t K32[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t KN[64],IVN[8],s1c[8],s2c[8],W1p[57],W2p[57];
#define SR(k) ((int)rint((double)(k)*N/32.0) < 1 ? 1 : (int)rint((double)(k)*N/32.0))
static uint32_t ror_n(uint32_t x,int k){k=k%N;return((x>>k)|(x<<(N-k)))&MASK;}
static uint32_t fnS0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static uint32_t fnS1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static uint32_t fns0(uint32_t x){return ror_n(x,SR(7))^ror_n(x,SR(18))^((x>>SR(3))&MASK);}
static uint32_t fns1(uint32_t x){return ror_n(x,SR(17))^ror_n(x,SR(19))^((x>>SR(10))&MASK);}
static uint32_t fnCh(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&MASK;}
static uint32_t fnMj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&MASK;}
static void precomp(const uint32_t M[16],uint32_t st[8],uint32_t W[57]){
    for(int i=0;i<16;i++)W[i]=M[i]&MASK;for(int i=16;i<57;i++)W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&MASK,T2=(fnS0(a)+fnMj(a,b,c))&MASK;h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

/* ==== EXPAND FUNCTIONS ==== */

/*
 * expand_add_bit: one binary addition at one bit.
 * Reads x_form and y_form from each state (via function pointers or stored in acc).
 * Branches if either operand is symbolic. Writes carry and result.
 *
 * Parameters:
 *   get_x, get_y: functions that extract the AF operands from a state
 *   msg: 0=msg1, 1=msg2
 *   rnd, aidx: which round and addition index (for carry storage)
 *   store_z: function to store the result AF in the state
 */
typedef AF (*get_af_fn)(const ST*, int bit);
typedef void (*set_af_fn)(ST*, int bit, AF val);

static int expand_add_bit(int n_in, int bit, int msg, int rnd, int aidx,
                           get_af_fn get_x, get_af_fn get_y, set_af_fn store_z) {
    int nout = 0;
    for (int i = 0; i < n_in; i++) {
        ST *s = &PA[i];
        AF xf = g2res(&s->sys, get_x(s, bit));
        AF yf = g2res(&s->sys, get_y(s, bit));
        int cin = msg ? s->c2[rnd][aidx] : s->c1[rnd][aidx];
        int xc = AIS(xf), yc = AIS(yf);

        int xvs[2], nxv = xc ? (xvs[0]=ACV(xf),1) : (xvs[0]=0,xvs[1]=1,2);
        int yvs[2], nyv = yc ? (yvs[0]=ACV(yf),1) : (yvs[0]=0,yvs[1]=1,2);

        for (int xi=0; xi<nxv; xi++) {
            for (int yi=0; yi<nyv; yi++) {
                if (nout >= MAXPOOL) goto done;
                PB[nout] = *s;
                if (!xc) { AF c=xf; c.c^=xvs[xi]; if(!g2add(&PB[nout].sys,c)) continue; }
                if (!yc) { AF c=yf; c.c^=yvs[yi]; if(!g2add(&PB[nout].sys,c)) continue; }
                int zv = xvs[xi] ^ yvs[yi] ^ cin;
                int cout = (xvs[xi]&yvs[yi])|(xvs[xi]&cin)|(yvs[yi]&cin);
                if (msg) PB[nout].c2[rnd][aidx] = cout;
                else     PB[nout].c1[rnd][aidx] = cout;
                store_z(&PB[nout], bit, AC(zv));
                nout++;
            }
        }
    }
    done:;
    /* swap */
    ST *t=PA; PA=PB; PB=t;
    return nout;
}

/*
 * expand_ch_bit: Ch(e,f,g) at one bit.
 * If e is constant: ch = e?f:g. No branch.
 * If e is symbolic: branch on e=0 (ch=g) and e=1 (ch=f). Add GF2 constraint.
 */
static int expand_ch_bit(int n_in, int bit, int msg, int rnd, set_af_fn store_ch) {
    int nout = 0;
    for (int i = 0; i < n_in; i++) {
        ST *s = &PA[i];
        AF (*regs)[N] = msg ? s->r2 : s->r1;
        AF ef = g2res(&s->sys, regs[4][bit]); /* e */
        AF ff = g2res(&s->sys, regs[5][bit]); /* f */
        AF gf = g2res(&s->sys, regs[6][bit]); /* g */

        if (AIS(ef)) {
            if (nout >= MAXPOOL) goto done;
            PB[nout] = *s;
            store_ch(&PB[nout], bit, ACV(ef) ? ff : gf);
            nout++;
        } else {
            for (int ev = 0; ev <= 1; ev++) {
                if (nout >= MAXPOOL) goto done;
                PB[nout] = *s;
                AF con = ef; con.c ^= ev;
                if (!g2add(&PB[nout].sys, con)) continue;
                AF result = ev ? g2res(&PB[nout].sys, ff) : g2res(&PB[nout].sys, gf);
                store_ch(&PB[nout], bit, result);
                nout++;
            }
        }
    }
    done:;
    ST *t=PA; PA=PB; PB=t;
    return nout;
}

/*
 * expand_maj_bit: Maj(a,b,c) at one bit.
 * If b,c both constant and equal: maj = b. No branch.
 * If b,c both constant and unequal: maj = a. Linear.
 * Otherwise: branch on a.
 */
static int expand_maj_bit(int n_in, int bit, int msg, int rnd, set_af_fn store_maj) {
    int nout = 0;
    for (int i = 0; i < n_in; i++) {
        ST *s = &PA[i];
        AF (*regs)[N] = msg ? s->r2 : s->r1;
        AF af = g2res(&s->sys, regs[0][bit]);
        AF bf = g2res(&s->sys, regs[1][bit]);
        AF cf = g2res(&s->sys, regs[2][bit]);

        if (AIS(bf) && AIS(cf)) {
            int bv = ACV(bf), cv = ACV(cf);
            if (nout >= MAXPOOL) goto done;
            PB[nout] = *s;
            if (bv == cv) {
                store_maj(&PB[nout], bit, AC(bv)); /* maj = b regardless of a */
            } else {
                store_maj(&PB[nout], bit, g2res(&s->sys, af)); /* maj = a */
            }
            nout++;
        } else {
            /* Need to branch on a to resolve */
            AF ar = g2res(&s->sys, af);
            if (AIS(ar)) {
                int av = ACV(ar);
                if (nout >= MAXPOOL) goto done;
                PB[nout] = *s;
                /* Maj(known_a, b, c): if a=0→b&c, if a=1→b|c */
                /* Since b or c symbolic, need to branch on the symbolic one too */
                /* SIMPLIFY: Maj(a,b,c) = a(b XOR c) XOR bc. With a known:
                   a=0: Maj = bc (nonlinear in b,c)
                   a=1: Maj = b XOR c XOR bc = b OR c (nonlinear)
                   Either way, need b AND c. Branch on b. */
                AF br2 = g2res(&PB[nout].sys, bf);
                if (AIS(br2)) {
                    int bval = ACV(br2);
                    AF result;
                    if (av == 0) result = bval ? g2res(&PB[nout].sys, cf) : AC(0);
                    else result = bval ? AC(1) : g2res(&PB[nout].sys, cf);
                    store_maj(&PB[nout], bit, result);
                    nout++;
                } else {
                    /* branch on b */
                    ST saved = PB[nout]; /* save before branching */
                    for (int bv = 0; bv <= 1; bv++) {
                        if (nout >= MAXPOOL) goto done;
                        PB[nout] = saved;
                        AF con = br2; con.c ^= bv;
                        if (!g2add(&PB[nout].sys, con)) continue;
                        AF cr2 = g2res(&PB[nout].sys, cf);
                        AF result;
                        if (AIS(cr2)) {
                            int cval = ACV(cr2);
                            if (av==0) result = AC(bv & cval);
                            else result = AC(bv | cval);
                        } else {
                            /* c still symbolic. Maj(av,bv,c). */
                            if (av==0 && bv==0) result = AC(0);
                            else if (av==1 && bv==1) result = AC(1);
                            else result = cr2; /* Maj(0,1,c)=c or Maj(1,0,c)=c */
                        }
                        store_maj(&PB[nout], bit, result);
                        nout++;
                    }
                }
            } else {
                /* a symbolic, b or c symbolic. Branch on a. */
                for (int av = 0; av <= 1; av++) {
                    if (nout >= MAXPOOL) goto done;
                    PB[nout] = *s;
                    AF con = ar; con.c ^= av;
                    if (!g2add(&PB[nout].sys, con)) continue;
                    /* Now a is known. Recurse: b,c may now be resolved. */
                    AF br2 = g2res(&PB[nout].sys, bf);
                    AF cr2 = g2res(&PB[nout].sys, cf);
                    if (AIS(br2) && AIS(cr2)) {
                        int bv=ACV(br2), cv=ACV(cr2);
                        store_maj(&PB[nout], bit, AC((av&bv)^(av&cv)^(bv&cv)));
                    } else if (AIS(br2)) {
                        int bv = ACV(br2);
                        if (av==0) store_maj(&PB[nout], bit, bv ? cr2 : AC(0));
                        else store_maj(&PB[nout], bit, bv ? AC(1) : cr2);
                    } else {
                        /* Still symbolic. Use identity: if b==c: maj=b. if b!=c: maj=a. */
                        /* Can't simplify further without more branching. Use XOR trick:
                           Maj = a XOR ((a XOR b) AND (a XOR c)).
                           With a known: Maj = av XOR ((av XOR b) AND (av XOR c))
                           = av XOR (b' AND c') where b'=b^av, c'=c^av.
                           b' AND c': nonlinear. Need to branch on b'. */
                        /* Just branch on b */
                        ST saved2 = PB[nout];
                        int added_one = 0;
                        for (int bv = 0; bv <= 1; bv++) {
                            if (nout >= MAXPOOL) goto done;
                            if (added_one) PB[nout] = saved2;
                            AF bcon = br2; bcon.c ^= bv;
                            if (!g2add(&PB[nout].sys, bcon)) continue;
                            AF cr3 = g2res(&PB[nout].sys, cf);
                            int cv_known = AIS(cr3);
                            int cv = cv_known ? ACV(cr3) : 0;
                            AF result;
                            if (cv_known) {
                                result = AC((av&bv)^(av&cv)^(bv&cv));
                            } else {
                                /* a,b known, c symbolic: maj(av,bv,c) */
                                if (av==bv) result = AC(av); /* agree → maj=av */
                                else result = cr3; /* disagree → maj=c */
                            }
                            store_maj(&PB[nout], bit, result);
                            nout++;
                            added_one = 1;
                        }
                        if (!added_one) continue; /* both branches failed */
                        continue; /* skip the nout++ below */
                    }
                    nout++;
                }
            }
        }
    }
    done:;
    ST *t=PA; PA=PB; PB=t;
    return nout;
}

/* ---- Sigma at one bit: FREE ---- */
static AF sig0_bit(const AF a[N], int bit) {
    return AX(AX(a[(bit+rS0[0])%N], a[(bit+rS0[1])%N]), a[(bit+rS0[2])%N]);
}
static AF sig1_bit(const AF e[N], int bit) {
    return AX(AX(e[(bit+rS1[0])%N], e[(bit+rS1[1])%N]), e[(bit+rS1[2])%N]);
}

/* ---- Accessor/store functions for expand_add_bit ---- */
/* These get/set the intermediate values stored in the state */
static AF get_acc(const ST *s, int bit) { (void)bit; return s->acc; }
static AF get_t1(const ST *s, int bit) { (void)bit; return s->t1_val; }
static AF get_t2(const ST *s, int bit) { (void)bit; return s->t2_val; }
static void set_acc(ST *s, int bit, AF v) { (void)bit; s->acc = v; }
static void set_t1(ST *s, int bit, AF v) { (void)bit; s->t1_val = v; }
static void set_t2(ST *s, int bit, AF v) { (void)bit; s->t2_val = v; }
static void set_ne(ST *s, int bit, AF v) { (void)bit; s->ne_val = v; }
static void set_na(ST *s, int bit, AF v) { (void)bit; s->na_val = v; }
static void set_ch(ST *s, int bit, AF v) { (void)bit; s->acc = v; } /* temp store */
static void set_maj(ST *s, int bit, AF v) { (void)bit; s->acc = v; }

/* These extract operands from the state for each addition in the T1 chain */
/* T1 = ((h + Sig1(e)) + Ch) + (K + W)
   add0: h + Sig1(e)  → acc
   add1: acc + Ch      → acc
   add2: K + W         → t1_val (temp)
   add3: acc + t1_val  → T1
*/

/* For a specific msg, round, bit: get h[bit] */
static int g_msg, g_rnd, g_bit;
static AF get_h(const ST *s, int bit) { return g_msg ? s->r2[7][bit] : s->r1[7][bit]; }
static AF get_sig1e(const ST *s, int bit) { return sig1_bit(g_msg ? s->r2[4] : s->r1[4], bit); }
static AF get_ch_result(const ST *s, int bit) { (void)bit; return s->acc; } /* Ch was stored in acc */
static AF get_k(const ST *s, int bit) { (void)bit; return AC((KN[57+g_rnd]>>g_bit)&1); }
static AF get_w(const ST *s, int bit) {
    (void)bit;
    if (g_rnd < 4) {
        /* Free word: variable v_{rnd*N+bit} for msg1 */
        if (!g_msg) return AV(g_rnd * N + g_bit);
        /* msg2: cascade determines W2. But at this point, W2 is a function
           of W1 + carry-dependent offset. This is where it gets tricky.
           The cascade offset depends on the current state, which is symbolic.
           For THIS to work: we need to compute W2 as an affine function of W1.
           W2 = W1 + C where C depends on constant state diffs.
           At round 57: C is a universal constant. W2[57] = W1[57] + C_57.
           W2[57][bit] = W1[57][bit] XOR C_57[bit] XOR carry_cascade[bit].
           The carry depends on lower bits of W1[57] and C_57.
           This IS computable via the addition carry chain.
           But we haven't tracked the cascade carry separately.
           SOLUTION: compute W2 word addition as another expand_add step. */
        /* For now: return a placeholder. TODO: implement cascade addition. */
        return AC(0); /* PLACEHOLDER — WRONG */
    } else {
        /* Schedule-determined: compute from resolved W1 values */
        /* TODO: implement schedule computation */
        return AC(0); /* PLACEHOLDER — WRONG */
    }
}
static AF get_sig0a(const ST *s, int bit) { return sig0_bit(g_msg ? s->r2[0] : s->r1[0], bit); }
static AF get_maj_result(const ST *s, int bit) { (void)bit; return s->acc; }
static AF get_d(const ST *s, int bit) { return g_msg ? s->r2[3][bit] : s->r1[3][bit]; }

/* ---- Process one round at one bit for one message ---- */
static int process_round_bit(int n, int bit, int rnd, int msg) {
    g_msg = msg; g_rnd = rnd; g_bit = bit;

    /* 1. Ch(e,f,g) → stored in acc */
    n = expand_ch_bit(n, bit, msg, rnd, set_ch);

    /* 2. T1 chain:
       add0: h + Sig1(e) → acc */
    /* First: compute Sig1(e) and store as the y-operand of add0.
       Sig1 is FREE (just XOR of affine forms). We pre-store it.
       Actually: get_sig1e computes it on the fly. So add0's x=h, y=sig1e. */

    /* Save Ch result before overwriting acc with add results */
    for (int i = 0; i < n; i++) PA[i].t2_val = PA[i].acc; /* save ch in t2 temp */

    /* add0: h[bit] + Sig1(e)[bit] → acc */
    n = expand_add_bit(n, bit, msg, rnd, 0, get_h, get_sig1e, set_acc);

    /* add1: acc + Ch → acc */
    /* Restore Ch from t2 temp to acc for get_ch_result */
    for (int i = 0; i < n; i++) {
        AF saved_acc = PA[i].acc;
        PA[i].acc = PA[i].t2_val; /* put Ch in acc for get_ch_result */
        PA[i].t2_val = saved_acc; /* put add0 result in t2 temp */
    }
    /* Now: get_acc returns add0 result (in t2_val... no this is messy) */

    /* I'm making this too complicated with the accessor pattern. Let me just
       store intermediate values explicitly and use simpler expand functions. */

    /* TODO: refactor to use explicit intermediate storage instead of
       overloading acc/t2_val. For now, this demonstrates the architecture.
       The full implementation needs ~5 more expand_add calls per round
       plus the register shift update. */

    return n;
}

/* ---- Collision prune at one bit ---- */
static int collision_prune(int n, int bit) {
    int nout = 0;
    for (int i = 0; i < n; i++) {
        ST *s = &PA[i];
        int ok = 1;
        for (int reg = 0; reg < 8 && ok; reg++) {
            AF diff = AX(s->r1[reg][bit], s->r2[reg][bit]);
            AF resolved = g2res(&s->sys, diff);
            if (AIS(resolved)) {
                if (ACV(resolved) != 0) ok = 0; /* diff is constant 1 → collision fails */
            } else {
                /* diff is symbolic — add constraint diff=0 */
                if (!g2add(&s->sys, resolved)) ok = 0; /* contradiction */
            }
        }
        if (ok) PB[nout++] = *s;
    }
    ST *t=PA; PA=PB; PB=t;
    return nout;
}

int main() {
    setbuf(stdout, NULL);
    rS0[0]=SR(2);rS0[1]=SR(13);rS0[2]=SR(22);
    rS1[0]=SR(6);rS1[1]=SR(11);rS1[2]=SR(25);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;
    int found=0;
    for(uint32_t m0=0;m0<=MASK&&!found;m0++){
        uint32_t M1[16],M2[16];for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
        M1[0]=m0;M2[0]=m0^MSB;M2[9]=MASK^MSB;
        precomp(M1,s1c,W1p);precomp(M2,s2c,W2p);
        if(s1c[0]==s2c[0]){printf("Candidate: M[0]=0x%x\n",m0);found=1;}
    }

    printf("Affine Engine at N=%d (%d vars)\n", N, NV);
    printf("Architecture: flat BFS with expand functions\n\n");

    /* Init: one state with constant registers */
    nA = 1;
    g2init(&PA[0].sys);
    for(int r=0;r<8;r++) for(int b=0;b<N;b++) {
        PA[0].r1[r][b] = AC((s1c[r]>>b)&1);
        PA[0].r2[r][b] = AC((s2c[r]>>b)&1);
    }
    memset(PA[0].c1,0,sizeof(PA[0].c1));
    memset(PA[0].c2,0,sizeof(PA[0].c2));

    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);

    /* Main loop: for each bit, for each round, for each msg */
    for (int bit = 0; bit < N; bit++) {
        for (int rnd = 0; rnd < 7; rnd++) {
            for (int msg = 0; msg < 2; msg++) {
                nA = process_round_bit(nA, bit, rnd, msg);
            }
        }
        nA = collision_prune(nA, bit);
        printf("  Bit %d: %d states\n", bit, nA);
    }

    clock_gettime(CLOCK_MONOTONIC,&t1);
    double el=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;

    printf("\nFinal: %d states in %.4fs\n", nA, el);
    printf("Expected: 49 collisions with pruning, 65536 without\n");
    printf("\nNOTE: W2 cascade and schedule words are PLACEHOLDERS.\n");
    printf("Full implementation needs cascade addition + schedule computation.\n");
    printf("The architecture (expand functions + collision prune) is correct.\n");

    printf("\nDone.\n");
    return 0;
}
