"""Trident de givre : skin d'objet (guide 14) pour tous les tridents du joueur, ensemble Givre (thème Éléments). Design original.
Écrit skin_trident_givre.png, skin_trident_givre_e.png et .build/skin_trident_givre_brut.bbmodel à côté de ce script.

Langage du set (.claude/styles/givre.md, épée/lance de givre) : glace = peau trans_ mince sur âme opaque à cœur cyan _e,
argent froid, flocons en relief à gemme hexagonale, cristaux hexagonaux pointus, fusée de cuir bleu nuit cloutée.
Silhouette propre (la lance de givre est une feuille de cristal plate en losange, oreilles de cristal) : **fourche d'argent**
en croissant biseauté (vrai volume, recette .claude/references/objets/volume-3d.md : biseaux en cubes inclinés à pente
unique 50°, plats, faces échantillonnées texel par texel, découpées par l'alpha, recouvrement 0,08), veine de glace
lumineuse incrustée sur ses plats ; **trois dents de glace à section hexagonale réelle** (stalactites : peau trans_ à 6 pans
autour d'une âme opaque à filets _e, pied enfoncé, ventre, pointe), serties dans des viroles d'argent ; deux petits cristaux
au pied de la dent centrale (vers l'avant et l'arrière, lisibles de profil), un cristal-ardillon sur le dehors de chaque dent
latérale (silhouette en ψ dans la case). Collet d'argent octogonal à flocons en relief et gemmes, douille conique, hampe
d'argent à bagues, fusée de cuir cloutée à la prise, pique de cristal au talon.

Étapes (guide 14) : `repos` (quelques aiguilles de givre aux viroles), `leve` (prêt à lancer : le givre gagne les dents,
18 aiguilles qui poussent avec q.use_progress, étoile qui pulse), `lance` (en vol : dents couvertes de givre, traînée de
flocons qui tournent le long de la hampe, vers l'arrière).
Repère : pointe vers +Y, axe en x = z = 8, du talon (y = -7,5) à la pointe (y = 23,7), plat face à +Z. Display des mains :
`objet.affichage_trident()` (recalcul de `item/trident_in_hand` du jar, comme skin_trident_orage).

Objet vivant (guide 14), sobre :
- item_idle (8 s) : scintillement à la pointe centrale puis à une pointe latérale ; flocons coupés (ctrl_emit -1) ;
- item_gui : rien ne bouge ;
- item_use (1,2 s, étape leve) : les aiguilles de givre grandissent avec q.use_progress, étoile qui pulse à la pointe ;
- event_release (0,6 s) : éclat de glace à la pointe (étoile add_ + gerbe de 8 éclats qui sortent puis rentrent) et flocons
  de Minecraft (ctrl_emit) ; **seul son** block.amethyst_block.chime ;
- event_select (0,6 s) : les dents poussent depuis leurs viroles, la centrale puis les latérales ;
- overlay_vol (1 s) : traînée de flocons de l'étape lance (groupes dessinés en vol seulement).
Effets repliés à 1/10 sur des pivots cachés dans la glace ; chaque groupe n'est mis à l'échelle que par une seule animation.
Fonctions avancées : trans_, add_, calque _e, ctrl_emit, emit_mc_snowflake, scale animé, étapes, animations d'objet,
Molang (q.use_progress). À juger en jeu : prise en main et pose levée (Display recalculé, le mod n'a pas trident_throwing),
glace avec et sans shader, event_release et son son, overlay_vol sur le trident en vol.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

NOM = "skin_trident_givre"
TEX = 512
TAU = 2 * math.pi
FOLD = 0.1

# Repère : a le long de la hampe (-> +Y, 0 au talon), b en travers (-> -X), z (-> +Z). 31,2 px comme skin_trident_orage.
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
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


C = lambda *c: np.array(c, np.float32)
G_DEEP, G_BODY, G_PALE, G_LIGHT = C(30, 96, 168), C(92, 186, 232), C(168, 226, 250), C(214, 244, 255)
BLANC = C(244, 253, 255)
LUEUR = C(150, 226, 255)
ARG_L, ARG_M, ARG_D = C(236, 244, 250), C(166, 186, 206), C(74, 90, 116)


def bez(P, s):
    P = [np.array(p, float) for p in P]
    u = 1 - s
    return u ** 3 * P[0] + 3 * u * u * s * P[1] + 3 * u * s * s * P[2] + s ** 3 * P[3]


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


def subdiv(pts, maxlen=2.0):
    out = []
    for i in range(len(pts) - 1):
        p, q = np.array(pts[i], float), np.array(pts[i + 1], float)
        n = max(1, int(math.ceil(np.linalg.norm(q - p) / maxlen)))
        for k in range(n):
            out.append((p + (q - p) * k / n, p + (q - p) * (k + 1) / n, k == 0 and i == 0, k == n - 1 and i == len(pts) - 2))
    return out


def d_stack(P, segs):
    out = []
    for p, q, *_ in segs:
        ab = q - p
        t = np.clip(((P - p) @ ab) / (ab @ ab), 0, 1)
        out.append(np.linalg.norm(P - (p + t[..., None] * ab), axis=-1))
    return np.stack(out)


# ------------------------------------------------------------------ croissant d'argent en vrai volume (opaque)
Z_E = 0.10                       # demi-épaisseur au fil
T_BIS = 1.19                     # pente unique des biseaux (50°)
H_C = 0.55                       # demi-épaisseur du plat (1,1 px)
WB = (H_C - Z_E) / T_BIS         # largeur des biseaux (0,38 px)
AL = math.atan(T_BIS)
TH = 0.3
DF = 16.0
RECOUV = 0.08
A_O = 22.6                       # centre du collet (le croissant passe dedans)
O_ = np.array((A_O, 0.0))
R_COL = 1.15
Z_COL = 0.85
A_CUT = 25.1                     # bout des bras, caché dans les viroles des dents latérales
B_LAT = 2.3                      # axe des dents latérales au pied
A_LAT = 24.75

LOW = resample([tuple(bez([(22.3, 0.9), (22.9, 2.05), (23.9, 2.88), (A_CUT, 2.98)], s)) for s in np.linspace(0, 1, 40)], 0.62)
UPP = resample([tuple(bez([(A_CUT, 1.66), (24.6, 1.47), (23.95, 1.08), (23.68, 0.55)], s)) for s in np.linspace(0, 1, 30)], 0.62)
_R = [(22.0, 0.0)] + LOW + UPP + [(23.45, 0.0)]
POLY = _R + [(a, -b) for a, b in _R[::-1]][1:-1]
FILS = [LOW, UPP, [(a, -b) for a, b in LOW], [(a, -b) for a, b in UPP]]
VEINES = [[(22.95, s * 0.95), (23.45, s * 1.55), (24.1, s * 2.0), (A_CUT - 0.05, s * 2.32)] for s in (1, -1)]


class Croissant:
    def __init__(self, nom, poly, fils):
        self.nom, self.poly = nom, poly
        self.segs = []
        for f in fils:
            self.segs += subdiv(f, 2.0)
        self.u = np.array((1.0, 0.0))

    def dE(self, P):
        return d_stack(P, self.segs).min(0)


CR = Croissant("croissant", POLY, FILS)


def givre_bruit(P2, f=9.0):
    """Petits grains de givre (déterministes) sur le bord."""
    x, y = P2[..., 0] * f, P2[..., 1] * f
    return np.mod(np.abs(np.sin(np.floor(x) * 12.9898 + np.floor(y) * 78.233)) * 43758.5453, 1.0)


def arg_biseau(P2, d):
    f = np.clip(d / WB, 0, 1)[..., None]
    col = lerp(ARG_L, ARG_M, f ** 0.8) * (1 + 0.03 * np.sin(P2[..., 0] * 9))[..., None]
    g = givre_bruit(P2)
    frost = (d < 0.16) | ((d < 0.3) & (g > 0.62))
    col = np.where(frost[..., None], lerp(col, BLANC, 0.75), col)
    col = np.where((d < 0.06)[..., None], BLANC, col)
    col = np.where((f[..., 0] > 0.9)[..., None], ARG_D, col)          # trait d'ombre à l'arête du plat
    return col, None


def arg_fil(P2, d):
    return np.zeros(P2.shape[:-1] + (3,), np.float32) + BLANC, None


def arg_plat(P2, d):
    col = ARG_M * (1 + 0.03 * np.sin(P2[..., 0] * 23 + P2[..., 1] * 3))[..., None] + np.zeros(P2.shape[:-1] + (3,), np.float32)
    col = np.where((d < WB + 0.06)[..., None], lerp(col, ARG_D, 0.5), col)
    db = np.min(np.stack([d_poly(P2, v) for v in VEINES]), axis=0)
    em = np.zeros(col.shape, np.float32)
    halo = db < 0.13
    col[halo] = lerp(col[halo], C(110, 170, 210), 0.5)
    coeur = db < 0.065
    col[coeur] = lerp(C(200, 246, 255), C(120, 214, 246), np.clip(db[coeur] / 0.065, 0, 1)[..., None])
    em[coeur] = LUEUR
    return col, em


# ------------------------------------------------------------------ cubes différés
TILES = {}
TRANS_TILES = set()
CUBES = []
SIX = ("north", "south", "east", "west", "up", "down")


def tuile(nom, rgba, e=None, trans=False):
    assert nom not in TILES, nom
    TILES[nom] = (rgba, e)
    if trans:
        TRANS_TILES.add(nom)
    return nom


def finir(col, al, em, masque):
    rgba = np.zeros(col.shape[:2] + (4,), np.uint8)
    rgba[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    rgba[..., 3] = (np.clip(al, 1, 254).astype(np.uint8) if al is not None else 255) * masque
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


def spec(groupe, nom, c, X, Y, s, peintures, trans):
    X, Y, Z = repere(X, Y)
    c = np.asarray(c, float)
    faces = {}
    for f, fn in peintures.items():
        P = points_face(c, X, Y, Z, s, f)
        col, al, em, m = fn(P)
        if m.any():
            faces[f] = tuile(f"{nom}_{f}", *finir(col, al, em, m), trans=trans)
    if faces:
        CUBES.append({"groupe": groupe, "nom": nom, "c": Wp(*c), "R": np.column_stack([Wv(*X), Wv(*Y), Wv(*Z)]),
                      "half": np.asarray(s, float) / 2, "faces": faces})


def volume_argent(pc, groupe):
    """Plaque biseautée fermée opaque (argent) : un cube de biseau par tronçon de fil et par face, un plat par face."""
    for idx, (p, q, v0, v1) in enumerate(pc.segs):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        pm = (p + q) / 2
        cand = np.array([pm + n * 0.25, pm - n * 0.25])
        prof = np.where(in_poly(cand, pc.poly), d_poly(cand, list(pc.poly) + [pc.poly[0]]), -1.0)
        if prof[1] > prof[0]:
            n = -n
        rentrant = lambda v: bool(in_poly(v[None], pc.poly)[0])
        e0 = (WB * 1.6 if rentrant(p - d * 0.25) else 0.15) if v0 else 0.04
        e1 = (WB * 1.6 if rentrant(q + d * 0.25) else 0.15) if v1 else 0.04
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        sy = (WB + 0.1) / math.cos(AL)
        for sg in (1, -1):
            Y = np.array((n[0] * math.cos(AL), n[1] * math.cos(AL), sg * math.sin(AL)))
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0], mid[1], sg * Z_E)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(P, idx=idx):
                P2 = P[..., :2]
                D = d_stack(P2, pc.segs)
                de = D.min(0)
                m = in_poly(P2, pc.poly) & (D[idx] <= de + RECOUV) & (de < WB + 0.03)
                col, em = arg_biseau(P2, de)
                return col, None, em, m

            def fil(P, idx=idx, n=n):
                P2 = P[..., :2] + n * 0.04
                D = d_stack(P2, pc.segs)
                m = in_poly(P2, pc.poly) & (D[idx] <= D.min(0) + RECOUV)
                col, em = arg_fil(P2, D.min(0))
                return col, None, em, m

            spec(groupe, f"{pc.nom}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil}, trans=False)
    pa = np.array(pc.poly) - O_
    s0, s1, t0, t1 = pa[:, 0].min() - 0.05, pa[:, 0].max() + 0.05, pa[:, 1].min() - 0.05, pa[:, 1].max() + 0.05
    Pc = O_ + np.array(((s0 + s1) / 2, (t0 + t1) / 2))
    for sg in (1, -1):
        X = np.array((1.0, 0.0, 0.0))
        Y = sg * np.array((0.0, 1.0, 0.0))
        Z = np.cross(X, Y)
        c = np.array((Pc[0], Pc[1], sg * H_C)) - Z * (TH / 2)

        def plat(P):
            P2 = P[..., :2]
            de = pc.dE(P2)
            m = in_poly(P2, pc.poly) & (de >= WB - 0.03) & (np.linalg.norm(P2 - O_, axis=-1) > R_COL - 0.6)
            col, em = arg_plat(P2, de)
            return col, None, em, m

        spec(groupe, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, (s1 - s0, t1 - t0, TH), {"south": plat}, trans=False)


# ------------------------------------------------------------------ tours (pièces rondes, comme skin_arc_givre)
OVL, OVW = 0.04, 0.03


def p_argent(xn, t, ex):
    k = np.clip(0.45 + 0.3 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    col = lerp(ARG_D, ARG_L, (k ** 1.2)[..., None]) * (1 + 0.03 * np.sin(t * 37 + xn * 3))[..., None]
    col = np.where((np.abs(xn) > 0.86)[..., None], np.minimum(col * 1.14 + 10, 255), col)
    if ex.get("givre"):
        col = np.where(((t > 0.7) & (np.abs(xn) < 0.8))[..., None], lerp(col, BLANC, 0.6), col)
    return col, None, None


def p_glace(xn, t, ex):
    """Âme d'un cristal (opaque) : cyan, arêtes blanches, filet _e au milieu du pan."""
    k = np.clip(0.35 + 0.35 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + 0.25 * t, 0, 1)
    col = lerp(C(40, 110, 176), G_LIGHT, (k ** 1.1)[..., None])
    col = np.where((np.abs(xn) > 0.84)[..., None], BLANC, col)
    em = np.zeros(col.shape, np.float32)
    if ex.get("e"):
        ln = np.abs(xn) < 0.2
        col[ln] = lerp(col[ln], C(200, 248, 255), 0.7)
        em[ln] = LUEUR
    return col, em, None


def p_peau(xn, t, ex):
    """Peau d'un cristal (trans_) : glace claire, arêtes blanches plus denses, pointe plus pâle."""
    k = np.clip(0.45 + 0.3 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + 0.2 * t, 0, 1)
    col = lerp(C(110, 196, 236), C(214, 244, 255), k[..., None])
    al = 150 + 40 * t + 10 * (1 - np.abs(xn))
    ar = np.abs(xn) > 0.8
    col = np.where(ar[..., None], BLANC, col)
    al = np.where(ar, 224, al)
    return col, None, al


def p_givre(xn, t, ex):
    """Aiguille de givre (opaque) : blanc bleuté, arêtes blanches."""
    k = np.clip(0.55 + 0.3 * (1 - np.abs(xn)) + 0.15 * t + ex.get("clair", 0.0), 0, 1)
    col = lerp(C(120, 190, 230), BLANC, k[..., None])
    return col, None, None


def p_gemme(xn, t, ex):
    k = np.clip(0.4 + 0.4 * (1 - np.abs(xn)) + 0.2 * t + ex.get("clair", 0.0), 0, 1)
    col = lerp(C(40, 130, 210), C(170, 236, 255), k[..., None])
    return col, np.clip(col * 0.8, 0, 200), None


PEINTRES = {"argent": p_argent, "glace": p_glace, "peau": p_peau, "givre": p_givre, "gemme": p_gemme}


def tuile_pan(nom, mat, L, w0, w1, ex):
    if nom in TILES:
        return nom
    wm = max(w0, w1) + 2 * OVW
    Lf = L + 2 * OVL
    Wt, Ht = max(2, int(math.ceil(wm * DF))), max(2, int(math.ceil(Lf * DF)))
    yy, xx = np.mgrid[0:Ht, 0:Wt]
    x = ((xx + 0.5) / Wt - 0.5) * wm
    y = Lf * (1 - (yy + 0.5) / Ht) - OVL
    t = np.clip(y / max(L, 1e-6), 0, 1)
    hw = (w0 + (w1 - w0) * t) / 2 + OVW
    mask = np.abs(x) <= hw
    xn = np.clip(x / np.maximum(hw - OVW, 1e-3), -1, 1)
    col, em, al = PEINTRES[mat](xn, t, ex)
    return tuile(nom, *finir(col, al, em, mask), trans=al is not None)


def tour(g, nom, O, ax, ref, profil, n=8, phase=0.0, cle=None):
    """profil = [(b0, r0, b1, r1, [(mat, ex), ...]), ...] le long de ax (rayon = apothème) ; matières alternées par pan."""
    O, ax = np.asarray(O, float), unit(ax)
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    cle = cle or nom
    for i, (b0, r0, b1, r1, mats) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        tiles = [tuile_pan(f"{cle}{i}{'abcd'[j]}", m, L, 2 * r0 * tn, 2 * r1 * tn, ex) for j, (m, ex) in enumerate(mats)]
        db, dr = (b1 - b0) / L, (r1 - r0) / L
        wm = max(2 * r0 * tn, 2 * r1 * tn) + 2 * OVW
        for k in range(n):
            th = phase + TAU * k / n
            e = math.cos(th) * ref + math.sin(th) * w3
            Pa, Pb = O + b0 * ax + r0 * e, O + b1 * ax + r1 * e
            Y = unit(Pb - Pa)
            N = -dr * ax + db * e
            X = np.cross(Y, N)
            c = (Pa + Pb) / 2 - N * TH / 2
            CUBES.append({"groupe": g, "nom": f"{nom}{i}_{k}", "c": c, "R": np.column_stack([X, Y, N]),
                          "half": np.array((wm / 2, L / 2 + OVL, TH / 2)), "faces": {"south": tiles[k % len(tiles)]}})


CRIS_PEAU = [("peau", {"clair": 0.06}), ("peau", {"clair": -0.08})]
CRIS_AME = [("glace", {"clair": 0.1, "e": True}), ("glace", {"clair": -0.1})]
GIVRE_MAT = [("givre", {"clair": 0.1}), ("givre", {"clair": -0.1})]


def stalactite(g_trans, g_ame, nom, base, d, ref, pts, L, cle=None):
    """Cristal hexagonal à section réelle : pts = [(b, r), ...] le long de l'axe, pointe en L. Peau trans_ + âme opaque."""
    cle = cle or nom
    prof_p = [(b0, r0, b1, r1, CRIS_PEAU) for (b0, r0), (b1, r1) in zip(pts[:-1], pts[1:])] + [(pts[-1][0], pts[-1][1], L, 0.0, CRIS_PEAU)]
    tour(g_trans, nom, base, d, ref, prof_p, n=6, phase=math.pi / 6, cle=cle + "_p")
    pa = [(b, max(r - 0.2, r * 0.45)) for b, r in pts]
    prof_a = [(b0, r0, b1, r1, CRIS_AME) for (b0, r0), (b1, r1) in zip(pa[:-1], pa[1:])] + [(pa[-1][0], pa[-1][1], L - 0.22, 0.0, CRIS_AME)]
    tour(g_ame, nom + "_ame", base, d, ref, prof_a, n=6, phase=math.pi / 6, cle=cle + "_a")


def t_disque(nom, n, Ra, N=48):
    R = Ra / math.cos(math.pi / n)
    yy, xx = np.mgrid[0:N, 0:N]
    x = ((xx + 0.5) / N - 0.5) * 2 * R
    y = (0.5 - (yy + 0.5) / N) * 2 * R
    th = np.arctan2(y, x)
    sect = np.round(th / (TAU / n)) * (TAU / n)
    apo = x * np.cos(sect) + y * np.sin(sect)
    mask = apo <= Ra
    rr = apo / Ra
    col = lerp(ARG_L, ARG_M, rr[..., None] ** 1.5)
    col[(rr > 0.72) & (rr < 0.8)] = BLANC
    col[rr > 0.92] = ARG_D
    return tuile(nom, *finir(col, None, None, mask))


def disque(g, nom, c, Nrm, up, n, Ra, tile):
    Nrm = unit(Nrm)
    Y = unit(up - (up @ Nrm) * Nrm)
    X = np.cross(Y, Nrm)
    R = Ra / math.cos(math.pi / n)
    CUBES.append({"groupe": g, "nom": nom, "c": np.asarray(c, float) - Nrm * TH / 2, "R": np.column_stack([X, Y, Nrm]),
                  "half": np.array((R, R, TH / 2)), "faces": {"south": tile}})


def t_unie(nom, W, H, c0, c1, ligne=None):
    yy, xx = np.mgrid[0:H, 0:W]
    q = (yy + 0.5) / H
    col = lerp(c0, c1, q[..., None]) * (1 + 0.04 * np.sin(xx * 0.7))[..., None]
    if ligne is not None:
        col[int(H * 0.4):int(H * 0.4) + 2] = ligne
    return tuile(nom, *finir(col, None, None, np.ones((H, W), bool)))


def t_cuir(W=128, H=16):
    """Cuir bleu nuit enroulé en biais, clous d'argent (fusée de l'épée de givre)."""
    r = np.random.default_rng(5)
    yy, xx = np.mgrid[0:H, 0:W]
    f = ((xx + yy * 0.9) / 14.0) % 1.0
    c = lerp(C(44, 56, 104), C(16, 20, 44), f[..., None])
    c = np.where((f > 0.86)[..., None], C(8, 10, 24), c)
    c *= r.uniform(0.95, 1.05, (H, W))[..., None]
    for x in range(3, W - 4, 10):
        c[6:10, x:x + 5] = (176, 196, 220)
    return tuile("cuir", *finir(c, None, None, np.ones((H, W), bool)))


def t_etoile(nom, N=48):
    """Scintillement additif : étoile à quatre branches, noir = invisible."""
    yy, xx = np.mgrid[0:N, 0:N]
    x = ((xx + 0.5) / N - 0.5) * 2
    y = ((yy + 0.5) / N - 0.5) * 2
    r = np.hypot(x, y)
    br = np.maximum(np.exp(-np.abs(x) * 14) * (1 - np.abs(y)), np.exp(-np.abs(y) * 14) * (1 - np.abs(x)))
    k = np.clip(br * 1.2 + np.exp(-r * 6) * 0.9, 0, 1)
    col = lerp(C(0, 0, 0), C(200, 240, 255), k[..., None] ** 0.8)
    return tuile(nom, *finir(col, None, None, np.ones((N, N), bool)))


def t_flocon(nom, N=40):
    """Flocon à six branches découpé par l'alpha (opaque), cœur cyan."""
    yy, xx = np.mgrid[0:N, 0:N]
    x = ((xx + 0.5) / N - 0.5) * 2
    y = ((yy + 0.5) / N - 0.5) * 2
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    m = np.zeros((N, N), bool)
    for k in range(6):
        a = TAU * k / 6
        u, v = x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)
        m |= (u > 0) & (u < 0.95) & (np.abs(v) < 0.09)
        for f0 in (0.45, 0.7):
            for sg in (1, -1):
                bx, by = math.cos(sg * 0.95), math.sin(sg * 0.95)
                uu, vv = u - f0, v
                pr = uu * bx + vv * by
                pe = -uu * by + vv * bx
                m |= (pr > 0) & (pr < 0.3 * (1.2 - f0)) & (np.abs(pe) < 0.07)
    m |= r < 0.2
    col = lerp(BLANC, C(150, 220, 250), np.clip(r, 0, 1)[..., None] ** 1.5) + np.zeros((N, N, 3), np.float32)
    col[r < 0.12] = C(170, 236, 255)
    return tuile(nom, *finir(col, None, None, m))


def barre(g, nom, p, q, r, Rang, faces):
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = T_ if abs(X @ T_) < 0.9 else A_
    Y0 = unit(ref - (ref @ X) * X)
    Z0 = np.cross(X, Y0)
    a = math.radians(Rang)
    Y = math.cos(a) * Y0 + math.sin(a) * Z0
    CUBES.append({"groupe": g, "nom": nom, "c": (p + q) / 2, "R": np.column_stack([X, Y, np.cross(X, Y)]),
                  "half": np.array((np.linalg.norm(q - p) / 2, r, r)), "faces": faces})


def bar8(g, nom, p, q, r, tile, ov=0.0):
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X = unit(q - p)
    Y0 = unit(W_ - (W_ @ X) * X)
    Z0 = np.cross(X, Y0)
    a_ = r * math.tan(math.pi / 8) * 1.02
    for k in range(4):
        gk = math.pi / 4 * k
        Yk = math.cos(gk) * Y0 + math.sin(gk) * Z0
        d = 0.03 * k
        Lk = L + 2 * ov - 2 * d
        CUBES.append({"groupe": g, "nom": nom + "abcd"[k], "c": (p + q) / 2, "R": np.column_stack([X, Yk, np.cross(X, Yk)]),
                      "half": np.array((Lk / 2, r, a_)), "faces": {"south": tile, "north": tile, "up": tile, "down": tile}})


def plaque2(g, nom, c, X, Y, taille, tile):
    """Plaque vue des deux côtés (scintillement additif, flocon)."""
    X, Y = unit(X), unit(Y)
    CUBES.append({"groupe": g, "nom": nom, "c": np.asarray(c, float), "R": np.column_stack([X, Y, np.cross(X, Y)]),
                  "half": np.array((taille / 2, taille / 2, 0.15)), "faces": {"south": tile, "north": tile}})


# ------------------------------------------------------------------ conception
GROUPES = []        # (nom, pivot, parent)


def grp(nom, pivot, parent):
    GROUPES.append((nom, np.asarray(pivot, float), parent))
    return nom


def bague(b0, b1, ra, ro, rb, c=0.12, mat="argent"):
    return [(b0, ra, b0 + c, ro, [(mat, {"clair": 0.15})]), (b0 + c, ro, b1 - c, ro, [(mat, {}), (mat, {"clair": -0.08})]),
            (b1 - c, ro, b1, rb, [(mat, {"clair": -0.12})])]


def ab(a, b):
    return np.array((a, b), float)


# dents : (nom, pied (a, b), direction (a, b), profil, longueur)
TH_LAT = math.radians(7)
DENTS = [("dent_c", ab(23.3, 0.0), ab(1.0, 0.0), [(0.0, 0.62), (1.7, 0.80), (4.9, 0.72)], 7.9)]
for s, nm in ((1, "dent_g"), (-1, "dent_d")):
    DENTS.append((nm, ab(A_LAT, s * B_LAT), ab(math.cos(TH_LAT), s * math.sin(TH_LAT)), [(0.0, 0.56), (1.2, 0.66), (3.0, 0.60)], 5.2))
OUT = {}


def w3(p2, z=0.0):
    return Wp(p2[0], p2[1], z)


def v3(d2, z=0.0):
    return Wv(d2[0], d2[1], z)


def aiguilles(g_parent, prefixe, n_par_dent, seed, taille=1.0, chacune=False):
    """Aiguilles de givre sur les dents (sortent de la glace, penchées vers la pointe). Retourne la liste des groupes."""
    rng = np.random.default_rng(seed)
    out = []
    for nm, p, d, pts, L in DENTS:
        dd = unit(v3(d))
        lat = unit(np.cross(T_, dd))
        nn = n_par_dent if nm == "dent_c" else max(2, n_par_dent - 2)
        for j in range(nn):
            s = 1.0 + (L - 3.2) * (j + rng.uniform(0.1, 0.9)) / nn
            ph = math.radians(60 * j + rng.uniform(-18, 18) + (30 if nm == "dent_c" else 0))
            rad = math.cos(ph) * T_ + math.sin(ph) * lat
            r = float(np.interp(s, [q[0] for q in pts], [q[1] for q in pts]))
            base = w3(p) + dd * s + rad * (r - 0.12)
            dirn = unit(rad * math.cos(math.radians(48)) + dd * math.sin(math.radians(48)))
            Ln = taille * (0.75 + 0.45 * rng.uniform())
            gn = grp(f"{prefixe}_{nm[-1]}{j}", base, g_parent) if chacune else g_parent
            tour(gn, f"{prefixe}_{nm[-1]}{j}_a", base, dirn, dd, [(0.0, 0.10, Ln * 0.55, 0.15, GIVRE_MAT), (Ln * 0.55, 0.15, Ln, 0.0, GIVRE_MAT)],
                 n=6, cle=f"aig{int(Ln * 10)}")
            out.append(gn)
    return out


def conception():
    commun = grp("trident_givre", Wp(A_PRISE), None)
    # --- hampe : pique de cristal, talon, hampe d'argent à bagues, fusée de cuir cloutée entre deux viroles
    manche = grp("manche", Wp(A_PRISE), commun)
    t_cuir()
    hampe_t = t_unie("hampe", 48, 12, ARG_M, ARG_D, ligne=ARG_L)
    bar8(manche, "fusee", Wp(14.45), Wp(18.95), 0.58, "cuir")
    tour(manche, "virole_bas", Wp(0), A_, W_, bague(14.0, 14.7, 0.50, 0.72, 0.62), n=8, phase=math.pi / 8)
    tour(manche, "virole_haut", Wp(0), A_, W_, bague(18.7, 19.4, 0.62, 0.72, 0.50), n=8, phase=math.pi / 8)
    bar8(manche, "hampe_bas", Wp(2.0), Wp(14.1), 0.47, hampe_t)
    bar8(manche, "hampe_haut", Wp(19.3), Wp(20.4), 0.47, hampe_t)
    for k, a_ in enumerate((6.2, 10.4)):
        tour(manche, f"bague{k}", Wp(0), A_, W_, bague(a_ - 0.25, a_ + 0.25, 0.47, 0.6, 0.47), n=8, phase=math.pi / 8)
    tour(manche, "talon", Wp(0), A_, W_, bague(1.35, 2.1, 0.42, 0.64, 0.52), n=8, phase=math.pi / 8)
    pique = grp("pique", Wp(1.4), manche)
    tour(pique, "pique", Wp(1.45), -A_, W_, [(0.0, 0.46, 0.14, 0.54, CRIS_AME), (0.14, 0.54, 0.6, 0.54, CRIS_AME),
                                             (0.6, 0.54, 1.45, 0.0, CRIS_AME)], n=6, phase=math.pi / 6)
    # --- tête : douille conique, collet octogonal (axe z) à flocons en relief et gemmes
    tete = grp("tete", Wp(A_O), commun)
    tour(tete, "douille", Wp(0), A_, W_, [(20.2, 0.50, 20.35, 0.60, [("argent", {"clair": 0.15})]),
                                          (20.35, 0.60, 21.2, 0.84, [("argent", {}), ("argent", {"clair": -0.08})]),
                                          (21.2, 0.84, 21.45, 0.78, [("argent", {"clair": -0.12})])], n=8, phase=math.pi / 8)
    tour(tete, "collet", Wp(A_O), T_, A_, bague(-Z_COL, Z_COL, R_COL - 0.18, R_COL, R_COL - 0.18, c=0.16), n=8, phase=math.pi / 8)
    td = t_disque("disque_collet", 8, R_COL - 0.18)
    bras_t = t_unie("bras", 32, 8, ARG_L, ARG_M, ligne=BLANC)
    cap_t = t_unie("bras_bout", 8, 8, BLANC, ARG_M)
    fb = {f: bras_t for f in ("south", "north", "up", "down")}
    fb.update(east=cap_t, west=cap_t)
    for s in (1, -1):
        cs = "e" if s > 0 else "i"
        fl = grp(f"flocon_{cs}", Wp(A_O, 0, s * Z_COL), tete)
        disque(fl, f"couvercle_{cs}", Wp(A_O, 0, s * Z_COL), T_ * s, A_, 8, R_COL - 0.18, td)
        zc = s * (Z_COL + 0.04)
        Rf = 0.98
        for k in range(3):
            th = math.radians(90 + 60 * k)
            e = math.cos(th) * A_ + math.sin(th) * W_
            barre(fl, f"bras_{cs}{k}", Wp(A_O, 0, zc) - e * Rf, Wp(A_O, 0, zc) + e * Rf, 0.11, 45, fb)
        for k in range(6):
            th = math.radians(90 + 60 * k)
            e = math.cos(th) * A_ + math.sin(th) * W_
            for fr, ln in ((0.55, 0.30), (0.82, 0.2)):
                base = Wp(A_O, 0, zc + s * 0.01) + e * Rf * fr
                for sg in (-1, 1):
                    t2 = th + sg * math.radians(55)
                    e2 = math.cos(t2) * A_ + math.sin(t2) * W_
                    barre(fl, f"branche_{cs}{k}{'pm'[sg < 0]}{int(fr * 10)}", base - e2 * 0.05, base + e2 * ln, 0.07, 45, fb)
        tour(fl, f"gemme_{cs}", Wp(A_O, 0, s * Z_COL), T_ * s, A_,
             [(0.0, 0.32, 0.18, 0.32, [("gemme", {"clair": 0.1}), ("gemme", {"clair": -0.1})]),
              (0.18, 0.32, 0.42, 0.0, [("gemme", {"clair": 0.2}), ("gemme", {})])], n=6, cle="gemme")
    # --- fourche : croissant d'argent biseauté (vrai volume), passe dans le collet ; bouts cachés dans les viroles
    volume_argent(CR, grp("croissant", Wp(A_O), tete))
    # --- dents de glace serties dans des viroles d'argent (chaque dent pousse depuis sa virole à event_select)
    OUT["dents"] = []
    for nm, p, d, pts, L in DENTS:
        dd = unit(v3(d))
        if nm == "dent_c":
            tour(tete, "virole_c", w3(p), dd, T_, bague(0.25, 0.8, 0.86, 0.96, 0.84, c=0.1), n=6, phase=math.pi / 6)
        else:
            tour(tete, f"virole_{nm[-1]}", w3(p), dd, T_, bague(-0.15, 0.5, 0.74, 0.84, 0.70, c=0.1), n=6, phase=math.pi / 6,
                 cle="virole_l")
        g = grp(nm, w3(p) + dd * 0.5, tete)
        ga, gt = grp(f"ame_{nm}", w3(p), g), grp(f"trans_{nm}", w3(p), g)
        stalactite(gt, ga, nm, w3(p), dd, T_, pts, L, cle="dc" if nm == "dent_c" else "dl")
        if nm == "dent_c":                                   # deux petits cristaux au pied, vers l'avant et l'arrière (profil)
            for zs in (1, -1):
                dz = unit(A_ * math.cos(math.radians(34)) + T_ * zs * math.sin(math.radians(34)))
                stalactite(gt, ga, f"pied{'pm'[zs < 0]}", Wp(24.25, 0, zs * 0.45), dz, W_, [(0.0, 0.26), (0.5, 0.32)], 1.7, cle="pied")
        else:                                               # ardillon de cristal sur le dehors, penché vers la pointe
            s = 1 if d[1] > 0 else -1
            th = TH_LAT + math.radians(34)
            dz = unit(v3(ab(math.cos(th), s * math.sin(th))))
            stalactite(gt, ga, f"ardillon_{nm[-1]}", w3(p) + dd * 2.0 + unit(v3(ab(0, s))) * 0.3, dz, T_,
                       [(0.0, 0.28), (0.5, 0.34)], 1.75, cle="ardillon")
        OUT["dents"].append((g, w3(p), dd, L))
    # --- effets repliés à 1/10 sur des pivots cachés dans la glace (un dépliage par animation)
    et = t_etoile("etoile")
    tip_c = Wp(A_MAX - 0.9)
    gg, pg, dg, Lg = OUT["dents"][1]
    tip_g = pg + dg * (Lg - 0.8)
    for nm, c, taille, par in (("add_scint_c", tip_c, 2.2, commun), ("add_scint_g", tip_g, 1.6, commun),
                               ("add_eclat", tip_c, 3.6, commun)):
        g = grp(nm, c, par)
        plaque2(g, f"{nm}_a", c, A_, W_, taille, et)
        plaque2(g, f"{nm}_b", c, A_, T_, taille * 0.8, et)
        OUT[nm] = g
    # éclat de glace au lancer (event_release) : huit éclats en gerbe nés de la pointe centrale
    OUT["eclats"] = grp("eclats", tip_c, commun)
    for j in range(8):
        ph = math.radians(22.5 + 45 * j)
        th = math.radians(30 if j % 2 == 0 else 52)
        d = unit(A_ * math.cos(th) + (W_ * math.cos(ph) + T_ * math.sin(ph)) * math.sin(th))
        L = 2.2 if j % 2 == 0 else 1.6
        tour(OUT["eclats"], f"eclat{j}", tip_c + A_ * 0.4 + d * 0.05, d, W_ * math.sin(ph) - T_ * math.cos(ph),
             [(0.0, 0.10, L * 0.6, 0.17, GIVRE_MAT), (L * 0.6, 0.17, L, 0.0, GIVRE_MAT)], n=6, cle=f"ecl{j % 2}")
    emit = grp("emit_mc_snowflake", Wp(A_MAX - 1.2), commun)
    grp("ctrl_emit", Wp(A_MAX - 1.2), emit)
    # --- étapes (groupes racine, guide 14)
    repos = grp(objet.etape("repos", "trident"), Wp(A_PRISE), None)
    leve = grp(objet.etape("leve", "trident"), Wp(A_PRISE), None)
    lance = grp(objet.etape("lance", "trident"), Wp(A_PRISE), None)
    # repos : un peu de givre aux viroles (deux aiguilles par virole latérale, trois à la centrale)
    g_rep = grp("givre_repos", Wp(A_O + 2), repos)
    rng = np.random.default_rng(3)
    for nm, p, d, pts, L in DENTS:
        dd = unit(v3(d))
        lat = unit(np.cross(T_, dd))
        for j in range(3 if nm == "dent_c" else 2):
            ph = math.radians(120 * j + 40 + rng.uniform(-15, 15))
            rad = math.cos(ph) * T_ + math.sin(ph) * lat
            r = float(pts[0][1]) + 0.1
            base = w3(p) + dd * (0.95 if nm == "dent_c" else 0.62) + rad * (r - 0.1)
            dirn = unit(rad * math.cos(math.radians(50)) + dd * math.sin(math.radians(50)))
            tour(g_rep, f"rep_{nm[-1]}{j}", base, dirn, dd, [(0.0, 0.09, 0.35, 0.12, GIVRE_MAT), (0.35, 0.12, 0.65, 0.0, GIVRE_MAT)],
                 n=6, cle="aigrep")
    # leve : le givre gagne les dents (une aiguille par groupe : elles poussent avec q.use_progress) + étoile qui pulse
    OUT["givre_leve"] = aiguilles(grp("givre_leve", Wp(26.0), leve), "lv", 7, 11, 1.0, chacune=True)
    g = grp("add_scint_leve", tip_c, leve)
    plaque2(g, "add_scint_leve_a", tip_c, A_, W_, 2.6, et)
    plaque2(g, "add_scint_leve_b", tip_c, A_, T_, 2.0, et)
    OUT["add_scint_leve"] = g
    # lance : dents couvertes de givre + traînée de flocons le long de la hampe (vers l'arrière)
    aiguilles(grp("givre_vol", Wp(26.0), lance), "vl", 7, 11, 1.15)
    tf = t_flocon("flocon")
    OUT["trainee"] = []
    rng = np.random.default_rng(21)
    for j in range(12):
        a = 23.0 - j * 1.55
        ph = rng.uniform(0, TAU)
        rr = rng.uniform(1.0, 1.9)
        c = Wp(a, rr * math.cos(ph), rr * math.sin(ph))
        g = grp(f"flocon_vol{j}", c, lance)
        t = rng.uniform(1.3, 1.9)
        plaque2(g, f"flocon_vol{j}_a", c, A_, unit(W_ * math.cos(ph + 1.2) + T_ * math.sin(ph + 1.2)), t, tf)
        OUT["trainee"].append(g)
    OUT["commun"], OUT["tete"], OUT["leve"], OUT["lance"] = commun, tete, leve, lance
    return [commun, repos, leve, lance]


RACINES = conception()

# ------------------------------------------------------------------ repli (effets des événements)
REPLIES = [OUT[k] for k in ("add_scint_c", "add_scint_g", "add_eclat", "eclats", "add_scint_leve")]
_piv = {n: p for n, p, _ in GROUPES}
for cb in CUBES:
    if cb["groupe"] in REPLIES:
        o = _piv[cb["groupe"]]
        cb["c"] = o + FOLD * (cb["c"] - o)
        cb["half"] = cb["half"] * FOLD


def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, (im, ime) in sorted(TILES.items(), key=lambda it: (-it[1][0].shape[0], -it[1][0].shape[1])):
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
    assert tex[TEX - 2, TEX - 2, 3] == 0
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    zone = np.zeros(semi.shape, bool)
    for n in TRANS_TILES:
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
    """Angles (X, Y, Z) tels que R = Rz Ry Rx ; blocage de cardan (Y = ±90°) : tout l'angle sur X (piège noté)."""
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
for nom, piv, parent in GROUPES:
    assert nom not in groups and len(nom) <= 64, nom
    groups[nom] = {"origin": [round(float(v), 4) for v in piv], "uuid": nuid(), "ids": [], "parent": parent, "rotation": [0, 0, 0]}
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
def s_(v):
    return v if isinstance(v, str) else f"{v + 0.0:.4f}".rstrip("0").rstrip(".")


def kf(ch, t, x, y=None, z=None, interp="linear"):
    y = x if y is None else y
    z = x if z is None else z
    return {"channel": ch, "data_points": [{"x": s_(x), "y": s_(y), "z": s_(z)}], "time": round(t, 4), "interpolation": interp}


def anim(name, length, loop="once"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 20,
            "selected": name == "item_idle", "animators": {}}


def piste(an, g, keys):
    an["animators"][groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": keys}


def echant(L, n):
    return [round(L * i / n, 4) for i in range(n + 1)]


DEPLIE = 1 / FOLD


def pop(t0, dur, L, pic=1.0):
    """Échelle (repliée = 1) : s'ouvre à DEPLIE·pic en 30 % de dur puis se referme."""
    keys = [kf("scale", 0.0, 1.0)]
    if t0 > 0:
        keys.append(kf("scale", t0, 1.0))
    for k in range(1, 9):
        u = k / 8
        v = 1 + (DEPLIE * pic - 1) * (math.sin(math.pi * min(1, u / 0.3) / 2) if u <= 0.3 else (1 - sm(u, 0.3, 1.0)))
        keys.append(kf("scale", t0 + dur * u, v))
    keys.append(kf("scale", L, 1.0))
    return keys


def pousse(t0, dur, over=1.07):
    keys = [kf("scale", 0.0, 0.05)]
    if t0 > 0:
        keys.append(kf("scale", t0, 0.05))
    for k in range(1, 11):
        u = k / 10
        v = 0.05 + (over - 0.05) * (1 - (1 - u / 0.7) ** 2) if u <= 0.7 else lerp(over, 1.0, (u - 0.7) / 0.3)
        keys.append(kf("scale", t0 + dur * u, v))
    return keys


def emit(an, keys):
    piste(an, "ctrl_emit", keys)


# item_idle (8 s) : un scintillement à la pointe centrale, puis à la pointe latérale ; émetteur coupé.
idle = anim("item_idle", 8.0, "loop")
piste(idle, OUT["add_scint_c"], pop(2.2, 0.5, 8.0))
piste(idle, OUT["add_scint_g"], pop(5.6, 0.45, 8.0, 0.9))
emit(idle, [kf("position", 0, -1, 0, 0), kf("position", 8.0, -1, 0, 0)])

# item_gui : rien ne bouge, émetteur coupé.
gui = anim("item_gui", 4.0, "loop")
emit(gui, [kf("position", 0, -1, 0, 0), kf("position", 4.0, -1, 0, 0)])

# item_use (levé pour lancer, 1,2 s en boucle) : le givre gagne les dents avec q.use_progress, l'étoile de la pointe pulse.
L_USE = 1.2
use = anim("item_use", L_USE, "loop")
for i, g in enumerate(OUT["givre_leve"]):
    k0 = 0.12 + 0.05 * (i % 6)
    piste(use, g, [kf("scale", 0, f"0.15+0.85*math.clamp((q.use_progress-{k0:.2f})*2.2,0,1)")])
piste(use, OUT["add_scint_leve"], [kf("scale", t, 1 + (DEPLIE * 0.9 - 1) * (0.5 - 0.5 * math.cos(TAU * t / L_USE))) for t in echant(L_USE, 12)])
emit(use, [kf("position", 0, -1, 0, 0), kf("position", L_USE, -1, 0, 0)])

# event_release (0,6 s) : éclat de glace à la pointe (étoile + gerbe d'éclats qui sortent puis rentrent), flocons ; le seul son.
L_REL = 0.6
rel = anim("event_release", L_REL)
piste(rel, OUT["add_eclat"], pop(0.0, 0.4, L_REL))
ks = [kf("scale", 0.0, 1.0)]
for t in echant(L_REL, 20)[1:]:
    ks.append(kf("scale", t, 1 + (DEPLIE * 1.05 - 1) * sm(t, 0.0, 0.06) * (1 - sm(t, 0.25, 0.48))))
piste(rel, OUT["eclats"], ks)
emit(rel, [kf("position", 0, 8, 0, 0), kf("position", 0.2, 8, 0, 0), kf("position", 0.21, 0, 0, 0), kf("position", L_REL, 0, 0, 0)])

# event_select (0,6 s) : les dents poussent depuis leurs viroles, la centrale puis les latérales.
L_SEL = 0.6
sel = anim("event_select", L_SEL)
for i, (g, *_r) in enumerate(OUT["dents"]):
    piste(sel, g, pousse(0.0 if i == 0 else 0.12 + 0.04 * i, 0.34, 1.08))

# overlay_vol (1 s) : traînée de flocons (étape lance, dessinée en vol seulement) : naissent, glissent vers l'arrière en tournant.
L_OV = 1.0
ov = anim("overlay_vol", L_OV, "loop")
for j, g in enumerate(OUT["trainee"]):
    ph = (j * 0.37) % 1.0
    tw = round((1 - ph) * L_OV, 4) % L_OV
    ts = sorted(set(echant(L_OV, 10) + ([round(tw - 0.001, 4), tw] if tw > 0.002 else [])))
    pos, sca, rot = [], [], []
    for t in ts:
        u = (t / L_OV + ph) % 1.0
        if tw > 0.002 and abs(t - (tw - 0.001)) < 1e-6:
            u = 0.999                                   # juste avant le retour : au bout de la course, échelle ~0
        if abs(t - L_OV) < 1e-6:
            u = ph                                      # boucle fermée : même pose qu'à t = 0
        pos.append(kf("position", t, 0, -4.5 * u, 0))
        sca.append(kf("scale", t, max(0.02, math.sin(math.pi * u) ** 0.7)))
        rot.append(kf("rotation", t, 0, 360 * (t / L_OV + ph), 0))
    ov["animators"][groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": pos + sca + rot}

ANIMS = [idle, gui, use, rel, sel, ov]

# ------------------------------------------------------------------ écriture
assert 150 <= len(elements) <= 4000, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
GUI = float(os.environ.get("GUI", "0.52"))
AFFICHAGE = objet.affichage("trident", **objet.affichage_trident(Y_BAS, Y_HAUT),
                            gui={"rotation": [0, 0, -45], "translation": [0, 0, 0], "scale": [GUI] * 3})
model = objet.modele(NOM, "trident", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son
limiter_sons(model)
# Un seul son, au lancer (event_release) : tools/sons.py ne connaît pas encore les événements d'objet, on le pose après.
rel["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "block.amethyst_block.chime")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def coins(filtre=None):
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


P = coins()
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"boîte {P.min(0).round(2)} .. {P.max(0).round(2)} ; biseaux {WB:.2f} px, croissant {2 * H_C:.2f} px")
print("Display :", json.dumps({k: AFFICHAGE[k] for k in ("thirdperson_righthand", "firstperson_righthand", "gui")}))
