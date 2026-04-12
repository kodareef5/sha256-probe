/*
 * ae3.c — Affine Engine v3. Round-serial, symbolic carry tracking.
 * One file. N=4. 16 variables. No placeholders. No approximations.
 * Target: find exactly 49 collisions.
 *
 * gcc -O3 -march=native -o ae3 ae3.c -lm
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
#define NV (8*N)       /* 32 variables: W1[57..60] + W2[57..60] × N bits.
                        * Cascade constraints link them via GF(2). */
#define MAXPOOL 2097152 /* 2M max states — need room for round 60 expansion */

/* ---- Affine Form: val = popcount(m & vars) % 2 XOR c ---- */
typedef struct { uint32_t m; uint8_t c; } AF;
static inline AF af_xor(AF a, AF b) { return (AF){a.m^b.m, (uint8_t)(a.c^b.c)}; }
static inline AF af_const(int v) { return (AF){0, (uint8_t)(v&1)}; }
static inline AF af_var(int i) { return (AF){1U<<i, 0}; }
static inline int af_is_const(AF f) { return f.m==0; }
static inline int af_val(AF f) { return f.c; } /* only valid if af_is_const */

/* ---- GF(2) RREF System ---- */
typedef struct { AF rows[NV]; uint8_t has[NV]; } G2;

static void g2_init(G2 *s) { memset(s, 0, sizeof(G2)); }

/* Add constraint f=0. Returns 1 if consistent, 0 if contradiction. */
static int g2_add(G2 *s, AF f) {
    for (int i = NV-1; i >= 0; i--)
        if ((f.m >> i) & 1 && s->has[i])
            f = af_xor(f, s->rows[i]);
    if (f.m == 0) return f.c ? 0 : 1;
    int p = 31 - __builtin_clz(f.m);
    s->rows[p] = f; s->has[p] = 1;
    for (int i = 0; i < NV; i++)
        if (i != p && s->has[i] && ((s->rows[i].m >> p) & 1))
            s->rows[i] = af_xor(s->rows[i], f);
    return 1;
}

/* Resolve f against the system. Returns simplified form. */
static AF g2_res(const G2 *s, AF f) {
    for (int i = NV-1; i >= 0; i--)
        if ((f.m >> i) & 1 && s->has[i])
            f = af_xor(f, s->rows[i]);
    return f;
}

/* Evaluate an affine form given concrete variable values. */
static int af_eval(AF f, uint32_t vars) {
    return (__builtin_popcount(f.m & vars) & 1) ^ f.c;
}

/* ---- State ---- */
typedef struct {
    G2 sys;
    AF r1[8][N]; /* msg1 registers: a=0,b=1,c=2,d=3,e=4,f=5,g=6,h=7 */
    AF r2[8][N]; /* msg2 registers */
    /* Work areas — ALL intermediates stored here so pool expansions don't lose data */
    AF ax[N], ay[N], az[N]; /* addition operands and result */
    int ac;                  /* addition carry */
    AF ch[N];   /* Ch result */
    AF sig1[N]; /* Sigma1(e) result */
    AF sig0[N]; /* Sigma0(a) result */
    AF maj[N];  /* Maj result */
    AF t1[N];   /* T1 partial/final */
    AF t2[N];   /* T2 */
    AF w[N];    /* message word for this round */
} ST;

/* Double-buffered pool */
static ST *PA, *PB;
static int nA;

/* ---- SHA-256 constants ---- */
static int rS0[3], rS1[3]; /* Sigma0, Sigma1 rotation amounts */
static uint32_t KN[64];    /* round constants truncated to N bits */
static uint32_t s1c[8], s2c[8]; /* precomputed state56 for both messages */
static uint32_t W1p[57], W2p[57]; /* precomputed schedules */

static int SR(int k) { int r = (int)rint((double)k*N/32.0); return r < 1 ? 1 : r; }

/* ---- Brute-force SHA helpers (for verification) ---- */
static uint32_t ror_n(uint32_t x, int k) { k %= N; return ((x>>k)|(x<<(N-k))) & MASK; }
static uint32_t bfS0(uint32_t a) { return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]); }
static uint32_t bfS1(uint32_t e) { return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]); }
static uint32_t bfCh(uint32_t e, uint32_t f, uint32_t g) { return ((e&f)^((~e)&g))&MASK; }
static uint32_t bfMj(uint32_t a, uint32_t b, uint32_t c) { return ((a&b)^(a&c)^(b&c))&MASK; }
static uint32_t bfs0(uint32_t x) { return ror_n(x,SR(7))^ror_n(x,SR(18))^((x>>SR(3))&MASK); }
static uint32_t bfs1(uint32_t x) { return ror_n(x,SR(17))^ror_n(x,SR(19))^((x>>SR(10))&MASK); }

static void bf_round(uint32_t s[8], uint32_t k, uint32_t w) {
    uint32_t T1 = (s[7]+bfS1(s[4])+bfCh(s[4],s[5],s[6])+k+w)&MASK;
    uint32_t T2 = (bfS0(s[0])+bfMj(s[0],s[1],s[2]))&MASK;
    s[7]=s[6];s[6]=s[5];s[5]=s[4];s[4]=(s[3]+T1)&MASK;
    s[3]=s[2];s[2]=s[1];s[1]=s[0];s[0]=(T1+T2)&MASK;
}

/* ---- Affine Sigma: FREE (XOR of rotated forms) ---- */
static void af_Sigma0(AF out[N], const AF a[N]) {
    for (int i = 0; i < N; i++)
        out[i] = af_xor(af_xor(a[(i+rS0[0])%N], a[(i+rS0[1])%N]), a[(i+rS0[2])%N]);
}
static void af_Sigma1(AF out[N], const AF e[N]) {
    for (int i = 0; i < N; i++)
        out[i] = af_xor(af_xor(e[(i+rS1[0])%N], e[(i+rS1[1])%N]), e[(i+rS1[2])%N]);
}

/* ==== PHASE 2: Symbolic N-bit addition ==== */

/*
 * af_add_word: compute z = x + y mod 2^N symbolically.
 *
 * Processes the carry chain bit by bit (0 to N-1).
 * At each bit: if both operands are constant, carry is determined.
 * If either is symbolic: BRANCH on its value, add GF2 constraint.
 *
 * Input: PA[0..n_in-1] states, each with x[N] and y[N] stored in the
 *        state's register fields (caller sets them up).
 * Output: PB[0..n_out-1] states, with z[N] written to caller-specified location.
 *
 * To avoid pointer gymnastics: pass x, y, z as arrays of AF, one per state.
 * The function reads x_arr[i*N+bit], y_arr[i*N+bit], writes z_arr[i*N+bit].
 * Carry state is tracked per-state in a local array.
 *
 * Actually: simpler to pass a function that does one addition on one state
 * and expands the pool. Then the caller calls it repeatedly.
 *
 * SIMPLEST: just implement it inline in the round function. The "addition"
 * is always between two AF[N] operands. We process N bits, branching as needed.
 *
 * For the pool expansion: at each bit, read PA, write PB, swap.
 * Each bit can expand the pool by up to 4x (2 operands × 2 values).
 * Over N=4 bits: up to 4^4 = 256x. But GF2 prunes most.
 */

/* Process one addition z=x+y for the entire pool.
 * x_off, y_off: offsets into state's register array to find the operands.
 * z_off: where to store the result.
 * But registers are AF[8][N] not flat arrays. Need different access pattern.
 *
 * Let's use a callback approach: the caller provides functions to extract
 * operands and store results. But that's what failed before.
 *
 * SIMPLEST POSSIBLE: pass AF arrays directly. The caller copies the operand
 * AFs into flat arrays before calling, and copies results back after.
 */

/* Add z = x + y for the whole pool. x and y are N-element AF arrays PER STATE.
 * x_all[i*N + bit] = x operand for state i at bit position bit.
 * Same for y_all, z_all.
 * carry_all[i] = carry-in for state i (initially 0).
 * Returns new pool size (after expansion + pruning). Pool is swapped. */
/* pool_add_word: compute az = ax + ay for all states in pool.
 * Caller sets PA[i].ax, PA[i].ay, PA[i].ac (carry=0) before calling.
 * Result written to PA[i].az. Pool may expand (branching on symbolic operands). */
static int pool_add_word(int n_in) {
    int n = n_in;
    for (int bit = 0; bit < N; bit++) {
        int nout = 0;
        for (int i = 0; i < n; i++) {
            AF xf = g2_res(&PA[i].sys, PA[i].ax[bit]);
            AF yf = g2_res(&PA[i].sys, PA[i].ay[bit]);
            int cin = PA[i].ac;
            int xc = af_is_const(xf), yc = af_is_const(yf);

            int xvs[2], nxv, yvs[2], nyv;
            if (xc) { xvs[0]=af_val(xf); nxv=1; }
            else { xvs[0]=0; xvs[1]=1; nxv=2; }
            if (yc) { yvs[0]=af_val(yf); nyv=1; }
            else { yvs[0]=0; yvs[1]=1; nyv=2; }

            for (int xi = 0; xi < nxv; xi++) {
                for (int yi = 0; yi < nyv; yi++) {
                    if (nout >= MAXPOOL) goto done_bit;
                    PB[nout] = PA[i]; /* copies ENTIRE state including ax,ay,az */
                    int ok = 1;
                    if (!xc) { AF c=xf; c.c^=xvs[xi]; ok=g2_add(&PB[nout].sys,c); }
                    if (ok && !yc) { AF c=yf; c.c^=yvs[yi]; ok=g2_add(&PB[nout].sys,c); }
                    if (!ok) continue;
                    int zv = xvs[xi] ^ yvs[yi] ^ cin;
                    int cout = (xvs[xi]&yvs[yi])|(xvs[xi]&cin)|(yvs[yi]&cin);
                    PB[nout].az[bit] = af_const(zv);
                    PB[nout].ac = cout;
                    nout++;
                }
            }
        }
        done_bit:;
        ST *tmp = PA; PA = PB; PB = tmp;
        n = nout;
    }
    return n;
}

/* ==== PHASE 3: Ch and Maj ==== */

/* pool_ch_word: compute Ch(e,f,g) for all N bits.
 * For each bit: if e is constant, ch = e?f:g (no branch).
 * If e is symbolic: branch on e, add GF2 constraint.
 * Caller sets PA[i].ax = e[N], PA[i].ay = f[N], PA[i].az used as g[N] input.
 * Result written to PA[i].az[N]. */
static int pool_ch_word(int n_in, const AF g_in[][N], int is_r2) {
    /* Process each bit independently. Each bit can branch (×2 if symbolic). */
    int n = n_in;
    for (int bit = 0; bit < N; bit++) {
        int nout = 0;
        for (int i = 0; i < n; i++) {
            AF ef = g2_res(&PA[i].sys, PA[i].ax[bit]); /* e */
            AF ff = PA[i].ay[bit]; /* f */
            AF gf = is_r2 ? PA[i].r2[6][bit] : PA[i].r1[6][bit]; /* g from registers */
            if (af_is_const(ef)) {
                PB[nout] = PA[i];
                PB[nout].az[bit] = af_val(ef) ? ff : gf;
                nout++;
            } else {
                for (int ev = 0; ev <= 1 && nout < MAXPOOL; ev++) {
                    PB[nout] = PA[i];
                    AF con = ef; con.c ^= ev;
                    if (!g2_add(&PB[nout].sys, con)) continue;
                    PB[nout].az[bit] = ev
                        ? g2_res(&PB[nout].sys, ff)
                        : g2_res(&PB[nout].sys, gf);
                    nout++;
                }
            }
        }
        ST *tmp = PA; PA = PB; PB = tmp; n = nout;
    }
    return n;
}

/* pool_maj_word: compute Maj(a,b,c) for all N bits.
 * If b,c both constant and equal → maj=b. If unequal → maj=a. No branch.
 * Otherwise branch on a (and possibly b).
 * Caller sets PA[i].ax=a, PA[i].ay=b. c read from registers.
 * Result in PA[i].az. */
static int pool_maj_word(int n_in, int is_r2) {
    int n = n_in;
    for (int bit = 0; bit < N; bit++) {
        int nout = 0;
        for (int i = 0; i < n; i++) {
            AF af = g2_res(&PA[i].sys, PA[i].ax[bit]);
            AF bf = g2_res(&PA[i].sys, PA[i].ay[bit]);
            AF cf = g2_res(&PA[i].sys, is_r2 ? PA[i].r2[2][bit] : PA[i].r1[2][bit]);

            if (af_is_const(af) && af_is_const(bf) && af_is_const(cf)) {
                int av=af_val(af), bv=af_val(bf), cv=af_val(cf);
                PB[nout] = PA[i];
                PB[nout].az[bit] = af_const((av&bv)^(av&cv)^(bv&cv));
                nout++;
            } else if (af_is_const(bf) && af_is_const(cf)) {
                int bv=af_val(bf), cv=af_val(cf);
                PB[nout] = PA[i];
                PB[nout].az[bit] = (bv==cv) ? af_const(bv) : af;
                nout++;
            } else {
                /* Branch on a */
                for (int av = 0; av <= 1 && nout < MAXPOOL; av++) {
                    PB[nout] = PA[i];
                    if (!af_is_const(af)) {
                        AF con = af; con.c ^= av;
                        if (!g2_add(&PB[nout].sys, con)) continue;
                    } else if (af_val(af) != av) continue;

                    AF br = g2_res(&PB[nout].sys, bf);
                    AF cr = g2_res(&PB[nout].sys, cf);
                    if (af_is_const(br) && af_is_const(cr)) {
                        int bv2=af_val(br), cv2=af_val(cr);
                        PB[nout].az[bit] = af_const((av&bv2)^(av&cv2)^(bv2&cv2));
                    } else if (af_is_const(br)) {
                        int bv2=af_val(br);
                        /* Maj(av,bv2,c): if av==bv2 → maj=av, else maj=c */
                        PB[nout].az[bit] = (av==bv2) ? af_const(av) : cr;
                    } else if (af_is_const(cr)) {
                        int cv2=af_val(cr);
                        PB[nout].az[bit] = (av==cv2) ? af_const(av) : br;
                    } else {
                        /* a known, b and c both symbolic. Maj(av,b,c).
                         * If av=0: maj=b&c (nonlinear). Need to branch on b. */
                        /* For N=4 POC: b and c are usually older registers (constant).
                         * If we hit this case, branch on b. */
                        ST saved = PB[nout];
                        int added = 0;
                        for (int bv2 = 0; bv2 <= 1 && nout < MAXPOOL; bv2++) {
                            if (added) PB[nout] = saved;
                            AF bcon = br; bcon.c ^= bv2;
                            if (!g2_add(&PB[nout].sys, bcon)) continue;
                            AF cr2 = g2_res(&PB[nout].sys, cf);
                            if (af_is_const(cr2)) {
                                int cv3 = af_val(cr2);
                                PB[nout].az[bit] = af_const((av&bv2)^(av&cv3)^(bv2&cv3));
                            } else {
                                PB[nout].az[bit] = (av==bv2) ? af_const(av) : cr2;
                            }
                            nout++; added = 1;
                        }
                        if (!added) continue;
                        continue; /* skip outer nout++ */
                    }
                    nout++;
                }
            }
        }
        ST *tmp = PA; PA = PB; PB = tmp; n = nout;
    }
    return n;
}

/* ==== PHASE 4: One SHA-256 round (symbolic, one message) ==== */

/* do_one_round: process one SHA-256 round for one message symbolically.
 * w[N] = message word (affine forms) for this round.
 * rnd = round index (0-6 for rounds 57-63).
 * is_r2 = 0 for msg1, 1 for msg2.
 * Modifies registers in PA[i].r1 or r2.
 * Returns new pool size. */
static int do_one_round(int n, int rnd, int is_r2) {
    #define REG(s,r) (is_r2 ? (s)->r2[r] : (s)->r1[r])

    /* 1. Compute Sigma1(e) and Sigma0(a) — FREE. Store in state. */
    for (int i = 0; i < n; i++) {
        af_Sigma1(PA[i].sig1, REG(&PA[i],4));
        af_Sigma0(PA[i].sig0, REG(&PA[i],0));
    }

    /* 2. Ch(e,f,g) → state.ch. Uses ax=e, ay=f, g from registers. */
    for (int i = 0; i < n; i++) {
        memcpy(PA[i].ax, REG(&PA[i],4), N*sizeof(AF)); /* e */
        memcpy(PA[i].ay, REG(&PA[i],5), N*sizeof(AF)); /* f */
    }
    n = pool_ch_word(n, NULL, is_r2);
    /* Save Ch result from az to ch */
    for (int i = 0; i < n; i++) memcpy(PA[i].ch, PA[i].az, N*sizeof(AF));

    /* 3. add0: h + Sig1(e) → t1 */
    for (int i = 0; i < n; i++) {
        memcpy(PA[i].ax, REG(&PA[i],7), N*sizeof(AF)); /* h */
        /* Recompute Sig1 (free, indices may have changed from Ch expansion) */
        af_Sigma1(PA[i].ay, REG(&PA[i],4));
        PA[i].ac = 0;
    }
    n = pool_add_word(n);
    for (int i = 0; i < n; i++) memcpy(PA[i].t1, PA[i].az, N*sizeof(AF));

    /* 4. add1: t1 + Ch → t1 */
    for (int i = 0; i < n; i++) {
        memcpy(PA[i].ax, PA[i].t1, N*sizeof(AF));
        memcpy(PA[i].ay, PA[i].ch, N*sizeof(AF));
        PA[i].ac = 0;
    }
    n = pool_add_word(n);
    for (int i = 0; i < n; i++) memcpy(PA[i].t1, PA[i].az, N*sizeof(AF));

    /* 5. add2: K + W → t2 (temp use of t2 for K+W result) */
    for (int i = 0; i < n; i++) {
        for (int b = 0; b < N; b++) PA[i].ax[b] = af_const((KN[57+rnd]>>b)&1);
        memcpy(PA[i].ay, PA[i].w, N*sizeof(AF)); /* W was set by caller */
        PA[i].ac = 0;
    }
    n = pool_add_word(n);
    for (int i = 0; i < n; i++) memcpy(PA[i].t2, PA[i].az, N*sizeof(AF));

    /* 6. add3: t1 + (K+W) → t1 = final T1 */
    for (int i = 0; i < n; i++) {
        memcpy(PA[i].ax, PA[i].t1, N*sizeof(AF));
        memcpy(PA[i].ay, PA[i].t2, N*sizeof(AF));
        PA[i].ac = 0;
    }
    n = pool_add_word(n);
    for (int i = 0; i < n; i++) memcpy(PA[i].t1, PA[i].az, N*sizeof(AF)); /* T1 final */

    /* 7. Maj(a,b,c) → maj. ax=a, ay=b, c from registers. */
    for (int i = 0; i < n; i++) {
        memcpy(PA[i].ax, REG(&PA[i],0), N*sizeof(AF)); /* a */
        memcpy(PA[i].ay, REG(&PA[i],1), N*sizeof(AF)); /* b */
    }
    n = pool_maj_word(n, is_r2);
    for (int i = 0; i < n; i++) memcpy(PA[i].maj, PA[i].az, N*sizeof(AF));

    /* 8. add4: Sig0(a) + Maj → t2 */
    for (int i = 0; i < n; i++) {
        /* Recompute Sig0 (free, safe after expansions) */
        af_Sigma0(PA[i].ax, REG(&PA[i],0));
        memcpy(PA[i].ay, PA[i].maj, N*sizeof(AF));
        PA[i].ac = 0;
    }
    n = pool_add_word(n);
    for (int i = 0; i < n; i++) memcpy(PA[i].t2, PA[i].az, N*sizeof(AF)); /* T2 */

    /* 9. add5: d + T1 → new_e (save in sig1 field, which is free now) */
    for (int i = 0; i < n; i++) {
        memcpy(PA[i].ax, REG(&PA[i],3), N*sizeof(AF)); /* d */
        memcpy(PA[i].ay, PA[i].t1, N*sizeof(AF));
        PA[i].ac = 0;
    }
    n = pool_add_word(n);
    /* Save new_e result (az) into sig1 field (reused as storage) */
    for (int i = 0; i < n; i++) memcpy(PA[i].sig1, PA[i].az, N*sizeof(AF));

    /* 10. add6: T1 + T2 → new_a */
    for (int i = 0; i < n; i++) {
        memcpy(PA[i].ax, PA[i].t1, N*sizeof(AF));
        memcpy(PA[i].ay, PA[i].t2, N*sizeof(AF));
        PA[i].ac = 0;
    }
    n = pool_add_word(n);
    /* az = new_a. sig1 = new_e. Both are state-internal, so indices are correct. */

    /* 11. Shift register update — ALL N bits */
    for (int i = 0; i < n; i++) {
        AF new_a[N], new_e[N];
        memcpy(new_a, PA[i].az, N*sizeof(AF));
        memcpy(new_e, PA[i].sig1, N*sizeof(AF)); /* new_e was saved in sig1 */
        AF (*R)[N] = is_r2 ? PA[i].r2 : PA[i].r1;
        /* Shift: h←g, g←f, f←e, e←new_e, d←c, c←b, b←a, a←new_a */
        memcpy(R[7], R[6], N*sizeof(AF)); /* h ← g */
        memcpy(R[6], R[5], N*sizeof(AF)); /* g ← f */
        memcpy(R[5], R[4], N*sizeof(AF)); /* f ← e */
        memcpy(R[4], new_e, N*sizeof(AF)); /* e ← new_e */
        memcpy(R[3], R[2], N*sizeof(AF)); /* d ← c */
        memcpy(R[2], R[1], N*sizeof(AF)); /* c ← b */
        memcpy(R[1], R[0], N*sizeof(AF)); /* b ← a */
        memcpy(R[0], new_a, N*sizeof(AF)); /* a ← new_a */
    }

    return n;
    #undef REG
}

/* ==== INIT + TEST ==== */
int main() {
    setbuf(stdout, NULL);
    rS0[0]=SR(2); rS0[1]=SR(13); rS0[2]=SR(22);
    rS1[0]=SR(6); rS1[1]=SR(11); rS1[2]=SR(25);
    for (int i=0;i<64;i++) KN[i]=((uint32_t[]){0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2}[i]) & MASK;

    /* Precompute schedules */
    { uint32_t M1[16],M2[16];
      for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
      M1[0]=0; M2[0]=MSB; M2[9]=MASK^MSB;
      for(int i=0;i<16;i++)W1p[i]=M1[i]&MASK;
      for(int i=16;i<57;i++)W1p[i]=(bfs1(W1p[i-2])+W1p[i-7]+bfs0(W1p[i-15])+W1p[i-16])&MASK;
      for(int i=0;i<16;i++)W2p[i]=M2[i]&MASK;
      for(int i=16;i<57;i++)W2p[i]=(bfs1(W2p[i-2])+W2p[i-7]+bfs0(W2p[i-15])+W2p[i-16])&MASK;
    }
    /* Hardcoded verified state56 */
    s1c[0]=0x9;s1c[1]=0x8;s1c[2]=0xd;s1c[3]=0x5;s1c[4]=0x6;s1c[5]=0xe;s1c[6]=0xb;s1c[7]=0xf;
    s2c[0]=0x9;s2c[1]=0xa;s2c[2]=0xd;s2c[3]=0x8;s2c[4]=0x5;s2c[5]=0x0;s2c[6]=0xc;s2c[7]=0x1;

    PA = calloc(MAXPOOL, sizeof(ST));
    PB = calloc(MAXPOOL, sizeof(ST));
    if (!PA || !PB) { printf("OOM\n"); return 1; }

    printf("ae3: Affine Engine v3, N=%d, %d vars\n", N, NV);
    printf("Phase 2 Test: symbolic addition 5 + (v0,v1,v2,v3)\n\n");

    /* ---- TEST 1: pool_add_word(const 5, symbolic v0..v3) ---- */
    nA = 1;
    g2_init(&PA[0].sys);
    for (int b = 0; b < N; b++) {
        PA[0].ax[b] = af_const((5>>b)&1);
        PA[0].ay[b] = af_var(b);
        PA[0].az[b] = af_const(0);
    }
    PA[0].ac = 0;

    nA = pool_add_word(nA);
    printf("  5 + (v0..v3): %d states (expected 16)\n", nA);

    int test1_ok = 1;
    for (int i = 0; i < nA; i++) {
        uint32_t v = 0;
        for (int b = 0; b < N; b++) {
            AF f = g2_res(&PA[i].sys, af_var(b));
            if (!af_is_const(f)) { test1_ok = 0; break; }
            v |= (af_val(f) << b);
        }
        uint32_t expected_z = (5 + v) & MASK;
        uint32_t actual_z = 0;
        for (int b = 0; b < N; b++) {
            if (!af_is_const(PA[i].az[b])) { test1_ok = 0; break; }
            actual_z |= (af_val(PA[i].az[b]) << b);
        }
        if (actual_z != expected_z) {
            printf("  FAIL: v=0x%x, expected z=0x%x, got z=0x%x\n", v, expected_z, actual_z);
            test1_ok = 0;
        }
    }
    printf("  Test 1 (addition correctness): %s\n\n", test1_ok ? "PASS" : "FAIL");

    /* ---- TEST 1b: with constraints v0=1, v1=0 ---- */
    nA = 1;
    g2_init(&PA[0].sys);
    g2_add(&PA[0].sys, (AF){1, 1});
    g2_add(&PA[0].sys, (AF){2, 0});
    for (int b = 0; b < N; b++) {
        PA[0].ax[b] = af_const((5>>b)&1);
        PA[0].ay[b] = af_var(b);
        PA[0].az[b] = af_const(0);
    }
    PA[0].ac = 0;
    nA = pool_add_word(nA);
    printf("  5 + (v0=1,v1=0,v2,v3): %d states (expected 4)\n", nA);

    /* ---- TEST 1c: fully constrained ---- */
    nA = 1;
    g2_init(&PA[0].sys);
    g2_add(&PA[0].sys, (AF){1, 1});
    g2_add(&PA[0].sys, (AF){2, 0});
    g2_add(&PA[0].sys, (AF){4, 1});
    g2_add(&PA[0].sys, (AF){8, 0});
    for (int b = 0; b < N; b++) {
        PA[0].ax[b] = af_const((5>>b)&1);
        PA[0].ay[b] = af_var(b);
        PA[0].az[b] = af_const(0);
    }
    PA[0].ac = 0;
    nA = pool_add_word(nA);
    printf("  5 + (1,0,1,0)=0xA: %d states (expected 1)\n", nA);
    if (nA == 1) {
        uint32_t z = 0;
        for (int b = 0; b < N; b++) z |= (af_val(PA[0].az[b]) << b);
        printf("  z = 0x%x (expected 0xa)\n", z);
    }

    printf("Phase 2 complete.\n\n");

    /* ==== Phase 4 Test: One round (57) msg1, verify against brute force ==== */
    printf("Phase 4 Test: round 57 msg1, symbolic W1[57] = v0..v3\n");

    nA = 1;
    g2_init(&PA[0].sys);
    for (int r = 0; r < 8; r++) for (int b = 0; b < N; b++) {
        PA[0].r1[r][b] = af_const((s1c[r]>>b)&1);
        PA[0].r2[r][b] = af_const((s2c[r]>>b)&1);
    }
    /* Set W1[57] = v0..v3 */
    for (int b = 0; b < N; b++) PA[0].w[b] = af_var(b);

    nA = do_one_round(nA, 0, 0); /* round 57, msg1 */
    printf("  After round 57 msg1: %d states (expected 16)\n", nA);

    /* Verify: for each state, extract v0..v3, compute brute-force round 57,
     * compare all 8 register values at all N bits. */
    int test4_ok = 1;
    for (int i = 0; i < nA && i < 16; i++) {
        uint32_t w1v = 0;
        for (int b = 0; b < N; b++) {
            AF f = g2_res(&PA[i].sys, af_var(b));
            if (!af_is_const(f)) { test4_ok = 0; break; }
            w1v |= (af_val(f) << b);
        }
        /* Brute-force round 57 */
        uint32_t bf[8]; memcpy(bf, s1c, 32);
        bf_round(bf, KN[57], w1v);
        /* Compare against affine state */
        for (int r = 0; r < 8; r++) {
            uint32_t sym_val = 0;
            for (int b = 0; b < N; b++) {
                AF f = g2_res(&PA[i].sys, PA[i].r1[r][b]);
                if (!af_is_const(f)) {
                    printf("  FAIL: state %d reg %d bit %d still symbolic (mask=0x%x)\n",
                           i, r, b, f.m);
                    test4_ok = 0; break;
                }
                sym_val |= (af_val(f) << b);
            }
            if (sym_val != bf[r]) {
                printf("  FAIL: state %d (w=%x) reg %d: symbolic=0x%x brute=0x%x\n",
                       i, w1v, r, sym_val, bf[r]);
                test4_ok = 0;
            }
        }
    }
    printf("  Test 4 (one-round equivalence): %s\n\n", test4_ok ? "PASS" : "FAIL");

    /* ==== Phase 5 Test: Cascade W2 for round 57 + msg2 round ==== */
    printf("Phase 5 Test: cascade W2[57] = W1[57] + 0x7, then round 57 msg2\n");

    /* Restart: process round 57 msg1 first (same as above) */
    nA = 1;
    g2_init(&PA[0].sys);
    for (int r = 0; r < 8; r++) for (int b = 0; b < N; b++) {
        PA[0].r1[r][b] = af_const((s1c[r]>>b)&1);
        PA[0].r2[r][b] = af_const((s2c[r]>>b)&1);
    }
    for (int b = 0; b < N; b++) PA[0].w[b] = af_var(b); /* W1[57] = v0..v3 */
    nA = do_one_round(nA, 0, 0); /* round 57 msg1 */
    printf("  After round 57 msg1: %d states\n", nA);

    /* Compute W2[57] = W1[57] + C_57 where C_57 = 0x7.
     * W1[57] = v0..v3 (symbolic). Use pool_add_word. */
    for (int i = 0; i < nA; i++) {
        for (int b = 0; b < N; b++) {
            PA[i].ax[b] = af_var(b); /* W1[57] */
            PA[i].ay[b] = af_const((0x7 >> b) & 1); /* C_57 */
        }
        PA[i].ac = 0;
    }
    nA = pool_add_word(nA);
    /* PA[i].az = W2[57]. Copy to w for the msg2 round. */
    for (int i = 0; i < nA; i++) memcpy(PA[i].w, PA[i].az, N*sizeof(AF));
    printf("  After cascade W2 computation: %d states\n", nA);

    /* Test: verify W2 values match cascade for all assignments */
    int test5a_ok = 1;
    for (int i = 0; i < nA && i < 32; i++) {
        uint32_t w1v = 0;
        for (int b = 0; b < N; b++) {
            AF f = g2_res(&PA[i].sys, af_var(b));
            if (af_is_const(f)) w1v |= (af_val(f) << b);
        }
        uint32_t w2_expected = (w1v + 0x7) & MASK;
        uint32_t w2_actual = 0;
        for (int b = 0; b < N; b++) {
            AF f = g2_res(&PA[i].sys, PA[i].w[b]);
            if (af_is_const(f)) w2_actual |= (af_val(f) << b);
        }
        if (w2_actual != w2_expected) {
            printf("  FAIL: w1=0x%x, w2 expected 0x%x got 0x%x\n", w1v, w2_expected, w2_actual);
            test5a_ok = 0;
        }
    }
    printf("  Test 5a (cascade W2 correctness): %s\n", test5a_ok ? "PASS" : "FAIL");

    /* Now run round 57 for msg2 using the cascaded W2 */
    nA = do_one_round(nA, 0, 1); /* round 57 msg2 */
    printf("  After round 57 msg2: %d states\n", nA);

    /* Verify msg2 registers against brute force */
    int test5b_ok = 1;
    for (int i = 0; i < nA && i < 32; i++) {
        uint32_t w1v = 0;
        for (int b = 0; b < N; b++) {
            AF f = g2_res(&PA[i].sys, af_var(b));
            if (af_is_const(f)) w1v |= (af_val(f) << b);
        }
        uint32_t w2v = (w1v + 0x7) & MASK;
        /* Brute-force round 57 msg2 */
        uint32_t bf2[8]; memcpy(bf2, s2c, 32);
        bf_round(bf2, KN[57], w2v);
        for (int r = 0; r < 8; r++) {
            uint32_t sym_val = 0;
            for (int b = 0; b < N; b++) {
                AF f = g2_res(&PA[i].sys, PA[i].r2[r][b]);
                if (!af_is_const(f)) { test5b_ok = 0; break; }
                sym_val |= (af_val(f) << b);
            }
            if (sym_val != bf2[r]) {
                printf("  FAIL: state %d (w1=%x w2=%x) reg %d: sym=0x%x bf=0x%x\n",
                       i, w1v, w2v, r, sym_val, bf2[r]);
                test5b_ok = 0;
            }
        }
    }
    printf("  Test 5b (msg2 round correctness): %s\n\n", test5b_ok ? "PASS" : "FAIL");

    /* ==== Phase 6: Full 7 rounds + cascade constraints + collision prune ==== */
    printf("Phase 6: Full 7 rounds with cascade + collision prune\n");
    printf("  32 variables (W1 + W2 independent, cascade via GF2 constraints)\n\n");

    nA = 1;
    g2_init(&PA[0].sys);
    for (int r = 0; r < 8; r++) for (int b = 0; b < N; b++) {
        PA[0].r1[r][b] = af_const((s1c[r]>>b)&1);
        PA[0].r2[r][b] = af_const((s2c[r]>>b)&1);
    }

    for (int rnd = 0; rnd < 7; rnd++) {
        int rr = 57 + rnd;
        int is_free = (rnd < 4);

        /* Set message words */
        if (is_free) {
            /* W1[rnd] = variables at offset rnd*N */
            /* W2[rnd] = variables at offset (4+rnd)*N */
            for (int i = 0; i < nA; i++) {
                for (int b = 0; b < N; b++)
                    PA[i].w[b] = af_var(rnd * N + b);
            }
        } else {
            /* Schedule-determined: compute from resolved variables */
            for (int i = 0; i < nA; i++) {
                uint32_t ww[4] = {0};
                for (int wd = 0; wd < 4; wd++) for (int b = 0; b < N; b++) {
                    AF f = g2_res(&PA[i].sys, af_var(wd*N+b));
                    if (af_is_const(f)) ww[wd] |= (af_val(f) << b);
                }
                uint32_t ws;
                if (rr==61) ws=(bfs1(ww[2])+W1p[54]+bfs0(W1p[46])+W1p[45])&MASK;
                else if (rr==62) ws=(bfs1(ww[3])+W1p[55]+bfs0(W1p[47])+W1p[46])&MASK;
                else { uint32_t w61=(bfs1(ww[2])+W1p[54]+bfs0(W1p[46])+W1p[45])&MASK;
                       ws=(bfs1(w61)+W1p[56]+bfs0(W1p[48])+W1p[47])&MASK; }
                for (int b = 0; b < N; b++)
                    PA[i].w[b] = af_const((ws >> b) & 1);
            }
        }

        /* Process msg1 */
        { int nb=nA; nA = do_one_round(nA, rnd, 0); printf("    msg1: %d->%d\n",nb,nA); }

        /* Set W2 for msg2 */
        if (is_free) {
            for (int i = 0; i < nA; i++) {
                for (int b = 0; b < N; b++)
                    PA[i].w[b] = af_var((4 + rnd) * N + b);
            }
        } else {
            /* Schedule for msg2 */
            for (int i = 0; i < nA; i++) {
                uint32_t ww2[4] = {0};
                for (int wd = 0; wd < 4; wd++) for (int b = 0; b < N; b++) {
                    AF f = g2_res(&PA[i].sys, af_var((4+wd)*N+b));
                    if (af_is_const(f)) ww2[wd] |= (af_val(f) << b);
                }
                uint32_t ws2;
                if (rr==61) ws2=(bfs1(ww2[2])+W2p[54]+bfs0(W2p[46])+W2p[45])&MASK;
                else if (rr==62) ws2=(bfs1(ww2[3])+W2p[55]+bfs0(W2p[47])+W2p[46])&MASK;
                else { uint32_t w61=(bfs1(ww2[2])+W2p[54]+bfs0(W2p[46])+W2p[45])&MASK;
                       ws2=(bfs1(w61)+W2p[56]+bfs0(W2p[48])+W2p[47])&MASK; }
                for (int b = 0; b < N; b++)
                    PA[i].w[b] = af_const((ws2 >> b) & 1);
            }
        }

        /* Process msg2 */
        { int nb=nA; nA = do_one_round(nA, rnd, 1); printf("    msg2: %d->%d\n",nb,nA); }

        /* CASCADE CONSTRAINT: new_a_msg1 = new_a_msg2 at all bits.
         * After the round, a = r1[0] for msg1, r2[0] for msg2.
         * Add constraint: r1[0][b] XOR r2[0][b] = 0 for all b. */
        if (is_free) {
            int nout = 0;
            for (int i = 0; i < nA; i++) {
                PB[nout] = PA[i];
                int ok = 1;
                for (int b = 0; b < N && ok; b++) {
                    AF diff = af_xor(PA[i].r1[0][b], PA[i].r2[0][b]);
                    AF rd = g2_res(&PB[nout].sys, diff);
                    if (af_is_const(rd)) {
                        if (af_val(rd) != 0) ok = 0; /* constant nonzero diff → prune */
                    } else {
                        if (!g2_add(&PB[nout].sys, rd)) ok = 0; /* contradiction → prune */
                    }
                }
                if (ok) nout++;
            }
            ST *tmp = PA; PA = PB; PB = tmp; nA = nout;
        }

        printf("  Round %d: %d states (after%s cascade)\n", rr, nA, is_free?" +":"");

        if (nA == 0) { printf("  DEAD\n"); break; }
    }

    /* COLLISION PRUNE: all 8 registers must match at all N bits */
    if (nA > 0) {
        printf("  Collision prune...\n");
        int nout = 0;
        for (int i = 0; i < nA; i++) {
            PB[nout] = PA[i];
            int ok = 1;
            for (int r = 0; r < 8 && ok; r++) {
                for (int b = 0; b < N && ok; b++) {
                    AF diff = af_xor(PA[i].r1[r][b], PA[i].r2[r][b]);
                    AF rd = g2_res(&PB[nout].sys, diff);
                    if (af_is_const(rd)) {
                        if (af_val(rd) != 0) ok = 0;
                    } else {
                        if (!g2_add(&PB[nout].sys, rd)) ok = 0;
                    }
                }
            }
            if (ok) nout++;
        }
        ST *tmp = PA; PA = PB; PB = tmp; nA = nout;
        printf("  After collision prune: %d states\n", nA);
    }

    /* Verify collisions */
    if (nA > 0) {
        printf("  Verifying collisions against brute force...\n");
        int n_verified = 0;
        for (int i = 0; i < nA && i < 100; i++) {
            uint32_t w1[4]={0}, w2[4]={0};
            for (int wd=0;wd<4;wd++) for(int b=0;b<N;b++){
                AF f1=g2_res(&PA[i].sys, af_var(wd*N+b));
                AF f2=g2_res(&PA[i].sys, af_var((4+wd)*N+b));
                if(af_is_const(f1)) w1[wd]|=(af_val(f1)<<b);
                if(af_is_const(f2)) w2[wd]|=(af_val(f2)<<b);
            }
            /* Run brute force 7 rounds */
            uint32_t sa[8],sb[8]; memcpy(sa,s1c,32);memcpy(sb,s2c,32);
            uint32_t W1s[7]={w1[0],w1[1],w1[2],w1[3],0,0,0};
            uint32_t W2s[7]={w2[0],w2[1],w2[2],w2[3],0,0,0};
            W1s[4]=(bfs1(W1s[2])+W1p[54]+bfs0(W1p[46])+W1p[45])&MASK;
            W2s[4]=(bfs1(W2s[2])+W2p[54]+bfs0(W2p[46])+W2p[45])&MASK;
            W1s[5]=(bfs1(W1s[3])+W1p[55]+bfs0(W1p[47])+W1p[46])&MASK;
            W2s[5]=(bfs1(W2s[3])+W2p[55]+bfs0(W2p[47])+W2p[46])&MASK;
            W1s[6]=(bfs1(W1s[4])+W1p[56]+bfs0(W1p[48])+W1p[47])&MASK;
            W2s[6]=(bfs1(W2s[4])+W2p[56]+bfs0(W2p[48])+W2p[47])&MASK;
            for(int r=0;r<7;r++){bf_round(sa,KN[57+r],W1s[r]);bf_round(sb,KN[57+r],W2s[r]);}
            int ok=1;for(int r=0;r<8;r++)if(sa[r]!=sb[r])ok=0;
            if(ok) n_verified++;
            if(i<5) printf("    W1=[%x,%x,%x,%x] W2=[%x,%x,%x,%x] %s\n",
                w1[0],w1[1],w1[2],w1[3],w2[0],w2[1],w2[2],w2[3],ok?"COLLISION":"no");
        }
        printf("  Verified: %d/%d are true collisions\n", n_verified, nA);
    }

    if (nA == 49) printf("\n*** ALL 49 COLLISIONS FOUND ***\n");
    else printf("\n  Final state count: %d (target: 49)\n", nA);

    free(PA); free(PB);
    printf("\nDone.\n");
    return 0;
}
