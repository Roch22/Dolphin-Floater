"""Dolphin tablet floater v1 - builds every part in its PRINT orientation (z=0 on the bed)."""
import numpy as np, manifold3d as mf, trimesh, json, sys
from design import (cyl, ring, revolve_profile, thread_solid, slot_cutter, shapely_to_manifold,
                    text_polys, PITCH, TH_DEPTH, SLOT_N, SLOT_DEG)
from dolphin import mesh_from_sdf
from dolphin2 import dolphin2_sdf, details2
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely import affinity

SEG = 160
CAV_R = 27.2 / 2
TUBE_R = 16.5
COLLAR_R = 19.5
T_THREAD = 14.0              # male thread length (both ends)
COLLAR_CONE = 3.0
COLLAR_CYL = 3.5
SLEEVE_L = 100.0
SLEEVE_GAP = 1.0
SLEEVE_CLR = 0.30
SLEEVE_IR = TUBE_R + SLEEVE_CLR
SLEEVE_OR = SLEEVE_IR + 2.4
THREAD_CLR = 0.25
ROWS, ROW_MARGIN, ROW_GAP = 3, 5.0, 4.5
# cap
CAP_R = 23.0
SKIN, POCKET_H, ROOF = 2.0, 8.0, 2.0
POCKET_RO, POCKET_RI = 19.6, 6.3          # 1/2" fender washer: 38.1 OD, ~13.5 hole
DRAIN_R = 3.0
CAP_THREAD, CAP_CBORE = 14.5, 3.0
PAUSE_Z = SKIN + POCKET_H                 # 10.0 mm
# dolphin socket
SOCK_THREAD = 16.0


def tm(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts, process=False)


def to_mf(t):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32),
                               tri_verts=np.asarray(t.faces, np.uint32)))


def rows(z0, length, n=None):
    n = ROWS if n is None else n
    usable = length - 2 * ROW_MARGIN
    rh = (usable - (n - 1) * ROW_GAP) / n
    out, z = [], z0 + ROW_MARGIN
    for _ in range(n):
        out.append((z, z + rh)); z += rh + ROW_GAP
    return out


def male_thread(z0, length, lead_at_top=True):
    th = thread_solid(TUBE_R - TH_DEPTH, TH_DEPTH, length, z0)
    if lead_at_top:
        zt = z0 + length
        ch = revolve_profile([(0, z0 - 1), (TUBE_R + 3, z0 - 1), (TUBE_R + 3, zt - 1.5),
                              (TUBE_R - TH_DEPTH - 0.4, zt + 0.01), (0, zt + 0.01)])
    else:
        ch = revolve_profile([(0, z0 - 0.01), (TUBE_R - TH_DEPTH - 0.4, z0 - 0.01), (TUBE_R + 3, z0 + 1.5),
                              (TUBE_R + 3, z0 + length + 1), (0, z0 + length + 1)])
    return th ^ ch


def female_cutter(z0, length, clr=THREAD_CLR):
    return thread_solid(TUBE_R - TH_DEPTH + clr, TH_DEPTH, length, z0)


# ------------------------------------------------------------------ TUBE
def tube(sleeve_len=SLEEVE_L, nrows=None):
    """print frame: z=0 = end that screws into the dolphin (on the bed)."""
    z = 0.0
    top_th = male_thread(0, T_THREAD, lead_at_top=False)          # lead-in at the bed end
    zc0 = T_THREAD
    collar = revolve_profile([(TUBE_R - 1, zc0), (TUBE_R, zc0), (COLLAR_R, zc0 + COLLAR_CONE),
                              (COLLAR_R, zc0 + COLLAR_CONE + COLLAR_CYL),
                              (TUBE_R - 1, zc0 + COLLAR_CONE + COLLAR_CYL)])
    zs0 = zc0 + COLLAR_CONE + COLLAR_CYL                           # sleeve contact face
    zb0 = zs0 + sleeve_len + SLEEVE_GAP                            # bottom thread start
    body = cyl(zb0 - zc0 + 0.02, TUBE_R, z0=zc0 - 0.01)
    bot_th = male_thread(zb0 - 0.01, T_THREAD + 0.01, lead_at_top=True)
    zend = zb0 + T_THREAD
    t = top_th + collar + body + bot_th
    t = t - cyl(zend + 2, CAV_R, z0=-1)
    # bore mouth chamfers
    t = t - cyl(1.0, CAV_R + 1.0, CAV_R, z0=-0.001)
    t = t - cyl(1.0, CAV_R, CAV_R + 1.0, z0=zend - 0.999)
    for (a, b) in rows(zs0, sleeve_len, nrows):
        t = t - (slot_cutter(a, b) - cyl(zend + 4, CAV_R - 0.5, z0=-2))
    # ticks on the collar cylinder: long = open (0,60..), medium = closed (30,90..), small = 10/20 steps
    ticks = []
    for deg in range(0, 360, 10):
        k = deg % 60
        L = 3.5 if k == 0 else (2.3 if k == 30 else 1.1)
        w, d = 0.9, 0.7
        tk = mf.Manifold.cube((2 * d, w, L + 0.01)).translate((COLLAR_R - d, -w / 2, zs0 - L))
        ticks.append(tk.rotate((0, 0, deg)))
    t = t - mf.Manifold.batch_boolean(ticks, mf.OpType.Add)
    info = dict(zs0=zs0, zb0=zb0, zend=zend)
    return t, info


# ------------------------------------------------------------------ SLEEVE
def sleeve(length=SLEEVE_L, nrows=None):
    """print frame: z=0 = end that touches the tube collar (pointer end)."""
    s = ring(length, SLEEVE_OR, SLEEVE_IR)
    for (a, b) in rows(0, length, nrows):
        s = s - slot_cutter(a, b)
    # pointer: small wedge at 0 deg, pointing at the collar ticks
    pts = [(SLEEVE_OR - 0.3, -1.4), (SLEEVE_OR + 1.3, 0), (SLEEVE_OR - 0.3, 1.4)]
    p = mf.Manifold.extrude(mf.CrossSection([pts]), ROW_MARGIN - 0.6)
    s = s + p
    # grip ribs at the far end (between last row and the end)
    ribs = []
    for i in range(24):
        if i % 4 == 0: continue
        r = mf.Manifold.cube((1.4, 1.4, ROW_MARGIN - 1.2)).translate((SLEEVE_OR - 0.4, -0.7, length - ROW_MARGIN + 0.6))
        ribs.append(r.rotate((0, 0, 15 * i + 7.5)))
    s = s + mf.Manifold.batch_boolean(ribs, mf.OpType.Add)
    s = s - cyl(0.6, SLEEVE_IR + 0.6, SLEEVE_IR, z0=-0.001)
    s = s - cyl(0.6, SLEEVE_IR, SLEEVE_IR + 0.6, z0=length - 0.599)
    return s


# ------------------------------------------------------------------ CAP
def badge_tool(r=10.5, hole_r=DRAIN_R, depth=0.6):
    outer = Point(0, 0).buffer(r, 128)
    ringg = outer.difference(outer.buffer(-0.7))
    the = text_polys(["THE"], 3.0)
    rock = text_polys(["ROCK"], 3.0)
    the = affinity.translate(the, 0, hole_r + 2.6)
    rock = affinity.translate(rock, 0, -(hole_r + 2.6))
    g = unary_union([ringg, the, rock])
    # mirror so it reads correctly when you look at the bottom of the cap
    return shapely_to_manifold(g, depth + 0.01, z0=-0.01, mirror_x=True)


def cap(clr=THREAD_CLR, washers=True, label=True):
    """print frame: floor on the bed (z=0), mouth up."""
    z_floor_in = SKIN + POCKET_H + ROOF if washers else 3.0
    H = z_floor_in + CAP_THREAD + CAP_CBORE
    c = cyl(H, CAP_R)
    gr = [cyl(H + 2, 1.5, z0=-1, seg=24).translate((23.6 * np.cos(a), 23.6 * np.sin(a), 0))
          for a in np.linspace(0, 2 * np.pi, 24, endpoint=False)]
    c = c - mf.Manifold.batch_boolean(gr, mf.OpType.Add)
    c = c - revolve_profile([(CAP_R - 0.8, -0.01), (CAP_R + 3, -0.01), (CAP_R + 3, 3.8)])        # bed edge
    c = c - revolve_profile([(CAP_R + 3, H - 3.8), (CAP_R + 3, H + 0.01), (CAP_R - 1.0, H + 0.01)])  # mouth edge
    # mouth counterbore (clamps the sleeve with its flat face)
    c = c - cyl(CAP_CBORE + 0.01, TUBE_R + 0.4, z0=H - CAP_CBORE)
    c = c - cyl(1.0, TUBE_R + 0.4, TUBE_R + 1.4, z0=H - 0.999)
    # internal thread
    c = c - female_cutter(z_floor_in - 0.01, CAP_THREAD + 0.6, clr)
    # thread entry chamfer to stop the first crest being razor thin
    c = c - cyl(1.2, TUBE_R - TH_DEPTH + clr, TUBE_R + clr + 0.4, z0=H - CAP_CBORE - 1.2)
    if washers:
        c = c - ring(POCKET_H, POCKET_RO, POCKET_RI, z0=SKIN)
    c = c - cyl(H + 2, DRAIN_R, z0=-1, seg=48)
    if label:
        c = c - badge_tool()
    return c, dict(H=H, z_floor_in=z_floor_in)


# ------------------------------------------------------------------ DOLPHIN
def dolphin_body(step=0.6):
    f = lambda P: np.maximum(np.maximum(dolphin2_sdf(P), -details2(P)), -(P[:, 2] + 0.37))
    m = mesh_from_sdf(f, (-125, -66, -2.03), (102, 66, 90), step)
    d = to_mf(m)
    d = d.trim_by_plane((0, 0, 1), 0.0)           # flat belly at z=0
    return d


def dolphin(socket_xy, vent_to, clr=THREAD_CLR, body=None):
    d = dolphin_body() if body is None else body
    sx, sy = socket_xy
    s = []
    # countersink for the collar cone (+0.3)
    s.append(cyl(COLLAR_CONE + 0.01, COLLAR_R + 0.35, TUBE_R + 0.35, z0=-0.01))
    s.append(cyl(0.8, COLLAR_R + 1.0, COLLAR_R + 0.35, z0=-0.01))          # bed-edge relief
    # female thread
    s.append(female_cutter(COLLAR_CONE - 0.5, SOCK_THREAD, clr))
    zt = COLLAR_CONE - 0.5 + SOCK_THREAD
    # pointed (45 deg) ceiling -> no bridging
    r0 = TUBE_R + clr
    s.append(cyl(r0 + 0.01, r0, 0.8, z0=zt - 0.01))
    tool = mf.Manifold.batch_boolean(s, mf.OpType.Add).translate((sx, sy, 0))
    d = d - tool
    # blowhole vent: straight channel from socket apex to the blowhole spot on the head
    a = np.array([sx, sy, zt + r0 - 2.0]); b = np.array(vent_to)
    v = b - a; L = np.linalg.norm(v)
    ch = mf.Manifold.cylinder(L + 6, 1.6, 1.6, 32).translate((0, 0, -2))
    # rotate z-axis onto v
    zax = np.array([0, 0, 1.0]); vn = v / L
    ang = np.degrees(np.arccos(np.clip(zax @ vn, -1, 1)))
    axis = np.cross(zax, vn)
    if np.linalg.norm(axis) > 1e-9:
        axis /= np.linalg.norm(axis)
        # build rotation matrix (Rodrigues)
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        t = np.radians(ang)
        R = np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K
        M = np.hstack([R, a[:, None]])
        ch = ch.transform(M)
    else:
        ch = ch.translate(tuple(a))
    d = d - ch
    return d, dict(zt=zt)
