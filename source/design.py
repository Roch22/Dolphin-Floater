"""Hot tub tablet floater v1 - parametric design (all mm).
Assembly frame = print frame of the float+tube part:
  z = 0 is the TOP face of the float (sits on the bed), tube points +z.
In the hot tub the whole thing is flipped (float up, cap down).
"""
import numpy as np, manifold3d as mf, trimesh
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from shapely.geometry import Polygon
from shapely.ops import unary_union

SEG = 160

# ---------------- parameters ----------------
TAB_D, TAB_H, N_TAB = 25.2, 16.0, 8
CAV_R = 27.2 / 2                 # tablet bore (1.0 mm clearance on diameter... 2.0 total)
TUBE_R = 16.5                    # tube outside radius (33 mm OD)
FLOAT_R, FLOAT_H = 70.0, 20.0    # 140 mm float
CONE_R0, COLLAR_R = 30.0, 19.5
Z_FLOAT, Z_CONE_END, Z_COLLAR_END = FLOAT_H, 31.0, 35.0
SLEEVE_L = 100.0
SLEEVE_CLR = 0.30                # radial clearance sleeve/tube
SLEEVE_IR = TUBE_R + SLEEVE_CLR
SLEEVE_OR = SLEEVE_IR + 2.4
Z_SLEEVE0 = Z_COLLAR_END
Z_SLEEVE1 = Z_SLEEVE0 + SLEEVE_L                 # 135
Z_THREAD0 = Z_SLEEVE1 + 1.0                      # 136
THREAD_L = 14.0
Z_TUBE_END = Z_THREAD0 + THREAD_L                # 150
CAV_L = 132.0
Z_CAV0 = Z_TUBE_END - CAV_L                      # 18
PITCH, TH_DEPTH = 3.0, 1.2
THREAD_CLR = 0.25                # radial, cap vs tube (0.25 worked on his capsule)
CAP_R = 22.0
CAP_CBORE = 3.0                  # unthreaded counterbore at cap mouth
CAP_THREAD = 14.5
CAP_FLOOR = 3.0
SLOT_N, SLOT_DEG = 6, 26.0       # 6 columns, 26 deg wide, 60 deg pitch
ROWS = 3
ROW_MARGIN, ROW_GAP = 5.0, 4.5


def cyl(h, r, r2=None, z0=0.0, seg=SEG):
    m = mf.Manifold.cylinder(h, r, r if r2 is None else r2, seg)
    return m.translate((0, 0, z0))


def ring(h, ro, ri, z0=0.0, seg=SEG):
    return cyl(h, ro, z0=z0, seg=seg) - cyl(h + 0.02, ri, z0=z0 - 0.01, seg=seg)


def revolve_profile(pts, seg=SEG):
    """pts: list of (r, z) closed polygon, r>=0."""
    return mf.Manifold.revolve(mf.CrossSection([pts]), seg)


def thread_profile(u):
    """radial height 0..1 over one pitch phase u in [0,1)."""
    u = u % 1.0
    if u < 0.15: return 0.0
    if u < 0.45: return (u - 0.15) / 0.30
    if u < 0.60: return 1.0
    if u < 0.90: return 1.0 - (u - 0.60) / 0.30
    return 0.0


def thread_solid(r_root, depth, h, z0, n=360):
    """Right-hand single-start trapezoid thread (solid incl. core) via twisted extrude."""
    pts = []
    for i in range(n):
        phi = 2 * np.pi * i / n
        r = r_root + depth * thread_profile(i / n)
        pts.append((r * np.cos(phi), r * np.sin(phi)))
    turns = h / PITCH
    m = mf.Manifold.extrude(mf.CrossSection([pts]), h, int(turns * 64), 360.0 * turns)
    return m.translate((0, 0, z0))


def slot_cutter(z0, z1, rmax=40.0, ang_deg=SLOT_DEG, centers=None):
    """wedge cutters (angular slots) between z0 and z1."""
    cuts = []
    centers = centers if centers is not None else [i * 360.0 / SLOT_N for i in range(SLOT_N)]
    for c in centers:
        a0, a1 = np.radians(c - ang_deg / 2), np.radians(c + ang_deg / 2)
        arc = [(rmax * np.cos(a), rmax * np.sin(a)) for a in np.linspace(a0, a1, 12)]
        poly = [(0, 0)] + arc
        cuts.append(mf.Manifold.extrude(mf.CrossSection([poly]), z1 - z0).translate((0, 0, z0)))
    return mf.Manifold.batch_boolean(cuts, mf.OpType.Add)


def row_ranges(z_s0, length):
    usable = length - 2 * ROW_MARGIN
    rh = (usable - (ROWS - 1) * ROW_GAP) / ROWS
    out, z = [], z_s0 + ROW_MARGIN
    for _ in range(ROWS):
        out.append((z, z + rh)); z += rh + ROW_GAP
    return out


def text_polys(lines, height, font="/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", gap=1.25):
    fp = FontProperties(fname=font)
    polys = []
    n = len(lines)
    for k, s in enumerate(lines):
        tp = TextPath((0, 0), s, size=height, prop=fp)
        rings = [Polygon(p) for p in tp.to_polygons() if len(p) > 2]
        g = None
        for r in sorted(rings, key=lambda r: -r.area):
            r = r.buffer(0)
            g = r if g is None else g.symmetric_difference(r)
        b = g.bounds
        dy = (n - 1) / 2 * height * gap - k * height * gap
        from shapely import affinity
        g = affinity.translate(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2 + dy)
        polys.append(g)
    return unary_union(polys)


def shapely_to_manifold(g, h, z0=0.0, mirror_x=False):
    from shapely import affinity
    if mirror_x: g = affinity.scale(g, -1, 1, origin=(0, 0))
    ms = []
    for p in (g.geoms if hasattr(g, 'geoms') else [g]):
        cs = mf.CrossSection([list(p.exterior.coords)[:-1]] + [list(i.coords)[:-1] for i in p.interiors],
                             mf.FillRule.EvenOdd)
        ms.append(mf.Manifold.extrude(cs, h).translate((0, 0, z0)))
    return mf.Manifold.batch_boolean(ms, mf.OpType.Add)


def badge(depth=0.6, r=9.0, mirror=True):
    """engraving tool for small round THE/ROCK badge on a bed-face (z=0)."""
    ringg = Polygon([(r * np.cos(a), r * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 90)]).buffer(0)
    ringg = ringg.difference(ringg.buffer(-0.7))
    txt = text_polys(["THE", "ROCK"], 3.6, gap=1.3)
    from shapely import affinity
    b = txt.bounds
    s = min(1.0, (2 * (r - 1.6)) / max(b[2] - b[0], 1e-6))
    txt = affinity.scale(txt, s, s, origin=(0, 0))
    g = unary_union([ringg, txt])
    return shapely_to_manifold(g, depth + 0.01, z0=-0.01, mirror_x=mirror)


# ---------------- FLOAT + TUBE (one print, grey) ----------------
def float_tube(thread_end=Z_TUBE_END):
    prof = [(0, 0), (FLOAT_R - 1.0, 0), (FLOAT_R, 1.0), (FLOAT_R, FLOAT_H - 4.0),
            (FLOAT_R - 1.2, FLOAT_H - 1.2), (FLOAT_R - 4.0, FLOAT_H), (CONE_R0, FLOAT_H),
            (COLLAR_R, Z_CONE_END), (COLLAR_R, Z_COLLAR_END), (0, Z_COLLAR_END)]
    body = revolve_profile(prof)
    # decorative V groove around the float side (two-tone look line)
    groove = revolve_profile([(FLOAT_R - 0.8, 8.0), (FLOAT_R + 1, 7.2), (FLOAT_R + 1, 8.8)])
    body = body - groove
    tube = cyl(Z_THREAD0 - Z_COLLAR_END + 0.01, TUBE_R, z0=Z_COLLAR_END - 0.005)
    th = thread_solid(TUBE_R - TH_DEPTH, TH_DEPTH, thread_end - Z_THREAD0 + 0.01, Z_THREAD0 - 0.005)
    # end chamfer (lead-in) on thread
    cham = revolve_profile([(0, thread_end - 3), (TUBE_R + 2, thread_end - 3),
                            (TUBE_R + 2, thread_end - 1.5), (TUBE_R - TH_DEPTH - 0.6, thread_end + 0.01),
                            (0, thread_end + 0.01)])
    th = th ^ cham
    part = body + tube + th
    # tablet bore + vent
    part = part - cyl(thread_end - Z_CAV0 + 1, CAV_R, z0=Z_CAV0)
    part = part - cyl(Z_CAV0 + 1, 1.5, z0=-0.5, seg=40)
    # bore mouth chamfer
    part = part - cyl(1.0, CAV_R + 1.0, CAV_R, z0=thread_end - 1.0 + 0.001)
    # slots in the tube under the sleeve
    for (a, b) in row_ranges(Z_SLEEVE0, SLEEVE_L):
        part = part - (slot_cutter(a, b) - cyl(500, CAV_R - 0.5, z0=-1))  # only through tube wall
    # tick marks engraved on collar: open at 0+60k (long), closed at 30+60k (medium), 10/20 small
    ticks = []
    for deg in range(0, 360, 10):
        k = deg % 60
        L = 4.0 if k == 0 else (2.6 if k == 30 else 1.3)
        w, d = 0.8, 0.7
        t = mf.Manifold.cube((d * 2, w, L + 0.01)).translate((COLLAR_R - d, -w / 2, Z_COLLAR_END - L))
        ticks.append(t.rotate((0, 0, deg)))
    part = part - mf.Manifold.batch_boolean(ticks, mf.OpType.Add)
    return part


# ---------------- SLEEVE (blue) ----------------
def sleeve(length=SLEEVE_L, z0=Z_SLEEVE0):
    s = ring(length, SLEEVE_OR, SLEEVE_IR, z0=z0)
    for (a, b) in row_ranges(z0, length):
        s = s - slot_cutter(a, b)
    # pointer ridge at 0 deg on the end that touches the collar (z0 side)
    p = mf.Manifold.cube((1.2, 1.8, ROW_MARGIN - 0.8)).translate((SLEEVE_OR - 0.2, -0.9, z0))
    # make the pointer an arrow tip toward the collar: chamfer top
    s = s + p
    # small entry chamfers inside both ends
    s = s - cyl(0.6, SLEEVE_IR + 0.6, SLEEVE_IR, z0=z0 - 0.001)
    s = s - cyl(0.6, SLEEVE_IR, SLEEVE_IR + 0.6, z0=z0 + length - 0.599)
    return s


# ---------------- CAP (blue) ----------------
def cap(clr=THREAD_CLR, z_top=Z_SLEEVE1, label=True):
    """built in assembly frame with its mouth (top in this frame) touching the sleeve end."""
    h = CAP_CBORE + CAP_THREAD + CAP_FLOOR
    c = cyl(h, CAP_R, z0=z_top)
    # grip scallops
    gr = []
    for i in range(24):
        a = 2 * np.pi * i / 24
        gr.append(cyl(h + 1, 1.5, z0=z_top - 0.5, seg=24).translate((23.0 * np.cos(a), 23.0 * np.sin(a), 0)))
    c = c - mf.Manifold.batch_boolean(gr, mf.OpType.Add)
    # outer edge chamfers
    c = c - revolve_profile([(CAP_R - 1.0, z_top - 0.01), (CAP_R + 2, z_top - 0.01), (CAP_R + 2, z_top + 3.0)])
    c = c - revolve_profile([(CAP_R + 2, z_top + h - 3.0), (CAP_R + 2, z_top + h + 0.01), (CAP_R - 0.8, z_top + h + 0.01)])
    # counterbore (mouth)
    c = c - cyl(CAP_CBORE + 0.01, TUBE_R + 0.4, z0=z_top - 0.005)
    c = c - cyl(1.0, TUBE_R + 1.2, TUBE_R + 0.4, z0=z_top - 0.001)
    # internal thread: cutter = tube thread grown by clr
    zt0 = z_top + CAP_CBORE - 0.5
    cutter = thread_solid(TUBE_R - TH_DEPTH + clr, TH_DEPTH, CAP_THREAD + 0.5 + 0.01, zt0)
    c = c - cutter
    # drain holes in the floor
    zf = z_top + CAP_CBORE + CAP_THREAD
    for i in range(3):
        a = 2 * np.pi * i / 3 + np.pi / 6
        c = c - cyl(CAP_FLOOR + 1, 1.5, z0=zf - 0.5, seg=32).translate((12.5 * np.cos(a), 12.5 * np.sin(a), 0))
    if label:
        # badge on the outside of the floor; tool built at z=0 facing -z, then flipped onto the floor face
        tool = badge()                                    # occupies z -0.01..0.6, readable from -z when mirrored
        tool = tool.mirror((0, 0, 1)).translate((0, 0, z_top + h))  # now z_top+h-0.6 .. +0.01
        c = c - tool
    return c


def to_tm(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts, process=True)


def cap_print(c, z_top=Z_SLEEVE1):
    """flip cap so floor is on the bed."""
    h = CAP_CBORE + CAP_THREAD + CAP_FLOOR
    return c.translate((0, 0, -(z_top + h))).mirror((0, 0, 1)).rotate((0, 0, 0)) if False else \
        c.rotate((180, 0, 0)).translate((0, 0, z_top + h))
