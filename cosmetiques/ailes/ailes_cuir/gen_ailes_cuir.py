"""Ailes de cuir — ailes de chauve-souris en cuir verni noir tendu sur une ossature d'argent noirci (ensemble Cuir, thème Fétiche).
Design original. Écrit ailes_cuir.png, ailes_cuir_e.png et .build/ailes_cuir_brut.bbmodel à côté de ce script.

Structure reprise de gen_ailes_abyssales.py (référence validée en jeu pour os et membrane) : humérus > avant-bras > poignet >
4 doigts à 2 phalanges, os octogonaux effilés et courbes, membrane peinte d'un seul tenant dans le plan de l'aile puis découpée
en plaques (alpha 0/255, tranches transparentes), chaque panneau porté par le doigt du dessus ; mirror() centralise les signes.
Matière et détails (.claude/styles/cuir.md) : membrane en cuir verni noir (liseré clair net du vernis le long de chaque os, filets
de reflet nets, coutures rouges en tirets le long des os et des bords, œillets argent près du bord de fuite festonné), doublure
rouge sang très sombre sur la face avant (côté joueur) ; os en argent noirci à arêtes claires ; bagues de cuir cloutées aux
articulations, rivets d'argent traversants au coude et au poignet, sangle à boucle autour de chaque avant-bras, embouts d'argent
au bout des doigts, griffe d'argent arrondie au pouce ; chaîne fine (maillons alternés de face et de profil) du poignet à la
première jointure du grand doigt, en quatre groupes imbriqués qui balancent avec un retard ; racine couverte par une pièce de
cuir rivetée (pas de plaque dorsale ni de sac).
Taille (.claude/styles/ailes-anatomie.md) : l'aile est dessinée en grand puis réduite par K autour de l'épaule (réduire(), recette
des ailes mécaniques) ; les épaisseurs des plaques ne sont pas réduites.
Couches (recette des ailes mécaniques, « clipping disparu ») : chaque panneau a sa couche sur une grille de PAS = 0,2 px réels
(plaques de 0,3 px) ; chaque os est placé à la profondeur de la jonction de ses panneaux ; les os, bagues et embouts sont tournés
de 22,5° autour de leur axe (aucune face parallèle au plan de la membrane) ; leurs bouts intérieurs sont transparents.
Contrôle : deux faces parallèles qui se recouvrent sont à 0,1 px au moins (mesuré par .build/../ scratchpad check_faces.py).
Fonctions avancées : event_equip (dépliage depuis le dos), event_unequip (repli, échelle presque nulle à la fin), son de cuir
item.armor.equip_leather à l'apparition et au retrait (tools/sons.py), overlay_ambiance (tools/ambiance.py : ctrl_teinte,
ctrl_lumiere, calque _e des coutures). Pas de emit_mc_ (bug du mod), pas de calque _r. À juger en jeu : _e, événements.
"""
import base64, io, json, math, os, re, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # calque _e embarqué (coutures rouges faiblement lumineuses)
TEX = 512
V0, DV = 26, 5      # battement à la fusée (glide) : constantes validées en jeu
TAU = 2 * math.pi
NOM = "ailes_cuir"


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ squelette, dans le plan de l'aile (aile droite, x > 0), avant réduction
Z = 5.2                                 # plan de l'aile (dos du joueur à z = 2) ; pivot de l'épaule
S_, E_, W_ = (5.4, 23.0), (9.5, 31.5), (19.0, 39.0)
HIP = (6.8, 14.5)                       # la membrane rejoint le corps ici
YAW = [20, -7, 8]                       # balayage arrière au repos : humérus, avant-bras, main
K = 0.50                               # réduction autour de l'épaule : envergure ouverte ≈ 62 px (1,6 à 2,2 fois le joueur)
PAS = 0.2                               # pas de la grille de couches, en px réels
EP = 0.3                                # épaisseur réelle des plaques
FINGERS = [                             # angle au poignet, longueurs, courbures (degrés) : doigts longs de chauve-souris
    dict(a=16, l1=17.8, l2=21.3, b1=-6, b2=-14),
    dict(a=-14, l1=19.5, l2=22.4, b1=-6, b2=-13),
    dict(a=-43, l1=18.4, l2=21.3, b1=-6, b2=-11),
    dict(a=-71, l1=16.1, l2=18.4, b1=-6, b2=-9),
]
NF = len(FINGERS)
N1, N2 = 3, 4                           # tronçons d'os par phalange (courbure ≥ 2° entre deux tronçons)
LAYER = {"m6": 0, "m5": 3, "m4": 6, "m3": 7, "m2": 8, "m1": 9}       # couche de chaque panneau (bas = côté joueur) ; deux couches libres
                                                                    # entre deux segments (humérus, avant-bras, main), qui pivotent l'un sur l'autre
ZF = [9.5, 8.5, 7.5, 6.5]               # couche de l'os de chaque doigt : à la jonction de ses deux panneaux
ROLL = [22, 31, 40, 13]                 # rotation de chaque doigt autour de son axe : quand l'éventail se ferme, deux os voisins
                                        # n'ont jamais de faces parallèles (ni avec la membrane : jamais un multiple de 45°)
Z_HUM, Z_AVB, Z_POI, Z_COU = 1.5, 4.5, 5.5, 3.0
ZC = 4.75                               # couche du plan Z (pivot de l'épaule)


def couche(i):
    """Profondeur avant réduction de la couche i (réduite : Z + (i − ZC) × PAS)."""
    return Z + (i - ZC) * PAS / K


def zr(i):
    """Profondeur réelle de la couche i (pièces non réduites : racine)."""
    return Z + (i - ZC) * PAS


def un(v):
    """Longueur réelle -> longueur avant réduction."""
    return v / K


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
    ls = [0.0]
    for a, b in zip(pts, pts[1:]):
        ls.append(ls[-1] + math.dist(a, b))
    d = u * ls[-1]
    for i in range(len(pts) - 1):
        if d <= ls[i + 1] or i == len(pts) - 2:
            k = (d - ls[i]) / max(1e-6, ls[i + 1] - ls[i])
            return (lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k))


def scallop(p, q, depth, n=28):
    """Bord de fuite entre deux pointes : arc arrondi creusé vers le poignet."""
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    dx, dy = W_[0] - mx, W_[1] - my
    dl = math.hypot(dx, dy)
    c = (mx + dx / dl * depth, my + dy / dl * depth)
    return [((1 - t) ** 2 * p[0] + 2 * t * (1 - t) * c[0] + t * t * q[0], (1 - t) ** 2 * p[1] + 2 * t * (1 - t) * c[1] + t * t * q[1])
            for t in (i / n for i in range(n + 1))]


ARCS = [scallop(FINGERS[k]["tip"], FINGERS[k + 1]["tip"], d) for k, d in zip(range(NF - 1), (6.0, 6.5, 5.5))]
ARC_B = scallop(FINGERS[-1]["tip"], HIP, 5.5, n=40)
M1, M2 = along(ARC_B, 0.36), along(ARC_B, 0.70)

# ------------------------------------------------------------------ carte de la membrane (texels de carte, px avant réduction)
R = 18
XM, YM = 60, 64
GW, GH = XM * R, YM * R
gy, gx = np.mgrid[0:GH, 0:GW]
X = (gx + 0.5) / R
Y = YM - (gy + 0.5) / R


def px(p):
    return (p[0] * R, (YM - p[1]) * R)


def fill(poly, val=255):
    im = Image.new("L", (GW, GH), 0)
    ImageDraw.Draw(im).polygon([px(p) for p in poly], fill=val)
    return im


def resampled(k):
    return [along(FINGERS[k]["pts"], i / 24) for i in range(25)]


RS = [resampled(k) for k in range(NF)]


def ray(a, b, n=24):
    return [(lerp(a[0], b[0], i / n), lerp(a[1], b[1], i / n)) for i in range(n + 1)]


outline = [S_, E_, W_] + FINGERS[0]["pts"][1:]
for k in range(NF - 1):
    outline += ARCS[k][1:]
outline += ARC_B[1:] + [(7.2, 19.0)]
mask_img = fill(outline)
M = np.array(mask_img) > 127
RAY_A = ray(along([E_, W_], 0.40), along(ARC_B, 0.30))


def erode(mask, r_px):
    n = int(round(r_px * R)) * 2 + 1
    return np.array(Image.fromarray(mask.astype(np.uint8) * 255, "L").filter(ImageFilter.MinFilter(n))) > 127


def offset(pts, d, toward=None):
    """Polyligne décalée de d le long de la normale (à droite du sens de parcours) ; toward : point vers lequel orienter la normale."""
    out = []
    for i, p in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1
        nx, ny = ty / l, -tx / l
        if toward is not None and (toward[0] - p[0]) * nx + (toward[1] - p[1]) * ny < 0:
            nx, ny = -nx, -ny
        out.append((p[0] + nx * d, p[1] + ny * d))
    return out


def dense(pts, step=0.15):
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.dist(a, b) / step))
        out += [(lerp(a[0], b[0], i / n), lerp(a[1], b[1], i / n)) for i in range(1, n + 1)]
    return out


def stroke(draw, pts, w, val=255):
    draw.line([px(p) for p in pts], fill=val, width=max(1, int(round(w * R))), joint="curve")


def dashes(draw, pts, w, on=0.55, per=0.95, val=255):
    """Couture : tirets réguliers le long de la polyligne."""
    pts = dense(pts)
    s, cur = 0.0, []
    for a, b in zip(pts, pts[1:]):
        if (s % per) < on:
            cur.append(a)
        elif cur:
            cur.append(a)
            if len(cur) > 1:
                draw.line([px(p) for p in cur], fill=val, width=max(1, int(round(w * R))))
            cur = []
        s += math.dist(a, b)
    if len(cur) > 1:
        draw.line([px(p) for p in cur], fill=val, width=max(1, int(round(w * R))))


BONES = [f["pts"] for f in FINGERS] + [[S_, E_, W_]]
stitch_img, lis_img, shadow_img, gloss_img = (Image.new("L", (GW, GH), 0) for _ in range(4))
sd, ld, hd, gd = (ImageDraw.Draw(i) for i in (stitch_img, lis_img, shadow_img, gloss_img))
for b in BONES:
    dashes(sd, offset(dense(b, 0.6), 1.1), 0.34, on=0.5, per=0.9)                           # couture le long de l'os, côté bas
    stroke(hd, b, 1.5)                                                     # ombre contre l'os
    stroke(ld, offset(dense(b, 0.6), 2.0), 0.40)                           # liseré du vernis, côté bas de l'os
# bord de fuite : couture à 0,8 px du bord, filet de reflet net plus loin (peau tendue)
for arc in ARCS + [ARC_B]:
    dashes(sd, offset(arc, 0.9, toward=W_), 0.34, on=0.5, per=0.9)
dashes(sd, offset(ray((7.2, 19.0), S_), 0.9, toward=W_), 0.34, on=0.5, per=0.9)
STI = (np.array(stitch_img) > 127) & M
LIS = (np.array(lis_img) > 127) & M & ~STI
GLO = (np.array(gloss_img) > 127) & M & ~STI
SHA = np.array(shadow_img.filter(ImageFilter.GaussianBlur(0.35 * R)), np.float32) / 255

# œillets d'argent près du bord de fuite
EYE = []
for arc, ts in zip(ARCS + [ARC_B], [(0.3, 0.7), (0.3, 0.7), (0.5,), (0.22, 0.48, 0.74)]):
    inner = offset(arc, 2.0, toward=W_)
    for t in ts:
        EYE.append(along(inner, t))
dist = lambda c: np.hypot(X - c[0], Y - c[1])
EYE_RING = np.zeros((GH, GW), bool)
EYE_HOLE = np.zeros((GH, GW), bool)
EYE_HI = np.zeros((GH, GW), bool)
for c in EYE:
    d_ = dist(c)
    ring = (d_ < 0.58) & (d_ >= 0.27)
    EYE_RING |= ring
    EYE_HOLE |= d_ < 0.27
    EYE_HI |= ring & ((X - c[0]) * -0.6 + (Y - c[1]) * 0.8 > 0.12)

RIM0 = M & ~erode(M, 0.22)             # bord extrême : reflet du vernis
RIM1 = M & ~erode(M, 0.5) & ~RIM0      # passepoil sombre

C_SH = np.array((14, 12, 16), np.float32)
C_BASE = np.array((34, 32, 38), np.float32)
C_MID = np.array((46, 44, 52), np.float32)
C_HI = np.array((92, 92, 104), np.float32)
C_HI2 = np.array((128, 128, 142), np.float32)
C_RED = np.array((150, 22, 36), np.float32)
C_REDH = np.array((214, 52, 64), np.float32)
C_AG = np.array((168, 172, 184), np.float32)
C_AGH = np.array((236, 238, 244), np.float32)

ang = np.arctan2(Y - W_[1], X - W_[0])
far = np.clip(np.hypot(X - W_[0], Y - W_[1]) / 36, 0, 1)


def peindre(face):
    """face = 'out' (cuir verni noir, dos) ou 'in' (doublure rouge sang, côté joueur)."""
    if face == "out":
        col = np.empty((GH, GW, 3), np.float32)
        col[...] = C_BASE
        col = lerp(col, C_MID, (far ** 1.5 * 0.6)[..., None])                 # peau tendue : un peu plus claire vers le bord
        col = lerp(col, C_SH, np.clip(SHA * 1.2, 0, 1)[..., None] * 0.9)       # plis sombres contre les os
        col[LIS] = C_HI2
        col[GLO] = C_HI
        col[RIM1] = C_SH
        col[RIM0] = C_HI
        st_c, st_h = C_RED, C_REDH
    else:
        base, sh, hi = np.array((60, 10, 18), np.float32), np.array((30, 4, 9), np.float32), np.array((92, 20, 30), np.float32)
        col = np.empty((GH, GW, 3), np.float32)
        col[...] = base
        col = lerp(col, hi, (far ** 2 * 0.4)[..., None])
        col = lerp(col, sh, np.clip(SHA * 1.2, 0, 1)[..., None] * 0.9)
        col[RIM1 | RIM0] = (16, 4, 8)
        st_c, st_h = np.array((132, 22, 34), np.float32), np.array((170, 34, 46), np.float32)
    col[STI] = st_c
    col[STI & ~erode(~STI, 0.06)] = st_c
    col[EYE_RING] = C_AG
    col[EYE_HI] = C_AGH
    col[EYE_RING & ~EYE_HI & ((Y - 0) > -1e9)] = col[EYE_RING & ~EYE_HI]
    col[EYE_HOLE] = (8, 6, 10)
    return col


COL_OUT, COL_IN = peindre("out"), peindre("in")
# centre clair des coutures (lisibilité à distance) : le cœur du tiret
_core = (np.array(stitch_img.filter(ImageFilter.MinFilter(3))) > 127) & M
COL_OUT[_core] = lerp(C_RED, C_REDH, 0.35)

# ------------------------------------------------------------------ panneaux : qui porte quoi


def tilted(pts, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(W_[0] + (x - W_[0]) * c - (y - W_[1]) * s, W_[1] + (x - W_[0]) * s + (y - W_[1]) * c) for x, y in pts]


def far_pts(pts, amount):
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    l = math.hypot(x1 - x0, y1 - y0)
    return pts + [(x1 + (x1 - x0) / l * amount, y1 + (y1 - y0) / l * amount)]


PANELS = []


def panel(name, owner, poly):
    m = np.array(fill(poly)) > 127
    PANELS.append(dict(name=name, owner=owner, mask=m & M, layer=LAYER[name]))


for k in range(NF - 1):
    f = FINGERS[k]
    poly = [W_] + far_pts(f["pts"], 3.0)[1:] + list(reversed(far_pts(tilted(RS[k + 1], -3.5), 6.0)))
    panel(f"m{k + 1}", f"d{k + 1}", poly)
f = FINGERS[-1]
poly = [W_] + far_pts(f["pts"], 3.0)[1:] + list(reversed(far_pts(tilted(RAY_A, -3.0), 5.0)))
panel("m4", "d4", poly)
poly = [along([S_, E_], 0.8), E_, (W_[0] + 0.8, W_[1] + 0.2), (W_[0] + 2.6, W_[1] - 3.0)] + \
    far_pts(ray((W_[0] + 2.6, W_[1] - 3.0), (M1[0] + 3.0, M1[1])), 4.0)[1:] + \
    [(M2[0] - 1.8, M2[1] - 4.0), (along([S_, E_], 0.8)[0] - 1.0, along([S_, E_], 0.8)[1] - 4.0)]
panel("m5", "elbow", poly)
poly = [S_, along([S_, E_], 1.0), (E_[0] + 1.2, E_[1] - 2.0), (M2[0] + 1.6, M2[1] - 4.5), (HIP[0] - 1.0, HIP[1] - 3.0), (HIP[0] - 1.2, HIP[1] + 2)]
panel("m6", "shoulder", poly)

# ------------------------------------------------------------------ tuiles peintes


def hook_shape(L, curve):
    return (lambda t: (L * (t - 0.12 * t * t), curve * L * t ** 2.1)), (lambda t: 0.14 * L * (1 - t) ** 0.75 + 0.035 * L)


def paint_hook(W, H, curve, bb):
    """Griffe d'argent arrondie (tuile ; bb = (y bas, y haut) en fraction de L ; x de -0,02 L à 1,04 L)."""
    ss = 4
    ax, ay = np.mgrid[0:H * ss, 0:W * ss][::-1]
    a = lerp(-0.02, 1.04, (ax + 0.5) / (W * ss))
    b = lerp(bb[1], bb[0], (ay + 0.5) / (H * ss))
    center, hw = hook_shape(1.0, curve)
    ts = np.linspace(0, 1, 160)
    dd = np.full(a.shape, 9.0, np.float32)
    side = np.zeros(a.shape, np.float32)
    for t in ts:
        cx, cy = center(t)
        dist_ = np.hypot(a - cx, b - cy) / hw(t)
        better = dist_ < dd
        dd[better] = dist_[better]
        side[better] = (b - cy)[better] / hw(t)
    inside = dd < 1
    c = np.empty(a.shape + (3,), np.float32)
    c[...] = (118, 121, 134)
    c = lerp(c, np.array((236, 238, 244), np.float32), (np.clip((side - 0.25) * 3, 0, 1))[..., None])     # arête claire nette
    c = lerp(c, np.array((58, 60, 70), np.float32), (np.clip((-side - 0.45) * 3, 0, 1))[..., None])
    c = lerp(c, np.array((40, 42, 50), np.float32), (np.clip((dd - 0.82) * 6, 0, 1))[..., None])
    rgb = Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    al = np.array(Image.fromarray(inside.astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110
    out = np.dstack([np.array(rgb), al * 255]).astype(np.uint8)
    out[~al, :3] = (118, 121, 134)
    return out


HOOK_BB = (-0.22, 0.48)
CURVE = 0.30
hook_big = paint_hook(84, 56, CURVE, HOOK_BB)


def strip_tile(w, h, base, hi, sh, mid=None):
    """Bande d'une face de tronçon : arête claire nette en haut, ombre en bas, aplat au milieu (pas de brossé)."""
    a = np.zeros((h, w, 4), np.uint8)
    for yy in range(h):
        q = yy / (h - 1)
        c = lerp(np.array(base, float), np.array(sh, float), max(0.0, q - 0.55) / 0.45 * 0.6)
        a[yy, :, :3] = c
    a[0:2, :, :3] = hi
    if mid is not None:
        a[2, :, :3] = mid
    a[h - 2:, :, :3] = sh
    a[..., 3] = 255
    return a


bone_tile = strip_tile(96, 16, (112, 115, 128), (226, 228, 236), (56, 58, 68), (150, 153, 166))
argent_tile = strip_tile(32, 16, (168, 172, 184), (240, 242, 248), (78, 80, 92), (206, 208, 216))


def leather_tile(w, h, rivet=False, stitch_cols=None):
    a = strip_tile(w, h, (34, 32, 38), (92, 92, 104), (14, 12, 16), (52, 50, 58))
    cols = stitch_cols if stitch_cols is not None else (2, w - 4)
    for c0 in cols:
        for y0 in range(3, h - 3, 5):
            a[y0:y0 + 3, c0:c0 + 2, :3] = (150, 22, 36)
            a[y0 + 1, c0:c0 + 2, :3] = (196, 44, 56)
    if rivet:
        cy, cx = h / 2, w / 2
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.hypot(yy + 0.5 - cy, xx + 0.5 - cx)
        a[d < 2.9, :3] = (78, 80, 92)
        a[d < 2.3, :3] = (168, 172, 184)
        a[(d < 1.6) & (yy + 0.5 < cy) & (xx + 0.5 < cx + 0.6), :3] = (240, 242, 248)
    return a


bague_tile = leather_tile(24, 16, rivet=True)
sangle_tile = leather_tile(40, 16)


def disc_tile(n, fn):
    yy, xx = np.mgrid[0:n, 0:n]
    u, v = (xx + 0.5) / n * 2 - 1, (yy + 0.5) / n * 2 - 1
    return fn(u, v, np.hypot(u, v))


def _cap_leather(u, v, r):
    a = np.zeros(u.shape + (4,), np.uint8)
    a[..., :3] = (34, 32, 38)
    a[(r > 0.78), :3] = (14, 12, 16)
    a[(u + v < -0.9) & (r < 0.78), :3] = (52, 50, 58)
    a[..., 3] = 255
    return a


cap_cuir = disc_tile(12, _cap_leather)


def _rivet(u, v, r):
    a = np.zeros(u.shape + (4,), np.uint8)
    a[..., :3] = (78, 80, 92)
    a[r < 0.9, :3] = (150, 154, 166)
    a[r < 0.62, :3] = (200, 203, 214)
    a[(np.hypot(u + 0.3, v + 0.3) < 0.32), :3] = (244, 246, 250)
    a[..., 3] = 255
    return a


rivet_tile = disc_tile(12, _rivet)


def _patch(u, v, r):
    """Dessus de la pièce de cuir de la racine : couture rouge en cercle, trois clous d'argent."""
    a = np.zeros(u.shape + (4,), np.uint8)
    a[..., :3] = (34, 32, 38)
    a[(u + v < -0.8), :3] = (48, 46, 54)
    a[r > 0.92, :3] = (14, 12, 16)
    th = np.degrees(np.arctan2(v, u)) % 360
    a[(r > 0.70) & (r < 0.80) & ((th % 30) < 18), :3] = (176, 34, 48)
    for k in range(3):
        cx, cy = 0.36 * math.cos(math.radians(90 + 120 * k)), 0.36 * math.sin(math.radians(90 + 120 * k))
        d = np.hypot(u - cx, v - cy)
        a[d < 0.17, :3] = (78, 80, 92)
        a[d < 0.13, :3] = (180, 184, 196)
        a[np.hypot(u - cx + 0.05, v - cy + 0.05) < 0.06, :3] = (244, 246, 250)
    a[..., 3] = 255
    return a


patch_tile = disc_tile(32, _patch)


def buckle_tile(w=26, h=20):
    """Boucle rectangulaire à ardillon, découpée par alpha."""
    ss = 4
    im = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=5 * ss, fill=255)
    d.rounded_rectangle([5 * ss, 5 * ss, w * ss - 1 - 5 * ss, h * ss - 1 - 5 * ss], radius=2 * ss, fill=0)
    d.rectangle([5 * ss, (h // 2 - 1.5) * ss, (w // 2 + 3) * ss, (h // 2 + 1.5) * ss], fill=255)       # ardillon
    al = np.array(im.resize((w, h), Image.LANCZOS)) > 110
    a = np.zeros((h, w, 4), np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    a[..., :3] = (168, 172, 184)
    a[(yy < 2) | (xx < 2), :3] = (240, 242, 248)
    a[(yy >= h - 2) | (xx >= w - 2), :3] = (78, 80, 92)
    a[(yy > h // 2 - 2) & (yy < h // 2 + 2) & (xx > 5) & (xx < w // 2 + 3), :3] = (206, 208, 216)
    a[..., 3] = al * 255
    a[~al, :3] = (168, 172, 184)
    return a


boucle_tile = buckle_tile()


def tail_tile(w=28, h=14):
    """Bout de sangle : cuir verni, coutures le long des bords, bout arrondi, un trou d'ardillon."""
    ss = 4
    im = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=h * ss // 2, fill=255)
    ImageDraw.Draw(im).rectangle([0, 0, w * ss // 2, h * ss - 1], fill=255)
    al = np.array(im.resize((w, h), Image.LANCZOS)) > 110
    a = np.zeros((h, w, 4), np.uint8)
    a[..., :3] = (34, 32, 38)
    a[0:2, :, :3] = (92, 92, 104)
    a[h - 2:, :, :3] = (14, 12, 16)
    for x0 in range(1, w - 6, 4):
        a[3, x0:x0 + 2, :3] = (176, 34, 48)
        a[h - 4, x0:x0 + 2, :3] = (176, 34, 48)
    a[h // 2 - 1:h // 2 + 1, w - 10:w - 8, :3] = (8, 6, 10)
    a[..., 3] = al * 255
    a[~al, :3] = (34, 32, 38)
    return a


bout_tile = tail_tile()


def ring_tile(w=20, h=12):
    """Maillon vu de face : anneau ovale d'argent, découpé par alpha."""
    yy, xx = np.mgrid[0:h * 4, 0:w * 4]
    u, v = (xx + 0.5) / (w * 4) * 2 - 1, (yy + 0.5) / (h * 4) * 2 - 1
    ro = (u / 1.0) ** 2 + (v / 1.0) ** 2
    ri = (u / 0.55) ** 2 + (v / 0.30) ** 2
    m = (ro < 1) & (ri > 1)
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((w, h), Image.LANCZOS)) > 110
    yy, xx = np.mgrid[0:h, 0:w]
    a = np.zeros((h, w, 4), np.uint8)
    a[..., :3] = (168, 172, 184)
    a[yy < h / 2 - 1, :3] = (220, 223, 232)
    a[yy >= h - 3, :3] = (90, 92, 104)
    a[..., 3] = al * 255
    a[~al, :3] = (168, 172, 184)
    return a


maillon_tile = ring_tile()
barre_tile = strip_tile(20, 4, (168, 172, 184), (236, 238, 244), (90, 92, 104))

# ------------------------------------------------------------------ atlas


def best_rect(mask):
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
    _, p["phi"], p["w"], p["h"], p["cx"], p["cy"] = best_rect(p["mask"])

FIXED = [("hook_big", hook_big), ("bone", bone_tile), ("argent", argent_tile), ("bague", bague_tile), ("sangle", sangle_tile),
         ("cap_cuir", cap_cuir), ("rivet", rivet_tile), ("patch", patch_tile), ("boucle", boucle_tile), ("bout", bout_tile),
         ("maillon", maillon_tile), ("barre", barre_tile)]
DIN = 0.62                              # densité de la doublure, relative au cuir verni du dos


def pack(dens):
    items = [(n, im.shape[1], im.shape[0]) for n, im in FIXED]
    for p in PANELS:
        items.append((p["name"] + "_out", int(math.ceil(p["w"] * dens)), int(math.ceil(p["h"] * dens))))
        items.append((p["name"] + "_in", int(math.ceil(p["w"] * dens * DIN)), int(math.ceil(p["h"] * dens * DIN))))
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


DENS = 12.0
while (UV := pack(DENS)) is None:
    DENS -= 0.1
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
for n, im in FIXED:
    u0, v0, u1, v1 = UV[n]
    tex[v0:v1, u0:u1] = im
# coutures des pièces de cuir (bagues, sangles) : faiblement lumineuses dans _e (×2,4 par ajouter_ambiance)
E_RED = np.array((120, 22, 30)) / 2.4
for n in ("bague", "sangle", "bout", "patch"):
    u0, v0, u1, v1 = UV[n]
    t_ = tex[v0:v1, u0:u1]
    red = (t_[..., 0] > 140) & (t_[..., 1] < 60) & (t_[..., 3] > 0)
    tex_e[v0:v1, u0:u1][red] = np.concatenate([E_RED, [255]]).astype(np.uint8)

STI_E = (np.array(stitch_img) > 127) & M
for p in PANELS:
    for face, col, fac in (("out", COL_OUT, 1.0), ("in", COL_IN, DIN)):
        u0, v0, u1, v1 = UV[p["name"] + "_" + face]
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
        al = p["mask"][iy, ix].reshape(H, ss, W, ss).mean(axis=(1, 3)) > 0.5
        cc = col[iy, ix].reshape(H, ss, W, ss, 3).mean(axis=(1, 3))
        if al.any():
            cc[~al] = cc[al].mean(axis=0)
        tex[v0:v1, u0:u1, :3] = np.clip(cc, 0, 255).astype(np.uint8)
        tex[v0:v1, u0:u1, 3] = al * 255
        vm = (STI_E[iy, ix].reshape(H, ss, W, ss).mean(axis=(1, 3)) > 0.3) & al
        tex_e[v0:v1, u0:u1][vm] = np.concatenate([E_RED, [255]]).astype(np.uint8)
        if face == "out":
            p["fill"] = float(al.mean())

CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC
assert set(np.unique(tex[..., 3])) <= {0, 255}, "semi-transparence"
assert set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence _e"


def b64(arr, name):
    img = Image.fromarray(arr, "RGBA")
    img.save(name, optimize=True)
    bb = io.BytesIO()
    img.save(bb, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(bb.getvalue()).decode()


tex_b64 = b64(tex, f"{NOM}.png")
tex_e_b64 = b64(tex_e, f"{NOM}_e.png")

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}
PLAQUES = set()


def nuid():
    return str(_uuid.uuid4())


def cube(name, frm, to, origin, rot=(0, 0, 0), faces=None, plaque=False):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to],
         "origin": [round(v, 4) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(v, 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(rot):
        e["rotation"] = [round(v, 3) for v in rot]
    elements.append(e)
    if plaque:
        PLAQUES.add(e["uuid"])
    return e["uuid"]


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups, name
    groups[name] = {"origin": [round(v, 4) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(v, 2) for v in rotation]}
    return name


def uvs(n, flip=False):
    u0, v0, u1, v1 = UV[n]
    return [u1, v0, u0, v1] if flip else [u0, v0, u1, v1]


def plate(s, g, name, cx, cy, w, h, phi, z, uv_out, uv_in=None, th=EP, flip_v=False):
    """Plaque fine (épaisseur réelle th, gardée par réduire()) : south = dos (uv_out), north = côté joueur (uv_in)."""
    def f(n):
        u0, v0, u1, v1 = UV[n]
        if flip_v:
            v0, v1 = v1, v0
        return (u0, u1) if s > 0 else (u1, u0), v0, v1
    (ua, ub), v0, v1 = f(uv_out)
    (ia, ib), w0, w1 = f(uv_in or uv_out)
    x = s * cx
    faces = {"south": [ua, v0, ub, v1], "north": [ib, w0, ia, w1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
    groups[g]["ids"].append(cube(name, [x - w / 2, cy - h / 2, z - th / 2], [x + w / 2, cy + h / 2, z + th / 2], [x, cy, z],
                                 rot=(0, 0, s * phi), faces=faces, plaque=True))


SH_CAP = un(0.12)       # retrait du second cube d'un octogone devant un bout visible : faces parallèles à 0,12 px réels


def bar(s, g, name, x, y, z, L, q, phi, tile="bone", u0=0.0, u1=1.0, octo=True, ov=0.03, r0=22.5, cap0=None, cap1=None, sh=SH_CAP, dz=0.0):
    """Tronçon le long de l'axe local X, tourné de r0 autour de son axe. cap0/cap1 : tuile du bout de départ / d'arrivée (None = transparent).
    dz : montée en profondeur sur la longueur (L reste la longueur dans le plan de l'aile ; le tronçon penche par une rotation Y)."""
    beta = -math.degrees(math.atan2(dz, L))
    L = math.hypot(L, dz)
    bu0, bv0, bu1, bv1 = UV[tile]
    ua, ub = lerp(bu0, bu1, u0), max(lerp(bu0, bu1, u1), lerp(bu0, bu1, u0) + 2)
    long_ = [ua, bv0, ub, bv1]
    c0 = uvs(cap0) if cap0 else CLEAR
    c1 = uvs(cap1) if cap1 else CLEAR
    a, b = (x - ov, x + L + ov) if s > 0 else (-x - L - ov, -x + ov)
    start, end = ("west", "east") if s > 0 else ("east", "west")
    faces = {"south": long_, "north": long_, "up": long_, "down": long_, start: c0, end: c1}
    o = [s * x, y, z]
    gid = groups[g]["ids"]
    gid.append(cube(name, [a, y - q, z - q], [b, y + q, z + q], o, rot=(r0, s * beta, s * phi), faces=faces))
    if octo:
        d0 = sh if cap0 else 0.0
        d1 = sh if cap1 else 0.0
        a2, b2 = (a + d0, b - d1) if s > 0 else (a + d1, b - d0)
        gid.append(cube(name + "o", [a2, y - q * 0.97, z - q * 0.97], [b2, y + q * 0.97, z + q * 0.97], o, rot=(r0 + 45, s * beta, s * phi), faces=faces))


def chain_bone(s, g, name, pts, r0, r1, z, u0=0.0, u1=1.0, tile="bone", zs=None, ze=None, nz=1, roll=22.5):
    """Os effilé et courbe : tronçons bout à bout, bouts intérieurs transparents. zs / ze : profondeur au départ / à
    l'arrivée, atteinte sur les nz premiers / derniers tronçons (l'os rejoint la profondeur de l'articulation)."""
    n = len(pts) - 1
    zz = [z] * (n + 1)
    if zs is not None:
        for i in range(nz):
            zz[i] = lerp(zs, z, i / nz)
    if ze is not None:
        for i in range(nz):
            zz[n - i] = lerp(ze, z, i / nz)
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        L = math.dist(pts[i], pts[i + 1])
        phi = math.degrees(math.atan2(yb - ya, xb - xa))
        t0, t1 = i / n, (i + 1) / n
        bar(s, g, f"{name}{i}", xa, ya, zz[i], L, lerp(r0, r1, (t0 + t1) / 2), phi, tile, lerp(u0, u1, t0), lerp(u0, u1, t1), ov=0.0, dz=zz[i + 1] - zz[i], r0=roll)


def sleeve(s, g, name, c, phi, L, q, z, tile, cap="cap_cuir", r0=22.5):
    """Manchon centré en c, le long de la direction phi (bague, sangle, embout) ; bouts visibles."""
    dx, dy = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    bar(s, g, name, c[0] - dx * L / 2, c[1] - dy * L / 2, z, L, q, phi, tile, ov=0.0, r0=r0, cap0=cap, cap1=cap)


def axle(s, g, name, x, y, z0, z1, r):
    """Rivet traversant : axe perpendiculaire au plan de l'aile, octogone, têtes bombées."""
    au0, av0, au1, av1 = UV["argent"]
    long_ = [au0, av0, au0 + 12, av1]
    faces = {"south": uvs("rivet"), "north": uvs("rivet"), "up": long_, "down": long_, "east": long_, "west": long_}
    X_ = s * x
    gid = groups[g]["ids"]
    zc = (z0 + z1) / 2
    gid.append(cube(name, [X_ - r, y - r, z0], [X_ + r, y + r, z1], [X_, y, zc], rot=(0, 0, 22.5 * s), faces=faces))
    gid.append(cube(name + "o", [X_ - r * 0.97, y - r * 0.97, z0 + SH_CAP], [X_ + r * 0.97, y + r * 0.97, z1 - SH_CAP], [X_, y, zc], rot=(0, 0, 67.5 * s), faces=faces))


def hook(s, g, name, x, y, z, L, ang, down=True, core=4):
    """Griffe recourbée : peau découpée dans le plan de l'aile + âme pleine plus étroite."""
    lo, hi = HOOK_BB
    if down:
        lo, hi = -hi, -lo
    H = (hi - lo) * L
    Wp = 1.06 * L
    phi = math.radians(ang)
    a0, b0 = (-0.02 + 1.04) / 2 * L, (lo + hi) / 2 * L
    cx, cy = x + a0 * math.cos(phi) - b0 * math.sin(phi), y + a0 * math.sin(phi) + b0 * math.cos(phi)
    plate(s, g, name, cx, cy, Wp, H, ang, z, "hook_big", flip_v=down)
    center, hw = hook_shape(L, -CURVE if down else CURVE)
    for j in range(core):
        t0, t1 = j / core * 0.72, (j + 1) / core * 0.72
        (a, b), (a2, b2) = center(t0), center(t1)
        xa, ya = x + a * math.cos(phi) - b * math.sin(phi), y + a * math.sin(phi) + b * math.cos(phi)
        xb, yb = x + a2 * math.cos(phi) - b2 * math.sin(phi), y + a2 * math.sin(phi) + b2 * math.cos(phi)
        q = max(0.2, hw((t0 + t1) / 2) * 0.55)
        bar(s, g, f"{name}c{j}", xa, ya, z, math.dist((xa, ya), (xb, yb)), q, math.degrees(math.atan2(yb - ya, xb - xa)), "argent", 0.1, 0.9,
            octo=False, ov=0.03, r0=45)


def link(s, g, name, c, phi, face_on, z):
    """Maillon (dimensions réelles : 1,25 de long, 0,72 de large, 0,3 d'épaisseur). face_on : anneau dans le plan de l'aile."""
    Lk, Wk = un(1.25), un(0.72)
    x = s * c[0]
    mu = uvs("maillon", s < 0)
    bu = uvs("barre", s < 0)
    if face_on:
        faces = {"south": mu, "north": uvs("maillon", s > 0), "up": bu, "down": bu, "east": CLEAR, "west": CLEAR}
        frm, to = [x - Lk / 2, c[1] - Wk / 2, z - EP / 2], [x + Lk / 2, c[1] + Wk / 2, z + EP / 2]
    else:
        faces = {"up": mu, "down": uvs("maillon", s > 0), "south": bu, "north": bu, "east": CLEAR, "west": CLEAR}
        frm, to = [x - Lk / 2, c[1] - EP / 2, z - Wk / 2], [x + Lk / 2, c[1] + EP / 2, z + Wk / 2]
    groups[g]["ids"].append(cube(name, frm, to, [x, c[1], z], rot=(0, 0, s * phi), faces=faces, plaque=True))


SEG = ["shoulder", "elbow", "wrist"]
CHAIN = {}
R_HUM, R_AVB = (1.05, 1.0), (1.02, 0.74)
R_P1, R_P2 = (0.80, 0.62), (0.58, 0.38)


def build(s):
    tag = "l" if s < 0 else "r"
    pv = [S_, E_, W_]
    segs = []
    for i in range(3):
        segs.append(group(f"{SEG[i]}_{tag}", [s * pv[i][0], pv[i][1], Z], parent=segs[i - 1] if i else None, rotation=(0, -s * YAW[i], 0)))
    sh, el, wr = segs

    # racine (non réduite) : l'os sort du dos sous une pièce de cuir rivetée
    rt = group(f"wingroot_{tag}", [s * S_[0], S_[1], Z])
    rpts = [(1.9, 21.6), (3.6, 22.2), (S_[0], S_[1])]
    zz = [3.4, lerp(3.4, zr(Z_HUM), 0.55), zr(Z_HUM)]
    for i in range(2):
        (xa, ya), (xb, yb) = rpts[i], rpts[i + 1]
        z_mid = (zz[i] + zz[i + 1]) / 2
        L = math.hypot(math.dist(rpts[i], rpts[i + 1]), zz[i + 1] - zz[i])
        bar(s, rt, f"root{i}_{tag}", xa, ya, z_mid, math.dist(rpts[i], rpts[i + 1]), lerp(0.72, 0.62, i), math.degrees(math.atan2(yb - ya, xb - xa)), "bone", 0.0, 0.08)
    pad_c, pad_r = (2.8, 21.9), 1.3
    su0, sv0, su1, sv1 = UV["sangle"]
    side = [su0, sv0, su0 + 16, sv1]
    pf = {"south": uvs("patch"), "north": CLEAR, "up": side, "down": side, "east": side, "west": side}
    X_ = s * pad_c[0]
    groups[rt]["ids"].append(cube(f"pad_{tag}", [X_ - pad_r, pad_c[1] - pad_r, 2.08], [X_ + pad_r, pad_c[1] + pad_r, 3.9], [X_, pad_c[1], 3.2], faces=pf))
    groups[rt]["ids"].append(cube(f"pad_{tag}o", [X_ - pad_r * 0.97, pad_c[1] - pad_r * 0.97, 2.1], [X_ + pad_r * 0.97, pad_c[1] + pad_r * 0.97, 3.9 - 0.12],
                                  [X_, pad_c[1], 3.2], rot=(0, 0, 45), faces=pf))

    # humérus et avant-bras : légère courbure, section qui s'affine ; os à la profondeur de leurs panneaux
    bow = lambda a, b, k, n: [(lerp(a[0], b[0], i / n) - k * (b[1] - a[1]) * math.sin(math.pi * i / n),
                               lerp(a[1], b[1], i / n) + k * (b[0] - a[0]) * math.sin(math.pi * i / n)) for i in range(n + 1)]
    chain_bone(s, sh, f"hum_{tag}", bow(S_, E_, 0.08, 3), *R_HUM, couche(Z_HUM), 0.05, 0.3, ze=couche(Z_COU))
    chain_bone(s, el, f"avb_{tag}", bow(E_, W_, -0.07, 4), *R_AVB, couche(Z_AVB), 0.3, 0.55, zs=couche(Z_COU), ze=couche(Z_POI), roll=5)
    # bagues de cuir cloutées aux articulations, rivets traversants
    sleeve(s, sh, f"bg_epaule_{tag}", along([S_, E_], 0.12), math.degrees(math.atan2(E_[1] - S_[1], E_[0] - S_[0])), 2.2, R_HUM[0] + 0.32, couche(Z_HUM), "bague")
    ang_e = math.degrees(math.atan2(W_[1] - E_[1], W_[0] - E_[0]))
    sleeve(s, el, f"bg_coude_{tag}", E_, (ang_e + 64) / 2, 2.6, 1.4, couche(Z_COU), "bague")
    axle(s, el, f"rv_coude_{tag}", E_[0], E_[1], couche(Z_COU) - un(1.32), couche(Z_COU) + un(1.32), un(0.36))
    sleeve(s, wr, f"bg_poignet_{tag}", (W_[0] - 0.3, W_[1] - 0.1), ang_e, 2.6, 1.35, couche(Z_POI), "bague")
    axle(s, wr, f"rv_poignet_{tag}", W_[0] - 0.3, W_[1] - 0.1, couche(Z_POI) - un(1.5), couche(Z_POI) + un(1.5), un(0.36))
    # sangle à boucle autour de l'avant-bras ; la boucle est posée sur le dos de la sangle
    sc = along(bow(E_, W_, -0.07, 4), 0.52)
    qs = 1.5
    sleeve(s, el, f"sangle_{tag}", sc, ang_e, 2.7, qs, couche(Z_AVB), "sangle", r0=0)
    z_bk = couche(Z_AVB) + 0.97 * qs * math.sqrt(2) + un(0.1 + EP / 2)
    plate(s, el, f"boucle_{tag}", sc[0], sc[1], un(1.05), un(1.8), ang_e, z_bk, "boucle")
    dx, dy = math.cos(math.radians(ang_e - 90)), math.sin(math.radians(ang_e - 90))
    plate(s, el, f"bout_{tag}", sc[0] + dx * un(1.65), sc[1] + dy * un(1.65), un(1.5), un(0.82), ang_e - 90, z_bk, "bout")

    # pouce : griffe d'argent arrondie au poignet
    th = group(f"thumb_{tag}", [s * W_[0], W_[1], Z], parent=wr)
    tpts = arc_from(W_, 74, 3.4, 8, 2)
    chain_bone(s, th, f"thb_{tag}", tpts, 0.82, 0.66, couche(9.5), 0.5, 0.65, zs=couche(Z_POI))
    hook(s, th, f"griffe_{tag}", tpts[-1][0], tpts[-1][1], couche(9.5), 9.4, 80, down=True, core=4)
    sleeve(s, th, f"bg_pouce_{tag}", tpts[-1], 80, 1.4, 0.98, couche(9.5), "argent", cap="rivet")

    # doigts : deux phalanges, bague cloutée à la jointure, embout d'argent arrondi au bout
    for k, f in enumerate(FINGERS):
        d = group(f"d{k + 1}_{tag}", [s * W_[0], W_[1], Z], parent=wr)
        db = group(f"d{k + 1}b_{tag}", [s * f["J"][0], f["J"][1], Z], parent=d)
        zf = couche(ZF[k])
        chain_bone(s, d, f"f{k + 1}a_{tag}", f["p1"], *R_P1, zf, 0.55, 0.78, zs=couche(Z_POI), roll=ROLL[k])
        chain_bone(s, db, f"f{k + 1}b_{tag}", f["p2"], *R_P2, zf, 0.78, 1.0, roll=ROLL[k])
        sleeve(s, db, f"bg_j{k + 1}_{tag}", f["J"], f["a"] + f["b1"], 1.7, R_P1[1] + 0.3, zf, "bague")
        e_ = f["end"]
        dx, dy = math.cos(math.radians(e_)), math.sin(math.radians(e_))
        tip = f["tip"]
        sleeve(s, db, f"emb{k + 1}_{tag}", (tip[0] + dx * 0.5, tip[1] + dy * 0.5), e_, 1.6, R_P2[1] + 0.26, zf, "argent", cap="rivet")
        sleeve(s, db, f"embd{k + 1}_{tag}", (tip[0] + dx * 1.2, tip[1] + dy * 1.2), e_, 1.3, (R_P2[1] + 0.26) * 0.62, zf, "argent", cap="rivet")

    # membrane : un panneau par doigt + avant-bras + humérus, chacun sur sa couche
    names = {"elbow": el, "shoulder": sh}
    for p in PANELS:
        owner = names.get(p["owner"], f"{p['owner']}_{tag}")
        plate(s, owner, f"{p['name']}_{tag}", p["cx"], p["cy"], p["w"], p["h"], p["phi"], couche(p["layer"]), p["name"] + "_out", p["name"] + "_in")

    # chaîne : du poignet à la première jointure du grand doigt, côté dos, au-dessus de la membrane ; pend en arc.
    # Un groupe porteur tourné le long de la corde (base z = angle de la corde), puis trois groupes imbriqués qui pivotent
    # autour de la corde : les deux bouts restent accrochés, le milieu balance plus fort et avec un retard.
    f0 = FINGERS[0]
    A_, B_ = (W_[0] + 1.6, W_[1] + 0.25), f0["J"]
    chord = math.degrees(math.atan2(B_[1] - A_[1], B_[0] - A_[0]))
    sag = 2.6
    zc = couche(LAYER["m1"]) + un(EP / 2 + 0.1 + 0.37)
    path = [(lerp(A_[0], B_[0], u), lerp(A_[1], B_[1], u) - sag * 4 * u * (1 - u)) for u in np.linspace(0, 1, 60)]
    NL = 11
    cs = [along(path, lerp(0.02, 0.98, i / (NL - 1))) for i in range(NL)]
    cr, sr = math.cos(math.radians(-chord)), math.sin(math.radians(-chord))
    loc = lambda p: (A_[0] + (p[0] - A_[0]) * cr - (p[1] - A_[1]) * sr, A_[1] + (p[0] - A_[0]) * sr + (p[1] - A_[1]) * cr)
    piv = [s * A_[0], A_[1], zc]
    gw = group(f"chn_{tag}", piv, parent=f"d1_{tag}", rotation=(0, 0, s * chord))
    g0 = group(f"ch0_{tag}", piv, parent=gw)
    g1 = group(f"ch1_{tag}", piv, parent=g0)
    g2 = group(f"ch2_{tag}", piv, parent=g1)
    owner = [g0, g0, g1, g1, g2, g2, g2, g1, g1, g0, g0]
    for i, c in enumerate(cs):
        a_ = cs[max(0, i - 1)]
        b_ = cs[min(NL - 1, i + 1)]
        phi = math.degrees(math.atan2(b_[1] - a_[1], b_[0] - a_[0])) - chord
        link(s, owner[i], f"ml{i}_{tag}", loc(c), phi, face_on=(i % 2 == 1), z=zc)
    ga, ga2, gb, gb2 = g0, g1, g2, None
    CHAIN[tag] = (ga, ga2, gb, gb2)
    return rt, sh


(LR_, L_), (RR_, R_) = build(-1), build(1)


def sous_arbre(racine):
    res = [racine]
    while True:
        plus = [n for n, g in groups.items() if g["parent"] in res and n not in res]
        if not plus:
            return res
        res += plus


def reduire(racine, s):
    """Réduit toute l'aile par K autour de l'épaule (pivots et cubes) ; les plaques gardent leur épaisseur."""
    P = np.array((s * S_[0], S_[1], Z))
    T = lambda v: P + K * (np.array(v, float) - P)
    par_uuid = {e["uuid"]: e for e in elements}
    for n in sous_arbre(racine):
        g = groups[n]
        g["origin"] = [round(v, 4) for v in T(g["origin"])]
        for u in g["ids"]:
            e = par_uuid[u]
            o = np.array(e["origin"], float)
            a, b = np.array(e["from"]) - o, np.array(e["to"]) - o
            k = np.full(3, K)
            if u in PLAQUES:
                k[int(np.argmin(b - a))] = 1.0
            o2 = T(o)
            e["origin"] = [round(v, 4) for v in o2]
            e["from"] = [round(v, 4) for v in o2 + a * k]
            e["to"] = [round(v, 4) for v in o2 + b * k]


reduire(L_, -1)
reduire(R_, 1)


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(),
             "children": [{"name": "item", "origin": [0, 0, 0], "uuid": nuid(),
                           "children": [bone(LR_), bone(RR_), bone(L_), bone(R_)]}]}]

# ------------------------------------------------------------------ animations
# Les courbes décrivent l'aile GAUCHE en termes d'intention :
#   fx > 0 : le plan bascule vers l'horizontale ; fy > 0 : pivote vers l'arrière ; fz > 0 : la pointe monte.
#   fold : 0 = doigts grands ouverts (pose du modèle), 1 = éventail fermé. curl : les dernières phalanges se creusent (≤ 4°).
# MIROIR D'AXES : seul endroit à toucher si la convention du mod change (un signe suffit).
# Repères de docs/guide-cosmetiques.md, section 3.
SX, SY, SZ = -1, -1, +1


def mirror(s, fx, fy, fz):
    """s = -1 aile gauche, +1 aile droite. Renvoie les valeurs de keyframe."""
    return SX * fx, s * SY * fy, s * SZ * fz


CLOSE = [52, 32, 12, -10]                # fermeture de chaque doigt à fold = 1 (degrés), vers D4
CURLW = [1.0, 0.9, 0.75, 0.55]


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 3)), "y": str(round(y + 0.0, 3)), "z": str(round(z + 0.0, 3))}],
            "time": round(t, 4), "interpolation": "linear"}


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


def anim(name, length, segs, fold, curl=C(0), n_kf=None, loop="loop", only=None, swing=(6, 1), scale=None, thumb=None):
    """segs : shoulder/elbow/wrist -> (fx, fy, fz). only : familles animées (attaque, blessé). swing : (amplitude °, nombre
    d'oscillations par boucle) de la chaîne, ou une fonction t -> angle. scale : échelle de l'épaule (événements)."""
    A = {}

    def put(g, kfs):
        if only is None or re.sub(r"\d*_[lr]$", "", g) in only:
            A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}

    n = n_kf or max(6, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]
    sw = swing if callable(swing) else (lambda t, a=swing[0], k=swing[1]: a * math.sin(TAU * k * t / length))
    lagged = lambda t, lag: sw((t - lag) % length) if loop == "loop" else sw(max(0.0, t - lag))
    for s, tag in ((-1, "l"), (1, "r")):
        for seg, (fx, fy, fz) in segs.items():
            kk = [kf("rotation", t, *mirror(s, fx(t), fy(t), fz(t))) for t in times]
            if seg == "shoulder" and scale is not None:
                kk += [kf("scale", t, scale(t), scale(t), scale(t)) for t in times]
            put(f"{seg}_{tag}", kk)
        for k in range(NF):
            dl = 0.03 * length * (NF - 1 - k)
            put(f"d{k + 1}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, -CLOSE[k] * fold((t - dl) % length if loop == "loop" else max(0.0, t - dl)))) for t in times])
            put(f"d{k + 1}b_{tag}", [kf("rotation", t, *mirror(s, 0, 0, -CURLW[k] * curl(t))) for t in times])
        th = thumb or (lambda t: 30 * max(0.0, fold(t)))
        put(f"thumb_{tag}", [kf("rotation", t, *mirror(s, 0, 0, th(t))) for t in times])
        g0, g1, g2, _ = CHAIN[tag]
        lag = 0.10 * length / max(1, (swing[1] if not callable(swing) else 1))
        put(g0, [kf("rotation", t, *mirror(s, lagged(t, 0), 0, 0)) for t in times])
        put(g1, [kf("rotation", t, *mirror(s, 0.35 * lagged(t, lag), 0, 0)) for t in times])
        put(g2, [kf("rotation", t, *mirror(s, 0.35 * lagged(t, 2 * lag), 0, 0)) for t in times])
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "idle", "animators": A}


Z0 = C(0)

# idle 8 s : repos, à demi fermé, respiration (4 s) + étirement ample 4,6–7,2 s
st = lambda t: bump(t, 4.6, 5.4, 6.0, 7.2)
mix = lambda f, v: (lambda t: f(t) * (1 - st(t)) + v * st(t))
idle = anim("idle", 8.0, {
    "shoulder": (mix(S(4, 1.0, 0, 6), 14), mix(S(4, 1.5, 0, 24), -4), mix(S(4, 2, 0, -10), 10)),
    "elbow":    (Z0, mix(S(4, 1, -40, -10), -4), mix(S(4, 1.5, -40, -12), 4)),
    "wrist":    (Z0, mix(S(4, 0.8, -70, 10), -6), mix(S(4, 1, -70, -18), 3))},
    fold=lambda t: (0.55 + 0.05 * math.sin(TAU * t / 4)) * (1 - st(t)) - 0.04 * st(t), curl=lambda t: (2 + 1 * math.sin(TAU * t / 4)) * (1 - st(t)),
    n_kf=48, swing=lambda t: 5 * math.sin(TAU * t / 4) + 7 * st(t) * math.sin(TAU * t / 1.0))

# fly 2,4 s : joueur debout en vol créatif, plan basculé d'environ 40°, battement ample ; descente tendue, remontée repliée
T = 2.4
up = lambda t, lag=0.0: 0.5 + 0.5 * math.cos(TAU * (t / T - lag))
fly = anim("fly", T, {
    "shoulder": (S(T, 4, 90, 40), S(T, 5, 90, -13), S(T, 22, 0, 0)),
    "elbow":    (Z0, lambda t: 8 - 4 * up(t, 0.12), S(T, 8, -45, -2)),
    "wrist":    (Z0, lambda t: -8 + 4 * up(t, 0.22), lambda t: 2 + 5 * math.sin(TAU * t / T - math.radians(75)) - 16 * up(t, 0.22))},
    fold=lambda t: 0.02 + 0.42 * up(t, 0.2), curl=lambda t: 0.5 + 3.5 * up(t, 0.26), n_kf=24, swing=(16, 2))

# glide 3,6 s : joueur couché, presque dans le plan du dos, grandes ouvertes ; battement lent et à la fusée (seuil validé)
G = 3.6
BOOST = f"math.clamp((math.max(q.ground_speed,q.vertical_speed)-{V0})/{DV},0,1)*math.clamp((q.vertical_speed+8)/4,0,1)"


def term(amp, speed, ph):
    if not amp:
        return ""
    p = f"{ph:+g}" if ph else ""
    return f"{amp:+g}*math.sin(q.anim_time*{speed}{p})"


def mol(sign, base, slow=(0, 0), boost=(0, 0)):
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
        sx, sy, sz = mirror(s_, 1, 1, 1)
        put(f"shoulder_{tag}", mol(sx, 8, (1.5, 90)), mol(sy, -14, (11, 0), (24, 0)), f"{sz * -4:g}")
        put(f"elbow_{tag}", "0", mol(sy, 8, (-3, -43), (11, -45)), f"{sz * 1:g}")
        put(f"wrist_{tag}", "0", mol(sy, -8, (4, -79), (13, -90)), f"{sz * 2:g}")
        for k in range(NF):
            c = CLOSE[k]
            put(f"d{k + 1}_{tag}", "0", "0", mol(sz, round(-c * 0.08, 2), (round(c * 0.05, 2), 90), (round(c * 0.07, 2), -90)))
            put(f"d{k + 1}b_{tag}", "0", "0", mol(sz, round(-1.5 * CURLW[k], 2), (round(1.0 * CURLW[k], 2), 60), (round(-2.5 * CURLW[k], 2), -120)))
        g0, g1, g2, _ = CHAIN[tag]
        for g_, a_, ph in ((g0, 1.0, 0), (g1, 0.35, -36), (g2, 0.35, -72)):
            put(g_, mol(sx, 0, (round(8 * a_, 2), ph), (round(10 * a_, 2), ph)), "0", "0")
    return {"uuid": nuid(), "name": "glide", "loop": "loop", "override": False, "length": G, "snapping": 24, "selected": False, "animators": A}


glide = glide_anim()

# fall 1,5 s : joueur debout, ailes relevées et ouvertes, plan demi-basculé (~26°) : freinage
AI = 1.5
fall = anim("fall", AI, {"shoulder": (S(AI, 3, 0, 26), C(-4), S(AI, 4, 0, 12)),
                         "elbow": (Z0, C(3), S(AI, 3, -40, 5)),
                         "wrist": (Z0, C(-4), S(AI, 3, -70, 4))},
            fold=S(AI, 0.05, 0, 0.09), curl=S(AI, 1.5, -60, 2), swing=(12, 2))

# walk 1,6 s : ramenées vers l'arrière, à moitié fermées, balancement au pas
W = 1.6
walk = anim("walk", W, {"shoulder": (C(8), S(W, 5, 0, 40), S(W, 3.5, 0, -6)),
                        "elbow": (Z0, S(W, 3, -40, -14), S(W, 2, -40, -18)),
                        "wrist": (Z0, S(W, 3, -70, 12), S(W, 2.5, -70, -10))},
            fold=C(0.75), curl=S(W, 1.5, -70, 2), swing=(10, 1))

# run 1,0 s : très vers l'arrière, abaissées, repli en S réparti sur les 3 articulations, éventail presque fermé
R_ = 1.0
run = anim("run", R_, {"shoulder": (C(16), S(R_, 3, 0, 58), S(R_, 3, 0, -8)),
                       "elbow": (Z0, S(R_, 2, -40, -24), S(R_, 1.5, -40, -20)),
                       "wrist": (Z0, S(R_, 3, -80, 26), S(R_, 2, -80, -8))},
           fold=C(0.9), curl=S(R_, 1.5, -60, 2), swing=(14, 1))

# sneak 3 s : éventail fermé, plis serrés dans le dos, griffe du pouce au-dessus de l'épaule
SN = 3.0
sneak = anim("sneak", SN, {"shoulder": (C(7), S(SN, 1, 0, 55), S(SN, 1, 0, -3)),
                           "elbow": (Z0, C(-15), S(SN, 1, -40, -20)),
                           "wrist": (Z0, C(5), C(-10))},
             fold=S(SN, 0.015, 0, 0.985), curl=C(3), swing=(5, 1))

# sleep 4 s : repliées, tombantes
SL = 4.0
sleep = anim("sleep", SL, {"shoulder": (C(12), S(SL, 1, 0, 58), S(SL, 1, 0, -12)),
                           "elbow": (Z0, C(-15), C(-20)),
                           "wrist": (Z0, C(6), S(SL, 1.5, -60, 0))},
             fold=C(1.0), curl=S(SL, 1, -60, 3), swing=(3, 1))

# swim 2 s : joueur couché ; ailes dans le plan du dos, rabattues vers les pieds, à demi fermées ; ondulation
SW = 2.0
swim = anim("swim", SW, {"shoulder": (C(7), S(SW, 7, 0, 2), C(-34)),
                         "elbow": (Z0, S(SW, 6, -45, 6), C(-10)),
                         "wrist": (Z0, S(SW, 7, -90, -4), C(-10))},
            fold=C(0.65), curl=S(SW, 2, -120, 2), swing=(6, 1))

# mount 3 s : repos relevé, pointes hautes, respiration ample
MT = 3.0
mount = anim("mount", MT, {"shoulder": (C(10), S(MT, 2.5, 0, 8), S(MT, 3.5, 0, 12)),
                           "elbow": (Z0, S(MT, 1.5, -40, -4), S(MT, 2, -40, 5)),
                           "wrist": (Z0, C(2), S(MT, 2, -70, -2))},
             fold=S(MT, 0.04, 0, 0.3), curl=S(MT, 1, -40, 2), swing=(8, 1))

# attack et hurt : une fois par-dessus l'état, dernière image neutre, seuls les groupes concernés
IMPULSE = {"shoulder", "elbow", "wrist", "d", "thumb", "ch"}
AT = 0.8
atk = lambda t: bump(t, 0.0, 0.14, 0.30, 0.72)
attack = anim("attack", AT, {"shoulder": (lambda t: 24 * atk(t), lambda t: -12 * atk(t), lambda t: 12 * atk(t)),
                             "elbow": (Z0, lambda t: -6 * atk(t), lambda t: 5 * atk(t)),
                             "wrist": (Z0, lambda t: -8 * atk(t), lambda t: 6 * atk(t))},
              fold=lambda t: -0.08 * atk(t), n_kf=16, loop="once", only=IMPULSE,
              swing=lambda t: 18 * bump(t, 0.1, 0.25, 0.35, 0.8) * math.sin(TAU * t / 0.4), thumb=lambda t: 0.0)

HU = 0.8
hu = lambda t: bump(t, 0.0, 0.08, 0.22, 0.72)
tr = lambda t: 3 * math.sin(TAU * t * 5 / HU) * (1 - sm(t, 0.25, 0.7))
hurt = anim("hurt", HU, {"shoulder": (lambda t: 6 * hu(t), lambda t: 16 * hu(t), lambda t: 8 * hu(t) + tr(t)),
                         "elbow": (Z0, lambda t: -6 * hu(t), lambda t: -3 * hu(t) + tr(t)),
                         "wrist": (Z0, lambda t: 8 * hu(t), lambda t: -3 * hu(t) + tr(t))},
            fold=lambda t: 0.25 * hu(t), n_kf=16, loop="once", only=IMPULSE,
            swing=lambda t: 16 * (1 - sm(t, 0.1, 0.8)) * math.sin(TAU * t / 0.32), thumb=lambda t: 0.0)

# event_equip 3,6 s (par-dessus l'état, rotations ajoutées, échelles multipliées) : les ailes sortent du dos toutes petites et
# serrées, grandissent, se déplient de l'épaule vers les doigts, s'étirent d'un coup (éventail un peu plus ouvert), puis reviennent au neutre.
EQ = 3.6
gr = lambda t: lerp(0.04, 1.0, sm(t, 0.0, 1.1))
pli = lambda t: 1 - sm(t, 0.9, 2.5)
etire = lambda t: bump(t, 2.3, 2.7, 2.9, 3.5)
equip = anim("event_equip", EQ, {"shoulder": (lambda t: 6 * etire(t), lambda t: 22 * pli(t), lambda t: -10 * pli(t) + 9 * etire(t)),
                                 "elbow": (Z0, lambda t: -10 * pli(t), lambda t: -12 * (1 - sm(t, 1.2, 2.6))),
                                 "wrist": (Z0, lambda t: 6 * pli(t), lambda t: -26 * (1 - sm(t, 1.5, 2.8)) + 4 * etire(t))},
             fold=lambda t: 0.45 * (1 - sm(t, 1.6, 2.9)) - 0.06 * etire(t), n_kf=36, loop="once", scale=gr,
             swing=lambda t: 12 * bump(t, 2.4, 2.7, 2.9, 3.6) * math.sin(TAU * t / 0.5), thumb=lambda t: 20 * (1 - sm(t, 1.5, 2.8)))

# event_unequip 4 s : repli soigné (doigts, puis coude, puis épaule), les ailes rentrent dans le dos et rapetissent ; dernière image presque nulle
UQ = 4.0
fin = lambda t: sm(t, 2.6, 3.9)
unequip = anim("event_unequip", UQ, {"shoulder": (Z0, lambda t: 22 * sm(t, 1.4, 3.0), lambda t: -10 * sm(t, 1.4, 3.0)),
                                     "elbow": (Z0, lambda t: -10 * sm(t, 1.0, 2.6), lambda t: -12 * sm(t, 1.0, 2.4)),
                                     "wrist": (Z0, lambda t: 6 * sm(t, 0.6, 2.2), lambda t: -26 * sm(t, 0.6, 2.0))},
               fold=lambda t: 0.45 * sm(t, 0.0, 1.4), n_kf=32, loop="once", scale=lambda t: lerp(1.0, 0.02, fin(t)),
               swing=lambda t: 9 * (1 - sm(t, 0.0, 2.0)) * math.sin(TAU * t / 0.6), thumb=lambda t: 20 * sm(t, 0.6, 2.0))


def son(a, t, nom):
    a["animators"]["effects"] = {"name": "Effects", "type": "effect",
                                 "keyframes": [{"channel": "sound", "data_points": [{"effect": nom, "file": ""}], "time": t}]}


son(equip, 0.1, "item.armor.equip_leather")
son(unequip, 0.4, "item.armor.equip_leather")

ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, attack, hurt, equip, unequip]
assert len(ANIMS) <= 15
assert 250 <= len(elements) <= 450, f"budget : {len(elements)} cubes"

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model)
from ambiance import ajouter_ambiance
ajouter_ambiance(model)
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))
with open(OUT) as fh:
    json.load(fh)


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 2, "groupes ; profondeur", depth(outliner[0]), ";", len(model["animations"]), "anims ;",
      sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      f"densité membrane {DENS:.1f} texels/px (avant réduction) ; panneaux {len(PANELS)} par aile")
