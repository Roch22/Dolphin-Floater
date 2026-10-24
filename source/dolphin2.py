"""Sleek dolphin riding a small wave base (original design). x forward, z up, belly/wave base on z=0."""
import numpy as np
from dolphin import smin, smax, round_cone, ellipsoid, rot, mesh_from_sdf

W = 1.28   # body width factor


def chain_sdf(q, pts, k):
    d = None
    for (a, ra), (b, rb) in zip(pts[:-1], pts[1:]):
        di = round_cone(q, a, b, ra, rb)
        d = di if d is None else smin(d, di, k)
    return d


def squash(p, axis, f):
    q = p.copy(); q[:, axis] = q[:, axis] / f
    return q


def dolphin2_sdf(p):
    # ---- body: one smooth streamlined sweep (dense spine, smooth radius) ----
    from scipy.interpolate import CubicSpline
    kx = np.array([-86, -70, -48, -20, 8, 34, 54])
    kz = CubicSpline(kx, [44, 38, 30, 25, 24, 27, 32])
    kr = CubicSpline(kx, [4.0, 7.5, 15.0, 24.0, 26.5, 24.5, 18.5])
    kw = CubicSpline(kx, [1.0, 1.08, 1.18, 1.26, 1.28, 1.24, 1.15])
    xs = np.linspace(-86, 54, 48)
    q = p.copy()
    q[:, 1] = p[:, 1] / kw(np.clip(p[:, 0], -86, 54))
    body = None
    for a, b in zip(xs[:-1], xs[1:]):
        di = round_cone(q, (a, 0, float(kz(a))), (b, 0, float(kz(b))), float(kr(a)), float(kr(b)))
        body = di if body is None else np.minimum(body, di)
    # melon (rounded forehead) and beak
    melon = ellipsoid(p, np.array([62, 0, 40]), np.array([15, 15.5, 13]))
    d = smin(body, melon, 7.0)
    beak = round_cone(p, (70, 0, 33), (94, 0, 34.5), 7.5, 3.6)
    d = smin(d, beak, 5.0)
    # ---- tall swept-back dorsal fin (thin, curved) ----
    fq = squash(p, 1, 0.38)
    fin = round_cone(fq, (8, 0, 44), (-16, 0, 84), 14.0, 1.6) * 0.38   # one straight smooth taper
    fin = smax(fin, -(p[:, 2] - 40), 3.0)
    d = smin(d, fin, 5.0)
    # ---- pointed pectoral flippers, swept back and down ----
    for s in (1, -1):
        fl = chain_sdf(squash(p, 2, 0.4), [((36, s * 27, 17 / 0.4), 10.0), ((25, s * 41, 11 / 0.4), 7.5),
                                           ((10, s * 55, 5 / 0.4), 2.0)], 4.0) * 0.4
        d = smin(d, fl, 4.0)
    # ---- forked tail flukes, tilted up so they print ----
    for s in (1, -1):
        tq = rot(p, np.array([-84, 0, 44]), 'y', 34)
        tq = squash(tq, 2, 0.32)
        fk = chain_sdf(tq, [((-82, 0, 44 / 0.32), 5.0), ((-90, s * 9, 44 / 0.32), 8.5),
                            ((-99, s * 17, 44 / 0.32), 6.0), ((-110, s * 25, 44 / 0.32), 1.5)], 4.0) * 0.32
        d = smin(d, fk, 3.0)
    # ---- eyes ----
    for s in (1, -1):
        d = smin(d, ellipsoid(p, np.array([56, s * 19.6, 36.5]), np.array([5.0, 3.2, 5.5])), 1.2)
    # ---- wave base under the belly (hides the socket, gives a flat print base) ----
    base = ellipsoid(p, np.array([6, 0, 3]), np.array([46, 36, 10]))
    d = smin(d, base, 8.0)
    return d


def details2(p):
    """cuts: pupils + smile line along the beak."""
    cuts = []
    for s in (1, -1):
        cuts.append(ellipsoid(p, np.array([58.6, s * 22.3, 37.4]), np.array([2.6, 1.8, 3.2])))
    line = [(95.5, 0, 33.2), (88, 4.3, 32.0), (80, 6.4, 31.2), (72, 8.6, 31.2), (66, 11.2, 32.8)]
    m = None
    for s in (1, -1):
        seq = [(x, s * y, z) for x, y, z in line]
        for a, b in zip(seq[:-1], seq[1:]):
            r = round_cone(p, a, b, 0.75, 0.75)
            m = r if m is None else np.minimum(m, r)
    cuts.append(m)
    return np.min(np.stack(cuts), 0)
