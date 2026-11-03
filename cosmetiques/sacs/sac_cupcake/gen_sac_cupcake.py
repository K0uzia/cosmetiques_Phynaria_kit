"""Sac cupcake : petit sac à dos en forme de cupcake fraise, porté dans le dos. Ensemble « Pâtisserie ». Design original.
Écrit sac_cupcake.png, sac_cupcake_e.png et .build/sac_cupcake_brut.bbmodel à côté de ce script.

- Caissette : anneau de 16 lamelles plissées (peau découpée, rayures fraise / crème), évasée vers le haut, fond plein.
- Glaçage : dôme en gradins octogonaux fins (âme pleine), bordé d'un anneau de plaques découpées dont le bas
  coule en gouttes arrondies sur la caissette. Vermicelles peints sur le dessus (planaire, continus d'un gradin à l'autre).
- Cerise : trois disques verticaux croisés + un disque horizontal (peau ronde) autour d'une âme pleine, queue articulée.
- Bretelles chocolat : devant (z = -2,2), pont sur l'épaule caché sous la tête, dos entre le joueur et le sac.
Groupe de premier niveau `body`. Le dos du joueur est à z = +2 : rien du sac ne descend sous z = 2,15.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # calque _e embarqué en seconde texture (correctif du clignotement annoncé le 2026-11-03, à vérifier en jeu)
NOM = "sac_cupcake"
TEX = 512
DENS = 24           # texels par px du modèle
TAU = 2 * math.pi
rng = np.random.default_rng(11)

# ------------------------------------------------------------------ dimensions (px du modèle)
ZC = 4.5                                    # axe du cupcake, en arrière du dos
YB, YT = 13.6, 17.7                         # caissette : bas, haut (le haut est caché sous le glaçage)
CB, CT = (2.75, 1.5), (3.1, 1.74)           # demi-axes (x, z) de la caissette en bas et en haut
NS = 16                                     # lamelles
YP = 18.35                                  # haut de l'anneau de gouttes = base du dôme
DT = (3.58, 2.03)                           # anneau de gouttes : demi-axes en haut (centre des plaques)
YD = 15.0                                   # bas des plus longues gouttes
GA, GB, GH = 3.8, 2.22, 2.45                # dôme : demi-axes x, z, hauteur
ND = 14                                     # plaques de gouttes
PP = 2.7                                    # exposant du profil du dôme (superellipse : plus gonflé qu'une demi-ellipse)
CR = 0.9                                    # rayon de la cerise
CY = YP + GH + CR - 0.12                    # centre de la cerise (posée, un peu enfoncée)

# ------------------------------------------------------------------ couleurs (bases poussées vers le blanc : lumière chaude de nuit)
GL_HI, GL_BASE, GL_SH, GL_DEEP = (np.array(c, np.float32) for c in ((255, 236, 242), (252, 190, 208), (226, 132, 164), (184, 84, 120)))
CREME, CREME_SH = np.array((255, 250, 240), np.float32), np.array((214, 194, 176), np.float32)
FRAISE, FRAISE_SH = np.array((240, 104, 134), np.float32), np.array((168, 50, 84), np.float32)
CHOCO = [np.array(c, np.float32) for c in ((58, 30, 22), (100, 56, 38), (150, 98, 66))]
CER = [np.array(c, np.float32) for c in ((96, 6, 22), (206, 24, 50), (250, 92, 104), (255, 238, 238))]
SPR = [(255, 255, 250), (140, 222, 190), (255, 222, 96), (186, 156, 244), (104, 60, 42), (124, 186, 252)]


def lerp(a, b, k):
    return a + (b - a) * k


def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


# ------------------------------------------------------------------ peinture : f(x, y) en px de la tuile (x à droite, y vers le bas)
TILES = {}          # nom -> (rgba, e_rgba)


def tile(name, w, h, fn, dens=DENS, ss=4):
    W, H = max(2, int(round(w * dens))), max(2, int(round(h * dens)))
    gy, gx = np.mgrid[0:H * ss, 0:W * ss]
    x, y = (gx + 0.5) / (W * ss) * w, (gy + 0.5) / (H * ss) * h
    rgb, cov, glow = fn(x, y)
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    c = np.array(Image.fromarray(rgb, "RGB").resize((W, H), Image.LANCZOS), np.float32)
    a = np.array(Image.fromarray((np.clip(cov, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    if a.any():
        c[~a] = c[a].mean(axis=0)
    e = c * 0.07                                   # fond additif très sombre (évite le saumon mat la nuit)
    if glow is not None:
        g = np.array(Image.fromarray((np.clip(glow, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS), np.float32)[..., None] / 255
        e = lerp(e, np.array((255, 228, 232), np.float32), np.clip(g * 1.6, 0, 1))
    out = np.dstack([c, a * 255]).astype(np.uint8)
    eo = np.dstack([e, a * 255]).astype(np.uint8)
    eo[~a] = 0
    TILES[name] = (out, eo)


def blurmask(m, r_px, ss_dens):
    """Arrondit les angles rentrants d'un masque : flou puis seuil."""
    im = Image.fromarray((m * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(r_px * ss_dens))
    return np.array(im, np.float32) / 255 > 0.5


# Lamelle de caissette : pli (milieu clair, plis sombres), ombre de recouvrement sous le glaçage, coins bas arrondis
SW_, SH_ = 1.24, math.hypot(YT - YB, CT[0] - CB[0])


def slat_fn(col, sh):
    def f(x, y):
        u = x / SW_
        k = np.abs(u - 0.5) * 2
        c = lerp(col, sh, (0.42 * k ** 1.6)[..., None])
        c = lerp(c, sh * 0.9, ((k > 0.84) * 0.55)[..., None])                       # pli marqué (3 texels)
        top = np.clip(1 - y / 1.35, 0, 1) ** 1.4                                     # ombre portée par le glaçage
        c = lerp(c, sh * 0.78, (top * 0.75)[..., None])
        c = lerp(c, sh, (np.clip((y - (SH_ - 0.5)) / 0.5, 0, 1) * 0.35)[..., None])   # contact du fond
        r = 0.28
        cx = np.clip(x, r, SW_ - r)
        cy = np.clip(y, 0, SH_ - r)
        cov = (np.hypot(x - cx, y - cy) <= r).astype(np.float32)
        return c, cov, None
    return f


tile("slat_creme", SW_, SH_, slat_fn(CREME, CREME_SH))
tile("slat_fraise", SW_, SH_, slat_fn(FRAISE, FRAISE_SH))


# Plaque de gouttes : bandeau plein en haut, gouttes à bout rond
DW = 1.72
DH = None


def drip_fn(drops, seed):
    def f(x, y):
        h = DH
        m = (y < 1.05 + 0.12 * np.sin(x * 4.1 + seed)).astype(np.uint8)
        dl = np.zeros_like(x)
        for xc, L, w in drops:
            r = w / 2
            stem = (np.abs(x - xc) < r * 0.86) & (y < L - r)
            bulb = np.hypot(x - xc, y - (L - r)) < r
            m |= (stem | bulb).astype(np.uint8)
            dl = np.maximum(dl, np.clip(1 - np.abs(x - (xc - r * 0.3)) / (r * 0.45), 0, 1) * (y > 0.9) * (y < L - r * 0.6))
        m = blurmask(m, 0.1, x.shape[1] / DW)
        edge = np.array(Image.fromarray((m * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.12 * x.shape[1] / DW)), np.float32) / 255
        c = lerp(GL_BASE, GL_SH, (np.clip(y / h, 0, 1) * 0.55)[..., None])
        c = lerp(c, GL_HI, (np.clip(1 - y / 0.32, 0, 1) * 0.8)[..., None])            # liseré de lumière en haut du bourrelet
        c = lerp(c, GL_HI, (dl * 0.7)[..., None])                                     # reflet le long des gouttes
        c = lerp(c, GL_DEEP, (np.clip((0.72 - edge) * 2.4, 0, 1) * 0.75)[..., None])  # bord sombre : se détache de la caissette
        return c, m.astype(np.float32), None
    return f


DH = 0
DROPS = [
    [(0.32, 2.15, 0.52), (1.18, 3.1, 0.62)],
    [(0.62, 3.25, 0.66), (1.42, 1.75, 0.46)],
    [(0.3, 1.7, 0.44), (0.95, 2.55, 0.58), (1.5, 1.45, 0.4)],
]
_top_pt = V(DT[0], YP, 0)
DH = 3.45
for i, d in enumerate(DROPS):
    tile(f"drip{i}", DW, DH, drip_fn(d, i * 1.7))


# Dessus du glaçage : projection planaire (x, z), dégradé radial et vermicelles (≥ 3,8 texels de large)
TW_, TH_ = 2 * GA, 2 * GB
SPRINKLES = []
_tries = 0
while len(SPRINKLES) < 22 and _tries < 4000:
    _tries += 1
    px_, pz_ = rng.uniform(-GA, GA), rng.uniform(-GB, GB)
    rho = math.hypot(px_ / GA, pz_ / GB)
    if not (0.3 < rho < 0.86) or any(math.hypot(px_ - a, pz_ - b) < 0.75 for a, b, _, _ in SPRINKLES):
        continue
    SPRINKLES.append((px_, pz_, rng.uniform(0, math.pi), SPR[len(SPRINKLES) % len(SPR)]))


def prof(y):
    """Rayon relatif du dôme à la hauteur y."""
    h = np.clip((np.asarray(y, float) - YP) / GH, 0, 1)
    return (1 - h ** PP) ** (1 / PP)


def gcol(rho):
    """Couleur du glaçage selon le rayon relatif : la même pour le dessus et les côtés des gradins, pour fondre les marches."""
    c = lerp(GL_HI, GL_BASE, (np.clip(rho / 0.8, 0, 1) ** 1.4)[..., None])
    return lerp(c, GL_SH, (np.clip((rho - 0.8) / 0.2, 0, 1) * 0.7)[..., None])


def gtop_fn(x, y):
    X, Z = x - GA, y - GB
    rho = np.clip(np.hypot(X / GA, Z / GB), 0, 1)
    c = gcol(rho)
    for sx, sz, a, col in SPRINKLES:
        L, r = 0.26, 0.085
        dx, dz = math.cos(a), math.sin(a)
        t = np.clip((X - sx) * dx + (Z - sz) * dz, -L, L)
        d = np.hypot(X - sx - t * dx, Z - sz - t * dz)
        c = np.where((d < r)[..., None], np.array(col, np.float32), c)
        c = np.where(((d < r * 0.45) & (t < -L * 0.2))[..., None], np.minimum(np.array(col, np.float32) + 60, 255), c)
    return c, np.ones_like(x), None


tile("gl_top", TW_, TH_, gtop_fn)


def gside_fn(x, y):
    # y : 0 = haut du dôme (YP + GH), GH = base. Côtés des gradins : plus sombres en bas, comme la normale du dôme
    c = gcol(prof(YP + GH - y)) * 0.96
    return c, np.ones_like(x), None


tile("gl_side", 0.4, GH, gside_fn)
tile("gl_under", 0.6, 0.6, lambda x, y: (np.broadcast_to(GL_DEEP * 0.92, x.shape + (3,)).copy(), np.ones_like(x), None))


def paper_fn(x, y):
    c = lerp(CREME_SH, CREME, (0.6 + 0.4 * np.sin(x * 9.0))[..., None] * 0.8)
    return c, np.ones_like(x), None


tile("paper", 1.0, 1.0, paper_fn)


# Cerise : disque ombré comme une sphère, reflet en haut à gauche (seul point lumineux du calque _e)
CD = 2 * CR + 0.1


def cherry_fn(x, y):
    X, Y = (x - CD / 2) / CR, -(y - CD / 2) / CR
    r = np.hypot(X, Y)
    cov = (r < 1).astype(np.float32)
    nz = np.sqrt(np.clip(1 - r * r, 0, 1))
    lam = np.clip(-0.42 * X + 0.55 * Y + 0.72 * nz, 0, 1)
    c = lerp(CER[0], CER[1], np.clip(lam * 1.6, 0, 1)[..., None])
    c = lerp(c, CER[2], np.clip((lam - 0.72) * 3, 0, 1)[..., None])
    dimple = np.hypot(X, (Y - 0.88) * 1.6) < 0.2
    c = np.where(dimple[..., None], CER[0], c)
    hl = np.hypot((X + 0.34) / 1.25, Y - 0.38) < 0.17
    c = np.where(hl[..., None], CER[3], c)
    return c, cov, hl.astype(np.float32)


tile("cerise", CD, CD, cherry_fn)
tile("cerise_coeur", 0.5, 0.5, lambda x, y: (np.broadcast_to(CER[1], x.shape + (3,)).copy(), np.ones_like(x), None))
tile("tige", 0.3, 1.2, lambda x, y: (lerp(np.array((120, 150, 62), np.float32), np.array((88, 70, 40), np.float32), np.clip(y / 1.2, 0, 1)[..., None]), np.ones_like(x), None))


def choco_fn(x, y):
    u = x / 1.0
    k = np.abs(u - 0.5) * 2
    c = lerp(CHOCO[1], CHOCO[0], (k > 0.72)[..., None] * 0.9)
    c = lerp(c, CHOCO[2], ((k < 0.17) * (np.sin(y * 18) > -0.2))[..., None] * 1.0)    # couture claire (4 texels)
    return c, np.ones_like(x), None


tile("choco", 1.0, 1.0, choco_fn)


def boucle_fn(x, y):
    c = np.broadcast_to(CREME, x.shape + (3,)).copy()
    hole = (np.abs(x - 0.7) < 0.42) & (np.abs(y - 0.35) < 0.12)
    c = np.where(hole[..., None], CHOCO[0], c)
    edge = (x < 0.07) | (x > 1.33) | (y < 0.07) | (y > 0.63)
    c = np.where(edge[..., None], CREME_SH, c)
    return c, np.ones_like(x), None


tile("boucle", 1.4, 0.7, boucle_fn)


# ------------------------------------------------------------------ atlas
UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
items = sorted(TILES.items(), key=lambda it: -it[1][0].shape[0])
x0 = y0 = shelf = 0
tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
for n, (im, ie) in items:
    h, w = im.shape[:2]
    if x0 + w + 1 > TEX:
        x0, y0, shelf = 0, y0 + shelf + 1, 0
    assert y0 + h <= TEX - 6, "atlas plein"
    tex[y0:y0 + h, x0:x0 + w], tex_e[y0:y0 + h, x0:x0 + w] = im, ie
    UV[n] = (x0, y0, x0 + w, y0 + h)
    x0 += w + 1
    shelf = max(shelf, h)
assert tex[TEX - 3, TEX - 3, 3] == 0
assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
b64 = []
for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
    im = Image.fromarray(arr, "RGBA")
    im.save(fn, optimize=True)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    b64.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
tex_b64, tex_e_b64 = b64

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


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


def plate(g, name, c, X, Y, w, h, tname, th=0.3, flip=False):
    """Plaque fine : contour par l'alpha, tranches transparentes. u suit X, le haut de l'image est +Y, la face south regarde X x Y."""
    X, Y = unit(np.asarray(X, float)), unit(np.asarray(Y, float))
    u0, v0, u1, v1 = UV[tname]
    if flip:
        u0, u1 = u1, u0
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
         {"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def ell(a, b, phi):
    """Point (x, z) d'une ellipse centrée sur l'axe du cupcake et sa normale sortante (horizontale)."""
    p = V(a * math.cos(phi), 0, ZC + b * math.sin(phi))
    n = unit(V(math.cos(phi) / a, 0, math.sin(phi) / b))
    return p, n


def arc_params(a, b, n, start=0.0):
    """n angles répartis à longueur d'arc égale sur l'ellipse (a, b)."""
    ph = np.linspace(0, TAU, 4001)
    pts = np.stack([a * np.cos(ph), b * np.sin(ph)], 1)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    tg = (np.arange(n) + start) / n * s[-1]
    return [float(np.interp(t, s, ph)) for t in tg]


body = group("body", V(0, 24, 0))
SAC_PIVOT = V(0, YP + GH - 0.3, ZC - GB + 0.05)     # haut arrière du dôme : le bas du sac ne peut que s'écarter du dos
sac = group("sac", SAC_PIVOT, parent=body)

# Caissette : lamelles plissées alternées fraise / crème, plis rentrants sur les lamelles fraise
for k, phi in enumerate(arc_params((CB[0] + CT[0]) / 2, (CB[1] + CT[1]) / 2, NS, 0.5)):
    pb, nb = ell(*CB, phi)
    pt, nt = ell(*CT, phi)
    inset = -0.11 if k % 2 else 0.0
    pb, pt = pb + nb * inset + V(0, YB, 0), pt + nt * inset + V(0, YT, 0)
    Y = unit(pt - pb)
    n0 = unit(nb + nt)
    n = unit(n0 - (n0 @ Y) * Y)
    X = np.cross(Y, n)
    plate(sac, f"lamelle{k}", (pb + pt) / 2, X, Y, SW_, SH_, "slat_fraise" if k % 2 else "slat_creme", th=0.3)

# Fond de la caissette : deux pavés en croix, inscrits dans l'ellipse du bas
uP = UV["paper"]
FOND = (CB[0] - 0.2, CB[1] - 0.2)

# Glaçage
gl = group("glacage", V(0, YP, ZC), parent=sac)

# Anneau de gouttes : plaques tangentes, du bourrelet (haut, contre le dôme) jusqu'aux gouttes sur la caissette
for k, phi in enumerate(arc_params(*DT, ND, 0.0)):
    pt, nt = ell(*DT, phi)
    cb_y = YP - DH
    tcb = (cb_y - YB) / (YT - YB)
    cbot = (lerp(CB[0], CT[0], tcb), lerp(CB[1], CT[1], tcb))
    pb, nb = ell(*cbot, phi)
    off = 0.06 if k % 2 else 0.0
    pt = pt + nt * off + V(0, YP, 0)
    pb = pb + nb * (0.5 + off) + V(0, cb_y, 0)
    Y = unit(pt - pb)
    n = unit(nt - (nt @ Y) * Y)
    X = np.cross(Y, n)
    L_ = np.linalg.norm(pt - pb)
    plate(gl, f"goutte{k}", (pt + pb) / 2, X, Y, DW, L_, f"drip{(k * 2) % 3}", th=0.3, flip=bool(k % 3 == 1))

# Dôme : gradins octogonaux (deux pavés en croix + quatre pavés de coin le long des cordes), dessus en projection planaire
ut0, vt0, ut1, vt1 = UV["gl_top"]
us0, vs0, us1, vs1 = UV["gl_side"]
ug = UV["gl_under"]


def top_uv(x0_, z0_, x1_, z1_):
    fu = lambda x: lerp(ut0, ut1, np.clip((x + GA) / (2 * GA), 0, 1))
    fv = lambda z: lerp(vt0, vt1, np.clip((z - ZC + GB) / (2 * GB), 0, 1))
    return [fu(x0_), fv(z0_), fu(x1_), fv(z1_)]


def side_uv(ya, yb):
    fv = lambda y: lerp(vs0, vs1, np.clip((YP + GH - y) / GH, 0, 1))
    return [us0, fv(yb), us1, fv(ya)]


# gradins répartis à longueur d'arc à peu près égale sur le profil (GA cos psi, YP + GH sin psi)
NT = 12
_yy = np.linspace(YP, YP + GH, 2001)
_pts = np.stack([GA * prof(_yy), _yy], 1)
_sl = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(_pts, axis=0), axis=1))])
YS = [float(np.interp(k / NT * _sl[-1], _sl, _yy)) for k in range(NT + 1)]
TIERS = []
for i in range(NT):
    ya, yb = YS[i], YS[i + 1]
    s = 1.0 if i == 0 else float(prof(ya + 0.45 * (yb - ya)))
    TIERS.append((ya, yb, max(s, 0.3)))
C1, S1 = math.cos(math.radians(22.5)), math.sin(math.radians(22.5))


def octo(g, prefix, ya, yb, a, b, sides, up_fn, down=None, corners=True):
    """Couche octogonale inscrite dans l'ellipse (a, b) : deux pavés en croix + quatre pavés de coin le long des cordes.
    Dessus décalés de 0,02 px pour ne jamais être coplanaires."""
    j = 0

    def box(name, x0_, z0_, x1_, z1_, rot=None, c=None, fp=None):
        nonlocal j
        top = yb - 0.02 * j
        faces = {"north": sides, "south": sides, "east": sides, "west": sides, "up": up_fn(*(fp or (x0_, z0_, x1_, z1_)))}
        if down is not None:
            faces["down"] = list(down)
        cube(g, name, V(x0_, ya + 0.01 * j * (down is not None), z0_), V(x1_, top, z1_), V(0, ya, ZC) if rot is None else c, rot or (0, 0, 0), faces)
        j += 1

    box(f"{prefix}_l", -a * C1, ZC - b * S1, a * C1, ZC + b * S1)
    box(f"{prefix}_p", -a * S1, ZC - b * C1, a * S1, ZC + b * C1)
    if not corners:
        return
    for qx in (-1, 1):
        for qz in (-1, 1):
            P1, P2 = V(qx * a * C1, 0, ZC + qz * b * S1), V(qx * a * S1, 0, ZC + qz * b * C1)
            t = unit(P2 - P1)
            n = V(-t[2], 0, t[0])
            if n @ (P1 + P2 - 2 * V(0, 0, ZC)) < 0:
                n = -n
            L_, d_ = np.linalg.norm(P2 - P1) + 0.1, min(0.9, b * 0.5)
            c = (P1 + P2) / 2 - n * (d_ / 2)
            R_ = np.column_stack([np.cross(V(0, 1, 0), n), V(0, 1, 0), n])
            ctr = V(c[0], ya, c[2])
            box(f"{prefix}_c{'d' if qx > 0 else 'g'}{'a' if qz > 0 else 'v'}", ctr[0] - L_ / 2, ctr[2] - d_ / 2, ctr[0] + L_ / 2, ctr[2] + d_ / 2,
                rot=euler(R_), c=ctr, fp=(c[0] - 0.6, c[2] - 0.6, c[0] + 0.6, c[2] + 0.6))


for i, (ya, yb, s) in enumerate(TIERS):
    octo(gl, f"dome{i}", ya, yb, GA * s, GB * s, side_uv(ya, yb), top_uv, down=ug if i == 0 else None, corners=s >= 0.42)

# Fond de la caissette : même octogone, en papier
octo(sac, "fond", YB + 0.12, YB + 0.5, *FOND, list(uP), lambda *a: list(uP), down=uP)

# Cerise : âme + trois disques verticaux à 60° + un disque horizontal ; queue dans son propre groupe
YTOP = YP + GH
cer = group("cerise", V(0, YTOP - 0.05, ZC), parent=gl)
cc = V(0, CY, ZC)
uc = UV["cerise_coeur"]
h_ = CR * 0.5
cube(cer, "cerise_ame", cc - h_, cc + h_, cc, (0, 0, 0), {f: list(uc) for f in ("north", "south", "east", "west", "up", "down")})
for k in range(3):
    a = math.radians(15 + 60 * k)
    plate(cer, f"cerise_disque{k}", cc, V(math.cos(a), 0, -math.sin(a)), V(0, 1, 0), CD, CD, "cerise", th=0.24)
plate(cer, "cerise_disque_h", cc, V(1, 0, 0), V(0, 0, -1), CD, CD, "cerise", th=0.24)
tig = group("tige", cc + V(0, CR - 0.1, 0), parent=cer)
ut = UV["tige"]
p0 = cc + V(0, CR - 0.25, 0)
mid_ = p0 + V(0.12, 0.7, 0.12)
end_ = mid_ + V(0.38, 0.55, 0.34)
for k, (pa, pb) in enumerate(((p0, mid_), (mid_, end_))):
    Yd = unit(pb - pa)
    Xd = unit(np.cross(Yd, V(0, 0, 1)))
    R_ = np.column_stack([Xd, Yd, np.cross(Xd, Yd)])
    L_ = np.linalg.norm(pb - pa) + 0.12
    ctr = (pa + pb) / 2
    cube(tig, f"tige{k}", ctr - V(0.13, L_ / 2, 0.13), ctr + V(0.13 - 0.01 * k, L_ / 2, 0.13 - 0.01 * k), ctr, euler(R_), {f: list(ut) for f in ("north", "south", "east", "west", "up", "down")})

# Bretelles chocolat (portées par le torse, pas par le sac)
uch, ub = UV["choco"], UV["boucle"]
SX, BW_, BT = 2.3, 1.0, 0.34
for s, tag in ((1, "d"), (-1, "g")):
    x0_, x1_ = s * SX - BW_ / 2, s * SX + BW_ / 2
    f6 = {f: list(uch) for f in ("north", "south", "east", "west", "up", "down")}
    cube(body, f"bretelle_av_{tag}", V(x0_, 15.2, -2.06 - BT), V(x1_, 24.36, -2.06), V(0, 24, 0), (0, 0, 0), f6)
    cube(body, f"bretelle_pont_{tag}", V(x0_ + 0.02, 24.0, -2.36), V(x1_ - 0.02, 24.32, 2.36), V(0, 24, 0), (0, 0, 0), f6)
    cube(body, f"bretelle_dos_{tag}", V(x0_, 16.4, 2.06), V(x1_, 24.36, 2.06 + BT), V(0, 24, 0), (0, 0, 0), f6)
    fb = {f: list(ub) for f in ("north", "south")}
    fb.update({f: [ub[0], ub[1], ub[0] + 3, ub[1] + 3] for f in ("east", "west", "up", "down")})
    cube(body, f"boucle_{tag}", V(s * SX - 0.7, 17.3, -2.58), V(s * SX + 0.7, 18.0, -2.1), V(0, 24, 0), (0, 0, 0), fb)


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node("body")]

# ------------------------------------------------------------------ animations
# Convention (guide, section 3) : rotation +X = le haut du groupe part vers l'arrière (+Z), donc ce qui est au-dessus du pivot recule.
# Le pivot du sac est en haut contre le dos : sac_rot(out) avec out >= 0 écarte le bas du sac du dos (rotation X négative).
# Cerise (pivot à sa base) : lean_back > 0 penche la cerise vers l'arrière (+Z), lean_side > 0 vers la droite du joueur (+X)
# (+Z monte le côté droit : le haut part vers la gauche, d'où le signe -).
def sac_rot(out, side=0.0):
    return (-abs(out), 0.0, side)


def cer_rot(lean_back, lean_side):
    return (lean_back, 0.0, -lean_side)


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def ring(t, t0, f, dec):
    """Oscillation amortie qui démarre à t0 (sin : vaut 0 au départ), pour les sursauts de la cerise."""
    if t < t0:
        return 0.0
    u = t - t0
    return math.sin(TAU * f * u) * math.exp(-dec * u)


def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 3)), "y": str(round(v[1] + 0.0, 3)), "z": str(round(v[2] + 0.0, 3))}],
            "time": round(t, 3), "interpolation": "linear"}


def anim(name, length, tracks, fps=10, loop="loop"):
    """tracks : groupe -> f(t) qui rend {canal: (x, y, z)}. Boucle : dernier keyframe identique au premier (linear)."""
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A = {}
    for g, f in tracks.items():
        kfs = []
        for t in times:
            tt = 0.0 if (loop == "loop" and i_close(t, length)) else t
            for ch, v in f(tt).items():
                kfs.append(kf(ch, t, v))
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


def i_close(t, L):
    return abs(t - L) < 1e-9


def S(t, L, k=1, ph=0.0):
    return math.sin(TAU * (k * t / L - ph))


def state(name, L, sac_f, gl_f, cer_f, tig_f, fps=10):
    tr = {"sac": lambda t: dict(zip(("rotation", "position"), sac_f(t))),
          "glacage": lambda t: {"scale": gl_f(t)},
          "cerise": lambda t: {"rotation": cer_rot(*cer_f(t))},
          "tige": lambda t: {"rotation": cer_rot(*tig_f(t))}}
    return anim(name, L, tr, fps=fps)


def squash(k):
    """Gélatine à volume à peu près constant : k > 0 écrase, k < 0 étire."""
    return (1 + 0.5 * k, 1 - k, 1 + 0.5 * k)


# idle 8 s : respiration très légère (période 4 s) + un petit « boing » de la cerise vers 5 s
L = 8.0
idle = state("idle", L,
             lambda t: (sac_rot(0.5 + 0.4 * (1 + S(t, L, 2)) / 2), (0, 0.06 * S(t, L, 2, 0.1), 0)),
             lambda t: squash(0.012 * S(t, L, 2, 0.15) + 0.05 * ring(t, 4.9, 2.0, 2.6)),
             lambda t: (1.2 * S(t, L, 2, 0.2) + 7 * ring(t, 5.0, 1.6, 2.2), 1.5 * S(t, L, 1, 0.3)),
             lambda t: (2.0 * S(t, L, 2, 0.3) + 10 * ring(t, 5.1, 1.6, 2.0), 2.0 * S(t, L, 1, 0.45)), fps=8)

# walk 1,6 s : deux pas par cycle -> deux rebonds ; la cerise ballotte de côté une fois par cycle, avec retard
L = 1.6
walk = state("walk", L,
             lambda t: (sac_rot(1.4 + 1.2 * (1 + S(t, L, 2)) / 2, 1.2 * S(t, L, 1)), (0, 0.16 * S(t, L, 2, 0.05), 0.05 * (1 + S(t, L, 2)))),
             lambda t: squash(0.03 * S(t, L, 2, 0.12)),
             lambda t: (4 + 4 * S(t, L, 2, 0.15), 7 * S(t, L, 1, 0.12)),
             lambda t: (5 * S(t, L, 2, 0.28), 9 * S(t, L, 1, 0.25)))

# run 1,0 s : rebond net, sac qui décolle un peu du dos, cerise couchée vers l'arrière qui fouette
L = 1.0
run = state("run", L,
            lambda t: (sac_rot(4.0 + 3.0 * (1 + S(t, L, 2)) / 2, 2.0 * S(t, L, 1)), (0, 0.32 * S(t, L, 2, 0.05), 0.12 * (1 + S(t, L, 2)))),
            lambda t: squash(0.06 * S(t, L, 2, 0.12)),
            lambda t: (12 + 7 * S(t, L, 2, 0.17), 11 * S(t, L, 1, 0.14)),
            lambda t: (8 + 8 * S(t, L, 2, 0.3), 14 * S(t, L, 1, 0.28)))

# sneak 3 s : torse penché, sac posé, cerise qui penche doucement
L = 3.0
sneak = state("sneak", L,
              lambda t: (sac_rot(2.5 + 0.8 * (1 + S(t, L, 1)) / 2), (0, -0.05 + 0.04 * S(t, L, 1), 0)),
              lambda t: squash(0.02 + 0.01 * S(t, L, 1, 0.1)),
              lambda t: (-6 + 2 * S(t, L, 1, 0.15), 3 * S(t, L, 1, 0.4)),
              lambda t: (-5 + 3 * S(t, L, 1, 0.3), 4 * S(t, L, 1, 0.55)))

# fly 2,4 s : sac qui flotte, cerise penchée vers l'arrière (traînée) qui oscille lentement
L = 2.4
fly = state("fly", L,
            lambda t: (sac_rot(3.0 + 2.0 * (1 + S(t, L, 1)) / 2, 1.5 * S(t, L, 1, 0.25)), (0, 0.15 * S(t, L, 1), 0.1 * (1 + S(t, L, 1)))),
            lambda t: squash(-0.025 * S(t, L, 1, 0.12)),
            lambda t: (10 + 4 * S(t, L, 2, 0.15), 5 * S(t, L, 1, 0.2)),
            lambda t: (8 + 6 * S(t, L, 2, 0.3), 7 * S(t, L, 1, 0.35)))

# glide 3,6 s : corps couché, la cerise pointe dans le vent : elle se couche vers l arrière du sac (rotation +X) et frémit
L = 3.6
glide = state("glide", L,
              lambda t: (sac_rot(1.5 + 1.0 * (1 + S(t, L, 2)) / 2), (0, 0, 0.05 * (1 + S(t, L, 2)))),
              lambda t: squash(0.02 * S(t, L, 4, 0.1)),
              lambda t: (18 + 3 * S(t, L, 12) + 2 * S(t, L, 2, 0.2), 3 * S(t, L, 2, 0.3)),
              lambda t: (12 + 5 * S(t, L, 12, 0.2), 4 * S(t, L, 2, 0.45)))

# fall 1,2 s : le sac se soulève et s'écarte, la cerise est tirée vers le haut (étirement) et vibre
L = 1.2
fall = state("fall", L,
             lambda t: (sac_rot(4.0 + 1.5 * (1 + S(t, L, 1)) / 2), (0, 0.22 + 0.06 * S(t, L, 2), 0.1)),
             lambda t: squash(-0.04 + 0.015 * S(t, L, 2, 0.1)),
             lambda t: (3 * S(t, L, 2, 0.1), 5 * S(t, L, 1, 0.2)),
             lambda t: (5 * S(t, L, 2, 0.25), 7 * S(t, L, 1, 0.35)))

# sleep 4 s : respiration très lente, cerise endormie penchée de côté
L = 4.0
sleep = state("sleep", L,
              lambda t: (sac_rot(0.4 + 0.3 * (1 + S(t, L, 1)) / 2), (0, 0.04 * S(t, L, 1), 0)),
              lambda t: squash(0.015 * S(t, L, 1, 0.1)),
              lambda t: (2 * S(t, L, 1, 0.2), 14 + 2 * S(t, L, 1, 0.25)),
              lambda t: (2 * S(t, L, 1, 0.35), 10 + 2 * S(t, L, 1, 0.4)), fps=8)

# hurt 0,8 s (once) : le sac sursaute, la gelée s'écrase, la cerise tremble puis revient à 0
L = 0.8
hu = lambda t: bump(t, 0.0, 0.07, 0.15, 0.65)
fade = lambda t: 1 - sm(t, 0.55, 0.8)
hurt = anim("hurt", L, {
    "sac": lambda t: {"rotation": sac_rot(7 * hu(t)), "position": (0, 0.35 * hu(t), 0.2 * hu(t))},
    "glacage": lambda t: {"scale": squash(0.09 * ring(t, 0.04, 3.0, 4.5) * fade(t))},
    "cerise": lambda t: {"rotation": cer_rot(-14 * ring(t, 0.02, 2.6, 4.0) * fade(t), 9 * ring(t, 0.06, 2.1, 4.0) * fade(t))},
    "tige": lambda t: {"rotation": cer_rot(-18 * ring(t, 0.08, 2.6, 4.0) * fade(t), 12 * ring(t, 0.1, 2.1, 4.0) * fade(t))},
}, fps=20, loop="once")

ANIMS = [idle, walk, run, sneak, fly, glide, fall, sleep, hurt]

assert 60 <= len(elements) <= 160, f"budget : {len(elements)} cubes"
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
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
