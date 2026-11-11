"""Pilon de chaudière : skin d'objet (guide 14) pour toutes les masses du joueur, ensemble Steampunk (thème Mécanique). Design original.
Écrit skin_masse_steampunk.png, skin_masse_steampunk_e.png et .build/skin_masse_steampunk_brut.bbmodel à côté de ce script.

Idée (fiche .claude/references/objets/marteaux-masses.md : masse à ailettes, tête dans l'axe du manche, face de frappe ; analogie
mécanique : marteau-pilon à vapeur, dont la chaudière pousse un pilon d'acier) : une masse de chaudronnier où chaque pièce sert.
Langage du set : skin_epee_steampunk (référence), skin_hache_steampunk (infrastructure reprise : tours, cadran, foyer, jet),
ligne « Langage » de sets-objets-2026-11-08.md, .claude/styles/steampunk.md (métal propre, laiton / cuivre / acier bruni).
- tête dans l'axe du manche (masse vanilla) = **chaudière** : bas = foyer (bande d'acier, portes à fentes rougeoyantes sur les deux
  faces), milieu = **couronne dentée de laiton** (8 dents en vrai volume autour de l'axe : les ailettes de la masse deviennent les
  dents d'un engrenage), haut = ballon de cuivre riveté à **manomètre ambre** sur les deux faces (une seule aiguille) ;
- sommet = **pilon d'acier poli** (collet de laiton, face de frappe chanfreinée) sur une tige : il frappe au coup qui touche ;
- épaule : soupape (+b) et échappement (-b) : la vapeur sort vers le haut, le long du manche ;
- douille conique de laiton, manche de bois sombre bagué, poignée de cuir cousu de laiton, pommeau de laiton.
Toutes les pièces rondes sont des **tours** (couronnes de pans peints, recette de skin_masse_orage) ; chaque dent est un **prisme
fermé** (flancs inclinés, sommet chanfreiné, bouts découpés par l'alpha), pas des couches.
Lumière _e seulement sur des sources logiques : verre ambre des deux cadrans, fentes des deux portes de foyer.

Repère, prise et Display : ceux de skin_masse_abyssal (a le long du manche vers le haut à droite, b en travers dans le plan de l'image,
z vers +Z = inventaire ; poing à a = 3,5 ; préréglage _MASSE de tools/objet.py, gui ramené à la case et recentré). Étape `repos`.

Objet vivant (guide 14) :
- item_idle (24 s) : la pression monte par crans (servo : échelon, dépassement, rappel), la soupape tremble puis se soulève, deux
  décharges de white_smoke par ctrl_emit ; **sans son** ;
- event_select (0,8 s) : tour d'essai de l'aiguille par crans, la couronne avance d'une dent (45°, symétrie d'ordre 8 : pas de saut
  à la fin), la soupape claque ;
- event_swing (0,4 s) : le pilon s'arme (recule), l'aiguille perd un cran ;
- event_hit (0,9 s) : le pilon frappe (+0,55 px puis retour), la couronne avance d'une dent, l'échappement crache un jet qui monte
  (`trans_jet` = **seul dépliage par scale** du modèle, ctrl_alpha, ctrl_emit +5), l'aiguille retombe de deux crans ; **seul son**
  block.fire.extinguish à 0,04 s (arme de mêlée, ligne Langage du set).
Aucun son sur event_use_start ni event_enter_*. Pas d'item_gui (figé, net dans l'inventaire).

Fonctions avancées : calque _e (cadrans, fentes des foyers), trans_jet, ctrl_alpha, emit_mc_white_smoke, ctrl_emit, scale et position
animés, animations d'objet. Non simulés par l'aperçu : animations en main, particules, ctrl_emit, son. À juger en jeu : event_hit et
le son d'un objet (pas encore vérifiés par le développeur), la tête dans la case, taille en 1re personne.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

AVEC_E = True
NOM = "skin_masse_steampunk"
TEX = 512
TAU = 2 * math.pi
K = 16.0            # facteur de réduction du jet au repos
F_GEO = 2.0         # géométrie F_GEO / K, clés scale <= K / F_GEO

# Repère : a le long du manche (vers la tête), b en travers dans le plan de l'image, z épaisseur (+Z = inventaire).
A_ = np.array((1.0, 1.0, 0.0)) / math.sqrt(2)
W_ = np.array((-1.0, 1.0, 0.0)) / math.sqrt(2)
T_ = np.array((0.0, 0.0, 1.0))


A_PRISE = 3.5                       # repère, prise et Display de skin_masse_abyssal / skin_masse_orage (pas de recentrage)
POING = np.array((3.66, 3.74, 8.0))
G0 = POING - A_PRISE * A_


def Wp(a, b=0.0, z=0.0):
    return G0 + A_ * a + W_ * b + T_ * z


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
    x = (t - a) / (b - a)
    return x * x * (3 - 2 * x)


def smv(t, a, b):
    x = np.clip((np.asarray(t, float) - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def A(c):
    return np.array(c, np.float32)


# Palette du set (ligne Langage ; métal propre, brossé ±5 % au plus)
BRASS = dict(hi=A((236, 196, 112)), base=A((190, 142, 64)), low=A((112, 76, 32)))
COPPER = dict(hi=A((232, 150, 96)), base=A((176, 92, 52)), low=A((98, 46, 26)))
STEEL = dict(hi=A((136, 140, 150)), base=A((78, 82, 92)), low=A((38, 40, 48)))
WOOD = dict(hi=A((122, 78, 46)), base=A((84, 50, 30)), low=A((40, 22, 14)))
LEATHER = dict(hi=A((150, 96, 60)), base=A((104, 62, 36)), low=A((60, 34, 20)))
FIL = A((220, 224, 232))
POLI = A((176, 180, 190))
AMBRE = A((255, 210, 120))
AMBRE_B = A((220, 150, 50))
VAPEUR = A((250, 250, 248))
VAPEUR_B = A((220, 224, 228))



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


TH = 0.3                         # épaisseur des plaques (z-fight sous shader en dessous)
DF = 16.0                        # texels par px des faces échantillonnées


# ------------------------------------------------------------------ cubes différés (monde, recentrés après coup)
TILES = {}          # nom -> (rgba, rgba_e | None)
TRANS = set()       # tuiles semi-transparentes (groupes trans_ seulement)
CUBES = []
SIX = ("north", "south", "east", "west", "up", "down")


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


def boite(g, nom, c, X, Y, s, faces):
    """Cube monde : centre c, axes X, Y (Z = X × Y), tailles s ; faces = {face: tuile}, les autres transparentes."""
    X, Y, Z = repere(X, Y)
    CUBES.append({"groupe": g, "nom": nom, "c": np.asarray(c, float), "R": np.column_stack([X, Y, Z]),
                  "half": np.asarray(s, float) / 2, "faces": dict(faces)})


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
    """Cube dans le plan (a, b, z) ; chaque face peinte est échantillonnée texel par texel et découpée par l'alpha."""
    X, Y, Z = repere(X, Y)
    c = np.asarray(c, float)
    faces = {}
    for f, fn in peintures.items():
        P = points_face(c, X, Y, Z, s, f)
        col, al, em, m = fn(P)
        if m.any():
            faces[f] = tuile(f"{nom}_{f}", *finir(col, al, em, m))
    if faces:
        CUBES.append({"groupe": groupe, "nom": nom, "c": Wp(*c), "R": np.column_stack([Wv(*X), Wv(*Y), Wv(*Z)]),
                      "half": np.asarray(s, float) / 2, "faces": faces})

# ------------------------------------------------------------------ tours (pièces rondes, recette de skin_epee_steampunk)
OVL, OVW = 0.04, 0.03
DENS = 16.0


def p_laiton(xn, t, y, r, L, ex):
    k = np.clip(0.3 + 0.55 * (1 - np.abs(xn) ** 1.4) + ex.get("clair", 0.0), 0, 1)
    col = lerp(BRASS["low"], BRASS["hi"], k[..., None])
    if ex.get("arete"):
        col = np.where(((y < 0.06) | (y > L - 0.06))[..., None], BRASS["low"] * 0.85, col)
    return col, None


def p_cuivre(xn, t, y, r, L, ex):
    k = np.clip(0.3 + 0.55 * (1 - np.abs(xn) ** 1.4) + ex.get("clair", 0.0), 0, 1)
    col = lerp(COPPER["low"], COPPER["hi"], k[..., None])
    if ex.get("riv"):
        pas = ex["riv"]
        yy = (y + ex.get("y0", 0.0)) % pas - pas / 2
        dx = xn * ex.get("demi", 0.25)
        dd = np.hypot(dx, yy)
        col = np.where((dd < 0.15)[..., None], COPPER["low"] * 0.7, col)
        col = np.where((dd < 0.11)[..., None], BRASS["base"], col)
        col = np.where((np.hypot(dx + 0.03, yy - 0.03) < 0.05)[..., None], BRASS["hi"], col)
    if ex.get("arete"):
        col = np.where(((y < 0.05) | (y > L - 0.05))[..., None], COPPER["low"] * 0.85, col)
    return col, None


def p_acier(xn, t, y, r, L, ex):
    k = np.clip(0.25 + 0.6 * (1 - np.abs(xn) ** 1.3) + ex.get("clair", 0.0), 0, 1)
    return lerp(STEEL["low"], STEEL["hi"], k[..., None]), None


def p_poli(xn, t, y, r, L, ex):
    """Acier poli de la pointerolle et du collet : clair, arête de lumière au milieu du pan."""
    k = np.clip(0.2 + 0.7 * (1 - np.abs(xn) ** 1.2) + ex.get("clair", 0.0), 0, 1)
    col = lerp(STEEL["base"], POLI, k[..., None])
    return np.where((np.abs(xn) < 0.18)[..., None], lerp(col, FIL, 0.5), col), None


def p_bois(xn, t, y, r, L, ex):
    k = np.clip(0.35 + 0.45 * (1 - np.abs(xn) ** 1.3), 0, 1)
    col = lerp(WOOD["low"], WOOD["hi"], k[..., None])
    g = np.sin(y * 7.0 + xn * 2.2 + np.sin(y * 1.3 + xn) * 1.8)
    return col * (1 - 0.1 * (g > 0.7))[..., None], None


def p_cuir(xn, t, y, r, L, ex):
    """Cuir enroulé en spirale (bandes en biais, joint sombre), couture de laiton au milieu de chaque bande."""
    f = ((y / 0.55 + xn * 0.18) % 1.0)
    k = (1 - np.abs(xn)) * 0.35
    col = lerp(LEATHER["low"], LEATHER["hi"], (0.35 + k + 0.25 * np.clip(1 - np.abs(f - 0.5) * 2.2, 0, 1))[..., None])
    col = np.where((f < 0.12)[..., None], LEATHER["low"] * 0.7, col)
    st = (np.abs(f - 0.5) < 0.07) & (np.abs(xn) < 0.6) & ((np.floor((y + 0.05) / 0.12) % 2) == 0)
    col = np.where(st[..., None], BRASS["base"], col)
    return col, None


def p_ambre(xn, t, y, r, L, ex):
    q = np.abs(xn + 0.25)
    col = lerp(A((255, 236, 180)), AMBRE_B, np.clip(q / 1.2, 0, 1)[..., None] ** 0.9)
    em = lerp(A((225, 170, 80)), A((160, 100, 30)), np.clip(np.abs(xn), 0, 1)[..., None])
    return col, em


def p_suie(xn, t, y, r, L, ex):
    return np.zeros(xn.shape + (3,), np.float32) + A((34, 28, 24)), None


PEINTRES = {"laiton": p_laiton, "cuivre": p_cuivre, "acier": p_acier, "poli": p_poli, "bois": p_bois, "cuir": p_cuir,
            "ambre": p_ambre, "suie": p_suie}


def tuile_pan(nom, mat, L, w0, w1, r0, r1, ex):
    """Tuile d'un pan trapézoïdal : rangée 0 = bout P1 (haut de la face south)."""
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
    ex = dict(ex)
    ex.setdefault("demi", max(w0, w1) / 2)
    col, em = PEINTRES[mat](xn, t, y + ex.get("y0", 0.0), r, L, ex)
    return tuile(nom, *finir(col, None, em, mask))


def tour(g, nom, O, ax, ref, profil, n=12, phase=0.0):
    """profil = [(b0, r0, b1, r1, mat, ex), ...] le long de ax depuis O (monde) ; une couronne de n pans par tronçon."""
    O, ax = np.asarray(O, float), unit(ax)
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
            Pa, Pb = O + b0 * ax + r0 * e, O + b1 * ax + r1 * e
            Y = unit(Pb - Pa)
            N = -dr * ax + db * e
            X = np.cross(Y, N)
            CUBES.append({"groupe": g, "nom": f"{nom}{i}_{k}", "c": (Pa + Pb) / 2 - N * TH / 2, "R": np.column_stack([X, Y, N]),
                          "half": np.array((wm / 2, L / 2 + OVL, TH / 2)), "faces": {"south": tile}})


def bague(b, r_in, r_out, long, mat="laiton", ex=None):
    """Profil d'une bague posée sur un fût : flanc, dessus (arêtes marquées), flanc."""
    ex = dict(ex or {})
    return [(b, r_in, b, r_out, mat, dict(ex)), (b, r_out, b + long, r_out, mat, dict(ex, arete=True)), (b + long, r_out, b + long, r_in, mat, dict(ex))]


def tuyau(g, nom, pts, r, mat="cuivre", collier=0.3):
    """Tuyau (monde) le long d'une polyligne : un cylindre à 8 pans par tronçon, collier de laiton à chaque coude."""
    pts = [np.asarray(p, float) for p in pts]
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]
        Ln = float(np.linalg.norm(q - p))
        tour(g, f"{nom}{i}_", p, q - p, T_, [(-0.08, r, Ln + 0.08, r, mat, {})], n=8, phase=math.pi / 8)
    for i in range(1, len(pts) - 1):
        d = unit(unit(pts[i + 1] - pts[i]) + unit(pts[i] - pts[i - 1]))
        tour(g, f"{nom}c{i}_", pts[i], d, T_, bague(-0.17, r - 0.02, collier, 0.34), n=8, phase=math.pi / 8)


# ------------------------------------------------------------------ tuiles peintes (cadran, couvercles, foyer, vapeur)
def disque_t(n, fn, ss=4):
    """Tuile ronde n × n texels : fn(X, Y, R) en coordonnées -1..1 (sur-échantillonnée) -> col, em."""
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    X, Y = (xx + 0.5 - N / 2) / (N / 2), -(yy + 0.5 - N / 2) / (N / 2)
    R = np.hypot(X, Y)
    col, em = fn(X, Y, R)
    m = R < 0.985
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.LANCZOS)).astype(np.float32)
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((n, n), Image.LANCZOS)) > 110
    e = None
    if em is not None:
        e = np.array(Image.fromarray(np.clip(em, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.NEAREST)).astype(np.float32)
    return finir(rgb, None, e, al)


def f_cadran(X, Y, R):
    """Cadran : verre ambre, 13 crans (-120° à +120° depuis le haut), zone rouge en haut de l'échelle, reflet."""
    col = lerp(BRASS["hi"], BRASS["low"], np.clip(0.5 - 0.5 * Y, 0, 1)[..., None] * 0.8) * np.ones(R.shape + (1,), np.float32)
    em = np.zeros(R.shape + (3,), np.float32)
    ang = np.degrees(np.arctan2(X, Y))
    glass = R < 0.86
    col[(R > 0.86) & (R < 0.92)] = BRASS["low"] * 0.7
    g = lerp(AMBRE, AMBRE_B, np.clip(R / 0.86, 0, 1)[..., None] ** 1.5)
    col[glass] = g[glass]
    em[glass] = (190, 126, 40)
    red = glass & (R > 0.56) & (R < 0.76) & (ang > 84) & (ang < 122)
    col[red] = (176, 44, 30)
    em[red] = (150, 30, 14)
    for k in range(13):
        a = -120 + 20 * k
        r0 = 0.54 if k % 2 == 0 else 0.64
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        along = X * sa + Y * ca
        across = np.abs(X * ca - Y * sa)
        tick = glass & (along > r0) & (along < 0.8) & (across < (0.055 if k % 2 == 0 else 0.04))
        col[tick] = (58, 32, 18)
        em[tick] = 0
    hl = glass & (np.abs(R - 0.68) < 0.04) & (ang < -40) & (ang > -95)
    col[hl] = lerp(AMBRE, VAPEUR, 0.7)
    return col, em


def f_couvercle(X, Y, R):
    """Couvercle de l'œil : acier poli, cercle de laiton, 4 rivets de laiton."""
    col = lerp(POLI, STEEL["base"], np.clip(0.5 - 0.5 * Y + R * 0.3, 0, 1)[..., None]) * np.ones(R.shape + (1,), np.float32)
    col[(R > 0.6) & (R < 0.74)] = BRASS["base"]
    col[(R > 0.6) & (R < 0.64)] = BRASS["hi"]
    col[R > 0.9] = STEEL["low"]
    for k in range(4):
        th = TAU * k / 4 + TAU / 8
        dr = np.hypot(X - 0.8 * math.cos(th) * 0.95, Y - 0.8 * math.sin(th) * 0.95)
        col[dr < 0.1] = BRASS["low"]
        col[dr < 0.075] = BRASS["hi"]
    return col, None


def t_octo(nom, n, Ra, fn, N=40):
    """Tuile en polygone régulier à n côtés d'apothème Ra (couvercle), peinte par fn(X, Y, R) sur le cercle circonscrit."""
    R_ = Ra / math.cos(math.pi / n)
    yy, xx = np.mgrid[0:N, 0:N]
    x = ((xx + 0.5) / N - 0.5) * 2
    y = (0.5 - (yy + 0.5) / N) * 2
    th = np.arctan2(y, x) - math.pi / n
    sect = np.round(th / (TAU / n)) * (TAU / n) + math.pi / n
    apo = (x * np.cos(sect) + y * np.sin(sect)) * R_
    mask = apo <= Ra
    col, em = fn(x, y, np.hypot(x, y) * R_ / Ra)
    return tuile(nom, *finir(col, None, em, mask))


def t_unie(c0, c1, W=16, H=8, bord=None):
    col = lerp(c0, c1, np.linspace(0, 1, H)[:, None, None] * np.ones((1, W, 1), np.float32))
    if bord is not None:
        col[0] = col[-1] = bord
        col[:, 0] = col[:, -1] = bord
    return finir(col, None, None, np.ones((H, W), bool))


def t_aiguille():
    c = np.zeros((16, 4, 3), np.float32) + A((34, 28, 26))
    c[:6] = (190, 44, 30)
    c[:, :1] *= 1.5
    return finir(c, None, None, np.ones((16, 4), bool))


def t_foyer(W=32, H=22):
    """Porte de foyer : cadre d'acier, 3 fentes rougeoyantes (_e vif), 4 rivets de laiton."""
    c = STEEL["base"] * np.ones((H, W, 3), np.float32)
    c[:2], c[:, :2] = STEEL["hi"], STEEL["hi"]
    c[-2:], c[:, -2:] = STEEL["low"], STEEL["low"]
    e = np.zeros((H, W, 3), np.float32)
    for x0 in (8, 14, 20):
        c[4:H - 4, x0:x0 + 3] = (255, 150, 52)
        c[5:H - 5, x0 + 1] = (255, 214, 120)
        e[4:H - 4, x0:x0 + 3] = (225, 112, 28)
        e[5:H - 5, x0 + 1] = (225, 170, 70)
    for x, y in ((3, 3), (W - 5, 3), (3, H - 5), (W - 5, H - 5)):
        c[y:y + 2, x:x + 2] = BRASS["hi"]
    return finir(c, None, e, np.ones((H, W), bool))


def cell_noise(h, w, cy, cx, seed):
    r = np.random.default_rng(seed)
    a = (r.random((cy + 2, cx + 2)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((w, h), Image.BICUBIC), np.float32) / 255


def t_vapeur(W, H, seed, plume=True):
    """Vapeur en dégradé d'opacité (alpha 1–254), blanc légèrement bleuté (tuiles des groupes trans_)."""
    ss = 3
    yy, xx = np.mgrid[0:H * ss, 0:W * ss]
    u = (xx + 0.5) / (W * ss)
    v = (yy + 0.5) / (H * ss) * 2 - 1
    n1 = cell_noise(H * ss, W * ss, 4, 9, seed)
    n2 = cell_noise(H * ss, W * ss, 9, 22, seed + 1)
    lump = 0.78 + 0.32 * n1 + 0.12 * n2
    if plume:
        hw = lerp(0.24, 0.96, u ** 0.55) * (0.82 + 0.25 * n1)
        prof = np.clip(1 - (np.abs(v) / np.maximum(hw, 1e-3)) ** 2, 0, 1) ** 0.6
        along = np.clip(u / 0.05, 0, 1) * np.clip(1 - u ** 1.7, 0, 1)
        a = 250 * prof * along * lump
    else:
        puffs = np.zeros_like(u)
        for px, py, pr in ((0.5, 0.05, 0.42), (0.33, -0.18, 0.30), (0.66, -0.2, 0.30), (0.5, -0.45, 0.30), (0.42, 0.42, 0.26), (0.6, 0.4, 0.24)):
            puffs = np.maximum(puffs, np.clip(1 - np.hypot(u - px, (v - py) / 2) / pr * 0.5, 0, 1))
        a = 300 * np.clip(puffs - 0.3, 0, 1) / 0.7 * lump * np.clip((1 - v) / 0.25, 0, 1)
    a = np.clip(a, 0, 254)
    c = lerp(VAPEUR_B, VAPEUR, np.clip(1 - np.abs(v) * 0.8, 0, 1)[..., None])
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(a.astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(np.int32)
    al[al < 10] = 0
    al = np.clip(al, 0, 254)
    out = np.dstack([rgb, al]).astype(np.uint8)
    out[al == 0, :3] = VAPEUR_B.astype(np.uint8)
    return out, None



TILES["cadran"] = disque_t(40, f_cadran)
_c, _ce = TILES["cadran"]
TILES["cadran_m"] = (_c[:, ::-1].copy(), None if _ce is None else _ce[:, ::-1].copy())   # cadran arrière vu « à travers »
TILES["aiguille"] = t_aiguille()
TILES["foyer"] = t_foyer(28, 20)
TILES["acier_b"] = t_unie(STEEL["hi"], STEEL["low"], bord=STEEL["low"])
TILES["laiton_b"] = t_unie(BRASS["hi"], BRASS["low"], bord=BRASS["low"])
TILES["jet"] = t_vapeur(128, 56, 71, plume=True)
TRANS.update({"jet"})


# ------------------------------------------------------------------ conception
GROUPES = []        # (nom, pivot, parent, rotation)


def grp(nom, pivot, parent, rotation=(0.0, 0.0, 0.0)):
    GROUPES.append((nom, np.asarray(pivot, float), parent, rotation))
    return nom


def plaque_vapeur(g, nom, c, X, Y, half, tile):
    boite(g, nom, c, X, Y, 2 * np.asarray(half, float), {"south": tile, "north": tile})



# ------------------------------------------------------------------ dents de la couronne (prismes fermés, plan (r, t) autour de l'axe)
N_DENT = 8
A_C0, A_C1 = 16.05, 18.95             # couronne (anneau de laiton)
A_D0, A_D1 = 16.3, 18.7               # dents, le long de l'axe
R_ANN = 2.08                          # rayon de l'anneau
R0, R1 = 1.95, float(os.environ.get("R1", "3.55"))   # pied (caché dans l'anneau) et sommet des dents
PH_DENT = math.radians(float(os.environ.get("PHD", "22.5")))   # dents décalées : aucune face à face avec la case
W0, W1, CH = 0.55, 0.36, 0.13          # demi-largeurs au pied et au sommet, chanfrein du sommet
OVP = 0.04
DENT_POLY = [(R0, -W0), (R1 - CH, -W1), (R1, -(W1 - CH)), (R1, W1 - CH), (R1 - CH, W1), (R0, W0)]   # sens direct (r, t)


def rt(P, th):
    """Coordonnées (r, t) d'un point (a, b, z) dans le plan de la dent d'angle th (axe du manche en b = z = 0)."""
    c, s = math.cos(th), math.sin(th)
    return np.stack([P[..., 1] * c + P[..., 2] * s, -P[..., 1] * s + P[..., 2] * c], axis=-1)


def p_dent_flanc(P, th, k_bord, sommet):
    Q = rt(P, th)
    a = P[..., 0]
    if sommet:
        xn = np.clip(Q[..., 1] / W1, -1, 1)
        col = lerp(BRASS["base"], BRASS["hi"], (1 - np.abs(xn) ** 1.5)[..., None] * 0.9 + 0.1)
    else:
        k = np.clip((Q[..., 0] - R_ANN) / (R1 - R_ANN), 0, 1)
        col = lerp(BRASS["low"], BRASS["base"], (0.25 + 0.75 * k)[..., None] * k_bord)
    col = np.where(((a < A_D0 + 0.07) | (a > A_D1 - 0.07))[..., None], BRASS["low"] * 0.9, col)
    return col.astype(np.float32), None, None, np.ones(P.shape[:-1], bool)


def p_dent_bout(P, th):
    Q = rt(P, th)
    m = in_poly(Q, DENT_POLY) & (Q[..., 0] > R_ANN - 0.08)
    d = d_poly(Q, DENT_POLY[1:-1])
    col = np.zeros(P.shape[:-1] + (3,), np.float32) + BRASS["base"]
    col = lerp(col, BRASS["hi"], np.clip(1 - d / 0.12, 0, 1)[..., None] * 0.6)
    col[d < 0.05] = BRASS["low"]
    return col, None, None, m


def dent(g, j):
    th = TAU * j / N_DENT + PH_DENT
    e = np.array((0.0, math.cos(th), math.sin(th)))
    tv = np.array((0.0, -math.sin(th), math.cos(th)))
    Ax = np.array((1.0, 0.0, 0.0))
    am, LA = (A_D0 + A_D1) / 2, A_D1 - A_D0
    poly = DENT_POLY
    cen = np.mean(np.array(poly), axis=0)
    for i in range(len(poly) - 1):                # le pied (dernier côté) reste caché dans l'anneau
        p, q = np.array(poly[i]), np.array(poly[i + 1])
        L = float(np.linalg.norm(q - p))
        d = (q - p) / L
        n2 = np.array((d[1], -d[0]))
        if (p + q) / 2 @ n2 - cen @ n2 < 0:
            n2 = -n2
        Y = d[0] * e + d[1] * tv
        N3 = n2[0] * e + n2[1] * tv
        Z = np.cross(Ax, Y)
        face = "south" if Z @ N3 > 0 else "north"
        m2 = (p + q) / 2
        c = Ax * am + m2[0] * e + m2[1] * tv - N3 * (TH / 2)
        sommet = abs(d[0]) < 1e-6
        k_bord = 1.0 if n2[1] > 0 else 0.8          # un flanc un peu plus sombre que l'autre
        spec(g, f"dent{j}_c{i}", c, Ax, Y, (LA + 2 * OVP, L + 2 * OVP, TH),
             {face: (lambda P, th=th, k=k_bord, s=sommet: p_dent_flanc(P, th, k, s))})
    rs, ts = [p[0] for p in poly], [p[1] for p in poly]
    rc, tc = (min(rs) + max(rs)) / 2, (min(ts) + max(ts)) / 2
    for sg, face in ((1, "south"), (-1, "north")):
        ab = A_D1 if sg > 0 else A_D0
        c = Ax * (ab - sg * TH / 2) + rc * e + tc * tv
        spec(g, f"dent{j}_b{'pm'[sg < 0]}", c, e, tv, (max(rs) - min(rs) + 0.1, max(ts) - min(ts) + 0.1, TH),
             {face: (lambda P, th=th: p_dent_bout(P, th))})


# ------------------------------------------------------------------ conception
A_F0, A_F1 = 14.9, 16.1               # foyer
A_B0, A_B1 = 18.95, 21.25             # ballon de cuivre
A_G = 20.1                            # manomètre
RD = 1.9                              # rayon du ballon
RF = 1.95                             # rayon du foyer
B_S = 1.6                             # soupape (+b) et échappement (-b) sur l'épaule
A_SB = 21.3
OUT = {}


def conception():
    racine = grp(objet.etape("repos", "masse"), Wp(A_PRISE), None)
    masse = grp("masse", Wp(A_PRISE), racine)
    ax = A_

    # --- manche : pommeau de laiton, poignée de cuir cousu, bague, bois sombre bagué, douille conique
    prof = [(-0.65, 0.0, -0.58, 0.42, "laiton", {"clair": 0.2}), (-0.58, 0.42, -0.36, 0.74, "laiton", {}),
            (-0.36, 0.74, 0.04, 0.74, "laiton", {"arete": True}), (0.04, 0.74, 0.2, 0.66, "laiton", {}),
            (0.2, 0.66, 6.2, 0.66, "cuir", {})]
    prof += bague(6.2, 0.66, 0.78, 0.36)
    prof += [(6.56, 0.66, 6.56, 0.56, "laiton", {}), (6.56, 0.56, 14.2, 0.56, "bois", {})]
    tour(masse, "manche", Wp(0), ax, T_, prof, n=12)
    for k, a0 in enumerate((9.3, 11.9)):
        tour(masse, f"bague{k}_", Wp(0), ax, T_, bague(a0, 0.5, 0.7, 0.32), n=12)
    tour(masse, "douille", Wp(0), ax, T_, [(13.75, 0.5, 13.8, 0.62, "laiton", {}), (13.8, 0.62, 14.3, 0.74, "laiton", {"arete": True}),
                                           (14.3, 0.74, A_F0, 1.2, "laiton", {"clair": 0.1})], n=12)

    tete = grp("tete", Wp(17.5), masse)
    # --- foyer : bande d'acier, fond plat, deux portes à fentes rougeoyantes (faces +Z et -Z)
    tour(tete, "foyer", Wp(0), ax, T_, [(A_F0, 1.2, A_F0, RF, "acier", {}), (A_F0, RF, A_F1, RF, "acier", {"clair": 0.08})],
         n=16, phase=TAU / 32)
    tour(tete, "bague_f", Wp(0), ax, T_, bague(A_F0 - 0.05, RF - 0.05, RF + 0.1, 0.22), n=16, phase=TAU / 32)
    for s in (1, -1):
        fz = {f: "acier_b" for f in SIX}
        fz["south" if s > 0 else "north"] = "foyer"
        boite(tete, f"foyer_{'pm'[s < 0]}", Wp((A_F0 + A_F1) / 2 + 0.06, 0, s * (RF - 0.07)), A_, W_, (0.86, 1.2, 0.3), fz)

    # --- couronne dentée de laiton (anneau + 8 dents en prismes fermés) : avance d'une dent aux événements
    cour = grp("couronne", Wp(17.5), tete)
    tour(cour, "anneau", Wp(0), ax, T_, [(A_C0, RF - 0.05, A_C0 + 0.12, R_ANN, "laiton", {"clair": 0.15}),
                                         (A_C0 + 0.12, R_ANN, A_C1 - 0.12, R_ANN, "laiton", {}),
                                         (A_C1 - 0.12, R_ANN, A_C1, RD - 0.05, "laiton", {"clair": -0.1})], n=16, phase=TAU / 32)
    for j in range(N_DENT):
        dent(cour, j)

    # --- ballon de cuivre riveté, bague de laiton, épaule bombée
    bal = [(A_B0, RD, A_B0 + 0.35, RD, "cuivre", {"riv": 0.75, "y0": 0.2}), (A_B0 + 0.35, RD, A_B1 - 0.35, RD, "cuivre", {}),
           (A_B1 - 0.35, RD, A_B1, RD, "cuivre", {"riv": 0.75, "y0": 0.2}),
           (A_B1, RD, A_B1 + 0.2, 1.72, "cuivre", {"clair": 0.06}), (A_B1 + 0.2, 1.72, A_B1 + 0.35, 1.32, "cuivre", {"clair": 0.12}),
           (A_B1 + 0.35, 1.32, A_B1 + 0.37, 0.6, "laiton", {})]
    tour(tete, "ballon", Wp(0), ax, T_, bal, n=16, phase=TAU / 32)
    # manomètres sur les deux faces (lunette haute qui sort du ballon), une seule aiguille
    C = Wp(A_G)
    for s in (1, -1):
        cs = "pm"[s < 0]
        tour(tete, f"lunette_{cs}", C + T_ * s * 1.5, T_ * s, A_,
             [(0.0, 0.92, 0.82, 0.92, "laiton", {"arete": True}), (0.82, 0.92, 0.88, 0.8, "laiton", {"clair": 0.2})], n=16)
        boite(tete, f"cadran_{cs}", C + T_ * s * 2.26, -W_, A_, (1.74, 1.74, 0.12), {"south": "cadran"} if s > 0 else {"north": "cadran_m"})
    a0 = math.radians(-120 + 40 * 1.0)             # niveau 1 au repos
    dn = A_ * math.cos(a0) - W_ * math.sin(a0)
    aig = grp("aiguille", C, tete)
    for s in (1, -1):
        c0 = C + T_ * s * 2.36
        boite(aig, f"aiguille_{'pm'[s < 0]}", c0 + dn * 0.3, np.cross(dn, T_), dn, (0.14, 0.74, 0.06), {f: "aiguille" for f in SIX})
        boite(aig, f"moyeu_{'pm'[s < 0]}", c0 + T_ * s * 0.02, A_, W_, (0.2, 0.2, 0.1), {f: "laiton_b" for f in SIX})

    # --- pilon : tige d'acier poli (fixe), pilon mobile (collet de laiton, corps poli, face de frappe chanfreinée)
    tour(tete, "tige", Wp(0), ax, T_, [(A_B1 + 0.1, 0.62, 22.5, 0.62, "poli", {})], n=12)
    pil = grp("pilon", Wp(22.0), tete)
    tour(pil, "pilon", Wp(0), ax, T_, [(21.6, 0.62, 21.6, 1.25, "laiton", {}), (21.6, 1.25, 21.86, 1.25, "laiton", {"arete": True}),
                                       (21.86, 1.25, 21.86, 1.15, "laiton", {"clair": -0.1}), (21.86, 1.15, 22.56, 1.15, "poli", {}),
                                       (22.56, 1.15, 22.76, 0.92, "poli", {"clair": 0.1}), (22.76, 0.92, 22.78, 0.0, "poli", {"clair": 0.2})],
         n=16, phase=TAU / 32)

    # --- soupape (+b) : tige d'acier, chapeau de laiton mobile
    vb = Wp(A_SB, B_S)
    tour(tete, "soupape_tige", vb, A_, T_, [(0.0, 0.17, 0.5, 0.17, "acier", {})], n=8)
    soup = grp("soupape", vb + A_ * 0.45, tete)
    tour(soup, "soupape_chapeau", vb, A_, T_, [(0.45, 0.17, 0.45, 0.32, "laiton", {}), (0.45, 0.32, 0.72, 0.32, "laiton", {"arete": True}),
                                              (0.72, 0.32, 0.74, 0.14, "laiton", {}), (0.74, 0.14, 0.88, 0.14, "laiton", {"clair": 0.1}),
                                              (0.88, 0.14, 0.91, 0.0, "laiton", {"clair": 0.2})], n=8)
    # --- échappement (-b) : tuyau de laiton à bague, gorge de suie ; jet caché (F_GEO / K) qui jaillit le long de +a
    eb = Wp(A_SB, -B_S)
    tour(tete, "echappement", eb, A_, T_, [(0.0, 0.22, 0.6, 0.22, "laiton", {})] + bague(0.45, 0.22, 0.3, 0.17)
         + [(0.62, 0.22, 0.66, 0.0, "suie", {})], n=8, phase=math.pi / 8)
    ej = eb + A_ * 0.62
    JL, JW = 4.5, 2.6
    jet = grp("trans_jet", ej, tete)
    for k in range(3):
        ang = math.radians(60 * k + 30)
        Yp = T_ * math.cos(ang) + W_ * math.sin(ang)
        plaque_vapeur(jet, f"jet{k}", ej + A_ * (JL / 2 * F_GEO / K), A_, Yp, np.array((JL / 2, JW / 2 * 0.8, 0.15)) * F_GEO / K, "jet")
    grp("ctrl_alpha", ej, jet)
    rz = math.degrees(math.atan2(A_[1], A_[0])) - 90      # +Y du groupe le long de l'échappement
    em = grp("emit_mc_white_smoke", eb + A_ * 0.8, tete, rotation=(0.0, 0.0, rz))
    grp("ctrl_emit", eb + A_ * 0.8, em)
    OUT.update(racine=racine, aiguille=aig, soupape=soup, jet=jet, couronne=cour, pilon=pil, masse=masse)
    return racine


RACINE = conception()


# ------------------------------------------------------------------ recentrage, atlas
def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def coins_cubes(liste):
    P = []
    for cb in liste:
        for i in range(8):
            sgn = np.array([1 if (i >> k) & 1 else -1 for k in range(3)])
            P.append(cb["c"] + cb["R"] @ (cb["half"] * sgn))
    return np.array(P)




UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, (im, ime) in sorted(TILES.items(), key=lambda it: (-it[1][0].shape[0], -it[1][0].shape[1], it[0])):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, f"atlas plein ({n}, y = {y})"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None and AVEC_E:
            tex_e[y:y + h, x:x + w] = ime
        x += w + 1
        shelf = max(shelf, h)
    assert tex[TEX - 2, TEX - 2, 3] == 0
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    zone = np.zeros(semi.shape, bool)
    for n in TRANS:
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


elements, groups = [], {}
for nom, piv, parent, r in GROUPES:
    assert nom not in groups and len(nom) <= 64, nom
    groups[nom] = {"origin": [round(float(v), 4) for v in piv], "uuid": nuid(), "ids": [], "parent": parent,
                   "rotation": [round(float(v), 3) for v in r]}
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


outliner = [bone_node(RACINE)]


# ------------------------------------------------------------------ animations (objet vivant, guide 14 ; inchangées)
def kf(t, x, y, z, ch="rotation"):
    f = lambda v: v if isinstance(v, str) else f"{v + 0.0:.4f}".rstrip("0").rstrip(".")
    return {"channel": ch, "data_points": [{"x": f(x), "y": f(y), "z": f(z)}], "time": round(t, 4), "interpolation": "linear"}


def anim(name, length, tracks, fps=24, loop="loop"):
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A__ = {}
    for (g, ch), f in tracks.items():
        ks = [kf(t, *f(t), ch=ch) for t in times] if callable(f) else [kf(0.0, *f, ch=ch), kf(length, *f, ch=ch)]
        A__.setdefault(groups[g]["uuid"], {"name": g, "type": "bone", "keyframes": []})["keyframes"] += ks
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": False, "animators": A__}


def step(tau, rise=0.05, over=0.28):
    """Échelon de servo : montée courte, dépassement puis rappel amorti."""
    if tau <= 0:
        return 0.0
    v = sm(tau, 0.0, rise)
    if tau > rise * 0.6:
        x = tau - rise * 0.6
        v += over * math.sin(TAU * x / 0.15) * math.exp(-x / 0.045)
    return v


def le_long(v, d):
    w = np.asarray(d, float) * v
    return float(w[0]), float(w[1]), float(w[2])


def needle(lvl):
    """Rotation de l'aiguille pour un écart de niveau (40° par cran ; monter = sens horaire vu de +Z = z négatif)."""
    return 0.0, 0.0, -40 * lvl


def axe_angle(n, deg):
    """Matrice de rotation de deg degrés autour de l'axe unitaire n (monde)."""
    n = unit(n)
    a = math.radians(deg)
    Kx = np.array([[0, -n[2], n[1]], [n[2], 0, -n[0]], [-n[1], n[0], 0]])
    return np.eye(3) + math.sin(a) * Kx + (1 - math.cos(a)) * Kx @ Kx


def tourne(deg):
    """Rotation de la couronne de deg degrés autour de l'axe du manche (angles d'Euler du groupe)."""
    if abs(deg) < 1e-6:
        return 0.0, 0.0, 0.0
    return euler(axe_angle(A_, deg))


AIG, SOUP, JET, COUR, PIL = OUT["aiguille"], OUT["soupape"], OUT["jet"], OUT["couronne"], OUT["pilon"]
CE = "ctrl_emit"
PAS_DENT = 360.0 / N_DENT


def valve(t, tps, trem):
    y = 0.035 * trem * math.sin(TAU * 23 * t + 0.7)
    for tp in tps:
        y += 0.24 * (step(t - tp, rise=0.035, over=0.2) - step(t - tp - 0.18, rise=0.04, over=0.35))
    return le_long(y, A_)


# --- item_idle (24 s) : deux cycles de pression ; quatre crans, tremblement, décharge (soupape + vapeur à l'échappement), sans son
L_IDLE = 24.0
TICKS = [1.5, 3.5, 5.5, 7.5, 13.5, 15.5, 17.5, 19.5]
PUFFS = [10.0, 22.0]
TW = 0.8


def tremble(t):
    return sum(bump(t, tp - TW, tp - TW * 0.75, tp - 0.03, tp) for tp in PUFFS)


def idle_level(t):
    v = sum(step(t - ti) for ti in TICKS) - sum(4 * step(t - tp - 0.03, rise=0.08, over=0.1) for tp in PUFFS)
    return v + 0.13 * tremble(t) * math.sin(TAU * 19 * t)


def idle_emit(t):
    return -1 + 4 * sum(bump(t, tp + 0.02, tp + 0.08, tp + 0.35, tp + 0.5) for tp in PUFFS), 0.0, 0.0


item_idle = anim("item_idle", L_IDLE, {
    (AIG, "rotation"): lambda t: needle(idle_level(t)),
    (SOUP, "position"): lambda t: valve(t, PUFFS, tremble(t)),
    (CE, "position"): idle_emit}, fps=30)

# --- event_select (0,8 s) : tour d'essai de l'aiguille par crans, la couronne avance d'une dent, la soupape claque
L_SEL = 0.8


def sel_needle(t):
    lvl = sum(step(t - ti) for ti in (0.2, 0.3, 0.4)) - 3 * step(t - 0.58, rise=0.08, over=0.1)
    return needle(lvl)


event_select = anim("event_select", L_SEL, {
    (AIG, "rotation"): sel_needle,
    (COUR, "rotation"): lambda t: tourne(PAS_DENT * min(1.0, step(t - 0.08, rise=0.12, over=0.12))),
    (SOUP, "position"): lambda t: valve(t, [0.6], 0.0)}, fps=40, loop="once")

# --- event_swing (0,4 s) : le pilon s'arme (recule de 0,22 px) puis revient ; l'aiguille perd un cran et remonte
L_ESW = 0.4
event_swing = anim("event_swing", L_ESW, {
    (PIL, "position"): lambda t: le_long(-0.22 * (sm(t, 0.02, 0.1) - sm(t, 0.22, 0.36)), A_),
    (AIG, "rotation"): lambda t: needle(-(step(t - 0.05, rise=0.03, over=0.15) - step(t - 0.22, rise=0.08, over=0.12)))},
    fps=60, loop="once")

# --- event_hit (0,9 s) : le pilon frappe, la couronne avance d'une dent, jet qui jaillit de l'échappement et monte
# (seul dépliage par scale du modèle), soupape, aiguille -2 crans ; seul son à 0,04 s
L_HIT = 0.9


def jet_scale(t):
    w = sm(t, 0.03, 0.1) * (1 + 0.3 * sm(t, 0.1, 0.4)) * (1 - sm(t, 0.5, 0.62))
    k = (1 + (K - 1) * w) / F_GEO
    return k, k, k


def pilon_hit(t):
    v = 0.55 * sm(t, 0.0, 0.05) * (1 - sm(t, 0.12, 0.5)) + 0.06 * math.sin(TAU * (t - 0.05) / 0.12) * math.exp(-(t - 0.05) / 0.06) * (t > 0.05)
    return le_long(v, A_)


event_hit = anim("event_hit", L_HIT, {
    (JET, "scale"): jet_scale,
    (JET, "position"): lambda t: le_long(1.4 * sm(t, 0.08, 0.6) * (1 - sm(t, 0.62, 0.66)), A_),
    ("ctrl_alpha", "position"): lambda t: (-sm(t, 0.28, 0.6) * (1 - sm(t, 0.66, 0.7)), 0.0, 0.0),
    (CE, "position"): lambda t: (5 * bump(t, 0.03, 0.06, 0.3, 0.45), 0.0, 0.0),
    (SOUP, "position"): lambda t: valve(t, [0.02], 0.0),
    (PIL, "position"): pilon_hit,
    (COUR, "rotation"): lambda t: tourne(PAS_DENT * min(1.0, step(t - 0.1, rise=0.1, over=0.15))),
    (AIG, "rotation"): lambda t: needle(-2 * (step(t - 0.03, rise=0.06, over=0.1) - step(t - 0.45, rise=0.2, over=0.08)))},
    fps=40, loop="once")

ANIMS = [item_idle, event_select, event_swing, event_hit]
ANIMS[0]["selected"] = True


# ------------------------------------------------------------------ écriture
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


assert len(elements) <= 8192, f"budget : {len(elements)} cubes"
P = coins()
LONGUEUR = float(((P - G0) @ A_).max() - ((P - G0) @ A_).min())
LARGEUR = float(((P - G0) @ W_).max() - ((P - G0) @ W_).min())
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
# Display : préréglage _MASSE (item/handheld_mace du jar) ; gui ramené à la case et recentré (comme skin_masse_abyssal)
_lo, _hi = P[:, :2].min(0), P[:, :2].max(0)
GUI = float(os.environ.get("GUI", "0")) or round(min(1.0, 15.6 / float(max(_hi - _lo))), 3)
_cb = (P.min(axis=0) + P.max(axis=0)) / 2
GUI_T = [round(float(-(_cb[0] - 8) * GUI), 2), round(float(-(_cb[1] - 8) * GUI), 2), 0]
AFFICHAGE = objet.affichage("masse", gui={"translation": GUI_T, "scale": [GUI] * 3})
model = objet.modele(NOM, "masse", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son  # noqa: E402
limiter_sons(model)
# Seul son : event_hit à 0,04 s (arme de mêlée, ligne Langage du set ; jamais à 0,0 s, muet au premier coup) ; ajouté après
# limiter_sons, qui ne connaît pas les états d'objet. Aucun son au repos, au coup dans le vide ni à l'arrivée en main.
event_hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "block.fire.extinguish")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))

print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur le long du manche {LONGUEUR:.1f} px ; largeur de la tête {LARGEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. "
      f"{P.max(axis=0).round(2)} ; gui {GUI} {GUI_T}")
