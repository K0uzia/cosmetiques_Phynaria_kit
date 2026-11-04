"""Queue mécanique : queue-instrument à vapeur, ensemble Steampunk (thème Mécanique). Design original.
Écrit queue_mecanique.png, queue_mecanique_e.png et .build/queue_mecanique_brut.bbmodel à côté de ce script.

Pas d'animal : ni épines, ni écailles, ni membrane. Une platine de laiton rivetée sur le bas du dos porte un moyeu,
une chape et un axe ; un manomètre à aiguille au-dessus de l'axe. Puis 9 anneaux de laiton octogonaux (deux en cuivre)
de diamètre décroissant, chacun traversé par un axe d'articulation, reliés par une tige d'acier et un ressort à boudin
(plaque découpée par alpha autour de la tige). Au bout, une soupape de cuivre évasée avec un voyant ambre.
Modèle au repos droit vers +Z : tout le galbe vient des animations.

Mouvement : chaque articulation avance par crans (cliquet : départ sec, léger dépassement, arrêt), l'onde descend de
segment en segment. Cycle de pression : la queue se raidit cran par cran (ressorts comprimés, aiguille qui grimpe),
la soupape tremble, décharge (bouffée, émission x3), puis la queue se relâche avec un rebond amorti.

Fonctions anticipées utilisées (.claude/rules/conventions-anticipees.md) :
- `emit_mc_white_smoke` : vapeur vanilla à la bouche de la soupape, direction +Y du groupe = axe de la buse ;
- `trans_vapeur` : bouffée modélisée, 3 plaques croisées en dégradé d'opacité (alpha 1–254), lisible en cutout (seuil 50 %) ;
- `ctrl_alpha` (enfant de trans_vapeur) : opacité = 1 + x ; x de 0 (normal) à -1 (invisible) pendant que la bouffée se résorbe ;
- son `block.fire.extinguish` (piste Effets, guide 6.5) à chaque décharge.
La cadence de la vapeur vanilla se règle côté staff (pas de ctrl_emit). Sans ces fonctions : bouffée en cutout qui jaillit puis
rétrécit (scale), le reste inchangé. À juger en jeu avec /cosmetique apercu.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # True : embarque le calque _e en seconde texture (correctif du mod annoncé le 2026-11-03, à vérifier en jeu).
NOM = "queue_mecanique"
TEX = 512
TAU = 2 * math.pi
FPS = 32            # échantillonnage des animations (l'optimiseur simplifie les arrêts)

# ------------------------------------------------------------------ matières (.claude/styles/steampunk.md)
BRASS = dict(hi=(236, 196, 112), base=(190, 142, 64), low=(112, 76, 32))
COPPER = dict(hi=(232, 150, 96), base=(176, 92, 52), low=(98, 46, 26))
STEEL = dict(hi=(136, 140, 150), base=(78, 82, 92), low=(38, 40, 48))
PATINA = np.array((132, 186, 160), np.float32)
PATINA_D = np.array((82, 138, 116), np.float32)
AMBER_HI, AMBER = np.array((255, 210, 120), np.float32), np.array((220, 150, 50), np.float32)


def A(c):
    return np.array(c, np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


def noise(h, w, cells, seed):
    r = np.random.default_rng(seed)
    a = (r.random((max(2, int(cells * h / max(h, w))) + 2, max(2, int(cells * w / max(h, w))) + 2)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((w, h), Image.BICUBIC), np.float32) / 255


def rivet(col, x, y, r, metal):
    """Rivet peint : anneau sombre, tête, éclat. Au moins 3 texels de rayon."""
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


def paint_ring(metal, seed, rmetal, LW=28, C=56):
    """Bague : u = le long de la queue, v = autour. Lèvres claires aux deux bouts, gorge sombre, rivet au milieu de la face."""
    r = np.random.default_rng(seed)
    streak = np.array(Image.fromarray((r.random((max(4, C // 6), LW)) * 255).astype(np.uint8), "L").resize((LW, C), Image.BILINEAR), np.float32) / 255 - 0.5
    v = np.abs((np.arange(C) + 0.5) / C - 0.5)[:, None] * 2
    col = A(metal["base"]) * np.ones((C, LW, 3), np.float32)
    col *= (1.12 - 0.3 * v ** 2)[..., None] * (1 + 0.16 * streak)[..., None]      # galbe : milieu de face plus clair
    u = np.minimum(np.arange(LW) + 0.5, LW - np.arange(LW) - 0.5)[None, :] * np.ones((C, 1))
    col[(u >= 3) & (u < 5)] = A(metal["low"]) * 0.8                               # gorge sous la lèvre
    col[u < 3] = A(metal["hi"]) * (0.95 + 0.1 * streak[u < 3])[..., None]         # lèvre claire : l'anneau se lit net
    n = noise(C, LW, 9, seed + 1)
    creux = (u >= 3) & (u < 6)
    col[creux & (n > 0.62)] = PATINA_D                                             # vert-de-gris dans les creux seulement
    col[(v > 0.86) & (u >= 5)] *= 0.72                                             # arête de la face (raccord avec la voisine)
    rivet(col, LW / 2, C / 2, 3.2, rmetal)
    return solid(col)


def paint_cap(metal, n=24, hole=STEEL):
    """Bout d'un anneau ou d'un axe : couronne claire, gorge, moyeu d'acier."""
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.maximum(np.abs(xx + 0.5 - n / 2), np.abs(yy + 0.5 - n / 2)) / (n / 2)
    col = A(metal["base"]) * np.ones((n, n, 3), np.float32)
    col[rr > 0.84] = A(metal["hi"])
    col[(rr > 0.66) & (rr <= 0.78)] = A(metal["low"])
    col[rr < 0.42] = A(hole["base"])
    col[rr < 0.24] = A(hole["low"])
    return solid(col)


def paint_rod(metal, seed, W=64, H=12, grooves=4):
    """Tige usinée : dégradé cylindrique en travers, gorges d'usinage."""
    r = np.random.default_rng(seed)
    q = np.abs((np.arange(H) + 0.5) / H - 0.5)[:, None, None] * 2
    col = lerp(lerp(A(metal["hi"]), A(metal["base"]), 0.35), A(metal["low"]), q ** 1.2) * np.ones((H, W, 3), np.float32)
    col *= 0.94 + 0.12 * r.random((1, W, 1), np.float32)
    for x in np.linspace(4, W - 6, grooves).astype(int):
        col[:, x:x + 2] *= 0.6
    return solid(col)


def paint_spring(W=64, H=32, coils=5.0):
    """Ressort à boudin, découpé par alpha : spires inclinées (un quart de pas par face), tête claire, flancs sombres."""
    ss = 4
    jj, ii = np.mgrid[0:H * ss, 0:W * ss]
    u, v = (ii + 0.5) / (W * ss), (jj + 0.5) / (H * ss)
    ph = (u * coils + v * 0.25) % 1.0
    m = ph < 0.56
    prof = np.clip(1 - np.abs(ph - 0.28) / 0.28, 0, 1)
    col = lerp(A(STEEL["low"]), A(STEEL["hi"]) * 1.12, (prof ** 0.8)[..., None])
    col = lerp(col, A(COPPER["base"]) * 0.8, 0.12)                                 # acier bleui, pointe chaude
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS), np.float32)
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110
    return cutout(rgb, al)


def paint_plate(W=88, H=92):
    """Platine : laiton brossé, biseau clair, filet gravé, rivets, vert-de-gris sous les rivets."""
    r = np.random.default_rng(31)
    streak = np.array(Image.fromarray((r.random((H, W // 10)) * 255).astype(np.uint8), "L").resize((W, H), Image.BILINEAR), np.float32) / 255 - 0.5
    col = A(BRASS["base"]) * np.ones((H, W, 3), np.float32) * (1 + 0.18 * streak)[..., None]
    yy, xx = np.mgrid[0:H, 0:W]
    e = np.minimum.reduce([xx, yy, W - 1 - xx, H - 1 - yy])
    # coins chanfreinés
    ch = (np.minimum(xx, W - 1 - xx) + np.minimum(yy, H - 1 - yy)) < 12
    col[(e >= 9) & (e < 11)] = A(BRASS["low"])                                     # filet gravé
    n = noise(H, W, 14, 32)
    col[(e >= 8) & (e < 13) & (n > 0.6)] = PATINA_D
    col[e < 4] = A(BRASS["hi"])
    col[(e >= 4) & (e < 6)] *= 0.6
    col[ch] = A(BRASS["low"]) * 0.5
    for x, y in ((7, 18), (W - 8, 18), (7, H - 18), (W - 8, H - 18), (W / 2, 6), (W / 2, H - 7)):
        col[int(y):int(y) + 10, int(x) - 2:int(x) + 2] = lerp(col[int(y):int(y) + 10, int(x) - 2:int(x) + 2], PATINA, 0.8)
        rivet(col, x, y, 3.4, COPPER)
    return solid(col)


def paint_dial(n=32):
    """Cadran du manomètre : fond crème, graduations, zone rouge à droite (pression haute), couronne de cuivre."""
    yy, xx = np.mgrid[0:n, 0:n]
    dx, dy = (xx + 0.5 - n / 2) / (n / 2), -(yy + 0.5 - n / 2) / (n / 2)
    r, th = np.hypot(dx, dy), np.degrees(np.arctan2(dx, dy))        # th : 0 en haut, + vers la droite
    col = A(COPPER["base"]) * np.ones((n, n, 3), np.float32)
    col[r < 0.98] = A(COPPER["hi"])
    col[r < 0.86] = A(COPPER["low"])
    col[r < 0.78] = A((232, 222, 192))
    tick = (r > 0.56) & (r < 0.74) & (np.abs(((th + 65) % 26) - 13) > 10.5) & (np.abs(th) < 70)
    col[tick] = A((50, 40, 34))
    col[(r > 0.5) & (r < 0.74) & (th > 40) & (th < 72)] = A((176, 44, 30))
    col[r < 0.14] = A(STEEL["low"])
    return solid(col)


def paint_mouth(n=32):
    """Bouche de la soupape : intérieur sombre, lèvre de cuivre claire."""
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.maximum(np.abs(xx + 0.5 - n / 2), np.abs(yy + 0.5 - n / 2)) / (n / 2)
    col = A(COPPER["hi"]) * np.ones((n, n, 3), np.float32)
    col[rr < 0.86] = A(COPPER["low"])
    col[rr < 0.72] = A((34, 24, 22))
    col[rr < 0.36] = A((20, 16, 16))
    return solid(col)


def paint_lamp(n=12):
    yy, xx = np.mgrid[0:n, 0:n]
    e = np.minimum.reduce([xx, yy, n - 1 - xx, n - 1 - yy])
    col = AMBER * np.ones((n, n, 3), np.float32)
    col[e < 2] = A(BRASS["low"])
    col[(xx < 6) & (yy < 6) & (e >= 2)] = AMBER_HI
    return solid(col)


def paint_disc(metal, n=24):
    """Joue de la chape : disque découpé par alpha, rivet au centre."""
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) / (n / 2)
    col = A(metal["base"]) * np.ones((n, n, 3), np.float32)
    col[r > 0.8] = A(metal["hi"])
    col[(r > 0.66) & (r <= 0.8)] = A(metal["low"])
    rivet(col, n / 2, n / 2, 3.2, STEEL)
    return cutout(col, r < 0.98)


def paint_vapeur(W=96, H=64):
    """Bouffée de vapeur, u = depuis la buse. Dégradé d'opacité (pour trans_) ; le cœur dépasse 50 % pour rester lisible en cutout."""
    ss = 3
    jj, ii = np.mgrid[0:H * ss, 0:W * ss]
    u, v = (ii + 0.5) / (W * ss), ((jj + 0.5) / (H * ss) - 0.5) * 2
    puffs = [(0.08, 0.0, 0.20), (0.22, 0.06, 0.34), (0.38, -0.08, 0.48), (0.55, 0.1, 0.62), (0.72, -0.06, 0.74), (0.88, 0.08, 0.66)]
    d = np.zeros(u.shape, np.float32)
    light = np.zeros(u.shape, np.float32)
    asp = W / H / 2       # un rayon en v vaut asp fois plus de px qu'en u
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
    out = np.dstack([rgb, np.clip(a8, 0, 254)]).astype(np.uint8)
    assert (out[..., 3] > 127).mean() > 0.3, "bouffée illisible en cutout"
    return out


TILES = {}
for nm, im in (("ring_brass", paint_ring(BRASS, 11, COPPER)), ("ring_copper", paint_ring(COPPER, 21, BRASS)),
               ("rod_steel", paint_rod(STEEL, 41)), ("rod_brass", paint_rod(BRASS, 42, grooves=3)), ("rod_copper", paint_rod(COPPER, 43, grooves=3)),
               ("spring", paint_spring())):
    TILES[nm] = im
    TILES[nm + "_T"] = np.ascontiguousarray(im.transpose(1, 0, 2))            # faces up/down : la longueur suit v
TILES.update(cap_brass=paint_cap(BRASS), cap_copper=paint_cap(COPPER), cap_steel=paint_cap(STEEL, hole=BRASS),
             plate=paint_plate(), dial=paint_dial(), mouth=paint_mouth(), lamp=paint_lamp(), disc=paint_disc(BRASS),
             needle=solid(A((150, 30, 24)) * np.ones((8, 8, 3), np.float32)), vapeur=paint_vapeur())


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
# calque _e : voyant ambre seulement, plus un souffle très sombre au fond de la bouche
u0, v0, u1, v1 = UV["lamp"]
tex_e[v0 + 2:v1 - 2, u0 + 2:u1 - 2] = (210, 130, 40, 255)
u0, v0, u1, v1 = UV["mouth"]
_yy, _xx = np.mgrid[0:v1 - v0, 0:u1 - u0]
_rr = np.maximum(np.abs(_xx + 0.5 - 16), np.abs(_yy + 0.5 - 16)) / 16
tex_e[v0:v1, u0:u1][(_rr < 0.72) & (_rr > 0.36)] = (60, 30, 10, 255)
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
    """UV retournée horizontalement."""
    return [t[2], t[1], t[0], t[3]]


def flv(t):
    return [t[0], t[3], t[2], t[1]]


def zfaces(long_, cap, cap_back=None, clear_ends=False):
    """Pavé le long de Z : west/east (u le long de Z), up/down (tuile transposée), north/south (bouts)."""
    L, LT = UV[long_], UV[long_ + "_T"]
    f = {"west": list(L), "east": fl(L), "up": list(LT), "down": flv(LT)}
    if clear_ends:
        f.update(north=CLEAR, south=CLEAR)
    else:
        f.update(north=list(UV[cap_back or cap]), south=list(UV[cap]))
    return f


def zbox(g, name, x, y, z0, z1, a, long_, cap, octo=True, cap_back=None, clear_ends=False, b=None):
    """Volume le long de Z centré sur (x, y), demi-section a (et b en hauteur). octo : second pavé à 45° (section octogonale)."""
    b = a if b is None else b
    f = zfaces(long_, cap, cap_back, clear_ends)
    o = (x, y, (z0 + z1) / 2)
    cube(g, name, (x - a, y - b, z0), (x + a, y + b, z1), o, (0, 0, 0), f)
    if octo:
        cube(g, name + "o", (x - a * 0.96, y - b * 0.96, z0 + 0.03), (x + a * 0.96, y + b * 0.96, z1 - 0.03), o, (0, 0, 45), f)


def xbox(g, name, x0, x1, y, z, a, long_, cap):
    """Axe le long de X (axes d'articulation) : octogonal, chapeaux aux deux bouts."""
    L = UV[long_]
    f = {"south": list(L), "north": fl(L), "up": list(L), "down": list(L), "east": list(UV[cap]), "west": list(UV[cap])}
    o = ((x0 + x1) / 2, y, z)
    cube(g, name, (x0, y - a, z - a), (x1, y + a, z + a), o, (0, 0, 0), f)
    cube(g, name + "o", (x0 + 0.03, y - a * 0.96, z - a * 0.96), (x1 - 0.03, y + a * 0.96, z + a * 0.96), o, (45, 0, 0), f)


# ---- racine : platine rivetée, moyeu, chape, axe, manomètre
P0 = np.array((0.0, 13.7, 4.05))      # axe de la chape = pivot de la queue
Y0 = P0[1]
base = group("queue_base", P0)
_pl, _bb = UV["plate"], UV["rod_brass"]
cube(base, "platine", (-2.2, 12.9, 2.05), (2.2, 17.3, 2.55), (0, 15.1, 2.3), (0, 0, 0),
     {"south": list(_pl), "north": list(_bb), "east": list(_bb), "west": list(_bb), "up": list(_bb), "down": list(_bb)})
zbox(base, "moyeu", 0, Y0, 2.5, 3.5, 0.72, "rod_steel", "cap_steel")
_d = UV["disc"]
for s in (-1, 1):
    x0, x1 = (0.62, 0.92) if s > 0 else (-0.92, -0.62)
    cube(base, f"joue_{'d' if s > 0 else 'g'}", (x0, Y0 - 0.8, P0[2] - 0.8), (x1, Y0 + 0.8, P0[2] + 0.8), (0, Y0, P0[2]), (0, 0, 0),
         {"east": list(_d), "west": fl(_d), "north": CLEAR, "south": CLEAR, "up": CLEAR, "down": CLEAR})
xbox(base, "axe", -1.12, 1.12, Y0, P0[2], 0.2, "rod_steel", "cap_brass")
GY = 16.0
zbox(base, "manometre", 0, GY, 2.5, 2.86, 0.6, "rod_copper", "dial", cap_back="cap_copper")
_ni = UV["needle"]
aig = group("aiguille", (0, GY, 2.95), parent=base)
cube(aig, "aiguille", (-0.08, GY - 0.08, 2.89), (0.08, GY + 0.52, 3.09), (0, GY, 2.95), (0, 0, 0), {f: list(_ni) for f in ("north", "south", "east", "west", "up", "down")})

# ---- segments : anneau (pivot au centre de l'anneau), axe d'articulation, tige, ressort
NS = 9
SPANS = [2.3, 2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6]
D = [lerp(2.9, 1.4, i / (NS - 1)) for i in range(NS)]
RL = [lerp(0.95, 0.6, i / (NS - 1)) for i in range(NS)]
CZ = [P0[2] + 1.6]
for L_ in SPANS:
    CZ.append(CZ[-1] + L_)
COPPER_RINGS = {3, 6}
SEG, SPR, GAP = [], [], []
for i in range(NS):
    SEG.append(group(f"tail{i}", P0 if i == 0 else (0, Y0, CZ[i]), parent=SEG[-1] if SEG else None))
for i in range(NS):
    g, a = SEG[i], 0.4 * D[i]
    mat = "copper" if i in COPPER_RINGS else "brass"
    zbox(g, f"anneau{i}", 0, Y0, CZ[i] - RL[i] / 2, CZ[i] + RL[i] / 2, a, f"ring_{mat}", f"cap_{mat}")
    pa = max(0.17, 0.085 * D[i])
    px = 1.37 * a + 0.22
    xbox(g, f"pivot{i}", -px, px, Y0, CZ[i], pa, "rod_steel", "cap_brass" if mat == "copper" else "cap_copper")
    if i == 0:      # tenon entre les joues de la chape
        zbox(g, "tenon", 0, Y0, P0[2] - 0.55, CZ[0] - RL[0] / 2 + 0.1, 0.5, "rod_steel", "cap_steel", octo=False, b=0.55)
    if i < NS - 1:
        zbox(g, f"tige{i}", 0, Y0, CZ[i], CZ[i + 1], 0.15 * D[i], "rod_steel", "cap_steel", octo=False)
        z0, z1 = CZ[i] + RL[i] / 2 - 0.1, CZ[i + 1] - RL[i + 1] / 2 + 0.1
        sp = group(f"ressort{i}", (0, Y0, z0), parent=g)
        sa = 0.29 * (D[i] + D[i + 1]) / 2
        zbox(sp, f"spire{i}", 0, Y0, z0, z1, sa, "spring", "cap_steel", clear_ends=True)
        SPR.append(sp)
        GAP.append(z1 - z0)

# ---- soupape : col, corps à voyant ambre, pavillon évasé en trois étages
tip = SEG[-1]
ZE = CZ[-1] + RL[-1] / 2
sou = group("soupape", (0, Y0, ZE), parent=tip)
zbox(sou, "col", 0, Y0, ZE - 0.1, ZE + 0.62, 0.3, "rod_copper", "cap_copper")
zbox(sou, "corps", 0, Y0, ZE + 0.6, ZE + 1.32, 0.48, "ring_brass", "cap_brass")
_la = UV["lamp"]
cube(sou, "voyant", (-0.2, Y0 + 0.4, ZE + 0.76), (0.2, Y0 + 0.84, ZE + 1.16), (0, Y0, ZE + 0.96), (0, 0, 0), {f: list(_la) for f in ("north", "south", "east", "west", "up", "down")})
for k, (za, zb, a) in enumerate(((1.3, 1.76, 0.4), (1.74, 2.16, 0.56), (2.14, 2.5, 0.72))):
    zbox(sou, f"pavillon{k}", 0, Y0, ZE + za, ZE + zb, a, "ring_copper", "mouth" if k == 2 else "cap_copper", cap_back="cap_copper")
ZM = ZE + 2.5
EM = group("emit_mc_white_smoke", (0, Y0, ZM + 0.05), parent=sou, rotation=(90, 0, 0))    # +Y du groupe = axe de la buse (+Z)
VG = group("trans_vapeur", (0, Y0, ZM - 0.35), parent=sou)
CA = group("ctrl_alpha", (0, Y0, ZM - 0.35), parent=VG)
_va = UV["vapeur"]
for k, ang in enumerate((0, 60, 120)):
    cube(VG, f"bouffee{k}", (-0.15 + 0.01 * k, Y0 - 1.7, ZM - 0.35), (0.15 + 0.01 * k, Y0 + 1.7, ZM - 0.35 + 4.6), (0, Y0, ZM), (0, 0, ang),
         {"west": list(_va), "east": fl(_va), "north": CLEAR, "south": CLEAR, "up": CLEAR, "down": CLEAR})


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "rotation": [0, 0, 0], "children": [bone(base), bone(SEG[0])]}]

# ------------------------------------------------------------------ animations
# Intention, pour la queue qui part vers +Z : pitch > 0 relève la pointe, yaw > 0 la porte vers +X (droite du joueur).
# MIROIR D'AXES : seul endroit à toucher si la convention du mod change. Guide, section 3 : +X = le haut part vers l'arrière, donc ce qui
# pointe vers +Z descend ; +Y = le côté droit avance, donc ce qui pointe vers +Z part vers +X ; +Z = le côté droit monte.
SX, SY, SZ = -1, +1, +1
PZ = +1             # position : +Z vers l'arrière (non vérifié en jeu : seuls +X et +Y sont décrits par le guide)


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


TAU_C, PER_C = 0.03, 0.13       # cran : départ sec (constante 0,03 s), dépassement d'environ 11 %, rappel en 0,13 s


def cran(ts):
    """Avance d'un cran au temps ts (s) depuis le tic : 0 -> 1, un dépassement, arrêt."""
    if ts <= 0:
        return 0.0
    return 1 - math.exp(-ts / TAU_C) * math.cos(TAU * ts / PER_C)


def palier(t, L, n):
    """Temps normalisé (0..1) déformé en n paliers par boucle : le mouvement avance par tics et s'arrête entre deux."""
    y = (t % L) / L * n
    k = math.floor(y)
    return (k + cran((y - k) * L / n)) / n


class Etat:
    """Cycle de pression d'un état. n tics par boucle ; la pression monte d'un cran à chacun des nc premiers ; tenue jusqu'au tic nd,
    décharge (rebond amorti, constante rel s, période per s) ; bouffée de taille puff, durée dp."""

    def __init__(self, L, n, nc, nd, rel=0.12, per=0.55, puff=1.0, dp=1.1, delay=0.04):
        self.L, self.n, self.nc, self.nd, self.rel, self.per = L, n, nc, nd, rel, per
        self.puff, self.dp, self.delay = puff, min(dp, 0.85 * L), delay
        self.Ls = L / n
        self.td = nd * self.Ls

    def P(self, t):
        t = t % self.L
        if t >= self.td:
            x = t - self.td
            return math.exp(-x / self.rel) * math.cos(TAU * x / self.per)
        y = t / self.Ls
        k = math.floor(y)
        if k >= self.nc:
            return 1.0
        return (k + cran(t - k * self.Ls)) / self.nc

    def hold(self, t):
        """Enveloppe de la tenue (soupape qui tremble), nulle aux bouts."""
        t = t % self.L
        a = self.nc * self.Ls
        return bump(t, a, a + 0.1, self.td - 0.08, self.td) if self.td - a > 0.2 else 0.0

    def tau(self, t):
        return (t - self.td) % self.L


def curve(*pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]

    def f(s):
        for a, b, u, v in zip(xs, xs[1:], ys, ys[1:]):
            if s <= b:
                return lerp(u, v, sm(s, a, b))
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
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx. Les écarts entre segments restent loin du blocage de cardan."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def frame(pitch, yaw):
    """Orientation absolue d'un segment (dans le repère du torse) pour un cap donné."""
    return rotm(*mirror(pitch, yaw))
SS = [i / (NS - 1) for i in range(NS)]


def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 3)), "y": str(round(v[1] + 0.0, 3)), "z": str(round(v[2] + 0.0, 3))}],
            "time": round(t, 4), "interpolation": "linear"}


def make_anim(name, L, tracks, loop="loop"):
    n = max(8, int(math.ceil(L * FPS)))
    times = [i * L / n for i in range(n + 1)]
    A_ = {}
    for g, chans in tracks.items():
        kfs = []
        for ch, f in chans.items():
            kfs += [kf(ch, t, f(t)) for t in times]
        A_[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": L, "snapping": 24, "selected": name == "idle", "animators": A_}


def state(name, E, rest_p, tense_p, rest_y=ZERO, tense_y=None, sway=0.0, m=1, sway_p=0.0, spring=0.2):
    """Cap absolu de chaque segment = pose de repos -> pose tendue selon la pression + balancement à cliquet ; les clés sont les écarts
    entre segments voisins. Segment i : même horloge, retardée de i * delay (l'onde descend de la base vers la soupape)."""
    tense_y = tense_y or rest_y
    L = E.L

    def head(i, t):
        s, tt = SS[i], t - i * E.delay
        p = E.P(tt)
        w = 0.25 + 0.75 * s
        ph = TAU * m * palier(tt, L, E.n)
        return (lerp(rest_p(s), tense_p(s), p) + sway_p * w * math.sin(ph + 1.3),
                lerp(rest_y(s), tense_y(s), p) + sway * w * math.sin(ph))

    tr = {}
    for i, g in enumerate(SEG):
        def rot(t, i=i):
            if not i:
                return mirror(*head(0, t))
            return euler(frame(*head(i - 1, t)).T @ frame(*head(i, t)))     # rotation exacte d'un segment à l'autre
        tr[g] = {"rotation": rot}
        if i:       # le segment suit son ressort, qui se comprime avec la pression
            tr[g]["position"] = lambda t, i=i: (0.0, 0.0, PZ * (-spring * E.P(t - (i - 1) * E.delay)) * GAP[i - 1])
    for j, sp in enumerate(SPR):
        tr[sp] = {"scale": lambda t, j=j: (1.0, 1.0, 1.0 - spring * E.P(t - j * E.delay))}
    # manomètre : l'aiguille grimpe cran par cran, frémit pendant la tenue, retombe à la décharge
    tr[aig] = {"rotation": lambda t: mirror(0, 0, 55 - 120 * E.P(t) + 3.0 * E.hold(t) * math.sin(TAU * 9 * t))}
    # soupape : tremble pendant la tenue, sursaute à la décharge
    tr[sou] = {"rotation": lambda t: mirror(1.6 * E.hold(t) * math.sin(TAU * 14 * t) + 5 * E.puff * math.exp(-E.tau(t) / 0.08) * math.sin(TAU * E.tau(t) / 0.16), 0)}
    dp = E.dp

    def vap(t):
        x = E.tau(t)
        if E.puff <= 0 or x >= dp:
            return (0.01, 0.01, 0.01)
        a = E.puff
        if x < 0.15 * dp:
            k = sm(x, 0, 0.15 * dp)
            return (max(0.01, 0.7 * a * k), max(0.01, 0.7 * a * k), max(0.01, 0.8 * a * k))
        if x < 0.72 * dp:
            k = sm(x, 0.15 * dp, 0.72 * dp)
            return (a * lerp(0.7, 1.25, k), a * lerp(0.7, 1.25, k), a * lerp(0.8, 1.6, k))
        k = sm(x, 0.72 * dp, dp)
        return (max(0.01, a * lerp(1.25, 0.0, k)), max(0.01, a * lerp(1.25, 0.0, k)), a * lerp(1.6, 1.9, k))

    tr[VG] = {"scale": vap}
    # ctrl_alpha : opacité = 1 + x (guide 4 bis) ; 0 = normal, -1 = invisible
    tr[CA] = {"position": lambda t: (-1.0 if E.puff <= 0 or E.tau(t) >= dp else -sm(E.tau(t), 0.3 * dp, dp), 0.0, 0.0)}
    a = make_anim(name, L, tr)
    if E.puff > 0:      # sifflement de vapeur à la décharge (guide 6.5)
        a["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
            {"channel": "sound", "data_points": [{"effect": "block.fire.extinguish", "file": ""}], "time": round(E.td, 3)}]}
    return a


# idle 8 s : 16 tics de 0,5 s. La pression monte en 8 tics (4 s), tenue 1 s, décharge à 5 s, relâche. Balancement : 2 allers-retours.
idle = state("idle", Etat(8.0, 16, 8, 10, rel=0.14, per=0.6, puff=1.0, dp=1.2, delay=0.045),
             curve((0, -32), (0.35, -12), (0.7, 22), (1, 48)), curve((0, -14), (0.35, 8), (0.7, 38), (1, 60)), sway=9, m=2, sway_p=2)
# walk 1,6 s : 8 tics (0,2 s), une petite décharge par foulée, balancement au rythme du pas
walk = state("walk", Etat(1.6, 8, 3, 4, rel=0.08, per=0.34, puff=0.65, dp=0.7, delay=0.025),
             curve((0, -24), (0.5, -6), (1, 16)), curve((0, -14), (0.5, 4), (1, 22)), sway=12, m=1, sway_p=2)
# run 1,0 s : tendue vers l'arrière, 4 tics, forte bouffée à chaque cycle (locomotive)
run = state("run", Etat(1.0, 4, 2, 2, rel=0.06, per=0.24, puff=1.0, dp=0.45, delay=0.02),
            curve((0, -9), (0.5, -3), (1, 5)), curve((0, -3), (0.5, 3), (1, 8)), sway=5, m=1, sway_p=1.5, spring=0.15)
# sneak 3 s : repliée en crochet, petite bouffée discrète
sneak = state("sneak", Etat(3.0, 6, 3, 4, rel=0.12, per=0.5, puff=0.45, dp=0.8, delay=0.04),
              curve((0, -60), (0.3, -28), (0.65, 44), (1, 112)), curve((0, -54), (0.3, -20), (0.65, 52), (1, 120)), sway=3, m=1, sway_p=1)
# fly 2,4 s : joueur debout, la queue traîne en arrière et en bas comme un gouvernail
fly = state("fly", Etat(2.4, 8, 4, 5, rel=0.1, per=0.45, puff=0.9, dp=0.9, delay=0.035),
            curve((0, -44), (0.5, -26), (1, -6)), curve((0, -30), (0.5, -10), (1, 6)), sway=10, m=1, sway_p=3)
# glide 3,6 s : joueur couché, la queue file dans l'axe du corps, vers les pieds ; ondulation à cliquet
glide = state("glide", Etat(3.6, 12, 6, 8, rel=0.12, per=0.5, puff=1.0, dp=1.0, delay=0.04),
              curve((0, -80), (0.5, -86), (1, -84)), curve((0, -78), (0.5, -81), (1, -76)), sway=7, m=2, sway_p=1)
# fall 1,5 s : relevée, ouverte pour l'équilibre
fall = state("fall", Etat(1.5, 6, 2, 3, rel=0.08, per=0.36, puff=0.8, dp=0.6, delay=0.025),
             curve((0, -8), (0.5, 12), (1, 34)), curve((0, 6), (0.5, 24), (1, 44)), sway=14, m=1, sway_p=3)
# swim 2 s : dans l'axe du corps, vers les pieds, ondulation ample ; pas de vapeur sous l'eau
swim = state("swim", Etat(2.0, 8, 3, 4, rel=0.1, per=0.4, puff=0.0, delay=0.06),
             curve((0, -80), (1, -86)), curve((0, -76), (1, -80)), sway=18, m=1, sway_p=1)
# mount 3 s : horizontale, pointe relevée et portée sur le côté (au-dessus de la monture)
mount = state("mount", Etat(3.0, 6, 3, 4, rel=0.12, per=0.5, puff=0.7, dp=0.9, delay=0.04),
              curve((0, -6), (0.5, 6), (1, 24)), curve((0, 2), (0.5, 14), (1, 30)),
              curve((0, 0), (0.4, 12), (1, 40)), curve((0, 0), (0.4, 14), (1, 44)), sway=3, m=1, sway_p=1)
# sleep 4 s : posée sur le côté, tics lents, petite bouffée de « ronflement »
sleep = state("sleep", Etat(4.0, 4, 2, 3, rel=0.2, per=0.8, puff=0.35, dp=1.0, delay=0.06),
              curve((0, -5), (0.25, -25), (0.5, -70), (1, -88)), curve((0, -3), (0.25, -22), (0.5, -66), (1, -85)),
              curve((0, 75), (0.25, 135), (0.5, 130), (1, 120)), curve((0, 75), (0.25, 136), (0.5, 131), (1, 121)), sway=1.5, m=1, spring=0.1)


def impulse(name, cur, pitch_a, yaw_a, lag):
    """attack / hurt : une fois par-dessus l'état, seulement les segments (écarts entre voisins), dernière image à zéro."""
    L = 0.8
    env = lambda t: 1 - sm(t, 0.68, 0.8)

    def head(i, t):
        v = cur(t - lag * i) * env(t)
        return pitch_a(SS[i]) * v, yaw_a(SS[i]) * v
    tr = {}
    for i, g in enumerate(SEG):
        def rot(t, i=i):
            p1, y1 = head(i, t)
            p0, y0 = head(i - 1, t) if i else (0.0, 0.0)
            return mirror(p1 - p0, y1 - y0)
        tr[g] = {"rotation": rot}
    a = make_anim(name, L, tr, loop="once")
    return a


def coup(t):
    """Trois crans rapides vers le haut (0,06 s chacun), puis décharge brusque et rebond amorti."""
    if t < 0:
        return 0.0
    if t < 0.24:
        k = math.floor(t / 0.08)
        return (k + cran(t - k * 0.08)) / 3
    x = t - 0.24
    return math.exp(-x / 0.06) * math.cos(TAU * x / 0.2)


attack = impulse("attack", coup, lambda s: 8 + 22 * s, lambda s: 4 + 10 * s, 0.015)


def sursaut(t):
    """Choc : la queue part d'un coup vers le bas et sur le côté, puis vibre en s'amortissant."""
    if t < 0:
        return 0.0
    return cran(t) * math.exp(-t / 0.18) * (1 + 0.35 * math.sin(TAU * t * 11))


hurt = impulse("hurt", sursaut, lambda s: -(6 + 10 * s), lambda s: 9 * math.sin(1.5 + 4 * s), 0.012)

ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, attack, hurt]
assert len(ANIMS) <= 16
assert 80 <= len(elements) <= 140, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": TEX_B64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": TEX_E_B64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
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
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
