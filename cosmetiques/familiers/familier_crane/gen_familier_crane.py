"""Familier crâne : petit crâne cornu abyssal qui flotte près du joueur. Design original (os charbon, reflets violets, vert acide).
Écrit familier_crane.png, familier_crane_e.png et .build/familier_crane_brut.bbmodel à côté de ce script.

Hiérarchie (body = torse du joueur) :
  fam_elan    (attack/hurt uniquement : position dans le repère du joueur, jamais touché par les états)
  fam_orbite  (pivot au centre du joueur : rotation Y, 360° exacts en idle)
  fam_pos     (position : flottement, rapprochement de l'épaule, descente au flanc)
  fam_regard  (rotation : inclinaison, coups d'oeil)
  fam_snap    (attack/hurt uniquement : rotation)
  crane > machoire, vert1 > vert2 > vert3 > vert4, emit_braise, emit_braise2

Le modèle au repos est à (+15, 27, 0), nez vers -Z : rigide dans l'orbite, il regarde donc toujours l'avant de sa course.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # True : embarque le calque _e en seconde texture. Réactivé le 2026-11-03 (correctif du mod annoncé, à vérifier en jeu).
NOM = "familier_crane"
TEX = 512
TAU = 2 * math.pi

# ------------------------------------------------------------------ matières (teintes d'ailes_abyssales, os un peu relevé pour un si petit objet)
C_OMBRE = np.array((11, 8, 16), np.float32)
C_OS = np.array((54, 47, 68), np.float32)
C_HAUT = np.array((132, 106, 172), np.float32)
C_RIM = np.array((146, 92, 186), np.float32)
C_AURA = np.array((24, 74, 38), np.float32)
C_VEIN = np.array((104, 214, 46), np.float32)
C_VCORE = np.array((186, 255, 96), np.float32)
E_VERT = np.array((132, 255, 72), np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


# ------------------------------------------------------------------ tuiles peintes
TUILES = {}      # nom -> spec d'une plaque peinte (dimensions en px du modèle)


def tuile(nom, w, h, outer, holes=(), ridges=(), sillons=(), verts=(), glows=(), rond=0.1, relief=1.0, teinte=1.0):
    TUILES[nom] = dict(w=w, h=h, outer=outer, holes=holes, ridges=ridges, sillons=sillons, verts=verts, glows=glows, rond=rond, relief=relief, teinte=teinte)
    return nom


def peint(sp, W, H, seed):
    """Plaque découpée : relief peint (bevel d'après le masque, arêtes, sillons), veines vertes, orbites. Renvoie (RGBA, RGBA du calque _e)."""
    ss = 3
    GW, GH = W * ss, H * ss
    w, h = sp["w"], sp["h"]
    d = GW / w          # texels sur-échantillonnés par px du modèle

    def P(p):
        return ((p[0] + w / 2) * d, (h / 2 - p[1]) * d)

    def blur(im, r):
        return np.array(im.filter(ImageFilter.GaussianBlur(r * d)), np.float32) / 255

    def lignes(traits):
        im = Image.new("L", (GW, GH), 0)
        dr = ImageDraw.Draw(im)
        for pts, lw in traits:
            dr.line([P(p) for p in pts], fill=255, width=max(1, int(round(lw * d))), joint="curve")
        return im

    m = Image.new("L", (GW, GH), 0)
    dm = ImageDraw.Draw(m)
    dm.polygon([P(p) for p in sp["outer"]], fill=255)
    ho = Image.new("L", (GW, GH), 0)
    for poly in sp["holes"]:
        ImageDraw.Draw(ho).polygon([P(p) for p in poly], fill=255)
        dm.polygon([P(p) for p in poly], fill=0)
    if sp["rond"]:
        m = Image.fromarray(((blur(m, sp["rond"]) > 0.5) * 255).astype(np.uint8), "L")
    Ma = np.array(m, np.float32) / 255
    hauteur = blur(m, 0.30) * 0.75 + blur(m, 0.75) * 0.75
    if sp["ridges"]:
        hauteur = hauteur + blur(lignes(sp["ridges"]), 0.13) * 1.1
    sil = lignes(sp["sillons"]) if sp["sillons"] else None
    if sil is not None:
        hauteur = hauteur - blur(sil, 0.07) * 1.0
    hauteur = hauteur * sp["relief"]
    gy, gx = np.gradient(hauteur)
    k = d * 0.42
    nx, ny = -gx * k, gy * k          # ny > 0 : la pente regarde le haut de l'image
    nn = np.sqrt(nx * nx + ny * ny + 1)
    lum = np.clip((-0.30 * nx + 0.78 * ny + 0.55) / nn, 0, 1)
    r = np.random.default_rng(seed)
    bruit = np.array(Image.fromarray((r.random((9, 9)) * 255).astype(np.uint8), "L").resize((GW, GH), Image.BICUBIC), np.float32) / 255
    lum = lum * (0.94 + 0.12 * bruit)
    c = lerp(C_OMBRE, C_OS, np.clip(lum / 0.55, 0, 1)[..., None])
    c = lerp(c, C_HAUT, np.clip((lum - 0.58) / 0.28, 0, 1)[..., None] * 0.9)
    c = c * sp["teinte"]
    bord = np.clip(1 - blur(m, 0.14), 0, 1) * Ma
    bord_haut = bord * np.clip(ny * 1.2 + 0.25, 0, 1)
    c = lerp(c, C_RIM, np.clip(bord_haut * 3.2, 0, 1)[..., None] * 0.95)
    if sp["holes"]:
        c = lerp(c, C_OMBRE, np.clip(blur(ho, 0.16) * 2.4, 0, 1)[..., None] * 0.85)
    if sil is not None:
        c = lerp(c, C_OMBRE, (np.array(sil) > 127)[..., None] * 0.92)
    em = np.zeros((GH, GW), np.float32)
    if sp["verts"]:
        v = lignes(sp["verts"])
        c = lerp(c, C_AURA, np.clip(blur(v, 0.2) * 1.6, 0, 1)[..., None] * 0.6)
        c = lerp(c, C_VEIN, (np.array(v) > 127)[..., None])
        co = lignes([(pts, lw * 0.45) for pts, lw in sp["verts"]])
        c = lerp(c, C_VCORE, (np.array(co) > 127)[..., None])
        em = np.maximum(em, (np.array(v) > 127).astype(np.float32) * 0.8)
    if sp["glows"]:
        yy, xx = np.mgrid[0:GH, 0:GW]
        X, Y = (xx + 0.5) / d - w / 2, h / 2 - (yy + 0.5) / d
        for cx, cy, rx, ry, ang in sp["glows"]:
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            a, b = (X - cx) * ca + (Y - cy) * sa, -(X - cx) * sa + (Y - cy) * ca
            q = np.sqrt((a / rx) ** 2 + (b / ry) ** 2)
            c = lerp(c, C_OMBRE, np.clip((1.75 - q) / 0.4, 0, 1)[..., None])
            c = lerp(c, C_AURA, np.clip((1.3 - q) / 0.25, 0, 1)[..., None])
            c = lerp(c, C_VEIN, np.clip((1.05 - q) / 0.2, 0, 1)[..., None])
            c = lerp(c, C_VCORE, np.clip((0.62 - q) / 0.2, 0, 1)[..., None])
            em = np.maximum(em, np.clip((1.05 - q) / 0.3, 0, 1))
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(m.resize((W, H), Image.LANCZOS)) > 110
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    if al.any():
        out[~al, :3] = rgb[al].mean(axis=0).astype(np.uint8)
    e = np.array(Image.fromarray((em * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    e &= al
    oe = np.zeros((H, W, 4), np.uint8)
    oe[e, :3] = E_VERT.astype(np.uint8)
    oe[e, 3] = 255
    return out, oe


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
    for t in np.linspace(0, 1, 120):
        cx, cy = center(t)
        d_ = np.hypot(a - cx, b - cy) / hw(t)
        ok = d_ < dd
        dd[ok], tt[ok] = d_[ok], t
    c = np.empty(a.shape + (3,), np.float32)
    c[...] = (40, 34, 50)
    c = lerp(c, np.array((126, 96, 168), np.float32), (np.clip(1 - dd * 1.6, 0, 1) * 0.8)[..., None])
    c = lerp(c, np.array((12, 8, 16), np.float32), (np.clip((dd - 0.62) * 2.2, 0, 1) * 0.8)[..., None])
    c = lerp(c, C_VEIN, np.clip((tt - 0.5) / 0.28, 0, 1)[..., None])
    c = lerp(c, C_VCORE, (np.clip((tt - 0.72) / 0.2, 0, 1) * np.clip(1 - dd * 1.2, 0, 1))[..., None])
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(((dd < 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    out[~al, :3] = (40, 34, 50)
    te = np.array(Image.fromarray((tt * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS), np.float32) / 255
    eo = np.zeros((H, W, 4), np.uint8)
    e = al & (te > 0.55)
    eo[e, :3] = E_VERT.astype(np.uint8)
    eo[e, 3] = 255
    return out, eo


def paint_bone(BW=96, BH=16):
    """Os : ventre sombre, arête claire ; bandes de vertèbre."""
    a = np.zeros((BH, BW, 4), np.float32)
    for yy in range(BH):
        q = abs((yy + 0.5) / BH - 0.5) * 2
        for xx in range(BW):
            u = xx / (BW - 1)
            c_ = lerp(np.array((58, 50, 72.0)), np.array((20, 16, 28.0)), q ** 1.2)
            c_ = lerp(c_, np.array((146, 110, 192.0)), max(0.0, 1 - q * 2.2) * (0.6 + 0.3 * math.sin(u * 15)))
            a[yy, xx, :3] = c_
    a[..., 3] = 255
    return a.astype(np.uint8)


def paint_corne(BW=96, BH=16):
    """Corne : anneaux sombres à la base, pointe vert acide (u = 1)."""
    a = np.zeros((BH, BW, 4), np.float32)
    e = np.zeros((BH, BW, 4), np.uint8)
    for yy in range(BH):
        q = abs((yy + 0.5) / BH - 0.5) * 2
        for xx in range(BW):
            u = xx / (BW - 1)
            c_ = lerp(np.array((60, 50, 78.0)), np.array((16, 12, 22.0)), q ** 1.1)
            c_ = lerp(c_, np.array((150, 112, 196.0)), max(0.0, 1 - q * 2.4) * 0.7)
            if u < 0.62 and (xx // 9) % 2 == 0:
                c_ = c_ * 0.62
            k = sm(u, 0.78, 0.98)
            c_ = lerp(c_, np.array((116, 224, 50.0)), k)
            c_ = lerp(c_, np.array((196, 255, 110.0)), sm(u, 0.86, 1.0) * max(0.0, 1 - q))
            a[yy, xx, :3] = c_
            if k > 0.4:
                e[yy, xx] = (132, 255, 72, 255)
    a[..., 3] = 255
    return a.astype(np.uint8), e


def paint_braise(PT=48):
    """Éclat irrégulier : coeur vif, liseré sombre, une seule silhouette."""
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
    hb, hbe = paint_hook(96, 64)
    hs, hse = paint_hook(48, 32)
    co, coe = paint_corne()
    br = paint_braise()
    fixed = [("hook_big", hb, hbe), ("hook_small", hs, hse), ("bone", paint_bone(), None), ("corne", co, coe), ("braise", br, None)]

    def pack(dens):
        items = [(n, im.shape[1], im.shape[0]) for n, im, _ in fixed] + [(n, int(math.ceil(s["w"] * dens)), int(math.ceil(s["h"] * dens))) for n, s in TUILES.items()]
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
        dens -= 0.5
    UV.update(uv)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, im, ie in fixed:
        u0, v0, u1, v1 = UV[n]
        tex[v0:v1, u0:u1] = im
        if ie is not None:
            tex_e[v0:v1, u0:u1] = ie
    u0, v0, u1, v1 = UV["braise"]
    tex_e[v0:v1, u0:u1, :3] = br[..., :3]
    tex_e[v0:v1, u0:u1, 3] = br[..., 3]
    for i, (n, s) in enumerate(TUILES.items()):
        u0, v0, u1, v1 = UV[n]
        tex[v0:v1, u0:u1], tex_e[v0:v1, u0:u1] = peint(s, u1 - u0, v1 - v0, 40 + i)
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


# ------------------------------------------------------------------ formes des plaques (px, centrées ; haut de l'image = +Y de la plaque)
def miroir(demi):
    """Contour symétrique : demi-contour côté x > 0, de haut en bas."""
    return list(demi) + [(-x, y) for x, y in reversed(demi)]


def orbite_trou(s):
    """Orbite en amande oblique, plus basse vers le nez : regard mauvais, pas humain. s = ±1."""
    return [(s * 0.42, 0.55), (s * 1.10, 1.18), (s * 2.18, 1.42), (s * 2.42, 0.72), (s * 1.72, 0.02), (s * 0.82, -0.12)]


tuile("masque", 5.6, 4.0,
      miroir([(0.0, 1.98), (1.1, 1.88), (2.5, 1.96), (2.78, 1.1), (2.72, 0.0), (2.2, -0.9), (1.42, -1.95), (0, -1.95)]),
      holes=[orbite_trou(1), orbite_trou(-1), [(0.0, -0.45), (0.3, -1.0), (0.0, -1.55), (-0.3, -1.0)]],
      ridges=[([(0.0, 1.9), (0.0, -0.2)], 0.3), ([(2.42, -0.3), (1.5, -1.3)], 0.2), ([(-2.42, -0.3), (-1.5, -1.3)], 0.2)],
      sillons=[([(-1.7, -0.5), (-1.1, -1.1), (-1.2, -1.6)], 0.09)], teinte=1.1)

tuile("orbites", 5.2, 2.4, [(-2.6, -1.2), (2.6, -1.2), (2.6, 1.2), (-2.6, 1.2)],
      glows=[(1.42, 0.5, 1.06, 0.66, 22), (-1.42, 0.5, 1.06, 0.66, -22)], rond=0, relief=0.0, teinte=0.5)

# arcade : un seul V épais devant le masque, qui pèse sur les orbites
tuile("arcade", 6.1, 1.9,
      miroir([(0.0, 0.02), (1.1, 0.72), (2.2, 0.95), (3.02, 0.92), (2.92, 0.46), (2.0, 0.06), (0.95, -0.42), (0.42, -0.9), (0.0, -0.72)]),
      ridges=[([(0.2, -0.3), (1.2, 0.3), (2.8, 0.7)], 0.2), ([(-0.2, -0.3), (-1.2, 0.3), (-2.8, 0.7)], 0.2)], teinte=1.2)

tuile("calotte", 2.7, 3.5,                # haut de l'image = avant du crâne
      miroir([(0.0, 1.72), (0.9, 1.72), (1.35, 1.3), (1.35, -1.74), (0.0, -1.74)]),
      ridges=[([(0, 1.6), (0, -1.7)], 0.3)],
      sillons=[([(1.25, 0.5), (0.8, 0.2), (0.62, -0.5), (1.25, -1.0)], 0.09)],
      verts=[([(0.12, 0.6), (-0.1, -0.2), (0.08, -1.7)], 0.2)])

tuile("chanfrein", 3.5, 2.4,              # gauche de l'image = avant
      [(-1.75, 0.35), (-0.7, 1.2), (1.75, 1.2), (1.75, -1.2), (-0.7, -1.2), (-1.75, -0.35)],
      ridges=[([(-1.6, 0.05), (1.7, -0.05)], 0.18)],
      sillons=[([(-0.4, 1.16), (-0.1, 0.5), (0.5, 0.3)], 0.09)])

tuile("tempe", 3.5, 2.6,                  # gauche de l'image = avant
      [(-1.75, 0.95), (-1.25, 1.3), (1.75, 1.3), (1.75, -1.3), (-1.0, -1.3), (-1.75, -0.8)],
      ridges=[([(-1.0, -1.02), (1.7, -1.1)], 0.16)],
      sillons=[([(1.7, 0.7), (1.0, 0.45), (0.8, -0.1), (0.25, -0.35)], 0.09)],
      glows=[(-0.62, 0.32, 0.92, 0.42, 16)])

ARR = [(-1.28, 1.34), (1.28, 0.72), (1.28, -0.72), (-1.28, -1.34)]    # gauche de l'image = avant : se resserre vers la nuque
tuile("arriere", 2.56, 2.7, ARR, ridges=[([(-1.2, 0), (1.2, 0)], 0.2)], sillons=[([(-0.5, 1.1), (-0.2, 0.3), (0.45, 0.1)], 0.09)])
tuile("arriere_v", 2.56, 2.7, ARR, ridges=[([(-1.2, 0), (1.2, 0)], 0.26)], verts=[([(-1.2, 0.02), (-0.2, -0.1), (0.9, 0.05)], 0.2)])
tuile("arriere_t", 2.56, 2.7, ARR, holes=[[(-0.72, 0.6), (0.3, 0.42), (0.55, -0.1), (0.05, -0.55), (-0.68, -0.5)]])

tuile("nuque", 3.3, 3.3,
      miroir([(0.0, 1.65), (0.95, 1.5), (1.65, 0.75), (1.65, -0.75), (0.95, -1.5), (0.0, -1.65)]),
      ridges=[([(0, 1.5), (0, 0.6)], 0.26)], verts=[([(0, 1.35), (0, 0.8)], 0.16)])

tuile("nez", 2.6, 1.8,                    # haut de l'image = vers le crâne
      miroir([(0.0, 0.9), (0.95, 0.9), (1.28, 0.1), (0.85, -0.82), (0.0, -0.9)]),
      holes=[[(0.2, -0.1), (0.58, -0.05), (0.5, -0.55), (0.16, -0.5)], [(-0.2, -0.1), (-0.58, -0.05), (-0.5, -0.55), (-0.16, -0.5)]],
      ridges=[([(0, 0.8), (0, 0.05)], 0.26)], teinte=1.15)

ZIG = lambda W_, n, h_: [(-W_ / 2 + W_ * (i / (2 * n)), (-h_ if i % 2 else -h_ * 0.25)) for i in range(2 * n + 1)]
tuile("dents_h", 2.5, 1.1, [(-1.25, 0.55), (1.25, 0.55)] + [(x, y + 0.05) for x, y in reversed(ZIG(2.5, 4, 0.55))], rond=0.03, relief=0.7, teinte=1.7)
tuile("dents_c", 2.0, 0.9, [(-1.0, 0.45), (1.0, 0.45)] + [(x, y) for x, y in reversed(ZIG(2.0, 3, 0.45))], rond=0.03, relief=0.7, teinte=1.7)
tuile("dents_b", 2.2, 0.8, [(-1.1, -0.4), (1.1, -0.4)] + [(x, -y) for x, y in reversed(ZIG(2.2, 3, 0.4))], rond=0.03, relief=0.7, teinte=1.45)
tuile("mentonniere", 3.4, 4.0,            # haut de l'image = avant
      [(-0.95, 2.0), (0.95, 2.0), (1.3, 1.0), (1.7, -2.0), (0.9, -2.0), (0.62, -0.4), (-0.62, -0.4), (-0.9, -2.0), (-1.7, -2.0), (-1.3, 1.0)],
      ridges=[([(0, 1.9), (0, 0.0)], 0.25)])
tuile("palais", 2.4, 3.0, [(-1.0, 1.5), (1.0, 1.5), (1.2, -1.5), (-1.2, -1.5)], verts=[([(0, 1.1), (0, -1.2)], 0.42)], rond=0.15, relief=0.3, teinte=0.5)

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


def plate(g, name, c, X, Y, tile, w=None, h=None, th=0.3, coque=False):
    """Plaque fine : contour par l'alpha, tranches transparentes. u suit X, le haut de l'image est +Y.
    coque=True : seule la face tournée vers l'extérieur du crâne est peinte (pas de double couche vue de biais)."""
    X = unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    if tile in TUILES:
        w, h = w or TUILES[tile]["w"], h or TUILES[tile]["h"]
    u0, v0, u1, v1 = UV[tile]
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    south, north = [u0, v0, u1, v1], [u1, v0, u0, v1]
    if coque:
        if R_[:, 2] @ (c - (C0 + V(0, 0.55, 0))) > 0:
            north = CLEAR
        else:
            south = CLEAR
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
         {"south": south, "north": north, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


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
        cube(g, name + "o", p + (-ov + 0.03, -r * 0.97, -r * 0.97), p + (L + ov - 0.03, r * 0.97, r * 0.97), p, euler(R45), faces)
    else:
        cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R45), faces)


def chain(g, name, pts, r0, r1, u0=0.0, u1=1.0, octo_until=1.0, tile="bone"):
    """Os effilé : tronçons qui se recouvrent, rayon qui décroît, couleur continue."""
    n = len(pts) - 1
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        bar(g, f"{name}{i}", pts[i], pts[i + 1], lerp(r0, r1, (t0 + t1) / 2), lerp(u0, u1, t0), lerp(u0, u1, t1), octo=t1 <= octo_until + 1e-6, tile=tile)


def hook(g, name, p, X, Y, L, tile="hook_small", core=1, z_ofs=0.07):
    """Griffe : peau découpée + âme pleine plus étroite. Elle part de p vers X et se recourbe vers Y."""
    p, X = np.asarray(p, float), unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    n = np.cross(X, Y)
    lo, hi = HOOK_BB
    c = p + X * (0.49 * L) + Y * ((lo + hi) / 2 * L) + n * z_ofs
    plate(g, name, c, X, Y, tile, w=1.02 * L, h=(hi - lo) * L)
    center, hw = hook_shape(L, CURVE)
    for j in range(core):
        t0, t1 = j / core * 0.72, (j + 1) / core * 0.72
        a, b = center(t0), center(t1)
        bar(g, f"{name}c{j}", p + X * a[0] + Y * a[1], p + X * b[0] + Y * b[1], max(0.14, hw((t0 + t1) / 2) * 0.62), 0.6, 0.9, octo=False, ov=0.05)
    return p + X * center(1)[0] + Y * center(1)[1]


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


C0 = V(15.0, 27.0, 0.0)       # centre du crâne au repos : sur l'orbite, côté droit du joueur


def L(x, y, z):
    return C0 + V(x, y, z)


EX, EY, EZ = V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)

g_elan = group("fam_elan", [0, 27, 0])
g_orb = group("fam_orbite", [0, 27, 0], parent=g_elan)
g_pos = group("fam_pos", C0, parent=g_orb)
g_reg = group("fam_regard", C0, parent=g_pos)
g_snap = group("fam_snap", C0, parent=g_reg)
g_cr = group("crane", C0, parent=g_snap)
g_jaw = group("machoire", L(0, -1.0, 0.5), parent=g_cr, rotation=(-5, 0, 0))     # légèrement entrouverte au repos

# âme du crâne, plus étroite vers la nuque
AY = 0.55
bar(g_cr, "ame", L(0, AY, -1.75), L(0, AY, 1.0), 1.72, 0.1, 0.5, ov=0.0)
bar(g_cr, "ame_nuque", L(0, AY, 0.95), L(0, AY, 2.6), 1.08, 0.1, 0.5, ov=0.0)
bar(g_cr, "ame_nez", L(0, -0.55, -3.35), L(0, -0.35, -1.6), 0.74, 0.1, 0.5, ov=0.0)

# plaques : deux ceintures d'octogone, droite devant, resserrée vers la nuque
RAD = 2.72
RN, ZA, ZN = 1.56, 0.92, 2.98            # rayon et z de la nuque, z de la jointure
plate(g_cr, "masque", L(0, AY - 0.15, -2.42), EX, V(0, 1, -0.10), "masque", coque=True)
plate(g_cr, "orbites", L(0, AY + 0.02, -1.98), EX, EY, "orbites", coque=True)
plate(g_cr, "arcade", L(0, AY + 1.18, -2.72), EX, V(0, 1, -0.28), "arcade")
plate(g_cr, "nuque", L(0, AY, ZN + 0.02), EX, EY, "nuque", coque=True)
for k in range(8):
    phi = k * TAU / 8                     # 0 : dessus ; 2 : côté +X
    n = V(math.sin(phi), math.cos(phi), 0)
    tan = V(math.cos(phi), -math.sin(phi), 0)
    tag = str(k)
    # ceinture avant (image : gauche = avant)
    if k == 0:
        plate(g_cr, "calotte", L(0, AY + RAD, -0.72), EX, V(0, 0, -1), "calotte", coque=True)
    elif k == 4:
        plate(g_cr, "fond", L(0, AY - RAD + 0.2, -0.45), EX, V(0, 0, -1), "calotte", w=2.3, h=2.8, coque=True)
    else:
        tu = "tempe" if k in (2, 6) else "chanfrein"
        Yk = -tan if k < 4 else tan
        if k in (3, 5):
            plate(g_cr, f"ceint_{tag}", L(*(n * RAD + Yk * 0.32 + V(0, AY, -0.5))), EZ, Yk, tu, w=3.0, h=1.75, coque=True)
        else:
            plate(g_cr, f"ceint_{tag}", L(*(n * RAD + V(0, AY, -0.72))), EZ, Yk, tu, coque=True)
    # ceinture arrière
    d_ = unit(n * (RN - RAD) + EZ * (ZN - ZA))
    ctr = n * ((RAD + RN) / 2) + V(0, AY, (ZA + ZN) / 2)
    tu = "arriere_v" if k == 0 else ("arriere_t" if k in (2, 6) else "arriere")
    plate(g_cr, f"arr_{tag}", L(*ctr), d_, -tan if 0 < k < 4 else tan, tu, coque=True)

for s_, tag in ((-1, "l"), (1, "r")):
    # corne : courte, part de l'angle du front et se recourbe vers l'arrière
    b = L(s_ * 1.95, AY + 2.15, -0.9)
    pts = [b, b + V(s_ * 0.6, 1.1, 0.0), b + V(s_ * 1.25, 1.95, 0.4), b + V(s_ * 1.62, 2.55, 1.15)]
    chain(g_cr, f"corne_{tag}", pts, 0.6, 0.24, 0.0, 0.62, octo_until=0.7, tile="corne")
    hook(g_cr, f"pointe_{tag}", pts[-1] - unit(pts[-1] - pts[-2]) * 0.15, pts[-1] - pts[-2], V(0, -1, 0.3), 2.0, core=1)
    bar(g_cr, f"bague_{tag}", b + V(s_ * -0.1, -0.2, 0), b + V(s_ * 0.17, 0.3, 0.01), 0.78, 0.05, 0.2, ov=0.0)
    # dents du haut et croc
    plate(g_cr, f"dents_h_{tag}", L(s_ * 1.2, -1.25, -2.35), EZ, EY, "dents_c")
    hook(g_cr, f"croc_{tag}", L(s_ * 0.98, -0.95, -3.05), V(0, -1, -0.12), V(0, 0, 1), 1.65, core=1)

# museau
plate(g_cr, "nez", L(0, -0.05, -3.02), EX, V(0, 0.38, 1), "nez")
plate(g_cr, "dents_h", L(0, -1.05, -3.42), EX, EY, "dents_h")
plate(g_cr, "palais", L(0, -1.28, -1.9), EX, V(0, 0, -1), "palais")

# mâchoire : deux branches, une mentonnière, dents et crocs qui remontent
for s_, tag in ((-1, "l"), (1, "r")):
    chain(g_jaw, f"branche_{tag}", [L(s_ * 1.5, -1.25, 0.3), L(s_ * 1.55, -2.0, -0.9), L(s_ * 1.12, -2.25, -2.9)], 0.38, 0.28, 0.3, 0.7)
    plate(g_jaw, f"dents_b_{tag}", L(s_ * 1.22, -1.7, -1.95), EZ, EY, "dents_c")
    hook(g_jaw, f"croc_b_{tag}", L(s_ * 0.82, -2.0, -3.02), V(0, 1, -0.1), V(0, 0, 1), 1.25, core=1)
bar(g_jaw, "menton", L(-1.1, -2.3, -2.95), L(1.1, -2.3, -2.95), 0.33, 0.3, 0.6)
plate(g_jaw, "mentonniere", L(0, -2.52, -1.1), EX, V(0, 0, -1), "mentonniere")
plate(g_jaw, "dents_b", L(0, -1.88, -3.24), EX, EY, "dents_b")

# traîne : 4 vertèbres imbriquées
LENS = [2.5, 2.3, 2.1, 1.9]
PENTE = [-6, -8, -8, -6]
RV = [0.92, 0.76, 0.62, 0.48]
QUEUE = L(0, 0.1, 2.95)
VP, VD = [QUEUE], []
for L_, a in zip(LENS, PENTE):
    d_ = V(0, math.sin(math.radians(a)), math.cos(math.radians(a)))
    VD.append(d_)
    VP.append(VP[-1] + d_ * L_)
SEG, par = [], g_cr
for i in range(4):
    SEG.append(group(f"vert{i + 1}", VP[i], parent=par))
    par = SEG[-1]
for i, (g, p, d_, L_, r) in enumerate(zip(SEG, VP, VD, LENS, RV)):
    u0, u1 = i / 4 * 0.9, (i + 1) / 4 * 0.9
    bar(g, f"vert_c{i}", p + d_ * 0.32, p + d_ * (0.72 * L_), r, u0, u1, ov=0.05)
    bar(g, f"col{i}", p - d_ * 0.1, p + d_ * (L_ + 0.05), r * 0.5, u0, u1, octo=False, ov=0.03)
    hook(g, f"epine{i}", p + d_ * (0.5 * L_) + EY * r * 0.8, EY + d_ * 0.6, d_, lerp(2.3, 1.2, i / 3), core=1)
    for s_, tag in ((-1, "l"), (1, "r")):
        hook(g, f"apo{i}_{tag}", p + d_ * (0.5 * L_) + EX * s_ * r * 0.8, EX * s_ + d_ * 0.6, d_, lerp(1.7, 0.95, i / 3), core=0)
hook(SEG[-1], "dard", VP[-1] - VD[-1] * 0.2, VD[-1], EY, 2.5, "hook_big", core=2)

# points de départ des braises : aux orbites
EMITS = [group("emit_braise", L(1.4, AY + 0.1, -2.75), parent=g_cr), group("emit_braise2", L(-1.4, AY + 0.1, -2.75), parent=g_cr)]

# particule : recette validée (une plaque, face up seule, y >= 0,3)
PG = group("particle_braise", [0, 0, 0])
_w = 3.2
_u0, _v0, _u1, _v1 = UV["braise"]
cube(PG, "braise", [-_w / 2, 0.3, -_w / 2], [_w / 2, 0.6, _w / 2], [0, 0, 0], (0, 0, 0), {"up": [_u0, _v0, _u1, _v1]})

outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone_node(g_elan)]}, bone_node(PG)]


# ------------------------------------------------------------------ animations
# Guide, section 3 : +X = le haut part vers l'arrière, donc le nez (-Z) monte et ce qui pointe vers +Z descend. +Y = le côté droit (+X) avance,
# donc le nez part vers -X et ce qui pointe vers +Z part vers +X. Position +Y : monte ; +X : droite du joueur.
def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 3)), "y": str(round(v[1] + 0.0, 3)), "z": str(round(v[2] + 0.0, 3))}], "time": round(t, 3), "interpolation": "linear"}


def anim(name, length, tracks, n_kf=None, loop="loop"):
    """tracks : groupe -> {"rotation": t -> (x,y,z), "position": t -> (x,y,z)}."""
    n = n_kf or max(6, int(round(length * 10)))
    times = [i * length / n for i in range(n + 1)]
    A = {groups[g]["uuid"]: {"name": g, "type": "bone", "keyframes": [kf(ch, t, f(t)) for ch, f in chans.items() for t in times]} for g, chans in tracks.items()}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


WV = [0.6, 0.85, 1.05, 1.25]


def etat(name, T, pos, regard, jaw, ty, tx, amp_y, amp_x, cycles, lag=0.14, orbite=None, n_kf=None):
    """Un état : pos(t), regard(t), mâchoire(t), traîne (bases ty/tx par vertèbre, ondulation amp_y/amp_x, déphasée en cascade)."""
    tr = {g_pos: {"position": pos}, g_reg: {"rotation": regard}, g_jaw: {"rotation": lambda t: (-jaw(t), 0, 0)}}
    if orbite:
        tr[g_orb] = {"rotation": lambda t: (0, orbite(t), 0)}
    for i, g in enumerate(SEG):
        def f(t, i=i):
            ph = TAU * (cycles * t / T - lag * i)
            return (tx[i] + amp_x * WV[i] * math.sin(ph + 1.1), ty[i] + amp_y * WV[i] * math.sin(ph), 0)
        tr[g] = {"rotation": f}
    return anim(name, T, tr, n_kf=n_kf)


def s_(T, k, ph=0.0):
    return lambda t: math.sin(TAU * k * t / T + ph)


# idle : 360° exacts en 12 s, plus vite aux deux passages à travers le plan des ailes ; penché vers l'intérieur de la virée.
TI = 12.0
def orbite_idle(t):
    u = t / TI
    return 360 * u + 12 * (math.sin(3 * TAU * (u - 0.25)) - 1)


def pos_idle(t):
    return (0, 1.15 * math.sin(TAU * 4 * t / TI) + 0.75 * math.sin(TAU * t / TI + 1.0), 0)


def regard_idle(t):
    coup = bump(t, 4.8, 5.4, 6.6, 7.2)      # coup d'oeil vers le joueur, puis reprend sa route
    return (3.5 * math.sin(TAU * 3 * t / TI), 26 * coup, 8 + 2.5 * math.sin(TAU * 2 * t / TI))


def claque(t, a, ouv=26):
    """Ouvre vite, referme d'un coup, léger rebond : ouverture > 0 en degrés."""
    return ouv * bump(t, a, a + 0.16, a + 0.26, a + 0.34) + 0.22 * ouv * bump(t, a + 0.34, a + 0.42, a + 0.42, a + 0.56)


def jaw_idle(t):
    return 3 * (0.5 + 0.5 * math.sin(TAU * 3 * t / TI)) + claque(t, 2.6) + claque(t, 9.0) + claque(t, 9.7, 18)


idle = etat("idle", TI, pos_idle, regard_idle, jaw_idle, [-9, -9, -9, -9], [2, 2, 1, 1], 8, 4, 3, orbite=orbite_idle, n_kf=144)

# perchoir : près de l'épaule droite, devant les ailes, traîne déviée vers l'extérieur
PX, PY, PZ = -5.3, 0.3, -5.5
TAIL_OUT = [46, 20, 16, 14]
TW = 1.6
walk = etat("walk", TW,
            lambda t: (PX + 0.3 * math.sin(TAU * t / TW), PY + 0.55 * math.sin(TAU * 2 * t / TW), PZ),
            lambda t: (2.5 * math.sin(TAU * 2 * t / TW + 0.6), -6 + 3 * math.sin(TAU * t / TW), 3 * math.sin(TAU * t / TW)),
            lambda t: 2 + 2 * math.sin(TAU * t / TW),
            TAIL_OUT, [4, 3, 2, 2], 8, 4, 1)

TR = 1.0
run = etat("run", TR,
           lambda t: (PX + 0.2 * math.sin(TAU * t / TR), PY - 0.5 + 0.8 * math.sin(TAU * 2 * t / TR), PZ - 0.8),
           lambda t: (-9 + 2.5 * math.sin(TAU * 2 * t / TR + 0.6), -4, 4 * math.sin(TAU * t / TR)),
           lambda t: 1 + 1 * math.sin(TAU * 2 * t / TR),
           [58, 18, 12, 10], [3, 2, 2, 1], 7, 3, 1, n_kf=12)

TF = 2.4
fly = etat("fly", TF,
           lambda t: (PX - 0.2, PY + 0.8 + 1.0 * math.sin(TAU * t / TF), PZ - 4.5),
           lambda t: (-6 + 3 * math.sin(TAU * t / TF + 0.5), -3 + 3 * math.sin(TAU * t / TF), 4 * math.sin(TAU * t / TF + 1.2)),
           lambda t: 3 + 3 * math.sin(TAU * t / TF),
           [64, 26, 20, 14], [5, 3, 2, 2], 8, 5, 1, n_kf=24)

# glide : le joueur est couché et le familier suit le torse : on relève le nez dans le sens du vol, c'est-à-dire vers +Y du torse.
TG = 3.6
glide = etat("glide", TG,
             lambda t: (PX + 1.0, PY + 0.6 * math.sin(TAU * t / TG), PZ + 1.5),
             lambda t: (62 + 2.5 * math.sin(TAU * t / TG), 0, 3 * math.sin(TAU * t / TG + 1.2)),
             lambda t: 2 + 2 * math.sin(TAU * t / TG),
             [30, 10, 6, 4], [-2, -1, -1, 0], 7, 3, 1, n_kf=24)

# sneak : descend au flanc, museau bas, traîne relâchée vers le bas et l'extérieur
TS = 3.0
sneak = etat("sneak", TS,
             lambda t: (-1.4 + 0.2 * math.sin(TAU * t / TS), -12.2 + 0.5 * math.sin(TAU * t / TS), -2.4),
             lambda t: (-10 + 2 * math.sin(TAU * t / TS), -5, 2 * math.sin(TAU * t / TS + 1)),
             lambda t: 1 + 1 * math.sin(TAU * t / TS),
             [52, 18, 12, 8], [14, 6, 4, 3], 4, 2, 1, n_kf=20)


# attack : claque vers l'avant du joueur et revient ; hurt : recul et tremblement. Une fois, retour à 0. Seuls fam_elan, fam_snap et machoire (delta) sont animés.
def _elan(t):
    return bump(t, 0.06, 0.20, 0.30, 0.70)


attack = anim("attack", 0.8, {
    g_elan: {"position": lambda t: (0, 0.8 * _elan(t), -6.5 * _elan(t))},
    g_snap: {"rotation": lambda t: (10 * bump(t, 0.0, 0.1, 0.1, 0.22) - 14 * bump(t, 0.12, 0.24, 0.3, 0.7), 0, 0)},
    g_jaw: {"rotation": lambda t: (-34 * bump(t, 0.0, 0.14, 0.14, 0.25) + 5 * bump(t, 0.22, 0.27, 0.3, 0.5), 0, 0)},
}, n_kf=24, loop="once")

hurt = anim("hurt", 0.8, {
    g_elan: {"position": lambda t: (0.9 * bump(t, 0.0, 0.06, 0.2, 0.6) * math.sin(TAU * t * 7), 1.6 * bump(t, 0.0, 0.08, 0.16, 0.65), 4.0 * bump(t, 0.0, 0.08, 0.16, 0.65))},
    g_snap: {"rotation": lambda t: (20 * bump(t, 0.0, 0.08, 0.16, 0.65), 0, 9 * bump(t, 0.0, 0.05, 0.2, 0.66) * math.sin(TAU * t * 6))},
    g_jaw: {"rotation": lambda t: (-16 * bump(t, 0.02, 0.1, 0.2, 0.55), 0, 0)},
}, n_kf=24, loop="once")

PF, PR = 3.0, 6.0
fall_p = anim("particle_braise_fall", PF, {PG: {"rotation": lambda t: (24 * math.sin(TAU * t / PF), 360 * t / PF, 18 * math.cos(2 * TAU * t / PF))}}, n_kf=24)
rest_p = anim("particle_braise_rest", PR, {PG: {"rotation": lambda t: (0, 0, 1.2 * math.sin(TAU * t / PR))}}, n_kf=12)

ANIMS = [idle, walk, run, fly, glide, sneak, attack, hurt, fall_p, rest_p]

assert 40 <= len(elements) <= 120, f"budget : {len(elements)} cubes"
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
retirer_particules(model)
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      f"densité {DENS:.1f} texels/px ; {len(EMITS)} emit_")
