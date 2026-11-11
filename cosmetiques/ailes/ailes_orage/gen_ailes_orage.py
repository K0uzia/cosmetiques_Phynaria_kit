"""Ailes d'orage (v7, 2026-11-08) — ensemble Orage (thème Éléments) : aile de faucon en plumes de métal forgé, la foudre court
sur le bord d'attaque et saute de pointe en pointe des primaires. Design original.
Fiches : .claude/styles/orage.md, .claude/styles/ailes-anatomie.md, .claude/references/effets/foudre.md (section « Ailes de
métal forgé », sources). Écrit ailes_orage.png, ailes_orage_e.png et .build/ailes_orage_brut.bbmodel.
Point de départ : gen_ailes_berenice.py (plume peau + âme, réduction K, cascade d'articulations), non modifié.

Retours qui fixent la v7 (.claude/rules/categories/ailes.md) :
- v6 (ailes en traits d'éclair) : « je n'aime pas du tout ». Direction choisie : vraie aile d'oiseau à plumes de métal sombre,
  foudre qui court sur les bords ;
- v1 : silhouette du givre refusée ; v2 : forme ouverte et bascule de vol faible (~6°) appréciées, repos « panier » et texture en
  zigzags « filet » refusés ; v4 : les ailes ne se croisent jamais.

Silhouette (propre à l'Orage) : aile « rapide » de faucon, longue, étroite et pointue. 7 primaires en lames longues et droites,
la 2e et la 3e depuis l'extérieur les plus longues (pointe de l'aile), la plus extérieure un peu plus courte ; bout taillé en
biseau (pointe côté bord d'attaque, comme un fil de lame) ; 7 secondaires courtes et égales (bord de fuite droit) ; pas de
petite paire. Différente du givre (éclats en éventail), du steampunk (lames rondes de papillon de nuit) et de Bérénice (aile
large et ronde, plumes ivoire).
Matière : acier d'orage bleu-noir martelé ; rémiges = lames : fil poli clair sur le bord extérieur, bande de revenu (cuivre puis
violet, couleurs de trempe de l'acier) derrière le fil, liseré d'or sur le bord intérieur, rachis en filet de foudre captive
(bleu-blanc, lumière nette de jour comme de nuit) ; couvertures sombres liserées d'or ; écailles et scapulaires gravées d'une
virgule d'or (lore : tambours gravés de virgules) ; crête du bord d'attaque en plaques d'acier clair.

Foudre (géométrie, cœur opaque blanc-bleu + calque _e, gaine add_ bleu-violet ; aucune trans_) :
- bord d'attaque : un trait en zigzag court de l'épaule au poignet puis le long du bord de la primaire extérieure, posé sur la
  crête ; le cœur est toujours là (le métal conduit), la gaine respire faiblement ;
- décharge (au hasard, toutes les 2 à 6 s selon l'état, plus souvent si la vie est basse) : la gaine s'allume section par
  section de l'épaule vers la pointe (0,2 s), puis l'éclair saute de pointe en pointe des primaires (4 arcs, en cascade), deux
  arcs en retour, gerbe d'étincelles aux pointes. Arcs entre pointes seulement ailes ouvertes (vol, élytres, chute, nage),
  au repos la décharge s'arrête à la pointe de l'aile repliée.

États : idle, walk, run, sneak, fly (bascule faible ~10°, V ouvert), glide (fusée V0 = 26, DV = 5), fall, swim, mount, sleep,
attack (déploiement brusque, décharge le long de l'aile), hurt (court-circuit : gaine coupée, recul, tremblement), event_equip
(les ailes sortent du dos repliées, se déploient en cascade, les lames s'ouvrent en éventail, puis la décharge court sur le bord
et saute de pointe en pointe ; un son block.copper_bulb.turn_on), event_unequip (repli, gaine éteinte, échelle 0).
Fonctions avancées : add_, ctrl_alpha, ctrl_emit, particle_etincelle + emit_etincelle, calque _e, event_equip, event_unequip,
son, Molang (q.life_time, q.instance_seed, q.health, q.max_health, variables v.).
À juger en jeu seulement (/cosmetique apercu) : hasard et cadence des décharges, gaine additive de jour, calque _e de nuit,
étincelles, somme de l'apparition avec l'état.
"""
import base64, io, json, math, os, random, re, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "ailes_orage"
TEX = 512
V0, DV = 26, 5      # battement à la fusée (glide), validé en jeu sur Bérénice
SS = 4
tex = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))


# ------------------------------------------------------------------ textures
def lerp(a, b, k):
    return a + (b - a) * k


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


GOLD = (222, 172, 70)
GOLD_E = (120, 92, 40)
COPPER = (184, 114, 62)
PAL = {
    # racine, milieu, bout (acier d'orage martelé)
    "p": ((26, 30, 46), (58, 66, 96), (86, 98, 134)),
    "s": ((26, 30, 46), (52, 60, 88), (76, 86, 120)),
    "g": ((34, 38, 56), (70, 78, 106), (96, 106, 140)),
    "m": ((30, 33, 50), (54, 60, 86), (66, 74, 102)),
    "l": ((28, 31, 46), (44, 49, 72), (52, 58, 84)),
    "k": ((30, 34, 50), (50, 56, 82), (62, 70, 100)),
    "r": ((70, 80, 110), (118, 130, 166), (150, 162, 198)),
    "u": ((22, 24, 36), (40, 45, 66), (52, 58, 84)),
}
SHAPE = {
    # demi-largeur intérieure, extérieure, début de l'arrondi, courbure, biseau (0 = bout rond), longueur d'ombre
    "p": (0.40, 0.36, 0.80, 0.05, 0.30, 0.40),
    "s": (0.42, 0.38, 0.80, 0.03, 0.22, 0.42),
    "g": (0.45, 0.38, 0.58, 0.05, 0.0, 0.36),
    "m": (0.45, 0.40, 0.52, 0.04, 0.0, 0.34),
    "l": (0.46, 0.42, 0.44, 0.03, 0.0, 0.16),
    "k": (0.46, 0.42, 0.44, 0.03, 0.0, 0.16),
    "r": (0.46, 0.42, 0.44, 0.03, 0.0, 0.16),
    "u": (0.45, 0.39, 0.56, 0.05, 0.0, 0.34),
}
BLADE = "ps"


def paint(W, H, kind, seed):
    rng = np.random.default_rng(seed)
    root, mid, tip = (np.array(c, np.float32) for c in PAL[kind])
    hi, ho, te, curve, cut, shl = SHAPE[kind]
    jitter = rng.uniform(0.96, 1.03)
    w, h = W * SS, H * SS
    x, y = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    t = y                                                     # 0 = base, 1 = pointe
    cx = 0.5 + curve * (t * t - 0.3)
    d = x - cx
    if kind in BLADE:
        # lame : se resserre un peu vers le bout, bout taillé en biseau (le côté intérieur est coupé plus tôt)
        env = (0.30 + 0.70 * smooth(t / 0.16)) * (1 - 0.18 * t)
        lim = np.where(d >= 0, ho * env, hi * env)
        xn = np.clip((d + hi * env) / np.maximum((hi + ho) * env, 1e-4), 0, 1)      # 0 bord intérieur, 1 bord extérieur
        tcut = 1 - cut * (1 - xn) ** 1.15 - 0.012
        r = np.abs(d) / np.maximum(lim, 1e-4)
        inside = (r < 1) & (t < tcut)
        dcut = (tcut - t) * H                                # distance au biseau, en texels (approchée)
    else:
        env = (0.28 + 0.72 * smooth(t / 0.20)) * np.where(t > te, np.sqrt(np.clip(1 - ((t - te) / (1 - te)) ** 2, 0, 1)), 1.0)
        lim = np.where(d >= 0, ho * env, hi * env)
        r = np.abs(d) / np.maximum(lim, 1e-4)
        inside = r < 1
        dcut = np.full_like(t, 99.0)
    alpha = inside * 255.0
    dist = np.minimum((1 - r) * lim * W, dcut)               # distance au bord, en texels

    k1 = smooth(t / 0.5)[..., None]
    k2 = smooth((t - 0.5) / 0.5)[..., None]
    col = lerp(lerp(root, mid, k1), tip, k2) * jitter
    # martelage : grain doux de basse fréquence (±5 % au plus, retour « traits jaunes partout » : pas de brossé fort)
    n = rng.normal(0, 1, (max(2, H // 10), max(2, W // 10))).astype(np.float32)
    n = np.array(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8), "L").resize((w, h), Image.BICUBIC), np.float32)
    col = col * (1 + 0.05 * ((n - 128) / 80).clip(-1, 1))[..., None]
    # relief : plus clair près du rachis, plus sombre au bord
    col = col * (1.06 - 0.20 * (r ** 2))[..., None]
    # ombre de recouvrement à la base
    shd = (np.clip(1 - t / shl, 0, 1) ** 1.25)[..., None]
    col = lerp(col, np.array((12, 13, 22), np.float32), shd * 0.72)

    ec = np.empty(col.shape, np.float32)
    ec[...] = (10, 11, 18)
    out_side = (d >= 0)[..., None]
    if kind in BLADE:
        # bord extérieur = fil de lame : fil poli (3,5 texels), puis bande de revenu cuivre puis violet
        fil = (dist < 2.5)[..., None] & (out_side | (dcut < 2.5)[..., None])
        cuivre = ((dist >= 2.5) & (dist < 4.1))[..., None] & out_side
        violet = ((dist >= 4.1) & (dist < 5.4))[..., None] & out_side
        col = np.where(cuivre, lerp(col, np.array((196, 118, 64), np.float32), 0.85), col)
        col = np.where(violet, lerp(col, np.array((112, 88, 172), np.float32), 0.70), col)
        col = np.where(fil, np.array((184, 198, 232), np.float32) * (0.92 + 0.08 * t[..., None]), col)
        # bord intérieur : liseré d'or (3,5 texels)
        orl = ((dist < 2.5) & (d < 0) & (t > 0.10) & (dcut >= 2.5))[..., None]
        col = np.where(orl, np.array(GOLD, np.float32), col)
        ec = np.where(fil & (t[..., None] > 0.25), np.array((70, 84, 124), np.float32), ec)
        ec = np.where(orl, np.array(GOLD_E, np.float32), ec)
        # rachis : filet de foudre captive (4 texels, cœur blanc au milieu), jusqu'avant le biseau
        ra = np.abs(d) * W
        on = (t > 0.05) & (dcut > 5)
        gl = ((ra < 1.7) & on)[..., None]
        cr = ((ra < 0.8) & on)[..., None]
        col = np.where(gl, np.array((120, 176, 255), np.float32), col)
        col = np.where(cr, np.array((232, 242, 255), np.float32), col)
        ec = np.where(gl, np.array((96, 150, 255), np.float32), ec)
        ec = np.where(cr, np.array((196, 218, 255), np.float32), ec)
    else:
        rim_c = {"g": COPPER, "m": COPPER, "l": GOLD, "k": (150, 96, 56), "r": (214, 224, 246), "u": (92, 102, 140)}[kind]
        rw = {"g": 2.6, "m": 3.2, "l": 3.5, "k": 2.6, "r": 3.0, "u": 3.0}[kind]
        rim = ((dist < rw) & (t > 0.10))[..., None]
        col = np.where(rim, np.array(rim_c, np.float32), col)
        if kind in "gmlk":
            ec = np.where(rim, np.array(GOLD_E if kind == "l" else (90, 60, 34), np.float32), ec)
        if kind == "g":         # rachis discret : filet bleu
            ra = np.abs(d) * W
            gl = ((ra < 1.6) & (t > 0.08) & (t < 0.86))[..., None]
            col = np.where(gl, np.array((96, 140, 220), np.float32), col)
            ec = np.where(gl, np.array((70, 110, 210), np.float32), ec)
        if kind == "l":
            # virgule d'or (moitié de cercle + deux demi-disques : la forme d'une virgule de tambour), centrée sur l'écaille
            px, py = x * W, t * H
            cxp, cyp, R = W * 0.5, H * 0.56, min(W, H) * 0.27
            dx, dy = px - cxp, py - cyp
            big = np.hypot(dx, dy) < R
            top = np.hypot(dx, dy + R / 2) < R / 2
            bot = np.hypot(dx, dy - R / 2) < R / 2
            vir = ((big & (dx < 0)) | top) & ~bot
            eye = np.hypot(dx, dy + R / 2) < R * 0.16
            vir = (vir & ~eye)[..., None]
            col = np.where(vir, np.array(GOLD, np.float32) * 1.02, col)
            ec = np.where(vir, np.array((168, 128, 54), np.float32), ec)
    ec = np.clip(ec, 0, 225)
    global PAINT_E
    PAINT_E = (np.minimum(np.array(Image.fromarray(ec.astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)), 225), None)
    rgb = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    a = Image.fromarray(alpha.astype(np.uint8), "L").resize((W, H), Image.LANCZOS)
    arr_rgb, arr_a = np.array(rgb), np.array(a)
    solid = arr_a > 110
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = arr_rgb
    if solid.any():
        arr[~solid, :3] = arr_rgb[solid].mean(axis=0).astype(np.uint8)
    arr[..., 3] = solid * 255
    return Image.fromarray(arr, "RGBA")


def edge_strip(kind, W=6, H=32):
    """Bande opaque des tranches (âmes) : acier sombre, suit le dégradé de la plume."""
    root, mid, tip = (np.array(c, np.float32) for c in PAL[kind])
    a = np.zeros((H, W, 4), np.float32)
    for yy in range(H):
        t = (yy + 0.5) / H
        c = lerp(root, mid, min(1, t * 2)) if t < 0.5 else lerp(mid, tip, (t - 0.5) * 2)
        a[yy, :, :3] = c * 0.8
    a[..., 3] = 255
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def solid_tile(W, H, base, line, dark):
    """Tuile opaque de matière (os de métal) : dégradé vertical et filet central d'or de 4 texels."""
    a = np.zeros((H, W, 4), np.float32)
    base, line, dark = (np.array(c, np.float32) for c in (base, line, dark))
    for yy in range(H):
        a[yy, :, :3] = lerp(base, dark, yy / max(1, H - 1))
    c = H // 2
    a[c - 2:c + 2, :, :3] = line
    a[..., 3] = 255
    return Image.fromarray(a.astype(np.uint8), "RGBA")


# --- foudre (recette de la v6 : cœur opaque, gaine additive), étincelle
CORE_C, CORE_B = (238, 245, 255), (110, 160, 255)
CORE_EC, CORE_EB = (198, 214, 225), (60, 96, 210)


def t_core():
    a = np.zeros((6, 16, 4), np.uint8)
    a[..., :3] = CORE_C
    a[0, :, :3] = a[5, :, :3] = CORE_B
    a[..., 3] = 255
    e = a.copy()
    e[..., :3] = CORE_EC
    e[0, :, :3] = e[5, :, :3] = CORE_EB
    return a, e


def t_halo():
    a = np.zeros((8, 16, 4), np.uint8)
    for v in range(8):
        dd = abs((v + 0.5) / 8 * 2 - 1)
        k = (1 - dd) ** 1.4
        a[v, :, :3] = np.array((10, 8, 34)) + k * np.array((40, 70, 170))
    a[..., 3] = 255
    return a


def t_spark(N=16, ss=4):
    yy, xx = np.mgrid[0:N * ss, 0:N * ss]
    x, y = (xx + 0.5) / (N * ss) * 2 - 1, 1 - (yy + 0.5) / (N * ss) * 2
    dd = np.abs(x) ** 0.5 + np.abs(y) ** 0.5
    m = np.array(Image.fromarray(((dd < 0.95) * 255).astype(np.uint8), "L").resize((N, N), Image.LANCZOS)) > 110
    c = np.array(Image.fromarray(((dd < 0.55) * 255).astype(np.uint8), "L").resize((N, N), Image.LANCZOS)) > 110
    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = (150, 200, 255)
    out[c, :3] = (245, 248, 255)
    out[..., 3] = m * 255
    return out


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


seed = 11
EIMG = {}
for kind, n, W, H in (("p", 5, 48, 224), ("s", 4, 48, 150), ("g", 4, 52, 104), ("m", 3, 44, 72),
                      ("u", 3, 48, 90), ("l", 4, 40, 48), ("k", 4, 40, 48), ("r", 4, 40, 48)):
    for i in range(n):
        name = f"{kind}{i}"
        im = paint(W, H, kind, seed)
        place(name, im)
        ea, emask = PAINT_E
        mask = np.array(im)[..., 3] > 0
        EIMG[name] = (ea, mask)
        seed += 1
for kind in PAL:
    place(f"edge_{kind}", edge_strip(kind))
place("bone", solid_tile(32, 32, (64, 72, 100), GOLD, (24, 26, 40)))
core_a, core_e = t_core()
for nm, arr in (("core", core_a), ("halo", t_halo()), ("spark", t_spark())):
    place(nm, Image.fromarray(arr, "RGBA"))
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex.getpixel((TEX - 3, TEX - 3))[3] == 0
_t = np.array(tex)
_t[..., :3] &= 0xFC
assert set(np.unique(_t[..., 3])) <= {0, 255}, "semi-transparence"
tex = Image.fromarray(_t, "RGBA")
tex.save(f"{NOM}.png")
_b = io.BytesIO()
tex.save(_b, "PNG", optimize=True)
tex_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()

# Calque lumineux : jamais assigné aux faces. Sources nettes : rachis de foudre des rémiges, cœurs d'éclair, virgules et liserés
# d'or (plus faibles) ; fond très sombre.
_e = np.zeros((TEX, TEX, 4), np.uint8)
for name, (ea, mask) in EIMG.items():
    u0, v0, u1, v1 = UV[name]
    _e[v0:v1, u0:u1, :3] = ea
    _e[v0:v1, u0:u1, 3] = mask * 255
for nm in [f"edge_{k}" for k in PAL] + ["bone"]:
    u0, v0, u1, v1 = UV[nm]
    _e[v0:v1, u0:u1] = (10, 11, 18, 255)
u0, v0, u1, v1 = UV["core"]
_e[v0:v1, u0:u1] = core_e
assert _e[..., :3].max() <= 225, "calque trop vif"
assert set(np.unique(_e[..., 3])) <= {0, 255}
tex_e = Image.fromarray(_e, "RGBA")
tex_e.save(f"{NOM}_e.png", optimize=True)
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
    assert name not in groups, name
    assert len(name.split("#")[0]) <= 64
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


ARM = [(3.0, 23.0), (10.0, 31.0), (20.0, 35.5), (30.5, 35.2)]   # main allongée : aile de faucon
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
    return 20 + 50 * f ** 1.15      # aile pointue : les primaires extérieures filent vers la pointe


EMITS = []


def emit(parent, at):
    """Point de départ de plume (guide, section 5 ter) : groupe vide, pivot = endroit exact, suit le groupe qui le porte."""
    EMITS.append(group("emit_etincelle" + (str(len(EMITS) + 1) if EMITS else ""), at, parent=parent))
    group(f"ctrl_emit#{len(EMITS)}", at, parent=EMITS[-1])


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

    # primaires (main) : 7 lames, os propres ; la 2e et la 3e depuis l'extérieur les plus longues (pointe de faucon)
    for k in range(NP):
        f = (k + 0.5) / NP
        ax, ay = pos(2, f)
        L = 23.0 + 11.0 * f ** 0.8 - (3.2 if k == NP - 1 else 0) + (0.6 if k % 2 else 0)
        tip = feather(f"p{k}_{tag}", s, ax, ay - 0.4, L, 5.4 - 0.7 * f, tilt_at(2, f), f"p{k % 5}", segs[2], remex(1.0), ncore=3, own_bone=True, dz=alt("p", k))
        TIPS[(s, k)] = (np.array(tip), ax, ay - 0.4, L, tilt_at(2, f), 5.4 - 0.7 * f)
        if k in (4, 5, 6):
            emit(f"p{k}_{tag}", tip)
    # secondaires (avant-bras) : 7 courtes et presque égales, bord de fuite droit
    for k in range(NS):
        f = (k + 0.5) / NS
        ax, ay = pos(1, f)
        L = 14.0 + 1.6 * f + (0.7 if k % 2 else 0)
        feather(f"s{k}_{tag}", s, ax, ay - 0.4, L, 5.0, tilt_at(1, f), f"s{k % 4}", segs[1], remex(0.5), ncore=2, own_bone=True, dz=alt("s", k))
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
    row("lc", 13, 4.4, 4.0, 3.9, lambda i, f: core_radius(i, f) + 0.5, STACK["l"], "k", 4, "d", 2.6, tilt_k=0.6, ncore=0)
    # côté face : sous-alaires claires et froides, deux rangées
    row("uc", 10, 8.5, 10.0, 5.2, lambda i, f: -0.1, STACK["u"], "u", 3, "v", 0.7)
    row("um", 11, 4.8, 4.8, 4.2, lambda i, f: core_radius(i, f) * 0.95, STACK["um"], "u", 3, "v", 2.0, ncore=0)
    row("ua", 12, 3.6, 3.2, 3.4, lambda i, f: core_radius(i, f) + 0.5, stack(-2.05 - MG[6], -1.6 - MG[6], 0.75, 0.62), "u", 3, "v", 3.4, tilt_k=0.6, ncore=0)
    # crête du bord d'attaque : le noyau n'est plus visible de dessus, ni replié
    ridge = lambda i, f: core_radius(i, f) * 0.56 + 0.75
    row("rd", 13, 3.6, 3.1, 3.7, ridge, STACK["rd"], "r", 4, "d", 0.4, tilt_k=0.5, ncore=0)
    row("rv", 13, 3.6, 3.1, 3.7, ridge, STACK["rv"], "r", 4, "v", 1.9, tilt_k=0.5, ncore=0)
    # attache au dos : écailles rondes qui descendent vers le corps, elles recouvrent la masse de l'épaule
    for k in range(3):
        feather(f"bk{k}_{tag}", s, 1.0 + 1.5 * k, 26.0 + 0.5 * k, 5.2, 3.9, 3 + 5 * k, f"r{(k + 2) % 4}", segs[0], STACK["bk"], side="v", ncore=0, dz=alt("bk", k))
    # scapulaires dorées : couvrent la racine et prolongent l'arche jusqu'à la colonne
    for k in range(4):
        feather(f"sc{k}_{tag}", s, 1.8 + 1.5 * k, 26.2 + 0.9 * k, 7.0 - 0.5 * k, 4.4, 2 + 7 * k, f"l{k}", segs[0], STACK["sc"], side="d", ncore=1, dz=alt("sc", k))

    return segs[0]


NP, NS = 7, 7
TIPS = {}
L_, R_ = build(-1), build(1)


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

# ------------------------------------------------------------------ foudre (construite après la réduction, en coordonnées finales)
# Les points sont calculés dans le dessin (aile droite), miroités puis réduits par la même transformation que les plumes : ils
# tombent exactement sur la crête et sur les pointes réduites.
def TF(s, v):
    P = np.array((s * 3.0, 23.0, Z))
    v = np.array((s * v[0], v[1], v[2]), float)
    return P + np.diag([K, K, 1.0]) @ (v - P)


def tile_faces(tile, caps=True):
    uv = list(UV[tile])
    f = {k: uv for k in ("north", "south", "up", "down")}
    if caps:
        u0, v0, u1, v1 = uv
        f["east"] = f["west"] = [u0 + 2, v0 + 1, u0 + 4, v1 - 1]
    else:
        f["east"] = f["west"] = CLEAR
    return f


def seg3(g, name, a, b, w, tile, ov, roll):
    """Tronçon droit de a à b (coordonnées finales) : cube le long de son axe X local, section w × w tournée de roll."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    rz = math.degrees(math.atan2(d[1], d[0]))
    ry = -math.degrees(math.asin(max(-1, min(1, d[2] / L))))
    groups[g]["ids"].append(cube(name, [a[0] - ov, a[1] - w / 2, a[2] - w / 2], [a[0] + L + ov, a[1] + w / 2, a[2] + w / 2], list(a),
                                 rot=(roll, ry, rz), faces=tile_faces(tile, caps=tile != "halo")))


ROLLS = [18, 52, 31, 66, 9, 44, 75, 24]
_rc = [0]


def trait(gc, gh, name, pts, w0, w1, halo=2.1, ovc=0.1):
    """Trait de foudre : cœur opaque (gc) + gaine add_ (gh) sur chaque tronçon ; épaisseur de w0 à w1."""
    n = len(pts) - 1
    for i in range(n):
        w = w0 + (w1 - w0) * i / max(1, n - 1)
        roll = ROLLS[_rc[0] % len(ROLLS)]
        _rc[0] += 1
        seg3(gc, f"{name}c{i}", pts[i], pts[i + 1], w, "core", ovc, roll)
        if gh is not None:
            seg3(gh, f"{name}h{i}", pts[i], pts[i + 1], w * halo + 0.12, "halo", 0.04, roll)


def zig(pts, J, seed, zj=0.12):
    """Zigzag à angles vifs sur une polyligne : chaque point intérieur écarté d'un côté puis de l'autre (dans le plan de l'aile)."""
    rng = random.Random(seed)
    out = [np.asarray(pts[0], float)]
    sg = rng.choice((-1, 1))
    for i in range(1, len(pts) - 1):
        tg = np.asarray(pts[i + 1], float) - np.asarray(pts[i - 1], float)
        nr = np.array((-tg[1], tg[0], 0.0))
        nr /= max(1e-6, np.linalg.norm(nr))
        out.append(np.asarray(pts[i], float) + nr * sg * J * rng.uniform(0.55, 1.0) + np.array((0, 0, rng.uniform(-zj, zj))))
        sg = -sg
    out.append(np.asarray(pts[-1], float))
    return out


def subdiv(a, b, n):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return [a + (b - a) * i / n for i in range(n + 1)]


def ctrl(nom, parent):
    return group(f"{nom}#{len(groups)}", groups[parent]["origin"], parent=parent)


BORD = []      # (s, groupe add_ de gaine, rang le long du bord : 0 épaule … 3 pointe)
ARCS = []      # (s, groupe du cœur, groupe add_ de la gaine, rang)
_lens = [math.dist(ARM[i], ARM[i + 1]) for i in range(3)]
_U = [0.0, _lens[0] / sum(_lens), (_lens[0] + _lens[1]) / sum(_lens), 1.0]


def crest(i, u):
    x, y = arch(u)
    f = (u - _U[i]) / (_U[i + 1] - _U[i])
    return (x, y + core_radius(i, f) * 0.56 + 0.75 + 1.15, Z + CORE_Z)


def blade_edge(s, k, a):
    """Point du bord extérieur (fil) de la primaire k à la distance a de sa base (dessin), à mi-épaisseur."""
    tip, ax, ay, L, tilt, w = TIPS[(s, k)]
    sn, cs = math.sin(math.radians(tilt)), math.cos(math.radians(tilt))
    off = w * 0.36 * (1 - 0.18 * a / L) + 0.15
    return (ax + sn * a + cs * off, ay - cs * a + sn * off, Z + alt("p", k) + lerp(0.6, -1.0, a / L))


for s, tag in ((-1, "l"), (1, "r")):
    # bord d'attaque : épaule → coude → poignet, posé sur la crête
    prev = None
    for i in range(3):
        nsub = (3, 4, 3)[i]
        pts = [TF(s, crest(i, lerp(_U[i], _U[i + 1], j / nsub))) for j in range(nsub + 1)]
        pts = zig(pts, 0.42, 31 * i + (s < 0), zj=0.1)
        if prev is not None:
            pts[0] = prev
        prev = pts[-1]
        gh = group(f"add_bord{i}_{tag}", pts[0], parent=f"{SEG[i]}_{tag}")
        ctrl("ctrl_alpha", gh)
        BORD.append((s, gh, i))
        trait(f"{SEG[i]}_{tag}", gh, f"bord{i}_{tag}", pts, (0.62, 0.56, 0.5)[i], (0.56, 0.5, 0.44)[i])
        seg3(f"{SEG[i]}_{tag}", f"noeud{i}_{tag}", pts[0] - np.array((0.32, 0, 0)), pts[0] + np.array((0.32, 0, 0)), 0.78, "core", 0, 45)
    # le long du fil de la primaire extérieure, jusqu'à sa pointe
    k = NP - 1
    tipL = TIPS[(s, k)][3]
    pts = [prev] + [TF(s, blade_edge(s, k, a)) for a in np.linspace(0.18, 0.985, 5) * tipL]
    pts = zig(pts, 0.36, 97 + (s < 0), zj=0.08)
    gh = group(f"add_bord3_{tag}", pts[0], parent=f"p{k}_{tag}")
    ctrl("ctrl_alpha", gh)
    BORD.append((s, gh, 3))
    trait(f"p{k}_{tag}", gh, f"bord3_{tag}", pts, 0.46, 0.32)
    # arcs de pointe en pointe des primaires (ailes ouvertes) : de la primaire k à la suivante, portés par la primaire k
    for r, k in enumerate((2, 3, 4, 5)):
        a = TF(s, blade_edge(s, k, TIPS[(s, k)][3] * 0.975))
        b = TF(s, blade_edge(s, k + 1, TIPS[(s, k + 1)][3] * 0.975))
        pts = zig(subdiv(a, b, 3), 0.55, 211 + 7 * k + (s < 0), zj=0.1)
        gc = group(f"arc{k}_{tag}", a, parent=f"p{k}_{tag}")
        ctrl("ctrl_alpha", gc)
        gh = group(f"add_arc{k}_{tag}", a, parent=gc)
        ctrl("ctrl_alpha", gh)
        ARCS.append((s, gc, gh, r))
        trait(gc, gh, f"arc{k}_{tag}", pts, 0.36, 0.3, halo=2.0)

# Particule : étincelle, un seul cube de 0,5 px, face south seule (réglage Face caméra), à 0,3 px au-dessus du pivot.
PL = group("particle_etincelle", [0, 0, 0])
groups[PL]["ids"].append(cube("etincelle", [-0.25, 0.3, -0.15], [0.25, 0.8, 0.15], [0, 0.55, 0], faces={"south": list(UV["spark"])}))


def nom_final(n):
    return n.split("#")[0]


def bone(name):
    g = groups[name]
    return {"name": nom_final(name), "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(),
             "children": [{"name": "item", "origin": [0, 0, 0], "uuid": nuid(),
                           "children": [bone("wingroot_l"), bone("wingroot_r"), bone(L_), bone(R_)]}]},
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


def _v(x):
    return x if isinstance(x, str) else str(round(x + 0.0, 3))


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": _v(x), "y": _v(y), "z": _v(z)}],
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


# --- Molang de la foudre (recette de la v6 : tirage par tranche sur q.life_time + q.instance_seed, vie basse = plus souvent)
VIE = "v.d=(q.max_health>0)*math.clamp(1.6-4*q.health/math.max(q.max_health,1),0,1);"


def H(x):
    return f"math.mod(math.abs(math.sin(({x})*127.1))*437.585,1)"


def chk(e):
    assert len(e) <= 512, (len(e), e)
    return e


def slot(s, P, pr):
    """v.g = 1 si une décharge part dans la tranche de P s en cours (probabilité pr, plus si la vie est basse) ; v.f = temps
    écoulé dans la tranche. Chaque aile a sa phase (c2)."""
    c2 = 0.37 if s > 0 else 0.81
    return (f"v.u=q.life_time/{P:g}+{c2:g}+q.instance_seed*13;v.g=({H('math.floor(v.u)')}<{pr:g}+0.3*v.d);"
            f"v.f=math.mod(v.u,1)*{P:g};")


RESTRIKE = "(v.f>0.42)*(v.f<0.47)+(v.f>0.53)*(v.f<0.57)"


def bord_expr(s, i, P, pr, R, c):
    a, b = 0.04 * i, 0.04 * i + 0.17
    return chk(VIE + slot(s, P, pr) + f"v.h={H(f'math.floor(q.life_time*{R:g}+{c:.3g})')};"
               f"math.min(-0.62+0.14*(v.h<0.35)+0.62*v.g*((v.f>{a:g})*(v.f<{b:g})+{RESTRIKE}),0)")


def arc_expr(s, r, P, pr):
    a = 0.17 + 0.035 * r
    return chk(VIE + slot(s, P, pr) + f"v.g*((v.f>{a:g})*(v.f<{a + 0.07:g})+{RESTRIKE})-1")


def emit_expr(s, P, pr):
    return chk(VIE + slot(s, P, pr) + "7*v.g*(v.f>0.17)*(v.f<0.5)-1")


def ctrl_de(g, nom):
    return next(gg["uuid"] for n, gg in groups.items() if gg["parent"] == g and nom_final(n) == nom)


def put_raw(A, u, nm, kfs):
    A[u] = {"name": nm, "type": "bone", "keyframes": kfs}


def side_of(g):
    return 1 if groups[g]["origin"][0] > 0 else -1


def storm(A, P, pr, R=7):
    for j, (s, g, i) in enumerate(BORD):
        put_raw(A, ctrl_de(g, "ctrl_alpha"), "ctrl_alpha", [kf("position", 0, bord_expr(s, i, P, pr, R, 0.13 + 1.71 * j), 0, 0)])
    for s, gc, gh, r in ARCS:
        e = arc_expr(s, r, P, pr)
        put_raw(A, ctrl_de(gc, "ctrl_alpha"), "ctrl_alpha", [kf("position", 0, e, 0, 0)])
        put_raw(A, ctrl_de(gh, "ctrl_alpha"), "ctrl_alpha", [kf("position", 0, e, 0, 0)])
    for g in EMITS:
        put_raw(A, ctrl_de(g, "ctrl_emit"), "ctrl_emit", [kf("position", 0, emit_expr(side_of(g), P, pr), 0, 0)])


def anim(name, length, segs, fan, rate, n_kf=None, loop="loop", only=None):
    """segs : shoulder/elbow/wrist -> (fx, fy, fz) ; fan(t) > 0 écarte les rémiges ; rate : (P, pr) des décharges.
    only : familles de groupes animées (attaque et blessé, joués une fois par-dessus l'état)."""
    A = {}

    def put(g, kfs):
        if only is None or re.sub(r"\d*_[lr]$", "", g) in only:
            A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}

    n = n_kf or max(6, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]   # interpolation linéaire : dernier keyframe = premier
    for s, tag in ((-1, "l"), (1, "r")):
        for seg, (fx, fy, fz) in segs.items():
            put(f"{seg}_{tag}", [kf("rotation", t, *mirror(s, fx(t), fy(t), fz(t))) for t in times])
        for k in range(NP):
            w = 0.4 + 0.6 * (k + 0.5) / NP
            put(f"p{k}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, fan(t) * w)) for t in times])
        for k in range(NS):
            put(f"s{k}_{tag}", [kf("rotation", t, *mirror(s, 0, 0, fan(t) * 0.3 * (k + 0.5) / NS)) for t in times])
    if rate:
        storm(A, *rate)
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "idle", "animators": A}


Z0 = C(0)

# idle 8 s : repos replié, plan vertical, lames qui pendent de leur côté (pointes aux mollets) ; respiration (4 s) + étirement
# ample ponctuel 4,6–7,2 s. Décharge au hasard toutes les ~5 s.
st = lambda t: bump(t, 4.6, 5.4, 6.0, 7.2)
mix = lambda f, v: (lambda t: f(t) * (1 - st(t)) + v * st(t))
idle = anim("idle", 8.0, {
    "shoulder": (mix(S(4, 1.0, 0, 5), 14), mix(S(4, 1.5, 0, 14), -8), mix(S(4, 2, 0, -20), 12)),
    "elbow":    (Z0, mix(S(4, 1, -40, -6), -4), mix(S(4, 1.5, -40, -20), 5)),
    "wrist":    (Z0, mix(S(4, 0.8, -70, 6), -6), mix(S(4, 1, -70, -30), 4))},
    fan=lambda t: (2 + 1.0 * math.sin(TAU * t / 4)) * (1 - st(t)) + 10 * st(t), rate=(2.6, 0.45), n_kf=48)

# fly 2,4 s : joueur debout en vol créatif. Bascule faible (~10°, retour v2 « l'angle est bien »), V ouvert, battement ample.
T = 2.4
up = lambda t, lag=0.0: 0.5 + 0.5 * math.cos(TAU * (t / T - lag))
fly = anim("fly", T, {
    "shoulder": (S(T, 3, 90, 10), S(T, 5, 90, -18), S(T, 22, 0, 4)),
    "elbow":    (Z0, lambda t: 8 - 3 * up(t, 0.12), S(T, 8, -45, -2)),
    "wrist":    (Z0, lambda t: -8 + 3 * up(t, 0.22), lambda t: 3 + 5 * math.sin(TAU * t / T - math.radians(75)) - 13 * up(t, 0.22))},
    fan=lambda t: 6 - 5 * math.cos(TAU * t / T), rate=(1.5, 0.6), n_kf=24)

# glide 3,6 s : joueur couché, le cosmétique suit le torse ; battement par Y, ample à la fusée (Molang).
G = 3.6
BOOST = f"math.clamp((math.max(q.ground_speed,q.vertical_speed)-{V0})/{DV},0,1)*math.clamp((q.vertical_speed+8)/4,0,1)"


def term(amp, speed, ph):
    if not amp:
        return ""
    p = f"{ph:+g}" if ph else ""
    return f"{amp:+g}*math.sin(q.anim_time*{speed}{p})"


def mol(sign, base, slow=(0, 0), boost=(0, 0)):
    e = f"{sign * base:g}" + term(sign * slow[0], 100, slow[1])
    if boost[0]:
        e += f"{sign * boost[0]:+g}*{BOOST}*math.sin(q.anim_time*600{boost[1]:+g})"
    assert len(e) <= 256
    return e


def mkf(x, y, z):
    return {"channel": "rotation", "data_points": [{"x": x, "y": y, "z": z}], "time": 0, "interpolation": "linear"}


def glide_anim():
    a = anim("glide", G, {k: (Z0, Z0, Z0) for k in SEG}, fan=C(0), rate=(1.8, 0.6), n_kf=24)
    A = a["animators"]

    def put(g, x, y, z):
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [mkf(x, y, z)]}

    for s_, tag in ((-1, "l"), (1, "r")):
        sy, sz = s_ * SY, s_ * SZ
        put(f"shoulder_{tag}", mol(SX, 8, (1.5, 90)), mol(sy, -14, (11, 0), (24, 0)), f"{sz * -4:g}")
        put(f"elbow_{tag}", "0", mol(sy, 8, (-3, -43), (11, -45)), f"{sz * 1:g}")
        put(f"wrist_{tag}", "0", mol(sy, -8, (4, -79), (13, -90)), f"{sz * 6:g}")
        for k in range(NP):
            w = 0.4 + 0.6 * (k + 0.5) / NP
            put(f"p{k}_{tag}", "0", "0", mol(sz, round(9 * w, 2), (round(-2 * w, 2), 90), (round(6 * w, 2), -90)))
        for k in range(NS):
            w = 0.3 * (k + 0.5) / NS
            put(f"s{k}_{tag}", "0", "0", mol(sz, round(9 * w, 2), (round(-2 * w, 2), 90)))
    return a


glide = glide_anim()

AI = 1.5
fall = anim("fall", AI, {"shoulder": (S(AI, 3, 0, 18), C(-4), S(AI, 4, 0, 16)),
                         "elbow": (Z0, C(3), S(AI, 3, -40, 7)),
                         "wrist": (Z0, C(-4), S(AI, 3, -70, 10))},
            fan=C(10), rate=(1.4, 0.6))
W = 1.6
walk = anim("walk", W, {"shoulder": (C(8), S(W, 5, 0, 30), S(W, 3.5, 0, -8)),
                        "elbow": (Z0, S(W, 3, -40, -10), S(W, 2, -40, -4)),
                        "wrist": (Z0, S(W, 3, -70, 14), S(W, 2.5, -70, -12))},
            fan=C(-5), rate=(2.2, 0.5))
R = 1.0
run = anim("run", R, {"shoulder": (C(16), S(R, 3, 0, 50), S(R, 3, 0, -16)),
                      "elbow": (Z0, S(R, 2, -40, -28), S(R, 1.5, -40, -5)),
                      "wrist": (Z0, S(R, 3, -80, 36), S(R, 2, -80, -8))},
          fan=C(-5), rate=(1.6, 0.55))
SN = 3.0
sneak = anim("sneak", SN, {"shoulder": (C(6), S(SN, 1, 0, 58), S(SN, 1, 0, 6)),
                           "elbow": (Z0, C(-34), S(SN, 1, -40, 6)),
                           "wrist": (Z0, C(38), C(10))},
             fan=C(-9), rate=(3.2, 0.35))
SL = 4.0
sleep = anim("sleep", SL, {"shoulder": (C(14), S(SL, 1, 0, 34), S(SL, 1, 0, -30)),
                           "elbow": (Z0, C(-16), C(-8)),
                           "wrist": (Z0, C(18), C(-16))},
             fan=C(-6), rate=(4.0, 0.25))
SW = 2.0
swim = anim("swim", SW, {"shoulder": (C(7), S(SW, 7, 0, 2), C(-34)),
                         "elbow": (Z0, S(SW, 6, -45, 6), C(-10)),
                         "wrist": (Z0, S(SW, 7, -90, -4), C(-8))},
            fan=C(-7), rate=(2.0, 0.5))
MT = 3.0
mount = anim("mount", MT, {"shoulder": (C(10), S(MT, 2.5, 0, 8), S(MT, 3.5, 0, 20)),
                           "elbow": (Z0, S(MT, 1.5, -40, -4), S(MT, 2, -40, 7)),
                           "wrist": (Z0, C(2), S(MT, 2, -70, 16))},
             fan=C(2), rate=(2.6, 0.45))


# --- outils des animations once : créneaux (fenêtres de temps), gardés justes dans l'aperçu de l'animation seule
def creneaux(t, fen):
    return 1.0 if any(a <= t < b for a, b in fen) else 0.0


def cles_creneaux(ch, fen, L, val=1.0, base=0.0, fin=None, uni=False):
    ts = {0.0, L, L - 0.005}
    for a, b in fen:
        ts |= {max(0.0, a - 0.005), a, max(0.0, min(L, b) - 0.005), min(L, b)}
    out = []
    for t in sorted(ts):
        v = base + val * creneaux(t if t < L else L - 1e-6, fen)
        if t >= L and fin is not None:
            v = fin
        out.append(kf(ch, t, v, v, v) if uni else kf(ch, t, v, 0, 0))
    return out


def decharge(A, L, t0, off_before=False, fin_arc=1.0):
    """Décharge des apparitions et de l'attaque : la gaine s'allume section par section de l'épaule vers la pointe à partir de
    t0, puis les arcs sautent de pointe en pointe, deux arcs en retour, gerbe d'étincelles. Par-dessus l'état : gaine +0,62 dans
    ses fenêtres (−1 avant t0 si off_before) ; arcs : ctrl_alpha +1 toute l'animation, échelle 0 hors de leurs fenêtres."""
    rs = [(t0 + 0.47, t0 + 0.52), (t0 + 0.58, t0 + 0.62)]
    for s, g, i in BORD:
        fen = [(t0 + 0.04 * i, t0 + 0.04 * i + 0.2)] + rs
        if off_before:
            kfs = cles_creneaux("position", fen + [(0.0, t0)], L, val=0.62, fin=0.0)
            kfs = [kf("position", k["time"], -1, 0, 0) if k["time"] < t0 - 0.004 else k for k in kfs]
        else:
            kfs = cles_creneaux("position", fen, L, val=0.62, fin=0.0)
        put_raw(A, ctrl_de(g, "ctrl_alpha"), "ctrl_alpha", kfs)
    for s, gc, gh, r in ARCS:
        a = t0 + 0.2 + 0.04 * r
        fen = [(a, a + 0.08)] + rs
        put_raw(A, ctrl_de(gc, "ctrl_alpha"), "ctrl_alpha", cles_creneaux("position", [(0.0, L)], L, fin=0.0))
        put_raw(A, ctrl_de(gh, "ctrl_alpha"), "ctrl_alpha", cles_creneaux("position", [(0.0, L)], L, fin=0.0))
        put_raw(A, groups[gc]["uuid"], nom_final(gc), cles_creneaux("scale", fen, L, fin=fin_arc, uni=True))
    for g in EMITS:
        put_raw(A, ctrl_de(g, "ctrl_emit"), "ctrl_emit", cles_creneaux("position", [(t0 + 0.2, t0 + 0.6)], L, val=8.0, fin=0.0))


# attack 0,8 s : anticipation (l'aile se ramasse), déploiement brusque à 0,14 s, la décharge court sur l'aile et saute de
# pointe en pointe pendant le gel, retour.
IMPULSE = {"shoulder", "elbow", "wrist", "p"}
AT = 0.8
atk = lambda t: bump(t, 0.06, 0.16, 0.34, 0.74) - 0.25 * bump(t, 0.0, 0.05, 0.05, 0.12)
attack = anim("attack", AT, {"shoulder": (lambda t: 18 * atk(t), lambda t: -14 * atk(t), lambda t: 16 * atk(t)),
                             "elbow": (Z0, lambda t: -6 * atk(t), lambda t: 5 * atk(t)),
                             "wrist": (Z0, lambda t: -8 * atk(t), lambda t: 4 * atk(t))},
              fan=lambda t: 12 * atk(t), rate=None, n_kf=16, loop="once", only=IMPULSE)
decharge(attack["animators"], AT, 0.12)

# hurt 0,8 s : court-circuit : recul, tremblement amorti, la gaine s'éteint trois fois, arcs coupés ; le cœur reste (sobre).
HU = 0.8
hu = lambda t: bump(t, 0.0, 0.08, 0.22, 0.72)
tr = lambda t: 3 * math.sin(TAU * t * 5 / HU) * (1 - sm(t, 0.25, 0.7))
hurt = anim("hurt", HU, {"shoulder": (lambda t: 6 * hu(t), lambda t: 16 * hu(t), lambda t: 8 * hu(t) + tr(t)),
                         "elbow": (Z0, lambda t: -6 * hu(t), lambda t: -3 * hu(t) + tr(t)),
                         "wrist": (Z0, lambda t: 8 * hu(t), lambda t: -3 * hu(t) + tr(t))},
            fan=lambda t: -7 * hu(t), rate=None, n_kf=16, loop="once", only=IMPULSE)
for s, g, i in BORD:
    put_raw(hurt["animators"], ctrl_de(g, "ctrl_alpha"), "ctrl_alpha",
            cles_creneaux("position", [(0.0, 0.12), (0.2, 0.3), (0.38, 0.5)], HU, val=-1.0, fin=0.0))
for s, gc, gh, r in ARCS:
    put_raw(hurt["animators"], groups[gc]["uuid"], nom_final(gc), cles_creneaux("scale", [(0.0, 0.6)], HU, val=-1.0, base=1.0, fin=1.0, uni=True))
    put_raw(hurt["animators"], ctrl_de(gc, "ctrl_alpha"), "ctrl_alpha", cles_creneaux("position", [], HU, fin=0.0))
    put_raw(hurt["animators"], ctrl_de(gh, "ctrl_alpha"), "ctrl_alpha", cles_creneaux("position", [], HU, fin=0.0))

# particule : l'étincelle scintille (échelle)
PF = 0.4
p_fall = {"uuid": nuid(), "name": "particle_etincelle_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24, "selected": False,
          "animators": {groups[PL]["uuid"]: {"name": PL, "type": "bone", "keyframes":
                        [kf("scale", t, *([1 + 0.35 * math.cos(TAU * t / PF)] * 3)) for t in [i * PF / 8 for i in range(9)]]}}}


# Apparition et retrait (guide 6.4), par-dessus l'état : rotations et positions s'AJOUTENT, échelles se MULTIPLIENT.
def event_anim(name, L, k_scale, k_fold, k_fan, k_root, n=None, sons=()):
    n = n or int(round(L * 10))
    times = [round(i * L / n, 3) for i in range(n + 1)]
    A = {}

    def put(g, kfs):
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": kfs}

    def lag(f, d):
        return lambda t: f(max(0.0, t - d))

    fold = {"shoulder": (0, 40, -25), "elbow": (0, -34, 6), "wrist": (0, 42, -16)}   # pli en Z serré, pointes vers le bas
    for s_, tag in ((-1, "l"), (1, "r")):
        for i, seg in enumerate(SEG):
            fx, fy, fz = fold[seg]
            kfold = lag(k_fold, 0.12 * i)
            ks = [kf("rotation", t, *mirror(s_, fx * kfold(t), fy * kfold(t), fz * kfold(t))) for t in times]
            if seg == "shoulder":
                ks += [kf("scale", t, k_scale(t), k_scale(t), k_scale(t)) for t in times]
                ks += [kf("position", t, 0, 0, -1.5 * k_fold(t)) for t in times]
            put(f"{seg}_{tag}", ks)
        put(f"wingroot_{tag}", [kf("scale", t, k_root(t), k_root(t), k_root(t)) for t in times])
        for k in range(NP):
            w = 0.4 + 0.6 * (k + 0.5) / NP
            put(f"p{k}_{tag}", [kf("rotation", t, *mirror(s_, 0, 0, k_fan(max(0.0, t - 0.03 * k)) * w)) for t in times])
    a = {"uuid": nuid(), "name": name, "loop": "once", "override": False, "length": L, "snapping": 24, "selected": False, "animators": A}
    if sons:
        a["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes":
                                     [{"channel": "sound", "data_points": [{"effect": e, "file": ""}], "time": t} for t, e in sons]}
    return a


# event_equip 2,0 s : les ailes sortent du dos repliées (0–0,5 s), grandissent et se déplient en cascade (0,25–1,1 s), les lames
# s'ouvrent d'un coup en éventail (0,8–1,05 s) ; à 1,0 s la décharge court sur le bord d'attaque et saute de pointe en pointe,
# gerbe d'étincelles ; tout se pose à 2,0 s. Gaine éteinte jusqu'à la décharge. Un seul son, au moment de la décharge.
EQ = 2.0
eq_scale = lambda t: 0.03 + 0.97 * sm(t, 0.0, 1.15) + 0.04 * bump(t, 0.9, 1.15, 1.25, 1.6)
eq_fold = lambda t: 1 - sm(t, 0.25, 1.1) - 0.18 * bump(t, 0.85, 1.05, 1.15, 1.5)
eq_fan = lambda t: 16 * bump(t, 0.8, 0.98, 1.15, 1.6) - 10 * (1 - sm(t, 0.3, 0.85))
equip = event_anim("event_equip", EQ, eq_scale, eq_fold, eq_fan, lambda t: 0.3 + 0.7 * sm(t, 0.0, 0.5),
                   sons=((1.0, "block.copper_bulb.turn_on"),))
decharge(equip["animators"], EQ, 1.0, off_before=True)
# event_unequip 2,2 s : la gaine s'éteint, les lames se serrent, l'aile se replie en cascade puis rentre dans le dos ; échelle 0.
UQ = 2.2
unequip = event_anim("event_unequip", UQ, lambda t: 1 - sm(t, 1.0, 2.0), lambda t: sm(t, 0.2, 1.3), lambda t: -10 * sm(t, 0.1, 0.8),
                     lambda t: 1 - sm(t, 1.4, 2.0))
for s, g, i in BORD:
    put_raw(unequip["animators"], ctrl_de(g, "ctrl_alpha"), "ctrl_alpha", cles_creneaux("position", [(0.15, UQ + 1)], UQ, val=-1.0, fin=-1.0))
for s, gc, gh, r in ARCS:
    put_raw(unequip["animators"], groups[gc]["uuid"], nom_final(gc), cles_creneaux("scale", [], UQ, base=0.0, fin=0.0, uni=True))

ANIMS = [idle, fly, glide, sneak, walk, run, fall, swim, mount, sleep, attack, hurt, p_fall, equip, unequip]
assert 6 <= len(EMITS) <= 32 and len(ANIMS) <= 32
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner,
         "textures": [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
                      {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}], "animations": ANIMS}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model)          # un son au plus, à l'apparition ; aucun en mouvement
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


def ngroupes(n):
    return 1 + sum(ngroupes(c) for c in n.get("children", []) if isinstance(c, dict))


print(len(elements), "cubes ;", sum(ngroupes(n) for n in outliner), "groupes ; profondeur", max(depth(n) for n in outliner), ";",
      len(ANIMS), "anims ;", sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;",
      os.path.getsize(OUT) // 1024, "Ko ;", len(EMITS), "emit_")
