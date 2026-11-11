"""Béret tartelette : un béret dont la galette est une tartelette aux fraises. Ensemble « Pâtisserie » (fraise, vanille,
chocolat), thème Mignon. Design original. Remplace `chapeau_patisserie` (« Chapeau macaron », archivé le 2026-11-08 :
« les trucs kawaii sont tous bof », « revois les têtes », pas une simple pâtisserie posée sur la tête).
Écrit beret_patisserie.png, beret_patisserie_e.png et .build/beret_patisserie_brut.bbmodel à côté de ce script.

Analogie (fiche .claude/styles/patisserie.md) : un béret = une galette ronde plus large que la tête (plateau ≈ 1,5 fois la tête),
portée inclinée, qui retombe sur un côté, avec une petite queue au centre (le cabillou). Ici :
- le bord roulé du béret est la **pâte sablée cannelée** (30 cannelures dorées, crête plus cuite poudrée de sucre glace) ;
  le béret est décalé vers la droite et retombe sur la droite et l'arrière (cannelures plus longues et inclinées vers l'extérieur,
  seulement là où elles sont hors de la tête) ;
- le plateau est la **crème pâtissière** à la vanille (disque découpé, jaune crème franc, grains de vanille) ;
- deux couronnes de **demi-fraises nappées** debout, face coupée vers l'extérieur (cœur blanc, chair rose, reflet de nappage net) ;
- le cabillou est **une fraise entière** à l'envers, collerette verte en étoile et queue courte, avec un brin de menthe.
Volume : disques à silhouette ronde par alpha (dessous de pâte, crème), anneau de cannelures en vrais cubes, fraises en plaque
découpée (face coupée ou silhouette) + âme pleine en gradins derrière (vrai volume, rien de plat).

Contraintes tête : dessous à y = 32,72 sur la tête (≥ 32,62), rien sous 32,62 à moins de 4,62 px du centre (contrôle sur tous les
coins, dans toutes les poses, événements combinés à l'étirement le plus fort) ; pas d'attack ni de hurt (tools/reactions.py).
Animations : idle 8 s (respiration, « boing » vers 5 s, les fraises tremblent comme de la gelée), walk, run (le vent couche la
fraise du dessus et la menthe), sneak (se tasse), fly, glide, swim, fall. Échelles autour du dessous (pivot à y = 32,72).
event_equip (1,0 s) : la tartelette sort de rien (0 → 1,25 → 0,9 → 1), les demi-fraises tombent une à une en tournant autour
de la tartelette, la fraise du dessus en dernier ; un son (`block.honey_block.place`). event_unequip (0,6 s) : les fraises sautent,
la tartelette se tasse et disparaît (dernière image : échelle 0).
Fonctions avancées : calque `_e` (fond noir, seuls les reflets de nappage des fraises), aucune particule.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "beret_patisserie"
AVEC_E = True
TEX = 512
SS = 4
TAU = 2 * math.pi
RNG = np.random.default_rng(7)

# ------------------------------------------------------------------ palette (couleurs franches : pas de pastel délavé)
PATE_L, PATE_M, PATE_D, PATE_CUIT = (252, 204, 116), (228, 152, 64), (138, 70, 24), (186, 100, 36)
PATE_PALE = (242, 196, 124)
SUCRE = (255, 252, 246)
CREME_L, CREME_M, CREME_D = (255, 236, 168), (252, 206, 104), (214, 148, 64)
VANILLE = (96, 58, 34)
FR_L, FR_M, FR_D, FR_DD = (255, 104, 104), (222, 30, 52), (150, 10, 34), (98, 4, 24)
CHAIR, COEUR = (255, 150, 158), (255, 238, 236)
GRAINE, GRAINE_D = (255, 214, 92), (150, 70, 20)
VERT_L, VERT_M, VERT_D = (150, 214, 92), (72, 162, 62), (30, 92, 42)
MENTHE_L, MENTHE_M, MENTHE_D = (170, 242, 168), (84, 196, 116), (36, 118, 72)
E_REFLET = (172, 150, 150)


def C(c):
    return np.array(c, np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


def sm01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def mix(col, c, k):
    return lerp(col, C(c), np.clip(k, 0, 1)[..., None])


def finish(col, alpha):
    """Réduit la peinture sur-échantillonnée (SS) : alpha 0/255, couleur moyenne hors silhouette."""
    H, W = col.shape[0] // SS, col.shape[1] // SS
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    solid = np.array(Image.fromarray((np.asarray(alpha, np.float32) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = rgb
    if solid.any():
        arr[~solid, :3] = rgb[solid].mean(axis=0).astype(np.uint8)
    arr[..., 3] = solid * 255
    return arr


def grid(W, H):
    """Coordonnées normalisées : x de 0 à 1 (gauche → droite), y de 0 à 1 (haut → bas), en sur-échantillonné."""
    xs = (np.arange(W * SS) + 0.5) / (W * SS)
    ys = (np.arange(H * SS) + 0.5) / (H * SS)
    return np.meshgrid(xs, ys)


def dots(W, H, n, rad, seed, minsep=None):
    """Masque de n points ronds (rayon en texels), placés au hasard sans se toucher."""
    rng = np.random.default_rng(seed)
    gx, gy = grid(W, H)
    px, py = gx * W, gy * H
    m = np.zeros(gx.shape, np.float32)
    pts = []
    minsep = minsep or rad * 3
    for _ in range(n * 20):
        if len(pts) >= n:
            break
        x, y = rng.uniform(rad, W - rad), rng.uniform(rad, H - rad)
        if all((x - a) ** 2 + (y - b) ** 2 > minsep ** 2 for a, b in pts):
            pts.append((x, y))
            m = np.maximum(m, np.clip(1.2 - np.hypot(px - x, py - y) / rad, 0, 1))
    return m


# ------------------------------------------------------------------ tuiles
def t_dessous(S=168):
    gx, gy = grid(S, S)
    u, v = gx * 2 - 1, gy * 2 - 1
    r = np.hypot(u, v)
    col = np.empty(r.shape + (3,), np.float32); col[...] = PATE_PALE
    col = mix(col, PATE_CUIT, sm01((r - 0.72) / 0.26) * 0.8)                 # bord plus cuit
    piq = (np.sin(u * 22) * np.sin(v * 22) > 0.93) & (r < 0.8)               # trous de fourchette (pâte piquée)
    col = mix(col, PATE_D, piq * 0.55)
    return finish(col, r < 1.0)


def t_creme(S=168):
    gx, gy = grid(S, S)
    u, v = gx * 2 - 1, gy * 2 - 1
    r = np.hypot(u, v)
    col = np.empty(r.shape + (3,), np.float32); col[...] = CREME_M
    col = mix(col, CREME_L, sm01(1 - np.hypot(u + 0.35, v + 0.4) / 0.75) * 0.8)   # lumière chaude du dessus
    col = mix(col, CREME_D, sm01((r - 0.86) / 0.12) * 0.85)                        # ombre de la paroi de pâte
    sp = dots(S, S, 60, 0.9, 3, minsep=8)
    col = mix(col, VANILLE, sp * 0.8)
    return finish(col, r < 1.0)


def t_cannelure(W=22, H=64, kind="out"):
    """Face d'une cannelure ; la tuile représente 4 px de haut (crête en haut)."""
    gx, gy = grid(W, H)
    s = np.cos((gx - 0.5) * math.pi) ** 1.3 if kind == "out" else np.ones_like(gx) * 0.55
    col = lerp(C(PATE_D), C(PATE_M), sm01(s / 0.55)[..., None])
    col = mix(col, PATE_L, sm01((s - 0.6) / 0.4) * 0.9)                          # arête claire de la cannelure, creux bruns
    col = mix(col, PATE_PALE, sm01((gy - 0.35) / 0.4) * 0.45)                 # bas de la paroi moins cuit
    col = mix(col, PATE_CUIT, sm01(1 - gy / 0.14) * 0.6 * s)                  # crête dorée
    col = mix(col, PATE_D, sm01(1 - np.abs(gy - 0.15) / 0.03) * 0.35)        # petit pli sous la crête
    grain = np.array(Image.fromarray((np.random.default_rng(4).random((H, W)) * 255).astype(np.uint8)).resize((W * SS, H * SS), Image.NEAREST)) / 255.0
    col = col * (1 - 0.06 * grain)[..., None]                                     # grain de la pâte sablée
    cuit = dots(W, H, 3, 2.2, 8 if kind == "out" else 9, minsep=10) * (gy > 0.2) * (gy < 0.6)
    col = mix(col, PATE_CUIT, cuit * 0.45)                                        # taches plus dorées, irrégulières
    if kind == "out":
        sug = dots(W, H, 14, 0.8, 11, minsep=3.5) * (gy < 0.12)
        col = mix(col, SUCRE, sug)
    return finish(col, np.ones_like(gx))


def t_crete(S=22):
    gx, gy = grid(S, S)
    s = np.cos((gx - 0.5) * math.pi) ** 0.6
    col = lerp(C(PATE_CUIT), C(PATE_L), s[..., None] * 0.8)
    col = mix(col, SUCRE, dots(S, S, 26, 0.9, 5, minsep=3.2))
    return finish(col, np.ones_like(gx))


def t_flat(c, W=8, H=8):
    gx, _ = grid(W, H)
    col = np.empty(gx.shape + (3,), np.float32); col[...] = c
    return finish(col, np.ones_like(gx))


def w_demi(v):
    """Demi-largeur (0..1) de la coupe d'une fraise debout, pointe en haut : v = 0 en bas (côté queue), 1 en haut."""
    low = 0.8 + 0.18 * np.sin(np.clip(v / 0.28, 0, 1) * math.pi / 2)
    high = 0.98 * np.clip(1 - ((v - 0.28) / 0.72) ** 2, 0, 1) ** 0.55
    return np.where(v < 0.28, low, high)


def w_entiere(v):
    """Fraise entière à l'envers (pointe en bas dans la crème) : v = 0 en bas (pointe), 1 en haut (épaules sous la collerette)."""
    low = 0.98 * np.clip(1 - ((v - 0.7) / 0.7) ** 2, 0, 1) ** 0.55
    high = 0.98 * np.sqrt(np.clip(1 - ((v - 0.7) / 0.34) ** 2, 0, 1))
    return np.where(v < 0.7, low, high)


def peau(gx, gy, W, H, seed, wfun, inv=False):
    """Peau de fraise rouge brillante : graines jaunes dans de petits creux, lumière en haut à gauche, reflet de nappage."""
    u = gx * 2 - 1
    v = 1 - gy
    w = wfun(v)
    a = (np.abs(u) < w) & (v < 0.985) & (v > 0.01)
    e = np.clip(1 - np.abs(u) / np.maximum(w, 1e-3), 0, 1)                    # 0 au bord, 1 au milieu
    col = lerp(C(FR_D), C(FR_M), sm01(e / 0.6)[..., None])
    col = mix(col, FR_L, sm01(1 - np.hypot(u + 0.35, (v - 0.65) * 1.4) / 0.55) * 0.55)
    col = mix(col, FR_DD, sm01((0.18 - v) / 0.18) * 0.5 if not inv else sm01((v - 0.82) / 0.18) * 0.4)
    # graines en quinconce
    px, py = gx * W, gy * H
    rows = np.round(py / 4.2)
    qx = px + (rows % 2) * 2.1
    cx = np.round(qx / 4.2) * 4.2
    d = np.hypot(qx - cx, py - rows * 4.2)
    rng = np.random.default_rng(seed)
    jit = rng.random(d.shape) * 0 + 1
    col = mix(col, FR_DD, sm01(1 - d / 1.5) * 0.5 * (e > 0.08) * jit)
    col = mix(col, GRAINE, sm01(1 - d / 0.8) * (e > 0.1))
    col = mix(col, GRAINE_D, sm01(1 - np.hypot(qx - cx + 0.3, py - rows * 4.2 + 0.3) / 0.35) * (e > 0.1) * 0.6)
    # reflet de nappage : fenêtre nette + point
    hl = (np.abs(u + 0.42) < 0.11) & (np.abs(v - 0.62) < 0.15) | (np.hypot(u + 0.2, (v - 0.8) * 1.2) < 0.07)
    col = mix(col, (255, 255, 255), hl * 0.95)
    return col, a, hl & a


def t_coupe(W, H, seed):
    """Face coupée d'une demi-fraise : peau rouge fine, chair qui pâlit vers le cœur blanc, fibres, nappage brillant."""
    gx, gy = grid(W, H)
    u, v = gx * 2 - 1, 1 - gy
    w = w_demi(v)
    a = (np.abs(u) < w) & (v < 0.985) & (v > 0.01)
    e = np.clip(1 - np.abs(u) / np.maximum(w, 1e-3), 0, 1)
    col = lerp(C(FR_D), C(FR_M), sm01(e / 0.12)[..., None])
    col = mix(col, CHAIR, sm01((e - 0.14) / 0.35))
    core = sm01(1 - np.abs(u) / (0.2 * (1 - v * 0.7) + 0.02)) * sm01((0.88 - v) / 0.2)
    col = mix(col, COEUR, np.maximum(core, sm01((e - 0.55) / 0.3) * 0.55))
    fib = (np.sin(np.arctan2(v - 0.15, u) * 14) > 0.75) & (e > 0.2) & (core < 0.5)
    col = mix(col, FR_M, fib * 0.35)
    col = mix(col, (255, 220, 220), sm01(1 - np.hypot(u + 0.3, v - 0.6) / 0.5) * 0.25)      # nappage : brillance générale
    hl = ((np.abs(u + 0.45) < 0.09) & (np.abs(v - 0.55) < 0.14)) | (np.hypot(u + 0.25, (v - 0.78) * 1.2) < 0.065)
    col = mix(col, (255, 255, 255), hl * 0.95)
    return finish(col, a), finish(np.where(hl[..., None] & a[..., None], C(E_REFLET), C((0, 0, 0))), a)


def t_peau(W, H, seed, wfun):
    gx, gy = grid(W, H)
    col, a, hl = peau(gx, gy, W, H, seed, wfun)
    return finish(col, a), finish(np.where(hl[..., None], C(E_REFLET), C((0, 0, 0))), a)


def t_peau_carre(S=20, seed=1):
    gx, gy = grid(S, S)
    col, a, _ = peau(gx * 0.5 + 0.25, gy * 0.5 + 0.25, S * 2, S * 2, seed, lambda v: np.ones_like(v) * 9)
    col = mix(col, FR_M, np.ones_like(gx) * 0.25)
    return finish(col, np.ones_like(gx))


def t_collerette(S=56):
    gx, gy = grid(S, S)
    u, v = gx * 2 - 1, gy * 2 - 1
    r, th = np.hypot(u, v), np.arctan2(v, u)
    lobe = np.abs(np.cos(3 * th)) ** 1.3
    R = 0.38 + 0.6 * lobe
    a = r < R
    col = lerp(C(VERT_D), C(VERT_M), sm01(r / 0.5)[..., None])
    col = mix(col, VERT_L, sm01((r - R * 0.55) / (R * 0.4)) * 0.6 * lobe)
    vein = (np.abs(np.sin(3 * th)) < 0.06) & (r > 0.2) & (r < R * 0.85)
    col = mix(col, VERT_D, vein * 0.7)
    col = mix(col, (120, 96, 46), sm01(1 - r / 0.16))                          # attache de la queue
    return finish(col, a)


def t_sepale(W=16, H=32):
    gx, gy = grid(W, H)
    u, v = gx * 2 - 1, 1 - gy
    w = 0.9 * np.clip(np.sin(np.clip(v, 0, 1) * math.pi * 0.62 + 0.25), 0, 1) * (1 - 0.6 * np.clip(v - 0.6, 0, 1))
    a = (np.abs(u) < w) & (v > 0.0) & (v < 0.97)
    col = lerp(C(VERT_D), C(VERT_M), sm01(1 - np.abs(u) / 0.9 + 0.2)[..., None])
    col = mix(col, VERT_L, sm01((v - 0.45) / 0.5) * 0.7)
    col = mix(col, VERT_D, (np.abs(u) < 0.08) * 0.6)
    return finish(col, a)


def t_menthe(W=28, H=44):
    gx, gy = grid(W, H)
    u, v = gx * 2 - 1, 1 - gy
    w = 0.92 * np.clip(np.sin(np.clip(v, 0, 1) * math.pi), 0, 1) ** 0.75 * (1 + 0.05 * np.sin(v * 40))   # bord finement denté
    a = (np.abs(u) < w) & (v > 0.02) & (v < 0.98)
    col = lerp(C(MENTHE_D), C(MENTHE_M), sm01(np.abs(u) / 0.25 + 0.3)[..., None])
    col = mix(col, MENTHE_L, sm01(1 - np.hypot(u + 0.3, v - 0.6) / 0.45) * 0.55)
    nerv = (np.abs(u) < 0.05) | ((np.abs(np.abs(u) * 1.6 - (v % 0.22) * 4) < 0.08) & (np.abs(u) < w * 0.8))
    col = mix(col, MENTHE_L, nerv * 0.6)
    return finish(col, a)


# ------------------------------------------------------------------ atlas
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
    e = np.zeros_like(im); e[..., 3] = im[..., 3]
    tex_e[y:y + h, x:x + w] = e if em is None else em
    UV[name] = (x, y, x + w, y + h)
    _cur[0] += w + 2
    _cur[2] = max(_cur[2], h)


place("dessous", t_dessous())
place("creme", t_creme())
place("collerette", t_collerette())
place("cann_out", t_cannelure(kind="out"))
place("cann_in", t_cannelure(kind="in"))
place("cann_cote", t_flat(PATE_D, 8, 64))
place("crete", t_crete())
place("pate_bas", t_flat(PATE_PALE))
for k in range(3):
    place(f"coupe{k}", *t_coupe(40, 52, k))
    place(f"peau{k}", *t_peau(40, 52, 10 + k, w_demi))
place("entiere", *t_peau(48, 58, 21, w_entiere))
place("peau_carre", t_peau_carre())
place("menthe", t_menthe())
place("sepale", t_sepale())
place("tige", t_flat((96, 132, 50), 6, 12))
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
GROUP_ELS = {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


def rot_matrix(rx, ry, rz):
    """Même ordre que le mod et le renderer : R = Rz Ry Rx, degrés."""
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def euler(R):
    if abs(R[2, 0]) > 0.99999:
        sg = -1.0 if R[2, 0] > 0 else 1.0
        out = (math.degrees(math.atan2(sg * R[0, 1], R[1, 1])), sg * 90.0, 0.0)
    else:
        ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
        out = (math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0])))
    assert np.allclose(rot_matrix(*out), R, atol=1e-6), "euler : rotation mal reconstruite"
    return out


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups and len(name) <= 64
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(float(v), 2) for v in rotation]}
    GROUP_ELS[name] = []
    return name


def add_el(g, name, c, size, rot, faces):
    c, size = np.asarray(c, float), np.asarray(size, float)
    rot = [round(float(v), 2) for v in rot]
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in c - size / 2],
         "to": [round(float(v), 3) for v in c + size / 2], "origin": [round(float(v), 3) for v in c], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = rot
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])
    R = rot_matrix(*rot)
    hs = size / 2
    GROUP_ELS[g] += [c + R @ (hs * V(sx, sy, sz)) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]


def cube_axes(g, name, c, size, X, Y, faces):
    Y = unit(Y)
    X = unit(X - np.dot(X, Y) * Y)              # Y prime, X redressé
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    add_el(g, name, c, size, euler(R_), faces)


def F(**kw):
    """Faces : tuile nommée, liste d'UV, ou absente = transparente."""
    out = {f: list(CLEAR) for f in ("north", "south", "east", "west", "up", "down")}
    for f, t in kw.items():
        out[f] = list(UV[t]) if isinstance(t, str) else list(t)
    return out


def all_faces(t):
    return F(north=t, south=t, east=t, west=t, up=t, down=t)


def uv_haut(t, h, full=4.0):
    """Partie haute d'une tuile qui représente `full` px de haut."""
    x0, y0, x1, y1 = UV[t]
    return [x0, y0, x1, y0 + (y1 - y0) * min(1.0, h / full)]


HEAD_TOP = 32.72              # dessous du béret : au-dessus de la seconde couche du skin (32,5), règle ≥ 32,62
HALF = 4.62                   # demi-côté de la tête + seconde couche + marge
CX, CZ = 1.2, 0.6             # le béret est décalé vers la droite et un peu vers l'arrière (porté incliné)
PIV = V(CX, HEAD_TOP, CZ)
BER = group("beret", PIV)

R_IN, R_OUT, N_CANN = 5.3, 6.3, 30
Y_CREME0, Y_CREME1 = 33.62, 33.97
R_DESSOUS, R_CREME = 5.6, 5.45
TILT = 7.0                    # le plateau penche vers la droite (porté incliné) ; keyframe/rotation -Z = côté droit qui descend
ST = math.sin(math.radians(TILT))
GARN = group("garniture", V(CX, Y_CREME1, CZ), BER, rotation=(0, 0, -TILT))

# dessous de pâte (disque) et crème pâtissière (disque) ; tranches transparentes
add_el(BER, "dessous_pate", (CX, HEAD_TOP + 0.1 + 0.175, CZ), (2 * R_DESSOUS, 0.35, 2 * R_DESSOUS), (0, 0, 0), F(down="dessous"))
add_el(GARN, "creme", (CX, (Y_CREME0 + Y_CREME1) / 2, CZ), (2 * R_CREME, Y_CREME1 - Y_CREME0, 2 * R_CREME), (0, 0, 0), F(up="creme"))


def hors_tete(pts, marge):
    """Distance minimale (méthode du carré) des points à la tête, négative si un point est au-dessus d'elle."""
    return min(max(abs(p[0]), abs(p[2])) - HALF for p in pts) - marge


UP = V(0, 1, 0)
chord = 2 * R_IN * math.sin(math.pi / N_CANN)
for i in range(N_CANN):
    th = TAU * (i + 0.5) / N_CANN
    n = V(math.cos(th), 0, math.sin(th))
    t = V(math.sin(th), 0, -math.cos(th))
    xr = (R_IN + R_OUT) / 2 * math.cos(th)
    top = 34.38 - ST * xr + 0.04 * math.sin(i * 2.7)          # la crête suit le plateau penché
    # bas de la paroi posé à plat sur la tête partout : seule la crête suit le plateau penché (un bas « tombé » sur le côté
    # droit faisait des cassures en marches au coin de la tête, où la paroi doit rester à y >= 32,62)
    phi = 0.0
    Y = math.cos(phi) * UP - math.sin(phi) * n       # le bas part vers l'extérieur quand le béret retombe
    h = top - (HEAD_TOP - 0.02)
    topc = V(CX, top, CZ) + n * (R_IN + R_OUT) / 2
    c = topc - Y * h / 2
    cube_axes(BER, f"cannelure_{i}", c, (chord, h, R_OUT - R_IN), t, Y,
              F(south=uv_haut("cann_out", h), north=uv_haut("cann_in", h), east=uv_haut("cann_cote", h),
                west=uv_haut("cann_cote", h), up="crete", down="pate_bas"))
    # bourrelet roulé (le bord du béret) : barre carrée tournée de 45° autour de la tangente, qui déborde un peu dehors
    lc = 2 * 6.12 * math.sin(math.pi / N_CANN)
    Yl = math.cos(math.radians(45)) * Y + math.sin(math.radians(45)) * np.cross(t, Y)
    cube_axes(BER, f"bourrelet_{i}", topc + n * 0.3 + Y * 0.02, (lc, 0.56, 0.56), t, Yl, all_faces("crete"))

# demi-fraises : face coupée vers l'extérieur, le haut penché vers le centre (face visible de côté comme de dessus)
FRAISES = []


def demi_fraise(name, th, r, W, H, lean, k, dy=0.0):
    n = V(math.cos(th), 0, math.sin(th))
    t = V(math.sin(th), 0, -math.cos(th))
    base = V(CX, Y_CREME1 - 0.1 + dy, CZ) + n * r
    g = group(name, base, GARN)
    a = math.radians(lean)
    Y = math.cos(a) * UP - math.sin(a) * n
    Z = np.cross(t, Y)
    # plaque coupée (0,3 px) à l'avant, âme rouge pleine en deux gradins derrière
    add_el_axes = lambda nm, c, size, faces: cube_axes(g, nm, c, size, t, Y, faces)
    add_el_axes(f"{name}_coupe", base + Y * H / 2 + Z * 0.15, (W, H, 0.3), F(south=f"coupe{k}", north=f"peau{k}"))
    add_el_axes(f"{name}_ame1", base + Y * (H * 0.3) - Z * 0.2, (W * 0.78, H * 0.6, 0.5), all_faces("peau_carre"))
    add_el_axes(f"{name}_ame2", base + Y * (H * 0.66) - Z * 0.12, (W * 0.46, H * 0.32, 0.36), all_faces("peau_carre"))
    FRAISES.append((g, th, t))


# rosace : les demi-fraises sont couchées vers le centre (face coupée tournée vers le haut et l'extérieur), en tuiles qui montent
# vers la fraise du milieu ; jamais debout (une couronne de pointes rouges se lirait comme une couronne)
N_EXT, N_INT = 11, 7
for i in range(N_EXT):
    demi_fraise(f"fraise_ext_{i}", TAU * i / N_EXT + 0.2, 4.3, 2.0, 2.6, 42 + 4 * math.sin(i * 1.9), i % 3)
for i in range(N_INT):
    demi_fraise(f"fraise_int_{i}", TAU * (i + 0.5) / N_INT + 0.2, 2.55, 1.8, 2.5, 26 + 4 * math.sin(i * 2.3), (i + 1) % 3, dy=1.05)

# fraise entière (le cabillou du béret) : pointe dans la crème, collerette verte et queue courte en haut, un peu penchée
FH, FW = 3.8, 2.8
CB = V(CX + 0.1, Y_CREME1 + 0.75, CZ - 0.05)
COEUR_G = group("fraise_coeur", CB, GARN)
RT = rot_matrix(-6, 0, -8)
Xa, Ya, Za = RT @ V(1, 0, 0), RT @ UP, RT @ V(0, 0, 1)
cube_axes(COEUR_G, "coeur_plaque_a", CB + Ya * FH / 2, (FW, FH, 0.3), Xa, Ya, F(south="entiere", north="entiere"))
cube_axes(COEUR_G, "coeur_plaque_b", CB + Ya * FH / 2, (FW, FH, 0.3), -Za, Ya, F(south="entiere", north="entiere"))
for k, (y0, y1, wk) in enumerate(((0.3, 1.1, 0.8), (1.1, 2.3, 1.6), (2.3, 3.3, 1.7))):
    q = rot_matrix(0, 45, 0)
    cube_axes(COEUR_G, f"coeur_ame{k}", CB + Ya * (y0 + y1) / 2, (wk, y1 - y0, wk), RT @ q @ V(1, 0, 0), Ya, all_faces("peau_carre"))
TOPF = CB + Ya * (FH - 0.12)
QUEUE = group("queue_fraise", TOPF, COEUR_G)
for k in range(6):                                    # collerette : six sépales qui retombent sur les épaules de la fraise
    az = math.radians(k * 60 + 15 + 9 * math.sin(k * 2.1))
    dh = math.cos(az) * Xa + math.sin(az) * Za
    dr = unit(dh * math.cos(math.radians(24)) - Ya * math.sin(math.radians(24)))
    cube_axes(QUEUE, f"sepale_{k}", TOPF + Ya * 0.1 + dr * 0.72, (0.72, 1.45, 0.3), np.cross(Ya, dr), dr, F(south="sepale", north="sepale"))
Yq = unit(Ya + 0.35 * Xa)
cube_axes(QUEUE, "queue", TOPF + Yq * 0.6, (0.36, 0.9, 0.36), Xa, Yq, all_faces("tige"))
Yq2 = unit(Ya + 1.1 * Xa)
cube_axes(QUEUE, "queue_bout", TOPF + Yq * 1.0 + Yq2 * 0.28, (0.3, 0.56, 0.3), Za, Yq2, all_faces("tige"))

# brin de menthe : deux feuilles glissées entre la fraise entière et la couronne intérieure, côté gauche-avant
MB = V(CX - 1.3, Y_CREME1 + 2.1, CZ - 1.2)
MENTHE = group("menthe", MB, GARN)
for k, (az, el) in enumerate(((-150, 42), (-100, 55), (-205, 50))):
    d_ = V(math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el)), math.sin(math.radians(az)) * math.cos(math.radians(el)))
    side = unit(np.cross(UP, d_))
    cube_axes(MENTHE, f"menthe_{k}", MB + d_ * 1.05, (1.3, 2.1, 0.3), side, d_, F(south="menthe", north="menthe"))


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "head", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone(BER)]}]

# ------------------------------------------------------------------ animations (valeurs de keyframe : +X le haut part en arrière,
# +Z le côté droit monte ; échelles du béret autour de son dessous)


def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 3)), "y": str(round(v[1] + 0.0, 3)), "z": str(round(v[2] + 0.0, 3))}],
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


def keys(t, pts):
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * sm(t, t0, t1)
    return pts[-1][1]


def squash(k):
    return (1 + 0.45 * k, 1 - k, 1 + 0.45 * k)


def s(L, k=1, ph=0.0):
    return lambda t: math.sin(TAU * (k * t / L - ph))


ALL_G = [BER] + [g for g, _, _ in FRAISES] + [COEUR_G, QUEUE, MENTHE]
POSES = {}


def anim(name, L, fn, loop="loop", fps=10):
    """fn(t) -> {groupe: {"rot":(x,y,z), "pos":(…), "scale":(…)}}"""
    n = max(8, int(round(L * fps)))
    times = [i * L / n for i in range(n + 1)]
    samples = [(t, fn(t % L if loop == "loop" and t < L - 1e-9 else (0.0 if loop == "loop" else t))) for t in times]
    A = {}
    for g in ALL_G:
        kfs = []
        for ch, dflt in (("rot", (0, 0, 0)), ("pos", (0, 0, 0)), ("scale", (1, 1, 1))):
            if any(ch in s_.get(g, {}) for _, s_ in samples):
                kfs += [kf({"rot": "rotation", "pos": "position", "scale": "scale"}[ch], t, s_.get(g, {}).get(ch, dflt)) for t, s_ in samples]
        if kfs:
            A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}
    POSES[name] = (L, fn, loop)
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": L, "snapping": 24,
            "selected": name == "idle", "animators": A}


def gelee(t, amp, f, ph=0.0, lean=0.0, roll=0.0):
    """Tremblement de chaque demi-fraise autour de son axe tangent (en retard selon sa place), plus une inclinaison commune."""
    out = {}
    for g, th, tg in FRAISES:
        a = amp(t, th) if callable(amp) else amp * math.sin(TAU * (f * t - ph) - th)
        out[g] = {"rot": (lean + a * tg[0], 0.0, roll + a * tg[2])}
    return out


def idle(t):
    L = 8.0
    br = 0.012 * math.sin(TAU * t / 4)
    k = br + 0.08 * bump(t, 4.7, 4.85, 4.9, 5.1) - 0.045 * bump(t, 5.05, 5.25, 5.3, 5.55)
    dmp = math.exp(-3.2 * max(0.0, t - 5.1)) * (t > 5.1)
    wob = 5.0 * math.sin(TAU * 2.6 * (t - 5.1)) * dmp
    o = gelee(t, lambda tt, th: wob * math.cos(th * 0.5) + 0.6 * math.sin(TAU * tt / 4 - th), 0)
    o[BER] = {"scale": squash(k), "pos": (0, 0.12 * bump(t, 5.1, 5.25, 5.3, 5.55), 0)}
    o[COEUR_G] = {"rot": (1.2 * math.sin(TAU * t / L) + 4 * wob / 5, 0, 1.5 * math.sin(TAU * t / L * 2 + 1) - 3 * wob / 5)}
    o[QUEUE] = {"rot": (0, 0, -6 * wob / 5 + 2 * math.sin(TAU * t / 4 + 0.6))}
    o[MENTHE] = {"rot": (2.5 * math.sin(TAU * t / 4 + 1.2), 0, 1.5 * math.sin(TAU * t / 8))}
    return o


def walk(t):
    L = 1.6
    st = math.sin(TAU * 2 * t / L)
    o = gelee(t, 3.0, 2 / L, ph=0.15)
    o[BER] = {"scale": squash(0.035 * st), "pos": (0, 0.08 * (1 - math.cos(TAU * 2 * t / L)) / 2, 0)}
    o[COEUR_G] = {"rot": (3 + 3.5 * math.sin(TAU * 2 * t / L - 1.0), 0, 2.5 * math.sin(TAU * t / L))}
    o[QUEUE] = {"rot": (0, 0, 6 * math.sin(TAU * 2 * t / L - 1.6))}
    o[MENTHE] = {"rot": (6 * math.sin(TAU * 2 * t / L - 1.3), 0, 0)}
    return o


def run(t):
    L = 1.0
    st = math.sin(TAU * 2 * t / L)
    o = gelee(t, 3.0, 2 / L, ph=0.12, lean=4.0)
    o[BER] = {"scale": squash(0.05 * st), "pos": (0, 0.12 * (1 - math.cos(TAU * 2 * t / L)) / 2, 0)}
    o[COEUR_G] = {"rot": (10 + 3 * math.sin(TAU * 4 * t / L), 0, 2 * math.sin(TAU * 2 * t / L))}
    o[QUEUE] = {"rot": (14 + 6 * math.sin(TAU * 4 * t / L + 0.5), 0, 4 * math.sin(TAU * 3 * t / L))}
    o[MENTHE] = {"rot": (16 + 8 * math.sin(TAU * 4 * t / L + 0.9), 0, 3 * math.sin(TAU * 3 * t / L))}
    return o


def sneak(t):
    L = 3.0
    o = gelee(t, 0.8, 1 / L)
    o[BER] = {"scale": squash(0.07 + 0.012 * math.sin(TAU * t / L))}
    o[COEUR_G] = {"rot": (-3 + 1.0 * math.sin(TAU * t / L), 0, 0)}
    o[MENTHE] = {"rot": (-6, 0, 0)}
    return o


def vent(L, lean, flut):
    def f(t):
        o = gelee(t, 1.5 * flut, 3 / L, lean=lean * 0.35)
        o[BER] = {"scale": squash(0.015 * math.sin(TAU * t / L))}
        o[COEUR_G] = {"rot": (lean + 2 * flut * math.sin(TAU * 3 * t / L), 0, 1.5 * math.sin(TAU * t / L))}
        o[QUEUE] = {"rot": (lean * 1.4 + 5 * flut * math.sin(TAU * 5 * t / L), 0, 3 * math.sin(TAU * 2 * t / L))}
        o[MENTHE] = {"rot": (lean * 1.6 + 8 * flut * math.sin(TAU * 5 * t / L + 0.7), 0, 3 * math.sin(TAU * 3 * t / L))}
        return o
    return f


def fall(t):
    L = 1.2
    o = gelee(t, 2.0, 2 / L)
    o[BER] = {"scale": squash(-0.04 + 0.01 * math.sin(TAU * t / L))}
    o[COEUR_G] = {"pos": (0, 0.18 + 0.05 * math.sin(TAU * t / L), 0), "rot": (-4, 0, 2 * math.sin(TAU * t / L))}
    o[MENTHE] = {"rot": (-10 + 4 * math.sin(TAU * 2 * t / L), 0, 0)}
    for g, _, _ in FRAISES:
        o[g]["pos"] = (0, 0.1 + 0.04 * math.sin(TAU * t / L), 0)
    return o


ANIMS = [anim("idle", 8.0, idle, fps=8), anim("walk", 1.6, walk), anim("run", 1.0, run, fps=12), anim("sneak", 3.0, sneak),
         anim("fly", 2.4, vent(2.4, 7, 1.0)), anim("glide", 3.6, vent(3.6, 14, 1.4)), anim("swim", 3.6, vent(3.6, 9, 0.8)),
         anim("fall", 1.2, fall)]

# event_equip (1,0 s) : la tartelette sort de rien, puis les fraises tombent une à une en tournant, la fraise du dessus en dernier
EQ = [(0.0, 0.0), (0.24, 1.25), (0.38, 0.9), (0.5, 1.03), (0.6, 1.0)]


def equip(t):
    # la galette s'étale d'abord à plat (y = 0), puis gonfle comme au four : le côté qui retombe ne traverse jamais la tête
    k = keys(t, EQ)
    ky = keys(t, [(0.0, 0.0), (0.16, 0.0), (0.28, 1.3), (0.4, 0.85), (0.52, 1.04), (0.62, 1.0)])
    o = {BER: {"scale": (k, ky, k)}}
    order = list(range(N_EXT)) + list(range(N_INT))
    for j, (g, th, tg) in enumerate(FRAISES):
        t0 = 0.3 + 0.026 * j
        vis = 1.0 if t >= t0 else 0.0
        drop = 3.0 * (1 - sm(t, t0, t0 + 0.12))
        sq = 0.25 * bump(t, t0 + 0.1, t0 + 0.13, t0 + 0.15, t0 + 0.24)
        o[g] = {"scale": (vis * (1 + 0.45 * sq), vis * (1 - sq), vis * (1 + 0.45 * sq)), "pos": (0, drop, 0)}
    t0 = 0.72
    vis = 1.0 if t >= t0 else 0.0
    sq = 0.3 * bump(t, t0 + 0.1, t0 + 0.13, t0 + 0.15, t0 + 0.26)
    o[COEUR_G] = {"scale": (vis * (1 + 0.45 * sq), vis * (1 - sq), vis * (1 + 0.45 * sq)), "pos": (0, 3.5 * (1 - sm(t, t0, t0 + 0.12)), 0)}
    kq = keys(t, [(0.0, 0.0), (0.84, 0.0), (0.92, 1.3), (1.0, 1.0)])
    o[QUEUE] = {"scale": (kq, kq, kq)}
    km = keys(t, [(0.0, 0.0), (0.78, 0.0), (0.9, 1.15), (1.0, 1.0)])
    o[MENTHE] = {"scale": (km, km, km)}
    return o


def unequip(t):
    k = keys(t, [(0.0, 1.0), (0.2, 1.08), (0.5, 0.0)])
    ky = keys(t, [(0.0, 1.0), (0.12, 0.8), (0.32, 0.0)])       # se dégonfle d'abord, puis rétrécit
    sq = squash(0.1 * bump(t, 0.0, 0.1, 0.12, 0.25))
    o = {BER: {"scale": (k * sq[0], ky * sq[1], k * sq[2])}}
    kf_ = keys(t, [(0.0, 1.0), (0.12, 1.0), (0.38, 0.0)])
    for g, th, tg in FRAISES + [(COEUR_G, 0, None), (MENTHE, 0, None)]:
        o[g] = {"pos": (0, 2.2 * sm(t, 0.0, 0.3), 0), "scale": (kf_, kf_, kf_)}
    return o


eq = anim("event_equip", 1.0, equip, loop="once", fps=30)
eq["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "block.honey_block.place", "file": ""}], "time": 0.22}]}
ANIMS += [eq, anim("event_unequip", 0.6, unequip, loop="once", fps=30)]

# ------------------------------------------------------------------ contrôle : rien du béret ne descend sur la tête (seconde couche
# comprise) dans aucune pose ; les événements sont combinés à l'étirement le plus fort des états (les échelles se multiplient)
PTS = np.array(GROUP_ELS[BER])
min_xz = min(fn(t)[BER].get("scale", (1, 1, 1))[0] for L, fn, lp in POSES.values() if lp == "loop" for t in np.linspace(0, L, 41))


def pire(scale, pos=(0, 0, 0)):
    P = PIV + (PTS - PIV) * np.asarray(scale) + np.asarray(pos)
    above = (np.abs(P[:, 0]) < HALF) & (np.abs(P[:, 2]) < HALF)
    return P[above, 1].min() if above.any() else 99.0


worst = 99.0
for name, (L, fn, lp) in POSES.items():
    for t in np.linspace(0, L, 61):
        sc = np.array(fn(t)[BER].get("scale", (1, 1, 1)), float)
        if lp == "once":
            sc = sc * np.array([min_xz, 1.0, min_xz])
        if sc[1] <= 0 or sc[0] <= 0:
            continue
        worst = min(worst, pire(sc, fn(t)[BER].get("pos", (0, 0, 0))))
assert worst >= 32.62, f"le béret entre dans la tête : y min {worst:.2f}"
assert max(max(abs(p[0]), abs(p[2])) for p in PTS) < 128

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
sys.path.insert(0, os.path.join("..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      f"y min au-dessus de la tête {worst:.2f} ; étirement mini {min_xz:.3f} ; bas du béret {PTS[:, 1].min():.2f}")
