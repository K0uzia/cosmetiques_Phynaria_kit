"""Masque de cuir : harnais de tête en cuir noir verni, quincaillerie chrome lourde, bâillon-boule rouge. Ensemble Cuir (thème Fétiche).
Écrit masque_cuir.png, masque_cuir_e.png et .build/masque_cuir_brut.bbmodel à côté de ce script.

Accessoire fétiche pour adultes (serveur privé, grade admin), posé sur le skin : le visage reste visible. Groupe de premier niveau head.
Design d'après la référence de l'utilisateur (harnais et boule seulement), aux proportions d'un vrai harnais ramenées à la tête de
8 px (1 px ≈ 2 cm) : sangles de 2,5 cm (1,2 px), épaisseur 0,35 px ; boule de 4 cm ; anneaux en O de 1,8 px, section 0,45.
Les versions précédentes (cubes à 0,6 px de la tête, décalque à 0,6 px de large, pixel art) se lisaient « cage », « fil de fer »,
« trop Minecraft ».

- Sangles : vrais volumes plats contre la tête, face intérieure à 4,62 px du centre (0,12 px au-dessus de la seconde couche du skin,
  gonflée de 0,5 dans Minecraft) et extérieure à 4,97. Une sangle qui passe par-dessus une autre est sur la couche 4,72..5,07.
  Aux arêtes de la tête, la sangle tourne : une pièce couvre le coin (son bout est peint comme la sangle), la pièce voisine s'arrête
  contre elle (bout non dessiné). Les diagonales du V sont des pièces tournées dans le plan de la face.
- Texture des sangles (40 texels/px) : cuir noir verni (18..34), reflet large et doux (90, 92, 104) sur le tiers haut, bords biseautés
  plus clairs (60, 62, 72), couture gris foncé en tirets à 4 texels des bords, tranches noir mat.
- Quincaillerie chrome (dégradé, reflet blanc net, ombre bleutée) : anneaux en O (plaque découpée ronde, peinte en tore, sur une âme
  de 16 tronçons pour l'épaisseur), boucle à rouleau (cadre, rouleau, ardillon) avec passant de cuir et bout de sangle arrondi troué,
  doubles rivets bombés.
- Bâillon : disque peint en sphère (reflet net en haut à gauche, liseré de lumière en bas à droite) dans un groupe cam_, rond sous tous
  les angles, rayon 1,05, centré à (0, 25,5, −4,45) et avancé de 0,62 px vers la caméra (compromis : plus, il se détache vu
  de dessous ; moins, la face de la tête le coupe de 3/4) ; deux petits anneaux le relient à la sangle.
  Dans le menu Apparence (pas de caméra), overlay_menu le tourne de 180° (q.is_in_menu) : face à z −5,07.
- Contrôle interne : aucune paire de faces dessinées parallèles et alignées sur les axes à moins de 0,1 px là où elles se recouvrent,
  peau (4) et seconde couche (4,5) comprises ; écart maximal face intérieure / peau des sangles < 0,8 px.
  Statique ; ambiance (pluie, nuit) de tools/ambiance.py ; pas de son, de particule ni de _r.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "masque_cuir"
TEX = 512
D = 40                       # texels par px pour les sangles
SS = 4

# ------------------------------------------------------------------ palette
LX_TOP, LX_BOT, LX_HL, LX_BEV, LX_ST, LX_MAT = (34, 34, 40), (18, 18, 22), (90, 92, 104), (60, 62, 72), (70, 72, 82), (12, 12, 14)
CR_W, CR_C, CR_B, CR_SH, CR_D = (255, 255, 255), (226, 230, 238), (150, 156, 170), (62, 70, 96), (28, 30, 40)
RG_B, RG_O, RG_C, RG_RIM = (200, 28, 36), (96, 10, 18), (255, 252, 252), (255, 120, 120)

# ------------------------------------------------------------------ couches (distance au centre de la tête)
HC = 28.0
L0 = (4.62, 4.97)            # sangle posée contre la tête
L1 = (4.72, 5.07)            # sangle qui passe par-dessus une autre
W = 1.2                      # largeur d'une sangle
LMAX = 10.2                  # longueur de la tuile de sangle


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ textures
def tile_strap(L=LMAX, w=W, dens=D):
    """Sangle de cuir verni vue de dessus : lignes = travers (0 = bord du reflet), colonnes = longueur."""
    H, Wd = int(round(w * dens)), int(round(L * dens))
    a = np.zeros((H, Wd, 4), np.uint8)
    for r in range(H):
        u = (r + 0.5) / H
        c = lerp(np.array(LX_TOP, float), np.array(LX_BOT, float), u)
        hl = math.exp(-((u - 0.3) / 0.13) ** 2)
        c = lerp(c, np.array(LX_HL, float), 0.85 * hl)
        a[r, :, :3] = c
    a[:3, :, :3] = LX_BEV
    a[-3:, :, :3] = LX_BEV
    a[3, :, :3] = (8, 8, 10)
    a[-4, :, :3] = (8, 8, 10)
    for row in (5, 6, H - 7, H - 6):
        for x in range(Wd):
            if x % 7 < 4:
                a[row, x, :3] = LX_ST
    a[..., 3] = 255
    return a


def tile_tail(L=1.6, w=1.0, dens=D, holes=(0.55, 1.05)):
    """Bout de sangle : bout arrondi (côté u max), deux trous cerclés de chrome sombre."""
    t = tile_strap(L, w, dens).astype(np.float32)
    H, Wd = t.shape[:2]
    yy, xx = np.mgrid[0:H * SS, 0:Wd * SS]
    X, Y = (xx + 0.5) / (SS * dens), (yy + 0.5) / (SS * dens)
    r = w / 2
    cx = L - r
    inside = (X <= cx) | (np.hypot(X - cx, Y - r) <= r)
    al = inside.reshape(H, SS, Wd, SS).mean(axis=(1, 3)) > 0.45
    rim = (X > cx) & (np.hypot(X - cx, Y - r) > r - 0.07) & inside
    rimd = rim.reshape(H, SS, Wd, SS).mean(axis=(1, 3)) > 0.3
    t[rimd, :3] = LX_BEV
    for h in holes:
        d = np.hypot(X - h, Y - r)
        for rad, col in ((0.13, CR_SH), (0.085, (4, 4, 6))):
            m = (d < rad).reshape(H, SS, Wd, SS).mean(axis=(1, 3)) > 0.45
            t[m, :3] = col
    t[..., 3] = al * 255
    t[~al, :3] = LX_BOT
    return t.astype(np.uint8)


def _chrome_shade(nx, ny, nz):
    """Chrome : dégradé selon la normale (lumière en haut à gauche), reflet blanc net, ombre bleutée, contre-jour en bas."""
    L = np.array((-0.5, 0.62, 0.6))
    L = L / np.linalg.norm(L)
    lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], -1, 1)
    c = lerp(np.array(CR_SH, np.float32), np.array(CR_B, np.float32), np.clip(lam + 0.35, 0, 1)[..., None])
    c = lerp(c, np.array(CR_C, np.float32), np.clip((lam - 0.45) * 2.5, 0, 1)[..., None])
    Hh = np.array((L[0], L[1], L[2] + 1.0))
    Hh = Hh / np.linalg.norm(Hh)
    spec = np.clip(nx * Hh[0] + ny * Hh[1] + nz * Hh[2], 0, 1) ** 40
    c = lerp(c, np.array(CR_W, np.float32), (spec > 0.5)[..., None] * 1.0)
    rim = np.clip(-(nx * 0.6 - ny * 0.7), 0, 1) * (nz < 0.5)
    c = lerp(c, np.array((176, 186, 210), np.float32), (rim * 0.35)[..., None])
    return c


def tile_ring(r0, r1, dens=48):
    """Anneau en O vu de face, peint en tore : découpé rond."""
    n = int(round(2 * r1 * dens))
    yy, xx = np.mgrid[0:n * SS, 0:n * SS]
    x = (xx + 0.5) / (n * SS) * 2 * r1 - r1
    y = r1 - (yy + 0.5) / (n * SS) * 2 * r1
    r = np.hypot(x, y)
    rm, hw = (r0 + r1) / 2, (r1 - r0) / 2
    s = np.clip((r - rm) / hw, -1, 1)
    nz = np.sqrt(np.clip(1 - s * s, 0, 1))
    phi = np.arctan2(y, x)
    c = _chrome_shade(np.cos(phi) * s, np.sin(phi) * s, nz)
    c = np.where((np.abs(s) > 0.9)[..., None], np.array(CR_D, np.float32), c)
    m = (r >= r0) & (r <= r1)
    rgb = c.reshape(n, SS, n, SS, 3).mean(axis=(1, 3))
    al = m.reshape(n, SS, n, SS).mean(axis=(1, 3)) > 0.45
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    out[..., 3] = al * 255
    out[~al, :3] = CR_B
    return out


def tile_dome(n=24):
    """Rivet en chapeau bombé vu de face."""
    yy, xx = np.mgrid[0:n * SS, 0:n * SS]
    x, y = (xx + 0.5) / (n * SS) * 2 - 1, 1 - (yy + 0.5) / (n * SS) * 2
    r = np.hypot(x, y)
    nz = np.sqrt(np.clip(1 - (r * 0.85) ** 2, 0, 1))
    c = _chrome_shade(x * 0.85, y * 0.85, nz)
    c = np.where((r > 0.88)[..., None], np.array(CR_D, np.float32), c)
    rgb = c.reshape(n, SS, n, SS, 3).mean(axis=(1, 3))
    al = (r <= 1).reshape(n, SS, n, SS).mean(axis=(1, 3)) > 0.45
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    out[..., 3] = al * 255
    out[~al, :3] = CR_B
    return out


def tile_bar(n=16):
    """Barre chrome (cadre de boucle, rouleau, âme d'anneau) : section ronde peinte en travers (lignes)."""
    a = np.zeros((n, n, 4), np.uint8)
    for r in range(n):
        s = (r + 0.5) / n * 2 - 1
        c = _chrome_shade(np.zeros(1), np.array([-s]), np.array([math.sqrt(max(0.0, 1 - s * s))]))[0]
        if abs(s) > 0.88:
            c = np.array(CR_D, float)
        a[r, :, :3] = np.clip(c, 0, 255)
    a[..., 3] = 255
    return a


def tile_flat(c, n=8):
    a = np.zeros((n, n, 4), np.uint8)
    a[..., :3] = c
    a[..., 3] = 255
    return a


def tile_ball(n=96):
    """Boule rouge brillante : ombrage de sphère, reflet net en haut à gauche, liseré de lumière en bas à droite."""
    yy, xx = np.mgrid[0:n * SS, 0:n * SS]
    u, v = (xx + 0.5) / (n * SS) * 2 - 1, (yy + 0.5) / (n * SS) * 2 - 1
    r = np.hypot(u, v)
    z = np.sqrt(np.clip(1 - r * r, 0, 1))
    L = np.array((-0.5, -0.62, 0.6)) / np.linalg.norm((-0.5, -0.62, 0.6))
    lam = np.clip(u * L[0] + v * L[1] + z * L[2], 0, 1)
    c = lerp(np.array(RG_O, np.float32), np.array(RG_B, np.float32), np.clip(lam * 1.3, 0, 1)[..., None])
    c = lerp(c, np.array((236, 72, 80), np.float32), np.clip((lam - 0.82) * 5, 0, 1)[..., None])
    rim = np.clip((u * 0.6 + v * 0.7) * 1.2 - 0.25, 0, 1) * np.clip((r - 0.78) * 6, 0, 1)
    c = lerp(c, np.array(RG_RIM, np.float32), (rim * 0.75)[..., None])
    c = lerp(c, np.array((70, 6, 12), np.float32), (np.clip((r - 0.95) * 25, 0, 1) * 0.7)[..., None])
    spot = np.hypot((u + 0.36) / 1.3, v + 0.42) < 0.16
    c = np.where(spot[..., None], np.array(RG_C, np.float32), c)
    rgb = c.reshape(n, SS, n, SS, 3).mean(axis=(1, 3))
    al = (r < 0.99).reshape(n, SS, n, SS).mean(axis=(1, 3)) > 0.45
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    out[..., 3] = al * 255
    out[~al, :3] = RG_B
    return out


# ================================================================== PARAMÈTRES DE LA PIÈCE
YM = 25.5                    # axe de la sangle de la bouche
XJ = 3.62                    # joues (face avant) : bord intérieur à 3,02, à l'extérieur des yeux du skin (|x| ≤ 3)
YR = 31.0                    # anneau du front
YV = 29.6                    # coude du V (au-dessus des yeux)
ZCH, W_CH = -3.5, 1.0        # sangle de menton : axe z et largeur (devant le cou : le torse s'arrête à z −2,25)
R_BIG = (0.45, 0.9)          # anneaux en O : rayons intérieur / extérieur (section 0,45)
R_SMALL = (0.2, 0.42)        # anneaux de la boule
BALL_C, BALL_R, BALL_S = np.array([0.0, YM, -4.45]), 1.05, 0.62
XB = 1.38                    # anneaux de la boule (x)
BX = -2.2                    # boucle de la nuque (x)
YCB = 24.3                   # boucle du menton, côté gauche (y)
TILES = {"sangle": tile_strap(), "sangle_menton": tile_strap(w=W_CH), "bout": tile_tail(), "mat": tile_flat(LX_MAT),
         "anneau": tile_ring(*R_BIG), "anneau_p": tile_ring(*R_SMALL), "rivet": tile_dome(), "barre": tile_bar(), "chrome_lisse": tile_flat((120, 126, 142)), "boule": tile_ball()}
# ================================================================== fin des paramètres

UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def build_atlas():
    uv, x, y, shelf = {}, 0, 0, 0
    for n, im in sorted(TILES.items(), key=lambda it: -it[1].shape[0]):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, "atlas plein"
        uv[n] = (x, y, x + w, y + h)
        x += w + 1
        shelf = max(shelf, h)
    UV.update(uv)
    tex = np.zeros((TEX, TEX, 4), np.uint8)
    for n, im in TILES.items():
        u0, v0, u1, v1 = UV[n]
        tex[v0:v1, u0:u1] = im
    assert tex[TEX - 3, TEX - 3, 3] == 0
    assert set(np.unique(tex[..., 3])) <= {0, 255}, "semi-transparence"
    b64 = []
    for arr, fn in ((tex, f"{NOM}.png"), (np.zeros_like(tex), f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        b64.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return b64


TEX_B64, TEX_E_B64 = build_atlas()

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx (ordre du mod et du renderer), blocage de cardan compris ; vérifié."""
    assert np.linalg.det(R) > 0.99, "repère indirect"
    if abs(R[2, 0]) > 1 - 1e-9:
        ry = -math.copysign(math.pi / 2, R[2, 0])
        rx = math.atan2(R[0, 1] if R[2, 0] < 0 else -R[0, 1], R[1, 1])
        rz = 0.0
    else:
        ry = math.asin(-R[2, 0])
        rx, rz = math.atan2(R[2, 1], R[2, 2]), math.atan2(R[1, 0], R[0, 0])
    a, b, c = rx, ry, rz
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    assert np.allclose(Rz @ Ry @ Rx, R, atol=1e-6), "euler"
    return tuple(math.degrees(v) for v in (rx, ry, rz))


def group(name, origin, parent=None):
    assert name not in groups
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in frm], "to": [round(float(v), 4) for v in to],
         "origin": [round(float(v), 4) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-4 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])
    return e


def frame(X, n):
    X, n = unit(X), unit(n)
    return np.column_stack([X, np.cross(n, X), n])


def oriented(g, name, c, R_, half, faces):
    c = np.asarray(c, float)
    cube(g, name, c - half, c + half, c, euler(R_), faces)


def T(tile, u_len=None, dens=D):
    """UV d'une tuile ; u_len (px) : sous-partie de cette longueur, depuis le début (sangles)."""
    u0, v0, u1, v1 = UV[tile]
    if u_len is not None:
        u1 = min(u1, u0 + max(1, round(u_len * dens)))
    return [u0, v0, u1, v1]


def strap(g, name, p, q, n, layer=L0, w=W, hl=None, end_p="mat", end_q="mat", tile="sangle"):
    """Sangle de p à q (points du plan de la face, composante n nulle depuis le centre de la tête), couche (d0, d1).
    hl : côté du reflet (par défaut vers le haut, sinon vers +x). end_p / end_q : 'sangle' (bout peint comme la face, au coin),
    'mat', ou None (bout caché contre la pièce voisine, non dessiné)."""
    p, q, n = np.asarray(p, float), np.asarray(q, float), unit(n)
    X = unit(q - p)
    if hl is None:
        hl = V(0, 1, 0) if abs(n[1]) < 0.5 else V(1, 0, 0)
    R_ = frame(X, n)
    flip = R_[:, 1] @ np.asarray(hl, float) < 0
    if flip:
        R_ = frame(-X, n)
        end_p, end_q = end_q, end_p
    STRAPS.append((name, layer[0]))
    d0, d1 = layer
    L = np.linalg.norm(q - p)
    assert L <= LMAX + 1e-6, (name, L)
    c = (p + q) / 2 + n * ((d0 + d1) / 2)
    th = d1 - d0
    f = {"south": T(tile, L), "north": T("mat"), "up": T("mat"), "down": T("mat")}
    for key, e in (("west", end_p), ("east", end_q)):
        if e == "sangle":
            f[key] = T(tile, th)
        elif e == "mat":
            f[key] = T("mat")
    oriented(g, name, c, R_, np.array([L / 2, w / 2, th / 2]), f)


def o_ring(g, name, c, n, u, rr=R_BIG, plate=(5.17, 5.47), core=(4.82, 5.27), N=32, tile="anneau"):
    """Anneau en O : plaque découpée ronde peinte en tore (devant), âme de N tronçons pour l'épaisseur vue de biais.
    d mesuré depuis c le long de n."""
    n, u = unit(n), unit(u)
    r0, r1 = rr
    c = np.asarray(c, float)
    R_ = frame(u, n)
    oriented(g, name, c + n * ((plate[0] + plate[1]) / 2), R_, np.array([r1, r1, (plate[1] - plate[0]) / 2]),
             {"south": T(tile), "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
    if core is None:
        return
    v = np.cross(n, u)
    a0, a1 = r0 + 0.08, r1 - 0.1
    rm, wr = (a0 + a1) / 2, a1 - a0
    Ls = 2 * rm * math.tan(math.pi / N)
    for i in range(N):
        a = 2 * math.pi * (i + 0.5) / N
        radial = u * math.cos(a) + v * math.sin(a)
        Rs = np.column_stack([np.cross(radial, n), radial, n])
        oriented(g, f"{name}_ame{i}", c + radial * rm + n * ((core[0] + core[1]) / 2), Rs, np.array([Ls / 2, wr / 2, (core[1] - core[0]) / 2]),
                 {k: T("chrome_lisse") for k in ("south", "north", "up", "down", "east", "west")})


def rivets(g, name, c, n, along, gap=0.56, d=5.17):
    """Double rivet bombé : deux têtes rondes (plaque découpée de d à d + 0,3, tranches transparentes) sur un fût en losange
    de 4,85 à d + 0,1 (faces à 0,1 px au moins des couches de sangle et de la tête)."""
    n, along = unit(n), unit(along)
    X = along
    R_ = frame(X, n)
    Y = R_[:, 1]
    c45 = math.cos(math.pi / 4)
    R45 = np.column_stack([c45 * X + c45 * Y, -c45 * X + c45 * Y, n])
    for k, s in enumerate((-0.5, 0.5)):
        p = np.asarray(c, float) + along * s * gap
        oriented(g, f"{name}{k}", p + n * (d + 0.15), R_, np.array([0.21, 0.21, 0.15]),
                 {"south": T("rivet"), "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
        oriented(g, f"{name}{k}_fut", p + n * ((4.85 + d + 0.1) / 2), R45, np.array([0.12, 0.12, (d + 0.1 - 4.85) / 2]),
                 {f: T("barre") for f in ("north", "south", "east", "west", "up", "down")})


def face_of(v):
    """Nom de la face d'un pavé aligné dont la normale est v (±X, ±Y, ±Z)."""
    ax = int(np.argmax(np.abs(v)))
    return (("west", "east"), ("down", "up"), ("north", "south"))[ax][int(v[ax] > 0)]


def wbox(g, name, base, ua, va, n, u, v, d, tile="barre", omit_u=False):
    """Pavé aligné sur les axes, décrit dans le repère (u le long de la sangle, v en travers, n vers l'extérieur) d'une face.
    omit_u : bouts ±u non dessinés (collés contre une autre pièce)."""
    ua, va, n = unit(ua), unit(va), unit(n)
    pts = [np.asarray(base, float) + ua * a + va * b + n * c for a in u for b in v for c in d]
    lo, hi = np.min(pts, axis=0), np.max(pts, axis=0)
    f = {k: T(tile) for k in ("north", "south", "east", "west", "up", "down")}
    if omit_u:
        del f[face_of(ua)], f[face_of(-ua)]
    cube(g, name, lo, hi, (lo + hi) / 2, (0, 0, 0), f)


def buckle(g, name, base, ua, va, n, d0=L0[0], w=W, tail=True, keeper=True):
    """Boucle à rouleau vue de face sur une sangle de largeur w (axe le long de ua, centre base) : deux barres en travers, deux
    longerons, rouleau sur la barre côté +u, ardillon ; passant de cuir et bout de sangle arrondi troué côté −u."""
    h = w / 2
    # cadre à peine plus large que la sangle (0,35 px de chaque côté) ; longerons entre les barres, bouts collés contre elles
    wbox(g, f"{name}_barre_g", base, ua, va, n, (-0.5, -0.2), (-h - 0.35, h + 0.35), (d0 + 0.45, d0 + 0.75))
    wbox(g, f"{name}_barre_d", base, ua, va, n, (0.2, 0.5), (-h - 0.35, h + 0.35), (d0 + 0.45, d0 + 0.75))
    wbox(g, f"{name}_long_h", base, ua, va, n, (-0.2, 0.2), (h + 0.1, h + 0.35), (d0 + 0.15, d0 + 0.45), omit_u=True)
    wbox(g, f"{name}_long_b", base, ua, va, n, (-0.2, 0.2), (-h - 0.35, -h - 0.1), (d0 + 0.15, d0 + 0.45), omit_u=True)
    wbox(g, f"{name}_rouleau", base, ua, va, n, (0.1, 0.6), (-h - 0.2, h + 0.2), (d0 + 0.25, d0 + 0.95))
    wbox(g, f"{name}_ardillon", base, ua, va, n, (-0.35, 0.35), (-0.15, 0.15), (d0 + 0.55, d0 + 0.85))
    if keeper:
        wbox(g, f"{name}_passant", base, ua, va, n, (-1.0, -0.65), (-h - 0.15, h + 0.15), (d0 + 0.2, d0 + 0.7), tile="mat")
    if tail:
        p = np.asarray(base, float) - ua * 0.55
        q = np.asarray(base, float) - ua * 2.15
        R_ = frame(-unit(ua), n)       # u de la tuile vers la pointe arrondie
        c = (p + q) / 2 + unit(n) * (d0 + 0.1 + 0.175)
        oriented(g, f"{name}_bout", c, R_, np.array([0.8, (w - 0.2) / 2, 0.175]),
                 {"south": T("bout"), "north": T("mat"), "up": T("mat"), "down": T("mat"), "west": T("mat"), "east": CLEAR})


X_, Y_, Z_ = V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)
STRAPS = []
E0, E1 = L0[1], L1[1]          # bouts de coin : 4,97 (couche 0), 5,07 (couche 1)
I0, I1 = L0[0], L1[0]          # plans intérieurs : 4,62, 4,72


def build():
    sg = group("sangles", [0, HC, 0])
    mt = group("metal", [0, HC, 0])
    # --- sangle de la bouche (L0) : avant de part et d'autre de la boule (bouts de coin), côtés, arrière
    for sx, t in ((1, "r"), (-1, "l")):
        strap(sg, f"bouche_avant_{t}", V(sx * (XB + 0.2), YM, 0), V(sx * E0, YM, 0), -Z_, end_p="mat", end_q="sangle")
        strap(sg, f"bouche_cote_{t}", V(0, YM, -I0), V(0, YM, I0), sx * X_, end_p=None, end_q=None)
    strap(sg, "bouche_arriere", V(-E0, YM, 0), V(E0, YM, 0), Z_, end_p="sangle", end_q="sangle")
    # --- sommet : vers l'avant (L0) jusqu'à l'anneau du front ; vers l'arrière (L1) jusqu'à la sangle de la bouche
    strap(sg, "sommet_avant", V(0, HC, -0.55), V(0, HC, -E0), Y_, end_p="mat", end_q="sangle")
    strap(sg, "front_haut", V(0, HC + I0, 0), V(0, YR + 0.6, 0), -Z_, end_p=None, end_q="mat")
    strap(sg, "sommet_arriere", V(0, HC, 0.55), V(0, HC, E1), Y_, layer=L1, end_p="mat", end_q="sangle")
    strap(sg, "nuque", V(0, HC + I1, 0), V(0, YM - 0.45, 0), Z_, layer=L1, end_p=None, end_q="mat")
    # --- V (L1) de l'anneau du front aux joues, puis joues (L0) jusqu'aux anneaux de la sangle de la bouche
    for sx, t in ((1, "r"), (-1, "l")):
        dv = unit(V(sx * XJ, YV, 0) - V(0, YR, 0))
        strap(sg, f"v_{t}", V(0, YR, 0) + dv * 0.68, V(sx * XJ, YV, 0) + dv * 0.35, -Z_, layer=L1)
        strap(sg, f"joue_{t}", V(sx * XJ, YV + 0.45, 0), V(sx * XJ, YM + 0.75, 0), -Z_, hl=sx * X_)
        rivets(mt, f"rivets_v_{t}", V(sx * XJ, YV + 0.05, 0), -Z_, Y_)
    # --- menton (L1) : côtés à z −3,5, de la sangle de la bouche à l'arête du bas, puis dessous (bouts de coin)
    for sx, t in ((1, "r"), (-1, "l")):
        strap(sg, f"menton_cote_{t}", V(0, YM + 0.85, ZCH), V(0, HC - I1, ZCH), sx * X_, layer=L1, w=W_CH, hl=-Z_,
              end_p="mat", end_q=None, tile="sangle_menton")
        rivets(mt, f"rivets_menton_{t}", V(0, YM, ZCH), sx * X_, Y_)
    strap(sg, "menton", V(-E1, HC, ZCH), V(E1, HC, ZCH), -Y_, layer=L1, w=W_CH, hl=-Z_, end_p="sangle", end_q="sangle", tile="sangle_menton")
    buckle(mt, "boucle_menton", V(0, YCB, ZCH), -Y_, Z_, -X_, d0=L1[0], w=W_CH, tail=False, keeper=False)
    rivets(mt, "rivets_nuque", V(0, YM, 0), Z_, Y_)
    # --- anneaux : sommet, front, jonctions joue / bouche, petits anneaux de la boule
    o_ring(mt, "anneau_sommet", V(0, HC, 0), Y_, X_)
    o_ring(mt, "anneau_front", V(0, YR, 0), -Z_, -X_)
    for sx, t in ((1, "r"), (-1, "l")):
        o_ring(mt, f"anneau_joue_{t}", V(sx * XJ, YM, 0), -Z_, -X_)
        # petits anneaux sur les flancs de la boule, tournés de 45° (vers l'avant et l'extérieur) : vus de biais, ils restent à côté
        nb = unit(V(sx, 0, -1))
        o_ring(mt, f"anneau_boule_{t}", V(sx * XB, YM, -4.95) - nb * 0.15, nb, Y_, rr=R_SMALL, plate=(0.0, 0.3), core=None, tile="anneau_p")
    # --- boucle à rouleau dans la nuque (sangle le long de +x, bout de sangle vers −x)
    buckle(mt, "boucle_nuque", V(BX, YM, 0), X_, Y_, Z_)
    # --- bâillon
    cam = group("cam_baillon", list(BALL_C))
    u0, v0, u1, v1 = UV["boule"]
    cube(cam, "boule", BALL_C + V(-BALL_R, -BALL_R, BALL_S - 0.3), BALL_C + V(BALL_R, BALL_R, BALL_S), list(BALL_C), (0, 0, 0),
         {"south": [u0, v0, u1, v1]})


build()


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "head", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone_node(n) for n in groups if groups[n]["parent"] is None]}]


# ------------------------------------------------------------------ contrôles
def corners(e):
    a, b = np.array(e["from"]), np.array(e["to"])
    o = np.array(e["origin"])
    rx, ry, rz = map(math.radians, e.get("rotation", [0, 0, 0]))
    Rx = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Ry = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Rz = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    R = Rz @ Ry @ Rx
    return {(i, j, k): (np.array([x, y, z]) - o) @ R.T + o
            for i, x in enumerate((a[0], b[0])) for j, y in enumerate((a[1], b[1])) for k, z in enumerate((a[2], b[2]))}


FACE_KEY = {"west": (0, 0), "east": (0, 1), "down": (1, 0), "up": (1, 1), "north": (2, 0), "south": (2, 1)}


def drawn_faces(e):
    """Faces dessinées (présentes, UV hors du texel transparent) dont la normale est alignée sur un axe : (axe, coordonnée, rectangle)."""
    P = corners(e)
    out = []
    for f, fd in e["faces"].items():
        if [round(v) for v in fd["uv"]] == CLEAR:
            continue
        ax, side = FACE_KEY[f]
        pts = np.array([p for key, p in P.items() if key[ax] == side])
        ext = pts.max(0) - pts.min(0)
        for a2 in range(3):
            if ext[a2] < 1e-4:
                o = [k for k in range(3) if k != a2]
                out.append((a2, pts[0][a2], pts[:, o].min(0), pts[:, o].max(0)))
    return out


SKIN = []
for dd, (y0, y1, h) in ((4.0, (24, 32, 4)), (4.5, (23.5, 32.5, 4.5))):
    for s in (-1, 1):
        SKIN += [(0, s * dd, np.array([y0, -h]), np.array([y1, h])), (2, s * dd, np.array([-h, y0]), np.array([h, y1])),
                 (1, HC + s * dd, np.array([-h, -h]), np.array([h, h]))]


def overlap(lo, hi, lo2, hi2):
    return all(np.minimum(hi, hi2) - np.maximum(lo, lo2) > 1e-4)


def check_faces(tol=0.1 - 1e-6):
    F = [(e["name"], drawn_faces(e)) for e in elements]
    bad = []
    for i in range(len(F)):
        for ax, p, lo, hi in F[i][1]:
            for ax2, p2, lo2, hi2 in SKIN:
                if ax == ax2 and abs(p - p2) < tol and overlap(lo, hi, lo2, hi2):
                    bad.append((F[i][0], "peau/couche", "xyz"[ax], round(p, 3), p2))
        for j in range(i + 1, len(F)):
            a_, b_ = F[i][0].split("_ame")[0], F[j][0].split("_ame")[0]
            if "_ame" in F[i][0] and "_ame" in F[j][0] and a_ == b_:
                continue        # tronçons d'une même âme d'anneau, bout à bout
            for ax, p, lo, hi in F[i][1]:
                for ax2, p2, lo2, hi2 in F[j][1]:
                    if ax == ax2 and abs(p - p2) < tol and overlap(lo, hi, lo2, hi2):
                        bad.append((F[i][0], F[j][0], "xyz"[ax], round(p, 3), round(p2, 3)))
    return bad


BAD = check_faces()
for b in BAD:
    print("faces parallèles proches :", b)
assert not BAD, f"{len(BAD)} paires de faces parallèles à moins de 0,1 px"


def inner_gap(e):
    """Écart entre la face intérieure d'une sangle et la peau : coin le plus proche du centre, en norme max."""
    P = np.array(list(corners(e).values())) - V(0, HC, 0)
    return float(np.min(np.max(np.abs(P), axis=1))) - 4.0


STRAP_GAP = max(d0 for _, d0 in STRAPS) - 4.0
allp = np.array([p for e in elements for p in corners(e).values()])
lo_, hi_ = allp.min(0), allp.max(0)
GAP_MAX = max(-lo_[0] - 4, hi_[0] - 4, -lo_[2] - 4, hi_[2] - 4, hi_[1] - 32, 24 - lo_[1])

# ------------------------------------------------------------------ modèle
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner,
         "textures": [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": TEX_B64},
                      {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": TEX_E_B64}],
         "animations": []}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
from ambiance import ajouter_ambiance
ajouter_ambiance(model, foyer=1.0)
if "cam_baillon" in groups:
    model["animations"].append({"uuid": nuid(), "name": "overlay_menu", "loop": "loop", "override": False, "length": 1.0, "snapping": 24,
                                "selected": False, "animators": {groups["cam_baillon"]["uuid"]: {"name": "cam_baillon", "type": "bone", "keyframes": [
                                    {"channel": "rotation", "data_points": [{"x": "0", "y": "q.is_in_menu * 180", "z": "0"}], "time": 0, "interpolation": "linear"}]}}})

os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))
print(len(elements), "cubes ;", len(groups) + 1, "groupes ;", len(model["animations"]), "anims ;", os.path.getsize(OUT) // 1024, "Ko ;",
      f"écart max à la peau {GAP_MAX:.2f} px ; face intérieure des sangles au plus à {STRAP_GAP:.2f} px de la peau")
