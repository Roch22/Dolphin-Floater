"""Original cartoon dolphin float body as a signed distance field -> mesh.
x = forward (beak +x), y = left, z = up. Belly is cut flat at z = 0 later."""
import numpy as np
from skimage.measure import marching_cubes
import trimesh


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def round_cone(p, a, b, r1, r2):
    """IQ sdRoundCone between points a,b with radii r1,r2 (vectorised)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ba = b - a; l2 = ba @ ba; rr = r1 - r2; a2 = l2 - rr * rr; il2 = 1.0 / l2
    pa = p - a
    y = pa @ ba
    z = y - l2
    xv = pa * l2 - y[:, None] * ba
    x2 = np.einsum('ij,ij->i', xv, xv)
    y2 = y * y * l2
    z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    out = np.empty(len(p))
    c1 = np.sign(z) * a2 * z2 > k
    c2 = np.sign(y) * a2 * y2 < k
    out[:] = (np.sqrt(x2 * a2 * il2) + y * rr) * il2 - r1
    out[c1] = np.sqrt(x2[c1] + z2[c1]) * il2 - r2
    out[c2] = np.sqrt(x2[c2] + y2[c2]) * il2 - r1
    return out


def ellipsoid(p, c, r):
    q = (p - c) / r
    k0 = np.linalg.norm(q, axis=1)
    k1 = np.linalg.norm(q / r, axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def rot(p, c, axis, deg):
    """rotate points p about centre c (inverse map for SDF eval)."""
    t = np.radians(-deg)
    q = p - c
    cs, sn = np.cos(t), np.sin(t)
    if axis == 'x': R = np.array([[1, 0, 0], [0, cs, -sn], [0, sn, cs]])
    if axis == 'y': R = np.array([[cs, 0, sn], [0, 1, 0], [-sn, 0, cs]])
    if axis == 'z': R = np.array([[cs, -sn, 0], [sn, cs, 0], [0, 0, 1]])
    return q @ R.T + c


S = 1.0          # global scale
WIDEN = 1.18     # body a bit wider than tall


def dolphin_sdf(p):
    p = p / S
    q = p.copy(); q[:, 1] = q[:, 1] / WIDEN          # widen body
    # --- body chain (tail -> head) ---
    chain = [((-74, 0, 50), 5.5), ((-60, 0, 34), 10.0), ((-38, 0, 24), 22.0),
             ((-8, 0, 22), 33.0), ((22, 0, 26), 31.0), ((44, 0, 34), 26.0)]
    d = None
    for (a, ra), (b, rb) in zip(chain[:-1], chain[1:]):
        di = round_cone(q, a, b, ra, rb)
        d = di if d is None else smin(d, di, 6.0)
    d = d * min(1.0, WIDEN)  # (approximate distance, fine for meshing)
    # --- beak (rostrum) with a little upturn, smiling ---
    beak = round_cone(p, (58, 0, 30), (82, 0, 27), 11.0, 7.0)
    d = smin(d, beak, 7.0)
    # --- melon bump on the forehead ---
    d = smin(d, ellipsoid(p, np.array([48, 0, 46]), np.array([18, 20, 16])), 6.0)
    # --- dorsal fin: flattened, swept back ---
    fp = rot(p, np.array([-12, 0, 52]), 'y', -28)
    fin = ellipsoid(fp, np.array([-12, 0, 62]), np.array([13, 4.2, 20]))
    fin = smax(fin, -(fp[:, 2] - 50), 2.0)           # only the part above the body
    d = smin(d, fin, 5.0)
    # --- tail flukes: tilted up 40 deg so they print with little support ---
    for s in (1, -1):
        fl = rot(p, np.array([-76, 0, 52]), 'z', s * 32)
        fl = rot(fl, np.array([-76, 0, 52]), 'y', 40)
        f = ellipsoid(fl, np.array([-83, s * 13, 54]), np.array([14, 18, 4.2]))
        d = smin(d, f, 4.0)
    # --- pectoral flippers: splayed out, resting on the bed ---
    for s in (1, -1):
        fp2 = rot(p, np.array([14, s * 30, 8]), 'z', -s * 35)
        fp2 = rot(fp2, np.array([14, s * 30, 8]), 'x', s * 18)
        f = ellipsoid(fp2, np.array([8, s * 40, 6]), np.array([15, 11, 4.0]))
        d = smin(d, f, 5.0)
    # --- eyes: cartoon domes on the sides of the head ---
    for s in (1, -1):
        e = ellipsoid(p, np.array([51, s * 22.0, 41]), np.array([8.0, 5.0, 9.5]))
        d = smin(d, e, 1.5)
    return d * S


def eye_details(p):
    """cut tool SDF: pupils + smile groove (negative inside the cut)."""
    cuts = []
    for s in (1, -1):
        cuts.append(ellipsoid(p, np.array([55.0, s * 26.6, 42.5]), np.array([4.2, 2.6, 5.0])))
    # smile: thin torus-ish groove along the beak line on each side
    t = np.linspace(0, 1, 40)
    sm = None
    for s in (1, -1):
        for i in range(len(t) - 1):
            pass
    # mouth line as a thin curved tube
    pts = [(80, 0, 24.5)]
    for s in (1, -1):
        for x, z, y in [(74, 24.5, 6.3), (66, 25.5, 9.5), (59, 27.5, 13.0), (54, 30.0, 16.5)]:
            pts.append((x, s * y, z))
    mouth = None
    left = [(80, 0, 24.6), (74, 6.6, 24.6), (66, 9.9, 25.4), (58.5, 13.6, 27.6), (54, 16.8, 30.6)]
    for s in (1, -1):
        seq = [(x, s * y, z) for x, y, z in left]
        for a, b in zip(seq[:-1], seq[1:]):
            m = round_cone(p, a, b, 0.9, 0.9)
            mouth = m if mouth is None else np.minimum(mouth, m)
    cuts.append(mouth)
    return np.min(np.stack(cuts), axis=0)


def mesh_from_sdf(f, lo, hi, step):
    xs = np.arange(lo[0], hi[0] + step, step)
    ys = np.arange(lo[1], hi[1] + step, step)
    zs = np.arange(lo[2], hi[2] + step, step)
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing='ij')
    P = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    vals = np.empty(len(P))
    for i in range(0, len(P), 400000):
        vals[i:i + 400000] = f(P[i:i + 400000])
    V = vals.reshape(X.shape)
    V = np.pad(V, 1, constant_values=10.0)
    verts, faces, _, _ = marching_cubes(V, 0.0, spacing=(step, step, step))
    verts += np.array(lo) - step
    m = trimesh.Trimesh(verts, faces[:, ::-1], process=True)
    if m.volume < 0: m.invert()
    return m
