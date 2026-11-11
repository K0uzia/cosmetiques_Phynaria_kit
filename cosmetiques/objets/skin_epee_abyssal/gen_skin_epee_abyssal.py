"""Croc de l'Abysse : skin d'objet (guide 14) pour toutes les épées du joueur, ensemble Abyssal (thème Démoniaque). Design original.
Écrit skin_epee_abyssal.png, skin_epee_abyssal_e.png et .build/skin_epee_abyssal_brut.bbmodel à côté de ce script.

Design (inchangé depuis la première version, reprise d'une des `lames_abyssales`) : sabre courbe d'os noir à un seul
tranchant, fil vert acide sur le côté convexe, lame qui s'amincit vers la pointe, éperon d'os sur le dos près du talon ;
garde en griffes recourbées (grande griffe vers la main, contre-griffe vers le dos, griffe de côté), poignée de cuir
pourpre-noir à clous d'os, griffe au pommeau. Langage : .claude/styles/abyssal.md (os charbon à reflet violacé, vert acide
réservé au fil, aux veines et aux pointes).

Vrai volume (2026-11-08, recette .claude/references/objets/volume-3d.md, prototype skin_epee_orage validé en jeu) : la
première version était une plaque découpée + âme + filet (« des couches » par la tranche). Maintenant :
- lame = volume fermé construit dans le repère de la corde (s le long de la corde, r en travers) : un plat incliné par face
  (demi-épaisseur 0,80 px au talon -> 0,27 à la pointe, plan exact), un biseau à pente unique (tan 0,62, 32° : lame large)
  par tronçon du fil et par face, de 0,10 px au fil jusqu'au plat ; le dos est un mur plein (pas de biseau : un seul
  tranchant), découpé par l'alpha à la hauteur de la surface ; couleurs portées par les faces : fil vert vif + _e, bande
  verte, halo sombre, biseau d'os sombre, arête violacée, plat d'os plus clair marbré, veines vertes qui montent du fil ;
- gouttière creusée le long du dos (parois + fond) : la lueur verte acide y est couchée (filet vif + _e sur un fond noir) ;
- garde et poignée en tours de pans (skin_masse_orage) : griffes = tronçons coniques à 8 pans le long d'une courbe, pointe
  verte + _e ; poignée de cuir à 12 pans à bandes en spirale, bagues et pommeau d'os, clous d'os en tiges à bouts coniques ;
  collet d'os en boîte au talon ; éperon = petite griffe plantée dans le dos.
Repère (catégorie objets, Recette) : construit dans le plan (a, b) (a le long de la poignée), axe pommeau -> pointe mesuré sur
la géométrie puis posé sur la diagonale du bloc, pointe en haut à droite vue de +Z, centré dans le bloc ; Display vanilla de
item/handheld, gui 0,76. Une étape : groupe racine `repos`.

Objet vivant (guide 14), animations inchangées :
- item_idle (6 s) : les griffes respirent à peine (±2,5°), le fil vert « souffle » (ctrl_lumiere, ±0,35) ;
- event_select (0,7 s) : la lame sort de la garde (échelle du groupe fer, seul dépliage), les griffes se déplient, le fil
  s'allume en dernier ;
- event_swing (0,45 s) : les griffes serrent la poignée pendant le coup, le fil s'avive ;
- event_hit (0,6 s) : éclat du fil (+1,6) et frisson des griffes ; un seul son (block.sculk.break) à 0,04 s (une clé à 0,0 s
  est muette au premier coup : diagnostic F5), aucun ailleurs.
Pas de particules. Fonctions avancées : calque _e (fil, veines, gouttière, pointes des griffes), ctrl_lumiere (non simulé),
scale animé (event_select), animations d'objet (non simulées par l'aperçu). À juger en jeu : lecture du volume par la tranche
et dans la case, ctrl_lumiere et event_hit sur un objet, le son.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

AVEC_E = True
NOM = "skin_epee_abyssal"
TEX = 512
TAU = 2 * math.pi
DF = 16.0                       # texels par px sur les faces des volumes
DENS = 16.0                     # texels par px sur les pans des tours
TH = 0.3                        # épaisseur des cubes (biseaux, plats, murs, pans)
RECOUV = 0.08                   # recouvrement des faces voisines
OVL, OVW = 0.04, 0.03           # recouvrement des pans (en long, en travers)

# palette (.claude/styles/abyssal.md)
OS_CLAIR = np.array((58, 50, 72), np.float32)
OS_BASE = np.array((30, 25, 40), np.float32)
OS_SOMBRE = np.array((14, 10, 20), np.float32)
ARETE = np.array((126, 92, 170), np.float32)
REFLET = np.array((98, 68, 126), np.float32)
AURA = np.array((22, 66, 40), np.float32)
VEIN = np.array((96, 200, 44), np.float32)
VCORE = np.array((150, 244, 70), np.float32)
FIL = np.array((190, 255, 96), np.float32)
E_COL = np.array((82, 211, 53), np.float32)        # calque _e du fil (valeur de la lame portée validée)
E_VEINE = np.array((60, 160, 40), np.float32)


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


# ------------------------------------------------------------------ lame : courbe dans le plan (a, b) (première version)
BL_START = (3.0, -0.32)
BL_LEN = 19.0
BL_A0, BL_A1 = -31.0, -7.0      # direction au talon et près de la pointe (degrés)
KW = 1.12


def blade_hs(t):
    """Demi-largeur côté dos."""
    return KW * 1.15 * (1 + 0.14 * math.sin(math.pi * min(t * 1.6, 1))) * max(0.0, 1 - t ** 1.7) ** 0.85 + 0.03


def blade_he(t):
    """Demi-largeur côté tranchant."""
    return KW * 1.5 * (1 + 0.10 * math.sin(math.pi * min(t * 1.4, 1))) * max(0.0, 1 - t ** 3.0) ** 0.8 + 0.03


def blade_curve(n=480):
    pts, angs = [], []
    x, y = BL_START
    ds = BL_LEN / n
    for i in range(n + 1):
        t = i / n
        ang = math.radians(lerp(BL_A0, BL_A1, t))
        pts.append((x, y))
        angs.append(ang)
        x += math.cos(ang) * ds
        y += math.sin(ang) * ds
    return np.array(pts), np.array(angs)


CURVE_PTS, CURVE_ANG = blade_curve()


def blade_at(t):
    i = min(int(round(t * (len(CURVE_PTS) - 1))), len(CURVE_PTS) - 1)
    a = CURVE_ANG[i]
    return CURVE_PTS[i], np.array((-math.sin(a), math.cos(a))), np.array((math.cos(a), math.sin(a)))


# repère de la corde : s le long de la corde (talon -> pointe), r en travers (vers le dos)
CH = CURVE_PTS[-1] - CURVE_PTS[0]
S_TIP = float(np.linalg.norm(CH))
CA = math.atan2(CH[1], CH[0])
DC = np.array((math.cos(CA), math.sin(CA)))
NC = np.array((-math.sin(CA), math.cos(CA)))
O_B = np.array(BL_START, float)


def vers_corde(p):
    q = np.asarray(p, float) - O_B
    return np.array((q @ DC, q @ NC))


def vers_plan(s, r):
    return O_B + s * DC + r * NC


def vers_plan_v(s, r):
    return s * DC + r * NC


TS = np.linspace(0, 1, 26)
_p0, _n0, _d0 = blade_at(0.0)
E_PTS = [vers_corde(_p0 - _n0 * blade_he(0) - _d0 * 0.3)] + [vers_corde(blade_at(t)[0] - blade_at(t)[1] * blade_he(t)) for t in TS[:-1]]
S_PTS = [vers_corde(_p0 + _n0 * blade_hs(0) - _d0 * 0.3)] + [vers_corde(blade_at(t)[0] + blade_at(t)[1] * blade_hs(t)) for t in TS[:-1]]
TIP = vers_corde(CURVE_PTS[-1])
E_PTS.append(TIP)
S_PTS.append(TIP)
LAME = [tuple(p) for p in E_PTS] + [tuple(p) for p in S_PTS[::-1][1:]]


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


def d_stack(P, segs):
    out = []
    for p, q, *_ in segs:
        ab = q - p
        t = np.clip(((P - p) @ ab) / (ab @ ab), 0, 1)
        out.append(np.linalg.norm(P - (p + t[..., None] * ab), axis=-1))
    return np.stack(out)


# ------------------------------------------------------------------ section : plat incliné, biseau à pente unique côté fil, dos plein
Z_E = 0.10                      # demi-épaisseur au fil
H0, H1 = 0.80, 0.27             # demi-épaisseur du plat au talon (s = 0) et à la pointe (s = S_TIP), linéaire (plan exact)
T_BIS = 0.62                    # pente unique des biseaux (32°) : lame large, biseau de 1,13 px au talon -> 0,27 à la pointe


def h_lame(s):
    return H0 + (H1 - H0) * np.asarray(s, float) / S_TIP


def wb_lame(s):
    return (h_lame(s) - Z_E) / T_BIS


SEGS_E = [(np.array(E_PTS[k], float), np.array(E_PTS[k + 1], float), k == 0, k == len(E_PTS) - 2) for k in range(len(E_PTS) - 1)]


def dE(P):
    return d_stack(P, SEGS_E).min(0)


def surf(P):
    d, h, wb = dE(P), h_lame(P[..., 0]), wb_lame(P[..., 0])
    return np.where(d < wb, Z_E + (h - Z_E) * np.clip(d / wb, 0, 1), h)


# gouttière le long du dos : centre à OFF px sous le dos, pointue aux deux bouts
OFF = 0.64
G_T = np.linspace(0.07, 0.60, 9)
GW = [0.09, 0.20, 0.26, 0.27, 0.27, 0.26, 0.23, 0.17, 0.08]
SLIT = [tuple(vers_corde(blade_at(t)[0] + blade_at(t)[1] * (blade_hs(t) - OFF))) for t in G_T]
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
    poly = [tuple(p) for p in cotes[1]] + [tuple(p) for p in cotes[-1][::-1]]
    return cotes, poly


GOUT_COTES, GOUT = _gouttiere()


def in_gout(P):
    return in_poly(P, GOUT)


def d_gout(P):
    return d_poly(P, GOUT + [GOUT[0]])


def d_axe_gout(P):
    return d_poly(P, SLIT)


# marge gouttière / biseau (contrôle) : le creux doit rester dans le plat
_g = np.array(GOUT)
_marge = float((dE(_g) - wb_lame(_g[:, 0])).min())
assert _marge > 0.12, f"gouttière trop près du biseau ({_marge:.2f} px)"


# veines : partent du fil et montent vers le dos (trois maîtresses + une branche chacune), en coordonnées de corde
def _veines():
    out = []
    for t0, L0, dt, br in ((0.10, 1.35, 0.05, 1), (0.27, 1.15, -0.04, -1), (0.45, 0.95, 0.05, 1)):
        pts = []
        for j in range(6):
            k = j / 5
            p, n, _ = blade_at(t0 + dt * k)
            w = p + n * (-blade_he(t0 + dt * k) - 0.05 + L0 * k * blade_he(t0) / 1.6) + n * 0.07 * math.sin(j * 2.4)
            pts.append(vers_corde(w))
        out.append([tuple(q) for q in pts])
        a = np.array(pts[3])
        d = unit(np.array(pts[4]) - a)
        ang = 0.5 * br
        rot = np.array((d[0] * math.cos(ang) - d[1] * math.sin(ang), d[0] * math.sin(ang) + d[1] * math.cos(ang)))
        out.append([tuple(a), tuple(a + rot * 0.3 + np.array((0.25 * br, 0.0)))])
    return out


VEINES = _veines()


def veines(P, col, em):
    d = np.min(np.stack([d_poly(P, v) for v in VEINES]), axis=0)
    m1, m0 = d < 0.13, d < 0.06
    col[m1] = VEIN
    col[m0] = VCORE
    em[m0] = E_VEINE
    return col, em


def bruit(P, seed=0.0):
    s, r = P[..., 0], P[..., 1]
    return (0.5 * np.sin(s * 1.7 + r * 2.3 + seed) + 0.3 * np.sin(s * 4.3 - r * 3.1 + 1.0 + seed) + 0.2 * np.sin(s * 9.1 + r * 7.7 + seed))


# --- peintures des faces du volume de la lame (P en coordonnées de corde)
def peint_biseau(P, de):
    f = de / wb_lame(P[..., 0])
    nz = bruit(P, 1.0)[..., None]
    col = lerp(OS_BASE, OS_SOMBRE, np.clip((f[..., None] - 0.5) / 0.45, 0, 1) * 0.7) + nz * 5 + np.zeros(P.shape[:-1] + (3,), np.float32)
    au = (f >= 0.34) & (f < 0.56)
    col[au] = lerp(AURA, col[au], np.clip((f[au, None] - 0.34) / 0.22, 0, 1))
    col[(f >= 0.16) & (f < 0.34)] = VEIN
    em = np.zeros(col.shape, np.float32)
    col, em = veines(P, col, em)
    col[f >= 0.92] = ARETE * 0.9                                 # arête violacée entre le biseau sombre et le plat
    col[f < 0.16] = FIL
    em[f < 0.18] = E_COL
    return col, em


def peint_fil(P):
    col = np.zeros(P.shape[:-1] + (3,), np.float32) + FIL
    return col, np.zeros_like(col) + E_COL


def peint_plat(P, de):
    wb = wb_lame(P[..., 0])
    nz = bruit(P, 2.0)
    col = lerp(OS_BASE, OS_CLAIR, np.clip(0.45 + 0.6 * nz, 0, 1)[..., None] * 0.85)
    col = col * (1 + 0.04 * np.sin(P[..., 0] * 7.0 + nz * 3))[..., None]       # lignes de croissance de l'os
    em = np.zeros(col.shape, np.float32)
    col, em = veines(P, col, em)
    col[de < wb + 0.05] = ARETE
    dg = d_gout(P)
    col[dg < 0.06] = ARETE                                        # lèvre de la gouttière
    col[(dg >= 0.06) & (dg < 0.11) & ~in_gout(P)] = OS_SOMBRE
    return col, em


def peint_dos(P):
    """Mur du dos : reflet violacé au milieu, sombre vers les arêtes, liseré violacé en haut."""
    P2 = P[..., :2]
    k = np.abs(P[..., 2]) / np.maximum(surf(P2), 0.05)
    col = lerp(REFLET, OS_BASE, np.clip(k[..., None] * 1.2, 0, 1)) + bruit(P2, 3.0)[..., None] * 5
    col[k > 0.86] = ARETE
    return col, np.zeros(col.shape, np.float32)


# ------------------------------------------------------------------ échantillonnage des faces (recette volume-3d)
SPECS = []
TILES = {}          # nom -> (rgba, rgba_e | None)


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
    on = masque & (em.max(axis=-1) > 0)
    rgba_e = np.zeros_like(rgba)
    rgba_e[..., :3] = np.clip(em, 0, 225).astype(np.uint8)
    rgba_e[..., 3] = on * 255
    rgba_e[~on] = 0
    return rgba, (rgba_e if on.any() else None)


def spec(groupe, nom, c, X, Y, s, peintures):
    X, Y, Z = repere(X, Y)
    faces = {}
    for f, fn in peintures.items():
        P = points_face(np.asarray(c, float), X, Y, Z, s, f)
        col, em, m = fn(P)
        if m.any():
            nomt = f"{nom}_{f}"
            TILES[nomt] = finir(col, em, m)
            faces[f] = nomt
    SPECS.append({"groupe": groupe, "nom": nom, "c": np.asarray(c, float), "X": X, "Y": Y, "s": s, "faces": faces})


def volume_lame():
    # biseaux : deux par tronçon du fil (un par face)
    for idx, (p, q, v0, v1) in enumerate(SEGS_E):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))                    # vers l'intérieur (le dos est du côté +r)
        sm_ = float((p[0] + q[0]) / 2)
        h, wb = float(h_lame(sm_)), float(wb_lame(sm_))
        al = math.atan2(h - Z_E, wb)
        e0 = 0.3 if v0 else 0.05
        e1 = wb * 1.3 if v1 else 0.05
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        sy = (wb + 0.08) / math.cos(al)
        for sg in (1, -1):
            Y = np.array((n[0] * math.cos(al), n[1] * math.cos(al), sg * math.sin(al)))
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0], mid[1], sg * Z_E)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(P, idx=idx):
                P2 = P[..., :2]
                D = d_stack(P2, SEGS_E)
                de = D.min(0)
                m = in_poly(P2, LAME) & (D[idx] <= de + RECOUV) & (de < wb_lame(P2[..., 0]) + 0.03)
                col, em = peint_biseau(P2, de)
                return col, em, m

            def fil(P, idx=idx, n=n):
                P2 = P[..., :2] + n * 0.06
                D = d_stack(P2, SEGS_E)
                m = in_poly(P2, LAME) & (D[idx] <= D.min(0) + RECOUV)
                col, em = peint_fil(P2)
                return col, em, m

            spec("fer", f"bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil})
    # plats : une plaque par face, plan exact (h linéaire en s)
    pa = np.array(LAME)
    a0, a1, b0, b1 = pa[:, 0].min() - 0.05, pa[:, 0].max() + 0.05, pa[:, 1].min() - 0.05, pa[:, 1].max() + 0.05
    sl = float((h_lame(a1) - h_lame(a0)) / (a1 - a0))
    ac, bc = (a0 + a1) / 2, (b0 + b1) / 2
    for sg in (1, -1):
        X = unit(np.array((1.0, 0.0, sg * sl)))
        Y = np.array((0.0, float(sg), 0.0))
        Z = np.cross(X, Y)
        c = np.array((ac, bc, sg * float(h_lame(ac)))) - Z * (TH / 2)

        def plat(P):
            P2 = P[..., :2]
            de = dE(P2)
            m = in_poly(P2, LAME) & (de >= wb_lame(P2[..., 0]) - 0.03) & ~in_gout(P2)
            col, em = peint_plat(P2, de)
            return col, em, m

        spec("fer", f"plat{'pm'[sg < 0]}", c, X, Y, ((a1 - a0) * math.sqrt(1 + sl * sl), b1 - b0, TH), {"south": plat})
    # dos : un mur plein par tronçon, face extérieure découpée par l'alpha à la hauteur de la surface
    for j in range(len(S_PTS) - 1):
        p, q = np.array(S_PTS[j], float), np.array(S_PTS[j + 1], float)
        d = unit(q - p)
        n_out = np.array((-d[1], d[0]))
        Ln = float(np.linalg.norm(q - p))
        mid = (p + q) / 2
        hm = float(max(h_lame(p[0]), h_lame(q[0]))) + 0.06
        X = np.array((d[0], d[1], 0.0))
        Y = np.array((0.0, 0.0, 1.0))
        Z = np.cross(X, Y)
        face = "south" if Z[:2] @ n_out > 0 else "north"

        def mur(P):
            P2 = P[..., :2]
            m = np.abs(P[..., 2]) <= surf(P2)
            col, em = peint_dos(P)
            return col, em, m

        c = np.array((mid[0], mid[1], 0.0)) - np.array((n_out[0], n_out[1], 0.0)) * (TH / 2)
        spec("fer", f"dos{j}", c, X, Y, (Ln + 0.04, 2 * hm, TH), {face: mur})


def gouttiere():
    pa = np.array(GOUT)
    box = (pa[:, 0].min() - 0.15, pa[:, 0].max() + 0.15, pa[:, 1].min() - 0.15, pa[:, 1].max() + 0.15)

    def fond(P):
        P2 = P[..., :2]
        m = in_gout(P2) | (d_gout(P2) < 0.1)
        dc = d_axe_gout(P2)
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + OS_SOMBRE
        em = np.zeros_like(col)
        col[dc < 0.24] = AURA
        col[dc < 0.15] = VEIN
        col[dc < 0.08] = VCORE
        em[dc < 0.15] = E_VEINE
        em[dc < 0.08] = E_COL
        return col, em, m

    a0, a1, b0, b1 = box
    spec("fer", "fond", ((a0 + a1) / 2, (b0 + b1) / 2, 0.0), (1, 0, 0), (0, 1, 0), (a1 - a0, b1 - b0, 2 * Z_FOND),
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
        top = min(float(surf(np.array([x]))[0]) for x in back + [p, q]) - 0.03
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
                dz = h_lame(P2[..., 0]) - np.abs(P[..., 2])
                col = lerp(OS_BASE, OS_SOMBRE, np.clip((dz[..., None] - 0.08) / 0.3, 0, 1)) + np.zeros(P.shape[:-1] + (3,), np.float32)
                col[dz < 0.08] = ARETE
                return col, np.zeros_like(col), np.ones(P.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zc)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec("fer", f"paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


# ------------------------------------------------------------------ tours (pièces rondes, recette de skin_masse_orage)
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


def p_os(xn, t, y, r, L, ex):
    k = np.clip(0.35 + 0.45 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    col = lerp(OS_SOMBRE, OS_CLAIR, k[..., None]) * (1 + 0.05 * np.sin(y * 23 + xn))[..., None]
    col = np.where((np.abs(xn) < 0.22)[..., None], lerp(col, REFLET, 0.45), col)
    return col, None


def p_bague(xn, t, y, r, L, ex):
    k = np.clip(0.4 + 0.5 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    return lerp(OS_BASE, ARETE, k[..., None] * 0.8), None


def p_cuir(xn, t, y, r, L, ex):
    f = ((y / 0.62 + xn * 0.16) % 1.0)[..., None]
    col = lerp(np.array((84, 44, 98), np.float32), np.array((38, 18, 48), np.float32), f)
    col = np.where(f > 0.82, np.array((14, 7, 18), np.float32), col)
    return col * (1 + 0.04 * np.sin(xn * 3 + y * 11))[..., None], None


def p_clou(xn, t, y, r, L, ex):
    k = (1 - np.abs(xn))[..., None]
    return lerp(np.array((150, 132, 160), np.float32), np.array((214, 200, 218), np.float32), k), None


def p_griffe(xn, t, y, r, L, ex):
    tg = ex["t0"] + (ex["t1"] - ex["t0"]) * t
    q = np.abs(xn)
    col = lerp(np.array((54, 48, 66), np.float32), np.array((26, 22, 34), np.float32), (q ** 1.2)[..., None])
    col = lerp(col, np.array((132, 98, 176), np.float32), (np.clip(1 - q * 2.4, 0, 1) * 0.45)[..., None])
    col = col * (1 - 0.18 * (np.sin(tg * 40.0) > 0.85))[..., None]                     # bagues de croissance
    col = lerp(col, np.array((132, 240, 58), np.float32), np.clip((tg - 0.62) / 0.25, 0, 1)[..., None])
    em = np.zeros(col.shape, np.float32)
    on = tg > 0.74
    em[on] = lerp(np.array((44, 110, 26), np.float32), np.array((96, 230, 58), np.float32), np.clip((tg[on] - 0.74) / 0.2, 0, 1)[..., None])
    return col, em


PEINTRES = {"os": p_os, "bague": p_bague, "cuir": p_cuir, "clou": p_clou, "griffe": p_griffe}


def tuile_pan(nom, mat, L, w0, w1, r0, r1, ex):
    """Tuile d'un pan trapézoïdal : rangée 0 = bout P1 (haut de la face south), colonne 0 = côté -X."""
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
    col, em = PEINTRES[mat](xn, t, y + ex.get("y0", 0.0), r, L, ex)
    TILES[nom] = _rgba(col, mask, em)
    return nom


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
    """Plan (a, b, z) de l'épée -> monde : rotation theta autour de Z, puis translation P0."""
    th, P0 = 0.0, V(0, 0, 0)


def W_(a, b, z=0.0):
    c, s = math.cos(Repere.th), math.sin(Repere.th)
    return Repere.P0 + V(c * a - s * b, s * a + c * b, z)


def Wv(a, b, z=0.0):
    c, s = math.cos(Repere.th), math.sin(Repere.th)
    return V(c * a - s * b, s * a + c * b, z)


def WC(s, r, z=0.0):
    """Repère de la corde de la lame -> monde."""
    return W_(*vers_plan(s, r), z)


def WCv(s, r, z=0.0):
    return Wv(*vers_plan_v(s, r), z)


def group(name, origin, parent=None, nom=None):
    assert name not in groups, name
    groups[name] = {"origin": [round(float(v), 4) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "nom": nom or name}
    return name


def boite(g, name, c, X, Y, s, faces):
    """Boîte centrée en c (monde), axes X, Y, tailles s ; faces {face: nom de tuile | CLEAR}."""
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
        L = math.hypot(b1 - b0, r1 - r0)
        if L < 1e-4:
            continue
        tile = tuile_pan(f"{nom}{i}", mat, L, 2 * r0 * tn, 2 * r1 * tn, r0, r1, ex)
        db, dr = (b1 - b0) / L, (r1 - r0) / L
        wm = max(2 * r0 * tn, 2 * r1 * tn) + 2 * OVW
        for k in range(n):
            th = phase + TAU * k / n
            e = math.cos(th) * ref + math.sin(th) * w3
            P0, P1 = O + b0 * ax + r0 * e, O + b1 * ax + r1 * e
            Y = unit(P1 - P0)
            N = -dr * ax + db * e
            X = np.cross(Y, N)
            boite(g, f"{nom}{i}_{k}", (P0 + P1) / 2 - N * TH / 2, X, Y, (wm, L + 2 * OVL, TH), {"south": tile})


def griffe(g, nom, p, X, Y, L, rmax, curve=0.30, nseg=8, n=8):
    """Griffe recourbée en tronçons coniques à 8 pans : part de p (monde) vers X, se recourbe vers Y ; pointe verte."""
    p, X = np.asarray(p, float), unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    nz = np.cross(X, Y)
    centre = lambda t: p + X * (L * (t - 0.12 * t * t)) + Y * (curve * L * t ** 2.1)
    ray = lambda t: rmax * (max(0.0, 1 - t) ** 0.8 + 0.06) / 1.06
    for i in range(nseg):
        t0, t1 = i / nseg, (i + 1) / nseg
        a, b = centre(t0), centre(t1)
        Ls = float(np.linalg.norm(b - a))
        prof = [(0.0, ray(t0), Ls, ray(t1) if i < nseg - 1 else 0.0, "griffe", {"t0": t0, "t1": t1})]
        if i == 0:                                   # bouchon conique : la racine n'est jamais un anneau ouvert
            prof.insert(0, (-0.3, 0.0, 0.0, ray(0.0), "griffe", {"t0": 0.0, "t1": 0.0}))
        tour(g, f"{nom}{i}_", a, b - a, nz, prof, n=n)


def bone_node(name):
    g = groups[name]
    return {"name": g["nom"], "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


def conception():
    SPECS.clear()
    volume_lame()
    gouttiere()


conception()

G0, G1 = (-2.8, 0.24), (2.9, -0.30)       # axe de la poignée (plan)


def build(theta, P0):
    """L'épée dans le plan (a, b) posé dans le plan XY du monde (plat vers ±Z), a tourné de theta, P0 = origine du plan."""
    elements.clear()
    groups.clear()
    Repere.th, Repere.P0 = theta, np.asarray(P0, float)
    out = {}
    nz = V(0, 0, 1)
    racine = group("repos", W_(0, 0), nom=objet.etape("repos", "epee"))
    epee = group("epee", W_(0, 0), parent=racine)
    # --- fer : lame en volume, éperon ; pivot sur la garde (l'apparition le fait sortir de la garde)
    fer = group("fer", W_(*BL_START), parent=epee)
    group("ctrl_lumiere_fer", W_(*BL_START), parent=fer, nom="ctrl_lumiere")
    for sp in SPECS:
        c = sp["c"]
        boite(fer, sp["nom"], WC(*c), WCv(*sp["X"]), WCv(*sp["Y"]), sp["s"], sp["faces"])
    pe, ne, de = blade_at(0.13)
    racine_ep = pe + ne * (blade_hs(0.13) - 0.3)
    griffe(fer, "eperon", W_(*racine_ep), Wv(*(ne * 0.85 - de * 0.5)), Wv(*(-de)), 1.8, 0.48, curve=0.34, nseg=5)
    # --- poignée : tour à 12 pans (pommeau d'os, cuir en spirale, bague d'os), clous d'os traversants
    ga, gb = np.array(G0), np.array(G1)
    Lh = float(np.linalg.norm(gb - ga))
    ax = Wv(*(gb - ga))
    prof = [(-1.05, 0.0, -0.92, 0.42, "os", {"clair": 0.15}), (-0.92, 0.42, -0.7, 0.74, "os", {"clair": 0.1}),
            (-0.7, 0.74, -0.25, 0.82, "os", {}), (-0.25, 0.82, -0.05, 0.62, "bague", {"clair": -0.1}),
            (-0.05, 0.62, Lh - 0.45, 0.6, "cuir", {}),
            (Lh - 0.45, 0.6, Lh - 0.3, 0.9, "bague", {"clair": 0.1}), (Lh - 0.3, 0.9, Lh + 0.15, 0.9, "bague", {}),
            (Lh + 0.15, 0.9, Lh + 0.3, 0.7, "bague", {"clair": -0.1})]
    tour(epee, "poignee", W_(*G0), ax, nz, prof, n=12)
    for k, u_ in enumerate((-1.45, 0.05, 1.55)):
        c = W_(u_, lerp(G0[1], G1[1], (u_ - G0[0]) / (G1[0] - G0[0])))
        tour(epee, f"clou{k}_", c - nz * 0.9, nz, ax, [(0.0, 0.0, 0.14, 0.27, "clou", {}), (0.14, 0.27, 1.66, 0.27, "clou", {}),
                                                        (1.66, 0.27, 1.8, 0.0, "clou", {})], n=8, phase=math.pi / 8)
    # --- collet d'os au talon : boîte dans l'axe du talon (cache la base de la lame), bord violacé
    p0, n0, d0 = blade_at(0.0)
    he0, hs0 = blade_he(0.0), blade_hs(0.0)
    cc = p0 + n0 * (hs0 - he0) / 2 - d0 * 0.15
    TILES.setdefault("collet_f", _rgba(*_collet(40, 64)))
    TILES.setdefault("collet_t", _rgba(*_collet(40, 16)))
    TILES.setdefault("collet_b", _rgba(*_collet(64, 16)))
    boite(epee, "collet", W_(*cc), Wv(*d0), Wv(*n0), (1.3, he0 + hs0 + 0.35, 1.8),
          {"south": "collet_f", "north": "collet_f", "up": "collet_t", "down": "collet_t", "east": "collet_b", "west": "collet_b"})
    # --- griffes (garde et pommeau), chacune dans son groupe (animées)
    g_b = group("griffe_garde", W_(2.8, -0.3), parent=epee)
    griffe(g_b, "gg", W_(*(p0 - n0 * (he0 - 0.15))), Wv(0.32, -1), Wv(-1, 0), 5.8, 0.62, nseg=10)
    g_h = group("griffe_contre", W_(2.9, 0.2), parent=epee)
    griffe(g_h, "gc", W_(*(p0 + n0 * (hs0 - 0.2))), Wv(0.45, 1), Wv(1, 0), 3.2, 0.46)
    g_c = group("griffe_cote", W_(2.9, -0.3), parent=epee)
    griffe(g_c, "gs", W_(*cc, 0.4), Wv(0.35, 0, 1), Wv(1, -0.2), 3.4, 0.44)
    g_p = group("griffe_pommeau", W_(-3.1, 0.25), parent=epee)
    griffe(g_p, "gp", W_(-3.35, 0.22), Wv(-0.75, -0.85), Wv(1, -0.4), 3.2, 0.42)
    out["griffes"] = [(g_b, 1), (g_h, -1), (g_c, 1), (g_p, -1)]
    out["fer"], out["racine"] = fer, racine
    return out


def _collet(W, H):
    yy, xx = np.mgrid[0:H, 0:W]
    u, v = (xx + 0.5) / W, (yy + 0.5) / H
    bord = np.minimum(np.minimum(u, 1 - u) * W, np.minimum(v, 1 - v) * H) / DF
    col = lerp(OS_BASE, OS_CLAIR, np.clip(0.4 + 0.3 * np.sin(u * 9 + v * 5), 0, 1)[..., None])
    col[bord < 0.12] = ARETE
    col[(bord >= 0.12) & (bord < 0.2)] = OS_SOMBRE
    return col, np.ones((H, W), bool)


def coins():
    P = []
    for e in elements:
        f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
        R = rmat(*e.get("rotation", (0, 0, 0)))
        for i in range(8):
            c = np.array([(f, t)[(i >> k) & 1][k] for k in range(3)])
            P.append(R @ (c - o) + o)
    return np.array(P)


# Passe 1 : arme posée sur a ; axe pommeau -> pointe mesuré sur la géométrie
build(0.0, V(0, 0, 0))
P = coins()
tip = P[np.argmax(P[:, 0])]
pom = P[np.argmin(P[:, 0])]
ax_ang = math.atan2(tip[1] - pom[1], tip[0] - pom[0])
THETA = math.radians(45) - ax_ang            # axe de l'arme sur la diagonale du bloc, pointe en haut à droite (vue de +Z)
build(THETA, V(0, 0, 0))
P = coins()
CENTRE = (P.min(axis=0) + P.max(axis=0)) / 2
F = build(THETA, V(8, 8, 8) - CENTRE)
P = coins()
D_ = np.array((1, 1, 0)) / math.sqrt(2)
LONGUEUR = float((P @ D_).max() - (P @ D_).min())
outliner = [bone_node(F["racine"])]


# ------------------------------------------------------------------ atlas (après la géométrie : toutes les tuiles sont connues)
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
        if ime is not None:
            tex_e[y:y + h, x:x + w] = ime
        x += w + 1
        shelf = max(shelf, h)
    UV[CLEAR] = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]
    assert tex[TEX - 2, TEX - 2, 3] == 0
    tex[..., :3] &= 0xFC
    assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
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
    for f in e["faces"].values():
        f["uv"] = list(UV[f["uv"]])


# ------------------------------------------------------------------ animations (objet vivant, guide 14 ; inchangées)
# Les griffes pivotent autour de la normale de la lame (+Z) : elles restent dans leur plan.
def rotkf(t, z):
    return {"channel": "rotation", "data_points": [{"x": "0", "y": "0", "z": str(round(z + 0.0, 2))}], "time": round(t, 3), "interpolation": "linear"}


def poskf(t, x):
    return {"channel": "position", "data_points": [{"x": str(round(x + 0.0, 3)), "y": "0", "z": "0"}], "time": round(t, 4), "interpolation": "linear"}


def sckf(t, v):
    return {"channel": "scale", "data_points": [{"x": str(round(v, 3)), "y": str(round(v, 3)), "z": str(round(v, 3))}], "time": round(t, 4),
            "interpolation": "linear"}


def anim(name, length, loop="loop"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "item_idle",
            "animators": {}}


def piste(an, g, keys):
    an["animators"][groups[g]["uuid"]] = {"name": groups[g]["nom"], "type": "bone", "keyframes": keys}


def echant(L, n, closed=True):
    return [L * i / n for i in range(n + 1 if closed else n)]


CTRL = "ctrl_lumiere_fer"

L_IDLE = 6.0
idle = anim("item_idle", L_IDLE)
for j, (g, sg) in enumerate(F["griffes"]):
    piste(idle, g, [rotkf(t, sg * 2.5 * math.sin(TAU * (t / L_IDLE - 0.11 * j))) for t in echant(L_IDLE, 24)])
piste(idle, CTRL, [poskf(t, 0.35 * math.sin(TAU * 2 * t / L_IDLE)) for t in echant(L_IDLE, 24)])

L_SEL = 0.7
sel = anim("event_select", L_SEL, "once")
piste(sel, F["fer"], [sckf(t, 0.2 + 0.8 * sm(t, 0.0, 0.32) + 0.06 * bump(t, 0.24, 0.32, 0.34, 0.5)) for t in echant(L_SEL, 21)])
for j, (g, sg) in enumerate(F["griffes"]):
    piste(sel, g, [rotkf(t, -sg * 28 * (1 - sm(t, 0.12 + 0.06 * j, 0.5 + 0.04 * j))) for t in echant(L_SEL, 21)])
piste(sel, CTRL, [poskf(t, -1 + 1 * sm(t, 0.3, 0.45) + 0.8 * bump(t, 0.38, 0.46, 0.5, 0.7)) for t in echant(L_SEL, 21)])

L_SW = 0.45
sw = anim("event_swing", L_SW, "once")
for j, (g, sg) in enumerate(F["griffes"]):
    piste(sw, g, [rotkf(t, -sg * 10 * bump(t, 0.0, 0.05, 0.14 + 0.02 * j, 0.42)) for t in echant(L_SW, 18)])
piste(sw, CTRL, [poskf(t, 0.9 * bump(t, 0.0, 0.04, 0.1, 0.4)) for t in echant(L_SW, 18)])

L_HIT = 0.6
hit = anim("event_hit", L_HIT, "once")
for j, (g, sg) in enumerate(F["griffes"]):
    piste(hit, g, [rotkf(t, sg * 4 * math.sin(TAU * 3 * t / 0.36) * (1 - sm(t, 0.0, 0.36))) for t in echant(L_HIT, 24)])
piste(hit, CTRL, [poskf(t, 1.6 * (sm(t, 0.0, 0.03) * (1 - sm(t, 0.06, 0.55)))) for t in echant(L_HIT, 24)])
SON_HIT = "block.sculk.break"

ANIMS = [idle, sel, sw, hit]

# ------------------------------------------------------------------ écriture
assert len(elements) <= 8192, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
AFFICHAGE = objet.affichage("epee", gui={"scale": [0.76, 0.76, 0.76]})     # lame courbe : boîte plus large, ramenée à la case
model = objet.modele(NOM, "epee", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons
limiter_sons(model)
# Un seul son, au coup qui touche ; tools/sons.py ne connaît pas encore les événements d'objet : remis ici, à 0,04 s
# (une clé à 0,0 s est muette au premier déclenchement, diagnostic F5).
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": SON_HIT, "file": ""}], "time": 0.04}]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur sur la diagonale {LONGUEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)} ; theta {math.degrees(THETA):.1f}° ;"
      f" marge gouttière/biseau {_marge:.2f} px")
