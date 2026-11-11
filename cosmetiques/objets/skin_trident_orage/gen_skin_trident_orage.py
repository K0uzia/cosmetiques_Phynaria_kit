"""Trident de l'orage : skin d'objet (guide 14) pour tous les tridents du joueur, ensemble Orage (thème Éléments). Design original.
Écrit skin_trident_orage.png, skin_trident_orage_e.png et .build/skin_trident_orage_brut.bbmodel à côté de ce script.

Idée : le trident de Minecraft appelle déjà la foudre (Canalisation) ; celui des Dompteurs d'orage est un paratonnerre forgé.
Famille (.claude/styles/orage.md) : acier d'orage bleu-noir martelé, fil poli clair + _e, bande de revenu cuivre puis violet,
liseré d'or, âme de foudre couchée dans une gouttière creusée, tambour d'or aux trois virgules, gaine de cuir bleu nuit entre
bagues d'or, talon à pointe de cristal.
Silhouette propre (la lance a un fer de cristal en feuille, ailettes croisées) : **fourche d'acier forgé** d'une seule pièce,
un croissant bas d'où montent trois dents biseautées : la centrale plus longue (cran d'éclair), les latérales évasées à
ardillon tourné vers le bas (comme une fouëne de pêche), le dessous du croissant liseré d'or. Douille en tronc de cône à
8 pans, collet d'or, tambour à 16 pans, hampe octogonale à bagues d'or, gaine de cuir à la prise, talon de cristal.

Vrai volume (recette .claude/references/objets/volume-3d.md) : la fourche est une plaque biseautée fermée (biseaux en cubes
inclinés à **pente unique de 52°** comme la pioche : à 40° les dents de 1,1 à 1,6 px n'auraient plus de plat pour la
gouttière ; plats inclinés qui suivent l'amincissement 1,60 px au croissant -> 0,44 px aux pointes, où la section devient un
losange), faces échantillonnées texel par texel et découpées par l'alpha, recouvrement 0,08 ; trois gouttières creusées
(dent centrale, deux bras du croissant) où la foudre est couchée des deux côtés (cœur clair + _e, gaine add_).

Étapes (guide 14) : `repos` (fourche froide, foudre couchée qui grésille), `leve` (prêt à lancer : même fourche, gouttières
plus vives, **arcs qui sautent entre les pointes**, étincelles aux trois pointes), `lance` (trident en vol : fourche chauffée
à blanc, éclairs le long des dents et traînée de foudre le long de la hampe, vers l'arrière).
Repère : pointe vers +Y, axe en x = z = 8, du talon (y = -7,5) à la pointe (y = 23,7), grand plat face à +Z. Display des
mains : `objet.affichage_trident()` (recalcul de `item/trident_in_hand` du jar : le skin tient la place du trident vanilla).

Objet vivant (guide 14), sobre :
- item_idle (8 s) : la foudre des gouttières grésille (Molang), arc en retour entre deux pointes toutes les 3 à 8 s ;
- item_gui : gouttières calmes ;
- item_use (0,5 s, étape leve) : les arcs entre les pointes vacillent de plus en plus vite avec q.use_progress, la fourche frémit ;
- event_release (0,6 s) : décharge des trois pointes vers l'avant (deux formes, fourches), gerbe emit_mc_electric_spark
  (ctrl_emit) ; **seul son** (embarqué, original : decharge_trident) ;
- event_select (0,7 s) : la foudre frappe la dent centrale puis saute aux deux dents latérales ;
- overlay_vol (1 s) : les éclairs de l'étape `lance` grésillent sur le trident en vol (groupes de l'étape lance seulement).
Éclairs des événements **repliés à 1/10 sur un pivot caché dans le métal** et dépliés par `scale` ×10 par une seule
animation chacun (échelles superposées : aucune).
Fonctions avancées : add_, ctrl_alpha, ctrl_emit, emit_mc_electric_spark, scale animé, calque _e, étapes, animations d'objet
(item_idle, item_gui, item_use, event_release, event_select, overlay_vol), Molang (q.life_time, q.use_progress, q.anim_time),
son embarqué. À juger en jeu : prise en main (Display recalculé du vanilla, pas encore vu), event_release et son son,
overlay sur le trident en vol, lecture de la fourche par la tranche et dans la case.
"""
import base64, io, json, math, os, random, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image, ImageDraw

NOM = "skin_trident_orage"
TEX = 512
TAU = 2 * math.pi
SS = 4
FOLD = 0.1                      # éclairs des événements repliés sur leur pivot

METAL = np.array([(22, 24, 36), (46, 52, 72), (70, 78, 104), (112, 122, 154), (170, 182, 214)], np.float32)
OR = np.array([(130, 90, 30), (176, 128, 44), (220, 170, 60), (255, 230, 140)], np.float32)
CRIS = np.array([(40, 40, 120), (70, 90, 200), (130, 160, 255), (190, 208, 255), (232, 240, 255)], np.float32)
CUIVRE = np.array((196, 118, 64), np.float32)
VIOLET = np.array((112, 88, 172), np.float32)
FIL_C = np.array((236, 244, 255), np.float32)
FIL_E = np.array((110, 150, 235), np.float32)
NIVS = ("repos", "leve", "lance")


def lerp(a, b, k):
    return a + (b - a) * k


def sm(t, a, b):
    if b <= a:
        return 1.0 if t >= b else 0.0
    x = min(1.0, max(0.0, (t - a) / (b - a)))
    return x * x * (3 - 2 * x)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def in_poly(P, poly):
    x, y = P[..., 0], P[..., 1]
    ins = np.zeros(x.shape, bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        ins ^= ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1)
    return ins


def d_poly(P, pts):
    d = np.full(P.shape[:-1], 1e9)
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i], float), np.array(pts[i + 1], float)
        ab = b - a
        t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
        d = np.minimum(d, np.linalg.norm(P - (a + t[..., None] * ab), axis=-1))
    return d


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


# ------------------------------------------------------------------ vrai volume (.claude/references/objets/volume-3d.md)
Z_E = 0.10                        # demi-épaisseur au fil
DF = 16.0                         # texels par px sur les faces des volumes
TH = 0.3                          # épaisseur des cubes de biseau, de plat, de paroi
RECOUV = 0.08
Z_FOND = 0.16
T_BIS = 1.28                      # pente unique des biseaux (52°)


class Gouttiere:
    """Gouttière en zigzag : bords décalés (onglets par intersection), polygone, distance."""

    def __init__(self, slit, gw):
        self.slit = slit
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
                t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / den
                pts.append(p1 + d1 * t)
            pts.append(lignes[-1][1])
            cotes[sg] = pts
        self.cotes = cotes
        self.poly = [tuple(p) for p in cotes[1]] + [tuple(p) for p in cotes[-1][::-1]]

    def dedans(self, P):
        return in_poly(P, self.poly)

    def dist(self, P):
        return d_poly(P, self.poly + [self.poly[0]])


class Piece:
    """Plaque biseautée : contour `poly`, fils `fils` (polylignes, sans la base cachée), profil h(a), wb(a), z au bord."""

    def __init__(self, nom, poly, fils, h, wb, ze, peint_biseau, peint_plat, peint_fil, gouts=()):
        self.nom, self.poly, self.h, self.wb, self.ze = nom, poly, h, wb, ze
        self.segs = [s for f in fils for s in subdiv(f)]
        self.peint_biseau, self.peint_plat, self.peint_fil, self.gouts = peint_biseau, peint_plat, peint_fil, list(gouts)
        pa = np.array(poly)
        self.box = (pa[:, 0].min() - 0.05, pa[:, 0].max() + 0.05, pa[:, 1].min() - 0.05, pa[:, 1].max() + 0.05)

    def dE(self, P):
        return d_stack(P, self.segs).min(0)

    def surf(self, P):
        d, h, wb = self.dE(P), self.h(P[..., 0]), self.wb(P[..., 0])
        return np.where(d < wb, self.ze + (h - self.ze) * np.clip(d / wb, 0, 1), h)


SPECS = {}          # pièce -> cubes du volume : dict(nom, c, X, Y, s, faces) en coordonnées locales (a, b, z)
TILES = {}          # tuiles échantillonnées : nom -> (rgba, rgba_e)


def repere(X, Y):
    X = unit(X)
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    return X, Y, np.cross(X, Y)


def points_face(c, X, Y, Z, s, face, dens=DF):
    sx, sy, sz = s
    dims = {"south": (sx, sy), "north": (sx, sy), "down": (sx, sz), "up": (sx, sz), "east": (sz, sy), "west": (sz, sy)}[face]
    W, H = max(2, int(round(dims[0] * dens))), max(2, int(round(dims[1] * dens)))
    U_, V_ = np.meshgrid((np.arange(W) + 0.5) / W, (np.arange(H) + 0.5) / H)
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
    rgba_e[..., :3] = np.clip(em, 0, 245).astype(np.uint8)
    rgba_e[..., 3] = on * 255
    rgba_e[~on] = 0
    return rgba, rgba_e


def spec(cle, nom, c, X, Y, s, peintures, dens=DF):
    """peintures : {face: fn(points (H, W, 3)) -> (col, em, masque)} ; les autres faces sont transparentes."""
    X, Y, Z = repere(X, Y)
    faces = {}
    for f, fn in peintures.items():
        col, em, m = fn(points_face(np.asarray(c, float), X, Y, Z, s, f, dens))
        if m.any():
            TILES[f"{nom}_{f}"] = finir(col, em, m)
            faces[f] = f"{nom}_{f}"
    SPECS.setdefault(cle, []).append({"nom": nom, "c": np.asarray(c, float), "X": X, "Y": Y, "s": s, "faces": faces})


def volume(pc):
    """Biseaux (deux par tronçon de fil, pente unique) + plats inclinés de la pièce pc."""
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

            spec(pc.nom, f"{pc.nom}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil})
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
            for G in pc.gouts:
                m &= ~G.dedans(P2)
            col, em = pc.peint_plat(P2, dE)
            return col, em, m

        spec(pc.nom, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, ((a1 - a0) * math.sqrt(1 + sl * sl), b1 - b0, TH), {"south": plat})


def gouttiere(pc, G, k, chaud):
    """Fond (âme de 0,32 px où repose la foudre) + parois verticales le long des deux bords, sur chaque face."""
    pa = np.array(G.poly)
    a0, a1, b0, b1 = pa[:, 0].min() - 0.15, pa[:, 0].max() + 0.15, pa[:, 1].min() - 0.15, pa[:, 1].max() + 0.15
    nm = f"{pc.nom}_g{k}"

    def fond(P):
        P2 = P[..., :2]
        m = G.dedans(P2) | (G.dist(P2) < 0.1)
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + np.array((16, 18, 34), np.float32) + cellules(P2, 3.0, 5.0)[..., None] * 6
        em = np.zeros_like(col) + np.array((14, 22, 70), np.float32) * (1.8 if chaud else 1.0)
        return col, em, m

    spec(pc.nom, f"{nm}_fond", ((a0 + a1) / 2, (b0 + b1) / 2, 0.0), (1, 0, 0), (0, 1, 0), (a1 - a0, b1 - b0, 2 * Z_FOND),
         {"south": fond, "north": fond})
    murs = []
    for sg, pts in G.cotes.items():
        for i in range(len(pts) - 1):
            murs.append((pts[i], pts[i + 1]))
    murs.append((G.cotes[1][0], G.cotes[-1][0]))
    murs.append((G.cotes[1][-1], G.cotes[-1][-1]))
    for j, (p, q) in enumerate(murs):
        p, q = np.asarray(p, float), np.asarray(q, float)
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        mid = (p + q) / 2
        inside_pt = mid - n * 0.05
        if not (G.dedans(np.array([inside_pt]))[0] or G.dist(np.array([inside_pt]))[0] < 1e-3):
            n = -n
        back = [p + n * TH, q + n * TH, mid + n * TH]
        top = min(float(pc.surf(np.array([x]))[0]) for x in back + [p, q]) - 0.03
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
                dz = pc.h(P2[..., 0]) - np.abs(P[..., 2])
                col = lerp(METAL[1], METAL[0], np.clip((dz[..., None] - 0.1) / 0.3, 0, 1)) + np.zeros(P.shape[:-1] + (3,), np.float32)
                em = np.zeros_like(col)
                lv = dz < 0.1
                col[lv] = (205, 222, 255) if chaud else (190, 208, 255)
                em[lv] = (90, 130, 235) if chaud else (60, 100, 210)
                return col, em, np.ones(P.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zc)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec(pc.nom, f"{nm}_paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


# ------------------------------------------------------------------ la fourche (plan a le long du trident, b en travers)
# Demi-contour b >= 0, du bas (base cachée dans la douille) à la pointe centrale.
DEMI = [(23.25, 0.62),                                            # base (cachée dans la douille)
        (23.7, 1.3), (24.3, 2.1), (25.0, 2.72),                   # dessous du croissant (liseré d'or)
        (26.2, 3.02), (27.7, 2.98), (29.1, 2.78), (30.25, 2.5),   # dos de la dent latérale, évasé, jusqu'à la pointe
        (29.4, 2.3), (28.85, 2.24),                               # retour de la pointe, intérieur
        (27.85, 1.42), (28.05, 2.02),                             # ardillon tourné vers le bas (large, lisible)
        (26.75, 2.02), (26.05, 1.86), (25.72, 1.48), (25.85, 1.06),   # fond de l'échancrure
        (26.45, 0.8), (28.25, 0.7),                               # flanc de la dent centrale
        (28.45, 0.5), (29.75, 0.47),                              # cran d'éclair
        (31.2, 0.0)]                                              # pointe centrale
TIP_C = (31.2, 0.0)
TIP_L = {1: (30.25, 2.5), -1: (30.25, -2.5)}
POLY = DEMI + [(a, -b) for a, b in DEMI[::-1][1:]]
FIL_D = DEMI[1:]                                                  # tout sauf la base
FILS = [FIL_D, [(a, -b) for a, b in FIL_D]]
A_MIN, A_MAX = 0.0, TIP_C[0]


def h_fer(a):
    """Demi-épaisseur du plat : 0,80 au croissant (1,60 px), 0,22 aux pointes (0,44 px : losange)."""
    return np.interp(np.asarray(a, float), [23.25, 25.6, 27.5, 31.2], [0.80, 0.74, 0.56, 0.22])


def wb_fer(a):
    return (h_fer(a) - Z_E) / T_BIS


GOUT_C = Gouttiere([(24.05, 0.0), (24.75, 0.07), (25.5, -0.07), (26.25, 0.07), (27.0, -0.06), (27.7, 0.05), (28.25, 0.0)],
                   [0.07, 0.15, 0.16, 0.15, 0.13, 0.11, 0.05])
GOUT_S = {sg: Gouttiere([(24.72, sg * 0.95), (24.84, sg * 1.4), (25.06, sg * 1.8), (25.28, sg * 2.06)], [0.05, 0.12, 0.1, 0.04])
          for sg in (1, -1)}
GOUTS = [GOUT_C, GOUT_S[1], GOUT_S[-1]]


def est_dessous(P):
    """Bande du dessous du croissant (liseré d'or sur les biseaux)."""
    return d_poly(P, [(23.25, 0.62), (23.7, 1.3), (24.3, 2.1), (25.0, 2.72), (25.4, 2.84)]) < 0.9 \
        if False else (d_poly(P, [(23.25, 0.62), (23.7, 1.3), (24.3, 2.1), (25.0, 2.72)]) < 0.55) | \
        (d_poly(P, [(23.25, -0.62), (23.7, -1.3), (24.3, -2.1), (25.0, -2.72)]) < 0.55)


def peint_biseau(chaud):
    def f(P, dE):
        wb = wb_fer(P[..., 0])
        fr = dE / wb
        nz = cellules(P, 2.2, 1.0)[..., None]
        col = lerp(METAL[3], METAL[2], np.clip((fr[..., None] - 0.78) / 0.15, 0, 1)) + nz * 10
        col = np.where((fr < 0.36)[..., None], lerp(METAL[4], METAL[3], np.clip((fr[..., None] - 0.14) / 0.22, 0, 1)) + nz * 6, col)
        cu = (fr >= 0.36) & (fr < 0.57)
        vi = (fr >= 0.57) & (fr < 0.78)
        col[cu] = lerp(col[cu], CUIVRE, 0.85)
        col[vi] = lerp(col[vi], VIOLET, 0.72)
        dess = est_dessous(P)
        od = dess & (fr >= 0.2) & (fr < 0.93)                      # dessous du croissant : biseau d'or
        col[od] = lerp(OR[2], OR[1], np.clip((fr[od, None] - 0.2) / 0.7, 0, 1)) + nz[od] * 10
        col[od & (fr < 0.36)] = OR[3]
        col[fr >= 0.93] = METAL[0]
        em = np.zeros(col.shape, np.float32)
        col[fr < 0.14] = FIL_C
        em[fr < 0.16] = FIL_E
        if chaud:                                                 # chauffé à blanc par la charge (étape lance)
            hot = fr < 0.6
            col[hot] = lerp(col[hot], FIL_C, 0.8)
            em[hot] = (150, 190, 255)
            em[(fr >= 0.6) & (fr < 0.93)] = (60, 70, 150)
        return col, em
    return f


def peint_fil(chaud):
    def f(P):
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + FIL_C
        em = np.zeros_like(col) + (np.array((170, 205, 255.)) if chaud else FIL_E)
        return col, em
    return f


def peint_plat(chaud):
    def f(P, dE):
        wb = wb_fer(P[..., 0])
        nz = cellules(P, 1.6, 2.0)[..., None]
        col = lerp(METAL[2], METAL[1], np.clip((dE[..., None] - wb[..., None] - 0.1) / 0.5, 0, 1) * 0.6) + nz * 16
        col = col + np.zeros(P.shape[:-1] + (3,), np.float32)
        em = np.zeros(col.shape, np.float32)
        if chaud:
            col = lerp(col, METAL[4], 0.35)
            em = em + np.array((40, 52, 120.))
        col[dE < wb + 0.04] = METAL[0]
        for G in GOUTS:
            dg = G.dist(P)
            levre = dg < 0.06
            col[levre] = (190, 208, 255)
            em[levre] = (90, 130, 235) if chaud else (60, 100, 210)
            col[(dg >= 0.06) & (dg < 0.1)] = METAL[0]
            orl = (dg >= 0.13) & (dg < 0.19) & (dE > wb + 0.06)
            col[orl] = OR[2]
            col[orl & (dg < 0.155)] = OR[3]
        return col, em
    return f


FOURCHES = {k: Piece(f"fourche_{k}", POLY, FILS, h_fer, wb_fer, Z_E, peint_biseau(k == "chaude"), peint_plat(k == "chaude"),
                     peint_fil(k == "chaude"), GOUTS) for k in ("froide", "chaude")}

# contrôle : chaque gouttière reste dans le plat (marge entre son bord et le bord des biseaux)
for _i, _G in enumerate(GOUTS):
    _pg = np.array(_G.poly)
    _m = (FOURCHES["froide"].dE(_pg) - wb_fer(_pg[:, 0])).min()
    print(f"gouttière {_i} : marge / biseaux {_m:+.2f} px")
    assert _m > 0.06, "la gouttière mord les biseaux"
_pp = np.array(POLY)
print(f"fourche : {_pp[:, 1].max() * 2:.1f} px de large ; pente {math.degrees(math.atan(T_BIS)):.0f}° ;"
      f" plat au milieu de la dent latérale : {2 * (0.4 - float(wb_fer(28.0))):+.2f} px")


def conception():
    SPECS.clear()
    TILES.clear()
    for k, pc in FOURCHES.items():
        volume(pc)
        for j, G in enumerate(GOUTS):
            gouttiere(pc, G, j, k == "chaude")
    douille()


# Douille : tronc de cône à 8 pans (plaques inclinées, faces découpées par l'alpha au secteur de chaque pan)
D_A0, D_A1, D_R0, D_R1 = 22.05, 23.55, 0.92, 0.74


def douille():
    dr = (D_R1 - D_R0) / (D_A1 - D_A0)
    for k in range(8):
        ph = TAU * k / 8 + TAU / 16
        nn = np.array((0.0, math.cos(ph), math.sin(ph)))
        t = np.array((0.0, -math.sin(ph), math.cos(ph)))
        X = unit(np.array((1.0, 0, 0)) + dr * nn)
        Y = t
        if np.cross(X, Y) @ nn < 0:
            Y = -t
        Z = np.cross(X, Y)
        Ln = (D_A1 - D_A0) * math.sqrt(1 + dr * dr)
        rm = (D_R0 + D_R1) / 2
        c = np.array(((D_A0 + D_A1) / 2, 0, 0)) + rm * nn - Z * (TH / 2)
        sy = 2 * D_R0 * math.tan(math.pi / 8) + 0.16

        def pan(P, ph=ph):
            a = P[..., 0]
            ang = np.arctan2(P[..., 2], P[..., 1])
            dd = np.abs((ang - ph + math.pi) % TAU - math.pi)
            r = np.hypot(P[..., 1], P[..., 2])
            m = dd <= math.pi / 8 + 0.08 / np.maximum(r, 0.3)
            nz = cellules(P[..., :2] * np.array((1.0, 3.0)), 2.2, 7.0 + ph)[..., None]
            col = lerp(METAL[3], METAL[1], np.clip((a[..., None] - D_A0) / (D_A1 - D_A0), 0, 1) * 0.7) + nz * 12
            col = np.where((dd > math.pi / 8 - 0.06)[..., None], METAL[4] * 0.92, col)          # arêtes claires entre les pans
            col = np.where((a < D_A0 + 0.22)[..., None], np.where((a < D_A0 + 0.08)[..., None], OR[3], OR[2]), col)
            zz = np.abs(((a - D_A0) * 2.6 + 0.5 * np.sign(np.sin(ang * 4 + 0.4))) % 1 - 0.5)       # filet d'or en zigzag
            col = np.where(((zz < 0.07) & (a > D_A0 + 0.35) & (a < D_A1 - 0.3))[..., None], OR[2], col)
            return col, np.zeros(col.shape, np.float32), m

        spec("douille", f"douille{k}", c, X, Y, (Ln, sy, TH), {"south": pan})


# ------------------------------------------------------------------ tuiles peintes (hampe, gaine, or, médaillon, foudre)
def g01(W, H):
    yy, xx = np.mgrid[0:H * SS, 0:W * SS]
    return (xx + 0.5) / (W * SS), (yy + 0.5) / (H * SS)


def red(col, W, H):
    im = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = im
    out[..., 3] = 255
    return out


HAMPE_A0, HAMPE_A1 = 1.5, 22.1


def t_hampe(W=330, H=12):
    """u le long de la hampe (a de HAMPE_A0 à HAMPE_A1), v en travers : arête claire, filets d'or en spirale espacés."""
    x, y = g01(W, H)
    q = np.abs(y - 0.5) * 2
    col = METAL[np.clip((3.3 * (1 - q ** 1.3) + 0.8 * (q < 0.16)).astype(int), 0, 4)]
    a = HAMPE_A0 + (HAMPE_A1 - HAMPE_A0) * x
    nz = np.sin(a * 37.0 + y * 3.0) * 4
    col = col + nz[..., None]
    gold = ((a > 5.6) & (a < 6.0)) | ((a > 10.2) & (a < 10.6)) | ((a > 20.1) & (a < 20.5))
    col = np.where(gold[..., None], OR[np.clip((2.6 * (1 - q ** 1.4) + 0.8 * (q < 0.2)).astype(int), 0, 3)], col)
    return red(col, W, H)


def t_gaine(W=120, H=12):
    x, y = g01(W, H)
    q = np.abs(y - 0.5) * 2
    cuir = lerp(np.array((18, 22, 48), np.float32), np.array((52, 62, 112), np.float32), (1 - q ** 1.5)[..., None])
    band = np.mod(x * 12 + y * 0.9, 1) < 0.16
    col = np.where(band[..., None], cuir * 0.55, cuir)
    col = np.where(((x < 0.04) | (x > 0.96))[..., None], OR[2], col)
    return red(col, W, H)


def t_or(W=24, H=12):
    x, y = g01(W, H)
    q = np.abs(y - 0.5) * 2
    return red(OR[np.clip((3.2 * (1 - q ** 1.4) + 0.6 * (q < 0.2)).astype(int), 0, 3)], W, H)


def t_or16(W=24, H=24, sens="u"):
    """Côté d'un carré du tambour à 16 pans : seule la bande centrale est sur le 16-gone, le reste est transparent."""
    a = t_or(W, H) if sens == "v" else np.transpose(t_or(H, W), (1, 0, 2)).copy()
    k = math.tan(math.radians(11.25)) + 0.03
    t = np.abs((np.arange(W if sens == "u" else H) + 0.5) / (W if sens == "u" else H) * 2 - 1)
    hors = t > k
    if sens == "u":
        a[:, hors] = 0
    else:
        a[hors, :] = 0
    return a


def medaillon(N=64, ss=4):
    """Tambour d'or : anneau d'or, fond de métal sombre, trois virgules d'or en spirale (famille de l'épée)."""
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
    a = np.array(im.resize((N, N), Image.LANCZOS))
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


def t_core():
    a = np.zeros((6, 16, 4), np.uint8)
    a[..., :3] = (236, 244, 255)
    a[0, :, :3] = a[5, :, :3] = (96, 146, 255)
    a[..., 3] = 255
    e = a.copy()
    e[..., :3] = (205, 226, 255)
    e[0, :, :3] = e[5, :, :3] = (50, 84, 210)
    return a, e


def t_halo(k):
    a = np.zeros((8, 16, 4), np.uint8)
    for v in range(8):
        d = abs((v + 0.5) / 8 * 2 - 1)
        a[v, :, :3] = np.clip(np.array((8, 7, 30)) + (1 - d) ** 1.4 * np.array((26, 44, 120)) * k, 0, 255)
    a[..., 3] = 255
    return a


def t_crk():
    a = np.zeros((4, 16, 4), np.uint8)
    a[..., :3] = (225, 236, 255)
    a[0, :, :3] = a[3, :, :3] = (120, 150, 255)
    a[..., 3] = 255
    return a


def t_cristal():
    a = t_unie(16, 8, CRIS[3], CRIS[1], 4, bords=CRIS[0])
    e = a.copy()
    e[..., :3] = np.clip(a[..., :3].astype(np.float32) * 0.7, 0, 225).astype(np.uint8)
    return a, e


UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    core, core_e = t_core()
    cri, cri_e = t_cristal()
    conception()
    items = [(n, im, ime) for n, (im, ime) in TILES.items()]
    items += [("hampe", t_hampe(), None), ("gaine", t_gaine(), None), ("or", t_or(), None), ("or16u", t_or16(48, 12, "u"), None),
              ("or16v", t_or16(12, 48, "v"), None), ("medaillon", medaillon(), None), ("core", core, core_e), ("cristal", cri, cri_e),
              ("crk", t_crk(), None), ("sombre", t_unie(32, 8, METAL[2], METAL[1], 3), None)]
    items += [(f"halo{k}", t_halo(m), None) for k, m in enumerate((1.0, 1.4, 1.8))]
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, im, ime in sorted(items, key=lambda it: (-it[1].shape[0], -it[1].shape[1])):
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
    print(f"atlas : {len(items)} tuiles, rempli jusqu'à y = {y + shelf} / {TEX}")
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

# ------------------------------------------------------------------ géométrie (repère de l'objet : a -> +Y, b -> -X, z -> +Z)
Y_BAS, Y_HAUT = -7.5, -7.5 + A_MAX            # même place que le trident vanilla (31 px, centré dans le bloc)
Q = np.array((8.0, Y_BAS - A_MIN, 8.0))
A_PRISE = 16.7                                 # la main du vanilla (objet.affichage_trident)
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def W_(a, b=0.0, z=0.0):
    return Q + np.array((-b, a, z), float)


def Wv(a, b=0.0, z=0.0):
    return np.array((-b, a, z), float)


def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def euler(R):
    """Angles (X, Y, Z) tels que R = Rz Ry Rx (ordre du mod et du renderer), blocage de cardan traité, vérifié."""
    if abs(R[2, 0]) < 0.99999:
        ry = math.asin(-R[2, 0])
        e = (math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0])))
    elif R[2, 0] < 0:
        e = (math.degrees(math.atan2(R[0, 1], R[0, 2])), 90.0, 0.0)
    else:
        e = (math.degrees(math.atan2(-R[0, 1], -R[0, 2])), -90.0, 0.0)
    assert np.allclose(rotm(*e), R, atol=1e-6), "euler"
    return e


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
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def boite(g, name, c, X, Y, sx, sy, sz, faces):
    """Boîte centrée en c (objet), axes X, Y (objet), tailles sx, sy, sz."""
    X = unit(X)
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    cube(g, name, c - (sx / 2, sy / 2, sz / 2), c + (sx / 2, sy / 2, sz / 2), c, euler(R_), faces)


def uvp(tile, part=None, flip=False):
    u0, v0, u1, v1 = UV[tile]
    if part:
        u0, u1 = u0 + (u1 - u0) * part[0], u0 + (u1 - u0) * part[1]
    return [u1, v0, u0, v1] if flip else [u0, v0, u1, v1]


def barre(g, name, a0, a1, r, tile, part=None, caps="or", octo=True):
    """Barre octogonale le long du trident (deux boîtes, la seconde tournée de 45° autour de l'axe) ; u le long de a."""
    lg, lgr = uvp(tile, part), uvp(tile, part, flip=True)
    if caps:
        u0, v0, u1, v1 = UV[caps]
        end = [u0 + 1, v0 + 1, u0 + 1 + min(10, u1 - u0 - 2), v1 - 1]
    else:
        end = CLEAR
    faces = {"south": lg, "north": lgr, "up": lg, "down": lg, "east": end, "west": end}
    c = W_((a0 + a1) / 2)
    boite(g, name, c, Wv(1), Wv(0, 1), a1 - a0, 2 * r, 2 * r, faces)
    if octo:
        Yq = unit(Wv(0, 1) * math.cos(math.pi / 4) + Wv(0, 0, 1) * math.sin(math.pi / 4))
        boite(g, name + "o", c, Wv(1), Yq, a1 - a0 - 0.1, 2 * r * 0.97, 2 * r * 0.97, faces)


def seg(g, name, p, q, w, tile, ov=0.06, roll=45.0):
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = np.array((0, 0, 1.0)) if abs(X[2]) < 0.9 else np.array((1.0, 0, 0))
    Y0 = unit(ref - (ref @ X) * X)
    Z0 = np.cross(X, Y0)
    r = math.radians(roll)
    u0, v0, u1, v1 = UV[tile]
    lg = [u0, v0, u1, v1]
    end = [u0 + 1, v0 + 1, u0 + 3, v0 + 3] if not tile.startswith("halo") else CLEAR
    boite(g, name, (p + q) / 2, X, Y0 * math.cos(r) + Z0 * math.sin(r), float(np.linalg.norm(q - p)) + 2 * ov, w, w,
          {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end})


ROLLS = [45, 18, 62, 33, 51, 9, 74, 27]
_rc = [0]


def trait(g, name, pts, w0, w1, tile):
    n = len(pts) - 1
    for i in range(n):
        roll = ROLLS[_rc[0] % len(ROLLS)]
        _rc[0] += 1
        seg(g, f"{name}{i}", pts[i], pts[i + 1], w0 + (w1 - w0) * i / max(1, n - 1), tile, roll=roll)


def halo_trait(g, name, pts, w, tile):
    for i in range(len(pts) - 1):
        seg(g, f"{name}{i}", pts[i], pts[i + 1], w, tile, ov=0.03, roll=0.0)


def zigzag(pts, n, J, seed, zj=0.0, z0=0.0):
    """Éclair qui suit une polyligne du plan (a, b) : n tronçons, écarts latéraux alternés ; points (a, b, z)."""
    rng = random.Random(seed)
    P = [np.array(p, float) for p in pts]
    ls = np.cumsum([0] + [np.linalg.norm(P[i + 1] - P[i]) for i in range(len(P) - 1)])

    def at(x):
        i = min(np.searchsorted(ls, x, side="right") - 1, len(P) - 2)
        k = (x - ls[i]) / max(ls[i + 1] - ls[i], 1e-9)
        return P[i] + (P[i + 1] - P[i]) * k, unit(P[i + 1] - P[i])

    out, sg = [], rng.choice((-1, 1))
    for i in range(n + 1):
        x = ls[-1] * min(1, max(0, (i + (rng.uniform(-0.25, 0.25) if 0 < i < n else 0)) / n))
        p, d = at(x)
        off = 0 if i in (0, n) else sg * rng.uniform(0.5, 1.0) * J
        sg = -sg
        q = p + np.array((-d[1], d[0])) * off
        out.append((q[0], q[1], z0 + (rng.uniform(-zj, zj) if 0 < i < n else 0)))
    return out


def eclair3d(p, q, n, J, seed, bombe=None):
    """Éclair de p à q (a, b, z) : n tronçons, écarts perpendiculaires alternés ; bombe = flèche (a, b, z) au milieu."""
    rng = random.Random(seed)
    p, q = np.asarray(p, float), np.asarray(q, float)
    d = unit(q - p)
    ref = np.array((0, 0, 1.0)) if abs(d[2]) < 0.9 else np.array((0, 1.0, 0))
    e1 = unit(ref - (ref @ d) * d)
    e2 = np.cross(d, e1)
    out, sg = [], 1
    for i in range(n + 1):
        t = i / n
        o = np.zeros(3) if i in (0, n) else (sg * rng.uniform(0.5, 1.0) * J * e1 + rng.uniform(-0.5, 0.5) * J * e2)
        if bombe is not None:
            o = o + np.asarray(bombe, float) * 4 * t * (1 - t)
        sg = -sg
        out.append(p + (q - p) * t + o)
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
    o = np.array(groups[g]["origin"])
    ids = {i for n in sous_groupes(g) for i in groups[n]["ids"]}
    for e in elements:
        if e["uuid"] in ids:
            for k in ("from", "to", "origin"):
                e[k] = [round(float(o[i] + FOLD * (e[k][i] - o[i])), 4) for i in range(3)]


def poser_specs(cle, g, prefixe=""):
    for sp in SPECS[cle]:
        u_ = {f: (list(UV[sp["faces"][f]]) if f in sp["faces"] else CLEAR) for f in ("north", "south", "east", "west", "up", "down")}
        boite(g, prefixe + sp["nom"], W_(*sp["c"]), Wv(*sp["X"]), Wv(*sp["Y"]), *sp["s"], u_)


# --- partie commune (toujours dessinée) : talon, hampe, gaine, tambour, douille
COMMUN = group("trident_orage", W_(A_PRISE))
uh = lambda a: (a - HAMPE_A0) / (HAMPE_A1 - HAMPE_A0)
G0, G1 = 14.35, 19.05                                       # gaine de cuir à la prise
GAINE = group("gaine", W_(A_PRISE), COMMUN)
barre(GAINE, "gaine", G0, G1, 0.6, "gaine")
for k, a_ in enumerate((G0 + 0.15, A_PRISE, G1 - 0.15)):    # bagues d'or en relief
    barre(GAINE, f"bague{k}", a_ - 0.17, a_ + 0.17, 0.72, "or")
HAMPE = group("hampe", W_(8.0), COMMUN)
barre(HAMPE, "hampe_ar", HAMPE_A0 + 0.05, G0 + 0.1, 0.5, "hampe", part=(uh(HAMPE_A0 + 0.05), uh(G0 + 0.1)))
barre(HAMPE, "hampe_av", G1 - 0.1, HAMPE_A1, 0.48, "hampe", part=(uh(G1 - 0.1), uh(HAMPE_A1)), caps=None)
for k, a_ in enumerate((5.8, 10.4)):                         # bagues d'or de la hampe
    barre(HAMPE, f"bague_h{k}", a_ - 0.14, a_ + 0.14, 0.6, "or")
TALON = group("talon", W_(1.0), COMMUN)
barre(TALON, "talon_or", 1.05, 1.65, 0.66, "or")
barre(TALON, "talon_cri0", 0.75, 1.15, 0.46, "cristal", caps="cristal")    # pointe de cristal (pommeau de la famille)
barre(TALON, "talon_cri1", 0.3, 0.8, 0.3, "cristal", caps="cristal")
barre(TALON, "talon_cri2", 0.0, 0.36, 0.15, "cristal", caps="cristal", octo=False)
TETE = group("tete", W_(21.5), COMMUN)
R_I = 1.32                                                  # tambour à 16 pans sous la douille, médaillons aux deux bouts
A_T0, A_T1 = 20.65, 21.45
for k in range(4):
    th = math.radians(22.5 * k)
    boite(TETE, f"tambour{k}", W_((A_T0 + A_T1) / 2), Wv(0, math.cos(th), math.sin(th)), Wv(0, -math.sin(th), math.cos(th)),
          2 * R_I, 2 * R_I, A_T1 - A_T0 - 0.04, {"north": CLEAR, "south": CLEAR, "east": UV["or16v"], "west": UV["or16v"],
                                                 "up": UV["or16u"], "down": UV["or16u"]})
MR = R_I / math.cos(math.radians(11.25)) + 0.01
for sg, a_ in ((1, A_T1 - 0.12), (-1, A_T0 + 0.12)):
    boite(TETE, f"medaillon{'pm'[sg < 0]}", W_(a_), Wv(0, 1), Wv(0, 0, 1), 2 * MR, 2 * MR, 0.3,
          {**{f: CLEAR for f in ("north", "south", "east", "west", "up", "down")},
           **({"south": uvp("medaillon")} if sg > 0 else {"north": uvp("medaillon", flip=True)})})
barre(TETE, "collet_bas", 20.35, 20.7, 0.72, "or")
barre(TETE, "collet", 21.4, 22.1, 0.98, "or")
barre(TETE, "douille_ame", 22.0, 23.45, 0.55, "sombre", caps="sombre")
poser_specs("douille", TETE)
EMIT = group("emit_mc_electric_spark", W_(29.5), COMMUN)    # gerbe au lancer, entre les dents
group("ctrl_emit", W_(29.5), EMIT)

# --- étapes (groupes racine, guide 14)
ETAPES, GAINES = {}, {}
FOUDRES = [zigzag(G.slit, max(4, int(round(len(G.slit) * 1.6))), 0.04, 17 + 5 * j) for j, G in enumerate(GOUTS)]
for niv, nm in enumerate(NIVS):
    racine = group(objet.etape(nm, "trident"), W_(A_PRISE))
    ETAPES[nm] = racine
    gf = group(f"fourche_{nm}", W_(24.0), racine)
    poser_specs("fourche_chaude" if nm == "lance" else "fourche_froide", gf, f"{nm[0]}_")
    fo = group(f"foudre_{nm}", W_(24.5), gf)
    GAINES[nm] = []
    for j, pts2 in enumerate(FOUDRES):
        for zs in (1, -1):
            trait(fo, f"eclair{j}{'pm'[zs < 0]}", [W_(x, y, zs * 0.17) for x, y, _ in pts2], 0.28 if j == 0 else 0.22, 0.2, "core")
        gg = group(f"add_gaine_{nm}_{j}", W_(*pts2[0][:2]), fo)
        ctrl(gg)
        for i in range(len(pts2) - 1):
            am = (pts2[i][0] + pts2[i + 1][0]) / 2
            seg(gg, f"gaine{i}", W_(*pts2[i][:2]), W_(*pts2[i + 1][:2]), min(0.78, 2 * float(h_fer(am)) - 0.16), f"halo{niv}",
                ov=0.04, roll=0.0)
        GAINES[nm].append(gg)

TIP3 = {"c": np.array((*TIP_C, 0.0)), "g": np.array((*TIP_L[1], 0.0)), "d": np.array((*TIP_L[-1], 0.0))}

# leve : arcs qui sautent entre les pointes (bombés vers l'avant), étincelles aux trois pointes
ARCS_LEVE = []
for j, (k0, k1, sd) in enumerate((("c", "g", 11), ("c", "d", 23), ("g", "d", 37))):
    p, q = TIP3[k0] + np.array((0.12, 0, 0)), TIP3[k1] + np.array((0.12, 0, 0))
    bom = np.array((0.9 if j < 2 else 1.9, 0.0, 0.25 * (1 if j % 2 else -1)))
    g = group(f"add_arc_leve{j}", W_(*((p + q) / 2)), ETAPES["leve"])
    ctrl(g)
    pts = eclair3d(p, q, 5 if j < 2 else 8, 0.2, sd, bombe=bom)
    trait(g, "a", [W_(*x) for x in pts], 0.2, 0.14, "crk")
    halo_trait(g, "h", [W_(*x) for x in pts], 0.5, "halo2")
    ARCS_LEVE.append(g)
ETIN = group("add_etincelles_leve", W_(*TIP_C), ETAPES["leve"])
ctrl(ETIN)
for nmp, tp in TIP3.items():
    for j, dv in enumerate(((1, 0.45, 0.3), (1, -0.45, -0.3))):
        dvec = unit(dv)
        pts = eclair3d(tp + dvec * 0.1, tp + dvec * 0.9, 3, 0.1, 300 + j + 7 * len(nmp) + int(tp[1] * 10))
        trait(ETIN, f"e{nmp}{j}", [W_(*x) for x in pts], 0.16, 0.1, "crk")

# lance (trident en vol) : éclairs le long des trois dents et traînée vers l'arrière le long de la hampe
VOL = []
for j, (sg, seed) in enumerate(((1, 51), (-1, 77))):
    out_ = [(a, sg * (b + 0.24)) for a, b in DEMI[3:8]]
    pts = zigzag(out_, 7, 0.16, seed, zj=0.12)
    g = group(f"add_vol_dent{'gd'[j]}", W_(27.0, sg * 2.6), ETAPES["lance"])
    ctrl(g)
    trait(g, "e", [W_(*p) for p in pts], 0.22, 0.14, "crk")
    halo_trait(g, "h", [W_(*p) for p in pts], 0.5, "halo2")
    VOL.append(g)
for j, (zs, seed) in enumerate(((1, 91), (-1, 97))):
    g = group(f"add_vol_trainee{j}", W_(14.0), ETAPES["lance"])
    ctrl(g)
    pts = eclair3d((22.0, 0.75 * zs, 0.45 * zs), (6.0, 0.9 * zs, -0.4 * zs), 10, 0.25, seed)
    trait(g, "t", [W_(*p) for p in pts], 0.22, 0.12, "crk")
    halo_trait(g, "h", [W_(*p) for p in pts], 0.48, "halo2")
    VOL.append(g)

# événements (dans la partie commune, repliés à 1/10 sur un pivot caché dans le métal de la fourche)
PIV = W_(25.0)
# item_idle : arc en retour entre la dent centrale et une dent latérale (deux formes)
IDLE = []
for j, (k1, sd) in enumerate((("g", 61), ("d", 67))):
    g = group(f"add_idle_arc{j}", PIV, COMMUN)
    ctrl(g)
    p, q = TIP3["c"] + np.array((0.1, 0, 0)), TIP3[k1] + np.array((0.1, 0, 0))
    trait(g, "a", [W_(*x) for x in eclair3d(p, q, 5, 0.18, sd, bombe=(0.7, 0, 0.2))], 0.18, 0.12, "crk")
    replier(g)
    IDLE.append(g)
# event_select : la foudre tombe sur la dent centrale, puis saute aux deux dents latérales
SEL = {}
for nm_f, seed, dv in (("a", 5, (1, 0.25, 0.3)), ("b", 9, (1, -0.3, -0.2))):
    g = group(f"add_sel_frappe_{nm_f}", PIV, COMMUN)
    ctrl(g)
    pts = eclair3d(TIP3["c"] + unit(dv) * 4.5, TIP3["c"] + np.array((0.05, 0, 0)), 6, 0.35, seed)
    trait(g, "f", [W_(*x) for x in pts], 0.28, 0.16, "crk")
    replier(g)
    SEL["frappe_" + nm_f] = g
for k1, sd in (("g", 71), ("d", 73)):
    g = group(f"add_sel_saut_{k1}", PIV, COMMUN)
    ctrl(g)
    pts = eclair3d(TIP3["c"] + np.array((0.1, 0, 0)), TIP3[k1] + np.array((0.1, 0, 0)), 5, 0.2, sd, bombe=(1.1, 0, 0))
    trait(g, "s", [W_(*x) for x in pts], 0.2, 0.14, "crk")
    replier(g)
    SEL["saut_" + k1] = g
# event_release : décharge des trois pointes vers l'avant (deux formes, fourches)
REL = []
for nm_f, seed in (("a", 31), ("b", 47)):
    g = group(f"add_tir_{nm_f}", PIV, COMMUN)
    ctrl(g)
    rng = random.Random(seed)
    for nmp, tp in TIP3.items():
        Ln = 5.0 if nmp == "c" else 3.6
        q = tp + np.array((Ln, tp[1] * 0.35, rng.uniform(-0.5, 0.5)))
        pts = eclair3d(tp + np.array((0.1, 0, 0)), q, 6 if nmp == "c" else 4, 0.3, seed + ord(nmp))
        trait(g, f"t{nmp}", [W_(*x) for x in pts], 0.3, 0.14, "crk")
        if nmp == "c":
            for kk in (2, 4):
                dd = unit(np.array((1.0, rng.choice((-1, 1)) * 0.8, rng.uniform(-0.4, 0.4))))
                trait(g, f"fk{kk}_", [W_(*x) for x in eclair3d(pts[kk], pts[kk] + dd * 1.4, 3, 0.15, seed + kk)], 0.16, 0.1, "crk")
    replier(g)
    REL.append(g)


def coins(filtre=None):
    Pp = []
    for e in elements:
        if filtre is not None and e["uuid"] not in filtre:
            continue
        f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
        R = rotm(*e.get("rotation", (0, 0, 0)))
        for i in range(8):
            Pp.append(R @ (np.array([(f, t)[(i >> k) & 1][k] for k in range(3)]) - o) + o)
    return np.array(Pp)


outliner = [bone_node(COMMUN)] + [bone_node(ETAPES[n]) for n in NIVS]


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


def restrike(Pp, pr, c2):
    return (f"v.u=q.life_time/{Pp:g}+{c2:.3g};v.s={H('math.floor(v.u)')};v.u=math.mod(v.u,1)*{Pp:g};"
            f"v.r=(v.s<{pr:g})*((v.u<0.07)+(v.u>0.13)*(v.u<0.19)+(v.u>0.26)*(v.u<0.32));")


def flick(R, c):
    return f"v.h={H(f'math.floor(q.life_time*{R:g}+{c:.3g})')};"


def onoff(intervalles, Ln, on=1.0, off=-1.0, r=0.012):
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


EVENT_GROUPS = IDLE + list(SEL.values()) + REL
P_RS = 5.5

# item_idle (8 s) : la foudre des gouttières grésille ; arc en retour entre deux pointes, au hasard (une forme par côté).
idle = anim("item_idle", 8.0)
for k, g in enumerate(GAINES["repos"]):
    piste_ctrl(idle, g, [kf("position", 0, chk(flick(9, 0.13 + 0.31 * k) + "-0.42+0.22*(v.h<0.3)-0.25*(v.h>0.82)"))])
for j, g in enumerate(IDLE):
    deplier(idle, g)
    piste_ctrl(idle, g, [kf("position", 0, chk(restrike(P_RS, 0.6, 0.37) + f"v.c={H('math.floor(v.u/1000+q.life_time/5.5+0.37)')};"
                                             + f"v.r*({'v.c<0.5' if j == 0 else 'v.c>=0.5'})-1"))])
for g in list(SEL.values()) + REL:
    piste_ctrl(idle, g, [kf("position", 0, -1)])
piste(idle, "ctrl_emit", [kf("position", 0, -1)])

# item_gui : inventaire calme.
gui = anim("item_gui", 4.0)
for g in GAINES["repos"]:
    piste_ctrl(gui, g, [kf("position", 0, -0.35)])
for g in EVENT_GROUPS:
    piste_ctrl(gui, g, [kf("position", 0, -1)])
piste(gui, "ctrl_emit", [kf("position", 0, -1)])

# item_use (0,5 s, étape leve) : arcs entre les pointes qui vacillent de plus en plus vite, fourche qui frémit.
use = anim("item_use", 0.5)
piste(use, ETAPES["leve"], [kf("rotation", 0, 0, 0, "math.sin(q.anim_time*360*13)*0.6*q.use_progress")])
for i, g in enumerate(ARCS_LEVE):
    piste_ctrl(use, g, [kf("position", 0, chk(flick(8 + 6 * i, 0.21 + 0.4 * i)
                                               + "-0.6+0.6*math.min(q.use_progress*1.5,1)-0.9*(v.h<0.22)+0.3*(v.h>0.85)"))])
piste_ctrl(use, ETIN, [kf("position", 0, chk(flick(15, 0.5) + "-1+1.3*(v.h>0.45)*math.min(q.use_progress*2,1)"))])
for k, g in enumerate(GAINES["leve"]):
    piste_ctrl(use, g, [kf("position", 0, chk(flick(10, 0.07 + 0.29 * k) + "-0.4+0.5*q.use_progress-0.3*(v.h<0.25)"))])
for g in EVENT_GROUPS:
    piste_ctrl(use, g, [kf("position", 0, -1)])
piste(use, "ctrl_emit", [kf("position", 0, -1)])

# event_release (0,6 s) : décharge des trois pointes vers l'avant, gerbe, un son.
L_REL = 0.6
rel = anim("event_release", L_REL, "once")
deplier(rel, REL[0])
deplier(rel, REL[1])
piste_ctrl(rel, REL[0], onoff([(0.0, 0.06), (0.14, 0.18), (0.28, 0.31)], L_REL))
piste_ctrl(rel, REL[1], onoff([(0.06, 0.12), (0.21, 0.25)], L_REL))
piste(rel, "ctrl_emit", [kf("position", t, 6 * bump(t, 0.0, 0.02, 0.1, 0.18) - 1) for t in np.round(np.linspace(0, 0.3, 16), 4)]
      + [kf("position", L_REL, -1)])

# event_select (0,7 s) : la foudre frappe la dent centrale, puis saute aux deux dents latérales.
L_SEL = 0.7
sel = anim("event_select", L_SEL, "once")
for g in SEL.values():
    deplier(sel, g)
piste_ctrl(sel, SEL["frappe_a"], onoff([(0.0, 0.07), (0.15, 0.19)], L_SEL))
piste_ctrl(sel, SEL["frappe_b"], onoff([(0.08, 0.13)], L_SEL))
piste_ctrl(sel, SEL["saut_g"], onoff([(0.13, 0.21), (0.3, 0.34)], L_SEL))
piste_ctrl(sel, SEL["saut_d"], onoff([(0.16, 0.24), (0.36, 0.4)], L_SEL))
for k, g in enumerate(GAINES["repos"]):
    t0 = 0.14 + 0.05 * (k % 2)
    piste_ctrl(sel, g, [kf("position", t, -0.6 * (1 - sm(t, 0.0, 0.1)) * (t < t0) + (1.0 * bump(t, t0, t0 + 0.04, t0 + 0.12, t0 + 0.4)
                                                                                    - 0.42 * sm(t, t0 + 0.12, t0 + 0.4)) * (t >= t0))
                        for t in np.round(np.linspace(0, L_SEL, 29), 4)])

# overlay_vol (1 s) : les éclairs de l'étape lance grésillent (trident en vol ; ces groupes ne sont dessinés qu'en vol).
ov = anim("overlay_vol", 1.0)
for i, g in enumerate(VOL):
    piste_ctrl(ov, g, [kf("position", 0, chk(flick(11 + 3 * i, 0.17 + 0.23 * i) + "-0.9*(v.h<0.3)+0.2*(v.h>0.8)"))])
for k, g in enumerate(GAINES["lance"]):
    piste_ctrl(ov, g, [kf("position", 0, chk(flick(9, 0.4 + 0.3 * k) + "-0.2*(v.h<0.3)"))])

ANIMS = [idle, gui, use, rel, sel, ov]

# ------------------------------------------------------------------ écriture
assert 150 <= len(elements) <= 3000, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
AFFICHAGE = objet.affichage("trident", **objet.affichage_trident(Y_BAS, Y_HAUT),
                            gui={"rotation": [0, 0, -45], "translation": [0, 0, 0], "scale": [0.52, 0.52, 0.52]})
model = objet.modele(NOM, "trident", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, embarquer_sons, cle_son
limiter_sons(model)
embarquer_sons(model, {"decharge_trident": "sons/decharge_trident.ogg"})
# Un seul son, au lancer (event_release) : tools/sons.py ne connaît pas encore les événements d'objet, on le pose après.
rel["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "decharge_trident")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


_P = coins()
print("Display :", json.dumps({k: AFFICHAGE[k] for k in ("thirdperson_righthand", "firstperson_righthand", "gui")}))
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print("boîte :", _P.min(0).round(2).tolist(), "->", _P.max(0).round(2).tolist())
