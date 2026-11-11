"""Gueule de l'Abysse : skin d'objet (guide 14) pour toutes les masses du joueur, ensemble Abyssal (thème Démoniaque).
Design original. Écrit skin_masse_abyssal.png, skin_masse_abyssal_e.png et .build/skin_masse_abyssal_brut.bbmodel.
Point de départ : gen_skin_lance_abyssal.py (classe Fer opaque du set devenue `Ailette`, tours, griffes, peintures) ;
repère, prise et Display (_MASSE, gui recentré) de skin_masse_givre / skin_masse_orage.

Référence réelle (.claude/references/objets/marteaux-masses.md) : la **masse à ailettes** (6 à 8 ailettes à bord concave
autour d'un noyau, étoile vue de dessus). Ici six **crocs d'os** en ailettes autour d'un nœud d'os : chaque ailette est une
plaque biseautée fermée en croc (bord extérieur convexe qui monte jusqu'à une pointe recourbée vers le haut, bord intérieur
creusé), vue de dessus la couronne se lit comme une gueule ronde de lamproie. Distinct des autres pièces du set (sabre, crocs
de pioche, fers en travers, dard, os d'aile, échine, fourche, écu).
- ailettes = vrai volume (recette .claude/references/objets/volume-3d.md) : plat incliné 1,30 -> 0,50 px (amincies vers la
  pointe), pente unique 40°, tous les bords biseautés sauf la racine (cachée dans le nœud) ; **vert seulement au fil** (fil
  vif + _e, bande verte, halo sombre, veines qui montent du fil), os nu à liseré violacé près du nœud ; **gouttière
  creusée** le long de chaque croc (filet vert + _e couché au fond) ; les six ailettes partagent les mêmes tuiles ;
- nœud d'os en tour à 12 pans (renflé), bagues d'os violacées, six clous d'os pâle entre les crocs, collet évasé, croc
  conique au sommet (pointe verte), hampe d'os à 12 pans baguée, poignée de cuir pourpre-noir en spirale à clous d'os pâle,
  griffe au talon.
Pas de métal, d'or ni de rouge. Une étape (`repos`). Repère : comme l'image vanilla de la masse, tête en haut à droite vue
de +Z (a le long du manche, b en travers dans le plan de l'image, z vers le spectateur), prise a = 3,5 sur le poing de
skin_masse_givre. Display : préréglage _MASSE de tools/objet.py, gui recentré.

Objet vivant (guide 14), sobre :
- item_idle (6 s) : les crocs respirent à contretemps (±2°), le fil souffle (ctrl_lumiere ±0,35) ;
- event_select (0,7 s) : la couronne de crocs sort du nœud (échelle de `crocs` : seul dépliage par scale), le fil s'allume ;
- event_swing (0,35 s) : la gueule se referme un peu sur le coup (crocs −5°), le fil s'avive ;
- event_hit (0,6 s) : la gueule s'ouvre d'un coup (+7°) puis frissonne, éclat du fil (+1,6), la tête tressaille ;
  **le seul son** (block.sculk.break à 0,04 s) ; aucun son ailleurs.
Pas de particules, pas d'item_gui (repli item_idle). Fonctions avancées : calque _e (fils, veines, gouttières, pointes),
ctrl_lumiere (non simulé par le renderer), scale animé, animations d'objet (non simulées par l'aperçu). À juger en jeu :
la couronne dans la case et en 1re personne, event_hit et son son, ctrl_lumiere sur un objet.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

NOM = "skin_masse_abyssal"
TEX = 512
TAU = 2 * math.pi
AVEC_E = True
GUI = float(os.environ.get("GUI", "0.76"))


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def lerp(a, b, k):
    return a + (b - a) * k


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def smv(t, a, b):
    u = np.clip((np.asarray(t, float) - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


# ------------------------------------------------------------------ repère (celui de skin_masse_givre / skin_masse_orage)
A_ = unit((1, 1, 0))            # a : le long du manche, vers la tête (haut à droite vue de +Z)
W_ = unit((-1, 1, 0))           # b : en travers, dans le plan de l'image
T_ = np.array((0.0, 0.0, 1.0))  # z : vers le spectateur
A_PRISE = 3.5
POING = np.array((3.66, 3.74, 8.0))
G0 = POING - A_PRISE * A_


def Wp(a, b=0.0, z=0.0):
    return G0 + A_ * a + W_ * b + T_ * z


def Wv(a, b=0.0, z=0.0):
    return A_ * a + W_ * b + T_ * z


# repère courant des volumes (une ailette = plan (a, rayon e_j), épaisseur selon n_j = A_ × e_j)
FR = [A_, W_, T_]


def Lp(a, b=0.0, z=0.0):
    return G0 + FR[0] * a + FR[1] * b + FR[2] * z


def Lv(a, b=0.0, z=0.0):
    return FR[0] * a + FR[1] * b + FR[2] * z


C = lambda *c: np.array(c, np.float32)
# palette Abyssal (sets-objets-2026-11-08.md, skin_epee_abyssal)
OS_CLAIR = C(58, 50, 72)
OS_BASE = C(30, 25, 40)
OS_SOMBRE = C(14, 10, 20)
ARETE = C(126, 92, 170)
REFLET = C(98, 68, 126)
AURA = C(22, 66, 40)
VEIN = C(96, 200, 44)
VCORE = C(150, 244, 70)
FIL = C(190, 255, 96)
E_COL = C(82, 211, 53)
E_VEINE = C(60, 160, 40)


# ------------------------------------------------------------------ outils 2D
def catmull(pts, n=10):
    pts = [np.array(p, float) for p in pts]
    P = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return np.array(out)


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


def normale_dedans(poly, p, d):
    n = np.array((-d[1], d[0]))
    return n if in_poly(np.array([p + n * 0.12]), poly)[0] else -n


# ------------------------------------------------------------------ tête : nœud d'os et ailettes (plan a, rayon b ; px)
A_NOEUD = 17.9                     # milieu du nœud
N0, N1 = 14.35, 21.45              # bas et haut du nœud


def r_noeud(a):
    """Apothème du nœud (tour à 12 pans) à l'abscisse a."""
    pts = [(N0, 0.0), (N0 + 0.02, 0.9), (14.6, 1.05), (15.0, 1.3), (15.6, 1.55), (17.9, 1.72), (20.2, 1.55),
           (20.8, 1.3), (21.2, 1.05), (N1 - 0.02, 0.9), (N1, 0.0)]
    return float(np.interp(a, [p[0] for p in pts], [p[1] for p in pts]))


B_RAC = 0.75                       # racine des ailettes (dans le nœud)
# croc : bord extérieur convexe du bas jusqu'à la pointe recourbée vers le haut, bord intérieur creusé jusqu'au haut du nœud
EXT = catmull([(15.05, B_RAC), (15.1, 1.5), (16.2, 2.2), (17.4, 3.05), (18.4, 4.0), (19.25, 4.95)], 7)
INT = catmull([(19.25, 4.95), (19.55, 3.85), (20.0, 2.8), (20.6, 2.0), (21.0, 1.5), (21.05, B_RAC)], 7)
_E = resample(EXT, 0.7)
_I = resample(INT, 0.7)
POLY = _E + _I[1:]                 # fermé par la racine (b = B_RAC, dans le nœud)
FIL_POLY = _E + _I[1:]             # tous les bords sont biseautés (la racine est cachée)
TIP = np.array(_E[-1])

# ------------------------------------------------------------------ vrai volume (os plein, opaque)
Z_E = 0.10                       # demi-épaisseur au fil
T_BIS = 0.85                     # pente unique des biseaux (40°)
TH = 0.3
DF = 16.0
RECOUV = 0.08
AL = math.atan(T_BIS)
Z_FOND = 0.16                    # fond de la gouttière
O_ = np.array((A_NOEUD, B_RAC))


class Ailette:
    """Plaque biseautée fermée (plan a, b) : contour poly, fils, plat z = h0 + k (P - O_)·u ; gouttière le long de `gaxe`."""

    def __init__(self, nom, poly, fil, u, h_racine, h_bout, gaxe, gw):
        self.nom, self.poly = nom, poly
        self.u = unit(u)
        pa = np.array(poly) - O_
        s_ = pa @ self.u
        self.L = float(s_.max())
        s_r = 0.6
        self.k = (h_bout - h_racine) / (self.L - s_r)
        self.h0 = h_racine - self.k * s_r
        self.segs = subdiv(fil)
        # gouttière : fuseau pointu aux deux bouts le long d'une courbe
        G = np.array(resample(catmull(gaxe, 8), 0.05))
        idx = np.linspace(0, len(G) - 1, 17).round().astype(int)
        ax, gl, gr = [], [], []
        for j, i in enumerate(idx):
            v = j / 16
            d = unit(G[min(i + 1, len(G) - 1)] - G[max(i - 1, 0)])
            n = np.array((-d[1], d[0]))
            w = gw * math.sin(math.pi * v) ** 0.6 + 0.012
            ax.append(tuple(G[i]))
            gl.append(tuple(G[i] + n * w))
            gr.append(tuple(G[i] - n * w))
        self.gax, self.gl, self.gr = ax, gl, gr
        self.gpoly = gl + gr[::-1]
        # reflet violacé : une ligne au milieu du pan, entre la gouttière et le bord extérieur
        Ee = np.array(resample(EXT, 0.1))
        cen = []
        for i in range(8, len(Ee) - 8, 4):
            d = unit(Ee[i + 1] - Ee[i - 1])
            n = normale_dedans(poly, Ee[i], d)
            cen.append(tuple(Ee[i] + n * 1.05))
        self.centres = cen
        # veines : partent du fil extérieur et montent vers le nœud
        Tr = np.array(resample(EXT, 0.05))
        ls = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(Tr, axis=0), axis=1))])
        self.veines = []
        for j, (t, pente, fr, br) in enumerate(((0.45, 0.45, 0.6, 0.5), (0.72, 0.35, 0.5, 0.0))):
            i = min(max(int(np.searchsorted(ls, t * ls[-1])), 1), len(Tr) - 2)
            d = unit(Tr[i + 1] - Tr[i - 1])
            n = normale_dedans(poly, Tr[i], d)
            st = Tr[i] + n * 0.02
            ln = 1.35 * fr
            pts = [st]
            for kk in (1, 2, 3, 4):
                ang = pente * (1 - 0.35 * kk) + 0.22 * math.sin(kk * 2.3 + j)
                pts.append(pts[-1] + (n * math.cos(ang) + d * math.sin(ang)) * ln / 4)
            self.veines.append([tuple(p) for p in pts])
            if br:
                b0 = np.array(pts[2])
                self.veines.append([tuple(b0), tuple(b0 + (n * 0.6 - d * np.sign(pente) * 0.8) * ln * br * 0.5)])

    def h(self, P):
        return self.h0 + self.k * ((np.asarray(P, float) - O_) @ self.u)

    def wb(self, P):
        return np.maximum((self.h(P) - Z_E) / T_BIS, 0.02)

    def dE(self, P):
        return d_stack(P, self.segs).min(0)

    def surf(self, P):
        P = np.asarray(P, float)
        return np.minimum(self.h(P), Z_E + T_BIS * self.dE(P))

    def s(self, P):
        return np.clip(((np.asarray(P, float) - O_) @ self.u) / self.L, 0, 1)

    def actif(self, P):
        """Le fil (vert) commence au-dessus du nœud : près de lui, l'os reste nu (liseré violacé)."""
        return smv(np.asarray(P, float)[..., 1], 2.0, 2.6)

    def in_g(self, P):
        return in_poly(P, self.gpoly)

    def d_g(self, P):
        return d_poly(P, list(self.gpoly) + [self.gpoly[0]])

    def d_ax(self, P):
        return d_poly(P, self.gax)

    def d_veine(self, P):
        return np.min(np.stack([d_poly(P, v) for v in self.veines]), axis=0)


GAXE = [(17.7, 1.9), (18.15, 2.4), (18.5, 2.95), (18.8, 3.55)]
AIL = Ailette("ail", POLY, FIL_POLY, (0.0, 1.0), 0.66, 0.25, GAXE, 0.27)


def bruit(P, seed=0.0):
    s, r = P[..., 0], P[..., 1]
    return 0.5 * np.sin(s * 1.7 + r * 2.3 + seed) + 0.3 * np.sin(s * 4.3 - r * 3.1 + 1.0 + seed) + 0.2 * np.sin(s * 9.1 + r * 7.7 + seed)


def veines(pc, P2, col, em):
    d = pc.d_veine(P2)
    k = pc.actif(P2)
    m1, m0 = (d < 0.12) & (k > 0.4), (d < 0.055) & (k > 0.4)
    col[m1] = VEIN
    col[m0] = VCORE
    em[m0] = E_VEINE
    return col, em


# --- peintures (couleur, alpha None = opaque, émissif)
def peint_biseau(pc, P2, d, sg):
    f = np.clip(d / pc.wb(P2), 0, 1.2)
    k = pc.actif(P2)
    nz = bruit(P2, 1.0 + sg)[..., None]
    col = lerp(OS_BASE, OS_SOMBRE, np.clip((f[..., None] - 0.5) / 0.45, 0, 1) * 0.7) + nz * 5 + np.zeros(P2.shape[:-1] + (3,), np.float32)
    em = np.zeros(col.shape, np.float32)
    fil_f, bande_f, halo_f = 0.22 * k, 0.42 * k, 0.56 * k
    au = (f >= bande_f) & (f < halo_f)
    col[au] = lerp(AURA, col[au], np.clip((f[au] - bande_f[au]) / np.maximum(halo_f[au] - bande_f[au], 1e-3), 0, 1)[..., None])
    col[(f >= fil_f) & (f < bande_f)] = VEIN
    col, em = veines(pc, P2, col, em)
    col[f >= 0.68] = ARETE                                        # liseré violacé large entre le fil et le plat (lisible dans la case)
    nu = (f < 0.30) & (k < 0.3)                                   # près du nœud : os nu à liseré violacé
    col[nu] = ARETE
    fil = f < fil_f
    col[fil] = FIL
    em[f < fil_f + 0.02 * k] = E_COL
    return col, None, em


def peint_fil(pc, P2, d, sg):
    k = pc.actif(P2)
    col = np.zeros(P2.shape[:-1] + (3,), np.float32) + ARETE
    em = np.zeros_like(col)
    on = k > 0.35
    col[on] = FIL
    em[on] = E_COL
    return col, None, em


def peint_plat(pc, P2, d, sg):
    wb = pc.wb(P2)
    nz = bruit(P2, 2.0 + 3 * sg)
    col = lerp(OS_BASE, OS_CLAIR * 1.1, np.clip(0.55 + 0.6 * nz, 0, 1)[..., None])
    col = col * (1 + 0.05 * np.sin(pc.s(P2) * 38.0 + nz * 2))[..., None]        # stries de croissance de l'os
    col = col * (1 - 0.25 * np.clip(1 - (P2[..., 1] - 1.6) / 1.0, 0, 1))[..., None]    # plus sombre contre le nœud
    dc = d_poly(P2, pc.centres)
    col = lerp(col, REFLET * 1.05, (np.clip(1.15 - dc / 1.1, 0, 1) * 0.8)[..., None])   # reflet violacé au milieu du pan (large : lisible)
    em = np.zeros(col.shape, np.float32)
    col, em = veines(pc, P2, col, em)
    col[d < wb + 0.05] = ARETE
    dg = pc.d_g(P2)
    col[dg < 0.06] = ARETE                                        # lèvre de la gouttière
    col[(dg >= 0.06) & (dg < 0.11) & ~pc.in_g(P2)] = OS_SOMBRE
    return col, None, em


# ------------------------------------------------------------------ cubes différés
TILES = {}
CUBES = []
SIX = ("north", "south", "east", "west", "up", "down")
SPEC_CACHE = {}


def tuile(nom, rgba, e=None):
    assert nom not in TILES, nom
    TILES[nom] = (rgba, e)
    return nom


def finir(col, al, em, masque):
    rgba = np.zeros(col.shape[:2] + (4,), np.uint8)
    rgba[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    rgba[..., 3] = 255 * masque
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


def spec(groupe, nom, cle, c, X, Y, s, peintures):
    """Cube dans le plan courant (a, b, z) ; chaque face peinte est échantillonnée texel par texel et découpée par l'alpha.
    Les six ailettes ont la même géométrie dans leur plan : tuiles calculées une fois (clé `cle`) puis reprises."""
    X, Y, Z = repere(X, Y)
    c = np.asarray(c, float)
    if cle not in SPEC_CACHE:
        faces = {}
        for f, fn in peintures.items():
            P = points_face(c, X, Y, Z, s, f)
            col, al, em, m = fn(P)
            if m.any():
                faces[f] = tuile(f"{cle}_{f}", *finir(col, al, em, m))
        SPEC_CACHE[cle] = faces
    faces = SPEC_CACHE[cle]
    if faces:
        CUBES.append({"groupe": groupe, "nom": nom, "c": Lp(*c), "R": np.column_stack([Lv(*X), Lv(*Y), Lv(*Z)]),
                      "half": np.asarray(s, float) / 2, "faces": faces})


def volume(pc, groupe, pre):
    """Plaque biseautée fermée opaque : deux biseaux par tronçon de fil (un par face), un plat incliné par face."""
    for idx, (p, q, v0, v1) in enumerate(pc.segs):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        pm = (p + q) / 2
        cand = np.array([pm + n * 0.25, pm - n * 0.25])
        prof = np.where(in_poly(cand, pc.poly), d_poly(cand, list(pc.poly) + [pc.poly[0]]), -1.0)
        if prof[1] > prof[0]:
            n = -n
        wmax = float(max(pc.wb(p[None])[0], pc.wb(q[None])[0]))
        e0 = wmax * 1.6 if v0 else 0.04
        e1 = wmax * 1.6 if v1 else 0.04
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        sy = (wmax + 0.1) / math.cos(AL)
        for sg in (1, -1):
            Y = np.array((n[0] * math.cos(AL), n[1] * math.cos(AL), sg * math.sin(AL)))
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0], mid[1], sg * Z_E)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(P, idx=idx, sg=sg):
                P2 = P[..., :2]
                D = d_stack(P2, pc.segs)
                de = D.min(0)
                own = D[idx] <= de + RECOUV
                m = in_poly(P2, pc.poly) & own & (de < pc.wb(P2) + 0.03) & (de >= -0.02)
                col, al, em = peint_biseau(pc, P2, de, sg)
                return col, al, em, m

            def fil(P, idx=idx, n=n, sg=sg):
                P2 = P[..., :2] + n * 0.04
                D = d_stack(P2, pc.segs)
                own = D[idx] <= D.min(0) + RECOUV
                m = in_poly(P2, pc.poly) & own
                col, al, em = peint_fil(pc, P2, D.min(0), sg)
                return col, al, em, m

            cle = f"{pc.nom}_bis{'pm'[sg < 0]}{idx}"
            spec(groupe, f"{pre}_bis{'pm'[sg < 0]}{idx}", cle, c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil})
    u = pc.u
    pp_ = np.array((-u[1], u[0]))
    pa = np.array(pc.poly) - O_
    s_, t_ = pa @ u, pa @ pp_
    s0, s1, t0, t1 = s_.min() - 0.05, s_.max() + 0.05, t_.min() - 0.05, t_.max() + 0.05
    Pc = O_ + u * (s0 + s1) / 2 + pp_ * (t0 + t1) / 2
    for sg in (1, -1):
        X = unit(np.array((u[0], u[1], sg * pc.k)))
        Y = sg * np.array((pp_[0], pp_[1], 0.0))
        Z = np.cross(X, Y)
        c = np.array((Pc[0], Pc[1], sg * float(pc.h(Pc)))) - Z * (TH / 2)

        def plat(P, sg=sg):
            P2 = P[..., :2]
            de = pc.dE(P2)
            m = in_poly(P2, pc.poly) & (de >= pc.wb(P2) - 0.03) & ~pc.in_g(P2)
            col, al, em = peint_plat(pc, P2, de, sg)
            return col, al, em, m

        spec(groupe, f"{pre}_plat{'pm'[sg < 0]}", f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y,
             ((s1 - s0) * math.sqrt(1 + pc.k ** 2), t1 - t0, TH), {"south": plat})


def gouttiere(pc, groupe, pre):
    """Gouttière creusée : trou dans les plats (alpha), parois d'os par tronçon et par face, fond où le filet vert est couché."""
    gp = np.array(pc.gpoly)
    a0, a1 = gp[:, 0].min() - 0.15, gp[:, 0].max() + 0.15
    b0, b1 = gp[:, 1].min() - 0.15, gp[:, 1].max() + 0.15

    def fond(P):
        P2 = P[..., :2]
        m = pc.in_g(P2) | (pc.d_g(P2) < 0.1)
        dc = pc.d_ax(P2)
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + OS_SOMBRE
        em = np.zeros_like(col)
        col[dc < 0.19] = AURA
        col[dc < 0.14] = VEIN
        col[dc < 0.08] = VCORE
        em[dc < 0.14] = E_VEINE
        em[dc < 0.08] = E_COL
        return col, None, em, m

    spec(groupe, f"{pre}_fond", f"{pc.nom}_fond", ((a0 + a1) / 2, (b0 + b1) / 2, 0.0), (1, 0, 0), (0, 1, 0),
         (a1 - a0, b1 - b0, 2 * Z_FOND), {"south": fond, "north": fond})
    murs = [(pts[i], pts[i + 1]) for pts in (pc.gl, pc.gr) for i in range(len(pts) - 1)]
    for j, (p, q) in enumerate(murs):
        p, q = np.asarray(p, float), np.asarray(q, float)
        Ln = float(np.linalg.norm(q - p))
        if Ln < 0.02:
            continue
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        mid = (p + q) / 2
        if pc.in_g(np.array([mid + n * 0.03]))[0]:
            n = -n                                                   # n vers l'extérieur de la gouttière
        back = [p + n * TH, q + n * TH, mid + n * TH]
        top = min(float(pc.surf(np.array([x]))[0]) for x in back + [p, q, mid]) - 0.03
        z0 = Z_FOND - 0.04
        if top - z0 < 0.06:
            continue
        for sg in (1, -1):
            zc = sg * (z0 + top) / 2
            X = np.array((d[0], d[1], 0.0))
            Y = np.array((0.0, 0.0, 1.0))
            Z = np.cross(X, Y)
            face = "south" if Z[:2] @ n < 0 else "north"

            def paroi(P):
                P2 = P[..., :2]
                dz = pc.h(P2) - np.abs(P[..., 2])
                col = lerp(OS_BASE, OS_SOMBRE, np.clip((dz[..., None] - 0.06) / 0.3, 0, 1)) + np.zeros(P.shape[:-1] + (3,), np.float32)
                col[dz < 0.07] = ARETE
                return col, None, None, np.ones(P.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zc)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec(groupe, f"{pre}_paroi{'pm'[sg < 0]}{j}", f"{pc.nom}_paroi{'pm'[sg < 0]}{j}", c, X, Y,
                 (Ln + 0.02, top - z0, TH), {face: paroi})


# ------------------------------------------------------------------ tours (pièces rondes, recette de skin_epee_abyssal)
OVL, OVW = 0.04, 0.03
DENS = 16.0


def p_os(xn, t, y, r, L, ex):
    k = np.clip(0.38 + 0.45 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    col = lerp(OS_SOMBRE, OS_CLAIR, k[..., None]) * (1 + 0.06 * np.sin(y * 23 + xn))[..., None]
    col = np.where((np.abs(xn) < 0.22)[..., None], lerp(col, REFLET, 0.45), col)
    return col, None


def p_noeud(xn, t, y, r, L, ex):
    """Nœud d'os : os marbré plus clair, reflet violacé au milieu du pan, deux sillons violacés en long (veines de l'os)."""
    k = np.clip(0.45 + 0.42 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    col = lerp(OS_SOMBRE, OS_CLAIR * 1.12, k[..., None]) * (1 + 0.06 * np.sin(y * 19 + xn * 2))[..., None]
    col = np.where((np.abs(xn) < 0.25)[..., None], lerp(col, REFLET, 0.5), col)
    col = np.where((np.abs(xn) > 0.88)[..., None], lerp(col, ARETE, 0.55), col)
    return col, None


def p_bague(xn, t, y, r, L, ex):
    k = np.clip(0.4 + 0.5 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    return lerp(OS_BASE, ARETE, k[..., None] * 0.85), None


def p_cuir(xn, t, y, r, L, ex):
    f = ((y / 0.62 + xn * 0.16) % 1.0)[..., None]
    col = lerp(C(84, 44, 98), C(38, 18, 48), f)
    col = np.where(f > 0.82, C(14, 7, 18), col)
    return col * (1 + 0.04 * np.sin(xn * 3 + y * 11))[..., None], None


def p_clou(xn, t, y, r, L, ex):
    k = (1 - np.abs(xn))[..., None]
    return lerp(C(150, 132, 160), C(214, 200, 218), k), None


def p_griffe(xn, t, y, r, L, ex):
    tg = ex["t0"] + (ex["t1"] - ex["t0"]) * t
    q = np.abs(xn)
    col = lerp(C(54, 48, 66), C(26, 22, 34), (q ** 1.2)[..., None])
    col = lerp(col, C(132, 98, 176), (np.clip(1 - q * 2.4, 0, 1) * 0.45)[..., None])
    col = col * (1 - 0.18 * (np.sin(tg * 40.0) > 0.85))[..., None]                     # bagues de croissance
    col = lerp(col, C(132, 240, 58), np.clip((tg - 0.62) / 0.25, 0, 1)[..., None])
    em = np.zeros(col.shape, np.float32)
    on = tg > 0.74
    em[on] = lerp(C(44, 110, 26), C(96, 230, 58), np.clip((tg[on] - 0.74) / 0.2, 0, 1)[..., None])
    return col, em


PEINTRES = {"os": p_os, "noeud": p_noeud, "bague": p_bague, "cuir": p_cuir, "clou": p_clou, "griffe": p_griffe}


def tuile_pan(nom, mat, L, w0, w1, r0, r1, ex):
    """Tuile d'un pan trapézoïdal : rangée 0 = bout P1 (haut de la face south)."""
    if nom in TILES:
        return nom
    wm = max(w0, w1) + 2 * OVW
    Lf = L + 2 * OVL
    Wt, Ht = max(2, int(math.ceil(wm * DENS))), max(2, int(math.ceil(Lf * DENS)))
    yy, xx = np.mgrid[0:Ht, 0:Wt]
    x = ((xx + 0.5) / Wt - 0.5) * wm
    y = Lf * (1 - (yy + 0.5) / Ht) - OVL
    t = np.clip(y / max(L, 1e-6), 0, 1)
    hw = (w0 + (w1 - w0) * t) / 2 + OVW
    mask = np.abs(x) <= hw
    xn = np.clip(x / np.maximum(hw - OVW, 1e-3), -1, 1)
    r = r0 + (r1 - r0) * t
    col, em = PEINTRES[mat](xn, t, y + ex.get("y0", 0.0), r, L, ex)
    return tuile(nom, *finir(col, None, em, mask))


def tour(g, nom, O, ax, ref, profil, n=12, phase=0.0, cle=None):
    """profil = [(b0, r0, b1, r1, mat, ex), ...] le long de ax depuis O (monde) ; une couronne de n pans par tronçon."""
    O, ax = np.asarray(O, float), unit(np.asarray(ax, float))
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    cle = cle or nom
    for i, (b0, r0, b1, r1, mat, ex) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        if L < 1e-4:
            continue
        tile = tuile_pan(f"{cle}{i}", mat, L, 2 * r0 * tn, 2 * r1 * tn, r0, r1, ex)
        db, dr = (b1 - b0) / L, (r1 - r0) / L
        wm = max(2 * r0 * tn, 2 * r1 * tn) + 2 * OVW
        for k in range(n):
            th = phase + TAU * k / n
            e = math.cos(th) * ref + math.sin(th) * w3
            Pa, Pb = O + b0 * ax + r0 * e, O + b1 * ax + r1 * e
            Y = unit(Pb - Pa)
            N = -dr * ax + db * e
            X = np.cross(Y, N)
            CUBES.append({"groupe": g, "nom": f"{nom}{i}_{k}", "c": (Pa + Pb) / 2 - N * TH / 2, "R": np.column_stack([X, Y, N]),
                          "half": np.array((wm / 2, L / 2 + OVL, TH / 2)), "faces": {"south": tile}})


def griffe(g, nom, p, X, Y, L, rmax, curve=0.30, nseg=8, n=8, cle=None):
    """Griffe recourbée en tronçons coniques à 8 pans : part de p (monde) vers X, se recourbe vers Y ; pointe verte."""
    p, X = np.asarray(p, float), unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    nz = np.cross(X, Y)
    cle = cle or nom
    centre = lambda t: p + X * (L * (t - 0.12 * t * t)) + Y * (curve * L * t ** 2.1)
    ray = lambda t: rmax * (max(0.0, 1 - t) ** 0.8 + 0.06) / 1.06
    for i in range(nseg):
        t0, t1 = i / nseg, (i + 1) / nseg
        a, b = centre(t0), centre(t1)
        prof = [(0.0, ray(t0), float(np.linalg.norm(b - a)), ray(t1) if i < nseg - 1 else 0.0, "griffe", {"t0": t0, "t1": t1})]
        if i == 0:                                   # bouchon conique : la racine n'est jamais un anneau ouvert
            prof.insert(0, (-0.3, 0.0, 0.0, ray(0.0), "griffe", {"t0": 0.0, "t1": 0.0}))
        tour(g, f"{nom}{i}_", a, b - a, nz, prof, n=n, cle=f"{cle}{i}_")


# ------------------------------------------------------------------ conception
GROUPES = []        # (nom, pivot, parent)
CTRL = "ctrl_lumiere"
N_AIL = 6


def grp(nom, pivot, parent):
    GROUPES.append((nom, np.asarray(pivot, float), parent))
    return nom


def e_ail(j):
    th = TAU * j / N_AIL
    e = math.cos(th) * W_ + math.sin(th) * T_
    return e, np.cross(A_, e)


OUT = {}


def conception():
    racine = grp(objet.etape("repos", "masse"), Wp(A_PRISE), None)
    masse = grp("masse", Wp(A_PRISE), racine)            # pivot dans la main : tressaillement au coup
    manche = grp("manche", Wp(A_PRISE), masse)

    def bg(a0, a1, r_in, r_out):
        return [(a0, r_in, a0 + 0.12, r_out, "bague", {"clair": 0.1}), (a0 + 0.12, r_out, a1 - 0.12, r_out, "bague", {}),
                (a1 - 0.12, r_out, a1, r_in, "bague", {"clair": -0.1})]
    R_H = 0.55
    prof = ([(-0.55, 0.0, -0.4, 0.62, "os", {"clair": 0.1})] + bg(-0.4, 0.25, 0.62, 0.82)
            + [(0.25, 0.68, 6.45, 0.68, "cuir", {})] + bg(6.45, 6.95, R_H, 0.80)
            + [(6.95, R_H, 9.9, R_H, "os", {"y0": 1.0})] + bg(9.9, 10.4, R_H, 0.70)
            + [(10.4, R_H, 13.2, 0.6, "os", {"y0": 3.0})] + bg(13.2, 13.65, 0.6, 0.82)
            + [(13.65, 0.7, 14.5, 1.12, "os", {"clair": 0.08})])
    tour(manche, "hampe", Wp(0), A_, T_, prof, n=12)
    for k, a in enumerate((1.4, 3.3, 5.2)):
        ax_ = T_ if k != 1 else W_
        tour(manche, f"clou{k}_", Wp(a) - ax_ * 0.86, ax_, A_, [(0.0, 0.0, 0.14, 0.24, "clou", {}), (0.14, 0.24, 1.58, 0.24, "clou", {}),
                                                              (1.58, 0.24, 1.72, 0.0, "clou", {})], n=8, phase=math.pi / 8, cle="clou")
    talon = grp("griffe_talon", Wp(-0.5), manche)
    griffe(talon, "gt", Wp(-0.45), -A_, W_, 1.55, 0.5, curve=0.22, nseg=6)

    # --- tête : nœud d'os renflé (12 pans), bagues violacées, croc conique au sommet, clous pâles entre les crocs
    tete = grp("tete", Wp(A_NOEUD), masse)
    grp(CTRL, Wp(A_NOEUD), tete)
    pts = [(N0, 0.0), (N0 + 0.02, 0.9), (14.6, 1.05), (15.0, 1.3), (15.6, 1.55), (17.9, 1.72), (20.2, 1.55),
           (20.8, 1.3), (21.2, 1.05), (N1 - 0.02, 0.9), (N1, 0.0)]
    mats = ["os", "bague", "bague", "noeud", "noeud", "noeud", "noeud", "bague", "bague", "os"]
    prof_n = []
    for i, ((b0, r0), (b1, r1)) in enumerate(zip(pts[:-1], pts[1:])):
        prof_n.append((b0, r0, b1, r1, mats[i], {"clair": 0.08 if mats[i] == "bague" else 0.0, "y0": 0.7 * i}))
    tour(tete, "noeud", Wp(0), A_, W_, prof_n, n=12, phase=TAU / 24)
    # bagues en relief : deux anneaux violacés qui serrent le nœud sous et au-dessus des crocs
    for nm, a0, a1, ra in (("bague_b", 14.75, 15.2, 1.38), ("bague_h", 20.55, 21.0, 1.38)):
        tour(tete, nm, Wp(0), A_, W_, bg(a0, a1, ra - 0.18, ra), n=12, phase=TAU / 24, cle="bg_noeud")
    # clous d'os pâle entre les crocs, au renflement
    for j in range(N_AIL):
        th = TAU * (j + 0.5) / N_AIL
        e = math.cos(th) * W_ + math.sin(th) * T_
        tour(tete, f"clou_n{j}_", Wp(A_NOEUD) + e * 1.45, e, A_,
             [(0.0, 0.34, 0.22, 0.34, "clou", {}), (0.22, 0.34, 0.45, 0.0, "clou", {"clair": 0.1})], n=8, cle="clou_n")
    # croc du sommet : collet d'os puis croc conique droit à pointe verte
    sommet = grp("croc_sommet", Wp(N1 - 0.1), tete)
    tour(sommet, "collet_s", Wp(0), A_, W_, bg(N1 - 0.2, N1 + 0.35, 0.82, 0.95), n=12, phase=TAU / 24)
    griffe(sommet, "cs", Wp(N1 + 0.3), A_, W_, 2.4, 0.66, curve=0.0, nseg=6, n=10)

    # --- crocs (ailettes) : groupe parent `crocs` (déplié à event_select), un groupe par croc (respire, s'ouvre)
    crocs = grp("crocs", Wp(A_NOEUD), tete)
    OUT["crocs"] = []
    for j in range(N_AIL):
        e, n = e_ail(j)
        FR[1], FR[2] = e, n
        g = grp(f"croc_{j}", Wp(A_NOEUD) + e * 1.5, crocs)
        volume(AIL, g, f"c{j}")
        gouttiere(AIL, g, f"c{j}")
        OUT["crocs"].append((g, n))
    FR[1], FR[2] = W_, T_
    OUT.update(racine=racine, masse=masse, tete=tete, crocs_grp=crocs, sommet=sommet, talon=talon)
    return racine


RACINE = conception()


# ------------------------------------------------------------------ atlas
def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


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
    assert set(np.unique(tex[..., 3])) <= {0, 255}, "semi-transparence interdite (aucun groupe trans_)"
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


def axe_angle(n, deg):
    """Matrice de rotation de deg degrés autour de l'axe unitaire n (monde)."""
    n = unit(n)
    a = math.radians(deg)
    K = np.array([[0, -n[2], n[1]], [n[2], 0, -n[0]], [-n[1], n[0], 0]])
    return np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K


SIGNE = float(os.environ.get("SIGNE", "-1"))    # sens contrôlé dans .build/anims.png : deg > 0 = pointes vers le bas et le dehors


def ouvre(t, n, deg):
    """Le croc tourne dans son plan autour de n = A_ × e (pivot à sa racine) : deg > 0 ouvre la gueule (pointe qui s'écarte
    vers le bas et le dehors, comme une fleur qui s'ouvre), deg < 0 la referme (pointes vers le sommet)."""
    x, y, z = euler(axe_angle(n, -deg * SIGNE))
    return kf("rotation", t, round(x, 3), round(y, 3), round(z, 3))


def rot(t, z):
    return kf("rotation", t, 0, 0, z)


def lum(t, x):
    return kf("position", t, x, 0, 0)


def anim(name, length, loop="once"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "item_idle", "animators": {}}


def piste(an, g, keys):
    an["animators"][groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": keys}


def echant(L, n):
    return [round(L * i / n, 4) for i in range(n + 1)]


CR = OUT["crocs"]

# item_idle (6 s) : les crocs respirent à contretemps (±2°), le fil souffle (ctrl_lumiere ±0,35).
L_IDLE = 6.0
idle = anim("item_idle", L_IDLE, "loop")
for j, (g, n) in enumerate(CR):
    piste(idle, g, [ouvre(t, n, 2.0 * math.sin(TAU * (t / L_IDLE - j / N_AIL))) for t in echant(L_IDLE, 24)])
piste(idle, CTRL, [lum(t, 0.35 * math.sin(TAU * 2 * t / L_IDLE)) for t in echant(L_IDLE, 24)])

# event_select (0,7 s) : la couronne de crocs sort du nœud (échelle de `crocs` : seul dépliage par scale), le fil s'allume.
L_SEL = 0.7
sel = anim("event_select", L_SEL)
piste(sel, OUT["crocs_grp"], [kf("scale", t, 0.35 + 0.65 * sm(t, 0.0, 0.32) + 0.07 * bump(t, 0.24, 0.32, 0.36, 0.52))
                              for t in echant(L_SEL, 21)])
for j, (g, n) in enumerate(CR):                      # les crocs se déplient en cascade autour du nœud
    piste(sel, g, [ouvre(t, n, -18 * (1 - sm(t, 0.16 + 0.035 * j, 0.42 + 0.035 * j))) for t in echant(L_SEL, 21)])
piste(sel, CTRL, [lum(t, -1 + 1 * sm(t, 0.3, 0.45) + 0.8 * bump(t, 0.4, 0.48, 0.52, 0.7)) for t in echant(L_SEL, 21)])

# event_swing (0,35 s) : la gueule se referme un peu sur le coup (−5°), le fil s'avive. Aucun son.
L_SW = 0.35
sw = anim("event_swing", L_SW)
for j, (g, n) in enumerate(CR):
    piste(sw, g, [ouvre(t, n, -5 * bump(t, 0.0, 0.08, 0.14, 0.33)) for t in echant(L_SW, 14)])
piste(sw, CTRL, [lum(t, 0.7 * bump(t, 0.0, 0.05, 0.1, 0.33)) for t in echant(L_SW, 14)])

# event_hit (0,6 s) : la gueule s'ouvre d'un coup (+7°) puis frissonne, éclat du fil (+1,6), la tête tressaille ;
# **le seul son** (block.sculk.break à 0,04 s).
L_HIT = 0.6
hit = anim("event_hit", L_HIT)
for j, (g, n) in enumerate(CR):
    piste(hit, g, [ouvre(t, n, 7 * sm(t, 0.0, 0.05) * (1 - sm(t, 0.08, 0.5)) + 2.0 * math.sin(TAU * 3 * t / 0.36 + j) * (1 - sm(t, 0.05, 0.4)))
                   for t in echant(L_HIT, 24)])
piste(hit, OUT["tete"], [rot(t, round(-2.5 * math.exp(-t / 0.1) * math.sin(TAU * t / 0.16), 3)) for t in echant(L_HIT, 24)])
piste(hit, CTRL, [lum(t, 1.6 * (sm(t, 0.0, 0.03) * (1 - sm(t, 0.06, 0.55)))) for t in echant(L_HIT, 24)])

ANIMS = [idle, sel, sw, hit]


# ------------------------------------------------------------------ écriture
assert len(elements) <= 8192, f"budget : {len(elements)} cubes"


def coins():
    P = []
    for e in elements:
        f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
        R = rotm(*e.get("rotation", (0, 0, 0)))
        for i in range(8):
            c = np.array([(f, t)[(i >> k) & 1][k] for k in range(3)])
            P.append(R @ (c - o) + o)
    return np.array(P)


P = coins()
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
# Display : préréglage _MASSE (item/handheld_mace du jar) ; gui ramené à la case (boîte plus grande que 16 px)
_cb = (P.min(axis=0) + P.max(axis=0)) / 2
GUI_T = [round(float(-(_cb[0] - 8) * GUI), 2), round(float(-(_cb[1] - 8) * GUI), 2), 0]
AFFICHAGE = objet.affichage("masse", gui={"translation": GUI_T, "scale": [GUI] * 3})
model = objet.modele(NOM, "masse", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son
limiter_sons(model)
# Un seul son, au coup qui touche (event_hit), une seule clé à 0,04 s (une clé à 0,0 est muette au premier coup).
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "block.sculk.break")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


LONG = float(((P - G0) @ A_).max() - ((P - G0) @ A_).min())
LARG = float(((P - G0) @ W_).max() - ((P - G0) @ W_).min())
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur {LONG:.1f} px, largeur de tête {LARG:.1f} px ; boîte {P.min(0).round(2)} .. {P.max(0).round(2)}")
gm = min(float(AIL.h(np.array([p]))[0] - Z_FOND) for p in AIL.gax)
marge = min(float(AIL.dE(np.array([p]))[0] - AIL.wb(np.array([p]))[0]) for p in AIL.gl + AIL.gr)
print(f"croc : épaisseur {2 * AIL.h(np.array([(18.0, 1.7)]))[0]:.2f} px au nœud -> {2 * AIL.h(TIP[None])[0]:.2f} à la pointe ; "
      f"profondeur mini de gouttière {gm:.2f} px, marge gouttière/biseau {marge:.2f} px ; GUI {GUI} {GUI_T}")
