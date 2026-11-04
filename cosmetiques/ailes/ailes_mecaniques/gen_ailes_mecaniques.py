"""Ailes mécaniques — ailes à vapeur articulées (laiton patiné, cuivre, acier sombre, vert-de-gris). Design original.
Écrit ailes_mecaniques.png, ailes_mecaniques_e.png et .build/ailes_mecaniques_brut.bbmodel à côté de ce script.

Squelette et orientations d'états repris de gen_ailes_abyssales.py : humérus > avant-bras > poignet > éventail.
Longerons : vrais volumes octogonaux. Éventail : 9 lames à deux sections (base + bout) qui pivotent toutes autour du
poignet, donc se referment sans ouvrir de trou. Chaque section = plaque découpée par alpha + âme pleine plus étroite.
Engrenages coude et poignet : disque par alpha + axe en volume, chacun dans son sous-groupe, 360° x k exact par boucle.
Vérin de l'humérus : le cylindre vise un tenon de l'avant-bras (cinématique calculée) et la tige coulisse (position).

Mouvement mécanique (.claude/styles/steampunk.md) : toute la pose suit une déformation du temps en paliers (palier()) :
départ sec, léger dépassement, arrêt ; nombre entier de crans par boucle (boucles fermées). Les lames gardent leur décalage
de phase, donc avancent cran par cran l'une après l'autre ; les engrenages avancent dent par dent.
Cycle de pression : manomètre sur chaque humérus (aiguille qui grimpe par crans, tremble, retombe), décharge à la tuyère
de l'avant-bras (trans_jet_<l|r>) : noyau de jet dense et court à la buse (trois plaques croisées en dégradé, échelle et
ctrl_alpha), puis 5 bouffées (bf<i>, plaque face caméra cam_) qui jaillissent l'une après l'autre le long du jet, grossissent et
s'éteignent (échelle vers 0). En vol, la pression monte pendant deux battements et la décharge propulse le troisième, plus ample.
En glide, les bouffées défilent à la fusée (Molang, math.mod).
Vapeur en particules (retour du 2026-11-04 : « pas juste pour mettre des particules ») : seulement là où une machine fume, les deux
évents de la petite chaudière et sa soupape de sûreté (points emit_vapeur…, convertis par tools/particules.py).
Fonctions avancées (guide 4 bis, 5 quater, 5 ter, 6.4, 6.5 ; .claude/rules/fonctions-avancees.md) : trans_ (jet, bouffées), cam_
(bouffées face caméra), ctrl_alpha (fondu du noyau, groupe trans_), particule modélisée vapeur, event_equip, masque de reflets
ailes_mecaniques_r.png (retiré par tools/ambiance.py tant que REFLETS = False), sifflement block.fire.extinguish (tools/sons.py).
Apparition (event_equip, 4,8 s, détail dans equip_anim()) : un sac dorsal sort du dos, la pression monte, les verrous claquent, les
portes s'ouvrent par crans, les ailes sortent repliées et se déplient par étapes, battement d'essai, engrenages qui s'emballent,
décharge, puis le sac rentre. Retour en jeu du 2026-11-04 : ctrl_alpha ne cache pas une partie opaque, donc les pièces propres à
l'apparition (sac, bouffées bfe<i>, fuites fu<i>) sont cachées dans tous les états par une échelle constante K_CACHE (le sac est
en plus enfoui dans le torse), qu'event_equip multiplie par 1/K_CACHE (échelles multipliées, guide 6.4).
"""
import base64, io, json, math, os, re, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # True : embarque ailes_mecaniques_e.png en seconde texture. Réactivé le 2026-11-03 (correctif du mod annoncé, à vérifier en jeu).
TEX = 512
V0, DV = 26, 5      # battement à la fusée (glide) : constantes validées en jeu
TAU = 2 * math.pi
NOM = "ailes_mecaniques"


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ squelette, dans le plan de l'aile (aile droite, x > 0)
Z = 5.2                                 # plan de l'aile (dos du joueur à z = 2)
S_, E_, W_ = (5.4, 23.0), (9.5, 31.5), (19.0, 39.0)
YAW = [20, -7, 8]                       # balayage arrière au repos : humérus, avant-bras, main

# Lames de la main : angle au poignet, longueur, matière du bout. Les longerons portent les lames 0, 3, 5 et 8.
RAYS = [(18.0, 31.0), (7.5, 32.5), (-3.0, 31.5), (-13.5, 30.5), (-24.0, 29.0), (-35.5, 27.5), (-47.0, 26.0), (-58.5, 24.5), (-70.0, 22.5)]
NR = len(RAYS)
SPARS = {0: 0.66, 3: 0.62, 5: 0.58, 8: 0.54}     # lame -> rayon du longeron à la base
CLOSE = [a - lerp(-36.0, -61.0, k / (NR - 1)) for k, (a, _) in enumerate(RAYS)]   # fermeture de chaque lame à fold = 1 (degrés)
CURLW = [lerp(1.0, 0.55, k / (NR - 1)) for k in range(NR)]
SECS = [(0.08, -106, 17.0), (0.29, -100, 18.5), (0.50, -94, 20.0), (0.71, -88, 21.5), (0.92, -80, 22.5)]     # u sur l'avant-bras, angle, longueur
TERS = [(0.25, -94, 9.0), (0.60, -97, 10.5), (0.92, -101, 12.5)]                                            # u sur l'humérus
AL_E, AL_W = 76.0, -30.0                                          # direction du pignon depuis le grand engrenage
PIN_E = (E_[0] + 4.8 * math.cos(math.radians(AL_E)), E_[1] + 4.8 * math.sin(math.radians(AL_E)))
PIN_W = (W_[0] + 3.9 * math.cos(math.radians(AL_W)), W_[1] + 3.9 * math.sin(math.radians(AL_W)))

rng = np.random.default_rng(1872)

# ------------------------------------------------------------------ matières
BRASS = dict(base=(178, 134, 60), hi=(238, 204, 122), low=(92, 62, 26))
COPPER = dict(base=(172, 88, 50), hi=(236, 150, 100), low=(84, 38, 22))
STEEL = dict(base=(70, 75, 86), hi=(150, 158, 172), low=(28, 30, 37))
PATINA = np.array((84, 156, 132), np.float32)
PATINA_D = np.array((46, 104, 92), np.float32)


def A(c):
    return np.array(c, np.float32)


def inset(mask, n):
    """Distance au bord, en texels, jusqu'à n (érosions successives)."""
    im = Image.fromarray(mask.astype(np.uint8) * 255, "L")
    d = np.zeros(mask.shape, np.float32)
    for i in range(n):
        im = im.filter(ImageFilter.MinFilter(3))
        d += np.array(im) > 127
    return d


def cell_noise(h, w, cells, seed):
    r = np.random.default_rng(seed)
    a = (r.random((max(2, int(cells * h / max(h, w))) + 2, max(2, int(cells * w / max(h, w))) + 2)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((w, h), Image.BICUBIC), np.float32) / 255


def rivet(col, x, y, r, metal):
    """Rivet peint : anneau sombre, tête claire, éclat. Au moins 3 à 4 texels pour rester lisible à distance de jeu."""
    h, w = col.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dd = np.hypot(xx + 0.5 - x, yy + 0.5 - y)
    col[dd <= r + 1.1] = A(metal["low"]) * 0.55
    col[dd <= r] = A(metal["base"])
    col[np.hypot(xx + 0.5 - x + r * 0.3, yy + 0.5 - y + r * 0.3) <= r * 0.55] = A(metal["hi"])


def poly_mask(w, h, polys, holes=(), ss=4):
    """Contours en coordonnées normalisées (u 0..1, v -1..1, +1 en haut) ; net : alpha 0/255."""
    im = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    conv = lambda u, v: (u * w * ss, (1 - v) / 2 * h * ss)
    for p in polys:
        d.polygon([conv(*q) for q in p], fill=255)
    for u, v, rx, ry in holes:
        cx, cy = conv(u, v)
        d.ellipse((cx - rx * ss, cy - ry * ss, cx + rx * ss, cy + ry * ss), fill=0)
    return np.array(im.resize((w, h), Image.LANCZOS)) > 110


def finish(col, mask):
    out = np.zeros(mask.shape + (4,), np.uint8)
    c = np.clip(col, 0, 255)
    if mask.any():
        c[~mask] = c[mask].mean(axis=0)
    out[..., :3] = c.astype(np.uint8)
    out[..., 3] = mask * 255
    return out


def paint_plate(w, h, poly, metal, seed, rivets=(), holes=(), tip=None, patina=0.3, root_shadow=True, rmetal=STEEL, spine=True):
    """Plaque de métal : brossé, bord biseauté, joint sombre, rivets, vert-de-gris en plaques nettes."""
    mask = poly_mask(w, h, [poly], holes)
    u = (np.arange(w) + 0.5)[None, :] / w * np.ones((h, 1))
    v = 1 - (np.arange(h) + 0.5)[:, None] / h * 2 * np.ones((1, w))
    r = np.random.default_rng(seed)
    streak = np.array(Image.fromarray((r.random((h, max(4, w // 12))) * 255).astype(np.uint8), "L").resize((w, h), Image.BILINEAR), np.float32) / 255 - 0.5
    col = A(metal["base"]) * np.ones((h, w, 3), np.float32)
    col *= (1 + 0.22 * streak)[..., None]
    col *= (1.08 - 0.20 * np.clip((-v + 0.2), 0, 1))[..., None]            # galbe : bord d'attaque plus clair
    if tip is not None:
        t0, tmetal = tip
        band = u >= t0
        col[band] = (A(tmetal["base"]) * ((1 + 0.2 * streak)[..., None]))[band]
        groove = (u >= t0 - 3.0 / w) & (u < t0)
        col[groove] = A(tmetal["low"]) * 0.7
    if spine:
        col[np.abs(v) < 2.5 / h * 2] = A(metal["low"])
    if patina:
        n = cell_noise(h, w, 22, seed + 1) * 0.5 + cell_noise(h, w, 48, seed + 2) * 0.5
        lim = 0.80 - patina * 0.24 + 0.20 * u                      # davantage vers la racine, où l'eau de condensation reste
        col[n > lim] = PATINA
        col[n > lim + 0.07] = PATINA_D
    d = inset(mask, 6)
    col[(d >= 3) & (d < 5)] = col[(d >= 3) & (d < 5)] * 0.48              # joint sombre
    col[d < 3] = A(metal["hi"]) * (0.9 + 0.2 * streak[d < 3])[..., None]  # biseau clair : le contour se lit net
    if root_shadow:
        col *= (0.45 + 0.55 * np.clip(u / 0.3, 0, 1))[..., None]           # ombre de recouvrement
    drip = np.random.default_rng(seed + 3)
    for ru, rv in rivets:
        x, y = ru * w, (1 - rv) / 2 * h
        if patina > 0.2 and drip.random() < 0.8:                           # le vert-de-gris coule depuis chaque rivet, vers le bout de la lame
            ln, wd = int(drip.uniform(9, 26)), drip.integers(3, 5)
            y0, y1, x0, x1 = int(y - wd / 2), int(y + wd / 2) + 1, int(x), int(x + ln)
            col[max(0, y0):y1, max(0, x0):min(w, x1)] = PATINA
            col[max(0, y0):y1, max(0, x0):min(w, x0 + ln // 2)] = PATINA_D
            col[max(0, int(y) - 5):int(y) + 6, max(0, int(x) - 5):int(x) + 6] = lerp(col[max(0, int(y) - 5):int(y) + 6, max(0, int(x) - 5):int(x) + 6], PATINA, 0.7)
    for ru, rv in rivets:
        rivet(col, ru * w, (1 - rv) / 2 * h, max(2.4, h * 0.045), rmetal)
    return finish(col, mask)


# Lames : u = 0 à la racine ; bord d'attaque (v > 0) droit, pointe chanfreinée, aucune pointe fine
OUTER = [(0, 0.54), (0.70, 0.94), (0.94, 0.72), (1.0, 0.30), (0.93, -0.70), (0.62, -1.0), (0, -0.54)]
OUTER2 = [(0, 0.54), (0.74, 0.96), (0.97, 0.62), (1.0, 0.0), (0.80, -0.92), (0.55, -1.0), (0, -0.54)]
INNER = [(0, 0.26), (0.08, 0.34), (1.0, 0.98), (1.0, -0.98), (0.08, -0.34), (0, -0.26)]
SEC = [(0, 0.34), (0.16, 0.52), (0.82, 1.0), (0.97, 0.70), (1.0, 0.22), (0.93, -0.62), (0.70, -1.0), (0.16, -0.52), (0, -0.34)]
RV_OUT = [(0.10, 0.62), (0.10, -0.62), (0.32, 0.76), (0.32, -0.76), (0.56, 0.74), (0.56, -0.74), (0.86, 0.48), (0.84, -0.42)]
RV_IN = [(0.30, 0.42), (0.30, -0.42), (0.62, 0.62), (0.62, -0.62), (0.90, 0.74), (0.90, -0.74)]
RV_SEC = [(0.20, 0.36), (0.20, -0.36), (0.42, 0.58), (0.42, -0.58), (0.65, 0.70), (0.65, -0.70), (0.86, 0.50), (0.84, -0.46)]
HOLES = [(0.76, 0.05, 4.8, 4.8)]

TILES = {}
OW, OH = 168, 84
TILES["out_brass"] = paint_plate(OW, OH, OUTER, BRASS, 11, RV_OUT, HOLES, tip=(0.83, COPPER), patina=0.38)
TILES["out_copper"] = paint_plate(OW, OH, OUTER2, COPPER, 21, RV_OUT, HOLES, tip=(0.82, BRASS), patina=0.46, rmetal=BRASS)
TILES["out_steel"] = paint_plate(OW, OH, OUTER, STEEL, 31, RV_OUT, HOLES, tip=(0.83, BRASS), patina=0.12, rmetal=BRASS)
TILES["in_steel"] = paint_plate(150, 58, INNER, STEEL, 41, RV_IN, patina=0.14, rmetal=BRASS)
TILES["in_brass"] = paint_plate(150, 58, INNER, BRASS, 51, RV_IN, patina=0.40)
TILES["sec_copper"] = paint_plate(172, 68, SEC, COPPER, 61, RV_SEC, patina=0.52, tip=(0.84, BRASS), rmetal=BRASS)
TILES["sec_steel"] = paint_plate(172, 68, SEC, STEEL, 71, RV_SEC, patina=0.14, tip=(0.84, COPPER), rmetal=BRASS)
TILES["ter"] = paint_plate(92, 52, SEC, STEEL, 81, [(0.25, 0.4), (0.25, -0.4), (0.60, 0.68), (0.60, -0.68)], patina=0.16, tip=(0.82, BRASS), rmetal=BRASS)
_chamf = [(0, 0.55), (0.06, 1), (0.94, 1), (1, 0.55), (1, -0.55), (0.94, -1), (0.06, -1), (0, -0.55)]
TILES["fair_long"] = paint_plate(150, 42, _chamf, BRASS, 91, [(x, y) for x in (0.08, 0.3, 0.52, 0.74, 0.92) for y in (0.66, -0.66)], patina=0.42, root_shadow=False, spine=False)
TILES["fair_short"] = paint_plate(92, 40, _chamf, STEEL, 95, [(x, y) for x in (0.1, 0.5, 0.9) for y in (0.64, -0.64)], patina=0.1, root_shadow=False, rmetal=BRASS, spine=False)
_spur = [(0, 0.5), (0.5, 0.8), (1.0, 0.1), (0.96, -0.2), (0.45, -0.8), (0, -0.5)]
TILES["spur"] = paint_plate(62, 34, _spur, STEEL, 97, [(0.2, 0.3), (0.2, -0.3)], tip=(0.64, BRASS), patina=0.08, rmetal=BRASS, root_shadow=False, spine=False)


def paint_sector(n, a0, a1, r0=0.15):
    """Capot du poignet : secteur riveté, en plaque découpée. Il couvre les racines de l'éventail."""
    ss = 4
    N = n * ss
    im = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(im)
    c = N / 2
    pts = [(c + r0 * c * math.cos(math.radians(a)), c - r0 * c * math.sin(math.radians(a))) for a in np.linspace(a0, a1, 24)]
    pts += [(c + 0.985 * c * math.cos(math.radians(a)), c - 0.985 * c * math.sin(math.radians(a))) for a in np.linspace(a1, a0, 48)]
    d.polygon(pts, fill=255)
    mask = np.array(im.resize((n, n), Image.LANCZOS)) > 110
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) / (n / 2)
    col = A(BRASS["base"]) * (0.92 + 0.14 * r)[..., None] * np.ones((n, n, 1), np.float32)
    nz = cell_noise(n, n, 12, 501) * 0.6 + cell_noise(n, n, 30, 502) * 0.4
    col[nz > 0.68] = PATINA
    col[nz > 0.73] = PATINA_D
    dd = inset(mask, 6)
    col[(dd >= 3) & (dd < 5)] *= 0.45
    col[dd < 3] = A(BRASS["hi"])
    for a in np.linspace(a0 - 7 * np.sign(a0 - a1), a1 + 7 * np.sign(a0 - a1), 8):
        rivet(col, n / 2 + 0.80 * n / 2 * math.cos(math.radians(a)), n / 2 - 0.80 * n / 2 * math.sin(math.radians(a)), n * 0.03, STEEL)
    # fentes du foyer : on voit rougeoyer le feu de la chaudière du poignet (lumière du calque _e, peinte plus bas)
    ang = np.degrees(np.arctan2(-(yy + 0.5 - n / 2), xx + 0.5 - n / 2))
    glow = np.zeros((n, n), np.float32)
    for a in np.linspace(a0 - 22, a1 + 26, 4):
        fente = (np.abs(ang - a) < 3.0) & (r > 0.56) & (r < 0.86) & mask        # hors du grand engrenage du poignet (rayon 0,48)
        glow = np.maximum(glow, fente * (1 - np.abs((r - 0.71) / 0.15)).clip(0.35, 1))
    col[glow > 0] = (70, 24, 10)
    SECTOR_GLOW[:] = [glow]
    return finish(col, mask)


SECTOR_GLOW = [None]


TILES["sector"] = paint_sector(112, 42, -96)
assert SECTOR_GLOW[0] is not None


def paint_gear(n, teeth, metal, tooth_phase, seed, spokes=None, hole=0.26, h_t=0.14):
    """Engrenage : disque par alpha (dents trapézoïdales, fenêtres). Une dent à l'angle tooth_phase (degrés), tous les 360/teeth."""
    ss = 4
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    dx, dy = (xx + 0.5 - N / 2) / (N / 2), -(yy + 0.5 - N / 2) / (N / 2)
    r, th = np.hypot(dx, dy), np.degrees(np.arctan2(dy, dx))
    pitch = 360 / teeth
    q = np.abs(((th - tooth_phase + pitch / 2) % pitch) - pitch / 2) / pitch      # 0 au centre de la dent, 0,5 au creux
    ro, rr = 0.98, 0.98 * (1 - h_t)
    edge = rr + (ro - rr) * np.clip((0.40 - q) / 0.17, 0, 1)                      # dent trapézoïdale : flancs nets
    m = (r <= edge) & (r >= hole)
    if spokes:
        ang = (th + 180 / spokes) % (360 / spokes) / (360 / spokes)
        win = (r > 0.42) & (r < rr - 0.17) & (np.abs(ang - 0.5) < 0.28)
        m &= ~win
    mask = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((n, n), Image.LANCZOS)) > 110
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) / (n / 2)
    col = A(metal["base"]) * np.ones((n, n, 3), np.float32)
    nz = cell_noise(n, n, 10, seed)
    col *= (0.86 + 0.28 * nz)[..., None]
    col[r > rr - 0.035] = A(metal["hi"])                                           # dents claires
    col[(r > rr - 0.13) & (r <= rr - 0.05)] *= 0.55                                # gorge sombre sous la couronne
    col[(r < hole + 0.11)] = A(metal["hi"]) * 0.9
    if nz.size and metal is BRASS:
        col[(nz > 0.80) & (r < rr - 0.14)] = PATINA
    return finish(col, mask)


G16 = paint_gear(92, 16, BRASS, 0.0, 601, spokes=5)
G8 = paint_gear(50, 8, STEEL, 22.5, 602, hole=0.30, h_t=0.22)
G12 = paint_gear(76, 12, COPPER, 0.0, 603, spokes=4)
G6 = paint_gear(42, 6, BRASS, 30.0, 604, hole=0.32, h_t=0.26)
TILES.update(g16=G16, g8=G8, g12=G12, g6=G6)


def bar_tile(metal, seed, groove=3):
    W_, H_ = 96, 16
    a = np.zeros((H_, W_, 3), np.float32)
    r = np.random.default_rng(seed)
    for yy in range(H_):
        q = abs((yy + 0.5) / H_ - 0.5) * 2
        c = lerp(A(metal["hi"]) * 0.8, A(metal["low"]), q ** 1.1)
        c = lerp(c, A(metal["base"]), 0.45)
        a[yy, :] = c
    a *= (0.92 + 0.16 * r.random((1, W_, 1), np.float32))
    for x in range(0, W_, W_ // groove):
        a[:, x:x + 2] = A(metal["base"]) * 0.62                                      # gorges d'usinage
    return finish(a, np.ones((H_, W_), bool))


def cap_tile(metal):
    n = 16
    c = A(metal["base"]) * np.ones((n, n, 3), np.float32)
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2)
    c[r > 6.2] = A(metal["low"])
    c[r < 3] = A(metal["hi"])
    return finish(c, np.ones((n, n), bool))


def rib_tile(metal, rm):
    w, h = 96, 12
    c = np.zeros((h, w, 3), np.float32)
    for yy in range(h):
        c[yy, :] = lerp(lerp(A(metal["base"]), A(metal["hi"]), 0.25), A(metal["low"]), abs((yy + 0.5) / h - 0.5) * 2)
    for x in np.arange(12, w, 32):
        rivet(c, x, h / 2, 2.0, rm)
    return finish(c, np.ones((h, w), bool))


TILES.update(bar_brass=bar_tile(BRASS, 701), bar_steel=bar_tile(STEEL, 702), bar_copper=bar_tile(COPPER, 703, 4))
TILES.update(cap_brass=cap_tile(BRASS), cap_steel=cap_tile(STEEL), cap_copper=cap_tile(COPPER))
TILES.update(rib_brass=rib_tile(BRASS, STEEL), rib_steel=rib_tile(STEEL, BRASS))

# Foyer de la petite chaudière : grille + braises, vue seulement de près
_f = np.zeros((16, 26, 3), np.float32)
_f[...] = (34, 28, 26)
_rf = np.random.default_rng(801)
_f[3:13, 3:23] = (118, 54, 22) + _rf.random((10, 20, 1), np.float32) * (72, 58, 16)
_f[3:13, 8:10] = _f[3:13, 15:17] = (30, 28, 30)
TILES["foyer"] = finish(_f, np.ones((16, 26), bool))


def paint_jet(w=24, h=56):
    """Jet de vapeur vu de côté, la buse en bas : panache qui s'élargit, dense à la base, qui s'efface vers le bout.
    Alpha en dégradé (groupe trans_) ; le cœur reste au-dessus de 50 % pour se lire aussi en cutout."""
    yy, xx = np.mgrid[0:h, 0:w]
    v = 1 - (yy + 0.5) / h                       # 0 à la buse, 1 au bout
    u = (xx + 0.5) / w * 2 - 1
    half = 0.28 + 0.62 * v ** 0.7 + 0.06 * np.sin(v * 17)
    r = np.abs(u) / half
    puff = 0.5 + 0.5 * np.sin(v * 23 + np.sin(u * 3) * 1.4)
    a = np.clip(1 - r, 0, 1) ** 0.8 * np.clip(1.15 - v * 1.05, 0, 1) * (0.78 + 0.22 * puff)
    alpha = np.clip(a * 300, 0, 254).astype(np.uint8)
    alpha[alpha < 14] = 0
    c = np.empty((h, w, 3), np.float32)
    c[...] = lerp(A((236, 240, 244)), A((206, 214, 222)), np.clip(r, 0, 1)[..., None])
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = c.astype(np.uint8)
    out[..., 3] = alpha
    return out


def paint_dial(n=28):
    """Cadran de manomètre : couronne de laiton rivetée, fond ivoire, graduations, zone rouge en haut à droite."""
    yy, xx = np.mgrid[0:n, 0:n]
    dx, dy = xx + 0.5 - n / 2, yy + 0.5 - n / 2
    r = np.hypot(dx, dy) / (n / 2)
    ang = np.degrees(np.arctan2(-dy, dx))                  # 0 à droite, 90 en haut
    c = np.empty((n, n, 3), np.float32)
    c[...] = (226, 214, 184)
    c[r > 0.80] = BRASS["base"]
    c[(r > 0.80) & (dy < -dx * 0.3)] = BRASS["hi"]
    c[r > 0.93] = BRASS["low"]
    # graduations de -120° à +120° autour du haut (sens horaire), la dernière part en rouge
    g = (90 - ang) % 360
    g = np.where(g > 180, g - 360, g)
    on = (np.abs(g) <= 122) & (r > 0.58) & (r < 0.76)
    tick = on & (np.abs(((g + 120) % 30) - 15) > 11.5)
    c[tick] = (52, 44, 36)
    c[on & (g > 72) & (r > 0.64)] = (186, 40, 30)
    c[r < 0.16] = STEEL["low"]
    return finish(c, r <= 1.0)


def paint_needle(w=4, h=16):
    c = np.empty((h, w, 3), np.float32)
    c[...] = (40, 36, 34)
    c[: h // 3] = (178, 36, 26)
    return finish(c, np.ones((h, w), bool))


def paint_bouffee(n, seed, a_max=236):
    """Bouffée de vapeur vue de face (groupe cam_ dans un groupe trans_) : quelques lobes ronds qui se chevauchent,
    bord irrégulier, opacité qui décroît vers le bord, ombre bleutée en bas à droite. Même recette que tools/particules.py."""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:n, 0:n]
    u, v = (xx + 0.5) / n * 2 - 1, (yy + 0.5) / n * 2 - 1
    d = np.full((n, n), 9.0)
    for _ in range(7):
        cx, cy, rr = r.uniform(-0.32, 0.32), r.uniform(-0.3, 0.3), r.uniform(0.42, 0.62)
        d = np.minimum(d, np.hypot(u - cx, v - cy) / rr)
    a = np.clip(1 - d, 0, 1) ** 0.75
    lum = np.clip(1 - np.hypot(u + 0.3, v + 0.35) / 1.5, 0, 1)
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = lerp(A((206, 214, 224)), A((250, 251, 252)), lum[..., None]).astype(np.uint8)
    out[..., 3] = np.where(a > 0.07, np.clip(a * a_max * 1.3, 1, 254), 0).astype(np.uint8)
    return out


TILES["jet"] = paint_jet()
BOUFFEES = [f"bouffee{i}" for i in range(3)]
for _i, _n in enumerate(BOUFFEES):
    TILES[_n] = paint_bouffee(30, 1900 + _i)
TILES["cadran"] = paint_dial()
TILES["aiguille"] = paint_needle()


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
    tex[v0:v1, u0:u1] = im
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC                                         # postérisation invisible à l'œil : PNG nettement plus léger
tex[tex[..., 3] == 0] = 0
_ju0, _jv0, _ju1, _jv1 = UV["jet"]
_opaque = tex.copy()
_opaque[_jv0:_jv1, _ju0:_ju1] = 0
for _n in BOUFFEES:
    _bu0, _bv0, _bu1, _bv1 = UV[_n]
    _opaque[_bv0:_bv1, _bu0:_bu1] = 0

# Calque lumineux, non embarqué tant que AVEC_E = False : foyer, bouts de tuyère ; fond noir ; un filet très sombre sur le capot.
u0, v0, u1, v1 = UV["foyer"]
tex_e[v0 + 3:v1 - 3, u0 + 3:u1 - 3] = (230, 120, 40, 255)
tex_e[v0 + 3:v1 - 3, u0 + 8:u0 + 10] = 0
tex_e[v0 + 3:v1 - 3, u0 + 15:u0 + 17] = 0
# nervures des lames : un filet de verre ambré où circule la vapeur chaude (calque _e, ×2,4 par ajouter_ambiance) ;
# ce sont les âmes pleines, visibles sur toute la longueur des lames, des deux côtés
for _nm in ("rib_brass", "rib_steel"):
    u0, v0, u1, v1 = UV[_nm]
    _h = v1 - v0
    _rows = np.abs(np.arange(_h) + 0.5 - _h / 2)[:, None] * np.ones((1, u1 - u0))
    _ligne = (tex[v0:v1, u0:u1, 3] > 0) & (_rows < max(1.2, _h * 0.18))
    _k = np.clip(1 - _rows / max(1.2, _h * 0.18), 0.5, 1)
    tex[v0:v1, u0:u1][_ligne] = (110, 60, 24, 255)
    tex_e[v0:v1, u0:u1][_ligne] = np.concatenate([(np.array((240, 150, 50))[None, :] * _k[_ligne][:, None] / 2.4).astype(np.uint8), np.full((int(_ligne.sum()), 1), 255, np.uint8)], axis=1)
u0, v0, u1, v1 = UV["sector"]
_g = SECTOR_GLOW[0]
tex_e[v0:v1, u0:u1][_g > 0] = np.concatenate([(np.array((235, 110, 34))[None, :] * _g[_g > 0][:, None] / 2.4).astype(np.uint8), np.full((int((_g > 0).sum()), 1), 255, np.uint8)], axis=1)   # ×2,4 par ajouter_ambiance
u0, v0, u1, v1 = UV["cap_copper"]
_yy, _xx = np.mgrid[0:16, 0:16]
_m = np.hypot(_xx + 0.5 - 8, _yy + 0.5 - 8) < 3
tex_e[v0:v1, u0:u1][_m] = (120, 64, 20, 255)
assert set(np.unique(_opaque[..., 3])) <= {0, 255}, "semi-transparence hors du jet (trans_)"
_cu0, _cv0, _cu1, _cv1 = UV["cadran"]
_dial = tex[_cv0:_cv1, _cu0:_cu1]
tex_e[_cv0:_cv1, _cu0:_cu1][(_dial[..., 3] > 0) & (_dial[..., 0] > 200) & (_dial[..., 2] > 150)] = (70, 58, 34, 255)   # fond du cadran, lueur douce
assert set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence _e"
tex_img = Image.fromarray(tex, "RGBA")
tex_img.save(f"{NOM}.png", optimize=True)
_b = io.BytesIO()
tex_img.save(_b, "PNG", optimize=True)
tex_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()
tex_r = np.zeros((TEX, TEX, 4), np.uint8)
REFLET = {"brass": 190, "copper": 160, "steel": 95, "g16": 185, "g8": 185, "g12": 185, "g6": 185, "sector": 150, "cadran": 70, "spur": 95}
for n_ in TILES:
    val = next((v for k, v in REFLET.items() if k in n_), 0)
    if val:
        u0, v0, u1, v1 = UV[n_]
        zone = tex[v0:v1, u0:u1, 3] > 0
        tex_r[v0:v1, u0:u1][zone] = (val, val, val, 255)
tex_r_img = Image.fromarray(tex_r, "RGBA")
tex_r_img.save(f"{NOM}_r.png", optimize=True)
_b = io.BytesIO()
tex_r_img.save(_b, "PNG", optimize=True)
tex_r_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()
tex_e_img = Image.fromarray(tex_e, "RGBA")
tex_e_img.save(f"{NOM}_e.png", optimize=True)
_b = io.BytesIO()
tex_e_img.save(_b, "PNG", optimize=True)
tex_e_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def cube(name, frm, to, origin, rot=(0, 0, 0), faces=None):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to],
         "origin": [round(v, 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(v, 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(rot):
        e["rotation"] = [round(v, 2) for v in rot]
    elements.append(e)
    return e["uuid"]


def group(name, origin, parent=None, rotation=(0, 0, 0), nom=None):
    """name : clé unique dans ce script ; nom : nom du groupe dans le modèle s'il doit se répéter (ctrl_alpha, emit_mc_…)."""
    assert name not in groups
    groups[name] = {"origin": [round(v, 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(v, 2) for v in rotation], "nom": nom or name}
    return name


def flat(s, g, name, x0, y0, r0, r1, w, th, z, phi, tile, solid=False):
    """Cube le long de l'axe local X depuis le pivot (x0, y0), tourné de phi dans le plan de l'aile.
    solid=False : plaque découpée, tranches transparentes. solid=True : âme pleine, 6 faces texturées."""
    u0, v0, u1, v1 = UV[tile]
    ua, ub = (u0, u1) if s > 0 else (u1, u0)
    if solid:
        side = [u0, v0, u1, v1]
        endc = [u0, v0 + 2, u0 + 3, v1 - 2]
        faces = {"south": [ua, v0, ub, v1], "north": [ub, v0, ua, v1], "up": side, "down": side, "east": endc, "west": endc}
    else:
        faces = {"south": [ua, v0, ub, v1], "north": [ub, v0, ua, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
    a, b = (x0 + r0, x0 + r1) if s > 0 else (-x0 - r1, -x0 - r0)
    groups[g]["ids"].append(cube(name, [a, y0 - w / 2, z - th / 2], [b, y0 + w / 2, z + th / 2], [s * x0, y0, z], rot=(0, 0, s * phi), faces=faces))


def bar(s, g, name, x, y, z, L, q, phi, mat, u0=0.0, u1=1.0, octo=True, ov=0.0):
    """Tronçon le long de l'axe local X. octo : section octogonale (deux cubes à 45°)."""
    bu0, bv0, bu1, bv1 = UV[f"bar_{mat}"]
    ua, ub = lerp(bu0, bu1, u0), max(lerp(bu0, bu1, u1), lerp(bu0, bu1, u0) + 2)
    long_ = [ua, bv0, ub, bv1]
    cu0, cv0, cu1, cv1 = UV[f"cap_{mat}"]
    end = [cu0, cv0, cu1, cv1]
    faces = {"south": long_, "north": long_, "up": long_, "down": long_, "east": end, "west": end}
    a, b = (x - ov, x + L + ov) if s > 0 else (-x - L - ov, -x + ov)
    o = [s * x, y, z]
    gid = groups[g]["ids"]
    gid.append(cube(name, [a, y - q, z - q], [b, y + q, z + q], o, rot=(0, 0, s * phi), faces=faces))
    if octo:
        gid.append(cube(name + "o", [a + 0.03, y - q * 0.97, z - q * 0.97], [b - 0.03, y + q * 0.97, z + q * 0.97], o, rot=(45, 0, s * phi), faces=faces))


def chain(s, g, name, pts, r0, r1, mat, u0=0.0, u1=1.0, z=Z, z1=None, ov=0.1):
    """Longeron : tronçons qui se recouvrent, rayon qui décroît."""
    n = len(pts) - 1
    z1 = z if z1 is None else z1
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        L = math.dist(pts[i], pts[i + 1])
        phi = math.degrees(math.atan2(yb - ya, xb - xa))
        t0, t1 = i / n, (i + 1) / n
        bar(s, g, f"{name}{i}", xa, ya, lerp(z, z1, (t0 + t1) / 2), L, lerp(r0, r1, (t0 + t1) / 2), phi, mat, lerp(u0, u1, t0), lerp(u0, u1, t1), ov=ov)


def axle(s, g, name, x, y, z0, z1, r, mat):
    """Axe perpendiculaire au plan de l'aile : octogone (deux cubes, le second à 45° autour de Z)."""
    bu0, bv0, bu1, bv1 = UV[f"bar_{mat}"]
    long_ = [bu0, bv0, bu0 + 30, bv1]
    cu0, cv0, cu1, cv1 = UV[f"cap_{mat}"]
    faces = {"south": [cu0, cv0, cu1, cv1], "north": [cu0, cv0, cu1, cv1], "up": long_, "down": long_, "east": long_, "west": long_}
    X = s * x
    gid = groups[g]["ids"]
    gid.append(cube(name, [X - r, y - r, z0], [X + r, y + r, z1], [X, y, (z0 + z1) / 2], faces=faces))
    gid.append(cube(name + "o", [X - r * 0.97, y - r * 0.97, z0 + 0.03], [X + r * 0.97, y + r * 0.97, z1 - 0.03], [X, y, (z0 + z1) / 2], rot=(0, 0, 45), faces=faces))


def disc(s, g, name, cx, cy, radius, z, tile, phase, th=0.45):
    """Disque découpé par alpha, centré sur (cx, cy), tourné de phase (la dent de référence vise cette direction)."""
    u0, v0, u1, v1 = UV[tile]
    ua, ub = (u0, u1) if s > 0 else (u1, u0)
    faces = {"south": [ua, v0, ub, v1], "north": [ub, v0, ua, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
    X = s * cx
    groups[g]["ids"].append(cube(name, [X - radius, cy - radius, z - th / 2], [X + radius, cy + radius, z + th / 2], [X, cy, z], rot=(0, 0, s * phase), faces=faces))


EMITS = []


def emit(parent, x, y, z):
    """Vapeur de Minecraft qui monte (+Y du groupe) ; le nom se répète (guide 5 ter)."""
    EMITS.append(group(f"emit_mc_white_smoke_{len(EMITS)}", [x, y, z], parent=parent, nom="emit_mc_white_smoke"))


def rotm(rx, ry, rz):
    """Même ordre que le renderer du dépôt : X, puis Y, puis Z."""
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
            @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))


ZV = Z + 2.0                                          # plan du vérin, côté dos
V_A, V_B = (4.6, 25.2), (13.4, 33.0)                  # tenon sur l'humérus (près de l'épaule) ; tenon sur l'avant-bras
CYL = 6.0                                             # longueur du cylindre
ROD_IN = 2.6                                          # la tige démarre à cette distance du pivot : marge dans le cylindre


def verin_aim(s, elbow_rot):
    """(rotations Y, Z du vérin, longueur) pour une rotation de coude ; tout est exprimé dans le repère de l'humérus."""
    P = np.array((s * E_[0], E_[1], Z))
    B = np.array((s * V_B[0], V_B[1], ZV)) - P
    B1 = rotm(*elbow_rot) @ B + P
    v = B1 - np.array((s * V_A[0], V_A[1], ZV))
    L = float(np.linalg.norm(v))
    u = s * v / L
    return math.degrees(math.asin(-u[2])), math.degrees(math.atan2(u[1], u[0])), L


NB_BF, NB_BFE = 5, 4      # bouffées par tuyère : états, apparition
K_CACHE = 0.2             # échelle constante des pièces de l'apparition dans tous les états en boucle (cachées : dans la buse,
                          # la soupape ou le torse) ; event_equip la multiplie par 1/K_CACHE (guide 6.4 : échelles multipliées)
CACHES = []               # groupes concernés


def bouffee(parent, name, x, y, z, size, tile):
    """Bouffée : groupe animé (position, échelle ; pivot au centre) > groupe cam_ (face caméra, sans animation : le mod
    applique l'animation d'un cam_ après l'orientation) > une plaque, face south seule. Renvoie le nom du groupe animé."""
    g = group(name, [x, y, z], parent=parent)
    c = group(f"cam_{name}", [x, y, z], parent=g)
    u0, v0, u1, v1 = UV[tile]
    h = size / 2
    groups[c]["ids"].append(cube(name, [x - h, y - h, z - 0.15], [x + h, y + h, z + 0.15], [x, y, z],
                                 faces={"south": [u0, v0, u1, v1], "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}))
    return g


VREST = {}
GAUGE, PRESS = {}, {}
SEG = ["shoulder", "elbow", "wrist"]
BUILD = {}


def build(s):
    tag = "l" if s < 0 else "r"
    pv = [S_, E_, W_]
    segs = []
    for i in range(3):
        segs.append(group(f"{SEG[i]}_{tag}", [s * pv[i][0], pv[i][1], Z], parent=segs[i - 1] if i else None, rotation=(0, -s * YAW[i], 0)))
    sh, el, wr = segs
    # racine : sort du dos, fixe ; pas de pièce dorsale, seulement la conduite qui va à la petite chaudière
    rt = group(f"wingroot_{tag}", [s * S_[0], S_[1], Z])
    chain(s, rt, f"root_{tag}", [(2.2, 21.8), (3.9, 22.2), S_], 0.72, 0.92, "steel", z=3.6, z1=Z)
    bar(s, rt, f"bague0_{tag}", 3.3, 22.05, 4.1, 0.8, 1.02, 13, "copper")

    # ------- longerons d'humérus et d'avant-bras
    chain(s, sh, f"hum_{tag}", [S_, (lerp(S_[0], E_[0], 0.5), lerp(S_[1], E_[1], 0.5)), E_], 1.08, 0.94, "steel")
    fa = [(lerp(E_[0], W_[0], t), lerp(E_[1], W_[1], t)) for t in (0, 0.33, 0.67, 1)]
    chain(s, el, f"avb_{tag}", fa, 1.04, 0.72, "brass")
    bar(s, sh, f"epaule_{tag}", S_[0] - 0.6, S_[1] - 1.1, Z, 1.2, 1.32, 64, "brass")
    bar(s, el, f"bague_{tag}", lerp(E_[0], W_[0], 0.48), lerp(E_[1], W_[1], 0.48), Z, 0.9, 1.08, 38.3, "copper")

    # ------- carénages rivetés sur les longerons : ils couvrent la racine des lames
    fphi = math.degrees(math.atan2(W_[1] - E_[1], W_[0] - E_[0]))
    flat(s, el, f"car_av_{tag}", E_[0], E_[1], 1.0, 12.4, 4.6, 0.36, Z + 0.86, fphi, "fair_long")
    hphi = math.degrees(math.atan2(E_[1] - S_[1], E_[0] - S_[0]))
    flat(s, sh, f"car_hum_{tag}", S_[0], S_[1], 0.6, 8.2, 3.8, 0.36, Z + 0.88, hphi, "fair_short")

    # ------- lames tertiaires et secondaires : plaque découpée + âme pleine
    for j, (u, a, L) in enumerate(TERS):
        px, py = lerp(S_[0], E_[0], u), lerp(S_[1], E_[1], u)
        g = group(f"ter{j + 1}_{tag}", [s * px, py, Z], parent=sh)
        zz = Z - 0.42 + 0.14 * j
        flat(s, g, f"tp{j}_{tag}", px, py, 0.8, L, 5.6, 0.4, zz, a, "ter")
        flat(s, g, f"tc{j}_{tag}", px, py, 1.0, L * 0.68, 0.8, 0.72, zz + 0.01, a, "rib_steel", solid=True)
    for j, (u, a, L) in enumerate(SECS):
        px, py = lerp(E_[0], W_[0], u), lerp(E_[1], W_[1], u)
        g = group(f"sec{j + 1}_{tag}", [s * px, py, Z], parent=el)
        zz = Z + 0.34 - 0.14 * j
        flat(s, g, f"sp{j}_{tag}", px, py, 0.8, L, 7.0, 0.4, zz, a, "sec_copper" if j % 2 == 0 else "sec_steel")
        flat(s, g, f"sc{j}_{tag}", px, py, 1.0, L * 0.70, 0.9, 0.74, zz + 0.012, a, "rib_brass", solid=True)

    # ------- éventail de la main
    for k, (a, L) in enumerate(RAYS):
        Ri = L * 0.52
        g = group(f"ray{k}_{tag}", [s * W_[0], W_[1], Z], parent=wr)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        J = (W_[0] + Ri * ca, W_[1] + Ri * sa)
        gb = group(f"ray{k}b_{tag}", [s * J[0], J[1], Z], parent=g)
        zz = Z + 0.56 - 0.14 * k
        flat(s, g, f"ri{k}_{tag}", W_[0], W_[1], 1.5, Ri + 0.9, 5.4, 0.4, zz, a, "in_steel" if k % 2 == 0 else "in_brass")
        flat(s, g, f"rc{k}_{tag}", W_[0], W_[1], 1.8, Ri, 0.8, 0.7, zz + 0.012, a, "rib_steel" if k % 2 == 0 else "rib_brass", solid=True)
        tile = ["out_brass", "out_copper", "out_brass", "out_steel"][k % 4]
        W_o = lerp(8.2, 9.6, (L - 22) / 13)
        flat(s, gb, f"ro{k}_{tag}", J[0], J[1], -0.9, L - Ri, W_o, 0.4, zz + 0.05, a, tile)
        flat(s, gb, f"rd{k}_{tag}", J[0], J[1], -0.5, (L - Ri) * 0.60, 0.85, 0.72, zz + 0.062, a, "rib_brass" if k % 2 == 0 else "rib_steel", solid=True)
        if k in SPARS:
            r0 = SPARS[k]
            chain(s, g, f"lg{k}_{tag}", [W_, (lerp(W_[0], J[0], 0.5), lerp(W_[1], J[1], 0.5)), J], r0, r0 * 0.76, "brass" if k % 2 == 0 else "steel", z=Z + 0.05 * (4 - k))
            T = (J[0] + (L - Ri - 2.2) * ca, J[1] + (L - Ri - 2.2) * sa)
            chain(s, gb, f"lh{k}_{tag}", [J, (lerp(J[0], T[0], 0.5), lerp(J[1], T[1], 0.5)), T], r0 * 0.70, r0 * 0.42, "steel" if k % 2 == 0 else "brass", z=Z + 0.05 * (4 - k))
            bar(s, gb, f"nod{k}_{tag}", J[0] - 0.42 * ca, J[1] - 0.42 * sa, Z + 0.05 * (4 - k), 0.84, r0 * 1.12, a, "copper")

    # ------- capot du poignet et éperon
    flat(s, wr, f"capot_{tag}", W_[0] - 6.2, W_[1], 0.0, 12.4, 12.4, 0.4, Z + 0.96, 0, "sector")
    bar(s, wr, f"nodw_{tag}", W_[0] - 1.2, W_[1] - 0.25, Z, 2.2, 0.98, 14, "steel")
    th = group(f"thumb_{tag}", [s * W_[0], W_[1], Z], parent=wr)
    flat(s, th, f"spur_{tag}", W_[0], W_[1], 1.0, 8.2, 3.0, 0.4, Z - 0.16, 76, "spur")
    flat(s, th, f"spurc_{tag}", W_[0], W_[1], 1.0, 5.6, 0.72, 0.7, Z - 0.15, 76, "rib_steel", solid=True)

    # ------- engrenages : chacun son sous-groupe, disque + axe en volume ; pignon engrené, tourne deux fois plus vite
    ge = group(f"gear_ea_{tag}", [s * E_[0], E_[1], Z], parent=el)
    gp = group(f"gear_ep_{tag}", [s * PIN_E[0], PIN_E[1], Z], parent=el)
    gw = group(f"gear_wa_{tag}", [s * W_[0], W_[1], Z], parent=wr)
    gq = group(f"gear_wp_{tag}", [s * PIN_W[0], PIN_W[1], Z], parent=wr)
    disc(s, ge, f"ge1_{tag}", E_[0], E_[1], 3.65, Z + 1.56, "g16", AL_E)
    disc(s, ge, f"ge2_{tag}", E_[0], E_[1], 3.65, Z - 1.56, "g16", AL_E + 0.0)
    axle(s, ge, f"gea_{tag}", E_[0], E_[1], Z - 2.0, Z + 2.0, 0.92, "steel")
    bar(s, el, f"bride_{tag}", E_[0], E_[1], Z + 1.12, 4.8, 0.42, AL_E, "steel", 0.1, 0.5)
    disc(s, gp, f"gp1_{tag}", PIN_E[0], PIN_E[1], 1.98, Z + 1.62, "g8", AL_E + 180 - 22.5 + 22.5)
    axle(s, gp, f"gpa_{tag}", PIN_E[0], PIN_E[1], Z + 0.6, Z + 2.05, 0.6, "brass")
    disc(s, gw, f"gw1_{tag}", W_[0], W_[1], 2.95, Z + 1.50, "g12", AL_W)
    disc(s, gw, f"gw2_{tag}", W_[0], W_[1], 2.95, Z - 1.26, "g12", AL_W)
    axle(s, gw, f"gwa_{tag}", W_[0], W_[1], Z - 1.7, Z + 1.95, 0.78, "brass")
    disc(s, gq, f"gq1_{tag}", PIN_W[0], PIN_W[1], 1.62, Z + 1.56, "g6", AL_W + 180 - 30 + 30)
    axle(s, gq, f"gqa_{tag}", PIN_W[0], PIN_W[1], Z + 0.6, Z + 2.0, 0.5, "steel")

    # ------- vérin : le cylindre (dans le repère de l'humérus) vise le tenon de l'avant-bras, la tige coulisse dedans
    y0, z0, L0 = verin_aim(s, (0, -s * YAW[1], 0))
    VREST[tag] = (y0, z0, L0)
    vc = group(f"verin_{tag}", [s * V_A[0], V_A[1], ZV], parent=sh, rotation=(0, y0, z0))
    vt = group(f"tige_{tag}", [s * V_A[0], V_A[1], ZV], parent=vc)
    bar(s, vc, f"vcyl_{tag}", V_A[0], V_A[1], ZV, CYL, 0.82, 0, "steel", 0.0, 0.6)
    bar(s, vc, f"vcol_{tag}", V_A[0] + CYL - 0.5, V_A[1], ZV, 0.7, 0.98, 0, "brass")
    bar(s, vc, f"vfon_{tag}", V_A[0] - 0.2, V_A[1], ZV, 0.8, 1.0, 0, "brass")
    bar(s, vt, f"vtig_{tag}", V_A[0] + ROD_IN, V_A[1], ZV, L0 - ROD_IN, 0.36, 0, "steel", 0.6, 1.0)
    axle(s, sh, f"vten0_{tag}", V_A[0], V_A[1], Z + 0.5, ZV + 0.5, 0.52, "brass")
    axle(s, el, f"vten1_{tag}", V_B[0], V_B[1], Z + 0.6, ZV + 0.5, 0.52, "brass")

    # ------- tuyaux de cuivre, colliers, tuyère au bout de l'avant-bras
    zp = Z + 1.15
    chain(s, sh, f"tuh_{tag}", [(5.9, 22.6), (8.1, 25.6), (10.6, 29.9)], 0.34, 0.32, "copper", z=zp, ov=0.08)
    chain(s, el, f"tuf_{tag}", [(10.6, 29.9), (14.2, 32.7), (18.0, 35.6)], 0.32, 0.30, "copper", z=zp, ov=0.08)
    bar(s, sh, f"coh_{tag}", 7.9, 25.3, zp, 0.6, 0.44, 54, "brass")
    bar(s, el, f"cof_{tag}", 14.0, 32.55, zp, 0.6, 0.42, 37, "brass")
    axle(s, el, f"tuy_{tag}", 18.0, 35.6, zp - 0.2, zp + 1.3, 0.54, "copper")

    # ------- manomètre sur l'humérus, côté bord de fuite, au-dessus des tuyaux ; l'aiguille a son propre groupe
    hx, hy = (E_[0] - S_[0]) / math.dist(S_, E_), (E_[1] - S_[1]) / math.dist(S_, E_)
    GP = (S_[0] + 0.35 * (E_[0] - S_[0]) + 2.6 * hy, S_[1] + 0.35 * (E_[1] - S_[1]) - 2.6 * hx)
    zg = Z + 1.8
    GAUGE[tag] = GP
    axle(s, sh, f"mano_tige_{tag}", GP[0], GP[1], Z + 0.95, zg - 0.12, 0.36, "brass")
    disc(s, sh, f"mano_{tag}", GP[0], GP[1], 1.3, zg, "cadran", 0, th=0.3)
    ag = group(f"aiguille_{tag}", [s * GP[0], GP[1], zg], parent=sh)
    au0, av0, au1, av1 = UV["aiguille"]
    groups[ag]["ids"].append(cube(f"aig_{tag}", [s * GP[0] - 0.13, GP[1] - 0.2, zg + 0.17], [s * GP[0] + 0.13, GP[1] + 1.05, zg + 0.24], [s * GP[0], GP[1], zg],
                                  faces={"south": [au0, av0, au1, av1], "north": [au0, av0, au1, av1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}))

    # ------- décharge à la tuyère (axe du jet = +Z du repère de l'avant-bras) :
    #   noyau : jet dense et court à la buse (trois plaques croisées en dégradé, échelle + ctrl_alpha, groupe trans_) ;
    #   bf<i> : bouffées des états, qui jaillissent l'une après l'autre le long de l'axe, grossissent et s'éteignent ;
    #   bfe<i> : bouffées de l'apparition (event_equip), cachées dans la buse dans les états (échelle constante K_CACHE).
    # Chaque bouffée : groupe animé (position, échelle) > groupe cam_ (face caméra) > une plaque. Plus de vapeur en particules ici.
    mz = zp + 1.32
    jg = group(f"trans_jet_{tag}", [s * 18.0, 35.6, mz], parent=el)
    nj = group(f"noyau_{tag}", [s * 18.0, 35.6, mz], parent=jg)
    ju0, jv0, ju1, jv1 = UV["jet"]
    JW, JL = 3.0, 4.8
    for i, a in enumerate((0, 60, 120)):
        # plaque dans un plan qui contient l'axe du jet ; faces up/down = l'image, la buse vers z = mz
        groups[nj]["ids"].append(cube(f"jet{i}_{tag}", [s * 18.0 - JW / 2, 35.6 - 0.15, mz + 0.05 + 0.04 * i], [s * 18.0 + JW / 2, 35.6 + 0.15, mz + 0.05 + 0.04 * i + JL],
                                      [s * 18.0, 35.6, mz], rot=(0, 0, a),
                                      faces={"up": [ju0, jv1, ju1, jv0], "down": [ju0, jv0, ju1, jv1], "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR}))
    group(f"ctrl_alpha_{tag}", [s * 18.0, 35.6, mz], parent=nj, nom="ctrl_alpha")
    zb = zp + 0.42                                    # au fond de la buse : les bouffées naissent dedans
    bfs = [bouffee(jg, f"bf{i}_{tag}", s * 18.0, 35.6, zb + 0.05 * i, 4.4, BOUFFEES[i % 3]) for i in range(NB_BF)]
    bfes = [bouffee(jg, f"bfe{i}_{tag}", s * 18.0, 35.6, zb + 0.05 * (NB_BF + i), 3.2, BOUFFEES[(i + 1) % 3]) for i in range(NB_BFE)]
    PRESS[tag] = (ag, nj, f"ctrl_alpha_{tag}", bfs, bfes)
    return rt, sh, tag


(LR_, L_, _), (RR_, R_, _) = build(-1), build(1)

for _t in "lr":
    CACHES.extend(PRESS[_t][4])

# Petite chaudière, très discrète, à la racine : un tambour plus étroit que le torse, deux évents. Pas un sac à dos.
# Sac dorsal de déploiement (event_equip) : boîtier de laiton, portes latérales à charnière arrière, deux verrous. Il n'est visible
# que pendant l'apparition. Retour en jeu du 2026-11-04 : ctrl_alpha −1 ne cache pas une partie opaque. Dans tous les états en
# boucle, le sac a donc une échelle constante K_CACHE et un recul SAC_ENFOUI (enfoui, tout petit, dans le torse) ; event_equip
# multiplie l'échelle par 1/K_CACHE et ajoute le recul inverse pendant l'apparition, puis revient à l'image neutre (1, 0).
SAC_X, SAC_Y0, SAC_Y1, SAC_Z0, SAC_Z1 = 5.7, 14.6, 24.8, 2.15, 6.6
SAC_ENFOUI = -2.6
SAC = group("sac", [0, (SAC_Y0 + SAC_Y1) / 2, SAC_Z0])       # pivot au centre de la face collée au dos : il sort du dos
_fl0, _flv0, _fl1, _flv1 = UV["fair_long"]
_bb0, _bbv0, _bb1, _bbv1 = UV["bar_brass"]
_cap = list(UV["cap_brass"])
groups[SAC]["ids"].append(cube("sac_coque", [-SAC_X + 0.45, SAC_Y0, SAC_Z0], [SAC_X - 0.45, SAC_Y1, SAC_Z1], [0, (SAC_Y0 + SAC_Y1) / 2, (SAC_Z0 + SAC_Z1) / 2],
                               faces={"south": [_fl0, _flv0, _fl1, _flv1], "north": [_fl0, _flv0, _fl1, _flv1], "up": [_bb0, _bbv0, _bb1, _bbv1],
                                      "down": [_bb0, _bbv0, _bb1, _bbv1], "east": CLEAR, "west": CLEAR}))
for _i, _y in enumerate((SAC_Y0 + 2.2, SAC_Y1 - 2.2)):
    groups[SAC]["ids"].append(cube(f"sac_cercle{_i}", [-SAC_X + 0.2, _y - 0.45, SAC_Z0 - 0.05], [SAC_X - 0.2, _y + 0.45, SAC_Z1 + 0.25], [0, _y, (SAC_Z0 + SAC_Z1) / 2],
                                   faces={"south": [_bb0, _bbv0, _bb1, _bbv1], "north": [_bb0, _bbv0, _bb1, _bbv1], "up": [_bb0, _bbv0, _bb1, _bbv1],
                                          "down": [_bb0, _bbv0, _bb1, _bbv1], "east": _cap, "west": _cap}))
PORTES = {}
for _s, _tag in ((-1, "l"), (1, "r")):
    _x = _s * (SAC_X - 0.2)
    _g = group(f"porte_{_tag}", [_x, SAC_Y0, SAC_Z1], parent=SAC)
    _fs = UV["fair_short"]
    groups[_g]["ids"].append(cube(f"porte_{_tag}", [_x - 0.2, SAC_Y0 + 0.15, SAC_Z0 + 0.1], [_x + 0.2, SAC_Y1 - 0.15, SAC_Z1 - 0.05], [_x, (SAC_Y0 + SAC_Y1) / 2, SAC_Z1],
                                  faces={"east": list(_fs), "west": list(_fs), "north": CLEAR, "south": CLEAR, "up": CLEAR, "down": CLEAR}))
    PORTES[_tag] = _g
# verrous : un loquet sur la face arrière, près du bord de chaque porte ; il pivote d'un quart de tour pour libérer la porte
VERROUS = {}
for _s, _tag in ((-1, "l"), (1, "r")):
    _x = _s * (SAC_X - 1.3)
    _g = group(f"verrou_{_tag}", [_x, (SAC_Y0 + SAC_Y1) / 2, SAC_Z1], parent=SAC)
    bar(1, _g, f"verrou_{_tag}", _x - 1.1, (SAC_Y0 + SAC_Y1) / 2, SAC_Z1 + 0.3, 2.2, 0.3, 0, "steel", octo=False)
    axle(1, _g, f"verrou_axe_{_tag}", _x, (SAC_Y0 + SAC_Y1) / 2, SAC_Z1 - 0.1, SAC_Z1 + 0.75, 0.42, "brass")
    VERROUS[_tag] = _g

CH = group("chaudiere", [0, 21.7, 3.5])
bar(1, CH, "drum", -2.2, 21.7, 3.5, 4.4, 1.22, 0, "copper")
bar(1, CH, "cerc0", -2.45, 21.7, 3.5, 0.5, 1.36, 0, "steel")
bar(1, CH, "cerc1", 1.95, 21.7, 3.5, 0.5, 1.36, 0, "steel")
for i, x in enumerate((-1.25, 1.25)):
    bar(1, CH, f"evt{i}", x, 22.7, 3.5, 1.5, 0.42, 90, "brass", octo=True)
    emit(CH, x, 24.5, 3.5)
# soupape de sûreté, sur le dessus arrière du tambour (sous la nuque) : tige, corps, clapet qui se soulève sous la pression.
# Elle lâche la vapeur en particules (point emit) et, pendant l'apparition, deux ou trois petites fuites modélisées (fu<i>).
SP = (0.0, 4.3)                                   # x, z de la soupape
bar(1, CH, "soup_tige", SP[0], 22.0, SP[1], 1.0, 0.27, 90, "steel")
bar(1, CH, "soup_corps", SP[0], 22.85, SP[1], 0.75, 0.52, 90, "brass")
CLAPET = group("clapet", [SP[0], 23.6, SP[1]], parent=CH)
bar(1, CLAPET, "soup_clapet", SP[0], 23.62, SP[1], 0.28, 0.62, 90, "copper", octo=False)
emit(CH, SP[0], 24.15, SP[1])
FUITE = group("trans_fuite", [SP[0], 23.2, SP[1]], parent=CH)
FUITES = [bouffee(FUITE, f"fu{i}", SP[0], 23.1 + 0.05 * i, SP[1] + 0.04 * i, 2.0, BOUFFEES[i % 3]) for i in range(3)]
CACHES.extend(FUITES)
_fu0, _fv0, _fu1, _fv1 = UV["foyer"]
groups[CH]["ids"].append(cube("foyer", [-0.65, 20.95, 4.68], [0.65, 21.75, 4.92], [0, 21.35, 4.8],
                              faces={"south": [_fu0, _fv0, _fu1, _fv1], "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}))



def bone(name):
    g = groups[name]
    return {"name": g["nom"], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(),
             "children": [{"name": "item", "origin": [0, 0, 0], "uuid": nuid(),
                           "children": [bone(CH), bone(SAC), bone(LR_), bone(RR_), bone(L_), bone(R_)]}]},
]

# ------------------------------------------------------------------ animations
# Les courbes décrivent l'aile GAUCHE en termes d'intention :
#   fx > 0 : le plan bascule vers l'horizontale ; fy > 0 : pivote vers l'arrière ; fz > 0 : la pointe monte.
#   fold : 0 = éventail grand ouvert (pose du modèle), 1 = fermé. curl : les bouts de lames se creusent.

# MIROIR D'AXES : seul endroit à toucher si la convention du mod change (un signe suffit).
# Repères de docs/guide-cosmetiques.md, section 3.
SX, SY, SZ = -1, -1, +1


def mirror(s, fx, fy, fz):
    """s = -1 aile gauche, +1 aile droite. Renvoie les valeurs de keyframe."""
    return SX * fx, s * SY * fy, s * SZ * fz


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 2)), "y": str(round(y + 0.0, 2)), "z": str(round(z + 0.0, 2))}],
            "time": round(t, 3), "interpolation": "linear"}


def mech(x, h=1.9):
    """Sinus durci : tient aux extrêmes, passe vite entre les deux. Mouvement de machine, mais sans angle droit."""
    return math.tanh(h * x) / math.tanh(h)


def palier(t, L, k, tau=0.075, w=2 * math.pi / 0.30):
    """Temps mécanique : k crans par boucle de durée L. Chaque cran part sec, dépasse un peu (réponse d'un servo
    sous-amorti, ~13 %), se stabilise et tient jusqu'au cran suivant. palier(0) = 0 et palier(L) = L : boucle fermée.
    Non borné : t au-delà de L continue (engrenages qui tournent plusieurs tours)."""
    if not k:
        return t
    x = t * k / L
    i = math.floor(x + 1e-9)
    u = x - i

    def e(v):
        return 1 - math.exp(-v / tau) * (math.cos(w * v) + math.sin(w * v) / (w * tau))
    return (i + e(u) + (1 - e(1.0)) * u) * L / k


def S(T, amp, ph=0.0, off=0.0):
    return lambda t: off + amp * mech(math.sin(TAU * t / T + math.radians(ph)))


def C(v):
    return lambda t: v


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


GEAR_PARTS = [("gear_ea", 1), ("gear_ep", -2), ("gear_wa", -1), ("gear_wp", 2)]    # sens et rapport (pignon deux fois plus rapide)


def add_gears(a, turns, ticks=0, n=None):
    """turns : tours du grand engrenage par boucle, entier. Même sens dans tous les états. ticks : crans par boucle (dent par dent)."""
    L = a["length"]
    n = n or 2
    times = [i * L / n for i in range(n + 1)] if ticks else [0, L]
    for s, tag in ((-1, "l"), (1, "r")):
        for name, ratio in GEAR_PARTS:
            v = 360.0 * turns * ratio
            g = f"{name}_{tag}"
            a["animators"][groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf("rotation", t, *mirror(s, 0, 0, v * palier(t, L, ticks) / L)) for t in times]}


def add_verin(a, elbow, n, W=lambda t: t):
    """Le cylindre suit le tenon de l'avant-bras, la tige coulisse : la liaison reste fermée dans tous les états."""
    L = a["length"]
    times = [i * L / n for i in range(n + 1)]
    for s, tag in ((-1, "l"), (1, "r")):
        y0, z0, L0 = VREST[tag]
        kc, kt = [], []
        for t in times:
            ex, ey, ez = mirror(s, *(f(W(t)) for f in elbow))
            y, z, ln = verin_aim(s, (ex, -s * YAW[1] + ey, ez))
            assert 0.2 < ROD_IN + ln - L0 < CYL - 0.3, f"tige hors du cylindre : {ln - L0:.2f}"
            kc.append(kf("rotation", t, 0, y - y0, z - z0))
            kt.append(kf("position", t, s * (ln - L0), 0, 0))
        a["animators"][groups[f"verin_{tag}"]["uuid"]] = {"name": f"verin_{tag}", "type": "bone", "keyframes": kc}
        a["animators"][groups[f"tige_{tag}"]["uuid"]] = {"name": f"tige_{tag}", "type": "bone", "keyframes": kt}


def cacher(A_):
    """Dans chaque état en boucle (et glide) : pièces de l'apparition cachées par une échelle constante, que event_equip multiplie.
    Le sac est en plus enfoui dans le torse (recul constant, qu'event_equip annule en l'ajoutant à l'envers)."""
    A_[groups[SAC]["uuid"]] = {"name": SAC, "type": "bone", "keyframes": [kf("scale", 0, K_CACHE, K_CACHE, K_CACHE), kf("position", 0, 0, 0, SAC_ENFOUI)]}
    for g in CACHES:
        A_[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf("scale", 0, K_CACHE, K_CACHE, K_CACHE)]}


def anim(name, length, segs, fold, curl=C(0), n_kf=None, loop="loop", only=None, turns=None, ticks=0, press=None):
    """segs : shoulder/elbow/wrist -> (fx, fy, fz). only : familles animées (attaque et blessé, joués une fois par-dessus l'état).
    ticks : crans par boucle (mouvement mécanique, voir palier) ; press : instants de décharge (voir add_pression)."""
    A_ = {}
    W = (lambda t: palier(t, length, ticks)) if ticks else (lambda t: t)

    def put(g, kfs):
        if only is None or re.sub(r"\d*_[lr]$", "", g) in only:
            A_[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}

    n = max(n_kf or max(6, int(round(length * 8))), ticks * 7)
    times = [i * length / n for i in range(n + 1)]   # interpolation linéaire : dernier keyframe = premier
    for s, tag in ((-1, "l"), (1, "r")):
        for seg, (fx, fy, fz) in segs.items():
            put(f"{seg}_{tag}", [kf("rotation", t, *mirror(s, fx(W(t)), fy(W(t)), fz(W(t)))) for t in times])
        for k in range(NR):
            # décalage de phase d'une lame à l'autre : le mécanisme se referme de proche en proche
            dl = 0.012 * length * (NR - 1 - k)
            # décalage de phase d'une lame à l'autre, appliqué avant les crans : elles avancent l'une après l'autre
            put(f"ray{k}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, -CLOSE[k] * fold(W((t - dl) % length) if loop == "loop" else max(0.0, t - dl)))) for t in times])
            put(f"ray{k}b_{tag}", [kf("rotation", t, *mirror(s, 0, 0, -CURLW[k] * curl(W(t)))) for t in times])
        for j in range(len(SECS)):
            put(f"sec{j + 1}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, (10 - 2.5 * j) * fold(W(t)))) for t in times])
        for j in range(len(TERS)):
            put(f"ter{j + 1}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, (2 + 2 * j) * fold(W(t)))) for t in times])
        put(f"thumb_{tag}", [kf("rotation", t, *mirror(s, 0, 0, 26 * max(0.0, fold(W(t))))) for t in times])
    if loop == "loop":
        cacher(A_)
    a = {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
         "selected": name == "idle", "animators": A_}
    if turns:
        add_gears(a, turns, ticks * 2, n)
        add_verin(a, segs["elbow"], n, W)
    if press is not None:
        add_pression(a, press, n)
    return a


BF_DEPART = [0.03 + 0.075 * i for i in range(NB_BF)]      # instant de départ de chaque bouffée après la décharge (s)
BF_VIE = [0.50 + 0.05 * i for i in range(NB_BF)]          # durée de vie (s)
BF_LOIN = 10.0                                              # distance parcourue par la première bouffée (px), le long du jet


def bouffee_profil(d, i, f=1.0, force=1.0):
    """(échelle, montée y, avance z) de la bouffée i, d secondes après la décharge. Elle part vite (pression), ralentit,
    grossit en s'éloignant puis s'éteint (échelle vers 0) ; chaque bouffée est un peu moins forte que la précédente."""
    u = (d - BF_DEPART[i] * f) / (BF_VIE[i] * f)
    if u < 0 or u > 1:
        return 0.0, 0.0, 0.0
    w = (1 - 0.1 * i) * force
    return (w * (0.3 + 1.6 * u) * (1 - sm(u, 0.55, 1.0)), 1.1 * u * u, BF_LOIN * w * (1 - (1 - u) ** 2.2))


def add_pression(a, rel, n, charge=1.0):
    """Cycle de pression. rel : instants de décharge dans la boucle (liste vide : pas de décharge, aiguille basse).
    Entre deux décharges l'aiguille grimpe par crans jusqu'à charge (0..1) et tremble au maximum ; à la décharge elle retombe
    avec un rebond, le jet jaillit (trans_jet : scale 0 -> 1 en 0,08 s, s'étire, se résorbe en 0,75 s) et siffle."""
    L = a["length"]
    extra = {round((r + d) % L, 4) for r in rel for d in (0, 0.04, 0.08, 0.12, 0.2, 0.3, 0.45, 0.6, 0.75)}
    times = sorted({round(i * L / n, 4) for i in range(n + 1)} | extra)

    def depuis(t):
        return min(((t - r) % L) for r in rel) if rel else None

    def needle(t):
        d = depuis(t)
        if d is None:
            return 0.12 * charge
        if d < 0.35:
            return charge * (1 - sm(d, 0.0, 0.22)) + 0.06 * math.sin(TAU * d / 0.12) * (1 - sm(d, 0.1, 0.35))
        per = L / len(rel)
        c = (d - 0.35) / max(per - 0.35, 1e-6)
        k = max(3, int(round(per / 0.4)))
        return charge * min(palier(c, 1.0, k), 1.0) + 0.035 * math.sin(TAU * d / 0.07) * sm(c, 0.82, 1.0)

    def jet(t):
        """Noyau : jet dense et court, à pleine force dès 0,05 s, qui faiblit pendant que les bouffées partent."""
        d = depuis(t)
        if d is None or d > 0.6:
            return 0.0, 0.0
        on = sm(d, 0.0, 0.05) * (1 - sm(d, 0.22, 0.5))
        return on, on * (1 + 0.3 * sm(d, 0.05, 0.3))

    def alpha_x(t):
        """ctrl_alpha du noyau (groupe trans_, vrai fondu) : 1 + x = opacité ; 0 = normal, −1 = invisible (guide 4 bis)."""
        d = depuis(t)
        return 0.0 if d is None else -sm(d, 0.25, 0.5)

    per = L / len(rel) if rel else L
    f = min(1.0, (per - 0.05) / (BF_DEPART[-1] + BF_VIE[-1] + 0.02))     # boucles courtes (course) : bouffées plus brèves
    for s, tag in ((-1, "l"), (1, "r")):
        ag, nj, ca, bfs, _ = PRESS[tag]
        put = lambda g, kfs: a["animators"].__setitem__(groups[g]["uuid"], {"name": groups[g]["nom"], "type": "bone", "keyframes": kfs})
        put(ag, [kf("rotation", t, *mirror(s, 0, 0, 120 - 240 * needle(t))) for t in times])
        put(nj, [kf("scale", t, jet(t)[0], jet(t)[0], jet(t)[1]) for t in times])
        put(ca, [kf("position", t, alpha_x(t), 0, 0) for t in times])
        for i, g in enumerate(bfs):
            li, Ti = BF_DEPART[i] * f, BF_VIE[i] * f
            ts = set(times)
            for r in rel:
                ts |= {round((r + li + Ti * j / 8) % L, 4) for j in range(9)} | {round((r + li - 0.005) % L, 4), round((r + li + Ti + 0.005) % L, 4)}
            ts = sorted(ts)

            def val(t):
                d = depuis(t)
                return (0.0, 0.0, 0.0) if d is None else bouffee_profil(d, i, f)
            ecart = s * 0.7 * (1 if i % 2 else -1) / BF_LOIN          # écart latéral alterné, proportionnel à l'avance
            put(g, [kf("scale", t, *[val(t)[0]] * 3) for t in ts] + [kf("position", t, ecart * val(t)[2], val(t)[1], val(t)[2]) for t in ts])
    if rel:
        # sifflement de vapeur à chaque décharge (guide 6.5)
        a["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
            {"channel": "sound", "data_points": [{"effect": "block.fire.extinguish", "file": ""}], "time": round(r % L, 3)} for r in rel]}


Z0 = C(0)

# idle 8 s : repos, demi-fermé ; respiration (4 s) + étirement ample 4,6–7,2 s. Engrenage : 1 tour en 8 s (45°/s).
st = lambda t: bump(t, 4.6, 5.3, 6.1, 7.2)
mix = lambda f, v: (lambda t: f(t) * (1 - st(t)) + v * st(t))
idle = anim("idle", 8.0, {
    "shoulder": (mix(S(4, 1.0, 0, 6), 15), mix(S(4, 1.5, 0, 14), -6), mix(S(4, 2, 0, 2), 7)),
    "elbow":    (Z0, mix(S(4, 1, -40, -6), -4), mix(S(4, 1.5, -40, -3), 4)),
    "wrist":    (Z0, mix(S(4, 0.8, -70, 8), -6), mix(S(4, 1, -70, -6), 3))},
    fold=lambda t: (0.22 + 0.05 * math.sin(TAU * t / 4)) * (1 - st(t)), curl=lambda t: (4 + 1.5 * math.sin(TAU * t / 4)) * (1 - st(t)), n_kf=48, turns=1,
    ticks=16, press=[4.5])

# fly 2,4 s : joueur debout en vol créatif. Plan basculé d'environ 40° (jamais 90°), battement ample. Engrenage : 300°/s.
T = 2.4
FLY = 3 * T
up = lambda t, lag=0.0: 0.5 + 0.5 * mech(math.cos(TAU * (t / T - lag)), 1.4)
boost3 = lambda t: 1 + 0.32 * bump(t, 4.7, 4.95, 5.8, 6.7)
fly = anim("fly", FLY, {
    "shoulder": (S(T, 4, 90, 40), S(T, 5, 90, -13), lambda t: S(T, 22, 0, 0)(t) * boost3(t)),
    "elbow":    (Z0, lambda t: 8 - 3 * up(t, 0.12), S(T, 8, -45, -2)),
    "wrist":    (Z0, lambda t: -8 + 3 * up(t, 0.22), lambda t: 2 + 5 * math.sin(TAU * t / T - math.radians(75)) - 15 * up(t, 0.22))},
    fold=lambda t: 0.02 + 0.40 * up(t, 0.2), curl=lambda t: 2 + 11 * up(t, 0.26), n_kf=24, turns=6, ticks=24, press=[4.8])

# glide 3,6 s : joueur couché, le cosmétique suit le torse : presque dans le plan du dos, grand ouvert, X faible.
# Battement lent hors du plan par Y, battement à la fusée (mêmes forme et constantes que les modèles validés en jeu).
G = 3.6
BOOST = f"math.clamp((math.max(q.ground_speed,q.vertical_speed)-{V0})/{DV},0,1)*math.clamp((q.vertical_speed+8)/4,0,1)"


def term(amp, speed, ph):
    """Texte Molang de amp*sin(speed*t + ph), signe compris ; amp = 0 : vide."""
    if not amp:
        return ""
    p = f"{ph:+g}" if ph else ""
    return f"{amp:+g}*math.sin(q.anim_time*{speed}{p})"


def mol(sign, base, slow=(0, 0), boost=(0, 0)):
    """base + slow[0]*sin(100t+slow[1]) + boost[0]*A*sin(600t+boost[1]), multiplié par sign (miroir). Courte, sans ? ni &&."""
    e = f"{sign * base:g}" + term(sign * slow[0], 100, slow[1])
    if boost[0]:
        e += f"{sign * boost[0]:+g}*{BOOST}*math.sin(q.anim_time*600{boost[1]:+g})"
    assert len(e) <= 256
    return e


def mkf(x, y, z):
    return {"channel": "rotation", "data_points": [{"x": x, "y": y, "z": z}], "time": 0, "interpolation": "linear"}


def glide_anim():
    A_ = {}

    def put(g, x, y, z):
        A_[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [mkf(x, y, z)]}

    for s_, tag in ((-1, "l"), (1, "r")):
        sx, sy, sz = mirror(s_, 1, 1, 1)      # le signe reste centralisé dans mirror()
        put(f"shoulder_{tag}", mol(sx, 8, (1.5, 90)), mol(sy, -14, (11, 0), (24, 0)), f"{sz * -4:g}")
        put(f"elbow_{tag}", "0", mol(sy, 8, (-3, -43), (11, -45)), f"{sz * 1:g}")
        put(f"wrist_{tag}", "0", mol(sy, -8, (4, -79), (13, -90)), f"{sz * 2:g}")
        for k in range(NR):
            c = CLOSE[k]
            put(f"ray{k}_{tag}", "0", "0", mol(sz, round(-c * 0.12, 2), (round(c * 0.05, 2), 90), (round(c * 0.07, 2), -90)))
            put(f"ray{k}b_{tag}", "0", "0", mol(sz, round(-3 * CURLW[k], 2), (round(1.5 * CURLW[k], 2), 60), (round(-5 * CURLW[k], 2), -120)))
    cacher(A_)
    a = {"uuid": nuid(), "name": "glide", "loop": "loop", "override": False, "length": G, "snapping": 24, "selected": False, "animators": A_}
    add_gears(a, 2, 12, 72)
    add_verin(a, (Z0, lambda t: 8 - 3 * math.sin(math.radians(t * 100 - 43)), C(1)), 18)   # tige calée sur le battement lent ; hors fusée
    # pression = fusée : l'aiguille monte avec la vitesse, les jets s'ouvrent et la vapeur sort en continu
    # bouffées à la fusée : elles défilent le long du jet (math.mod), 2,5 par seconde et par bouffée, décalées d'un cinquième :
    # 9 cycles exacts en 3,6 s, boucle fermée. Elles grossissent puis s'éteignent (sin de 0 à 180°), cachées sans fusée.
    for s_, tag in ((-1, "l"), (1, "r")):
        ag, nj, ca, bfs, _ = PRESS[tag]
        sz = mirror(s_, 1, 1, 1)[2]
        A_[groups[ag]["uuid"]] = {"name": ag, "type": "bone", "keyframes": [mkf("0", "0", f"{sz:g}*(108-216*{BOOST})")]}
        A_[groups[nj]["uuid"]] = {"name": nj, "type": "bone", "keyframes": [{"channel": "scale", "data_points": [{"x": BOOST, "y": BOOST, "z": f"1.3*{BOOST}"}], "time": 0, "interpolation": "linear"}]}
        for i, g in enumerate(bfs):
            # vie de 0 à 0,9 (P) ; de 0,9 à 1 la bouffée, éteinte, revient à la buse : position continue, boucle fermée
            P = f"math.mod(q.anim_time*2.5+{i / NB_BF:g},1)"
            sc = f"{BOOST}*math.max(0,math.sin({P}*200))*(0.5+{P})"
            ret = f"math.min((1-{P})*10,1)"
            pz = f"{BF_LOIN:g}*math.sin(math.min({P}/0.9,1)*90)*{ret}"
            py = f"1.1*{P}*{P}*{ret}"
            assert max(map(len, (sc, pz, py))) <= 256, (len(sc), len(pz))
            A_[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [
                {"channel": "scale", "data_points": [{"x": sc, "y": sc, "z": sc}], "time": 0, "interpolation": "linear"},
                {"channel": "position", "data_points": [{"x": "0", "y": py, "z": pz}], "time": 0, "interpolation": "linear"}]}
    return a


glide = glide_anim()

# fall 1,5 s : joueur debout, ailes relevées et ouvertes, plan peu basculé (freinage). Engrenage : 240°/s.
AI = 1.5
fall = anim("fall", AI, {"shoulder": (S(AI, 3, 0, 26), C(-4), S(AI, 3, 0, 6)),
                         "elbow": (Z0, C(3), S(AI, 3, -40, 5)),
                         "wrist": (Z0, C(-4), S(AI, 2, -70, 2))},
            fold=S(AI, 0.05, 0, 0.09), curl=S(AI, 3, -60, 8), turns=1, ticks=6, press=[0.2])

# walk 1,6 s : ramenées vers l'arrière, à moitié fermées, balancement au pas. Engrenage : 225°/s.
WK = 1.6
walk = anim("walk", 2 * WK, {"shoulder": (C(8), S(WK, 5, 0, 30), S(WK, 3.5, 0, -8)),
                         "elbow": (Z0, S(WK, 3, -40, -10), S(WK, 2, -40, -4)),
                         "wrist": (Z0, S(WK, 3, -70, 14), S(WK, 2.5, -70, -22))},
            fold=C(0.55), curl=S(WK, 2, -70, 6), turns=2, ticks=8, press=[1.6])

# run 1,0 s : très vers l'arrière, abaissées, repli en S réparti sur les 3 articulations, éventail presque fermé. 360°/s.
RN = 1.0
run = anim("run", RN, {"shoulder": (C(16), S(RN, 3, 0, 50), S(RN, 3, 0, -14)),
                       "elbow": (Z0, S(RN, 2, -40, -28), S(RN, 1.5, -40, -5)),
                       "wrist": (Z0, S(RN, 3, -80, 34), S(RN, 2, -80, -28))},
           fold=C(0.8), curl=S(RN, 2, -60, 8), turns=1, ticks=4, press=[0.5])

# sneak 4 s : éventail fermé, plis serrés dans le dos, éperon qui dépasse au-dessus de l'épaule. Engrenage : 90°/s.
SN = 4.0
sneak = anim("sneak", SN, {"shoulder": (C(7), S(SN, 1, 0, 10), S(SN, 1, 0, 8)),
                           "elbow": (Z0, C(-15), S(SN, 1, -40, 0)),
                           "wrist": (Z0, C(5), C(-34))},
             fold=S(SN, 0.015, 0, 0.985), curl=C(9), turns=1, ticks=8, press=[])

# sleep 8 s : repliées, tombantes, engrenage au ralenti (45°/s, comme au repos)
SL = 8.0
sleep = anim("sleep", SL, {"shoulder": (C(12), S(SL, 1, 0, 12), S(SL, 1, 0, 2)),
                           "elbow": (Z0, C(-14), C(-4)),
                           "wrist": (Z0, C(6), C(-30))},
             fold=C(1.0), curl=S(SL, 1, -60, 10), turns=1, ticks=8, press=[])

# swim 2 s : joueur couché. Dans le plan du dos, rabattues vers les pieds, à demi fermées ; ondulation par Y. Engrenage : 180°/s.
SW = 2.0
swim = anim("swim", SW, {"shoulder": (C(7), S(SW, 7, 0, 2), C(-34)),
                         "elbow": (Z0, S(SW, 6, -45, 6), C(-10)),
                         "wrist": (Z0, S(SW, 7, -90, -4), C(-10))},
            fold=C(0.65), curl=S(SW, 4, -120, 6), turns=1, ticks=6, press=[])

# mount 3 s : repos relevé, pointes hautes, respiration ample. Engrenage : 120°/s.
MT = 3.0
mount = anim("mount", MT, {"shoulder": (C(10), S(MT, 2.5, 0, 8), S(MT, 3.5, 0, 12)),
                           "elbow": (Z0, S(MT, 1.5, -40, -4), S(MT, 2, -40, 5)),
                           "wrist": (Z0, C(2), S(MT, 2, -70, -2))},
             fold=S(MT, 0.04, 0, 0.26), curl=S(MT, 1.5, -40, 4), turns=1, ticks=6, press=[])

# attack et hurt : une fois par-dessus l'état, dernière image neutre, seuls les groupes concernés (ni engrenages ni vérin).
IMPULSE = {"shoulder", "elbow", "wrist", "ray", "thumb"}
AT = 0.8
atk = lambda t: bump(t, 0.0, 0.10, 0.30, 0.72)
attack = anim("attack", AT, {"shoulder": (lambda t: 24 * atk(t), lambda t: -12 * atk(t), lambda t: 8 * atk(t)),
                             "elbow": (Z0, lambda t: -6 * atk(t), lambda t: 5 * atk(t)),
                             "wrist": (Z0, lambda t: -8 * atk(t), lambda t: 6 * atk(t))},
              fold=lambda t: -0.08 * atk(t), n_kf=16, loop="once", only=IMPULSE, ticks=4)

HU = 0.8
hu = lambda t: bump(t, 0.0, 0.06, 0.22, 0.72)
tr = lambda t: 3 * math.sin(TAU * t * 5 / HU) * (1 - sm(t, 0.25, 0.7))
hurt = anim("hurt", HU, {"shoulder": (lambda t: 6 * hu(t), lambda t: 16 * hu(t), lambda t: 8 * hu(t) + tr(t)),
                         "elbow": (Z0, lambda t: -6 * hu(t), lambda t: -3 * hu(t) + tr(t)),
                         "wrist": (Z0, lambda t: 8 * hu(t), lambda t: -3 * hu(t) + tr(t))},
            fold=lambda t: 0.25 * hu(t), n_kf=16, loop="once", only=IMPULSE)


def equip_anim():
    """event_equip (guide 6.4), joué une fois par-dessus l'état quand les ailes apparaissent. Rotations et positions s'ajoutent à
    l'état, échelles multipliées ; dernière image neutre (échelle 1, rotations et positions 0). Séquence de machine (4,8 s) :
      0,00–0,50  le sac sort du dos (échelle K_CACHE -> 1, il quitte le torse), en deux crans ;
      0,50–1,30  la pression monte : aiguilles des manomètres par crans ; 0,92–1,62 le clapet de la soupape tremble et fuit ;
      1,28–1,46  les deux verrous claquent (quart de tour, dépassement) ;
      1,45–2,00  sifflement (seul son) : les portes s'ouvrent en trois crans, la pression retombe un peu ;
      2,00–2,45  les ailes sortent, repliées, en trois crans (échelle multipliée 0,015 -> 1) ;
      2,45–3,53  dépliage par étapes : humérus, coude, poignet, puis l'éventail lame par lame au cliquet (dépassement et rappel) ;
      2,00–3,85  la pression remonte jusqu'au maximum ;
      3,45–4,35  les engrenages s'emballent (deux tours) puis se calent avec un rebond ; 3,55–4,17 battement d'essai ;
      3,95–4,60  décharge : bouffées de vapeur aux tuyères, les aiguilles retombent ;
      4,15–4,55  les portes se referment en deux crans, les verrous se reverrouillent ;
      4,45–4,75  le sac rentre dans le dos ; 4,80 image neutre."""
    L = 4.8
    n = int(L * 25)
    ts = {round(i * L / n, 4) for i in range(n + 1)} | {round(L - 0.05, 4), round(L - 0.001, 4)}
    A_ = {}

    def put(key, kfs):
        A_[groups[key]["uuid"]] = {"name": groups[key]["nom"], "type": "bone", "keyframes": kfs}

    def crans(t, a, b, k):
        """Progression de a à b en k crans mécaniques (palier : départ sec, dépassement, arrêt), 0 avant, 1 après."""
        if t <= a:
            return 0.0
        if t >= b:
            return 1.0
        return palier((t - a) / (b - a), 1.0, k)

    # ---- bouffées de l'apparition, cachées dans les états par l'échelle K_CACHE (dans la buse, dans la soupape)
    def bouffees_evt(groupes, departs, vies, profils):
        res = []
        for g, t0, vie, profil in zip(groupes, departs, vies, profils):
            ts.update({round(t0 - 0.005, 4), round(t0 + vie + 0.005, 4)} | {round(t0 + vie * j / 9, 4) for j in range(10)})

            def val(t, t0=t0, vie=vie, profil=profil):
                """(échelle de l'événement, position) ; échelle totale = K_CACHE × valeur."""
                if t < t0:
                    return 1.0, (0, 0, 0)
                if t <= t0 + vie:
                    sc, pos = profil(min(1.0, max(0.0, (t - t0) / vie)))
                    return sc / K_CACHE, pos
                if t < L - 0.05:
                    return 0.0, (0, 0, 0)
                return sm(t, L - 0.05, L), (0, 0, 0)
            res.append((g, val))
        return res

    def profil_fuite(u):
        """Petite fuite à la soupape : elle monte (+Y) et recule un peu."""
        return 0.9 * (0.35 + 1.1 * u) * (1 - sm(u, 0.5, 1.0)), (0, 3.2 * (1 - (1 - u) ** 1.8), 0.9 * u)

    def profil_tuyere(i):
        def f(u):
            sc, y, z = bouffee_profil(BF_DEPART[i] + u * BF_VIE[i], i, 1.0, 0.95)
            sc *= 4.4 / 3.2                     # plaque de 3,2 px (cachée dans la buse), même taille finale que bf<i>
            return sc, (0, y, z)
        return f

    T_DECH = 3.95
    evt = bouffees_evt(FUITES, (0.98, 1.2, 1.46), (0.6, 0.6, 0.7), [profil_fuite] * 3)
    for tag in "lr":
        bfes = PRESS[tag][4]
        evt += bouffees_evt(bfes, [T_DECH + BF_DEPART[i] for i in range(len(bfes))], [BF_VIE[i] for i in range(len(bfes))],
                            [profil_tuyere(i) for i in range(len(bfes))])
    times = sorted(t for t in ts if 0 <= t <= L)

    for g, val in evt:
        put(g, [kf("scale", t, *[val(t)[0]] * 3) for t in times] + [kf("position", t, *val(t)[1]) for t in times])

    # ---- sac : sort du dos, puis y rentre ; échelle totale K_CACHE × valeur, recul total SAC_ENFOUI + position
    em = lambda t: crans(t, 0.0, 0.5, 2) * (1 - crans(t, 4.45, 4.75, 2))
    put(SAC, [kf("scale", t, *[(K_CACHE + (1 - K_CACHE) * em(t)) / K_CACHE] * 3) for t in times]
        + [kf("position", t, 0, 0, -SAC_ENFOUI * em(t)) for t in times])
    for k, (tag, sg) in enumerate((("l", -1), ("r", 1))):
        verrou = lambda t: 90 * (crans(t, 1.28 + 0.06 * k, 1.40 + 0.06 * k, 1) - crans(t, 4.45 + 0.04 * k, 4.55 + 0.04 * k, 1))
        put(VERROUS[tag], [kf("rotation", t, 0, 0, sg * verrou(t)) for t in times])
        porte = lambda t: 100 * crans(t, 1.45, 2.0, 3) * (1 - crans(t, 4.15, 4.45, 2))
        put(PORTES[tag], [kf("rotation", t, 0, sg * porte(t), 0) for t in times])

    # ---- pression : l'aiguille monte par crans, tremble, retombe un peu à l'ouverture, remonte au maximum, décharge
    def pression(t):
        p = crans(t, 0.5, 1.3, 5) * (1 - 0.3 * crans(t, 1.45, 1.62, 1)) + 0.3 * crans(t, 2.0, 3.85, 6)
        p += 0.04 * math.sin(TAU * t / 0.07) * (bump(t, 1.1, 1.2, 1.4, 1.5) + bump(t, 3.6, 3.7, 3.88, 3.95))
        return p * (1 - crans(t, T_DECH, 4.3, 1))
    put(CLAPET, [kf("position", t, 0, 0.22 * bump(t, 0.92, 0.98, 1.5, 1.62) + 0.05 * math.sin(TAU * t / 0.06) * bump(t, 0.9, 1.0, 1.4, 1.55), 0)
                 for t in times])

    # ---- engrenages : s'emballent (deux tours, départ lent, accélération), se calent avec un rebond amorti ; image finale à 0
    def spin(t):
        u = min(max((t - 3.45) / 0.75, 0.0), 1.0)
        g = u * u * u * (10 - 15 * u + 6 * u * u)
        if t > 4.2:
            g += 0.03 * math.sin(TAU * (t - 4.2) / 0.12) * math.exp(-(t - 4.2) / 0.06)
        return g

    out = lambda t: 0.015 + 0.985 * crans(t, 2.0, 2.45, 3)          # les ailes sortent du sac (échelle multipliée)
    h = lambda t: crans(t, 2.45, 2.80, 1)                            # humérus
    c = lambda t: crans(t, 2.70, 3.00, 1)                            # coude
    w = lambda t: crans(t, 2.85, 3.15, 1)                            # poignet
    lame = lambda t, k: crans(t, 3.0 + 0.05 * k, 3.13 + 0.05 * k, 1)   # éventail, lame par lame au cliquet

    def flap(t, lag=0.0):
        """Battement d'essai : descente puis remontée, amorti, 0 aux deux bouts."""
        u = (t - 3.55 - lag) / 0.5
        return 0.0 if u <= 0 or u >= 1 else -16 * math.sin(TAU * u) * (1 - u) ** 0.5

    for tag, sg in (("l", -1), ("r", 1)):
        ag = PRESS[tag][0]
        put(ag, [kf("rotation", t, *mirror(sg, 0, 0, -150 * pression(t))) for t in times])
        put(f"shoulder_{tag}", [kf("rotation", t, *mirror(sg, 0, 28 * (1 - h(t)), -24 * (1 - h(t)) + flap(t))) for t in times]
            + [kf("scale", t, *[out(t)] * 3) for t in times])
        put(f"elbow_{tag}", [kf("rotation", t, *mirror(sg, 0, -18 * (1 - c(t)), 10 * (1 - c(t)) + 0.45 * flap(t, 0.06))) for t in times])
        put(f"wrist_{tag}", [kf("rotation", t, *mirror(sg, 0, 16 * (1 - w(t)), -26 * (1 - w(t)) + 0.5 * flap(t, 0.12))) for t in times])
        put(f"thumb_{tag}", [kf("rotation", t, *mirror(sg, 0, 0, 26 * (1 - w(t)))) for t in times])
        for k in range(NR):
            put(f"ray{k}_{tag}", [kf("rotation", t, *mirror(sg, 0, 0, -CLOSE[k] * (1 - lame(t, k)))) for t in times])
        for j in range(len(SECS)):
            put(f"sec{j + 1}_{tag}", [kf("rotation", t, *mirror(sg, 0, 0, (10 - 2.5 * j) * (1 - c(t)))) for t in times])
        for j in range(len(TERS)):
            put(f"ter{j + 1}_{tag}", [kf("rotation", t, *mirror(sg, 0, 0, (2 + 2 * j) * (1 - h(t)))) for t in times])
        for name, ratio in GEAR_PARTS:
            g = f"{name}_{tag}"
            # 720° × rapport = tours entiers : la dernière clé repasse à 0 sans que la dent change de place
            put(g, [kf("rotation", t, *mirror(sg, 0, 0, 0 if t >= L else 720 * ratio * spin(t))) for t in times])
    # un seul son (tools/sons.py) : le sifflement quand les verrous lâchent et que les portes s'ouvrent
    A_["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
        {"channel": "sound", "data_points": [{"effect": "block.fire.extinguish", "file": ""}], "time": 1.45}]}
    return {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": L, "snapping": 24, "selected": False, "animators": A_}


equip = equip_anim()
ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, attack, hurt, equip]
assert len(EMITS) == 3 and len(ANIMS) <= 16
assert 200 <= len(elements) <= 450, f"budget : {len(elements)} cubes"

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
textures.append({"name": f"{NOM}_r.png", "uv_width": TEX, "uv_height": TEX, "source": tex_r_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
# Sons rares : aucun en mouvement, un au plus au repos (boucle ≥ 8 s), à l'attaque et à la blessure (retour de l'utilisateur).
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
# Particules Minecraft mal placées en jeu (bug du mod, 2026-11-04) : remplacées par une vapeur modélisée.
from particules import remplacer_emit_mc
remplacer_emit_mc(model, {"white_smoke": "vapeur"})
from sons import limiter_sons
limiter_sons(model)
# Ambiance : métal mouillé sous la pluie, lumière plus forte la nuit et sous la pluie, éclats sur les arêtes polies.
from ambiance import ajouter_ambiance
ajouter_ambiance(model)
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))
with open(OUT) as fh:
    json.load(fh)


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 2, "groupes ; profondeur", depth(outliner[0]), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      f"{len(EMITS)} emit_")
