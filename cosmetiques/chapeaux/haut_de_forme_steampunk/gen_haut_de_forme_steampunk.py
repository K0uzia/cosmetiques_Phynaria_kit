"""Haut-de-forme Steampunk : ensemble Steampunk (thème Mécanique). Design original. Refonte du 2026-11-08.
Écrit haut_de_forme_steampunk.png, _e.png, _r.png et .build/haut_de_forme_steampunk_brut.bbmodel à côté de ce script.
Ancien générateur : .build/gen_avant.py (version du 2026-11-05) et .build/gen_avant_v1.py.

Retour de l'utilisateur (2026-11-08) : « mécanique revoir tout sauf aile et hibou », « revois les tete et epaule ».
L'ancien chapeau se lisait comme une boîte brun-noir : calotte octogonale presque carrée (élargie aux coins pour la règle
des 4,62 px), petits engrenages illisibles, lunettes minuscules.

Ce qui change (proportions d'un vrai haut-de-forme, sources plus bas) :
- le chapeau est POSÉ sur le dessus de la tête (bord à y >= 32,62) : la calotte peut enfin être ronde (16 pans), un peu
  cintrée à mi-hauteur puis évasée vers le haut (« slightly waisted crown »), dessus plat ; hauteur 7,9 px pour 9,4 de
  large (rapport d'un vrai chapeau : 14 cm pour 17) ; une jupe de feutre carrée (face intérieure à 4,68 px) descend
  jusqu'à y = 31,7 et cache le jour entre la tête et le bord ; bord ovale (7,1 x 6,4), relevé de 20° sur les côtés,
  bordé de cuir ; ruban de cuir cousu (1,6 px, une boucle de laiton à gauche) ;
- une seule machine, dont chaque pièce sert : la porte de foyer à l'arrière (fentes rougeoyantes, _e) chauffe la calotte-
  chaudière ; le manomètre à droite lit la pression (cadran éclairé) ; un tuyau de cuivre en monte vers la cheminée du
  dessus (soupape, bouffées de vapeur), un autre descend vers le petit moteur à vapeur posé sur le bord avant droit ;
  le pignon du moteur entraîne la roue dentée de la charnière : les grandes lunettes d'aviateur (coques de cuivre, verres
  ambre éclairés) passent par l'avant du bord et viennent devant les yeux en sneak, verres toujours droits (biellette) ;
  puis deux loupes d'horloger pivotent l'une après l'autre devant le verre droit (mise au point), et tout remonte.
- mouvement mécanique (fiche de style) : crans avec dépassement et rappel, arrivée en butée avec rebond, pièces décalées
  dans le temps ; cycle de pression (aiguille qui monte par crans, soupape qui tremble, décharge : bouffée, aiguille qui
  retombe) ; vapeur qui monte, jamais qui retombe ;
- pas d'attack ni de hurt (pièce portée) ; event_equip (1,5 s) : le chapeau tombe sur la tête et rebondit, les loupes
  font un essai, l'aiguille bondit, la soupape lâche un jet ; un seul son (à l'équipement).

Fonctions avancées utilisées (docs/guide-cosmetiques.md 4 bis, 5 ter, 6.4), à juger en jeu (/cosmetique apercu) :
- calque _e (verres, cadran, fentes du foyer, fente du sifflet) ; trans_vapeur (bouffées) + ctrl_alpha ; trans_jet ;
- emit_mc_white_smoke (bouche de la cheminée) + ctrl_emit (-1 hors décharge, +4 pendant la décharge), non simulé ;
- event_equip ; reflets _r écrits mais coupés tant que REFLETS = False (tools/ambiance.py).

Sources (proportions et mécanismes, aucune œuvre) : anatomie du chapeau https://blog.tenthstreethats.com/posts/anatomy-of-a-hat ;
mesures d'un haut-de-forme de soie (calotte 14 cm, bord 4,5 cm devant et derrière, ruban 4 cm, calotte légèrement cintrée,
bord relevé sur les côtés) https://collections.hampshireculture.org.uk/object/top-hat-mens-black-silk-plush-high-slightly-waisted-crown-deep-hatband-black-wool-frieze ;
lunettes d'atelier à loupes basculantes (loupes d'horloger sur l'oculaire droit, ressort qui les tient en place)
https://www.instructables.com/Steampunk-Googles , https://lostbiro.com/blog/?p=1488 ; fiche .claude/references/objets/chapeaux-lunettes.md.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # calque _e embarqué (réactivé le 2026-11-03, correctif du mod annoncé, à vérifier en jeu)
TEX = 512
TAU = 2 * math.pi
NOM = "haut_de_forme_steampunk"

# ------------------------------------------------------------------ palette (.claude/styles/steampunk.md)
FELT = dict(base=(52, 40, 36), hi=(96, 78, 66), low=(26, 20, 18))
BRASS = dict(base=(190, 142, 64), hi=(236, 196, 112), low=(112, 76, 32))
COPPER = dict(base=(176, 92, 52), hi=(232, 150, 96), low=(98, 46, 26))
STEEL = dict(base=(78, 82, 92), hi=(136, 140, 150), low=(38, 40, 48))
LEATHER = dict(base=(104, 62, 36), hi=(150, 96, 60), low=(60, 34, 20))


def A(c):
    return np.array(c, np.float32)


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


FELT = dict(base=(70, 50, 43), hi=(124, 96, 80), low=(34, 24, 20))        # feutre brun chaud (l'ancien brun-noir se lisait en bloc)
# ------------------------------------------------------------------ peinture
def cell_noise(h, w, cells, seed):
    r = np.random.default_rng(seed)
    a = (r.random((max(2, int(cells * h / max(h, w))) + 2, max(2, int(cells * w / max(h, w))) + 2)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((w, h), Image.BICUBIC), np.float32) / 255


def inset(mask, n):
    im = Image.fromarray(mask.astype(np.uint8) * 255, "L")
    d = np.zeros(mask.shape, np.float32)
    for _ in range(n):
        im = im.filter(ImageFilter.MinFilter(3))
        d += np.array(im) > 127
    return d


def rivet(col, x, y, r, metal):
    """Rivet peint : anneau sombre, tête, éclat. 3 texels au moins."""
    h, w = col.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dd = np.hypot(xx + 0.5 - x, yy + 0.5 - y)
    col[dd <= r + 1.0] = A(metal["low"]) * 0.6
    col[dd <= r] = A(metal["base"])
    col[np.hypot(xx + 0.5 - x + r * 0.3, yy + 0.5 - y + r * 0.3) <= r * 0.5] = A(metal["hi"])


def finish(col, mask):
    out = np.zeros(mask.shape + (4,), np.uint8)
    c = np.clip(col, 0, 255)
    if mask.any():
        c[~mask] = c[mask].mean(axis=0)
    out[..., :3] = c.astype(np.uint8)
    out[..., 3] = mask * 255
    return out


def grid(W, H, w, h, ss=1):
    """Coordonnées locales d'une plaque (a vers la droite, b vers le haut), au centre de chaque texel."""
    jj, ii = np.mgrid[0:H * ss, 0:W * ss]
    return ((ii + 0.5) / (W * ss) - 0.5) * w, (0.5 - (jj + 0.5) / (H * ss)) * h


def ss_mask(W, H, w, h, fn, ss=3):
    a, b = grid(W, H, w, h, ss)
    return fn(a, b).reshape(H, ss, W, ss).mean(axis=(1, 3)) > 0.5


def felt_col(W, H, w, h, seed, sheen=0.25, top_edge=True):
    """Feutre brun-noir : duvet fin, stries verticales, reflet doux, liseré clair en haut."""
    a, b = grid(W, H, w, h)
    r = np.random.default_rng(seed)
    streak = np.array(Image.fromarray((r.random((3, max(4, W // 2))) * 255).astype(np.uint8), "L").resize((W, H), Image.BILINEAR), np.float32) / 255
    fine = cell_noise(H, W, max(W, H) // 2, seed + 1)
    blot = cell_noise(H, W, 6, seed + 2)
    col = A(FELT["base"]) * np.ones((H, W, 3), np.float32)
    col *= (0.90 + 0.10 * fine + 0.14 * (streak - 0.5) + 0.10 * (blot - 0.5))[..., None]
    sx = sheen * w
    col = lerp(col, A(FELT["hi"]), (0.42 * np.exp(-((a - sx) / (0.16 * w)) ** 2) * (0.55 + 0.45 * (b / h + 0.5)))[..., None])
    col *= (0.84 + 0.16 * (b / h + 0.5))[..., None]
    if top_edge:
        col[:2] = A(FELT["hi"]) * 0.95
    return col


TILES, TILES_E, SEMI = {}, {}, set()
N16 = 16
T16 = math.tan(math.pi / N16)


def felt_plain(W, H, seed, grad=(0.86, 1.0)):
    """Feutre sans reflet peint (l'éclairage par face fait le rond) : duvet fin, légères stries, dégradé vertical."""
    r = np.random.default_rng(seed)
    streak = np.array(Image.fromarray((r.random((3, max(4, W // 3))) * 255).astype(np.uint8), "L").resize((W, H), Image.BILINEAR), np.float32) / 255
    fine = cell_noise(H, W, max(W, H) // 2, seed + 1)
    blot = cell_noise(H, W, 5, seed + 2)
    col = A(FELT["base"]) * np.ones((H, W, 3), np.float32)
    col *= (0.92 + 0.08 * fine + 0.06 * (streak - 0.5) + 0.06 * (blot - 0.5))[..., None]
    g = np.linspace(grad[1], grad[0], H)[:, None, None]
    return col * g


# ---- calotte : deux étages de 16 pans (bas légèrement rentrant, haut évasé), dessus plat
YC0, YW, YC1 = 33.25, 36.75, 41.15
AP0, APW, AP1 = 4.72, 4.60, 4.95             # apothèmes (distance du centre aux pans) en bas, à la taille, en haut
TIERS = [(YC0, YW, AP0, APW), (YW, YC1, APW, AP1)]


def apo(y):
    for y0, y1, a0, a1 in TIERS:
        if y0 - 1e-6 <= y <= y1 + 1e-6:
            return lerp(a0, a1, (y - y0) / (y1 - y0))
    return AP0 if y < YC0 else AP1


TIER_G = []
for i, (y0, y1, a0, a1) in enumerate(TIERS):
    al = math.atan((a1 - a0) / (y1 - y0))
    Hs = (y1 - y0) / math.cos(al)
    wb, wt = 2 * a0 * T16 + 0.07, 2 * a1 * T16 + 0.07
    w = max(wb, wt)
    TIER_G.append((al, Hs, w))
    for v in range(2):
        W, H = int(round(w * 26)), int(round(Hs * 26))
        m = ss_mask(W, H, w, Hs, lambda a, b, wb=wb, wt=wt, Hs=Hs: np.abs(a) <= lerp(wb / 2, wt / 2, b / Hs + 0.5))
        col = felt_plain(W, H, 100 + 10 * i + v, (0.80, 0.98) if i == 0 else (0.92, 1.04))
        if i == 1:
            col[:3] = A(FELT["hi"]) * 0.92                              # arête du dessus, nette
        TILES[f"mur{i}{v}"] = finish(col, m)

LID = 2 * (AP1 + 0.12)


def in_poly(x, z, ap):
    d = np.full(np.shape(x), -1e9)
    for k in range(N16):
        ph = 2 * math.pi * k / N16
        d = np.maximum(d, x * math.cos(ph) + z * math.sin(ph))
    return d <= ap


def lid_tile():
    W = H = int(round(LID * 20))
    a, b = grid(W, H, LID, LID, 3)
    m = in_poly(a, -b, AP1 + 0.06).reshape(H, 3, W, 3).mean(axis=(1, 3)) > 0.5
    a, b = grid(W, H, LID, LID)
    col = felt_plain(W, H, 140, (1.0, 1.0)) * 1.04
    rr = np.hypot(a, b)
    col *= (1 + 0.02 * np.sin(rr * 5.5))[..., None]
    d = inset(m, 4)
    col[(d < 3) & m] = A(FELT["hi"]) * 0.95
    return finish(col, m)


TILES["couvercle"] = lid_tile()

# ---- bord ovale, ailes relevées, ourlet de cuir ; posé sur la tête : face du dessous à y >= 32,62 au-dessus de la tête
BA, BB = 7.1, 6.4
B_TH = 0.45
B_Y = 32.85 + B_TH / 2                       # dessous à 32,85 (marge pour les inclinaisons du chapeau)
FLAP_X, CURL = 4.9, math.radians(20)
FLAP_L = (BA - FLAP_X) / math.cos(CURL) + 0.08


def in_brim(x, z, m=0.04):
    return (x / (BA - m)) ** 2 + (z / (BB - m)) ** 2 <= 1


def brim_col(x, z, seed):
    H, W = x.shape
    col = felt_plain(W, H, seed, (1.0, 1.0)) * 1.08
    r = np.hypot(x, z)
    col *= (0.58 + 0.42 * np.clip((r - AP0) / 1.0, 0, 1))[..., None]      # ombre au pied de la calotte
    e = (x / BA) ** 2 + (z / BB) ** 2
    col = lerp(col, A(FELT["hi"]), (0.35 * np.clip((e - 0.82) / 0.18, 0, 1))[..., None])   # bord usé, plus clair
    return col


def brim_tile(name, c, X, Y, w, h, seed, dens=18):
    W, H = int(round(w * dens)), int(round(h * dens))
    a, b = grid(W, H, w, h, 3)
    xw = c[0] + a * X[0] + b * Y[0]
    zw = c[2] + a * X[2] + b * Y[2]
    m = in_brim(xw, zw).reshape(H, 3, W, 3).mean(axis=(1, 3)) > 0.5
    a, b = grid(W, H, w, h)
    TILES[name] = finish(brim_col(c[0] + a * X[0] + b * Y[0], c[2] + a * X[2] + b * Y[2], seed), m)


C20, S20 = math.cos(CURL), math.sin(CURL)
BRIM = [("bord_c", (0, B_Y, 0), (1, 0, 0), (0, 0, -1), 2 * FLAP_X, 2 * BB),
        ("bord_r", (FLAP_X + C20 * FLAP_L / 2, B_Y + S20 * FLAP_L / 2, 0), (C20, S20, 0), (0, 0, -1), FLAP_L, 2 * BB),
        ("bord_l", (-FLAP_X - C20 * FLAP_L / 2, B_Y + S20 * FLAP_L / 2, 0), (-C20, S20, 0), (0, 0, 1), FLAP_L, 2 * BB)]
for i, (n, c, X, Y, w, h) in enumerate(BRIM):
    brim_tile(n, c, X, Y, w, h, 121 + i)

# ---- jupe sous le bord (cache le jour entre la tête et le bord) : carrée, face intérieure à 4,68 px
JUPE_D, JUPE_Y0 = 4.75, 31.75
TILES["jupe"] = finish(felt_plain(160, 16, 150, (0.62, 0.8)), np.ones((16, 160), bool))

# ---- ruban de cuir cousu
BD_Y0, BD_Y1 = 33.4, 35.04


def band_tile(seed):
    W, H = 28, 40
    r = np.random.default_rng(seed)
    col = A(LEATHER["base"]) * np.ones((H, W, 3), np.float32)
    col *= (0.90 + 0.14 * cell_noise(H, W, 9, seed) + 0.04 * r.random((H, W)))[..., None]
    col[:3] = A(LEATHER["low"])
    col[-3:] = A(LEATHER["low"])
    col[3:6] = A(LEATHER["hi"]) * 0.92
    for row in (8, H - 11):                                             # coutures en fil de laiton, 3 texels
        for x0 in range(1, W, 7):
            col[row:row + 3, x0:x0 + 4] = A(BRASS["hi"]) * 0.82
    return finish(col, np.ones((H, W), bool))


TILES["ruban"] = band_tile(131)
# ---- métal : barres, capuchons, engrenages, plaques
def bar_tile(metal, seed, grooves=3, slot=False):
    W, H = 96, 16
    a = np.zeros((H, W, 3), np.float32)
    r = np.random.default_rng(seed)
    for yy in range(H):
        q = abs((yy + 0.5) / H - 0.5) * 2
        a[yy, :] = lerp(lerp(A(metal["hi"]) * 0.85, A(metal["low"]), q ** 1.1), A(metal["base"]), 0.42)
    a *= (0.95 + 0.10 * r.random((1, W, 1), np.float32))      # brossé ±5 %
    for x in range(W // (grooves + 1), W, W // (grooves + 1)):
        a[:, x:x + 2] = A(metal["base"]) * 0.6
    if slot:                                                            # lumière du sifflet : fente sombre
        a[4:12, 38:58] = (30, 20, 16)
    return finish(a, np.ones((H, W), bool))


def cap_tile(metal, hole=False):
    n = 16
    c = A(metal["base"]) * np.ones((n, n, 3), np.float32)
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2)
    c[r > 6.2] = A(metal["low"])
    c[r < 3] = (24, 16, 14) if hole else A(metal["hi"])
    return finish(c, np.ones((n, n), bool))


TILES.update(bar_brass=bar_tile(BRASS, 41), bar_steel=bar_tile(STEEL, 42), bar_copper=bar_tile(COPPER, 43, 4),
             bar_leather=bar_tile(LEATHER, 44, 2), bar_felt=bar_tile(FELT, 45, 0), sifflet=bar_tile(BRASS, 46, 2, slot=True))
TILES.update(cap_brass=cap_tile(BRASS), cap_steel=cap_tile(STEEL), cap_copper=cap_tile(COPPER),
             cap_leather=cap_tile(LEATHER), cap_felt=cap_tile(FELT), bouche=cap_tile(STEEL, hole=True))


TILES["ruban_c"] = band_tile(132)
def paint_gear(n, teeth, metal, tooth_phase, seed, spokes=None, hole=0.24, h_t=0.16):
    """Engrenage (repris de ailes_steampunk) : dents trapézoïdales, une dent à tooth_phase (degrés, sens trigo)."""
    ss = 4
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    dx, dy = (xx + 0.5 - N / 2) / (N / 2), -(yy + 0.5 - N / 2) / (N / 2)
    r, th = np.hypot(dx, dy), np.degrees(np.arctan2(dy, dx))
    pitch = 360 / teeth
    q = np.abs(((th - tooth_phase + pitch / 2) % pitch) - pitch / 2) / pitch
    ro, rr = 0.98, 0.98 * (1 - h_t)
    edge = rr + (ro - rr) * np.clip((0.40 - q) / 0.17, 0, 1)
    m = (r <= edge) & (r >= hole)
    if spokes:
        ang = (th + 180 / spokes) % (360 / spokes) / (360 / spokes)
        m &= ~((r > 0.42) & (r < rr - 0.17) & (np.abs(ang - 0.5) < 0.26))
    mask = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((n, n), Image.LANCZOS)) > 110
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) / (n / 2)
    col = A(metal["base"]) * np.ones((n, n, 3), np.float32)
    nz = cell_noise(n, n, 10, seed)
    col *= (0.95 + 0.10 * nz)[..., None]                 # métal propre : ±5 % au plus (retour du 2026-11-04)
    col[r > rr - 0.04] = A(metal["hi"])
    col[(r > rr - 0.14) & (r <= rr - 0.05)] *= 0.55
    col[r < hole + 0.12] = A(metal["hi"]) * 0.9
    return finish(col, mask)



# ---- roue de la charnière (10 dents) et pignon du moteur (6 dents), rapport 10/6. Plaques vues depuis +X : u suit -Z, v suit +Y.
R_GH, R_GP = 0.88, 0.528
HT_H, HT_P = 0.2, 0.28
GDIST = R_GH * 0.98 * (1 - HT_H / 2) + R_GP * 0.98 * (1 - HT_P / 2)
G_ANG = 150.0                                # direction du pignon depuis la roue, dans l'image (sens trigo depuis +u)
TILES["roue10"] = paint_gear(64, 10, BRASS, G_ANG + 18, 151, spokes=5, h_t=HT_H, hole=0.2)
TILES["roue6"] = paint_gear(40, 6, BRASS, G_ANG + 180, 152, hole=0.28, h_t=HT_P)
def disc_tile(n, r_out, r_in, metal, rivets=0, seed=0, rr=2.0):
    """Anneau ou disque de laiton riveté (r en fraction du demi-côté)."""
    yy, xx = np.mgrid[0:n * 3, 0:n * 3]
    r = np.hypot(xx + 0.5 - n * 1.5, yy + 0.5 - n * 1.5) / (n * 1.5)
    m = ((r <= r_out) & (r >= r_in)).reshape(n, 3, n, 3).mean(axis=(1, 3)) > 0.5
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) / (n / 2)
    col = A(metal["base"]) * np.ones((n, n, 3), np.float32)
    col *= (0.95 + 0.10 * cell_noise(n, n, 10, seed))[..., None]
    col[np.abs(r - r_out) < 2.2 / n] = A(metal["hi"])
    col[np.abs(r - r_in) < 2.2 / n] = A(metal["low"])
    for k in range(rivets):
        an = TAU * (k + 0.5) / rivets
        rm = (r_out + max(r_in, 0.5)) / 2
        rivet(col, n / 2 + rm * n / 2 * math.cos(an), n / 2 - rm * n / 2 * math.sin(an), rr, STEEL)
    return finish(col, m)


TILES["cercle"] = disc_tile(80, 0.98, 0.70, BRASS, rivets=8, seed=161, rr=2.2)    # monture d'une lentille
TILES["lunette"] = disc_tile(64, 0.98, 0.80, BRASS, rivets=6, seed=162, rr=1.6)   # lunette du manomètre
TILES["embase"] = disc_tile(48, 0.98, 0.0, BRASS, rivets=6, seed=163, rr=1.6)     # bride de la cheminée
def verre_tile(n=56):
    yy, xx = np.mgrid[0:n, 0:n]
    dx, dy = (xx + 0.5 - n / 2) / (n / 2), (yy + 0.5 - n / 2) / (n / 2)
    r = np.hypot(dx, dy)
    m = ss_mask(n, n, 2.0, 2.0, lambda a, b: np.hypot(a, b) <= 0.98)
    col = lerp(A((226, 156, 54)), A((140, 80, 26)), np.clip(r, 0, 1)[..., None] ** 1.5)
    hl = np.exp(-(((dx + 0.35) / 0.22) ** 2 + ((dy + 0.38) / 0.12) ** 2))      # reflet en croissant, en haut à gauche
    col = lerp(col, A((255, 228, 160)), (np.clip(hl * 1.4, 0, 1))[..., None])
    col[r > 0.9] = A((96, 54, 20))
    e = np.zeros((n, n, 4), np.uint8)
    ec = lerp(A((120, 70, 18)), A((60, 30, 8)), np.clip(r, 0, 1)[..., None])
    e[..., :3] = np.clip(ec, 0, 255).astype(np.uint8)
    e[..., 3] = m * 255
    e[~m] = 0
    return finish(col, m), e


TILES["verre"], TILES_E["verre"] = verre_tile()


def cadran_tile(n=56):
    """Cadran crème, graduations de -110° à +110° (sens horaire depuis le haut), zone rouge en haut de l'échelle."""
    m = ss_mask(n, n, 2.0, 2.0, lambda a, b: np.hypot(a, b) <= 0.98)
    yy, xx = np.mgrid[0:n, 0:n]
    dx, dy = (xx + 0.5 - n / 2) / (n / 2), -(yy + 0.5 - n / 2) / (n / 2)
    r = np.hypot(dx, dy)
    beta = np.degrees(np.arctan2(dx, dy))                             # angle horaire depuis le haut
    col = lerp(A((236, 222, 182)), A((182, 160, 116)), np.clip(r, 0, 1)[..., None] ** 2)
    red = (beta > 62) & (beta < 112) & (r > 0.62) & (r < 0.84)
    col[red] = (178, 44, 30)
    for k in range(9):
        b0 = -110 + 27.5 * k
        tick = (np.abs(beta - b0) < (3.2 if k % 2 == 0 else 2.2)) & (r > (0.58 if k % 2 == 0 else 0.68)) & (r < 0.86)
        col[tick] = (40, 30, 24)
    col[r < 0.16] = A(BRASS["base"])
    return finish(col, m)


TILES["cadran"] = cadran_tile()
# cadran éclairé (source nette et logique, retour « aucune lumière sur le set ») : fond crème doux, graduations sombres ;
# tools/ambiance.py multiplie par 2,4 les sources déjà peintes (≈ 170 la nuit, plafond 225)
_cd = TILES["cadran"].astype(np.float32)
_lit = (_cd[..., 3] > 0) & (_cd[..., :3].mean(axis=2) > 150)
_ce = np.zeros(_cd.shape, np.uint8)
_ce[..., :3] = np.where(_lit[..., None], _cd[..., :3] * 0.30, 0).astype(np.uint8)
_ce[..., 3] = np.where(_cd[..., 3] > 0, 255, 0)
TILES_E["cadran"] = _ce
_ng = np.zeros((24, 8, 3), np.float32)
_ng[...] = (38, 34, 34)
_ng[:7] = (196, 46, 32)
TILES["aiguille"] = finish(_ng, np.ones((24, 8), bool))


# ---- vapeur : alpha en dégradé (groupes trans_), silhouette nette au seuil de 50 %
def vapeur_tile(W, H, w, h, blobs, seed):
    a, b = grid(W, H, w, h)
    b = b + h / 2                                                      # 0 en bas
    s = np.zeros(a.shape, np.float32)
    lit = np.zeros(a.shape, np.float32)
    for (bx, by, br) in blobs:
        d = np.hypot(a - bx, b - by) / br
        s = np.maximum(s, 1 - d)
        lit = np.maximum(lit, np.clip(1 - np.hypot(a - bx + 0.3 * br, b - by - 0.35 * br) / br, 0, 1))
    s += 0.06 * (cell_noise(H, W, 8, seed) - 0.5)
    al = np.where(s < 0.12, lerp(16, 118, np.clip(s / 0.12, 0, 1)), lerp(178, 255, np.clip((s - 0.12) / 0.4, 0, 1)) * (1 - 0.24 * b / h))
    al = np.where(s <= 0, 0, al)
    col = lerp(A((206, 212, 222)), A((250, 250, 248)), np.clip(lit * 1.3, 0, 1)[..., None])
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(al, 0, 255).astype(np.uint8)
    out[out[..., 3] == 0, :3] = (230, 234, 238)
    return out


PUFF_W, PUFF_H = 2.0, 3.2
JET_W, JET_H = 1.0, 2.1
TILES["vapeur"] = vapeur_tile(40, 64, PUFF_W, PUFF_H, [(0, 0.55, 0.55), (-0.32, 1.2, 0.5), (0.3, 1.65, 0.48), (-0.12, 2.25, 0.42), (0.14, 2.8, 0.32)], 71)
TILES["jet"] = vapeur_tile(24, 50, JET_W, JET_H, [(0, 0.3, 0.32), (-0.1, 0.7, 0.36), (0.1, 1.15, 0.38), (-0.06, 1.6, 0.34), (0.04, 1.9, 0.2)], 72)
SEMI.update({"vapeur", "jet"})


# ---- porte du foyer (arrière) : cadre de laiton riveté, fond d'acier, trois fentes rougeoyantes
DOOR_W, DOOR_H = 2.5, 1.4


def porte_tile():
    W, H = int(DOOR_W * 32), int(DOOR_H * 32)
    a, b = grid(W, H, DOOR_W, DOOR_H)
    m = ss_mask(W, H, DOOR_W, DOOR_H, lambda a, b: (np.abs(a) <= DOOR_W / 2 - 0.02) & (np.abs(b) <= DOOR_H / 2 - 0.02)
                & ~((np.abs(a) > DOOR_W / 2 - 0.22) & (np.abs(b) > DOOR_H / 2 - 0.22) & (np.hypot(np.abs(a) - DOOR_W / 2 + 0.22, np.abs(b) - DOOR_H / 2 + 0.22) > 0.2)))
    col = A(STEEL["base"]) * np.ones((H, W, 3), np.float32) * (0.95 + 0.08 * cell_noise(H, W, 8, 171))[..., None]
    fr = (np.abs(a) > DOOR_W / 2 - 0.3) | (np.abs(b) > DOOR_H / 2 - 0.3)
    col[fr] = A(BRASS["base"])
    col[fr & ((np.abs(a) > DOOR_W / 2 - 0.1) | (np.abs(b) > DOOR_H / 2 - 0.1))] = A(BRASS["hi"])
    col[~fr & ((np.abs(a) > DOOR_W / 2 - 0.36) | (np.abs(b) > DOOR_H / 2 - 0.36))] = A(BRASS["low"]) * 0.7
    e = np.zeros((H, W, 4), np.uint8)
    for k in (-1, 0, 1):
        sl = (np.abs(b - 0.26 * k) < 0.055) & (np.abs(a + 0.12) < 0.62)
        glow = np.clip(1 - np.abs(a + 0.12) / 0.62, 0, 1)
        col[sl] = lerp(A((150, 50, 14)), A((255, 176, 70)), glow[sl][:, None])
        e[sl, 0], e[sl, 1], e[sl, 2] = (lerp(150, 200, glow[sl])).astype(np.uint8), (lerp(46, 92, glow[sl])).astype(np.uint8), 14
        e[sl, 3] = 255
    for (pa, pb) in ((-1.05, 0.5), (1.05, 0.5), (-1.05, -0.5), (1.05, -0.5)):
        rivet(col, (pa / DOOR_W + 0.5) * W, (0.5 - pb / DOOR_H) * H, 2.2, STEEL)
    out = finish(col, m)
    e[~m] = 0
    return out, e


TILES["porte"], TILES_E["porte"] = porte_tile()

# ------------------------------------------------------------------ atlas
def pack():
    items = sorted(((n, t.shape[1], t.shape[0]) for n, t in TILES.items()), key=lambda it: -it[2])
    uv, x, y, shelf = {}, 0, 0, 0
    for n, w, h in items:
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, f"atlas plein : {n}"
        uv[n] = (x, y, x + w, y + h)
        x += w + 1
        shelf = max(shelf, h)
    return uv


UV = pack()
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
for n, im in TILES.items():
    u0, v0, u1, v1 = UV[n]
    if n not in SEMI:
        assert set(np.unique(im[..., 3])) <= {0, 255}, f"semi-transparence hors trans_ : {n}"
    tex[v0:v1, u0:u1] = im
for n, im in TILES_E.items():
    u0, v0, u1, v1 = UV[n]
    tex_e[v0:v1, u0:u1] = im
# fente du sifflet : braise très douce
u0, v0, u1, v1 = UV["sifflet"]
tex_e[v0 + 5:v0 + 11, u0 + 40:u0 + 56] = (96, 40, 10, 255)
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC
tex[tex[..., 3] == 0] = 0
assert set(np.unique(tex_e[..., 3])) <= {0, 255}


def b64(arr, fn):
    im = Image.fromarray(arr, "RGBA")
    im.save(fn, optimize=True)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


# masque de reflets : valeur constante par image (le mod moyenne par face), alpha recopié
REFLET = {"bar_brass": 200, "cap_brass": 190, "sifflet": 190, "roue12": 210, "roue6": 210, "platine": 170, "cercle": 215, "lunette": 210,
          "embase": 190, "verre": 235, "bar_copper": 165, "cap_copper": 160, "bar_steel": 140, "cap_steel": 130, "bouche": 90,
          "aiguille": 110, "cadran": 70, "bar_leather": 30, "cap_leather": 30, "ruban": 30, "ruban_c": 30}
tex_r = np.zeros((TEX, TEX, 4), np.uint8)
for n in TILES:
    u0, v0, u1, v1 = UV[n]
    k = 0 if n in SEMI else REFLET.get(n, 14)                       # feutre : 14, presque mat
    tex_r[v0:v1, u0:u1, :3] = k
    tex_r[v0:v1, u0:u1, 3] = np.where(tex[v0:v1, u0:u1, 3] > 0, 255, 0)
tex_r[tex_r[..., 3] == 0] = 0
tex_b64, tex_e_b64, tex_r_b64 = b64(tex, f"{NOM}.png"), b64(tex_e, f"{NOM}_e.png"), b64(tex_r, f"{NOM}_r.png")
# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx, ordre du mod et du renderer. Blocage de cardan à Y = ±90° traité
    (rz = 0, rx porte la rotation restante) ; vérifié par reconstruction."""
    s = -R[2, 0]
    if abs(s) < 0.99999:
        ex, ey, ez = math.atan2(R[2, 1], R[2, 2]), math.asin(s), math.atan2(R[1, 0], R[0, 0])
    elif s > 0:
        ex, ey, ez = math.atan2(R[0, 1], R[1, 1]), math.pi / 2, 0.0
    else:
        ex, ey, ez = math.atan2(-R[0, 1], R[1, 1]), -math.pi / 2, 0.0
    cx, sx, cy, sy, cz, sz = math.cos(ex), math.sin(ex), math.cos(ey), math.sin(ey), math.cos(ez), math.sin(ez)
    Rr = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    assert np.abs(Rr - R).max() < 1e-3, "euler : reconstruction"
    return math.degrees(ex), math.degrees(ey), math.degrees(ez)


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups, name
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(float(v), 2) for v in rotation]}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def box(g, name, c, X, Y, size, faces):
    """Cube centré en c, axes locaux X, Y (Z = X x Y), tailles (sx, sy, sz)."""
    X, Y = unit(X), unit(Y)
    Y = unit(Y - (Y @ X) * X)
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c, s = np.asarray(c, float), np.asarray(size, float) / 2
    cube(g, name, c - s, c + s, c, euler(R_), faces)


def plate(g, name, c, X, Y, w, h, tile, th=0.3, sides=None):
    """Plaque : face south (+Z local = X x Y) à l'endroit, north en miroir, tranches transparentes sauf sides."""
    u0, v0, u1, v1 = UV[tile]
    f = {"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
    f.update(sides or {})
    box(g, name, c, X, Y, (w, h, th), f)


def bar(g, name, p, q, r, mat, octo=True, ov=0.0, ends=None, up=None, roll=0.0, ends_o=None):
    """Tronçon de p à q, section carrée de demi-côté r (+ un second cube à 45° si octo, plus court de 0,1 px à chaque bout
    pour que les bouts des deux cubes ne soient pas dans le même plan) ; roll : rotation de la section autour de l'axe."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = np.asarray(up, float) if up is not None else (V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0))
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    if roll:
        cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        Y, Z_ = cr * Y + sr * Z_, -sr * Y + cr * Z_
    L = np.linalg.norm(q - p) + 2 * ov
    c = (p + q) / 2
    bu0, bv0, bu1, bv1 = UV[f"bar_{mat}"] if f"bar_{mat}" in UV else UV[mat]
    ub = bu0 + max(4, min(bu1 - bu0, (bu1 - bu0) * L / 6))
    lg = [bu0, bv0, ub, bv1] if f"bar_{mat}" in UV else [bu0 + 30, bv0, bu0 + 66, bv1]   # sifflet : la fente (lumière) au milieu
    cu = UV[f"cap_{mat}"] if f"cap_{mat}" in UV else UV["cap_brass"]
    en = [cu[0], cu[1], cu[2], cu[3]]
    faces = {"south": lg, "north": lg, "up": lg, "down": lg, "east": en, "west": en}
    faces_o = dict(faces, **(ends_o if ends_o is not None else (ends or {})))
    faces.update(ends or {})
    box(g, name, c, X, Y, (L, 2 * r, 2 * r), faces)
    faces = faces_o
    if octo:
        k = math.sqrt(0.5)
        if L > 0.5:
            box(g, name + "o", c, X, k * Y + k * Z_, (L - 0.22, 2 * r * 0.97, 2 * r * 0.97), faces)
        else:                                                           # tronçon court : bouts du second cube transparents
            box(g, name + "o", c, X, k * Y + k * Z_, (L - 0.06, 2 * r * 0.97, 2 * r * 0.97), dict(faces, east=CLEAR, west=CLEAR))


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


UP = V(0, 1, 0)
HAT = group("chapeau", [0, B_Y, 0])

# ---- calotte
for i, (y0, y1, a0, a1) in enumerate(TIERS):
    al, Hs, w = TIER_G[i]
    for k in range(N16):
        ph = 2 * math.pi * k / N16
        n_ = V(math.cos(ph), 0, math.sin(ph))
        X = np.cross(UP, n_)
        Y = UP * math.cos(al) + n_ * math.sin(al)
        c = n_ * ((a0 + a1) / 2 - 0.15) + V(0, (y0 + y1) / 2, 0)
        plate(HAT, f"mur{i}_{k}", c, X, Y, w, Hs, f"mur{i}{k % 2}", th=0.3)
plate(HAT, "couvercle", V(0, YC1 - 0.13, 0), V(1, 0, 0), V(0, 0, -1), LID, LID, "couvercle", th=0.3)

# ---- bord + ourlet de cuir
for n, c, X, Y, w, h in BRIM:
    plate(HAT, n, V(*c), V(*X), V(*Y), w, h, n, th=B_TH)


def brim_y(x):
    return B_Y + max(0.0, abs(x) - FLAP_X) * math.tan(CURL)


NR = 36
ROLL = []
for i in range(NR):
    t = 2 * math.pi * i / NR
    x, z = (BA - 0.08) * math.cos(t), (BB - 0.08) * math.sin(t)
    ROLL.append(V(x, brim_y(x), z))
for i in range(NR):
    bar(HAT, f"ourlet{i}", ROLL[i], ROLL[(i + 1) % NR], 0.24, "leather", octo=True, ov=0.1, roll=11.25 + 22.5 * (i % 2))

# ---- jupe (sous le bord)
JH = 32.87 - JUPE_Y0
for k, (n_, X) in enumerate(((V(1, 0, 0), V(0, 0, -1)), (V(-1, 0, 0), V(0, 0, 1)), (V(0, 0, 1), V(1, 0, 0)), (V(0, 0, -1), V(-1, 0, 0)))):
    L_ = 2 * (JUPE_D + 0.3) if k < 2 else 2 * JUPE_D
    plate(HAT, f"jupe{k}", n_ * (JUPE_D + 0.15) + V(0, JUPE_Y0 + JH / 2, 0), X, UP, L_, JH, "jupe", th=0.3)

# ---- ruban (16 pans, face intérieure à 0,12 px du feutre)
al0 = TIER_G[0][0]
YM = (BD_Y0 + BD_Y1) / 2
AM = apo(YM)
for k in range(N16):
    ph = 2 * math.pi * k / N16
    n_ = V(math.cos(ph), 0, math.sin(ph))
    X = np.cross(UP, n_)
    Y = UP * math.cos(al0) + n_ * math.sin(al0)
    w = 2 * (AM + 0.42) * T16 + 0.06
    u0, v0, u1, v1 = UV["ruban"]
    plate(HAT, f"ruban{k}", n_ * (AM + 0.27) + V(0, YM, 0), X, Y, w, (BD_Y1 - BD_Y0) - 0.12 * (k % 2), "ruban", th=0.3,
          sides={"up": [u0, v0, u1, v0 + 3], "down": [u0, v1 - 3, u1, v1]})
O_B = AM + 0.42                              # face extérieure du ruban

# ---- boucle de laiton (côté gauche)
xb = -(O_B + 0.07)
bz0, bz1, by0, by1 = -0.95, 0.55, BD_Y0 + 0.3, BD_Y1 - 0.3
for i, (p, q) in enumerate(((V(-(O_B - 0.04), by0, bz0), V(-(O_B - 0.04), by0, bz1)), (V(-(O_B - 0.04), by1, bz0), V(-(O_B - 0.04), by1, bz1)),
                            (V(xb, by0, bz0), V(xb, by1, bz0)), (V(xb, by0, bz1), V(xb, by1, bz1)))):
    bar(HAT, f"boucle{i}", p, q, 0.16 if i < 2 else 0.17, "brass", octo=False, ov=0.05 if i < 2 else 0.0, roll=45 if i < 2 else 0)
bar(HAT, "ardillon", V(-(O_B + 0.24), YM, bz0 + 0.07), V(-(O_B + 0.24), YM, 0.0), 0.1, "steel", octo=False)
plate(HAT, "bout_ruban", V(-(O_B + 0.32), YM - 0.12, -1.5), V(0, 0, 1), V(0, 1, 0), 1.1, 1.5, "ruban_c", th=0.3)

# ---- porte du foyer (arrière, au-dessus du ruban)
alw = al0
yd = 35.9
nb = V(0, 0, 1)
plate(HAT, "porte", nb * (apo(yd) + 0.27) + V(0, yd, 0), np.cross(UP, nb), UP * math.cos(alw) + nb * math.sin(alw), DOOR_W, DOOR_H, "porte", th=0.3)
bar(HAT, "loquet", V(0.95, yd + 0.35, apo(yd) + 0.6), V(0.95, yd - 0.35, apo(yd) + 0.6), 0.1, "steel", octo=False)
bar(HAT, "poignee", V(0.95, yd, apo(yd) + 0.45), V(0.95, yd, apo(yd) + 0.75), 0.12, "brass", octo=False)

# ---- manomètre (côté droit), sur sa console ; couches à 0,1 px au moins l'une de l'autre (repris de la version précédente)
MZ, MY = 0.0, 35.9
xm = O_B
bar(HAT, "console", V(apo(MY) - 0.12, MY, MZ), V(xm + 0.4, MY, MZ), 0.32, "brass", octo=True)
MANO = group("manometre", [xm, MY, MZ], parent=HAT)
bar(MANO, "boitier", V(xm + 0.12, MY, MZ), V(xm + 0.72, MY, MZ), 1.12, "brass", octo=True, ends={"east": list(UV["cadran"])}, ends_o={})
plate(MANO, "lunette", V(xm + 1.35, MY, MZ), V(0, 0, -1), V(0, 1, 0), 2.75, 2.75, "lunette", th=0.3)
NEEDLE = group("aiguille", [xm + 0.96, MY, MZ], parent=MANO)
ua, va, ub_, vb = UV["aiguille"]
box(NEEDLE, "aiguille", V(xm + 0.96, MY + 0.36, MZ), V(0, 0, -1), V(0, 1, 0), (0.3, 1.08, 0.24),
    {f: [ua, va, ub_, vb] for f in ("east", "west", "up", "down", "north", "south")})

# ---- cheminée (arrière droit, sur le dessus)
CX, CZ, CY = 2.35, 2.35, YC1 + 0.12
CHEM = group("cheminee", [CX, CY, CZ], parent=HAT, rotation=(6, 0, -5))


def col_(g, name, y0, y1, r, mat, octo=True, ends=None):
    bar(g, name, V(CX, y0, CZ), V(CX, y1, CZ), r, mat, octo=octo, ends=ends, up=V(0, 0, 1))


plate(CHEM, "embase", V(CX, CY + 0.12, CZ), V(1, 0, 0), V(0, 0, -1), 2.0, 2.0, "embase", th=0.36)
col_(CHEM, "embase_n", CY - 0.3, CY + 0.52, 0.66, "brass")
col_(CHEM, "fut", CY + 0.08, CY + 3.2, 0.6, "copper")
col_(CHEM, "bague_1", CY + 1.1, CY + 1.4, 0.72, "brass")
col_(CHEM, "bague_2", CY + 2.45, CY + 2.72, 0.72, "brass")
col_(CHEM, "sifflet", CY + 2.85, CY + 4.05, 0.46, "sifflet")
SOUP = group("soupape", [CX, CY + 4.05, CZ], parent=CHEM)
bu = UV["bouche"]
col_(SOUP, "chapeau_soupape", CY + 3.82, CY + 4.32, 0.56, "steel", ends={"east": list(bu)})
col_(SOUP, "bouton", CY + 4.2, CY + 4.6, 0.18, "brass", octo=False)
MOUTH = V(CX, CY + 4.7, CZ)
EMIT = group("emit_mc_white_smoke", MOUTH, parent=CHEM)
CTRL_E = group("ctrl_emit", MOUTH, parent=EMIT)
VAP = group("trans_vapeur", [CX, CY + 4.35, CZ], parent=CHEM)
CTRL_A = group("ctrl_alpha", [CX, CY + 4.35, CZ], parent=VAP)
JET = group("trans_jet", [CX, CY + 0.8, CZ], parent=CHEM)
for i, yaw in enumerate((0, 60, 120)):
    X = V(math.cos(math.radians(yaw)), 0, -math.sin(math.radians(yaw)))
    plate(VAP, f"bouffee{i}", V(CX, CY + 4.35 + PUFF_H / 2, CZ) + 0.01 * i * X, X, UP, PUFF_W, PUFF_H, "vapeur", th=0.3)
    plate(JET, f"jet{i}", V(CX, CY + 0.8 + JET_H / 2, CZ) + 0.01 * i * X, X, UP, JET_W, JET_H, "jet", th=0.3)

# ---- charnière des lunettes (bord avant), roue dentée, moteur à vapeur et son pignon
HY, HZ = B_Y + 0.4, -(BB - 0.25)             # axe de la charnière, posé sur le bord avant
H_ = V(0, HY, HZ)
AX_X = 3.25                                  # bras des lunettes à x = ±3,25
bar(HAT, "patte", V(0, HY, HZ), V(0, HY, HZ + 1.25), 0.28, "brass", octo=False, roll=45)
bar(HAT, "noeud_c", V(-0.5, HY, HZ), V(0.5, HY, HZ), 0.3, "brass", octo=True)
bar(HAT, "axe_charniere", V(-AX_X - 0.55, HY, HZ), V(4.15, HY, HZ), 0.14, "steel", octo=True)
GX = 3.83                                    # plan de la roue dentée
PY, PZ = HY + GDIST * math.sin(math.radians(G_ANG)), HZ - GDIST * math.cos(math.radians(G_ANG))
MOT_X0, MOT_X1, MOT_R = 2.4, 3.42, 0.5
bar(HAT, "moteur", V(MOT_X0, PY, PZ), V(MOT_X1, PY, PZ), MOT_R, "brass", octo=True)
bar(HAT, "moteur_cyl", V(MOT_X0 + 0.25, PY, PZ), V(MOT_X1 - 0.25, PY, PZ), MOT_R + 0.12, "copper", octo=True)
bar(HAT, "axe_pignon", V(MOT_X1 - 0.05, PY, PZ), V(GX + 0.5, PY, PZ), 0.12, "steel", octo=False)
PIGNON = group("pignon", [GX + 0.12, PY, PZ], parent=HAT)
plate(PIGNON, "pignon_dents", V(GX + 0.12, PY, PZ), V(0, 0, -1), UP, 2 * R_GP, 2 * R_GP, "roue6", th=0.32)

ARM = group("bras_lunettes", H_, parent=HAT)
plate(ARM, "roue_charniere", V(GX, HY, HZ), V(0, 0, -1), UP, 2 * R_GH, 2 * R_GH, "roue10", th=0.32)

# ---- lunettes : position au repos (verres contre la calotte, haut) et baissée (devant les yeux)
LX, CUP_R, CUP_D = 1.72, 1.25, 0.9
Y_DOWN, Z_DOWN = 27.7, -5.62                 # centre des verres baissés : devant les yeux, coque à 5,17 px du visage
Z_REST = -5.47                               # au repos, dos des coques à 0,1 px au moins de la calotte
r_arm = math.hypot(Y_DOWN - HY, Z_DOWN - HZ)
Y_REST = HY + math.sqrt(r_arm ** 2 - (Z_REST - HZ) ** 2)
B0 = V(0, Y_REST, Z_REST)
phi_r = math.degrees(math.atan2(Z_REST - HZ, Y_REST - HY))
phi_d = math.degrees(math.atan2(Z_DOWN - HZ, Y_DOWN - HY))
TH_D = phi_d - phi_r - 360.0                 # passe par l'avant (environ -192°)
assert -200 < TH_D < -185, TH_D
assert Y_REST + CUP_R < YC1 - 0.3 and Z_REST + CUP_D / 2 <= -(apo(Y_REST + CUP_R) + 0.1), (Y_REST, Z_REST)

for s_, tag in ((-1, "l"), (1, "r")):
    bar(ARM, f"noeud_{tag}", V(s_ * (AX_X - 0.3), HY, HZ), V(s_ * (AX_X + 0.3), HY, HZ), 0.3, "brass", octo=True)
    bar(ARM, f"bras_{tag}", V(s_ * AX_X, HY, HZ), V(s_ * AX_X, B0[1], B0[2]), 0.17, "brass", octo=False, ov=0.05, up=V(1, 0, 0))
LUN = group("lunettes", B0, parent=ARM)
bar(LUN, "pont", B0 + V(-0.62, 0.25, 0), B0 + V(0.62, 0.25, 0), 0.2, "brass", octo=False)
LENS = []
for s_, tag in ((-1, "l"), (1, "r")):
    c = B0 + V(s_ * LX, 0, 0)
    bar(LUN, f"coque_{tag}", c + V(0, 0, -CUP_D / 2), c + V(0, 0, CUP_D / 2), CUP_R, "copper", octo=True,
        ends={"west": CLEAR, "east": list(UV["cap_leather"])})
    plate(LUN, f"verre_{tag}", c + V(0, 0, -0.15), V(-1, 0, 0), UP, 2.3, 2.3, "verre", th=0.3)
    plate(LUN, f"cercle_{tag}", c + V(0, 0, -0.6), V(-1, 0, 0), UP, 3.05, 3.05, "cercle", th=0.3)
    bar(LUN, f"tourillon_{tag}", c + V(s_ * 1.1, 0, 0), c + V(s_ * (AX_X - LX + 0.35), 0, 0), 0.2, "steel", octo=False)

# ---- deux loupes d'horloger sur l'oculaire droit : pivot en haut à droite, elles tournent dans le plan du verre
CR = B0 + V(LX, 0, 0)
PIV = CR + V(0.9, 0.9, 0)
ZF = -0.75                                   # face avant de la monture
bar(LUN, "axe_loupes", PIV + V(0, 0, ZF + 0.02), PIV + V(0, 0, ZF - 1.75), 0.15, "steel", octo=False)
LOUPES = []
for j, (rl, dz, rho) in enumerate(((0.66, ZF - 0.12 - 0.27, 128.0), (0.48, ZF - 0.12 - 0.54 - 0.12 - 0.27, 152.0))):
    zc = CR[2] + dz
    cc = V(CR[0], CR[1], zc)
    g = group(f"loupe{j + 1}", V(PIV[0], PIV[1], zc), parent=LUN, rotation=(0, 0, rho))
    LOUPES.append((g, rho))
    bar(g, f"tube{j + 1}", cc + V(0, 0, -0.27), cc + V(0, 0, 0.27), rl, "brass", octo=True, ends={"west": CLEAR, "east": CLEAR})
    plate(g, f"verre_loupe{j + 1}", cc, V(-1, 0, 0), UP, 2 * rl * 0.93, 2 * rl * 0.93, "verre", th=0.3)
    d = unit(cc - V(PIV[0], PIV[1], zc))
    bar(g, f"bras_loupe{j + 1}", V(PIV[0], PIV[1], zc), cc - d * (rl * 0.9), 0.12, "brass", octo=False)
    bar(g, f"bague_loupe{j + 1}", V(PIV[0], PIV[1], zc - 0.13), V(PIV[0], PIV[1], zc + 0.13), 0.24, "brass", octo=True)

# ---- tuyaux de cuivre : manomètre -> moteur (sur le bord, autour du ruban), manomètre -> cheminée (le long de la calotte)
PIPE_A = [V(xm + 0.42, MY - 1.0, 0.0), V(xm + 0.42, B_Y + 0.62, 0.0)]
for ang in (-18, -36):
    a_ = math.radians(ang)
    PIPE_A.append(V(5.5 * math.cos(a_), B_Y + 0.62, 5.5 * math.sin(a_)))
PIPE_A.append(V(3.05, PY - 0.05, PZ + MOT_R - 0.15))
PIPE_B = [V(xm + 0.42, MY + 0.9, 0.0), V(xm + 0.45, MY + 1.7, 0.6), V(5.3, 39.95, 1.5), V(4.75, YC1 + 0.45, 2.0), V(CX + 0.75, YC1 + 0.45, CZ)]
for nm, P_ in (("tuyau_a", PIPE_A), ("tuyau_b", PIPE_B)):
    for i in range(len(P_) - 1):
        bar(HAT, f"{nm}{i}", P_[i], P_[i + 1], 0.2, "copper", octo=False, ov=0.1, roll=45 if i % 2 == 0 else 0)
for nm, (p, q) in (("collier_a", (PIPE_A[2], PIPE_A[3])), ("collier_b", (PIPE_B[2], PIPE_B[3]))):
    m_ = lerp(p, q, 0.5)
    u_ = unit(q - p)
    bar(HAT, nm, m_ - 0.25 * u_, m_ + 0.25 * u_, 0.3, "brass", octo=False, roll=22.5)

outliner = [{"name": "head", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone_node(HAT)]}]
N_GROUPS = len(groups) + 1
# ------------------------------------------------------------------ animations
def kf(ch, t, x, y, z):
    f = lambda v: v if isinstance(v, str) else str(round(v + 0.0, 3 if ch != "rotation" else 2))
    return {"channel": ch, "data_points": [{"x": f(x), "y": f(y), "z": f(z)}], "time": round(t, 4), "interpolation": "linear"}


def anim(name, L, tracks, loop="loop", fps=30):
    """tracks : groupe -> {canal: t -> (x, y, z)}. Échantillonnage fin, l'optimiseur simplifie les arrêts."""
    n = max(8, int(math.ceil(L * fps)))
    times = [i * L / n for i in range(n + 1)]
    A_ = {}
    for g, chans in tracks.items():
        A_[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(ch, t, *f(t)) for ch, f in chans.items() for t in times]}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": L, "snapping": 24, "selected": name == "idle", "animators": A_}


def step_resp(u, rise, ov=0.12):
    """Cran de servo : 0 -> 1 avec dépassement ov puis rappel, en 2,6 x rise."""
    if u <= 0:
        return 0.0
    a, b, c = rise, rise * 1.8, rise * 2.6
    if u < a:
        return (1 + ov) * sm(u, 0, a)
    if u < b:
        return 1 + ov - 1.35 * ov * sm(u, a, b)
    if u < c:
        return 1 - 0.35 * ov + 0.35 * ov * sm(u, b, c)
    return 1.0


def stop_resp(u, rise, amt=0.05, d1=0.16, d2=0.1):
    """Arrivée en butée : accélère, touche, rebondit un peu, se pose."""
    if u <= 0:
        return 0.0
    if u < rise:
        return (u / rise) ** 2
    if u < rise + d1:
        return 1 - amt * math.sin(math.pi * (u - rise) / d1)
    if u < rise + d1 + d2:
        return 1 - 0.3 * amt * math.sin(math.pi * (u - rise - d1) / d2)
    return 1.0


def ticks(t, L, n, rise, phase=0.0):
    """n crans régulièrement espacés par boucle ; valeur en crans, ticks(t + L) = ticks(t) + n."""
    P = L / n
    tt = t - phase * P
    k = math.floor(tt / P + 1e-9)
    return k + step_resp(tt - k * P, rise) + phase * 0


def ring(u, T=0.18, tau=0.1):
    """Vibration amortie après un choc (0 à u = 0)."""
    return math.exp(-u / tau) * math.sin(TAU * u / T) if u > 0 else 0.0


P_MIN, P_MAX = 0.14, 0.88


class Pression:
    """Cycle de pression de période P, décharge à td : l'aiguille monte par crans, la soupape tremble, puis décharge."""

    def __init__(self, P, td, ncr, W, puff_D, puff_amp, D2, rise=0.06):
        self.__dict__.update(locals())

    def tau(self, t):
        return (t - self.td) % self.P

    def p(self, t):
        u, P = self.tau(t), self.P
        drop = step_resp(u, 0.07, 0.15)
        c0, c1 = 0.12 * P + 0.25 * self.D2, P - self.W - 0.06
        climb = sum(step_resp(u - (c0 + i * (c1 - c0) / max(1, self.ncr - 1)), self.rise, 0.22) for i in range(self.ncr)) / self.ncr
        env = bump(u, P - self.W, P - self.W + 0.08, P - 0.05, P - 0.01)
        return P_MAX - (P_MAX - P_MIN) * drop + (P_MAX - P_MIN) * climb + 0.035 * env * math.sin(TAU * 17 * u)

    def env(self, t):
        u, P = self.tau(t), self.P
        return bump(u, P - self.W, P - self.W + 0.08, P - 0.05, P - 0.01)

    def needle(self, t):
        return (110 - 220 * self.p(t), 0, 0)

    def valve_pos(self, t):
        u = self.tau(t)
        k = min(1.0, self.P / 3)
        lift = 0.42 * bump(u, 0, 0.04, 0.22 * k + 0.05, 0.32 * k + 0.08) + 0.07 * bump(u, 0.38 * k + 0.08, 0.41 * k + 0.09, 0.43 * k + 0.1, 0.48 * k + 0.12)
        return (0, lift + 0.05 * self.env(t) * abs(math.sin(TAU * 19 * u)), 0)

    def valve_rot(self, t):
        u, e = self.tau(t), self.env(t)
        return (4 * e * math.sin(TAU * 9 * u + 1), 0, 6 * e * math.sin(TAU * 13 * u))

    def puff(self, t):
        """(échelle, position y, alpha 0..1) de la bouffée."""
        u, D, a = self.tau(t), self.puff_D, self.puff_amp
        if u >= D:
            return (0, 0, 0), 0.0, 0.0
        s_in = 1 - (1 - min(1.0, u / 0.14)) ** 3
        g = sm(u, 0.1, D)
        sx = a * s_in * (1 + 0.45 * g) * (1 - sm(u, 0.62 * D, D))
        sy = a * s_in * (1 + 1.0 * g) * (1 - sm(u, 0.72 * D, D))
        return (sx, sy, sx), a * (0.15 * s_in + 2.6 * g ** 0.8), 1 - sm(u, 0.15, 0.95 * D)

    def emit(self, t):
        """ctrl_emit : coupé (-1), cinq fois la cadence du staff pendant les 0,35 s de la décharge."""
        return (-1 + 5 * bump(self.tau(t), 0.0, 0.02, 0.3, 0.36), 0, 0)

    def tracks(self, vap_rot=0.0):
        return {NEEDLE: {"rotation": self.needle}, CTRL_E: {"position": self.emit},
                SOUP: {"rotation": self.valve_rot, "position": self.valve_pos},
                VAP: {"scale": lambda t: self.puff(t)[0], "position": lambda t: (0, self.puff(t)[1], 0), "rotation": lambda t: (vap_rot, 0, 0)},
                CTRL_A: {"position": lambda t: (self.puff(t)[2] - 1, 0, 0)}}

    def recoil(self, t, amp=1.0):
        u = self.tau(t)
        return (-0.8 * amp * ring(u, 0.22, 0.12), 0, 0), (0, 0.08 * amp * bump(u, 0, 0.04, 0.06, 0.25), 0)


def merge(*ds):
    out = {}
    for d in ds:
        for g, ch in d.items():
            out.setdefault(g, {}).update(ch)
    return out


def add3(*fs):
    return lambda t: tuple(sum(f(t)[i] for f in fs) for i in range(3))



def kz(v):
    return (0, 0, v)


# idle 8 s : deux décharges (toutes les 4 s) ; à chaque décharge le chapeau tressaille et les lunettes cliquettent
PI = Pression(4.0, 3.3, 5, 0.5, 1.4, 1.0, 1.1)
idle = anim("idle", 8.0, merge(PI.tracks(), {
    HAT: {"rotation": lambda t: PI.recoil(t)[0], "position": lambda t: PI.recoil(t)[1]},
    LUN: {"rotation": lambda t: (3.0 * ring(PI.tau(t)), 0, 0)},
    LOUPES[0][0]: {"rotation": lambda t: kz(4 * ring(PI.tau(t) - 0.03, 0.2, 0.1))},
    LOUPES[1][0]: {"rotation": lambda t: kz(-5 * ring(PI.tau(t) - 0.06, 0.18, 0.1))}}), fps=30)

# walk 3,2 s : décharge toutes les 1,6 s ; un pas toutes les 0,8 s secoue les lunettes ; bouffée un peu vers l'arrière
PW = Pression(1.6, 1.2, 3, 0.25, 1.05, 0.85, 0.7, rise=0.05)
walk = anim("walk", 3.2, merge(PW.tracks(vap_rot=14), {
    HAT: {"rotation": lambda t: (0.6 * math.sin(TAU * t / 0.8) + PW.recoil(t)[0][0], 0, 0.4 * math.sin(TAU * t / 1.6)), "position": lambda t: PW.recoil(t)[1]},
    LUN: {"rotation": lambda t: (2.5 * ring((t - 0.1) % 0.8) + 2.5 * ring(PW.tau(t)), 0, 0)},
    LOUPES[0][0]: {"rotation": lambda t: kz(3 * ring((t - 0.12) % 0.8, 0.2, 0.1))},
    LOUPES[1][0]: {"rotation": lambda t: kz(-4 * ring((t - 0.15) % 0.8, 0.18, 0.1))}}), fps=40)

# run 2,0 s : décharge toutes les secondes, vapeur rabattue vers l'arrière, chapeau poussé en arrière par le vent
PR = Pression(1.0, 0.7, 3, 0.18, 0.75, 0.9, 0.5, rise=0.04)
run = anim("run", 2.0, merge(PR.tracks(vap_rot=42), {
    HAT: {"rotation": lambda t: (1.5 + 0.5 * math.sin(TAU * t / 0.5) + 0.8 * PR.recoil(t)[0][0], 0, 0), "position": lambda t: PR.recoil(t)[1]},
    LUN: {"rotation": lambda t: (3.0 * ring((t - 0.05) % 0.5, 0.14, 0.08) + 2.5 * ring(PR.tau(t)), 0, 0)},
    LOUPES[0][0]: {"rotation": lambda t: kz(4 * ring((t - 0.07) % 0.5, 0.16, 0.08))},
    LOUPES[1][0]: {"rotation": lambda t: kz(-5 * ring((t - 0.09) % 0.5, 0.15, 0.08))}}), fps=48)

# sneak 10 s : le moteur tourne, les lunettes passent par l'avant et se posent devant les yeux en butée (rebond), les deux
# loupes pivotent devant le verre droit l'une après l'autre (crans), mise au point, elles repartent, puis tout remonte.
SL = 10.0
PS = Pression(10.0, 5.6, 6, 0.5, 1.3, 0.6, 1.0)


def sneak_arm(t):
    return stop_resp(t - 0.15, 0.55, 0.035, 0.18, 0.1) - stop_resp(t - 8.9, 0.6, 0.04, 0.18, 0.1)


def loupe_in(t, t_in, t_out):
    return step_resp(t - t_in, 0.12, 0.1) - step_resp(t - t_out, 0.12, 0.08)


sneak = anim("sneak", SL, merge(PS.tracks(), {
    ARM: {"rotation": lambda t: (TH_D * sneak_arm(t), 0, 0)},
    LUN: {"rotation": lambda t: (-TH_D * sneak_arm(t) + 5 * ring(t - 0.72, 0.22, 0.12) - 4 * ring(t - 9.52, 0.2, 0.1), 0, 0)},
    PIGNON: {"rotation": lambda t: (-TH_D * 10 / 6 * sneak_arm(t), 0, 0)},
    LOUPES[0][0]: {"rotation": lambda t: kz(-LOUPES[0][1] * loupe_in(t, 1.5, 7.6))},
    LOUPES[1][0]: {"rotation": lambda t: kz(-LOUPES[1][1] * loupe_in(t, 2.4, 7.0) + 6 * (step_resp(t - 3.4, 0.05, 0.3) - step_resp(t - 3.8, 0.05, 0.3)))},
    HAT: {"rotation": lambda t: PS.recoil(t, 0.5)[0], "position": lambda t: PS.recoil(t, 0.5)[1]}}), fps=30)

# fall 1,2 s : le chapeau se soulève un peu, tout cliquette, vapeur coupée, aiguille affolée
FL = 1.2
fall = anim("fall", FL, {
    HAT: {"rotation": lambda t: (2.5 + 1.2 * math.sin(TAU * t / 0.6), 0, 0.6 * math.sin(TAU * t / FL)), "position": lambda t: (0, 0.32 + 0.08 * math.sin(TAU * t / FL), 0)},
    LUN: {"rotation": lambda t: (3.5 * math.sin(TAU * t / 0.3) + 1.5 * math.sin(TAU * t / 0.1), 0, 0)},
    LOUPES[0][0]: {"rotation": lambda t: kz(5 * math.sin(TAU * t / 0.3 + 1))},
    LOUPES[1][0]: {"rotation": lambda t: kz(-6 * math.sin(TAU * t / 0.2 + 2))},
    SOUP: {"position": lambda t: (0, 0.05 + 0.04 * math.sin(TAU * t / 0.15), 0), "rotation": lambda t: (3 * math.sin(TAU * t / 0.2), 0, 4 * math.sin(TAU * t / 0.3))},
    NEEDLE: {"rotation": lambda t: (110 - 220 * (0.55 + 0.12 * math.sin(TAU * t / 0.4) + 0.04 * math.sin(TAU * t / 0.1)), 0, 0)},
    VAP: {"scale": lambda t: (0, 0, 0)}, CTRL_E: {"position": lambda t: (-1, 0, 0)}}, fps=30)


def jet(t):
    """Jet : sort du fût (position), jaillit (échelle), monte, se résorbe, puis rentre caché."""
    up = 3.6 * sm(t, 0.04, 0.1) + 1.6 * sm(t, 0.12, 0.55)
    back = sm(t, 0.62, 0.66)
    sx = 1 + 2.4 * sm(t, 0.1, 0.2) - 3.4 * sm(t, 0.42, 0.62) + 1.0 * sm(t, 0.66, 0.74)
    sy = 1 + 3.0 * sm(t, 0.1, 0.22) + 1.0 * sm(t, 0.22, 0.5) - 5.0 * sm(t, 0.45, 0.62) + 1.0 * sm(t, 0.66, 0.74)
    return (sx, sy, sx), (0, up * (1 - back), 0)


# event_equip 1,5 s (par-dessus l'état) : le chapeau tombe sur la tête et rebondit en butée, la soupape lâche un jet de
# vapeur, l'aiguille bondit, les deux loupes font un essai ; tout revient à 0.
EQ = 1.5


def eq_jet(t):
    return jet(min(0.8, max(0.0, t - 0.62)))


equip = anim("event_equip", EQ, {
    HAT: {"position": lambda t: (0, 3.5 * (1 - stop_resp(t, 0.34, 0.06, 0.14, 0.08)), 0),
          "scale": lambda t: (lambda k: (k, k, k))(0.35 + 0.65 * sm(t, 0.0, 0.26))},
    NEEDLE: {"rotation": lambda t: (-150 * bump(t, 0.45, 0.6, 0.62, 0.95), 0, 0)},
    SOUP: {"position": lambda t: (0, 0.5 * bump(t, 0.6, 0.65, 0.95, 1.1), 0)},
    JET: {"scale": lambda t: eq_jet(t)[0], "position": lambda t: eq_jet(t)[1]},
    CTRL_E: {"position": lambda t: (5 * bump(t, 0.64, 0.66, 1.0, 1.1), 0, 0)},
    LUN: {"rotation": lambda t: (5 * ring(t - 0.36, 0.2, 0.1), 0, 0)},
    LOUPES[0][0]: {"rotation": lambda t: kz(-LOUPES[0][1] * 0.35 * bump(t, 0.7, 0.8, 1.0, 1.12))},
    LOUPES[1][0]: {"rotation": lambda t: kz(-LOUPES[1][1] * 0.35 * bump(t, 0.82, 0.92, 1.1, 1.24))}}, loop="once", fps=40)

ANIMS = [idle, walk, run, sneak, fall, equip]

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
textures.append({"name": f"{NOM}_r.png", "uv_width": TEX, "uv_height": TEX, "source": tex_r_b64})
equip["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "block.fire.extinguish", "file": ""}], "time": 0.66}]}
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
from ambiance import ajouter_ambiance
ajouter_ambiance(model)


# ------------------------------------------------------------------ faces proches (.claude/references/procedures/remise-aux-regles.md)
def decoller(model, seuil=0.1, cible=0.115, pas_max=0.26, passes=16, ep_min=0.28, log=print):
    """Écarte les faces parallèles visibles qui se chevauchent à moins de `seuil` px (faces opposées comprises), sur la
    pose de base : la face de la pièce la plus petite avance (de préférence) ou recule le long de sa normale jusqu'à
    `cible` px, de `pas_max` px au plus, sans qu'une pièce devienne plus mince que `ep_min`. Modifie model sur place."""
    import tempfile
    import numpy as np
    import render_bbmodel as rb
    from PIL import Image
    AX = {"east": (0, 1), "west": (0, -1), "up": (1, 1), "down": (1, -1), "south": (2, 1), "north": (2, -1)}
    by = {e["uuid"]: e for e in model["elements"]}
    tex = model["textures"][0]["source"].split(",", 1)[1]
    A = np.asarray(Image.open(io.BytesIO(base64.b64decode(tex))).convert("RGBA"))[..., 3] > 127
    H, W = A.shape

    def ordre():
        out = []

        def w(n):
            if isinstance(n, str):
                e = by[n]
                for f, fd in e["faces"].items():
                    if fd.get("texture") is None:
                        continue
                    u1, v1, u2, v2 = fd["uv"]
                    if u1 == u2 or v1 == v2:
                        continue
                    out.append((n, f))
            else:
                for c in n.get("children", []):
                    w(c)
        for n in model["outliner"]:
            if isinstance(n, dict) and n.get("name", "").startswith("particle_"):
                continue
            w(n)
        return out

    def opaque(uv4, s, t):
        top = uv4[0] + (uv4[1] - uv4[0]) * s[..., None]
        bot = uv4[3] + (uv4[2] - uv4[3]) * s[..., None]
        uv = top + (bot - top) * t[..., None]
        return A[np.clip((uv[..., 1] * H).astype(int), 0, H - 1), np.clip((uv[..., 0] * W).astype(int), 0, W - 1)]

    S_, T_ = np.meshgrid(np.linspace(0.02, 0.98, 20), np.linspace(0.02, 0.98, 20))
    S_, T_ = S_.ravel(), T_.ravel()
    restant = None
    cumul = {}                                  # déplacement total de chaque face : jamais de retour en arrière (pas d'oscillation)
    for passe in range(passes):
        fd, tmp = tempfile.mkstemp(suffix=".bbmodel")
        os.close(fd)
        with open(tmp, "w") as fh:
            json.dump({k: v for k, v in model.items() if k != "animations"}, fh)
        Q, _ = rb.load_model(tmp)
        os.remove(tmp)
        ids = ordre()
        assert len(ids) == len(Q)
        centre = {}
        for (eid, f), q in zip(ids, Q):
            centre.setdefault(eid, []).append(np.mean(np.array(q[0], float), 0))
        centre = {k: np.mean(v, 0) for k, v in centre.items()}
        F = []
        for (eid, f), q in zip(ids, Q):
            P, uv = np.array(q[0], float), np.array(q[1], float)
            n = np.cross(P[1] - P[0], P[3] - P[0])
            ar = np.linalg.norm(n)
            if ar < 1e-9:
                continue
            n = n / ar
            c = P.mean(0)
            out = n if (c - centre[eid]) @ n >= 0 else -n
            pts = P[0] + (P[1] - P[0]) * S_[:, None] + (P[3] - P[0]) * T_[:, None]
            op = opaque(uv, S_, T_)
            if not op.any():
                continue
            F.append(dict(eid=eid, f=f, P=P, n=out, ar=ar, pts=pts[op], lo=P.min(0) - seuil, hi=P.max(0) + seuil))
        paires = []
        for i in range(len(F)):
            a = F[i]
            for j in range(i + 1, len(F)):
                b = F[j]
                if a["eid"] == b["eid"] or abs(a["n"] @ b["n"]) < 0.9986:
                    continue
                if (a["lo"] > b["hi"]).any() or (b["lo"] > a["hi"]).any():
                    continue
                # échantillons opaques de b proches du plan de a et dans a (et réciproquement)
                best = None
                for x, y in ((a, b), (b, a)):
                    d = (y["pts"] - x["P"][0]) @ x["n"]
                    near = np.abs(d) < seuil
                    if not near.any():
                        continue
                    e1, e2 = x["P"][1] - x["P"][0], x["P"][3] - x["P"][0]
                    M = np.stack([e1, e2], 1)
                    st, *_ = np.linalg.lstsq(M, (y["pts"][near] - x["P"][0]).T, rcond=None)
                    ins = (st[0] > 0.005) & (st[0] < 0.995) & (st[1] > 0.005) & (st[1] < 0.995)
                    if not ins.any():
                        continue
                    dd = d[near][ins]
                    sd = float(dd[np.argmin(np.abs(dd))])
                    if best is None or abs(sd) < abs(best[1]):
                        best = (x is a, sd)
                if best is not None:
                    paires.append((i, j, best))
        if passe == 0:
            log(f"faces proches (< {seuil} px) avant décollement : {len(paires)}")
        if not paires:
            restant = 0
            break
        bouge = {}
        non = 0
        for i, j, (a_ref, sd) in paires:
            ref, oth = (F[i], F[j]) if a_ref else (F[j], F[i])
            # sd : distance signée de oth au plan de ref, le long de la normale sortante de ref
            opts = []
            for cible_s in (cible, -cible):
                for qui, k in ((oth, oth["n"] @ ref["n"]), (ref, -1.0)):
                    ds = cible_s - sd
                    delta = ds / k                      # avance de la face de qui le long de sa normale sortante
                    e = by[qui["eid"]]
                    ax, sg = AX[qui["f"]]
                    ep = e["to"][ax] - e["from"][ax]
                    if abs(delta) > pas_max or ep + delta < min(ep_min, ep):
                        continue
                    if (qui["eid"], qui["f"]) in bouge:
                        continue
                    c0 = cumul.get((qui["eid"], qui["f"]), 0.0)
                    if c0 * delta < 0 or abs(c0 + delta) > 1.4 * pas_max:
                        continue
                    score = abs(delta) + (0.04 if delta < 0 else 0) + 0.002 * qui["ar"]
                    opts.append((score, qui, delta))
            if not opts:
                non += 1
                continue
            _, qui, delta = min(opts, key=lambda o: o[0])
            bouge[(qui["eid"], qui["f"])] = delta
        for (eid, f), delta in bouge.items():
            cumul[(eid, f)] = cumul.get((eid, f), 0.0) + delta
            e = by[eid]
            ax, sg = AX[f]
            if sg > 0:
                e["to"][ax] = round(e["to"][ax] + delta, 3)
            else:
                e["from"][ax] = round(e["from"][ax] - delta, 3)
        restant = len(paires)
        log(f"  passe {passe + 1} : {len(paires)} paires, {len(bouge)} faces déplacées, {non} sans solution")
        if not bouge or passe == passes - 1:
            for i, j, (a_ref, sd) in paires:
                log(f"    reste {sd:+.3f} px : {by[F[i]['eid']]['name']}.{F[i]['f']} / {by[F[j]['eid']]['name']}.{F[j]['f']}")
            break
    return restant


RESTE_PROCHES = decoller(model)


def tete_libre(model, cas):
    """Rien d'opaque dans la tête et sa seconde couche (|x|, |z| < 4,62 et y < 32,62), sur les poses données."""
    import tempfile
    import render_bbmodel as rb
    os.environ["MODCONV"] = "1"                 # rotations lues telles quelles, comme le mod
    fd, tmp = tempfile.mkstemp(suffix=".bbmodel")
    os.close(fd)
    with open(tmp, "w") as fh:
        json.dump(model, fh)
    pire = None
    for nom, t in cas:
        Q, _ = rb.load_model(tmp, anim_time=t, anim_name=nom)
        for q in Q:
            P = np.array(q[0], float)
            S, T = np.meshgrid(np.linspace(0, 1, 6), np.linspace(0, 1, 6))
            pts = P[0] + (P[1] - P[0]) * S.ravel()[:, None] + (P[3] - P[0]) * T.ravel()[:, None]
            dans = (np.abs(pts[:, 0]) < 4.62) & (np.abs(pts[:, 2]) < 4.62) & (pts[:, 1] < 32.62) & (pts[:, 1] > 23.5)
            if dans.any():
                pire = (nom, t, pts[dans][0])
                break
        if pire:
            break
    os.remove(tmp)
    assert pire is None, f"pièce dans la tête : {pire}"


tete_libre(model, [("idle", 0.0), ("sneak", 0.5), ("sneak", 1.0), ("sneak", 3.0), ("sneak", 9.2), ("sneak", 9.6), ("run", 0.3), ("fall", 0.3)])
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", N_GROUPS, "groupes ; profondeur", depth(outliner[0]), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      f"bascule des lunettes {TH_D:.1f}° ; repos y={Y_REST:.2f} ; restant proches {RESTE_PROCHES}")
