/*
 * bdd_from_collisions.c — Build BDD from collision list
 *
 * Reads collision coordinates from stdin (format: "COLL w57 w58 w59 w60")
 * and builds the interleaved-variable BDD for the collision function.
 *
 * Much faster than brute-force truth table: only processes actual collisions.
 * For N=10 with ~946 collisions, this takes seconds instead of hours.
 *
 * Usage: grep '^COLL' solver_output.txt | ./bdd_from_coll N
 *
 * Compile: gcc -O3 -march=native -o bdd_from_coll bdd_from_collisions.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

static int N;
static int NVARS;

/* BDD core */
typedef struct { int var,lo,hi; } BDDNode;
#define BDD_FALSE 0
#define BDD_TRUE  1
static BDDNode *bdd_nodes; static int bdd_count, bdd_cap;
typedef struct { int var,lo,hi,node_id,next; } UEntry;
#define UHASH_BITS 22
#define UHASH_SIZE (1<<UHASH_BITS)
#define UHASH_MASK (UHASH_SIZE-1)
static int *uhash_table; static UEntry *uentry_pool; static int uentry_count, uentry_cap;
#define CHASH_BITS 22
#define CHASH_SIZE (1<<CHASH_BITS)
#define CHASH_MASK (CHASH_SIZE-1)
typedef struct { int op,f,g,result; } CEntry;
static CEntry *comp_table;

static void bdd_init(void) {
    bdd_cap=1<<20; bdd_nodes=malloc(bdd_cap*sizeof(BDDNode));
    bdd_nodes[0]=(BDDNode){-1,0,0}; bdd_nodes[1]=(BDDNode){-1,1,1}; bdd_count=2;
    uhash_table=malloc(UHASH_SIZE*sizeof(int));
    for(int i=0;i<UHASH_SIZE;i++) uhash_table[i]=-1;
    uentry_cap=1<<20; uentry_pool=malloc(uentry_cap*sizeof(UEntry)); uentry_count=0;
    comp_table=calloc(CHASH_SIZE,sizeof(CEntry));
    for(int i=0;i<CHASH_SIZE;i++) comp_table[i].op=-1;
}

static int bdd_make(int var, int lo, int hi) {
    if(lo==hi) return lo;
    uint32_t h=((uint32_t)var*7919u+(uint32_t)lo*104729u+(uint32_t)hi*1000003u)&UHASH_MASK;
    for(int ei=uhash_table[h];ei>=0;ei=uentry_pool[ei].next){
        UEntry*e=&uentry_pool[ei];
        if(e->var==var&&e->lo==lo&&e->hi==hi) return e->node_id;
    }
    if(bdd_count>=bdd_cap){bdd_cap*=2;bdd_nodes=realloc(bdd_nodes,bdd_cap*sizeof(BDDNode));}
    int id=bdd_count++; bdd_nodes[id]=(BDDNode){var,lo,hi};
    if(uentry_count>=uentry_cap){uentry_cap*=2;uentry_pool=realloc(uentry_pool,uentry_cap*sizeof(UEntry));}
    int nei=uentry_count++;
    uentry_pool[nei]=(UEntry){var,lo,hi,id,uhash_table[h]}; uhash_table[h]=nei;
    return id;
}

enum { OP_AND=0, OP_OR=1 };
static int bdd_apply(int op, int f, int g) {
    if(f<=1&&g<=1) return (op==OP_AND?(f&g):(f|g))?BDD_TRUE:BDD_FALSE;
    if(op==OP_AND){
        if(f==BDD_FALSE||g==BDD_FALSE) return BDD_FALSE;
        if(f==BDD_TRUE) return g; if(g==BDD_TRUE) return f; if(f==g) return f;
    } else {
        if(f==BDD_TRUE||g==BDD_TRUE) return BDD_TRUE;
        if(f==BDD_FALSE) return g; if(g==BDD_FALSE) return f; if(f==g) return f;
    }
    if(f>g){int t=f;f=g;g=t;}
    uint32_t ch=((uint32_t)op*314159u+(uint32_t)f*271828u+(uint32_t)g*161803u)&CHASH_MASK;
    CEntry*ce=&comp_table[ch];
    if(ce->op==op&&ce->f==f&&ce->g==g) return ce->result;
    int vf=(f<=1)?NVARS:bdd_nodes[f].var, vg=(g<=1)?NVARS:bdd_nodes[g].var;
    int v=(vf<vg)?vf:vg;
    int flo=f,fhi=f,glo=g,ghi=g;
    if(vf==v){flo=bdd_nodes[f].lo;fhi=bdd_nodes[f].hi;}
    if(vg==v){glo=bdd_nodes[g].lo;ghi=bdd_nodes[g].hi;}
    int lo=bdd_apply(op,flo,glo), hi=bdd_apply(op,fhi,ghi);
    int result=bdd_make(v,lo,hi);
    ce->op=op;ce->f=f;ce->g=g;ce->result=result;
    return result;
}

/* Build a "point BDD": TRUE only at one specific assignment.
 * Variables in interleaved order: var 4*b+w, w=0:W57, w=1:W58, w=2:W59, w=3:W60
 * Process from deepest variable to shallowest for optimal BDD size. */
static int make_point_bdd(uint32_t w57, uint32_t w58, uint32_t w59, uint32_t w60) {
    int result = BDD_TRUE;
    /* Process from LAST variable (NVARS-1) to first (0) */
    for (int v = NVARS-1; v >= 0; v--) {
        int b = v / 4;    /* bit position */
        int w = v % 4;    /* word: 0=W57, 1=W58, 2=W59, 3=W60 */
        uint32_t word;
        switch(w) {
            case 0: word = w57; break;
            case 1: word = w58; break;
            case 2: word = w59; break;
            default: word = w60; break;
        }
        int bit = (word >> b) & 1;
        if (bit)
            result = bdd_make(v, BDD_FALSE, result);  /* hi = result, lo = FALSE */
        else
            result = bdd_make(v, result, BDD_FALSE);  /* lo = result, hi = FALSE */
    }
    return result;
}

/* Node counting */
static int *vis; static int vis_cap;
static int cnt_rec(int n){
    if(n<=1)return 0;
    if(n>=vis_cap){int nc=n+1;vis=realloc(vis,nc*sizeof(int));
        memset(vis+vis_cap,0,(nc-vis_cap)*sizeof(int));vis_cap=nc;}
    if(vis[n])return 0; vis[n]=1;
    return 1+cnt_rec(bdd_nodes[n].lo)+cnt_rec(bdd_nodes[n].hi);
}
static int count_nodes(int root){
    if(vis_cap<bdd_count){vis=realloc(vis,bdd_count*sizeof(int));vis_cap=bdd_count;}
    memset(vis,0,vis_cap*sizeof(int)); return cnt_rec(root);
}
static double satcount(int node,int level){
    if(node==BDD_FALSE)return 0.0;
    if(node==BDD_TRUE)return ldexp(1.0,NVARS-level);
    int v=bdd_nodes[node].var;
    return ldexp(1.0,v-level)*(satcount(bdd_nodes[node].lo,v+1)+satcount(bdd_nodes[node].hi,v+1));
}

int main(int argc, char **argv) {
    setbuf(stdout,NULL);
    struct timespec t0,t_now;
    clock_gettime(CLOCK_MONOTONIC,&t0);

    N = (argc>1) ? atoi(argv[1]) : 8;
    if(N<2||N>32){printf("N must be 2..32\n");return 1;}
    NVARS = 4*N;

    printf("=== BDD from Collision List, N=%d (%d variables) ===\n\n", N, NVARS);

    bdd_init();

    /* Read collision coordinates from stdin */
    int collision_bdd = BDD_FALSE;
    int ncoll = 0;
    char line[256];
    uint32_t w57, w58, w59, w60;

    printf("Reading collisions from stdin...\n");

    while (fgets(line, sizeof(line), stdin)) {
        if (sscanf(line, "COLL %x %x %x %x", &w57, &w58, &w59, &w60) == 4 ||
            sscanf(line, "%x %x %x %x", &w57, &w58, &w59, &w60) == 4) {

            int point = make_point_bdd(w57, w58, w59, w60);
            collision_bdd = bdd_apply(OP_OR, collision_bdd, point);
            ncoll++;

            if (ncoll % 100 == 0) {
                int cn = count_nodes(collision_bdd);
                printf("  %d collisions read, BDD nodes: %d\n", ncoll, cn);
            }
        }
    }

    clock_gettime(CLOCK_MONOTONIC,&t_now);
    double el=(t_now.tv_sec-t0.tv_sec)+(t_now.tv_nsec-t0.tv_nsec)/1e9;

    int final_nodes = count_nodes(collision_bdd);
    double sat = satcount(collision_bdd, 0);

    printf("\n=== RESULTS ===\n\n");
    printf("N = %d\n", N);
    printf("Collisions read: %d\n", ncoll);
    printf("BDD nodes: %d\n", final_nodes);
    printf("BDD satcount: %.0f\n", sat);
    printf("Match: %s\n", (ncoll==(int)sat)?"YES":"NO");
    printf("Nodes per collision: %.1f\n", (double)final_nodes/ncoll);
    printf("Total allocated: %d\n", bdd_count-2);
    printf("Construction time: %.2fs\n", el);

    /* Per-variable node counts */
    printf("\nNodes per variable:\n");
    int var_cnt[256]; memset(var_cnt,0,sizeof(var_cnt));
    for(int i=2;i<bdd_count;i++)
        if(bdd_nodes[i].var>=0&&bdd_nodes[i].var<NVARS) var_cnt[bdd_nodes[i].var]++;
    for(int v=0;v<NVARS;v++){
        const char *wn;
        switch(v%4){case 0:wn="W57";break;case 1:wn="W58";break;case 2:wn="W59";break;default:wn="W60";}
        if(var_cnt[v]>0) printf("  var %2d (%s[%d]): %d\n",v,wn,v/4,var_cnt[v]);
    }

    free(bdd_nodes);free(uentry_pool);free(uhash_table);free(comp_table);free(vis);
    return 0;
}
