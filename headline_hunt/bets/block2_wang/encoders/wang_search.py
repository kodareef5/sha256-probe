#!/usr/bin/env python3
"""Bit-level constraint network for SHA-256 differential characteristics.

Increment 4 of the block2_wang Wang trail engine. The engine primitives
(wang_trail_engine.py) give sound forward + backward refinement on individual
operations; this module wires a whole multi-round characteristic into a graph of
bit-condition NODES connected by per-operation CONSTRAINTS, and runs a worklist
arc-consistency fixpoint (propagate-and-refine) over the network. A guess-and-
determine SEARCH (next increment) sits on top of propagate().

Node  = a single bit-condition, keyed (word_name, bit_index); value = a 4-bit mask
        over pair-values (x,x*) (see wang_trail_engine.COND).
Constraint = a list of node keys + a refine fn that intersects each node's mask
        with the values participating in some feasible assignment. An empty mask
        anywhere => the characteristic is infeasible (contradiction).

This increment: the network builder + propagate() fixpoint, validated against the
lib.sha256 concrete oracle (a real trail is a fixpoint; a corrupted output is
caught). Search is deliberately deferred so each commit stays fully tested.
"""
import os
import sys
from itertools import product

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "../../../..")))

from wang_trail_engine import (  # noqa: E402
    COND, N, bits, sym, _XOR, _CH, _MAJ, _refine_add_bit,
)


# ---- per-constraint refinement (arc-consistency) ----

def refine_parity(masks):
    """Linear (XOR / Sigma / sigma) over k<=4 bit-nodes: total GF(2) sum = 0 in BOTH
    the x-plane and the x*-plane (an output bit is the XOR of its source bits)."""
    surv = [0] * len(masks)
    for combo in product(*[bits(m) for m in masks]):
        xx = xs = 0
        for v in combo:
            xx ^= v >> 1
            xs ^= v & 1
        if xx == 0 and xs == 0:
            for j, v in enumerate(combo):
                surv[j] |= 1 << v
    return surv


def _refine_func3(masks, op):
    """out = op(x,y,z) bitwise (Ch, Maj). nodes order [out, x, y, z]."""
    mo, mx, my, mz = masks
    no = nx = ny = nz = 0
    for vx in bits(mx):
        x, xs = vx >> 1, vx & 1
        for vy in bits(my):
            y, ys = vy >> 1, vy & 1
            for vz in bits(mz):
                z, zs = vz >> 1, vz & 1
                ov = (op(x, y, z) << 1) | op(xs, ys, zs)
                if (mo >> ov) & 1:
                    no |= 1 << ov
                    nx |= 1 << vx
                    ny |= 1 << vy
                    nz |= 1 << vz
    return [no, nx, ny, nz]


def refine_ch(masks):
    return _refine_func3(masks, _CH)


def refine_maj(masks):
    return _refine_func3(masks, _MAJ)


def refine_adder(masks):
    """Full-adder bit: nodes order [a, b, cin, sum, cout]."""
    return list(_refine_add_bit(*masks))


def refine_eq(masks):
    m = masks[0] & masks[1]
    return [m, m]


# ---- the network ----

class Net:
    def __init__(self):
        self.var = {}          # node key -> mask
        self.cons = []         # list of (nodes, refine_fn)
        self.watch = {}        # node key -> [constraint indices]

    def _ensure(self, key):
        if key not in self.var:
            self.var[key] = COND["?"]

    def pin(self, key, mask):
        self._ensure(key)
        self.var[key] &= mask

    def add_con(self, nodes, refn):
        for nd in nodes:
            self._ensure(nd)
        idx = len(self.cons)
        self.cons.append((nodes, refn))
        for nd in nodes:
            self.watch.setdefault(nd, []).append(idx)

    def propagate(self):
        """Worklist arc-consistency to fixpoint. Returns True iff contradiction."""
        q = list(range(len(self.cons)))
        inq = set(q)
        while q:
            idx = q.pop()
            inq.discard(idx)
            nodes, refn = self.cons[idx]
            cur = [self.var[n] for n in nodes]
            new = refn(cur)
            for nd, old, nw in zip(nodes, cur, new):
                if nw != old:
                    self.var[nd] = nw
                    if nw == 0:
                        return True
                    for c2 in self.watch[nd]:
                        if c2 not in inq:
                            q.append(c2)
                            inq.add(c2)
        return any(m == 0 for m in self.var.values())

    # convenience
    def pin_word(self, name, x, xstar):
        for i in range(N):
            v = (((x >> i) & 1) << 1) | ((xstar >> i) & 1)
            self.pin((name, i), 1 << v)

    def word_pair_contained(self, name, x, xstar):
        for i in range(N):
            v = (((x >> i) & 1) << 1) | ((xstar >> i) & 1)
            if not (self.var.get((name, i), 0) >> v) & 1:
                return False
        return True


# ---- builders for SHA-256 operations (rotations: out[i] = in[(i+r) % N]) ----

def link_linear(net, src, dst, rots, shrs=()):
    """dst[i] = XOR over rotations rots and shifts shrs of src.  rots: list of r
    (ROTR); shrs: list of s (SHR, drops out-of-range)."""
    for i in range(N):
        nodes = [(dst, i)] + [(src, (i + r) % N) for r in rots]
        for s in shrs:
            if i + s < N:
                nodes.append((src, i + s))
        net.add_con(nodes, refine_parity)


def link_func3(net, x, y, z, out, refn):
    for i in range(N):
        net.add_con([(out, i), (x, i), (y, i), (z, i)], refn)


def link_add(net, an, bn, sn, carry_name, cin0="0"):
    net.pin((carry_name, 0), COND[cin0])
    for i in range(N):
        net.add_con([(an, i), (bn, i), (carry_name, i), (sn, i), (carry_name, i + 1)],
                    refine_adder)


def link_eq(net, an, bn):
    for i in range(N):
        net.add_con([(an, i), (bn, i)], refine_eq)


def build_round(net, t, kconst):
    """Wire one SHA-256 round t: state {a..h}{t} + W{t} -> {a..h}{t+1}."""
    a, b, c, d, e, f, g, h = (f"{x}{t}" for x in "abcdefgh")
    na, nb, nc, nd, ne, nf, ng, nh = (f"{x}{t+1}" for x in "abcdefgh")
    e1, chv, e0, mj = f"e1_{t}", f"ch_{t}", f"e0_{t}", f"maj_{t}"
    T1, T2, W, Kn = f"T1_{t}", f"T2_{t}", f"W{t}", f"Kc{t}"
    for i in range(N):
        net.pin((Kn, i), COND["1"] if (kconst >> i) & 1 else COND["0"])
    link_linear(net, e, e1, [6, 11, 25])               # Sigma1
    link_linear(net, a, e0, [2, 13, 22])               # Sigma0
    link_func3(net, e, f, g, chv, refine_ch)
    link_func3(net, a, b, c, mj, refine_maj)
    # T1 = h + e1 + ch + K + W  (chain of 2-input adds)
    ps1, ps2, ps3 = f"ps1_{t}", f"ps2_{t}", f"ps3_{t}"
    link_add(net, h, e1, ps1, f"c0_{t}")
    link_add(net, ps1, chv, ps2, f"c1_{t}")
    link_add(net, ps2, Kn, ps3, f"c2_{t}")
    link_add(net, ps3, W, T1, f"c3_{t}")
    link_add(net, e0, mj, T2, f"c4_{t}")
    link_add(net, T1, T2, na, f"c5_{t}")               # a' = T1 + T2
    link_add(net, d, T1, ne, f"c6_{t}")                # e' = d + T1
    link_eq(net, nb, a)
    link_eq(net, nc, b)
    link_eq(net, nd, c)
    link_eq(net, nf, e)
    link_eq(net, ng, f)
    link_eq(net, nh, g)


def build_rounds(net, R, kconsts):
    for t in range(R):
        build_round(net, t, kconsts[t])


# ---- concrete oracle (lib.sha256) for validation ----

def concrete_rounds(st0, msgs, kconsts):
    """Run R concrete rounds; return list of states st0..stR (each an 8-tuple)."""
    import lib.sha256 as L

    states = [list(st0)]
    st = list(st0)
    for t in range(len(msgs)):
        a, b, c, d, e, f, g, h = st
        t1 = L.add(h, L.Sigma1(e), L.Ch(e, f, g), kconsts[t], msgs[t])
        t2 = L.add(L.Sigma0(a), L.Maj(a, b, c))
        st = [L.add(t1, t2), a, b, c, L.add(d, t1), e, f, g]
        states.append(st)
    return states


def _selftest():
    import random
    import lib.sha256 as L

    rng = random.Random(20260526)
    R = 3
    kconsts = L.K[:R]
    REG = "abcdefgh"

    # (1) SOUNDNESS: a real differential trail must be a network fixpoint (no contradiction),
    #     and forward propagation from pinned inputs must CONTAIN the true outputs.
    for _ in range(300):
        st0 = [rng.getrandbits(N) for _ in range(8)]
        msgs = [rng.getrandbits(N) for _ in range(R)]
        dst0 = [rng.getrandbits(N) for _ in range(8)]
        dmsg = [rng.getrandbits(N) for _ in range(R)]
        st0s = [x ^ dx for x, dx in zip(st0, dst0)]
        msgss = [w ^ dw for w, dw in zip(msgs, dmsg)]
        states = concrete_rounds(st0, msgs, kconsts)
        statess = concrete_rounds(st0s, msgss, kconsts)

        net = Net()
        build_rounds(net, R, kconsts)
        for j in range(8):
            net.pin_word(f"{REG[j]}0", states[0][j], statess[0][j])
        for t in range(R):
            net.pin_word(f"W{t}", msgs[t], msgss[t])
        contra = net.propagate()
        assert not contra, "real trail wrongly rejected"
        for t in range(1, R + 1):
            for j in range(8):
                assert net.word_pair_contained(f"{REG[j]}{t}", states[t][j], statess[t][j]), \
                    (t, REG[j])
        # forward determined the final state fully (inputs were concrete)
        for j in range(8):
            for i in range(N):
                assert bin(net.var[(f"{REG[j]}{R}", i)]).count("1") == 1

    # (2) CONTRADICTION: corrupt one output bit -> the network must detect infeasibility.
    caught = 0
    for _ in range(200):
        st0 = [rng.getrandbits(N) for _ in range(8)]
        msgs = [rng.getrandbits(N) for _ in range(R)]
        states = concrete_rounds(st0, msgs, kconsts)  # zero-difference trail
        net = Net()
        build_rounds(net, R, kconsts)
        for j in range(8):
            net.pin_word(f"{REG[j]}0", states[0][j], states[0][j])
        for t in range(R):
            net.pin_word(f"W{t}", msgs[t], msgs[t])
        # force a' at round 0, bit b to DIFFER (impossible for a zero-diff trail)
        b = rng.randrange(N)
        net.pin(("a1", b), COND["x"])
        if net.propagate():
            caught += 1
    assert caught == 200, f"only caught {caught}/200 planted contradictions"

    print("wang_search increment-4 (constraint network + fixpoint) self-tests: PASS")
    print(f"  R={R}: 300 trails are fixpoints w/ forward-determined outputs; "
          f"200/200 planted contradictions caught")


if __name__ == "__main__":
    _selftest()
