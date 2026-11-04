"""Épaulières mécaniques : paire asymétrique en laiton riveté, ensemble Steampunk (thème Mécanique). Design original.
Écrit epaulieres_mecaniques.png, epaulieres_mecaniques_e.png et .build/epaulieres_mecaniques_brut.bbmodel à côté de ce script.

Chaque épaule : un dôme (disque découpé + âme, couronne de facettes) et trois lames qui se recouvrent en tuiles
(chaque lame glisse sous le bord de la précédente), bord roulé clair, vert-de-gris dans les creux, sangle de cuir cousu.
- Droite (right_arm, la plus grande) : petite chaudière sur l'arrière de l'épaule, deux cheminées de cuivre à chapeau
  évasé, inclinées vers l'arrière et le haut, soupape à levier. Bouffées modélisées (plaques croisées translucides).
- Gauche (left_arm, plus petite) : manomètre à cadran ambre (aiguille dans son groupe, verre translucide) et
  engrenage + pignon qui avancent dent par dent.
Mouvement : cycle de pression (l'aiguille grimpe par paliers, tremble au maximum, décharge par les cheminées, retombe
avec un rebond) ; lames et cheminées jouent d'un cran à la décharge ; engrenage à échappement dans une couche permanente.

Fonctions avancées utilisées (.claude/rules/fonctions-avancees.md, docs/guide-cosmetiques.md) — à juger en jeu
(/cosmetique apercu), la pièce reste lisible sans elles :
- epaulieres_mecaniques_r.png : masque de reflets (laiton poli clair, cuivre/acier moyens, cuir et cadran mats) ;
- son block.fire.extinguish à chaque décharge (idle, walk, run) et au début de l'attaque ;
- trans_vapeur_r, trans_jet_1, trans_jet_2, trans_verre_l : alpha 1–254 (sans la fonction : cutout, cœur des bouffées lisible,
  verre invisible) ;
- emit_mc_white_smoke à la bouche de chaque cheminée (même nom pour les deux points, guide 5 ter), direction = +Y du
  groupe, orienté le long de la cheminée. Pas de ctrl_emit : absent du guide et refusé par le vérificateur ; la cadence
  reste celle du staff (conseil : Quand = Toujours, Rafale = À l'attaque) ;
- ctrl_alpha (fondu des bouffées, x = -1 invisible, 0 normal) ;
- overlay_engrenage : couche permanente, l'engrenage ne saute pas entre deux états.
Attaque : rotations et positions s'ajoutent à l'état, échelles se multiplient (guide, 6.4). Le jet d'attaque est donc
un groupe à part, rangé à l'échelle 1 DANS la cheminée (invisible), que l'attaque agrandit et fait sortir.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # calque _e embarqué (correctif du mod annoncé le 2026-11-03, à vérifier en jeu)
NOM = "epaulieres_mecaniques"
TEX = 512
TAU = 2 * math.pi
FPS = 30            # échantillonnage des courbes (paliers : >= 24 images/s), l'optimiseur simplifie


def lerp(a, b, k):
    return a + (b - a) * k


def A(c):
    return np.array(c, np.float32)


# ------------------------------------------------------------------ matières (fiche .claude/styles/steampunk.md)
BRASS = dict(hi=(236, 196, 112), base=(190, 142, 64), low=(112, 76, 32))
BRASS_D = dict(hi=(214, 170, 92), base=(160, 116, 50), low=(92, 60, 24))
COPPER = dict(hi=(232, 150, 96), base=(176, 92, 52), low=(98, 46, 26))
STEEL = dict(hi=(136, 140, 150), base=(78, 82, 92), low=(38, 40, 48))
PATINA, PATINA_D = A((132, 186, 160)), A((82, 138, 116))
CUIR = dict(hi=(150, 96, 60), base=(104, 62, 36), low=(60, 34, 20))


def inset(mask, n):
    im = Image.fromarray(mask.astype(np.uint8) * 255, "L")
    d = np.zeros(mask.shape, np.float32)
    for _ in range(n):
        im = im.filter(ImageFilter.MinFilter(3))
        d += np.array(im) > 127
    return d


def cell_noise(h, w, cells, seed):
    r = np.random.default_rng(seed)
    a = (r.random((max(2, int(cells * h / max(h, w))) + 2, max(2, int(cells * w / max(h, w))) + 2)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((w, h), Image.BICUBIC), np.float32) / 255


def rivet(col, x, y, r, metal):
    """Rivet peint : anneau sombre, tête, éclat. Diamètre >= 4 texels."""
    h, w = col.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dd = np.hypot(xx + 0.5 - x, yy + 0.5 - y)
    col[dd <= r + 1.0] = A(metal["low"]) * 0.55
    col[dd <= r] = A(metal["base"])
    col[np.hypot(xx + 0.5 - x + r * 0.3, yy + 0.5 - y + r * 0.3) <= r * 0.5] = A(metal["hi"])


def finish(col, mask, alpha=None):
    out = np.zeros(mask.shape + (4,), np.uint8)
    c = np.clip(col, 0, 255)
    if mask.any():
        c[~mask] = c[mask].mean(axis=0)
    out[..., :3] = c.astype(np.uint8)
    out[..., 3] = (mask * 255) if alpha is None else alpha
    return out


def disc_mask(n, r0, r1=0.0, ss=4):
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    r = np.hypot(xx + 0.5 - N / 2, yy + 0.5 - N / 2) / (N / 2)
    m = ((r <= r0) & (r >= r1)).astype(np.uint8) * 255
    return np.array(Image.fromarray(m, "L").resize((n, n), Image.LANCZOS)) > 110


def polar(n):
    yy, xx = np.mgrid[0:n, 0:n]
    dx, dy = (xx + 0.5 - n / 2) / (n / 2), -(yy + 0.5 - n / 2) / (n / 2)
    return np.hypot(dx, dy), np.degrees(np.arctan2(dx, dy))     # angle compté depuis le haut, sens horaire


TILES = {}


def paint_strip(W, H, metal, seed, n_riv, patina=0.35, rmetal=COPPER, top_shadow=0.30):
    """Lame déroulée : brossé horizontal, ombre de recouvrement et vert-de-gris en haut (sous la lame du dessus),
    ligne gravée, rangée de rivets, bord roulé clair en bas. Les facettes d'une lame se partagent la bande en u."""
    r = np.random.default_rng(seed)
    v = (np.arange(H) + 0.5)[:, None] / H * np.ones((1, W))
    streak = np.array(Image.fromarray((r.random((H, max(4, W // 20))) * 255).astype(np.uint8), "L").resize((W, H), Image.BILINEAR), np.float32) / 255 - 0.5
    col = A(metal["base"]) * np.ones((H, W, 3), np.float32)
    col *= (1 + 0.16 * streak)[..., None]
    col *= (0.94 + 0.14 * np.sin(np.pi * np.clip((v - 0.15) / 0.85, 0, 1)))[..., None]
    n = cell_noise(H, W, 34, seed + 1) * 0.5 + cell_noise(H, W, 80, seed + 2) * 0.5
    lim = 0.74 - patina * 0.3 + 0.32 * v
    col[n > lim] = PATINA
    col[n > lim + 0.06] = PATINA_D
    col *= lerp(0.40, 1.0, np.clip(v / top_shadow, 0, 1) ** 0.8)[..., None]
    col[:2] = A(metal["low"]) * 0.5
    yl = int(H * 0.70)
    col[yl] = A(metal["low"]) * 0.85
    col[yl + 1] = A(metal["hi"]) * 0.92
    col[H - 7] = A(metal["low"]) * 0.5                      # bord roulé : gorge sombre, bourrelet clair
    col[H - 6:H - 2] = A(metal["hi"]) * (1.0 + 0.08 * streak[H - 6:H - 2, :, None])
    col[H - 4] = A((250, 226, 160))
    col[H - 2:] = A(metal["base"]) * 0.78
    drip = np.random.default_rng(seed + 3)
    ry = 0.42 * H
    for i in range(n_riv):
        x = (i + 0.5) / n_riv * W
        if drip.random() < 0.7:                                 # le vert-de-gris coule depuis le rivet, vers le bas
            ln, wd = int(drip.uniform(5, 11)), 3
            col[int(ry):int(ry) + ln, int(x - wd / 2):int(x + wd / 2) + 1] = lerp(col[int(ry):int(ry) + ln, int(x - wd / 2):int(x + wd / 2) + 1], PATINA, 0.75)
    for i in range(n_riv):
        rivet(col, (i + 0.5) / n_riv * W, ry, 2.4, rmetal)
    return finish(col, np.ones((H, W), bool))


TILES["s_ring"] = paint_strip(232, 34, BRASS, 11, 12, patina=0.25, top_shadow=0.45)
TILES["s_l1"] = paint_strip(232, 44, BRASS, 21, 10, patina=0.35)
TILES["s_l2"] = paint_strip(232, 44, BRASS_D, 31, 10, patina=0.45, rmetal=STEEL)
TILES["s_l3"] = paint_strip(232, 44, BRASS, 41, 10, patina=0.40)


def paint_dome(n=72):
    """Dessus du dôme : disque repoussé (anneaux de tournage), bossette, couronne de rivets de cuivre, biseau clair."""
    m = disc_mask(n, 0.985)
    r, th = polar(n)
    col = A(BRASS["base"]) * np.ones((n, n, 3), np.float32)
    col *= (0.92 + 0.08 * np.sin(r * 46))[..., None]
    col *= (1.12 - 0.22 * r)[..., None]
    nz = cell_noise(n, n, 14, 51) * 0.6 + cell_noise(n, n, 34, 52) * 0.4
    col[(nz > 0.70) & (r > 0.3)] = PATINA
    col[(nz > 0.76) & (r > 0.3)] = PATINA_D
    col[r < 0.30] = A(BRASS["low"]) * 0.7
    col[r < 0.24] = A(BRASS["hi"])
    col[np.hypot(*np.mgrid[0:n, 0:n] - np.array([n * 0.46, n * 0.46])[:, None, None]) < n * 0.05] = A((252, 232, 176))
    d = inset(m, 6)
    col[(d >= 3) & (d < 5)] *= 0.5
    col[(d < 3) & m] = A(BRASS["hi"])
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        rivet(col, n / 2 + 0.66 * n / 2 * math.sin(a), n / 2 - 0.66 * n / 2 * math.cos(a), 2.6, COPPER)
    return finish(col, m)


TILES["dome"] = paint_dome()


def bar_tile(metal, seed, groove=3):
    W_, H_ = 96, 16
    a = np.zeros((H_, W_, 3), np.float32)
    r = np.random.default_rng(seed)
    for yy in range(H_):
        q = abs((yy + 0.5) / H_ - 0.5) * 2
        a[yy, :] = lerp(lerp(A(metal["hi"]) * 0.8, A(metal["low"]), q ** 1.1), A(metal["base"]), 0.45)
    a *= (0.92 + 0.16 * r.random((1, W_, 1), np.float32))
    for x in range(0, W_, W_ // groove):
        a[:, x:x + 2] = A(metal["base"]) * 0.62
    return finish(a, np.ones((H_, W_), bool))


def cap_tile(metal, hole=False):
    n = 16
    c = A(metal["base"]) * np.ones((n, n, 3), np.float32)
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2)
    c[r > 6.2] = A(metal["low"])
    if hole:                                    # bouche de cheminée : suie au centre, lèvre claire
        c[r < 6.0] = A(metal["hi"])
        c[r < 4.6] = A((30, 22, 18))
        c[r < 3.0] = A((14, 10, 9))
    else:
        c[r < 3] = A(metal["hi"])
    return finish(c, np.ones((n, n), bool))


def flat_tile(c, n=16, noise=0.1, seed=5):
    r = np.random.default_rng(seed)
    a = A(c) * (1 - noise / 2 + noise * r.random((n, n, 1), np.float32))
    return finish(a, np.ones((n, n), bool))


TILES.update(bar_brass=bar_tile(BRASS, 701), bar_steel=bar_tile(STEEL, 702), bar_copper=bar_tile(COPPER, 703, 4))
TILES.update(cap_brass=cap_tile(BRASS), cap_steel=cap_tile(STEEL), cap_copper=cap_tile(COPPER), mouth=cap_tile(COPPER, True))
TILES.update(edge=flat_tile(BRASS["hi"]), under=flat_tile((84, 58, 26)), roll=bar_tile(dict(hi=(252, 228, 160), base=(222, 178, 96), low=(140, 98, 44)), 705, 6))


def paint_cuir(W=64, H=20):
    """Sangle : cuir grainé, bords sombres, coutures en fil de laiton (tirets de 4 texels, 2 de haut)."""
    r = np.random.default_rng(91)
    c = lerp(A(CUIR["low"]), A(CUIR["base"]), 0.55 + 0.45 * cell_noise(H, W, 26, 92)[..., None])
    c *= (0.92 + 0.12 * r.random((H, W, 1), np.float32))
    c[:2], c[-2:] = A(CUIR["low"]) * 0.8, A(CUIR["low"]) * 0.8
    c[2] = A(CUIR["hi"])
    for y in (4, H - 6):
        for x in range(1, W, 7):
            c[y:y + 2, x:x + 4] = A((214, 176, 96))
            c[y + 2, x:x + 4] = A(CUIR["low"]) * 0.7
    return finish(c, np.ones((H, W), bool))


TILES["cuir"] = paint_cuir()


def paint_buckle(W=24, H=28):
    c = A(BRASS["base"]) * np.ones((H, W, 3), np.float32)
    c[:3], c[:, :3] = A(BRASS["hi"]), A(BRASS["hi"])
    c[-3:], c[:, -3:] = A(BRASS["low"]), A(BRASS["low"])
    c[7:H - 7, 7:W - 7] = A(CUIR["base"])                # fenêtre : on voit le cuir
    c[7:H - 7, W // 2 - 1:W // 2 + 2] = A(STEEL["hi"])  # ardillon
    return finish(c, np.ones((H, W), bool))


TILES["buckle"] = paint_buckle()


def paint_bracket(W=48, H=30):
    c = A(BRASS_D["base"]) * np.ones((H, W, 3), np.float32)
    nz = cell_noise(H, W, 12, 77)
    c[nz > 0.7] = PATINA
    d = inset(np.ones((H, W), bool) & np.pad(np.ones((H - 2, W - 2), bool), 1), 4)
    c[d < 2] = A(BRASS["hi"])
    for x, y in ((5, 5), (W - 5, 5), (5, H - 5), (W - 5, H - 5)):
        rivet(c, x, y, 2.2, STEEL)
    return finish(c, np.ones((H, W), bool))


TILES["bracket"] = paint_bracket()


def paint_gear(n, teeth, metal, seed, spokes=None, hole=0.18, h_t=0.14):
    """Engrenage découpé par alpha ; une dent vers la droite de l'image (angle 0), puis tous les 360/teeth."""
    ss = 4
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    dx, dy = (xx + 0.5 - N / 2) / (N / 2), -(yy + 0.5 - N / 2) / (N / 2)
    r, th = np.hypot(dx, dy), np.degrees(np.arctan2(dy, dx))
    pitch = 360 / teeth
    q = np.abs(((th + pitch / 2) % pitch) - pitch / 2) / pitch
    ro, rr = 0.98, 0.98 * (1 - h_t)
    m = (r <= rr + (ro - rr) * np.clip((0.40 - q) / 0.17, 0, 1)) & (r >= hole)
    if spokes:
        ang = (th + 180 / spokes) % (360 / spokes) / (360 / spokes)
        m &= ~((r > 0.40) & (r < rr - 0.17) & (np.abs(ang - 0.5) < 0.26))
    mask = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((n, n), Image.LANCZOS)) > 110
    r, _ = polar(n)
    col = A(metal["base"]) * np.ones((n, n, 3), np.float32)
    nz = cell_noise(n, n, 10, seed)
    col *= (0.86 + 0.28 * nz)[..., None]
    col[r > rr - 0.04] = A(metal["hi"])
    col[(r > rr - 0.14) & (r <= rr - 0.06)] *= 0.55
    col[r < hole + 0.12] = A(metal["hi"]) * 0.9
    if metal is BRASS:
        col[(nz > 0.80) & (r < rr - 0.15)] = PATINA
    return finish(col, mask)


G12_T, G6_T = 12, 6
TILES["g12"] = paint_gear(64, G12_T, BRASS, 601, spokes=4)
TILES["g6"] = paint_gear(40, G6_T, STEEL, 602, hole=0.22, h_t=0.24)
R12_OUT, R6_OUT = 1.5, 0.9
PITCH_D = R12_OUT * 0.98 * (1 - 0.14 / 2) + R6_OUT * 0.98 * (1 - 0.24 / 2) - 0.02


def paint_dial(n=64):
    """Cadran : verre ambre éclairé par derrière, graduations de -120° à +120° (sens horaire), zone rouge au maximum."""
    m = disc_mask(n, 0.99)
    r, a = polar(n)
    col = lerp(A((252, 226, 160)), A((222, 156, 62)), np.clip(r, 0, 1)[..., None] ** 1.5)
    glow = m & (r < 0.92)
    red = (a > 78) & (a < 120) & (r > 0.70) & (r < 0.86)
    col[red] = A((176, 36, 26))
    ticks = np.zeros((n, n), bool)
    for k in range(25):
        ang = -120 + 10 * k
        major = k % 3 == 0
        d = np.abs(((a - ang + 180) % 360) - 180) * np.pi / 180 * r * n / 2
        ticks |= (d < (1.3 if major else 0.75)) & (r > (0.60 if major else 0.72)) & (r < 0.88)
    col[ticks] = A((44, 26, 14))
    col[r > 0.92] = A(BRASS["low"]) * 0.6
    col[(r < 0.11)] = A((60, 40, 20))
    e = np.zeros((n, n, 3), np.float32)
    e[glow & ~ticks] = (64, 40, 12)                 # lueur douce et chaude
    e[glow & ~ticks & (r < 0.5)] = (78, 50, 16)
    e[red & ~ticks] = (70, 14, 8)
    return finish(col, m), e, m


DIAL, DIAL_E, DIAL_M = paint_dial()
TILES["dial"] = DIAL


def paint_bezel(n=72, r_in=0.80):
    m = disc_mask(n, 0.985, r_in)
    r, a = polar(n)
    col = A(BRASS["base"]) * np.ones((n, n, 3), np.float32)
    col *= (0.86 + 0.3 * np.clip((r - r_in) / (1 - r_in), 0, 1))[..., None]
    col[r < r_in + 0.04] = A(BRASS["low"]) * 0.6
    col[(r > 0.90) & (r < 0.94)] = A(BRASS["hi"])
    for k in range(4):
        ang = math.radians(45 + 90 * k)
        rivet(col, n / 2 + 0.895 * n / 2 * math.sin(ang), n / 2 - 0.895 * n / 2 * math.cos(ang), 2.2, STEEL)
    return finish(col, m)


TILES["bezel"] = paint_bezel()


def paint_glass(n=56):
    """Verre : ambre très léger (alpha 54), reflet en croissant (alpha 112). Tout sous 128 : invisible en cutout."""
    ss = 4
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    u, v = (xx + 0.5) / N * 2 - 1, (yy + 0.5) / N * 2 - 1
    r = np.hypot(u, v)
    alpha = np.where(r < 0.97, 54.0, 0.0)
    cres = (r < 0.80) & (r > 0.58) & (np.degrees(np.arctan2(u, -v)) < -20) & (np.degrees(np.arctan2(u, -v)) > -95)
    alpha[cres] = 112.0
    al = np.array(Image.fromarray(alpha.astype(np.uint8), "L").resize((n, n), Image.NEAREST))
    c = np.empty((n, n, 3), np.float32)
    c[...] = (255, 212, 136)
    cr = np.array(Image.fromarray((cres * 255).astype(np.uint8), "L").resize((n, n), Image.NEAREST)) > 127
    c[cr] = (255, 246, 222)
    out = finish(c, al > 0, alpha=al)
    return out


TILES["glass"] = paint_glass()


def paint_needle(W=16, H=64):
    """Aiguille : pivot au centre de l'image, pointe vers le haut (bout rouge), queue courte à contrepoids."""
    ss = 4
    im = Image.new("L", (W * ss, H * ss), 0)
    d = ImageDraw.Draw(im)
    cx, cy = W * ss / 2, H * ss / 2
    d.polygon([(cx - 2.2 * ss, cy), (cx - 0.7 * ss, 3 * ss), (cx + 0.7 * ss, 3 * ss), (cx + 2.2 * ss, cy)], fill=255)
    d.polygon([(cx - 1.6 * ss, cy), (cx + 1.6 * ss, cy), (cx + 1.2 * ss, cy + 9 * ss), (cx - 1.2 * ss, cy + 9 * ss)], fill=255)
    d.ellipse((cx - 3.4 * ss, cy + 6 * ss, cx + 3.4 * ss, cy + 12.8 * ss), fill=255)
    d.ellipse((cx - 3.2 * ss, cy - 3.2 * ss, cx + 3.2 * ss, cy + 3.2 * ss), fill=255)
    m = np.array(im.resize((W, H), Image.LANCZOS)) > 110
    yy = np.arange(H)[:, None] * np.ones((1, W))
    col = np.empty((H, W, 3), np.float32)
    col[...] = (34, 30, 30)
    col[yy < 15] = (196, 40, 28)
    col[(np.abs(yy - H / 2) < 2.5) & (np.abs(np.arange(W)[None, :] - W / 2 + 0.5) < 2.5)] = BRASS["hi"]
    return finish(col, m)


TILES["needle"] = paint_needle()


def paint_steam(W=64, H=96):
    """Bouffée de vapeur : lobes qui s'élargissent en montant ; opacité en dégradé (1–254), dense en bas.
    Le cœur au-dessus de 50 % garde une silhouette de bouffée en cutout."""
    ss = 3
    w, h = W * ss, H * ss
    yy, xx = np.mgrid[0:h, 0:w]
    x, y = (xx + 0.5) / w, 1 - (yy + 0.5) / h                 # y = 0 en bas (bouche), 1 en haut
    lobes = [(0.50, 0.08, 0.13), (0.43, 0.24, 0.20), (0.60, 0.36, 0.22), (0.42, 0.52, 0.25), (0.60, 0.68, 0.24),
             (0.44, 0.82, 0.20), (0.62, 0.90, 0.13)]
    dens = np.zeros((h, w), np.float32)
    lit = np.zeros((h, w), np.float32)
    for lx, ly, lr in lobes:
        dd = np.hypot((x - lx) * 1.0, (y - ly) * 1.5) / lr
        dens = np.maximum(dens, np.clip(1 - dd ** 2, 0, 1) ** 0.6)
        lit = np.maximum(lit, np.clip(1 - np.hypot(x - lx + 0.3 * lr, (y - ly - 0.3 * lr) * 1.5) / lr, 0, 1))
    al = np.clip(dens * 1.35, 0, 1) * (1 - 0.62 * y) * 254
    al = np.array(Image.fromarray(al.astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(np.float32)
    al[al < 6] = 0
    l = np.array(Image.fromarray((lit * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS), np.float32)[..., None] / 255
    c = lerp(A((206, 212, 220)), A((250, 250, 248)), np.clip(l * 1.6, 0, 1))
    return finish(c, al > 0, alpha=np.clip(al, 0, 254).astype(np.uint8))


TILES["steam"] = paint_steam()

# ------------------------------------------------------------------ atlas
SEMI = {"glass", "steam"}


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
for n_, im in TILES.items():
    u0, v0, u1, v1 = UV[n_]
    tex[v0:v1, u0:u1] = im
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
u0, v0, u1, v1 = UV["dial"]
tex_e[v0:v1, u0:u1, :3] = DIAL_E.astype(np.uint8)
tex_e[v0:v1, u0:u1, 3] = (DIAL_E.max(axis=2) > 0) * 255
tex[..., :3] &= 0xFC
tex[tex[..., 3] == 0] = 0
semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
zone = np.zeros(semi.shape, bool)
for n_ in SEMI:
    u0, v0, u1, v1 = UV[n_]
    zone[v0:v1, u0:u1] = True
assert not (semi & ~zone).any(), "semi-transparence hors des images trans_"
assert set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence _e"


def b64png(arr, fn):
    im = Image.fromarray(arr, "RGBA")
    im.save(fn, optimize=True)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


# Masque de reflets _r (guide 5 quater, lu par face) : laiton poli clair, cuivre et acier moyens, cuir et cadran mats.
REFLET = {"dome": 210, "s_ring": 190, "s_l1": 170, "s_l2": 150, "s_l3": 170, "bar_brass": 190, "cap_brass": 190, "edge": 200,
          "roll": 220, "bezel": 210, "g12": 170, "bracket": 120, "buckle": 170, "bar_copper": 150, "cap_copper": 150, "mouth": 60,
          "bar_steel": 120, "cap_steel": 120, "g6": 120, "needle": 40, "dial": 50, "under": 20, "cuir": 15, "glass": 0, "steam": 0}
tex_r = np.zeros((TEX, TEX, 4), np.uint8)
for n_, val in REFLET.items():
    u0, v0, u1, v1 = UV[n_]
    op = tex[v0:v1, u0:u1, 3] == 255
    tex_r[v0:v1, u0:u1, :3] = np.where(op[..., None], val, 0)
    tex_r[v0:v1, u0:u1, 3] = op * 255
assert set(UV) == set(REFLET), set(UV) ^ set(REFLET)
tex_b64, tex_e_b64, tex_r_b64 = b64png(tex, f"{NOM}.png"), b64png(tex_e, f"{NOM}_e.png"), b64png(tex_r, f"{NOM}_r.png")

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
    """Angles (X, Y, Z) tels que R = Rz Ry Rx (ordre du mod et du renderer)."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def frame(X=None, Y=None):
    """Repère orthonormé direct ; X prioritaire si Y n'est pas donné, sinon Y prioritaire."""
    if Y is not None:
        Y = unit(Y)
        X = unit(X - (X @ Y) * Y)
    else:
        X = unit(X)
        Y = unit(V(0, 1, 0) - X[1] * X) if abs(X[1]) < 0.95 else unit(V(1, 0, 0) - X[0] * X)
    return np.column_stack([X, Y, np.cross(X, Y)])


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
    return e


def T(name):
    return list(UV[name])


def flip(uv):
    return [uv[2], uv[1], uv[0], uv[3]]


def box(g, name, c, R, size, faces):
    """Cube centré en c, axes locaux = colonnes de R, taille (w, h, th) selon X, Y, Z locaux."""
    c = np.asarray(c, float)
    s = np.asarray(size, float) / 2
    return cube(g, name, c - s, c + s, c, euler(R), faces)


def bar(g, name, p, q, r, mat, u0=0.0, u1=1.0, octo=True, ov=0.0, end_p=None, end_q=None):
    """Tronçon de p à q : section octogonale (deux cubes à 45°) ou losange seul."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = float(np.linalg.norm(q - p))
    X = unit(q - p)
    ref = V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0)
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R0 = np.column_stack([X, Y, Z_])
    R45 = np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])
    bu0, bv0, bu1, bv1 = UV[f"bar_{mat}"]
    ua = lerp(bu0, bu1, u0)
    lg = [ua, bv0, max(lerp(bu0, bu1, u1), ua + 2), bv1]
    ep, eq = end_p or T(f"cap_{mat}"), end_q or T(f"cap_{mat}")
    faces = {"south": lg, "north": lg, "up": lg, "down": lg, "west": ep, "east": eq}
    if octo:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R0), faces)
        cube(g, name + "o", p + (-ov + 0.03, -r * 0.97, -r * 0.97), p + (L + ov - 0.03, r * 0.97, r * 0.97), p, euler(R45), faces)
    else:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R45), faces)


def disc_x(g, name, c, r, th, tile, phase=0.0):
    """Disque découpé dans le plan YZ (repère canonique, face visible = west, -X) ; phase = rotation autour de X."""
    c = np.asarray(c, float)
    cube(g, name, c - (th / 2, r, r), c + (th / 2, r, r), c, (phase, 0, 0),
         {"west": T(tile), "east": flip(T(tile)), "north": CLEAR, "south": CLEAR, "up": CLEAR, "down": CLEAR})


# ------------------------------------------------------------------ lames : contours en tuiles autour du bras
AXE = 6.0                                    # axe du bras (|x|), section 4 x 4 (guide : bras de 4 x 12 x 4)
THETAS = [-90, -60, -30, 0, 30, 60, 90]      # 0 = côté extérieur, -90 = avant (-Z), +90 = arrière (+Z)
INNER_A = -1.52                              # bord intérieur des facettes avant/arrière : x = 4,48 (tête et torse épargnés)
TH = 0.5                                     # épaisseur des lames


def support(t):
    return 2 * (abs(math.cos(math.radians(t))) + abs(math.sin(math.radians(t))))


def contour(c, circle=None):
    """Points (a, b) du contour : a vers l'extérieur depuis l'axe, b = z. Lignes d'appui du carré du bras + jeu c
    (ou cercle de rayon `circle`). Extrémités avant et arrière prolongées vers l'intérieur jusqu'à INNER_A."""
    off = [circle if circle else support(t) + c for t in THETAS]
    n = [(math.cos(math.radians(t)), math.sin(math.radians(t))) for t in THETAS]
    pts = [(INNER_A, -off[0])]
    for i in range(len(THETAS) - 1):
        (a1, b1), (a2, b2) = n[i], n[i + 1]
        det = a1 * b2 - a2 * b1
        pts.append(((off[i] * b2 - off[i + 1] * b1) / det, (a1 * off[i + 1] - a2 * off[i]) / det))
    pts.append((INNER_A, off[-1]))
    return pts


def P3(s, a, b, y):
    return V(s * (AXE + a), y, b)


def rise_f(a, b):
    """0 côté extérieur, 1 à l'avant et à l'arrière : le bord des lames remonte en arc, comme une vraie épaulière."""
    return min(1.0, abs(math.degrees(math.atan2(b, a))) / 90) ** 1.5


LAMES = {}      # (s, k) -> dict(top=(c, y), bot=(c, y))


def tuck(c_e, y_e, c_top, y_top, ins=0.55):
    """Haut de la lame suivante : à `ins` à l'intérieur du bord bas de la précédente, sous son épaisseur (calcul à θ = 0)."""
    dA, dy = c_e - c_top, y_top - y_e
    al = math.atan2(dA, dy)
    m = TH + 0.08
    return c_e - ins * math.sin(al) - m * math.cos(al), y_e + ins * math.cos(al) - m * math.sin(al)


def lame(s, g, name, top, bot, strip, roll=False, circle_top=None, rise=(0.0, 0.0)):
    """Une lame = 7 facettes pleines qui suivent le contour ; la bande `strip` se déroule le long des facettes."""
    (ct, yt), (cb, yb) = top, bot
    Pt = contour(ct, circle_top)
    Pb = contour(cb)
    seg = [math.dist(Pb[i], Pb[i + 1]) for i in range(len(Pb) - 1)]
    U = np.concatenate([[0], np.cumsum(seg)]) / sum(seg)
    su0, sv0, su1, sv1 = UV[strip]
    for i in range(len(THETAS)):
        t0, t1 = (P3(s, *Pt[j], yt + rise[0] * rise_f(*Pt[j])) for j in (i, i + 1))
        b0, b1 = (P3(s, *Pb[j], yb + rise[1] * rise_f(*Pb[j])) for j in (i, i + 1))
        X = unit(b1 - b0)
        Tm, Bm = (t0 + t1) / 2, (b0 + b1) / 2
        Yr = Tm - Bm
        Y = unit(Yr - (Yr @ X) * X)
        R = np.column_stack([X, Y, np.cross(X, Y)])
        th = math.radians(THETAS[i])
        out = V(s * math.cos(th), 0, math.sin(th))
        Zo = R[:, 2] if R[:, 2] @ out > 0 else -R[:, 2]
        xs = [(q - Bm) @ X for q in (t0, t1, b0, b1)]
        ys = [(q - Bm) @ Y for q in (t0, t1, b0, b1)]
        w = max(xs) - min(xs) + 0.24
        h = max(ys) - min(ys) + 0.12
        Cc = Bm + X * ((max(xs) + min(xs)) / 2) + Y * ((max(ys) + min(ys)) / 2) + R[:, 2] * (((Tm + Bm) / 2 - Bm) @ R[:, 2])
        ua, ub = lerp(su0, su1, U[i]), lerp(su0, su1, U[i + 1])
        face_out = [ua, sv0, ub, sv1]
        outer_is_south = R[:, 2] @ out > 0
        faces = {"south": face_out if outer_is_south else T("under"), "north": T("under") if outer_is_south else flip(face_out),
                 "up": T("under"), "down": T("edge"), "east": T("edge"), "west": T("edge")}
        box(g, f"{name}_f{i}", Cc + Zo * (TH / 2), R, (w, h, TH), faces)
        if roll:
            q0, q1 = b0 + Zo * (TH * 0.55) - Y * 0.04, b1 + Zo * (TH * 0.55) - Y * 0.04
            bar(g, f"{name}_r{i}", q0, q1, 0.3, "steel", octo=False, ov=0.1, end_p=T("edge"), end_q=T("edge"))
            elements[-1]["faces"].update({f: {"uv": [round(v, 2) for v in T("roll")], "texture": 0} for f in ("south", "north", "up", "down")})


def surface(s, k, t, frac):
    """Point de la face extérieure de la lame k (0 = couronne du dôme) à l'angle t, fraction frac du haut vers le bas,
    et normale extérieure (inclinée par l'évasement)."""
    (ct, yt), (cb, yb) = LAMES[(s, k)]["top"], LAMES[(s, k)]["bot"]
    c = lerp(ct, cb, frac)
    th = math.radians(t)
    rt, rb = LAMES[(s, k)]["rise"]
    f = min(1.0, abs(t) / 90) ** 1.5
    y = lerp(yt + rt * f, yb + rb * f, frac)
    off = support(t) + c + TH
    al = math.atan2(cb - ct, yt - yb)
    n = V(s * math.cos(th) * math.cos(al), math.sin(al), math.sin(th) * math.cos(al))
    return V(s * (AXE + off * math.cos(th)), y, off * math.sin(th)), unit(n)


def sangle(s, g, tag, y0, y1):
    """Brassard de cuir cousu sous l'épaulière : avant, extérieur, arrière (le côté du torse reste nu), boucle de laiton."""
    cy, h = (y0 + y1) / 2, y1 - y0
    cu = T("cuir")
    fz = {"north": cu, "south": cu, "up": T("under"), "down": T("under"), "east": cu, "west": cu}
    xo = s * (AXE + 2.0 + 0.2)
    cube(g, f"sg_av_{tag}", [min(s * 4.38, s * 8.42), y0, -2.42], [max(s * 4.38, s * 8.42), y1, -2.02], [s * 6, cy, -2.2], (0, 0, 0), fz)
    cube(g, f"sg_ar_{tag}", [min(s * 4.38, s * 8.42), y0, 2.02], [max(s * 4.38, s * 8.42), y1, 2.42], [s * 6, cy, 2.2], (0, 0, 0), fz)
    cube(g, f"sg_ex_{tag}", [min(xo - 0.2, xo + 0.2), y0 + 0.02, -2.4], [max(xo - 0.2, xo + 0.2), y1 - 0.02, 2.4], [xo, cy, 0], (0, 0, 0), fz)
    bk = T("buckle")
    cube(g, f"sg_boucle_{tag}", [min(xo, xo + s * 0.42), cy - h * 0.62, -0.62], [max(xo, xo + s * 0.42), cy + h * 0.62, 0.62], [xo, cy, 0], (0, 0, 0),
         {"north": T("edge"), "south": T("edge"), "up": T("edge"), "down": T("edge"), "east": bk, "west": bk})
    return xo


def epauliere(s, tag, dome_y, dome_r, ring_bot, heights, flares, strap, rises):
    arm = group("left_arm" if s < 0 else "right_arm", V(s * 5, 22, 0))
    ep = group(f"epauliere_{tag}", V(s * 5, 22, 0), parent=arm)
    # dôme : disque découpé, âme octogonale qui remplit le dessous, couronne de facettes qui descend vers les lames
    dm = group(f"dome_{tag}", V(s * AXE, dome_y, 0), parent=ep)
    c0 = V(s * AXE, dome_y + 0.45, 0)
    cube(dm, f"dome_disque_{tag}", c0 - (dome_r, 0.2, dome_r), c0 + (dome_r, 0.2, dome_r), c0, (0, 0, 0),
         {"up": T("dome"), "down": T("under"), "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR})
    bar(dm, f"dome_ame_{tag}", V(s * AXE, 23.9, 0), V(s * AXE, dome_y + 0.3, 0), 1.17, "brass")
    ring_top = (None, dome_y)
    LAMES[(s, 0)] = dict(top=(dome_r - 0.25 - 2.0, dome_y), bot=ring_bot, rise=(0.0, rises[0]))
    lame(s, dm, f"couronne_{tag}", (0.0, dome_y), ring_bot, "s_ring", roll=True, circle_top=dome_r - 0.25, rise=(0.0, rises[0]))
    prev = ring_bot
    prev_top = LAMES[(s, 0)]["top"]
    gs = []
    for k, (hk, fk) in enumerate(zip(heights, flares)):
        ct, yt = tuck(prev[0], prev[1], prev_top[0], prev_top[1])
        top, bot = (ct, yt), (ct + fk, yt - hk)
        LAMES[(s, k + 1)] = dict(top=top, bot=bot, rise=(rises[k], rises[k + 1]))
        g = group(f"lame{k + 1}_{tag}", V(s * AXE, yt, 0), parent=ep)
        lame(s, g, f"lame{k + 1}_{tag}", top, bot, ["s_l1", "s_l2", "s_l3"][k], roll=(k == len(heights) - 1), rise=(rises[k], rises[k + 1]))
        gs.append(g)
        prev, prev_top = bot, top
    # brassard et suspente : la suspente descend de sous la dernière lame jusqu'au brassard
    sg = group(f"sangle_{tag}", V(s * 6, strap[1], 0), parent=ep)
    xo = sangle(s, sg, tag, *strap)
    yb = LAMES[(s, len(heights))]["bot"][1]
    cu = T("cuir")
    cube(sg, f"sg_susp_{tag}", [min(xo - s * 0.1, xo + s * 0.3), strap[1] - 0.1, -0.5], [max(xo - s * 0.1, xo + s * 0.3), yb + 1.2, 0.5],
         [xo, strap[1], 0], (0, 0, 0), {f: cu for f in ("north", "south", "east", "west", "up", "down")})
    return arm, ep, gs


# ---- droite : la grande, cheminées
ARM_R, EP_R, LAMES_R = epauliere(1, "r", 25.15, 1.72, (0.80, 24.55), (2.1, 2.05, 2.05), (1.05, 1.12, 1.22), (16.8, 18.15), (0.25, 0.6, 0.95, 1.25))
# ---- gauche : la petite, manomètre et engrenage
ARM_L, EP_L, LAMES_L = epauliere(-1, "l", 24.95, 1.58, (0.62, 24.45), (1.85, 1.8, 1.75), (0.9, 0.95, 1.0), (17.5, 18.75), (0.2, 0.5, 0.8, 1.05))

# ------------------------------------------------------------------ droite : chaudière, cheminées, soupape, vapeur
CH = group("chaudiere_r", V(7.4, 23.45, 3.62), parent=EP_R)
DR_Y, DR_Z, DR_R = 23.45, 3.62, 0.95
bar(CH, "tambour", V(5.95, DR_Y, DR_Z), V(8.95, DR_Y, DR_Z), DR_R, "copper")
bar(CH, "cercle0", V(5.85, DR_Y, DR_Z), V(6.3, DR_Y, DR_Z), DR_R + 0.13, "brass")
bar(CH, "cercle1", V(8.6, DR_Y, DR_Z), V(9.05, DR_Y, DR_Z), DR_R + 0.13, "brass")

DIR_C = [unit(V(0.10, 1, 0.46)), unit(V(0.22, 1, 0.40))]
BASES = [V(6.75, DR_Y + DR_R - 0.25, DR_Z), V(8.15, DR_Y + DR_R - 0.25, DR_Z)]
LEN_C = [5.0, 4.1]
CHEM, MOUTH, RC = [], [], []
EMIT_NAME = "emit_mc_white_smoke"
for k in range(2):
    d, B, L = DIR_C[k], BASES[k], LEN_C[k]
    g = group(f"cheminee{k + 1}_r", B, parent=CH)
    CHEM.append(g)
    bar(g, f"bride{k}", B - d * 0.05, B + d * 0.45, 0.78, "brass")
    bar(g, f"fut{k}", B, B + d * (L - 0.35), 0.52, "copper", 0.0, 0.8)
    bar(g, f"collier{k}", B + d * (L * 0.52), B + d * (L * 0.52 + 0.4), 0.64, "brass")
    bar(g, f"col{k}", B + d * (L - 0.75), B + d * (L - 0.2), 0.66, "copper")
    bar(g, f"chapeau{k}", B + d * (L - 0.25), B + d * (L + 0.12), 0.84, "copper", end_q=T("mouth"))
    M = B + d * (L + 0.12)
    MOUTH.append(M)
    R_c = frame(X=V(1, 0, 0), Y=d)
    RC.append(R_c)
    gname = EMIT_NAME if k == 0 else EMIT_NAME + "@2"      # même nom dans le modèle (voir plus bas), clé interne distincte
    group(gname, M + d * 0.25, parent=g, rotation=euler(R_c))
    # jet d'attaque : 2 plaques croisées rangées DANS le fût, que l'attaque agrandit (x 3,6) et fait sortir
    J0 = M - d * 1.25
    jg = group(f"trans_jet_{k + 1}", J0, parent=g, rotation=euler(R_c))
    for j, a in enumerate((0, 90)):
        cube(jg, f"jet{k}_{j}", J0 + V(-0.4, 0.05, -0.05), J0 + V(0.4, 1.15, 0.05), J0, (0, a + 20 * k, 0),
             {"south": T("steam"), "north": flip(T("steam")), "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})

# soupape à levier, entre les deux cheminées : le levier se soulève à la décharge
SV = V(7.45, DR_Y + DR_R - 0.2, DR_Z - 0.15)
SP = group("soupape_r", SV, parent=CH)
bar(SP, "soup_corps", SV, SV + V(0, 0.95, 0), 0.34, "brass")
LV = SV + V(0, 0.95, 0)
LG = group("levier_r", LV, parent=SP)
bar(LG, "levier", LV + V(-0.3, 0.05, 0), LV + V(1.55, 0.05, 0), 0.14, "steel", octo=False)
bar(LG, "contrepoids", LV + V(1.25, 0.05, 0), LV + V(1.75, 0.05, 0), 0.3, "brass")

# bouffées des états : 3 plaques croisées par cheminée, sous un même groupe trans_ (un seul ctrl_alpha)
TV = group("trans_vapeur_r", V(7.4, 27, 4), parent=EP_R)
group("ctrl_alpha", V(7.4, 27, 4), parent=TV)
PUFF = []
for k in range(2):
    M = MOUTH[k]
    g = group(f"vapeur{k + 1}_r", M, parent=TV, rotation=euler(RC[k]))
    PUFF.append(g)
    for j, a in enumerate((0, 60, 120)):
        cube(g, f"vap{k}_{j}", M + V(-1.5, 0.06, -0.15 + 0.01 * j), M + V(1.5, 4.3, 0.15 + 0.01 * j), M, (0, a + 15 * k, 0),
             {"south": T("steam"), "north": flip(T("steam")), "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})

# ------------------------------------------------------------------ gauche : manomètre, tuyau, engrenages
gp, gn = surface(-1, 1, -32, 0.12)
N_G = unit(gn + V(0, 0.18, -0.12))
B_G = gp - N_G * 0.25
R_G = frame(X=-N_G)
MN = group("manometre_l", B_G, parent=EP_L, rotation=euler(R_G))
O = B_G
bar(MN, "boitier", O + V(0.45, 0, 0), O + V(-0.88, 0, 0), 1.42, "brass", end_q=T("cap_brass"))
disc_x(MN, "cadran", O + V(-0.97, 0, 0), 1.32, 0.3, "dial")
disc_x(MN, "lunette", O + V(-1.22, 0, 0), 1.64, 0.5, "bezel", 22.5)
cube(MN, "moyeu", O + V(-1.58, -0.17, -0.17), O + V(-1.26, 0.17, 0.17), O + V(-1.42, 0, 0), (0, 0, 0), {f: T("cap_brass") for f in ("north", "south", "east", "west", "up", "down")})
bar(MN, "raccord", O + V(-0.2, -1.3, 0.0), O + V(-0.2, -1.95, 0.0), 0.36, "brass")
NE = group("aiguille_l", O + V(-1.27, 0, 0), parent=MN)
cube(NE, "aiguille", O + V(-1.27 - 0.15, -1.2, -0.3), O + V(-1.27 + 0.15, 1.2, 0.3), O + V(-1.27, 0, 0), (0, 0, 0),
     {"west": T("needle"), "east": flip(T("needle")), "north": CLEAR, "south": CLEAR, "up": CLEAR, "down": CLEAR})
VR = group("trans_verre_l", O + V(-1.72, 0, 0), parent=MN)
disc_x(VR, "verre", O + V(-1.72, 0, 0), 1.36, 0.3, "glass")
# tuyau de pression : du raccord du manomètre, il file vers l'arrière et passe sous la lame 2
p0 = O + R_G @ V(-0.2, -1.9, 0.0)
q1, nq1 = surface(-1, 2, 10, 0.05)
p1 = q1 + nq1 * 0.35
p2 = p1 + V(0.25, -0.2, 1.4)
bar(EP_L, "tuyau0", p0, p1, 0.3, "copper", ov=0.1)
bar(EP_L, "tuyau1", p1, p2, 0.3, "copper", ov=0.1)
bar(EP_L, "tuyau_coll", p1 - unit(p1 - p0) * 0.3, p1 + unit(p1 - p0) * 0.1, 0.38, "brass")

mp, mn = surface(-1, 2, 22, 0.55)
R_M = frame(X=-mn)
B_M = mp - mn * 0.05
MC = group("meca_l", B_M, parent=EP_L, rotation=euler(R_M))
O = B_M
BETA = math.radians(64)                                  # le pignon est au-dessus et vers l'arrière de la roue
DIRP = V(0, math.sin(BETA), math.cos(BETA))
GC, PC = O + V(-0.55, -0.55, -0.35), None
PC = GC + DIRP * PITCH_D
mid = (GC + PC) / 2
Rb = np.column_stack([V(1, 0, 0), DIRP, np.cross(V(1, 0, 0), DIRP)])
box(MC, "platine", mid + V(-0.12, 0, 0), Rb, (0.3, PITCH_D + 2.2, 2.0), {f: T("bracket") for f in ("west", "east")} | {f: T("edge") for f in ("north", "south", "up", "down")})
phi_d = math.degrees(math.atan2(DIRP[1], DIRP[2]))       # angle image (depuis +Z vers +Y) du pignon vu de la roue
RG = group("roue_l", GC, parent=MC)
disc_x(RG, "roue", GC + V(-0.42, 0, 0), R12_OUT, 0.4, "g12", -phi_d)
bar(RG, "roue_moyeu", GC + V(0.1, 0, 0), GC + V(-0.86, 0, 0), 0.5, "steel")
PG = group("pignon_l", PC, parent=MC)
disc_x(PG, "pignon", PC + V(-0.47, 0, 0), R6_OUT, 0.4, "g6", -(phi_d + 180 + 180 / G6_T))
cube(PG, "pignon_axe", PC + V(-0.82, -0.3, -0.3), PC + V(0.1, 0.3, 0.3), PC, (0, 0, 0), {f: T("cap_steel") for f in ("north", "south", "east", "west", "up", "down")})


def bone(name):
    g = groups[name]
    return {"name": name.split("@")[0], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone(ARM_R), bone(ARM_L)]


# ------------------------------------------------------------------ garde-fous de placement (pose de base)
def corners(e):
    a, b = e["from"], e["to"]
    from itertools import product
    import numpy as _np
    o = _np.array(e["origin"], float)
    rx, ry, rz = map(math.radians, e.get("rotation", [0, 0, 0]))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    R = (_np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ _np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ _np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))
    return [R @ (_np.array(p, float) - o) + o for p in product(*zip(a, b))]


def world(name, p):
    """Point p d'un cube du groupe `name` après les rotations de base des groupes parents."""
    chain = []
    g = name
    while g:
        chain.append(g)
        g = groups[g]["parent"]
    for gname in chain:
        gg = groups[gname]
        o = np.array(gg["origin"], float)
        rx, ry, rz = map(math.radians, gg["rotation"])
        cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
        R = (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))
        p = R @ (p - o) + o
    return p


owner = {eid: g for g, gg in groups.items() for eid in gg["ids"]}
for e in elements:
    if e["name"].startswith("jet"):
        continue
    for p in corners(e):
        w = world(owner[e["uuid"]], p)
        assert not (abs(w[0]) < 4.2 and abs(w[2]) < 4.2 and w[1] > 24.0), f"{e['name']} dans la tête : {w}"
        assert not (abs(w[0]) < 4.0 and w[1] > 12), f"{e['name']} dans le torse : {w}"
        if w[1] > 25.9:
            assert math.hypot(w[0], w[2]) > 5.9, f"{e['name']} trop près de la tête qui tourne : {w}"


# ------------------------------------------------------------------ animations
def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 3)), "y": str(round(y + 0.0, 3)), "z": str(round(z + 0.0, 3))}],
            "time": round(t, 4), "interpolation": "linear"}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def servo(x, w=30.0, z=0.55):
    """Réponse indicielle d'un servo sous-amorti : 0 avant x = 0, dépasse un peu 1 puis s'y stabilise."""
    if x <= 0:
        return 0.0
    wd = w * math.sqrt(1 - z * z)
    return 1 - math.exp(-z * w * x) * (math.cos(wd * x) + z / math.sqrt(1 - z * z) * math.sin(wd * x))


def kick(x, up=0.09, w=30.0, z=0.45):
    """Cran : à-coup bref (montée servo, retour servo) avec rebond, revient à 0."""
    return servo(x, w, z) - servo(x - up, w * 0.8, z)


def anim(name, length, tracks, loop="loop", fps=FPS):
    """tracks : {groupe: [(canal, f(t) -> (x, y, z))]} ; interpolation linéaire, dernier keyframe = premier pour les boucles."""
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A_ = {}
    for g, chans in tracks.items():
        kfs = []
        for ch, f in chans:
            vals = [f(t) for t in times]
            kfs += [kf(ch, t, *v) for t, v in zip(times, vals)]
        A_[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 30,
            "selected": name == "idle", "animators": A_}


# MIROIR D'AXES (guide, section 3) : +Z = le côté droit monte. Une lame qui « se soulève » vers l'extérieur :
# +Z à droite (s = +1), -Z à gauche. Seul endroit à toucher si la convention change.
def lift(s, deg):
    return 0.0, 0.0, s * deg


# Aiguille : rotation autour de l'axe du cadran (X du repère du manomètre) ; +X = sens horaire vu de face (calculé :
# l'image du cadran a +Z à droite sur la face west). Pression 0 -> -120°, 1 -> +120°.
def needle_rot(P):
    return 240.0 * (P - 0.5), 0.0, 0.0


def pressure(t, steps, trem, td, drop_w=24.0, drop_z=0.62, base=0.0):
    """Montée par paliers (servo), tremblement au maximum, décharge brutale avec rebond sur la butée."""
    Pb = base + sum(dp * servo(t - ti, 30, 0.5) for ti, dp in steps)
    if td is None:
        return Pb
    tr = 0.028 * math.sin(TAU * 13 * t) * bump(t, trem - 0.06, trem + 0.08, td - 0.04, td + 0.01)
    return base + (Pb - base) * (1 - servo(t - td, drop_w, drop_z)) + tr


def puff_scale(x, k=1.0, big=1.0):
    """Bouffée : jaillit (0 -> 1 en 0,15 s), s'étire, se résorbe. x = temps depuis le jet."""
    u = x / k
    if u <= 0 or u >= 1.08:
        return 0.0, 0.0, 0.0
    g = 1.12 * (1 - (1 - min(u / 0.15, 1)) ** 2.4) - 0.12 * sm(u, 0.15, 0.26)
    st = sm(u, 0.22, 0.85)
    out = 1 - sm(u, 0.78, 1.06)
    return big * g * (1 + 0.45 * st) * out, big * g * (1 + 0.75 * st) * out, big * g * (1 + 0.45 * st) * out


def puff_pos(x, k=1.0):
    u = x / k
    if u <= 0 or u >= 1.08:
        return 0.0, 0.0, 0.0
    return 0.0, 1.6 * sm(u, 0.1, 1.0), 0.25 * sm(u, 0.2, 1.0)


def puff_alpha(x, k=1.0):
    """ctrl_alpha (guide : 1 + position) : 0 = opaque, -1 = invisible."""
    u = x / k
    if u <= 0 or u >= 1.08:
        return 0.0, 0.0, 0.0
    return -sm(u, 0.32, 0.98), 0.0, 0.0


def state(name, L, steps, trem, td, k_puff, lame_amp=1.0, extra=None):
    """Cycle de pression partagé : aiguille, soupape, décharge par les deux cheminées (la 2 un peu après), crans des lames."""
    D2 = 0.07 * k_puff
    tr = {}
    tr["aiguille_l"] = [("rotation", lambda t: needle_rot(pressure(t, steps, trem, td)))]
    lev = lambda t: 3.0 * math.sin(TAU * 17 * t) * bump(t, trem - 0.06, trem + 0.08, td - 0.04, td) + \
        26 * (servo((t - td + 0.03) % L, 26, 0.4) - servo((t - td + 0.03) % L - 0.36 * k_puff, 20, 0.45))
    tr["levier_r"] = [("rotation", lambda t: lift(1, lev(t)))]
    for k, g in enumerate(CHEM):
        dk = td + D2 * k
        tr[g] = [("rotation", lambda t, dk=dk: (2.6 * kick((t - dk) % L), 0.0, 0.0))]
    for k, g in enumerate(PUFF):
        dk = td + D2 * k
        tr[g] = [("scale", lambda t, dk=dk: puff_scale((t - dk) % L, k_puff)), ("position", lambda t, dk=dk: puff_pos((t - dk) % L, k_puff))]
    tr["ctrl_alpha"] = [("position", lambda t: puff_alpha((t - td) % L, k_puff))]
    for s, gs in ((1, LAMES_R), (-1, LAMES_L)):
        for j, g in enumerate(gs):
            a = lame_amp * (1.0 + 0.6 * j) * (1.0 if s > 0 else 0.6)
            dj = td + 0.03 * j + (0.0 if s > 0 else 0.05)
            tr[g] = [("rotation", lambda t, a=a, dj=dj, s=s: lift(s, a * kick((t - dj) % L))),
                     ("position", lambda t, a=a, dj=dj: (0.0, 0.05 * a * kick((t - dj) % L), 0.0))]
    if extra:
        extra(tr)
    return sound(anim(name, L, tr), [td])


def sound(a, times, name="block.fire.extinguish"):
    """Sifflement de vapeur à la décharge (guide 6.5 : clé sound de la piste Effets)."""
    a["animators"]["effects"] = {"name": "Effects", "type": "effect",
                                 "keyframes": [{"channel": "sound", "data_points": [{"effect": name, "file": ""}], "time": round(t, 3)} for t in times]}
    return a


def ticks(t0, period, n, sizes):
    return [(t0 + i * period, sizes[i]) for i in range(n)]


def norm_steps(raw, total):
    s = sum(raw)
    return [r / s * total for r in raw]


# idle 4 s : une décharge par boucle. La pression monte en 6 paliers (1 tic sur 2 de l'échappement à 1/3 s).
idle = state("idle", 4.0, ticks(0.33, 0.333, 6, norm_steps([5, 4.4, 3.8, 3.2, 2.6, 2.0], 0.93)), 2.35, 2.95, 1.0)
# walk 2,4 s : décharge plus fréquente, 5 paliers plus rapprochés
walk = state("walk", 2.4, ticks(0.15, 0.2, 5, norm_steps([5, 4.2, 3.4, 2.6, 2.0], 0.93)), 1.15, 1.5, 0.85)
# run 1,2 s : la pression monte vite (4 paliers en 0,4 s), décharge forte et courte
run = state("run", 1.2, ticks(0.04, 0.1, 4, norm_steps([5, 4, 3, 2], 0.97)), 0.46, 0.62, 0.68, lame_amp=1.4)


# sneak 4 s : machine au ralenti, sans décharge : l'aiguille monte de 3 crans puis fuit cran par cran ; fumée réduite
def sneak_anim():
    L = 4.0
    up = ticks(0.4, 0.333, 3, [0.12, 0.1, 0.08])
    down = [(2.4 + 0.5 * i, -0.1) for i in range(3)]
    tr = {"aiguille_l": [("rotation", lambda t: needle_rot(pressure(t, up + down, 1.8, None)))]}
    for g in PUFF:
        tr[g] = [("scale", lambda t: (0.0, 0.0, 0.0))]
    for s, gs in ((1, LAMES_R), (-1, LAMES_L)):
        for j, g in enumerate(gs):
            tr[g] = [("rotation", lambda t, s=s, j=j: lift(s, -0.6 * (1 + j * 0.4)))]   # lames serrées contre le bras
    return anim("sneak", L, tr)


sneak = sneak_anim()


# fall 1 s : en l'air, les lames flottent un peu, l'aiguille rebondit sur des à-coups, fumée un peu plus forte
def fall_anim():
    L = 1.0
    jolts = [(0.08, 0.10), (0.33, -0.10), (0.58, 0.08), (0.83, -0.08)]
    tr = {"aiguille_l": [("rotation", lambda t: needle_rot(pressure(t, jolts, 0.5, None, base=0.5)))]}
    for g in PUFF:
        tr[g] = [("scale", lambda t: (0.0, 0.0, 0.0))]
    for s, gs in ((1, LAMES_R), (-1, LAMES_L)):
        for j, g in enumerate(gs):
            tr[g] = [("rotation", lambda t, s=s, j=j: lift(s, (1.6 + 0.8 * j) + 0.6 * math.sin(TAU * (2 * t / L - 0.1 * j))))]
    tr["levier_r"] = [("rotation", lambda t: lift(1, 4 + 3 * math.sin(TAU * 2 * t / L)))]
    return anim("fall", L, tr)


fall = fall_anim()


# attack 0,8 s (once, par-dessus l'état) : grosse décharge immédiate. Positions et rotations s'ajoutent, échelles se
# multiplient (guide, 6.4) : seuls les jets rangés dans les fûts (échelle 1 dans les états) peuvent apparaître ici.
def attack_anim():
    L = 0.8
    tr = {}
    for k in range(2):
        g = f"trans_jet_{k + 1}"
        dk = 0.02 + 0.05 * k
        d = DIR_C[k]

        def sc(t, dk=dk):
            u = t - dk
            if u <= 0:
                return 1.0, 1.0, 1.0
            grow = 1 - (1 - min(u / 0.1, 1)) ** 2.4
            back = sm(u, 0.42, 0.7)
            sx = 1 + (3.6 - 1) * grow * (1 + 0.35 * sm(u, 0.1, 0.42)) * (1 - back)
            sy = 1 + (3.6 - 1) * grow * (1 + 0.7 * sm(u, 0.1, 0.42)) * (1 - back)
            return sx, sy, sx

        def ps(t, dk=dk, d=d):
            u = t - dk
            if u <= 0:
                return 0.0, 0.0, 0.0
            out = 1.25 * (1 - (1 - min(u / 0.08, 1)) ** 2) * (1 - sm(u, 0.5, 0.72)) + 0.9 * sm(u, 0.12, 0.45) * (1 - sm(u, 0.45, 0.72))
            return tuple(d * out)
        tr[g] = [("scale", sc), ("position", ps)]
        tr[CHEM[k]] = [("rotation", lambda t, dk=dk: (5.0 * kick(t - dk, 0.1), 0.0, 0.0))]
    fin = lambda t: 1 - sm(t, 0.62, 0.8)
    tr["levier_r"] = [("rotation", lambda t: lift(1, 34 * (servo(t, 30, 0.4) - servo(t - 0.38, 22, 0.45)) * fin(t)))]
    tr["aiguille_l"] = [("rotation", lambda t: (-70 * (servo(t - 0.02, 26, 0.5) - servo(t - 0.4, 14, 0.7)) * fin(t), 0.0, 0.0))]
    for s, gs in ((1, LAMES_R), (-1, LAMES_L)):
        for j, g in enumerate(gs):
            a = (3.0 + 1.5 * j) * (1.0 if s > 0 else 0.6)
            tr[g] = [("rotation", lambda t, a=a, j=j, s=s: lift(s, a * kick(t - 0.03 * j, 0.1) * fin(t)))]
    return sound(anim("attack", L, tr, loop="once"), [0.02])


attack = attack_anim()


# hurt 0,8 s (once) : l'aiguille s'affole (oscillations larges amorties), le levier claque, les lames tremblent
def hurt_anim():
    L = 0.8
    env = lambda t: math.exp(-4.2 * t) * (1 - sm(t, 0.55, 0.8))
    tr = {"aiguille_l": [("rotation", lambda t: (95 * math.sin(TAU * 7.5 * t) * env(t) + 40 * kick(t, 0.12, 24, 0.5), 0.0, 0.0))],
          "levier_r": [("rotation", lambda t: lift(1, 14 * abs(math.sin(TAU * 9 * t)) * env(t)))]}
    for s, gs in ((1, LAMES_R), (-1, LAMES_L)):
        for j, g in enumerate(gs):
            tr[g] = [("rotation", lambda t, s=s, j=j: lift(s, 2.2 * math.sin(TAU * (11 * t - 0.15 * j)) * env(t)))]
    return anim("hurt", L, tr, loop="once")


hurt = hurt_anim()


# overlay_engrenage 4 s : échappement à 1/3 s, la roue avance d'une dent (30°) avec dépassement et rappel,
# le pignon (6 dents) de deux dents par tic en sens inverse : 360° et 720° exactement par boucle.
def gear_anim():
    L, n = 4.0, G12_T
    p = L / n

    def ang(t, step):
        if t >= L - 1e-9:
            return n * step
        return step * sum(servo(t - (i * p + 0.02), 12 / p, 0.5) for i in range(n))
    tr = {"roue_l": [("rotation", lambda t: (ang(t, 360 / G12_T), 0.0, 0.0))],
          "pignon_l": [("rotation", lambda t: (-ang(t, 360 / G6_T), 0.0, 0.0))]}
    return anim("overlay_engrenage", L, tr, fps=36)


gear = gear_anim()

ANIMS = [idle, walk, run, sneak, fall, attack, hurt, gear]
assert len(ANIMS) <= 16
assert 130 <= len(elements) <= 200, f"budget : {len(elements)} cubes"

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


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko")
