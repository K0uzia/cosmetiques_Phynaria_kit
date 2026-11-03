"""Aura bulle de chewing-gum : une grosse bulle rose bonbon flotte à côté de l'épaule droite, gonfle par petites bouffées,
éclate (lambeaux qui jaillissent) puis réapparaît petite et regonfle. Design original, ensemble « Kawaii ».
Écrit aura_bulle_chewing_gum.png, aura_bulle_chewing_gum_e.png et .build/aura_bulle_chewing_gum_brut.bbmodel à côté de ce script.

Construction ronde : coque de 72 pastilles (0,3 px) tangentes à la sphère, aux directions réparties par répulsion. Chaque pastille est
découpée par alpha selon sa cellule (point gardé s'il est sous les plans des 41 autres) : deux plans tangents à même distance
se coupent pile sur la frontière des cellules, donc les pastilles se raboutent en polyèdre convexe à 72 facettes,
sans écaille ni recouvrement visible. Silhouette ronde à ~3 % près sous tous les angles, aucun plan intérieur
visible, tranches transparentes. Chaque pastille est peinte d'après le point de sphère qu'elle couvre (clair en haut, plus
foncé en bas, reflets fixes) : seul l'éclairage du jeu facette légèrement. Âme pleine au centre, sous la coque.

Groupes : body > choc (hurt seul) > flotte (flottement, décalage par état) > bulle (scale : gonfle / éclate) et eclat > frag_k
(lambeaux : scale et position, cachés hors de l'éclat). particle_gomme / particle_bullette à la racine, emit_ sur la bulle.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "aura_bulle_chewing_gum"
AVEC_E = True       # calque _e embarqué en seconde texture (correctif du clignotement annoncé le 2026-11-03, à vérifier en jeu)
TEX = 512
SS = 4
TAU = 2 * math.pi
UP = np.array((0.0, 1.0, 0.0))


def lerp(a, b, k):
    return a + (b - a) * k


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


# ------------------------------------------------------------------ textures
# Rose bonbon poussé vers le blanc (la lumière chaude de nuit vire au saumon) ; contraste de valeur net haut / bas.
C_LIGHT = np.array((255, 214, 233), np.float32)
C_MID = np.array((255, 158, 202), np.float32)
C_DARK = np.array((214, 92, 152), np.float32)
C_LIMB = np.array((190, 70, 132), np.float32)
C_BOUNCE = np.array((255, 196, 222), np.float32)
C_WHITE = np.array((255, 255, 255), np.float32)
C_HALO = np.array((255, 236, 244), np.float32)
L_WORLD = unit((-0.3, 0.8, -0.5))
E_BG = np.array((14, 5, 10), np.float32)       # fond additif très sombre
E_HI = np.array((190, 186, 190), np.float32)   # seul le reflet brille


def finish(col, alpha, W, H, ecol=None):
    """Réduit la peinture sur-échantillonnée : alpha 0/255, couleur moyenne hors silhouette."""
    def down(c):
        return np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    rgb = down(col)
    solid = np.array(Image.fromarray((alpha * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = rgb
    if solid.any():
        arr[~solid, :3] = rgb[solid].mean(axis=0).astype(np.uint8)
    arr[..., 3] = solid * 255
    em = np.zeros((H, W, 4), np.uint8)
    if ecol is not None:
        em[..., :3] = np.minimum(down(ecol), 190)
        em[..., 3] = arr[..., 3]
    return arr, em


HL = [(unit((-0.38, 0.72, -0.58)), 0.95, 0.932),    # gros reflet : haut, côté face 3/4 (≈ 18°)
      (unit((0.42, 0.66, 0.62)), 0.978, 0.968),    # reflet plus petit au dos, pour qu'on en voie un de partout
      (unit((0.32, 0.30, -0.9)), 0.9965, 0.994)]   # petite étincelle
LIM_V = unit((0, 0, 1))


def sphere_color(s):
    """Couleur de la bulle au point s (unitaire) et calque lumineux."""
    hs = s @ UP
    t = (1 - hs) / 2                                  # 0 en haut, 1 en bas
    col = lerp(np.broadcast_to(C_LIGHT, s.shape), C_MID, smooth(t / 0.55)[..., None])
    col = lerp(col, C_DARK, smooth((t - 0.55) / 0.45)[..., None])
        # contre-jour rosé tout en bas : l'effet « translucide » peint
    col = lerp(col, C_BOUNCE, (smooth((t - 0.86) / 0.1) * 0.5)[..., None])
    ecol = np.broadcast_to(E_BG, s.shape).copy()
    for lh, c1, c2 in HL:
        c = s @ lh
        col = lerp(col, C_HALO, smooth((c - c2) / 0.01)[..., None])
        core = smooth((c - c1) / 0.006)[..., None]
        col = lerp(col, C_WHITE, core)
        ecol = lerp(ecol, E_HI, core)
    return col, ecol


def plate_face(n, ex, ey, h, others, W=40):
    """Pastille tangente : pixel (x à droite, y en haut) -> point p = h·n + x·ex + y·ey, gardé si p est sous le plan de
    chaque autre pastille (cellule du polyèdre, marge MARGE) ; couleur du point de sphère sous lui."""
    w = W * SS
    g = ((np.arange(w) + 0.5) / w * 2 - 1) * PLATE_HALF
    x, y = np.meshgrid(g, -g)
    p = h * n + x[..., None] * ex + y[..., None] * ey
    alpha = (p @ np.array(others).T).max(axis=-1) < h + MARGE
    assert not (alpha[0].any() or alpha[-1].any() or alpha[:, 0].any() or alpha[:, -1].any()), "cellule plus grande que la pastille"
    sph = p / np.linalg.norm(p, axis=-1, keepdims=True)
    col, ecol = sphere_color(sph)
    return finish(col, alpha, W, W, ecol)


def splat(W, seed, ring=False):
    """Lambeau de gomme (ou mini-bulle si ring) : contour rond à lobes, ombre peinte, petit reflet."""
    rng = np.random.default_rng(seed)
    w = W * SS
    g = (np.arange(w) + 0.5) / w * 2 - 1
    x, y = np.meshgrid(g, -g)
    a = np.arctan2(y, x)
    r = np.sqrt(x * x + y * y)
    if ring:
        lim = 0.9 + 0 * a
    else:
        ph = rng.uniform(0, TAU, 3)
        lim = 0.7 + 0.12 * np.sin(3 * a + ph[0]) + 0.08 * np.sin(5 * a + ph[1]) + 0.05 * np.sin(2 * a + ph[2])
    q = r / lim
    alpha = q < 1
    t = (1 - y) / 2
    col = lerp(np.broadcast_to(C_LIGHT, x.shape + (3,)), C_MID, smooth(t / 0.6)[..., None])
    col = lerp(col, C_DARK, smooth((t - 0.5) / 0.5)[..., None])
    col = lerp(col, C_LIMB, smooth((q - 0.72) / 0.28)[..., None] * 0.5)
    hi = np.hypot((x + 0.22) / 0.26, (y - 0.3) / 0.18) < 1
    col = lerp(col, C_WHITE, hi[..., None] * 1.0)
    ecol = np.broadcast_to(E_BG, col.shape).copy()
    ecol = lerp(ecol, E_HI * 0.8, hi[..., None] * 1.0)
    return finish(col, alpha, W, W, ecol)


UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_cur = [0, 0, 0]


def place(name, im, em):
    h, w = im.shape[:2]
    if _cur[0] + w > TEX:
        _cur[:] = [0, _cur[1] + _cur[2] + 2, 0]
    x, y = _cur[0], _cur[1]
    assert y + h <= TEX - 6, "atlas plein"
    tex[y:y + h, x:x + w] = im
    tex_e[y:y + h, x:x + w] = em
    UV[name] = (x, y, x + w, y + h)
    _cur[0] += w + 2
    _cur[2] = max(_cur[2], h)


# 72 directions réparties par répulsion (départ spirale de Fibonacci, déterministe) : rayon de couverture ~17°
R_B = 3.5                                        # rayon gonflée (diamètre 7 px)
N_P = 72
H_T = R_B * 0.975                                # distance du centre aux faces : sommets du polyèdre à ≤ 1,02 R
PLATE_HALF = H_T * math.tan(math.radians(22))  # demi-côté du cube porteur (couvre la plus grande cellule)
MARGE = 0.01                                     # px de recouvrement : bouche les fentes sans écaille visible


def spread(N, it=600):
    i = np.arange(N) + 0.5
    y = 1 - 2 * i / N
    r = np.sqrt(1 - y * y)
    a = math.pi * (3 - 5 ** 0.5) * i
    P = np.stack([r * np.cos(a), y, r * np.sin(a)], 1)
    for _ in range(it):
        d = P[:, None, :] - P[None, :, :]
        dist = np.linalg.norm(d, axis=2) + np.eye(N)
        P = P + (d / dist[..., None] ** 3).sum(1) * 0.002
        P /= np.linalg.norm(P, axis=1)[:, None]
    return [P[k] for k in range(N)]


DIRS = spread(N_P)
FRAMES = []
for k, n in enumerate(DIRS):
    ey = UP - (UP @ n) * n
    ey = unit(ey) if np.linalg.norm(ey) > 1e-3 else np.array((0.0, 0.0, -1.0))
    ex = np.cross(ey, n)                              # ex × ey = n : face south = extérieur
    FRAMES.append((ex, ey, n))
    place(f"b{k}", *plate_face(n, ex, ey, H_T, [d for j, d in enumerate(DIRS) if j != k]))

for i in range(3):
    place(f"frag{i}", *splat(24, 10 + i))
place("gomme", *splat(24, 20))
place("bullette", *splat(24, 0, ring=True))
core = np.zeros((8, 8, 4), np.uint8)
core[..., :3] = lerp(C_MID, C_DARK, 0.15).astype(np.uint8)
core[..., 3] = 255
core_e = np.zeros((8, 8, 4), np.uint8)
core_e[..., :3] = E_BG.astype(np.uint8)
core_e[..., 3] = 255
place("core", core, core_e)

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


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx, ordre du mod et du renderer."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if abs(R[2, 0]) > 1 - 1e-9:                      # blocage de cardan (Y = ±90°) : X fixé à 0, tout passe dans Z
        return 0.0, math.degrees(ry), math.degrees(math.atan2(-R[0, 1], R[1, 1]))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(float(v), 2) for v in rotation]}
    return name


def cube(g, name, c, size, X, Y, faces):
    """Cube centré en c, axes X, Y (orthonormés), Z = X × Y."""
    c, size = np.asarray(c, float), np.asarray(size, float)
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    rot = euler(R_)
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in c - size / 2],
         "to": [round(float(v), 3) for v in c + size / 2], "origin": [round(float(v), 3) for v in c], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


SKIN = 0.3
C = V(10.0, 27.5, -2.5)      # centre de la bulle : à droite de la tête (x > 4 + rayon), un peu devant et au-dessus de l'épaule
D = 2 * R_B                  # diamètre gonflée ; 3 px dégonflée = scale 0,43
S0 = 3.0 / D

group("choc", C, parent=None)
group("flotte", C, parent="choc")
group("bulle", C, parent="flotte")
for k, (ex, ey, n) in enumerate(FRAMES):
    u0, v0, u1, v1 = UV[f"b{k}"]
    # dos : même découpe (UV miroir), sinon les coins carrés du dos ressortent entre les pastilles voisines
    faces = {"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
    cube("bulle", f"pastille{k}", C + n * (H_T - SKIN / 2), (2 * PLATE_HALF, 2 * PLATE_HALF, SKIN), ex, ey, faces)
CS = 2.6                     # âme : coin à 2,25 px du centre, sous la coque (face intérieure à 3,08 px)
cube("bulle", "ame", C, (CS, CS, CS), V(1, 0, 0), V(0, 1, 0), {f: list(UV["core"]) for f in ("north", "south", "east", "west", "up", "down")})

EMITS = {"gomme": [], "bullette": []}
for k, dv in enumerate((V(0.6, 0.5, -0.6), V(-0.7, 0.3, 0.6), V(0.5, -0.4, 0.7))):
    nm = "emit_gomme" + (str(k + 1) if k else "")
    EMITS["gomme"].append(group(nm, C + unit(dv) * (D / 2), parent="bulle"))
for k, dv in enumerate((V(0.2, 1, 0), V(-0.4, 0.9, -0.3))):
    nm = "emit_bullette" + (str(k + 1) if k else "")
    EMITS["bullette"].append(group(nm, C + unit(dv) * (D / 2 + 0.4), parent="flotte"))

# lambeaux de l'éclat : plaques rondes à lobes, face vers l'extérieur, cachées (scale ~0) hors de l'éclat
group("eclat", C, parent="flotte")
FRAGS = []
rng = np.random.default_rng(7)
for k in range(7):
    az = TAU * k / 7 + rng.uniform(-0.25, 0.25)
    el = rng.uniform(-0.55, 0.75)
    dvec = V(math.cos(el) * math.cos(az), math.sin(el), math.cos(el) * math.sin(az))
    p = C + dvec * 2.6
    g = group(f"frag{k}", p, parent="eclat")
    n = dvec
    ey = UP - (UP @ n) * n
    ey = unit(ey) if np.linalg.norm(ey) > 1e-6 else V(0, 0, -1)
    ex = np.cross(ey, n)
    sz = 1.5 + 0.3 * (k % 3) / 2
    tile = list(UV[f"frag{k % 3}"])
    cube(g, f"lambeau{k}", p, (sz, sz, SKIN), ex, ey, {"south": tile, "north": [tile[2], tile[1], tile[0], tile[3]],
                                                         "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
    FRAGS.append((g, dvec))


# Particules (guide, section 5 ter) : un seul cube de 0,3 px, face up seule, forme peinte, 0,3 px au-dessus du pivot.
def particle(nm, size):
    g = group(f"particle_{nm}", [0, 0, 0])
    PY = 0.3
    cube(g, nm, V(0, PY + SKIN / 2, 0), (size, SKIN, size), V(1, 0, 0), V(0, 1, 0), {"up": list(UV[nm])})
    return g


PG = particle("gomme", 1.2)
PB = particle("bullette", 1.4)


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone("choc")]}, bone(PG), bone(PB)]


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


HID = 0.02          # échelle « cachée » : jamais 0 strict (matrice dégénérée)


def bubble_scale(t, tp, smax):
    """Cycle de la bulle sur [0, tp + 0,6] : bouffées jusqu'à smax, tremblote, éclate, cachée, réapparaît à S0."""
    if t < tp:
        u = t / tp
        u = u - math.sin(TAU * 3 * u) / (TAU * 3) * 0.85          # 3 bouffées, petites pauses entre
        s = S0 + (smax - S0) * (1 - (1 - u) ** 1.4)
        wob = 0.035 * sm(t, tp - 0.6, tp - 0.1) * math.sin(TAU * (t - tp) / 0.2)
        return s * (1 + wob), s * (1 - wob), s * (1 + wob)
    d = t - tp
    if d < 0.04:
        k = smax * lerp(1.0, 1.1, d / 0.04)
        return k, k, k
    if d < 0.1:
        k = lerp(smax * 1.1, HID, (d - 0.04) / 0.06)
        return k, k, k
    if d < 0.38:
        return HID, HID, HID
    if d < 0.5:
        k = lerp(HID, S0 * 1.18, sm(d, 0.38, 0.5))
        return k, k, k
    k = lerp(S0 * 1.18, S0, sm(d, 0.5, 0.6))
    return k, k, k


def bubble_times(L, tp):
    n = int(round(tp * 12))
    ts = [i * tp / n for i in range(n)]
    ts += [tp + d for d in (0, 0.02, 0.04, 0.07, 0.1, 0.38, 0.41, 0.44, 0.47, 0.5, 0.55, 0.6)]
    return [t for t in ts if t <= L + 1e-6]


def frag_anim(tp, L, dvec, k):
    """Lambeau : jaillit vers l'extérieur avec l'éclat, se rétrécit sur place, caché le reste du cycle (fin = début)."""
    t1 = tp + 0.04
    ts = [0.0, t1 - 0.001, t1, t1 + 0.06, t1 + 0.14, t1 + 0.22, t1 + 0.3, t1 + 0.31, L]
    sc, po, ro = [], [], []
    for t in ts:
        d = t - t1
        if d < 0 or d > 0.3:
            s, dist = HID, 0.0
        else:
            s = lerp(0.4, 1.0, sm(d, 0, 0.06)) * (1 - sm(d, 0.16, 0.3) * (1 - HID))
            dist = 2.6 * (1 - (1 - min(d / 0.3, 1)) ** 2)
        sc.append(kf("scale", t, s, s, s))
        p = dvec * dist + V(0, -1.2 * (max(d, 0) / 0.3) ** 2 if 0 <= d <= 0.3 else 0, 0)
        po.append(kf("position", t, *p))
        ro.append(kf("rotation", t, 0, 0, (60 + 25 * k) * (min(max(d, 0), 0.3) / 0.3) if d <= 0.3 else 0))
    return sc + po + ro


def state(name, tp, smax, off, bob, ncyc, sway):
    """tp : durée de gonflage ; smax : échelle max ; off : décalage de la bulle (px) ; bob, ncyc : flottement Y ;
    sway : balancement (°). Durée = tp + 0,6 s, tout périodique sur la durée."""
    L = round(tp + 0.6, 3)
    A = {}
    A[groups["bulle"]["uuid"]] = {"name": "bulle", "type": "bone",
                                 "keyframes": [kf("scale", t, *bubble_scale(t, tp, smax)) for t in bubble_times(L, tp)] +
                                              [kf("scale", L, *bubble_scale(0.0, tp, smax))]}
    n = max(16, int(round(L * 8)))
    times = [i * L / n for i in range(n + 1)]
    w = TAU * ncyc / L
    keys = [kf("position", t, off[0] + 0.3 * bob * math.sin(w * t / ncyc), off[1] + bob * math.sin(w * t), off[2]) for t in times]
    keys += [kf("rotation", t, sway * 0.5 * math.sin(w * t + 1.1), 0, sway * math.sin(w * t / ncyc * max(1, ncyc // 2) + 0.4)) for t in times]
    A[groups["flotte"]["uuid"]] = {"name": "flotte", "type": "bone", "keyframes": keys}
    for k, (g, dvec) in enumerate(FRAGS):
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": frag_anim(tp, L, dvec, k)}
    return {"uuid": nuid(), "name": name, "loop": "loop", "override": False, "length": L, "snapping": 24, "selected": name == "idle",
            "animators": A}


idle = state("idle", 3.4, 1.0, (0, 0, 0), 0.45, 1, 4)
walk = state("walk", 3.0, 1.0, (0, -0.3, 0.8), 0.5, 2, 5)
run = state("run", 1.8, 0.92, (0.3, -0.8, 3.2), 0.35, 3, 6)          # traîne derrière, gonfle vite
sneak = state("sneak", 4.4, 0.85, (-0.6, -2.4, 0.4), 0.3, 1, 3)       # plus basse, plus petite, plus lente
fly = state("fly", 2.4, 1.0, (0.6, 1.4, 0.4), 0.8, 2, 7)              # plus haute, flottement ample
glide = state("glide", 2.4, 0.9, (0.0, -0.5, 2.6), 0.4, 2, 4)         # élytres : corps couché, la bulle file derrière l'épaule

# hurt 0,8 s : sursaut de côté puis tremblement amorti, sur `choc` seul (aucun état ne l'anime)
HU = 0.8
hts = [j * HU / 16 for j in range(17)]
tr = lambda t: math.sin(TAU * t * 5 / HU) * (1 - sm(t, 0.1, 0.7))
hurt = {"uuid": nuid(), "name": "hurt", "loop": "once", "override": False, "length": HU, "snapping": 24, "selected": False,
        "animators": {groups["choc"]["uuid"]: {"name": "choc", "type": "bone", "keyframes":
                      [kf("position", t, 1.2 * sm(t, 0, 0.06) * (1 - sm(t, 0.15, 0.7)), 0, 0) for t in hts] +
                      [kf("rotation", t, 0, 0, -9 * tr(t)) for t in hts] +
                      [kf("scale", t, 1 + 0.08 * tr(t), 1 - 0.08 * tr(t), 1 + 0.08 * tr(t)) for t in hts]}}}


def particle_anim(name, g, length, curve, n):
    times = [i * length / n for i in range(n + 1)]
    return {"uuid": nuid(), "name": name, "loop": "loop", "override": False, "length": length, "snapping": 24, "selected": False,
            "animators": {groups[g]["uuid"]: {"name": g, "type": "bone", "keyframes": [kf("rotation", t, *curve(t)) for t in times]}}}


gomme_fall = particle_anim("particle_gomme_fall", PG, 2.0, lambda t: (35 * math.sin(TAU * t / 2.0), 360 * t / 2.0, 20 * math.cos(TAU * t / 2.0)), 16)
gomme_rest = particle_anim("particle_gomme_rest", PG, 4.0, lambda t: (0, 0, 1.0 * math.sin(TAU * t / 4.0)), 8)
bull_fall = particle_anim("particle_bullette_fall", PB, 3.0, lambda t: (55 + 15 * math.sin(TAU * t / 3.0), 360 * t / 3.0, 10 * math.sin(2 * TAU * t / 3.0)), 18)
bull_rest = particle_anim("particle_bullette_rest", PB, 4.0, lambda t: (0, 0, 1.0 * math.sin(TAU * t / 4.0)), 8)

ANIMS = [idle, walk, run, sneak, fly, glide, hurt, gomme_fall, gomme_rest, bull_fall, bull_rest]
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


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(x) for x in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      sum(len(v) for v in EMITS.values()), "emit_")
