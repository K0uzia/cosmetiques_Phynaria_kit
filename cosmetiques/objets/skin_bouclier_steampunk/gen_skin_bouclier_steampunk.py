"""Rondache de chaudière : skin de bouclier (guide 14, type `bouclier`), ensemble Steampunk (thème Mécanique). Design original.
Écrit skin_bouclier_steampunk.png, skin_bouclier_steampunk_e.png et .build/skin_bouclier_steampunk_brut.bbmodel à côté de ce script.

Idée (analogie : la porte ronde d'une boîte à fumée de locomotive, bombée et rivetée, montée sur une roue dentée) :
- devant : **roue dentée de laiton** à 24 dents (signature du set, lue comme un engrenage dans la case), cerclage de cuivre
  riveté, **dôme d'acier bruni en 24 pans rivetés** (une porte de chaudière), moyeu de laiton et **manomètre ambre** au centre ;
- dos (vu en 1re personne) : petite **chaudière de cuivre** couchée sur deux selles de laiton, **porte de foyer à fentes**
  rougeoyantes, **second manomètre** sur la chaudière (même aiguille que celui de devant), tuyau de cuivre à **volant de vanne**
  qui monte jusqu'à la **soupape** dressée au-dessus du bord (le seul endroit d'où la vapeur sort, et elle monte) ; poignée de
  cuir cousu entre deux montants de laiton (place de la poignée vanilla), sangle d'avant-bras à boucle de laiton.
Chaque pièce sert au circuit : le foyer chauffe la chaudière, la pression se lit des deux côtés, la soupape décharge.
Lumière _e seulement : verre ambre des deux cadrans, fentes du foyer.

Vrai volume (recette .claude/references/objets/volume-3d.md) : la roue est une **plaque biseautée fermée** (pente unique 58°,
1,10 px, biseaux par tronçon de contour, faces échantillonnées texel par texel et découpées par l'alpha, recouvrement 0,06),
faite de 12 secteurs identiques (deux dents chacun, mêmes tuiles, posés par rotation) ; toutes les pièces rondes sont des
**tours** (couronnes de pans de 0,3 px) : cerclage, dôme, moyeu, dos bombé, chaudière, soupape, tuyau, poignée, montants.

Repère : celui du bouclier de Minecraft (plaque vanilla 12 x 22 de z = 1 à 2, face vers +Z, poignée vers -Z), Display de
`item/shield.json` recopié (gui réduit : la roue est plus large), étapes `repos` et `bloque` = deux copies (mêmes tuiles), pose de
blocage `pose_bloque` en Molang q.in_first_person x q.hand, calculée et contrôlée par matrices (technique de skin_bouclier_abyssal).

Objet vivant (« saccadé mécanique », styles/steampunk.md) :
- item_idle (24 s) : **garde** (pose_bloque, recette 2 du retour du 2026-11-08 soir), la pression monte par crans (les deux
  aiguilles : échelon, dépassement, rappel), le foyer s'avive (ctrl_lumiere), la soupape tremble puis se soulève : bouffée de
  white_smoke (ctrl_emit) ; deux cycles ; aucun son ;
- item_use (1,2 s) : garde, aiguilles au rouge qui tremblent, soupape qui frémit, foyer vif ; un coup paré
  (q.hit_by_entity) soulève la soupape et lâche de la vapeur (ctrl_emit) ;
- event_select (0,8 s) : on ouvre la vanne (volant d'un quart de tour par crans), tour d'essai des aiguilles, le foyer s'allume ;
- event_hit (0,9 s) : décharge : jet de vapeur modélisé qui jaillit de la soupape et **monte** (trans_jet, seul dépliage par
  `scale`, fondu ctrl_alpha), white_smoke (ctrl_emit +5), aiguilles qui chutent de trois crans ; **le seul son**
  (block.fire.extinguish à 0,04 s).
Aucun son ni animation sur event_use_start ni event_enter_* (rejoués à chaque coupure de l'utilisation, recette 3).
Fonctions avancées : calque _e, trans_jet, ctrl_alpha, ctrl_lumiere, emit_mc_white_smoke + ctrl_emit, étapes repos/bloque,
animations d'objet (item_idle, item_use, event_select, event_hit), Molang (q.in_first_person, q.hand, q.hit_by_entity), scale
animé. Non simulés par l'aperçu : animations en main, particules, ctrl_emit, ctrl_lumiere, son. À juger en jeu : garde tenue 5 s
(deux mains, 1re et 3e personne), dos en 1re personne, event_hit d'un bouclier et son son, vapeur au coup paré.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

NOM = "skin_bouclier_steampunk"
TEX = 512
TAU = 2 * math.pi
GUI = float(os.environ.get("GUI", "0.63"))
GUI_TY = float(os.environ.get("GUI_TY", "3.0"))
TH = 0.3
RECOUV = 0.06
OVL, OVW = 0.04, 0.03
DENS = 16.0                       # texels par px sur les pans des tours
DF = 14.0                         # texels par px sur les faces échantillonnées (roue)
KJ, F_GEO = 15.0, 1.0             # jet caché : géométrie F_GEO / KJ, clés scale <= KJ / F_GEO


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


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


A = lambda *c: np.array(c, np.float32)
BRASS = dict(hi=A(236, 196, 112), base=A(190, 142, 64), low=A(112, 76, 32))
COPPER = dict(hi=A(232, 150, 96), base=A(176, 92, 52), low=A(98, 46, 26))
STEEL = dict(hi=A(136, 140, 150), base=A(78, 82, 92), low=A(38, 40, 48))
LEATHER = dict(hi=A(150, 96, 60), base=A(104, 62, 36), low=A(60, 34, 20))
BR_FIL = A(250, 224, 150)
AMBRE, AMBRE_B = A(255, 210, 120), A(220, 150, 50)
VAPEUR, VAPEUR_B = A(250, 250, 248), A(220, 224, 228)


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


# ------------------------------------------------------------------ la roue dentée (un secteur de 30°, deux dents, repère local)
N_SECT = 12
DEMI = math.radians(15.0)
R_IN, R_ROOT, R_TIP = 7.15, 8.25, 9.15
ZR = 1.5                          # plan moyen (plaque vanilla : z 1 à 2)
H_R = 0.55                        # demi-épaisseur : 1,10 px
Z_E = 0.10                        # demi-épaisseur au fil
T_BIS = 1.6                       # pente unique des biseaux (58°) : dents étroites
AL = math.atan(T_BIS)
DELTA = 0.06 / R_ROOT             # recouvrement entre secteurs voisins


def pol(a, r):
    return (r * math.cos(a), r * math.sin(a))


class Secteur:
    """Secteur de la roue : plaque biseautée fermée, contour extérieur (dents) biseauté, arc intérieur caché sous le dôme et le dos."""

    def __init__(self):
        self.nom = "roue"
        ar, at = 0.62 / R_ROOT, 0.40 / R_TIP
        fil = [pol(-DEMI - DELTA, R_ROOT)]
        for c in (math.radians(-7.5), math.radians(7.5)):
            fil += [pol(c - ar, R_ROOT), pol(c - at, R_TIP), pol(c + at, R_TIP), pol(c + ar, R_ROOT)]
        fil.append(pol(DEMI + DELTA, R_ROOT))
        self.fil = fil
        self.poly = fil + [pol(a, R_IN) for a in np.linspace(DEMI + DELTA, -DEMI - DELTA, 12)]
        self.segs = subdiv(fil, 2.0)
        self.O = np.zeros(2)
        self.u = np.array((1.0, 0.0))
        self.k = 0.0
        self.h0 = H_R

    def h(self, P):
        return np.full(np.asarray(P, float).shape[:-1], self.h0)

    def wb(self, P):
        return np.maximum((self.h(P) - Z_E) / T_BIS, 0.02)

    def dE(self, P):
        return d_stack(P, self.segs).min(0)

    def masque_plat(self, P2, sg):
        """Le plat avant passe sous le cerclage (r 7,25), le plat arrière sous le bord du dos (r 7,45)."""
        return np.linalg.norm(P2, axis=-1) >= (7.15 if sg > 0 else 7.35)


SECT = Secteur()


def peint_biseau(pc, P2, d, sg):
    f = np.clip(d / pc.wb(P2), 0, 1.2)[..., None]
    col = lerp(BRASS["hi"], BRASS["base"], np.clip(f / 0.9, 0, 1) ** 0.8) + np.zeros(P2.shape[:-1] + (3,), np.float32)
    col = np.where(f < 0.16, BR_FIL, col)
    col = np.where(f > 0.88, BRASS["low"], col)
    return col, None, None


def peint_fil(pc, P2, d, sg):
    return np.zeros(P2.shape[:-1] + (3,), np.float32) + BR_FIL, None, None


def peint_plat(pc, P2, d, sg):
    r = np.linalg.norm(P2, axis=-1)
    k = np.clip((r - 7.2) / 1.9, 0, 1) * 0.55 + 0.25
    col = lerp(BRASS["base"], BRASS["hi"], k[..., None]) * (1 + 0.035 * np.sin(r * 40.0))[..., None]
    col = np.where((np.abs(r - 7.86) < 0.055)[..., None], BRASS["low"], col)        # cercle primitif gravé
    col = np.where((d < pc.wb(P2) + 0.05)[..., None], BRASS["low"] * 1.1, col)       # arête du plat
    return col, None, None


# ------------------------------------------------------------------ cubes différés (tuiles partagées par les deux étapes)
TILES = {}
TRANS = set()
CUBES = []
SPEC_CACHE = {}
SIX = ("north", "south", "east", "west", "up", "down")
XF = [np.zeros(3), np.eye(3)]     # repère local -> modèle des faces échantillonnées en cours
NSUF = [""]
SFX = ["r"]


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
    """Cube dans le repère local ; faces échantillonnées texel par texel, découpées par l'alpha ; posé par XF."""
    X, Y, Z = repere(X, Y)
    c = np.asarray(c, float)
    if nom not in SPEC_CACHE:
        faces = {}
        for f, fn in peintures.items():
            P = points_face(c, X, Y, Z, s, f)
            col, al, em, m = fn(P)
            if m.any():
                faces[f] = tuile(f"{nom}_{f}", *finir(col, al, em, m))
        SPEC_CACHE[nom] = faces
    faces = SPEC_CACHE[nom]
    if faces:
        T, M = XF
        CUBES.append({"groupe": groupe, "nom": f"{SFX[0]}_{nom}{NSUF[0]}", "c": T + M @ c, "R": M @ np.column_stack([X, Y, Z]),
                      "half": np.asarray(s, float) / 2, "faces": faces})


def volume(pc, groupe):
    """Plaque biseautée fermée opaque : deux biseaux par tronçon de fil (un par face), un plat par face."""
    for idx, (p, q, v0, v1) in enumerate(pc.segs):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        pm = (p + q) / 2
        cand = np.array([pm + n * 0.2, pm - n * 0.2])
        prof = np.where(in_poly(cand, pc.poly), d_poly(cand, list(pc.poly) + [pc.poly[0]]), -1.0)
        if prof[1] > prof[0]:
            n = -n
        wmax = float(max(pc.wb(p[None])[0], pc.wb(q[None])[0]))
        e0 = wmax * 1.6 if v0 else 0.04
        e1 = wmax * 1.6 if v1 else 0.04
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        sy = (wmax + 0.1) / math.cos(AL)
        for sg in (1, -1):
            Y = np.array((n[0] * math.cos(AL), n[1] * math.cos(AL), sg * math.sin(AL)))
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0], mid[1], sg * Z_E)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(P, idx=idx, sg=sg):
                P2 = P[..., :2]
                D = d_stack(P2, pc.segs)
                de = D.min(0)
                own = D[idx] <= de + RECOUV
                m = in_poly(P2, pc.poly) & own & (de < pc.wb(P2) + 0.03) & (de >= -0.02)
                col, al, em = peint_biseau(pc, P2, de, sg)
                return col, al, em, m

            def fil(P, idx=idx, n=n, sg=sg):
                P2 = P[..., :2] + n * 0.04
                D = d_stack(P2, pc.segs)
                own = D[idx] <= D.min(0) + RECOUV
                m = in_poly(P2, pc.poly) & own
                col, al, em = peint_fil(pc, P2, D.min(0), sg)
                return col, al, em, m

            spec(groupe, f"{pc.nom}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil})
    u = pc.u
    pp_ = np.array((-u[1], u[0]))
    pa = np.array(pc.poly) - pc.O
    s_, t_ = pa @ u, pa @ pp_
    s0, s1, t0, t1 = s_.min() - 0.05, s_.max() + 0.05, t_.min() - 0.05, t_.max() + 0.05
    Pc = pc.O + u * (s0 + s1) / 2 + pp_ * (t0 + t1) / 2
    for sg in (1, -1):
        X = unit(np.array((u[0], u[1], sg * pc.k)))
        Y = sg * np.array((pp_[0], pp_[1], 0.0))
        Z = np.cross(X, Y)
        c = np.array((Pc[0], Pc[1], sg * float(pc.h(Pc)))) - Z * (TH / 2)

        def plat(P, sg=sg):
            P2 = P[..., :2]
            de = pc.dE(P2)
            m = in_poly(P2, pc.poly) & (de >= pc.wb(P2) - 0.03) & pc.masque_plat(P2, sg)
            col, al, em = peint_plat(pc, P2, de, sg)
            return col, al, em, m

        spec(groupe, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, ((s1 - s0) * math.sqrt(1 + pc.k ** 2), t1 - t0, TH), {"south": plat})


# ------------------------------------------------------------------ tours (pièces rondes : couronnes de pans de 0,3 px)
def rivets(col, x, y, pts, rr=0.15):
    for rx, ry in pts:
        d = np.hypot(x - rx, y - ry)
        col = np.where((d < rr)[..., None], BRASS["low"] * 0.8, col)
        col = np.where((d < rr * 0.72)[..., None], BRASS["base"], col)
        col = np.where((np.hypot(x - rx + 0.035, y - ry - 0.035) < rr * 0.35)[..., None], BRASS["hi"], col)
    return col


def _metal(M, xn, y, L, ex, k0=0.3, k1=0.55):
    k = np.clip(k0 + k1 * (1 - np.abs(xn) ** 1.4) + ex.get("clair", 0.0), 0, 1)
    col = lerp(M["low"], M["hi"], k[..., None]) * (1 + 0.035 * np.sin(y * 29.0 + xn * 2.0))[..., None]
    if ex.get("arete"):
        col = np.where(((y < 0.06) | (y > L - 0.06))[..., None], M["low"] * 0.85, col)
    if ex.get("riv"):
        col = rivets(col, ex["_x"], y, [(0.0, yy) for yy in ex["riv"]], ex.get("rr", 0.15))
    return col


def p_laiton(xn, t, y, L, ex):
    return _metal(BRASS, xn, y, L, ex)


def p_cuivre(xn, t, y, L, ex):
    return _metal(COPPER, xn, y, L, ex)


def p_acier(xn, t, y, L, ex):
    """Acier bruni clair (lisible dans la case), joints de tôle au bord des pans, demi-rivets de laiton sur les joints."""
    col = _metal(STEEL, xn, y, L, ex, k0=0.42, k1=0.45)
    cote = ex.get("cote", 0)                 # joints une arête sur deux : +1 seulement à droite du pan, -1 seulement à gauche
    if ex.get("joint"):
        j = (xn > 0.9) if cote > 0 else ((xn < -0.9) if cote < 0 else (np.abs(xn) > 0.93))
        col = np.where(j[..., None], STEEL["low"], col)
    if ex.get("rivb"):
        x, hw = ex["_x"], ex["_hw"]
        sx = np.abs(x) if cote == 0 else np.where(x * cote > 0, np.abs(x), -1e3)
        for yy in ex["rivb"]:
            d = np.hypot(sx - hw, y - yy)
            col = np.where((d < 0.16)[..., None], BRASS["low"] * 0.8, col)
            col = np.where((d < 0.115)[..., None], BRASS["base"], col)
            col = np.where((np.hypot(sx - hw + 0.03, y - yy - 0.03) < 0.05)[..., None], BRASS["hi"], col)
    if ex.get("spires"):
        f = (y / ex["spires"]) % 1.0
        col = np.where((f < 0.35)[..., None], STEEL["low"] * 1.1, col)
    return col


def p_cuir(xn, t, y, L, ex):
    """Cuir enroulé en spirale (bandes en biais, joint sombre), couture de laiton au milieu de chaque bande."""
    f = ((y / 0.55 + xn * 0.18) % 1.0)
    k = (1 - np.abs(xn)) * 0.35
    col = lerp(LEATHER["low"], LEATHER["hi"], (0.35 + k + 0.25 * np.clip(1 - np.abs(f - 0.5) * 2.2, 0, 1))[..., None])
    col = np.where((f < 0.12)[..., None], LEATHER["low"] * 0.7, col)
    st = (np.abs(f - 0.5) < 0.07) & (np.abs(xn) < 0.6) & ((np.floor((y + 0.05) / 0.12) % 2) == 0)
    return np.where(st[..., None], BRASS["base"], col)


def p_suie(xn, t, y, L, ex):
    return np.zeros(xn.shape + (3,), np.float32) + A(34, 28, 24)


PEINTRES = {"laiton": p_laiton, "cuivre": p_cuivre, "acier": p_acier, "cuir": p_cuir, "suie": p_suie}


def tuile_pan(nom, mat, L, w0, w1, ex):
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
    ex = dict(ex)
    ex["_x"], ex["_hw"] = x, hw - OVW
    col = PEINTRES[mat](xn, t, y, L, ex)
    return tuile(nom, *finir(col, None, None, mask))


def tour(g, nom, O, ax, ref, profil, n=12, phase=0.0):
    """profil = [(b0, r0, b1, r1, mat, ex), ...] le long de ax depuis O (modèle) ; une couronne de n pans par tronçon."""
    O, ax = np.asarray(O, float), unit(np.asarray(ax, float))
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    for i, (b0, r0, b1, r1, mat, ex) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        if L < 1e-4:
            continue
        tile = tuile_pan(f"{nom}{i}", mat, L, 2 * r0 * tn, 2 * r1 * tn, {k_: v_ for k_, v_ in ex.items() if k_ != "alt"})
        tile_b = tuile_pan(f"{nom}{i}b", mat, L, 2 * r0 * tn, 2 * r1 * tn, {**ex, **ex["alt"]}) if "alt" in ex else tile
        db, dr = (b1 - b0) / L, (r1 - r0) / L
        wm = max(2 * r0 * tn, 2 * r1 * tn) + 2 * OVW
        for k in range(n):
            th = phase + TAU * k / n
            e = math.cos(th) * ref + math.sin(th) * w3
            Pa, Pb = O + b0 * ax + r0 * e, O + b1 * ax + r1 * e
            Y = unit(Pb - Pa)
            N = -dr * ax + db * e
            X = np.cross(Y, N)
            CUBES.append({"groupe": g, "nom": f"{SFX[0]}_{nom}{i}_{k}", "c": (Pa + Pb) / 2 - N * TH / 2, "R": np.column_stack([X, Y, N]),
                          "half": np.array((wm / 2, L / 2 + OVL, TH / 2)), "faces": {"south": tile_b if k % 2 else tile}})


def barre(g, nom, p, q, r, mat, ref, n=8, cap="laiton"):
    """Barre à n pans fermée par deux chanfreins."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = float(np.linalg.norm(q - p))
    c = min(0.1, L / 4)
    tour(g, nom, p, q - p, ref, [(0.0, r * 0.55, c, r, cap, {"clair": 0.1}), (c, r, L - c, r, mat, {}),
                                 (L - c, r, L, r * 0.55, cap, {"clair": -0.05}), (L, r * 0.55, L, 0.0, cap, {}),
                                 (0.0, 0.0, 0.0, r * 0.55, cap, {})], n=n, phase=math.pi / n)


def tuyau(g, nom, pts, r, mat="cuivre", collier=0.4):
    """Tuyau le long d'une polyligne : un cylindre à 8 pans par tronçon, collier de laiton à chaque coude."""
    pts = [np.asarray(p, float) for p in pts]
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]
        Ln = float(np.linalg.norm(q - p))
        ref = (0, 0, 1) if abs(unit(q - p)[2]) < 0.9 else (1, 0, 0)
        tour(g, f"{nom}{i}_", p, q - p, ref, [(-0.08, r, Ln + 0.08, r, mat, {})], n=8, phase=math.pi / 8)
    for i in range(1, len(pts) - 1):
        d = unit(unit(pts[i + 1] - pts[i]) + unit(pts[i] - pts[i - 1]))
        ref = (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)
        tour(g, f"{nom}c{i}_", pts[i], d, ref,
             [(-0.17, r - 0.02, -0.17, collier, "laiton", {}), (-0.17, collier, 0.17, collier, "laiton", {"arete": True}),
              (0.17, collier, 0.17, r - 0.02, "laiton", {})], n=8, phase=math.pi / 8)


def boite(g, nom, c, X, Y, s, faces):
    X, Y, Z = repere(X, Y)
    CUBES.append({"groupe": g, "nom": f"{SFX[0]}_{nom}", "c": np.asarray(c, float), "R": np.column_stack([X, Y, Z]),
                  "half": np.asarray(s, float) / 2, "faces": dict(faces)})


# ------------------------------------------------------------------ tuiles peintes (cadrans, foyer, aiguilles, jet)
def disque(nom, n, fn, ss=4):
    """Tuile ronde n × n texels : fn(X, Y, R) en coordonnées -1..1 (sur-échantillonnée) -> col, em."""
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    X, Y = (xx + 0.5 - N / 2) / (N / 2), -(yy + 0.5 - N / 2) / (N / 2)
    R = np.hypot(X, Y)
    col, em = fn(X, Y, R)
    m = R < 0.985
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.LANCZOS)).astype(np.float32)
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((n, n), Image.LANCZOS)) > 110
    e = np.array(Image.fromarray(np.clip(em, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.NEAREST)).astype(np.float32)
    return tuile(nom, *finir(rgb, None, e, al))


def f_cadran(X, Y, R):
    """Cadran : lunette de laiton fine, verre ambre, 13 crans (-120° à +120°), zone rouge en haut de l'échelle (skin_epee_steampunk)."""
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


def t_unie(nom, W, H, c0, c1, bord=None):
    col = lerp(c0, c1, np.linspace(0, 1, H)[:, None, None] * np.ones((1, W, 1), np.float32))
    if bord is not None:
        col[0] = col[-1] = bord
        col[:, 0] = col[:, -1] = bord
    return tuile(nom, *finir(col, None, None, np.ones((H, W), bool)))


def t_aiguille():
    c = np.zeros((16, 4, 3), np.float32) + A(34, 28, 26)
    c[:6] = (190, 44, 30)
    c[:, :1] *= 1.5
    return tuile("aiguille", *finir(c, None, None, np.ones((16, 4), bool)))


def t_foyer(W=40, H=12):
    """Porte de foyer : cadre d'acier, 4 fentes rougeoyantes (_e vif), 4 rivets de laiton."""
    c = STEEL["base"] * np.ones((H, W, 3), np.float32)
    c[:2], c[:, :2] = STEEL["hi"], STEEL["hi"]
    c[-2:], c[:, -2:] = STEEL["low"], STEEL["low"]
    e = np.zeros((H, W, 3), np.float32)
    for x0 in (9, 15, 21, 27):
        c[3:H - 3, x0:x0 + 3] = (255, 150, 52)
        c[4:H - 4, x0 + 1] = (255, 214, 120)
        e[3:H - 3, x0:x0 + 3] = (225, 112, 28)
        e[4:H - 4, x0 + 1] = (225, 170, 70)
    for x, y in ((3, 3), (W - 5, 3), (3, H - 5), (W - 5, H - 5)):
        c[y:y + 2, x:x + 2] = BRASS["hi"]
    return tuile("foyer", *finir(c, None, e, np.ones((H, W), bool)))


def t_sangle(W=32, H=16):
    """Sangle de cuir : bords sombres, couture de laiton des deux côtés."""
    y = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
    x = np.ones((H, 1)) * np.arange(W)[None, :]
    col = lerp(LEATHER["base"], LEATHER["hi"], (0.5 - 0.4 * np.abs(y - 0.5))[..., None]) * np.ones((1, 1, 3), np.float32)
    col[(y < 0.1) | (y > 0.9)] = LEATHER["low"]
    st = ((np.abs(y - 0.2) < 0.05) | (np.abs(y - 0.8) < 0.05)) & ((x // 2) % 2 == 0)
    col[st] = BRASS["base"]
    return tuile("sangle", *finir(col, None, None, np.ones((H, W), bool)))


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
    TILES["jet"] = (out, None)
    TRANS.add("jet")
    return "jet"


R_CAD, R_CAD_D = 1.95, 0.86
disque("cadran", 80, f_cadran)
disque("cadran_d", 40, f_cadran)
t_unie("laiton_b", 16, 8, BRASS["hi"], BRASS["low"], bord=BRASS["low"])
t_unie("acier_b", 16, 8, STEEL["hi"], STEEL["low"], bord=STEEL["low"])
t_unie("cuir_b", 8, 8, LEATHER["base"], LEATHER["low"])
t_aiguille()
t_foyer()
t_sangle()
t_jet()

# ------------------------------------------------------------------ conception
GROUPES = []        # (clé, pivot, parent) ; nom affiché = clé avant « # »
N_F = 24
PH_F = math.pi / N_F
PHI0, CRAN = -100.0, 40.0           # aiguille : niveau 0 à -100° (depuis le haut), 40° par cran, 5 crans jusqu'au rouge
BY, BZ, BR = 5.0, -0.62, 1.0        # chaudière du dos (axe x)
Z_DIAL = 3.12
G_AV = 1.30                         # x du manomètre du dos
PX, PY_H = -4.35, 9.0               # tuyau montant et pied de la soupape


def dz_dos(r):
    """Hauteur z du dos bombé à la distance r de l'axe."""
    return float(np.interp(r, [0.0, 2.0, 4.5, 6.95, 7.45], [0.48, 0.50, 0.60, 0.72, 0.72]))


def grp(nom, pivot, parent):
    GROUPES.append((nom, np.asarray(pivot, float), parent))
    return nom


def aiguille(g, nom, C, z, L, w, th, sg):
    phi = math.radians(PHI0)
    dn = np.array((math.sin(phi), math.cos(phi), 0.0))
    boite(g, f"{nom}", np.asarray(C, float) + dn * (L / 2 - 0.25 * L) + np.array((0, 0, z)), np.cross(dn, (0, 0, 1)), dn,
          (w, L, th), {f: "aiguille" for f in SIX})
    boite(g, f"{nom}_moyeu", np.asarray(C, float) + np.array((0, 0, z + sg * 0.03)), (1, 0, 0), (0, 1, 0), (0.2 + w, 0.2 + w, th + 0.04),
          {f: "laiton_b" for f in SIX})


def build(sfx, parent):
    """Une copie du bouclier (mêmes tuiles)."""
    SFX[0] = sfx
    O = {}
    # --- roue dentée : 12 secteurs identiques posés par rotation
    gr = grp(f"roue_{sfx}", (0, 0, ZR), parent)
    for j in range(N_SECT):
        phi = DEMI + 2 * DEMI * j
        c, s = math.cos(phi), math.sin(phi)
        XF[0], XF[1] = np.array((0.0, 0.0, ZR)), np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
        NSUF[0] = f"_{j}"
        volume(SECT, gr)
    XF[0], XF[1] = np.zeros(3), np.eye(3)
    NSUF[0] = ""
    # --- face : cerclage de cuivre riveté, dôme d'acier en 24 pans rivetés, moyeu de laiton, manomètre ambre
    gf = grp(f"face_{sfx}", (0, 0, ZR), parent)
    tour(gf, "cerclage", (0, 0, 0), (0, 0, 1), (1, 0, 0),
         [(1.95, 7.25, 2.40, 7.25, "cuivre", {"clair": 0.05}), (2.40, 7.25, 2.40, 6.60, "cuivre", {"riv": [0.325], "clair": 0.1}),
          (2.40, 6.60, 2.25, 6.48, "cuivre", {"clair": -0.1})], n=N_F, phase=PH_F)
    tour(gf, "dome", (0, 0, 0), (0, 0, 1), (1, 0, 0),
         [(2.25, 6.48, 2.62, 4.6, "acier", {"joint": True, "rivb": [0.32], "cote": 1, "alt": {"joint": False, "cote": -1}}),
          (2.62, 4.6, 2.86, 2.5, "acier", {"joint": True, "rivb": [1.85], "clair": 0.05, "cote": 1, "alt": {"joint": False, "cote": -1}})], n=N_F, phase=PH_F)
    tour(gf, "moyeu", (0, 0, 0), (0, 0, 1), (1, 0, 0),
         [(2.80, 2.50, 3.25, 2.42, "laiton", {"arete": True}), (3.25, 2.42, 3.32, 2.05, "laiton", {"clair": 0.15}),
          (3.32, 2.05, 3.12, 1.88, "laiton", {"clair": -0.15})], n=N_F, phase=PH_F)
    boite(gf, "cadran", (0, 0, Z_DIAL - 0.06), (1, 0, 0), (0, 1, 0), (2 * R_CAD, 2 * R_CAD, 0.12), {"south": "cadran"})
    O["aig_av"] = ga = grp(f"aiguille_av_{sfx}", (0, 0, Z_DIAL + 0.07), gf)
    aiguille(ga, "aiguille_av", (0, 0, 0), Z_DIAL + 0.07, 1.6, 0.16, 0.06, 1)
    # --- dos bombé : bord d'acier, anneau de laiton riveté, tôles en 24 pans
    gd = grp(f"dos_{sfx}", (0, 0, 0.5), parent)
    tour(gd, "dos", (0, 0, 0), (0, 0, -1), (1, 0, 0),
         [(-1.02, 7.45, -0.72, 7.45, "acier", {}), (-0.72, 7.45, -0.72, 6.95, "laiton", {"riv": [0.25], "clair": 0.1}),
          (-0.72, 6.95, -0.60, 4.5, "acier", {"joint": True, "rivb": [0.3], "cote": 1, "alt": {"joint": False, "cote": -1}}),
          (-0.60, 4.5, -0.50, 2.0, "acier", {"joint": True, "cote": 1, "alt": {"joint": False, "cote": -1}}),
          (-0.50, 2.0, -0.48, 0.0, "acier", {})], n=N_F, phase=PH_F)
    # --- chaudière de cuivre couchée (fonds bombés de laiton), selles, porte de foyer, manomètre du dos
    gb = grp(f"chaudiere_{sfx}", (0, BY, BZ), gd)
    x0 = -3.75
    prof = [(0.0, 0.0, 0.14, 0.55, "laiton", {"clair": 0.2}), (0.14, 0.55, 0.42, 0.9, "laiton", {"clair": 0.05}),
            (0.42, 0.9, 0.5, 1.1, "laiton", {}), (0.5, 1.1, 0.78, 1.1, "laiton", {"arete": True}), (0.78, 1.1, 0.8, BR, "laiton", {}),
            (0.8, BR, 6.7, BR, "cuivre", {"riv": [0.18, 2.95, 5.72]}),
            (6.7, BR, 6.72, 1.1, "laiton", {}), (6.72, 1.1, 7.0, 1.1, "laiton", {"arete": True}), (7.0, 1.1, 7.08, 0.9, "laiton", {}),
            (7.08, 0.9, 7.36, 0.55, "laiton", {"clair": 0.05}), (7.36, 0.55, 7.5, 0.0, "laiton", {"clair": 0.2})]
    tour(gb, "chaudiere", (x0, BY, BZ), (1, 0, 0), (0, 0, -1), prof, n=12)
    for k, xs in enumerate((-2.4, 2.4)):
        zt = dz_dos(math.hypot(xs, BY)) + 0.05
        boite(gb, f"selle{k}", (xs, BY, (zt + BZ) / 2), (1, 0, 0), (0, 1, 0), (0.5, 1.3, zt - BZ), {f: "laiton_b" for f in SIX})
    O["foyer"] = gfo = grp(f"foyer_{sfx}", (-1.4, BY, BZ - BR), gb)
    boite(gfo, "foyer", (-1.4, BY, BZ - BR - 0.06), (1, 0, 0), (0, 1, 0), (1.8, 0.5, 0.12),
          {"north": "foyer", "east": "acier_b", "west": "acier_b", "up": "acier_b", "down": "acier_b"})
    O["lum"] = grp(f"ctrl_lumiere#{sfx}", (-1.4, BY, BZ - BR), gfo)
    zg = BZ - BR + 0.05
    tour(gb, "tige_m", (G_AV, BY, zg), (0, 0, -1), (0, 1, 0), [(0.0, 0.22, 0.47, 0.22, "laiton", {})], n=8, phase=math.pi / 8)
    ZG0 = zg - 0.45
    tour(gb, "boitier_m", (G_AV, BY, ZG0), (0, 0, -1), (0, 1, 0),
         [(0.0, 0.22, 0.0, 0.95, "laiton", {}), (0.0, 0.95, 0.3, 0.95, "laiton", {"arete": True}),
          (0.3, 0.95, 0.36, 0.8, "laiton", {"clair": 0.15})], n=16)
    boite(gb, "cadran_d", (G_AV, BY, ZG0 - 0.30 + 0.06), (1, 0, 0), (0, 1, 0), (2 * R_CAD_D, 2 * R_CAD_D, 0.12), {"north": "cadran_d@m"})
    O["aig_dos"] = gad = grp(f"aiguille_dos_{sfx}", (G_AV, BY, ZG0 - 0.35), gb)
    aiguille(gad, "aiguille_dos", (G_AV, BY, 0), ZG0 - 0.35, 0.7, 0.1, 0.05, -1)
    # --- tuyau de la chaudière à la soupape, volant de vanne, soupape dressée au-dessus du bord
    gt = grp(f"tuyau_{sfx}", (PX, BY, BZ), gd)
    tuyau(gt, "tuyau", [(x0 + 0.15, BY, BZ), (PX, BY, BZ), (PX, PY_H + 0.1, BZ)], 0.3)
    VY = 6.7
    tour(gt, "v_tige", (PX, VY, BZ - 0.25), (0, 0, -1), (0, 1, 0), [(0.0, 0.11, 0.7, 0.11, "acier", {"clair": 0.2})], n=8)
    tour(gt, "v_embase", (PX, VY, BZ - 0.22), (0, 0, -1), (0, 1, 0),
         [(0.0, 0.2, 0.18, 0.2, "laiton", {"arete": True}), (0.18, 0.2, 0.2, 0.0, "laiton", {})], n=8)
    VC = np.array((PX, VY, BZ - 0.95))
    O["volant"] = gv = grp(f"volant_{sfx}", VC, gt)
    RV = 0.62
    for k in range(8):
        a_ = TAU * (k + 0.5) / 8
        p = VC + np.array((math.cos(a_), math.sin(a_), 0)) * RV
        boite(gv, f"jante{k}", p, (-math.sin(a_), math.cos(a_), 0), (math.cos(a_), math.sin(a_), 0),
              (2 * RV * math.tan(math.pi / 8) + 0.1, 0.16, 0.16), {f: "acier_b" for f in SIX})
    for k in range(2):
        a_ = math.pi / 4 + math.pi / 2 * k
        boite(gv, f"rayon{k}", VC, (math.cos(a_), math.sin(a_), 0), (-math.sin(a_), math.cos(a_), 0), (2 * RV - 0.1, 0.11, 0.11),
              {f: "acier_b" for f in SIX})
    boite(gv, "v_moyeu", VC, (1, 0, 0), (0, 1, 0), (0.26, 0.26, 0.2), {f: "laiton_b" for f in SIX})
    S0 = np.array((PX, PY_H, BZ))
    tour(gt, "soupape", S0, (0, 1, 0), (0, 0, 1),
         [(0.0, 0.3, 0.0, 0.5, "laiton", {}), (0.0, 0.5, 0.18, 0.5, "laiton", {"arete": True}), (0.18, 0.5, 0.22, 0.36, "laiton", {}),
          (0.22, 0.36, 0.86, 0.36, "acier", {"spires": 0.13, "clair": 0.15}), (0.86, 0.36, 0.86, 0.5, "laiton", {"clair": -0.1})], n=12)
    O["clapet"] = gc = grp(f"clapet_{sfx}", S0 + np.array((0, 0.86, 0)), gt)
    tour(gc, "clapet", S0 + np.array((0, 0.9, 0)), (0, 1, 0), (0, 0, 1),
         [(0.0, 0.3, 0.0, 0.52, "laiton", {}), (0.0, 0.52, 0.16, 0.52, "laiton", {"arete": True}), (0.16, 0.52, 0.26, 0.3, "laiton", {"clair": 0.1}),
          (0.26, 0.3, 0.3, 0.14, "laiton", {"clair": 0.2}), (0.3, 0.14, 0.31, 0.0, "suie", {})], n=12)
    # jet de vapeur caché dans le clapet (déplié par event_hit seul), point de white_smoke au-dessus
    JP = S0 + np.array((0, 0.96, 0))
    JL, JW = 4.5, 2.4
    f = F_GEO / KJ
    O["jet"] = gj = grp(f"trans_jet_{sfx}", JP, gc)
    for k in range(3):
        an = math.radians(60 * k)
        Yp = np.array((math.cos(an), 0.0, math.sin(an)))
        boite(gj, f"jet{k}", JP + np.array((0, JL / 2 * f, 0)), (0, 1, 0), Yp, (JL * f, JW * f, 0.15 * f * 2), {"south": "jet", "north": "jet"})
    O["alpha"] = grp(f"ctrl_alpha#{sfx}", JP, gj)
    em = grp(f"emit_mc_white_smoke#{sfx}", S0 + np.array((0, 1.5, 0)), gt)
    O["emit"] = grp(f"ctrl_emit#{sfx}", S0 + np.array((0, 1.5, 0)), em)
    # --- poignée de cuir cousu entre deux montants de laiton (place de la poignée vanilla : x -1..1, y -3..3, z -5..1)
    gp = grp(f"poignee_{sfx}", (0, 0, -2.0), gd)
    for k, yp in enumerate((3.15, -3.15)):
        barre(gp, f"montant{k}", (0, yp, dz_dos(abs(yp)) + 0.1), (0, yp, -4.75), 0.42, "laiton", (1, 0, 0))
    tour(gp, "poignee", (0, -3.0, -4.2), (0, 1, 0), (0, 0, 1), [(0.0, 0.58, 6.0, 0.58, "cuir", {})], n=12, phase=math.pi / 12)
    for k, yp in enumerate((-2.85, 2.85)):
        barre(gp, f"virole{k}", (0, yp - 0.22, -4.2), (0, yp + 0.22, -4.2), 0.7, "laiton", (0, 0, 1), n=12)
    # --- sangle d'avant-bras rivetée, boucle de laiton
    YS = -5.2
    for k, xs in enumerate((-3.85, 3.85)):
        zr = dz_dos(math.hypot(xs, YS))
        tour(gp, f"attache{k}", (xs, YS, zr + 0.05), (0, 0, -1), (0, 1, 0),
             [(0.0, 0.5, 0.38, 0.5, "laiton", {"arete": True}), (0.38, 0.5, 0.42, 0.25, "laiton", {"clair": 0.15}),
              (0.42, 0.25, 0.44, 0.0, "laiton", {"clair": 0.25})], n=8, phase=math.pi / 8)
    zs = dz_dos(6.5) - 0.3
    pts = [(-3.85, YS, zs), (-2.3, YS, -0.75), (2.3, YS, -0.75), (3.85, YS, zs)]
    for k in range(3):
        p, q = np.array(pts[k]), np.array(pts[k + 1])
        d = unit(q - p)
        boite(gp, f"sangle{k}", (p + q) / 2, d, (0, 1, 0), (float(np.linalg.norm(q - p)) + 0.12, 1.0, 0.3),
              {"north": "sangle", "south": "cuir_b", "up": "cuir_b", "down": "cuir_b"})
    for k, (dx, w, h) in enumerate(((-0.28, 0.12, 1.3), (0.28, 0.12, 1.3))):
        boite(gp, f"boucle{k}", (-1.2 + dx, YS, -0.92), (1, 0, 0), (0, 1, 0), (w, h, 0.16), {f: "laiton_b" for f in SIX})
    for k, sy in enumerate((-0.6, 0.6)):
        boite(gp, f"boucle_b{k}", (-1.2, YS + sy, -0.92), (1, 0, 0), (0, 1, 0), (0.68, 0.12, 0.16), {f: "laiton_b" for f in SIX})
    boite(gp, "ardillon", (-1.2, YS, -0.95), (1, 0, 0), (0, 1, 0), (0.6, 0.08, 0.08), {f: "acier_b" for f in SIX})
    return O


racine_r = grp(objet.etape("repos", "bouclier"), (0, 0, 0), None)
OR_ = build("r", racine_r)
racine_b = grp(objet.etape("bloque", "bouclier"), (0, 0, 0), None)
pose = grp("pose_bloque", (0, 0, 0), racine_b)
OB_ = build("b", pose)


# ------------------------------------------------------------------ atlas
def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    print("aire des tuiles", sum(a.shape[0] * a.shape[1] for a, _ in TILES.values()), "max", max(a.shape[:2] for a, _ in TILES.values()))
    sky = np.zeros(TEX, int)          # rangement en ligne d'horizon
    ymax = 0
    for n, (im, ime) in sorted(TILES.items(), key=lambda it: (-it[1][0].shape[0], -it[1][0].shape[1])):
        h, w = im.shape[:2]
        best = None
        for x0 in range(0, TEX - w):
            yb = int(sky[x0:x0 + w + 1].max())
            if best is None or yb < best[0]:
                best = (yb, x0)
        y, x = best
        assert y + h <= TEX - 6, f"atlas plein ({n}, y = {y})"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None:
            tex_e[y:y + h, x:x + w] = ime
        sky[x:x + w + 1] = y + h + 1
        ymax = max(ymax, y + h)
    assert tex[TEX - 2, TEX - 2, 3] == 0
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    zone = np.zeros(semi.shape, bool)
    for n in TRANS:
        u0, v0, u1, v1 = UV[n]
        zone[v0:v1, u0:u1] = True
    assert not (semi & ~zone).any(), "semi-transparence hors des tuiles trans_"
    assert set(np.unique(tex_e[..., 3])) <= {0, 255}
    print(f"atlas : {len(TILES)} tuiles, rangées jusqu'à y = {ymax}")
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


def uv_de(t):
    if t.endswith("@m"):
        u0, v0, u1, v1 = UV[t[:-2]]
        return [u1, v0, u0, v1]
    return list(UV[t])


elements, groups = [], {}
for nom, piv, parent in GROUPES:
    assert nom not in groups and len(nom.split("#")[0]) <= 64, nom
    groups[nom] = {"origin": [round(float(v), 4) for v in piv], "uuid": nuid(), "ids": [], "parent": parent, "rotation": [0, 0, 0]}
_noms = set()
for cb in CUBES:
    c, h = cb["c"], cb["half"]
    R = cb["R"]
    assert abs(np.linalg.det(R) - 1) < 1e-6, cb["nom"]
    assert cb["nom"] not in _noms, cb["nom"]
    _noms.add(cb["nom"])
    rot = euler(R)
    e = {"name": cb["nom"], "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in c - h],
         "to": [round(float(v), 4) for v in c + h], "origin": [round(float(v), 4) for v in c], "box_uv": False,
         "faces": {f: {"uv": uv_de(cb["faces"][f]) if f in cb["faces"] else CLEAR, "texture": 0} for f in SIX}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[cb["groupe"]]["ids"].append(e["uuid"])


def bone_node(name):
    g = groups[name]
    return {"name": name.split("#")[0], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node(racine_r), bone_node(racine_b)]

# ------------------------------------------------------------------ réglages Display (item/shield.json et item/shield_blocking.json du jar 26.1.2)
VAN = {"thirdperson_righthand": ((0, 90, 0), (10, 6, -4), 1), "thirdperson_lefthand": ((0, 90, 0), (10, 6, 12), 1),
       "firstperson_righthand": ((0, 180, 5), (-10, 1.75, -10), 1.25), "firstperson_lefthand": ((0, 180, 5), (10, 0, -10), 1.25),
       "gui": ((15, -25, -5), (2, GUI_TY, 0), GUI), "fixed": ((0, 180, 0), (-4.5, 4.5, -5), 0.55), "on_shelf": ((0, 0, 0), (11, 18.5, 8.7), 1.4),
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
ERR_POSE = 0.0
for c in VAN_BLOQUE:
    gauche = c.endswith("lefthand")
    Hm = np.linalg.inv(disp(VAN[c], gauche)) @ disp(VAN_BLOQUE[c], gauche)
    Rm = Hm[:3, :3]
    assert np.allclose(Rm @ Rm.T, np.eye(3), atol=1e-6)
    CORR[c] = (euler(Rm), Hm[:3, 3])
    e, t = CORR[c]
    for p in ((0, 0, 1.5), (9, 0, 2), (-9, 0, 1), (0, 3, -5), (0, 0.5, 3.3), (-4.3, 10.3, -0.6)):
        a = disp(VAN[c], gauche) @ np.append(rotm(*e) @ np.array(p, float) + t, 1)
        b = disp(VAN_BLOQUE[c], gauche) @ np.append(np.array(p, float), 1)
        ERR_POSE = max(ERR_POSE, float(np.linalg.norm(a[:3] - b[:3])) * 16)
        assert np.allclose(a, b, atol=1e-6), c
    print(f"parade {c:23s} rotation {np.round(e, 2).tolist()} position {np.round(t, 3).tolist()}")
print(f"pose de blocage : écart max (matrices) {ERR_POSE:.5f} px")


def molang_combo(i, chan):
    v = {c: (CORR[c][0][i] if chan == "rot" else CORR[c][1][i]) for c in CORR}
    f = lambda x: f"({x:.3f})"
    return (f"q.in_first_person*(q.hand*{f(v['firstperson_lefthand'])}+(1-q.hand)*{f(v['firstperson_righthand'])})"
            f"+(1-q.in_first_person)*(q.hand*{f(v['thirdperson_lefthand'])}+(1-q.hand)*{f(v['thirdperson_righthand'])})")


# ------------------------------------------------------------------ animations (objet vivant, guide 14)
def s_(v):
    return v if isinstance(v, str) else f"{v + 0.0:.4f}".rstrip("0").rstrip(".")


def kf(ch, t, x, y=None, z=None, interp="linear"):
    y = x if y is None else y
    z = x if z is None else z
    return {"channel": ch, "data_points": [{"x": s_(x), "y": s_(y), "z": s_(z)}], "time": round(t, 4), "interpolation": interp}


def anim(name, length, loop="once"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 100,
            "selected": name == "item_idle", "animators": {}}


def piste(an, g, keys):
    u = groups[g]["uuid"]
    if u in an["animators"]:
        an["animators"][u]["keyframes"] += keys
    else:
        an["animators"][u] = {"name": g.split("#")[0], "type": "bone", "keyframes": keys}


def chk(e):
    assert len(e) <= 512 and e.count(";") <= 16, (len(e), e)
    return e


def echant(L, fps):
    n = max(6, int(round(L * fps)))
    return [round(L * i / n, 4) for i in range(n + 1)]


def step(tau, rise=0.05, over=0.28):
    """Échelon de servo : montée courte, dépassement puis rappel amorti."""
    if tau <= 0:
        return 0.0
    v = sm(tau, 0.0, rise)
    if tau > rise * 0.6:
        x = tau - rise * 0.6
        v += over * math.sin(TAU * x / 0.15) * math.exp(-x / 0.045)
    return v


def aig(t, lvl):
    return kf("rotation", t, 0, 0, -CRAN * lvl)            # monter = sens horaire vu de +Z


def lum(t, x):
    return kf("position", t, x, 0, 0)


def deux_aiguilles(an, O, f, ts):
    for g in (O["aig_av"], O["aig_dos"]):
        piste(an, g, [aig(t, f(t)) for t in ts])


rot_m = [chk(molang_combo(i, "rot")) for i in range(3)]
pos_m = [chk(molang_combo(i, "pos")) for i in range(3)]


def garde(an, L):
    piste(an, pose, [kf("rotation", 0, *rot_m), kf("rotation", L, *rot_m), kf("position", 0, *pos_m), kf("position", L, *pos_m)])


# item_idle (24 s) : garde (recette 2) ; deux cycles : cinq crans de pression, la soupape tremble puis se soulève (white_smoke)
L_IDLE = 24.0
TICKS = [1.5, 3.0, 4.5, 6.0, 7.5, 13.5, 15.0, 16.5, 18.0, 19.5]
PUFFS = [10.0, 22.0]
TW = 1.2


def tremble(t):
    return sum(bump(t, tp - TW, tp - TW * 0.75, tp - 0.03, tp) for tp in PUFFS)


def idle_level(t):
    v = sum(step(t - ti) for ti in TICKS) - sum(5 * step(t - tp - 0.03, rise=0.12, over=0.08) for tp in PUFFS)
    return v + 0.1 * tremble(t) * math.sin(TAU * 19 * t)


def leve_idle(t):
    return sum(bump(t, tp - 0.02, tp + 0.04, tp + 0.4, tp + 0.6) for tp in PUFFS)


idle = anim("item_idle", L_IDLE, "loop")
garde(idle, L_IDLE)
ts = echant(L_IDLE, 20)
for O in (OR_, OB_):
    deux_aiguilles(idle, O, idle_level, ts)
    piste(idle, O["clapet"], [kf("position", t, 0, 0.13 * leve_idle(t) + 0.025 * tremble(t) * math.sin(TAU * 23 * t), 0) for t in ts])
    piste(idle, O["lum"],
          [lum(t, -0.45 + 0.1 * idle_level(t) + 0.08 * math.sin(TAU * 6 * t / L_IDLE)) for t in ts])
    piste(idle, O["emit"], [lum(t, -1 + 4 * leve_idle(t)) for t in ts])

# item_use (1,2 s) : garde, aiguilles au rouge qui tremblent, soupape qui frémit, foyer vif ; vapeur au coup paré
L_USE = 1.2
use = anim("item_use", L_USE, "loop")
garde(use, L_USE)
tu = echant(L_USE, 30)
for O in (OR_, OB_):
    deux_aiguilles(use, O, lambda t: 4.85 + 0.12 * math.sin(TAU * 4 * t / L_USE) + 0.05 * math.sin(TAU * 11 * t / L_USE), tu)
    piste(use, O["clapet"], [kf("position", 0, 0, chk("0.03*math.sin(q.life_time*1500)+0.14*q.hit_by_entity"), 0)])
    piste(use, O["lum"], [lum(0, chk("0.35+0.15*math.sin(q.life_time*500)+0.5*q.hit_by_entity"))])
    piste(use, O["emit"], [lum(0, chk("-1+6*q.hit_by_entity"))])

# event_select (0,8 s) : la vanne s'ouvre d'un quart de tour (deux crans), tour d'essai des aiguilles, le foyer s'allume
L_SEL = 0.8
sel = anim("event_select", L_SEL)
tsel = echant(L_SEL, 40)
for O in (OR_, OB_):
    piste(sel, O["volant"], [kf("rotation", t, 0, 0, -45 * (step(t - 0.04, 0.06, 0.15) + step(t - 0.14, 0.06, 0.15))) for t in tsel])
    deux_aiguilles(sel, O, lambda t: sum(step(t - ti) for ti in (0.22, 0.3, 0.38)) - 3 * step(t - 0.56, rise=0.1, over=0.1), tsel)
    piste(sel, O["lum"], [lum(t, -1.0 + 1.0 * sm(t, 0.2, 0.3) + 0.5 * bump(t, 0.28, 0.34, 0.4, 0.7)) for t in tsel])

# event_hit (0,9 s) : décharge : jet qui jaillit de la soupape et monte, vapeur, aiguilles qui chutent ; le seul son
L_HIT = 0.9
hit = anim("event_hit", L_HIT)
th_ = echant(L_HIT, 40)


def jet_scale(t):
    w = sm(t, 0.03, 0.1) * (1 + 0.25 * sm(t, 0.1, 0.4)) / 1.25 * (1 - sm(t, 0.5, 0.64))
    k = (1 + (KJ - 1) * w) / F_GEO
    return k


for O in (OR_, OB_):
    piste(hit, O["jet"], [kf("scale", t, jet_scale(t)) for t in th_] +
          [kf("position", t, 0, 1.2 * sm(t, 0.08, 0.62) * (1 - sm(t, 0.64, 0.68)), 0) for t in th_])
    piste(hit, O["alpha"], [lum(t, -sm(t, 0.3, 0.62) * (1 - sm(t, 0.66, 0.7))) for t in th_])
    piste(hit, O["emit"], [lum(t, 5 * bump(t, 0.03, 0.06, 0.32, 0.5)) for t in th_])
    piste(hit, O["clapet"], [kf("position", t, 0, 0.16 * bump(t, 0.0, 0.03, 0.3, 0.45), 0) for t in th_])
    deux_aiguilles(hit, O, lambda t: -3 * (step(t - 0.03, rise=0.06, over=0.1) - step(t - 0.45, rise=0.2, over=0.08)), th_)

ANIMS = [idle, use, sel, hit]

# ------------------------------------------------------------------ écriture
assert len(elements) <= 8192, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = objet.modele(NOM, "bouclier", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son  # noqa: E402
limiter_sons(model)
# Un seul son, au coup qui touche (event_hit), à 0,04 s ; rien à event_use_start ni event_enter_* (recette 3).
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "block.fire.extinguish")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def coins(ok=lambda e: True):
    P = []
    for e in elements:
        if not ok(e):
            continue
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
print(f"boîte {P.min(0).round(2)} .. {P.max(0).round(2)} ; roue : {2 * H_R:.2f} px, biseau {float(SECT.wb(np.zeros((1, 2)))[0]):.2f} px")
