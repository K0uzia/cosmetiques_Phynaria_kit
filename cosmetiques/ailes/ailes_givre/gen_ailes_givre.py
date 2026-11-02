"""Ailes de givre — ailes de longs cristaux de glace (bleu nuit, cyan, blanc givré), sur un squelette d'os de givre clair. Design original.
Écrit ailes_givre.png, ailes_givre_e.png et .build/ailes_givre_brut.bbmodel à côté de ce script.

Structure et orientations reprises de gen_ailes_abyssales.py : humérus > avant-bras > poignet, éventail qui rayonne du poignet.
Un cristal = peau + âme : un cube fin dont seules les faces nord et sud sont peintes (contour anguleux découpé par alpha 0/255,
tranches transparentes) et, dedans, des tronçons pleins plus étroits, invisibles de face, qui remplissent l'épaisseur.
Pas de semi-transparence : la translucidité est un motif de pixels pleins et vides sur les flancs, hors de l'âme ;
les reflets internes sont peints (facettes en chevrons, éclats, fissures). La pose neutre (fold = 0) est l'aile ouverte.
"""
import base64, io, json, math, os, re, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = False      # True : embarque ailes_givre_e.png en seconde texture. False tant que le bug du mod n'est pas corrigé.
TEX = 512
V0, DV = 26, 5      # battement à la fusée (glide) : constantes validées en jeu sur Aurelion et les ailes abyssales
TAU = 2 * math.pi
NOM = "ailes_givre"


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ squelette et cristaux (aile droite, x > 0)
Z = 5.2                                 # plan de l'aile (dos du joueur à z = 2)
S_, E_, W_ = (5.4, 23.0), (9.5, 31.5), (19.0, 39.0)
YAW = [20, -7, 8]                       # balayage arrière au repos : humérus, avant-bras, main

# Rémiges de la main : angle au poignet, longueur, largeur. Irrégulier exprès : le bord de l'éventail reste dentelé.
PRIM = [(19, 25, 4.8), (3, 31, 5.2), (-11, 24, 4.8), (-26, 32, 5.4), (-41, 26, 5.0), (-56, 30, 5.2), (-71, 23, 4.8)]
# Rangée intermédiaire, derrière : portée par la rémige du dessus, bouche les vides de l'éventail.
MID = [(11, 18.5, 4.6), (-4, 16, 4.6), (-18, 21, 4.8), (-34, 17, 4.6), (-49, 21, 4.8), (-64, 17, 4.6)]
# Secondaires de l'avant-bras : position le long de l'os, angle, longueur, largeur.
SEC = [(0.92, -80, 25, 5.4), (0.72, -85, 21, 5.2), (0.52, -89, 27, 5.6), (0.30, -94, 22, 5.2), (0.10, -99, 25, 5.4)]
# Tertiaires de l'humérus.
TERT = [(0.92, -100, 18, 4.8), (0.58, -104, 13, 4.4)]
FCLOSE = [lerp(52, -14, i / (len(PRIM) - 1)) for i in range(len(PRIM))]      # fermeture à fold = 1 (degrés)
SCLOSE = [-10, -7, -4, -1, 2]


def along(a, b, u):
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u))


def polar(p, ang, r):
    return (p[0] + r * math.cos(math.radians(ang)), p[1] + r * math.sin(math.radians(ang)))


# ------------------------------------------------------------------ peinture d'un cristal
RAMP = np.array([(7, 13, 40), (11, 25, 68), (16, 48, 108), (24, 84, 150), (38, 132, 192), (70, 184, 226), (136, 222, 244), (198, 240, 252), (240, 252, 255)], np.float32)
rng = np.random.default_rng(1207)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16


def ramp(v):
    """Palette par paliers nets : aucune couleur intermédiaire, c'est ce qui fait lire des facettes et pas un dégradé flou."""
    return RAMP[np.clip((v * len(RAMP)).astype(int), 0, len(RAMP) - 1)]


def paint_crystal(W, H, nseg, windows=True):
    """Tuile : u de la base (gauche) à la pointe (droite), b de -1 à +1 en travers. Renvoie rgba, calque _e, âme [(u0, u1, bc, hw)]."""
    ss = 4
    r = rng
    tipb = float(r.uniform(-0.32, 0.32))
    su = float(r.uniform(0.70, 0.80))                         # où commence le biseau de la pointe
    top_u = [0, 0.09, float(r.uniform(0.34, 0.5)), su, float(su + r.uniform(0.09, 0.14)), 1]
    top_b = [0.26, 0.60, float(r.uniform(0.74, 0.86)), float(r.uniform(0.88, 0.98)), float(r.uniform(0.46, 0.62)), tipb]
    bot_u = [0, 0.13, float(r.uniform(0.42, 0.58)), float(su - r.uniform(0.0, 0.06)), float(su + r.uniform(0.06, 0.12)), 1]
    bot_b = [-0.26, -0.66, float(-r.uniform(0.80, 0.98)), float(-r.uniform(0.76, 0.92)), float(-r.uniform(0.36, 0.52)), tipb]
    # abscisses croissantes pour np.interp
    top_u = list(np.maximum.accumulate(top_u)); bot_u = list(np.maximum.accumulate(bot_u))
    yy, xx = np.mgrid[0:H * ss, 0:W * ss]
    u = (xx + 0.5) / (W * ss)
    b = 1 - 2 * (yy + 0.5) / (H * ss)
    top, bot = np.interp(u, top_u, top_b), np.interp(u, bot_u, bot_b)
    mask = (b < top) & (b > bot)
    mid = (top + bot) / 2
    ridge = np.interp(u, [0, 0.35, su, 1], [0.0, float(r.uniform(-0.12, 0.12)), float(r.uniform(-0.1, 0.1)), tipb])
    dtop, dbot = np.clip(top - ridge, 0.01, None), np.clip(ridge - bot, 0.01, None)
    s = np.where(b > ridge, (b - ridge) / dtop, (ridge - b) / dbot)    # 0 sur l'arête, 1 sur le bord
    facet = np.where(b > ridge, np.where(s < 0.52, 0.11, 0.21), np.where(s < 0.58, -0.05, -0.13))
    # le biseau de pointe est une facette de plus, plus claire
    bevel = u > su + 0.04 + 0.08 * s
    facet = facet + bevel * 0.10
    v = 0.04 + 0.88 * u ** 1.15 + facet - 0.10 * s                     # les paliers forment des chevrons
    v = np.where(u < 0.16, v - (0.16 - u) * 1.0, v)                    # ombre de recouvrement à la base
    # éclats internes : polygones francs, un cran plus clairs
    sh = Image.new("L", (W * ss, H * ss), 0)
    dsh = ImageDraw.Draw(sh)
    cr = Image.new("L", (W * ss, H * ss), 0)
    dcr = ImageDraw.Draw(cr)
    for _ in range(int(3 + 4 * W / 340)):
        uc, bc = r.uniform(0.2, 0.86), r.uniform(-0.55, 0.55)
        lu, lb = r.uniform(0.03, 0.10), r.uniform(0.07, 0.17)
        sk = r.uniform(-0.7, 0.7)
        P = [(uc - lu, bc + sk * lb), (uc - lu * 0.2, bc + lb), (uc + lu, bc - sk * lb), (uc + lu * 0.1, bc - lb)]
        dsh.polygon([(a * W * ss, (1 - c) / 2 * H * ss) for a, c in P], fill=255)
    for _ in range(2):                                                 # fissures sombres anguleuses
        uc, bc = r.uniform(0.25, 0.7), r.uniform(-0.5, 0.5)
        pts = [(uc, bc)]
        for _k in range(3):
            pts.append((pts[-1][0] + r.uniform(0.03, 0.08), pts[-1][1] + r.uniform(-0.28, 0.28)))
        dcr.line([(a * W * ss, (1 - c) / 2 * H * ss) for a, c in pts], fill=255, width=max(4, ss * 2 - 2))
    v = v + (np.array(sh) > 127) * 0.17 - (np.array(cr) > 127) * 0.17
    col = ramp(v)
    # arêtes : ligne blanche sur l'arête centrale, sur 3 texels au moins
    rw = 3.2 / H * 2 / 2                                                # demi-largeur en unités de b
    ridge_line = (np.abs(b - ridge) < rw) & (u > 0.14)
    col = np.where(ridge_line[..., None], ramp(v + 0.30), col)

    # réduction : pas de filtrage de l'alpha, sinon des pixels semi-transparents
    def down_mask(a):
        return a.reshape(H, ss, W, ss).mean(axis=(1, 3)) > 0.5
    al = down_mask(mask)
    rgb = col[ss // 2::ss, ss // 2::ss].astype(np.float32)          # échantillon central : la palette reste franche
    # liseré de givre : plus clair, net, 3 texels
    er = np.array(Image.fromarray(al.astype(np.uint8) * 255, "L").filter(ImageFilter.MinFilter(5))) > 127
    rim = al & ~er
    rv = np.clip(0.42 + 0.52 * ((np.arange(W) + 0.5) / W) ** 0.9, 0, 1)
    rgb = np.where(rim[..., None], ramp(np.broadcast_to(rv, (H, W))), rgb)

    # âme : tronçons pleins dans le contour
    us = np.linspace(0.04, {1: 0.74, 3: 0.92, 4: 0.94}[nseg], nseg + 1)
    core = []
    for i in range(nseg):
        t = np.linspace(us[i], us[i + 1], 12)
        tt, bb = np.interp(t, top_u, top_b), np.interp(t, bot_u, bot_b)
        hw = float((tt - bb).min() / 2 * 0.48)
        core.append((float(us[i]), float(us[i + 1]), float(((tt + bb) / 2).mean()), hw))

    # translucidité : motif de pixels pleins et vides sur les flancs, hors de l'âme et du liseré
    px_u = (np.arange(W) + 0.5) / W
    px_b = 1 - 2 * (np.arange(H) + 0.5) / H
    PU, PB = np.meshgrid(px_u, px_b)
    if windows:
        inside_core = np.zeros((H, W), bool)
        for u0, u1, bc, hw in core:
            inside_core |= (PU >= u0 - 0.01) & (PU <= u1 + 0.01) & (np.abs(PB - bc) < hw + 0.06)
        er2 = np.array(Image.fromarray(er.astype(np.uint8) * 255, "L").filter(ImageFilter.MinFilter(3))) > 127
        dens = np.clip((PU - 0.18) / 0.20, 0, 1) * np.clip((0.80 - PU) / 0.18, 0, 1) * 0.5
        cell = BAYER[(np.arange(H)[:, None] // 2) % 4, (np.arange(W)[None, :] // 2) % 4]
        holes = (cell < dens) & er2 & ~inside_core
        al = al & ~holes

    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    out[..., 3] = al * 255
    # calque lumineux : la seule arête centrale, très sombre à la base, vive à la pointe
    rl = ridge_line.reshape(H, ss, W, ss).mean(axis=(1, 3)) > 0.4
    rl &= al
    k = np.clip((PU - 0.25) / 0.7, 0, 1)[..., None]
    ec = lerp(np.array((8, 34, 70), np.float32), np.array((150, 226, 255), np.float32), k)
    oe = np.zeros((H, W, 4), np.uint8)
    oe[..., :3] = (ec * rl[..., None]).astype(np.uint8)
    oe[..., 3] = rl * 255
    return out, oe, core


# tuiles : sept longues, quatre moyennes, quatre courtes
TILES = {}
for i in range(7):
    TILES[f"L{i}"] = dict(zip(("im", "e", "core"), paint_crystal(330, 42, 4)))
for i in range(4):
    TILES[f"M{i}"] = dict(zip(("im", "e", "core"), paint_crystal(150, 40, 3)))
for i in range(4):
    TILES[f"S{i}"] = dict(zip(("im", "e", "core"), paint_crystal(84, 30, 1, windows=False)))

# Os de givre : blanc bleuté, ombres bleues franches, filet clair central. u = le long de l'os.
BW, BH = 96, 16
_a = np.zeros((BH, BW, 4), np.uint8)
_bp = np.array([(104, 146, 190), (150, 192, 224), (196, 226, 244), (232, 246, 252)], np.float32)
for yy in range(BH):
    q = abs((yy + 0.5) / BH - 0.5) * 2
    for xx in range(BW):
        u = xx / (BW - 1)
        idx = 3.0 * (1 - q ** 1.1) * (0.82 + 0.18 * (1 if (xx // 7 + yy // 5) % 2 else -1))
        _a[yy, xx, :3] = _bp[int(np.clip(idx, 0, 3))]
_a[..., 3] = 255
bone_tile = _a

# Âme : même dégradé que la peau, vu par la tranche
_c = np.zeros((16, 96, 4), np.uint8)
_uu = (np.arange(96) + 0.5) / 96
_c[..., :3] = ramp(np.broadcast_to(0.10 + 0.62 * _uu ** 1.15, (16, 96)) + 0.08 * (np.arange(16)[:, None] % 8 < 4)).astype(np.uint8)
_c[..., 3] = 255
core_tile = _c

# Flocon-particule : six branches, une seule plaque ; pixels pleins seulement
PT = 48
_fs = PT * 4
_fm = Image.new("L", (_fs, _fs), 0)
_fd = ImageDraw.Draw(_fm)
_fc = Image.new("L", (_fs, _fs), 0)
_fdc = ImageDraw.Draw(_fc)
_o = _fs / 2
for _k in range(6):
    _a0 = math.radians(_k * 60 + 30)
    _dx, _dy = math.cos(_a0), math.sin(_a0)
    _end = (_o + _dx * _fs * 0.47, _o + _dy * _fs * 0.47)
    _fd.line([(_o, _o), _end], fill=255, width=int(_fs * 0.058))
    _fdc.line([(_o, _o), (_o + _dx * _fs * 0.3, _o + _dy * _fs * 0.3)], fill=255, width=int(_fs * 0.024))
    for _rr, _bl in ((0.17, 0.12), (0.31, 0.10)):
        _bx, _by = _o + _dx * _fs * _rr, _o + _dy * _fs * _rr
        for _sg in (-1, 1):
            _a1 = _a0 + _sg * math.radians(58)
            _fd.line([(_bx, _by), (_bx + math.cos(_a1) * _fs * _bl, _by + math.sin(_a1) * _fs * _bl)], fill=255, width=int(_fs * 0.042))
_fd.regular_polygon((_o, _o, _fs * 0.09), 6, fill=255)
_fa = np.array(_fm.resize((PT, PT), Image.LANCZOS)) > 110
_fci = np.array(_fc.resize((PT, PT), Image.LANCZOS)) > 90
flake_tile = np.zeros((PT, PT, 4), np.uint8)
flake_tile[..., :3] = (120, 208, 238)
flake_tile[_fci, :3] = (244, 253, 255)
flake_tile[..., 3] = _fa * 255


# ------------------------------------------------------------------ atlas
FIXED = [(n, t["im"]) for n, t in TILES.items()] + [("bone", bone_tile), ("corestrip", core_tile), ("flake", flake_tile)]
UV = {}
_x, _y, _shelf = 0, 0, 0
for n, im in sorted(FIXED, key=lambda it: -it[1].shape[0]):
    h, w = im.shape[:2]
    if _x + w + 1 > TEX:
        _x, _y, _shelf = 0, _y + _shelf + 1, 0
    UV[n] = (_x, _y, _x + w, _y + h)
    _x += w + 1
    _shelf = max(_shelf, h)
assert _y + _shelf <= TEX - 6, "atlas trop petit"
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
for n, im in FIXED:
    u0, v0, u1, v1 = UV[n]
    tex[v0:v1, u0:u1] = im
    if n in TILES:
        tex_e[v0:v1, u0:u1] = TILES[n]["e"]
_fv = UV["flake"]
tex_e[_fv[1]:_fv[3], _fv[0]:_fv[2], :3] = np.array((110, 190, 230), np.uint8) * _fci[..., None]
tex_e[_fv[1]:_fv[3], _fv[0]:_fv[2], 3] = _fci * 255

CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC
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


USED_Z = []


def free_z(z, th):
    """Profondeur libre : aucune face nord ou sud à moins de 0,03 px d'une autre, sur toute l'aile."""
    while any(abs(z + d - q) < 0.03 for d in (-th / 2, th / 2) for q in USED_Z):
        z += 0.012
    USED_Z.extend((z - th / 2, z + th / 2))
    return z


ZCACHE = {}


def crystal(s, g, name, p, ang, L, wd, z, th, tile):
    """Cristal le long de l'axe local X depuis p. Peau : faces nord et sud découpées. Âme : tronçons pleins, faces du dessus et du dessous seules."""
    key = name.rsplit("_", 1)[0]
    if key not in ZCACHE:
        ZCACHE[key] = free_z(z, th)                           # même profondeur sur les deux ailes
    z = ZCACHE[key]
    x0, y0 = p
    o = [s * x0, y0, z]
    rot = (0, 0, s * ang)
    ids = groups[g]["ids"]
    u0, v0, u1, v1 = UV[tile]
    ua, ub = (u0, u1) if s > 0 else (u1, u0)
    a, b = (x0, x0 + L) if s > 0 else (-x0 - L, -x0)
    faces = {"south": [ua, v0, ub, v1], "north": [ub, v0, ua, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
    ids.append(cube(name, [a, y0 - wd / 2, z - th / 2], [b, y0 + wd / 2, z + th / 2], o, rot=rot, faces=faces))
    cu0, cv0, cu1, cv1 = UV["corestrip"]
    for i, (t0, t1, bc, hw) in enumerate(TILES[tile]["core"]):
        q0, q1 = lerp(cu0, cu1, t0), max(lerp(cu0, cu1, t1), lerp(cu0, cu1, t0) + 2)
        lng = [q0, cv0, q1, cv1] if s > 0 else [q1, cv0, q0, cv1]
        A, B = (x0 + L * t0, x0 + L * t1) if s > 0 else (-x0 - L * t1, -x0 - L * t0)
        yc = y0 + bc * wd / 2
        h = hw * wd / 2
        cf = {"up": lng, "down": lng}      # pas de capuchons : vus par la tranche, ils se lisent comme des blocs
        ids.append(cube(f"{name}k{i}", [A, yc - h, z - th / 2 + 0.03], [B, yc + h, z + th / 2 - 0.03], o, rot=rot, faces=cf))


def bar(s, g, name, x, y, z, L, q, phi, u0, u1, octo=True, ov=0.0):
    """Tronçon d'os le long de l'axe local X : section octogonale (deux cubes à 45°), sinon losange seul."""
    bu0, bv0, bu1, bv1 = UV["bone"]
    ua, ub = lerp(bu0, bu1, u0), max(lerp(bu0, bu1, u1), lerp(bu0, bu1, u0) + 2)
    long_ = [ua, bv0, ub, bv1]
    end = [ua, bv0 + 3, ua + 2, bv1 - 3]
    faces = {"south": long_, "north": long_, "up": long_, "down": long_, "east": end, "west": end}
    a, b = (x - ov, x + L + ov) if s > 0 else (-x - L - ov, -x + ov)
    o = [s * x, y, z]
    gid = groups[g]["ids"]
    if octo:
        gid.append(cube(name, [a, y - q, z - q], [b, y + q, z + q], o, rot=(0, 0, s * phi), faces=faces))
        gid.append(cube(name + "o", [a + 0.03, y - q * 0.97, z - q * 0.97], [b - 0.03, y + q * 0.97, z + q * 0.97], o, rot=(45, 0, s * phi), faces=faces))
    else:
        gid.append(cube(name, [a, y - q, z - q], [b, y + q, z + q], o, rot=(45, 0, s * phi), faces=faces))


def chain(s, g, name, pts, r0, r1, u0=0.0, u1=1.0, z=Z, z1=None):
    """Os effilé : tronçons qui se recouvrent, rayon qui décroît."""
    n = len(pts) - 1
    z1 = z if z1 is None else z1
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        t0, t1 = i / n, (i + 1) / n
        phi = math.degrees(math.atan2(yb - ya, xb - xa))
        bar(s, g, f"{name}{i}", xa, ya, lerp(z, z1, t0), math.dist(pts[i], pts[i + 1]), lerp(r0, r1, (t0 + t1) / 2), phi, lerp(u0, u1, t0), lerp(u0, u1, t1), ov=0.12)


EMITS = []


def emit(parent, at, s):
    EMITS.append(group("emit_givre" + (str(len(EMITS) + 1) if EMITS else ""), [s * at[0], at[1], Z], parent=parent))


SEG = ["shoulder", "elbow", "wrist"]


def build(s):
    tag = "l" if s < 0 else "r"
    pv = [S_, E_, W_]
    segs = []
    for i in range(3):
        segs.append(group(f"{SEG[i]}_{tag}", [s * pv[i][0], pv[i][1], Z], parent=segs[i - 1] if i else None, rotation=(0, -s * YAW[i], 0)))
    sh, el, wr = segs
    # racine : sort du dos, sans pièce dorsale ; trois petits cristaux
    rt = group(f"wingroot_{tag}", [s * S_[0], S_[1], Z])
    chain(s, rt, f"root_{tag}", [(1.6, 21.4), (3.4, 21.9), S_], 0.8, 1.0, 0.0, 0.1, z=3.4, z1=Z)
    crystal(s, rt, f"rc0_{tag}", (2.6, 22.4), 74, 7.0, 2.4, 4.3, 0.5, "S0")
    crystal(s, rt, f"rc1_{tag}", (3.2, 22.3), 38, 5.0, 2.0, 4.9, 0.5, "S1")
    crystal(s, rt, f"rc2_{tag}", (3.0, 21.6), -24, 4.2, 1.9, 4.6, 0.5, "S2")

    # os
    chain(s, sh, f"hum_{tag}", [S_, along(S_, E_, 0.5), E_], 1.05, 0.95, 0.05, 0.3)
    chain(s, el, f"avb_{tag}", [E_, along(E_, W_, 0.33), along(E_, W_, 0.66), W_], 1.05, 0.72, 0.3, 0.55)
    bar(s, el, f"coude_{tag}", E_[0] - 0.7, E_[1] - 0.45, Z, 1.6, 1.15, 38, 0.2, 0.3)
    bar(s, wr, f"nodw_{tag}", W_[0] - 0.8, W_[1] - 0.2, Z, 1.8, 0.98, 14, 0.5, 0.6)

    # éperons : cristal du poignet, pièce maîtresse de la silhouette, et petit éclat du coude
    th = group(f"thumb_{tag}", [s * W_[0], W_[1], Z], parent=wr)
    chain(s, th, f"thb_{tag}", [W_, polar(W_, 76, 2.6)], 0.7, 0.5, 0.5, 0.65)
    crystal(s, th, f"spk0_{tag}", polar(W_, 76, 1.6), 78, 10.5, 2.8, Z + 0.1, 0.6, "M0")
    crystal(s, th, f"spk1_{tag}", polar(W_, 62, 1.0), 104, 6.5, 2.2, Z - 0.5, 0.5, "S3")
    crystal(s, el, f"spur_{tag}", (E_[0] + 0.1, E_[1] + 0.2), 116, 5.2, 2.2, Z - 0.2, 0.5, "S1")

    # éventail de la main : une rémige par groupe, escalier de profondeur, chaque rémige recouvre la suivante
    for k, (a, L, wd) in enumerate(PRIM):
        g = group(f"c{k + 1}_{tag}", [s * W_[0], W_[1], Z], parent=wr)
        crystal(s, g, f"p{k}_{tag}", polar(W_, a, 0.4), a, L, wd, Z - 0.75 + 0.25 * k, 0.66, f"L{k % 7}")
        if k < len(MID):
            ma, mL, mw = MID[k]
            crystal(s, g, f"q{k}_{tag}", polar(W_, ma, 0.4), ma, mL, mw, Z - 1.65 + 0.11 * k, 0.6, f"M{k % 4}")
        # couverts dessus et dessous : petits cristaux qui cachent la racine
        crystal(s, g, f"cb{k}_{tag}", polar(W_, a + 4, 1.4), a + 4, 11.0 - (k % 2) * 2.2, 3.8, Z + 1.55 + 0.09 * k, 0.5, f"S{k % 4}")
        crystal(s, g, f"cf{k}_{tag}", polar(W_, a - 4, 1.4), a - 4, 10.0 - (k % 2) * 1.8, 3.6, Z - 2.35 - 0.09 * k, 0.5, f"S{(k + 2) % 4}")

    # secondaires
    for k, (u, a, L, wd) in enumerate(SEC):
        p = along(E_, W_, u)
        g = group(f"s{k + 1}_{tag}", [s * p[0], p[1], Z], parent=el)
        crystal(s, g, f"sc{k}_{tag}", p, a, L, wd, Z - 0.58 - 0.17 * k + 0.68, 0.6, f"L{(k + 3) % 7}" if L > 23 else f"M{k % 4}")
        crystal(s, g, f"sb{k}_{tag}", along(E_, W_, u - 0.04), a + 5, 9.5 - (k % 2) * 2, 3.6, Z + 1.45 - 0.08 * k, 0.5, f"S{(k + 1) % 4}")
        crystal(s, g, f"sf{k}_{tag}", along(E_, W_, u + 0.04), a - 5, 8.5 - (k % 2) * 1.6, 3.4, Z - 1.5 - 0.08 * k, 0.5, f"S{(k + 3) % 4}")

    # tertiaires et scapulaires, fixés à l'humérus
    for k, (u, a, L, wd) in enumerate(TERT):
        crystal(s, sh, f"t{k}_{tag}", along(S_, E_, u), a, L, wd, Z - 0.96 - 0.2 * k, 0.7, f"M{(k + 1) % 4}")
    crystal(s, sh, f"sca0_{tag}", along(S_, E_, 0.42), -96, 7.8, 3.2, Z + 1.0, 0.5, "S2")
    crystal(s, sh, f"sca1_{tag}", along(S_, E_, 0.78), -103, 9.0, 3.4, Z - 1.85, 0.5, "S0")

    # points de départ des flocons : pointe des cristaux
    emit(f"c2_{tag}", polar(W_, PRIM[1][0], PRIM[1][1]), s)
    emit(f"c4_{tag}", polar(W_, PRIM[3][0], PRIM[3][1]), s)
    emit(f"c6_{tag}", polar(W_, PRIM[5][0], PRIM[5][1]), s)
    u, a, L, _w = SEC[2]
    emit(f"s3_{tag}", polar(along(E_, W_, u), a, L), s)
    return rt, sh


(LR_, L_), (RR_, Rr_) = build(-1), build(1)

# Particule (guide, section 5 ter) : une seule plaque, face up seule, à 0,3 px au-dessus du pivot, image de flocon.
PL = group("particle_givre", [0, 0, 0])
PW, PTH, PY = 3.4, 0.3, 0.3
pu0, pv0, pu1, pv1 = UV["flake"]
groups[PL]["ids"].append(cube("flocon", [-PW / 2, PY, -PW / 2], [PW / 2, PY + PTH, PW / 2], [0, 0, 0], faces={"up": [pu0, pv0, pu1, pv1]}))


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(),
             "children": [{"name": "item", "origin": [0, 0, 0], "uuid": nuid(),
                           "children": [bone(LR_), bone(RR_), bone(L_), bone(Rr_)]}]},
            bone(PL)]

# ------------------------------------------------------------------ animations
# Mêmes intentions et mêmes axes que les ailes abyssales (orientations validées en jeu) :
#   fx > 0 : le plan bascule vers l'horizontale ; fy > 0 : pivote vers l'arrière ; fz > 0 : la pointe monte.
#   fold : 0 = éventail ouvert (pose du modèle), 1 = éventail fermé.
# Mouvement raide : pas de phalange qui se creuse, retards très courts, courbes à plateaux (snap) : de brefs à-coups entre des arrêts.

# MIROIR D'AXES : seul endroit à toucher si la convention du mod change (un signe suffit).
SX, SY, SZ = -1, -1, +1


def mirror(s, fx, fy, fz):
    """s = -1 aile gauche, +1 aile droite. Renvoie les valeurs de keyframe."""
    return SX * fx, s * SY * fy, s * SZ * fz


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 2)), "y": str(round(y + 0.0, 2)), "z": str(round(z + 0.0, 2))}],
            "time": round(t, 3), "interpolation": "linear"}


def snapv(x, k=2.4):
    """x dans -1..1 -> même plage, mais à plateaux."""
    return math.tanh(k * x) / math.tanh(k)


def S(T, amp, ph=0.0, off=0.0, k=2.4):
    return lambda t: off + amp * snapv(math.sin(TAU * t / T + math.radians(ph)), k)


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


def anim(name, length, segs, fold, n_kf=None, loop="loop", only=None):
    """segs : shoulder/elbow/wrist -> (fx, fy, fz). only : familles animées (attaque et blessé, joués une fois par-dessus l'état)."""
    A = {}

    def put(g, kfs):
        if only is None or re.sub(r"\d*_[lr]$", "", g) in only:
            A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}

    n = n_kf or max(10, int(round(length * 12)))
    times = [i * length / n for i in range(n + 1)]   # interpolation linéaire : dernier keyframe = premier
    NP = len(PRIM)
    for s, tag in ((-1, "l"), (1, "r")):
        for seg, (fx, fy, fz) in segs.items():
            put(f"{seg}_{tag}", [kf("rotation", t, *mirror(s, fx(t), fy(t), fz(t))) for t in times])
        for k in range(NP):
            dl = 0.012 * length * (NP - 1 - k)      # léger décalage : les lames claquent l'une après l'autre
            put(f"c{k + 1}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, -FCLOSE[k] * fold((t - dl) % length if loop == "loop" else max(0.0, t - dl)))) for t in times])
        for k in range(len(SEC)):
            put(f"s{k + 1}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, -SCLOSE[k] * fold(t))) for t in times])
        put(f"thumb_{tag}", [kf("rotation", t, *mirror(s, 0, 0, 28 * max(0.0, fold(t)))) for t in times])
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "idle", "animators": A}


Z0 = C(0)

# idle 8 s : respiration à plateaux (4 s), étirement sec 4,6–6,6 s
st = lambda t: bump(t, 4.6, 4.95, 6.15, 6.6)
mix = lambda f, v: (lambda t: f(t) * (1 - st(t)) + v * st(t))
idle = anim("idle", 8.0, {
    "shoulder": (mix(S(4, 1.0, 0, 6), 15), mix(S(4, 1.5, 0, 14), -6), mix(S(4, 2, 0, 2), 10)),
    "elbow":    (Z0, mix(S(4, 1, -30, -6), -4), mix(S(4, 1.5, -30, -3), 4)),
    "wrist":    (Z0, mix(S(4, 0.8, -50, 8), -6), mix(S(4, 1, -50, -6), 3))},
    fold=lambda t: (0.22 + 0.05 * snapv(math.sin(TAU * t / 4))) * (1 - st(t)), n_kf=80)

# fly 2,4 s : joueur debout en vol créatif : plan basculé d'environ 40°. Descente brève et dure, remontée poignet fléchi, éventail fermé.
T = 2.4
up = lambda t, lag=0.0: 0.5 + 0.5 * snapv(math.cos(TAU * (t / T - lag)))
fly = anim("fly", T, {
    "shoulder": (S(T, 4, 90, 40), S(T, 5, 90, -13), S(T, 22, 0, 0, k=1.8)),
    "elbow":    (Z0, lambda t: 8 - 3 * up(t, 0.08), S(T, 8, -30, -2)),
    "wrist":    (Z0, lambda t: -8 + 3 * up(t, 0.14), lambda t: 2 + 5 * snapv(math.sin(TAU * t / T - math.radians(50))) - 15 * up(t, 0.14))},
    fold=lambda t: 0.02 + 0.40 * up(t, 0.14), n_kf=36)

# glide 3,6 s : joueur couché, le cosmétique suit le torse : presque dans le plan du dos, grandes ouvertes.
# Battement lent hors du plan par Y (à plateaux), et battement à la fusée (même expression et mêmes constantes qu'Aurelion et abyssales).
G = 3.6
BOOST = f"math.clamp((math.max(q.ground_speed,q.vertical_speed)-{V0})/{DV},0,1)*math.clamp((q.vertical_speed+8)/4,0,1)"


def term(amp, speed, ph):
    """Texte Molang de amp*clamp(1.6*sin(speed*t + ph)), signe compris ; amp = 0 : vide."""
    if not amp:
        return ""
    p = f"{ph:+g}" if ph else ""
    return f"{amp:+g}*math.clamp(1.6*math.sin(q.anim_time*{speed}{p}),-1,1)"


def mol(sign, base, slow=(0, 0), boost=(0, 0)):
    e = f"{sign * base:g}" + term(sign * slow[0], 100, slow[1])
    if boost[0]:
        e += f"{sign * boost[0]:+g}*{BOOST}*math.sin(q.anim_time*600{boost[1]:+g})"
    assert len(e) <= 256
    return e


def mkf(x, y, z):
    return {"channel": "rotation", "data_points": [{"x": x, "y": y, "z": z}], "time": 0, "interpolation": "linear"}


def glide_anim():
    A = {}

    def put(g, x, y, z):
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [mkf(x, y, z)]}

    for s_, tag in ((-1, "l"), (1, "r")):
        sx, sy, sz = mirror(s_, 1, 1, 1)      # le signe reste centralisé dans mirror()
        put(f"shoulder_{tag}", mol(sx, 8, (1.5, 90)), mol(sy, -14, (11, 0), (24, 0)), f"{sz * -4:g}")
        put(f"elbow_{tag}", "0", mol(sy, 8, (-3, -30), (11, -45)), f"{sz * 1:g}")
        put(f"wrist_{tag}", "0", mol(sy, -8, (4, -50), (13, -90)), f"{sz * 2:g}")
        for k, c in enumerate(FCLOSE):
            put(f"c{k + 1}_{tag}", "0", "0", mol(sz, round(-c * 0.12, 2), (round(c * 0.05, 2), 90), (round(c * 0.07, 2), -90)))
    return {"uuid": nuid(), "name": "glide", "loop": "loop", "override": False, "length": G, "snapping": 24, "selected": False, "animators": A}


glide = glide_anim()

# fall 1,5 s : joueur debout, ailes relevées et ouvertes, plan peu basculé (freinage), ~26°
AI = 1.5
fall = anim("fall", AI, {"shoulder": (S(AI, 3, 0, 26), C(-4), S(AI, 4, 0, 12)),
                         "elbow": (Z0, C(3), S(AI, 3, -30, 5)),
                         "wrist": (Z0, C(-4), S(AI, 3, -50, 4))},
            fold=S(AI, 0.05, 0, 0.09))

# walk 1,6 s : ramenées vers l'arrière, à moitié fermées, à-coup au rythme du pas
WK = 1.6
walk = anim("walk", WK, {"shoulder": (C(8), S(WK, 5, 0, 30), S(WK, 3.5, 0, -8)),
                         "elbow": (Z0, S(WK, 3, -30, -10), S(WK, 2, -30, -4)),
                         "wrist": (Z0, S(WK, 3, -50, 14), S(WK, 2.5, -50, -22))},
            fold=C(0.55))

# run 1,0 s : très vers l'arrière, abaissées, repli en S réparti sur les 3 articulations, éventail presque fermé
RU = 1.0
run = anim("run", RU, {"shoulder": (C(16), S(RU, 3, 0, 50), S(RU, 3, 0, -14)),
                       "elbow": (Z0, S(RU, 2, -30, -28), S(RU, 1.5, -30, -5)),
                       "wrist": (Z0, S(RU, 3, -50, 34), S(RU, 2, -50, -28))},
           fold=C(0.8))

# sneak 3 s : éventail fermé, plis serrés dans le dos, cristal du poignet qui dépasse au-dessus de l'épaule
SN = 3.0
sneak = anim("sneak", SN, {"shoulder": (C(7), S(SN, 1, 0, 10), S(SN, 1, 0, 8)),
                           "elbow": (Z0, C(-15), S(SN, 1, -30, 0)),
                           "wrist": (Z0, C(5), C(-34))},
             fold=S(SN, 0.015, 0, 0.985))

# sleep 4 s : repliées, tombantes
SL = 4.0
sleep = anim("sleep", SL, {"shoulder": (C(12), S(SL, 1, 0, 12), S(SL, 1, 0, 2)),
                           "elbow": (Z0, C(-14), C(-4)),
                           "wrist": (Z0, C(6), C(-30))},
             fold=C(1.0))

# swim 2 s : joueur couché. Ailes dans le plan du dos, rabattues vers les pieds, à demi fermées ; ondulation hors du plan par Y.
SW = 2.0
swim = anim("swim", SW, {"shoulder": (C(7), S(SW, 7, 0, 2), C(-34)),
                         "elbow": (Z0, S(SW, 6, -30, 6), C(-10)),
                         "wrist": (Z0, S(SW, 7, -60, -4), C(-10))},
            fold=C(0.65))

# mount 3 s : repos relevé, pointes hautes
MT = 3.0
mount = anim("mount", MT, {"shoulder": (C(10), S(MT, 2.5, 0, 8), S(MT, 3.5, 0, 12)),
                           "elbow": (Z0, S(MT, 1.5, -30, -4), S(MT, 2, -30, 5)),
                           "wrist": (Z0, C(2), S(MT, 2, -50, -2))},
             fold=S(MT, 0.04, 0, 0.26))

# attack et hurt : une fois par-dessus l'état, dernière image neutre, seuls les groupes concernés.
IMPULSE = {"shoulder", "elbow", "wrist", "c", "s", "thumb"}
AT = 0.8
atk = lambda t: bump(t, 0.0, 0.07, 0.24, 0.60)
attack = anim("attack", AT, {"shoulder": (lambda t: 24 * atk(t), lambda t: -12 * atk(t), lambda t: 12 * atk(t)),
                             "elbow": (Z0, lambda t: -6 * atk(t), lambda t: 5 * atk(t)),
                             "wrist": (Z0, lambda t: -8 * atk(t), lambda t: 6 * atk(t))},
              fold=lambda t: -0.08 * atk(t), n_kf=24, loop="once", only=IMPULSE)

HU = 0.8
hu = lambda t: bump(t, 0.0, 0.05, 0.20, 0.60)
tr = lambda t: 3 * snapv(math.sin(TAU * t * 6 / HU), 4) * (1 - sm(t, 0.2, 0.58))
hurt = anim("hurt", HU, {"shoulder": (lambda t: 6 * hu(t), lambda t: 16 * hu(t), lambda t: 8 * hu(t) + tr(t)),
                         "elbow": (Z0, lambda t: -6 * hu(t), lambda t: -3 * hu(t) + tr(t)),
                         "wrist": (Z0, lambda t: 8 * hu(t), lambda t: -3 * hu(t) + tr(t))},
            fold=lambda t: 0.25 * hu(t), n_kf=32, loop="once", only=IMPULSE)

for _an in (attack, hurt):                 # retour à 0 : la dernière image du mode once reste affichée
    for _b in _an["animators"].values():
        _end = _b["keyframes"][-1]["data_points"][0]
        assert all(abs(float(_end[a])) < 0.02 for a in "xyz"), (_an["name"], _b["name"], _end)


def particle_anim(name, length, curve, n):
    times = [i * length / n for i in range(n + 1)]
    return {"uuid": nuid(), "name": name, "loop": "loop", "override": False, "length": length, "snapping": 24, "selected": False,
            "animators": {groups[PL]["uuid"]: {"name": PL, "type": "bone", "keyframes": [kf("rotation", t, *curve(t)) for t in times]}}}


# chute 3 s : un tour complet autour de Y (boucle fermée) et un balancement ; repos 6 s : respire à peine
PF, PR = 3.0, 6.0
givre_fall = particle_anim("particle_givre_fall", PF, lambda t: (24 * math.sin(TAU * t / PF), 360 * t / PF, 18 * math.cos(2 * TAU * t / PF)), 24)
givre_rest = particle_anim("particle_givre_rest", PR, lambda t: (0, 0, 1.2 * math.sin(TAU * t / PR)), 12)

ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, attack, hurt, givre_fall, givre_rest]
assert 6 <= len(EMITS) <= 8 and len(ANIMS) <= 16
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
      f"{len(EMITS)} emit_ ; texture {len(tex_b64) // 1024} Ko")
