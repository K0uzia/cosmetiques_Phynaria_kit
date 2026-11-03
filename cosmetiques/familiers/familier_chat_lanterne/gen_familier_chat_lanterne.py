"""Familier chat-lanterne : petit chat rond en lanterne de papier qui flotte à gauche du joueur. Design original (ensemble Kawaii).
Écrit familier_chat_lanterne.png, familier_chat_lanterne_e.png et .build/familier_chat_lanterne_brut.bbmodel à côté de ce script.

Corps : polyèdre de papier (10 fuseaux x 4 bandes) dont chaque facette est une PEAU fine peinte en 3D (côtes, visage, lueur de bougie),
autour d'une ÂME pleine (prismes octogonaux couleur ambre, qui comblent l'épaisseur et laissent filtrer la lumière aux jointures).
Cerclages en bambou haut et bas, anse en cordelette rose, pompon, oreilles peau + âme, queue en crochet.

Hiérarchie (body = torse du joueur) :
  fam_elan    (attack/hurt uniquement : position)
  fam_pos     (position d'état : flottement, rapprochement en sneak)
  fam_swing   (pivot au sommet de l'anse : balancement de lanterne)
  fam_snap    (attack/hurt uniquement : rotation)
  lanterne    (rotation de base Y = 25° : le visage regarde un peu vers l'extérieur ; animée pour les coups d'oeil)
    oreille_l, oreille_r, yeux (position : clignement, sommeil), queue1 > queue2 > queue3, pompon
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # calque _e embarqué en seconde texture (correctif du clignotement annoncé le 2026-11-03, à vérifier en jeu)
NOM = "familier_chat_lanterne"
TEX = 512
TAU = 2 * math.pi
SS = 3

# ------------------------------------------------------------------ forme du corps
RH, RV = 3.2, 2.95                  # rayons horizontal et vertical (lanterne un peu aplatie)
NLON, DLON = 10, 36.0               # fuseaux ; une côte au milieu du visage (phi = 0), un oeil par fuseau avant
LATS = [-64.0, -32.0, 0.0, 32.0, 64.0]
YAW = 25.0                          # le visage tourne vers l'extérieur (gauche du joueur)
C0 = np.array((-13.0, 26.5, 3.0))   # centre de la lanterne : côté gauche, hauteur d'épaule, un peu en arrière
TH = 0.3                            # épaisseur d'une peau

# ------------------------------------------------------------------ couleurs (bases poussées vers le blanc : nuit chaude = saumon sinon)
C_PAPIER = np.array((252, 250, 244), np.float32)
C_BAS = np.array((250, 242, 226), np.float32)
C_CHAUD = np.array((255, 228, 172), np.float32)
C_OMBRE = np.array((206, 186, 156), np.float32)
C_COTE = np.array((188, 150, 98), np.float32)
C_COTE_H = np.array((226, 196, 142), np.float32)
C_FIL = np.array((216, 196, 160), np.float32)
C_ROSE = np.array((248, 156, 176), np.float32)
C_ROSE_C = np.array((250, 190, 204), np.float32)
C_YEUX = np.array((56, 34, 46), np.float32)
C_BOUCHE = np.array((96, 52, 60), np.float32)
C_NEZ = np.array((238, 120, 146), np.float32)
C_FLAMME = np.array((255, 200, 120), np.float32)
C_FLAMME_C = np.array((255, 244, 206), np.float32)
E_CHAUD = np.array((255, 158, 66), np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def smv(x, a, b):
    u = np.clip((x - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def V(*a):
    return np.array(a, float)


def P(phi, lat, k=1.0):
    """Point de l'ellipsoïde (repère local de la lanterne, visage vers -Z, phi > 0 vers +X)."""
    p, l = math.radians(phi), math.radians(lat)
    return V(RH * math.cos(l) * math.sin(p), RV * math.sin(l), -RH * math.cos(l) * math.cos(p)) * k


def seg_dist(px, py, pts):
    """Distance de chaque point (px, py) à une polyligne."""
    d = np.full(px.shape, 1e9, np.float32)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        vx, vy = bx - ax, by - ay
        t = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy), 0, 1)
        d = np.minimum(d, np.hypot(px - ax - t * vx, py - ay - t * vy))
    return d


# ------------------------------------------------------------------ peinture 3D du papier
EYE_X, EYE_Y = 0.97, 0.72
EYE_W, EYE_H = 1.05, 1.22
MOUTH = [(-0.44, -0.10), (-0.33, -0.27), (-0.20, -0.31), (-0.08, -0.22), (0.0, -0.13), (0.08, -0.22), (0.20, -0.31), (0.33, -0.27), (0.44, -0.10)]
FLAMMES = (90.0, 180.0, -90.0)


def papier(p):
    """p : (..., 3) points du papier en repère local. Renvoie (rgb, émissif rgb) en float 0-255."""
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    rh = np.hypot(x, z)
    phi = np.degrees(np.arctan2(x, -z))
    lat = np.degrees(np.arctan2(y / RV, rh / RH))
    rel = np.mod(phi, DLON)
    dcote = np.minimum(rel, DLON - rel)                       # degrés jusqu'à la côte la plus proche
    dc_px = np.radians(dcote) * rh
    dcentre = np.abs(rel - DLON / 2) / (DLON / 2)               # 0 au milieu du fuseau, 1 sur la côte

    # fond : blanc en haut, crème en bas, lueur chaude au centre de chaque fuseau (bougie)
    c = lerp(C_PAPIER, C_BAS, smv(-lat, -10, 50)[..., None])
    g = np.exp(-((lat + 6) / 26.0) ** 2) * (0.55 + 0.45 * np.cos(np.pi * dcentre / 2) ** 2)
    c = lerp(c, C_CHAUD, (0.30 * g)[..., None])
    # ombre de recouvrement sous les cerclages
    c = lerp(c, C_OMBRE, (0.75 * smv(np.abs(lat), 46, 63))[..., None])

    # visage (vue de face orthographique), ne compte que sur l'avant
    avant = z < -0.8
    fx, fy = x, y
    zone = avant & ((np.abs(fx) / 0.62) ** 2 + ((fy - 0.25) / 1.15) ** 2 < 1)
    # côtes verticales (bambou) : bande sombre, coeur plus clair ; effacées au milieu du visage
    k_cote = (dc_px < 0.13) & ~zone
    k_bord = (dc_px >= 0.13) & (dc_px < 0.36) & ~zone
    c = lerp(c, c * 0.93, k_bord[..., None] * (1 - (dc_px - 0.13) / 0.23)[..., None])
    c = np.where(k_cote[..., None], lerp(C_COTE, C_COTE_H, np.clip(1 - dc_px / 0.07, 0, 1)[..., None]), c)
    # fils horizontaux discrets
    for l0 in (-32.0, 32.0):
        dl = np.abs(lat - l0) * math.pi / 180 * RV
        c = np.where(((dl < 0.06) & ~zone & ~k_cote)[..., None], C_FIL, c)

    # bougie qui se devine sur les côtés et au dos : flamme en goutte + halo
    flam = np.zeros(x.shape, np.float32)
    flam_c = np.zeros(x.shape, np.float32)
    for f0 in FLAMMES:
        dphi = (phi - f0 + 180) % 360 - 180
        dx = np.radians(dphi) * rh
        dy = y + 0.15
        wy = 0.40 * (1 - 0.55 * np.clip(dy / 0.8, 0, 1))
        q = np.sqrt((dx / np.maximum(wy, 0.05)) ** 2 + (dy / np.where(dy > 0, 0.85, 0.42)) ** 2)
        halo = np.exp(-(dx ** 2 + (dy * 0.8) ** 2) / 0.9)
        flam = np.maximum(flam, halo)
        flam_c = np.maximum(flam_c, (q < 1).astype(np.float32))
    c = lerp(c, C_FLAMME, (0.32 * flam)[..., None])
    c = np.where(flam_c[..., None] > 0, lerp(C_FLAMME, C_FLAMME_C, 0.55), c)

    # traits du visage
    d_joue = ((np.abs(fx) - 1.72) / 0.48) ** 2 + ((fy + 0.05) / 0.30) ** 2
    joue = avant & (d_joue < 1)
    c = np.where(joue[..., None], lerp(C_ROSE, C_ROSE_C, np.clip(d_joue - 0.35, 0, 1)[..., None]), c)
    # yeux fermés « ‿ » (visibles quand les yeux ouverts rentrent : clignement, sommeil)
    ferme = np.zeros(x.shape, bool)
    for s in (-1, 1):
        arc = [(s * EYE_X + 0.38 * math.cos(a), EYE_Y + 0.12 - 0.30 * math.sin(a)) for a in np.linspace(0.15, math.pi - 0.15, 9)]
        ferme |= avant & (seg_dist(fx, fy, arc) < 0.085)
    bouche = avant & (seg_dist(fx, fy, MOUTH) < 0.07)
    nez = avant & ((fx / 0.17) ** 2 + ((fy - 0.0) / 0.11) ** 2 < 1)
    c = np.where((ferme | bouche)[..., None], np.where(ferme[..., None], C_YEUX, C_BOUCHE), c)
    c = np.where(nez[..., None], C_NEZ, c)

    # calque _e : fond additif très sombre, coeur des fuseaux un peu plus chaud, liserés fins le long des côtes, flamme = point focal
    e = 0.03 + 0.20 * g * (1 - smv(np.abs(lat), 40, 60))
    e = np.where(k_bord & (dc_px < 0.19), 0.22, e)
    e = np.maximum(e, 0.30 * flam * (1 - smv(np.abs(lat), 30, 50)))
    e = np.where(flam_c > 0, 0.85, e)
    e = np.where(k_cote | ferme | bouche | nez, 0.0, e)
    e = np.where(joue, 0.10, e)
    e = np.where(np.abs(lat) > 60, 0.0, e)
    ergb = E_CHAUD * e[..., None]
    ergb = np.where((flam_c > 0)[..., None], np.array((255, 178, 86), np.float32) * 0.82, ergb)
    ergb = np.where(joue[..., None], np.array((90, 30, 40), np.float32) * 0.5, ergb)
    return c, ergb


# ------------------------------------------------------------------ géométrie du papier : facettes
FACETS = []      # dict(name, c (centre du cube), X, Y, w, h, poly (coord. plaque), cout (centre de la face extérieure))

for j in range(len(LATS) - 1):
    for k in range(NLON):
        p0, p1 = k * DLON, (k + 1) * DLON
        l0, l1 = LATS[j], LATS[j + 1]
        v = [P(p0, l0), P(p1, l0), P(p1, l1), P(p0, l1)]
        X = unit(v[1] - v[0])
        mid_b, mid_t = (v[0] + v[1]) / 2, (v[2] + v[3]) / 2
        Y = mid_t - mid_b
        Y = unit(Y - (Y @ X) * X)
        n = np.cross(X, Y)
        cen = sum(v) / 4
        if n @ cen < 0:
            X = -X
            n = -n
        pts = [((q - cen) @ X, (q - cen) @ Y) for q in v]
        xs, ys = [a for a, _ in pts], [b for _, b in pts]
        bx, by = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        cout = cen + X * bx + Y * by
        w, h = max(xs) - min(xs) + 0.08, max(ys) - min(ys) + 0.08
        poly = [(a - bx, b - by) for a, b in pts]
        FACETS.append(dict(name=f"pap_{j}_{k}", cout=cout, c=cout - n * TH / 2, X=X, Y=Y, n=n, w=w, h=h, poly=poly, band=j, gore=k))


def facet_at(phi, lat):
    j = max(i for i in range(4) if LATS[i] <= lat)
    k = int(phi // DLON) % NLON
    return next(f for f in FACETS if f["band"] == j and f["gore"] == k)


# ------------------------------------------------------------------ peintres de tuiles (renvoient RGBA, RGBA du calque _e)
def finish(rgb_ss, mask_ss, e_ss, W, H):
    rgb = np.array(Image.fromarray(np.clip(rgb_ss, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray((mask_ss * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    if al.any():
        out[~al, :3] = rgb[al].mean(axis=0).astype(np.uint8)
    oe = np.zeros((H, W, 4), np.uint8)
    if e_ss is not None:
        ergb = np.array(Image.fromarray(np.clip(e_ss, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
        on = al & (ergb.max(axis=2) > 2)
        oe[on, :3] = ergb[on]
        oe[on, 3] = 255
    return out, oe


def grid(W, H, w, h):
    """Coordonnées plaque (x vers la droite de l'image, y vers le haut) des texels sur-échantillonnés."""
    gx = ((np.arange(W * SS) + 0.5) / (W * SS) - 0.5) * w
    gy = (0.5 - (np.arange(H * SS) + 0.5) / (H * SS)) * h
    return np.meshgrid(gx, gy)


def poly_mask(px, py, poly, grow=0.0, rond=0.0, W=1, H=1, w=1.0):
    d = W * SS / w
    m = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(m).polygon([((a + w / 2) * d, (H * SS / 2) - b * d) for a, b in poly], fill=255)
    if grow > 0:
        m = m.filter(ImageFilter.MaxFilter(2 * max(1, int(round(grow * d))) + 1))
    if rond:
        m = Image.fromarray(((np.array(m.filter(ImageFilter.GaussianBlur(rond * d)), np.float32) > 127) * 255).astype(np.uint8))
    return np.array(m, np.float32) / 255


def paint_facet(f):
    def painter(W, H):
        px, py = grid(W, H, f["w"], f["h"])
        pts = f["cout"][None, None, :] + f["X"][None, None, :] * px[..., None] + f["Y"][None, None, :] * py[..., None]
        rgb, e = papier(pts)
        m = poly_mask(px, py, f["poly"], grow=0.03, W=W, H=H, w=f["w"])
        return finish(rgb, m, e, W, H)
    return painter


def paint_eye(W, H):
    px, py = grid(W, H, EYE_W, EYE_H)
    q = (px / (EYE_W / 2)) ** 2 + (py / (EYE_H / 2)) ** 2
    m = (q < 1).astype(np.float32)
    c = np.zeros(px.shape + (3,), np.float32)
    c[...] = C_YEUX
    c = lerp(c, np.array((118, 74, 96), np.float32), (smv(-py, 0.0, 0.55) * 0.75)[..., None])      # reflet bas, chaud
    c = lerp(c, np.array((30, 18, 26), np.float32), smv(q, 0.72, 1.0)[..., None])
    h1 = ((px + 0.20) / 0.20) ** 2 + ((py - 0.25) / 0.22) ** 2 < 1
    h2 = ((px - 0.22) / 0.10) ** 2 + ((py + 0.22) / 0.10) ** 2 < 1
    c = np.where((h1 | h2)[..., None], np.array((255, 255, 255), np.float32), c)
    e = np.zeros_like(c)
    e = np.where(h1[..., None], np.array((150, 140, 128), np.float32), e)
    return finish(c, m, e, W, H)


EAR_W, EAR_H, EAR_Y0 = 1.8, 2.0, -0.4      # plaque d'oreille : base enterrée sous la surface (y < 0)
EAR_POLY = [(-0.9, -0.4), (0.9, -0.4), (0.13, 1.56), (-0.13, 1.56)]


def paint_ear(face):
    def painter(W, H):
        px, py = grid(W, H, EAR_W, EAR_H)
        py = py + (EAR_Y0 + EAR_H / 2)                 # y = 0 à la base visible
        poly = [(a, b - (EAR_Y0 + EAR_H / 2)) for a, b in EAR_POLY]
        m = poly_mask(px, py, poly, rond=0.22, W=W, H=H, w=EAR_W)
        bord = 1 - np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.09 * W * SS / EAR_W)), np.float32) / 255 * 1.0
        c = np.zeros(px.shape + (3,), np.float32)
        c[...] = C_PAPIER
        c = lerp(c, C_BAS, smv(-py, -1.4, 0.2)[..., None] * 0.6)
        if face:
            inner = poly_mask(px, py, [(-0.55, -0.1), (0.55, -0.1), (0.07, 1.12), (-0.07, 1.12)], rond=0.18, W=W, H=H, w=EAR_W)
            c = lerp(c, C_ROSE_C, inner[..., None])
            c = lerp(c, C_ROSE, (inner * smv(-py, -0.9, 0.1))[..., None] * 0.7)
        c = lerp(c, C_COTE, np.clip(bord * 3.0, 0, 1)[..., None] * (m[..., None] > 0))
        c = lerp(c, C_OMBRE, smv(-py, -0.25, 0.25)[..., None] * 0.8)      # ombre à la racine
        e = np.zeros_like(c)
        return finish(c, m, e, W, H)
    return painter


def strip(W, H, fn):
    """Bande : u = 0..1 sur la longueur, v = 0..1 sur la largeur. fn(u, v) -> (rgb, e)."""
    u, v = np.meshgrid((np.arange(W * SS) + 0.5) / (W * SS), (np.arange(H * SS) + 0.5) / (H * SS))
    c, e = fn(u, v)
    return finish(c, np.ones(u.shape, np.float32), e, W, H)


def bois(u, v):
    q = np.abs(v - 0.5) * 2
    c = lerp(np.array((236, 206, 146), np.float32), np.array((196, 156, 98), np.float32), (q ** 1.6)[..., None])
    c = c * (1 + 0.05 * np.sin(u * 60 + np.sin(u * 13) * 2))[..., None]
    c = np.where((np.abs(v - 0.5) < 0.07)[..., None], np.array((246, 160, 178), np.float32), c)       # fil rose noué autour
    return c, None


def bois_disque(u, v):
    r = np.hypot(u - 0.5, v - 0.5) * 2
    c = lerp(np.array((238, 210, 152), np.float32), np.array((200, 160, 102), np.float32), smv(r, 0.5, 1.2)[..., None])
    c = c * (1 + 0.04 * np.sin(r * 40))[..., None]
    c = np.where((r < 0.42)[..., None], np.array((120, 82, 50), np.float32), c)
    c = np.where((r < 0.30)[..., None], np.array((255, 214, 150), np.float32), c)           # lumière qui monte par l'ouverture
    e = np.where((r < 0.30)[..., None], E_CHAUD * 0.45, 0.0 * c)
    return c, e


def cordon(u, v):
    q = np.abs(v - 0.5) * 2
    c = lerp(np.array((250, 172, 190), np.float32), np.array((206, 104, 132), np.float32), (q ** 1.4)[..., None])
    c = c * (1 - 0.10 * (np.sin((u * 14 + v * 1.2) * TAU) > 0.4))[..., None]                    # torsade
    return c, None


def queue_bande(u, v):
    q = np.abs(v - 0.5) * 2
    c = lerp(C_PAPIER, np.array((222, 206, 182), np.float32), (q ** 1.5)[..., None])
    c = lerp(c, lerp(np.array((250, 228, 206), np.float32), np.array((222, 190, 160), np.float32), (q ** 1.5)[..., None]), smv(u, 0.25, 0.7)[..., None])
    c = lerp(c, lerp(C_ROSE_C, C_ROSE, (q ** 1.2)[..., None]), smv(u, 0.78, 0.86)[..., None])
    return c, None


def ame(u, v):
    c = np.zeros(u.shape + (3,), np.float32)
    c[...] = (255, 214, 146)
    c = c * (1 - 0.06 * np.abs(v - 0.5))[..., None]
    return c, E_CHAUD * 0.40 + 0 * c


def paint_disque(rgb0, rgb1, e=None):
    """Disque duveteux (pompon, bout de queue, perle)."""
    def painter(W, H):
        px, py = grid(W, H, 1.0, 1.0)
        r = np.hypot(px, py) * 2
        ang = np.arctan2(py, px)
        m = (r < 0.94 + 0.05 * np.sin(ang * 9)).astype(np.float32)
        c = lerp(np.array(rgb0, np.float32), np.array(rgb1, np.float32), smv(r, 0.2, 1.0)[..., None])
        c = lerp(c, c * 1.08, smv(py, 0.0, 0.5)[..., None])
        return finish(c, m, None if e is None else np.broadcast_to(np.array(e, np.float32), c.shape).copy(), W, H)
    return painter


# ------------------------------------------------------------------ atlas
TILES = {}      # nom -> (w_px_modèle, h_px_modèle, peintre) ou (W, H fixes, peintre, True)


def tile(name, w, h, painter, fixed=False):
    TILES[name] = (w, h, painter, fixed)


for f in FACETS:
    tile(f["name"], f["w"], f["h"], paint_facet(f))
tile("oeil", EYE_W, EYE_H, paint_eye)
tile("oreille_av", EAR_W, EAR_H, paint_ear(True))
tile("oreille_ar", EAR_W, EAR_H, paint_ear(False))
tile("bois", 96, 18, lambda W, H: strip(W, H, bois), fixed=True)
tile("bois_disque", 40, 40, lambda W, H: strip(W, H, bois_disque), fixed=True)
tile("cordon", 48, 10, lambda W, H: strip(W, H, cordon), fixed=True)
tile("queue", 96, 16, lambda W, H: strip(W, H, queue_bande), fixed=True)
tile("ame", 16, 16, lambda W, H: strip(W, H, ame), fixed=True)
tile("pompon", 30, 30, paint_disque((255, 196, 210), (232, 120, 150)), fixed=True)
tile("bout", 24, 24, paint_disque((252, 200, 214), (236, 136, 162)), fixed=True)
tile("perle", 20, 20, paint_disque((255, 214, 224), (222, 104, 136)), fixed=True)
tile("rose_ame", 12, 12, lambda W, H: strip(W, H, lambda u, v: (np.array((238, 140, 166), np.float32) + 0 * u[..., None], None)), fixed=True)
tile("oreille_ame", 12, 12, lambda W, H: strip(W, H, lambda u, v: (lerp(C_BAS, C_OMBRE, 0.35) + 0 * u[..., None], None)), fixed=True)

UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def atlas():
    def pack(dens):
        items = []
        for n, (w, h, _, fx) in TILES.items():
            items.append((n, w, h) if fx else (n, int(math.ceil(w * dens)), int(math.ceil(h * dens))))
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

    dens = 48.0
    while (uv := pack(dens)) is None:
        dens -= 0.5
    UV.update(uv)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, (w, h, painter, fx) in TILES.items():
        u0, v0, u1, v1 = UV[n]
        im, ie = painter(u1 - u0, v1 - v0)
        tex[v0:v1, u0:u1] = im
        tex_e[v0:v1, u0:u1] = ie
    assert tex[TEX - 3, TEX - 3, 3] == 0
    tex[..., :3] &= 0xFE
    assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
    b64 = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        b64.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return dens, b64


DENS, (tex_b64, tex_e_b64) = atlas()

# ------------------------------------------------------------------ cubes et groupes
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx (ordre du mod et du renderer)."""
    sy = -R[2, 0]
    if abs(sy) > 0.99999:                      # blocage de cardan (axe X local sur ±Z) : rz = 0, tout passe dans rx
        ry = math.copysign(math.pi / 2, sy)
        ang = (math.degrees(math.atan2(R[0, 1], R[0, 2])) if sy > 0 else math.degrees(math.atan2(-R[0, 1], -R[0, 2]))), math.degrees(ry), 0.0
    else:
        ang = math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(math.asin(sy)), math.degrees(math.atan2(R[1, 0], R[0, 0]))
    assert np.allclose(rot_matrix(*ang), R, atol=1e-4), "euler : reconstruction fausse"
    return ang


def rot_matrix(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


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


def L(p):
    """Repère local de la lanterne -> coordonnées du modèle (avant la rotation de base du groupe lanterne)."""
    return C0 + np.asarray(p, float)


def plate(g, name, c, X, Y, tilename, w, h, th=TH, side="s"):
    """Plaque fine : contour par l'alpha, tranches transparentes. side : 's' face extérieure (X x Y) seule, 'n' face intérieure seule, 'b' les deux."""
    X = unit(X)
    Y = unit(np.asarray(Y, float) - (np.asarray(Y, float) @ X) * X)
    u0, v0, u1, v1 = UV[tilename]
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = L(c)
    south = [u0, v0, u1, v1] if side in "sb" else CLEAR
    north = [u1, v0, u0, v1] if side in "nb" else CLEAR
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
         {"south": south, "north": north, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def frame_from_axis(X):
    ref = V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0)
    Y = unit(ref - (ref @ X) * X)
    return Y, np.cross(X, Y)


def bar(g, name, p, q, r, tilename, u0=0.0, u1=1.0, octo=True, ov=0.08):
    """Tronçon : section octogonale (deux cubes à 45°) ou losange seul. p, q en repère local."""
    p, q = L(p), L(q)
    Ln = np.linalg.norm(q - p)
    X = unit(q - p)
    Y, Z_ = frame_from_axis(X)
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R0 = np.column_stack([X, Y, Z_])
    R45 = np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])
    bu0, bv0, bu1, bv1 = UV[tilename]
    ua = lerp(bu0, bu1, u0)
    ub = max(lerp(bu0, bu1, u1), ua + 2)
    lg = [ua, bv0, ub, bv1]
    mid = (bv0 + bv1) / 2
    end = [ub - 2, mid - 2, ub, mid + 2]
    faces = {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end}
    if octo:
        cube(g, name, p + (-ov, -r, -r), p + (Ln + ov, r, r), p, euler(R0), faces)
        cube(g, name + "o", p + (-ov + 0.03, -r * 0.97, -r * 0.97), p + (Ln + ov - 0.03, r * 0.97, r * 0.97), p, euler(R45), faces)
    else:
        cube(g, name, p + (-ov, -r, -r), p + (Ln + ov, r, r), p, euler(R45), faces)


def prisme(g, name, y0, y1, a, side_tile, top_tile=None, bot_tile=None):
    """Prisme octogonal vertical (deux cubes à 45° autour de Y), centré sur l'axe de la lanterne."""
    s = UV[side_tile]
    for i, (k, ang) in enumerate(((1.0, 0.0), (0.97, 45.0))):
        d = 0.03 * i
        faces = {f: list(s) for f in ("north", "south", "east", "west")}
        faces["up"] = list(UV[top_tile]) if top_tile else list(s)
        faces["down"] = list(UV[bot_tile]) if bot_tile else list(s)
        c = L(V(0, (y0 + y1) / 2, 0))
        cube(g, f"{name}{'o' if i else ''}", L(V(-a * k, y0 + d, -a * k)), L(V(a * k, y1 - d, a * k)), c, (0, ang, 0), faces)


def boule(g, name, c, dia, tilename, core_tile=None):
    """Petite boule : trois disques croisés découpés par l'alpha + âme pleine."""
    c = np.asarray(c, float)
    for tag, X, Y in (("a", V(1, 0, 0), V(0, 1, 0)), ("b", V(0, 0, 1), V(0, 1, 0)), ("c", V(1, 0, 0), V(0, 0, 1))):
        plate(g, f"{name}_{tag}", c, X, Y, tilename, dia, dia, th=0.3, side="b")
    if core_tile:
        a = dia * 0.27
        cube(g, f"{name}_ame", L(c - a), L(c + a), L(c), (0, 0, 0), {f: list(UV[core_tile]) for f in ("north", "south", "east", "west", "up", "down")})


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


Y_ANSE = 4.3
g_elan = group("fam_elan", [0, 24, 0])
g_pos = group("fam_pos", C0, parent=g_elan)
g_sw = group("fam_swing", L(V(0, Y_ANSE, 0)), parent=g_pos)
g_snap = group("fam_snap", C0, parent=g_sw)
g_lan = group("lanterne", C0, parent=g_snap, rotation=(0, YAW, 0))

# papier
for f in FACETS:
    plate(g_lan, f["name"], f["c"], f["X"], f["Y"], f["name"], f["w"], f["h"])

# âme : trois prismes ambrés, toujours en retrait des facettes
def ame_max(y0, y1, marge=0.06):
    """Plus grande demi-largeur d'un prisme octogonal [y0, y1] dont tous les coins restent marge px sous les facettes."""
    def ok(a):
        for ang in (0.0, 45.0):
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            for sx in (-a, a):
                for sz in (-a, a):
                    for yy in (y0, y1):
                        q = V(sx * ca + sz * sa, yy, -sx * sa + sz * ca)
                        if max(f["n"] @ q - f["n"] @ f["cout"] for f in FACETS) > -marge:
                            return False
        return True
    a = 0.2
    while ok(a + 0.02):
        a += 0.02
    return a


prisme(g_lan, "ame_m", -0.95, 0.95, ame_max(-0.95, 0.95), "ame")
prisme(g_lan, "ame_h", 0.85, 1.95, ame_max(0.85, 1.95), "ame")
prisme(g_lan, "ame_b", -1.95, -0.85, ame_max(-1.95, -0.85), "ame")

# cerclages en bambou
Y_TOP = RV * math.sin(math.radians(64))
prisme(g_lan, "cercle_h", Y_TOP - 0.3, Y_TOP + 0.42, 1.6, "bois", top_tile="bois_disque", bot_tile="bois")
prisme(g_lan, "cercle_b", -Y_TOP - 0.42, -Y_TOP + 0.3, 1.6, "bois", top_tile="bois", bot_tile="bois_disque")

# anse en cordelette, perle au sommet
YT = Y_TOP + 0.38
ANSE = [V(-0.8, YT, 0), V(-0.6, YT + 0.85, 0), V(0, Y_ANSE - 0.05, 0), V(0.6, YT + 0.85, 0), V(0.8, YT, 0)]
for i in range(4):
    bar(g_lan, f"anse{i}", ANSE[i], ANSE[i + 1], 0.16, "cordon", i / 4, (i + 1) / 4, octo=False, ov=0.06)
boule(g_lan, "perle", V(0, Y_ANSE, 0), 0.62, "perle")

# yeux ouverts : une plaque par fuseau avant, parallèle à la facette, 0,06 px au-dessus
g_yeux = group("yeux", C0, parent=g_lan)
for s, tag in ((-1, "l"), (1, "r")):
    f = facet_at(18.0 if s > 0 else 342.0, 10.0)
    n = f["n"]
    # point de la facette qui se projette de face en (s*EYE_X, EYE_Y)
    x0, y0 = s * EYE_X, EYE_Y
    d0 = n @ f["cout"]
    zf = (d0 - n[0] * x0 - n[1] * y0) / n[2]
    ctr = V(x0, y0, zf) + n * (0.06 + TH / 2)
    up = V(0, 1, 0)
    Yp = unit(up - (up @ n) * n)
    Xp = np.cross(Yp, n)
    plate(g_yeux, f"oeil_{tag}", ctr, Xp, Yp, "oeil", EYE_W, EYE_H)

# oreilles : deux peaux (avant rose, arrière crème) autour d'une âme pleine plus étroite
EARS = {}
for s, tag in ((-1, "l"), (1, "r")):
    b = P(s * 40.0, 50.0, 0.93)
    Yu = unit(V(s * 0.55, 1.0, 0.12))
    n0 = unit(V(s * 0.42, 0.0, -1.0))
    Xe = unit(np.cross(Yu, n0))
    ne = np.cross(Xe, Yu)
    g_e = group(f"oreille_{tag}", L(b), parent=g_lan)
    EARS[tag] = g_e
    cy = EAR_Y0 + EAR_H / 2
    plate(g_e, f"oreille_{tag}_av", b + Yu * cy + ne * 0.17, Xe, Yu, "oreille_av", EAR_W, EAR_H, side="s")
    plate(g_e, f"oreille_{tag}_ar", b + Yu * cy - ne * 0.17, Xe, Yu, "oreille_ar", EAR_W, EAR_H, side="n")
    R_ = np.column_stack([Xe, Yu, ne])
    for i, (wc, y0c, y1c) in enumerate(((0.86, -0.3, 0.62), (0.40, 0.55, 1.06))):
        cc = b + Yu * ((y0c + y1c) / 2)
        hw, hh = wc / 2, (y1c - y0c) / 2
        cube(g_e, f"oreille_{tag}_ame{i}", L(cc) - (hw, hh, 0.15), L(cc) + (hw, hh, 0.15), L(cc), euler(R_),
             {f_: list(UV["oreille_ame"]) for f_ in ("north", "south", "east", "west", "up", "down")})

# queue en crochet, au dos (+Z), qui remonte et se recourbe vers l'avant
Q0 = V(0, -1.2, 2.45)
NQ, LQ = 6, 3.5
QP = [Q0]
for i in range(NQ):
    s_ = (i + 0.5) / NQ
    a = math.radians(-14 + 178 * s_ ** 1.35)        # cap dans le plan YZ : 0 = vers l'arrière, 90 = vers le haut, > 90 = se recourbe vers l'avant
    QP.append(QP[-1] + V(0, math.sin(a), math.cos(a)) * (LQ / NQ))
g_q1 = group("queue1", L(QP[0]), parent=g_lan)
g_q2 = group("queue2", L(QP[2]), parent=g_q1)
g_q3 = group("queue3", L(QP[4]), parent=g_q2)
for i in range(NQ):
    bar((g_q1, g_q1, g_q2, g_q2, g_q3, g_q3)[i], f"queue_s{i}", QP[i], QP[i + 1], lerp(0.36, 0.27, i / (NQ - 1)), "queue", i / NQ, (i + 1) / NQ, octo=True, ov=0.1)
boule(g_q3, "queue_bout", QP[-1] + unit(QP[-1] - QP[-2]) * 0.12, 0.9, "bout", core_tile="rose_ame")

# pompon sous la lanterne
g_pom = group("pompon", L(V(0, -Y_TOP - 0.42, 0)), parent=g_lan)
bar(g_pom, "pompon_fil", V(0, -Y_TOP - 0.3, 0), V(0, -Y_TOP - 1.25, 0), 0.15, "cordon", 0.0, 0.5, octo=False)
boule(g_pom, "pompon", V(0, -Y_TOP - 1.65, 0), 1.0, "pompon", core_tile="rose_ame")

outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone_node(g_elan)]}]


# ------------------------------------------------------------------ animations
# Guide, section 3 : +X = le haut part vers l'arrière ; +Y = le côté droit (+X) avance ; +Z = le côté droit monte.
# Position +Y : monte ; +X : droite du joueur. La position d'un groupe est exprimée dans le repère de son parent.
def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 3)), "y": str(round(v[1] + 0.0, 3)), "z": str(round(v[2] + 0.0, 3))}], "time": round(t, 3), "interpolation": "linear"}


def anim(name, length, tracks, n_kf=None, loop="loop"):
    n = n_kf or max(8, int(round(length * 10)))
    times = [i * length / n for i in range(n + 1)]
    A = {groups[g]["uuid"]: {"name": g, "type": "bone", "keyframes": [kf(ch, t, f(t)) for ch, f in chans.items() for t in times]} for g, chans in tracks.items()}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


def S(T, k, ph=0.0):
    return lambda t: math.sin(TAU * k * t / T + ph)


def ear_rot(side, tx, tz):
    """Intention écrite pour l'oreille droite (+X) : tz > 0 = la pointe part vers l'extérieur ; le signe Z est centralisé ici."""
    return (tx, 0.0, -side * tz)


def flick(t, a, amp=1.0):
    return amp * (bump(t, a, a + 0.07, a + 0.12, a + 0.22) - 0.35 * bump(t, a + 0.18, a + 0.24, a + 0.26, a + 0.36))


def etat(name, T, pos, swing, regard=None, ears=None, eyes=None, tail=None, pompon=None, n_kf=None):
    """pos(t), swing(t) : position de fam_pos et rotation du balancement. ears(t) -> (tx, tz, tx_l_extra, tz_l_extra...)."""
    tr = {g_pos: {"position": pos}, g_sw: {"rotation": swing}}
    if regard:
        tr[g_lan] = {"rotation": regard}
    if ears:
        tr[EARS["l"]] = {"rotation": lambda t: ear_rot(-1, *ears(t, -1))}
        tr[EARS["r"]] = {"rotation": lambda t: ear_rot(1, *ears(t, 1))}
    if eyes:
        tr[g_yeux] = {"position": lambda t: (0, 0, eyes(t))}
    if tail:
        base, amp_y, amp_x, cyc, lag = tail
        for i, g in enumerate((g_q1, g_q2, g_q3)):
            def f(t, i=i):
                ph = TAU * (cyc * t / T - lag * i)
                w = (0.7, 1.0, 1.25)[i]
                return (base[i] + amp_x * w * math.sin(ph + 1.2), amp_y * w * math.sin(ph), 0)
            tr[g] = {"rotation": f}
    if pompon:
        tr[g_pom] = {"rotation": pompon}
    return anim(name, T, tr, n_kf=n_kf)


PUSH = 0.9      # recul des yeux ouverts derrière le papier (laisse voir les yeux fermés peints)


def blink(t, *ts):
    return PUSH * sum(bump(t, a, a + 0.05, a + 0.13, a + 0.2) for a in ts)


# idle (8 s) : flottement (4 s), balancement de lanterne, coup d'oeil vers le joueur, oreilles qui tressaillent, clignements
TI = 8.0
idle = etat("idle", TI,
            lambda t: (0.25 * math.sin(TAU * t / TI), 0.6 * S(TI, 2)(t) + 0.2 * S(TI, 1, 1.0)(t), 0),
            lambda t: (2.5 * S(TI, 3, 0.4)(t), 0, 5.0 * S(TI, 2, 0.9)(t)),
            regard=lambda t: (0, -32 * bump(t, 3.0, 3.5, 4.6, 5.1), 9 * bump(t, 3.2, 3.6, 4.5, 4.9)),
            ears=lambda t, s: (3 * S(TI, 2)(t), 4 + (14 * flick(t, 1.6) if s < 0 else 14 * flick(t, 5.8) + 10 * flick(t, 6.3))),
            eyes=lambda t: blink(t, 2.3, 6.9),
            tail=([-6, -4, -4], 14, 6, 2, 0.12),
            pompon=lambda t: (-3.0 * S(TI, 3, -0.6)(t), 0, -5.0 * S(TI, 2, 0.1)(t)),
            n_kf=96)

TW = 1.6
walk = etat("walk", TW,
            lambda t: (0.3 * S(TW, 1)(t), 0.45 * S(TW, 2, 0.5)(t), 1.5),
            lambda t: (-6 + 3 * S(TW, 2)(t), 0, 4 * S(TW, 1, 0.6)(t)),
            ears=lambda t, s: (8 + 3 * S(TW, 2, 0.8)(t), 6),
            tail=([4, -2, -4], 16, 6, 1, 0.14),
            pompon=lambda t: (8 - 4 * S(TW, 2, -0.8)(t), 0, -5 * S(TW, 1, -0.4)(t)),
            n_kf=16)

TR = 1.0
run = etat("run", TR,
           lambda t: (0.3 * S(TR, 1)(t), -0.4 + 0.5 * S(TR, 2, 0.5)(t), 3.6),
           lambda t: (-16 + 3.5 * S(TR, 2)(t), 0, 5 * S(TR, 1, 0.6)(t)),
           ears=lambda t, s: (24 + 3 * S(TR, 2, 0.8)(t), 10),
           tail=([12, 16, 22], 10, 5, 1, 0.14),
           pompon=lambda t: (22 - 4 * S(TR, 2, -0.8)(t), 0, -6 * S(TR, 1, -0.4)(t)),
           n_kf=12)

TS = 3.0
sneak = etat("sneak", TS,
             lambda t: (1.6 + 0.15 * S(TS, 1)(t), -4.2 + 0.35 * S(TS, 1, 0.5)(t), 1.2),
             lambda t: (-5 + 1.5 * S(TS, 1)(t), 0, 2.5 * S(TS, 1, 1.0)(t)),
             regard=lambda t: (0, -14, 6),
             ears=lambda t, s: (6, 26 + 3 * S(TS, 1)(t)),
             eyes=lambda t: blink(t, 1.9),
             tail=([-14, -12, -10], 8, 4, 1, 0.12),
             pompon=lambda t: (4 - 2 * S(TS, 1, -0.8)(t), 0, -3 * S(TS, 1, 0.2)(t)),
             n_kf=24)

TF = 2.4
fly = etat("fly", TF,
           lambda t: (0.2 * S(TF, 1)(t), 1.4 + 0.9 * S(TF, 1)(t), 1.5),
           lambda t: (-8 + 5 * S(TF, 1, -1.2)(t), 0, 6 * S(TF, 1, 0.3)(t)),
           ears=lambda t, s: (-4 + 6 * S(TF, 1, -0.6)(t), 2 + 5 * S(TF, 2)(t)),
           tail=([6, 4, 6], 18, 10, 1, 0.14),
           pompon=lambda t: (10 - 6 * S(TF, 1, -2.0)(t), 0, -7 * S(TF, 1, -0.6)(t)),
           n_kf=24)

# glide et swim : le corps est couché et le familier suit le torse ; +X ~70° remet la lanterne debout dans le monde.
# Position : +Z du torse = vers le haut du monde, -Y du torse = vers l'arrière de la course.
TG = 3.6
glide = etat("glide", TG,
             lambda t: (0, -2.0 + 0.3 * S(TG, 1)(t), 3.5 + 0.5 * S(TG, 1, 0.8)(t)),
             lambda t: (70 + 4 * S(TG, 1)(t), 0, 4 * S(TG, 1, 1.0)(t)),
             ears=lambda t, s: (20, 10),
             tail=([16, 18, 20], 10, 4, 1, 0.12),
             pompon=lambda t: (-10 + 4 * S(TG, 1, -0.8)(t), 0, -4 * S(TG, 1, 0.2)(t)),
             n_kf=24)

TN = 3.2
swim = etat("swim", TN,
            lambda t: (0, -1.0 + 0.5 * S(TN, 1)(t), 3.0 + 0.7 * S(TN, 1, 1.2)(t)),
            lambda t: (62 + 7 * S(TN, 1)(t), 0, 6 * S(TN, 1, 1.4)(t)),
            ears=lambda t, s: (10 + 4 * S(TN, 1)(t), 8),
            tail=([4, 6, 8], 20, 8, 1, 0.16),
            pompon=lambda t: (-6 + 8 * S(TN, 1, -1.0)(t), 0, -6 * S(TN, 1, 0.4)(t)),
            n_kf=24)

TA = 1.2
fall = etat("fall", TA,
            lambda t: (0, 2.0 + 0.3 * S(TA, 1)(t), 0.5),
            lambda t: (5 + 2.5 * S(TA, 1)(t), 0, 3 * S(TA, 1, 0.8)(t)),
            ears=lambda t, s: (-8, 14 + 3 * S(TA, 2)(t)),
            tail=([-22, -10, 0], 8, 4, 1, 0.12),
            pompon=lambda t: (-18 + 4 * S(TA, 1, -0.8)(t), 0, -4 * S(TA, 1, 0.1)(t)),
            n_kf=12)

TZ = 4.0
sleep = etat("sleep", TZ,
             lambda t: (0.6, -1.6 + 0.35 * S(TZ, 1)(t), 0),
             lambda t: (-9 + 1.5 * S(TZ, 1)(t), 0, 3 * S(TZ, 1, 1.2)(t)),
             regard=lambda t: (0, -10, 8 + 2 * S(TZ, 1, 0.5)(t)),
             ears=lambda t, s: (4, 34 + 2 * S(TZ, 1)(t)),
             eyes=lambda t: PUSH,
             tail=([-10, -18, -22], 4, 2, 1, 0.12),
             pompon=lambda t: (8 - 1.5 * S(TZ, 1, -0.8)(t), 0, -3 * S(TZ, 1, 0.2)(t)),
             n_kf=20)

TM = 4.0
mount = etat("mount", TM,
             lambda t: (0, 0.5 + 0.5 * S(TM, 1)(t), 0.5),
             lambda t: (-2 + 2 * S(TM, 1)(t), 0, 4 * S(TM, 1, 0.9)(t)),
             ears=lambda t, s: (2, 6 + 10 * flick(t, 2.4)),
             eyes=lambda t: blink(t, 1.2),
             tail=([-6, -4, -4], 12, 5, 1, 0.12),
             pompon=lambda t: (2 - 2 * S(TM, 1, -0.8)(t), 0, -4 * S(TM, 1, 0.1)(t)),
             n_kf=32)


# attack / hurt : une fois, retour à 0 ; seuls fam_elan, fam_snap et yeux sont animés.
def _el(t):
    return bump(t, 0.05, 0.2, 0.32, 0.72)


attack = anim("attack", 0.8, {
    g_elan: {"position": lambda t: (1.0 * _el(t), 0.6 * _el(t), -4.0 * _el(t))},
    g_snap: {"rotation": lambda t: (-14 * bump(t, 0.05, 0.18, 0.3, 0.7), 0, 8 * bump(t, 0.1, 0.25, 0.35, 0.7))},
}, n_kf=24, loop="once")

hurt = anim("hurt", 0.8, {
    g_elan: {"position": lambda t: (-0.6 * bump(t, 0.0, 0.06, 0.2, 0.6) * math.sin(TAU * t * 7), 1.2 * bump(t, 0.0, 0.08, 0.16, 0.65), 2.6 * bump(t, 0.0, 0.08, 0.16, 0.65))},
    g_snap: {"rotation": lambda t: (16 * bump(t, 0.0, 0.08, 0.16, 0.65), 0, 10 * bump(t, 0.0, 0.05, 0.2, 0.66) * math.sin(TAU * t * 6))},
    g_yeux: {"position": lambda t: (0, 0, PUSH * bump(t, 0.0, 0.04, 0.4, 0.5))},
}, n_kf=24, loop="once")

ANIMS = [idle, walk, run, sneak, fly, glide, swim, fall, sleep, mount, attack, hurt]

assert 60 <= len(elements) <= 140, f"budget : {len(elements)} cubes"
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


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      f"densité {DENS:.1f} texels/px")
