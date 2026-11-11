"""Harpon à pression : skin d'objet (guide 14) pour tous les tridents du joueur, ensemble Steampunk (thème Mécanique).
Design original. Écrit skin_trident_steampunk.png, skin_trident_steampunk_e.png et .build/skin_trident_steampunk_brut.bbmodel.

Point de départ : gen_skin_lance_steampunk.py (classe Fer opaque, roue dentée, cadrans, tours, foyer, vapeur, animations ; les
plages communes en sont recopiées telles quelles) ; repère, longueur, prise, étapes et Display de skin_trident_abyssal /
skin_trident_orage (objet.affichage_trident(), 31,2 px), gui 0,6.

Référence réelle (.claude/references/objets/tridents.md) : fouëne de pêche forgée (trois dents à ardillons tournés vers le
bas, la centrale plus longue) et harpon à poudre ou à air des baleiniers (la charge chasse le fer). Ici un **harpon de
chaudronnier** où chaque pièce sert au circuit de vapeur :
- fourche d'acier bruni forgée d'une pièce = une plaque biseautée fermée (recette .claude/references/objets/volume-3d.md :
  croissant + trois dents dans un seul contour, plat incliné 1,60 -> 0,48 px, pente unique 52°), fil poli sur le haut des dents
  et les ardillons seulement, croissant et gorges **bordés de laiton**, gouttière creusée dans l'axe de la dent centrale (filet de
  laiton au fond), rivets de sertissage peints ;
- la fourche est sertie dans la **roue dentée de laiton** (signature du set) : manomètre ambre au moyeu sur les deux faces, une
  aiguille ; une seule **buse de cuivre** sur la roue, côté +b (le haut en main) : elle crache la vapeur au lancer ;
- la hampe est le tube de vapeur : acier bruni à bagues de laiton, poignée de cuir cousu de laiton, douille de laiton ; au talon,
  la **chaudière de cuivre rivetée** (porte de foyer à fentes sur les deux faces, soupape côté +b, lentille-témoin ambre) et un
  **œillet de ligne** de laiton (où l'on attache la corde du harpon).
Distinct de la lance du set (fer en feuille, deux buses en V, réservoir au milieu de la hampe, bois) : fourche en ψ, une buse,
chaudière au talon, hampe d'acier. Lumière _e seulement sur des sources logiques : verre ambre des deux cadrans, fentes des
deux foyers, lentille-témoin allumée quand le harpon est armé (étapes leve et lance).

Étapes (guide 14) : `repos` (lentille-témoin éteinte), `leve` (prêt à lancer : lentille allumée, l'aiguille monte au rouge avec
q.use_progress), `lance` (en vol, dessiné à sa taille, **pointe vers +Y comme le veut le guide** : l'étape n'est pas couchée
tant que le développeur n'a pas répondu, categories/objets.md recette 5 ; lentille allumée + traînée de vapeur `trans_` le long de
la hampe par overlay_vol). Repère : pointe vers +Y, axe en x = z = 8, du talon (y = -7,5) à la pointe (y = 23,7), plat face à +Z.
En main (mesuré par objet.matrice_main / matrice_premiere) : en 3e personne +a part devant et **+b monte** ; en 1re personne +a
monte vers l'avant et +b descend : la buse crache le long de (cos 65° a ; sin 65° b) : monte en 3e personne, à peu près
horizontale en 1re.

Objet vivant (guide 14) :
- item_idle (24 s) : la pression monte par crans (servo : échelon, dépassement, rappel), la soupape tremble puis se soulève, deux
  décharges de white_smoke à la buse par ctrl_emit ; **sans son** ;
- item_gui : figé, vapeur coupée ;
- item_use (1,2 s, étape leve) : l'aiguille monte au rouge avec q.use_progress et y tremble, la soupape frémit ; sans son ;
- event_release (0,9 s) : au lancer, la buse crache un jet qui monte (`trans_jet` = seul dépliage par scale, ctrl_alpha,
  ctrl_emit +5), l'aiguille retombe, la soupape claque ; **seul son** block.fire.extinguish à 0,04 s (arme lancée : au tir) ;
- event_select (0,8 s) : arrivée en main : tour d'essai de l'aiguille par crans, la soupape claque une fois ;
- event_swing (0,4 s) : coup au corps à corps : l'aiguille perd un cran et remonte ; sans son ;
- overlay_vol (1,2 s) : traînée de 8 bouffées de vapeur (étape lance, dessinée en vol seulement), échelle propre à chacune.
Aucun son sur event_use_start ni event_enter_* ; jet caché au repos (géométrie F_GEO / K dans la buse, clés scale <= 8).

Fonctions avancées : calque _e (cadrans, fentes des foyers, lentille), trans_jet et trans_ de la traînée, ctrl_alpha,
emit_mc_white_smoke, ctrl_emit, scale et position animés, étapes, Molang (q.use_progress), animations d'objet. Non simulés par
l'aperçu : animations en main, particules, ctrl_emit, son. À juger en jeu : la fourche dans la case, item_use (aiguille au
rouge), event_release (jet, son), overlay_vol et l'orientation en vol (attente du développeur).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402


AVEC_E = True
NOM = "skin_trident_steampunk"
TEX = 512
TAU = 2 * math.pi
K = 16.0            # facteur de réduction du jet au repos
F_GEO = 2.0         # géométrie F_GEO / K, clés scale <= K / F_GEO

GUI = float(os.environ.get("GUI", "0.6"))    # échelle de l'inventaire (celle de skin_trident_abyssal : ψ lisible dans la case)

# Repère : trident pointe vers +Y, axe en x = z = 8 ; a le long de la hampe (-> +Y, 0 au talon), b en travers (-> -X),
# z (-> +Z = inventaire). 31,2 px comme skin_trident_orage / skin_trident_abyssal (vanilla 31), prise à 16,7 px du talon.
A_MAX = 31.2
Y_BAS, Y_HAUT = -7.5, -7.5 + A_MAX
A_PRISE = 16.7
A_ = np.array((0.0, 1.0, 0.0))
W_ = np.array((-1.0, 0.0, 0.0))
T_ = np.array((0.0, 0.0, 1.0))
P0 = np.array((8.0, Y_BAS, 8.0))

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
A_O = 21.0                           # centre de la roue dentée (sertissage de la fourche, axe z)
O_ = np.array((A_O, 0.0))
R_RIM, R_DENT, GZ, TZ = 1.35, 1.80, 0.85, 0.6   # roue : rayon du flanc, bout des dents, demi-épaisseur, demi-épaisseur des dents
R_COL = R_RIM                        # la fourche naît dans la roue (racine cachée)
A_FIL = A_O + 0.3                    # en deçà, le bord est dans la roue : pas de biseau
R_H = 0.48                           # hampe (tube de vapeur)
RB = 0.92                            # chaudière de cuivre au talon
A_POLI0, A_POLI1 = 25.2, 26.4        # fil poli au-dessus (haut des dents) ; laiton en dessous (croissant, gorges)

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



# Fourche forgée : croissant sorti de la roue, deux dents latérales à ardillon tourné vers le bas sur leur dehors, gorges en U
# de ~1,8 px (en dessous, le ψ ne se lit pas à taille réelle : skin_trident_abyssal), dent centrale plus longue à pointe en
# losange. Contour fait de « courses » lissées (catmull) jointes à des sommets vifs (pointes, ardillons).
COURSES = [                      # demi-contour b >= 0, de la racine (dans la roue) à la pointe centrale
    [(20.7, 0.80), (21.6, 1.10), (22.4, 1.85), (23.0, 2.75), (23.55, 3.40), (24.15, 3.72), (24.85, 3.76)],  # croissant -> pied de l'ardillon
    [(24.85, 3.76), (24.20, 4.62)],                                       # dessous de l'ardillon (pointe vers le bas)
    [(24.20, 4.62), (25.5, 4.30), (26.6, 4.02), (27.8, 3.82), (29.0, 3.66), (29.55, 3.52)],   # dos de l'ardillon -> pointe latérale
    [(29.55, 3.52), (28.6, 3.02), (27.4, 2.74), (26.0, 2.60), (24.9, 2.46), (24.15, 1.98), (24.30, 1.16), (25.3, 0.84),
     (26.4, 0.78), (27.4, 0.82), (28.4, 1.16), (29.1, 1.24)],             # dedans de la dent latérale, gorge en U, dent centrale
    [(29.1, 1.24), (30.1, 0.74), (A_MAX, 0.0)],                           # pointe en losange
]
BARBE_PTS = [(24.20, 4.62), (24.20, -4.62)]      # pointes des ardillons (polies)


def demi_contour():
    out = []
    for i, c in enumerate(COURSES):
        pts = catmull(c, 4) if len(c) > 2 else np.array(c, float)
        out.extend([tuple(p) for p in (pts if i == 0 else pts[1:])])
    return out


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


# ------------------------------------------------------------------ vrai volume (acier plein, opaque)
Z_E = 0.10                       # demi-épaisseur au fil
T_BIS = 1.28                     # pente unique des biseaux (52°) : dents de 1,2-1,6 px, il reste un plat
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
    """Plaque biseautée fermée (repère de la fourche, u, w) : contour poly, fils (sans la racine cachée dans la roue), plat
    z = h0 + k (P - O)·u ; fil poli au haut des dents et aux ardillons, bords de laiton au croissant et dans les gorges ;
    gouttière en fuseau dans l'axe de la dent centrale ; reflets le long des lignes `centres`."""

    def __init__(self, nom, poly, fil, centres, u, h_racine, h_bout, g0, g1, gw):
        self.nom, self.poly = nom, poly
        self.u = unit(u)
        pa = np.array(poly) - O_
        s_ = pa @ self.u
        self.L = float(s_.max())
        s_r = 0.6
        self.k = (h_bout - h_racine) / (self.L - s_r)
        self.h0 = h_racine - self.k * s_r
        self.segs = subdiv(fil)
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
        self.centres = centres

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
        """1 sur les fils qui travaillent (haut des dents, ardillons : acier poli), 0 au croissant et dans les gorges (laiton)."""
        P = np.asarray(P, float)
        k = smv(P[..., 0], A_POLI0, A_POLI1)
        for q in BARBE_PTS:
            k = np.maximum(k, np.clip(1.35 - np.linalg.norm(P - np.array(q), axis=-1) / 0.55, 0, 1))
        return k

    def in_g(self, P):
        return in_poly(P, self.gpoly)

    def d_g(self, P):
        return d_poly(P, list(self.gpoly) + [self.gpoly[0]])

    def d_ax(self, P):
        return d_poly(P, self.gax)


_H = resample(demi_contour(), 0.45)
_B = [(a, -b) for a, b in _H[::-1]]
POLY = _H + _B[1:]                                # fermé par la racine (dans la roue)
_i0 = next(i for i, p in enumerate(_H) if p[0] >= A_FIL) - 1
FIL_FER = _H[_i0:] + _B[1:len(_B) - _i0]
G0, G1, GW = 23.4, 29.8, 0.22                     # gouttière dans l'axe de la dent centrale
CENTRES = []
for sg in (1, -1):
    CENTRES.append([(a, sg * b) for a, b in ((24.6, 3.15), (25.8, 3.32), (26.8, 3.34), (27.8, 3.30), (28.8, 3.28))])  # dents latérales
    CENTRES.append([(a, sg * b) for a, b in ((24.9, 0.52), (26.2, 0.50), (27.6, 0.54), (28.6, 0.70), (29.6, 0.56))])  # dent centrale
    CENTRES.append([(a, sg * b) for a, b in ((22.4, 1.25), (23.0, 2.05), (23.7, 2.75))])                             # croissant
FER = Fer("fer", POLY, FIL_FER, CENTRES, (1.0, 0.0), 0.80, 0.24, G0, G1, GW)
RIVETS = [(23.05, 1.25), (23.05, -1.25)]          # rivets de sertissage sur le croissant


def brosse(P, seed=0.0):
    """Brossé fin parallèle au fil (±4 %)."""
    s, r = P[..., 0], P[..., 1]
    return (np.sin((s * 0.35 + r) * 41.0 + seed) * 0.5 + np.sin((s * 0.35 + r) * 17.0 + s * 0.6 + seed * 3) * 0.5) * 0.04


# --- peintures de la fourche (acier bruni clair, fil poli sur les dents, bords de laiton ailleurs ; aucune lumière)
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
    dc = np.min(np.stack([d_poly(P2, c_) for c_ in pc.centres]), axis=0)
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
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + STEEL["low"] * 0.85
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


def p_ambre_eteint(xn, t, y, r, L, ex):
    """Lentille-témoin éteinte (étape repos) : verre ambre sombre, reflet, aucune lumière."""
    q = np.abs(xn + 0.25)
    col = lerp(A((176, 120, 52)), A((96, 58, 22)), np.clip(q / 1.2, 0, 1)[..., None] ** 0.9)
    return col, None


PEINTRES["ambre_eteint"] = p_ambre_eteint

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
TILES["jet"] = t_vapeur(128, 56, 71, plume=True)
TRANS.update({"jet"})

TILES["bouffee"] = t_vapeur(48, 48, 83, plume=False)
TRANS.update({"bouffee"})


# ------------------------------------------------------------------ conception
GROUPES = []        # (nom, pivot, parent, rotation)


def grp(nom, pivot, parent, rotation=(0.0, 0.0, 0.0)):
    GROUPES.append((nom, np.asarray(pivot, float), parent, rotation))
    return nom


def plaque_vapeur(g, nom, c, X, Y, half, tile):
    boite(g, nom, c, X, Y, 2 * np.asarray(half, float), {"south": tile, "north": tile})



def ang_dents():
    """Dents de la roue (angle en degrés depuis +a, vers +b) : 18 places, retirées là où passent fourche, douille et buse."""
    half_t = math.degrees(0.55 / 2 / R_DENT) + 1.5
    rel = np.array(POLY) - O_
    rr = np.linalg.norm(rel, axis=1)
    near = rel[(rr > R_RIM - 0.3) & (rr < R_DENT + 0.4)]
    angs = np.degrees(np.arctan2(near[:, 1], near[:, 0]))
    f0, f1 = angs.min() - half_t, angs.max() + half_t
    obst = [(180.0, math.degrees(math.atan(0.80 / R_RIM)) + half_t), (B_ANG, math.degrees(math.atan(0.34 / R_RIM)) + half_t)]
    dif = lambda a, b: abs((a - b + 180) % 360 - 180)
    out = []
    for k in range(18):
        th = (10 + 20 * k + 180) % 360 - 180
        if f0 <= th <= f1 or any(dif(th, c) < w for c, w in obst):
            continue
        out.append(th)
    return out


B_ANG = 65.0                         # buse à 65° de l'axe, côté +b : la vapeur monte en main (3e personne), horizontale en 1re
E_JET = Wv(math.cos(math.radians(B_ANG)), math.sin(math.radians(B_ANG)))     # direction de la buse (monde)
SOUP_DIR = W_                        # soupape de la chaudière sur le dessus en main (+b)
L_BUSE = 1.4
A_FOYER, A_SOUP, A_LENT = 2.45, 4.1, 4.15
OUT = {}


def lentille(g, nom, mat):
    """Lentille-témoin en dôme sur les deux faces de la chaudière (verre ambre serti de laiton)."""
    for s in (1, -1):
        tour(g, f"{nom}_{'pm'[s < 0]}", Wp(A_LENT, 0, s * (RB - 0.04)), T_ * s, A_,
             [(0.0, 0.27, 0.12, 0.27, "laiton", {"arete": True}), (0.12, 0.27, 0.14, 0.2, "laiton", {"clair": 0.15}),
              (0.14, 0.2, 0.22, 0.15, mat, {}), (0.22, 0.15, 0.27, 0.0, mat, {})], n=8, phase=math.pi / 8)


def conception():
    commun = grp("trident_steampunk", Wp(A_PRISE), None)

    # --- œillet de ligne de laiton au talon (axe z) : on y attache la corde du harpon
    tour(commun, "oeillet", Wp(0.56, 0, -0.17), T_, A_,
         [(0.0, 0.30, 0.0, 0.56, "laiton", {}), (0.0, 0.56, 0.34, 0.56, "laiton", {"arete": True}),
          (0.34, 0.56, 0.34, 0.30, "laiton", {"clair": -0.1}), (0.34, 0.30, 0.0, 0.30, "laiton", {"clair": -0.25})], n=12)

    # --- hampe : chaudière de cuivre rivetée au talon, tube d'acier bruni à bagues de laiton, poignée de cuir, douille de laiton
    prof = [(0.98, 0.0, 1.08, 0.40, "laiton", {"clair": 0.1})] + bague(1.08, 0.40, 0.52, 0.22)
    prof += [(1.30, 0.52, 1.45, RB, "cuivre", {"clair": 0.08})] + bague(1.45, RB, RB + 0.13, 0.3)
    prof += [(1.75, RB, 3.15, RB, "cuivre", {"riv": 0.5, "y0": 0.1})] + bague(3.15, RB, RB + 0.13, 0.3)
    prof += [(3.45, RB, 4.9, RB, "cuivre", {"riv": 0.5, "y0": 0.3})] + bague(4.9, RB, RB + 0.13, 0.3)
    prof += [(5.2, RB, 5.45, R_H, "cuivre", {"clair": -0.05})]
    prof += [(5.45, R_H, 9.0, R_H, "acier", {"clair": 0.1})] + bague(9.0, R_H, 0.62, 0.3)
    prof += [(9.3, R_H, 13.0, R_H, "acier", {"clair": 0.1})] + bague(13.0, R_H, 0.62, 0.3)
    prof += [(13.3, R_H, 14.7, R_H, "acier", {"clair": 0.1})] + bague(14.7, R_H, 0.74, 0.35)
    prof += [(15.05, 0.64, 18.35, 0.64, "cuir", {})] + bague(18.35, R_H, 0.74, 0.35)
    prof += [(18.7, 0.58, 19.6, 0.78, "laiton", {"clair": 0.05}), (19.6, 0.78, 19.95, 0.78, "laiton", {"arete": True})]
    tour(commun, "hampe", Wp(0), A_, T_, prof, n=12)
    # portes du foyer sur les deux faces de la chaudière (fentes rougeoyantes : le foyer chauffe l'eau)
    for s in (1, -1):
        boite(commun, f"foyer_{'pm'[s < 0]}", Wp(A_FOYER, 0, s * (RB + 0.05)), A_, W_, (1.1, 0.8, 0.1),
              {("south" if s > 0 else "north"): "foyer"})
    # soupape de la chaudière, sur le dessus en main (+b) : tige d'acier, chapeau de laiton mobile
    vb = Wp(A_SOUP, RB - 0.05)
    tour(commun, "soupape_tige", vb, SOUP_DIR, A_, [(0.0, 0.16, 0.45, 0.16, "acier", {})], n=8)
    soup = grp("soupape", vb + SOUP_DIR * 0.42, commun)
    tour(soup, "soupape_chapeau", vb, SOUP_DIR, A_, [(0.42, 0.16, 0.42, 0.3, "laiton", {}), (0.42, 0.3, 0.68, 0.3, "laiton", {"arete": True}),
                                                    (0.68, 0.3, 0.7, 0.13, "laiton", {}), (0.7, 0.13, 0.84, 0.13, "laiton", {"clair": 0.1}),
                                                    (0.84, 0.13, 0.87, 0.0, "laiton", {"clair": 0.2})], n=8)

    # --- roue dentée de laiton (flanc à 24 pans, faces découpées par l'alpha, dents en boîtes), manomètres sur les deux faces
    tete = grp("tete", Wp(A_O), commun)
    C = Wp(A_O)
    tour(tete, "flanc", C - T_ * GZ, T_, A_, [(0.0, R_RIM, 2 * GZ, R_RIM, "laiton", {"arete": True})], n=24)
    for s in (1, -1):
        boite(tete, f"roue_{'pm'[s < 0]}", C + T_ * s * (GZ + 0.02 - TH / 2), A_ * s, W_, (2 * R_PL, 2 * R_PL, TH), {"south": "roue"})
    dents = ang_dents()
    OUT["dents"] = dents
    for k, th in enumerate(dents):
        e = Wv(math.cos(math.radians(th)), math.sin(math.radians(th)))
        t_ = np.cross(T_, e)
        boite(tete, f"dent{k}", C + e * (R_RIM + 0.22), e, t_, (0.55, 0.5, 2 * TZ), {f: "dent" for f in SIX})
    for s in (1, -1):
        cs = "pm"[s < 0]
        tour(tete, f"lunette_{cs}", C + T_ * s * (GZ - 0.12), T_ * s, A_,
             [(0.0, 0.74, 0.32, 0.74, "laiton", {"arete": True}), (0.32, 0.74, 0.38, 0.62, "laiton", {"clair": 0.2})], n=16)
        boite(tete, f"cadran_{cs}", C + T_ * s * (GZ + 0.14), -W_, A_, (1.36, 1.36, 0.12),
              {"south": "cadran"} if s > 0 else {"north": "cadran_m"})
    a0 = math.radians(-120 + 40 * 1.0)             # niveau 1 au repos
    dn = A_ * math.cos(a0) - W_ * math.sin(a0)
    aig = grp("aiguille", C, tete)
    for s in (1, -1):
        c0 = C + T_ * s * (GZ + 0.24)
        boite(aig, f"aiguille_{'pm'[s < 0]}", c0 + dn * 0.24, np.cross(dn, T_), dn, (0.13, 0.58, 0.06), {f: "aiguille" for f in SIX})
        boite(aig, f"moyeu_{'pm'[s < 0]}", c0 + T_ * s * 0.02, A_, W_, (0.18, 0.18, 0.1), {f: "laiton_b" for f in SIX})

    # --- buse de cuivre sur la roue, côté +b (bague de laiton, pavillon évasé à gorge de suie)
    pb = C + E_JET * (R_RIM - 0.3)
    tour(tete, "buse", pb, E_JET, T_, [(0.0, 0.24, 0.9, 0.24, "cuivre", {})] + bague(0.3, 0.24, 0.32, 0.22)
         + [(0.9, 0.24, 0.9, 0.2, "laiton", {}), (0.9, 0.2, L_BUSE - 0.05, 0.42, "laiton", {"clair": 0.1}),
            (L_BUSE - 0.05, 0.42, L_BUSE, 0.42, "laiton", {"arete": True}), (L_BUSE, 0.42, L_BUSE - 0.04, 0.0, "suie", {})],
         n=8, phase=math.pi / 8)

    # --- fourche d'acier bruni en vrai volume (plaque biseautée fermée, gouttière creusée)
    fer = grp("fer", C, tete)
    volume(FER, fer)
    gouttiere(FER, fer)

    # --- jet de la buse (caché au repos dans le pavillon, F_GEO / K) ; pivot à sa base : il jaillit vers l'extérieur
    mouth = C + E_JET * (R_RIM - 0.3 + L_BUSE)
    jb = mouth - E_JET * 0.6
    JL, JW = 4.5, 2.6
    nperp = unit(np.cross(E_JET, T_))
    jet = grp("trans_jet", jb, commun)
    for k in range(3):
        ang = math.radians(60 * k + 30)
        Yp = T_ * math.cos(ang) + nperp * math.sin(ang)
        plaque_vapeur(jet, f"jet{k}", jb + E_JET * (JL / 2 * F_GEO / K), E_JET, Yp, np.array((JL / 2, JW / 2 * 0.8, 0.15)) * F_GEO / K, "jet")
    grp("ctrl_alpha", jb, jet)
    rz = math.degrees(math.atan2(E_JET[1], E_JET[0])) - 90      # +Y du groupe le long de la buse
    em = grp("emit_mc_white_smoke", mouth + E_JET * 0.1, commun, rotation=(0.0, 0.0, rz))
    grp("ctrl_emit", mouth + E_JET * 0.1, em)

    # --- étapes (groupes racine, guide 14) : lentille-témoin éteinte au repos, allumée armé et en vol ; traînée de vapeur en vol
    repos = grp(objet.etape("repos", "trident"), Wp(A_PRISE), None)
    leve = grp(objet.etape("leve", "trident"), Wp(A_PRISE), None)
    lance = grp(objet.etape("lance", "trident"), Wp(A_PRISE), None)
    lentille(repos, "lentille_repos", "ambre_eteint")
    lentille(leve, "lentille_leve", "ambre")
    lentille(lance, "lentille_vol", "ambre")
    OUT["sillage"] = []
    rng = np.random.default_rng(29)
    for j in range(8):
        a = 18.5 - j * 2.0
        ph = rng.uniform(0, TAU)
        rr = rng.uniform(0.9, 1.4)
        c = Wp(a, rr * math.cos(ph), rr * math.sin(ph))
        g = grp(f"trans_traine{j}", c, lance)
        s_ = rng.uniform(1.3, 1.9)
        plaque_vapeur(g, f"traine{j}_a", c, A_, W_, (s_ / 2, s_ / 2, 0.15), "bouffee")
        plaque_vapeur(g, f"traine{j}_b", c + T_ * 0.02, A_, T_, (s_ / 2 * 0.85, s_ / 2 * 0.85, 0.15), "bouffee")
        OUT["sillage"].append(g)
    OUT.update(commun=commun, aiguille=aig, soupape=soup, jet=jet)
    return [commun, repos, leve, lance]


RACINES = conception()


# ------------------------------------------------------------------ atlas
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


outliner = [bone_node(r) for r in RACINES]

# ------------------------------------------------------------------ animations (objet vivant, guide 14)
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



AIG, SOUP, JET = OUT["aiguille"], OUT["soupape"], OUT["jet"]
CE = "ctrl_emit"


def valve(t, tps, trem):
    y = 0.035 * trem * math.sin(TAU * 23 * t + 0.7)
    for tp in tps:
        y += 0.24 * (step(t - tp, rise=0.035, over=0.2) - step(t - tp - 0.18, rise=0.04, over=0.35))
    return le_long(y, SOUP_DIR)


# --- item_idle (24 s) : deux cycles de pression ; quatre crans, tremblement, décharge (soupape + vapeur à la buse), sans son
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
    (CE, "position"): idle_emit}, fps=30)

# --- item_gui : figé (net dans l'inventaire), vapeur coupée
item_gui = anim("item_gui", 4.0, {(CE, "position"): (-1, 0, 0)})

# --- event_select (0,8 s) : tour d'essai de l'aiguille par crans, la soupape claque une fois
L_SEL = 0.8


def sel_needle(t):
    lvl = sum(step(t - ti) for ti in (0.2, 0.3, 0.4)) - 3 * step(t - 0.58, rise=0.08, over=0.1)
    return needle(lvl)


event_select = anim("event_select", L_SEL, {
    (AIG, "rotation"): sel_needle,
    (SOUP, "position"): lambda t: valve(t, [0.6], 0.0)}, fps=40, loop="once")

# --- item_use (1,2 s en boucle, étape leve) : l'aiguille monte au rouge avec q.use_progress et y tremble, la soupape frémit,
# vapeur coupée (la pression est retenue) ; sans son. Molang : niveau 1 -> 5,3 (zone rouge) quand q.use_progress atteint 0,77.
L_USE = 1.2
LVL_USE = 4.3
AIG_USE = (f"-40*({LVL_USE}*math.clamp(q.use_progress*1.3,0,1)"
           f"+0.12*math.clamp(q.use_progress*1.3,0,1)*math.sin(q.anim_time*360*7/{L_USE}))")
item_use = anim("item_use", L_USE, {
    (AIG, "rotation"): (0, 0, AIG_USE),
    (SOUP, "position"): lambda t: le_long(0.03 + 0.03 * math.sin(TAU * 12 * t / L_USE), SOUP_DIR),
    (CE, "position"): (-1, 0, 0)}, fps=30)

# --- event_swing (0,4 s) : coup au corps à corps, l'aiguille perd un cran et remonte ; sans son
L_ESW = 0.4
event_swing = anim("event_swing", L_ESW, {
    (AIG, "rotation"): lambda t: needle(-(step(t - 0.05, rise=0.03, over=0.15) - step(t - 0.22, rise=0.08, over=0.12)))},
    fps=60, loop="once")

# --- event_release (0,9 s) : au lancer, jet qui jaillit de la buse et monte (seul dépliage par scale), soupape, aiguille qui
# retombe du rouge ; seul son
L_REL = 0.9


def jet_scale(t):
    w = sm(t, 0.03, 0.1) * (1 + 0.3 * sm(t, 0.1, 0.4)) * (1 - sm(t, 0.5, 0.62))
    k = (1 + (K - 1) * w) / F_GEO
    return k, k, k


event_release = anim("event_release", L_REL, {
    (JET, "scale"): jet_scale,
    (JET, "position"): lambda t: le_long(1.4 * sm(t, 0.08, 0.6) * (1 - sm(t, 0.62, 0.66)), E_JET),
    ("ctrl_alpha", "position"): lambda t: (-sm(t, 0.28, 0.6) * (1 - sm(t, 0.66, 0.7)), 0.0, 0.0),
    (CE, "position"): lambda t: (5 * bump(t, 0.03, 0.06, 0.3, 0.45), 0.0, 0.0),
    (SOUP, "position"): lambda t: valve(t, [0.02], 0.0),
    (AIG, "rotation"): lambda t: needle(-2 * (step(t - 0.03, rise=0.06, over=0.1) - step(t - 0.45, rise=0.2, over=0.08)))},
    fps=40, loop="once")

# --- overlay_vol (1,2 s, étape lance dessinée en vol seulement) : chaque bouffée naît près de la roue, glisse vers le talon en
# grossissant puis s'efface (échelle) ; seule animation qui met ces bouffées à l'échelle.
L_OV = 1.2
overlay_vol = {"uuid": nuid(), "name": "overlay_vol", "loop": "loop", "override": False, "length": L_OV, "snapping": 24,
               "selected": False, "animators": {}}
for j, g in enumerate(OUT["sillage"]):
    ph = (j * 0.37) % 1.0
    tw = round((1 - ph) * L_OV, 4) % L_OV
    ts = sorted(set([round(L_OV * i / 12, 4) for i in range(13)] + ([round(tw - 0.001, 4), tw] if tw > 0.002 else [])))
    pos, sca = [], []
    for t in ts:
        u = (t / L_OV + ph) % 1.0
        if tw > 0.002 and abs(t - (tw - 0.001)) < 1e-6:
            u = 0.999
        if abs(t - L_OV) < 1e-6:
            u = ph
        pos.append(kf(t, *le_long(-3.0 * u, A_), ch="position"))
        sca.append(kf(t, *([max(0.02, math.sin(math.pi * u) ** 0.8 * (0.6 + 0.6 * u))] * 3), ch="scale"))
    overlay_vol["animators"][groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": pos + sca}

ANIMS = [item_idle, item_gui, item_use, event_select, event_swing, event_release, overlay_vol]
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
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
AFFICHAGE = objet.affichage("trident", **objet.affichage_trident(Y_BAS, Y_HAUT),
                            gui={"rotation": [0, 0, -45], "translation": [0, 0, 0], "scale": [GUI] * 3})
model = objet.modele(NOM, "trident", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son  # noqa: E402
limiter_sons(model)
# Seul son : event_release à 0,04 s (arme lancée : au tir ; jamais à 0,0 s, muet au premier lancer) ; ajouté après limiter_sons,
# qui ne connaît pas les états d'objet. Aucun son au repos, à la levée (event_use_start, event_enter_*), au coup ni à l'arrivée.
event_release["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "block.fire.extinguish")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))

print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur {float(P[:, 1].max() - P[:, 1].min()):.1f} px ; largeur {float(P[:, 0].max() - P[:, 0].min()):.1f} px ; "
      f"boîte {P.min(0).round(2)} .. {P.max(0).round(2)} ; gui {GUI} ; dents {OUT['dents']}")
gm = min(float(FER.h(np.array([p]))[0] - Z_FOND) for p in FER.gax)
marge = min(float(FER.dE(np.array([p]))[0] - FER.wb(np.array([p]))[0]) for p in FER.gl + FER.gr)
rel_ = np.array(POLY) - O_
rr_ = np.linalg.norm(rel_, axis=1)
amax = float(np.degrees(np.arctan2(rel_[:, 1], rel_[:, 0]))[(rr_ > R_RIM) & (rr_ < R_RIM + L_BUSE + 4.5)].max())
print(f"fourche : {FER.L:.2f} px, épaisseur {2 * FER.h(np.array([O_ + FER.u * 0.6]))[0]:.2f} -> {2 * FER.h(np.array([O_ + FER.u * FER.L]))[0]:.2f} px, "
      f"profondeur mini de gouttière {gm:.2f} px, marge gouttière/biseau {marge:.2f} px ; angle maxi du contour {amax:.1f}° (buse {B_ANG}°)")
print("Display :", json.dumps({k: AFFICHAGE[k] for k in ("thirdperson_righthand", "firstperson_righthand", "gui")}))
