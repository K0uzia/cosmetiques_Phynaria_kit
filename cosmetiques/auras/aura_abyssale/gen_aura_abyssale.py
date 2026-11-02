"""Aura abyssale : 6 éclats d'os et 2 griffes en orbite lente autour de la taille et du torse. Design original, à porter avec ailes_abyssales.
Écrit aura_abyssale.png, aura_abyssale_e.png et .build/aura_abyssale_brut.bbmodel à côté de ce script.

Chaque pièce a sa chaîne de 4 groupes sous `body` :
  orb_<p> (inclinaison fixe du plan) > spin_<p> (Y, exactement 360° par boucle) > rad_<p> (flottement Y, rayon, balancement)
  > burst_<p> (animé par `hurt` seul, pour rester juste que le mod remplace ou additionne les pistes).
Un éclat = deux plaques croisées découpées par alpha, autour d'une arête pleine effilée où court la veine.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

NOM = "aura_abyssale"
AVEC_E = False      # True : embarque le calque _e en seconde texture. False tant que le bug du mod n'est pas corrigé.
TEX = 256
TAU = 2 * math.pi
DENS = 24           # texels par px du modèle pour les images d'éclats

C_DARK = np.array((14, 11, 19), np.float32)
C_BASE = np.array((30, 25, 38), np.float32)
C_HIGH = np.array((66, 54, 82), np.float32)
C_RIM = np.array((118, 94, 148), np.float32)
C_AURA = np.array((22, 66, 40), np.float32)
C_VEIN = np.array((96, 200, 44), np.float32)
C_VCORE = np.array((150, 244, 70), np.float32)
C_E = np.array((132, 255, 72), np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ images
def rgba(rgb, al):
    out = np.dstack([np.clip(rgb, 0, 255), al * 255.0]).astype(np.uint8)
    if al.any():
        out[~al, :3] = out[al][:, :3].mean(axis=0).astype(np.uint8)
    return out


def emissive(line, al):
    m = line & al
    out = np.zeros(al.shape + (4,), np.uint8)
    out[m, :3] = C_E.astype(np.uint8)
    out[m, 3] = 255
    return out


def paint_shard(seed, W=120, H=44):
    """Éclat vu à plat : base à gauche, pointe à droite. Silhouette anguleuse ; une fissure verte de chaque côté de l'arête."""
    ss = 4
    r = np.random.default_rng(seed)
    ts = [0.0, 0.14, 0.34, 0.52, 0.7, 0.86]
    prof = [0.1, 0.58, 1.0, 0.74, 0.44, 0.2]
    top = [(t, 0.5 - 0.47 * k * r.uniform(0.8, 1.0)) for t, k in zip(ts, prof)] + [(0.995, 0.46)]
    bot = [(t, 0.5 + 0.47 * k * r.uniform(0.8, 1.0)) for t, k in zip(ts, prof)] + [(0.995, 0.54)]
    poly = [((0.012 + x * 0.976) * W * ss, y * H * ss) for x, y in top + bot[::-1]]
    mask = Image.new("L", (W * ss, H * ss), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    vein, core = Image.new("L", mask.size, 0), Image.new("L", mask.size, 0)
    vd, cd = ImageDraw.Draw(vein), ImageDraw.Draw(core)
    for sgn, ts_ in ((1, (0.2, 0.3, 0.42, 0.54, 0.68)), (-1, (0.24, 0.35, 0.47, 0.6, 0.76))):
        path = []
        for i, t in enumerate(ts_):
            off = (0.17 + 0.13 * (i % 2)) * (1 - 0.55 * t) * r.uniform(0.92, 1.08)
            path.append((t * W * ss, (0.5 + sgn * off) * H * ss))
        vd.line(path, fill=255, width=5 * ss, joint="curve")
        cd.line(path, fill=255, width=2 * ss, joint="curve")
    fm = np.array(mask.filter(ImageFilter.GaussianBlur(H * ss * 0.13)), np.float32) / 255
    gy, gx = np.mgrid[0:H * ss, 0:W * ss]
    u = (gx + 0.5) / (W * ss)
    grain = np.sin(u * 44 + gy * 0.02 * ss + seed)
    c = lerp(C_BASE, C_HIGH, np.clip((fm - 0.55) * 1.7, 0, 1)[..., None] * 0.65) * (1 + 0.07 * grain)[..., None]
    c = lerp(c, C_DARK, np.clip(0.3 - u * 1.6, 0, 1)[..., None])
    rim = np.clip((0.55 - fm) * 3.4, 0, 1) * (np.array(mask) > 127)
    c = lerp(c, C_RIM, rim[..., None] * 0.8)
    v = np.array(vein.filter(ImageFilter.GaussianBlur(5 * ss)), np.float32) / 255
    c = lerp(c, C_AURA, np.clip(v * 1.3, 0, 1)[..., None] * 0.55)
    c = lerp(c, C_VEIN, (np.array(vein) > 127)[..., None] * 1.0)
    c = lerp(c, C_VCORE, (np.array(core) > 127)[..., None] * 1.0)
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS), np.float32)
    al = np.array(mask.resize((W, H), Image.LANCZOS)) > 110
    line = np.array(core.resize((W, H), Image.LANCZOS)) > 100
    return rgba(rgb, al), emissive(line, al)


def paint_spine(W=64, H=16):
    """Arête : charbon, bande de veine au centre. Long : u ; travers : v."""
    q = np.abs((np.arange(H) + 0.5) / H - 0.5)[:, None] * 2
    u = (np.arange(W) + 0.5)[None, :] / W
    c = lerp(C_HIGH * 0.8, C_DARK, (q ** 0.8)[..., None])
    c = np.where((q < 0.42)[..., None], C_AURA, c)
    c = np.where((q < 0.27)[..., None], C_VEIN, c)
    c = c * (0.92 + 0.08 * np.sin(u * 30))[..., None]
    al = np.ones((H, W), bool)
    return rgba(c, al), emissive(q < 0.27 * np.ones_like(u), al)


def paint_bone(W=48, H=12):
    q = np.abs((np.arange(H) + 0.5) / H - 0.5)[:, None] * 2
    u = (np.arange(W) + 0.5)[None, :] / W
    c = lerp(C_HIGH * 0.85, C_DARK, (q ** 1.1)[..., None]) * (0.9 + 0.14 * np.sin(u * 34))[..., None]
    al = np.ones((H, W), bool)
    return rgba(c, al), np.zeros((H, W, 4), np.uint8)


HOOK_BB = (-0.20, 0.46)
CURVE = 0.30


def hook_shape(L, curve=CURVE):
    """Griffe : axe recourbé vers +y local, largeur qui s'effile."""
    return (lambda t: (L * (t - 0.12 * t * t), curve * L * t ** 2.1)), (lambda t: (0.135 * L * (1 - t) ** 0.8 + 0.008 * L) * min(1.0, 0.42 + t / 0.2))


def paint_hook(W=96, H=64):
    ss = 4
    ay, ax = np.mgrid[0:H * ss, 0:W * ss]
    a = lerp(-0.02, 1.0, (ax + 0.5) / (W * ss))
    b = lerp(HOOK_BB[1], HOOK_BB[0], (ay + 0.5) / (H * ss))
    center, hw = hook_shape(1.0)
    dd = np.full(a.shape, 9.0, np.float32)
    tt = np.zeros(a.shape, np.float32)
    for t in np.linspace(0, 1, 200):
        cx, cy = center(t)
        d_ = np.hypot(a - cx, b - cy) / hw(t)
        ok = d_ < dd
        dd[ok], tt[ok] = d_[ok], t
    c = np.empty(a.shape + (3,), np.float32)
    c[...] = C_BASE
    c = lerp(c, C_HIGH, (np.clip(1 - dd * 1.6, 0, 1) * 0.72)[..., None])
    c = lerp(c, C_RIM, (np.clip((dd - 0.68) * 3.2, 0, 1) * 0.7)[..., None])
    vein = (dd < 0.2) & (tt > 0.06)
    c = lerp(c, C_AURA, (np.clip(1 - dd * 2.4, 0, 1) * 0.5)[..., None])
    c = lerp(c, C_VEIN, vein[..., None] * 1.0)
    c = lerp(c, C_VCORE, ((dd < 0.09) & (tt > 0.08))[..., None] * 1.0)
    c = lerp(c, np.array((132, 240, 58), np.float32), np.clip((tt - 0.8) / 0.16, 0, 1)[..., None])
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS), np.float32)
    al = np.array(Image.fromarray(((dd < 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    line = np.array(Image.fromarray(((dd < 0.12) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 100
    return rgba(rgb, al), emissive(line, al)


def paint_braise(P=48):
    """Éclat rond et léger : disque au bord à peine irrégulier, cœur vif, liseré sombre. Une seule silhouette."""
    ss = 4
    r = np.random.default_rng(7)
    rays = r.uniform(0.86, 1.0, 14)
    poly = []
    for i, k in enumerate(rays):
        a = i / len(rays) * TAU
        rr = 0.47 * k * P * ss
        poly.append((P * ss / 2 + rr * math.cos(a), P * ss / 2 + rr * math.sin(a)))
    m = Image.new("L", (P * ss, P * ss), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    f = np.array(m.filter(ImageFilter.GaussianBlur(P * 0.5)), np.float32) / 255
    c = np.empty(f.shape + (3,), np.float32)
    c[...] = (26, 70, 30)
    c = lerp(c, np.array((110, 220, 50), np.float32), np.clip((f - 0.34) * 3.0, 0, 1)[..., None])
    c = lerp(c, np.array((206, 255, 118), np.float32), np.clip((f - 0.62) * 5.0, 0, 1)[..., None])
    rgb = np.array(Image.fromarray(c.astype(np.uint8), "RGB").resize((P, P), Image.LANCZOS), np.float32)
    al = np.array(m.resize((P, P), Image.LANCZOS)) > 110
    line = np.array(Image.fromarray((f * 255).astype(np.uint8), "L").resize((P, P), Image.LANCZOS)) > 120
    return rgba(rgb, al), emissive(line, al)


UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def build_atlas():
    items = [(f"shard{i}", *paint_shard(11 + i * 5)) for i in range(3)]
    items += [("hook", *paint_hook()), ("spine", *paint_spine()), ("bone", *paint_bone()), ("braise", *paint_braise())]
    items.sort(key=lambda it: -it[1].shape[0])
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, im, em in items:
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, "atlas plein"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        tex_e[y:y + h, x:x + w] = em
        x += w + 1
        shelf = max(shelf, h)
    assert tex[TEX - 3, TEX - 3, 3] == 0
    assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
    out = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        out.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return out


TEX_B64, TEX_E_B64 = build_atlas()

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx, ordre du mod et du renderer."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "rotation": [round(float(v), 2) for v in rotation]}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def plate(g, name, c, X, Y, w, h, tile, th=0.3):
    """Plaque fine : contour par l'alpha, tranches transparentes. u suit X, le haut de l'image est +Y."""
    X, Y = unit(np.asarray(X, float)), unit(np.asarray(Y, float))
    u0, v0, u1, v1 = UV[tile]
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
         {"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def bar(g, name, p, q, r, tile="spine", u0=0.0, u1=1.0, octo=False, ov=0.04, turn=0.0):
    """Tronçon plein : losange (un cube à 45°) ou octogone (deux cubes). u suit la longueur."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X = unit(q - p)
    ref = V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0)
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    tile_uv = UV[tile]
    ua, ub = lerp(tile_uv[0], tile_uv[2], u0), lerp(tile_uv[0], tile_uv[2], u1)
    lg = [ua, tile_uv[1], ub, tile_uv[3]]
    end = [ua, tile_uv[1], ua + 2, tile_uv[1] + 1]
    faces = {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end}

    def rot(deg):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        return np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])

    cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(rot(45 + turn)), faces)
    if octo:
        cube(g, name + "o", p + (-ov + 0.03, -r * 0.97, -r * 0.97), p + (L + ov - 0.03, r * 0.97, r * 0.97), p, euler(rot(turn)), faces)


# Pièces : orbite (phi, rayon, hauteur, inclinaison du plan), forme, orientation autour de la tangente de vol.
#   nom      phi   r     h     rx   rz    L    image     lacet tangage emit
SHARDS = [
    ("e1",   20,  10.9, 19.8,   6,  -5,  5.0, "shard0",  10,   8,  True),
    ("e2",   85,  11.2, 16.6,  -4,   5,  3.6, "shard1",  -7,  14,  True),
    ("e3",  140,  10.9, 18.3,   7,   4,  4.4, "shard2",  11,  -7,  False),
    ("e4",  200,  11.2, 16.0,  -5,  -4,  5.4, "shard0",  -6, -12,  True),
    ("e5",  265,  11.0, 20.0,   4,   7,  3.4, "shard2",  10,  12,  True),
    ("e6",  320,  10.8, 17.3,  -6,  -7,  4.2, "shard1",  -9,  -9,  True),
]
#   griffes : sens d'orbite inverse, en dehors et au-dessus / au-dessous des éclats : elles les croisent sans les toucher (mesuré)
CLAWS = [
    ("g1",   60,  12.2, 11.8,   3,  -3,  5.6),
    ("g2",  235,  12.0, 23.6,  -5,   5,  5.6),
]

PIECES = []    # (nom, phi, sens de rotation)
EMITS = []
root_children = []


def chain(name, phi, r, h, rx, rz):
    """orb > spin > rad > burst. Tout est placé à sa vraie position : les clés de spin partent de 0."""
    orb = group(f"orb_{name}", (0, h, 0), rotation=(rx, 0, rz))
    spin = group(f"spin_{name}", (0, h, 0), parent=orb)
    a = math.radians(phi)
    centre = V(r * math.cos(a), h, r * math.sin(a))
    rad = group(f"rad_{name}", centre, parent=spin)
    burst = group(f"burst_{name}", centre, parent=rad)
    root_children.append(orb)
    return burst, centre, a


for nm, phi, r, h, rx, rz, L, tile, yaw, pitch, has_emit in SHARDS:
    g, c, a = chain(nm, phi, r, h, rx, rz)
    PIECES.append((nm, phi, +1))
    out = V(math.cos(a), 0, math.sin(a))
    tang = V(math.sin(a), 0, -math.cos(a))          # sens du déplacement sous Y positif : la pointe mène
    up = V(0, 1, 0)
    X = unit(tang * math.cos(math.radians(yaw)) + out * math.sin(math.radians(yaw)) + up * math.sin(math.radians(pitch)))
    Y0 = unit(up - (up @ X) * X)
    Z0 = np.cross(X, Y0)
    Y1 = unit(Y0 * math.cos(math.radians(35)) + Z0 * math.sin(math.radians(35)))     # croix qui ne se présente jamais d'équerre à la caméra
    Y2 = np.cross(X, Y1)
    w = 0.27 * L + 0.1
    plate(g, f"{nm}_pa", c, X, Y1, L, w, tile)
    plate(g, f"{nm}_pb", c + X * 0.02, X, Y2, L * 0.97, w * 0.94, tile)
    base = c - X * (L * 0.43)
    ra = 0.1 + 0.022 * L
    bar(g, f"{nm}_ar", base, base + X * (L * 0.42), ra, u0=0.0, u1=0.5)
    bar(g, f"{nm}_at", base + X * (L * 0.42), base + X * (L * 0.74), ra * 0.66, u0=0.5, u1=1.0, turn=11)
    if has_emit:
        EMITS.append(group("emit_braise" + (str(len(EMITS) + 1) if EMITS else ""), c + X * (L * 0.48), parent=g))

for nm, phi, r, h, rx, rz, L in CLAWS:
    g, c, a = chain(nm, phi, r, h, rx, rz)
    PIECES.append((nm, phi, -1))
    out = V(math.cos(a), 0, math.sin(a))
    tang = V(-math.sin(a), 0, math.cos(a))          # sens inverse
    X = unit(tang + out * 0.12 + V(0, 0.1, 0))
    Y = unit(out * 0.75 + V(0, 0.65 if h > 18 else -0.65, 0))      # chaque griffe se recourbe à l'opposé des éclats
    Y = unit(Y - (Y @ X) * X)
    n = np.cross(X, Y)
    p = c - X * (L * 0.48)
    lo, hi = HOOK_BB
    plate(g, f"{nm}_peau", p + X * (0.49 * L) + Y * ((lo + hi) / 2 * L) + n * 0.05, X, Y, 1.02 * L, (hi - lo) * L, "hook")
    center, hw = hook_shape(L)
    for j in range(2):
        t0, t1 = j / 2 * 0.46, (j + 1) / 2 * 0.46     # l'âme s'arrête avant la courbure : sinon sa corde sort de la griffe
        A, B = center(t0), center(t1)
        bar(g, f"{nm}_c{j}", p + X * A[0] + Y * A[1], p + X * B[0] + Y * B[1], max(0.15, hw((t0 + t1) / 2) * 0.3), turn=j * 9)
    bar(g, f"{nm}_col", p - X * 0.12, p + X * 0.55, 0.36, "bone", 0.1, 0.8, octo=True)

# Particule : recette validée en jeu (une plaque, face up seule, au-dessus du pivot).
PG = group("particle_braise", (0, 0, 0))
pw = 2.4
u0_, v0_, u1_, v1_ = UV["braise"]
cube(PG, "braise", [-pw / 2, 0.3, -pw / 2], [pw / 2, 0.6, pw / 2], [0, 0, 0], (0, 0, 0), {"up": [u0_, v0_, u1_, v1_]})


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone_node(n) for n in root_children]}, bone_node(PG)]


# ------------------------------------------------------------------ animations
def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 3)), "y": str(round(v[1] + 0.0, 3)), "z": str(round(v[2] + 0.0, 3))}],
            "time": round(t, 3), "interpolation": "linear"}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def clip(name, L, tracks, n=None, loop="loop"):
    """tracks : groupe -> {canal: fonction t -> (x, y, z)} ; une piste fournie en liste de temps garde ces temps."""
    n = n or max(8, int(round(L * 4)))
    times = [i * L / n for i in range(n + 1)]
    A = {}
    for g, chans in tracks.items():
        keys = []
        for ch, f in chans.items():
            ts = f[1] if isinstance(f, tuple) else times
            fn = f[0] if isinstance(f, tuple) else f
            keys += [kf(ch, t, fn(t)) for t in ts]
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": keys}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": L, "snapping": 24, "selected": name == "idle", "animators": A}


# Durées multiples de 4 s ; un tour par boucle dans tous les états. Le rayon vit dans rad_<p> : le plan et le centre ne changent pas d'un état à l'autre.
#          nom     L   Δrayon flott balanc périodes (diviseurs entiers de L)
STATES = [("idle",  24,  0.0,  0.70,  6.0, (3, 4, 5)),
          ("walk",  16, -0.5,  0.55,  6.0, (3, 4, 5)),
          ("run",    8, -1.2,  0.30,  4.0, (3, 4, 5)),
          ("sneak", 32, -1.1,  0.30,  3.0, (5, 6, 7)),
          ("fly",   12,  0.0,  0.90,  8.0, (2, 3, 4))]


def state_anim(name, L, dr, amp, rock, ks):
    tr = {}
    for i, (nm, phi, sens) in enumerate(PIECES):
        a = math.radians(phi)
        out = (math.cos(a), math.sin(a))
        k = ks[i % 3]
        ph = i * 1.9

        def pos(t, k=k, ph=ph, out=out):
            s = TAU * k * t / L + ph
            rr = dr + 0.2 * math.sin(TAU * ks[0] * t / L + ph * 2)
            return (out[0] * rr, amp * math.sin(s), out[1] * rr)

        def rot(t, k=k, ph=ph):
            s = TAU * k * t / L + ph
            return (rock * math.sin(s + 0.7), 0, rock * 0.8 * math.cos(s))

        tr[f"spin_{nm}"] = {"rotation": ((lambda t, sens=sens: (0, sens * 360 * t / L, 0)), [0.0, L])}
        tr[f"rad_{nm}"] = {"rotation": rot, "position": pos}
    return clip(name, L, tr, n=int(L * 2))


def hurt_anim():
    """Éclats projetés vers l'extérieur puis rappelés. Seul animateur de burst_<p> : rien à perdre de l'état en cours."""
    L = 0.8
    tr = {}
    for i, (nm, phi, _s) in enumerate(PIECES):
        a = math.radians(phi)
        out = (math.cos(a), math.sin(a))
        push = 3.4 + 0.4 * (i % 3)

        def curve(t, i=i):
            return bump(t, 0.0, 0.08 + 0.01 * i, 0.2, 0.76)

        def pos(t, out=out, push=push, i=i, curve=curve):
            v = curve(t)
            return (out[0] * push * v, (0.7 if i % 2 else -0.7) * v, out[1] * push * v)

        def rot(t, i=i, curve=curve):
            v = curve(t)
            return ((-1) ** i * 38 * v, 0, (-1) ** (i // 2) * 26 * v)

        tr[f"burst_{nm}"] = {"position": pos, "rotation": rot}
    return clip("hurt", L, tr, n=16, loop="once")


def particle_anims():
    PF, PR = 3.0, 6.0
    fall = clip("particle_braise_fall", PF, {PG: {"rotation": lambda t: (20 * math.sin(TAU * t / PF), 360 * t / PF, 14 * math.cos(2 * TAU * t / PF))}}, n=24)
    rest = clip("particle_braise_rest", PR, {PG: {"rotation": lambda t: (0, 0, 1.2 * math.sin(TAU * t / PR))}}, n=12)
    return [fall, rest]


ANIMS = [state_anim(*s) for s in STATES] + [hurt_anim()] + particle_anims()

# ------------------------------------------------------------------ écriture
assert 20 <= len(elements) <= 80, f"budget : {len(elements)} cubes"
assert 4 <= len(EMITS) <= 6
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": TEX_B64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": TEX_E_B64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;", len(EMITS), "emit_")
