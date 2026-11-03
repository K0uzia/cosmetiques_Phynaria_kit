"""Ailes mécaniques — ailes à vapeur articulées (laiton patiné, cuivre, acier sombre, vert-de-gris). Design original.
Écrit ailes_mecaniques.png, ailes_mecaniques_e.png et .build/ailes_mecaniques_brut.bbmodel à côté de ce script.

Squelette et orientations d'états repris de gen_ailes_abyssales.py : humérus > avant-bras > poignet > éventail.
Longerons : vrais volumes octogonaux. Éventail : 9 lames à deux sections (base + bout) qui pivotent toutes autour du
poignet, donc se referment sans ouvrir de trou. Chaque section = plaque découpée par alpha + âme pleine plus étroite.
Engrenages coude et poignet : disque par alpha + axe en volume, chacun dans son sous-groupe, 360° x k exact par boucle.
Vérin de l'humérus : le cylindre vise un tenon de l'avant-bras (cinématique calculée) et la tige coulisse (position).
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
    return finish(col, mask)


TILES["sector"] = paint_sector(112, 42, -96)


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


def paint_cloud(n):
    """Nuage de vapeur : une image, plate, bouffées à bords nets, ombre douce peinte en deux tons."""
    ss = 4
    N = n * ss
    puffs = [(0.50, 0.42, 0.24), (0.30, 0.52, 0.18), (0.70, 0.54, 0.18), (0.42, 0.66, 0.17), (0.61, 0.70, 0.15), (0.19, 0.64, 0.10), (0.82, 0.68, 0.09)]
    yy, xx = np.mgrid[0:N, 0:N]
    u, v = (xx + 0.5) / N, (yy + 0.5) / N
    m = np.zeros((N, N), bool)
    light = np.zeros((N, N), np.float32)
    for x, y, r in puffs:
        d2 = np.hypot(u - x, v - y) / r
        m |= d2 < 1
        light = np.maximum(light, np.clip(1 - np.hypot(u - x + 0.25 * r, v - y + 0.35 * r) / r, 0, 1))
    mask = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((n, n), Image.LANCZOS)) > 110
    l = np.array(Image.fromarray((light * 255).astype(np.uint8), "L").resize((n, n), Image.LANCZOS), np.float32) / 255
    c = np.empty((n, n, 3), np.float32)
    c[...] = (150, 158, 164)
    c[l > 0.16] = (198, 204, 208)
    c[l > 0.44] = (238, 241, 243)
    return finish(c, mask)


TILES["vapeur"] = paint_cloud(48)


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

# Calque lumineux, non embarqué tant que AVEC_E = False : foyer, bouts de tuyère ; fond noir ; un filet très sombre sur le capot.
u0, v0, u1, v1 = UV["foyer"]
tex_e[v0 + 3:v1 - 3, u0 + 3:u1 - 3] = (230, 120, 40, 255)
tex_e[v0 + 3:v1 - 3, u0 + 8:u0 + 10] = 0
tex_e[v0 + 3:v1 - 3, u0 + 15:u0 + 17] = 0
u0, v0, u1, v1 = UV["cap_copper"]
_yy, _xx = np.mgrid[0:16, 0:16]
_m = np.hypot(_xx + 0.5 - 8, _yy + 0.5 - 8) < 3
tex_e[v0:v1, u0:u1][_m] = (120, 64, 20, 255)
assert set(np.unique(tex[..., 3])) <= {0, 255}, "semi-transparence"
assert set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence _e"
tex_img = Image.fromarray(tex, "RGBA")
tex_img.save(f"{NOM}.png", optimize=True)
_b = io.BytesIO()
tex_img.save(_b, "PNG", optimize=True)
tex_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()
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


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups
    groups[name] = {"origin": [round(v, 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(v, 2) for v in rotation]}
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
    EMITS.append(group("emit_vapeur" + (str(len(EMITS) + 1) if EMITS else ""), [x, y, z], parent=parent))


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


VREST = {}
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
    emit(el, s * 18.0, 35.6, zp + 1.5)
    return rt, sh, tag


(LR_, L_, _), (RR_, R_, _) = build(-1), build(1)

# Petite chaudière, très discrète, à la racine : un tambour plus étroit que le torse, deux évents. Pas un sac à dos.
CH = group("chaudiere", [0, 21.7, 3.5])
bar(1, CH, "drum", -2.2, 21.7, 3.5, 4.4, 1.22, 0, "copper")
bar(1, CH, "cerc0", -2.45, 21.7, 3.5, 0.5, 1.36, 0, "steel")
bar(1, CH, "cerc1", 1.95, 21.7, 3.5, 0.5, 1.36, 0, "steel")
for i, x in enumerate((-1.25, 1.25)):
    bar(1, CH, f"evt{i}", x, 22.7, 3.5, 1.5, 0.42, 90, "brass", octo=True)
    emit(CH, x, 24.5, 3.5)
_fu0, _fv0, _fu1, _fv1 = UV["foyer"]
groups[CH]["ids"].append(cube("foyer", [-0.65, 20.95, 4.68], [0.65, 21.75, 4.92], [0, 21.35, 4.8],
                              faces={"south": [_fu0, _fv0, _fu1, _fv1], "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}))

# Particule (guide, section 5 ter) : une seule plaque, face up seule, 0,3 px au-dessus du pivot : aucun contact avec le sol.
PL = group("particle_vapeur", [0, 0, 0])
PW, PTH, PY = 3.6, 0.3, 0.3
_pu0, _pv0, _pu1, _pv1 = UV["vapeur"]
groups[PL]["ids"].append(cube("vapeur", [-PW / 2, PY, -PW / 2], [PW / 2, PY + PTH, PW / 2], [0, 0, 0], faces={"up": [_pu0, _pv0, _pu1, _pv1]}))


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(),
             "children": [{"name": "item", "origin": [0, 0, 0], "uuid": nuid(),
                           "children": [bone(CH), bone(LR_), bone(RR_), bone(L_), bone(R_)]}]},
            bone(PL)]

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


def add_gears(a, turns):
    """turns : tours du grand engrenage par boucle, entier. Même sens dans tous les états."""
    L = a["length"]
    for s, tag in ((-1, "l"), (1, "r")):
        for name, ratio in GEAR_PARTS:
            v = 360.0 * turns * ratio
            g = f"{name}_{tag}"
            a["animators"][groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf("rotation", 0, *mirror(s, 0, 0, 0)), kf("rotation", L, *mirror(s, 0, 0, v))]}


def add_verin(a, elbow, n):
    """Le cylindre suit le tenon de l'avant-bras, la tige coulisse : la liaison reste fermée dans tous les états."""
    L = a["length"]
    times = [i * L / n for i in range(n + 1)]
    for s, tag in ((-1, "l"), (1, "r")):
        y0, z0, L0 = VREST[tag]
        kc, kt = [], []
        for t in times:
            ex, ey, ez = mirror(s, *(f(t) for f in elbow))
            y, z, ln = verin_aim(s, (ex, -s * YAW[1] + ey, ez))
            assert 0.2 < ROD_IN + ln - L0 < CYL - 0.3, f"tige hors du cylindre : {ln - L0:.2f}"
            kc.append(kf("rotation", t, 0, y - y0, z - z0))
            kt.append(kf("position", t, s * (ln - L0), 0, 0))
        a["animators"][groups[f"verin_{tag}"]["uuid"]] = {"name": f"verin_{tag}", "type": "bone", "keyframes": kc}
        a["animators"][groups[f"tige_{tag}"]["uuid"]] = {"name": f"tige_{tag}", "type": "bone", "keyframes": kt}


def anim(name, length, segs, fold, curl=C(0), n_kf=None, loop="loop", only=None, turns=None):
    """segs : shoulder/elbow/wrist -> (fx, fy, fz). only : familles animées (attaque et blessé, joués une fois par-dessus l'état)."""
    A_ = {}

    def put(g, kfs):
        if only is None or re.sub(r"\d*_[lr]$", "", g) in only:
            A_[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}

    n = n_kf or max(6, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]   # interpolation linéaire : dernier keyframe = premier
    for s, tag in ((-1, "l"), (1, "r")):
        for seg, (fx, fy, fz) in segs.items():
            put(f"{seg}_{tag}", [kf("rotation", t, *mirror(s, fx(t), fy(t), fz(t))) for t in times])
        for k in range(NR):
            # décalage de phase d'une lame à l'autre : le mécanisme se referme de proche en proche
            dl = 0.012 * length * (NR - 1 - k)
            put(f"ray{k}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, -CLOSE[k] * fold((t - dl) % length if loop == "loop" else max(0.0, t - dl)))) for t in times])
            put(f"ray{k}b_{tag}", [kf("rotation", t, *mirror(s, 0, 0, -CURLW[k] * curl(t))) for t in times])
        for j in range(len(SECS)):
            put(f"sec{j + 1}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, (10 - 2.5 * j) * fold(t))) for t in times])
        for j in range(len(TERS)):
            put(f"ter{j + 1}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, (2 + 2 * j) * fold(t))) for t in times])
        put(f"thumb_{tag}", [kf("rotation", t, *mirror(s, 0, 0, 26 * max(0.0, fold(t)))) for t in times])
    a = {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
         "selected": name == "idle", "animators": A_}
    if turns:
        add_gears(a, turns)
        add_verin(a, segs["elbow"], n)
    return a


Z0 = C(0)

# idle 8 s : repos, demi-fermé ; respiration (4 s) + étirement ample 4,6–7,2 s. Engrenage : 1 tour en 8 s (45°/s).
st = lambda t: bump(t, 4.6, 5.3, 6.1, 7.2)
mix = lambda f, v: (lambda t: f(t) * (1 - st(t)) + v * st(t))
idle = anim("idle", 8.0, {
    "shoulder": (mix(S(4, 1.0, 0, 6), 15), mix(S(4, 1.5, 0, 14), -6), mix(S(4, 2, 0, 2), 7)),
    "elbow":    (Z0, mix(S(4, 1, -40, -6), -4), mix(S(4, 1.5, -40, -3), 4)),
    "wrist":    (Z0, mix(S(4, 0.8, -70, 8), -6), mix(S(4, 1, -70, -6), 3))},
    fold=lambda t: (0.22 + 0.05 * math.sin(TAU * t / 4)) * (1 - st(t)), curl=lambda t: (4 + 1.5 * math.sin(TAU * t / 4)) * (1 - st(t)), n_kf=48, turns=1)

# fly 2,4 s : joueur debout en vol créatif. Plan basculé d'environ 40° (jamais 90°), battement ample. Engrenage : 300°/s.
T = 2.4
up = lambda t, lag=0.0: 0.5 + 0.5 * mech(math.cos(TAU * (t / T - lag)), 1.4)
fly = anim("fly", T, {
    "shoulder": (S(T, 4, 90, 40), S(T, 5, 90, -13), S(T, 22, 0, 0)),
    "elbow":    (Z0, lambda t: 8 - 3 * up(t, 0.12), S(T, 8, -45, -2)),
    "wrist":    (Z0, lambda t: -8 + 3 * up(t, 0.22), lambda t: 2 + 5 * math.sin(TAU * t / T - math.radians(75)) - 15 * up(t, 0.22))},
    fold=lambda t: 0.02 + 0.40 * up(t, 0.2), curl=lambda t: 2 + 11 * up(t, 0.26), n_kf=24, turns=2)

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
    a = {"uuid": nuid(), "name": "glide", "loop": "loop", "override": False, "length": G, "snapping": 24, "selected": False, "animators": A_}
    add_gears(a, 2)
    add_verin(a, (Z0, lambda t: 8 - 3 * math.sin(math.radians(t * 100 - 43)), C(1)), 18)   # tige calée sur le battement lent ; hors fusée
    return a


glide = glide_anim()

# fall 1,5 s : joueur debout, ailes relevées et ouvertes, plan peu basculé (freinage). Engrenage : 240°/s.
AI = 1.5
fall = anim("fall", AI, {"shoulder": (S(AI, 3, 0, 26), C(-4), S(AI, 3, 0, 6)),
                         "elbow": (Z0, C(3), S(AI, 3, -40, 5)),
                         "wrist": (Z0, C(-4), S(AI, 2, -70, 2))},
            fold=S(AI, 0.05, 0, 0.09), curl=S(AI, 3, -60, 8), turns=1)

# walk 1,6 s : ramenées vers l'arrière, à moitié fermées, balancement au pas. Engrenage : 225°/s.
WK = 1.6
walk = anim("walk", WK, {"shoulder": (C(8), S(WK, 5, 0, 30), S(WK, 3.5, 0, -8)),
                         "elbow": (Z0, S(WK, 3, -40, -10), S(WK, 2, -40, -4)),
                         "wrist": (Z0, S(WK, 3, -70, 14), S(WK, 2.5, -70, -22))},
            fold=C(0.55), curl=S(WK, 2, -70, 6), turns=1)

# run 1,0 s : très vers l'arrière, abaissées, repli en S réparti sur les 3 articulations, éventail presque fermé. 360°/s.
RN = 1.0
run = anim("run", RN, {"shoulder": (C(16), S(RN, 3, 0, 50), S(RN, 3, 0, -14)),
                       "elbow": (Z0, S(RN, 2, -40, -28), S(RN, 1.5, -40, -5)),
                       "wrist": (Z0, S(RN, 3, -80, 34), S(RN, 2, -80, -28))},
           fold=C(0.8), curl=S(RN, 2, -60, 8), turns=1)

# sneak 4 s : éventail fermé, plis serrés dans le dos, éperon qui dépasse au-dessus de l'épaule. Engrenage : 90°/s.
SN = 4.0
sneak = anim("sneak", SN, {"shoulder": (C(7), S(SN, 1, 0, 10), S(SN, 1, 0, 8)),
                           "elbow": (Z0, C(-15), S(SN, 1, -40, 0)),
                           "wrist": (Z0, C(5), C(-34))},
             fold=S(SN, 0.015, 0, 0.985), curl=C(9), turns=1)

# sleep 8 s : repliées, tombantes, engrenage au ralenti (45°/s, comme au repos)
SL = 8.0
sleep = anim("sleep", SL, {"shoulder": (C(12), S(SL, 1, 0, 12), S(SL, 1, 0, 2)),
                           "elbow": (Z0, C(-14), C(-4)),
                           "wrist": (Z0, C(6), C(-30))},
             fold=C(1.0), curl=S(SL, 1, -60, 10), turns=1)

# swim 2 s : joueur couché. Dans le plan du dos, rabattues vers les pieds, à demi fermées ; ondulation par Y. Engrenage : 180°/s.
SW = 2.0
swim = anim("swim", SW, {"shoulder": (C(7), S(SW, 7, 0, 2), C(-34)),
                         "elbow": (Z0, S(SW, 6, -45, 6), C(-10)),
                         "wrist": (Z0, S(SW, 7, -90, -4), C(-10))},
            fold=C(0.65), curl=S(SW, 4, -120, 6), turns=1)

# mount 3 s : repos relevé, pointes hautes, respiration ample. Engrenage : 120°/s.
MT = 3.0
mount = anim("mount", MT, {"shoulder": (C(10), S(MT, 2.5, 0, 8), S(MT, 3.5, 0, 12)),
                           "elbow": (Z0, S(MT, 1.5, -40, -4), S(MT, 2, -40, 5)),
                           "wrist": (Z0, C(2), S(MT, 2, -70, -2))},
             fold=S(MT, 0.04, 0, 0.26), curl=S(MT, 1.5, -40, 4), turns=1)

# attack et hurt : une fois par-dessus l'état, dernière image neutre, seuls les groupes concernés (ni engrenages ni vérin).
IMPULSE = {"shoulder", "elbow", "wrist", "ray", "thumb"}
AT = 0.8
atk = lambda t: bump(t, 0.0, 0.10, 0.30, 0.72)
attack = anim("attack", AT, {"shoulder": (lambda t: 24 * atk(t), lambda t: -12 * atk(t), lambda t: 8 * atk(t)),
                             "elbow": (Z0, lambda t: -6 * atk(t), lambda t: 5 * atk(t)),
                             "wrist": (Z0, lambda t: -8 * atk(t), lambda t: 6 * atk(t))},
              fold=lambda t: -0.08 * atk(t), n_kf=16, loop="once", only=IMPULSE)

HU = 0.8
hu = lambda t: bump(t, 0.0, 0.06, 0.22, 0.72)
tr = lambda t: 3 * math.sin(TAU * t * 5 / HU) * (1 - sm(t, 0.25, 0.7))
hurt = anim("hurt", HU, {"shoulder": (lambda t: 6 * hu(t), lambda t: 16 * hu(t), lambda t: 8 * hu(t) + tr(t)),
                         "elbow": (Z0, lambda t: -6 * hu(t), lambda t: -3 * hu(t) + tr(t)),
                         "wrist": (Z0, lambda t: 8 * hu(t), lambda t: -3 * hu(t) + tr(t))},
            fold=lambda t: 0.25 * hu(t), n_kf=16, loop="once", only=IMPULSE)


def particle_anim(name, length, curve, n):
    times = [i * length / n for i in range(n + 1)]
    return {"uuid": nuid(), "name": name, "loop": "loop", "override": False, "length": length, "snapping": 24, "selected": False,
            "animators": {groups[PL]["uuid"]: {"name": PL, "type": "bone", "keyframes": [kf("rotation", t, *curve(t)) for t in times]}}}


# chute/montée 4 s : un tour complet autour de Y (boucle fermée), léger roulis ; repos 6 s : respire à peine
PF, PR = 4.0, 6.0
vapeur_fall = particle_anim("particle_vapeur_fall", PF, lambda t: (14 * math.sin(TAU * t / PF), 360 * t / PF, 10 * math.cos(TAU * t / PF)), 24)
vapeur_rest = particle_anim("particle_vapeur_rest", PR, lambda t: (0, 0, 1.2 * math.sin(TAU * t / PR)), 12)

ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, attack, hurt, vapeur_fall, vapeur_rest]
assert 3 <= len(EMITS) <= 5 and len(ANIMS) <= 16
assert 200 <= len(elements) <= 450, f"budget : {len(elements)} cubes"

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))
with open(OUT) as fh:
    json.load(fh)


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 2, "groupes ; profondeur", depth(outliner[0]), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      f"{len(EMITS)} emit_")
