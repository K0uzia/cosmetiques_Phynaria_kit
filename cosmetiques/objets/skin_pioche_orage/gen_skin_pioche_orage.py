"""Pic de l'orage : skin d'objet (guide 14) pour toutes les pioches du joueur, ensemble Orage (thème Éléments). Design original.
Écrit skin_pioche_orage.png, skin_pioche_orage_e.png et .build/skin_pioche_orage_brut.bbmodel à côté de ce script.

Référence réelle (.claude/references/objets/pioches-marteaux-pneumatiques.md, Pic de mineur) : fer d'acier forgé à œil central
traversé par le manche, coin enfoncé au-dessus de l'œil, deux bras recourbés vers le manche (croissant) : une **pointe** pour
attaquer la roche, un **tranchant plat** (pic-hache) ; attelles (langets) d'acier rivetées le long du manche sous l'œil ; les
bouts de travail sont trempés (couleurs de revenu derrière le fil), le reste reste brut de forge.
Famille Orage (ailes_orage v7, skin_epee_orage, skin_hache_orage, skin_masse_orage, skin_lance_orage ; .claude/styles/orage.md) :
- acier d'orage bleu-noir martelé, arêtes polies claires, liseré d'or en retrait du bord (comme la garde de l'épée) ;
- bouts de travail polis presque blancs (+ _e), bande de revenu cuivre puis violet derrière (comme les rémiges et le fil de l'épée) ;
- œil = tambour d'or aux trois virgules (seul ornement, comme la garde de l'épée et la joue de la hache), coin d'or au-dessus ;
- âme de foudre au centre du bras-pointe : fente en zigzag ouverte de part en part où court un vrai trait de foudre en géométrie
  (cœur opaque blanc à bord bleu + calque _e, gaine add_ en 3 sections), qui part du tambour et file vers la pointe ;
- la foudre naît toujours d'un point : la pointe du pic (décharges), ou la frappe (event_select).
Silhouette (reconnaissable sans la couleur) : croissant asymétrique, **bec de faucon** (pointe recourbée en crochet, large à l'œil)
d'un côté, **tranchant évasé coupé en biseau** (comme le bout des primaires des ailes) de l'autre ; différente du pic à vapeur
(cylindre + pic) et de la hache (fer barbu d'un seul côté).
Vrai volume (F3, retour en jeu du 2026-11-08 14 h 22 : « c'est des couches » ; recette .claude/references/objets/volume-3d.md,
prototype skin_epee_orage validé en jeu à 15 h 05) : chaque bras du fer est une plaque biseautée fermée, deux biseaux par
tronçon de bord (≤ 1,05 px) et par face à pente unique (52° : bras épais et étroits, il reste un plat pour la gouttière), un plat
incliné par face qui suit l'amincissement (bec 1,52 -> 0,48 px à la pointe, tranchant 1,48 -> 0,60 px au fil) ; le bec finit en
losange, le tranchant en coin. Fil poli + _e, trempe cuivre/violet aux bouts de travail, liseré d'or ailleurs : peints sur les
faces des biseaux et des plats (échantillonnées texel par texel, découpées par l'alpha, recouvrement 0,08). Fente de foudre =
gouttière creusée dans le plat du bec (parois, fond de 0,32 px où la foudre est couchée). Œil = collet d'acier à 16 pans
(3,1 px, 1,72 d'épaisseur) + tambour d'or à 16 pans aux virgules ; coin d'or chanfreiné ; attelles = bandes biseautées pointues
posées sur la hampe, rivets octogonaux. Manche octogonal inchangé (« le manche est bien »).
Repère (catégorie objets, Recette) : comme iron_pickaxe.png vu de +Z : manche du bas à gauche vers le haut à droite (axe a), fer en
travers (b) ; bec vers le haut à gauche (+b, le bras qui frappe en 3e personne), tranchant vers le bas à droite ; boîte centrée
dans le bloc. ~21 px le long du manche (vanilla ≈ 18,4 ; pic à vapeur 20,5). Display vanilla item/handheld, gui réglé à la case.

Objet vivant (guide 14), sobre :
- item_idle (8 s) : la gaine de la fente vacille (Molang, 9 Hz), petites fourches sur le plat au hasard, arc en retour toutes les
  3 à 8 s avec une petite décharge à la pointe ;
- item_swing (boucle 0,3 s, minage) : à chaque coup de pic la fente s'avive et une petite décharge claque à la pointe ;
- item_gui : gaine au repos, rien d'autre ;
- event_select (0,7 s) : un éclair venu du dehors du croissant frappe la pointe, la fente s'allume de la pointe vers le tambour ;
- event_swing (0,35 s) : vague de la fente du tambour vers la pointe ;
- event_hit (0,7 s) : décharge de la pointe, l'arc remonte le dos du croissant jusqu'au tranchant, arcs en retour, frisson ;
  **le seul son** (embarqué, original : arc_pioche) ;
- event_break (0,6 s) : bloc cassé : la pointe décharge dans la roche (trois éclairs ramifiés qui partent de la pointe, deux formes
  alternées), gerbe d'étincelles emit_mc_electric_spark (ctrl_emit +8 pendant 0,2 s, coupée sinon), sans son (on casse beaucoup
  de blocs : le bruit du jeu suffit).
Chaque groupe replié n'est déplié que par une seule animation d'état et jamais par deux événements qui peuvent se superposer (les
échelles se multiplient) : états = petite décharge + fourches ; event_select = foudre du ciel ; event_hit = décharge de la pointe +
arcs du dos ; event_break = éclairs de la roche ; event_swing ne déplie rien.
Éclairs **repliés à 1/10 sur leur pivot** au repos (invisibles figés, dans l'inventaire et animations coupées) et dépliés par
`scale` ×10 ; allumés par ctrl_alpha.
Fonctions avancées : add_, ctrl_alpha, ctrl_emit + emit_mc_electric_spark, scale animé, calque _e, animations d'objet (item_idle,
item_swing, item_gui, event_select, event_swing, event_hit, event_break), Molang (q.life_time), son embarqué. À juger en jeu :
event_hit, event_break et item_swing (pas encore vérifiés par le développeur), son d'un objet, scale et ctrl_alpha sur un objet,
arcs add_ de jour, taille en 1re personne.
"""
import base64, io, json, math, os, random, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image, ImageDraw

NOM = "skin_pioche_orage"
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


# ------------------------------------------------------------------ dessin (plan a le long du manche, b en travers ; px)
A_O = 17.3                                         # centre de l'œil (tambour)
MR = 1.2                                           # rayon du tambour


def bez(P, s):
    P = [np.array(p, float) for p in P]
    u = 1 - s
    c = u ** 3 * P[0] + 3 * u * u * s * P[1] + 3 * u * s * s * P[2] + s ** 3 * P[3]
    d = 3 * u * u * (P[1] - P[0]) + 6 * u * s * (P[2] - P[1]) + 3 * s * s * (P[3] - P[2])
    return c, d / np.linalg.norm(d)


BEC = [(A_O, 0.0), (A_O + 0.7, 2.3), (A_O - 0.5, 4.6), (A_O - 3.1, 5.9)]          # bras-pointe (+b), bec de faucon
TRA = [(A_O, 0.0), (A_O + 0.6, -2.0), (A_O - 0.3, -3.8), (A_O - 2.0, -4.9)]       # bras-tranchant (-b)


def w_bec(s):
    return 0.14 + 1.12 * (1 - s) ** 0.75


def w_tra(s):
    return 0.98 - 0.3 * s + 0.42 * sm(s, 0.65, 1.0)


def bras(Pb, wf, sgn, n=48):
    """Polygone d'un bras : bord extérieur (côté +a, convexe), bout, bord intérieur. Renvoie (poly, extérieur, intérieur)."""
    ext, inn = [], []
    for s in np.linspace(0, 1, n):
        c, d = bez(Pb, s)
        no = sgn * np.array((d[1], -d[0]))
        ext.append(c + no * wf(s))
        inn.append(c - no * wf(s))
    return ext, inn


_e, _i = bras(BEC, w_bec, 1)
_c1, _d1 = bez(BEC, 1.0)
TIP = tuple(_c1 + _d1 * 0.25)                     # pointe du bec
TIP_D = _d1                                       # direction de la pointe
P_BEC = [tuple(p) for p in _e] + [TIP] + [tuple(p) for p in _i[::-1]]
EXT_BEC = [tuple(p) for p in _e]
_e2, _i2 = bras(TRA, w_tra, -1)
_c2, _d2 = bez(TRA, 1.0)
_e2[-1] = _e2[-1] - _d2 * 0.2                     # tranchant coupé en biseau (bord intérieur plus long)
_i2[-1] = _i2[-1] + _d2 * 0.38
FIL_TRA = [tuple(_e2[-1]), tuple(_i2[-1])]        # le fil du tranchant
P_TRA = [tuple(p) for p in _e2] + [tuple(p) for p in _i2[::-1]]
EXT_TRA = [tuple(p) for p in _e2]


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


def m_boss(P):
    da = P[..., 0] - A_O
    ha = np.where(da > 0, 1.75, 1.5)
    return (np.abs(da / ha) ** 3 + np.abs(P[..., 1] / 1.5) ** 3) < 1


def m_tete(P):
    return m_boss(P) | in_poly(P, P_BEC) | in_poly(P, P_TRA)


# fente en éclair dans le bec : du bord du tambour vers la pointe, écarts qui se resserrent
SLIT_W = 0.2
SLIT = []
for _k, _s in enumerate(np.linspace(0.22, 0.62, 8)):
    _c, _d = bez(BEC, _s)
    _no = np.array((_d[1], -_d[0]))
    _amp = (0.18 - 0.12 * (_s - 0.22) / 0.40) * (0 if _k in (0, 7) else (1 if _k % 2 else -1))
    SLIT.append(tuple(_c + _no * _amp))



# ------------------------------------------------------------------ vrai volume (.claude/references/objets/volume-3d.md)
# Fer à section réelle : chaque bras est une plaque biseautée fermée (deux biseaux par tronçon de bord et par face, un plat
# incliné par face qui suit l'amincissement vers le bout de travail). Les couleurs du fil, du poli, de la trempe et du liseré
# d'or sont peintes SUR les faces des volumes ; chaque face est échantillonnée texel par texel dans le plan de la pioche et
# découpée par l'alpha. Fente de foudre = gouttière creusée (parois + fond) dans le plat du bec.
def unit(v):
    return v / np.linalg.norm(v)


Z_E = 0.10                        # demi-épaisseur au bord (fil)
DF = 16.0                         # texels par px sur les faces des volumes
TH = 0.3                          # épaisseur des cubes de biseau, de plat, de paroi
RECOUV = 0.08                     # recouvrement des faces voisines
T_BIS = 0.85                      # pente des biseaux de la recette (40°), attelles
T_FER = 1.3                       # pente unique des biseaux du fer (52°) : bras épais et étroits, il reste un plat pour la gouttière
R_COL = 1.55                      # rayon (apothème) du collet de l'œil
O_ = np.array((A_O, 0.0))


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


# --- bras du fer : bec (pointe, +b) et tranchant (-b)
def _fils_bras(ext, inn, bout, pas=1.05):
    e = hors_collet(resample(ext, pas))
    i = hors_collet(resample(inn, pas))
    return e + ([bout] if bout is not None else []) + i[::-1]


FIL_BEC = _fils_bras(_e, _i, TIP)
FIL_TRA_P = _fils_bras(_e2, _i2, None)
U_BEC = unit(np.array(TIP) - O_)
L_BEC = float((np.array(TIP) - O_) @ U_BEC)
H_BEC0, H_BEC1 = 0.76, 0.24                  # demi-épaisseur au collet -> à la pointe (1,52 px -> 0,48 px)
K_BEC = (H_BEC1 - H_BEC0) / (L_BEC - R_COL)
C_FIL = (np.array(FIL_TRA[0]) + np.array(FIL_TRA[1])) / 2
U_TRA = unit(C_FIL - O_)
L_TRA = float((C_FIL - O_) @ U_TRA)
H_TRA0, H_TRA1 = 0.74, 0.30                  # coin du tranchant : 1,48 px -> 0,60 px au fil
K_TRA = (H_TRA1 - H_TRA0) / (L_TRA - R_COL)

# Gouttière : zigzag de la fente, demi-largeur par sommet (pointue aux deux bouts)
GW = [0.08, 0.21, 0.22, 0.21, 0.20, 0.18, 0.16, 0.07]
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


BEC_P = Piece("bec", P_BEC, [FIL_BEC], O_, U_BEC, H_BEC0 - K_BEC * R_COL, K_BEC, Z_E, peint_biseau_fer, peint_plat_fer,
              peint_fil_fer, trou=in_gout, t=T_FER, trempe=lambda P: (np.linalg.norm(P - np.array(TIP), axis=-1), (0.95, 1.25, 1.58, 1.66)))
TRA_P = Piece("tranchant", P_TRA, [FIL_TRA_P], O_, U_TRA, H_TRA0 - K_TRA * R_COL, K_TRA, Z_E, peint_biseau_fer, peint_plat_fer,
              peint_fil_fer, t=T_FER, trempe=lambda P: (d_poly(P, FIL_TRA), (0.5, 0.74, 0.98, 1.05)))
# Attelles (langets) : bandes d'acier biseautées posées sur les faces avant et arrière de la hampe, pointues vers le bas.
A_AT0, A_AT1, W_AT = A_O - 1.25, A_O - 5.5, 0.38
POLY_AT = [(A_AT0, W_AT), (A_AT1 + 0.8, W_AT), (A_AT1, 0.0), (A_AT1 + 0.8, -W_AT), (A_AT0, -W_AT)]
Z_HAMPE = 0.53
ATTELLES = [Piece(f"attelle{'pm'[sg < 0]}", POLY_AT, [POLY_AT], O_, (1.0, 0.0), 0.2, 0.0, 0.05, peint_biseau_att, peint_plat_att,
                  peint_fil_att, t=0.6, z0=sg * Z_HAMPE, cotes=(sg,)) for sg in (1, -1)]


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
    marge = BEC_P.dE(pts) - BEC_P.wb(pts)
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


def t_collet():
    def p(P, r, apo):
        nz = cellules(P + 30, 2.0, 8.0)[..., None]
        col = lerp(METAL[2], METAL[1], 0.4) + nz * 16 + np.zeros(P.shape[:-1] + (3,), np.float32)
        col[apo > R_COL - 0.14] = METAL[4]
        col[(apo > R_COL - 0.22) & (apo <= R_COL - 0.14)] = METAL[0]
        orl = (r > 1.2) & (r < 1.3)
        col[orl] = OR[2]
        return col
    return disque16(56, R_COL, peindre=p)


def conception():
    SPECS.clear()
    TILES.clear()
    volume(BEC_P, "fer")
    gouttiere(BEC_P, "fer")
    volume(TRA_P, "fer")
    for pc in ATTELLES:
        volume(pc, "manche")


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
    items += [("medaillon", medaillon(), None), ("collet", t_collet(), None), ("cuir", t_cuir(), None), ("core", core, core_e),
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
    """Plan (a, b, z) de la pioche -> monde : rotation theta autour de Z, puis translation P0."""
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


def prisme16(g, nom, R, zh, tile_cote, tile_face):
    """Prisme à 16 pans autour de l'œil : 16 parois de TH (côtés `tile_cote`), deux faces découpées par l'alpha."""
    cote = 2 * R * math.tan(math.pi / 16)
    for k in range(16):
        th = TAU * k / 16
        nrm = np.array((math.cos(th), math.sin(th)))
        tg = np.array((-nrm[1], nrm[0]))
        c = O_ + nrm * (R - TH / 2)
        u0, v0, u1, v1 = UV[tile_cote]
        boite(g, f"{nom}{k}", W_(c[0], c[1]), Wv(*tg), V(0, 0, 1), cote + 0.03, 2 * zh, TH,
              {"south": [u0, v0, u1, v1], "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
    u0, v0, u1, v1 = UV[tile_face]
    Rc = R / math.cos(math.pi / 16)
    for sg in (1, -1):
        fc = {"south": [u0, v0, u1, v1]} if sg > 0 else {"north": [u1, v0, u0, v1]}
        boite(g, f"{nom}_face{'pm'[sg < 0]}", W_(A_O, 0, sg * (zh - TH / 2)), Wv(1, 0), Wv(0, 1), 2 * Rc, 2 * Rc, TH,
              {**{f: CLEAR for f in ("north", "south", "east", "west", "up", "down")}, **fc})


def build(theta, P0):
    elements.clear()
    groups.clear()
    _rc[0] = 0
    Repere.th, Repere.P0 = theta, np.asarray(P0, float)
    out = {}
    racine = group(objet.etape("repos", "pioche"), W_(A_O, 0))
    pioche = group("pioche", W_(A_O, 0), racine)
    # --- manche : pommeau à pointe de cristal, poignée de cuir entre bagues d'or, hampe d'acier, attelles biseautées rivetées
    manche = group("manche", W_(4.0, 0), pioche)
    barre(manche, "pommeau", -0.2, 1.1, 0.86, "metal")
    barre(manche, "pom_bague", 0.22, 0.58, 0.94, "or")
    barre(manche, "pom_cri", -1.05, -0.15, 0.44, "cristal")
    barre(manche, "pom_cri2", -1.55, -1.0, 0.23, "cristal", octo=False)
    barre(manche, "bague1", 1.05, 1.5, 0.74, "or")
    barre(manche, "poignee", 1.45, 7.3, 0.64, "cuir")
    barre(manche, "bague2", 7.25, 7.65, 0.72, "or")
    barre(manche, "hampe", 7.6, A_O + 1.2, Z_HAMPE + 0.02, "hampe")
    for zs in (1, -1):
        for j, a in enumerate((A_O - 4.6, A_O - 3.4, A_O - 2.2)):
            for r_ in (0.0, 45.0):
                rr = math.radians(r_)
                boite(manche, f"rivet{'pm'[zs < 0]}{j}{int(r_)}", W_(a, 0, zs * (Z_HAMPE + 0.25)), Wv(math.cos(rr), math.sin(rr)),
                      Wv(-math.sin(rr), math.cos(rr)), 0.3, 0.3, 0.16, strip("or"))
    # --- fer : bec et tranchant en vrai volume, œil (collet à 16 pans + tambour d'or aux virgules), coin d'or chanfreiné
    fer = group("fer", W_(A_O, 0), pioche)
    poser_specs({"fer": fer, "manche": manche})
    prisme16(fer, "collet", R_COL, 0.86, "metal", "collet")
    prisme16(fer, "tambour", 1.08, 1.1, "or", "medaillon")
    boite(fer, "coin", W_(A_O + 1.78, 0), Wv(1, 0), Wv(0, 1), 0.56, 0.9, 0.92, strip("or"))
    Xq = unit(Wv(1, 0) * math.cos(math.pi / 4) + V(0, 0, 1) * math.sin(math.pi / 4))
    boite(fer, "coin_ch", W_(A_O + 1.78, 0), Xq, Wv(0, 1), 0.6, 0.86, 0.6, strip("or"))
    # --- foudre de la fente : cœur opaque + _e couché au fond de la gouttière, gaine add_ en NG sections
    foudre = group("foudre", W_(*SLIT[0]), fer)
    pts2 = zigzag(SLIT, 4 * NG, 0.04, 17)
    pts = [W_(*p) for p in pts2]
    trait(foudre, "eclair", pts, 0.34, 0.22, "core")
    out["gaines"] = []
    per = (len(pts) - 1) // NG
    for k in range(NG):
        gg = group(f"add_gaine_{k}", tuple(pts[k * per]), foudre)
        ctrl(gg)
        for i in range(k * per, (k + 1) * per):
            pm = np.array(((pts2[i][0] + pts2[i + 1][0]) / 2, (pts2[i][1] + pts2[i + 1][1]) / 2))
            seg(gg, f"gaine{i}", pts[i], pts[i + 1], min(0.8, 2 * float(BEC_P.h(pm)) - 0.14), "halo", ov=0.04, roll=0.0)
        out["gaines"].append(gg)
    # fourches de la fente sur le plat (faces avant et arrière) — états seulement
    out["fourches"] = []
    on_slit = le_long(SLIT)
    for v in range(2):
        fg = group(f"add_fourche_{'ab'[v]}", W_(*SLIT[0]), foudre)
        ctrl(fg)
        rng = random.Random(40 + v)
        for k in range(3):
            t = (k + 0.25 + 0.5 * rng.random()) / 3
            p = on_slit(t)
            d = unit(on_slit(min(1, t + 0.02)) - p)
            side = 1 if (k + v) % 2 == 0 else -1
            dirn = tourner(d, rng.uniform(40, 65) * side)
            q = p + dirn * rng.uniform(0.5, 0.7)
            for zs in (1, -1):
                zz = zigzag([p + dirn * 0.36, q], 3, 0.1, 70 + 10 * v + k)
                trait(fg, f"f{k}{'pm'[zs < 0]}", [W_(x, y, zs * (float(BEC_P.surf(np.array([(x, y)]))[0]) + 0.07)) for x, y, _ in zz],
                      0.16, 0.12, "crk")
        replier(fg)
        out["fourches"].append(fg)
    # --- arcs du dos du croissant : du tranchant au bec (event_hit)
    dos = [tuple(p) for p in EXT_TRA[::-1] if True][: int(len(EXT_TRA) * 0.68)]
    dos += [(A_O + 1.62 * math.cos(u), 1.4 * math.sin(u)) for u in np.linspace(-1.0, 1.0, 7)]
    dos += [tuple(p) for p in EXT_BEC[int(len(EXT_BEC) * 0.32):]] + [TIP]
    dos = [p for p in dos if np.array(p)[0] <= A_O + 1.8]
    arcs = group("arcs_dos", W_(*TIP), fer)
    out["fil"] = []
    at = le_long(exterieur(dos, 0.17))
    for k in range(N_FIL):
        t0, t1 = k / N_FIL, (k + 1) / N_FIL
        sous = [tuple(at(t)) for t in np.linspace(t0, t1, 4)]
        g = group(f"add_dos_{k}", W_(*sous[0]), arcs)
        ctrl(g)
        zz = zigzag(sous, 4, 0.14, 100 + 7 * k, zj=0.08)
        trait(g, "a", [W_(*p) for p in zz], 0.23, 0.19, "crk")
        replier(g)
        out["fil"].append(g)
    # --- décharges de la pointe : a (event_hit), r (états)
    out["pointe"] = {}
    for nm, seed, angs, lf in (("a", 5, (-40, 2, 38), 1.0), ("r", 13, (-26, 20), 0.7)):
        g = group(f"add_pointe_{nm}", W_(*TIP), arcs)
        ctrl(g)
        rng = random.Random(seed)
        for j, an in enumerate(angs):
            q = np.array(TIP) + tourner(TIP_D, an) * rng.uniform(1.0, 1.6) * lf
            zz = zigzag([TIP, tuple(q)], 3, 0.2, seed * 10 + j)
            trait(g, f"p{j}", [W_(*p) for p in zz], 0.24, 0.14, "crk")
        replier(g)
        out["pointe"][nm] = g
    # --- foudre qui tombe sur la pointe (event_select) : du dehors du croissant vers la pointe, deux formes
    out["ciel"] = []
    n_out = np.array((TIP_D[1], -TIP_D[0]))
    for nm, seed, off in (("a", 61, 0.0), ("b", 67, 0.9)):
        g = group(f"add_ciel_{nm}", W_(*TIP), arcs)
        ctrl(g)
        haut = np.array(TIP) + n_out * 5.2 + TIP_D * (1.2 + off) + np.array((0.0, -off))
        zz = zigzag([tuple(haut), TIP], 6, 0.45, seed, zj=0.15)
        trait(g, "c", [W_(*p) for p in zz], 0.2, 0.3, "crk")
        b0 = np.array(zz[2][:2])
        bz = zigzag([tuple(b0), tuple(b0 + tourner(unit(np.array(TIP) - haut), 38 if nm == "a" else -38) * 1.6)], 3, 0.25, seed + 1)
        trait(g, "cb", [W_(*p) for p in bz], 0.16, 0.12, "crk")
        replier(g)
        out["ciel"].append(g)
    # --- la pointe décharge dans la roche (event_break) : trois éclairs ramifiés, deux formes
    out["roche"] = []
    for nm, seed, angs in (("a", 21, (-34, 4, 37)), ("b", 29, (-18, 24, 52))):
        g = group(f"add_roche_{nm}", W_(*TIP), arcs)
        ctrl(g)
        rng = random.Random(seed)
        for j, an in enumerate(angs):
            eclair_branche(g, f"r{j}", TIP, tourner(TIP_D, an), rng.uniform(3.2, 4.2), seed + 5 * j, branches=1 if j != 1 else 2)
        replier(g)
        out["roche"].append(g)
    rot_emit = (0, 0, round(math.degrees(math.atan2(-Wv(*TIP_D)[0], Wv(*TIP_D)[1])), 2))
    em = group("emit_mc_electric_spark", W_(*TIP), fer, rotation=rot_emit)
    group("ctrl_emit", W_(*TIP), em)
    out["emit"] = em
    out["racine"], out["pioche"] = racine, pioche
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


K = float(os.environ.get("K", "1.0"))
THETA = math.radians(45)          # le long de la diagonale du bloc, fer en haut à droite (vue de +Z), comme la vanilla
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



FILS = F["fil"]
GAINES = F["gaines"]
PA, PR = F["pointe"]["a"], F["pointe"]["r"]
CIEL = F["ciel"]
ROCHE = F["roche"]
TOUS = FILS + [PA, PR] + CIEL + ROCHE + F["fourches"]


def eteindre(an, sauf=()):
    for g in TOUS:
        if g not in sauf:
            piste_ctrl(an, g, [kf("position", 0, -1)])


def emit(an, keys):
    gg = next(gg for n, gg in groups.items() if gg["parent"] == F["emit"] and n.startswith("ctrl_emit"))
    an["animators"][gg["uuid"]] = {"name": "ctrl_emit", "type": "bone", "keyframes": keys}


# item_idle : la fente vit (gaine qui vacille, fourches), petite décharge de la pointe aux arcs en retour ; le reste éteint.
idle = anim("item_idle", 8.0)
for k, g in enumerate(GAINES):
    piste_ctrl(idle, g, [kf("position", 0, gaine_idle(k))])
for v, fg in enumerate(F["fourches"]):
    deplier(idle, fg)
    piste_ctrl(idle, fg, [kf("position", 0, fourche_idle(v))])
deplier(idle, PR)
piste_ctrl(idle, PR, [kf("position", 0, chk(restrike(P_RS, PR_RS, 0.37) + "v.r-1"))])
eteindre(idle, sauf=F["fourches"] + [PR])
emit(idle, [kf("position", 0, -1)])

# item_swing (boucle 0,3 s, rythme du geste de minage) : à chaque coup la fente s'avive et la pointe claque.
L_MIN = 0.3
mine = anim("item_swing", L_MIN)
T_IMP = 0.14
for k, g in enumerate(GAINES):
    t0 = T_IMP - 0.03 + 0.012 * k
    piste_ctrl(mine, g, [kf("position", t, -0.3 + 0.95 * bump(t, t0, t0 + 0.02, t0 + 0.05, t0 + 0.13)) for t in np.round(np.linspace(0, L_MIN, 16), 4)])
deplier(mine, PR)
piste_ctrl(mine, PR, onoff([(T_IMP, T_IMP + 0.05)], L_MIN))
eteindre(mine, sauf=[PR])
emit(mine, [kf("position", 0, -1)])

# item_gui : inventaire calme.
gui = anim("item_gui", 4.0)
for g in GAINES:
    piste_ctrl(gui, g, [kf("position", 0, -0.3)])
eteindre(gui)
emit(gui, [kf("position", 0, -1)])

# event_select (0,7 s) : un éclair frappe la pointe (deux formes), la fente s'allume de la pointe vers le tambour.
L_SEL = 0.7
sel = anim("event_select", L_SEL, "once")
for g in CIEL:
    deplier(sel, g)
piste_ctrl(sel, CIEL[0], onoff([(0.0, 0.07), (0.15, 0.19)], L_SEL))
piste_ctrl(sel, CIEL[1], onoff([(0.08, 0.13)], L_SEL))
for k, g in enumerate(GAINES):
    t0 = 0.1 + 0.06 * (NG - 1 - k)
    piste_ctrl(sel, g, [kf("position", t, -0.6 * (1 - sm(t, 0.0, 0.1)) * (t < t0) + (1.0 * bump(t, t0, t0 + 0.04, t0 + 0.12, t0 + 0.4)
                                                                                     - 0.38 * sm(t, t0 + 0.12, t0 + 0.4)) * (t >= t0))
                         for t in np.round(np.linspace(0, L_SEL, 29), 4)])

# event_swing (0,35 s) : la fente s'avive en vague du tambour vers la pointe (ne déplie rien).
L_SW = 0.35
sw = anim("event_swing", L_SW, "once")
for k, g in enumerate(GAINES):
    t0 = 0.025 * k
    piste_ctrl(sw, g, [kf("position", t, 0.6 * bump(t, t0, t0 + 0.04, t0 + 0.1, t0 + 0.3)) for t in np.round(np.linspace(0, L_SW, 15), 4)])

# event_hit (0,7 s) : décharge de la pointe, l'arc remonte le dos du croissant jusqu'au tranchant, trois arcs en retour.
L_HIT = 0.7
hit = anim("event_hit", L_HIT, "once")
RESTRIKES = [(0.22, 0.27), (0.32, 0.36), (0.42, 0.45)]
deplier(hit, PA)
piste_ctrl(hit, PA, onoff([(0.0, 0.09), RESTRIKES[0], RESTRIKES[2]], L_HIT))
for k, g in enumerate(FILS):
    deplier(hit, g)
    t0 = 0.04 + 0.03 * (N_FIL - 1 - k)                      # de la pointe (dernier tronçon) vers le tranchant
    iv = [(t0, t0 + 0.09)]
    for j, (a, b) in enumerate(RESTRIKES):
        if j == 0 or (j == 1 and k % 2 == 1) or (j == 2 and k >= N_FIL - 3):
            iv.append((a, b))
    piste_ctrl(hit, g, onoff(iv, L_HIT))
for k, g in enumerate(GAINES):
    piste_ctrl(hit, g, [kf("position", t, 1.2 * sm(t, 0.0, 0.02) * (1 - sm(t, 0.08, 0.6))
                         + 0.4 * sum(bump(t, a - 0.01, a, b, b + 0.02) for a, b in RESTRIKES)) for t in np.round(np.linspace(0, L_HIT, 36), 4)])
piste(hit, F["pioche"], [kf("rotation", t, 0, 0, 2.5 * math.sin(TAU * t / 0.07) * (1 - sm(t, 0.0, 0.28))) for t in np.round(np.linspace(0, 0.3, 19), 4)]
      + [kf("rotation", L_HIT, 0, 0, 0)])

# event_break (0,6 s) : bloc cassé, la pointe décharge dans la roche (deux formes alternées), gerbe d'étincelles ; sans son.
L_BR = 0.6
brk = anim("event_break", L_BR, "once")
for g in ROCHE:
    deplier(brk, g)
piste_ctrl(brk, ROCHE[0], onoff([(0.0, 0.08), (0.17, 0.21)], L_BR))
piste_ctrl(brk, ROCHE[1], onoff([(0.08, 0.15), (0.26, 0.29)], L_BR))
for k, g in enumerate(GAINES):
    t0 = 0.03 * (NG - 1 - k)
    piste_ctrl(brk, g, [kf("position", t, 0.9 * bump(t, t0, t0 + 0.02, t0 + 0.08, t0 + 0.35)) for t in np.round(np.linspace(0, L_BR, 25), 4)])
emit(brk, [kf("position", 0, 8), kf("position", 0.2, 8), kf("position", 0.21, -1), kf("position", L_BR, -1)])

ANIMS = [idle, mine, gui, sel, sw, hit, brk]

# ------------------------------------------------------------------ écriture
assert 80 <= len(elements) <= 2500, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
GUI = float(os.environ.get("GUI", "0.84"))
AFFICHAGE = objet.affichage("pioche", gui={"scale": [GUI] * 3})
model = objet.modele(NOM, "pioche", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, embarquer_sons, cle_son
limiter_sons(model)
embarquer_sons(model, {"arc_pioche": "sons/arc_pioche.ogg"})
# Un seul son, au coup qui touche (event_hit) : tools/sons.py ne connaît pas encore les événements d'objet, on le pose après.
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "arc_pioche")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur le long du manche {LONGUEUR:.1f} px ; largeur {LARGEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)}")
