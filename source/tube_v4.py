"""v4: reinforced tube. Same threads/collar as v3 (cap, sleeve, dolphin socket unchanged)."""
import numpy as np, manifold3d as mf
import build_all as B
from design import cyl, revolve_profile

CAV_R4 = 26.6 / 2          # bore 27.2 -> 26.6 (tablet 25.2): thicker wall at the thread roots
SLOT4 = 18.0               # slot width 26 -> 18 deg: ribs 34 -> 42 deg wide
MARGIN4, GAP4 = 9.0, 7.0   # solid bands: ends 5 -> 9 mm, between rows 4.5 -> 7 mm
TAPER = 3.0                # slot ends taper over 3 mm (no sharp corners, no bridges)


def rows4(z0, length, n=3):
    rh = (length - 2 * MARGIN4 - (n - 1) * GAP4) / n
    out, z = [], z0 + MARGIN4
    for _ in range(n):
        out.append((z, z + rh)); z += rh + GAP4
    return out


def wedge(c, ang, z0, z1, rmax=40.0):
    a0, a1 = np.radians(c - ang / 2), np.radians(c + ang / 2)
    poly = [(0, 0)] + [(rmax * np.cos(a), rmax * np.sin(a)) for a in np.linspace(a0, a1, 10)]
    return mf.Manifold.extrude(mf.CrossSection([poly]), z1 - z0).translate((0, 0, z0))


def tapered_slots(z0, z1, ang=SLOT4, n=6, steps=6):
    cuts = []
    for i in range(n):
        c = i * 360.0 / n
        cuts.append(wedge(c, ang, z0 + TAPER, z1 - TAPER))
        for k in range(steps):                       # stepped V ends
            f = 1 - (k + 1) / (steps + 1)
            h = TAPER / steps
            cuts.append(wedge(c, ang * f, z0 + TAPER - (k + 1) * h, z0 + TAPER - k * h))
            cuts.append(wedge(c, ang * f, z1 - TAPER + k * h, z1 - TAPER + (k + 1) * h))
    return mf.Manifold.batch_boolean(cuts, mf.OpType.Add)


def tube4(sleeve_len=B.SLEEVE_L, nrows=3):
    top_th = B.male_thread(0, B.T_THREAD, lead_at_top=False)
    zc0 = B.T_THREAD
    collar = revolve_profile([(B.TUBE_R - 1, zc0), (B.TUBE_R, zc0), (B.COLLAR_R, zc0 + B.COLLAR_CONE),
                              (B.COLLAR_R, zc0 + B.COLLAR_CONE + B.COLLAR_CYL),
                              (B.TUBE_R - 1, zc0 + B.COLLAR_CONE + B.COLLAR_CYL)])
    zs0 = zc0 + B.COLLAR_CONE + B.COLLAR_CYL
    zb0 = zs0 + sleeve_len + B.SLEEVE_GAP
    body = cyl(zb0 - zc0 + 0.02, B.TUBE_R, z0=zc0 - 0.01)
    bot_th = B.male_thread(zb0 - 0.01, B.T_THREAD + 0.01, lead_at_top=True)
    zend = zb0 + B.T_THREAD
    t = top_th + collar + body + bot_th
    t = t - cyl(zend + 2, CAV_R4, z0=-1)
    t = t - cyl(1.0, CAV_R4 + 1.0, CAV_R4, z0=-0.001)
    t = t - cyl(1.0, CAV_R4, CAV_R4 + 1.0, z0=zend - 0.999)
    keep_core = cyl(zend + 4, CAV_R4 - 0.5, z0=-2)
    for (a, b) in rows4(zs0, sleeve_len, nrows):
        t = t - (tapered_slots(a, b) - keep_core)
    ticks = []
    for deg in range(0, 360, 10):
        k = deg % 60
        L = 3.5 if k == 0 else (2.3 if k == 30 else 1.1)
        w, d = 0.9, 0.7
        tk = mf.Manifold.cube((2 * d, w, L + 0.01)).translate((B.COLLAR_R - d, -w / 2, zs0 - L))
        ticks.append(tk.rotate((0, 0, deg)))
    t = t - mf.Manifold.batch_boolean(ticks, mf.OpType.Add)
    return t, dict(zs0=zs0, zb0=zb0, zend=zend)
