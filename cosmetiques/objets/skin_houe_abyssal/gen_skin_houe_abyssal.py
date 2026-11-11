"""Serre de l'Abysse : skin d'objet (guide 14) pour toutes les houes du joueur, ensemble Abyssal (thème Démoniaque).
Design original. Écrit skin_houe_abyssal.png, skin_houe_abyssal_e.png et .build/skin_houe_abyssal_brut.bbmodel.
Point de départ : gen_skin_pelle_abyssal.py (classe Fer opaque de la hache du set, tours, griffes, peintures, animations) ;
technique de la lame en travers dans son propre repère (Lp/Lv, CUR) reprise du principe des houes Orage et Givre (pas de
leur design).

Référence réelle (.claude/references/objets/houes.md) : houe à œil et col de cygne (œil qui prend le manche, col recourbé,
lame plate en travers de l'axe, angle de travail 55–70°, lame penchée vers la poignée : elle mord puis tire la terre).
Ici une **serre** : une mandibule d'os (le col) sort de l'œil et porte une lame d'os en ongle de bête, étroite dans sa bague,
flancs qui s'évasent, **fil creux entre deux crocs** (les coins) qui mordent la terre. Silhouette reconnaissable sans la
couleur : crochet d'un seul côté, terminé par une lame en éventail à deux crocs ; ni deux crocs opposés (pioche), ni fer le
long du manche (hache), ni bout rond (pelle), ni lame longue (épée) ; différente des houes Orage (trapèze à dents d'éclair)
et Givre (croissant convexe).
- lame = une plaque biseautée fermée (recette .claude/references/objets/volume-3d.md) : plat incliné par face (1,52 px à la
  racine -> 0,54 px aux crocs), tous les bords biseautés (pente unique 40°) sauf la racine cachée dans la bague ; **vert
  seulement au fil** (fil vif + _e, bande verte, halo sombre, veines qui montent du fil, pointes des crocs) ; flancs en os nu
  à liseré violacé ; **gouttière creusée** dans l'axe (le canal de la dent), filet vert + _e couché au fond ;
- **lame dans son propre repère** (u de la racine vers le fil, w en travers, z normale des plats), à 58° du manche, tournée
  de ROLL = 34° autour de son axe : dans la case on voit son plat (sinon, par la tranche, elle se lit comme un bout de
  pioche), en main aussi ;
- col = mandibule d'os octogonale qui s'affine, crête de trois épines d'os à pointe verte sur son dos ; bague d'os violacée
  à la jonction col / lame ; œil d'os octogonal le long du manche entre bagues violacées ; bouton (celui de la houe vanilla)
  en croc conique à pointe verte ; manche d'os, poignée de cuir pourpre-noir en spirale à clous d'os pâle, griffe au pommeau.
Pas de métal, d'or ni de rouge. Repère : comme iron_hoe.png vu de +Z (manche du bas à gauche vers le haut à droite, tête vers
le haut à gauche), boîte centrée dans le bloc. Display vanilla item/handheld (tools/objet.py), gui réglé à la case. Étape
unique `repos`.

Objet vivant (guide 14), sobre :
- item_idle (6 s) : les épines de la crête respirent à tour de rôle (±3°), le fil souffle (ctrl_lumiere, ±0,35) ;
- event_select (0,7 s) : la serre sort de la bague (échelle de `lame` : seul dépliage par scale), la crête se dresse, le fil
  s'allume en dernier ;
- event_swing (0,4 s) : le geste de labour (la serre pique de 3°, pivot dans la main), le fil s'avive ;
- event_hit (0,6 s) : éclat du fil (+1,6), frisson de la crête ; **le seul son** (block.sculk.break à 0,04 s) ;
- event_break (0,55 s) : la serre mord (+5°) puis tire (−2,5°), le fil « boit » (+0,7), sans son.
Aucun son sur event_use_start. Pas de particules, pas d'item_gui, item_ground repli sur item_idle.
Fonctions avancées : calque _e (fil, veines, gouttière, pointes), ctrl_lumiere (non simulé par le renderer), scale animé
(event_select), animations d'objet (non simulées par l'aperçu). À juger en jeu : lecture de la houe dans la case et en main,
event_swing au labour (supposé), event_hit / event_break et le son, ctrl_lumiere sur un objet.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

NOM = "skin_houe_abyssal"
TEX = 512
TAU = 2 * math.pi
AVEC_E = True
GUI = float(os.environ.get("GUI", "0.84"))   # échelle de l'inventaire

# Repère de l'image (iron_hoe.png vu de +Z) : a le long du manche (vers la tête), b en travers dans le plan de l'image
# (col et lame vers +b, en haut à gauche), z épaisseur.
A_ = np.array((1.0, 1.0, 0.0)) / math.sqrt(2)
W_ = np.array((-1.0, 1.0, 0.0)) / math.sqrt(2)
T_ = np.array((0.0, 0.0, 1.0))
P0 = np.zeros(3)          # recalé après coup (boîte centrée dans le bloc)


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


# ------------------------------------------------------------------ tête dans le plan de l'image (a, b ; px)
A_O = 16.2                       # centre de l'œil (la douille d'os qui prend le manche)
R_OE = 1.12                      # apothème de l'œil (octogone le long du manche)
ANG = math.radians(float(os.environ.get("ANG", "58")))     # angle de travail : lame à 58° du manche, penchée vers la poignée
D_L = np.array((-math.cos(ANG), math.sin(ANG)))            # direction de la lame dans le plan (a, b)
N_L = np.array((D_L[1], -D_L[0]))                          # normale du dos de la lame dans le plan (côté +a)
NC = [(A_O + 0.1, 0.55), (A_O + 1.0, 1.45), (A_O + 1.05, 2.55), (A_O + 0.55, 3.3)]   # axe du col (la mandibule)
R_L = bez(NC, 1.0)[0]                                      # racine de la lame (dans la bague)
ROLL = math.radians(float(os.environ.get("ROLL", "34")))  # lame tournée autour de son axe : son plat se voit dans la case

# repère de la lame (u de la racine vers le fil, w en travers, z normale des plats) ; e3 = e1 x e2 (direct)
E1 = unit(Wv(*D_L))
E2 = unit(math.cos(ROLL) * T_ + math.sin(ROLL) * Wv(*N_L))
E3 = np.cross(E1, E2)
CUR = ["img"]                    # repère des volumes en cours : "img" (a, b, z) ou "lame" (u, w, z)


def Lp(u, w=0.0, z=0.0):
    return Wp(*R_L) + E1 * u + E2 * w + E3 * z


def Lv(u, w=0.0, z=0.0):
    return E1 * u + E2 * w + E3 * z


# ------------------------------------------------------------------ dessin de la lame (repère de la lame : u, w ; px)
# Serre : lame d'os taillée en ongle de bête, étroite dans la bague, flancs qui s'évasent, fil **creux** entre deux crocs
# (les coins) : elle mord la terre et la tire, comme une serre. Seul le fil (crocs compris) est vert.
O_ = np.zeros(2)                 # racine de la lame (centre de la bague)
U_FIL = 0.55                     # en deçà (u < 0,55), le bord est caché dans la bague : pas de biseau
FLANC_P = catmull([(-0.2, 0.70), (0.6, 0.77), (1.5, 1.04), (2.5, 1.58), (3.5, 2.28), (4.4, 2.88), (5.05, 3.15)], 6)
FIL_C = catmull([(5.05, 3.15), (4.74, 2.25), (4.5, 1.15), (4.42, 0.0), (4.5, -1.15), (4.74, -2.25), (5.05, -3.15)], 6)
FLANC_M = [(a, -b) for a, b in FLANC_P[::-1]]
B_BAGUE = 1.16                   # apothème de la bague qui cache la jonction col / lame

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
        # reflets violacés : une ligne au milieu de chaque pan, entre la gouttière et le flanc
        self.centres = [[(a, sg * 0.58 * b) for a, b in flanc if 1.2 < a < 4.4] for sg in (1, -1)]
        # veines : partent du fil et montent vers la racine, en se ramifiant un peu
        Tr = np.array(resample(tranchant, 0.05))
        ls = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(Tr, axis=0), axis=1))])
        self.veines = []
        for j, (t, pente, fr, br) in enumerate(((0.16, 0.30, 0.70, 0.5), (0.33, -0.25, 0.95, 0.0), (0.50, 0.20, 1.05, 0.5),
                                                (0.67, -0.25, 0.95, 0.0), (0.84, 0.30, 0.70, 0.45))):
            i = min(max(int(np.searchsorted(ls, t * ls[-1])), 1), len(Tr) - 2)
            d = unit(Tr[i + 1] - Tr[i - 1])
            n = normale_dedans(poly, Tr[i], d)
            st = Tr[i] + n * 0.02
            ln = 1.45 * fr
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
        """Tranchant (le vert ne vit qu'ici) : 1 si le bord le plus proche est le fil, 0 sur les flancs."""
        P = np.asarray(P, float)
        d_t = d_poly(P, self.tranchant)
        d_n = np.min(np.stack([d_poly(P, n) for n in self.nus]), axis=0)
        return smv(d_n - d_t, -0.02, 0.22)

    def in_g(self, P):
        return in_poly(P, self.gpoly)

    def d_g(self, P):
        return d_poly(P, list(self.gpoly) + [self.gpoly[0]])

    def d_ax(self, P):
        return d_poly(P, self.gax)

    def d_veine(self, P):
        return np.min(np.stack([d_poly(P, v) for v in self.veines]), axis=0)


FLP_R, FIL_R, FLM_R = resample(FLANC_P, 0.9), resample(FIL_C, 0.75), resample(FLANC_M, 0.9)
POLY = FLP_R + FIL_R[1:] + FLM_R[1:]             # fermé par la racine (u = -0,2, dans la bague)


def hors_bague(pts):
    for i, p in enumerate(pts):
        if p[0] >= U_FIL:
            return pts[max(0, i - 1):]
    return pts


FLP_F = hors_bague(FLP_R)
FLM_F = hors_bague(FLM_R[::-1])[::-1]
FIL_LAME = FLP_F + FIL_R[1:] + FLM_F[1:]
LAME = Fer("lame", POLY, FIL_LAME, FIL_R, [FLP_F, FLM_F], FLANC_P, (1.0, 0.0), 0.76, 0.27, 1.25, 3.95, 0.30)


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
    col = col * (1 - 0.22 * np.clip(1 - (P2[..., 0] - 0.5) / 1.6, 0, 1))[..., None]    # plus sombre vers la racine (le coin épais)
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
        P_, V_ = (Lp, Lv) if CUR[0] == "lame" else (Wp, Wv)
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


def grp(nom, pivot, parent):
    GROUPES.append((nom, np.asarray(pivot, float), parent))
    return nom


OUT = {}
EPINES = ((0.32, 0.85, 0.27), (0.56, 1.05, 0.30), (0.80, 0.85, 0.26))    # crête de la mandibule : (s sur le col, longueur, rayon)


def conception():
    racine = grp(objet.etape("repos", "houe"), Wp(A_O), None)
    houe = grp("houe", Wp(4.0), racine)                    # pivot dans la main : le geste de labour
    # --- manche : talon renflé, poignée de cuir en spirale cloutée d'os, bague, hampe d'os jusque dans l'œil
    manche = grp("manche", Wp(3.0), houe)
    prof = [(-0.15, 0.0, 0.0, 0.62, "os", {"clair": 0.15}), (0.0, 0.62, 0.15, 0.95, "bague", {"clair": 0.1}),
            (0.15, 0.95, 0.85, 0.95, "bague", {}), (0.85, 0.95, 1.05, 0.80, "bague", {"clair": -0.1}),
            (1.05, 0.80, 6.3, 0.80, "cuir", {}),
            (6.3, 0.80, 6.42, 0.94, "bague", {"clair": 0.1}), (6.42, 0.94, 6.75, 0.94, "bague", {}),
            (6.75, 0.94, 6.88, 0.72, "bague", {"clair": -0.1}),
            (6.88, 0.72, A_O - 2.3, 0.64, "os", {}),
            (A_O - 2.3, 0.64, A_O - 2.15, 0.84, "bague", {"clair": 0.1}), (A_O - 2.15, 0.84, A_O - 1.8, 0.84, "bague", {}),
            (A_O - 1.8, 0.84, A_O - 1.65, 0.62, "bague", {"clair": -0.1}),
            (A_O - 1.65, 0.62, A_O + 0.6, 0.62, "os", {})]
    tour(manche, "manche", Wp(0), A_, T_, prof, n=12)
    for k, a in enumerate((2.1, 3.7, 5.3)):
        tour(manche, f"clou{k}_", Wp(a, 0, -0.98), T_, A_, [(0.0, 0.0, 0.14, 0.26, "clou", {}), (0.14, 0.26, 1.82, 0.26, "clou", {}),
                                                           (1.82, 0.26, 1.96, 0.0, "clou", {})], n=8, phase=math.pi / 8)
    gp = grp("griffe_pommeau", Wp(0.3), houe)
    griffe(gp, "gp", Wp(0.35, -0.2), Wv(-0.85, -0.6), Wv(0.7, -1.0), 2.5, 0.40)
    # --- tête : œil d'os octogonal le long du manche (la douille), bagues violacées, chapeau fermé
    tete = grp("tete", Wp(A_O), houe)
    grp("ctrl_lumiere", Wp(A_O), tete)
    a0 = A_O - 1.15
    tour(tete, "oeil", Wp(a0), A_, T_,
         [(0.0, 0.55, 0.14, R_OE + 0.16, "bague", {"clair": 0.1}), (0.14, R_OE + 0.16, 0.46, R_OE + 0.16, "bague", {}),
          (0.46, R_OE + 0.16, 0.58, R_OE, "bague", {"clair": -0.1}), (0.58, R_OE, 1.78, R_OE, "os", {"clair": 0.05}),
          (1.78, R_OE, 1.9, R_OE + 0.16, "bague", {"clair": 0.1}), (1.9, R_OE + 0.16, 2.2, R_OE + 0.16, "bague", {}),
          (2.2, R_OE + 0.16, 2.42, 0.0, "os", {"clair": 0.1})], n=8, phase=math.pi / 8)
    # bouton au bout de l'œil (celui de la houe vanilla) : croc d'os conique à pointe verte, un peu recourbé vers l'arrière
    bouton = grp("bouton", Wp(A_O + 1.2), tete)
    griffe(bouton, "bouton", Wp(A_O + 1.05, 0.0), Wv(1, -0.05), Wv(0, -1), 1.7, 0.62, curve=0.25, nseg=6)
    # --- col : mandibule d'os octogonale qui s'affine, de l'œil à la bague de la lame
    col = grp("col", Wp(A_O), tete)
    ss = np.linspace(0.0, 1.0, 11)
    for i in range(len(ss) - 1):
        p, q = bez(NC, ss[i])[0], bez(NC, ss[i + 1])[0]
        r0, r1 = 0.66 - 0.16 * ss[i], 0.66 - 0.16 * ss[i + 1]
        L = float(np.linalg.norm(q - p))
        tour(col, f"col{i}_", Wp(*p), Wv(*(q - p)), T_, [(-0.06, r0, L + 0.06, r1, "os", {"y0": 3.0 * ss[i]})], n=8, phase=math.pi / 8)
    # crête : trois épines d'os sur le dos de la mandibule (côté +a), pointes vertes recourbées vers l'œil
    epines = []
    for j, (s_, L, rm) in enumerate(EPINES):
        p, d = bez(NC, s_)
        n = np.array((d[1], -d[0]))                        # normale extérieure (côté +a)
        r = 0.66 - 0.16 * s_
        base = Wp(*(p + n * (r - 0.12)))
        g = grp(f"epine_{j}", base, col)
        griffe(g, f"ep{j}_", base, Wv(*(n * 1.0 + d * 0.25)), Wv(*(-d)), L, rm, curve=0.35, nseg=6)
        epines.append(g)
    # bague d'os violacée qui cache la jonction col / lame (axe de la lame)
    CUR[0] = "img"
    tour(col, "bague_lame", Lp(-0.55), E1, E2,
         [(0.0, 0.5, 0.16, B_BAGUE, "bague", {"clair": 0.1}), (0.16, B_BAGUE, 0.82, B_BAGUE, "bague", {}),
          (0.82, B_BAGUE, 1.02, 0.85, "bague", {"clair": -0.1})], n=8, phase=math.pi / 8)
    # --- lame : serre d'os plein en vrai volume, dans son propre repère ; pivot à la racine (elle sort de la bague)
    lame = grp("lame", Lp(0.0), col)
    CUR[0] = "lame"
    volume(LAME, lame)
    gouttiere(LAME, lame)
    CUR[0] = "img"
    OUT.update(racine=racine, houe=houe, tete=tete, lame=lame, epines=epines, gp=gp, bouton=bouton)
    return racine


RACINE = conception()


# ------------------------------------------------------------------ recentrage (boîte centrée dans le bloc)
def coins_cubes(liste):
    P = []
    for cb in liste:
        for i in range(8):
            sgn = np.array([1 if (i >> k) & 1 else -1 for k in range(3)])
            P.append(cb["c"] + cb["R"] @ (cb["half"] * sgn))
    return np.array(P)


_Pc = coins_cubes(CUBES)
DEC = np.array((8.0, 8.0, 8.0)) - (_Pc.min(0) + _Pc.max(0)) / 2
for cb in CUBES:
    cb["c"] = cb["c"] + DEC
GROUPES = [(n, p + DEC, par) for n, p, par in GROUPES]



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


CTRL = "ctrl_lumiere"
EP = OUT["epines"]

# item_idle (6 s) : les épines de la crête respirent à tour de rôle (±3°), le bouton à peine, le fil souffle.
L_IDLE = 6.0
idle = anim("item_idle", L_IDLE, "loop")
for j, g in enumerate(EP):
    piste(idle, g, [rot(t, 3.0 * math.sin(TAU * (t / L_IDLE - 0.12 * j))) for t in echant(L_IDLE, 24)])
piste(idle, OUT["bouton"], [rot(t, -2.0 * math.sin(TAU * (t / L_IDLE - 0.5))) for t in echant(L_IDLE, 24)])
piste(idle, CTRL, [lum(t, 0.35 * math.sin(TAU * 2 * t / L_IDLE)) for t in echant(L_IDLE, 24)])

# event_select (0,7 s) : la serre sort de la bague (échelle de `lame` : seul dépliage par scale), la crête se dresse
# d'avant en arrière, le fil s'allume en dernier.
L_SEL = 0.7
sel = anim("event_select", L_SEL)
piste(sel, OUT["lame"], [kf("scale", t, 0.3 + 0.7 * sm(t, 0.0, 0.32) + 0.06 * bump(t, 0.26, 0.33, 0.36, 0.5)) for t in echant(L_SEL, 21)])
for j, g in enumerate(EP):
    piste(sel, g, [rot(t, -35 * (1 - sm(t, 0.2 + 0.07 * j, 0.42 + 0.07 * j))) for t in echant(L_SEL, 21)])
piste(sel, CTRL, [lum(t, -1 + 1 * sm(t, 0.3, 0.45) + 0.8 * bump(t, 0.4, 0.48, 0.52, 0.7)) for t in echant(L_SEL, 21)])

# event_swing (0,4 s) : le geste de labour (la serre pique de 3° puis revient ; pivot dans la main), le fil s'avive.
L_SW = 0.4
sw = anim("event_swing", L_SW)
piste(sw, OUT["houe"], [rot(t, 3.0 * sm(t, 0.0, 0.08) * (1 - sm(t, 0.1, 0.34))) for t in echant(L_SW, 16)])
piste(sw, CTRL, [lum(t, 0.9 * bump(t, 0.0, 0.04, 0.1, 0.36)) for t in echant(L_SW, 16)])

# event_hit (0,6 s) : éclat du fil (+1,6), frisson de la crête ; **le seul son** (block.sculk.break à 0,04 s).
L_HIT = 0.6
hit = anim("event_hit", L_HIT)
for j, g in enumerate(EP):
    piste(hit, g, [rot(t, 4 * math.sin(TAU * 3 * t / 0.36 + j) * (1 - sm(t, 0.0, 0.36))) for t in echant(L_HIT, 24)])
piste(hit, CTRL, [lum(t, 1.6 * (sm(t, 0.0, 0.03) * (1 - sm(t, 0.06, 0.55)))) for t in echant(L_HIT, 24)])

# event_break (0,55 s) : la serre mord (+5°) puis tire la terre vers la main (−2,5°), le fil « boit » (+0,7), sans son.
L_BR = 0.55
brk = anim("event_break", L_BR)
piste(brk, OUT["houe"], [rot(t, 5.0 * sm(t, 0.0, 0.09) * (1 - sm(t, 0.1, 0.24)) - 2.5 * bump(t, 0.12, 0.24, 0.3, 0.5))
                         for t in echant(L_BR, 22)])
piste(brk, CTRL, [lum(t, 0.7 * (sm(t, 0.0, 0.05) * (1 - sm(t, 0.1, 0.5)))) for t in echant(L_BR, 22)])

ANIMS = [idle, sel, sw, hit, brk]

# ------------------------------------------------------------------ écriture
assert len(elements) <= 8192, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
AFFICHAGE = objet.affichage("houe", gui={"scale": [GUI] * 3})
model = objet.modele(NOM, "houe", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
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
D_ = np.array((1, 1, 0)) / math.sqrt(2)
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur le long du manche {float((P @ D_).max() - (P @ D_).min()):.1f} px ; boîte {P.min(0).round(2)} .. {P.max(0).round(2)}")
gm = min(float(LAME.h(np.array([p]))[0] - Z_FOND) for p in LAME.gax)
marge = min(float(LAME.dE(np.array([p]))[0] - LAME.wb(np.array([p]))[0]) for p in LAME.gl + LAME.gr)
print(f"lame : épaisseur {2 * LAME.h(np.array([O_ + LAME.u * 0.6]))[0]:.2f} px à la racine -> {2 * LAME.h(np.array([O_ + LAME.u * LAME.L]))[0]:.2f} aux crocs ; "
      f"profondeur mini de gouttière {gm:.2f} px, marge gouttière/biseau {marge:.2f} px")
