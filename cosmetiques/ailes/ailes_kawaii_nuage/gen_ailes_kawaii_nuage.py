"""Ailes Nuage Guimauve (refonte du 2026-11-08) — ailes de chérubin-guimauve : un nuage dodu posé sur le bras, d'où
pendent deux rangées nettes de plumes rondes (couvertures rose framboise, rémiges lilas). Design original.
Ensemble Kawaii (thème Mignon). Écrit ailes_kawaii_nuage.png, ailes_kawaii_nuage_e.png et .build/ailes_kawaii_nuage_brut.bbmodel.

Pourquoi la refonte (« les trucs kawaii sont tous bof », 2026-11-08) : l'ancienne aile empilait six rangées de gouttes rose pâle
et blanches de même taille et de même valeur : en jeu, une masse floue sans structure. Ici :
- trois bandes de valeur seulement, lisibles de loin : NUAGE blanc (bosses rondes en vrai volume) / COUVERTURES rose franc /
  RÉMIGES lilas franc ; liseré coloré franc de 4 texels (framboise, violet), jamais de contour sombre ni noir ;
- proportions de dessin chibi (aile elliptique : bras court, plumes larges à bout rond, bout de l'aile arrondi par des
  primaires qui raccourcissent vers l'extérieur ; bord de fuite en festons réguliers) ;
- matière : nuage = boules peintes depuis leur normale (lumière en haut côté colonne, ombre froide lavande en bas, reflet en
  « fenêtre » net), bâties en dôme de 3 disques empilés (même ombrage recadré : de face on lit une boule, de profil un relief)
  autour d'une âme pleine ; plumes = peau + âme (recette des ailes de Bérénice, « la rondeur est bien ») avec fenêtre de reflet
  net et ombre de recouvrement mauve à la base ;
- dessous (vu de face quand l'aile s'ouvre) : rémiges crème rosé à liseré rose, sous-couvertures crème, bosses de nuage.
Recherche : codes de l'aile « chibi » des tutoriels de dessin (contour en festons, rangées qui s'allongent vers le bas, ne pas
détailler chaque plume, forme d'ensemble d'abord) ; leçon du thème : pastels très clairs = blancs en jeu → couleurs franches,
volumes doux (.claude/styles/kawaii.md). Silhouette différente des ailes de papillon de l'ensemble (plumes et nuage, pas
de membrane ni de nervures).

Squelette, animations, croisement : repris tels quels de la version précédente (12 états, attack/hurt, sneak et course
écartés le 2026-11-08 pour ne jamais croiser la colonne, vérificateur). Apparition (event_equip, 1,6 s) : le petit nuage de
l'épaule gonfle d'abord (« plop »), puis l'aile en sort repliée et s'ouvre comme un étirement ; retrait : à l'envers.
Lumière (_e) : seulement le liseré violet du bout des rémiges (≈ 190), net ; rien de diffus.
Fonctions avancées : calque _e, event_equip, event_unequip, un son à l'apparition (entity.chicken.egg). À juger en jeu :
apparition et retrait (somme avec l'état), liseré _e de nuit.
"""
import base64, io, json, math, os, re, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "ailes_kawaii_nuage"
AVEC_E = True
TEX = 512
V0, DV = 26, 5      # frétillement à la fusée (glide) : recette validée des ailes de Bérénice
SS = 4
D = 12.0            # texels par unité d'origine (avant K) : ≈ 6,7 texels/px en jeu
tex = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))


# ------------------------------------------------------------------ textures
def lerp(a, b, k):
    return a + (b - a) * k


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


F = lambda c: np.array(c, np.float32)
WHITE = F((255, 255, 255))

# Plumes : racine (sous la rangée du dessus), milieu, bout, liseré, ombre de recouvrement, reflet, lueur _e (ou None)
PLUME = {
    # rémiges : lilas franc, liseré violet ; bout un peu plus clair (on lit le feston)
    "p":  dict(root=(182, 152, 244), mid=(204, 180, 255), tip=(220, 200, 255), rim=(130, 86, 210), shadow=(146, 116, 208),
               hi=(240, 234, 255), shl=0.40, win=None, rimw=4.2, e=(160, 128, 205)),
    "s":  dict(root=(188, 158, 246), mid=(210, 186, 255), tip=(224, 206, 255), rim=(134, 90, 212), shadow=(150, 120, 210),
               hi=(238, 230, 255), shl=0.40, win=None, rimw=4.2, e=None),
    # couvertures : rose framboise franc, liseré framboise
    "g":  dict(root=(232, 104, 162), mid=(248, 124, 178), tip=(252, 144, 190), rim=(204, 52, 122), shadow=(184, 88, 156),
               hi=(255, 228, 240), shl=0.38, win=0.50, rimw=4.0, e=None),
    # dessous : rémiges crème rosé (liseré rose), sous-couvertures crème
    "pv": dict(root=(246, 160, 198), mid=(255, 180, 212), tip=(255, 194, 222), rim=(220, 84, 146), shadow=(200, 120, 176),
               hi=(255, 232, 242), shl=0.30, win=None, rimw=4.0, e=None),
    "u":  dict(root=(204, 180, 248), mid=(222, 204, 255), tip=(232, 218, 255), rim=(140, 104, 214), shadow=(160, 132, 212),
               hi=(246, 242, 255), shl=0.30, win=0.50, rimw=3.8, e=None),
}
NUAGE = dict(base=(255, 253, 254), mid=(255, 248, 252), shade=(238, 220, 244), rim=(204, 150, 210))
E_MAX = (160, 128, 205)


def _finish(col, alpha, ec, W, H):
    e_img = np.array(Image.fromarray(np.clip(ec, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    e_img = np.minimum(e_img, np.array(E_MAX, np.uint8))
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    a = np.array(Image.fromarray(alpha.astype(np.uint8), "L").resize((W, H), Image.LANCZOS))
    solid = a > 110
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = rgb
    if solid.any():
        arr[~solid, :3] = rgb[solid].mean(axis=0).astype(np.uint8)
    arr[..., 3] = solid * 255
    return Image.fromarray(arr, "RGBA"), e_img, solid


def window(px, py, cx, cy, rx, ry):
    """Reflet en « fenêtre » : ellipse nette (bord d'un texel après réduction) + petit point dessous."""
    a = 1 - smooth((((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 - 0.75) / 0.5)
    b = 1 - smooth((((px - cx - 0.2 * rx) / (rx * 0.38)) ** 2 + ((py - cy - 1.65 * ry) / (ry * 0.38)) ** 2 - 0.75) / 0.5)
    return np.maximum(a, b * 0.9)


def paint(W, H, kind, seed):
    """Plume ronde de chérubin : base arrondie, ventre large, bout en demi-ellipse franche. Base en haut, bout en bas."""
    P = {k: (F(v) if isinstance(v, tuple) else v) for k, v in PLUME[kind].items()}
    rng = np.random.default_rng(seed)
    jit = rng.uniform(0.985, 1.01)
    w, h = W * SS, H * SS
    x, y = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    t = y
    hw = 0.48
    ry = min(0.46, hw * W / H * 1.05)                       # bout : demi-ellipse (rond franc, jamais pointu)
    te = 1 - ry
    rb = min(0.16, hw * W / H * 0.5)
    grow = 0.62 + 0.38 * np.sin(np.pi / 2 * np.clip(t / te, 0, 1)) ** 0.6     # plume large dès la base : forme « chibi »
    tipcap = np.where(t > te, np.sqrt(np.clip(1 - ((t - te) / ry) ** 2, 0, 1)), 1.0)
    basecap = np.where(t < rb, np.sqrt(np.clip(1 - ((rb - t) / rb) ** 2, 0, 1)) * 0.5 + 0.5, 1.0)
    lim = hw * grow * tipcap * basecap
    d = x - 0.5
    r = np.abs(d) / np.maximum(lim, 1e-4)
    alpha = (r < 1) * 255.0

    k1 = smooth(t / 0.5)[..., None]
    k2 = smooth((t - 0.5) / 0.5)[..., None]
    col = lerp(lerp(P["root"], P["mid"], k1), P["tip"], k2) * jit
    col = col * (1.04 - 0.10 * (r ** 2))[..., None]                                # bombé doux
    shd = (np.clip(1 - t / P["shl"], 0, 1) ** 1.2)[..., None]
    col = lerp(col, P["shadow"], shd * 0.8)                                        # ombre de recouvrement
    side = (np.clip((r - 0.55) / 0.45, 0, 1) * (d < 0))[..., None]
    col = lerp(col, P["shadow"], side * 0.25)                                      # bord intérieur recouvert par la voisine
    px, py = x * W, y * H                                                          # en texels
    if P["win"] is None:                                                           # rémiges : reflet doux en bande, pas de pois
        wn = (np.exp(-((d + 0.16) / 0.10) ** 2) * smooth((t - 0.38) / 0.15) * (1 - smooth((t - 0.80) / 0.1)))[..., None]
        col = lerp(col, P["hi"], wn * 0.45)
    else:
        wn = window(px, py, 0.34 * W, P["win"] * H, 0.12 * W, min(0.09 * H, 0.17 * W))[..., None]
        col = lerp(col, P["hi"], wn * 0.9)
    dist = (1 - r) * lim * W
    rk = (np.clip((P["rimw"] - dist) / 1.2 + 0.5, 0, 1) * smooth((t - 0.10) / 0.12))[..., None]
    col = lerp(col, P["rim"], rk)                                                  # liseré coloré franc (≥ 4 texels)

    ec = np.zeros(col.shape, np.float32)
    if P["e"] is not None:                                                          # lueur : fin liseré au bout seulement
        line = (np.clip((P["rimw"] - dist) / 1.2 + 0.5, 0, 1) * smooth((t - 0.72) / 0.10))[..., None]
        ec = lerp(ec, P["e"], line)
    return _finish(col, alpha, ec, W, H)


def paint_puff(W, H, crop, seed, rim=True):
    """Bosse de nuage : boule mate éclairée depuis sa normale (lumière en haut, côté colonne), ombre froide en bas, reflet en
    fenêtre net. crop < 1 : disque central de la même boule (dôme empilé sans couture de face)."""
    rng = np.random.default_rng(seed)
    w, h = W * SS, H * SS
    x, y = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    nx, ny = (x * 2 - 1) * crop, (y * 2 - 1) * crop
    r2 = nx ** 2 + ny ** 2
    alpha = (r2 < crop ** 2) * 255.0
    nz = np.sqrt(np.clip(1 - r2, 0, 1))
    L = np.array((-0.42, -0.58, 0.70))
    L = L / np.linalg.norm(L)
    lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    c = NUAGE
    col = lerp(F(c["shade"]), F(c["mid"]), smooth(lam * 1.25)[..., None])
    col = lerp(col, F(c["base"]), smooth((lam - 0.62) / 0.3)[..., None])
    col = col * rng.uniform(0.99, 1.005)
    wn = window(nx, ny, -0.36, -0.40, 0.22, 0.15)[..., None]
    col = lerp(col, WHITE, wn * 0.95)
    if rim:
        dist = (1 - np.sqrt(r2)) * W / 2
        k = (np.clip((3.4 - dist) / 1.2 + 0.5, 0, 1) * (0.55 + 0.45 * smooth((ny + 0.2) / 0.8)))[..., None]
        col = lerp(col, F(c["rim"]), k)                                           # liseré lavande, plus marqué en bas
    return _finish(col, alpha, np.zeros(col.shape, np.float32), W, H)


def edge_strip(kind, W=6, H=32):
    """Bande opaque des âmes : suit le dégradé de la plume, teintée par le liseré pour dessiner le bord vu de profil."""
    P = PLUME[kind]
    a = np.zeros((H, W, 4), np.float32)
    for yy in range(H):
        t = (yy + 0.5) / H
        cc = lerp(F(P["root"]), F(P["mid"]), min(1, t * 2)) if t < 0.5 else lerp(F(P["mid"]), F(P["tip"]), (t - 0.5) * 2)
        a[yy, :, :3] = lerp(cc, F(P["rim"]), 0.35)
    a[..., 3] = 255
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def solid_tile(W, H, top, bot):
    a = np.zeros((H, W, 4), np.float32)
    top, bot = F(top), F(bot)
    for yy in range(H):
        a[yy, :, :3] = lerp(top, bot, yy / max(1, H - 1))
    a[..., 3] = 255
    return Image.fromarray(a.astype(np.uint8), "RGBA")


# images à peindre : nom → (fonction, W, H) ; puis rangées par hauteur décroissante dans l'atlas
SPECS = {}
def spec_plume(name, kind, w, L):
    SPECS[name] = ("plume", kind, int(round(w * D)), int(round((L + 0.4) * D)))


for i in range(2):
    spec_plume(f"pL{i}", "p", 4.6, 11.0)
    spec_plume(f"pS{i}", "p", 4.6, 7.8)
for i in range(3):
    spec_plume(f"s{i}", "s", 4.4, 11.4)
spec_plume("pvL0", "pv", 4.6, 11.0)
spec_plume("pvS0", "pv", 4.6, 7.8)
spec_plume("sv0", "pv", 4.4, 11.4)
for i in range(3):
    spec_plume(f"g{i}", "g", 4.4, 5.2)
for i in range(2):
    spec_plume(f"u{i}", "u", 4.2, 4.8)
for i in range(3):
    SPECS[f"nu{i}"] = ("puff", 1.0, 56, 56)
SPECS["nuA"] = ("puff", 0.72, 40, 40)
SPECS["nuB"] = ("puff", 0.42, 24, 24)

UV, EIMG = {}, {}
cx_, cy_, shelf = 0, 0, 0


def place(name, img):
    global cx_, cy_, shelf
    w, h = img.size
    if cx_ + w > TEX:
        cx_, cy_, shelf = 0, cy_ + shelf, 0
    assert cy_ + h <= TEX, "atlas plein"
    tex.paste(img, (cx_, cy_))
    UV[name] = (cx_, cy_, cx_ + w, cy_ + h)
    cx_ += w
    shelf = max(shelf, h)


seed = 1
for name, sp in sorted(SPECS.items(), key=lambda kv: -kv[1][3]):
    if sp[0] == "plume":
        im, ea, mask = paint(sp[2], sp[3], sp[1], seed)
    else:
        im, ea, mask = paint_puff(sp[2], sp[3], sp[1], seed, rim=sp[1] >= 1.0)
    place(name, im)
    EIMG[name] = (ea, mask)
    seed += 1
for kind in ("p", "s", "g", "pv", "u"):
    place(f"edge_{kind}", edge_strip(kind))
place("edge_nu", solid_tile(6, 32, (255, 250, 255), (232, 222, 250)))
place("bone", solid_tile(16, 16, (250, 236, 250), (214, 200, 240)))
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex.getpixel((TEX - 3, TEX - 3))[3] == 0
_t = np.array(tex)
_t[..., :3] &= 0xFC
assert set(np.unique(_t[..., 3])) <= {0, 255}, "semi-transparence"
tex = Image.fromarray(_t, "RGBA")
tex.save(f"{NOM}.png", optimize=True)
_b = io.BytesIO()
tex.save(_b, "PNG", optimize=True)
tex_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()

# Calque lumineux (guide, section 5 bis) : jamais assigné aux faces, additif.
_e = np.zeros((TEX, TEX, 4), np.uint8)
for name, (ea, mask) in EIMG.items():
    u0, v0, u1, v1 = UV[name]
    _e[v0:v1, u0:u1, :3] = ea
    _e[v0:v1, u0:u1, 3] = mask * 255
for name in [f"edge_{k}" for k in ("p", "s", "g", "pv", "u", "nu")] + ["bone"]:
    u0, v0, u1, v1 = UV[name]
    _e[v0:v1, u0:u1] = (0, 0, 0, 255)
_emax = int(_e[..., :3].max())
assert 150 <= _emax <= 225, ("sources _e : 150 à 225", _emax)
tex_e = Image.fromarray(_e, "RGBA")
tex_e.save(f"{NOM}_e.png", optimize=True)
_b = io.BytesIO()
tex_e.save(_b, "PNG", optimize=True)
tex_e_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()

# ------------------------------------------------------------------ géométrie
ALL = ("north", "south", "east", "west", "up", "down")


def nuid():
    return str(_uuid.uuid4())


elements, groups = [], {}

# Taille : géométrie dessinée en unités d'origine, agrandie de K autour de la racine (x = ±2,6, y = 23, z = 2).
K = 1.8
P0 = (2.6, 23.0, 2.0)
LR = 1.4


def kx(p):
    sx = 1 if p[0] >= 0 else -1
    c = (sx * P0[0], P0[1], P0[2])
    return [c[i] + K * (p[i] - c[i]) for i in range(3)]


def cube(name, frm, to, origin, rot=(0, 0, 0), faces=None):
    sx = 1 if origin[0] >= 0 else -1
    c = (sx * P0[0], P0[1], P0[2])
    frm, to, origin = ([c[i] + K * (q[i] - c[i]) for i in range(3)] for q in (frm, to, origin))
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(v, 2) for v in frm], "to": [round(v, 2) for v in to],
         "origin": [round(v, 2) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(v, 1) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(rot):
        e["rotation"] = [round(v, 1) for v in rot]
    elements.append(e)
    return e["uuid"]


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups
    origin = kx(origin)
    groups[name] = {"origin": [round(v, 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(v, 2) for v in rotation]}
    return name


Z = 3.9          # plan médian de l'aile (dos du joueur à z = 2)
SKIN = 0.3
EMBED = 0.12

# Couches : deux plumes voisines d'une rangée ne sont jamais au même niveau (recette ailes_berenice).
ALT = {"p": [0.45, 0.0, 0.3, 0.6, 0.15], "s": [0.3, 0.0, 0.2, 0.7], "t": [0.6, -0.3], "gc": [0.0, 0.3, 0.6],
       "uc": [0.0, -0.36, -0.18]}


def alt(fam, k):
    v = ALT.get(fam, [0.0])
    return v[k % len(v)]


def stack(z0, z1, t0, t1):
    return (lambda a, L: lerp(z0, z1, a / L)), (lambda a, L: lerp(t0, t1, a / L))


def remex(bend):
    return stack(0.45, -bend, 1.15, 0.64)


STACK = {"g": stack(1.75, 1.30, 0.9, 0.62), "u": stack(-0.75, -0.55, 0.9, 0.62)}


def feather(name, s, ax, ay, L, w, tilt, uv, parent, prof, side="both", ncore=2, own_bone=False, zb=None, uv_v=None, ekind=None):
    """Plume peau + âme. tilt > 0 : le bout part vers l'extérieur. uv_v : image du dessous (face north)."""
    kind = ekind or re.match(r"[a-z]+", uv).group()
    zc, thick = prof
    zb = Z if zb is None else zb
    bx = s * ax
    tgt = group(name, [bx, ay, zb + zc(0, L)], parent=parent) if own_bone else parent

    def faces_of(u):
        u0, v0, u1, v1 = UV[u]
        so = [u0, v0, u1, v1] if s > 0 else [u1, v0, u0, v1]
        return so, [so[2], v0, so[0], v1]

    south, north = faces_of(uv)
    if uv_v:
        north = faces_of(uv_v)[1]
    rz = s * tilt
    sn, cs = math.sin(math.radians(tilt)), math.cos(math.radians(tilt))
    zd = lambda a: zb + zc(a, L) + thick(a, L) / 2
    zv = lambda a: zb + zc(a, L) - thick(a, L) / 2

    def skin(tag, z0, z1, faces_s, faces_n, inward):
        pitch = math.degrees(math.atan2(z0 - z1, L))
        a, b = sorted((z0, z0 + inward * SKIN))
        faces = {"south": faces_s, "north": faces_n, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
        groups[tgt]["ids"].append(cube(f"{name}.{tag}", [bx - w / 2, ay - L, a], [bx + w / 2, ay + 0.4, b], [bx, ay, z0],
                                       rot=(pitch, 0, rz), faces=faces))

    if side in ("both", "d"):
        skin("d", zd(0), zd(L), south, CLEAR if side == "both" else north, -1)
    if side in ("both", "v"):
        skin("v", zv(0), zv(L), CLEAR if side == "both" else south, north, +1)

    e0, e1, e2, e3 = UV[f"edge_{kind}"]
    t_start, t_end = 0.16, 0.80
    for j in range(ncore):
        t0 = lerp(t_start, t_end, j / ncore)
        t1 = lerp(t_start, t_end, (j + 1) / ncore)
        a0, a1 = t0 * L, t1 * L
        k = 1 - 0.45 * (j + 0.5) / ncore
        wc = w * 0.46 * k
        if side == "both":
            top, bot = zd(a1) - SKIN + EMBED, zv(a1) + SKIN - EMBED
        elif side == "d":
            top = zd(a1) - SKIN + EMBED
            bot = top - max(0.45, thick(a1, L))
        else:
            bot = zv(a1) + SKIN - EMBED
            top = bot + max(0.45, thick(a1, L))
        zm = (top + bot) / 2
        x, y = bx + s * sn * a0, ay - cs * a0
        if side == "both":
            pitch = math.degrees(math.atan2(zc(a0, L) - zc(a1, L), a1 - a0))
        else:
            sf = zd if side == "d" else zv
            pitch = math.degrees(math.atan2(sf(a0) - sf(a1), a1 - a0))
        z = zm + math.tan(math.radians(pitch)) * (a1 - a0)
        ea, eb = lerp(e1, e3, t0), lerp(e1, e3, t1)
        faces = {"south": [e0, ea, e2, eb], "north": [e0, ea, e2, eb], "east": [e0, ea, e2, eb], "west": [e0, ea, e2, eb],
                 "up": [e0, ea, e2, min(e3, ea + 1)], "down": [e0, max(e1, eb - 1), e2, eb]}
        ov = 0.12 if j else 0.0
        groups[tgt]["ids"].append(cube(f"{name}.c{j}", [x - wc / 2, y - (a1 - a0), z - (top - bot) / 2], [x + wc / 2, y + ov, z + (top - bot) / 2],
                                       [x, y, z], rot=(pitch, 0, rz), faces=faces))


# Bosse de nuage : dôme de 3 disques (même boule recadrée) + âme pleine derrière le grand disque. out = +1 : dôme vers le dos
# (+Z, face south) ; -1 : vers le joueur (face north, dessous de l'aile).
DOME = [(1.0, 0.0, None), (0.72, 0.39, "nuA"), (0.42, 0.70, "nuB")]


def puff(name, s, cx, cy, d, z0, parent, var, out=+1, zback=None, core=True):
    """Bosse de nuage. De face : grand disque + 2 calottes (même boule recadrée : on lit une sphère). Derrière : âme
    octogonale pleine (essai de disques croisés abandonné : traits gris en croix sur chaque boule)."""
    bx = s * cx
    big = UV[f"nu{var % 3}"]
    for n, (f, dz, img) in enumerate(DOME):
        u0, v0, u1, v1 = UV[img] if img else big
        so = [u0, v0, u1, v1] if s > 0 else [u1, v0, u0, v1]
        no = [so[2], v0, so[0], v1]
        r = d * f / 2
        zf = z0 + out * dz                       # face visible
        a, b = sorted((zf, zf - out * SKIN))
        faces = {"south": so if out > 0 else CLEAR, "north": no if out < 0 else CLEAR,
                 "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
        groups[parent]["ids"].append(cube(f"{name}.{n}", [bx - r, cy - r, a], [bx + r, cy + r, b], [bx, cy, zf], faces=faces))
    # âme : prisme octogonal (deux cubes à 45°) caché derrière le grand disque (bosses isolées : épaule)
    if not core:
        return
    e0, e1, e2, e3 = UV["edge_nu"]
    q = d * 0.21
    zi = z0 - out * (SKIN - EMBED)
    depth = max(0.7, out * (zi - zback)) if zback is not None else max(0.7, d * 0.34)   # âme jusqu'au bras : pas de vide de profil
    a, b = sorted((zi, zi - out * depth))
    for n, rz in enumerate((0, 45)):
        groups[parent]["ids"].append(cube(f"{name}.c{n}", [bx - q, cy - q, a + 0.03 * n], [bx + q, cy + q, b - 0.03 * n], [bx, cy, (a + b) / 2],
                                          rot=(0, 0, rz), faces={k: [e0, e1, e2, e3] for k in ALL}))


def puff_up(name, s, cx, cy, zc, d, ang, parent, var):
    """Bosse de nuage tournée vers le haut (disque horizontal + calottes) : vu de dessus et de 3/4 haut, le dessus du nuage
    reste fait de boules, pas d'une barre."""
    bx = s * cx
    for n, (f, dy, img) in enumerate(DOME):
        u0, v0, u1, v1 = UV[img] if img else UV[f"nu{var % 3}"]
        r = d * f / 2
        yf = cy + dy
        faces = {"up": [u0, v0, u1, v1], "down": CLEAR, "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR}
        groups[parent]["ids"].append(cube(f"{name}.{n}", [bx - r, yf - SKIN, zc - r], [bx + r, yf, zc + r], [bx, cy, zc],
                                          rot=(0, 0, s * ang), faces=faces))


def tube(name, s, i, parent, y_off, hy, z1, z2):
    """Âme continue du nuage le long d'un segment du bras : prisme octogonal (boîte + boîte tournée de 45° autour du bras).
    De profil et de dessus, le nuage est un volume plein, pas une palissade d'âmes séparées."""
    (x0, y0), (x1, y1) = ARM[i], ARM[i + 1]
    L = math.dist(ARM[i], ARM[i + 1])
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    a, b = sorted([s * (x0 - 0.5), s * (x0 + L + (0.5 if i < 2 else -0.3))])
    zc, hz = (z1 + z2) / 2, (z2 - z1) / 2
    yc = y0 + y_off
    fc = {k: list(UV["edge_nu"]) for k in ALL}
    groups[parent]["ids"].append(cube(f"{name}a", [a, yc - hy, z1], [b, yc + hy, z2], [s * x0, y0, zc], rot=(0, 0, s * ang), faces=fc))
    q = min(hy, hz) * 1.0
    groups[parent]["ids"].append(cube(f"{name}b", [a + 0.12, yc - q, zc - q], [b - 0.12, yc + q, zc + q], [s * x0, y0, zc],
                                      rot=(45, 0, s * ang), faces=fc))
    return ang


# bras court et arqué : épaule basse près de la colonne, sommet vers y = 28,4, main courte
ARM = [(2.6, 23.0), (5.0, 26.5), (8.2, 28.4), (10.8, 27.9)]
YAW = [14, -6, 6]
SEG = ["shoulder", "elbow", "wrist"]
NP, NS = 5, 4


def pos(i, f):
    return lerp(ARM[i][0], ARM[i + 1][0], f), lerp(ARM[i][1], ARM[i + 1][1], f)


def tilt_at(i, f):
    if i == 0:
        return 0 + 3 * f
    if i == 1:
        return 3 + 10 * f
    return 15 + 56 * f ** 1.1


CORE_R = [(1.30, 1.10), (1.10, 0.85), (0.85, 0.60)]
CORE_Z = 0.8


def core_radius(i, f):
    return lerp(CORE_R[i][0], CORE_R[i][1], f)


def chaikin(pts, n=3):
    for _ in range(n):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(lerp(a[0], b[0], .25), lerp(a[1], b[1], .25)), (lerp(a[0], b[0], .75), lerp(a[1], b[1], .75))]
        out.append(pts[-1])
        pts = out
    return pts


SMOOTH = chaikin(ARM)
_ls = [0.0]
for a_, b_ in zip(SMOOTH, SMOOTH[1:]):
    _ls.append(_ls[-1] + math.dist(a_, b_))
LENS = [math.dist(ARM[i], ARM[i + 1]) for i in range(3)]


def arch(u):
    d = u * _ls[-1]
    for n in range(len(SMOOTH) - 1):
        if d <= _ls[n + 1]:
            k = (d - _ls[n]) / max(1e-6, _ls[n + 1] - _ls[n])
            return lerp(SMOOTH[n][0], SMOOTH[n + 1][0], k), lerp(SMOOTH[n][1], SMOOTH[n + 1][1], k)
    return SMOOTH[-1]


def seg_at(u):
    dd = u * sum(LENS)
    i = 0
    while i < 2 and dd > LENS[i]:
        dd -= LENS[i]
        i += 1
    return i, min(1.0, dd / LENS[i])


# Nuage du bras : deux rangées de bosses. Niveaux de profondeur en quinconce (période 4) : deux bosses qui se recouvrent
# ne sont jamais au même niveau.
CLOUD_LV = [0.0, 0.49, 0.60]   # calculé : aucun écart < 0,08 entre disques de deux bosses voisines (disques à 0 / 0,39 / 0,70 : écart mini 0,10, soit 0,19 px)


def build(s):
    tag = "l" if s < 0 else "r"
    segs = []
    for i in range(3):
        segs.append(group(f"{SEG[i]}_{tag}", [s * ARM[i][0], ARM[i][1], Z], parent=segs[i - 1] if i else None,
                          rotation=(0, -s * YAW[i], 0)))
    # noyau : section octogonale (deux cubes à 45°), caché sous le nuage
    bone_faces = {k: list(UV["bone"]) for k in ALL}
    zb = Z + CORE_Z
    for i in range(3):
        (x0, y0), (x1, y1) = ARM[i], ARM[i + 1]
        L = math.dist(ARM[i], ARM[i + 1])
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        a, b = sorted([s * (x0 - 0.4), s * (x0 + L + 0.2)])
        r = (CORE_R[i][0] + CORE_R[i][1]) / 2
        q = r * 0.56
        groups[segs[i]]["ids"].append(cube(f"arm{i}_{tag}", [a, y0 - q, zb - q], [b, y0 + q, zb + q],
                                           [s * x0, y0, zb], rot=(0, 0, s * ang), faces=bone_faces))
        groups[segs[i]]["ids"].append(cube(f"arm{i}b_{tag}", [a + 0.09, y0 - q * 0.97, zb - q * 0.97], [b - 0.09, y0 + q * 0.97, zb + q * 0.97],
                                           [s * x0, y0, zb], rot=(45, 0, s * ang), faces=bone_faces))
    a, b = sorted([s * 1.2, s * 2.9])
    wr = group(f"wingroot_{tag}", [s * 2.6, 23.0, Z])
    groups[wr]["ids"].append(cube(f"root_{tag}", [a, 22.5, 2.15], [b, 24.2, Z + 0.9], [s * 2.6, 23.0, Z], faces=bone_faces))

    # rémiges : primaires (main, 5, os propres) qui raccourcissent vers l'extérieur → bout de l'aile rond
    for k in range(NP):
        f = (k + 0.5) / NP
        ax, ay = pos(2, f)
        L = (8.2 - 3.0 * f ** 1.3 + (0.25 if k % 2 else 0)) * LR
        big = L > 9.4
        feather(f"p{k}_{tag}", s, ax, ay - 0.3, L, 4.6, tilt_at(2, f), f"pL{k % 2}" if big else f"pS{k % 2}", segs[2], remex(0.6),
                ncore=2, own_bone=True, zb=Z + alt("p", k), uv_v="pvL0" if big else "pvS0")
    # secondaires (avant-bras, 4) : bord de fuite en festons réguliers
    for k in range(NS):
        f = (k + 0.5) / NS
        ax, ay = pos(1, f)
        L = (8.0 + 0.4 * f + (0.5 if k % 2 else 0)) * LR
        feather(f"s{k}_{tag}", s, ax, ay - 0.3, L, 4.4, tilt_at(1, f), f"s{k % 3}", segs[1], remex(0.35), ncore=2, own_bone=True,
                zb=Z + alt("s", k), uv_v="sv0")
    # tertiaires (humérus, 2)
    for k in range(2):
        f = (k + 0.55) / 2
        ax, ay = pos(0, f)
        feather(f"t{k}_{tag}", s, ax, ay - 0.3, 6.4 + 1.2 * k, 4.2, tilt_at(0, f), f"s{(k + 1) % 3}", segs[0], remex(0.2), ncore=2,
                zb=Z + alt("t", k), uv_v="sv0")

    # couvertures (dos) : une seule rangée rose franc, larges, qui couvrent le haut des rémiges
    NG = 6
    for k in range(NG):
        u = lerp(0.02, 0.96, (k + 0.5) / NG)
        i, f = seg_at(u)
        ax, ay = arch(u)
        L = lerp(5.4, 4.8, u) * (1 + 0.05 * math.sin(k * 2.4))
        feather(f"gc{k}_{tag}", s, ax, ay - 0.4, L, 4.4, tilt_at(i, f) * 0.9, f"g{k % 3}", segs[i], STACK["g"], side="d", ncore=1,
                zb=Z + alt("gc", k))
    # sous-couvertures (dessous) : crème
    NU = 6
    for k in range(NU):
        u = lerp(0.04, 0.96, (k + 0.5) / NU)
        i, f = seg_at(u)
        ax, ay = arch(u)
        feather(f"uc{k}_{tag}", s, ax, ay - 0.3, lerp(5.0, 4.4, u), 4.2, tilt_at(i, f) * 0.9, f"u{k % 2}", segs[i], STACK["u"], side="v",
                ncore=1, zb=Z + alt("uc", k))

    # NUAGE du bras (dos) : grosses bosses sur le bras, petites bosses en crête au-dessus (bord d'attaque festonné)
    NC = 7
    for k in range(NC):
        u = lerp(0.0, 0.97, (k + 0.5) / NC)
        i, f = seg_at(u)
        ax, ay = arch(u)
        d = lerp(4.3, 3.4, u ** 0.8)
        puff(f"cl{k}_{tag}", s, ax, ay - 0.25, d, Z + 2.65 + CLOUD_LV[k % 3], segs[i], k, core=False)
    NK = 6
    for k in range(NK):
        u = lerp(0.04, 0.99, (k + 0.5) / NK)
        i, f = seg_at(u)
        ax, ay = arch(u)
        d = lerp(3.3, 2.5, u)
        puff(f"ck{k}_{tag}", s, ax, ay + core_radius(i, f) + 0.95, d, Z + 1.25 + CLOUD_LV[(k + 1) % 3], segs[i], k + 1, core=False)
    # nuage du dessous : une rangée de bosses côté joueur (vue de face quand l'aile s'ouvre)
    NV = 6
    for k in range(NV):
        u = lerp(0.04, 0.97, (k + 0.5) / NV)
        i, f = seg_at(u)
        ax, ay = arch(u)
        puff(f"cv{k}_{tag}", s, ax, ay + 0.2, lerp(3.8, 3.0, u), Z - 1.55 - CLOUD_LV[k % 3], segs[i], k + 2, out=-1, core=False)
    # âme continue du nuage (un prisme par segment) et bosses du dessus
    for i in range(3):
        ang = tube(f"cloud{i}_{tag}", s, i, segs[i], 0.35, 1.45 - 0.15 * i, Z + 0.95, Z + 1.50)
        n = 3 if i < 2 else 2
        for k in range(n):
            f = (k + 0.5) / n
            ax, ay = pos(i, f)
            puff_up(f"cu{i}{k}_{tag}", s, ax, ay + 0.35 + 1.45 - 0.15 * i + 0.08 + CLOUD_LV[(3 * i + k) % 3], Z + 1.55 + 0.25 * ((k + i) % 2 - 0.5),
                    lerp(2.9, 2.3, (i + f) / 3), ang, segs[i], k + i)
    # petit nuage de l'épaule : couvre l'attache (on ne voit jamais où l'aile « est collée »)
    lr = 0.12 if s < 0 else 0.0
    for k, (cx, cy, d, dz) in enumerate([(3.5, 24.3, 4.2, 0.0), (4.4, 26.3, 3.6, 0.16), (3.3, 22.4, 3.2, 0.08)]):
        puff(f"sc{k}_{tag}", s, cx, cy, d, Z + 4.1 + dz + lr, segs[0], k, zback=Z + 1.0)
    return segs[0]


L_, R_ = build(-1), build(1)


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(),
             "children": [bone("wingroot_l"), bone("wingroot_r"), bone(L_), bone(R_)]}]

# ------------------------------------------------------------------ animations
# Intention pour l'aile GAUCHE : fx > 0 le plan bascule vers l'horizontale ; fy > 0 pivote vers l'arrière ; fz > 0 la pointe monte.
TAU = 2 * math.pi
# MIROIR D'AXES : seul endroit à toucher si la convention change (guide, section 3).
SX, SY, SZ = -1, -1, +1


def mirror(s, fx, fy, fz):
    return SX * fx, s * SY * fy, s * SZ * fz


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 2)), "y": str(round(y + 0.0, 2)), "z": str(round(z + 0.0, 2))}],
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


def add(*fs):
    return lambda t: sum(f(t) for f in fs)


def anim(name, length, segs, fan, n_kf=None, loop="loop", only=None):
    A = {}

    def put(g, kfs):
        if only is None or re.sub(r"\d*_[lr]$", "", g) in only:
            A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}

    n = n_kf or max(8, int(round(length * 10)))
    times = [i * length / n for i in range(n + 1)]
    for s, tag in ((-1, "l"), (1, "r")):
        for seg, (fx, fy, fz) in segs.items():
            put(f"{seg}_{tag}", [kf("rotation", t, *mirror(s, fx(t), fy(t), fz(t))) for t in times])
        for k in range(5):
            w = 0.4 + 0.6 * (k + 0.5) / 5
            put(f"p{k}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, fan(t) * w)) for t in times])
        for k in range(4):
            put(f"s{k}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, fan(t) * 0.3 * (k + 0.5) / 4)) for t in times])
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "idle", "animators": A}


Z0 = C(0)

# idle 8 s : respiration (4 s), ailes ouvertes à moitié (balayage arrière 15°, refonte 2026-11-08 : silhouette lisible de dos) ; étirement-frétillement (5 Hz,
# 4,9–6,3 s) : elles s'ouvrent et battent trois petits coups
fr = lambda t: bump(t, 4.9, 5.1, 6.0, 6.3)
wig = lambda amp, ph=0: (lambda t: amp * fr(t) * math.sin(TAU * 5 * (t - 4.9) + math.radians(ph)))
idle = anim("idle", 8.0, {
    "shoulder": (add(S(4, 1.0, 0, 4), lambda t: 6 * fr(t)), add(S(4, 1.5, 0, 15), lambda t: -14 * fr(t)), add(S(4, 2, 0, 2), wig(11), lambda t: 4 * fr(t))),
    "elbow":    (Z0, add(S(4, 1, -40, -10), lambda t: 6 * fr(t)), add(S(4, 1.5, -40, -2), wig(5, -50))),
    "wrist":    (Z0, add(S(4, 0.8, -70, 12), lambda t: -8 * fr(t)), add(S(4, 1, -70, -6), wig(6, -90)))},
    fan=lambda t: 3 + 1.0 * math.sin(TAU * t / 4) + 6 * fr(t), n_kf=200)

# fly 0,7 s : petites ailes qui frétillent. Joueur debout : plan basculé d'environ 40°, battement court et rapide.
T = 0.7
up = lambda t, lag=0.0: 0.5 + 0.5 * math.cos(TAU * (t / T - lag))
fly = anim("fly", T, {
    "shoulder": (S(T, 4, 90, 40), S(T, 5, 90, 4), S(T, 24, 0, 9)),
    "elbow":    (Z0, lambda t: 6 - 4 * up(t, 0.12), S(T, 9, -45, 0)),
    "wrist":    (Z0, lambda t: -6 + 4 * up(t, 0.22), lambda t: 4 + 5 * math.sin(TAU * t / T - math.radians(75)) - 10 * up(t, 0.22))},
    fan=lambda t: 6 - 5 * math.cos(TAU * t / T), n_kf=21)

# glide 3,6 s : corps couché, ailes dans le plan du dos, grandes ouvertes, battement lent ; frétillement à la fusée (Molang, recette Aurelion)
G = 3.6
BOOST = f"math.clamp((math.max(q.ground_speed,q.vertical_speed)-{V0})/{DV},0,1)*math.clamp((q.vertical_speed+8)/4,0,1)"


def term(amp, speed, ph):
    if not amp:
        return ""
    p = f"{ph:+g}" if ph else ""
    return f"{amp:+g}*math.sin(q.anim_time*{speed}{p})"


def mol(sign, base, slow=(0, 0), boost=(0, 0)):
    e = f"{sign * base:g}" + term(sign * slow[0], 100, slow[1])
    if boost[0]:
        e += f"{sign * boost[0]:+g}*{BOOST}*math.sin(q.anim_time*600{boost[1]:+g})"
    assert len(e) <= 256
    return e


def mkf(x, y, z):
    return {"channel": "rotation", "data_points": [{"x": x, "y": y, "z": z}], "time": 0, "interpolation": "linear"}


def glide_anim():
    a = anim("glide", G, {k: (Z0, Z0, Z0) for k in SEG}, fan=C(0), n_kf=8)
    A = a["animators"]
    A.clear()

    def put(g, x, y, z):
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [mkf(x, y, z)]}

    for s_, tag in ((-1, "l"), (1, "r")):
        sy, sz = s_ * SY, s_ * SZ
        put(f"shoulder_{tag}", mol(SX, 8, (1.5, 90)), mol(sy, -12, (10, 0), (22, 0)), f"{sz * -2:g}")
        put(f"elbow_{tag}", "0", mol(sy, 6, (-3, -43), (10, -45)), f"{sz * 2:g}")
        put(f"wrist_{tag}", "0", mol(sy, -6, (4, -79), (12, -90)), f"{sz * 6:g}")
        for k in range(5):
            w = 0.4 + 0.6 * (k + 0.5) / 5
            put(f"p{k}_{tag}", "0", "0", mol(sz, round(9 * w, 2), (round(-2 * w, 2), 90), (round(6 * w, 2), -90)))
        for k in range(4):
            w = 0.3 * (k + 0.5) / 4
            put(f"s{k}_{tag}", "0", "0", mol(sz, round(9 * w, 2), (round(-2 * w, 2), 90)))
    return a


glide = glide_anim()

# fall 1,5 s : relevées et ouvertes (freinage), plan demi-basculé ; petit frétillement d'équilibre
AI = 1.5
fall = anim("fall", AI, {"shoulder": (S(AI, 3, 0, 26), C(-4), add(C(16), S(AI / 3, 5, 0))),
                         "elbow": (Z0, C(3), S(AI / 3, 3, -40, 6)),
                         "wrist": (Z0, C(-4), S(AI / 3, 3, -70, 8))},
            fan=C(9), n_kf=24)

# walk 1,6 s : ramenées vers l'arrière, petit balancement au pas (deux pas par cycle)
W = 1.6
walk = anim("walk", W, {"shoulder": (C(6), S(W, 4, 0, 24), S(W / 2, 3, 0, -2)),
                        "elbow": (Z0, S(W, 3, -40, -8), S(W / 2, 2, -40, -2)),
                        "wrist": (Z0, S(W, 3, -70, 10), S(W / 2, 2.5, -70, -4))},
            fan=C(-4))

# run 1,0 s : nettement vers l'arrière, abaissées, repli en S réparti sur les 3 articulations, petit sautillement
R = 1.0
run = anim("run", R, {"shoulder": (C(12), S(R, 3, 0, 42), S(R / 2, 3, 0, -12)),
                      "elbow": (Z0, S(R, 2, -40, -24), S(R / 2, 1.5, -40, -4)),
                      "wrist": (Z0, S(R, 3, -80, 30), S(R / 2, 2, -80, -6))},
          fan=C(-5))
RUN_ECART = 1.2   # 2026-11-08 : scapulaires à 3,6 px de l'autre côté de la colonne (épaule à 45°) → épaule écartée vers l'extérieur
for s_, tag in ((-1, "l"), (1, "r")):
    run["animators"][groups[f"shoulder_{tag}"]["uuid"]]["keyframes"].append(kf("position", 0, s_ * RUN_ECART, 0, 0))

# sneak 3 s : repliées serrées dans le dos, pointes qui remontent. Mise au guide du 2026-11-08 : épaule 50° → 40° (le coude
# et le poignet reprennent le repli, -30 → -20 et 34 → 36) et épaule écartée de 1,4 px vers l'extérieur : les scapulaires
# (loin derrière le pivot) passaient la colonne de 4,55 px (vérificateur, ailes_orage v4) ; 2,49 px mesurés, même silhouette.
SN = 3.0
SN_ECART = 1.4
sneak = anim("sneak", SN, {"shoulder": (C(4), S(SN, 1, 0, 40), S(SN, 1, 0, 8)),
                           "elbow": (Z0, C(-20), S(SN, 1, -40, 6)),
                           "wrist": (Z0, C(36), C(12))},
             fan=C(-8))
for s_, tag in ((-1, "l"), (1, "r")):     # position : +x = droite du joueur (guide, section 3)
    sneak["animators"][groups[f"shoulder_{tag}"]["uuid"]]["keyframes"].append(kf("position", 0, s_ * SN_ECART, 0, 0))

# sleep 4 s : repliées, tombantes, respiration très lente
SL = 4.0
sleep = anim("sleep", SL, {"shoulder": (C(10), S(SL, 1, 0, 32), S(SL, 1.5, 0, -10)),
                           "elbow": (Z0, C(-14), C(-10)),
                           "wrist": (Z0, C(16), C(-16))},
             fan=C(-6))

# swim 2 s : corps couché, ailes dans le plan du dos, rabattues vers les pieds, ondulation hors du plan par Y. Déduit.
SW = 2.0
swim = anim("swim", SW, {"shoulder": (C(6), S(SW, 7, 0, 2), C(-14)),
                         "elbow": (Z0, S(SW, 6, -45, 4), C(-12)),
                         "wrist": (Z0, S(SW, 7, -90, -4), C(-10))},
            fan=C(-6))

# mount 3 s : repos relevé, pointes hautes, respiration ample
MT = 3.0
mount = anim("mount", MT, {"shoulder": (C(8), S(MT, 2.5, 0, 6), S(MT, 3.5, 0, 16)),
                           "elbow": (Z0, S(MT, 1.5, -40, -4), S(MT, 2, -40, 6)),
                           "wrist": (Z0, C(2), S(MT, 2, -70, 12))},
             fan=C(2))

# attack et hurt : une fois par-dessus l'état, dernière image neutre, seuls les groupes concernés
IMPULSE = {"shoulder", "elbow", "wrist", "p"}
AT = 0.8
atk = lambda t: bump(t, 0.0, 0.12, 0.28, 0.70)
attack = anim("attack", AT, {"shoulder": (lambda t: 22 * atk(t), lambda t: -12 * atk(t), lambda t: 18 * atk(t)),
                             "elbow": (Z0, lambda t: -6 * atk(t), lambda t: 5 * atk(t)),
                             "wrist": (Z0, lambda t: -6 * atk(t), lambda t: 5 * atk(t))},
              fan=lambda t: 10 * atk(t), n_kf=16, loop="once", only=IMPULSE)

HU = 0.8
hu = lambda t: bump(t, 0.0, 0.08, 0.22, 0.70)
tr = lambda t: 4 * math.sin(TAU * t * 6 / HU) * (1 - sm(t, 0.25, 0.7))
hurt = anim("hurt", HU, {"shoulder": (lambda t: 6 * hu(t), lambda t: 16 * hu(t), lambda t: 8 * hu(t) + tr(t)),
                         "elbow": (Z0, lambda t: -6 * hu(t), lambda t: -3 * hu(t) + tr(t)),
                         "wrist": (Z0, lambda t: 8 * hu(t), lambda t: -3 * hu(t) + tr(t))},
            fan=lambda t: -6 * hu(t), n_kf=24, loop="once", only=IMPULSE)



# Apparition et retrait (guide 6.4), recette ailes_berenice adaptée : rotations et positions s'AJOUTENT à l'état, échelles se
# MULTIPLIENT. Pas de sac : les ailes sortent du haut du dos, repliées et minuscules, gonflent comme une guimauve (« plop » :
# 1,15 → 0,93 → 1), puis s'ouvrent comme un étirement, un peu au-delà de la pose, et s'y posent.
def event_anim(name, L, k_scale, k_fold, k_fan, k_root, sons=()):
    n = int(round(L * 15))
    times = [round(i * L / n, 3) for i in range(n + 1)]
    A = {}

    def put(g, kfs):
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}

    def lag(f, d):
        return lambda t: f(max(0.0, t - d))

    fold = {"shoulder": (0, 40, -20), "elbow": (0, -30, 6), "wrist": (0, 36, -14)}   # pli en Z serré, pointes vers le bas
    for s_, tag in ((-1, "l"), (1, "r")):
        for i, seg in enumerate(SEG):
            fx, fy, fz = fold[seg]
            kfo = lag(k_fold, 0.1 * i)
            ks = [kf("rotation", t, *mirror(s_, fx * kfo(t), fy * kfo(t), fz * kfo(t))) for t in times]
            if seg == "shoulder":
                ks += [kf("scale", t, k_scale(t), k_scale(t), k_scale(t)) for t in times]
                ks += [kf("position", t, 0, 0, -1.5 * k_fold(t)) for t in times]   # sortie du dos (sens z supposé, à voir en jeu)
            put(f"{seg}_{tag}", ks)
        put(f"wingroot_{tag}", [kf("scale", t, k_root(t), k_root(t), k_root(t)) for t in times])
        for k in range(5):
            w = 0.4 + 0.6 * (k + 0.5) / 5
            put(f"p{k}_{tag}", [kf("rotation", t, *mirror(s_, 0, 0, k_fan(max(0.0, t - 0.03 * k)) * w)) for t in times])
    a = {"uuid": nuid(), "name": name, "loop": "once", "override": False, "length": L, "snapping": 24, "selected": False, "animators": A}
    if sons:
        a["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes":
                                     [{"channel": "sound", "data_points": [{"effect": e, "file": ""}], "time": t} for t, e in sons]}
    return a


EQ = 1.6
eq_scale = lambda t: 0.03 + 1.12 * sm(t, 0.0, 0.42) - 0.22 * sm(t, 0.42, 0.58) + 0.07 * sm(t, 0.58, 0.75)
eq_fold = lambda t: 1 - sm(t, 0.55, 1.2) - 0.18 * bump(t, 1.0, 1.15, 1.25, 1.55)
eq_fan = lambda t: 14 * bump(t, 1.0, 1.15, 1.25, 1.55) - 10 * (1 - sm(t, 0.5, 1.1))
equip = event_anim("event_equip", EQ, eq_scale, eq_fold, eq_fan, lambda t: 0.3 + 0.7 * sm(t, 0.0, 0.4),
                   sons=((0.42, "entity.chicken.egg"),))
# retrait 1,6 s : petite inspiration (×1,1), l'aile se replie en cascade, puis rentre dans le dos en rapetissant ; dernière image à 0.
UQ = 1.6
unequip = event_anim("event_unequip", UQ, lambda t: 1 + 0.1 * bump(t, 0.0, 0.25, 0.35, 0.7) - sm(t, 0.7, 1.5),
                     lambda t: sm(t, 0.15, 0.9), lambda t: -10 * sm(t, 0.1, 0.6), lambda t: 1 - sm(t, 1.0, 1.5))

ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, attack, hurt, equip, unequip]
assert len(ANIMS) <= 16
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner,
         "textures": textures, "animations": ANIMS}
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model)          # un son au plus, à l'apparition ; aucun en mouvement
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))
with open(OUT) as fh:
    json.load(fh)


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", depth(outliner[0]), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko")
