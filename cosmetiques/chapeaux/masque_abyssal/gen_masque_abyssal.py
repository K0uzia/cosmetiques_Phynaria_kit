"""Masque abyssal : masque démoniaque à grandes cornes (os charbon à reflets violacés, fissures vert acide). Design original, à porter avec ailes_abyssales.
Écrit masque_abyssal.png, masque_abyssal_e.png et .build/masque_abyssal_brut.bbmodel à côté de ce script.

Plaques d'os découpées par alpha (face, nez, mâchoire, tempes, front), orbites percées pour laisser voir les yeux du skin,
arêtes en volumes effilés, sangles vers la nuque sans casque complet. Deux grandes cornes et deux petites. Groupe de premier niveau head.
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
    # Particules qui tombent et se posent : réservées aux ailes (.claude/rules/retours-en-jeu.md).
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
    from particules import retirer_particules
    retirer_particules(model)
    with open(out, "w") as fh:
        json.dump(model, fh, separators=(",", ":"))

    def depth(n, d=1):
        return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])

    print(len(elements), "cubes ;", n_groups, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(anims), "anims ;",
          sum(len(b["keyframes"]) for a in anims for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
          f"densité {dens:.1f} texels/px ; {emits} emit_ ; {len(PANELS)} images de membrane")

# ------------------------------------------------------------------ masque
NOM = "masque_abyssal"
C_CHAR = np.array((28, 24, 36), np.float32)
C_CHAR2 = np.array((58, 48, 76), np.float32)
C_REFLET = np.array((116, 86, 156), np.float32)
C_OMBRE = np.array((11, 8, 16), np.float32)


class Os(Carte):
    """Plaque d'os : charbon à reflets violacés, liseré clair, ombre autour des découpes, fissures vert acide."""

    def finish(self):
        self.M = np.array(self.mask) > 127
        blot = self._noise(10, 3) * 0.6 + self._noise(30, 4) * 0.4
        col = lerp(C_CHAR, C_CHAR2, np.clip((blot - 0.3) * 1.8, 0, 1)[..., None])
        # reflet : bande oblique, plus claire vers le haut, stries fines de l'os
        band = np.clip(1 - np.abs((self.Y - self.y0) / (self.y1 - self.y0) - 0.68) * 3.2, 0, 1)
        col = lerp(col, C_REFLET, (band * 0.34 * np.clip(blot * 1.5, 0, 1))[..., None])
        col = col * (1 + 0.07 * np.sin(self.Y * 7 + self.X * 2 + 6 * self._noise(8, 5)))[..., None]
        edge = np.clip(1 - self._blur(Image.fromarray(self.M.astype(np.uint8) * 255, "L"), 0.3), 0, 1)
        col = lerp(col, C_OMBRE, (np.clip((edge - 0.1) * 3, 0, 1) * 0.65)[..., None])
        col = lerp(col, C_REFLET, (np.clip((edge - 0.34) * 6, 0, 1) * self.M * 0.8)[..., None])
        col = lerp(col, C_AURA, (np.clip(self._blur(self.vein_img, 0.3) * 1.2, 0, 1) * 0.55)[..., None])
        col = lerp(col, C_VEIN, (np.array(self.vein_img) > 127)[..., None] * 1.0)
        core = np.array(self.core_img) > 127
        self.col = lerp(col, C_VCORE, core[..., None] * 1.0).astype(np.float32)
        self.Vc = core & self.M
        return self


def sym(right):
    """Contour complet à partir de la moitié droite, du haut au bas de l'axe."""
    return right + [(-x, y) for x, y in reversed(right) if abs(x) > 1e-6]


def crack(ct, pts, w0=0.3, w1=0.22, seed=0):
    """Fissure sur les deux moitiés : ligne brisée, pas de courbe douce."""
    ct.vein(pts, 0, 1, w0, w1, wob=0.05, seed=seed)
    ct.vein([(-x, y) for x, y in pts], 0, 1, w0, w1, wob=0.05, seed=seed + 50)


ORBIT = [(0.75, 27.0), (2.1, 26.55), (3.55, 28.5), (3.45, 29.45), (1.9, 29.05), (0.6, 28.45)]
# Plaque de face : pic du front, joues, pointes de mâchoire ; la bouche reste ouverte
face = Os(-4.8, 4.8, 24.4, 33.6, seed=71)
face.add(sym([(0, 33.4), (1.2, 32.2), (2.6, 33.0), (4.25, 31.9), (4.65, 29.6), (4.4, 27.2), (4.2, 25.0), (2.9, 24.7), (1.7, 25.5), (0.9, 24.9), (0, 25.5)]))
for sg in (1, -1):
    face.cut([(sg * x, y) for x, y in ORBIT])
    # orbite : anneau vert, juste autour de la découpe
    ring = [(sg * (x + (0.22 if x > 2 else -0.05)), y + (0.25 if y > 28 else -0.25)) for x, y in ORBIT]
    face.vein(ring + [ring[0]], 0, 1, 0.22, 0.22, wob=0.0, seed=2 if sg > 0 else 3)
crack(face, [(3.55, 29.8), (3.1, 30.5), (3.45, 31.0), (2.9, 31.9), (2.6, 32.7)], seed=4)
crack(face, [(0.6, 29.1), (0.95, 30.0), (0.45, 30.8), (0.8, 31.6)], 0.26, 0.22, seed=5)
crack(face, [(2.9, 26.3), (3.4, 25.9), (3.1, 25.3)], 0.26, 0.22, seed=6)
face.finish()
face.panel("face", rect=True)

# Nez : volume en avant, deux narines percées
nez = Os(-1.1, 1.1, 25.5, 30.0, seed=72)
nez.add(sym([(0, 29.8), (0.55, 28.6), (1.0, 26.6), (0.7, 25.8), (0, 25.6)]))
nez.cut([(0.2, 26.3), (0.6, 26.45), (0.5, 26.9), (0.25, 26.8)])
nez.cut([(-0.2, 26.3), (-0.6, 26.45), (-0.5, 26.9), (-0.25, 26.8)])
nez.vein([(0, 29.3), (0.18, 28.4), (-0.12, 27.7)], 0, 1, 0.24, 0.22, wob=0.0, seed=1)
nez.finish()
nez.panel("nez", rect=True)

# Mâchoire : portée par son propre groupe, elle s'ouvre à l'attaque
jaw = Os(-0.1, 2.6, 22.2, 27.0, seed=73)
jaw.add([(0.0, 26.8), (2.3, 26.4), (2.5, 25.0), (1.5, 22.4), (0.7, 24.3)])
jaw.vein([(1.8, 26.3), (1.25, 25.3), (1.65, 24.6), (1.5, 23.5)], 0, 1, 0.28, 0.22, wob=0.0, seed=1)
jaw.finish()
jaw.panel("jaw", rect=True)

# Tempe : plaque qui longe le côté de la tête vers l'arrière, percée et découpée ; u = vers l'arrière
tempe = Os(-0.1, 5.6, 24.8, 32.3, seed=74)
tempe.add([(0, 25.0), (1.6, 27.4), (3.3, 27.9), (4.0, 28.9), (5.4, 29.4), (5.4, 31.1), (3.4, 31.2), (2.4, 32.0), (0, 32.1)])
tempe.hole((2.5, 29.8), 0.55, 0.38, 0.4)
tempe.vein([(0.5, 30.6), (1.3, 30.0), (1.5, 29.1), (2.2, 28.7), (3.3, 28.7)], 0, 1, 0.28, 0.22, wob=0.0, seed=1)
tempe.finish()
tempe.panel("tempe", rect=True)

# Dessus du front : petite plaque d'attache des petites cornes, sans casque
front = Os(-3.6, 3.6, -0.1, 4.0, seed=75)
front.add(sym([(0, 3.7), (1.4, 3.2), (3.3, 2.0), (3.5, 0.0), (0, 0.0)]))
crack(front, [(1.8, 0.2), (1.5, 1.2), (2.1, 2.2)], 0.26, 0.22, seed=1)
front.finish()
front.panel("front", rect=True)

DENS = atlas(NOM)

# ------------------------------------------------------------------ géométrie
ZF = -4.42
masque = group("masque", [0, 28, ZF])
mach = group("machoire", [0, 26.6, ZF - 0.3])
plate(masque, "face", V(0, 29.0, ZF), V(1, 0, 0), V(0, 1, 0), 9.6, 9.2, "face")
plate(masque, "nez", V(0, 27.75, ZF - 0.5), V(1, 0, 0), V(0, 1, 0), 2.2, 4.5, "nez")
for s_, tag in ((-1, "l"), (1, "r")):
    # Mâchoire : plaque inclinée vers l'arrière sur le côté, épouse la joue
    X_ = V(s_ * math.cos(math.radians(18)), 0, math.sin(math.radians(18)))
    o = V(s_ * 2.05, 0, ZF - 0.72)
    plate(mach, f"jaw_{tag}", o + X_ * 1.25 + V(0, 24.6, 0), X_, V(0, 1, 0), 2.7, 4.8, "jaw")
    chain(mach, f"mand_{tag}_", [V(s_ * 4.42, 26.2, -4.72), V(s_ * 4.25, 25.0, -4.82), V(s_ * 3.75, 23.9, -5.0), V(s_ * 3.2, 22.9, -5.15)], 0.36, 0.2, 0.2, 0.7, octo_until=0.34)
    hook(mach, f"pique_{tag}", V(s_ * 3.2, 23.0, -5.15), V(-s_ * 0.2, -1, -0.15), V(-s_, 0, 0), 3.0, core=1)
    # crocs de la lèvre supérieure, portés par le masque
    hook(masque, f"croc_{tag}", V(s_ * 0.85, 25.35, -4.85), V(0, -1, -0.12), V(-s_, 0, 0), 2.8, core=2)
    hook(masque, f"crocb_{tag}", V(s_ * 1.85, 25.7, -4.95), V(0, -1, -0.1), V(-s_, 0, 0), 1.9, core=1)
    # arcades
    chain(masque, f"arcade_{tag}_", [V(s_ * 0.4, 29.2, -5.0), V(s_ * 1.6, 29.7, -5.15), V(s_ * 3.0, 30.25, -5.05), V(s_ * 4.55, 31.5, -4.75)], 0.42, 0.24, 0.05, 0.3)
    # pommette
    chain(masque, f"pommette_{tag}_", [V(s_ * 4.5, 27.4, -4.75), V(s_ * 3.3, 26.45, -4.95), V(s_ * 2.2, 26.1, -5.0)], 0.3, 0.2, 0.3, 0.5, octo_until=0.5)
    # tempe et lanières vers l'arrière : pas de casque, juste deux sangles d'os
    plate(masque, f"tempe_{tag}", V(s_ * 4.46, 28.55, -4.3 + 2.75), V(0, 0, 1), V(0, 1, 0), 5.7, 7.5, "tempe")
    chain(masque, f"sangle_{tag}_", [V(s_ * 4.68, 30.3, -0.3), V(s_ * 4.72, 30.2, 1.6), V(s_ * 4.72, 30.0, 3.4), V(s_ * 4.6, 29.9, 4.65)], 0.3, 0.26, 0.2, 0.4, octo_until=0)
    chain(masque, f"sangleb_{tag}_", [V(s_ * 4.68, 28.1, -1.2), V(s_ * 4.72, 28.5, 1.4), V(s_ * 4.6, 29.4, 4.6)], 0.24, 0.22, 0.4, 0.5, octo_until=0)
chain(masque, "nuque_", [V(-4.7, 29.9, 4.68), V(-1.6, 30.1, 4.76), V(1.6, 30.1, 4.76), V(4.7, 29.9, 4.68)], 0.3, 0.3, 0.2, 0.3, octo_until=0)
# nez et front : arêtes pleines
chain(masque, "arete_", [V(0, 29.8, -5.05), V(0, 28.6, -5.45), V(0, 27.4, -5.75), V(0, 26.5, -5.7)], 0.42, 0.24, 0.1, 0.4)
chain(masque, "crete_", [V(0, 33.2, -4.85), V(0, 31.8, -5.0), V(0, 30.2, -5.1)], 0.16, 0.3, 0.3, 0.1)
# plaque du dessus : du front vers le sommet du crâne
Yf = unit(V(0, 0.12, 1))
plate(masque, "front", V(0, 32.42, ZF + 0.12) + Yf * 1.95, V(1, 0, 0), Yf, 7.2, 4.1, "front")

EMITS = []


def emit(parent, at):
    EMITS.append(group("emit_braise" + (str(len(EMITS) + 1) if EMITS else ""), at, parent=parent))


def arc3d(p, d, steps, turn):
    """Trajet : la direction tourne pas à pas. turn(i) -> ajout à la direction ; longueur(i) dans steps."""
    pts = [np.asarray(p, float)]
    d = np.asarray(d, float)
    for i, L_ in enumerate(steps):
        d = unit(d + turn(i))
        pts.append(pts[-1] + d * L_)
    return pts, d


# Grandes cornes : sortent des tempes, partent vers l'extérieur et l'arrière, puis montent
TIPS = []
HORN_ROOT, HORN_TIP, MID = [], [], []
BIG = [3.1, 3.0, 2.8, 2.6, 2.4, 2.2, 2.0, 1.8, 1.5]
for s_, tag in ((-1, "l"), (1, "r")):
    pts, d_end = arc3d(V(s_ * 5.3, 30.7, -1.5), V(s_ * 0.8, 0.28, 0.5), BIG,
                       lambda i: V(-s_ * 0.11, 0.06 + 0.075 * i, 0.10 - 0.03 * i))
    g0 = group(f"corne_{tag}", pts[0])
    g1 = group(f"corne_mi_{tag}", pts[6], parent=g0)
    g2 = group(f"corne_bout_{tag}", pts[8], parent=g1)
    HORN_ROOT.append(g0)
    MID.append((g1, s_))
    HORN_TIP.append((g2, s_))
    R_ = [lerp(1.32, 0.4, (i / 8) ** 0.85) for i in range(9)]
    for i in range(9):
        tgt = g0 if i < 6 else (g1 if i < 8 else g2)
        bar(tgt, f"corne{i}_{tag}", pts[i], pts[i + 1], R_[i], 0.05 + i * 0.09, 0.05 + (i + 1) * 0.09, octo=i < 7, ov=0.12)
    # attache : renflement entre la tempe et la corne, en dehors de la tête
    bar(g0, f"socle_{tag}", V(s_ * 4.72, 30.5, -1.75), pts[0] + V(s_ * 0.5, 0.15, 0.3), 0.72, 0.0, 0.05, octo=True, ov=0.05)
    end = hook(g2, f"pointe_{tag}", pts[9], d_end, V(s_ * 0.5, -0.1, 0.8), 5.2, "hook_big", core=3)
    TIPS.append((g2, end))

# Petites cornes : sur le front, courtes, tournées vers l'arrière
SMALL_TIP = []
for s_, tag in ((-1, "l"), (1, "r")):
    pts, d_end = arc3d(V(s_ * 2.1, 33.1, -2.5), V(s_ * 0.3, 0.9, -0.1), [1.7, 1.6, 1.4, 1.2],
                       lambda i: V(0, -0.02, 0.26))
    g = group(f"petite_{tag}", pts[0])
    g2 = group(f"petite_bout_{tag}", pts[3], parent=g)
    SMALL_TIP.append((g2, s_))
    chain(g, f"pc_{tag}_", pts[:4], 0.56, 0.3, 0.1, 0.6, octo_until=0.67)
    bar(g2, f"pcb_{tag}", pts[3], pts[4], 0.24, 0.6, 0.8, octo=False, ov=0.06)
    e_ = hook(g2, f"ppointe_{tag}", pts[4], d_end, V(0, -0.3, 1), 2.6, core=1)
    if s_ < 0:
        SMALL_END = (g2, e_)

emit(*TIPS[0])
emit(*TIPS[1])
emit(*SMALL_END)

PG = particle()
outliner = [{"name": "head", "origin": [0, 24, 0], "uuid": nuid(),
             "children": [bone_node(masque), bone_node(mach)] + [bone_node(g) for g in HORN_ROOT] + [bone_node(f"petite_{t}") for t in "lr"]},
            bone_node(PG)]


# ------------------------------------------------------------------ animations
# Les cornes sont rigides : seules leurs pointes oscillent, de quelques degrés. Guide, section 3 : +X = le haut part vers l'arrière.
# MIROIR D'AXES : seul endroit à toucher si la convention du mod change.
SX, SZ = +1, +1


def mirror(s, back, out):
    """back > 0 : vers l'arrière ; out > 0 : vers l'extérieur du côté s (-1 gauche, +1 droite)."""
    return SX * back, 0, s * SZ * -out


def tracks(back, out, jaw_x=None, T=1.0):
    tr = {}
    for w, lst in ((0.5, MID), (1.0, HORN_TIP), (1.0, SMALL_TIP)):
        for g, s_ in lst:
            tr[g] = (lambda w, s_: (lambda t: mirror(s_, w * back(t), w * out(t))))(w, s_)
    if jaw_x:
        tr[mach] = lambda t: (jaw_x(t), 0, 0)
    return tr


def state(name, L, a_back, off, a_out, jaw=None, n_kf=None):
    return anim(name, L, tracks(S(L, a_back, 0, off), S(L, a_out, 70), jaw), n_kf=n_kf)


idle = state("idle", 8.0, 0.8, 0, 0.6, S(8, 0.5, 0, 0.5), n_kf=24)
walk = state("walk", 1.6, 1.0, 0, 0.8)
run = state("run", 1.0, 1.4, 2.0, 1.0)
sneak = state("sneak", 3.0, 0.5, -0.5, 0.4)
fly = state("fly", 2.4, 1.8, 3.0, 1.2, n_kf=20)
glide = state("glide", 3.6, 2.0, 4.0, 1.4, n_kf=28)

# attack et hurt : peu de groupes, dernière image à zéro. Attaque : la mâchoire s'ouvre ; blessé : les pointes tremblent.
atk = lambda t: bump(t, 0.0, 0.1, 0.26, 0.7)
hu = lambda t: bump(t, 0.0, 0.07, 0.2, 0.68)
vib = lambda t: math.sin(TAU * t * 5 / 0.8) * (1 - sm(t, 0.2, 0.7))
attack = anim("attack", 0.8, {mach: lambda t: (11 * atk(t), 0, 0), **{g: (lambda s_: (lambda t: mirror(s_, -3 * atk(t), 2 * atk(t))))(s_) for g, s_ in HORN_TIP}}, n_kf=16, loop="once")
hurt = anim("hurt", 0.8, {mach: lambda t: (5 * hu(t), 0, 0), **{g: (lambda s_: (lambda t: mirror(s_, 3 * hu(t), 3 * vib(t))))(s_) for g, s_ in HORN_TIP}}, n_kf=16, loop="once")

ANIMS = [idle, walk, run, sneak, fly, glide, attack, hurt] + particle_anims(PG)
assert 2 <= len(EMITS) <= 3
write(NOM, outliner, ANIMS, len(groups) + 1, (80, 220), len(EMITS), DENS)
