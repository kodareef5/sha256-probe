"""
_qw_kit.py — shared Szegedy-discriminant helpers for Wave-7 quantum-walk cards
(W7-QW1..QW5). READ-ONLY toward sha256_review; built on shabridge.

THE OBJECT (all five cards share it):
  - P = a column-stochastic transition matrix (a classical Markov/diff-config chain).
  - Szegedy discriminant D = sqrt(P .* P^T)  (ELEMENTWISE/Hadamard geometric mean).
    Note: the canonical Szegedy discriminant is D_ij = sqrt(P_ij * P_ji). When P is
    *reversible* (detailed balance), D is symmetric and its singular values are
    |eigenvalues of P| -> "D just sqrt-relabels P". The cards' whole bet is that the
    non-invertible feed-forward makes P NON-reversible so D != relabel(P). Every probe
    therefore reports BOTH spectra and the divergence.
  - phase gap   = 2*sqrt(1 - s2)  where s2 = 2nd-largest singular value of D (Szegedy).
  - top edge    = s_max(D).
  - corank(D)   = # of (near-)zero singular values.
"""
import sys, numpy as np
sys.path.insert(0, '/Users/mac/Desktop/sha256_theory_lab/wild_angles/probes/kernels')
import shabridge as sb  # noqa: F401


def discriminant(P):
    """Szegedy discriminant D_ij = sqrt(P_ij * P_ji) (Hadamard geometric mean)."""
    P = np.asarray(P, dtype=float)
    return np.sqrt(np.maximum(P * P.T, 0.0))


def svals(M):
    """Singular values, descending."""
    return np.linalg.svd(np.asarray(M, dtype=float), compute_uv=False)


def perron(P):
    """|eigenvalues| of P, descending (the 'reversible relabel' reference spectrum)."""
    ev = np.abs(np.linalg.eigvals(np.asarray(P, dtype=float)))
    return np.sort(ev)[::-1]


def is_reversible(P, tol=1e-9):
    """A column-stochastic P is reversible iff it has a stationary pi with
    pi_i P_ji = pi_j P_ij. We test the WEAKER necessary condition that D's
    singular values equal |eig(P)| (the only thing the cards care about: does
    D *relabel* P). Returns max abs gap between sorted s(D) and |eig(P)|."""
    sD = svals(discriminant(P))
    eP = perron(P)
    k = min(len(sD), len(eP))
    return float(np.max(np.abs(sD[:k] - eP[:k])))


def szegedy_phase_gap(P):
    """Szegedy phase gap = 2*sqrt(1 - s2), s2 = 2nd singular value of D.
    (For the top eigenphase; small gap = slow walk = the 'wall'.)"""
    sD = svals(discriminant(P))
    s2 = sD[1] if len(sD) > 1 else 0.0
    return 2.0 * np.sqrt(max(0.0, 1.0 - s2)), s2, sD


def corank(M, thr):
    """# singular values < thr * s_max (i.e. relative threshold)."""
    sv = svals(M)
    smax = sv[0] if len(sv) else 0.0
    if smax <= 0:
        return len(sv), sv
    return int(np.sum(sv < thr * smax)), sv
