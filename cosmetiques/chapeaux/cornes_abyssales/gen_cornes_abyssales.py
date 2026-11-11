"""Cornes abyssales : cornes en crochet qui ont percé le crâne, racines d'os qui s'étendent sur la tête et se referment sur
les yeux en demi-masque fendu, au regard vert acide. Design original, ensemble Abyssal (thème Démoniaque), à porter avec ailes_abyssales.
Écrit cornes_abyssales.png, cornes_abyssales_e.png et .build/cornes_abyssales_brut.bbmodel à côté de ce script.
Fiche de style : .claude/styles/abyssal.md ; fiche du sujet : .claude/references/creatures/demons.md (section « Cornes qui percent le crâne »).

Refonte du 2026-11-08 de bandeau_abyssal (avant : .build/gen_avant.py, .build/avant_livrable.bbmodel ; plus ancien : _v1) :
l'utilisateur, « revois les têtes [...] tu as fait une fixette sur des couronnes et bandeaux », « bandeau à revoir ».
Gardé tel quel (validé en jeu, « incroyable », cornes « niquel ») : les cornes (tracé, bagues, pointes en crochet, socle),
les oreilles pointues (forme, animations), la palette, les fentes du regard (même dessin).
Retiré : la bande de cuir, le pli, le nœud, les clous et les pans flottants.
Nouveau, d'après l'anatomie réelle d'une corne (cheville osseuse qui prolonge l'os frontal, base perlée en couronne de nodules,
surface striée et poreuse ; WikiVet, « Horn - Anatomy & Physiology ») :
- au pied de chaque corne, une collerette de six nodules d'os (la « meule ») ;
- quatre racines d'os aplaties par côté (relief soudé au crâne, 0,4–0,7 px d'épais, 0,7–2,8 px de large ; des tubes
  octogonaux faisaient « pattes d'araignée », cage de tubes déjà refusée sur les harnais) : tempe → arcade, nuque, oreille,
  front en V ; elles tournent aux arêtes de la tête et leur dos est fendu d'une fissure vert acide brisée (calque _e) ;
- un demi-masque d'os en deux lobes posé à plat sur les yeux (plaque de 0,3 px, face intérieure à 4,62), arcades en relief,
  fentes découpées : le regard vert est une plaque à part, posée devant, qui s'allume en dernier à l'apparition, cligne une
  fois par boucle au repos et se plisse en sneak (affût).
Rien en porte-à-faux devant le visage : tout ce qui est devant les yeux est posé sur le masque, lui-même collé à la tête.
Pas d'attack ni de hurt (pièce portée). Un seul son : craquement d'os quand les cornes percent (event_equip).
Fonctions avancées : calque _e, event_equip, event_unequip, canal scale (regard). À juger en jeu : apparition et retrait,
clignement et plissement du regard (scale), calque _e de nuit, lisibilité des fissures à distance.
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


def paint_bone_v(BW=96, BH=16):
    """Os des racines : même os que les cornes, fendu au milieu d'une fissure vert acide brisée (trois tronçons)."""
    # dos plat d'une racine : os charbon assez clair et uni (un dégradé sombre aux bords la faisait lire comme un fil),
    # biseau lilas au bord, stries de croissance en travers
    a = np.zeros((BH, BW, 4), np.float32)
    for yy in range(BH):
        q = abs((yy + 0.5) / BH - 0.5) * 2
        for xx in range(BW):
            u = xx / (BW - 1)
            c_ = lerp(np.array((70, 58, 90.0)), np.array((50, 42, 64.0)), q ** 2)
            if q > 0.78:
                c_ = np.array((116, 88, 156.0))
            a[yy, xx, :3] = c_ * (0.92 + 0.12 * (math.sin(u * 55 + 0.3 * yy) > 0.6))
    a[..., 3] = 255
    e = np.zeros((BH, BW, 4), np.uint8)
    r = np.random.default_rng(7)
    for xx in range(BW):
        u = xx / (BW - 1)
        if not any(lo <= u <= hi for lo, hi in ((0.06, 0.30), (0.40, 0.62), (0.72, 0.93))):
            continue
        yc = BH / 2 - 0.5 + 1.3 * math.sin(u * 23 + 1.0) + 0.6 * math.sin(u * 61)
        for yy in range(BH):
            d = abs(yy - yc)
            if d < 2.6:
                a[yy, xx, :3] = lerp(a[yy, xx, :3], C_AURA, 0.7)
            if d < 1.1:
                a[yy, xx, :3] = C_VEIN
                e[yy, xx] = (132, 255, 72, 255)
            if d < 0.5:
                a[yy, xx, :3] = C_VCORE
                e[yy, xx] = (206, 255, 118, 255)
    return a.astype(np.uint8), e


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
    bv, bve = paint_bone_v()
    fixed = [("hook_big", hb), ("hook_small", hs), ("bone", paint_bone()), ("bone_v", bv)]

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

    dens = 40.0
    while (uv := pack(dens)) is None:
        dens -= 0.1
    UV.update(uv)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, im in fixed:
        u0, v0, u1, v1 = UV[n]
        tex[v0:v1, u0:u1] = im
    for n, im in (("hook_big", hbe), ("hook_small", hse), ("bone_v", bve)):
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


def bar(g, name, p, q, r, u0=0.0, u1=1.0, octo=True, ov=0.1, tile="bone"):
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
    bu0, bv0, bu1, bv1 = UV[tile]
    ua = lerp(bu0, bu1, u0)
    ub = max(lerp(bu0, bu1, u1), ua + 2)
    lg = [ua, bv0, ub, bv1]
    end = [ua, bv0 + 3, ua + 2, bv1 - 3]
    faces = {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end}
    if octo:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R0), faces)
        # bouts du cube à 45° rentrés de 0,1 px (avant : 0,03 px, faces de bout presque confondues)
        cube(g, name + "o", p + (-ov + 0.1, -r * 0.97, -r * 0.97), p + (L + ov - 0.1, r * 0.97, r * 0.97), p, euler(R45), faces)
    else:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R45), faces)


def chain(g, name, pts, r0, r1, u0=0.0, u1=1.0, octo_until=1.0, tile="bone"):
    """Os effilé : tronçons qui se recouvrent, rayon qui décroît, couleur continue."""
    n = len(pts) - 1
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        bar(g, f"{name}{i}", pts[i], pts[i + 1], lerp(r0, r1, (t0 + t1) / 2), lerp(u0, u1, t0), lerp(u0, u1, t1), octo=t1 <= octo_until + 1e-6, tile=tile)


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
    from reactions import retirer_reactions
    retirer_reactions(model)
    with open(out, "w") as fh:
        json.dump(model, fh, separators=(",", ":"))

    def depth(n, d=1):
        return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])

    print(len(elements), "cubes ;", n_groups, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(anims), "anims ;",
          sum(len(b["keyframes"]) for a in anims for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
          f"densité {dens:.1f} texels/px ; {emits} emit_ ; {len(PANELS)} images de membrane")

# ------------------------------------------------------------------ cornes abyssales
NOM = "cornes_abyssales"
FACE = 4.77                 # plan du demi-masque : plaque de 0,3 px, face intérieure à 4,62 (hors de la seconde couche du skin, 4,5)
HC = 28.0                   # centre de la tête


class Mat(Carte):
    """Matière non membraneuse : os ou peau, selon la palette. Marques claires, usure, ombres aux découpes."""

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


OS = [(30, 25, 38), (64, 52, 84), (118, 88, 158), (11, 8, 16), (84, 68, 108)]      # charbon du masque (style Abyssal)
PEAU = [(122, 104, 134), (170, 152, 178), (88, 66, 104), (54, 40, 70), (150, 130, 160)]


def fente(sg):
    """Fente du regard (même dessin que bandeau_abyssal, validé) : pointe intérieure basse, extérieure haute."""
    return ([(sg * 0.55, 27.85), (sg * 1.35, 28.5), (sg * 3.45, 28.72), (sg * 3.05, 27.95), (sg * 1.5, 27.72)],
            [(sg * 0.95, 27.98), (sg * 1.5, 28.28), (sg * 3.05, 28.48), (sg * 2.8, 28.12), (sg * 1.55, 27.92)])


def gonfle(poly, k):
    cx, cy = sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly)
    return [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in poly]


MX0, MX1, MY0, MY1 = -5.0, 5.0, 26.4, 31.0
# Demi-masque : deux lobes d'os sur les yeux, arcade qui remonte vers la tempe, pommette en bas ; fentes découpées
mq = Mat(MX0, MX1, MY0, MY1, seed=91, pal=OS)
for sg in (1, -1):
    mq.add([(sg * x, y) for x, y in [(0.5, 29.5), (1.6, 30.05), (3.0, 30.38), (4.2, 30.66), (4.74, 30.2), (4.74, 28.6),
                                      (4.5, 27.25), (4.05, 26.7), (3.5, 26.95), (2.7, 27.2), (1.8, 27.35), (1.0, 27.5), (0.5, 27.95)]])
for sg in (1, -1):
    mq.cut(gonfle(fente(sg)[0], 1.08))
    # fissures qui partent du regard : vers la tempe et vers la pommette, fines
    mq.vein([(sg * 3.5, 28.78), (sg * 3.85, 29.35), (sg * 4.35, 30.0)], w0=0.24, w1=0.14, wob=0.05, seed=1 if sg > 0 else 2)
    mq.vein([(sg * 2.6, 27.7), (sg * 2.85, 27.35), (sg * 3.3, 27.05)], w0=0.2, w1=0.12, wob=0.04, seed=3 if sg > 0 else 4)
    mq.seams((sg * 0.9, 29.35), (sg * 3.9, 30.1), n=5, w=0.16)      # stries de croissance sous l'arcade
mq.finish()
mq.panel("masque", rect=True)

# Regard : plaque à part, posée devant le masque, un peu plus grande que la fente
rg = Mat(MX0, MX1, MY0, MY1, seed=92, pal=OS)
for sg in (1, -1):
    out, core = fente(sg)
    rg.add(gonfle(out, 1.14))
    rg.blade(gonfle(out, 1.02), core)
rg.finish()
rg.panel("regard", rect=True)

# Oreille : longue feuille pointue, encoche déchirée (inchangée, validée). u = de la racine vers la pointe.
EL, EH = 7.6, 2.6
ear = Mat(-0.1, EL + 0.1, -EH / 2 - 0.1, EH / 2 + 0.1, seed=89, pal=PEAU)
ear.add([(0, 0.5), (1.6, 1.15), (3.4, 1.25), (5.6, 0.75), (EL, 0.28), (5.6, -0.25), (3.4, -0.75), (1.4, -0.95), (0, -0.55)])
ear.cut([(3.1, 1.5), (3.8, 1.5), (3.5, 0.5)])
ear.cut([(5.05, -0.6), (5.5, -0.6), (5.1, 0.05)])
ear.finish(grain=0.5)
ear.panel("oreille", rect=True)

DENS = atlas(NOM)

# ------------------------------------------------------------------ géométrie
YC = (MY0 + MY1) / 2
masque = group("masque", [0, 30.3, -FACE])
plate(masque, "masque", V(0, YC, -FACE), V(1, 0, 0), V(0, 1, 0), MX1 - MX0, MY1 - MY0, "masque")
regard = group("regard", [0, 28.2, -FACE - 0.4], parent=masque)
plate(regard, "regard", V(0, YC, -(FACE + 0.15 + 0.25)), V(1, 0, 0), V(0, 1, 0), MX1 - MX0, MY1 - MY0, "regard", th=0.2)


def d_os(r):
    """Distance du centre d'un os octogonal couché sur la tête : section la plus large 1,38 r, face intérieure à 4,64 au moins."""
    return 4.66 + 1.38 * r


def racine(g, name, spec, w0, w1, h0=0.28, h1=0.18, u0=0.05, u1=0.95):
    """Racine d'os aplatie, couchée sur la tête (relief soudé au crâne, pas un tube) : largeur 2w qui s'effile, épaisseur 2h,
    face intérieure à 4,66 du centre. spec : points (x, y, z) ; 'D' / '-D' = sur la face (±), 'T' = sur le dessus de la tête.
    Un point qui a deux coordonnées sur la surface est sur une arête : la racine y tourne. Aux arêtes, le tronçon d'avant
    dépasse de h + 0,12 et celui d'après de h − 0,12 (pas de creux au coin, pas de faces confondues). Face du dessus :
    os fendu de vert (bone_v) ; tronçons alternés de 0,1 px plus épais (nœuds de croissance)."""
    n = len(spec) - 1
    H = [lerp(h0, h1, i / n) for i in range(n + 1)]
    pts = []
    for i, p in enumerate(spec):
        d = 4.66 + H[i]
        q = []
        for c in p:
            if c == "T":
                c = HC + d
            elif isinstance(c, str):
                c = (-1 if c.startswith("-") else 1) * d
            q.append(float(c))
        pts.append(V(*q))
    ctr = V(0, HC, 0)

    def faces_de(p):
        return {(k, 1 if p[k] - ctr[k] > 0 else -1) for k in range(3) if abs(p[k] - ctr[k]) >= 4.6}

    F = [faces_de(p) for p in pts]
    coin = [len(f) >= 2 for f in F]
    bu0, bv0, bu1, bv1 = UV["bone"]
    cu0, cv0, cu1, cv1 = UV["bone_v"]
    for i in range(n):
        a, b = pts[i], pts[i + 1]
        com = F[i] & F[i + 1]
        assert com, f"{name}{i} : tronçon qui ne suit pas une face"
        k, sg = sorted(com)[0]
        N_ = V(0, 0, 0)
        N_[k] = sg
        X = unit(b - a)
        Y = unit(N_ - (N_ @ X) * X)
        Z_ = np.cross(X, Y)
        L = np.linalg.norm(b - a)
        h = (H[i] + H[i + 1]) / 2 + (0.05 if i % 2 else -0.05)
        w = lerp(w0, w1, (i + 0.5) / n)
        ea = max(0.05, h - 0.12) if coin[i] else 0.1      # le point d'arête est sur l'axe de la racine (à h de la face)
        eb = (h + 0.12) if coin[i + 1] else 0.1
        ua, ub = lerp(cu0, cu1, lerp(u0, u1, i / n)), lerp(cu0, cu1, lerp(u0, u1, (i + 1) / n))
        ga, gb = lerp(bu0, bu1, lerp(u0, u1, i / n)), lerp(bu0, bu1, lerp(u0, u1, (i + 1) / n))
        os_ = [ga, bv0, max(gb, ga + 2), bv1]
        bout = [ga, bv0 + 3, ga + 2, bv1 - 3]
        # centre de la section : la face intérieure à 4,66 (hauteur moyenne du tronçon)
        o = a - Y * ((H[i] + H[i + 1]) / 2 - h)
        cube(g, f"{name}{i}", o + (-ea, -h, -w), o + (L + eb, h, w), o, euler(np.column_stack([X, Y, Z_])),
             {"up": [ua, cv0, max(ub, ua + 2), cv1], "down": os_, "south": os_, "north": os_, "east": bout, "west": bout})
    return pts


# Arcades : en relief sur le masque (face intérieure 0,12 px dans la plaque), jusqu'au coin de la tête
for s_, tag in ((-1, "l"), (1, "r")):
    pts = []
    for (x, y), r in zip([(0.6, 29.62), (1.6, 30.1), (3.0, 30.42), (4.25, 30.7), (5.0, 30.8)], [0.42, 0.42, 0.38, 0.34, 0.3]):
        pts.append(V(s_ * x, y, -(FACE + 0.15 - 0.12 + 1.38 * r)))
    chain(masque, f"arcade_{tag}", pts, 0.44, 0.3, 0.1, 0.6)

# Cornes : inchangées (validées en jeu). Base épaisse au-dessus des tempes ; balaient vers l'arrière, pointes en crochet vers l'avant
SEGL = [2.7, 2.6, 2.4, 2.2, 2.0, 1.8, 1.6]
RAD = [lerp(1.5, 0.48, (i / (len(SEGL) - 1)) ** 0.8) for i in range(len(SEGL))]
RACINES = []
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
    for i in range(len(SEGL)):
        tgt = g0 if i < 5 else g1
        bar(tgt, f"corne{i}_{tag}", pts[i], pts[i + 1], RAD[i], 0.05 + i * 0.12, 0.05 + (i + 1) * 0.12, octo=True, ov=0.1)
        if i < len(SEGL) - 1:
            d_ = unit(pts[i + 1] - pts[i])
            bar(tgt, f"bague{i}_{tag}", pts[i + 1] - d_ * 0.52, pts[i + 1] - d_ * 0.2, RAD[i] + 0.12, 0.42, 0.48, octo=True, ov=0.0)
    bar(g0, f"socle_{tag}", V(s_ * 3.0, 32.15, -1.2), V(s_ * 3.0, 34.7, -1.2), 1.25, 0.0, 0.03, octo=True, ov=0.0)
    d_end = unit(pts[-1] - pts[-2])
    hook(g1, f"pointe_{tag}", pts[-1] - d_end * 0.15, d_end, V(0, -1, 0.2), 3.6, "hook_big", core=2)

    # Racines : groupe à part, origine au pied de la corne (elles s'étendent depuis lui à l'apparition)
    gr = group(f"racines_{tag}", [s_ * 3.0, 32.8, -1.2])
    RACINES.append(gr)
    S_ = "sD" if s_ > 0 else "-D"
    # meule : six nodules d'os en couronne au pied de la corne
    for k in range(6):
        a = math.radians(30 + 60 * k + (12 if s_ > 0 else -12))
        dx, dz = math.cos(a), math.sin(a)
        r_ = 0.34 if k % 2 else 0.4
        y_ = HC + d_os(r_) + 0.05
        c0 = V(s_ * 3.0 + dx * 1.15, y_, -1.2 + dz * 1.15)
        bar(gr, f"meule{k}_{tag}", c0, c0 + V(dx * 0.75, 0.12, dz * 0.75), r_, 0.15 + 0.1 * k, 0.22 + 0.1 * k, octo=True, ov=0.0)
    # tempe → coin du front (rejoint l'arcade du masque)
    racine(gr, f"rtempe_{tag}", [(s_ * 3.6, "T", -2.2), (s_ * 4.2, "T", -3.0), (S_, "T", -3.55), (S_, 31.6, -3.95), (S_, 30.9, "-D")], 1.4, 0.55, 0.34, 0.22)
    # nuque
    racine(gr, f"rnuque_{tag}", [(s_ * 3.4, "T", 0.3), (s_ * 3.1, "T", 2.0), (s_ * 2.7, "T", 3.6), (s_ * 2.4, "T", "D"), (s_ * 2.0, 31.3, "D"),
                                 (s_ * 1.5, 30.0, "D"), (s_ * 1.05, 29.0, "D")], 1.15, 0.4, 0.32, 0.2)
    # vers l'oreille : descend sur le côté et finit en nodule à sa racine
    racine(gr, f"roreille_{tag}", [(s_ * 4.0, "T", -0.5), (S_, "T", 0.05), (S_, 31.3, 0.45), (S_, 29.8, 0.55), (S_, 28.75, 0.45)], 1.05, 0.55, 0.32, 0.22)
    # front, en V vers la racine du nez
    racine(gr, f"rfront_{tag}", [(s_ * 2.2, "T", -2.4), (s_ * 1.35, "T", -3.6), (s_ * 0.95, "T", "-D"), (s_ * 0.75, 31.4, "-D"), (s_ * 0.5, 30.35, "-D")], 0.9, 0.35, 0.28, 0.18)

# Oreilles : forme et mouvement inchangés ; elles sortent du nodule au bout de la racine
EARS = []
for s_, tag in ((-1, "l"), (1, "r")):
    root = V(s_ * 5.15, 28.3, 0.45)
    X_ = unit(V(s_ * 0.58, 0.3, 0.76))
    Y_ = unit(V(0, 1, 0) - (V(0, 1, 0) @ X_) * X_)
    g = group(f"oreille_{tag}", root)
    EARS.append((g, s_))
    plate(g, f"peau_{tag}", root + X_ * (EL / 2), X_, Y_, EL + 0.2, EH + 0.2, "oreille")
    bar(g, f"ame0_{tag}", root + Y_ * 0.05, root + X_ * 2.4 + Y_ * 0.15, 0.24, 0.1, 0.2, octo=False, ov=0.05)
    bar(g, f"ame1_{tag}", root + X_ * 2.3 + Y_ * 0.15, root + X_ * 4.2 + Y_ * 0.12, 0.14, 0.1, 0.2, octo=False, ov=0.05)
    for k, u_ in enumerate((1.7, 2.6)):
        bar(g, f"anneau{k}_{tag}", root + X_ * u_ + Y_ * 0.15, root + X_ * (u_ + 0.45) + Y_ * 0.15, 0.4 - 0.05 * k, 0.5, 0.6, octo=True, ov=0.0)
    bar(g, f"nodule_{tag}", root + X_ * 0.05, root + X_ * 0.75, 0.4, 0.3, 0.4, octo=True, ov=0.0)

outliner = [{"name": "head", "origin": [0, 24, 0], "uuid": nuid(),
             "children": [bone_node(masque)] + [bone_node(f"corne_{t}") for t in "lr"] + [bone_node(r) for r in RACINES]
             + [bone_node(f"oreille_{t}") for t in "lr"]}]


# ------------------------------------------------------------------ animations
# Intention sur un côté s (-1 gauche, +1 droit) : back > 0 ramène l'oreille vers l'arrière ; up > 0 relève.
# MIROIR D'AXES : seul endroit à toucher si la convention du mod change (guide, section 3 : +Y = le côté droit avance ; +Z = le côté droit monte).
SX, SY, SZ = -1, -1, +1


def mirror(s, swing, back, up):
    return SX * swing, s * SY * back, s * SZ * up


def kfc(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 3)), "y": str(round(y + 0.0, 3)), "z": str(round(z + 0.0, 3))}],
            "time": round(t, 3), "interpolation": "linear"}


def state(name, L, ear_b, ear_up, n_kf=None, cycles=1, regard=None):
    """Oreilles discrètes ; regard : fonction t -> échelle verticale de la fente (clignement, plissement)."""
    tr = {}
    for g, s_ in EARS:
        def e(t, s_=s_):
            ph = TAU * (cycles * t / L + (0.1 if s_ > 0 else 0))
            return mirror(s_, 0, ear_b + 0.5 * ear_up * math.sin(ph), ear_up * math.sin(ph + 0.8))
        tr[g] = e
    a = anim(name, L, tr, n_kf=n_kf)
    if regard is not None:
        n = int(round(L * 24))
        a["animators"][groups["regard"]["uuid"]] = {"name": "regard", "type": "bone",
                                                     "keyframes": [kfc("scale", i * L / n, 1, regard(i * L / n), 1) for i in range(n + 1)]}
    return a


# Clignement : une fois par boucle de repos (fermeture 0,08 s, réouverture 0,14 s)
blink = lambda t: 1 - 0.9 * bump(t, 5.1, 5.18, 5.2, 5.34)
idle = state("idle", 8.0, 0, 1.0, n_kf=32, cycles=2, regard=blink)
walk = state("walk", 1.6, 2, 1.0)
run = state("run", 1.0, 6, 1.4)
sneak = state("sneak", 3.0, -1, 0.5, regard=lambda t: 0.55 + 0.05 * math.sin(TAU * t / 3.0))     # affût : regard plissé
fly = state("fly", 2.4, 8, 1.2, n_kf=20)
glide = state("glide", 3.6, 10, 1.2, n_kf=28, cycles=2)


# ------------------------------------------------------------------ apparition et retrait
# Joués par-dessus l'état (guide 6.4) : rotations ajoutées, échelles multipliées.
def event(name, L, k_racine, k_corne, k_masque, k_oreille, k_regard, r_oreille, son=None):
    n = int(round(L * 24))
    times = [i * L / n for i in range(n + 1)]
    A = {}

    def put(g, sc, rot=None, sy=None):
        ks = [kfc("scale", t, sc(t), sc(t) if sy is None else sy(t), sc(t)) for t in times]
        if rot is not None:
            ks += [kfc("rotation", t, *rot(t)) for t in times]
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": ks}

    put("masque", k_masque)
    put("regard", lambda t: 1.0, sy=k_regard)
    for s_, tag in ((-1, "l"), (1, "r")):
        put(f"racines_{tag}", k_racine)
        put(f"corne_{tag}", k_corne)
        put(f"oreille_{tag}", k_oreille, lambda t, s_=s_: mirror(s_, 0, r_oreille(t), 0))
    if son:
        A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [{"channel": "sound", "data_points": [{"effect": son[1], "file": ""}], "time": son[0]}]}
    return {"uuid": nuid(), "name": name, "loop": "once", "override": False, "length": L, "snapping": 24, "selected": False, "animators": A}


# event_equip 1,6 s : 0–0,45 s les racines s'étendent depuis le pied des cornes ; 0,25–0,9 s les cornes percent (craquement
# d'os à 0,3 s, petit dépassement) ; 0,35–0,75 s le demi-masque se referme sur les yeux ; 0,6–1,0 s les oreilles se déplient ;
# 1,1–1,35 s le regard s'allume en dernier (la fente s'ouvre).
equip = event("event_equip", 1.6,
              k_racine=lambda t: 0.05 + 0.95 * sm(t, 0.0, 0.45),
              k_corne=lambda t: 0.04 + 0.96 * sm(t, 0.25, 0.85) + 0.06 * bump(t, 0.7, 0.85, 0.9, 1.1),
              k_masque=lambda t: sm(t, 0.35, 0.75),
              k_oreille=lambda t: 0.2 + 0.8 * sm(t, 0.6, 0.95),
              k_regard=lambda t: sm(t, 1.1, 1.3) + 0.15 * bump(t, 1.25, 1.3, 1.32, 1.45),
              r_oreille=lambda t: 26 * (1 - sm(t, 0.75, 1.15)) * sm(t, 0.55, 0.75),
              son=(0.3, "block.bone_block.break"))
# event_unequip 1,2 s : le regard s'éteint, les oreilles se replient, les cornes rentrent, le masque s'ouvre, les racines se
# retirent ; dernière image à l'échelle 0, gardée jusqu'au départ.
unequip = event("event_unequip", 1.2,
                k_racine=lambda t: 1 - sm(t, 0.7, 1.15),
                k_corne=lambda t: 1 - sm(t, 0.2, 0.8),
                k_masque=lambda t: 1 - sm(t, 0.5, 0.9),
                k_oreille=lambda t: 1 - sm(t, 0.1, 0.5),
                k_regard=lambda t: 1 - sm(t, 0.0, 0.15),
                r_oreille=lambda t: 26 * sm(t, 0.0, 0.3))

ANIMS = [idle, walk, run, sneak, fly, glide, equip, unequip]
import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons as _limiter
_m = {"animations": ANIMS}
_limiter(_m)
write(NOM, outliner, ANIMS, len(groups) + 1, (120, 600), 0, DENS)
