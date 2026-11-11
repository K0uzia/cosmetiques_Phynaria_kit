"""Hache de l'orage : skin d'objet (guide 14) pour toutes les haches du joueur, ensemble Orage (thème Éléments). Design original.
Écrit skin_hache_orage.png, skin_hache_orage_e.png et .build/skin_hache_orage_brut.bbmodel à côté de ce script.

Références (fiche .claude/references/objets/haches.md) : anatomie d'une vraie hache (fer : fil, pointe, talon, joues,
œil, douille, barbe ; manche). Silhouette d'une hache barbue à une main : tranchant long et convexe, barbe qui descend le long
du manche (le fil fait presque deux fois la hauteur de la douille), talon court. Traduction pour l'Orage (.claude/styles/orage.md) :
- barbe découpée en marches d'éclair (même grammaire que les ailerons du casque), liseré d'or le long des marches ;
- joue fendue par un éclair : une gouttière en zigzag part du tambour d'or aux trois virgules (à l'œil) et court vers le fil
  sans l'atteindre ; au fond, un vrai trait de foudre en géométrie (cœur opaque blanc à bord bleu + calque _e, gaine add_) ;
- acier d'orage bleu-noir martelé, fil poli presque blanc (+ _e), trempe cuivre puis violet derrière le fil (famille Orage) ;
- talon en éperon d'éclair (deux marches), douille d'acier, poignée de cuir bleu nuit entre deux bagues d'or, pommeau à bague
  d'or et pointe de cristal d'orage (_e), comme l'épée et la pioche.
Vrai volume (F3, retour en jeu du 2026-11-08 14 h 22 : « c'est des couches » ; recette .claude/references/objets/volume-3d.md,
prototype skin_epee_orage validé en jeu à 15 h 05) : la lame (tranchant, joues, barbe) est une plaque biseautée fermée : deux
biseaux par tronçon de bord (≤ 1 px sur les courbes, sommets des marches gardés vifs) et par face, à pente unique de 40° (fer
large de 6 px : il reste un grand plat) ; un plat incliné par face qui s'amincit vers le fil (1,60 px à l'œil -> 0,60 px au fil,
avant K) ; le dos et les marches de la barbe ont le même biseau (liseré d'or), le tranchant est poli et trempé. Talon : même
recette, pente de 50° (éperon étroit). Fente de foudre = gouttière creusée dans le plat de la joue (parois, fond où la foudre
est couchée). Tambour d'or à 16 pans aux virgules posé sur la joue ; douille octogonale ; manche octogonal (« le manche est bien »).
Repère (catégorie objets, Recette) : construite dans un plan (a le long du manche, b vers le tranchant), posée sur la diagonale
du bloc, fer en haut à droite, tranchant vers le haut à gauche comme l'image vanilla de la hache (vue de +Z), centrée dans le bloc.
Display vanilla de item/handheld (tools/objet.py), échelle gui réglée pour la case. Une étape : groupe racine `repos`.

Objet vivant (guide 14), format free, sobre :
- item_idle (boucle) : la gaine de l'éclair de la fente vacille (Molang, 9 Hz), petites fourches sur la joue au hasard, un arc
  en retour toutes les 3 à 8 s.
- event_select (0,6 s) : la fente se charge (la gaine monte), un arc parcourt le fil une fois, de la pointe à la barbe.
- event_swing (0,35 s) : la fente s'avive pendant le coup, une fourche (ne déplie rien).
- event_hit (0,7 s) : un arc saute de la fente au fil et **court sur le fil** dans les deux sens (pointe et barbe), puis trois
  arcs en retour sur tout le fil (formes alternées), frisson de 2,5° ; **le seul son** (embarqué, original : arc_hache).
- item_gui : gaine au repos, rien d'autre (inventaire calme).
Arcs et fourches **repliés à 1/10 sur un pivot caché dans le métal** au repos (invisibles figés : inventaire, animations coupées,
aperçus ; l'ancienne version laissait une frange blanche le long du fil) et dépliés par `scale` ×10 ; allumés par ctrl_alpha.
Chaque groupe replié n'est déplié que par une seule animation (échelles qui se multiplient sinon) : item_idle = fourches ;
event_select = son propre jeu d'arcs du fil ; event_hit = saut + un autre jeu d'arcs du fil ; event_swing ne déplie rien.
Pas de particules. Fonctions avancées : add_, ctrl_alpha, scale animé, calque _e, animations d'objet (item_idle, item_gui,
event_select, event_swing, event_hit), Molang (q.life_time), son embarqué. À juger en jeu : event_hit et son son (pas encore
vérifiés par le développeur), scale et ctrl_alpha sur un objet, lisibilité des arcs add_ de jour, lecture du fer par la tranche.
"""
import base64, io, json, math, os, random, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image, ImageDraw

NOM = "skin_hache_orage"
TEX = 512
TAU = 2 * math.pi
DENS = 20.0                     # texels par px sur les plaques
FOLD = 0.1                      # pièces repliées sur leur pivot au repos

METAL = np.array([(22, 24, 36), (46, 52, 72), (70, 78, 104), (112, 122, 154), (170, 182, 214)], np.float32)
OR = np.array([(130, 90, 30), (176, 128, 44), (220, 170, 60), (255, 230, 140)], np.float32)
CRIS = np.array([(40, 40, 120), (70, 90, 200), (130, 160, 255), (190, 208, 255), (232, 240, 255)], np.float32)
CUIR = np.array([(18, 20, 38), (34, 40, 70), (52, 62, 104)], np.float32)
CUIVRE = np.array((196, 118, 64), np.float32)
VIOLET = np.array((112, 88, 172), np.float32)


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




# ------------------------------------------------------------------ dessin du fer (plan a le long du manche, b vers le tranchant ; px)
HS = 0.82                        # échelle du fer autour de l'œil
EYE = np.array((16.7, 0.0))


def hs(pts):
    return [tuple(EYE + (np.array(p, float) - EYE) * HS) for p in pts]


TOP = hs([(18.6, 0.7), (18.9, 2.2), (19.5, 3.9), (20.2, 5.4), (20.9, 6.6)])                        # dos du tranchant
EDGE = hs([(20.9, 6.6), (20.3, 7.2), (19.0, 7.6), (17.2, 7.85), (15.2, 7.8), (13.3, 7.4), (11.6, 6.65), (10.3, 5.65), (9.3, 4.5)])
BEARD = hs([(9.3, 4.5), (10.9, 4.0), (10.5, 3.0), (12.6, 2.3), (12.3, 1.4), (14.2, 0.7)])          # marches d'éclair
LAME = TOP + EDGE[1:] + BEARD[1:]
TALON = [(18.4, -0.7), (18.1, -1.6), (17.3, -1.95), (17.75, -2.55), (16.25, -3.45), (16.4, -2.45), (15.85, -2.15),
         (15.55, -1.35), (15.1, -0.7)]
MED_C, MED_R = np.array((16.75, 1.75)), 0.92                                                  # tambour d'or à l'œil
TAMBOUR = EYE + (MED_C - EYE) * HS
SLIT = hs([(16.45, 2.6), (15.05, 3.75), (16.65, 4.35), (14.85, 5.8), (15.9, 6.4)])               # fente en éclair


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


def m_tete(P):
    return in_poly(P, LAME) | in_poly(P, TALON)

# ------------------------------------------------------------------ vrai volume (.claude/references/objets/volume-3d.md)
# Fer à section réelle : la lame (tranchant, joues, barbe) et le talon sont des plaques biseautées fermées (deux biseaux par
# tronçon de bord et par face, un plat incliné par face qui s'amincit vers le fil). Les couleurs du fil, du poli, de la trempe
# et du liseré d'or sont peintes SUR les faces des volumes ; chaque face est échantillonnée texel par texel dans le plan de la
# hache et découpée par l'alpha. Fente de foudre = gouttière creusée (parois + fond) dans le plat de la joue.
def unit(v):
    return v / np.linalg.norm(v)


Z_E = 0.12                        # demi-épaisseur au bord (fil) ; tout est réduit par K = 0,86 ensuite
DF = 16.0                         # texels par px sur les faces des volumes
TH = 0.35                         # épaisseur des cubes de biseau, de plat, de paroi (0,30 après K)
RECOUV = 0.08                     # recouvrement des faces voisines
T_BIS = 0.85                      # pente unique de la lame (40°, recette) : fer large (6 px), il reste un grand plat
T_TAL = 1.2                       # talon étroit (éperon de 0,6 à 1,2 px) : pente plus raide (50°)
R_D = 0.8                         # rayon de la douille (œil)
O_ = EYE


def resample(pts, pas):
    """Polyligne ré-échantillonnée en tronçons de longueur ~pas (bouts gardés)."""
    P = np.array(pts, float)
    ls = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    n = max(1, int(round(ls[-1] / pas)))
    out = []
    for x in np.linspace(0, ls[-1], n + 1):
        i = min(np.searchsorted(ls, x, side="right") - 1, len(P) - 2)
        k = (x - ls[i]) / max(ls[i + 1] - ls[i], 1e-9)
        out.append(P[i] + (P[i + 1] - P[i]) * k)
    return [tuple(p) for p in out]


def hors_collet(pts, marge=0.55):
    """Garde la polyligne à partir du premier point à moins de `marge` à l'intérieur du collet."""
    for i, p in enumerate(pts):
        if np.linalg.norm(np.array(p) - O_) >= R_COL - marge:
            return pts[max(0, i - 1):]
    return pts


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


class Piece:
    """Plaque biseautée : contour `poly`, fils `fils` (polylignes, sans la base cachée), plat plan z = h0 + k (P - O)·u,
    bord à z = ze, pente de biseau t ; z0 décale toute la pièce (attelles), `cotes` = faces construites (+1, -1)."""

    def __init__(self, nom, poly, fils, O, u, h0, k, ze, peint_biseau, peint_plat, peint_fil, trou=None, t=T_BIS, z0=0.0,
                 cotes=(1, -1), trempe=None):
        self.nom, self.poly, self.O, self.u, self.h0, self.k, self.ze, self.t = nom, poly, np.array(O, float), unit(np.array(u, float)), h0, k, ze, t
        self.segs = [s for f in fils for s in subdiv(f)]
        self.peint_biseau, self.peint_plat, self.peint_fil, self.trou = peint_biseau, peint_plat, peint_fil, trou
        self.z0, self.cotes, self.trempe = z0, cotes, trempe

    def h(self, P):
        return self.h0 + self.k * ((np.asarray(P, float) - self.O) @ self.u)

    def wb(self, P):
        return np.maximum((self.h(P) - self.ze) / self.t, 0.02)

    def dE(self, P):
        return d_stack(P, self.segs).min(0)

    def surf(self, P):
        d, h, wb = self.dE(P), self.h(P), self.wb(P)
        return np.where(d < wb, self.ze + (h - self.ze) * np.clip(d / wb, 0, 1), h)


SPECS = []          # cubes du volume : dict(groupe, nom, c, X, Y, s, faces) en coordonnées du plan
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


def spec(groupe, nom, c, X, Y, s, peintures, dens=DF):
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
    SPECS.append({"groupe": groupe, "nom": nom, "c": np.asarray(c, float), "X": X, "Y": Y, "s": s, "faces": faces})


def volume(pc, groupe):
    """Biseaux (deux par tronçon de fil) + plats inclinés de la pièce pc."""
    for idx, (p, q, v0, v1) in enumerate(pc.segs):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        if not in_poly(np.array([(p + q) / 2 + n * 0.05]), pc.poly)[0]:
            n = -n
        pm = (p + q) / 2
        h, wb = float(pc.h(pm)), float(pc.wb(pm))
        al = math.atan2(h - pc.ze, wb)
        e0 = wb * 1.3 if v0 else 0.04
        e1 = wb * 1.3 if v1 else 0.04
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        sy = (wb + 0.08) / math.cos(al)
        for sg in pc.cotes:
            Y = np.array((n[0] * math.cos(al), n[1] * math.cos(al), sg * math.sin(al)))
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0], mid[1], pc.z0 + sg * pc.ze)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(P, idx=idx):
                P2 = P[..., :2]
                D = d_stack(P2, pc.segs)
                dE = D.min(0)
                m = in_poly(P2, pc.poly) & (D[idx] <= dE + RECOUV) & (dE < pc.wb(P2) + 0.03)
                col, em = pc.peint_biseau(pc, P2, dE)
                return col, em, m

            def fil(P, idx=idx, n=n):
                P2 = P[..., :2] + n * 0.06
                D = d_stack(P2, pc.segs)
                m = in_poly(P2, pc.poly) & (D[idx] <= D.min(0) + RECOUV)
                col, em = pc.peint_fil(pc, P2)
                return col, em, m

            spec(groupe, f"{pc.nom}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil})
    # plats : une plaque par face, inclinée le long de u pour suivre l'amincissement (dessus à z = z0 ± h)
    u = pc.u
    pp = np.array((-u[1], u[0]))
    pa = np.array(pc.poly) - pc.O
    s_, t_ = pa @ u, pa @ pp
    s0, s1, t0, t1 = s_.min() - 0.05, s_.max() + 0.05, t_.min() - 0.05, t_.max() + 0.05
    Pc = pc.O + u * (s0 + s1) / 2 + pp * (t0 + t1) / 2
    for sg in pc.cotes:
        X = unit(np.array((u[0], u[1], sg * pc.k)))
        Y = sg * np.array((pp[0], pp[1], 0.0))
        Z = np.cross(X, Y)
        c = np.array((Pc[0], Pc[1], pc.z0 + sg * float(pc.h(Pc)))) - Z * (TH / 2)

        def plat(P):
            P2 = P[..., :2]
            dE = pc.dE(P2)
            m = in_poly(P2, pc.poly) & (dE >= pc.wb(P2) - 0.03)
            if pc.trou is not None:
                m &= ~pc.trou(P2)
            col, em = pc.peint_plat(pc, P2, dE)
            return col, em, m

        spec(groupe, f"{pc.nom}_plat{'pm'[sg < 0]}", c, X, Y, ((s1 - s0) * math.sqrt(1 + pc.k ** 2), t1 - t0, TH), {"south": plat})




# --- gouttière : zigzag de la fente, demi-largeur par sommet (pointue au bout côté fil ; le départ est sous le tambour)
GW = [0.16, 0.30, 0.31, 0.28, 0.08]
Z_FOND = 0.19                     # fond de 0,38 px (0,33 après K)


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
                pts.append((p2 + p3) / 2)
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

# --- peintures (couleurs portées par les faces des volumes)
def bandes_trempe(pc, P):
    """Bouts de travail trempés : distance au bout -> (poli, cuivre, violet, filet sombre), comme l'ancienne version."""
    if pc.trempe is None:
        return None
    d, (j0, j1, j2, j3) = pc.trempe(P)
    return d, j0, j1, j2, j3


def appliquer_trempe(pc, P, col):
    bt = bandes_trempe(pc, P)
    if bt is None:
        return np.zeros(P.shape[:-1], bool)
    d, j0, j1, j2, j3 = bt
    po = d < j0
    col[po] = lerp(METAL[4], np.array((236, 244, 255), np.float32), np.clip(1 - d[po] / j0, 0, 1)[..., None])
    cu = (d >= j0) & (d < j1)
    col[cu] = lerp(col[cu], CUIVRE, 0.85)
    vi = (d >= j1) & (d < j2)
    col[vi] = lerp(col[vi], VIOLET, 0.7)
    col[(d >= j2) & (d < j3)] = METAL[0]
    return d < j3


def peint_biseau_fer(pc, P, dE):
    f = dE / pc.wb(P)
    nz = cellules(P, 2.2, 1.0)[..., None]
    col = lerp(METAL[3], METAL[2], np.clip((f[..., None] - 0.70) / 0.2, 0, 1)) + nz * 10
    col = np.where((f < 0.3)[..., None], lerp(METAL[4], METAL[3], np.clip((f[..., None] - 0.08) / 0.22, 0, 1)) + nz * 6, col)
    em = np.zeros(col.shape, np.float32)
    tr = appliquer_trempe(pc, P, col)
    orl = (f >= 0.44) & (f < 0.66) & ~tr                       # liseré d'or sur le biseau, hors des bouts trempés
    col[orl] = OR[2]
    col[orl & (f < 0.52)] = OR[3]
    col[f >= 0.93] = METAL[0]                                   # arête du plat : trait d'ombre net
    bt = bandes_trempe(pc, P)
    vif = (f < 0.16) & (bt[0] < bt[2]) if bt is not None else np.zeros(f.shape, bool)
    col[vif] = (236, 244, 255)
    em[vif] = (110, 150, 235)
    return col, em


def peint_fil_fer(pc, P):
    col = np.zeros(P.shape[:-1] + (3,), np.float32) + METAL[4]
    em = np.zeros_like(col)
    bt = bandes_trempe(pc, P)
    if bt is not None:
        vif = bt[0] < bt[2]
        col[vif] = (236, 244, 255)
        em[vif] = (110, 150, 235)
    return col, em


def peint_plat_fer(pc, P, dE):
    wb = pc.wb(P)
    nz = cellules(P, 1.6, 2.0)[..., None]
    col = lerp(METAL[2], METAL[1], np.clip((dE[..., None] - wb[..., None] - 0.1) / 0.5, 0, 1) * 0.6) + nz * 16
    appliquer_trempe(pc, P, col)
    col[dE < wb + 0.04] = METAL[0]
    em = np.zeros(col.shape, np.float32)
    if pc.trou is not None:
        dg = d_gout(P)
        levre = dg < 0.07
        col[levre] = (190, 208, 255)
        em[levre] = (60, 100, 210)
        col[(dg >= 0.07) & (dg < 0.13)] = METAL[0]
        orl = (dg >= 0.19) & (dg < 0.27) & (dE > wb + 0.1)
        col[orl] = OR[2]
        col[orl & (dg < 0.22)] = OR[3]
    return col, em


def peint_biseau_att(pc, P, dE):
    f = dE / pc.wb(P)
    nz = cellules(P, 2.4, 6.0)[..., None]
    col = lerp(METAL[4], METAL[3], np.clip(f[..., None] / 0.7, 0, 1)) + nz * 8
    col[f >= 0.9] = METAL[1]
    return col, np.zeros(col.shape, np.float32)


def peint_fil_att(pc, P):
    col = np.zeros(P.shape[:-1] + (3,), np.float32) + METAL[3]
    return col, np.zeros_like(col)


def peint_plat_att(pc, P, dE):
    nz = cellules(P, 1.8, 7.0)[..., None]
    col = lerp(METAL[3], METAL[2], 0.55) + nz * 14 + np.zeros(P.shape[:-1] + (3,), np.float32)
    col[dE < pc.wb(P) + 0.04] = METAL[1]
    return col, np.zeros(col.shape, np.float32)




# --- pièces du fer : lame (tranchant + joues + barbe) et talon
FIL_LAME = resample(TOP, 1.0) + resample(EDGE, 1.0)[1:] + BEARD[1:]      # sommets des marches gardés vifs
C_EDGE = np.array(EDGE[len(EDGE) // 2], float)
U_L = unit(C_EDGE - O_)
L_L = float((C_EDGE - O_) @ U_L)
H_L0, H_L1 = 0.80, 0.30                      # demi-épaisseur à la douille -> au fil (1,60 -> 0,60 px avant K)
K_L = (H_L1 - H_L0) / (L_L - R_D)
LAME_P = Piece("lame", LAME, [FIL_LAME], O_, U_L, H_L0 - K_L * R_D, K_L, Z_E, peint_biseau_fer, peint_plat_fer,
               peint_fil_fer, trou=in_gout, t=T_BIS, trempe=lambda P: (d_poly(P, EDGE), (0.34, 0.6, 0.86, 0.94)))
U_T = np.array((0.0, -1.0))
H_T0, H_T1 = 0.66, 0.36                      # talon : 1,32 px à la douille -> 0,72 px au bout de l'éperon
L_T = 3.45
K_T = (H_T1 - H_T0) / (L_T - R_D)
TALON_P = Piece("talon", TALON, [TALON], O_, U_T, H_T0 - K_T * R_D, K_T, Z_E, peint_biseau_fer, peint_plat_fer, peint_fil_fer,
                t=T_TAL)


def conception():
    SPECS.clear()
    TILES.clear()
    volume(LAME_P, "fer")
    gouttiere(LAME_P, "fer")
    volume(TALON_P, "fer")

def gouttiere(pc, groupe):
    """Fond (âme de 0,32 px où repose la foudre) + parois verticales le long des deux bords, sur chaque face."""
    pa = np.array(GOUT)
    box = (pa[:, 0].min() - 0.15, pa[:, 0].max() + 0.15, pa[:, 1].min() - 0.15, pa[:, 1].max() + 0.15)

    def fond(P):
        P2 = P[..., :2]
        m = in_gout(P2) | (d_gout(P2) < 0.1)
        col = np.zeros(P.shape[:-1] + (3,), np.float32) + np.array((16, 18, 34), np.float32) + cellules(P2, 3.0, 5.0)[..., None] * 6
        em = np.zeros_like(col) + np.array((14, 22, 70), np.float32)
        return col, em, m

    a0, a1, b0, b1 = box
    spec(groupe, "fond", ((a0 + a1) / 2, (b0 + b1) / 2, 0.0), (1, 0, 0), (0, 1, 0), (a1 - a0, b1 - b0, 2 * Z_FOND),
         {"south": fond, "north": fond})
    murs = []
    for sg, pts in GOUT_COTES.items():
        for i in range(len(pts) - 1):
            murs.append((pts[i], pts[i + 1]))
    murs.append((GOUT_COTES[1][0], GOUT_COTES[-1][0]))
    murs.append((GOUT_COTES[1][-1], GOUT_COTES[-1][-1]))
    for j, (p, q) in enumerate(murs):
        p, q = np.asarray(p, float), np.asarray(q, float)
        if np.linalg.norm(q - p) < 0.03:
            continue
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
                dz = pc.h(P2) - np.abs(P[..., 2])
                col = lerp(METAL[1], METAL[0], np.clip((dz[..., None] - 0.1) / 0.3, 0, 1)) + np.zeros(P.shape[:-1] + (3,), np.float32)
                em = np.zeros_like(col)
                lv = dz < 0.1
                col[lv] = (190, 208, 255)
                em[lv] = (60, 100, 210)
                return col, em, np.ones(P.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zc)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec(groupe, f"paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


def controle_gouttiere():
    """Marge entre la gouttière et le bord du plat du bec (doit rester > 0)."""
    pts = np.array([p for c in GOUT_COTES.values() for p in c])
    marge = LAME_P.dE(pts) - LAME_P.wb(pts)
    return float(marge.min())


def disque16(N, R_apo, ss=4, peindre=None):
    """Tuile d'une face de prisme à 16 pans (apothème R_apo, tuile de côté 2 R_apo / cos(11,25°))."""
    Rc = R_apo / math.cos(math.pi / 16)
    M = N * ss
    yy, xx = np.mgrid[0:M, 0:M]
    X = ((xx + 0.5) / M * 2 - 1) * Rc
    Y = (1 - (yy + 0.5) / M * 2) * Rc
    th = np.arctan2(Y, X)
    r = np.hypot(X, Y)
    sect = np.mod(th, TAU / 16) - TAU / 32
    apo = r * np.cos(sect)
    col = peindre(np.stack([X, Y], -1), r, apo)
    m = apo <= R_apo
    a = np.zeros((M, M, 4), np.float32)
    a[..., :3] = col
    a[..., 3] = m * 255
    im = np.array(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").resize((N, N), Image.BOX))
    im[..., 3] = (im[..., 3] > 128) * 255
    im[im[..., 3] == 0] = 0
    return im


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


# ------------------------------------------------------------------ atlas
UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    core, core_e = t_core()
    cri, cri_e = t_cristal()
    conception()
    items = [(n, im, ime) for n, (im, ime) in TILES.items()]
    items += [("medaillon", medaillon(), None), ("cuir", t_cuir(), None), ("core", core, core_e),
              ("cristal", cri, cri_e), ("halo", t_halo(), None), ("crk", t_crk(), None),
              ("metal", t_unie(64, 12, METAL[3], METAL[1], 2, bords=METAL[4]), None),
              ("hampe", t_unie(64, 12, METAL[2], METAL[0], 6, bords=METAL[3]), None),
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
    print(f"atlas : {len(items)} tuiles, hauteur utilisée {y + shelf}/{TEX} ; marge gouttière/plat {controle_gouttiere():.3f} px")
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


def unit(v):
    return v / np.linalg.norm(v)


def euler(R):
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def rmat(rx, ry, rz):
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


class Repere:
    """Plan (a, b, z) de la hache -> monde : rotation theta autour de Z, puis translation P0."""
    th, P0 = 0.0, V(0, 0, 0)

    @classmethod
    def p(cls, a, b, z=0.0):
        c, s = math.cos(cls.th), math.sin(cls.th)
        return cls.P0 + V(c * a - s * b, s * a + c * b, z)

    @classmethod
    def v(cls, a, b, z=0.0):
        c, s = math.cos(cls.th), math.sin(cls.th)
        return V(c * a - s * b, s * a + c * b, z)


W_, Wv = Repere.p, Repere.v


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups, name
    assert len(name.split("#")[0]) <= 64
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [float(v) for v in rotation]}
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
    """Boîte centrée en c (monde), axes X, Y (monde), tailles sx, sy, sz."""
    X = unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    cube(g, name, c - (sx / 2, sy / 2, sz / 2), c + (sx / 2, sy / 2, sz / 2), c, euler(R_), faces)


def plaque(g, name, box, tile, th):
    """Plaque du plan (a, b) couvrant box = (a0, a1, b0, b1), découpée par l'alpha de la tuile ; tranches transparentes."""
    a0, a1, b0, b1 = box
    u0, v0, u1, v1 = UV[tile]
    boite(g, name, W_((a0 + a1) / 2, (b0 + b1) / 2), Wv(1, 0), Wv(0, 1), a1 - a0, b1 - b0, th,
          {"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def strip(tile, caps=True):
    u0, v0, u1, v1 = UV[tile]
    lg = [u0, v0, u1, v1]
    end = [u0 + 1, v0 + 1, u0 + 3, v0 + 3] if caps else CLEAR
    return {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end}


def barre(g, name, a0, a1, r, tile, b=0.0, octo=True, caps=True):
    """Barre le long du manche (axe a), section r ; octogonale (deux cubes à 45°)."""
    Ln = a1 - a0
    c = W_((a0 + a1) / 2, b)
    X, Y = Wv(1, 0), Wv(0, 1)
    boite(g, name, c, X, Y, Ln, 2 * r, 2 * r, strip(tile, caps))
    if octo:
        Yq = unit(Y * math.cos(math.pi / 4) + V(0, 0, 1) * math.sin(math.pi / 4))
        boite(g, name + "o", c, X, Yq, Ln - 0.1, 2 * r * 0.97, 2 * r * 0.97, strip(tile, caps))


def seg(g, name, p, q, w, tile, ov=0.06, roll=45.0):
    """Tronçon de trait (monde) de p à q, section w × w tournée de roll autour de l'axe."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = V(0, 0, 1) if abs(X[2]) < 0.9 else V(1, 0, 0)
    Y0 = unit(ref - (ref @ X) * X)
    Z0 = np.cross(X, Y0)
    r = math.radians(roll)
    Y = Y0 * math.cos(r) + Z0 * math.sin(r)
    Ln = float(np.linalg.norm(q - p))
    boite(g, name, (p + q) / 2, X, Y, Ln + 2 * ov, w, w, strip(tile, caps=tile != "halo"))


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
    """Éclair qui suit une polyligne (plan a, b) : n tronçons irréguliers, écarts latéraux alternés ; renvoie des points (a, b, z)."""
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


def le_long(pts):
    P = [np.array(p, float) for p in pts]
    ls = np.cumsum([0] + [np.linalg.norm(P[i + 1] - P[i]) for i in range(len(P) - 1)])

    def at(t):
        x = t * ls[-1]
        i = min(np.searchsorted(ls, x, side="right") - 1, len(P) - 2)
        return P[i] + (P[i + 1] - P[i]) * (x - ls[i]) / max(ls[i + 1] - ls[i], 1e-9)
    return at


def exterieur(pts, dist):
    """Polyligne décalée de dist vers l'extérieur du fer."""
    out = []
    P = [np.array(p, float) for p in pts]
    for i, p in enumerate(P):
        d = unit(P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)])
        n = np.array((-d[1], d[0]))
        if m_tete(np.array([p + n * 0.08]))[0]:
            n = -n
        out.append(tuple(p + n * dist))
    return out


def bone_node(name):
    g = groups[name]
    return {"name": name.split("#")[0], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


def sous_groupes(g):
    out = [g]
    for n, gg in groups.items():
        if gg["parent"] == g:
            out += sous_groupes(n)
    return out


def replier(g):
    """Replie toute la géométrie du groupe à FOLD autour de son pivot (dépliée par scale 1/FOLD dans les animations)."""
    o = np.array(groups[g]["origin"])
    ids = {i for n in sous_groupes(g) for i in groups[n]["ids"]}
    for e in elements:
        if e["uuid"] in ids:
            for k in ("from", "to", "origin"):
                e[k] = [round(float(o[i] + FOLD * (e[k][i] - o[i])), 4) for i in range(3)]


N_FIL = 6
NG = 3


def eclair_branche(g, nom, p0, d, Ln, seed, w0=0.26, w1=0.14, branches=1, J=0.22):
    """Éclair ramifié (plan a, b) depuis p0 dans la direction d : tronc + `branches` fourches."""
    rng = random.Random(seed)
    p0 = np.array(p0, float)
    q = p0 + d * Ln
    zz = zigzag([tuple(p0), tuple(q)], 5, J, seed, zj=0.12)
    trait(g, f"{nom}t", [W_(*p) for p in zz], w0, w1, "crk")
    for j in range(branches):
        i = 2 + j
        b0 = np.array(zz[i][:2])
        sg = 1 if (seed + j) % 2 == 0 else -1
        an = math.radians(rng.uniform(30, 50)) * sg
        bd = np.array((d[0] * math.cos(an) - d[1] * math.sin(an), d[0] * math.sin(an) + d[1] * math.cos(an)))
        bz = zigzag([tuple(b0), tuple(b0 + bd * Ln * rng.uniform(0.35, 0.5))], 3, J * 0.6, seed * 3 + j, z0=zz[i][2])
        trait(g, f"{nom}b{j}", [W_(*p) for p in bz], w1 * 0.95, w1 * 0.7, "crk")


def tourner(d, deg):
    a = math.radians(deg)
    return np.array((d[0] * math.cos(a) - d[1] * math.sin(a), d[0] * math.sin(a) + d[1] * math.cos(a)))


def poser_specs(cibles):
    """Pose les cubes du volume (SPECS) dans les groupes `cibles` (nom de spec -> groupe)."""
    for sp in SPECS:
        u_ = {}
        for f in ("north", "south", "east", "west", "up", "down"):
            if f in sp["faces"]:
                u0, v0, u1, v1 = UV[sp["faces"][f]]
                u_[f] = [u0, v0, u1, v1]
            else:
                u_[f] = CLEAR
        boite(cibles[sp["groupe"]], sp["nom"], W_(*sp["c"]), Wv(*sp["X"]), Wv(*sp["Y"]), *sp["s"], u_)


def prisme16(g, nom, R, zh, tile_cote, tile_face, C=None):
    """Prisme à 16 pans autour de l'œil : 16 parois de TH (côtés `tile_cote`), deux faces découpées par l'alpha."""
    C = O_ if C is None else np.asarray(C, float)
    cote = 2 * R * math.tan(math.pi / 16)
    for k in range(16):
        th = TAU * k / 16
        nrm = np.array((math.cos(th), math.sin(th)))
        tg = np.array((-nrm[1], nrm[0]))
        c = C + nrm * (R - TH / 2)
        u0, v0, u1, v1 = UV[tile_cote]
        boite(g, f"{nom}{k}", W_(c[0], c[1]), Wv(*tg), V(0, 0, 1), cote + 0.03, 2 * zh, TH,
              {"south": [u0, v0, u1, v1], "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
    u0, v0, u1, v1 = UV[tile_face]
    Rc = R / math.cos(math.pi / 16)
    for sg in (1, -1):
        fc = {"south": [u0, v0, u1, v1]} if sg > 0 else {"north": [u1, v0, u0, v1]}
        boite(g, f"{nom}_face{'pm'[sg < 0]}", W_(C[0], C[1], sg * (zh - TH / 2)), Wv(1, 0), Wv(0, 1), 2 * Rc, 2 * Rc, TH,
              {**{f: CLEAR for f in ("north", "south", "east", "west", "up", "down")}, **fc})




def decaler(pts, dist):
    """Polyligne décalée vers l'extérieur du fer (dist > 0) ou vers l'intérieur (dist < 0) ; EDGE tourne dans le sens horaire."""
    out = []
    P = [np.array(p, float) for p in pts]
    for i, p in enumerate(P):
        d = unit(P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)])
        out.append(tuple(p + np.array((d[1], -d[0])) * dist))
    return out


N_FIL = 7
NG = 3
FIL_EXT = decaler(EDGE, 0.2)                 # arcs juste au-dehors du fil
FIL_INT = decaler(EDGE, -0.6)                # pivots des arcs, cachés dans le métal (arcs repliés au repos)


def build(theta, P0):
    elements.clear()
    groups.clear()
    _rc[0] = 0
    Repere.th, Repere.P0 = theta, np.asarray(P0, float)
    out = {}
    racine = group(objet.etape("repos", "hache"), W_(4.0, 0))
    hache = group("hache", W_(4.0, 0), racine)
    # --- manche : pommeau à bague d'or et pointe de cristal, poignée de cuir entre bagues d'or, hampe d'acier (famille Orage)
    manche = group("manche", W_(4.0, 0), hache)
    barre(manche, "pommeau", -0.35, 0.9, 0.86, "metal")
    barre(manche, "pom_bague", 0.08, 0.44, 0.94, "or")
    barre(manche, "pom_cri", -1.25, -0.3, 0.46, "cristal")
    barre(manche, "pom_cri2", -1.75, -1.2, 0.24, "cristal", octo=False)
    barre(manche, "bague1", 0.9, 1.32, 0.78, "or")
    barre(manche, "poignee", 1.3, 7.42, 0.67, "cuir")
    barre(manche, "bague2", 7.4, 7.82, 0.75, "or")
    barre(manche, "hampe", 7.8, 14.4, 0.58, "hampe")
    barre(manche, "bague3", 14.35, 14.75, 0.72, "or")
    # --- fer : douille (œil), lame et talon en vrai volume, tambour d'or à 16 pans posé sur la joue
    fer = group("fer", W_(16.6, 0), hache)
    a0d, a1d = 14.72, 18.65
    barre(fer, "douille", a0d + 0.35, a1d, R_D, "metal")
    barre(fer, "douille_b", a0d, a0d + 0.4, 0.68, "sombre")
    barre(fer, "chapeau", 18.6, 19.15, 0.66, "or")
    barre(fer, "chapeau2", 19.1, 19.45, 0.4, "metal", octo=False)
    poser_specs({"fer": fer})
    zt = float(LAME_P.h(TAMBOUR)) + 0.2
    prisme16(fer, "tambour", MED_R, zt, "or", "medaillon", C=TAMBOUR)
    # --- foudre de la fente : cœur opaque + _e couché au fond de la gouttière, gaine add_ en NG sections
    foudre = group("foudre", W_(*SLIT[0]), fer)
    pts2 = zigzag(SLIT, 4 * NG, 0.04, 11)
    pts = [W_(*p) for p in pts2]
    for zs in (1, -1):                            # couchée sur le fond (z ±0,19) de chaque côté : dessus à 0,40, sous la lèvre
        for i in range(len(pts) - 1):
            seg(foudre, f"eclair{'pm'[zs < 0]}{i}", pts[i] + V(0, 0, zs * 0.2), pts[i + 1] + V(0, 0, zs * 0.2),
                0.40 - 0.10 * i / (len(pts) - 2), "core", roll=0.0)
    out["gaines"] = []
    per = (len(pts) - 1) // NG
    for k in range(NG):
        gg = group(f"add_gaine_{k}", tuple(pts[k * per]), foudre)
        ctrl(gg)
        for i in range(k * per, (k + 1) * per):
            pm = np.array(((pts2[i][0] + pts2[i + 1][0]) / 2, (pts2[i][1] + pts2[i + 1][1]) / 2))
            seg(gg, f"gaine{i}", pts[i], pts[i + 1], min(0.8, 2 * float(LAME_P.h(pm)) - 0.14), "halo", ov=0.04, roll=0.0)
        out["gaines"].append(gg)
    # --- fourches sur le plat de la joue (faces avant et arrière), dépliées par l'état seulement ; pivot dans le tambour
    out["fourches"] = []
    on_slit = le_long(SLIT)
    for v in range(2):
        fg = group(f"add_fourche_{'ab'[v]}", W_(*SLIT[0]), foudre)
        ctrl(fg)
        rng = random.Random(40 + v)
        for k in range(4):
            t = (k + 0.3 + 0.4 * rng.random()) / 4
            p = on_slit(t)
            d = unit(on_slit(min(1, t + 0.02)) - p)
            side = 1 if (k + v) % 2 == 0 else -1
            dirn = tourner(d, rng.uniform(35, 70) * side)
            q = p + dirn * rng.uniform(0.8, 1.3)
            for zs in (1, -1):
                zz = zigzag([p + dirn * 0.4, q], 3, 0.15, 70 + 10 * v + k)
                trait(fg, f"f{k}{'pm'[zs < 0]}", [W_(x, y, zs * (float(LAME_P.surf(np.array([(x, y)]))[0]) + 0.07)) for x, y, _ in zz],
                      0.18, 0.13, "crk")
        replier(fg)
        out["fourches"].append(fg)
    # --- arcs du fil : un jeu pour event_select, un jeu (saut + fil) pour event_hit ; pivots cachés dans le métal
    arcs = group("arcs_fil", W_(*SLIT[-1]), fer)
    end = np.array(SLIT[-1])
    on_edge = le_long(EDGE)
    t_j = min(np.linspace(0, 1, 200), key=lambda t: np.linalg.norm(on_edge(t) - end))
    out["t_jonction"] = t_j
    out["saut"] = []
    for v in range(2):
        g = group(f"add_saut_{'ab'[v]}", W_(*SLIT[-1]), arcs)
        ctrl(g)
        e_ = on_edge(t_j)
        zz = zigzag([tuple(end), tuple(e_ + unit(e_ - end) * 0.24)], 3, 0.25, 90 + v)
        trait(g, "s", [W_(*p) for p in zz], 0.3, 0.24, "crk")
        replier(g)
        out["saut"].append(g)
    at_ext, at_int = le_long(FIL_EXT), le_long(FIL_INT)
    for jeu, graine in (("sel", 300), ("hit", 100)):
        out[jeu] = []
        for k in range(N_FIL):
            t0, t1 = k / N_FIL, (k + 1) / N_FIL
            sous = [tuple(at_ext(t)) for t in np.linspace(t0, t1, 4)]
            g = group(f"add_fil_{jeu}{k}", W_(*at_int((t0 + t1) / 2)), arcs)
            ctrl(g)
            zz = zigzag(sous, 4, 0.16, graine + 7 * k, zj=0.08)
            trait(g, "a", [W_(*p) for p in zz], 0.24, 0.2, "crk")
            replier(g)
            out[jeu].append((g, k, (t0 + t1) / 2))
    out["racine"], out["hache"] = racine, hache
    for e in elements:
        for k in ("from", "to", "origin"):
            e[k] = [round(float(P0[i] + K * (e[k][i] - P0[i])), 4) for i in range(3)]
    for gg in groups.values():
        gg["origin"] = [round(float(P0[i] + K * (gg["origin"][i] - P0[i])), 4) for i in range(3)]
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


K = float(os.environ.get("K", "0.86"))   # échelle globale (longueur ~19 px sur la diagonale, vanilla ≈ 16,3)
THETA = math.radians(45)          # axe du manche sur la diagonale du bloc ; b (tranchant) vers le haut à gauche, comme la vanilla
build(THETA, V(0, 0, 0))
P = coins()
CENTRE = (P.min(axis=0) + P.max(axis=0)) / 2
F = build(THETA, V(8, 8, 8) - CENTRE)
P = coins()
D_ = np.array((1, 1, 0)) / math.sqrt(2)
LONGUEUR = float((P @ D_).max() - (P @ D_).min())
LARGEUR = float((P @ np.array((-1, 1, 0)) / math.sqrt(2)).max() - (P @ np.array((-1, 1, 0)) / math.sqrt(2)).min())
outliner = [bone_node(F["racine"])]


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


def restrike(P, pr, c2):
    """v.r = 1 pendant trois arcs en retour (60 ms, séparés de 60 ms) d'une tranche de P s tirée avec la probabilité pr."""
    return (f"v.u=q.life_time/{P:g}+{c2:.3g};v.s={H('math.floor(v.u)')};v.u=math.mod(v.u,1)*{P:g};"
            f"v.r=(v.s<{pr:g})*((v.u<0.07)+(v.u>0.13)*(v.u<0.19)+(v.u>0.26)*(v.u<0.32));")


def flick(R, c):
    return f"v.h={H(f'math.floor(q.life_time*{R:g}+{c:.3g})')};"


P_RS, PR_RS = 5.5, 0.6            # un arc en retour toutes les ~3 à 8 s


def gaine_idle(k):
    return chk(restrike(P_RS, PR_RS, 0.37) + flick(9, 0.13 + 0.31 * k) + "-0.38+0.22*(v.h<0.3)-0.25*(v.h>0.82)+0.7*v.r")


def fourche_idle(v):
    cond = "(v.h<0.1)" if v == 0 else "(v.h>0.9)"
    return chk(restrike(P_RS, PR_RS, 0.37) + flick(6, 0.29 + 1.7 * v) + f"math.max({cond},v.r)-1")


def onoff(intervalles, Ln, on=1.0, off=-1.0, r=0.012):
    """Clés ctrl_alpha : off, puis on pendant chaque intervalle (a, b) ; rampes de r s."""
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




GAINES = F["gaines"]
FOURCHES = F["fourches"]
SAUT = F["saut"]
FSEL = F["sel"]
FHIT = F["hit"]
TJ = F["t_jonction"]
TOUS = [g for g, _, _ in FSEL + FHIT] + SAUT + FOURCHES


def eteindre(an, sauf=()):
    for g in TOUS:
        if g not in sauf:
            piste_ctrl(an, g, [kf("position", 0, -1)])


# item_idle : la fente vit (gaine qui vacille, fourches au hasard) ; arcs du fil repliés et éteints.
idle = anim("item_idle", 8.0)
for k, g in enumerate(GAINES):
    piste_ctrl(idle, g, [kf("position", 0, gaine_idle(k))])
for v, fg in enumerate(FOURCHES):
    deplier(idle, fg)
    piste_ctrl(idle, fg, [kf("position", 0, fourche_idle(v))])
eteindre(idle, sauf=FOURCHES)

# item_gui : inventaire calme (gaine au repos, rien d'autre).
gui = anim("item_gui", 4.0)
for g in GAINES:
    piste_ctrl(gui, g, [kf("position", 0, -0.3)])
eteindre(gui)

# event_select (0,6 s) : la fente se charge, un arc parcourt le fil de la pointe à la barbe (jeu « sel »).
L_SEL = 0.6
sel = anim("event_select", L_SEL, "once")
for k, g in enumerate(GAINES):
    piste_ctrl(sel, g, [kf("position", t, -0.6 * (1 - sm(t, 0.0, 0.2)) + 0.9 * bump(t, 0.18 + 0.02 * k, 0.24 + 0.02 * k, 0.3, 0.55))
                         for t in np.round(np.linspace(0, L_SEL, 13), 4)])
for g, k, t in FSEL:
    deplier(sel, g)
    t0 = 0.22 + 0.035 * k
    piste_ctrl(sel, g, onoff([(t0, t0 + 0.07)], L_SEL))
piste_ctrl(sel, FOURCHES[1], onoff([(0.2, 0.26)], L_SEL))

# event_swing (0,35 s) : la fente s'avive pendant le coup, une fourche (ne déplie rien).
L_SW = 0.35
sw = anim("event_swing", L_SW, "once")
for k, g in enumerate(GAINES):
    t0 = 0.02 * k
    piste_ctrl(sw, g, [kf("position", t, 0.6 * bump(t, t0, t0 + 0.04, t0 + 0.1, t0 + 0.32)) for t in np.round(np.linspace(0, L_SW, 15), 4)])
piste_ctrl(sw, FOURCHES[0], onoff([(0.03, 0.09)], L_SW))

# event_hit (0,7 s) : l'arc saute de la fente au fil et court sur le fil dans les deux sens, puis trois arcs en retour (jeu « hit »).
L_HIT = 0.7
hit = anim("event_hit", L_HIT, "once")
RESTRIKES = [(0.24, 0.29, 1), (0.34, 0.38, 0), (0.44, 0.47, 1)]
for v, g in enumerate(SAUT):
    deplier(hit, g)
    iv = [(0.0, 0.1)] if v == 0 else []
    iv += [(a, b) for j, (a, b, vv) in enumerate(RESTRIKES) if (v == 1) == (j == 1)]   # saut : forme a, puis b, puis a
    piste_ctrl(hit, g, onoff(iv, L_HIT))
for g, k, t in FHIT:
    deplier(hit, g)
    t0 = 0.05 + 0.32 * abs(t - TJ)                   # front qui s'éloigne de la jonction (~0,03 s par tronçon)
    iv = [(t0, t0 + 0.09)]
    for j, (a, b, vv) in enumerate(RESTRIKES):       # tout, puis un tronçon sur deux, puis le milieu (les bouts s'éteignent d'abord)
        if j == 0 or (j == 1 and k % 2 == 1) or (j == 2 and abs(t - TJ) < 0.3):
            iv.append((a, b))
    piste_ctrl(hit, g, onoff(iv, L_HIT))
for g in GAINES:
    piste_ctrl(hit, g, [kf("position", t, 1.2 * sm(t, 0.0, 0.02) * (1 - sm(t, 0.08, 0.6))
                         + 0.4 * sum(bump(t, a - 0.01, a, b, b + 0.02) for a, b, _ in RESTRIKES)) for t in np.round(np.linspace(0, L_HIT, 36), 4)])
for v, fg in enumerate(FOURCHES):
    piste_ctrl(hit, fg, onoff([(0.0, 0.12)] + [(a, b) for a, b, vv in RESTRIKES if vv == v], L_HIT))
piste(hit, F["hache"], [kf("rotation", t, 0, 0, 2.5 * math.sin(TAU * t / 0.07) * (1 - sm(t, 0.0, 0.28))) for t in np.round(np.linspace(0, 0.3, 19), 4)]
      + [kf("rotation", L_HIT, 0, 0, 0)])

ANIMS = [idle, gui, sel, sw, hit]

# ------------------------------------------------------------------ écriture
assert 80 <= len(elements) <= 2500, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
GUI = float(os.environ.get("GUI", "0.86"))
AFFICHAGE = objet.affichage("hache", gui={"scale": [GUI] * 3})
model = objet.modele(NOM, "hache", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, embarquer_sons, cle_son
limiter_sons(model)
embarquer_sons(model, {"arc_hache": "sons/arc_hache.ogg"})
# Un seul son, au coup qui touche (event_hit) : tools/sons.py ne connaît pas encore les événements d'objet, on le pose après.
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "arc_hache")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur sur la diagonale {LONGUEUR:.1f} px ; largeur {LARGEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)}")
