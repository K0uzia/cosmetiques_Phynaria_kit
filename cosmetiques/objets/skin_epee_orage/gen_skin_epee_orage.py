"""Lame du tonnerre : skin d'objet (guide 14) pour toutes les épées du joueur, ensemble Orage (thème Éléments). Design original.
Écrit skin_epee_orage.png, skin_epee_orage_e.png et .build/skin_epee_orage_brut.bbmodel à côté de ce script.

Famille : ailes_orage v7 (aile de faucon en lames d'acier forgé), skin_hache_orage (fente d'éclair dans la joue),
skin_masse_orage, skin_lance_orage. Langage repris (.claude/styles/orage.md) :
- acier d'orage bleu-noir martelé ; fil poli clair, bande de revenu cuivre puis violet derrière le fil (couleurs de trempe,
  comme les rémiges des ailes) ; liseré d'or ; virgules d'or seulement sur le tambour de la garde ;
- âme de foudre au centre de la lame : la gorge est une fente en zigzag ouverte de part en part, et dans la fente court un
  vrai trait de foudre en géométrie (cœur opaque blanc à bord bleu + calque _e, gaine add_ en 4 sections) ;
- la foudre naît toujours d'un point : de la pointe (event_select, event_hit) ou de la gorge (fourches au repos).
Silhouette propre (reconnaissable sans la couleur, différente du givre droit à garde de cristaux et du sabre abyssal) :
lame droite et large à **dents d'éclair** (une dent sur chaque fil, décalées : la lame se lit en zigzag), pointe **en biseau**
(fil bas coupé en diagonale, comme le bout des primaires des ailes), garde en **deux ailes de faucon** de deux plumes balayées
vers la pointe (rachis en filet de foudre, liseré d'or), tambour d'or aux trois virgules au croisement, fusée de cuir bleu
nuit entre bagues d'or, pommeau d'acier à pointe de cristal d'orage (_e, comme la hache).
Vrai volume (F3, retour en jeu du 2026-11-08 14 h 22 : « c'est des couches » ; recette .claude/references/objets/volume-3d.md) :
lame à section hexagonale creusée, amincie du talon (1,56 px) à la pointe (0,54 px) : deux biseaux par fil (un cube incliné
à pente unique de 40° par tronçon de fil ≤ 2 px et par face), un plat incliné par face, gouttière en zigzag (parois, fond de
0,32 px) où la foudre est couchée ; fil, poli, cuivre et violet de trempe peints sur les faces des biseaux ; chaque face est
échantillonnée texel par texel dans le plan de l'épée et découpée par l'alpha (onglets, dents, pointe), recouvrement 0,08.
Garde : ailes biseautées de la même façon (1,1 px, liseré d'or sur le biseau, rachis de foudre en relief), croisillon
chanfreiné, tambour à 16 pans, collet d'or. Fusée et pommeau inchangés (validés : « le manche est bien »).
Ancienne gorge fendue à jour : remplacée par une gouttière (plus de plaques empilées par la tranche).
Repère (catégorie objets, Recette) : plan (a le long de l'épée, b en travers) posé sur la diagonale du bloc, pointe en haut à
droite vue de +Z comme l'image vanilla, centré dans le bloc. Longueur ~27,5 px (vanilla 22,6 ; épée de givre validée à 26,7).
Display vanilla item/handheld (tools/objet.py), gui 0,75. Une étape : `repos`.

Objet vivant (guide 14), sobre :
- item_idle (8 s) : la gaine de la gorge vacille (Molang, 9 Hz), petites fourches de la gorge sur le plat au hasard, arc en
  retour toutes les 3 à 8 s avec une petite décharge à la pointe.
- item_gui : gaine au repos, rien d'autre (fourches repliées).
- event_select (0,7 s) : la foudre frappe la pointe (deux formes), puis descend : la gorge s'allume de la pointe vers la garde,
  deux arcs courent sur les fils de la pointe à la garde.
- event_swing (0,35 s) : la gorge s'avive en vague de la garde vers la pointe, un arc file sur le fil haut (traînée du geste).
- event_hit (0,7 s) : décharge de la pointe, l'arc revient sur les deux fils vers la garde, trois arcs en retour, frisson de
  2,5° ; **le seul son** (embarqué, original : arc_epee).
Arcs des fils, décharges de la pointe et fourches **repliés à 1/10 sur leur pivot** au repos (invisibles dans l'inventaire et
animations coupées, sans dépendre d'une animation) et dépliés par `scale` ×10 dans les animations qui les montrent ; allumés par
ctrl_alpha. Chaque groupe replié n'est déplié que par une seule animation (les échelles des animations superposées se
multiplient) : un jeu d'arcs des fils et de décharges par événement, fourches et petite décharge pour item_idle seul.
Fonctions avancées : add_, ctrl_alpha, scale animé, calque _e, animations d'objet (item_idle, item_gui, event_select,
event_swing, event_hit), Molang (q.life_time), son embarqué. À juger en jeu : event_hit et son son (pas encore vérifiés par
le développeur), scale et ctrl_alpha sur un objet, arcs add_ de jour, taille en 1re personne.
"""
import base64, io, json, math, os, random, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image, ImageDraw

NOM = "skin_epee_orage"
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


# ------------------------------------------------------------------ dessin (plan a, b ; px)
A_G = 7.3                                         # centre de la garde
TIP = (26.2, 0.35)
U = [(7.9, 1.62), (9.7, 1.62), (10.75, 2.14), (10.98, 1.55), (16.0, 1.45), (22.4, 1.25), (25.1, 0.86), TIP]       # fil haut
L = [(7.9, -1.62), (11.9, -1.58), (12.95, -2.08), (13.18, -1.5), (17.5, -1.4), (22.9, -1.13), (24.6, -0.56), TIP]  # fil bas (biseau)
LAME = U + L[::-1][1:-1]
SLIT = [(8.7, 0.0), (11.0, 0.32), (13.5, -0.28), (16.0, 0.3), (18.4, -0.26), (20.7, 0.18), (22.3, -0.02)]           # gorge en éclair
G_HAUT = [(6.35, 0.8), (6.45, 1.9), (6.9, 3.0), (7.7, 4.1), (8.7, 4.9), (9.55, 5.3), (9.05, 4.35), (8.55, 3.8), (9.4, 3.6),
          (8.8, 2.65), (8.5, 1.7), (8.45, 0.8)]                                                                  # aile de garde, 2 plumes
RACHIS = [[(7.15, 1.0), (7.35, 2.4), (8.05, 3.7), (9.2, 4.95)], [(7.9, 1.0), (8.2, 2.2), (9.05, 3.45)]]


def miroir(pts):
    return [(a, -b) for a, b in pts]


G_BAS = miroir(G_HAUT)


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


def d_fil(P):
    return np.minimum(d_poly(P, U), d_poly(P, L))


def m_lame(P):
    return in_poly(P, LAME)


# ------------------------------------------------------------------ vrai volume (.claude/references/objets/volume-3d.md)
# Section de la lame : hexagone creusé. Deux biseaux par fil (plans inclinés, un cube tourné par tronçon de fil et par face),
# un plat par face (plaque inclinée qui suit l'amincissement), une gouttière creusée en zigzag (parois + fond) où court la
# foudre. Les couleurs du fil et de la trempe sont peintes SUR les faces des biseaux, pas sur des plaques empilées.
# Tout est construit dans le plan (a, b, z) de l'épée ; les tuiles sont échantillonnées face par face (texel -> point du plan),
# l'alpha découpe chaque face à la forme exacte (onglets aux coins, dents, pointe).
def unit(v):
    return v / np.linalg.norm(v)


Z_E = 0.10                        # demi-épaisseur au fil
DF = 16.0                         # texels par px sur les faces des volumes
TH = 0.3                          # épaisseur des cubes de biseau, de plat, de paroi
RECOUV = 0.08                     # recouvrement des faces voisines (un texel et demi) : pas de fente entre deux grilles de texels


def h_lame(a):
    """Demi-épaisseur du plat : 0,78 au talon (1,56 px) -> 0,27 à la pointe (0,54 px), amincissement linéaire."""
    return 0.78 + (0.27 - 0.78) * np.clip((np.asarray(a, float) - 8.0) / (26.2 - 8.0), 0, 1)


T_BIS = 0.85                      # pente unique des biseaux (40°) : tronçons voisins dans le même plan, onglets sans fente


def wb_lame(a):
    """Largeur du biseau (dans le plan) = (h - z_fil) / pente : 0,80 au talon -> 0,20 à la pointe."""
    return (h_lame(a) - Z_E) / T_BIS


H_G, WB_G, ZE_G = 0.55, 0.32, 0.12    # ailes de garde : 1,1 px au plat, biseau de 0,32, 0,24 au bord
H_G_FN = lambda a: np.full(np.shape(a), H_G, float)
WB_G_FN = lambda a: np.full(np.shape(a), WB_G, float)

# Gouttière : zigzag de la gorge, demi-largeur par sommet (pointue aux deux bouts)
GW = [0.12, 0.30, 0.32, 0.32, 0.30, 0.26, 0.10]
Z_FOND = 0.16                     # le fond (âme de la gouttière) va de -0,16 à +0,16


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


def _gouttiere():
    S = [np.array(p, float) for p in SLIT]
    nrm = []
    for i in range(len(S) - 1):
        d = unit(S[i + 1] - S[i])
        nrm.append(np.array((-d[1], d[0])))
    cotes = {}
    for sg in (1, -1):
        lignes = [(S[i] + sg * nrm[i] * GW[i], S[i + 1] + sg * nrm[i] * GW[i + 1]) for i in range(len(S) - 1)]
        pts = [lignes[0][0]]
        for i in range(len(lignes) - 1):
            (p1, p2), (p3, p4) = lignes[i], lignes[i + 1]
            d1, d2 = p2 - p1, p4 - p3
            den = d1[0] * d2[1] - d1[1] * d2[0]
            t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / den
            pts.append(p1 + d1 * t)
        pts.append(lignes[-1][1])
        cotes[sg] = pts
    poly = [tuple(p) for p in cotes[1]] + [tuple(p) for p in cotes[-1][::-1]]
    return cotes, poly


GOUT_COTES, GOUT = _gouttiere()


def in_gout(P):
    return in_poly(P, GOUT)


def d_gout(P):
    return d_poly(P, GOUT + [GOUT[0]])


class Piece:
    """Plaque biseautée : contour `poly`, fils `fils` (polylignes, sans la base cachée), profil h(a), wb(a), z au bord."""

    def __init__(self, nom, poly, fils, h, wb, ze, peint_biseau, peint_plat, peint_fil, trou=None):
        self.nom, self.poly, self.h, self.wb, self.ze = nom, poly, h, wb, ze
        self.segs = [s for f in fils for s in subdiv(f)]
        self.peint_biseau, self.peint_plat, self.peint_fil, self.trou = peint_biseau, peint_plat, peint_fil, trou
        pa = np.array(poly)
        self.box = (pa[:, 0].min() - 0.05, pa[:, 0].max() + 0.05, pa[:, 1].min() - 0.05, pa[:, 1].max() + 0.05)

    def dE(self, P):
        return d_stack(P, self.segs).min(0)

    def surf(self, P):
        """Demi-épaisseur de la surface au point (a, b)."""
        d, h, wb = self.dE(P), self.h(P[..., 0]), self.wb(P[..., 0])
        return np.where(d < wb, self.ze + (h - self.ze) * np.clip(d / wb, 0, 1), h)


SPECS = []          # cubes du volume : dict(groupe, nom, c, X, Y, s, faces) en coordonnées du plan
TILES = {}          # tuiles échantillonnées : nom -> (rgba, rgba_e)


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
    SPECS.append({"groupe": groupe, "nom": nom, "c": np.asarray(c, float), "X": X, "Y": Y, "s": s, "faces": faces})


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


def volume(pc, groupe):
    """Biseaux (deux par tronçon de fil) + plats inclinés de la pièce pc."""
    for idx, (p, q, v0, v1) in enumerate(pc.segs):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        if not in_poly(np.array([(p + q) / 2 + n * 0.05]), pc.poly)[0]:
            n = -n
        am = float((p[0] + q[0]) / 2)
        h, wb = float(pc.h(am)), float(pc.wb(am))
        al = math.atan2(h - pc.ze, wb)
        e0 = wb * 1.3 if v0 else 0.04
        e1 = wb * 1.3 if v1 else 0.04
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        sy = (wb + 0.08) / math.cos(al)
        for sg in (1, -1):
            Y = np.array((n[0] * math.cos(al), n[1] * math.cos(al), sg * math.sin(al)))
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0], mid[1], sg * pc.ze)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(P, idx=idx):
                P2 = P[..., :2]
                D = d_stack(P2, pc.segs)
                dE = D.min(0)
                m = in_poly(P2, pc.poly) & (D[idx] <= dE + RECOUV) & (dE < pc.wb(P2[..., 0]) + 0.03)
                col, em = pc.peint_biseau(P2, dE)
                return col, em, m

            def fil(P, idx=idx, n=n):
                P2 = P[..., :2] + n * 0.06
                D = d_stack(P2, pc.segs)
                m = in_poly(P2, pc.poly) & (D[idx] <= D.min(0) + RECOUV)
                col, em = pc.peint_fil(P2)
                return col, em, m

            spec(groupe, f"{pc.nom}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil})
    # plats : une plaque par face, inclinée pour suivre l'amincissement (dessus à z = ±h(a))
    a0, a1, b0, b1 = pc.box
    sl = float((pc.h(a1) - pc.h(a0)) / (a1 - a0))
    ac, bc = (a0 + a1) / 2, (b0 + b1) / 2
    for sg in (1, -1):
        X = unit(np.array((1.0, 0.0, sg * sl)))
        Y = np.array((0.0, float(sg), 0.0))
        Z = np.cross(X, Y)
        c = np.array((ac, bc, sg * float(pc.h(ac)))) - Z * (TH / 2)

        def plat(P):
            P2 = P[..., :2]
            dE = pc.dE(P2)
            m = in_poly(P2, pc.poly) & (dE >= pc.wb(P2[..., 0]) - 0.03)
            if pc.trou is not None:
                m &= ~pc.trou(P2)
            col, em = pc.peint_plat(P2, dE)
            return col, em, m

        spec(groupe, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, ((a1 - a0) * math.sqrt(1 + sl * sl), b1 - b0, TH), {"south": plat})


# --- peintures (couleurs portées par les faces des volumes)
def peint_biseau_lame(P, dE):
    wb = wb_lame(P[..., 0])
    f = dE / wb
    nz = cellules(P, 2.2, 1.0)[..., None]
    col = lerp(METAL[3], METAL[2], np.clip((f[..., None] - 0.78) / 0.15, 0, 1)) + nz * 10
    col = np.where((f < 0.36)[..., None], lerp(METAL[4], METAL[3], np.clip((f[..., None] - 0.14) / 0.22, 0, 1)) + nz * 6, col)
    cu = (f >= 0.36) & (f < 0.57)
    vi = (f >= 0.57) & (f < 0.78)
    col[cu] = lerp(col[cu], CUIVRE, 0.85)
    col[vi] = lerp(col[vi], VIOLET, 0.72)
    col[f >= 0.93] = METAL[0]                                   # arête du plat : trait d'ombre net
    em = np.zeros(col.shape, np.float32)
    col[f < 0.14] = (236, 244, 255)
    em[f < 0.16] = (110, 150, 235)
    return col, em


def peint_fil_lame(P):
    col = np.zeros(P.shape[:-1] + (3,), np.float32) + np.array((236, 244, 255), np.float32)
    em = np.zeros_like(col) + np.array((110, 150, 235), np.float32)
    return col, em


def peint_plat_lame(P, dE):
    wb = wb_lame(P[..., 0])
    nz = cellules(P, 1.6, 2.0)[..., None]
    col = lerp(METAL[2], METAL[1], np.clip((dE[..., None] - wb[..., None] - 0.1) / 0.5, 0, 1) * 0.6) + nz * 16
    col[dE < wb + 0.04] = METAL[0]
    em = np.zeros(col.shape, np.float32)
    dg = d_gout(P)
    levre = dg < 0.07
    col[levre] = (190, 208, 255)
    em[levre] = (60, 100, 210)
    col[(dg >= 0.07) & (dg < 0.13)] = METAL[0]
    orl = (dg >= 0.19) & (dg < 0.27) & (dE > wb + 0.1)
    col[orl] = OR[2]
    col[orl & (dg < 0.22)] = OR[3]
    return col, em


def peint_biseau_garde(P, dE):
    f = dE / WB_G
    nz = cellules(P, 2.0, 3.0)[..., None]
    col = lerp(METAL[3], METAL[2], 0.4) + nz * 10 + np.zeros(P.shape[:-1] + (3,), np.float32)
    col[f < 0.62] = OR[2]
    col[f < 0.22] = OR[3]
    cu = (f >= 0.62) & (f < 0.85)
    col[cu] = lerp(col[cu], CUIVRE, 0.7)
    col[f >= 0.93] = METAL[0]
    return col, np.zeros(col.shape, np.float32)


def peint_fil_garde(P):
    col = np.zeros(P.shape[:-1] + (3,), np.float32) + OR[3]
    return col, np.zeros_like(col)


def peint_plat_garde(P, dE):
    nz = cellules(P, 1.8, 4.0)[..., None]
    col = lerp(METAL[2], METAL[1], 0.3) + nz * 16 + np.zeros(P.shape[:-1] + (3,), np.float32)
    col[dE < WB_G + 0.04] = METAL[0]
    return col, np.zeros(col.shape, np.float32)


LAME_P = Piece("lame", LAME, [U, L], h_lame, wb_lame, Z_E, peint_biseau_lame, peint_plat_lame, peint_fil_lame, trou=in_gout)
GARDES = [Piece(f"aile_{nm}", poly, [poly], H_G_FN, WB_G_FN, ZE_G, peint_biseau_garde, peint_plat_garde, peint_fil_garde)
          for nm, poly in (("h", G_HAUT), ("b", G_BAS))]


def gouttiere(groupe):
    """Fond (âme de 0,32 px où repose la foudre) + parois verticales le long des deux bords, sur chaque face."""
    pa = np.array(GOUT)
    box = (pa[:, 0].min() - 0.15, pa[:, 0].max() + 0.15, pa[:, 1].min() - 0.15, pa[:, 1].max() + 0.15)

    def fond(P):
        P2 = P[..., :2]
        m = in_gout(P2) | (d_gout(P2) < 0.1)
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + np.array((16, 18, 34), np.float32) + cellules(P2, 3.0, 5.0)[..., None] * 6
        em = np.zeros_like(col) + np.array((14, 22, 70), np.float32)
        return col, em, m

    a0, a1, b0, b1 = box
    spec(groupe, "fond", ((a0 + a1) / 2, (b0 + b1) / 2, 0.0), (1, 0, 0), (0, 1, 0), (a1 - a0, b1 - b0, 2 * Z_FOND),
         {"south": fond, "north": fond})
    centre = np.array(SLIT).mean(axis=0)
    murs = []
    for sg, pts in GOUT_COTES.items():
        for i in range(len(pts) - 1):
            murs.append((pts[i], pts[i + 1]))
    murs.append((GOUT_COTES[1][0], GOUT_COTES[-1][0]))
    murs.append((GOUT_COTES[1][-1], GOUT_COTES[-1][-1]))
    for j, (p, q) in enumerate(murs):
        p, q = np.asarray(p, float), np.asarray(q, float)
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        mid = (p + q) / 2
        # n doit pointer hors de la gouttière (le mur est derrière sa face visible)
        inside_pt = mid - n * 0.05
        if not (in_gout(np.array([inside_pt]))[0] or d_gout(np.array([inside_pt]))[0] < 1e-3):
            n = -n
        back = [p + n * TH, q + n * TH, mid + n * TH]
        top = min(float(LAME_P.surf(np.array([x]))[0]) for x in back + [p, q]) - 0.03
        z0 = Z_FOND - 0.04
        Ln = float(np.linalg.norm(q - p))
        for sg in (1, -1):
            zc = sg * (z0 + top) / 2
            X = np.array((d[0], d[1], 0.0))
            Y = np.array((0.0, 0.0, 1.0))
            Z = np.cross(X, Y)
            face = "south" if Z[:2] @ n < 0 else "north"          # face tournée vers la gouttière

            def paroi(P):
                P2 = P[..., :2]
                dz = LAME_P.h(P2[..., 0]) - np.abs(P[..., 2])
                col = lerp(METAL[1], METAL[0], np.clip((dz[..., None] - 0.1) / 0.3, 0, 1)) + np.zeros(P.shape[:-1] + (3,), np.float32)
                em = np.zeros_like(col)
                lv = dz < 0.1
                col[lv] = (190, 208, 255)
                em[lv] = (60, 100, 210)
                return col, em, np.ones(P.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zc)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec(groupe, f"paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


def conception():
    SPECS.clear()
    TILES.clear()
    volume(LAME_P, "lame")
    gouttiere("lame")
    for pc in GARDES:
        volume(pc, "garde")



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


# ------------------------------------------------------------------ atlas
UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    core, core_e = t_core()
    cri, cri_e = t_cristal()
    conception()
    items = [(n, im, ime) for n, (im, ime) in TILES.items()]
    items += [("medaillon", medaillon(), None), ("cuir", t_cuir(), None), ("core", core, core_e), ("cristal", cri, cri_e),
              ("halo", t_halo(), None), ("crk", t_crk(), None),
              ("metal", t_unie(64, 12, METAL[3], METAL[1], 2, bords=METAL[4]), None),
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
    """Plan (a, b, z) de l'épée -> monde : rotation theta autour de Z, puis translation P0."""
    th, P0 = 0.0, V(0, 0, 0)

    @classmethod
    def p(cls, a, b, z=0.0):
        c, s = math.cos(cls.th), math.sin(cls.th)
        return cls.P0 + V(c * a - s * b, s * a + c * b, z)

    @classmethod
    def v(cls, a, b, z=0.0):
        c, s = math.cos(cls.th), math.sin(cls.th)
        return V(c * a - s * b, s * a + c * b, z)


W_, Wv = Repere.p, Repere.v


def group(name, origin, parent=None):
    assert name not in groups, name
    assert len(name.split("#")[0]) <= 64
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent}
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


def plaque(g, name, box, tile, th):
    """Plaque du plan (a, b) couvrant box = (a0, a1, b0, b1), découpée par l'alpha de la tuile ; tranches transparentes."""
    a0, a1, b0, b1 = box
    u0, v0, u1, v1 = UV[tile]
    boite(g, name, W_((a0 + a1) / 2, (b0 + b1) / 2), Wv(1, 0), Wv(0, 1), a1 - a0, b1 - b0, th,
          {"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def strip(tile, caps=True):
    u0, v0, u1, v1 = UV[tile]
    lg = [u0, v0, u1, v1]
    end = [u0 + 1, v0 + 1, u0 + 3, v0 + 3] if caps else CLEAR
    return {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end}


def barre(g, name, a0, a1, r, tile, b=0.0, octo=True, caps=True):
    """Barre le long de l'épée (axe a), section r ; octogonale (deux cubes à 45°)."""
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
    ref = V(0, 0, 1) if abs(X[2]) < 0.9 else V(1, 0, 0)
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


def ame(g, name, masque, box, demi, pas=0.3, inset=0.12, tile="sombre"):
    """Âme pleine : tranches de `pas` px le long de b, découpées en segments le long de a là où le masque (érodé de inset)
    couvre toute la tranche ; épaisseur 2 × demi. Donne les côtés (les plaques ont des tranches transparentes)."""
    a0, a1, b0, b1 = box
    da = 0.05
    aa = np.arange(a0, a1, da) + da / 2
    n = 0
    b = b0
    while b + pas <= b1 + 1e-6:
        ok = np.ones(len(aa), bool)
        for bb in np.linspace(b, b + pas, 4):
            for off in ((0, 0), (inset, 0), (-inset, 0), (0, inset), (0, -inset)):
                P = np.stack([aa + off[0], np.full_like(aa, bb + off[1])], -1)
                ok &= masque(P)
        i = 0
        while i < len(aa):
            if ok[i]:
                j = i
                while j + 1 < len(aa) and ok[j + 1]:
                    j += 1
                if (j - i + 1) * da >= 0.25:
                    s0, s1 = aa[i] - da / 2, aa[j] + da / 2
                    boite(g, f"{name}{n}", W_((s0 + s1) / 2, b + pas / 2), Wv(1, 0), Wv(0, 1), s1 - s0, pas + 0.002, 2 * demi,
                          strip(tile))
                    n += 1
                i = j + 1
            else:
                i += 1
        b += pas
    return n


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


def exterieur(pts, dist):
    """Polyligne décalée de dist vers l'extérieur de la lame."""
    out = []
    P = [np.array(p, float) for p in pts]
    for i, p in enumerate(P):
        d = unit(P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)])
        n = np.array((-d[1], d[0]))
        if m_lame(np.array([p + n * 0.08]))[0]:
            n = -n
        out.append(tuple(p + n * dist))
    return out


def bone_node(name):
    g = groups[name]
    return {"name": name.split("#")[0], "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
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


N_FIL = 6
NG = 4


def build(theta, P0):
    elements.clear()
    groups.clear()
    _rc[0] = 0
    Repere.th, Repere.P0 = theta, np.asarray(P0, float)
    out = {}
    racine = group(objet.etape("repos", "epee"), W_(4.0, 0))
    epee = group("epee", W_(4.0, 0), racine)
    # --- fusée et pommeau
    poignee = group("poignee", W_(4.0, 0), epee)
    barre(poignee, "pommeau", -0.2, 1.2, 0.9, "metal")
    barre(poignee, "pom_bague", 0.25, 0.62, 0.98, "or")
    barre(poignee, "pom_cri", -1.1, -0.15, 0.46, "cristal")
    barre(poignee, "pom_cri2", -1.6, -1.05, 0.24, "cristal", octo=False)
    barre(poignee, "bague1", 1.15, 1.6, 0.76, "or")
    barre(poignee, "fusee", 1.55, 6.5, 0.63, "cuir")
    barre(poignee, "bague2", 6.45, 6.85, 0.74, "or")
    # --- garde : croisillon chanfreiné, deux ailes de faucon biseautées, tambour à 16 pans, collet d'or
    garde = group("garde", W_(A_G, 0), epee)
    boite(garde, "croisillon", W_(A_G, 0), Wv(1, 0), Wv(0, 1), 2.2, 3.3, 1.8, strip("metal"))
    Xq = unit(Wv(1, 0) * math.cos(math.pi / 4) + V(0, 0, 1) * math.sin(math.pi / 4))
    boite(garde, "croisillon_ch", W_(A_G, 0), Xq, Wv(0, 1), 1.45, 3.24, 1.45, strip("sombre"))
    boite(garde, "collet", W_(8.55, 0), Wv(1, 0), Wv(0, 1), 0.34, 3.6, 1.7, strip("or"))
    lame = group("lame", W_(8.0, 0), epee)
    for sp in SPECS:
        u_ = {}
        for f in ("north", "south", "east", "west", "up", "down"):
            if f in sp["faces"]:
                u0, v0, u1, v1 = UV[sp["faces"][f]]
                u_[f] = [u0, v0, u1, v1]
            else:
                u_[f] = CLEAR
        g = garde if sp["groupe"] == "garde" else lame
        boite(g, sp["nom"], W_(*sp["c"]), Wv(*sp["X"]), Wv(*sp["Y"]), *sp["s"], u_)
    for pc, rs in zip(GARDES, (RACHIS, [miroir(r) for r in RACHIS])):
        for sg in (1, -1):
            for j, r in enumerate(rs):
                trait(garde, f"rachis_{pc.nom}{'pm'[sg < 0]}{j}", [W_(x, y, sg * (H_G + 0.01)) for x, y in r], 0.2, 0.16, "core")
    R_I = 1.1
    for k in range(4):
        th = math.radians(22.5 * k)
        boite(garde, f"tambour{k}", W_(A_G, 0), Wv(math.cos(th), math.sin(th)), Wv(-math.sin(th), math.cos(th)), 2 * R_I, 2 * R_I, 2.0,
              {"north": CLEAR, "south": CLEAR, "east": UV["or"], "west": UV["or"], "up": UV["or"], "down": UV["or"]})
    u0, v0, u1, v1 = UV["medaillon"]
    MR = R_I / math.cos(math.radians(11.25)) + 0.01
    for sg in (1, -1):
        fc = {"south": [u0, v0, u1, v1]} if sg > 0 else {"north": [u1, v0, u0, v1]}
        boite(garde, f"medaillon{'pm'[sg < 0]}", W_(A_G, 0, sg * 0.88), Wv(1, 0), Wv(0, 1), 2 * MR, 2 * MR, 0.3,
              {**{f: CLEAR for f in ("north", "south", "east", "west", "up", "down")}, **fc})
    # --- foudre de la gorge : cœur opaque + _e couché au fond de la gouttière, gaine add_ en NG sections
    foudre = group("foudre", W_(*SLIT[0]), lame)
    pts2 = zigzag(SLIT, 4 * NG, 0.06, 17)
    pts = [W_(*p) for p in pts2]
    trait(foudre, "eclair", pts, 0.38, 0.26, "core")
    out["gaines"] = []
    per = (len(pts) - 1) // NG
    for k in range(NG):
        gg = group(f"add_gaine_{k}", tuple(pts[k * per]), foudre)
        ctrl(gg)
        for i in range(k * per, (k + 1) * per):
            am = (pts2[i][0] + pts2[i + 1][0]) / 2
            seg(gg, f"gaine{i}", pts[i], pts[i + 1], min(0.82, 2 * float(h_lame(am)) - 0.14), "halo", ov=0.04, roll=0.0)
        out["gaines"].append(gg)
    # fourches de la gorge sur le plat (deux jeux, faces avant et arrière) — item_idle seulement
    out["fourches"] = []
    on_slit = le_long(SLIT)
    for v in range(2):
        fg = group(f"add_fourche_{'ab'[v]}", W_(*SLIT[0]), foudre)
        ctrl(fg)
        rng = random.Random(40 + v)
        for k in range(4):
            t = (k + 0.25 + 0.5 * rng.random()) / 4
            p = on_slit(t)
            p2 = on_slit(min(1, t + 0.02))
            d = unit(p2 - p)
            side = 1 if (k + v) % 2 == 0 else -1
            ang = math.radians(rng.uniform(40, 65)) * side
            dirn = np.array((d[0] * math.cos(ang) - d[1] * math.sin(ang), d[0] * math.sin(ang) + d[1] * math.cos(ang)))
            q = p + dirn * rng.uniform(0.6, 0.85)
            for zs in (1, -1):
                zz = zigzag([p + dirn * 0.4, q], 3, 0.12, 70 + 10 * v + k)
                trait(fg, f"f{k}{'pm'[zs < 0]}", [W_(x, y, zs * (float(LAME_P.surf(np.array([(x, y)]))[0]) + 0.07)) for x, y, _ in zz],
                      0.17, 0.13, "crk")
        replier(fg)
        out["fourches"].append(fg)
    # --- arcs des fils : N_FIL tronçons par fil, de la garde à la pointe. Un jeu par événement (s = select, w = swing,
    # c = hit) : chaque groupe n'est déplié que par une seule animation (les échelles des animations superposées se
    # multiplient, un groupe déplié par swing et hit serait à ×100 au coup qui touche). Même tracé, zigzag tiré à part par jeu
    # (des cubes identiques seraient « strictement superposés »).
    arcs = group("arcs_fil", W_(*TIP), lame)
    out["fil"] = {}
    for ev, cotes in (("s", "hb"), ("w", "h"), ("c", "hb")):
        out["fil"][ev] = []
        for side, poly in (("h", [(8.6, 1.62)] + U[1:]), ("b", [(8.6, -1.62)] + L[1:])):
            if side not in cotes:
                continue
            at = le_long(exterieur(poly, 0.17))
            for k in range(N_FIL):
                t0, t1 = k / N_FIL, (k + 1) / N_FIL
                sous = [tuple(at(t)) for t in np.linspace(t0, t1, 4)]
                g = group(f"add_fil_{ev}{side}{k}", W_(*sous[0]), arcs)
                ctrl(g)
                zz = zigzag(sous, 4, 0.14, 100 + 7 * k + (31 if side == "b" else 0) + 500 * "swc".index(ev), zj=0.07)
                trait(g, "a", [W_(*p) for p in zz], 0.23, 0.19, "crk")
                replier(g)
                out["fil"][ev].append((g, side, k))
    # --- décharges de la pointe : deux formes, un jeu pour event_select (s) et un pour event_hit (c), + une pour item_idle
    out["pointe"] = {}
    for nm, seed, angs, ev in (("a", 5, (-38, 4, 41), "s"), ("b", 9, (-22, 28, 63), "s"),
                               ("a", 5, (-38, 4, 41), "c"), ("b", 9, (-22, 28, 63), "c"), ("r", 13, (-30, 18), "")):
        g = group(f"add_pointe_{ev}{nm}", W_(*TIP), arcs)
        ctrl(g)
        rng = random.Random(seed)
        base = math.atan2(0.35 - (-0.56), 26.2 - 24.6) * 0.3       # un peu vers le fil haut (la pointe est en biseau)
        for j, an in enumerate(angs):
            a = base + math.radians(an)
            Ln = rng.uniform(1.0, 1.7) * (0.75 if nm == "r" else 1.0)
            q = np.array(TIP) + np.array((math.cos(a), math.sin(a))) * Ln
            zz = zigzag([TIP, tuple(q)], 3, 0.2, seed * 10 + j + (500 if ev == "c" else 0))
            trait(g, f"p{j}", [W_(*p) for p in zz], 0.24, 0.14, "crk")
        replier(g)
        out["pointe"][ev + nm] = g
    out["racine"], out["epee"] = racine, epee
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
THETA = math.radians(45)          # le long de la diagonale du bloc, pointe en haut à droite (vue de +Z), comme la vanilla
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


FILS_S, FILS_W, FILS_C = F["fil"]["s"], F["fil"]["w"], F["fil"]["c"]
FILS = FILS_S + FILS_W + FILS_C
GAINES = F["gaines"]
PA_S, PB_S, PA_C, PB_C, PR = (F["pointe"][k] for k in ("sa", "sb", "ca", "cb", "r"))

# item_idle : la gorge vit (gaine qui vacille, fourches), petite décharge de la pointe aux arcs en retour ; fils éteints.
idle = anim("item_idle", 8.0)
for k, g in enumerate(GAINES):
    piste_ctrl(idle, g, [kf("position", 0, gaine_idle(k))])
for v, fg in enumerate(F["fourches"]):
    deplier(idle, fg)
    piste_ctrl(idle, fg, [kf("position", 0, fourche_idle(v))])
deplier(idle, PR)
piste_ctrl(idle, PR, [kf("position", 0, chk(restrike(P_RS, PR_RS, 0.37) + "v.r-1"))])
for g, side, k in FILS:
    piste_ctrl(idle, g, [kf("position", 0, -1)])
for g in (PA_S, PB_S, PA_C, PB_C):
    piste_ctrl(idle, g, [kf("position", 0, -1)])

# item_gui : inventaire calme.
gui = anim("item_gui", 4.0)
for g in GAINES:
    piste_ctrl(gui, g, [kf("position", 0, -0.3)])
for g in [x[0] for x in FILS] + [PA_S, PB_S, PA_C, PB_C, PR] + F["fourches"]:
    piste_ctrl(gui, g, [kf("position", 0, -1)])

# event_select (0,7 s) : la foudre frappe la pointe, puis descend la gorge et les fils jusqu'à la garde.
L_SEL = 0.7
sel = anim("event_select", L_SEL, "once")
for g in (PA_S, PB_S):
    deplier(sel, g)
piste_ctrl(sel, PA_S, onoff([(0.0, 0.07), (0.15, 0.19)], L_SEL))
piste_ctrl(sel, PB_S, onoff([(0.08, 0.13)], L_SEL))
for k, g in enumerate(GAINES):
    t0 = 0.1 + 0.05 * (NG - 1 - k)
    piste_ctrl(sel, g, [kf("position", t, -0.6 * (1 - sm(t, 0.0, 0.1)) * (t < t0) + (1.0 * bump(t, t0, t0 + 0.04, t0 + 0.12, t0 + 0.4)
                                                                                     - 0.38 * sm(t, t0 + 0.12, t0 + 0.4)) * (t >= t0))
                         for t in np.round(np.linspace(0, L_SEL, 29), 4)])
for g, side, k in FILS_S:
    deplier(sel, g)
    t0 = 0.13 + 0.035 * (N_FIL - 1 - k) + (0.02 if side == "b" else 0)
    piste_ctrl(sel, g, onoff([(t0, t0 + 0.07)], L_SEL))

# event_swing (0,35 s) : la gorge s'avive en vague garde -> pointe, un arc file sur le fil haut.
L_SW = 0.35
sw = anim("event_swing", L_SW, "once")
for k, g in enumerate(GAINES):
    t0 = 0.02 * k
    piste_ctrl(sw, g, [kf("position", t, 0.6 * bump(t, t0, t0 + 0.04, t0 + 0.1, t0 + 0.3)) for t in np.round(np.linspace(0, L_SW, 15), 4)])
for g, side, k in FILS_W:
    deplier(sw, g)
    t0 = 0.04 + 0.022 * k
    piste_ctrl(sw, g, onoff([(t0, t0 + 0.06)], L_SW))

# event_hit (0,7 s) : décharge de la pointe, l'arc revient sur les deux fils vers la garde, trois arcs en retour.
L_HIT = 0.7
hit = anim("event_hit", L_HIT, "once")
RESTRIKES = [(0.24, 0.29), (0.34, 0.38), (0.44, 0.47)]
for g in (PA_C, PB_C):
    deplier(hit, g)
piste_ctrl(hit, PA_C, onoff([(0.0, 0.09), RESTRIKES[1]], L_HIT))
piste_ctrl(hit, PB_C, onoff([(0.02, 0.07), RESTRIKES[0], RESTRIKES[2]], L_HIT))
for g, side, k in FILS_C:
    deplier(hit, g)
    t0 = 0.04 + 0.03 * (N_FIL - 1 - k)
    iv = [(t0, t0 + 0.09)]
    for j, (a, b) in enumerate(RESTRIKES):
        if j == 0 or (j == 1 and k % 2 == 1) or (j == 2 and k >= N_FIL - 3):
            iv.append((a, b))
    piste_ctrl(hit, g, onoff(iv, L_HIT))
for k, g in enumerate(GAINES):
    piste_ctrl(hit, g, [kf("position", t, 1.2 * sm(t, 0.0, 0.02) * (1 - sm(t, 0.08, 0.6))
                         + 0.4 * sum(bump(t, a - 0.01, a, b, b + 0.02) for a, b in RESTRIKES)) for t in np.round(np.linspace(0, L_HIT, 36), 4)])
piste(hit, F["epee"], [kf("rotation", t, 0, 0, 2.5 * math.sin(TAU * t / 0.07) * (1 - sm(t, 0.0, 0.28))) for t in np.round(np.linspace(0, 0.3, 19), 4)]
      + [kf("rotation", L_HIT, 0, 0, 0)])

ANIMS = [idle, gui, sel, sw, hit]

# ------------------------------------------------------------------ écriture
assert 80 <= len(elements) <= 1500, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
GUI = float(os.environ.get("GUI", "0.75"))
AFFICHAGE = objet.affichage("epee", gui={"scale": [GUI] * 3})
model = objet.modele(NOM, "epee", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, embarquer_sons, cle_son
limiter_sons(model)
embarquer_sons(model, {"arc_epee": "sons/arc_epee.ogg"})
# Un seul son, au coup qui touche (event_hit) : tools/sons.py ne connaît pas encore les événements d'objet, on le pose après.
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "arc_epee")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur sur la diagonale {LONGUEUR:.1f} px ; largeur {LARGEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)}")
