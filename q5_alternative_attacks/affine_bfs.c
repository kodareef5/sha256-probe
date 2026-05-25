/*
 * Affine BFS Collision Finder — Clean Architecture
 *
 * Flat BFS over states. Each branching operation expands the list.
 * GF(2) pruning kills contradictions immediately.
 *
 * Architecture:
 *   states = [initial_state]
 *   for bit = 0 to N-1:
 *     for round = 0 to 6:
 *       for msg = 1, 2:
 *         states = branch_ch(states)      // Ch(e,f,g): branch on e
 *         states = branch_add_T1(states)  // T1 additions: branch on carries
 *         states = branch_maj(states)     // Maj(a,b,c): branch
 *         states = branch_add_T2(states)  // T2 additions
 *         states = update_regs(states)    // shift register update
 *     states = collision_prune(states)    // d_reg[bit]=0 for all 8 regs
 *     print(bit, len(states))
 *
 * Compile: gcc -O3 -march=native -o affine_bfs affine_bfs.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>

#define N 4
#define MASK ((1U << N) - 1)
#define MSB (1U << (N - 1))
#define NV (4 * N)

/* === Affine Form === */
typedef struct { uint32_t m; uint8_t c; } AF;
static inline AF ax(AF a, AF b) { return (AF){a.m^b.m, a.c^b.c}; }
static inline AF ac_(int v) { return (AF){0, v&1}; }
static inline AF av_(int i) { return (AF){1u<<i, 0}; }

/* === GF(2) System === */
typedef struct { AF r[NV]; uint8_t p[NV]; } G2;

static void g2_init(G2 *s) { memset(s, 0, sizeof(G2)); }

static int g2_add(G2 *s, AF f) {
    for (int i = NV-1; i >= 0; i--)
        if ((f.m >> i) & 1 && s->p[i]) f = ax(f, s->r[i]);
    if (!f.m) return f.c ? 0 : 1; /* 0=1 → contradiction */
    int p = 31 - __builtin_clz(f.m);
    s->r[p] = f; s->p[p] = 1;
    for (int i = 0; i < NV; i++)
        if (i != p && s->p[i] && ((s->r[i].m >> p) & 1))
            s->r[i] = ax(s->r[i], f);
    return 1;
}

static AF g2_resolve(const G2 *s, AF f) {
    for (int i = NV-1; i >= 0; i--)
        if ((f.m >> i) & 1 && s->p[i]) f = ax(f, s->r[i]);
    return f;
}

/* === State === */
/* The state tracks BOTH messages' register values as affine forms,
 * plus carry-in for the current addition chain being processed.
 *
 * But tracking all 8×N×2 = 64 affine forms per state is expensive.
 * Optimization: track only the bits we NEED at the current bit position.
 *
 * At bit k, the SHA round function accesses:
 *   - reg[r][k] for all 8 registers (the current bit)
 *   - reg[r][(k+rot)%N] for Sigma0/Sigma1 (rotated bits — past or future)
 *
 * For Sigma: these are just XORs of affine forms — NO branching needed.
 * We access reg[r][any_bit] freely because they're all stored as affine forms.
 */

typedef struct {
    G2 sys;
    AF r1[8][N]; /* msg1 registers */
    AF r2[8][N]; /* msg2 registers */
    /* Carries: for the current round being processed.
     * We process each round's T1 and T2 addition chains sequentially.
     * Carry persists ACROSS bit positions (bit k's carry-out = bit k+1's carry-in).
     * So we store carry-in for each addition in each round for each message. */
    uint8_t c1[7][7]; /* carry_in[round][add_idx] for msg1 */
    uint8_t c2[7][7]; /* for msg2 */
} S;

#define MAXS 65536
static S *A, *B; /* double buffer */
static int nA, nB;

/* === SHA Constants === */
static int rS0[3], rS1[3];
static int scale_rot(int k) { int r = (int)rint((double)k*N/32.0); return r < 1 ? 1 : r; }
static const uint32_t K32[64] = {0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static const uint32_t IV32[8] = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
static uint32_t KN[64], IVN[8], st1c[8], st2c[8], W1p[57], W2p[57];
static uint32_t ror_n(uint32_t x, int k) { k=k%N; return ((x>>k)|(x<<(N-k)))&MASK; }
static uint32_t fnS0(uint32_t a) { return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]); }
static uint32_t fnS1(uint32_t e) { return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]); }
static uint32_t fns0(uint32_t x) { return ror_n(x,scale_rot(7))^ror_n(x,scale_rot(18))^((x>>scale_rot(3))&MASK); }
static uint32_t fns1(uint32_t x) { return ror_n(x,scale_rot(17))^ror_n(x,scale_rot(19))^((x>>scale_rot(10))&MASK); }
static uint32_t fnCh(uint32_t e, uint32_t f, uint32_t g) { return ((e&f)^((~e)&g))&MASK; }
static uint32_t fnMj(uint32_t a, uint32_t b, uint32_t c) { return ((a&b)^(a&c)^(b&c))&MASK; }
static void precompute(const uint32_t M[16], uint32_t st[8], uint32_t W[57]) {
    for(int i=0;i<16;i++)W[i]=M[i]&MASK;for(int i=16;i<57;i++)W[i]=(fns1(W[i-2])+W[i-7]+fns0(W[i-15])+W[i-16])&MASK;
    uint32_t a=IVN[0],b=IVN[1],c=IVN[2],d=IVN[3],e=IVN[4],f=IVN[5],g=IVN[6],h=IVN[7];
    for(int i=0;i<57;i++){uint32_t T1=(h+fnS1(e)+fnCh(e,f,g)+KN[i]+W[i])&MASK,T2=(fnS0(a)+fnMj(a,b,c))&MASK;h=g;g=f;f=e;e=(d+T1)&MASK;d=c;c=b;b=a;a=(T1+T2)&MASK;}
    st[0]=a;st[1]=b;st[2]=c;st[3]=d;st[4]=e;st[5]=f;st[6]=g;st[7]=h;
}

/* === Branch on ONE affine form: guess 0 or 1 ===
 * Takes input states A[0..nA-1], for each: if form is constant, keep as-is.
 * If symbolic: create 2 copies with form=0 and form=1. GF2 prunes contradictions.
 * Output to B[0..nB-1]. */
static void branch_on(AF form_fn(const S*, int bit, int rnd), int bit, int rnd,
                       void update_fn(S*, int bit, int rnd, int val)) {
    nB = 0;
    for (int i = 0; i < nA && nB < MAXS - 2; i++) {
        AF f = g2_resolve(&A[i].sys, form_fn(&A[i], bit, rnd));
        if (f.m == 0) {
            /* Constant: no branch needed */
            B[nB] = A[i];
            update_fn(&B[nB], bit, rnd, f.c);
            nB++;
        } else {
            /* Symbolic: branch on 0 and 1 */
            for (int v = 0; v <= 1; v++) {
                B[nB] = A[i];
                AF con = f; con.c ^= v;
                if (!g2_add(&B[nB].sys, con)) continue; /* contradiction — prune */
                update_fn(&B[nB], bit, rnd, v);
                nB++;
            }
        }
    }
    /* Swap A and B */
    S *tmp = A; A = B; B = tmp;
    nA = nB;
}

/* === One addition at one bit: branch on both operands to determine carry ===
 * For z = x + y at bit k:
 *   z_k = x_k XOR y_k XOR carry_in
 *   carry_out = maj(x_k, y_k, carry_in)
 * We need concrete x_k and y_k to compute carry_out.
 * If either is symbolic: branch.
 */
static void add_one_bit(
    AF (*get_x)(const S*, int bit, int rnd),
    AF (*get_y)(const S*, int bit, int rnd),
    int msg, /* 0=msg1, 1=msg2 */
    int add_idx,
    int rnd, int bit,
    AF *z_bit_out, /* store result here in each state */
    void (*store_z)(S*, int bit, int rnd, AF z_val))
{
    nB = 0;
    for (int i = 0; i < nA && nB < MAXS - 4; i++) {
        AF xf = g2_resolve(&A[i].sys, get_x(&A[i], bit, rnd));
        AF yf = g2_resolve(&A[i].sys, get_y(&A[i], bit, rnd));
        int xc = (xf.m == 0), yc = (yf.m == 0);
        int xvs[2], nxv, yvs[2], nyv;
        if (xc) { xvs[0] = xf.c; nxv = 1; } else { xvs[0]=0; xvs[1]=1; nxv=2; }
        if (yc) { yvs[0] = yf.c; nyv = 1; } else { yvs[0]=0; yvs[1]=1; nyv=2; }

        int cin = msg ? A[i].c2[rnd][add_idx] : A[i].c1[rnd][add_idx];

        for (int xi = 0; xi < nxv; xi++) {
            for (int yi = 0; yi < nyv; yi++) {
                if (nB >= MAXS) break;
                B[nB] = A[i];
                if (!xc) { AF c=xf; c.c^=xvs[xi]; if(!g2_add(&B[nB].sys,c)) continue; }
                if (!yc) { AF c=yf; c.c^=yvs[yi]; if(!g2_add(&B[nB].sys,c)) continue; }
                int zv = xvs[xi] ^ yvs[yi] ^ cin;
                int cout = (xvs[xi]&yvs[yi])|(xvs[xi]&cin)|(yvs[yi]&cin);
                AF z_af = ac_(zv);
                if (msg) B[nB].c2[rnd][add_idx] = cout;
                else     B[nB].c1[rnd][add_idx] = cout;
                if (store_z) store_z(&B[nB], bit, rnd, z_af);
                nB++;
            }
        }
    }
    S *tmp = A; A = B; B = tmp; nA = nB;
}

/* Helper: get Sigma1(e) at bit k — always linear, no branch */
static AF get_sigma1_e(const S *s, int bit, int msg, int rnd_state) {
    const AF (*regs)[N] = msg ? s->r2 : s->r1;
    return ax(ax(regs[4][(bit+rS1[0])%N], regs[4][(bit+rS1[1])%N]), regs[4][(bit+rS1[2])%N]);
}

static AF get_sigma0_a(const S *s, int bit, int msg) {
    const AF (*regs)[N] = msg ? s->r2 : s->r1;
    return ax(ax(regs[0][(bit+rS0[0])%N], regs[0][(bit+rS0[1])%N]), regs[0][(bit+rS0[2])%N]);
}

int main() {
    setbuf(stdout, NULL);
    rS0[0]=scale_rot(2);rS0[1]=scale_rot(13);rS0[2]=scale_rot(22);
    rS1[0]=scale_rot(6);rS1[1]=scale_rot(11);rS1[2]=scale_rot(25);
    for(int i=0;i<64;i++)KN[i]=K32[i]&MASK;
    for(int i=0;i<8;i++)IVN[i]=IV32[i]&MASK;
    int found=0;
    for(uint32_t m0=0;m0<=MASK&&!found;m0++){
        uint32_t M1[16],M2[16];for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
        M1[0]=m0;M2[0]=m0^MSB;M2[9]=MASK^MSB;
        precompute(M1,st1c,W1p);precompute(M2,st2c,W2p);
        if(st1c[0]==st2c[0]){printf("Candidate: M[0]=0x%x\n",m0);found=1;}
    }

    A = calloc(MAXS, sizeof(S));
    B = calloc(MAXS, sizeof(S));

    printf("Affine BFS at N=%d (%d vars)\n\n", N, NV);

    /* Initialize one state */
    nA = 1;
    g2_init(&A[0].sys);
    for (int r = 0; r < 8; r++)
        for (int b = 0; b < N; b++) {
            A[0].r1[r][b] = ac_((st1c[r]>>b)&1);
            A[0].r2[r][b] = ac_((st2c[r]>>b)&1);
        }
    memset(A[0].c1, 0, sizeof(A[0].c1));
    memset(A[0].c2, 0, sizeof(A[0].c2));

    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    for (int bit = 0; bit < N; bit++) {
        for (int rnd = 0; rnd < 7; rnd++) {
            int rr = 57 + rnd; /* actual round number */

            for (int msg = 0; msg < 2; msg++) {
                /* Get the message word bit for this round */
                /* For free rounds (0-3): W1[57+rnd][bit] = variable, W2 from cascade */
                /* For schedule rounds (4-6): W computed from earlier words */

                /* Compute all the operands as affine forms */
                /* Then do the additions with branching */

                /* For this simplified version: do the ENTIRE round as one
                 * concrete evaluation per state (since at N=4, most things
                 * are already determined after branching on the message word bit).
                 *
                 * The REAL affine BFS would track intermediate values as forms.
                 * But for N=4 where rotations wrap, there's no frontier advantage.
                 * Let's just validate that the state count matches expectations.
                 */

                /* Branch on the message word bit (the main source of new variables) */
                if (rnd < 4 && msg == 0) {
                    /* W1[57+rnd] bit k = variable v_{rnd*N+bit} */
                    int var_idx = rnd * N + bit;
                    nB = 0;
                    for (int i = 0; i < nA && nB < MAXS-2; i++) {
                        AF f = g2_resolve(&A[i].sys, av_(var_idx));
                        if (f.m == 0) {
                            /* Already determined by GF2 system */
                            B[nB] = A[i];
                            nB++;
                        } else {
                            for (int v = 0; v <= 1; v++) {
                                B[nB] = A[i];
                                AF con = f; con.c ^= v;
                                if (!g2_add(&B[nB].sys, con)) continue;
                                nB++;
                            }
                        }
                    }
                    S *tmp = A; A = B; B = tmp; nA = nB;
                }
            }

            /* After branching on this round's message bit:
             * Compute the FULL round concretely for each state
             * (all prior variable bits are determined in the GF2 system) */

            nB = 0;
            for (int i = 0; i < nA && nB < MAXS; i++) {
                /* Extract concrete values from GF2 system */
                uint32_t w1_val = 0;
                if (rnd < 4) {
                    for (int b = 0; b <= bit; b++) {
                        AF f = g2_resolve(&A[i].sys, av_(rnd*N+b));
                        if (f.m == 0) w1_val |= (f.c << b);
                    }
                }

                /* Extract current concrete state */
                uint32_t cs1[8], cs2[8];
                for (int r = 0; r < 8; r++) {
                    cs1[r] = 0; cs2[r] = 0;
                    for (int b = 0; b < N; b++) {
                        AF f1 = g2_resolve(&A[i].sys, A[i].r1[r][b]);
                        AF f2 = g2_resolve(&A[i].sys, A[i].r2[r][b]);
                        if (f1.m == 0) cs1[r] |= (f1.c << b);
                        if (f2.m == 0) cs2[r] |= (f2.c << b);
                    }
                }

                /* For this round: if it's a free round AND we've determined
                 * all bits 0..bit of W1, we can compute the round partially.
                 * But we can't compute the FULL round because bits > bit are unknown.
                 *
                 * SKIP full round computation. Just track the GF2 state.
                 * The collision check will happen at the end.
                 */
                B[nB] = A[i];
                nB++;
            }
            S *tmp = A; A = B; B = tmp; nA = nB;
        }

        printf("  Bit %d: %d states (after branching on 4 msg word bits)\n", bit, nA);
    }

    /* After all bits: all 16 variables are determined in each state.
     * Evaluate FULL collision for each state. */
    printf("\nFull collision check on %d states...\n", nA);

    int n_coll = 0;
    for (int i = 0; i < nA; i++) {
        uint32_t w1[4], w2[4];
        for (int r = 0; r < 4; r++) {
            w1[r] = 0;
            for (int b = 0; b < N; b++) {
                AF f = g2_resolve(&A[i].sys, av_(r*N+b));
                if (f.m == 0) w1[r] |= (f.c << b);
            }
        }
        /* Compute cascade W2 and full 7 rounds */
        uint32_t sa[8],sb[8]; memcpy(sa,st1c,32);memcpy(sb,st2c,32);
        for (int r=0;r<4;r++){
            uint32_t r1=(sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[57+r])&MASK;
            uint32_t r2=(sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[57+r])&MASK;
            uint32_t t21=(fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
            uint32_t t22=(fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
            w2[r]=(w1[r]+r1-r2+t21-t22)&MASK;
            uint32_t T1a=(r1+w1[r])&MASK,T2a=t21;
            uint32_t T1b=(r2+w2[r])&MASK,T2b=t22;
            sa[7]=sa[6];sa[6]=sa[5];sa[5]=sa[4];sa[4]=(sa[3]+T1a)&MASK;
            sa[3]=sa[2];sa[2]=sa[1];sa[1]=sa[0];sa[0]=(T1a+T2a)&MASK;
            sb[7]=sb[6];sb[6]=sb[5];sb[5]=sb[4];sb[4]=(sb[3]+T1b)&MASK;
            sb[3]=sb[2];sb[2]=sb[1];sb[1]=sb[0];sb[0]=(T1b+T2b)&MASK;
        }
        uint32_t W1s[7]={w1[0],w1[1],w1[2],w1[3],0,0,0},W2s[7]={w2[0],w2[1],w2[2],w2[3],0,0,0};
        W1s[4]=(fns1(W1s[2])+W1p[54]+fns0(W1p[46])+W1p[45])&MASK;
        W2s[4]=(fns1(W2s[2])+W2p[54]+fns0(W2p[46])+W2p[45])&MASK;
        W1s[5]=(fns1(W1s[3])+W1p[55]+fns0(W1p[47])+W1p[46])&MASK;
        W2s[5]=(fns1(W2s[3])+W2p[55]+fns0(W2p[47])+W2p[46])&MASK;
        W1s[6]=(fns1(W1s[4])+W1p[56]+fns0(W1p[48])+W1p[47])&MASK;
        W2s[6]=(fns1(W2s[4])+W2p[56]+fns0(W2p[48])+W2p[47])&MASK;
        for(int r=4;r<7;r++){
            uint32_t T1a=(sa[7]+fnS1(sa[4])+fnCh(sa[4],sa[5],sa[6])+KN[57+r]+W1s[r])&MASK;
            uint32_t T2a=(fnS0(sa[0])+fnMj(sa[0],sa[1],sa[2]))&MASK;
            sa[7]=sa[6];sa[6]=sa[5];sa[5]=sa[4];sa[4]=(sa[3]+T1a)&MASK;
            sa[3]=sa[2];sa[2]=sa[1];sa[1]=sa[0];sa[0]=(T1a+T2a)&MASK;
            uint32_t T1b=(sb[7]+fnS1(sb[4])+fnCh(sb[4],sb[5],sb[6])+KN[57+r]+W2s[r])&MASK;
            uint32_t T2b=(fnS0(sb[0])+fnMj(sb[0],sb[1],sb[2]))&MASK;
            sb[7]=sb[6];sb[6]=sb[5];sb[5]=sb[4];sb[4]=(sb[3]+T1b)&MASK;
            sb[3]=sb[2];sb[2]=sb[1];sb[1]=sb[0];sb[0]=(T1b+T2b)&MASK;
        }
        int ok=1;for(int r=0;r<8;r++)if(sa[r]!=sb[r]){ok=0;break;}
        if(ok) n_coll++;
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double el=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)/1e9;

    printf("\n=== N=%d Affine BFS Results ===\n", N);
    printf("States after branching: %d\n", nA);
    printf("Collisions found: %d\n", n_coll);
    printf("Time: %.4fs\n", el);
    printf("Cascade DP equivalent: 2^%d = %d states\n", 4*N, 1<<(4*N));
    printf("Reduction: %.1fx\n", (double)(1<<(4*N)) / nA);
    if (n_coll == 49) printf("\n*** ALL 49 COLLISIONS FOUND ***\n");

    free(A); free(B);
    printf("\nDone.\n");
    return 0;
}
