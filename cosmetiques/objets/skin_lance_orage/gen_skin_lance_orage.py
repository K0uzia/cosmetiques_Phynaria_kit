"""Lance de la tempête : skin d'objet (guide 14) pour toutes les lances du joueur, ensemble Orage (thème Éléments). Design original.
Écrit skin_lance_orage.png, skin_lance_orage_e.png et .build/skin_lance_orage_brut.bbmodel à côté de ce script.

Même design que la version validée en jeu le 2026-11-05 (prise en main, étapes levée/lancée, lueur de nuit) : hampe de métal
d'orage octogonale à bagues d'or, gaine de cuir bleu nuit, talon d'or et pointe de cristal, anneau de tambour aux trois
virgules d'or, fer de cristal d'orage en feuille à deux crans d'éclair par bord, croisé d'ailettes ; étapes `repos` (sobre),
`leve` (cristal plus clair, arêtes allumées, éclat à la pointe), `lance` (presque blanc, chargé, éclairs le long du fer et de
la hampe). Toujours sans animation (les étapes portent tout ; réglages Display validés, inchangés).

Vrai volume (retour en jeu du 2026-11-08 14 h 22 : « c'est des couches » ; recette .claude/references/objets/volume-3d.md,
reprise de skin_epee_orage) :
- fer = plaque biseautée fermée à section hexagonale (losange vers la pointe, où le plat disparaît) : un cube de biseau
  incliné à pente unique de 40° par tronçon de fil (≤ 2 px) et par face, un plat incliné par face qui suit l'amincissement
  (1,24 px à la douille -> 0,50 à la pointe) ; crans d'éclair à sommets vifs ; fil, poli et cristal peints sur les faces ;
- gouttière creusée en zigzag au milieu du fer (parois, fond de 0,32 px), foudre couchée au fond (cœur opaque + _e, gaine add_)
  : elle remplace le filet d'éclair peint ;
- ailettes = deux plaques biseautées perpendiculaires au fer (même recette, 0,68 px), nées de la douille, à crans d'éclair :
  elles reprennent la feuille croisée d'avant, qui se lisait comme une pile de plaques transparentes ;
- douille = tronc de cône à 8 pans (plaques inclinées découpées par l'alpha), collet et lèvre d'or ; tambour à 16 pans aux
  médaillons à virgules (famille de l'épée) ; pointe du talon = cristal octogonal en trois tronçons (pommeau de l'épée) ;
- éclat (leve) et éclairs (lance) = traits de foudre en géométrie (cœur blanc dans add_, gaine add_), comme les arcs des autres
  objets d'Orage, au lieu de plaques trans_ croisées.
Le cristal est opaque (faces colorées, facettes peintes) : des faces trans_ laisseraient voir l'intérieur du volume.
Repère (catégorie objets, Recette) : pointe vers +Y, centrée dans le bloc (y de -9 à 25), grand plat du fer face à +Z.
Fonctions avancées : add_, calque _e, étapes du guide 14. Rien d'animé (ni son, ni particule).
"""
import base64, io, json, math, os, random, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image, ImageDraw

NOM = "skin_lance_orage"
TEX = 512
TAU = 2 * math.pi
SS = 4
K_R = 1.12                              # rayons de la hampe et de la gaine un peu forcis (lisibles dans la case)
DF = float(os.environ.get("DF", "14"))  # texels par px sur les faces des volumes

METAL = np.array([(22, 24, 36), (46, 52, 72), (70, 78, 104), (112, 122, 154), (170, 182, 214)], np.float32)
OR = np.array([(130, 90, 30), (176, 128, 44), (220, 170, 60), (255, 230, 140)], np.float32)
CRIS = np.array([(30, 30, 96), (50, 60, 160), (80, 104, 220), (130, 160, 255), (190, 208, 255), (232, 240, 255)], np.float32)
BLANC = np.array((236, 244, 255), np.float32)
NIVS = ("repos", "leve", "lance")


def lerp(a, b, k):
    return a + (b - a) * k


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


# ------------------------------------------------------------------ outils du plan (a le long de la lance, b en travers, z)
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


def cellules(P, f=1.7, seed=0.0):
    """Facettes : valeur constante par cellule, -0,5..0,5."""
    ix, iy = np.floor(P[..., 0] * f + 0.37 * np.floor(P[..., 1] * f)), np.floor(P[..., 1] * f)
    v = np.sin(ix * 127.1 + iy * 311.7 + seed * 74.7) * 43758.5453
    return v - np.floor(v) - 0.5


# ------------------------------------------------------------------ fer : feuille à deux crans d'éclair par bord (design d'avant)
FA0, FER_L, FER_H = 13.3, 8.4, 3.4
TIP = (FA0 + FER_L, 0.0)


def hw_fer(u):
    """Demi-largeur du fer (profil de la version validée) : u de la base (0) à la pointe (1)."""
    prof = np.interp(u, [0, 0.06, 0.28, 0.46, 0.62, 0.80, 1.0], [0.18, 0.62, 1.0, 0.86, 0.70, 0.42, 0.0])
    k1 = 0.30 * np.clip(1 - (u - 0.40) / 0.13, 0, 1) * (u >= 0.40)
    k2 = 0.22 * np.clip(1 - (u - 0.64) / 0.12, 0, 1) * (u >= 0.64)
    return float(np.clip(prof - k1 - k2, 0, None)) * FER_H / 2


KN = [0.0, 0.06, 0.17, 0.28, 0.3999, 0.40, 0.46, 0.53, 0.62, 0.6399, 0.64, 0.70, 0.76, 0.80, 0.90, 1.0]
U_F = [(FA0 + FER_L * u, hw_fer(u)) for u in KN[:-1]] + [TIP]
L_F = [(a, -b) for a, b in U_F]
FER = U_F + L_F[::-1][1:-1]
Z_E = 0.10                        # demi-épaisseur au fil
TH = 0.3                          # épaisseur des cubes de biseau, de plat, de paroi
RECOUV = 0.08
T_BIS = 0.85                      # pente unique des biseaux (40°)


def h_fer(a):
    """Demi-épaisseur du plat : 0,55 dans la douille, 0,62 à sa sortie (1,24 px), 0,25 à la pointe (0,50 px)."""
    return np.interp(np.asarray(a, float), [FA0, 14.4, TIP[0]], [0.55, 0.62, 0.25])


def wb_fer(a):
    return (h_fer(a) - Z_E) / T_BIS


# Ailettes : feuille croisée (plan perpendiculaire au fer), nées de la douille, deux crans d'éclair, fondues dans le fer
AIL = [(12.95, 0.0), (12.95, 0.78), (13.55, 1.42), (14.15, 1.62), (14.2, 1.18), (14.75, 1.34), (14.8, 0.96), (15.5, 0.5), (16.1, 0.0)]
H_A, ZE_A = 0.34, 0.08
H_A_FN = lambda a: np.full(np.shape(a), H_A, float)
WB_A_FN = lambda a: np.full(np.shape(a), (H_A - ZE_A) / T_BIS, float)

# Gouttière en zigzag au milieu du fer, au-dessus des ailettes (qui finissent dans le fer à a = 16,1)
SLIT = [(16.3, 0.0), (16.95, 0.09), (17.65, -0.09), (18.35, 0.09), (19.05, -0.08), (19.75, 0.07), (20.4, 0.0)]
GW = [0.07, 0.17, 0.19, 0.19, 0.17, 0.14, 0.06]
Z_FOND = 0.16


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
    return cotes, [tuple(p) for p in cotes[1]] + [tuple(p) for p in cotes[-1][::-1]]


GOUT_COTES, GOUT = _gouttiere()


def in_gout(P):
    return in_poly(P, GOUT)


def d_gout(P):
    return d_poly(P, GOUT + [GOUT[0]])


class Piece:
    """Plaque biseautée : contour `poly`, fils `fils` (sans la base cachée), profil h(a), wb(a), z au bord."""

    def __init__(self, nom, poly, fils, h, wb, ze, peint, trou=None):
        self.nom, self.poly, self.h, self.wb, self.ze, self.peint, self.trou = nom, poly, h, wb, ze, peint, trou
        self.segs = [s for f in fils for s in subdiv(f)]
        pa = np.array(poly)
        self.box = (pa[:, 0].min() - 0.05, pa[:, 0].max() + 0.05, pa[:, 1].min() - 0.05, pa[:, 1].max() + 0.05)

    def dE(self, P):
        return d_stack(P, self.segs).min(0)

    def surf(self, P):
        d, h, wb = self.dE(P), self.h(P[..., 0]), self.wb(P[..., 0])
        return np.where(d < wb, self.ze + (h - self.ze) * np.clip(d / wb, 0, 1), h)


SPECS = []          # cubes : dict(groupe, nom, c, X, Y, s, faces) dans le plan (a, b, z)
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


def spec(groupe, nom, c, X, Y, s, peintures, M=None):
    """peintures : {face: fn(points (H, W, 3)) -> (col, em, masque)} ; les autres faces sont transparentes.
    M : passage du plan de la pièce au plan de la lance (ailettes : plan perpendiculaire)."""
    X, Y, Z = repere(X, Y)
    c = np.asarray(c, float)
    faces = {}
    for f, fn in peintures.items():
        col, em, m = fn(points_face(c, X, Y, Z, s, f))
        if m.any():
            TILES[f"{nom}_{f}"] = finir(col, em, m)
            faces[f] = f"{nom}_{f}"
    if M is not None:
        c, X, Y = M @ c, M @ X, M @ Y
    SPECS.append({"groupe": groupe, "nom": nom, "c": c, "X": X, "Y": Y, "s": s, "faces": faces})


def volume(pc, groupe, tag, M=None):
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
                col, em = pc.peint("biseau", P2, dE)
                return col, em, m

            def fil(P, idx=idx, n=n):
                P2 = P[..., :2] + n * 0.06
                D = d_stack(P2, pc.segs)
                m = in_poly(P2, pc.poly) & (D[idx] <= D.min(0) + RECOUV)
                col, em = pc.peint("fil", P2, D.min(0))
                return col, em, m

            spec(groupe, f"{tag}{pc.nom}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil}, M)
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
            col, em = pc.peint("plat", P2, dE)
            return col, em, m

        spec(groupe, f"{tag}{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, ((a1 - a0) * math.sqrt(1 + sl * sl), b1 - b0, TH), {"south": plat}, M)


# --- peintures du cristal d'orage, par étape (0 repos, 1 leve, 2 lance) : couleurs portées par les faces
FIL_E = (np.array((110, 150, 235.)), np.array((165, 190, 250.)), np.array((225, 235, 255.)))
ECLAIR = (0.0, 0.22, 0.48)                      # éclaircissement du cristal par étape


def peintre(niv, wb_fn, ailette=False):
    def peint(face, P, dE):
        sh = P.shape[:-1] + (3,)
        if face == "fil":
            return np.zeros(sh, np.float32) + BLANC, np.zeros(sh, np.float32) + FIL_E[niv]
        u = np.clip((P[..., 0] - FA0) / FER_L, 0, 1)[..., None]
        wb = wb_fn(P[..., 0])
        em = np.zeros(sh, np.float32)
        if face == "biseau":
            f = (dE / wb)[..., None]
            nz = cellules(P, 2.4, 1.0 + niv)[..., None]
            col = lerp(CRIS[4], CRIS[2], np.clip((f - 0.36) / 0.5, 0, 1)) + nz * 14
            col = np.where(f < 0.36, lerp(CRIS[5], CRIS[4], np.clip((f - 0.14) / 0.22, 0, 1)), col)
            col = np.where(f >= 0.93, CRIS[1] * (0.8 if ailette else 0.9), col)
            col = lerp(col, BLANC, ECLAIR[niv])
            col = np.where(f < 0.14, BLANC, col)
            em = np.where(f < 0.16, FIL_E[niv], em)
            if niv == 1:
                em = np.where((f >= 0.16) & (f < 0.40), np.array((60, 84, 180.)), em)
            if niv == 2:
                em = np.where((f >= 0.16) & (f < 0.93), lerp(np.array((70, 92, 190.)), np.array((40, 52, 130.)), f), em)
            return col, em
        # plat : cristal facetté, plus clair vers la pointe, arête sombre au bord des biseaux
        nz = cellules(P, 1.5, 3.0 + niv)[..., None]
        col = lerp(CRIS[1], CRIS[3], 0.25 + 0.6 * u) + nz * 26
        if ailette:
            col = lerp(CRIS[1], CRIS[2], 0.5) + nz * 22 + np.zeros(sh, np.float32)
        col = lerp(col, CRIS[5], ECLAIR[niv])
        if niv == 2:
            em = em + lerp(np.array((30, 40, 96.)), np.array((64, 82, 165.)), u)
        bord = (dE < wb + 0.05)[..., None]
        col = np.where(bord, CRIS[0] * (1 + ECLAIR[niv]), col)
        if not ailette:
            dg = d_gout(P)[..., None]
            levre = dg < 0.07
            col = np.where(levre, np.array((200, 216, 255.)), col)
            em = np.where(levre, np.array((60, 100, 210.)) * (1 + 0.5 * niv), em)
            col = np.where((dg >= 0.07) & (dg < 0.12), CRIS[0], col)
            orl = (dg >= 0.18) & (dg < 0.26) & (dE > wb + 0.12)[..., None]
            col = np.where(orl, np.where(dg < 0.21, OR[3], OR[2]), col)
        return col, em
    return peint


M_AIL = {1: np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float),      # (a, b', z') -> (a, -z', b') : ailette vers +z
         -1: np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)}      # (a, b', z') -> (a, z', -b') : ailette vers -z


def gouttiere(groupe, tag, pc, niv):
    """Fond (âme de 0,32 px où repose la foudre) + parois verticales le long des deux bords, sur chaque face."""
    pa = np.array(GOUT)
    a0, a1, b0, b1 = pa[:, 0].min() - 0.15, pa[:, 0].max() + 0.15, pa[:, 1].min() - 0.15, pa[:, 1].max() + 0.15

    def fond(P):
        P2 = P[..., :2]
        m = in_gout(P2) | (d_gout(P2) < 0.1)
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + np.array((16, 18, 40), np.float32) + cellules(P2, 3.0, 5.0)[..., None] * 6
        em = np.zeros_like(col) + np.array((14, 22, 70), np.float32) * (1 + 0.6 * niv)
        return col, em, m

    spec(groupe, f"{tag}fond", ((a0 + a1) / 2, (b0 + b1) / 2, 0.0), (1, 0, 0), (0, 1, 0), (a1 - a0, b1 - b0, 2 * Z_FOND),
         {"south": fond, "north": fond})
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
        inside_pt = mid - n * 0.05
        if not (in_gout(np.array([inside_pt]))[0] or d_gout(np.array([inside_pt]))[0] < 1e-3):
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
                col = lerp(CRIS[1], CRIS[0], np.clip((dz[..., None] - 0.1) / 0.3, 0, 1)) + np.zeros(P.shape[:-1] + (3,), np.float32)
                col = lerp(col, CRIS[3], ECLAIR[niv] * 0.6)
                em = np.zeros_like(col)
                lv = dz < 0.1
                col[lv] = (200, 216, 255)
                em[lv] = np.array((60, 100, 210.)) * (1 + 0.5 * niv)
                return col, em, np.ones(P.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zc)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec(groupe, f"{tag}paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


FERS = {}


def conception():
    SPECS.clear()
    TILES.clear()
    for niv, nm in enumerate(NIVS):
        tag = "rlx"[niv]
        fer = Piece("fer", FER, [U_F, L_F], h_fer, wb_fer, Z_E, peintre(niv, wb_fer), trou=in_gout)
        FERS[niv] = fer
        volume(fer, f"fer_{nm}", tag)
        gouttiere(f"fer_{nm}", tag, fer, niv)
        for sg in (1, -1):
            ail = Piece(f"ail{'pm'[sg < 0]}", AIL, [AIL[1:]], H_A_FN, WB_A_FN, ZE_A, peintre(niv, WB_A_FN, ailette=True))
            volume(ail, f"fer_{nm}", tag, M_AIL[sg])
    douille()


# Douille : tronc de cône à 8 pans (plaques inclinées, faces découpées par l'alpha au secteur de chaque pan)
D_A0, D_A1, D_R0, D_R1 = 12.85, 14.3, 0.84, 0.70


def douille():
    dr = (D_R1 - D_R0) / (D_A1 - D_A0)
    for k in range(8):
        ph = TAU * k / 8
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
            col = np.where((a > D_A1 - 0.24)[..., None], np.where((a > D_A1 - 0.09)[..., None], OR[3], OR[2]), col)
            col = np.where(((a > D_A1 - 0.32) & (a <= D_A1 - 0.24))[..., None], METAL[0], col)
            zz = np.abs(((a - D_A0) * 2.6 + 0.5 * np.sign(np.sin(ang * 4 + 0.4))) % 1 - 0.5)       # filet d'or en zigzag
            col = np.where(((zz < 0.07) & (a > D_A0 + 0.25) & (a < D_A1 - 0.4))[..., None], OR[2], col)
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


def t_hampe(W=336, H=12):
    """u le long de la hampe (a de -9 à 12), v en travers : arête claire, bagues d'or (version validée)."""
    x, y = g01(W, H)
    q = np.abs(y - 0.5) * 2
    col = METAL[np.clip((3.3 * (1 - q ** 1.3) + 0.8 * (q < 0.16)).astype(int), 0, 4)]
    a = -9 + 21 * x
    gold = ((a > -3.6) & (a < -3.0)) | ((a > 3.0) & (a < 3.6)) | ((a > 7.4) & (a < 7.8)) | (a > 11.4)
    col = np.where(gold[..., None], OR[np.clip((2.6 * (1 - q ** 1.4) + 0.8 * (q < 0.2)).astype(int), 0, 3)], col)
    return red(col, W, H)


def t_gaine(W=120, H=12):
    x, y = g01(W, H)
    q = np.abs(y - 0.5) * 2
    cuir = lerp(np.array((18, 22, 48), np.float32), np.array((52, 62, 112), np.float32), (1 - q ** 1.5)[..., None])
    band = np.mod(x * 12 + y * 0.9, 1) < 0.16
    col = np.where(band[..., None], cuir * 0.55, cuir)
    col = np.where(((x < 0.05) | (x > 0.95))[..., None], OR[2], col)
    return red(col, W, H)


def t_or16(W=24, H=24, sens="u"):
    """Côté d'un carré du tambour à 16 pans : seule la bande centrale (|t| <= R tan 11,25°) est sur le 16-gone, le reste
    (les coins qui dépasseraient en étoile) est transparent."""
    a = t_or(W, H) if sens == "v" else np.transpose(t_or(H, W), (1, 0, 2)).copy()
    k = math.tan(math.radians(11.25)) + 0.03
    t = np.abs((np.arange(W if sens == "u" else H) + 0.5) / (W if sens == "u" else H) * 2 - 1)
    hors = t > k
    if sens == "u":
        a[:, hors] = 0
    else:
        a[hors, :] = 0
    return a


def t_or(W=24, H=12):
    x, y = g01(W, H)
    q = np.abs(y - 0.5) * 2
    return red(OR[np.clip((3.2 * (1 - q ** 1.4) + 0.6 * (q < 0.2)).astype(int), 0, 3)], W, H)


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
    a = t_unie(16, 8, CRIS[4], CRIS[1], 4, bords=CRIS[0])
    e = a.copy()
    e[..., :3] = np.clip(a[..., :3].astype(np.float32) * 0.75, 0, 225).astype(np.uint8)
    return a, e


UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    core, core_e = t_core()
    cri, cri_e = t_cristal()
    conception()
    items = [(n, im, ime) for n, (im, ime) in TILES.items()]
    items += [("hampe", t_hampe(), None), ("gaine", t_gaine(), None), ("or", t_or(), None), ("or16u", t_or16(48, 12, "u"), None), ("or16v", t_or16(12, 48, "v"), None), ("medaillon", medaillon(), None),
              ("core", core, core_e), ("cristal", cri, cri_e), ("crk", t_crk(), None),
              ("sombre", t_unie(32, 8, METAL[2], METAL[1], 3), None)]
    items += [(f"halo{k}", t_halo(m), None) for k, m in enumerate((1.0, 1.35, 1.8))]
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


# contrôle : la gouttière reste dans le plat (marge entre son bord et le bord des biseaux)
_pg = np.array([p for p in GOUT])
_fer0 = Piece("fer", FER, [U_F, L_F], h_fer, wb_fer, Z_E, None)
_m = (_fer0.dE(_pg) - wb_fer(_pg[:, 0])).min()
print(f"marge gouttière / biseaux : {_m:+.2f} px")
assert _m > 0.08, "la gouttière mord les biseaux"
tex_b64, tex_e_b64 = atlas()

# ------------------------------------------------------------------ géométrie (repère de l'objet : a -> +Y, b -> -X, z -> +Z)
A_MIN, A_MAX = -12.3, TIP[0]                    # talon .. pointe (inchangés : réglages Display validés)
Q = np.array((8.0, 8.0 - (A_MIN + A_MAX) / 2, 8.0))
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
    """Barre octogonale le long de la lance (deux boîtes, la seconde tournée de 45° autour de l'axe) ; u de la tuile le long de a."""
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


def eclair3d(p, q, n, J, seed):
    """Éclair droit de p à q (a, b, z) : n tronçons, écarts perpendiculaires alternés dans deux directions."""
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
        sg = -sg
        out.append(p + (q - p) * t + o)
    return out


def bone_node(name):
    g = groups[name]
    return {"name": name.split("#")[0], "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


def poser_specs(nom_groupe, g):
    for sp in SPECS:
        if sp["groupe"] != nom_groupe:
            continue
        u_ = {f: (list(UV[sp["faces"][f]]) if f in sp["faces"] else CLEAR) for f in ("north", "south", "east", "west", "up", "down")}
        boite(g, sp["nom"], W_(*sp["c"]), Wv(*sp["X"]), Wv(*sp["Y"]), *sp["s"], u_)


# Partie commune (toujours dessinée) : gaine, hampe, talon, tambour, collet, douille
COMMUN = group("lance_tempete", W_(0))
GAINE = group("gaine", W_(0), COMMUN)
uh = lambda a: (a + 9) / 21
barre(GAINE, "gaine", -2.5, 2.5, 0.56 * K_R, "gaine")
for k, a_ in enumerate((-1.7, 0.0, 1.7)):          # bagues d'or en relief sur la gaine
    barre(GAINE, f"bague{k}", a_ - 0.18, a_ + 0.18, 0.56 * K_R + 0.12, "or")
H_AV = group("hampe_av", W_(2.5), COMMUN)
barre(H_AV, "hampe_av", 2.62, 12.3, 0.42 * K_R, "hampe", part=(uh(2.62), uh(12.0)), caps=None)
H_AR = group("hampe_ar", W_(-2.5), COMMUN)
barre(H_AR, "hampe_ar", -8.88, -2.62, 0.42 * K_R, "hampe", part=(uh(-8.88), uh(-2.62)))
barre(H_AR, "talon", -9.5, -9.0, 0.6 * K_R, "or")
barre(H_AR, "talon_cri0", -10.75, -9.42, 0.44, "cristal", caps="cristal")          # pointe de cristal (pommeau de l'épée)
barre(H_AR, "talon_cri1", -11.75, -10.65, 0.29, "cristal", caps="cristal")
barre(H_AR, "talon_cri2", -12.3, -11.68, 0.15, "cristal", caps="cristal", octo=False)
TETE = group("tete", W_(12.15), COMMUN)
R_I = 1.5                                        # tambour à 16 pans autour de la hampe (anneau d'avant), médaillons aux deux bouts
A_T0, A_T1 = 12.1, 12.8
for k in range(4):
    th = math.radians(22.5 * k)
    boite(TETE, f"tambour{k}", W_((A_T0 + A_T1) / 2), Wv(0, math.cos(th), math.sin(th)), Wv(0, -math.sin(th), math.cos(th)),
          2 * R_I, 2 * R_I, A_T1 - A_T0 - 0.04, {"north": CLEAR, "south": CLEAR, "east": UV["or16v"], "west": UV["or16v"], "up": UV["or16u"], "down": UV["or16u"]})
MR = R_I / math.cos(math.radians(11.25)) + 0.01
for sg, a_ in ((1, A_T1 - 0.12), (-1, A_T0 + 0.12)):
    fc = {"south": uvp("medaillon")} if sg > 0 else {"north": uvp("medaillon", flip=True)}
    boite(TETE, f"medaillon{'pm'[sg < 0]}", W_(a_), Wv(0, 1), Wv(0, 0, 1), 2 * MR, 2 * MR, 0.3,
          {**{f: CLEAR for f in ("north", "south", "east", "west", "up", "down")}, **fc})
barre(TETE, "collet", 12.78, 13.12, 0.92, "or")
barre(TETE, "douille_ame", 13.05, 14.22, 0.45, "sombre", caps="sombre")
barre(TETE, "levre", 14.18, 14.42, 0.73, "or")
poser_specs("douille", TETE)

# Étapes (groupes racine, guide 14) : fer de chaque étape + foudre couchée dans la gouttière + effets propres
FOUDRE_PTS = [W_(*p) for p in zigzag(SLIT, 12, 0.05, 17)]
ETAPES = {}
for niv, nm in enumerate(NIVS):
    racine = group(objet.etape(nm, "lance"), W_(0))
    g = group(f"fer_{nm}", W_(FA0), racine)
    poser_specs(f"fer_{nm}", g)
    fo = group(f"foudre_{nm}", W_(*SLIT[0]), g)
    trait(fo, "eclair", FOUDRE_PTS, 0.38, 0.26, "core")
    ga = group(f"add_gaine_{nm}", W_(*SLIT[0]), fo)
    for i in range(len(FOUDRE_PTS) - 1):
        am = (FOUDRE_PTS[i][1] + FOUDRE_PTS[i + 1][1]) / 2 - Q[1]
        seg(ga, f"gaine{i}", FOUDRE_PTS[i], FOUDRE_PTS[i + 1], min(0.82, 2 * float(h_fer(am)) - 0.14), f"halo{niv}", ov=0.04, roll=0.0)
    ETAPES[nm] = racine

# leve : éclat en étoile à la pointe (six rayons de foudre en géométrie, add_)
ECLAT = group("add_eclat", W_(*TIP), ETAPES["leve"])
for j, dvec in enumerate(((1, 0, 0), (0.55, 0.83, 0), (0.55, -0.83, 0), (0.5, 0, 0.86), (0.5, 0, -0.86), (-0.15, 0.7, 0.7))):
    dvec = unit(dvec)
    Ln = (1.5, 1.1, 1.1, 0.9, 0.9, 0.7)[j]
    pts = eclair3d(np.array((*TIP, 0.0)) + dvec * 0.15, np.array((*TIP, 0.0)) + dvec * Ln, 3, 0.12, 300 + j)
    trait(ECLAT, f"r{j}", [W_(*p) for p in pts], 0.2, 0.12, "crk")

# lance : éclairs figés, de l'anneau à la pointe le long des deux fils, et sur la hampe avant (la charge monte vers le fer)
ECL = group("add_eclairs", W_(FA0), ETAPES["lance"])


def exterieur(poly, dist, sg):
    out = []
    P = [np.array(p, float) for p in poly]
    for i, p in enumerate(P):
        d = unit(P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)])
        n = np.array((-d[1], d[0]))
        if n[1] * sg < 0:
            n = -n
        out.append(tuple(p + n * dist))
    return out


for sg, poly in ((1, U_F[2:]), (-1, L_F[2:])):
    pts = zigzag(exterieur(poly, 0.22, sg), 9, 0.16, 51 if sg > 0 else 77, zj=0.12)
    trait(ECL, f"fil{'pm'[sg < 0]}", [W_(*p) for p in pts], 0.24, 0.14, "crk")
    for i in range(len(pts) - 1):
        seg(ECL, f"halo_fil{'pm'[sg < 0]}{i}", W_(*pts[i]), W_(*pts[i + 1]), 0.55, "halo2", ov=0.03, roll=0.0)
for j, (zs, seed) in enumerate(((1, 91), (-1, 97))):
    pts = eclair3d((4.5, 0.62 * zs, 0.35 * zs), (12.0, 0.75 * zs, -0.3 * zs), 8, 0.22, seed)
    trait(ECL, f"hampe{j}", [W_(*p) for p in pts], 0.22, 0.16, "crk")
    for i in range(len(pts) - 1):
        seg(ECL, f"halo_hampe{j}{i}", W_(*pts[i]), W_(*pts[i + 1]), 0.5, "halo2", ov=0.03, roll=0.0)

outliner = [bone_node(n) for n, gg in groups.items() if gg["parent"] is None]

# ------------------------------------------------------------------ réglages Display (inchangés, validés en jeu le 2026-11-05)


def display_vanilla(rot_v, trans_v, ech_v, longueur_v, incl_x=0.0):
    """Display de la lance de Minecraft (image plate, pointe en haut à gauche de l'image de 32 × 32 : axe (-1, 1) du modèle,
    longueur longueur_v px du modèle) recalculé pour cet objet (axe +Y, longueur A_MAX - A_MIN, prise en Q)."""
    Rv = objet._rxyz((incl_x, 0, 0))[:3, :3] @ objet._rxyz(rot_v)[:3, :3] @ rotm(0, 0, 45)
    ex, ey, ez = euler(Rv.T)
    rot = [round(-ex, 2) + 0.0, round(-ey, 2) + 0.0, round(-ez, 2) + 0.0]
    assert np.allclose(objet._rxyz(rot)[:3, :3], Rv, atol=1e-3)
    k = ech_v * longueur_v / (A_MAX - A_MIN)
    prise = np.array((0, Q[1] - 8, 0))
    tr = np.asarray(trans_v, float) - objet._rxyz(rot)[:3, :3] @ (k * prise)
    return {"rotation": rot, "translation": [round(float(v), 2) for v in tr], "scale": [round(k, 3)] * 3}


LV = 30 * math.sqrt(2) / 2
AFFICHAGE = objet.affichage(
    "lance",
    thirdperson_righthand=display_vanilla((5, 270, -40), (0, 2, 2), 1.7, LV),
    firstperson_righthand=display_vanilla((-20, 90, -35), (3.13, 2.0, 0.13), 1.36, LV, incl_x=-25),
    gui={"rotation": [0, 0, -45], "translation": [0, 0, 0], "scale": [0.6, 0.6, 0.6]},
)
for c_ in ("thirdperson", "firstperson"):
    d_ = AFFICHAGE[f"{c_}_righthand"]
    AFFICHAGE[f"{c_}_lefthand"] = {"rotation": [d_["rotation"][0], -d_["rotation"][1], -d_["rotation"][2]],
                                   "translation": [-d_["translation"][0], d_["translation"][1], d_["translation"][2]], "scale": list(d_["scale"])}

# ------------------------------------------------------------------ écriture
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = objet.modele(NOM, "lance", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE)
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


Pc = []
for e in elements:
    f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
    R = rotm(*e.get("rotation", (0, 0, 0)))
    for i in range(8):
        Pc.append(R @ (np.array([(f, t)[(i >> k) & 1][k] for k in range(3)]) - o) + o)
Pc = np.array(Pc)
print("Display :", json.dumps({k: AFFICHAGE[k] for k in ("thirdperson_righthand", "firstperson_righthand", "gui")}))
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), "; 0 anims ; 0 keyframes ;",
      os.path.getsize(out) // 1024, "Ko")
print("boîte :", Pc.min(0).round(2).tolist(), "->", Pc.max(0).round(2).tolist())
