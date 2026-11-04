"""Haut-de-forme mécanique : ensemble Steampunk (thème Mécanique). Design original.
Écrit haut_de_forme_mecanique.png, haut_de_forme_mecanique_e.png et .build/haut_de_forme_mecanique_brut.bbmodel à côté de ce script.

Pièce de tête (groupe de premier niveau head). Calotte de feutre brun-noir légèrement évasée, à pans coupés ; bord à ourlet
roulé, relevé sur les côtés ; ruban de cuir cousu, boucle de laiton à droite. À gauche, deux engrenages de laiton qui
s'entraînent (12 et 6 dents, rapport 2, avance dent par dent). À droite, un manomètre relié par un tuyau de cuivre à la
petite cheminée de l'arrière droit (sifflet, soupape qui tremble puis se soulève à chaque décharge). À l'avant, des
lunettes de laiton à verres ambre sur un bras articulé à la charnière du bord : elles basculent devant les yeux en sneak
et en attack (le verre reste vertical : contre-rotation de la monture), sinon elles restent posées sur le ruban.

Mouvement mécanique : crans avec dépassement et rappel (step_resp), cycle de pression (aiguille qui monte par crans,
soupape qui tremble, décharge : bouffée, aiguille qui retombe), pièces décalées dans le temps.

Fonctions anticipées ou récentes utilisées (docs/guide-cosmetiques.md 4 bis, 5 ter, 6.4 ; .claude/rules/conventions-anticipees.md),
la pièce reste correcte sans elles :
- trans_vapeur : bouffée de chaque décharge, 3 plaques croisées, alpha en dégradé, lisible en cutout (seuil 50 %) ;
- ctrl_alpha (dans trans_vapeur) : x de 0 (normal) à -1 (invisible), convention « 1 + position » du guide ;
- trans_jet : grand jet de l'attaque, caché dans le fût de la cheminée hors de l'attaque (position et échelle neutres) ;
- emit_mc_white_smoke (bouche de la cheminée, +Y du groupe vers le haut) : cadence réglée par le staff (guide 5 ter).
  Pas de ctrl_emit : le guide et le vérificateur ne connaissent que ctrl_alpha, ctrl_teinte, ctrl_lumiere et ctrl_uv ;
  la synchronisation avec la décharge passe par la bouffée modélisée (trans_vapeur) ;
- overlay_engrenages : les engrenages avancent en permanence par-dessus l'état, sans saut entre deux états ;
- haut_de_forme_mecanique_r.png : masque de reflets (guide 5 quater), une valeur par matière, lu par face :
  laiton et verre clairs, cuivre et acier moyens, feutre et cuir presque mats, vapeur sans reflet ;
- son block.fire.extinguish (piste Effets) à chaque décharge de idle, walk, run, sneak et au jet de l'attaque.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # calque _e embarqué (réactivé le 2026-11-03, correctif du mod annoncé, à vérifier en jeu)
TEX = 512
TAU = 2 * math.pi
NOM = "haut_de_forme_mecanique"

# ------------------------------------------------------------------ palette (.claude/styles/steampunk.md)
FELT = dict(base=(52, 40, 36), hi=(96, 78, 66), low=(26, 20, 18))
BRASS = dict(base=(190, 142, 64), hi=(236, 196, 112), low=(112, 76, 32))
COPPER = dict(base=(176, 92, 52), hi=(232, 150, 96), low=(98, 46, 26))
STEEL = dict(base=(78, 82, 92), hi=(136, 140, 150), low=(38, 40, 48))
LEATHER = dict(base=(104, 62, 36), hi=(150, 96, 60), low=(60, 34, 20))
PATINA = np.array((82, 138, 116), np.float32)
PATINA_D = np.array((56, 104, 88), np.float32)


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

# ---- calotte : 4 pans principaux, 4 pans coupés, couvercle
Y_B, Y_T = 31.1, 40.1                      # bas et haut de la calotte
D_B, D_T = 4.7, 5.2                        # demi-largeur extérieure en bas, en haut (évasée)
CH_ = 0.75                                 # pan coupé : |x| + |z| <= 2d - CH_
TH_W = 0.5                                 # épaisseur des pans
ALPHA_M = math.atan((D_T - D_B) / (Y_T - Y_B))
E_B, E_T = (2 * D_B - CH_) / math.sqrt(2), (2 * D_T - CH_) / math.sqrt(2)
ALPHA_C = math.atan((E_T - E_B) / (Y_T - Y_B))
HM = (Y_T - Y_B) / math.cos(ALPHA_M)
HC = (Y_T - Y_B) / math.cos(ALPHA_C)
HALF_B, HALF_T = D_B - CH_ + 0.06, D_T - CH_ + 0.06        # demi-largeur d'un pan principal à la jonction
W_M = 2 * HALF_T
W_C = CH_ * math.sqrt(2) + 0.12


def wall_tile(seed, sheen):
    W, H = 92, 92
    m = ss_mask(W, H, W_M, HM, lambda a, b: np.abs(a) <= lerp(HALF_B, HALF_T, b / HM + 0.5))
    return finish(felt_col(W, H, W_M, HM, seed, sheen), m)


TILES["mur_a"] = wall_tile(11, 0.22)
TILES["mur_b"] = wall_tile(12, -0.18)
TILES["pan"] = finish(felt_col(16, 92, W_C, HC, 13, 0.0), np.ones((92, 16), bool))

LID = 2 * D_T


def lid_tile():
    W = H = 104
    m = ss_mask(W, H, LID, LID, lambda a, b: (np.abs(a) <= D_T) & (np.abs(b) <= D_T) & (np.abs(a) + np.abs(b) <= 2 * D_T - CH_))
    a, b = grid(W, H, LID, LID)
    rr = np.hypot(a, b)
    col = felt_col(W, H, LID, LID, 14, 0.0, top_edge=False)
    col *= (1 + 0.018 * np.sin(rr * 6))[..., None]
    col = lerp(col, A(FELT["hi"]), (0.30 * np.exp(-((a + 1.6) ** 2 + (b - 1.6) ** 2) / 6))[..., None])
    d = inset(m, 3)
    col[(d < 2) & m] = A(FELT["hi"]) * 0.9                          # arête du sommet, nette
    return finish(col, m)


TILES["couvercle"] = lid_tile()

# ---- bord : plaque centrale + deux ailes relevées, ourlet roulé autour
B_A, B_B, B_R = 6.1, 6.0, 2.0               # demi-largeur (x), demi-profondeur (z), rayon des coins
B_Y, B_TH = 31.0, 0.5
FLAP_X, CURL = 4.4, math.radians(18)
FLAP_L = (B_A - FLAP_X) / math.cos(CURL) + 0.05


def in_brim(x, z, m=0.04):
    ax, az = np.abs(x), np.abs(z)
    qx, qz = np.maximum(ax - (B_A - B_R), 0), np.maximum(az - (B_B - B_R), 0)
    return (ax <= B_A - m) & (az <= B_B - m) & (np.hypot(qx, qz) <= B_R - m)


def brim_col(x, z, seed):
    H, W = x.shape
    r = np.hypot(x, z)
    col = A(FELT["base"]) * np.ones((H, W, 3), np.float32) * 1.06
    col *= (0.92 + 0.10 * cell_noise(H, W, max(W, H) // 2, seed) + 0.06 * np.sin(r * 8.5))[..., None]
    crown = np.maximum(np.abs(x), np.abs(z))
    col *= (0.55 + 0.45 * np.clip((crown - D_B) / 0.9, 0, 1))[..., None]     # ombre au pied de la calotte
    return col


def brim_tile(name, c, X, Y, w, h, seed, dens=10):
    W, H = int(round(w * dens)), int(round(h * dens))
    ss = 3
    a, b = grid(W, H, w, h, ss)
    xw = c[0] + a * X[0] + b * Y[0]
    zw = c[2] + a * X[2] + b * Y[2]
    m = in_brim(xw, zw).reshape(H, ss, W, ss).mean(axis=(1, 3)) > 0.5
    a, b = grid(W, H, w, h)
    TILES[name] = finish(brim_col(c[0] + a * X[0] + b * Y[0], c[2] + a * X[2] + b * Y[2], seed), m)


C18, S18 = math.cos(CURL), math.sin(CURL)
BRIM = [("bord_c", (0, B_Y, 0), (1, 0, 0), (0, 0, -1), 2 * FLAP_X, 2 * B_B),
        ("bord_r", (FLAP_X + C18 * FLAP_L / 2, B_Y + S18 * FLAP_L / 2, 0), (C18, S18, 0), (0, 0, -1), FLAP_L, 2 * B_B),
        ("bord_l", (-FLAP_X - C18 * FLAP_L / 2, B_Y + S18 * FLAP_L / 2, 0), (-C18, S18, 0), (0, 0, 1), FLAP_L, 2 * B_B)]
for i, (n, c, X, Y, w, h) in enumerate(BRIM):
    brim_tile(n, c, X, Y, w, h, 21 + i)

# ---- ruban de cuir cousu
BD_Y0, BD_Y1 = 31.3, 33.4


def band_tile(w, seed):
    W, H = max(16, int(round(w * 10))), 22
    r = np.random.default_rng(seed)
    col = A(LEATHER["base"]) * np.ones((H, W, 3), np.float32)
    col *= (0.86 + 0.22 * cell_noise(H, W, max(W, H) // 3, seed) + 0.06 * r.random((H, W)))[..., None]
    col[:2] = A(LEATHER["low"])
    col[-2:] = A(LEATHER["low"])
    col[2:4] = A(LEATHER["hi"]) * 0.9
    for row in (5, H - 7):                                              # coutures en fil de laiton, 2 texels
        for x0 in range(1, W, 6):
            col[row:row + 2, x0:x0 + 4] = A(BRASS["hi"]) * 0.85
    return finish(col, np.ones((H, W), bool))


TILES["ruban"] = band_tile(8.4, 31)
TILES["ruban_c"] = band_tile(1.6, 32)


# ---- métal : barres, capuchons, engrenages, plaques
def bar_tile(metal, seed, grooves=3, slot=False):
    W, H = 96, 16
    a = np.zeros((H, W, 3), np.float32)
    r = np.random.default_rng(seed)
    for yy in range(H):
        q = abs((yy + 0.5) / H - 0.5) * 2
        a[yy, :] = lerp(lerp(A(metal["hi"]) * 0.85, A(metal["low"]), q ** 1.1), A(metal["base"]), 0.42)
    a *= (0.92 + 0.16 * r.random((1, W, 1), np.float32))
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


def paint_gear(n, teeth, metal, tooth_phase, seed, spokes=None, hole=0.24, h_t=0.16):
    """Engrenage (repris de ailes_mecaniques) : dents trapézoïdales, une dent à tooth_phase (degrés, sens trigo)."""
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
    col *= (0.86 + 0.28 * nz)[..., None]
    col[r > rr - 0.04] = A(metal["hi"])
    col[(r > rr - 0.14) & (r <= rr - 0.05)] *= 0.55
    col[r < hole + 0.12] = A(metal["hi"]) * 0.9
    col[(nz > 0.80) & (r < rr - 0.15)] = PATINA
    return finish(col, mask)


# Engrenages du côté gauche : grand (12 dents) et pignon (6 dents), rapport 2. Plaque vue depuis -X : u suit +Z, v suit +Y.
GB = (33.7, 0.25)                          # centre du grand (y, z)
R_GB, R_GS = 1.9, 1.0
HT_B, HT_S = 0.16, 0.26
GDIST = R_GB * 0.98 * (1 - HT_B / 2) + R_GS * 0.98 * (1 - HT_S / 2)
G_ANG = 52.0                               # direction du pignon depuis le grand, dans l'image (sens trigo depuis +u)
GS = (GB[0] + GDIST * math.sin(math.radians(G_ANG)), GB[1] + GDIST * math.cos(math.radians(G_ANG)))
TILES["roue12"] = paint_gear(80, 12, BRASS, G_ANG + 15, 51, spokes=4, h_t=HT_B)        # creux face au pignon
TILES["roue6"] = paint_gear(44, 6, BRASS, G_ANG + 180, 52, hole=0.30, h_t=HT_S)         # dent face au creux


def plaque_engrenages():
    """Platine rivetée derrière les deux engrenages : deux disques reliés, laiton patiné."""
    z0, z1 = min(GB[1] - 1.35, GS[1] - 0.95) - 0.1, max(GB[1] + 1.35, GS[1] + 0.95) + 0.1
    y0, y1 = min(GB[0] - 1.35, GS[0] - 0.95) - 0.1, max(GB[0] + 1.35, GS[0] + 0.95) + 0.1
    w, h = z1 - z0, y1 - y0
    W, H = int(round(w * 18)), int(round(h * 18))
    zc, yc = (z0 + z1) / 2, (y0 + y1) / 2
    ca = (GB[1] - zc, GB[0] - yc)         # centres en coordonnées de plaque (a suit +Z, b suit +Y)
    cb = (GS[1] - zc, GS[0] - yc)

    def fn(a, b):
        d1 = np.hypot(a - ca[0], b - ca[1]) <= 1.35
        d2 = np.hypot(a - cb[0], b - cb[1]) <= 0.95
        vx, vy = cb[0] - ca[0], cb[1] - ca[1]
        L = math.hypot(vx, vy)
        t = ((a - ca[0]) * vx + (b - ca[1]) * vy) / L
        n_ = np.abs(-(a - ca[0]) * vy + (b - ca[1]) * vx) / L
        return d1 | d2 | ((t > 0) & (t < L) & (n_ < 0.75))
    m = ss_mask(W, H, w, h, fn)
    col = A(BRASS["base"]) * np.ones((H, W, 3), np.float32) * 0.9
    nz = cell_noise(H, W, 14, 53)
    col *= (0.86 + 0.25 * nz)[..., None]
    col[(nz > 0.72) & m] = PATINA
    col[(nz > 0.80) & m] = PATINA_D
    d = inset(m, 5)
    col[(d >= 2) & (d < 4)] *= 0.5
    col[d < 2] = A(BRASS["hi"])
    for (pa, pb) in ((ca[0] - 0.95, ca[1] - 0.2), (ca[0] + 0.5, ca[1] - 0.9), (cb[0] + 0.55, cb[1] + 0.35)):
        rivet(col, (pa / w + 0.5) * W, (0.5 - pb / h) * H, 2.2, STEEL)
    return finish(col, m), (w, h, zc, yc)


TILES["platine"], PLATINE = plaque_engrenages()


def disc_tile(n, r_out, r_in, metal, rivets=0, seed=0, rr=2.0):
    """Anneau ou disque de laiton riveté (r en fraction du demi-côté)."""
    yy, xx = np.mgrid[0:n * 3, 0:n * 3]
    r = np.hypot(xx + 0.5 - n * 1.5, yy + 0.5 - n * 1.5) / (n * 1.5)
    m = ((r <= r_out) & (r >= r_in)).reshape(n, 3, n, 3).mean(axis=(1, 3)) > 0.5
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) / (n / 2)
    col = A(metal["base"]) * np.ones((n, n, 3), np.float32)
    col *= (0.88 + 0.22 * cell_noise(n, n, 10, seed))[..., None]
    col[np.abs(r - r_out) < 2.2 / n] = A(metal["hi"])
    col[np.abs(r - r_in) < 2.2 / n] = A(metal["low"])
    for k in range(rivets):
        an = TAU * (k + 0.5) / rivets
        rm = (r_out + max(r_in, 0.5)) / 2
        rivet(col, n / 2 + rm * n / 2 * math.cos(an), n / 2 - rm * n / 2 * math.sin(an), rr, STEEL)
    return finish(col, m)


TILES["cercle"] = disc_tile(72, 0.98, 0.66, BRASS, rivets=8, seed=61)       # monture d'une lentille
TILES["lunette"] = disc_tile(64, 0.98, 0.80, BRASS, rivets=6, seed=62, rr=1.6)  # lunette du manomètre
TILES["embase"] = disc_tile(48, 0.98, 0.0, BRASS, rivets=6, seed=63, rr=1.6)    # bride de la cheminée


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
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx, ordre du mod et du renderer."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


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


def bar(g, name, p, q, r, mat, octo=True, ov=0.0, ends=None, up=None):
    """Tronçon de p à q, section carrée de demi-côté r (+ un second cube à 45° si octo)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = np.asarray(up, float) if up is not None else (V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0))
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    L = np.linalg.norm(q - p) + 2 * ov
    c = (p + q) / 2
    bu0, bv0, bu1, bv1 = UV[f"bar_{mat}"] if f"bar_{mat}" in UV else UV[mat]
    ub = bu0 + max(4, min(bu1 - bu0, (bu1 - bu0) * L / 6))
    lg = [bu0, bv0, ub, bv1]
    cu = UV[f"cap_{mat}"] if f"cap_{mat}" in UV else UV["cap_brass"]
    en = [cu[0], cu[1], cu[2], cu[3]]
    faces = {"south": lg, "north": lg, "up": lg, "down": lg, "east": en, "west": en}
    faces.update(ends or {})
    box(g, name, c, X, Y, (L, 2 * r, 2 * r), faces)
    if octo:
        k = math.sqrt(0.5)
        box(g, name + "o", c, X, k * Y + k * Z_, (L - 0.06, 2 * r * 0.97, 2 * r * 0.97), faces)


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


UP = V(0, 1, 0)
HAT = group("chapeau", [0, 31.2, 0])

# ---- calotte
for k in range(8):
    phi = math.radians(45 * k)
    n_ = V(math.cos(phi), 0, math.sin(phi))
    main = k % 2 == 0
    al = ALPHA_M if main else ALPHA_C
    dm = (D_B + D_T) / 2 if main else (E_B + E_T) / 2
    X = np.cross(UP, n_)
    Y = UP * math.cos(al) + n_ * math.sin(al)
    c = n_ * (dm - TH_W / 2) + V(0, (Y_B + Y_T) / 2, 0)
    if main:
        plate(HAT, f"mur{k // 2}", c, X, Y, W_M, HM, "mur_a" if k in (0, 4) else "mur_b", th=TH_W)
    else:
        plate(HAT, f"pan{k // 2}", c, X, Y, W_C, HC, "pan", th=TH_W)
plate(HAT, "couvercle", V(0, Y_T - 0.05, 0), V(1, 0, 0), V(0, 0, -1), LID, LID, "couvercle", th=0.3)

# ---- bord + ourlet roulé
for n, c, X, Y, w, h in BRIM:
    plate(HAT, n, V(*c), V(*X), V(*Y), w, h, n, th=B_TH)


def brim_y(x):
    return B_Y + max(0.0, abs(x) - FLAP_X) * math.tan(CURL)


def outline(n_side=3, n_arc=3):
    pts = []
    cx, cz = B_A - B_R, B_B - B_R
    corners = [((cx, -cz), -90), ((cx, cz), 0), ((-cx, cz), 90), ((-cx, -cz), 180)]   # avant droit, arrière droit…
    for (ox, oz), a0 in corners:
        for i in range(n_arc):
            a = math.radians(a0 + 90 * i / n_arc)
            pts.append((ox + B_R * math.cos(a), oz + B_R * math.sin(a)))
        a = math.radians(a0 + 90)
        p0 = (ox + B_R * math.cos(a), oz + B_R * math.sin(a))
        nxt = corners[(corners.index(((ox, oz), a0)) + 1) % 4]
        a1 = math.radians(nxt[1])
        p1 = (nxt[0][0] + B_R * math.cos(a1), nxt[0][1] + B_R * math.sin(a1))
        for i in range(n_side):
            pts.append((lerp(p0[0], p1[0], i / n_side), lerp(p0[1], p1[1], i / n_side)))
    return pts


ROLL = [V(x, brim_y(x), z) for x, z in outline()]
for i in range(len(ROLL)):
    p, q = ROLL[i], ROLL[(i + 1) % len(ROLL)]
    bar(HAT, f"ourlet{i}", p, q, 0.34, "felt", octo=True, ov=0.12)

# ---- ruban (pans plus larges que la calotte de 0,28)
YM = (BD_Y0 + BD_Y1) / 2
dB = D_B + (YM - Y_B) * math.tan(ALPHA_M)
for k in range(8):
    phi = math.radians(45 * k)
    n_ = V(math.cos(phi), 0, math.sin(phi))
    main = k % 2 == 0
    al = ALPHA_M if main else ALPHA_C
    dist = (dB + 0.28 - 0.15) if main else ((2 * dB - CH_) / math.sqrt(2) + 0.28 - 0.15)
    X = np.cross(UP, n_)
    Y = UP * math.cos(al) + n_ * math.sin(al)
    t = "ruban" if main else "ruban_c"
    w = 8.4 if main else 1.42
    u0, v0, u1, v1 = UV[t]
    plate(HAT, f"ruban{k}", n_ * dist + V(0, YM, 0), X, Y, w, BD_Y1 - BD_Y0, t, th=0.3,
          sides={"up": [u0, v0, u1, v0 + 3], "down": [u0, v1 - 3, u1, v1]})


def wall_out(y, extra=0.0):
    return D_B + (y - Y_B) * math.tan(ALPHA_M) + extra


# ---- boucle de laiton (côté droit, vers l'avant)
xb = wall_out(32.7, 0.28) + 0.1
bz0, bz1, by0, by1 = -3.05, -1.55, 31.78, 33.66
for i, (p, q) in enumerate(((V(xb, by0, bz0), V(xb, by0, bz1)), (V(xb, by1, bz0), V(xb, by1, bz1)),
                            (V(xb, by0, bz0), V(xb, by1, bz0)), (V(xb, by0, bz1), V(xb, by1, bz1)))):
    bar(HAT, f"boucle{i}", p, q, 0.17, "brass", octo=False, ov=0.16)
bar(HAT, "ardillon", V(xb + 0.05, 32.72, bz0 - 0.1), V(xb + 0.05, 32.72, -2.05), 0.15, "steel", octo=False)
plate(HAT, "bout_ruban", V(xb - 0.02, 32.35, -3.55), V(0, 0, -1), V(0, 1, 0), 1.0, 1.55, "ruban_c", th=0.3)

# ---- engrenages (côté gauche) : platine, deux roues sur leurs axes, le tout incliné comme le pan
xg = -(wall_out(GB[0], 0.28))
ENG = group("engrenages", [xg, GB[0], GB[1]], parent=HAT, rotation=(0, 0, math.degrees(ALPHA_M)))
pw, ph, zc, yc = PLATINE
plate(ENG, "platine", V(xg - 0.08, yc, zc), V(0, 0, 1), V(0, 1, 0), pw, ph, "platine", th=0.36)
GEARS = []
for nm, (gy, gz), R_, tile, xoff in (("roue_g", GB, R_GB, "roue12", 0.0), ("roue_p", GS, R_GS, "roue6", 0.06)):
    xd = xg - 0.95 - xoff
    g = group(nm, [xd, gy, gz], parent=ENG)
    GEARS.append(g)
    plate(g, f"{nm}_dents", V(xd, gy, gz), V(0, 0, 1), V(0, 1, 0), 2 * R_, 2 * R_, tile, th=0.4)
    bar(g, f"{nm}_moyeu", V(xg - 0.2, gy, gz), V(xd + 0.15, gy, gz), R_ * 0.42, "brass", octo=True)
    bar(g, f"{nm}_axe", V(xd - 0.1, gy, gz), V(xd - 0.5, gy, gz), 0.3 if R_ > 1.5 else 0.22, "steel", octo=True)

# ---- manomètre (côté droit, vers l'arrière) relié à la cheminée
MZ, MY = 1.6, 34.5
xm = wall_out(MY)
MANO = group("manometre", [xm, MY, MZ], parent=HAT, rotation=(0, 0, -math.degrees(ALPHA_M)))
bar(MANO, "boitier", V(xm - 0.08, MY, MZ), V(xm + 0.55, MY, MZ), 0.94, "brass", octo=True)
plate(MANO, "cadran", V(xm + 0.62, MY, MZ), V(0, 0, -1), V(0, 1, 0), 2.3, 2.3, "cadran", th=0.3)
plate(MANO, "lunette", V(xm + 0.97, MY, MZ), V(0, 0, -1), V(0, 1, 0), 2.75, 2.75, "lunette", th=0.3)
NEEDLE = group("aiguille", [xm + 0.9, MY, MZ], parent=MANO)
ua, va, ub_, vb = UV["aiguille"]
box(NEEDLE, "aiguille", V(xm + 0.95, MY + 0.36, MZ), V(0, 0, -1), V(0, 1, 0), (0.3, 1.08, 0.3),
    {f: [ua, va, ub_, vb] for f in ("east", "west", "up", "down", "north", "south")})
bar(NEEDLE, "pivot_aig", V(xm + 0.78, MY, MZ), V(xm + 1.15, MY, MZ), 0.2, "brass", octo=False)

# ---- cheminée (arrière droit, sur le couvercle)
CX, CZ, CY = 2.55, 2.55, Y_T + 0.1
CHEM = group("cheminee", [CX, CY, CZ], parent=HAT, rotation=(6, 0, -5))


def col_(g, name, y0, y1, r, mat, octo=True, ends=None):
    bar(g, name, V(CX, y0, CZ), V(CX, y1, CZ), r, mat, octo=octo, ends=ends, up=V(0, 0, 1))


plate(CHEM, "embase", V(CX, CY + 0.12, CZ), V(1, 0, 0), V(0, 0, -1), 2.0, 2.0, "embase", th=0.36)
col_(CHEM, "embase_n", CY - 0.1, CY + 0.42, 0.66, "brass")
col_(CHEM, "fut", CY + 0.25, CY + 3.2, 0.6, "copper")
col_(CHEM, "bague_1", CY + 1.1, CY + 1.4, 0.72, "brass")
col_(CHEM, "bague_2", CY + 2.6, CY + 2.9, 0.72, "brass")
col_(CHEM, "sifflet", CY + 3.15, CY + 4.05, 0.46, "sifflet")
SOUP = group("soupape", [CX, CY + 4.05, CZ], parent=CHEM)
bu = UV["bouche"]
col_(SOUP, "chapeau_soupape", CY + 4.02, CY + 4.32, 0.56, "steel", ends={"east": list(bu)})
col_(SOUP, "bouton", CY + 4.3, CY + 4.6, 0.18, "brass", octo=False)
MOUTH = V(CX, CY + 4.7, CZ)
EMIT = group("emit_mc_white_smoke", MOUTH, parent=CHEM)
VAP = group("trans_vapeur", [CX, CY + 4.35, CZ], parent=CHEM)
CTRL_A = group("ctrl_alpha", [CX, CY + 4.35, CZ], parent=VAP)
JET = group("trans_jet", [CX, CY + 0.8, CZ], parent=CHEM)
for i, yaw in enumerate((0, 60, 120)):
    X = V(math.cos(math.radians(yaw)), 0, -math.sin(math.radians(yaw)))
    plate(VAP, f"bouffee{i}", V(CX, CY + 4.35 + PUFF_H / 2, CZ) + 0.01 * i * X, X, UP, PUFF_W, PUFF_H, "vapeur", th=0.3)
    plate(JET, f"jet{i}", V(CX, CY + 0.8 + JET_H / 2, CZ) + 0.01 * i * X, X, UP, JET_W, JET_H, "jet", th=0.3)

# tuyau de cuivre du manomètre à l'embase de la cheminée (repère du chapeau, hors inclinaisons)
PIPE = [V(5.12, 35.6, 1.6), V(5.45, 39.3, 1.72), V(5.02, 40.62, 2.02), V(3.4, 40.5, 2.45)]
for i in range(len(PIPE) - 1):
    bar(HAT, f"tuyau{i}", PIPE[i], PIPE[i + 1], 0.22, "copper", octo=False, ov=0.12)
bar(HAT, "collier0", lerp(PIPE[0], PIPE[1], 0.5) - 0.3 * unit(PIPE[1] - PIPE[0]), lerp(PIPE[0], PIPE[1], 0.5) + 0.3 * unit(PIPE[1] - PIPE[0]), 0.31, "brass", octo=False)
bar(HAT, "collier1", lerp(PIPE[2], PIPE[3], 0.5) - 0.3 * unit(PIPE[3] - PIPE[2]), lerp(PIPE[2], PIPE[3], 0.5) + 0.3 * unit(PIPE[3] - PIPE[2]), 0.3, "brass", octo=False)

# ---- lunettes : charnière sur l'ourlet avant, bras, monture qui garde les verres verticaux
H_ = V(0, 30.8, -6.5)                     # charnière
B0 = V(0, 33.4, -5.5)                     # pont des lunettes au repos, posé sur le ruban
LX = 1.85                                 # demi-écart des verres
for s_ in (-1, 1):
    bar(HAT, f"charniere_{'l' if s_ < 0 else 'r'}", V(s_ * 0.55, H_[1], H_[2]), V(s_ * 1.15, H_[1], H_[2]), 0.3, "brass", octo=True)
bar(HAT, "axe_charniere", V(-1.3, H_[1], H_[2]), V(1.3, H_[1], H_[2]), 0.17, "steel", octo=True)
ARM = group("bras_lunettes", H_, parent=HAT)
bar(ARM, "noeud_bras", V(-0.5, H_[1], H_[2]), V(0.5, H_[1], H_[2]), 0.3, "brass", octo=True)
bar(ARM, "bras", H_, B0, 0.22, "brass", octo=False, ov=0.05, up=V(1, 0, 0))
LUN = group("lunettes", B0, parent=ARM)
bar(LUN, "pont", B0 + V(-0.6, 0.15, 0), B0 + V(0.6, 0.15, 0), 0.2, "brass", octo=False)
LENS = []
for s_, tag in ((-1, "l"), (1, "r")):
    c = B0 + V(s_ * LX, 0, 0)
    g = group(f"lentille_{tag}", c, parent=LUN)
    LENS.append(g)
    bar(g, f"coque_{tag}", c + V(0, 0, -0.35), c + V(0, 0, 0.35), 1.0, "brass", octo=True, ends={"west": CLEAR, "east": list(UV["cap_leather"])})
    plate(g, f"verre_{tag}", c + V(0, 0, -0.25), V(-1, 0, 0), UP, 2.3, 2.3, "verre", th=0.3)
    plate(g, f"cercle_{tag}", c + V(0, 0, -0.5), V(-1, 0, 0), UP, 3.0, 3.0, "cercle", th=0.3)
    bar(LUN, f"branche_{tag}", c + V(s_ * 1.35, 0, 0.1), c + V(s_ * 1.85, 0, 0.1), 0.2, "steel", octo=False)

# Bras : angle de bascule pour amener le pont devant les yeux (y ≈ 28,35), en passant devant le bord
r_arm = math.hypot(B0[1] - H_[1], B0[2] - H_[2])
phi_r = math.degrees(math.atan2(B0[2] - H_[2], B0[1] - H_[1]))
phi_d = math.degrees(math.acos((28.35 - H_[1]) / r_arm))
TH_D = phi_d - phi_r - 360.0
B_D = H_ + r_arm * V(0, math.cos(math.radians(phi_d)), math.sin(math.radians(phi_d)))
assert -4.7 > B_D[2] + 0.35 > -5.2 and B_D[1] + 1.5 < B_Y - B_TH / 2 - 0.2, B_D


def check_path():
    """Verres (verticaux) le long de la bascule : jamais dans la tête, le bord ni la calotte."""
    worst = 9.0
    for th in np.linspace(TH_D - 9, 0.5, 240):
        a = math.radians(phi_r + th)
        b = H_ + r_arm * V(0, math.cos(a), math.sin(a))
        for s_ in (-1, 1):
            for k in range(16):
                an = TAU * k / 16
                for dz in (-0.65, 0.35):
                    p = b + V(s_ * LX + 1.5 * math.cos(an), 1.5 * math.sin(an), dz)
                    if abs(p[0]) < 4.05 and abs(p[2]) < 4.05 and p[1] < 32.05:
                        worst = min(worst, -4.05 - p[2])
                    if in_brim(np.array([p[0]]), np.array([p[2]]), -0.4)[0] and abs(p[1] - brim_y(p[0])) < 0.65:
                        raise AssertionError(f"verre dans le bord à {th:.0f}°")
                    if Y_B < p[1] < Y_T and max(abs(p[0]), abs(p[2])) < wall_out(p[1]) + 0.05:
                        raise AssertionError(f"verre dans la calotte à {th:.0f}°")
    assert worst > 0.3, f"verre dans la tête : {worst:.2f}"


check_path()

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

    def tracks(self, vap_rot=0.0):
        return {NEEDLE: {"rotation": self.needle},
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


# idle 8 s : deux décharges (toutes les 4 s), petites bouffées entre elles
PI = Pression(4.0, 3.3, 5, 0.5, 1.4, 1.0, 1.1)
idle = anim("idle", 8.0, merge(PI.tracks(), {
    HAT: {"rotation": lambda t: PI.recoil(t)[0], "position": lambda t: PI.recoil(t)[1]},
    LUN: {"rotation": lambda t: (3.5 * ring(PI.tau(t)), 0, 0)}}), fps=30)

# walk 3,2 s : décharge toutes les 1,6 s ; un pas toutes les 0,8 s secoue les lunettes ; la bouffée part un peu vers l'arrière
PW = Pression(1.6, 1.2, 3, 0.25, 1.05, 0.85, 0.7, rise=0.05)
walk = anim("walk", 3.2, merge(PW.tracks(vap_rot=14), {
    HAT: {"rotation": lambda t: (0.6 * math.sin(TAU * t / 0.8) + PW.recoil(t)[0][0], 0, 0.4 * math.sin(TAU * t / 1.6)), "position": lambda t: PW.recoil(t)[1]},
    LUN: {"rotation": lambda t: (2.5 * ring((t - 0.1) % 0.8) + 3 * ring(PW.tau(t)), 0, 0)}}), fps=40)

# run 2,0 s : décharge toutes les secondes, vapeur rabattue vers l'arrière, chapeau poussé en arrière par le vent
PR = Pression(1.0, 0.7, 3, 0.18, 0.75, 0.9, 0.5, rise=0.04)
run = anim("run", 2.0, merge(PR.tracks(vap_rot=42), {
    HAT: {"rotation": lambda t: (2.5 + 0.7 * math.sin(TAU * t / 0.5) + PR.recoil(t)[0][0], 0, 0), "position": lambda t: PR.recoil(t)[1]},
    LUN: {"rotation": lambda t: (3.5 * ring((t - 0.05) % 0.5, 0.14, 0.08) + 3 * ring(PR.tau(t)), 0, 0)}}), fps=48)

# sneak 6 s : les lunettes basculent devant les yeux (dépassement, rappel), mise au point cran par cran, puis remontent en butée
PS = Pression(6.0, 3.0, 5, 0.45, 1.3, 0.6, 1.0)


def sneak_arm(t):
    return TH_D * (step_resp(t - 0.25, 0.32, 0.03) - stop_resp(t - 4.95, 0.42, 0.05))


def focus(t, d):
    up = sum(step_resp(t - d - ti, 0.06, 0.2) for ti in (1.6, 1.95, 2.3))
    dn = sum(step_resp(t - d - ti, 0.06, 0.2) for ti in (3.7, 4.05, 4.4))
    return (0, 0, 20 * (up - dn))


sneak = anim("sneak", 6.0, merge(PS.tracks(), {
    ARM: {"rotation": lambda t: (sneak_arm(t), 0, 0)},
    LUN: {"rotation": lambda t: (-sneak_arm(t) + 5 * ring(t - 0.57, 0.22, 0.12) - 4 * ring(t - 5.37, 0.2, 0.1), 0, 0)},
    LENS[0]: {"rotation": lambda t: focus(t, 0)},
    LENS[1]: {"rotation": lambda t: (0, 0, -focus(t, 0.35)[2])},
    HAT: {"rotation": lambda t: PS.recoil(t, 0.5)[0], "position": lambda t: PS.recoil(t, 0.5)[1]}}), fps=30)

# fall 1,2 s : le chapeau se soulève un peu, tout cliquette, vapeur coupée, aiguille affolée
FL = 1.2
fall = anim("fall", FL, {
    HAT: {"rotation": lambda t: (2.5 + 1.2 * math.sin(TAU * t / 0.6), 0, 0.6 * math.sin(TAU * t / FL)), "position": lambda t: (0, 0.32 + 0.08 * math.sin(TAU * t / FL), 0)},
    LUN: {"rotation": lambda t: (3.5 * math.sin(TAU * t / 0.3) + 1.5 * math.sin(TAU * t / 0.1), 0, 0)},
    SOUP: {"position": lambda t: (0, 0.05 + 0.04 * math.sin(TAU * t / 0.15), 0), "rotation": lambda t: (3 * math.sin(TAU * t / 0.2), 0, 4 * math.sin(TAU * t / 0.3))},
    NEEDLE: {"rotation": lambda t: (110 - 220 * (0.55 + 0.12 * math.sin(TAU * t / 0.4) + 0.04 * math.sin(TAU * t / 0.1)), 0, 0)},
    VAP: {"scale": lambda t: (0, 0, 0)}}, fps=30)

# attack 0,8 s (once, groupes concernés) : lunettes baissées d'un coup, grande décharge (jet), remontée en butée.
# Rotations ajoutées à l'état (guide 6.4) : rien si le joueur est déjà accroupi (lunettes déjà baissées).
AT = 0.8
NS = "(1-q.is_sneaking)*"


def atk_arm(t):
    return TH_D * (step_resp(t - 0.02, 0.09, 0.03) - stop_resp(t - 0.46, 0.14, 0.05, 0.08, 0.05))


def jet(t):
    """Jet de l'attaque : sort du fût (position), jaillit (échelle), monte, se résorbe, puis rentre caché."""
    up = 3.6 * sm(t, 0.04, 0.1) + 1.6 * sm(t, 0.12, 0.55)
    back = sm(t, 0.62, 0.66)
    sx = 1 + 2.4 * sm(t, 0.1, 0.2) - 3.4 * sm(t, 0.42, 0.62) + 1.0 * sm(t, 0.66, 0.74)
    sy = 1 + 3.0 * sm(t, 0.1, 0.22) + 1.0 * sm(t, 0.22, 0.5) - 5.0 * sm(t, 0.45, 0.62) + 1.0 * sm(t, 0.66, 0.74)
    return (sx, sy, sx), (0, up * (1 - back), 0)


attack = anim("attack", AT, {
    ARM: {"rotation": lambda t: (NS + f"({atk_arm(t):.2f})", 0, 0)},
    LUN: {"rotation": lambda t: (NS + f"({(-atk_arm(t) + 6 * ring(t - 0.11, 0.16, 0.08) * (1 - sm(t, 0.68, 0.8))):.2f})", 0, 0)},
    JET: {"scale": lambda t: jet(t)[0], "position": lambda t: jet(t)[1]},
    SOUP: {"position": lambda t: (0, 0.55 * bump(t, 0.05, 0.09, 0.45, 0.6), 0)},
    HAT: {"rotation": lambda t: (-2.5 * bump(t, 0.06, 0.12, 0.16, 0.5), 0, 0), "position": lambda t: (0, 0.12 * bump(t, 0.06, 0.1, 0.14, 0.4), 0)}},
    loop="once", fps=50)

# hurt 0,8 s (once) : sursaut, tremblement amorti, aiguille qui saute, soupape qui claque
HU = 0.8
hu = lambda t: bump(t, 0.0, 0.06, 0.2, 0.65)
vib = lambda t: math.sin(TAU * t * 5 / HU) * (1 - sm(t, 0.2, 0.7))
hurt = anim("hurt", HU, {
    HAT: {"rotation": lambda t: (5 * hu(t) + 2.5 * vib(t) * hu(t), 0, 2 * vib(t) * hu(t)), "position": lambda t: (0, 0.25 * hu(t), 0)},
    LUN: {"rotation": lambda t: (7 * ring(t - 0.03, 0.16, 0.1) * (1 - sm(t, 0.65, 0.8)), 0, 0)},
    SOUP: {"position": lambda t: (0, 0.3 * bump(t, 0.0, 0.04, 0.12, 0.3), 0)},
    NEEDLE: {"rotation": lambda t: (-40 * bump(t, 0.0, 0.05, 0.2, 0.6), 0, 0)}}, loop="once", fps=50)

# overlay_engrenages 8 s : échappement, 12 crans du grand (1 tour), le pignon fait 2 tours ; joué en permanence par-dessus l'état
OV = 8.0
overlay = anim("overlay_engrenages", OV, {
    GEARS[0]: {"rotation": lambda t: (-30 * ticks(t, OV, 12, 0.07, 0.3), 0, 0)},
    GEARS[1]: {"rotation": lambda t: (60 * ticks(t, OV, 12, 0.07, 0.3), 0, 0)}}, fps=30)

ANIMS = [idle, walk, run, sneak, fall, attack, hurt, overlay]
assert len(ANIMS) <= 16
assert 110 <= len(elements) <= 170, f"budget : {len(elements)} cubes"

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
textures.append({"name": f"{NOM}_r.png", "uv_width": TEX, "uv_height": TEX, "source": tex_r_b64})


def sons(a, times):
    """Clés de son de la piste Effets (guide 6.5) : sifflement de vapeur à chaque décharge."""
    a["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
        {"channel": "sound", "data_points": [{"effect": "block.fire.extinguish", "file": ""}], "time": round(t, 3)} for t in times]}


for a, P in ((idle, PI), (walk, PW), (run, PR), (sneak, PS)):
    sons(a, [P.td + k * P.P for k in range(-3, 12) if 0 <= P.td + k * P.P < a["length"]])
sons(attack, [0.06])
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


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", N_GROUPS, "groupes ; profondeur", depth(outliner[0]), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      f"bascule des lunettes {TH_D:.1f}° ; pont baissé y={B_D[1]:.2f} z={B_D[2]:.2f}")
