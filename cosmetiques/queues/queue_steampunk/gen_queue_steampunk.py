"""Queue Steampunk v3 : colonne articulée à câbles (ensemble Steampunk, thème Mécanique). Design original.
Écrit queue_steampunk.png, queue_steampunk_e.png et .build/queue_steampunk_brut.bbmodel à côté de ce script.
Ancien générateur : .build/gen_avant.py (v2, anneaux à cliquet) et .build/gen_avant_v1.py.

Demande (2026-11-08) : « mécanique revoir tout sauf aile et hibou ». Une queue plus belle et plus logique.

Mécanisme (d'après les queues robotiques à câbles et les robots serpents, sources dans .claude/references/creatures/mecaniques.md) :
- dix vertèbres : chacune est une cloison octogonale de laiton (bulkhead) qui diminue vers la pointe, percée de quatre
  œillets d'acier ; une rotule d'acier entre deux vertèbres (joint universel : tangage et lacet découplés) tenue dans une
  coupelle de cuivre ; un tube d'acier creux relie la rotule à la cloison (la vapeur passe dedans jusqu'à la pointe) ;
- quatre câbles de cuivre (haut, bas, gauche, droite) passent par les œillets de toutes les cloisons : tirer un câble
  plie toute la colonne de son côté. Ils s'enroulent dans le boîtier de commande du bas du dos ;
- boîtier de commande sur une platine rivetée (≥ 2,37 px du centre du torse) : tambours de tangage sur ses flancs
  (engrenages qui tournent quand la queue monte ou descend), tambour de lacet sur le dessus (tourne quand elle part sur
  le côté), deux vérins latéraux qui poussent la première vertèbre (tige coulissante dans son cylindre, calculée), un
  manomètre relié au boîtier par un tuyau, deux voyants ambre de tension ;
- pointe : empennage de quatre ailettes de laiton (gouvernail d'équilibre, la pointe a un sens : elle stabilise et elle
  porte la buse), bague-témoin ambre allumée, buse évasée par où la vapeur de la colonne s'échappe et monte.
Modèle au repos droit vers +Z : tout le galbe vient des animations.

Mouvement : onde progressive fluide (forme du robot serpent : angle = A·sin(ωt − k·s), amplitude et retard croissants
vers la pointe), cap absolu de chaque vertèbre puis rotation exacte d'une vertèbre à l'autre. Cycle de pression (repos,
marche, vol…) : la pression monte doucement (aiguille par crans, queue qui se raidit et se relève, onde réduite), puis
décharge à la buse (jet + fumée qui monte), la queue se relâche avec un rebond amorti qui descend vers la pointe.

Fonctions avancées utilisées (docs/guide-cosmetiques.md 4 bis, 5 ter, 6.4), à juger en jeu (/cosmetique apercu) :
- `emit_mc_white_smoke` + `ctrl_emit` : vapeur de Minecraft à la buse, coupée hors des décharges et sous l'eau ;
- `trans_vapeur` + `ctrl_alpha` : jet modélisé, 3 plaques croisées en dégradé d'opacité, qui jaillit puis s'efface ;
- calque `_e` : cadran du manomètre, voyants du boîtier, bague-témoin de la pointe ; event_equip ;
- sons : un seul au repos (boucle de 20 s, décharge) et un à l'équipement (tools/sons.py) ; ni attack ni hurt (queue).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

AVEC_E = True
NOM = "queue_steampunk"
TEX = 512
TAU = 2 * math.pi
FPS = 12            # échantillonnage (interpolation linéaire, l'optimiseur simplifie)

# ------------------------------------------------------------------ matières (.claude/styles/steampunk.md)
BRASS = dict(hi=(236, 196, 112), base=(190, 142, 64), low=(112, 76, 32))
COPPER = dict(hi=(232, 150, 96), base=(176, 92, 52), low=(98, 46, 26))
STEEL = dict(hi=(136, 140, 150), base=(78, 82, 92), low=(38, 40, 48))
AMBER_HI, AMBER = np.array((255, 214, 130), np.float32), np.array((222, 150, 50), np.float32)


def A(c):
    return np.array(c, np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


def brush(h, w, seed, cells=6, amp=0.10):
    """Brossé léger (±5 %) : métal propre."""
    r = np.random.default_rng(seed)
    a = (r.random((max(2, h // cells), w)) * 255).astype(np.uint8)
    return (np.array(Image.fromarray(a, "L").resize((w, h), Image.BILINEAR), np.float32) / 255 - 0.5) * amp


def rivet(col, x, y, r, metal):
    h, w = col.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    col[np.hypot(xx + 0.5 - x, yy + 0.5 - y) <= r + 1.0] = A(metal["low"]) * 0.6
    col[np.hypot(xx + 0.5 - x, yy + 0.5 - y) <= r] = A(metal["base"])
    col[np.hypot(xx + 0.5 - x + r * 0.35, yy + 0.5 - y + r * 0.35) <= r * 0.5] = A(metal["hi"])


def solid(col):
    return np.dstack([np.clip(col, 0, 255), np.full(col.shape[:2], 255.0)]).astype(np.uint8)


def cutout(col, mask):
    out = np.zeros(mask.shape + (4,), np.uint8)
    c = np.clip(col, 0, 255)
    if mask.any():
        c[~mask] = c[mask].mean(axis=0)
    out[..., :3] = c.astype(np.uint8)
    out[..., 3] = mask * 255
    return out


def down(rgb_hi, m_hi, w, h):
    rgb = np.array(Image.fromarray(np.clip(rgb_hi, 0, 255).astype(np.uint8), "RGB").resize((w, h), Image.LANCZOS), np.float32)
    al = np.array(Image.fromarray(m_hi.astype(np.uint8) * 255, "L").resize((w, h), Image.LANCZOS)) > 110
    return cutout(rgb, al)


# ------------------------------------------------------------------ textures
def paint_band(metal, seed, LW=16, C=40, lip=3, rivets=0, rmetal=STEEL):
    """Flanc d'une bague ou d'une cloison : u = le long de la queue, v = autour. Lèvres claires, gorge, galbe."""
    v = np.abs((np.arange(C) + 0.5) / C - 0.5)[:, None] * 2
    col = A(metal["base"]) * np.ones((C, LW, 3), np.float32)
    col *= (1.12 - 0.3 * v ** 2)[..., None] * (1 + brush(C, LW, seed))[..., None]
    u = np.minimum(np.arange(LW) + 0.5, LW - np.arange(LW) - 0.5)[None, :] * np.ones((C, 1))
    col[(u >= lip) & (u < lip + 2)] = A(metal["low"]) * 0.85
    col[u < lip] = A(metal["hi"])
    col[(v > 0.88) & (u >= lip + 2)] *= 0.75
    for k in range(rivets):
        rivet(col, LW / 2, C * (k + 0.5) / rivets, 2.6, rmetal)
    return solid(col)


def paint_vert(metal, n=44, holes=True):
    """Face d'une cloison vertébrale : couronne claire, gorge, champ, quatre œillets de câble, rivets, moyeu."""
    yy, xx = np.mgrid[0:n, 0:n]
    dx, dy = (xx + 0.5 - n / 2) / (n / 2), (yy + 0.5 - n / 2) / (n / 2)
    rc, r = np.maximum(np.abs(dx), np.abs(dy)), np.hypot(dx, dy)
    col = A(metal["base"]) * np.ones((n, n, 3), np.float32) * (1 + brush(n, n, 7))[..., None]
    col *= (1.06 - 0.12 * r)[..., None]
    col[rc > 0.86] = A(metal["hi"])
    col[(rc > 0.74) & (rc <= 0.8)] = A(metal["low"])
    if holes:
        for cx, cy in ((0.62, 0), (-0.62, 0), (0, 0.62), (0, -0.62)):
            d = np.hypot(dx - cx, dy - cy)
            col[d < 0.17] = A(STEEL["hi"])
            col[d < 0.10] = A((30, 26, 24))
        for cx, cy in ((0.44, 0.44), (-0.44, 0.44), (0.44, -0.44), (-0.44, -0.44)):
            rivet(col, n / 2 + cx * n / 2, n / 2 + cy * n / 2, 2.4, COPPER)
    col[r < 0.34] = A(STEEL["base"])
    col[r < 0.27] = A(STEEL["hi"]) * 0.9
    col[r < 0.16] = A((34, 30, 30))
    return solid(col)


def paint_cap(metal, n=24, hole=STEEL):
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.maximum(np.abs(xx + 0.5 - n / 2), np.abs(yy + 0.5 - n / 2)) / (n / 2)
    col = A(metal["base"]) * np.ones((n, n, 3), np.float32)
    col[rr > 0.82] = A(metal["hi"])
    col[(rr > 0.62) & (rr <= 0.74)] = A(metal["low"])
    col[rr < 0.42] = A(hole["base"])
    col[rr < 0.24] = A(hole["low"])
    return solid(col)


def paint_ball(n=20):
    """Rotule d'acier poli : dégradé sphérique, reflet net en haut à gauche."""
    yy, xx = np.mgrid[0:n, 0:n]
    dx, dy = (xx + 0.5 - n / 2) / (n / 2), (yy + 0.5 - n / 2) / (n / 2)
    r = np.hypot(dx, dy)
    k = np.clip(1 - r / 1.25, 0, 1)
    col = lerp(A(STEEL["low"]), A(STEEL["hi"]) * 1.25, (k ** 0.9)[..., None])
    col[np.hypot(dx + 0.32, dy + 0.32) < 0.2] = A((214, 218, 226))
    return solid(col)


def paint_rod(metal, seed, W=64, H=12, grooves=4, bright=0.35):
    r = np.random.default_rng(seed)
    q = np.abs((np.arange(H) + 0.5) / H - 0.5)[:, None, None] * 2
    col = lerp(lerp(A(metal["hi"]), A(metal["base"]), bright), A(metal["low"]), q ** 1.2) * np.ones((H, W, 3), np.float32)
    col *= 0.96 + 0.08 * r.random((1, W, 1), np.float32)
    for x in np.linspace(4, W - 6, grooves).astype(int) if grooves else []:
        col[:, x:x + 2] *= 0.62
    return solid(col)


def paint_cable(W=64, H=8):
    """Câble de cuivre toronné : torons inclinés, clair au milieu."""
    jj, ii = np.mgrid[0:H, 0:W]
    q = np.abs((jj + 0.5) / H - 0.5) * 2
    ph = ((ii + jj * 0.9) / 3.2) % 1.0
    col = lerp(A(COPPER["hi"]), A(COPPER["low"]), (q ** 1.3)[..., None]) * np.ones((H, W, 3), np.float32)
    col *= (0.86 + 0.18 * np.clip(1 - np.abs(ph - 0.5) * 2.4, 0, 1))[..., None]
    return solid(col)


def paint_panel(W, H, seed, lenses=False, hole=False, rivets=True):
    """Panneau du boîtier : laiton, biseau clair, filet gravé, rivets ; face avant : voyants ambre et passage de la colonne."""
    col = A(BRASS["base"]) * np.ones((H, W, 3), np.float32) * (1 + brush(H, W, seed))[..., None]
    yy, xx = np.mgrid[0:H, 0:W]
    e = np.minimum.reduce([xx, yy, W - 1 - xx, H - 1 - yy])
    col[e < 3] = A(BRASS["hi"])
    col[(e >= 3) & (e < 5)] *= 0.62
    col[(e >= 7) & (e < 9)] = A(BRASS["low"])
    if rivets:
        for x, y in ((5.5, 5.5), (W - 5.5, 5.5), (5.5, H - 5.5), (W - 5.5, H - 5.5)):
            rivet(col, x, y, 2.6, COPPER)
    if hole:
        d = np.hypot(xx + 0.5 - W / 2, yy + 0.5 - H * 0.5)
        col[d < 9] = A(COPPER["hi"])
        col[d < 7] = A(COPPER["low"])
        col[d < 5] = A((30, 24, 22))
    if lenses:
        for cx in (W * 0.2, W * 0.8):
            d = np.hypot(xx + 0.5 - cx, yy + 0.5 - H * 0.28)
            col[d < 5.2] = A(BRASS["low"]) * 0.7
            col[d < 4.0] = AMBER
            col[np.hypot(xx + 0.5 - cx + 1.3, yy + 0.5 - H * 0.28 + 1.3) < 1.6] = AMBER_HI
    return solid(col)


def paint_plate(W=88, H=84):
    col = A(BRASS["base"]) * np.ones((H, W, 3), np.float32) * (1 + brush(H, W, 31))[..., None]
    yy, xx = np.mgrid[0:H, 0:W]
    e = np.minimum.reduce([xx, yy, W - 1 - xx, H - 1 - yy])
    ch = (np.minimum(xx, W - 1 - xx) + np.minimum(yy, H - 1 - yy)) < 12
    col[(e >= 9) & (e < 11)] = A(BRASS["low"])
    col[e < 4] = A(BRASS["hi"])
    col[(e >= 4) & (e < 6)] *= 0.6
    col[ch] = A(BRASS["low"]) * 0.5
    for x, y in ((7, 16), (W - 8, 16), (7, H - 16), (W - 8, H - 16), (W / 2, 6), (W / 2, H - 7)):
        rivet(col, x, y, 3.2, COPPER)
    return solid(col)


def paint_gear(n, teeth, metal, spokes=None, hole=0.26, h_t=0.16):
    ss = 4
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    dx, dy = (xx + 0.5 - N / 2) / (N / 2), -(yy + 0.5 - N / 2) / (N / 2)
    r, th = np.hypot(dx, dy), np.degrees(np.arctan2(dy, dx))
    pitch = 360 / teeth
    q = np.abs(((th + pitch / 2) % pitch) - pitch / 2) / pitch
    ro, rr = 0.98, 0.98 * (1 - h_t)
    edge = rr + (ro - rr) * np.clip((0.40 - q) / 0.17, 0, 1)
    m = (r <= edge) & (r >= hole)
    if spokes:
        ang = (th + 180 / spokes) % (360 / spokes) / (360 / spokes)
        m &= ~((r > 0.42) & (r < rr - 0.17) & (np.abs(ang - 0.5) < 0.28))
    mask = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((n, n), Image.LANCZOS)) > 110
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) / (n / 2)
    col = A(metal["base"]) * np.ones((n, n, 3), np.float32) * (1 + brush(n, n, teeth))[..., None]
    col[r > rr - 0.04] = A(metal["hi"])
    col[(r > rr - 0.14) & (r <= rr - 0.06)] *= 0.55
    col[r < hole + 0.12] = A(metal["hi"]) * 0.9
    return cutout(col, mask)


def paint_dial(n=32):
    yy, xx = np.mgrid[0:n, 0:n]
    dx, dy = (xx + 0.5 - n / 2) / (n / 2), -(yy + 0.5 - n / 2) / (n / 2)
    r, th = np.hypot(dx, dy), np.degrees(np.arctan2(dx, dy))
    col = A(COPPER["base"]) * np.ones((n, n, 3), np.float32)
    col[r < 0.98] = A(COPPER["hi"])
    col[r < 0.86] = A(COPPER["low"])
    col[r < 0.78] = A((236, 226, 196))
    tick = (r > 0.56) & (r < 0.74) & (np.abs(((th + 65) % 26) - 13) > 10.5) & (np.abs(th) < 70)
    col[tick] = A((50, 40, 34))
    col[(r > 0.5) & (r < 0.74) & (th > 40) & (th < 72)] = A((176, 44, 30))
    col[r < 0.14] = A(STEEL["low"])
    return solid(col)


def paint_mouth(n=32):
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.maximum(np.abs(xx + 0.5 - n / 2), np.abs(yy + 0.5 - n / 2)) / (n / 2)
    col = A(COPPER["hi"]) * np.ones((n, n, 3), np.float32)
    col[rr < 0.86] = A(COPPER["low"])
    col[rr < 0.72] = A((34, 24, 22))
    col[rr < 0.36] = A((20, 16, 16))
    return solid(col)


def paint_lampband(LW=14, C=40):
    """Bague-témoin : verre ambre entre deux lèvres de laiton, reflet clair."""
    u = np.minimum(np.arange(LW) + 0.5, LW - np.arange(LW) - 0.5)[None, :] * np.ones((C, 1))
    v = np.abs((np.arange(C) + 0.5) / C - 0.5)[:, None] * 2 * np.ones((1, LW))
    col = AMBER * np.ones((C, LW, 3), np.float32)
    col[(v < 0.35) & (u >= 4)] = AMBER_HI
    col[u < 3] = A(BRASS["hi"])
    col[(u >= 3) & (u < 4)] = A(BRASS["low"])
    return solid(col)


def paint_fin(W=80, H=104):
    """Ailette d'empennage (u = le long de la queue, v = envergure des deux côtés de l'axe) : en losange (pointe de flèche), liseré clair, nervure, rivets. Découpée par alpha."""
    ss = 4
    jj, ii = np.mgrid[0:H * ss, 0:W * ss]
    u, v = (ii + 0.5) / (W * ss), np.abs((jj + 0.5) / (H * ss) - 0.5) * 2
    span = np.where(u < 0.55, 0.2 + 0.78 * u / 0.55, 0.98 - (u - 0.55) / 0.45 * 0.72)
    m = (v <= span) & (u > 0.0) & (u < 0.985)
    # distance (en u-v normalisé, approchée) au bord : liseré
    dist = np.minimum(span - v, np.minimum(u, 0.985 - u) * W / H * 2 * 0.5)
    col = A(BRASS["base"]) * np.ones(u.shape + (3,), np.float32)
    col *= (1.05 - 0.15 * v)[..., None]
    col[(dist < 0.075) & m] = A(BRASS["hi"])
    col[(dist >= 0.075) & (dist < 0.11) & m] = A(BRASS["low"]) * 0.9
    col[(np.abs(v - span * 0.5) < 0.02) & (dist >= 0.11)] *= 0.72        # nervure
    out = down(col, m, W, H)
    c = out[..., :3].astype(np.float32)
    for uu, vv in ((0.32, 0.3), (0.62, 0.5)):
        for sgn in (-1, 1):
            rivet(c, uu * W, H / 2 + sgn * vv * H / 2 * 0.9, 2.4, COPPER)
    keep = out[..., 3] > 0
    out[..., :3] = np.where(keep[..., None], np.clip(c, 0, 255), out[..., :3]).astype(np.uint8)
    return out


def paint_vapeur(W=96, H=64):
    ss = 3
    jj, ii = np.mgrid[0:H * ss, 0:W * ss]
    u, v = (ii + 0.5) / (W * ss), ((jj + 0.5) / (H * ss) - 0.5) * 2
    puffs = [(0.08, 0.0, 0.20), (0.22, 0.06, 0.34), (0.38, -0.08, 0.48), (0.55, 0.1, 0.62), (0.72, -0.06, 0.74), (0.88, 0.08, 0.66)]
    d = np.zeros(u.shape, np.float32)
    light = np.zeros(u.shape, np.float32)
    asp = W / H / 2
    for cu, cv, rad in puffs:
        q = np.hypot((u - cu) * asp * 2, v - cv) / rad
        d = np.maximum(d, 1 - q)
        light = np.maximum(light, 1 - np.hypot((u - cu) * asp * 2 + 0.25 * rad, v - cv - 0.3 * rad) / rad)
    fade = lerp(1.0, 0.62, np.clip((u - 0.35) / 0.65, 0, 1))
    al = np.clip(d / 0.42, 0, 1) ** 0.8 * fade
    col = lerp(A((206, 212, 220)), A((250, 250, 248)), np.clip(light * 1.6, 0, 1)[..., None])
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    a8 = np.array(Image.fromarray((al * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(np.int32)
    a8[a8 < 8] = 0
    return np.dstack([rgb, np.clip(a8, 0, 254)]).astype(np.uint8)


TILES = {}
for nm, im in (("rim_brass", paint_band(BRASS, 11, LW=14, lip=3)), ("rim_copper", paint_band(COPPER, 12, LW=14, lip=3)),
               ("collar", paint_band(COPPER, 13, LW=16, C=32, lip=3)), ("tube", paint_rod(STEEL, 41, grooves=3)),
               ("cable", paint_cable()), ("cyl", paint_band(BRASS, 14, LW=56, C=20, lip=4, rivets=0)),
               ("rodp", paint_rod(STEEL, 42, grooves=0, bright=0.1)), ("pipe", paint_rod(COPPER, 43, grooves=2)),
               ("nozzle", paint_band(COPPER, 15, LW=40, C=32, lip=4)), ("lampband", paint_lampband()),
               ("fin", paint_fin()), ("eyelet", paint_band(STEEL, 16, LW=12, C=12, lip=2))):
    TILES[nm] = im
    TILES[nm + "_T"] = np.ascontiguousarray(im.transpose(1, 0, 2))
TILES.update(vert_brass=paint_vert(BRASS), vert_copper=paint_vert(COPPER), vertp_brass=paint_vert(BRASS, holes=False),
             vertp_copper=paint_vert(COPPER, holes=False), cap_brass=paint_cap(BRASS), cap_copper=paint_cap(COPPER),
             cap_steel=paint_cap(STEEL, hole=BRASS), ball=paint_ball(), plate=paint_plate(),
             box_side=paint_panel(56, 48, 51), box_front=paint_panel(64, 48, 52, lenses=True, hole=True),
             box_top=paint_panel(64, 56, 53), lug=paint_panel(20, 20, 54, rivets=False),
             gear_p=paint_gear(64, 14, BRASS, spokes=5), gear_y=paint_gear(56, 12, STEEL, spokes=4, hole=0.3),
             dial=paint_dial(), mouth=paint_mouth(), vapeur=paint_vapeur(),
             needle=solid(A((150, 30, 24)) * np.ones((8, 8, 3), np.float32)))


def pack():
    items = sorted(((n, t.shape[1], t.shape[0]) for n, t in TILES.items()), key=lambda it: (-it[2], -it[1]))
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
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
for n, im in TILES.items():
    u0, v0, u1, v1 = UV[n]
    tex[v0:v1, u0:u1] = im
tex[..., :3] &= 0xFC
tex[tex[..., 3] == 0] = 0
semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
u0, v0, u1, v1 = UV["vapeur"]
semi[v0:v1, u0:u1] = False
assert not semi.any(), "semi-transparence hors de la bouffée trans_"


def light_e(name, pred, gain):
    """Calque _e : sources nettes (cadran, voyants, bague-témoin), 150-225."""
    u0, v0, u1, v1 = UV[name]
    c = tex[v0:v1, u0:u1].astype(np.float32)
    lit = (c[..., 3] > 0) & pred(c)
    tex_e[v0:v1, u0:u1, :3] = np.where(lit[..., None], np.clip(c[..., :3] * gain, 0, 225), 0).astype(np.uint8)
    tex_e[v0:v1, u0:u1, 3] = np.where(lit, 255, 0)


ambre = lambda c: (c[..., 0] > 200) & (c[..., 2] < 150) & (c[..., 1] > 130)
light_e("dial", lambda c: c[..., :3].mean(axis=2) > 170, 0.62)
light_e("box_front", ambre, 0.88)
for nm in ("lampband", "lampband_T"):
    light_e(nm, ambre, 0.9)
assert set(np.unique(tex_e[..., 3])) <= {0, 255}


def b64(arr, fn):
    im = Image.fromarray(arr, "RGBA")
    im.save(fn, optimize=True)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


TEX_B64, TEX_E_B64 = b64(tex, f"{NOM}.png"), b64(tex_e, f"{NOM}_e.png")

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups and len(name) <= 64
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


def fl(t):
    return [t[2], t[1], t[0], t[3]]


def flv(t):
    return [t[0], t[3], t[2], t[1]]


def zfaces(long_, cap, cap_back=None, clear_ends=False):
    L, LT = UV[long_], UV[long_ + "_T"]
    f = {"west": list(L), "east": fl(L), "up": list(LT), "down": flv(LT)}
    if clear_ends:
        f.update(north=CLEAR, south=CLEAR)
    else:
        f.update(north=list(UV[cap_back or cap]), south=list(UV[cap]))
    return f


def zbox(g, name, x, y, z0, z1, a, long_, cap, octo=True, cap_back=None, cap_o=None, b=None, rot=(0, 0, 0), origin=None,
         clear_ends=False, rec=0.11):
    """Volume le long de Z centré sur (x, y), demi-section a (b en hauteur). octo : second pavé à 45° (section octogonale),
    en retrait aux bouts (jamais dans le même plan) ; cap_o : bouts du second pavé (sinon ceux du premier)."""
    b = a if b is None else b
    f = zfaces(long_, cap, cap_back, clear_ends)
    o = origin or (x, y, (z0 + z1) / 2)
    cube(g, name, (x - a, y - b, z0), (x + a, y + b, z1), o, rot, f)
    if octo:
        fo = dict(f)
        if cap_o and not clear_ends:
            fo.update(north=list(UV[cap_o]), south=list(UV[cap_o]))
        rz = (rot[0], rot[1], rot[2] + 45)
        cube(g, name + "o", (x - a * 0.95, y - b * 0.95, z0 + rec), (x + a * 0.95, y + b * 0.95, z1 - rec), o, rz, fo)


def allf(t):
    return {f: list(UV[t]) for f in ("north", "south", "east", "west", "up", "down")}


Y0 = 13.9
P0 = np.array((0.0, Y0, 5.55))        # première rotule = pivot de la queue

# ---- base : platine, boîtier de commande, tambours, manomètre, vérins
base = group("queue_base", P0)
_pl, _bb = UV["plate"], UV["cap_brass"]
cube(base, "platine", (-2.6, 12.6, 2.37), (2.6, 16.9, 2.87), (0, 14.75, 2.62), (0, 0, 0),
     {"south": list(_pl), "north": list(_bb), "east": list(UV["rim_brass_T"]), "west": list(UV["rim_brass_T"]),
      "up": list(UV["rim_brass"]), "down": list(UV["rim_brass"])})
BX0, BX1, BY0, BY1, BZ0, BZ1 = -1.25, 1.25, 12.95, 14.85, 2.6, 4.95
cube(base, "boitier", (BX0, BY0, BZ0), (BX1, BY1, BZ1), (0, Y0, 3.9), (0, 0, 0),
     {"south": list(UV["box_front"]), "north": CLEAR, "east": list(UV["box_side"]), "west": fl(UV["box_side"]),
      "up": list(UV["box_top"]), "down": list(UV["box_top"])})
GZ = 3.92
TAMB = []
for s in (-1, 1):
    nm = "tambour_" + ("d" if s > 0 else "g")
    g = group(nm, (s * 1.42, Y0, GZ), parent=base)
    x0, x1 = (1.38, 1.68) if s > 0 else (-1.68, -1.38)
    r_ = 0.98
    cube(g, nm, (x0, Y0 - r_, GZ - r_), (x1, Y0 + r_, GZ + r_), (s * 1.42, Y0, GZ), (0, 0, 0),
         {"east": list(UV["gear_p"]), "west": fl(UV["gear_p"]), "north": CLEAR, "south": CLEAR, "up": CLEAR, "down": CLEAR})
    cube(g, nm + "_axe", (1.1 if s > 0 else -1.82, Y0 - 0.22, GZ - 0.22), (1.82 if s > 0 else -1.1, Y0 + 0.22, GZ + 0.22),
         (s * 1.42, Y0, GZ), (0, 0, 0), allf("cap_steel"))
    TAMB.append(g)
GL = group("tambour_lacet", (0, BY1 + 0.17, 3.98), parent=base)
cube(GL, "tambour_lacet", (-0.8, BY1 + 0.13, 3.18), (0.8, BY1 + 0.43, 4.78), (0, BY1 + 0.17, 3.98), (0, 0, 0),
     {"up": list(UV["gear_y"]), "down": list(UV["gear_y"]), "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR})
cube(GL, "moyeu_lacet", (-0.22, BY1 - 0.12, 3.76), (0.22, BY1 + 0.6, 4.2), (0, BY1 + 0.2, 3.98), (0, 0, 0), allf("cap_brass"))
# manomètre relié au boîtier par un tuyau de cuivre
GY = 16.05
zbox(base, "manometre", 0, GY, 2.6, 3.27, 0.62, "rim_copper", "dial", cap_back="cap_copper", cap_o="cap_copper")
aig = group("aiguille", (0, GY, 3.39), parent=base)
cube(aig, "aiguille", (-0.08, GY - 0.08, 3.3), (0.08, GY + 0.5, 3.48), (0, GY, 3.39), (0, 0, 0), allf("needle"))
cube(base, "tuyau_mano", (-0.13, BY1 - 0.12, 2.98), (0.13, GY - 0.86, 3.24), (0, 15.1, 3.11), (0, 0, 0),
     {"east": list(UV["pipe_T"]), "west": list(UV["pipe_T"]), "north": list(UV["pipe_T"]), "south": list(UV["pipe_T"]),
      "up": CLEAR, "down": CLEAR})
# col de la colonne et coupelle de la première rotule
# vérins latéraux : cylindre (base) + tige (première vertèbre), axe calculé à chaque image
PX = 2.15
C_ = {s: np.array((s * PX, Y0, 3.2)) for s in (-1, 1)}
A0 = {s: np.array((s * PX, Y0, P0[2] + 0.55 * 0.55 + 0.2)) for s in (-1, 1)}
CYL = {}
for s in (-1, 1):
    sd = "d" if s > 0 else "g"
    cube(base, f"chape_verin_{sd}", (s * PX - 0.42, Y0 - 0.42, 2.6), (s * PX + 0.42, Y0 + 0.42, 3.42), (s * PX, Y0, 3.0), (0, 0, 0), allf("lug"))
    g = group(f"verin_{sd}", C_[s], parent=base)
    zbox(g, f"cylindre_{sd}", s * PX, Y0, 3.05, 5.2, 0.3, "cyl", "cap_brass", cap_back="cap_brass")
    CYL[s] = g

# ---- vertèbres
NS = 9
SS = [i / (NS - 1) for i in range(NS)]
LEN = [lerp(2.35, 1.6, s) for s in SS]
RD = [lerp(1.4, 0.7, s) for s in SS]          # demi-largeur de la cloison
RB = [lerp(0.55, 0.32, s) for s in SS]          # rayon de la rotule
TR = [lerp(0.3, 0.17, s) for s in SS]           # rayon du tube
JZ = [P0[2]]
for L_ in LEN:
    JZ.append(JZ[-1] + L_)
COPPER_V = {3, 6}
SEG, TIGE = [], {}


def disc_z(i):
    return JZ[i] + RB[i] * 0.55, JZ[i] + RB[i] * 0.55 + 0.4


for i in range(NS):
    SEG.append(group(f"vert{i}", (0, Y0, JZ[i]), parent=SEG[-1] if SEG else None))
for i in range(NS):
    g, J = SEG[i], JZ[i]
    rb = RB[i]
    # rotule (vue ronde sous tous les angles : trois pavés tournés)
    cube(g, f"rotule{i}", (-rb, Y0 - rb, J - rb), (rb, Y0 + rb, J + rb), (0, Y0, J), (0, 0, 0), allf("ball"))
    rr = rb - 0.12
    cube(g, f"rotule{i}x", (-rr, Y0 - rb * 0.97, J - rb * 0.97), (rr, Y0 + rb * 0.97, J + rb * 0.97), (0, Y0, J), (45, 0, 0), allf("ball"))
    cube(g, f"rotule{i}y", (-rb * 0.97, Y0 - rr, J - rb * 0.97), (rb * 0.97, Y0 + rr, J + rb * 0.97), (0, Y0, J), (0, 45, 0), allf("ball"))
    # cloison vertébrale
    mat = "copper" if i in COPPER_V else "brass"
    z0, z1 = disc_z(i)
    zbox(g, f"cloison{i}", 0, Y0, z0, z1, RD[i], f"rim_{mat}", f"vert_{mat}", cap_o=f"vertp_{mat}")
    # œillets d'acier aux quatre câbles
    for k, (ex, ey) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        if i == 0 and ey == 0:
            continue        # première vertèbre : les oreilles des vérins prennent la place des œillets latéraux
        c = RD[i] + 0.04
        hw, r0, r1 = 0.25, RD[i] - 0.2, RD[i] + 0.3
        if ex:
            frm, to = (min(ex * r0, ex * r1), Y0 - hw, z0 - 0.13), (max(ex * r0, ex * r1), Y0 + hw, z1 + 0.13)
        else:
            frm, to = (-hw, Y0 + min(ey * r0, ey * r1), z0 - 0.13), (hw, Y0 + max(ey * r0, ey * r1), z1 + 0.13)
        cube(g, f"oeillet{i}_{k}", frm, to, (0, Y0, J), (0, 0, 0), allf("eyelet"))
    if i == 0:      # oreilles des vérins
        for s in (-1, 1):
            sd = "d" if s > 0 else "g"
            cube(g, f"oreille_{sd}", (min(s * (RD[0] - 0.2), s * (PX + 0.27)), Y0 - 0.27, z0 - 0.14),
                 (max(s * (RD[0] - 0.2), s * (PX + 0.27)), Y0 + 0.27, z1 + 0.14), (0, Y0, J), (0, 0, 0), allf("lug"))
            tg = group(f"tige_{sd}", A0[s], parent=g)
            zbox(tg, f"tige_{sd}", s * PX, Y0, A0[s][2] - 2.3, A0[s][2], 0.15, "rodp", "cap_steel", octo=False)
            TIGE[s] = tg
    # tube creux jusqu'à la coupelle suivante
    zn = JZ[i + 1]
    rbn = RB[i + 1] if i + 1 < NS else 0.3
    zbox(g, f"tube{i}", 0, Y0, z0 + 0.1, zn - rbn - 0.16 if i + 1 < NS else zn - 0.1, TR[i], "tube", "cap_steel", clear_ends=True)
    if i + 1 < NS:
        zbox(g, f"coupelle{i}", 0, Y0, zn - rbn - 0.3, zn - rbn * 0.3, rbn + 0.14, "collar", "cap_copper")
        # câbles jusqu'aux œillets de la cloison suivante
        za = z1 + 0.03
        zb = JZ[i + 1] + RB[i + 1] * 0.55 - 0.03
        ra, rbb = RD[i] + 0.04, RD[i + 1] + 0.04
        Lc = zb - za
        ang = math.degrees(math.atan2(ra - rbb, Lc))
        zm = (za + zb) / 2
        rm = (ra + rbb) / 2
        Lh = math.hypot(Lc, ra - rbb) / 2
        cf = {"east": list(UV["cable"]), "west": fl(UV["cable"]), "up": list(UV["cable_T"]), "down": flv(UV["cable_T"]),
              "north": CLEAR, "south": CLEAR}
        cft = {"north": CLEAR, "south": CLEAR, "east": list(UV["cable"]), "west": fl(UV["cable"]),
               "up": list(UV["cable_T"]), "down": flv(UV["cable_T"])}
        h = 0.15
        cube(g, f"cable{i}_h", (-h, Y0 + rm - h, zm - Lh), (h, Y0 + rm + h, zm + Lh), (0, Y0 + rm, zm), (ang, 0, 0), cft)
        cube(g, f"cable{i}_b", (-h, Y0 - rm - h, zm - Lh), (h, Y0 - rm + h, zm + Lh), (0, Y0 - rm, zm), (-ang, 0, 0), cft)
        if i > 0:
            cube(g, f"cable{i}_d", (rm - h, Y0 - h, zm - Lh), (rm + h, Y0 + h, zm + Lh), (rm, Y0, zm), (0, -ang, 0), cf)
            cube(g, f"cable{i}_g", (-rm - h, Y0 - h, zm - Lh), (-rm + h, Y0 + h, zm + Lh), (-rm, Y0, zm), (0, ang, 0), cf)
# coupelle de la première rotule (dans la base)
zbox(base, "coupelle_base", 0, Y0, BZ1 - 0.25, P0[2] - RB[0] * 0.3, RB[0] + 0.15, "collar", "cap_copper")

# ---- pointe : empennage, bague-témoin, buse
JT = JZ[NS]
tip = group("pointe", (0, Y0, JT), parent=SEG[-1])
zbox(tip, "manchon", 0, Y0, JT - 0.32, JT + 0.62, 0.36, "collar", "cap_copper", rec=0.06)
zbox(tip, "temoin", 0, Y0, JT + 0.4, JT + 0.95, 0.45, "lampband", "cap_brass", rec=0.16)
zbox(tip, "fut", 0, Y0, JT + 0.73, JT + 3.3, 0.33, "nozzle", "cap_copper", clear_ends=True, rec=0.04)
FZ0, FZ1, FS = JT + 0.3, JT + 3.3, 1.85
cube(tip, "ailette_v", (-0.15, Y0 - FS, FZ0), (0.15, Y0 + FS, FZ1), (0, Y0, (FZ0 + FZ1) / 2), (0, 0, 0),
     {"west": list(UV["fin"]), "east": fl(UV["fin"]), "north": CLEAR, "south": CLEAR, "up": CLEAR, "down": CLEAR})
cube(tip, "ailette_h", (-FS, Y0 - 0.15, FZ0 + 0.03), (FS, Y0 + 0.15, FZ1 - 0.03), (0, Y0, (FZ0 + FZ1) / 2), (0, 0, 0),
     {"up": list(UV["fin_T"]), "down": flv(UV["fin_T"]), "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR})
zbox(tip, "pavillon0", 0, Y0, JT + 3.15, JT + 3.6, 0.4, "nozzle", "cap_copper", rec=0.06)
zbox(tip, "pavillon1", 0, Y0, JT + 3.5, JT + 3.9, 0.52, "nozzle", "mouth", cap_back="cap_copper", cap_o="cap_copper", rec=0.14)
ZM = JT + 3.9
EM = group("emit_mc_white_smoke", (0, Y0, ZM + 0.05), parent=tip, rotation=(90, 0, 0))    # +Y du groupe = axe de la buse (+Z)
CE = group("ctrl_emit", (0, Y0, ZM + 0.05), parent=EM)
VG = group("trans_vapeur", (0, Y0, ZM - 0.3), parent=tip)
CA = group("ctrl_alpha", (0, Y0, ZM - 0.3), parent=VG)
_va = UV["vapeur"]
for k, ang in enumerate((0, 60, 120)):
    cube(VG, f"bouffee{k}", (-0.15 + 0.01 * k, Y0 - 1.6, ZM - 0.3), (0.15 + 0.01 * k, Y0 + 1.6, ZM - 0.3 + 4.2), (0, Y0, ZM), (0, 0, ang),
         {"west": list(_va), "east": fl(_va), "north": CLEAR, "south": CLEAR, "up": CLEAR, "down": CLEAR})


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "rotation": [0, 0, 0], "children": [bone(base), bone(SEG[0])]}]

# ------------------------------------------------------------------ animations
# Pour la queue qui part vers +Z : pitch > 0 relève la pointe, yaw > 0 la porte vers +X (droite du joueur).
# Seul endroit à toucher si la convention change (guide 3 ; essentiel.md, Axes).
SX, SY, SZ = -1, +1, +1


def mirror(pitch, yaw, roll=0.0):
    return SX * pitch, SY * yaw, SZ * roll


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def cran(ts, tau=0.03, per=0.13):
    if ts <= 0:
        return 0.0
    return 1 - math.exp(-ts / tau) * math.cos(TAU * ts / per)


def curve(*pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]

    def f(s):
        for a, b, u, v in zip(xs, xs[1:], ys, ys[1:]):
            if s <= b:
                return lerp(u, v, sm(s, a, b)) if s >= a else u
        return ys[-1]
    return f


ZERO = curve((0, 0), (1, 0))


def rotm(rx, ry, rz):
    """Ordre du mod et du renderer : X, puis Y, puis Z (R = Rz Ry Rx)."""
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
            @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))


def euler(R):
    s = -R[2, 0]
    if abs(s) < 0.99999:
        ex, ey, ez = math.atan2(R[2, 1], R[2, 2]), math.asin(s), math.atan2(R[1, 0], R[0, 0])
    elif s > 0:
        ex, ey, ez = math.atan2(R[0, 1], R[1, 1]), math.pi / 2, 0.0
    else:
        ex, ey, ez = math.atan2(-R[0, 1], R[1, 1]), -math.pi / 2, 0.0
    assert np.abs(rotm(*map(math.degrees, (ex, ey, ez))) - R).max() < 1e-3, "euler : reconstruction"
    return math.degrees(ex), math.degrees(ey), math.degrees(ez)


def frame(pitch, yaw):
    return rotm(*mirror(pitch, yaw))


def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 3)), "y": str(round(v[1] + 0.0, 3)), "z": str(round(v[2] + 0.0, 3))}],
            "time": round(t, 4), "interpolation": "linear"}


def make_anim(name, L, tracks, loop="loop", fps=FPS):
    n = max(16, int(math.ceil(L * fps)))
    times = [i * L / n for i in range(n + 1)]
    A_ = {}
    for g, chans in tracks.items():
        kfs = []
        for ch, f in chans.items():
            kfs += [kf(ch, t, f(t)) for t in times]
        A_[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": L, "snapping": 24, "selected": name == "idle", "animators": A_}


class Pression:
    """Une décharge par boucle à tv (s) : la pression monte doucement pendant `rise` s avant, puis tombe d'un coup
    (constante rel s) avec un rebond amorti (période per s). puff : taille du jet (0 = aucune vapeur, sous l'eau)."""

    def __init__(self, L, tv, rise, rel=0.12, per=0.5, puff=1.0, dp=1.0):
        self.L, self.tv, self.rise, self.rel, self.per, self.puff, self.dp = L, tv, min(rise, 0.8 * L), rel, per, puff, min(dp, 0.8 * L)

    def d(self, t):
        return (t - self.tv) % self.L

    def P(self, t):
        if self.puff <= 0 and self.rise <= 0:
            return 0.0
        d = self.d(t)
        u = d - (self.L - self.rise)
        if u >= 0:
            return sm(u, 0, self.rise)
        return math.exp(-d / self.rel) * math.cos(TAU * d / self.per)


def needle_p(p):
    """L'aiguille monte par crans (8 graduations)."""
    q = max(0.0, min(1.0, p)) * 8
    k = math.floor(q)
    return (k + sm(q - k, 0.0, 0.3)) / 8


def state(name, L, pr, rest_p, tense_p=None, rest_y=ZERO, Ay=8.0, my=1, ky=0.7, Ap=2.0, mp=1, kp=0.7, lag=0.035, roll_tip=0.0):
    """Cap absolu de chaque vertèbre (pitch, yaw) = pose (repos -> tendue selon la pression) + onde progressive
    A·w(s)·sin(ωt − 2π·k·s), w croissant vers la pointe ; la pression arrive avec un retard croissant (lag par vertèbre).
    Les clés sont les rotations exactes d'une vertèbre à la suivante."""
    tense_p = tense_p or (lambda s: rest_p(s) + 10 * s)

    def head(i, t):
        s = SS[i]
        p = pr.P(t - i * lag)
        w = 0.18 + 0.82 * s
        damp = 1 - 0.45 * max(0.0, p)
        pitch = lerp(rest_p(s), tense_p(s), p) + Ap * w * damp * math.sin(TAU * (mp * t / L - kp * s) + 1.2)
        yaw = rest_y(s) + Ay * w * damp * math.sin(TAU * (my * t / L - ky * s))
        return pitch, yaw

    tr = {}
    for i, g in enumerate(SEG):
        def rot(t, i=i):
            if not i:
                return euler(frame(*head(0, t)))
            return euler(frame(*head(i - 1, t)).T @ frame(*head(i, t)))
        tr[g] = {"rotation": rot}
    # vérins : axe du cylindre vers l'oreille de la première vertèbre, la tige suit (télescopique)
    for s in (-1, 1):
        def aim(t, s=s):
            R0 = frame(*head(0, t))
            Aw = P0 + R0 @ (A0[s] - P0)
            d = Aw - C_[s]
            d = d / np.linalg.norm(d)
            pitch, yaw = math.degrees(math.asin(d[1])), math.degrees(math.atan2(d[0], d[2]))
            return R0, frame(pitch, yaw)
        tr[CYL[s]] = {"rotation": lambda t, aim=aim: euler(aim(t)[1])}
        tr[TIGE[s]] = {"rotation": lambda t, aim=aim: (lambda R0, Rc: euler(R0.T @ Rc))(*aim(t))}
    # tambours : enroulent les câbles (tangage sur les flancs, lacet sur le dessus), rapport 3:1 sur la courbure totale
    for g in TAMB:
        tr[g] = {"rotation": lambda t: mirror(3.0 * (head(NS - 1, t)[0] - head(0, t)[0]) + 2.0 * head(0, t)[0], 0)}
    tr[GL] = {"rotation": lambda t: (0.0, 3.0 * (head(NS - 1, t)[1] - head(0, t)[1]) + 2.0 * head(0, t)[1], 0.0)}
    # manomètre : monte par crans avec la pression, retombe à la décharge
    tr[aig] = {"rotation": lambda t: mirror(0, 0, 55 - 120 * needle_p(pr.P(t)))}
    # pointe : petit recul à la décharge
    dp = pr.dp

    def tipr(t):
        x = pr.d(t - NS * lag)
        k = pr.puff * 5 * math.exp(-x / 0.08) * math.sin(TAU * x / 0.18) if pr.puff > 0 else 0.0
        return mirror(k, 0, roll_tip)
    tr[tip] = {"rotation": tipr}

    def vap(t):
        x = pr.d(t - NS * lag)
        if pr.puff <= 0 or x >= dp:
            return (0.01, 0.01, 0.01)
        a = pr.puff
        if x < 0.12 * dp:
            k = sm(x, 0, 0.12 * dp)
            return (max(0.01, 0.6 * a * k), max(0.01, 0.6 * a * k), max(0.01, 0.8 * a * k))
        if x < 0.7 * dp:
            k = sm(x, 0.12 * dp, 0.7 * dp)
            return (a * lerp(0.6, 1.2, k), a * lerp(0.6, 1.2, k), a * lerp(0.8, 1.5, k))
        k = sm(x, 0.7 * dp, dp)
        return (max(0.01, a * lerp(1.2, 0.0, k)), max(0.01, a * lerp(1.2, 0.0, k)), a * lerp(1.5, 1.8, k))
    tr[VG] = {"scale": vap}
    tr[CA] = {"position": lambda t: (-1.0 if pr.puff <= 0 or pr.d(t - NS * lag) >= dp else -sm(pr.d(t - NS * lag), 0.3 * dp, dp), 0.0, 0.0)}
    tr[CE] = {"position": lambda t: (-1.0 + (5 * bump(pr.d(t - NS * lag), 0.0, 0.03, 0.3 * dp, 0.4 * dp) if pr.puff > 0 else 0.0), 0.0, 0.0)}
    a = make_anim(name, L, tr)
    if pr.puff > 0:
        a["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
            {"channel": "sound", "data_points": [{"effect": "block.fire.extinguish", "file": ""}], "time": round(pr.tv + NS * lag, 3)}]}
    return a, head


# idle 20 s : cinq ondes lentes de 4 s ; la pression monte de 11 à 16 s, décharge à 16 s (un son), relâche.
idle, H_IDLE = state("idle", 20.0, Pression(20.0, 16.0, 5.0, rel=0.16, per=0.7, puff=1.0, dp=1.3),
                     curve((0, -40), (0.35, -22), (0.7, 18), (1, 58)), curve((0, -30), (0.35, -4), (0.7, 42), (1, 80)),
                     rest_y=curve((0, 0), (1, 8)), Ay=11, my=5, ky=0.75, Ap=3, mp=5, kp=0.6, lag=0.045)
walk, _ = state("walk", 1.6, Pression(1.6, 1.2, 0.0, rel=0.1, per=0.4, puff=0.0),
                curve((0, -22), (0.5, -6), (1, 14)), Ay=13, my=1, ky=0.7, Ap=3, mp=2, kp=0.5, lag=0.03)
run, _ = state("run", 1.0, Pression(1.0, 0.5, 0.0, rel=0.06, per=0.24, puff=0.6, dp=0.4),
               curve((0, -10), (0.5, -3), (1, 5)), Ay=7, my=1, ky=0.85, Ap=2.5, mp=2, kp=0.6, lag=0.02)
sneak, _ = state("sneak", 3.0, Pression(3.0, 2.0, 0.0, puff=0.0),
                 curve((0, -42), (0.3, -22), (0.65, 40), (1, 96)), Ay=4, my=1, ky=0.6, Ap=2, mp=1, lag=0.04)
fly, _ = state("fly", 2.4, Pression(2.4, 1.8, 1.0, rel=0.1, per=0.45, puff=0.8, dp=0.9),
               curve((0, -40), (0.5, -24), (1, -6)), curve((0, -34), (0.5, -14), (1, 6)), Ay=10, my=1, ky=0.8, Ap=4, mp=1, lag=0.035)
glide, _ = state("glide", 3.6, Pression(3.6, 2.6, 1.4, rel=0.12, per=0.5, puff=0.9, dp=1.0),
                 curve((0, -48), (0.4, -70), (1, -80)), curve((0, -46), (0.4, -66), (1, -74)), Ay=8, my=2, ky=0.8, Ap=2, mp=2, lag=0.04)
fall, _ = state("fall", 1.5, Pression(1.5, 1.0, 0.0, puff=0.0),
                curve((0, -6), (0.5, 12), (1, 34)), Ay=14, my=1, ky=0.6, Ap=4, mp=1, lag=0.025)
swim, _ = state("swim", 2.0, Pression(2.0, 1.0, 0.0, puff=0.0),
                curve((0, -48), (0.4, -74), (1, -84)), Ay=18, my=1, ky=1.0, Ap=2, mp=1, lag=0.05)
mount, _ = state("mount", 3.0, Pression(3.0, 2.2, 0.0, puff=0.0),
                 curve((0, -8), (0.5, 6), (1, 24)), rest_y=curve((0, 4), (0.4, 14), (1, 40)), Ay=4, my=1, ky=0.6, Ap=2, mp=1, lag=0.04)
sleep, _ = state("sleep", 4.0, Pression(4.0, 3.0, 0.0, puff=0.0),
                 curve((0, -40), (0.4, -65), (1, -55)), rest_y=curve((0, 15), (0.4, 60), (1, 110)), Ay=1.5, my=1, ky=0.5, Ap=1.5, mp=1, lag=0.06)


def equip_anim():
    """event_equip 2 s (s'ajoute à l'état) : la colonne sort du boîtier enroulée, se déroule vertèbre par vertèbre
    (départ sec, léger dépassement), les tambours dévident les câbles, le témoin s'allume, première décharge (un son)."""
    L = 2.0
    tr = {SEG[0]: {"scale": lambda t: (lambda k: (k, k, k))(0.35 + 0.65 * sm(t, 0.0, 0.3))}}
    for i, g in enumerate(SEG):
        t0 = 0.25 + 0.1 * i
        curl = 34.0 if i else 16.0
        r_ = tr.setdefault(g, {})
        r_["rotation"] = lambda t, t0=t0, curl=curl: mirror(curl * (1 - (cran(t - t0, 0.04, 0.2) if t > t0 else 0.0)) * (1 - sm(t, 1.85, 2.0)), 0.0)
    for g in TAMB:
        tr[g] = {"rotation": lambda t: mirror(-720 * sm(t, 0.25, 1.3), 0)}
    tr[aig] = {"rotation": lambda t: mirror(0, 0, -100 * bump(t, 0.5, 1.2, 1.4, 1.6))}
    tr[CE] = {"position": lambda t: (5 * bump(t, 1.45, 1.48, 1.75, 1.85), 0.0, 0.0)}
    a = make_anim("event_equip", L, tr, loop="once", fps=24)
    a["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
        {"channel": "sound", "data_points": [{"effect": "block.fire.extinguish", "file": ""}], "time": 1.45}]}
    return a


equip = equip_anim()
ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, equip]
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": TEX_B64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": TEX_E_B64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
from ambiance import ajouter_ambiance
ajouter_ambiance(model)

# faces proches (.claude/references/procedures/remise-aux-regles.md), repris de la v2
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
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(model["animations"]), "anims ;",
      sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
