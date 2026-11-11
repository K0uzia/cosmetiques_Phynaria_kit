"""DOCSTRING"""
import base64, io, json, math, os, random, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image, ImageDraw

NOM = "skin_lance_givre"
TEX = 512
TAU = 2 * math.pi
FOLD = 0.1

# Repère (catégorie objets) : lance pointe vers +Y, centrée ; a le long de la hampe (-> +Y), b en travers (-> -X), z (-> +Z).
# Même longueur et même prise que skin_lance_orage (réglages Display validés en jeu le 2026-11-05).
A_MIN, A_MAX = -12.3, 21.7
A_ = np.array((0.0, 1.0, 0.0))
W_ = np.array((-1.0, 0.0, 0.0))
T_ = np.array((0.0, 0.0, 1.0))
P0 = np.array((8.0, 8.0 - (A_MIN + A_MAX) / 2, 8.0))


def Wp(a, b=0.0, z=0.0):
    return P0 + A_ * a + W_ * b + T_ * z


def Wv(a, b=0.0, z=0.0):
    return A_ * a + W_ * b + T_ * z


def lerp(a, b, k):
    return a + (b - a) * k


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


C = lambda *c: np.array(c, np.float32)
G_DEEP, G_BODY, G_PALE, G_LIGHT = C(30, 96, 168), C(92, 186, 232), C(168, 226, 250), C(214, 244, 255)
BLANC = C(244, 253, 255)
LUEUR = C(150, 226, 255)
ARG_L, ARG_M, ARG_D = C(236, 244, 250), C(166, 186, 206), C(74, 90, 116)

def bez(P, s):
    P = [np.array(p, float) for p in P]
    u = 1 - s
    c = u ** 3 * P[0] + 3 * u * u * s * P[1] + 3 * u * s * s * P[2] + s ** 3 * P[3]
    d = 3 * u * u * (P[1] - P[0]) + 6 * u * s * (P[2] - P[1]) + 3 * s * s * (P[3] - P[2])
    return c, d / np.linalg.norm(d)

def courbe(B, n=40):
    return [tuple(bez(B, s)[0]) for s in np.linspace(0, 1, n)]


def in_poly(P, poly):
    x, y = P[..., 0], P[..., 1]
    ins = np.zeros(x.shape, bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1)
        ins ^= c
    return ins


def d_poly(P, pts):
    d = np.full(P.shape[:-1], 1e9)
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i]), np.array(pts[i + 1])
        ab = b - a
        t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
        d = np.minimum(d, np.linalg.norm(P - (a + t[..., None] * ab), axis=-1))
    return d


def resample(pts, pas):
    P = np.array(pts, float)
    ls = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    n = max(1, int(round(ls[-1] / pas)))
    out = []
    for x in np.linspace(0, ls[-1], n + 1):
        i = min(np.searchsorted(ls, x, side="right") - 1, len(P) - 2)
        k = (x - ls[i]) / max(ls[i + 1] - ls[i], 1e-9)
        out.append(P[i] + (P[i + 1] - P[i]) * k)
    return [tuple(p) for p in out]

# ------------------------------------------------------------------ vrai volume (peau trans_ + âme opaque)
Z_E = 0.10                       # demi-épaisseur au fil
T_BIS = 0.50                     # pente unique des biseaux (27°) : section losange, 1,7 px à l'épaule, 0,2 au bout
TH = 0.3
DF = 16.0
DELTA = 0.20                     # retrait de l'âme
ZC_MIN = 0.05
RECOUV_AME = 0.08
SQ = math.sqrt(1 + T_BIS ** 2)
D_OFF = (ZC_MIN - Z_E + DELTA * SQ) / T_BIS          # bord de l'âme depuis le fil
D_EXTRA = DELTA * (SQ - 1) / T_BIS                   # arête biseau/plat de l'âme plus loin que celle de la peau
AL = math.atan(T_BIS)


def subdiv(pts, maxlen=2.0):
    out = []
    for i in range(len(pts) - 1):
        p, q = np.array(pts[i], float), np.array(pts[i + 1], float)
        n = max(1, int(math.ceil(np.linalg.norm(q - p) / maxlen)))
        for k in range(n):
            out.append((p + (q - p) * k / n, p + (q - p) * (k + 1) / n, k == 0, k == n - 1))
    return out


def d_stack(P, segs):
    out = []
    for p, q, *_ in segs:
        ab = q - p
        t = np.clip(((P - p) @ ab) / (ab @ ab), 0, 1)
        out.append(np.linalg.norm(P - (p + t[..., None] * ab), axis=-1))
    return np.stack(out)


# ------------------------------------------------------------------ fer : long cristal en feuille, section losange
A_O = 12.9                   # centre du collet (le fer naît dedans)
O_ = np.array((A_O, 0.0))
R_COL = 1.15                 # apothème du collet (octogone, axe z)
Z_COL = 0.85                 # demi-épaisseur du collet
TIP = np.array((A_MAX, 0.0))
# demi-largeur du fer le long de a : racine cachée dans le collet, épaule anguleuse, long effilement convexe
HA = [A_O - 0.3, 13.6, 15.0, 16.0, 19.5, A_MAX]
HW = [0.50, 0.75, 1.45, 1.35, 0.62, 0.0]
U_F = [(a, w) for a, w in zip(HA[1:], HW[1:])]
P_FER = [(HA[0], HW[0])] + U_F + [(a, -w) for a, w in U_F[::-1][1:]] + [(HA[0], -HW[0])]
FIL_FER = U_F + [(a, -w) for a, w in U_F[::-1][1:]]
U_FER = np.array((1.0, 0.0))
L_FER = A_MAX - A_O


def hw_fer(a):
    return np.interp(a, HA, HW)


class Bras:
    """Plaque biseautée fermée : contour poly, fil (polyligne, sans la racine cachée dans le collet)."""

    def __init__(self, nom, poly, fil, u, L, centre):
        self.nom, self.poly, self.centre = nom, poly, centre
        self.u = unit(np.asarray(u, float))
        self.k = 0.0
        self.L = L
        self.segs = subdiv(fil)

    def h(self, P):
        """Section losange : le « plat » est juste au-dessus de l'arête, les biseaux se rejoignent au milieu (pas de table)."""
        a = np.asarray(P, float)[..., 0]
        return Z_E + T_BIS * (hw_fer(a) + 0.06)

    def wb(self, P):
        return np.maximum((self.h(P) - Z_E) / T_BIS, 0.02)

    def dE(self, P):
        return d_stack(P, self.segs).min(0)

    def s(self, P):
        """0 au collet -> 1 à la pointe."""
        return np.clip(((np.asarray(P, float) - O_) @ self.u) / self.L, 0, 1)

    def ame_ok(self, P):
        return self.h(P) - DELTA > ZC_MIN + 0.03


# plume de givre : nervure dans l'arête, barbes en chevron vers la pointe (cœur cyan _e)
VEINES = [[(13.3, 0.0), (20.6, 0.0)]]
for a0 in np.arange(14.3, 19.8, 0.95):
    for sg in (1, -1):
        VEINES.append([(a0, 0.0), (a0 + 0.62, sg * 0.6 * hw_fer(a0 + 0.62))])
B_FER = Bras("fer", P_FER, FIL_FER, U_FER, L_FER, VEINES)


EPS_PEAU = 0.05                  # peau : chaque tronçon déborde de 0,05 px sur le précédent seulement (pas de fente, pas d'alpha doublé)


def proprietaire(D, idx, P2=None, segs=None):
    """Cellule du tronçon idx, plus une bande de EPS_PEAU au-delà de la bissectrice qui le sépare du tronçon précédent."""
    am = np.argmin(D, axis=0)
    own = am == idx
    if P2 is None or idx == 0:
        return own
    p0, q0 = segs[idx - 1][0], segs[idx - 1][1]
    p1, q1 = segs[idx][0], segs[idx][1]
    if np.linalg.norm(q0 - p1) > 1e-6:
        return own
    nb = unit(unit(q0 - p0) + unit(q1 - p1))           # normale de la bissectrice, du précédent vers idx
    return own | ((am == idx - 1) & (((P2 - p1) @ nb) > -EPS_PEAU))


def d_veines(P2, veines):
    return np.min(np.stack([d_poly(P2, v) for v in veines]), axis=0)


def chevrons(pc, P2):
    db = d_veines(P2, pc.centre)
    return (np.floor((((P2 - O_) @ pc.u) * 0.75 + 2.2 * db) / 1.3) % 2) * 2 - 1


# --- peintures : (couleur, alpha | None, émissif | None) ; d = distance au fil
def peau_plat(pc, P2, d, sg):
    s = pc.s(P2)[..., None]
    return lerp(C(104, 192, 236), C(168, 226, 250), s), np.full(P2.shape[:-1], 170.0), None


def peau_biseau(pc, P2, d, sg):
    hw = np.maximum(hw_fer(P2[..., 0]), 0.05)
    f = np.clip(np.abs(P2[..., 1]) / hw, 0, 1)            # 0 à l'arête, 1 au fil
    g = chevrons(pc, P2)
    s = pc.s(P2)
    col = lerp(C(150, 214, 244), C(200, 240, 255), f[..., None]) * (1 + 0.04 * g)[..., None]
    al = 160 + 30 * s + 8 * g
    frange = d < D_OFF + 0.04                      # pas d'âme derrière : glace claire plus dense, pas de vide
    arete = np.abs(P2[..., 1]) < 0.07
    for m, c, a in ((frange, C(206, 240, 255), 214), (arete, BLANC, 214), (d < 0.1, BLANC, 228)):
        col = np.where(m[..., None], c, col)
        al = np.where(m, a, al)
    return col, al, None


def peau_fil(pc, P2, d, sg):
    return np.zeros(P2.shape[:-1] + (3,), np.float32) + BLANC, np.full(P2.shape[:-1], 226.0), None


def ame_biseau(pc, P2, d, sg):
    """Âme opaque : bleu nuit au collet -> cyan pâle à la pointe, chevrons de taille, plume de givre lumineuse."""
    s = pc.s(P2)
    k1 = np.clip(s / 0.25, 0, 1)[..., None]
    k2 = np.clip((s - 0.25) / 0.75, 0, 1)[..., None]
    col = lerp(lerp(G_DEEP, G_BODY, k1), G_PALE, k2 * 0.55)
    hw = np.maximum(hw_fer(P2[..., 0]), 0.05)
    f = np.clip(np.abs(P2[..., 1]) / hw, 0, 1)
    col = col * (0.95 - 0.22 * f)[..., None] * (1 + 0.07 * chevrons(pc, P2))[..., None]
    db = d_veines(P2, pc.centre)
    em = np.zeros(col.shape, np.float32)
    cw = 0.17 * (1 - 0.4 * s)
    halo = db < cw + 0.12
    col[halo] = lerp(col[halo], C(150, 226, 250), 0.55)
    coeur = db < cw
    col[coeur] = lerp(C(205, 248, 255), C(120, 214, 246), np.clip(db[coeur] / cw[coeur], 0, 1)[..., None])
    em[coeur] = LUEUR
    col[d < D_OFF + 0.08] = G_DEEP * 0.8
    return col, None, em


def ame_fil(pc, P2, d, sg):
    return np.zeros(P2.shape[:-1] + (3,), np.float32) + G_LIGHT, None, None


ame_plat = ame_biseau


# ------------------------------------------------------------------ cubes différés
TILES = {}
TRANS_TILES = set()
CUBES = []
SIX = ("north", "south", "east", "west", "up", "down")


def tuile(nom, rgba, e=None, trans=False):
    assert nom not in TILES, nom
    TILES[nom] = (rgba, e)
    if trans:
        TRANS_TILES.add(nom)
    return nom


def finir(col, al, em, masque):
    rgba = np.zeros(col.shape[:2] + (4,), np.uint8)
    rgba[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    rgba[..., 3] = (np.clip(al, 1, 254).astype(np.uint8) if al is not None else 255) * masque
    rgba[~masque] = 0
    e = None
    if em is not None:
        on = masque & (em.max(axis=-1) > 0)
        if on.any():
            e = np.zeros_like(rgba)
            e[..., :3] = np.clip(em, 0, 225).astype(np.uint8)
            e[..., 3] = on * 255
            e[~on] = 0
    return rgba, e


def repere(X, Y):
    X = unit(X)
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    return X, Y, np.cross(X, Y)


def points_face(c, X, Y, Z, s, face, dens=DF):
    sx, sy, sz = s
    dims = {"south": (sx, sy), "north": (sx, sy), "down": (sx, sz), "up": (sx, sz), "east": (sz, sy), "west": (sz, sy)}[face]
    W, H = max(2, int(round(dims[0] * dens))), max(2, int(round(dims[1] * dens)))
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    U_, V_ = np.meshgrid(u, v)
    if face == "south":
        x, y, z = -sx / 2 + U_ * sx, sy / 2 - V_ * sy, np.full_like(U_, sz / 2)
    elif face == "north":
        x, y, z = sx / 2 - U_ * sx, sy / 2 - V_ * sy, np.full_like(U_, -sz / 2)
    elif face == "down":
        x, y, z = -sx / 2 + U_ * sx, np.full_like(U_, -sy / 2), sz / 2 - V_ * sz
    elif face == "up":
        x, y, z = -sx / 2 + U_ * sx, np.full_like(U_, sy / 2), -sz / 2 + V_ * sz
    elif face == "east":
        x, y, z = np.full_like(U_, sx / 2), sy / 2 - V_ * sy, sz / 2 - U_ * sz
    else:
        x, y, z = np.full_like(U_, -sx / 2), sy / 2 - V_ * sy, -sz / 2 + U_ * sz
    return c + x[..., None] * X + y[..., None] * Y + z[..., None] * Z


def spec(groupe, nom, c, X, Y, s, peintures, trans):
    X, Y, Z = repere(X, Y)
    c = np.asarray(c, float)
    faces = {}
    for f, fn in peintures.items():
        P = points_face(c, X, Y, Z, s, f)
        col, al, em, m = fn(P)
        if m.any():
            faces[f] = tuile(f"{nom}_{f}", *finir(col, al, em, m), trans=trans)
    if faces:
        CUBES.append({"groupe": groupe, "nom": nom, "c": Wp(*c), "R": np.column_stack([Wv(*X), Wv(*Y), Wv(*Z)]),
                      "half": np.asarray(s, float) / 2, "faces": faces})


def volume(pc, groupe, ame):
    """Peau (ame=False, trans_) ou âme opaque (ame=True, plans parallèles décalés de DELTA vers l'intérieur)."""
    pb, pf, pp = (ame_biseau, ame_fil, ame_plat) if ame else (peau_biseau, peau_fil, peau_plat)
    d0 = D_OFF if ame else 0.0
    z0 = ZC_MIN if ame else Z_E
    ex = D_EXTRA if ame else 0.0
    for idx, (p, q, v0, v1) in enumerate(pc.segs):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        pm = (p + q) / 2
        cand = np.array([pm + n * 0.25, pm - n * 0.25])
        prof = np.where(in_poly(cand, pc.poly), d_poly(cand, list(pc.poly) + [pc.poly[0]]), -1.0)
        if prof[1] > prof[0]:
            n = -n
        wmax = float(max(pc.wb(p[None])[0], pc.wb(q[None])[0]))
        rentrant = lambda v: bool(in_poly((v)[None], pc.poly)[0])      # sommet rentrant : prolongement du fil dans le fer
        e0 = (wmax * 1.6 if rentrant(p - d * 0.25) else 0.15) if v0 else 0.04
        e1 = (wmax * 1.6 if rentrant(q + d * 0.25) else 0.15) if v1 else 0.04
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        sy = (wmax + ex - d0 + 0.1) / math.cos(AL)
        if sy < 0.08:
            continue
        for sg in (1, -1):
            Y = np.array((n[0] * math.cos(AL), n[1] * math.cos(AL), sg * math.sin(AL)))
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0] + n[0] * d0, mid[1] + n[1] * d0, sg * z0)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(P, idx=idx, sg=sg):
                P2 = P[..., :2]
                D = d_stack(P2, pc.segs)
                de = D.min(0)
                own = (D[idx] <= de + RECOUV_AME) if ame else proprietaire(D, idx, P2, pc.segs)
                m = in_poly(P2, pc.poly) & own & (de < pc.wb(P2) + ex + 0.03) & (de >= d0 - 0.02)
                if ame:
                    m &= pc.ame_ok(P2)
                col, al, em = pb(pc, P2, de, sg)
                return col, al, em, m

            def fil(P, idx=idx, n=n, sg=sg):
                P2 = P[..., :2] + n * (0.04 + d0)
                D = d_stack(P2, pc.segs)
                own = D[idx] <= D.min(0) + RECOUV_AME          # fil presque opaque : recouvrement permis (pas de coin ouvert)
                m = in_poly(P2, pc.poly) & own
                if ame:
                    m &= pc.ame_ok(P2)
                col, al, em = pf(pc, P2, D.min(0), sg)
                return col, al, em, m

            spec(groupe, f"{pc.nom}_{'ame' if ame else 'peau'}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH),
                 {"south": haut, "down": fil}, trans=not ame)
    u = pc.u
    pp_ = np.array((-u[1], u[0]))
    pa = np.array(pc.poly) - O_
    s_, t_ = pa @ u, pa @ pp_
    s0, s1, t0, t1 = s_.min() - 0.05, s_.max() + 0.05, t_.min() - 0.05, t_.max() + 0.05
    Pc = O_ + u * (s0 + s1) / 2 + pp_ * (t0 + t1) / 2
    dz = DELTA if ame else 0.0
    for sg in (1, -1):
        X = unit(np.array((u[0], u[1], sg * pc.k)))
        Y = sg * np.array((pp_[0], pp_[1], 0.0))
        Z = np.cross(X, Y)
        c = np.array((Pc[0], Pc[1], sg * (float(pc.h(Pc)) - dz))) - Z * (TH / 2)

        def plat(P, sg=sg):
            P2 = P[..., :2]
            de = pc.dE(P2)
            m = in_poly(P2, pc.poly) & (de >= pc.wb(P2) + ex - 0.03) & (np.linalg.norm(P2 - O_, axis=-1) > R_COL - 0.6)
            if ame:
                m &= pc.ame_ok(P2)
            col, al, em = pp(pc, P2, de, sg)
            return col, al, em, m

        spec(groupe, f"{pc.nom}_{'ame' if ame else 'peau'}_plat{'pm'[sg < 0]}", c, X, Y,
             ((s1 - s0) * math.sqrt(1 + pc.k ** 2), t1 - t0, TH), {"south": plat}, trans=not ame)


# ------------------------------------------------------------------ tours (pièces rondes, comme skin_epee_givre)
OVL, OVW = 0.04, 0.03


def p_argent(xn, t, ex):
    k = np.clip(0.45 + 0.3 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + ex.get("pointe", 0.0) * t, 0, 1)
    col = lerp(ARG_D, ARG_L, (k ** 1.2)[..., None]) * (1 + 0.03 * np.sin(t * 37 + xn * 3))[..., None]
    col = np.where((np.abs(xn) > 0.86)[..., None], np.minimum(col * 1.14 + 10, 255), col)
    if ex.get("givre"):
        col = np.where(((t > 0.82) & (np.abs(xn) < 0.75))[..., None], lerp(col, BLANC, 0.6), col)
    return col, None


def p_glace(xn, t, ex):
    k = np.clip(0.35 + 0.35 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + 0.25 * t, 0, 1)
    col = lerp(C(40, 110, 176), G_LIGHT, (k ** 1.1)[..., None])
    col = np.where((np.abs(xn) > 0.84)[..., None], BLANC, col)
    em = np.zeros(col.shape, np.float32)
    if ex.get("e"):
        ln = np.abs(xn) < 0.16
        col[ln] = lerp(col[ln], C(200, 248, 255), 0.7)
        em[ln] = LUEUR
    return col, em


def p_gemme(xn, t, ex):
    k = np.clip(0.4 + 0.4 * (1 - np.abs(xn)) + 0.2 * t + ex.get("clair", 0.0), 0, 1)
    col = lerp(C(40, 130, 210), C(170, 236, 255), k[..., None])
    return col, np.clip(col * 0.8, 0, 200)


PEINTRES = {"argent": p_argent, "glace": p_glace, "gemme": p_gemme}


def tuile_pan(nom, mat, L, w0, w1, ex):
    if nom in TILES:
        return nom
    wm = max(w0, w1) + 2 * OVW
    Lf = L + 2 * OVL
    Wt, Ht = max(2, int(math.ceil(wm * DF))), max(2, int(math.ceil(Lf * DF)))
    yy, xx = np.mgrid[0:Ht, 0:Wt]
    x = ((xx + 0.5) / Wt - 0.5) * wm
    y = Lf * (1 - (yy + 0.5) / Ht) - OVL
    t = np.clip(y / max(L, 1e-6), 0, 1)
    hw = (w0 + (w1 - w0) * t) / 2 + OVW
    mask = np.abs(x) <= hw
    xn = np.clip(x / np.maximum(hw - OVW, 1e-3), -1, 1)
    col, em = PEINTRES[mat](xn, t, ex)
    return tuile(nom, *finir(col, None, em, mask))


def tour(g, nom, O, ax, ref, profil, n=8, phase=0.0, partage=None):
    """profil = [(b0, r0, b1, r1, [(mat, ex), ...]), ...] le long de ax (rayon = apothème)."""
    O, ax = np.asarray(O, float), unit(ax)
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    pref = partage or nom
    for i, (b0, r0, b1, r1, mats) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        tiles = [tuile_pan(f"{pref}{i}{'abcd'[j]}", m, L, 2 * r0 * tn, 2 * r1 * tn, ex) for j, (m, ex) in enumerate(mats)]
        db, dr = (b1 - b0) / L, (r1 - r0) / L
        wm = max(2 * r0 * tn, 2 * r1 * tn) + 2 * OVW
        for k in range(n):
            th = phase + TAU * k / n
            e = math.cos(th) * ref + math.sin(th) * w3
            Pa, Pb = O + b0 * ax + r0 * e, O + b1 * ax + r1 * e
            Y = unit(Pb - Pa)
            N = -dr * ax + db * e
            X = np.cross(Y, N)
            c = (Pa + Pb) / 2 - N * TH / 2
            CUBES.append({"groupe": g, "nom": f"{nom}{i}_{k}", "c": c, "R": np.column_stack([X, Y, N]),
                          "half": np.array((wm / 2, L / 2 + OVL, TH / 2)), "faces": {"south": tiles[k % len(tiles)]}})


def t_disque(nom, n, Ra, N=48):
    R = Ra / math.cos(math.pi / n)
    yy, xx = np.mgrid[0:N, 0:N]
    x = ((xx + 0.5) / N - 0.5) * 2 * R
    y = (0.5 - (yy + 0.5) / N) * 2 * R
    th = np.arctan2(y, x)
    sect = np.round(th / (TAU / n)) * (TAU / n)
    apo = x * np.cos(sect) + y * np.sin(sect)
    mask = apo <= Ra
    rr = apo / Ra
    col = lerp(ARG_L, ARG_M, rr[..., None] ** 1.5)
    col[(rr > 0.72) & (rr < 0.8)] = BLANC
    col[rr > 0.92] = ARG_D
    return tuile(nom, *finir(col, None, None, mask))


def disque(g, nom, c, Nrm, up, n, Ra, tile):
    Nrm = unit(Nrm)
    Y = unit(up - (up @ Nrm) * Nrm)
    X = np.cross(Y, Nrm)
    R = Ra / math.cos(math.pi / n)
    CUBES.append({"groupe": g, "nom": nom, "c": np.asarray(c, float) - Nrm * TH / 2, "R": np.column_stack([X, Y, Nrm]),
                  "half": np.array((R, R, TH / 2)), "faces": {"south": tile}})


def t_unie(nom, W, H, c0, c1, ligne=None):
    yy, xx = np.mgrid[0:H, 0:W]
    q = (yy + 0.5) / H
    col = lerp(c0, c1, q[..., None]) * (1 + 0.04 * np.sin(xx * 0.7))[..., None]
    if ligne is not None:
        col[int(H * 0.4):int(H * 0.4) + 2] = ligne
    return tuile(nom, *finir(col, None, None, np.ones((H, W), bool)))


def t_cuir(W=128, H=16):
    """Cuir bleu nuit enroulé en biais, couture d'argent (fusée de l'épée)."""
    r = np.random.default_rng(5)
    yy, xx = np.mgrid[0:H, 0:W]
    f = ((xx + yy * 0.9) / 14.0) % 1.0
    c = lerp(C(44, 56, 104), C(16, 20, 44), f[..., None])
    c = np.where((f > 0.86)[..., None], C(8, 10, 24), c)
    c *= r.uniform(0.95, 1.05, (H, W))[..., None]
    for x in range(3, W - 4, 10):
        c[6:10, x:x + 5] = (176, 196, 220)
    return tuile("cuir", *finir(c, None, None, np.ones((H, W), bool)))


def t_sangle(W=64, H=8):
    yy, xx = np.mgrid[0:H, 0:W]
    c = lerp(C(74, 92, 150), C(32, 40, 82), ((yy + 0.5) / H)[..., None]) + np.zeros((H, W, 3), np.float32)
    c[0] = c[-1] = (120, 140, 190)
    c[:, ::8] *= 0.8
    return tuile("sangle", *finir(c, None, None, np.ones((H, W), bool)))


def t_etoile(nom, N=48):
    """Scintillement additif : étoile à quatre branches, noir = invisible."""
    yy, xx = np.mgrid[0:N, 0:N]
    x = ((xx + 0.5) / N - 0.5) * 2
    y = ((yy + 0.5) / N - 0.5) * 2
    r = np.hypot(x, y)
    br = np.maximum(np.exp(-np.abs(x) * 14) * (1 - np.abs(y)), np.exp(-np.abs(y) * 14) * (1 - np.abs(x)))
    k = np.clip(br * 1.2 + np.exp(-r * 6) * 0.9, 0, 1)
    col = lerp(C(0, 0, 0), C(200, 240, 255), k[..., None] ** 0.8)
    return tuile(nom, *finir(col, None, None, np.ones((N, N), bool)))


def barre(g, nom, p, q, r, Rang, faces):
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = T_ if abs(X @ T_) < 0.9 else A_
    Y0 = unit(ref - (ref @ X) * X)
    Z0 = np.cross(X, Y0)
    a = math.radians(Rang)
    Y = math.cos(a) * Y0 + math.sin(a) * Z0
    CUBES.append({"groupe": g, "nom": nom, "c": (p + q) / 2, "R": np.column_stack([X, Y, np.cross(X, Y)]),
                  "half": np.array((np.linalg.norm(q - p) / 2, r, r)), "faces": faces})


def bar8(g, nom, p, q, r, tile, ov=0.0):
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X = unit(q - p)
    Y0 = unit(W_ - (W_ @ X) * X)
    Z0 = np.cross(X, Y0)
    a_ = r * math.tan(math.pi / 8) * 1.02
    for k in range(4):
        gk = math.pi / 4 * k
        Yk = math.cos(gk) * Y0 + math.sin(gk) * Z0
        d = 0.03 * k
        Lk = L + 2 * ov - 2 * d
        CUBES.append({"groupe": g, "nom": nom + "abcd"[k], "c": (p + q) / 2, "R": np.column_stack([X, Yk, np.cross(X, Yk)]),
                      "half": np.array((Lk / 2, r, a_)), "faces": {"south": tile, "north": tile, "up": tile, "down": tile}})


def plaque_add(g, nom, c, X, Y, taille, tile):
    """Plaque additive vue des deux côtés (scintillement)."""
    X, Y = unit(X), unit(Y)
    CUBES.append({"groupe": g, "nom": nom, "c": np.asarray(c, float), "R": np.column_stack([X, Y, np.cross(X, Y)]),
                  "half": np.array((taille / 2, taille / 2, 0.15)), "faces": {"south": tile, "north": tile}})


# ------------------------------------------------------------------ conception
GROUPES = []        # (nom, pivot, parent)


def grp(nom, pivot, parent):
    GROUPES.append((nom, np.asarray(pivot, float), parent))
    return nom


def bague(b0, b1, ra, ro, rb, c=0.12, mat="argent"):
    return [(b0, ra, b0 + c, ro, [(mat, {"clair": 0.15})]), (b0 + c, ro, b1 - c, ro, [(mat, {}), (mat, {"clair": -0.08})]),
            (b1 - c, ro, b1, rb, [(mat, {"clair": -0.12})])]


GLACE_ALT = [("glace", {"clair": 0.12, "e": True}), ("glace", {"clair": -0.1})]
GLACE_MAT = [("glace", {"clair": 0.05}), ("glace", {"clair": -0.12})]
# oreilles de cristal nées du collet (les ailettes d'une lance à ailes) : (angle depuis +a vers +b (deg), longueur, rayon)
OREILLES = [(64, 2.0, 0.38), (-64, 2.0, 0.38), (112, 1.15, 0.27), (-112, 1.15, 0.27)]
A_CH = 17.0                  # collier de givre de la charge (item_use)
A_PT = 19.9                  # pivot des effets de la pointe, caché dans la glace
OUT = {}


def conception():
    racine = grp(objet.etape("repos", "lance"), Wp(0), None)
    lance = grp("lance", Wp(0), racine)
    # --- hampe : pique de cristal, virole, hampe d'argent, fusée de cuir cloutée entre deux viroles, hampe, douille conique
    manche = grp("manche", Wp(0), lance)
    t_cuir()
    hampe_t = t_unie("hampe", 48, 12, ARG_M, ARG_D, ligne=ARG_L)
    bar8(manche, "fusee", Wp(-2.5), Wp(2.5), 0.58, "cuir")
    tour(manche, "virole_bas", Wp(0), A_, W_, bague(-3.15, -2.4, 0.50, 0.72, 0.62), n=8, phase=math.pi / 8)
    tour(manche, "virole_haut", Wp(0), A_, W_, bague(2.4, 3.15, 0.62, 0.72, 0.50), n=8, phase=math.pi / 8)
    bar8(manche, "hampe_bas", Wp(-9.0), Wp(-3.0), 0.47, hampe_t)
    bar8(manche, "hampe_haut", Wp(3.0), Wp(11.2), 0.47, hampe_t)
    tour(manche, "bague_bas", Wp(0), A_, W_, bague(-6.4, -5.9, 0.47, 0.6, 0.47), n=8, phase=math.pi / 8)
    tour(manche, "bague_haut", Wp(0), A_, W_, bague(6.8, 7.3, 0.47, 0.6, 0.47), n=8, phase=math.pi / 8)
    tour(manche, "talon", Wp(0), A_, W_, bague(-9.6, -8.9, 0.42, 0.64, 0.52), n=8, phase=math.pi / 8)
    pique = grp("pique", Wp(-9.6), manche)
    tour(pique, "pique", Wp(-9.55), -A_, W_, [(0.0, 0.46, 0.14, 0.54, GLACE_ALT), (0.14, 0.54, 0.75, 0.54, GLACE_ALT),
                                             (0.75, 0.54, -A_MIN - 9.55, 0.0, GLACE_ALT)], n=6)
    # --- tête : douille conique d'argent, collet octogonal (axe z) à flocons en relief et gemmes
    tete = grp("tete", Wp(A_O), lance)
    tour(tete, "douille", Wp(0), A_, W_, [(11.0, 0.50, 11.15, 0.60, [("argent", {"clair": 0.15})]),
                                          (11.15, 0.60, 11.95, 0.84, [("argent", {}), ("argent", {"clair": -0.08})]),
                                          (11.95, 0.84, 12.1, 0.78, [("argent", {"clair": -0.12})])], n=8, phase=math.pi / 8)
    tour(tete, "collet", Wp(A_O), T_, A_, bague(-Z_COL, Z_COL, R_COL - 0.18, R_COL, R_COL - 0.18, c=0.16), n=8, phase=math.pi / 8)
    td = t_disque("disque_collet", 8, R_COL - 0.18)
    bras_t = t_unie("bras", 32, 8, ARG_L, ARG_M, ligne=BLANC)
    cap_t = t_unie("bras_bout", 8, 8, BLANC, ARG_M)
    fb = {f: bras_t for f in ("south", "north", "up", "down")}
    fb.update(east=cap_t, west=cap_t)
    for s in (1, -1):
        cs = "e" if s > 0 else "i"
        fl = grp(f"flocon_{cs}", Wp(A_O, 0, s * Z_COL), tete)
        disque(fl, f"couvercle_{cs}", Wp(A_O, 0, s * Z_COL), T_ * s, A_, 8, R_COL - 0.18, td)
        zc = s * (Z_COL + 0.04)
        Rf = 0.98
        for k in range(3):
            th = math.radians(90 + 60 * k)
            e = math.cos(th) * A_ + math.sin(th) * W_
            barre(fl, f"bras_{cs}{k}", Wp(A_O, 0, zc) - e * Rf, Wp(A_O, 0, zc) + e * Rf, 0.11, 45, fb)
        for k in range(6):
            th = math.radians(90 + 60 * k)
            e = math.cos(th) * A_ + math.sin(th) * W_
            for fr, ln in ((0.55, 0.30), (0.82, 0.2)):
                base = Wp(A_O, 0, zc + s * 0.01) + e * Rf * fr
                for sg in (-1, 1):
                    t2 = th + sg * math.radians(55)
                    e2 = math.cos(t2) * A_ + math.sin(t2) * W_
                    barre(fl, f"branche_{cs}{k}{'pm'[sg < 0]}{int(fr * 10)}", base - e2 * 0.05, base + e2 * ln, 0.07, 45, fb)
        tour(fl, f"gemme_{cs}", Wp(A_O, 0, s * Z_COL), T_ * s, A_,
             [(0.0, 0.32, 0.18, 0.32, [("gemme", {"clair": 0.1}), ("gemme", {"clair": -0.1})]),
              (0.18, 0.32, 0.42, 0.0, [("gemme", {"clair": 0.2}), ("gemme", {})])], n=6, partage="gemme")
    # oreilles de cristal (lance à ailes : elles arrêtent la proie sur la hampe)
    OUT["oreilles"] = []
    for i, (ang, L, r) in enumerate(OREILLES):
        th = math.radians(ang)
        d = unit(A_ * math.cos(th) + W_ * math.sin(th))
        base = Wp(A_O) + d * (R_COL - 0.4)
        cg = grp(f"oreille_{i + 1}", base, tete)
        tl_ = min(L * 0.45, r * 1.9)
        tour(cg, cg, base, d, T_, [(0.0, r * 0.8, 0.2, r, GLACE_ALT), (0.2, r, L - tl_, r, GLACE_ALT),
                                    (L - tl_, r, L, 0.0, GLACE_ALT)], n=6, phase=math.pi / 6)
        OUT["oreilles"].append((cg, base, d, L))
    # --- fer : peau de glace trans_ + âme opaque ; pivot au collet (il pousse depuis le collet)
    g = grp("fer", Wp(A_O), tete)
    volume(B_FER, grp("ame_fer", Wp(A_O), g), True)
    volume(B_FER, grp("trans_fer", Wp(A_O), g), False)
    # --- effets repliés à 1/10 sur des pivots cachés dans la glace (un dépliage par animation)
    et = t_etoile("etoile")
    ptw = Wp(A_PT)
    cg, base, d, L = OUT["oreilles"][0]
    orw = base + d * (L * 0.45)
    for nm, c, taille in (("add_scint_pointe", ptw, 2.2), ("add_scint_oreille", orw, 1.6), ("add_coup", ptw, 3.2),
                          ("add_scint_charge", ptw, 2.6)):
        g = grp(nm, c, tete)
        plaque_add(g, f"{nm}_a", c, A_, W_, taille, et)
        plaque_add(g, f"{nm}_b", c, A_, T_, taille * 0.8, et)
        OUT[nm] = g
    # aiguilles de givre (event_hit) : six cristaux fins en gerbe vers l'avant, nés de la pointe
    OUT["aiguilles"] = grp("aiguilles", ptw, tete)
    for j in range(6):
        ph = math.radians(30 + 60 * j)
        th = math.radians(24 if j % 2 == 0 else 38)
        d = unit(A_ * math.cos(th) + (W_ * math.cos(ph) + T_ * math.sin(ph)) * math.sin(th))
        L = 2.3 if j % 2 == 0 else 1.7
        tour(OUT["aiguilles"], f"aiguille{j}", ptw + A_ * 0.6 + d * 0.05, d, W_ * math.sin(ph) - T_ * math.cos(ph),
             [(0.0, 0.10, L * 0.6, 0.15, GLACE_MAT), (L * 0.6, 0.15, L, 0.0, GLACE_MAT)], n=6, partage=f"aig{j % 2}")
    # collier de givre de la charge (item_use) : huit épines qui poussent autour du fer, couchées vers la hampe
    chw = Wp(A_CH)
    OUT["charge"] = grp("charge", chw, tete)                         # enveloppe : grandit à event_use_start
    OUT["givre_charge"] = grp("givre_charge", chw, OUT["charge"])   # replié, déplié par item_use
    for j in range(8):
        ph = math.radians(22.5 + 45 * j)
        rad = W_ * math.cos(ph) + T_ * math.sin(ph)
        d = unit(rad * math.cos(math.radians(38)) - A_ * math.sin(math.radians(38)))
        L = 1.5 if j % 2 == 0 else 1.1
        tour(OUT["givre_charge"], f"epine{j}", chw + rad * 0.3 + d * 0.05, d, W_ * math.sin(ph) - T_ * math.cos(ph),
             [(0.0, 0.11, L * 0.55, 0.16, GLACE_MAT), (L * 0.55, 0.16, L, 0.0, GLACE_MAT)], n=6, partage=f"epi{j % 2}")
    OUT["tipw"], OUT["tdw"] = Wp(A_PT + 0.4), A_
    OUT["racine"], OUT["lance"], OUT["tete"], OUT["pique"] = racine, lance, tete, pique
    return racine


RACINE = conception()

# ------------------------------------------------------------------ repli (repère fixe : pas de recentrage, Display validé)
def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


REPLIES = [OUT[k] for k in ("add_scint_pointe", "add_scint_oreille", "add_coup", "add_scint_charge", "aiguilles", "givre_charge")]
_piv = {n: p for n, p, _ in GROUPES}
for cb in CUBES:
    if cb["groupe"] in REPLIES:
        o = _piv[cb["groupe"]]
        cb["c"] = o + FOLD * (cb["c"] - o)
        cb["half"] = cb["half"] * FOLD

UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, (im, ime) in sorted(TILES.items(), key=lambda it: (-it[1][0].shape[0], -it[1][0].shape[1])):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, f"atlas plein ({n}, y = {y})"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None:
            tex_e[y:y + h, x:x + w] = ime
        x += w + 1
        shelf = max(shelf, h)
    assert tex[TEX - 2, TEX - 2, 3] == 0
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    zone = np.zeros(semi.shape, bool)
    for n in TRANS_TILES:
        u0, v0, u1, v1 = UV[n]
        zone[v0:v1, u0:u1] = True
    assert not (semi & ~zone).any(), "semi-transparence hors des tuiles trans_"
    assert set(np.unique(tex_e[..., 3])) <= {0, 255}
    print(f"atlas : {len(TILES)} tuiles, rangées jusqu'à y = {y + shelf}")
    res = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        res.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return res


tex_b64, tex_e_b64 = atlas()


def euler(R):
    """Angles (X, Y, Z) tels que R = Rz Ry Rx ; blocage de cardan (Y = ±90°) : tout l'angle sur X (piège noté)."""
    if abs(R[2, 0]) < 0.99999:
        e = (math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(math.asin(-R[2, 0])), math.degrees(math.atan2(R[1, 0], R[0, 0])))
    elif R[2, 0] < 0:
        e = (math.degrees(math.atan2(R[0, 1], R[0, 2])), 90.0, 0.0)
    else:
        e = (math.degrees(math.atan2(-R[0, 1], -R[0, 2])), -90.0, 0.0)
    assert np.allclose(rotm(*e), R, atol=1e-5), "euler"
    return e


def nuid():
    return str(_uuid.uuid4())


elements, groups = [], {}
for nom, piv, parent in GROUPES:
    assert nom not in groups and len(nom) <= 64, nom
    groups[nom] = {"origin": [round(float(v), 4) for v in piv], "uuid": nuid(), "ids": [], "parent": parent, "rotation": [0, 0, 0]}
# émetteur de flocons au milieu du fil : +Y du groupe le long de la normale sortante (rotation autour de Z seulement, plan de l'image)
_rz = math.degrees(math.atan2(-OUT["tdw"][0], OUT["tdw"][1]))
groups["emit_mc_snowflake"] = {"origin": [round(float(v), 4) for v in OUT["tipw"]], "uuid": nuid(), "ids": [], "parent": OUT["tete"],
                               "rotation": [0, 0, round(_rz, 2)]}
groups["ctrl_emit"] = {"origin": [round(float(v), 4) for v in OUT["tipw"]], "uuid": nuid(), "ids": [], "parent": "emit_mc_snowflake",
                       "rotation": [0, 0, 0]}
for cb in CUBES:
    c, h = cb["c"], cb["half"]
    R = cb["R"]
    assert abs(np.linalg.det(R) - 1) < 1e-6, cb["nom"]
    rot = euler(R)
    e = {"name": cb["nom"], "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in c - h],
         "to": [round(float(v), 4) for v in c + h], "origin": [round(float(v), 4) for v in c], "box_uv": False,
         "faces": {f: {"uv": list(UV[cb["faces"][f]]) if f in cb["faces"] else CLEAR, "texture": 0} for f in SIX}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[cb["groupe"]]["ids"].append(e["uuid"])


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node(RACINE)]

# ------------------------------------------------------------------ animations (objet vivant, guide 14)
def s_(v):
    return v if isinstance(v, str) else f"{v + 0.0:.4f}".rstrip("0").rstrip(".")


def kf(ch, t, x, y=None, z=None, interp="linear"):
    y = x if y is None else y
    z = x if z is None else z
    return {"channel": ch, "data_points": [{"x": s_(x), "y": s_(y), "z": s_(z)}], "time": round(t, 4), "interpolation": interp}


def anim(name, length, loop="once"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 20,
            "selected": name == "item_idle", "animators": {}}


def piste(an, g, keys):
    an["animators"][groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": keys}


def echant(L, n):
    return [round(L * i / n, 4) for i in range(n + 1)]


DEPLIE = 1 / FOLD


def pop(t0, dur, L, pic=1.0):
    """Échelle (repliée = 1) : s'ouvre à DEPLIE·pic en 30 % de dur puis se referme ; clés à 20 images/s."""
    keys = [kf("scale", 0.0, 1.0)]
    if t0 > 0:
        keys.append(kf("scale", t0, 1.0))
    for k in range(1, 9):
        u = k / 8
        v = 1 + (DEPLIE * pic - 1) * (math.sin(math.pi * min(1, u / 0.3) / 2) if u <= 0.3 else (1 - sm(u, 0.3, 1.0)))
        keys.append(kf("scale", t0 + dur * u, v))
    keys.append(kf("scale", L, 1.0))
    return keys


def pousse(t0, dur, over=1.07):
    keys = [kf("scale", 0.0, 0.05)]
    if t0 > 0:
        keys.append(kf("scale", t0, 0.05))
    for k in range(1, 11):
        u = k / 10
        v = 0.05 + (over - 0.05) * (1 - (1 - u / 0.7) ** 2) if u <= 0.7 else lerp(over, 1.0, (u - 0.7) / 0.3)
        keys.append(kf("scale", t0 + dur * u, v))
    return keys


def emit(an, keys):
    an["animators"][groups["ctrl_emit"]["uuid"]] = {"name": "ctrl_emit", "type": "bone", "keyframes": keys}



# item_idle (8 s) : un scintillement à la pointe, puis à l'oreille de cristal ; émetteur coupé.
idle = anim("item_idle", 8.0, "loop")
piste(idle, OUT["add_scint_pointe"], pop(2.4, 0.5, 8.0))
piste(idle, OUT["add_scint_oreille"], pop(5.8, 0.45, 8.0, 0.9))
emit(idle, [kf("position", 0, -1, 0, 0), kf("position", 8.0, -1, 0, 0)])

# item_gui : rien ne bouge, émetteur coupé.
gui = anim("item_gui", 4.0, "loop")
emit(gui, [kf("position", 0, -1, 0, 0), kf("position", 4.0, -1, 0, 0)])

# item_use (lance levée pour la charge, 1,6 s en boucle) : le collier de givre est sorti et respire, la pointe scintille,
# quelques flocons tombent de la pointe (cadence du staff, ctrl_emit 0).
L_USE = 1.6
use = anim("item_use", L_USE, "loop")
piste(use, OUT["givre_charge"], [kf("scale", t, DEPLIE * (1 + 0.06 * math.sin(TAU * t / L_USE))) for t in echant(L_USE, 12)])
piste(use, OUT["add_scint_charge"], pop(0.5, 0.6, L_USE, 0.9))
emit(use, [kf("position", 0, 0, 0, 0), kf("position", L_USE, 0, 0, 0)])

# event_use_start (0,4 s) : le givre gagne le fer (le collier pousse depuis le cœur du fer, en léger dépassement).
L_US = 0.4
ustart = anim("event_use_start", L_US)
piste(ustart, OUT["charge"], pousse(0.0, 0.36, 1.1))

# event_select (0,6 s) : la glace pousse depuis le collet (fer), puis les oreilles en cascade et la pique du talon.
L_SEL = 0.6
sel = anim("event_select", L_SEL)
piste(sel, "fer", pousse(0.0, 0.32))
for i, (cg, *_r) in enumerate(OUT["oreilles"]):
    piste(sel, cg, pousse(0.18 + 0.05 * i, 0.22, 1.12))
piste(sel, OUT["pique"], pousse(0.1, 0.3))

# event_swing (0,3 s) : coup d'estoc, éclat blanc à la pointe au moment de l'impact.
L_SW = 0.3
sw = anim("event_swing", L_SW)
piste(sw, OUT["add_coup"], pop(0.06, 0.2, L_SW))

# event_hit (0,5 s) : le givre jaillit de la pointe (six aiguilles en gerbe qui sortent puis rentrent) + frisson + gerbe de
# flocons (ctrl_emit +8 : s'ajoute au -1 de l'état) ; le seul son.
L_HIT = 0.5
hit = anim("event_hit", L_HIT)
ks = [kf("scale", 0.0, 1.0)]
for t in echant(L_HIT, 20)[1:]:
    v = 1 + (DEPLIE * 1.05 - 1) * sm(t, 0.0, 0.06) * (1 - sm(t, 0.22, 0.42))
    ks.append(kf("scale", t, v))
piste(hit, OUT["aiguilles"], ks)
piste(hit, OUT["lance"], [kf("rotation", t, 0, 0, 1.0 * math.sin(TAU * t / 0.08) * (1 - sm(t, 0.0, 0.26))) for t in echant(0.28, 14)]
      + [kf("rotation", L_HIT, 0, 0, 0)])
emit(hit, [kf("position", 0, 8, 0, 0), kf("position", 0.22, 8, 0, 0), kf("position", 0.23, 0, 0, 0), kf("position", L_HIT, 0, 0, 0)])

ANIMS = [idle, gui, use, ustart, sel, sw, hit]


# ------------------------------------------------------------------ réglages Display (ceux de skin_lance_orage, validés en jeu)
def display_vanilla(rot_v, trans_v, ech_v, longueur_v, incl_x=0.0):
    """Display de la lance de Minecraft (image plate, pointe en haut à gauche de l'image de 32 × 32 : axe (-1, 1) du modèle,
    longueur longueur_v px du modèle) recalculé pour cet objet (axe +Y, longueur A_MAX - A_MIN, prise en P0)."""
    Rv = objet._rxyz((incl_x, 0, 0))[:3, :3] @ objet._rxyz(rot_v)[:3, :3] @ rotm(0, 0, 45)
    ex, ey, ez = euler(Rv.T)
    rot = [round(-ex, 2) + 0.0, round(-ey, 2) + 0.0, round(-ez, 2) + 0.0]
    assert np.allclose(objet._rxyz(rot)[:3, :3], Rv, atol=1e-3)
    k = ech_v * longueur_v / (A_MAX - A_MIN)
    prise = np.array((0, P0[1] - 8, 0))
    tr = np.asarray(trans_v, float) - objet._rxyz(rot)[:3, :3] @ (k * prise)
    return {"rotation": rot, "translation": [round(float(v), 2) for v in tr], "scale": [round(k, 3)] * 3}


LV = 30 * math.sqrt(2) / 2
GUI = float(os.environ.get("GUI", "0.6"))
AFFICHAGE = objet.affichage(
    "lance",
    thirdperson_righthand=display_vanilla((5, 270, -40), (0, 2, 2), 1.7, LV),
    firstperson_righthand=display_vanilla((-20, 90, -35), (3.13, 2.0, 0.13), 1.36, LV, incl_x=-25),
    gui={"rotation": [0, 0, -45], "translation": [0, 0, 0], "scale": [GUI] * 3},
)
for c_ in ("thirdperson", "firstperson"):
    d_ = AFFICHAGE[f"{c_}_righthand"]
    AFFICHAGE[f"{c_}_lefthand"] = {"rotation": [d_["rotation"][0], -d_["rotation"][1], -d_["rotation"][2]],
                                   "translation": [-d_["translation"][0], d_["translation"][1], d_["translation"][2]], "scale": list(d_["scale"])}

# ------------------------------------------------------------------ écriture
assert 150 <= len(elements) <= 3000, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = objet.modele(NOM, "lance", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son
limiter_sons(model)
# Un seul son, au coup qui touche (event_hit) : tools/sons.py ne connaît pas encore les événements d'objet, on le pose après.
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "block.amethyst_block.chime")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def coins():
    P = []
    for e in elements:
        f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
        R = rotm(*e.get("rotation", (0, 0, 0)))
        for i in range(8):
            c = np.array([(f, t)[(i >> k) & 1][k] for k in range(3)])
            P.append(R @ (c - o) + o)
    return np.array(P)


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


P = coins()
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur {float(P[:, 1].max() - P[:, 1].min()):.1f} px ; boîte {P.min(0).round(2)} .. {P.max(0).round(2)}")
print(f"âme : bord à {D_OFF:.3f} px du fil ; fer {L_FER:.2f} px, épaisseur à l'épaule {2 * float(B_FER.h(np.array([[15.0, 0]]))[0]):.2f} px")
print("Display :", json.dumps({k: AFFICHAGE[k] for k in ("thirdperson_righthand", "firstperson_righthand", "gui")}))

