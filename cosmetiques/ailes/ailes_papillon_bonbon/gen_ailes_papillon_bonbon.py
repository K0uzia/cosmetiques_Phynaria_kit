"""Ailes papillon bonbon — ailes de papillon en vitrail de sucre (fraise, menthe, citron, lavande, pêche). Design original.
Écrit ailes_papillon_bonbon.png, ailes_papillon_bonbon_e.png et .build/ailes_papillon_bonbon_brut.bbmodel à côté de ce script.

Technique d'ailes_abyssales : nervures en vrai volume (baguettes octogonales effilées) + membrane peinte d'un seul tenant
dans le plan de l'aile, découpée par alpha (0/255), tranches transparentes. Ici chaque aile est rigide (papillon) :
une plaque par aile, portée par un seul groupe qui pivote à la racine.
Deux paires par côté : antérieure arrondie (~15 x 12 px) et postérieure ronde (~10 px) avec une queue en goutte.
Ourlet de crème en volume tout autour (losanges qui se recouvrent) : l'aile reste lisible par la tranche.
"""
import base64, io, json, math, os, re, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # calque _e embarqué en seconde texture, jamais assigné aux faces (correctif annoncé le 2026-11-03, à vérifier en jeu)
TEX = 512
V0, DV = 26, 5      # battement à la fusée (glide) : constantes d'Aurelion, validées en jeu
TAU = 2 * math.pi
NOM = "ailes_papillon_bonbon"


def lerp(a, b, k):
    return a + (b - a) * k


def catmull(ctrl, n=40):
    """Spline fermée de Catmull-Rom : contour arrondi, sans angle."""
    out, m = [], len(ctrl)
    for i in range(m):
        p0, p1, p2, p3 = ctrl[i - 1], ctrl[i], ctrl[(i + 1) % m], ctrl[(i + 2) % m]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    return out


def resample(loop, step):
    """Polyligne fermée rééchantillonnée à pas constant (longueur d'arc)."""
    pts = loop + [loop[0]]
    ls = [0.0]
    for a, b in zip(pts, pts[1:]):
        ls.append(ls[-1] + math.dist(a, b))
    n = max(6, int(round(ls[-1] / step)))
    out, j = [], 0
    for i in range(n):
        d = ls[-1] * i / n
        while ls[j + 1] < d:
            j += 1
        k = (d - ls[j]) / max(1e-9, ls[j + 1] - ls[j])
        out.append((lerp(pts[j][0], pts[j + 1][0], k), lerp(pts[j][1], pts[j + 1][1], k)))
    return out


# ------------------------------------------------------------------ formes (aile droite, x > 0, px du modèle)
ZF, ZH = 3.45, 3.0                      # plans des ailes (dos du joueur à z = 2) ; l'antérieure recouvre la postérieure côté dos
PIV_F, PIV_H = (1.6, 23.2), (1.6, 21.8)

WINGS = {
    "fore": dict(
        ctrl=[(1.7, 23.7), (3.3, 27.4), (5.9, 31.0), (9.3, 33.5), (12.8, 34.4), (15.5, 33.4), (16.6, 30.6), (16.1, 27.4),
              (14.3, 24.8), (11.2, 23.0), (7.2, 22.3), (3.6, 22.5)],
        disc=[(2.3, 23.4), (4.8, 26.3), (8.0, 27.9), (9.9, 27.2), (9.4, 24.8), (6.6, 23.4)],
        C=(6.6, 25.6), z=ZF, piv=PIV_F,
        rays=[104, 66, 32, 0, -34, -72],
        ring=[9, 0.52, 0.46, 0.56, 0.48, 0.55],
        pal_shift=0),
    "hind": dict(
        ctrl=[(1.8, 22.3), (4.6, 22.7), (8.4, 22.6), (10.9, 21.2), (11.7, 18.4), (10.9, 15.5), (9.2, 13.6), (8.5, 12.2),
              (8.7, 10.6), (8.9, 9.4), (8.2, 8.5), (7.3, 9.0), (7.2, 10.4), (7.3, 12.0), (6.2, 13.4), (4.2, 15.2),
              (2.6, 17.8), (1.8, 20.3)],
        disc=[(2.2, 21.6), (5.2, 21.6), (7.3, 19.7), (6.6, 17.6), (4.4, 17.8), (2.6, 19.8)],
        C=(4.6, 19.8), z=ZH, piv=PIV_H,
        rays=[32, -6, -44, -82, -128],
        ring=[9, 0.50, 0.56, 0.48, 0.54],
        pal_shift=2),
}
for w in WINGS.values():
    w["out"] = catmull(w["ctrl"])
    w["dloop"] = catmull(w["disc"], 24)

# ------------------------------------------------------------------ peinture : carte de chaque aile dans son plan
R = 24                                   # texels de carte par px modèle
PAL = [np.array(c, np.float32) for c in ((255, 156, 182), (150, 232, 196), (255, 232, 128), (192, 168, 252), (255, 186, 146))]
WHITE = np.array((255, 253, 250), np.float32)
CREAM = np.array((255, 246, 226), np.float32)
LEAD = np.array((178, 104, 150), np.float32)      # ligne de nervure, mauve plus foncé
DISC = np.array((246, 222, 255), np.float32)


def polar(loop, C, nb=720):
    """Rayon du contour selon l'angle autour de C (le plus lointain si le contour se replie)."""
    ang = np.array([math.atan2(p[1] - C[1], p[0] - C[0]) for p in loop])
    dist = np.array([math.dist(p, C) for p in loop])
    bins = ((ang + math.pi) / TAU * nb).astype(int) % nb
    r = np.full(nb, np.nan)
    for b, d in zip(bins, dist):
        if np.isnan(r[b]) or d > r[b]:
            r[b] = d
    idx = np.arange(nb)
    good = ~np.isnan(r)
    return np.interp(idx, idx[good], r[good], period=nb)


def rad_at(tab, a):
    nb = len(tab)
    return np.interp((np.asarray(a) + math.pi) / TAU * nb, np.arange(nb + 1), np.append(tab, tab[0]))


def thick(draw, pts, width):
    """Trait épais à bouts et jointures ronds (pas d'interstices aux jointures, contrairement à line(width=…))."""
    r = width / 2
    for a, b in zip(pts, pts[1:]):
        draw.line([a, b], fill=255, width=max(1, int(round(width))))
    for x, y in pts:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=255)


def paint(w):
    xs = [p[0] for p in w["out"]]
    ys = [p[1] for p in w["out"]]
    x0, x1 = math.floor(min(xs) * 4 - 1) / 4, math.ceil(max(xs) * 4 + 1) / 4
    y0, y1 = math.floor(min(ys) * 4 - 1) / 4, math.ceil(max(ys) * 4 + 1) / 4
    GW, GH = int(round((x1 - x0) * R)), int(round((y1 - y0) * R))
    w["box"] = (x0, y0, x1, y1)
    gy, gx = np.mgrid[0:GH, 0:GW]
    X, Y = x0 + (gx + 0.5) / R, y1 - (gy + 0.5) / R
    px = lambda p: ((p[0] - x0) * R, (y1 - p[1]) * R)

    def poly_mask(loop):
        im = Image.new("L", (GW, GH), 0)
        ImageDraw.Draw(im).polygon([px(p) for p in loop], fill=255)
        return im

    M_img = poly_mask(w["out"])
    M = np.array(M_img) > 127
    D = np.array(poly_mask(w["dloop"])) > 127
    C = w["C"]
    ro, rd = polar(w["out"], C), polar(w["dloop"], C)
    A = np.arctan2(Y - C[1], X - C[0])
    dist = np.hypot(X - C[0], Y - C[1])
    rho = (dist - rad_at(rd, A)) / np.maximum(0.3, rad_at(ro, A) - rad_at(rd, A))
    rays = sorted(math.radians(a) for a in w["rays"])
    sector = np.searchsorted(np.array(rays), A) % len(rays)   # secteur entre deux nervures (le dernier fait le tour)
    ring = np.array(w["ring"])[sector]
    band = (rho > ring).astype(int)
    cell = np.where(D, 0, 1 + sector * 2 + band)
    tail = (Y < 12.6) & (X > 6.5) if "tail" not in w and w is WINGS["hind"] else np.zeros_like(M)
    cell = np.where(tail, 99, cell)

    # nervures : traits sombres (sous les baguettes en volume) + nervures secondaires peintes (sombre + âme crème)
    lead_img = Image.new("L", (GW, GH), 0)
    core_img = Image.new("L", (GW, GH), 0)
    ld, cd = ImageDraw.Draw(lead_img), ImageDraw.Draw(core_img)
    w["veins"] = []
    for a in rays:
        dv = (math.cos(a), math.sin(a))
        r0, r1 = float(rad_at(rd, a)), float(rad_at(ro, a)) - 0.15
        p0, p1 = (C[0] + dv[0] * r0, C[1] + dv[1] * r0), (C[0] + dv[0] * r1, C[1] + dv[1] * r1)
        # légère courbure : la nervure se creuse vers le bas, comme une baguette de sucre étirée
        n = 3
        bow = 0.06 * (r1 - r0)
        pts = [(lerp(p0[0], p1[0], i / n) + bow * dv[1] * math.sin(math.pi * i / n),
                lerp(p0[1], p1[1], i / n) - bow * dv[0] * math.sin(math.pi * i / n)) for i in range(n + 1)]
        w["veins"].append(pts)
        thick(ld, [px(p) for p in pts], 0.8 * R)
    dl = w["dloop"] + [w["dloop"][0]]
    thick(ld, [px(p) for p in dl], 0.8 * R)
    for k in range(len(rays)):
        if w["ring"][k] > 1:
            continue                              # secteur qui fait le tour par la racine : pas de nervure transverse
        a0, a1 = rays[k - 1], rays[k]
        if k == 0:
            a0 -= TAU
        aa = np.linspace(a0, a1, 30)
        rr = rad_at(rd, aa) + w["ring"][k] * (rad_at(ro, aa) - rad_at(rd, aa))
        pts = [px((C[0] + r * math.cos(t), C[1] + r * math.sin(t))) for t, r in zip(aa, rr)]
        thick(ld, pts, 0.4 * R)
        thick(cd, pts, 0.2 * R)
    if w is WINGS["hind"]:
        thick(ld, [px((6.6, 13.0)), px((9.4, 13.0))], 0.4 * R)
        thick(cd, [px((6.6, 13.0)), px((9.4, 13.0))], 0.2 * R)
    L = (np.array(lead_img) > 127) & M
    Cc = (np.array(core_img) > 127) & M
    near = np.clip(np.array(lead_img.filter(ImageFilter.GaussianBlur(0.7 * R)), np.float32) / 255 * 1.6, 0, 1)

    # couleur de base par cellule, éclaircie vers le blanc (lumière chaude de nuit : saumon sinon)
    col = np.zeros((GH, GW, 3), np.float32)
    ids = np.unique(cell[M])
    hl_img = Image.new("L", (GW, GH), 0)
    hd = ImageDraw.Draw(hl_img)
    for cid in ids:
        sel = (cell == cid) & M
        if cid == 0:
            base = DISC
        elif cid == 99:
            base = PAL[3]
        else:
            base = PAL[((cid - 1) // 2 * 2 + ((cid - 1) % 2) * 3 + w["pal_shift"]) % 5]
        col[sel] = base
        # reflet : ellipse blanche en haut à gauche de la cellule + petit point
        yy, xx = np.nonzero(sel & ~L)
        if len(xx) < 30:
            continue
        cx, cy = xx.mean(), yy.mean()
        s = math.sqrt(len(xx)) / R                     # taille de la cellule (px)
        ox, oy = cx - 0.20 * s * R, cy - 0.20 * s * R
        rx, ry = max(0.35, 0.20 * s) * R, max(0.18, 0.09 * s) * R
        ell = []
        for i in range(24):
            t = i / 24 * TAU
            ex, ey = rx * math.cos(t), ry * math.sin(t)
            c_, s_ = math.cos(math.radians(-38)), math.sin(math.radians(-38))
            ell.append((ox + ex * c_ - ey * s_, oy + ex * s_ + ey * c_))
        hd.polygon(ell, fill=255)
        dr = max(0.14, 0.05 * s) * R
        dx_, dy_ = ox + 0.32 * s * R, oy + 0.08 * s * R
        hd.ellipse([dx_ - dr, dy_ - dr, dx_ + dr, dy_ + dr], fill=255)
    cellf = cell.astype(np.float32)
    # dégradé interne : cœur de la cellule plus blanc, bord contre les nervures plus saturé
    k_white = np.clip(0.55 - 0.55 * near, 0, 0.55)[..., None]
    col = lerp(col, WHITE, 0.22 + k_white)
    col = lerp(col, col * np.array((0.86, 0.80, 0.88), np.float32), (near * 0.55)[..., None])
    fine = np.array(Image.fromarray((np.random.default_rng(5).random((GH // 6 + 1, GW // 6 + 1)) * 255).astype(np.uint8), "L")
                    .resize((GW, GH), Image.BICUBIC), np.float32) / 255
    col = col * (0.97 + 0.05 * fine)[..., None]
    HL = (np.array(hl_img) > 127) & M & ~np.array(lead_img.filter(ImageFilter.MaxFilter(9)), bool)
    col[HL] = WHITE
    # ourlet de crème, séparé de la membrane par un fin trait sombre
    Mb = np.array(M_img.filter(ImageFilter.GaussianBlur(0.45 * R)), np.float32) / 255
    edge = Mb > 0.80                              # érosion douce : ourlet de largeur régulière, sans dents
    edge2 = Mb > 0.90
    col[edge & ~edge2 & ~tail] = LEAD
    col[L] = LEAD
    col[Cc] = CREAM
    col[M & ~edge] = CREAM

    # calque lumineux : fond additif très sombre, fins liserés sur les reflets et l'âme des nervures secondaires
    e = col * 0.05
    e[HL] = (92, 86, 96)
    e[Cc] = (70, 60, 70)
    e[M & ~edge] = (40, 34, 36)
    e[L] = (8, 4, 8)
    w.update(map_col=col, map_e=e, map_M=M, GW=GW, GH=GH)


for w in WINGS.values():
    paint(w)


# ------------------------------------------------------------------ tuiles : baguette de sucre (nervures, ourlet)
def stick_tile(c_mid, c_edge, e_line):
    BW, BH = 96, 16
    a = np.zeros((BH, BW, 4), np.uint8)
    ae = np.zeros((BH, BW, 4), np.uint8)
    for yy in range(BH):
        q = abs((yy + 0.5) / BH - 0.5) * 2
        for xx in range(BW):
            u = xx / (BW - 1)
            c = lerp(np.array(c_mid, float), np.array(c_edge, float), q ** 1.6)
            c = c * (0.985 + 0.03 * math.sin(u * 30 + yy))       # torsade discrète de sucre filé
            a[yy, xx, :3] = np.clip(c, 0, 255)
            ae[yy, xx, :3] = e_line if q < 0.2 else (14, 10, 12)
    a[..., 3] = 255
    ae[..., 3] = 255
    return a, ae


vein_tile, vein_e = stick_tile((255, 252, 244), (232, 196, 214), (120, 104, 116))
rim_tile, rim_e = stick_tile((255, 248, 232), (238, 206, 200), (96, 84, 92))

# ------------------------------------------------------------------ atlas
DENS = 18.0


def pack(dens):
    items = [("fore", WINGS["fore"]), ("hind", WINGS["hind"])]
    uv, x = {}, 0
    hmax = 0
    for n, w in items:
        x0, y0, x1, y1 = w["box"]
        W, H = int(math.ceil((x1 - x0) * dens)), int(math.ceil((y1 - y0) * dens))
        uv[n] = (x, 0, x + W, H)
        x += W + 1
        hmax = max(hmax, H)
    if x > TEX or hmax + 40 > TEX:
        return None
    uv["vein"] = (0, hmax + 2, 96, hmax + 18)
    uv["rim"] = (98, hmax + 2, 194, hmax + 18)
    return uv


while (UV := pack(DENS)) is None:
    DENS -= 0.25
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
for n, im, ie in (("vein", vein_tile, vein_e), ("rim", rim_tile, rim_e)):
    u0, v0, u1, v1 = UV[n]
    tex[v0:v1, u0:u1] = im
    tex_e[v0:v1, u0:u1] = ie
for n, w in WINGS.items():
    u0, v0, u1, v1 = UV[n]
    W, H = u1 - u0, v1 - v0
    x0, y0, x1, y1 = w["box"]
    # recadrage exact de la carte sur la zone d'atlas (la boîte en px = W/DENS)
    w["box"] = (x0, y1 - H / DENS, x0 + W / DENS, y1)
    GWn, GHn = int(round(W / DENS * R)), int(round(H / DENS * R))
    pad = lambda arr: np.pad(arr, ((0, max(0, GHn - arr.shape[0])), (0, max(0, GWn - arr.shape[1]))) + ((0, 0),) * (arr.ndim - 2))[:GHn, :GWn]
    rgb = Image.fromarray(np.clip(pad(w["map_col"]), 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    erg = Image.fromarray(np.clip(pad(w["map_e"]), 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    al = np.array(Image.fromarray(pad(w["map_M"]).astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110
    c = np.array(rgb)
    c[~al] = c[al].mean(axis=0).astype(np.uint8)
    tex[v0:v1, u0:u1, :3] = c
    tex[v0:v1, u0:u1, 3] = al * 255
    ce = np.array(erg)
    ce[~al] = 0
    tex_e[v0:v1, u0:u1, :3] = ce
    tex_e[v0:v1, u0:u1, 3] = al * 255

CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC
assert set(np.unique(tex[..., 3])) <= {0, 255}, "semi-transparence"
assert set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence _e"


def b64(img, path):
    img.save(path, optimize=True)
    b = io.BytesIO()
    img.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


tex_b64 = b64(Image.fromarray(tex, "RGBA"), f"{NOM}.png")
tex_e_b64 = b64(Image.fromarray(tex_e, "RGBA"), f"{NOM}_e.png")

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


def plate(s, g, name, w, uvname, th=0.3):
    """Membrane : une plaque fine, contour par l'alpha, tranches transparentes ; u inversé pour l'aile gauche."""
    u0, v0, u1, v1 = UV[uvname]
    x0, y0, x1, y1 = w["box"]
    ua, ub = (u0, u1) if s > 0 else (u1, u0)
    xa, xb = (x0, x1) if s > 0 else (-x1, -x0)
    z = w["z"]
    faces = {"south": [ua, v0, ub, v1], "north": [ub, v0, ua, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
    groups[g]["ids"].append(cube(name, [xa, y0, z - th / 2], [xb, y1, z + th / 2], [s * (x0 + x1) / 2, (y0 + y1) / 2, z], faces=faces))


def bar(s, g, name, x, y, z, L, q, phi, u0, u1, tile="vein", octo=True, ov=0.0):
    """Tronçon de baguette le long de l'axe local X. octo : section octogonale (deux cubes à 45°), sinon losange seul."""
    bu0, bv0, bu1, bv1 = UV[tile]
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


def chain(s, g, name, pts, r0, r1, z, tile="vein", octo=True, ov=0.12, closed=False):
    if closed:
        pts = pts + [pts[0]]
    n = len(pts) - 1
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        L = math.dist(pts[i], pts[i + 1])
        phi = math.degrees(math.atan2(yb - ya, xb - xa))
        q = lerp(r0, r1, (i + 0.5) / n)
        bar(s, g, f"{name}{i}", xa, ya, z, L, q, phi, i / n, (i + 1) / n, tile=tile,
            octo=octo if not callable(octo) else octo(i, n), ov=ov)


def build(s):
    tag = "l" if s < 0 else "r"
    out = []
    for n, w in WINGS.items():
        g = group(f"{n}_{tag}", [s * w["piv"][0], w["piv"][1], w["z"]], parent=None)
        plate(s, g, f"{n}_m_{tag}", w, n)
        # nervures en volume : cellule discale (baguette continue) et nervures rayonnantes effilées
        chain(s, g, f"{n}_dc_{tag}", resample(w["dloop"], 2.2), 0.36, 0.36, w["z"], closed=True)
        for k, pts in enumerate(w["veins"]):
            chain(s, g, f"{n}_v{k}_{tag}", pts, 0.36, 0.27, w["z"] + 0.02 * (k % 2), octo=lambda i, nn: i < nn - 1)
        # ourlet de crème en volume : losanges qui se recouvrent, pas plus serré dans la goutte
        chain(s, g, f"{n}_rim_{tag}", resample(w["out"], 2.0 if n == "fore" else 1.6), 0.3, 0.3, w["z"] + 0.01,
              tile="rim", octo=False, ov=0.14, closed=True)
        out.append(g)
    # perle de sucre à la racine : cache la jonction des deux ailes, fixe
    rt = group(f"root_{tag}", [s * 1.4, 22.5, 3.2])
    bar(s, rt, f"perle_{tag}", 0.8, 22.5, 3.2, 1.3, 0.62, 90, 0.4, 0.6, tile="rim", octo=True)
    return out + [rt]


GL, GR = build(-1), build(1)


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone(n) for n in GL + GR]}]

# ------------------------------------------------------------------ animations
# Papillon : ailes rigides qui pivotent à la racine. Intention, aile GAUCHE :
#   fx > 0 : le plan bascule vers l'horizontale ; fy > 0 : l'aile se referme vers l'arrière (V) ; fz > 0 : la pointe monte.
# La pose du modèle (0, 0, 0) est l'aile grande ouverte dans le plan du dos.
# MIROIR D'AXES : seul endroit à toucher si la convention change (repères du guide, section 3), comme ailes_abyssales.
SX, SY, SZ = -1, -1, +1


def mirror(s, fx, fy, fz):
    return SX * fx, s * SY * fy, s * SZ * fz


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 2)), "y": str(round(y + 0.0, 2)), "z": str(round(z + 0.0, 2))}],
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


def anim(name, length, fore, lag=0.08, hind_amp=0.9, hind_off=(0, 0, 2), n_kf=None, loop="loop"):
    """fore(t) -> (fx, fy, fz). La postérieure suit avec un retard (fraction de la durée d'un battement, en secondes ici)."""
    A = {}
    n = n_kf or max(8, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]       # linéaire : dernier keyframe = premier
    lag_s = lag * length if loop == "loop" else lag

    def hind(t):
        tt = (t - lag_s) % length if loop == "loop" else max(0.0, t - lag_s)
        fx, fy, fz = fore(tt)
        k = 1.0 if loop == "loop" else (1.0 if t > 0 else 0.0)
        # bascule X et abaissement Z réduits : sous le pivot, ils enverraient les queues se croiser derrière le dos une fois l'aile balayée
        return fx * 0.35, fy * hind_amp, fz * 0.4 + hind_off[2] * k

    for s, tag in ((-1, "l"), (1, "r")):
        A[groups[f"fore_{tag}"]["uuid"]] = {"name": f"fore_{tag}", "type": "bone",
                                            "keyframes": [kf("rotation", t, *mirror(s, *fore(t))) for t in times]}
        A[groups[f"hind_{tag}"]["uuid"]] = {"name": f"hind_{tag}", "type": "bone",
                                            "keyframes": [kf("rotation", t, *mirror(s, *hind(t))) for t in times]}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "idle", "animators": A}


def sn(t, T, k=1, ph=0.0):
    return math.sin(TAU * k * t / T + math.radians(ph))


# idle 8 s : demi-ouvertes, respiration douce (4 s) puis grande ouverture lente 4,4–7,6 s
idle = anim("idle", 8.0, lambda t: (6, 34 + 8 * sn(t, 8, 2) - 26 * bump(t, 4.4, 5.6, 6.3, 7.6), 4 + 2 * sn(t, 8, 2, -40)),
            lag=0.02, n_kf=64)
# walk 1,6 s : un peu refermées vers l'arrière, petit battement au pas
walk = anim("walk", 1.6, lambda t: (6, 42 + 7 * sn(t, 1.6), 2 + 3 * sn(t, 1.6, 1, -40)), lag=0.08, n_kf=16)
# run 1,0 s : nettement refermées vers l'arrière et abaissées, frémissement
run = anim("run", 1.0, lambda t: (10, 62 + 5 * sn(t, 1.0, 2), -16 + 2 * sn(t, 1.0, 2, -60)), lag=0.06, n_kf=16)
# sneak 3 s : refermées dos à dos vers l'arrière, pointes qui remontent
sneak = anim("sneak", 3.0, lambda t: (4, 80 + 1.5 * sn(t, 3.0), 8 + 1 * sn(t, 3.0, 1, -40)), lag=0.05, hind_off=(0, 0, 0), n_kf=12)
# fly 2,4 s : joueur debout, plan basculé ~40°, battement rapide et ample (4 battements)
fly = anim("fly", 2.4, lambda t: (40, 34 - 38 * sn(t, 2.4, 4), 4 + 6 * sn(t, 2.4, 4, -50)), lag=0.06 / 4, n_kf=64)
# fall 1,5 s : demi-basculées (~26°), ouvertes et relevées pour freiner, frémissement
fall = anim("fall", 1.5, lambda t: (26, 14 + 7 * sn(t, 1.5, 2), 10 + 3 * sn(t, 1.5, 2, -60)), lag=0.05, n_kf=24)
# swim 2 s : corps couché, ailes dans le plan du dos rabattues vers les pieds, ondulation
swim = anim("swim", 2.0, lambda t: (4, 22 + 12 * sn(t, 2.0), -24 + 4 * sn(t, 2.0, 1, -60)), lag=0.1, n_kf=20)
# mount 3 s : relevées, respiration ample
mount = anim("mount", 3.0, lambda t: (6, 28 + 10 * sn(t, 3.0), 8 + 3 * sn(t, 3.0, 1, -40)), lag=0.05, n_kf=18)
# sleep 4 s : refermées, tombantes, respiration très lente
sleep = anim("sleep", 4.0, lambda t: (2, 76 + 2 * sn(t, 4.0), -10 + 1.5 * sn(t, 4.0, 1, -40)), lag=0.05, n_kf=12)
# attack / hurt : une fois par-dessus l'état, retour à 0. Attaque = claquement vers l'arrière (vers l'avant, l'aile entrerait dans le bras)
attack = anim("attack", 0.8, lambda t: (8 * bump(t, 0, 0.1, 0.25, 0.7), 30 * bump(t, 0, 0.1, 0.25, 0.7), 8 * bump(t, 0, 0.1, 0.25, 0.7)),
              lag=0.05, hind_off=(0, 0, 0), n_kf=16, loop="once")
hurt = anim("hurt", 0.8, lambda t: (4 * bump(t, 0, 0.08, 0.22, 0.7),
                                    22 * bump(t, 0, 0.08, 0.22, 0.7) + 4 * math.sin(TAU * 5 * t / 0.8) * (1 - sm(t, 0.25, 0.7)),
                                    -4 * bump(t, 0, 0.08, 0.22, 0.7)),
            lag=0.04, hind_off=(0, 0, 0), n_kf=16, loop="once")

# glide 3,6 s : grandes ouvertes presque dans le plan du dos, battement lent, ample à la fusée (forme et constantes d'Aurelion)
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


def glide_anim():
    A = {}
    for s_, tag in ((-1, "l"), (1, "r")):
        sx, sy, sz = mirror(s_, 1, 1, 1)
        for g, ph, zoff in (("fore", 0, 2), ("hind", -30, -2)):
            A[groups[f"{g}_{tag}"]["uuid"]] = {"name": f"{g}_{tag}", "type": "bone", "keyframes": [
                {"channel": "rotation", "data_points": [{"x": mol(sx, 6, (1.5, 90 + ph)), "y": mol(sy, 8, (7, ph), (22, ph * 1.5)),
                                                         "z": f"{sz * zoff:g}"}], "time": 0, "interpolation": "linear"}]}
    return {"uuid": nuid(), "name": "glide", "loop": "loop", "override": False, "length": G, "snapping": 24, "selected": False, "animators": A}


glide = glide_anim()

ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, attack, hurt]
assert len(ANIMS) <= 16
assert 150 <= len(elements) <= 320, f"budget : {len(elements)} cubes"

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", depth(outliner[0]), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      f"densité membrane {DENS:.2f} texels/px")
