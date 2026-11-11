"""Masse de givre : skin d'objet (guide 14) pour toutes les masses du joueur, ensemble Givre (thème Éléments). Design original.
Écrit skin_masse_givre.png, skin_masse_givre_e.png et .build/skin_masse_givre_brut.bbmodel à côté de ce script.

Langage du set (.claude/styles/givre.md, épée/trident de givre) : glace = peau trans_ mince sur âme opaque à cœur cyan _e,
argent froid, flocons en relief à gemme hexagonale, cristaux hexagonaux pointus, fusée de cuir bleu nuit cloutée.
Silhouette propre : **masse en grappe de cristaux**. Un noyau d'argent hexagonal (prisme à 6 pans chanfreiné aux deux bouts,
deux filets de glace lumineuse qui en font le tour) d'où rayonnent des cristaux hexagonaux à section réelle (peau trans_ à
6 pans + âme opaque à filet _e), sertis dans des viroles d'argent : six cristaux en couronne au milieu (les deux du plan de
l'image longs, les quatre autres moyens, tous penchés de 20° vers le haut), deux couronnes de six petits cristaux sur les
chanfreins (vers le haut et vers le manche), un grand cristal de tête dans l'axe. Manche : pique de cristal, pommeau
d'argent, fusée de cuir cloutée, hampe d'argent baguée, collet octogonal à flocons en relief et gemmes (comme le trident),
douille.

**Vrai volume** (recette .claude/references/objets/volume-3d.md, technique des pièces rondes de skin_masse_orage) : toute pièce
ronde est un **tour** (profil (b, rayon), une couronne de pans par tronçon, pan = plaque de 0,3 px posée sur la surface, face
extérieure peinte et découpée en trapèze par l'alpha, tranches transparentes) ; aucun carré croisé, aucune plaque empilée.
Le noyau est fermé aux deux bouts : les effets repliés y sont cachés (contrôlé à la génération).

Repère (catégorie objets, Recette) : comme l'image vanilla de la masse, en diagonale, tête en haut à droite vue de +Z ;
repère local (a le long du manche, b en travers dans le plan de l'image, z vers le spectateur) de skin_masse_orage, prise
(a = 3,5) sur le point du poing. Display : préréglage _MASSE de tools/objet.py, gui 0,76. Une étape : repos.

Objet vivant (guide 14), sobre :
- item_idle (8 s, boucle) : un scintillement à la pointe d'un long cristal, puis à celle du cristal de tête ; flocons coupés ;
- item_gui : rien ne bouge ;
- event_select (0,7 s) : la glace pousse depuis ses viroles, le cristal de tête puis les couronnes en cascade ;
- event_hit (0,6 s) : la masse écrase, **le givre éclate** : étoile add_ au noyau, gerbe de 14 éclats de givre qui jaillissent
  du noyau puis rentrent, la tête frémit, flocons de Minecraft (ctrl_emit +8) ; **seul son** block.amethyst_cluster.break,
  une seule clé (aucun son dans item_idle ni ailleurs).
Pas d'item_swing (repli item_idle), pas d'event_swing (il jouerait avec event_hit au coup qui touche).
Effets repliés à 1/10 sur des pivots cachés (noyau fermé, âme des cristaux) ; chaque groupe n'est mis à l'échelle que par
une seule animation (aucune « échelle superposée »).
Fonctions avancées : trans_, add_, calque _e, ctrl_emit + emit_mc_snowflake, scale animé, animations d'objet. À juger en jeu :
la glace avec et sans shader, event_hit et son son, la grappe dans la case d'inventaire, taille en 1re personne.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

NOM = "skin_masse_givre"
TEX = 512
TAU = 2 * math.pi
FOLD = 0.1
TH = 0.3
DF = 16.0
OVL, OVW = 0.04, 0.03


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def lerp(a, b, k):
    return a + (b - a) * k


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


# ------------------------------------------------------------------ repère (celui de skin_masse_orage)
A_ = unit((1, 1, 0))            # a : le long du manche, vers la tête (haut à droite vue de +Z)
W_ = unit((-1, 1, 0))           # b : en travers, dans le plan de l'image
T_ = np.array((0.0, 0.0, 1.0))  # z : vers le spectateur
A_PRISE = 3.5
POING = np.array((3.66, 3.74, 8.0))
G0 = POING - A_PRISE * A_


def Wp(a, b=0.0, z=0.0):
    return G0 + A_ * a + W_ * b + T_ * z


# ------------------------------------------------------------------ palette (fiche givre.md)
C = lambda *c: np.array(c, np.float32)
G_LIGHT = C(214, 244, 255)
BLANC = C(244, 253, 255)
LUEUR = C(150, 226, 255)
ARG_L, ARG_M, ARG_D = C(236, 244, 250), C(166, 186, 206), C(74, 90, 116)
NUIT = C(16, 22, 50)

# ------------------------------------------------------------------ tuiles
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


# --- peintres des pans : xn en travers (-1..1), t le long (0 = début du tronçon, 1 = fin)
def p_argent(xn, t, ex):
    k = np.clip(0.45 + 0.3 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    col = lerp(ARG_D, ARG_L, (k ** 1.2)[..., None]) * (1 + 0.03 * np.sin(t * 37 + xn * 3))[..., None]
    col = np.where((np.abs(xn) > 0.86)[..., None], np.minimum(col * 1.14 + 10, 255), col)
    if ex.get("givre"):
        col = np.where(((t > 0.7) & (np.abs(xn) < 0.8))[..., None], lerp(col, BLANC, 0.6), col)
    return col, None, None


def p_noyau(xn, t, ex):
    """Palier du noyau : argent froid, deux filets de glace lumineuse (t = 0,1 et 0,9) qui font le tour, givre aux arêtes."""
    k = np.clip(0.42 + 0.32 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    col = lerp(ARG_D, ARG_L, (k ** 1.2)[..., None]) * (1 + 0.025 * np.sin(t * 29 + xn * 4))[..., None]
    col = np.where((np.abs(xn) > 0.86)[..., None], lerp(col, BLANC, 0.55), col)
    em = np.zeros(col.shape, np.float32)
    for tc in (0.1, 0.9):
        d = np.abs(t - tc)
        bord = (d >= 0.035) & (d < 0.055)
        col = np.where(bord[..., None], NUIT, col)
        fil = d < 0.035
        col = np.where(fil[..., None], C(200, 246, 255), col)
        em[fil] = LUEUR
    return col, em, None


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
    """Éclat de givre (opaque) : blanc bleuté, arêtes blanches."""
    k = np.clip(0.55 + 0.3 * (1 - np.abs(xn)) + 0.15 * t + ex.get("clair", 0.0), 0, 1)
    col = lerp(C(120, 190, 230), BLANC, k[..., None])
    return col, None, None


def p_gemme(xn, t, ex):
    k = np.clip(0.4 + 0.4 * (1 - np.abs(xn)) + 0.2 * t + ex.get("clair", 0.0), 0, 1)
    col = lerp(C(40, 130, 210), C(170, 236, 255), k[..., None])
    return col, np.clip(col * 0.8, 0, 200), None


PEINTRES = {"argent": p_argent, "noyau": p_noyau, "glace": p_glace, "peau": p_peau, "givre": p_givre, "gemme": p_gemme}


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
    """profil = [(b0, r0, b1, r1, [(mat, ex), ...]), ...] le long de ax (rayon = apothème) ; matières alternées par pan.
    Pan k centré sur la direction cos(phase + 2πk/n)·ref + sin(...)·(ax × ref)."""
    O, ax = np.asarray(O, float), unit(ax)
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    cle = cle or nom
    for i, (b0, r0, b1, r1, mats) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        if L < 1e-4:
            continue
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
ARG = [("argent", {}), ("argent", {"clair": -0.08})]


def cristal(g_trans, g_ame, nom, base, d, ref, pts, L, cle=None):
    """Cristal hexagonal à section réelle : pts = [(s, r), ...] le long de l'axe, pointe en L. Peau trans_ + âme opaque
    0,2 px en retrait (l'âme cache la peau arrière ; seuls les bords et la pointe restent vraiment transparents)."""
    cle = cle or nom
    prof_p = [(b0, r0, b1, r1, CRIS_PEAU) for (b0, r0), (b1, r1) in zip(pts[:-1], pts[1:])] + [(pts[-1][0], pts[-1][1], L, 0.0, CRIS_PEAU)]
    tour(g_trans, nom, base, d, ref, prof_p, n=6, phase=math.pi / 6, cle=cle + "_p")
    pa = [(b, max(r - 0.2, r * 0.45)) for b, r in pts]
    prof_a = [(b0, r0, b1, r1, CRIS_AME) for (b0, r0), (b1, r1) in zip(pa[:-1], pa[1:])] + [(pa[-1][0], pa[-1][1], L - 0.22, 0.0, CRIS_AME)]
    tour(g_ame, nom + "_ame", base, d, ref, prof_a, n=6, phase=math.pi / 6, cle=cle + "_a")


def bague(b0, b1, ra, ro, rb, c=0.12, mat="argent"):
    return [(b0, ra, b0 + c, ro, [(mat, {"clair": 0.15})]), (b0 + c, ro, b1 - c, ro, [(mat, {}), (mat, {"clair": -0.08})]),
            (b1 - c, ro, b1, rb, [(mat, {"clair": -0.12})])]


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
    """Barre octogonale (fusée, hampe : la technique du manche validée en jeu)."""
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
    """Plaque vue des deux côtés (scintillement additif)."""
    X, Y = unit(X), unit(Y)
    Y = unit(Y - (Y @ X) * X)
    CUBES.append({"groupe": g, "nom": nom, "c": np.asarray(c, float), "R": np.column_stack([X, Y, np.cross(X, Y)]),
                  "half": np.array((taille / 2, taille / 2, 0.15)), "faces": {"south": tile, "north": tile}})


# ------------------------------------------------------------------ conception
GROUPES = []        # (nom, pivot, parent)


def grp(nom, pivot, parent):
    GROUPES.append((nom, np.asarray(pivot, float), parent))
    return nom


# cotes (repère local, px)
A_N0, A_P0, A_P1, A_N1 = 14.6, 15.5, 18.3, 19.2     # noyau : bas, palier, haut du palier, haut
R_N0, R_N = 0.75, 1.5                               # apothème aux bouts, apothème du palier
A_C = 16.9                                          # couronne de cristaux (milieu du palier)
A_COL = 12.7                                        # collet à flocons
R_COL, Z_COL = 0.98, 0.62
OUT = {}


def r_noyau(a):
    """Apothème du noyau à l'abscisse a (contrôle des effets repliés)."""
    if A_N0 <= a <= A_P0:
        return lerp(R_N0, R_N, (a - A_N0) / (A_P0 - A_N0))
    if A_P0 <= a <= A_P1:
        return R_N
    if A_P1 <= a <= A_N1:
        return lerp(R_N, R_N0, (a - A_P1) / (A_N1 - A_P1))
    return -1.0


def flocon_collet(fl, cs, s, td, fb):
    zc = s * (Z_COL + 0.04)
    Rf = 0.8
    disque(fl, f"couvercle_{cs}", Wp(A_COL, 0, s * Z_COL), T_ * s, A_, 8, R_COL - 0.18, td)
    for k in range(3):
        th = math.radians(90 + 60 * k)
        e = math.cos(th) * A_ + math.sin(th) * W_
        barre(fl, f"bras_{cs}{k}", Wp(A_COL, 0, zc) - e * Rf, Wp(A_COL, 0, zc) + e * Rf, 0.1, 45, fb)
    for k in range(6):
        th = math.radians(90 + 60 * k)
        e = math.cos(th) * A_ + math.sin(th) * W_
        for fr, ln in ((0.55, 0.24), (0.82, 0.16)):
            base = Wp(A_COL, 0, zc + s * 0.01) + e * Rf * fr
            for sg in (-1, 1):
                t2 = th + sg * math.radians(55)
                e2 = math.cos(t2) * A_ + math.sin(t2) * W_
                barre(fl, f"branche_{cs}{k}{'pm'[sg < 0]}{int(fr * 10)}", base - e2 * 0.05, base + e2 * ln, 0.065, 45, fb)
    tour(fl, f"gemme_{cs}", Wp(A_COL, 0, s * Z_COL), T_ * s, A_,
         [(0.0, 0.28, 0.16, 0.28, [("gemme", {"clair": 0.1}), ("gemme", {"clair": -0.1})]),
          (0.16, 0.28, 0.38, 0.0, [("gemme", {"clair": 0.2}), ("gemme", {})])], n=6, cle="gemme")


def conception():
    racine = grp("repos", Wp(A_PRISE), None)
    # --- manche : pique de cristal, pommeau, fusée de cuir cloutée, hampe d'argent baguée, collet à flocons, douille
    manche = grp("manche", Wp(A_PRISE), racine)
    t_cuir()
    hampe_t = t_unie("hampe", 48, 12, ARG_M, ARG_D, ligne=ARG_L)
    tour(manche, "pommeau", Wp(0), A_, W_, [(-0.55, 0.0, -0.55, 0.5, [("argent", {"clair": -0.1})])]
         + bague(-0.55, 0.1, 0.5, 0.82, 0.66, c=0.16)
         + [(0.1, 0.66, 0.6, 0.66, ARG)], n=8, phase=math.pi / 8)
    pique = grp("pique", Wp(-0.5), manche)
    cristal(grp("trans_pique", Wp(-0.5), pique), grp("ame_pique", Wp(-0.5), pique), "pique", Wp(-0.45), -A_, W_,
            [(0.0, 0.44), (0.45, 0.5)], 1.75)
    bar8(manche, "fusee", Wp(0.5), Wp(6.5), 0.62, "cuir")
    tour(manche, "virole_fusee", Wp(0), A_, W_, bague(6.35, 7.05, 0.56, 0.74, 0.56), n=8, phase=math.pi / 8)
    bar8(manche, "hampe", Wp(6.9), Wp(14.3), 0.5, hampe_t)
    for k, a_ in enumerate((9.6,)):
        tour(manche, f"bague{k}", Wp(0), A_, W_, bague(a_ - 0.25, a_ + 0.25, 0.47, 0.62, 0.47), n=8, phase=math.pi / 8)
    td = t_disque("disque_collet", 8, R_COL - 0.18)
    tour(manche, "collet", Wp(A_COL), T_, A_, bague(-Z_COL, Z_COL, R_COL - 0.18, R_COL, R_COL - 0.18, c=0.16), n=8, phase=math.pi / 8)
    bras_t = t_unie("bras", 32, 8, ARG_L, ARG_M, ligne=BLANC)
    cap_t = t_unie("bras_bout", 8, 8, BLANC, ARG_M)
    fb = {f: bras_t for f in ("south", "north", "up", "down")}
    fb.update(east=cap_t, west=cap_t)
    for s in (1, -1):
        cs = "e" if s > 0 else "i"
        flocon_collet(grp(f"flocon_{cs}", Wp(A_COL, 0, s * Z_COL), manche), cs, s, td, fb)
    tour(manche, "douille", Wp(0), A_, W_, [(14.05, 0.5, 14.2, 0.62, [("argent", {"clair": 0.15})]),
                                            (14.2, 0.62, 14.75, 0.8, ARG)], n=8, phase=math.pi / 8)

    # --- tête : noyau d'argent hexagonal fermé (pans centrés sur les cristaux de la couronne)
    tete = grp("tete", Wp(A_C), racine)
    NOY = [("noyau", {}), ("noyau", {"clair": -0.07})]
    tour(tete, "noyau", Wp(0), A_, W_,
         [(A_N0, 0.0, A_N0, R_N0, [("argent", {"clair": -0.12})]),
          (A_N0, R_N0, A_P0, R_N, [("argent", {"clair": 0.05, "givre": True}), ("argent", {"clair": -0.05, "givre": True})]),
          (A_P0, R_N, A_P1, R_N, NOY),
          (A_P1, R_N, A_N1, R_N0, [("argent", {"clair": 0.12}), ("argent", {"clair": 0.02})]),
          (A_N1, R_N0, A_N1, 0.0, [("argent", {"clair": 0.18})])], n=6, phase=0.0)

    OUT["cristaux"] = []                               # (ordre de pousse, groupe)
    # couronne du milieu : 6 cristaux penchés de 20° vers le haut ; les deux du plan de l'image (b = ±) longs
    for k in range(6):
        th = TAU * k / 6
        e = math.cos(th) * W_ + math.sin(th) * T_
        d = unit(e * math.cos(math.radians(20)) + A_ * math.sin(math.radians(20)))
        base = Wp(A_C) + e * (R_N - 0.15)
        long_ = k in (0, 3)
        tour(tete, f"virole_c{k}", base, d, A_, bague(-0.15, 0.55, 0.62, 0.74, 0.62, c=0.1), n=6, phase=math.pi / 6,
             cle="virole_c")
        g = grp(f"cristal_c{k}", base, tete)
        if long_:
            cristal(grp(f"trans_c{k}", base, g), grp(f"ame_c{k}", base, g), f"c{k}", base, d, A_,
                    [(0.0, 0.5), (1.1, 0.62), (2.9, 0.56)], 4.0, cle="cl")
        else:
            cristal(grp(f"trans_c{k}", base, g), grp(f"ame_c{k}", base, g), f"c{k}", base, d, A_,
                    [(0.0, 0.48), (0.8, 0.56), (2.0, 0.5)], 2.9, cle="cm")
        OUT["cristaux"].append((1 if long_ else 2, g))
        if k == 0:
            OUT["tip_long"] = base + d * 3.1
    # couronnes des chanfreins : 6 petits cristaux entre les grands (vers le manche, puis vers le haut)
    for ring, (a_b, rb, tilt, L, pts, ordre) in enumerate(((15.2, 0.95, -38, 1.75, [(0.0, 0.3), (0.5, 0.36), (1.0, 0.33)], 4),
                                                           (18.8, 0.85, 48, 2.1, [(0.0, 0.34), (0.6, 0.4), (1.25, 0.37)], 3))):
        for k in range(6):
            th = TAU * (k + 0.5) / 6
            e = math.cos(th) * W_ + math.sin(th) * T_
            d = unit(e * math.cos(math.radians(tilt)) + A_ * math.sin(math.radians(tilt)))
            base = Wp(a_b) + e * rb
            nm = f"{'bh'[ring]}{k}"
            g = grp(f"cristal_{nm}", base, tete)
            cristal(grp(f"trans_{nm}", base, g), grp(f"ame_{nm}", base, g), nm, base, d, A_, pts, L, cle=f"r{ring}")
            OUT["cristaux"].append((ordre, g))
    # grand cristal de tête, dans l'axe, serti dans une virole posée sur le haut du noyau
    tour(tete, "virole_t", Wp(A_N1 - 0.15), A_, W_, bague(0.0, 0.55, 0.66, 0.8, 0.7, c=0.1), n=6, phase=math.pi / 6)
    g = grp("cristal_t", Wp(A_N1), tete)
    cristal(grp("trans_t", Wp(A_N1), g), grp("ame_t", Wp(A_N1), g), "t", Wp(A_N1 + 0.1), A_, W_,
            [(0.0, 0.56), (1.3, 0.7), (3.2, 0.62)], 4.6)
    OUT["cristaux"].append((0, g))
    OUT["tip_t"] = Wp(A_N1 + 0.1 + 3.6)

    # --- effets repliés à 1/10 : scintillements (item_idle) dans l'âme des cristaux, étoile et éclats (event_hit) dans le noyau
    et = t_etoile("etoile")
    for nm, c, taille in (("add_scint_long", OUT["tip_long"], 2.0), ("add_scint_t", OUT["tip_t"], 2.3)):
        g = grp(nm, c, tete)
        plaque2(g, f"{nm}_a", c, A_, W_, taille, et)
        plaque2(g, f"{nm}_b", c, A_, T_, taille * 0.8, et)
        OUT[nm] = g
    centre = Wp(A_C)
    g = grp("add_eclat", centre, tete)
    for j, (X, Y) in enumerate(((A_, W_), (A_, T_), (W_, T_))):
        plaque2(g, f"add_eclat_{j}", centre + A_ * 0.4, X, Y, 4.6 - 0.4 * j, et)
    OUT["add_eclat"] = g
    OUT["eclats"] = grp("eclats", centre, tete)
    rng = np.random.default_rng(17)
    for j in range(14):
        # directions réparties sur la sphère (spirale de Fibonacci), sans aller vers le manche
        z = 1 - 2 * (j + 0.5) / 14
        ph = j * math.pi * (3 - math.sqrt(5))
        rr = math.sqrt(1 - z * z)
        da = 0.15 + 0.85 * (z + 1) / 2 - 0.25        # composante le long du manche, de -0,1 à +0,75
        dv = unit(A_ * da + (W_ * math.cos(ph) + T_ * math.sin(ph)) * max(rr, 0.55))
        L = 1.6 + 1.1 * rng.uniform()
        p0 = centre + dv * (R_N + 0.9)
        ref = unit(np.cross(dv, T_ if abs(dv @ T_) < 0.9 else A_))
        tour(OUT["eclats"], f"eclat{j}", p0, dv, ref,
             [(0.0, 0.12, L * 0.55, 0.2, GIVRE_MAT), (L * 0.55, 0.2, L, 0.0, GIVRE_MAT)], n=6, cle=f"ecl{j % 3}")
    emit = grp("emit_mc_snowflake", Wp(A_C, 0.0, 0.0), tete)
    grp("ctrl_emit", Wp(A_C, 0.0, 0.0), emit)
    OUT["racine"], OUT["tete"] = racine, tete
    return [racine]


RACINES = conception()

# ------------------------------------------------------------------ repli des effets
REPLIES = [OUT[k] for k in ("add_scint_long", "add_scint_t", "add_eclat", "eclats")]
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


def coins_cube(cb):
    return [cb["c"] + cb["R"] @ (cb["half"] * np.array([(-1, 1)[(i >> k) & 1] for k in range(3)])) for i in range(8)]


# contrôle : éclats et étoile repliés dans le noyau fermé ; scintillements dans l'âme des cristaux (pas au bord)
_hors = set()
for cb in CUBES:
    if cb["groupe"] in ("add_eclat", "eclats"):
        for p in coins_cube(cb):
            v = p - G0
            a, rad = v @ A_, math.hypot(v @ W_, v @ T_)
            if not (rad < r_noyau(a) * 0.95 - 0.12):
                _hors.add(cb["nom"])
assert not _hors, f"effets repliés hors du noyau : {sorted(_hors)}"

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


def pousse(t0, dur, L, over=1.07):
    keys = [kf("scale", 0.0, 0.05)]
    if t0 > 0:
        keys.append(kf("scale", t0, 0.05))
    for k in range(1, 11):
        u = k / 10
        v = 0.05 + (over - 0.05) * (1 - (1 - u / 0.7) ** 2) if u <= 0.7 else lerp(over, 1.0, (u - 0.7) / 0.3)
        keys.append(kf("scale", t0 + dur * u, v))
    if t0 + dur < L - 1e-4:
        keys.append(kf("scale", L, 1.0))
    return keys


def emit(an, keys):
    piste(an, "ctrl_emit", keys)


# item_idle (8 s) : un scintillement à la pointe d'un long cristal, puis à celle du cristal de tête ; émetteur coupé.
L_IDLE = 8.0
idle = anim("item_idle", L_IDLE, "loop")
piste(idle, OUT["add_scint_long"], pop(2.0, 0.5, L_IDLE))
piste(idle, OUT["add_scint_t"], pop(5.4, 0.45, L_IDLE, 0.9))
emit(idle, [kf("position", 0, -1, 0, 0), kf("position", L_IDLE, -1, 0, 0)])

# item_gui : rien ne bouge, émetteur coupé.
gui = anim("item_gui", 4.0, "loop")
emit(gui, [kf("position", 0, -1, 0, 0), kf("position", 4.0, -1, 0, 0)])

# event_select (0,7 s) : la glace pousse depuis ses viroles, cristal de tête, grands, moyens, puis petites couronnes.
L_SEL = 0.7
sel = anim("event_select", L_SEL)
for i, (ordre, g) in enumerate(OUT["cristaux"]):
    piste(sel, g, pousse(0.07 * ordre + 0.012 * (i % 6), 0.3, L_SEL, 1.08))

# event_hit (0,6 s) : le givre éclate — étoile au noyau, gerbe d'éclats qui jaillit puis rentre, la tête frémit, flocons.
L_HIT = 0.6
hit = anim("event_hit", L_HIT)
piste(hit, OUT["add_eclat"], pop(0.0, 0.32, L_HIT, 1.1))
ks = [kf("scale", 0.0, 1.0)]
for t in echant(L_HIT, 24)[1:]:
    ks.append(kf("scale", t, 1 + (DEPLIE * 1.08 - 1) * sm(t, 0.0, 0.05) * (1 - sm(t, 0.24, 0.46))))
piste(hit, OUT["eclats"], ks)
piste(hit, OUT["tete"], [kf("rotation", t, 0, 0, round(-3.0 * math.exp(-t / 0.1) * math.sin(TAU * t / 0.16), 3)) for t in echant(L_HIT, 24)])
emit(hit, [kf("position", 0, 8, 0, 0), kf("position", 0.22, 8, 0, 0), kf("position", 0.23, -1, 0, 0), kf("position", L_HIT, -1, 0, 0)])

ANIMS = [idle, gui, sel, hit]

# ------------------------------------------------------------------ écriture
assert 150 <= len(elements) <= 4000, f"budget : {len(elements)} cubes"


def coins(sauf=()):
    P = []
    ids = {u for n in sauf for u in groups[n]["ids"]}
    for e in elements:
        if e["uuid"] in ids:
            continue
        f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
        R = rotm(*e.get("rotation", (0, 0, 0)))
        for i in range(8):
            c = np.array([(f, t)[(i >> k) & 1][k] for k in range(3)])
            P.append(R @ (c - o) + o)
    return np.array(P)


P = coins(sauf=REPLIES)
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
# Display : préréglage _MASSE (item/handheld_mace du jar) ; gui ramené à la case (boîte plus grande que 16 px)
GUI = float(os.environ.get("GUI", "0.76"))
_cb = (P.min(axis=0) + P.max(axis=0)) / 2
GUI_T = [round(float(-(_cb[0] - 8) * GUI), 2), round(float(-(_cb[1] - 8) * GUI), 2), 0]
AFFICHAGE = objet.affichage("masse", gui={"translation": GUI_T, "scale": [GUI] * 3})
model = objet.modele(NOM, "masse", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son
limiter_sons(model)
# Un seul son, au coup qui touche (event_hit), une seule clé à 0,04 s (le mod ne joue rien au tout premier instant : une clé à 0,0 est muette) ; tools/sons.py ne connaît pas encore les événements d'objet.
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "block.amethyst_cluster.break")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


LONG = float(((P - G0) @ A_).max() - ((P - G0) @ A_).min())
LARG = float(((P - G0) @ W_).max() - ((P - G0) @ W_).min())
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur {LONG:.1f} px, largeur de tête {LARG:.1f} px ; boîte visible {P.min(0).round(2)} .. {P.max(0).round(2)}")
