"""Bandeau abyssal : bandeau de cuir sur les yeux, regard vert, cornes en crochet, oreilles pointues. Design original, à porter avec ailes_abyssales.
Écrit bandeau_abyssal.png, bandeau_abyssal_e.png et .build/bandeau_abyssal_brut.bbmodel à côté de ce script.

Bande de cuir décollée de la tête, deux fentes vert acide peintes, deux pans déchirés à 3 sections qui flottent à l'arrière ;
deux cornes épaisses à bagues, qui balaient vers l'arrière et reviennent en crochet ; oreilles en peau + âme. Groupe de premier niveau head.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # True : embarque le calque _e en seconde texture. Réactivé le 2026-11-03 (correctif du mod annoncé, à vérifier en jeu).
TEX = 512
TAU = 2 * math.pi

# ------------------------------------------------------------------ matières communes (mêmes teintes que ailes_abyssales)
C_DARK = np.array((17, 7, 26), np.float32)
C_BASE = np.array((42, 16, 60), np.float32)
C_HIGH = np.array((82, 28, 104), np.float32)
C_RIM = np.array((122, 42, 124), np.float32)
C_AURA = np.array((22, 66, 40), np.float32)
C_VEIN = np.array((96, 200, 44), np.float32)
C_VCORE = np.array((150, 244, 70), np.float32)
WM, WB = 0.50, 0.36      # épaisseur (px) d'une veine maîtresse et d'une branche


def lerp(a, b, k):
    return a + (b - a) * k


def along(pts, u):
    """Point au paramètre u (0..1, longueur d'arc) d'une polyligne 2D."""
    ls = [0.0]
    for a, b in zip(pts, pts[1:]):
        ls.append(ls[-1] + math.dist(a, b))
    d = u * ls[-1]
    for i in range(len(pts) - 1):
        if d <= ls[i + 1] or i == len(pts) - 2:
            k = (d - ls[i]) / max(1e-6, ls[i + 1] - ls[i])
            return (lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k))


def ray(a, b, n=24):
    return [(lerp(a[0], b[0], i / n), lerp(a[1], b[1], i / n)) for i in range(n + 1)]


def scallop(p, q, toward, depth, n=24):
    """Bord de membrane entre deux pointes : arc creusé vers un point."""
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    dx, dy = toward[0] - mx, toward[1] - my
    dl = math.hypot(dx, dy)
    c = (mx + dx / dl * depth, my + dy / dl * depth)
    return [((1 - t) ** 2 * p[0] + 2 * t * (1 - t) * c[0] + t * t * q[0], (1 - t) ** 2 * p[1] + 2 * t * (1 - t) * c[1] + t * t * q[1])
            for t in (i / n for i in range(n + 1))]


class Carte:
    """Morceau de membrane peint à plat, en px du modèle ; les plaques viennent y découper leur image."""

    def __init__(self, x0, x1, y0, y1, seed=1, center=(0, 0), rc=20.0, R=18):
        self.x0, self.x1, self.y0, self.y1, self.R = x0, x1, y0, y1, R
        self.GW, self.GH = int(round((x1 - x0) * R)), int(round((y1 - y0) * R))
        gy, gx = np.mgrid[0:self.GH, 0:self.GW]
        self.X, self.Y = x0 + (gx + 0.5) / R, y1 - (gy + 0.5) / R
        self.seed, self.center, self.rc = seed, center, rc
        self.rng = np.random.default_rng(seed)
        self.mask = Image.new("L", (self.GW, self.GH), 0)
        self.vein_img = Image.new("L", (self.GW, self.GH), 0)
        self.core_img = Image.new("L", (self.GW, self.GH), 0)
        self.bone_img = Image.new("L", (self.GW, self.GH), 0)

    def px(self, p):
        return ((p[0] - self.x0) * self.R, (self.y1 - p[1]) * self.R)

    def add(self, poly):
        ImageDraw.Draw(self.mask).polygon([self.px(p) for p in poly], fill=255)

    def cut(self, poly):
        ImageDraw.Draw(self.mask).polygon([self.px(p) for p in poly], fill=0)

    def hole(self, c, rx, ry, ang=0.0):
        pts = []
        for i in range(9):
            a = i / 9 * TAU
            r = self.rng.uniform(0.7, 1.15)
            x, y = rx * r * math.cos(a), ry * r * math.sin(a)
            pts.append((c[0] + x * math.cos(ang) - y * math.sin(ang), c[1] + x * math.sin(ang) + y * math.cos(ang)))
        self.cut(pts)

    def tear(self, arc, t, width, depth, toward):
        p, l, r = along(arc, t), along(arc, max(0.0, t - width)), along(arc, min(1.0, t + width))
        dx, dy = toward[0] - p[0], toward[1] - p[1]
        n = math.hypot(dx, dy)
        dx, dy = dx / n, dy / n
        jog = self.rng.uniform(-0.5, 0.5)
        tipn = (p[0] + dx * depth - dy * jog, p[1] + dy * depth + dx * jog)
        mid = (p[0] + dx * depth * 0.55 + dy * jog * 0.6, p[1] + dy * depth * 0.55 - dx * jog * 0.6)
        out = (p[0] - dx * 2.5, p[1] - dy * 2.5)
        self.cut([l, mid, tipn, (mid[0] + 0.2, mid[1] - 0.2), r, out])

    def vein(self, path, u0=0.0, u1=1.0, w0=WM, w1=WB, wob=0.15, seed=0):
        r = np.random.default_rng(self.seed * 100 + seed)
        n = 14
        ph = r.uniform(0, TAU)
        pts = []
        for i in range(n + 1):
            x, y = along(path, lerp(u0, u1, i / n))
            off = wob * math.sin(i * 0.9 + ph)
            pts.append((x + off * 0.7, y + off * 0.7))
        vd, cd = ImageDraw.Draw(self.vein_img), ImageDraw.Draw(self.core_img)
        for i in range(n):
            w = lerp(w0, w1, (i + 0.5) / n)
            vd.line([self.px(pts[i]), self.px(pts[i + 1])], fill=255, width=max(1, int(round(w * self.R))))
            cd.line([self.px(pts[i]), self.px(pts[i + 1])], fill=255, width=max(1, int(round(w * 0.5 * self.R))))

    def bone(self, pts, width):
        ImageDraw.Draw(self.bone_img).line([self.px(p) for p in pts], fill=255, width=max(1, int(width * self.R)))

    def _blur(self, im, r):
        return np.array(im.filter(ImageFilter.GaussianBlur(r * self.R)), np.float32) / 255

    def _noise(self, cells, seed):
        r = np.random.default_rng(self.seed * 10 + seed)
        a = (r.random((cells, cells)) * 255).astype(np.uint8)
        return np.array(Image.fromarray(a, "L").resize((self.GW, self.GH), Image.BICUBIC), np.float32) / 255

    def finish(self):
        self.M = np.array(self.mask) > 127
        ang = np.arctan2(self.Y - self.center[1], self.X - self.center[0])
        dist = np.hypot(self.X - self.center[0], self.Y - self.center[1])
        blot = self._noise(12, 3) * 0.6 + self._noise(34, 4) * 0.4
        fib = np.sin(ang * 92 + 5 * self._noise(9, 5))
        far = np.clip(dist / self.rc, 0, 1)
        near = np.clip(self._blur(self.bone_img, 1.2) * 1.7, 0, 1)
        k = np.clip((blot - 0.32) * 1.9, 0, 1)[..., None]
        col = lerp(C_BASE, C_HIGH, k * 0.75) * (1 + 0.09 * fib)[..., None]
        col = lerp(col, C_DARK, (near * 0.82)[..., None])
        col = lerp(col, C_HIGH, (far ** 3 * 0.35)[..., None])
        edge = np.clip(1 - self._blur(Image.fromarray(self.M.astype(np.uint8) * 255, "L"), 0.42), 0, 1)
        col = lerp(col, C_RIM, (np.clip((edge - 0.16) * 3.2, 0, 1) * self.M * 0.9)[..., None])
        col = lerp(col, C_AURA, (np.clip(self._blur(self.vein_img, 0.55) * 1.3, 0, 1) * 0.6)[..., None])
        col = lerp(col, C_VEIN, (np.array(self.vein_img) > 127)[..., None] * 1.0)
        core = np.array(self.core_img) > 127
        self.col = lerp(col, C_VCORE, core[..., None] * 1.0).astype(np.float32)
        self.Vc = core & self.M
        return self

    def poly_mask(self, poly):
        im = Image.new("L", (self.GW, self.GH), 0)
        ImageDraw.Draw(im).polygon([self.px(p) for p in poly], fill=255)
        return np.array(im) > 127

    def panel(self, name, poly=None, clip=None, rect=False):
        """Déclare une plaque : son image est la zone de carte couverte par poly et clip."""
        m = self.M.copy() if poly is None else (self.poly_mask(poly) & self.M)
        if clip is not None:
            m &= clip
        p = dict(name=name, carte=self, mask=m)
        if rect:
            p.update(phi=0, w=self.x1 - self.x0, h=self.y1 - self.y0, cx=(self.x0 + self.x1) / 2, cy=(self.y0 + self.y1) / 2)
        else:
            ys, xs = np.nonzero(m[::4, ::4])
            px_, py_ = self.x0 + (xs * 4 + 0.5) / self.R, self.y1 - (ys * 4 + 0.5) / self.R
            best = None
            for deg in range(0, 180, 2):
                c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
                a, b = px_ * c + py_ * s, -px_ * s + py_ * c
                w, h = a.max() - a.min() + 0.5, b.max() - b.min() + 0.5
                if best is None or w * h < best[0]:
                    ca, cb = (a.max() + a.min()) / 2, (b.max() + b.min()) / 2
                    best = (w * h, deg, w, h, ca * c - cb * s, ca * s + cb * c)
            _, p["phi"], p["w"], p["h"], p["cx"], p["cy"] = best
        PANELS.append(p)
        return p


PANELS = []


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
    c = lerp(c, np.array((132, 240, 58), np.float32), np.clip((tt - 0.58) / 0.28, 0, 1)[..., None])
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(((dd < 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    out[~al, :3] = (26, 22, 34)
    te = np.array(Image.fromarray((tt * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS), np.float32)[..., None] / 255
    ec = lerp(np.array((10, 34, 12), np.float32), np.array((156, 255, 84), np.float32), np.clip((te - 0.2) / 0.7, 0, 1))
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
            a[yy, xx, :3] = c_ * (0.9 + 0.2 * math.sin(u * 40 + yy * 0.6))
    a[..., 3] = 255
    return a.astype(np.uint8)


def paint_braise(PT=48):
    """Éclat irrégulier : cœur vif, liseré sombre, une seule silhouette."""
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
tex_b64 = tex_e_b64 = None


def atlas(nom, hook_big=(84, 56), hook_small=(48, 32)):
    """Range toutes les images (densité la plus haute qui tient) et écrit les deux PNG."""
    global tex_b64, tex_e_b64
    hb, hbe = paint_hook(*hook_big)
    hs, hse = paint_hook(*hook_small)
    fixed = [("hook_big", hb), ("hook_small", hs), ("bone", paint_bone()), ("braise", paint_braise())]

    def pack(dens):
        items = [(n, im.shape[1], im.shape[0]) for n, im in fixed] + [(p["name"], int(math.ceil(p["w"] * dens)), int(math.ceil(p["h"] * dens))) for p in PANELS]
        items.sort(key=lambda it: -it[2])
        uv, x, y, shelf = {}, 0, 0, 0
        for n, w, h in items:
            if x + w + 1 > TEX:
                x, y, shelf = 0, y + shelf + 1, 0
            if y + h > TEX - 6 or w > TEX:
                return None
            uv[n] = (x, y, x + w, y + h)
            x += w + 1
            shelf = max(shelf, h)
        return uv

    dens = 12.0
    while (uv := pack(dens)) is None:
        dens -= 0.1
    UV.update(uv)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, im in fixed:
        u0, v0, u1, v1 = UV[n]
        tex[v0:v1, u0:u1] = im
    for n, im in (("hook_big", hbe), ("hook_small", hse)):
        u0, v0, u1, v1 = UV[n]
        tex_e[v0:v1, u0:u1] = im
    for p in PANELS:
        u0, v0, u1, v1 = UV[p["name"]]
        W, H, ct, ss = u1 - u0, v1 - v0, p["carte"], 3
        jj, ii = np.mgrid[0:H * ss, 0:W * ss]
        a, b = ((ii + 0.5) / (W * ss) - 0.5) * p["w"], (0.5 - (jj + 0.5) / (H * ss)) * p["h"]
        c, s = math.cos(math.radians(p["phi"])), math.sin(math.radians(p["phi"]))
        wx, wy = p["cx"] + a * c - b * s, p["cy"] + a * s + b * c
        ix = np.clip(((wx - ct.x0) * ct.R).astype(int), 0, ct.GW - 1)
        iy = np.clip(((ct.y1 - wy) * ct.R).astype(int), 0, ct.GH - 1)
        al = p["mask"][iy, ix].reshape(H, ss, W, ss).mean(axis=(1, 3)) > 0.5
        cc = ct.col[iy, ix].reshape(H, ss, W, ss, 3).mean(axis=(1, 3))
        if al.any():
            cc[~al] = cc[al].mean(axis=0)
        tex[v0:v1, u0:u1, :3] = np.clip(cc, 0, 255).astype(np.uint8)
        tex[v0:v1, u0:u1, 3] = al * 255
        vm = (ct.Vc[iy, ix].reshape(H, ss, W, ss).mean(axis=(1, 3)) > 0.34) & al
        tex_e[v0:v1, u0:u1, :3] = np.array((132, 255, 72), np.uint8) * vm[..., None]
        tex_e[v0:v1, u0:u1, 3] = vm * 255
    assert tex[TEX - 3, TEX - 3, 3] == 0
    tex[..., :3] &= 0xFC
    assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
    b64 = []
    for arr, fn in ((tex, f"{nom}.png"), (tex_e, f"{nom}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        b64.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    tex_b64, tex_e_b64 = b64
    return dens


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


def plate(g, name, c, X, Y, w, h, tile, flip_v=False, th=0.3):
    """Plaque fine : contour par l'alpha, tranches transparentes. u suit X, le haut de l'image est +Y."""
    X, Y = unit(np.asarray(X, float)), unit(np.asarray(Y, float))
    u0, v0, u1, v1 = UV[tile]
    if flip_v:
        v0, v1 = v1, v0
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
         {"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def bar(g, name, p, q, r, u0=0.0, u1=1.0, octo=True, ov=0.1):
    """Tronçon d'os : section octogonale (deux cubes à 45°) ou losange seul."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X = unit(q - p)
    ref = V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0)
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R0 = np.column_stack([X, Y, Z_])
    R45 = np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])
    bu0, bv0, bu1, bv1 = UV["bone"]
    ua = lerp(bu0, bu1, u0)
    ub = max(lerp(bu0, bu1, u1), ua + 2)
    lg = [ua, bv0, ub, bv1]
    end = [ua, bv0 + 3, ua + 2, bv1 - 3]
    faces = {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end}
    if octo:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R0), faces)
        cube(g, name + "o", p + (-ov + 0.03, -r * 0.97, -r * 0.97), p + (L + ov - 0.03, r * 0.97, r * 0.97), p, euler(R45), faces)
    else:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R45), faces)


def chain(g, name, pts, r0, r1, u0=0.0, u1=1.0, octo_until=1.0):
    """Os effilé : tronçons qui se recouvrent, rayon qui décroît, couleur continue."""
    n = len(pts) - 1
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        bar(g, f"{name}{i}", pts[i], pts[i + 1], lerp(r0, r1, (t0 + t1) / 2), lerp(u0, u1, t0), lerp(u0, u1, t1), octo=t1 <= octo_until + 1e-6)


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
        t0, t1 = j / core * 0.72, (j + 1) / core * 0.72
        a, b = center(t0), center(t1)
        bar(g, f"{name}c{j}", p + X * a[0] + Y * a[1], p + X * b[0] + Y * b[1], max(0.16, hw((t0 + t1) / 2) * 0.62), 0.6, 0.9, octo=False, ov=0.06)
    return p + X * center(1)[0] + Y * center(1)[1]


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


def particle():
    """Particule (guide, section 5 ter) : une seule plaque, face up seule, à 0,3 px au-dessus du pivot."""
    g = group("particle_braise", [0, 0, 0])
    w = 3.2
    u0, v0, u1, v1 = UV["braise"]
    cube(g, "braise", [-w / 2, 0.3, -w / 2], [w / 2, 0.6, w / 2], [0, 0, 0], (0, 0, 0), {"up": [u0, v0, u1, v1]})
    return g


# ------------------------------------------------------------------ animations
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


def anim(name, length, tracks, n_kf=None, loop="loop"):
    """tracks : groupe -> fonction t -> (x, y, z) en valeurs de keyframe."""
    n = n_kf or max(6, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]
    A = {groups[g]["uuid"]: {"name": g, "type": "bone", "keyframes": [kf(t, *f(t)) for t in times]} for g, f in tracks.items()}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


def particle_anims(g):
    PF, PR = 3.0, 6.0
    return [anim("particle_braise_fall", PF, {g: lambda t: (24 * math.sin(TAU * t / PF), 360 * t / PF, 18 * math.cos(2 * TAU * t / PF))}, n_kf=24),
            anim("particle_braise_rest", PR, {g: lambda t: (0, 0, 1.2 * math.sin(TAU * t / PR))}, n_kf=12)]


def write(nom, outliner, anims, n_groups, budget, emits, dens):
    assert budget[0] <= len(elements) <= budget[1], f"budget : {len(elements)} cubes"
    textures = [{"name": f"{nom}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
    if AVEC_E:
        textures.append({"name": f"{nom}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
    model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": nom, "resolution": {"width": TEX, "height": TEX},
             "elements": elements, "outliner": outliner, "textures": textures, "animations": anims}
    os.makedirs(".build", exist_ok=True)
    out = f".build/{nom}_brut.bbmodel"
    with open(out, "w") as fh:
        json.dump(model, fh, separators=(",", ":"))

    def depth(n, d=1):
        return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])

    print(len(elements), "cubes ;", n_groups, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(anims), "anims ;",
          sum(len(b["keyframes"]) for a in anims for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
          f"densité {dens:.1f} texels/px ; {emits} emit_ ; {len(PANELS)} images de membrane")

# ------------------------------------------------------------------ bandeau
NOM = "bandeau_abyssal"
BAND = 4.45                 # distance de la bande à l'axe : décollée de la tête (±4)
Y0, Y1 = 25.9, 30.3         # hauteur de la bande : couvre les yeux


class Mat(Carte):
    """Matière non membraneuse : cuir ou peau, selon la palette. Marques claires (coutures), usure, ombres aux découpes."""

    def __init__(self, *a, pal=None, **k):
        super().__init__(*a, **k)
        self.pal = [np.array(c, np.float32) for c in pal]
        self.seam_img = Image.new("L", (self.GW, self.GH), 0)

    def seams(self, a, b, n=6, w=0.22):
        d = ImageDraw.Draw(self.seam_img)
        for i in range(n):
            t0, t1 = (i + 0.2) / n, (i + 0.7) / n
            d.line([self.px((lerp(a[0], b[0], t0), lerp(a[1], b[1], t0))), self.px((lerp(a[0], b[0], t1), lerp(a[1], b[1], t1)))], fill=255, width=max(1, int(w * self.R)))

    def blade(self, pts, core_pts):
        """Trait vert plein : la forme est un polygone, pour des bords nets."""
        ImageDraw.Draw(self.vein_img).polygon([self.px(p) for p in pts], fill=255)
        ImageDraw.Draw(self.core_img).polygon([self.px(p) for p in core_pts], fill=255)

    def finish(self, grain=1.0):
        base, high, rim, ombre, couture = self.pal
        self.M = np.array(self.mask) > 127
        blot = self._noise(9, 3) * 0.55 + self._noise(40, 4) * 0.45
        col = lerp(base, high, (np.clip((blot - 0.34) * 2.1, 0, 1) * 0.8)[..., None])
        col = col * (1 + 0.06 * grain * np.sin(self.Y * 11 + self.X * 3 + 8 * self._noise(14, 5)))[..., None]
        edge = np.clip(1 - self._blur(Image.fromarray(self.M.astype(np.uint8) * 255, "L"), 0.3), 0, 1)
        col = lerp(col, ombre, (np.clip((edge - 0.08) * 3, 0, 1) * 0.5)[..., None])
        col = lerp(col, rim, (np.clip((edge - 0.32) * 6, 0, 1) * self.M * 0.85)[..., None])
        col = lerp(col, couture, (np.array(self.seam_img) > 127)[..., None] * 1.0)
        col = lerp(col, C_AURA, (np.clip(self._blur(self.vein_img, 0.34) * 1.4, 0, 1) * 0.72)[..., None])
        col = lerp(col, C_VEIN, (np.array(self.vein_img) > 127)[..., None] * 1.0)
        core = np.array(self.core_img) > 127
        self.col = lerp(col, np.array((190, 255, 96), np.float32), core[..., None] * 1.0).astype(np.float32)
        self.Vc = core & self.M
        return self


CUIR = [(24, 12, 30), (60, 28, 72), (100, 56, 112), (8, 4, 11), (88, 72, 100)]
PEAU = [(122, 104, 134), (170, 152, 178), (88, 66, 104), (54, 40, 70), (150, 130, 160)]


def torn(ct, x0, x1, top, bot, points, seed):
    """Bande dont les bords haut et bas sont usés, avec quelques encoches ; points = position relative sur le bord."""
    r = np.random.default_rng(seed)
    up, dn = [], []
    n = 12
    for i in range(n + 1):
        x = lerp(x0, x1, i / n)
        up.append((x, top - r.uniform(0, 0.14)))
        dn.append((x, bot + r.uniform(0, 0.14)))
    ct.add(up + list(reversed(dn)))
    for side, t, w, d_ in points:
        x = lerp(x0, x1, t)
        y = top if side > 0 else bot
        ct.cut([(x - w, y + side * 0.3), (x + w, y + side * 0.3), (x + 0.1 * w, y - side * d_)])


# Face : deux fentes vert acide, très nettes
L_F = BAND + 0.45
fr = Mat(-L_F, L_F, Y0 - 0.1, Y1 + 0.1, seed=81, pal=CUIR)
torn(fr, -L_F, L_F, Y1, Y0, [(1, 0.12, 0.28, 0.5), (1, 0.84, 0.32, 0.7), (-1, 0.3, 0.3, 0.75), (-1, 0.78, 0.26, 0.45)], 1)
for sg in (1, -1):
    # fente : pointe intérieure basse, extérieure haute ; 8–9 texels de haut au milieu
    fr.blade([(sg * 0.55, 27.85), (sg * 1.35, 28.5), (sg * 3.45, 28.72), (sg * 3.05, 27.95), (sg * 1.5, 27.72)],
             [(sg * 0.95, 27.98), (sg * 1.5, 28.28), (sg * 3.05, 28.48), (sg * 2.8, 28.12), (sg * 1.55, 27.92)])
fr.seams((-L_F + 0.4, Y1 - 0.45), (L_F - 0.4, Y1 - 0.45), n=11)
fr.seams((-L_F + 0.4, Y0 + 0.45), (L_F - 0.4, Y0 + 0.45), n=11)
fr.finish()
fr.panel("band_f", rect=True)

# Côtés et dos : même bande, usée, sans regard
for name, sd, pts in (("band_c", 82, [(1, 0.25, 0.3, 0.6), (-1, 0.62, 0.3, 0.7)]), ("band_d", 83, [(1, 0.7, 0.3, 0.55), (-1, 0.2, 0.3, 0.6)])):
    ct = Mat(-L_F, L_F, Y0 - 0.1, Y1 + 0.1, seed=sd, pal=CUIR)
    torn(ct, -L_F, L_F, Y1, Y0, pts, sd)
    ct.seams((-L_F + 0.4, Y1 - 0.45), (L_F - 0.4, Y1 - 0.45), n=11)
    ct.seams((-L_F + 0.4, Y0 + 0.45), (L_F - 0.4, Y0 + 0.45), n=11)
    ct.finish()
    ct.panel(name, rect=True)

# Pli : petite bande posée par-dessus, elle cache la racine de l'oreille et donne de l'épaisseur
pli = Mat(-1.5, 1.5, -2.0, 2.0, seed=84, pal=CUIR)
pli.add([(-1.35, 1.8), (1.3, 1.9), (1.4, -1.7), (0.3, -1.25), (-1.3, -1.85)])
pli.seams((-1.0, 1.4), (-1.0, -1.4), n=4)
pli.finish()
pli.panel("pli", rect=True)

# Nœud du dos
noeud = Mat(-1.6, 1.6, -1.3, 1.3, seed=85, pal=CUIR)
noeud.add([(-1.5, 0.4), (-0.5, 1.15), (0.7, 1.05), (1.5, 0.3), (1.1, -1.0), (-0.9, -1.15)])
noeud.seams((-1.0, 0.0), (1.0, 0.1), n=4)
noeud.finish()
noeud.panel("noeud", rect=True)

# Pans déchirés : trois sections, chacune avec son image. Coordonnées locales : y descend depuis l'articulation.
PAN = [(2.5, 2.2, 5.0), (2.2, 1.75, 4.8), (1.75, 0.9, 4.6)]
for j, (w0, w1, h) in enumerate(PAN):
    ct = Mat(-1.4, 1.4, -h - 0.1, 0.5, seed=86 + j, pal=CUIR)
    if j < 2:
        ct.add([(-w0 / 2, 0.4), (w0 / 2, 0.4), (w1 / 2, -h), (-w1 / 2, -h)])
    else:
        ct.add([(-w0 / 2, 0.4), (w0 / 2, 0.4), (w1 / 2 + 0.1, -h * 0.7), (0.35, -h * 0.85), (0.2, -h), (-0.15, -h * 0.72), (-w1 / 2, -h * 0.92)])
    for i, (sd_, yy, d_) in enumerate(((1, -h * 0.3, 0.65), (-1, -h * 0.68, 0.5))):
        x = sd_ * lerp(w0, w1, -yy / h) / 2
        ct.cut([(x + sd_ * 0.2, yy + 0.3), (x + sd_ * 0.2, yy - 0.3), (x - sd_ * d_, yy)])
    if j == 1:
        ct.hole((0.15, -h * 0.5), 0.3, 0.42)
    ct.finish()
    ct.panel(f"pan{j}", rect=True)

# Oreille : longue feuille pointue, encoche déchirée. u = de la racine vers la pointe.
EL, EH = 7.6, 2.6
ear = Mat(-0.1, EL + 0.1, -EH / 2 - 0.1, EH / 2 + 0.1, seed=89, pal=PEAU)
ear.add([(0, 0.5), (1.6, 1.15), (3.4, 1.25), (5.6, 0.75), (EL, 0.28), (5.6, -0.25), (3.4, -0.75), (1.4, -0.95), (0, -0.55)])
ear.cut([(3.1, 1.5), (3.8, 1.5), (3.5, 0.5)])
ear.cut([(5.05, -0.6), (5.5, -0.6), (5.1, 0.05)])
ear.finish(grain=0.5)
ear.panel("oreille", rect=True)

DENS = atlas(NOM)

# ------------------------------------------------------------------ géométrie
EMITS = []


def emit(parent, at):
    EMITS.append(group("emit_braise" + (str(len(EMITS) + 1) if EMITS else ""), at, parent=parent))


YC = (Y0 + Y1) / 2
PH = Y1 - Y0 + 0.2
bande = group("bande", [0, YC, 0])
PW = 2 * L_F
plate(bande, "bande_f", V(0, YC, -BAND), V(1, 0, 0), V(0, 1, 0), PW, PH, "band_f")
plate(bande, "bande_d", V(0, YC, BAND + 0.03), V(-1, 0, 0), V(0, 1, 0), PW, PH, "band_d")
plate(bande, "bande_e", V(BAND + 0.06, YC, 0), V(0, 0, -1), V(0, 1, 0), PW, PH, "band_c")
plate(bande, "bande_w", V(-BAND - 0.06, YC, 0), V(0, 0, 1), V(0, 1, 0), PW, PH, "band_c")
# clous d'os, discrets, sur le haut de la bande
for i, x in enumerate((-3.6, -1.2, 1.2, 3.6)):
    bar(bande, f"clou_f{i}", V(x - 0.22, Y1 - 0.75, -BAND - 0.3), V(x + 0.22, Y1 - 0.75, -BAND - 0.3), 0.2, 0.2, 0.3, octo=False, ov=0.0)
for s_, tag in ((-1, "l"), (1, "r")):
    plate(bande, f"pli_{tag}", V(s_ * (BAND + 0.42), YC - 0.1, 0.7), V(0, 0, 1), V(0, 1, 0), 3.0, 4.0, "pli")
    bar(bande, f"clou_{tag}", V(s_ * (BAND + 0.62), Y1 - 0.9, 0.2), V(s_ * (BAND + 0.62), Y1 - 0.9, 0.7), 0.2, 0.2, 0.3, octo=False, ov=0.0)
plate(bande, "noeud", V(0, 28.3, BAND + 0.34), V(1, 0, 0), V(0, 1, 0), 3.2, 2.6, "noeud")
bar(bande, "boucle", V(-0.75, 28.25, BAND + 0.6), V(0.75, 28.25, BAND + 0.6), 0.34, 0.15, 0.3, octo=True, ov=0.0)
emit(bande, V(0.0, 28.2, -BAND - 0.4))

# Pans : trois sections articulées, derrière le nœud. Le droit pend un peu plus bas et un peu plus écarté.
PANS = []
for s_, tag, drop, rx in ((-1, "l", 0.0, 7), (1, "r", -0.5, 11)):
    parent = None
    y = 27.8 + drop
    for j, (_, _, h) in enumerate(PAN):
        g = group(f"pan{j}_{tag}", [s_ * 1.05, y, BAND + 0.55 + 0.04 * j], parent=parent, rotation=(-rx if j == 0 else -3, 0, s_ * 6 if j == 0 else 0))
        plate(g, f"mpan{j}_{tag}", V(s_ * 1.05, y + (0.5 - h - 0.1) / 2, BAND + 0.55 + 0.04 * j), V(s_, 0, 0), V(0, 1, 0), 2.8, h + 0.6, f"pan{j}")
        PANS.append((g, s_, j))
        parent = g
        y -= h - 0.1


# Cornes : base épaisse sur le dessus de la tête, au-dessus des tempes ; balaient vers l'arrière, puis les pointes reviennent vers l'avant en crochet
SEGL = [2.7, 2.6, 2.4, 2.2, 2.0, 1.8, 1.6]
RAD = [lerp(1.5, 0.48, (i / (len(SEGL) - 1)) ** 0.8) for i in range(len(SEGL))]
HORN_TIP = []
for s_, tag in ((-1, "l"), (1, "r")):
    p = V(s_ * 3.0, 34.35, -1.2)
    ang = 30.0
    xd = 0.5
    pts = [p]
    for i, L_ in enumerate(SEGL):
        d_ = unit(V(s_ * xd, math.sin(math.radians(ang)), math.cos(math.radians(ang))))
        pts.append(pts[-1] + d_ * L_)
        ang += 23 + 3 * i
        xd *= 0.72
    g0 = group(f"corne_{tag}", pts[0])
    g1 = group(f"corne_bout_{tag}", pts[5], parent=g0)
    HORN_TIP.append((g1, s_))
    for i in range(len(SEGL)):
        tgt = g0 if i < 5 else g1
        bar(tgt, f"corne{i}_{tag}", pts[i], pts[i + 1], RAD[i], 0.05 + i * 0.12, 0.05 + (i + 1) * 0.12, octo=True, ov=0.1)
        if i < len(SEGL) - 1:
            # bague de nervure, à chaque jointure
            d_ = unit(pts[i + 1] - pts[i])
            bar(tgt, f"bague{i}_{tag}", pts[i + 1] - d_ * 0.32, pts[i + 1] + d_ * 0.1, RAD[i] + 0.12, 0.42, 0.48, octo=True, ov=0.0)
    # socle : court, posé sur le crâne, juste sous la base de la corne
    bar(g0, f"socle_{tag}", V(s_ * 3.0, 32.15, -1.2), V(s_ * 3.0, 34.7, -1.2), 1.25, 0.0, 0.03, octo=True, ov=0.0)
    d_end = unit(pts[-1] - pts[-2])
    end = hook(g1, f"pointe_{tag}", pts[-1] - d_end * 0.15, d_end, V(0, -1, 0.2), 3.6, "hook_big", core=2)
    emit(g1, end)

# Oreilles : sortent de sous le pli vers l'arrière et un peu vers le haut
EARS = []
for s_, tag in ((-1, "l"), (1, "r")):
    root = V(s_ * (BAND + 0.2), 28.1, 0.4)
    X_ = unit(V(s_ * 0.58, 0.3, 0.76))
    Y_ = unit(V(0, 1, 0) - (V(0, 1, 0) @ X_) * X_)
    g = group(f"oreille_{tag}", root)
    EARS.append((g, s_))
    plate(g, f"peau_{tag}", root + X_ * (EL / 2), X_, Y_, EL + 0.2, EH + 0.2, "oreille")
    bar(g, f"ame0_{tag}", root + Y_ * 0.05, root + X_ * 2.4 + Y_ * 0.15, 0.24, 0.1, 0.2, octo=False, ov=0.05)
    bar(g, f"ame1_{tag}", root + X_ * 2.3 + Y_ * 0.15, root + X_ * 4.2 + Y_ * 0.12, 0.16, 0.1, 0.2, octo=False, ov=0.05)
    for k, u_ in enumerate((1.7, 2.6)):
        bar(g, f"anneau{k}_{tag}", root + X_ * u_ + Y_ * 0.15, root + X_ * (u_ + 0.45) + Y_ * 0.15, 0.4 - 0.05 * k, 0.5, 0.6, octo=True, ov=0.0)

PG = particle()
outliner = [{"name": "head", "origin": [0, 24, 0], "uuid": nuid(),
             "children": [bone_node(bande)] + [bone_node(f"pan0_{t}") for t in "lr"] + [bone_node(f"corne_{t}") for t in "lr"] + [bone_node(f"oreille_{t}") for t in "lr"]},
            bone_node(PG)]


# ------------------------------------------------------------------ animations
# Intention sur un côté s (-1 gauche, +1 droit) : swing > 0 écarte vers l'arrière ce qui pend ; back > 0 ramène l'oreille vers l'arrière ; up > 0 relève.
# MIROIR D'AXES : seul endroit à toucher si la convention du mod change. Guide, section 3 : +X = le haut part vers l'arrière, donc ce qui pend avance ;
# +Y = le côté droit avance ; +Z = le côté droit monte.
SX, SY, SZ = -1, -1, +1


def mirror(s, swing, back, up):
    return SX * swing, s * SY * back, s * SZ * up


def state(name, L, swing, amp, sway, ear_b, ear_up, n_kf=None, cycles=1):
    """swing : écart de chaque section ; amp, sway : flottement, en cascade le long du pan ; oreilles discrètes."""
    tr = {}
    for g, s_, j in PANS:
        def f(t, s_=s_, j=j):
            ph = TAU * (cycles * t / L - 0.13 * j - (0.08 if s_ > 0 else 0))
            return mirror(s_, swing[j] + amp * (0.6 + 0.4 * j) * math.sin(ph), 0, sway * (0.6 + 0.4 * j) * math.sin(ph + 1.1))
        tr[g] = f
    for g, s_ in EARS:
        def e(t, s_=s_):
            ph = TAU * (cycles * t / L + (0.1 if s_ > 0 else 0))
            return mirror(s_, 0, ear_b + 0.5 * ear_up * math.sin(ph), ear_up * math.sin(ph + 0.8))
        tr[g] = e
    return anim(name, L, tr, n_kf=n_kf)


idle = state("idle", 8.0, (1, 1, 1), 1.4, 1.2, 0, 1.0, n_kf=32, cycles=2)
walk = state("walk", 1.6, (9, 7, 6), 2.5, 2.5, 2, 1.0)
run = state("run", 1.0, (24, 14, 10), 4.5, 4.0, 6, 1.4)
sneak = state("sneak", 3.0, (0, 1, 1), 0.8, 0.8, -1, 0.5)
fly = state("fly", 2.4, (36, 16, 10), 5, 5, 8, 1.2, n_kf=20)
glide = state("glide", 3.6, (46, 14, 8), 4, 5, 10, 1.2, n_kf=28, cycles=2)

# attack et hurt : peu de groupes, dernière image à zéro
atk = lambda t: bump(t, 0.0, 0.1, 0.24, 0.68)
hu = lambda t: bump(t, 0.0, 0.07, 0.18, 0.66)
vib = lambda t: math.sin(TAU * t * 5 / 0.8) * (1 - sm(t, 0.2, 0.7))
tr_a, tr_h = {}, {}
for g, s_ in EARS:
    tr_a[g] = (lambda s_: (lambda t: mirror(s_, 0, 14 * atk(t), -4 * atk(t))))(s_)
    tr_h[g] = (lambda s_: (lambda t: mirror(s_, 0, 10 * hu(t), 5 * vib(t) * hu(t))))(s_)
for g, s_, j in PANS:
    if j == 0:
        tr_a[g] = (lambda s_: (lambda t: mirror(s_, 22 * atk(t), 0, 0)))(s_)
        tr_h[g] = (lambda s_: (lambda t: mirror(s_, 12 * hu(t), 0, 3 * vib(t) * hu(t))))(s_)
attack = anim("attack", 0.8, tr_a, n_kf=16, loop="once")
hurt = anim("hurt", 0.8, tr_h, n_kf=16, loop="once")

ANIMS = [idle, walk, run, sneak, fly, glide, attack, hurt] + particle_anims(PG)
assert 2 <= len(EMITS) <= 3
write(NOM, outliner, ANIMS, len(groups) + 1, (80, 200), len(EMITS), DENS)
