"""Diadème céleste : fin bandeau d'or doux, pierre ivoire, ailettes de plumes en éventail aux tempes. Design original, assorti à aurelion_wings.
Écrit diademe_celeste.png, diademe_celeste_e.png et .build/diademe_celeste_brut.bbmodel à côté de ce script.

Tout est dans le groupe de premier niveau head. Plumes : peau ronde découpée par alpha autour d'une âme pleine plus étroite.
Le bandeau passe à 4,65 px de l'axe, au-dessus de la seconde couche du skin (4,5 px). Les ailettes partent des tempes (z de -2 à +1)
et remontent vers l'arrière : rien n'avance devant le front, hormis le bandeau et la pierre.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "diademe_celeste"
AVEC_E = False      # True : embarque le calque _e en seconde texture. False tant que le bug du mod n'est pas corrigé.
TEX = 512
SS = 4
TAU = 2 * math.pi


# ------------------------------------------------------------------ textures
def lerp(a, b, k):
    return a + (b - a) * k


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


GOLD_D, GOLD_M, GOLD_L = (np.array(c, np.float32) for c in ((176, 138, 78), (232, 198, 122), (252, 232, 176)))
PAL = {
    # racine, milieu, bout, liseré, ombre, couleur de pointe : mêmes valeurs que aurelion_wings
    "p": ((222, 216, 202), (252, 250, 243), (254, 251, 240), (176, 150, 104), (150, 138, 116), (238, 200, 116)),
    "l": ((240, 212, 148), (250, 232, 180), (254, 242, 204), (186, 148, 84), (176, 146, 96), (255, 244, 208)),
}
SHAPE = {
    # demi-largeur intérieure, extérieure, début de l'arrondi, courbure, début de pointe colorée, longueur d'ombre
    "p": (0.42, 0.33, 0.62, 0.12, 0.72, 0.26),
    "l": (0.46, 0.42, 0.44, 0.03, 0.86, 0.16),
}


def finish(col, alpha, W, H):
    """Réduit la peinture sur-échantillonnée : alpha 0/255, couleur moyenne hors silhouette (ni frange, ni PNG lourd)."""
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    solid = np.array(Image.fromarray((alpha * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = rgb
    if solid.any():
        arr[~solid, :3] = rgb[solid].mean(axis=0).astype(np.uint8)
    arr[..., 3] = solid * 255
    return arr


def paint(W, H, kind, seed):
    """Plume : base en haut, pointe en bas, côté extérieur à droite. Renvoie la texture et le calque lumineux."""
    rng = np.random.default_rng(seed)
    root, mid, tip, rim, shadow, gold = (np.array(c, np.float32) for c in PAL[kind])
    hi, ho, te, curve, g0, shl = SHAPE[kind]
    te += rng.uniform(-0.03, 0.03)
    jitter = rng.uniform(0.97, 1.02)
    w, h = W * SS, H * SS
    x, y = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    t = y
    cx = 0.5 + curve * (t * t - 0.3)
    env = (0.28 + 0.72 * smooth(t / 0.20)) * np.where(t > te, np.sqrt(np.clip(1 - ((t - te) / (1 - te)) ** 2, 0, 1)), 1.0)
    d = x - cx
    lim = np.where(d >= 0, ho * env, hi * env)
    r = np.abs(d) / np.maximum(lim, 1e-4)
    alpha = r < 1
    col = lerp(lerp(root, mid, smooth(t / 0.5)[..., None]), tip, smooth((t - 0.5) / 0.5)[..., None]) * jitter
    col = col * (1.04 - 0.17 * (r ** 2))[..., None]
    col = col * (1 + 0.035 * np.sin((t * H - np.abs(d) * W * 1.4) * TAU / 6.0) * (r > 0.1))[..., None]
    gk = smooth((t - g0) / max(1e-3, 1 - g0))[..., None]
    col = lerp(col, gold, gk * 0.85)
    col = lerp(col, shadow, (np.clip(1 - t / shl, 0, 1) ** 1.25)[..., None] * 0.72)
    col = col * (1 - 0.20 * (np.clip((r - 0.45) / 0.55, 0, 1) * (d < 0))[..., None])
    dist = (1 - r) * lim * W
    col = lerp(col, rim, (np.clip(1 - dist / 3.5, 0, 1) * (t > 0.12))[..., None] * 0.72)
    ec = np.empty(col.shape, np.float32)
    ec[...] = (42, 36, 22) if kind == "l" else (40, 39, 35)
    ec = lerp(ec, np.array((128, 104, 58), np.float32), gk)
    ec = lerp(ec, np.array((118, 106, 78), np.float32), (np.clip(1 - dist / 2.2, 0, 1) * (t > 0.12))[..., None])
    if kind == "p":
        ra = np.clip(1 - np.abs(d) * W / 1.5, 0, 1)[..., None] * (t < 0.93)[..., None]
        col = lerp(col, np.array((255, 248, 226), np.float32), ra * 0.75)
        ec = lerp(ec, np.array((170, 162, 136), np.float32), ra)
    out = finish(col, alpha, W, H)
    eo = np.array(Image.fromarray(np.clip(ec, 0, 200).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    return out, np.dstack([eo, out[..., 3]]).astype(np.uint8)


def edge_strip(kind, W=6, H=32):
    """Bande opaque de l'âme : suit le dégradé de la plume, assombrie pour dessiner le bord."""
    root, mid, tip, rim, shadow, gold = (np.array(c, np.float32) for c in PAL[kind])
    g0 = SHAPE[kind][4]
    a = np.zeros((H, W, 4), np.float32)
    for yy in range(H):
        t = (yy + 0.5) / H
        c = lerp(root, mid, min(1, t * 2)) if t < 0.5 else lerp(mid, tip, (t - 0.5) * 2)
        c = lerp(c, gold, float(smooth((t - g0) / max(1e-3, 1 - g0))) * 0.85)
        a[yy, :, :3] = lerp(c, rim, 0.38)
    a[..., 3] = 255
    return a.astype(np.uint8)


def band_tile(W=32, H=16):
    """Or doux en volume : filet clair au centre, bords plus sombres."""
    a = np.zeros((H, W, 4), np.float32)
    for yy in range(H):
        q = abs((yy + 0.5) / H - 0.5) * 2
        a[yy, :, :3] = lerp(GOLD_L, GOLD_D, q ** 1.3)
    a[..., 3] = 255
    return a.astype(np.uint8)


def front_band(W=164, H=68):
    """Plaque du front : bandeau qui descend en arc vers la pierre, deux paires de feuilles fines. Coordonnées en px du modèle."""
    w, h = W * SS, H * SS
    gx, gy = np.meshgrid((np.arange(w) + 0.5) / w * FW - FW / 2, FY1 - (np.arange(h) + 0.5) / h * (FY1 - FY0))
    q = np.abs(gx) / (FW / 2)
    cy = BAND_Y - DIP * (1 - q ** 1.6)
    ht = 0.35 + 0.08 * (1 - q)
    d = (gy - cy) / ht                     # -1 bord bas, +1 bord haut
    band = np.abs(d) < 1
    col = np.empty(gx.shape + (3,), np.float32)
    col[...] = GOLD_M
    col = lerp(col, GOLD_L, np.clip(1 - np.abs(d) * 1.7, 0, 1)[..., None])
    col = lerp(col, GOLD_D, np.clip(np.abs(d) * 1.8 - 0.95, 0, 1)[..., None])
    leaf = np.zeros(gx.shape, bool)
    leaf_d = np.ones(gx.shape, np.float32) * 9
    for sgn in (-1, 1):
        for x0, ang, L_, W_ in ((1.75, 34, 1.5, 0.42), (2.85, 46, 1.2, 0.34)):
            y0 = BAND_Y - DIP * (1 - (x0 / (FW / 2)) ** 1.6) + 0.1
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            a = (gx - sgn * x0) * sgn * ca + (gy - y0) * sa
            b = -(gx - sgn * x0) * sgn * sa + (gy - y0) * ca
            k = np.clip(a / L_, 0, 1)
            lw = W_ * np.sin(math.pi * k) ** 0.8 * (a > 0) * (a < L_)
            dd = np.abs(b) / np.maximum(lw, 1e-3)
            inside = (dd < 1) & (a > 0) & (a < L_)
            leaf |= inside
            leaf_d = np.where(inside, np.minimum(leaf_d, dd), leaf_d)
    m = leaf & ~band
    lc = lerp(GOLD_L, GOLD_D, smooth(leaf_d * 1.2 - 0.25)[..., None])
    col = np.where(m[..., None], lc, col)
    ec = np.zeros(gx.shape + (3,), np.float32)
    ec[...] = (34, 28, 16)
    ec = lerp(ec, np.array((128, 104, 58), np.float32), np.clip(1 - np.abs(d) * 2.4, 0, 1)[..., None] * band[..., None])
    out = finish(col, band | leaf, W, H)
    eo = np.array(Image.fromarray(ec.astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    return out, np.dstack([eo, out[..., 3]]).astype(np.uint8)


def rosette(W=48, lobes=12):
    """Sertissure ronde à lobes, plate, or : disque découpé par alpha."""
    w = W * SS
    gx, gy = np.meshgrid((np.arange(w) + 0.5) / w * 2 - 1, (np.arange(w) + 0.5) / w * 2 - 1)
    r, th = np.hypot(gx, gy), np.arctan2(gy, gx)
    rim = 0.93 + 0.05 * np.cos(th * lobes)
    q = r / rim
    col = np.empty(gx.shape + (3,), np.float32)
    col[...] = GOLD_M
    col = lerp(col, GOLD_D, smooth((q - 0.72) / 0.28)[..., None])
    col = lerp(col, GOLD_L, np.clip(1 - np.abs(q - 0.52) / 0.12, 0, 1)[..., None] * 0.9)
    col = lerp(col, GOLD_D, (q < 0.40)[..., None] * 0.55)
    ec = np.empty(col.shape, np.float32)
    ec[...] = (34, 28, 16)
    ec = lerp(ec, np.array((128, 104, 58), np.float32), np.clip(1 - np.abs(q - 0.52) / 0.12, 0, 1)[..., None])
    out = finish(col, q < 1, W, W)
    eo = np.array(Image.fromarray(ec.astype(np.uint8), "RGB").resize((W, W), Image.LANCZOS))
    return out, np.dstack([eo, out[..., 3]]).astype(np.uint8)


def gem_tile(W, H, top, bot, reflet=None):
    """Pierre ivoire : dégradé doux de la face, reflet or en bas."""
    a = np.zeros((H, W, 4), np.float32)
    top, bot = np.array(top, np.float32), np.array(bot, np.float32)
    for yy in range(H):
        a[yy, :, :3] = lerp(top, bot, (yy + 0.5) / H)
    if reflet:
        a[H // 5:H // 5 + 4, W // 5:W // 5 + 6, :3] = reflet
    a[..., 3] = 255
    return a.astype(np.uint8)


def gem_disc(W=36):
    """Cabochon ivoire : peau ronde, nacre claire au centre, reflet haut, bord or doux."""
    w = W * SS
    gx, gy = np.meshgrid((np.arange(w) + 0.5) / w * 2 - 1, (np.arange(w) + 0.5) / w * 2 - 1)
    r = np.hypot(gx, gy)
    col = np.empty(gx.shape + (3,), np.float32)
    col[...] = (255, 252, 240)
    col = lerp(col, np.array((226, 206, 160), np.float32), smooth((r - 0.45) / 0.5)[..., None])
    col = lerp(col, np.array((255, 255, 255), np.float32), (np.hypot(gx + 0.25, gy + 0.32) < 0.2)[..., None])
    ec = np.empty(col.shape, np.float32)
    ec[...] = (70, 62, 42)
    ec = lerp(ec, np.array((180, 168, 132), np.float32), np.clip(1 - r / 0.6, 0, 1)[..., None])
    out = finish(col, r < 0.98, W, W)
    eo = np.array(Image.fromarray(ec.astype(np.uint8), "RGB").resize((W, W), Image.LANCZOS))
    return out, np.dstack([eo, out[..., 3]]).astype(np.uint8)


def particle_plume(PLW=40, PLH=160):
    """Plume-particule, recette validée : une seule silhouette, courbure et contour peints dans l'image."""
    y_, x_ = np.mgrid[0:PLH * SS, 0:PLW * SS]
    t = (y_ + 0.5) / (PLH * SS)
    d = (x_ + 0.5) / (PLW * SS) - 0.5
    c = 0.13 * (np.sin(t * math.pi) - 0.5)
    v = np.clip((t - 0.10) / 0.90, 0, 1)
    env = 0.34 * np.sin(math.pi * v ** 0.85) ** 0.42
    dd = np.abs(d - c)
    a = dd < np.maximum(env, 0.018 * (t < 0.97))
    col = np.empty(a.shape + (3,), np.float32)
    col[...] = (248, 245, 234)
    col = col * (1.0 - 0.14 * (dd / np.maximum(env, 0.02))[..., None] ** 2)
    col = col * (1 + 0.03 * np.sin((t * PLH - dd * PLW * 1.4) * TAU / 7))[..., None]
    col = lerp(col, np.array((236, 202, 124), np.float32), smooth((t - 0.78) / 0.22)[..., None] * 0.8)
    col = lerp(col, np.array((205, 192, 165), np.float32), (dd < 0.02)[..., None] * 0.8)
    return finish(col, a, PLW, PLH)


# Bandeau, en px du modèle : plaque de front de x = ±FW/2, y de FY0 à FY1
FW, FY0, FY1 = 8.2, 28.9, 32.3
BAND_Y, DIP = 30.7, 0.85       # hauteur du bandeau aux tempes ; descente au centre, vers la pierre
GEM_Y = BAND_Y - DIP

UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_cur = [0, 0, 0]


def place(name, im, em=None):
    h, w = im.shape[:2]
    if _cur[0] + w > TEX:
        _cur[:] = [0, _cur[1] + _cur[2] + 2, 0]
    x, y = _cur[0], _cur[1]
    assert y + h <= TEX - 6, "atlas plein"
    tex[y:y + h, x:x + w] = im
    if em is not None:
        tex_e[y:y + h, x:x + w] = em
    UV[name] = (x, y, x + w, y + h)
    _cur[0] += w + 2
    _cur[2] = max(_cur[2], h)


seed = 1
for i in range(4):
    place(f"p{i}", *paint(44, 150, "p", seed))
    seed += 1
for i in range(3):
    place(f"l{i}", *paint(40, 48, "l", seed))
    seed += 1
place("front", *front_band())
place("rosace", *rosette())
place("disc", *gem_disc())
place("plume", particle_plume())
for kind in PAL:
    e = edge_strip(kind)
    em = np.zeros(e.shape, np.uint8)
    em[...] = (30, 29, 26, 255)
    place(f"edge_{kind}", e, em)
b_ = band_tile()
be = np.zeros(b_.shape, np.uint8)
be[...] = (34, 28, 16, 255)
be[6:10, :, :3] = (128, 104, 58)
place("band", b_, be)
for name, top, bot, rf in (("gem_f", (255, 253, 244), (240, 226, 192), (255, 255, 255)), ("gem_s", (238, 228, 204), (206, 186, 142), None)):
    g_ = gem_tile(24, 24, top, bot, rf)
    ge = np.zeros(g_.shape, np.uint8)
    ge[...] = (150, 140, 108, 255) if name == "gem_f" else (70, 62, 42, 255)
    place(name, g_, ge)

CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC
assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
assert tex_e[..., :3].max() <= 200, "calque trop vif"
_b64 = []
for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(fn, optimize=True)
    _buf = io.BytesIO()
    im_.save(_buf, "PNG", optimize=True)
    _b64.append("data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode())
tex_b64, tex_e_b64 = _b64

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


def cube(g, name, c, size, X, Y, faces):
    """Cube centré en c, axes X, Y (orthonormés), Z = X × Y."""
    c, size = np.asarray(c, float), np.asarray(size, float)
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    rot = euler(R_)
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in c - size / 2], "to": [round(float(v), 3) for v in c + size / 2],
         "origin": [round(float(v), 3) for v in c], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def all_faces(tile):
    return {f: list(UV[tile]) for f in ("north", "south", "east", "west", "up", "down")}


SKIN = 0.3       # épaisseur d'une peau
EMBED = 0.12     # l'âme entre d'autant dans la peau : ni vide, ni face coplanaire


def feather(g, name, p, d, vane, L, w, tile, t0=0.6, t1=0.32, ncore=2, bow=0.25, skins=(1, -1)):
    """Plume hybride partant de p vers d ; vane = côté droit de l'image, Z = X × Y. t0, t1 : épaisseur totale à la base, à la pointe.
    Les deux peaux se rejoignent vers la pointe (t1 proche de SKIN) : profil en lentille, pas de bout fourchu sur une plume de cette taille.
    bow : la pointe s'écarte du plan vers -Z. skins : peaux à poser, +1 côté +Z, -1 côté -Z."""
    p, d = np.asarray(p, float), unit(np.asarray(d, float))
    X0 = unit(vane - (vane @ d) * d)
    Y0 = -d
    Z0 = np.cross(X0, Y0)
    u0, v0, u1, v1 = UV[tile]
    tip = p + d * L
    for sg in skins:
        a = p + Z0 * (sg * (t0 / 2 - SKIN / 2))
        b = tip + Z0 * (-bow + sg * (t1 / 2 - SKIN / 2))
        ax = unit(b - a)
        X = unit(X0 - (X0 @ ax) * ax)
        faces = {"south": [u0, v0, u1, v1] if sg > 0 else CLEAR, "north": [u1, v0, u0, v1] if sg < 0 else CLEAR,
                 "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
        cube(g, f"{name}.{'d' if sg > 0 else 'v'}", (a + b) / 2, (w, float(np.linalg.norm(b - a)), SKIN), X, -ax, faces)
    kind = tile[0]
    e0, e1, e2, e3 = UV[f"edge_{kind}"]
    t_a, t_b = 0.16, 0.92
    for j in range(ncore):
        f0, f1 = lerp(t_a, t_b, j / ncore), lerp(t_a, t_b, (j + 1) / ncore)
        c0, c1 = p + d * (f0 * L) + Z0 * (-bow * f0), p + d * (f1 * L) + Z0 * (-bow * f1)
        ax = unit(c1 - c0)
        X = unit(X0 - (X0 @ ax) * ax)
        th = max(0.3, lerp(t0, t1, f1) - 2 * SKIN + 2 * EMBED)
        wc = w * 0.38 * (1 - 0.5 * (j + 0.5) / ncore)
        ov = 0.12 if j else 0.0
        ea, eb = lerp(e1, e3, f0), lerp(e1, e3, f1)
        fc = [e0, ea, e2, eb]
        cube(g, f"{name}.c{j}", (c0 + c1) / 2 - ax * ov / 2, (wc, float(np.linalg.norm(c1 - c0)) + ov, th), X, -ax,
             {"south": fc, "north": fc, "east": fc, "west": fc, "up": [e0, ea, e2, min(e3, ea + 1)], "down": [e0, max(e1, eb - 1), e2, eb]})
    return tip


# Bandeau : front, biseaux, tempes, nuque. Les biseaux évitent le coin à 90° de la tête.
BZ, BTH, BH = 4.8, 0.3, 0.62
BAND = group("bandeau", [0, BAND_Y, 0])
fu0, fv0, fu1, fv1 = UV["front"]
fy = (FY0 + FY1) / 2
cube(BAND, "front", V(0, fy, -BZ), (FW, FY1 - FY0, BTH), V(1, 0, 0), V(0, 1, 0),
     {"north": [fu1, fv0, fu0, fv1], "south": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
# âme du front : deux lames dans la plaque, elles donnent un dessus au bandeau vu de haut
for sgn, tag in ((-1, "l"), (1, "r")):
    pa, pb = V(sgn * 0.3, GEM_Y + 0.05, -BZ), V(sgn * (FW / 2 - 0.05), BAND_Y, -BZ)
    ax_ = unit(pb - pa)
    cube(BAND, f"ame_{tag}", (pa + pb) / 2, (float(np.linalg.norm(pb - pa)), 0.26, 0.22), ax_, V(-ax_[1], ax_[0], 0), all_faces("band"))
hw = FW / 2
for sgn, tag in ((-1, "l"), (1, "r")):
    # tempe
    cube(BAND, f"tempe_{tag}", V(sgn * BZ, BAND_Y, 0), (BTH, BH, 2 * hw + 0.1), V(1, 0, 0), V(0, 1, 0), all_faces("band"))
    # biseaux avant et arrière
    for sz, zt in ((-1, "av"), (1, "ar")):
        c_ = V(sgn * (hw + BZ) / 2, BAND_Y + (0.015 if sz < 0 else -0.015), sz * (hw + BZ) / 2)
        ln = (BZ - hw) * math.sqrt(2) + 0.24
        X_ = unit(V(sgn, 0, -sz))
        cube(BAND, f"biseau_{zt}_{tag}", c_, (ln, BH - 0.04, BTH - 0.03), X_, V(0, 1, 0), all_faces("band"))
cube(BAND, "nuque", V(0, BAND_Y, BZ), (2 * hw + 0.1, BH, BTH), V(1, 0, 0), V(0, 1, 0), all_faces("band"))

# Pierre : sertissure à lobes, cabochon : peau ronde autour d'une âme octogonale. Elle n'avance que de 0,9 px devant le bandeau.
STONE = group("pierre", [0, GEM_Y, -BZ])
ru0, rv0, ru1, rv1 = UV["rosace"]
RS = 2.7
cube(STONE, "serti", V(0, GEM_Y, -5.13), (RS, RS, 0.3), V(1, 0, 0), V(0, 1, 0),
     {"north": [ru1, rv0, ru0, rv1], "south": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
gem_f = {"north": list(UV["gem_f"]), "south": list(UV["gem_s"]), "east": list(UV["gem_s"]), "west": list(UV["gem_s"]), "up": list(UV["gem_f"]), "down": list(UV["gem_s"])}
R45 = (V(math.sqrt(.5), math.sqrt(.5), 0), V(-math.sqrt(.5), math.sqrt(.5), 0))
cube(STONE, "gem0", V(0, GEM_Y, -5.39), (1.12, 1.12, 0.22), V(1, 0, 0), V(0, 1, 0), gem_f)
cube(STONE, "gem0b", V(0, GEM_Y, -5.385), (1.09, 1.09, 0.19), *R45, gem_f)
du0, dv0, du1, dv1 = UV["disc"]
cube(STONE, "cabochon", V(0, GEM_Y, -5.58), (1.75, 1.75, 0.3), V(1, 0, 0), V(0, 1, 0),
     {"north": [du1, dv0, du0, dv1], "south": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})

# Ailettes : éventail qui part de la tempe, de la verticale vers l'arrière. Écartement vers l'extérieur et roulis : lisible de face comme de profil.
NF = 6
FAN_A = [-4 + 68 * i / (NF - 1) for i in range(NF)]     # 0° = vertical, 90° = vers l'arrière
FAN_L = [6.2, 7.6, 8.4, 8.2, 7.2, 5.8]
FAN_W = [2.2, 2.45, 2.55, 2.5, 2.3, 2.05]
SPLAY = 0.40         # tangente de l'écartement vers l'extérieur
ROLL = [0.8, 0.68, 0.56, 0.44, 0.32, 0.2]   # le bord avant passe à l'extérieur ; roulis varié : jamais toutes par la tranche en même temps
ANCH_Z, ANCH_Y = -0.7, 31.0
EMITS = []
FANS = []


def build(s):
    tag = "l" if s < 0 else "r"
    fan = group(f"fan_{tag}", [s * BZ, ANCH_Y, ANCH_Z])
    FANS.append(fan)
    for i in range(NF):
        a = math.radians(FAN_A[i])
        d = unit(V(s * SPLAY, math.cos(a), math.sin(a)))
        back = V(0, -math.sin(a), math.cos(a))
        vane = back - V(s * ROLL[i], 0, 0)
        p = V(s * (5.0 + 0.05 * i), ANCH_Y + 0.15 - 0.10 * i, ANCH_Z - 1.1 + 0.46 * i)
        g = group(f"d{i}_{tag}", p, parent=fan)
        tip = feather(g, f"d{i}{tag}", p, d, vane, FAN_L[i], FAN_W[i], f"p{(i + (0 if s < 0 else 2)) % 4}", ncore=3 if FAN_L[i] > 8 else 2, bow=0.3 * (i + 1) / NF)
        if i == 2:
            EMITS.append(group("emit_plume" + ("" if s < 0 else "2"), tip, parent=g))
    # couvertures d'or : petites écailles qui couvrent la naissance de l'éventail
    for i, (ang, L_, w_, dz) in enumerate(((12, 2.8, 1.75, -0.8), (40, 3.0, 1.85, 0.0), (66, 2.7, 1.65, 0.8))):
        a = math.radians(ang)
        d = unit(V(s * (SPLAY + 0.22), math.cos(a), math.sin(a)))
        back = V(0, -math.sin(a), math.cos(a))
        p = V(s * (5.28 + 0.03 * i), ANCH_Y - 0.25, ANCH_Z + dz)
        feather(fan, f"cv{i}{tag}", p, d, back - V(s * 0.25, 0, 0), L_, w_, f"l{i}", t0=0.5, t1=0.32, ncore=1, bow=0.05)
    # agrafe de tempe : petite rosace sur le bandeau, sous les couvertures
    Y_ = V(0, 1, 0)
    X_ = V(0, 0, -s)      # Z = X × Y = (s, 0, 0) : la face south regarde vers l'extérieur
    cl = V(s * 5.11, BAND_Y, ANCH_Z)
    cube(fan, f"agrafe_{tag}", cl, (2.0, 2.0, 0.3), X_, Y_, {"south": list(UV["rosace"]), "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
    cube(fan, f"bouton_{tag}", V(s * 5.40, BAND_Y, ANCH_Z), (0.72, 0.72, 0.3), X_, Y_, all_faces("gem_f"))


build(-1)
build(1)


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


# Particule (guide, section 5 ter) : une seule plaque, courbure peinte, face up seule, à 0,3 px au-dessus du pivot.
PL = group("particle_plume", [0, 0, 0])
PW, PLEN, PTH, PY = 1.7, 5.6, 0.3, 0.3
pu0, pv0, pu1, pv1 = UV["plume"]
cube(PL, "plume", V(0, PY + PTH / 2, 0), (PW, PTH, PLEN), V(1, 0, 0), V(0, 1, 0), {"up": [pu0, pv0, pu1, pv1]})

outliner = [{"name": "head", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone(BAND), bone(STONE)] + [bone(f) for f in FANS]}, bone(PL)]


# ------------------------------------------------------------------ animations
# Repères du guide, section 3 : +X = le haut part vers l'arrière ; +Z = le côté droit (+X) monte, donc une plume dressée part vers la gauche.
# Pour une ailette de côté s (-1 gauche, +1 droite) : « s'ouvrir vers l'extérieur » = Z de signe -s.
def kf(t, x, y, z):
    return {"channel": "rotation", "data_points": [{"x": str(round(x + 0.0, 2)), "y": str(round(y + 0.0, 2)), "z": str(round(z + 0.0, 2))}],
            "time": round(t, 3), "interpolation": "linear"}


def S(T, amp, ph=0.0, off=0.0):
    return lambda t: off + amp * math.sin(TAU * t / T + math.radians(ph))


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


WEIGHT = [(i / (NF - 1) - 0.35) for i in range(NF)]     # poids d'écartement de l'éventail : l'avant reste presque fixe, l'arrière s'ouvre


def anim(name, length, back, open_, spread, n_kf=None, loop="loop", lag=0.05):
    """back : fan bascule vers l'arrière ; open_ : s'ouvre vers l'extérieur ; spread : éventail, > 0 ouvert. Léger retard en cascade."""
    n = n_kf or max(8, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]
    A = {}
    per = (lambda t: t % length) if loop == "loop" else (lambda t: max(0.0, t))
    for s, tag in ((-1, "l"), (1, "r")):
        A[groups[f"fan_{tag}"]["uuid"]] = {"name": f"fan_{tag}", "type": "bone", "keyframes": [kf(t, back(t), 0, -s * open_(t)) for t in times]}
        for i in range(NF):
            dl = lag * length * i / (NF - 1)
            g = f"d{i}_{tag}"
            A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(t, WEIGHT[i] * spread(per(t - dl)), 0, 0) for t in times]}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


# idle 8 s : respiration (4 s) et étirement ample de 4,6 à 7,2 s
st = lambda t: bump(t, 4.6, 5.4, 6.0, 7.2)
idle = anim("idle", 8.0, S(4, 1.0, 0, 1), lambda t: S(4, 1.0)(t) + 4 * st(t), lambda t: S(4, 1.5)(t) + 9 * st(t), n_kf=48)
# walk 1,6 s : légèrement ramené en arrière, balancement au pas
walk = anim("walk", 1.6, S(1.6, 1.8, 0, 5), S(1.6, 1.4), S(1.6, 2.0, 40, -1))
# run 1,0 s : couché en arrière, serré
run = anim("run", 1.0, S(1.0, 2.0, 0, 20), S(1.0, 1.2, 0, -2), S(1.0, 2.0, 40, -7))
# sneak 3 s : refermé, plaqué vers la tête
sneak = anim("sneak", 3.0, S(3, 0.8, 0, 8), S(3, 0.6, 0, -7), S(3, 1.0, 40, -11))
# fly 2,4 s : éventail grand ouvert, battement lent
fly = anim("fly", 2.4, S(2.4, 2.5, 0, 12), S(2.4, 6.0, 0, 5), S(2.4, 4.0, -40, 8), n_kf=24)
# glide 3,6 s : traîne vers l'arrière, ondulation douce
glide = anim("glide", 3.6, S(3.6, 2.0, 0, 26), S(3.6, 2.5, 0, 2), S(3.6, 3.0, -40, -3), n_kf=24)
# attack et hurt : une fois, dernière image à zéro
atk = lambda t: bump(t, 0.0, 0.12, 0.28, 0.72)
attack = anim("attack", 0.8, lambda t: -2 * atk(t), lambda t: 9 * atk(t), lambda t: 16 * atk(t), n_kf=16, loop="once", lag=0.02)
hu = lambda t: bump(t, 0.0, 0.07, 0.2, 0.72)
tr = lambda t: 3.5 * math.sin(TAU * t * 5 / 0.8) * (1 - sm(t, 0.2, 0.7))
hurt = anim("hurt", 0.8, lambda t: 10 * hu(t) + tr(t) * 0.5, lambda t: tr(t), lambda t: -6 * hu(t), n_kf=16, loop="once", lag=0.02)


def particle_anim(name, length, curve, n):
    times = [i * length / n for i in range(n + 1)]
    return {"uuid": nuid(), "name": name, "loop": "loop", "override": False, "length": length, "snapping": 24, "selected": False,
            "animators": {groups[PL]["uuid"]: {"name": PL, "type": "bone", "keyframes": [kf(t, *curve(t)) for t in times]}}}


PF, PR = 4.0, 6.0
plume_fall = particle_anim("particle_plume_fall", PF, lambda t: (20 * math.sin(TAU * t / PF), 360 * t / PF, 14 * math.cos(2 * TAU * t / PF)), 24)
plume_rest = particle_anim("particle_plume_rest", PR, lambda t: (0, 0, 1.2 * math.sin(TAU * t / PR)), 12)

ANIMS = [idle, walk, run, sneak, fly, glide, attack, hurt, plume_fall, plume_rest]
assert len(EMITS) == 2 and 40 <= len(elements) <= 120, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
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
