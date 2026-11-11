"""Lame de givre : épée longue de cristal tenue dans la main droite, ensemble Givre (thème Éléments). Design original.
Écrit lame_givre.png, lame_givre_e.png et .build/lame_givre_brut.bbmodel à côté de ce script.

Lame de cristal taillée : section en losange (arête centrale sur chaque face, tranchants en haut et en bas), quatre vraies
facettes planes sur la longueur, puis quatre facettes triangulaires pour la pointe en biseau (pointe décalée vers le haut).
Chaque facette est une plaque fine `trans_` (alpha 150–222) dont seule la face extérieure est peinte, découpée exactement à son
contour : glace bleutée, bande d'arête et biseau du tranchant plus clairs, chevrons de taille, fissures blanches fines, givre en
dentelle au talon. Dedans, une âme opaque fine en losange (cœur cyan lumineux au calque _e) le long de l'arête centrale.
Garde d'argent froid : moyeu octogonal, flocon à six branches sur chaque flanc, trois cristaux d'argent pointus de chaque côté
(en haut, en bas) qui s'écartent en éventail. Fusée gainée de cuir bleu nuit, viroles d'argent, pommeau = petit prisme de glace.

Repère : la lame vise -Z (devant le joueur), a = distance vers l'avant depuis la prise P0, w = hauteur, t = vers l'extérieur (+X).
`prise` porte la pose d'état, `coup` l'attaque et la blessure (jouées par-dessus : rotations ajoutées à l'état sans conflit).

Fonctions spéciales (guide 4 bis, 5 ter, 6.4, 6.5) :
- `trans_lame` : peau de cristal semi-transparente (marche avec shader, vu en jeu sur d'autres pièces) ;
- `cam_scintille1..4` : petites étoiles face caméra sur les tranchants, la pointe et le flocon, qui scintillent dans
  `overlay_scintille` (échelle quasi nulle le reste du temps) ;
- `ctrl_lumiere` dans le cœur : légère pulsation (overlay) et flash à l'attaque (non simulé par le renderer, à voir en jeu) ;
- `eclats` : nova de six éclats de glace autour de la garde à l'attaque, construite 8 fois plus petite et cachée dans le
  moyeu au repos, agrandie par l'animation (échelles multipliées : l'état ne la touche jamais) ;
- `event_equip` (1,2 s) : les cristaux de la garde poussent en cascade, les flocons tournent, puis la lame pousse depuis la garde ;
- particules modélisées : `particle_eclat` (éclats de givre, rafale à l'attaque, points le long des tranchants) et
  `particle_brume` (brume froide translucide au repos, sous la lame) ; rien qui tombe et se pose (réglages : « Disparaît ») ;
- sons (tools/sons.py) : `block.amethyst_block.hit` à l'attaque, `block.amethyst_block.chime` à l'apparition.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True
NOM = "lame_givre"
TEX = 512
TAU = 2 * math.pi
KE = 3.0            # réduction de la nova d'éclats au repos (assez pour la cacher dans le moyeu, faces encore à 0,11 px)
KG = 16.0           # réduction des étoiles de scintillement au repos
# Géométrie de base agrandie par étoile, clés d'échelle divisées d'autant (même taille à l'écran) :
# l'étoile de la pointe monte à 1,3 KG dans event_equip, au-delà du plafond de 16 fois du guide (3, 7).
# Seul écart : hors scintillement, le point résiduel de l'étoile 3 fait 0,12 px au lieu de 0,09 (invisible).
GF = (1.0, 1.0, 1.35, 1.0)

P0 = np.array((6.0, 11.3, -0.6))     # prise : sous le poing (bras x 4..8, bas du bras y = 12)
A_ = np.array((0.0, 0.0, -1.0))      # le long de la lame (devant)
W_ = np.array((0.0, 1.0, 0.0))       # hauteur
T_ = np.array((1.0, 0.0, 0.0))       # vers l'extérieur

# Lame
A_BASE, A_SH, A_TIP = 2.55, 16.6, 20.4
HW0, HW1 = 1.25, 0.80               # demi-largeur au talon et au début de la pointe
KT = 0.40                           # demi-épaisseur = KT × demi-largeur (section en losange)
TIP_W = 0.25                        # décalage de la pointe vers le haut : biseau
HUB_A, HUB_R, HUB_T = 2.45, 0.85, 0.75
FL_T = HUB_T + 0.3                 # plan du flocon (face extérieure à FL_T + 0,15)
DENS = 33.0
rng = np.random.default_rng(23)


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


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def BL(a, w=0.0, t=0.0):
    return P0 + A_ * a + W_ * w + T_ * t


def hw(a):
    return lerp(HW0, HW1, (a - A_BASE) / (A_SH - A_BASE))


# ------------------------------------------------------------------ facettes (géométrie avant la peinture : la tuile suit le contour)
def facet_frame(poly, inward_hint):
    """poly : sommets 3D coplanaires (repère monde). Renvoie X (le long), Y, n (extérieur), coordonnées 2D, centre du rectangle."""
    P = [np.asarray(p, float) for p in poly]
    X = unit(P[-1] - P[0]) if len(P) == 4 else unit(P[2] - (P[0] + P[1]) / 2)
    n = unit(np.cross(P[1] - P[0], P[-1] - P[0]))
    if n @ inward_hint > 0:
        n = -n
    X = unit(X - (X @ n) * n)
    Y = np.cross(n, X)
    o = P[0]
    xy = np.array([((p - o) @ X, (p - o) @ Y) for p in P])
    return X, Y, n, o, xy


FACETS = []          # (nom, poly 3D, côté st, côté sw, partie)
for st in (1, -1):
    for sw in (1, -1):
        R0, R1 = BL(A_BASE, 0, st * KT * HW0), BL(A_SH, 0, st * KT * HW1)
        E0, E1 = BL(A_BASE, sw * HW0, 0), BL(A_SH, sw * HW1, 0)
        tag = ("e" if st > 0 else "i") + ("h" if sw > 0 else "b")
        FACETS.append((f"facette_{tag}", [R0, E0, E1, R1], st, sw, "corps"))
        FACETS.append((f"pointe_{tag}", [R1, E1, BL(A_TIP, TIP_W, 0)], st, sw, "pointe"))


def line_dist(p, a, b):
    """Distance de points 2D p (n, 2) à la droite (a, b)."""
    d = unit(b - a)
    q = p - a
    return np.abs(q[:, 0] * d[1] - q[:, 1] * d[0])


def paint_facet(poly, st, sw, part, seed):
    centre = BL((A_BASE + A_TIP) / 2)
    hint = centre - np.mean(poly, axis=0)
    X, Y, n, o, xy = facet_frame(poly, hint)
    x0, y0 = xy.min(0) - 0.04
    x1, y1 = xy.max(0) + 0.04
    w, h = x1 - x0, y1 - y0
    Wt, Ht = int(math.ceil(w * DENS)), int(math.ceil(h * DENS))
    ss = 3
    GW, GH = Wt * ss, Ht * ss
    jj, ii = np.mgrid[0:GH, 0:GW]
    px = x0 + (ii + 0.5) / GW * w
    py = y1 - (jj + 0.5) / GH * h
    pts = np.stack([px.ravel(), py.ravel()], 1)
    m = Image.new("L", (GW, GH), 0)
    ImageDraw.Draw(m).polygon([((x - x0) / w * GW, (y1 - y) / h * GH) for x, y in xy], fill=255)
    mask = np.array(m) > 127
    # distances à l'arête (ridge) et au tranchant (edge)
    if part == "corps":
        dr = line_dist(pts, xy[0], xy[3]).reshape(GH, GW)
        de = line_dist(pts, xy[1], xy[2]).reshape(GH, GW)
    else:
        dr = line_dist(pts, xy[0], xy[2]).reshape(GH, GW)
        de = line_dist(pts, xy[1], xy[2]).reshape(GH, GW)
    f = dr / np.maximum(dr + de, 1e-6)                      # 0 sur l'arête, 1 sur le tranchant
    P3 = o + px[..., None] * X + py[..., None] * Y
    a = (P3 - P0) @ A_
    u = np.clip((a - A_BASE) / (A_TIP - A_BASE), 0, 1)       # 0 au talon, 1 à la pointe
    r = np.random.default_rng(seed)
    # glace : bleu profond au talon, cyan, presque blanc vers la pointe
    c = np.empty(a.shape + (3,), np.float32)
    deep, body, pale = np.array((30, 96, 168.)), np.array((92, 186, 232.)), np.array((168, 226, 250.))
    k1 = np.clip(u / 0.22, 0, 1)[..., None]
    k2 = np.clip((u - 0.22) / 0.78, 0, 1)[..., None]
    c[...] = lerp(lerp(deep, body, k1), pale, k2 * 0.85)
    al = 150 + 24 * u
    # chevrons de taille : paliers obliques (miroir entre facettes hautes et basses : chevrons)
    g = np.floor((a * 0.75 + 2.2 * f) / 1.35) % 2
    c *= (1 + 0.06 * (g - 0.5) * 2)[..., None]
    # bande d'arête plus claire, puis biseau du tranchant (une seconde taille, plus claire et plus opaque)
    band_r = f < 0.24
    c = np.where(band_r[..., None], lerp(c, np.array((214, 244, 255.)), 0.35), c)
    al = np.where(band_r, al + 18, al)
    bev = f > 0.74
    c = np.where(bev[..., None], lerp(c, np.array((232, 250, 255.)), 0.55), c)
    al = np.where(bev, 205, al)
    if part == "pointe":
        c = lerp(c, np.array((236, 250, 255.)), 0.18)
        al = al + 10
    # fissures blanches fines (3 texels), ramifiées
    cr = Image.new("L", (GW, GH), 0)
    dc = ImageDraw.Draw(cr)
    nfis = 3 if part == "corps" else 1
    for _ in range(nfis):
        sx = r.uniform(0.12, 0.85) * w + x0
        sy = r.uniform(0.25, 0.75) * h + y0
        pl = [(sx, sy)]
        ang = r.uniform(-0.9, 0.9)
        for k in range(4):
            ang += r.uniform(-0.8, 0.8)
            ln = r.uniform(0.25, 0.6)
            pl.append((pl[-1][0] + math.cos(ang) * ln, pl[-1][1] + math.sin(ang) * ln * 0.6))
            if k == 1:
                b = pl[-1]
                a2 = ang + r.choice([-1, 1]) * r.uniform(0.9, 1.4)
                dc.line([((b[0] - x0) / w * GW, (y1 - b[1]) / h * GH),
                         ((b[0] + math.cos(a2) * 0.3 - x0) / w * GW, (y1 - b[1] - math.sin(a2) * 0.18) / h * GH)], fill=255, width=2 * ss)
        dc.line([((x - x0) / w * GW, (y1 - y) / h * GH) for x, y in pl], fill=255, width=3 * ss)
    fis = np.array(cr) > 127
    c = np.where(fis[..., None], np.array((240, 252, 255.)), c)
    al = np.where(fis, 215, al)
    # givre en dentelle au talon
    if part == "corps":
        nz = np.array(Image.fromarray((r.random((12, 40)) * 255).astype(np.uint8), "L").resize((GW, GH), Image.BICUBIC), np.float32) / 255
        frost = (u < 0.035 + 0.05 * nz) & (nz > 0.35)
        c = np.where(frost[..., None], np.array((236, 248, 255.)), c)
        al = np.where(frost, 222, al)
    # lignes d'arête et de tranchant : blanc net, ≥ 3 texels
    rid = dr < 3.2 / DENS
    edg = de < 2.4 / DENS
    c = np.where((rid | edg)[..., None], np.array((246, 253, 255.)), c)
    al = np.where(rid | edg, 222, al)
    # réduction : couleur LANCZOS, alpha franc sur le contour (moyenne du masque > 0,5), valeur peinte dedans
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((Wt, Ht), Image.LANCZOS))
    inside = mask.reshape(Ht, ss, Wt, ss).mean(axis=(1, 3)) > 0.5
    alv = np.array(Image.fromarray(np.clip(al, 0, 255).astype(np.uint8), "L").resize((Wt, Ht), Image.BOX))
    alpha = np.where(inside, np.clip(alv, 150, 222), 0).astype(np.uint8)
    out = np.dstack([rgb, alpha]).astype(np.uint8)
    out[~inside, :3] = (150, 220, 245)
    return out, dict(X=X, Y=Y, n=n, c=o + X * (x0 + w / 2) + Y * (y0 + h / 2), w=w, h=h)


# ------------------------------------------------------------------ tuiles opaques
def strip_tile(base, light, dark, W=96, H=24, seed=1, line=None):
    """Bande de métal ou de glace : dégradé travers (facette), léger brossé, liseré clair optionnel."""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W]
    q = (yy + 0.5) / H
    c = lerp(np.array(light, np.float32), np.array(dark, np.float32), (q ** 1.1)[..., None])
    c = lerp(c, np.array(base, np.float32), 0.45)
    c *= (1 + 0.05 * np.sin(xx * 0.7 + r.uniform(0, 6)) * np.sin(yy * 0.4))[..., None]
    if line is not None:
        c[int(H * 0.38):int(H * 0.38) + 3] = line
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(c, 0, 255)
    out[..., 3] = 255
    return out


def cap_tile(light, dark, n=24):
    """Bout facetté : quatre triangles (clair en haut à gauche, sombre en bas à droite)."""
    yy, xx = np.mgrid[0:n, 0:n]
    u, v = (xx + 0.5) / n - 0.5, (yy + 0.5) / n - 0.5
    k = np.where(np.abs(u) > np.abs(v), np.where(u < 0, 0.15, 0.7), np.where(v < 0, 0.0, 0.9))
    c = lerp(np.array(light, np.float32), np.array(dark, np.float32), k[..., None])
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = c
    out[..., 3] = 255
    return out


def cuir_tile(W=128, H=16):
    """Cuir bleu nuit enroulé en biais, couture d'argent."""
    r = np.random.default_rng(5)
    yy, xx = np.mgrid[0:H, 0:W]
    f = ((xx + yy * 0.9) / 14.0) % 1.0
    c = lerp(np.array((44, 56, 104.)), np.array((16, 20, 44.)), f[..., None])
    c = np.where((f > 0.86)[..., None], np.array((8, 10, 24.)), c)
    c *= r.uniform(0.95, 1.05, (H, W))[..., None]
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(c, 0, 255)
    for x in range(3, W - 4, 10):
        out[6:10, x:x + 5, :3] = (176, 196, 220)
    out[..., 3] = 255
    return out


def coeur_tile(W=480, H=14):
    yy, xx = np.mgrid[0:H, 0:W]
    q = np.abs((yy + 0.5) / H - 0.5) * 2
    c = lerp(np.array((200, 248, 255.)), np.array((60, 168, 226.)), (q ** 1.3)[..., None])
    c *= (1 + 0.06 * np.sin(xx * 0.21))[..., None]
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(c, 0, 255)
    out[..., 3] = 255
    e = np.zeros((H, W, 4), np.uint8)
    ec = lerp(np.array((210, 248, 255.)), np.array((110, 200, 240.)), (q ** 1.2)[..., None])
    ec *= (0.9 + 0.1 * np.sin(xx * 0.13))[..., None]
    e[..., :3] = np.clip(ec, 0, 255)
    e[..., 3] = 255
    return out, e


def flocon_tile(n=88):
    """Flocon à six branches, argent givré, centre hexagonal cyan ; calque _e sur le centre et l'axe des branches."""
    ss = 4
    N = n * ss
    m = Image.new("L", (N, N), 0)
    core = Image.new("L", (N, N), 0)
    d, dk = ImageDraw.Draw(m), ImageDraw.Draw(core)
    C = N / 2
    R = N * 0.48
    for k in range(6):
        th = math.radians(90 + 60 * k)
        ex, ey = C + math.cos(th) * R, C - math.sin(th) * R
        d.line([(C, C), (ex, ey)], fill=255, width=int(N * 0.085))
        dk.line([(C, C), (C + math.cos(th) * R * 0.82, C - math.sin(th) * R * 0.82)], fill=255, width=int(N * 0.028))
        for fr, ln in ((0.42, 0.24), (0.68, 0.17)):
            bx, by = C + math.cos(th) * R * fr, C - math.sin(th) * R * fr
            for sg in (-1, 1):
                t2 = th + sg * math.radians(55)
                d.line([(bx, by), (bx + math.cos(t2) * R * ln, by - math.sin(t2) * R * ln)], fill=255, width=int(N * 0.06))
        # bout de branche : petit losange
        d.polygon([(ex + math.cos(th) * N * 0.0, ey), (ex - math.cos(th + 1.2) * N * 0.04, ey + math.sin(th + 1.2) * N * 0.04),
                   (C + math.cos(th) * R * 0.9, C - math.sin(th) * R * 0.9), (ex - math.cos(th - 1.2) * N * 0.04, ey + math.sin(th - 1.2) * N * 0.04)], fill=255)
    hexa = [(C + math.cos(math.radians(30 + 60 * k)) * N * 0.14, C - math.sin(math.radians(30 + 60 * k)) * N * 0.14) for k in range(6)]
    d.polygon(hexa, fill=255)
    hexi = [(C + math.cos(math.radians(30 + 60 * k)) * N * 0.085, C - math.sin(math.radians(30 + 60 * k)) * N * 0.085) for k in range(6)]
    dk.polygon(hexi, fill=255)
    yy, xx = np.mgrid[0:N, 0:N]
    rr = np.hypot(xx - C, yy - C) / R
    c = lerp(np.array((236, 244, 250.)), np.array((132, 156, 182.)), np.clip(rr, 0, 1)[..., None] ** 1.2)
    sh = ((xx - C) * 0.6 + (yy - C) * 0.8) / R                     # éclairage de biais
    c *= (1 - 0.12 * sh)[..., None]
    corem = np.array(core) > 127
    c = np.where(corem[..., None], lerp(np.array((150, 226, 255.)), np.array((220, 250, 255.)), np.clip(1 - rr * 3, 0, 1)[..., None]), c)
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.LANCZOS))
    al = np.array(m.resize((n, n), Image.LANCZOS)) > 110
    # liseré d'ombre au bord : les branches se détachent du moyeu d'argent
    er = np.array(Image.fromarray(al.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(3))) > 127
    rgb[al & ~er] = (rgb[al & ~er] * 0.62).astype(np.uint8)
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    out[~al, :3] = (180, 200, 220)
    ce = np.array(core.resize((n, n), Image.LANCZOS)) > 110
    e = np.zeros((n, n, 4), np.uint8)
    e[ce & al] = (150, 222, 255, 255)
    return out, e


def star_tile(n=40, sharp=True):
    """Étoile à quatre branches (scintillement) : blanc au centre, cyan au bout."""
    ss = 4
    N = n * ss
    m = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(m)
    C = N / 2
    for k in range(4):
        th = math.radians(90 * k)
        L = N * (0.48 if k % 2 == 0 else 0.40)
        p = [(C + math.cos(th) * L, C - math.sin(th) * L), (C + math.cos(th + math.pi / 2) * N * 0.07, C - math.sin(th + math.pi / 2) * N * 0.07),
             (C, C), (C + math.cos(th - math.pi / 2) * N * 0.07, C - math.sin(th - math.pi / 2) * N * 0.07)]
        d.polygon(p, fill=255)
    d.ellipse([C - N * 0.1, C - N * 0.1, C + N * 0.1, C + N * 0.1], fill=255)
    yy, xx = np.mgrid[0:N, 0:N]
    rr = np.hypot(xx - C, yy - C) / (N / 2)
    c = lerp(np.array((255, 255, 255.)), np.array((150, 226, 255.)), np.clip(rr * 1.4, 0, 1)[..., None])
    rgb = np.array(Image.fromarray(c.astype(np.uint8), "RGB").resize((n, n), Image.LANCZOS))
    al = np.array(m.resize((n, n), Image.LANCZOS)) > 110
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    out[~al, :3] = (220, 245, 255)
    e = out.copy()
    e[~al] = 0
    return out, e


def eclat_tile(n=40):
    """Particule : éclat de givre anguleux, deux facettes peintes, liseré blanc."""
    ss = 4
    N = n * ss
    m = Image.new("L", (N, N), 0)
    P = [(0.52, 0.03), (0.70, 0.36), (0.62, 0.52), (0.80, 0.70), (0.50, 0.97), (0.40, 0.66), (0.22, 0.58), (0.38, 0.30)]
    ImageDraw.Draw(m).polygon([(x * N, y * N) for x, y in P], fill=255)
    yy, xx = np.mgrid[0:N, 0:N]
    side = (xx / N - 0.5) * 1.0 + (yy / N - 0.5) * 0.25
    c = np.where((side < 0)[..., None], np.array((214, 244, 255.)), np.array((112, 196, 236.)))
    rgb = np.array(Image.fromarray(c.astype(np.uint8), "RGB").resize((n, n), Image.LANCZOS))
    al = np.array(m.resize((n, n), Image.LANCZOS)) > 110
    er = np.array(Image.fromarray(al.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(3))) > 127
    rgb[al & ~er] = (248, 254, 255)
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    out[~al, :3] = (180, 230, 250)
    e = np.zeros_like(out)
    e[al & ~er] = (170, 230, 255, 255)
    return out, e


def brume_tile(n=36):
    """Particule : brume froide, bouffée douce semi-transparente (groupe trans_)."""
    r = np.random.default_rng(41)
    yy, xx = np.mgrid[0:n, 0:n]
    u, v = (xx + 0.5) / n * 2 - 1, (yy + 0.5) / n * 2 - 1
    d = np.full((n, n), 9.0)
    for _ in range(6):
        cx, cy, rr = r.uniform(-0.3, 0.3), r.uniform(-0.25, 0.25), r.uniform(0.45, 0.62)
        d = np.minimum(d, np.hypot(u - cx, (v - cy) * 1.25) / rr)
    a = np.clip(1 - d, 0, 1) ** 0.9
    lum = np.clip(1 - np.hypot(u + 0.3, v + 0.35) / 1.4, 0, 1)
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = lerp(np.array((168, 200, 226.)), np.array((240, 250, 255.)), lum[..., None]).astype(np.uint8)
    out[..., 3] = np.where(a > 0.06, np.clip(a * 190, 1, 190), 0).astype(np.uint8)
    return out


UV = {}
TRANS_TILES = set()
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
FACET_INFO = {}


def atlas():
    items = []
    for i, (nm, poly, st, sw, part) in enumerate(FACETS):
        im, info = paint_facet(poly, st, sw, part, 100 + i)
        FACET_INFO[nm] = info
        items.append((nm, im, None))
        TRANS_TILES.add(nm)
    co, coe = coeur_tile()
    items.append(("coeur", co, coe))
    items.append(("coeur_cap", np.ascontiguousarray(co[:, :14]), np.ascontiguousarray(coe[:, :14])))
    AL, AM, AD = (236, 244, 250), (166, 186, 206), (74, 90, 116)
    items.append(("argent_h", strip_tile(AM, AL, AM, seed=2, line=(250, 253, 255)), None))
    items.append(("argent_b", strip_tile(AM, AM, AD, seed=3), None))
    items.append(("argent_cap", cap_tile(AL, AD), None))
    GL, GM, GD = (232, 250, 255), (120, 206, 238), (30, 92, 150)
    gl = strip_tile(GM, GL, GD, seed=4, line=(246, 254, 255))
    gle = np.zeros_like(gl)
    gle[int(24 * 0.38):int(24 * 0.38) + 3] = (150, 226, 255, 255)
    items.append(("glace", gl, gle))
    items.append(("glace_cap", cap_tile(GL, GD), None))
    items.append(("cuir", cuir_tile(), None))
    items.append(("cuir_cap", cap_tile((50, 62, 110), (14, 18, 40), 16), None))
    fl, fle = flocon_tile()
    items.append(("flocon", fl, fle))
    stt, ste = star_tile()
    items.append(("etoile", stt, ste))
    ec, ece = eclat_tile()
    items.append(("eclat", ec, ece))
    items.append(("brume", brume_tile(), None))
    TRANS_TILES.add("brume")
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, im, ime in sorted(items, key=lambda it: -it[1].shape[0]):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, f"atlas plein ({n})"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None:
            tex_e[y:y + h, x:x + w] = ime
        x += w + 1
        shelf = max(shelf, h)
    assert tex[TEX - 3, TEX - 3, 3] == 0
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    zone = np.zeros(semi.shape, bool)
    for n in TRANS_TILES:
        u0, v0, u1, v1 = UV[n]
        zone[v0:v1, u0:u1] = True
    assert not (semi & ~zone).any(), "semi-transparence hors des tuiles trans_"
    assert set(np.unique(tex_e[..., 3])) <= {0, 255}
    print(f"atlas : rangées utilisées jusqu'à y = {y + shelf}")
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


def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def euler(R):
    """Angles (X, Y, Z) tels que R = Rz Ry Rx (ordre du mod et du renderer), blocage de cardan traité, vérifié par reconstruction."""
    if abs(R[2, 0]) < 0.99999:
        ry = math.asin(-R[2, 0])
        e = (math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0])))
    elif R[2, 0] < 0:
        e = (math.degrees(math.atan2(R[0, 1], R[0, 2])), 90.0, 0.0)
    else:
        e = (math.degrees(math.atan2(-R[0, 1], -R[0, 2])), -90.0, 0.0)
    assert np.allclose(rotm(*e), R, atol=1e-6), "euler"
    return e


def group(name, origin, parent=None):
    assert name not in groups, name
    groups[name] = {"origin": [round(float(v), 4) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "rotation": [0, 0, 0]}
    return name


def cube(g, name, frm, to, origin, rot, faces, prec=3):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), prec) for v in frm], "to": [round(float(v), prec) for v in to],
         "origin": [round(float(v), prec) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def oriented(g, name, c, X, Y, half, faces, prec=3):
    X = unit(X)
    Y = unit(np.asarray(Y, float) - (np.asarray(Y, float) @ X) * X)
    Z = np.cross(X, Y)
    c = np.asarray(c, float)
    half = np.asarray(half, float)
    cube(g, name, c - half, c + half, c, euler(np.column_stack([X, Y, Z])), faces, prec)


def full(tile):
    return list(UV[tile])


def strip(tile, cap, u0=0.0, u1=1.0):
    bu0, bv0, bu1, bv1 = UV[tile]
    ua = lerp(bu0, bu1, u0)
    ub = max(lerp(bu0, bu1, u1), ua + 2)
    lg = [ua, bv0, ub, bv1]
    return {"south": lg, "north": lg, "up": lg, "down": lg, "east": full(cap), "west": full(cap)}


def frame_of(X, ref):
    X = unit(X)
    ref = np.asarray(ref, float)
    if abs(ref @ X) > 0.95:
        ref = np.array((0.0, 0.0, 1.0)) if abs(X[2]) < 0.9 else np.array((1.0, 0.0, 0.0))
    Y = unit(ref - (ref @ X) * X)
    return X, Y, np.cross(X, Y)


def bar2(g, name, p, q, r, tile, cap, ref=W_, inset=0.1, u0=0.0, u1=1.0):
    """Octogone en deux cubes (0 et 45°) ; le second est rentré de 0,1 px à chaque bout : bouts jamais à moins de 0,1 px."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X, Y, Z = frame_of(q - p, ref)
    c45, s45 = math.cos(math.pi / 4), math.sin(math.pi / 4)
    fb = strip(tile, cap, u0, u1)
    cube(g, name, p + (0, -r, -r), p + (L, r, r), p, euler(np.column_stack([X, Y, Z])), fb)
    cube(g, name + "o", p + (inset, -r * 0.97, -r * 0.97), p + (L - inset, r * 0.97, r * 0.97), p,
         euler(np.column_stack([X, c45 * Y + s45 * Z, -s45 * Y + c45 * Z])), fb)


def bar8(g, name, p, q, r, tile, cap, ref=W_, ov=0.03, u0=0.0, u1=1.0, ends=True):
    """Octogone régulier : 4 plaques à 0, 45, 90, 135° (union exacte), bouts décalés de 0,03 px par plaque."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X, Y, Z = frame_of(q - p, ref)
    a_ = r * math.tan(math.pi / 8) * 1.02
    cu0, cv0, cu1, cv1 = UV[cap]
    cm, ch_ = (cu0 + cu1) / 2, (cu1 - cu0) / 2 * a_ / r
    fk = dict(strip(tile, cap, u0, u1), east=[cm - ch_, cv0, cm + ch_, cv1], west=[cm - ch_, cv0, cm + ch_, cv1])
    if not ends:
        fk.update(east=CLEAR, west=CLEAR)
    for k in range(4):
        gk = math.pi / 4 * k
        Yk = math.cos(gk) * Y + math.sin(gk) * Z
        Rk = np.column_stack([X, Yk, np.cross(X, Yk)])
        d = 0.03 * k
        cube(g, name + ("", "b", "c", "d")[k], p + (-ov + d, -r, -a_), p + (L + ov - d, r, a_), p, euler(Rk), fk)


def prism(g, name, p, d, r, L, tile, cap, ref=W_, octo=True, K=1.0, u0=0.0, u1=1.0, ov=0.06):
    """Cristal pointu : corps octogonal (deux cubes à 45°) ou en losange (un cube), pointe en biseau faite de deux cubes
    tournés de 45° autour de deux axes perpendiculaires (pointe vue de deux côtés). K : réduction autour de p (caché au repos)."""
    p = np.asarray(p, float)
    X, Y, Z = frame_of(d, ref)
    rd = r if octo else r * math.sqrt(2)
    Lb = L - rd
    E = p + X * Lb
    pr = 4
    def sc(v):
        return p + (np.asarray(v, float) - p) / K
    c45, s45 = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R45 = np.column_stack([X, c45 * Y + s45 * Z, -s45 * Y + c45 * Z])
    fb = strip(tile, cap, u0, u1)
    if octo:
        R0 = np.column_stack([X, Y, Z])
        cube(g, name, p + np.array((-ov, -r, -r)) / K, p + np.array((Lb + ov, r, r)) / K, p, euler(R0), fb, pr)
        cube(g, name + "o", p + np.array((-ov + 0.12, -r * 0.97, -r * 0.97)) / K, p + np.array((Lb + ov - 0.12, r * 0.97, r * 0.97)) / K, p, euler(R45), fb, pr)
    else:
        cube(g, name, p + np.array((-ov, -r, -r)) / K, p + np.array((Lb + 0.02, r, r)) / K, p, euler(R45), fb, pr)
    rp = rd - 0.11 if octo else 0.7 * rd
    h = rd / math.sqrt(2)
    Ec = sc(E)
    XA, ZA = (X + Z) * c45, (-X + Z) * c45
    oriented(g, name + "pa", Ec, XA, Y, np.array((h, rp, h)) / K, {f: full(cap) for f in ("north", "south", "east", "west", "up", "down")}, pr)
    if octo:
        XB, YB = (X + Y) * c45, (-X + Y) * c45
        oriented(g, name + "pb", Ec, XB, YB, np.array((h, h, rp)) / K, {f: full(cap) for f in ("north", "south", "east", "west", "up", "down")}, pr)


def plate(g, name, c, X, Y, w, h, tile, th=0.3, back=False):
    """Plaque fine : face +Z (south) peinte, tranches transparentes ; back=True peint aussi la face arrière."""
    X = unit(X)
    Y = unit(np.asarray(Y, float) - (np.asarray(Y, float) @ X) * X)
    u0, v0, u1, v1 = UV[tile]
    faces = {"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1] if back else CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_), faces)


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


bras = group("right_arm", [5, 22, 0])
prise = group("prise", P0, parent=bras)
coup = group("coup", P0, parent=prise)

# Fusée : cuir bleu nuit sous le poing, viroles d'argent
# (bouts de la fusée cachés dans les viroles et le moyeu : transparents, aucune face parallèle à moins de 0,1 px)
bar8(coup, "fusee", BL(-2.4), BL(1.9), 0.5, "cuir", "cuir_cap", u0=0.0, u1=1.0, ov=0.0, ends=False)
bar2(coup, "virole_av", BL(0.85), BL(1.25), 0.65, "argent_h", "argent_cap", inset=0.12)
bar2(coup, "virole_ar", BL(-2.8), BL(-2.2), 0.65, "argent_h", "argent_cap", inset=0.12)
# Pommeau : petit prisme de glace, pointe vers l'arrière
pom = group("pommeau", BL(-2.55), parent=coup)
prism(pom, "pommeau_prisme", BL(-2.44), -A_, 0.46, 1.25, "glace", "glace_cap", ref=W_, u0=0.1, u1=0.35, ov=0.0)

# Garde : moyeu octogonal (axe t), flocons sur les flancs, cristaux d'argent en éventail
garde = group("garde", BL(HUB_A), parent=coup)
bar2(garde, "moyeu", BL(HUB_A, 0, -HUB_T), BL(HUB_A, 0, HUB_T), HUB_R, "argent_b", "argent_cap", ref=A_, inset=0.12)
FLOCONS = []
for s in (1, -1):
    fg = group(f"flocon_{'e' if s > 0 else 'i'}", BL(HUB_A, 0, s * FL_T), parent=garde)
    FLOCONS.append(fg)
    # face peinte vers l'extérieur (+Z local = s·t)
    X = A_ if s > 0 else -A_
    plate(fg, f"flocon_{'e' if s > 0 else 'i'}", BL(HUB_A, 0, s * FL_T), X, W_, 2.5, 2.5, "flocon")

# cristaux : (côté sw, angle depuis la verticale vers l'avant (deg), inclinaison vers l'extérieur (deg), longueur, rayon)
CRIST = [(1, 24, 0, 3.1, 0.36), (1, 58, 14, 2.2, 0.30), (1, -14, -12, 1.6, 0.27),
         (-1, 24, 0, 3.0, 0.36), (-1, 58, -14, 2.2, 0.30), (-1, -14, 12, 1.6, 0.27)]
CGROUPS = []
for i, (sw, ang, tilt, L, r) in enumerate(CRIST):
    th, tl = math.radians(ang), math.radians(tilt)
    d = unit(W_ * sw * math.cos(th) + A_ * math.sin(th) + T_ * math.tan(tl))
    base = BL(HUB_A) + d * 0.35
    cg = group(f"cristal_{'h' if sw > 0 else 'b'}{i % 3 + 1}", base, parent=garde)
    CGROUPS.append((cg, sw, i % 3))
    prism(cg, f"cristal_{'h' if sw > 0 else 'b'}{i % 3 + 1}", base, d, r, L, "argent_h", "argent_cap", ref=T_, u0=0.0 + 0.2 * (i % 3), u1=0.35 + 0.2 * (i % 3))

# Nova d'éclats de glace (attaque) : six éclats radiaux, cachés dans le moyeu au repos (×1/KE)
eclats = group("eclats", BL(HUB_A), parent=garde)
for k in range(6):
    th = math.radians(38 + 60 * k)
    d = unit(W_ * math.cos(th) + T_ * math.sin(th) + A_ * 0.35)
    prism(eclats, f"eclat{k + 1}", BL(HUB_A), d, 0.17, 2.7, "glace", "glace_cap", ref=A_, octo=False, K=KE, u0=0.4, u1=0.7, ov=0.0)

# Lame : peau de cristal trans_ + âme (cœur cyan) ; groupe lame = pivot au talon, pour qu'elle pousse depuis la garde
lame = group("lame", BL(HUB_A + 0.6), parent=garde)
peau = group("trans_lame", BL(HUB_A + 0.6), parent=lame)
for nm, poly, st, sw, part in FACETS:
    inf = FACET_INFO[nm]
    th = 0.3
    plate(peau, nm, inf["c"] - inf["n"] * th / 2, inf["X"], inf["Y"], inf["w"], inf["h"], nm, th=th)
coeur = group("coeur", BL(HUB_A + 0.6), parent=lame)
group("ctrl_lumiere", BL(HUB_A + 0.6), parent=coeur)


def diamond_bar(g, name, p, q, r, tile, cap, u0=0.0, u1=1.0):
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X, Y, Z = frame_of(q - p, W_)
    c45, s45 = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R45 = np.column_stack([X, c45 * Y + s45 * Z, -s45 * Y + c45 * Z])
    cube(g, name, p + (0, -r, -r), p + (L, r, r), p, euler(R45), strip(tile, cap, u0, u1))


diamond_bar(coeur, "coeur", BL(2.3), BL(A_SH + 0.25), 0.20, "coeur", "coeur_cap")
diamond_bar(coeur, "coeur_pointe", BL(A_SH - 0.25), BL(A_TIP - 1.15, TIP_W * 0.7), 0.07, "coeur", "coeur_cap", 0.8, 1.0)

# Scintillements : étoiles face caméra (cam_), cachées par l'échelle hors de leur instant
GLINTS = []
for k, (a, w, t) in enumerate(((7.5, hw(7.5) + 0.05, 0.0), (12.8, -hw(12.8) - 0.05, 0.0), (A_TIP + 0.05, TIP_W, 0.0), (HUB_A, 0.0, FL_T + 0.25))):
    cg = group(f"cam_scintille{k + 1}", BL(a, w, t), parent=lame if k < 3 else garde)
    GLINTS.append(cg)
    c = BL(a, w, t) + np.array((0, 0, 0.2)) / KG * GF[k]
    sz = (1.45 if k < 3 else 1.15) / KG * GF[k]
    u0, v0, u1, v1 = UV["etoile"]
    cube(cg, f"scintille{k + 1}", c - (sz / 2, sz / 2, 0.15 / KG * GF[k]), c + (sz / 2, sz / 2, 0.15 / KG * GF[k]), c, (0, 0, 0),
         {"south": [u0, v0, u1, v1], "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})

# Points d'émission : éclats le long des tranchants, brume sous la lame
EMITS = []
for k, a in enumerate((6.0, 11.0, 16.0)):
    EMITS.append(group("emit_eclat" + (str(k + 1) if k else ""), BL(a, (1 if k % 2 == 0 else -1) * (hw(a) + 0.1)), parent=lame))
for k, a in enumerate((5.0, 12.5)):
    EMITS.append(group("emit_brume" + (str(k + 1) if k else ""), BL(a, -hw(a) - 0.4), parent=lame))

# Particules (racine, non portées) : recette validée, un seul cube de 0,3 px, face up seule, au-dessus du pivot
PE = group("particle_eclat", [0, 0, 0])
u0, v0, u1, v1 = UV["eclat"]
cube(PE, "eclat", [-0.65, 0.3, -0.65], [0.65, 0.6, 0.65], [0, 0.45, 0], (0, 0, 0), {"up": [u0, v0, u1, v1]})
PB = group("particle_brume", [0, 0, 0])
PBT = group("trans_particule_brume", [0, 0, 0], parent=PB)
u0, v0, u1, v1 = UV["brume"]
cube(PBT, "brume", [-1.3, 0.3, -1.3], [1.3, 0.6, 1.3], [0, 0.45, 0], (0, 0, 0), {"up": [u0, v0, u1, v1]})

outliner = [bone_node(bras), bone_node(PE), bone_node(PB)]


# ------------------------------------------------------------------ animations
# Guide, section 3 : +X bascule le haut vers l'arrière, donc relève la pointe (devant) ; +Y avance le côté droit, donc la pointe part
# vers l'intérieur (-X) ; +Z monte le côté droit. Une seule main : pas de miroir. pose(rise, inward, roll) : roll penche le tranchant
# du haut vers l'extérieur.
def pose(rise, inward, roll):
    return rise, inward, -roll


def kf(t, x, y, z, ch="rotation"):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 4)), "y": str(round(y + 0.0, 4)), "z": str(round(z + 0.0, 4))}],
            "time": round(t, 4), "interpolation": "linear"}


def anim(name, length, tracks, fps=24, loop="loop"):
    """tracks : {(groupe, canal): f(t) -> (x, y, z)}."""
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A = {}
    for (g, ch), f in tracks.items():
        A.setdefault(groups[g]["uuid"], {"name": g, "type": "bone", "keyframes": []})["keyframes"] += [kf(t, *f(t), ch=ch) for t in times]
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


def state(name, L, rise, inward, roll, amp, cycles, fps=12):
    """La glace ne plie pas : la lame entière oscille, raide, avec un petit tremblement en plus."""
    def f(t):
        ph = TAU * cycles * t / L
        return pose(rise + amp * math.sin(ph), inward + 0.35 * amp * math.sin(ph + 1.2), roll + 0.25 * amp * math.sin(ph + 0.6))
    return anim(name, L, {(prise, "rotation"): f}, fps=fps)


idle = state("idle", 8.0, 0.0, 0.0, 0.0, 0.8, 2, fps=6)
walk = state("walk", 1.6, 2.0, 0.5, 0.0, 2.0, 1)
run = state("run", 1.0, 10.0, 2.0, 2.0, 3.0, 1, fps=16)
sneak = state("sneak", 3.0, -18.0, 2.0, -3.0, 0.8, 1)
fall = state("fall", 2.0, 6.0, 0.0, 0.0, 1.5, 1)


# attack (once, 0,8 s) : petit armé, coupe, la garde s'écarte, nova d'éclats, flash du cœur ; tout revient à 0 avant 0,75 s
def coup_attack(t):
    up = bump(t, 0.0, 0.08, 0.08, 0.16)
    cut = bump(t, 0.08, 0.2, 0.26, 0.7)
    return pose(7 * up - 14 * cut, 4 * cut, 6 * cut)


def eclats_scale(t):
    k = sm(t, 0.1, 0.17) * (1 + 0.15 * bump(t, 0.17, 0.22, 0.24, 0.32)) * (1 - sm(t, 0.42, 0.62))
    s = 1 + (KE - 1) * k
    return s, s, s


def eclats_rot(t):
    return 0.0, 0.0, 0.0


def coeur_scale(t):
    k = bump(t, 0.08, 0.14, 0.22, 0.5)
    return 1 + 0.28 * k, 1 + 0.28 * k, 1.0


def coeur_lum(t):
    return 1.6 * bump(t, 0.08, 0.13, 0.22, 0.55), 0.0, 0.0


tr_a = {(coup, "rotation"): coup_attack, (eclats, "scale"): eclats_scale,
        (coeur, "scale"): coeur_scale, ("ctrl_lumiere", "position"): coeur_lum}
for cg, sw, j in CGROUPS:
    tr_a[(cg, "rotation")] = (lambda t, sw=sw, j=j: (sw * (10 + 4 * j) * bump(t, 0.09 + 0.02 * j, 0.17 + 0.02 * j, 0.24, 0.6), 0.0, 0.0))
for k, g in enumerate(GLINTS[:3]):
    pass
attack = anim("attack", 0.8, tr_a, fps=40, loop="once")


# hurt (once, 0,8 s) : sursaut et tremblement amorti, les cristaux vibrent
def coup_hurt(t):
    env = sm(t, 0.0, 0.05) * (1 - sm(t, 0.45, 0.75))
    trem = math.sin(TAU * t / 0.1) * math.exp(-4.0 * t)
    return pose(env * (-6 + 3.5 * trem), env * 1.5, env * 4 * trem)


tr_h = {(coup, "rotation"): coup_hurt}
for cg, sw, j in CGROUPS:
    tr_h[(cg, "rotation")] = (lambda t, sw=sw, j=j: (sw * 3 * math.sin(TAU * t / 0.07 + j) * math.exp(-6 * t) * sm(t, 0, 0.03) * (1 - sm(t, 0.6, 0.75)), 0.0, 0.0))
hurt = anim("hurt", 0.8, tr_h, fps=40, loop="once")


# event_equip (1,2 s) : les cristaux de la garde poussent en cascade, les flocons tournent, puis la lame pousse depuis la garde
def grow(t, a, b, over=0.1, lo=0.02):
    k = sm(t, a, b)
    k += over * math.sin(math.pi * sm(t, b - 0.08, b + 0.14)) * (t < b + 0.14)
    return lo + (1 - lo) * k


tr_e = {}
ORDRE = [0, 3, 1, 4, 2, 5]
for rank, i in enumerate(ORDRE):
    cg = CGROUPS[i][0]
    a0 = 0.02 + 0.06 * rank
    tr_e[(cg, "scale")] = (lambda t, a0=a0: (grow(t, a0, a0 + 0.22),) * 3)
for fg in FLOCONS:
    tr_e[(fg, "rotation")] = (lambda t: (360 * sm(t, 0.0, 0.7), 0.0, 0.0))
    tr_e[(fg, "scale")] = (lambda t: (grow(t, 0.0, 0.3, 0.0, 0.2),) * 3)


def lame_grow(t):
    z = grow(t, 0.36, 1.0, 0.04, 0.01)
    xy = lerp(0.35, 1.0, sm(t, 0.36, 0.95))
    return xy, xy, z


tr_e[(lame, "scale")] = lame_grow
tr_e[(GLINTS[2], "scale")] = (lambda t: ((1 + (1.3 * KG - 1) * bump(t, 0.95, 1.02, 1.06, 1.18)) / GF[2],) * 3)
equip = anim("event_equip", 1.2, tr_e, fps=30, loop="once")


# overlay_scintille (6 s, permanente) : chaque étoile s'allume une fois, à son tour ; le cœur pulse doucement
L_OV = 6.0
TW = [(0.6, 0.0), (2.1, 25.0), (3.5, 10.0), (4.8, 40.0)]


def glint(k):
    t0, rot0 = TW[k]

    def sc(t):
        # repos à 1 (l'échelle d'event_equip se multiplie à celle-ci) ; pic à KG / GF = même étoile à l'écran
        v = 1 + (KG / GF[k] - 1) * bump(t, t0, t0 + 0.16, t0 + 0.2, t0 + 0.5)
        return v, v, v

    def ro(t):
        return 0.0, 0.0, rot0 + 60 * sm(t, t0, t0 + 0.5)
    return sc, ro


tr_o = {}
for k, g in enumerate(GLINTS):
    sc, ro = glint(k)
    tr_o[(g, "scale")] = sc
tr_o[("ctrl_lumiere", "position")] = (lambda t: (0.2 * math.sin(TAU * 2 * t / L_OV), 0.0, 0.0))
overlay = anim("overlay_scintille", L_OV, tr_o, fps=20)

# particules : l'éclat tourne sur lui-même, la brume tourne lentement et respire
PFE, PFB = 1.5, 4.0
pfe = anim("particle_eclat_fall", PFE, {(PE, "rotation"): lambda t: (30 * math.sin(TAU * t / PFE), 360 * t / PFE, 20 * math.cos(TAU * t / PFE))}, fps=12)
pfb = anim("particle_brume_fall", PFB, {(PB, "rotation"): lambda t: (0, 90 * math.sin(TAU * t / PFB), 0),
                                         (PB, "scale"): lambda t: (1 + 0.2 * math.sin(TAU * t / PFB),) * 3}, fps=6)

attack["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "block.amethyst_block.hit", "file": ""}], "time": 0.1}]}
equip["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "block.amethyst_block.chime", "file": ""}], "time": 0.4}]}

ANIMS = [idle, walk, run, sneak, fall, attack, hurt, equip, overlay, pfe, pfb]

# ------------------------------------------------------------------ écriture
assert 60 <= len(elements) <= 130, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from particules import retirer_particules
from sons import limiter_sons
retirer_particules(model, montantes=True)      # garde éclats et brume (rien ne se pose : pas d'animation _rest)
limiter_sons(model, attaque=True)
from reactions import retirer_reactions
retirer_reactions(model, garder=("attack",))
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;", len(EMITS), "emit_")
