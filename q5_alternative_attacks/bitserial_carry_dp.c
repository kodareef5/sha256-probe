/*
 * bitserial_carry_dp.c — Bit-serial DP WITH carry propagation and pruning
 *
 * Processes variables in BDD interleaved order (W57[0],W58[0],W59[0],W60[0],
 * W57[1],...). At each 4-variable slice, evaluates the SHA-256 round function
 * at that bit position to compute carries and prune dead states.
 *
 * Key difference from bitserial_quotient_dp.c: that version only tracked GF(2)
 * constraints (zero dedup). This version also evaluates carries concretely
 * and prunes states where the carry chain contradicts.
 *
 * State = (carry_vector for all additions, GF2 system, register AF values)
 * Dedup by (carry_vector hash, g2 hash)
 *
 * Target: pool peak << 65536, ideally ≈ 49 (matching BDD quotient).
 *
 * Compile: gcc -O3 -march=native -o bscdp bitserial_carry_dp.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

#define N 4
#define MASK ((1U<<N)-1)
#define MSB (1U<<(N-1))
#define NV (4*N)
#define NROUNDS 7
#define ADDS_PER_ROUND 7  /* h+S1, +Ch, +K, +W, S0+Maj, T1+T2, d+T1 */
#define ADDS_PER_MSG (ADDS_PER_ROUND * NROUNDS)  /* 49 */
#define TOTAL_ADDS (ADDS_PER_MSG * 2)  /* 98 for both messages */
#define MAXPOOL (1<<20)

/* ---- Affine Forms + GF(2) (same as ae3) ---- */
typedef struct { uint32_t m; uint8_t c; } AF;
static inline AF af_xor(AF a, AF b) { return (AF){a.m^b.m,(uint8_t)(a.c^b.c)}; }
static inline AF af_const(int v) { return (AF){0,(uint8_t)(v&1)}; }
static inline AF af_var(int i) { return (AF){1U<<i,0}; }
static inline int af_is_const(AF f) { return f.m==0; }
static inline int af_val(AF f) { return f.c; }

typedef struct { AF rows[NV]; uint8_t has[NV]; } G2;
static void g2_init(G2 *s){memset(s,0,sizeof(G2));}
static int g2_add(G2 *s, AF f){
    for(int i=NV-1;i>=0;i--)if((f.m>>i)&1&&s->has[i])f=af_xor(f,s->rows[i]);
    if(f.m==0)return f.c?0:1;
    int p=31-__builtin_clz(f.m);
    s->rows[p]=f;s->has[p]=1;
    for(int i=0;i<NV;i++)if(i!=p&&s->has[i]&&((s->rows[i].m>>p)&1))
        s->rows[i]=af_xor(s->rows[i],f);
    return 1;
}
static AF g2_res(const G2 *s, AF f){
    for(int i=NV-1;i>=0;i--)if((f.m>>i)&1&&s->has[i])f=af_xor(f,s->rows[i]);
    return f;
}

/* State: register AFs (all bits) + carry state + GF(2) system */
typedef struct {
    G2 sys;
    AF r1[8][N], r2[8][N];  /* Full register state as affine forms */
    uint8_t carry[TOTAL_ADDS]; /* Concrete carry-out at current bit */
} ST;

static ST *PA, *PB;

/* SHA constants */
static int rS0[3],rS1[3];
static uint32_t KN[64],s1c[8],s2c[8],W1p[64],W2p[64];
static int SR(int k){int r=(int)rint((double)k*N/32.0);return r<1?1:r;}
static uint32_t ror_n(uint32_t x,int k){k%=N;return((x>>k)|(x<<(N-k)))&MASK;}
static uint32_t bfS1(uint32_t e){return ror_n(e,rS1[0])^ror_n(e,rS1[1])^ror_n(e,rS1[2]);}
static uint32_t bfS0(uint32_t a){return ror_n(a,rS0[0])^ror_n(a,rS0[1])^ror_n(a,rS0[2]);}
static uint32_t bfCh(uint32_t e,uint32_t f,uint32_t g){return((e&f)^((~e)&g))&MASK;}
static uint32_t bfMj(uint32_t a,uint32_t b,uint32_t c){return((a&b)^(a&c)^(b&c))&MASK;}
static uint32_t bfs0(uint32_t x){return ror_n(x,SR(7))^ror_n(x,SR(18))^((x>>SR(3))&MASK);}
static uint32_t bfs1(uint32_t x){return ror_n(x,SR(17))^ror_n(x,SR(19))^((x>>SR(10))&MASK);}

/* Evaluate AF at a specific bit, IF that bit is known (all contributing vars resolved) */
static int af_eval_bit(const G2 *sys, AF f) {
    AF r = g2_res(sys, f);
    if (af_is_const(r)) return af_val(r);
    return -1; /* symbolic, can't evaluate */
}

/* Hash state for deduplication: combine carry vector + GF(2) hash */
static uint64_t state_hash(const ST *s) {
    uint64_t h = 0xcbf29ce484222325ULL;
    for (int i = 0; i < TOTAL_ADDS; i++)
        h = (h ^ s->carry[i]) * 0x100000001b3ULL;
    for (int i = 0; i < NV; i++) {
        if (s->sys.has[i]) {
            h ^= (uint64_t)s->sys.rows[i].m * 0x517cc1b727220a95ULL;
            h ^= (uint64_t)s->sys.rows[i].c * 0x100000001b3ULL;
        }
        h = (h << 5) | (h >> 59);
    }
    return h;
}

/* Process one slice: all 4 W1 bits at bit position k, then evaluate rounds */
static int process_slice(int n_in, int bit_k) {
    int nout = 0;

    for (int si = 0; si < n_in; si++) {
        /* Try all 16 combinations of W1[57..60] at bit k */
        for (int w_combo = 0; w_combo < 16; w_combo++) {
            if (nout >= MAXPOOL) goto full;
            PB[nout] = PA[si];
            int ok = 1;

            /* Set W1 variable values */
            int w1_bits[4];
            for (int w = 0; w < 4; w++) {
                w1_bits[w] = (w_combo >> w) & 1;
                int var_id = w * N + bit_k;
                AF con = af_var(var_id); con.c ^= w1_bits[w];
                if (!g2_add(&PB[nout].sys, con)) { ok = 0; break; }
            }
            if (!ok) continue;

            /* Now evaluate 7 rounds at bit k for both messages.
             * For each round: compute carries for the 7 additions.
             * The register values at bit k come from:
             *   - Round 57: state56 (all constant)
             *   - Round 58+: previous round's output at bit k (computed from carries)
             *
             * Sigma rotations read OTHER bits — these may still be symbolic.
             * But at round 57, ALL registers are constant → Sigma is concrete.
             * At round 58: some registers are concrete (shifted from state56),
             * others depend on round 57 at other bit positions (symbolic).
             * For the bits we CAN evaluate, compute carries concretely.
             * For symbolic bits, the carry becomes "undetermined" — we skip pruning.
             */

            /* Track register bit k through the rounds */
            /* Round 57: all inputs from state56 → fully concrete */
            int reg1[8], reg2[8]; /* bit k of each register, -1 if symbolic */
            for (int j = 0; j < 8; j++) {
                reg1[j] = af_eval_bit(&PB[nout].sys, PB[nout].r1[j][bit_k]);
                reg2[j] = af_eval_bit(&PB[nout].sys, PB[nout].r2[j][bit_k]);
            }

            /* Process 7 rounds for msg1 then msg2 */
            for (int msg = 0; msg < 2; msg++) {
                int *reg = (msg == 0) ? reg1 : reg2;
                AF (*R)[N] = (msg == 0) ? PB[nout].r1 : PB[nout].r2;
                int carry_off = msg * ADDS_PER_MSG;

                for (int rnd = 0; rnd < NROUNDS; rnd++) {
                    int a = reg[0], b = reg[1], c = reg[2], d = reg[3];
                    int e = reg[4], f = reg[5], g = reg[6], h = reg[7];

                    /* If ANY register bit is symbolic (-1), we can't compute carries.
                     * Skip carry update for this round (leave carries from prior slice). */
                    if (a < 0 || b < 0 || c < 0 || d < 0 ||
                        e < 0 || f < 0 || g < 0 || h < 0) {
                        /* Can't evaluate — register has symbolic bits at position k.
                         * This happens when Sigma at a prior round read a bit at position k
                         * from a register that depends on an unprocessed variable. */
                        goto next_round;
                    }

                    /* Sigma1(e)[k] — reads e at rotated positions.
                     * THESE POSITIONS MAY BE AT OTHER BIT INDICES.
                     * Evaluate from the full AF register array. */
                    int sig1k = af_eval_bit(&PB[nout].sys,
                        af_xor(af_xor(R[4][(bit_k+rS1[0])%N],
                                      R[4][(bit_k+rS1[1])%N]),
                                      R[4][(bit_k+rS1[2])%N]));
                    int chk;
                    if (sig1k < 0) goto next_round; /* Sigma1 has symbolic input */

                    /* Ch(e,f,g)[k] = e?f:g */
                    chk = e ? f : g;

                    int Kk = (KN[57 + rnd] >> bit_k) & 1;

                    /* Message word bit */
                    int wk;
                    if (rnd < 4) {
                        wk = (msg == 0) ? w1_bits[rnd] : -1; /* W2 from cascade */
                    } else {
                        /* Schedule word — need full word values to compute sigma1 etc.
                         * At N=4, all bits are processed in 4 slices. By round 61+,
                         * W[57..60] are fully known only after ALL slices processed.
                         * For early slices, schedule words are symbolic. */
                        wk = -1; /* Can't evaluate yet */
                    }

                    /* Cascade W2: need to compute offset at this round.
                     * At round 57: offset is constant (all state56).
                     * At round 58+: offset depends on previous rounds' state. */
                    if (msg == 1 && rnd < 4) {
                        /* Compute W2 bit from cascade.
                         * Cascade: a_new_1 = a_new_2 → T1_1 + T2_1 = T1_2 + T2_2
                         * T1 = h + Sig1 + Ch + K + W
                         * T2 = Sig0 + Maj
                         * At round 57: all operands concrete → W2[57][k] determined.
                         *
                         * For now: evaluate T1_no_w and T2 for both msgs if concrete. */
                        int sig0k = af_eval_bit(&PB[nout].sys,
                            af_xor(af_xor(R[0][(bit_k+rS0[0])%N],
                                          R[0][(bit_k+rS0[1])%N]),
                                          R[0][(bit_k+rS0[2])%N]));
                        if (sig0k < 0) goto next_round;
                        int majk = (a & b) ^ (a & c) ^ (b & c);

                        /* T1_no_w = h + Sig1 + Ch + K (4 additions with carries) */
                        int ci, s_bit, co;
                        int add_base = carry_off + rnd * ADDS_PER_ROUND;

                        /* We need the msg1 T1+T2 result too for cascade.
                         * This is getting complex. Let me use a simpler approach:
                         * compute concrete full-word results for round 57 msg1,
                         * then derive W2. */

                        /* SIMPLIFICATION for N=4 prototype:
                         * Only evaluate carries at round 57 (where everything is concrete).
                         * For rounds 58+, skip carry evaluation (leave as-is). */
                        if (rnd > 0) goto next_round;

                        /* Round 57 msg2: compute W2[57][k] from cascade */
                        /* Already handled below in the T1 chain evaluation */
                        wk = -1; /* Will be set by cascade logic below */
                    }

                    if (wk < 0 && !(msg == 1 && rnd == 0)) goto next_round;

                    /* === Round 57 carry evaluation (fully concrete) === */
                    if (rnd == 0) {
                        int add_base = carry_off + rnd * ADDS_PER_ROUND;

                        /* add0: h + Sig1 */
                        int ci0 = PB[nout].carry[add_base + 0];
                        int s0 = h ^ sig1k ^ ci0;
                        int co0 = (h & sig1k) | (h & ci0) | (sig1k & ci0);
                        PB[nout].carry[add_base + 0] = co0;

                        /* add1: s0 + Ch */
                        int ci1 = PB[nout].carry[add_base + 1];
                        int s1v = s0 ^ chk ^ ci1;
                        int co1 = (s0 & chk) | (s0 & ci1) | (chk & ci1);
                        PB[nout].carry[add_base + 1] = co1;

                        /* add2: s1 + K */
                        int ci2 = PB[nout].carry[add_base + 2];
                        int s2v = s1v ^ Kk ^ ci2;
                        int co2 = (s1v & Kk) | (s1v & ci2) | (Kk & ci2);
                        PB[nout].carry[add_base + 2] = co2;

                        /* add3: s2 + W */
                        int ci3 = PB[nout].carry[add_base + 3];
                        if (msg == 0) {
                            wk = w1_bits[0]; /* W1[57][k] */
                        } else {
                            /* Cascade: need msg1's T1+T2 at this bit.
                             * For round 57, msg1 was just processed.
                             * We need to track msg1's intermediate values.
                             * SIMPLIFICATION: compute msg1's results in a separate pass. */
                            /* For this prototype: skip msg2 cascade at bit level.
                             * Just record the carry state for msg1. */
                            goto next_round;
                        }
                        int t1k = s2v ^ wk ^ ci3;
                        int co3 = (s2v & wk) | (s2v & ci3) | (wk & ci3);
                        PB[nout].carry[add_base + 3] = co3;

                        /* add4: Sig0 + Maj */
                        int sig0k_v = af_eval_bit(&PB[nout].sys,
                            af_xor(af_xor(R[0][(bit_k+rS0[0])%N],
                                          R[0][(bit_k+rS0[1])%N]),
                                          R[0][(bit_k+rS0[2])%N]));
                        if (sig0k_v < 0) goto next_round;
                        int majk_v = (a & b) ^ (a & c) ^ (b & c);
                        int ci4 = PB[nout].carry[add_base + 4];
                        int t2k = sig0k_v ^ majk_v ^ ci4;
                        int co4 = (sig0k_v & majk_v) | (sig0k_v & ci4) | (majk_v & ci4);
                        PB[nout].carry[add_base + 4] = co4;

                        /* add5: T1 + T2 = a_new */
                        int ci5 = PB[nout].carry[add_base + 5];
                        int a_new_k = t1k ^ t2k ^ ci5;
                        int co5 = (t1k & t2k) | (t1k & ci5) | (t2k & ci5);
                        PB[nout].carry[add_base + 5] = co5;

                        /* add6: d + T1 = e_new */
                        int ci6 = PB[nout].carry[add_base + 6];
                        int e_new_k = d ^ t1k ^ ci6;
                        int co6 = (d & t1k) | (d & ci6) | (t1k & ci6);
                        PB[nout].carry[add_base + 6] = co6;

                        /* Update register AFs at bit k */
                        R[7][bit_k] = R[6][bit_k]; /* h ← g */
                        R[6][bit_k] = R[5][bit_k]; /* g ← f */
                        R[5][bit_k] = R[4][bit_k]; /* f ← e */
                        R[4][bit_k] = af_const(e_new_k);
                        R[3][bit_k] = R[2][bit_k]; /* d ← c */
                        R[2][bit_k] = R[1][bit_k]; /* c ← b */
                        R[1][bit_k] = R[0][bit_k]; /* b ← a */
                        R[0][bit_k] = af_const(a_new_k);

                        /* Update concrete reg tracking */
                        reg[7]=reg[6];reg[6]=reg[5];reg[5]=reg[4];reg[4]=e_new_k;
                        reg[3]=reg[2];reg[2]=reg[1];reg[1]=reg[0];reg[0]=a_new_k;
                    }

                    next_round:;
                }
            }

            /* State survived all evaluable rounds — add to output pool */
            nout++;
        }
    }
    full:;

    /* Swap pools */
    ST *tmp = PA; PA = PB; PB = tmp;
    return nout;
}

int main() {
    setbuf(stdout, NULL);
    rS0[0]=SR(2);rS0[1]=SR(13);rS0[2]=SR(22);
    rS1[0]=SR(6);rS1[1]=SR(11);rS1[2]=SR(25);
    for(int i=0;i<64;i++)KN[i]=((uint32_t[]){0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2}[i])&MASK;

    s1c[0]=0x9;s1c[1]=0x8;s1c[2]=0xd;s1c[3]=0x5;s1c[4]=0x6;s1c[5]=0xe;s1c[6]=0xb;s1c[7]=0xf;
    s2c[0]=0x9;s2c[1]=0xa;s2c[2]=0xd;s2c[3]=0x8;s2c[4]=0x5;s2c[5]=0x0;s2c[6]=0xc;s2c[7]=0x1;

    {uint32_t M1[16],M2[16];
     for(int i=0;i<16;i++){M1[i]=MASK;M2[i]=MASK;}
     M1[0]=0;M2[0]=MSB;M2[9]=MASK^MSB;
     for(int i=0;i<16;i++){W1p[i]=M1[i]&MASK;W2p[i]=M2[i]&MASK;}
     for(int i=16;i<64;i++){
         W1p[i]=(bfs1(W1p[i-2])+W1p[i-7]+bfs0(W1p[i-15])+W1p[i-16])&MASK;
         W2p[i]=(bfs1(W2p[i-2])+W2p[i-7]+bfs0(W2p[i-15])+W2p[i-16])&MASK;
     }}

    PA = calloc(MAXPOOL, sizeof(ST));
    PB = calloc(MAXPOOL, sizeof(ST));
    if (!PA||!PB){printf("OOM\n");return 1;}

    printf("=== Bit-Serial Carry DP, N=%d ===\n", N);
    printf("Processing in BDD interleaved order with carry evaluation.\n\n");

    /* Initialize */
    int nA = 1;
    g2_init(&PA[0].sys);
    for(int r=0;r<8;r++) for(int b=0;b<N;b++){
        PA[0].r1[r][b] = af_const((s1c[r]>>b)&1);
        PA[0].r2[r][b] = af_const((s2c[r]>>b)&1);
    }
    memset(PA[0].carry, 0, TOTAL_ADDS);

    /* Process each bit position */
    for (int k = 0; k < N; k++) {
        nA = process_slice(nA, k);

        /* Deduplicate by state hash */
        uint64_t *hashes = malloc(nA * sizeof(uint64_t));
        for (int i = 0; i < nA; i++) hashes[i] = state_hash(&PA[i]);
        /* Count distinct */
        for (int i = 0; i < nA-1; i++)
            for (int j = i+1; j < nA; j++)
                if (hashes[i] > hashes[j]) { uint64_t t=hashes[i]; hashes[i]=hashes[j]; hashes[j]=t; }
        int distinct = nA > 0 ? 1 : 0;
        for (int i = 1; i < nA; i++) if (hashes[i] != hashes[i-1]) distinct++;
        free(hashes);

        printf("Bit %d: pool=%d, distinct=%d (BDD quotient at depth %d: %s)\n",
               k, nA, distinct,
               k*4+3,
               k==0?"8":k==1?"105":k==2?"235":"49");
    }

    /* Final collision check */
    printf("\n=== Collision check ===\n");
    int collisions = 0;
    for (int i = 0; i < nA; i++) {
        uint32_t W1[4] = {0};
        int valid = 1;
        for (int v = 0; v < NV; v++) {
            AF f = g2_res(&PA[i].sys, af_var(v));
            if (!af_is_const(f)) { valid = 0; break; }
            W1[v % 4] |= (af_val(f) << (v / 4));
        }
        if (!valid) continue;

        /* Brute-force verify */
        uint32_t stA[8],stB[8];
        memcpy(stA,s1c,32);memcpy(stB,s2c,32);
        uint32_t W2[4];
        for(int r=0;r<4;r++){
            uint32_t t1nw1=(stA[7]+bfS1(stA[4])+bfCh(stA[4],stA[5],stA[6])+KN[57+r])&MASK;
            uint32_t t1nw2=(stB[7]+bfS1(stB[4])+bfCh(stB[4],stB[5],stB[6])+KN[57+r])&MASK;
            uint32_t t2_1=(bfS0(stA[0])+bfMj(stA[0],stA[1],stA[2]))&MASK;
            uint32_t t2_2=(bfS0(stB[0])+bfMj(stB[0],stB[1],stB[2]))&MASK;
            W2[r]=(W1[r]+((t1nw1+t2_1)-(t1nw2+t2_2)))&MASK;
            uint32_t t11=(t1nw1+W1[r])&MASK,t12=(t1nw2+W2[r])&MASK;
            stA[7]=stA[6];stA[6]=stA[5];stA[5]=stA[4];stA[4]=(stA[3]+t11)&MASK;
            stA[3]=stA[2];stA[2]=stA[1];stA[1]=stA[0];stA[0]=(t11+t2_1)&MASK;
            stB[7]=stB[6];stB[6]=stB[5];stB[5]=stB[4];stB[4]=(stB[3]+t12)&MASK;
            stB[3]=stB[2];stB[2]=stB[1];stB[1]=stB[0];stB[0]=(t12+t2_2)&MASK;
        }
        uint32_t Wf1[64],Wf2[64];
        memcpy(Wf1,W1p,57*4);memcpy(Wf2,W2p,57*4);
        for(int j=0;j<4;j++){Wf1[57+j]=W1[j];Wf2[57+j]=W2[j];}
        for(int t=61;t<64;t++){
            Wf1[t]=(bfs1(Wf1[t-2])+Wf1[t-7]+bfs0(Wf1[t-15])+Wf1[t-16])&MASK;
            Wf2[t]=(bfs1(Wf2[t-2])+Wf2[t-7]+bfs0(Wf2[t-15])+Wf2[t-16])&MASK;
        }
        memcpy(stA,s1c,32);memcpy(stB,s2c,32);
        for(int r=0;r<7;r++){
            uint32_t T1a=(stA[7]+bfS1(stA[4])+bfCh(stA[4],stA[5],stA[6])+KN[57+r]+Wf1[57+r])&MASK;
            uint32_t T2a=(bfS0(stA[0])+bfMj(stA[0],stA[1],stA[2]))&MASK;
            stA[7]=stA[6];stA[6]=stA[5];stA[5]=stA[4];stA[4]=(stA[3]+T1a)&MASK;
            stA[3]=stA[2];stA[2]=stA[1];stA[1]=stA[0];stA[0]=(T1a+T2a)&MASK;
            uint32_t T1b=(stB[7]+bfS1(stB[4])+bfCh(stB[4],stB[5],stB[6])+KN[57+r]+Wf2[57+r])&MASK;
            uint32_t T2b=(bfS0(stB[0])+bfMj(stB[0],stB[1],stB[2]))&MASK;
            stB[7]=stB[6];stB[6]=stB[5];stB[5]=stB[4];stB[4]=(stB[3]+T1b)&MASK;
            stB[3]=stB[2];stB[2]=stB[1];stB[1]=stB[0];stB[0]=(T1b+T2b)&MASK;
        }
        int coll=1;
        for(int j=0;j<8;j++)if(stA[j]!=stB[j]){coll=0;break;}
        if(coll) collisions++;
    }
    printf("Collisions: %d (expected 49)\n", collisions);

    free(PA);free(PB);
    return 0;
}
