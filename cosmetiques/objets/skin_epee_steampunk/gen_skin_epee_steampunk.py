"""Lame de pression : skin d'objet (guide 14) pour toutes les épées du joueur, ensemble Steampunk (thème Mécanique). Design original.
Écrit skin_epee_steampunk.png, skin_epee_steampunk_e.png et .build/skin_epee_steampunk_brut.bbmodel à côté de ce script.

Idée (l'épée d'un chaudronnier : chaque pièce sert au circuit de vapeur, .claude/styles/steampunk.md) :
- pommeau = petite chaudière de cuivre rivetée, porte de foyer à fentes rougeoyantes sur les deux plats, soupape de laiton au bout ;
- la vapeur monte par un tuyau de cuivre qui fait **garde de main** (côté -b) jusqu'à la garde, avec un volant de vanne sur +Z ;
- garde = **roue dentée de laiton** dans le plan de la lame (lue comme un engrenage dans la case), manomètre ambre au moyeu sur les
  deux faces (aiguille dans son groupe), dents seulement là où ni la lame, ni la poignée, ni les tuyaux ne passent ;
- quillon côté +b = tuyau de cuivre terminé par une **buse** évasée : c'est par là que la pression se décharge ;
- lame droite à deux tranchants en acier bruni, fil poli clair (pas de lumière sur le fil : rien ne l'explique) ; dans la gouttière
  creusée est serti un **tube de niveau** de verre ambré (le niveau d'eau d'une chaudière), entre deux raccords de laiton, graduations
  gravées à côté, filets de laiton aux lèvres.
Lumière _e seulement sur trois sources logiques : cadran ambre, tube de niveau, fentes du foyer.

Vrai volume (recette .claude/references/objets/volume-3d.md, prototype skin_epee_orage validé en jeu) : lame hexagonale creusée,
amincie 1,56 -> 0,54 px, biseaux à pente unique 40° (un cube incliné par tronçon de fil <= 2 px et par face), plats inclinés, gouttière
creusée (parois + fond), couleurs portées par les faces échantillonnées texel par texel et découpées par l'alpha, recouvrement 0,08.
Pièces rondes en tours de pans (skin_masse_orage, skin_epee_abyssal) : chaudière, poignée de cuir cousu, tuyaux, buse, bagues,
lunette du manomètre, flanc de la roue ; faces de la roue et cadrans en plaques découpées par l'alpha.

Repère (catégorie objets, Recette) : plan (a le long de l'épée, b en travers, z = normale vue de l'inventaire) posé sur la diagonale
du bloc, pointe en haut à droite vue de +Z comme l'image vanilla, centré ; Display vanilla item/handheld, gui ramené à la case.
Une étape : groupe racine `repos`.

Objet vivant (guide 14), sobre :
- item_idle (24 s) : la pression monte par crans (aiguille : échelon, dépassement, rappel), le tube de niveau s'avive avec elle
  (ctrl_lumiere), la soupape tremble, puis décharge : bouffée de white_smoke à la buse (ctrl_emit), l'aiguille retombe ; deux cycles ;
  aucun son ;
- event_select (0,8 s) : on ouvre la vanne (volant d'un quart de tour par crans), l'aiguille fait son tour d'essai, le tube s'allume ;
- event_swing (0,35 s) : l'aiguille perd un cran et remonte, le tube vacille ;
- event_hit (0,9 s) : décharge : jet de vapeur modélisé qui jaillit de la buse et **monte** (trans_jet, seul dépliage par scale,
  fondu ctrl_alpha), white_smoke (ctrl_emit +5), volant d'un quart de tour, aiguille qui chute de trois crans puis remonte, frisson ;
  **le seul son** du skin (block.fire.extinguish à 0,04 s ; une clé à 0,0 s est muette au premier coup).
Aucun son sur event_use_start ni event_enter_* (il n'y en a pas). Jet caché au repos : géométrie F_GEO / KJ dans la buse.

Fonctions avancées : calque _e, trans_jet, ctrl_alpha, ctrl_lumiere, emit_mc_white_smoke + ctrl_emit, scale animé, animations
d'objet. Non simulés par l'aperçu : animations en main, particules, ctrl_emit, ctrl_lumiere, son. À juger en jeu : event_hit et son
son (pas encore vérifiés par le développeur), jet de vapeur sur un objet, lecture de la roue dans la case.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

AVEC_E = True
NOM = "skin_epee_steampunk"
TEX = 512
TAU = 2 * math.pi
DF = 16.0                       # texels par px sur les faces des volumes
DENS = 16.0                     # texels par px sur les pans des tours
TH = 0.3                        # épaisseur des cubes (biseaux, plats, parois, pans)
RECOUV = 0.08                   # recouvrement des faces voisines
OVL, OVW = 0.04, 0.03           # recouvrement des pans (en long, en travers)
KJ, F_GEO = 16.0, 2.0           # jet caché : géométrie F_GEO / KJ, clés scale <= KJ / F_GEO


def A(c):
    return np.array(c, np.float32)


# Palette du set (.claude/styles/steampunk.md ; métal propre, brossé ±5 % au plus)
BRASS = dict(hi=A((236, 196, 112)), base=A((190, 142, 64)), low=A((112, 76, 32)))
COPPER = dict(hi=A((232, 150, 96)), base=A((176, 92, 52)), low=A((98, 46, 26)))
STEEL = dict(hi=A((136, 140, 150)), base=A((78, 82, 92)), low=A((38, 40, 48)))
LEATHER = dict(hi=A((150, 96, 60)), base=A((104, 62, 36)), low=A((60, 34, 20)))
FIL = A((220, 224, 232))
POLI = A((176, 180, 190))
AMBRE = A((255, 210, 120))
AMBRE_B = A((220, 150, 50))
VAPEUR = A((250, 250, 248))
VAPEUR_B = A((220, 224, 228))


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


def unit(v):
    return v / np.linalg.norm(v)


def V(*a):
    return np.array(a, float)


# ------------------------------------------------------------------ dessin (plan a, b ; px)
A_G = 7.6                                   # centre de la roue de garde
R_RIM, R_DENT, GZ, TZ = 1.9, 2.45, 0.9, 0.66
TIP = (25.6, 0.0)
U = [(8.3, 1.72), (13.0, 1.74), (18.0, 1.6), (21.5, 1.32), (23.8, 0.92), (24.9, 0.48), TIP]
L = [(a, -b) for a, b in U[:-1]] + [TIP]
LAME = U + L[::-1][1:-1]
SLIT = [(9.95, 0.0), (10.6, 0.0), (13.0, 0.0), (16.0, 0.0), (19.3, 0.0), (19.95, 0.0)]
GW = [0.10, 0.37, 0.39, 0.39, 0.37, 0.10]
Z_FOND = 0.16
TUBE = (10.75, 19.05, 0.22)                 # tube de niveau : a0, a1, rayon
Q_DIR = unit(np.array((0.3, 1.0)))          # quillon (+b) : tuyau vers la buse
Q_S, Q_E = 1.6, 4.1                         # le long du quillon depuis le centre de la roue
BOW = [(A_G - 0.45, -1.55), (6.6, -2.75), (5.4, -3.25), (3.8, -3.35), (2.3, -3.05), (1.15, -2.15), (0.55, -1.05), (0.35, -0.5)]
VOLANT = (4.6, -3.3)


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


Z_E = 0.10


def h_lame(a):
    """Demi-épaisseur du plat : 0,78 au talon (1,56 px) -> 0,27 à la pointe (0,54 px)."""
    return 0.78 + (0.27 - 0.78) * np.clip((np.asarray(a, float) - 8.3) / (TIP[0] - 8.3), 0, 1)


T_BIS = 0.85                                # pente unique des biseaux (40°)


def wb_lame(a):
    return (h_lame(a) - Z_E) / T_BIS


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


def brosse(P, seed=0.0):
    """Brossé fin le long de a (±4 %)."""
    v = np.sin(P[..., 1] * 61.0 + seed) * 0.5 + np.sin(P[..., 1] * 23.0 + P[..., 0] * 0.7 + seed * 3) * 0.5
    return v * 0.04


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
            if abs(den) < 1e-9:
                pts.append(p2)
                continue
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
        d, h, wb = self.dE(P), self.h(P[..., 0]), self.wb(P[..., 0])
        return np.where(d < wb, self.ze + (h - self.ze) * np.clip(d / wb, 0, 1), h)


SPECS = []
TILES = {}          # nom -> (rgba, rgba_e | None)
TRANS = set()       # tuiles semi-transparentes (groupes trans_ seulement)


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


def _rgba(col, mask, em=None):
    H, W = mask.shape
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    out[..., 3] = mask * 255
    out[~mask, :3] = 0
    e = None
    if em is not None:
        m = mask & (em.max(axis=2) > 0)
        if m.any():
            e = np.zeros((H, W, 4), np.uint8)
            e[..., :3] = np.clip(em, 0, 225).astype(np.uint8)
            e[..., 3] = m * 255
            e[~m, :3] = 0
    return out, e


def spec(groupe, nom, c, X, Y, s, peintures, dens=DF):
    X, Y, Z = repere(X, Y)
    faces = {}
    for f, fn in peintures.items():
        P = points_face(np.asarray(c, float), X, Y, Z, s, f, dens)
        col, em, m = fn(P)
        if m.any():
            nomt = f"{nom}_{f}"
            TILES[nomt] = _rgba(col, m, em)
            faces[f] = nomt
    SPECS.append({"groupe": groupe, "nom": nom, "c": np.asarray(c, float), "X": X, "Y": Y, "s": s, "faces": faces})


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


# --- peintures de la lame (acier bruni, fil poli, aucune lumière)
def peint_biseau_lame(P, dE):
    f = (dE / wb_lame(P[..., 0]))[..., None]
    col = lerp(POLI, STEEL["base"] * 1.12, np.clip((f - 0.16) / 0.5, 0, 1)) * (1 + brosse(P, 1.0))[..., None]
    col = np.where(f < 0.16, FIL + np.zeros_like(col), col)
    col = np.where(f >= 0.92, STEEL["low"] + np.zeros_like(col), col)
    return col, None


def peint_fil_lame(P):
    return np.zeros(P.shape[:-1] + (3,), np.float32) + FIL, None


def peint_plat_lame(P, dE):
    wb = wb_lame(P[..., 0])
    col = (STEEL["base"] * 1.05 + np.zeros(P.shape[:-1] + (3,), np.float32)) * (1 + brosse(P, 2.0))[..., None]
    col[dE < wb + 0.04] = STEEL["low"]
    dg = d_gout(P)
    a = P[..., 0]
    col[dg < 0.08] = BRASS["hi"]                                   # lèvre de laiton du sertissage
    col[(dg >= 0.08) & (dg < 0.13)] = BRASS["low"]
    # graduations gravées du côté +b (tous les 1,0 px, une sur quatre plus longue et en laiton)
    ph = (a - 10.75) / 1.0
    near = np.abs(ph - np.round(ph)) * 1.0 < 0.06
    k4 = (np.round(ph) % 4 == 0)
    zone = (P[..., 1] > 0) & (dg >= 0.2) & (a > 10.6) & (a < 19.2)
    long_ = zone & near & k4 & (dg < 0.56)
    court = zone & near & ~k4 & (dg < 0.4)
    col[court] = STEEL["low"]
    col[long_] = BRASS["base"]
    return col, None


LAME_P = Piece("lame", LAME, [U, L], h_lame, wb_lame, Z_E, peint_biseau_lame, peint_plat_lame, peint_fil_lame, trou=in_gout)


def gouttiere(groupe):
    """Fond (âme de 0,32 px) + parois le long des deux bords, sur chaque face ; lèvre de laiton."""
    pa = np.array(GOUT)
    box = (pa[:, 0].min() - 0.15, pa[:, 0].max() + 0.15, pa[:, 1].min() - 0.15, pa[:, 1].max() + 0.15)

    def fond(P):
        P2 = P[..., :2]
        m = in_gout(P2) | (d_gout(P2) < 0.1)
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + STEEL["low"] * 0.8
        return col, None, m

    a0, a1, b0, b1 = box
    spec(groupe, "fond", ((a0 + a1) / 2, (b0 + b1) / 2, 0.0), (1, 0, 0), (0, 1, 0), (a1 - a0, b1 - b0, 2 * Z_FOND),
         {"south": fond, "north": fond})
    murs = []
    for sg, pts in GOUT_COTES.items():
        for i in range(len(pts) - 1):
            murs.append((pts[i], pts[i + 1]))
    for j, (p, q) in enumerate(murs):
        p, q = np.asarray(p, float), np.asarray(q, float)
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        mid = (p + q) / 2
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
            face = "south" if Z[:2] @ n < 0 else "north"

            def paroi(P):
                P2 = P[..., :2]
                dz = LAME_P.h(P2[..., 0]) - np.abs(P[..., 2])
                col = lerp(STEEL["base"], STEEL["low"], np.clip((dz[..., None] - 0.1) / 0.3, 0, 1)) + np.zeros(P.shape[:-1] + (3,), np.float32)
                col[dz < 0.1] = BRASS["base"]
                return col, None, np.ones(P.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zc)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec(groupe, f"paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


def conception():
    SPECS.clear()
    volume(LAME_P, "lame")
    gouttiere("lame")


conception()
_marge = float(min(LAME_P.wb(np.array([a]))[0] for a, _ in SLIT))


# ------------------------------------------------------------------ tuiles des tours (pans trapézoïdaux)
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
        hw = np.maximum(np.abs(xn).max(), 1e-3)
        dx = xn * ex.get("demi", 0.25)
        dd = np.hypot(dx, yy)
        col = np.where((dd < 0.15)[..., None], COPPER["low"] * 0.7, col)
        col = np.where((dd < 0.11)[..., None], BRASS["base"], col)
        col = np.where((np.hypot(dx + 0.03, yy - 0.03) < 0.05)[..., None], BRASS["hi"], col)
    return col, None


def p_acier(xn, t, y, r, L, ex):
    k = np.clip(0.25 + 0.6 * (1 - np.abs(xn) ** 1.3) + ex.get("clair", 0.0), 0, 1)
    return lerp(STEEL["low"], STEEL["hi"], k[..., None]), None


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
    # ménisque : trait clair tous les 2,6 px (bulles de niveau), très discret
    return col, em


def p_suie(xn, t, y, r, L, ex):
    return np.zeros(xn.shape + (3,), np.float32) + A((34, 28, 24)), None


PEINTRES = {"laiton": p_laiton, "cuivre": p_cuivre, "acier": p_acier, "cuir": p_cuir, "ambre": p_ambre, "suie": p_suie}


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
    ex = dict(ex)
    ex.setdefault("demi", max(w0, w1) / 2)
    col, em = PEINTRES[mat](xn, t, y, r, L, ex)
    TILES[nom] = _rgba(col, mask, em)
    return nom


# ------------------------------------------------------------------ tuiles peintes (plaques, cadrans, dents)
def disque(n, fn, ss=4):
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
    return _rgba(rgb, al, e)


def f_roue(X, Y, R):
    """Face de la roue de garde : couronne polie, gorge, voile creusé à 6 évidements sombres et 6 rivets, moyeu de cuivre."""
    col = lerp(BRASS["base"], BRASS["hi"], np.clip(0.5 + 0.4 * Y, 0, 1)[..., None]) * np.ones(R.shape + (1,), np.float32)
    col[(R > 0.78) & (R < 0.82)] = BRASS["low"] * 0.8
    web = (R >= 0.48) & (R <= 0.78)
    col[web] = lerp(BRASS["low"], BRASS["base"], np.clip(0.4 + 0.3 * Y[web], 0, 1)[..., None])
    ang = np.arctan2(Y, X)
    for k in range(6):
        th = TAU * k / 6 + TAU / 12
        hx, hy = 0.63 * math.cos(th), 0.63 * math.sin(th)
        dh = np.hypot(X - hx, Y - hy)
        col[dh < 0.115] = BRASS["low"] * 0.45
        col[(dh < 0.115) & (Y - hy < -0.04)] = BRASS["low"] * 0.75                    # bord éclairé du creux
        th2 = TAU * k / 6
        rx, ry = 0.63 * math.cos(th2), 0.63 * math.sin(th2)
        dr = np.hypot(X - rx, Y - ry)
        col[dr < 0.06] = BRASS["low"] * 0.7
        col[dr < 0.045] = BRASS["hi"]
    col[(R > 0.44) & (R < 0.48)] = BRASS["low"] * 0.8
    col[R <= 0.44] = lerp(COPPER["base"], COPPER["hi"], np.clip(0.5 + 0.5 * Y, 0, 1)[..., None])[R <= 0.44]
    return col, None


def f_cadran(X, Y, R):
    """Cadran : lunette de laiton fine, verre ambre, 13 crans (-120° à +120°), zone rouge en haut de l'échelle."""
    col = lerp(BRASS["hi"], BRASS["low"], np.clip(0.5 - 0.5 * Y, 0, 1)[..., None] * 0.8) * np.ones(R.shape + (1,), np.float32)
    em = np.zeros(R.shape + (3,), np.float32)
    ang = np.degrees(np.arctan2(X, Y))
    glass = R < 0.84
    col[(R > 0.84) & (R < 0.9)] = BRASS["low"] * 0.7
    g = lerp(AMBRE, AMBRE_B, np.clip(R / 0.84, 0, 1)[..., None] ** 1.5)
    col[glass] = g[glass]
    em[glass] = (190, 126, 40)
    red = glass & (R > 0.58) & (R < 0.76) & (ang > 84) & (ang < 122)
    col[red] = (176, 44, 30)
    em[red] = (150, 30, 14)
    for k in range(13):
        a = -120 + 20 * k
        r0 = 0.56 if k % 2 == 0 else 0.64
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        along = X * sa + Y * ca
        across = np.abs(X * ca - Y * sa)
        tick = glass & (along > r0) & (along < 0.8) & (across < (0.05 if k % 2 == 0 else 0.035))
        col[tick] = (58, 32, 18)
        em[tick] = 0
    hl = glass & (np.abs(R - 0.68) < 0.04) & (ang < -40) & (ang > -95)
    col[hl] = lerp(AMBRE, VAPEUR, 0.7)
    return col, em


def t_unie(W, H, c0, c1, bord=None):
    col = lerp(c0, c1, np.linspace(0, 1, H)[:, None, None] * np.ones((1, W, 1), np.float32))
    if bord is not None:
        col[0] = col[-1] = bord
        col[:, 0] = col[:, -1] = bord
    return _rgba(col, np.ones((H, W), bool))


def t_aiguille():
    c = np.zeros((16, 4, 3), np.float32) + A((34, 28, 26))
    c[:6] = (190, 44, 30)
    c[:, :1] *= 1.5
    return _rgba(c, np.ones((16, 4), bool))


def t_foyer(W=32, H=16):
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
    for x, y in ((3, 3), (W - 4, 3), (3, H - 4), (W - 4, H - 4)):
        c[y:y + 2, x:x + 2] = BRASS["hi"]
    return _rgba(c, np.ones((H, W), bool), e)


def cell_noise(h, w, cy, cx, seed):
    r = np.random.default_rng(seed)
    a = (r.random((cy + 2, cx + 2)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((w, h), Image.BICUBIC), np.float32) / 255


def t_jet(W=128, H=56, seed=71):
    """Vapeur en dégradé d'opacité (alpha 1–254), blanc légèrement bleuté (tuile du groupe trans_jet)."""
    ss = 3
    yy, xx = np.mgrid[0:H * ss, 0:W * ss]
    u = (xx + 0.5) / (W * ss)
    v = (yy + 0.5) / (H * ss) * 2 - 1
    n1 = cell_noise(H * ss, W * ss, 4, 9, seed)
    n2 = cell_noise(H * ss, W * ss, 9, 22, seed + 1)
    lump = 0.78 + 0.32 * n1 + 0.12 * n2
    hw = lerp(0.22, 0.96, u ** 0.55) * (0.82 + 0.25 * n1)
    prof = np.clip(1 - (np.abs(v) / np.maximum(hw, 1e-3)) ** 2, 0, 1) ** 0.6
    along = np.clip(u / 0.05, 0, 1) * np.clip(1 - u ** 1.7, 0, 1)
    a = np.clip(250 * prof * along * lump, 0, 254)
    c = lerp(VAPEUR_B, VAPEUR, np.clip(1 - np.abs(v) * 0.8, 0, 1)[..., None])
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(a.astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(np.int32)
    al[al < 10] = 0
    al = np.clip(al, 0, 254)
    out = np.dstack([rgb, al]).astype(np.uint8)
    out[al == 0, :3] = VAPEUR_B.astype(np.uint8)
    return out, None


R_PL = R_RIM + 0.02
TILES["roue"] = disque(int(round(2 * R_PL * 16)), f_roue)
TILES["cadran"] = disque(48, f_cadran)
TILES["dent"] = t_unie(10, 10, BRASS["hi"], BRASS["base"], bord=BRASS["low"])
TILES["dent_bout"] = t_unie(10, 10, BRASS["hi"] * 1.0, BRASS["hi"] * 0.92, bord=BRASS["low"])
TILES["aiguille"] = t_aiguille()
TILES["foyer"] = t_foyer()
TILES["acier_b"] = t_unie(16, 8, STEEL["hi"], STEEL["low"], bord=STEEL["low"])
TILES["laiton_b"] = t_unie(16, 8, BRASS["hi"], BRASS["low"], bord=BRASS["low"])
TILES["jet"] = t_jet()
TRANS.add("jet")


# ------------------------------------------------------------------ géométrie (monde)
elements, groups = [], {}
CLEAR = "CLEAR"
SIX = ("north", "south", "east", "west", "up", "down")


def nuid():
    return str(_uuid.uuid4())


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx (ordre du mod et du renderer)."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if abs(R[2, 0]) > 0.99999:
        return math.degrees(math.atan2(-R[1, 2], R[1, 1])), math.degrees(ry), 0.0
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def rmat(rx, ry, rz):
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


class Repere:
    th, P0 = 0.0, V(0, 0, 0)


def W_(a, b, z=0.0):
    c, s = math.cos(Repere.th), math.sin(Repere.th)
    return Repere.P0 + V(c * a - s * b, s * a + c * b, z)


def Wv(a, b, z=0.0):
    c, s = math.cos(Repere.th), math.sin(Repere.th)
    return V(c * a - s * b, s * a + c * b, z)


def group(name, origin, parent=None, nom=None, rotation=(0, 0, 0)):
    assert name not in groups, name
    groups[name] = {"origin": [round(float(v), 4) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "nom": nom or name,
                    "rotation": [round(float(v), 3) for v in rotation]}
    return name


def boite(g, name, c, X, Y, s, faces):
    X, Y, Z = repere(X, Y)
    c, s = np.asarray(c, float), np.asarray(s, float)
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in c - s / 2],
         "to": [round(float(v), 4) for v in c + s / 2], "origin": [round(float(v), 4) for v in c], "box_uv": False,
         "faces": {f: {"uv": faces.get(f, CLEAR), "texture": 0} for f in SIX}}
    rot = euler(np.column_stack([X, Y, Z]))
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def tour(g, nom, O, ax, ref, profil, n=12, phase=0.0):
    """profil = [(b0, r0, b1, r1, mat, ex), ...] le long de ax depuis O (monde) ; une couronne de n pans par tronçon."""
    O, ax = np.asarray(O, float), unit(np.asarray(ax, float))
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    for i, (b0, r0, b1, r1, mat, ex) in enumerate(profil):
        L_ = math.hypot(b1 - b0, r1 - r0)
        if L_ < 1e-4:
            continue
        tile = tuile_pan(f"{nom}{i}", mat, L_, 2 * r0 * tn, 2 * r1 * tn, r0, r1, ex)
        db, dr = (b1 - b0) / L_, (r1 - r0) / L_
        wm = max(2 * r0 * tn, 2 * r1 * tn) + 2 * OVW
        for k in range(n):
            th = phase + TAU * k / n
            e = math.cos(th) * ref + math.sin(th) * w3
            P0, P1 = O + b0 * ax + r0 * e, O + b1 * ax + r1 * e
            Y = unit(P1 - P0)
            N = -dr * ax + db * e
            X = np.cross(Y, N)
            boite(g, f"{nom}{i}_{k}", (P0 + P1) / 2 - N * TH / 2, X, Y, (wm, L_ + 2 * OVL, TH), {"south": tile})


def tuyau(g, nom, pts, r, mat="cuivre", collier=0.37):
    """Tuyau (monde) le long d'une polyligne : un cylindre à 8 pans par tronçon, collier de laiton à chaque coude."""
    pts = [np.asarray(p, float) for p in pts]
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]
        Ln = float(np.linalg.norm(q - p))
        ref = V(0, 0, 1)
        tour(g, f"{nom}{i}_", p, q - p, ref, [(-0.08, r, Ln + 0.08, r, mat, {})], n=8, phase=math.pi / 8)
    for i in range(1, len(pts) - 1):
        d = unit(unit(pts[i + 1] - pts[i]) + unit(pts[i] - pts[i - 1]))
        tour(g, f"{nom}c{i}_", pts[i], d, V(0, 0, 1),
             [(-0.17, r - 0.02, -0.17, collier, "laiton", {}), (-0.17, collier, 0.17, collier, "laiton", {"arete": True}),
              (0.17, collier, 0.17, r - 0.02, "laiton", {})], n=8, phase=math.pi / 8)


def plaque(g, name, c, X, Y, w, h, th, tile, dos=None):
    """Plaque découpée par l'alpha (south = tuile, north = tuile `dos` miroir si donnée), tranches transparentes."""
    faces = {"south": tile}
    if dos is not None:
        faces["north"] = dos
    boite(g, name, c, X, Y, (w, h, th), faces)


MIROIR = {}         # nom de tuile -> UV inversée en u (face arrière vue « à travers »)


def bone_node(name):
    g = groups[name]
    return {"name": g["nom"], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


def ang_dents():
    """Dents de la roue (angle en degrés depuis +a) : 18 places, retirées là où passent lame, poignée et tuyaux."""
    half_t = math.degrees(0.55 / 2 / 2.17)
    q_ang = math.degrees(math.atan2(Q_DIR[1], Q_DIR[0]))
    b0 = np.array(BOW[1]) - np.array((A_G, 0.0))
    bow_ang = math.degrees(math.atan2(b0[1], b0[0]))
    out = []
    for k in range(18):
        th = 10 + 20 * k
        th = (th + 180) % 360 - 180
        lame = math.degrees(math.atan(1.74 / 2.17)) + half_t + 1.5
        poi = math.degrees(math.atan(0.75 / 2.17)) + half_t + 1.0
        tuy = math.degrees(math.atan(0.42 / 2.1)) + half_t + 1.0
        dif = lambda a, b: abs((a - b + 180) % 360 - 180)
        if dif(th, 0) < lame or dif(th, 180) < poi or dif(th, q_ang) < tuy or dif(th, bow_ang) < tuy:
            continue
        out.append(th)
    return out


DENTS = ang_dents()
PHI0, CRAN = -100.0, 40.0           # aiguille : niveau 0 à -100° (depuis le haut), 40° par cran, 5 crans jusqu'au rouge


def build(theta, P0):
    elements.clear()
    groups.clear()
    Repere.th, Repere.P0 = theta, np.asarray(P0, float)
    out = {}
    nz = V(0, 0, 1)
    ax = Wv(1, 0)
    racine = group("repos", W_(4.0, 0), nom=objet.etape("repos", "epee"))
    epee = group("epee", W_(4.0, 0), parent=racine)
    # --- lame (volume, gouttière) et tube de niveau ambré entre deux raccords de laiton
    lame = group("lame", W_(8.3, 0), parent=epee)
    for sp in SPECS:
        boite(lame, sp["nom"], W_(*sp["c"]), Wv(*sp["X"]), Wv(*sp["Y"]), sp["s"], sp["faces"])
    a0, a1, rt = TUBE
    tube = group("tube", W_(a0, 0), parent=lame)
    group("ctrl_lumiere_tube", W_(a0, 0), parent=tube, nom="ctrl_lumiere")
    tour(tube, "tube", W_(a0, 0), ax, nz, [(0.0, rt, a1 - a0, rt, "ambre", {})], n=8)
    for k, ac in enumerate((a0 - 0.05, a1 + 0.05)):
        sg = -1 if k == 0 else 1
        tour(lame, f"raccord{k}_", W_(ac, 0), ax * sg, nz,
             [(-0.25, 0.3, 0.12, 0.3, "laiton", {"arete": True}), (0.12, 0.3, 0.3, 0.12, "laiton", {}), (0.3, 0.12, 0.34, 0.0, "laiton", {})],
             n=8)
    # --- roue de garde : flanc à 24 pans, deux faces découpées par l'alpha, dents en boîtes, lunettes et cadrans
    garde = group("garde", W_(A_G, 0), parent=epee)
    C = W_(A_G, 0)
    tour(garde, "flanc", C - nz * GZ, nz, ax, [(0.0, R_RIM, 2 * GZ, R_RIM, "laiton", {"arete": True})], n=24)
    for sg in (1, -1):
        plaque(garde, f"face{'pm'[sg < 0]}", C + nz * sg * (GZ + 0.02 - TH / 2), Wv(1, 0) * sg, Wv(0, 1), 2 * R_PL, 2 * R_PL, TH, "roue")
    for k, th in enumerate(DENTS):
        e = Wv(math.cos(math.radians(th)), math.sin(math.radians(th)))
        t_ = np.cross(nz, e)
        boite(garde, f"dent{k}", C + e * (R_RIM + 0.25 - 0.05), e, t_, (0.6, 0.55, 2 * TZ),
              {f: ("dent_bout" if f == "west" else "dent") for f in SIX})
    for sg in (1, -1):
        tour(garde, f"lunette{'pm'[sg < 0]}_", C + nz * sg * GZ, nz * sg, V(1, 0, 0),
             [(0.0, 1.12, 0.22, 1.12, "laiton", {"clair": 0.1}), (0.22, 1.12, 0.3, 1.0, "laiton", {"clair": 0.2})], n=16)
        # cadran arrière vu « à travers » (UV inversée en u) : même échelle et même sens que l'aiguille, qui tourne autour de Z
        boite(garde, f"cadran{'pm'[sg < 0]}", C + nz * sg * (GZ + 0.26), V(1, 0, 0), V(0, 1, 0), (2.04, 2.04, 0.12),
              {"south": "cadran"} if sg > 0 else {"north": "cadran@m"})
    aig = group("aiguille", C, parent=garde)
    phi = math.radians(PHI0)
    dn = V(math.sin(phi), math.cos(phi), 0)
    for sg in (1, -1):
        z = sg * (GZ + 0.38)
        boite(aig, f"aiguille{'pm'[sg < 0]}", C + dn * 0.33 + nz * z, np.cross(dn, nz), dn, (0.1, 0.78, 0.05),
              {f: "aiguille" for f in SIX})
        boite(aig, f"moyeu{'pm'[sg < 0]}", C + nz * (z + sg * 0.03), V(1, 0, 0), V(0, 1, 0), (0.16, 0.16, 0.08), {f: "laiton_b" for f in SIX})
    out["aiguille"] = aig
    # --- quillon +b : tuyau de cuivre, collier, buse évasée (gorge de suie, paroi intérieure)
    tuy = group("tuyaux", W_(A_G, 0), parent=epee)
    QS = np.array((A_G, 0.0)) + Q_DIR * Q_S
    QE = np.array((A_G, 0.0)) + Q_DIR * Q_E
    qd = Wv(*Q_DIR)
    tour(tuy, "quillon", W_(*QS), qd, nz, [(0.0, 0.4, Q_E - Q_S, 0.4, "cuivre", {})], n=12)
    QM = np.array((A_G, 0.0)) + Q_DIR * 2.95
    tour(tuy, "q_collier", W_(*QM), qd, nz, [(-0.18, 0.38, -0.18, 0.5, "laiton", {}), (-0.18, 0.5, 0.18, 0.5, "laiton", {"arete": True}),
                                            (0.18, 0.5, 0.18, 0.38, "laiton", {})], n=12)
    tour(tuy, "buse", W_(*QE), qd, nz, [(-0.12, 0.42, 0.32, 0.46, "laiton", {"arete": True}), (0.32, 0.46, 0.78, 0.72, "laiton", {"clair": 0.1}),
                                       (0.78, 0.72, 0.86, 0.72, "laiton", {"clair": 0.2})], n=12)
    tour(tuy, "buse_in", W_(*QE), qd, nz, [(0.86, 0.66, 0.34, 0.40, "laiton", {"clair": -0.25})], n=12)
    tour(tuy, "gorge", W_(*QE), qd, nz, [(0.3, 0.42, 0.34, 0.0, "suie", {})], n=12)
    # --- garde de main -b : tuyau de vapeur de la chaudière à la roue, volant de vanne sur +Z
    tuyau(tuy, "arc", [W_(*p) for p in BOW], 0.3)
    VC = W_(*VOLANT)
    tour(tuy, "v_tige", VC + nz * 0.2, nz, ax, [(0.0, 0.11, 0.62, 0.11, "acier", {})], n=8)
    tour(tuy, "v_embase", VC + nz * 0.16, nz, ax, [(0.0, 0.2, 0.18, 0.2, "laiton", {"arete": True}), (0.18, 0.2, 0.2, 0.0, "laiton", {})], n=8)
    vol = group("volant", VC, parent=tuy)
    RV, ZV = 0.62, 0.78
    for k in range(8):
        a_ = TAU * (k + 0.5) / 8
        p = VC + nz * ZV + Wv(math.cos(a_), math.sin(a_)) * RV
        t_ = Wv(-math.sin(a_), math.cos(a_))
        boite(vol, f"jante{k}", p, t_, Wv(math.cos(a_), math.sin(a_)), (2 * RV * math.tan(math.pi / 8) + 0.1, 0.16, 0.16), {f: "acier_b" for f in SIX})
    for k in range(2):
        a_ = math.pi / 4 + math.pi / 2 * k
        boite(vol, f"rayon{k}", VC + nz * ZV, Wv(math.cos(a_), math.sin(a_)), Wv(-math.sin(a_), math.cos(a_)), (2 * RV - 0.1, 0.11, 0.11),
              {f: "acier_b" for f in SIX})
    boite(vol, "v_moyeu", VC + nz * ZV, ax, Wv(0, 1), (0.26, 0.26, 0.2), {f: "laiton_b" for f in SIX})
    out["volant"] = vol
    # --- jet de vapeur caché dans la buse (déplié par event_hit seul), point de white_smoke à la bouche
    JP = W_(*(QE + Q_DIR * 0.3))
    JL, JW = 4.0, 2.2
    f = F_GEO / KJ
    jet = group("trans_jet", JP, parent=tuy)
    for k in range(3):
        an = math.radians(60 * k)
        Yp = nz * math.cos(an) + np.cross(nz, qd) * math.sin(an)
        boite(jet, f"jet{k}", JP + qd * (JL / 2 * f), qd, Yp, (JL * f, JW * f, 0.15 * f * 2), {"south": "jet", "north": "jet"})
    group("ctrl_alpha_jet", JP, parent=jet, nom="ctrl_alpha")
    rz = math.degrees(math.atan2(qd[1], qd[0])) - 90
    em = group("emit_mc_white_smoke", W_(*(QE + Q_DIR * 0.85)), parent=tuy, rotation=(0, 0, rz))
    group("ctrl_emit", W_(*(QE + Q_DIR * 0.85)), parent=em)
    out["jet"] = jet
    # --- poignée de cuir cousu entre deux viroles, pommeau-chaudière riveté, foyer, soupape
    poi = group("poignee", W_(4.0, 0), parent=epee)
    tour(poi, "fusee", W_(0, 0), ax, nz, [(1.3, 0.62, 5.6, 0.62, "cuir", {})], n=12)
    tour(poi, "virole_b", W_(0, 0), ax, nz, [(1.2, 0.6, 1.2, 0.74, "laiton", {}), (1.2, 0.74, 1.55, 0.74, "laiton", {"arete": True}),
                                            (1.55, 0.74, 1.55, 0.6, "laiton", {})], n=12)
    tour(poi, "virole_h", W_(0, 0), ax, nz, [(5.45, 0.6, 5.45, 0.74, "laiton", {}), (5.45, 0.74, 5.95, 0.74, "laiton", {"arete": True})], n=12)
    prof = [(-2.92, 0.0, -2.86, 0.34, "laiton", {"clair": 0.2}), (-2.86, 0.34, -2.62, 0.34, "laiton", {"arete": True}),
            (-2.62, 0.34, -2.6, 0.2, "laiton", {}), (-2.6, 0.2, -2.3, 0.2, "acier", {}),
            (-2.3, 0.2, -2.28, 0.42, "laiton", {}), (-2.28, 0.42, -2.08, 0.72, "laiton", {"clair": 0.15}),
            (-2.08, 0.72, -1.95, 0.92, "laiton", {}), (-1.95, 0.92, -1.95, 0.97, "laiton", {}),
            (-1.95, 0.97, -1.6, 0.97, "laiton", {"arete": True}), (-1.6, 0.97, -1.58, 0.88, "laiton", {}),
            (-1.58, 0.88, 0.95, 0.88, "cuivre", {"riv": 0.62, "y0": 0.31}), (0.95, 0.88, 0.97, 0.97, "laiton", {}),
            (0.97, 0.97, 1.3, 0.97, "laiton", {"arete": True}), (1.3, 0.97, 1.45, 0.66, "laiton", {})]
    tour(poi, "chaudiere", W_(0, 0), ax, nz, prof, n=12)
    for sg in (1, -1):
        boite(poi, f"foyer{'pm'[sg < 0]}", W_(-0.35, 0, sg * (0.88 + 0.07)), ax, Wv(0, 1), (1.1, 0.44, 0.1), {"south" if sg > 0 else "north": "foyer"})
    out["racine"], out["epee"], out["tube"] = racine, epee, tube
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


K = float(os.environ.get("K", "0.95"))      # 27,4 px (vanilla 22,6 ; épée d orage validée 27,5)
THETA = math.radians(45)
build(THETA, V(0, 0, 0))
P = coins()
CENTRE = (P.min(axis=0) + P.max(axis=0)) / 2
F = build(THETA, V(8, 8, 8) - CENTRE)
if abs(K - 1) > 1e-6:
    P0_ = V(8, 8, 8)
    for e in elements:
        for k_ in ("from", "to", "origin"):
            e[k_] = [round(float(P0_[i] + K * (e[k_][i] - P0_[i])), 4) for i in range(3)]
    for gg in groups.values():
        gg["origin"] = [round(float(P0_[i] + K * (gg["origin"][i] - P0_[i])), 4) for i in range(3)]
P = coins()
D_ = np.array((1, 1, 0)) / math.sqrt(2)
E_ = np.array((-1, 1, 0)) / math.sqrt(2)
LONGUEUR = float((P @ D_).max() - (P @ D_).min())
LARGEUR = float((P @ E_).max() - (P @ E_).min())
outliner = [bone_node(F["racine"])]


# ------------------------------------------------------------------ atlas (après la géométrie)
def atlas():
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    UV = {}
    x, y, shelf = 0, 0, 0
    for n, (im, ime) in sorted(TILES.items(), key=lambda it: (-it[1][0].shape[0], it[0])):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, "atlas plein"
        UV[n] = [x, y, x + w, y + h]
        tex[y:y + h, x:x + w] = im
        if ime is not None and AVEC_E:
            tex_e[y:y + h, x:x + w] = ime
        x += w + 1
        shelf = max(shelf, h)
    UV[CLEAR] = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]
    assert tex[TEX - 2, TEX - 2, 3] == 0
    tex[..., :3] &= 0xFC
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    zone = np.zeros(semi.shape, bool)
    for n in TRANS:
        u0, v0, u1, v1 = UV[n]
        zone[v0:v1, u0:u1] = True
    assert not (semi & ~zone).any(), "semi-transparence hors des tuiles trans_"
    assert set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence _e"
    res = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        res.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    print(f"atlas : {len(TILES)} tuiles, rempli jusqu'à y = {y + shelf}")
    return res, UV


(tex_b64, tex_e_b64), UV = atlas()
for e in elements:
    for fc in e["faces"].values():
        if fc["uv"].endswith("@m"):
            u0, v0, u1, v1 = UV[fc["uv"][:-2]]
            fc["uv"] = [u1, v0, u0, v1]
        else:
            fc["uv"] = list(UV[fc["uv"]])


# ------------------------------------------------------------------ animations (objet vivant, guide 14)
def kf(t, x, y=0.0, z=0.0, ch="rotation"):
    f = lambda v: v if isinstance(v, str) else str(round(v + 0.0, 3))
    return {"channel": ch, "data_points": [{"x": f(x), "y": f(y), "z": f(z)}], "time": round(t, 4), "interpolation": "linear"}


def anim(name, length, tracks, fps=24, loop="loop"):
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A_ = {}
    for (g, ch), fn in tracks.items():
        ks = [kf(t, *fn(t), ch=ch) for t in times]
        A_.setdefault(groups[g]["uuid"], {"name": groups[g]["nom"], "type": "bone", "keyframes": []})["keyframes"] += ks
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": False, "animators": A_}


def step(tau, rise=0.05, over=0.28):
    """Échelon de servo : montée courte, dépassement puis rappel amorti."""
    if tau <= 0:
        return 0.0
    v = sm(tau, 0.0, rise)
    if tau > rise * 0.6:
        x = tau - rise * 0.6
        v += over * math.sin(TAU * x / 0.15) * math.exp(-x / 0.045)
    return v


def needle(lvl):
    return 0.0, 0.0, -CRAN * lvl            # monter = sens horaire vu de +Z


AIG, VOL, JET, EPEE = F["aiguille"], F["volant"], F["jet"], F["epee"]
CL, CE, CA = "ctrl_lumiere_tube", "ctrl_emit", "ctrl_alpha_jet"
JD = Wv(*Q_DIR)

# --- item_idle (24 s) : deux cycles ; cinq crans de pression, tremblement, décharge (white_smoke à la buse), aiguille qui retombe
L_IDLE = 24.0
TICKS = [1.5, 3.0, 4.5, 6.0, 7.5, 13.5, 15.0, 16.5, 18.0, 19.5]
PUFFS = [10.0, 22.0]
TW = 1.2


def tremble(t):
    return sum(bump(t, tp - TW, tp - TW * 0.75, tp - 0.03, tp) for tp in PUFFS)


def idle_level(t):
    v = sum(step(t - ti) for ti in TICKS) - sum(5 * step(t - tp - 0.03, rise=0.12, over=0.08) for tp in PUFFS)
    return v + 0.1 * tremble(t) * math.sin(TAU * 19 * t)


def idle_lum(t):
    return -0.5 + 0.11 * idle_level(t) + 0.25 * sum(bump(t, tp - 0.02, tp + 0.03, tp + 0.15, tp + 0.5) for tp in PUFFS), 0.0, 0.0


def idle_emit(t):
    return -1 + 4 * sum(bump(t, tp + 0.02, tp + 0.08, tp + 0.4, tp + 0.6) for tp in PUFFS), 0.0, 0.0


item_idle = anim("item_idle", L_IDLE, {(AIG, "rotation"): lambda t: needle(idle_level(t)), (CL, "position"): idle_lum,
                                       (CE, "position"): idle_emit}, fps=30)

# --- event_select (0,8 s) : on ouvre la vanne d'un quart de tour (deux crans), l'aiguille fait son tour d'essai, le tube s'allume
L_SEL = 0.8


def sel_needle(t):
    return needle(sum(step(t - ti) for ti in (0.22, 0.3, 0.38)) - 3 * step(t - 0.56, rise=0.1, over=0.1))


event_select = anim("event_select", L_SEL, {
    (VOL, "rotation"): lambda t: (0.0, 0.0, -45 * (step(t - 0.04, 0.06, 0.15) + step(t - 0.14, 0.06, 0.15))),
    (AIG, "rotation"): sel_needle,
    (CL, "position"): lambda t: (-1.0 + 1.0 * sm(t, 0.2, 0.3) + 0.5 * bump(t, 0.28, 0.34, 0.4, 0.7), 0.0, 0.0)}, fps=40, loop="once")

# --- event_swing (0,35 s) : l'aiguille perd un cran et remonte, le tube vacille
L_SW = 0.35
event_swing = anim("event_swing", L_SW, {
    (AIG, "rotation"): lambda t: needle(-(step(t - 0.03, rise=0.03, over=0.15) - step(t - 0.18, rise=0.08, over=0.12))),
    (CL, "position"): lambda t: (0.45 * bump(t, 0.0, 0.03, 0.08, 0.3), 0.0, 0.0)}, fps=40, loop="once")

# --- event_hit (0,9 s) : décharge : jet qui jaillit de la buse et monte, vapeur, vanne d'un quart de tour, aiguille qui chute
L_HIT = 0.9


def jet_scale(t):
    w = sm(t, 0.03, 0.1) * (1 + 0.3 * sm(t, 0.1, 0.4)) * (1 - sm(t, 0.5, 0.64))
    k = (1 + (KJ - 1) * w) / F_GEO
    return k, k, k


def jet_pos(t):
    v = (JD * 0.9 + V(0, 0.6, 0)) * sm(t, 0.08, 0.62) * (1 - sm(t, 0.64, 0.68))       # le long de la buse, puis vers le haut
    return float(v[0]), float(v[1]), float(v[2])


event_hit = anim("event_hit", L_HIT, {
    (JET, "scale"): jet_scale, (JET, "position"): jet_pos,
    (CA, "position"): lambda t: (-sm(t, 0.3, 0.62) * (1 - sm(t, 0.66, 0.7)), 0.0, 0.0),
    (CE, "position"): lambda t: (5 * bump(t, 0.03, 0.06, 0.32, 0.5), 0.0, 0.0),
    (VOL, "rotation"): lambda t: (0.0, 0.0, -45 * (step(t - 0.02, 0.05, 0.12) + step(t - 0.12, 0.05, 0.12))),
    (AIG, "rotation"): lambda t: needle(-3 * (step(t - 0.03, rise=0.06, over=0.1) - step(t - 0.45, rise=0.2, over=0.08))),
    (CL, "position"): lambda t: (0.9 * sm(t, 0.0, 0.03) * (1 - sm(t, 0.08, 0.6)), 0.0, 0.0),
    (EPEE, "rotation"): lambda t: (0.0, 0.0, 2.0 * math.sin(TAU * t / 0.07) * (1 - sm(t, 0.0, 0.3)) * (t < 0.3))}, fps=40, loop="once")

ANIMS = [item_idle, event_select, event_swing, event_hit]
ANIMS[0]["selected"] = True

# ------------------------------------------------------------------ écriture
assert len(elements) <= 8192, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
_lo, _hi = P[:, :2].min(0), P[:, :2].max(0)
GUI = float(os.environ.get("GUI", "0")) or round(min(0.85, 16.4 / float(max(_hi - _lo))), 3)
AFFICHAGE = objet.affichage("epee", gui={"scale": [GUI] * 3})
model = objet.modele(NOM, "epee", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons  # noqa: E402
limiter_sons(model)
# Un seul son, au coup qui touche ; tools/sons.py ne connaît pas les événements d'objet : remis ici, à 0,04 s
# (une clé à 0,0 s est muette au premier déclenchement, diagnostic F5). Aucun son ailleurs.
event_hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "block.fire.extinguish", "file": ""}], "time": 0.04}]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur sur la diagonale {LONGUEUR:.1f} px ; largeur {LARGEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)} ;"
      f" gui {GUI} ; dents {len(DENTS)} ; biseau mini sous la gouttière {_marge:.2f} px")
