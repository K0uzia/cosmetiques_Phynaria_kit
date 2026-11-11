"""Houe de l'orage : skin d'objet (guide 14) pour toutes les houes du joueur, ensemble Orage (thème Éléments). Design original.
Écrit skin_houe_orage.png, skin_houe_orage_e.png et .build/skin_houe_orage_brut.bbmodel à côté de ce script.
Point de départ : gen_skin_pelle_orage.py (matières, peinture, foudre, animations) et gen_skin_pioche_orage.py (manche, œil) ;
la tête est nouvelle (col de cygne + lame en travers, dans son propre repère).

Référence réelle (.claude/references/objets/houes.md) : houe à œil et col de cygne (fer forgé : œil qui prend le manche, col
recourbé, lame plate en travers de l'axe, fil trempé ; angle de travail lame/manche de 55 à 70°, la lame penchée vers la
poignée pour mordre puis tirer la terre). La lame est un vrai plat : large dans l'épaisseur de l'image (vue de +Z, comme
iron_hoe.png, on la voit par la tranche ; en main, on voit son plat et son fil).
Famille Orage (ailes_orage v7, skin_epee_orage, skin_pioche_orage, skin_pelle_orage, skin_hache_orage ; .claude/styles/orage.md) :
- acier d'orage bleu-noir martelé, bord poli clair, liseré d'or en retrait ;
- fil de la lame trempé : poli presque blanc (+ _e) puis bande de revenu cuivre et violet ;
- œil = tambour d'or aux trois virgules, coin d'or et pointe-paratonnerre de cristal au-dessus de l'œil (le bouton de la
  houe vanilla) ;
- âme de foudre : fente en zigzag à angles vifs dans le col (vue dans l'inventaire) et dans le plat de la lame (vue en main),
  où court un vrai trait de foudre en géométrie (cœur opaque + _e, gaine add_ en 3 sections : col, lame, lame) ;
- une dent d'éclair sur chaque flanc de la lame, décalées (comme l'épée et la pelle) ;
- manche de la pioche : pommeau à pointe de cristal, poignée de cuir bleu nuit entre bagues d'or, attelles rivetées.
Silhouette (reconnaissable sans la couleur) : crochet d'un seul côté (col recourbé + lame qui revient vers la poignée) et
pointe de cristal au bout de l'œil ; ni croissant à deux bras (pioche), ni large fer dans l'axe (pelle), ni lame le long du
manche (hache).
Vrai volume (.claude/references/objets/volume-3d.md, refait le 2026-11-08 après le retour en jeu « c'est des couches ») :
- col de cygne = barre à section octogonale aplatie qui s'affine (1,02 x 0,66 -> 0,82 x 0,62 px de demi-section), deux boîtes
  par tronçon (droite + tournée de 45°) découpées par l'alpha sur l'octogone ; gouttière de foudre creusée dans ses plats ;
- lame = plaque biseautée fermée (pente unique 40°, lame large), amincie 1,48 -> 0,56 px vers le fil, tous les bords biseautés
  sauf la base ; fil poli + _e, trempe cuivre/violet, liseré d'or des flancs peints sur les faces ; gouttière creusée (parois +
  fond), foudre couchée sur le fond de chaque côté ; nervure octogonale qui prolonge le col sur les deux plats ;
- bague d'or à 16 pans à la jonction col/lame ; œil = collet à 16 pans + tambour d'or à 16 pans ; pointe de cristal à facettes ;
- lame tournée de ROLL = 28° autour de son axe : dans l'inventaire on voit un peu son plat (par la tranche, elle se lisait comme
  un bout de pioche) ; arcs et décharges repliés sur des pivots cachés dans le métal.
Repère (catégorie objets, Recette) : comme iron_hoe.png vu de +Z : manche du bas à gauche vers le haut à droite (axe a), col et
lame vers le haut à gauche (+b) ; boîte centrée dans le bloc. Display vanilla item/handheld, gui réglé à la case.

Objet vivant (guide 14), sobre :
- item_idle (8 s) : la gaine des fentes vacille (Molang, 9 Hz), petites fourches sur le plat de la lame au hasard, arc en retour
  toutes les 3 à 8 s avec une petite décharge au fil ;
- item_swing (boucle 0,3 s) : à chaque coup la fente s'avive et le fil claque ;
- item_gui : gaine au repos, rien d'autre ;
- event_select (0,7 s) : un éclair venu d'en haut frappe la pointe-paratonnerre, court du col jusqu'à la lame, le fil décharge ;
- event_swing (0,35 s) : le geste de labour (la lame pique de 3° vers le sol puis revient), vague dans la fente ; le labour
  (clic droit sur l'herbe) fait balancer le bras : il doit jouer event_swing (supposé) ;
- event_hit (0,7 s) : décharge du fil, les arcs remontent les deux flancs de la lame, arcs en retour, frisson ;
  **le seul son** (embarqué, original : arc_houe) ;
- event_break (0,6 s) : bloc cassé : la lame mord (+5°) puis tire la terre (−2,5°) et revient ; le fil décharge dans le sol
  (éclairs ramifiés en éventail, deux formes alternées), gerbe emit_mc_electric_spark (ctrl_emit +7 pendant 0,2 s, coupée
  sinon) ; sans son (on casse beaucoup de blocs).
Chaque groupe replié n'est déplié que par une seule animation d'état et jamais par deux événements qui peuvent se superposer (les
échelles se multiplient) : états = petite décharge + fourches ; event_select = foudre du ciel + décharge du fil propre ;
event_hit = décharge du fil + arcs des flancs ; event_break = éclairs du sol ; event_swing ne déplie rien.
Éclairs repliés à 1/10 sur leur pivot au repos (invisibles figés, dans l'inventaire et animations coupées), dépliés par scale ×10,
allumés par ctrl_alpha.
Fonctions avancées : add_, ctrl_alpha, ctrl_emit + emit_mc_electric_spark, scale animé, calque _e, animations d'objet (item_idle,
item_swing, item_gui, event_select, event_swing, event_hit, event_break), Molang (q.life_time), son embarqué. À juger en jeu :
event_hit, event_break et item_swing (pas encore vérifiés par le développeur), event_swing au labour, son d'un objet, scale et
ctrl_alpha sur un objet, arcs add_ de jour, taille en 1re personne.
"""
import base64, io, json, math, os, random, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image, ImageDraw

NOM = "skin_houe_orage"
TEX = 512
TAU = 2 * math.pi
DENS = 20.0                     # texels par px sur les plaques
FOLD = 0.1                      # pièces repliées sur leur pivot au repos

METAL = np.array([(22, 24, 36), (46, 52, 72), (70, 78, 104), (112, 122, 154), (170, 182, 214)], np.float32)
OR = np.array([(130, 90, 30), (176, 128, 44), (220, 170, 60), (255, 230, 140)], np.float32)
CRIS = np.array([(40, 40, 120), (70, 90, 200), (130, 160, 255), (190, 208, 255), (232, 240, 255)], np.float32)
CUIR = np.array([(18, 20, 38), (34, 40, 70), (52, 62, 104)], np.float32)
CUIVRE = np.array((196, 118, 64), np.float32)
VIOLET = np.array((112, 88, 172), np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))



# ------------------------------------------------------------------ dessin
# Col : plan de l'image (a le long du manche, b en travers ; px), épaisseur selon Z. Lame : son propre repère (u de la racine vers
# le fil, w en travers, épaisseur selon la normale de ses plats), tourné de ROLL autour de son axe : dans l'inventaire on voit un
# peu son plat (vue par la tranche, elle se lisait comme un bout de pioche).
A_O = 17.3                                         # centre de l'œil (tambour)
A_TOP = A_O + 2.95                                 # bout de la pointe-paratonnerre
ANG = math.radians(58)                             # angle de travail : lame à 58° du manche, penchée vers la poignée
D_L = np.array((-math.cos(ANG), math.sin(ANG)))    # direction de la lame dans le plan (a, b)
N_L = np.array((D_L[1], -D_L[0]))                  # normale du dos de la lame (côté +a, vers l'extérieur)
NC = [(A_O, 0.0), (A_O + 0.6, 1.1), (A_O + 0.75, 2.0), (A_O + 0.3, 2.75)]   # axe du col de cygne
L_L = 3.6                                          # longueur de la lame
HW0, HW1 = 1.4, 2.35                               # demi-largeur de la lame à la racine et au fil
STEP_L = {1: (0.42, 0.26), -1: (0.6, 0.22)}        # dent d'éclair de chaque flanc (x, retrait), décalées
ROLL = math.radians(float(os.environ.get("ROLL", "28")))   # lame tournée autour de son axe (plat visible dans l'inventaire)


def bez(P, s):
    P = [np.array(p, float) for p in P]
    u = 1 - s
    c = u ** 3 * P[0] + 3 * u * u * s * P[1] + 3 * u * s * s * P[2] + s ** 3 * P[3]
    d = 3 * u * u * (P[1] - P[0]) + 6 * u * s * (P[2] - P[1]) + 3 * s * s * (P[3] - P[2])
    return c, d / np.linalg.norm(d)


R_L = bez(NC, 1.0)[0]                              # racine de la lame (bout du col)


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


def unit(v):
    return v / np.linalg.norm(v)


# --- contour de la lame (repère de la lame : u, w)
def hw_lisse(u):
    return HW0 + (HW1 - HW0) * max(u, 0.0) / L_L ** 1.0 * (max(u, 0.0) / L_L) ** 0.4


def hw(u, sg):
    x = u / L_L
    u0, r = STEP_L[sg]
    return hw_lisse(u) - r * sm(x, u0, u0 + 0.02)


def bout(w):
    return L_L + 0.07 * (1 - (w / HW1) ** 2)


def flanc_vif(sg):
    """Flanc en tronçons d'environ 0,9 px, dent d'éclair à angle vif, dernier point sur le fil."""
    x0, r = STEP_L[sg]
    us = x0 * L_L
    n1 = max(2, int(round((us - 0.3) / 0.9)) + 1)
    n2 = max(2, int(round((L_L - us) / 0.9)) + 1)
    a = [(u, sg * hw_lisse(u)) for u in np.linspace(0.3, us, n1)]
    b = [(u, sg * (hw_lisse(u) - r)) for u in np.linspace(us + 0.05, L_L, n2)]
    b[-1] = (bout(b[-1][1]), b[-1][1])
    return a + b


U_RAC, W_RAC = -0.2, 0.62                          # base de la lame, cachée sous la bague d'or
FP, FM = flanc_vif(1), flanc_vif(-1)
FIL_L = [(bout(w), w) for w in np.linspace(FP[-1][1], FM[-1][1], 6)]
P_LAME = [(U_RAC, W_RAC)] + FP + FIL_L[1:-1] + FM[::-1] + [(U_RAC, -W_RAC)]
FILS_L = list(P_LAME)                              # tous les bords sont biseautés, sauf la base (u = U_RAC)
TIP = (bout(0.0), 0.0)                             # milieu du fil (repère de la lame)
TIP_D = np.array((1.0, 0.0))
TIP_IN = (L_L - 0.6, 0.0)                          # pivot des décharges, caché dans le métal


def flanc(sg, u0=0.0, u1=L_L, n=48):
    return [(u, sg * hw(u, sg)) for u in np.linspace(u0, u1, n)]


EXT_P, EXT_M = flanc(1, 0.4, L_L - 0.05, 40), flanc(-1, 0.4, L_L - 0.05, 40)


def m_lame(P):
    return in_poly(P, P_LAME)


# --- section du col (plan de l'image) : octogone aplati qui s'affine de l'œil à la lame
def col_yh(s):
    return 1.02 - 0.2 * s                          # demi-largeur dans le plan de l'image


def col_zh(s):
    return 0.66 - 0.04 * s                         # demi-épaisseur (selon Z)


def col_m(s):
    return col_zh(s) + 0.7 * col_yh(s)             # chanfreins à 45° : |y| + |z| <= m


# fentes de foudre (gouttières) : col (vue dans l'inventaire) et plat de la lame (vue en main)
SLIT_C = []
for _k, _s in enumerate(np.linspace(0.5, 0.95, 5)):
    _c, _d = bez(NC, _s)
    _n = np.array((-_d[1], _d[0]))
    SLIT_C.append(tuple(_c + _n * (0.0, 0.17, -0.17, 0.12, 0.0)[_k]))
GW_C = [0.07, 0.17, 0.18, 0.16, 0.07]
SLIT_L = [(u, a) for u, a in zip(np.linspace(1.15, 2.75, 6), (0.0, 0.36, -0.34, 0.3, -0.26, 0.0))]
GW_L = [0.08, 0.2, 0.21, 0.2, 0.18, 0.07]
SLIT_W = 0.2


# ------------------------------------------------------------------ vrai volume (.claude/references/objets/volume-3d.md)
# Lame = plaque biseautée fermée (deux biseaux par tronçon de bord et par face, un plat incliné par face qui suit
# l'amincissement vers le fil) ; col et nervure = barres à section octogonale (deux boîtes par tronçon, faces découpées par
# l'alpha à leur intersection). Couleurs portées par les faces, échantillonnées texel par texel dans le plan de la pièce.
Z_E = 0.10                        # demi-épaisseur au bord (fil)
DF = 16.0                         # texels par px sur les faces des volumes
TH = 0.3                          # épaisseur des cubes de biseau, de plat, de paroi
RECOUV = 0.08                     # recouvrement des faces voisines
T_BIS = 0.85                      # pente unique des biseaux (40°) : lame large, il reste un grand plat
R_COL = 1.35                      # rayon (apothème) du collet de l'œil
O_ = np.array((A_O, 0.0))
H_L0, H_L1 = 0.74, 0.28           # demi-épaisseur de la lame à la racine -> au fil (1,48 -> 0,56 px)
K_L = (H_L1 - H_L0) / L_L
Z_FOND = 0.16


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


def cellules(P, f=1.7, seed=0.0):
    """Martelé : valeur constante par cellule (facettes de marteau), -0,5..0,5."""
    ix, iy = np.floor(P[..., 0] * f + 0.37 * np.floor(P[..., 1] * f)), np.floor(P[..., 1] * f)
    v = np.sin(ix * 127.1 + iy * 311.7 + seed * 74.7) * 43758.5453
    return v - np.floor(v) - 0.5


class Gout:
    """Gouttière : zigzag de la fente, demi-largeur par sommet (pointue aux deux bouts) ; bords en onglet."""

    def __init__(self, slit, gw):
        S = [np.array(p, float) for p in slit]
        nrm = []
        for i in range(len(S) - 1):
            d = unit(S[i + 1] - S[i])
            nrm.append(np.array((-d[1], d[0])))
        cotes = {}
        for sg in (1, -1):
            lignes = [(S[i] + sg * nrm[i] * gw[i], S[i + 1] + sg * nrm[i] * gw[i + 1]) for i in range(len(S) - 1)]
            pts = [lignes[0][0]]
            for i in range(len(lignes) - 1):
                (p1, p2), (p3, p4) = lignes[i], lignes[i + 1]
                d1, d2 = p2 - p1, p4 - p3
                den = d1[0] * d2[1] - d1[1] * d2[0]
                if abs(den) < 1e-9:
                    pts.append((p2 + p3) / 2)
                    continue
                t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / den
                pts.append(p1 + d1 * t)
            pts.append(lignes[-1][1])
            cotes[sg] = pts
        self.slit, self.cotes = slit, cotes
        self.poly = [tuple(p) for p in cotes[1]] + [tuple(p) for p in cotes[-1][::-1]]

    def inside(self, P):
        return in_poly(P, self.poly)

    def d(self, P):
        return d_poly(P, self.poly + [self.poly[0]])


GT_C, GT_L = Gout(SLIT_C, GW_C), Gout(SLIT_L, GW_L)


class Piece:
    """Plaque biseautée : contour `poly`, fils `fils` (polylignes, sans la base cachée), plat plan z = h0 + k (P - O)·u,
    bord à z = ze, pente de biseau t ; z0 décale toute la pièce (attelles), `cotes` = faces construites (+1, -1)."""

    def __init__(self, nom, poly, fils, O, u, h0, k, ze, peint_biseau, peint_plat, peint_fil, trou=None, t=T_BIS, z0=0.0,
                 cotes=(1, -1), trempe=None):
        self.nom, self.poly, self.O, self.u, self.h0, self.k, self.ze, self.t = nom, poly, np.array(O, float), unit(np.array(u, float)), h0, k, ze, t
        self.segs = [s for f in fils for s in subdiv(f)]
        self.peint_biseau, self.peint_plat, self.peint_fil, self.trou = peint_biseau, peint_plat, peint_fil, trou
        self.z0, self.cotes, self.trempe = z0, cotes, trempe

    def h(self, P):
        return self.h0 + self.k * ((np.asarray(P, float) - self.O) @ self.u)

    def wb(self, P):
        return np.maximum((self.h(P) - self.ze) / self.t, 0.02)

    def dE(self, P):
        return d_stack(P, self.segs).min(0)

    def surf(self, P):
        d, h, wb = self.dE(P), self.h(P), self.wb(P)
        return np.where(d < wb, self.ze + (h - self.ze) * np.clip(d / wb, 0, 1), h)


SPECS = []          # cubes du volume : dict(fr, groupe, nom, c, X, Y, s, faces) en coordonnées du plan de leur repère
TILES = {}          # tuiles échantillonnées : nom -> (rgba, rgba_e)
CUR_FR = ["img"]    # repère des specs en cours : "img" (col, manche) ou "lame"


def repere(X, Y):
    X = unit(np.asarray(X, float))
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


def finir(col, em, masque):
    rgba = np.zeros(col.shape[:2] + (4,), np.uint8)
    rgba[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    rgba[..., 3] = masque * 255
    rgba[~masque] = 0
    rgba_e = np.zeros_like(rgba)
    on = masque & (em.max(axis=-1) > 0)
    rgba_e[..., :3] = np.clip(em, 0, 255).astype(np.uint8)
    rgba_e[..., 3] = on * 255
    rgba_e[~on] = 0
    return rgba, rgba_e


def spec(groupe, nom, c, X, Y, s, peintures, dens=DF):
    """peintures : {face: fn(points (H, W, 3)) -> (col, em, masque)} ; les autres faces sont transparentes."""
    X, Y, Z = repere(X, Y)
    faces = {}
    for f, fn in peintures.items():
        P = points_face(np.asarray(c, float), X, Y, Z, s, f, dens)
        col, em, m = fn(P)
        if m.any():
            nomt = f"{nom}_{f}"
            TILES[nomt] = finir(col, em, m)
            faces[f] = nomt
    SPECS.append({"fr": CUR_FR[0], "groupe": groupe, "nom": nom, "c": np.asarray(c, float), "X": X, "Y": Y, "s": s, "faces": faces})


def volume(pc, groupe):
    """Biseaux (deux par tronçon de fil) + plats inclinés de la pièce pc."""
    for idx, (p, q, v0, v1) in enumerate(pc.segs):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        if not in_poly(np.array([(p + q) / 2 + n * 0.05]), pc.poly)[0]:
            n = -n
        pm = (p + q) / 2
        h, wb = float(pc.h(pm)), float(pc.wb(pm))
        al = math.atan2(h - pc.ze, wb)
        e0 = wb * 1.3 if v0 else 0.04
        e1 = wb * 1.3 if v1 else 0.04
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        sy = (wb + 0.08) / math.cos(al)
        for sg in pc.cotes:
            Y = np.array((n[0] * math.cos(al), n[1] * math.cos(al), sg * math.sin(al)))
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0], mid[1], pc.z0 + sg * pc.ze)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(P, idx=idx):
                P2 = P[..., :2]
                D = d_stack(P2, pc.segs)
                dE = D.min(0)
                m = in_poly(P2, pc.poly) & (D[idx] <= dE + RECOUV) & (dE < pc.wb(P2) + 0.03)
                col, em = pc.peint_biseau(pc, P2, dE)
                return col, em, m

            def fil(P, idx=idx, n=n):
                P2 = P[..., :2] + n * 0.06
                D = d_stack(P2, pc.segs)
                m = in_poly(P2, pc.poly) & (D[idx] <= D.min(0) + RECOUV)
                col, em = pc.peint_fil(pc, P2)
                return col, em, m

            spec(groupe, f"{pc.nom}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil})
    u = pc.u
    pp = np.array((-u[1], u[0]))
    pa = np.array(pc.poly) - pc.O
    s_, t_ = pa @ u, pa @ pp
    s0, s1, t0, t1 = s_.min() - 0.05, s_.max() + 0.05, t_.min() - 0.05, t_.max() + 0.05
    Pc = pc.O + u * (s0 + s1) / 2 + pp * (t0 + t1) / 2
    for sg in pc.cotes:
        X = unit(np.array((u[0], u[1], sg * pc.k)))
        Y = sg * np.array((pp[0], pp[1], 0.0))
        Z = np.cross(X, Y)
        c = np.array((Pc[0], Pc[1], pc.z0 + sg * float(pc.h(Pc)))) - Z * (TH / 2)

        def plat(P):
            P2 = P[..., :2]
            dE = pc.dE(P2)
            m = in_poly(P2, pc.poly) & (dE >= pc.wb(P2) - 0.03)
            if pc.trou is not None:
                m &= ~pc.trou.inside(P2)
            col, em = pc.peint_plat(pc, P2, dE)
            return col, em, m

        spec(groupe, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, ((s1 - s0) * math.sqrt(1 + pc.k ** 2), t1 - t0, TH), {"south": plat})


def octa(groupe, nom, segs, Yv, dims, gout=None, bout_ferme=False):
    """Barre à section octogonale le long de segs [(p, q)] (points du plan, 3D) ; Yv(i) = axe Y de la section (Z = X × Y),
    dims(i) = (yh, zh, m) : |y| <= yh, |z| <= zh, |y| + |z| <= m. Deux boîtes par tronçon (A droite, B tournée de 45°),
    faces découpées par l'alpha sur l'octogone (intersection des deux) et au tronçon le plus proche (recouvrement 0,08)."""
    chords = [(np.asarray(p, float)[:2], np.asarray(q, float)[:2]) for p, q in segs]
    n = len(segs)
    for i, (p, q) in enumerate(segs):
        p, q = np.asarray(p, float), np.asarray(q, float)
        X = unit(q - p)
        Y = np.asarray(Yv(i), float)
        Y = unit(Y - (Y @ X) * X)
        Z = np.cross(X, Y)
        yh, zh, m = dims(i)
        e0 = 0.3 if i > 0 else 0.02
        e1 = 0.3 if i < n - 1 else 0.02
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        c = (p - X * e0 + q + X * e1) / 2

        def own(P, i=i):
            D = d_stack(P[..., :2], chords)
            return D[i] <= D.min(0) + RECOUV

        def loc(P, c=c, Y=Y, Z=Z):
            R = P - c
            return R @ Y, R @ Z

        def fA_z(P, yh=yh, zh=zh, m=m, own=own, loc=loc):
            y, z = loc(P)
            msk = own(P) & (np.abs(y) <= m - zh + 0.02)
            if gout is not None:
                msk &= ~gout.inside(P[..., :2])
            col, em = peint_octa("plat", P, y, z, (yh, zh, m), gout)
            return col, em, msk

        def fA_y(P, yh=yh, zh=zh, m=m, own=own, loc=loc):
            y, z = loc(P)
            msk = own(P) & (np.abs(z) <= m - yh + 0.02)
            col, em = peint_octa("cote", P, y, z, (yh, zh, m))
            return col, em, msk

        def fB(P, yh=yh, zh=zh, m=m, own=own, loc=loc):
            y, z = loc(P)
            msk = own(P) & (np.abs(y) <= yh + 0.02) & (np.abs(z) <= zh + 0.02)
            col, em = peint_octa("chanf", P, y, z, (yh, zh, m))
            return col, em, msk

        def cap(P, yh=yh, zh=zh, m=m, loc=loc):
            y, z = loc(P)
            msk = (np.abs(y) <= yh) & (np.abs(z) <= zh) & (np.abs(y) + np.abs(z) <= m)
            col, em = peint_octa("chanf", P, y, z, (yh, zh, m))
            return col, em, msk

        fa = {"south": fA_z, "north": fA_z, "up": fA_y, "down": fA_y}
        if bout_ferme and i == n - 1:
            fa["east"] = cap
        spec(groupe, f"{nom}A{i}", c, X, Y, (Ln, 2 * yh, 2 * zh), fa)
        spec(groupe, f"{nom}B{i}", c, X, unit(Y + Z), (Ln, m * math.sqrt(2), m * math.sqrt(2)), {f: fB for f in ("south", "north", "up", "down")})


def peint_octa(kind, P, y, z, dims, gout=None):
    """Col et nervure : plats martelés bleu-noir à liseré d'or et arête d'ombre, chanfreins polis clairs, côtés d'acier."""
    yh, zh, m = dims
    P2 = P[..., :2]
    base = np.zeros(P.shape[:-1] + (3,), np.float32)
    em = np.zeros_like(base)
    if kind == "plat":
        fl = m - zh
        ay = np.abs(y)
        col = base + lerp(METAL[2], METAL[1], 0.35) + cellules(P2, 1.8, 3.0)[..., None] * 16
        orl = (ay >= fl - 0.27) & (ay < fl - 0.15)
        if gout is not None:
            dg = gout.d(P2)
            orl &= dg > 0.2
        col[orl] = OR[2]
        col[orl & (ay < fl - 0.23)] = OR[3]
        col[ay >= fl - 0.06] = METAL[0]
        if gout is not None:
            levre = dg < 0.07
            col[levre] = (190, 208, 255)
            em[levre] = (60, 100, 210)
            col[(dg >= 0.07) & (dg < 0.13)] = METAL[0]
    elif kind == "cote":
        col = base + lerp(METAL[3], METAL[2], 0.5) + cellules(P2 + 7, 2.0, 4.0)[..., None] * 12
        col[np.abs(z) >= (m - yh) - 0.05] = METAL[1]
    else:
        col = base + lerp(METAL[4], METAL[3], 0.45) + cellules(P2 + 3, 2.2, 5.0)[..., None] * 8
    return col, em


# --- peintures de la lame et des attelles (couleurs portées par les faces des volumes)
def appliquer_trempe(pc, P, col):
    if pc.trempe is None:
        return np.zeros(P.shape[:-1], bool)
    d, (j0, j1, j2, j3) = pc.trempe(P)
    po = d < j0
    col[po] = lerp(METAL[4], np.array((236, 244, 255), np.float32), np.clip(1 - d[po] / j0, 0, 1)[..., None])
    cu = (d >= j0) & (d < j1)
    col[cu] = lerp(col[cu], CUIVRE, 0.85)
    vi = (d >= j1) & (d < j2)
    col[vi] = lerp(col[vi], VIOLET, 0.7)
    col[(d >= j2) & (d < j3)] = METAL[0]
    return d < j3


def peint_biseau_fer(pc, P, dE):
    f = dE / pc.wb(P)
    nz = cellules(P, 2.2, 1.0)[..., None]
    col = lerp(METAL[3], METAL[2], np.clip((f[..., None] - 0.70) / 0.2, 0, 1)) + nz * 10
    col = np.where((f < 0.3)[..., None], lerp(METAL[4], METAL[3], np.clip((f[..., None] - 0.08) / 0.22, 0, 1)) + nz * 6, col)
    em = np.zeros(col.shape, np.float32)
    tr = appliquer_trempe(pc, P, col)
    orl = (f >= 0.44) & (f < 0.66) & ~tr                       # liseré d'or sur le biseau des flancs
    col[orl] = OR[2]
    col[orl & (f < 0.52)] = OR[3]
    col[f >= 0.93] = METAL[0]                                   # arête du plat : trait d'ombre net
    if pc.trempe is not None:
        d, (j0, j1, j2, j3) = pc.trempe(P)
        vif = (f < 0.16) & (d < j2)
        col[vif] = (236, 244, 255)
        em[vif] = (110, 150, 235)
    return col, em


def peint_fil_fer(pc, P):
    col = np.zeros(P.shape[:-1] + (3,), np.float32) + METAL[4]
    em = np.zeros_like(col)
    if pc.trempe is not None:
        d, (j0, j1, j2, j3) = pc.trempe(P)
        vif = d < j2
        col[vif] = (236, 244, 255)
        em[vif] = (110, 150, 235)
    return col, em


def peint_plat_fer(pc, P, dE):
    wb = pc.wb(P)
    nz = cellules(P, 1.6, 2.0)[..., None]
    col = lerp(METAL[2], METAL[1], np.clip((dE[..., None] - wb[..., None] - 0.1) / 0.5, 0, 1) * 0.6) + nz * 16
    appliquer_trempe(pc, P, col)
    col[dE < wb + 0.04] = METAL[0]
    em = np.zeros(col.shape, np.float32)
    if pc.trou is not None:
        dg = pc.trou.d(P)
        levre = dg < 0.07
        col[levre] = (190, 208, 255)
        em[levre] = (60, 100, 210)
        col[(dg >= 0.07) & (dg < 0.13)] = METAL[0]
        orl = (dg >= 0.19) & (dg < 0.27) & (dE > wb + 0.1)
        col[orl] = OR[2]
        col[orl & (dg < 0.22)] = OR[3]
    return col, em


def peint_biseau_att(pc, P, dE):
    f = dE / pc.wb(P)
    nz = cellules(P, 2.4, 6.0)[..., None]
    col = lerp(METAL[4], METAL[3], np.clip(f[..., None] / 0.7, 0, 1)) + nz * 8
    col[f >= 0.9] = METAL[1]
    return col, np.zeros(col.shape, np.float32)


def peint_fil_att(pc, P):
    col = np.zeros(P.shape[:-1] + (3,), np.float32) + METAL[3]
    return col, np.zeros_like(col)


def peint_plat_att(pc, P, dE):
    nz = cellules(P, 1.8, 7.0)[..., None]
    col = lerp(METAL[3], METAL[2], 0.55) + nz * 14 + np.zeros(P.shape[:-1] + (3,), np.float32)
    col[dE < pc.wb(P) + 0.04] = METAL[0]
    return col, np.zeros(col.shape, np.float32)


LAME_P = Piece("lame", P_LAME, [FILS_L], (0.0, 0.0), (1.0, 0.0), H_L0, K_L, Z_E, peint_biseau_fer, peint_plat_fer, peint_fil_fer,
               trou=GT_L, t=T_BIS, trempe=lambda P: (d_poly(P, FIL_L), (0.5, 0.74, 0.98, 1.05)))
# Attelles (langets) : bandes d'acier biseautées posées sur les faces avant et arrière de la hampe, pointues vers le bas.
A_AT0, A_AT1, W_AT = A_O - 1.1, A_O - 5.4, 0.38
POLY_AT = [(A_AT0, W_AT), (A_AT1 + 0.8, W_AT), (A_AT1, 0.0), (A_AT1 + 0.8, -W_AT), (A_AT0, -W_AT)]
Z_HAMPE = 0.53
ATTELLES = [Piece(f"attelle{'pm'[sg < 0]}", POLY_AT, [POLY_AT], O_, (1.0, 0.0), 0.2, 0.0, 0.05, peint_biseau_att, peint_plat_att,
                  peint_fil_att, t=0.6, z0=sg * Z_HAMPE, cotes=(sg,)) for sg in (1, -1)]

# col : axe du col de cygne (plan de l'image), prolongé sous la bague d'or
_S_COL = np.linspace(0.0, 1.0, 10)
_PC = [bez(NC, s)[0] for s in _S_COL] + [R_L + D_L * 0.15]
COL_SEGS = [((_PC[i][0], _PC[i][1], 0.0), (_PC[i + 1][0], _PC[i + 1][1], 0.0)) for i in range(len(_PC) - 1)]
_S_MID = [min(1.0, (_S_COL[i] + _S_COL[i + 1]) / 2) if i < len(_S_COL) - 1 else 1.0 for i in range(len(COL_SEGS))]
_DENSE = np.array([bez(NC, s)[0] for s in np.linspace(0, 1, 120)])
_DENSE_S = np.linspace(0, 1, 120)


def col_dims(i):
    s = _S_MID[i]
    return col_yh(s), col_zh(s), col_m(s)


def col_Y(i):
    p, q = np.array(COL_SEGS[i][0]), np.array(COL_SEGS[i][1])
    d = unit(q - p)
    return (-d[1], d[0], 0.0)


def surf_col(P):
    """Hauteur du plat du col (z) au point P du plan."""
    D = np.linalg.norm(P[..., None, :] - _DENSE, axis=-1)
    return col_zh(_DENSE_S[D.argmin(-1)])


# nervure : le col se prolonge sur les deux plats de la lame (repère de la lame), s'affine et meurt avant la gouttière
_U_RIB = np.linspace(-0.25, 1.0, 6)
RIB_SEGS = [((_U_RIB[i], 0.0, 0.0), (_U_RIB[i + 1], 0.0, 0.0)) for i in range(len(_U_RIB) - 1)]


def rib_dims(i):
    um = (_U_RIB[i] + _U_RIB[i + 1]) / 2
    x = (um - _U_RIB[0]) / (_U_RIB[-1] - _U_RIB[0])
    zr = float(LAME_P.h0 + LAME_P.k * um) + 0.2 - 0.15 * x
    wr = 0.6 - 0.36 * x
    return wr, zr, max(zr, wr) + 0.6 * min(zr, wr)


def gouttiere(gt, groupe, surf, pre):
    """Fond (âme de 0,32 px où repose la foudre) + parois verticales le long des deux bords, sur chaque face."""
    pa = np.array(gt.poly)
    a0, a1, b0, b1 = pa[:, 0].min() - 0.15, pa[:, 0].max() + 0.15, pa[:, 1].min() - 0.15, pa[:, 1].max() + 0.15

    def fond(P):
        P2 = P[..., :2]
        m = gt.inside(P2) | (gt.d(P2) < 0.1)
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + np.array((16, 18, 34), np.float32) + cellules(P2, 3.0, 5.0)[..., None] * 6
        em = np.zeros_like(col) + np.array((14, 22, 70), np.float32)
        return col, em, m

    spec(groupe, f"{pre}fond", ((a0 + a1) / 2, (b0 + b1) / 2, 0.0), (1, 0, 0), (0, 1, 0), (a1 - a0, b1 - b0, 2 * Z_FOND),
         {"south": fond, "north": fond})
    murs = []
    for sg, pts in gt.cotes.items():
        for i in range(len(pts) - 1):
            murs.append((pts[i], pts[i + 1]))
    murs.append((gt.cotes[1][0], gt.cotes[-1][0]))
    murs.append((gt.cotes[1][-1], gt.cotes[-1][-1]))
    for j, (p, q) in enumerate(murs):
        p, q = np.asarray(p, float), np.asarray(q, float)
        if np.linalg.norm(q - p) < 0.03:
            continue
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        mid = (p + q) / 2
        inside_pt = mid - n * 0.05
        if not (gt.inside(np.array([inside_pt]))[0] or gt.d(np.array([inside_pt]))[0] < 1e-3):
            n = -n
        back = [p + n * TH, q + n * TH, mid + n * TH]
        top = min(float(surf(np.array([x]))[0]) for x in back + [p, q]) - 0.03
        z0 = Z_FOND - 0.04
        Ln = float(np.linalg.norm(q - p))
        for sg in (1, -1):
            zc = sg * (z0 + top) / 2
            X = np.array((d[0], d[1], 0.0))
            Y = np.array((0.0, 0.0, 1.0))
            Z = np.cross(X, Y)
            face = "south" if Z[:2] @ n < 0 else "north"

            def paroi(P):
                P2 = P[..., :2]
                dz = surf(P2) - np.abs(P[..., 2])
                col = lerp(METAL[1], METAL[0], np.clip((dz[..., None] - 0.1) / 0.3, 0, 1)) + np.zeros(P.shape[:-1] + (3,), np.float32)
                em = np.zeros_like(col)
                lv = dz < 0.1
                col[lv] = (190, 208, 255)
                em[lv] = (60, 100, 210)
                return col, em, np.ones(P.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zc)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec(groupe, f"{pre}paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


def controle_gouttieres():
    """Marges (px) : gouttière de la lame / bord du plat, gouttière du col / bord du plat du col (doivent rester > 0)."""
    pts = np.array([p for c in GT_L.cotes.values() for p in c])
    m_l = float((LAME_P.dE(pts) - LAME_P.wb(pts)).min())
    m_c = 1e9
    for p in [p for c in GT_C.cotes.values() for p in c]:
        D = np.linalg.norm(_DENSE - np.array(p), axis=1)
        j = D.argmin()
        s = _DENSE_S[j]
        m_c = min(m_c, (col_m(s) - col_zh(s)) - 0.06 - D[j])
    return m_l, m_c


def conception():
    SPECS.clear()
    TILES.clear()
    CUR_FR[0] = "img"
    octa("fer", "col", COL_SEGS, col_Y, col_dims, gout=GT_C)
    gouttiere(GT_C, "fer", surf_col, "col_")
    for pc in ATTELLES:
        volume(pc, "manche")
    CUR_FR[0] = "lame"
    volume(LAME_P, "lame")
    gouttiere(GT_L, "lame", LAME_P.surf, "lame_")
    octa("lame", "nervure", RIB_SEGS, lambda i: (0.0, 1.0, 0.0), rib_dims, bout_ferme=True)
    CUR_FR[0] = "img"


def disque16(N, R_apo, ss=4, peindre=None):
    """Tuile d'une face de prisme à 16 pans (apothème R_apo, tuile de côté 2 R_apo / cos(11,25°))."""
    Rc = R_apo / math.cos(math.pi / 16)
    M = N * ss
    yy, xx = np.mgrid[0:M, 0:M]
    X = ((xx + 0.5) / M * 2 - 1) * Rc
    Y = (1 - (yy + 0.5) / M * 2) * Rc
    th = np.arctan2(Y, X)
    r = np.hypot(X, Y)
    sect = np.mod(th, TAU / 16) - TAU / 32
    apo = r * np.cos(sect)
    col = peindre(np.stack([X, Y], -1), r, apo)
    m = apo <= R_apo
    a = np.zeros((M, M, 4), np.float32)
    a[..., :3] = col
    a[..., 3] = m * 255
    im = np.array(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").resize((N, N), Image.BOX))
    im[..., 3] = (im[..., 3] > 128) * 255
    im[im[..., 3] == 0] = 0
    return im


def t_collet():
    def p(P, r, apo):
        nz = cellules(P + 30, 2.0, 8.0)[..., None]
        col = lerp(METAL[2], METAL[1], 0.4) + nz * 16 + np.zeros(P.shape[:-1] + (3,), np.float32)
        col[apo > R_COL - 0.14] = METAL[4]
        col[(apo > R_COL - 0.22) & (apo <= R_COL - 0.14)] = METAL[0]
        orl = (r > 1.13) & (r < 1.22)
        col[orl] = OR[2]
        return col
    return disque16(48, R_COL, peindre=p)


R_BAGUE = 1.12


def t_bague():
    def p(P, r, apo):
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + OR[2] + cellules(P + 11, 3.0, 9.0)[..., None] * 14
        col[apo > R_BAGUE - 0.12] = OR[3]
        col[(apo > R_BAGUE - 0.2) & (apo <= R_BAGUE - 0.12)] = OR[0]
        col[r < 0.7] = OR[1]
        return col
    return disque16(40, R_BAGUE, peindre=p)



def medaillon(N=64, ss=4):
    """Tambour d'or : anneau d'or, fond de métal sombre, trois virgules d'or en spirale."""
    M = N * ss
    im = Image.new("RGBA", (M, M), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, M - 1, M - 1), fill=tuple(int(v) for v in OR[1]) + (255,))
    d.ellipse((M * 0.07, M * 0.07, M * 0.93, M * 0.93), fill=tuple(int(v) for v in OR[3]) + (255,))
    d.ellipse((M * 0.13, M * 0.13, M * 0.87, M * 0.87), fill=tuple(int(v) for v in METAL[1]) + (255,))
    c = M / 2
    for k in range(3):
        th = TAU * k / 3 + 0.4
        hx, hy = c + 0.17 * M * math.cos(th), c + 0.17 * M * math.sin(th)
        r = 0.115 * M
        for j in range(26):
            u = j / 25
            a = th + u * 1.9
            rr = 0.17 * M + u * 0.11 * M
            w = r * (1 - u) ** 1.2
            x, y = c + rr * math.cos(a), c + rr * math.sin(a)
            d.ellipse((x - w, y - w, x + w, y + w), fill=tuple(int(v) for v in OR[2]) + (255,))
        d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=tuple(int(v) for v in OR[3]) + (255,))
    im = im.resize((N, N), Image.LANCZOS)
    a = np.array(im)
    a[..., 3] = (a[..., 3] > 128) * 255
    a[a[..., 3] == 0] = 0
    return a


def t_unie(W, H, c0, c1, seed=1, bords=None):
    rng = np.random.default_rng(seed)
    a = np.zeros((H, W, 4), np.uint8)
    v = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
    col = lerp(np.array(c0, np.float32), np.array(c1, np.float32), v[..., None]) + rng.normal(0, 4, (H, W, 1))
    if bords is not None:
        col[0] = col[-1] = bords
    a[..., :3] = np.clip(col, 0, 255)
    a[..., 3] = 255
    return a


def t_cuir(W=96, H=16):
    a = np.zeros((H, W, 4), np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    ph = ((xx + yy * 1.4) % 12) / 12
    col = np.where((ph < 0.16)[..., None], CUIR[0], lerp(CUIR[2], CUIR[1], ph[..., None]))
    col = col + np.where((ph > 0.55) & (ph < 0.62), 1, 0)[..., None] * (OR[1] - col) * 0.6
    a[..., :3] = np.clip(col, 0, 255)
    a[..., 3] = 255
    return a


def t_core():
    a = np.zeros((6, 16, 4), np.uint8)
    a[..., :3] = (236, 244, 255)
    a[0, :, :3] = a[5, :, :3] = (96, 146, 255)
    a[..., 3] = 255
    e = a.copy()
    e[..., :3] = (205, 226, 255)
    e[0, :, :3] = e[5, :, :3] = (50, 84, 210)
    return a, e


def t_halo():
    a = np.zeros((8, 16, 4), np.uint8)
    for v in range(8):
        d = abs((v + 0.5) / 8 * 2 - 1)
        k = (1 - d) ** 1.4
        a[v, :, :3] = np.array((8, 7, 30)) + k * np.array((26, 44, 120))
    a[..., 3] = 255
    return a


def t_crk():
    a = np.zeros((4, 16, 4), np.uint8)
    a[..., :3] = (225, 236, 255)
    a[0, :, :3] = a[3, :, :3] = (120, 150, 255)
    a[..., 3] = 255
    return a


def t_cristal():
    a = t_unie(16, 8, CRIS[4], CRIS[1], 4, bords=CRIS[0])
    e = a.copy()
    e[..., :3] = np.clip(a[..., :3].astype(np.float32) * 0.75, 0, 225).astype(np.uint8)
    return a, e


def t_poli():
    a = t_unie(16, 8, (240, 246, 255), (196, 210, 238), 7, bords=(150, 170, 220))
    e = a.copy()
    e[..., :3] = (90, 130, 225)
    return a, e


# ------------------------------------------------------------------ atlas
UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    core, core_e = t_core()
    cri, cri_e = t_cristal()
    conception()
    items = [(n, im, ime) for n, (im, ime) in TILES.items()]
    items += [("medaillon", medaillon(), None), ("collet", t_collet(), None), ("bague", t_bague(), None), ("cuir", t_cuir(), None),
              ("core", core, core_e), ("cristal", cri, cri_e), ("halo", t_halo(), None), ("crk", t_crk(), None),
              ("metal", t_unie(64, 12, METAL[3], METAL[1], 2, bords=METAL[4]), None),
              ("hampe", t_unie(64, 12, METAL[2], METAL[0], 6, bords=METAL[3]), None),
              ("sombre", t_unie(32, 8, METAL[2], METAL[1], 3), None),
              ("or", t_unie(16, 8, OR[3], OR[1], 5, bords=OR[0]), None)]
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, im, ime in sorted(items, key=lambda it: -it[1].shape[0]):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, "atlas plein"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None:
            tex_e[y:y + h, x:x + w] = ime
        x += w + 1
        shelf = max(shelf, h)
    assert tex[TEX - 2, TEX - 2, 3] == 0
    assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
    m_l, m_c = controle_gouttieres()
    print(f"atlas : {len(items)} tuiles, hauteur utilisée {y + shelf}/{TEX} ; marges gouttière/plat : lame {m_l:.3f} px, col {m_c:.3f} px")
    res = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        res.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return res


tex_b64, tex_e_b64 = atlas()


# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


def euler(R):
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def rmat(rx, ry, rz):
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx




class Repere:
    """Repère plan -> monde : origine O, axes e1, e2 (monde), épaisseur selon e3 = e1 × e2."""

    def __init__(self, O, e1, e2):
        self.O, self.e1, self.e2 = np.asarray(O, float), unit(np.asarray(e1, float)), unit(np.asarray(e2, float))
        self.e3 = np.cross(self.e1, self.e2)

    def p(self, x, y, z=0.0):
        return self.O + x * self.e1 + y * self.e2 + z * self.e3

    def v(self, x, y, z=0.0):
        return x * self.e1 + y * self.e2 + z * self.e3


FR = [None]                         # repère courant : celui de l'image (col, manche) ou celui de la lame


def W_(x, y, z=0.0):
    return FR[0].p(x, y, z)


def Wv(x, y, z=0.0):
    return FR[0].v(x, y, z)


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups, name
    assert len(name.split("#")[0]) <= 64
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [float(v) for v in rotation]}
    return name


def ctrl(parent):
    return group(f"ctrl_alpha#{len(groups)}", groups[parent]["origin"], parent=parent)


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in frm], "to": [round(float(v), 4) for v in to],
         "origin": [round(float(v), 4) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def boite(g, name, c, X, Y, sx, sy, sz, faces):
    """Boîte centrée en c (monde), axes X, Y (monde), tailles sx, sy, sz."""
    X = unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    cube(g, name, c - (sx / 2, sy / 2, sz / 2), c + (sx / 2, sy / 2, sz / 2), c, euler(R_), faces)



def strip(tile, caps=True):
    u0, v0, u1, v1 = UV[tile]
    lg = [u0, v0, u1, v1]
    end = [u0 + 1, v0 + 1, u0 + 3, v0 + 3] if caps else CLEAR
    return {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end}


def barre(g, name, a0, a1, r, tile, b=0.0, octo=True, caps=True):
    """Barre le long du manche (axe a), section r ; octogonale (deux cubes à 45°)."""
    Ln = a1 - a0
    c = W_((a0 + a1) / 2, b)
    X, Y = Wv(1, 0), Wv(0, 1)
    boite(g, name, c, X, Y, Ln, 2 * r, 2 * r, strip(tile, caps))
    if octo:
        Yq = unit(Y * math.cos(math.pi / 4) + V(0, 0, 1) * math.sin(math.pi / 4))
        boite(g, name + "o", c, X, Yq, Ln - 0.1, 2 * r * 0.97, 2 * r * 0.97, strip(tile, caps))


def seg(g, name, p, q, w, tile, ov=0.06, roll=45.0):
    """Tronçon de trait (monde) de p à q, section w × w tournée de roll autour de l'axe."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = Wv(0, 0, 1)
    if abs(ref @ X) > 0.9:
        ref = Wv(1, 0, 0)
    Y0 = unit(ref - (ref @ X) * X)
    Z0 = np.cross(X, Y0)
    r = math.radians(roll)
    Y = Y0 * math.cos(r) + Z0 * math.sin(r)
    Ln = float(np.linalg.norm(q - p))
    boite(g, name, (p + q) / 2, X, Y, Ln + 2 * ov, w, w, strip(tile, caps=tile != "halo"))


ROLLS = [45, 18, 62, 33, 51, 9, 74, 27]
_rc = [0]


def trait(g, name, pts, w0, w1, tile):
    n = len(pts) - 1
    for i in range(n):
        w = w0 + (w1 - w0) * i / max(1, n - 1)
        roll = ROLLS[_rc[0] % len(ROLLS)]
        _rc[0] += 1
        seg(g, f"{name}{i}", pts[i], pts[i + 1], w, tile, roll=roll)



def zigzag(pts, n, J, seed, zj=0.0, z0=0.0):
    """Éclair qui suit une polyligne (plan a, b) : n tronçons irréguliers, écarts latéraux alternés ; renvoie des points (a, b, z)."""
    rng = random.Random(seed)
    P = [np.array(p, float) for p in pts]
    ls = np.cumsum([0] + [np.linalg.norm(P[i + 1] - P[i]) for i in range(len(P) - 1)])
    tot = ls[-1]

    def at(x):
        i = min(np.searchsorted(ls, x, side="right") - 1, len(P) - 2)
        k = (x - ls[i]) / max(ls[i + 1] - ls[i], 1e-9)
        return P[i] + (P[i + 1] - P[i]) * k, unit(P[i + 1] - P[i])

    out = []
    sg = rng.choice((-1, 1))
    for i in range(n + 1):
        x = tot * min(1, max(0, (i + (rng.uniform(-0.25, 0.25) if 0 < i < n else 0)) / n))
        p, d = at(x)
        nr = np.array((-d[1], d[0]))
        off = 0 if i in (0, n) else sg * rng.uniform(0.5, 1.0) * J
        sg = -sg
        q = p + nr * off
        out.append((q[0], q[1], z0 + (rng.uniform(-zj, zj) if 0 < i < n else 0)))
    return out


def le_long(pts):
    P = [np.array(p, float) for p in pts]
    ls = np.cumsum([0] + [np.linalg.norm(P[i + 1] - P[i]) for i in range(len(P) - 1)])

    def at(t):
        x = t * ls[-1]
        i = min(np.searchsorted(ls, x, side="right") - 1, len(P) - 2)
        return P[i] + (P[i + 1] - P[i]) * (x - ls[i]) / max(ls[i + 1] - ls[i], 1e-9)
    return at


def bone_node(name):
    g = groups[name]
    return {"name": name.split("#")[0], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


def sous_groupes(g):
    out = [g]
    for n, gg in groups.items():
        if gg["parent"] == g:
            out += sous_groupes(n)
    return out


def replier(g):
    """Replie toute la géométrie du groupe à FOLD autour de son pivot (dépliée par scale 1/FOLD dans les animations)."""
    o = np.array(groups[g]["origin"])
    ids = {i for n in sous_groupes(g) for i in groups[n]["ids"]}
    for e in elements:
        if e["uuid"] in ids:
            for k in ("from", "to", "origin"):
                e[k] = [round(float(o[i] + FOLD * (e[k][i] - o[i])), 4) for i in range(3)]




def exterieur(pts, dist, masque):
    """Polyligne décalée de dist vers l'extérieur de la forme."""
    out = []
    P = [np.array(p, float) for p in pts]
    for i, p in enumerate(P):
        d = unit(P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)])
        n = np.array((-d[1], d[0]))
        if masque(np.array([p + n * 0.08]))[0]:
            n = -n
        out.append(tuple(p + n * dist))
    return out


N_FIL = 6
NG = 3


def eclair_branche(g, nom, p0, d, Ln, seed, w0=0.26, w1=0.14, branches=1, J=0.22):
    """Éclair ramifié (plan a, b) depuis p0 dans la direction d : tronc + `branches` fourches."""
    rng = random.Random(seed)
    p0 = np.array(p0, float)
    q = p0 + d * Ln
    zz = zigzag([tuple(p0), tuple(q)], 5, J, seed, zj=0.12)
    trait(g, f"{nom}t", [W_(*p) for p in zz], w0, w1, "crk")
    for j in range(branches):
        i = 2 + j
        b0 = np.array(zz[i][:2])
        sg = 1 if (seed + j) % 2 == 0 else -1
        an = math.radians(rng.uniform(30, 50)) * sg
        bd = np.array((d[0] * math.cos(an) - d[1] * math.sin(an), d[0] * math.sin(an) + d[1] * math.cos(an)))
        bz = zigzag([tuple(b0), tuple(b0 + bd * Ln * rng.uniform(0.35, 0.5))], 3, J * 0.6, seed * 3 + j, z0=zz[i][2])
        trait(g, f"{nom}b{j}", [W_(*p) for p in bz], w1 * 0.95, w1 * 0.7, "crk")


def tourner(d, deg):
    a = math.radians(deg)
    return np.array((d[0] * math.cos(a) - d[1] * math.sin(a), d[0] * math.sin(a) + d[1] * math.cos(a)))


def poser_specs(cibles, fr):
    """Pose les cubes du volume (SPECS) du repère `fr` dans les groupes `cibles` (nom de spec -> groupe), repère courant FR."""
    for sp in SPECS:
        if sp["fr"] != fr:
            continue
        u_ = {}
        for f in ("north", "south", "east", "west", "up", "down"):
            if f in sp["faces"]:
                u0, v0, u1, v1 = UV[sp["faces"][f]]
                u_[f] = [u0, v0, u1, v1]
            else:
                u_[f] = CLEAR
        boite(cibles[sp["groupe"]], sp["nom"], W_(*sp["c"]), Wv(*sp["X"]), Wv(*sp["Y"]), *sp["s"], u_)


def prisme16(g, nom, R, zh, tile_cote, tile_face, C=(0.0, 0.0)):
    """Prisme à 16 pans d'axe e3 du repère courant : 16 parois de TH (côtés `tile_cote`), deux faces découpées par l'alpha."""
    C = np.asarray(C, float)
    cote = 2 * R * math.tan(math.pi / 16)
    for k in range(16):
        th = TAU * k / 16
        nrm = np.array((math.cos(th), math.sin(th)))
        tg = np.array((-nrm[1], nrm[0]))
        c = C + nrm * (R - TH / 2)
        u0, v0, u1, v1 = UV[tile_cote]
        boite(g, f"{nom}{k}", W_(c[0], c[1]), Wv(*tg), Wv(0, 0, 1), cote + 0.03, 2 * zh, TH,
              {"south": [u0, v0, u1, v1], "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
    u0, v0, u1, v1 = UV[tile_face]
    Rc = R / math.cos(math.pi / 16)
    for sg in (1, -1):
        fc = {"south": [u0, v0, u1, v1]} if sg > 0 else {"north": [u1, v0, u0, v1]}
        boite(g, f"{nom}_face{'pm'[sg < 0]}", W_(C[0], C[1], sg * (zh - TH / 2)), Wv(1, 0), Wv(0, 1), 2 * Rc, 2 * Rc, TH,
              {**{f: CLEAR for f in ("north", "south", "east", "west", "up", "down")}, **fc})


def gaine(parent, k, pts, w):
    gg = group(f"add_gaine_{k}", tuple(pts[0]), parent)
    ctrl(gg)
    for i in range(len(pts) - 1):
        seg(gg, f"gaine{k}_{i}", pts[i], pts[i + 1], w, "halo", ov=0.04, roll=0.0)
    return gg


def foudre_couchee(g, nom, pts2, w0, w1):
    """Trait de foudre couché sur le fond de la gouttière, de chaque côté (cœur opaque blanc + _e)."""
    for zs in (1, -1):
        pts = [W_(a, b, zs * 0.17) for a, b in pts2]
        for i in range(len(pts) - 1):
            seg(g, f"{nom}{'pm'[zs < 0]}{i}", pts[i], pts[i + 1], w0 + (w1 - w0) * i / max(1, len(pts) - 2), "core", roll=0.0)


def decharge(parent, nom, seed, angs, lf, out):
    g = group(f"add_pointe_{nom}", W_(*TIP_IN), parent)
    ctrl(g)
    rng = random.Random(seed)
    for j, an in enumerate(angs):
        q = np.array(TIP) + tourner(TIP_D, an) * rng.uniform(1.0, 1.6) * lf
        zz = zigzag([TIP, tuple(q)], 3, 0.2, seed * 10 + j)
        trait(g, f"p{j}", [W_(*p) for p in zz], 0.24, 0.14, "crk")
    replier(g)
    out[nom] = g


def build(theta, P0):
    elements.clear()
    groups.clear()
    _rc[0] = 0
    c, s_ = math.cos(theta), math.sin(theta)
    IMG = Repere(P0, V(c, s_, 0), V(-s_, c, 0))
    FR[0] = IMG
    out = {}
    racine = group(objet.etape("repos", "houe"), W_(A_O, 0))
    houe = group("houe", W_(4.5, 0), racine)                       # pivot dans la main : le geste de labour
    # --- manche : pommeau à pointe de cristal, poignée de cuir entre bagues d'or, hampe d'acier, attelles biseautées rivetées ;
    #     au-dessus de l'œil, coin d'or et pointe-paratonnerre de cristal à facettes
    manche = group("manche", W_(4.0, 0), houe)
    barre(manche, "pommeau", -0.2, 1.1, 0.86, "metal")
    barre(manche, "pom_bague", 0.22, 0.58, 0.94, "or")
    barre(manche, "pom_cri", -1.05, -0.15, 0.44, "cristal")
    barre(manche, "pom_cri2", -1.55, -1.0, 0.23, "cristal", octo=False)
    barre(manche, "bague1", 1.05, 1.5, 0.74, "or")
    barre(manche, "poignee", 1.45, 7.3, 0.64, "cuir")
    barre(manche, "bague2", 7.25, 7.65, 0.72, "or")
    barre(manche, "hampe", 7.6, A_O + 1.0, Z_HAMPE + 0.02, "hampe")
    barre(manche, "coin", A_O + 1.2, A_O + 1.75, 0.62, "or")
    for j, (a0, a1, r) in enumerate(((A_O + 1.7, A_O + 2.3, 0.4), (A_O + 2.25, A_O + 2.6, 0.3), (A_O + 2.55, A_O + 2.8, 0.2),
                                     (A_O + 2.75, A_TOP, 0.1))):
        barre(manche, f"pointe_cri{j}", a0, a1, r, "cristal")
    for zs in (1, -1):
        for j, a in enumerate((A_O - 4.5, A_O - 3.3, A_O - 2.1)):
            for r_ in (0.0, 45.0):
                rr = math.radians(r_)
                boite(manche, f"rivet{'pm'[zs < 0]}{j}{int(r_)}", W_(a, 0, zs * (Z_HAMPE + 0.25)), Wv(math.cos(rr), math.sin(rr)),
                      Wv(-math.sin(rr), math.cos(rr)), 0.3, 0.3, 0.16, strip("or"))
    # --- col de cygne en vrai volume (octogone qui s'affine, gouttière de foudre), œil = collet à 16 pans + tambour d'or
    fer = group("fer", W_(A_O, 0), houe)
    poser_specs({"fer": fer, "manche": manche}, "img")
    prisme16(fer, "collet", R_COL, 0.84, "metal", "collet", C=O_)
    prisme16(fer, "tambour", 1.08, 1.06, "or", "medaillon", C=O_)
    foudre = group("foudre", W_(*SLIT_C[0]), fer)
    foudre_couchee(foudre, "eclair_c", SLIT_C, 0.32, 0.26)
    out["gaines"] = [gaine(foudre, 0, [W_(a, b) for a, b in SLIT_C], 0.8)]
    # foudre qui tombe sur la pointe-paratonnerre (event_select) : venue d'en haut, deux formes ; pivot caché dans le tambour
    out["ciel"] = []
    TOPC = np.array((A_TOP, 0.0))
    for nm, seed, off in (("a", 61, 0.0), ("b", 67, 0.9)):
        g = group(f"add_ciel_{nm}", W_(A_O + 0.35, 0), fer)
        ctrl(g)
        haut = TOPC + unit(np.array((0.62, 0.78))) * 5.4 + np.array((off * 0.5, -off))
        zz = zigzag([tuple(haut), tuple(TOPC)], 6, 0.45, seed, zj=0.15)
        trait(g, "c", [W_(*p) for p in zz], 0.2, 0.3, "crk")
        b0 = np.array(zz[2][:2])
        bz = zigzag([tuple(b0), tuple(b0 + tourner(unit(TOPC - haut), 38 if nm == "a" else -38) * 1.6)], 3, 0.25, seed + 1)
        trait(g, "cb", [W_(*p) for p in bz], 0.16, 0.12, "crk")
        replier(g)
        out["ciel"].append(g)

    # --- lame : son propre repère (u de la racine vers le fil, w en travers, épaisseur selon e3), tourné de ROLL autour de u
    e1 = IMG.v(*D_L)
    e2 = math.cos(ROLL) * V(0, 0, 1) + math.sin(ROLL) * IMG.v(*N_L)
    LAME_FR = Repere(IMG.p(*R_L), e1, e2)
    FR[0] = LAME_FR
    lame = group("lame", W_(0, 0), fer)
    poser_specs({"lame": lame}, "lame")
    # bague d'or à la jonction du col et de la lame (axe = celui de la lame)
    FR[0] = Repere(LAME_FR.p(-0.05, 0), LAME_FR.e2, LAME_FR.e3)
    prisme16(lame, "bague", R_BAGUE, 0.27, "or", "bague")
    FR[0] = LAME_FR
    foudre_l = group("foudre_lame", W_(*SLIT_L[0]), lame)
    foudre_couchee(foudre_l, "eclair_l", SLIT_L, 0.3, 0.24)
    pts_l = [W_(a, b) for a, b in SLIT_L]
    out["gaines"] += [gaine(foudre_l, 1, pts_l[:4], min(0.8, 2 * float(LAME_P.h(np.array(SLIT_L[3]))) - 0.14)),
                      gaine(foudre_l, 2, pts_l[3:], 2 * float(LAME_P.h(np.array(SLIT_L[-1]))) - 0.14)]
    # fourches de la fente sur le plat (faces avant et arrière) — états seulement
    out["fourches"] = []
    on_slit = le_long(SLIT_L)
    for v in range(2):
        fg = group(f"add_fourche_{'ab'[v]}", W_(*SLIT_L[0]), foudre_l)
        ctrl(fg)
        rng = random.Random(40 + v)
        for k in range(3):
            t = (k + 0.25 + 0.5 * rng.random()) / 3
            p = on_slit(t)
            d = unit(on_slit(min(1, t + 0.02)) - p)
            side = 1 if (k + v) % 2 == 0 else -1
            dirn = tourner(d, rng.uniform(40, 65) * side)
            q = p + dirn * rng.uniform(0.6, 0.9)
            for zs in (1, -1):
                zz = zigzag([p + dirn * (SLIT_W + 0.12), q], 3, 0.1, 70 + 10 * v + k)
                trait(fg, f"f{k}{'pm'[zs < 0]}", [W_(x, y, zs * (float(LAME_P.surf(np.array([(x, y)]))[0]) + 0.07)) for x, y, _ in zz],
                      0.16, 0.12, "crk")
        replier(fg)
        out["fourches"].append(fg)
    # --- arcs des deux flancs : du fil vers la racine (event_hit) ; pivots cachés dans le métal (0,6 px en dedans du flanc)
    arcs = group("arcs_flancs", W_(*TIP_IN), lame)
    out["fil"], out["rang"] = [], []
    for sg, bd in ((1, EXT_P), (-1, EXT_M)):
        at = le_long(exterieur(bd, 0.17, m_lame))
        at_in = le_long(exterieur(bd, -0.6, m_lame))
        for k in range(N_FIL // 2):
            t0, t1 = k / (N_FIL // 2), (k + 1) / (N_FIL // 2)
            sous = [tuple(at(t)) for t in np.linspace(t0, t1, 4)]
            g = group(f"add_flanc_{'pm'[sg < 0]}{k}", W_(*at_in((t0 + t1) / 2)), arcs)
            ctrl(g)
            zz = zigzag(sous, 4, 0.14, 100 + 7 * k + (50 if sg < 0 else 0), zj=0.08)
            trait(g, "a", [W_(*p) for p in zz], 0.23, 0.19, "crk")
            replier(g)
            out["fil"].append(g)
            out["rang"].append(k)                                # 0 = racine, N_FIL/2 - 1 = fil
    # --- décharges du fil : a (event_hit), r (états), s (event_select)
    out["pointe"] = {}
    decharge(arcs, "a", 5, (-40, 2, 38), 1.0, out["pointe"])
    decharge(arcs, "r", 13, (-26, 20), 0.7, out["pointe"])
    decharge(arcs, "s", 31, (-48, -8, 30), 0.85, out["pointe"])
    # --- le fil décharge dans la terre (event_break) : éclairs ramifiés en éventail sur la largeur de la lame, deux formes
    out["roche"] = []
    for nm, seed, angs in (("a", 21, (-34, 4, 37)), ("b", 29, (-18, 24, 52))):
        g = group(f"add_terre_{nm}", W_(*TIP_IN), arcs)
        ctrl(g)
        rng = random.Random(seed)
        for j, an in enumerate(angs):
            eclair_branche(g, f"r{j}", TIP, tourner(TIP_D, an), rng.uniform(3.2, 4.2), seed + 5 * j, branches=1 if j != 1 else 2)
        replier(g)
        out["roche"].append(g)
    dw = Wv(*TIP_D)
    rot_emit = (0, 0, round(math.degrees(math.atan2(-dw[0], dw[1])), 2))
    em = group("emit_mc_electric_spark", W_(*TIP), lame, rotation=rot_emit)
    group("ctrl_emit", W_(*TIP), em)
    out["emit"] = em
    FR[0] = IMG
    out["racine"], out["houe"] = racine, houe
    for e in elements:
        for k in ("from", "to", "origin"):
            e[k] = [round(float(P0[i] + K * (e[k][i] - P0[i])), 4) for i in range(3)]
    for gg in groups.values():
        gg["origin"] = [round(float(P0[i] + K * (gg["origin"][i] - P0[i])), 4) for i in range(3)]
    return out



def coins():
    P = []
    for e in elements:
        f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
        R = rmat(*e.get("rotation", (0, 0, 0)))
        for i in range(8):
            c = np.array([(f, t)[(i >> k) & 1][k] for k in range(3)])
            P.append(R @ (c - o) + o)
    return np.array(P)




K = float(os.environ.get("K", "1.0"))
THETA = math.radians(45)          # le long de la diagonale du bloc, tête en haut à droite (vue de +Z), comme iron_hoe.png
build(THETA, V(0, 0, 0))
P = coins()
CENTRE = (P.min(axis=0) + P.max(axis=0)) / 2
F = build(THETA, V(8, 8, 8) - CENTRE)
P = coins()
D_ = np.array((1, 1, 0)) / math.sqrt(2)
LONGUEUR = float((P @ D_).max() - (P @ D_).min())
LARGEUR = float((P @ np.array((-1, 1, 0)) / math.sqrt(2)).max() - (P @ np.array((-1, 1, 0)) / math.sqrt(2)).min())
outliner = [bone_node(F["racine"])]


# ------------------------------------------------------------------ animations (objet vivant, guide 14)
def s(v):
    return v if isinstance(v, str) else f"{v + 0.0:.4f}".rstrip("0").rstrip(".")


def kf(ch, t, x, y=0, z=0, interp="linear"):
    return {"channel": ch, "data_points": [{"x": s(x), "y": s(y), "z": s(z)}], "time": round(t, 4), "interpolation": interp}


def anim(name, length, loop="loop"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 100,
            "selected": name == "item_idle", "animators": {}}


def ctrl_de(g):
    return next((n, gg) for n, gg in groups.items() if gg["parent"] == g and n.startswith("ctrl_alpha"))


def piste_ctrl(an, g, keys):
    n, gg = ctrl_de(g)
    an["animators"][gg["uuid"]] = {"name": "ctrl_alpha", "type": "bone", "keyframes": keys}


def piste(an, g, keys):
    an["animators"][groups[g]["uuid"]] = {"name": g.split("#")[0], "type": "bone", "keyframes": keys}


DEPLIE = 1 / FOLD


def deplier(an, g):
    piste(an, g, [kf("scale", 0.0, DEPLIE, DEPLIE, DEPLIE, "step")])


def chk(e):
    assert len(e) <= 512, (len(e), e)
    return e


def H(x):
    return f"math.mod(math.abs(math.sin(({x})*127.1))*437.585,1)"


def restrike(P, pr, c2):
    """v.r = 1 pendant trois arcs en retour (60 ms, séparés de 60 ms) d'une tranche de P s tirée avec la probabilité pr."""
    return (f"v.u=q.life_time/{P:g}+{c2:.3g};v.s={H('math.floor(v.u)')};v.u=math.mod(v.u,1)*{P:g};"
            f"v.r=(v.s<{pr:g})*((v.u<0.07)+(v.u>0.13)*(v.u<0.19)+(v.u>0.26)*(v.u<0.32));")


def flick(R, c):
    return f"v.h={H(f'math.floor(q.life_time*{R:g}+{c:.3g})')};"


P_RS, PR_RS = 5.5, 0.6            # un arc en retour toutes les ~3 à 8 s


def gaine_idle(k):
    return chk(restrike(P_RS, PR_RS, 0.37) + flick(9, 0.13 + 0.31 * k) + "-0.38+0.22*(v.h<0.3)-0.25*(v.h>0.82)+0.7*v.r")


def fourche_idle(v):
    cond = "(v.h<0.1)" if v == 0 else "(v.h>0.9)"
    return chk(restrike(P_RS, PR_RS, 0.37) + flick(6, 0.29 + 1.7 * v) + f"math.max({cond},v.r)-1")


def onoff(intervalles, Ln, on=1.0, off=-1.0, r=0.012):
    """Clés ctrl_alpha : off, puis on pendant chaque intervalle (a, b) ; rampes de r s."""
    ks = [kf("position", 0.0, off)]
    for a, b in intervalles:
        ks += [kf("position", max(0.0, a - r), off), kf("position", a, on), kf("position", b, on), kf("position", b + r, off)]
    ks.append(kf("position", Ln, off))
    ks.sort(key=lambda k: k["time"])
    dedup = []
    for k in ks:
        if dedup and abs(dedup[-1]["time"] - k["time"]) < 1e-4:
            dedup[-1] = k
        else:
            dedup.append(k)
    return dedup




FILS = F["fil"]
GAINES = F["gaines"]
PA, PR, PS = F["pointe"]["a"], F["pointe"]["r"], F["pointe"]["s"]
CIEL = F["ciel"]
ROCHE = F["roche"]
TOUS = FILS + [PA, PR, PS] + CIEL + ROCHE + F["fourches"]


def eteindre(an, sauf=()):
    for g in TOUS:
        if g not in sauf:
            piste_ctrl(an, g, [kf("position", 0, -1)])


def emit(an, keys):
    gg = next(gg for n, gg in groups.items() if gg["parent"] == F["emit"] and n.startswith("ctrl_emit"))
    an["animators"][gg["uuid"]] = {"name": "ctrl_emit", "type": "bone", "keyframes": keys}


# item_idle : les fentes vivent (gaine qui vacille, fourches), petite décharge du fil aux arcs en retour ; le reste éteint.
idle = anim("item_idle", 8.0)
for k, g in enumerate(GAINES):
    piste_ctrl(idle, g, [kf("position", 0, gaine_idle(k))])
for v, fg in enumerate(F["fourches"]):
    deplier(idle, fg)
    piste_ctrl(idle, fg, [kf("position", 0, fourche_idle(v))])
deplier(idle, PR)
piste_ctrl(idle, PR, [kf("position", 0, chk(restrike(P_RS, PR_RS, 0.37) + "v.r-1"))])
eteindre(idle, sauf=F["fourches"] + [PR])
emit(idle, [kf("position", 0, -1)])

# item_swing (boucle 0,3 s) : à chaque coup la fente s'avive et le fil claque.
L_MIN = 0.3
mine = anim("item_swing", L_MIN)
T_IMP = 0.14
for k, g in enumerate(GAINES):
    t0 = T_IMP - 0.03 + 0.012 * k
    piste_ctrl(mine, g, [kf("position", t, -0.3 + 0.95 * bump(t, t0, t0 + 0.02, t0 + 0.05, t0 + 0.13)) for t in np.round(np.linspace(0, L_MIN, 16), 4)])
deplier(mine, PR)
piste_ctrl(mine, PR, onoff([(T_IMP, T_IMP + 0.05)], L_MIN))
eteindre(mine, sauf=[PR])
emit(mine, [kf("position", 0, -1)])

# item_gui : inventaire calme.
gui = anim("item_gui", 4.0)
for g in GAINES:
    piste_ctrl(gui, g, [kf("position", 0, -0.3)])
eteindre(gui)
emit(gui, [kf("position", 0, -1)])

# event_select (0,7 s) : un éclair frappe la pointe-paratonnerre (deux formes), court du col vers la lame, le fil décharge.
L_SEL = 0.7
sel = anim("event_select", L_SEL, "once")
for g in CIEL:
    deplier(sel, g)
piste_ctrl(sel, CIEL[0], onoff([(0.0, 0.07), (0.15, 0.19)], L_SEL))
piste_ctrl(sel, CIEL[1], onoff([(0.08, 0.13)], L_SEL))
for k, g in enumerate(GAINES):
    t0 = 0.08 + 0.06 * k
    piste_ctrl(sel, g, [kf("position", t, -0.6 * (1 - sm(t, 0.0, 0.1)) * (t < t0) + (1.0 * bump(t, t0, t0 + 0.04, t0 + 0.12, t0 + 0.4)
                                                                                     - 0.38 * sm(t, t0 + 0.12, t0 + 0.4)) * (t >= t0))
                         for t in np.round(np.linspace(0, L_SEL, 29), 4)])
deplier(sel, PS)
piste_ctrl(sel, PS, onoff([(0.22, 0.29), (0.34, 0.37)], L_SEL))

# event_swing (0,35 s) : le geste de labour — la lame pique vers le sol (3°) et revient ; vague dans la fente (ne déplie rien).
L_SW = 0.35
sw = anim("event_swing", L_SW, "once")
for k, g in enumerate(GAINES):
    t0 = 0.025 * k
    piste_ctrl(sw, g, [kf("position", t, 0.6 * bump(t, t0, t0 + 0.04, t0 + 0.1, t0 + 0.3)) for t in np.round(np.linspace(0, L_SW, 15), 4)])
piste(sw, F["houe"], [kf("rotation", t, 0, 0, 3.0 * sm(t, 0.0, 0.08) * (1 - sm(t, 0.1, 0.32))) for t in np.round(np.linspace(0, L_SW, 15), 4)])

# event_hit (0,7 s) : décharge du fil, les arcs remontent les deux flancs de la lame jusqu'à la racine, trois arcs en retour.
L_HIT = 0.7
hit = anim("event_hit", L_HIT, "once")
RESTRIKES = [(0.22, 0.27), (0.32, 0.36), (0.42, 0.45)]
NB = N_FIL // 2
deplier(hit, PA)
piste_ctrl(hit, PA, onoff([(0.0, 0.09), RESTRIKES[0], RESTRIKES[2]], L_HIT))
for g, k in zip(FILS, F["rang"]):
    deplier(hit, g)
    t0 = 0.04 + 0.035 * (NB - 1 - k)                        # du fil (dernier tronçon) vers la racine
    iv = [(t0, t0 + 0.09)]
    for j, (a, b) in enumerate(RESTRIKES):
        if j == 0 or (j == 1 and k % 2 == 1) or (j == 2 and k == NB - 1):
            iv.append((a, b))
    piste_ctrl(hit, g, onoff(iv, L_HIT))
for k, g in enumerate(GAINES):
    piste_ctrl(hit, g, [kf("position", t, 1.2 * sm(t, 0.0, 0.02) * (1 - sm(t, 0.08, 0.6))
                         + 0.4 * sum(bump(t, a - 0.01, a, b, b + 0.02) for a, b in RESTRIKES)) for t in np.round(np.linspace(0, L_HIT, 36), 4)])
piste(hit, F["houe"], [kf("rotation", t, 0, 0, 2.5 * math.sin(TAU * t / 0.07) * (1 - sm(t, 0.0, 0.28))) for t in np.round(np.linspace(0, 0.3, 19), 4)]
      + [kf("rotation", L_HIT, 0, 0, 0)])

# event_break (0,6 s) : bloc cassé. La lame mord la terre (+5°), tire la motte vers soi (−2,5°) et revient ; le fil décharge dans
# le sol (deux formes alternées), gerbe d'étincelles ; sans son.
L_BR = 0.6
brk = anim("event_break", L_BR, "once")
for g in ROCHE:
    deplier(brk, g)
piste_ctrl(brk, ROCHE[0], onoff([(0.0, 0.08), (0.17, 0.21)], L_BR))
piste_ctrl(brk, ROCHE[1], onoff([(0.08, 0.15), (0.26, 0.29)], L_BR))
for k, g in enumerate(GAINES):
    t0 = 0.03 * (NG - 1 - k)
    piste_ctrl(brk, g, [kf("position", t, 0.9 * bump(t, t0, t0 + 0.02, t0 + 0.08, t0 + 0.35)) for t in np.round(np.linspace(0, L_BR, 25), 4)])
piste(brk, F["houe"], [kf("rotation", t, 0, 0, 5.0 * sm(t, 0.0, 0.06) * (1 - sm(t, 0.08, 0.2)) - 2.5 * bump(t, 0.12, 0.22, 0.3, 0.5))
                       for t in np.round(np.linspace(0, L_BR, 25), 4)])
emit(brk, [kf("position", 0, 7), kf("position", 0.2, 7), kf("position", 0.21, -1), kf("position", L_BR, -1)])

ANIMS = [idle, mine, gui, sel, sw, hit, brk]

# ------------------------------------------------------------------ écriture
assert 80 <= len(elements) <= 2500, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
GUI = float(os.environ.get("GUI", "0.84"))
AFFICHAGE = objet.affichage("houe", gui={"scale": [GUI] * 3})
model = objet.modele(NOM, "houe", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, embarquer_sons, cle_son
limiter_sons(model)
embarquer_sons(model, {"arc_houe": "sons/arc_houe.ogg"})
# Un seul son, au coup qui touche (event_hit) : tools/sons.py ne connaît pas encore les événements d'objet, on le pose après.
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "arc_houe")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur le long du manche {LONGUEUR:.1f} px ; largeur {LARGEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)}")
