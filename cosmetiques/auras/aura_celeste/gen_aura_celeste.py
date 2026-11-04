"""Aura céleste : 7 plumes ivoire qui gravitent autour du torse sur trois plans inclinés, en flottant. Design original, assortie à aurelion_wings.
Écrit aura_celeste.png, aura_celeste_e.png et .build/aura_celeste_brut.bbmodel à côté de ce script.

Plume : peau ronde découpée par alpha autour d'une âme pleine plus étroite, hampe nue en volume. Chaque plan : orbite_x (inclinaison fixe)
> choc_x (seul groupe animé par hurt, joué par-dessus l'état) > spin_x (exactement 360° par boucle) > p<k> (flottement Y, rayon, léger balancement).
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "aura_celeste"
AVEC_E = True       # True : embarque le calque _e en seconde texture. Réactivé le 2026-11-03 (correctif du mod annoncé, à vérifier en jeu).
TEX = 512
SS = 4
TAU = 2 * math.pi


# ------------------------------------------------------------------ textures
def lerp(a, b, k):
    return a + (b - a) * k


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


PAL = {
    # racine, milieu, bout, liseré, ombre, couleur de pointe : mêmes valeurs que aurelion_wings
    "p": ((222, 216, 202), (252, 250, 243), (254, 251, 240), (176, 150, 104), (150, 138, 116), (238, 200, 116)),
    "l": ((240, 212, 148), (250, 232, 180), (254, 242, 204), (186, 148, 84), (176, 146, 96), (255, 244, 208)),
}
SHAPE = {
    # demi-largeur intérieure, extérieure, début de l'arrondi, courbure, début de pointe colorée, longueur d'ombre
    "p": (0.42, 0.33, 0.62, 0.20, 0.72, 0.26),
    "l": (0.46, 0.42, 0.44, 0.03, 0.86, 0.16),
}


def finish(col, alpha, W, H):
    """Réduit la peinture sur-échantillonnée : alpha 0/255, couleur moyenne hors silhouette (ni frange, ni PNG lourd)."""
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    solid = np.array(Image.fromarray((alpha * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = rgb
    if solid.any():
        arr[~solid, :3] = rgb[solid].mean(axis=0).astype(np.uint8)
    arr[..., 3] = solid * 255
    return arr


def paint(W, H, kind, seed):
    """Plume : base en haut, pointe en bas, côté extérieur à droite. Renvoie la texture et le calque lumineux."""
    rng = np.random.default_rng(seed)
    root, mid, tip, rim, shadow, gold = (np.array(c, np.float32) for c in PAL[kind])
    hi, ho, te, curve, g0, shl = SHAPE[kind]
    te += rng.uniform(-0.03, 0.03)
    jitter = rng.uniform(0.97, 1.02)
    w, h = W * SS, H * SS
    x, y = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    t = y
    cx = 0.5 + curve * (t * t - 0.3)
    env = (0.28 + 0.72 * smooth(t / 0.20)) * np.where(t > te, np.sqrt(np.clip(1 - ((t - te) / (1 - te)) ** 2, 0, 1)), 1.0)
    d = x - cx
    lim = np.where(d >= 0, ho * env, hi * env)
    r = np.abs(d) / np.maximum(lim, 1e-4)
    alpha = r < 1
    # encoche dans la vanne extérieure : la marque qui fait lire une plume plutôt qu'un grain
    alpha &= ~((d > 0) & (r > 0.42) & (np.abs(t - rng.uniform(0.46, 0.6) - r * 0.13) < 0.024 * r))
    col = lerp(lerp(root, mid, smooth(t / 0.5)[..., None]), tip, smooth((t - 0.5) / 0.5)[..., None]) * jitter
    col = col * (1.04 - 0.17 * (r ** 2))[..., None]
    col = col * (1 + 0.035 * np.sin((t * H - np.abs(d) * W * 1.4) * TAU / 6.0) * (r > 0.1))[..., None]
    gk = smooth((t - g0) / max(1e-3, 1 - g0))[..., None]
    col = lerp(col, gold, gk * 0.85)
    col = lerp(col, shadow, (np.clip(1 - t / shl, 0, 1) ** 1.25)[..., None] * 0.72)
    col = col * (1 - 0.20 * (np.clip((r - 0.45) / 0.55, 0, 1) * (d < 0))[..., None])
    dist = (1 - r) * lim * W
    col = lerp(col, rim, (np.clip(1 - dist / 3.5, 0, 1) * (t > 0.12))[..., None] * 0.72)
    ec = np.empty(col.shape, np.float32)
    ec[...] = (42, 36, 22) if kind == "l" else (40, 39, 35)
    ec = lerp(ec, np.array((128, 104, 58), np.float32), gk)
    ec = lerp(ec, np.array((118, 106, 78), np.float32), (np.clip(1 - dist / 2.2, 0, 1) * (t > 0.12))[..., None])
    if kind == "p":
        ra = np.clip(1 - np.abs(d) * W / 1.5, 0, 1)[..., None] * (t < 0.93)[..., None]
        col = lerp(col, np.array((255, 248, 226), np.float32), ra * 0.75)
        ec = lerp(ec, np.array((170, 162, 136), np.float32), ra)
    out = finish(col, alpha, W, H)
    eo = np.array(Image.fromarray(np.clip(ec, 0, 200).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    return out, np.dstack([eo, out[..., 3]]).astype(np.uint8)


def edge_strip(kind, W=6, H=32):
    """Bande opaque de l'âme : suit le dégradé de la plume, assombrie pour dessiner le bord."""
    root, mid, tip, rim, shadow, gold = (np.array(c, np.float32) for c in PAL[kind])
    g0 = SHAPE[kind][4]
    a = np.zeros((H, W, 4), np.float32)
    for yy in range(H):
        t = (yy + 0.5) / H
        c = lerp(root, mid, min(1, t * 2)) if t < 0.5 else lerp(mid, tip, (t - 0.5) * 2)
        c = lerp(c, gold, float(smooth((t - g0) / max(1e-3, 1 - g0))) * 0.85)
        a[yy, :, :3] = lerp(c, rim, 0.38)
    a[..., 3] = 255
    return a.astype(np.uint8)


def particle_plume(PLW=40, PLH=160):
    """Plume-particule, recette validée : une seule silhouette, courbure et contour peints dans l'image."""
    y_, x_ = np.mgrid[0:PLH * SS, 0:PLW * SS]
    t = (y_ + 0.5) / (PLH * SS)
    d = (x_ + 0.5) / (PLW * SS) - 0.5
    c = 0.13 * (np.sin(t * math.pi) - 0.5)
    v = np.clip((t - 0.10) / 0.90, 0, 1)
    env = 0.34 * np.sin(math.pi * v ** 0.85) ** 0.42
    dd = np.abs(d - c)
    a = dd < np.maximum(env, 0.018 * (t < 0.97))
    col = np.empty(a.shape + (3,), np.float32)
    col[...] = (248, 245, 234)
    col = col * (1.0 - 0.14 * (dd / np.maximum(env, 0.02))[..., None] ** 2)
    col = col * (1 + 0.03 * np.sin((t * PLH - dd * PLW * 1.4) * TAU / 7))[..., None]
    col = lerp(col, np.array((236, 202, 124), np.float32), smooth((t - 0.78) / 0.22)[..., None] * 0.8)
    col = lerp(col, np.array((205, 192, 165), np.float32), (dd < 0.02)[..., None] * 0.8)
    return finish(col, a, PLW, PLH)


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
    UV[name] = (x, y, x + w, y + h)
    _cur[0] += w + 2
    _cur[2] = max(_cur[2], h)


for i in range(4):
    place(f"p{i}", *paint(56, 140, "p", i + 1))
place("plume", particle_plume())
e_ = edge_strip("p")
em_ = np.zeros(e_.shape, np.uint8)
em_[...] = (30, 29, 26, 255)
place("edge_p", e_, em_)

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
    assert name not in groups
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


def all_faces(tile):
    return {f: list(UV[tile]) for f in ("north", "south", "east", "west", "up", "down")}


SKIN = 0.3       # épaisseur d'une peau
EMBED = 0.12     # l'âme entre d'autant dans la peau : ni vide, ni face coplanaire


def feather(g, name, p, d, vane, L, w, tile, t0=0.6, t1=0.32, ncore=2, bow=0.25, skins=(1, -1)):
    """Plume hybride partant de p vers d ; vane = côté droit de l'image, Z = X × Y. t0, t1 : épaisseur totale à la base, à la pointe.
    Les deux peaux se rejoignent vers la pointe (t1 proche de SKIN) : profil en lentille, pas de bout fourchu sur une plume de cette taille.
    bow : la pointe s'écarte du plan vers -Z. skins : peaux à poser, +1 côté +Z, -1 côté -Z."""
    p, d = np.asarray(p, float), unit(np.asarray(d, float))
    X0 = unit(vane - (vane @ d) * d)
    Y0 = -d
    Z0 = np.cross(X0, Y0)
    u0, v0, u1, v1 = UV[tile]
    tip = p + d * L
    for sg in skins:
        a = p + Z0 * (sg * (t0 / 2 - SKIN / 2))
        b = tip + Z0 * (-bow + sg * (t1 / 2 - SKIN / 2))
        ax = unit(b - a)
        X = unit(X0 - (X0 @ ax) * ax)
        faces = {"south": [u0, v0, u1, v1] if sg > 0 else CLEAR, "north": [u1, v0, u0, v1] if sg < 0 else CLEAR,
                 "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
        cube(g, f"{name}.{'d' if sg > 0 else 'v'}", (a + b) / 2, (w, float(np.linalg.norm(b - a)), SKIN), X, -ax, faces)
    kind = tile[0]
    e0, e1, e2, e3 = UV[f"edge_{kind}"]
    t_a, t_b = 0.16, 0.92
    for j in range(ncore):
        f0, f1 = lerp(t_a, t_b, j / ncore), lerp(t_a, t_b, (j + 1) / ncore)
        c0, c1 = p + d * (f0 * L) + Z0 * (-bow * f0), p + d * (f1 * L) + Z0 * (-bow * f1)
        ax = unit(c1 - c0)
        X = unit(X0 - (X0 @ ax) * ax)
        th = max(0.3, lerp(t0, t1, f1) - 2 * SKIN + 2 * EMBED)
        wc = w * 0.38 * (1 - 0.5 * (j + 0.5) / ncore)
        ov = 0.12 if j else 0.0
        ea, eb = lerp(e1, e3, f0), lerp(e1, e3, f1)
        fc = [e0, ea, e2, eb]
        cube(g, f"{name}.c{j}", (c0 + c1) / 2 - ax * ov / 2, (wc, float(np.linalg.norm(c1 - c0)) + ov, th), X, -ax,
             {"south": fc, "north": fc, "east": fc, "west": fc, "up": [e0, ea, e2, min(e3, ea + 1)], "down": [e0, max(e1, eb - 1), e2, eb]})
    return tip


CENTER = V(0, 18.0, 0)      # axe de l'orbite : centre du torse
#         plan : inclinaison X, Z, rayon, hauteur relative
PLANES = {"a": (14, 9, 11.0, 1.5), "b": (-11, -8, 10.6, -2.5), "c": (7, -17, 12.0, 3.0)}
#        plan, angle, longueur, largeur, descente de la pointe, ouverture vers l'extérieur, lance des plumes
PLUMES = [("a", 20, 5.8, 1.9, 22, 0.20, True), ("a", 140, 5.0, 1.7, 34, 0.32, False), ("a", 262, 5.6, 1.85, 15, 0.14, True),
          ("b", 78, 5.2, 1.75, 40, 0.26, True), ("b", 228, 6.0, 2.0, 27, 0.18, False),
          ("c", 188, 4.6, 1.6, 18, 0.34, True), ("c", 322, 5.4, 1.8, 30, 0.22, True)]
PDATA, EMITS = [], []
for pl, (rx, rz, _, _) in PLANES.items():
    group(f"orbite_{pl}", CENTER, rotation=(rx, 0, rz))
    group(f"choc_{pl}", CENTER, parent=f"orbite_{pl}")
    group(f"spin_{pl}", CENTER, parent=f"choc_{pl}")

for k, (pl, phi, L, w, drop, flare, em) in enumerate(PLUMES):
    _, _, Rp, dy = PLANES[pl]
    f = math.radians(phi)
    rad = V(math.cos(f), 0, -math.sin(f))             # vers l'extérieur
    tg = V(-math.sin(f), 0, -math.cos(f))             # sens de l'orbite (+Y) : la pointe traîne derrière
    c = CENTER + rad * Rp + V(0, dy, 0)
    dp = math.radians(drop)
    d = unit(-tg * math.cos(dp) + V(0, -math.sin(dp), 0) + rad * 0.06)
    vane = V(0, 1, 0) + rad * flare
    base = c - d * (L / 2)
    g = group(f"p{k}", c, parent=f"spin_{pl}")
    tip = feather(g, f"f{k}", base, d, vane, L, w, f"p{k % 4}", t0=0.56, t1=0.32, ncore=3, bow=0.18)
    # hampe nue : le seul morceau qui dépasse de la base
    X0 = unit(vane - (vane @ d) * d)
    e0, e1, e2, e3 = UV["edge_p"]
    fq = [e0, e1, e2, lerp(e1, e3, 0.3)]
    cube(g, f"f{k}.q", base + d * (0.05 * L), (0.24, 0.34 * L, 0.24), X0, -d, {n: fq for n in ("north", "south", "east", "west", "up", "down")})
    PDATA.append((g, rad, k))
    if em:
        EMITS.append(group("emit_plume" + (str(len(EMITS) + 1) if EMITS else ""), tip, parent=g))


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


# Particule (guide, section 5 ter) : une seule plaque, courbure peinte, face up seule, à 0,3 px au-dessus du pivot.
PL = group("particle_plume", [0, 0, 0])
PW, PLEN, PTH, PY = 1.9, 6.0, 0.3, 0.3
pu0, pv0, pu1, pv1 = UV["plume"]
cube(PL, "plume", V(0, PY + PTH / 2, 0), (PW, PTH, PLEN), V(1, 0, 0), V(0, 1, 0), {"up": [pu0, pv0, pu1, pv1]})

outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone(f"orbite_{pl}") for pl in PLANES]}, bone(PL)]


# ------------------------------------------------------------------ animations
def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 2)), "y": str(round(y + 0.0, 2)), "z": str(round(z + 0.0, 2))}],
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


def state(name, length, dr, y0, amp, cycles, sway, breathe=0.0):
    """Un tour exact par boucle. dr : rayon en plus (px) ; y0 : hauteur en plus ; amp, cycles : flottement Y (cycles entiers par boucle) ;
    sway : balancement de la plume (°) ; breathe : va-et-vient du rayon (px)."""
    A = {}
    nspin = 16
    for pl in PLANES:
        A[groups[f"spin_{pl}"]["uuid"]] = {"name": f"spin_{pl}", "type": "bone", "keyframes": [kf("rotation", i * length / nspin, 0, 360.0 * i / nspin, 0) for i in range(nspin + 1)]}
    n = max(16, int(round(length * 4)))
    times = [i * length / n for i in range(n + 1)]
    for g, rad, k in PDATA:
        ph = k * 2.399      # déphasage par plume, angle d'or
        w = TAU * cycles / length
        keys = [kf("position", t, *(rad * (dr + breathe * math.sin(w * t + ph * 0.7)) + V(0, y0 + amp * math.sin(w * t + ph), 0))) for t in times]
        keys += [kf("rotation", t, sway * math.sin(w * t + ph + 1.0), sway * 0.7 * math.sin(w * t + ph * 1.3), sway * math.cos(w * t + ph)) for t in times]
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": keys}
    return {"uuid": nuid(), "name": name, "loop": "loop", "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


idle = state("idle", 16.0, 0.0, 0.0, 0.7, 2, 7, 0.25)
walk = state("walk", 12.0, -0.4, 0.0, 0.6, 3, 6, 0.2)
run = state("run", 6.0, -1.0, -0.3, 0.35, 3, 5, 0.1)        # plus resserrée, tour plus rapide
sneak = state("sneak", 20.0, -0.8, -1.5, 0.45, 2, 5, 0.15)  # plus basse et calme
fly = state("fly", 9.0, 1.2, 0.5, 1.0, 3, 10, 0.4)          # plus large, flottement ample

# hurt 0,8 s : sursaut de chaque plan puis tremblement amorti, dernière image à zéro ; choc_x n'est animé par aucun état
HU = 0.8
hu = lambda t: bump(t, 0.0, 0.07, 0.2, 0.72)
tr = lambda t: math.sin(TAU * t * 5 / HU) * (1 - sm(t, 0.15, 0.7))
hurt_A = {}
for i, pl in enumerate(PLANES):
    sg = 1 if i % 2 else -1
    times = [j * HU / 16 for j in range(17)]
    hurt_A[groups[f"choc_{pl}"]["uuid"]] = {"name": f"choc_{pl}", "type": "bone", "keyframes":
        [kf("rotation", t, sg * 7 * tr(t), 0, -sg * 6 * tr(t)) for t in times] + [kf("position", t, 0, 1.4 * hu(t), 0) for t in times]}
hurt = {"uuid": nuid(), "name": "hurt", "loop": "once", "override": False, "length": HU, "snapping": 24, "selected": False, "animators": hurt_A}


def particle_anim(name, length, curve, n):
    times = [i * length / n for i in range(n + 1)]
    return {"uuid": nuid(), "name": name, "loop": "loop", "override": False, "length": length, "snapping": 24, "selected": False,
            "animators": {groups[PL]["uuid"]: {"name": PL, "type": "bone", "keyframes": [kf("rotation", t, *curve(t)) for t in times]}}}


PF, PR = 4.0, 6.0
plume_fall = particle_anim("particle_plume_fall", PF, lambda t: (20 * math.sin(TAU * t / PF), 360 * t / PF, 14 * math.cos(2 * TAU * t / PF)), 24)
plume_rest = particle_anim("particle_plume_rest", PR, lambda t: (0, 0, 1.2 * math.sin(TAU * t / PR)), 12)

ANIMS = [idle, walk, run, sneak, fly, hurt, plume_fall, plume_rest]
assert 4 <= len(EMITS) <= 6 and 6 <= len(PLUMES) <= 8 and 40 <= len(elements) <= 120, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
# Particules qui tombent et se posent : réservées aux ailes (.claude/rules/retours-en-jeu.md).
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from particules import retirer_particules
retirer_particules(model)
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;", len(EMITS), "emit_")
