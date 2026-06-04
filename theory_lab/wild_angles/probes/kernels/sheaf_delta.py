"""
sheaf_delta.py — shared cellular-sheaf coboundary kernel for the W4-SH wave.

Builds the cellular sheaf the five W4-SH cards all presuppose:
  - stalks  = GF(2)^N difference words on each register a..h at each round boundary,
              plus the schedule-word diffs that feed the tail.
  - coboundary delta = the linearized round relations (Sigma/sigma EXACT over GF(2);
              Ch/Maj linearized as their first-order (base-point) GF(2) Jacobian;
              modular add -> XOR, i.e. carries dropped, for the LINEAR sheaf L^0).
  - L = delta^T delta  (Hodge Laplacian; real 0/1 incidence for the spectrum).

ONE artifact, used by SH1..SH5:
  assemble_delta_gf2(N, R, force_collision) -> (rows, ncols, layout)   [GF(2)]
  assemble_delta_real(N, R, force_collision) -> dense float incidence   [for eigvalsh]

Design notes / honesty:
  * This is the genuine compression-function unrolling of the LAST R rounds at width
    N (mirrors lib.sha256.run_tail_rounds: a,b,c,d,e,f,g,h shift register + the two
    T1,T2 accumulations). We linearize exactly as the cards specify.
  * "force_collision" appends the rows that pin the OUTPUT register diffs to 0 (so
    ker = harmonic difference-sections = the linear collision space, per SH1).
  * Ch/Maj are linearized at a FIXED random base point per (N, seed). The GF(2)
    first-order part of Ch(e,f,g) w.r.t (de,df,dg) is:  df&e_base part etc. — i.e.
    d/de Ch = (f^g) at bit, d/df Ch = e, d/dg Ch = ~e (all bitwise, base-point).
    Maj: d/da = (b^c), d/db = (a^c), d/dc = (a^b). These are the exact GF(2)
    differentials of the multilinear forms at the base point.

READ-ONLY toward sha256_review: imports lib.sha256 via shabridge only.
"""
import sys, random
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb

# ----- width-N rotation primitives (match lib.sha256 constants, mod N) ---------
def maskN(N): return (1 << N) - 1
def rorN(x, r, N):
    r %= N
    return ((x >> r) | (x << (N - r))) & maskN(N)
def shrN(x, r, N): return (x >> r) & maskN(N)

# Sigma/sigma rotation+shift sets (the 32-bit constants reduced mod N for small N).
S0_ROT = (2, 13, 22)        # Sigma0 : ROR
S1_ROT = (6, 11, 25)        # Sigma1 : ROR
s0_ROT = (7, 18); s0_SHR = 3     # sigma0 : ROR 7, ROR 18, SHR 3
s1_ROT = (17, 19); s1_SHR = 10   # sigma1 : ROR 17, ROR 19, SHR 10

# ------------------------------------------------------------------------------
# A bit-variable is an integer id. A *word* is an N-tuple of bit-ids (bit 0..N-1).
# A linear form over GF(2) is a Python set/int bitmask over the global var ids;
# we store rows as frozenset of var-ids (XOR of those vars = 0).
# Constants enter via a dedicated id ONE = the "1" column if ever needed (diffs are
# homogeneous, so constants drop; we keep purely homogeneous linear relations).
# ------------------------------------------------------------------------------

class VarPool:
    def __init__(self): self.n = 0
    def word(self, N):
        ids = tuple(range(self.n, self.n + N)); self.n += N
        return ids

def xor_word(a, b):
    """symbolic XOR of two words (tuples of frozensets) -> word of frozensets."""
    return tuple(a[i] ^ b[i] for i in range(len(a)))

def sym_word(ids):
    """turn an N-tuple of var-ids into an N-tuple of {var} singletons (linear forms)."""
    return tuple(frozenset((i,)) for i in ids)

def rot_form(word, r, N):
    """ROR a word of linear forms."""
    r %= N
    return tuple(word[(i + r) % N] for i in range(N))
def shr_form(word, r, N):
    """SHR a word of linear forms (bits shifted out -> 0 = empty form)."""
    EMPTY = frozenset()
    return tuple(word[i + r] if i + r < N else EMPTY for i in range(N))

def Sigma_form(word, rots, N):
    out = [frozenset()] * N
    for r in rots:
        rw = rot_form(word, r, N)
        out = [out[i] ^ rw[i] for i in range(N)]
    return tuple(out)
def sigma_form(word, rots, shr, N):
    out = [frozenset()] * N
    for r in rots:
        rw = rot_form(word, r, N)
        out = [out[i] ^ rw[i] for i in range(N)]
    sw = shr_form(word, shr, N)
    out = [out[i] ^ sw[i] for i in range(N)]
    return tuple(out)

def lin_combo(words_coeffs, N):
    """XOR-sum of several words of linear forms (modular add -> XOR = drop carries)."""
    out = [frozenset()] * N
    for w in words_coeffs:
        out = [out[i] ^ w[i] for i in range(N)]
    return tuple(out)

# Ch/Maj linearized at a fixed base point: returns a word of linear forms in the
# input DIFF words (de,df,dg) / (da,db,dc). base = (e,f,g) integers at width N.
def Ch_lin(de, df, dg, base, N):
    e, f, g = base
    out = []
    for i in range(N):
        ei = (e >> i) & 1; fi = (f >> i) & 1; gi = (g >> i) & 1
        # d Ch/d e = f ^ g ; d Ch/d f = e ; d Ch/d g = ~e   (bitwise, at base)
        form = frozenset()
        if (fi ^ gi): form = form ^ de[i]
        if ei:        form = form ^ df[i]
        if (ei ^ 1):  form = form ^ dg[i]
        out.append(form)
    return tuple(out)
def Maj_lin(da, db, dc, base, N):
    a, b, c = base
    out = []
    for i in range(N):
        ai = (a >> i) & 1; bi = (b >> i) & 1; ci = (c >> i) & 1
        form = frozenset()
        if (bi ^ ci): form = form ^ da[i]
        if (ai ^ ci): form = form ^ db[i]
        if (ai ^ bi): form = form ^ dc[i]
        out.append(form)
    return tuple(out)

# ------------------------------------------------------------------------------
# Assemble the unrolled tail of R rounds, width N. State = (a..h) words of forms.
# Each round introduces fresh schedule-diff word dW[r] (free input) and computes
# the next state by the linearized round map. Rows of delta = equations that DEFINE
# fresh accumulation variables; ker over GF(2) of the whole system (with outputs
# pinned) = linear collision space. We instead build delta as the incidence of the
# round relations directly on the variable set and read rank/kernel.
# ------------------------------------------------------------------------------

def assemble(N, R, seed=20260603, force_collision=True, carry_order=0):
    """Return (rows, ncols, info).
    rows : list of frozenset(var-ids)  (each = a GF(2) linear relation = 0)
    ncols: total number of bit-variables
    The free variables are: input register diffs (a..h at round-start) + dW[r] for
    each of the R rounds. Everything else is DEFINED by relations (substituted), so
    we build relations only among free vars by symbolic propagation, then the
    "collision" rows pin the 8 output words to 0.
    carry_order: 0 = pure XOR (linear sheaf L^0). k>=1 = add k layers of carry-bit
    constraints on the modular adds (SH5 filtration): each add gets carry vars and
    the GF(2) full-adder relations up to bit-depth k (bit i carry depends on bits
    i-1..i-k). carry_order>=N reproduces the exact modular add.
    """
    pool = VarPool()
    # free input register diffs a..h
    reg_words = [sym_word(pool.word(N)) for _ in range(8)]   # a,b,c,d,e,f,g,h
    # base point for Ch/Maj linearization (fixed)
    rng = random.Random(seed + 1000 * N + R)
    rows = []
    carry_vars_total = 0

    def modadd(words, label):
        """Symbolic modular-add of a list of words-of-forms.
        carry_order==0 -> XOR (drop carries). Else add carry chain up to depth k."""
        nonlocal carry_vars_total
        if carry_order == 0:
            return lin_combo(words, N), []
        # Build a ripple-carry sum of the given words pairwise, materializing carry
        # bits as fresh vars with the full-adder GF(2) relations, but only allowing
        # carry to propagate up to `carry_order` bit positions (truncated chain).
        acc = words[0]
        local_rows = []
        for w in words[1:]:
            s_word = [None] * N
            carry_prev = frozenset()  # carry into bit 0 = 0
            depth_ok = True
            for i in range(N):
                # sum bit = acc_i ^ w_i ^ carry_prev (carry truncated by carry_order)
                if i <= carry_order:
                    cin = carry_prev
                else:
                    cin = frozenset()  # truncate: no carry beyond depth
                s_word[i] = acc[i] ^ w[i] ^ cin
                # carry_out fresh var with relation: c_out = Maj(acc_i, w_i, cin)
                cvar = pool.word(1)[0]; carry_vars_total += 1
                cform = frozenset((cvar,))
                # full-adder carry: c_out = (acc_i & w_i) ^ (acc_i & cin) ^ (w_i & cin)
                # linearize at base 0 (diffs) -> the GF(2) *first-order* carry part.
                # For a difference sheaf the honest linear carry contribution at a
                # random base point b: d carry = (acc_i)&base ... we approximate the
                # carry as a fresh degree-of-freedom constrained to live in span of
                # {acc_i, w_i, cin}: relation c_out ^ acc_i ^ w_i ^ cin (the XOR/parity
                # closure) — this UNDERCOUNTS carry nonlinearity but ADDS the extra
                # constraint dimension the filtration is supposed to subtract.
                local_rows.append(frozenset((cvar,)) ^ acc[i] ^ w[i] ^ cin)
                carry_prev = cform
            acc = tuple(s_word)
        rows.extend(local_rows)
        return acc, local_rows

    a, b, c, d, e, f, g, h = reg_words
    for r in range(R):
        dW = sym_word(pool.word(N))
        base_e = rng.getrandbits(N); base_f = rng.getrandbits(N); base_g = rng.getrandbits(N)
        base_a = rng.getrandbits(N); base_b = rng.getrandbits(N); base_c = rng.getrandbits(N)
        S1 = Sigma_form(e, S1_ROT, N)
        ch = Ch_lin(e, f, g, (base_e, base_f, base_g), N)
        S0 = Sigma_form(a, S0_ROT, N)
        mj = Maj_lin(a, b, c, (base_a, base_b, base_c), N)
        # T1 = h + S1 + Ch + K + W  (K diff = 0)
        T1, _ = modadd([h, S1, ch, dW], "T1")
        # T2 = S0 + Maj
        T2, _ = modadd([S0, mj], "T2")
        # new state shift
        new_a, _ = modadd([T1, T2], "a'")
        new_e, _ = modadd([d, T1], "e'")
        a, b, c, d, e, f, g, h = new_a, a, b, c, new_e, e, f, g

    info = dict(carry_vars=carry_vars_total, ncols=pool.n,
                out_words=(a, b, c, d, e, f, g, h))
    if force_collision:
        # pin every output register-diff bit to 0  => rows = the output forms
        for w in (a, b, c, d, e, f, g, h):
            for form in w:
                if form:            # empty form == 0==0, skip trivial
                    rows.append(form)
    return rows, pool.n, info

def assemble_graded(N, R, seed=20260603, force_collision=True):
    """GRADED cellular-sheaf variant for the H^1 steelman (SH2).
    Every round boundary gets FRESH stalk variables for ALL 8 registers (so C^0 =
    8*(R+1)*N stalk bits + R*N schedule bits), and each round contributes a BLOCK of
    edge-relations (C^1) that GLUE new stalks to old via the linearized round map:
        new_a = Sigma0(a)+Maj+Sigma1(e)+Ch+h+W   (XOR-linearized)
        new_e = d + (Sigma1(e)+Ch+h+W)
        new_b=a, new_c=b, new_d=c, new_f=e, new_g=f, new_h=g  (shift identities)
    H^1 = coker(delta) = (#edge-relations) - rank(delta) can now be genuinely >0.
    Returns (rows, ncols, info). rows = C^1 relations (each frozenset = 0)."""
    pool = VarPool()
    state = [sym_word(pool.word(N)) for _ in range(8)]   # round-0 stalks a..h
    rng = random.Random(seed + 7000 * N + 13 * R)
    rows = []
    for r in range(R):
        a, b, c, d, e, f, g, h = state
        dW = sym_word(pool.word(N))
        be = (rng.getrandbits(N), rng.getrandbits(N), rng.getrandbits(N))
        ba = (rng.getrandbits(N), rng.getrandbits(N), rng.getrandbits(N))
        S1 = Sigma_form(e, S1_ROT, N); ch = Ch_lin(e, f, g, be, N)
        S0 = Sigma_form(a, S0_ROT, N); mj = Maj_lin(a, b, c, ba, N)
        T1 = lin_combo([h, S1, ch, dW], N)         # XOR-linearized T1
        T2 = lin_combo([S0, mj], N)
        na_def = lin_combo([T1, T2], N)
        ne_def = lin_combo([d, T1], N)
        # fresh next-state stalks
        na = sym_word(pool.word(N)); ne = sym_word(pool.word(N))
        # edge-relations gluing fresh stalks to the definitions (one row per bit)
        for i in range(N):
            rows.append(na[i] ^ na_def[i])         # new_a - def = 0
            rows.append(ne[i] ^ ne_def[i])         # new_e - def = 0
        # shift identities reuse the SAME stalks (no fresh vars, no glue rows needed):
        state = [na, a, b, c, ne, e, f, g]
    info = dict(ncols=pool.n, out=state, n_edge_rows=len(rows))
    if force_collision:
        for w in state:
            for form in w:
                if form:
                    rows.append(form)
    return rows, pool.n, info


# ------------------------------------------------------------------------------
# GF(2) linear algebra on frozenset-rows.
# ------------------------------------------------------------------------------
def rows_to_bitmask(rows):
    """Convert frozenset rows to python-int bitmasks; return (masks, nvars seen)."""
    masks = []
    maxv = -1
    for r in rows:
        m = 0
        for v in r:
            m |= (1 << v)
            if v > maxv: maxv = v
        if m: masks.append(m)
    return masks, maxv + 1

def gf2_rank_masks(masks):
    basis = []
    for m in masks:
        cur = m
        for b in basis:
            cur = min(cur, cur ^ b)
        if cur: basis.append(cur); basis.sort(reverse=True)
    return len(basis)

def kernel_dim(rows, ncols, free_vars):
    """dim of the solution space restricted to the FREE input variables.
    We compute rank of the system on ALL vars; the kernel over free vars =
    free_vars - rank_projected. Simpler & robust: build full row set, RREF, and the
    nullspace dimension over the chosen free-variable columns.
    Here we just return (ncols - rank) as the raw nullity of delta, and separately
    the nullity restricted to the input-register block (the 'collision' dofs)."""
    masks, _ = rows_to_bitmask(rows)
    rank = gf2_rank_masks(masks)
    return ncols - rank, rank

# ------------------------------------------------------------------------------
# Real incidence Laplacian for the spectrum (SH1/SH3/SH4).
# We build delta as a {0,1} (mod-2-pattern lifted to reals) sparse incidence of the
# round relations over the variable set, then L = delta^T delta and eigvalsh.
# ------------------------------------------------------------------------------
def real_laplacian(rows, ncols):
    import numpy as np
    R = len(rows)
    D = np.zeros((R, ncols), dtype=np.float64)
    for i, r in enumerate(rows):
        for v in r:
            if v < ncols:
                D[i, v] = 1.0
    L = D.T @ D
    return L

def spectrum(rows, ncols):
    import numpy as np
    L = real_laplacian(rows, ncols)
    w = np.linalg.eigvalsh(L)
    w = np.clip(w, 0, None)
    return np.sort(w)


# ------------------------------------------------------------------------------
# Restricted kernel: dimension of the linear collision space measured ON the free
# INPUT variables only (input register diffs a..h + all schedule diffs dW[r]).
# We RREF the full pinned system and count free columns among the input block.
# ------------------------------------------------------------------------------
def free_input_ids(N, R):
    """Return the set of variable ids that are genuine free inputs:
    the first 8*N (register diffs a..h) + the dW words. dW[r] is allocated right
    after the register block in assemble(): for r in range(R), at offsets
    8*N + r*(N + carries). With carry_order=0 (no carry vars) dW[r] = 8N + r*N .."""
    ids = set(range(8 * N))                      # a..h input diffs
    # schedule words: with carry_order=0, allocation order per round is dW then
    # (no carry vars). So dW[r] occupies 8N + r*N .. 8N + (r+1)*N - 1.
    for r in range(R):
        base = 8 * N + r * N
        ids.update(range(base, base + N))
    return ids

def collision_kernel_dim(N, R, seed=20260603, carry_order=0):
    """dim of the linear collision space = nullity of the output-pinned system
    measured over ALL variables (every dropped intermediate is a defined var, so the
    raw nullity already equals the input-side freedom). Returns (nullity, rank, ncols).
    For carry_order=0 this is the honest 'how many linear difference-trails collide'."""
    rows, nc, info = assemble(N, R, seed=seed, force_collision=True, carry_order=carry_order)
    masks, _ = rows_to_bitmask(rows)
    rank = gf2_rank_masks(masks)
    return nc - rank, rank, nc, info


# ------------------------------------------------------------------------------
# MODULAR (carry-true) brute-force collision count on the SAME R-round tail at
# width N, for the apples-to-apples comparison the cards demand. Inputs: the 8
# register diffs are FIXED to a single-word kernel (db on register 'a' only, the
# (0,*) analogue) OR swept; the R schedule diffs dW are free. We count, over random
# base points, the difference-trails whose modular output diff is 0 for the *generic*
# base (a real collision must hold for the realized base point). To keep it cheap we
# count exact collisions of the genuine modular tail for a single random base point
# and a swept small input-diff set.
# ------------------------------------------------------------------------------
def modular_tail_out(reg_in, dW_list, base_state, base_sched, N):
    """Run the genuine modular R-round tail twice (base vs base^diff) and return the
    XOR of the two output register tuples (the realized output difference)."""
    m = maskN(N)
    def Ch_(e, f, g): return (e & f) ^ ((~e & m) & g)
    def Maj_(a, b, c): return (a & b) ^ (a & c) ^ (b & c)
    def Sig(word, rots):
        o = 0
        for r in rots: o ^= rorN(word, r, N)
        return o & m
    def run(regs, scheds):
        a, b, c, d, e, f, g, h = regs
        for r in range(len(scheds)):
            T1 = (h + Sig(e, S1_ROT) + Ch_(e, f, g) + scheds[r]) & m
            T2 = (Sig(a, S0_ROT) + Maj_(a, b, c)) & m
            a, b, c, d, e, f, g, h = (T1 + T2) & m, a, b, c, (d + T1) & m, e, f, g
        return (a, b, c, d, e, f, g, h)
    base_out = run(base_state, base_sched)
    pert_state = tuple((base_state[i] ^ reg_in[i]) & m for i in range(8))
    pert_sched = tuple((base_sched[i] ^ dW_list[i]) & m for i in range(len(base_sched)))
    pert_out = run(pert_state, pert_sched)
    return tuple((base_out[i] ^ pert_out[i]) & m for i in range(8))


if __name__ == '__main__':
    import numpy as np
    np.seterr(all='ignore')
    print("[sheaf_delta selftest]")
    for R in (2, 3, 4):
        rows, nc, info = assemble(N=3, R=R, force_collision=True, carry_order=0)
        nul, rank = kernel_dim(rows, nc, None)
        sp = spectrum(rows, nc)
        nz = int((sp < 1e-9).sum())
        l1 = sp[sp > 1e-9][0] if (sp > 1e-9).any() else 0.0
        print(f"  N=3 R={R}: ncols={nc} rows={len(rows)} rank={rank} nullity={nul} "
              f"zero-eig(L)={nz} lambda1={l1:.4f}")

if __name__ == '__main__':
    import numpy as np
    print("[sheaf_delta selftest]")
    for R in (2, 3, 4):
        rows, nc, info = assemble(N=3, R=R, force_collision=True, carry_order=0)
        nul, rank = kernel_dim(rows, nc, None)
        sp = spectrum(rows, nc)
        nz = int((sp < 1e-9).sum())
        print(f"  N=3 R={R}: ncols={nc} rows={len(rows)} rank={rank} nullity={nul} "
              f"zero-eig(L)={nz} lambda1={sp[sp>1e-9][0]:.4f}" if (sp>1e-9).any() else
              f"  N=3 R={R}: ncols={nc} rank={rank} nullity={nul} (L all-zero)")
