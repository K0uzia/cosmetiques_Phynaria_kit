"""Égide de l'Abysse : skin de bouclier (guide 14, type `bouclier`), ensemble Abyssal (thème Démoniaque). Design original.
Écrit skin_bouclier_abyssal.png, skin_bouclier_abyssal_e.png et .build/skin_bouclier_abyssal_brut.bbmodel à côté de ce script.

Idée : une **écaille d'os charbon** taillée en écu (pointe en bas, bord haut creusé entre deux épaules), bombée en carène,
armée de deux **cornes en crochet** aux épaules (signature du set, cornes_abyssales) et d'un umbo en collet d'os d'où sort une
**griffe conique à pointe verte**. Les veines de l'écaille sont des **gouttières creusées** où court le filet vert acide : on
les voit devant (3e personne, inventaire) et au dos (1re personne). Pas d'ailes repliées (Orage), pas de vertèbres ni
d'épines dorsales (« trop créature », styles/abyssal.md).
Famille Abyssal (sets-objets-2026-11-08.md, « Abyssal ») : os charbon taillé, plat marbré, biseaux plus sombres, arêtes en
liseré violacé, reflet violacé au milieu des pans ; cuir pourpre-noir en spirale à clous d'os pâle ; vert acide seulement aux
gouttières et aux pointes (cornes, griffe de l'umbo, pointe basse de l'écu, griffe de la quille) ; pas de métal, d'or ni de rouge.
Références (.claude/references/objets/boucliers.md) : écu (corps bombé, pointe en bas), umbo (bosse sur la poignée, point
focal), orle (bord renforcé : ici le biseau à liseré violacé), traverses et poignée au dos.

Vrai volume (recette .claude/references/objets/volume-3d.md), pas de plaques empilées :
- l'écu = deux demi-plaques biseautées fermées (classe Plaque, d'après la classe Fer opaque de gen_skin_lance_abyssal.py) :
  biseaux à pente unique 40°, plats plans inclinés (1,70 px à la quille -> 1,00 px au bord), faces échantillonnées texel par
  texel et découpées par l'alpha, recouvrement 0,08 ; chaque moitié tournée de 12° autour de la quille (carène) ;
- trois gouttières creusées par moitié (trou alpha dans les plats, parois d'os, fond où le filet vert + _e est couché) ;
- quille d'os octogonale devant et au dos, bagues violacées, griffe en haut et en bas ; umbo en tour octogonale (bague,
  collet, couvercle cerclé de violet) + griffe conique ; cornes en tronçons coniques ; dos : traverses d'os, montants,
  poignée de cuir en spirale (place de la poignée vanilla), bagues violacées, clous d'os.

Repère : celui du bouclier de Minecraft (plaque vanilla 12 x 22 de z = 1 à 2, face vers +Z, poignée vers -Z), Display de
`item/shield.json` recopié, étapes `repos` et `bloque` = deux copies (mêmes tuiles), pose de blocage `pose_bloque` en Molang
q.in_first_person x q.hand, calculée et contrôlée par matrices (technique de skin_bouclier_orage, reprise telle quelle).

Objet vivant (sobre) :
- item_idle (6 s) : **garde** (pose_bloque, recette 2 du retour du 2026-11-08 soir : une coupure d'utilisation ne fait plus
  retomber l'écu), cornes qui respirent à contretemps (±2,5°), veines qui soufflent (ctrl_lumiere) ;
- item_use (1,2 s) : garde, cornes dressées (+7°) qui frémissent, veines plus vives ; éclat quand un coup touche le porteur
  (q.hit_by_entity) ;
- event_select (0,7 s) : la griffe de l'umbo sort du collet (seul groupe déplié par `scale`), les cornes se déplient ;
- event_hit (0,5 s) : éclat des veines, cornes qui frissonnent ; **le seul son** (block.sculk.break à 0,04 s).
Aucun son ni animation sur event_use_start ni event_enter_* (rejoués à chaque coupure de l'utilisation, recette 3).
Fonctions avancées : calque _e (filets des gouttières, pointes vertes), ctrl_lumiere (non simulé par le renderer), étapes
repos/bloque, animations d'objet (item_idle, item_use, event_select, event_hit), Molang (q.in_first_person, q.hand,
q.hit_by_entity), scale animé. À juger en jeu : garde tenue 5 s (deux mains, 1re et 3e personne), lecture de l'écaille dans
la case et du dos en 1re personne, event_hit d'un bouclier et son son.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

NOM = "skin_bouclier_abyssal"
TEX = 512
TAU = 2 * math.pi
GUI = float(os.environ.get("GUI", "0.58"))    # la case : cornes et pointe comprises (vanilla 0,65)


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


def smv(t, a, b):
    u = np.clip((np.asarray(t, float) - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


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


# ------------------------------------------------------------------ géométrie 2D
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


# ------------------------------------------------------------------ l'écaille (demi-plaque droite, repère local u vers le bord, v vers le haut)
ZH = 1.5                          # plan moyen à la quille (plaque vanilla : z 1 à 2)
TILT = math.radians(12.0)         # carène
CT, ST = math.cos(TILT), math.sin(TILT)
U_R = -0.3                        # racine (cachée sous la quille)
CONTOUR = catmull([(0.0, 8.85), (1.3, 9.0), (2.7, 9.45), (3.9, 9.95), (4.75, 10.25), (5.55, 9.85), (6.0, 8.7), (6.2, 6.4),
                   (6.15, 3.4), (5.8, 0.0), (5.1, -3.5), (4.0, -6.6), (2.65, -9.0), (1.25, -10.9), (0.0, -12.0)], 6)
FIL_D = resample(CONTOUR, 0.7)
EPAULE = (4.75, 10.25)
H_RAC, H_BORD = 0.85, 0.50       # demi-épaisseurs à la quille et au bord (1,70 -> 1,00 px)
Z_E = 0.10                        # demi-épaisseur au fil
T_BIS = 0.85                      # pente unique des biseaux (40°)
AL = math.atan(T_BIS)
TH = 0.3
DF = 12.0                         # texels par px sur les faces échantillonnées (atlas 512 : deux demi-plaques)
RECOUV = 0.08
Z_FOND = 0.16
UMBO = np.array((0.0, 0.5))
# gouttières (veines de l'écaille) : ligne médiane (u, v) depuis l'umbo vers le bord, demi-largeur maxi
GOUTS = [([(1.55, 2.0), (2.35, 3.9), (3.1, 5.9), (3.75, 7.6)], 0.36),
         ([(2.0, 0.55), (3.2, 0.95), (4.35, 1.7), (5.0, 2.45)], 0.32),
         ([(1.45, -1.15), (2.15, -3.2), (2.6, -5.1), (2.55, -6.8)], 0.34)]


def hw_contour(v):
    i = np.argsort(CONTOUR[:, 1])
    return float(np.interp(v, CONTOUR[i, 1], CONTOUR[i, 0]))


class Gout:
    def __init__(self, pts, gw):
        c = catmull(pts, 8)
        c = np.array(resample(c, 0.45))
        n = len(c)
        tg = np.gradient(c, axis=0)
        tg /= np.linalg.norm(tg, axis=1)[:, None]
        nr = np.column_stack([-tg[:, 1], tg[:, 0]])
        w = np.array([gw * max(0.0, math.sin(math.pi * k / (n - 1))) ** 0.6 + 0.012 for k in range(n)])
        self.ax = [tuple(p) for p in c]
        self.gl = [tuple(p) for p in c + nr * w[:, None]]
        self.gr = [tuple(p) for p in c - nr * w[:, None]]
        self.poly = self.gl + self.gr[::-1]


class Plaque:
    """Demi-écaille biseautée fermée (repère local) : contour poly, fil = contour extérieur (sans la racine), plat incliné
    h = h0 + k (P - O)·u ; vert seulement près de la pointe basse ; gouttières creusées."""

    def __init__(self, nom, sg_u):
        self.nom, self.sg = nom, sg_u
        m = lambda pts: [(sg_u * a, b) for a, b in pts]
        fil = m(FIL_D)
        self.poly = [(sg_u * U_R, FIL_D[0][1])] + fil + [(sg_u * U_R, FIL_D[-1][1])]
        self.fil = fil
        self.O = np.array((0.0, 0.0))
        self.u = np.array((float(sg_u), 0.0))
        self.L = max(abs(a) for a, b in fil)
        self.k = (H_BORD - H_RAC) / self.L
        self.h0 = H_RAC
        self.segs = subdiv(fil)
        self.gouts = [Gout(m(p), w) for p, w in GOUTS]
        # veines de surface : seulement depuis la pointe verte (bas de l'écu)
        Tr = np.array(resample([p for p in fil if p[1] < -8.6], 0.05))
        ls = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(Tr, axis=0), axis=1))])
        self.veines = []
        for j, (t, pente) in enumerate(((0.25, 0.35), (0.6, -0.3))):
            i = min(max(int(np.searchsorted(ls, t * ls[-1])), 1), len(Tr) - 2)
            d = unit(Tr[i + 1] - Tr[i - 1])
            nn = np.array((-d[1], d[0]))
            if not in_poly(np.array([Tr[i] + nn * 0.12]), self.poly)[0]:
                nn = -nn
            pts = [Tr[i] + nn * 0.02]
            for kk in (1, 2, 3, 4):
                ang = pente * (1 - 0.3 * kk) + 0.25 * math.sin(kk * 2.1 + j)
                pts.append(pts[-1] + (nn * math.cos(ang) + d * math.sin(ang)) * 0.32)
            self.veines.append([tuple(p) for p in pts])

    def h(self, P):
        return self.h0 + self.k * ((np.asarray(P, float) - self.O) @ self.u)

    def wb(self, P):
        return np.maximum((self.h(P) - Z_E) / T_BIS, 0.02)

    def dE(self, P):
        return d_stack(P, self.segs).min(0)

    def surf(self, P):
        P = np.asarray(P, float)
        return np.minimum(self.h(P), Z_E + T_BIS * self.dE(P))

    def actif(self, P):
        """Vert seulement à la pointe basse de l'écu."""
        return smv(-np.asarray(P, float)[..., 1], 9.4, 10.6)

    def in_g(self, P):
        r = np.zeros(P.shape[:-1], bool)
        for g in self.gouts:
            r |= in_poly(P, g.poly)
        return r

    def d_g(self, P):
        return np.min(np.stack([d_poly(P, list(g.poly) + [g.poly[0]]) for g in self.gouts]), axis=0)

    def d_ax(self, P):
        return np.min(np.stack([d_poly(P, g.ax) for g in self.gouts]), axis=0)

    def d_veine(self, P):
        return np.min(np.stack([d_poly(P, v) for v in self.veines]), axis=0)


PL = {"d": Plaque("ecaille_d", 1), "g": Plaque("ecaille_g", -1)}
FR = {"d": (np.array((0.0, 0.0, ZH)), np.column_stack([(CT, 0, -ST), (0, 1, 0), (ST, 0, CT)])),
      "g": (np.array((0.0, 0.0, ZH)), np.column_stack([(CT, 0, ST), (0, 1, 0), (-ST, 0, CT)]))}
for _c, (_T, _M) in FR.items():
    assert np.allclose(np.cross(_M[:, 0], _M[:, 1]), _M[:, 2])


def Wa(cote, a, b, z=0.0):
    T, M = FR[cote]
    return T + M @ np.array((a, b, z), float)


def bruit(P, seed=0.0):
    s, r = P[..., 0], P[..., 1]
    return 0.5 * np.sin(s * 1.7 + r * 2.3 + seed) + 0.3 * np.sin(s * 4.3 - r * 3.1 + 1.0 + seed) + 0.2 * np.sin(s * 9.1 + r * 7.7 + seed)


def veines(pc, P2, col, em):
    d = pc.d_veine(P2)
    m1, m0 = d < 0.11, d < 0.05
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
    fil_f, bande_f, halo_f = 0.16 * k, 0.34 * k, 0.56 * k
    au = (f >= bande_f) & (f < halo_f)
    col[au] = lerp(AURA, col[au], np.clip((f[au] - bande_f[au]) / np.maximum(halo_f[au] - bande_f[au], 1e-3), 0, 1)[..., None])
    col[(f >= fil_f) & (f < bande_f)] = VEIN
    col, em = veines(pc, P2, col, em)
    col[f >= 0.90] = ARETE * 0.9
    nu = (f < 0.40) & (k < 0.3)                                   # bord d'os nu : liseré violacé large (lit la silhouette dans la case)
    col[nu] = ARETE
    col[f < fil_f] = FIL
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
    nz = bruit(P2, 2.0 + 3 * sg + pc.sg)
    col = lerp(OS_BASE, OS_CLAIR, np.clip(0.62 + 0.5 * nz, 0, 1)[..., None])
    ru = np.linalg.norm(P2 - UMBO, axis=-1)
    col = col * (1 + 0.06 * np.sin(ru * 5.2 + nz * 1.5))[..., None]               # stries de croissance autour de l'umbo
    fr = np.abs(P2[..., 0]) / np.maximum(np.array([hw_contour(v) for v in P2[..., 1].ravel()]).reshape(P2.shape[:-1]), 0.5)
    col = lerp(col, REFLET, (np.clip(1 - np.abs(fr - 0.62) / 0.2, 0, 1) * 0.5)[..., None])   # reflet violacé au milieu du pan
    col = col * (1 - 0.18 * np.clip(1 - np.abs(P2[..., 0]) / 0.9, 0, 1))[..., None]          # ombre le long de la quille
    em = np.zeros(col.shape, np.float32)
    col, em = veines(pc, P2, col, em)
    col[d < wb + 0.05] = ARETE
    dg = pc.d_g(P2)
    ing = pc.in_g(P2)
    col[(dg < 0.06) & ~ing] = ARETE                               # lèvre de la gouttière
    col[(dg >= 0.06) & (dg < 0.12) & ~ing] = OS_SOMBRE
    return col, None, em


# ------------------------------------------------------------------ cubes différés (tuiles partagées par les deux étapes)
TILES = {}
CUBES = []
SPEC_CACHE = {}
SIX = ("north", "south", "east", "west", "up", "down")
XF = [np.zeros(3), np.eye(3)]     # repère local -> modèle des faces échantillonnées en cours


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


def spec(groupe, nom, c, X, Y, s, peintures):
    """Cube dans le repère local (u, v, z) ; faces échantillonnées texel par texel, découpées par l'alpha ; posé par XF."""
    X, Y, Z = repere(X, Y)
    c = np.asarray(c, float)
    if nom not in SPEC_CACHE:
        faces = {}
        for f, fn in peintures.items():
            P = points_face(c, X, Y, Z, s, f)
            col, al, em, m = fn(P)
            if m.any():
                faces[f] = tuile(f"{nom}_{f}", *finir(col, al, em, m))
        SPEC_CACHE[nom] = faces
    faces = SPEC_CACHE[nom]
    if faces:
        T, M = XF
        CUBES.append({"groupe": groupe, "nom": f"{SFX[0]}_{nom}", "c": T + M @ c, "R": M @ np.column_stack([X, Y, Z]),
                      "half": np.asarray(s, float) / 2, "faces": faces})


def volume(pc, groupe):
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

            spec(groupe, f"{pc.nom}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil})
    u = pc.u
    pp_ = np.array((-u[1], u[0]))
    pa = np.array(pc.poly) - pc.O
    s_, t_ = pa @ u, pa @ pp_
    s0, s1, t0, t1 = s_.min() - 0.05, s_.max() + 0.05, t_.min() - 0.05, t_.max() + 0.05
    Pc = pc.O + u * (s0 + s1) / 2 + pp_ * (t0 + t1) / 2
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

        spec(groupe, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, ((s1 - s0) * math.sqrt(1 + pc.k ** 2), t1 - t0, TH), {"south": plat})


def gouttieres(pc, groupe):
    """Gouttières creusées : trou dans les plats (alpha), parois d'os par tronçon et par face, fond au filet vert."""
    for gi, G in enumerate(pc.gouts):
        gp = np.array(G.poly)
        a0, a1 = gp[:, 0].min() - 0.15, gp[:, 0].max() + 0.15
        b0, b1 = gp[:, 1].min() - 0.15, gp[:, 1].max() + 0.15

        def fond(P, G=G):
            P2 = P[..., :2]
            m = in_poly(P2, G.poly) | (d_poly(P2, list(G.poly) + [G.poly[0]]) < 0.1)
            dc = d_poly(P2, G.ax)
            col = np.zeros(P.shape[:-1] + (3,), np.float32) + OS_SOMBRE
            em = np.zeros_like(col)
            col[dc < 0.22] = AURA
            col[dc < 0.16] = VEIN
            col[dc < 0.09] = VCORE
            em[dc < 0.16] = E_VEINE
            em[dc < 0.09] = E_COL
            return col, None, em, m

        spec(groupe, f"{pc.nom}_fond{gi}", ((a0 + a1) / 2, (b0 + b1) / 2, 0.0), (1, 0, 0), (0, 1, 0), (a1 - a0, b1 - b0, 2 * Z_FOND),
             {"south": fond, "north": fond})
        pts_l = G.gl[::2] + ([G.gl[-1]] if (len(G.gl) - 1) % 2 else [])
        pts_r = G.gr[::2] + ([G.gr[-1]] if (len(G.gr) - 1) % 2 else [])
        murs = [(pts[i], pts[i + 1]) for pts in (pts_l, pts_r) for i in range(len(pts) - 1)]
        for j, (p, q) in enumerate(murs):
            p, q = np.asarray(p, float), np.asarray(q, float)
            Ln = float(np.linalg.norm(q - p))
            if Ln < 0.02:
                continue
            d = unit(q - p)
            n = np.array((-d[1], d[0]))
            mid = (p + q) / 2
            if in_poly(np.array([mid + n * 0.03]), G.poly)[0]:
                n = -n
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
                spec(groupe, f"{pc.nom}_paroi{gi}{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.04, top - z0, TH), {face: paroi})


# ------------------------------------------------------------------ tours (pièces rondes, recette de skin_epee_abyssal)
OVL, OVW = 0.04, 0.03
DENS = 16.0


def p_os(xn, t, y, r, L, ex):
    k = np.clip(0.35 + 0.45 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    col = lerp(OS_SOMBRE, OS_CLAIR, k[..., None]) * (1 + 0.06 * np.sin(y * 23 + xn))[..., None]
    col = np.where((np.abs(xn) < 0.22)[..., None], lerp(col, REFLET, 0.45), col)
    return col, None


def p_bague(xn, t, y, r, L, ex):
    k = np.clip(0.4 + 0.5 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    return lerp(OS_BASE, ARETE, k[..., None] * 0.8), None


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


PEINTRES = {"os": p_os, "bague": p_bague, "cuir": p_cuir, "clou": p_clou, "griffe": p_griffe}


def tuile_pan(nom, mat, L, w0, w1, r0, r1, ex):
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


def tour(g, nom, O, ax, ref, profil, n=12, phase=0.0):
    """profil = [(b0, r0, b1, r1, mat, ex), ...] le long de ax depuis O (modèle) ; une couronne de n pans par tronçon."""
    O, ax = np.asarray(O, float), unit(np.asarray(ax, float))
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    for i, (b0, r0, b1, r1, mat, ex) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        if L < 1e-4:
            continue
        tile = tuile_pan(f"{nom}{i}", mat, L, 2 * r0 * tn, 2 * r1 * tn, r0, r1, ex)
        db, dr = (b1 - b0) / L, (r1 - r0) / L
        wm = max(2 * r0 * tn, 2 * r1 * tn) + 2 * OVW
        for k in range(n):
            th = phase + TAU * k / n
            e = math.cos(th) * ref + math.sin(th) * w3
            Pa, Pb = O + b0 * ax + r0 * e, O + b1 * ax + r1 * e
            Y = unit(Pb - Pa)
            N = -dr * ax + db * e
            X = np.cross(Y, N)
            CUBES.append({"groupe": g, "nom": f"{SFX[0]}_{nom}{i}_{k}", "c": (Pa + Pb) / 2 - N * TH / 2, "R": np.column_stack([X, Y, N]),
                          "half": np.array((wm / 2, L / 2 + OVL, TH / 2)), "faces": {"south": tile}})


def barre(g, nom, p, q, r, mat, ref, n=8, cap="os"):
    """Barre octogonale fermée par deux chanfreins (pas d'anneau ouvert)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = float(np.linalg.norm(q - p))
    c = min(0.1, L / 4)
    tour(g, nom, p, q - p, ref, [(0.0, r * 0.55, c, r, cap, {"clair": 0.1}), (c, r, L - c, r, mat, {}),
                                 (L - c, r, L, r * 0.55, cap, {"clair": -0.05}), (L, r * 0.55, L, 0.0, cap, {}),
                                 (0.0, 0.0, 0.0, r * 0.55, cap, {})], n=n, phase=math.pi / n)


def griffe(g, nom, p, X, Y, L, rmax, curve=0.30, nseg=8, n=8):
    """Griffe recourbée en tronçons coniques à 8 pans : part de p vers X, se recourbe vers Y ; pointe verte."""
    p, X = np.asarray(p, float), unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    nz = np.cross(X, Y)
    centre = lambda t: p + X * (L * (t - 0.12 * t * t)) + Y * (curve * L * t ** 2.1)
    ray = lambda t: rmax * (max(0.0, 1 - t) ** 0.8 + 0.06) / 1.06
    for i in range(nseg):
        t0, t1 = i / nseg, (i + 1) / nseg
        a, b = centre(t0), centre(t1)
        prof = [(0.0, ray(t0), float(np.linalg.norm(b - a)), ray(t1) if i < nseg - 1 else 0.0, "griffe", {"t0": t0, "t1": t1})]
        if i == 0:
            prof.insert(0, (-0.3, 0.0, 0.0, ray(0.0), "griffe", {"t0": 0.0, "t1": 0.0}))
        tour(g, f"{nom}{i}_", a, b - a, nz, prof, n=n)


def t_disque(nom, n, Ra, N=48):
    """Face d'os : os marbré, cercle violacé, bord sombre."""
    if nom in TILES:
        return nom
    R = Ra / math.cos(math.pi / n)
    yy, xx = np.mgrid[0:N, 0:N]
    x = ((xx + 0.5) / N - 0.5) * 2 * R
    y = (0.5 - (yy + 0.5) / N) * 2 * R
    th = np.arctan2(y, x)
    sect = np.round(th / (TAU / n)) * (TAU / n)
    apo = x * np.cos(sect) + y * np.sin(sect)
    mask = apo <= Ra
    rr = apo / Ra
    col = lerp(OS_CLAIR, OS_BASE, rr[..., None] ** 1.3) * (1 + 0.05 * np.sin(np.hypot(x, y) * 14))[..., None]
    col[(rr > 0.70) & (rr < 0.80)] = ARETE
    col[rr > 0.92] = OS_SOMBRE
    return tuile(nom, *finir(col, None, None, mask))


def disque(g, nom, c, Nrm, up, n, Ra, tile, phase=0.0):
    Nrm = unit(Nrm)
    up = np.asarray(up, float)
    Y = unit(up - (up @ Nrm) * Nrm)
    X = np.cross(Y, Nrm)
    if phase:
        cph, sph = math.cos(phase), math.sin(phase)
        X, Y = cph * X + sph * Y, -sph * X + cph * Y
    R = Ra / math.cos(math.pi / n)
    CUBES.append({"groupe": g, "nom": f"{SFX[0]}_{nom}", "c": np.asarray(c, float) - Nrm * TH / 2, "R": np.column_stack([X, Y, Nrm]),
                  "half": np.array((R, R, TH / 2)), "faces": {"south": tile}})


# ------------------------------------------------------------------ conception
GROUPES = []        # (clé, pivot, parent) ; nom affiché = clé avant « # »
SFX = ["r"]
Z_Q = ZH + 0.55                   # quille avant
R_Q = 0.62
Z_QD = ZH - 1.0                   # quille du dos
Z_U0 = ZH + 0.25                  # pied de l'umbo
R_U = 2.2


def grp(nom, pivot, parent):
    GROUPES.append((nom, np.asarray(pivot, float), parent))
    return nom


def bg(a0, a1, r_in, r_out):
    return [(a0, r_in, a0 + 0.1, r_out, "bague", {"clair": 0.1}), (a0 + 0.1, r_out, a1 - 0.1, r_out, "bague", {}),
            (a1 - 0.1, r_out, a1, r_in, "bague", {"clair": -0.1})]


def build(sfx, parent):
    """Une copie de l'écu (mêmes tuiles)."""
    SFX[0] = sfx
    O = {}
    # --- les deux demi-écailles
    for cote in ("d", "g"):
        pc = PL[cote]
        T, M = FR[cote]
        XF[0], XF[1] = T, M
        ge = grp(f"ecaille_{cote}_{sfx}", Wa(cote, 3.0 * pc.sg, 0.0), parent)
        volume(pc, ge)
        gouttieres(pc, ge)
    XF[0], XF[1] = np.zeros(3), np.eye(3)
    # --- quille d'os octogonale devant (bagues violacées), griffes en haut et en bas
    gq = grp(f"quille_{sfx}", (0, 0, Z_Q), parent)
    prof = ([(-10.9, 0.0, -10.75, R_Q, "os", {"clair": 0.1})] + bg(-10.75, -10.2, R_Q, 0.78)
            + [(-10.2, R_Q, -6.3, R_Q, "os", {})] + bg(-6.3, -5.85, R_Q, 0.74)
            + [(-5.85, R_Q, -1.4, R_Q, "os", {"y0": 1.0})]
            + [(2.4, R_Q, 6.1, R_Q, "os", {"y0": 2.0})] + bg(6.1, 6.55, R_Q, 0.74)
            + [(6.55, R_Q, 8.5, R_Q, "os", {"y0": 3.0})] + bg(8.5, 9.0, R_Q, 0.8)
            + [(9.0, 0.8, 9.12, 0.0, "os", {"clair": 0.15})])
    tour(gq, "quille", (0, 0, Z_Q), (0, 1, 0), (0, 0, 1), prof, n=8, phase=math.pi / 8)
    O["griffe_haut"] = g_h = grp(f"griffe_haut_{sfx}", (0, 8.9, Z_Q), gq)
    griffe(g_h, "gh", (0, 8.9, Z_Q - 0.05), (0, 1, 0.12), (0, 0, -1), 1.7, 0.5, curve=0.22, nseg=6)
    g_b = grp(f"griffe_bas_{sfx}", (0, -10.6, Z_Q - 0.2), gq)
    griffe(g_b, "gb", (0, -10.6, Z_Q - 0.25), (0, -1, -0.05), (0, 0, 1), 2.1, 0.6, curve=0.12, nseg=6)
    # --- quille du dos
    gd = grp(f"dos_{sfx}", (0, 0, -2.0), parent)
    barre(gd, "quille_dos", (0, -10.4, Z_QD), (0, 8.4, Z_QD), 0.46, "os", (1, 0, 0))
    # traverses d'os (dos des deux moitiés), bagues violacées aux bouts
    for cote in ("d", "g"):
        pc = PL[cote]
        for k, (vb, ue) in enumerate(((6.2, 5.4), (-4.2, 4.6))):
            p = Wa(cote, pc.sg * 0.3, vb, -(float(pc.h(np.array((0.3 * pc.sg, vb)))) + 0.2))
            q = Wa(cote, pc.sg * ue, vb, -(float(pc.h(np.array((ue * pc.sg, vb)))) + 0.2))
            barre(gd, f"traverse_{cote}{k}", p, q, 0.34, "os", FR[cote][1][:, 2], cap="bague")
    # montants et poignée de cuir (place de la poignée vanilla : x -1..1, y -3..3, z -5..1)
    for k, yp in enumerate((3.15, -3.15)):
        barre(gd, f"montant{k}", (0, yp, Z_QD + 0.1), (0, yp, -4.75), 0.42, "os", (1, 0, 0), cap="bague")
    tour(gd, "poignee", (0, -3.0, -4.2), (0, 1, 0), (0, 0, 1),
         [(0.0, 0.58, 6.0, 0.58, "cuir", {})], n=8, phase=math.pi / 8)
    for k, yp in enumerate((-2.85, 2.85)):
        barre(gd, f"bague_p{k}", (0, yp - 0.2, -4.2), (0, yp + 0.2, -4.2), 0.68, "bague", (0, 0, 1), cap="bague")
    for k, yp in enumerate((-1.5, 0.0, 1.5)):
        barre(gd, f"clou{k}", (0, yp, -4.2 - 0.78), (0, yp, -4.2 + 0.78), 0.2, "clou", (0, 1, 0), cap="clou")
    # --- umbo : collet d'os octogonal (bague, collet, gradin), couvercle cerclé de violet, griffe conique à pointe verte
    O["umbo"] = gu = grp(f"umbo_{sfx}", (UMBO[0], UMBO[1], Z_U0), parent)
    U0 = np.array((UMBO[0], UMBO[1], Z_U0))
    tour(gu, "umbo", U0, (0, 0, 1), (0, 1, 0),
         [(0.0, R_U - 0.1, 0.16, R_U, "bague", {"clair": 0.1}), (0.16, R_U, 0.62, R_U - 0.3, "os", {"clair": 0.08}),
          (0.62, R_U - 0.3, 0.8, 1.55, "bague", {}), (0.8, 1.55, 1.2, 1.38, "os", {"clair": 0.12})], n=8, phase=math.pi / 8)
    td = t_disque("disque_umbo", 8, 1.38)
    disque(gu, "couvercle", U0 + np.array((0, 0, 1.2)), (0, 0, 1), (0, 1, 0), 8, 1.38, td, phase=math.pi / 8)
    O["pointe"] = gp = grp(f"pointe_umbo_{sfx}", U0 + np.array((0, 0, 1.1)), gu)
    griffe(gp, "pu", U0 + np.array((0, 0, 1.05)), (0, 0.18, 1), (0, 1, 0), 2.4, 0.92, curve=0.16, nseg=7)
    # --- cornes en crochet aux épaules (montent, puis se recourbent vers la quille)
    O["cornes"] = []
    for cote in ("d", "g"):
        pc = PL[cote]
        base = Wa(cote, pc.sg * (EPAULE[0] - 0.25), EPAULE[1] - 0.45, 0.0)
        gc = grp(f"corne_{cote}_{sfx}", base, parent)
        griffe(gc, f"co{cote}", base, (0.42 * pc.sg, 0.9, -0.12), (-pc.sg, 0.25, 0), 3.6, 0.72, curve=0.38, nseg=8)
        O["cornes"].append((gc, pc.sg))
    O["ctrl"] = grp(f"ctrl_lumiere#{sfx}", (0, 0, ZH), parent)
    return O


racine_r = grp(objet.etape("repos", "bouclier"), (0, 0, 0), None)
OR_ = build("r", racine_r)
racine_b = grp(objet.etape("bloque", "bouclier"), (0, 0, 0), None)
pose = grp("pose_bloque", (0, 0, 0), racine_b)
OB_ = build("b", pose)


# ------------------------------------------------------------------ atlas
def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    print("aire des tuiles", sum(a.shape[0] * a.shape[1] for a, _ in TILES.values()), "max", max(a.shape[:2] for a, _ in TILES.values()))
    # rangement en ligne d'horizon (skyline, bas-gauche) : des rangées perdaient trop de place
    sky = np.zeros(TEX, int)
    for n, (im, ime) in sorted(TILES.items(), key=lambda it: (-it[1][0].shape[0], -it[1][0].shape[1])):
        h, w = im.shape[:2]
        best = None
        for x0 in range(0, TEX - w):
            yb = int(sky[x0:x0 + w + 1].max())
            if best is None or yb < best[0]:
                best = (yb, x0)
        y, x = best
        assert y + h <= TEX - 6, f"atlas plein ({n}, y = {y})"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None:
            tex_e[y:y + h, x:x + w] = ime
        sky[x:x + w + 1] = y + h + 1
    shelf = 0
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
    """Angles (X, Y, Z) tels que R = Rz Ry Rx ; blocage de cardan (Y = ±90°) : tout l'angle sur X."""
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
    assert nom not in groups and len(nom.split("#")[0]) <= 64, nom
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
    return {"name": name.split("#")[0], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node(racine_r), bone_node(racine_b)]

# ------------------------------------------------------------------ réglages Display (item/shield.json et item/shield_blocking.json du jar 26.1.2)
VAN = {"thirdperson_righthand": ((0, 90, 0), (10, 6, -4), 1), "thirdperson_lefthand": ((0, 90, 0), (10, 6, 12), 1),
       "firstperson_righthand": ((0, 180, 5), (-10, 1.75, -10), 1.25), "firstperson_lefthand": ((0, 180, 5), (10, 0, -10), 1.25),
       "gui": ((15, -25, -5), (2, float(os.environ.get("GUI_TY", "2.3")), 0), GUI), "fixed": ((0, 180, 0), (-4.5, 4.5, -5), 0.55), "on_shelf": ((0, 0, 0), (11, 18.5, 8.7), 1.4),
       "ground": ((0, 0, 0), (2, 4, 2), 0.25)}
VAN_BLOQUE = {"thirdperson_righthand": ((45, 155, 0), (-3.49, 11, -2), 1), "thirdperson_lefthand": ((45, 155, 0), (11.51, 7, 2.5), 1),
              "firstperson_righthand": ((0, 180, -5), (-15, 3.25, -11), 1.25), "firstperson_lefthand": ((0, 180, -5), (5, 5, -11), 1.25)}
AFFICHAGE = objet.affichage("bouclier", **{c: {"rotation": list(r), "translation": list(t), "scale": [s] * 3} for c, (r, t, s) in VAN.items()})


def disp(v, gauche):
    """Display appliqué comme ItemTransform.apply : main gauche = rotation Y, Z et translation X inversées."""
    r, t, s = v
    r, t = list(r), list(t)
    if gauche:
        r[1], r[2], t[0] = -r[1], -r[2], -t[0]
    return objet.matrice_display({"rotation": r, "translation": t, "scale": [s] * 3})


CORR = {}
ERR_POSE = 0.0
for c in VAN_BLOQUE:
    gauche = c.endswith("lefthand")
    Hm = np.linalg.inv(disp(VAN[c], gauche)) @ disp(VAN_BLOQUE[c], gauche)
    Rm = Hm[:3, :3]
    assert np.allclose(Rm @ Rm.T, np.eye(3), atol=1e-6)
    CORR[c] = (euler(Rm), Hm[:3, 3])
    e, t = CORR[c]
    for p in ((0, 0, 1.5), (6, 10, 2), (-6, -11, 1), (0, 3, -5), (0, 0.5, 6.0), (7.5, 13, 1)):
        a = disp(VAN[c], gauche) @ np.append(rotm(*e) @ np.array(p, float) + t, 1)
        b = disp(VAN_BLOQUE[c], gauche) @ np.append(np.array(p, float), 1)
        ERR_POSE = max(ERR_POSE, float(np.linalg.norm(a[:3] - b[:3])) * 16)
        assert np.allclose(a, b, atol=1e-6), c
    print(f"parade {c:23s} rotation {np.round(e, 2).tolist()} position {np.round(t, 3).tolist()}")
print(f"pose de blocage : écart max (matrices) {ERR_POSE:.5f} px")


def molang_combo(i, chan):
    v = {c: (CORR[c][0][i] if chan == "rot" else CORR[c][1][i]) for c in CORR}
    f = lambda x: f"({x:.3f})"
    return (f"q.in_first_person*(q.hand*{f(v['firstperson_lefthand'])}+(1-q.hand)*{f(v['firstperson_righthand'])})"
            f"+(1-q.in_first_person)*(q.hand*{f(v['thirdperson_lefthand'])}+(1-q.hand)*{f(v['thirdperson_righthand'])})")


# ------------------------------------------------------------------ animations (objet vivant, guide 14)
def s_(v):
    return v if isinstance(v, str) else f"{v + 0.0:.4f}".rstrip("0").rstrip(".")


def kf(ch, t, x, y=None, z=None, interp="linear"):
    y = x if y is None else y
    z = x if z is None else z
    return {"channel": ch, "data_points": [{"x": s_(x), "y": s_(y), "z": s_(z)}], "time": round(t, 4), "interpolation": interp}


def lum(t, x):
    return kf("position", t, x, 0, 0)


def anim(name, length, loop="once"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 100,
            "selected": name == "item_idle", "animators": {}}


def piste(an, g, keys):
    u = groups[g]["uuid"]
    if u in an["animators"]:
        an["animators"][u]["keyframes"] += keys
    else:
        an["animators"][u] = {"name": g.split("#")[0], "type": "bone", "keyframes": keys}


def chk(e):
    assert len(e) <= 512 and e.count(";") <= 16, (len(e), e)
    return e


def echant(L, n):
    return [round(L * i / n, 4) for i in range(n + 1)]


def corne(t, sg, ang):
    """Corne du côté sg ouverte de `ang` degrés (rotation autour de z ; + = la pointe s'écarte de la quille)."""
    return kf("rotation", t, 0, 0, -sg * ang)


rot_m = [chk(molang_combo(i, "rot")) for i in range(3)]
pos_m = [chk(molang_combo(i, "pos")) for i in range(3)]


def garde(an, L):
    piste(an, pose, [kf("rotation", 0, *rot_m), kf("rotation", L, *rot_m), kf("position", 0, *pos_m), kf("position", L, *pos_m)])


# item_idle (6 s) : garde (recette 2), cornes qui respirent à contretemps, veines qui soufflent
L_IDLE = 6.0
idle = anim("item_idle", L_IDLE, "loop")
garde(idle, L_IDLE)
for O in (OR_, OB_):
    for j, (g, sg) in enumerate(O["cornes"]):
        piste(idle, g, [corne(t, sg, 2.5 * math.sin(TAU * (t / L_IDLE - 0.5 * j))) for t in echant(L_IDLE, 24)])
    piste(idle, O["ctrl"], [lum(t, 0.3 * math.sin(TAU * 2 * t / L_IDLE)) for t in echant(L_IDLE, 24)])

# item_use (1,2 s) : garde, cornes dressées qui frémissent, veines plus vives, éclat quand un coup touche le porteur
L_USE = 1.2
use = anim("item_use", L_USE, "loop")
garde(use, L_USE)
for O in (OR_, OB_):
    for j, (g, sg) in enumerate(O["cornes"]):
        piste(use, g, [corne(t, sg, 7.0 + 1.0 * math.sin(TAU * 3 * t / L_USE + 1.7 * j)) for t in echant(L_USE, 24)])
    piste(use, O["ctrl"], [lum(0, chk("0.5+0.25*math.sin(q.life_time*300)+1.1*q.hit_by_entity"))])

# event_select (0,7 s) : la griffe de l'umbo sort du collet (seul groupe déplié par scale), puis les cornes se déplient
L_SEL = 0.7
sel = anim("event_select", L_SEL)
piste(sel, OR_["pointe"], [kf("scale", t, 0.25 + 0.75 * sm(t, 0.0, 0.3) + 0.06 * bump(t, 0.24, 0.3, 0.34, 0.48)) for t in echant(L_SEL, 21)])
for O in (OR_, OB_):
    for j, (g, sg) in enumerate(O["cornes"]):
        piste(sel, g, [corne(t, sg, -24 * (1 - sm(t, 0.2 + 0.07 * j, 0.5 + 0.07 * j))) for t in echant(L_SEL, 21)])
    piste(sel, O["ctrl"], [lum(t, -1 + sm(t, 0.3, 0.45) + 0.8 * bump(t, 0.42, 0.5, 0.54, 0.7)) for t in echant(L_SEL, 21)])

# event_hit (0,5 s) : éclat des veines, cornes qui frissonnent ; le seul son (block.sculk.break à 0,04 s)
L_HIT = 0.5
hit = anim("event_hit", L_HIT)
for O in (OR_, OB_):
    for j, (g, sg) in enumerate(O["cornes"]):
        piste(hit, g, [corne(t, sg, 4 * math.sin(TAU * 3 * t / 0.3 + j) * (1 - sm(t, 0.0, 0.32))) for t in echant(L_HIT, 20)])
    piste(hit, O["ctrl"], [lum(t, 1.5 * (sm(t, 0.0, 0.03) * (1 - sm(t, 0.06, 0.46)))) for t in echant(L_HIT, 20)])

ANIMS = [idle, use, sel, hit]

# ------------------------------------------------------------------ écriture
assert len(elements) <= 8192, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = objet.modele(NOM, "bouclier", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son
limiter_sons(model)
# Un seul son, au coup qui touche (event_hit), à 0,04 s ; rien à event_use_start ni event_enter_* (recette 3).
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "block.sculk.break")]}
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
print(f"boîte {P.min(0).round(2)} .. {P.max(0).round(2)}")
pc = PL["d"]
gm = min(float(pc.h(np.array([p]))[0] - Z_FOND) for G in pc.gouts for p in G.ax)
marge = min(float(pc.dE(np.array([p]))[0] - pc.wb(np.array([p]))[0]) for G in pc.gouts for p in G.gl + G.gr)
print(f"écaille : {2 * H_RAC:.2f} px à la quille -> {2 * float(pc.h(np.array((pc.L, 0)))):.2f} au bord ; "
      f"profondeur mini de gouttière {gm:.2f} px, marge gouttière/biseau {marge:.2f} px")
