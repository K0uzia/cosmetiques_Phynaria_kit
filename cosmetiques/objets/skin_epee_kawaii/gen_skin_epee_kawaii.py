"""Lame Câline : skin d'objet (guide 14) pour toutes les épées du joueur, ensemble Kawaii (thème Mignon). Design original.
Écrit skin_epee_kawaii.png, skin_epee_kawaii_e.png et .build/skin_epee_kawaii_brut.bbmodel à côté de ce script.

Idée (référence du langage Kawaii des objets, ligne « Langage » de sets-objets-2026-11-08.md ; .claude/styles/kawaii.md) :
- garde = **gros cœur de sucre framboise dodu** (plaque biseautée fermée « coussin », 2 px d'épaisseur), lobes vers la pointe :
  la lame sort de l'échancrure ; grand reflet blanc en fenêtre, petit contre-reflet ;
- de chaque côté du cœur, **deux bosses de nuage** (sphères de pans) en guise de quillons ; pommeau = petit nuage de trois bosses ;
- lame droite de **sucre lilas** mat, pointe en **ogive arrondie** (aucune pointe vive), fil crème, bande rose bonbon le long du fil,
  liseré lilas foncé à l'arête du plat ; gouttière creusée (fond lavande) où sont serties **quatre dragées-cœurs** roses en volume ;
- fusée de **guimauve torsadée** rose bonbon / crème (spirale continue d'un pan à l'autre, comme l'arc de guimauve) entre deux
  bagues lavande.
Lumière _e seulement sur de petites sources nettes : les dragées-cœurs (225,140,196) et le contre-reflet du cœur.

Vrai volume (recette .claude/references/objets/volume-3d.md) : lame hexagonale creusée, amincie 1,56 -> 0,54 px, biseaux à pente
unique 40° (un cube incliné par tronçon de fil <= 2 px et par face), plats inclinés, gouttière creusée (parois + fond), couleurs
portées par les faces échantillonnées texel par texel et découpées par l'alpha, recouvrement 0,08. Cœur et dragées = la même
`Piece` sur un contour fermé (tous les bords biseautés). Pièces rondes en tours de pans, une tuile par pan (éclairage et spirale).

Repère (catégorie objets, Recette) : plan (a le long de l'épée, b en travers, z = normale vue de l'inventaire) posé sur la diagonale
du bloc, pointe en haut à droite vue de +Z comme l'image vanilla, centré ; Display vanilla item/handheld, gui ramené à la case.
Une étape : groupe racine `repos`.

Objet vivant (guide 14), doux et rebondi :
- item_idle (8 s) : le cœur bat (double battement toutes les 4 s, `scale` : seul dépliage de ce groupe), les dragées s'avivent
  au battement (ctrl_lumiere), les nuages flottent doucement ; aucun son ;
- event_select (0,7 s) : « plop » : les nuages de la garde et du pommeau gonflent 0 -> 1,25 -> 0,92 -> 1 (seul dépliage par
  `scale` de ces groupes), le cœur se dandine, les dragées s'allument ;
- event_swing (0,4 s) : les nuages suivent en retard (rotation amortie), le cœur penche ;
- event_hit (0,9 s) : bouffée de six cœurs de sucre `trans_coeurs` (cachés huit fois plus petits dans le cœur, seul dépliage par
  `scale` de ce groupe) qui s'écartent, montent et s'effacent (ctrl_alpha) + emit_mc_heart (ctrl_emit +5), cœur qui fait
  « boing », dragées vives ; **le seul son** du skin : `pof_sucre` embarqué (sons/pof_sucre.py, original) à 0,04 s.
Aucun son sur event_use_start ni event_enter_* (il n'y en a pas).

Fonctions avancées : calque _e, trans_coeurs, ctrl_alpha, ctrl_lumiere, emit_mc_heart + ctrl_emit, scale animé, son embarqué,
animations d'objet. Non simulés par l'aperçu : animations en main, particules, ctrl_emit, ctrl_lumiere, son. À juger en jeu :
event_hit et son son (pas encore vérifiés par le développeur), bouffée de cœurs, lecture du cœur et des nuages dans la case.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

AVEC_E = True
NOM = "skin_epee_kawaii"
TEX = 512
TAU = 2 * math.pi
DF = 16.0                       # texels par px sur les faces des volumes
DENS = 16.0                     # texels par px sur les pans des tours
TH = 0.3                        # épaisseur des cubes (biseaux, plats, parois, pans)
RECOUV = 0.08                   # recouvrement des faces voisines
OVL, OVW = 0.04, 0.03           # recouvrement des pans (en long, en travers)
KC, F_GEO = 16.0, 2.0           # bouffée de cœurs cachée : géométrie F_GEO / KC, clés scale <= KC / F_GEO


def A(c):
    return np.array(c, np.float32)


# Palette du set (.claude/styles/kawaii.md ; langage des objets Kawaii)
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
A_G = 7.4                                   # centre du cœur de garde
A0 = 7.7                                    # talon de la lame (caché dans le cœur)
TIP = (25.55, 0.0)
U = [(A0, 1.75), (11.0, 1.84), (14.5, 1.86), (18.0, 1.8), (21.0, 1.62), (23.0, 1.36), (24.2, 1.05), (24.95, 0.7),
     (25.35, 0.36), TIP]                    # ogive arrondie : la courbure resserre vers la pointe sans angle vif
L = [(a, -b) for a, b in U[:-1]] + [TIP]
LAME = U + L[::-1][1:-1]
SLIT = [(10.05, 0.0), (10.7, 0.0), (13.0, 0.0), (16.0, 0.0), (18.6, 0.0), (19.25, 0.0)]
GW = [0.12, 0.5, 0.52, 0.52, 0.5, 0.12]
Z_FOND = 0.16
DRAGEES = [11.25, 13.45, 15.65, 17.85]       # centres des dragées-cœurs le long de la gouttière


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
    return 0.78 + (0.27 - 0.78) * np.clip((np.asarray(a, float) - A0) / (TIP[0] - A0), 0, 1)


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


def grain(P, seed=0.0):
    """Grain de sucre mat (±3 %)."""
    v = np.sin(P[..., 0] * 37.0 + P[..., 1] * 11.0 + seed) * np.sin(P[..., 1] * 43.0 - P[..., 0] * 7.0 + seed * 2)
    return v * 0.02


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
def peint_biseau_lame(P, dE):
    f = (dE / wb_lame(P[..., 0]))[..., None]
    col = lerp(LILAS["hi"], LILAS["base"] * 1.04, np.clip((f - 0.42) / 0.45, 0, 1))
    col = np.where(f < 0.42, lerp(BONBON, LILAS["hi"], np.clip((f - 0.30) / 0.12, 0, 1)), col)
    col = np.where(f < 0.17, CREME + np.zeros_like(col), col)
    col = np.where(f >= 0.9, LISERE + np.zeros_like(col), col)
    return col * (1 + grain(P, 1.0))[..., None], None


def peint_fil_lame(P):
    return np.zeros(P.shape[:-1] + (3,), np.float32) + CREME, None


def peint_plat_lame(P, dE):
    wb = wb_lame(P[..., 0])
    k = np.clip(0.45 + 0.25 * P[..., 1] / 1.8, 0, 1)[..., None]       # +b = vers le haut en main : un peu plus clair
    col = lerp(LILAS["base"], LILAS["hi"], k * 0.55) * (1 + grain(P, 2.0))[..., None]
    col[dE < wb + 0.05] = LISERE
    dg = d_gout(P)
    col[dg < 0.09] = CREME                                          # lèvre crème de la gouttière
    col[(dg >= 0.09) & (dg < 0.14)] = LILAS["low"]
    return col, None


LAME_P = Piece("lame", LAME, [U, L], h_lame, wb_lame, Z_E, peint_biseau_lame, peint_plat_lame, peint_fil_lame, trou=in_gout)


def gouttiere(groupe):
    """Fond lavande (âme de 0,32 px) + parois le long des deux bords, sur chaque face ; lèvre crème."""
    pa = np.array(GOUT)
    box = (pa[:, 0].min() - 0.15, pa[:, 0].max() + 0.15, pa[:, 1].min() - 0.15, pa[:, 1].max() + 0.15)

    def fond(P):
        P2 = P[..., :2]
        m = in_gout(P2) | (d_gout(P2) < 0.1)
        col = lerp(LAVANDE["low"], LAVANDE["base"], np.clip(0.4 + 0.5 * P2[..., 1] / 0.5, 0, 1)[..., None]) + np.zeros(P.shape[:-1] + (3,), np.float32)
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
                col = lerp(LILAS["base"], LAVANDE["low"], np.clip((dz[..., None] - 0.1) / 0.3, 0, 1)) + np.zeros(P.shape[:-1] + (3,), np.float32)
                col[dz < 0.1] = CREME
                return col, None, np.ones(P.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zc)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec(groupe, f"paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


# --- cœur de garde (framboise) : plaque « coussin » fermée, tous les bords biseautés
H_C, ZE_C, WB_C = 1.0, 0.3, 0.86
COEUR = coeur_poly(1.05, 0.5, 1.2, -1.85, 0.42, n=44, oy=A_G)
CL_ = np.array(COEUR)
REFLET = (A_G + 0.6, 1.05)                   # fenêtre de reflet sur le lobe +b (haut en main et dans la case)


def peint_biseau_coeur(P, dE):
    f = np.clip(dE / WB_C, 0, 1)[..., None]
    # éclairage du biseau : sa pente tourne vers l'extérieur ; le côté +a +b (haut dans la case) est le plus clair
    dirn = np.stack([P[..., 0] - (A_G - 0.2), P[..., 1]], -1)
    dirn = dirn / np.maximum(np.linalg.norm(dirn, axis=-1, keepdims=True), 1e-6)
    lum = np.clip(0.5 + 0.5 * (dirn @ np.array((0.707, 0.707))), 0, 1)[..., None]
    col = lerp(FRAMB["low"], lerp(FRAMB["base"], FRAMB["hi"], 0.3), np.clip(f * 1.15, 0, 1)) * (0.9 + 0.2 * lum)
    col = np.where(f < 0.1, FRAMB["low"] * 0.92, col)
    col, _ = reflet_coeur(P, col)
    return col, None


def reflet_coeur(P, col):
    """Grande fenêtre de reflet (ellipse le long du lobe +b, barre de fenêtre) et petit contre-reflet lumineux, biseau et plat."""
    a, b = P[..., 0], P[..., 1]
    col = np.array(col, np.float32)
    em = np.zeros(P.shape[:-1] + (3,), np.float32)
    da, db = a - REFLET[0], b - REFLET[1]
    u = (da * 0.6 + db * 0.8)
    v = (-da * 0.8 + db * 0.6)
    fen = (u / 0.62) ** 2 + (v / 0.26) ** 2 < 1
    col[fen] = BLANC
    col[fen & (np.abs(u + 0.08) < 0.05)] = FRAMB["hi"]
    cr = np.hypot(a - (A_G - 0.95), b + 1.05) < 0.17
    col[cr] = A((255, 220, 236))
    em[cr] = (210, 150, 186)
    return col, em


def peint_plat_coeur(P, dE):
    a, b = P[..., 0], P[..., 1]
    k = np.clip(0.45 + 0.2 * ((a - A_G) + b) / 2.2, 0, 1)[..., None]
    col = lerp(lerp(FRAMB["base"], FRAMB["hi"], 0.3), FRAMB["hi"], k) + np.zeros(P.shape[:-1] + (3,), np.float32)
    return reflet_coeur(P, col)


def peint_fil_coeur(P):
    return np.zeros(P.shape[:-1] + (3,), np.float32) + FRAMB["low"] * 0.85, None


COEUR_P = Piece("coeur", COEUR, [COEUR + [COEUR[0]]], cst(H_C), cst(WB_C), ZE_C, peint_biseau_coeur, peint_plat_coeur,
                peint_fil_coeur, maxlen=0.6)


# --- dragées-cœurs (sucre rose, lumière _e) serties dans la gouttière, lobes vers la pointe
H_D, ZE_D, WB_D = 0.40, 0.22, 0.24


def peint_dragee(P, dE):
    col = np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE
    em = np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE_E
    return col, em


def peint_dragee_plat(P, dE):
    col, em = peint_dragee(P, dE)
    a, b = P[..., 0], P[..., 1]
    fa = np.array([min(DRAGEES, key=lambda x: abs(x - v)) for v in a.ravel()]).reshape(a.shape)
    hl = np.hypot(a - (fa + 0.12), b - 0.18) < 0.09
    col[hl] = BLANC
    em[hl] = (225, 200, 215)
    return col, em


def peint_dragee_fil(P):
    return np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE * 0.86, np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE_E * 0.8


DRAGEES_P = []
for _i, _a in enumerate(DRAGEES):
    _poly = coeur_poly(1.0, 0.45, 1.15, -1.6, 0.45, n=18, oy=_a + 0.04, sx=0.2)
    DRAGEES_P.append(Piece(f"dragee{_i}", _poly, [_poly + [_poly[0]]], cst(H_D), cst(WB_D), ZE_D, lambda P, dE: peint_dragee(P, dE),
                           peint_dragee_plat, peint_dragee_fil, maxlen=0.6))


def conception():
    SPECS.clear()
    volume(LAME_P, "lame")
    gouttiere("lame")
    volume(COEUR_P, "coeur", prolonge=0.6)
    for pc in DRAGEES_P:
        volume(pc, "dragees", prolonge=0.6)


conception()
_marge = float(min(LAME_P.wb(np.array([a]))[0] for a, _ in SLIT))


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
    """Guimauve torsadée deux brins : phase = longueur + angle du point sur le pourtour (spirale continue d'un pan à l'autre)."""
    ang = ex["ang"] + xn * math.pi / ex["n"]
    f = (y / ex["pas"] + ang / math.pi) % 1.0                      # deux brins par tour
    rose = f < 0.5
    col = np.where(rose[..., None], GUIM_R, GUIM_C)
    edge = np.minimum(np.abs(f - 0.5), np.minimum(f, 1 - f))        # creux entre deux brins
    lum = lum_tex(xn, t, ex)[..., None]
    col = col * (0.8 + 0.22 * lum)
    sh = np.clip(1 - edge / 0.08, 0, 1)[..., None]
    col = lerp(col, np.where(rose[..., None], A((176, 60, 120)), A((206, 186, 214))), sh * 0.6)
    return col, None


PEINTRES = {"nuage": p_nuage, "lavande": p_lavande, "guimauve": p_guimauve}


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
def t_coeur_trans(n=40):
    """Petit cœur de sucre translucide (alpha 150 -> bord 235), reflet blanc ; tuile du groupe trans_coeurs."""
    ss = 4
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    X, Y = (xx + 0.5 - N / 2) / (N / 2) * 2.4, -(yy + 0.5 - N / 2) / (N / 2) * 2.4 + 0.2
    dd = np.full(X.shape, 9.0)
    tt = np.linspace(0, 1, 31)
    for s in (1, -1):
        for t_ in tt:
            cx, cy = s * 1.0 * (1 - t_), 0.45 + (-1.6 - 0.45) * t_
            rr = 1.15 + (0.45 - 1.15) * t_
            dd = np.minimum(dd, np.hypot(X - cx, Y - cy) - rr)
    inside = dd < 0
    a = np.where(inside, np.clip(150 + 85 * np.clip(1 + dd / 0.5, 0, 1), 0, 235), 0)
    col = np.zeros(X.shape + (3,), np.float32) + FRAMB["hi"]
    col = lerp(col, BONBON, np.clip(-dd / 1.0, 0, 1)[..., None] * 0.6)
    fen = ((X - 0.75) / 0.42) ** 2 + ((Y - 0.75) / 0.24) ** 2 < 1
    col[fen] = BLANC
    a = np.where(fen & inside, 245, a)
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.LANCZOS))
    al = np.array(Image.fromarray(a.astype(np.uint8), "L").resize((n, n), Image.LANCZOS)).astype(np.int32)
    al[al < 40] = 0
    al = np.clip(al, 0, 254)
    out = np.dstack([rgb, al]).astype(np.uint8)
    out[al == 0, :3] = 0
    return out, None


TILES["coeur_t"] = t_coeur_trans()
TRANS.add("coeur_t")


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
NUAGES_G = [(A_G - 0.15, 2.55, 0.92), (A_G - 0.55, 3.45, 0.66), (A_G - 0.15, -2.55, 0.92), (A_G - 0.55, -3.45, 0.66)]
NUAGES_P = [(0.0, 0.0, 1.0), (0.45, 0.92, 0.7), (0.45, -0.92, 0.7), (-0.85, 0.0, 0.62)]
C_COEURS = (A_G + 0.2, 0.0)                 # centre de la bouffée de cœurs (cachée dans le cœur)
BOUFFEE = [(-60, 2.6, 1.5), (-25, 3.2, 1.8), (8, 2.7, 1.4), (38, 3.3, 1.7), (72, 2.5, 1.35), (105, 2.1, 1.15)]


def build(theta, P0):
    elements.clear()
    groups.clear()
    Repere.th, Repere.P0 = theta, np.asarray(P0, float)
    out = {}
    nz = V(0, 0, 1)
    ax = Wv(1, 0)
    racine = group("repos", W_(3.5, 0), nom=objet.etape("repos", "epee"))
    epee = group("epee", W_(3.5, 0), parent=racine)
    # --- lame (volume, gouttière) et dragées-cœurs serties
    lame = group("lame", W_(A0, 0), parent=epee)
    drag = group("dragees", W_(14.5, 0), parent=lame)
    group("ctrl_lumiere_dragees", W_(14.5, 0), parent=drag, nom="ctrl_lumiere")
    coeur = group("coeur", W_(A_G, 0), parent=epee)
    group("ctrl_lumiere_coeur", W_(A_G, 0), parent=coeur, nom="ctrl_lumiere")
    for sp in SPECS:
        g = {"lame": lame, "dragees": drag, "coeur": coeur}[sp["groupe"]]
        boite(g, sp["nom"], W_(*sp["c"]), Wv(*sp["X"]), Wv(*sp["Y"]), sp["s"], sp["faces"])
    # --- nuages de garde (quillons) : sortent du cœur au « plop »
    ng = group("nuages", W_(A_G, 0), parent=epee)
    for k, (a, b, r) in enumerate(NUAGES_G):
        boule(ng, f"ng{k}_", W_(a, b), r)
    # --- fusée de guimauve torsadée entre deux bagues lavande, pommeau-nuage
    poi = group("poignee", W_(3.5, 0), parent=epee)
    tour(poi, "fusee", W_(0, 0), ax, nz, [(0.95, 0.6, 5.7, 0.6, "guimauve", {"pas": 1.15})], n=12)
    tour(poi, "bague_b", W_(0, 0), ax, nz, [(0.75, 0.48, 0.8, 0.76, "lavande", {}), (0.8, 0.76, 1.2, 0.76, "lavande", {"arete": True}),
                                           (1.2, 0.76, 1.24, 0.58, "lavande", {})], n=12)
    tour(poi, "bague_h", W_(0, 0), ax, nz, [(5.45, 0.58, 5.5, 0.76, "lavande", {}), (5.5, 0.76, 5.92, 0.76, "lavande", {"arete": True}),
                                           (5.92, 0.76, 5.98, 0.5, "lavande", {})], n=12)
    npo = group("nuage_pommeau", W_(0.9, 0), parent=epee)
    for k, (a, b, r) in enumerate(NUAGES_P):
        boule(npo, f"np{k}_", W_(a, b), r)
    # --- bouffée de cœurs (trans_), F_GEO / KC de sa taille, cachée dans le cœur ; point de cœurs de Minecraft
    CC = W_(*C_COEURS)
    f = F_GEO / KC
    tc = group("trans_coeurs", CC, parent=epee)
    for k, (ang, dist, sz) in enumerate(BOUFFEE):
        dirn = Wv(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        boite(tc, f"bouffee{k}", CC + dirn * dist * f + nz * (0.03 * k - 0.08) * f, V(1, 0, 0), V(0, 1, 0), (sz * f, sz * f, 0.3 * f),
              {"south": "coeur_t", "north": "coeur_t"})
    group("ctrl_alpha_coeurs", CC, parent=tc, nom="ctrl_alpha")
    up = W_(A_G + 1.2, 0)
    em = group("emit_mc_heart", up, parent=epee)
    group("ctrl_emit", up, parent=em)
    out.update(racine=racine, epee=epee, coeur=coeur, nuages=ng, pommeau=npo, coeurs=tc, dragees=drag)
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


K = float(os.environ.get("K", "0.97"))
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
def kf(t, x, y=0.0, z=0.0, ch="rotation"):
    f = lambda v: v if isinstance(v, str) else f"{v + 0.0:.4f}".rstrip("0").rstrip(".")
    return {"channel": ch, "data_points": [{"x": f(x), "y": f(y), "z": f(z)}], "time": round(t, 4), "interpolation": "linear"}


def anim(name, length, tracks, fps=24, loop="loop"):
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A_ = {}
    for (g, ch), fn in tracks.items():
        ks = [kf(t, *fn(t), ch=ch) for t in times]
        A_.setdefault(groups[g]["uuid"], {"name": groups[g]["nom"], "type": "bone", "keyframes": []})["keyframes"] += ks
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": False, "animators": A_}


def ressort(t, t0, amp, f=5.0, amort=0.12):
    """Oscillation amortie qui part de t0 (rebond de guimauve)."""
    if t < t0:
        return 0.0
    x = t - t0
    return amp * math.sin(TAU * f * x) * math.exp(-x / amort)


COEUR_G, NG, NPO, TC, DRG = F["coeur"], F["nuages"], F["pommeau"], F["coeurs"], F["dragees"]
CLD, CLC, CE, CA = "ctrl_lumiere_dragees", "ctrl_lumiere_coeur", "ctrl_emit", "ctrl_alpha_coeurs"

# --- item_idle (8 s) : double battement toutes les 4 s, dragées au battement, nuages qui flottent ; aucun son
L_IDLE = 8.0
BATS = [0.8, 4.8]


def battement(t):
    v = 0.0
    for tb in BATS:
        v += bump(t, tb, tb + 0.08, tb + 0.12, tb + 0.3) + 0.6 * bump(t, tb + 0.3, tb + 0.38, tb + 0.42, tb + 0.66)
    return v


def idle_coeur(t):
    b = battement(t)
    return 1 + 0.07 * b, 1 + 0.07 * b, 1 - 0.03 * b              # gonfle à plat, s'aplatit un peu (volume à peu près constant)


def idle_nuages(t):
    return 0.0, 0.07 * math.sin(TAU * t / L_IDLE * 2), 0.0


def idle_pommeau(t):
    return 0.0, 0.05 * math.sin(TAU * t / L_IDLE * 2 + 1.6), 0.0


item_idle = anim("item_idle", L_IDLE, {
    (COEUR_G, "scale"): idle_coeur, (NG, "position"): idle_nuages, (NPO, "position"): idle_pommeau,
    (CLD, "position"): lambda t: (0.35 * battement(t), 0.0, 0.0),
    (CE, "position"): lambda t: (-1.0, 0.0, 0.0)}, fps=24)

# --- event_select (0,7 s) : plop des nuages (0 -> 1,25 -> 0,92 -> 1), le cœur se dandine, les dragées s'allument


def plop(t, t0):
    if t <= t0:
        return 0.0
    x = t - t0
    if x < 0.16:
        return 1.25 * sm(x, 0.0, 0.16)
    if x < 0.3:
        return lerp(1.25, 0.92, sm(x, 0.16, 0.3))
    return lerp(0.92, 1.0, sm(x, 0.3, 0.45))


L_SEL = 0.7
event_select = anim("event_select", L_SEL, {
    (NG, "scale"): lambda t: (plop(t, 0.06),) * 3,
    (NPO, "scale"): lambda t: (plop(t, 0.0),) * 3,
    (COEUR_G, "rotation"): lambda t: (0.0, 0.0, ressort(t, 0.08, 7.0, f=3.2, amort=0.18)),
    (CLD, "position"): lambda t: (-1.0 + 1.0 * sm(t, 0.15, 0.3) + 0.5 * bump(t, 0.3, 0.36, 0.42, 0.65), 0.0, 0.0)}, fps=40, loop="once")

# --- event_swing (0,4 s) : les nuages suivent en retard, le cœur penche puis revient
L_SW = 0.4
event_swing = anim("event_swing", L_SW, {
    (NG, "rotation"): lambda t: (0.0, 0.0, ressort(t, 0.02, -6.0, f=4.0, amort=0.1) * (t < 0.39)),
    (NPO, "rotation"): lambda t: (0.0, 0.0, ressort(t, 0.04, 5.0, f=4.0, amort=0.1) * (t < 0.39)),
    (COEUR_G, "rotation"): lambda t: (0.0, 0.0, ressort(t, 0.0, 3.0, f=4.5, amort=0.09) * (t < 0.39))}, fps=40, loop="once")

# --- event_hit (0,9 s) : bouffée de cœurs de sucre qui s'écarte, monte et s'efface ; « boing » du cœur ; cœurs de Minecraft
L_HIT = 0.9


def coeurs_scale(t):
    w = sm(t, 0.03, 0.22) * (1 - sm(t, 0.74, 0.76))
    k = 1 + (KC / F_GEO - 1) * w
    return k, k, k


def coeurs_pos(t):
    v = V(0, 1.6, 0) * sm(t, 0.1, 0.72) * (1 - sm(t, 0.74, 0.76))
    return float(v[0]), float(v[1]), float(v[2])


event_hit = anim("event_hit", L_HIT, {
    (TC, "scale"): coeurs_scale, (TC, "position"): coeurs_pos,
    (CA, "position"): lambda t: (-sm(t, 0.35, 0.7) * (1 - sm(t, 0.8, 0.84)), 0.0, 0.0),
    (CE, "position"): lambda t: (5 * bump(t, 0.03, 0.06, 0.3, 0.45), 0.0, 0.0),
    (COEUR_G, "rotation"): lambda t: (0.0, 0.0, ressort(t, 0.02, 9.0, f=4.0, amort=0.14) * (t < 0.88)),
    (CLD, "position"): lambda t: (0.9 * sm(t, 0.0, 0.04) * (1 - sm(t, 0.1, 0.6)), 0.0, 0.0),
    (CLC, "position"): lambda t: (0.6 * sm(t, 0.0, 0.04) * (1 - sm(t, 0.1, 0.5)), 0.0, 0.0)}, fps=40, loop="once")

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
from sons import limiter_sons, embarquer_sons  # noqa: E402
limiter_sons(model)
# Un seul son, au coup qui touche ; tools/sons.py ne connaît pas les événements d'objet : remis ici, à 0,04 s
# (une clé à 0,0 s est muette au premier déclenchement, diagnostic F5). Aucun son ailleurs.
embarquer_sons(model, {"pof_sucre": "sons/pof_sucre.ogg"})
event_hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "pof_sucre", "file": ""}], "time": 0.04}]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur sur la diagonale {LONGUEUR:.1f} px ; largeur {LARGEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)} ;"
      f" gui {GUI} ; biseau mini sous la gouttière {_marge:.2f} px")
