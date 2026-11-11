"""Arc de l'orage : skin d'objet (guide 14) pour tous les arcs du joueur, ensemble Orage (thème Éléments). Design original.
Écrit skin_arc_orage.png, skin_arc_orage_e.png et .build/skin_arc_orage_brut.bbmodel à côté de ce script.

Famille (.claude/styles/orage.md) : ailes_orage v7 (aile de faucon en lames d'acier forgé), skin_epee_orage (recette du vrai
volume, validée en jeu), pioche, hache, pelle, houe. Langage repris : acier d'orage bleu-noir martelé, fil poli clair + _e,
bande de revenu cuivre puis violet, liseré d'or, âme de foudre couchée dans une gouttière, tambour d'or aux trois virgules,
fusée de cuir bleu nuit entre bagues d'or, pointe de cristal.
Silhouette propre : chaque branche est une **aile de faucon repliée** en deux os, comme une vraie aile : le **bras** (large,
bord d'attaque lisse côté dos de l'arc, trois rémiges en dents côté corde) et la **main** (une primaire longue à pointe en
biseau, recourbée vers l'avant : la recourbure d'un arc recourbé), articulés au **poignet**, un petit tambour d'or.
Poignée défléchie : prise de cuir bleu nuit entre bagues d'or, fenêtre de tir décalée et repose-flèche d'or, tambour aux
trois virgules sur le montant haut, logements chanfreinés à axe d'or où pivotent les bras, stabilisateur de cristal.
Vrai volume (recette .claude/references/objets/volume-3d.md, retour en jeu du 2026-11-08 14 h 22 « c'est des couches ») :
bras et main = plaques biseautées fermées (biseaux en cubes inclinés à pente unique par pièce, 52° sur le bras pour garder la
place de la gouttière, 40° sur la main ; plats inclinés qui suivent l'amincissement : bras 1,44 → 1,00 px, main 0,94 → 0,48 px
vers la pointe), faces échantillonnées texel par texel et découpées par l'alpha, recouvrement 0,08 ; gouttière creusée en
zigzag dans le bras (parois + fond) où la foudre est couchée. Pointe de flèche = petite plaque biseautée (losange).
Étapes (guide 14, `.claude/references/objets/arcs.md`) : la même branche (mêmes tuiles) reposée par étape : l'aile se replie
(bras qui recule, main qui se déroule), corde en V vers le point d'encoche, flèche d'acier encochée de plus en plus loin.
La corde se charge : `repos` corde claire ; `bande_1` arcs autour du point d'encoche ; `bande_2` sur les deux tiers de la
corde, gaine bleue ; `bande_3` toute la corde, fourches aux poupées, foudre qui gaine la flèche, pointe chauffée à blanc.
Repère (comme bow.png vu de +Z) : flèche vers le HAUT À GAUCHE (S_), branches le long de H_, poing en (5, 10, 8) (Display
vanilla item/bow), comme skin_arc_givre.

Objet vivant (guide 14), sobre :
- item_idle (8 s) : la foudre des gouttières grésille (Molang), arc en retour toutes les 3 à 8 s avec une petite étincelle à
  la pointe de l'aile haute ;
- item_gui : gouttières calmes ;
- item_use (0,5 s) : l'arc frémit avec la tension (q.use_progress), les arcs de la corde et la gaine vacillent, plus vifs ;
- event_enter_bande_3 (0,35 s) : deux arcs sautent des poignets à la pointe de la flèche (charge complète) ;
- event_release (0,7 s) : la flèche part dans une décharge (deux formes d'éclair le long de la ligne de tir, fourches), corde
  qui vibre, ailes qui frissonnent, gerbe emit_mc_electric_spark (ctrl_emit) ; **seul son** (embarqué, original :
  decharge_arc) ;
- event_select (0,7 s) : la foudre frappe le tambour, puis court le long des deux ailes jusqu'aux pointes.
Éclairs des événements **repliés à 1/10 sur un pivot caché dans le métal** et dépliés par `scale` ×10 par une seule
animation chacun (échelles superposées : aucune).
Fonctions avancées : add_, ctrl_alpha, ctrl_emit, emit_mc_electric_spark, scale animé, calque _e, animations d'objet
(item_idle, item_gui, item_use, event_enter_bande_3, event_release, event_select), Molang (q.life_time, q.use_progress,
q.anim_time), son embarqué. À juger en jeu : event_release et son son (pas encore vérifiés par le développeur), lecture des
ailes par la tranche et dans la case, scale et ctrl_alpha sur un objet.
"""
import base64, io, json, math, os, random, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image, ImageDraw

NOM = "skin_arc_orage"
TEX = 512
TAU = 2 * math.pi
FOLD = 0.1                      # éclairs repliés sur leur pivot au repos

METAL = np.array([(22, 24, 36), (46, 52, 72), (70, 78, 104), (112, 122, 154), (170, 182, 214)], np.float32)
OR = np.array([(130, 90, 30), (176, 128, 44), (220, 170, 60), (255, 230, 140)], np.float32)
CRIS = np.array([(40, 40, 120), (70, 90, 200), (130, 160, 255), (190, 208, 255), (232, 240, 255)], np.float32)
CUIR = np.array([(18, 20, 38), (34, 40, 70), (52, 62, 104)], np.float32)
CUIVRE = np.array((196, 118, 64), np.float32)
VIOLET = np.array((112, 88, 172), np.float32)
FIL_C = np.array((236, 244, 255), np.float32)
FIL_E = np.array((110, 150, 235), np.float32)


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
    return v / np.linalg.norm(v)


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

    def __init__(self, nom, poly, fils, h, wb, ze, peint_biseau, peint_plat, peint_fil, gout=None):
        self.nom, self.poly, self.h, self.wb, self.ze = nom, poly, h, wb, ze
        self.segs = [s for f in fils for s in subdiv(f)]
        self.peint_biseau, self.peint_plat, self.peint_fil, self.gout = peint_biseau, peint_plat, peint_fil, gout
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


def spec(cle, nom, c, X, Y, s, peintures, dens=DF):
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
    SPECS.setdefault(cle, []).append({"nom": nom, "c": np.asarray(c, float), "X": X, "Y": Y, "s": s, "faces": faces})


def volume(pc):
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
            if pc.gout is not None:
                m &= ~pc.gout.dedans(P2)
            col, em = pc.peint_plat(P2, dE)
            return col, em, m

        spec(pc.nom, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, ((a1 - a0) * math.sqrt(1 + sl * sl), b1 - b0, TH), {"south": plat})


def gouttiere(pc):
    """Fond (âme de 0,32 px où repose la foudre) + parois verticales le long des deux bords, sur chaque face."""
    G = pc.gout
    pa = np.array(G.poly)
    a0, a1, b0, b1 = pa[:, 0].min() - 0.15, pa[:, 0].max() + 0.15, pa[:, 1].min() - 0.15, pa[:, 1].max() + 0.15

    def fond(P):
        P2 = P[..., :2]
        m = G.dedans(P2) | (G.dist(P2) < 0.1)
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + np.array((16, 18, 34), np.float32) + cellules(P2, 3.0, 5.0)[..., None] * 6
        em = np.zeros_like(col) + np.array((14, 22, 70), np.float32)
        return col, em, m

    spec(pc.nom, f"{pc.nom}_fond", ((a0 + a1) / 2, (b0 + b1) / 2, 0.0), (1, 0, 0), (0, 1, 0), (a1 - a0, b1 - b0, 2 * Z_FOND),
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
                col[lv] = (190, 208, 255)
                em[lv] = (60, 100, 210)
                return col, em, np.ones(P.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zc)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec(pc.nom, f"{pc.nom}_paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


# ------------------------------------------------------------------ dessin des pièces (coordonnées locales a, b)
# Bras : a = 0 au pivot du logement, a = LA au poignet ; b > 0 côté corde (ventre, rémiges en dents), b < 0 côté dos (bord
# d'attaque lisse). Main : a = 0 au poignet, pointe en biseau vers le dos.
LA = 3.7
ARM_DOS = [(3.9, -0.55), (3.0, -0.95), (1.6, -1.25), (0.3, -1.28), (-0.45, -1.2)]
ARM_VENTRE = [(-0.45, 1.0), (1.15, 1.6), (1.0, 1.02), (2.25, 1.38), (2.1, 0.88), (3.2, 1.05), (3.05, 0.62), (3.9, 0.5)]
ARM = ARM_VENTRE + ARM_DOS
DENTS = [(1.15, 1.6), (2.25, 1.38), (3.2, 1.05)]
SLIT_ARM = [(0.45, 0.02), (1.15, -0.16), (1.85, 0.12), (2.55, -0.12), (3.3, 0.06)]
GW_ARM = [0.08, 0.22, 0.24, 0.22, 0.08]
GOUT_ARM = Gouttiere(SLIT_ARM, GW_ARM)

LH = 3.45
TIPH = (3.45, -0.22)
MAIN_VENTRE = [(-0.3, 0.54), (1.4, 0.5), (2.3, 0.42), (2.95, 0.2), TIPH]
MAIN_DOS = [TIPH, (2.75, -0.42), (1.5, -0.52), (-0.3, -0.56)]
MAIN = MAIN_VENTRE[:-1] + MAIN_DOS
NOCK = (2.6, 0.18)                # poupée : la corde s'attache là, côté ventre


def h_arm(a):
    return 0.72 + (0.50 - 0.72) * np.clip((np.asarray(a, float) + 0.45) / 4.35, 0, 1)


T_ARM = 1.28                      # 52° : le bras garde un plat assez large pour la gouttière


def wb_arm(a):
    return (h_arm(a) - Z_E) / T_ARM


def h_main(a):
    return 0.47 + (0.24 - 0.47) * np.clip((np.asarray(a, float) + 0.3) / 3.75, 0, 1)


T_MAIN = 0.85                     # 40°


def wb_main(a):
    return (h_main(a) - Z_E) / T_MAIN


def peint_biseau_acier(wbf):
    def f(P, dE):
        wb = wbf(P[..., 0])
        fr = dE / wb
        nz = cellules(P, 2.2, 1.0)[..., None]
        col = lerp(METAL[3], METAL[2], np.clip((fr[..., None] - 0.78) / 0.15, 0, 1)) + nz * 10
        col = np.where((fr < 0.36)[..., None], lerp(METAL[4], METAL[3], np.clip((fr[..., None] - 0.14) / 0.22, 0, 1)) + nz * 6, col)
        cu = (fr >= 0.36) & (fr < 0.57)
        vi = (fr >= 0.57) & (fr < 0.78)
        col[cu] = lerp(col[cu], CUIVRE, 0.85)
        col[vi] = lerp(col[vi], VIOLET, 0.72)
        col[fr >= 0.93] = METAL[0]
        em = np.zeros(col.shape, np.float32)
        col[fr < 0.14] = FIL_C
        em[fr < 0.16] = FIL_E
        return col, em
    return f


def peint_fil(P):
    col = np.zeros(P.shape[:-1] + (3,), np.float32) + FIL_C
    em = np.zeros_like(col) + FIL_E
    return col, em


def peint_plat_bras(P, dE):
    wb = wb_arm(P[..., 0])
    nz = cellules(P, 1.6, 2.0)[..., None]
    col = lerp(METAL[2], METAL[1], np.clip((dE[..., None] - wb[..., None] - 0.1) / 0.5, 0, 1) * 0.6) + nz * 16
    # rémiges : une séparation sombre + un reflet de la gouttière vers chaque dent (on lit des plumes repliées)
    for k, (ta, tb) in enumerate(DENTS):
        p0 = np.array((ta - 0.85, 0.0))
        p1 = np.array((ta - 0.06, tb - 0.12))
        ab = p1 - p0
        t = np.clip(((P - p0) @ ab) / (ab @ ab), 0, 1)
        dd = np.linalg.norm(P - (p0 + t[..., None] * ab), axis=-1)
        sep = (dd < 0.045) & (P[..., 1] > 0.18)
        col[sep] = METAL[0]
        rf = (dd >= 0.045) & (dd < 0.11) & (P[..., 1] > 0.18) & ((P - p0) @ np.array((ab[1], -ab[0])) < 0)
        col[rf] = lerp(col[rf], METAL[4], 0.45)
    col[dE < wb + 0.04] = METAL[0]
    em = np.zeros(col.shape, np.float32)
    dg = GOUT_ARM.dist(P)
    levre = dg < 0.06
    col[levre] = (190, 208, 255)
    em[levre] = (60, 100, 210)
    col[(dg >= 0.06) & (dg < 0.11)] = METAL[0]
    orl = (dg >= 0.16) & (dg < 0.23) & (dE > wb + 0.08)
    col[orl] = OR[2]
    col[orl & (dg < 0.19)] = OR[3]
    return col, em


def peint_plat_main(P, dE):
    wb = wb_main(P[..., 0])
    nz = cellules(P, 1.8, 6.0)[..., None]
    col = lerp(METAL[2], METAL[1], 0.35) + nz * 16 + np.zeros(P.shape[:-1] + (3,), np.float32)
    em = np.zeros(col.shape, np.float32)
    # rachis de la primaire : filet de foudre (clair + _e) bordé d'or, de la base à 85 % de la longueur
    ra = (np.abs(P[..., 1] - (-0.04 + 0.03 * P[..., 0])) < 0.055) & (P[..., 0] > 0.15) & (P[..., 0] < 2.75)
    ro = (np.abs(P[..., 1] - (-0.04 + 0.03 * P[..., 0])) < 0.11) & (P[..., 0] > 0.1) & (P[..., 0] < 2.8) & ~ra
    col[ro] = OR[2]
    col[ra] = (205, 222, 255)
    em[ra] = (70, 110, 225)
    col[dE < wb + 0.04] = METAL[0]
    return col, em


ARM_P = Piece("bras", ARM, [ARM_VENTRE, ARM_DOS], h_arm, wb_arm, Z_E, peint_biseau_acier(wb_arm), peint_plat_bras, peint_fil,
              gout=GOUT_ARM)
MAIN_P = Piece("main", MAIN, [MAIN_VENTRE, MAIN_DOS], h_main, wb_main, Z_E, peint_biseau_acier(wb_main), peint_plat_main,
               peint_fil)

# Pointe de flèche : losange biseauté (a le long de la flèche, b dans le plan de l'arc)
PT_POLY = [(0.0, 0.2), (0.45, 0.6), (1.85, 0.0), (0.45, -0.6), (0.0, -0.2)]
PT_FILS = [[(0.0, 0.2), (0.45, 0.6), (1.85, 0.0), (0.45, -0.6), (0.0, -0.2)]]


def h_pt(a):
    return 0.3 + (0.12 - 0.3) * np.clip(np.asarray(a, float) / 1.85, 0, 1)


ZE_PT = 0.06


def wb_pt(a):
    return (h_pt(a) - ZE_PT) / 0.85


def peint_plat_pt(chaud):
    def f(P, dE):
        col = lerp(METAL[3], METAL[2], 0.4) + cellules(P, 2.4, 8.0)[..., None] * 12 + np.zeros(P.shape[:-1] + (3,), np.float32)
        em = np.zeros(col.shape, np.float32)
        ar = np.abs(P[..., 1]) < 0.05
        col[ar] = METAL[4] if not chaud else FIL_C
        if chaud:
            em[ar] = FIL_E
        col[dE < wb_pt(P[..., 0]) + 0.03] = METAL[0]
        return col, em
    return f


def peint_biseau_pt(chaud):
    base = peint_biseau_acier(wb_pt)

    def f(P, dE):
        col, em = base(P, dE)
        if chaud:                                          # pointe chauffée à blanc par la charge
            fr = dE / wb_pt(P[..., 0])
            hot = fr < 0.55
            col[hot] = FIL_C
            em[hot] = (150, 190, 255)
        return col, em
    return f


PT_FROID = Piece("pointe", PT_POLY, PT_FILS, h_pt, wb_pt, ZE_PT, peint_biseau_pt(False), peint_plat_pt(False), peint_fil)
PT_CHAUD = Piece("pointe_ch", PT_POLY, PT_FILS, h_pt, wb_pt, ZE_PT, peint_biseau_pt(True), peint_plat_pt(True), peint_fil)


def conception():
    SPECS.clear()
    TILES.clear()
    volume(ARM_P)
    gouttiere(ARM_P)
    volume(MAIN_P)
    volume(PT_FROID)
    volume(PT_CHAUD)


# ------------------------------------------------------------------ textures simples
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


def poignet_tile(N=32, ss=4):
    """Face du poignet : disque d'or, anneau clair, un œil de cristal au centre (_e à part)."""
    M = N * ss
    im = Image.new("RGBA", (M, M), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, M - 1, M - 1), fill=tuple(int(v) for v in OR[1]) + (255,))
    d.ellipse((M * 0.1, M * 0.1, M * 0.9, M * 0.9), fill=tuple(int(v) for v in OR[3]) + (255,))
    d.ellipse((M * 0.18, M * 0.18, M * 0.82, M * 0.82), fill=tuple(int(v) for v in METAL[1]) + (255,))
    d.ellipse((M * 0.33, M * 0.33, M * 0.67, M * 0.67), fill=tuple(int(v) for v in CRIS[3]) + (255,))
    d.ellipse((M * 0.42, M * 0.38, M * 0.55, M * 0.5), fill=tuple(int(v) for v in CRIS[4]) + (255,))
    im = im.resize((N, N), Image.LANCZOS)
    a = np.array(im)
    a[..., 3] = (a[..., 3] > 128) * 255
    a[a[..., 3] == 0] = 0
    e = np.zeros_like(a)
    yy, xx = np.mgrid[0:N, 0:N]
    rr = np.hypot(xx + 0.5 - N / 2, yy + 0.5 - N / 2) / (N / 2)
    on = rr < 0.34
    e[on, :3] = (120, 160, 240)
    e[on, 3] = 255
    return a, e


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


def t_corde():
    """Corde au repos : fil d'acier clair tressé, une lueur bleue faible (_e)."""
    a = np.zeros((6, 24, 4), np.uint8)
    xx = np.arange(24)
    for v in range(6):
        k = ((xx + v * 2) % 6) < 3
        a[v, :, :3] = np.where(k[:, None], (200, 214, 240), (150, 166, 204))
    a[0, :, :3] = a[5, :, :3] = (90, 104, 150)
    a[..., 3] = 255
    e = np.zeros_like(a)
    e[1:5, :, :3] = (40, 60, 130)
    e[1:5, :, 3] = 255
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


def t_penne(W=48, H=16, ss=4):
    """Penne d'empennage (demi-plume vue de côté, découpée par l'alpha) : acier bleu, bord d'or, barbes."""
    M, Nn = W * ss, H * ss
    im = Image.new("RGBA", (M, Nn), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    poly = [(0, Nn - 1), (M * 0.12, Nn * 0.15), (M * 0.55, 0), (M * 0.98, Nn * 0.25), (M - 1, Nn - 1)]
    d.polygon(poly, fill=tuple(int(v) for v in OR[2]) + (255,))
    inner = [(M * 0.05, Nn - 1), (M * 0.15, Nn * 0.32), (M * 0.55, Nn * 0.17), (M * 0.93, Nn * 0.38), (M * 0.95, Nn - 1)]
    d.polygon(inner, fill=tuple(int(v) for v in METAL[2]) + (255,))
    for k in range(7):
        x = M * (0.18 + 0.11 * k)
        d.line([(x, Nn - 1), (x + M * 0.07, Nn * 0.3)], fill=tuple(int(v) for v in METAL[1]) + (255,), width=ss)
    im = im.resize((W, H), Image.LANCZOS)
    a = np.array(im)
    a[..., 3] = (a[..., 3] > 110) * 255
    a[a[..., 3] == 0] = 0
    return a


# ------------------------------------------------------------------ atlas
UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    core, core_e = t_core()
    cri, cri_e = t_cristal()
    crd, crd_e = t_corde()
    pg, pg_e = poignet_tile()
    conception()
    items = [(n, im, ime) for n, (im, ime) in TILES.items()]
    items += [("medaillon", medaillon(), None), ("poignet", pg, pg_e), ("cuir", t_cuir(), None), ("core", core, core_e),
              ("corde", crd, crd_e), ("cristal", cri, cri_e), ("halo", t_halo(), None), ("crk", t_crk(), None),
              ("penne", t_penne(), None),
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
    print("atlas : hauteur utilisée", y + shelf, "/", TEX, ";", len(TILES), "tuiles échantillonnées")
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


def euler(R):
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def rmat(rx, ry, rz):
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


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


def seg(g, name, p, q, w, tile, ov=0.06, roll=45.0, w2=None):
    """Tronçon (monde) de p à q, section w × w2 tournée de roll autour de l'axe (repère : +Z du monde)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = V(0, 0, 1) if abs(X[2]) < 0.9 else V(1, 0, 0)
    Y0 = unit(ref - (ref @ X) * X)
    Z0 = np.cross(X, Y0)
    r = math.radians(roll)
    Y = Y0 * math.cos(r) + Z0 * math.sin(r)
    Ln = float(np.linalg.norm(q - p))
    boite(g, name, (p + q) / 2, X, Y, Ln + 2 * ov, w, w if w2 is None else w2, strip(tile, caps=tile != "halo"))


def barre(g, name, p, q, r, tile, octo=True, caps=True, ov=0.0):
    """Barre octogonale (deux cubes, le second tourné de 45° autour de l'axe), de p à q (monde)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    Ln = float(np.linalg.norm(q - p)) + 2 * ov
    c = (p + q) / 2
    ref = V(0, 0, 1) if abs(X[2]) < 0.9 else V(1, 0, 0)
    Y0 = unit(ref - (ref @ X) * X)
    boite(g, name, c, X, Y0, Ln, 2 * r, 2 * r, strip(tile, caps))
    if octo:
        Z0 = np.cross(X, Y0)
        Yq = unit(Y0 + Z0)
        boite(g, name + "o", c, X, Yq, Ln - 0.06, 2 * r * 0.97, 2 * r * 0.97, strip(tile, caps))


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
    """Éclair qui suit une polyligne 2D : n tronçons irréguliers, écarts latéraux alternés ; renvoie des points (x, y, z)."""
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


def zigzag3(p, q, n, J, seed):
    """Éclair 3D de p à q (monde) : écarts alternés dans deux directions perpendiculaires."""
    rng = random.Random(seed)
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = V(0, 0, 1) if abs(X[2]) < 0.9 else V(1, 0, 0)
    Y = unit(ref - (ref @ X) * X)
    Z = np.cross(X, Y)
    out = [p]
    sg = rng.choice((-1, 1))
    for i in range(1, n):
        t = (i + rng.uniform(-0.25, 0.25)) / n
        out.append(p + (q - p) * t + (Y * sg * rng.uniform(0.5, 1.0) + Z * rng.uniform(-0.6, 0.6)) * J)
        sg = -sg
    out.append(q)
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


# --- repère de l'arc (comme skin_arc_givre) : s vers l'avant (flèche), h le long des branches, z vers +Z (face d'inventaire)
S_ = V(-1, 1, 0) / math.sqrt(2)
H_ = V(1, 1, 0) / math.sqrt(2)
Z_ = V(0, 0, 1)
C0 = V(8.0, 8.0, 8.0)
SG = 3.55                          # prise : s du milieu du poing
HG = -0.7                          # prise : h du milieu du poing -> (5, 10, 8)
HA = 0.85                          # ligne de la flèche
BP = np.column_stack([S_, H_, -Z_])     # (s, h, z_local) -> monde, direct (z local = -Z du monde)


def P(s, h, z=0.0):
    return C0 + S_ * s + H_ * h + Z_ * z


GONDS = {"haut": (V(3.0, 3.7), 1), "bas": (V(3.0, -3.2), -1)}


def pose(origin_sh, phi, sgn):
    """Repère local (a, b, z) -> monde d'une pièce posée en origin_sh, angle phi (depuis +h vers l'archer), branche sgn."""
    ph = math.radians(phi)
    d = V(-math.sin(ph), math.cos(ph))
    b = V(-math.cos(ph), -math.sin(ph))
    R = np.array([[d[0], b[0], 0.0], [d[1], b[1], 0.0], [0.0, 0.0, 1.0]])
    F = np.diag([1.0, float(sgn), float(sgn)])
    M = BP @ F @ R
    off = C0 + S_ * float(origin_sh[0]) + H_ * float(origin_sh[1])
    return M, off


def poser(g, cle, M, off, prefixe):
    for sp in SPECS[cle]:
        u_ = {}
        for f in ("north", "south", "east", "west", "up", "down"):
            u_[f] = list(UV[sp["faces"][f]]) if f in sp["faces"] else CLEAR
        boite(g, prefixe + sp["nom"], off + M @ sp["c"], M @ sp["X"], M @ sp["Y"], *sp["s"], u_)


def tambour(g, name, c, R_I, epais, face_tile, n_axe=None):
    """Tambour à 16 pans d'axe +Z (4 carrés tournés de 22,5°, côtés en or), fermé par deux médaillons."""
    for k in range(4):
        th = math.radians(22.5 * k)
        X = S_ * math.cos(th) + H_ * math.sin(th)
        Y = -S_ * math.sin(th) + H_ * math.cos(th)
        boite(g, f"{name}{k}", c, X, Y, 2 * R_I, 2 * R_I, epais,
              {"north": CLEAR, "south": CLEAR, "east": UV["or"], "west": UV["or"], "up": UV["or"], "down": UV["or"]})
    u0, v0, u1, v1 = UV[face_tile]
    MR = R_I / math.cos(math.radians(11.25)) + 0.01
    for sg in (1, -1):
        fc = {"south": [u0, v0, u1, v1]} if sg > 0 else {"north": [u1, v0, u0, v1]}
        boite(g, f"{name}_f{'pm'[sg < 0]}", c + Z_ * sg * (epais / 2 - 0.12), S_, H_, 2 * MR, 2 * MR, 0.3,
              {**{f: CLEAR for f in ("north", "south", "east", "west", "up", "down")}, **fc})


# tension des étapes : angle du bras (depuis +h vers l'archer), angle absolu de la main (négatif = recourbée vers l'avant)
PHI_BRAS = (28.0, 40.0)
PHI_MAIN = (-12.0, 18.0)
# (nom, tension, tirage de la corde depuis la prise (None : corde droite), niveau de charge)
ETAPES = [("repos", 0.0, None, 0), ("bande_1", 0.33, 5.6, 1), ("bande_2", 0.66, 7.8, 2), ("bande_3", 1.0, 10.0, 3)]
L_FL = 11.2                        # flèche : de l'encoche au bout de la pointe


def branche(g_etape, nm, d, sgn, etape, out):
    """Une aile-branche posée pour la tension d : bras + gouttière + foudre, poignet, main, poupée. Renvoie (poupée, poignet) en (s, h)."""
    gond, _ = GONDS[nm]
    pa = lerp(PHI_BRAS[0], PHI_BRAS[1], d)
    ph = lerp(PHI_MAIN[0], PHI_MAIN[1], d)
    Ma, oa = pose(gond, pa, sgn)
    ra = math.radians(pa)
    poignet = gond + LA * V(-math.sin(ra), sgn * math.cos(ra))
    Mh, oh = pose(poignet, ph, sgn)
    gb = group(f"aile_{nm}_{etape}", P(*gond), parent=g_etape)
    poser(gb, "bras", Ma, oa, f"{nm}_{etape}_")
    poser(gb, "main", Mh, oh, f"{nm}_{etape}_")
    # collet d'or où le bras sort du logement (bouge avec le bras)
    boite(gb, f"collet_{nm}_{etape}", oa + Ma @ V(0.62, -0.1, 0), Ma @ V(1, 0, 0), Ma @ V(0, 1, 0), 0.26, 2.5, 1.62, strip("or"))
    # foudre couchée au fond de la gouttière, des deux côtés ; gaine add_ en 2 sections
    gf = group(f"foudre_{nm}_{etape}", oa + Ma @ V(*SLIT_ARM[0], 0), parent=gb)
    for zs in (1, -1):
        pts2 = zigzag(SLIT_ARM, 8, 0.05, 17 + (3 if zs < 0 else 0))
        pts = [oa + Ma @ V(x, y, zs * 0.17) for x, y, _ in pts2]
        trait(gf, f"eclair_{'pm'[zs < 0]}", pts, 0.3, 0.22, "core")
    gaines = []
    pts2 = zigzag(SLIT_ARM, 8, 0.05, 17)
    for k in range(2):
        gg = group(f"add_gaine_{nm}_{etape}_{k}", oa + Ma @ V(*pts2[4 * k][:2], 0), gf)
        ctrl(gg)
        for i in range(4 * k, 4 * k + 4):
            am = (pts2[i][0] + pts2[i + 1][0]) / 2
            seg(gg, f"gaine{i}", oa + Ma @ V(*pts2[i][:2], 0), oa + Ma @ V(*pts2[i + 1][:2], 0),
                min(0.78, 2 * float(h_arm(am)) - 0.16), "halo", ov=0.04, roll=0.0)
        gaines.append(gg)
    out.setdefault("gaines", {}).setdefault(etape, []).extend(gaines)
    # poignet : petit tambour d'or à œil de cristal
    tambour(gb, f"poignet_{nm}_{etape}", P(*poignet), 0.68, 1.46, "poignet")
    # poupée d'or traversante, au ventre de la main
    nk = oh + Mh @ V(*NOCK, 0)
    barre(gb, f"poupee_{nm}_{etape}", nk - Z_ * (float(h_main(NOCK[0])) + 0.17), nk + Z_ * (float(h_main(NOCK[0])) + 0.17), 0.24, "or")
    tip = oh + Mh @ V(*TIPH, 0)
    return nk, P(*poignet), tip, (Ma, oa), (Mh, oh), gb


def construire():
    elements.clear()
    groups.clear()
    _rc[0] = 0
    out = {}
    arc = group("arc", P(SG, HG))
    out["arc"] = arc
    # --- poignée défléchie
    pg = group("poignee", P(SG, HG), arc)
    barre(pg, "prise", P(SG, -1.95), P(SG + 0.02, 0.3), 0.7, "cuir")
    barre(pg, "bague_bas", P(SG, -2.3), P(SG, -1.9), 0.8, "or")
    barre(pg, "bague_haut", P(SG + 0.02, 0.25), P(SG + 0.02, 0.58), 0.8, "or")
    barre(pg, "montant_bas", P(SG - 0.02, -2.2), P(3.05, -3.0), 0.6, "metal", ov=0.05)
    barre(pg, "montant_haut", P(SG - 0.12, 1.55), P(3.05, 3.5), 0.6, "metal", ov=0.05)
    # fenêtre de tir : montant décalé vers -Z, la flèche passe à côté, sur un repose-flèche d'or
    boite(pg, "fenetre", (P(SG + 0.02, 0.5, -0.72) + P(SG - 0.12, 1.75, -0.72)) / 2, H_, S_, 1.35, 1.2, 0.6, strip("metal"))
    boite(pg, "repose", P(SG + 0.05, 0.56, -0.05), S_, H_, 0.9, 0.22, 1.0, strip("or"))
    # tambour aux trois virgules sur le montant haut
    tambour(pg, "tambour", P(SG - 0.28, 2.45), 0.98, 1.8, "medaillon")
    # logements chanfreinés (le bras pivote sur un axe d'or)
    for nm, (gond, sgn) in GONDS.items():
        pa = PHI_BRAS[0]
        Ma, oa = pose(gond, pa, sgn)
        c = oa + Ma @ V(0.05, -0.05, 0)
        X, Y = Ma @ V(1, 0, 0), Ma @ V(0, 1, 0)
        boite(pg, f"logement_{nm}", c, X, Y, 1.3, 2.75, 1.72, strip("metal"))
        Xq = unit(X + Ma @ V(0, 0, 1))
        boite(pg, f"logement_{nm}_ch", c, Xq, Y, 1.0, 2.69, 1.0, strip("sombre"))
        barre(pg, f"axe_{nm}", P(*gond) - Z_ * 1.02, P(*gond) + Z_ * 1.02, 0.34, "or")
    # stabilisateur de cristal sous la prise (pointe vers l'avant)
    barre(pg, "stab_or", P(SG + 0.35, -2.75), P(SG + 0.8, -2.8), 0.42, "or")
    barre(pg, "stab_cri", P(SG + 0.75, -2.8), P(SG + 1.7, -2.9), 0.32, "cristal")
    barre(pg, "stab_pointe", P(SG + 1.65, -2.9), P(SG + 2.2, -2.95), 0.17, "cristal", octo=False)
    # point d'émission des étincelles au tir (fenêtre)
    em = group("emit_mc_electric_spark", P(SG + 0.6, HA), arc)
    group("ctrl_emit", P(SG + 0.6, HA), em)
    out["emit"] = em

    out["etape"], out["corde"], out["aile"], out["arcs_corde"], out["geo"] = {}, {}, {}, {}, {}
    for nom_e, d, tir, charge in ETAPES:
        ge = group(objet.etape(nom_e, "arc"), P(SG, HG))
        out["etape"][nom_e] = ge
        geo = {}
        for nm, (gond, sgn) in GONDS.items():
            nk, wr, tip, Ta, Th, gb = branche(ge, nm, d, sgn, nom_e, out)
            geo[nm] = (nk, wr, tip, Ta, Th)
            out["aile"].setdefault(nom_e, []).append(gb)
        out["geo"][nom_e] = geo
        # --- corde : poupée -> (contact sur le poignet si la ligne directe le traverse) -> point d'encoche
        gc = group(f"corde_{nom_e}", P(SG - (tir or 0) - 2.3, HA), ge)
        out["corde"][nom_e] = gc
        enc = P(SG - tir, HA) if tir else None
        chemins = []
        for nm in ("haut", "bas"):
            nk, wr, tip, Ta, Th = geo[nm]
            cible = enc if enc is not None else geo["bas" if nm == "haut" else "haut"][0]
            Ma, oa = Ta
            ventre = Ma @ V(0, 1, 0)                       # vers la corde, dans le plan
            contact = wr + ventre * 0.82
            dl = unit(cible - nk)
            # côté de la ligne poupée -> cible où se trouve le poignet : s'il est du côté de la corde, la corde s'y appuie
            v_ = contact - nk
            perp = v_ - (v_ @ dl) * dl
            pts = [nk, contact, cible] if perp @ ventre > 0 and np.linalg.norm(perp) > 1e-3 else [nk, cible]
            chemins.append(pts)
        if enc is None:
            # corde droite entre les deux contacts (une seule ligne : haut -> bas)
            h_pts, b_pts = chemins
            pts = h_pts[:-1] + b_pts[:-1][::-1]
            chemins = [pts]
        for j, pts in enumerate(chemins):
            for i in range(len(pts) - 1):
                seg(gc, f"corde{j}{i}", pts[i], pts[i + 1], 0.2, "corde", ov=0.05, roll=0.0)
        out["chemins_" + nom_e] = chemins
        if enc is None:
            continue
        barre(gc, f"tranchefil_{nom_e}", enc - H_ * 0.45, enc + H_ * 0.45, 0.26, "or")
        # --- arcs qui chargent la corde, depuis le point d'encoche (part croissante avec la charge)
        part = {1: 0.32, 2: 0.66, 3: 1.0}[charge]
        ga = group(f"add_corde_{nom_e}", enc, ge)
        ctrl(ga)
        for j, pts in enumerate(chemins):
            pr = pts[::-1]                                  # de l'encoche vers la poupée
            ls = np.cumsum([0] + [np.linalg.norm(pr[i + 1] - pr[i]) for i in range(len(pr) - 1)])
            tot = ls[-1] * part
            n = max(3, int(round(tot / 0.9)))

            def at(x, pr=pr, ls=ls):
                i = min(np.searchsorted(ls, x, side="right") - 1, len(pr) - 2)
                k = (x - ls[i]) / max(ls[i + 1] - ls[i], 1e-9)
                return pr[i] + (pr[i + 1] - pr[i]) * k
            perp = unit(np.cross(Z_, unit(pr[-1] - pr[0])))
            for v in range(2 if charge >= 2 else 1):
                rng = random.Random(300 + 31 * j + 7 * v + 100 * charge)
                sg = 1 if v == 0 else -1
                ptsz = []
                for i in range(n + 1):
                    p = at(tot * i / n)
                    if 0 < i < n:          # l'arc s'enroule autour de la corde : écarts alternés en z et en travers
                        p = p + Z_ * sg * rng.uniform(0.14, 0.3) * (1 if i % 2 else -1) + perp * rng.uniform(-0.14, 0.14)
                    ptsz.append(p)
                trait(ga, f"a{j}{v}_", ptsz, 0.17, 0.12, "crk")
            if charge >= 2:
                for i in range(len(pr) - 1):
                    a_, b_ = ls[i], min(ls[i + 1], tot)
                    if b_ <= a_:
                        break
                    seg(ga, f"gaine{j}{i}", at(a_), at(b_), 0.5 if charge == 2 else 0.62, "halo", ov=0.03, roll=0.0)
        if charge == 3:
            # fourches aux poupées
            for nm in ("haut", "bas"):
                nk = geo[nm][0]
                for k, ang in enumerate((-35, 30)):
                    dl = unit(enc - nk)
                    rr = math.radians(ang)
                    dir_ = dl * math.cos(rr) + unit(np.cross(Z_, dl)) * math.sin(rr)
                    trait(ga, f"fourche_{nm}{k}_", zigzag3(nk, nk + dir_ * 1.1, 3, 0.18, 60 + k + (5 if nm == "bas" else 0)), 0.15, 0.1, "crk")
        out["arcs_corde"][nom_e] = ga
        # --- flèche d'acier encochée
        gfl = group(f"fleche_{nom_e}", enc, ge)
        s0 = SG - tir
        barre(gfl, "encoche", P(s0 - 0.08, HA), P(s0 + 0.35, HA), 0.22, "or")
        s_pt = s0 + L_FL - 1.85
        barre(gfl, "fut", P(s0 + 0.3, HA), P(s_pt + 0.1, HA), 0.15, "sombre")
        barre(gfl, "virole", P(s_pt - 0.3, HA), P(s_pt + 0.05, HA), 0.22, "or")
        Mp, op = pose(V(s_pt, HA), -90.0, 1)
        poser(gfl, "pointe_ch" if charge == 3 else "pointe", Mp, op, f"{nom_e}_")
        u0, v0, u1, v1 = UV["penne"]
        for k, upv in enumerate((H_, Z_, -H_, -Z_)):
            c = P(s0 + 1.35, HA) + upv * 0.42
            right = S_
            boite(gfl, f"penne{k}", c, right, upv, 1.7, 0.56, 0.3,
                  {"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
        if charge == 3:
            gs = group(f"add_gaine_fleche_{nom_e}", P(s0 + 2.0, HA), ge)
            ctrl(gs)
            trait(gs, "f", zigzag3(P(s0 + 2.2, HA), P(s_pt - 0.2, HA), 6, 0.28, 91), 0.15, 0.11, "crk")
            out["gaine_fleche"] = gs

    # --- éclairs des événements (repliés à 1/10 sur un pivot caché dans le métal)
    geo0 = out["geo"]["repos"]
    out["sel"] = {}
    # event_select : la foudre frappe le tambour (deux formes), puis court le long des deux ailes
    ct = P(SG - 0.28, 2.45)
    for nm_f, seed, ang in (("a", 5, 40), ("b", 9, 58)):
        g = group(f"add_sel_frappe_{nm_f}", ct, arc)
        ctrl(g)
        rr = math.radians(ang)
        q = ct + (S_ * math.cos(rr) + H_ * math.sin(rr)) * 3.6
        trait(g, "f", zigzag3(ct + (q - ct) * 0.25, q, 5, 0.32, seed), 0.26, 0.14, "crk")
        replier(g)
        out["sel"]["frappe_" + nm_f] = g
    for nm, (gond, sgn) in GONDS.items():
        nk, wr, tip, (Ma, oa), (Mh, oh) = geo0[nm]
        chemin = [oa + Ma @ V(a, -1.28 + 0.3 * a / 3.6 - 0.15, 0) for a in (0.6, 2.0, 3.6)] + [oh + Mh @ V(a, b - 0.15, 0) for a, b in ((1.3, -0.52), (2.6, -0.4))] + [tip]
        for k in range(len(chemin) - 1):
            piv = oa + Ma @ V(min(3.4, 0.6 + 1.4 * k), 0, 0) if k < 2 else oh + Mh @ V(min(2.4, 0.3 + 1.1 * (k - 2)), 0, 0)
            g = group(f"add_sel_{nm}{k}", piv, arc)
            ctrl(g)
            trait(g, "a", zigzag3(chemin[k], chemin[k + 1], 3, 0.14, 200 + 10 * k + (5 if nm == "bas" else 0)), 0.2, 0.16, "crk")
            replier(g)
            out["sel"][f"{nm}{k}"] = g
    # item_idle : petite étincelle à la pointe de l'aile haute
    nk, wr, tip, (Ma, oa), (Mh, oh) = geo0["haut"]
    piv = oh + Mh @ V(2.4, 0, 0)
    g = group("add_idle_pointe", piv, arc)
    ctrl(g)
    dtip = unit(tip - (oh + Mh @ V(2.0, -0.1, 0)))
    for j, an in enumerate((-30, 25)):
        rr = math.radians(an)
        dd = dtip * math.cos(rr) + unit(np.cross(Z_, dtip)) * math.sin(rr)
        trait(g, f"p{j}", zigzag3(tip, tip + dd * 1.2, 3, 0.16, 400 + j), 0.2, 0.12, "crk")
    replier(g)
    out["idle_pointe"] = g
    # event_enter_bande_3 : deux arcs des poignets à la pointe de la flèche (dans l'étape bande_3)
    geo3 = out["geo"]["bande_3"]
    pointe = P(SG - 10.0 + L_FL - 0.6, HA)
    out["charge"] = []
    for nm in ("haut", "bas"):
        wr = geo3[nm][1]
        g = group(f"add_charge_{nm}", wr, out["etape"]["bande_3"])
        ctrl(g)
        trait(g, "c", zigzag3(wr, pointe, 6, 0.4, 500 + (7 if nm == "bas" else 0)), 0.22, 0.14, "crk")
        replier(g)
        out["charge"].append(g)
    # event_release : la flèche part dans une décharge (deux formes le long de la ligne de tir + fourches)
    w0 = P(SG - 0.2, 0.56, -0.05)
    out["tir"] = []
    for nm_f, seed in (("a", 31), ("b", 47)):
        g = group(f"add_tir_{nm_f}", w0, arc)
        ctrl(g)
        q = P(SG + 7.8, HA)
        pts = zigzag3(P(SG + 0.5, HA), q, 9, 0.3, seed)
        trait(g, "t", pts, 0.32, 0.14, "crk")
        rng = random.Random(seed)
        for k in (3, 6):
            dd = unit(S_ + H_ * rng.choice((-1, 1)) * 0.8 + Z_ * rng.uniform(-0.4, 0.4))
            trait(g, f"fk{k}_", zigzag3(pts[k], pts[k] + dd * 1.4, 3, 0.15, seed + k), 0.16, 0.1, "crk")
        replier(g)
        out["tir"].append(g)
    return out


F = construire()


def coins(filtre=None):
    Pp = []
    for e in elements:
        if filtre is not None and e["uuid"] not in filtre:
            continue
        f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
        R = rmat(*e.get("rotation", (0, 0, 0)))
        for i in range(8):
            c = np.array([(f, t)[(i >> k) & 1][k] for k in range(3)])
            Pp.append(R @ (c - o) + o)
    return np.array(Pp)


outliner = [bone_node(F["arc"])] + [bone_node(F["etape"][e[0]]) for e in ETAPES]
ids_repos = {i for n in sous_groupes(F["arc"]) + sous_groupes(F["etape"]["repos"]) for i in groups[n]["ids"]}
P_REPOS = coins(ids_repos)
for nm in ("haut", "bas"):
    nk, wr, tip, *_ = F["geo"]["repos"][nm]
    print(f"repos {nm} : poupée {np.round(nk, 2)} pointe {np.round(tip, 2)}")
POINTES = float(np.linalg.norm(F["geo"]["repos"]["haut"][2] - F["geo"]["repos"]["bas"][2]))


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


P_RS, PR_RS = 5.5, 0.6


def gaine_idle(k):
    return chk(restrike(P_RS, PR_RS, 0.37) + flick(9, 0.13 + 0.31 * k) + "-0.42+0.22*(v.h<0.3)-0.25*(v.h>0.82)+0.7*v.r")


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


EVENT_GROUPS = list(F["sel"].values()) + [F["idle_pointe"]] + F["tir"]
GAINES_REPOS = F["gaines"]["repos"]
GAINES_BANDE = [g for e in ("bande_1", "bande_2", "bande_3") for g in F["gaines"][e]]

# item_idle : la foudre des gouttières grésille, arc en retour au hasard avec une étincelle à la pointe haute.
idle = anim("item_idle", 8.0)
for k, g in enumerate(GAINES_REPOS):
    piste_ctrl(idle, g, [kf("position", 0, gaine_idle(k))])
deplier(idle, F["idle_pointe"])
piste_ctrl(idle, F["idle_pointe"], [kf("position", 0, chk(restrike(P_RS, PR_RS, 0.37) + "v.r-1"))])
for g in list(F["sel"].values()) + F["tir"]:
    piste_ctrl(idle, g, [kf("position", 0, -1)])
piste(idle, "ctrl_emit", [kf("position", 0, -1)])

# item_gui : inventaire calme.
gui = anim("item_gui", 4.0)
for g in GAINES_REPOS:
    piste_ctrl(gui, g, [kf("position", 0, -0.35)])
for g in EVENT_GROUPS:
    piste_ctrl(gui, g, [kf("position", 0, -1)])
piste(gui, "ctrl_emit", [kf("position", 0, -1)])

# item_use (0,5 s) : l'arc frémit avec la tension ; la corde grésille, plus vive à pleine tension.
use = anim("item_use", 0.5)
TREM = "math.sin(q.anim_time*360*14)*0.8*q.use_progress*q.use_progress"
piste(use, F["arc"], [kf("rotation", 0, 0, 0, TREM)])
for e in ("bande_1", "bande_2", "bande_3"):
    piste(use, F["etape"][e], [kf("rotation", 0, 0, 0, TREM)])
for i, (e, g) in enumerate(F["arcs_corde"].items()):
    piste_ctrl(use, g, [kf("position", 0, chk(flick(13, 0.21 + 0.4 * i) + "-0.45+0.45*q.use_progress-0.9*(v.h<0.18)+0.3*(v.h>0.85)"))])
for k, g in enumerate(GAINES_BANDE):
    piste_ctrl(use, g, [kf("position", 0, chk(flick(10, 0.07 + 0.29 * k) + "-0.4+0.5*q.use_progress-0.3*(v.h<0.25)"))])
piste_ctrl(use, F["gaine_fleche"], [kf("position", 0, chk(flick(16, 0.5) + "-1+1.2*(v.h>0.35)"))])
piste(use, "ctrl_emit", [kf("position", 0, -1)])

# event_enter_bande_3 (0,35 s) : deux arcs sautent des poignets à la pointe de la flèche.
L_E3 = 0.35
e3 = anim("event_enter_bande_3", L_E3, "once")
for j, g in enumerate(F["charge"]):
    deplier(e3, g)
    piste_ctrl(e3, g, onoff([(0.0 + 0.03 * j, 0.08 + 0.03 * j), (0.16, 0.2)] if j == 0 else [(0.03, 0.11), (0.21, 0.24)], L_E3))

# event_release (0,7 s) : la flèche part dans une décharge ; corde qui vibre, ailes qui frissonnent, gerbe, un son.
L_REL = 0.7
rel = anim("event_release", L_REL, "once")
ta, tb = F["tir"]
deplier(rel, ta)
deplier(rel, tb)
piste_ctrl(rel, ta, onoff([(0.0, 0.06), (0.15, 0.19), (0.3, 0.33)], L_REL))
piste_ctrl(rel, tb, onoff([(0.06, 0.12), (0.22, 0.26)], L_REL))
cr = F["corde"]["repos"]
piste(rel, cr, [kf("position", t, *(S_ * 0.35 * math.sin(TAU * 16 * t) * math.exp(-t / 0.14) * sm(t, 0.0, 0.02)).round(4))
                for t in np.round(np.linspace(0, 0.45, 28), 4)] + [kf("position", L_REL, 0, 0, 0)])
for j, g in enumerate(F["aile"]["repos"]):
    sg = 1 if j == 0 else -1
    piste(rel, g, [kf("rotation", t, 0, 0, sg * 1.8 * math.sin(TAU * 11 * t) * math.exp(-t / 0.12) * sm(t, 0.0, 0.02))
                   for t in np.round(np.linspace(0, 0.4, 25), 4)] + [kf("rotation", L_REL, 0, 0, 0)])
for k, g in enumerate(GAINES_REPOS):
    piste_ctrl(rel, g, [kf("position", t, 0.9 * sm(t, 0.0, 0.02) * (1 - sm(t, 0.08, 0.5)) - 0.4 * sm(t, 0.08, 0.5))
                        for t in np.round(np.linspace(0, L_REL, 15), 4)])
piste(rel, "ctrl_emit", [kf("position", t, 6 * bump(t, 0.0, 0.02, 0.1, 0.18) - 1) for t in np.round(np.linspace(0, 0.3, 16), 4)]
      + [kf("position", L_REL, -1)])

# event_select (0,7 s) : la foudre frappe le tambour, puis court le long des deux ailes jusqu'aux pointes.
L_SEL = 0.7
sel = anim("event_select", L_SEL, "once")
deplier(sel, F["sel"]["frappe_a"])
deplier(sel, F["sel"]["frappe_b"])
piste_ctrl(sel, F["sel"]["frappe_a"], onoff([(0.0, 0.07), (0.15, 0.19)], L_SEL))
piste_ctrl(sel, F["sel"]["frappe_b"], onoff([(0.08, 0.13)], L_SEL))
for nm in ("haut", "bas"):
    k = 0
    while f"{nm}{k}" in F["sel"]:
        g = F["sel"][f"{nm}{k}"]
        deplier(sel, g)
        t0 = 0.14 + 0.045 * k + (0.015 if nm == "bas" else 0)
        piste_ctrl(sel, g, onoff([(t0, t0 + 0.08)], L_SEL))
        k += 1
for k, g in enumerate(GAINES_REPOS):
    t0 = 0.14 + 0.06 * (k % 2)
    piste_ctrl(sel, g, [kf("position", t, -0.6 * (1 - sm(t, 0.0, 0.1)) * (t < t0) + (1.0 * bump(t, t0, t0 + 0.04, t0 + 0.12, t0 + 0.4)
                                                                                    - 0.42 * sm(t, t0 + 0.12, t0 + 0.4)) * (t >= t0))
                        for t in np.round(np.linspace(0, L_SEL, 29), 4)])

ANIMS = [idle, gui, use, e3, rel, sel]

# ------------------------------------------------------------------ écriture
assert 150 <= len(elements) <= 3000, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
_P = coins()
_lo, _hi = _P[:, :2].min(0), _P[:, :2].max(0)
_c = (_lo + _hi) / 2
GUI_S = round(min(1.0, 15.4 / float(max(_hi - _lo))), 3)
GUI_T = [round(float((8 - _c[0]) * GUI_S), 2), round(float((8 - _c[1]) * GUI_S), 2), 0]
AFFICHAGE = objet.affichage("arc", gui={"scale": [GUI_S] * 3, "translation": GUI_T})
model = objet.modele(NOM, "arc", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, embarquer_sons, cle_son
limiter_sons(model)
embarquer_sons(model, {"decharge_arc": "sons/decharge_arc.ogg"})
# Un seul son, au tir (event_release) : tools/sons.py ne connaît pas encore les événements d'objet, on le pose après.
rel["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "decharge_arc")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"pointe à pointe (repos) {POINTES:.1f} px ; boîte {_P.min(axis=0).round(2)} .. {_P.max(axis=0).round(2)} ; gui {GUI_S} {GUI_T}")
