"""Écu de l'orage : skin de bouclier (guide 14, type `bouclier`), ensemble Orage (thème Éléments). Design original.
Écrit skin_bouclier_orage.png, skin_bouclier_orage_e.png et .build/skin_bouclier_orage_brut.bbmodel à côté de ce script.

Idée : deux ailes de faucon en acier d'orage forgé, repliées l'une contre l'autre autour d'un tambour d'or aux trois virgules
(l'umbo) ; la foudre est couchée dans des gouttières creusées qui partent du tambour vers les plumes, et s'allume quand on
lève l'écu. Famille Orage (.claude/styles/orage.md, ailes v7, épée, trident) : acier bleu-noir martelé, fil poli clair + _e,
bande de revenu cuivre puis violet, liseré d'or, tambour aux virgules, pointe de cristal, foudre en géométrie (cœur clair +
_e, gaine add_), née d'un point (le tambour, la pointe du cimier).
Références (.claude/references/objets/boucliers.md) : écu (haut droit, flancs qui se referment en pointe, corps bombé), umbo
(bosse bombée sur la poignée), orle (bord renforcé), traverses et poignée au dos ; aile de faucon repliée (poignet saillant,
couvertures en écailles, primaires dont les pointes s'étagent vers le bas).

Vrai volume (recette .claude/references/objets/volume-3d.md), pas de plaques empilées :
- chaque aile = une plaque biseautée fermée (biseaux en cubes inclinés à pente unique 40°, plats inclinés qui suivent
  l'amincissement 1,90 px à la quille -> 1,18 px au bord, faces échantillonnées texel par texel, découpées par l'alpha,
  recouvrement 0,08) ; les deux ailes sont tournées de 14° autour de la quille : l'écu est bombé en carène ;
- bord extérieur biseauté (fil poli + _e, revenu cuivre/violet peints sur les biseaux), pointes des primaires en dents qui
  s'étagent jusqu'à la pointe de l'écu, poignet en éperon ; bord haut roulé (bourrelet octogonal de 2,4 px, bagues d'or) ;
- couvertures = une seconde plaque biseautée de 0,72 px à trois écailles, à moitié enfoncée dans l'aile (relief forgé) ;
- trois gouttières en zigzag par aile, creusées (parois + fond), la foudre couchée au fond des deux côtés (vue de face en
  3e personne, de dos en 1re personne) ;
- umbo : tambour d'or à 16 pans en deux gradins (peau bleu nuit cloutée d'or, médaillon aux trois virgules) ; quille
  octogonale devant et derrière, pointe de cristal en haut (paratonnerre), talon d'or et de cristal en bas ;
- dos : deux traverses octogonales, montants, poignée de cuir bleu nuit entre bagues d'or (place de la poignée vanilla).

Repère : celui du bouclier de Minecraft (modèle d'entité retourné, centré sur l'origine du bloc ; plaque vanilla 12 x 22 de
z = 1 à 2, face vers +Z, poignée vers -Z). Réglages Display recopiés de `item/shield.json` (jar 26.1.2), comme
skin_bouclier_givre. Étapes `repos` et `bloque` = deux copies de l'écu (mêmes tuiles). Le mod garde les réglages Display du
repos pendant le blocage : `item_use` pose l'écu comme `item/shield_blocking` par le groupe `pose_bloque` (rotation et
position en Molang selon q.in_first_person et q.hand, calculées et contrôlées par matrices ici, technique de
skin_bouclier_givre).

Objet vivant (sobre) :
- item_idle (8 s) : la foudre couchée dort (gaine faible qui grésille, une gouttière se ravive de temps en temps) ;
- item_gui : calme ;
- item_use : pose de blocage ; gouttières allumées (étape bloque : cœur vif, gaine forte qui grésille), arcs qui sautent
  par moments de la pointe du cimier aux deux poignets ; **décharge en retour** quand un coup est bloqué : quatre éclairs
  ramifiés jaillissent du tambour vers l'avant + gerbe emit_mc_electric_spark (ctrl_emit). Le guide n'a pas d'événement
  « coup bloqué » : déclenchée par q.hit_by_entity ou par la hausse de q.item_durability (un coup bloqué use le bouclier ;
  variables mémorisées v.bp / v.bt mises à jour par le groupe vide `calcul_parade`, toujours dessiné) ; 0,45 s ;
- event_use_start (0,5 s) : la foudre s'allume gouttière après gouttière, du tambour vers le bord, arcs du cimier ;
  aucun son (correctif F6 : rejoué à chaque coupure de l'utilisation ; garde aussi dans item_idle). Aucun son à la décharge : une clé de son ne peut pas suivre une
  requête Molang ;
- event_select (0,7 s) : la foudre frappe la pointe du cimier, puis les gouttières s'allument une à une.
Éclairs des événements repliés à 1/10 sur un pivot caché dans le métal (cimier, tambour), dépliés par `scale` par une seule
animation chacun (échelles superposées : aucune).
Fonctions avancées : add_, ctrl_alpha, ctrl_emit, emit_mc_electric_spark, scale animé, calque _e, étapes repos/bloque,
animations d'objet (item_idle, item_gui, item_use, event_use_start, event_select), Molang (q.in_first_person, q.hand,
q.hit_by_entity, q.item_durability, q.life_time, variables mémorisées), son embarqué. À juger en jeu : pose de blocage (deux
mains, 1re et 3e personne), décharge sur un coup bloqué (q.hit_by_entity vaut-il 1 sur un coup bloqué ? sinon l'usure ; rien
en créatif), son d'objet, lecture du volume par la tranche.
"""
import base64, io, json, math, os, random, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image, ImageDraw

NOM = "skin_bouclier_orage"
TEX = 512
TAU = 2 * math.pi
SS = 4
FOLD = 0.1

METAL = np.array([(22, 24, 36), (46, 52, 72), (70, 78, 104), (112, 122, 154), (170, 182, 214)], np.float32)
OR = np.array([(130, 90, 30), (176, 128, 44), (220, 170, 60), (255, 230, 140)], np.float32)
CRIS = np.array([(40, 40, 120), (70, 90, 200), (130, 160, 255), (190, 208, 255), (232, 240, 255)], np.float32)
CUIVRE = np.array((196, 118, 64), np.float32)
VIOLET = np.array((112, 88, 172), np.float32)
FIL_C = np.array((236, 244, 255), np.float32)
FIL_E = np.array((110, 150, 235), np.float32)
LAQUE = np.array([(14, 18, 42), (30, 38, 84), (52, 64, 128)], np.float32)


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
Z_E = 0.12                        # demi-épaisseur au fil
DF_B, DF_P, DF_G = 12.0, 9.0, 12.0   # texels par px : biseaux, plats, gouttières (l'écu est grand : l'atlas 512 doit suffire)
TH = 0.3
RECOUV = 0.08
Z_FOND = 0.16
T_BIS = 0.85                      # pente unique des biseaux (40°)


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
    """Plaque biseautée : contour `poly`, fils `fils` (polylignes biseautées), profil h(a) linéaire, wb(a), z au bord."""

    def __init__(self, nom, poly, fils, h, wb, ze, gouts=()):
        self.nom, self.poly, self.h, self.wb, self.ze = nom, poly, h, wb, ze
        self.segs = [s for f in fils for s in subdiv(f)]
        self.gouts = list(gouts)
        pa = np.array(poly)
        self.box = (pa[:, 0].min() - 0.05, pa[:, 0].max() + 0.05, pa[:, 1].min() - 0.05, pa[:, 1].max() + 0.05)

    def dE(self, P):
        return d_stack(P, self.segs).min(0)

    def surf(self, P):
        d, h, wb = self.dE(P), self.h(P[..., 0]), self.wb(P[..., 0])
        return np.where(d < wb, self.ze + (h - self.ze) * np.clip(d / wb, 0, 1), h)


SPECS = {}
TILES = {}


def repere(X, Y):
    X = unit(X)
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    return X, Y, np.cross(X, Y)


def points_face(c, X, Y, Z, s, face, dens):
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


def spec(cle, nom, c, X, Y, s, peintures, dens):
    X, Y, Z = repere(X, Y)
    faces = {}
    for f, fn in peintures.items():
        col, em, m = fn(points_face(np.asarray(c, float), X, Y, Z, s, f, dens))
        if m.any():
            TILES[f"{nom}_{f}"] = finir(col, em, m)
            faces[f] = f"{nom}_{f}"
    SPECS.setdefault(cle, []).append({"nom": nom, "c": np.asarray(c, float), "X": X, "Y": Y, "s": s, "faces": faces})


def volume(pc, cle):
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

            def haut(P, idx=idx, sg=sg):
                P2 = P[..., :2]
                D = d_stack(P2, pc.segs)
                dE = D.min(0)
                m = in_poly(P2, pc.poly) & (D[idx] <= dE + RECOUV) & (dE < pc.wb(P2[..., 0]) + 0.03)
                col, em = pc.peint_biseau(P2, dE, sg)
                return col, em, m

            def fil(P, idx=idx, n=n):
                P2 = P[..., :2] + n * 0.06
                D = d_stack(P2, pc.segs)
                m = in_poly(P2, pc.poly) & (D[idx] <= D.min(0) + RECOUV)
                col = np.zeros(P.shape[:-1] + (3,), np.float32) + FIL_C
                em = np.zeros_like(col) + FIL_E
                return col, em, m

            spec(cle, f"{pc.nom}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil}, DF_B)
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
            for G in pc.gouts:
                m &= ~G.dedans(P2)
            col, em = pc.peint_plat(P2, dE, sg)
            return col, em, m

        spec(cle, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, ((a1 - a0) * math.sqrt(1 + sl * sl), b1 - b0, TH), {"south": plat}, DF_P)


def gouttiere(pc, G, k, cle):
    """Fond (âme de 0,32 px, orienté le long de la gouttière) + parois verticales le long des deux bords, sur chaque face."""
    pa = np.array(G.poly)
    dd = unit(np.array(G.slit[-1], float) - np.array(G.slit[0], float))
    nn = np.array((-dd[1], dd[0]))
    pu, pv = pa @ dd, pa @ nn
    u0, u1, v0, v1 = pu.min() - 0.15, pu.max() + 0.15, pv.min() - 0.15, pv.max() + 0.15
    cc = dd * (u0 + u1) / 2 + nn * (v0 + v1) / 2
    nm = f"{pc.nom}_g{k}"

    def fond(P):
        P2 = P[..., :2]
        m = G.dedans(P2) | (G.dist(P2) < 0.1)
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + np.array((16, 18, 34), np.float32) + cellules(P2, 3.0, 5.0)[..., None] * 6
        em = np.zeros_like(col) + np.array((14, 22, 70), np.float32)
        return col, em, m

    spec(cle, f"{nm}_fond", (cc[0], cc[1], 0.0), (dd[0], dd[1], 0), (nn[0], nn[1], 0), (u1 - u0, v1 - v0, 2 * Z_FOND),
         {"south": fond, "north": fond}, DF_G)
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
            spec(cle, f"{nm}_paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi}, 16.0)


# ------------------------------------------------------------------ l'écu : deux ailes (repère de l'aile droite : u vers le bord, v vers le haut)
TILT = math.radians(14.0)          # carène : chaque aile tournée de 14° autour de la quille
ZH = 1.4                           # plan moyen des ailes à la quille (plaque vanilla : z 1 à 2)
Y_SH, Y_PT, W_MAX = 0.5, -12.0, 6.55


def arc_pt(s):
    """Bord bas de l'écu, du flanc (s = 0) à la pointe (s = 1)."""
    v = Y_SH - s * (Y_SH - Y_PT)
    u = W_MAX * max(0.0, 1 - s ** 1.7) ** 0.72
    return np.array((u, v))


def arc_nrm_in(s):
    e = 1e-3
    t = unit(arc_pt(min(1, s + e)) - arc_pt(max(0, s - e)))
    n = np.array((-t[1], t[0]))
    return n if n[0] < 0 else -n


TOP = [(0.0, 9.8), (1.6, 10.25), (3.4, 10.45), (5.0, 10.3), (5.9, 9.95)]
SPUR = [(6.45, 10.7), (6.98, 11.05), (6.8, 9.7)]
OUTER = [(6.62, 8.0), (6.56, 4.0), tuple(arc_pt(0.0))]
TEETH_S = (0.12, 0.29, 0.46, 0.62, 0.78)
TEETH, NOTCHES = [], []
for s_ in TEETH_S:
    tip = arc_pt(s_) - arc_nrm_in(s_) * 0.12
    notch = arc_pt(s_ + 0.022) + arc_nrm_in(s_ + 0.022) * 0.62
    TEETH += [tuple(tip), tuple(notch)]
    NOTCHES.append(notch)
POINTE = (0.0, Y_PT)
DEMI = TOP + SPUR + OUTER + TEETH + [POINTE]
FIL_AILE = [TOP[-1]] + SPUR + OUTER + TEETH + [POINTE]


def h_aile(a):
    return 0.95 - 0.055 * np.abs(np.asarray(a, float))


def wb_aile(a):
    return (h_aile(a) - Z_E) / T_BIS


# couvertures : trois écailles (plaque biseautée de 0,72 px posée sur l'aile, à moitié enfoncée)
H_COV, ZE_COV = 0.36, 0.1
COV_C, COV_R = (4.95, 3.15, 1.35), 0.9
COV = [(0.25, 9.72), (1.6, 10.13), (3.4, 10.33), (5.0, 10.18), (5.75, 9.86), (5.95, 8.6), (5.85, 8.0)]
for uc in COV_C:
    for k in range(1, 8):
        th = math.pi * k / 8
        COV.append((uc + COV_R * math.cos(th), 8.0 - COV_R * math.sin(th)))
    COV.append((uc - COV_R, 8.0))
COV.append((0.25, 8.0))
FIL_COV = COV[4:-1]


def h_cov(a):
    return np.zeros_like(np.asarray(a, float)) + H_COV


def wb_cov(a):
    return (h_cov(a) - ZE_COV) / T_BIS


# gouttières (aile droite) : elles partent du tambour vers les plumes
SLITS = [([(2.2, 4.8), (3.1, 5.6), (3.35, 5.2), (4.4, 6.1), (4.6, 5.72), (5.3, 6.3)], [0.07, 0.25, 0.27, 0.27, 0.23, 0.06]),
         ([(2.75, 2.05), (3.6, 1.2), (3.42, 0.78), (4.35, -0.3), (4.12, -0.7), (4.8, -1.85)], [0.07, 0.26, 0.28, 0.27, 0.23, 0.06]),
         ([(1.5, 0.2), (1.28, -1.6), (1.85, -2.3), (1.58, -4.2), (2.1, -4.9), (1.82, -6.5), (2.08, -7.1), (1.7, -7.95)],
          [0.07, 0.24, 0.26, 0.26, 0.25, 0.23, 0.2, 0.05])]

AILES = {}
for cote, sg_u in (("d", 1), ("g", -1)):
    mir = lambda pts, sg_u=sg_u: [(sg_u * a, b) for a, b in pts]
    poly = mir(DEMI)
    gouts = [Gouttiere(mir(sl), gw) for sl, gw in SLITS]
    aile = Piece(f"aile_{cote}", poly, [mir(FIL_AILE)], h_aile, wb_aile, Z_E, gouts)
    cov = Piece(f"cov_{cote}", mir(COV), [mir(FIL_COV)], h_cov, wb_cov, ZE_COV)
    aile.sg_u, cov.sg_u = sg_u, sg_u
    AILES[cote] = (aile, cov)

for cote, (aile, cov) in AILES.items():
    for i, G in enumerate(aile.gouts):
        pg = np.array(G.poly)
        m = (aile.dE(pg) - wb_aile(pg[:, 0])).min()
        dt = np.hypot(np.abs(pg[:, 0]) * math.cos(TILT), pg[:, 1] - 3.0).min()
        print(f"aile {cote} gouttière {i} : marge / biseaux {m:+.2f} px ; distance au tambour {dt:.2f} px")
        assert m > 0.06, "la gouttière mord les biseaux"
        assert dt > 2.62, "la gouttière passe sous le tambour"
        assert (np.abs(pg[:, 0]) > 0.75).all(), "la gouttière passe sous la quille"
        assert (pg[:, 1] < 7.0).all() or (np.abs(pg[:, 0]) > 6.0).all(), "la gouttière passe sous les couvertures"


# ------------------------------------------------------------------ peintures des faces
def feather_lines(Pm):
    """Gravures des primaires : une ligne depuis chaque encoche, vers le haut et la quille (Pm : coordonnées de l'aile droite)."""
    best = np.full(Pm.shape[:-1], 9.0)
    for nt in NOTCHES[:-1]:
        a = np.asarray(nt, float) + np.array((-0.05, 0.05))
        b = a + unit((-0.62, 1.0)) * 3.4
        best = np.minimum(best, d_poly(Pm, [a, b]))
    return best


def peint_biseau_aile(pc):
    def f(P, dE, sg):
        wb = pc.wb(P[..., 0])
        fr = dE / wb
        nz = cellules(P, 2.2, 1.0)[..., None]
        col = lerp(METAL[3], METAL[2], np.clip((fr[..., None] - 0.78) / 0.15, 0, 1)) + nz * 10
        col = np.where((fr < 0.36)[..., None], lerp(METAL[4], METAL[3], np.clip((fr[..., None] - 0.14) / 0.22, 0, 1)) + nz * 6, col)
        cu = (fr >= 0.36) & (fr < 0.57)
        vi = (fr >= 0.57) & (fr < 0.78)
        col[cu] = lerp(col[cu], CUIVRE, 0.85)
        col[vi] = lerp(col[vi], VIOLET, 0.72)
        col[(fr >= 0.86) & (fr < 0.93)] = OR[2]
        col[fr >= 0.93] = METAL[0]
        em = np.zeros(col.shape, np.float32)
        col[fr < 0.14] = FIL_C
        em[fr < 0.16] = FIL_E
        return col, em
    return f


def peint_plat_aile(pc):
    def f(P, dE, sg):
        wb = pc.wb(P[..., 0])
        Pm = np.stack([np.abs(P[..., 0]), P[..., 1]], -1)
        nz = cellules(Pm, 1.5, 2.0 + (sg < 0))[..., None]
        col = lerp(METAL[2], METAL[1], np.clip((dE[..., None] - wb[..., None] - 0.1) / 0.8, 0, 1) * 0.55) + nz * 14
        col = col + np.zeros(P.shape[:-1] + (3,), np.float32)
        em = np.zeros(col.shape, np.float32)
        topv = np.interp(Pm[..., 0], [p[0] for p in TOP], [p[1] for p in TOP])
        col = col * (1 - 0.35 * np.clip(1 - (topv - Pm[..., 1] - 1.0) / 0.6, 0, 1))[..., None]      # ombre sous le bourrelet
        col = col * (1 - 0.3 * np.clip(1 - (Pm[..., 0] - 0.55) / 0.5, 0, 1))[..., None]               # ombre de la quille
        if sg > 0:
            fl = feather_lines(Pm)
            col[fl < 0.05] = METAL[0]
            col[(fl >= 0.05) & (fl < 0.1)] = METAL[3]
        else:                                                    # dos : rayons du revers, plus sombre
            col = col * 0.85
        col[dE < wb + 0.04] = METAL[0]
        for G in pc.gouts:
            dg = G.dist(P)
            levre = dg < 0.06
            col[levre] = (190, 208, 255)
            em[levre] = (60, 100, 210)
            col[(dg >= 0.06) & (dg < 0.1)] = METAL[0]
            orl = (dg >= 0.15) & (dg < 0.23) & (dE > wb + 0.06)
            col[orl] = OR[2]
            col[orl & (dg < 0.185)] = OR[3]
        return col, em
    return f


def peint_biseau_cov(pc):
    def f(P, dE, sg):
        wb = pc.wb(P[..., 0])
        fr = dE / wb
        nz = cellules(P, 2.4, 3.0)[..., None]
        col = lerp(OR[3], OR[1], np.clip(fr[..., None], 0, 1)) + nz * 8
        col[(fr >= 0.45) & (fr < 0.75)] = lerp(col[(fr >= 0.45) & (fr < 0.75)], CUIVRE, 0.7)
        col[fr >= 0.9] = METAL[0]
        em = np.zeros(col.shape, np.float32)
        col[fr < 0.18] = FIL_C
        em[fr < 0.2] = FIL_E * 0.8
        return col, em
    return f


def peint_plat_cov(pc):
    def f(P, dE, sg):
        wb = pc.wb(P[..., 0])
        Pm = np.stack([np.abs(P[..., 0]), P[..., 1]], -1)
        nz = cellules(Pm, 2.0, 4.0)[..., None]
        col = lerp(METAL[3], METAL[2], np.clip((dE[..., None] - wb[..., None]) / 1.0, 0, 1)) + nz * 12
        col = col + np.zeros(P.shape[:-1] + (3,), np.float32)
        em = np.zeros(col.shape, np.float32)
        for uc in COV_C:                                         # rachis d'or de chaque écaille
            r = np.abs(Pm[..., 0] - uc)
            on = (r < 0.07) & (Pm[..., 1] > 7.5) & (Pm[..., 1] < 9.5)
            col[on] = OR[3]
            col[(r >= 0.07) & (r < 0.11) & (Pm[..., 1] > 7.5) & (Pm[..., 1] < 9.5)] = OR[1]
        col[dE < wb + 0.04] = METAL[0]
        return col, em
    return f


for aile, cov in AILES.values():
    aile.peint_biseau, aile.peint_plat = peint_biseau_aile(aile), peint_plat_aile(aile)
    cov.peint_biseau, cov.peint_plat = peint_biseau_cov(cov), peint_plat_cov(cov)


def conception():
    SPECS.clear()
    TILES.clear()
    for cote, (aile, cov) in AILES.items():
        volume(aile, aile.nom)
        for j, G in enumerate(aile.gouts):
            gouttiere(aile, G, j, aile.nom)
        volume(cov, cov.nom)


# ------------------------------------------------------------------ tuiles peintes
def g01(W, H):
    yy, xx = np.mgrid[0:H * SS, 0:W * SS]
    return (xx + 0.5) / (W * SS), (yy + 0.5) / (H * SS)


def red(col, W, H):
    im = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = im
    out[..., 3] = 255
    return out


def t_rebord(W=160, H=12):
    """Bourrelet : acier poli, arête claire au milieu de chaque pan, coups de marteau le long."""
    x, y = g01(W, H)
    q = np.abs(y - 0.5) * 2
    col = lerp(METAL[4], METAL[2], (q ** 1.2)[..., None]) + np.sin(x * 61.0 + np.floor(x * 23) * 1.7)[..., None] * 6
    col = np.where((q > 0.86)[..., None], METAL[1], col)
    return red(col, W, H)


def t_acier(W=64, H=12):
    x, y = g01(W, H)
    q = np.abs(y - 0.5) * 2
    col = lerp(METAL[3], METAL[1], (q ** 1.3)[..., None]) + np.sin(x * 40.0)[..., None] * 4
    return red(col, W, H)


def t_cap(c0, c1, N=12):
    x, y = g01(N, N)
    r = np.maximum(np.abs(x - 0.5), np.abs(y - 0.5)) * 2
    return red(lerp(np.array(c0, np.float32), np.array(c1, np.float32), r[..., None]), N, N)


def t_cuir(W=96, H=12):
    x, y = g01(W, H)
    q = np.abs(y - 0.5) * 2
    cuir = lerp(LAQUE[0], LAQUE[2], (1 - q ** 1.5)[..., None])
    band = np.mod(x * 10 + y * 0.9, 1) < 0.16
    col = np.where(band[..., None], cuir * 0.55, cuir)
    return red(col, W, H)


def t_or(W=24, H=12):
    x, y = g01(W, H)
    q = np.abs(y - 0.5) * 2
    return red(OR[np.clip((3.2 * (1 - q ** 1.4) + 0.6 * (q < 0.2)).astype(int), 0, 3)], W, H)


def t_or16(W=24, H=24, sens="u"):
    a = t_or(W, H) if sens == "v" else np.transpose(t_or(H, W), (1, 0, 2)).copy()
    k = math.tan(math.radians(11.25)) + 0.03
    t = np.abs((np.arange(W if sens == "u" else H) + 0.5) / (W if sens == "u" else H) * 2 - 1)
    hors = t > k
    if sens == "u":
        a[:, hors] = 0
    else:
        a[hors, :] = 0
    return a


def disque(N, dessin, ss=4):
    M = N * ss
    im = Image.new("RGBA", (M, M), (0, 0, 0, 0))
    dessin(ImageDraw.Draw(im), M)
    a = np.array(im.resize((N, N), Image.LANCZOS))
    a[..., 3] = (a[..., 3] > 128) * 255
    a[a[..., 3] == 0] = 0
    return a


def rgb(c):
    return tuple(int(v) for v in c) + (255,)


def medaillon(N=96):
    """Tambour d'or : anneau d'or, fond de métal sombre, trois virgules d'or en spirale (famille de l'épée)."""
    def dessin(d, M):
        d.ellipse((0, 0, M - 1, M - 1), fill=rgb(OR[1]))
        d.ellipse((M * 0.06, M * 0.06, M * 0.94, M * 0.94), fill=rgb(OR[3]))
        d.ellipse((M * 0.12, M * 0.12, M * 0.88, M * 0.88), fill=rgb(METAL[1]))
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
                d.ellipse((x - w, y - w, x + w, y + w), fill=rgb(OR[2]))
            d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=rgb(OR[3]))
    return disque(N, dessin)


def peau(N=96, r_in=0.72):
    """Peau du tambour (gradin bas) : laque bleu nuit, cercle de clous d'or, anneau d'or au bord."""
    def dessin(d, M):
        d.ellipse((0, 0, M - 1, M - 1), fill=rgb(OR[1]))
        d.ellipse((M * 0.04, M * 0.04, M * 0.96, M * 0.96), fill=rgb(OR[2]))
        d.ellipse((M * 0.08, M * 0.08, M * 0.92, M * 0.92), fill=rgb(LAQUE[1]))
        d.ellipse((M * 0.14, M * 0.14, M * 0.86, M * 0.86), fill=rgb(LAQUE[0]))
        c = M / 2
        for k in range(12):
            th = TAU * k / 12 + 0.13
            rr = M * (0.5 * (0.92 + r_in) / 2 + 0.005)
            x, y = c + rr * math.cos(th), c + rr * math.sin(th)
            w = M * 0.03
            d.ellipse((x - w, y - w, x + w, y + w), fill=rgb(OR[3]))
            d.ellipse((x - w * 0.4, y - w * 0.4 - w * 0.3, x + w * 0.4, y + w * 0.4 - w * 0.3), fill=(255, 245, 200, 255))
    return disque(N, dessin)


def t_core(vif):
    a = np.zeros((6, 16, 4), np.uint8)
    a[..., :3] = (236, 244, 255) if vif else (92, 108, 158)
    a[0, :, :3] = a[5, :, :3] = (96, 146, 255) if vif else (40, 56, 120)
    a[..., 3] = 255
    e = a.copy()
    e[..., :3] = (205, 226, 255) if vif else (44, 60, 120)
    e[0, :, :3] = e[5, :, :3] = (50, 84, 210) if vif else (24, 40, 120)
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
    e = a.copy()
    e[..., :3] = (200, 220, 255)
    return a, e


def t_cristal():
    rng = np.random.default_rng(4)
    a = np.zeros((8, 16, 4), np.uint8)
    v = np.linspace(0, 1, 8)[:, None] * np.ones((1, 16))
    col = lerp(CRIS[3], CRIS[1], v[..., None]) + rng.normal(0, 4, (8, 16, 1))
    col[0] = col[-1] = CRIS[0]
    a[..., :3] = np.clip(col, 0, 255)
    a[..., 3] = 255
    e = a.copy()
    e[..., :3] = np.clip(a[..., :3].astype(np.float32) * 0.7, 0, 225).astype(np.uint8)
    return a, e


UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    cv, cv_e = t_core(True)
    cd, cd_e = t_core(False)
    crk, crk_e = t_crk()
    cri, cri_e = t_cristal()
    conception()
    items = [(n, im, ime) for n, (im, ime) in TILES.items()]
    items += [("rebord", t_rebord(), None), ("acier", t_acier(), None), ("cuir", t_cuir(), None), ("or", t_or(), None),
              ("or16u", t_or16(48, 12, "u"), None), ("or16v", t_or16(12, 48, "v"), None), ("medaillon", medaillon(), None),
              ("peau", peau(), None), ("cap_acier", t_cap(METAL[3], METAL[1]), None), ("cap_cuir", t_cap(LAQUE[2], LAQUE[0]), None),
              ("core_vif", cv, cv_e), ("core_dim", cd, cd_e), ("crk", crk, crk_e), ("cristal", cri, cri_e)]
    items += [(f"halo{k}", t_halo(m), None) for k, m in enumerate((0.8, 1.4, 1.9))]
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

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


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
    X = unit(X)
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    cube(g, name, c - (sx / 2, sy / 2, sz / 2), c + (sx / 2, sy / 2, sz / 2), c, euler(R_), faces)


def uvp(tile, flip=False):
    u0, v0, u1, v1 = UV[tile]
    return [u1, v0, u0, v1] if flip else [u0, v0, u1, v1]


def frame_of(X, ref):
    X = unit(X)
    ref = np.asarray(ref, float)
    if abs(ref @ X) > 0.95:
        ref = np.array((0.0, 0.0, 1.0)) if abs(X[2]) < 0.9 else np.array((1.0, 0.0, 0.0))
    Y = unit(ref - (ref @ X) * X)
    return X, Y, np.cross(X, Y)


def bar8(g, name, p, q, r, tile, cap, ref=(0, 0, 1), ov=0.03):
    """Barre octogonale (4 plaques à 0, 45, 90, 135°) de p à q ; bouts décalés de 0,03 px par plaque."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X, Y, Z = frame_of(q - p, ref)
    a_ = r * math.tan(math.pi / 8) * 1.02
    lg = uvp(tile)
    cu0, cv0, cu1, cv1 = UV[cap]
    fk = {"south": lg, "north": lg, "up": lg, "down": lg, "east": [cu0, cv0, cu1, cv1], "west": [cu0, cv0, cu1, cv1]}
    for k in range(4):
        gk = math.pi / 4 * k
        Yk = math.cos(gk) * Y + math.sin(gk) * Z
        Rk = np.column_stack([X, Yk, np.cross(X, Yk)])
        d = 0.03 * k
        cube(g, name + ("", "b", "c", "d")[k], p + (-ov + d, -r, -a_), p + (L + ov - d, r, a_), p, euler(Rk), fk)


def prisme(g, name, p, d, r, L, ref=(0, 0, 1)):
    """Cristal : corps octogonal, pointe en biseau (deux cubes tournés de 45°)."""
    p = np.asarray(p, float)
    X, Y, Z = frame_of(d, ref)
    Lb = L - r
    E = p + X * Lb
    c45 = math.cos(math.pi / 4)
    for k, (Yk, s_) in enumerate(((Y, 1.0), (c45 * Y + c45 * Z, 0.97))):
        Rk = np.column_stack([X, Yk, np.cross(X, Yk)])
        cube(g, name + ("", "o")[k], p + np.array((-0.04 + 0.1 * k, -r * s_, -r * s_)), p + np.array((Lb + 0.04 - 0.1 * k, r * s_, r * s_)),
             p, euler(Rk), {f: uvp("cristal") for f in ("north", "south", "east", "west", "up", "down")})
    rp, h = r - 0.11, r / math.sqrt(2)
    allf = {f: uvp("cristal") for f in ("north", "south", "east", "west", "up", "down")}
    boite(g, name + "pa", E, (X + Z) * c45, Y, 2 * h, 2 * rp, 2 * h, allf)
    boite(g, name + "pb", E, (X + Y) * c45, (-X + Y) * c45, 2 * h, 2 * h, 2 * rp, allf)


def seg(g, name, p, q, w, tile, ov=0.06, roll=45.0, ref=(0, 0, 1)):
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = np.asarray(ref, float)
    if abs(ref @ X) > 0.9:
        ref = np.array((1.0, 0, 0))
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


def trait(g, name, pts, w0, w1, tile, ref=(0, 0, 1)):
    n = len(pts) - 1
    for i in range(n):
        roll = ROLLS[_rc[0] % len(ROLLS)]
        _rc[0] += 1
        seg(g, f"{name}{i}", pts[i], pts[i + 1], w0 + (w1 - w0) * i / max(1, n - 1), tile, roll=roll, ref=ref)


def zigzag(pts, n, J, seed):
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
        out.append((q[0], q[1]))
    return out


def eclair3d(p, q, n, J, seed, bombe=None):
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


# repères des ailes : monde = T + M @ (a, b, z)
CT, ST = math.cos(TILT), math.sin(TILT)
FR = {"d": (np.array((0.0, 0.0, ZH)), np.column_stack([(CT, 0, -ST), (0, 1, 0), (ST, 0, CT)])),
      "g": (np.array((0.0, 0.0, ZH)), np.column_stack([(CT, 0, ST), (0, 1, 0), (-ST, 0, CT)]))}
for _c, (_T, _M) in FR.items():
    assert np.allclose(np.cross(_M[:, 0], _M[:, 1]), _M[:, 2])


def fr_cov(cote):
    """Repère des couvertures dans celui de l'aile : tourné de la pente du plat, posé dessus (à moitié enfoncé)."""
    T, M = FR[cote]
    sgu = AILES[cote][0].sg_u
    ph = math.atan(-0.055 * sgu)
    Mc = np.column_stack([(math.cos(ph), 0, math.sin(ph)), (0, 1, 0), (-math.sin(ph), 0, math.cos(ph))])
    return T + M @ np.array((0, 0, float(h_aile(0.0)) + 0.03)), M @ Mc


def Wa(cote, a, b, z=0.0):
    T, M = FR[cote]
    return T + M @ np.array((a, b, z), float)


def poser(cle, g, prefixe, T, M):
    for sp in SPECS[cle]:
        u_ = {f: (list(UV[sp["faces"][f]]) if f in sp["faces"] else CLEAR) for f in ("north", "south", "east", "west", "up", "down")}
        boite(g, prefixe + sp["nom"], T + M @ sp["c"], M @ sp["X"], M @ sp["Y"], *sp["s"], u_)


DRUM = np.array((0.0, 3.0))
R1, R2 = 2.55, 1.9
Z_D0, Z_D1, Z_D2 = 1.3, 3.0, 3.7
Z_QUILLE, R_QUILLE = ZH + 0.86, 0.62
Z_DOS = ZH - 0.95
Y_CRIS = 10.3


def tambour(g, sfx, R, z0, z1, face_tile):
    for k in range(4):
        th = math.radians(22.5 * k)
        boite(g, f"tambour{sfx}{k}", (DRUM[0], DRUM[1], (z0 + z1) / 2), (math.cos(th), math.sin(th), 0), (-math.sin(th), math.cos(th), 0),
              2 * R, 2 * R, z1 - z0 - 0.02, {"north": CLEAR, "south": CLEAR, "east": uvp("or16v"), "west": uvp("or16v"),
                                             "up": uvp("or16u"), "down": uvp("or16u")})
    MR = R / math.cos(math.radians(11.25)) + 0.01
    boite(g, f"face{sfx}", (DRUM[0], DRUM[1], z1 - 0.15), (1, 0, 0), (0, 1, 0), 2 * MR, 2 * MR, 0.3,
          {**{f: CLEAR for f in ("north", "south", "east", "west", "up", "down")}, "south": uvp(face_tile)})


def build_ecu(sfx, parent, vif):
    """Une copie de l'écu (mêmes tuiles) ; vif : foudre allumée (étape bloque)."""
    G = {"gaines": [], "arcs": []}
    for cote in ("d", "g"):
        aile, cov = AILES[cote]
        T, M = FR[cote]
        ga = group(f"aile_{cote}_{sfx}", Wa(cote, 3.0, 0.0), parent)
        poser(aile.nom, ga, f"{sfx}_", T, M)
        Tc, Mc = fr_cov(cote)
        poser(cov.nom, ga, f"{sfx}_", Tc, Mc)
        # bourrelet du bord haut (bord d'attaque de l'aile), bagues d'or
        for i in range(len(TOP) - 1):
            p = Wa(cote, aile.sg_u * TOP[i][0], TOP[i][1] + 0.02, 0.2)
            q = Wa(cote, aile.sg_u * TOP[i + 1][0], TOP[i + 1][1] + 0.02, 0.2)
            bar8(ga, f"{sfx}_rebord_{cote}{i}", p, q, 1.18, "rebord", "cap_acier", ref=M[:, 2], ov=0.08)
        for j, (u_, v_) in enumerate(((3.4, 10.47), (5.9, 9.97))):
            dv = unit(np.array(TOP[min(j + 3, len(TOP) - 1)]) - np.array(TOP[min(j + 2, len(TOP) - 2)]))
            c = np.array((u_, v_))
            p = Wa(cote, aile.sg_u * (c - dv * 0.2)[0], (c - dv * 0.2)[1], 0.2)
            q = Wa(cote, aile.sg_u * (c + dv * 0.2)[0], (c + dv * 0.2)[1], 0.2)
            bar8(ga, f"{sfx}_bague_{cote}{j}", p, q, 1.3, "or", "or", ref=M[:, 2])
        # foudre couchée au fond des gouttières (des deux côtés), gaine add_
        fo = group(f"foudre_{cote}_{sfx}", Wa(cote, aile.sg_u * 3.0, 1.0), ga)
        for j, Gt in enumerate(aile.gouts):
            pts2 = zigzag(Gt.slit, max(4, int(round(len(Gt.slit) * 1.5))), 0.05, 17 + 5 * j + (cote == "g") * 3)
            for zs in (1, -1):
                trait(fo, f"{sfx}_eclair_{cote}{j}{'pm'[zs < 0]}", [Wa(cote, x, y, zs * 0.17) for x, y in pts2],
                      0.3, 0.22, "core_vif" if vif else "core_dim", ref=M[:, 2])
            gg = group(f"add_gaine_{sfx}_{cote}{j}", Wa(cote, *pts2[0]), fo)
            ctrl(gg)
            for i in range(len(pts2) - 1):
                am = (pts2[i][0] + pts2[i + 1][0]) / 2
                seg(gg, f"gaine{i}", Wa(cote, *pts2[i]), Wa(cote, *pts2[i + 1]), min(0.8, 2 * float(h_aile(am)) - 0.2),
                    "halo2" if vif else "halo0", ov=0.04, roll=0.0, ref=M[:, 2])
            G["gaines"].append((gg, j, cote))
    # quille devant et derrière, tambour, cimier de cristal, talon
    gq = group(f"quille_{sfx}", (0, 0, Z_QUILLE), parent)
    bar8(gq, f"{sfx}_quille_bas", (0, -11.75, Z_QUILLE - 0.05), (0, DRUM[1] - 2.2, Z_QUILLE), R_QUILLE, "rebord", "cap_acier", ref=(1, 0, 0))
    bar8(gq, f"{sfx}_quille_haut", (0, DRUM[1] + 2.2, Z_QUILLE), (0, 9.7, Z_QUILLE - 0.02), R_QUILLE, "rebord", "cap_acier", ref=(1, 0, 0))
    bar8(gq, f"{sfx}_quille_dos", (0, -11.3, Z_DOS), (0, 9.6, Z_DOS), 0.5, "acier", "cap_acier", ref=(1, 0, 0))
    bar8(gq, f"{sfx}_collet", (0, 9.25, ZH + 0.15), (0, 10.4, ZH + 0.15), 1.05, "or", "or", ref=(1, 0, 0))
    prisme(gq, f"{sfx}_cimier", (0, Y_CRIS, ZH + 0.15), (0, 1, 0), 0.52, 2.0)
    bar8(gq, f"{sfx}_talon", (0, -12.4, ZH + 0.1), (0, -11.45, ZH + 0.1), 0.78, "or", "or", ref=(1, 0, 0))
    prisme(gq, f"{sfx}_talon_cri", (0, -12.3, ZH + 0.1), (0, -1, 0), 0.42, 1.2)
    for k, yb in enumerate((-6.0, 7.6)):
        bar8(gq, f"{sfx}_bague_q{k}", (0, yb - 0.22, Z_QUILLE), (0, yb + 0.22, Z_QUILLE), 0.76, "or", "or", ref=(1, 0, 0))
    gt = group(f"tambour_{sfx}", (DRUM[0], DRUM[1], 2.4), parent)
    tambour(gt, f"{sfx}_1", R1, Z_D0, Z_D1, "peau")
    tambour(gt, f"{sfx}_2", R2, Z_D1 - 0.1, Z_D2, "medaillon")
    # dos : traverses, montants, poignée de cuir entre bagues d'or
    gd = group(f"dos_{sfx}", (0, 0, -2), parent)
    for cote in ("d", "g"):
        aile = AILES[cote][0]
        T, M = FR[cote]
        for k, (vb, ue) in enumerate(((6.9, 5.4), (-3.6, 5.2))):
            p = Wa(cote, aile.sg_u * 0.35, vb, -(float(h_aile(0.35)) + 0.22))
            q = Wa(cote, aile.sg_u * ue, vb, -(float(h_aile(ue)) + 0.22))
            bar8(gd, f"{sfx}_traverse_{cote}{k}", p, q, 0.36, "acier", "or", ref=-M[:, 2])
    for k, yp in enumerate((3.15, -3.15)):
        bar8(gd, f"{sfx}_montant{k}", (0, yp, Z_DOS - 0.3), (0, yp, -4.75), 0.42, "acier", "or", ref=(1, 0, 0))
    bar8(gd, f"{sfx}_poignee", (0, -3.0, -4.2), (0, 3.0, -4.2), 0.58, "cuir", "cap_cuir", ref=(0, 0, 1))
    for k, yp in enumerate((-2.85, 2.85)):
        bar8(gd, f"{sfx}_bague_p{k}", (0, yp - 0.18, -4.2), (0, yp + 0.18, -4.2), 0.68, "or", "or", ref=(0, 0, 1))
    return G


CRIS_TIP = np.array((0.0, Y_CRIS + 2.0, ZH + 0.15))
SPUR_TIP = {c: Wa(c, AILES[c][0].sg_u * SPUR[1][0], SPUR[1][1], 0.0) for c in ("d", "g")}

racine_c = group("bouclier_orage", (0, 0, 0))
group("calcul_parade", (0, 0, 0), racine_c)
racine_r = group(objet.etape("repos", "bouclier"), (0, 0, 0))
GR = build_ecu("r", racine_r, False)
racine_b = group(objet.etape("bloque", "bouclier"), (0, 0, 0))
pose = group("pose_bloque", (0, 0, 0), racine_b)
GB = build_ecu("b", pose, True)

# bloque : arcs du cimier aux deux poignets (au-dessus du bourrelet)
for j, c in enumerate(("d", "g")):
    p, q = CRIS_TIP + np.array((0, -0.9, 0.1)), SPUR_TIP[c] + np.array((0, 0.15, 0.1))
    g = group(f"add_arc_cimier{j}", (p + q) / 2, pose)
    ctrl(g)
    pts = eclair3d(p, q, 7, 0.22, 41 + 9 * j, bombe=(0, 0.7, 0.5))
    trait(g, "a", pts, 0.2, 0.14, "crk")
    for i in range(len(pts) - 1):
        seg(g, f"h{i}", pts[i], pts[i + 1], 0.5, "halo2", ov=0.03, roll=0.0)
    GB["arcs"].append(g)
# bloque : décharge en retour (repliée dans le tambour), deux formes
PIV_T = np.array((DRUM[0], DRUM[1], 2.2))
FACE_T = np.array((DRUM[0], DRUM[1], Z_D2 + 0.05))
DECH = []
for nm_f, seed in (("a", 31), ("b", 47)):
    g = group(f"add_decharge_{nm_f}", PIV_T, pose)
    ctrl(g)
    rng = random.Random(seed)
    for k in range(4):
        ang = TAU * (k + 0.5 + rng.uniform(-0.18, 0.18)) / 4 + (0.4 if nm_f == "b" else 0.0)
        dv = unit(np.array((0.7 * math.cos(ang), 0.7 * math.sin(ang), 1.0)))
        p0 = FACE_T + np.array((math.cos(ang), math.sin(ang), 0)) * 0.9
        pts = eclair3d(p0, p0 + dv * rng.uniform(5.0, 6.5), 6, 0.35, seed + 7 * k)
        trait(g, f"t{k}_", pts, 0.3, 0.14, "crk")
        for kk in (2, 4):
            dd = unit(dv + np.array((rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), 0.2)))
            trait(g, f"f{k}{kk}_", eclair3d(pts[kk], pts[kk] + dd * 1.6, 3, 0.15, seed + 13 * k + kk), 0.16, 0.1, "crk")
    replier(g)
    DECH.append(g)
EMIT = group("emit_mc_electric_spark", FACE_T, pose)
group("ctrl_emit", FACE_T, EMIT)

# event_select : la foudre frappe la pointe du cimier (repliée dans le collet), deux formes
PIV_C = np.array((0.0, 9.8, ZH + 0.15))
SEL = []
for nm_f, seed, dv in (("a", 5, (0.35, 1, 0.3)), ("b", 9, (-0.3, 1, -0.2))):
    g = group(f"add_sel_frappe_{nm_f}", PIV_C, racine_c)
    ctrl(g)
    pts = eclair3d(CRIS_TIP + unit(dv) * 6.0, CRIS_TIP + np.array((0, 0.05, 0)), 7, 0.4, seed)
    trait(g, "f", pts, 0.3, 0.16, "crk")
    for kk in (2, 4):
        trait(g, f"fk{kk}_", eclair3d(pts[kk], pts[kk] + unit((dv[0] * 2 + 0.5 * (kk - 3), 0.4, 0.3)) * 1.5, 3, 0.15, seed + kk),
              0.16, 0.1, "crk")
    replier(g)
    SEL.append(g)


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


outliner = [bone_node(racine_c), bone_node(racine_r), bone_node(racine_b)]

# ------------------------------------------------------------------ réglages Display (item/shield.json et item/shield_blocking.json du jar 26.1.2)
VAN = {"thirdperson_righthand": ((0, 90, 0), (10, 6, -4), 1), "thirdperson_lefthand": ((0, 90, 0), (10, 6, 12), 1),
       "firstperson_righthand": ((0, 180, 5), (-10, 1.75, -10), 1.25), "firstperson_lefthand": ((0, 180, 5), (10, 0, -10), 1.25),
       "gui": ((15, -25, -5), (2, 3, 0), 0.65), "fixed": ((0, 180, 0), (-4.5, 4.5, -5), 0.55), "on_shelf": ((0, 0, 0), (11, 18.5, 8.7), 1.4),
       "ground": ((0, 0, 0), (2, 4, 2), 0.25)}
VAN_BLOQUE = {"thirdperson_righthand": ((45, 155, 0), (-3.49, 11, -2), 1), "thirdperson_lefthand": ((45, 155, 0), (11.51, 7, 2.5), 1),
              "firstperson_righthand": ((0, 180, -5), (-15, 3.25, -11), 1.25), "firstperson_lefthand": ((0, 180, -5), (5, 5, -11), 1.25)}
AFFICHAGE = objet.affichage("bouclier", **{c: {"rotation": list(r), "translation": list(t), "scale": [s] * 3} for c, (r, t, s) in VAN.items()})


def disp(v, gauche):
    """Display appliqué comme ItemTransform.apply : main gauche = rotation Y, Z et translation X inversées."""
    r, t, s = v
    r, t = list(r), list(t)
    if gauche:
        r[1], r[2], t[0] = -r[1], -r[2], -t[0]
    return objet.matrice_display({"rotation": r, "translation": t, "scale": [s] * 3})


CORR = {}
for c in VAN_BLOQUE:
    gauche = c.endswith("lefthand")
    Hm = np.linalg.inv(disp(VAN[c], gauche)) @ disp(VAN_BLOQUE[c], gauche)
    Rm = Hm[:3, :3]
    assert np.allclose(Rm @ Rm.T, np.eye(3), atol=1e-6)
    CORR[c] = (euler(Rm), Hm[:3, 3])
    e, t = CORR[c]
    for p in ((0, 0, 1.5), (6, 10, 2), (-6, -11, 1), (0, 3, -5)):
        a = disp(VAN[c], gauche) @ np.append(rotm(*e) @ np.array(p, float) + t, 1)
        b = disp(VAN_BLOQUE[c], gauche) @ np.append(np.array(p, float), 1)
        assert np.allclose(a, b, atol=1e-6), c
    print(f"parade {c:23s} rotation {np.round(e, 2).tolist()} position {np.round(t, 3).tolist()}")


def molang_combo(i, chan):
    v = {c: (CORR[c][0][i] if chan == "rot" else CORR[c][1][i]) for c in CORR}
    f = lambda x: f"({x:.3f})"
    return (f"q.in_first_person*(q.hand*{f(v['firstperson_lefthand'])}+(1-q.hand)*{f(v['firstperson_righthand'])})"
            f"+(1-q.in_first_person)*(q.hand*{f(v['thirdperson_lefthand'])}+(1-q.hand)*{f(v['thirdperson_righthand'])})")


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
    u = groups[g]["uuid"]
    if u in an["animators"]:
        an["animators"][u]["keyframes"] += keys
    else:
        an["animators"][u] = {"name": g.split("#")[0], "type": "bone", "keyframes": keys}


def chk(e):
    assert len(e) <= 512 and e.count(";") <= 16, (len(e), e)
    return e


def H(x):
    return f"math.mod(math.abs(math.sin(({x})*127.1))*437.585,1)"


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


# coup bloqué : q.hit_by_entity, ou hausse de l'usure (un coup bloqué use le bouclier) ; une seule clé met à jour v.bp / v.bt
CALC = "v.bd=q.item_durability;v.bt=v.bt+(q.life_time-v.bt)*(v.bd>v.bp+0.00001)*v.bi;v.bp=v.bd;v.bi=1;0"
BK = "math.max(q.hit_by_entity,(q.life_time-v.bt<0.45)*(v.bt>0))"
DEPLIE = 1 / FOLD


def deplier(an, g):
    piste(an, g, [kf("scale", 0.0, DEPLIE, DEPLIE, DEPLIE, "step")])


def rang(j, cote):
    return j + (0.5 if cote == "g" else 0.0)


# item_idle (8 s) : la foudre dort, une gouttière se ravive de temps en temps
idle = anim("item_idle", 8.0)
rot_m = [molang_combo(i, "rot") for i in range(3)]
pos_m = [molang_combo(i, "pos") for i in range(3)]
for e_ in rot_m + pos_m:
    chk(e_)
# Correctif F6 : la garde vit aussi dans item_idle (pose_bloque n'est dessiné qu'à l'étape bloque) ; si le mod voit « plus
# utilisé » une image, item_idle reprend sans fondu ni retombée (objets.md, « Retour en jeu 2026-11-08 soir », recette 2).
piste(idle, pose, [kf("rotation", 0, *rot_m), kf("rotation", 8.0, *rot_m), kf("position", 0, *pos_m), kf("position", 8.0, *pos_m)])
piste(idle, "calcul_parade", [kf("position", 0, chk(CALC))])
for k, (g, j, cote) in enumerate(GR["gaines"]):
    piste_ctrl(idle, g, [kf("position", 0, chk(flick(7, 0.13 + 0.31 * k) + f"v.r={H(f'math.floor(q.life_time/3.1+{0.17 * k:.2f})')};"
                                               + "-0.62+0.22*(v.h<0.3)-0.2*(v.h>0.85)+0.55*(v.r>0.86)"))])
for g in SEL:
    piste_ctrl(idle, g, [kf("position", 0, -1)])

# item_gui : calme
gui = anim("item_gui", 4.0)
for g, j, cote in GR["gaines"]:
    piste_ctrl(gui, g, [kf("position", 0, -0.45)])
for g in SEL:
    piste_ctrl(gui, g, [kf("position", 0, -1)])

# item_use : pose de blocage, gouttières allumées, arcs du cimier, décharge en retour sur un coup bloqué
use = anim("item_use", 1.0)
piste(use, pose, [kf("rotation", 0, *rot_m), kf("rotation", 1.0, *rot_m), kf("position", 0, *pos_m), kf("position", 1.0, *pos_m)])
piste(use, "calcul_parade", [kf("position", 0, chk(CALC))])
for k, (g, j, cote) in enumerate(GB["gaines"]):
    piste_ctrl(use, g, [kf("position", 0, chk(flick(10, 0.07 + 0.29 * k) + f"-0.12-0.35*(v.h<0.16)+0.12*{BK}"))])
for i, g in enumerate(GB["arcs"]):
    piste_ctrl(use, g, [kf("position", 0, chk(flick(9 + 4 * i, 0.21 + 0.4 * i) + f"v.r={H(f'math.floor(q.life_time/1.7+{0.37 + 0.5 * i:.2f})')};"
                                               + f"-1+(v.r>0.55)*(v.h>0.35)+{BK}*(v.h>0.2)"))])
for i, g in enumerate(DECH):
    piste(use, g, [kf("scale", 0, *([chk(f"1+9*{BK}")] * 3))])
    piste_ctrl(use, g, [kf("position", 0, chk(flick(14, 0.5) + f"-1+{BK}*({'v.h<0.5' if i == 0 else 'v.h>=0.5'})"))])
piste(use, "ctrl_emit", [kf("position", 0, chk(f"-1+8*{BK}"))])
for g in SEL:
    piste_ctrl(use, g, [kf("position", 0, -1)])

# event_use_start (0,5 s) : la foudre s'allume gouttière après gouttière, du tambour vers le bord ; arcs du cimier ; sans son (F6)
L_US = 0.5
us = anim("event_use_start", L_US, "once")
TS = np.round(np.linspace(0, L_US, 26), 4)
for g, j, cote in GB["gaines"]:
    t0 = 0.02 + 0.07 * rang(j, cote)
    piste_ctrl(us, g, [kf("position", t, -1 + sm(t, t0, t0 + 0.04) + 0.25 * bump(t, t0 + 0.02, t0 + 0.05, t0 + 0.09, t0 + 0.2)) for t in TS])
for i, g in enumerate(GB["arcs"]):
    piste_ctrl(us, g, onoff([(0.2 + 0.04 * i, 0.27 + 0.04 * i), (0.33, 0.36)], L_US, on=1.0, off=0.0))

# event_select (0,7 s) : la foudre frappe la pointe du cimier, puis les gouttières s'allument une à une
L_SEL = 0.7
sel = anim("event_select", L_SEL, "once")
for g in SEL:
    deplier(sel, g)
piste_ctrl(sel, SEL[0], onoff([(0.0, 0.07), (0.15, 0.19)], L_SEL))
piste_ctrl(sel, SEL[1], onoff([(0.08, 0.13)], L_SEL))
for g, j, cote in GR["gaines"]:
    t0 = 0.16 + 0.06 * rang(j, cote)
    piste_ctrl(sel, g, [kf("position", t, 1.0 * bump(t, t0, t0 + 0.04, t0 + 0.12, t0 + 0.4)) for t in np.round(np.linspace(0, L_SEL, 29), 4)])

ANIMS = [idle, gui, use, us, sel]

# ------------------------------------------------------------------ écriture
assert 300 <= len(elements) <= 3000, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = objet.modele(NOM, "bouclier", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons
limiter_sons(model)
# Correctif F6 : aucun son (recette 3) ; event_use_start est rejoué à chaque coupure de l'utilisation (son répété en jeu)
# et le jeu joue déjà item.shield.block au coup paré. Son embarqué charge_bouclier retiré (rangé dans .build/sons_retires).
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


_P = coins()
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print("boîte :", _P.min(0).round(2).tolist(), "->", _P.max(0).round(2).tolist())
