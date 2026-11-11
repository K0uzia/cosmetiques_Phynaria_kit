"""Sac cupcake : petit sac à dos en forme de cupcake fraise, porté dans le dos. Ensemble « Pâtisserie ». Design original.
Écrit sac_patisserie.png, sac_patisserie_e.png et .build/sac_patisserie_brut.bbmodel à côté de ce script.

- Caissette : anneau de 16 lamelles plissées (peau découpée, rayures fraise / crème), évasée vers le haut, fond plein.
- Glaçage : dôme en 6 bandes coniques de 16 plaques fines en trapèze (découpées par alpha, peintes depuis la position 3D de
  leurs texels), chapeau plat, dessous sombre ; bordé d'un anneau de plaques découpées dont le bas coule en gouttes arrondies
  sur la caissette. Vermicelles peints en projection planaire, continus d'une plaque à l'autre.
- Cerise : trois disques verticaux croisés + un disque horizontal (peau ronde) autour d'une âme pleine, queue articulée.
- Bretelles chocolat : devant (z = -2,2), pont sur l'épaule caché sous la tête, dos entre le joueur et le sac.
Groupe de premier niveau `body`. Le dos du joueur est à z = +2 : rien du sac ne descend sous z = 2,15.

Remise aux règles du 2026-11-05 (`.claude/references/procedures/remise-aux-regles.md`, fiche `.claude/styles/patisserie.md`) :
- dôme refait (les gradins en pavés croisés donnaient 188 paires de faces parallèles à moins de 0,1 px) ; fond de caissette en
  une plaque elliptique ; pont et boucles des bretelles écartés : 0 paire, pose de base et poses principales (`.build/mesure_faces.py`) ;
- `event_equip` (1,1 s) : le sac sort du dos en « plop » (0 -> 1,25 -> 0,9 -> 1), le glaçage descend et coule, la cerise tombe,
  s'enfonce et rebondit, un son à l'impact (`block.honey_block.place`) ; `event_unequip` (0,7 s) : la cerise saute, le sac
  s'écrase puis rentre dans le dos (échelle 0 gardée). Groupe `apparition` réservé à ces deux événements ;
- sons limités par `tools/sons.py` ; calque `_e` : fond très léger (≤ 18, contre le saumon de nuit) et une seule source nette,
  le reflet de la cerise (≤ 225). Pas d'`add_`, de `cam_`, de `trans_` (glaçage opaque : crème au beurre) ni de rotation continue.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # calque _e embarqué en seconde texture (correctif du clignotement annoncé le 2026-11-03, à vérifier en jeu)
NOM = "sac_patisserie"
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
        e = lerp(e, np.array((225, 196, 204), np.float32), np.clip(g * 1.6, 0, 1))     # source nette : reflet de la cerise (≤ 225)
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




def gside_fn(x, y):
    # y : 0 = haut du dôme (YP + GH), GH = base. Côtés des gradins : plus sombres en bas, comme la normale du dôme
    c = gcol(prof(YP + GH - y)) * 0.96
    return c, np.ones_like(x), None




def paper_fn(x, y):
    c = lerp(CREME_SH, CREME, (0.6 + 0.4 * np.sin(x * 9.0))[..., None] * 0.8)
    return c, np.ones_like(x), None




# Dôme (remise aux règles du 2026-11-05) : bandes coniques de plaques fines en trapèze, découpées par alpha, qui suivent le profil
# (les anciens gradins en pavés croisés donnaient 188 paires de faces parallèles à moins de 0,1 px). Chaque plaque est peinte
# depuis la position 3D de ses texels : même dégradé radial et mêmes vermicelles qu'avant, continus d'une plaque à l'autre.
NB, NPL = 6, 16                     # bandes, plaques par bande
S_CAP = 0.30                        # rayon relatif du chapeau plat au sommet
LUM = unit(V(-0.35, 0.85, 0.40))    # lumière peinte : en haut, un peu côté dos (le sac se voit surtout de dos)


def _phis(a, b, n):
    ph = np.linspace(0, TAU, 4001)
    pts = np.stack([a * np.cos(ph), b * np.sin(ph)], 1)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    return [float(np.interp(k / n * s[-1], s, ph)) for k in range(n)] + [TAU]


_yy = np.linspace(YP, YP + GH, 4001)
_ss = prof(_yy)
_ycap = float(np.interp(-S_CAP, -_ss, _yy))
_m = _yy <= _ycap
_pts = np.stack([GA * _ss[_m], _yy[_m]], 1)
_sl = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(_pts, axis=0), axis=1))])
DYS = [float(np.interp(k / NB * _sl[-1], _sl, _yy[_m])) for k in range(NB + 1)]
DSS = [1.0] + [float(prof(y)) for y in DYS[1:-1]] + [S_CAP]
# angles des plaques : normales à pas constant (et non longueur d'arc constante) : à l'arrière et à l'avant de l'ellipse, deux
# plaques voisines gardent un angle franc entre elles (sinon presque parallèles, à moins de 0,1 px l'une de l'autre)
PHI = [math.atan2(GB * math.sin(p_), GA * math.cos(p_)) % TAU for p_ in np.arange(NPL) * TAU / NPL] + [TAU]


def dpt(s, y, ph):
    return V(GA * s * math.cos(ph), y, ZC + GB * s * math.sin(ph))


DOME = []           # (nom de tuile, centre, X, Y, w, h)
for i in range(NB):
    for k in range(NPL):
        B1, B0 = dpt(DSS[i], DYS[i], PHI[k]), dpt(DSS[i], DYS[i], PHI[k + 1])          # sens choisi pour que la face south regarde dehors
        T1, T0 = dpt(DSS[i + 1], DYS[i + 1], PHI[k]), dpt(DSS[i + 1], DYS[i + 1], PHI[k + 1])
        X = unit(B1 - B0)
        Bm, Tm = (B0 + B1) / 2, (T0 + T1) / 2
        d = Tm - Bm
        du = float(d @ X)
        Yv = d - du * X
        h = float(np.linalg.norm(Yv))
        Yu = Yv / h
        n = np.cross(X, Yu)
        if n @ (Bm - V(0, Bm[1], ZC)) < 0:
            raise SystemExit("plaque du dôme retournée")
        wb, wt = float(np.linalg.norm(B1 - B0)), float(np.linalg.norm(T1 - T0))
        mb = 0.36 if i == 0 else 0.05           # la bande du bas descend sous le bourrelet (ferme la vue de dessous)
        mt = 0.05
        ov = 0.05                               # recouvrement latéral : aucun jour entre deux plaques
        umin = min(-wb / 2, du - wt / 2) - ov
        umax = max(wb / 2, du + wt / 2) + ov
        w_, h_ = umax - umin, h + mb + mt
        name = f"dome{i}_{k}"

        def fn(x, y, umin=umin, h=h, mb=mb, wb=wb, wt=wt, du=du, Bm=Bm, X=X, Yu=Yu, n=n, ov=ov):
            u = x + umin
            v = (h + 0.05) - y                  # haut de l'image = bord haut (+ marge)
            q = np.clip(v / h, 0, 1)
            half = lerp(wb / 2, wt / 2, q) + ov
            ctr = du * q
            cov = (np.abs(u - ctr) <= half) & (v >= -mb) & (v <= h + 0.05)
            P = Bm[None, None, :] + u[..., None] * X + v[..., None] * Yu
            Xp, Zp = P[..., 0], P[..., 2] - ZC
            rho = np.clip(np.hypot(Xp / GA, Zp / GB), 0, 1)
            c = gcol(rho)
            for sx, sz, a, col in SPRINKLES:
                L, r = 0.26, 0.085
                dx, dz = math.cos(a), math.sin(a)
                t = np.clip((Xp - sx) * dx + (Zp - sz) * dz, -L, L)
                dd = np.hypot(Xp - sx - t * dx, Zp - sz - t * dz)
                c = np.where((dd < r)[..., None], np.array(col, np.float32), c)
                c = np.where(((dd < r * 0.45) & (t < -L * 0.2))[..., None], np.minimum(np.array(col, np.float32) + 60, 255), c)
            c = c * (0.94 + 0.07 * float(n @ LUM))
            c = lerp(c, GL_DEEP, (np.clip((DYS[0] - P[..., 1]) / 0.3, 0, 1) * 0.6)[..., None])   # dessous du bourrelet
            return c, cov.astype(np.float32), None
        tile(name, w_, h_, fn)
        c3 = Bm + X * ((umin + umax) / 2) + Yu * ((h + mt - mb) / 2) - n * 0.15
        DOME.append((name, c3, X, Yu, w_, h_))


def cap_fn(x, y):
    a, b = GA * S_CAP + 0.06, GB * S_CAP + 0.06
    X, Z = x - a, y - b
    cov = np.hypot(X / a, Z / b) < 1
    c = gcol(np.clip(np.hypot(X / GA, Z / GB), 0, 1))
    return c, cov.astype(np.float32), None


tile("dome_cap", 2 * (GA * S_CAP + 0.06), 2 * (GB * S_CAP + 0.06), cap_fn)
FA, FB = CB[0] - 0.12, CB[1] - 0.12


def fond_fn(x, y):
    X, Z = x - FA, y - FB
    c = lerp(CREME_SH, CREME, (0.6 + 0.4 * np.sin(np.arctan2(Z / FB, X / FA) * 16))[..., None] * 0.8)
    return c, (np.hypot(X / FA, Z / FB) < 1).astype(np.float32), None


tile("fond", 2 * FA, 2 * FB, fond_fn)


def under_fn(x, y):
    a, b = GA + 0.02, GB + 0.02
    X, Z = x - a, y - b
    c = np.broadcast_to(GL_DEEP * 0.92, x.shape + (3,)).copy()
    return c, (np.hypot(X / a, Z / b) < 1).astype(np.float32), None


tile("dome_dessous", 2 * (GA + 0.02), 2 * (GB + 0.02), under_fn)



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
APP_PIVOT = V(0, 15.6, ZC - CB[1])                  # bas du sac contre le dos : il « sort » du dos en pop
app = group("apparition", APP_PIVOT, parent=body)    # porté seulement par event_equip / event_unequip (échelle)
sac = group("sac", SAC_PIVOT, parent=app)

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

# Dôme : bandes coniques de plaques (voir la peinture plus haut), chapeau plat, dessous sombre qui ferme le bourrelet
for name, c3, X, Yu, w_, h_ in DOME:
    plate(gl, name, c3, X, Yu, w_, h_, name, th=0.3)
uc_ = UV["dome_cap"]
cube(gl, "dome_chapeau", V(-(GA * S_CAP + 0.06), DYS[-1] - 0.3, ZC - (GB * S_CAP + 0.06)), V(GA * S_CAP + 0.06, DYS[-1], ZC + GB * S_CAP + 0.06),
     V(0, DYS[-1], ZC), (0, 0, 0), {"up": [uc_[0], uc_[1], uc_[2], uc_[3]], "down": CLEAR, "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR})
ud_ = UV["dome_dessous"]
cube(gl, "dome_dessous", V(-(GA + 0.02), YP - 0.36, ZC - (GB + 0.02)), V(GA + 0.02, YP - 0.06, ZC + GB + 0.02), V(0, YP, ZC), (0, 0, 0),
     {"down": [ud_[0], ud_[3], ud_[2], ud_[1]], "up": CLEAR, "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR})
# Fond de la caissette : une seule plaque elliptique en papier
uf_ = UV["fond"]
cube(sac, "fond", V(-FA, YB + 0.12, ZC - FB), V(FA, YB + 0.42, ZC + FB), V(0, YB, ZC), (0, 0, 0),
     {"down": [uf_[0], uf_[3], uf_[2], uf_[1]], "up": CLEAR, "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR})



# Cerise : âme + trois disques verticaux à 60° + un disque horizontal ; queue dans son propre groupe
YTOP = DYS[-1]                              # sommet du dôme (chapeau plat)
cer = group("cerise", V(0, YTOP - 0.05, ZC), parent=gl)
cc = V(0, YTOP + CR - 0.12, ZC)
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
    cube(body, f"bretelle_pont_{tag}", V(x0_ + 0.12, 24.05, -2.25), V(x1_ - 0.12, 24.25, 2.25), V(0, 24, 0), (0, 0, 0), f6)
    cube(body, f"bretelle_dos_{tag}", V(x0_, 16.4, 2.06), V(x1_, 24.36, 2.06 + BT), V(0, 24, 0), (0, 0, 0), f6)
    fb = {f: list(ub) for f in ("north", "south")}
    fb.update({f: [ub[0], ub[1], ub[0] + 3, ub[1] + 3] for f in ("east", "west", "up", "down")})
    cube(body, f"boucle_{tag}", V(s * SX - 0.7, 17.3, -2.58), V(s * SX + 0.7, 18.0, -2.22), V(0, 24, 0), (0, 0, 0), fb)


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

# event_equip 1,1 s : « plop » gourmand. Le sac sort du dos en s'écrasant puis rebondit (0 -> 1,25 -> 0,9 -> 1), le glaçage
# descend et coule (échelle y depuis sa base), puis la cerise tombe d'en haut, s'enfonce, rebondit deux fois, la queue ballotte.
def keys(t, ts, vs):
    return float(np.interp(t, ts, vs))


def eq_app(t):
    s_ = keys(t, [0, 0.2, 0.34, 0.46, 0.6], [0.0, 1.25, 0.9, 1.05, 1.0])
    q = keys(t, [0, 0.2, 0.34, 0.46, 0.6], [0.0, -0.10, 0.12, -0.04, 0.0])     # étiré en montant, écrasé au rebond
    return {"scale": (s_ * (1 + 0.5 * q), s_ * (1 - q), s_ * (1 + 0.5 * q))}


T_IMP = 0.72


def eq_gl(t):
    sy = keys(t, [0, 0.12, 0.42, 0.56, T_IMP, T_IMP + 0.06, T_IMP + 0.18, 1.1], [0.35, 0.35, 1.12, 1.0, 1.0, 0.9, 1.02, 1.0])
    k = 1 - sy
    return {"scale": (1 + 0.5 * k, sy, 1 + 0.5 * k)}


def eq_cer(t):
    if t < 0.45:
        return {"scale": (0, 0, 0), "position": (0, 6.0, 0)}
    if t < T_IMP:
        u = (t - 0.45) / (T_IMP - 0.45)
        return {"scale": (1, 1, 1), "position": (0, 6.0 * (1 - u * u), 0)}
    u = t - T_IMP
    hop = 0.7 * max(0.0, math.sin(math.pi * u / 0.16)) if u < 0.16 else (0.18 * max(0.0, math.sin(math.pi * (u - 0.16) / 0.1)) if u < 0.26 else 0.0)
    sq = keys(u, [0, 0.04, 0.1, 0.2], [0.0, 0.18, -0.06, 0.0])
    return {"scale": (1 + 0.5 * sq, 1 - sq, 1 + 0.5 * sq), "position": (0, hop, 0)}


def eq_tig(t):
    return {"rotation": cer_rot(-16 * ring(t, T_IMP, 2.6, 4.5), 10 * ring(t, T_IMP + 0.03, 2.1, 4.5))}


equip = anim("event_equip", 1.1, {"apparition": eq_app, "glacage": eq_gl, "cerise": eq_cer, "tige": eq_tig}, fps=30, loop="once")
equip["animators"]["effects"] = {"name": "Effects", "type": "effect",
                                 "keyframes": [{"channel": "sound", "data_points": [{"effect": "block.honey_block.place", "file": ""}], "time": T_IMP}]}


# event_unequip 0,7 s : la cerise saute et disparaît, le sac s'écrase puis rentre dans le dos (échelle 0, gardée jusqu'au départ)
def un_app(t):
    s_ = keys(t, [0, 0.12, 0.22, 0.55, 0.7], [1.0, 1.0, 1.08, 0.0, 0.0])
    q = keys(t, [0, 0.12, 0.22, 0.55], [0.0, 0.12, -0.08, 0.0])
    return {"scale": (s_ * (1 + 0.5 * q), s_ * (1 - q), s_ * (1 + 0.5 * q))}


def un_cer(t):
    s_ = keys(t, [0, 0.1, 0.3, 0.7], [1.0, 1.1, 0.0, 0.0])
    return {"scale": (s_, s_, s_), "position": (0, keys(t, [0, 0.08, 0.28, 0.7], [0.0, -0.2, 1.6, 1.6]), 0)}


unequip = anim("event_unequip", 0.7, {"apparition": un_app, "cerise": un_cer}, fps=30, loop="once")

ANIMS = [idle, walk, run, sneak, fly, glide, fall, sleep, hurt, equip, unequip]

assert 60 <= len(elements) <= 160, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
