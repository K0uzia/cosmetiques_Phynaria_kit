"""Aura cœurs-nuage (ensemble « Nuage Guimauve ») : 5 cœurs dodus en orbite lente autour du torse, un mince anneau de nuages
qui tourne au sol, et des petits cœurs-particules (rose, lavande, crème) qui montent autour du joueur. Design original.
Écrit aura_coeurs_nuage.png, aura_coeurs_nuage_e.png et .build/aura_coeurs_nuage_brut.bbmodel à côté de ce script.

Cœur en orbite : peau ronde découpée par alpha (deux plaques, recto et verso) autour d'une âme pleine plus étroite (losange + bloc des lobes).
Chaîne : orbite (inclinaison fixe) > choc (animé par hurt seul) > spin (exactement 360° par boucle) > c<k> (flottement, battement).
Anneau : une seule plaque de 0,3 px découpée par alpha (recette anneau), symétrie d'ordre 12 : un saut de phase entre états ne se voit pas.
Il est replié (scale ~0) dans les états où le corps n'est plus debout au-dessus des pieds (accroupi, élytres, nage, sommeil, monture).
Particules (guide, section 5 ter) : un seul cube de 0,3 px, face up seule, cœur peint ; animation _fall = redressé, tourne comme une pièce, bat.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "aura_coeurs_nuage"
AVEC_E = True       # True : embarque le calque _e en seconde texture (correctif du clignotement annoncé le 2026-11-03, à vérifier en jeu).
TEX = 512
SS = 4
TAU = 2 * math.pi


# ------------------------------------------------------------------ textures
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
    if solid.any():
        arr[~solid, :3] = rgb[solid].mean(axis=0).astype(np.uint8)
    arr[..., 3] = solid * 255
    return arr


def shrink(col, W, H, alpha_small):
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    return np.dstack([rgb, alpha_small]).astype(np.uint8)


# Cœur : bases poussées vers le blanc (la lumière chaude de nuit vire le pastel au saumon), liseré net pour le contraste de valeur.
#        clair (reflet), base, ombre basse, liseré, lueur _e (fond), lueur _e (trait)
HPAL = {
    "rose":    ((255, 246, 250), (255, 208, 226), (240, 156, 192), (214, 92, 146), (34, 12, 22), (150, 64, 104)),
    "lavande": ((250, 246, 255), (226, 212, 255), (186, 164, 238), (128, 96, 206), (22, 14, 36), (106, 78, 168)),
    "creme":   ((255, 255, 252), (255, 249, 236), (246, 220, 206), (226, 128, 160), (30, 24, 18), (150, 100, 108)),
}
# Cœur implicite (x² + y² − 1)³ − x² y³ ≤ 0 : bornes x ±1,139, y de −1 à 1,236 (mesurées ci-dessous).
HX, HY0, HY1 = 1.16, -1.03, 1.26


def heart_field(W, H):
    """Champ du cœur sur la grille sur-échantillonnée ; y vers le haut de l'image."""
    w, h = W * SS, H * SS
    u, v = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    x = (u - 0.5) * 2 * HX
    y = HY1 - v * (HY1 - HY0)
    f = (x * x + y * y - 1) ** 3 - x * x * y ** 3
    a = f <= 0
    return x, y, a, inner_dist(a) / SS


def inner_dist(a, nmax=48):
    """Distance au bord (en texels de la grille) par érosions successives, voisinage 4 et 8 alternés (octogone)."""
    d = np.zeros(a.shape, np.float32)
    cur = a.copy()
    for i in range(nmax):
        d += cur
        p = np.pad(cur, 1)
        nxt = cur & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
        if i % 2:
            nxt &= p[:-2, :-2] & p[:-2, 2:] & p[2:, :-2] & p[2:, 2:]
        cur = nxt
        if not cur.any():
            break
    return d - 0.5 * a


def paint_heart(W, H, pal, shine=True):
    """Cœur dodu : dégradé du reflet (haut gauche) vers l'ombre (bas), liseré de ~3,5 texels, reflet kawaii (ovale + point)."""
    light, base, shade, rim, e_bg, e_line = (np.array(c, np.float32) for c in pal)
    x, y, a, dist = heart_field(W, H)
    # volume : lumière venant du haut gauche
    k = np.clip(0.5 + 0.38 * (-x * 0.55 + y * 0.8) / 1.2, 0, 1)
    col = lerp(shade, base, smooth(k * 1.6)[..., None])
    col = lerp(col, light, smooth((k - 0.62) / 0.38)[..., None] * 0.7)
    # ombre de recouvrement en bas de la pointe et contre le bord droit
    col = lerp(col, shade, (smooth((-y - 0.35) / 0.6) * 0.55)[..., None])
    # liseré net
    rimk = np.clip(1 - (dist - 2.2) / 1.6, 0, 1)
    col = lerp(col, rim, rimk[..., None] * 0.9)
    e = np.empty(col.shape, np.float32)
    e[...] = e_bg
    # trait lumineux fin juste à l'intérieur du liseré (point focal de la lueur)
    line = np.clip(1 - np.abs(dist - 5.0) / 1.2, 0, 1)
    e = lerp(e, e_line, line[..., None])
    if shine:
        # reflet ovale incliné sur le lobe gauche + petit point
        ox, oy = x + 0.48, y - 0.52
        c, s = math.cos(0.6), math.sin(0.6)
        rx, ry = ox * c + oy * s, -ox * s + oy * c
        ov = (rx / 0.30) ** 2 + (ry / 0.15) ** 2 < 1
        dot = (x + 0.12) ** 2 + (y - 0.86) ** 2 < 0.075 ** 2
        sh = (ov | dot)[..., None]
        col = np.where(sh, np.array((255, 255, 255), np.float32), col)
        e = np.where(sh, np.array((170, 160, 168), np.float32), e)
    out = finish(col, a, W, H)
    return out, shrink(e, W, H, out[..., 3]), a


def edge_strip(pal, W=6, H=16):
    """Bande opaque de l'âme : couleur du liseré, assombrie vers le bas."""
    rim, shade = np.array(pal[3], np.float32), np.array(pal[2], np.float32)
    arr = np.zeros((H, W, 4), np.uint8)
    for yy in range(H):
        arr[yy, :, :3] = lerp(lerp(shade, rim, 0.55), rim, yy / (H - 1)).astype(np.uint8)
    arr[..., 3] = 255
    em = np.zeros_like(arr)
    em[..., :3] = np.array(pal[4]) // 2
    em[..., 3] = 255
    return arr, em


RING_D = 24.0         # diamètre de l'anneau (px)
RING_T = 176          # texels de côté : 7,3 texels par px
NPUFF = 12


def paint_ring(N=RING_T):
    """Anneau de nuages vu de dessus : 12 gros flocons + 12 petits à l'extérieur, liseré lavande, joue rose côté extérieur."""
    n = N * SS
    u, v = np.meshgrid((np.arange(n) + 0.5) / n, (np.arange(n) + 0.5) / n)
    px = (u - 0.5) * RING_D
    pz = (v - 0.5) * RING_D
    white = np.array((255, 253, 250), np.float32)
    lav = np.array((198, 182, 236), np.float32)
    rimc = np.array((150, 124, 210), np.float32)
    blush = np.array((252, 196, 218), np.float32)
    col = np.zeros(px.shape + (3,), np.float32)
    a = np.zeros(px.shape, bool)
    tpx = RING_D / n           # px par texel sur-échantillonné
    puffs = []
    for i in range(NPUFF):
        f = TAU * (i + 0.5) / NPUFF
        puffs.append((10.25, f, 1.25, 0))       # petits, extérieurs, dessinés d'abord (recouverts)
    for i in range(NPUFF):
        f = TAU * i / NPUFF
        puffs.append((9.3, f, 1.75, 1))
    for i in range(NPUFF):
        f = TAU * (i + 0.5) / NPUFF
        puffs.append((8.15, f, 1.15, 2))       # petits, intérieurs, dessus : le cercle intérieur ondule aussi
    for R, f, r, kind in puffs:
        cx, cz = R * math.cos(f), R * math.sin(f)
        dx, dz = px - cx, pz - cz
        d = np.hypot(dx, dz) / r
        m = d < 1
        # lumière du haut gauche de l'image, ombre à l'opposé
        k = np.clip(0.55 + 0.45 * (-(dx + dz) / (r * 1.4)), 0, 1)
        c = lerp(lav, white, smooth(k * 1.5)[..., None])
        c = lerp(c, blush, (smooth((d - 0.35) / 0.65) * 0.55 * (kind == 0))[..., None])
        edge = (1 - d) * r / tpx / SS          # distance au bord du flocon, en texels finaux
        c = lerp(c, rimc, np.clip(1 - (edge - 1.6) / 1.4, 0, 1)[..., None] * 0.85)
        col = np.where(m[..., None], c, col)
        a |= m
    out = finish(col, a, N, N)
    e = np.zeros(out.shape, np.uint8)
    e[..., :3] = (10, 8, 14)
    e[..., 3] = out[..., 3]
    return out, e


def particle_heart(W, H, pal):
    """Cœur-particule : même peinture, un peu plus contrastée (lu de loin, plus petit)."""
    return paint_heart(W, H, pal, shine=True)


UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_cur = [0, 0, 0]
MASK = {}


def place(name, im, em=None):
    h, w = im.shape[:2]
    if _cur[0] + w > TEX:
        _cur[:] = [0, _cur[1] + _cur[2] + 2, 0]
    x, y = _cur[0], _cur[1]
    assert y + h <= TEX - 6, "atlas plein"
    tex[y:y + h, x:x + w] = im
    if em is not None:
        tex_e[y:y + h, x:x + w] = em
    UV[name] = (x, y, x + w, y + h)
    _cur[0] += w + 2
    _cur[2] = max(_cur[2], h)


ring, ring_e = paint_ring()
place("ring", ring, ring_e)
for nm, pal in HPAL.items():
    im, em, a = paint_heart(64, 62, pal)
    place(f"h_{nm}", im, em)
    MASK[nm] = a
for nm, pal in HPAL.items():
    im, em, _ = particle_heart(48, 46, pal)
    place(f"pt_{nm}", im, em)
for nm, pal in HPAL.items():
    place(f"edge_{nm}", *edge_strip(pal))

CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC
assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
assert tex_e[..., :3].max() <= 200, "calque trop vif"
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


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups and len(name) <= 64
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "rotation": [round(float(v), 2) for v in rotation]}
    return name


def cube(g, name, c, size, X, Y, faces):
    """Cube centré en c, axes X, Y (orthonormés), Z = X × Y."""
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


SKIN = 0.3
EMBED = 0.12


def inside(nm, hx, hy):
    """Point du cœur (coordonnées du champ) dans la silhouette peinte, avec une marge."""
    a = MASK[nm]
    H, W = a.shape
    u = int((hx / (2 * HX) + 0.5) * W)
    v = int((HY1 - hy) / (HY1 - HY0) * H)
    return 0 <= u < W and 0 <= v < H and bool(a[v, u])


def puffy_heart(g, name, c, X, Y, w, thick, nm):
    """Cœur dodu centré en c (centre de l'image), largeur w (px), plan (X, Y), normale Z = X × Y.
    Deux peaux (recto +Z, verso −Z) + âme : bloc des lobes et losange de la pointe, plus étroits que la silhouette."""
    Z = np.cross(X, Y)
    s = w / (2 * HX)                         # px par unité du champ
    h = (HY1 - HY0) * s
    cy = (HY1 + HY0) / 2                      # centre de l'image dans le champ
    u0, v0, u1, v1 = UV[f"h_{nm}"]
    for sg in (1, -1):
        faces = {"south": [u0, v0, u1, v1] if sg > 0 else CLEAR, "north": [u1, v0, u0, v1] if sg < 0 else CLEAR,
                 "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
        cube(g, f"{name}.{'r' if sg > 0 else 'v'}", c + Z * sg * (thick / 2 - SKIN / 2), (w, h, SKIN), X, Y, faces)
    th = thick - 2 * SKIN + 2 * EMBED
    e0, e1, e2, e3 = UV[f"edge_{nm}"]
    fc = [e0, e1, e2, e3]
    allf = {f: fc for f in ("north", "south", "east", "west", "up", "down")}
    # lobes : bloc centré en (0, 0.42), demi-largeur 0.72, demi-hauteur 0.36 (unités du champ)
    lx, ly, lw, lh = 0.0, 0.40, 0.70, 0.34
    for qx in (-lw, lw):
        for qy in (ly - lh, ly + lh):
            assert inside(nm, qx, qy), ("âme hors silhouette (lobes)", qx, qy)
    cube(g, f"{name}.c0", c + Y * (ly - cy) * s, (2 * lw * s, 2 * lh * s, th), X, Y, allf)
    # pointe : losange (carré tourné de 45°) centré en (0, −0.12), demi-diagonale 0.62
    py, pd = -0.14, 0.60
    for qx, qy in ((0, py - pd), (0, py + pd), (-pd, py), (pd, py)):
        assert inside(nm, qx * 0.97, qy * 0.97 if qy < 0 else qy), ("âme hors silhouette (pointe)", qx, qy)
    side = pd * math.sqrt(2) * s
    Xd = unit(X * math.cos(math.radians(45)) + Y * math.sin(math.radians(45)))
    Yd = np.cross(Z, Xd)
    cube(g, f"{name}.c1", c + Y * (py - cy) * s, (side, side, th - 0.04), Xd, Yd, allf)
    return c + Y * (HY1 - cy) * s * 0.9


BODY_C = V(0, 17.0, 0)                      # centre de l'orbite
ORBIT_TILT = (7, 0, -5)
#        angle, rayon, hauteur, largeur, épaisseur, couleur
HEARTS = [(30, 10.4, 2.4, 4.4, 1.0, "rose"), (100, 11.0, -1.8, 3.6, 0.9, "lavande"), (170, 10.2, 3.6, 3.2, 0.9, "creme"),
          (245, 10.0, 0.6, 4.0, 1.0, "rose"), (315, 11.2, -0.8, 3.4, 0.9, "lavande")]
EMIT_N = {}
EMITS = []


def emit(kind, pos, parent):
    k = EMIT_N.get(kind, 0) + 1
    EMIT_N[kind] = k
    EMITS.append(group(f"emit_coeur_{kind}" + (str(k) if k > 1 else ""), pos, parent=parent))


group("orbite", BODY_C, rotation=ORBIT_TILT)
group("choc", BODY_C, parent="orbite")
group("spin", BODY_C, parent="choc")
HDATA = []
for k, (phi, R, dy, w, th, nm) in enumerate(HEARTS):
    f = math.radians(phi)
    rad = V(math.cos(f), 0, -math.sin(f))
    c = BODY_C + rad * R + V(0, dy, 0)
    g = group(f"c{k}", c, parent="spin")
    Y = V(0, 1, 0)
    X = np.cross(Y, rad)                    # X × Y = rad : le recto regarde vers l'extérieur
    top = puffy_heart(g, f"h{k}", c, X, Y, w, th, nm)
    HDATA.append((g, rad, k))
    emit(("rose", "lavande", "creme", "rose", "creme")[k], top + V(0, 0.4, 0), g)

# anneau de nuages au sol, autour des pieds
group("nuage", V(0, 0, 0))
group("nuage_spin", V(0, 0, 0), parent="nuage")
group("nuage_echelle", V(0, 0.45, 0), parent="nuage_spin")
r0, r1, r2, r3 = UV["ring"]
cube("nuage_echelle", "anneau", V(0, 0.45, 0), (RING_D, 0.3, RING_D), V(1, 0, 0), V(0, 1, 0),
     {"up": [r0, r1, r2, r3], "down": CLEAR, "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR})
for i, kind in enumerate(("lavande", "creme", "rose", "lavande", "creme", "rose")):
    f = TAU * (i + 0.25) / 6
    emit(kind, V(9.3 * math.cos(f), 1.2, 9.3 * math.sin(f)), "nuage_spin")
# près des épaules
emit("creme", V(-6.5, 25.5, 1.5), None)
emit("lavande", V(6.5, 25.5, 1.5), None)


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


# Particules : un seul cube de 0,3 px, face up seule, à 0,3 px au-dessus du pivot. Image en haut = côté −Z (nord) :
# redressé par +X dans _fall, le haut du cœur monte.
PSIZE = {"rose": 3.0, "lavande": 2.6, "creme": 2.2}
PGROUPS = []
for nm, pw in PSIZE.items():
    pg = group(f"particle_coeur_{nm}", V(0, 0, 0))
    PGROUPS.append(pg)
    a0, b0, a1, b1 = UV[f"pt_{nm}"]
    ph = pw * (b1 - b0) / (a1 - a0)
    cube(pg, f"coeur_{nm}", V(0, 0.3 + 0.15, 0), (pw, 0.3, ph), V(1, 0, 0), V(0, 1, 0), {"up": [a0, b0, a1, b1]})

root_children = ["orbite", "nuage"] + [n for n in groups if n.startswith("emit_") and groups[n]["parent"] is None]
outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone(n) for n in root_children]}] + [bone(p) for p in PGROUPS]


# ------------------------------------------------------------------ animations
def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 3)), "y": str(round(y + 0.0, 3)), "z": str(round(z + 0.0, 3))}],
            "time": round(t, 3), "interpolation": "linear"}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def beat(t, period):
    """Battement de cœur « lub-dub » : deux impulsions rapprochées par période, retour exact à 0."""
    p = (t % period) / period
    return math.exp(-((p - 0.12) / 0.045) ** 2) + 0.6 * math.exp(-((p - 0.30) / 0.045) ** 2)


def spin_track(length, turns=1, n=16):
    return [kf("rotation", i * length / n, 0, 360.0 * turns * i / n, 0) for i in range(n + 1)]


RING_HIDE = 0.02


def state(name, length, dr, y0, amp, cycles, sway, beat_amp, ring=1.0, ring_turns=1, orbit_turns=1, self_turns=1):
    """dr : rayon en plus (px) ; y0 : hauteur en plus ; amp, cycles : flottement (cycles entiers par boucle) ; sway : balancement (°) ;
    beat_amp : amplitude du battement (échelle) ; ring : échelle de l'anneau (RING_HIDE = replié)."""
    A = {groups["spin"]["uuid"]: {"name": "spin", "type": "bone", "keyframes": spin_track(length, orbit_turns)},
         groups["nuage_spin"]["uuid"]: {"name": "nuage_spin", "type": "bone", "keyframes": spin_track(length, -ring_turns)}}
    if ring != 1.0:
        A[groups["nuage_echelle"]["uuid"]] = {"name": "nuage_echelle", "type": "bone", "keyframes": [kf("scale", 0, ring, 1, ring), kf("scale", length, ring, 1, ring)]}
    n = max(24, int(round(length * 6)))
    times = [i * length / n for i in range(n + 1)]
    bper = length / max(1, round(length / 2.0))           # battement toutes les ~2 s, entier par boucle
    for g, rad, k in HDATA:
        ph = k * 2.399
        w = TAU * cycles / length
        keys = [kf("position", t, *(rad * dr + V(0, y0 + amp * math.sin(w * t + ph), 0))) for t in times]
        st = 360.0 * self_turns * (1 if k % 2 else -1) / length      # le cœur tourne sur lui-même : jamais longtemps vu par la tranche
        keys += [kf("rotation", t, sway * 0.4 * math.sin(w * t + ph + 1.0), st * t + sway * math.sin(w * t + ph * 1.3), sway * 0.6 * math.cos(w * t + ph)) for t in times]
        if beat_amp:
            bt = [i * bper / 20 for i in range(20)]
            bt = [t0 + j * bper for j in range(int(round(length / bper))) for t0 in bt] + [length]
            sh = 0.37 * k
            keys += [kf("scale", t, *([1 + beat_amp * beat(t + sh * bper, bper)] * 3)) for t in bt]
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": keys}
    return {"uuid": nuid(), "name": name, "loop": "loop", "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


H_ = RING_HIDE
STATES = [
    state("idle", 16.0, 0.0, 0.0, 0.7, 2, 12, 0.10, self_turns=2),
    state("walk", 12.0, -0.3, 0.0, 0.6, 3, 10, 0.06),
    state("run", 8.0, -1.2, -0.6, 0.4, 4, 8, 0.0, orbit_turns=2),        # plus resserrée, plus rapide
    state("sneak", 16.0, -1.0, -2.0, 0.45, 2, 8, 0.06, ring=H_),          # plus basse ; anneau replié (corps penché)
    state("fly", 12.0, 1.4, 0.6, 1.0, 3, 16, 0.08),                      # plus large, flottement ample
    state("glide", 8.0, 0.8, 0.0, 0.6, 2, 8, 0.0, ring=H_),
    state("swim", 12.0, 0.4, 0.0, 0.8, 2, 14, 0.0, ring=H_),
    state("mount", 16.0, 0.6, 1.5, 0.6, 2, 10, 0.08, ring=H_),
    state("sleep", 24.0, -0.5, -1.0, 0.4, 2, 6, 0.05, ring=H_),
]

# hurt 0,8 s : sursaut de l'orbite puis tremblement amorti, dernière image à zéro ; choc n'est animé par aucun état
HU = 0.8
hu = lambda t: bump(t, 0.0, 0.07, 0.2, 0.72)
tr = lambda t: math.sin(TAU * t * 5 / HU) * (1 - sm(t, 0.15, 0.7))
times = [j * HU / 16 for j in range(17)]
hurt = {"uuid": nuid(), "name": "hurt", "loop": "once", "override": False, "length": HU, "snapping": 24, "selected": False, "animators": {
    groups["choc"]["uuid"]: {"name": "choc", "type": "bone", "keyframes":
        [kf("rotation", t, 7 * tr(t), 0, -6 * tr(t)) for t in times] + [kf("position", t, 0, 1.4 * hu(t), 0) for t in times]
        + [kf("scale", t, *([1 + 0.12 * hu(t)] * 3)) for t in times]}}}


def particle_anim(name, pg, length, rot, scl, n):
    times = [i * length / n for i in range(n + 1)]
    keys = [kf("rotation", t, *rot(t)) for t in times] + [kf("scale", t, *([scl(t)] * 3)) for t in times]
    return {"uuid": nuid(), "name": name, "loop": "loop", "override": False, "length": length, "snapping": 24, "selected": False,
            "animators": {groups[pg]["uuid"]: {"name": pg, "type": "bone", "keyframes": keys}}}


PANIMS = []
for i, (nm, pg) in enumerate(zip(PSIZE, PGROUPS)):
    PF = (3.0, 3.6, 2.4)[i]
    sgn = 1 if i % 2 == 0 else -1
    # _fall : redressé (~82°), tourne comme une pièce (360° par boucle), léger roulis, petit battement
    PANIMS.append(particle_anim(f"particle_coeur_{nm}_fall", pg, PF,
                                lambda t, PF=PF, sgn=sgn: (82 + 6 * math.sin(TAU * t / PF), sgn * 360 * t / PF, 8 * math.sin(2 * TAU * t / PF)),
                                lambda t, PF=PF: 1 + 0.12 * beat(t, PF / 2), 36))
    # _rest : posé à plat (rotation 0), battement lent
    PR = 4.0
    PANIMS.append(particle_anim(f"particle_coeur_{nm}_rest", pg, PR, lambda t, PR=PR: (0, 0, 0), lambda t, PR=PR: 1 + 0.08 * beat(t, PR / 2), 24))

ANIMS = STATES + [hurt] + PANIMS
assert len(ANIMS) <= 16, len(ANIMS)
assert len(EMITS) <= 32 and len(PGROUPS) <= 4
assert 20 <= len(elements) <= 60, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
# Les cœurs montent : on les garde, sans animation au sol (particules qui tombent et se posent : réservées aux ailes).
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from particules import retirer_particules
retirer_particules(model, montantes=True)
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;", len(EMITS), "emit_")
