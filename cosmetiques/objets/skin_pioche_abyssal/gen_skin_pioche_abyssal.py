"""Pic de l'Abysse : skin d'objet (guide 14) pour toutes les pioches du joueur, ensemble Abyssal (thème Démoniaque). Design original.
Écrit skin_pioche_abyssal.png, skin_pioche_abyssal_e.png et .build/skin_pioche_abyssal_brut.bbmodel à côté de ce script.

Référence réelle (.claude/references/objets/pioches-marteaux-pneumatiques.md, Pic de mineur) : fer à œil traversé par le
manche, deux bras qui se recourbent vers le manche (croissant de l'image vanilla), pointe pour attaquer la roche.
Traduction Abyssal (langage de skin_epee_abyssal, .claude/styles/abyssal.md ; suivi sets-objets-2026-11-08.md) :
- fer = deux crocs d'os charbon taillé : **croc long** (+b, le bras qui frappe en 3e personne) à deux barbillons recourbés
  côté manche, comme une mâchoire ; **croc court** (-b) plus crochu ; pointes et fils de la partie qui travaille en vert acide
  (+ _e), qui s'éteint vers l'œil (os nu près du manche) ;
- vrai volume (.claude/references/objets/volume-3d.md, validé en jeu) : chaque croc est une plaque biseautée fermée (classe
  Bras de skin_pioche_givre, mais opaque : pas de peau trans_, os plein), pente unique 51° (tan 1,25 : bras étroits, il reste
  un plat), amincie 1,60 -> 0,48 px ; plat d'os marbré à reflet violacé, arête violacée, veines vertes qui montent du fil ;
  **gouttière creusée** le long de chaque croc (parois d'os, lèvre violacée, filet vert + _e couché au fond) ;
- œil = collet d'os octogonal à 8 pans en tour, couvercles d'os cerclés de violet, bossette conique à pointe verte de chaque
  côté ; **corne** recourbée qui sort du haut de l'œil (griffe en tronçons coniques, pointe verte) ;
- manche : hampe d'os à bagues de croissance, bagues d'os violacées, poignée de cuir pourpre-noir en spirale à trois clous
  d'os, pommeau d'os et **griffe de pommeau** recourbée (comme la garde de l'épée).
Pas de métal, d'or ni de rouge. Silhouette (sans la couleur) : croissant de deux crocs crochus, barbillons de mâchoire, corne
au sommet, griffe au pommeau ; différente du pic de l'orage (bec de faucon, tranchant en coin), du piolet de givre (pic denté
+ panne à fil droit, couronne de cristaux) et du pic à vapeur.
Repère (catégorie objets, Recette) : comme iron_pickaxe.png vu de +Z : manche du bas à gauche vers le haut à droite (axe a),
fer en travers (b), croc long vers le haut à gauche. Boîte centrée dans le bloc, Display vanilla item/handheld, gui 0,84.

Objet vivant (guide 14), sobre :
- item_idle (6 s) : la corne et la griffe du pommeau respirent (±2,5°), le fil vert souffle (ctrl_lumiere) ;
- event_select (0,6 s) : les crocs sortent de l'œil (échelle de pic et panne : seul dépliage), la corne se déplie, le fil
  s'allume en dernier ;
- event_swing (0,4 s) : la corne se crispe, le fil s'avive ;
- event_hit (0,5 s) : éclat du fil (+1,6) et frisson de la tête ; **le seul son** (block.sculk.break à 0,04 s : une clé à
  0,0 s est muette au premier coup) ;
- event_break (0,5 s) : le croc mord (la tête plonge de 3° puis revient), le fil pulse ; sans son.
Aucun son sur event_use_start. Pas de particules.
Fonctions avancées : calque _e (fils, pointes, veines, gouttières), ctrl_lumiere (non simulé), scale animé (event_select),
animations d'objet (non simulées par l'aperçu). À juger en jeu : lecture des crocs par la tranche et dans la case,
ctrl_lumiere et event_hit / event_break sur un objet, le son.
Une seule étape : groupe racine `repos`.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

NOM = "skin_pioche_abyssal"
TEX = 512
TAU = 2 * math.pi
AVEC_E = True

# Repère : a le long du manche (vers la tête), b en travers dans le plan de l'image (croc long vers +b), z épaisseur.
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
# --- langage du set (skin_epee_abyssal)
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

# ------------------------------------------------------------------ dessin du fer (plan a, b ; px)
A_O = 16.4                   # centre de l'œil
O_ = np.array((A_O, 0.0))
R_COL = 1.5                  # apothème du collet (octogone)
Z_COL = 1.0                  # demi-épaisseur du collet


def bez(P, s):
    P = [np.array(p, float) for p in P]
    u = 1 - s
    c = u ** 3 * P[0] + 3 * u * u * s * P[1] + 3 * u * s * s * P[2] + s ** 3 * P[3]
    d = 3 * u * u * (P[1] - P[0]) + 6 * u * s * (P[2] - P[1]) + 3 * s * s * (P[3] - P[2])
    return c, d / np.linalg.norm(d)


PIC = [(A_O, 0.0), (A_O + 1.0, 2.6), (A_O + 0.35, 5.3), (A_O - 2.3, 7.2)]       # croc long (+b)
PAN = [(A_O, 0.0), (A_O + 0.8, -2.0), (A_O + 0.25, -3.7), (A_O - 1.75, -5.0)]  # croc court (-b), plus crochu


def w_pic(s):
    return 0.30 + 0.98 * (1 - s) ** 0.8


def w_pan(s):
    return 0.30 + 0.95 * (1 - s) ** 0.75


DENTS = [0.50, 0.66]          # barbillons sous le croc long (côté manche), inclinés vers la tête
H_DENT = 0.34


def bras(Pb, wf, sgn, n=40, dents=()):
    """Bord extérieur (côté +a, convexe) et bord intérieur (côté manche) d'un bras ; barbillons en dents de scie sur l'intérieur."""
    ext, inn = [], []
    base = [s for s in np.round(np.linspace(0, 1, n), 4) if not any(sk - 0.09 < s < sk + 0.03 for sk in dents)]
    ss = sorted(set(base) | {round(s, 4) for s in dents} | {round(s - 0.085, 4) for s in dents})
    for s in ss:
        c, d = bez(Pb, s)
        no = sgn * np.array((d[1], -d[0]))
        ext.append(c + no * wf(s))
        inn.append(c - no * wf(s))
    out_i = []
    for s, p in zip(ss, inn):
        c, d = bez(Pb, s)
        no = sgn * np.array((d[1], -d[0]))
        if any(abs(s - sk) < 1e-3 for sk in dents):
            out_i.append(c - no * (wf(s) + H_DENT) + d * 0.12)   # pointe du barbillon, tournée vers la tête
            out_i.append(c - no * wf(s) + d * 0.03)             # retombée presque droite
        else:
            out_i.append(p)
    return ext, out_i


_e, _i = bras(PIC, w_pic, 1, dents=DENTS)
_c1, _d1 = bez(PIC, 1.0)
TIP = tuple(_c1 + _d1 * 0.35)
TIP_D = _d1
_e2, _i2 = bras(PAN, w_pan, -1)
_c2, _d2 = bez(PAN, 1.0)
TIP2 = tuple(_c2 + _d2 * 0.35)
CENTRE_PIC = [tuple(bez(PIC, s)[0]) for s in np.linspace(0, 1, 30)] + [TIP]
CENTRE_PAN = [tuple(bez(PAN, s)[0]) for s in np.linspace(0, 1, 24)] + [TIP2]


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


def hors_collet(pts, marge=0.5):
    for i, p in enumerate(pts):
        if np.linalg.norm(np.array(p) - O_) >= R_COL - marge:
            return pts[max(0, i - 1):]
    return pts


def lisser_avec_dents(pts, pas=0.9):
    """Ré-échantillonne les parties lisses, garde les sommets des barbillons tels quels."""
    P = [np.array(p, float) for p in pts]
    garde = [0]
    for i in range(1, len(P) - 1):
        d1, d2 = unit(P[i] - P[i - 1]), unit(P[i + 1] - P[i])
        if d1 @ d2 < math.cos(math.radians(25)):
            garde.append(i)
    garde.append(len(P) - 1)
    out = []
    for j in range(len(garde) - 1):
        part = [tuple(p) for p in P[garde[j]:garde[j + 1] + 1]]
        L = sum(np.linalg.norm(np.array(part[k + 1]) - np.array(part[k])) for k in range(len(part) - 1))
        seg = resample(part, pas) if L > pas * 1.2 else [part[0], part[-1]]
        out += seg if not out else seg[1:]
    return out


# ------------------------------------------------------------------ vrai volume (os plein, opaque)
Z_E = 0.10                       # demi-épaisseur au fil
T_BIS = 1.25                     # pente unique des biseaux (51°) : bras étroits, il reste un plat pour la gouttière
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


class Bras:
    """Plaque biseautée fermée : contour poly, fil (polyligne sans la racine cachée dans l'œil), plat z = h0 + k (P - O)·u,
    gouttière creusée le long de la courbe Pb entre g0 et g1."""

    def __init__(self, nom, poly, fil, u, h_racine, h_bout, L, centre, Pb, sgn, wf, g0, g1, gw):
        self.nom, self.poly, self.centre = nom, poly, centre
        self.u = unit(np.asarray(u, float))
        self.k = (h_bout - h_racine) / (L - R_COL)
        self.h0 = h_racine - self.k * R_COL
        self.L = L
        self.segs = subdiv(fil)
        # gouttière : axe = la courbe du bras, demi-largeur en fuseau (pointue aux deux bouts)
        ax, gl, gr = [], [], []
        for j, t in enumerate(np.linspace(g0, g1, 14)):
            c, d = bez(Pb, t)
            no = sgn * np.array((d[1], -d[0]))
            v = j / 13
            w = gw * math.sin(math.pi * v) ** 0.6 + 0.012
            ax.append(tuple(c))
            gl.append(tuple(c + no * w))
            gr.append(tuple(c - no * w))
        self.gax, self.gl, self.gr = ax, gl, gr
        self.gpoly = gl + gr[::-1]
        # veines : partent du fil (deux bords) et montent vers la gouttière, dans la partie qui travaille
        self.veines = []
        for t, side, br in ((0.42, 1, 1), (0.58, -1, -1), (0.72, 1, -1), (0.36, -1, 1)):
            c, d = bez(Pb, t)
            no = sgn * np.array((d[1], -d[0]))
            w = wf(t)
            st = c + side * no * (w - 0.02)
            ln = max(0.2, w - 0.32)
            pts = [st]
            for k in (1, 2, 3):
                pts.append(st - side * no * ln * k / 3 - d * 0.10 * k + d * br * 0.09 * math.sin(k * 2.2))
            self.veines.append([tuple(p) for p in pts])

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
        """0 à l'œil -> 1 au bout."""
        return np.clip(((np.asarray(P, float) - O_) @ self.u) / self.L, 0, 1)

    def actif(self, P):
        """Partie qui travaille (le vert ne vit qu'ici) : 0 près de l'œil -> 1 au-delà du milieu."""
        return smv(self.s(P), 0.30, 0.55)

    def in_g(self, P):
        return in_poly(P, self.gpoly)

    def d_g(self, P):
        return d_poly(P, list(self.gpoly) + [self.gpoly[0]])

    def d_ax(self, P):
        return d_poly(P, self.gax)

    def d_veine(self, P):
        return np.min(np.stack([d_poly(P, v) for v in self.veines]), axis=0)


U_PIC = unit(np.array(TIP) - O_)
L_PIC = float((np.array(TIP) - O_) @ U_PIC)
U_PAN = unit(np.array(TIP2) - O_)
L_PAN = float((np.array(TIP2) - O_) @ U_PAN)
E_PIC, I_PIC = resample(_e, 0.9), lisser_avec_dents(_i)
P_PIC = E_PIC + [TIP] + I_PIC[::-1]
FIL_PIC = hors_collet(E_PIC) + [TIP] + hors_collet(I_PIC)[::-1]
E_PAN, I_PAN = resample(_e2, 0.9), resample(_i2, 0.9)
P_PAN = E_PAN + [TIP2] + I_PAN[::-1]
FIL_PAN = hors_collet(E_PAN) + [TIP2] + hors_collet(I_PAN)[::-1]
B_PIC = Bras("pic", P_PIC, FIL_PIC, U_PIC, 0.80, 0.24, L_PIC, CENTRE_PIC, PIC, 1, w_pic, 0.26, 0.82, 0.19)
B_PAN = Bras("panne", P_PAN, FIL_PAN, U_PAN, 0.78, 0.26, L_PAN, CENTRE_PAN, PAN, -1, w_pan, 0.30, 0.78, 0.17)


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
    # bandes du fil (vert vif, bande verte, halo sombre) proportionnelles à k : rien près de l'œil
    fil_f, bande_f, halo_f = 0.16 * k, 0.34 * k, 0.56 * k
    au = (f >= bande_f) & (f < halo_f)
    col[au] = lerp(AURA, col[au], np.clip((f[au] - bande_f[au]) / np.maximum(halo_f[au] - bande_f[au], 1e-3), 0, 1)[..., None])
    col[(f >= fil_f) & (f < bande_f)] = VEIN
    col, em = veines(pc, P2, col, em)
    col[f >= 0.90] = ARETE * 0.9                                  # arête violacée entre le biseau sombre et le plat
    nu = (f < 0.14) & (k < 0.3)                                   # fil d'os nu près de l'œil : liseré violacé
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
    col = col * (1 + 0.05 * np.sin(pc.s(P2) * 38.0 + nz * 2))[..., None]        # bagues de croissance de l'os, en travers
    dc = d_poly(P2, pc.centre)
    col = lerp(col, REFLET, (np.clip(1 - dc / 0.45, 0, 1) * 0.35)[..., None])   # reflet violacé au milieu du plat
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
        CUBES.append({"groupe": groupe, "nom": nom, "c": Wp(*c), "R": np.column_stack([Wv(*X), Wv(*Y), Wv(*Z)]),
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
            m = (in_poly(P2, pc.poly) & (de >= pc.wb(P2) - 0.03) & (np.linalg.norm(P2 - O_, axis=-1) > R_COL - 0.6)
                 & ~pc.in_g(P2))
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
        Ls = float(np.linalg.norm(b - a))
        prof = [(0.0, ray(t0), Ls, ray(t1) if i < nseg - 1 else 0.0, "griffe", {"t0": t0, "t1": t1})]
        if i == 0:                                   # bouchon conique : la racine n'est jamais un anneau ouvert
            prof.insert(0, (-0.3, 0.0, 0.0, ray(0.0), "griffe", {"t0": 0.0, "t1": 0.0}))
        tour(g, f"{nom}{i}_", a, b - a, nz, prof, n=n)


def t_disque(nom, n, Ra, N=48):
    """Couvercle d'os de l'œil : os marbré, cercle violacé, bord sombre."""
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


def disque(g, nom, c, Nrm, up, n, Ra, tile):
    Nrm = unit(Nrm)
    Y = unit(up - (up @ Nrm) * Nrm)
    X = np.cross(Y, Nrm)
    R = Ra / math.cos(math.pi / n)
    CUBES.append({"groupe": g, "nom": nom, "c": np.asarray(c, float) - Nrm * TH / 2, "R": np.column_stack([X, Y, Nrm]),
                  "half": np.array((R, R, TH / 2)), "faces": {"south": tile}})


# ------------------------------------------------------------------ conception
GROUPES = []        # (nom, pivot, parent)


def grp(nom, pivot, parent):
    GROUPES.append((nom, np.asarray(pivot, float), parent))
    return nom


OUT = {}


def conception():
    racine = grp(objet.etape("repos", "pioche"), Wp(A_O), None)
    pioche = grp("pioche", Wp(3.0), racine)
    # --- manche : pommeau d'os, poignée de cuir en spirale cloutée d'os, bague, hampe d'os, bague sous l'œil
    manche = grp("manche", Wp(3.0), pioche)
    prof = [(-0.75, 0.0, -0.6, 0.46, "os", {"clair": 0.15}), (-0.6, 0.46, -0.3, 0.74, "os", {"clair": 0.1}),
            (-0.3, 0.74, 0.1, 0.74, "bague", {}), (0.1, 0.74, 0.3, 0.56, "bague", {"clair": -0.1}),
            (0.3, 0.56, 6.3, 0.56, "cuir", {}),
            (6.3, 0.56, 6.45, 0.78, "bague", {"clair": 0.1}), (6.45, 0.78, 6.85, 0.78, "bague", {}),
            (6.85, 0.78, 7.0, 0.54, "bague", {"clair": -0.1}),
            (7.0, 0.54, A_O - 1.95, 0.48, "os", {}),
            (A_O - 1.95, 0.48, A_O - 1.8, 0.68, "bague", {"clair": 0.1}), (A_O - 1.8, 0.68, A_O - 1.45, 0.68, "bague", {}),
            (A_O - 1.45, 0.68, A_O - 1.3, 0.5, "bague", {"clair": -0.1})]
    tour(manche, "manche", Wp(0), A_, T_, prof, n=12)
    for k, a in enumerate((1.6, 3.35, 5.1)):
        tour(manche, f"clou{k}_", Wp(a, 0, -0.86), T_, A_, [(0.0, 0.0, 0.14, 0.26, "clou", {}), (0.14, 0.26, 1.58, 0.26, "clou", {}),
                                                          (1.58, 0.26, 1.72, 0.0, "clou", {})], n=8, phase=math.pi / 8)
    gp = grp("griffe_pommeau", Wp(-0.5), pioche)
    griffe(gp, "gp", Wp(-0.55, -0.1), Wv(-0.75, -0.75), Wv(1, -0.35), 3.0, 0.42)
    # --- tête : collet d'os octogonal (axe z), couvercles cerclés de violet, bossettes à pointe verte
    tete = grp("tete", Wp(A_O), pioche)
    grp("ctrl_lumiere", Wp(A_O), tete)
    tour(tete, "collet", Wp(A_O, 0, -Z_COL), T_, A_,
         [(0.0, R_COL - 0.2, 0.18, R_COL, "bague", {"clair": 0.1}), (0.18, R_COL, 2 * Z_COL - 0.18, R_COL, "os", {"clair": 0.05}),
          (2 * Z_COL - 0.18, R_COL, 2 * Z_COL, R_COL - 0.2, "bague", {"clair": 0.1})], n=8, phase=math.pi / 8)
    td = t_disque("disque_collet", 8, R_COL - 0.2)
    for s in (1, -1):
        cs = "e" if s > 0 else "i"
        disque(tete, f"couvercle_{cs}", Wp(A_O, 0, s * Z_COL), T_ * s, A_, 8, R_COL - 0.2, td)
        tour(tete, f"bossette_{cs}", Wp(A_O, 0, s * (Z_COL - 0.05)), T_ * s, A_,
             [(0.0, 0.62, 0.22, 0.62, "bague", {"clair": 0.15}), (0.22, 0.62, 0.95, 0.0, "griffe", {"t0": 0.45, "t1": 1.0})], n=8)
    # corne qui sort du haut de l'œil et se recourbe vers le croc long
    corne = grp("corne", Wp(A_O + R_COL - 0.4), tete)
    griffe(corne, "corne", Wp(A_O + R_COL - 0.45, 0.2), Wv(1, 0.22), Wv(0, 1), 2.5, 0.58, curve=0.40, nseg=8)
    # --- crocs : os plein en vrai volume ; pivot à l'œil (ils sortent de l'œil)
    for pc in (B_PIC, B_PAN):
        g = grp(pc.nom, Wp(A_O), tete)
        volume(pc, g)
        gouttiere(pc, g)
    OUT.update(racine=racine, pioche=pioche, tete=tete, corne=corne, griffe_pommeau=gp)
    return racine


RACINE = conception()


# ------------------------------------------------------------------ recentrage, atlas
def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


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


# ------------------------------------------------------------------ animations (objet vivant, guide 14)
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
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 20,
            "selected": name == "item_idle", "animators": {}}


def piste(an, g, keys):
    an["animators"][groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": keys}


def echant(L, n):
    return [round(L * i / n, 4) for i in range(n + 1)]


CTRL = "ctrl_lumiere"
# Les pièces tournent autour de +Z (normale du plan de l'image) : elles restent dans leur plan.
L_IDLE = 6.0
idle = anim("item_idle", L_IDLE, "loop")
piste(idle, OUT["corne"], [rot(t, 2.5 * math.sin(TAU * t / L_IDLE)) for t in echant(L_IDLE, 24)])
piste(idle, OUT["griffe_pommeau"], [rot(t, -2.5 * math.sin(TAU * (t / L_IDLE - 0.15))) for t in echant(L_IDLE, 24)])
piste(idle, CTRL, [lum(t, 0.35 * math.sin(TAU * 2 * t / L_IDLE)) for t in echant(L_IDLE, 24)])

L_SEL = 0.6
sel = anim("event_select", L_SEL)
for j, g in enumerate(("pic", "panne")):
    t0 = 0.04 * j
    piste(sel, g, [kf("scale", t, 0.2 + 0.8 * sm(t, t0, t0 + 0.28) + 0.07 * bump(t, t0 + 0.2, t0 + 0.28, t0 + 0.3, t0 + 0.45))
                   for t in echant(L_SEL, 18)])
piste(sel, OUT["corne"], [rot(t, -30 * (1 - sm(t, 0.15, 0.48))) for t in echant(L_SEL, 18)])
piste(sel, OUT["griffe_pommeau"], [rot(t, 24 * (1 - sm(t, 0.1, 0.42))) for t in echant(L_SEL, 18)])
piste(sel, CTRL, [lum(t, -1 + sm(t, 0.28, 0.42) + 0.8 * bump(t, 0.36, 0.44, 0.46, 0.6)) for t in echant(L_SEL, 18)])

L_SW = 0.4
sw = anim("event_swing", L_SW)
piste(sw, OUT["corne"], [rot(t, -10 * bump(t, 0.0, 0.05, 0.14, 0.38)) for t in echant(L_SW, 16)])
piste(sw, OUT["griffe_pommeau"], [rot(t, 8 * bump(t, 0.0, 0.05, 0.16, 0.38)) for t in echant(L_SW, 16)])
piste(sw, CTRL, [lum(t, 0.9 * bump(t, 0.0, 0.04, 0.1, 0.36)) for t in echant(L_SW, 16)])

L_HIT = 0.5
hit = anim("event_hit", L_HIT)
piste(hit, OUT["tete"], [rot(t, 1.6 * math.sin(TAU * t / 0.09) * (1 - sm(t, 0.0, 0.3))) for t in echant(L_HIT, 25)])
piste(hit, CTRL, [lum(t, 1.6 * sm(t, 0.0, 0.03) * (1 - sm(t, 0.06, 0.46))) for t in echant(L_HIT, 25)])

L_BR = 0.5
brk = anim("event_break", L_BR)
piste(brk, OUT["pioche"], [rot(t, -3.0 * bump(t, 0.0, 0.06, 0.1, 0.42)) for t in echant(L_BR, 20)])
piste(brk, OUT["corne"], [rot(t, 3 * math.sin(TAU * t / 0.12) * (1 - sm(t, 0.0, 0.4))) for t in echant(L_BR, 20)])
piste(brk, CTRL, [lum(t, 1.0 * bump(t, 0.0, 0.05, 0.12, 0.45)) for t in echant(L_BR, 20)])

ANIMS = [idle, sel, sw, hit, brk]

# ------------------------------------------------------------------ écriture
assert len(elements) <= 8192, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
GUI = float(os.environ.get("GUI", "0.84"))
AFFICHAGE = objet.affichage("pioche", gui={"scale": [GUI] * 3})
model = objet.modele(NOM, "pioche", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
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
for pc in (B_PIC, B_PAN):
    gm = min(float(pc.h(np.array([p]))[0] - Z_FOND) for p in pc.gax)
    marge = min(float(pc.dE(np.array([p]))[0] - pc.wb(np.array([p]))[0]) for p in pc.gl + pc.gr)
    print(f"{pc.nom} : {pc.L:.2f} px, profondeur mini de gouttière {gm:.2f} px, marge gouttière/biseau {marge:.2f} px")
