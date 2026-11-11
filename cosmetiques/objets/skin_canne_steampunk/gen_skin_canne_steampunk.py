"""Canne à vapeur : skin d'objet (guide 14) pour toutes les cannes à pêche du joueur, ensemble Steampunk (thème Mécanique).
Design original. Écrit skin_canne_steampunk.png, skin_canne_steampunk_e.png et .build/skin_canne_steampunk_brut.bbmodel.

Idée (`.claude/references/objets/cannes-a-peche.md`, langage du set : ligne « Langage » de sets-objets-2026-11-08.md,
référence skin_epee_steampunk) : la canne des pêcheurs de quai de l'Atelier de laiton, où chaque pièce sert au circuit de vapeur.
- talon : pommeau de laiton, entretoise de bois sombre ; porte-moulinet de laiton fileté ; poignée de cuir cousu de laiton ;
- **petite chaudière** de cuivre rivetée posée sur le porte-moulinet (côté +b, le haut en 3e personne), calottes de laiton,
  porte de foyer à fentes rougeoyantes (`_e`) sur ses deux flancs, **soupape** sur le dessus d'où part la vapeur ;
- **moulinet à engrenages** sous la canne (côté −b) : bobine de fil d'acier entre deux flasques de laiton **dentées** (16 dents
  en volume), entraînée par un **pignon** (8 dents) à manivelle de bois ; **manomètre ambre** au moyeu sur les deux faces (une
  seule aiguille), relié à la chaudière par un fin tuyau de cuivre ; cadre en deux étriers de laiton ;
- scion d'acier bruni à 8 pans (0,62 → 0,27 px) en trois brins à viroles de laiton, anneaux de laiton ligaturés de cuivre,
  tête de laiton et anneau de tête en (15 ; 15), d'où part la ligne du jeu ; ligne = fil d'acier clair (aucune lumière).
Au repos (`repos`), la ligne pend comme sur l'image vanilla et porte un **leurre-hélice** : corps de cuivre en obus, hélice de
laiton, hameçon d'acier poli. Lancée (`lancee`), ligne et leurre sont partis (flotteur et ligne du jeu, non personnalisables).

Vrai volume (`.claude/references/objets/volume-3d.md`) : toute pièce ronde est un tour (couronne de pans de 0,3 px posés sur la
surface, face extérieure peinte et découpée par l'alpha, tranches transparentes) ; dents, étriers, anneaux, hélice = boîtes
pleines peintes sur leurs six faces. Aucune plaque peinte empilée.

Repère et Display : ceux de skin_canne_abyssal (talon en bas à gauche, pointe en haut à droite ; moulinet côté −b = bas en
3e personne ; préréglage `_CANNE` de tools/objet.py, `gui` ramené à la case). Deux copies complètes (une par étape).

Objet vivant (guide 14), format free :
- item_idle (24 s, boucle) : la pression monte par crans (servo : échelon, dépassement, rappel), la soupape tremble puis se
  soulève, deux décharges de white_smoke par ctrl_emit ; la ligne se balance, le leurre tourne et son hélice aussi ; **sans son** ;
- event_enter_lancee (0,9 s) : le scion se charge puis fouette, la bobine se dévide (3 tours), le pignon et la manivelle suivent ;
  **aucun son** (recette 4 de categories/objets.md) ;
- event_enter_repos (0,8 s) : la manivelle ramène (bobine 2 tours), la ligne retombe en se balançant ;
- event_select (0,8 s) : tour d'essai de l'aiguille par crans, la manivelle fait un tour (bobine un demi-tour), la soupape claque ;
- event_swing (0,6 s ; lancer, remontée, coup) : la soupape crache un jet qui monte (`trans_jet` = **seul dépliage par scale**,
  ctrl_alpha, ctrl_emit +5), l'aiguille perd deux crans ; **seul son** block.fire.extinguish à 0,04 s.
Rien sur event_use_start. Fonctions avancées : calque _e (cadrans, fentes du foyer), trans_jet, ctrl_alpha, emit_mc_white_smoke,
ctrl_emit, scale et position animés, son d'objet. Non simulés par l'aperçu : animations en main, particules, ctrl_emit, son.
À juger en jeu : la ligne du jeu qui part de la pointe, le son d'event_swing (lancer et remontée), le moulinet dans la case.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

AVEC_E = True
NOM = "skin_canne_steampunk"
TEX = 512
DENS = 16.0              # texels par px sur les pans
TH = 0.3                 # épaisseur d'un pan
TAU = 2 * math.pi
K = 16.0                 # facteur de réduction du jet au repos
F_GEO = 2.0              # géométrie F_GEO / K, clés scale <= K / F_GEO


def lerp(a, b, k):
    return a + (b - a) * k


def C(*c):
    return np.asarray(c, np.float32)


# ------------------------------------------------------------------ palette du set (sets-objets-2026-11-08.md, Steampunk)
BRASS = dict(hi=C(236, 196, 112), base=C(190, 142, 64), low=C(112, 76, 32))
COPPER = dict(hi=C(232, 150, 96), base=C(176, 92, 52), low=C(98, 46, 26))
STEEL = dict(hi=C(136, 140, 150), base=C(78, 82, 92), low=C(38, 40, 48))
WOOD = dict(hi=C(122, 78, 46), base=C(84, 50, 30), low=C(40, 22, 14))
LEATHER = dict(hi=C(150, 96, 60), base=C(104, 62, 36), low=C(60, 34, 20))
FIL = C(220, 224, 232)
POLI = C(176, 180, 190)
AMBRE, AMBRE_B = C(255, 210, 120), C(220, 150, 50)
VAPEUR, VAPEUR_B = C(250, 250, 248), C(220, 224, 228)

# ------------------------------------------------------------------ tuiles (atlas rempli après la géométrie)
TUILES = {}              # nom -> (rgba, e ou None)
TRANS = set()            # tuiles semi-transparentes (groupes trans_ seulement)


def tuile(nom, rgba, e=None):
    if nom not in TUILES:
        TUILES[nom] = (rgba, e)
    return nom


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


# --- peintres des pans : xn en travers (-1..1), t le long (0 = P0, 1 = P1), y en px depuis P0, r le rayon
def p_laiton(xn, t, y, r, L, ex):
    k = np.clip(0.3 + 0.55 * (1 - np.abs(xn) ** 1.4) + ex.get("clair", 0.0), 0, 1)
    col = lerp(BRASS["low"], BRASS["hi"], k[..., None])
    if ex.get("arete"):
        col = np.where(((y < 0.06) | (y > L - 0.06))[..., None], BRASS["low"] * 0.85, col)
    if ex.get("filet"):                     # filetage du porte-moulinet : sillons en biais
        f = ((y / 0.22 + xn * 0.08) % 1.0)
        col = np.where((f < 0.3)[..., None], BRASS["low"] * 0.95, col)
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


def p_ligature(xn, t, y, r, L, ex):
    """Ligature de fil de cuivre aux anneaux : spires fines."""
    k = np.clip(0.35 + 0.5 * (1 - np.abs(xn) ** 1.4), 0, 1)
    col = lerp(COPPER["low"], COPPER["hi"], k[..., None])
    return np.where((((y / 0.09) % 1.0) < 0.35)[..., None], COPPER["low"] * 0.8, col), None


def p_acier(xn, t, y, r, L, ex):
    k = np.clip(0.25 + 0.6 * (1 - np.abs(xn) ** 1.3) + ex.get("clair", 0.0), 0, 1)
    col = lerp(STEEL["low"], STEEL["hi"], k[..., None])
    return np.where((np.abs(xn) < 0.16)[..., None], lerp(col, POLI, 0.35), col), None


def p_poli(xn, t, y, r, L, ex):
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
    return np.where(st[..., None], BRASS["base"], col), None


def p_fil(xn, t, y, r, L, ex):
    """Fil d'acier enroulé sur la bobine : spires claires sur fond sombre."""
    base = lerp(STEEL["low"], STEEL["base"], (0.3 + 0.5 * (1 - np.abs(xn)))[..., None])
    spire = np.mod(y * 7.0 + 0.15 * xn, 1) < 0.55
    return np.where(spire[..., None], lerp(STEEL["hi"], FIL, (1 - np.abs(xn))[..., None] * 0.8), base), None


def p_suie(xn, t, y, r, L, ex):
    return np.zeros(xn.shape + (3,), np.float32) + C(34, 28, 24), None


PEINTRES = {"laiton": p_laiton, "cuivre": p_cuivre, "ligature": p_ligature, "acier": p_acier, "poli": p_poli, "bois": p_bois,
            "cuir": p_cuir, "fil": p_fil, "suie": p_suie}
OVL, OVW = 0.04, 0.03     # recouvrement en long et en travers entre pans voisins


def tuile_pan(nom, mat, L, w0, w1, r0, r1, ex):
    """Tuile d'un pan trapézoïdal : rangée 0 = bout P1 (haut de la face south)."""
    if nom in TUILES:
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
    return tuile(nom, *_rgba(col, mask, em))


# ------------------------------------------------------------------ tuiles peintes (cadran, flasque, foyer, vapeur, blocs)
def disque_t(nom, n, fn, ss=4):
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
    return tuile(nom, *_rgba(rgb, al, e))


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


def f_flasque(X, Y, R):
    """Face de flasque : laiton, six trous d'allègement (fond de bobine sombre), cercle gravé, bord sombre."""
    col = lerp(BRASS["hi"], BRASS["base"], np.clip(0.5 - 0.4 * Y + 0.3 * R, 0, 1)[..., None]) * np.ones(R.shape + (1,), np.float32)
    col[(R > 0.36) & (R < 0.42)] = BRASS["low"]
    col[R > 0.9] = BRASS["low"] * 0.9
    for k in range(6):
        th = TAU * k / 6
        d = np.hypot(X - 0.64 * math.cos(th), Y - 0.64 * math.sin(th))
        col[d < 0.17] = BRASS["low"] * 0.8
        col[d < 0.13] = STEEL["low"] * 0.8
    return col, None


def f_pignon(X, Y, R):
    col = lerp(BRASS["hi"], BRASS["base"], np.clip(0.5 - 0.4 * Y, 0, 1)[..., None]) * np.ones(R.shape + (1,), np.float32)
    col[(R > 0.5) & (R < 0.6)] = BRASS["low"]
    col[R > 0.88] = BRASS["low"] * 0.9
    col[R < 0.28] = STEEL["hi"]
    return col, None


def t_bloc(nom, c0, c1, W=16, H=16, bord=None):
    """Tuile pleine d'une boîte (dents, étriers, aiguille, anneaux, ligne) : dégradé en travers."""
    yy, xx = np.mgrid[0:H, 0:W]
    x = (xx + 0.5) / W * 2 - 1
    k = (1 - np.abs(x)) ** 0.8
    col = lerp(c0, c1, k[..., None])
    if bord is not None:
        col[0], col[-1], col[:, 0], col[:, -1] = bord, bord, bord, bord
    return tuile(nom, *_rgba(col, np.ones(x.shape, bool)))


def t_aiguille():
    c = np.zeros((16, 4, 3), np.float32) + C(34, 28, 26)
    c[:6] = (190, 44, 30)
    c[:, :1] *= 1.5
    return tuile("aiguille", *_rgba(c, np.ones((16, 4), bool)))


def t_foyer(W=18, H=10):
    """Porte de foyer : cadre d'acier, 3 fentes rougeoyantes (_e vif), rivets de laiton aux coins."""
    c = STEEL["base"] * np.ones((H, W, 3), np.float32)
    c[:1], c[:, :1] = STEEL["hi"], STEEL["hi"]
    c[-1:], c[:, -1:] = STEEL["low"], STEEL["low"]
    e = np.zeros((H, W, 3), np.float32)
    for x0 in (5, 8, 11):
        c[2:H - 2, x0:x0 + 2] = (255, 150, 52)
        c[3:H - 3, x0] = (255, 214, 120)
        e[2:H - 2, x0:x0 + 2] = (225, 112, 28)
        e[3:H - 3, x0] = (225, 170, 70)
    for x, y in ((1, 1), (W - 3, 1), (1, H - 3), (W - 3, H - 3)):
        c[y:y + 2, x:x + 2] = BRASS["hi"]
    return tuile("foyer", *_rgba(c, np.ones((H, W), bool), e))


def cell_noise(h, w, cy, cx, seed):
    r = np.random.default_rng(seed)
    a = (r.random((cy + 2, cx + 2)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((w, h), Image.BICUBIC), np.float32) / 255


def t_vapeur(nom, W, H, seed):
    """Panache de vapeur en dégradé d'opacité (alpha 1–254), blanc légèrement bleuté (tuile des groupes trans_)."""
    ss = 3
    yy, xx = np.mgrid[0:H * ss, 0:W * ss]
    u = (xx + 0.5) / (W * ss)
    v = (yy + 0.5) / (H * ss) * 2 - 1
    n1 = cell_noise(H * ss, W * ss, 4, 9, seed)
    n2 = cell_noise(H * ss, W * ss, 9, 22, seed + 1)
    lump = 0.78 + 0.32 * n1 + 0.12 * n2
    hw = lerp(0.24, 0.96, u ** 0.55) * (0.82 + 0.25 * n1)
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
    TRANS.add(nom)
    TUILES[nom] = (out, None)
    return nom


disque_t("cadran", 40, f_cadran)
_c, _ce = TUILES["cadran"]
TUILES["cadran_m"] = (_c[:, ::-1].copy(), None if _ce is None else _ce[:, ::-1].copy())   # cadran arrière vu « à travers »
disque_t("flasque", 44, f_flasque)
disque_t("pignon", 20, f_pignon)
t_aiguille()
t_foyer()
t_vapeur("jet", 112, 48, 71)
t_bloc("bloc_laiton", BRASS["low"], BRASS["hi"])
t_bloc("bloc_laiton_b", BRASS["hi"], BRASS["low"], bord=BRASS["low"])
t_bloc("bloc_cuivre", COPPER["low"], COPPER["hi"])
t_bloc("bloc_acier", STEEL["low"], STEEL["hi"], bord=STEEL["low"])
t_bloc("bloc_poli", STEEL["base"], FIL)
t_bloc("bloc_ligne", STEEL["hi"], FIL)
t_bloc("bloc_bois", WOOD["low"], WOOD["hi"])
CLEAR = "CLEAR"


# ------------------------------------------------------------------ repère (celui de skin_canne_abyssal)
def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


A_W = unit(V(1, 1.08, 0))        # a : le long de la canne, du talon vers la pointe (haut à droite vue de +Z)
B_W = unit(V(-1.08, 1, 0))       # b : en travers ; −b = côté du moulinet et des anneaux (le bas en 3e personne)
Z_W = V(0, 0, 1)
A_FIN = 17.2                     # bout de la tête
TIP = V(15.0, 15.1, 8.0)         # coin d'où le jeu fait partir sa ligne
G0 = TIP - A_FIN * A_W
A_PRISE = 0.5                    # milieu de la poignée = point du poing


def W(a, b=0.0, z=0.0):
    return G0 + a * A_W + b * B_W + z * Z_W


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


# ------------------------------------------------------------------ géométrie
elements, groups = [], {}        # clé unique -> groupe
ELEM_ETAPE = {}


def nuid():
    return str(_uuid.uuid4())


def group(key, origin, parent=None, name=None, rotation=(0.0, 0.0, 0.0)):
    assert key not in groups, key
    name = name or key
    assert len(name) <= 64
    groups[key] = {"name": name, "origin": [round(float(v), 3) for v in np.asarray(origin, float)], "uuid": nuid(), "ids": [],
                   "parent": parent, "rotation": [round(float(v), 3) for v in rotation]}
    return key


_ETAPE = ["repos"]


def cube_c(g, name, c, h, R, faces):
    """Cube de centre c (monde), demi-tailles h, axes R (colonnes), faces {face: CLEAR | (tuile, (u0, v0, u1, v1))}."""
    c, h = np.asarray(c, float), np.asarray(h, float)
    assert abs(np.linalg.det(R) - 1) < 1e-6, name
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in c - h],
         "to": [round(float(v), 4) for v in c + h], "origin": [round(float(v), 4) for v in c], "box_uv": False,
         "faces": {f: {"uv": uv, "texture": 0} for f, uv in faces.items()}}
    rot = euler(R)
    assert np.allclose(rmat(*rot), R, atol=1e-5), name
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])
    ELEM_ETAPE[e["uuid"]] = _ETAPE[0]
    return e


def T(tile, u0=0.0, v0=0.0, u1=1.0, v1=1.0):
    return (tile, (u0, v0, u1, v1))


SIX = ("north", "south", "east", "west", "up", "down")


def boite(g, name, c, X, Y, s, tile, faces=None):
    """Boîte pleine (monde) : axes X, Y (Z = X × Y), tailles s ; six faces peintes de `tile` (ou `faces`)."""
    X = unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    Z = np.cross(X, Y)
    f = faces if faces is not None else {k: T(tile) for k in SIX}
    f = {k: f.get(k, CLEAR) for k in SIX}
    cube_c(g, name, c, np.asarray(s, float) / 2, np.column_stack([X, Y, Z]), f)


def tour(g, nom, tnom, O, ax, ref, profil, n=16, phase=0.0):
    """profil = [(b0, r0, b1, r1, mat, ex), ...] parcouru dans le sens +ax (rayon = apothème). `tnom` nomme les tuiles
    (partagées par les deux copies d'étape). Chaque pan : plaque de TH px, face extérieure (south) peinte."""
    O, ax = np.asarray(O, float), unit(np.asarray(ax, float))
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    for i, (b0, r0, b1, r1, mat, ex) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        if L < 1e-4:
            continue
        tile = tuile_pan(f"{tnom}{i}", mat, L, 2 * r0 * tn, 2 * r1 * tn, r0, r1, ex)
        db, dr = (b1 - b0) / L, (r1 - r0) / L
        wm = max(2 * r0 * tn, 2 * r1 * tn) + 2 * OVW
        for k in range(n):
            th = phase + TAU * k / n
            e = math.cos(th) * ref + math.sin(th) * w3
            P0, P1 = O + b0 * ax + r0 * e, O + b1 * ax + r1 * e
            Y = unit(P1 - P0)
            N = -dr * ax + db * e
            X = np.cross(Y, N)
            c = (P0 + P1) / 2 - N * TH / 2
            faces = {f: CLEAR for f in SIX}
            faces["south"] = T(tile)
            cube_c(g, f"{nom}{i}_{k}", c, (wm / 2, L / 2 + OVL, TH / 2), np.column_stack([X, Y, N]), faces)


def bague(b0, b1, ra, rb, ro, mat="laiton", c=0.13, ex=None):
    """Bague biseautée : du rayon ra (b0) monte à ro, palier, redescend à rb (b1)."""
    ex = ex or {}
    return [(b0, ra, b0 + c, ro, mat, dict(ex, clair=0.12)), (b0 + c, ro, b1 - c, ro, mat, dict(ex, arete=True)),
            (b1 - c, ro, b1, rb, mat, dict(ex, clair=-0.1))]


def disque(g, nom, c, N, up, Ra, tile, n=16):
    """Disque à n pans (apothème Ra) : plaque dont seule la face extérieure (normale N) est peinte."""
    N = unit(np.asarray(N, float))
    Y = unit(up - (up @ N) * N)
    X = np.cross(Y, N)
    R = Ra / math.cos(math.pi / n)
    faces = {f: CLEAR for f in SIX}
    faces["south"] = T(tile)
    cube_c(g, nom, np.asarray(c, float) - N * TH / 2, (R, R, TH / 2), np.column_stack([X, Y, N]), faces)


def barre(g, name, a, b, s, tile, ov=0.0, Y=None, bouts=True):
    """Barre pleine de section s × s de a à b (monde), quatre faces longues peintes."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    X = unit(b - a)
    if Y is None:
        ref = Z_W if abs(X @ Z_W) < 0.9 else A_W
        Y = ref - (ref @ X) * X
    Y = unit(Y - (Y @ X) * X)
    Zc = np.cross(X, Y)
    L = float(np.linalg.norm(b - a))
    cap = T(tile, 0.3, 0.3, 0.7, 0.7) if bouts else CLEAR
    cube_c(g, name, (a + b) / 2, (L / 2 + ov, s / 2, s / 2), np.column_stack([X, Y, Zc]),
           {"north": T(tile), "south": T(tile), "up": T(tile), "down": T(tile), "east": cap, "west": cap})


def anneau(g, nom, c, ax, rg, s=0.22, n=8, tile="bloc_laiton"):
    """Anneau : n barres pleines en polygone (apothème rg) dans le plan perpendiculaire à `ax`."""
    ax = unit(np.asarray(ax, float))
    e1 = unit(B_W - (B_W @ ax) * ax)
    e2 = np.cross(ax, e1)
    side = 2 * rg * math.tan(math.pi / n)
    for k in range(n):
        th = TAU * k / n
        d = math.cos(th) * e1 + math.sin(th) * e2
        t = -math.sin(th) * e1 + math.cos(th) * e2
        m = np.asarray(c, float) + d * rg
        barre(g, f"{nom}_{k}", m - t * side / 2, m + t * side / 2, s, tile, ov=s * 0.42, Y=d)


def tuyau(g, nom, tnom, pts, r, mat="cuivre"):
    """Tuyau (monde) le long d'une polyligne : un cylindre à 8 pans par tronçon, collier de laiton à chaque coude."""
    pts = [np.asarray(p, float) for p in pts]
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]
        Ln = float(np.linalg.norm(q - p))
        tour(g, f"{nom}{i}_", f"{tnom}{i}_", p, q - p, Z_W if abs(unit(q - p) @ Z_W) < 0.9 else A_W,
             [(-0.06, r, Ln + 0.06, r, mat, {})], n=8, phase=math.pi / 8)
    for i in range(1, len(pts) - 1):
        d = unit(unit(pts[i + 1] - pts[i]) + unit(pts[i] - pts[i - 1]))
        tour(g, f"{nom}c{i}_", f"{tnom}c", pts[i], d, Z_W if abs(d @ Z_W) < 0.9 else A_W, bague(-0.14, 0.14, r - 0.02, r - 0.02, r + 0.08, c=0.05), n=8,
             phase=math.pi / 8)


def dents(g, nom, c, n, r0, r1, w, z0, z1, ph, tile="bloc_laiton"):
    """Couronne de n dents pleines (boîtes peintes sur six faces) dans le plan (A_W, B_W), de r0 à r1, z de z0 à z1."""
    for j in range(n):
        th = ph + TAU * j / n
        e = math.cos(th) * A_W + math.sin(th) * B_W
        tg = -math.sin(th) * A_W + math.cos(th) * B_W
        boite(g, f"{nom}{j}", np.asarray(c, float) + e * (r0 + r1) / 2 + Z_W * (z0 + z1) / 2, tg, e, (w, r1 - r0, z1 - z0), tile)


# ---- cotes (repère local a, b, z ; px)
A_TALON = -4.3
A_BRIN = (2.75, 7.62, 11.95)     # départ des trois brins (pivots de flexion : bague d'arrêt, viroles)
A_TETE = 15.2                    # début de la tête de laiton
GUIDES = ((5.2, 0.44), (9.5, 0.38), (12.9, 0.33), (14.4, 0.29))   # (a, rayon de l'anneau)
# moulinet : flasques dentées, bobine de fil, moyeu à manomètre
A_MOUL, B_MOUL = -2.75, -3.05
R_PL, R_BOB = 1.32, 0.95         # flasques, bobine
Z_PL, Z_GAP = 0.78, 0.4          # demi-épaisseur du tambour, demi-largeur de la gouttière
R_D0, R_D1 = 1.24, 1.66          # dents de la flasque (16)
Z_ET = 1.0                       # étriers du cadre (milieu, épaisseur 0,3)
R_LUN = 0.8                      # lunette du manomètre
# pignon (8 dents) à manivelle, côté +a (sous la poignée), dans le plan des dents de la flasque +Z
D_PIN = 2.34
R_P0, R_P1 = 0.42, 0.78
# chaudière sur le porte-moulinet (+b)
A_CH0, A_CH1, R_CH = -4.05, -1.95, 0.5
B_CH = 0.78 + 0.07 + R_CH
A_SOUP = -2.65


def r_scion(a):
    return 0.62 + (0.27 - 0.62) * (a - A_BRIN[0]) / (A_TETE - A_BRIN[0])


def profil_brin(a0, a1, guides, virole, y0):
    """Brin d'acier de a0 à a1 qui s'affine, ligatures de cuivre aux anneaux, virole de laiton au bout (sauf le dernier)."""
    out, a = [], a0
    marques = [(ga - 0.24, ga + 0.24, 0.06, "ligature") for ga, _ in guides]
    if virole:
        marques.append((a1 - 0.42, a1 + 0.0, 0.14, "laiton"))
    for m0, m1, d, mat in marques:
        out.append((a, r_scion(a), m0, r_scion(m0), "acier", {"y0": y0 + a}))
        out += bague(m0, m1, r_scion(m0), r_scion(m1), r_scion((m0 + m1) / 2) + d, mat=mat, c=0.08)
        a = m1
    if a < a1:
        out.append((a, r_scion(a), a1, r_scion(a1), "acier", {"y0": y0 + a}))
    return out


PROFIL_BASE = ([(A_TALON - 0.05, 0.0, A_TALON + 0.02, 0.5, "laiton", {"clair": 0.2}),
                (A_TALON + 0.02, 0.5, A_TALON + 0.2, 0.86, "laiton", {"clair": 0.08}),
                (A_TALON + 0.2, 0.86, A_TALON + 0.5, 0.86, "laiton", {"arete": True}),
                (A_TALON + 0.5, 0.86, A_TALON + 0.5, 0.74, "laiton", {}),
                (A_TALON + 0.5, 0.74, -3.55, 0.74, "bois", {})]
               + bague(-3.55, -3.2, 0.74, 0.78, 0.92)
               + [(-3.2, 0.78, -2.3, 0.78, "laiton", {"filet": True})]
               + bague(-2.3, -1.45, 0.78, 0.86, 0.98)
               + [(-1.45, 0.86, 2.35, 0.86, "cuir", {})]
               + bague(2.35, A_BRIN[0], 0.86, r_scion(A_BRIN[0]), 0.96))
PROFIL_TETE = (bague(A_TETE, 16.05, r_scion(A_TETE), 0.34, 0.5, c=0.15)
               + [(16.05, 0.34, A_FIN - 0.35, 0.22, "laiton", {}), (A_FIN - 0.35, 0.22, A_FIN - 0.2, 0.3, "laiton", {"clair": 0.15}),
                  (A_FIN - 0.2, 0.3, A_FIN, 0.0, "laiton", {"clair": 0.25})])
PROFILS = [PROFIL_BASE, profil_brin(A_BRIN[0], A_BRIN[1], GUIDES[:1], True, 0.0),
           profil_brin(A_BRIN[1], A_BRIN[2], GUIDES[1:2], True, 5.0), profil_brin(A_BRIN[2], A_TETE, GUIDES[2:], False, 9.0),
           PROFIL_TETE]


def centre_anneau(a, rg):
    return W(a, -(r_scion(a) + 0.2 + rg + 0.11))


A_ANT = 15.55                                 # anneau de tête, sur la tête
R_ANT = 0.26
C_ANT = W(A_ANT, -(0.5 + 0.12 + R_ANT + 0.11))
C_MOUL = W(A_MOUL, B_MOUL)
P_BOB = C_MOUL + B_W * (R_BOB + 0.09)         # la ligne quitte la bobine par le haut
C_PIN = C_MOUL + A_W * D_PIN
Y_BAS_LIGNE = 4.4                             # la ligne pendante descend jusqu'ici (image vanilla)
PH_FL = math.pi / 16                          # flasque : un creux face au pignon (direction +a)
PH_PIN = math.pi                              # pignon : une dent vers la flasque (direction −a)
A0_AIG = math.radians(-120 + 40 * 1.0)        # niveau 1 au repos (40° par cran)
RZ_EMIT = math.degrees(math.atan2(B_W[1], B_W[0])) - 90   # +Y du point d'émission le long de +b


def build(st):
    """Une copie complète de la canne dans le groupe d'étape `st` ; renvoie les groupes animés."""
    _ETAPE[0] = st
    p = st[0]
    racine = group(objet.etape(st, "canne"), W(A_PRISE))
    base = group(f"{p}_canne", W(A_PRISE), parent=racine)
    tour(base, f"{p}b", "b", W(0), A_W, B_W, PROFIL_BASE, n=8, phase=math.pi / 8)

    # --- chaudière de cuivre sur le porte-moulinet (+b) : calottes de laiton, cerclages, foyers sur les flancs, soupape
    CH = W(0, B_CH)
    prof_ch = ([(A_CH0, 0.0, A_CH0 + 0.12, 0.36, "laiton", {"clair": 0.2}), (A_CH0 + 0.12, 0.36, A_CH0 + 0.3, R_CH, "laiton", {})]
               + [(A_CH0 + 0.3, R_CH, A_CH1 - 0.3, R_CH, "cuivre", {"riv": 0.62, "y0": 0.1})]
               + [(A_CH1 - 0.3, R_CH, A_CH1 - 0.12, 0.36, "laiton", {}), (A_CH1 - 0.12, 0.36, A_CH1, 0.0, "laiton", {"clair": 0.2})])
    tour(base, f"{p}ch", "ch", CH, A_W, Z_W, prof_ch, n=12, phase=math.pi / 12)
    for k, a0 in enumerate((A_CH0 + 0.3, A_CH1 - 0.52)):
        tour(base, f"{p}cer{k}_", "cer", CH + A_W * a0, A_W, Z_W, bague(0.0, 0.22, R_CH - 0.02, R_CH - 0.02, R_CH + 0.08, c=0.05),
             n=12, phase=math.pi / 12)
    for k, a0 in enumerate((A_CH0 + 0.55, A_CH1 - 0.55)):        # deux pattes de laiton qui tiennent la chaudière
        boite(base, f"{p}patte{k}", W(a0, 0.86), A_W, B_W, (0.32, 0.36, 0.5), "bloc_laiton_b")
    for s in (1, -1):
        fz = {"south": T("foyer")} if s > 0 else {"north": T("foyer")}
        fz.update({f: T("bloc_acier") for f in ("east", "west", "up", "down")})
        boite(base, f"{p}foyer_{'pm'[s < 0]}", CH + A_W * (-3.15) + Z_W * s * (R_CH - 0.04), A_W, B_W, (1.05, 0.56, 0.3), None, faces=fz)
    vb = W(A_SOUP, B_CH + R_CH - 0.05)
    tour(base, f"{p}stige", "stige", vb, B_W, A_W, [(0.0, 0.15, 0.42, 0.15, "acier", {})], n=8)
    soup = group(f"{p}_soupape", vb + B_W * 0.4, parent=base)
    tour(soup, f"{p}schap", "schap", vb, B_W, A_W, [(0.38, 0.15, 0.38, 0.3, "laiton", {}), (0.38, 0.3, 0.62, 0.3, "laiton", {"arete": True}),
                                                    (0.62, 0.3, 0.64, 0.16, "laiton", {}), (0.64, 0.16, 0.76, 0.16, "laiton", {"clair": 0.1}),
                                                    (0.76, 0.16, 0.78, 0.0, "suie", {})], n=8)
    ej = vb + B_W * 0.7
    JL, JW = 4.0, 2.2
    jet = group(f"{p}_trans_jet", ej, parent=soup, name=f"trans_jet_{st}")
    for k in range(3):
        ang = math.radians(60 * k + 30)
        Yp = Z_W * math.cos(ang) + A_W * math.sin(ang)
        h = np.array((JL / 2, JW / 2 * 0.8, 0.15)) * F_GEO / K
        boite(jet, f"{p}jet{k}", ej + B_W * (JL / 2 * F_GEO / K), B_W, Yp, 2 * h, None, faces={"south": T("jet"), "north": T("jet")})
    alpha = group(f"{p}_ctrl_alpha", ej, parent=jet, name="ctrl_alpha")
    em = group(f"{p}_emit", ej + B_W * 0.1, parent=base, name="emit_mc_white_smoke", rotation=(0.0, 0.0, RZ_EMIT))
    ce = group(f"{p}_ctrl_emit", ej + B_W * 0.1, parent=em, name="ctrl_emit")

    # --- moulinet : cadre (deux étriers de laiton du porte-moulinet au moyeu), moyeu fixe à manomètre sur les deux faces
    moul = group(f"{p}_moulinet", C_MOUL, parent=base)
    for s in (1, -1):
        cs = "pm"[s < 0]
        top = W(A_MOUL, -0.7, s * Z_ET)
        boite(moul, f"{p}etrier_{cs}", (top + C_MOUL + Z_W * s * Z_ET) / 2, B_W, A_W, (float(np.linalg.norm(top - C_MOUL - Z_W * s * Z_ET)) + 0.3, 0.42, 0.3),
              "bloc_laiton_b")
        boite(moul, f"{p}semelle_{cs}", W(A_MOUL, -0.72, s * 0.62), A_W, B_W, (1.5, 0.2, 0.5), "bloc_laiton_b")
        tour(moul, f"{p}lun_{cs}", "lun", C_MOUL + Z_W * s * (Z_ET + 0.12), Z_W * s, A_W,
             [(0.0, R_LUN, 0.3, R_LUN, "laiton", {"arete": True}), (0.3, R_LUN, 0.34, R_LUN - 0.1, "laiton", {"clair": 0.2})], n=16)
        boite(moul, f"{p}cadran_{cs}", C_MOUL + Z_W * s * (Z_ET + 0.4), V(1, 0, 0), V(0, 1, 0), (1.58, 1.58, 0.12), None,
              faces={"south": T("cadran")} if s > 0 else {"north": T("cadran_m")})
    tour(moul, f"{p}axe", "axe", C_MOUL, Z_W, A_W, [(-Z_ET, 0.2, Z_ET, 0.2, "poli", {})], n=8)
    aig = group(f"{p}_aiguille", C_MOUL, parent=moul)
    dn = V(0, 1, 0) * math.cos(A0_AIG) + V(1, 0, 0) * math.sin(A0_AIG)
    for s in (1, -1):
        c0 = C_MOUL + Z_W * s * (Z_ET + 0.5)
        boite(aig, f"{p}aig_{'pm'[s < 0]}", c0 + dn * 0.28, np.cross(dn, Z_W), dn, (0.14, 0.7, 0.06), "aiguille")
        boite(aig, f"{p}moyeu_{'pm'[s < 0]}", c0 + Z_W * s * 0.02, V(1, 0, 0), V(0, 1, 0), (0.2, 0.2, 0.1), "bloc_laiton_b")
    # bobine (tourne) : flasques de laiton dentées, gouttière où le fil d'acier est enroulé
    bob = group(f"{p}_bobine", C_MOUL, parent=moul)
    prof_m = ([(-Z_PL, 1.1, -0.62, R_PL, "laiton", {"clair": 0.1}), (-0.62, R_PL, -Z_GAP, R_PL, "laiton", {"arete": True}),
               (-Z_GAP, R_PL, -Z_GAP, R_BOB, "laiton", {"clair": -0.2}),
               (-Z_GAP, R_BOB, Z_GAP, R_BOB, "fil", {}),
               (Z_GAP, R_BOB, Z_GAP, R_PL, "laiton", {"clair": -0.2}),
               (Z_GAP, R_PL, 0.62, R_PL, "laiton", {"arete": True}), (0.62, R_PL, Z_PL, 1.1, "laiton", {"clair": -0.1})])
    tour(bob, f"{p}m", "m", C_MOUL, Z_W, A_W, prof_m, n=16)
    for s, cs in ((1, "av"), (-1, "ar")):
        disque(bob, f"{p}fl_{cs}", C_MOUL + Z_W * s * Z_PL, Z_W * s, B_W, 1.12, "flasque")
        z0, z1 = (Z_PL - 0.38, Z_PL - 0.02) if s > 0 else (-Z_PL + 0.02, -Z_PL + 0.38)
        dents(bob, f"{p}d{cs}", C_MOUL, 16, R_D0, R_D1, 0.3, z0, z1, PH_FL)
    # pignon à manivelle (tourne en sens inverse, rapport 2), support fixe depuis l'étrier +Z
    boite(moul, f"{p}bras_pin", (C_MOUL + C_PIN) / 2 + Z_W * Z_ET, A_W, B_W, (D_PIN + 0.3, 0.3, 0.3), "bloc_laiton_b")
    pin = group(f"{p}_pignon", C_PIN, parent=moul)
    tour(pin, f"{p}pc", "pc", C_PIN, Z_W, A_W, [(Z_PL - 0.4, R_P0, Z_PL, R_P0, "laiton", {"arete": True})], n=12)
    disque(pin, f"{p}pf", C_PIN + Z_W * Z_PL, Z_W, B_W, R_P0 + 0.02, "pignon", n=12)
    disque(pin, f"{p}pf2", C_PIN + Z_W * (Z_PL - 0.4), -Z_W, B_W, R_P0 + 0.02, "pignon", n=12)
    dents(pin, f"{p}pd", C_PIN, 8, R_P0 - 0.06, R_P1, 0.26, Z_PL - 0.36, Z_PL - 0.04, PH_PIN)
    tour(pin, f"{p}paxe", "paxe", C_PIN, Z_W, A_W, [(Z_PL - 0.02, 0.14, Z_ET + 0.17, 0.14, "poli", {})], n=8)
    d_m = unit(A_W - 0.45 * B_W)
    zb = Z_ET + 0.3
    barre(pin, f"{p}manivelle", C_PIN + Z_W * zb - d_m * 0.2, C_PIN + Z_W * zb + d_m * 0.95, 0.26, "bloc_laiton_b")
    tour(pin, f"{p}bouton", "bouton", C_PIN + d_m * 0.85 + Z_W * (zb + 0.13), Z_W, A_W,
         [(0.0, 0.24, 0.62, 0.26, "bois", {}), (0.62, 0.26, 0.7, 0.3, "laiton", {}), (0.7, 0.3, 0.78, 0.0, "laiton", {"clair": 0.2})], n=8)
    # tuyau de cuivre : chaudière -> manomètre (par le flanc +Z de la canne)
    tuyau(base, f"{p}tuy", "tuy", [W(-2.05, B_CH, 0.4), W(-2.05, 0.2, 0.98), W(-2.05, -1.2, 1.12), W(-2.3, B_MOUL + 0.66, Z_ET + 0.2)], 0.12)

    # --- scion : trois brins imbriqués (pivots aux viroles), anneaux, ligne dans les anneaux
    brins, parent = [], base
    for i, a0 in enumerate(A_BRIN):
        g = group(f"{p}_brin{i + 1}", W(a0), parent=parent)
        tour(g, f"{p}s{i}", f"s{i}", W(0), A_W, B_W, PROFILS[1 + i], n=8, phase=math.pi / 8)
        brins.append(g)
        parent = g
    pts_ligne = [P_BOB]
    for ga, rg in GUIDES:
        i = sum(ga >= a0 for a0 in A_BRIN) - 1
        c = centre_anneau(ga, rg)
        anneau(brins[i], f"{p}an{ga:.0f}", c, A_W, rg)
        barre(brins[i], f"{p}pied{ga:.0f}", W(ga, -r_scion(ga) + 0.1), c + B_W * (rg - 0.05), 0.22, "bloc_laiton", Y=A_W)
        pts_ligne.append(c)
    tete = group(f"{p}_tete", W(A_TETE), parent=brins[-1])
    tour(tete, f"{p}t", "t", W(0), A_W, B_W, PROFIL_TETE, n=8, phase=math.pi / 8)
    anneau(tete, f"{p}ant", C_ANT, A_W, R_ANT, s=0.24)
    barre(tete, f"{p}piedant", W(A_ANT, -0.42), C_ANT + B_W * (R_ANT - 0.05), 0.24, "bloc_laiton", Y=A_W)
    pts_ligne.append(C_ANT)
    owners = [base] + brins[:3] + [brins[-1]]
    for j in range(len(pts_ligne) - 1):
        g = owners[min(j, len(owners) - 1)]
        barre(g, f"{p}ligne{j}", pts_ligne[j], pts_ligne[j + 1], 0.14, "bloc_ligne", ov=0.05, Y=Z_W, bouts=False)
    out = {"racine": racine, "moul": moul, "bob": bob, "pin": pin, "aig": aig, "soup": soup, "jet": jet, "alpha": alpha, "ce": ce,
           "brins": brins, "tete": tete, "bout": W(A_FIN)}

    if st == "repos":
        # --- ligne pendante (image vanilla) et leurre-hélice : émerillon de laiton, obus de cuivre, hélice, hameçon d'acier
        lg = group("r_ligne", C_ANT, parent=tete)
        bas = V(C_ANT[0], Y_BAS_LIGNE, C_ANT[2])
        barre(lg, "r_pend", C_ANT, bas, 0.14, "bloc_ligne", ov=0.05, Y=Z_W)
        le = group("r_leurre", bas, parent=lg)
        dn_ = V(0, -1, 0)
        anneau_l = bas + V(0, -0.12, 0)
        boite(le, "r_emer", anneau_l, V(1, 0, 0), V(0, 1, 0), (0.22, 0.3, 0.22), "bloc_laiton_b")
        hel = group("r_helice", bas + V(0, -0.42, 0), parent=le)
        tour(hel, "r_hmoy", "hmoy", bas + V(0, -0.27, 0), dn_, V(1, 0, 0), [(0.0, 0.0, 0.05, 0.14, "laiton", {}),
                                                                         (0.05, 0.14, 0.3, 0.14, "laiton", {})], n=8)
        for k in (1, -1):
            pal = V(k * 0.42, -0.42, 0)
            X = V(k, 0, 0)
            Yb = unit(V(0, math.cos(math.radians(28)), k * math.sin(math.radians(28))))
            boite(hel, f"r_pale{'pm'[k < 0]}", bas + pal, X, Yb, (0.62, 0.34, 0.3), "bloc_laiton")
        tour(le, "r_obus", "obus", bas + V(0, -0.55, 0), dn_, V(1, 0, 0),
             [(0.0, 0.0, 0.08, 0.26, "laiton", {"clair": 0.15}), (0.08, 0.26, 0.2, 0.3, "laiton", {"arete": True}),
              (0.2, 0.3, 0.32, 0.4, "cuivre", {}), (0.32, 0.4, 1.05, 0.4, "cuivre", {"riv": 0.36, "y0": 0.05}),
              (1.05, 0.4, 1.35, 0.24, "cuivre", {"clair": 0.08}), (1.35, 0.24, 1.48, 0.1, "laiton", {}),
              (1.48, 0.1, 1.5, 0.0, "laiton", {})], n=8, phase=math.pi / 8)
        h0 = bas + V(0, -2.0, 0)
        croc = [h0 + V(0, 0.08, 0), h0 + V(0.0, -0.55, 0), h0 + V(0.3, -0.9, 0), h0 + V(0.68, -0.76, 0), h0 + V(0.78, -0.32, 0)]
        for j in range(4):
            barre(le, f"r_croc{j}", croc[j], croc[j + 1], 0.2, "bloc_poli", ov=0.07, Y=Z_W)
        barre(le, "r_ardillon", croc[-1], croc[-1] + V(-0.24, -0.22, 0), 0.18, "bloc_poli", ov=0.05, Y=Z_W)
        out["ligne"], out["leurre"], out["helice"] = lg, le, hel
    return out


F = {st: build(st) for st in ("repos", "lancee")}


def node(key):
    g = groups[key]
    kids = [n for n, gg in groups.items() if gg["parent"] == key]
    return {"name": g["name"], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": g["ids"] + [node(k) for k in kids]}


outliner = [node(F[st]["racine"]) for st in ("repos", "lancee")]


def coins_de(e):
    f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
    R = rmat(*e.get("rotation", (0, 0, 0)))
    return [R @ (np.array([(f, t)[(i >> k) & 1][k] for k in range(3)]) - o) + o for i in range(8)]


P = np.array([c for e in elements for c in coins_de(e)])
LONGUEUR = float((P @ A_W).max() - (P @ A_W).min())


# ------------------------------------------------------------------ animations (objet vivant, guide 14)
def fmt(v):
    return v if isinstance(v, str) else f"{float(v) + 0.0:.4f}".rstrip("0").rstrip(".")


def kf(t, x, y, z, ch="rotation"):
    return {"channel": ch, "data_points": [{"x": fmt(x), "y": fmt(y), "z": fmt(z)}], "time": round(t, 4), "interpolation": "linear"}


def anim(name, length, tracks, fps=24, loop="loop"):
    """tracks = {(clé de groupe, canal): f(t) -> (x, y, z)} échantillonné à fps."""
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A__ = {}
    for (g, ch), f in tracks.items():
        A__.setdefault(groups[g]["uuid"], {"name": groups[g]["name"], "type": "bone", "keyframes": []})["keyframes"] += \
            [kf(t, *f(t), ch=ch) for t in times]
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "item_idle", "animators": A__}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


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
    """Rotation de l'aiguille (40° par cran ; monter = sens horaire vu de +Z = z négatif)."""
    return 0.0, 0.0, -40 * lvl


def rz(deg):
    return 0.0, 0.0, deg


def valve(t, tps, trem):
    y = 0.035 * trem * math.sin(TAU * 23 * t + 0.7)
    for tp in tps:
        y += 0.22 * (step(t - tp, rise=0.035, over=0.2) - step(t - tp - 0.18, rise=0.04, over=0.35))
    return le_long(y, B_W)


R_, L_ = F["repos"], F["lancee"]
FLEX = (0.22, 0.33, 0.45)        # part de la flexion portée par chaque brin

# --- item_idle (24 s) : deux cycles de pression (quatre crans, tremblement, décharge par la soupape), ligne et leurre ; sans son
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


tr = {}
for S in (R_, L_):
    tr[(S["aig"], "rotation")] = lambda t: needle(idle_level(t))
    tr[(S["soup"], "position")] = lambda t: valve(t, PUFFS, tremble(t))
    tr[(S["ce"], "position")] = idle_emit
tr[(R_["ligne"], "rotation")] = lambda t: (3.0 * math.sin(TAU * t / 4 + 1.2), 0.0, 2.2 * math.sin(TAU * t / 4))
tr[(R_["leurre"], "rotation")] = lambda t: (4.0 * math.sin(TAU * t / 4 + 0.4), 360 * 3 * t / L_IDLE, 3.5 * math.sin(TAU * t / 4 - 0.9))
tr[(R_["helice"], "rotation")] = lambda t: (0.0, -360 * 12 * t / L_IDLE, 0.0)
tr[(L_["brins"][2], "rotation")] = lambda t: (0.0, 0.0, 0.5 * math.sin(TAU * 6 * t / L_IDLE) * math.sin(TAU * 3 * t / L_IDLE) ** 2)
item_idle = anim("item_idle", L_IDLE, tr, fps=24)


# --- event_enter_lancee (0,9 s) : le scion se charge puis fouette ; la bobine se dévide (3 tours), le pignon suit (×2) ; sans son
def flex_lancer(t):
    if t < 0.2:
        return 9.0 * math.sin(math.pi / 2 * t / 0.2)
    if t < 0.32:
        u = (t - 0.2) / 0.12
        return 9.0 - 23.0 * u * u * (3 - 2 * u)
    return -14.0 * math.exp(-(t - 0.32) / 0.14) * math.cos(TAU * (t - 0.32) / 0.22)


L_LAN = 0.9


def devide(t):
    u = t / L_LAN
    return -1080 * (1 - (1 - u) ** 3) * (min(1.0, t / 0.25) ** 2)


tr = {(g, "rotation"): (lambda t, f_=f_: (0.0, 0.0, round(f_ * flex_lancer(t) * (1 if t < L_LAN - 1e-6 else 0), 3)))
      for g, f_ in zip(L_["brins"], FLEX)}
tr[(L_["bob"], "rotation")] = lambda t: rz(devide(t) if t < L_LAN - 1e-6 else -1080)
tr[(L_["pin"], "rotation")] = lambda t: rz(-2 * devide(t) if t < L_LAN - 1e-6 else 2160)
event_lancee = anim("event_enter_lancee", L_LAN, tr, fps=40, loop="once")

# --- event_enter_repos (0,8 s) : la manivelle ramène (bobine 2 tours), la ligne retombe en se balançant, à-coup du scion
L_REP = 0.8
tr = {(R_["bob"], "rotation"): lambda t: rz(720 * sm(t, 0, L_REP)),
      (R_["pin"], "rotation"): lambda t: rz(-1440 * sm(t, 0, L_REP)),
      (R_["ligne"], "rotation"): lambda t: (0.0, 0.0, 0.0 if t >= L_REP - 1e-6 else 55 * math.exp(-t / 0.16) * math.cos(TAU * t / 0.42)),
      (R_["leurre"], "rotation"): lambda t: (0.0, 0.0, 0.0 if t >= L_REP - 1e-6 else -30 * math.exp(-t / 0.2) * math.sin(TAU * t / 0.36))}
for g, f_ in zip(R_["brins"], FLEX):
    tr[(g, "rotation")] = lambda t, f_=f_: (0.0, 0.0, 0.0 if t >= L_REP - 1e-6 else round(f_ * 6.0 * math.exp(-t / 0.12) * math.sin(TAU * t / 0.2), 3))
event_repos = anim("event_enter_repos", L_REP, tr, fps=40, loop="once")

# --- event_select (0,8 s) : tour d'essai de l'aiguille par crans, la manivelle fait un tour (bobine un demi-tour : flasques à
# 6 trous et 16 dents, symétriques par 180°, pas de saut à la fin), la soupape claque
L_SEL = 0.8


def sel_needle(t):
    return needle(sum(step(t - ti) for ti in (0.2, 0.3, 0.4)) - 3 * step(t - 0.58, rise=0.08, over=0.1))


tr = {}
for S in (R_, L_):
    tr[(S["aig"], "rotation")] = sel_needle
    tr[(S["pin"], "rotation")] = lambda t: rz(-360 * sm(t, 0.05, 0.6))
    tr[(S["bob"], "rotation")] = lambda t: rz(180 * sm(t, 0.05, 0.6))
    tr[(S["soup"], "position")] = lambda t: valve(t, [0.62], 0.0)
event_select = anim("event_select", L_SEL, tr, fps=40, loop="once")

# --- event_swing (0,6 s ; lancer, remontée, coup) : la soupape crache un jet qui monte (seul dépliage par scale du modèle),
# ctrl_alpha, ctrl_emit +5, l'aiguille perd deux crans ; seul son du modèle à 0,04 s
L_SW = 0.6


def jet_scale(t):
    w = sm(t, 0.03, 0.1) * (1 + 0.3 * sm(t, 0.1, 0.35)) * (1 - sm(t, 0.42, 0.54))
    k = (1 + (K - 1) * w) / F_GEO
    return k, k, k


tr = {}
for S in (R_, L_):
    tr[(S["jet"], "scale")] = jet_scale
    tr[(S["jet"], "position")] = lambda t: le_long(1.2 * sm(t, 0.08, 0.5) * (1 - sm(t, 0.52, 0.56)), B_W)
    tr[(S["alpha"], "position")] = lambda t: (-sm(t, 0.24, 0.5) * (1 - sm(t, 0.56, 0.6)), 0.0, 0.0)
    tr[(S["ce"], "position")] = lambda t: (5 * bump(t, 0.03, 0.06, 0.28, 0.42), 0.0, 0.0)
    tr[(S["soup"], "position")] = lambda t: valve(t, [0.02], 0.0)
    tr[(S["aig"], "rotation")] = lambda t: needle(-2 * (step(t - 0.03, rise=0.06, over=0.1) - step(t - 0.38, rise=0.16, over=0.08)))
event_swing = anim("event_swing", L_SW, tr, fps=40, loop="once")

ANIMS = [item_idle, event_lancee, event_repos, event_select, event_swing]

# ------------------------------------------------------------------ atlas (tuiles créées pendant la géométrie)
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_x = _y = _sh = 0
for n, (im, em) in sorted(TUILES.items(), key=lambda it: (-it[1][0].shape[0], -it[1][0].shape[1], it[0])):
    h, w = im.shape[:2]
    if _x + w + 1 > TEX:
        _x, _y, _sh = 0, _y + _sh + 1, 0
    UV[n] = (_x, _y, _x + w, _y + h)
    tex[_y:_y + h, _x:_x + w] = im
    if em is not None:
        tex_e[_y:_y + h, _x:_x + w] = em
    _x += w + 1
    _sh = max(_sh, h)
assert _y + _sh <= TEX - 4, f"atlas plein ({_y + _sh})"
UV_CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]
semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
zone = np.zeros(semi.shape, bool)
for n in TRANS:
    u0, v0, u1, v1 = UV[n]
    zone[v0:v1, u0:u1] = True
assert not (semi & ~zone).any(), "semi-transparence hors des tuiles trans_"
assert set(np.unique(tex_e[..., 3])) <= {0, 255}
for e in elements:
    for f, fc in e["faces"].items():
        if fc["uv"] == CLEAR:
            fc["uv"] = UV_CLEAR
        else:
            nom, (u0, v0, u1, v1) = fc["uv"]
            a, b, c, d = UV[nom]
            fc["uv"] = [round(lerp(a, c, u0), 3), round(lerp(b, d, v0), 3), round(lerp(a, c, u1), 3), round(lerp(b, d, v1), 3)]


def b64(arr, path):
    im = Image.fromarray(arr, "RGBA")
    im.save(path, optimize=True)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


tex_b64 = b64(tex, f"{NOM}.png")
tex_e_b64 = b64(tex_e, f"{NOM}_e.png")

# ------------------------------------------------------------------ écriture
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
# Display : préréglage _CANNE (item/handheld_rod du jar) ; gui ramené à la case (étape repos, ligne et leurre compris)
_bb = np.array([c for e in elements if ELEM_ETAPE[e["uuid"]] == "repos" for c in coins_de(e)])
_cb = (_bb.min(axis=0) + _bb.max(axis=0)) / 2
GUI = float(os.environ.get("GUI", "0")) or round(min(1.0, 15.6 / float(max(_bb.max(axis=0)[:2] - _bb.min(axis=0)[:2]))), 2)
GUI_T = [round(float(-(_cb[0] - 8) * GUI), 2), round(float(-(_cb[1] - 8) * GUI), 2), 0]
AFFICHAGE = objet.affichage("canne", gui={"translation": GUI_T, "scale": [GUI] * 3})
model = objet.modele(NOM, "canne", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son  # noqa: E402
limiter_sons(model)
# Un seul son : event_swing (lancer, remontée, coup), clé à 0,04 s ; rien à event_enter_* ni event_use_start (recette 4).
event_swing["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "block.fire.extinguish")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      len(TUILES), "tuiles ; gui", GUI, GUI_T)
print(f"longueur {LONGUEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)} ; bout {np.round(F['repos']['bout'], 2)}")
