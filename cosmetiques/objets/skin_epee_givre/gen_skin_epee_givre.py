"""Épée de givre : skin d'objet (guide 14) pour toutes les épées du joueur, ensemble Givre (thème Éléments). Design original.
Écrit skin_epee_givre.png, skin_epee_givre_e.png et .build/skin_epee_givre_brut.bbmodel à côté de ce script.

Design validé en jeu (2026-11-05, version allongée, captures 23.12.24–35) et gardé : lame de cristal translucide au cœur
cyan lumineux, garde d'argent froid à flocons et six cristaux en éventail, fusée de cuir bleu nuit entre viroles d'argent,
pommeau de glace. Même repère, même longueur (26,7 px sur la diagonale, lame de 19,2 px depuis la garde), même Display
(item/handheld, `gui` 0,85). Version précédente : .build/gen_avant.py.

Vrai volume (retour en jeu du 2026-11-08 14 h 22 : « c'est des couches » ; recette .claude/references/objets/volume-3d.md,
prototype skin_epee_orage validé à 15 h 05) :
- lame à section **hexagonale** amincie (1,44 px au talon -> 0,52 à la pointe, 0,20 au fil), biseaux à pente unique de 36°
  (tan 0,72 : table d'environ 1 px tout du long, losange vers la pointe), un cube incliné par fil droit et par face, un plat
  incliné par face, faces échantillonnées texel par texel et découpées par l'alpha ;
- glace translucide **sans faces internes visibles** : peau `trans_` mince (biseaux, plats, fils) autour d'une **âme opaque**
  de même forme, 0,2 px en retrait (plans parallèles décalés), qui porte le cœur cyan (calque _e) et les facettes sombres.
  L'âme cache la moitié arrière de la peau ; seule une bande de 0,27 px le long des fils et le bout de la pointe restent
  vraiment transparents (glace claire au bord, comme un vrai cristal). Une lame `trans_` creuse laisserait voir ses faces
  arrière à travers les faces avant ; un cristal tout opaque perdrait la transparence validée de l'ensemble ;
- garde : moyeu octogonal en tour (8 pans biseautés), **flocons en relief** (trois bras en barres à section losange, branches,
  gemme hexagonale à pointe au calque _e) au lieu d'une plaque peinte, six **cristaux hexagonaux** à pointe (tours de 6 pans)
  au lieu de barres octogonales en deux carrés ; pommeau de glace hexagonal à pointe ; viroles en bagues biseautées à 8 pans ;
  fusée octogonale gardée (« le manche est bien »).
Objet vivant, sobre : event_select (0,6 s) : la glace pousse (lame puis cristaux de la garde, échelle depuis leur base, en
cascade ; chaque groupe n'est déplié que par cette animation). Pas de son (une sélection de barre d'objets est fréquente).
Fonctions avancées : trans_, calque _e, scale animé, event_select. À juger en jeu : la glace sur âme opaque avec et sans
shader, event_select et scale sur un objet, lecture de la lame par la tranche.
Une seule étape : groupe racine `repos`.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image, ImageDraw

NOM = "skin_epee_givre"
TEX = 512
TAU = 2 * math.pi

# Repère de l'objet (bloc 0..16) : lame en diagonale vers le haut à droite, plat vers +Z (face vue dans l'inventaire).
A_ = np.array((1.0, 1.0, 0.0)) / math.sqrt(2)     # a : le long de la lame (vers la pointe)
W_ = np.array((-1.0, 1.0, 0.0)) / math.sqrt(2)    # b : en travers, dans le plan de l'image
T_ = np.array((0.0, 0.0, 1.0))                     # z : épaisseur (A × W)
KL, KP, KG = 1.32, 1.22, 1.12       # allongement validé en jeu (lame, poignée ; garde, largeurs)
HUB_A = 2.45


def AA(a):
    return HUB_A + (a - HUB_A) * (KL if a > HUB_A else KP)


A_MIN, A_MAX = AA(-3.69), AA(17.0)
P0 = np.array((8.0, 8.0, 8.0)) - A_ * (A_MIN + A_MAX) / 2    # épée centrée dans le bloc (inchangé)
A_BASE, A_SH, A_TIP = AA(2.55), AA(13.6), AA(17.0)
HW0, HW1 = 1.25 * KG, 0.80 * KG
TIP_W = 0.25 * KG
TIP = (A_TIP, TIP_W)
HUB_R, HUB_T = 0.85 * KG, 0.75 * KG


def Wp(a, b=0.0, z=0.0):
    return P0 + A_ * a + W_ * b + T_ * z


def Wv(a, b=0.0, z=0.0):
    return A_ * a + W_ * b + T_ * z


def lerp(a, b, k):
    return a + (b - a) * k


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


C = lambda *c: np.array(c, np.float32)
G_DEEP, G_BODY, G_PALE, G_LIGHT = C(30, 96, 168), C(92, 186, 232), C(168, 226, 250), C(214, 244, 255)
BLANC = C(244, 253, 255)
LUEUR = C(150, 226, 255)
ARG_L, ARG_M, ARG_D = C(236, 244, 250), C(166, 186, 206), C(74, 90, 116)

# ------------------------------------------------------------------ dessin de la lame (plan a, b ; px)
U_FIL = [(A_BASE, HW0), (A_SH, HW1), TIP]
L_FIL = [(A_BASE, -HW0), (A_SH, -HW1), TIP]
LAME = U_FIL + [(A_SH, -HW1), (A_BASE, -HW0)]


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


def b_centre(a):
    """Axe de la lame : b = 0 jusqu'à l'épaulement, puis vers la pointe décalée (biseau)."""
    return TIP_W * np.clip((np.asarray(a, float) - A_SH) / (A_TIP - A_SH), 0, 1)


def demi_largeur(a):
    a = np.asarray(a, float)
    k1 = np.clip((a - A_BASE) / (A_SH - A_BASE), 0, 1)
    k2 = np.clip((a - A_SH) / (A_TIP - A_SH), 0, 1)
    return np.where(a < A_SH, lerp(HW0, HW1, k1), HW1 * (1 - k2))


# ------------------------------------------------------------------ vrai volume (.claude/references/objets/volume-3d.md)
Z_E = 0.10                       # demi-épaisseur au fil (0,20 px)
T_BIS = 0.72                     # pente unique des biseaux (36°)
AL = math.atan(T_BIS)
TH = 0.3                         # épaisseur des cubes de surface
DF = 16.0                        # texels par px
DELTA = 0.20                     # retrait de l'âme sous la peau (normal aux faces)
ZC_MIN = 0.05                    # demi-épaisseur de l'âme à son bord
RECOUV_PEAU, RECOUV_AME = 0.0, 0.08    # pas de recouvrement sur la peau translucide (double alpha = coutures)


def h_lame(a):
    """Demi-épaisseur du plat : 0,72 au talon (1,44 px) -> 0,26 à la pointe (0,52 px), amincissement linéaire."""
    return 0.72 + (0.26 - 0.72) * np.clip((np.asarray(a, float) - A_BASE) / (A_TIP - A_BASE), 0, 1)


def wb_lame(a):
    return (h_lame(a) - Z_E) / T_BIS


D_OFF = (ZC_MIN - Z_E) / T_BIS + DELTA / math.sin(AL)          # bord de l'âme, depuis le fil (0,27 px)
D_C_EXTRA = DELTA * (1 / math.cos(AL) - 1) / T_BIS             # l'arête biseau/plat de l'âme est un peu plus loin


def subdiv(pts):
    out = []
    for i in range(len(pts) - 1):
        out.append((np.array(pts[i], float), np.array(pts[i + 1], float), True, True))
    return out


SEGS = subdiv(U_FIL) + subdiv(L_FIL)   # fils droits : un cube par fil droit (même plan, pas de couture sur la peau)


def d_stack(P, segs=SEGS):
    out = []
    for p, q, *_ in segs:
        ab = q - p
        t = np.clip(((P - p) @ ab) / (ab @ ab), 0, 1)
        out.append(np.linalg.norm(P - (p + t[..., None] * ab), axis=-1))
    return np.stack(out)


def dE(P):
    return d_stack(P).min(0)


def proprietaire(D, idx):
    """Chaque point appartient au fil le plus proche (indice le plus petit en cas d'égalité) : partition exacte."""
    am = np.argmin(D, axis=0)
    return am == idx


# --- motifs dans le plan de la lame (fissures, givre), une image par face (sg)
PL_A0, PL_A1, PL_B0, PL_B1, PL_D = A_BASE - 0.5, A_TIP + 0.5, -1.9, 1.9, 40.0


def _plan_motifs(sg, seed):
    r = np.random.default_rng(seed)
    Wd, Hd = int((PL_A1 - PL_A0) * PL_D), int((PL_B1 - PL_B0) * PL_D)
    fis = Image.new("L", (Wd, Hd), 0)
    d = ImageDraw.Draw(fis)

    def px(a, b):
        return ((a - PL_A0) * PL_D, (PL_B1 - b) * PL_D)
    for k in range(7):
        a = lerp(A_BASE + 1.0, A_TIP - 2.5, (k + r.uniform(0.1, 0.9)) / 7)
        b = r.uniform(-0.7, 0.7)
        pl = [(a, b)]
        ang = r.uniform(0.3, 1.2) * r.choice([-1, 1])
        for j in range(4):
            ang += r.uniform(-0.7, 0.7)
            ln = r.uniform(0.25, 0.55)
            pl.append((pl[-1][0] + math.cos(ang) * ln * 0.8, pl[-1][1] + math.sin(ang) * ln * 0.6))
            if j == 1:
                b0 = pl[-1]
                a2 = ang + r.choice([-1, 1]) * r.uniform(0.9, 1.4)
                d.line([px(*b0), px(b0[0] + math.cos(a2) * 0.3, b0[1] + math.sin(a2) * 0.2)], fill=255, width=2)
        d.line([px(*p) for p in pl], fill=255, width=3)
    nz = Image.fromarray((r.random((10, 60)) * 255).astype(np.uint8), "L").resize((Wd, Hd), Image.BICUBIC)
    return np.array(fis) > 127, np.array(nz, np.float32) / 255


MOTIFS = {sg: _plan_motifs(sg, 31 + (sg > 0)) for sg in (1, -1)}


def motif(P2, sg):
    fis, nz = MOTIFS[sg]
    i = np.clip(((PL_B1 - P2[..., 1]) * PL_D).astype(int), 0, fis.shape[0] - 1)
    j = np.clip(((P2[..., 0] - PL_A0) * PL_D).astype(int), 0, fis.shape[1] - 1)
    return fis[i, j], nz[i, j]


def chevrons(P2):
    """Paliers de taille obliques (miroir haut/bas : chevrons), comme la lame validée."""
    db = np.abs(P2[..., 1] - b_centre(P2[..., 0]))
    return (np.floor((P2[..., 0] * 0.75 + 2.2 * db) / 1.35) % 2) * 2 - 1


# --- peintures : (couleur, alpha, émissif) ; alpha None = opaque
def u_of(P2):
    return np.clip((P2[..., 0] - A_BASE) / (A_TIP - A_BASE), 0, 1)


def peau_plat(P2, d, sg):
    u = u_of(P2)[..., None]
    g = chevrons(P2)[..., None]
    col = lerp(C(104, 192, 236), C(168, 226, 250), u) * (1 + 0.05 * g)
    al = 142 + 30 * u[..., 0] + 6 * g[..., 0]
    fis, nz = motif(P2, sg)
    frost = (u[..., 0] < 0.035 + 0.05 * nz) & (nz > 0.35)
    arete = d < wb_lame(P2[..., 0]) + 0.07
    for m, c, a in ((fis, BLANC, 215), (frost, C(236, 248, 255), 222), (arete, BLANC, 212)):
        col = np.where(m[..., None], c, col)
        al = np.where(m, a, al)
    return col, al, None


def peau_biseau(P2, d, sg):
    f = d / wb_lame(P2[..., 0])
    u = u_of(P2)
    g = chevrons(P2)
    col = lerp(C(196, 238, 255), C(140, 208, 242), np.clip(f, 0, 1)[..., None]) * (1 + 0.04 * g)[..., None]
    al = 170 + 20 * u + 8 * g
    fis, nz = motif(P2, sg)
    frost = (u < 0.035 + 0.05 * nz) & (nz > 0.35)
    for m, c, a in ((fis, BLANC, 215), (frost, C(236, 248, 255), 222), (f > 0.88, BLANC, 212), (f < 0.14, BLANC, 225)):
        col = np.where(m[..., None], c, col)
        al = np.where(m, a, al)
    return col, al, None


def peau_fil(P2, d, sg):
    return np.zeros(P2.shape[:-1] + (3,), np.float32) + BLANC, np.full(P2.shape[:-1], 225.0), None


def ame_plat(P2, d, sg):
    a, b = P2[..., 0], P2[..., 1]
    u = u_of(P2)
    k1 = np.clip(u / 0.22, 0, 1)[..., None]
    k2 = np.clip((u - 0.22) / 0.78, 0, 1)[..., None]
    col = lerp(lerp(G_DEEP, G_BODY, k1), G_PALE, k2 * 0.7)
    db = np.abs(b - b_centre(a))
    hw = np.maximum(demi_largeur(a), 0.3)
    col = col * (0.62 + 0.25 * np.clip(db / hw, 0, 1))[..., None]          # plus sombre au cœur de la masse
    col = col * (1 + 0.07 * chevrons(P2))[..., None]
    em = np.zeros(col.shape, np.float32)
    cw = 0.24 * (1 - 0.5 * u)
    halo = db < cw + 0.13
    col[halo] = lerp(col[halo], C(150, 226, 250), 0.55)
    coeur = db < cw
    col[coeur] = lerp(C(200, 248, 255), C(120, 214, 246), np.clip(db[coeur] / cw[coeur], 0, 1)[..., None])
    em[coeur] = LUEUR
    fis, _ = motif(P2, sg)
    col[fis & ~coeur] = lerp(col[fis & ~coeur], BLANC, 0.35)
    col[d < wb_lame(a) + D_C_EXTRA + 0.06] = G_DEEP * 0.8                  # arête sombre : la facette se lit
    return col, None, em


def ame_biseau(P2, d, sg):
    wb = wb_lame(P2[..., 0]) + D_C_EXTRA
    f = np.clip((d - D_OFF) / np.maximum(wb - D_OFF, 0.05), 0, 1)[..., None]
    col = lerp(G_PALE, G_BODY, f * 0.8) * (1 + 0.05 * chevrons(P2))[..., None]
    return col, None, None


def ame_fil(P2, d, sg):
    return np.zeros(P2.shape[:-1] + (3,), np.float32) + G_LIGHT, None, None


# ------------------------------------------------------------------ cubes différés (la tuile est résolue après l'atlas)
TILES = {}                 # nom -> (rgba, rgba_e)
TRANS_TILES = set()
CUBES = []                 # dict(groupe, nom, c (monde), R (colonnes monde), half, faces {face: tuile | None})
SIX = ("north", "south", "east", "west", "up", "down")


def tuile(nom, rgba, e=None, trans=False):
    assert nom not in TILES, nom
    TILES[nom] = (rgba, e)
    if trans:
        TRANS_TILES.add(nom)
    return nom


def finir(col, al, em, masque):
    """alpha : None = opaque (0/255 par le masque), sinon 1..254 dans le masque (peau trans_)."""
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
    """Cube du plan (a, b, z) ; peintures : {face: fn(P (H, W, 3) en plan) -> (col, alpha, em, masque)}."""
    X, Y, Z = repere(X, Y)
    c = np.asarray(c, float)
    faces = {}
    for f, fn in peintures.items():
        P = points_face(c, X, Y, Z, s, f)
        col, al, em, m = fn(P)
        if m.any():
            faces[f] = tuile(f"{nom}_{f}", *finir(col, al, em, m), trans=trans)
    R = np.column_stack([Wv(*X), Wv(*Y), Wv(*Z)])
    CUBES.append({"groupe": groupe, "nom": nom, "c": Wp(*c), "R": R, "half": np.asarray(s, float) / 2, "faces": faces})


def volume(groupe, ame):
    """Peau (ame=False, trans_) ou âme opaque (ame=True, plans parallèles décalés de DELTA vers l'intérieur)."""
    rec = RECOUV_AME if ame else RECOUV_PEAU
    pb, pf, pp = (ame_biseau, ame_fil, ame_plat) if ame else (peau_biseau, peau_fil, peau_plat)
    for idx, (p, q, v0, v1) in enumerate(SEGS):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        if not in_poly(np.array([(p + q) / 2 + n * 0.05]), LAME)[0]:
            n = -n
        am = float((p[0] + q[0]) / 2)
        wb = float(wb_lame(min(am, A_TIP)))
        wmax = float(wb_lame(min(p[0], q[0])))
        e0 = wmax * 1.6 if v0 else 0.04
        e1 = wmax * 1.6 if v1 else 0.04
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        d0 = D_OFF if ame else 0.0
        z0 = ZC_MIN if ame else Z_E
        sy = (wmax + (D_C_EXTRA if ame else 0.0) - d0 + 0.1) / math.cos(AL)
        for sg in (1, -1):
            Y = np.array((n[0] * math.cos(AL), n[1] * math.cos(AL), sg * math.sin(AL)))
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0] + n[0] * d0, mid[1] + n[1] * d0, sg * z0)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(P, idx=idx, sg=sg):
                P2 = P[..., :2]
                D = d_stack(P2)
                de = D.min(0)
                lim = wb_lame(P2[..., 0]) + (D_C_EXTRA if ame else 0.0) + 0.03
                own = (D[idx] <= de + rec) if rec > 0 else proprietaire(D, idx)
                m = in_poly(P2, LAME) & own & (de < lim) & (de >= d0 - 0.02)
                col, al, em = pb(P2, de, sg)
                return col, al, em, m

            def fil(P, idx=idx, n=n, sg=sg):
                P2 = P[..., :2] + n * 0.04
                D = d_stack(P2)
                own = (D[idx] <= D.min(0) + rec) if rec > 0 else proprietaire(D, idx)
                m = in_poly(P2, LAME) & own
                col, al, em = pf(P2, D.min(0), sg)
                return col, al, em, m

            spec(groupe, f"{'ame' if ame else 'peau'}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil},
                 trans=not ame)
    # plats : une plaque par face, inclinée pour suivre l'amincissement
    pa = np.array(LAME)
    a0, a1, b0, b1 = pa[:, 0].min() - 0.05, pa[:, 0].max() + 0.05, pa[:, 1].min() - 0.05, pa[:, 1].max() + 0.05
    sl = float((h_lame(a1) - h_lame(a0)) / (a1 - a0))
    ac, bc = (a0 + a1) / 2, (b0 + b1) / 2
    dz = DELTA if ame else 0.0
    for sg in (1, -1):
        X = unit(np.array((1.0, 0.0, sg * sl)))
        Y = np.array((0.0, float(sg), 0.0))
        Z = np.cross(X, Y)
        c = np.array((ac, bc, sg * (float(h_lame(ac)) - dz))) - Z * (TH / 2)

        def plat(P, sg=sg):
            P2 = P[..., :2]
            de = dE(P2)
            m = in_poly(P2, LAME) & (de >= wb_lame(P2[..., 0]) + (D_C_EXTRA if ame else 0.0) - 0.03)
            col, al, em = pp(P2, de, sg)
            return col, al, em, m

        spec(groupe, f"{'ame' if ame else 'peau'}_plat{'pm'[sg < 0]}", c, X, Y, ((a1 - a0) * math.sqrt(1 + sl * sl), b1 - b0, TH),
             {"south": plat}, trans=not ame)


# ------------------------------------------------------------------ tours (pièces rondes : couronnes de pans, skin_masse_orage)
OVL, OVW = 0.04, 0.03


def p_argent(xn, t, ex):
    k = np.clip(0.45 + 0.3 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + ex.get("pointe", 0.0) * t, 0, 1)
    col = lerp(ARG_D, ARG_L, (k ** 1.2)[..., None]) * (1 + 0.03 * np.sin(t * 37 + xn * 3))[..., None]
    col = np.where((np.abs(xn) > 0.86)[..., None], np.minimum(col * 1.14 + 10, 255), col)        # arête claire
    if ex.get("givre"):
        col = np.where(((t > 0.82) & (np.abs(xn) < 0.75))[..., None], lerp(col, BLANC, 0.6), col)
    return col, None


def p_glace(xn, t, ex):
    k = np.clip(0.35 + 0.35 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + 0.25 * t, 0, 1)
    col = lerp(C(40, 110, 176), G_LIGHT, (k ** 1.1)[..., None])
    col = np.where((np.abs(xn) > 0.84)[..., None], BLANC, col)
    em = np.zeros(col.shape, np.float32)
    if ex.get("e"):
        ln = np.abs(xn) < 0.16
        col[ln] = lerp(col[ln], C(200, 248, 255), 0.7)
        em[ln] = LUEUR
    return col, em


def p_gemme(xn, t, ex):
    k = np.clip(0.4 + 0.4 * (1 - np.abs(xn)) + 0.2 * t + ex.get("clair", 0.0), 0, 1)
    col = lerp(C(40, 130, 210), C(170, 236, 255), k[..., None])
    return col, np.clip(col * 0.8, 0, 200)


PEINTRES = {"argent": p_argent, "glace": p_glace, "gemme": p_gemme}


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
    col, em = PEINTRES[mat](xn, t, ex)
    return tuile(nom, *finir(col, None, em, mask))


def tour(g, nom, O, ax, ref, profil, n=8, phase=0.0):
    """profil = [(b0, r0, b1, r1, [(mat, ex), ...]), ...] le long de ax (rayon = apothème) ; matières alternées par pan.
    Chaque pan : plaque de TH px, face extérieure (south) sur la surface, autres faces transparentes."""
    O, ax = np.asarray(O, float), unit(ax)
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    for i, (b0, r0, b1, r1, mats) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        tiles = [tuile_pan(f"{nom}{i}{'abcd'[j]}", m, L, 2 * r0 * tn, 2 * r1 * tn, ex) for j, (m, ex) in enumerate(mats)]
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


def t_disque(nom, n, Ra, N=48):
    """Couvercle en polygone régulier (apothème Ra) : argent givré, anneau clair, découpé par l'alpha."""
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
    """Cuir bleu nuit enroulé en biais, couture d'argent (inchangé)."""
    r = np.random.default_rng(5)
    yy, xx = np.mgrid[0:H, 0:W]
    f = ((xx + yy * 0.9) / 14.0) % 1.0
    c = lerp(C(44, 56, 104), C(16, 20, 44), f[..., None])
    c = np.where((f > 0.86)[..., None], C(8, 10, 24), c)
    c *= r.uniform(0.95, 1.05, (H, W))[..., None]
    for x in range(3, W - 4, 10):
        c[6:10, x:x + 5] = (176, 196, 220)
    return tuile("cuir", *finir(c, None, None, np.ones((H, W), bool)))


def barre(g, nom, p, q, r, Rang, faces):
    """Barre de section carrée 2r tournée de Rang degrés autour de son axe (45 : section en losange)."""
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
    """Octogone régulier : 4 plaques à 0, 45, 90, 135° (fusée validée), bouts cachés (transparents)."""
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


# ------------------------------------------------------------------ conception
GROUPES = []        # (nom, pivot, parent)


def grp(nom, pivot, parent):
    GROUPES.append((nom, np.asarray(pivot, float), parent))
    return nom


def bague(b0, b1, ra, ro, rb, c=0.12, mat="argent"):
    return [(b0, ra, b0 + c, ro, [(mat, {"clair": 0.15})]), (b0 + c, ro, b1 - c, ro, [(mat, {}), (mat, {"clair": -0.08})]),
            (b1 - c, ro, b1, rb, [(mat, {"clair": -0.12})])]


ARGENT_ALT = [("argent", {"clair": 0.1, "pointe": 0.2, "givre": True}), ("argent", {"clair": -0.1, "pointe": 0.25, "givre": True})]
GLACE_ALT = [("glace", {"clair": 0.12, "e": True}), ("glace", {"clair": -0.1})]
# cristaux de la garde : (côté, angle depuis la verticale vers l'avant (deg), inclinaison vers l'extérieur (deg), longueur, rayon)
CRIST = [(1, 24, 0, 3.1, 0.36), (1, 58, 14, 2.2, 0.30), (1, -14, -12, 1.6, 0.27),
         (-1, 24, 0, 3.0, 0.36), (-1, 58, -14, 2.2, 0.30), (-1, -14, 12, 1.6, 0.27)]


def conception():
    racine = grp(objet.etape("repos", "epee"), (8, 8, 8), None)
    epee = grp("epee", P0, racine)
    # --- manche : fusée octogonale gardée, viroles en bagues biseautées, pommeau de glace hexagonal à pointe
    manche = grp("manche", Wp(AA(-1.0)), epee)
    t_cuir()
    bar8(manche, "fusee", Wp(AA(-2.4)), Wp(AA(1.9)), 0.5 * KG, "cuir")
    for nm, a0, a1 in (("virole_ar", AA(-2.8), AA(-2.2)), ("virole_av", AA(0.85), AA(1.25))):
        tour(manche, nm, Wp(0), A_, W_, bague(a0, a1, 0.58, 0.73, 0.58), n=8, phase=math.pi / 8)
    disque(manche, "virole_fond", Wp(AA(-2.8)), -A_, W_, 8, 0.6, t_disque("disque_virole", 8, 0.6, 24))
    pom = grp("pommeau", Wp(AA(-2.8)), manche)
    a0 = AA(-2.8)
    Lp = a0 - A_MIN
    tour(pom, "pommeau", Wp(a0), -A_, W_, [(0.0, 0.46, 0.12, 0.56, GLACE_ALT), (0.12, 0.56, Lp * 0.5, 0.56, GLACE_ALT),
                                          (Lp * 0.5, 0.56, Lp, 0.0, GLACE_ALT)], n=6)
    # --- garde : moyeu octogonal (axe z), couvercles, flocons en relief, six cristaux hexagonaux en éventail
    garde = grp("garde", Wp(HUB_A), epee)
    tour(garde, "moyeu", Wp(HUB_A), T_, A_, bague(-HUB_T, HUB_T, 0.80, HUB_R, 0.80, c=0.14), n=8, phase=math.pi / 8)
    td = t_disque("disque_moyeu", 8, 0.80)
    sec = 0.24
    bras_t = t_unie("bras", 32, 8, ARG_L, ARG_M, ligne=BLANC)
    cap_t = t_unie("bras_bout", 8, 8, BLANC, ARG_M)
    fb = {f: bras_t for f in ("south", "north", "up", "down")}
    fb.update(east=cap_t, west=cap_t)
    for s in (1, -1):
        cs = "e" if s > 0 else "i"
        fl = grp(f"flocon_{cs}", Wp(HUB_A, 0, s * HUB_T), garde)
        disque(fl, f"couvercle_{cs}", Wp(HUB_A, 0, s * HUB_T), T_ * s, A_, 8, 0.80, td)
        zc = s * (HUB_T + 0.04)
        Rf = 1.38
        for k in range(3):
            th = math.radians(90 + 60 * k + 15)
            e = math.cos(th) * A_ + math.sin(th) * W_
            barre(fl, f"bras_{cs}{k}", Wp(HUB_A, 0, zc) - e * Rf, Wp(HUB_A, 0, zc) + e * Rf, sec / 2, 45, fb)
        for k in range(6):
            th = math.radians(90 + 60 * k + 15)
            e = math.cos(th) * A_ + math.sin(th) * W_
            for fr, ln in ((0.52, 0.42), (0.80, 0.30)):
                base = Wp(HUB_A, 0, zc + s * 0.01) + e * Rf * fr
                for sg in (-1, 1):
                    t2 = th + sg * math.radians(55)
                    e2 = math.cos(t2) * A_ + math.sin(t2) * W_
                    barre(fl, f"branche_{cs}{k}{'pm'[sg < 0]}{int(fr * 10)}", base - e2 * 0.05, base + e2 * ln, 0.085, 45, fb)
        tour(fl, f"gemme_{cs}", Wp(HUB_A, 0, s * HUB_T), T_ * s, A_,
             [(0.0, 0.40, 0.22, 0.40, [("gemme", {"clair": 0.1}), ("gemme", {"clair": -0.1})]),
              (0.22, 0.40, 0.50, 0.0, [("gemme", {"clair": 0.2}), ("gemme", {})])], n=6)
    for i, (sw, ang, tilt, L, r) in enumerate(CRIST):
        th, tl = math.radians(ang), math.radians(tilt)
        d = unit(W_ * sw * math.cos(th) + A_ * math.sin(th) + T_ * math.tan(tl))
        base = Wp(HUB_A) + d * 0.35 * KG
        L, r = L * KG, r * KG
        cg = grp(f"cristal_{'h' if sw > 0 else 'b'}{i % 3 + 1}", base, garde)
        tl_ = min(L * 0.45, r * 1.9)
        tour(cg, cg, base, d, T_, [(0.0, r * 0.8, 0.2, r, ARGENT_ALT), (0.2, r, L - tl_, r, ARGENT_ALT),
                                    (L - tl_, r, L, 0.0, ARGENT_ALT)], n=6, phase=math.pi / 6)
    # --- lame : peau de glace trans_ + âme opaque (cœur cyan) ; pivot au talon (elle pousse depuis la garde)
    lame = grp("lame", Wp(A_BASE), garde)
    peau = grp("trans_lame", Wp(A_BASE), lame)
    coeur = grp("coeur", Wp(A_BASE), lame)
    volume(coeur, True)
    volume(peau, False)
    return racine


RACINE = conception()

# ------------------------------------------------------------------ atlas
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


# ------------------------------------------------------------------ émission
def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def euler(R):
    """Angles (X, Y, Z) tels que R = Rz Ry Rx ; blocage de cardan (Y = ±90°) : Z = 0, tout l'angle sur X ; vérifié."""
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
    groups[nom] = {"origin": [round(float(v), 4) for v in piv], "uuid": nuid(), "ids": [], "parent": parent}
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
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node(RACINE)]


# ------------------------------------------------------------------ animation : event_select, la glace pousse
def s_(v):
    return f"{v + 0.0:.4f}".rstrip("0").rstrip(".")


def kf(ch, t, x, interp="linear"):
    return {"channel": ch, "data_points": [{"x": s_(x), "y": s_(x), "z": s_(x)}], "time": round(t, 4), "interpolation": interp}


def pousse(t0, dur, over=1.07):
    """Échelle depuis la base : 0,05 -> dépassement -> 1, échantillonnée à 20 images/s."""
    keys = [kf("scale", 0.0, 0.05)]
    if t0 > 0:
        keys.append(kf("scale", t0, 0.05))
    for k in range(1, 11):
        u = k / 10
        v = 0.05 + (over - 0.05) * (1 - (1 - u / 0.7) ** 2) if u <= 0.7 else lerp(over, 1.0, (u - 0.7) / 0.3)
        keys.append(kf("scale", t0 + dur * u, v))
    return keys


L_SEL = 0.6
sel = {"uuid": nuid(), "name": "event_select", "loop": "once", "override": False, "length": L_SEL, "snapping": 20,
       "selected": True, "animators": {}}
sel["animators"][groups["lame"]["uuid"]] = {"name": "lame", "type": "bone", "keyframes": pousse(0.0, 0.32)}
ordre = ["cristal_h1", "cristal_b1", "cristal_h2", "cristal_b2", "cristal_h3", "cristal_b3"]
for i, nm in enumerate(ordre):
    sel["animators"][groups[nm]["uuid"]] = {"name": nm, "type": "bone", "keyframes": pousse(0.14 + 0.045 * i, 0.22, 1.12)}
ANIMS = [sel]

# ------------------------------------------------------------------ écriture
assert 150 <= len(elements) <= 1500, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
AFFICHAGE = objet.affichage("epee", gui={"scale": [0.85, 0.85, 0.85]})   # 26,7 px en diagonale : ramenée à la case
model = objet.modele(NOM, "epee", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


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


P = coins()
D_ = np.array((1, 1, 0)) / math.sqrt(2)
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur sur la diagonale {float((P @ D_).max() - (P @ D_).min()):.1f} px ; boîte {P.min(0).round(2)} .. {P.max(0).round(2)}")
print(f"âme : bord à {D_OFF:.3f} px du fil, arête +{D_C_EXTRA:.3f} ; biseau {float(wb_lame(A_BASE)):.2f} -> {float(wb_lame(A_TIP)):.2f} px")
