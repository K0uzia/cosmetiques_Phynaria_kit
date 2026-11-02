"""Ailes abyssales — ailes de démon membraneuses (charbon, pourpre-noir, veines vert acide). Design original.
Écrit ailes_abyssales.png, ailes_abyssales_e.png et .build/ailes_abyssales_brut.bbmodel à côté de ce script.

Squelette de chauve-souris : humérus > avant-bras > poignet > 4 doigts à 2 phalanges qui rayonnent du poignet.
Membrane : toute l'aile est peinte une seule fois dans le plan de l'aile (carte « monde », en px du modèle), puis
découpée en plaques rectangulaires (alpha 0/255, tranches transparentes), chacune portée par un segment.
Chaque panneau est porté par le doigt du DESSUS : quand les doigts se ferment vers D4, les panneaux glissent les uns
sur les autres comme les lames d'un éventail, sans jamais ouvrir de trou. La pose neutre (fold = 0) est l'aile
grande ouverte : les animations ne font que fermer.
Griffes et cornes : recette peau + âme d'Aurelion (plaque découpée, âme pleine plus étroite).
"""
import base64, io, json, math, os, re, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = False      # True : embarque ailes_abyssales_e.png en seconde texture. False tant que le bug du mod n'est pas corrigé.
TEX = 512
V0, DV = 26, 5      # battement à la fusée (glide) : mêmes constantes qu'Aurelion, validées en jeu
TAU = 2 * math.pi
NOM = "ailes_abyssales"


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ squelette, dans le plan de l'aile (aile droite, x > 0)
Z = 5.2                                 # plan de l'aile (dos du joueur à z = 2)
S_, E_, W_ = (5.4, 23.0), (9.5, 31.5), (19.0, 39.0)
HIP = (6.8, 14.5)                       # la membrane rejoint le corps ici
YAW = [20, -7, 8]                       # balayage arrière au repos : humérus, avant-bras, main
FINGERS = [                             # angle au poignet, longueurs, courbures (degrés), le doigt se creuse vers le bas
    dict(a=14, l1=14.5, l2=17.0, b1=-5, b2=-15),
    dict(a=-15, l1=16.0, l2=18.0, b1=-5, b2=-13),
    dict(a=-44, l1=15.0, l2=17.5, b1=-4, b2=-10),
    dict(a=-73, l1=13.0, l2=15.0, b1=-3, b2=-7),
]
NF = len(FINGERS)
N1, N2 = 4, 5                           # sous-segments d'os par phalange


def arc_from(p, ang, L, bend, n):
    pts, x, y = [p], p[0], p[1]
    for i in range(n):
        a = math.radians(ang + bend * (i + 0.5) / n)
        x, y = x + L / n * math.cos(a), y + L / n * math.sin(a)
        pts.append((x, y))
    return pts


for f in FINGERS:
    p1 = arc_from(W_, f["a"], f["l1"], f["b1"], N1)
    p2 = arc_from(p1[-1], f["a"] + f["b1"], f["l2"], f["b2"], N2)
    f["p1"], f["p2"], f["pts"], f["J"], f["tip"] = p1, p2, p1 + p2[1:], p1[-1], p2[-1]
    f["end"] = f["a"] + f["b1"] + f["b2"]


def along(pts, u):
    """Point au paramètre u (0..1, longueur d'arc) d'une polyligne."""
    ls = [0.0]
    for a, b in zip(pts, pts[1:]):
        ls.append(ls[-1] + math.dist(a, b))
    d = u * ls[-1]
    for i in range(len(pts) - 1):
        if d <= ls[i + 1] or i == len(pts) - 2:
            k = (d - ls[i]) / max(1e-6, ls[i + 1] - ls[i])
            return (lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k))


def scallop(p, q, depth, n=24):
    """Bord de fuite entre deux pointes : arc creusé vers le poignet."""
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    dx, dy = W_[0] - mx, W_[1] - my
    dl = math.hypot(dx, dy)
    c = (mx + dx / dl * depth, my + dy / dl * depth)
    return [((1 - t) ** 2 * p[0] + 2 * t * (1 - t) * c[0] + t * t * q[0], (1 - t) ** 2 * p[1] + 2 * t * (1 - t) * c[1] + t * t * q[1])
            for t in (i / n for i in range(n + 1))]


ARCS = [scallop(FINGERS[k]["tip"], FINGERS[k + 1]["tip"], d) for k, d in zip(range(NF - 1), (6.5, 7.0, 6.0))]
ARC_B = scallop(FINGERS[-1]["tip"], HIP, 6.0, n=36)                     # du dernier doigt à la hanche
M1, M2 = along(ARC_B, 0.36), along(ARC_B, 0.70)

# ------------------------------------------------------------------ carte de la membrane
R = 18                                  # texels de carte par px modèle
XM, YM = 58, 62
GW, GH = XM * R, YM * R
gy, gx = np.mgrid[0:GH, 0:GW]
X = (gx + 0.5) / R
Y = YM - (gy + 0.5) / R
rng = np.random.default_rng(66)


def px(p):
    return (p[0] * R, (YM - p[1]) * R)


def fill(poly, val=255, img=None, size=None):
    im = img if img is not None else Image.new("L", (GW, GH), 0)
    ImageDraw.Draw(im).polygon([px(p) for p in poly], fill=val)
    return im


def blur(arr_img, radius_px):
    return np.array(arr_img.filter(ImageFilter.GaussianBlur(radius_px * R)), np.float32) / 255


def noise(cells, seed):
    r = np.random.default_rng(seed)
    a = (r.random((cells, cells)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((GW, GH), Image.BICUBIC), np.float32) / 255


outline = [S_, E_, W_] + FINGERS[0]["pts"][1:]
for k in range(NF - 1):
    outline += ARCS[k][1:] + []
outline += ARC_B[1:] + [(7.2, 19.0)]
mask_img = fill(outline)

# Déchirures : encoches sur les bords de fuite, trous dans la membrane. Graine fixe : le résultat est reproductible.
d = ImageDraw.Draw(mask_img)


def tear(arc, t, width, depth):
    p, l, r = along(arc, t), along(arc, max(0.0, t - width)), along(arc, min(1.0, t + width))
    dx, dy = W_[0] - p[0], W_[1] - p[1]
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    jog = rng.uniform(-0.6, 0.6)
    tipn = (p[0] + dx * depth - dy * jog, p[1] + dy * depth + dx * jog)
    mid = (p[0] + dx * depth * 0.55 + dy * jog * 0.6, p[1] + dy * depth * 0.55 - dx * jog * 0.6)
    out = (p[0] - dx * 2.5, p[1] - dy * 2.5)
    d.polygon([px(q) for q in (l, mid, tipn, (mid[0] + 0.25, mid[1] - 0.25), r, out)], fill=0)


TEARS = [[(0.20, 0.035, 1.6), (0.47, 0.03, 4.2), (0.72, 0.04, 1.8)],
         [(0.16, 0.03, 1.5), (0.38, 0.04, 2.4), (0.63, 0.03, 4.6), (0.85, 0.03, 1.5)],
         [(0.26, 0.04, 3.4), (0.55, 0.03, 1.7), (0.80, 0.03, 2.8)],
         [(0.14, 0.022, 1.8), (0.30, 0.018, 4.0), (0.50, 0.024, 1.8), (0.66, 0.02, 3.2), (0.84, 0.024, 1.6)]]
for arc, ts in zip(ARCS + [ARC_B], TEARS):
    for t, w, dep in ts:
        tear(arc, t, w, dep)


def resampled(k):
    return [along(FINGERS[k]["pts"], i / 24) for i in range(25)]


RS = [resampled(k) for k in range(NF)]


def ray(a, b, n=24):
    return [(lerp(a[0], b[0], i / n), lerp(a[1], b[1], i / n)) for i in range(n + 1)]


def mix_paths(p, q, k):
    return [(lerp(a[0], b[0], k), lerp(a[1], b[1], k)) for a, b in zip(p, q)]


def tatter(p, q, k, u, rx, ry):
    c = mix_paths(p, q, k)[int(round(u * 24))]
    pts = []
    ang0 = math.atan2(c[1] - W_[1], c[0] - W_[0])
    for i in range(9):
        a = i / 9 * TAU
        r = rng.uniform(0.7, 1.15)
        x, y = rx * r * math.cos(a), ry * r * math.sin(a)
        pts.append((c[0] + x * math.cos(ang0) - y * math.sin(ang0), c[1] + x * math.sin(ang0) + y * math.cos(ang0)))
    d.polygon([px(q_) for q_ in pts], fill=0)


tatter(RS[0], RS[1], 0.58, 0.78, 1.5, 0.75)
tatter(RS[1], RS[2], 0.40, 0.66, 1.2, 0.65)
tatter(RS[1], RS[2], 0.62, 0.86, 1.0, 0.55)
tatter(RS[2], RS[3], 0.52, 0.74, 1.4, 0.7)
RAY_A, RAY_B = ray(along([E_, W_], 0.40), along(ARC_B, 0.30)), ray(E_, along(ARC_B, 0.60))
tatter(RAY_A, RAY_B, 0.45, 0.72, 1.3, 0.7)
tatter(ray(along([S_, E_], 0.4), along(ARC_B, 0.84)), RAY_B, 0.7, 0.62, 1.0, 0.55)

M = np.array(mask_img) > 127

# Veines : réseau radial depuis le poignet, épaisseur ≥ 3–4 texels sur la texture
vein_img = Image.new("L", (GW, GH), 0)
core_img = Image.new("L", (GW, GH), 0)
vd, cd = ImageDraw.Draw(vein_img), ImageDraw.Draw(core_img)


def vein(path, u0, u1, w0, w1, wob=0.2, seed=0):
    r = np.random.default_rng(seed)
    n = 14
    pts = []
    ph = r.uniform(0, TAU)
    for i in range(n + 1):
        u = lerp(u0, u1, i / n)
        x, y = along(path, u)
        off = wob * math.sin(i * 0.9 + ph)
        pts.append((x + off * 0.7, y + off * 0.7))
    for i in range(n):
        w = lerp(w0, w1, (i + 0.5) / n)
        vd.line([px(pts[i]), px(pts[i + 1])], fill=255, width=max(1, int(round(w * R))))
        cd.line([px(pts[i]), px(pts[i + 1])], fill=255, width=max(1, int(round(w * 0.5 * R))))
    return pts


def branch(start, end, w0, w1, seed):
    return vein(ray(start, end), 0, 1, w0, w1, wob=0.12, seed=seed)


WM, WB = 0.50, 0.36          # épaisseur (px) d'une veine maîtresse et d'une branche
seed = 10
paths = [(RS[0], RS[1]), (RS[1], RS[2]), (RS[2], RS[3]), (RS[3], RAY_A), (RAY_A, RAY_B)]
for p, q in paths:
    m = mix_paths(p, q, 0.5)
    tr = vein(m, 0.14, 0.90, WM, WB, seed=seed)
    seed += 1
    for u, k, e in ((0.46, 0.24, 0.88), (0.62, 0.76, 0.94)):
        st = along(m, u)
        en = mix_paths(p, q, k)[int(round(e * 24))]
        branch(st, en, WB, WB * 0.8, seed)
        seed += 1
inner = ray(along([S_, E_], 0.35), along(ARC_B, 0.84))
vein(inner, 0.08, 0.86, WM, WB, seed=seed)
branch(along(inner, 0.5), along(ARC_B, 0.95), WB, WB * 0.8, seed + 1)
branch(along(inner, 0.45), along(ARC_B, 0.74), WB, WB * 0.8, seed + 2)

V = np.array(vein_img, np.float32) / 255
Vc = (np.array(core_img) > 127) & M

# Ombre des os : les panneaux s'assombrissent contre les doigts, le centre du panneau reste plus clair
bone_img = Image.new("L", (GW, GH), 0)
bd = ImageDraw.Draw(bone_img)
for f in FINGERS:
    bd.line([px(p) for p in f["pts"]], fill=255, width=int(0.9 * R))
bd.line([px(p) for p in (S_, E_, W_)], fill=255, width=int(1.6 * R))
near_bone = np.clip(blur(bone_img, 1.5) * 1.7, 0, 1)

ang = np.arctan2(Y - W_[1], X - W_[0])
dist = np.hypot(X - W_[0], Y - W_[1])
blot = noise(12, 3) * 0.6 + noise(34, 4) * 0.4
fib = np.sin(ang * 92 + 5 * noise(9, 5))
far = np.clip(dist / 38, 0, 1)

C_DARK = np.array((17, 7, 26), np.float32)
C_BASE = np.array((42, 16, 60), np.float32)
C_HIGH = np.array((82, 28, 104), np.float32)
C_RIM = np.array((122, 42, 124), np.float32)
C_AURA = np.array((22, 66, 40), np.float32)
C_VEIN = np.array((96, 200, 44), np.float32)
C_VCORE = np.array((150, 244, 70), np.float32)

k = np.clip((blot - 0.32) * 1.9, 0, 1)[..., None]
col = lerp(C_BASE, C_HIGH, k * 0.75)
col = col * (1 + 0.09 * fib)[..., None]                                     # fibres radiales
col = lerp(col, C_DARK, (near_bone * 0.82)[..., None])                      # plis sombres le long des os
col = lerp(col, C_HIGH, (far ** 3 * 0.35)[..., None])                       # la membrane s'éclaircit vers le bord, comme une peau tendue
edge = np.clip(1 - blur(Image.fromarray(M.astype(np.uint8) * 255, "L"), 0.42), 0, 1)
rim = np.clip((edge - 0.16) * 3.2, 0, 1) * M
col = lerp(col, C_RIM, (rim * 0.9)[..., None])                              # bord déchiré lisible, plus clair que la peau
aura = np.clip(blur(vein_img, 0.55) * 1.3, 0, 1)
col = lerp(col, C_AURA, (aura * 0.6)[..., None])
col = lerp(col, C_VEIN, (V > 0.5)[..., None] * 1.0)
col = lerp(col, C_VCORE, ((np.array(core_img) > 127))[..., None] * 1.0)
col = col.astype(np.float32)

# ------------------------------------------------------------------ panneaux : qui porte quoi
OV = 1.3      # recouvrement entre plaques voisines d'un même doigt (px)


def tilted(pts, deg):
    """Polyligne tournée autour du poignet : déborde sous le doigt voisin, pour recouvrir."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(W_[0] + (x - W_[0]) * c - (y - W_[1]) * s, W_[1] + (x - W_[0]) * s + (y - W_[1]) * c) for x, y in pts]


def far_pts(pts, amount):
    """Prolonge le contour au-delà de la pointe : la carte M coupe, pas le polygone."""
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    l = math.hypot(x1 - x0, y1 - y0)
    return pts + [(x1 + (x1 - x0) / l * amount, y1 + (y1 - y0) / l * amount)]


def side(J, ang_deg, sign, ov):
    """Demi-plan normal au doigt en J : sign = -1 côté poignet, +1 côté pointe."""
    dx, dy = math.cos(math.radians(ang_deg)), math.sin(math.radians(ang_deg))
    return ((X - J[0]) * dx + (Y - J[1]) * dy) * sign >= -ov


PANELS = []


def panel(name, owner, poly, z, clip=None):
    m = np.array(fill(poly)) > 127
    if clip is not None:
        m &= clip
    PANELS.append(dict(name=name, owner=owner, mask=m & M, z=z))


for k in range(NF - 1):
    f = FINGERS[k]
    poly = [W_] + far_pts(f["pts"], 3.0)[1:] + list(reversed(far_pts(tilted(RS[k + 1], -3.5), 6.0)))
    ja = f["a"] + f["b1"]
    zb = -0.21 + 0.13 * k
    panel(f"m{k + 1}a", f"d{k + 1}", poly, zb, side(f["J"], ja, -1, OV))
    panel(f"m{k + 1}b", f"d{k + 1}b", poly, zb + 0.04, side(f["J"], ja, +1, OV))

# dernier doigt : son panneau part vers l'intérieur, jusqu'au rayon qui descend de l'avant-bras
f = FINGERS[-1]
poly = [W_] + far_pts(f["pts"], 3.0)[1:] + list(reversed(far_pts(tilted(RAY_A, -3.0), 5.0)))
panel("m4a", "d4", poly, 0.18, side(f["J"], f["a"] + f["b1"], -1, OV))
panel("m4b", "d4b", poly, 0.22, side(f["J"], f["a"] + f["b1"], +1, OV))
# avant-bras
poly = [along([S_, E_], 0.8), E_, (W_[0] + 0.8, W_[1] + 0.2), (W_[0] + 2.6, W_[1] - 3.0)] + \
    far_pts(ray((W_[0] + 2.6, W_[1] - 3.0), (M1[0] + 3.0, M1[1])), 4.0)[1:] + \
    [(M2[0] - 1.8, M2[1] - 4.0), (along([S_, E_], 0.8)[0] - 1.0, along([S_, E_], 0.8)[1] - 4.0)]
panel("m5", "elbow", poly, -0.30)
# humérus : jusqu'au corps
poly = [S_, along([S_, E_], 1.0), (E_[0] + 1.2, E_[1] - 2.0), (M2[0] + 1.6, M2[1] - 4.5), (HIP[0] - 1.0, HIP[1] - 3.0), (HIP[0] - 1.2, HIP[1] + 2)]
panel("m6", "shoulder", poly, -0.26)

# ------------------------------------------------------------------ peinture des griffes, os, particule


def hook_shape(L, curve):
    """Griffe : axe recourbé, largeur qui s'effile ; x, y en px. curve > 0 : se recourbe vers +y."""
    return (lambda t: (L * (t - 0.12 * t * t), curve * L * t ** 2.1)), (lambda t: 0.135 * L * (1 - t) ** 0.8 + 0.006 * L)


def paint_hook(W, H, curve, bb):
    """Tuile de griffe (bb = (y bas, y haut) en fraction de L) ; x de -0.02L à L."""
    ss = 4
    ax, ay = np.mgrid[0:H * ss, 0:W * ss][::-1]
    a = lerp(-0.02, 1.0, (ax + 0.5) / (W * ss))
    b = lerp(bb[1], bb[0], (ay + 0.5) / (H * ss))
    center, hw = hook_shape(1.0, curve)
    ts = np.linspace(0, 1, 200)
    cx = np.array([center(t)[0] for t in ts])
    cy = np.array([center(t)[1] for t in ts])
    hws = np.array([hw(t) for t in ts])
    dd = np.full(a.shape, 9.0, np.float32)
    tt = np.zeros(a.shape, np.float32)
    rr = np.zeros(a.shape, np.float32)
    for i in range(len(ts)):
        dist_ = np.hypot(a - cx[i], b - cy[i]) / hws[i]
        better = dist_ < dd
        dd[better], tt[better] = dist_[better], ts[i]
    inside = dd < 1
    base = np.array((26, 22, 34), np.float32)
    hi = np.array((98, 72, 132), np.float32)
    acid = np.array((132, 240, 58), np.float32)
    c = np.empty(a.shape + (3,), np.float32)
    c[...] = base
    c = lerp(c, hi, (np.clip(1 - dd * 1.6, 0, 1) * 0.72)[..., None])
    c = lerp(c, np.array((12, 8, 16), np.float32), (np.clip((dd - 0.62) * 2.2, 0, 1) * 0.8)[..., None])
    c = lerp(c, acid, (np.clip((tt - 0.58) / 0.28, 0, 1))[..., None])
    rgb = Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    al = np.array(Image.fromarray(inside.astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110
    out = np.dstack([np.array(rgb), al * 255]).astype(np.uint8)
    out[~al, :3] = (26, 22, 34)
    # calque lumineux : la griffe, de très sombre à vif vers la pointe
    te = np.array(Image.fromarray((tt * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS), np.float32)[..., None] / 255
    ec = lerp(np.array((10, 34, 12), np.float32), np.array((156, 255, 84), np.float32), np.clip((te - 0.2) / 0.7, 0, 1))
    eo = np.dstack([ec, al * 255.0]).astype(np.uint8)
    eo[~al] = 0
    return out, eo


HOOK_BB = (-0.20, 0.46)
CURVE = 0.30
hook_big, hook_big_e = paint_hook(84, 56, CURVE, HOOK_BB)
hook_small, hook_small_e = paint_hook(48, 32, CURVE, HOOK_BB)

# Os : charbon, filet violacé central. u = le long de l'os (racine à gauche, pointe à droite)
BW, BH = 96, 16
_a = np.zeros((BH, BW, 4), np.float32)
_n = np.random.default_rng(8)
for yy in range(BH):
    q = abs((yy + 0.5) / BH - 0.5) * 2
    for xx in range(BW):
        u = xx / (BW - 1)
        c_ = lerp(np.array((54, 48, 66.0)), np.array((26, 22, 34.0)), q ** 1.2)
        c_ = lerp(c_, np.array((132, 98, 176.0)), max(0.0, 1 - q * 2.2) * (0.55 + 0.3 * math.sin(u * 15)))
        c_ = c_ * (0.9 + 0.2 * math.sin(u * 40 + yy * 0.6))
        _a[yy, xx, :3] = c_
_a[..., 3] = 255
bone_tile = _a.astype(np.uint8)

# Braise-particule : éclat anguleux, cœur vif, liseré sombre ; une seule plaque
PT = 48
_pm = Image.new("L", (PT * 4, PT * 4), 0)
_shard = [(0.58, 0.02), (0.72, 0.30), (0.66, 0.42), (0.86, 0.60), (0.60, 0.98), (0.50, 0.70), (0.30, 0.80), (0.38, 0.46), (0.20, 0.34), (0.46, 0.26)]
ImageDraw.Draw(_pm).polygon([(x * PT * 4, y * PT * 4) for x, y in _shard], fill=255)
_pf = np.array(_pm.filter(ImageFilter.GaussianBlur(PT * 0.2)), np.float32) / 255
_pmn = np.array(_pm) > 127
_pc = np.empty(_pf.shape + (3,), np.float32)
_pc[...] = (28, 74, 30)
_ks = np.clip((_pf - 0.32) * 2.6, 0, 1)[..., None]
_pc = lerp(_pc, np.array((120, 232, 52), np.float32), _ks)
_pc = lerp(_pc, np.array((206, 255, 118), np.float32), np.clip((_pf - 0.66) * 4.5, 0, 1)[..., None])
_pi = np.array(Image.fromarray(_pc.astype(np.uint8), "RGB").resize((PT, PT), Image.LANCZOS))
_pa = np.array(_pm.resize((PT, PT), Image.LANCZOS)) > 110
braise_tile = np.dstack([_pi, _pa * 255]).astype(np.uint8)
braise_tile[~_pa, :3] = _pi[_pa].mean(axis=0).astype(np.uint8)


# ------------------------------------------------------------------ atlas
def best_rect(mask):
    """Rectangle d'aire minimale autour de la zone opaque (angle en degrés)."""
    ys, xs = np.nonzero(mask[::6, ::6])
    px_ = (xs * 6 + 0.5) / R
    py_ = YM - (ys * 6 + 0.5) / R
    best = None
    for deg in range(0, 180, 2):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        a = px_ * c + py_ * s
        b = -px_ * s + py_ * c
        w, h = a.max() - a.min() + 0.5, b.max() - b.min() + 0.5
        if best is None or w * h < best[0]:
            cxa, cxb = (a.max() + a.min()) / 2, (b.max() + b.min()) / 2
            best = (w * h, deg, w, h, cxa * c - cxb * s, cxa * s + cxb * c)
    return best


for p in PANELS:
    area, p["phi"], p["w"], p["h"], p["cx"], p["cy"] = best_rect(p["mask"])

FIXED = [("hook_big", hook_big), ("hook_small", hook_small), ("bone", bone_tile), ("braise", braise_tile)]


def pack(dens):
    """Rangement par étagères ; dernière rangée libre pour le texel transparent."""
    items = [(n, im.shape[1], im.shape[0]) for n, im in FIXED]
    for p in PANELS:
        items.append((p["name"], int(math.ceil(p["w"] * dens)), int(math.ceil(p["h"] * dens))))
    items.sort(key=lambda it: -it[2])
    uv, x, y, shelf = {}, 0, 0, 0
    for n, w, h in items:
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        if y + h > TEX - 6 or w > TEX:
            return None
        uv[n] = (x, y, x + w, y + h)
        x += w + 1
        shelf = max(shelf, h)
    return uv


DENS = 9.0
while (UV := pack(DENS)) is None:
    DENS -= 0.1
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
for n, im in FIXED:
    u0, v0, u1, v1 = UV[n]
    tex[v0:v1, u0:u1] = im
tex_e[UV["hook_big"][1]:UV["hook_big"][3], UV["hook_big"][0]:UV["hook_big"][2]] = hook_big_e
tex_e[UV["hook_small"][1]:UV["hook_small"][3], UV["hook_small"][0]:UV["hook_small"][2]] = hook_small_e

for p in PANELS:
    u0, v0, u1, v1 = UV[p["name"]]
    W, H = u1 - u0, v1 - v0
    ss = 3
    jj, ii = np.mgrid[0:H * ss, 0:W * ss]
    a = ((ii + 0.5) / (W * ss) - 0.5) * p["w"]
    b = (0.5 - (jj + 0.5) / (H * ss)) * p["h"]
    c, s = math.cos(math.radians(p["phi"])), math.sin(math.radians(p["phi"]))
    wx = p["cx"] + a * c - b * s
    wy = p["cy"] + a * s + b * c
    ix = np.clip((wx * R).astype(int), 0, GW - 1)
    iy = np.clip(((YM - wy) * R).astype(int), 0, GH - 1)
    sm_ = p["mask"][iy, ix]
    al = sm_.reshape(H, ss, W, ss).mean(axis=(1, 3)) > 0.5
    cc = col[iy, ix].reshape(H, ss, W, ss, 3).mean(axis=(1, 3))
    if al.any():
        cc[~al] = cc[al].mean(axis=0)                       # pas de frange, PNG compact
    tex[v0:v1, u0:u1, :3] = np.clip(cc, 0, 255).astype(np.uint8)
    tex[v0:v1, u0:u1, 3] = al * 255
    # calque lumineux : les veines seules
    vm = Vc[iy, ix].reshape(H, ss, W, ss).mean(axis=(1, 3)) > 0.34
    vm &= al
    tex_e[v0:v1, u0:u1, :3] = np.array((132, 255, 72), np.uint8)
    tex_e[v0:v1, u0:u1, 3] = vm * 255
    tex_e[v0:v1, u0:u1, :3] *= vm[..., None]
    p["fill"] = float(al.mean())

CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC                                         # postérisation invisible à l'œil : PNG nettement plus léger
assert set(np.unique(tex[..., 3])) <= {0, 255}, "semi-transparence"
assert set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence _e"
tex_img = Image.fromarray(tex, "RGBA")
tex_img.save(f"{NOM}.png", optimize=True)
_b = io.BytesIO()
tex_img.save(_b, "PNG", optimize=True)
tex_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()
tex_e_img = Image.fromarray(tex_e, "RGBA")
tex_e_img.save(f"{NOM}_e.png", optimize=True)
_b = io.BytesIO()
tex_e_img.save(_b, "PNG", optimize=True)
tex_e_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def cube(name, frm, to, origin, rot=(0, 0, 0), faces=None):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to],
         "origin": [round(v, 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(v, 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(rot):
        e["rotation"] = [round(v, 2) for v in rot]
    elements.append(e)
    return e["uuid"]


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups
    groups[name] = {"origin": [round(v, 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(v, 2) for v in rotation]}
    return name


def plate(s, g, name, cx, cy, w, h, phi, z, uv, flip_v=False, th=0.3):
    """Plaque fine : contour par l'alpha, tranches transparentes. Le même morceau d'image sert aux deux ailes (u inversé à gauche)."""
    u0, v0, u1, v1 = UV[uv]
    if flip_v:
        v0, v1 = v1, v0
    ua, ub = (u0, u1) if s > 0 else (u1, u0)
    x = s * cx
    faces = {"south": [ua, v0, ub, v1], "north": [ub, v0, ua, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
    groups[g]["ids"].append(cube(name, [x - w / 2, cy - h / 2, z - th / 2], [x + w / 2, cy + h / 2, z + th / 2], [x, cy, z], rot=(0, 0, s * phi), faces=faces))


def bar(s, g, name, x, y, z, L, q, phi, u0, u1, octo=True, ov=0.0):
    """Tronçon d'os le long de l'axe local X. octo : section octogonale (deux cubes à 45°), sinon losange seul."""
    bu0, bv0, bu1, bv1 = UV["bone"]
    ua, ub = lerp(bu0, bu1, u0), max(lerp(bu0, bu1, u1), lerp(bu0, bu1, u0) + 2)
    long_ = [ua, bv0, ub, bv1]
    end = [ua, bv0 + 3, ua + 2, bv1 - 3]
    faces = {"south": long_, "north": long_, "up": long_, "down": long_, "east": end, "west": end}
    a, b = (x - ov, x + L + ov) if s > 0 else (-x - L - ov, -x + ov)
    o = [s * x, y, z]
    gid = groups[g]["ids"]
    if octo:
        gid.append(cube(name, [a, y - q, z - q], [b, y + q, z + q], o, rot=(0, 0, s * phi), faces=faces))
        gid.append(cube(name + "o", [a + 0.03, y - q * 0.97, z - q * 0.97], [b - 0.03, y + q * 0.97, z + q * 0.97], o, rot=(45, 0, s * phi), faces=faces))
    else:
        gid.append(cube(name, [a, y - q, z - q], [b, y + q, z + q], o, rot=(45, 0, s * phi), faces=faces))


def chain(s, g, name, pts, r0, r1, u0=0.0, u1=1.0, octo_until=1.0, z=Z, z1=None):
    """Os effilé et légèrement courbe : tronçons qui se recouvrent, rayon qui décroît, couleur continue le long de l'os."""
    n = len(pts) - 1
    z1 = z if z1 is None else z1
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        L = math.dist(pts[i], pts[i + 1])
        phi = math.degrees(math.atan2(yb - ya, xb - xa))
        t0, t1 = i / n, (i + 1) / n
        q = lerp(r0, r1, (t0 + t1) / 2)
        bar(s, g, f"{name}{i}", xa, ya, lerp(z, z1, t0), L, q, phi, lerp(u0, u1, t0), lerp(u0, u1, t1), octo=(t1 <= octo_until + 1e-6), ov=0.12)


def hook(s, g, name, x, y, z, L, ang, tile, down=False, core=3):
    """Griffe recourbée : peau découpée dans le plan de l'aile + âme pleine plus étroite. down : se recourbe vers le bas de l'axe."""
    lo, hi = HOOK_BB
    if down:
        lo, hi = -hi, -lo
    H = (hi - lo) * L
    Wp = 1.02 * L
    phi = math.radians(ang)
    a0, b0 = (-0.02 + 1.0) / 2 * L, (lo + hi) / 2 * L
    cx, cy = x + a0 * math.cos(phi) - b0 * math.sin(phi), y + a0 * math.sin(phi) + b0 * math.cos(phi)
    plate(s, g, name, cx, cy, Wp, H, ang, z + 0.07, tile, flip_v=down)
    center, hw = hook_shape(L, -CURVE if down else CURVE)
    for j in range(core):
        t0, t1 = j / core * 0.72, (j + 1) / core * 0.72
        (a, b), (a2, b2) = center(t0), center(t1)
        xa, ya = x + a * math.cos(phi) - b * math.sin(phi), y + a * math.sin(phi) + b * math.cos(phi)
        xb, yb = x + a2 * math.cos(phi) - b2 * math.sin(phi), y + a2 * math.sin(phi) + b2 * math.cos(phi)
        q = max(0.16, hw((t0 + t1) / 2) * 0.62)
        bar(s, g, f"{name}c{j}", xa, ya, z, math.dist((xa, ya), (xb, yb)), q, math.degrees(math.atan2(yb - ya, xb - xa)), 0.6, 0.9, octo=False, ov=0.08)


EMITS = []


def emit(parent, at, s):
    EMITS.append(group("emit_braise" + (str(len(EMITS) + 1) if EMITS else ""), [s * at[0], at[1], Z], parent=parent))


SEG = ["shoulder", "elbow", "wrist"]


def build(s):
    tag = "l" if s < 0 else "r"
    pv = [S_, E_, W_]
    segs = []
    for i in range(3):
        segs.append(group(f"{SEG[i]}_{tag}", [s * pv[i][0], pv[i][1], Z], parent=segs[i - 1] if i else None, rotation=(0, -s * YAW[i], 0)))
    sh, el, wr = segs
    # racine : sort du dos, fixe, pas de pièce dorsale ; deux petites cornes
    rt = group(f"wingroot_{tag}", [s * S_[0], S_[1], Z])
    chain(s, rt, f"root_{tag}", [(1.6, 21.4), (3.4, 21.9), (S_[0], S_[1])], 0.8, 1.0, 0.0, 0.1, z=3.4, z1=Z)
    hook(s, rt, f"horn0_{tag}", 2.4, 23.8, 4.9, 5.2, 72, "hook_small", down=True, core=3)
    hook(s, rt, f"horn1_{tag}", 3.4, 22.0, 4.9, 3.6, -22, "hook_small", down=False, core=2)

    # humérus et avant-bras : légère courbure, section qui s'affine
    bow = lambda a, b, k, n: [(lerp(a[0], b[0], i / n) - k * (b[1] - a[1]) * math.sin(math.pi * i / n),
                               lerp(a[1], b[1], i / n) + k * (b[0] - a[0]) * math.sin(math.pi * i / n)) for i in range(n + 1)]
    chain(s, sh, f"hum_{tag}", bow(S_, E_, 0.07, 3), 1.02, 0.98, 0.05, 0.3)
    chain(s, el, f"avb_{tag}", bow(E_, W_, -0.05, 5), 1.05, 0.68, 0.3, 0.55)
    bar(s, el, f"coude_{tag}", E_[0] - 0.7, E_[1] - 0.45, Z, 1.6, 1.12, 38, 0.2, 0.3, octo=True)
    bar(s, wr, f"nodw_{tag}", W_[0] - 0.8, W_[1] - 0.2, Z, 1.8, 0.92, 14, 0.5, 0.6, octo=True)
    hook(s, el, f"spur_{tag}", E_[0] + 0.1, E_[1] + 0.3, Z, 4.6, 118, "hook_small", down=True, core=2)

    # pouce : griffe recourbée au poignet, pièce maîtresse de la silhouette
    th = group(f"thumb_{tag}", [s * W_[0], W_[1], Z], parent=wr)
    chain(s, th, f"thb_{tag}", arc_from(W_, 74, 3.2, 8, 2), 0.72, 0.55, 0.5, 0.65)
    tb = arc_from(W_, 74, 3.2, 8, 2)[-1]
    hook(s, th, f"griffe_{tag}", tb[0], tb[1], Z, 9.4, 80, "hook_big", down=True, core=4)

    # doigts : deux phalanges, griffe au bout
    for k, f in enumerate(FINGERS):
        d = group(f"d{k + 1}_{tag}", [s * W_[0], W_[1], Z], parent=wr)
        db = group(f"d{k + 1}b_{tag}", [s * f["J"][0], f["J"][1], Z], parent=d)
        chain(s, d, f"f{k + 1}a_{tag}", f["p1"], 0.66, 0.42, 0.55, 0.78)
        chain(s, db, f"f{k + 1}b_{tag}", f["p2"], 0.42, 0.2, 0.78, 1.0, octo_until=0.61)
        bar(s, db, f"nod{k + 1}_{tag}", f["J"][0] - 0.45, f["J"][1], Z, 0.9, 0.5, f["a"] + f["b1"], 0.75, 0.8, octo=True)
        hook(s, db, f"cl{k + 1}_{tag}", f["tip"][0], f["tip"][1], Z, 4.2, f["end"], "hook_small", down=True, core=2)

    # membrane
    names = {"elbow": el, "shoulder": sh}
    for p in PANELS:
        owner = names.get(p["owner"], f"{p['owner']}_{tag}")
        plate(s, owner, f"{p['name']}_{tag}", p["cx"], p["cy"], p["w"], p["h"], p["phi"], Z + p["z"], p["name"])

    # points de départ des braises : bout des doigts et bord des membranes
    emit(f"d1b_{tag}", FINGERS[0]["tip"], s)
    emit(f"d2b_{tag}", FINGERS[1]["tip"], s)
    emit(f"d3b_{tag}", along(ARCS[2], 0.5), s)
    emit(f"d4b_{tag}", FINGERS[3]["tip"], s)
    return rt, sh


(LR_, L_), (RR_, R_) = build(-1), build(1)

# Particule (guide, section 5 ter) : une seule plaque, face up seule, à 0,3 px au-dessus du pivot : aucun contact avec le sol.
PL = group("particle_braise", [0, 0, 0])
PW, PTH, PY = 3.2, 0.3, 0.3
pu0, pv0, pu1, pv1 = UV["braise"]
groups[PL]["ids"].append(cube("braise", [-PW / 2, PY, -PW / 2], [PW / 2, PY + PTH, PW / 2], [0, 0, 0], faces={"up": [pu0, pv0, pu1, pv1]}))


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(),
             "children": [{"name": "item", "origin": [0, 0, 0], "uuid": nuid(),
                           "children": [bone(LR_), bone(RR_), bone(L_), bone(R_)]}]},
            bone(PL)]

# ------------------------------------------------------------------ animations
# Les courbes décrivent l'aile GAUCHE en termes d'intention :
#   fx > 0 : le plan bascule vers l'horizontale ; fy > 0 : pivote vers l'arrière ; fz > 0 : la pointe monte.
#   fold : 0 = doigts grands ouverts (pose du modèle), 1 = éventail fermé. curl : les dernières phalanges se creusent.

# MIROIR D'AXES : seul endroit à toucher si la convention du mod change (un signe suffit).
# Repères de docs/guide-cosmetiques.md, section 3 : +X = le haut bascule vers l'arrière,
# +Y = le côté droit (+X) avance, +Z = le côté droit monte, donc le côté gauche descend.
SX, SY, SZ = -1, -1, +1


def mirror(s, fx, fy, fz):
    """s = -1 aile gauche, +1 aile droite. Renvoie les valeurs de keyframe."""
    return SX * fx, s * SY * fy, s * SZ * fz


CLOSE = [50, 30, 10, -12]                # fermeture de chaque doigt à fold = 1 (degrés), vers D4
CURLW = [1.0, 0.9, 0.75, 0.55]


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 2)), "y": str(round(y + 0.0, 2)), "z": str(round(z + 0.0, 2))}],
            "time": round(t, 3), "interpolation": "linear"}


def S(T, amp, ph=0.0, off=0.0):
    return lambda t: off + amp * math.sin(TAU * t / T + math.radians(ph))


def C(v):
    return lambda t: v


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def anim(name, length, segs, fold, curl=C(0), n_kf=None, loop="loop", only=None):
    """segs : shoulder/elbow/wrist -> (fx, fy, fz). only : familles animées (attaque et blessé, joués une fois par-dessus l'état)."""
    A = {}

    def put(g, kfs):
        if only is None or re.sub(r"\d*_[lr]$", "", g) in only:
            A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}

    n = n_kf or max(6, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]   # interpolation linéaire : dernier keyframe = premier
    for s, tag in ((-1, "l"), (1, "r")):
        for seg, (fx, fy, fz) in segs.items():
            put(f"{seg}_{tag}", [kf("rotation", t, *mirror(s, fx(t), fy(t), fz(t))) for t in times])
        for k in range(NF):
            # le doigt le plus proche du bord suit le mouvement avec un léger retard
            dl = 0.03 * length * (NF - 1 - k)
            put(f"d{k + 1}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, -CLOSE[k] * fold((t - dl) % length if loop == "loop" else max(0.0, t - dl)))) for t in times])
            put(f"d{k + 1}b_{tag}", [kf("rotation", t, *mirror(s, 0, 0, -CURLW[k] * curl(t))) for t in times])
        # le pouce se relève quand la main se ferme : la griffe reste la pointe haute de la silhouette
        put(f"thumb_{tag}", [kf("rotation", t, *mirror(s, 0, 0, 32 * max(0.0, fold(t)))) for t in times])
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "idle", "animators": A}


Z0 = C(0)

# idle 8 s : repos menaçant, à demi fermé ; respiration (4 s) + étirement ample 4,6–7,2 s
st = lambda t: bump(t, 4.6, 5.4, 6.0, 7.2)
mix = lambda f, v: (lambda t: f(t) * (1 - st(t)) + v * st(t))
idle = anim("idle", 8.0, {
    "shoulder": (mix(S(4, 1.0, 0, 6), 15), mix(S(4, 1.5, 0, 14), -6), mix(S(4, 2, 0, 2), 10)),
    "elbow":    (Z0, mix(S(4, 1, -40, -6), -4), mix(S(4, 1.5, -40, -3), 4)),
    "wrist":    (Z0, mix(S(4, 0.8, -70, 8), -6), mix(S(4, 1, -70, -6), 3))},
    fold=lambda t: (0.22 + 0.05 * math.sin(TAU * t / 4)) * (1 - st(t)), curl=lambda t: (4 + 1.5 * math.sin(TAU * t / 4)) * (1 - st(t)), n_kf=48)

# fly 2,4 s : le joueur reste debout en vol créatif. Plan basculé d'environ 40° (jamais 90°), ailes ouvertes, battement ample.
# Remontée : poignet fléchi, doigts qui se ferment ; descente : aile tendue.
T = 2.4
up = lambda t, lag=0.0: 0.5 + 0.5 * math.cos(TAU * (t / T - lag))
fly = anim("fly", T, {
    "shoulder": (S(T, 4, 90, 40), S(T, 5, 90, -13), S(T, 22, 0, 0)),
    "elbow":    (Z0, lambda t: 8 - 3 * up(t, 0.12), S(T, 8, -45, -2)),
    "wrist":    (Z0, lambda t: -8 + 3 * up(t, 0.22), lambda t: 2 + 5 * math.sin(TAU * t / T - math.radians(75)) - 15 * up(t, 0.22))},
    fold=lambda t: 0.02 + 0.40 * up(t, 0.2), curl=lambda t: 2 + 11 * up(t, 0.26), n_kf=24)

# glide 3,6 s : joueur couché, le cosmétique suit le torse : presque dans le plan du dos, grandes ouvertes, X faible.
# Battement lent hors du plan par Y, et battement à la fusée (même forme d'expression et mêmes constantes qu'Aurelion, validées en jeu).
G = 3.6
BOOST = f"math.clamp((math.max(q.ground_speed,q.vertical_speed)-{V0})/{DV},0,1)*math.clamp((q.vertical_speed+8)/4,0,1)"


def term(amp, speed, ph):
    """Texte Molang de amp*sin(speed*t + ph), signe compris ; amp = 0 : vide."""
    if not amp:
        return ""
    p = f"{ph:+g}" if ph else ""
    return f"{amp:+g}*math.sin(q.anim_time*{speed}{p})"


def mol(sign, base, slow=(0, 0), boost=(0, 0)):
    """base + slow[0]*sin(100t+slow[1]) + boost[0]*A*sin(600t+boost[1]), multiplié par sign (miroir). Courte, sans ? ni &&."""
    e = f"{sign * base:g}" + term(sign * slow[0], 100, slow[1])
    if boost[0]:
        e += f"{sign * boost[0]:+g}*{BOOST}*math.sin(q.anim_time*600{boost[1]:+g})"
    assert len(e) <= 256
    return e


def mkf(x, y, z):
    return {"channel": "rotation", "data_points": [{"x": x, "y": y, "z": z}], "time": 0, "interpolation": "linear"}


def glide_anim():
    A = {}

    def put(g, x, y, z):
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [mkf(x, y, z)]}

    for s_, tag in ((-1, "l"), (1, "r")):
        sx, sy, sz = mirror(s_, 1, 1, 1)      # le signe reste centralisé dans mirror()
        put(f"shoulder_{tag}", mol(sx, 8, (1.5, 90)), mol(sy, -14, (11, 0), (24, 0)), f"{sz * -4:g}")
        put(f"elbow_{tag}", "0", mol(sy, 8, (-3, -43), (11, -45)), f"{sz * 1:g}")
        put(f"wrist_{tag}", "0", mol(sy, -8, (4, -79), (13, -90)), f"{sz * 2:g}")
        for k in range(NF):
            c = CLOSE[k]
            put(f"d{k + 1}_{tag}", "0", "0", mol(sz, round(-c * 0.12, 2), (round(c * 0.05, 2), 90), (round(c * 0.07, 2), -90)))
            put(f"d{k + 1}b_{tag}", "0", "0", mol(sz, round(-3 * CURLW[k], 2), (round(1.5 * CURLW[k], 2), 60), (round(-5 * CURLW[k], 2), -120)))
    return {"uuid": nuid(), "name": "glide", "loop": "loop", "override": False, "length": G, "snapping": 24, "selected": False, "animators": A}


glide = glide_anim()

# fall 1,5 s : joueur debout, ailes relevées et ouvertes, plan peu basculé (freinage), ~26°
AI = 1.5
fall = anim("fall", AI, {"shoulder": (S(AI, 3, 0, 26), C(-4), S(AI, 4, 0, 12)),
                         "elbow": (Z0, C(3), S(AI, 3, -40, 5)),
                         "wrist": (Z0, C(-4), S(AI, 3, -70, 4))},
            fold=S(AI, 0.05, 0, 0.09), curl=S(AI, 3, -60, 8))

# walk 1,6 s : ramenées vers l'arrière, à moitié fermées, balancement au pas
W = 1.6
walk = anim("walk", W, {"shoulder": (C(8), S(W, 5, 0, 30), S(W, 3.5, 0, -8)),
                        "elbow": (Z0, S(W, 3, -40, -10), S(W, 2, -40, -4)),
                        "wrist": (Z0, S(W, 3, -70, 14), S(W, 2.5, -70, -22))},
            fold=C(0.55), curl=S(W, 2, -70, 6))

# run 1,0 s : très vers l'arrière, abaissées, repli en S réparti sur les 3 articulations, éventail presque fermé
R_ = 1.0
run = anim("run", R_, {"shoulder": (C(16), S(R_, 3, 0, 50), S(R_, 3, 0, -14)),
                       "elbow": (Z0, S(R_, 2, -40, -28), S(R_, 1.5, -40, -5)),
                       "wrist": (Z0, S(R_, 3, -80, 34), S(R_, 2, -80, -28))},
           fold=C(0.8), curl=S(R_, 2, -60, 8))

# sneak 3 s : éventail fermé, plis serrés dans le dos, griffe du poignet qui dépasse au-dessus de l'épaule
SN = 3.0
sneak = anim("sneak", SN, {"shoulder": (C(7), S(SN, 1, 0, 10), S(SN, 1, 0, 8)),
                           "elbow": (Z0, C(-15), S(SN, 1, -40, 0)),
                           "wrist": (Z0, C(5), C(-34))},
             fold=S(SN, 0.015, 0, 0.985), curl=C(9))

# sleep 4 s : repliées, tombantes
SL = 4.0
sleep = anim("sleep", SL, {"shoulder": (C(12), S(SL, 1, 0, 12), S(SL, 1, 0, 2)),
                           "elbow": (Z0, C(-14), C(-4)),
                           "wrist": (Z0, C(6), C(-30))},
             fold=C(1.0), curl=S(SL, 1, -60, 10))

# swim 2 s : joueur couché. Ailes dans le plan du dos, rabattues vers les pieds, à demi fermées ; ondulation hors du plan par Y.
SW = 2.0
swim = anim("swim", SW, {"shoulder": (C(7), S(SW, 7, 0, 2), C(-34)),
                         "elbow": (Z0, S(SW, 6, -45, 6), C(-10)),
                         "wrist": (Z0, S(SW, 7, -90, -4), C(-10))},
            fold=C(0.65), curl=S(SW, 4, -120, 6))

# mount 3 s : repos relevé, pointes hautes, respiration ample
MT = 3.0
mount = anim("mount", MT, {"shoulder": (C(10), S(MT, 2.5, 0, 8), S(MT, 3.5, 0, 12)),
                           "elbow": (Z0, S(MT, 1.5, -40, -4), S(MT, 2, -40, 5)),
                           "wrist": (Z0, C(2), S(MT, 2, -70, -2))},
             fold=S(MT, 0.04, 0, 0.26), curl=S(MT, 1.5, -40, 4))

# attack et hurt : une fois par-dessus l'état, dernière image neutre, seuls les groupes concernés.
IMPULSE = {"shoulder", "elbow", "wrist", "d", "thumb"}
AT = 0.8
atk = lambda t: bump(t, 0.0, 0.14, 0.30, 0.72)
attack = anim("attack", AT, {"shoulder": (lambda t: 24 * atk(t), lambda t: -12 * atk(t), lambda t: 12 * atk(t)),
                             "elbow": (Z0, lambda t: -6 * atk(t), lambda t: 5 * atk(t)),
                             "wrist": (Z0, lambda t: -8 * atk(t), lambda t: 6 * atk(t))},
              fold=lambda t: -0.08 * atk(t), n_kf=16, loop="once", only=IMPULSE)

HU = 0.8
hu = lambda t: bump(t, 0.0, 0.08, 0.22, 0.72)
tr = lambda t: 3 * math.sin(TAU * t * 5 / HU) * (1 - sm(t, 0.25, 0.7))
hurt = anim("hurt", HU, {"shoulder": (lambda t: 6 * hu(t), lambda t: 16 * hu(t), lambda t: 8 * hu(t) + tr(t)),
                         "elbow": (Z0, lambda t: -6 * hu(t), lambda t: -3 * hu(t) + tr(t)),
                         "wrist": (Z0, lambda t: 8 * hu(t), lambda t: -3 * hu(t) + tr(t))},
            fold=lambda t: 0.25 * hu(t), n_kf=16, loop="once", only=IMPULSE)


def particle_anim(name, length, curve, n):
    times = [i * length / n for i in range(n + 1)]
    return {"uuid": nuid(), "name": name, "loop": "loop", "override": False, "length": length, "snapping": 24, "selected": False,
            "animators": {groups[PL]["uuid"]: {"name": PL, "type": "bone", "keyframes": [kf("rotation", t, *curve(t)) for t in times]}}}


# chute 3 s : un tour complet autour de Y (boucle fermée) et un balancement ; repos 6 s : respire à peine
PF, PR = 3.0, 6.0
braise_fall = particle_anim("particle_braise_fall", PF, lambda t: (24 * math.sin(TAU * t / PF), 360 * t / PF, 18 * math.cos(2 * TAU * t / PF)), 24)
braise_rest = particle_anim("particle_braise_rest", PR, lambda t: (0, 0, 1.2 * math.sin(TAU * t / PR)), 12)

ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, attack, hurt, braise_fall, braise_rest]
assert 6 <= len(EMITS) <= 8 and len(ANIMS) <= 16
assert 150 <= len(elements) <= 500, f"budget : {len(elements)} cubes"

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))
with open(OUT) as fh:
    json.load(fh)


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 2, "groupes ; profondeur", depth(outliner[0]), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      f"densité membrane {DENS:.1f} texels/px ; {len(EMITS)} emit_ ; panneaux {len(PANELS)} par aile")
