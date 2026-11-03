"""Épaulettes guimauve : une guimauve dodue sur chaque épaule, ensemble « Pâtisserie ». Design original (série kawaii).
Écrit epaulettes_guimauve.png, epaulettes_guimauve_e.png et .build/epaulettes_guimauve_brut.bbmodel à côté de ce script.

Chaque guimauve est un cylindre aux arêtes arrondies : coque de plaques fines (12 côtés, 4 anneaux de profil + 2 couvercles),
chaque plaque découpée par alpha en trapèze pour fermer le polygone, autour d'une âme pleine octogonale.
Toute la peinture (poudre de sucre, ombre de base, visage) est une fonction continue de (angle, abscisse le long du profil) :
elle passe d'un anneau à l'autre sans couture.
Droite (x > 0) : vanille crème, visage endormi, fanion chocolat au cœur fraise.
Gauche (x < 0) : fraise pâle, visage souriant, fanion vanille à l'étoile fraise.
Groupes de premier niveau right_arm / left_arm : le mod remplace leur pivot par l'épaule.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

AVEC_E = True       # calque _e embarqué en seconde texture (correctif du clignotement annoncé le 2026-11-03, à vérifier en jeu)
NOM = "epaulettes_guimauve"
TEX = 512
TAU = 2 * math.pi
TH = 0.3            # épaisseur des plaques
NS = 12             # côtés du polygone de la coque
A_ = 2.0            # apothème (rayon) de la guimauve
H_ = 3.0            # hauteur
RC, RB = 1.0, 0.5   # rayon d'arrondi du haut et du bas
Y0 = 24.08          # base : 0,08 px au-dessus du dessus du bras (y = 24), sans le traverser
CX = 6.45           # centre |x| : bord intérieur à x = 4,38 (tête à x = 4)
EXT = 0.04          # recouvrement entre anneaux

# Profil (rayon, hauteur) de bas en haut : chanfrein bas, flanc, deux segments pour l'arrondi du haut.
_c45 = math.cos(math.pi / 4)
PROFIL = [(A_ - RB, 0.0), (A_, RB), (A_, H_ - RC), (A_ - RC + RC * _c45, H_ - RC + RC * _c45), (A_ - RC, H_)]
SEGS = []
_l = 0.0
for (r0, h0), (r1, h1) in zip(PROFIL, PROFIL[1:]):
    L = math.hypot(r1 - r0, h1 - h0)
    SEGS.append(dict(r0=r0, h0=h0, r1=r1, h1=h1, L=L, l0=_l))
    _l += L
L_TOP = _l          # abscisse du bord du couvercle


def lerp(a, b, k):
    return a + (b - a) * k


def sm(x, a, b):
    u = np.clip((x - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


# ------------------------------------------------------------------ parfums
SAVEURS = {
    "vanille": dict(base=(250, 244, 230), haut=(255, 253, 246), ombre=(214, 196, 170), grain=(226, 210, 182), sucre=(255, 255, 255),
                    joue=(255, 150, 160), trait=(84, 50, 44), yeux="dort", seed=3),
    "fraise": dict(base=(255, 226, 232), haut=(255, 244, 247), ombre=(228, 168, 182), grain=(240, 196, 206), sucre=(255, 255, 255),
                   joue=(240, 104, 136), trait=(92, 44, 56), yeux="sourit", seed=7),
}


def noise_field(seed, n=256):
    return np.random.default_rng(seed).random((n, n))


def paint(sv, xs, l):
    """Couleur et masque de joue en fonction de xs (abscisse horizontale autour de la guimauve, 0 = face avant, + à droite
    pour qui la regarde) et l (abscisse le long du profil : 0 = arête du bas, L_TOP = bord du couvercle, au-delà = couvercle)."""
    c = {k: np.array(v, np.float32) for k, v in sv.items() if isinstance(v, tuple)}
    col = np.empty(xs.shape + (3,), np.float32)
    col[...] = c["base"]
    col = lerp(col, c["haut"], sm(l, 2.0, 3.6)[..., None])                         # dessus plus blanc
    col = lerp(col, c["ombre"], (1 - sm(l, -0.2, 1.0))[..., None] * 0.95)            # ombre douce à la base
    col = lerp(col, c["ombre"] * 0.82, (1 - sm(l, -0.9, 0.05))[..., None])           # dessous
    # poudre de sucre : cellules de 0,13 px, grains blancs (dessus surtout) et grains beiges plus rares
    f = noise_field(sv["seed"])
    K = 1 / 0.13
    ix = np.floor(xs * K).astype(int) % 256
    iy = np.floor(l * K).astype(int) % 256
    rnd = f[iy, ix]
    rnd2 = f[(iy * 7 + 13) % 256, (ix * 5 + 31) % 256]
    fx, fy = xs * K - np.floor(xs * K), l * K - np.floor(l * K)
    inside = (np.hypot(fx - 0.5, fy - 0.5) < 0.42)
    dens = 0.10 + 0.22 * sm(l, 1.6, 3.4)
    col = np.where((inside & (rnd < dens))[..., None], c["sucre"], col)
    col = np.where((inside & (rnd > 0.965) & (rnd2 < 0.6) & (l > 0.3))[..., None], c["grain"], col)
    # visage, sur le flanc avant
    trait = c["trait"]
    joue = np.zeros(xs.shape, bool)
    face = np.abs(xs) < 1.8
    if sv["yeux"] == "dort":
        for ex in (-0.62, 0.62):          # yeux fermés en arc vers le bas
            d = np.hypot(xs - ex, (l - 1.98) * 1.1)
            col = np.where((face & (np.abs(d - 0.27) < 0.105) & (l < 1.98))[..., None], trait, col)
    else:
        for ex in (-0.62, 0.62):          # yeux ouverts, reflet blanc
            d = np.hypot((xs - ex) / 0.21, (l - 1.82) / 0.29)
            col = np.where((face & (d < 1))[..., None], trait, col)
            g = np.hypot(xs - (ex - 0.06), l - 1.93) < 0.085
            col = np.where(g[..., None], np.array((255, 255, 255), np.float32), col)
    d = np.hypot(xs, (l - 1.50) * 1.15)   # petite bouche en sourire
    col = np.where((face & (np.abs(d - 0.19) < 0.075) & (l < 1.50))[..., None], trait, col)
    for ex in (-1.05, 1.05):              # joues
        j = np.hypot((xs - ex) / 0.30, (l - 1.48) / 0.19) < 1
        col = np.where(j[..., None], c["joue"], col)
        joue |= j
    return col, joue


# ------------------------------------------------------------------ images : anneaux et couvercles, peints au texel
DENS = 24.0
TAN = math.tan(math.pi / NS)


def ring_geom(seg):
    rmax = max(seg["r0"], seg["r1"])
    return 2 * rmax * TAN + 0.04, seg["L"] + 2 * EXT


def phi_i(i):
    return TAU * i / NS


def img_ring(sv, seg):
    w, L = ring_geom(seg)
    cw, rh = int(math.ceil(w * DENS)), int(math.ceil(L * DENS))
    ss = 3
    jj, ii = np.mgrid[0:rh * ss, 0:NS * cw * ss]
    col_i = ii // (cw * ss)
    uf = ((ii % (cw * ss)) + 0.5) / (cw * ss)
    vf = (jj + 0.5) / (rh * ss)
    t = (uf - 0.5) * w
    s_ = -EXT + (1 - vf) * L
    r = seg["r0"] + (seg["r1"] - seg["r0"]) * np.clip(s_ / seg["L"], 0, 1)
    phi = TAU * col_i / NS - np.arctan2(t, r)
    phi = (phi + math.pi) % TAU - math.pi
    xs = -phi * A_
    l = seg["l0"] + s_
    col, joue = paint(sv, xs, l)
    al = np.abs(t) <= r * TAN + 0.025
    return down(col, al, joue, rh, NS * cw, ss), cw, rh


def img_cap(sv, top):
    ap = A_ - RC if top else A_ - RB
    w = 2 * ap / math.cos(math.pi / NS) + 0.06
    n = int(math.ceil(w * DENS))
    ss = 3
    jj, ii = np.mgrid[0:n * ss, 0:n * ss]
    x = ((ii + 0.5) / (n * ss) - 0.5) * w
    z = ((jj + 0.5) / (n * ss) - 0.5) * w * (1 if top else -1)
    r = np.hypot(x, z)
    phi = np.arctan2(x, -z)
    al = np.ones(x.shape, bool)
    for i in range(NS):
        p = phi_i(i)
        al &= (x * math.sin(p) - z * math.cos(p)) <= ap + 0.025
    l = (L_TOP + (ap - r)) if top else -(ap - r)
    col, joue = paint(sv, -phi * np.clip(r / A_, 0.2, 1) * A_, l)
    return down(col, al, joue, n, n, ss), w


def down(col, al, joue, h, w, ss):
    rgb = col.reshape(h, ss, w, ss, 3).mean(axis=(1, 3))
    a = al.reshape(h, ss, w, ss).mean(axis=(1, 3)) > 0.5
    j = joue.reshape(h, ss, w, ss).mean(axis=(1, 3)) > 0.5
    return rgb, a, j


def img_fanion(kind):
    """Fanion : hampe à gauche de l'image (u = 0), queue d'aronde arrondie à droite. Bordure de 0,18 px, motif central."""
    FW, FH = 2.6, 1.7
    W, H_px = int(math.ceil(FW * DENS)), int(math.ceil(FH * DENS))
    ss = 4
    m = Image.new("L", (W * ss, H_px * ss), 0)
    S = DENS * ss
    P = lambda x, y: (x * S, y * S)
    d = ImageDraw.Draw(m)
    r = 0.28
    # rectangle aux coins arrondis puis encoche arrondie
    d.rounded_rectangle([P(0.0, 0.05), P(FW - 0.02, FH - 0.05)], radius=r * S, fill=255)
    d.polygon([P(FW + 0.1, 0.42), P(FW - 0.72, FH / 2), P(FW + 0.1, FH - 0.42)], fill=0)
    d.ellipse([P(FW - 0.85, FH / 2 - 0.13), P(FW - 0.59, FH / 2 + 0.13)], fill=0)
    M = np.array(m, np.float32) / 255
    inner = Image.new("L", m.size, 0)
    di = ImageDraw.Draw(inner)
    b = 0.18
    di.rounded_rectangle([P(b, 0.05 + b), P(FW - 0.02 - b, FH - 0.05 - b)], radius=(r - 0.08) * S, fill=255)
    di.polygon([P(FW + 0.1, 0.42 - b), P(FW - 0.72 - b * 1.3, FH / 2), P(FW + 0.1, FH - 0.42 + b)], fill=0)
    I = np.array(inner, np.float32) / 255
    mo = Image.new("L", m.size, 0)
    dm = ImageDraw.Draw(mo)
    cx, cy = 1.02, FH / 2
    if kind == "choco":
        fond, bord, motif, reflet = (98, 58, 40), (170, 116, 78), (246, 92, 124), (255, 214, 226)
        rr = 0.27     # cœur : deux disques + triangle
        dm.ellipse([P(cx - 2 * rr + 0.02, cy - 0.42), P(cx + 0.02, cy - 0.42 + 2 * rr)], fill=255)
        dm.ellipse([P(cx - 0.02, cy - 0.42), P(cx + 2 * rr - 0.02, cy - 0.42 + 2 * rr)], fill=255)
        dm.polygon([P(cx - 2 * rr + 0.04, cy - 0.12), P(cx + 2 * rr - 0.04, cy - 0.12), P(cx, cy + 0.5)], fill=255)
        gl = (cx - 0.3, cy - 0.27, 0.075)
    else:
        fond, bord, motif, reflet = (254, 242, 214), (206, 146, 86), (244, 112, 146), (255, 222, 232)
        pts = []
        for k in range(10):
            ang = -math.pi / 2 + k * math.pi / 5
            rad = 0.52 if k % 2 == 0 else 0.24
            pts.append(P(cx + rad * math.cos(ang), cy + 0.04 + rad * math.sin(ang)))
        dm.polygon(pts, fill=255)
        gl = (cx - 0.12, cy - 0.12, 0.07)
    Mo = np.array(mo, np.float32) / 255
    col = np.empty(M.shape + (3,), np.float32)
    col[...] = bord
    col = lerp(col, np.array(fond, np.float32), I[..., None])
    col = lerp(col, np.array(motif, np.float32), Mo[..., None])
    yy, xx = np.mgrid[0:M.shape[0], 0:M.shape[1]]
    g = np.hypot(xx / S - gl[0], yy / S - gl[1]) < gl[2]
    col[g & (Mo > 0.5)] = reflet
    # ombre de la hampe (pli près du bâton)
    col *= (0.82 + 0.18 * np.clip(xx / S / 0.5, 0, 1))[..., None]
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H_px), Image.LANCZOS), np.float32)
    al = np.array(Image.fromarray((M * 255).astype(np.uint8), "L").resize((W, H_px), Image.LANCZOS)) > 110
    return (rgb, al, np.zeros(al.shape, bool)), FW, FH


def img_flat(c0, c1, w=24, h=12, stripes=False):
    yy, xx = np.mgrid[0:h, 0:w]
    q = np.abs((yy + 0.5) / h - 0.5) * 2
    col = lerp(np.array(c0, np.float32), np.array(c1, np.float32), (q ** 1.4)[..., None])
    if stripes:
        col *= (0.92 + 0.08 * np.sin(xx * 0.9 + yy * 0.3))[..., None]
    return col, np.ones((h, w), bool), np.zeros((h, w), bool)


IMGS = {}       # nom -> (rgb, alpha, joue)
for nom_s, sv in SAVEURS.items():
    for k, seg in enumerate(SEGS):
        im, cw, rh = img_ring(sv, seg)
        IMGS[f"{nom_s}_anneau{k}"] = im
        seg.setdefault("cw", cw)
    IMGS[f"{nom_s}_haut"], CAP_T = img_cap(sv, True)
    IMGS[f"{nom_s}_bas"], CAP_B = img_cap(sv, False)
IMGS["fanion_choco"], FW, FH = img_fanion("choco")
IMGS["fanion_vanille"], _, _ = img_fanion("vanille")
IMGS["bois"] = img_flat((222, 182, 128), (150, 104, 62), 32, 10, stripes=True)
IMGS["perle_fraise"] = img_flat((255, 170, 190), (226, 104, 136), 10, 10)
IMGS["perle_choco"] = img_flat((150, 96, 66), (84, 48, 34), 10, 10)
IMGS["ame_vanille"] = img_flat((246, 236, 216), (220, 204, 180), 10, 10)
IMGS["ame_fraise"] = img_flat((255, 222, 230), (232, 182, 196), 10, 10)

UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def atlas():
    items = sorted(((n, im[0].shape[1], im[0].shape[0]) for n, im in IMGS.items()), key=lambda it: -it[2])
    x = y = shelf = 0
    for n, w, h in items:
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, "atlas plein"
        UV[n] = (x, y, x + w, y + h)
        x += w + 1
        shelf = max(shelf, h)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, (rgb, al, joue) in IMGS.items():
        u0, v0, u1, v1 = UV[n]
        rgb = rgb.copy()
        if al.any():
            rgb[~al] = rgb[al].mean(axis=0)
        tex[v0:v1, u0:u1, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        tex[v0:v1, u0:u1, 3] = al * 255
        if "anneau" in n or n.endswith("_haut") or n.endswith("_bas"):
            # lueur : fond additif très sombre, minuscule touche sur les joues
            e = np.zeros(rgb.shape, np.float32)
            e[...] = (12, 9, 11)
            e[joue] = (46, 16, 26)
            tex_e[v0:v1, u0:u1, :3] = (e * al[..., None]).astype(np.uint8)
            tex_e[v0:v1, u0:u1, 3] = al * 255
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
    return b64


tex_b64, tex_e_b64 = atlas()

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
    assert name not in groups and len(name) <= 64
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


def plate(g, name, c, X, Y, w, h, uv, th=TH):
    """Plaque fine : contour par l'alpha, tranches transparentes. u suit X, le haut de l'image est +Y, la face south regarde X x Y."""
    X, Y = unit(np.asarray(X, float)), unit(np.asarray(Y, float))
    u0, v0, u1, v1 = uv
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
         {"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def box(g, name, c, X, Y, w, h, d, tile):
    """Vrai volume, texturé sur 6 faces."""
    X, Y = unit(np.asarray(X, float)), unit(np.asarray(Y, float))
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    cube(g, name, c - (w / 2, h / 2, d / 2), c + (w / 2, h / 2, d / 2), c, euler(R_), {f: list(UV[tile]) for f in ("north", "south", "east", "west", "up", "down")})


def baton(g, name, p, q, r, tile):
    """Bâton octogonal : deux cubes le long de p→q, l'un tourné de 45° autour de l'axe."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    Y = unit(q - p)
    ref = V(1, 0, 0)
    X = unit(ref - (ref @ Y) * Y)
    Z = np.cross(X, Y)
    L = np.linalg.norm(q - p)
    c45 = math.cos(math.pi / 4)
    box(g, name, (p + q) / 2, X, Y, 2 * r, L, 2 * r, tile)
    box(g, name + "o", (p + q) / 2, c45 * X + c45 * Z, Y, 2 * r * 0.97, L - 0.06, 2 * r * 0.97, tile)


def guimauve(g, tag, sv_nom, C):
    """Coque de 12 côtés x 4 anneaux + 2 couvercles, âme octogonale. n(phi) = (sin phi, 0, -cos phi) : phi = 0 regarde l'avant."""
    up = V(0, 1, 0)
    for k, seg in enumerate(SEGS):
        w, L = ring_geom(seg)
        u0, v0, u1, v1 = UV[f"{sv_nom}_anneau{k}"]
        cw = seg["cw"]
        dr, dh = seg["r1"] - seg["r0"], seg["h1"] - seg["h0"]
        for i in range(NS):
            p = phi_i(i)
            n = V(math.sin(p), 0, -math.cos(p))
            X = np.cross(up, n)
            Y = unit(dr * n + dh * up)
            N = np.cross(X, Y)
            mid = C + n * (seg["r0"] + seg["r1"]) / 2 + up * (seg["h0"] + seg["h1"]) / 2 - N * TH / 2
            plate(g, f"peau{k}_{i}_{tag}", mid, X, Y, w, L, (u0 + i * cw, v0, u0 + (i + 1) * cw, v1))
    plate(g, f"dessus_{tag}", C + up * (H_ - TH / 2), V(1, 0, 0), V(0, 0, -1), CAP_T, CAP_T, UV[f"{sv_nom}_haut"])
    plate(g, f"dessous_{tag}", C + up * (TH / 2), V(1, 0, 0), V(0, 0, 1), CAP_B, CAP_B, UV[f"{sv_nom}_bas"])
    # âme : coin du carré à 1,2·√2 = 1,70 < face intérieure de la coque (1,70 à 1,75 selon l'angle)
    c45 = math.cos(math.pi / 4)
    box(g, f"ame_{tag}", C + up * 1.45, V(1, 0, 0), up, 2.3, 1.9, 2.3, f"ame_{sv_nom}")
    box(g, f"ameo_{tag}", C + up * 1.45, V(c45, 0, c45), up, 2.26, 1.84, 2.26, f"ame_{sv_nom}")


PIQUES, GUIMAUVES, FANIONS = [], [], []


def epaulette(s, tag, sv_nom, fanion, perle):
    arm = group("left_arm" if s < 0 else "right_arm", V(s * 5, 22, 0))
    C = V(s * CX, Y0, 0)
    gm = group(f"guimauve_{tag}", C, parent=arm)
    guimauve(gm, tag, sv_nom, C)
    GUIMAUVES.append((gm, s))
    # pique : plantée dans le dessus, un peu vers l'extérieur et l'arrière
    base = C + V(s * 0.15, 1.2, 0.1)
    top = C + V(s * 0.7, H_ + 3.0, 0.45)
    emerge = C + V(s * (0.15 + 0.55 * (H_ - 1.2) / (H_ + 1.8)), H_, 0.1 + 0.35 * (H_ - 1.2) / (H_ + 1.8))
    gp = group(f"pique_{tag}", emerge, parent=arm)
    baton(gp, f"baton_{tag}", base, top, 0.19, "bois")
    ax = unit(top - base)
    box(gp, f"perle_{tag}", top + ax * 0.2, V(1, 0, 0), ax, 0.56, 0.56, 0.56, perle)
    PIQUES.append((gp, s))
    # fanion : hampe contre le bâton, du haut du bâton vers le bas ; pivot sur l'axe du bâton à mi-hauteur
    yf = top[1] - 0.12 - FH / 2
    hinge = base + ax * ((yf - base[1]) / ax[1])
    gf = group(f"fanion_{tag}", hinge, parent=gp)
    out = V(s, 0, 0)
    plate(gf, f"drapeau_{tag}", hinge + out * (FW / 2 + 0.16) + V(0, 0, 0.0), out, V(0, 1, 0), FW, FH, UV[fanion])
    FANIONS.append((gf, s))


epaulette(1, "r", "vanille", "fanion_choco", "perle_fraise")
epaulette(-1, "l", "fraise", "fanion_vanille", "perle_choco")


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node("right_arm"), bone_node("left_arm")]

# ------------------------------------------------------------------ animations
# MIROIR D'AXES : seul endroit à toucher si la convention change (guide, section 3).
# +X : le haut bascule vers l'arrière. +Y : le côté droit avance. +Z : le côté droit monte.
def pique_rot(s, out, back):
    """out > 0 : le haut de la pique part vers l'extérieur ; back > 0 : vers l'arrière."""
    return back, 0.0, -s * out


def fanion_rot(s, trail, lift):
    """trail > 0 : la pointe du fanion part vers l'arrière ; lift > 0 : elle monte."""
    return 0.0, -s * trail, s * lift


def squash(k):
    """k > 0 : étirée en hauteur ; volume conservé."""
    return 1 / math.sqrt(1 + k), 1 + k, 1 / math.sqrt(1 + k)


def bump(t, a, b, c, d):
    def s_(x, a, b):
        if x <= a:
            return 0.0
        if x >= b:
            return 1.0
        u = (x - a) / (b - a)
        return u * u * (3 - 2 * u)
    return s_(t, a, b) * (1 - s_(t, c, d))


def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 3)), "y": str(round(v[1] + 0.0, 3)), "z": str(round(v[2] + 0.0, 3))}],
            "time": round(t, 3), "interpolation": "linear"}


def anim(name, length, tracks, kps=20, loop="loop"):
    n = max(8, int(round(length * kps)))
    times = [i * length / n for i in range(n + 1)]
    A = {}
    for g, chans in tracks.items():
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(ch, t, f(t)) for ch, f in chans.items() for t in times]}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


def state(name, L, cyc, k0, kA, hop, back0, leanA, out0, trail0, flut, fcyc, lift0, liftA, extra=None):
    """cyc rebonds par boucle (au rythme du pas) ; squash k0 + kA ; saut hop px ; pique : back0/out0 + leanA ;
    fanion : trail0 + flut (fcyc battements par boucle), lift0 + liftA (suit le rebond avec retard)."""
    ex = extra or (lambda t: 0.0)
    tr = {}
    for (gm, s), (gp, _), (gf, _) in zip(GUIMAUVES, PIQUES, FANIONS):
        ph = 0.0 if s > 0 else 0.08

        def k_(t, ph=ph):
            return k0 - kA * math.cos(TAU * (cyc * t / L - ph)) + ex(t)

        def hop_(t, ph=ph):
            return hop * (0.5 - 0.5 * math.cos(TAU * (cyc * t / L - ph)))

        tr[gm] = {"scale": lambda t, k_=k_: squash(k_(t)), "position": lambda t, hop_=hop_: (0, hop_(t), 0)}
        tr[gp] = {"position": lambda t, k_=k_, hop_=hop_: (0, hop_(t) + H_ * (squash(k_(t))[1] - 1), 0),
                  "rotation": lambda t, s=s, ph=ph: pique_rot(s, out0 + 0.5 * leanA * math.sin(TAU * (cyc * t / L - ph - 0.12)),
                                                              back0 + leanA * math.sin(TAU * (cyc * t / L - ph - 0.12)))}
        tr[gf] = {"rotation": lambda t, s=s, ph=ph: fanion_rot(s, trail0 + flut * math.sin(TAU * (fcyc * t / L - ph - 0.2)),
                                                               lift0 + liftA * math.cos(TAU * (cyc * t / L - ph - 0.25)))}
    return anim(name, L, tr)


def baille(t):
    """Idle : petit trémoussement joyeux vers 5 s (2,5 rebonds rapides), nul hors de la fenêtre."""
    return 0.06 * bump(t, 4.9, 5.15, 5.9, 6.4) * math.sin(TAU * 2.5 * (t - 4.9))


ANIMS = [
    state("idle", 8.0, 2, 0.0, 0.025, 0.0, 0.0, 1.5, 0.0, 8, 5, 4, 0, 3, extra=baille),
    state("walk", 1.6, 2, 0.0, 0.05, 0.15, 2.0, 3.0, 0.0, 16, 8, 4, 0, 6),
    state("run", 1.0, 2, 0.0, 0.08, 0.35, 8.0, 5.0, 0.0, 42, 14, 6, 4, 10),
    state("sneak", 3.0, 1, -0.12, 0.02, 0.0, 6.0, 1.0, 10.0, 6, 3, 2, -24, 2),
    state("fly", 2.4, 1, 0.03, 0.04, 0.0, 10.0, 2.0, 0.0, 46, 15, 8, 4, 5),
    state("glide", 3.6, 1, -0.06, 0.02, 0.0, 0.0, 1.0, 3.0, 12, 18, 12, -48, 4),
    state("fall", 1.2, 2, 0.07, 0.02, 0.0, -4.0, 1.5, 0.0, 6, 12, 4, 34, 5),
    state("swim", 3.0, 1, -0.05, 0.03, 0.0, 3.0, 2.0, 2.0, 10, 8, 4, -40, 5),
]

atk = lambda t: bump(t, 0.0, 0.1, 0.24, 0.68)
hu = lambda t: bump(t, 0.0, 0.07, 0.18, 0.7)
vib = lambda t: math.sin(TAU * t * 5 / 0.8)
tr_a, tr_h = {}, {}
for (gm, s), (gp, _), (gf, _) in zip(GUIMAUVES, PIQUES, FANIONS):
    ka = lambda t: 0.07 * atk(t) * math.cos(TAU * t * 3 / 0.8)
    kh = lambda t: -0.15 * hu(t) * math.cos(TAU * t * 4 / 0.8)
    for tr, k_ in ((tr_a, ka), (tr_h, kh)):
        tr[gm] = {"scale": lambda t, k_=k_: squash(k_(t))}
        tr[gp] = {"position": lambda t, k_=k_: (0, H_ * (squash(k_(t))[1] - 1), 0)}
    tr_a[gf] = {"rotation": lambda t, s=s: fanion_rot(s, 26 * atk(t), 8 * atk(t) * vib(t))}
    tr_h[gf] = {"rotation": lambda t, s=s: fanion_rot(s, 14 * hu(t), 24 * vib(t) * hu(t))}
    tr_h[gp]["rotation"] = lambda t, s=s: pique_rot(s, 4 * vib(t + 0.05) * hu(t), -5 * hu(t))
ANIMS += [anim("attack", 0.8, tr_a, kps=25, loop="once"), anim("hurt", 0.8, tr_h, kps=25, loop="once")]

assert 60 <= len(elements) <= 150, f"budget : {len(elements)} cubes"
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
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      f"densité {DENS:.0f} texels/px ; {len(IMGS)} images")
