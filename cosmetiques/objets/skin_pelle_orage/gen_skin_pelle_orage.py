"""Pelle de l'orage : skin d'objet (guide 14) pour toutes les pelles du joueur, ensemble Orage (thème Éléments). Design original.
Écrit skin_pelle_orage.png, skin_pelle_orage_e.png et .build/skin_pelle_orage_brut.bbmodel à côté de ce script.
Point de départ : gen_skin_pioche_orage.py (matières, peinture du fer, foudre, animations) ; seuls le dessin du fer, le manche et
les arcs ont changé.

Référence réelle (.claude/references/objets/pelles.md) : pelle à bout rond (fer en cuillère, pointe arrondie qui entre dans la
terre, épaules à marchepieds où le pied appuie, nervure dans l'axe, douille rivetée qui prend le manche, poignée en D).
Famille Orage (ailes_orage v7, skin_epee_orage, skin_pioche_orage, skin_hache_orage, skin_masse_orage ; .claude/styles/orage.md) :
- acier d'orage bleu-noir martelé, bord poli clair, liseré d'or en retrait sur les épaules et les flancs ;
- avant du fer trempé (le fil qui entre dans la terre) : poli presque blanc (+ _e) puis bande de revenu cuivre et violet ;
- tambour d'or aux trois virgules à la base du fer, au bout de la douille (même tambour que l'épée et la pioche) ;
- nervure = âme de foudre : gouttière en zigzag à angles vifs creusée dans l'axe du fer, où court un vrai trait de foudre en
  géométrie couché sur le fond de chaque côté (cœur opaque blanc à bord bleu + calque _e, gaine add_ en 3 sections) ;
- une dent d'éclair sur chaque flanc, décalées (comme les dents de l'épée) ; bouts des épaules rabattus vers le manche (en aile) ;
- poignée en D : traverse de cuir bleu nuit entre embouts d'or, pointe de cristal au bas du D (le pommeau de la famille) ;
  poignée de cuir bleu nuit entre bagues d'or, douille à rivets d'or.
Silhouette (reconnaissable sans la couleur) : fer large en écu arrondi au bout du manche, D au talon ; différente de la pioche
(croissant) et de la lance (fer étroit).
Vrai volume (retour en jeu du 2026-11-08 14 h 22 : « c'est des couches » ; recette .claude/references/objets/volume-3d.md, prototype
skin_epee_orage validé à 15 h 05) : fer en cuillère = une plaque biseautée fermée. Biseaux à pente unique de 40° (fer large de 6 px)
sur les ailes des épaules, les flancs, les dents d'éclair (sommets gardés vifs) et le bout rond ; plats en 6 bandes par face, cordes
d'un creux parabolique (bords relevés de 0,70 px vers +Z : avant creux, dos bombé) qui suivent l'amincissement 1,56 -> 0,56 px
(avant K) ; fil poli + _e et trempe cuivre/violet peints sur les faces ; gouttière creusée (parois, fond) ; tambour d'or à 16 pans ;
marchepieds sur le haut des épaules ; douille, rivets, manche et poignée en D octogonaux. Ancienne version (plaques empilées) :
.build/gen_avant.py.
Repère (catégorie objets, Recette) : comme iron_shovel.png vu de +Z : manche du bas à gauche vers le haut à droite (axe a), fer en
haut à droite, plat du fer vers ±Z ; boîte centrée dans le bloc. 21,8 px sur la diagonale (pelle vanilla ≈ 18 ; K = 0,92).
Display vanilla item/handheld, gui réglé à la case.

Objet vivant (guide 14), sobre :
- item_idle (8 s) : la gaine de la fente vacille (Molang, 9 Hz), petites fourches sur le plat au hasard, arc en retour toutes les
  3 à 8 s avec une petite décharge à la pointe ;
- item_swing (boucle 0,3 s, on creuse) : à chaque coup de pelle la fente s'avive et une petite décharge claque à la pointe ;
- item_gui : gaine au repos, rien d'autre ;
- event_select (0,7 s) : un éclair venu d'en haut frappe la pointe, la fente s'allume de la pointe vers le tambour ;
- event_swing (0,35 s) : vague de la fente du tambour vers la pointe (ne déplie rien) ;
- event_hit (0,7 s) : décharge de la pointe, les arcs remontent les deux flancs jusqu'aux épaules, arcs en retour, frisson ;
  **le seul son** (embarqué, original : arc_pelle) ;
- event_break (0,6 s) : bloc cassé, le geste de la pelletée : le fer se relève de 5° (levier) puis revient, la pointe décharge
  dans le sol (trois éclairs ramifiés, deux formes alternées), gerbe emit_mc_electric_spark (ctrl_emit +7 pendant 0,2 s, coupée
  sinon) ; sans son (on casse beaucoup de blocs).
Chaque groupe replié n'est déplié que par une seule animation d'état et jamais par deux événements qui peuvent se superposer (les
échelles se multiplient) : états = petite décharge + fourches ; event_select = foudre du ciel ; event_hit = décharge de la pointe +
arcs des flancs ; event_break = éclairs du sol ; event_swing ne déplie rien.
Éclairs repliés à 1/10 sur un pivot caché dans le métal au repos (0,6 px en dedans du fil, 1,2 px en dedans du bout) (invisibles figés, dans l'inventaire et animations coupées), dépliés par scale ×10,
allumés par ctrl_alpha.
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

NOM = "skin_pelle_orage"
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
A_S = 11.6                                         # épaules du fer (haut de la lame, côté manche)
A_T = 19.5                                         # pointe du fer
A_O = A_S + 0.45                                   # centre du tambour (base de la lame, au bout de la douille)
MR = 1.2                                           # rayon du tambour
W0 = 3.0                                           # demi-largeur du fer
STEP = {1: (0.47, 0.3), -1: (0.63, 0.26)}          # dent d'éclair de chaque bord (u, retrait), décalées comme sur l'épée


def unit(v):
    return v / np.linalg.norm(v)


def w_lame(u, sg):
    u0, r = STEP[sg]
    base = W0 * (0.93 + 0.07 * sm(u, 0.0, 0.3)) * max(0.0, 1 - max(0.0, (u - 0.3) / 0.7) ** 1.9) ** 0.52
    return max(0.0, base - r * sm(u, u0, u0 + 0.02) * (1 - sm(u, 0.86, 1.0)))


A_B = A_S + 0.35                                   # début du bord latéral


def a_de(u):
    return A_B + u * (A_T - A_B)


def bord(sg, u0=0.0, u1=1.0, n=64):
    """Bord latéral du fer côté sg, de l'épaule (u0) vers la pointe (u1)."""
    return [(a_de(u), sg * w_lame(u, sg)) for u in np.linspace(u0, u1, n)]


def epaule(sg):
    """Haut du fer côté sg, du col vers le bout de l'épaule rabattu vers le manche (en aile), puis retour au bord."""
    return [(A_S + 0.2, sg * 0.85), (A_S + 0.02, sg * 1.75), (A_S - 0.42, sg * (W0 + 0.1)), (A_B, sg * w_lame(0.0, sg))]


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


def cote_fil(sg):
    """Fil d'un flanc, de l'épaule à la pointe ; la dent d'éclair gardée vive (deux sommets)."""
    u0, _ = STEP[sg]
    return resample(bord(sg, 0.0, u0, 48), 0.75) + resample(bord(sg, u0 + 0.02, 1.0, 200), 0.6)


TIP = (A_T, 0.0)                                   # pointe du fer
TIP_D = np.array((1.0, 0.0))                       # direction de la pointe
_FP, _FM = cote_fil(1), cote_fil(-1)
FIL = epaule(1)[1:3] + _FP + _FM[::-1][1:] + epaule(-1)[1:3][::-1]    # bords tranchants : ailes des épaules, flancs, bout rond
P_LAME = epaule(1)[:1] + FIL + epaule(-1)[:1]
FIL_TRA = [p for p in FIL if p[0] >= a_de(0.6)]                      # fil trempé : l'avant du fer, qui entre dans la terre
EXT_P, EXT_M = bord(1, 0.04, 0.99), bord(-1, 0.04, 0.99)


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
    return (np.abs(da / 1.45) ** 3 + np.abs(P[..., 1] / 1.45) ** 3) < 1


def m_tete(P):
    return m_boss(P) | in_poly(P, P_LAME)


# fente en éclair dans l'axe du fer (la nervure d'une vraie pelle) : du tambour vers la pointe, écarts qui se resserrent ;
# le départ est caché sous le tambour
SLIT = []
for _k, _a in enumerate(np.linspace(A_O + MR - 0.35, A_S + 0.68 * (A_T - A_S), 7)):
    _amp = (0.42 - 0.2 * _k / 6) * (0 if _k in (0, 6) else (1 if _k % 2 else -1))
    SLIT.append((_a, _amp))


# ------------------------------------------------------------------ vrai volume (.claude/references/objets/volume-3d.md)
# Fer en cuillère à section réelle : une plaque biseautée fermée. Deux biseaux par tronçon de fil (flancs, dents, bout rond) et
# par face, à pente unique de 40° (fer large de 6 px : grand plat) ; plats en six bandes par face qui suivent le creux (cordes
# d'une parabole : bords relevés de 0,70 px vers +Z, l'avant du fer est creux, le dos bombé) et l'amincissement (1,56 px aux
# épaules -> 0,56 px au bout). Le haut des épaules n'a pas de fil : il est fermé par les marchepieds. Couleurs portées par les
# faces, échantillonnées texel par texel dans le plan de la pelle et découpées par l'alpha. Fente = gouttière creusée.
Z_E = 0.12                        # demi-épaisseur au fil ; tout est réduit par K = 0,92 ensuite
DF = 16.0                         # texels par px sur les faces des volumes
TH = 0.33                         # épaisseur des cubes de biseau, de plat, de paroi (0,30 après K)
RECOUV = 0.08                     # recouvrement des faces voisines
T_BIS = 0.85                      # pente unique (40°)
H0, H1 = 0.78, 0.28               # demi-épaisseur aux épaules -> au bout
K_H = (H1 - H0) / (A_T - A_S)
CB = 0.70                         # creux de la cuillère : bords relevés de CB à |b| = W0
NB_BANDES = 6


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


SEGS = subdiv(FIL)


def zc_b(b):
    return CB * (np.asarray(b, float) / W0) ** 2


def zc(P):
    """Surface moyenne du fer (creux de la cuillère)."""
    return zc_b(np.asarray(P, float)[..., 1])


def h(P):
    return H0 + K_H * (np.asarray(P, float)[..., 0] - A_S)


def wb(P):
    return np.maximum((h(P) - Z_E) / T_BIS, 0.02)


def dE(P):
    return d_stack(P, SEGS).min(0)


def surf(P):
    """Demi-épaisseur réelle (biseau compris) autour de la surface moyenne."""
    d, hh, w = dE(P), h(P), wb(P)
    return np.where(d < w, Z_E + (hh - Z_E) * np.clip(d / w, 0, 1), hh)


def zs(P, sg):
    return zc(P) + sg * surf(P)


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
    W, H_ = max(2, int(round(dims[0] * dens))), max(2, int(round(dims[1] * dens)))
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H_) + 0.5) / H_
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


# --- gouttière : zigzag de la fente, demi-largeur par sommet (pointue au bout ; le départ est sous le tambour)
GW = [0.14, 0.25, 0.26, 0.25, 0.23, 0.19, 0.07]
Z_FOND = 0.18                     # fond de 0,36 px (0,33 après K)


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
J_TR = (0.4, 0.6, 0.8, 0.86)


def d_trempe(P):
    """Distance au bout de travail : fil de l'avant du fer, bout rond plus large (comme l'ancienne version)."""
    return np.minimum(d_poly(P, FIL_TRA), np.linalg.norm(P - np.array(TIP), axis=-1) * 0.42)


def appliquer_trempe(P, col):
    d = d_trempe(P)
    j0, j1, j2, j3 = J_TR
    po = d < j0
    col[po] = lerp(METAL[4], np.array((236, 244, 255), np.float32), np.clip(1 - d[po] / j0, 0, 1)[..., None])
    cu = (d >= j0) & (d < j1)
    col[cu] = lerp(col[cu], CUIVRE, 0.85)
    vi = (d >= j1) & (d < j2)
    col[vi] = lerp(col[vi], VIOLET, 0.7)
    col[(d >= j2) & (d < j3)] = METAL[0]
    return d


def pointe(P, col, em):
    dT = np.linalg.norm(P - np.array(TIP), axis=-1)
    col[dT < 0.4] = (240, 246, 255)
    em[dT < 0.42] = (120, 160, 240)


def peint_biseau(P, d_):
    f = d_ / wb(P)
    nz = cellules(P, 2.2, 1.0)[..., None]
    col = lerp(METAL[3], METAL[2], np.clip((f[..., None] - 0.70) / 0.2, 0, 1)) + nz * 10
    col = np.where((f < 0.3)[..., None], lerp(METAL[4], METAL[3], np.clip((f[..., None] - 0.08) / 0.22, 0, 1)) + nz * 6, col)
    em = np.zeros(col.shape, np.float32)
    d = appliquer_trempe(P, col)
    tr = d < J_TR[3]
    orl = (f >= 0.44) & (f < 0.66) & ~tr                       # liseré d'or sur le biseau, hors du bout trempé
    col[orl] = OR[2]
    col[orl & (f < 0.52)] = OR[3]
    col[f >= 0.93] = METAL[0]                                   # arête du plat : trait d'ombre net
    vif = (f < 0.16) & (d < J_TR[1])
    col[vif] = (236, 244, 255)
    em[vif] = (110, 150, 235)
    pointe(P, col, em)
    return col, em


def peint_fil(P):
    col = np.zeros(P.shape[:-1] + (3,), np.float32) + METAL[4]
    em = np.zeros_like(col)
    vif = d_trempe(P) < J_TR[1]
    col[vif] = (236, 244, 255)
    em[vif] = (110, 150, 235)
    pointe(P, col, em)
    return col, em


def peint_plat(P, d_):
    w = wb(P)
    nz = cellules(P, 1.6, 2.0)[..., None]
    col = lerp(METAL[2], METAL[1], np.clip((d_[..., None] - w[..., None] - 0.1) / 0.5, 0, 1) * 0.6) + nz * 16
    appliquer_trempe(P, col)
    col[d_ < w + 0.04] = METAL[0]
    em = np.zeros(col.shape, np.float32)
    # bord de la gouttière : lèvre claire (+ _e), filet sombre, liseré d'or en retrait
    dg = d_gout(P)
    levre = dg < 0.07
    col[levre] = (190, 208, 255)
    em[levre] = (60, 100, 210)
    col[(dg >= 0.07) & (dg < 0.13)] = METAL[0]
    orl = (dg >= 0.19) & (dg < 0.27) & (d_ > w + 0.1)
    col[orl] = OR[2]
    col[orl & (dg < 0.22)] = OR[3]
    pointe(P, col, em)
    return col, em


def volume(groupe):
    """Biseaux (deux par tronçon de fil) + plats en bandes qui suivent le creux et l'amincissement."""
    for idx, (p, q, v0, v1) in enumerate(SEGS):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        pm = (p + q) / 2
        if not in_poly(np.array([pm + n * 0.05]), P_LAME)[0]:
            n = -n
        hh, w = float(h(pm)), float(wb(pm))
        e0 = w * 1.3 if v0 else 0.04
        e1 = w * 1.3 if v1 else 0.04
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        pin = mid + n * w
        for sg in (1, -1):
            z_e = float(zc(mid)) + sg * Z_E
            z_i = float(zc(pin)) + sg * hh
            Yv = np.array((n[0] * w, n[1] * w, z_i - z_e))
            Lw = float(np.linalg.norm(Yv))
            Y = Yv / Lw
            sy = Lw * (w + 0.08) / w
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0], mid[1], z_e)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(P, idx=idx):
                P2 = P[..., :2]
                D = d_stack(P2, SEGS)
                d_ = D.min(0)
                m = in_poly(P2, P_LAME) & (D[idx] <= d_ + RECOUV) & (d_ < wb(P2) + 0.03)
                col, em = peint_biseau(P2, d_)
                return col, em, m

            def fil(P, idx=idx, n=n):
                P2 = P[..., :2] + n * 0.06
                D = d_stack(P2, SEGS)
                m = in_poly(P2, P_LAME) & (D[idx] <= D.min(0) + RECOUV)
                col, em = peint_fil(P2)
                return col, em, m

            spec(groupe, f"bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil})
    # plats : NB_BANDES bandes le long du manche par face, chacune plane (corde de la parabole du creux, pente de l'amincissement)
    pa = np.array(P_LAME)
    bs = np.linspace(pa[:, 1].min() - 0.02, pa[:, 1].max() + 0.02, NB_BANDES + 1)
    aa = np.linspace(pa[:, 0].min() - 0.1, pa[:, 0].max() + 0.1, 400)
    for i in range(NB_BANDES):
        b0, b1 = float(bs[i]), float(bs[i + 1])
        G = np.stack(np.meshgrid(aa, np.linspace(b0 - 0.15, b1 + 0.15, 12)), -1)
        ins = in_poly(G, P_LAME).any(0)
        a0, a1 = float(aa[ins].min()) - 0.1, float(aa[ins].max()) + 0.1
        z0_, z1_ = float(zc_b(b0)), float(zc_b(b1))
        Bi = (z1_ - z0_) / (b1 - b0)
        ac, bc, zcc = (a0 + a1) / 2, (b0 + b1) / 2, (z0_ + z1_) / 2
        for sg in (1, -1):
            X = unit(np.array((1.0, 0.0, sg * K_H)))
            Y = sg * np.array((0.0, 1.0, Bi))
            Xr, Yr, Zr = repere(X, Y)
            c = np.array((ac, bc, zcc + sg * float(h(np.array((ac, bc)))))) - Zr * (TH / 2)

            def plat(P, b0=b0, b1=b1):
                P2 = P[..., :2]
                d_ = dE(P2)
                m = in_poly(P2, P_LAME) & (d_ >= wb(P2) - 0.03) & ~in_gout(P2)
                m &= (P2[..., 1] >= b0 - RECOUV) & (P2[..., 1] <= b1 + RECOUV)
                col, em = peint_plat(P2, d_)
                return col, em, m

            spec(groupe, f"plat{'pm'[sg < 0]}{i}", c, X, Y,
                 ((a1 - a0) * math.sqrt(1 + K_H ** 2), (b1 - b0 + 0.3) * math.sqrt(1 + Bi ** 2), TH), {"south": plat})


def gouttiere(groupe):
    """Fond (âme de 0,36 px où repose la foudre) + parois verticales le long des deux bords, sur chaque face."""
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
        top = min(float(surf(np.array([x]))[0]) for x in back + [p, q]) - 0.03
        z0 = Z_FOND - 0.04
        Ln = float(np.linalg.norm(q - p))
        zm = float(zc(mid))
        for sg in (1, -1):
            zcen = zm + sg * (z0 + top) / 2
            X = np.array((d[0], d[1], 0.0))
            Y = np.array((0.0, 0.0, 1.0))
            Z = np.cross(X, Y)
            face = "south" if Z[:2] @ n < 0 else "north"

            def paroi(P):
                P2 = P[..., :2]
                dz = h(P2) - np.abs(P[..., 2] - zc(P2))
                col = lerp(METAL[1], METAL[0], np.clip((dz[..., None] - 0.1) / 0.3, 0, 1)) + np.zeros(P.shape[:-1] + (3,), np.float32)
                em = np.zeros_like(col)
                lv = dz < 0.1
                col[lv] = (190, 208, 255)
                em[lv] = (60, 100, 210)
                return col, em, np.ones(P.shape[:-1], bool)

            c = np.array((mid[0], mid[1], zcen)) + np.array((n[0], n[1], 0.0)) * (TH / 2)
            spec(groupe, f"paroi{'pm'[sg < 0]}{j}", c, X, Y, (Ln + 0.02, top - z0, TH), {face: paroi})


def controle_gouttiere():
    """Marge entre la gouttière et le bord du plat (doit rester > 0)."""
    pts = np.array([p for c in GOUT_COTES.values() for p in c])
    return float((dE(pts) - wb(pts)).min())


def conception():
    SPECS.clear()
    TILES.clear()
    volume("fer")
    gouttiere("fer")



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
    items += [("medaillon", medaillon(), None), ("cuir", t_cuir(), None), ("core", core, core_e), ("cristal", cri, cri_e),
              ("halo", t_halo(), None), ("crk", t_crk(), None),
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
    """Plan (a, b, z) de la pelle -> monde : rotation theta autour de Z, puis translation P0."""
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


def ame(g, name, masque, box, demi, pas=0.3, inset=0.12, tile="sombre"):
    """Âme pleine : tranches de `pas` px le long de b, découpées en segments le long de a là où le masque (érodé de inset)
    couvre toute la tranche ; épaisseur 2 × demi. Donne les côtés (les plaques ont des tranches transparentes)."""
    a0, a1, b0, b1 = box
    da = 0.05
    aa = np.arange(a0, a1, da) + da / 2
    n = 0
    b = b0
    while b + pas <= b1 + 1e-6:
        ok = np.ones(len(aa), bool)
        for bb in np.linspace(b, b + pas, 4):
            for off in ((0, 0), (inset, 0), (-inset, 0), (0, inset), (0, -inset)):
                P = np.stack([aa + off[0], np.full_like(aa, bb + off[1])], -1)
                ok &= masque(P)
        i = 0
        while i < len(aa):
            if ok[i]:
                j = i
                while j + 1 < len(aa) and ok[j + 1]:
                    j += 1
                if (j - i + 1) * da >= 0.25:
                    s0, s1 = aa[i] - da / 2, aa[j] + da / 2
                    boite(g, f"{name}{n}", W_((s0 + s1) / 2, b + pas / 2), Wv(1, 0), Wv(0, 1), s1 - s0, pas + 0.002, 2 * demi,
                          strip(tile))
                    n += 1
                i = j + 1
            else:
                i += 1
        b += pas
    return n


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


def Wz(x, y, dz=0.0):
    """Point du plan posé sur la surface moyenne du fer (creux de la cuillère) + dz."""
    return W_(x, y, float(zc(np.array((x, y)))) + dz)


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


def prisme16(g, nom, R, zh, tile_cote, tile_face, C):
    """Prisme à 16 pans : 16 parois de TH (côtés `tile_cote`), deux faces découpées par l'alpha."""
    C = np.asarray(C, float)
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


def seg8(g, name, p, q, w, tile, ov=0.06):
    """Tronçon octogonal (deux sections carrées à 0° et 45°)."""
    seg(g, name, p, q, w, tile, ov=ov, roll=0.0)
    seg(g, name + "o", p, q, w * 0.8, tile, ov=max(0.0, ov - 0.03), roll=45.0)


def build(theta, P0):
    elements.clear()
    groups.clear()
    _rc[0] = 0
    Repere.th, Repere.P0 = theta, np.asarray(P0, float)
    out = {}
    racine = group(objet.etape("repos", "pelle"), W_(A_O, 0))
    pelle = group("pelle", W_(A_O, 0), racine)
    # --- manche : poignée en D en volume (traverse de cuir entre embouts d'or, bras octogonaux, pointe de cristal), cuir bleu
    #     nuit entre bagues d'or, hampe d'acier, douille rivetée qui porte le fer
    manche = group("manche", W_(4.0, 0), pelle)
    AD = -2.3                                                     # traverse du D
    seg8(manche, "traverse", W_(AD, -1.45), W_(AD, 1.45), 0.9, "cuir", ov=0.0)
    for sg in (1, -1):
        c = "pm"[sg < 0]
        seg8(manche, f"embout{c}", W_(AD, sg * 1.38), W_(AD, sg * 1.9), 1.06, "or", ov=0.0)
        seg8(manche, f"bras_d{c}0", W_(0.35, sg * 0.3), W_(-0.75, sg * 1.5), 0.62, "hampe")
        seg8(manche, f"bras_d{c}1", W_(-0.75, sg * 1.5), W_(AD + 0.35, sg * 1.68), 0.62, "hampe")
        barre(manche, f"genou{c}", -0.95, -0.55, 0.36, "or", b=sg * 1.5)          # bague d'or au coude du D
    barre(manche, "pom_cri", AD - 1.0, AD - 0.35, 0.36, "cristal")
    barre(manche, "pom_cri2", AD - 1.42, AD - 0.95, 0.2, "cristal", octo=False)
    barre(manche, "fourche", -0.15, 0.55, 0.66, "metal")
    barre(manche, "bague1", 0.45, 0.9, 0.78, "or")
    barre(manche, "poignee", 0.85, 5.6, 0.62, "cuir")
    barre(manche, "bague2", 5.55, 5.95, 0.72, "or")
    barre(manche, "hampe", 5.9, 9.8, 0.55, "hampe")
    barre(manche, "bague3", 9.45, 9.85, 0.76, "or")
    barre(manche, "douille", 9.8, 10.9, 0.66, "metal")
    barre(manche, "douille2", 10.85, A_S, 0.72, "metal")
    for zs_ in (1, -1):
        for j, a in enumerate((10.35, 11.25)):
            rr = 0.66 + 0.14 * j
            for r_, rot in ((0, 0.0), (1, 45.0)):                 # rivet octogonal (deux carrés tournés)
                ang = math.radians(rot)
                boite(manche, f"rivet{'pm'[zs_ < 0]}{j}{r_}", W_(a, 0, zs_ * (rr + 0.06)), Wv(math.cos(ang), math.sin(ang)),
                      Wv(-math.sin(ang), math.cos(ang)), 0.34, 0.34, 0.16, strip("or"))
    # --- fer en vrai volume (biseaux, plats en bandes, gouttière), tambour d'or à 16 pans, marchepieds sur les épaules
    fer = group("fer", W_(A_O, 0), pelle)
    poser_specs({"fer": fer})
    prisme16(fer, "tambour", MR, float(h(np.array((A_O, 0.0)))) + 0.3, "or", "medaillon", (A_O, 0.0))
    for sg in (1, -1):
        e = [np.array(p, float) for p in epaule(sg)]
        for j, (p, q) in enumerate(((e[0], e[1]),)):               # marchepied sur le haut de l'épaule (le pied appuie)
            d = unit(q - p)
            n = np.array((-d[1], d[0]))
            if not in_poly(np.array([(p + q) / 2 + n * 0.1]), P_LAME)[0]:
                n = -n
            ext = 0.14
            p2, q2 = p - d * ext, q + d * ext
            Ln = float(np.linalg.norm(q2 - p2))
            zp, zq = float(zc(p2)), float(zc(q2))
            cc = (p2 + q2) / 2 + n * (0.2 - 0.06)
            hz = float(h(cc)) + 0.12
            X = Wv(*(q2 - p2), zq - zp)
            boite(fer, f"marchepied{'pm'[sg < 0]}{j}", W_(cc[0], cc[1], (zp + zq) / 2), X, Wv(*n), Ln, 0.4, 2 * hz,
                  strip("metal"))
    # --- foudre de la gouttière : cœur opaque + _e couché sur le fond de chaque côté, gaine add_ en NG sections
    foudre = group("foudre", W_(*SLIT[0]), fer)
    pts = [W_(a, b) for a, b in SLIT]                     # les angles vifs de la fente : un vrai zigzag
    for zs_ in (1, -1):
        for i in range(len(pts) - 1):
            seg(foudre, f"eclair{'pm'[zs_ < 0]}{i}", pts[i] + V(0, 0, zs_ * 0.22), pts[i + 1] + V(0, 0, zs_ * 0.22),
                0.34 - 0.08 * i / (len(pts) - 2), "core", roll=0.0)
    out["gaines"] = []
    per = (len(pts) - 1) // NG
    for k in range(NG):
        gg = group(f"add_gaine_{k}", tuple(pts[k * per]), foudre)
        ctrl(gg)
        for i in range(k * per, (k + 1) * per):
            pm = np.array(((SLIT[i][0] + SLIT[i + 1][0]) / 2, (SLIT[i][1] + SLIT[i + 1][1]) / 2))
            seg(gg, f"gaine{i}", pts[i], pts[i + 1], min(1.1, 2 * float(h(pm)) - 0.14), "halo", ov=0.04, roll=0.0)
        out["gaines"].append(gg)
    # fourches de la fente sur le plat (faces avant et arrière) — états seulement ; pivot sous le tambour
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
            q = p + dirn * rng.uniform(0.7, 1.0)
            for zs_ in (1, -1):
                zz = zigzag([p + dirn * 0.4, q], 3, 0.1, 70 + 10 * v + k)
                trait(fg, f"f{k}{'pm'[zs_ < 0]}", [W_(x, y, float(zs(np.array([(x, y)]), zs_)[0]) + zs_ * 0.07) for x, y, _ in zz],
                      0.16, 0.12, "crk")
        replier(fg)
        out["fourches"].append(fg)
    # --- arcs des deux bords : de la pointe vers les épaules (event_hit) ; posés sur la surface moyenne (bords relevés),
    #     pivots cachés dans le métal, 0,6 px en dedans du fil (repliés à 1/10 au repos : rien ne dépasse)
    arcs = group("arcs_bords", W_(*TIP), fer)
    out["fil"], out["rang"] = [], []
    for sg, bd in ((1, EXT_P), (-1, EXT_M)):
        at = le_long(exterieur(bd, 0.17))
        ai = le_long(exterieur(bd, -0.6))
        for k in range(N_FIL // 2):
            t0, t1 = k / (N_FIL // 2), (k + 1) / (N_FIL // 2)
            sous = [tuple(at(t)) for t in np.linspace(t0, t1, 4)]
            piv = ai((t0 + t1) / 2)
            g = group(f"add_bord_{'pm'[sg < 0]}{k}", Wz(*piv), arcs)
            ctrl(g)
            zz = zigzag(sous, 4, 0.14, 100 + 7 * k + (50 if sg < 0 else 0), zj=0.08)
            trait(g, "a", [Wz(x, y, z) for x, y, z in zz], 0.23, 0.19, "crk")
            replier(g)
            out["fil"].append(g)
            out["rang"].append(k)                                # 0 = épaule, N_FIL/2 - 1 = pointe
    # --- décharges de la pointe : a (event_hit), r (états) ; pivot caché 1,2 px en dedans du bout
    PIV = np.array(TIP) - TIP_D * 1.2
    out["pointe"] = {}
    for nm, seed, angs, lf in (("a", 5, (-40, 2, 38), 1.0), ("r", 13, (-26, 20), 0.7)):
        g = group(f"add_pointe_{nm}", W_(*PIV), arcs)
        ctrl(g)
        rng = random.Random(seed)
        for j, an in enumerate(angs):
            q = np.array(TIP) + tourner(TIP_D, an) * rng.uniform(1.0, 1.6) * lf
            zz = zigzag([TIP, tuple(q)], 3, 0.2, seed * 10 + j)
            trait(g, f"p{j}", [W_(*p) for p in zz], 0.24, 0.14, "crk")
        replier(g)
        out["pointe"][nm] = g
    # --- foudre qui tombe sur la pointe (event_select) : venue d'en haut, deux formes
    out["ciel"] = []
    for nm, seed, off in (("a", 61, 0.0), ("b", 67, 0.9)):
        g = group(f"add_ciel_{nm}", W_(*PIV), arcs)
        ctrl(g)
        haut = np.array(TIP) + unit(np.array((0.72, 0.69))) * 5.4 + np.array((off * 0.5, -off))
        zz = zigzag([tuple(haut), TIP], 6, 0.45, seed, zj=0.15)
        trait(g, "c", [W_(*p) for p in zz], 0.2, 0.3, "crk")
        b0 = np.array(zz[2][:2])
        bz = zigzag([tuple(b0), tuple(b0 + tourner(unit(np.array(TIP) - haut), 38 if nm == "a" else -38) * 1.6)], 3, 0.25, seed + 1)
        trait(g, "cb", [W_(*p) for p in bz], 0.16, 0.12, "crk")
        replier(g)
        out["ciel"].append(g)
    # --- la pointe décharge dans le sol (event_break) : trois éclairs ramifiés, deux formes
    out["roche"] = []
    for nm, seed, angs in (("a", 21, (-34, 4, 37)), ("b", 29, (-18, 24, 52))):
        g = group(f"add_roche_{nm}", W_(*PIV), arcs)
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
    out["racine"], out["pelle"] = racine, pelle
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


K = float(os.environ.get("K", "0.92"))      # 21,8 px sur la diagonale (pelle vanilla ≈ 18)
THETA = math.radians(45)          # le long de la diagonale du bloc, fer en haut à droite (vue de +Z), comme iron_shovel.png
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

# event_hit (0,7 s) : décharge de la pointe, les arcs remontent les deux bords du fer jusqu'aux épaules, trois arcs en retour.
L_HIT = 0.7
hit = anim("event_hit", L_HIT, "once")
RESTRIKES = [(0.22, 0.27), (0.32, 0.36), (0.42, 0.45)]
NB = N_FIL // 2
deplier(hit, PA)
piste_ctrl(hit, PA, onoff([(0.0, 0.09), RESTRIKES[0], RESTRIKES[2]], L_HIT))
for g, k in zip(FILS, F["rang"]):
    deplier(hit, g)
    t0 = 0.04 + 0.035 * (NB - 1 - k)                        # de la pointe (dernier tronçon) vers l'épaule
    iv = [(t0, t0 + 0.09)]
    for j, (a, b) in enumerate(RESTRIKES):
        if j == 0 or (j == 1 and k % 2 == 1) or (j == 2 and k == NB - 1):
            iv.append((a, b))
    piste_ctrl(hit, g, onoff(iv, L_HIT))
for k, g in enumerate(GAINES):
    piste_ctrl(hit, g, [kf("position", t, 1.2 * sm(t, 0.0, 0.02) * (1 - sm(t, 0.08, 0.6))
                         + 0.4 * sum(bump(t, a - 0.01, a, b, b + 0.02) for a, b in RESTRIKES)) for t in np.round(np.linspace(0, L_HIT, 36), 4)])
piste(hit, F["pelle"], [kf("rotation", t, 0, 0, 2.5 * math.sin(TAU * t / 0.07) * (1 - sm(t, 0.0, 0.28))) for t in np.round(np.linspace(0, 0.3, 19), 4)]
      + [kf("rotation", L_HIT, 0, 0, 0)])

# event_break (0,6 s) : bloc cassé. Le fer vient de mordre la terre : petit coup de levier (le fer se relève de 5° comme on
# soulève une pelletée, puis revient), la pointe décharge dans le sol (deux formes alternées), gerbe d'étincelles ; sans son.
L_BR = 0.6
brk = anim("event_break", L_BR, "once")
for g in ROCHE:
    deplier(brk, g)
piste_ctrl(brk, ROCHE[0], onoff([(0.0, 0.08), (0.17, 0.21)], L_BR))
piste_ctrl(brk, ROCHE[1], onoff([(0.08, 0.15), (0.26, 0.29)], L_BR))
for k, g in enumerate(GAINES):
    t0 = 0.03 * (NG - 1 - k)
    piste_ctrl(brk, g, [kf("position", t, 0.9 * bump(t, t0, t0 + 0.02, t0 + 0.08, t0 + 0.35)) for t in np.round(np.linspace(0, L_BR, 25), 4)])
piste(brk, F["pelle"], [kf("rotation", t, 0, 0, 5.0 * sm(t, 0.0, 0.07) * (1 - sm(t, 0.12, 0.45))) for t in np.round(np.linspace(0, L_BR, 19), 4)])
emit(brk, [kf("position", 0, 7), kf("position", 0.2, 7), kf("position", 0.21, -1), kf("position", L_BR, -1)])

ANIMS = [idle, mine, gui, sel, sw, hit, brk]

# ------------------------------------------------------------------ écriture
assert 80 <= len(elements) <= 2500, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
GUI = float(os.environ.get("GUI", "0.86"))
AFFICHAGE = objet.affichage("pelle", gui={"scale": [GUI] * 3})
model = objet.modele(NOM, "pelle", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, embarquer_sons, cle_son
limiter_sons(model)
embarquer_sons(model, {"arc_pelle": "sons/arc_pelle.ogg"})
# Un seul son, au coup qui touche (event_hit) : tools/sons.py ne connaît pas encore les événements d'objet, on le pose après.
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "arc_pelle")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur le long du manche {LONGUEUR:.1f} px ; largeur {LARGEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)}")

