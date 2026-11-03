"""Halo donut : un beignet glacé rose fraise, vermicelles multicolores, qui flotte à plat au-dessus de la tête. Design original, ensemble « Kawaii ».
Écrit halo_donut.png, halo_donut_e.png et .build/halo_donut_brut.bbmodel à côté de ce script.

Construction (leçons « Anneau, halo ») : le dessus est UNE seule plaque, anneau de glaçage découpé par alpha (aucun segment, donc ni pointillés
ni créneaux sous _e). Le volume rond vient d'une coque fermée à section octogonale autour de la plaque : chanfrein haut glacé avec coulures,
paroi extérieure dorée à bande crème, chanfrein bas doré, plaque du dessous (pâte) et paroi du trou. Les segments de la coque se chevauchent
(aucun jour) et ne portent que du sombre dans _e : la lueur reste sur la plaque unique du dessus, en anneau plus étroit.
Tout est dans head > donut (inclinaison, flottement) > donut_tour (rotation sur lui-même).
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "halo_donut"
AVEC_E = True       # calque _e embarqué en seconde texture (correctif du clignotement annoncé le 2026-11-03, à vérifier en jeu)
TEX = 256
SS = 4
TAU = 2 * math.pi

# ------------------------------------------------------------------ dimensions (px), centre du donut
CY = 35.0                   # centre : dessous à 34, dessus à 36 (la tête culmine à 32)
R_OUT, R_HOLE = 4.0, 1.5    # paroi extérieure (apothème), paroi du trou (apothème)
R_TOP = 3.37                # bord intérieur des chanfreins
Y_TOP, Y_WALL = 1.0, 0.35   # dessus / dessous à ±1, paroi verticale de -0.35 à +0.35
CH_Y = 0.97                 # les chanfreins s'arrêtent sous les plaques : rien ne perce le glaçage
N_OUT, N_IN = 16, 10
HP = 3.64                   # demi-côté des plaques
HOLE_TEX = 1.45             # trou découpé dans les plaques, plus petit que la paroi : aucun jour vu de dessus
GL_MIN, GL_AMP = 3.47, 0.14  # rayon du glaçage : ≥ 3.44 (coins du polygone des chanfreins), vagues de 9 lobes

# ------------------------------------------------------------------ couleurs (bases poussées vers le blanc : la nuit chaude vire au saumon)
def C(*v):
    return np.array(v, np.float32)


PINK_L, PINK_M, PINK_D, PINK_RIM = C(255, 236, 244), C(255, 200, 222), C(238, 150, 186), C(214, 112, 156)
DOUGH_CREAM, DOUGH_L, DOUGH_M, DOUGH_D, DOUGH_SH = C(255, 240, 210), C(246, 208, 140), C(232, 176, 100), C(196, 132, 68), C(160, 98, 50)
SPRINKLES = [C(120, 222, 192), C(120, 186, 248), C(255, 226, 104), C(186, 150, 248), C(255, 255, 255), C(255, 156, 112)]


def lerp(a, b, k):
    return a + (b - a) * k


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def finish(col, alpha, W, H):
    """Réduit la peinture sur-échantillonnée : alpha 0/255, couleur moyenne hors silhouette."""
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    solid = np.array(Image.fromarray((alpha * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = rgb
    if solid.any() and not solid.all():
        arr[~solid, :3] = rgb[solid].mean(axis=0).astype(np.uint8)
    arr[..., 3] = solid * 255
    return arr


def down(arr, W, H):
    return np.array(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))


def grid(W, H, x0, x1, y0, y1):
    """Grille sur-échantillonnée en coordonnées modèle."""
    w, h = W * SS, H * SS
    return np.meshgrid(x0 + (np.arange(w) + 0.5) / w * (x1 - x0), y0 + (np.arange(h) + 0.5) / h * (y1 - y0))


def glaze_radius(th):
    return GL_MIN + GL_AMP * (0.5 + 0.5 * np.cos(9 * th + 0.6 * np.sin(4 * th)))


def glaze_top(W=120):
    """Plaque du dessus : anneau de glaçage, bord en vagues rondes, ombré en tore, vermicelles ≥ 3 texels. Renvoie texture et calque _e."""
    gx, gz = grid(W, W, -HP, HP, -HP, HP)
    r, th = np.hypot(gx, gz), np.arctan2(gz, gx)
    ro = glaze_radius(th)
    ring = (r > HOLE_TEX) & (r < ro)
    q = (r - HOLE_TEX) / (ro - HOLE_TEX)                  # 0 au trou, 1 au bord
    col = np.empty(gx.shape + (3,), np.float32)
    col[...] = PINK_M
    col = lerp(col, PINK_L, (np.clip(1 - np.abs(q - 0.42) / 0.30, 0, 1) ** 1.5)[..., None] * 0.85)   # crête du tore
    col = lerp(col, PINK_D, smooth((q - 0.72) / 0.28)[..., None] * 0.7)                            # retombée vers le bord
    col = lerp(col, PINK_D, smooth((0.22 - q) / 0.22)[..., None] * 0.8)                            # bord du trou
    dist_out = (ro - r) * W / (2 * HP)                    # texels jusqu'au bord
    col = lerp(col, PINK_RIM, np.clip(1 - dist_out / 3.0, 0, 1)[..., None] * 0.75)                 # liseré du bord, 3 texels
    col = lerp(col, PINK_RIM, np.clip(1 - (r - HOLE_TEX) * W / (2 * HP) / 3.0, 0, 1)[..., None] * 0.75)
    # reflets doux (deux petites virgules blanches)
    for cx, cz, a in ((-1.6, -1.5, 0.55), (1.7, 1.3, 0.4)):
        d = np.hypot((gx - cx) / 0.75, (gz - cz) / 0.32)
        col = lerp(col, C(255, 255, 255), (d < 1)[..., None] * a)
    # vermicelles : gélules arrondies, 0,24 px de large (≈ 4 texels), répartis sans se toucher
    ec = np.zeros(gx.shape + (3,), np.float32)
    rng = np.random.default_rng(7)
    placed = []
    tries = 0
    while len(placed) < 24 and tries < 4000:
        tries += 1
        rr = rng.uniform(1.95, 3.15)
        a = rng.uniform(0, TAU)
        px, pz = rr * math.cos(a), rr * math.sin(a)
        if any(math.hypot(px - x, pz - z) < 0.78 for x, z in placed):
            continue
        placed.append((px, pz))
        ang = rng.uniform(0, math.pi)
        L, Wd = 0.62, 0.24
        ux, uz = math.cos(ang), math.sin(ang)
        s = (gx - px) * ux + (gz - pz) * uz
        t = -(gx - px) * uz + (gz - pz) * ux
        sc = np.clip(s, -(L - Wd) / 2, (L - Wd) / 2)
        dd = np.hypot(s - sc, t) / (Wd / 2)
        m = (dd < 1) & ring
        c = SPRINKLES[len(placed) % len(SPRINKLES)]
        shade = lerp(c * 0.78, np.minimum(c * 1.08 + 18, 255), smooth((-t / (Wd / 2) + 1) / 2)[..., None])   # moitié éclairée, moitié ombrée
        col = np.where(m[..., None], shade, col)
        ec = np.where(m[..., None], c * 0.22, ec)
    # calque _e : anneau plus étroit que le glaçage, fond très sombre, fine ligne lumineuse au milieu
    e_ring = (r > 1.85) & (r < 3.2)
    base = np.where(ec.sum(-1, keepdims=True) > 0, ec, C(30, 14, 22))
    line = np.clip(1 - np.abs(r - 2.55) / 0.16, 0, 1)
    base = lerp(base, C(205, 132, 170), (line ** 0.7)[..., None])
    out = finish(col, ring, W, W)
    eo = down(base, W, W)
    em = np.array(Image.fromarray((e_ring * 255).astype(np.uint8), "L").resize((W, W), Image.LANCZOS)) > 110
    e = np.dstack([eo, em * out[..., 3] // 255 * 255]).astype(np.uint8)
    return out, e


def dough_bottom(W=112):
    """Plaque du dessous : pâte dorée, plus claire vers le milieu de l'anneau, bords brunis."""
    gx, gz = grid(W, W, -HP, HP, -HP, HP)
    r = np.hypot(gx, gz)
    ro = GL_MIN - 0.02
    ring = (r > HOLE_TEX) & (r < ro)
    q = (r - HOLE_TEX) / (ro - HOLE_TEX)
    col = np.empty(gx.shape + (3,), np.float32)
    col[...] = DOUGH_M
    col = lerp(col, DOUGH_L, np.clip(1 - np.abs(q - 0.5) / 0.35, 0, 1)[..., None] * 0.9)
    col = lerp(col, DOUGH_D, smooth((q - 0.8) / 0.2)[..., None] * 0.7 + smooth((0.18 - q) / 0.18)[..., None] * 0.7)
    rng = np.random.default_rng(3)
    col = col * (1 + 0.035 * rng.standard_normal(gx.shape))[..., None]
    return finish(col, ring, W, W)


WT = 1.66   # largeur physique d'un segment de coque (px)


def drip_edge(gx, base, drips, wd=0.16):
    """Bord inférieur du glaçage : bande de hauteur base, coulures rondes (u en fraction, L en px) raccordées par un congé."""
    edge = base + 0.03 * np.sin(gx * TAU * 2 + 1.3)
    for u, L in drips:
        dx = np.abs(gx - u) * WT
        lobe = np.where(dx < wd, L - wd + np.sqrt(np.clip(wd * wd - dx * dx, 0, None)), 0)
        k = np.clip((2.3 * wd - dx) / (1.3 * wd), 0, 1)
        fil = np.where(dx < 2.3 * wd, edge + (L - wd - edge) * k ** 3, 0)     # congé concave : la coulure naît en douceur
        edge = np.maximum(edge, np.maximum(lobe, np.minimum(fil, L)))
    return edge


def wall_tile(drips, W=34, H=17, h_px=0.82):
    """Paroi extérieure : le glaçage du chanfrein déborde en haut et coule en gouttes rondes ; pâte dorée claire au milieu,
    plus brune en bas ; ombre de recouvrement sous le glaçage."""
    gx, gy = grid(W, H, 0, 1, 0, h_px)          # gy : 0 en haut
    yy = gy / h_px
    col = np.empty(gx.shape + (3,), np.float32)
    col[...] = DOUGH_L
    col = lerp(col, DOUGH_CREAM, smooth(1 - np.abs(yy - 0.55) / 0.30)[..., None] * 0.45)
    col = lerp(col, DOUGH_M, smooth((yy - 0.7) / 0.3)[..., None])
    edge = drip_edge(gx, 0.13, drips)
    m = gy < edge
    col = lerp(col, DOUGH_SH, (np.clip(1 - (gy - edge) / 0.08, 0, 1) * ~m)[..., None] * 0.6)
    gl = lerp(PINK_M, PINK_D, smooth(gy / 0.5)[..., None] * 0.6)
    gl = lerp(gl, PINK_RIM, np.clip(1 - (edge - gy) / 0.07, 0, 1)[..., None] * 0.55)
    col = np.where(m[..., None], gl, col)
    return finish(col, np.ones(gx.shape, bool), W, H)


def chamfer_up_tile(sprinkle, W=34, H=20, L_px=0.96):
    """Chanfrein haut : entièrement glacé (le rose se lit à hauteur des yeux), un vermicelle pour lier au dessus."""
    gx, gy = grid(W, H, 0, 1, 0, L_px)
    col = lerp(PINK_L[None, None], PINK_M[None, None], smooth(gy / 0.45)[..., None])
    col = lerp(col, PINK_M * 0.97, smooth((gy - 0.5) / 0.46)[..., None])
    if sprinkle:
        (u, v, ang), c = sprinkle
        ux, uz = math.cos(ang), math.sin(ang)
        px_, py_ = gx * WT, gy
        s_ = (px_ - u * WT) * ux + (py_ - v) * uz
        t_ = -(px_ - u * WT) * uz + (py_ - v) * ux
        sc = np.clip(s_, -0.19, 0.19)
        mm = np.hypot(s_ - sc, t_) < 0.12
        shade = lerp(c * 0.78, np.minimum(c * 1.08 + 18, 255), smooth((-t_ / 0.12 + 1) / 2)[..., None])
        col = np.where(mm[..., None], shade, col)
    return finish(col, np.ones(gx.shape, bool), W, H)


def chamfer_low_tile(W=34, H=20):
    """Chanfrein bas : pâte dorée, plus brune vers le bas (haut de l'image = côté paroi)."""
    gx, gy = grid(W, H, 0, 1, 0, 1)
    col = lerp(DOUGH_L[None, None], DOUGH_D[None, None], smooth(gy * 0.9)[..., None])
    rng = np.random.default_rng(5)
    col = col * (1 + 0.03 * rng.standard_normal(gx.shape))[..., None]
    return finish(col, np.ones(gx.shape, bool), W, H)


def flat_tile(c, W=8, H=8):
    a = np.zeros((H, W, 4), np.uint8)
    a[..., :3] = c
    a[..., 3] = 255
    return a


UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_cur = [0, 0, 0]


def place(name, im, em=None):
    h, w = im.shape[:2]
    if _cur[0] + w > TEX:
        _cur[:] = [0, _cur[1] + _cur[2] + 2, 0]
    x, y = _cur[0], _cur[1]
    assert y + h <= TEX - 6, "atlas plein"
    tex[y:y + h, x:x + w] = im
    if em is not None:
        tex_e[y:y + h, x:x + w] = em
    else:   # hors glaçage : additif quasi nul, opaque là où la texture l'est
        tex_e[y:y + h, x:x + w, :3] = (18, 12, 8)
        tex_e[y:y + h, x:x + w, 3] = im[..., 3]
    UV[name] = (x, y, x + w, y + h)
    _cur[0] += w + 2
    _cur[2] = max(_cur[2], h)


place("glaze", *glaze_top())
place("bottom", dough_bottom())
# variantes : coulures sur la paroi (u, longueur en px), vermicelle sur le chanfrein ((u, v, angle), couleur)
DRIPS = {
    "a": ([(0.30, 0.50)], ((0.70, 0.40, 0.5), SPRINKLES[0])),
    "b": ([(0.22, 0.34), (0.68, 0.56)], None),
    "c": ([(0.60, 0.62)], ((0.25, 0.55, 2.4), SPRINKLES[1])),
    "d": ([(0.45, 0.40)], ((0.78, 0.30, 1.2), SPRINKLES[2])),
}
for k, (wd, spr) in DRIPS.items():
    place(f"ch_up_{k}", chamfer_up_tile(spr))
    place(f"wall_{k}", wall_tile(wd))
place("ch_low", chamfer_low_tile())
place("dough", flat_tile((232, 176, 100)))
place("dough_d", flat_tile((196, 132, 68)))
place("pink", flat_tile((250, 196, 218)))

CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC
assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
gu0, gv0, gu1, gv1 = UV["glaze"]
_mask = np.ones(TEX * TEX, bool).reshape(TEX, TEX)
_mask[gv0:gv1, gu0:gu1] = False
assert tex_e[_mask][..., :3].max() <= 40, "calque _e : rien de vif hors du glaçage"
assert tex_e[..., :3].max() <= 210
_b64 = []
for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(fn, optimize=True)
    _buf = io.BytesIO()
    im_.save(_buf, "PNG", optimize=True)
    _b64.append("data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode())
tex_b64, tex_e_b64 = _b64

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
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "rotation": [0, 0, 0]}
    return name


def cube(g, name, c, size, X, Y, faces):
    """Cube centré en c, axes locaux X, Y (orthonormés), Z = X × Y ; face south = +Z local."""
    c, size = np.asarray(c, float), np.asarray(size, float)
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    rot = euler(R_)
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in c - size / 2], "to": [round(float(v), 3) for v in c + size / 2],
         "origin": [round(float(v), 3) for v in c], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def faces_with(south, other):
    return {"south": list(UV[south]), "north": list(UV[other]), "east": list(UV[other]), "west": list(UV[other]), "up": list(UV[other]), "down": list(UV[other])}


DONUT = group("donut", [0, CY, 0])
TOUR = group("donut_tour", [0, CY, 0], parent=DONUT)
UP = V(0, 1, 0)
O = V(0, CY, 0)

# Plaque du dessus : glaçage, une seule plaque, face up + face down (lèvre de glaçage vue d'en dessous au bord)
cube(TOUR, "glacage", O + V(0, Y_TOP - 0.15, 0), (2 * HP, 0.3, 2 * HP), V(1, 0, 0), UP,
     {"up": [gu0, gv0, gu1, gv1], "down": [gu0, gv1, gu1, gv0], "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR})
bu0, bv0, bu1, bv1 = UV["bottom"]
cube(TOUR, "dessous", O + V(0, -Y_TOP + 0.15, 0), (2 * HP, 0.3, 2 * HP), V(1, 0, 0), UP,
     {"down": [bu0, bv0, bu1, bv1], "up": [bu0, bv1, bu1, bv0], "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR})

# Coque extérieure : 16 segments, section octogonale (chanfrein haut, paroi, chanfrein bas). Segments chevauchés : aucun jour.
W_OUT = 2 * R_OUT * math.tan(math.pi / N_OUT) + 0.07
assert abs(W_OUT - WT) < 0.02
SEQ = "abcdbadcabdcbacd"
L_CH = math.hypot(R_OUT - R_TOP, CH_Y - Y_WALL)
for k in range(N_OUT):
    th = TAU * (k + 0.5) / N_OUT
    n = V(math.cos(th), 0, math.sin(th))
    v = SEQ[k]
    # paroi verticale
    Z = n
    X = np.cross(UP, Z)
    fw = faces_with(f"wall_{v}", f"wall_{v}")
    fw["up"], fw["down"] = list(UV["pink"]), list(UV["dough"])     # bords qui dépassent des chanfreins : couleur du voisin
    cube(TOUR, f"paroi{k}", O + n * (R_OUT - 0.25), (W_OUT, 2 * Y_WALL + 0.12, 0.5), X, UP, fw)
    # chanfrein haut : de (R_OUT, Y_WALL) à (R_TOP, CH_Y)
    p0, p1 = n * R_OUT + UP * Y_WALL, n * R_TOP + UP * CH_Y
    Yc = unit(p1 - p0)
    Zc = unit(np.cross(np.cross(UP, n), Yc))
    Xc = np.cross(Yc, Zc)
    cube(TOUR, f"chanfrein_h{k}", O + (p0 + p1) / 2 - Zc * 0.22, (W_OUT, L_CH + 0.04, 0.44), Xc, Yc, faces_with(f"ch_up_{v}", f"ch_up_{v}"))
    # chanfrein bas : de (R_TOP, -CH_Y) à (R_OUT, -Y_WALL), haut de l'image côté paroi
    p0, p1 = n * R_TOP - UP * CH_Y, n * R_OUT - UP * Y_WALL
    Yc = unit(p1 - p0)
    Zc = unit(np.cross(np.cross(UP, n), Yc))
    Xc = np.cross(Yc, Zc)
    cube(TOUR, f"chanfrein_b{k}", O + (p0 + p1) / 2 - Zc * 0.22, (W_OUT, L_CH + 0.04, 0.44), Xc, Yc, faces_with("ch_low", "ch_low"))

# Paroi du trou : 10 segments tournés vers le centre, pâte plus sombre (le creux)
W_IN = 2 * R_HOLE * math.tan(math.pi / N_IN) + 0.06
for k in range(N_IN):
    th = TAU * (k + 0.5) / N_IN
    n = V(math.cos(th), 0, math.sin(th))
    Z = -n
    X = np.cross(UP, Z)
    cube(TOUR, f"trou{k}", O + n * (R_HOLE + 0.2), (W_IN, 2 * Y_TOP - 0.1, 0.4), X, UP, faces_with("dough_d", "dough"))


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "head", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone(DONUT)]}]

# ------------------------------------------------------------------ animations
# Repères du guide, section 3 : rotation +X = le haut part vers l'arrière, donc le bord avant du donut se soulève ;
# +Z = le côté droit (+X) monte. Position +Y = monte. Le tour sur lui-même est porté par donut_tour, l'inclinaison par donut :
# le plan incliné tourne sans que l'inclinaison ne tourne avec lui.
L = 8.0     # toutes les boucles : 8 s, un tour (45°/s), même vitesse dans tous les états


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 3)), "y": str(round(y + 0.0, 3)), "z": str(round(z + 0.0, 3))}],
            "time": round(t, 3), "interpolation": "linear"}


def S(T, amp, ph=0.0, off=0.0):
    return lambda t: off + amp * math.sin(TAU * t / T + math.radians(ph))


def K(v):
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


def anim(name, length, rx, rz, py, turns=1, rate=8, loop="loop"):
    n = int(round(length * rate))
    times = [i * length / n for i in range(n + 1)]   # linéaire : dernier keyframe = premier (à 360°·k près)
    A = {groups[DONUT]["uuid"]: {"name": DONUT, "type": "bone",
                                 "keyframes": [kf("rotation", t, rx(t), 0, rz(t)) for t in times] + [kf("position", t, 0, py(t), 0) for t in times]}}
    if turns:
        A[groups[TOUR]["uuid"]] = {"name": TOUR, "type": "bone", "keyframes": [kf("rotation", t, 0, 360.0 * turns * t / length, 0) for t in times]}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


# idle : flotte doucement (±0,35 px, 4 s), oscille à peine
idle = anim("idle", L, S(8, 2.0), S(8, 2.0, 90), S(4, 0.35))
# walk : petit bond à chaque pas (1,6 s le cycle, deux pas), bord avant un peu soulevé, balancement latéral
walk = anim("walk", L, S(0.8, 1.2, 90, 3), S(1.6, 2.5), S(0.8, 0.22, 0, 0.1), rate=10)
# run : traîne vers l'arrière (bord avant relevé), rebond vif au pas
run = anim("run", L, S(0.5, 1.5, 90, 9), S(1.0, 3.0), S(0.5, 0.25, 0, 0.2), rate=16)
# sneak : se tasse vers la tête, presque immobile
sneak = anim("sneak", L, S(8, 1.0, 0, -2), S(8, 1.0, 90), S(4, 0.15, 0, -0.8))
# fly : plus haut, roulis ample et lent
fly = anim("fly", L, S(4, 3.0, 0, 8), S(8, 5.0), S(2, 0.4, 0, 0.6))
# glide : couché avec le corps, traîne nettement, flottement lent
glide = anim("glide", L, S(4, 2.0, 0, 14), S(8, 3.0), S(4, 0.3, 0, 0.3))
# fall : décolle un peu de la tête (inertie), dodeline
fall = anim("fall", L, S(2, 4.0), S(2, 4.0, 90), S(2, 0.3, 0, 1.0))
# hurt : sursaut vers le haut, bascule vers l'arrière et tremblement amorti, retour à 0 ; seul le groupe donut
hu = lambda t: bump(t, 0.0, 0.08, 0.22, 0.75)
tr = lambda t: math.sin(TAU * t * 6 / 0.8) * (1 - sm(t, 0.15, 0.7))
hurt = anim("hurt", 0.8, lambda t: 12 * hu(t) + 3 * tr(t), lambda t: 5 * tr(t), lambda t: 1.6 * hu(t), turns=0, rate=20, loop="once")

ANIMS = [idle, walk, run, sneak, fly, glide, fall, hurt]
assert 30 <= len(elements) <= 100, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko")
