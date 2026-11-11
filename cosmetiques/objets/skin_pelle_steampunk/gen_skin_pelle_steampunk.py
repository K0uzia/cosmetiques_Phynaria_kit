"""Pelle de chauffe : skin d'objet (guide 14) pour toutes les pelles du joueur, ensemble Steampunk (thème Mécanique). Design original.
Écrit skin_pelle_steampunk.png, skin_pelle_steampunk_e.png et .build/skin_pelle_steampunk_brut.bbmodel à côté de ce script.
Point de départ : gen_skin_hache_steampunk.py (classe Fer opaque, roue dentée, cadran, tours, peintures, animations) ; fer en bout
rond dans l'axe comme gen_skin_pelle_abyssal.py (gouttière axiale).

Idée (fiche .claude/references/objets/pelles.md : poignée en D, manche, douille, col et « frog », fer à bout rond, nervure, fil) :
une pelle de terrassier de chaudronnier, où la vapeur sert au circuit de pression comme sur les autres outils du set.
- **Poignée en D** de laiton (deux branches tournées) à traverse de cuir cousu de laiton : la silhouette « pelle » au talon ;
- manche de bois sombre ; **chaudière de cuivre rivetée** au milieu du manche (cerclages de laiton), porte de foyer à fentes
  rougeoyantes sur les deux faces, soupape sur le flanc -b, en haut quand on la tient (la vapeur monte) ;
- tuyau de cuivre à colliers de la chaudière à la roue (il porte la pression au manomètre) ;
- « frog » = **roue dentée de laiton** dans le plan du fer (signature de l'épée et de la hache), manomètre ambre sur les deux
  faces, une seule aiguille ; dents retirées là où passent fer, manche et tuyau ;
- fer = **plaque d'acier bruni en vrai volume** (recette .claude/references/objets/volume-3d.md) : épaules larges presque droites,
  flancs presque parallèles, **bout rond** (demi-largeur 2,9 px : pelle, pas lance ni raquette) ; plat plan incliné 1,60 -> 0,54 px
  vers le bout, pente unique 40°, racine cachée dans la roue ; fil poli au bout seulement, épaules et flancs bordés de laiton ;
  nervure = gouttière creusée dans l'axe (lèvre et filet de laiton) ; trois rivets de sertissage peints au col.
Lumière _e seulement sur des sources logiques : verre ambre des deux cadrans, fentes des deux portes de foyer.

Repère (catégorie objets, Recette) : comme iron_shovel.png vu de +Z, manche du bas à gauche vers le haut à droite, fer en haut à
droite ; boîte centrée dans le bloc ; Display vanilla item/handheld (tools/objet.py), échelle gui ramenée à la case. Étape `repos`.

Objet vivant (guide 14), sobre, « saccadé mécanique » :
- item_idle (24 s) : la pression monte par crans (échelon, dépassement, rappel), la soupape tremble puis se soulève ; deux
  décharges : bouffée modélisée qui monte (`trans_bouffee`, **seul dépliage par scale** du modèle) + white_smoke par ctrl_emit ;
  **seul son** block.fire.extinguish à 22,02 s, une fois par boucle (outil : une décharge au repos, ligne Langage du set) ;
- item_swing (0,3 s, en boucle pendant qu'on creuse) : l'aiguille tremble, la soupape frémit, vapeur coupée ;
- event_select (0,8 s) : arrivée en main : l'aiguille fait son tour d'essai par crans, la soupape claque une fois ;
- event_swing (0,4 s) : l'aiguille perd un cran et remonte ;
- event_break (0,7 s) : la pelletée : le fer se relève de 5° autour de la roue puis revient, l'aiguille perd un cran, la soupape
  claque, white_smoke (ctrl_emit +4) ; sans son ni dépliage.
Aucun son sur event_use_start ni event_enter_*, ni aux événements. Pas d'item_gui (figé, net dans l'inventaire).
Bouffée cachée au repos : géométrie F_GEO / K sous le chapeau de la soupape, l'animation l'agrandit (clés scale <= 8).

Fonctions avancées : calque _e (cadrans, fentes des foyers), trans_bouffee, emit_mc_white_smoke, ctrl_emit, scale animé, animations
d'objet. Non simulés par l'aperçu : animations en main, particules, ctrl_emit, son. À juger en jeu : item_swing et event_break (pas
encore vérifiés par le développeur), le son d'un objet, le fer par la tranche et dans la case.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

AVEC_E = True
NOM = "skin_pelle_steampunk"
TEX = 512
TAU = 2 * math.pi
K = 16.0            # facteur de réduction du jet au repos
F_GEO = 2.0         # géométrie F_GEO / K, clés scale <= K / F_GEO

# Repère : a le long du manche (vers la tête), b en travers dans le plan de l'image (fil vers +b), z épaisseur (+Z = inventaire).
A_ = np.array((1.0, 1.0, 0.0)) / math.sqrt(2)
W_ = np.array((-1.0, 1.0, 0.0)) / math.sqrt(2)
T_ = np.array((0.0, 0.0, 1.0))


def Wp(a, b=0.0, z=0.0):
    return A_ * a + W_ * b + T_ * z


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
    x = (t - a) / (b - a)
    return x * x * (3 - 2 * x)


def smv(t, a, b):
    x = np.clip((np.asarray(t, float) - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def A(c):
    return np.array(c, np.float32)


# Palette du set (ligne Langage ; métal propre, brossé ±5 % au plus)
BRASS = dict(hi=A((236, 196, 112)), base=A((190, 142, 64)), low=A((112, 76, 32)))
COPPER = dict(hi=A((232, 150, 96)), base=A((176, 92, 52)), low=A((98, 46, 26)))
STEEL = dict(hi=A((136, 140, 150)), base=A((78, 82, 92)), low=A((38, 40, 48)))
WOOD = dict(hi=A((122, 78, 46)), base=A((84, 50, 30)), low=A((40, 22, 14)))
LEATHER = dict(hi=A((150, 96, 60)), base=A((104, 62, 36)), low=A((60, 34, 20)))
FIL = A((220, 224, 232))
POLI = A((176, 180, 190))
PLAT = A((146, 150, 160))       # plat du fer : acier clair (en sombre, un fer d'acier ne se lit pas dans la case : pioche du set)
AMBRE = A((255, 210, 120))
AMBRE_B = A((220, 150, 50))
VAPEUR = A((250, 250, 248))
VAPEUR_B = A((220, 224, 228))

# ------------------------------------------------------------------ dessin (plan a, b ; px)
A_O = 11.7                           # centre de la roue dentée (le « frog » entre douille et fer)
O_ = np.array((A_O, 0.0))
R_RIM, R_DENT, GZ, TZ = 1.6, 2.12, 0.92, 0.64   # roue : rayon du flanc, bout des dents, demi-épaisseur, demi-épaisseur des dents
R_COL = R_RIM                        # le fer naît dans la roue (racine cachée)
RB = 0.95                            # chaudière du manche
EP = 0.9                             # tuyau le long du manche (côté -b)
S_B0, S_B1 = 5.0, 7.7                # chaudière de cuivre (le long du manche)
S_V = 6.75                           # soupape sur le flanc haut (en main) de la chaudière
S_GRIP0 = 2.6                        # haut de la poignée en D (fourche sur le manche)
VALVE = -W_                          # soupape et vapeur : côté -b = HAUT en main (mesuré au rendu : +b descend en 3e personne)


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


# Fer de pelle à bout rond : col étroit dans la roue, épaules larges presque droites (là où le pied appuie), flancs presque
# parallèles qui se resserrent à peine, bout rond (le fil, seul poli). Demi-largeur 2,9 px : il se lit comme une pelle.
FLANC_P = catmull([(12.2, 0.78), (13.05, 0.9), (13.45, 1.6), (13.75, 2.45), (14.15, 2.86), (15.1, 2.9), (16.3, 2.76),
                   (17.3, 2.5)], 6)
BOUT = catmull([(17.3, 2.5), (18.3, 2.05), (19.1, 1.38), (19.65, 0.72), (19.95, 0.2), (20.03, 0.0), (19.95, -0.2),
                (19.65, -0.72), (19.1, -1.38), (18.3, -2.05), (17.3, -2.5)], 6)
FLANC_M = [(a_, -b_) for a_, b_ in FLANC_P[::-1]]


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


def hors_collet(pts, marge=0.45):
    for i, p in enumerate(pts):
        if np.linalg.norm(np.array(p) - O_) >= R_COL - marge:
            return pts[max(0, i - 1):]
    return pts


# ------------------------------------------------------------------ vrai volume (acier plein, opaque)
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
    """Plaque biseautée fermée (skin_hache_steampunk, gouttière axiale de skin_pelle_abyssal) : contour poly, fils (sans la racine
    cachée dans la roue), plat z = h0 + k (P - O)·u ; bout = seul bord poli, épaules et flancs bordés de laiton ; nervure creusée
    dans l'axe."""

    def __init__(self, nom, poly, fil, tranchant, nus, u, h_racine, h_bout, g0, g1, gw):
        self.nom, self.poly = nom, poly
        self.u = unit(u)
        pa = np.array(poly) - O_
        s_ = pa @ self.u
        self.L = float(s_.max())
        s_r = 1.0
        self.k = (h_bout - h_racine) / (self.L - s_r)
        self.h0 = h_racine - self.k * s_r
        self.segs = subdiv(fil)
        self.tranchant, self.nus = tranchant, nus
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
        # reflets : une ligne au milieu de chaque pan, entre la nervure et le flanc
        self.centres = [[(a_, sg * 1.45) for a_ in np.linspace(14.6, 17.8, 8)] for sg in (1, -1)]

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
        """1 si le bord le plus proche est le bout (fil poli), 0 aux épaules et aux flancs (bordés de laiton)."""
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


FLP_R, BOUT_R, FLM_R = resample(FLANC_P, 0.9), resample(BOUT, 0.9), resample(FLANC_M, 0.9)
POLY = FLP_R + BOUT_R[1:] + FLM_R[1:]            # fermé par la racine (dans la roue)
FLP_F = hors_collet(FLP_R)
FLM_F = hors_collet(FLM_R[::-1])[::-1]
FIL_FER = FLP_F + BOUT_R[1:] + FLM_F[1:]
FER = Fer("fer", POLY, FIL_FER, BOUT_R, [FLP_F, FLM_F], (1.0, 0.0), 0.80, 0.27, 14.45, 18.35, 0.24)
RIVETS = [tuple(O_ + 2.05 * np.array((math.cos(math.radians(a)), math.sin(math.radians(a))))) for a in (-24, 0, 24)]


def brosse(P, seed=0.0):
    """Brossé fin parallèle au fil (±4 %)."""
    s, r = P[..., 0], P[..., 1]
    return (np.sin((s * 0.35 + r) * 41.0 + seed) * 0.5 + np.sin((s * 0.35 + r) * 17.0 + s * 0.6 + seed * 3) * 0.5) * 0.04


# --- peintures du fer (acier bruni clair, fil poli au tranchant, bords de laiton ailleurs ; aucune lumière)
def peint_biseau(pc, P2, d, sg):
    f = np.clip(d / pc.wb(P2), 0, 1.2)[..., None]
    act = pc.actif(P2)[..., None]
    col = lerp(FIL, POLI, np.clip((f - 0.12) / 0.25, 0, 1))
    col = lerp(col, PLAT * 0.92, np.clip((f - 0.4) / 0.5, 0, 1)) * (1 + brosse(P2, 1.0 + sg))[..., None]
    col = np.where(f < 0.12, FIL + np.zeros_like(col), col)
    nu = lerp(BRASS["hi"], BRASS["base"], np.clip(f / 0.55, 0, 1))
    nu = np.where(f > 0.6, PLAT * 0.92 * (1 + brosse(P2, 1.0 + sg))[..., None], nu)
    nu = np.where((f > 0.55) & (f <= 0.66), BRASS["low"] + np.zeros_like(nu), nu)
    col = lerp(nu, col, act)
    col = np.where(f >= 0.9, STEEL["low"] + np.zeros_like(col), col)
    return col, None, None


def peint_fil(pc, P2, d, sg):
    act = pc.actif(P2)[..., None]
    return lerp(BRASS["base"], FIL, act) + np.zeros(P2.shape[:-1] + (3,), np.float32), None, None


def peint_plat(pc, P2, d, sg):
    wb = pc.wb(P2)
    col = (PLAT + np.zeros(P2.shape[:-1] + (3,), np.float32)) * (1 + brosse(P2, 2.0 + 3 * sg))[..., None]
    dc = np.minimum(d_poly(P2, pc.centres[0]), d_poly(P2, pc.centres[1]))
    col = lerp(col, POLI, (np.clip(1 - dc / 0.5, 0, 1) * 0.3)[..., None])           # reflet le long du milieu du plat
    col[d < wb + 0.05] = STEEL["low"]
    dg = pc.d_g(P2)
    out = ~pc.in_g(P2)
    col[(dg < 0.07) & out] = BRASS["hi"]                                           # lèvre de laiton du sertissage
    col[(dg >= 0.07) & (dg < 0.12) & out] = BRASS["low"]
    ro = np.linalg.norm(P2 - O_, axis=-1)
    col[(ro < R_RIM + 0.14)] = STEEL["low"] * 0.9                                   # ombre portée de la roue
    for r in RIVETS:                                                                # rivets de sertissage (4–5 texels)
        dr = np.linalg.norm(P2 - np.array(r), axis=-1)
        col[dr < 0.17] = BRASS["low"]
        col[dr < 0.13] = BRASS["base"]
        col[np.linalg.norm(P2 - np.array(r) - (0.04, 0.04), axis=-1) < 0.06] = BRASS["hi"]
    return col, None, None




# ------------------------------------------------------------------ cubes différés (monde, recentrés après coup)
TILES = {}          # nom -> (rgba, rgba_e | None)
TRANS = set()       # tuiles semi-transparentes (groupes trans_ seulement)
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


def boite(g, nom, c, X, Y, s, faces):
    """Cube monde : centre c, axes X, Y (Z = X × Y), tailles s ; faces = {face: tuile}, les autres transparentes."""
    X, Y, Z = repere(X, Y)
    CUBES.append({"groupe": g, "nom": nom, "c": np.asarray(c, float), "R": np.column_stack([X, Y, Z]),
                  "half": np.asarray(s, float) / 2, "faces": dict(faces)})


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
    """Gouttière creusée : trou dans les plats (alpha), parois d'acier par tronçon et par face, fond à filet de laiton."""
    gp = np.array(pc.gpoly)
    a0, a1 = gp[:, 0].min() - 0.15, gp[:, 0].max() + 0.15
    b0, b1 = gp[:, 1].min() - 0.15, gp[:, 1].max() + 0.15

    def fond(P):
        P2 = P[..., :2]
        m = pc.in_g(P2) | (pc.d_g(P2) < 0.1)
        dc = pc.d_ax(P2)
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + STEEL["base"] * 0.92
        col[dc < 0.07] = BRASS["base"]
        col[dc < 0.03] = BRASS["hi"]
        return col, None, None, m

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
                col = lerp(STEEL["base"], STEEL["low"], np.clip((dz[..., None] - 0.06) / 0.3, 0, 1)) + np.zeros(P.shape[:-1] + (3,), np.float32)
                col[dz < 0.08] = BRASS["base"]
                return col, None, None, np.ones(P.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zc)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec(groupe, f"{pc.nom}_paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


# ------------------------------------------------------------------ tours (pièces rondes, recette de skin_epee_steampunk)
OVL, OVW = 0.04, 0.03
DENS = 16.0


def p_laiton(xn, t, y, r, L, ex):
    k = np.clip(0.3 + 0.55 * (1 - np.abs(xn) ** 1.4) + ex.get("clair", 0.0), 0, 1)
    col = lerp(BRASS["low"], BRASS["hi"], k[..., None])
    if ex.get("arete"):
        col = np.where(((y < 0.06) | (y > L - 0.06))[..., None], BRASS["low"] * 0.85, col)
    return col, None


def p_cuivre(xn, t, y, r, L, ex):
    k = np.clip(0.3 + 0.55 * (1 - np.abs(xn) ** 1.4) + ex.get("clair", 0.0), 0, 1)
    col = lerp(COPPER["low"], COPPER["hi"], k[..., None])
    if ex.get("riv"):
        pas = ex["riv"]
        yy = (y + ex.get("y0", 0.0)) % pas - pas / 2
        dx = xn * ex.get("demi", 0.25)
        dd = np.hypot(dx, yy)
        col = np.where((dd < 0.15)[..., None], COPPER["low"] * 0.7, col)
        col = np.where((dd < 0.11)[..., None], BRASS["base"], col)
        col = np.where((np.hypot(dx + 0.03, yy - 0.03) < 0.05)[..., None], BRASS["hi"], col)
    if ex.get("arete"):
        col = np.where(((y < 0.05) | (y > L - 0.05))[..., None], COPPER["low"] * 0.85, col)
    return col, None


def p_acier(xn, t, y, r, L, ex):
    k = np.clip(0.25 + 0.6 * (1 - np.abs(xn) ** 1.3) + ex.get("clair", 0.0), 0, 1)
    return lerp(STEEL["low"], STEEL["hi"], k[..., None]), None


def p_poli(xn, t, y, r, L, ex):
    """Acier poli de la pointerolle et du collet : clair, arête de lumière au milieu du pan."""
    k = np.clip(0.2 + 0.7 * (1 - np.abs(xn) ** 1.2) + ex.get("clair", 0.0), 0, 1)
    col = lerp(STEEL["base"], POLI, k[..., None])
    return np.where((np.abs(xn) < 0.18)[..., None], lerp(col, FIL, 0.5), col), None


def p_bois(xn, t, y, r, L, ex):
    k = np.clip(0.35 + 0.45 * (1 - np.abs(xn) ** 1.3), 0, 1)
    col = lerp(WOOD["low"], WOOD["hi"], k[..., None])
    g = np.sin(y * 7.0 + xn * 2.2 + np.sin(y * 1.3 + xn) * 1.8)
    return col * (1 - 0.1 * (g > 0.7))[..., None], None


def p_cuir(xn, t, y, r, L, ex):
    """Cuir enroulé en spirale (bandes en biais, joint sombre), couture de laiton au milieu de chaque bande."""
    f = ((y / 0.55 + xn * 0.18) % 1.0)
    k = (1 - np.abs(xn)) * 0.35
    col = lerp(LEATHER["low"], LEATHER["hi"], (0.35 + k + 0.25 * np.clip(1 - np.abs(f - 0.5) * 2.2, 0, 1))[..., None])
    col = np.where((f < 0.12)[..., None], LEATHER["low"] * 0.7, col)
    st = (np.abs(f - 0.5) < 0.07) & (np.abs(xn) < 0.6) & ((np.floor((y + 0.05) / 0.12) % 2) == 0)
    col = np.where(st[..., None], BRASS["base"], col)
    return col, None


def p_ambre(xn, t, y, r, L, ex):
    q = np.abs(xn + 0.25)
    col = lerp(A((255, 236, 180)), AMBRE_B, np.clip(q / 1.2, 0, 1)[..., None] ** 0.9)
    em = lerp(A((225, 170, 80)), A((160, 100, 30)), np.clip(np.abs(xn), 0, 1)[..., None])
    return col, em


def p_suie(xn, t, y, r, L, ex):
    return np.zeros(xn.shape + (3,), np.float32) + A((34, 28, 24)), None


PEINTRES = {"laiton": p_laiton, "cuivre": p_cuivre, "acier": p_acier, "poli": p_poli, "bois": p_bois, "cuir": p_cuir,
            "ambre": p_ambre, "suie": p_suie}


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
    ex = dict(ex)
    ex.setdefault("demi", max(w0, w1) / 2)
    col, em = PEINTRES[mat](xn, t, y + ex.get("y0", 0.0), r, L, ex)
    return tuile(nom, *finir(col, None, em, mask))


def tour(g, nom, O, ax, ref, profil, n=12, phase=0.0):
    """profil = [(b0, r0, b1, r1, mat, ex), ...] le long de ax depuis O (monde) ; une couronne de n pans par tronçon."""
    O, ax = np.asarray(O, float), unit(ax)
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


def bague(b, r_in, r_out, long, mat="laiton", ex=None):
    """Profil d'une bague posée sur un fût : flanc, dessus (arêtes marquées), flanc."""
    ex = dict(ex or {})
    return [(b, r_in, b, r_out, mat, dict(ex)), (b, r_out, b + long, r_out, mat, dict(ex, arete=True)), (b + long, r_out, b + long, r_in, mat, dict(ex))]


def tuyau(g, nom, pts, r, mat="cuivre", collier=0.3):
    """Tuyau (monde) le long d'une polyligne : un cylindre à 8 pans par tronçon, collier de laiton à chaque coude."""
    pts = [np.asarray(p, float) for p in pts]
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]
        Ln = float(np.linalg.norm(q - p))
        tour(g, f"{nom}{i}_", p, q - p, T_, [(-0.08, r, Ln + 0.08, r, mat, {})], n=8, phase=math.pi / 8)
    for i in range(1, len(pts) - 1):
        d = unit(unit(pts[i + 1] - pts[i]) + unit(pts[i] - pts[i - 1]))
        tour(g, f"{nom}c{i}_", pts[i], d, T_, bague(-0.17, r - 0.02, collier, 0.34), n=8, phase=math.pi / 8)


# ------------------------------------------------------------------ tuiles peintes (cadran, couvercles, foyer, vapeur)
def disque_t(n, fn, ss=4):
    """Tuile ronde n × n texels : fn(X, Y, R) en coordonnées -1..1 (sur-échantillonnée) -> col, em."""
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    X, Y = (xx + 0.5 - N / 2) / (N / 2), -(yy + 0.5 - N / 2) / (N / 2)
    R = np.hypot(X, Y)
    col, em = fn(X, Y, R)
    m = R < 0.985
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.LANCZOS)).astype(np.float32)
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((n, n), Image.LANCZOS)) > 110
    e = None
    if em is not None:
        e = np.array(Image.fromarray(np.clip(em, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.NEAREST)).astype(np.float32)
    return finir(rgb, None, e, al)


def f_cadran(X, Y, R):
    """Cadran : verre ambre, 13 crans (-120° à +120° depuis le haut), zone rouge en haut de l'échelle, reflet."""
    col = lerp(BRASS["hi"], BRASS["low"], np.clip(0.5 - 0.5 * Y, 0, 1)[..., None] * 0.8) * np.ones(R.shape + (1,), np.float32)
    em = np.zeros(R.shape + (3,), np.float32)
    ang = np.degrees(np.arctan2(X, Y))
    glass = R < 0.86
    col[(R > 0.86) & (R < 0.92)] = BRASS["low"] * 0.7
    g = lerp(AMBRE, AMBRE_B, np.clip(R / 0.86, 0, 1)[..., None] ** 1.5)
    col[glass] = g[glass]
    em[glass] = (190, 126, 40)
    red = glass & (R > 0.56) & (R < 0.76) & (ang > 84) & (ang < 122)
    col[red] = (176, 44, 30)
    em[red] = (150, 30, 14)
    for k in range(13):
        a = -120 + 20 * k
        r0 = 0.54 if k % 2 == 0 else 0.64
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        along = X * sa + Y * ca
        across = np.abs(X * ca - Y * sa)
        tick = glass & (along > r0) & (along < 0.8) & (across < (0.055 if k % 2 == 0 else 0.04))
        col[tick] = (58, 32, 18)
        em[tick] = 0
    hl = glass & (np.abs(R - 0.68) < 0.04) & (ang < -40) & (ang > -95)
    col[hl] = lerp(AMBRE, VAPEUR, 0.7)
    return col, em


def f_couvercle(X, Y, R):
    """Couvercle de l'œil : acier poli, cercle de laiton, 4 rivets de laiton."""
    col = lerp(POLI, STEEL["base"], np.clip(0.5 - 0.5 * Y + R * 0.3, 0, 1)[..., None]) * np.ones(R.shape + (1,), np.float32)
    col[(R > 0.6) & (R < 0.74)] = BRASS["base"]
    col[(R > 0.6) & (R < 0.64)] = BRASS["hi"]
    col[R > 0.9] = STEEL["low"]
    for k in range(4):
        th = TAU * k / 4 + TAU / 8
        dr = np.hypot(X - 0.8 * math.cos(th) * 0.95, Y - 0.8 * math.sin(th) * 0.95)
        col[dr < 0.1] = BRASS["low"]
        col[dr < 0.075] = BRASS["hi"]
    return col, None


def t_octo(nom, n, Ra, fn, N=40):
    """Tuile en polygone régulier à n côtés d'apothème Ra (couvercle), peinte par fn(X, Y, R) sur le cercle circonscrit."""
    R_ = Ra / math.cos(math.pi / n)
    yy, xx = np.mgrid[0:N, 0:N]
    x = ((xx + 0.5) / N - 0.5) * 2
    y = (0.5 - (yy + 0.5) / N) * 2
    th = np.arctan2(y, x) - math.pi / n
    sect = np.round(th / (TAU / n)) * (TAU / n) + math.pi / n
    apo = (x * np.cos(sect) + y * np.sin(sect)) * R_
    mask = apo <= Ra
    col, em = fn(x, y, np.hypot(x, y) * R_ / Ra)
    return tuile(nom, *finir(col, None, em, mask))


def t_unie(c0, c1, W=16, H=8, bord=None):
    col = lerp(c0, c1, np.linspace(0, 1, H)[:, None, None] * np.ones((1, W, 1), np.float32))
    if bord is not None:
        col[0] = col[-1] = bord
        col[:, 0] = col[:, -1] = bord
    return finir(col, None, None, np.ones((H, W), bool))


def t_aiguille():
    c = np.zeros((16, 4, 3), np.float32) + A((34, 28, 26))
    c[:6] = (190, 44, 30)
    c[:, :1] *= 1.5
    return finir(c, None, None, np.ones((16, 4), bool))


def t_foyer(W=32, H=22):
    """Porte de foyer : cadre d'acier, 3 fentes rougeoyantes (_e vif), 4 rivets de laiton."""
    c = STEEL["base"] * np.ones((H, W, 3), np.float32)
    c[:2], c[:, :2] = STEEL["hi"], STEEL["hi"]
    c[-2:], c[:, -2:] = STEEL["low"], STEEL["low"]
    e = np.zeros((H, W, 3), np.float32)
    for x0 in (8, 14, 20):
        c[4:H - 4, x0:x0 + 3] = (255, 150, 52)
        c[5:H - 5, x0 + 1] = (255, 214, 120)
        e[4:H - 4, x0:x0 + 3] = (225, 112, 28)
        e[5:H - 5, x0 + 1] = (225, 170, 70)
    for x, y in ((3, 3), (W - 5, 3), (3, H - 5), (W - 5, H - 5)):
        c[y:y + 2, x:x + 2] = BRASS["hi"]
    return finir(c, None, e, np.ones((H, W), bool))


def cell_noise(h, w, cy, cx, seed):
    r = np.random.default_rng(seed)
    a = (r.random((cy + 2, cx + 2)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((w, h), Image.BICUBIC), np.float32) / 255


def t_vapeur(W, H, seed, plume=True):
    """Vapeur en dégradé d'opacité (alpha 1–254), blanc légèrement bleuté (tuiles des groupes trans_)."""
    ss = 3
    yy, xx = np.mgrid[0:H * ss, 0:W * ss]
    u = (xx + 0.5) / (W * ss)
    v = (yy + 0.5) / (H * ss) * 2 - 1
    n1 = cell_noise(H * ss, W * ss, 4, 9, seed)
    n2 = cell_noise(H * ss, W * ss, 9, 22, seed + 1)
    lump = 0.78 + 0.32 * n1 + 0.12 * n2
    if plume:
        hw = lerp(0.24, 0.96, u ** 0.55) * (0.82 + 0.25 * n1)
        prof = np.clip(1 - (np.abs(v) / np.maximum(hw, 1e-3)) ** 2, 0, 1) ** 0.6
        along = np.clip(u / 0.05, 0, 1) * np.clip(1 - u ** 1.7, 0, 1)
        a = 250 * prof * along * lump
    else:
        puffs = np.zeros_like(u)
        for px, py, pr in ((0.5, 0.05, 0.42), (0.33, -0.18, 0.30), (0.66, -0.2, 0.30), (0.5, -0.45, 0.30), (0.42, 0.42, 0.26), (0.6, 0.4, 0.24)):
            puffs = np.maximum(puffs, np.clip(1 - np.hypot(u - px, (v - py) / 2) / pr * 0.5, 0, 1))
        a = 300 * np.clip(puffs - 0.3, 0, 1) / 0.7 * lump * np.clip((1 - v) / 0.25, 0, 1)
    a = np.clip(a, 0, 254)
    c = lerp(VAPEUR_B, VAPEUR, np.clip(1 - np.abs(v) * 0.8, 0, 1)[..., None])
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(a.astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(np.int32)
    al[al < 10] = 0
    al = np.clip(al, 0, 254)
    out = np.dstack([rgb, al]).astype(np.uint8)
    out[al == 0, :3] = VAPEUR_B.astype(np.uint8)
    return out, None



def f_roue(X, Y, R):
    """Face de la roue (skin_epee_steampunk) : couronne, gorge, voile creusé à 6 évidements sombres et 6 rivets, moyeu de cuivre."""
    col = lerp(BRASS["base"], BRASS["hi"], np.clip(0.5 + 0.4 * Y, 0, 1)[..., None]) * np.ones(R.shape + (1,), np.float32)
    col[(R > 0.78) & (R < 0.82)] = BRASS["low"] * 0.8
    web = (R >= 0.48) & (R <= 0.78)
    col[web] = lerp(BRASS["low"], BRASS["base"], np.clip(0.4 + 0.3 * Y[web], 0, 1)[..., None])
    for k in range(6):
        th = TAU * k / 6 + TAU / 12
        hx, hy = 0.63 * math.cos(th), 0.63 * math.sin(th)
        dh = np.hypot(X - hx, Y - hy)
        col[dh < 0.115] = BRASS["low"] * 0.45
        col[(dh < 0.115) & (Y - hy < -0.04)] = BRASS["low"] * 0.75
        th2 = TAU * k / 6
        dr = np.hypot(X - 0.63 * math.cos(th2), Y - 0.63 * math.sin(th2))
        col[dr < 0.06] = BRASS["low"] * 0.7
        col[dr < 0.045] = BRASS["hi"]
    col[(R > 0.44) & (R < 0.48)] = BRASS["low"] * 0.8
    col[R <= 0.44] = lerp(COPPER["base"], COPPER["hi"], np.clip(0.5 + 0.5 * Y, 0, 1)[..., None])[R <= 0.44]
    return col, None


R_PL = R_RIM + 0.02
TILES["roue"] = disque_t(int(round(2 * R_PL * 16)), f_roue)
TILES["cadran"] = disque_t(40, f_cadran)
_c, _ce = TILES["cadran"]
TILES["cadran_m"] = (_c[:, ::-1].copy(), None if _ce is None else _ce[:, ::-1].copy())   # cadran arrière vu « à travers »
TILES["aiguille"] = t_aiguille()
TILES["foyer"] = t_foyer(28, 20)
TILES["acier_b"] = t_unie(STEEL["hi"], STEEL["low"], bord=STEEL["low"])
TILES["laiton_b"] = t_unie(BRASS["hi"], BRASS["low"], bord=BRASS["low"])
TILES["dent"] = t_unie(BRASS["hi"], BRASS["base"], W=10, H=10, bord=BRASS["low"])
TILES["bouffee"] = t_vapeur(48, 56, 72, plume=False)
TRANS.update({"bouffee"})


# ------------------------------------------------------------------ conception
GROUPES = []        # (nom, pivot, parent, rotation)


def grp(nom, pivot, parent, rotation=(0.0, 0.0, 0.0)):
    GROUPES.append((nom, np.asarray(pivot, float), parent, rotation))
    return nom


def plaque_vapeur(g, nom, c, X, Y, half, tile):
    boite(g, nom, c, X, Y, 2 * np.asarray(half, float), {"south": tile, "north": tile})


def ang_dents():
    """Dents de la roue (angle en degrés depuis +a, vers +b) : 18 places, retirées là où passent fer, manche et tuyau."""
    half_t = math.degrees(0.55 / 2 / R_DENT) + 1.5
    rel = np.array(POLY) - O_
    rr = np.linalg.norm(rel, axis=1)
    near = rel[(rr > R_RIM - 0.3) & (rr < R_DENT + 0.4)]
    angs = np.degrees(np.arctan2(near[:, 1], near[:, 0]))
    f0, f1 = angs.min() - half_t, angs.max() + half_t
    obst = [(180.0, math.degrees(math.atan(0.72 / R_RIM)) + half_t)]
    p0, p1 = np.array(TUYAU[-2]), np.array(TUYAU[-1])
    for x in np.linspace(0, 1, 40):                         # tuyau : toutes les places qu'il frôle
        q = p0 + (p1 - p0) * x - O_
        if np.linalg.norm(q) < R_DENT + 0.5:
            obst.append((math.degrees(math.atan2(q[1], q[0])), math.degrees(math.atan(0.3 / np.linalg.norm(q))) + half_t))
    dif = lambda a, b: abs((a - b + 180) % 360 - 180)
    out = []
    for k in range(18):
        th = (10 + 20 * k + 180) % 360 - 180
        if f0 <= th <= f1 or any(dif(th, c) < w for c, w in obst):
            continue
        out.append(th)
    return out


TUYAU = [(S_B1 - 0.25, -0.62), (S_B1 + 0.4, -EP), (9.35, -EP), (10.95, -1.22)]
OUT = {}


def conception():
    racine = grp(objet.etape("repos", "pelle"), Wp(A_O), None)
    pel = grp("pelle", Wp(A_O), racine)

    # --- poignée en D : traverse de cuir cousu de laiton, embouts de laiton, deux branches de laiton jusqu'à la fourche du manche
    TR0, TRH = 0.5, 1.3
    tour(pel, "traverse", Wp(TR0, -TRH), W_, T_,
         [(0.0, 0.0, 0.0, 0.44, "laiton", {"clair": 0.2}), (0.0, 0.44, 0.24, 0.44, "laiton", {"arete": True}),
          (0.24, 0.44, 0.24, 0.39, "laiton", {}), (0.24, 0.39, 2 * TRH - 0.24, 0.39, "cuir", {}),
          (2 * TRH - 0.24, 0.39, 2 * TRH - 0.24, 0.44, "laiton", {}), (2 * TRH - 0.24, 0.44, 2 * TRH, 0.44, "laiton", {"arete": True}),
          (2 * TRH, 0.44, 2 * TRH, 0.0, "laiton", {"clair": 0.2})], n=12)
    for s in (1, -1):
        p0, p1 = Wp(TR0 + 0.05, s * (TRH - 0.3)), Wp(S_GRIP0 + 0.15, s * 0.36)
        Ln = float(np.linalg.norm(p1 - p0))
        tour(pel, f"branche_{'pm'[s < 0]}", p0, p1 - p0, T_, [(0.0, 0.27, Ln, 0.27, "laiton", {"arete": True})], n=8, phase=math.pi / 8)
    # --- manche : fourche de laiton, bois sombre, chaudière de cuivre rivetée cerclée de laiton, bois, bague sous la roue
    prof = [(S_GRIP0 - 0.3, 0.0, S_GRIP0 - 0.3, 0.5, "laiton", {"clair": 0.15}), (S_GRIP0 - 0.3, 0.5, S_GRIP0 + 0.1, 0.68, "laiton", {}),
            (S_GRIP0 + 0.1, 0.68, S_GRIP0 + 0.55, 0.68, "laiton", {"arete": True}), (S_GRIP0 + 0.55, 0.68, S_GRIP0 + 0.62, 0.56, "laiton", {}),
            (S_GRIP0 + 0.62, 0.56, S_B0 - 0.05, 0.56, "bois", {}), (S_B0 - 0.05, 0.56, S_B0 + 0.15, RB, "cuivre", {"clair": 0.05})]
    prof += bague(S_B0 + 0.15, RB, RB + 0.13, 0.3)
    prof += [(S_B0 + 0.45, RB, S_B1 - 0.45, RB, "cuivre", {"riv": 0.55, "y0": 0.1})]
    prof += bague(S_B1 - 0.45, RB, RB + 0.13, 0.3)
    prof += [(S_B1 - 0.15, RB, S_B1 + 0.05, 0.56, "cuivre", {}), (S_B1 + 0.05, 0.56, A_O, 0.56, "bois", {})]
    tour(pel, "manche", Wp(0), A_, T_, prof, n=12)
    tour(pel, "bague_roue", Wp(0), A_, T_, bague(A_O - R_RIM - 0.45, 0.56, 0.74, 0.4), n=12)
    # portes du foyer sur les deux faces de la chaudière (fentes rougeoyantes)
    for s in (1, -1):
        boite(pel, f"foyer_{'pm'[s < 0]}", Wp(S_B0 + 1.05, 0, s * (RB + 0.05)), A_, W_, (1.1, 0.8, 0.1), {("south" if s > 0 else "north"): "foyer"})
    # tuyau de cuivre de la chaudière à la roue (la pression va au manomètre), colliers de laiton
    tuyau(pel, "tuyau", [Wp(*p) for p in TUYAU], 0.21)
    # soupape sur le flanc -b de la chaudière (haut en main) : tige d'acier, chapeau de laiton, bouffée cachée
    vb = Wp(S_V) + VALVE * (RB * 0.9)
    tour(pel, "soupape_tige", vb, VALVE, T_, [(0.0, 0.17, 0.55, 0.17, "acier", {})], n=8)
    soup = grp("soupape", vb + VALVE * 0.5, pel)
    tour(soup, "soupape_chapeau", vb, VALVE, T_, [(0.5, 0.17, 0.5, 0.34, "laiton", {}), (0.5, 0.34, 0.78, 0.34, "laiton", {"arete": True}),
                                                 (0.78, 0.34, 0.8, 0.14, "laiton", {}), (0.8, 0.14, 0.94, 0.14, "laiton", {"clair": 0.1}),
                                                 (0.94, 0.14, 0.97, 0.0, "laiton", {"clair": 0.2})], n=8)
    bo = vb + VALVE * 0.62
    bouf = grp("trans_bouffee", bo, soup)
    for k in range(3):
        ang = math.radians(60 * k)
        Xp = T_ * math.cos(ang) + unit(np.cross(VALVE, T_)) * math.sin(ang)
        plaque_vapeur(bouf, f"bouffee{k}", bo + VALVE * (1.05 * F_GEO / K), Xp, VALVE, np.array((0.9, 1.05, 0.15)) * F_GEO / K, "bouffee")
    rz = math.degrees(math.atan2(VALVE[1], VALVE[0])) - 90      # +Y du groupe le long de la soupape
    em = grp("emit_mc_white_smoke", vb + VALVE * 1.0, pel, rotation=(0.0, 0.0, rz))
    grp("ctrl_emit", vb + VALVE * 1.0, em)

    # --- « frog » : roue dentée de laiton (flanc à 24 pans, faces découpées par l'alpha, dents en boîtes), manomètres sur les deux faces
    tete = grp("tete", Wp(A_O), pel)
    C = Wp(A_O)
    tour(tete, "flanc", C - T_ * GZ, T_, A_, [(0.0, R_RIM, 2 * GZ, R_RIM, "laiton", {"arete": True})], n=24)
    for s in (1, -1):
        boite(tete, f"roue_{'pm'[s < 0]}", C + T_ * s * (GZ + 0.02 - TH / 2), A_ * s, W_, (2 * R_PL, 2 * R_PL, TH), {"south": "roue"})
    dents = ang_dents()
    OUT["dents"] = dents
    for k, th in enumerate(dents):
        e = Wv(math.cos(math.radians(th)), math.sin(math.radians(th)))
        t_ = np.cross(T_, e)
        boite(tete, f"dent{k}", C + e * (R_RIM + 0.25), e, t_, (0.6, 0.55, 2 * TZ), {f: "dent" for f in SIX})
    for s in (1, -1):
        cs = "pm"[s < 0]
        tour(tete, f"lunette_{cs}", C + T_ * s * (GZ - 0.12), T_ * s, A_,
             [(0.0, 0.92, 0.32, 0.92, "laiton", {"arete": True}), (0.32, 0.92, 0.38, 0.8, "laiton", {"clair": 0.2})], n=16)
        boite(tete, f"cadran_{cs}", C + T_ * s * (GZ + 0.14), -W_, A_, (1.74, 1.74, 0.12),
              {"south": "cadran"} if s > 0 else {"north": "cadran_m"})
    a0 = math.radians(-120 + 40 * 1.0)             # niveau 1 au repos
    dn = A_ * math.cos(a0) - W_ * math.sin(a0)
    aig = grp("aiguille", C, tete)
    for s in (1, -1):
        c0 = C + T_ * s * (GZ + 0.24)
        boite(aig, f"aiguille_{'pm'[s < 0]}", c0 + dn * 0.3, np.cross(dn, T_), dn, (0.14, 0.74, 0.06), {f: "aiguille" for f in SIX})
        boite(aig, f"moyeu_{'pm'[s < 0]}", c0 + T_ * s * 0.02, A_, W_, (0.2, 0.2, 0.1), {f: "laiton_b" for f in SIX})

    # --- fer d'acier bruni en vrai volume (plaque biseautée fermée, nervure creusée) ; pivot au centre de la roue (pelletée)
    fer = grp("fer", C, tete)
    volume(FER, fer)
    gouttiere(FER, fer)
    OUT.update(racine=racine, aiguille=aig, soupape=soup, bouffee=bouf, fer=fer)
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
GROUPES = [(n, p + DEC, par, r) for n, p, par, r in GROUPES]

UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, (im, ime) in sorted(TILES.items(), key=lambda it: (-it[1][0].shape[0], -it[1][0].shape[1], it[0])):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, f"atlas plein ({n}, y = {y})"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None and AVEC_E:
            tex_e[y:y + h, x:x + w] = ime
        x += w + 1
        shelf = max(shelf, h)
    assert tex[TEX - 2, TEX - 2, 3] == 0
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    zone = np.zeros(semi.shape, bool)
    for n in TRANS:
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
for nom, piv, parent, r in GROUPES:
    assert nom not in groups and len(nom) <= 64, nom
    groups[nom] = {"origin": [round(float(v), 4) for v in piv], "uuid": nuid(), "ids": [], "parent": parent,
                   "rotation": [round(float(v), 3) for v in r]}
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


# ------------------------------------------------------------------ animations (objet vivant, guide 14 ; inchangées)
def kf(t, x, y, z, ch="rotation"):
    f = lambda v: v if isinstance(v, str) else f"{v + 0.0:.4f}".rstrip("0").rstrip(".")
    return {"channel": ch, "data_points": [{"x": f(x), "y": f(y), "z": f(z)}], "time": round(t, 4), "interpolation": "linear"}


def anim(name, length, tracks, fps=24, loop="loop"):
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A__ = {}
    for (g, ch), f in tracks.items():
        ks = [kf(t, *f(t), ch=ch) for t in times] if callable(f) else [kf(0.0, *f, ch=ch), kf(length, *f, ch=ch)]
        A__.setdefault(groups[g]["uuid"], {"name": g, "type": "bone", "keyframes": []})["keyframes"] += ks
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": False, "animators": A__}


def step(tau, rise=0.05, over=0.28):
    """Échelon de servo : montée courte, dépassement puis rappel amorti."""
    if tau <= 0:
        return 0.0
    v = sm(tau, 0.0, rise)
    if tau > rise * 0.6:
        x = tau - rise * 0.6
        v += over * math.sin(TAU * x / 0.15) * math.exp(-x / 0.045)
    return v


def le_long(v, d):
    w = np.asarray(d, float) * v
    return float(w[0]), float(w[1]), float(w[2])


def needle(lvl):
    """Rotation de l'aiguille pour un écart de niveau (40° par cran ; monter = sens horaire vu de +Z = z négatif)."""
    return 0.0, 0.0, -40 * lvl


AIG, SOUP, BOUF, FERG = OUT["aiguille"], OUT["soupape"], OUT["bouffee"], OUT["fer"]
CE = "ctrl_emit"


def valve(t, tps, trem):
    y = 0.035 * trem * math.sin(TAU * 23 * t + 0.7)
    for tp in tps:
        y += 0.24 * (step(t - tp, rise=0.035, over=0.2) - step(t - tp - 0.18, rise=0.04, over=0.35))
    return le_long(y, VALVE)


def puff(t, tp, p=1.0):
    if not (tp <= t <= tp + 0.72 * p):
        return 0.0, 0.0
    sz = sm(t, tp + 0.02, tp + 0.1 * p) * (1 + 0.3 * sm(t, tp + 0.1 * p, tp + 0.45 * p)) * (1 - sm(t, tp + 0.3 * p, tp + 0.62 * p))
    up = 0.9 * sm(t, tp + 0.05, tp + 0.62 * p) * (1 - sm(t, tp + 0.64 * p, tp + 0.7 * p))
    return sz, up


def puff_scale(t, tps):
    k = (1 + (K - 1) * max(puff(t, tp)[0] for tp in tps)) / F_GEO
    return k, k, k


def puff_pos(t, tps):
    return le_long(max(puff(t, tp)[1] for tp in tps), VALVE)


SIGNE_B = 1.0


def rotb(a):
    """Rotation de a degrés autour de l'axe en travers du fer (W_), petits angles (comme skin_pelle_abyssal)."""
    a = a * SIGNE_B
    return -a / math.sqrt(2), a / math.sqrt(2), 0.0


# --- item_idle (24 s) : deux cycles de pression ; quatre crans, tremblement, décharge (soupape + bouffée + vapeur) ; seul son
L_IDLE = 24.0
TICKS = [1.5, 3.5, 5.5, 7.5, 13.5, 15.5, 17.5, 19.5]
PUFFS = [10.0, 22.0]
TW = 0.8


def tremble(t):
    return sum(bump(t, tp - TW, tp - TW * 0.75, tp - 0.03, tp) for tp in PUFFS)


def idle_level(t):
    v = sum(step(t - ti) for ti in TICKS) - sum(4 * step(t - tp - 0.03, rise=0.08, over=0.1) for tp in PUFFS)
    return v + 0.13 * tremble(t) * math.sin(TAU * 19 * t)


def idle_emit(t):
    return -1 + 4 * sum(bump(t, tp + 0.02, tp + 0.08, tp + 0.35, tp + 0.5) for tp in PUFFS), 0.0, 0.0


item_idle = anim("item_idle", L_IDLE, {
    (AIG, "rotation"): lambda t: needle(idle_level(t)),
    (SOUP, "position"): lambda t: valve(t, PUFFS, tremble(t)),
    (BOUF, "scale"): lambda t: puff_scale(t, PUFFS), (BOUF, "position"): lambda t: puff_pos(t, PUFFS),
    (CE, "position"): idle_emit}, fps=30)

# --- item_swing (boucle 0,3 s) : on creuse : l'aiguille tremble, la soupape frémit, vapeur coupée
L_ISW = 0.3
item_swing = anim("item_swing", L_ISW, {
    (AIG, "rotation"): lambda t: needle(0.12 * math.sin(TAU * 3 * t / L_ISW)),
    (SOUP, "position"): lambda t: le_long(0.04 * math.sin(TAU * 2 * t / L_ISW), VALVE),
    (CE, "position"): (-1, 0, 0)}, fps=48)

# --- event_select (0,8 s) : tour d'essai de l'aiguille par crans, la soupape claque une fois
L_SEL = 0.8


def sel_needle(t):
    lvl = sum(step(t - ti) for ti in (0.2, 0.3, 0.4)) - 3 * step(t - 0.58, rise=0.08, over=0.1)
    return needle(lvl)


event_select = anim("event_select", L_SEL, {
    (AIG, "rotation"): sel_needle,
    (SOUP, "position"): lambda t: valve(t, [0.6], 0.0)}, fps=40, loop="once")

# --- event_swing (0,4 s) : l'aiguille perd un cran et remonte
L_ESW = 0.4
event_swing = anim("event_swing", L_ESW, {
    (AIG, "rotation"): lambda t: needle(-(step(t - 0.05, rise=0.03, over=0.15) - step(t - 0.22, rise=0.08, over=0.12)))},
    fps=60, loop="once")

# --- event_break (0,7 s) : la pelletée : le fer se relève de 5° puis revient, l'aiguille perd un cran, la soupape claque,
#     white_smoke (ctrl_emit +4) ; sans son ni dépliage
L_BRK = 0.7


def pelletee(t):
    return 5.0 * sm(t, 0.02, 0.16) * (1 - sm(t, 0.3, 0.62))


event_break = anim("event_break", L_BRK, {
    (FERG, "rotation"): lambda t: rotb(pelletee(t)),
    (AIG, "rotation"): lambda t: needle(-(step(t - 0.04, rise=0.04, over=0.2) - step(t - 0.4, rise=0.12, over=0.1))),
    (SOUP, "position"): lambda t: valve(t, [0.05], 0.0),
    (CE, "position"): lambda t: (-1 + 5 * bump(t, 0.04, 0.08, 0.3, 0.45), 0.0, 0.0)}, fps=40, loop="once")

ANIMS = [item_idle, item_swing, event_select, event_swing, event_break]
ANIMS[0]["selected"] = True


# ------------------------------------------------------------------ écriture
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


assert len(elements) <= 8192, f"budget : {len(elements)} cubes"
P = coins()
LONGUEUR = float((P @ A_).max() - (P @ A_).min())
LARGEUR = float((P @ W_).max() - (P @ W_).min())
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
_lo, _hi = P[:, :2].min(0), P[:, :2].max(0)
GUI_S = float(os.environ.get("GUI", "0")) or round(min(1.0, 15.6 / float(max(_hi - _lo))), 3)
AFFICHAGE = objet.affichage("pelle", gui={"scale": [GUI_S] * 3})
model = objet.modele(NOM, "pelle", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son  # noqa: E402
limiter_sons(model)
# Seul son : une décharge au repos, à la seconde bouffée d'item_idle (22,02 s, une fois par boucle de 24 s ; outil, ligne Langage du
# set, comme skin_pioche_steampunk) ; ajouté après limiter_sons, qui ne connaît pas les états d'objet. Aucun son aux événements.
item_idle["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(PUFFS[1] + 0.02, "block.fire.extinguish")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))

print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur le long du manche {LONGUEUR:.1f} px ; largeur du fer {LARGEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. "
      f"{P.max(axis=0).round(2)} ; gui {GUI_S} ; dents {OUT['dents']}")
gm = min(float(FER.h(np.array([p]))[0] - Z_FOND) for p in FER.gax)
marge = min(float(FER.dE(np.array([p]))[0] - FER.wb(np.array([p]))[0]) for p in FER.gl + FER.gr)
print(f"fer : {FER.L:.2f} px, profondeur mini de gouttière {gm:.2f} px, marge gouttière/biseau {marge:.2f} px")
