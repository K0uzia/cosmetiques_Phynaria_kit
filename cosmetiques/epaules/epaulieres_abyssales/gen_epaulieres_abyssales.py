"""Épaulières abyssales : paire asymétrique d'os noir fissuré de vert acide. Design original, à porter avec ailes_abyssales et bandeau_abyssal.
Écrit epaulieres_abyssales.png, epaulieres_abyssales_e.png et .build/epaulieres_abyssales_brut.bbmodel à côté de ce script.

Sur chaque épaule : deux rangs de plaques d'os en éventail (peau découpée + arête pleine), griffes octogonales qui partent vers l'extérieur
puis remontent (plus grandes et plus nombreuses à gauche), lanières de cuir cousu sur l'avant et l'arrière du bras.
Groupes de premier niveau right_arm (x > 0) et left_arm (x < 0) : le mod remplace leur pivot par l'épaule.

Remise aux règles du 2026-11-05 (.claude/references/procedures/remise-aux-regles.md) ; plaques, griffes, lanières, palette et proportions inchangées.
- Faces proches (mesuré par .build/mesure_noms.py, pose de base et poses) : griffes à torsion alternée de ±6° entre tronçons
  (faces jamais parallèles quand elles plient), dernier tronçon tourné de 22,5° face à la pointe découpée ; arêtes des plaques
  bout à bout, en losange calé sur la plaque ; octogones chanfreinés (culots à 0,12 px) ; lanières : sections bout à bout
  (pivot sur la jointure), âme de cuir plus épaisse que la peau de 0,12 px par face, clou et boucle à 0,15 px des faces.
- Tête et bras : sous-col écarté de la tête (bord intérieur à 4,65 px du centre, seconde couche du skin à 4,5) ; lanières
  décollées de la seconde couche du bras (face intérieure à 2,37 px de l'axe, seconde couche à 2,25).
- Texture HD : cartes peintes à 30 texels/px environ (18 avant), tuiles d'os et de cuir agrandies.
- Lumière : calque _e baissé (tools/ambiance.py le multiplie par 2,4, plafond 225) pour un vert franc.
- Apparition : event_equip (1,4 s) : les plaques poussent depuis l'épaule, puis les griffes sortent une à une ; pas de son.
- overlay_ambiance ajoutée par tools/ambiance.py.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # True : embarque le calque _e en seconde texture. Réactivé le 2026-11-03 (correctif du mod annoncé, à vérifier en jeu).
NOM = "epaulieres_abyssales"
TEX = 512
TAU = 2 * math.pi

C_AURA = np.array((22, 66, 40), np.float32)
C_VEIN = np.array((96, 200, 44), np.float32)
E_COL = (34, 88, 22)    # calque _e : x 2,4 par tools/ambiance.py (plafond 225) -> (82, 211, 53)
STRAP_Z = 2.52          # centre des lanières : face intérieure à 2,37 (seconde couche du bras à 2,25)
STRAP_CORE = 0.54       # âme de cuir : 0,12 px au-dessus de chaque face de la peau (0,3)
OS = [(32, 27, 40), (66, 55, 86), (136, 100, 180), (9, 7, 13), (136, 100, 180)]
CUIR = [(24, 12, 30), (60, 28, 72), (100, 56, 112), (8, 4, 11), (112, 92, 124)]


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ cartes : matière peinte à plat, en px du modèle
class Mat:
    def __init__(self, x0, x1, y0, y1, seed=1, pal=CUIR, R=18):
        self.x0, self.x1, self.y0, self.y1, self.R = x0, x1, y0, y1, R
        self.GW, self.GH = int(round((x1 - x0) * R)), int(round((y1 - y0) * R))
        gy, gx = np.mgrid[0:self.GH, 0:self.GW]
        self.X, self.Y = x0 + (gx + 0.5) / R, y1 - (gy + 0.5) / R
        self.seed = seed
        self.pal = [np.array(c, np.float32) for c in pal]
        self.mask = Image.new("L", (self.GW, self.GH), 0)
        self.vein_img = Image.new("L", (self.GW, self.GH), 0)
        self.core_img = Image.new("L", (self.GW, self.GH), 0)
        self.seam_img = Image.new("L", (self.GW, self.GH), 0)

    def px(self, p):
        return ((p[0] - self.x0) * self.R, (self.y1 - p[1]) * self.R)

    def add(self, poly):
        ImageDraw.Draw(self.mask).polygon([self.px(p) for p in poly], fill=255)

    def cut(self, poly):
        ImageDraw.Draw(self.mask).polygon([self.px(p) for p in poly], fill=0)

    def seams(self, a, b, n=6, w=0.2):
        d = ImageDraw.Draw(self.seam_img)
        for i in range(n):
            t0, t1 = (i + 0.2) / n, (i + 0.7) / n
            d.line([self.px((lerp(a[0], b[0], t0), lerp(a[1], b[1], t0))), self.px((lerp(a[0], b[0], t1), lerp(a[1], b[1], t1)))], fill=255, width=max(1, int(w * self.R)))

    def crack(self, pts, w=0.42):
        """Fissure : ruban brisé qui s'affine vers son dernier point."""
        n = len(pts) - 1
        for im, k in ((self.vein_img, 1.0), (self.core_img, 0.42)):
            d = ImageDraw.Draw(im)
            for i in range(n):
                a, b = pts[i], pts[i + 1]
                nx, ny = -(b[1] - a[1]), b[0] - a[0]
                l = math.hypot(nx, ny) or 1
                nx, ny = nx / l, ny / l
                wa, wb = w * k * (1 - i / (n + 0.4)) / 2, w * k * (1 - (i + 1) / (n + 0.4)) / 2
                d.polygon([self.px((a[0] + nx * wa, a[1] + ny * wa)), self.px((b[0] + nx * wb, b[1] + ny * wb)),
                           self.px((b[0] - nx * wb, b[1] - ny * wb)), self.px((a[0] - nx * wa, a[1] - ny * wa))], fill=255)

    def _blur(self, im, r):
        return np.array(im.filter(ImageFilter.GaussianBlur(r * self.R)), np.float32) / 255

    def _noise(self, cells, seed):
        r = np.random.default_rng(self.seed * 10 + seed)
        a = (r.random((cells, cells)) * 255).astype(np.uint8)
        return np.array(Image.fromarray(a, "L").resize((self.GW, self.GH), Image.BICUBIC), np.float32) / 255

    rim_k = 0.85

    def relief(self, col):
        return col

    def finish(self, grain=1.0):
        base, high, rim, ombre, couture = self.pal
        self.M = np.array(self.mask) > 127
        blot = self._noise(9, 3) * 0.55 + self._noise(40, 4) * 0.45
        col = lerp(base, high, (np.clip((blot - 0.34) * 2.1, 0, 1) * 0.8)[..., None])
        col = col * (1 + 0.06 * grain * np.sin(self.Y * 11 + self.X * 3 + 8 * self._noise(14, 5)))[..., None]
        col = self.relief(col)
        edge = np.clip(1 - self._blur(Image.fromarray(self.M.astype(np.uint8) * 255, "L"), 0.3), 0, 1)
        col = lerp(col, ombre, (np.clip((edge - 0.08) * 3, 0, 1) * 0.5)[..., None])
        col = lerp(col, rim, (np.clip((edge - 0.34) * 6, 0, 1) * self.M * self.rim_k)[..., None])
        col = lerp(col, couture, (np.array(self.seam_img) > 127)[..., None] * 1.0)
        col = lerp(col, C_AURA, (np.clip(self._blur(self.vein_img, 0.3) * 1.4, 0, 1) * 0.72)[..., None])
        col = lerp(col, C_VEIN, (np.array(self.vein_img) > 127)[..., None] * 1.0)
        core = np.array(self.core_img) > 127
        self.col = lerp(col, np.array((190, 255, 96), np.float32), core[..., None] * 1.0).astype(np.float32)
        self.Vc = core & self.M
        return self


class Lame(Mat):
    """Plaque d'os : ombre de recouvrement à la racine, stries de croissance, arête claire au milieu."""
    rim_k = 0.5

    def relief(self, col):
        base, high, rim, ombre, _ = self.pal
        t = (self.X - self.x0) / (self.x1 - self.x0)
        h = self.y1 - self.y0
        col = col * (1 + 0.20 * np.sin(t * 40 + 3 * self._noise(7, 6)))[..., None]
        col = lerp(col, rim, (np.exp(-(self.Y / (0.11 * h)) ** 2) * (0.25 + 0.3 * t) * 0.8)[..., None])
        return lerp(col, ombre, (np.clip(1 - t / 0.34, 0, 1) ** 1.3 * 0.9)[..., None])


PANELS = []


def panel(name, ct):
    PANELS.append(dict(name=name, carte=ct, w=ct.x1 - ct.x0, h=ct.y1 - ct.y0))


def lame_outline(L, W):
    """Silhouette de plaque : racine étroite, ventre vers le tiers, long bout en ogive, dissymétrique (bord de fuite plus creusé)."""
    def hw(t):
        return W / 2 * (0.45 + 0.55 * math.sin(math.pi / 2 * min(t / 0.34, 1))) * (1 - max(0.0, (t - 0.34) / 0.66) ** 1.35)
    n = 28
    up = [(L * i / n, hw(i / n)) for i in range(n + 1)]
    return up + [(x, -y * (1 - 0.3 * x / L)) for x, y in reversed(up)]


# Trois lames : même gabarit, découpes et fissures différentes
LL, LW = 6.0, 4.0
M_ = 0.15
LAMES = [
    ("lame_a", 21, [(1, 0.62, 0.32)], [[(5.0, 0.0), (4.3, 0.35), (3.7, 0.05), (3.0, 0.5), (2.2, 0.25)], [(3.7, 0.05), (3.3, -0.55), (2.8, -0.75)]]),
    ("lame_b", 22, [(-1, 0.48, 0.36), (1, 0.8, 0.22)], [[(3.9, 1.4), (3.5, 0.9), (3.8, 0.35), (3.1, -0.15), (3.3, -0.7), (2.7, -1.2)]]),
    ("lame_c", 23, [(-1, 0.72, 0.28)], [[(4.6, -0.7), (4.0, -0.25), (4.3, 0.3), (3.5, 0.55)], [(2.7, -1.5), (2.5, -0.95), (2.0, -0.8)]]),
]
for name, sd, chips, cracks in LAMES:
    ct = Lame(-M_, LL + M_, -LW / 2 - M_, LW / 2 + M_, seed=sd, pal=OS)
    ct.add(lame_outline(LL, LW))
    for side, t, d_ in chips:
        x = t * LL
        ct.cut([(x - 0.3, side * (LW / 2 + 0.2)), (x + 0.3, side * (LW / 2 + 0.2)), (x + 0.05, side * (LW / 2 - 0.45 - d_))])
    for c_ in cracks:
        ct.crack(c_)
    ct.finish()
    panel(name, ct)

# Sous-col de cuir, sous la racine des plaques
col_ = Mat(-1.65, 1.65, -2.8, 2.8, seed=31)
col_.add([(-1.55, -2.3), (-1.2, -2.7), (1.3, -2.65), (1.55, -2.1), (1.5, 2.2), (1.2, 2.7), (-1.25, 2.65), (-1.55, 2.2)])
col_.seams((-1.2, -2.3), (-1.2, 2.3), n=6)
col_.finish()
panel("col", col_)

# Lanières : section haute droite, deux sections libres dont un bout effiloché. Coordonnées locales : y descend depuis l'articulation.
SW = 1.5
for name, sd, H, tail in (("lan_h", 34, 4.2, False), ("lan_m", 35, 3.4, False), ("lan_b", 36, 3.5, True)):
    ct = Mat(-SW / 2 - 0.1, SW / 2 + 0.1, -H - 0.1, 0.1, seed=sd)
    w0, w1 = (SW / 2, SW / 2 * (0.92 if tail else 1.0))
    if tail:
        ct.add([(-w0, 0), (w0, 0), (w1, -H * 0.55), (0.55, -H * 0.86), (0.3, -H * 0.72), (0.15, -H), (-0.08, -H * 0.68), (-0.3, -H * 0.92), (-0.48, -H * 0.62), (-w1, -H * 0.5)])
    else:
        ct.add([(-w0, 0), (w0, 0), (w1, -H), (-w1, -H)])
    k = 0.72 if tail else 1.0
    ct.seams((-0.45, -0.25), (-0.45, -H * k + 0.2), n=max(3, int(H * k * 1.3)))
    ct.seams((0.45, -0.25), (0.45, -H * k + 0.2), n=max(3, int(H * k * 1.3)))
    ct.finish()
    panel(name, ct)


# ------------------------------------------------------------------ images fixes
def hook_shape(L, curve):
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
    ec = lerp(np.array((3, 10, 3), np.float32), np.array((40, 96, 24), np.float32), np.clip((te - 0.2) / 0.7, 0, 1))
    eo = np.dstack([ec, al * 255.0]).astype(np.uint8)
    eo[~al] = 0
    return out, eo


def paint_bone(BW=480, BH_=24):
    a = np.zeros((BH_, BW, 4), np.float32)
    for yy in range(BH_):
        q = abs((yy + 0.5) / BH_ - 0.5) * 2
        for xx in range(BW):
            u = xx / (BW - 1)
            c_ = lerp(np.array((54, 48, 66.0)), np.array((26, 22, 34.0)), q ** 1.2)
            c_ = lerp(c_, np.array((132, 98, 176.0)), max(0.0, 1 - q * 2.2) * (0.55 + 0.3 * math.sin(u * 75)))
            a[yy, xx, :3] = c_ * (0.9 + 0.2 * math.sin(u * 200 + yy * 0.4))
    a[..., 3] = 255
    return a.astype(np.uint8)


def paint_cuir(S=96):
    r = np.random.default_rng(7)
    n = np.array(Image.fromarray((r.random((12, 12)) * 255).astype(np.uint8), "L").resize((S, S), Image.BICUBIC), np.float32)[..., None] / 255
    c = lerp(np.array(CUIR[0], np.float32), np.array(CUIR[1], np.float32), n * 0.7 + r.random((S, S, 1), np.float32) * 0.12)
    return np.dstack([c, np.full((S, S), 255.0, np.float32)]).astype(np.uint8)


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


def atlas():
    """Range toutes les images (densité la plus haute qui tient) et écrit les deux PNG."""
    global tex_b64, tex_e_b64
    hb, hbe = paint_hook(84, 56)
    fixed = [("hook", hb), ("bone", paint_bone()), ("cuir", paint_cuir()), ("braise", paint_braise())]

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

    dens = 34.0
    while (uv := pack(dens)) is None:
        dens -= 0.1
    UV.update(uv)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, im in fixed:
        u0, v0, u1, v1 = UV[n]
        tex[v0:v1, u0:u1] = im
    u0, v0, u1, v1 = UV["hook"]
    tex_e[v0:v1, u0:u1] = hbe
    for p in PANELS:
        u0, v0, u1, v1 = UV[p["name"]]
        W, H, ct, ss = u1 - u0, v1 - v0, p["carte"], 3
        jj, ii = np.mgrid[0:H * ss, 0:W * ss]
        wx = ct.x0 + (ii + 0.5) / (W * ss) * p["w"]
        wy = ct.y1 - (jj + 0.5) / (H * ss) * p["h"]
        ix = np.clip(((wx - ct.x0) * ct.R).astype(int), 0, ct.GW - 1)
        iy = np.clip(((ct.y1 - wy) * ct.R).astype(int), 0, ct.GH - 1)
        al = ct.M[iy, ix].reshape(H, ss, W, ss).mean(axis=(1, 3)) > 0.5
        cc = ct.col[iy, ix].reshape(H, ss, W, ss, 3).mean(axis=(1, 3))
        if al.any():
            cc[~al] = cc[al].mean(axis=0)
        tex[v0:v1, u0:u1, :3] = np.clip(cc, 0, 255).astype(np.uint8)
        tex[v0:v1, u0:u1, 3] = al * 255
        vm = (ct.Vc[iy, ix].reshape(H, ss, W, ss).mean(axis=(1, 3)) > 0.34) & al
        tex_e[v0:v1, u0:u1, :3] = np.array(E_COL, np.uint8) * vm[..., None]
        tex_e[v0:v1, u0:u1, 3] = vm * 255
    assert tex[TEX - 3, TEX - 3, 3] == 0
    tex[..., :3] &= 0xFC
    assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
    b64 = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        b64.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    tex_b64, tex_e_b64 = b64
    return dens


DENS = atlas()

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
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent}
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


def bar(g, name, p, q, r, u0=0.0, u1=1.0, octo=True, ov=0.1, turn=0.0, up=None, caps=(True, True)):
    """Tronçon d'os : section octogonale (deux cubes à 45°) ou losange seul. turn : torsion autour de l'axe (degrés) ;
    up : direction de référence de la section (sinon la verticale) ; caps : culots de départ et de bout visibles."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X = unit(q - p)
    ref = np.asarray(up, float) if up is not None else (V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0))
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    ct, st = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    Y, Z_ = ct * Y + st * Z_, -st * Y + ct * Z_
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R0 = np.column_stack([X, Y, Z_])
    R45 = np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])
    bu0, bv0, bu1, bv1 = UV["bone"]
    ua = lerp(bu0, bu1, u0)
    ub = max(lerp(bu0, bu1, u1), ua + 2)
    lg = [ua, bv0, ub, bv1]
    end = [ua, bv0 + 3, ua + 2, bv1 - 3]
    faces = {"south": lg, "north": lg, "up": lg, "down": lg, "east": end if caps[1] else CLEAR, "west": end if caps[0] else CLEAR}
    if octo:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R0), faces)
        ch = 0.12                                    # chanfrein : culots des deux pavés à 0,12 px l'un de l'autre
        cube(g, name + "o", p + (-ov + ch, -r * 0.97, -r * 0.97), p + (L + ov - ch, r * 0.97, r * 0.97), p, euler(R45), faces)
    else:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R45), faces)


def chain(g, name, pts, r0, r1, u0=0.0, u1=1.0, octo=True, up=None):
    """Arête droite : tronçons bout à bout, culots intérieurs transparents."""
    n = len(pts) - 1
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        bar(g, f"{name}{i}", pts[i], pts[i + 1], lerp(r0, r1, (t0 + t1) / 2), lerp(u0, u1, t0), lerp(u0, u1, t1), octo=octo, ov=0.0, up=up,
            caps=(i == 0, i == n - 1))


def hook(g, name, p, X, Y, L):
    """Griffe : peau découpée + âme pleine plus étroite. Elle part de p vers X et se recourbe vers Y."""
    p, X = np.asarray(p, float), unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    n = np.cross(X, Y)
    lo, hi = HOOK_BB
    c = p + X * (0.49 * L) + Y * ((lo + hi) / 2 * L) + n * 0.07
    plate(g, name, c, X, Y, 1.02 * L, (hi - lo) * L, "hook")
    center, hw = hook_shape(L, CURVE)
    a, b = center(0.0), center(0.6)
    # âme en losange calée sur la plaque : ses faces à 45° de la peau
    bar(g, f"{name}c", p + X * a[0] + Y * a[1], p + X * b[0] + Y * b[1], max(0.16, hw(0.3) * 0.62), 0.6, 0.9, octo=False, ov=0.06, up=n)
    return p + X * center(1)[0] + Y * center(1)[1]


def box(g, name, c, X, Y, w, h, th, tile="cuir", bouts=(True, True)):
    """Âme de cuir : vrai volume, texturé sur 6 faces ; bouts : faces up et down visibles (transparentes aux jointures)."""
    X, Y = unit(np.asarray(X, float)), unit(np.asarray(Y, float))
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    u0, v0, u1, v1 = UV[tile]
    c = np.asarray(c, float)
    fc = {f: [u0, v0, u1, v1] for f in ("north", "south", "east", "west")}
    fc["up"] = [u0, v0, u1, v1] if bouts[0] else CLEAR
    fc["down"] = [u0, v0, u1, v1] if bouts[1] else CLEAR
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_), fc)


def lame(g, name, root, d, nhint, L, W, tile, ofs=0.0):
    """Plaque d'os : peau découpée sur son plan, arête pleine en losange le long du milieu, en saillie des deux côtés."""
    X = unit(np.asarray(d, float))
    N = unit(np.asarray(nhint, float) - (np.asarray(nhint, float) @ X) * X)
    Y = np.cross(N, X)
    root = np.asarray(root, float) + N * ofs
    sL, sW = L / LL, W / LW
    plate(g, name, root + X * (L / 2), X, Y, (LL + 2 * M_) * sL, (LW + 2 * M_) * sW, tile)
    chain(g, name + "a", [root + X * L * 0.14, root + X * L * 0.45, root + X * L * 0.78], 0.46 * sW, 0.2 * sW, 0.1, 0.5, octo=False, up=N)


# Un côté : s = -1 gauche, +1 droit. Tous les x s'écrivent en valeur absolue et sont multipliés par s.
EMITS = []
CLAWS, STRAPS = [], []
TIPS = []


def emit(parent, at):
    EMITS.append(group("emit_braise" + (str(len(EMITS) + 1) if EMITS else ""), at, parent=parent))


def griffe(arm, s, tag, k, base, L, a0, a1, zf, n, r0, emits=False):
    """Griffe : part vers l'extérieur, se relève vers la verticale ; dernière section et pointe dans leur propre groupe."""
    base = V(s * base[0], base[1], base[2])
    dirs = lambda a: unit(V(s * math.cos(math.radians(a)), math.sin(math.radians(a)), zf))
    seg = L * 0.78 / n
    pts = [base]
    for i in range(n):
        pts.append(pts[-1] + dirs(lerp(a0, a1, (i + 0.5) / n)) * seg)
    g0 = group(f"griffe{k}_{tag}", base, parent=arm)
    g1 = group(f"griffe{k}_bout_{tag}", pts[-2], parent=g0)
    r_ = lambda i: lerp(r0, r0 * 0.42, (i + 0.5) / n)
    for i in range(n):
        # torsion alternée de ±6° (faces des tronçons voisins jamais parallèles au pli) ; le dernier à 22,5° de la pointe découpée
        tw = 22.5 if i == n - 1 else (6.0 if i % 2 == 0 else -6.0)
        bar(g1 if i == n - 1 else g0, f"griffe{k}_{i}_{tag}", pts[i], pts[i + 1], r_(i), 0.05 + i * 0.14, 0.05 + (i + 1) * 0.14, octo=True, ov=0.08,
            turn=tw, caps=(i > 0, True))     # le départ est caché dans la bague
    d0 = unit(pts[1] - pts[0])
    bar(g0, f"griffe{k}_bague_{tag}", pts[0] - d0 * 0.45, pts[0] + d0 * 0.2, r0 + 0.17, 0.42, 0.48, octo=True, ov=0.0, turn=30)
    d1 = unit(pts[-1] - pts[-2])
    tip = hook(g1, f"griffe{k}_pointe_{tag}", pts[-1] - d1 * 0.12, d1, dirs(a1 + 90), L * 0.34)
    CLAWS.append((g0, g1, s, k))
    TIPS.append(pts[0:] + [tip])
    if emits:
        emit(g1, tip)


def laniere(arm, armure, s, tag, zs, nom, x_top, x_bot, y_top, y_band, k_tail):
    """Lanière : section haute en biais sur le bras, boucle d'os, deux sections libres en dessous. zs = -1 avant, +1 arrière."""
    z = zs * STRAP_Z
    X_ = V(s * -zs, 0, 0)       # X x Y doit sortir du bras
    x_top = max(x_top, 5.55)    # bord intérieur de la section haute à 4,7 px au moins de l'axe : hors de la seconde couche de la tête
    top, bot = V(s * x_top, y_top, z), V(s * x_bot, y_band, z)
    Y_h = unit(top - bot)
    X_h = unit(X_ - (X_ @ Y_h) * Y_h)
    Hh = np.linalg.norm(top - bot)
    mid = (top + bot) / 2
    # peau (marges transparentes de 0,1 px autour de la carte) et âme bout à bout avec la section suivante, sur la jointure bot
    # la section haute s'arrête 0,15 px au-dessus de la jointure, la suivante 0,15 px au-dessous : la boucle (rayon 0,3) cache l'écart
    Hc = Hh - 0.15
    mid = top - Y_h * (Hc / 2)
    plate(armure, f"lan_h_{nom}_{tag}", mid, X_h, Y_h, SW + 0.2, Hc + 0.2, "lan_h")
    box(armure, f"lan_ha_{nom}_{tag}", mid, X_h, Y_h, SW * 0.58, Hc, STRAP_CORE, bouts=(True, False))
    cl = top - Y_h * 0.75
    bar(armure, f"clou_{nom}_{tag}", cl, cl + V(0, 0, zs * 0.5), 0.3, 0.2, 0.3, octo=False, ov=0.0)
    # boucle d'os à la jointure, à peine plus large que la lanière : une barre de bras à bras ferait une croix
    bar(armure, f"boucle_{nom}_{tag}", bot + V(-0.8, 0, zs * 0.30), bot + V(0.8, 0, zs * 0.30), 0.3, 0.15, 0.3, octo=True, ov=0.0, turn=30)
    y = y_band
    cx = s * x_bot
    parent = armure
    for j, (tile, H) in enumerate((("lan_m", 3.4 * k_tail), ("lan_b", 3.5 * k_tail))):
        zj = z                                   # sections bout à bout, pivot sur la jointure
        g = group(f"laniere{j}_{nom}_{tag}", [cx, y, zj], parent=parent)
        # chaque section pivote de ±5° autour de la verticale : les faces de deux sections voisines ne sont jamais parallèles
        Xj = unit(X_ + V(0, 0, (1 if j == 0 else -1) * math.tan(math.radians(5))))
        y0 = y - (0.15 if j == 0 else 0.0)       # sous la boucle
        Hj = H - (0.15 if j == 0 else 0.0)
        plate(g, f"lan{j}_{nom}_{tag}", V(cx, y0 - Hj / 2, zj), Xj, V(0, 1, 0), SW + 0.2, Hj + 0.2, tile)
        h_core = Hj * (1 if j == 0 else 0.5)
        box(g, f"lan{j}a_{nom}_{tag}", V(cx, y0 - h_core / 2, zj), Xj, V(0, 1, 0), SW * 0.58, h_core, STRAP_CORE, bouts=(j == 0, j == 1))
        STRAPS.append((g, s, zs, j))
        parent = g
        y -= H


def epauliere(s, tag, azA, azB, sc, griffes, emit_k, x_lan, y_band, k_tail):
    arm = group("left_arm" if s < 0 else "right_arm", V(s * 5, 22, 0))
    armure = group(f"armure_{tag}", V(s * 5, 22, 0), parent=arm)
    # sous-col : couvre le dessus de l'épaule, jamais au-delà de x = 4,1 (tête et cou)
    plate(armure, f"col_{tag}", V(s * 6.05, 24.36, 0), V(s, 0, 0), V(0, 0, -s), 2.8, 5.6, "col")   # bord intérieur à 4,65 : hors de la tête
    # rang bas : descend sur le flanc du bras, en éventail vu de profil. Sous le rang haut.
    hb = V(s * 8.5, 24.55, 0)
    tiles = ["lame_b", "lame_a", "lame_c", "lame_b"]
    mid = (len(azB) - 1) / 2
    for i, b in enumerate(azB):
        ca, sa = math.cos(math.radians(b)), math.sin(math.radians(b))
        d = V(s * 0.32, -ca, sa)
        off = 1 - abs(i - mid) / max(mid, 1) * 0.28
        lame(armure, f"bas{i}_{tag}", hb + V(0, 0, sa * 0.5), d, V(s, 0.2, sa * 0.35), (6.4 + 0.5 * i) * sc * off, 3.1 * sc, tiles[i % 4], ofs=0.2 * (len(azB) - abs(i - mid)))
    # rang haut : part du dessus de l'épaule, s'étale vers l'avant, l'extérieur et l'arrière
    hh = V(s * 5.45, 25.3, 0)
    mid = (len(azA) - 1) / 2
    for i, a in enumerate(azA):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        d = V(s * ca, -0.42, sa)
        lame(armure, f"haut{i}_{tag}", hh, d, V(s * 0.42, 1, sa * 0.42), (5.6 if abs(a) < 35 else 5.1) * sc, 3.3 * sc, tiles[(i + 1) % 4], ofs=0.16 * (len(azA) - abs(i - mid)))
    for k, g_ in enumerate(griffes):
        griffe(arm, s, tag, k, *g_, emits=k in emit_k)
    laniere(arm, armure, s, tag, -1, "av", x_lan[0][0], x_lan[0][1], 24.25, y_band, k_tail)
    laniere(arm, armure, s, tag, 1, "ar", x_lan[1][0], x_lan[1][1], 24.25, y_band, k_tail)
    return arm


# griffes : (base |x|, y, z), longueur, angle de départ, angle final, dérive en z, sections, rayon
epauliere(-1, "l", (-50, -17, 15, 46), (-48, -18, 10, 36), 1.0,
          [((6.8, 25.7, -1.7), 5.6, 12, 58, -0.30, 3, 0.52),
           ((7.4, 25.3, -0.5), 8.6, 22, 86, -0.08, 4, 0.72),
           ((6.8, 25.8, 0.8), 6.8, 40, 96, 0.14, 3, 0.6),
           ((8.0, 25.0, 1.6), 4.6, 2, 52, 0.26, 3, 0.48)],
          {1, 2}, ((5.0, 7.0), (5.2, 6.8)), 20.2, 1.0)
epauliere(1, "r", (-44, -2, 40), (-40, -6, 28), 0.9,
          [((7.0, 25.4, -1.2), 4.0, 14, 62, -0.28, 2, 0.42),
           ((7.3, 25.2, 0.1), 5.8, 28, 88, 0.02, 3, 0.52),
           ((7.0, 25.3, 1.4), 3.6, 8, 56, 0.26, 2, 0.4)],
          {1}, ((5.2, 6.7), (5.0, 7.0)), 20.6, 0.8)


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


PG = group("particle_braise", [0, 0, 0])
_w = 3.2
_u0, _v0, _u1, _v1 = UV["braise"]
cube(PG, "braise", [-_w / 2, 0.3, -_w / 2], [_w / 2, 0.6, _w / 2], [0, 0, 0], (0, 0, 0), {"up": [_u0, _v0, _u1, _v1]})

outliner = [bone_node("right_arm"), bone_node("left_arm"), bone_node(PG)]

# Marge tête / bandeau : aucune griffe dans x ±5,8 au-dessus de y = 24.
for tr in TIPS:
    for p in tr:
        assert abs(p[0]) >= 5.8, f"griffe trop près de la tête : {p}"


# ------------------------------------------------------------------ animations
# Intentions : out > 0 écarte la griffe de la tête, back > 0 bascule son haut vers l'arrière ; swing >= 0 décolle la lanière du bras.
# MIROIR D'AXES : seul endroit à toucher si la convention du mod change. Guide, section 3 : +X = le haut part vers l'arrière, donc ce qui pend avance ;
# +Z = le côté droit monte, donc le haut part vers la gauche.
def griffe_rot(s, out, back):
    return back, 0.0, -s * out


def lan_rot(s, zs, swing, sway):
    return -zs * swing, 0.0, s * sway


def kf(t, x, y, z):
    return {"channel": "rotation", "data_points": [{"x": str(round(x + 0.0, 2)), "y": str(round(y + 0.0, 2)), "z": str(round(z + 0.0, 2))}],
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


def anim(name, length, tracks, n_kf=None, loop="loop"):
    n = n_kf or max(6, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]
    A = {groups[g]["uuid"]: {"name": g, "type": "bone", "keyframes": [kf(t, *f(t)) for t in times]} for g, f in tracks.items()}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


def state(name, L, cycles, c_rest, c_amp, s_rest, s_amp, n_kf=None, shiver=None):
    """c_ : griffes (écart au repos, amplitude) ; s_ : lanières. shiver(t) : frisson additionnel, à période entière."""
    tr = {}
    sh = shiver or (lambda t, ph: 0.0)
    for g0, g1, s, k in CLAWS:
        ph0 = 0.13 * k + (0.31 if s > 0 else 0)

        def f0(t, s=s, ph0=ph0):
            ph = TAU * (cycles * t / L - ph0)
            return griffe_rot(s, c_rest + c_amp * math.sin(ph) + sh(t, ph0), 0.5 * c_amp * math.cos(ph))

        def f1(t, s=s, ph0=ph0):
            ph = TAU * (cycles * t / L - ph0 - 0.14)
            return griffe_rot(s, 1.4 * c_amp * math.sin(ph) + 1.5 * sh(t, ph0 + 0.25), 0.0)
        tr[g0], tr[g1] = f0, f1
    for g, s, zs, j in STRAPS:
        def fs(t, s=s, zs=zs, j=j):
            ph = TAU * (cycles * t / L - 0.15 * j - (0.2 if zs > 0 else 0) - (0.31 if s > 0 else 0))
            amp = s_amp * (1 + 0.5 * j)
            return lan_rot(s, zs, s_rest * (1 if j == 0 else 0.6) + amp * math.sin(ph) + 0.5 * abs(sh(t, j * 0.2)), 0.7 * amp * math.sin(ph + 1.1))
        tr[g] = fs
    return anim(name, L, tr, n_kf=n_kf)


def frisson(t, ph):
    """Idle : deux frissons brefs sur 8 s, à 3 Hz (24 périodes dans la boucle)."""
    w = bump(t, 2.5, 2.8, 3.3, 3.8) + 0.7 * bump(t, 6.0, 6.25, 6.6, 7.0)
    return 1.5 * w * math.sin(TAU * (3 * t - ph))


idle = state("idle", 8.0, 2, 0.5, 0.6, 1.3, 0.8, n_kf=96, shiver=frisson)
walk = state("walk", 1.6, 2, 1.0, 1.3, 4.5, 2.5)
run = state("run", 1.0, 2, 2.0, 2.2, 13.0, 4.5)
sneak = state("sneak", 3.0, 1, -0.5, 0.5, 2.0, 1.0)

atk = lambda t: bump(t, 0.0, 0.1, 0.24, 0.68)
hu = lambda t: bump(t, 0.0, 0.07, 0.18, 0.7)
vib = lambda t: math.sin(TAU * t * 5 / 0.8)
tr_a, tr_h = {}, {}
for g0, g1, s, k in CLAWS:
    tr_a[g0] = (lambda s: (lambda t: griffe_rot(s, 7 * atk(t), 0)))(s)
    tr_a[g1] = (lambda s: (lambda t: griffe_rot(s, 6 * atk(t), 0)))(s)
    tr_h[g0] = (lambda s, k: (lambda t: griffe_rot(s, 3.2 * vib(t + k * 0.03) * hu(t), -2 * hu(t))))(s, k)
    tr_h[g1] = (lambda s, k: (lambda t: griffe_rot(s, 5 * vib(t + k * 0.03 + 0.04) * hu(t), 0)))(s, k)
for g, s, zs, j in STRAPS:
    tr_a[g] = (lambda s, zs, j: (lambda t: lan_rot(s, zs, (17 - 8 * j) * atk(t), 0)))(s, zs, j)
    tr_h[g] = (lambda s, zs, j: (lambda t: lan_rot(s, zs, (11 - 3 * j) * hu(t), 3 * vib(t) * hu(t))))(s, zs, j)
attack = anim("attack", 0.8, tr_a, n_kf=16, loop="once")
hurt = anim("hurt", 0.8, tr_h, n_kf=16, loop="once")

def equip_anim():
    """event_equip (1,4 s, jouée par-dessus l'état) : les plaques poussent depuis l'épaule, puis les griffes sortent une à une
    (échelle depuis leur bague, léger dépassement) ; les lanières retombent en se balançant. Dernière image : zéro."""
    LE = 1.4
    times = [j * LE / 28 for j in range(29)]
    A = {}

    def sc_keys(f):
        return [{"channel": "scale", "data_points": [{"x": str(round(f(t), 3)), "y": str(round(f(t), 3)), "z": str(round(f(t), 3))}],
                 "time": round(t, 3), "interpolation": "linear"} for t in times]
    for tag in ("l", "r"):
        g = f"armure_{tag}"
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": sc_keys(lambda t: 0.2 + 0.8 * sm(t, 0.0, 0.45))}
    for g0, g1, s, k in CLAWS:
        d = 0.35 + 0.12 * k + (0.05 if s > 0 else 0)
        f = lambda t, d=d: sm(t, d, d + 0.35) * (1 + 0.1 * bump(t, d + 0.25, d + 0.35, d + 0.4, d + 0.6))
        A[groups[g0]["uuid"]] = {"name": g0, "type": "bone", "keyframes": sc_keys(f)}
    for g, s, zs, j in STRAPS:
        sw = lambda t, j=j: 22 * (1 - sm(t, 0.2, 1.3)) * math.cos(TAU * 1.6 * (t - 0.1 * j))
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(t, *lan_rot(s, zs, max(0.0, sw(t)), 0)) for t in times]}
    return {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": LE, "snapping": 24, "selected": False, "animators": A}


PF, PR = 3.0, 6.0
ANIMS = [idle, walk, run, sneak, attack, hurt, equip_anim(),
         anim("particle_braise_fall", PF, {PG: lambda t: (24 * math.sin(TAU * t / PF), 360 * t / PF, 18 * math.cos(2 * TAU * t / PF))}, n_kf=24),
         anim("particle_braise_rest", PR, {PG: lambda t: (0, 0, 1.2 * math.sin(TAU * t / PR))}, n_kf=12)]

assert 2 <= len(EMITS) <= 3
assert 50 <= len(elements) <= 160, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
# Particules qui tombent et se posent : réservées aux ailes (.claude/rules/retours-en-jeu.md).
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from particules import retirer_particules
from sons import limiter_sons
from ambiance import ajouter_ambiance
retirer_particules(model)
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
ajouter_ambiance(model)
assert len(model["animations"]) <= 16
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      f"densité {DENS:.1f} texels/px ; {len(EMITS)} emit_ ; {len(PANELS)} images")
