"""Pic Câlin : skin d'objet (guide 14) pour toutes les pioches du joueur, ensemble Kawaii (thème Mignon). Design original.
Écrit skin_pioche_kawaii.png, skin_pioche_kawaii_e.png et .build/skin_pioche_kawaii_brut.bbmodel à côté de ce script.
(Assemblé par .build/assembler.py : gabarit .build/gabarit.py + fonctions communes reprises de gen_skin_epee_kawaii.py.)

Idée (langage Kawaii des objets, ligne « Langage » de sets-objets-2026-11-08.md ; .claude/styles/kawaii.md ; référence du set
skin_epee_kawaii « Lame Câline ») : la pioche de mineur de l'image vanilla (manche en diagonale, fer en croissant dont les bras se
recourbent vers le manche), faite en sucre et en guimauve :
- œil = **gros cœur de sucre framboise dodu** (plaque biseautée fermée « coussin », 2,2 px d'épaisseur), lobes vers le haut :
  le croissant sort de ses deux lobes, le manche entre par sa pointe ; grand reflet blanc en fenêtre, petit contre-reflet `_e` ;
- fer = deux bras de **sucre lilas** mat, dodus, recourbés vers le manche, **bouts en ogive arrondie** (aucune pointe vive),
  fil crème, bande rose bonbon le long du fil, liseré lilas foncé à l'arête du plat ; une gouttière creusée (fond lavande) le
  long de chaque bras où sont serties **deux dragées-cœurs** roses `_e` en volume ;
- manche de **guimauve torsadée** rose bonbon / crème (spirale continue), bague lavande sous le cœur et à la prise ;
  pommeau = petit **nuage** de quatre bosses (sphères de pans).
Lumière _e seulement sur de petites sources nettes : les quatre dragées-cœurs (225,140,196) et le contre-reflet du cœur.

Vrai volume (recette .claude/references/objets/volume-3d.md) : chaque bras = plaque biseautée fermée (classe Bras, comme les
pioches Steampunk et Abyssale) : plat plan incliné 1,60 -> 0,60 px de l'œil au bout, pente unique 45° (tan 1,0 : bras dodus,
biseaux larges et doux, il reste un plat pour la gouttière), un cube incliné par tronçon de fil <= 0,9 px et par face, gouttière
creusée (parois, lèvre crème, fond lavande), faces échantillonnées texel par texel et découpées par l'alpha, recouvrement 0,08.
Le bout rond est un demi-cercle biseauté comme le reste du fil. Cœur et dragées = la même `Piece` sur un contour fermé (tous les
bords biseautés). Pièces rondes en tours de pans, une tuile par pan (éclairage lissé, spirale).

Repère (catégorie objets, Recette) : plan (a le long du manche, b en travers, z = normale vue de l'inventaire) posé sur la
diagonale du bloc, manche du bas à gauche vers le haut à droite, bras +b vers le haut à gauche, bras -b vers le bas à droite,
comme iron_pickaxe.png ; boîte centrée ; Display vanilla item/handheld, gui ramené à la case. Une étape : groupe racine `repos`.

Objet vivant (guide 14), doux et rebondi :
- item_idle (24 s) : le cœur bat (double battement toutes les 4 s, `scale` : seul dépliage de ce groupe), les dragées s'avivent
  au battement (ctrl_lumiere), le nuage du pommeau flotte ; à 20 s, « soupir » : grand battement, bouffée de six cœurs de sucre
  `trans_coeurs` (cachés huit fois plus petits dans le cœur, seul dépliage par `scale` de ce groupe) qui montent et s'effacent
  (ctrl_alpha), emit_mc_heart (ctrl_emit) et **le seul son** du skin : `pof_sucre` embarqué (sons/pof_sucre.py, original, repris
  de la Lame Câline) à 20,04 s, une fois par boucle de 24 s (outil : un son au repos, boucle >= 20 s) ;
- item_swing (0,3 s, minage) : la tête se dandine, le pommeau bat la mesure, dragées vives, particules coupées ; sans son ;
- event_select (0,7 s) : « plop » du nuage du pommeau 0 -> 1,25 -> 0,92 -> 1 (seul dépliage par `scale` de ce groupe), la tête
  se dandine, les dragées s'allument ;
- event_swing (0,4 s) : la tête et le pommeau suivent en retard (rotation amortie) ;
- event_break (0,8 s) : bloc cassé : « boing » de la tête, dragées vives, cœurs de Minecraft (ctrl_emit +5) ; sans son.
Aucun son sur event_use_start ni event_enter_* (il n'y en a pas), aucun son aux événements.

Fonctions avancées : calque _e, trans_coeurs, ctrl_alpha, ctrl_lumiere, emit_mc_heart + ctrl_emit, scale animé, son embarqué,
animations d'objet. Non simulés par l'aperçu : animations en main, particules, ctrl_emit, ctrl_lumiere, son. À juger en jeu :
item_swing et event_break (pas encore vérifiés par le développeur), le son d'un objet au repos, lecture du croissant dans la case.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

AVEC_E = True
NOM = "skin_pioche_kawaii"
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

# Palette du set (.claude/styles/kawaii.md ; langage des objets Kawaii, reprise de la Lame Câline)
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


def bez(P, s):
    P = [np.array(p, float) for p in P]
    u = 1 - s
    c = u ** 3 * P[0] + 3 * u * u * s * P[1] + 3 * u * s * s * P[2] + s ** 3 * P[3]
    d = 3 * u * u * (P[1] - P[0]) + 6 * u * s * (P[2] - P[1]) + 3 * s * s * (P[3] - P[2])
    return c, d / np.linalg.norm(d)


# ------------------------------------------------------------------ dessin (plan a, b ; px)
A_O = 17.6                                  # centre du cœur-œil
SX_C = 1.1                                  # cœur un peu plus gros que la garde de l'épée (il porte tout le fer)
O_ = np.array((A_O - 0.2, 0.0))             # pivot de la tête (centre du cœur, un peu bas)
ARM = [(A_O + 0.05, 0.95), (A_O + 0.05, 3.3), (A_O - 0.45, 5.4), (A_O - 2.4, 7.0)]   # bras +b : racine dans le lobe, se recourbe vers le manche
Z_E = 0.10                                  # demi-épaisseur au fil
T_BIS = 1.0                                 # pente unique des biseaux (45°)
Z_FOND = 0.16                               # fond de la gouttière
R_HIDE = 1.0                                # fil retiré à moins de R_HIDE de la racine (dans le cœur)
H_RAC, H_BOUT = 0.76, 0.30                  # demi-épaisseur du plat : 1,60 px près du cœur -> 0,60 px au bout rond


def w_bras(s):
    return 0.55 + 0.75 * (1 - s) ** 0.8


class Bras:
    """Plaque biseautée fermée : contour poly, fil (polyligne sans la racine cachée dans le cœur), plat z = h0 + k (P - O)·u,
    gouttière creusée le long de la ligne médiane entre g0 et g1 (bords gl, gr ; axe gax)."""

    def __init__(self, nom, sig, g0=0.36, g1=0.86, gw=0.31):
        self.nom, self.sig = nom, sig
        M = lambda p: np.array((p[0], sig * p[1]))
        self.O = M(ARM[0])
        ext, inn, cen = [], [], []
        for s in np.linspace(0, 1, 48):
            c, d = bez(ARM, s)
            c, d = M(c), M(d)
            no = sig * np.array((d[1], -d[0]))                      # vers +a (dessus du croissant)
            ext.append(c + no * (w_bras(s) - 0.25 * (1 - s) ** 3))
            inn.append(c - no * (w_bras(s) - 0.5 * (1 - s) ** 3))     # côté manche plus mince à la racine (caché dans le cœur)
            cen.append(c)
        c1, d1 = bez(ARM, 1.0)
        c1, d1 = M(c1), M(d1)
        no1 = sig * np.array((d1[1], -d1[0]))
        w1 = w_bras(1.0)
        cap = [tuple(c1 + w1 * (math.cos(f) * no1 + math.sin(f) * d1)) for f in np.linspace(0, math.pi, 11)[1:-1]]
        E, I = resample(ext, 0.9), resample(inn, 0.9)
        self.poly = E + cap + I[::-1]
        hors = lambda pts: [p for p in pts if np.linalg.norm(np.array(p) - self.O) >= R_HIDE]
        self.fil = hors(E) + cap + hors(I)[::-1]
        self.segs = subdiv(self.fil, 0.9)
        tip = c1 + d1 * w1
        self.u = unit(tip - self.O)
        self.L = float((tip - self.O) @ self.u)
        self.k = (H_BOUT - H_RAC) / (self.L - R_HIDE)
        self.h0 = H_RAC - self.k * R_HIDE
        self.centre = [tuple(c) for c in cen] + [tuple(tip)]
        gax, gl, gr = [], [], []
        for j, s in enumerate(np.linspace(g0, g1, 14)):
            c, d = bez(ARM, s)
            c, d = M(c), M(d)
            no = sig * np.array((d[1], -d[0]))
            v = j / 13
            w = gw * math.sin(math.pi * v) ** 0.6 + 0.012
            gax.append(tuple(c))
            gl.append(tuple(c + no * w))
            gr.append(tuple(c - no * w))
        self.gax, self.gl, self.gr = gax, gl, gr
        self.gpoly = gl + gr[::-1]

    def bez(self, s):
        c, d = bez(ARM, s)
        return np.array((c[0], self.sig * c[1])), np.array((d[0], self.sig * d[1]))

    def h(self, P):
        return self.h0 + self.k * ((np.asarray(P, float) - self.O) @ self.u)

    def wb(self, P):
        return np.maximum((self.h(P) - Z_E) / T_BIS, 0.02)

    def dE(self, P):
        return d_stack(P, self.segs).min(0)

    def surf(self, P):
        P = np.asarray(P, float)
        return np.minimum(self.h(P), Z_E + T_BIS * self.dE(P))

    def in_g(self, P):
        return in_poly(P, self.gpoly)

    def d_g(self, P):
        return d_poly(P, list(self.gpoly) + [self.gpoly[0]])

    def d_ax(self, P):
        return d_poly(P, self.gax)


BRAS = [Bras("bras_h", 1), Bras("bras_b", -1)]


# --- peintures des bras (sucre lilas mat, fil crème, bande rose bonbon, liseré lilas foncé ; aucune lumière)
def peint_biseau_bras(pc, P2, d):
    f = np.clip(d / pc.wb(P2), 0, 1.2)[..., None]
    col = lerp(LILAS["hi"], LILAS["base"] * 1.04, np.clip((f - 0.42) / 0.45, 0, 1))
    col = np.where(f < 0.42, lerp(BONBON, LILAS["hi"], np.clip((f - 0.30) / 0.12, 0, 1)), col)
    col = np.where(f < 0.17, CREME + np.zeros_like(col), col)
    col = np.where(f >= 0.9, LISERE + np.zeros_like(col), col)
    return col * (1 + grain(P2, 1.0 + pc.sig))[..., None], None


def peint_fil_bras(pc, P2):
    return np.zeros(P2.shape[:-1] + (3,), np.float32) + CREME, None


def peint_plat_bras(pc, P2, d):
    wb = pc.wb(P2)
    k = np.clip(0.45 + 0.25 * (P2[..., 0] - A_O + 1.0) / 2.5, 0, 1)[..., None]     # +a (dessus du croissant) un peu plus clair
    col = lerp(LILAS["base"], LILAS["hi"], k * 0.55) * (1 + grain(P2, 2.0 + pc.sig))[..., None]
    col[d < wb + 0.05] = LISERE
    dg = pc.d_g(P2)
    out = ~pc.in_g(P2)
    col[(dg < 0.09) & out] = CREME                                  # lèvre crème de la gouttière
    col[(dg >= 0.09) & (dg < 0.14) & out] = LILAS["low"]
    return col, None


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
SPECS = []
TILES = {}          # nom -> (rgba, rgba_e | None)
TRANS = set()       # tuiles semi-transparentes (groupes trans_ seulement)


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


def dans_coeur(P2):
    """Intérieur du cœur-œil à plus de 0,45 px de son bord : le bras y est caché (et son plat, plus haut près de la racine,
    percerait le cœur)."""
    return in_poly(P2, COEUR) & (d_poly(P2, COEUR + [COEUR[0]]) > 0.45)


def volume_bras(pc, groupe):
    """Plaque biseautée fermée opaque : deux biseaux par tronçon de fil (un par face), un plat incliné par face."""
    AL = math.atan(T_BIS)
    for idx, (p, q, v0, v1) in enumerate(pc.segs):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        pm = (p + q) / 2
        cand = np.array([pm + n * 0.25, pm - n * 0.25])
        prof = np.where(in_poly(cand, pc.poly), d_poly(cand, list(pc.poly) + [pc.poly[0]]), -1.0)
        if prof[1] > prof[0]:
            n = -n
        wmax = float(max(pc.wb(p[None])[0], pc.wb(q[None])[0]))
        e0 = wmax * 1.3 if v0 else 0.04
        e1 = wmax * 1.3 if v1 else 0.04
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

            def haut(P, idx=idx):
                P2 = P[..., :2]
                D = d_stack(P2, pc.segs)
                de = D.min(0)
                own = D[idx] <= de + RECOUV
                m = in_poly(P2, pc.poly) & own & (de < pc.wb(P2) + 0.03) & ~dans_coeur(P2)
                col, em = peint_biseau_bras(pc, P2, de)
                return col, em, m

            def fil(P, idx=idx, n=n):
                P2 = P[..., :2] + n * 0.04
                D = d_stack(P2, pc.segs)
                own = D[idx] <= D.min(0) + RECOUV
                m = in_poly(P2, pc.poly) & own & ~dans_coeur(P2)
                col, em = peint_fil_bras(pc, P2)
                return col, em, m

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

        def plat(P):
            P2 = P[..., :2]
            de = pc.dE(P2)
            m = (in_poly(P2, pc.poly) & (de >= pc.wb(P2) - 0.03) & ~dans_coeur(P2) & ~pc.in_g(P2))
            col, em = peint_plat_bras(pc, P2, de)
            return col, em, m

        spec(groupe, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, ((s1 - s0) * math.sqrt(1 + pc.k ** 2), t1 - t0, TH), {"south": plat})


def gouttiere_bras(pc, groupe):
    """Gouttière creusée : trou dans les plats (alpha), parois de sucre par tronçon et par face, fond lavande, lèvre crème."""
    gp = np.array(pc.gpoly)
    a0, a1 = gp[:, 0].min() - 0.15, gp[:, 0].max() + 0.15
    b0, b1 = gp[:, 1].min() - 0.15, gp[:, 1].max() + 0.15

    def fond(P):
        P2 = P[..., :2]
        m = pc.in_g(P2) | (pc.d_g(P2) < 0.1)
        dc = pc.d_ax(P2)
        col = lerp(LAVANDE["base"], LAVANDE["low"], np.clip(dc / 0.35, 0, 1)[..., None]) + np.zeros(P.shape[:-1] + (3,), np.float32)
        return col, None, m

    spec(groupe, f"{pc.nom}_fond", ((a0 + a1) / 2, (b0 + b1) / 2, 0.0), (1, 0, 0), (0, 1, 0), (a1 - a0, b1 - b0, 2 * Z_FOND),
         {"south": fond, "north": fond})
    murs = [(pts[i], pts[i + 1]) for pts in (pc.gl, pc.gr) for i in range(len(pts) - 1)]
    for j, (p, q) in enumerate(murs):
        p, q = np.asarray(p, float), np.asarray(q, float)
        Ln = float(np.linalg.norm(q - p))
        if Ln < 0.02:
            continue
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        mid = (p + q) / 2
        if pc.in_g(np.array([mid + n * 0.03]))[0]:
            n = -n                                                   # n vers l'extérieur de la gouttière
        back = [p + n * TH, q + n * TH, mid + n * TH]
        top = min(float(pc.surf(np.array([x]))[0]) for x in back + [p, q, mid]) - 0.03
        z0 = Z_FOND - 0.04
        if top - z0 < 0.06:
            continue
        for sg in (1, -1):
            zc = sg * (z0 + top) / 2
            X = np.array((d[0], d[1], 0.0))
            Y = np.array((0.0, 0.0, 1.0))
            Z = np.cross(X, Y)
            face = "south" if Z[:2] @ n < 0 else "north"

            def paroi(P):
                P2 = P[..., :2]
                dz = pc.h(P2) - np.abs(P[..., 2])
                col = lerp(LILAS["base"], LAVANDE["low"], np.clip((dz[..., None] - 0.1) / 0.3, 0, 1)) + np.zeros(P.shape[:-1] + (3,), np.float32)
                col[dz < 0.1] = CREME
                return col, None, np.ones(P.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zc)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec(groupe, f"{pc.nom}_paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


# --- cœur-œil (framboise) : plaque « coussin » fermée, tous les bords biseautés
H_C, ZE_C, WB_C = 1.1, 0.32, 0.92
A_G = A_O
COEUR = coeur_poly(1.05, 0.5, 1.2, -1.85, 0.42, n=48, oy=A_G, sx=SX_C)
REFLET = (A_G + 0.66, 1.15)                  # fenêtre de reflet sur le lobe +b (haut en main et dans la case)


def reflet_coeur(P, col):
    """Grande fenêtre de reflet (ellipse le long du lobe +b, barre de fenêtre) et petit contre-reflet lumineux, biseau et plat."""
    a, b = P[..., 0], P[..., 1]
    col = np.array(col, np.float32)
    em = np.zeros(P.shape[:-1] + (3,), np.float32)
    da, db = a - REFLET[0], b - REFLET[1]
    u = (da * 0.6 + db * 0.8)
    v = (-da * 0.8 + db * 0.6)
    fen = (u / 0.68) ** 2 + (v / 0.28) ** 2 < 1
    col[fen] = BLANC
    col[fen & (np.abs(u + 0.08) < 0.05)] = FRAMB["hi"]
    cr = np.hypot(a - (A_G - 1.0), b + 1.15) < 0.19
    col[cr] = A((255, 220, 236))
    em[cr] = (210, 150, 186)
    return col, em


def peint_biseau_coeur(P, dE):
    f = np.clip(dE / WB_C, 0, 1)[..., None]
    dirn = np.stack([P[..., 0] - (A_G - 0.2), P[..., 1]], -1)
    dirn = dirn / np.maximum(np.linalg.norm(dirn, axis=-1, keepdims=True), 1e-6)
    lum = np.clip(0.5 + 0.5 * (dirn @ np.array((0.707, 0.707))), 0, 1)[..., None]
    col = lerp(FRAMB["low"], lerp(FRAMB["base"], FRAMB["hi"], 0.3), np.clip(f * 1.15, 0, 1)) * (0.9 + 0.2 * lum)
    col = np.where(f < 0.1, FRAMB["low"] * 0.92, col)
    col, _ = reflet_coeur(P, col)
    return col, None


def peint_plat_coeur(P, dE):
    a, b = P[..., 0], P[..., 1]
    k = np.clip(0.45 + 0.2 * ((a - A_G) + b) / 2.4, 0, 1)[..., None]
    col = lerp(lerp(FRAMB["base"], FRAMB["hi"], 0.3), FRAMB["hi"], k) + np.zeros(P.shape[:-1] + (3,), np.float32)
    return reflet_coeur(P, col)


def peint_fil_coeur(P):
    return np.zeros(P.shape[:-1] + (3,), np.float32) + FRAMB["low"] * 0.85, None


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

COEUR_P = Piece("coeur", COEUR, [COEUR + [COEUR[0]]], cst(H_C), cst(WB_C), ZE_C, peint_biseau_coeur, peint_plat_coeur,
                peint_fil_coeur, maxlen=0.6)


# --- dragées-cœurs (sucre rose, lumière _e) serties dans les gouttières, lobes vers le bout du bras
H_D, ZE_D, WB_D = 0.36, 0.20, 0.20
S_DRAG = (0.52, 0.72)                        # abscisses (paramètre de la courbe) des dragées sur chaque bras


def dragee_piece(nom, pc, s):
    c, d = pc.bez(s)
    no = pc.sig * np.array((d[1], -d[0]))                       # vers +a
    loc = coeur_poly(1.0, 0.45, 1.15, -1.6, 0.45, n=18, sx=0.145)   # (y, x) : y vers les lobes
    poly = [tuple(c + d * (y + 0.03) + no * x) for y, x in loc]
    hp = c + d * 0.07 + no * 0.11                                  # reflet blanc sur le lobe du dessus

    def plat(P, dE):
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE
        em = np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE_E
        hl = np.hypot(P[..., 0] - hp[0], P[..., 1] - hp[1]) < 0.075
        col[hl] = BLANC
        em[hl] = (225, 200, 215)
        return col, em

    def bis(P, dE):
        return (np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE, np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE_E)

    def fil(P):
        return (np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE * 0.86, np.zeros(P.shape[:-1] + (3,), np.float32) + DRAGEE_E * 0.8)

    return Piece(nom, poly, [poly + [poly[0]]], cst(H_D), cst(WB_D), ZE_D, bis, plat, fil, maxlen=0.6)


DRAGEES_P = [dragee_piece(f"dragee_{pc.nom}{i}", pc, s) for pc in BRAS for i, s in enumerate(S_DRAG)]


def conception():
    SPECS.clear()
    for pc in BRAS:
        volume_bras(pc, "bras")
        gouttiere_bras(pc, "bras")
    volume(COEUR_P, "coeur", prolonge=0.6)
    for pc in DRAGEES_P:
        volume(pc, "dragees", prolonge=0.6)


conception()


def _marges():
    """Marge plat/gouttière (px) le long de chaque bras : demi-largeur du plat - demi-largeur de la gouttière."""
    out = []
    for pc in BRAS:
        for c, l in zip(pc.gax[1:-1], pc.gl[1:-1]):
            c, l = np.array(c), np.array(l)
            dE = float(pc.dE(c[None])[0])
            out.append(dE - float(pc.wb(c[None])[0]) - float(np.linalg.norm(l - c)))
    return min(out)


_marge = _marges()


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

# pommeau = nuage de quatre bosses (a, b, rayon)
NUAGES_P = [(0.0, 0.0, 1.0), (0.45, 0.92, 0.7), (0.45, -0.92, 0.7), (-0.85, 0.0, 0.62)]
C_COEURS = (A_G + 0.2, 0.0)                 # centre de la bouffée de cœurs (cachée dans le cœur)
BOUFFEE = [(-60, 2.6, 1.5), (-25, 3.2, 1.8), (8, 2.7, 1.4), (38, 3.3, 1.7), (72, 2.5, 1.35), (105, 2.1, 1.15)]
R_MANCHE = 0.62


def build(theta, P0):
    elements.clear()
    groups.clear()
    Repere.th, Repere.P0 = theta, np.asarray(P0, float)
    out = {}
    nz = V(0, 0, 1)
    ax = Wv(1, 0)
    racine = group("repos", W_(3.5, 0), nom=objet.etape("repos", "pioche"))
    pioche = group("pioche", W_(3.5, 0), parent=racine)
    # --- tête : cœur-œil, bras de sucre lilas (volume, gouttières), dragées-cœurs serties
    tete = group("tete", W_(A_O - 1.0, 0), parent=pioche)
    bras = group("bras", W_(*O_), parent=tete)
    drag = group("dragees", W_(*O_), parent=bras)
    group("ctrl_lumiere_dragees", W_(*O_), parent=drag, nom="ctrl_lumiere")
    coeur = group("coeur", W_(A_G, 0), parent=tete)
    group("ctrl_lumiere_coeur", W_(A_G, 0), parent=coeur, nom="ctrl_lumiere")
    for sp in SPECS:
        g = {"bras": bras, "dragees": drag, "coeur": coeur}[sp["groupe"]]
        boite(g, sp["nom"], W_(*sp["c"]), Wv(*sp["X"]), Wv(*sp["Y"]), sp["s"], sp["faces"])
    # --- manche de guimauve torsadée entre deux bagues lavande (la pointe du cœur se pose sur la bague haute)
    poi = group("poignee", W_(3.5, 0), parent=pioche)
    a_h = A_O - 2.95
    tour(poi, "manche", W_(0, 0), ax, nz, [(0.95, R_MANCHE, A_O - 1.0, R_MANCHE, "guimauve", {"pas": 1.3})], n=12)
    tour(poi, "bague_b", W_(0, 0), ax, nz, [(0.75, 0.48, 0.8, 0.78, "lavande", {}), (0.8, 0.78, 1.22, 0.78, "lavande", {"arete": True}),
                                           (1.22, 0.78, 1.26, 0.6, "lavande", {})], n=12)
    tour(poi, "bague_h", W_(0, 0), ax, nz, [(a_h - 0.04, 0.6, a_h, 0.8, "lavande", {}), (a_h, 0.8, a_h + 0.5, 0.8, "lavande", {"arete": True}),
                                           (a_h + 0.5, 0.8, a_h + 0.56, 0.52, "lavande", {})], n=12)
    npo = group("nuage_pommeau", W_(0.9, 0), parent=pioche)
    for k, (a, b, r) in enumerate(NUAGES_P):
        boule(npo, f"np{k}_", W_(a, b), r)
    # --- bouffée de cœurs (trans_), F_GEO / KC de sa taille, cachée dans le cœur ; point de cœurs de Minecraft
    CC = W_(*C_COEURS)
    f = F_GEO / KC
    tc = group("trans_coeurs", CC, parent=pioche)
    for k, (ang, dist, sz) in enumerate(BOUFFEE):
        dirn = Wv(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        boite(tc, f"bouffee{k}", CC + dirn * dist * f + nz * (0.03 * k - 0.08) * f, V(1, 0, 0), V(0, 1, 0), (sz * f, sz * f, 0.3 * f),
              {"south": "coeur_t", "north": "coeur_t"})
    group("ctrl_alpha_coeurs", CC, parent=tc, nom="ctrl_alpha")
    up = W_(A_G + 1.3, 0)
    em = group("emit_mc_heart", up, parent=pioche)
    group("ctrl_emit", up, parent=em)
    out.update(racine=racine, pioche=pioche, tete=tete, coeur=coeur, pommeau=npo, coeurs=tc, dragees=drag)
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

K = float(os.environ.get("K", "1.0"))
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


def plop(t, t0):
    if t <= t0:
        return 0.0
    x = t - t0
    if x < 0.16:
        return 1.25 * sm(x, 0.0, 0.16)
    if x < 0.3:
        return lerp(1.25, 0.92, sm(x, 0.16, 0.3))
    return lerp(0.92, 1.0, sm(x, 0.3, 0.45))


TETE, COEUR_G, NPO, TC, DRG = F["tete"], F["coeur"], F["pommeau"], F["coeurs"], F["dragees"]
CLD, CLC, CE, CA = "ctrl_lumiere_dragees", "ctrl_lumiere_coeur", "ctrl_emit", "ctrl_alpha_coeurs"

# --- item_idle (24 s) : double battement toutes les 4 s, soupir à 20 s (bouffée de cœurs, son), pommeau qui flotte
L_IDLE = 24.0
BATS = [0.8, 4.8, 8.8, 12.8, 16.8]
T_S = 20.0                                   # soupir : grand battement, bouffée de cœurs, seul son


def battement(t):
    v = 0.0
    for tb in BATS:
        v += bump(t, tb, tb + 0.08, tb + 0.12, tb + 0.3) + 0.6 * bump(t, tb + 0.3, tb + 0.38, tb + 0.42, tb + 0.66)
    return v + 1.6 * bump(t, T_S, T_S + 0.1, T_S + 0.16, T_S + 0.45)


def idle_coeur(t):
    b = battement(t)
    return 1 + 0.07 * b, 1 + 0.07 * b, 1 - 0.03 * b              # gonfle à plat, s'aplatit un peu (volume à peu près constant)


def coeurs_scale(t, t0=T_S):
    w = sm(t, t0 + 0.03, t0 + 0.22) * (1 - sm(t, t0 + 1.24, t0 + 1.27))
    k = 1 + (KC / F_GEO - 1) * w
    return k, k, k


def coeurs_pos(t, t0=T_S):
    v = V(0, 1.8, 0) * sm(t, t0 + 0.1, t0 + 1.2) * (1 - sm(t, t0 + 1.24, t0 + 1.27))
    return float(v[0]), float(v[1]), float(v[2])


item_idle = anim("item_idle", L_IDLE, {
    (COEUR_G, "scale"): idle_coeur,
    (NPO, "position"): lambda t: (0.0, 0.06 * math.sin(TAU * t / L_IDLE * 6 + 1.6), 0.0),
    (CLD, "position"): lambda t: (0.35 * battement(t), 0.0, 0.0),
    (TC, "scale"): coeurs_scale, (TC, "position"): coeurs_pos,
    (CA, "position"): lambda t: (-sm(t, T_S + 0.55, T_S + 1.15) * (1 - sm(t, T_S + 1.3, T_S + 1.35)), 0.0, 0.0),
    (CE, "position"): lambda t: (-1.0 + 5.0 * bump(t, T_S + 0.03, T_S + 0.06, T_S + 0.3, T_S + 0.45), 0.0, 0.0)}, fps=20)

# --- item_swing (0,3 s, boucle pendant le minage) : la tête se dandine, le pommeau bat la mesure, dragées vives ; particules coupées
L_ISW = 0.3
item_swing = anim("item_swing", L_ISW, {
    (TETE, "rotation"): lambda t: (0.0, 0.0, 2.0 * math.sin(TAU * t / L_ISW)),
    (NPO, "rotation"): lambda t: (0.0, 0.0, -4.0 * math.sin(TAU * t / L_ISW - 0.9)),
    (CLD, "position"): lambda t: (0.25 + 0.15 * math.cos(TAU * t / L_ISW), 0.0, 0.0),
    (CE, "position"): lambda t: (-1.0, 0.0, 0.0)}, fps=40)

# --- event_select (0,7 s) : plop du nuage du pommeau (0 -> 1,25 -> 0,92 -> 1), la tête se dandine, les dragées s'allument
L_SEL = 0.7
event_select = anim("event_select", L_SEL, {
    (NPO, "scale"): lambda t: (plop(t, 0.04),) * 3,
    (TETE, "rotation"): lambda t: (0.0, 0.0, ressort(t, 0.08, 5.0, f=3.2, amort=0.18)),
    (CLD, "position"): lambda t: (-1.0 + 1.0 * sm(t, 0.15, 0.3) + 0.5 * bump(t, 0.3, 0.36, 0.42, 0.65), 0.0, 0.0)}, fps=40, loop="once")

# --- event_swing (0,4 s) : la tête et le pommeau suivent en retard
L_SW = 0.4
event_swing = anim("event_swing", L_SW, {
    (TETE, "rotation"): lambda t: (0.0, 0.0, ressort(t, 0.02, -4.0, f=4.0, amort=0.1) * (t < 0.39)),
    (NPO, "rotation"): lambda t: (0.0, 0.0, ressort(t, 0.04, 5.0, f=4.0, amort=0.1) * (t < 0.39))}, fps=40, loop="once")

# --- event_break (0,8 s) : bloc cassé : « boing » de la tête, dragées vives, cœurs de Minecraft ; sans son
L_BRK = 0.8
event_break = anim("event_break", L_BRK, {
    (TETE, "rotation"): lambda t: (0.0, 0.0, ressort(t, 0.02, 6.0, f=4.0, amort=0.14) * (t < 0.78)),
    (CE, "position"): lambda t: (5 * bump(t, 0.03, 0.06, 0.3, 0.45), 0.0, 0.0),
    (CLD, "position"): lambda t: (0.9 * sm(t, 0.0, 0.04) * (1 - sm(t, 0.1, 0.6)), 0.0, 0.0),
    (CLC, "position"): lambda t: (0.6 * sm(t, 0.0, 0.04) * (1 - sm(t, 0.1, 0.5)), 0.0, 0.0)}, fps=40, loop="once")

ANIMS = [item_idle, item_swing, event_select, event_swing, event_break]
ANIMS[0]["selected"] = True

# ------------------------------------------------------------------ écriture
assert len(elements) <= 8192, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
_lo, _hi = P[:, :2].min(0), P[:, :2].max(0)
GUI = float(os.environ.get("GUI", "0")) or round(min(0.85, 16.4 / float(max(_hi - _lo))), 3)
AFFICHAGE = objet.affichage("pioche", gui={"scale": [GUI] * 3})
model = objet.modele(NOM, "pioche", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, embarquer_sons  # noqa: E402
limiter_sons(model)
# Un seul son, au soupir du repos (outil : un son dans item_idle, boucle de 24 s) ; tools/sons.py ne connaît pas les
# événements d'objet : remis ici, à 20,04 s. Aucun son ailleurs.
embarquer_sons(model, {"pof_sucre": "sons/pof_sucre.ogg"})
item_idle["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "pof_sucre", "file": ""}], "time": T_S + 0.04}]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur sur la diagonale {LONGUEUR:.1f} px ; largeur {LARGEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)} ;"
      f" gui {GUI} ; marge plat/gouttière mini {_marge:.2f} px")
