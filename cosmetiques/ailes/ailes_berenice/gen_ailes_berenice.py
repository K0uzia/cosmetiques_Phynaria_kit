"""Ailes de Bérénice (ex-« Aurelion ») — ensemble Bérénice, thème Divin : plumes ivoire à pointe dorée, halo d'or. Design original.
Fiche de style : .claude/styles/berenice.md. Écrit ailes_berenice.png, ailes_berenice_e.png et .build/ailes_berenice_brut.bbmodel.

Validé en jeu, à ne pas toucher : forme et rondeur des plumes (peau + âme), plume-particule qui tombe, palette ivoire/or,
battement à la fusée en glide (V0 = 26, DV = 5, piqués exclus).

Mise aux règles du 2026-11-04 :
- taille : l'aile est réduite dans son plan (K = 0,62 autour de l'épaule, petite paire 0,66 autour de sa racine), profondeur gardée :
  envergure déployée 59–69 px (fly, glide, étirement), repliée au repos pointes au niveau des mollets (y ≈ 4), extension < 60 px ;
- couches : deux plumes voisines d'une rangée jamais au même niveau (ALT), rangées écartées (MG), plus de roulis ; contrôle par
  .build/mesure.py (paires de faces parallèles à moins de 0,1 px qui se recouvrent) ;
- event_equip (1,8 s, son embarqué souffle_plumes : souffle et froissement de plumes, tintement en mi) et event_unequip (2,2 s, finit à l'échelle 0) : pas de sac, les ailes sortent du dos ;
- overlay_halo : tour et flottement du halo en couche permanente (il ne saute plus entre deux états) ;
- calque _e : sources nettes (pointes des primaires, filets d'or, rachis), fond très sombre ; pas de reflets _r (bug du mod).
Fonctions avancées : particle_plume + emit_plume (plumes qui tombent), calque _e, overlay_, event_equip, event_unequip, son embarqué (phynaria_sounds, sons/souffle_plumes.py).
À juger en jeu seulement (/cosmetique apercu) : apparition et retrait (somme avec l'état, sens de la position z), calque _e de nuit
(avec shader : invisible à ce jour, bug du mod), particules.

Plume hybride : une PEAU (plaque fine dont le contour rond vient de l'alpha 0/255, tranches transparentes) et une ÂME
(cubes pleins opaques, plus étroits que le contour donc invisibles de face, qui remplissent l'épaisseur).
De face et de dos on lit le contour rond ; par la tranche, un profil plein et effilé.
Texture : image de plume = base en HAUT, pointe en BAS, côté extérieur de l'aile à DROITE (u croissant).
Rangées, du dos vers l'avant : scapulaires et petites couvertures dorées, moyennes liserées d'or,
grandes ivoire, rémiges (secondaires chaudes, primaires à pointe dorée), sous-alaires froides.
Petite paire basse : éventail champagne.
"""
import base64, io, json, math, os, re, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

TEX = 512
V0, DV = 26, 5      # battement à la fusée (glide) : vitesse de déclenchement et plage, en blocs/s, à régler en jeu
SS = 4
tex = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))


# ------------------------------------------------------------------ textures
def lerp(a, b, k):
    return a + (b - a) * k


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


PAL = {
    # racine, milieu, bout, liseré, ombre, couleur de pointe
    "p": ((222, 216, 202), (252, 250, 243), (254, 251, 240), (176, 150, 104), (150, 138, 116), (238, 200, 116)),
    "s": ((212, 204, 186), (244, 238, 224), (250, 244, 228), (166, 142, 104), (140, 128, 106), (232, 200, 130)),
    "f": ((184, 162, 124), (232, 214, 176), (244, 226, 180), (140, 112, 72), (120, 102, 76), (240, 206, 128)),
    "g": ((226, 222, 210), (255, 254, 250), (255, 254, 250), (196, 170, 118), (160, 150, 130), (246, 228, 176)),
    "m": ((234, 226, 204), (253, 249, 236), (253, 244, 214), (194, 160, 100), (170, 150, 116), (244, 218, 150)),
    "l": ((240, 212, 148), (250, 232, 180), (254, 242, 204), (186, 148, 84), (176, 146, 96), (255, 244, 208)),
    "u": ((204, 204, 204), (240, 240, 238), (248, 248, 244), (150, 148, 144), (146, 146, 146), (240, 234, 216)),
}
SHAPE = {
    # demi-largeur intérieure, extérieure, début de l'arrondi, courbure, début de pointe colorée, longueur d'ombre
    "p": (0.42, 0.31, 0.62, 0.14, 0.74, 0.42),
    "s": (0.43, 0.33, 0.68, 0.08, 0.88, 0.45),
    "f": (0.42, 0.32, 0.68, 0.12, 0.74, 0.40),
    "g": (0.45, 0.38, 0.58, 0.05, 0.92, 0.36),
    "m": (0.45, 0.40, 0.52, 0.04, 0.84, 0.34),
    "l": (0.46, 0.42, 0.44, 0.03, 0.86, 0.16),
    "u": (0.45, 0.39, 0.56, 0.05, 0.93, 0.34),
}


def paint(W, H, kind, seed):
    rng = np.random.default_rng(seed)
    root, mid, tip, rim, shadow, gold = (np.array(c, np.float32) for c in PAL[kind])
    hi, ho, te, curve, g0, shl = SHAPE[kind]
    te += rng.uniform(-0.03, 0.03)
    jitter = rng.uniform(0.97, 1.02)
    w, h = W * SS, H * SS
    x, y = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    t = y                                                     # 0 = base, 1 = pointe
    cx = 0.5 + curve * (t * t - 0.3)
    env = (0.28 + 0.72 * smooth(t / 0.20)) * np.where(t > te, np.sqrt(np.clip(1 - ((t - te) / (1 - te)) ** 2, 0, 1)), 1.0)
    d = x - cx
    inner = hi * env
    lim = np.where(d >= 0, ho * env, inner)
    r = np.abs(d) / np.maximum(lim, 1e-4)
    alpha = (r < 1) * 255.0

    k1 = smooth(t / 0.5)[..., None]
    k2 = smooth((t - 0.5) / 0.5)[..., None]
    col = lerp(lerp(root, mid, k1), tip, k2) * jitter
    # relief de vanne : plus clair près du rachis, plus sombre au bord
    col = col * (1.04 - 0.17 * (r ** 2))[..., None]
    # barbes obliques, période lisible (~6 texels)
    bx = np.abs(d) * W
    barbs = np.sin((t * H - bx * 1.4) * math.tau / 6.0)
    col = col * (1 + 0.035 * barbs * (r > 0.1))[..., None]
    # pointe colorée
    gk = smooth((t - g0) / max(1e-3, 1 - g0))[..., None]
    col = lerp(col, gold, gk * 0.85)
    # ombre de recouvrement peinte à la base + ombre du bord intérieur (recouvert par la voisine)
    shd = (np.clip(1 - t / shl, 0, 1) ** 1.25)[..., None]
    col = lerp(col, shadow, shd * 0.72)
    side = (np.clip((r - 0.45) / 0.55, 0, 1) * (d < 0))[..., None]
    col = col * (1 - 0.20 * side)
    # liseré d'au moins 3–4 texels
    dist = (1 - r) * lim * W
    rk = (np.clip(1 - dist / 3.5, 0, 1) * (t > 0.12))[..., None]
    col = lerp(col, rim, rk * 0.72)
    # rachis
    if kind in "psfg":
        ra = (np.clip(1 - np.abs(d) * W / 1.5, 0, 1) * (t < 0.93))[..., None]
        col = lerp(col, np.array((255, 248, 226), np.float32), ra * 0.75)
        rb = (np.clip(1 - np.abs(d * W + 2.0) / 1.2, 0, 1) * (t < 0.93) * (t > 0.2))[..., None]
        col = col * (1 - 0.18 * rb)

    # calque lumineux (2026-11-04, retour « je ne vois aucune lumière ») : fond additif très sombre, et des sources nettes, vives
    # (150 à 225) sur de petites surfaces : pointes dorées des primaires (point focal), filets d'or des moyennes couvertures,
    # rachis fins des rémiges. Le reste ne fait qu'une lueur douce.
    global PAINT_E
    ec = np.empty(col.shape, np.float32)
    ec[...] = np.array((22, 19, 12) if kind == "l" else (20, 19, 16), np.float32)
    pointe = {"p": (218, 182, 100), "s": (150, 124, 70), "f": (150, 124, 70)}.get(kind, (96, 80, 46))
    ec = lerp(ec, np.array(pointe, np.float32), gk)
    thin = (np.clip(1 - dist / 2.2, 0, 1) * (t > 0.12))[..., None]
    ec = lerp(ec, np.array((168, 142, 84) if kind == "m" else (64, 58, 44), np.float32), thin)
    if kind in "psfg":
        ra = np.array((156, 148, 122) if kind in "ps" else (96, 92, 78), np.float32)
        ec = lerp(ec, ra, np.clip(1 - np.abs(d) * W / 1.5, 0, 1)[..., None] * (t < 0.93)[..., None])
    PAINT_E = (np.array(Image.fromarray(np.clip(ec, 0, 225).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)), None)
    rgb = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    a = Image.fromarray(alpha.astype(np.uint8), "L").resize((W, H), Image.LANCZOS)
    arr_rgb, arr_a = np.array(rgb), np.array(a)
    solid = arr_a > 128
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = arr_rgb
    if solid.any():
        arr[~solid, :3] = arr_rgb[solid].mean(axis=0).astype(np.uint8)   # pas de frange sombre, PNG compact
    arr[..., 3] = solid * 255
    return Image.fromarray(arr, "RGBA")


def edge_strip(kind, W=6, H=32):
    """Bande opaque des tranches : suit le dégradé de la plume (t=0 en haut), assombrie pour dessiner le bord."""
    root, mid, tip, rim, shadow, gold = (np.array(c, np.float32) for c in PAL[kind])
    g0 = SHAPE[kind][4]
    a = np.zeros((H, W, 4), np.float32)
    for yy in range(H):
        t = (yy + 0.5) / H
        c = lerp(root, mid, min(1, t * 2)) if t < 0.5 else lerp(mid, tip, (t - 0.5) * 2)
        c = lerp(c, gold, float(smooth((t - g0) / max(1e-3, 1 - g0))) * 0.85)
        a[yy, :, :3] = lerp(c, rim, 0.38)
    a[..., 3] = 255
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def solid_tile(W, H, base, line, dark):
    """Tuile opaque de matière (os, or) : dégradé vertical et filet central de 4 texels."""
    a = np.zeros((H, W, 4), np.float32)
    base, line, dark = (np.array(c, np.float32) for c in (base, line, dark))
    for yy in range(H):
        a[yy, :, :3] = lerp(line, dark, yy / max(1, H - 1)) * 0.45 + base * 0.55
    c = H // 2
    a[c - 2:c + 2, :, :3] = line
    a[..., 3] = 255
    return Image.fromarray(a.astype(np.uint8), "RGBA")


UV = {}
cx_, cy_, shelf = 0, 0, 0


def place(name, img):
    global cx_, cy_, shelf
    w, h = img.size
    if cx_ + w > TEX:
        cx_, cy_, shelf = 0, cy_ + shelf, 0
    assert cy_ + h <= TEX, "atlas plein"
    tex.paste(img, (cx_, cy_))
    UV[name] = (cx_, cy_, cx_ + w, cy_ + h)
    cx_ += w
    shelf = max(shelf, h)


seed = 1
EIMG = {}
for kind, n, W, H in (("p", 5, 52, 208), ("s", 4, 52, 150), ("f", 3, 48, 160), ("g", 4, 52, 104), ("m", 3, 44, 72),
                      ("u", 3, 48, 90), ("l", 4, 40, 48)):
    for i in range(n):
        name = f"{kind}{i}"
        im = paint(W, H, kind, seed)
        place(name, im)
        ea, emask = PAINT_E
        mask = np.array(im)[..., 3] > 0
        EIMG[name] = (ea, mask & emask if emask is not None else mask)
        seed += 1

# Halo : une seule plaque, anneau parfait par l'alpha, tuile dédiée 128×128. Le reste de la tuile garde la couleur or, pas de frange sombre.
HT, HALF = 128, 7.25            # taille de la tuile (texels), demi-côté de la plaque (px)
RH, RW = 6.4, 0.55              # rayon, demi-largeur de l'anneau (px)
yy_, xx_ = np.mgrid[0:HT, 0:HT]
rr_ = np.hypot(xx_ + 0.5 - HT / 2, yy_ + 0.5 - HT / 2) * HALF / (HT / 2)
_h = np.zeros((HT, HT, 4), np.uint8)
_h[..., :3] = (240, 202, 110)
_h[..., 3] = (np.abs(rr_ - RH) <= RW) * 255
place("halo", Image.fromarray(_h, "RGBA"))
for kind in PAL:
    place(f"edge_{kind}", edge_strip(kind))
place("bone", solid_tile(32, 32, (240, 234, 216), (250, 246, 234), (190, 176, 150)))

# Plume-particule : image dédiée, une seule silhouette continue, fine et effilée, avec hampe nue à la base.
PLW, PLH = 40, 160
_y, _x = np.mgrid[0:PLH * SS, 0:PLW * SS]
_t_ = (_y + 0.5) / (PLH * SS)
_d = (_x + 0.5) / (PLW * SS) - 0.5
_c = 0.13 * (np.sin(_t_ * math.pi) - 0.5)              # la courbure de la plume vient de l'image : hampe et contour en arc
_v = np.clip((_t_ - 0.10) / 0.90, 0, 1)
_env = 0.34 * np.sin(math.pi * _v ** 0.85) ** 0.42      # s'ouvre vite, s'effile longuement vers la pointe
_dd = np.abs(_d - _c)
_a = (_dd < np.maximum(_env, 0.018 * (_t_ < 0.97)))
_col = np.empty(_a.shape + (3,), np.float32)
_col[...] = (248, 245, 234)
_col = _col * (1.0 - 0.14 * (_dd / np.maximum(_env, 0.02))[..., None] ** 2)
_col = _col * (1 + 0.03 * np.sin((_t_ * PLH - _dd * PLW * 1.4) * math.tau / 7))[..., None]
_col = lerp(_col, np.array((236, 202, 124), np.float32), smooth((_t_ - 0.78) / 0.22)[..., None] * 0.8)
_col = lerp(_col, np.array((205, 192, 165), np.float32), (_dd < 0.02)[..., None] * 0.8)
_pi = Image.fromarray(np.clip(_col, 0, 255).astype(np.uint8), "RGB").resize((PLW, PLH), Image.LANCZOS)
_pm = np.array(Image.fromarray(_a.astype(np.uint8) * 255, "L").resize((PLW, PLH), Image.LANCZOS)) > 110
_pa = np.dstack([np.array(_pi), _pm * 255]).astype(np.uint8)
tex.paste(Image.fromarray(_pa, "RGBA"), (468, 0))       # place libre à droite de la première rangée
assert 468 >= max(v[2] for v in UV.values() if v[3] <= 208 and v[1] < 160)
UV["plume"] = (468, 0, 468 + PLW, PLH)
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex.getpixel((TEX - 3, TEX - 3))[3] == 0
_t = np.array(tex)
_t[..., :3] &= 0xFC          # postérisation invisible à l'oeil : PNG nettement plus léger
assert set(np.unique(_t[..., 3])) <= {0, 255}, "semi-transparence"
tex = Image.fromarray(_t, "RGBA")
tex.save("ailes_berenice.png")
_b = io.BytesIO()
tex.save(_b, "PNG", optimize=True)
tex_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()

# Calque lumineux (guide, section 5 bis) : jamais assigné aux faces, additif. Halo : cœur plus étroit que l'anneau, bord or.
# Plumes : même agencement que la texture, 225 au plus ; plume-particule : rien.
_e = np.zeros((TEX, TEX, 4), np.uint8)
for name, (ea, mask) in EIMG.items():
    u0, v0, u1, v1 = UV[name]
    _e[v0:v1, u0:u1, :3] = ea
    _e[v0:v1, u0:u1, 3] = mask * 255
for kind in PAL:
    u0, v0, u1, v1 = UV[f"edge_{kind}"]
    _e[v0:v1, u0:u1] = (16, 15, 13, 255)
u0, v0, u1, v1 = UV["bone"]
_e[v0:v1, u0:u1] = (16, 15, 13, 255)
assert _e[..., :3].max() <= 225, "calque trop vif"
u0, v0, u1, v1 = UV["halo"]
_e[v0:v1, u0:u1, :3] = (225, 200, 118)      # cœur du halo : source nette, 225 au plus
_e[v0:v1, u0:u1, 3] = (np.abs(rr_ - RH) <= RW * 0.55) * 255
assert set(np.unique(_e[..., 3])) <= {0, 255}
tex_e = Image.fromarray(_e, "RGBA")
tex_e.save("ailes_berenice_e.png", optimize=True)
_b = io.BytesIO()
tex_e.save(_b, "PNG", optimize=True)
tex_e_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()

# ------------------------------------------------------------------ géométrie
ALL = ("north", "south", "east", "west", "up", "down")


def nuid():
    return str(_uuid.uuid4())


elements, groups = [], {}


def cube(name, frm, to, origin, rot=(0, 0, 0), faces=None):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(v, 2) for v in frm], "to": [round(v, 2) for v in to],
         "origin": [round(v, 2) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(v, 1) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(rot):
        e["rotation"] = [round(v, 1) for v in rot]
    elements.append(e)
    return e["uuid"]


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups
    groups[name] = {"origin": [round(v, 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(v, 2) for v in rotation]}
    return name


K = 0.62         # réduction de la grande aile dans son plan (section « taille ») : envergure déployée ≈ 52–70 px
KL = 0.66        # petite paire, autour de sa propre racine
Z = 5.5          # plan médian de l'aile (dos du joueur à z = 2) ; reculé de 1 px (2026-11-04) : les rangées du dessous, décalées en couches, restent hors du torse
# Couches (retour en jeu « texture qui clipe entre les plumes », recette des lames empilées) : deux plumes voisines d'une même rangée
# ne sont jamais au même niveau. Une sur deux est décalée en profondeur (+ vers le dos, − vers la face), d'assez pour que leurs faces
# et celles de leurs âmes restent à 0,1 px au moins (mesuré par .build/mesure.py). Remplace l'ancien roulis de 4°, dont les tuiles se
# croisaient dès que deux voisines n'avaient pas la même inclinaison.
ALT = {"p": [0.3, 3], "s": 0.35, "t": 0.35, "lf": [0.45, 4],
       "gc": 0.45, "mc": 0.45, "lc": 0.5, "rd": [0, 0.6, 0, 0.9, 0, 0.6, 0, 0.6, 0, 0.6, 0, 0.6, 0], "sc": 0.6, "lc_": 0.6,
       "uc": -0.45, "um": -0.45, "ua": -0.45, "bk": -0.45,
       "rv": [0, -0.7, 0, -0.7, 0, -0.7, -0.25, -0.95, -0.25, -0.95, -0.25, -0.95, -0.25]}   # crête du dessous, très pentue : réglée plume à plume
ROLL = 0.0       # roulis autour du rachis (abandonné : voir ALT)


def alt(fam, k):
    """Décalage en profondeur de la plume k d'une famille : ALT[fam] = δ (une plume sur deux) ou [δ, période]."""
    v = ALT.get(fam, 0)
    if isinstance(v, list) and len(v) > 3:      # liste explicite, une valeur par plume
        return v[k % len(v)]
    d, per, ph = (v, 2, 0) if not isinstance(v, list) else (list(v) + [0])[:3]
    return d * ((k + ph) % per)       # roulis autour du rachis : chaque plume passe sur sa voisine extérieure (tuiles, pas de faces coplanaires)
SKIN = 0.3       # épaisseur d'une peau
EMBED = 0.12     # l'âme entre d'autant dans la peau : ni vide, ni face coplanaire


def stack(z0, z1, t0, t1):
    """Rangée : centre de z0 à z1 (rel. au plan), épaisseur totale de t0 à t1, le long de la plume.
    Les valeurs de STACK font reposer chaque rangée sur la précédente : rien de vide en profondeur."""
    return (lambda a, L: lerp(z0, z1, a / L)), (lambda a, L: lerp(t0, t1, a / L))


def remex(bend):
    """Rémige : base épaisse, centrée sur le plan ; le bout se penche côté face."""
    return stack(0.6, -bend, 1.3, 0.64)


MG = [0.3, 0.5, 0.6, 0.8, 0.35, 0.5, 0.9]   # écart ajouté entre rangées, à cause des décalages de ALT : g, m, l, sc (dos) ; u, um, ua (face)
STACK = {"g": stack(1.70 + MG[0], 1.10 + MG[0], 1.0, 0.62), "m": stack(2.65 + MG[1], 1.89 + MG[1], 0.9, 0.62), "l": stack(3.50 + MG[2], 2.69 + MG[2], 0.8, 0.62),
         "u": stack(-0.50 - MG[4], -0.36 - MG[4], 1.0, 0.62), "um": stack(-1.45 - MG[5], -1.03 - MG[5], 0.9, 0.62), "sc": stack(4.40 + MG[3], 3.60 + MG[3], 0.8, 0.62),
         "lf": stack(0.50, 0.00, 1.1, 0.64), "lc": stack(1.50, 0.80, 0.8, 0.62),
         # crête : écailles sans âme, en toit sur le noyau, du sommet vers le dos ou vers la face
         "rd": stack(1.35, 3.05, 0.62, 0.62), "rv": stack(1.05, -1.75, 0.62, 0.62), "bk": stack(1.5, -2.0, 0.62, 0.62)}


def feather(name, s, ax, ay, L, w, tilt, uv, parent, prof, side="both", ncore=2, own_bone=False, zb=None, dz=0.0, roll=None):
    """Plume hybride : base en haut, tilt > 0 = la pointe part vers l'extérieur.
    side : "both" = deux peaux (rémiges), "d" = peau du dessus seule, "v" = peau du dessous seule (couvertures posées sur la rangée voisine).
    prof = (centre(a, L), épaisseur totale(a, L)) relatifs au plan zb."""
    kind = re.match(r"[a-z]+", uv).group()
    zc, thick = prof
    zb = (Z if zb is None else zb) + dz
    roll = ROLL if roll is None else roll
    bx = s * ax
    tgt = group(name, [bx, ay, zb + zc(0, L)], parent=parent) if own_bone else parent
    u0, v0, u1, v1 = UV[uv]
    south = [u0, v0, u1, v1] if s > 0 else [u1, v0, u0, v1]
    north = [south[2], v0, south[0], v1]
    rz = s * tilt
    sn, cs = math.sin(math.radians(tilt)), math.cos(math.radians(tilt))
    zd = lambda a: zb + zc(a, L) + thick(a, L) / 2      # surface extérieure, côté dos
    zv = lambda a: zb + zc(a, L) - thick(a, L) / 2      # surface extérieure, côté face

    def skin(tag, z0, z1, faces_s, faces_n, inward):
        """inward = -1 : la plaque s'étend vers -z depuis sa surface ; +1 : vers +z."""
        pitch = math.degrees(math.atan2(z0 - z1, L))
        a, b = sorted((z0, z0 + inward * SKIN))
        faces = {"south": faces_s, "north": faces_n, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
        groups[tgt]["ids"].append(cube(f"{name}.{tag}", [bx - w / 2, ay - L, a], [bx + w / 2, ay + 0.6, b], [bx, ay, z0],
                                       rot=(pitch, -s * roll, rz), faces=faces))

    if side in ("both", "d"):
        skin("d", zd(0), zd(L), south, CLEAR if side == "both" else north, -1)
    if side in ("both", "v"):
        skin("v", zv(0), zv(L), CLEAR if side == "both" else south, north, +1)

    # âme : hampe épaisse qui s'effile, plus étroite que le contour
    e0, e1, e2, e3 = UV[f"edge_{kind}"]
    t_start, t_end = (0.16, 0.84) if not dz else (0.22, 0.79)   # bouts d'âme de deux voisines jamais au même endroit
    for j in range(ncore):
        cut = lambda jj: lerp(t_start, t_end, jj / ncore) + (0.06 if dz and 0 < jj < ncore else 0.0)
        t0, t1 = cut(j), cut(j + 1)
        a0, a1 = t0 * L, t1 * L
        k = 1 - 0.55 * (j + 0.5) / ncore
        wc = w * 0.50 * k
        if side == "both":
            top, bot = zd(a1) - SKIN + EMBED, zv(a1) + SKIN - EMBED    # côté mince : l'âme ne perce jamais la peau
        elif side == "d":
            top = zd(a1) - SKIN + EMBED
            bot = top - max(0.45, thick(a1, L))
        else:
            bot = zv(a1) + SKIN - EMBED
            top = bot + max(0.45, thick(a1, L))
        zm = (top + bot) / 2
        x, y = bx + s * sn * a0, ay - cs * a0
        if side == "both":
            pitch = math.degrees(math.atan2(zc(a0, L) - zc(a1, L), a1 - a0))
        else:
            sf = zd if side == "d" else zv
            pitch = math.degrees(math.atan2(sf(a0) - sf(a1), a1 - a0))
        z = zm + math.tan(math.radians(pitch)) * (a1 - a0)            # zm vaut au côté mince : on remonte au pivot
        ea, eb = lerp(e1, e3, t0), lerp(e1, e3, t1)
        faces = {"south": [e0, ea, e2, eb], "north": [e0, ea, e2, eb], "east": [e0, ea, e2, eb], "west": [e0, ea, e2, eb],
                 "up": [e0, ea, e2, min(e3, ea + 1)], "down": [e0, max(e1, eb - 1), e2, eb]}
        ov = 0.15 if j else 0.0
        groups[tgt]["ids"].append(cube(f"{name}.c{j}", [x - wc / 2, y - (a1 - a0), z - (top - bot) / 2], [x + wc / 2, y + ov, z + (top - bot) / 2],
                                       [x, y, z], rot=(pitch, -s * roll, rz), faces=faces))
    return bx + s * sn * L, ay - cs * L, zb + zc(L, L)


ARM = [(3.0, 23.0), (10.0, 31.0), (20.0, 35.5), (29.0, 36.0)]
YAW = [22, -8, 8]     # balayage arrière au repos (humérus arrière, avant-bras revient, main repart)
SEG = ["shoulder", "elbow", "wrist"]


def pos(i, f):
    return lerp(ARM[i][0], ARM[i + 1][0], f), lerp(ARM[i][1], ARM[i + 1][1], f)


def bell(x, c, w):
    return math.exp(-((x - c) / w) ** 2)


def tilt_at(i, f):
    """Inclinaison des plumes le long du bras : verticale près du corps, éventail sur la main."""
    if i == 0:
        return 0 + 3 * f
    if i == 1:
        return 3 + 14 * f
    return 18 + 44 * f ** 1.1


EMITS = []


def emit(parent, at):
    """Point de départ de plume (guide, section 5 ter) : groupe vide, pivot = endroit exact, suit le groupe qui le porte."""
    EMITS.append(group("emit_plume" + (str(len(EMITS) + 1) if EMITS else ""), at, parent=parent))


CORE_R = [(1.95, 1.65), (1.65, 1.25), (1.25, 0.8)]   # rayon du noyau au début et à la fin de chaque segment
CORE_Z = 1.2                                         # centre du noyau par rapport au plan : noyau côté dos, sous les couvertures


def core_radius(i, f):
    return lerp(CORE_R[i][0], CORE_R[i][1], f)


def chaikin(pts, n=3):
    for _ in range(n):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(lerp(a[0], b[0], .25), lerp(a[1], b[1], .25)), (lerp(a[0], b[0], .75), lerp(a[1], b[1], .75))]
        out.append(pts[-1])
        pts = out
    return pts


# Arête d'attaque : arche continue, sans coin. Ajoute un départ bas près de la colonne pour adoucir l'épaule.
SMOOTH = chaikin(ARM)
_ls = [0.0]
for a_, b_ in zip(SMOOTH, SMOOTH[1:]):
    _ls.append(_ls[-1] + math.dist(a_, b_))


def arch(u):
    d = u * _ls[-1]
    for n in range(len(SMOOTH) - 1):
        if d <= _ls[n + 1]:
            return (lerp(SMOOTH[n][0], SMOOTH[n + 1][0], (d - _ls[n]) / max(1e-6, _ls[n + 1] - _ls[n])),
                    lerp(SMOOTH[n][1], SMOOTH[n + 1][1], (d - _ls[n]) / max(1e-6, _ls[n + 1] - _ls[n])))
    return SMOOTH[-1]


def build(s):
    tag = "l" if s < 0 else "r"
    segs = []
    for i in range(3):
        segs.append(group(f"{SEG[i]}_{tag}", [s * ARM[i][0], ARM[i][1], Z], parent=segs[i - 1] if i else None,
                          rotation=(0, -s * YAW[i], 0)))
    # noyau osseux et musculaire : section octogonale (deux cubes à 45°), s'affine vers la main ; sous les couvertures
    bone_faces = {k: list(UV["bone"]) for k in ALL}
    zb = Z + CORE_Z
    for i in range(3):
        (x0, y0), (x1, y1) = ARM[i], ARM[i + 1]
        L = math.dist(ARM[i], ARM[i + 1])
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        a, b = sorted([s * (x0 - 0.5), s * (x0 + L + 0.3)])
        r = (CORE_R[i][0] + CORE_R[i][1]) / 2
        q = r * 0.56
        groups[segs[i]]["ids"].append(cube(f"arm{i}_{tag}", [a, y0 - q, zb - q], [b, y0 + q, zb + q],
                                           [s * x0, y0, zb], rot=(0, 0, s * ang), faces=bone_faces))
        groups[segs[i]]["ids"].append(cube(f"arm{i}b_{tag}", [a + 0.18, y0 - q * 0.97, zb - q * 0.97], [b - 0.18, y0 + q * 0.97, zb + q * 0.97],
                                           [s * x0, y0, zb], rot=(45, 0, s * ang), faces=bone_faces))
    # masse de l'épaule, contre le dos ; groupe fixe : elle ne sort pas sur le côté du torse quand l'aile se replie
    gold_faces = {k: list(UV["bone"]) for k in ALL}
    a, b = sorted([s * 0.9, s * 3.4])
    wr = group(f"wingroot_{tag}", [s * 3.0, 23.0, Z])
    groups[wr]["ids"].append(cube(f"root_{tag}", [a, 21.4, 2.15], [b, 24.6, Z + 1.2], [s * 3.0, 23.0, Z], faces=gold_faces))

    # primaires (main) : 8, os propres, longues et effilées, éventail
    NP = 8
    for k in range(NP):
        f = (k + 0.5) / NP
        ax, ay = pos(2, f)
        L = 24.0 + 6.5 * bell(f, 0.45, 0.45) - 4.0 * max(0.0, (f - 0.7) / 0.3) + (0.8 if k % 2 else 0)
        tip = feather(f"p{k}_{tag}", s, ax, ay - 0.4, L, 6.0 - 0.8 * f, tilt_at(2, f), f"p{k % 5}", segs[2], remex(1.1), ncore=3, own_bone=True, dz=alt("p", k))
        if k in (2, 4, 6):
            emit(f"p{k}_{tag}", tip)
    # secondaires (avant-bras) : 6, os propres, bord de fuite en vagues
    NS = 6
    for k in range(NS):
        f = (k + 0.5) / NS
        ax, ay = pos(1, f)
        L = 15.5 + 3.0 * f + (1.4 if k % 2 else 0)
        tip = feather(f"s{k}_{tag}", s, ax, ay - 0.4, L, 5.4, tilt_at(1, f), f"s{k % 4}", segs[1], remex(0.5), ncore=2, own_bone=True, dz=alt("s", k))
        if k in (1, 4):
            emit(f"s{k}_{tag}", tip)
    # tertiaires (humérus) : 3
    for k in range(3):
        f = (k + 0.6) / 3
        ax, ay = pos(0, f)
        feather(f"t{k}_{tag}", s, ax, ay - 0.4, 10.0 + 1.6 * k, 5.4, tilt_at(0, f), f"s{(k + 1) % 4}", segs[0], remex(0.3), ncore=1, dz=alt("t", k + 1))

    def row(prefix, n, L0, L1, w, lift, prof, kind, nv, side, phase=0.0, span=(0.03, 0.97), tilt_k=0.9, ncore=1):
        """Rangée d'écailles qui suit l'arche lissée ; longueurs variées ; cubes directs du segment porteur."""
        lens = [math.dist(ARM[i], ARM[i + 1]) for i in range(3)]
        tot = sum(lens)
        for k in range(n):
            u = lerp(span[0], span[1], (k + 0.5) / n)
            dd = u * tot
            i = 0
            while i < 2 and dd > lens[i]:
                dd -= lens[i]
                i += 1
            f = min(1.0, dd / lens[i])
            ax, ay = arch(u)
            vary = 1 + 0.07 * math.sin(k * 2.4 + phase)
            feather(f"{prefix}{k}_{tag}", s, ax, ay + lift(i, f), lerp(L0, L1, u) * vary, w, tilt_at(i, f) * tilt_k, f"{kind}{k % nv}", segs[i], prof, side=side, ncore=ncore, dz=alt(prefix, k))

    # côté dos : grandes (ivoire vive), moyennes (liseré d'or), petites (écailles d'or)
    row("gc", 11, 9.0, 11.0, 5.2, lambda i, f: -0.2, STACK["g"], "g", 4, "d", 0.0)
    row("mc", 11, 6.2, 6.8, 4.6, lambda i, f: 0.5, STACK["m"], "m", 3, "d", 1.3)
    row("lc", 13, 4.4, 4.0, 3.9, lambda i, f: core_radius(i, f) + 0.5, STACK["l"], "l", 4, "d", 2.6, tilt_k=0.6, ncore=0)
    # côté face : sous-alaires claires et froides, deux rangées
    row("uc", 10, 8.5, 10.0, 5.2, lambda i, f: -0.1, STACK["u"], "u", 3, "v", 0.7)
    row("um", 11, 4.8, 4.8, 4.2, lambda i, f: core_radius(i, f) * 0.95, STACK["um"], "m", 3, "v", 2.0, ncore=0)
    row("ua", 12, 3.6, 3.2, 3.4, lambda i, f: core_radius(i, f) + 0.5, stack(-2.05 - MG[6], -1.6 - MG[6], 0.75, 0.62), "l", 4, "v", 3.4, tilt_k=0.6, ncore=0)
    # crête du bord d'attaque : le noyau n'est plus visible de dessus, ni replié
    ridge = lambda i, f: core_radius(i, f) * 0.56 + 0.75
    row("rd", 13, 3.6, 3.1, 3.7, ridge, STACK["rd"], "l", 4, "d", 0.4, tilt_k=0.5, ncore=0)
    row("rv", 13, 3.6, 3.1, 3.7, ridge, STACK["rv"], "l", 4, "v", 1.9, tilt_k=0.5, ncore=0)
    # attache au dos : écailles rondes qui descendent vers le corps, elles recouvrent la masse de l'épaule
    for k in range(3):
        feather(f"bk{k}_{tag}", s, 1.0 + 1.5 * k, 26.0 + 0.5 * k, 5.2, 3.9, 3 + 5 * k, f"l{(k + 2) % 4}", segs[0], STACK["bk"], side="v", ncore=0, dz=alt("bk", k))
    # scapulaires dorées : couvrent la racine et prolongent l'arche jusqu'à la colonne
    for k in range(4):
        feather(f"sc{k}_{tag}", s, 1.8 + 1.5 * k, 26.2 + 0.9 * k, 7.0 - 0.5 * k, 4.4, 2 + 7 * k, f"l{k}", segs[0], STACK["sc"], side="d", ncore=1, dz=alt("sc", k))

    # petite paire basse : éventail radial sous la grande aile, un peu en retrait
    zl = Z - 0.4
    r0 = group(f"lowroot_{tag}", [s * 3.0, 17.0, zl], rotation=(0, -s * 26, 0))
    r1 = group(f"lowmid_{tag}", [s * 7.0, 15.5, zl], parent=r0)
    (xa, xb) = sorted([s * 1.4, s * 3.4])
    groups[r0]["ids"].append(cube(f"lowarm_{tag}", [xa, 16.0, 2.6], [xb, 17.3, zl + 0.6], [s * 3.0, 17.0, zl], rot=(0, 0, -s * 14), faces=gold_faces))
    NF = 6
    for k in range(NF):
        f = (k + 0.5) / NF
        tilt = lerp(38, 78, f)
        L = lerp(13.5, 15.5, f)
        par, ox, oy = (r0, 3.2 + 0.5 * k, 16.8 - 0.25 * k) if k < 2 else (r1, 3.2 + 1.0 * k, 16.8 - 0.25 * k)
        feather(f"lf{k}_{tag}", s, ox, oy, L, 4.8, tilt, f"f{k % 3}", par, STACK["lf"], ncore=2, own_bone=True, zb=zl, dz=alt("lf", k))
    for k in range(3):
        f = (k + 0.5) / 3
        feather(f"lc_{k}_{tag}", s, 1.9 + 2.3 * k, 18.0 - 0.5 * k, 4.6, 3.6, lerp(46, 72, f), f"l{k + 1}", r0 if k == 0 else r1, STACK["lc"], side="d", ncore=1, zb=zl, dz=alt("lc_", k))
    return segs[0], r0


(L_, LD_), (R_, RD_) = build(-1), build(1)


# ------------------------------------------------------------------ taille (2026-11-04, .claude/styles/ailes-anatomie.md)
# L'aile est dessinée en grand puis réduite DANS SON PLAN (x, y) par K autour de l'épaule ; la profondeur (z : empilement des
# rangées, épaisseur des peaux et des âmes) garde ses valeurs, donc l'écart entre couches ne diminue pas. Un cube tourné est
# remplacé par le cube le plus proche de son image (décomposition polaire) : rotations de quelques degrés, erreur négligeable.


def _euler(Rm):
    """Inverse de rot_matrix (R = Rz·Ry·Rx, ordre de Blockbench)."""
    ry = math.asin(max(-1.0, min(1.0, -Rm[2, 0])))
    return (math.degrees(math.atan2(Rm[2, 1], Rm[2, 2])), math.degrees(ry), math.degrees(math.atan2(Rm[1, 0], Rm[0, 0])))


def _rot(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
            @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))


def reduire(racine, P, k):
    M = np.diag([k, k, 1.0])
    P = np.array(P, float)
    T = lambda v: P + M @ (np.array(v, float) - P)
    par_uuid = {e["uuid"]: e for e in elements}
    todo = [racine]
    while todo:
        n = todo.pop()
        todo += [m for m, g in groups.items() if g["parent"] == n]
        g = groups[n]
        g["origin"] = [round(v, 3) for v in T(g["origin"])]
        for u in g["ids"]:
            e = par_uuid[u]
            o = np.array(e["origin"], float)
            Rm = _rot(*e.get("rotation", (0, 0, 0)))
            ext = np.array(e["to"]) - np.array(e["from"])
            # axes propres du cube, du plus long au plus mince : le plus long garde sa direction exacte, le plan des deux plus
            # longs (le plan d'une plaque) est exactement l'image du plan d'origine ; seul l'axe mince est recalculé.
            i0, i1, i2 = np.argsort(-ext)
            MR = M @ Rm
            l = MR[:, i0] / np.linalg.norm(MR[:, i0])
            w = MR[:, i1] - (MR[:, i1] @ l) * l
            sc = np.ones(3)
            sc[i0] = np.linalg.norm(MR[:, i0])
            sc[i1] = np.linalg.norm(w)
            w /= sc[i1]
            nrm = np.cross(l, w)
            if nrm @ Rm[:, i2] < 0:
                nrm = -nrm
            Q = np.zeros((3, 3))
            Q[:, i0], Q[:, i1], Q[:, i2] = l, w, nrm
            if np.linalg.det(Q) < 0:          # repère indirect : on retourne l'axe mince et on garde la boîte symétrique
                Q[:, i2] = -Q[:, i2]
            sc[i2] = 1.0 if ext[i2] <= 0.35 else abs(MR[:, i2] @ Q[:, i2])   # axe mince : plaque gardée à son épaisseur ; sinon : ≈ 1 s'il est en profondeur (peaux, âmes), ≈ K s'il est dans le plan (os)
            a, b = (np.array(e["from"]) - o) * sc, (np.array(e["to"]) - o) * sc
            if np.linalg.det(Q) > 0 and Q[:, i2] @ Rm[:, i2] < 0:
                a[i2], b[i2] = -b[i2], -a[i2]
            o2 = T(o)
            e["origin"] = [round(v, 3) for v in o2]
            e["from"] = [round(v, 3) for v in o2 + a]
            e["to"] = [round(v, 3) for v in o2 + b]
            rr = _euler(Q)
            if any(abs(v) > 1e-3 for v in rr):
                e["rotation"] = [round(v, 2) for v in rr]
            else:
                e.pop("rotation", None)


for _s, _t in ((-1, "l"), (1, "r")):
    for _g in (f"shoulder_{_t}", f"wingroot_{_t}"):
        reduire(_g, (_s * 3.0, 23.0, Z), K)
    reduire(f"lowroot_{_t}", (_s * 3.0, 17.0, Z - 0.4), KL)

# halo : une seule plaque carrée dont l'anneau vient de l'alpha ; aucun segment, aucun chevauchement. Tranches transparentes.
H = group("halo", [0, 36.5, 0])
hu0, hv0, hu1, hv1 = UV["halo"]
groups[H]["ids"].append(cube("halo", [-HALF, 36.43, -HALF], [HALF, 36.58, HALF], [0, 36.5, 0],
                             faces={"up": [hu0, hv0, hu1, hv1], "down": [hu0, hv1, hu1, hv0], "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR}))

# Particule (guide, section 5 ter) : une seule plaque, courbure et contour peints dans l'image. Couchée, base vers -Z, pointe vers +Z.
# Face up seule texturée : aucune double couche, et la plaque flotte à 0,3 px au-dessus du pivot : aucun contact avec le sol.
PL = group("particle_plume", [0, 0, 0])
PW, PLEN, PTH, PY = 2.4, 7.0, 0.3, 0.3
pu0, pv0, pu1, pv1 = UV["plume"]
groups[PL]["ids"].append(cube("plume", [-PW / 2, PY, -PLEN / 2], [PW / 2, PY + PTH, PLEN / 2], [0, 0, 0],
                              faces={"up": [pu0, pv0, pu1, pv1]}))


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(),
             "children": [{"name": "item", "origin": [0, 0, 0], "uuid": nuid(),
                           "children": [bone("wingroot_l"), bone("wingroot_r"), bone(L_), bone(R_), bone(LD_), bone(RD_)]}]},
            # groupe de premier niveau : suit la tête (le mod remplace son pivot par le cou) ; le halo garde son pivot au centre de l'anneau
            {"name": "head", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone(H)]},
            bone(PL)]

# ------------------------------------------------------------------ animations
# Les courbes décrivent l'aile GAUCHE en termes d'intention :
#   fx > 0 : le plan bascule vers l'horizontale ; fy > 0 : pivote vers l'arrière ; fz > 0 : la pointe monte.
TAU = 2 * math.pi

# MIROIR D'AXES : seul endroit à toucher si la convention du mod change (un signe suffit).
# Repères de docs/guide-cosmetiques.md, section 3 : +X = le haut bascule vers l'arrière,
# +Y = le côté droit (+X) avance, +Z = le côté droit monte, donc le côté gauche descend.
SX, SY, SZ = -1, -1, +1


def mirror(s, fx, fy, fz):
    """s = -1 aile gauche, +1 aile droite. Renvoie les valeurs de keyframe."""
    return SX * fx, s * SY * fy, s * SZ * fz


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 2)), "y": str(round(y + 0.0, 2)), "z": str(round(z + 0.0, 2))}],
            "time": round(t, 3), "interpolation": "linear"}


def S(T, amp, ph=0.0, off=0.0):
    return lambda t: off + amp * math.sin(TAU * t / T + math.radians(ph))


def C(v):
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


def anim(name, length, segs, fan, n_kf=None, halo=None, halo_pos=None, loop="loop", only=None, low_z=0.8):
    """segs : shoulder/elbow/wrist -> (fx, fy, fz) ; fan(t) > 0 écarte les rémiges.
    halo(t) -> (x, y, z) en valeurs de keyframe, halo_pos(t) -> déplacement Y (px).
    only : familles de groupes animées (attaque et blessé, joués une fois par-dessus l'état)."""
    A = {}

    def put(g, kfs):
        if only is None or re.sub(r"\d*_[lr]$", "", g) in only:
            A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}

    n = n_kf or max(6, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]   # interpolation linéaire : dernier keyframe = premier
    dl = 0.08 * length
    for s, tag in ((-1, "l"), (1, "r")):
        for seg, (fx, fy, fz) in segs.items():
            put(f"{seg}_{tag}", [kf("rotation", t, *mirror(s, fx(t), fy(t), fz(t))) for t in times])
        # petite paire : 80 % d'amplitude, léger retard ; lowmid suit le coude
        for low, seg in (("lowroot", "shoulder"), ("lowmid", "elbow")):
            fx, fy, fz = segs[seg]
            put(f"{low}_{tag}", [kf("rotation", t, *mirror(s, 0.8 * fx((t - dl) % length), 0.8 * fy((t - dl) % length),
                                                          low_z * fz((t - dl) % length))) for t in times])
        for k in range(8):
            w = 0.4 + 0.6 * (k + 0.5) / 8
            put(f"p{k}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, fan(t) * w)) for t in times])
        for k in range(6):
            put(f"s{k}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, fan(t) * 0.3 * (k + 0.5) / 6)) for t in times])
        for k in range(6):
            w = 0.25 + 0.55 * (k + 0.5) / 6
            put(f"lf{k}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, fan((t - dl) % length) * w)) for t in times])
    halo_kf = []
    if halo:
        halo_kf += [kf("rotation", t, *halo(t)) for t in times]
    if halo_pos:
        halo_kf += [kf("position", t, 0, halo_pos(t), 0) for t in times]
    if halo_kf:
        put("halo", halo_kf)
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "idle", "animators": A}


def spin(T):
    """Exactement un tour par boucle, valeurs de keyframe entre 0 et 360°."""
    return lambda t: (0, 360.0 * t / T, 0)


def rock(T, ax=2.0, az=1.5, ox=0.0):
    """Le halo se balance sans tourner, pour les états courts où un tour complet serait trop rapide."""
    return lambda t: (ox + ax * math.sin(TAU * t / T), 0, az * math.cos(TAU * t / T))


Z0 = C(0)

# idle 8 s : repos replié, plan vertical, plumes qui pendent (pointes au niveau des mollets, 2026-11-04 : Z de l'épaule, du coude et
# du poignet abaissés de 22, 18 et 20°) ; respiration (4 s) + étirement ample ponctuel 4,6–7,2 s. Halo : couche overlay_halo.
st = lambda t: bump(t, 4.6, 5.4, 6.0, 7.2)
mix = lambda f, v: (lambda t: f(t) * (1 - st(t)) + v * st(t))
idle = anim("idle", 8.0, {
    "shoulder": (mix(S(4, 1.0, 0, 5), 16), mix(S(4, 1.5, 0, 14), -8), mix(S(4, 2, 0, -20), 12)),
    "elbow":    (Z0, mix(S(4, 1, -40, -6), -4), mix(S(4, 1.5, -40, -20), 5)),
    "wrist":    (Z0, mix(S(4, 0.8, -70, 6), -6), mix(S(4, 1, -70, -30), 4))},
    fan=lambda t: (3 + 1.0 * math.sin(TAU * t / 4)) * (1 - st(t)) + 11 * st(t), n_kf=48)

# fly 2,4 s : le joueur reste debout en vol créatif. Plan basculé d'environ 40° (pas 90°), ailes ouvertes, battement ample.
# Y annule le balayage de repos pour que l'aile reste étalée, lisible de face, de dos et de dessous.
T = 2.4
up = lambda t, lag=0.0: 0.5 + 0.5 * math.cos(TAU * (t / T - lag))
fly = anim("fly", T, {
    "shoulder": (S(T, 4, 90, 40), S(T, 5, 90, -18), S(T, 24, 0, 2)),
    "elbow":    (Z0, lambda t: 8 - 3 * up(t, 0.12), S(T, 8, -45, -2)),
    "wrist":    (Z0, lambda t: -8 + 3 * up(t, 0.22), lambda t: 3 + 5 * math.sin(TAU * t / T - math.radians(75)) - 13 * up(t, 0.22))},
    fan=lambda t: 7 - 6 * math.cos(TAU * t / T), n_kf=24, halo=rock(T, 2, 2, 14))

# glide 3,6 s : joueur couché, le cosmétique suit le torse. Horizontal dans le monde = dans le plan du dos, X faible.
# Le battement sort du plan du dos : il passe par Y (pivot autour de l'axe du corps), plus par Z. Déduit, non observé en jeu.
G = 3.6
# Battement à la fusée : A monte avec la vitesse et s'annule en piqué. Période 0,6 s (600 °/s), base 3,6 s (100 °/s) : tout se ferme sur 3,6 s.
BOOST = f"math.clamp((math.max(q.ground_speed,q.vertical_speed)-{V0})/{DV},0,1)*math.clamp((q.vertical_speed+8)/4,0,1)"


def term(amp, speed, ph):
    """Texte Molang de amp*sin(speed*t + ph), signe compris ; amp = 0 : vide."""
    if not amp:
        return ""
    p = f"{ph:+g}" if ph else ""
    return f"{amp:+g}*math.sin(q.anim_time*{speed}{p})"


def mol(sign, base, slow=(0, 0), boost=(0, 0)):
    """base + slow[0]*sin(100t+slow[1]) + boost[0]*A*sin(600t+boost[1]), multiplié par sign (miroir). Courte, sans ? ni &&."""
    e = f"{sign * base:g}" + term(sign * slow[0], 100, slow[1])
    if boost[0]:
        e += f"{sign * boost[0]:+g}*{BOOST}*math.sin(q.anim_time*600{boost[1]:+g})"
    assert len(e) <= 256
    return e


def mkf(x, y, z):
    return {"channel": "rotation", "data_points": [{"x": x, "y": y, "z": z}], "time": 0, "interpolation": "linear"}


def glide_anim():
    a = anim("glide", G, {k: (Z0, Z0, Z0) for k in SEG}, fan=C(0), n_kf=24, halo=rock(G, 1.5, 1.5, 16), only={"halo"})
    A = a["animators"]

    def put(g, x, y, z):
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [mkf(x, y, z)]}

    for s_, tag in ((-1, "l"), (1, "r")):
        sy, sz = s_ * SY, s_ * SZ        # même miroir que mirror() : X = SX * fx, Y = s * SY * fy, Z = s * SZ * fz
        put(f"shoulder_{tag}", mol(SX, 8, (1.5, 90)), mol(sy, -14, (11, 0), (24, 0)), f"{sz * -4:g}")
        put(f"elbow_{tag}", "0", mol(sy, 8, (-3, -43), (11, -45)), f"{sz * 1:g}")
        put(f"wrist_{tag}", "0", mol(sy, -8, (4, -79), (13, -90)), f"{sz * 6:g}")
        put(f"lowroot_{tag}", mol(SX, 6.4, (1.2, 62)), mol(sy, -11, (9, -29), (15, -30)), f"{sz * -3:g}")
        put(f"lowmid_{tag}", "0", mol(sy, 6.4, (-2.4, -72), (6, -75)), f"{sz * 1:g}")
        for k in range(8):
            w = 0.4 + 0.6 * (k + 0.5) / 8
            put(f"p{k}_{tag}", "0", "0", mol(sz, round(10 * w, 2), (round(-2 * w, 2), 90), (round(7 * w, 2), -90)))
        for k in range(6):
            w = 0.3 * (k + 0.5) / 6
            put(f"s{k}_{tag}", "0", "0", mol(sz, round(10 * w, 2), (round(-2 * w, 2), 90)))
        for k in range(6):
            w = 0.25 + 0.55 * (k + 0.5) / 6
            put(f"lf{k}_{tag}", "0", "0", mol(sz, round(10 * w, 2), (round(-2 * w, 2), 61)))
    return a


glide = glide_anim()

# fall 1,5 s (état « en l'air » du mod) : joueur debout, ailes relevées et ouvertes, plan peu basculé (freinage)
AI = 1.5
fall = anim("fall", AI, {"shoulder": (S(AI, 3, 0, 26), C(-4), S(AI, 4, 0, 16)),
                         "elbow": (Z0, C(3), S(AI, 3, -40, 7)),
                         "wrist": (Z0, C(-4), S(AI, 3, -70, 10))},
            fan=C(11), halo=rock(AI, 1.5, 1.5, 6))

# walk 1,6 s : ramenées vers l'arrière, balancement au pas
W = 1.6
walk = anim("walk", W, {"shoulder": (C(8), S(W, 5, 0, 30), S(W, 3.5, 0, -8)),
                        "elbow": (Z0, S(W, 3, -40, -10), S(W, 2, -40, -4)),
                        "wrist": (Z0, S(W, 3, -70, 14), S(W, 2.5, -70, -12))},
            fan=C(-5), halo=rock(W, 1.2, 1.2))

# run 1,0 s : très vers l'arrière, abaissées, repli en S réparti sur les 3 articulations
R = 1.0
run = anim("run", R, {"shoulder": (C(16), S(R, 3, 0, 50), S(R, 3, 0, -16)),
                      "elbow": (Z0, S(R, 2, -40, -28), S(R, 1.5, -40, -5)),
                      "wrist": (Z0, S(R, 3, -80, 36), S(R, 2, -80, -8))},
          fan=C(-5), halo=rock(R, 1.5, 1.5, 8))

# sneak 3 s : repliées serrées dans le dos
SN = 3.0
sneak = anim("sneak", SN, {"shoulder": (C(6), S(SN, 1, 0, 58), S(SN, 1, 0, 6)),
                           "elbow": (Z0, C(-34), S(SN, 1, -40, 6)),
                           "wrist": (Z0, C(38), C(10))},
             fan=C(-9), halo=rock(SN, 1, 1))

# sleep 4 s : tombantes, pointes vers le bas ; la petite paire ne suit presque pas Z pour ne pas croiser sous le torse
SL = 4.0
sleep = anim("sleep", SL, {"shoulder": (C(14), S(SL, 1, 0, 34), S(SL, 1, 0, -30)),
                           "elbow": (Z0, C(-16), C(-8)),
                           "wrist": (Z0, C(18), C(-16))},
             fan=C(-6), low_z=0.1)

# swim 2 s : joueur couché. Ailes dans le plan du dos, rabattues vers les pieds (Z négatif), profilées ; ondulation hors du plan par Y. Déduit, non observé en jeu.
SW = 2.0
swim = anim("swim", SW, {"shoulder": (C(7), S(SW, 7, 0, 2), C(-34)),
                         "elbow": (Z0, S(SW, 6, -45, 6), C(-10)),
                         "wrist": (Z0, S(SW, 7, -90, -4), C(-8))},
            fan=C(-7), halo=rock(SW, 1.5, 1.5, 10), low_z=0.5)

# mount 3 s : repos relevé, pointes hautes, respiration ample
MT = 3.0
mount = anim("mount", MT, {"shoulder": (C(10), S(MT, 2.5, 0, 8), S(MT, 3.5, 0, 20)),
                           "elbow": (Z0, S(MT, 1.5, -40, -4), S(MT, 2, -40, 7)),
                           "wrist": (Z0, C(2), S(MT, 2, -70, 16))},
             fan=C(2))

# attack et hurt : une fois par-dessus l'état, dernière image neutre, seuls les groupes concernés.
IMPULSE = {"shoulder", "elbow", "wrist", "p", "lowroot"}
# attack 0,8 s : déploiement brusque puis retour
AT = 0.8
atk = lambda t: bump(t, 0.0, 0.14, 0.30, 0.72)
attack = anim("attack", AT, {"shoulder": (lambda t: 26 * atk(t), lambda t: -14 * atk(t), lambda t: 14 * atk(t)),
                             "elbow": (Z0, lambda t: -6 * atk(t), lambda t: 5 * atk(t)),
                             "wrist": (Z0, lambda t: -8 * atk(t), lambda t: 4 * atk(t))},
              fan=lambda t: 12 * atk(t), n_kf=16, loop="once", only=IMPULSE)

# hurt 0,8 s : sursaut vers l'arrière + tremblement amorti
HU = 0.8
hu = lambda t: bump(t, 0.0, 0.08, 0.22, 0.72)
tr = lambda t: 3 * math.sin(TAU * t * 5 / HU) * (1 - sm(t, 0.25, 0.7))
hurt = anim("hurt", HU, {"shoulder": (lambda t: 6 * hu(t), lambda t: 16 * hu(t), lambda t: 8 * hu(t) + tr(t)),
                         "elbow": (Z0, lambda t: -6 * hu(t), lambda t: -3 * hu(t) + tr(t)),
                         "wrist": (Z0, lambda t: 8 * hu(t), lambda t: -3 * hu(t) + tr(t))},
            fan=lambda t: -7 * hu(t), n_kf=16, loop="once", only=IMPULSE)



def particle_anim(name, length, curve, n):
    times = [i * length / n for i in range(n + 1)]
    return {"uuid": nuid(), "name": name, "loop": "loop", "override": False, "length": length, "snapping": 24, "selected": False,
            "animators": {groups[PL]["uuid"]: {"name": PL, "type": "bone", "keyframes": [kf("rotation", t, *curve(t)) for t in times]}}}


# chute 4 s : un tour complet autour de Y (boucle fermée) et un balancement doux. Plus d'animation de repos au sol (16 animations
# au plus) : elle ne faisait que 1,2° de balancement, la plume posée reste immobile (guide 5 ter : animation facultative).
PF = 4.0
plume_fall = particle_anim("particle_plume_fall", PF, lambda t: (20 * math.sin(TAU * t / PF), 360 * t / PF, 14 * math.cos(2 * TAU * t / PF)), 24)

# overlay_halo 8 s (guide 6.4) : le tour du halo et son flottement, joués en permanence par-dessus l'état. Avant, le tour était dans
# idle, sleep et mount seulement : il sautait à chaque changement d'état. Les états gardent leur léger balancement (rock), qui s'ajoute.
HO = 8.0
_ht = [i * HO / 48 for i in range(49)]
overlay_halo = {"uuid": nuid(), "name": "overlay_halo", "loop": "loop", "override": False, "length": HO, "snapping": 24, "selected": False,
                "animators": {groups["halo"]["uuid"]: {"name": "halo", "type": "bone", "keyframes":
                              [kf("rotation", t, 0, 360.0 * t / HO, 0) for t in _ht] + [kf("position", t, 0, 0.5 * math.sin(TAU * t / HO), 0) for t in _ht]}}}


# Apparition et retrait (guide 6.4). Joués une fois par-dessus l'état : rotations et positions s'AJOUTENT à celles de l'état, échelles
# se MULTIPLIENT. Pas de sac ni de boîtier : les ailes sortent du haut du dos, pliées et minuscules, grandissent, se déplient de l'épaule
# vers les primaires (cascade), s'étirent un peu au-delà de la pose de l'état, puis s'y posent. Le halo s'allume en dernier.
def event_anim(name, L, k_scale, k_fold, k_fan, k_halo, k_root, n=None, sons=()):
    """k_scale(t) : échelle des ailes ; k_fold(t) : 1 = repliées dans le dos, 0 = pose de l'état ; k_fan(t) : ouverture ajoutée des
    rémiges (°) ; k_halo(t) : échelle du halo ; k_root(t) : échelle des masses d'épaule. Dernière image : neutre (equip) ou 0 (unequip)."""
    n = n or int(round(L * 10))
    times = [round(i * L / n, 3) for i in range(n + 1)]
    A = {}

    def put(g, kfs):
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}

    def lag(f, d):                       # cascade : chaque articulation suit avec un retard
        return lambda t: f(max(0.0, t - d))

    fold = {"shoulder": (0, 40, -25), "elbow": (0, -34, 6), "wrist": (0, 42, -16)}   # pli en Z serré, pointes vers le bas
    for s_, tag in ((-1, "l"), (1, "r")):
        for i, seg in enumerate(SEG):
            fx, fy, fz = fold[seg]
            kfold = lag(k_fold, 0.12 * i)
            ks = [kf("rotation", t, *mirror(s_, fx * kfold(t), fy * kfold(t), fz * kfold(t))) for t in times]
            if seg == "shoulder":
                ks += [kf("scale", t, k_scale(t), k_scale(t), k_scale(t)) for t in times]
                # sortie du dos : la racine part de 1,5 px dans le torse (canal position, z supposé dans le sens du modèle)
                ks += [kf("position", t, 0, 0, -1.5 * k_fold(t)) for t in times]
            put(f"{seg}_{tag}", ks)
        kl, sl = lag(k_fold, 0.1), lag(k_scale, 0.15)
        put(f"lowroot_{tag}", [kf("rotation", t, *mirror(s_, 0, 30 * kl(t), -20 * kl(t))) for t in times]
            + [kf("scale", t, sl(t), sl(t), sl(t)) for t in times])
        put(f"wingroot_{tag}", [kf("scale", t, k_root(t), k_root(t), k_root(t)) for t in times])
        for k in range(8):
            w = 0.4 + 0.6 * (k + 0.5) / 8
            put(f"p{k}_{tag}", [kf("rotation", t, *mirror(s_, 0, 0, k_fan(max(0.0, t - 0.03 * k)) * w)) for t in times])
        for k in range(6):
            w = 0.25 + 0.55 * (k + 0.5) / 6
            put(f"lf{k}_{tag}", [kf("rotation", t, *mirror(s_, 0, 0, k_fan(max(0.0, t - 0.1 - 0.03 * k)) * w)) for t in times])
    put("halo", [kf("scale", t, k_halo(t), k_halo(t), k_halo(t)) for t in times])
    a = {"uuid": nuid(), "name": name, "loop": "once", "override": False, "length": L, "snapping": 24, "selected": False, "animators": A}
    if sons:
        a["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes":
                                     [{"channel": "sound", "data_points": [{"effect": e, "file": ""}], "time": t} for t, e in sons]}
    return a


# event_equip 1,8 s : 0–0,5 s les ailes sortent du dos (échelle 0,03 → 0,6), 0,25–1,2 s elles grandissent et se déplient en
# cascade, 0,8–1,3 s les primaires s'ouvrent au-delà de la pose (étirement), 1,3–1,8 s tout se pose ; halo de 1,0 à 1,6 s.
# Un seul son, discret, au moment où l'éventail s'ouvre (tools/sons.py : un au plus pour un événement).
EQ = 1.8
eq_scale = lambda t: 0.03 + 0.97 * sm(t, 0.0, 1.15) + 0.04 * bump(t, 0.9, 1.15, 1.25, 1.6)
eq_fold = lambda t: 1 - sm(t, 0.25, 1.1) - 0.18 * bump(t, 0.85, 1.05, 1.15, 1.5)        # passe un peu au-delà (étirement), revient à 0
eq_fan = lambda t: 14 * bump(t, 0.8, 1.05, 1.15, 1.45) - 10 * (1 - sm(t, 0.3, 0.9))     # rémiges serrées, puis éventail qui s'ouvre
equip = event_anim("event_equip", EQ, eq_scale, eq_fold, eq_fan, lambda t: sm(t, 1.0, 1.6), lambda t: 0.3 + 0.7 * sm(t, 0.0, 0.5),
                   sons=((0.75, "souffle_plumes"),))   # son embarqué, sommet du souffle à 1,1 s (sons/souffle_plumes.py)
# event_unequip 2,2 s : l'apparition à l'envers, sans étirement : le halo s'éteint, les rémiges se serrent, l'aile se replie en
# cascade puis rentre dans le dos en rapetissant ; dernière image à l'échelle 0, gardée jusqu'au départ (guide 6.4).
UQ = 2.2
unequip = event_anim("event_unequip", UQ, lambda t: 1 - sm(t, 1.0, 2.0), lambda t: sm(t, 0.2, 1.3), lambda t: -10 * sm(t, 0.1, 0.8),
                     lambda t: 1 - sm(t, 0.0, 0.6), lambda t: 1 - sm(t, 1.4, 2.0))

ANIMS = [idle, fly, glide, sneak, walk, run, fall, swim, mount, sleep, attack, hurt, plume_fall, overlay_halo, equip, unequip]
assert 6 <= len(EMITS) <= 32 and len(ANIMS) <= 16
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": "ailes_berenice",
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner,
         "textures": [{"name": "ailes_berenice.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
                      {"name": "ailes_berenice_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}], "animations": ANIMS}
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
embarquer_sons(model, {"souffle_plumes": "sons/souffle_plumes.ogg"})   # son original synthétisé (tools/synthe.py)
limiter_sons(model)          # un son au plus, à l'apparition ; aucun en mouvement (retour « infernal »)
os.makedirs(".build", exist_ok=True)
OUT = ".build/ailes_berenice_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))
with open(OUT) as fh:
    json.load(fh)


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 3, "groupes ; profondeur", depth(outliner[0]), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko")
