"""Tire-Bisou : skin d'objet (guide 14) pour toutes les arbalètes du joueur, ensemble Kawaii (thème Mignon). Design original.
Écrit skin_arbalete_kawaii.png, skin_arbalete_kawaii_e.png et .build/skin_arbalete_kawaii_brut.bbmodel à côté de ce script.
Généré par .build/assembler.py depuis .build/gabarit.py et les fonctions communes de gen_skin_epee_kawaii.py (ne pas éditer
le générateur assemblé : éditer le gabarit, ou ses parties .build/part_*.py, puis relancer l'assembleur).

Idée (fiche .claude/styles/kawaii.md, langage Kawaii des objets ; sœur de l'Arc de guimauve, mais silhouette propre) :
- logement de l'arc = **gros cœur de sucre framboise « coussin »** couché dans le plan de l'image, **pointe vers l'avant**
  (la pointe du cœur fait la proue), grand reflet blanc en fenêtre, contre-reflet `_e` ; l'arbrier entre dans l'échancrure ;
- arc = deux **bras de sucre lilas** en vrai volume (plaque biseautée fermée, pente unique 45°, 1,40 -> 0,72 px, bout en ogive
  arrondie, fil crème, bande rose bonbon, liseré lilas foncé), sortis des lobes du cœur, une **dragée-cœur `_e`** sertie sur
  chaque face ; **perle lavande** au bout de chaque bras où s'attache la corde (l'arc a des branches de guimauve et des
  nuages : ici le sucre lilas des lames du set) ;
- étrier = **anneau lavande** en tours devant la pointe du cœur ; arbrier de **guimauve torsadée** (spirale continue), crosse
  plus dodue entre deux bagues lavande, **talon-nuage** de trois bosses ; noix lavande en travers, détente lavande ;
- corde lumineuse rose blanc (`_e`) : source nette et logique, vue de face comme de dos.

Vrai volume (recette .claude/references/objets/volume-3d.md, retour en jeu « pas des couches empilées ») : cœur, bras, dragées,
plumes, pointe-cœur = `Piece` sur un contour fermé, posées par `poser()` (mêmes tuiles d'une étape à l'autre) ; arbrier,
bagues, noix, étrier, perles, nuage, carreau, fusée en tours de pans (éclairage lissé texel par texel).

Repère (celui de l'arbalète vanilla, validé en jeu sur skin_arbalete_steampunk ; comme skin_arbalete_abyssal) : S_ = avant
(carreau vers le HAUT À GAUCHE de l'image), H_ = le long de l'arc, Z = face vue dans l'inventaire ; W(s, h, z). Display
vanilla `crossbow`, gui calculé sur la boîte (fût + repos).

Étapes (groupes racine ; `arbalete` toujours dessiné) : `repos`, `bande_1..3` (les bras reculent de 5/10/14° dans le cœur, la
corde recule jusqu'à la noix), `chargee` (carreau : bâton de sucre crème rayé de lilas, trois plumes lilas, **pointe-cœur
framboise allumée** `_e`), `chargee_fusee` (fusée en sucre d'orge rose et crème, coiffe framboise, bagues lavande).
Carreau et fusée tirés restent ceux du jeu (non personnalisables).

Objet vivant (guide 14) :
- `item_idle` (8 s) : le cœur bat (double battement deux fois), dragées qui s'avivent au battement (`ctrl_lumiere`), le
  talon-nuage respire ; sans son ;
- `item_use` (0,6 s) : le cœur bat plus fort avec `q.use_progress`, les bras frémissent ; sans son ;
- `event_charged` (0,5 s) : « plop » du cœur, dragées et pointe-cœur qui s'allument ; sans son ;
- `event_release` (0,9 s) : squash du cœur, bras qui vibrent, corde qui « twang », nuage de sucre `trans_paillettes`
  (`ctrl_alpha`) + paillettes-étoiles `_e` cachés K fois plus petits dans le cœur (seuls dépliages par `scale` de ces groupes),
  `emit_mc_heart` (rafale « Au tir ») ; **seul son** : `paillettes` embarqué (sons/paillettes.py, original) à **0,04 s** ;
- `event_select` (0,6 s) : « plop » du cœur puis du talon-nuage.
Aucun son sur event_use_start, event_enter_* ni event_charged.

Fonctions avancées : `trans_paillettes`, `ctrl_alpha`, `ctrl_lumiere`, `emit_mc_heart`, calque `_e` (corde, dragées,
contre-reflet, pointe-cœur, paillettes), son embarqué, Molang `q.use_progress`, event_charged, event_release. Non simulés par
l'aperçu : animations en main, particules, ctrl_lumiere, son (à juger en jeu, `/cosmetique apercu`).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

AVEC_E = True
NOM = "skin_arbalete_kawaii"
TEX = 512
TAU = 2 * math.pi
DF = 16.0                       # texels par px sur les faces des volumes
DENS = 16.0                     # texels par px sur les pans des tours
TH = 0.3                        # épaisseur des cubes (biseaux, plats, pans)
RECOUV = 0.08                   # recouvrement des faces voisines
OVL, OVW = 0.04, 0.03           # recouvrement des pans (en long, en travers)
K = 8.0                         # nuage de sucre et paillettes K fois plus petits au repos


def A(c):
    return np.array(c, np.float32)


LILAS = dict(hi=A((232, 220, 255)), base=A((184, 160, 244)), low=A((120, 92, 200)))
LISERE = A((130, 86, 210))
CREME = A((255, 246, 240))
BONBON = A((255, 170, 206))
FRAMB = dict(hi=A((255, 128, 176)), base=A((226, 52, 118)), low=A((150, 22, 78)))
NUAGE = dict(hi=A((255, 252, 250)), base=A((255, 249, 247)), low=A((214, 202, 232)))
GUIM_R = A((242, 104, 166))
GUIM_C = A((252, 240, 244))
LAVANDE = dict(hi=A((242, 236, 255)), base=A((208, 192, 248)), low=A((146, 124, 206)))
DRAGEE = A((255, 150, 202))
DRAGEE_E = A((225, 140, 196))
BLANC = A((255, 255, 255))
CORDE = A((255, 214, 236))
CORDE_E = A((255, 168, 214))
LUMIERE = np.array((-0.35, 0.7, 0.62)) / np.linalg.norm((-0.35, 0.7, 0.62))   # lumière de dessin (haut, un peu à gauche, devant)

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


def grain(P, seed=0.0):
    """Grain de sucre mat (±3 %)."""
    v = np.sin(P[..., 0] * 37.0 + P[..., 1] * 11.0 + seed) * np.sin(P[..., 1] * 43.0 - P[..., 0] * 7.0 + seed * 2)
    return v * 0.02


def coeur_poly(cx, cy, R, yb, rb, n=40, ox=0.0, oy=0.0, sx=1.0):
    """Contour d'un cœur dodu (x en travers, y vers les lobes) : union de deux « gélules effilées » lobe -> bas arrondi.
    Rayon par rayon depuis un point intérieur (le cœur est étoilé depuis ce point). Renvoie des points (a, b) = (oy + y, ox + x)."""
    tt = np.linspace(0, 1, 41)

    def dedans(p):
        ok = False
        for s in (1, -1):
            c1, c2 = np.array((s * cx, cy)), np.array((0.0, yb))
            cs = c1[None] + tt[:, None] * (c2 - c1)[None]
            rs = R + tt * (rb - R)
            ok = ok or bool((np.linalg.norm(p[None] - cs, axis=1) <= rs).any())
        return ok

    O = np.array((0.0, cy - 0.35 * R))
    pts = []
    for k in range(n):
        ph = math.pi / 2 + TAU * k / n
        d = np.array((math.cos(ph), math.sin(ph)))
        lo, hi = 0.0, 6.0 * R
        for _ in range(28):
            mid = (lo + hi) / 2
            if dedans(O + d * mid):
                lo = mid
            else:
                hi = mid
        p = O + d * lo
        pts.append((oy + p[1] * sx, ox + p[0] * sx))
    return pts


class Piece:
    """Plaque biseautée : contour `poly`, fils `fils` (polylignes, sans la base cachée), profil h(a), wb(a), z au bord."""

    def __init__(self, nom, poly, fils, h, wb, ze, peint_biseau, peint_plat, peint_fil, trou=None, maxlen=2.0):
        self.nom, self.poly, self.h, self.wb, self.ze = nom, poly, h, wb, ze
        self.segs = [s for f in fils for s in subdiv(f, maxlen)]
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


def volume(pc, groupe, prolonge=1.3):
    """Biseaux (deux par tronçon de fil) + plats inclinés de la pièce pc."""
    for idx, (p, q, v0, v1) in enumerate(pc.segs):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        if not in_poly(np.array([(p + q) / 2 + n * 0.05]), pc.poly)[0]:
            n = -n
        am = float((p[0] + q[0]) / 2)
        h, wb = float(pc.h(am)), float(pc.wb(am))
        al = math.atan2(h - pc.ze, wb)
        e0 = wb * prolonge if v0 else 0.04
        e1 = wb * prolonge if v1 else 0.04
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

        def plat(P, sg=sg):
            P2 = P[..., :2]
            dE = pc.dE(P2)
            m = in_poly(P2, pc.poly) & (dE >= pc.wb(P2[..., 0]) - 0.03)
            if pc.trou is not None:
                m &= ~pc.trou(P2)
            col, em = pc.peint_plat(P2, dE)
            return col, em, m

        spec(groupe, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, ((a1 - a0) * math.sqrt(1 + sl * sl), b1 - b0, TH), {"south": plat})


def cst(v):
    return lambda a: v + 0.0 * np.asarray(a, float)


# --- peintures de la lame (sucre lilas mat, fil crème, bande rose bonbon, liseré lilas foncé ; aucune lumière)


# ------------------------------------------------------------------ pièces en volume (repère local : a, b dans le plan, z normal)
def piece_coeur(nom, sc, H, ZE, WB, lum=0, n=48):
    """Cœur de sucre framboise « coussin » (contour du cœur du set ×sc), lobes vers +a ; reflet en fenêtre sur le lobe +b, petit
    contre-reflet `_e` ; lum > 0 : toute la pièce luit (pointe-cœur chargée)."""
    poly = coeur_poly(1.05, 0.5, 1.2, -1.85, 0.42, n=n, sx=sc)
    pa = np.array(poly)
    ac = float((pa[:, 0].min() + pa[:, 0].max()) / 2)
    poly = [(a - ac, b) for a, b in poly]
    ref = (0.6 * sc - ac, 1.05 * sc)
    cref = (-0.95 * sc - ac, -1.05 * sc)

    def reflet(P, col):
        a, b = P[..., 0], P[..., 1]
        col = np.array(col, np.float32)
        da, db = a - ref[0], b - ref[1]
        u = (da * 0.6 + db * 0.8) / sc
        v = (-da * 0.8 + db * 0.6) / sc
        fen = (u / 0.62) ** 2 + (v / 0.26) ** 2 < 1
        col[fen] = BLANC
        col[fen & (np.abs(u + 0.08) < 0.05)] = FRAMB["hi"]
        cr = np.hypot(a - cref[0], b - cref[1]) < 0.17 * sc
        col[cr] = A((255, 220, 236))
        em = np.zeros(P.shape[:-1] + (3,), np.float32)
        if lum:
            em = np.clip(col * (lum / 225.0) * 0.95, 0, 225)
        em[cr] = (210, 150, 186) if not lum else (225, 200, 215)
        return col, (em if em.max() > 0 else None)

    def biseau(P, dE):
        f = np.clip(dE / WB, 0, 1)[..., None]
        dirn = np.stack([P[..., 0] + 0.2 * sc, P[..., 1]], -1)
        dirn = dirn / np.maximum(np.linalg.norm(dirn, axis=-1, keepdims=True), 1e-6)
        lumi = np.clip(0.5 + 0.5 * (dirn @ np.array((0.707, 0.707))), 0, 1)[..., None]
        col = lerp(FRAMB["low"], lerp(FRAMB["base"], FRAMB["hi"], 0.3), np.clip(f * 1.15, 0, 1)) * (0.9 + 0.2 * lumi)
        col = np.where(f < 0.1, FRAMB["low"] * 0.92, col)
        return reflet(P, col)

    def plat(P, dE):
        a, b = P[..., 0], P[..., 1]
        k = np.clip(0.45 + 0.2 * (a + b) / (2.2 * sc), 0, 1)[..., None]
        col = lerp(lerp(FRAMB["base"], FRAMB["hi"], 0.3), FRAMB["hi"], k) + np.zeros(P.shape[:-1] + (3,), np.float32)
        return reflet(P, col)

    def fil(P):
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + FRAMB["low"] * 0.85
        return col, (np.clip(col * lum / 225.0, 0, 225) if lum else None)

    return Piece(nom, poly, [poly + [poly[0]]], cst(H), cst(WB), ZE, biseau, plat, fil, maxlen=0.6)


def piece_dragee(nom, sc=0.2):
    """Dragée-cœur de sucre rose (lumière `_e`), comme celles de l'épée du set."""
    poly = coeur_poly(1.0, 0.45, 1.15, -1.6, 0.45, n=18, sx=sc)
    pa = np.array(poly)
    ac = float((pa[:, 0].min() + pa[:, 0].max()) / 2)
    poly = [(a - ac, b) for a, b in poly]
    H_D, ZE_D, WB_D = 0.40, 0.22, 0.24

    def bis(P, dE):
        return np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE, np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE_E

    def plat(P, dE):
        col, em = bis(P, dE)
        hl = np.hypot(P[..., 0] - (0.4 * sc - ac), P[..., 1] - 0.9 * sc) < 0.09
        col[hl] = BLANC
        em[hl] = (225, 200, 215)
        return col, em

    def fil(P):
        return np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE * 0.86, np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE_E * 0.8

    return Piece(nom, poly, [poly + [poly[0]]], cst(H_D), cst(WB_D), ZE_D, bis, plat, fil, maxlen=0.6)


def b_plume(u):
    """Bord extérieur d'une plume d'empennage (u = 0 avant, 1 arrière) : basse devant, haute vers l'arrière, bout arrondi
    (une goutte symétrique de 1 px faisait, à quatre, un bulbe lilas autour du bâton)."""
    u = np.asarray(u, float)
    monte = 0.16 + 0.5 * np.sin(np.pi / 2 * np.clip(u / 0.78, 0, 1)) ** 1.4
    fin = np.sqrt(np.clip(1 - ((u - 0.78) / 0.22) ** 2, 0, 1))
    return np.where(u <= 0.78, monte, 0.16 + 0.5 * fin)


def piece_plume(nom):
    """Plume d'empennage : goutte lilas à bout blanc, a vers l'avant (a = 1,05 avant, −1,05 arrière), b vers l'extérieur ;
    la base (b < 0,05) est cachée dans le bâton : seul le bord extérieur est biseauté."""
    us = np.linspace(0, 1, 17)
    out = [(1.05 - 2.1 * u, float(b_plume(u))) for u in us]
    poly = out + [(-1.05, -0.05), (1.05, -0.05)]
    H_P, ZE_P, WB_P = 0.2, 0.1, 0.16

    def peint(P):
        a, b = P[..., 0], P[..., 1]
        u = np.clip((1.05 - a) / 2.1, 0, 1)
        bo = b_plume(u)
        k = np.clip(b / np.maximum(bo, 0.2), 0, 1)
        col = lerp(LILAS["base"], LILAS["hi"], (0.25 + 0.6 * (1 - k))[..., None])
        col = np.where((u > 0.76)[..., None], lerp(col, BLANC, 0.85), col)
        col = np.where((np.abs(b - 0.42 * bo) < 0.05)[..., None] & (u > 0.12)[..., None], LILAS["low"] * 1.1, col)   # barbe
        return col * (1 + grain(P, 3.0))[..., None]

    def bis(P, dE):
        f = np.clip(dE / WB_P, 0, 1)[..., None]
        return lerp(LILAS["low"], peint(P), 0.45 + 0.55 * f), None

    def plat(P, dE):
        return peint(P), None

    def fil(P):
        return np.zeros(P.shape[:-1] + (3,), np.float32) + LILAS["low"], None

    return Piece(nom, poly, [out], cst(H_P), cst(WB_P), ZE_P, bis, plat, fil, maxlen=0.6)



# --- bras de l'arc : sucre lilas, plaque biseautée fermée (a le long du bras depuis la racine, b vers l'avant)
L_BR, AB_BR = 6.2, 2.0           # longueur du bras, recul du bout (courbe b = -AB·(a/L)²)
W0_BR, W1_BR = 0.92, 0.58        # demi-largeur racine -> bout
H0_BR, H1_BR, ZE_BR = 0.70, 0.36, 0.10
T_BR = 1.0                       # pente unique des biseaux (45°)


def br_c(a):
    return -AB_BR * (np.clip(np.asarray(a, float), 0, None) / L_BR) ** 2


def br_w(a):
    return W0_BR + (W1_BR - W0_BR) * np.clip(np.asarray(a, float) / L_BR, 0, 1)


def br_h(a):
    return H0_BR + (H1_BR - H0_BR) * np.asarray(a, float) / L_BR


def br_wb(a):
    return (br_h(a) - ZE_BR) / T_BR


def piece_branche(nom, n=24):
    def tn(a):
        t = np.array((1.0, -2 * AB_BR * max(a, 0.0) / L_BR ** 2))
        t /= np.linalg.norm(t)
        return t, np.array((-t[1], t[0]))

    gauche, droite = [], []
    for a in np.linspace(-0.35, L_BR, n):
        t, nv = tn(a)
        c = np.array((a, float(br_c(a))))
        w = float(br_w(a))
        gauche.append(c + nv * w)
        droite.append(c - nv * w)
    t, nv = tn(L_BR)
    c = np.array((L_BR, float(br_c(L_BR))))
    w = float(br_w(L_BR))
    cap = [c + nv * w * math.cos(ph) + t * w * math.sin(ph) for ph in np.linspace(0, math.pi, 11)[1:-1]]
    poly = [(float(p[0]), float(p[1])) for p in gauche + cap + droite[::-1]]

    def bis(P, dE):
        f = (dE / br_wb(P[..., 0]))[..., None]
        col = lerp(LILAS["hi"], LILAS["base"] * 1.04, np.clip((f - 0.42) / 0.45, 0, 1))
        col = np.where(f < 0.42, lerp(BONBON, LILAS["hi"], np.clip((f - 0.30) / 0.12, 0, 1)), col)
        col = np.where(f < 0.17, CREME + np.zeros_like(col), col)
        col = np.where(f >= 0.9, LISERE + np.zeros_like(col), col)
        return col * (1 + grain(P, 1.0))[..., None], None

    def plat(P, dE):
        a, b = P[..., 0], P[..., 1]
        k = np.exp(-((b - br_c(a) - 0.18) / 0.32) ** 2)
        col = lerp(LILAS["base"], LILAS["hi"], (0.2 + 0.55 * k)[..., None])
        return col * (1 + grain(P, 2.0))[..., None], None

    def fil(P):
        return np.zeros(P.shape[:-1] + (3,), np.float32) + CREME * 0.97, None

    return Piece(nom, poly, [poly + [poly[0]]], br_h, br_wb, ZE_BR, bis, plat, fil, maxlen=0.6)


SC_C = 0.95                                  # cœur-logement : 4,3 px de large
COEUR_P = piece_coeur("coeur", SC_C, 1.25, 0.36, 1.0)
DRAGEE_P = piece_dragee("dragee")
PLUME_P = piece_plume("plume")
BRANCHE_P = piece_branche("branche")
POINTE_P = piece_coeur("pointe", 2.2 / 4.5, 0.52, 0.24, 0.38, lum=225, n=36)


def conception():
    SPECS.clear()
    volume(COEUR_P, "coeur", prolonge=0.6)
    volume(DRAGEE_P, "dragee", prolonge=0.6)
    volume(PLUME_P, "plume", prolonge=0.6)
    volume(BRANCHE_P, "branche", prolonge=0.6)
    volume(POINTE_P, "pointe", prolonge=0.6)


conception()

# ------------------------------------------------------------------ tuiles des tours (une tuile par pan : éclairage, spirale)
def lum_tex(xn, t, ex):
    """Éclairage de dessin lissé texel par texel : normale interpolée en travers du pan (et en latitude pour une sphère)."""
    rad = ex["e"][None, None] + (xn * ex["tn"])[..., None] * ex["t3"][None, None]
    rad = rad / np.linalg.norm(rad, axis=-1, keepdims=True)
    if "lat0" in ex:
        lat = (ex["lat0"] + (ex["lat1"] - ex["lat0"]) * t)[..., None]
        Nn = np.cos(lat) * rad + np.sin(lat) * ex["ax"][None, None]
    else:
        Nn = ex["db"] * rad - ex["dr"] * ex["ax"][None, None]
        Nn = Nn / np.linalg.norm(Nn, axis=-1, keepdims=True)
    return np.clip(0.5 + 0.5 * (Nn @ LUMIERE), 0, 1)


def p_nuage(xn, t, y, r, L, ex):
    k = lum_tex(xn, t, ex)
    col = lerp(NUAGE["low"], NUAGE["base"], np.clip(0.25 + k * 1.1, 0, 1)[..., None])
    col = np.where((k > 0.9)[..., None], NUAGE["hi"], col)
    return col, None


def p_lavande(xn, t, y, r, L, ex):
    k = lum_tex(xn, t, ex)
    col = lerp(LAVANDE["low"], LAVANDE["hi"], k[..., None])
    if ex.get("arete"):
        col = np.where(((y < 0.05) | (y > L - 0.05))[..., None], LAVANDE["low"], col)
    return col, None


def p_guimauve(xn, t, y, r, L, ex):
    """Guimauve torsadée deux brins : phase = longueur (+ y0 du tronçon : spirale continue le long de la branche) + angle."""
    ang = ex["ang"] + xn * math.pi / ex["n"]
    f = ((y + ex.get("y0", 0.0)) / ex["pas"] + ang / math.pi) % 1.0
    rose = f < 0.5
    col = np.where(rose[..., None], GUIM_R, GUIM_C)
    edge = np.minimum(np.abs(f - 0.5), np.minimum(f, 1 - f))
    lum = lum_tex(xn, t, ex)[..., None]
    col = col * (0.8 + 0.22 * lum)
    sh = np.clip(1 - edge / 0.08, 0, 1)[..., None]
    col = lerp(col, np.where(rose[..., None], A((176, 60, 120)), A((206, 186, 214))), sh * 0.6)
    return col, None


def p_baton(xn, t, y, r, L, ex):
    """Bâton de sucre crème à une rayure lilas en spirale (fût de la flèche)."""
    ang = ex["ang"] + xn * math.pi / ex["n"]
    f = ((y + ex.get("y0", 0.0)) / ex["pas"] + ang / TAU) % 1.0
    lil = f < 0.32
    col = np.where(lil[..., None], LILAS["base"], CREME)
    lum = lum_tex(xn, t, ex)[..., None]
    return col * (0.78 + 0.24 * lum), None


def p_framb(xn, t, y, r, L, ex):
    k = lum_tex(xn, t, ex)
    return lerp(FRAMB["low"], FRAMB["base"], np.clip(0.3 + k, 0, 1)[..., None]), None


PEINTRES = {"nuage": p_nuage, "lavande": p_lavande, "guimauve": p_guimauve, "baton": p_baton, "framb": p_framb}

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
    col, em = PEINTRES[mat](xn, t, y, r, L, dict(ex))
    TILES[nom] = _rgba(col, mask, em)
    return nom


# ------------------------------------------------------------------ tuiles peintes (bouffée de cœurs)


# ------------------------------------------------------------------ tuiles peintes (corde, nuage de sucre, paillettes)
def flat(col, em=None, n=8):
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    out[..., 3] = 255
    e = None
    if em is not None:
        e = out.copy()
        e[..., :3] = np.clip(em, 0, 225).astype(np.uint8)
    return out, e


TILES["corde"] = flat(CORDE, CORDE_E)


def sugar_puff(N=64):
    """Petit nuage de sucre translucide (tuile du groupe trans_paillettes)."""
    yy, xx = np.mgrid[0:N, 0:N]
    u, v = (xx + 0.5) / N, (yy + 0.5) / N
    f = np.zeros((N, N))
    for px, py, pr in ((0.5, 0.56, 0.3), (0.3, 0.6, 0.21), (0.7, 0.6, 0.21), (0.42, 0.36, 0.2), (0.62, 0.38, 0.18)):
        f = np.maximum(f, np.clip(1 - np.hypot(u - px, v - py) / pr, 0, 1))
    a = np.clip(f / 0.35, 0, 1)
    al = (60 + 150 * a + 40 * np.clip((f - 0.15) / 0.2, 0, 1) * (1 - a)) * (f > 0.02)
    al = np.clip(al, 0, 230).astype(np.int32)
    col = lerp(A((255, 168, 212)), A((255, 244, 250)), np.clip(1 - v * 1.2, 0, 1)[..., None])
    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    out[..., 3] = al
    out[al == 0, :3] = 0
    return out, None


TILES["sucre"] = sugar_puff()
TRANS.add("sucre")


def star_tile(N=24):
    """Paillette-étoile à quatre branches arrondies, `_e`."""
    ss = 4
    yy, xx = np.mgrid[0:N * ss, 0:N * ss]
    u = (xx + 0.5) / (N * ss) * 2 - 1
    v = (yy + 0.5) / (N * ss) * 2 - 1
    r = np.hypot(u, v)
    th = np.arctan2(v, u)
    m = r <= 0.32 + 0.62 * np.abs(np.cos(2 * th)) ** 6
    col = lerp(A((255, 196, 228)), A((255, 255, 255)), np.clip(1 - r * 1.4, 0, 1)[..., None])
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((N, N), Image.LANCZOS))
    al = np.array(Image.fromarray((m * 255).astype(np.uint8), "L").resize((N, N), Image.LANCZOS)) > 110
    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = al * 255
    out[~al, :3] = 0
    e = out.copy()
    e[al, :3] = (225, 205, 225)
    return out, e


TILES["etoile"] = star_tile()


# ------------------------------------------------------------------ géométrie (monde)
elements, groups = [], {}
CLEAR = "CLEAR"
SIX = ("north", "south", "east", "west", "up", "down")

def nuid():
    return str(_uuid.uuid4())


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx (ordre du mod et du renderer)."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if abs(R[2, 0]) > 1 - 1e-9:
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
    """profil = [(b0, r0, b1, r1, mat, ex), ...] le long de ax depuis O (monde) ; une couronne de n pans par tronçon,
    une tuile par pan (ex["lum"] = éclairage de dessin du pan, ex["ang"] = angle du pan)."""
    O, ax = np.asarray(O, float), unit(np.asarray(ax, float))
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    for i, (b0, r0, b1, r1, mat, ex) in enumerate(profil):
        L_ = math.hypot(b1 - b0, r1 - r0)
        if L_ < 1e-4:
            continue
        db, dr = (b1 - b0) / L_, (r1 - r0) / L_
        wm = max(2 * r0 * tn, 2 * r1 * tn) + 2 * OVW
        for k in range(n):
            th = phase + TAU * k / n
            e = math.cos(th) * ref + math.sin(th) * w3
            P0, P1 = O + b0 * ax + r0 * e, O + b1 * ax + r1 * e
            Y = unit(P1 - P0)
            N = -dr * ax + db * e
            X = np.cross(Y, N)
            exk = dict(ex, ang=th, n=n, e=e, t3=unit(np.cross(ax, e)), ax=ax, tn=tn, db=db, dr=dr)
            tile = tuile_pan(f"{nom}{i}_{k}", mat, L_, 2 * r0 * tn, 2 * r1 * tn, r0, r1, exk)
            boite(g, f"{nom}{i}_{k}", (P0 + P1) / 2 - N * TH / 2, X, Y, (wm, L_ + 2 * OVL, TH), {"south": tile})


def boule(g, nom, C, R, n=12, anneaux=6, mat="nuage"):
    """Sphère de pans (axe z : vue de l'inventaire, contour à n pans), du dos (-z) à l'avant (+z)."""
    prof = []
    for i in range(anneaux):
        l0 = -math.pi / 2 + math.pi * i / anneaux
        l1 = -math.pi / 2 + math.pi * (i + 1) / anneaux
        prof.append((R * math.sin(l0), R * math.cos(l0), R * math.sin(l1), R * math.cos(l1), mat, {"lat0": l0, "lat1": l1}))
    tour(g, nom, C, V(0, 0, 1), Wv(1, 0), prof, n=n, phase=math.pi / n)


def bone_node(name):
    g = groups[name]
    return {"name": g["nom"], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


# nuages : (a, b, rayon) ; quillons de part et d'autre du cœur, pommeau en trois bosses


def coins():
    P = []
    for e in elements:
        f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
        R = rmat(*e.get("rotation", (0, 0, 0)))
        for i in range(8):
            c = np.array([(f, t)[(i >> k) & 1][k] for k in range(3)])
            P.append(R @ (c - o) + o)
    return np.array(P)

S_ = V(-1, 1, 0) / math.sqrt(2)     # vers l'avant (carreau : haut à gauche de l'image vanilla)
H_ = V(1, 1, 0) / math.sqrt(2)      # le long de l'arc (bras haut en haut à droite)
Z_ = V(0, 0, 1)                     # face vue dans l'inventaire
S_MID = -0.8                        # milieu de l'arbalète le long du fût (centrée dans le bloc)
C0 = V(8, 8, 8) - S_ * S_MID
Repere.th, Repere.P0 = math.radians(45), C0
ZB = 0.85                           # plan de l'arc, de la corde et du carreau (au-dessus de l'arbrier)


def W(s, h=0.0, z=0.0):
    return C0 + S_ * s + H_ * h + Z_ * z


def poser(g, piece, C, ca, cb, pre=""):
    """Pose les cubes de `piece` (specs en repère local) : monde = C + ca·a + cb·b + (ca × cb)·z (rotation pure)."""
    ca, cb = unit(np.asarray(ca, float)), unit(np.asarray(cb, float))
    M = np.column_stack([ca, cb, np.cross(ca, cb)])
    n = 0
    for sp in SPECS:
        if sp["groupe"] != piece:
            continue
        boite(g, pre + sp["nom"], np.asarray(C, float) + M @ sp["c"], M @ sp["X"], M @ sp["Y"], sp["s"], sp["faces"])
        n += 1
    assert n, piece
    return M


def guimauve(g, nom, s0, s1, r, seg=2.0, pas=1.4, y0=0.0):
    """Arbrier de guimauve torsadée le long de S_ (h = 0, z = 0), tronçons ≤ seg, spirale continue."""
    n = max(1, int(math.ceil((s1 - s0) / seg - 1e-6)))
    for i in range(n):
        a, b = s0 + (s1 - s0) * i / n, s0 + (s1 - s0) * (i + 1) / n
        tour(g, f"{nom}{i}_", W(a), S_, Z_, [(-0.03, r, b - a + 0.03, r, "guimauve", {"pas": pas, "y0": y0 + a - s0})], n=12)


def bague(g, nom, P, ax, rb, l=0.3):
    tour(g, nom, P, ax, Z_ if abs(float(np.asarray(ax) @ Z_)) < 0.9 else S_,
         [(-l, rb - 0.18, -l + 0.06, rb, "lavande", {}), (-l + 0.06, rb, l - 0.06, rb, "lavande", {"arete": True}),
          (l - 0.06, rb, l, rb - 0.18, "lavande", {})], n=12)


# ------------------------------------------------------------------ fût (groupe `arbalete`, toujours dessiné)
ARB = group("arbalete", W(0))
S_H = 3.7                                   # centre du cœur-logement
C_HEART = W(S_H, 0, ZB)
coeur = group("coeur", C_HEART, parent=ARB)
M_COEUR = poser(coeur, "coeur", C_HEART, V(0, 1, 0), V(-1, 0, 0))      # droit dans la case (lobes vers +Y), reflet en haut à gauche
EM_COEUR = group("emit_mc_heart", W(S_H + 1.2, 0, ZB + 0.8), parent=coeur)
_pc = np.array(COEUR_P.poly)
A_CREUX = float(_pc[(np.abs(_pc[:, 1]) < 0.25) & (_pc[:, 0] > 0), 0].min())
boule(coeur, "creux", C_HEART + M_COEUR @ V(A_CREUX - 0.4, 0, 0), 0.72, n=12, anneaux=6, mat="framb")
_sw = np.array([(M_COEUR @ V(a, b, 0)) @ S_ for a, b in COEUR_P.poly])
print("cœur : de s =", round(S_H + float(_sw.min()), 2), "à", round(S_H + float(_sw.max()), 2))

# arbrier de guimauve : crosse dodue (r 0,86) entre deux bagues, fût (r 0,62) qui entre dans l'échancrure du cœur
S_T, S_C = -6.3, -3.7
guimauve(ARB, "crosse", S_T, S_C, 0.86, seg=1.4, pas=1.5)
guimauve(ARB, "fut", S_C, S_H - 0.5, 0.62, seg=2.1, pas=1.3)
bague(ARB, "bague_crosse", W(S_C), S_, 1.04)
bague(ARB, "bague_talon", W(S_T + 0.12), S_, 1.04)
bague(ARB, "bague_avant", W(S_H - 1.9), S_, 0.8, l=0.22)
# talon-nuage : trois bosses au bout de la crosse
NUAGE_T = group("nuage_talon", W(S_T), parent=ARB)
for j, (ds, dh, dz, r) in enumerate(((-0.75, 0.0, 0.0, 1.12), (-0.25, 0.95, 0.15, 0.8), (-0.3, -0.92, -0.1, 0.78))):
    boule(NUAGE_T, f"talon{j}_", W(S_T + ds, dh, dz), r, n=12, anneaux=6)
# noix lavande en travers, détente lavande sous l'arbrier
A_NOIX, A_LATCH = -2.0, -1.5
tour(ARB, "noix", W(A_NOIX, -0.85, 0.42), H_, Z_, [(0.0, 0.0, 0.06, 0.34, "lavande", {}), (0.06, 0.36, 1.64, 0.36, "lavande", {"arete": True}),
                                               (1.64, 0.34, 1.7, 0.0, "lavande", {})], n=10)
_dt = unit(-Z_ * 0.9 - S_ * 0.45)
tour(ARB, "detente", W(-2.9, 0, -0.45), _dt, S_, [(0.0, 0.2, 0.85, 0.17, "lavande", {}), (0.85, 0.17, 1.0, 0.0, "lavande", {})], n=8)
boule(ARB, "detente_bout", W(-2.9, 0, -0.45) + _dt * 0.95, 0.24, n=8, anneaux=4, mat="lavande")
# étrier : anneau lavande en U devant la pointe du cœur (jambes cachées dans le cœur)
Z_ETR, R_ETR, HW, S_U = ZB - 0.45, 0.26, 1.0, 6.3
pts = [(5.0, HW), (S_U, HW)] + [(S_U + HW * math.sin(p), HW * math.cos(p)) for p in np.linspace(0, math.pi, 13)[1:-1]] + [(S_U, -HW), (5.0, -HW)]
for i in range(len(pts) - 1):
    p, q = W(*pts[i], Z_ETR), W(*pts[i + 1], Z_ETR)
    L = float(np.linalg.norm(q - p))
    tour(ARB, f"etrier{i}_", p, q - p, Z_, [(-0.06, R_ETR, L + 0.06, R_ETR, "lavande", {})], n=8)
EMIT_S = S_U + HW + 0.6

# --- nuage de sucre et paillettes (event_release), K fois plus petits au repos, enfouis dans le cœur (creux et fermé)
TP = group("trans_paillettes", C_HEART, parent=ARB)
group("ctrl_alpha", C_HEART, parent=TP)
for j, (ds, dh, r) in enumerate(((0.0, 0.0, 2.0), (0.45, -1.6, 1.4), (0.25, 1.65, 1.45))):
    c = C_HEART + (S_ * ds + H_ * dh + Z_ * (0.25 * (j - 1))) / K
    boite(TP, f"sucre{j}", c, H_, S_, (2 * r / K, 2 * r / K, 0.3 / K), {"south": "sucre", "north": "sucre"})
ET = group("etincelles", C_HEART, parent=ARB)
for j, (ds, dh, dz, r) in enumerate(((2.2, 0.5, 1.0, 0.55), (0.8, -2.8, -0.6, 0.45), (1.2, 2.9, 0.5, 0.5), (3.0, -1.3, -0.4, 0.4),
                                     (-0.5, 1.8, 1.0, 0.38))):
    c = C_HEART + (S_ * ds + H_ * dh + Z_ * dz) / K
    boite(ET, f"etoile{j}", c, H_, S_, (2 * r / K, 2 * r / K, 0.3 / K), {"south": "etoile", "north": "etoile"})

# ------------------------------------------------------------------ étapes : bras reposés, corde, carreau ou fusée
R_S, R_H = S_H - 0.2, 1.0                  # racine des bras (dans les lobes du cœur)
# (nom, recul des bras en degrés, recul de la corde 0..1, chargement)
ETAPES = [("repos", 0.0, 0.0, None), ("bande_1", 5.0, 0.33, None), ("bande_2", 10.0, 0.66, None), ("bande_3", 14.0, 1.0, None),
          ("chargee", 14.0, 1.0, "carreau"), ("chargee_fusee", 14.0, 1.0, "fusee")]
STAGE, BRG, CORDE_G, CTRLS, POINTE_G = {}, {}, {}, {}, {}
A_DR = 2.4                                  # dragée sur le plat du bras, à 2,4 px de la racine


def corde(g, a, b, nom):
    d = unit(b - a)
    Lc = float(np.linalg.norm(b - a))
    boite(g, nom, (a + b) / 2, d, np.cross(Z_, d), (Lc + 0.1, 0.32, 0.32), {f: "corde" for f in SIX})


for nom_e, deg, rec, charg in ETAPES:
    st = group(objet.etape(nom_e, "arbalete"), (8, 8, 8))
    STAGE[nom_e] = st
    drag = group(f"dragees_{nom_e}", C_HEART, parent=st)
    CTRLS[nom_e] = group(f"ctrl_lumiere_{nom_e}", C_HEART, parent=drag, nom="ctrl_lumiere")
    th = math.radians(deg)
    BRG[nom_e], att = [], {}
    for side, sg in (("haut", 1), ("bas", -1)):
        Rt = W(R_S, sg * R_H, ZB)
        gb = group(f"bras_{side}_{nom_e}", Rt, parent=st)
        BRG[nom_e].append(gb)
        ca = sg * H_ * math.cos(th) - S_ * math.sin(th)
        cb = S_ * math.cos(th) + sg * H_ * math.sin(th)
        poser(gb, "branche", Rt, ca, cb, pre=f"{nom_e}_{side}_")
        bc = float(br_c(L_BR))
        boule(gb, "perle", Rt + ca * (L_BR + 0.12) + cb * bc, 0.5, n=10, anneaux=5, mat="lavande")
        att[side] = Rt + ca * (L_BR + 0.12) + cb * bc
        base = Rt + ca * A_DR + cb * (float(br_c(A_DR)) + 0.08)
        for zz in (1, -1):
            poser(drag, "dragee", base + Z_ * zz * (float(br_h(A_DR)) - 0.04), V(0, 1, 0), V(-zz, 0, 0), pre=f"{nom_e}_{side}{'pm'[zz < 0]}_")
    ah, ab = att["haut"], att["bas"]
    s_att = float((ah - C0) @ S_)
    if rec == 0:
        gc = group(f"corde_{nom_e}", (ah + ab) / 2, parent=st)
        corde(gc, ah, ab, f"corde_{nom_e}")
        CORDE_G[nom_e] = gc
        print(f"repos : attaches de la corde à s = {s_att:.2f}, h = ±{float((ah - C0) @ H_):.2f}")
        continue
    nock = W(s_att + (A_LATCH - s_att) * rec, 0.0, ZB)
    gc = group(f"corde_{nom_e}", nock, parent=st)
    corde(gc, ah, nock, f"corde_h_{nom_e}")
    corde(gc, ab, nock, f"corde_b_{nom_e}")
    CORDE_G[nom_e] = gc
    if charg == "carreau":
        fl = group(f"carreau_{nom_e}", nock, parent=st)
        a_, b_ = A_LATCH + 0.1, 8.2
        nseg = int(math.ceil((b_ - a_) / 2.6))
        for i in range(nseg):
            s0, s1 = a_ + (b_ - a_) * i / nseg, a_ + (b_ - a_) * (i + 1) / nseg
            tour(fl, f"baton{i}_", W(s0, 0, ZB), S_, Z_, [(-0.03, 0.21, s1 - s0 + 0.03, 0.21, "baton", {"pas": 0.9, "y0": s0 - a_})], n=8)
        boule(fl, "encoche_", W(A_LATCH + 0.12, 0, ZB), 0.3, n=8, anneaux=4)
        for k, cb in enumerate((H_, -H_, Z_)):
            poser(fl, "plume", W(A_LATCH + 1.35, 0, ZB) + cb * 0.08, S_, cb, pre=f"{k}_")
        ct = W(8.2 + 0.45, 0, ZB)
        gp = group(f"pointe_{nom_e}", ct, parent=fl)
        POINTE_G[nom_e] = gp
        poser(gp, "pointe", ct, -S_, H_)
    elif charg == "fusee":
        fu = group(f"fusee_{nom_e}", nock, parent=st)
        zf = ZB + 0.1
        a0, a1 = A_LATCH + 0.1, 7.0
        nseg = int(math.ceil((a1 - a0) / 2.6))
        for i in range(nseg):
            s0, s1 = a0 + (a1 - a0) * i / nseg, a0 + (a1 - a0) * (i + 1) / nseg
            tour(fu, f"fusee{i}_", W(s0, 0, zf), S_, Z_, [(-0.03, 0.42, s1 - s0 + 0.03, 0.42, "baton", {"pas": 1.1, "y0": s0 - a0})], n=10)
        tour(fu, "fusee_fond", W(a0, 0, zf), S_, Z_, [(-0.02, 0.0, 0.04, 0.5, "lavande", {}), (0.04, 0.5, 0.3, 0.5, "lavande", {"arete": True}),
                                                     (0.3, 0.5, 0.36, 0.4, "lavande", {})], n=10)
        for k, s0 in enumerate((0.0, 1.2)):
            bague(fu, f"fusee_bague{k}_", W(s0, 0, zf), S_, 0.52, l=0.18)
        tour(fu, "coiffe", W(a1, 0, zf), S_, Z_, [(-0.02, 0.44, 0.35, 0.44, "framb", {}), (0.35, 0.44, 0.75, 0.32, "framb", {}),
                                                 (0.75, 0.32, 1.15, 0.0, "framb", {})], n=10)
        tour(fu, "meche", W(a0, 0, zf), -S_, Z_ * 0.3 + H_, [(0.0, 0.08, 0.5, 0.06, "framb", {}), (0.5, 0.06, 0.58, 0.0, "framb", {})], n=6)

outliner = [bone_node(ARB)] + [bone_node(STAGE[e]) for e, *_ in ETAPES]
P = coins()

def atlas():
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    UV = {}
    # rangement en ligne d'horizon (beaucoup de petites tuiles)
    sky = np.zeros(TEX, int)
    for n, (im, ime) in sorted(TILES.items(), key=lambda it: (-it[1][0].shape[0], -it[1][0].shape[1], it[0])):
        h, w = im.shape[:2]
        best = None
        for x in range(0, TEX - w + 1):
            y = int(sky[x:x + w + 1].max()) if x + w + 1 <= TEX else int(sky[x:x + w].max())
            if y + h <= TEX - 6 and (best is None or y < best[1]):
                best = (x, y)
                if y == 0:
                    break
        assert best is not None, "atlas plein"
        x, y = best
        UV[n] = [x, y, x + w, y + h]
        tex[y:y + h, x:x + w] = im
        if ime is not None and AVEC_E:
            tex_e[y:y + h, x:x + w] = ime
        sky[x:min(TEX, x + w + 1)] = y + h + 1
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
    print(f"atlas : {len(TILES)} tuiles, rempli jusqu'à y = {int(sky.max())}")
    return res, UV


(tex_b64, tex_e_b64), UV = atlas()
for e in elements:
    for fc in e["faces"].values():
        fc["uv"] = list(UV[fc["uv"]])


# ------------------------------------------------------------------ animations (objet vivant, guide 14)
def kf(t, x, y, z, ch="rotation"):
    f = lambda v: v if isinstance(v, str) else f"{v + 0.0:.4f}".rstrip("0").rstrip(".")
    return {"channel": ch, "data_points": [{"x": f(x), "y": f(y), "z": f(z)}], "time": round(t, 4), "interpolation": "linear"}


def anim(name, length, tracks, fps=24, loop="loop"):
    """tracks : {(groupe, canal): f(t) -> (x, y, z)} échantillonné, ou (x, y, z) constant (Molang permis)."""
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A_ = {}
    for (g, ch), fn in tracks.items():
        ks = [kf(t, *fn(t), ch=ch) for t in times] if callable(fn) else [kf(0.0, *fn, ch=ch), kf(length, *fn, ch=ch)]
        A_.setdefault(groups[g]["uuid"], {"name": groups[g]["nom"], "type": "bone", "keyframes": []})["keyframes"] += ks
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": False, "animators": A_}


def le_long(v, d):
    w = np.asarray(d, float) * v
    return float(w[0]), float(w[1]), float(w[2])


def uni(k):
    return k, k, k


def battement(t, t0, amp):
    """Double battement « lub-dub » à partir de t0 (0,5 s en tout), retour exact à 0."""
    u = t - t0
    return amp * (bump(u, 0.0, 0.07, 0.09, 0.2) + 0.6 * bump(u, 0.2, 0.27, 0.29, 0.45))


def plop(t, t0=0.0, d=0.5, k0=0.6):
    u = (t - t0) / d
    if u <= 0:
        return k0
    if u >= 1:
        return 1.0
    return float(np.interp(u, [0, 0.35, 0.62, 0.82, 1.0], [k0, 1.2, 0.93, 1.02, 1.0]))


# --- item_idle (8 s) : deux doubles battements, dragées qui s'avivent au battement, talon-nuage qui respire
L_IDLE = 8.0
idle_tracks = {(coeur, "scale"): lambda t: uni(1 + battement(t, 0.3, 0.06) + battement(t, 4.3, 0.06)),
               (NUAGE_T, "scale"): lambda t: uni(1 + 0.03 * math.sin(TAU * 2 * t / L_IDLE))}
for e in CTRLS:
    idle_tracks[(CTRLS[e], "position")] = lambda t: (0.4 * (battement(t, 0.3, 1.0) + battement(t, 4.3, 1.0)), 0.0, 0.0)
item_idle = anim("item_idle", L_IDLE, idle_tracks, fps=20)

# --- item_use (0,6 s) : le cœur bat plus fort à mesure que l'arbalète se tend ; les bras frémissent
BAT = "math.pow(math.max(0, math.sin(q.anim_time * 600)), 3)"
use_tracks = {(coeur, "scale"): tuple(["1 + 0.09 * q.use_progress * " + BAT] * 3)}
for e in ("bande_1", "bande_2", "bande_3"):
    use_tracks[(CTRLS[e], "position")] = ("0.6 * q.use_progress", "0", "0")
    for gb, sg in zip(BRG[e], (1, -1)):
        use_tracks[(gb, "rotation")] = ("0", "0", f"{sg} * 0.6 * q.use_progress * math.sin(q.anim_time * 2400)")
item_use = anim("item_use", 0.6, use_tracks)

# --- event_charged (0,5 s) : la noix prend la corde ; plop du cœur, dragées et pointe-cœur qui s'allument (sans son)
ch_tracks = {(coeur, "scale"): lambda t: uni(1 - 0.08 * bump(t, 0.0, 0.04, 0.06, 0.12) + 0.1 * bump(t, 0.08, 0.15, 0.18, 0.4))}
for e in ("chargee", "chargee_fusee"):
    ch_tracks[(CTRLS[e], "position")] = lambda t: (0.9 * bump(t, 0.0, 0.06, 0.15, 0.48), 0.0, 0.0)
ch_tracks[(POINTE_G["chargee"], "scale")] = lambda t: uni(plop(t, 0.04, 0.42, 0.7))
event_charged = anim("event_charged", 0.5, ch_tracks, fps=40, loop="once")

# --- event_release (0,9 s) : squash du cœur, bras qui vibrent, corde qui « twang », nuage de sucre qui jaillit et monte
L_REL = 0.9


def squash(t):
    return 1 - 0.12 * bump(t, 0.0, 0.035, 0.05, 0.1) + 0.12 * bump(t, 0.06, 0.12, 0.16, 0.3) - 0.03 * bump(t, 0.28, 0.34, 0.36, 0.48)


def vib(t, amp):
    if t < 0.02:
        return 0.0
    u = t - 0.02
    return amp * math.sin(TAU * u / 0.11) * math.exp(-u / 0.12) * (1 - sm(t, 0.7, 0.85))


def nuage_s(t):
    w = sm(t, 0.03, 0.14) * (1 + 0.15 * bump(t, 0.1, 0.16, 0.2, 0.32) + 0.3 * sm(t, 0.2, 0.78)) * (1 - sm(t, 0.8, 0.84))
    return uni(1 + (K - 1) * w)


def nuage_p(t):
    env = 1 - sm(t, 0.82, 0.84)
    return le_long(env, S_ * (2.6 * sm(t, 0.03, 0.25) + 1.4 * sm(t, 0.25, 0.8)) + V(0, 1, 0) * 1.6 * sm(t, 0.15, 0.8))


def nuage_a(t):
    return -sm(t, 0.35, 0.78) * (1 - sm(t, 0.86, 0.9)), 0.0, 0.0


def etin_s(t):
    w = sm(t, 0.05, 0.14) * (1 + 0.2 * bump(t, 0.1, 0.15, 0.2, 0.3)) * (1 - sm(t, 0.45, 0.72))
    return uni(1 + (K - 1) * w)


rel_tracks = {(coeur, "scale"): lambda t: uni(squash(t)),
              (BRG["repos"][0], "rotation"): lambda t: (0.0, 0.0, vib(t, 2.4)),
              (BRG["repos"][1], "rotation"): lambda t: (0.0, 0.0, -vib(t, 2.4)),
              (CORDE_G["repos"], "position"): lambda t: le_long(vib(t, 0.35), S_),
              (TP, "scale"): nuage_s, (TP, "position"): nuage_p, ("ctrl_alpha", "position"): nuage_a,
              (ET, "scale"): etin_s, (ET, "position"): nuage_p,
              (ET, "rotation"): lambda t: (0.0, 0.0, 120 * sm(t, 0.05, 0.75) * (1 - sm(t, 0.8, 0.84))),
              (CTRLS["repos"], "position"): lambda t: (0.8 * sm(t, 0.0, 0.04) * (1 - sm(t, 0.1, 0.6)), 0.0, 0.0)}
event_release = anim("event_release", L_REL, rel_tracks, fps=50, loop="once")

# --- event_select (0,6 s) : « plop » du cœur, puis du talon-nuage
sel_tracks = {(coeur, "scale"): lambda t: uni(plop(t, 0.0, 0.45)),
              (NUAGE_T, "scale"): lambda t: uni(plop(t, 0.1, 0.45))}
event_select = anim("event_select", 0.6, sel_tracks, fps=40, loop="once")

ANIMS = [item_idle, item_use, event_charged, event_release, event_select]
ANIMS[0]["selected"] = True


# ------------------------------------------------------------------ écriture
def ids_de(name):
    g = groups[name]
    return set(g["ids"]).union(*[ids_de(n) for n, gg in groups.items() if gg["parent"] == name])


def coins_de(ids):
    sel = [e for e in elements if e["uuid"] in ids]
    Pq = []
    for e in sel:
        f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
        R = rmat(*e.get("rotation", (0, 0, 0)))
        for i in range(8):
            c = np.array([(f, t)[(i >> k) & 1][k] for k in range(3)])
            Pq.append(R @ (c - o) + o)
    return np.array(Pq)


assert len(elements) <= 8192, f"budget : {len(elements)} cubes"
_P = coins_de(ids_de(ARB) | ids_de(STAGE["repos"]))
_lo, _hi = _P[:, :2].min(0), _P[:, :2].max(0)
_c = (_lo + _hi) / 2
GUI_S = round(min(1.0, 15.4 / float(max(_hi - _lo))), 3)
GUI_T = [round(float((8 - _c[0]) * GUI_S), 2), round(float((8 - _c[1]) * GUI_S), 2), 0]
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
AFFICHAGE = objet.affichage("arbalete", gui={"scale": [GUI_S] * 3, "translation": GUI_T})
model = objet.modele(NOM, "arbalete", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import embarquer_sons  # noqa: E402
# Un seul son, au tir (event_release : l'arbalète passe de chargée à vide), à 0,04 s (une clé à 0,0 s est muette au premier
# déclenchement, diagnostic F5). Aucun son ailleurs (ni event_use_start, ni event_enter_*, ni event_charged).
embarquer_sons(model, {"paillettes": "sons/paillettes.ogg"})
event_release["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "paillettes", "file": ""}], "time": 0.04}]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print("boîte :", P.min(0).round(2).tolist(), "->", P.max(0).round(2).tolist(), "; gui", GUI_S, GUI_T)
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
