"""Ailes Nuage Guimauve — petites ailes rondes et dodues de chérubin-guimauve (crème, rose, lavande). Design original.
Ensemble « Nuage Guimauve » (pièce sœur : oreilles_lapin_nuage, dont on reprend la palette).
Écrit ailes_nuage_guimauve.png, ailes_nuage_guimauve_e.png et .build/ailes_nuage_guimauve_brut.bbmodel à côté de ce script.

Recette Aurelion (validée en jeu) adaptée à une petite aile : chaque plume = PEAU (plaque fine, contour en goutte
découpé par alpha 0/255, tranches transparentes) autour d'une ÂME (cubes pleins plus étroits, invisibles de face).
Texture de plume : base en HAUT, bout rond en BAS, côté extérieur de l'aile à DROITE.
Rangées, du dos vers l'avant : scapulaires et petites couvertures rose pâle, moyennes crème à liseré rose, grandes
crème-blanc rosé, rémiges (secondaires blanc rosé, primaires courtes à bout lavande), sous-alaires lavande pâle.
Calque _e : fond très sombre, fin liseré lavande au bout des primaires, rien d'autre.
"""
import base64, io, json, math, os, re, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "ailes_nuage_guimauve"
AVEC_E = True       # correctif du clignotement annoncé côté mod le 2026-11-03 : à vérifier en jeu
TEX = 512
V0, DV = 26, 5      # frétillement à la fusée (glide) : recette validée d'Aurelion
SS = 4
tex = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))


# ------------------------------------------------------------------ textures
def lerp(a, b, k):
    return a + (b - a) * k


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


# palette « Nuage Guimauve » (oreilles_lapin_nuage) : bases poussées vers le blanc, ombres froides contre le saumon de nuit
CREME = (255, 249, 247)
OMB = (214, 202, 232)            # ombre de recouvrement : lavande grisée
OMB_D = (190, 176, 220)
ROSE_L = (255, 214, 230)
ROSE_D = (240, 168, 200)
LAV = (206, 190, 248)
LAV_D = (168, 146, 228)
LAV_LIS = (146, 124, 206)
LAV_HI = (238, 232, 255)
E_FOND = (13, 10, 18)
E_LAV = (112, 96, 170)

PAL = {
    # racine, milieu, bout, liseré, ombre, couleur de bout
    "p": ((246, 238, 248), (255, 250, 252), (250, 244, 255), LAV_LIS, OMB_D, LAV),
    "s": ((250, 236, 242), (255, 244, 248), (255, 240, 246), (232, 184, 210), OMB, (246, 222, 240)),
    "g": ((255, 246, 244), CREME, (255, 252, 250), (246, 190, 214), OMB, (255, 236, 242)),
    "m": ((255, 244, 244), (255, 250, 249), (255, 246, 248), ROSE_D, OMB, ROSE_L),
    "l": ((255, 222, 236), (255, 230, 240), ROSE_L, (232, 150, 190), (220, 186, 214), (255, 206, 226)),
    "u": ((232, 226, 252), LAV_HI, (244, 240, 255), LAV_D, OMB_D, (226, 216, 254)),
}
TIPK = {"p": 0.62, "s": 0.78, "g": 0.80, "m": 0.70, "l": 0.70, "u": 0.82}   # début de la couleur de bout
RIMK = {"p": 0.72, "s": 0.50, "g": 0.42, "m": 0.55, "l": 0.50, "u": 0.50}   # force du liseré : seul le bout des primaires est franc
SHL = {"p": 0.42, "s": 0.46, "g": 0.40, "m": 0.36, "l": 0.22, "u": 0.36}    # longueur de l'ombre de recouvrement


def paint(W, H, kind, seed):
    """Plume en goutte : base étroite arrondie, ventre large, bout en demi-ellipse. Renvoie (RGBA, calque e RGB, masque)."""
    rng = np.random.default_rng(seed)
    root, mid, tip, rim, shadow, tipc = (np.array(c, np.float32) for c in PAL[kind])
    jitter = rng.uniform(0.985, 1.01)
    w, h = W * SS, H * SS
    x, y = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    t = y
    hw = 0.47
    ry = min(0.48, hw * W / H * 1.15)                      # bout : demi-ellipse un peu allongée, jamais pointue
    te = 1 - ry
    rb = min(0.2, hw * W / H * 0.55)                       # base arrondie aussi : aucun coin
    grow = 0.46 + 0.54 * np.sin(np.pi / 2 * np.clip(t / te, 0, 1)) ** 0.7
    tipcap = np.where(t > te, np.sqrt(np.clip(1 - ((t - te) / ry) ** 2, 0, 1)), 1.0)
    basecap = np.where(t < rb, np.sqrt(np.clip(1 - ((rb - t) / rb) ** 2, 0, 1)) * 0.6 + 0.4, 1.0)
    env = grow * tipcap * basecap
    cx = 0.5 + 0.03 * (t * t - 0.3)
    d = x - cx
    lim = hw * env
    r = np.abs(d) / np.maximum(lim, 1e-4)
    alpha = (r < 1) * 255.0

    k1 = smooth(t / 0.5)[..., None]
    k2 = smooth((t - 0.5) / 0.5)[..., None]
    col = lerp(lerp(root, mid, k1), tip, k2) * jitter
    col = col * (1.03 - 0.12 * (r ** 2))[..., None]                      # bombé
    gk = smooth((t - TIPK[kind]) / max(1e-3, 1 - TIPK[kind]))[..., None]
    col = lerp(col, tipc, gk * 0.9)                                        # bout coloré
    blob = np.exp(-(((d + 0.10) / 0.16) ** 2 + ((t - 0.55) / 0.16) ** 2))[..., None]
    col = lerp(col, np.array((255, 255, 255), np.float32), blob * 0.45)    # reflet guimauve
    shd = (np.clip(1 - t / SHL[kind], 0, 1) ** 1.3)[..., None]
    col = lerp(col, shadow, shd * 0.75)                                    # ombre de recouvrement
    side = (np.clip((r - 0.5) / 0.5, 0, 1) * (d < 0))[..., None]
    col = lerp(col, shadow, side * 0.30)                                   # bord intérieur recouvert par la voisine
    dist = (1 - r) * lim * W
    rk = (np.clip(1 - dist / 3.5, 0, 1) * (t > 0.14))[..., None]
    col = lerp(col, rim, rk * RIMK[kind])                                        # liseré de 3–4 texels
    if kind in "ps":
        ra = (np.clip(1 - np.abs(d) * W / 1.6, 0, 1) * (t > 0.1) * (t < 0.70))[..., None]
        col = lerp(col, np.array((236, 222, 246), np.float32), ra * 0.55)  # rachis discret

    # calque e : fond additif très sombre ; primaires : fin liseré lavande au bout seulement
    ec = np.empty(col.shape, np.float32)
    ec[...] = np.array(E_FOND, np.float32)
    if kind == "p":
        tipline = (np.clip(1 - dist / 3.2, 0, 1) * smooth((t - 0.70) / 0.12))[..., None]
        ec = lerp(ec, np.array(E_LAV, np.float32), tipline)
    e_img = np.array(Image.fromarray(np.clip(ec, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))

    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    a = np.array(Image.fromarray(alpha.astype(np.uint8), "L").resize((W, H), Image.LANCZOS))
    solid = a > 110
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = rgb
    if solid.any():
        arr[~solid, :3] = rgb[solid].mean(axis=0).astype(np.uint8)
    arr[..., 3] = solid * 255
    return Image.fromarray(arr, "RGBA"), e_img, solid


def edge_strip(kind, W=6, H=32):
    """Bande opaque des âmes : suit le dégradé de la plume, teintée par le liseré pour dessiner le bord."""
    root, mid, tip, rim, shadow, tipc = (np.array(c, np.float32) for c in PAL[kind])
    a = np.zeros((H, W, 4), np.float32)
    for yy in range(H):
        t = (yy + 0.5) / H
        c = lerp(root, mid, min(1, t * 2)) if t < 0.5 else lerp(mid, tip, (t - 0.5) * 2)
        c = lerp(c, tipc, float(smooth((t - TIPK[kind]) / (1 - TIPK[kind]))) * 0.9)
        a[yy, :, :3] = lerp(c, rim, 0.30)
    a[..., 3] = 255
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def solid_tile(W, H, top, bot):
    a = np.zeros((H, W, 4), np.float32)
    top, bot = np.array(top, np.float32), np.array(bot, np.float32)
    for yy in range(H):
        a[yy, :, :3] = lerp(top, bot, yy / max(1, H - 1))
    a[..., 3] = 255
    return Image.fromarray(a.astype(np.uint8), "RGBA")


UV = {}
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


# environ 10 texels par pixel ; image au rapport de la plume pour que le bout reste rond
seed = 1
EIMG = {}
for name, kind, W, H in ([(f"p{i}", "p", 40, 88) for i in range(3)] + [(f"p{i}", "p", 40, 56) for i in (3, 4)]
                         + [(f"s{i}", "s", 38, 88) for i in range(4)] + [(f"g{i}", "g", 36, 52) for i in range(3)]
                         + [(f"u{i}", "u", 36, 52) for i in range(3)] + [(f"m{i}", "m", 32, 36) for i in range(3)]
                         + [(f"l{i}", "l", 28, 28) for i in range(4)]):
    im, ea, mask = paint(W, H, kind, seed)
    place(name, im)
    EIMG[name] = (ea, mask)
    seed += 1
for kind in PAL:
    place(f"edge_{kind}", edge_strip(kind))
place("bone", solid_tile(16, 16, (255, 236, 244), (232, 214, 238)))
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
for name in [f"edge_{k}" for k in PAL] + ["bone"]:
    u0, v0, u1, v1 = UV[name]
    _e[v0:v1, u0:u1] = (*E_FOND, 255)
assert _e[..., :3].max() <= 180, "calque trop vif"
assert set(np.unique(_e[..., 3])) <= {0, 255}
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


def cube(name, frm, to, origin, rot=(0, 0, 0), faces=None):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(v, 2) for v in frm], "to": [round(v, 2) for v in to],
         "origin": [round(v, 2) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(v, 1) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(rot):
        e["rotation"] = [round(v, 1) for v in rot]
    elements.append(e)
    return e["uuid"]


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups
    groups[name] = {"origin": [round(v, 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(v, 2) for v in rotation]}
    return name


Z = 3.9          # plan médian de l'aile (dos du joueur à z = 2)
ROLL = 4.0       # roulis : chaque plume passe sur sa voisine extérieure
SKIN = 0.3
EMBED = 0.12


def stack(z0, z1, t0, t1):
    return (lambda a, L: lerp(z0, z1, a / L)), (lambda a, L: lerp(t0, t1, a / L))


def remex(bend):
    return stack(0.45, -bend, 1.15, 0.64)


# profondeurs d'Aurelion réduites d'un tiers : petite aile, mais dodue près du bras
STACK = {"g": stack(1.15, 0.75, 0.9, 0.62), "m": stack(1.80, 1.30, 0.8, 0.62), "l": stack(2.40, 1.85, 0.7, 0.62),
         "u": stack(-0.45, -0.30, 0.9, 0.62), "um": stack(-1.10, -0.75, 0.8, 0.62), "sc": stack(3.0, 2.45, 0.7, 0.62),
         "rd": stack(0.95, 2.05, 0.62, 0.62), "rv": stack(0.75, -1.25, 0.62, 0.62), "bk": stack(1.1, -0.9, 0.62, 0.62)}


def feather(name, s, ax, ay, L, w, tilt, uv, parent, prof, side="both", ncore=2, own_bone=False, zb=None):
    """Plume peau + âme (recette Aurelion). tilt > 0 : le bout part vers l'extérieur."""
    kind = re.match(r"[a-z]+", uv).group()
    zc, thick = prof
    zb = Z if zb is None else zb
    bx = s * ax
    tgt = group(name, [bx, ay, zb + zc(0, L)], parent=parent) if own_bone else parent
    u0, v0, u1, v1 = UV[uv]
    south = [u0, v0, u1, v1] if s > 0 else [u1, v0, u0, v1]
    north = [south[2], v0, south[0], v1]
    rz = s * tilt
    sn, cs = math.sin(math.radians(tilt)), math.cos(math.radians(tilt))
    zd = lambda a: zb + zc(a, L) + thick(a, L) / 2
    zv = lambda a: zb + zc(a, L) - thick(a, L) / 2

    def skin(tag, z0, z1, faces_s, faces_n, inward):
        pitch = math.degrees(math.atan2(z0 - z1, L))
        a, b = sorted((z0, z0 + inward * SKIN))
        faces = {"south": faces_s, "north": faces_n, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
        groups[tgt]["ids"].append(cube(f"{name}.{tag}", [bx - w / 2, ay - L, a], [bx + w / 2, ay + 0.4, b], [bx, ay, z0],
                                       rot=(pitch, -s * ROLL, rz), faces=faces))

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
        wc = w * 0.52 * k
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
                                       [x, y, z], rot=(pitch, -s * ROLL, rz), faces=faces))
    return bx + s * sn * L, ay - cs * L, zb + zc(L, L)


# bras court et arqué : épaule basse près de la colonne, sommet vers y = 28,5, main courte
ARM = [(2.6, 23.0), (5.2, 26.6), (8.4, 28.5), (10.8, 28.1)]
YAW = [14, -6, 6]
SEG = ["shoulder", "elbow", "wrist"]


def pos(i, f):
    return lerp(ARM[i][0], ARM[i + 1][0], f), lerp(ARM[i][1], ARM[i + 1][1], f)


def tilt_at(i, f):
    if i == 0:
        return 0 + 3 * f
    if i == 1:
        return 3 + 11 * f
    return 15 + 58 * f ** 1.1


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


def arch(u):
    d = u * _ls[-1]
    for n in range(len(SMOOTH) - 1):
        if d <= _ls[n + 1]:
            k = (d - _ls[n]) / max(1e-6, _ls[n + 1] - _ls[n])
            return lerp(SMOOTH[n][0], SMOOTH[n + 1][0], k), lerp(SMOOTH[n][1], SMOOTH[n + 1][1], k)
    return SMOOTH[-1]


def build(s):
    tag = "l" if s < 0 else "r"
    segs = []
    for i in range(3):
        segs.append(group(f"{SEG[i]}_{tag}", [s * ARM[i][0], ARM[i][1], Z], parent=segs[i - 1] if i else None,
                          rotation=(0, -s * YAW[i], 0)))
    # noyau : section octogonale (deux cubes à 45°), sous les couvertures
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
    # attache contre le dos, groupe fixe, couverte par les scapulaires
    a, b = sorted([s * 1.2, s * 2.9])
    wr = group(f"wingroot_{tag}", [s * 2.6, 23.0, Z])
    groups[wr]["ids"].append(cube(f"root_{tag}", [a, 22.5, 2.15], [b, 24.2, Z + 0.9], [s * 2.6, 23.0, Z], faces=bone_faces))

    # primaires (main) : 5, courtes et rondes, os propres, éventail ; les extérieures raccourcissent : bout de l'aile rond
    NP = 5
    for k in range(NP):
        f = (k + 0.5) / NP
        ax, ay = pos(2, f)
        L = 8.6 - 3.8 * f ** 1.4 + (0.3 if k % 2 else 0)
        feather(f"p{k}_{tag}", s, ax, ay - 0.3, L, 3.9 - 0.3 * f, tilt_at(2, f), f"p{k}", segs[2], remex(0.6), ncore=2, own_bone=True)
    # secondaires (avant-bras) : 4, bord de fuite en festons
    NS = 4
    for k in range(NS):
        f = (k + 0.5) / NS
        ax, ay = pos(1, f)
        L = 8.4 + 0.5 * f + (0.6 if k % 2 else 0)
        feather(f"s{k}_{tag}", s, ax, ay - 0.3, L, 3.8, tilt_at(1, f), f"s{k % 4}", segs[1], remex(0.35), ncore=2, own_bone=True)
    # tertiaires (humérus) : 2
    for k in range(2):
        f = (k + 0.55) / 2
        ax, ay = pos(0, f)
        feather(f"t{k}_{tag}", s, ax, ay - 0.3, 6.6 + 1.0 * k, 3.8, tilt_at(0, f), f"s{(k + 1) % 4}", segs[0], remex(0.2), ncore=2)

    def row(prefix, n, L0, L1, w, lift, prof, kind, nv, side, phase=0.0, span=(0.03, 0.97), tilt_k=0.9, ncore=1):
        lens = [math.dist(ARM[i], ARM[i + 1]) for i in range(3)]
        tot = sum(lens)
        for k in range(n):
            u = lerp(span[0], span[1], (k + 0.5) / n)
            dd = u * tot
            i = 0
            while i < 2 and dd > lens[i]:
                dd -= lens[i]
                i += 1
            f = min(1.0, dd / lens[i])
            ax, ay = arch(u)
            vary = 1 + 0.06 * math.sin(k * 2.4 + phase)
            feather(f"{prefix}{k}_{tag}", s, ax, ay + lift(i, f), lerp(L0, L1, u) * vary, w, tilt_at(i, f) * tilt_k,
                    f"{kind}{k % nv}", segs[i], prof, side=side, ncore=ncore)

    # côté dos : grandes (crème), moyennes (liseré rose), petites (rose pâle)
    row("gc", 7, 5.0, 4.6, 3.5, lambda i, f: -0.15, STACK["g"], "g", 3, "d", 0.0)
    row("mc", 7, 3.5, 3.2, 3.1, lambda i, f: 0.35, STACK["m"], "m", 3, "d", 1.3)
    row("lc", 8, 2.6, 2.4, 2.7, lambda i, f: core_radius(i, f) + 0.35, STACK["l"], "l", 4, "d", 2.6, tilt_k=0.6, ncore=0)
    # côté face : sous-alaires lavande pâle, deux rangées
    row("uc", 6, 5.0, 4.6, 3.5, lambda i, f: -0.1, STACK["u"], "u", 3, "v", 0.7)
    row("um", 7, 3.2, 3.0, 3.0, lambda i, f: core_radius(i, f) * 0.9, STACK["um"], "m", 3, "v", 2.0, span=(0.14, 0.97), ncore=0)
    # crête du bord d'attaque : bourrelet rond, le noyau ne se voit ni de dessus ni de dessous
    ridge = lambda i, f: core_radius(i, f) * 0.56 + 0.55
    row("rd", 8, 2.6, 2.3, 2.7, ridge, STACK["rd"], "l", 4, "d", 0.4, tilt_k=0.5, ncore=0)
    row("rv", 8, 2.6, 2.3, 2.7, ridge, STACK["rv"], "l", 4, "v", 1.9, tilt_k=0.5, ncore=0)
    # attache au dos : écailles rondes côté face, scapulaires côté dos qui couvrent la racine
    for k in range(2):
        feather(f"bk{k}_{tag}", s, 2.1 + 1.1 * k, 24.8 + 0.4 * k, 3.2, 2.8, 3 + 6 * k, f"l{(k + 2) % 4}", segs[0], STACK["bk"], side="v", ncore=0)
    for k in range(3):
        feather(f"sc{k}_{tag}", s, 2.15 + 1.1 * k, 25.0 + 0.7 * k, 4.2 - 0.3 * k, 2.9, 2 + 7 * k, f"l{k}", segs[0], STACK["sc"], side="d", ncore=1)
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

# idle 8 s : respiration (4 s) + petit frétillement (5 Hz, 4,9–6,3 s) : trois battements courts, ailes un peu ouvertes
fr = lambda t: bump(t, 4.9, 5.1, 6.0, 6.3)
wig = lambda amp, ph=0: (lambda t: amp * fr(t) * math.sin(TAU * 5 * (t - 4.9) + math.radians(ph)))
idle = anim("idle", 8.0, {
    "shoulder": (add(S(4, 1.0, 0, 4), lambda t: 6 * fr(t)), add(S(4, 1.5, 0, 10), lambda t: -6 * fr(t)), add(S(4, 2, 0, 4), wig(11))),
    "elbow":    (Z0, S(4, 1, -40, -4), add(S(4, 1.5, -40, -1), wig(5, -50))),
    "wrist":    (Z0, S(4, 0.8, -70, 4), add(S(4, 1, -70, -4), wig(6, -90)))},
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

# sneak 3 s : repliées serrées dans le dos, pointes qui remontent
SN = 3.0
sneak = anim("sneak", SN, {"shoulder": (C(4), S(SN, 1, 0, 50), S(SN, 1, 0, 8)),
                           "elbow": (Z0, C(-30), S(SN, 1, -40, 6)),
                           "wrist": (Z0, C(34), C(12))},
             fan=C(-8))

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

ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, attack, hurt]
assert len(ANIMS) <= 16
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner,
         "textures": textures, "animations": ANIMS}
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
