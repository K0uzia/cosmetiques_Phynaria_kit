"""Lames abyssales : paire de longues lames courbes à un seul tranchant, une par main. Design original, assorti à ailes_abyssales et bandeau_abyssal.
Écrit lames_abyssales.png, lames_abyssales_e.png et .build/lames_abyssales_brut.bbmodel à côté de ce script.

Lame : une plaque découpée par alpha (contour courbe sans marches) autour d'une âme d'os pleine et d'un filet vert en volume, lisible par la tranche.
Garde et pommeau : griffes recourbées (peau + âme). Poignée de cuir cousu, clous d'os. Groupes de premier niveau right_arm (x > 0) et left_arm (x < 0).
Tout est construit dans un plan vertical (a vers l'avant, b vers le haut), origine au centre de la poignée, légèrement ouvert vers l'extérieur.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

AVEC_E = True       # True : embarque le calque _e en seconde texture. Réactivé le 2026-11-03 (correctif du mod annoncé, à vérifier en jeu).
NOM = "lames_abyssales"
TEX = 512
TAU = 2 * math.pi

# Prise : poignée sous le poing (bas du bras à y = 12), à peine enfoncée pour que la main la serre.
HAND_X, HAND_Y, HAND_Z = 6.0, 11.3, -0.6
YAW = 6.0           # ouverture du plan de lame vers l'extérieur (degrés) : dégage la jambe, lisible de face

# Lame, dans le plan (a, b)
BL_START = (3.0, -0.32)
BL_LEN = 19.0
BL_A0, BL_A1 = -31.0, -7.0      # direction au talon et près de la pointe (degrés)
DENS = 25.0                     # texels par px sur la lame


def lerp(a, b, k):
    return a + (b - a) * k


def blade_hs(t):
    """Demi-largeur côté dos."""
    return 1.15 * (1 + 0.14 * math.sin(math.pi * min(t * 1.6, 1))) * max(0.0, 1 - t ** 1.7) ** 0.85 + 0.03


def blade_he(t):
    """Demi-largeur côté tranchant."""
    return 1.5 * (1 + 0.10 * math.sin(math.pi * min(t * 1.4, 1))) * max(0.0, 1 - t ** 3.0) ** 0.8 + 0.03


def band(t):
    """Largeur du tranchant vert (px) : ≥ 0,3 px, soit 6 texels."""
    return lerp(0.62, 0.30, t)


def blade_curve(n=480):
    pts, angs = [], []
    x, y = BL_START
    ds = BL_LEN / n
    for i in range(n + 1):
        t = i / n
        ang = math.radians(lerp(BL_A0, BL_A1, t))
        pts.append((x, y))
        angs.append(ang)
        x += math.cos(ang) * ds
        y += math.sin(ang) * ds
    return np.array(pts), np.array(angs)


CURVE_PTS, CURVE_ANG = blade_curve()
TS = np.linspace(0, 1, len(CURVE_PTS))


def blade_at(t):
    """Point de l'axe et normale (vers le dos) au paramètre t."""
    i = min(int(round(t * (len(CURVE_PTS) - 1))), len(CURVE_PTS) - 1)
    a = CURVE_ANG[i]
    return CURVE_PTS[i], np.array((-math.sin(a), math.cos(a)))


def blade_poly():
    sp = [blade_at(t)[0] + blade_at(t)[1] * blade_hs(t) for t in TS[::4]]
    ed = [blade_at(t)[0] - blade_at(t)[1] * blade_he(t) for t in TS[::4]]
    # éperon d'os sur le dos, près du talon : une seule dent douce
    i0, i1, i2 = 16, 22, 30
    tip = blade_at(TS[i0 * 4])[0] + blade_at(TS[i0 * 4])[1] * (blade_hs(TS[i0 * 4]) + 0.95) + np.array((-0.55, 0.0))
    sp = sp[:i0] + [tip] + sp[i1:]
    return sp + ed[::-1], i2


BLADE_POLY, _ = blade_poly()
CHORD = CURVE_PTS[-1] - CURVE_PTS[0]
CHORD_ANG = math.atan2(CHORD[1], CHORD[0])
CX, CY = math.cos(CHORD_ANG), math.sin(CHORD_ANG)


def to_chord(p):
    return (p[0] * CX + p[1] * CY, -p[0] * CY + p[1] * CX)


_cp = np.array([to_chord(p) for p in BLADE_POLY])
U0, V0, U1, V1 = _cp[:, 0].min() - 0.1, _cp[:, 1].min() - 0.1, _cp[:, 0].max() + 0.1, _cp[:, 1].max() + 0.1
BLADE_W, BLADE_H = U1 - U0, V1 - V0


def smooth_noise(shape, cells, seed):
    r = np.random.default_rng(seed)
    a = (r.random((cells, cells)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((shape[1], shape[0]), Image.BICUBIC), np.float32) / 255


def paint_blade():
    W, H = int(math.ceil(BLADE_W * DENS)), int(math.ceil(BLADE_H * DENS))
    ss = 3
    GW, GH = W * ss, H * ss
    m = Image.new("L", (GW, GH), 0)
    ImageDraw.Draw(m).polygon([((u - U0) / BLADE_W * GW, (V1 - v) / BLADE_H * GH) for u, v in _cp], fill=255)
    jj, ii = np.mgrid[0:GH, 0:GW]
    uu, vv = U0 + (ii + 0.5) / GW * BLADE_W, V1 - (jj + 0.5) / GH * BLADE_H
    aa, bb = uu * CX - vv * CY, uu * CY + vv * CX
    dd = np.full(aa.shape, 1e9, np.float32)
    tt = np.zeros(aa.shape, np.float32)
    off = np.zeros(aa.shape, np.float32)
    for k in range(0, len(CURVE_PTS), 2):
        t = float(TS[k])
        p, nrm = blade_at(t)
        d2 = (aa - p[0]) ** 2 + (bb - p[1]) ** 2
        ok = d2 < dd
        dd[ok], tt[ok] = d2[ok], t
        off[ok] = ((aa - p[0]) * nrm[0] + (bb - p[1]) * nrm[1])[ok]
    he = np.vectorize(blade_he)(tt)
    hs = np.vectorize(blade_hs)(tt)
    bw = np.vectorize(band)(tt)
    to_edge = off + he                 # distance au tranchant (px)
    to_spine = hs - off                # distance au dos (px)
    n1, n2 = smooth_noise(aa.shape, 11, 7), smooth_noise(aa.shape, 42, 8)
    blot = n1 * 0.6 + n2 * 0.4
    # os noir-charbon, taillé : un pan haut clair et un pan bas sombre, séparés par une arête violacée
    ridge = (hs - he) * 0.32 + (off * 0.0)
    q = off - ridge
    c = np.empty(aa.shape + (3,), np.float32)
    c[...] = (30, 25, 40)
    c = lerp(c, np.array((58, 50, 72), np.float32), (np.clip((blot - 0.34) * 2.2, 0, 1) * 0.75)[..., None])
    c = lerp(c, np.array((14, 10, 20), np.float32), (np.clip(-q / 1.3, 0, 1) * 0.72)[..., None])
    c *= (1 + 0.05 * np.sin(tt * 150 + 7 * n1))[..., None]
    c = lerp(c, np.array((126, 92, 170), np.float32), (np.clip(1 - np.abs(q) / 0.17, 0, 1) * (0.55 + 0.4 * np.sin(tt * 19)))[..., None].clip(0, 1))
    c = lerp(c, np.array((98, 68, 126), np.float32), (to_spine < 0.13)[..., None] * 0.9)
    # tranchant : aura sombre, bande verte nette, filet vif sur le fil
    c = lerp(c, np.array((22, 66, 40), np.float32), (np.clip(1 - (to_edge - bw) / 0.34, 0, 1) * 0.85)[..., None])
    vein = np.zeros(aa.shape, bool)
    mv = Image.new("L", (GW, GH), 0)
    dv = ImageDraw.Draw(mv)
    for t0, h0, dt in ((0.10, 1.25, 0.05), (0.27, 1.05, -0.04), (0.45, 0.85, 0.05)):
        pts = []
        for j in range(5):
            k = j / 4
            p, nrm = blade_at(t0 + dt * k)
            w = p + nrm * lerp(-blade_he(t0), -blade_he(t0) + h0, k) + nrm * 0.06 * math.sin(j * 2.4)
            u_, v_ = to_chord(w)
            pts.append(((u_ - U0) / BLADE_W * GW, (V1 - v_) / BLADE_H * GH))
        for j in range(4):
            dv.line([pts[j], pts[j + 1]], fill=255, width=max(1, int((0.3 - 0.04 * j) * DENS * ss)))
    vein = np.array(mv) > 127
    c = lerp(c, np.array((96, 200, 44), np.float32), vein[..., None] * 1.0)
    edge_band = to_edge < bw
    edge_core = to_edge < bw * 0.42
    c = lerp(c, np.array((96, 200, 44), np.float32), edge_band[..., None] * 1.0)
    c = lerp(c, np.array((190, 255, 96), np.float32), edge_core[..., None] * 1.0)
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(m.resize((W, H), Image.LANCZOS)) > 110
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    out[~al, :3] = rgb[al].mean(axis=0).astype(np.uint8)
    # calque _e : le tranchant et les veines seulement, en lignes fines
    glow = np.array(Image.fromarray(((edge_core | vein) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 120
    glow &= al
    eo = np.zeros((H, W, 4), np.uint8)
    eo[glow] = (132, 255, 72, 255)
    return out, eo


def hook_shape(L, curve):
    """Griffe : axe recourbé, largeur qui s'effile. curve > 0 : se recourbe vers +y local."""
    return (lambda t: (L * (t - 0.12 * t * t), curve * L * t ** 2.1)), (lambda t: 0.135 * L * (1 - t) ** 0.8 + 0.006 * L)


HOOK_BB = (-0.20, 0.46)
CURVE = 0.30


def paint_hook(W, H):
    ss = 4
    ay, ax = np.mgrid[0:H * ss, 0:W * ss]
    a = lerp(-0.02, 1.0, (ax + 0.5) / (W * ss))
    b = lerp(HOOK_BB[1], HOOK_BB[0], (ay + 0.5) / (H * ss))
    center, hw = hook_shape(1.0, CURVE)
    dd = np.full(a.shape, 9.0, np.float32)
    tt = np.zeros(a.shape, np.float32)
    for t in np.linspace(0, 1, 200):
        cx, cy = center(t)
        d_ = np.hypot(a - cx, b - cy) / hw(t)
        ok = d_ < dd
        dd[ok], tt[ok] = d_[ok], t
    c = np.empty(a.shape + (3,), np.float32)
    c[...] = (26, 22, 34)
    c = lerp(c, np.array((98, 72, 132), np.float32), (np.clip(1 - dd * 1.6, 0, 1) * 0.72)[..., None])
    c = lerp(c, np.array((12, 8, 16), np.float32), (np.clip((dd - 0.62) * 2.2, 0, 1) * 0.8)[..., None])
    c = lerp(c, np.array((132, 240, 58), np.float32), np.clip((tt - 0.66) / 0.24, 0, 1)[..., None])
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(((dd < 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    out[~al, :3] = (26, 22, 34)
    te = np.array(Image.fromarray((tt * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS), np.float32)[..., None] / 255
    ec = lerp(np.array((10, 34, 12), np.float32), np.array((156, 255, 84), np.float32), np.clip((te - 0.3) / 0.6, 0, 1))
    eo = np.dstack([ec, al * 255.0]).astype(np.uint8)
    eo[~al] = 0
    return out, eo


def paint_bone(BW=96, BH=16):
    a = np.zeros((BH, BW, 4), np.float32)
    for yy in range(BH):
        q = abs((yy + 0.5) / BH - 0.5) * 2
        for xx in range(BW):
            u = xx / (BW - 1)
            c_ = lerp(np.array((54, 48, 66.0)), np.array((26, 22, 34.0)), q ** 1.2)
            c_ = lerp(c_, np.array((132, 98, 176.0)), max(0.0, 1 - q * 2.2) * (0.55 + 0.3 * math.sin(u * 15)))
            a[yy, xx, :3] = c_ * (0.96 + 0.05 * math.sin(u * 40 + yy * 0.6))
    a[..., 3] = 255
    return a.astype(np.uint8)


def paint_cuir(W=64, H=16):
    """Cuir noir-pourpre enroulé : bandes en travers, couture claire au milieu."""
    r = np.random.default_rng(5)
    a = np.zeros((H, W, 4), np.float32)
    for y in range(H):
        for x in range(W):
            f = (x / 12.0) % 1.0
            c_ = lerp(np.array((84, 44, 98.0)), np.array((38, 18, 48.0)), f)
            c_ = lerp(c_, np.array((14, 7, 18.0)), 1.0 if f > 0.82 else 0.0)
            a[y, x, :3] = c_ * r.uniform(0.96, 1.04)
    for x in range(1, W - 4, 9):
        a[6:10, x:x + 5, :3] = (176, 156, 184)
    a[..., 3] = 255
    return a.astype(np.uint8)


def paint_vert(W=24, H=8):
    a = np.zeros((H, W, 4), np.uint8)
    a[..., :3] = (96, 200, 44)
    a[3:5, :, :3] = (190, 255, 96)
    a[..., 3] = 255
    return a


def paint_clou(W=16, H=8):
    """Os pâle : les clous tranchent sur le cuir sombre."""
    a = np.zeros((H, W, 4), np.uint8)
    a[..., :3] = (168, 150, 176)
    a[3:5, :, :3] = (214, 200, 218)
    a[..., 3] = 255
    return a


def paint_braise(PT=48):
    """Éclat irrégulier : cœur vif, liseré sombre, une seule silhouette."""
    from PIL import ImageFilter
    m = Image.new("L", (PT * 4, PT * 4), 0)
    shard = [(0.58, 0.02), (0.72, 0.30), (0.66, 0.42), (0.86, 0.60), (0.60, 0.98), (0.50, 0.70), (0.30, 0.80), (0.38, 0.46), (0.20, 0.34), (0.46, 0.26)]
    ImageDraw.Draw(m).polygon([(x * PT * 4, y * PT * 4) for x, y in shard], fill=255)
    f = np.array(m.filter(ImageFilter.GaussianBlur(PT * 0.2)), np.float32) / 255
    c = np.empty(f.shape + (3,), np.float32)
    c[...] = (28, 74, 30)
    c = lerp(c, np.array((120, 232, 52), np.float32), np.clip((f - 0.32) * 2.6, 0, 1)[..., None])
    c = lerp(c, np.array((206, 255, 118), np.float32), np.clip((f - 0.66) * 4.5, 0, 1)[..., None])
    i = np.array(Image.fromarray(c.astype(np.uint8), "RGB").resize((PT, PT), Image.LANCZOS))
    al = np.array(m.resize((PT, PT), Image.LANCZOS)) > 110
    out = np.dstack([i, al * 255]).astype(np.uint8)
    out[~al, :3] = i[al].mean(axis=0).astype(np.uint8)
    return out


UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def atlas():
    bl, ble = paint_blade()
    hb, hbe = paint_hook(150, 100)
    hs, hse = paint_hook(84, 56)
    items = [("lame", bl, ble), ("hook_big", hb, hbe), ("hook_small", hs, hse), ("bone", paint_bone(), None), ("cuir", paint_cuir(), None), ("vert", paint_vert(), paint_vert()), ("clou", paint_clou(), None), ("braise", paint_braise(), None)]
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, im, ime in sorted(items, key=lambda it: -it[1].shape[0]):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, "atlas plein"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None:
            tex_e[y:y + h, x:x + w] = ime
        x += w + 1
        shelf = max(shelf, h)
    assert tex[TEX - 3, TEX - 3, 3] == 0
    tex[..., :3] &= 0xFC
    assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
    res = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        res.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return res


tex_b64, tex_e_b64 = atlas()

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


def group(name, origin, parent=None):
    assert name not in groups
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "rotation": [0, 0, 0]}
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


def strip(tile, u0, u1):
    bu0, bv0, bu1, bv1 = UV[tile]
    ua = lerp(bu0, bu1, u0)
    ub = max(lerp(bu0, bu1, u1), ua + 2)
    lg = [ua, bv0, ub, bv1]
    end = [ua, bv0 + 3, ua + 2, bv0 + 5]
    return {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end}


def slab(g, name, p, q, up, h, th, tile="bone", u0=0.0, u1=1.0, ov=0.05):
    """Tronçon plat : hauteur ±h dans le plan de lame, épaisseur ±th."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X = unit(q - p)
    Y = unit(up - (up @ X) * X)
    Z_ = np.cross(X, Y)
    cube(g, name, p + (-ov, -h, -th), p + (L + ov, h, th), p, euler(np.column_stack([X, Y, Z_])), strip(tile, u0, u1))


def bar(g, name, p, q, r, u0=0.0, u1=1.0, octo=True, ov=0.1, tile="bone"):
    """Tronçon d'os ou de cuir : section octogonale (deux cubes à 45°) ou losange seul."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X = unit(q - p)
    ref = V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0)
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R0 = np.column_stack([X, Y, Z_])
    R45 = np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])
    faces = strip(tile, u0, u1)
    if octo:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R0), faces)
        cube(g, name + "o", p + (-ov + 0.03, -r * 0.97, -r * 0.97), p + (L + ov - 0.03, r * 0.97, r * 0.97), p, euler(R45), faces)
    else:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R45), faces)


def hook(g, name, p, X, Y, L, tile="hook_small", core=2, z_ofs=0.07):
    """Griffe : peau découpée + âme pleine plus étroite. Elle part de p vers X et se recourbe vers Y."""
    p, X = np.asarray(p, float), unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    n = np.cross(X, Y)
    lo, hi = HOOK_BB
    c = p + X * (0.49 * L) + Y * ((lo + hi) / 2 * L) + n * z_ofs
    plate(g, name, c, X, Y, 1.02 * L, (hi - lo) * L, tile)
    center, hw = hook_shape(L, CURVE)
    for j in range(core):
        t0, t1 = j / core * 0.84, (j + 1) / core * 0.84
        a, b = center(t0), center(t1)
        bar(g, f"{name}c{j}", p + X * a[0] + Y * a[1], p + X * b[0] + Y * b[1], max(0.13, hw((t0 + t1) / 2) * 0.62), 0.6, 0.9, octo=False, ov=0.06)


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


EMITS = []


def emit(parent, at):
    EMITS.append(group("emit_braise" + (str(len(EMITS) + 1) if EMITS else ""), at, parent=parent))


GARDES = []


def build(s, tag, bras):
    psi = math.radians(YAW)
    A = V(s * math.sin(psi), 0, -math.cos(psi))
    B = V(0, 1, 0)
    P0 = V(s * HAND_X, HAND_Y, HAND_Z)
    W = lambda a, b=0.0: P0 + A * a + B * b
    Wv = lambda a, b: A * a + B * b
    n = np.cross(A, B)

    lame = group(f"lame_{tag}", P0, parent=bras)

    # Lame : une seule plaque découpée
    uc, vc = (U0 + U1) / 2, (V0 + V1) / 2
    cc = (uc * CX - vc * CY, uc * CY + vc * CX)
    plate(lame, f"lame_peau_{tag}", W(*cc), Wv(CX, CY), Wv(-CY, CX), BLADE_W, BLADE_H, "lame")

    # Âme d'os : plate, en retrait du dos et du tranchant ; filet vert en volume sur le fil, lisible par la tranche
    N = 11
    for i in range(N):
        t0, t1 = 0.86 * i / N, 0.86 * (i + 1) / N
        tm = (t0 + t1) / 2
        hs, he, bw = blade_hs(tm), blade_he(tm), band(tm)
        hi, lo = hs - 0.24, -(he - bw - 0.14)
        mid, half = (hi + lo) / 2, max(0.1, (hi - lo) / 2)
        pa, na = blade_at(t0)
        pb, nb = blade_at(t1)
        slab(lame, f"ame{i}_{tag}", W(*(pa + na * mid)), W(*(pb + nb * mid)), Wv(*((na + nb) / 2)), half, lerp(0.40, 0.22, tm), "bone", 0.05 + 0.08 * i, 0.13 + 0.08 * i)
    M = 12
    for i in range(M):
        t0, t1 = 0.97 * i / M, 0.97 * (i + 1) / M
        tm = (t0 + t1) / 2
        pa, na = blade_at(t0)
        pb, nb = blade_at(t1)
        oa, ob = -(blade_he(t0) - band(t0) * 0.5), -(blade_he(t1) - band(t1) * 0.5)
        slab(lame, f"fil{i}_{tag}", W(*(pa + na * oa)), W(*(pb + nb * ob)), Wv(*((na + nb) / 2)), band(tm) * 0.33, lerp(0.26, 0.17, tm), "vert", 0.1, 0.9, ov=0.03)

    # Points d'émission le long du tranchant
    for t in (0.25, 0.55, 0.85):
        p, nrm = blade_at(t)
        emit(lame, W(*(p - nrm * blade_he(t))))

    # Poignée : cuir cousu, sous le poing, de l'arrière du bras à la garde
    G0, G1 = (-2.8, 0.24), (2.9, -0.30)
    Gm = ((G0[0] + G1[0]) / 2, (G0[1] + G1[1]) / 2)
    bar(lame, f"poignee0_{tag}", W(*G0), W(*Gm), 0.6, 0.0, 0.5, tile="cuir", ov=0.04)
    bar(lame, f"poignee1_{tag}", W(*Gm), W(*G1), 0.6, 0.5, 1.0, tile="cuir", ov=0.04)
    for k, u_ in enumerate((-1.45, 0.05, 1.55)):
        c = W(u_, lerp(G0[1], G1[1], (u_ - G0[0]) / (G1[0] - G0[0])))
        bar(lame, f"clou{k}_{tag}", c - n * 0.86, c + n * 0.86, 0.27, 0.1, 0.9, octo=False, ov=0.0, tile="clou")
    # Bagues d'os aux deux bouts
    bar(lame, f"bague_g_{tag}", W(2.55, -0.26), W(3.1, -0.32), 0.92, 0.3, 0.45)
    bar(lame, f"bague_p_{tag}", W(-3.2, 0.28), W(-2.8, 0.24), 0.8, 0.3, 0.45)

    # Garde : griffe recourbée vers la main, contre-griffe vers le haut, griffe latérale ; pommeau : petite griffe
    g_b = group(f"garde_{tag}", W(2.8, -0.3), parent=lame)
    hook(g_b, f"griffe_garde_{tag}", W(2.75, -0.55), Wv(0.32, -1), Wv(-1, 0), 5.8, "hook_big", core=3)
    g_h = group(f"contre_{tag}", W(2.9, 0.2), parent=lame)
    hook(g_h, f"griffe_contre_{tag}", W(2.95, 0.3), Wv(0.45, 1), Wv(1, 0), 3.2, "hook_small", core=2)
    g_c = group(f"griffe_ext_{tag}", W(2.9, -0.3), parent=lame)
    hook(g_c, f"griffe_laterale_{tag}", W(2.85, -0.3) + V(s * 0.3, 0, 0), V(s, 0, 0) + A * 0.35, A + V(0, -0.2, 0), 3.4, "hook_small", core=2)
    g_p = group(f"pommeau_{tag}", W(-3.1, 0.25), parent=lame)
    hook(g_p, f"griffe_pommeau_{tag}", W(-3.05, 0.1), Wv(-0.75, -0.85), Wv(1, -0.4), 3.2, "hook_small", core=2)
    GARDES.append((g_b, g_h, g_c, g_p, s))
    return lame


bras_r = group("right_arm", [5, 22, 0])
bras_l = group("left_arm", [-5, 22, 0])
LAMES = [(build(1, "r", bras_r), 1), (build(-1, "l", bras_l), -1)]

PG = group("particle_braise", [0, 0, 0])
u0, v0, u1, v1 = UV["braise"]
cube(PG, "braise", [-1.6, 0.3, -1.6], [1.6, 0.6, 1.6], [0, 0, 0], (0, 0, 0), {"up": [u0, v0, u1, v1]})
outliner = [bone_node(bras_r), bone_node(bras_l), bone_node(PG)]


# ------------------------------------------------------------------ animations
# Guide, section 3 : +X relève ce qui pointe vers l'avant ; +Y amène vers -x ce qui pointe vers l'avant ; +Z pousse le bas vers +x.
# Intention pour un côté s : rise relève la pointe ; inward ramène la pointe vers l'axe du corps ; roll tourne le fil vers l'axe. MIROIR D'AXES ici seulement.
def mirror(s, rise, inward, roll):
    return rise, s * inward, -s * roll


def kf(t, x, y, z):
    return {"channel": "rotation", "data_points": [{"x": str(round(x + 0.0, 2)), "y": str(round(y + 0.0, 2)), "z": str(round(z + 0.0, 2))}],
            "time": round(t, 3), "interpolation": "linear"}


def anim(name, length, tracks, n_kf=None, loop="loop"):
    n = n_kf or max(6, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]
    A = {groups[g]["uuid"]: {"name": g, "type": "bone", "keyframes": [kf(t, *f(t)) for t in times]} for g, f in tracks.items()}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def state(name, L, rise, inward, amp, cycles, griffe_off, griffe_amp, n_kf=None):
    """Lame : pose + oscillation ; griffes : resserrées de griffe_off, avec un léger frémissement."""
    tr = {}
    for g, s in LAMES:
        def f(t, s=s):
            ph = TAU * (cycles * t / L + (0.07 if s < 0 else 0))
            return mirror(s, rise + amp * math.sin(ph), inward, 0.35 * amp * math.sin(ph + 1.0))
        tr[g] = f
    for gb, gh, gc, gp, s in GARDES:
        for j, g in enumerate((gb, gh, gc, gp)):
            sg = (1, -1, 1, -1)[j]

            def e(t, s=s, j=j, sg=sg):
                ph = TAU * (cycles * t / L - 0.12 * j + (0.07 if s < 0 else 0))
                return mirror(1, sg * (griffe_off + griffe_amp * math.sin(ph)), 0, 0)
            tr[g] = e
    return anim(name, L, tr, n_kf=n_kf)


idle = state("idle", 8.0, 0.0, 0.0, 0.9, 2, 0.0, 2.5, n_kf=32)
run = state("run", 1.0, 14.0, 2.0, 2.5, 2, 5.0, 1.5, n_kf=12)
sneak = state("sneak", 3.0, -6.0, -3.0, 0.6, 1, 6.0, 1.0, n_kf=12)


def a_lame(s, delay, k):
    def f(t):
        # armé bref, coupe, retour à zéro bien avant la fin
        up = bump(t, delay, delay + 0.09, delay + 0.09, delay + 0.2)
        cut = bump(t, delay + 0.09, delay + 0.22, delay + 0.26, 0.72)
        return mirror(s, k * (9 * up - 9 * cut), k * 9 * cut, k * 7 * cut)
    return f


tr_a = {LAMES[0][0]: a_lame(1, 0.0, 1.0), LAMES[1][0]: a_lame(-1, 0.05, 0.7)}
for gb, gh, gc, gp, s in GARDES:
    tr_a[gb] = (lambda t: (12 * bump(t, 0.02, 0.14, 0.26, 0.7), 0, 0))
attack = anim("attack", 0.8, tr_a, n_kf=24, loop="once")

PF, PR = 3.0, 6.0
pfall = anim("particle_braise_fall", PF, {PG: lambda t: (24 * math.sin(TAU * t / PF), 360 * t / PF, 18 * math.cos(2 * TAU * t / PF))}, n_kf=24)
prest = anim("particle_braise_rest", PR, {PG: lambda t: (0, 0, 1.2 * math.sin(TAU * t / PR))}, n_kf=12)

ANIMS = [idle, run, sneak, attack, pfall, prest]

# ------------------------------------------------------------------ écriture
assert 60 <= len(elements) <= 180, f"budget : {len(elements)} cubes"
assert len(EMITS) == 6
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;", len(EMITS), "emit_")
