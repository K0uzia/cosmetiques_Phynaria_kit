"""Houe de givre : skin d'objet (guide 14) pour toutes les houes du joueur, ensemble Givre (thème Éléments). Design original.
Écrit skin_houe_givre.png, skin_houe_givre_e.png et .build/skin_houe_givre_brut.bbmodel à côté de ce script.
Point de départ : gen_skin_hache_givre.py (glace peau/âme, classe Bras, œil d'argent, manche, animations) ; technique de la
lame en travers dans son propre repère reprise du principe de skin_houe_orage (pas de son design).

Référence réelle (.claude/references/objets/houes.md) : houe à œil et col de cygne (œil qui prend le manche, col recourbé,
lame plate en travers de l'axe, fil trempé ; angle de travail lame/manche de 55 à 70°, la lame penchée vers la poignée pour
mordre puis tirer la terre). Ici une **houe en croissant** (lame en demi-lune : fil convexe, deux cornes qui reviennent vers le
col, dos creux), forme réelle des houes à lame en demi-lune qui tranchent les racines sous la surface.
Famille Givre (.claude/styles/givre.md ; références de set : skin_epee_givre, skin_pioche_givre, skin_hache_givre,
skin_pelle_givre en vrai volume) :
- glace = peau `trans_` mince autour d'une âme opaque de même forme (plans parallèles décalés de 0,2 px) qui porte un
  **éventail de givre** cyan (sept rayons nés de la racine qui s'ouvrent vers le fil, brindilles, calque _e) et les chevrons de
  taille ; fil blanc, bande claire le long des fils, fissures blanches fines ;
- argent froid pour la structure (œil, col de cygne octogonal qui s'affine, virole de la lame, hampe), flocon en relief (barres
  à section losange) et gemme hexagonale _e sur les deux faces de l'œil (comme la hache, le piolet, la pelle, la garde de
  l'épée) ; fusée de cuir bleu nuit cloutée d'argent ;
- cristal hexagonal pointu au bout de l'œil (le « bouton » de la houe vanilla) et à la pique.
Silhouette (reconnaissable sans la couleur) : crochet d'un seul côté terminé par un **croissant de lune** à deux cornes ; ni
croissant à deux bras (piolet), ni large auge (pelle), ni fer le long du manche (hache) ; différente de la houe de l'orage
(lame trapèze à dents d'éclair).
Vrai volume (recette .claude/references/objets/volume-3d.md, validée en jeu le 2026-11-08) : la lame est une plaque biseautée
fermée (deux biseaux par tronçon de bord et par face, pente unique 40°, tous les bords biseautés sauf la racine cachée dans la
virole ; plat incliné qui s'amincit de la racine vers le fil, 1,32 -> 0,56 px), faces échantillonnées texel par texel et
découpées par l'alpha ; contour de découpe = sommets du fil ; peau sans recouvrement, âme avec recouvrement 0,08.
**Lame dans son propre repère** (u de la racine vers le fil, w en travers, z selon la normale de ses plats), tournée de ROLL
autour de u : dans l'inventaire (vue de +Z) on voit son plat de biais, donc le croissant, et pas seulement sa tranche.
Repère (catégorie objets, Recette) : comme iron_hoe.png vu de +Z : manche du bas à gauche vers le haut à droite (axe a), col et
lame vers le haut à gauche (+b) ; boîte centrée dans le bloc. Display vanilla item/handheld, gui réglé à la case.

Objet vivant (guide 14), sobre (la glace ne plie pas) :
- item_idle (8 s) : un scintillement à la corne haute (2,4 s) puis à la corne basse (5,8 s) ;
- item_gui : rien ne bouge ;
- event_select (0,6 s) : la glace pousse depuis la virole (la lame), puis le cristal de l'œil ;
- event_swing (0,35 s) : le geste de labour (la lame pique de 3° puis revient) + éclat blanc au milieu du fil ; le labour
  (clic droit sur l'herbe) fait balancer le bras : il doit jouer event_swing (supposé) ;
- event_hit (0,5 s) : six aiguilles de givre jaillissent du fil + frisson ; **le seul son** (block.amethyst_block.chime) ;
- event_break (0,7 s) : la lame mord (+5°) puis tire la terre (−2,5°) ; la terre retournée se couvre de givre : six mottes de
  terre givrée sortent du fil, roulent et fondent, une étoile de givre s'ouvre au fil, gerbe de flocons emit_mc_snowflake
  (ctrl_emit +7 pendant 0,2 s, coupée sinon) ; sans son (on casse beaucoup de blocs).
Chaque groupe replié (scale) n'est déplié que par une seule animation (échelles superposées) ; pièces repliées à 1/10 sur un
pivot caché dans la glace au repos.
Fonctions avancées : trans_, add_, calque _e, scale, position et rotation animés, ctrl_emit + emit_mc_snowflake, animations
d'objet (item_idle, item_gui, event_select, event_swing, event_hit, event_break). À juger en jeu : la glace sur âme opaque avec
et sans shader, event_hit / event_break / event_swing au labour (pas encore vérifiés par le développeur), son d'un objet, scale
et position sur un objet, lecture du croissant dans la case et en main.
Une seule étape : groupe racine `repos`.
"""
import base64, io, json, math, os, random, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image, ImageDraw

NOM = "skin_houe_givre"
TEX = 512
TAU = 2 * math.pi
FOLD = 0.1

# Repère de l'image : a le long du manche (vers la tête), b en travers dans le plan de l'image (col vers +b), z épaisseur.
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


# ------------------------------------------------------------------ tête dans le plan de l'image (a, b ; px)
A_O = float(os.environ.get("A_O", "16.6"))   # centre de l'œil
R_OE = 1.25                  # apothème de l'œil (octogone)
Z_OE = 0.92                  # demi-épaisseur de l'œil
ANG = math.radians(float(os.environ.get("ANG", "60")))     # angle de travail : lame à 60° du manche, penchée vers la poignée
D_L = np.array((-math.cos(ANG), math.sin(ANG)))            # direction de la lame dans le plan (a, b)
N_L = np.array((D_L[1], -D_L[0]))                          # normale du dos de la lame dans le plan (côté +a)
NC = [(A_O, 0.0), (A_O + 0.6, 1.2), (A_O + 0.75, 2.15), (A_O + 0.3, 2.95)]   # axe du col de cygne
R_L = bez(NC, 1.0)[0]                                      # racine de la lame (bout du col)
ROLL = math.radians(float(os.environ.get("ROLL", "34")))  # lame tournée autour de son axe (plat visible dans l'inventaire)

# repère de la lame (u, w, z) -> monde (avant recentrage) ; e3 = e1 x e2 (direct)
E1 = unit(Wv(*D_L))
E2 = unit(math.cos(ROLL) * T_ + math.sin(ROLL) * Wv(*N_L))
E3 = np.cross(E1, E2)
CUR = ["img"]                 # repère des volumes en cours : "img" ou "lame"


def Lp(u, w=0.0, z=0.0):
    return Wp(*R_L) + E1 * u + E2 * w + E3 * z


def Lv(u, w=0.0, z=0.0):
    return E1 * u + E2 * w + E3 * z


# ------------------------------------------------------------------ dessin de la lame (repère de la lame : u, w ; px)
HS = float(os.environ.get("HS", "1.0"))     # échelle de la lame
O_ = np.zeros(2)             # racine de la lame (dans la virole)
R_COL = 0.7                  # rayon de la racine (référence de l'amincissement)


def rel(pts):
    return [(HS * u, HS * w) for u, w in pts]


# croissant (côté +w ; -w en miroir) : racine -> dos creux -> corne -> fil convexe -> milieu du fil
BZ_DOS = rel([(-0.25, 0.62), (1.15, 0.9), (1.6, 2.15), (0.6, 2.95)])
BZ_FIL = rel([(0.6, 2.95), (1.95, 3.65), (3.65, 2.6), (3.75, 0.0)])


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
T_BIS = 0.85                     # pente unique des biseaux (40°) : lame large, il reste un plat
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


class Bras:
    """Plaque biseautée : contour poly, fil (polyligne, sans la racine cachée dans la virole), plat z = h0 + k (P - O)·u."""

    def __init__(self, nom, poly, fil, u, h_racine, h_bout, L, centre):
        self.nom, self.poly, self.centre = nom, poly, centre
        self.u = unit(np.asarray(u, float))
        self.k = (h_bout - h_racine) / (L - R_COL)
        self.h0 = h_racine - self.k * R_COL
        self.L = L
        self.segs = subdiv(fil)

    def h(self, P):
        return self.h0 + self.k * ((np.asarray(P, float) - O_) @ self.u)

    def wb(self, P):
        return np.maximum((self.h(P) - Z_E) / T_BIS, 0.02)

    def dE(self, P):
        return d_stack(P, self.segs).min(0)

    def s(self, P):
        """0 à la racine -> 1 au fil."""
        return np.clip(((np.asarray(P, float) - O_) @ self.u) / self.L, 0, 1)

    def ame_ok(self, P):
        return self.h(P) - DELTA > ZC_MIN + 0.03


_DOS = resample(courbe(BZ_DOS), 0.85)
_FIL = resample(courbe(BZ_FIL), 0.85)
DEMI = _DOS + _FIL[1:]                                      # racine -> dos -> corne -> fil -> milieu du fil (côté +w)
# contour = exactement les sommets du fil (le bord de la racine, dans la virole, n'est pas biseauté)
P_LAME = DEMI + [(u, -w) for u, w in DEMI[::-1][1:]]
FIL_LAME = list(P_LAME)
CORNE = np.array(_DOS[-1])                                  # pointe de la corne +w
MID = np.array(_FIL[-1])                                    # milieu du fil
NRM_MID = np.array((1.0, 0.0))                              # normale sortante au milieu du fil
U_FER = np.array((1.0, 0.0))
L_FER = float(MID[0])


# éventail de givre : sept rayons nés près de la racine qui s'ouvrent vers le fil, brindilles en chevron (cœur cyan _e)
def _eventail():
    v = []
    org = np.array((0.35 * HS, 0.0))
    for k, ang in enumerate((-66, -44, -22, 0, 22, 44, 66)):
        e = np.array((math.cos(math.radians(ang)), math.sin(math.radians(ang))))
        r = 0.55
        while r < 6:
            P = org + e * (r + 0.1)
            if not in_poly(P[None], P_LAME)[0] or d_poly(P[None], P_LAME + [P_LAME[0]])[0] < 0.75:
                break
            r += 0.1
        if r < 1.0:
            continue
        p0, p1 = org + e * 0.55, org + e * r
        v.append([tuple(p0), tuple(p1)])
        for fr in (0.5, 0.78):
            if r * fr < 1.1:
                continue
            q = org + e * (r * fr)
            for sg in (1, -1):
                a2 = math.radians(ang + sg * 40)
                e2 = np.array((math.cos(a2), math.sin(a2)))
                v.append([tuple(q), tuple(q + e2 * (0.55 if fr < 0.6 else 0.4))])
    return v


VEINES = _eventail()
B_FER = Bras("lame", P_LAME, FIL_LAME, U_FER, 0.66, 0.28, L_FER, VEINES)

def proprietaire(D, idx):
    return np.argmin(D, axis=0) == idx


# --- motifs : chevrons de taille et fissures, dans le plan du fer
def d_veines(P2, veines):
    return np.min(np.stack([d_poly(P2, v) for v in veines]), axis=0)


def chevrons(pc, P2):
    db = d_veines(P2, pc.centre)
    return (np.floor((((P2 - O_) @ pc.u) * 0.75 + 2.2 * db) / 1.3) % 2) * 2 - 1


def _fissures(seed):
    r = np.random.default_rng(seed)
    A0, A1, B0, B1, D = -0.6, 4.2, -3.8, 3.8, 40.0
    Wd, Hd = int((A1 - A0) * D), int((B1 - B0) * D)
    im = Image.new("L", (Wd, Hd), 0)
    d = ImageDraw.Draw(im)

    def px(a, b):
        return ((a - A0) * D, (B1 - b) * D)
    n = 0
    while n < 9:
        P = np.array((r.uniform(0.5, 3.4), r.uniform(-2.9, 2.9)))
        if (not in_poly(P[None], P_LAME)[0] or d_poly(P[None], FIL_LAME)[0] < 0.6 or np.linalg.norm(P - O_) < 0.9
                or d_veines(P[None], VEINES)[0] < 0.3):
            continue
        n += 1
        pl = [tuple(P)]
        ang = r.uniform(0, TAU)
        for j in range(3):
            ang += r.uniform(-0.7, 0.7)
            ln = r.uniform(0.2, 0.42)
            pl.append((pl[-1][0] + math.cos(ang) * ln, pl[-1][1] + math.sin(ang) * ln))
        d.line([px(*p) for p in pl], fill=255, width=3)
    return np.array(im) > 127, (A0, B1, D)

FISS = {sg: _fissures(41 + (sg > 0)) for sg in (1, -1)}


def fissure(P2, sg):
    im, (A0, B1, D) = FISS[sg]
    i = np.clip(((B1 - P2[..., 1]) * D).astype(int), 0, im.shape[0] - 1)
    j = np.clip(((P2[..., 0] - A0) * D).astype(int), 0, im.shape[1] - 1)
    return im[i, j]


# --- peintures : (couleur, alpha | None, émissif | None)
def peau_plat(pc, P2, d, sg):
    s = pc.s(P2)[..., None]
    g = chevrons(pc, P2)[..., None]
    col = lerp(C(104, 192, 236), C(168, 226, 250), s) * (1 + 0.05 * g)
    al = 142 + 34 * s[..., 0] + 6 * g[..., 0]
    fis = fissure(P2, sg)
    arete = d < pc.wb(P2) + 0.07
    for m, c, a in ((fis, BLANC, 212), (arete, BLANC, 212)):
        col = np.where(m[..., None], c, col)
        al = np.where(m, a, al)
    return col, al, None


def peau_biseau(pc, P2, d, sg):
    f = d / pc.wb(P2)
    g = chevrons(pc, P2)
    col = lerp(C(196, 238, 255), C(140, 208, 242), np.clip(f, 0, 1)[..., None]) * (1 + 0.04 * g)[..., None]
    al = 168 + 22 * pc.s(P2) + 8 * g
    frange = d < D_OFF + 0.04                      # pas d'âme derrière : glace claire plus dense, pas de vide
    for m, c, a in ((frange, C(206, 240, 255), 214), (f > 0.88, BLANC, 212), (f < 0.16, BLANC, 228)):
        col = np.where(m[..., None], c, col)
        al = np.where(m, a, al)
    return col, al, None


def peau_fil(pc, P2, d, sg):
    return np.zeros(P2.shape[:-1] + (3,), np.float32) + BLANC, np.full(P2.shape[:-1], 226.0), None


def ame_plat(pc, P2, d, sg):
    s = pc.s(P2)
    k1 = np.clip(s / 0.25, 0, 1)[..., None]
    k2 = np.clip((s - 0.25) / 0.75, 0, 1)[..., None]
    col = lerp(lerp(G_DEEP, G_BODY, k1), G_PALE, k2 * 0.6)
    db = d_veines(P2, pc.centre)
    col = col * (0.64 + 0.25 * np.clip(d / 0.9, 0, 1))[..., None]
    col = col * (1 + 0.07 * chevrons(pc, P2))[..., None]
    em = np.zeros(col.shape, np.float32)
    cw = 0.2 * (1 - 0.45 * s)
    halo = db < cw + 0.12
    col[halo] = lerp(col[halo], C(150, 226, 250), 0.55)
    coeur = db < cw
    col[coeur] = lerp(C(205, 248, 255), C(120, 214, 246), np.clip(db[coeur] / cw[coeur], 0, 1)[..., None])
    em[coeur] = LUEUR
    fis = fissure(P2, sg)
    col[fis & ~coeur] = lerp(col[fis & ~coeur], BLANC, 0.35)
    col[d < pc.wb(P2) + D_EXTRA + 0.06] = G_DEEP * 0.8
    return col, None, em


def ame_biseau(pc, P2, d, sg):
    wb = pc.wb(P2) + D_EXTRA
    f = np.clip((d - D_OFF) / np.maximum(wb - D_OFF, 0.05), 0, 1)[..., None]
    col = lerp(G_PALE, G_BODY, f * 0.8) * (1 + 0.05 * chevrons(pc, P2))[..., None]
    return col, None, None


def ame_fil(pc, P2, d, sg):
    return np.zeros(P2.shape[:-1] + (3,), np.float32) + G_LIGHT, None, None


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
        P_, V_ = (Lp, Lv) if CUR[0] == "lame" else (Wp, Wv)
        CUBES.append({"groupe": groupe, "nom": nom, "c": P_(*c), "R": np.column_stack([V_(*X), V_(*Y), V_(*Z)]),
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
        e0 = wmax * 1.6 if v0 else 0.04
        e1 = wmax * 1.6 if v1 else 0.04
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
                own = (D[idx] <= de + RECOUV_AME) if ame else proprietaire(D, idx)
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
# cristal au bout de l'œil (le « bouton » de la houe vanilla) : (angle depuis +a vers +b (deg), inclinaison z (deg), longueur, rayon)
COURONNE = [(-4, 0, 2.0, 0.42)]
# mottes de terre givrée (event_break) : (position le long du fil w, écart en travers (deg), élévation vers la face intérieure
# (deg), distance, tour (deg), taille)
MOTTES = [(-1.9, -22, 48, 3.8, 260, 0.74), (-0.9, -10, 62, 4.6, -300, 0.88), (0.1, 3, 52, 5.2, 340, 0.96),
          (1.0, 12, 66, 4.4, -260, 0.84), (1.9, 24, 44, 3.6, 300, 0.7), (0.5, 6, 34, 5.8, -320, 0.62)]
# aiguilles de event_hit : position le long du fil (w), longueur
AIGUILLES = [(-2.1, 1.4), (-1.3, 1.75), (-0.45, 2.05), (0.45, 2.0), (1.3, 1.7), (2.1, 1.35)]
OUT = {}


def fil_en(w):
    """Point du fil (côté convexe) à la hauteur w, et sa normale sortante (repère de la lame)."""
    F = np.array(_FIL)
    sg = 1 if w >= 0 else -1
    ws = F[:, 1]
    i = int(np.argmin(np.abs(ws - abs(w))))
    i = min(max(i, 1), len(F) - 2)
    p = F[i] * np.array((1, sg))
    t = unit((F[i + 1] - F[i - 1]) * np.array((1, sg)))
    n = np.array((t[1], -t[0]))
    if n[0] < 0:
        n = -n
    return p, n


def t_terre(nom, N=12):
    """Terre retournée prise par le givre : brun sombre, cristaux blancs serrés sur le haut."""
    r = np.random.default_rng(len(nom) + 3)
    yy, xx = np.mgrid[0:N, 0:N]
    q = (yy + 0.5) / N
    col = lerp(C(104, 78, 58), C(52, 38, 30), (q ** 1.2)[..., None]) * r.uniform(0.9, 1.08, (N, N))[..., None]
    givre = (r.uniform(0, 1, (N, N)) < 0.75 - q * 0.8)
    col[givre] = lerp(C(214, 238, 250), BLANC, r.uniform(0, 1, givre.sum())[..., None])
    return tuile(nom, *finir(col, None, None, np.ones((N, N), bool)))


def t_flocon_add(nom, N=64):
    """Étoile de givre additive (six branches et leurs barbes), noir = invisible."""
    yy, xx = np.mgrid[0:N, 0:N]
    P = np.stack([((xx + 0.5) / N - 0.5) * 2, (0.5 - (yy + 0.5) / N) * 2], -1)
    k = np.zeros((N, N))
    for j in range(6):
        th = TAU * j / 6
        e = np.array((math.cos(th), math.sin(th)))
        segs = [((0, 0), tuple(e * 0.95))]
        for fr, ln in ((0.45, 0.3), (0.7, 0.2)):
            for sg in (1, -1):
                t2 = th + sg * math.radians(55)
                segs.append((tuple(e * fr), tuple(e * fr + np.array((math.cos(t2), math.sin(t2))) * ln)))
        for a, b in segs:
            dd = d_poly(P, [a, b])
            k = np.maximum(k, np.exp(-(dd / 0.045) ** 2))
    r = np.hypot(P[..., 0], P[..., 1])
    k = np.clip(k * (1 - 0.4 * r) + np.exp(-r * 7) * 0.8, 0, 1)
    col = lerp(C(0, 0, 0), C(196, 238, 255), k[..., None] ** 0.9)
    return tuile(nom, *finir(col, None, None, np.ones((N, N), bool)))


def motte(g, nom, c, taille, tiles, seed):
    """Motte en volume : une boîte + la même tournée de 45° autour d'un axe (bloc aux arêtes abattues)."""
    rng = np.random.default_rng(seed)
    v = unit(rng.normal(size=3))
    w = unit(np.cross(v, unit(rng.normal(size=3))))
    R0 = np.column_stack([v, w, np.cross(v, w)])
    a = math.radians(45)
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    for k, (R, sc) in enumerate(((R0, (1.0, 0.86, 0.8)), (R0 @ Rx, (0.9, 0.74, 0.74)))):
        CUBES.append({"groupe": g, "nom": f"{nom}{'ab'[k]}", "c": np.asarray(c, float), "R": R,
                      "half": np.array(sc) * taille / 2, "faces": {f: tiles[(k + i) % 2] for i, f in enumerate(SIX)}})


def conception():
    racine = grp(objet.etape("repos", "houe"), Wp(A_O), None)
    houe = grp("houe", Wp(4.5), racine)                     # pivot dans la main : le geste de labour
    # --- manche : pique de cristal, virole, fusée de cuir cloutée, virole, hampe d'argent jusqu'à l'œil
    manche = grp("manche", Wp(3.0), houe)
    t_cuir()
    hampe_t = t_unie("hampe", 48, 12, ARG_M, ARG_D, ligne=ARG_L)
    bar8(manche, "fusee", Wp(0.55), Wp(6.35), 0.56, "cuir")
    tour(manche, "virole_bas", Wp(0), A_, W_, bague(-0.05, 0.6, 0.48, 0.70, 0.62), n=8, phase=math.pi / 8)
    tour(manche, "virole_haut", Wp(0), A_, W_, bague(6.3, 6.95, 0.62, 0.70, 0.50), n=8, phase=math.pi / 8)
    bar8(manche, "hampe", Wp(6.9), Wp(A_O - 0.6), 0.47, hampe_t)
    tour(manche, "bague_gorge", Wp(0), A_, W_, bague(A_O - 3.0, A_O - 2.45, 0.50, 0.62, 0.50), n=8, phase=math.pi / 8)
    pique = grp("pique", Wp(0.0), manche)
    tour(pique, "pique", Wp(-0.05), -A_, W_, [(0.0, 0.46, 0.14, 0.52, GLACE_ALT), (0.14, 0.52, 0.75, 0.52, GLACE_ALT),
                                              (0.75, 0.52, 2.15, 0.0, GLACE_ALT)], n=6)
    # --- tête : œil octogonal d'argent (axe z), couvercles, flocons en relief, gemmes
    tete = grp("tete", Wp(A_O), houe)
    tour(tete, "oeil", Wp(A_O), T_, A_, bague(-Z_OE, Z_OE, R_OE - 0.18, R_OE, R_OE - 0.18, c=0.16), n=8, phase=math.pi / 8)
    td = t_disque("disque_oeil", 8, R_OE - 0.18)
    bras_t = t_unie("bras", 32, 8, ARG_L, ARG_M, ligne=BLANC)
    cap_t = t_unie("bras_bout", 8, 8, BLANC, ARG_M)
    fb = {f: bras_t for f in ("south", "north", "up", "down")}
    fb.update(east=cap_t, west=cap_t)
    for s in (1, -1):
        cs = "e" if s > 0 else "i"
        fl = grp(f"flocon_{cs}", Wp(A_O, 0, s * Z_OE), tete)
        disque(fl, f"couvercle_{cs}", Wp(A_O, 0, s * Z_OE), T_ * s, A_, 8, R_OE - 0.18, td)
        zc = s * (Z_OE + 0.04)
        Rf = 1.1
        for k in range(3):
            th = math.radians(90 + 60 * k)
            e = math.cos(th) * A_ + math.sin(th) * W_
            barre(fl, f"bras_{cs}{k}", Wp(A_O, 0, zc) - e * Rf, Wp(A_O, 0, zc) + e * Rf, 0.12, 45, fb)
        for k in range(6):
            th = math.radians(90 + 60 * k)
            e = math.cos(th) * A_ + math.sin(th) * W_
            for fr, ln in ((0.55, 0.33), (0.82, 0.22)):
                base = Wp(A_O, 0, zc + s * 0.01) + e * Rf * fr
                for sg in (-1, 1):
                    t2 = th + sg * math.radians(55)
                    e2 = math.cos(t2) * A_ + math.sin(t2) * W_
                    barre(fl, f"branche_{cs}{k}{'pm'[sg < 0]}{int(fr * 10)}", base - e2 * 0.05, base + e2 * ln, 0.075, 45, fb)
        tour(fl, f"gemme_{cs}", Wp(A_O, 0, s * Z_OE), T_ * s, A_,
             [(0.0, 0.34, 0.2, 0.34, [("gemme", {"clair": 0.1}), ("gemme", {"clair": -0.1})]),
              (0.2, 0.34, 0.44, 0.0, [("gemme", {"clair": 0.2}), ("gemme", {})])], n=6, partage="gemme")
    # cristal au bout de l'œil (le « bouton » de la houe vanilla)
    OUT["couronne"] = []
    for i, (ang, tilt, L, r) in enumerate(COURONNE):
        th, tl = math.radians(ang), math.radians(tilt)
        d = unit(A_ * math.cos(th) + W_ * math.sin(th) + T_ * math.tan(tl))
        base = Wp(A_O) + d * (R_OE - 0.35)
        cg = grp(f"cristal_{i + 1}", base, tete)
        tl_ = min(L * 0.45, r * 1.9)
        tour(cg, cg, base, d, T_, [(0.0, r * 0.8, 0.2, r, GLACE_ALT), (0.2, r, L - tl_, r, GLACE_ALT),
                                    (L - tl_, r, L, 0.0, GLACE_ALT)], n=6, phase=math.pi / 6)
        OUT["couronne"].append(cg)
    # --- col de cygne d'argent : barre octogonale qui s'affine, de l'œil à la virole de la lame
    col = grp("col", Wp(A_O), tete)
    ss = np.linspace(0.18, 1.0, 7)
    for i in range(len(ss) - 1):
        p, q = bez(NC, ss[i])[0], bez(NC, ss[i + 1])[0]
        r = 0.58 - 0.16 * (ss[i] + ss[i + 1]) / 2
        bar8(col, f"col{i}", Wp(*p), Wp(*q), r, hampe_t, ov=0.07)
    # virole de la lame (axe E1) : cache la racine du croissant
    tour(col, "virole_lame", Wp(*R_L), E1, E2, bague(-0.42, 0.34, 0.5, 0.96, 0.8, c=0.14), n=8, phase=math.pi / 8)
    tour(col, "givre_virole", Wp(*R_L), E1, E2, [(0.34, 0.8, 0.46, 0.6, [("glace", {"clair": 0.15})])], n=8, phase=math.pi / 8)
    # --- lame en croissant : peau de glace trans_ + âme opaque, dans son propre repère ; pivot à la racine (elle pousse de là)
    g = grp("lame", Lp(0.0), col)
    CUR[0] = "lame"
    volume(B_FER, grp("ame_lame", Lp(0.0), g), True)
    volume(B_FER, grp("trans_lame", Lp(0.0), g), False)
    CUR[0] = "img"
    # --- effets repliés (un dépliage par animation), pivots cachés dans la glace
    et = t_etoile("etoile")
    nw = unit(Lv(*NRM_MID))
    reps = []
    for nm, sg in (("add_scint_haut", 1), ("add_scint_bas", -1)):
        cn = CORNE * np.array((1, sg))
        c = Lp(*(cn + unit(np.array((1.9, 0.0)) - cn) * 0.42))
        g = grp(nm, c, tete)
        plaque_add(g, f"{nm}_a", c, E1, E2, 1.8, et)
        plaque_add(g, f"{nm}_b", c, E3, E2, 1.4, et)
        OUT[nm] = g
        reps.append(g)
    midw = Lp(*MID)
    g = grp("add_coup", midw - nw * 0.3, tete)
    plaque_add(g, "add_coup_a", midw - nw * 0.3, E1, E2, 2.8, et)
    plaque_add(g, "add_coup_b", midw - nw * 0.3, E3, E2, 2.2, et)
    OUT["add_coup"] = g
    reps.append(g)
    # étoile de givre de event_break (la terre retournée se couvre de givre)
    fl_t = t_flocon_add("flocon_add")
    g = grp("add_givre", midw - nw * 0.4, tete)
    plaque_add(g, "add_givre_a", midw - nw * 0.4, E2, E3, 4.2, fl_t)
    plaque_add(g, "add_givre_b", midw - nw * 0.4, E1, E2, 3.0, fl_t)
    OUT["add_givre"] = g
    reps.append(g)
    # aiguilles de givre (event_hit) : six cristaux fins nés du fil, en éventail le long de la courbe
    piv_f = Lp(MID[0] - 0.5, 0.0)
    OUT["aiguilles"] = grp("aiguilles", piv_f, tete)
    reps.append(OUT["aiguilles"])
    for j, (w, L) in enumerate(AIGUILLES):
        p, n2 = fil_en(w)
        el = math.radians(24 if j % 2 == 0 else -14)
        d = unit(Lv(n2[0], n2[1], 0.0) + E3 * math.tan(el))
        tour(OUT["aiguilles"], f"aiguille{j}", Lp(*(p - n2 * 0.3)), d, E3,
             [(0.0, 0.10, L * 0.6, 0.15, GLACE_MAT), (L * 0.6, 0.15, L, 0.0, GLACE_MAT)], n=6, partage=f"aig{j % 3}")
    # mottes de terre givrée (event_break) : cachées dans la glace au repos, partent du fil vers la face intérieure (côté manche)
    f_in = E3 if E3 @ (-A_) > 0 else -E3
    tt = [t_terre("terre_a"), t_terre("terre_b", 10)]
    piv_m = Lp(MID[0] - 1.0, 0.0)
    OUT["mottes"] = []
    for j, (w, an, el, dist, tr, taille) in enumerate(MOTTES):
        gm = grp(f"motte_{j}", piv_m, tete)
        p, n2 = fil_en(w)
        a, e = math.radians(an), math.radians(el)
        dn = unit(Lv(n2[0], n2[1], 0.0))
        d = unit((dn * math.cos(a) + E2 * math.sin(a)) * math.cos(e) + f_in * math.sin(e))
        c0 = Lp(*(p - n2 * 0.5))
        motte(gm, f"motte{j}", c0, taille, tt, 11 + j)
        OUT["mottes"].append((gm, d * dist, tr))
        reps.append(gm)
    OUT["replies"] = reps
    OUT["tipw"], OUT["tdw"] = midw, nw
    OUT["racine"], OUT["houe"], OUT["tete"] = racine, houe, tete
    return racine


RACINE = conception()

# ------------------------------------------------------------------ recentrage, repli, atlas
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


REPLIES = OUT["replies"]
_fixes = [cb for cb in CUBES if cb["groupe"] not in REPLIES]
_Pc = coins_cubes(_fixes)
DEC = np.array((8.0, 8.0, 8.0)) - (_Pc.min(0) + _Pc.max(0)) / 2
for cb in CUBES:
    cb["c"] = cb["c"] + DEC
GROUPES = [(n, p + DEC, par) for n, p, par in GROUPES]
OUT["tipw"] = OUT["tipw"] + DEC
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


# item_idle (8 s) : scintillement à la corne haute, puis à la corne basse ; émetteur coupé.
idle = anim("item_idle", 8.0, "loop")
piste(idle, OUT["add_scint_haut"], pop(2.4, 0.5, 8.0))
piste(idle, OUT["add_scint_bas"], pop(5.8, 0.45, 8.0, 0.9))
emit(idle, [kf("position", 0, -1, 0, 0), kf("position", 8.0, -1, 0, 0)])

# item_gui : rien ne bouge, émetteur coupé.
gui = anim("item_gui", 4.0, "loop")
emit(gui, [kf("position", 0, -1, 0, 0), kf("position", 4.0, -1, 0, 0)])

# event_select (0,6 s) : la glace pousse depuis la virole (le croissant), puis le cristal de l'œil.
L_SEL = 0.6
sel = anim("event_select", L_SEL)
piste(sel, "lame", pousse(0.0, 0.32))
for i, cg in enumerate(OUT["couronne"]):
    piste(sel, cg, pousse(0.22 + 0.06 * i, 0.24, 1.12))

# event_swing (0,35 s) : le geste de labour (la lame pique de 3° puis revient), éclat blanc au milieu du fil.
L_SW = 0.35
sw = anim("event_swing", L_SW)
piste(sw, OUT["houe"], [kf("rotation", t, 0, 0, 3.0 * sm(t, 0.0, 0.08) * (1 - sm(t, 0.1, 0.32))) for t in echant(L_SW, 14)])
piste(sw, OUT["add_coup"], pop(0.07, 0.2, L_SW))

# event_hit (0,5 s) : le givre jaillit du fil (aiguilles qui sortent puis rentrent) + frisson ; seul son.
L_HIT = 0.5
hit = anim("event_hit", L_HIT)
ks = [kf("scale", 0.0, 1.0)]
for t in echant(L_HIT, 20)[1:]:
    v = 1 + (DEPLIE * 1.05 - 1) * sm(t, 0.0, 0.06) * (1 - sm(t, 0.22, 0.42))
    ks.append(kf("scale", t, v))
piste(hit, OUT["aiguilles"], ks)
piste(hit, OUT["tete"], [kf("rotation", t, 0, 0, 1.6 * math.sin(TAU * t / 0.08) * (1 - sm(t, 0.0, 0.26))) for t in echant(0.28, 14)]
      + [kf("rotation", L_HIT, 0, 0, 0)])

# event_break (0,7 s) : la lame mord (+5°) puis tire la terre (−2,5°) ; six mottes de terre givrée roulent vers la poignée et
# fondent, l'étoile de givre s'ouvre au fil ; gerbe de flocons.
L_BR = 0.7
brk = anim("event_break", L_BR)
rk = []
for t in echant(L_BR, 14):
    th = 5.0 * sm(t, 0.0, 0.1) * (1 - sm(t, 0.12, 0.3)) - 2.5 * bump(t, 0.14, 0.3, 0.38, 0.62)
    rk.append(kf("rotation", t, 0, 0, th))
piste(brk, OUT["houe"], rk)
piste(brk, OUT["add_givre"], pop(0.1, 0.55, L_BR, 1.0))
for j, (g, vec, tr) in enumerate(OUT["mottes"]):
    t0 = 0.12 + 0.015 * (j % 4)
    sk, pk, rr = [], [], []
    for t in echant(L_BR, 14):
        u = max(0.0, t - t0) / (L_BR - t0)
        vol = 1 - (1 - u) ** 2.0                                     # départ rapide, freine
        tomb = 2.6 * u * u                                           # la terre retombe
        sc = 1.0 if t < t0 else 1 + (DEPLIE - 1) * sm(u, 0.0, 0.08) * (1 - sm(u, 0.62, 1.0))
        pos = vec * vol + np.array((0.0, -tomb, 0.0))
        sk.append(kf("scale", t, sc))
        pk.append(kf("position", t, *[float(v) for v in pos]))
        rr.append(kf("rotation", t, tr * vol * 0.3, tr * vol * 0.5, tr * vol * 0.2))
    sk[-1] = kf("scale", L_BR, 1.0)
    pk[-1] = kf("position", L_BR, 0, 0, 0)
    rr[-1] = kf("rotation", L_BR, 0, 0, 0)
    piste(brk, g, sk + pk + rr)
emit(brk, [kf("position", 0, -1, 0, 0), kf("position", 0.1, 7, 0, 0), kf("position", 0.3, 7, 0, 0), kf("position", 0.31, -1, 0, 0),
           kf("position", L_BR, -1, 0, 0)])

ANIMS = [idle, gui, sel, sw, hit, brk]

# ------------------------------------------------------------------ écriture
assert 150 <= len(elements) <= 3000, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
GUI = float(os.environ.get("GUI", "0.84"))
AFFICHAGE = objet.affichage("houe", gui={"scale": [GUI] * 3})
model = objet.modele(NOM, "houe", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
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
D_ = np.array((1, 1, 0)) / math.sqrt(2)
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur le long du manche {float((P @ D_).max() - (P @ D_).min()):.1f} px ; boîte {P.min(0).round(2)} .. {P.max(0).round(2)}")
print(f"âme : bord à {D_OFF:.3f} px du fil, arête +{D_EXTRA:.3f} ; lame {L_FER:.2f} px, plat {B_FER.h(MID[None])[0]*2:.2f} px au milieu du fil, {B_FER.h(np.zeros((1,2)))[0]*2:.2f} à la racine")

