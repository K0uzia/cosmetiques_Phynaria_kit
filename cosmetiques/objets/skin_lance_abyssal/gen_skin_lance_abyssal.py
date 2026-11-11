"""Dard de l'Abysse : skin d'objet (guide 14) pour toutes les lances du joueur, ensemble Abyssal (thème Démoniaque).
Design original. Écrit skin_lance_abyssal.png, skin_lance_abyssal_e.png et .build/skin_lance_abyssal_brut.bbmodel.
Point de départ : gen_skin_houe_abyssal.py (classe Fer opaque du set, tours, griffes, peintures, animations) ; repère,
longueur, prise et display_vanilla() de skin_lance_orage (validés en jeu le 2026-11-05, recopiés de skin_lance_givre).

Référence réelle (.claude/references/objets/lances.md) : lance à ailes / à sanglier (fer en feuille à deux tranchants sur une
douille, deux ailettes derrière le fer qui retiennent la proie). Ici un **dard** : fer d'os charbon en feuille large
(épaule à 3,9 px), long effilement, **deux fils verts** ; les ailettes deviennent des **barbes de harpon** en griffes
recourbées vers la hampe, nées d'un collet d'os octogonal (bossette conique à pointe verte sur chaque face). Distinct de
l'épée (sabre courbe à un fil), des outils du set (fers en travers) et des lances Orage (cristal) et Givre (losange de glace).
- fer = une plaque biseautée fermée (recette .claude/references/objets/volume-3d.md) : section hexagonale creusée, plat
  incliné 1,60 -> 0,54 px, pente unique 40°, tous les bords biseautés sauf la racine (dans le collet) ; **vert seulement au
  fil** (fil vif + _e, bande verte, halo sombre, veines qui montent du fil), os nu à liseré violacé près du collet ;
  **gouttière creusée** dans l'axe (fuseau, filet vert + _e couché au fond) ;
- hampe d'os à 12 pans, bagues d'os violacées, poignée de cuir pourpre-noir en spirale à trois clous d'os pâle, douille
  conique ; griffe au talon (pointe verte).
Pas de métal, d'or ni de rouge. Une seule étape (`repos`), repère fixe (pas de recentrage), Display de la lance Orage.

Objet vivant (guide 14), sobre :
- item_idle (6 s) : les barbes respirent à contretemps (±3°), le fil souffle (ctrl_lumiere ±0,35) ;
- item_use (1,6 s, lance levée pour la charge) : barbes écartées de 20° qui frémissent, petites barbes des plats aussi, fil
  plus vif ; q.use_progress non utilisé (valeur inconnue pour une lance) ;
- event_use_start (0,4 s) : les barbes se hérissent (échelle du groupe parent `barbes`), fil qui s'allume ; **aucun son** ;
- event_select (0,7 s) : le dard sort du collet (échelle de `fer`), les barbes se déplient depuis la hampe ;
- event_swing (0,3 s) : l'estoc (la lance pousse de 0,7 px dans son axe), le fil s'avive ;
- event_hit (0,6 s) : éclat du fil (+1,6), barbes qui frissonnent ; **le seul son** (block.sculk.break à 0,04 s).
Un seul groupe déplié par `scale` par animation. Pas de particules, pas d'item_gui, item_ground repli sur item_idle.
Fonctions avancées : calque _e (fils, veines, gouttière, pointes), ctrl_lumiere (non simulé par le renderer), scale et
position animés, animations d'objet (non simulées par l'aperçu). À juger en jeu : lecture du dard dans la case et en main,
item_use / event_use_start pendant la charge, event_hit et le son, ctrl_lumiere sur un objet.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

NOM = "skin_lance_abyssal"
TEX = 512
TAU = 2 * math.pi
AVEC_E = True
GUI = float(os.environ.get("GUI", "0.6"))    # échelle de l'inventaire (celle des lances Orage et Givre)

# Repère (catégorie objets) : lance pointe vers +Y, centrée ; a le long de la hampe (-> +Y), b en travers (-> -X), z (-> +Z).
# Même longueur et même prise que skin_lance_orage (réglages Display validés en jeu le 2026-11-05) : pas de recentrage.
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


# ------------------------------------------------------------------ dessin du fer (plan a, b ; px) : contour de la version précédente
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

def bez(P, s):
    P = [np.array(p, float) for p in P]
    u = 1 - s
    c = u ** 3 * P[0] + 3 * u * u * s * P[1] + 3 * u * s * s * P[2] + s ** 3 * P[3]
    d = 3 * u * u * (P[1] - P[0]) + 6 * u * s * (P[2] - P[1]) + 3 * s * s * (P[3] - P[2])
    return c, d / np.linalg.norm(d)


# ------------------------------------------------------------------ fer de la lance (plan a, b ; px)
# Dard : fer d'os en feuille large (épaule à 15 px, 3,9 px de large), long effilement jusqu'à la pointe ; les deux bords
# sont des fils (vert), la racine est cachée dans le collet. Section hexagonale creusée (plats + biseaux, gouttière).
A_O = 12.9                       # centre du collet d'os (axe z) où naît le fer
R_COL = 1.25                     # apothème du collet (octogone)
Z_COL = 0.88                     # demi-épaisseur du collet
A_R = 12.5                       # racine du fer (cachée dans le collet)
O_ = np.array((A_R, 0.0))
A_FIL = 13.0                     # en deçà, le bord est dans le collet : pas de biseau
HAUT = catmull([(A_R - 0.3, 0.55), (13.4, 0.82), (14.3, 1.62), (15.0, 1.95), (15.8, 1.90), (17.2, 1.45), (19.0, 0.86),
                (20.6, 0.34), (A_MAX, 0.0)], 6)


def hw_fer(a):
    return float(np.interp(a, HAUT[:, 0], HAUT[:, 1]))



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


# ------------------------------------------------------------------ vrai volume (os plein, opaque)
Z_E = 0.10                       # demi-épaisseur au fil
T_BIS = 0.85                     # pente unique des biseaux (40°) : fer large, il reste un grand plat pour la gouttière
TH = 0.3
DF = 16.0
RECOUV = 0.08
AL = math.atan(T_BIS)
Z_FOND = 0.16                    # fond de la gouttière


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


class Fer:
    """Plaque biseautée fermée (repère de la lame, u, w) : contour poly, fils (polyligne sans la racine cachée dans la bague),
    plat z = h0 + k (P - O)·u ; tranchant = `tranchant` (le vert ne vit que là) ; gouttière en fuseau dans l'axe."""

    def __init__(self, nom, poly, fil, tranchant, nus, flanc, u, h_racine, h_bout, g0, g1, gw):
        self.nom, self.poly = nom, poly
        self.u = unit(u)
        pa = np.array(poly) - O_
        s_ = pa @ self.u
        self.L = float(s_.max())
        s_r = 0.6
        self.k = (h_bout - h_racine) / (self.L - s_r)
        self.h0 = h_racine - self.k * s_r
        self.segs = subdiv(fil)
        self.tranchant, self.nus = tranchant, nus
        # gouttière dans l'axe (le canal de la dent) : fuseau pointu aux deux bouts
        ax, gl, gr = [], [], []
        for j in range(17):
            v = j / 16
            a = g0 + (g1 - g0) * v
            w = gw * math.sin(math.pi * v) ** 0.6 + 0.012
            ax.append((a, 0.0))
            gl.append((a, w))
            gr.append((a, -w))
        self.gax, self.gl, self.gr = ax, gl, gr
        self.gpoly = gl + gr[::-1]
        # reflets violacés : une ligne au milieu de chaque pan, entre la gouttière et le fil
        self.centres = flanc
        # veines : partent du fil et montent vers la racine, en se ramifiant un peu
        Tr = np.array(resample(tranchant, 0.05))
        ls = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(Tr, axis=0), axis=1))])
        self.veines = []
        for j, (t, pente, fr, br) in enumerate(((0.10, 0.30, 0.80, 0.5), (0.22, -0.25, 0.95, 0.0), (0.34, 0.20, 0.85, 0.45),
                                                (0.66, -0.20, 0.85, 0.45), (0.78, 0.25, 0.95, 0.0), (0.90, -0.30, 0.80, 0.5))):
            i = min(max(int(np.searchsorted(ls, t * ls[-1])), 1), len(Tr) - 2)
            d = unit(Tr[i + 1] - Tr[i - 1])
            n = normale_dedans(poly, Tr[i], d)
            st = Tr[i] + n * 0.02
            ln = min(1.45 * fr, 0.8 * abs(float(st[1])))
            pts = [st]
            for kk in (1, 2, 3, 4):
                ang = pente * (1 - 0.35 * kk) + 0.22 * math.sin(kk * 2.3 + j)
                q = pts[-1] + (n * math.cos(ang) + d * math.sin(ang)) * ln / 4
                pts.append(q)
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
        """0 à la racine -> 1 au fil."""
        return np.clip(((np.asarray(P, float) - O_) @ self.u) / self.L, 0, 1)

    def actif(self, P):
        """Les deux bords sont des fils (vert) ; près du collet, l'os reste nu (liseré violacé)."""
        return smv(np.asarray(P, float)[..., 0], A_FIL + 0.6, A_FIL + 1.3)

    def in_g(self, P):
        return in_poly(P, self.gpoly)

    def d_g(self, P):
        return d_poly(P, list(self.gpoly) + [self.gpoly[0]])

    def d_ax(self, P):
        return d_poly(P, self.gax)

    def d_veine(self, P):
        return np.min(np.stack([d_poly(P, v) for v in self.veines]), axis=0)


_H = resample(HAUT, 0.8)
_B = [(a, -b) for a, b in _H[::-1]]
POLY = _H + _B[1:]                                # fermé par la racine (a = A_R - 0,3, dans le collet)
_i0 = next(i for i, p in enumerate(_H) if p[0] >= A_FIL) - 1
FIL_FER = _H[_i0:] + _B[1:len(_B) - _i0]
G0, G1, GW = 13.5, 19.6, 0.30                     # gouttière dans l'axe (le canal du dard)
CENTRES = [[(a, sg * 0.5 * (GW * math.sin(math.pi * (a - G0) / (G1 - G0)) ** 0.6 + hw_fer(a))) for a in np.linspace(14.2, 18.6, 12)]
           for sg in (1, -1)]
FER = Fer("fer", POLY, FIL_FER, FIL_FER, None, CENTRES, (1.0, 0.0), 0.80, 0.27, G0, G1, GW)

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
    # bandes du fil (vert vif, bande verte, halo sombre) proportionnelles à k : rien au dos ni à la gorge
    fil_f, bande_f, halo_f = 0.16 * k, 0.34 * k, 0.56 * k
    au = (f >= bande_f) & (f < halo_f)
    col[au] = lerp(AURA, col[au], np.clip((f[au] - bande_f[au]) / np.maximum(halo_f[au] - bande_f[au], 1e-3), 0, 1)[..., None])
    col[(f >= fil_f) & (f < bande_f)] = VEIN
    col, em = veines(pc, P2, col, em)
    col[f >= 0.90] = ARETE * 0.9                                  # arête violacée entre le biseau sombre et le plat
    nu = (f < 0.14) & (k < 0.3)                                   # dos et gorge : os nu à liseré violacé
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
    col = lerp(OS_BASE, OS_CLAIR, np.clip(0.45 + 0.6 * nz, 0, 1)[..., None] * 0.85)
    col = col * (1 + 0.05 * np.sin(pc.s(P2) * 38.0 + nz * 2))[..., None]        # stries de croissance de l'os, parallèles au fil
    col = col * (1 - 0.22 * np.clip(1 - (P2[..., 0] - A_R - 1.0) / 1.6, 0, 1))[..., None]    # plus sombre vers le collet
    dc = np.minimum(*[d_poly(P2, c) for c in pc.centres])
    col = lerp(col, REFLET, (np.clip(1 - dc / 0.5, 0, 1) * 0.35)[..., None])    # reflet violacé au milieu du pan
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
    """Cube dans le plan (a, b, z) ; chaque face peinte est échantillonnée texel par texel et découpée par l'alpha."""
    X, Y, Z = repere(X, Y)
    c = np.asarray(c, float)
    faces = {}
    for f, fn in peintures.items():
        P = points_face(c, X, Y, Z, s, f)
        col, al, em, m = fn(P)
        if m.any():
            faces[f] = tuile(f"{nom}_{f}", *finir(col, al, em, m))
    if faces:
        P_, V_ = Wp, Wv
        CUBES.append({"groupe": groupe, "nom": nom, "c": P_(*c), "R": np.column_stack([V_(*X), V_(*Y), V_(*Z)]),
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

        spec(groupe, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, ((s1 - s0) * math.sqrt(1 + pc.k ** 2), t1 - t0, TH), {"south": plat})


def gouttiere(pc, groupe):
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
        col[dc < 0.15] = AURA
        col[dc < 0.10] = VEIN
        col[dc < 0.05] = VCORE
        em[dc < 0.10] = E_VEINE
        em[dc < 0.05] = E_COL
        return col, None, em, m

    spec(groupe, f"{pc.nom}_fond", ((a0 + a1) / 2, (b0 + b1) / 2, 0.0), (1, 0, 0), (0, 1, 0), (a1 - a0, b1 - b0, 2 * Z_FOND),
         {"south": fond, "north": fond})
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
            spec(groupe, f"{pc.nom}_paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


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


def tour(g, nom, O, ax, ref, profil, n=12, phase=0.0):
    """profil = [(b0, r0, b1, r1, mat, ex), ...] le long de ax depuis O (monde) ; une couronne de n pans par tronçon."""
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
            CUBES.append({"groupe": g, "nom": f"{nom}{i}_{k}", "c": (Pa + Pb) / 2 - N * TH / 2, "R": np.column_stack([X, Y, N]),
                          "half": np.array((wm / 2, L / 2 + OVL, TH / 2)), "faces": {"south": tile}})


def griffe(g, nom, p, X, Y, L, rmax, curve=0.30, nseg=8, n=8):
    """Griffe recourbée en tronçons coniques à 8 pans : part de p (monde) vers X, se recourbe vers Y ; pointe verte."""
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
        if i == 0:                                   # bouchon conique : la racine n'est jamais un anneau ouvert
            prof.insert(0, (-0.3, 0.0, 0.0, ray(0.0), "griffe", {"t0": 0.0, "t1": 0.0}))
        tour(g, f"{nom}{i}_", a, b - a, nz, prof, n=n)


def t_disque(nom, n, Ra, N=48):
    """Face d'os : os marbré, cercle violacé, bord sombre."""
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
    Y = unit(up - (up @ Nrm) * Nrm)
    X = np.cross(Y, Nrm)
    if phase:
        cph, sph = math.cos(phase), math.sin(phase)
        X, Y = cph * X + sph * Y, -sph * X + cph * Y
    R = Ra / math.cos(math.pi / n)
    CUBES.append({"groupe": g, "nom": nom, "c": np.asarray(c, float) - Nrm * TH / 2, "R": np.column_stack([X, Y, Nrm]),
                  "half": np.array((R, R, TH / 2)), "faces": {"south": tile}})


# ------------------------------------------------------------------ conception
GROUPES = []        # (nom, pivot, parent)
CTRL = "ctrl_lumiere"


def grp(nom, pivot, parent):
    GROUPES.append((nom, np.asarray(pivot, float), parent))
    return nom


OUT = {}
# barbes de harpon nées du collet : (côté b, longueur, rayon, courbure) ; deux petites sur les plats (±z) pour le volume
BARBES = ((1, 2.75, 0.50, 0.40), (-1, 2.75, 0.50, 0.40))
BARBES_Z = ((1, 1.45, 0.34, 0.30), (-1, 1.45, 0.34, 0.30))


def conception():
    racine = grp(objet.etape("repos", "lance"), Wp(0), None)
    lance = grp("lance", Wp(0), racine)                  # pivot dans la main : l'estoc
    # --- hampe d'os octogonale (12 pans), bagues d'os violacées, poignée de cuir pourpre-noir en spirale, douille conique
    manche = grp("manche", Wp(0), lance)

    def bg(a0, a1, r_in, r_out):
        return [(a0, r_in, a0 + 0.12, r_out, "bague", {"clair": 0.1}), (a0 + 0.12, r_out, a1 - 0.12, r_out, "bague", {}),
                (a1 - 0.12, r_out, a1, r_in, "bague", {"clair": -0.1})]
    R_H = 0.50
    prof = ([(-9.75, 0.0, -9.6, 0.58, "os", {"clair": 0.1})] + bg(-9.6, -8.9, 0.58, 0.74)
            + [(-8.9, R_H, -6.4, R_H, "os", {})] + bg(-6.4, -5.95, R_H, 0.64)
            + [(-5.95, R_H, -3.05, R_H, "os", {"y0": 2.0})] + bg(-3.05, -2.55, R_H, 0.78)
            + [(-2.55, 0.64, 2.55, 0.64, "cuir", {})] + bg(2.55, 3.05, R_H, 0.78)
            + [(3.05, R_H, 6.6, R_H, "os", {"y0": 1.0})] + bg(6.6, 7.05, R_H, 0.64)
            + [(7.05, R_H, 10.6, R_H, "os", {"y0": 3.0})] + bg(10.6, 11.05, R_H, 0.70)
            + [(11.05, 0.56, 12.0, 0.86, "os", {"clair": 0.08}), (12.0, 0.86, 12.2, 0.86, "bague", {})])
    tour(manche, "hampe", Wp(0), A_, T_, prof, n=12)
    for k, a in enumerate((-1.7, 0.0, 1.7)):
        ax_ = T_ if k != 1 else W_
        tour(manche, f"clou{k}_", Wp(a) - ax_ * 0.82, ax_, A_, [(0.0, 0.0, 0.14, 0.24, "clou", {}), (0.14, 0.24, 1.5, 0.24, "clou", {}),
                                                              (1.5, 0.24, 1.64, 0.0, "clou", {})], n=8, phase=math.pi / 8)
    # griffe du talon : croc d'os qui prolonge la hampe, un peu recourbé, pointe verte (plante la lance au sol)
    talon = grp("griffe_talon", Wp(-9.6), lance)
    griffe(talon, "gt", Wp(-9.6), -A_, W_, -A_MIN - 9.6 + 0.05, 0.46, curve=0.10, nseg=7)
    # --- tête : collet d'os octogonal (axe z) cerclé de violet, bossette conique à pointe verte sur chaque face
    tete = grp("tete", Wp(A_O), lance)
    grp(CTRL, Wp(A_O), tete)
    tour(tete, "collet", Wp(A_O, 0, -Z_COL), T_, A_,
         [(0.0, R_COL - 0.2, 0.16, R_COL, "bague", {"clair": 0.12}), (0.16, R_COL, 2 * Z_COL - 0.16, R_COL, "os", {"clair": 0.05}),
          (2 * Z_COL - 0.16, R_COL, 2 * Z_COL, R_COL - 0.2, "bague", {"clair": -0.05})], n=8, phase=math.pi / 8)
    td = t_disque("disque_collet", 8, R_COL - 0.2)
    OUT["bossettes"] = []
    for s in (1, -1):
        cs = "e" if s > 0 else "i"
        disque(tete, f"couvercle_{cs}", Wp(A_O, 0, s * Z_COL), T_ * s, A_, 8, R_COL - 0.2, td, phase=math.pi / 8)
        g = grp(f"bossette_{cs}", Wp(A_O, 0, s * Z_COL), tete)
        griffe(g, f"bo{cs}", Wp(A_O, 0, s * (Z_COL - 0.05)), T_ * s, A_, 0.75, 0.36, curve=0.0, nseg=4)
        OUT["bossettes"].append(g)
    # barbes de harpon (les ailettes d'une lance à ailes, en griffes) : elles partent du collet vers l'extérieur et se
    # recourbent vers la hampe ; groupe parent `barbes` (déplié à event_use_start), une barbe par groupe (respire, s'ouvre)
    barbes = grp("barbes", Wp(A_O), tete)
    OUT["barbes"], OUT["barbes_z"] = [], []
    for s, L, rm, cu in BARBES:
        base = Wp(A_O - 0.15, s * (R_COL - 0.35))
        g = grp(f"barbe_{'gd'[s < 0]}", base, barbes)
        griffe(g, f"ba{'gd'[s < 0]}", base, Wv(-0.42, s * 0.91), Wv(-1, 0), L, rm, curve=cu, nseg=8)
        OUT["barbes"].append((g, s))
    for s, L, rm, cu in BARBES_Z:
        base = Wp(A_O - 0.35, 0, s * (Z_COL - 0.3))
        g = grp(f"barbe_{'eo'[s < 0]}", base, barbes)
        griffe(g, f"bz{'eo'[s < 0]}", base, Wv(-0.5, 0, s * 0.87), Wv(-1, 0), L, rm, curve=cu, nseg=6)
        OUT["barbes_z"].append((g, s))
    # --- fer : dard d'os plein en vrai volume ; pivot à la racine (il sort du collet à event_select)
    fer = grp("fer", Wp(A_R), tete)
    volume(FER, fer)
    gouttiere(FER, fer)
    OUT.update(racine=racine, lance=lance, tete=tete, fer=fer, barbes_grp=barbes, talon=talon)
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


def s_(v):
    return v if isinstance(v, str) else f"{v + 0.0:.4f}".rstrip("0").rstrip(".")


def kf(ch, t, x, y=None, z=None, interp="linear"):
    y = x if y is None else y
    z = x if z is None else z
    return {"channel": ch, "data_points": [{"x": s_(x), "y": s_(y), "z": s_(z)}], "time": round(t, 4), "interpolation": interp}


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


BA = OUT["barbes"]
BZ = OUT["barbes_z"]


def ouvre(s):
    """Signe de rotation (axe z) qui écarte de la hampe la barbe du côté s (côté +b = -X du modèle)."""
    return -s


# item_idle (6 s) : les barbes respirent à contretemps (±3°), le fil souffle (ctrl_lumiere ±0,35).
L_IDLE = 6.0
idle = anim("item_idle", L_IDLE, "loop")
for j, (g, s) in enumerate(BA):
    piste(idle, g, [rot(t, ouvre(s) * 3.0 * math.sin(TAU * (t / L_IDLE - 0.5 * j))) for t in echant(L_IDLE, 24)])
piste(idle, CTRL, [lum(t, 0.35 * math.sin(TAU * 2 * t / L_IDLE)) for t in echant(L_IDLE, 24)])

# item_use (lance levée pour la charge, 1,6 s en boucle) : les barbes s'écartent (+20°) et frémissent, le fil brûle plus fort.
L_USE = 1.6
use = anim("item_use", L_USE, "loop")
for j, (g, s) in enumerate(BA):
    piste(use, g, [rot(t, ouvre(s) * (20.0 + 1.5 * math.sin(TAU * 4 * t / L_USE + j * 1.7))) for t in echant(L_USE, 32)])
for j, (g, s) in enumerate(BZ):
    piste(use, g, [kf("rotation", t, -s * (14.0 + 1.0 * math.sin(TAU * 4 * t / L_USE + j)), 0, 0) for t in echant(L_USE, 32)])
piste(use, CTRL, [lum(t, 0.55 + 0.3 * math.sin(TAU * 2 * t / L_USE)) for t in echant(L_USE, 32)])

# event_use_start (0,4 s) : les barbes se hérissent (échelle du groupe parent `barbes` : seul dépliage de l'animation), le
# fil s'allume. Aucun son (rejoué quand le mod croit l'objet lâché).
L_US = 0.4
ustart = anim("event_use_start", L_US)
piste(ustart, OUT["barbes_grp"], [kf("scale", t, 1 + 0.2 * bump(t, 0.0, 0.08, 0.14, 0.36)) for t in echant(L_US, 16)])
piste(ustart, CTRL, [lum(t, 0.9 * bump(t, 0.0, 0.05, 0.1, 0.38)) for t in echant(L_US, 16)])

# event_select (0,7 s) : le dard sort du collet (échelle de `fer` : seul dépliage par scale), puis les barbes se déplient
# depuis la hampe l'une après l'autre, le fil s'allume en dernier.
L_SEL = 0.7
sel = anim("event_select", L_SEL)
piste(sel, OUT["fer"], [kf("scale", t, 0.3 + 0.7 * sm(t, 0.0, 0.3) + 0.06 * bump(t, 0.24, 0.3, 0.34, 0.48)) for t in echant(L_SEL, 21)])
for j, (g, s) in enumerate(BA):
    piste(sel, g, [rot(t, -ouvre(s) * 38 * (1 - sm(t, 0.22 + 0.08 * j, 0.46 + 0.08 * j))) for t in echant(L_SEL, 21)])
piste(sel, CTRL, [lum(t, -1 + 1 * sm(t, 0.3, 0.45) + 0.8 * bump(t, 0.4, 0.48, 0.52, 0.7)) for t in echant(L_SEL, 21)])

# event_swing (0,3 s) : l'estoc (la lance pousse de 0,7 px dans son axe puis revient), le fil s'avive.
L_SW = 0.3
sw = anim("event_swing", L_SW)
piste(sw, OUT["lance"], [kf("position", t, 0, 0.7 * sm(t, 0.0, 0.06) * (1 - sm(t, 0.08, 0.28)), 0) for t in echant(L_SW, 15)])
piste(sw, CTRL, [lum(t, 0.9 * bump(t, 0.0, 0.04, 0.08, 0.28)) for t in echant(L_SW, 15)])

# event_hit (0,6 s) : éclat du fil (+1,6), les barbes frissonnent ; **le seul son** (block.sculk.break à 0,04 s).
L_HIT = 0.6
hit = anim("event_hit", L_HIT)
for j, (g, s) in enumerate(BA):
    piste(hit, g, [rot(t, ouvre(s) * 5 * math.sin(TAU * 3 * t / 0.36 + j) * (1 - sm(t, 0.0, 0.36))) for t in echant(L_HIT, 24)])
piste(hit, CTRL, [lum(t, 1.6 * (sm(t, 0.0, 0.03) * (1 - sm(t, 0.06, 0.55)))) for t in echant(L_HIT, 24)])

ANIMS = [idle, use, ustart, sel, sw, hit]


# ------------------------------------------------------------------ écriture
assert len(elements) <= 8192, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
# ------------------------------------------------------------------ réglages Display (ceux de skin_lance_orage, validés en jeu)
def display_vanilla(rot_v, trans_v, ech_v, longueur_v, incl_x=0.0):
    """Display de la lance de Minecraft (image plate, pointe en haut à gauche de l'image de 32 × 32 : axe (-1, 1) du modèle,
    longueur longueur_v px du modèle) recalculé pour cet objet (axe +Y, longueur A_MAX - A_MIN, prise en P0)."""
    Rv = objet._rxyz((incl_x, 0, 0))[:3, :3] @ objet._rxyz(rot_v)[:3, :3] @ rotm(0, 0, 45)
    ex, ey, ez = euler(Rv.T)
    rot_ = [round(-ex, 2) + 0.0, round(-ey, 2) + 0.0, round(-ez, 2) + 0.0]
    assert np.allclose(objet._rxyz(rot_)[:3, :3], Rv, atol=1e-3)
    k = ech_v * longueur_v / (A_MAX - A_MIN)
    prise = np.array((0, P0[1] - 8, 0))
    tr = np.asarray(trans_v, float) - objet._rxyz(rot_)[:3, :3] @ (k * prise)
    return {"rotation": rot_, "translation": [round(float(v), 2) for v in tr], "scale": [round(k, 3)] * 3}


LV = 30 * math.sqrt(2) / 2
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
model = objet.modele(NOM, "lance", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son
limiter_sons(model)
# Un seul son, au coup qui touche (event_hit), à 0,04 s : tools/sons.py ne connaît pas encore les événements d'objet.
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
print(f"longueur {float(P[:, 1].max() - P[:, 1].min()):.1f} px ; boîte {P.min(0).round(2)} .. {P.max(0).round(2)}")
gm = min(float(FER.h(np.array([p]))[0] - Z_FOND) for p in FER.gax)
marge = min(float(FER.dE(np.array([p]))[0] - FER.wb(np.array([p]))[0]) for p in FER.gl + FER.gr)
print(f"fer : épaisseur {2 * FER.h(np.array([O_ + FER.u * 0.6]))[0]:.2f} px à la racine -> {2 * FER.h(np.array([O_ + FER.u * FER.L]))[0]:.2f} à la pointe ; "
      f"profondeur mini de gouttière {gm:.2f} px, marge gouttière/biseau {marge:.2f} px")
print("Display :", json.dumps({k: AFFICHAGE[k] for k in ("thirdperson_righthand", "firstperson_righthand", "gui")}))
