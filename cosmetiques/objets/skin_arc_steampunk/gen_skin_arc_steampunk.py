"""Pistolet à vapeur : skin d'objet (guide 14) pour tous les arcs du joueur, ensemble Steampunk (thème Mécanique). Design original.
Écrit skin_arc_steampunk.png, skin_arc_steampunk_e.png et .build/skin_arc_steampunk_brut.bbmodel à côté de ce script.
Version en vrai volume (2026-11-10) ; la version en barres octogonales et plaques empilées est gardée dans .build/gen_avant.py
(et la toute première, l'arme portée `pistolet_steampunk`, dans .build/gen_avant_v1.py).

Même design, nom, fiche, repère, étapes, Display et animations que la version d'avant (retour de l'utilisateur sur toute la série :
« faut te baser sur les modèles Minecraft … pour avoir de vrais modèles 3D, pas des couches empilées ; le manche de l'épée par
exemple est bien »). Type `arc` : ses trois étapes de bande deviennent la montée en pression et l'armement du chien, le tir
(flèche qui part) devient le jet de vapeur. Langage du set : skin_epee_steampunk (référence), ligne « Langage » de
sets-objets-2026-11-08.md, .claude/styles/steampunk.md (métal propre : laiton, cuivre, acier bruni ; bois sombre).

Vrai volume (recette .claude/references/objets/volume-3d.md ; tours et peintures de skin_pioche_steampunk) :
- **tours** (couronnes de pans posés sur la surface, face extérieure peinte et découpée en trapèze par l'alpha) pour toutes les
  pièces rondes : chaudière de cuivre rivetée à fonds bombés et cerclages, boîtier et lunette du manomètre, soupape, manchon,
  tuyau à colliers et vanne, ressort à boudin (une spire par groupe), canon d'acier à bagues, **pavillon évasé à 16 pans peint
  dedans et dehors**, chien (axe, bras, marteau, crête), percuteur, lentille-témoin en dôme, fléchette ;
- **plaques fermées biseautées** (plats + biseaux à pente unique par tronçon de contour + chant fermé, faces échantillonnées texel
  par texel et découpées par l'alpha, recouvrement 0,08) pour les pièces plates : crosse de bois à monture de laiton (1,24 px),
  carcasse de laiton à platine rivetée (1,24 px), calotte de crosse, pontet de laiton, détente d'acier poli.
Lumière _e seulement sur des sources logiques : verre ambre du cadran, lentille-témoin (allumée en bande_3), fentes du foyer
sous la chaudière (face -Z, vues de dos).

Repère du skin d'objet : dans le bloc 16³, dessiné comme l'image de l'arc de Minecraft vue depuis +Z (inventaire) : la flèche de
l'image va du bas à droite vers le HAUT À GAUCHE, la poignée de l'arc est vers (5, 10). Donc S_ (le long du canon, vers la bouche)
= (−1, 1, 0)/√2, H_ (vers le haut de l'arme, opposé à la crosse) = (1, 1, 0)/√2, X_ = +Z (côté du manomètre : vu dans l'inventaire et
à la 1re personne). Le poing (P0) est au point que la main tient avec le Display vanilla `item/bow` (repère de bow_pulling_2.png,
inverse de objet.matrice_main) : en visée, canon vers l'avant, crosse vers le bas. Pas de recentrage (le poing reste à P0).

Étapes (groupes à la racine, guide 14 ; le groupe `pistolet` est toujours dessiné) :
`repos` (chien abattu, aiguille basse, lentille éteinte, pas de fléchette), `bande_1` (chien au demi-cran, aiguille au milieu,
fléchette chargée), `bande_2` (chien armé, aiguille haute), `bande_3` (aiguille dans la zone rouge, lentille ambre allumée au _e).

Objet vivant (guide 14), animations de la version d'avant :
- `item_idle` (8 s) : la pression monte par crans (servo : échelon, dépassement, rappel), la soupape tremble puis lâche une petite
  bouffée qui monte (`trans_bouffee`, seul dépliage par scale de ce groupe) ; aucune particule, aucun son ;
- `item_use` (boucle 0,5 s) : pendant que l'arc se bande, la soupape vibre et l'aiguille tremble de plus en plus (Molang
  `q.use_progress`), la vapeur fuit par la soupape (`emit_mc_white_smoke` + `ctrl_emit` = 3·use_progress − 1) ; aucun son ;
- `event_release` (0,8 s) : le chien tombe, le canon recule sur son ressort, jet de vapeur `trans_jet` (seul dépliage par scale de
  ce groupe, fondu `ctrl_alpha`) qui jaillit du pavillon et monte, `emit_mc_poof` + `emit_mc_white_smoke` (`ctrl_emit` +5/+4),
  l'aiguille retombe ; **seul son** du skin : `tir_vapeur` embarqué (sons/tir_vapeur.py, original), clé à 0,04 s (une clé à 0,0
  est muette au premier tir, diagnostic F5) ;
- `event_select` (0,9 s) : l'arme arrive en main : le canon coulisse en place, l'aiguille fait son tour d'essai, la soupape se
  soulève (sans bouffée modélisée : `trans_bouffee` n'est déplié que par item_idle) ; aucun son.
Aucun son sur event_use_start ni event_enter_* (il n'y en a pas). Pas d'item_gui (figé et net dans l'inventaire), pas
d'item_ground (repli : item_idle). Jet et bouffée cachés au repos : géométrie F_GEO / K, enfouie dans la gorge du canon et le
chapeau de soupape ; l'animation l'agrandit (clés scale ≤ 16, guide 3 et 7). Superposition (guide 6.4) : les événements
s'ajoutent à l'état.

Fonctions avancées : `trans_jet`, `trans_bouffee`, `ctrl_alpha`, `emit_mc_white_smoke` ×2, `emit_mc_poof`, `ctrl_emit`, calque _e
(cadran, lentille, foyer), son embarqué `tir_vapeur`, Molang `q.use_progress`. Non simulés par le renderer : ctrl_emit,
particules, animations d'objet en main, Molang des objets (à juger en jeu, `/cosmetique apercu`).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

AVEC_E = True
NOM = "skin_arc_steampunk"
TEX = 512
TAU = 2 * math.pi
K = 16.0            # facteur de réduction du jet et de la bouffée au repos
F_GEO = 2.0         # géométrie F_GEO / K, clés scale ≤ K / F_GEO

# Repère de l'image vanilla bow.png vue depuis +Z (voir l'en-tête) ; poing au point tenu par la main (Display item/bow)
S_ = np.array((-1.0, 1.0, 0.0)) / math.sqrt(2)     # vers la bouche
H_ = np.array((1.0, 1.0, 0.0)) / math.sqrt(2)      # vers le haut de l'arme
X_ = np.array((0.0, 0.0, 1.0))                     # côté du manomètre (inventaire, 1re personne)
D_ = -S_                                           # droite du cadran vu depuis +Z (D_ × H_ = X_)
P0 = np.array((5.0, 10.0, 8.0))                    # milieu du poing


def Wp(s, h=0.0, x=0.0):
    return P0 + S_ * s + H_ * h + X_ * x


def Wv(s, h=0.0, x=0.0):
    return S_ * s + H_ * h + X_ * x


def Lp(s, h=0.0, z=0.0):
    """Repère direct des pièces plates (spec) : (S_, H_, -X_) ; les plaques sont symétriques en z, peintes des deux côtés."""
    return P0 + S_ * s + H_ * h - X_ * z


def Lv(s, h=0.0, z=0.0):
    return S_ * s + H_ * h - X_ * z


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


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def A(c):
    return np.array(c, np.float32)


def dirp(theta):
    """Direction dans le plan de l'arme, theta en degrés depuis l'avant (S_) vers le haut (H_)."""
    a = math.radians(theta)
    return S_ * math.cos(a) + H_ * math.sin(a)


# Palette du set (ligne Langage ; métal propre, brossé ±5 % au plus)
BRASS = dict(hi=A((236, 196, 112)), base=A((190, 142, 64)), low=A((112, 76, 32)))
COPPER = dict(hi=A((232, 150, 96)), base=A((176, 92, 52)), low=A((98, 46, 26)))
STEEL = dict(hi=A((136, 140, 150)), base=A((78, 82, 92)), low=A((38, 40, 48)))
WOOD = dict(hi=A((122, 78, 46)), base=A((84, 50, 30)), low=A((40, 22, 14)))
FIL = A((220, 224, 232))
POLI = A((176, 180, 190))
AMBRE = A((255, 210, 120))
AMBRE_B = A((220, 150, 50))
VAPEUR = A((250, 250, 248))
VAPEUR_B = A((220, 224, 228))

# ------------------------------------------------------------------ cotes (plan s, h ; px) de la version d'avant
HA = 1.55          # axe du canon au-dessus du poing
HC = 3.05          # axe de la chaudière
RCH = 1.0          # apothème de la chaudière (12 pans)
SM = 1.5           # manomètre (flanc +X)
XB = 0.55          # base du boîtier du manomètre
SS = 2.3           # soupape (dessus)
SP = 3.8           # tuyau vertical, vanne
RS0, RS1, RR, NC = 4.35, 5.55, 0.86, 3     # ressort à boudin
NSP = NC * 8
B0 = 7.25          # gorge du pavillon
B_END = 9.1        # bouche du pavillon
H_PIV = (-0.5, 2.15)   # axe du chien
TH_REPOS, TH_ARME = 63.0, 132.0

# ------------------------------------------------------------------ géométrie 2D
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


def bez(P, s):
    P = [np.array(p, float) for p in P]
    u = 1 - s
    c = u ** 3 * P[0] + 3 * u * u * s * P[1] + 3 * u * s * s * P[2] + s ** 3 * P[3]
    d = 3 * u * u * (P[1] - P[0]) + 6 * u * s * (P[2] - P[1]) + 3 * s * s * (P[3] - P[2])
    return c, d / np.linalg.norm(d)


def resample(pts, pas, ferme=False):
    P = np.array(list(pts) + ([pts[0]] if ferme else []), float)
    ls = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    n = max(1, int(round(ls[-1] / pas)))
    out = []
    for x in np.linspace(0, ls[-1], n + 1):
        i = min(np.searchsorted(ls, x, side="right") - 1, len(P) - 2)
        k = (x - ls[i]) / max(ls[i + 1] - ls[i], 1e-9)
        out.append(P[i] + (P[i + 1] - P[i]) * k)
    if ferme:
        out = out[:-1]
    return [tuple(p) for p in out]


def lisse(ctrl, n=10):
    """Contour fermé lissé (Catmull-Rom) passant par les points de contrôle."""
    P = [np.array(p, float) for p in ctrl]
    m = len(P)
    out = []
    for i in range(m):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % m], P[(i + 2) % m]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                    + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)))
    return out


def bande(P, w0, w1, n=24):
    """Contour fermé d'une bande le long d'une Bézier (demi-largeur w0 -> w1), bouts carrés."""
    g, d = [], []
    for s in np.linspace(0, 1, n):
        c, t = bez(P, s)
        no = np.array((-t[1], t[0]))
        w = lerp(w0, w1, s)
        g.append(tuple(c + no * w))
        d.append(tuple(c - no * w))
    return g + d[::-1]


def subdiv(pts, maxlen=0.9):
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


# ------------------------------------------------------------------ cubes différés (monde)
TH = 0.3
DF = 16.0
RECOUV = 0.08
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
    """Cube dans le plan (s, h, x) de l'arme ; chaque face peinte est échantillonnée texel par texel et découpée par l'alpha."""
    X, Y, Z = repere(X, Y)
    c = np.asarray(c, float)
    faces = {}
    for f, fn in peintures.items():
        P = points_face(c, X, Y, Z, s, f)
        col, al, em, m = fn(P)
        if m.any():
            faces[f] = tuile(f"{nom}_{f}", *finir(col, al, em, m))
    if faces:
        CUBES.append({"groupe": groupe, "nom": nom, "c": Lp(*c), "R": np.column_stack([Lv(*X), Lv(*Y), Lv(*Z)]),
                      "half": np.asarray(s, float) / 2, "faces": faces})


# ------------------------------------------------------------------ plaques fermées biseautées (pièces plates)
class Plaque:
    """Plaque fermée dans le plan de l'arme (x = 0) : contour fermé poly, plats à ±h, biseaux à pente unique t_bis du bord
    (demi-épaisseur z_e) au plat, chant vertical qui ferme le bord ; mat = peintures {biseau, plat, chant}."""

    def __init__(self, nom, poly, h, z_e, t_bis, mat, seg=0.9):
        self.nom, self.poly, self.mat = nom, [tuple(map(float, p)) for p in poly], mat
        self.h_, self.ze, self.tb = h, z_e, t_bis
        self.al = math.atan(t_bis)
        self.segs = subdiv(self.poly + [self.poly[0]], seg)
        self.ferme = self.poly + [self.poly[0]]

    def h(self, P):
        return np.full(np.shape(P)[:-1], self.h_)

    def wb(self, P):
        return np.maximum((self.h(P) - self.ze) / self.tb, 0.02)

    def dE(self, P):
        return d_stack(P, self.segs).min(0)


def volume_plaque(pc, groupe):
    for idx, (p, q, v0, v1) in enumerate(pc.segs):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        pm = (p + q) / 2
        if not in_poly(np.array([pm + n * 0.03]), pc.poly)[0]:
            n = -n                                                 # n vers l'intérieur
        wmax = float(pc.wb(p[None])[0])
        e0 = wmax * 1.6 + 0.04 if v0 else 0.04
        e1 = wmax * 1.6 + 0.04 if v1 else 0.04
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        sy = (wmax + 0.1) / math.cos(pc.al)
        for sg in (1, -1):
            Y = np.array((n[0] * math.cos(pc.al), n[1] * math.cos(pc.al), sg * math.sin(pc.al)))
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0], mid[1], sg * pc.ze)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(P, idx=idx, sg=sg):
                P2 = P[..., :2]
                D = d_stack(P2, pc.segs)
                de = D.min(0)
                own = D[idx] <= de + RECOUV
                wb = pc.wb(P2)
                m = in_poly(P2, pc.poly) & own & (de < wb + 0.03) & (de >= -0.02)
                col, em = pc.mat["biseau"](P2, np.clip(de / wb, 0, 1.2), sg)
                return col, None, em, m

            spec(groupe, f"{pc.nom}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut})
        # chant : mur vertical du bord, face extérieure sur le contour
        no = -n
        X = np.array((d[0], d[1], 0.0))
        Y = np.array((0.0, 0.0, 1.0))
        Z = np.cross(X, Y)
        face = "south" if Z[:2] @ no > 0 else "north"
        c = np.array((pm[0], pm[1], 0.0)) - np.array((no[0], no[1], 0.0)) * (TH / 2)

        def chant(P, idx=idx, n=n):
            P2 = P[..., :2] + n * 0.04
            D = d_stack(P2, pc.segs)
            own = D[idx] <= D.min(0) + RECOUV
            col, em = pc.mat["chant"](P2, P[..., 2] / max(pc.ze, 1e-3))
            return col, None, em, own

        spec(groupe, f"{pc.nom}_chant{idx}", c, X, Y, (float(np.linalg.norm(q - p)) + 0.08, 2 * pc.ze + 0.08, TH), {face: chant})
    P = np.array(pc.poly)
    s0, s1 = P[:, 0].min() - 0.05, P[:, 0].max() + 0.05
    h0, h1 = P[:, 1].min() - 0.05, P[:, 1].max() + 0.05
    for sg in (1, -1):
        X = np.array((1.0, 0.0, 0.0))
        Y = np.array((0.0, float(sg), 0.0))
        Z = np.cross(X, Y)
        c = np.array(((s0 + s1) / 2, (h0 + h1) / 2, sg * pc.h_)) - Z * (TH / 2)

        def plat(P, sg=sg):
            P2 = P[..., :2]
            de = pc.dE(P2)
            wb = pc.wb(P2)
            m = in_poly(P2, pc.poly) & (de >= wb - 0.03)
            col, em = pc.mat["plat"](P2, de, wb, sg)
            return col, None, em, m

        spec(groupe, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, (s1 - s0, h1 - h0, TH), {"south": plat})


def brosse(P2, ax=(1.0, 0.0), seed=0.0):
    """Brossé fin (±4 %) le long de ax."""
    ax = np.asarray(ax, float)
    s = P2 @ ax
    r = P2 @ np.array((-ax[1], ax[0]))
    return (np.sin(s * 41.0 + r * 3.0 + seed) * 0.5 + np.sin(s * 17.0 + r * 0.6 + seed * 3) * 0.5) * 0.04


def z3(P2):
    return np.zeros(P2.shape[:-1] + (3,), np.float32)


def mat_laiton(rivets=(), rainure=None, ax=(1.0, 0.0)):
    """Laiton brossé : biseau clair, arête sombre au plat, rainure de platine et rivets en option ; chant sombre."""
    def biseau(P2, f, sg):
        col = lerp(BRASS["hi"], BRASS["base"], np.clip((f - 0.2) / 0.7, 0, 1)[..., None]) * (1 + brosse(P2, ax, 1 + sg))[..., None]
        col = np.where((f < 0.14)[..., None], lerp(BRASS["hi"], FIL, 0.25) + z3(P2), col)
        col = np.where((f >= 0.9)[..., None], BRASS["low"] + z3(P2), col)
        return col, None

    def plat(P2, d, wb, sg):
        col = (BRASS["base"] * 1.04 + z3(P2)) * (1 + brosse(P2, ax, 2 + 3 * sg))[..., None]
        if rainure is not None:
            r0, r1 = rainure
            col = np.where(((d >= wb + r0) & (d < wb + r1))[..., None], BRASS["low"] + z3(P2), col)
            col = np.where(((d >= wb + r1) & (d < wb + r1 + 0.05))[..., None], BRASS["hi"] + z3(P2), col)
        for (rs, rh, rr) in rivets:
            dd = np.hypot(P2[..., 0] - rs, P2[..., 1] - rh)
            col = np.where((dd < rr)[..., None], BRASS["low"] + z3(P2), col)
            col = np.where((dd < rr * 0.72)[..., None], BRASS["hi"] + z3(P2), col)
            col = np.where((np.hypot(P2[..., 0] - rs + rr * 0.25, P2[..., 1] - rh - rr * 0.25) < rr * 0.3)[..., None], FIL + z3(P2), col)
        return col, None

    def chant(P2, zn):
        k = np.clip(0.55 - 0.35 * np.abs(zn), 0, 1)[..., None]
        return lerp(BRASS["low"], BRASS["base"], k) + z3(P2), None

    return dict(biseau=biseau, plat=plat, chant=chant)


def mat_acier_poli():
    def biseau(P2, f, sg):
        col = lerp(FIL, POLI, np.clip((f - 0.1) / 0.5, 0, 1)[..., None]) + z3(P2)
        col = np.where((f >= 0.9)[..., None], STEEL["base"] + z3(P2), col)
        return col, None

    def plat(P2, d, wb, sg):
        return (POLI * 0.92 + z3(P2)) * (1 + brosse(P2, (0.3, 1.0), sg))[..., None], None

    def chant(P2, zn):
        return lerp(STEEL["hi"], STEEL["base"], np.abs(zn)[..., None]) + z3(P2), None

    return dict(biseau=biseau, plat=plat, chant=chant)


GAX = unit(np.array((-0.8, -3.05)))      # axe de la crosse (vers le bas, un peu vers l'arrière)


def mat_crosse():
    """Plaquettes de bois sombre veiné (quadrillage au centre), monture de laiton sur les biseaux et le chant ; vis de laiton."""
    perp = np.array((-GAX[1], GAX[0]))

    def biseau(P2, f, sg):
        col = lerp(BRASS["hi"], BRASS["base"], np.clip((f - 0.15) / 0.6, 0, 1)[..., None]) * (1 + brosse(P2, GAX, 4 + sg))[..., None]
        col = np.where((f >= 0.88)[..., None], BRASS["low"] + z3(P2), col)
        return col, None

    def plat(P2, d, wb, sg):
        a, r = P2 @ GAX, P2 @ perp
        g = np.sin(a * 6.0 + r * 9.0 + np.sin(a * 1.7 + r * 3.0) * 1.6)
        k = np.clip(0.42 + 0.18 * np.sin(r * 4.0 + 0.6) + 0.1 * g, 0, 1)
        col = lerp(WOOD["low"], WOOD["hi"], k[..., None]) + z3(P2)
        dd = d - wb
        col = np.where((dd < 0.07)[..., None], WOOD["low"] * 0.8 + z3(P2), col)        # ombre contre la monture
        # quadrillage (losanges) dans la zone centrale de la plaquette
        zone = (dd > 0.2) & (a > 1.1) & (a < 2.45)
        u, v = (a + r) / 0.21, (a - r) / 0.21
        ligne = (np.abs(u - np.round(u)) < 0.16) | (np.abs(v - np.round(v)) < 0.16)
        col = np.where((zone & ligne)[..., None], WOOD["low"] * 0.75 + z3(P2), col)
        col = np.where((zone & ~ligne)[..., None], col * 1.08, col)
        # vis de plaquette (laiton) sous le poing
        cv = np.array((-0.12, -0.75))
        dv = np.hypot(P2[..., 0] - cv[0], P2[..., 1] - cv[1])
        col = np.where((dv < 0.13)[..., None], BRASS["low"] + z3(P2), col)
        col = np.where((dv < 0.095)[..., None], BRASS["hi"] + z3(P2), col)
        col = np.where(((dv < 0.095) & (np.abs((P2 - cv) @ np.array((0.7, 0.7))) < 0.022))[..., None], BRASS["low"] + z3(P2), col)
        return col, None

    def chant(P2, zn):
        k = np.clip(0.55 - 0.35 * np.abs(zn), 0, 1)[..., None]
        return lerp(BRASS["low"], BRASS["base"], k) + z3(P2), None

    return dict(biseau=biseau, plat=plat, chant=chant)


# ------------------------------------------------------------------ tours (pièces rondes, recette de skin_epee_steampunk)
OVL, OVW = 0.04, 0.03
DENS = 16.0


def p_laiton(xn, t, y, r, L, ex):
    k = np.clip(0.3 + 0.55 * (1 - np.abs(xn) ** 1.4) + ex.get("clair", 0.0), 0, 1)
    col = lerp(BRASS["low"], BRASS["hi"], k[..., None])
    if ex.get("arete"):
        col = np.where(((y < 0.06) | (y > L - 0.06))[..., None], BRASS["low"] * 0.85, col)
    return col, None


def p_laiton_in(xn, t, y, r, L, ex):
    """Dedans du pavillon : laiton plus sombre qui s'assombrit vers la gorge."""
    k = np.clip(0.15 + 0.35 * t + 0.2 * (1 - np.abs(xn)), 0, 1)
    return lerp(BRASS["low"] * 0.55, BRASS["base"], k[..., None]), None


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
    col = lerp(STEEL["low"], STEEL["hi"], k[..., None])
    if ex.get("strie"):
        col = np.where(((np.floor(y / 0.07) % 2) == 0)[..., None], col * 0.82, col)
    return col, None


def p_poli(xn, t, y, r, L, ex):
    k = np.clip(0.2 + 0.7 * (1 - np.abs(xn) ** 1.2) + ex.get("clair", 0.0), 0, 1)
    col = lerp(STEEL["base"], POLI, k[..., None])
    return np.where((np.abs(xn) < 0.18)[..., None], lerp(col, FIL, 0.5), col), None


def p_ambre(xn, t, y, r, L, ex):
    q = np.abs(xn + 0.25)
    col = lerp(A((255, 236, 180)), AMBRE_B, np.clip(q / 1.2, 0, 1)[..., None] ** 0.9)
    em = lerp(A((225, 170, 80)), A((160, 100, 30)), np.clip(np.abs(xn), 0, 1)[..., None])
    return col, em


def p_ambre_eteint(xn, t, y, r, L, ex):
    q = np.abs(xn + 0.25)
    return lerp(A((176, 120, 52)), A((92, 56, 22)), np.clip(q / 1.2, 0, 1)[..., None] ** 0.9), None


def p_suie(xn, t, y, r, L, ex):
    return np.zeros(xn.shape + (3,), np.float32) + A((34, 28, 24)), None


PEINTRES = {"laiton": p_laiton, "laiton_in": p_laiton_in, "cuivre": p_cuivre, "acier": p_acier, "poli": p_poli,
            "ambre": p_ambre, "ambre_eteint": p_ambre_eteint, "suie": p_suie}


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
    """profil = [(b0, r0, b1, r1, mat, ex), ...] le long de ax depuis O (monde) ; une couronne de n pans par tronçon.
    ex["dedans"] = matière : la face intérieure du pan est peinte aussi (pavillon)."""
    O, ax = np.asarray(O, float), unit(ax)
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    for i, (b0, r0, b1, r1, mat, ex) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        if L < 1e-4:
            continue
        tile = tuile_pan(f"{nom}{i}", mat, L, 2 * r0 * tn, 2 * r1 * tn, r0, r1, ex)
        faces = {"south": tile}
        if ex.get("dedans"):
            faces["north"] = tuile_pan(f"{nom}{i}_in", ex["dedans"], L, 2 * r0 * tn, 2 * r1 * tn, r0, r1, {})
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
                          "half": np.array((wm / 2, L / 2 + OVL, TH / 2)), "faces": dict(faces)})


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
        tour(g, f"{nom}{i}_", p, q - p, X_, [(-0.08, r, Ln + 0.08, r, mat, {})], n=8, phase=math.pi / 8)
    for i in range(1, len(pts) - 1):
        d = unit(unit(pts[i + 1] - pts[i]) + unit(pts[i] - pts[i - 1]))
        tour(g, f"{nom}c{i}_", pts[i], d, X_, bague(-0.17, r - 0.02, collier, 0.34), n=8, phase=math.pi / 8)


# ------------------------------------------------------------------ tuiles peintes (cadran, foyer, vapeur)
def disque_t(n, fn, ss=4):
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
    """Cadran : verre ambre, 13 crans (-120° à +120° depuis le haut, sens horaire), zone rouge en haut de l'échelle, reflet."""
    col = lerp(BRASS["hi"], BRASS["low"], np.clip(0.5 - 0.5 * Y, 0, 1)[..., None] * 0.8) * np.ones(R.shape + (1,), np.float32)
    em = np.zeros(R.shape + (3,), np.float32)
    ang = np.degrees(np.arctan2(X, Y))
    glass = R < 0.86
    col[(R > 0.86) & (R < 0.92)] = BRASS["low"] * 0.7
    g = lerp(AMBRE, AMBRE_B, np.clip(R / 0.86, 0, 1)[..., None] ** 1.5)
    col[glass] = g[glass]
    em[glass] = (190, 126, 40)
    red = glass & (R > 0.52) & (R < 0.78) & (ang > 84) & (ang < 124)
    col[red] = (176, 44, 30)
    em[red] = (150, 30, 14)
    for k in range(13):
        a = -120 + 20 * k
        r0 = 0.52 if k % 2 == 0 else 0.64
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        along = X * sa + Y * ca
        across = np.abs(X * ca - Y * sa)
        tick = glass & (along > r0) & (along < 0.8) & (across < (0.065 if k % 2 == 0 else 0.045))
        col[tick] = (58, 32, 18)
        em[tick] = 0
    hl = glass & (np.abs(R - 0.68) < 0.04) & (ang < -40) & (ang > -95)
    col[hl] = lerp(AMBRE, VAPEUR, 0.7)
    return col, em


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


def t_foyer(W=36, H=16):
    """Porte de foyer : cadre d'acier, 4 fentes rougeoyantes (_e vif), 4 rivets de laiton."""
    c = STEEL["base"] * np.ones((H, W, 3), np.float32)
    c[:2], c[:, :2] = STEEL["hi"], STEEL["hi"]
    c[-2:], c[:, -2:] = STEEL["low"], STEEL["low"]
    e = np.zeros((H, W, 3), np.float32)
    for x0 in (7, 13, 19, 25):
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


TILES["cadran"] = disque_t(32, f_cadran)
TILES["aiguille"] = t_aiguille()
TILES["foyer"] = t_foyer()
TILES["acier_b"] = t_unie(STEEL["hi"], STEEL["low"], bord=STEEL["low"])
TILES["laiton_b"] = t_unie(BRASS["hi"], BRASS["low"], bord=BRASS["low"])
TILES["jet"] = t_vapeur(128, 56, 71, plume=True)
TILES["bouffee"] = t_vapeur(48, 56, 72, plume=False)
TRANS.update({"jet", "bouffee"})


# ------------------------------------------------------------------ conception
GROUPES = []        # (nom, pivot monde, parent, rotation)


def grp(nom, pivot, parent, rotation=(0.0, 0.0, 0.0)):
    GROUPES.append((nom, np.asarray(pivot, float), parent, rotation))
    return nom


def plaque_vapeur(g, nom, c, X, Y, half, tile):
    boite(g, nom, c, X, Y, 2 * np.asarray(half, float), {"south": tile, "north": tile})


C_AX = lambda s: Wp(s, HA)
OUT = {}

# contours des pièces plates (plan s, h)
CROSSE = lisse([(0.95, 1.0), (0.74, 0.2), (0.52, -0.85), (0.3, -1.85), (0.12, -2.38), (-0.35, -2.5), (-0.9, -2.3),
                (-0.82, -1.3), (-0.64, -0.2), (-0.66, 0.55), (-0.9, 0.95), (0.0, 1.05)], n=4)


def calotte(poly, a_cut, off=0.13):
    """Calotte de crosse : le bas du contour de la crosse (au-delà de a_cut le long de GAX) décalé de off vers l'extérieur,
    fermé par la coupe droite (le chant de la calotte reste à off du chant de la crosse : pas de faces presque confondues)."""
    P = np.array(resample(poly, 0.12, ferme=True))
    n = len(P)
    a = P @ GAX
    i0 = int(np.argmax(a))
    idx = [i0]
    for sens in (1, -1):
        j = i0
        while a[(j + sens) % n] > a_cut:
            j = (j + sens) % n
            idx = idx + [j] if sens > 0 else [j] + idx
    out = []
    for j in idx:
        t = unit(P[(j + 1) % n] - P[j - 1])
        no = np.array((t[1], -t[0]))
        if in_poly((P[j] + no * 0.02)[None], [tuple(q) for q in P])[0]:
            no = -no
        out.append(tuple(P[j] + no * off))
    return resample(out, 0.3)


CARCASSE = [(-0.95, 1.05), (-0.75, 0.8), (1.6, 0.8), (1.88, 1.05), (1.88, 2.3), (-0.95, 2.3)]
PONTET = bande([(1.62, 0.95), (1.72, -0.2), (1.35, -0.62), (0.48, -0.55)], 0.15, 0.13, n=16)
DETENTE = bande([(1.08, 0.88), (1.08, 0.45), (0.94, 0.12), (1.14, -0.08)], 0.13, 0.08, n=10)


def conception():
    pis = grp("pistolet", P0, None)

    # --- pièces plates : plaques fermées biseautées
    volume_plaque(Plaque("crosse", resample(CROSSE, 0.42, ferme=True), 0.62, 0.38, 1.0, mat_crosse()), pis)
    volume_plaque(Plaque("calotte", calotte(CROSSE, float(np.array((0.0, -2.05)) @ GAX)), 0.75, 0.47, 1.0, mat_laiton(ax=tuple(GAX))), pis)
    volume_plaque(Plaque("carcasse", CARCASSE, 0.62, 0.4, 1.0,
                         mat_laiton(rivets=((-0.62, 1.12, 0.1), (1.5, 1.12, 0.1), (0.45, 1.12, 0.1)), rainure=(0.16, 0.22)), seg=0.8), pis)
    volume_plaque(Plaque("pontet", resample(PONTET, 0.3, ferme=True), 0.17, 0.08, 1.0, mat_laiton(ax=(0.0, 1.0))), pis)
    volume_plaque(Plaque("detente", resample(DETENTE, 0.2, ferme=True), 0.13, 0.06, 1.0, mat_acier_poli()), pis)
    # anneau de dragonne sous la calotte
    tour(pis, "dragonne", Wp(-0.42, -2.48), Wv(GAX[0], GAX[1]), X_,
         [(0.0, 0.26, 0.12, 0.26, "laiton", {"arete": True}), (0.12, 0.26, 0.2, 0.12, "laiton", {"clair": 0.1}),
          (0.2, 0.12, 0.23, 0.0, "laiton", {"clair": 0.25})], n=8)

    # --- chaudière de cuivre rivetée au-dessus de la carcasse : fonds bombés, cerclages de laiton
    ch = [(-0.3, 0.0, -0.27, 0.42, "cuivre", {"clair": 0.15}), (-0.27, 0.42, -0.1, 0.78, "cuivre", {"clair": 0.08}),
          (-0.1, 0.78, 0.0, RCH, "cuivre", {})]
    ch += [(0.0, RCH, 0.45, RCH, "cuivre", {"riv": 0.45, "y0": 0.22})]
    ch += bague(0.45, RCH, RCH + 0.13, 0.35)
    ch += [(0.8, RCH, 2.2, RCH, "cuivre", {"riv": 0.47, "y0": 0.0})]
    ch += bague(2.2, RCH, RCH + 0.13, 0.35)
    ch += [(2.55, RCH, 3.0, RCH, "cuivre", {"riv": 0.45, "y0": 0.22}),
           (3.0, RCH, 3.1, 0.78, "cuivre", {}), (3.1, 0.78, 3.27, 0.42, "cuivre", {"clair": 0.08}),
           (3.27, 0.42, 3.3, 0.0, "cuivre", {"clair": 0.15})]
    tour(pis, "chaudiere", Wp(0, HC), S_, X_, ch, n=12)
    # percuteur : bouton d'acier au dos du fond arrière, là où frappe le chien
    tour(pis, "percuteur", Wp(-0.25, 2.72), -S_, X_, [(0.0, 0.17, 0.26, 0.17, "acier", {}), (0.26, 0.17, 0.3, 0.0, "poli", {})], n=8)
    # manomètre sur le flanc +X : boîtier et lunette de laiton à 16 pans, cadran ambre, moyeu (aiguille dans les étapes)
    tour(pis, "manometre", Wp(SM, HC, XB), X_, H_,
         [(0.0, 0.62, 0.42, 0.62, "laiton", {}), (0.42, 0.62, 0.42, 0.7, "laiton", {}),
          (0.42, 0.7, 0.74, 0.7, "laiton", {"arete": True}), (0.74, 0.7, 0.8, 0.6, "laiton", {"clair": 0.2})], n=16)
    boite(pis, "cadran", Wp(SM, HC, XB + 0.68), D_, H_, (1.22, 1.22, 0.12), {"south": "cadran"})
    boite(pis, "moyeu", Wp(SM, HC, XB + 0.79), D_, H_, (0.16, 0.16, 0.08), {f: "laiton_b" for f in SIX})
    # porte du foyer sous la chaudière, au dos (-X) : fentes rougeoyantes
    boite(pis, "foyer", Wp(SM, HC, -(RCH + 0.05)), D_, H_, (1.1, 0.48, 0.1), {"north": "foyer"})

    # --- soupape sur le dessus : tige d'acier, chapeau de laiton mobile, bouffée cachée dans le chapeau
    vb = Wp(SS, HC + RCH - 0.05)
    tour(pis, "soupape_tige", vb, H_, X_, [(0.0, 0.17, 0.55, 0.17, "acier", {})], n=8)
    soup = grp("soupape", vb + H_ * 0.5, pis)
    tour(soup, "soupape_chapeau", vb, H_, X_, [(0.5, 0.17, 0.5, 0.34, "laiton", {}), (0.5, 0.34, 0.78, 0.34, "laiton", {"arete": True}),
                                              (0.78, 0.34, 0.8, 0.14, "laiton", {}), (0.8, 0.14, 0.94, 0.14, "laiton", {"clair": 0.1}),
                                              (0.94, 0.14, 0.97, 0.0, "laiton", {"clair": 0.2})], n=8)
    bo = vb + H_ * 0.62
    bouf = grp("trans_bouffee", bo, soup)
    for k in range(3):
        ang = math.radians(60 * k)
        Xp = X_ * math.cos(ang) + S_ * math.sin(ang)
        plaque_vapeur(bouf, f"bouffee{k}", bo + H_ * (1.05 * F_GEO / K), Xp, H_, np.array((0.9, 1.05, 0.15)) * F_GEO / K, "bouffee")
    # fuite de vapeur à la soupape pendant la montée en pression (item_use) : +Y du groupe vers le haut de l'arme (H_)
    em_s = grp("emit_mc_white_smoke@2", vb + H_ * 1.05, soup, rotation=(0, 0, -45))
    grp("ctrl_emit@2", vb + H_ * 1.05, em_s)

    # --- manchon du canon, tuyau de cuivre à vanne de la chaudière au manchon
    ma = [(1.7, 0.5, 1.7, 0.7, "laiton", {}), (1.7, 0.7, 4.05, 0.7, "laiton", {})]
    ma += bague(4.05, 0.7, 0.92, 0.3, "cuivre", {"riv": 0.4})
    ma += [(4.35, 0.7, 4.35, 0.5, "laiton", {"clair": -0.1})]
    tour(pis, "manchon", C_AX(0), S_, X_, ma, n=12)
    tour(pis, "manchon_bague", C_AX(0), S_, X_, bague(2.2, 0.7, 0.8, 0.22), n=12)
    tuyau(pis, "tuyau", [Wp(3.15, HC), Wp(SP, HC), Wp(SP, HA + 0.5)], 0.22)
    vm = Wp(SP, 2.38)
    tour(pis, "vanne", vm, H_, X_, [(-0.2, 0.22, -0.2, 0.32, "laiton", {}), (-0.2, 0.32, 0.2, 0.32, "laiton", {"arete": True}),
                                    (0.2, 0.32, 0.2, 0.22, "laiton", {})], n=8, phase=math.pi / 8)
    tour(pis, "vanne_tige", vm + X_ * 0.25, X_, H_, [(0.0, 0.08, 0.42, 0.08, "acier", {})], n=8)
    RV, VC = 0.34, vm + X_ * 0.66
    for k in range(8):
        a_ = TAU * (k + 0.5) / 8
        e_ = S_ * math.cos(a_) + H_ * math.sin(a_)
        t_ = -S_ * math.sin(a_) + H_ * math.cos(a_)
        boite(pis, f"jante{k}", VC + e_ * RV, t_, e_, (2 * RV * math.tan(math.pi / 8) + 0.06, 0.12, 0.12), {f: "acier_b" for f in SIX})
    for k in range(2):
        a_ = math.pi / 4 + math.pi / 2 * k
        boite(pis, f"rayon{k}", VC, S_ * math.cos(a_) + H_ * math.sin(a_), -S_ * math.sin(a_) + H_ * math.cos(a_), (2 * RV - 0.06, 0.08, 0.08),
              {f: "acier_b" for f in SIX})
    boite(pis, "v_moyeu", VC, S_, H_, (0.18, 0.18, 0.14), {f: "laiton_b" for f in SIX})

    # --- ressort à boudin : du manchon à la bague du canon ; chaque tronçon de spire dans son groupe (compression au recul)
    pts = []
    for i in range(NSP + 1):
        th = i * TAU / 8 + math.pi / 8
        s = RS0 + (RS1 - RS0) * i / NSP
        pts.append(Wp(s, HA + RR * math.sin(th), RR * math.cos(th)))
    spires = []
    for i in range(NSP):
        gsp = grp(f"spire{i}", pts[i], pis)
        spires.append(gsp)
        Ln = float(np.linalg.norm(pts[i + 1] - pts[i]))
        tour(gsp, "spire", pts[i], pts[i + 1] - pts[i], S_, [(-0.05, 0.09, Ln + 0.05, 0.09, "acier", {"clair": 0.1})], n=6)

    # --- canon coulissant : tube d'acier, bagues, pavillon évasé peint dedans et dehors
    can = grp("canon", C_AX(4.2), pis)
    tu = [(2.0, 0.0, 2.0, 0.5, "acier", {}), (2.0, 0.5, 7.4, 0.5, "acier", {})]
    tu += bague(5.55, 0.5, 0.92, 0.3)
    tu += bague(6.95, 0.5, 0.64, 0.3, "cuivre", {"riv": 0.33})
    tour(can, "tube", C_AX(0), S_, X_, tu, n=12)
    pv = [(B0 - 0.1, 0.5, B0 + 0.55, 0.6, "laiton", {"dedans": "laiton_in"}),
          (B0 + 0.55, 0.6, B0 + 1.2, 0.86, "laiton", {"dedans": "laiton_in"}),
          (B0 + 1.2, 0.86, B_END, 1.45, "laiton", {"dedans": "laiton_in", "clair": 0.05})]
    pv += [(B_END, 1.45, B_END + 0.06, 1.55, "laiton", {"clair": 0.1}), (B_END + 0.06, 1.55, B_END + 0.14, 1.55, "laiton", {"arete": True}),
           (B_END + 0.14, 1.55, B_END + 0.14, 1.3, "laiton", {"clair": 0.15})]
    tour(can, "pavillon", C_AX(0), S_, X_, pv, n=16, phase=math.pi / 16)
    tour(can, "gorge", C_AX(B0 + 0.05), S_, X_, [(0.0, 0.5, 0.0, 0.0, "suie", {})], n=12)

    # jet de vapeur : 3 plaques croisées contenant l'axe, cachées dans la gorge (taille F_GEO / K)
    JL, JW = 5.5, 3.2
    jet = grp("trans_jet", C_AX(B0), can)
    for k in range(3):
        ang = math.radians(60 * k + 30)
        Yp = H_ * math.cos(ang) + X_ * math.sin(ang)
        plaque_vapeur(jet, f"jet{k}", C_AX(B0) + S_ * (JL / 2 * F_GEO / K), S_, Yp, np.array((JL / 2, JW / 2, 0.15)) * F_GEO / K, "jet")
    grp("ctrl_alpha", C_AX(B0), jet)
    # particules de Minecraft à la bouche : +Y du groupe le long du canon (rotation Z +45° : +Y vers S_)
    e1 = grp("emit_mc_poof", C_AX(B_END - 0.15), can, rotation=(0, 0, 45))
    grp("ctrl_emit@1", C_AX(B_END - 0.15), e1)
    e3 = grp("emit_mc_white_smoke@1", C_AX(B_END - 0.4), can, rotation=(0, 0, 45))
    grp("ctrl_emit@3", C_AX(B_END - 0.4), e3)

    # ================================================================== étapes (montée en pression, armement du chien)
    piv = Wp(*H_PIV)

    def chien(g, theta):
        d = dirp(theta)
        tete = piv + d * 0.95
        tour(g, "chien_axe", piv - X_ * 0.72, X_, H_, [(0.0, 0.0, 0.0, 0.2, "laiton", {"clair": 0.1}),
                                                     (0.0, 0.2, 1.44, 0.2, "acier", {}), (1.44, 0.2, 1.44, 0.0, "laiton", {"clair": 0.1})], n=8)
        tour(g, "chien_bras", piv, d, X_, [(0.0, 0.17, 0.95, 0.13, "acier", {})], n=8)
        tour(g, "chien_tete", tete - X_ * 0.25, X_, d, [(0.0, 0.0, 0.0, 0.25, "poli", {}), (0.0, 0.25, 0.5, 0.25, "acier", {"strie": True}),
                                                        (0.5, 0.25, 0.5, 0.0, "poli", {})], n=8)
        tour(g, "chien_crete", tete, dirp(theta + 60), X_, [(0.0, 0.13, 0.48, 0.06, "acier", {"strie": True}), (0.48, 0.06, 0.52, 0.0, "poli", {})], n=8)

    def aiguille(g, nom, level):
        """Aiguille du manomètre : groupe tournant autour de X_ (niveau 0..6 = -120°..+120° depuis le haut, sens horaire vu de +Z)."""
        a = math.radians(-120 + 40 * level)
        d = H_ * math.cos(a) + D_ * math.sin(a)
        c0 = Wp(SM, HC, XB + 0.77)
        ga = grp(nom, c0, g)
        boite(ga, nom, c0 + d * 0.22, np.cross(d, X_), d, (0.11, 0.6, 0.05), {f: "aiguille" for f in SIX})
        return ga

    def flechette(g):
        """Fléchette d'acier chargée dans le canon (la flèche du jeu), tête hors du pavillon, bague de cuivre."""
        fl = [(6.3, 0.0, 6.3, 0.13, "acier", {}), (6.3, 0.13, B_END - 0.2, 0.13, "acier", {})]
        fl += bague(B_END - 0.55, 0.13, 0.24, 0.2, "cuivre")
        fl += [(B_END - 0.2, 0.13, B_END - 0.2, 0.3, "poli", {}), (B_END - 0.2, 0.3, B_END + 0.25, 0.22, "poli", {}),
               (B_END + 0.25, 0.22, B_END + 0.62, 0.0, "poli", {"clair": 0.15})]
        tour(g, "flechette", C_AX(0), S_, X_, fl, n=8)

    etapes = [("repos", TH_REPOS, 1.0, False, False), ("bande_1", 100.0, 3.0, False, True), ("bande_2", TH_ARME, 4.5, False, True),
              ("bande_3", TH_ARME, 6.0, True, True)]
    stage, aig, chi = {}, {}, {}
    for nom_e, th, lvl, lit, fl in etapes:
        g = grp(objet.etape(nom_e, "arc"), (8, 8, 8), None)
        stage[nom_e] = g
        gc = grp("chien_" + nom_e, piv, g)
        chi[nom_e] = gc
        chien(gc, th)
        aig[nom_e] = aiguille(g, "aiguille_" + nom_e, lvl)
        mat = "ambre" if lit else "ambre_eteint"
        tour(g, "lentille_" + ("on" if lit else "off"), Wp(-0.5, 1.45, 0.56), X_, H_,
             [(0.0, 0.36, 0.2, 0.36, "laiton", {"arete": True}), (0.2, 0.36, 0.2, 0.26, "laiton", {"clair": 0.1}),
              (0.2, 0.26, 0.3, 0.18, mat, {}), (0.3, 0.18, 0.34, 0.0, mat, {})], n=8)
        if fl:
            flechette(g)
    OUT.update(pistolet=pis, soupape=soup, bouffee=bouf, canon=can, jet=jet, spires=spires, stage=stage, aig=aig, chien=chi,
               etapes=etapes)


conception()


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
    if abs(R[2, 0]) < 1 - 1e-9:
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
    return {"name": name.split("@")[0], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node(n) for n, gg in groups.items() if gg["parent"] is None]


# ------------------------------------------------------------------ animations (objet vivant, guide 14 ; celles d'avant)
def kf(t, x, y, z, ch="rotation"):
    f = lambda v: v if isinstance(v, str) else f"{v + 0.0:.4f}".rstrip("0").rstrip(".")
    return {"channel": ch, "data_points": [{"x": f(x), "y": f(y), "z": f(z)}], "time": round(t, 4), "interpolation": "linear"}


def anim(name, length, tracks, fps=24, loop="loop"):
    """tracks : {(groupe, canal): f(t) -> (x, y, z)} échantillonné, ou (x, y, z) constant (Molang permis)."""
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A__ = {}
    for (g, ch), f in tracks.items():
        ks = [kf(t, *f(t), ch=ch) for t in times] if callable(f) else [kf(0.0, *f, ch=ch), kf(length, *f, ch=ch)]
        A__.setdefault(groups[g]["uuid"], {"name": g.split("@")[0], "type": "bone", "keyframes": []})["keyframes"] += ks
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": False, "animators": A__}


def step(tau, rise=0.05, over=0.28):
    """Échelon de servo : montée courte, dépassement puis rappel amorti (un rebond)."""
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


SOUP, BOUF, CAN, JET, SPIRES = OUT["soupape"], OUT["bouffee"], OUT["canon"], OUT["jet"], OUT["spires"]
AIG, CHIEN = OUT["aig"], OUT["chien"]
CE_POOF, CE_SOUP, CE_BOUCHE = "ctrl_emit@1", "ctrl_emit@2", "ctrl_emit@3"

# --- item_idle (8 s) : deux cycles de pression ; crans +1, +1, tremblement, décharge −2 (bouffée qui monte)
L_IDLE = 8.0
TICKS = [0.9, 1.9, 4.9, 5.9]
PUFFS = [3.0, 7.0]
TW = 0.55


def tremble(t):
    return sum(bump(t, tp - TW, tp - TW * 0.75, tp - 0.03, tp) for tp in PUFFS)


def idle_level(t):
    v = sum(step(t - ti) for ti in TICKS) - sum(2 * step(t - tp - 0.03, rise=0.07, over=0.11) for tp in PUFFS)
    return v + 0.13 * tremble(t) * math.sin(TAU * 19 * t)


def puff(t, tp, p=1.0):
    """(taille relative, montée) d'une bouffée partie à tp."""
    if not (tp <= t <= tp + 0.72 * p):
        return 0.0, 0.0
    sz = sm(t, tp + 0.02, tp + 0.1 * p) * (1 + 0.3 * sm(t, tp + 0.1 * p, tp + 0.45 * p)) * (1 - sm(t, tp + 0.3 * p, tp + 0.62 * p))
    up = 0.9 * sm(t, tp + 0.05, tp + 0.62 * p) * (1 - sm(t, tp + 0.64 * p, tp + 0.7 * p))
    return sz, up


def puff_scale_at(t, tps):
    sz = max(puff(t, tp)[0] for tp in tps)
    k = (1 + (K - 1) * sz) / F_GEO
    return k, k, k


def puff_pos_at(t, tps):
    return le_long(max(puff(t, tp)[1] for tp in tps), H_)


def valve_at(t, tps, trem):
    y = 0.035 * trem * math.sin(TAU * 23 * t + 0.7)
    for tp in tps:
        y += 0.24 * (step(t - tp, rise=0.035, over=0.2) - step(t - tp - 0.18, rise=0.04, over=0.35))
    return le_long(y, H_)


item_idle = anim("item_idle", L_IDLE, {
    (AIG["repos"], "rotation"): lambda t: needle(idle_level(t)),
    (SOUP, "position"): lambda t: valve_at(t, PUFFS, tremble(t)),
    (BOUF, "scale"): lambda t: puff_scale_at(t, PUFFS), (BOUF, "position"): lambda t: puff_pos_at(t, PUFFS),
    (CE_POOF, "position"): (-1, 0, 0), (CE_SOUP, "position"): (-1, 0, 0), (CE_BOUCHE, "position"): (-1, 0, 0)}, fps=30)

# --- item_use (boucle 0,5 s) : la pression monte avec q.use_progress (les étapes portent l'aiguille et le chien) ;
# la soupape vibre, les aiguilles tremblent, la vapeur fuit à la soupape de plus en plus fort ; rien ne part de la bouche.
VIB = "math.sin(q.anim_time * 360 * 22) * 0.05 * q.use_progress"
TREM = "math.sin(q.anim_time * 360 * 18) * 7 * q.use_progress * q.use_progress"
use_tracks = {(SOUP, "position"): (VIB + " * 0.7071", VIB + " * 0.7071", 0),
              (CE_SOUP, "position"): ("q.use_progress * 3 - 1", 0, 0),
              (CE_POOF, "position"): (-1, 0, 0), (CE_BOUCHE, "position"): (-1, 0, 0)}
for e in ("bande_1", "bande_2", "bande_3"):
    use_tracks[(AIG[e], "rotation")] = (0, 0, TREM)
item_use = anim("item_use", 0.5, use_tracks)

# --- event_release (0,8 s) : la flèche part. Le chien tombe, le canon recule sur son ressort, jet de vapeur qui monte, l'aiguille
# retombe de la zone rouge (écart depuis le niveau du repos), bouffée et vapeur de Minecraft à la bouche, un son.
REC = 0.6


def recoil(t):
    return REC * sm(t, 0.02, 0.045) * (1 - sm(t, 0.09, 0.3)) - 0.1 * bump(t, 0.25, 0.31, 0.33, 0.45)


def jet_scale(t):
    w = sm(t, 0.03, 0.11) * (1 + 0.3 * sm(t, 0.11, 0.45)) * (1 - sm(t, 0.55, 0.68))
    k = (1 + (K - 1) * w) / F_GEO
    return k, k, k


def jet_pos(t):
    env = 1 - sm(t, 0.66, 0.7)
    return le_long(1.0 * sm(t, 0.12, 0.62) * env, S_ * 0.6 + H_ * 0.8)     # le jet file vers l'avant puis monte


def jet_alpha(t):
    return -sm(t, 0.32, 0.64) * (1 - sm(t, 0.72, 0.76)), 0.0, 0.0


def needle_release(t):
    return needle(5 * (1 - step(t - 0.035, rise=0.06, over=0.08)))     # de 6 (zone rouge) à 1 (repos)


rel_tracks = {(CAN, "position"): lambda t: le_long(recoil(t), -S_),
              (CHIEN["repos"], "rotation"): lambda t: (0.0, 0.0, (TH_REPOS - TH_ARME) * (1 - sm(t, 0.0, 0.025)) + 4 * bump(t, 0.02, 0.03, 0.05, 0.12)),
              (AIG["repos"], "rotation"): needle_release,
              (JET, "scale"): jet_scale, (JET, "position"): jet_pos, ("ctrl_alpha", "position"): jet_alpha,
              (CE_POOF, "position"): lambda t: (5 * bump(t, 0.03, 0.05, 0.12, 0.18), 0.0, 0.0),
              (CE_BOUCHE, "position"): lambda t: (4 * bump(t, 0.06, 0.09, 0.4, 0.5), 0.0, 0.0)}
for i, gsp in enumerate(SPIRES):
    # compression du ressort : le tronçon i avance de recul × i / NSP (le bout côté canon suit la bague)
    rel_tracks[(gsp, "position")] = (lambda t, f=(i + 0.5) / NSP: le_long(recoil(t) * f, -S_))
event_release = anim("event_release", 0.8, rel_tracks, fps=60, loop="once")
event_release["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "tir_vapeur", "file": ""}], "time": 0.04}]}


# --- event_select (0,9 s) : l'arme arrive en main. Le canon coulisse en place (ressort qui se détend), l'aiguille fait son tour
# d'essai par crans (monte de 3, retombe), la soupape se soulève. Aucun son, aucune échelle (bouffée : item_idle seulement).
def sel_canon(t):
    return 0.45 * (1 - step(t - 0.08, rise=0.1, over=0.2))


def sel_needle(t):
    return needle(sum(step(t - ti) for ti in (0.2, 0.3, 0.4)) - 3 * step(t - 0.62, rise=0.08, over=0.1))


sel_tracks = {(CAN, "position"): lambda t: le_long(sel_canon(t), -S_), (AIG["repos"], "rotation"): sel_needle,
              (SOUP, "position"): lambda t: valve_at(t, [0.6], 0.0)}
for i, gsp in enumerate(SPIRES):
    sel_tracks[(gsp, "position")] = (lambda t, f=(i + 0.5) / NSP: le_long(sel_canon(t) * f, -S_))
event_select = anim("event_select", 0.9, sel_tracks, fps=40, loop="once")

ANIMS = [item_idle, item_use, event_release, event_select]
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
# Réglages Display : ceux de la version d'avant (arc de Minecraft item/bow en main ; inventaire réduit et recentré).
_lo, _hi = P[:, :2].min(0), P[:, :2].max(0)
_c = (_lo + _hi) / 2
_gs = round(min(1.3, 15.0 / float(max(_hi - _lo))), 3)
GUI_S, GUI_T = 1.3, [5.98, -6.52, 0]
AFFICHAGE = objet.affichage("arc", gui={"scale": [GUI_S] * 3, "translation": GUI_T})
model = objet.modele(NOM, "arc", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import embarquer_sons  # noqa: E402
embarquer_sons(model, {"tir_vapeur": "sons/tir_vapeur.ogg"})   # son original synthétisé (tools/synthe.py), seul son du skin
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))

print("boîte :", P.min(0).round(2).tolist(), "->", P.max(0).round(2).tolist(),
      f"; gui {GUI_S} {GUI_T} (calculé : {_gs}, {[round(float((8 - _c[0]) * _gs), 2), round(float((8 - _c[1]) * _gs), 2), 0]})")
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
