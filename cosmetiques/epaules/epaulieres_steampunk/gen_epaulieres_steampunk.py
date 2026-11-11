"""Épaulières Steampunk (refonte du 2026-11-08) : paire d'épaulières articulées en éventail, ensemble Steampunk (thème Mécanique).
Design original. Écrit epaulieres_steampunk.png, epaulieres_steampunk_e.png et .build/epaulieres_steampunk_brut.bbmodel.
Ancien générateur : .build/gen_avant.py (bloc doré qui entourait le bras : « moche de ouf », 2026-11-08).

Idée : la construction d'une vraie épaulière d'armure (lames à arête médiane qui se recouvrent, articulées sur rivets
coulissants et cuirs) traduite en machine d'horloger. Sur chaque épaule :
- un rang haut de 4 lames qui couvre le dessus de l'épaule, et un rang bas de 4 lames qui descend sur le flanc du bras,
  ouvertes en éventail autour d'un **moyeu** (même découpe et même alternance acier / laiton / cuivre que les lames
  des ailes Steampunk, validées) : silhouette dentelée, pas de bloc ;
- un **moyeu à engrenage** sur le flanc extérieur : la roue de 12 dents porte l'éventail du rang bas (elle tourne quand
  les lames s'ouvrent à l'apparition) et arme la pompe par crans ; un pignon l'entraîne ; chapeau à lentille-témoin ambre ;
- deux sangles de cuir cousu (avant et arrière), boucle de laiton, bout libre qui se balance.
Droite (right_arm) : petite chaudière de cuivre posée derrière l'épaule, porte du foyer à fentes rougeoyantes, deux
cheminées qui montent au-dessus de l'épaule, soupape à levier. Gauche (left_arm) : accumulateur de cuivre, colonne
montante et **manomètre** à cadran ambre au-dessus de l'épaule, soupape-sifflet.
Logique : la roue avance d'une dent à chaque tic ; la pression monte (aiguille à gauche, levier de soupape à droite),
tremble au maximum, puis décharge (jet modélisé qui monte + fumée de Minecraft) ; les lames claquent d'un cran.

Fonctions avancées (.claude/rules/fonctions-avancees.md ; à juger en jeu avec /cosmetique apercu) :
- trans_jet_* (jets de vapeur, alpha 1–254), trans_verre_l (verre du cadran) ; ctrl_alpha dans chaque jet (fondu) ;
- emit_mc_white_smoke aux deux bouches de cheminée et à la soupape-sifflet (même nom, guide 5 ter), ctrl_emit dans
  chaque point : -1 hors décharge, +4/+5 pendant la décharge ;
- calque _e (cadran, foyer, lentilles), overlay_ambiance (tools/ambiance.py) ; event_equip (1,6 s) avec un seul son.
Ni attack ni hurt (pièce portée). Sons : un seul, à l'équipement (tools/sons.py).
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True
NOM = "epaulieres_steampunk"
TEX = 512
TAU = 2 * math.pi
FPS = 30

def lerp(a, b, k):
    return a + (b - a) * k


def A(c):
    return np.array(c, np.float32)


# ------------------------------------------------------------------ matières (fiche .claude/styles/steampunk.md)
BRASS = dict(hi=(236, 196, 112), base=(190, 142, 64), low=(112, 76, 32))
BRASS_D = dict(hi=(214, 170, 92), base=(160, 116, 50), low=(92, 60, 24))
COPPER = dict(hi=(232, 150, 96), base=(176, 92, 52), low=(98, 46, 26))
STEEL = dict(hi=(136, 140, 150), base=(78, 82, 92), low=(38, 40, 48))
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




# Palette des ailes Steampunk (validées en jeu) : laiton chaud, cuivre, acier bleuté ; métal propre (brossé ±6 %, pas de patine).
BRASS = dict(hi=(238, 204, 122), base=(178, 134, 60), low=(92, 62, 26))
BRASS_D = dict(hi=(214, 170, 92), base=(150, 110, 48), low=(84, 56, 22))
COPPER = dict(hi=(236, 150, 100), base=(172, 88, 50), low=(84, 38, 22))
STEEL = dict(hi=(150, 158, 172), base=(70, 75, 86), low=(28, 30, 37))
CUIR = dict(hi=(150, 96, 60), base=(98, 58, 34), low=(54, 30, 18))
VEINE = 0.06
TILES = {}
def bar_tile(metal, seed, groove=3):
    W_, H_ = 96, 16
    a = np.zeros((H_, W_, 3), np.float32)
    r = np.random.default_rng(seed)
    for yy in range(H_):
        q = abs((yy + 0.5) / H_ - 0.5) * 2
        a[yy, :] = lerp(lerp(A(metal["hi"]) * 0.8, A(metal["low"]), q ** 1.1), A(metal["base"]), 0.45)
    a *= (0.95 + 0.10 * r.random((1, W_, 1), np.float32))
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
    col *= (0.95 + 0.10 * nz)[..., None]
    col[r > rr - 0.04] = A(metal["hi"])
    col[(r > rr - 0.14) & (r <= rr - 0.06)] *= 0.55
    col[r < hole + 0.12] = A(metal["hi"]) * 0.9
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


def paint_foyer(n=32):
    """Porte du foyer (bout extérieur de la chaudière) : cuivre, bague sombre, grille à trois fentes où rougeoie le feu.
    Source de lumière nette et logique (retour « aucune lumière sur le set ») : calque _e sur les fentes seules."""
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) / (n / 2)
    col = A(COPPER["base"]) * np.ones((n, n, 3), np.float32)
    col[r > 0.82] = A(COPPER["low"])
    col[(r > 0.62) & (r <= 0.72)] = A(BRASS["hi"])
    fente = np.zeros((n, n), bool)
    for y0 in (10, 15, 20):
        fente[y0:y0 + 3, 9:n - 9] = True
    col[fente] = A((255, 168, 72))
    col[fente & (yy % 5 == (10 % 5))] = A((255, 214, 128))
    e = np.zeros((n, n, 3), np.float32)
    e[fente] = (100, 46, 12)                        # x 2,4 par tools/ambiance.py : environ 225, 110, 29 la nuit
    return finish(col, np.ones((n, n), bool)), e


TILES["foyer"], FOYER_E = paint_foyer()


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


# ------------------------------------------------------------------ lames (même langage que les lames des ailes Steampunk)
def poly_mask(w, h, polys, ss=4):
    """Contours en coordonnées normalisées (u 0..1 de la racine au bout, v -1..1, +1 en haut) ; alpha net 0/255."""
    im = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    for p in polys:
        d.polygon([(u * w * ss, (1 - v) / 2 * h * ss) for u, v in p], fill=255)
    return np.array(im.resize((w, h), Image.LANCZOS)) > 110


def paint_lame(w, h, poly, metal, seed, rivets, tip, rmetal):
    """Lame d'épaulière : brossé léger, galbe, bout d'une autre matière derrière une gorge, joint sombre et biseau clair
    sur tout le contour (le contour se lit net à distance), ombre de recouvrement à la racine, rivets de 4 texels et plus."""
    mask = poly_mask(w, h, [poly])
    u = (np.arange(w) + 0.5)[None, :] / w * np.ones((h, 1))
    v = 1 - (np.arange(h) + 0.5)[:, None] / h * 2 * np.ones((1, w))
    r = np.random.default_rng(seed)
    streak = np.array(Image.fromarray((r.random((h, max(4, w // 12))) * 255).astype(np.uint8), "L").resize((w, h), Image.BILINEAR), np.float32) / 255 - 0.5
    col = A(metal["base"]) * np.ones((h, w, 3), np.float32)
    col *= (1 + VEINE * streak)[..., None]
    col *= (1.10 - 0.22 * np.abs(v) ** 1.5)[..., None]                    # galbe : le milieu bombé accroche la lumière
    t0, tmetal = tip
    band = u >= t0
    col[band] = (A(tmetal["base"]) * (1 + VEINE * streak)[..., None] * (1.10 - 0.22 * np.abs(v) ** 1.5)[..., None])[band]
    col[(u >= t0 - 3.0 / w) & (u < t0)] = A(tmetal["low"]) * 0.7
    d = inset(mask, 6)
    col[(d >= 3) & (d < 5)] = col[(d >= 3) & (d < 5)] * 0.48
    col[d < 3] = A(metal["hi"]) * (0.9 + VEINE * streak[d < 3])[..., None]
    col *= (0.42 + 0.58 * np.clip(u / 0.32, 0, 1))[..., None]               # ombre sous la lame du dessus
    for ru, rv in rivets:
        rivet(col, ru * w, (1 - rv) / 2 * h, max(2.4, h * 0.046), rmetal)
    return finish(col, mask)


# racine étroite, s'élargit vers le bout, bout arrondi par chanfreins (aucune pointe fine)
LAME = [(0, 0.60), (0.40, 0.86), (0.74, 1.0), (0.90, 0.92), (0.98, 0.64), (1.0, 0.25), (1.0, -0.25), (0.98, -0.64),
        (0.90, -0.92), (0.74, -1.0), (0.40, -0.86), (0, -0.60)]
RIV = [(0.22, 0.58), (0.22, -0.58), (0.50, 0.70), (0.50, -0.70), (0.86, 0.66), (0.86, -0.66), (0.93, 0.0)]
LW_, LH_ = 150, 84
TILES["l_brass"] = paint_lame(LW_, LH_, LAME, BRASS, 11, RIV, (0.80, COPPER), STEEL)
TILES["l_steel"] = paint_lame(LW_, LH_, LAME, STEEL, 31, RIV, (0.80, BRASS), BRASS)
TILES["l_copper"] = paint_lame(LW_, LH_, LAME, COPPER, 21, RIV, (0.80, BRASS), BRASS)
TILES["l_steel2"] = paint_lame(LW_, LH_, LAME, STEEL, 41, RIV, (0.80, COPPER), BRASS)


def paint_lens(n=28):
    """Lentille-témoin : verre ambre bombé dans une bague de laiton ; calque _e sur le verre seul (source nette)."""
    m = disc_mask(n, 0.99)
    r, a = polar(n)
    col = A(BRASS["base"]) * np.ones((n, n, 3), np.float32)
    col[r > 0.86] = A(BRASS["low"])
    col[(r > 0.70) & (r <= 0.80)] = A(BRASS["hi"])
    glass = r < 0.66
    col[glass] = lerp(A((255, 236, 170)), A((214, 132, 40)), np.clip(r / 0.66, 0, 1)[..., None] ** 1.3)[glass]
    col[(r < 0.22) & (a > -80) & (a < 10)] = A((255, 250, 228))
    e = np.zeros((n, n, 3), np.float32)
    e[glass] = (100, 62, 16)
    e[glass & (r < 0.35)] = (106, 78, 28)
    return finish(col, m), e


TILES["lens"], LENS_E = paint_lens()

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
for n_, E in (("dial", DIAL_E), ("foyer", FOYER_E), ("lens", LENS_E)):
    u0, v0, u1, v1 = UV[n_]
    tex_e[v0:v1, u0:u1, :3] = E.astype(np.uint8)
    tex_e[v0:v1, u0:u1, 3] = (E.max(axis=2) > 0) * 255
tex[..., :3] &= 0xFC
tex[tex[..., 3] == 0] = 0
semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
zone = np.zeros(semi.shape, bool)
for n_ in SEMI:
    u0, v0, u1, v1 = UV[n_]
    zone[v0:v1, u0:u1] = True
assert not (semi & ~zone).any(), "semi-transparence hors des images trans_"


def b64png(arr, fn):
    im = Image.fromarray(arr, "RGBA")
    im.save(fn, optimize=True)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


tex_b64, tex_e_b64 = b64png(tex, f"{NOM}.png"), b64png(tex_e, f"{NOM}_e.png")
if os.path.exists(f"{NOM}_r.png"):
    os.remove(f"{NOM}_r.png")          # reflets _r retirés partout (tools/ambiance.py, REFLETS = False)

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
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx (ordre du mod et du renderer), blocage de cardan traité."""
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


def frame_n(N, up=(0, 1, 0)):
    """Repère dont le Z local est N (face south visible), Y local au plus près de up."""
    N = unit(N)
    up = np.asarray(up, float)
    Y = unit(up - (up @ N) * N)
    return np.column_stack([np.cross(Y, N), Y, N])


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


def plate(g, name, c, X, Y, w, h, tile, th=0.3):
    """Plaque fine : contour par l'alpha, tranches transparentes. u suit X, le haut de l'image est +Y ; face south = X x Y."""
    X = unit(X)
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    return cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
                {"south": T(tile), "north": flip(T(tile)), "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def disc(g, name, c, N, size, tile, th=0.3, up=(0, 1, 0)):
    R_ = frame_n(N, up)
    return plate(g, name, c, R_[:, 0], R_[:, 1], size, size, tile, th)


def bar(g, name, p, q, r, mat, octo=True, ov=0.0, caps=(True, True), end_p=None, end_q=None, up=None):
    """Tronçon de p à q : section octogonale (deux cubes à 45°, le second en retrait de 0,11 à chaque bout) ou losange."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = float(np.linalg.norm(q - p))
    X = unit(q - p)
    ref = np.asarray(up, float) if up is not None else (V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0))
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R0 = np.column_stack([X, Y, Z_])
    R45 = np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])
    lg = T("bar_" + mat)
    cap = T("cap_" + mat)
    faces = {"south": lg, "north": lg, "up": lg, "down": lg,
             "east": (end_q or cap) if caps[1] else CLEAR, "west": (end_p or cap) if caps[0] else CLEAR}
    if octo:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R0), faces)
        f2 = dict(faces, east=cap if caps[1] else CLEAR, west=cap if caps[0] else CLEAR)
        cube(g, name + "o", p + (-ov + 0.11, -r * 0.97, -r * 0.97), p + (L + ov - 0.11, r * 0.97, r * 0.97), p, euler(R45), f2)
    else:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R45), faces)


def core(g, name, c, X, Y, w, h, th, tile):
    """Âme pleine (cuir) : vrai volume, texturé sur 6 faces."""
    X = unit(X)
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    fc = {f: T(tile) for f in ("north", "south", "east", "west", "up", "down")}
    return cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_), fc)


# ------------------------------------------------------------------ une épaulière
LAME_T = ["l_brass", "l_steel", "l_copper", "l_steel2"]
RIDGE = {"l_brass": "steel", "l_steel": "brass", "l_copper": "brass", "l_steel2": "brass"}
LH, LB, ROUE, PIGNON, STRAPS, ARM = {}, {}, {}, {}, {}, {}
SW = 1.35            # largeur des sangles
STRAP_Z = 2.68       # âme de cuir : face intérieure à 2,41 px de l'axe du bras (seconde couche du skin à 2,25)


def lame(arm, name, root, d, nhint, L, W, tile, ofs):
    X = unit(d)
    nh = np.asarray(nhint, float)
    N = unit(nh - (nh @ X) * X)
    Y = np.cross(N, X)
    root = np.asarray(root, float) + N * ofs
    g = group(name, root, parent=arm)
    plate(g, name + "_p", root + X * (L / 2), X, Y, L, W, tile)
    # arête médiane en losange (lames d'armure « à arête » : volume et reflet), cachée sous la lame du dessus à la racine
    bar(g, name + "_a", root + X * (0.08 * L), root + X * (0.74 * L), 0.27 * W / 3.2, RIDGE[tile], octo=False, up=N, caps=(False, True))
    return g


def sangle(arm, s, tag, zs):
    """Sangle de cuir cousu : section fixe en biais sur le bras, boucle de laiton, bout libre qui pend (son propre groupe)."""
    z = zs * STRAP_Z
    Nout = V(0, 0, zs)
    top, jt = V(s * 6.2, 24.25, z), V(s * 6.9, 21.0, z)
    X = unit(jt - top)
    Y = np.cross(Nout, X)
    L = float(np.linalg.norm(jt - top))
    plate(arm, f"sangle_h_{tag}{'a' if zs < 0 else 'p'}", (top + jt) / 2 + X * 0.05, X, Y, L + 0.1, SW, "cuir")
    core(arm, f"sangle_ha_{tag}{'a' if zs < 0 else 'p'}", (top + jt) / 2, X, Y, L, SW * 0.58, 0.54, "cuir")
    # boucle : cadre de laiton posé sur la sangle, ardillon d'acier
    plate(arm, f"boucle_{tag}{'a' if zs < 0 else 'p'}", jt + Nout * 0.42, V(0, -1, 0), np.cross(Nout, V(0, -1, 0)), 1.0, SW + 0.35, "buckle", th=0.24)
    g = group(f"sangle_{tag}{'a' if zs < 0 else 'p'}", jt, parent=arm)
    X2 = unit(V(s * 0.12, -1, 0))
    Y2 = np.cross(Nout, X2)
    L2 = 2.7
    plate(g, f"sangle_b_{tag}{'a' if zs < 0 else 'p'}", jt + X2 * (L2 / 2 + 0.05), X2, Y2, L2, SW, "cuir")
    core(g, f"sangle_ba_{tag}{'a' if zs < 0 else 'p'}", jt + X2 * (L2 * 0.32), X2, Y2, L2 * 0.6, SW * 0.58, 0.54, "cuir")
    STRAPS.setdefault(s, []).append((g, zs))


def epauliere(s, tag, azA, LA, azB, LB_, k):
    arm = group("right_arm" if s > 0 else "left_arm", V(s * 5, 22, 0))
    ARM[s] = arm
    # rang bas : jupe de lames en cône autour du bras (côté extérieur, de l'avant à l'arrière), chaque lame tournée vers
    # l'extérieur du bras : lisible de face comme de profil ; les lames se recouvrent en tuiles, celle du milieu par-dessus
    mid = (len(azB) - 1) / 2
    LB[s] = []
    for i, b in enumerate(azB):
        cb, sb = math.cos(math.radians(b)), math.sin(math.radians(b))
        rad = V(s * cb, 0, sb)
        root = V(s * 6.0, 24.75, 0) + rad * 2.85
        g = lame(arm, f"bas{i}_{tag}", root, rad * 0.52 + V(0, -1, 0), rad + V(0, 0.25, 0), LB_[i] * k, 3.1 * k,
                 LAME_T[(i + (1 if s > 0 else 0)) % 4], 0.12 * (len(azB) - abs(i - mid)) - 0.1)
        LB[s].append((g, b, i))
    # rang haut : couvre le dessus de l'épaule, s'étale vers l'avant, l'extérieur et l'arrière
    hh = V(s * 6.0, 25.35, 0)
    mid = (len(azA) - 1) / 2
    LH[s] = []
    for i, a in enumerate(azA):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        g = lame(arm, f"haut{i}_{tag}", hh, V(s * ca, -0.55, sa), V(s * ca * 0.55, 1, sa * 0.55), LA[i] * k, 3.4 * k,
                 LAME_T[(i + (0 if s > 0 else 1)) % 4], 0.14 * (len(azA) - abs(i - mid)))
        LH[s].append((g, a, i))
    # moyeu : roue de 12 dents (porte l'éventail du rang bas), pignon d'acier, axe à chapeau et lentille-témoin
    N = V(s, 0, 0)
    HC = V(s * 9.95, 24.45, 0)
    bar(arm, f"axe_{tag}", V(s * 8.9, 24.45, 0), V(s * 10.3, 24.45, 0), 0.42, "brass", caps=(False, True))
    bar(arm, f"chapeau_{tag}", V(s * 10.24, 24.45, 0), V(s * 10.7, 24.45, 0), 0.7, "brass", end_q=T("lens"))   # lentille-témoin du moyeu
    ROUE[s] = group(f"roue_{tag}", HC, parent=arm)
    disc(ROUE[s], f"roue_{tag}_d", HC, N, 2 * R12_OUT, "g12")
    Xl = frame_n(N)[:, 0]
    beta = math.radians(330 if s > 0 else 210)
    PC = HC + PITCH_D * (math.cos(beta) * Xl + math.sin(beta) * V(0, 1, 0)) + N * 0.14
    PIGNON[s] = group(f"pignon_{tag}", PC, parent=arm)
    disc(PIGNON[s], f"pignon_{tag}_d", PC, N, 2 * R6_OUT, "g6")
    bar(arm, f"axe_p_{tag}", PC - N * 0.55, PC + N * 0.42, 0.24, "steel", caps=(False, True))
    sangle(arm, s, tag, -1)
    sangle(arm, s, tag, 1)
    return arm


ARM_R = epauliere(1, "r", (-64, -32, 0, 32, 64), (5.6, 6.2, 6.5, 6.2, 5.7), (-72, -36, 0, 36, 72), (6.1, 6.9, 7.4, 7.0, 6.2), 1.0)
ARM_L = epauliere(-1, "l", (-64, -32, 0, 32, 64), (5.7, 6.2, 6.5, 6.2, 5.6), (-72, -36, 0, 36, 72), (6.2, 7.0, 7.5, 6.8, 6.1), 0.95)

# ------------------------------------------------------------------ droite : chaudière, foyer, cheminées, soupape
DY, DZ, DRR = 26.05, 3.3, 0.95
CH = group("chaudiere_r", V(7.3, DY, DZ), parent=ARM_R)
bar(CH, "tambour", V(5.9, DY, DZ), V(8.7, DY, DZ), DRR, "copper")
bar(CH, "cercle0", V(5.75, DY, DZ), V(6.2, DY, DZ), DRR + 0.13, "brass")
bar(CH, "cercle1", V(8.4, DY, DZ), V(8.88, DY, DZ), DRR + 0.13, "brass", end_q=T("foyer"))     # porte du foyer : fentes rougeoyantes
for i, x in enumerate((6.6, 8.0)):                                                         # selles de fixation sur le rang haut
    bar(CH, f"selle{i}", V(x, DY - 0.6, DZ - 0.2), V(x, 24.75, DZ - 0.75), 0.2, "steel", caps=(False, False))

DIR_C = [unit(V(0.05, 1, 0.20)), unit(V(0.20, 1, 0.15))]
BASES = [V(6.45, DY + DRR - 0.2, DZ), V(8.05, DY + DRR - 0.2, DZ)]
LEN_C = [5.3, 4.3]
EMIT = "emit_mc_white_smoke"
CHEM, JETS = [], []


def jet(parent, k, J0, d, w, h):
    """Jet de vapeur : 2 plaques croisées translucides rangées DANS la bouche (invisibles), que la décharge agrandit et fait
    sortir ; ctrl_alpha (fondu) dans le groupe."""
    R_c = np.column_stack([V(1, 0, 0) - d[0] * d, d, np.cross(unit(V(1, 0, 0) - d[0] * d), d)])
    R_c[:, 0] = unit(R_c[:, 0])
    R_c[:, 2] = np.cross(R_c[:, 0], R_c[:, 1])
    jg = group(f"trans_jet_{k}", J0, parent=parent, rotation=euler(R_c))
    group(f"ctrl_alpha@{k}", J0, parent=jg)
    for j, a in enumerate((0, 90)):
        cube(jg, f"jet{k}_{j}", J0 + V(-w / 2, 0.05, -0.15), J0 + V(w / 2, h, 0.15), J0, (0, a + 20 * k, 0),
             {"south": T("steam"), "north": flip(T("steam")), "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
    JETS.append((jg, f"ctrl_alpha@{k}", d))
    return R_c


def emit(parent, k, M, R_c):
    g = group(EMIT + ("" if k == 1 else f"@{k}"), M, parent=parent, rotation=euler(R_c))
    group(f"ctrl_emit@{k}", M, parent=g)


for k in range(2):
    d, B, L = DIR_C[k], BASES[k], LEN_C[k]
    g = group(f"cheminee{k + 1}_r", B, parent=CH)
    CHEM.append(g)
    bar(g, f"bride{k}", B - d * 0.05, B + d * 0.45, 0.74, "brass")
    bar(g, f"fut{k}", B, B + d * (L - 0.3), 0.5, "copper")
    bar(g, f"collier{k}", B + d * (L * 0.55), B + d * (L * 0.55 + 0.4), 0.63, "brass")
    bar(g, f"col{k}", B + d * (L - 0.8), B + d * (L - 0.25), 0.64, "copper")
    bar(g, f"chapeau{k}", B + d * (L - 0.3), B + d * (L + 0.1), 0.84, "copper", end_q=T("mouth"))
    M = B + d * (L + 0.1)
    R_c = jet(g, k + 1, M - d * 1.25, d, 0.8, 1.15)
    emit(g, k + 1, M + d * 0.25, R_c)

# soupape à levier, devant les cheminées : le levier se soulève quand la pression monte, saute à la décharge
SV = V(7.25, DY + 0.55, DZ - 0.72)
SP = group("soupape_r", SV, parent=CH)
bar(SP, "soup_corps", SV, SV + V(0, 0.95, 0), 0.3, "brass")
bar(SP, "soup_tete", SV + V(0, 0.8, 0), SV + V(0, 1.15, 0), 0.42, "brass")
LV = SV + V(0, 1.0, 0)
LG = group("levier_r", LV, parent=SP)
bar(LG, "levier", LV + V(-0.25, 0.22, 0), LV + V(1.6, 0.22, 0), 0.13, "steel", octo=False)
bar(LG, "contrepoids", LV + V(1.3, 0.22, 0), LV + V(1.8, 0.22, 0), 0.3, "brass")

# ------------------------------------------------------------------ gauche : accumulateur, colonne, manomètre, sifflet
AY, AZ = 25.95, 3.2
AC = group("accu_l", V(-7.1, AY, AZ), parent=ARM_L)
bar(AC, "accu", V(-5.95, AY, AZ), V(-8.45, AY, AZ), 0.82, "copper")
bar(AC, "accu_c0", V(-5.8, AY, AZ), V(-6.25, AY, AZ), 0.95, "brass")
bar(AC, "accu_c1", V(-8.15, AY, AZ), V(-8.62, AY, AZ), 0.95, "brass", end_q=T("lens"))       # lentille-témoin : pression prête
for i, x in enumerate((-6.6, -7.65)):
    bar(AC, f"selle_l{i}", V(x, AY - 0.55, AZ - 0.2), V(x, 24.75, AZ - 0.75), 0.2, "steel", caps=(False, False))
G = V(-7.4, 29.15, 1.0)
NG = unit(V(-0.38, 0.12, -1))
R0_, R1_ = V(-7.05, AY + 0.7, AZ - 0.1), V(-7.1, 28.25, 2.55)
bar(AC, "colonne", R0_, R1_, 0.26, "brass")
bar(AC, "coude", R1_ - V(0, 0.3, 0), R1_ + V(0, 0.3, 0), 0.36, "brass")
bar(AC, "colonne2", R1_, G - NG * 0.62, 0.24, "brass")
RG = frame_n(NG)
MN = group("manometre_l", G, parent=AC, rotation=euler(RG))
bar(MN, "boitier", G + V(0, 0, -0.75), G + V(0, 0, -0.25), 1.42, "copper")
plate(MN, "cadran", G + V(0, 0, -0.06), V(1, 0, 0), V(0, 1, 0), 2.5, 2.5, "dial", th=0.12)
plate(MN, "lunette", G + V(0, 0, 0.11), V(1, 0, 0), V(0, 1, 0), 3.3, 3.3, "bezel", th=0.42)
NE = group("aiguille_l", G, parent=MN)
plate(NE, "aiguille", G + V(0, 0, 0.17), V(1, 0, 0), V(0, 1, 0), 0.42, 1.7, "needle", th=0.1)
VR = group("trans_verre_l", G, parent=MN)
plate(VR, "verre", G + V(0, 0, 0.37), V(1, 0, 0), V(0, 1, 0), 2.55, 2.55, "glass", th=0.08)
# soupape-sifflet sur le bout extérieur de l'accumulateur : petite décharge quand l'aiguille est au rouge
SL = V(-7.45, AY + 0.6, AZ)
SFL = group("sifflet_l", SL, parent=AC)
bar(SFL, "sifflet", SL, SL + V(0, 1.0, 0), 0.3, "brass", caps=(False, True), end_q=T("mouth"))
bar(SFL, "sifflet_b", SL + V(0, 0.2, 0), SL + V(0, 0.5, 0), 0.42, "brass")
R_s = jet(SFL, 3, SL + V(0, 0.25, 0), V(0, 1, 0), 0.4, 0.7)
emit(SFL, 3, SL + V(0, 1.25, 0), R_s)


def bone(name):
    g = groups[name]
    return {"name": name.split("@")[0], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone(ARM_R), bone(ARM_L)]


# ------------------------------------------------------------------ garde-fous de placement (pose de base)
def world_corners():
    """Coins de chaque cube dans le monde, rotations des groupes comprises."""
    def rot(r):
        rx, ry, rz = map(math.radians, r)
        cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
        return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    owner = {u: g for g, gg in groups.items() for u in gg["ids"]}
    out = []
    for e in elements:
        a, b = np.array(e["from"]), np.array(e["to"])
        o = np.array(e["origin"])
        Rm = rot(e.get("rotation", (0, 0, 0)))
        pts = [o + Rm @ (np.array([x, y, z]) - o) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
        g = owner[e["uuid"]]
        while g:
            gg = groups[g]
            if any(gg["rotation"]):
                Rg, og = rot(gg["rotation"]), np.array(gg["origin"])
                pts = [og + Rg @ (p - og) for p in pts]
            g = gg["parent"]
        out.append((e["name"], pts))
    return out


_viol = []
for nm, pts in world_corners():
    for p in pts:
        if abs(p[0]) < 5.0 and p[1] > 24.0 and abs(p[2]) < 4.5:
            _viol.append((nm, "tête", p))
        ax = 6.0 if p[0] > 0 else -6.0
        if abs(p[0] - ax) < 2.37 and 12 < p[1] < 24.35 and abs(p[2]) < 2.37:
            _viol.append((nm, "bras", p))
for v_ in _viol[:12]:
    print("  placement :", v_[0], v_[1], np.round(v_[2], 2))

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
    """Réponse d'un servo sous-amorti : 0 avant x = 0, dépasse un peu 1 puis s'y stabilise."""
    if x <= 0:
        return 0.0
    wd = w * math.sqrt(1 - z * z)
    return 1 - math.exp(-z * w * x) * (math.cos(wd * x) + z / math.sqrt(1 - z * z) * math.sin(wd * x))


def kick(x, up=0.09, w=30.0, z=0.45):
    """Cran : à-coup bref avec rebond, revient à 0."""
    return servo(x, w, z) - servo(x - up, w * 0.8, z)


def anim(name, length, tracks, loop="loop", fps=FPS):
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A_ = {}
    for g, chans in tracks.items():
        kfs = []
        for ch, f in chans:
            kfs += [kf(ch, t, *f(t)) for t in times]
        A_[groups[g]["uuid"]] = {"name": g.split("@")[0], "type": "bone", "keyframes": kfs}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": fps,
            "selected": name == "idle", "animators": A_}


def sound(a, times, name="block.fire.extinguish"):
    a["animators"]["effects"] = {"name": "Effects", "type": "effect",
                                 "keyframes": [{"channel": "sound", "data_points": [{"effect": name, "file": ""}], "time": round(t, 3)} for t in times]}
    return a


# MIROIR D'AXES (guide, section 3 ; rotations du mod = rotations directes de Blockbench). Seul endroit à toucher si la
# convention change. lift : une lame qui se soulève vers l'extérieur (+Z à droite, -Z à gauche).
# Rang bas (pend) : +X rapproche son azimut de l'avant (bout vers l'avant), donc (b·k, 0, 0) referme l'éventail de k.
# Rang haut (à plat) : (0, s·a·k, 0) le referme vers l'azimut 0.
def lift(s, deg):
    return 0.0, 0.0, s * deg


def liftc(s, b, deg):
    """Lame du rang bas (azimut b) : le bout s'écarte du bras le long de son rayon (petits angles)."""
    return -math.sin(math.radians(b)) * deg, 0.0, s * math.cos(math.radians(b)) * deg


def add(*rs):
    return tuple(sum(r[i] for r in rs) for i in range(3))


# Aiguille : canonique, pointe en haut à mi-pression ; pression 0 -> -120° (à gauche), 1 -> +120° (sens horaire vu de face).
def needle_rot(P):
    return 0.0, 0.0, -240.0 * (P - 0.5)


def gear_angle(t, L, ticks, step=30.0, w=34.0):
    """Roue à échappement : un cran par tic (servo), exactement 360° par boucle (12 tics de 30°)."""
    if t >= L - 1e-9:
        return step * len(ticks)
    return step * sum(servo(t - ti, w, 0.5) for ti in ticks)


def pressure(t, steps, trem, td, base=0.1):
    """Montée par paliers, tremblement au maximum, décharge brutale avec rebond sur la butée."""
    Pb = base + sum(dp * servo(t - ti, 30, 0.5) for ti, dp in steps)
    tr = 0.03 * math.sin(TAU * 13 * t) * bump(t, trem - 0.06, trem + 0.08, td - 0.04, td + 0.01)
    return base + (Pb - base) * (1 - servo(t - td, 24.0, 0.62)) + tr


def jet_tracks(tr, k, t0, L, big=1.0):
    """Décharge d'un jet à t0 : sort de la bouche (0,08 s), monte et grossit, s'efface (ctrl_alpha), rentre invisible.
    Positions dans le repère du parent (direction d de la buse) ; échelle dans le repère du jet (Y = d)."""
    jg, ag, d = JETS[k - 1]

    def u_(t):
        return (t - t0) % L

    def pos(t):
        u = u_(t)
        if u >= 0.9:
            return 0.0, 0.0, 0.0
        out = 1 - (1 - min(u / 0.08, 1)) ** 2
        rise = sm(u, 0.05, 0.6)
        back = sm(u, 0.64, 0.82)
        return tuple(d * (1.25 * out + 1.5 * big * rise) * (1 - back))

    def sc(t):
        u = u_(t)
        if u >= 0.9:
            return 1.0, 1.0, 1.0
        out = 1 - (1 - min(u / 0.08, 1)) ** 2.4
        rise = sm(u, 0.05, 0.6)
        g = out * (1 - sm(u, 0.64, 0.82))
        return 1 + big * (2.0 * g + 1.2 * rise * g), 1 + big * (2.6 * g + 1.8 * rise * g), 1 + big * (2.0 * g + 1.2 * rise * g)

    def al(t):
        u = u_(t)
        if u >= 0.9:
            return 0.0, 0.0, 0.0
        return -sm(u, 0.18, 0.6) * (1 - sm(u, 0.84, 0.88)), 0.0, 0.0
    tr.setdefault(jg, []).extend([("position", pos), ("scale", sc)])
    tr.setdefault(ag, []).append(("position", al))


def emit_track(tr, k, events, L):
    """ctrl_emit (1 + position) : -1 coupé ; +gain pendant chaque décharge (t0, gain, durée)."""
    def f(t):
        v = -1.0
        for t0, gain, dur in events:
            v += gain * bump((t - t0) % L, 0.0, 0.02, dur, dur + 0.08)
        return v, 0.0, 0.0
    tr[f"ctrl_emit@{k}"] = [("position", f)]


def straps(tr, s, f):
    for j, (g, zs) in enumerate(STRAPS[s]):
        tr[g] = [("rotation", lambda t, zs=zs, j=j: (-zs * f(t, j), 0.0, s * 0.4 * f(t, j + 0.5)))]


# ---- repos (8 s) : à gauche, la roue arme la pompe (12 tics), l'aiguille grimpe par paliers, tremble au rouge, le sifflet
# lâche un jet ; à droite, décalé, la roue arme la chaudière, le levier de soupape se soulève peu à peu, tremble, et les deux
# cheminées déchargent ; chaque décharge fait claquer les lames du côté d'un cran.
def idle_anim():
    L = 8.0
    tr = {}
    TL = [0.25 + 0.42 * i for i in range(12)]                 # gauche : 0,25 -> 4,87
    TR = [3.3 + 0.36 * i for i in range(12)]                  # droite : 3,3 -> 7,26 (la pression sert à la boucle suivante)
    TD_L, TD_R = 5.9, 2.4
    tr[ROUE[-1]] = [("rotation", lambda t: (-gear_angle(t, L, TL), 0.0, 0.0))]
    tr[PIGNON[-1]] = [("rotation", lambda t: (2 * gear_angle(t, L, TL), 0.0, 0.0))]
    tr[ROUE[1]] = [("rotation", lambda t: (gear_angle(t, L, TR), 0.0, 0.0))]
    tr[PIGNON[1]] = [("rotation", lambda t: (-2 * gear_angle(t, L, TR), 0.0, 0.0))]
    steps_l = [(TL[i], 0.15) for i in range(1, 12, 2)]
    tr["aiguille_l"] = [("rotation", lambda t: needle_rot(pressure(t, steps_l, 5.2, TD_L)))]

    def p_r(t):
        return (1 - servo(t - TD_R, 22, 0.6)) + sum(servo(t - ti, 30, 0.5) for ti in TR) / 12
    lev = lambda t: 9 * p_r(t) + 3.0 * math.sin(TAU * 17 * t) * bump(t, 1.8, 1.9, TD_R - 0.04, TD_R) + \
        22 * (servo(t - TD_R + 0.03, 26, 0.4) - servo(t - TD_R - 0.36, 20, 0.45))
    tr["levier_r"] = [("rotation", lambda t: lift(1, lev(t)))]
    for k, g in enumerate(CHEM):
        dk = TD_R + 0.07 * k
        tr[g] = [("rotation", lambda t, dk=dk: (2.4 * kick((t - dk) % L), 0.0, 0.0))]
        jet_tracks(tr, k + 1, dk, L)
    jet_tracks(tr, 3, TD_L, L, big=0.7)
    emit_track(tr, 1, [(TD_R, 5, 0.3)], L)
    emit_track(tr, 2, [(TD_R + 0.07, 5, 0.3)], L)
    emit_track(tr, 3, [(TD_L, 4, 0.25)], L)
    tr["sifflet_l"] = [("rotation", lambda t: (0.0, 0.0, -1.5 * math.sin(TAU * 21 * t) * bump(t, 5.2, 5.3, TD_L, TD_L + 0.3)))]
    for s, td, amp in ((1, TD_R, 2.6), (-1, TD_L, 1.6)):
        for g, b, i in LB[s]:
            dj = td + 0.03 * abs(i - 2)
            tr[g] = [("rotation", lambda t, s=s, b=b, dj=dj, a=amp * (1 + 0.2 * abs(i - 2)): liftc(s, b, a * kick((t - dj) % L)))]
        for g, a, i in LH[s]:
            dj = td + 0.02 * i
            tr[g] = [("rotation", lambda t, s=s, dj=dj, a=amp * 0.6: lift(s, a * kick((t - dj) % L)))]
        straps(tr, s, lambda t, j, td=td: 1.2 + 0.6 * math.sin(TAU * (t / L * 2 - 0.2 * j)) + 4 * kick((t - td - 0.05) % L, 0.16, 18, 0.3))
    return anim("idle", L, tr)


# ---- marche (1,6 s, deux pas) : la machine tourne plus vite (12 tics), chaque pas fait claquer l'éventail d'un cran,
# petite bouffée à chaque pas droit ; l'aiguille oscille au milieu.
def walk_anim():
    L = 1.6
    tr = {}
    TK = [0.03 + L / 12 * i for i in range(12)]
    for s in (1, -1):
        tr[ROUE[s]] = [("rotation", lambda t, s=s: (s * gear_angle(t, L, TK, w=48), 0.0, 0.0))]
        tr[PIGNON[s]] = [("rotation", lambda t, s=s: (-2 * s * gear_angle(t, L, TK, w=48), 0.0, 0.0))]
        for g, b, i in LB[s]:
            ph = 0.04 * i + (0 if s > 0 else 0.5)
            tr[g] = [("rotation", lambda t, s=s, b=b, ph=ph, i=i: add((2.2 * math.sin(TAU * (2 * t / L - ph)), 0.0, 0.0),
                                                                 liftc(s, b, 1.0 + 1.6 * kick((t - ph * L / 2) % (L / 2), 0.07, 34, 0.4))))]
        for g, a, i in LH[s]:
            ph = 0.03 * i + (0 if s > 0 else 0.5)
            tr[g] = [("rotation", lambda t, s=s, ph=ph: lift(s, 0.8 * kick((t - ph * L / 2) % (L / 2), 0.07, 34, 0.4)))]
        straps(tr, s, lambda t, j, s=s: 5 + 4 * math.sin(TAU * (2 * t / L - 0.15 * j - (0 if s > 0 else 0.5))))
    tr["aiguille_l"] = [("rotation", lambda t: needle_rot(0.55 + 0.06 * math.sin(TAU * 2 * t / L) + 0.02 * math.sin(TAU * 13 * t / L)))]
    tr["levier_r"] = [("rotation", lambda t: lift(1, 5 + 6 * kick((t - 0.4) % (L / 2), 0.08, 30, 0.4)))]
    for k, g in enumerate(CHEM):
        tr[g] = [("rotation", lambda t, k=k: (1.4 * kick((t - 0.4 - 0.05 * k) % (L / 2)), 0.0, 0.0))]
    for k in range(2):
        jet_tracks(tr, k + 1, 0.4 + 0.05 * k, L, big=0.5)
    emit_track(tr, 1, [(0.4, 2, 0.2)], L)
    emit_track(tr, 2, [(0.45, 2, 0.2)], L)
    emit_track(tr, 3, [], L)
    return anim("walk", L, tr)


# ---- course (1 s) : l'éventail du rang bas se couche vers l'arrière, le rang haut se soulève (vent), les cheminées
# penchent en arrière et crachent à chaque foulée ; aiguille haute qui tremble.
def run_anim():
    L = 1.0
    tr = {}
    TK = [0.02 + L / 12 * i for i in range(12)]
    for s in (1, -1):
        tr[ROUE[s]] = [("rotation", lambda t, s=s: (s * gear_angle(t, L, TK, w=60), 0.0, 0.0))]
        tr[PIGNON[s]] = [("rotation", lambda t, s=s: (-2 * s * gear_angle(t, L, TK, w=60), 0.0, 0.0))]
        for g, b, i in LB[s]:
            ph = 0.05 * i + (0 if s > 0 else 0.5)
            tr[g] = [("rotation", lambda t, s=s, b=b, ph=ph, i=i: add((-8 - 1.5 * i - 3 * math.sin(TAU * (2 * t / L - ph)), 0.0, 0.0),
                                                                 liftc(s, b, 3 + 1.5 * math.sin(TAU * (2 * t / L - ph - 0.2)))))]
        for g, a, i in LH[s]:
            ph = 0.04 * i + (0 if s > 0 else 0.5)
            tr[g] = [("rotation", lambda t, s=s, ph=ph: lift(s, 3 + 1.5 * math.sin(TAU * (2 * t / L - ph))))]
        straps(tr, s, lambda t, j, s=s: 16 + 6 * math.sin(TAU * (2 * t / L - 0.15 * j - (0 if s > 0 else 0.5))))
    tr["aiguille_l"] = [("rotation", lambda t: needle_rot(0.86 + 0.04 * math.sin(TAU * 4 * t / L) + 0.025 * math.sin(TAU * 13 * t)))]
    tr["levier_r"] = [("rotation", lambda t: lift(1, 12 + 14 * kick((t - 0.3) % L, 0.12, 26, 0.4)))]
    for k, g in enumerate(CHEM):
        tr[g] = [("rotation", lambda t, k=k: (6 + 2.5 * kick((t - 0.3 - 0.06 * k) % L), 0.0, 0.0))]
        jet_tracks(tr, k + 1, 0.3 + 0.06 * k, L, big=0.85)
    emit_track(tr, 1, [(0.3, 4, 0.25)], L)
    emit_track(tr, 2, [(0.36, 4, 0.25)], L)
    emit_track(tr, 3, [], L)
    return anim("run", L, tr)


# ---- accroupi (3 s) : machine au ralenti, éventails à demi refermés et serrés contre le bras, aiguille basse, sans vapeur.
def sneak_anim():
    L = 3.0
    tr = {}
    TK = [0.1 + L / 12 * i for i in range(12)]
    for s in (1, -1):
        tr[ROUE[s]] = [("rotation", lambda t, s=s: (s * gear_angle(t, L, TK), 0.0, 0.0))]
        tr[PIGNON[s]] = [("rotation", lambda t, s=s: (-2 * s * gear_angle(t, L, TK), 0.0, 0.0))]
        for g, b, i in LB[s]:
            tr[g] = [("rotation", lambda t, s=s, b=b, i=i: liftc(s, b, -2.5 + 0.4 * math.sin(TAU * (t / L - 0.05 * i))))]
        for g, a, i in LH[s]:
            tr[g] = [("rotation", lambda t, s=s, a=a: add((0.0, s * a * 0.2, 0.0), lift(s, -4)))]
        straps(tr, s, lambda t, j: 1.0 + 0.5 * math.sin(TAU * (t / L - 0.2 * j)))
    tr["aiguille_l"] = [("rotation", lambda t: needle_rot(0.22 + 0.03 * math.sin(TAU * 2 * t / L) + 0.012 * math.sin(TAU * 17 * t / L)))]
    for k in (1, 2, 3):
        emit_track(tr, k, [], L)
    return anim("sneak", L, tr)


# ---- apparition (event_equip, 1,6 s, par-dessus l'état) : la roue fait un tour et ouvre l'éventail lame après lame
# (cran par cran, servo), les cheminées sortent en télescope, l'aiguille fait son tour d'essai, première décharge, un son.
def equip_anim():
    L = 1.6
    tr = {}

    def closed(t, t0):
        return 1.0 if t <= t0 else max(0.0, 1 - servo(t - t0, 22, 0.5)) if t < L - 1e-9 else 0.0
    for s in (1, -1):
        for g, b, i in LB[s]:
            t0 = 0.22 + 0.08 * abs(i - 2) + 0.03 * i
            tr[g] = [("rotation", lambda t, s=s, b=b, t0=t0: liftc(s, b, 62 * closed(t, t0))),
                     ("scale", lambda t, t0=t0: (lambda k: (k, k, k))(1 - 0.35 * closed(t, t0 - 0.1)))]
        for g, a, i in LH[s]:
            t0 = 0.05 + 0.07 * abs(i - 2)
            tr[g] = [("rotation", lambda t, s=s, a=a, t0=t0: add((0.0, s * a * closed(t, t0), 0.0), lift(s, -10 * closed(t, t0)))),
                     ("scale", lambda t, t0=t0: (lambda k: (k, k, k))(1 - 0.4 * closed(t, t0)))]
        ang = lambda t: 360.0 * (1 if t >= L - 1e-9 else min(1.0, servo(t - 0.15, 9, 0.6)))
        tr[ROUE[s]] = [("rotation", lambda t, s=s: (s * ang(t), 0.0, 0.0))]
        tr[PIGNON[s]] = [("rotation", lambda t, s=s: (-2 * s * ang(t), 0.0, 0.0))]
    for k, g in enumerate(CHEM):
        t0 = 0.55 + 0.08 * k
        tr[g] = [("scale", lambda t, t0=t0: (1.0, 1.0 if t >= L - 1e-9 else 0.25 + 0.75 * min(1.08, servo(t - t0, 18, 0.5)) if t > t0 else 0.25, 1.0))]
    tr["aiguille_l"] = [("rotation", lambda t: (0.0, 0.0, -230 * bump(t, 0.6, 0.95, 1.05, 1.4)))]
    tr["levier_r"] = [("rotation", lambda t: lift(1, 26 * bump(t, 1.08, 1.12, 1.3, 1.45)))]
    for k in range(2):
        jet_tracks(tr, k + 1, 1.12 + 0.05 * k, 99.0)
    jet_tracks(tr, 3, 1.25, 99.0, big=0.7)
    emit_track(tr, 1, [(1.12, 6, 0.3)], 99.0)
    emit_track(tr, 2, [(1.17, 6, 0.3)], 99.0)
    emit_track(tr, 3, [(1.25, 5, 0.25)], 99.0)
    for k in (1, 2, 3):                           # par-dessus l'état : ctrl_emit s'ajoute, l'état vaut déjà -1
        f0 = tr[f"ctrl_emit@{k}"][0][1]
        tr[f"ctrl_emit@{k}"] = [("position", lambda t, f0=f0: (f0(t)[0] + 1.0, 0.0, 0.0))]
    return sound(anim("event_equip", L, tr, loop="once"), [1.12])


ANIMS = [idle_anim(), walk_anim(), run_anim(), sneak_anim(), equip_anim()]
assert len(ANIMS) <= 16

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
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
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko")
