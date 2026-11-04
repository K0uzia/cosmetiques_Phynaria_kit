"""Baguette en sucre d'orge : baguette magique tenue dans la main droite, ensemble « Pâtisserie » (fraise, vanille, chocolat). Design original.
Écrit baguette_sucre_orge.png, baguette_sucre_orge_e.png et .build/baguette_sucre_orge_brut.bbmodel à côté de ce script.

Tige octogonale (deux cubes à 45°) à rayures fraise / vanille et fil rose : chaque face décale la rayure d'un huitième de pas, la spirale se lit tout autour.
Nœud de ruban rose sous le bout : peau découpée par alpha (deux plaques) autour d'âmes pleines, nœud central en volume.
Étoile-bonbon dodue à 5 branches arrondies : deux étages de peau (grande étoile liserée fraise, petite étoile bombée avec visage)
autour d'âmes pleines plus étroites ; le liseré fraise se retrouve sur les flancs des âmes, lisible par la tranche.

Repère local de la baguette : axe de la tige = +X local, plan de l'étoile au repos = XY local. Le groupe `baguette` porte une
rotation de base qui envoie +X local sur la direction de la tige dans la main. Le groupe `etoile` tourne sur l'axe de la tige
(canal x, Molang q.life_time : rotation continue, sans saut entre états).
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # calque _e embarqué en seconde texture (correctif du clignotement annoncé le 2026-11-03, à vérifier en jeu)
NOM = "baguette_sucre_orge"
TEX = 256
TAU = 2 * math.pi

# Prise dans le poing droit (bras x 4..8, bas du bras y = 12)
P0 = np.array((6.0, 11.2, -0.5))
TILT = 55.0         # tige levée au-dessus de l'horizontale, vers l'avant (degrés)
YAW = 10.0          # ouverture vers l'extérieur (degrés)
ROLL = 0.0          # roulis de la baguette sur son axe (réglé plus bas pour que +Z local regarde vers l'avant)
STAR_ROLL = 0.0     # roulis de repos de l'étoile

# Le long de la tige (px, depuis la prise)
S_POM0, S_POM1 = -2.55, -1.85
S_TIGE0, S_TIGE1 = -1.95, 9.9
C_STAR = 11.15
S_NOEUD = 7.05

# Étoile
R_OUT, R_IN, RHO = 2.9, 1.58, 0.66      # rayon des pointes (arrondi compris), rayon des creux du polygone, arrondi
T2 = 0.70                                # échelle de l'étage bombé
DS = 20.0                                # texels par px sur l'étoile
LISERE = 0.28                            # liseré fraise (px) : 5–6 texels


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


# ------------------------------------------------------------------ couleurs (bases poussées vers le blanc : lumière chaude de nuit)
FRAISE = np.array((222, 52, 82), np.float32)
FRAISE_S = np.array((168, 30, 62), np.float32)
VANILLE = np.array((255, 252, 244), np.float32)
VANILLE_S = np.array((226, 218, 214), np.float32)
ROSE = np.array((255, 138, 184), np.float32)
ROSE_S = np.array((214, 84, 140), np.float32)
ROSE_C = np.array((255, 206, 226), np.float32)
JAUNE = np.array((255, 250, 214), np.float32)      # vanille pâle, presque blanc
JAUNE_M = np.array((255, 232, 150), np.float32)
JAUNE_S = np.array((232, 190, 96), np.float32)
CHOCO = np.array((70, 36, 34), np.float32)


def finish(rgb_big, mask_big, W, H):
    rgb = np.array(Image.fromarray(np.clip(rgb_big, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(mask_big.astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    if al.any():
        out[~al, :3] = rgb[al].mean(axis=0).astype(np.uint8)
    return out, al


# ------------------------------------------------------------------ étoile
def star_poly(R0, r0, cx, cy, k):
    """Polygone étoile (pointe vers le haut de l'image), en pixels d'image ; k = pixels par px."""
    pts = []
    for i in range(10):
        a = math.radians(90 + 36 * i)
        rr = R0 if i % 2 == 0 else r0
        pts.append((cx + math.cos(a) * rr * k, cy - math.sin(a) * rr * k))
    return pts


def star_mask(N, k, scale, inset=0.0, grow=0.0):
    """Étoile arrondie (somme de Minkowski polygone ⊕ disque, puis creux adoucis), canevas N×N, centre au milieu."""
    rho = RHO * scale - inset + grow
    R0, r0 = (R_OUT - RHO) * scale, R_IN * scale * 0.86
    m = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(m)
    poly = star_poly(R0, r0, N / 2, N / 2, k)
    d.polygon(poly, fill=255)
    rp = max(rho, 0.02) * k
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        d.line([p, q], fill=255, width=int(round(2 * rp)))
        d.ellipse([p[0] - rp, p[1] - rp, p[0] + rp, p[1] + rp], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(0.22 * k * scale))
    return np.array(m) > 127


def paint_star(scale, kind):
    """kind : 'grand' (étage 1, liseré fraise), 'face' (étage 2 avec visage), 'dos' (étage 2 sans visage). Image : pointe vers le haut."""
    W = int(math.ceil(2 * (R_OUT * scale + 0.08) * DS))
    ss = 4
    N, k = W * ss, DS * ss
    m = star_mask(N, k, scale)
    inner = star_mask(N, k, scale, inset=LISERE)
    yy, xx = np.mgrid[0:N, 0:N]
    X, Y = (xx + 0.5 - N / 2) / k, -(yy + 0.5 - N / 2) / k      # px, Y vers le haut
    h = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").filter(ImageFilter.GaussianBlur(0.55 * k * scale)), np.float32) / 255
    c = np.empty((N, N, 3), np.float32)
    lum = np.clip((h - 0.35) / 0.55, 0, 1)
    c[...] = lerp(JAUNE_S, JAUNE_M, np.clip(lum * 1.6, 0, 1)[..., None])
    c = lerp(c, JAUNE, np.clip(lum * 1.4 - 0.35, 0, 1)[..., None])
    # lumière douce en haut à gauche, ombre en bas à droite (bombé)
    dirl = np.clip((-X * 0.5 + Y * 0.8) / (R_OUT * scale), -1, 1)
    c *= (1 + 0.06 * dirl)[..., None]
    e = np.zeros((N, N, 3), np.float32)
    e[...] = (26, 20, 6)
    if kind == "grand":
        # ombre de recouvrement autour de l'étage bombé
        sh = star_mask(N, k, T2, grow=0.32) & ~star_mask(N, k, T2, grow=-0.02)
        c = lerp(c, JAUNE_S * 0.92, sh[..., None] * 0.75)
        lis = m & ~inner
        c[lis] = FRAISE
        # filet clair dans le liseré, côté lumière : sucre glacé
        lis_in = m & ~star_mask(N, k, scale, inset=LISERE * 0.45)
        c[lis & ~lis_in & (dirl > 0.15)] = lerp(FRAISE, VANILLE, 0.35)
        c[lis_in & (dirl < -0.2)] = FRAISE_S
        e[lis] = (104, 30, 50)
    else:
        rim = m & ~star_mask(N, k, scale, inset=0.12)
        c[rim] = lerp(c[rim], JAUNE_S, 0.6)
    # reflet : arc blanc sur la branche haute gauche
    a = np.arctan2(Y, X)
    rr = np.hypot(X, Y)
    ref = (np.abs(rr - 0.62 * R_OUT * scale) < 0.075 * max(1.0, 1.4 * scale) + 0.04) & (a > math.radians(108)) & (a < math.radians(150)) & inner
    dot = np.hypot(X + 0.70 * R_OUT * scale * math.cos(math.radians(162)) * -1, Y - 0.70 * R_OUT * scale * math.sin(math.radians(162))) < 0.13
    ref |= dot & inner
    c[ref] = (255, 255, 255)
    e[ref] = (150, 140, 92)
    if kind == "face":
        # visage kawaii : yeux 0,26 × 0,38 px (5 × 7 texels), reflet 2 texels, joues roses, petite bouche
        for sx in (-1, 1):
            ex, ey = sx * 0.40, 0.05
            eye = ((X - ex) / 0.13) ** 2 + ((Y - ey) / 0.19) ** 2 < 1
            c[eye] = CHOCO
            e[eye] = 0
            glint = np.hypot(X - (ex - 0.04), Y - (ey + 0.07)) < 0.055
            c[glint] = (255, 255, 255)
            cheek = ((X - sx * 0.70) / 0.17) ** 2 + ((Y + 0.20) / 0.10) ** 2 < 1
            c[cheek] = lerp(c[cheek], ROSE, 0.85)
        mouth = (np.abs(np.hypot(X, Y + 0.08) - 0.17) < 0.055) & (Y < -0.16) & (np.abs(X) < 0.16)
        c[mouth] = CHOCO
        e[mouth] = 0
    elif kind == "dos":
        # petite spirale de sucre au dos
        sp = np.zeros_like(m)
        for t in np.linspace(0, 1, 120):
            px_, py_ = math.cos(t * 2.4 * TAU) * 0.55 * t, math.sin(t * 2.4 * TAU) * 0.55 * t
            sp |= np.hypot(X - px_, Y - py_) < 0.055
        c[sp & inner] = lerp(JAUNE_S, VANILLE, 0.2)
    out, al = finish(c, m, W, W)
    eo_rgb = np.array(Image.fromarray(np.clip(e, 0, 255).astype(np.uint8), "RGB").resize((W, W), Image.NEAREST))
    eo = np.dstack([eo_rgb, al * 255]).astype(np.uint8)
    eo[~al] = 0
    eo[al & (eo_rgb.sum(axis=2) == 0)] = 0
    # image tournée : pointe vers la droite (u croissant = +X local, axe de la tige)
    return np.ascontiguousarray(np.rot90(out, -1)), np.ascontiguousarray(np.rot90(eo, -1)), W / DS


# ------------------------------------------------------------------ ruban
BOW_X0, BOW_X1, BOW_Y0, BOW_Y1 = -2.05, 2.05, -1.75, 0.95     # boîte canonique (px) : x = local Y, y vers la pointe = local X
DB = 18.0


def paint_bow():
    W, H = int(round((BOW_X1 - BOW_X0) * DB)), int(round((BOW_Y1 - BOW_Y0) * DB))
    ss = 4
    k = DB * ss
    yy, xx = np.mgrid[0:H * ss, 0:W * ss]
    X = BOW_X0 + (xx + 0.5) / k
    Y = BOW_Y1 - (yy + 0.5) / k
    m = np.zeros(X.shape, bool)
    fold = np.zeros(X.shape, np.float32)
    for sx in (-1, 1):
        ang = math.radians(14) * sx
        xr, yr = X - sx * 1.05, Y - 0.12
        u = xr * math.cos(ang) + yr * math.sin(ang)
        v = -xr * math.sin(ang) + yr * math.cos(ang)
        loop = (u / 0.92) ** 2 + (v / 0.6) ** 2 < 1
        m |= loop
        fold = np.maximum(fold, loop * np.clip(1 - np.hypot((X - sx * 0.62) / 0.5, (Y - 0.1) / 0.3), 0, 1))
        # pan qui pend, bout arrondi
        t = np.clip((0.0 - Y) / 1.45, 0, 1)
        cxl = sx * (0.18 + 0.42 * t)
        tail = (np.abs(X - cxl) < 0.24) & (Y < 0.0) & (Y > -1.35)
        tail |= np.hypot(X - sx * 0.60, Y + 1.35) < 0.24
        m |= tail
    knot = np.hypot(X / 0.42, Y / 0.48) < 1
    m |= knot
    h = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").filter(ImageFilter.GaussianBlur(0.3 * k)), np.float32) / 255
    c = np.empty(X.shape + (3,), np.float32)
    c[...] = lerp(ROSE_S, ROSE, np.clip((h - 0.3) / 0.5, 0, 1)[..., None])
    c = lerp(c, ROSE_S * 0.9, np.clip(fold * 1.6, 0, 1)[..., None])
    hl = np.zeros(X.shape, bool)
    for sx in (-1, 1):
        hl |= (np.abs(np.hypot((X - sx * 1.15) / 0.62, (Y - 0.2) / 0.36) - 1) < 0.16) & (Y > 0.25)
    c[hl & m] = ROSE_C
    c[knot] = ROSE_S
    out, _ = finish(c, m, W, H)
    return np.ascontiguousarray(np.rot90(out, -1))


# ------------------------------------------------------------------ tige à rayures
DT = 14.0
PAS = 3.0                           # pas de la spirale (px)
L_TIGE = S_TIGE1 - S_TIGE0
P_TEX = int(round(PAS * DT))


def paint_tige(H=8):
    """Rayures en biais : sur une face, la ligne v couvre 45° de tour (du bord +22,5° au bord -22,5°), la rayure s'y décale d'un seizième de pas
    de part et d'autre ; d'une face à l'autre, le décalage d'UV d'un huitième de pas raccorde la spirale."""
    W = int(math.ceil(L_TIGE * DT)) + P_TEX + 4
    a = np.zeros((H, W, 4), np.uint8)
    for x in range(W):
        for y in range(H):
            ph = x + P_TEX / 16 - (y + 0.5) / H * P_TEX / 8
            f = (ph % P_TEX) / P_TEX
            if f < 0.46:
                col = FRAISE
            elif 0.70 <= f < 0.70 + 4.0 / P_TEX:
                col = ROSE
            else:
                col = VANILLE
            q = abs((y + 0.5) / H - 0.5) * 2
            a[y, x, :3] = np.clip(col * (1.0 - 0.07 * q ** 2), 0, 255)
    a[..., 3] = 255
    return a


def paint_plein(col, H=8, W=16, band=None):
    a = np.zeros((H, W, 4), np.uint8)
    for y in range(H):
        q = abs((y + 0.5) / H - 0.5) * 2
        a[y, :, :3] = np.clip(np.array(col) * (1.0 - 0.1 * q ** 2), 0, 255)
    if band is not None:
        a[:, W // 2 - 2:W // 2 + 2, :3] = band
    a[..., 3] = 255
    return a


def paint_etincelle(PT=40):
    """Étincelle à 4 branches arrondies, cœur blanc, contour rose : une seule silhouette."""
    ss = 4
    N = PT * ss
    yy, xx = np.mgrid[0:N, 0:N]
    X, Y = (xx + 0.5 - N / 2) / (N / 2), -(yy + 0.5 - N / 2) / (N / 2)
    f = np.maximum(1 - (np.abs(X) ** 0.6 + np.abs(Y) ** 0.6) ** (1 / 0.6) / 0.95, 0)
    m = Image.fromarray((f > 0) .astype(np.uint8) * 255, "L").filter(ImageFilter.GaussianBlur(N * 0.02))
    m = np.array(m) > 127
    c = np.empty((N, N, 3), np.float32)
    c[...] = lerp(ROSE, JAUNE, np.clip(f * 3.2, 0, 1)[..., None])
    c = lerp(c, np.array((255, 255, 255), np.float32), np.clip((f - 0.45) * 4, 0, 1)[..., None])
    out, _ = finish(c, m, PT, PT)
    return out


UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 2, TEX - 2]


def atlas():
    s1, s1e, w1 = paint_star(1.0, "grand")
    s2f, s2fe, w2 = paint_star(T2, "face")
    s2b, s2be, _ = paint_star(T2, "dos")
    items = [("star1", s1, s1e), ("star2f", s2f, s2fe), ("star2b", s2b, s2be), ("bow", paint_bow(), None), ("tige", paint_tige(), None),
             ("core_star", paint_plein(lerp(FRAISE, VANILLE, 0.12), band=(244, 128, 150)), None), ("ruban", paint_plein(ROSE, band=tuple(ROSE_C.astype(int))), None),
             ("vanille", paint_plein(VANILLE, band=tuple(ROSE.astype(int))), None), ("jaune", paint_plein(JAUNE_M), None),
             ("etincelle", paint_etincelle(), None)]
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, im, ime in sorted(items, key=lambda it: -it[1].shape[0]):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 4, "atlas plein"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None:
            tex_e[y:y + h, x:x + w] = ime
        x += w + 1
        shelf = max(shelf, h)
    assert tex[TEX - 3, TEX - 3, 3] == 0
    assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
    res = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        res.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return res, w1, w2


(tex_b64, tex_e_b64), W_STAR1, W_STAR2 = atlas()

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx, ordre du mod et du renderer."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(float(v), 3) for v in rotation]}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def L(s, y=0.0, z=0.0):
    """Point du repère local de la baguette (avant rotation du groupe) : s le long de la tige."""
    return P0 + V(s, y, z)


def plate(g, name, c, w, h, tile, th=0.3, rz=0.0):
    """Plaque fine dans le plan XY local : contour par l'alpha, tranches transparentes. u suit +X, le haut de l'image est +Y."""
    u0, v0, u1, v1 = UV[tile]
    c = np.asarray(c, float)
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, (0, 0, rz),
         {"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def solid(tile, end=None):
    u0, v0, u1, v1 = UV[tile]
    lg = [u0, v0, u1, v1]
    e = end or [u0 + 1, v0 + 1, u0 + 4, v0 + 4]
    return {"south": lg, "north": [u1, v0, u0, v1], "up": lg, "down": lg, "east": e, "west": e}


def octo_x(g, name, s0, s1, r, tile, spiral=False):
    """Tronçon octogonal le long de +X local : deux cubes, le second tourné de 45° sur l'axe."""
    u0, v0, u1, v1 = UV[tile]
    ends = [u0 + 2, v0 + 2, u0 + 6, v0 + 6] if tile != "tige" else [u0 + int(0.6 * P_TEX), v0 + 1, u0 + int(0.6 * P_TEX) + 4, v0 + 5]
    for j, (rot, rr) in enumerate(((0.0, r), (45.0, r * 0.97))):
        theta = {"south": 0.0, "up": 90.0, "north": 180.0, "down": 270.0}
        faces = {}
        for f, th in theta.items():
            if spiral:
                off = ((th - rot) % 360) / 360 * P_TEX     # Rx(+45) amène +Y vers +Z : l angle de la face diminue
                a0 = u0 + off + (s0 - S_TIGE0) * DT
                a1 = u0 + off + (s1 - S_TIGE0) * DT
                lg = [a0, v0, a1, v1]
            else:
                lg = [u0, v0, u1, v1]
            faces[f] = ([lg[2], lg[3], lg[0], lg[1]] if spiral else [lg[2], lg[1], lg[0], lg[3]]) if f == "north" else lg   # nord : u et v retournés, sens du tour cohérent
        faces["east"] = faces["west"] = ends
        d = 0.02 * j
        cube(g, name + ("o" if j else ""), L(s0 + d, -rr, -rr), L(s1 - d, rr, rr), L(0), (rot, 0, 0), faces)


def box_dir(g, name, p, q, hw, hz, tile, rz_only=True, ov=0.0):
    """Cube allongé de p à q dans le plan XY local (rotation autour de Z seule), demi-largeur hw, demi-épaisseur hz."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    d = q - p
    ln = math.hypot(d[0], d[1])
    ang = math.degrees(math.atan2(d[1], d[0]))
    cube(g, name, p + (-ov, -hw, -hz), p + (ln + ov, hw, hz), p, (0, 0, ang), solid(tile))


# Orientation de la tige dans la main
psi, alpha = math.radians(YAW), math.radians(TILT)
A_DIR = V(math.sin(psi) * math.cos(alpha), math.sin(alpha), -math.cos(psi) * math.cos(alpha))
Y0 = math.degrees(math.asin(-A_DIR[2]))
Z0 = math.degrees(math.atan2(A_DIR[1], A_DIR[0]))
# roulis : +Z local (visage de l'étoile) tourné vers l'avant et l'extérieur, un peu vers le bas
want = unit(V(0.45, 0, -1.0))
want = unit(want - (want @ A_DIR) * A_DIR)
best = max(range(0, 360, 1), key=lambda r: rotm(r, Y0, Z0)[:, 2] @ want)
ROLL = float(best if best <= 180 else best - 360)
R_BAG = rotm(ROLL, Y0, Z0)
assert np.allclose(R_BAG[:, 0], A_DIR, atol=1e-6)

bras = group("right_arm", [5, 22, 0])
prise = group("prise", P0, parent=bras)
bag = group("baguette", P0, parent=prise, rotation=(ROLL, Y0, Z0))

# Pommeau : bille de sucre vanille, bague rose
octo_x(bag, "pommeau", S_POM0, S_POM1, 0.74, "vanille")
octo_x(bag, "pommeau_bout", S_POM0 - 0.28, S_POM0 + 0.05, 0.5, "vanille")
# Tige torsadée, légèrement effilée vers l'étoile, en trois tronçons qui gardent la phase de la spirale
cuts = [S_TIGE0, 2.0, 6.0, S_TIGE1]
for i in range(3):
    octo_x(bag, f"tige{i}", cuts[i] - (0.03 if i else 0), cuts[i + 1], lerp(0.58, 0.52, i / 2), "tige", spiral=True)

# Nœud de ruban : deux plaques (peau) de part et d'autre, âmes pleines dans les boucles et les pans, nœud en volume
nd = group("noeud", L(S_NOEUD), parent=bag)
bw, bh = BOW_Y1 - BOW_Y0, BOW_X1 - BOW_X0
bc = L(S_NOEUD + (BOW_Y0 + BOW_Y1) / 2)
plate(nd, "ruban_av", bc + V(0, 0, 0.3), bw, bh, "bow")
plate(nd, "ruban_ar", bc - V(0, 0, 0.3), bw, bh, "bow")
cube(nd, "noeud_coeur", L(S_NOEUD - 0.4, -0.42, -0.58), L(S_NOEUD + 0.42, 0.42, 0.58), L(S_NOEUD), (0, 0, 0), solid("ruban"))
for sy in (-1, 1):
    tag = "g" if sy > 0 else "d"
    # boucle : âme le long du grand axe, plus étroite que la silhouette
    box_dir(nd, f"boucle_{tag}", L(S_NOEUD + 0.05, sy * 0.3, 0), L(S_NOEUD + 0.12 + 0.34, sy * 1.75, 0), 0.32, 0.36, "ruban")
    box_dir(nd, f"pan_{tag}", L(S_NOEUD - 0.1, sy * 0.2, 0), L(S_NOEUD - 1.3, sy * 0.58, 0), 0.13, 0.36, "ruban")

# Étoile : groupe qui tourne sur l'axe de la tige, sous-groupe qui « pétille » (échelle)
et = group("etoile", L(C_STAR), parent=bag, rotation=(STAR_ROLL, 0, 0))
pop = group("etoile_pop", L(C_STAR), parent=et)
SC = L(C_STAR)
plate(pop, "etoile_av", SC + V(0, 0, 0.70), W_STAR1, W_STAR1, "star1")
plate(pop, "etoile_ar", SC - V(0, 0, 0.70), W_STAR1, W_STAR1, "star1")
plate(pop, "bombe_av", SC + V(0, 0, 1.02), W_STAR2, W_STAR2, "star2f")
plate(pop, "bombe_ar", SC - V(0, 0, 1.02), W_STAR2, W_STAR2, "star2b")


def half_width(rad, frac_angle=0.0):
    """Demi-largeur (px) de la branche à la distance rad du centre, mesurée sur le masque peint de l'étage 1."""
    N, k = 600, 600 / (2 * R_OUT + 0.4)
    m = star_mask(N, k, 1.0)
    cy = int(N / 2 - rad * k)
    row = m[cy]
    cx = N // 2
    if not row[cx]:
        return 0.0
    l = r = cx
    while l > 0 and row[l - 1]:
        l -= 1
    while r < N - 1 and row[r + 1]:
        r += 1
    return min(cx - l, r - cx) / k


# âmes : centre octogonal (épaisseur jusqu'à l'étage 1), cœur de l'étage bombé, trois tronçons par branche
for j, (rot, hw) in enumerate(((0.0, 0.8), (45.0, 0.78))):
    cube(pop, f"ame_centre{'o' if j else ''}", SC - (hw, hw, 0.8 - 0.02 * j), SC + (hw, hw, 0.8 - 0.02 * j), SC, (0, 0, rot), solid("core_star"))
for j, (rot, hw) in enumerate(((0.0, 0.55), (45.0, 0.53))):
    cube(pop, f"ame_bombe{'o' if j else ''}", SC - (hw, hw, 1.0 - 0.02 * j), SC + (hw, hw, 1.0 - 0.02 * j), SC, (0, 0, rot), solid("jaune"))
SEG = ((0.55, 1.35), (1.25, 1.85), (1.75, 2.18))
for b in range(5):
    ang = 36 * 2 * b            # pointe 0 le long de +X local (axe de la tige)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for i, (r0, r1) in enumerate(SEG):
        hw = max(0.12, half_width(r1) - 0.12)
        p = SC + V(ca * r0, sa * r0, 0)
        q = SC + V(ca * r1, sa * r1, 0)
        box_dir(pop, f"branche{b}_{i}", p, q, hw, 0.5 - 0.02 * i, "core_star")

# Points d'émission : bouts des branches
EMITS = []


def emit(parent, at):
    EMITS.append(group("emit_etincelle" + (str(len(EMITS) + 1) if EMITS else ""), at, parent=parent))


for b in range(5):
    ang = math.radians(72 * b)
    emit(pop, SC + V(math.cos(ang) * R_OUT, math.sin(ang) * R_OUT, 0))

# Particule : une seule plaque de 0,3 px, face up seule, au-dessus du pivot
PG = group("particle_etincelle", [0, 0, 0])
u0, v0, u1, v1 = UV["etincelle"]
cube(PG, "etincelle", [-1.0, 0.3, -1.0], [1.0, 0.6, 1.0], [0, 0, 0], (0, 0, 0), {"up": [u0, v0, u1, v1]})


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node(bras), bone_node(PG)]


# ------------------------------------------------------------------ animations
# Guide, section 3 : +X bascule le haut vers l'arrière (relève la pointe, qui part vers l'avant), +Y avance le côté droit
# (la pointe, devant, part vers la gauche du joueur = vers l'intérieur), +Z monte le côté droit.
# Une seule main droite : pas de miroir. Intention : rise relève la pointe, inward la ramène vers l'axe du corps, roll la penche vers l'extérieur.
def pose(rise, inward, roll):
    return rise, inward, -roll


def kf(t, x, y, z, ch="rotation"):
    f = lambda v: v if isinstance(v, str) else str(round(v + 0.0, 3))
    return {"channel": ch, "data_points": [{"x": f(x), "y": f(y), "z": f(z)}], "time": round(t, 3), "interpolation": "linear"}


SPIN = 45.0         # °/s : un tour en 8 s, piloté par q.life_time (continu d'un état à l'autre, pas de tourbillon au fondu)
SPIN_EXPR = f"q.life_time*{SPIN:g}"


def anim(name, length, tracks, n_kf=None, loop="loop", spin=True, scale_tracks=None):
    n = n_kf or max(6, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]
    A = {}
    for g, f in tracks.items():
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(t, *f(t)) for t in times]}
    for g, f in (scale_tracks or {}).items():
        A.setdefault(groups[g]["uuid"], {"name": g, "type": "bone", "keyframes": []})["keyframes"] += [kf(t, *([f(t)] * 3), ch="scale") for t in times]
    if spin:
        A[groups[et]["uuid"]] = {"name": et, "type": "bone", "keyframes": [kf(0.0, SPIN_EXPR, "0", "0")]}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


LS = 8.0            # tous les états durent 8 s : la rotation continue de l'étoile (45 °/s) y fait exactement un tour


def scint(t):
    """Scintillement : deux petits gonflements de l'étoile par boucle de 8 s."""
    return 1 + 0.07 * bump(t, 1.2, 1.45, 1.5, 1.9) + 0.05 * bump(t, 5.0, 5.25, 5.3, 5.7)


def state(name, rise, inward, roll, amp, cycles, n_kf, twinkle=False):
    def f(t):
        ph = TAU * cycles * t / LS
        return pose(rise + amp * math.sin(ph), inward + 0.5 * amp * math.sin(ph + 1.2), roll + 0.4 * amp * math.sin(ph + 0.6))
    return anim(name, LS, {prise: f}, n_kf=n_kf, scale_tracks={pop: scint} if twinkle else None)


idle = state("idle", 0.0, 0.0, 0.0, 2.0, 2, 48, twinkle=True)           # respiration 4 s
walk = state("walk", 3.0, 1.0, 0.0, 3.5, 5, 80)                          # pas de 1,6 s
run = state("run", 16.0, 3.0, 4.0, 4.5, 8, 128)                          # pointe ramenée en arrière, pas de 1,0 s
sneak = state("sneak", -10.0, 6.0, -3.0, 1.2, 2, 32)                     # baguette baissée, rapprochée du corps


def moulinet(t):
    """Attaque : un tour de pointe (cercle) avec fondu d'entrée et de sortie, retour exact à 0."""
    env = bump(t, 0.0, 0.12, 0.5, 0.74)
    p = TAU * sm(t, 0.04, 0.62)
    return pose(env * (8 + 12 * math.sin(p)), env * 12 * (math.cos(p) - 0.2), env * 8 * math.sin(p))


def pop_attaque(t):
    return 1 + 0.22 * bump(t, 0.28, 0.4, 0.44, 0.7)


attack = anim("attack", 0.8, {prise: moulinet}, n_kf=32, loop="once", spin=False, scale_tracks={pop: pop_attaque})


def sursaut(t):
    env = sm(t, 0.0, 0.06) * (1 - sm(t, 0.42, 0.76))
    trem = math.sin(TAU * t / 0.13) * math.exp(-4 * t)
    return pose(env * (13 + 4 * trem), env * -3, env * 5 * trem)


hurt = anim("hurt", 0.8, {prise: sursaut}, n_kf=32, loop="once", spin=False)

PF, PR = 2.0, 4.0
pfall = anim("particle_etincelle_fall", PF, {PG: lambda t: (0, 360 * t / PF, 0)}, n_kf=16, spin=False,
             scale_tracks={PG: lambda t: 1 + 0.15 * math.sin(2 * TAU * t / PF)})
prest = anim("particle_etincelle_rest", PR, {PG: lambda t: (0, 90 * t / PR * 4, 0)}, n_kf=16, spin=False)

ANIMS = [idle, walk, run, sneak, attack, hurt, pfall, prest]

# ------------------------------------------------------------------ écriture
assert 40 <= len(elements) <= 130, f"budget : {len(elements)} cubes"
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


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      len(EMITS), "emit_ ; roulis", ROLL, "; base", round(Y0, 2), round(Z0, 2))
