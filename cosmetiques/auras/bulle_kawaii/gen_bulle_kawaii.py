"""Bulle de chewing-gum (v3, revue du 2026-11-08) : une grappe de bulles de gomme rose bonbon derrière la tête et les épaules,
qui gonflent par bouffées puis éclatent l'une après l'autre (« pop » : éclair, lambeaux), sur une lueur rose qui épouse la
silhouette, avec un rond de bulles au sol et des bullettes qui montent. Design original, ensemble Kawaii (thème Mignon,
fiche .claude/styles/kawaii.md ; .claude/references/effets/bulles.md, .claude/references/effets/auras.md).
Écrit bulle_kawaii.png, bulle_kawaii_e.png et .build/bulle_kawaii_brut.bbmodel à côté de ce script.

Pourquoi une refonte (avis du 2026-11-08 : « bof pas très beau », « revoir les aura ») : la v2 (gardée dans .build/gen_avant.py)
était une seule boule de 72 facettes à côté de l'épaule : un objet en orbite (« pas une aura »), facettée, rose terne et
petite à 10 blocs. Ici la bulle redevient une lumière autour de la silhouette, comme aura_berenice (« bien ») :
- Grappe de 7 bulles (rayons 1,5 à 6,2 px) dans un seul groupe cam_ centré sur la nuque, reculées de 10 à 11 px : toujours
  derrière la tête vue de la caméra, jamais devant le visage. Chaque bulle est une plaque face caméra peinte comme une sphère :
  film rose franc en trans_ (alpha 150 au centre, 235 au bord, plus clair au bord), grand reflet blanc en « fenêtre » en haut
  à gauche, petit contre-reflet, liseré menthe irisé en bas. Couleurs franches (leçon du set : pastel clair en trans_ = blanc).
- Cycle de 20 s au repos : chaque bulle renaît petite, gonfle en trois bouffées, tremble en se tendant, puis éclate : éclair
  additif (anneau et traits de « pop » rose et menthe) qui s'ouvre en 0,3 s, lambeaux de gomme qui partent en étoile et
  rétrécissent. Cinq éclats bien espacés (2,5 / 6 / 9,5 / 13 / 17,5 s) et quatre petits ; un seul son, le pop de la grosse
  bulle à 17,5 s (son embarqué pop_gomme, sons/pop_gomme.py).
- Lueur de silhouette : disques add_ rose bonbon en cam_ reculés derrière chaque partie du corps, vides au centre (recette
  aura_brasier v3 / aura_berenice). Ils sont devant les bulles vues de la caméra : trans_ ne cache pas cet additif.
- Sol : rond de 16 petites bulles brillantes en trans_ (lisible de jour), doublé d'une lueur rose additive (lisible de nuit),
  qui tourne lentement ; masqué quand le corps n'est pas debout.
- Bullettes : particle_bullette (0,7 px, une face) qui montent depuis 10 points. Rien ne tombe ni ne se pose.
- Calque _e : seulement les reflets blancs des bulles (≈ 200 après tools/ambiance.py) : des points nets qui brillent la nuit.

États : idle (cycle de 20 s), walk et run (bulles plus petites qui traînent vers l'arrière, rebond au pas), sneak (rentrées),
fly, fall (étirées vers le haut), glide et swim (corps couché : bulles réduites), mount, sleep (une seule bulle de sommeil qui
respire, sans éclater). Pas d'attack ni de hurt (pièce portée). event_equip (1,4 s) : les bulles naissent l'une après
l'autre en « plop » (son embarqué bloup) ; event_unequip (1,2 s) : elles se tendent et éclatent en cascade (un pop).
overlay_bulles : rotation lente des disques et du rond au sol. overlay_ambiance ajoutée par tools/ambiance.py.

Fonctions avancées (guide 4 bis, 5 ter, 6.4, 6.5) : trans_, add_, cam_, ctrl_alpha, particle_/emit_, overlay_, event_equip,
event_unequip, sons embarqués, calque _e.

Ce qui se juge seulement en jeu (/cosmetique apercu) : la teinte réelle du film trans_ sur le ciel, l'additif de jour, le fondu
de l'éclair (ctrl_alpha non simulé : le rendu le montre plein), les overlays, les bullettes, le calque _e de nuit.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "bulle_kawaii"
AVEC_E = True       # reflets des bulles seulement (sources nettes) ; les textures add_ n'ont rien dans _e
TEX = 512
SS = 4
RNG = np.random.default_rng(17)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def grille(W, H):
    n_w, n_h = W * SS, H * SS
    return np.meshgrid((np.arange(n_w) + 0.5) / n_w * 2 - 1, 1 - (np.arange(n_h) + 0.5) / n_h * 2)


# ------------------------------------------------------------------ palettes
ROSE_ADD = [(0.0, (0, 0, 0)), (0.2, (34, 6, 22)), (0.45, (112, 24, 72)), (0.7, (200, 58, 130)), (0.9, (244, 108, 176)), (1.0, (255, 150, 204))]
MENTHE_ADD = [(0.0, (0, 0, 0)), (0.3, (10, 40, 34)), (0.7, (60, 170, 140)), (1.0, (150, 240, 214))]
G_FORT, G_DOUX = 0.58, 0.42

GUM_LIT = np.array((255, 150, 206), float)
GUM = np.array((255, 74, 162), float)
GUM_OMB = np.array((200, 34, 124), float)
GUM_BORD = np.array((255, 176, 218), float)
MENTHE = np.array((120, 232, 206), float)
BLANC = np.array((255, 255, 255), float)


def pal(stops, f):
    f = np.clip(f, 0, 1)
    xs = [s_[0] for s_ in stops]
    return np.stack([np.interp(f, xs, [s_[1][c] for s_ in stops]) for c in range(3)], axis=-1)


def reduire_add(rgb, W, H):
    """Texture additive : presque noir = transparent, alpha 0/255."""
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = np.array(im)
    lum = arr[..., :3].max(axis=2)
    arr[..., 3] = (lum > 14) * 255
    arr[lum <= 14, :3] = 0
    return arr


def reduire_trans(rgb, a, W, H, e=None):
    """Texture trans_ : couverture < 50 % = transparent, sinon alpha 1..254 ; e : intensité _e (0..255) facultative."""
    cov = np.array(Image.fromarray((np.clip(a, 0, 1) > 0).astype(np.uint8) * 255, "L").resize((W, H), Image.BOX)) / 255
    am = np.array(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.BOX)).astype(float)
    am = am / np.maximum(cov, 1e-3)
    col = np.array(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    arr = np.zeros((H, W, 4), np.uint8)
    inside = cov >= 0.5
    arr[..., :3] = col
    arr[..., 3] = np.where(inside, np.clip(am, 1, 254), 0).astype(np.uint8)
    arr[~inside, :3] = 0
    em = np.zeros((H, W, 4), np.uint8)
    if e is not None:
        if e.ndim == 2:
            e = np.repeat(e[..., None], 3, axis=2)
        ev = np.array(Image.fromarray(np.clip(e, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
        ev = np.where((inside & (ev.max(axis=2) > 10))[..., None], ev, 0)
        em[..., :3] = ev
        em[..., 3] = np.where(ev.max(axis=2) > 0, 255, 0)
    return arr, em


# ------------------------------------------------------------------ peintures
CORE = 0.42


def disque_f(seed, N=64):
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    wob = 1 + 0.05 * np.sin(5 * a + seed) + 0.035 * np.sin(9 * a + 2.3 * seed)
    s_ = np.clip((r / wob - CORE) / (0.97 - CORE), 0, 1)
    f = (1 - s_) ** 1.7 * 0.95 * smooth(r / wob / CORE) ** 1.3
    return f * smooth((1 - r) / 0.06)


def ellipse_tournee(x, y, cx, cy, ax, ay, rot, dur=0.06):
    c, s_ = math.cos(rot), math.sin(rot)
    u, v = (x - cx) * c + (y - cy) * s_, -(x - cx) * s_ + (y - cy) * c
    d = np.hypot(u / ax, v / ay)
    return smooth((1 - d) / dur)


def bulle_f(N, var=0):
    """Sphère de gomme vue de face : (rgb, alpha 0..1, intensité _e)."""
    x, y = grille(N, N)
    r = np.hypot(x, y)
    nz = np.sqrt(np.clip(1 - r * r, 0, 1))
    L = np.array((-0.45, 0.62, 0.64))
    L /= np.linalg.norm(L)
    ndl = x * L[0] + y * L[1] + nz * L[2]
    k = smooth(ndl * 0.6 + 0.62)
    rgb = GUM_OMB[None, None] * (1 - k[..., None]) + GUM[None, None] * k[..., None]
    rgb = rgb + (GUM_LIT - GUM)[None, None] * smooth((ndl - 0.55) / 0.4)[..., None]
    fres = (1 - nz) ** 2.0
    rgb = rgb * (1 - 0.55 * fres[..., None]) + GUM_BORD[None, None] * 0.55 * fres[..., None]
    # lumière renvoyée en bas (gomme épaisse) : croissant plus clair
    rebond = smooth((r - 0.62) / 0.2) * smooth((-y - 0.25) / 0.35) * smooth((0.97 - r) / 0.05)
    rgb = rgb * (1 - 0.35 * rebond[..., None]) + GUM_BORD[None, None] * 0.35 * rebond[..., None]
    a = 0.70 + 0.25 * fres
    # liseré menthe irisé, en bas à gauche (arc fin près du bord)
    ang = np.arctan2(y, x)
    arc_c = math.radians(-128 + 14 * var)
    da = np.angle(np.exp(1j * (ang - arc_c)))
    menthe = np.exp(-((r - 0.84) / 0.035) ** 2) * smooth((0.75 - np.abs(da)) / 0.35)
    rgb = rgb * (1 - 0.85 * menthe[..., None]) + MENTHE[None, None] * 0.85 * menthe[..., None]
    a = np.maximum(a, 0.85 * menthe)
    # reflet en fenêtre (grand, net) + point, contre-reflet en croissant en bas à droite
    fen = ellipse_tournee(x, y, -0.38, 0.42, 0.24, 0.15, math.radians(38), 0.10)
    fen = np.maximum(fen, ellipse_tournee(x, y, -0.08, 0.66, 0.075, 0.06, 0, 0.2))
    contre = np.exp(-((r - 0.78) / 0.04) ** 2) * smooth((0.42 - np.abs(np.angle(np.exp(1j * (ang - math.radians(-38)))))) / 0.2)
    hi = np.maximum(fen, 0.8 * contre)
    rgb = rgb * (1 - hi[..., None]) + BLANC[None, None] * hi[..., None]
    a = np.maximum(a, 0.99 * fen)
    a = np.maximum(a, 0.85 * contre)
    disque = (r < 0.985).astype(float)
    # calque _e : reflets blancs nets + liseré rose fin au bord (le contour de la bulle se lit la nuit)
    liser = np.exp(-((r - 0.93) / 0.03) ** 2)
    e = (92 * fen + 50 * contre)[..., None] * np.ones(3) + (62 * liser)[..., None] * np.array((1.0, 0.42, 0.74))
    return rgb, a * disque, e * disque[..., None]


def lambeau_f(N, seed):
    """Lambeau de gomme déchiré : goutte allongée aux bords dentelés, bord plus clair."""
    x, y = grille(N, N)
    rng = np.random.default_rng(seed)
    a_ = np.arctan2(y, x)
    bord = 0.62 + 0.10 * np.sin(3 * a_ + rng.uniform(0, 6)) + 0.08 * np.sin(5 * a_ + rng.uniform(0, 6)) + 0.05 * np.sin(9 * a_ + rng.uniform(0, 6))
    d = np.hypot(x / 1.0, y / 0.62) / bord
    m = (d < 1).astype(float)
    k = smooth((d - 0.55) / 0.45)
    rgb = GUM[None, None] * (1 - k[..., None]) + GUM_BORD[None, None] * k[..., None]
    hi = ellipse_tournee(x, y, -0.18, 0.12, 0.22, 0.08, 0.2, 0.3)
    rgb = rgb * (1 - 0.7 * hi[..., None]) + BLANC[None, None] * 0.7 * hi[..., None]
    return rgb, m * (0.88 + 0.10 * k), None


def eclair_f(N):
    """Éclair du pop (additif) : anneau fin rose, 8 traits de « pop » alternés, 4 petites croix menthe."""
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    rose = 0.9 * np.exp(-((r - 0.52) / 0.035) ** 2) + 0.35 * np.exp(-((r - 0.5) / 0.12) ** 2)
    menthe = np.zeros_like(x)
    for k in range(8):
        ak = k * np.pi / 4 + np.pi / 8
        da = np.angle(np.exp(1j * (a - ak)))
        r0, r1 = (0.66, 0.95) if k % 2 == 0 else (0.68, 0.84)
        trait = np.exp(-((r * da) / 0.035) ** 2) * smooth((r - r0) / 0.04) * smooth((r1 - r) / 0.04)
        rose = np.maximum(rose, trait)
    for k in range(4):
        ak = k * np.pi / 2
        cx, cy = 0.74 * math.cos(ak), 0.74 * math.sin(ak)
        u, v = x - cx, y - cy
        croix = np.maximum(np.exp(-(u / 0.02) ** 2) * smooth((0.08 - np.abs(v)) / 0.03),
                           np.exp(-(v / 0.02) ** 2) * smooth((0.08 - np.abs(u)) / 0.03))
        menthe = np.maximum(menthe, croix)
    m = smooth((1 - r) / 0.03)
    return (pal(ROSE_ADD, rose) * 0.95 + pal(MENTHE_ADD, menthe) * 0.95) * m[..., None]


def sol_bulles_f(N):
    """Rond de 16 petites bulles brillantes (trans_)."""
    x, y = grille(N, N)
    rgb = np.zeros(x.shape + (3,))
    a = np.zeros(x.shape)
    e = np.zeros(x.shape)
    n = 16
    for k in range(n):
        ak = k * 2 * np.pi / n + 0.15 * math.sin(3 * k)
        rr = 0.78 + 0.07 * math.sin(2.3 * k)
        R = 0.075 + 0.04 * (0.5 + 0.5 * math.sin(1.7 * k + 1))
        cx, cy = rr * math.cos(ak), rr * math.sin(ak)
        u, v = (x - cx) / R, (y - cy) / R
        rl = np.hypot(u, v)
        m = rl < 0.98
        if not m.any():
            continue
        nz = np.sqrt(np.clip(1 - rl * rl, 0, 1))
        fres = (1 - nz) ** 2
        k_ = smooth((-0.45 * u + 0.62 * v + 0.64 * nz) * 0.6 + 0.45)
        c = GUM_OMB * (1 - k_[..., None]) + GUM * k_[..., None]
        c = c * (1 - 0.5 * fres[..., None]) + GUM_BORD * 0.5 * fres[..., None]
        hi = ellipse_tournee(u, v, -0.35, 0.4, 0.28, 0.18, math.radians(38), 0.15)
        c = c * (1 - hi[..., None]) + BLANC * hi[..., None]
        al = np.maximum(0.66 + 0.28 * fres, hi)
        rgb = np.where(m[..., None], c, rgb)
        a = np.where(m, al, a)
        e = np.where(m, 70 * hi, e)
    return rgb, a, e


def sol_lueur_f(N):
    x, y = grille(N, N)
    r = np.hypot(x, y)
    f = 0.75 * np.exp(-((r - 0.80) / 0.10) ** 2) + 0.25 * np.exp(-((r - 0.80) / 0.22) ** 2)
    return pal(ROSE_ADD, f) * 0.55 * smooth((1 - r) / 0.03)[..., None]


def bullette_f(N=16):
    x, y = grille(N, N)
    r = np.hypot(x, y)
    m = r < 0.9
    rgb = np.zeros(x.shape + (3,))
    k = smooth((r - 0.45) / 0.4)
    c = GUM * (1 - k[..., None]) * 0.0 + GUM * 1.0
    c = c * (1 - 0.5 * k[..., None]) + GUM_BORD * 0.5 * k[..., None]
    hi = ellipse_tournee(x, y, -0.32, 0.34, 0.24, 0.18, 0.6, 0.2)
    c = c * (1 - hi[..., None]) + BLANC * hi[..., None]
    rgb[:] = c
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").resize((N, N), Image.LANCZOS)
    al = np.array(Image.fromarray((m * 255).astype(np.uint8), "L").resize((N, N), Image.LANCZOS)) > 110
    arr = np.zeros((N, N, 4), np.uint8)
    arr[..., :3] = np.array(im)
    arr[..., 3] = al * 255
    arr[~al, :3] = 0
    return arr


# ------------------------------------------------------------------ atlas
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)


def poser(nom, im, x, y, em=None):
    h, w = im.shape[:2]
    assert x + w <= TEX and y + h <= TEX and not tex[y:y + h, x:x + w, 3].any(), nom
    tex[y:y + h, x:x + w] = im
    if em is not None:
        tex_e[y:y + h, x:x + w] = em
    UV[nom] = (x, y, x + w, y + h)


for k, (sd, g, nm) in enumerate(((0.0, G_FORT, "fort0"), (2.1, G_FORT, "fort1"), (4.0, G_DOUX, "doux0"), (5.7, G_DOUX, "doux1"))):
    poser(nm, reduire_add(pal(ROSE_ADD, disque_f(sd)) * g, 64, 64), 64 * k, 0)
poser("bullette", bullette_f(16), 256, 0)
poser("eclair", reduire_add(eclair_f(96), 96, 96), 288, 0)
for k in range(4):
    rgb, a, _ = lambeau_f(32, 40 + k)
    im, _ = reduire_trans(rgb, a, 32, 32)
    poser(f"lam{k}", im, 384 + 32 * k, 0)
for nm, N, (px, py), var in (("grande", 192, (0, 96), 0), ("moyenne", 128, (192, 96), 1), ("petiteA", 64, (320, 96), 2), ("petiteB", 64, (384, 96), 3)):
    rgb, a, e = bulle_f(N, var)
    im, em = reduire_trans(rgb, a, N, N, e)
    poser(nm, im, px, py, em)
rgb, a, e = sol_bulles_f(192)
im, em = reduire_trans(rgb, a, 192, 192, e)
poser("sol_bulles", im, 0, 288, em)
poser("sol_lueur", reduire_add(sol_lueur_f(192), 192, 192), 192, 288)


def b64(arr):
    buf = io.BytesIO()
    Image.fromarray(arr, "RGBA").save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


Image.fromarray(tex, "RGBA").save(f"{NOM}.png", optimize=True)
if AVEC_E:
    Image.fromarray(tex_e, "RGBA").save(f"{NOM}_e.png", optimize=True)


# ------------------------------------------------------------------ géométrie
def nuid():
    return str(_uuid.uuid4())


class G:
    def __init__(self, nom, origin, parent=None, rotation=None):
        assert len(nom) <= 64
        self.nom, self.origin, self.uuid, self.enfants = nom, [round(float(v), 3) for v in origin], nuid(), []
        self.rotation = rotation
        if parent is not None:
            parent.enfants.append(self)

    def json(self):
        d = {"name": self.nom, "origin": self.origin, "uuid": self.uuid,
             "children": [c.json() if isinstance(c, G) else c for c in self.enfants]}
        if self.rotation:
            d["rotation"] = [round(float(v), 3) for v in self.rotation]
        return d


elements = []


def plaque(g, nom, c, w, h, uv, face="south", ep=0.3):
    c = np.asarray(c, float)
    if face in ("south", "north"):
        a, b = c - (w / 2, h / 2, ep / 2), c + (w / 2, h / 2, ep / 2)
    else:
        a, b = c - (w / 2, ep / 2, h / 2), c + (w / 2, ep / 2, h / 2)
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in a], "to": [round(float(v), 3) for v in b],
         "origin": [round(float(v), 3) for v in c], "box_uv": False, "faces": {face: {"uv": [round(float(v), 2) for v in uv], "texture": 0}}}
    elements.append(e)
    g.enfants.append(e["uuid"])


MEMBRES = {m: G(m, (0, 24, 0)) for m in ("head", "body", "right_arm", "left_arm", "right_leg", "left_leg")}

# Lueur de silhouette : membre > aura_z (événements) > etat_z (états) > add_z > ctrl_alpha + cam_…
RECUL = {"tete": 4.5, "corps": 4.0, "bras_d": 3.4, "bras_g": 3.4, "jambe_d": 3.4, "jambe_g": 3.4}
ZONES = {
    "tete": ("head", (0, 28, 0), [((0, 28.2, 0), 8.6, "fort")]),
    "corps": ("body", (0, 18, 0), [((0, 21.5, 0), 6.4, "fort"), ((0, 18, 0), 5.8, "doux"), ((0, 14.5, 0), 5.8, "doux")]),
    "bras_d": ("right_arm", (6, 18, 0), [((6, 21.5, 0), 5.2, "doux"), ((6, 18, 0), 4.8, "doux"), ((6, 14.2, 0), 4.6, "doux")]),
    "bras_g": ("left_arm", (-6, 18, 0), [((-6, 21.5, 0), 5.2, "doux"), ((-6, 18, 0), 4.8, "doux"), ((-6, 14.2, 0), 4.6, "doux")]),
    "jambe_d": ("right_leg", (2, 6, 0), [((2, 10, 0), 4.6, "doux"), ((2, 6, 0), 4.4, "doux"), ((2, 2.2, 0), 4.2, "doux")]),
    "jambe_g": ("left_leg", (-2, 6, 0), [((-2, 10, 0), 4.6, "doux"), ((-2, 6, 0), 4.4, "doux"), ((-2, 2.2, 0), 4.2, "doux")]),
}
AURA, ETAT, ADD, DISQUES, ALPHA, HAUT = {}, {}, {}, [], {}, {}
for z, (m, c, discs) in ZONES.items():
    AURA[z] = G(f"aura_{z}", c, MEMBRES[m])
    ETAT[z] = G(f"etat_{z}", c, AURA[z])
    ADD[z] = G(f"add_{z}", c, ETAT[z])
    ALPHA[z] = G("ctrl_alpha", c, ADD[z])
    for k, (p, R, t) in enumerate(discs):
        g = G(f"cam_{z}{k + 1}", p, ADD[z])
        plaque(g, f"lueur_{z}{k + 1}", (p[0], p[1], p[2] - RECUL[z] - 0.12 * k), 2 * R, 2 * R, UV[f"{t}{(k + len(DISQUES)) % 2}"])
        DISQUES.append(g)
        HAUT[g.uuid] = p[1]

# Grappe de bulles : un groupe cam_ centré sur la nuque (repère du torse) ; z local < 0 = derrière, vu de la caméra.
NC = (0, 27.0, 0)
#          (dx, dy, R, texture, recul, période, instant de l'éclat, lambeaux)
BULLES = [(-5.0, 7.0, 6.2, "grande", 10.0, 20.0, 17.5, 8),
          (6.0, 5.0, 4.2, "moyenne", 10.35, 20.0, 9.5, 6),
          (9.6, -1.8, 2.8, "petiteA", 10.7, 20.0, 2.5, 5),
          (-10.4, -0.8, 3.0, "petiteB", 10.55, 20.0, 13.0, 5),
          (3.0, 11.2, 2.4, "petiteA", 10.85, 20.0, 6.0, 5),
          (-12.6, 6.0, 1.5, "petiteB", 11.0, 10.0, 4.5, 0),
          (11.8, 6.6, 1.6, "petiteA", 11.15, 10.0, 8.0, 0)]
AURA["bulles"] = G("aura_bulles", NC, MEMBRES["body"])
ETAT["bulles"] = G("etat_bulles", NC, AURA["bulles"])
CAMB = G("cam_bulles", NC, ETAT["bulles"])
NAIT, BUL, POP, POPA, LAMS = [], [], [], [], []
for i, (dx, dy, R, t, rc, P, tp, nl) in enumerate(BULLES):
    c = (NC[0] + dx, NC[1] + dy, NC[2] - rc)
    nait = G(f"nait_{i + 1}", c, CAMB)
    bul = G(f"bulle_{i + 1}", c, nait)
    tg = G(f"trans_bulle{i + 1}", c, bul)
    plaque(tg, f"bulle{i + 1}", c, 2 * R, 2 * R, UV[t])
    pop = G(f"pop_{i + 1}", c, CAMB)
    cf = (c[0], c[1], c[2] + 0.25)
    ag = G(f"add_pop{i + 1}", cf, pop)
    al = G("ctrl_alpha", cf, ag)
    plaque(ag, f"eclair{i + 1}", cf, 2.6 * R, 2.6 * R, UV["eclair"])
    lams = []
    if nl:
        tl = G(f"trans_lam{i + 1}", c, pop)
        for j in range(nl):
            th = 2 * math.pi * (j + 0.5 * (i % 2)) / nl + 0.3 * math.sin(3 * j + i)
            lg = G(f"lam{i + 1}_{j + 1}", c, tl)                                   # position et échelle animées
            rg = G(f"lamr{i + 1}_{j + 1}", c, lg, rotation=(0, 0, math.degrees(th)))  # orientation fixe, le long du rayon
            w = R * (0.8 + 0.15 * math.sin(2 * j + i))
            plaque(rg,f"lambeau{i + 1}_{j + 1}", (c[0], c[1], c[2] + 0.12 + 0.02 * j), w, w, UV[f"lam{(i + j) % 4}"])
            lams.append((lg, th))
    NAIT.append(nait); BUL.append(bul); POP.append(ag); POPA.append(al); LAMS.append(lams)

# Sol : rond de bulles trans_ + lueur add_ juste au-dessus ; suit le torse, masqué quand le corps n'est pas debout.
SC = (0, 0.4, 0)
AURA["sol"] = G("aura_sol", SC, MEMBRES["body"])
ETAT["sol"] = G("etat_sol", SC, AURA["sol"])
SOL = G("sol_tourne", SC, ETAT["sol"])
TRANS_S = G("trans_sol", SC, SOL)
plaque(TRANS_S, "sol_bulles", (0, 0.45, 0), 30, 30, UV["sol_bulles"], face="up")
ADD["sol"] = G("add_sol", SC, SOL)
ALPHA["sol"] = G("ctrl_alpha", SC, ADD["sol"])
plaque(ADD["sol"], "sol_lueur", (0, 0.72, 0), 30, 30, UV["sol_lueur"], face="up")

EMITS = []
POINTS = [("tete", (0, 33, 0)), ("tete", (3.8, 31, 1.5)), ("tete", (-3.8, 31, 1.5)),
          ("corps", (2.5, 23, 2.6)), ("corps", (-2.5, 16, 2.6)),
          ("bras_d", (8.4, 23.5, 0)), ("bras_g", (-8.4, 23.5, 0)), ("bras_d", (6.5, 12.5, 0)),
          ("jambe_d", (4.3, 4, 0)), ("jambe_g", (-4.3, 4, 0))]
for k, (z, p) in enumerate(POINTS):
    EMITS.append(G("emit_bullette" + (str(k + 1) if k else ""), p, ETAT[z]))

PART = G("particle_bullette", (0, 0, 0))
plaque(PART, "bullette", (0, 0.75, 0), 0.7, 0.7, UV["bullette"])

outliner = [MEMBRES[m].json() for m in MEMBRES] + [PART.json()]


# ------------------------------------------------------------------ animations
def s(v):
    return v if isinstance(v, str) else str(round(v + 0.0, 4))


def kf(ch, t, x, y, z, interp="linear"):
    return {"channel": ch, "data_points": [{"x": s(x), "y": s(y), "z": s(z)}], "time": round(t, 4), "interpolation": interp}


def piste(A, g, keys):
    A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += keys


def sinus(L, k, ph, amp, base=0.0):
    if amp == 0:
        return base
    return f"{s(base)}+{s(amp)}*math.sin(q.anim_time*{s(360 * k / L)}+{int(ph)})"


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


PH = {z: int(RNG.integers(0, 360)) for z in list(ZONES) + ["sol", "bulles"]}
PHB = [int(RNG.integers(0, 360)) for _ in BULLES]

# --- cycle d'une bulle (temps depuis son dernier éclat : tau, période P)
D_CACHE = 0.7        # cachée après l'éclat
D_TEND = 0.45        # se tend et tremble avant l'éclat
D_POP = 0.32         # éclair
D_LAM = 0.5          # lambeaux


def taille(tau, P, ph):
    """(sx, sy) d'une bulle : renaît à 0,18, gonfle en 3 bouffées, flotte, se tend (1,1), éclate."""
    if tau < D_CACHE:
        return 0.0, 0.0
    fin = P - D_TEND
    if tau >= fin:
        u = (tau - fin) / D_TEND
        g = 1 + 0.10 * u ** 1.5
        tr = 0.035 * u * math.sin(2 * math.pi * 9 * u)
        return g * (1 + tr), g * (1 - tr)
    T_g = min(P - D_CACHE - D_TEND - 1.2, 3.0 * (P / 10))
    u = (tau - D_CACHE) / T_g
    if u < 1:
        n = 3
        step = min(int(u * n), n - 1)
        fr = u * n - step
        g = (step + smooth(fr / 0.45)) / n
        base = 0.18 + 0.82 * g
        # rebond : la bouffée dépasse un peu puis se pose (squash-and-stretch)
        osc = 0.06 * math.sin(math.pi * min(fr / 0.45, 1)) if fr < 0.45 else 0.025 * math.exp(-(fr - 0.45) * 8) * math.sin((fr - 0.45) * 30)
        return base * (1 + osc), base * (1 - osc * 0.8)
    w = 0.03 * math.sin(2 * math.pi * (tau - D_CACHE) / 2.2 + ph)
    return 1 + w, 1 - w


def echantillons(L, extra):
    ts = set(round(i * 0.1, 4) for i in range(int(L * 10) + 1))
    for t in extra:
        for d in (-0.04, -0.02, 0.0, 0.02, 0.06, 0.12, 0.2, 0.32, 0.36, 0.5, 0.52):
            v = round(t + d, 4)
            if 0 <= v <= L:
                ts.add(v)
    return sorted(ts)


def cycle_idle(A, L):
    for i, (dx, dy, R, t, rc, P, tp, nl) in enumerate(BULLES):
        pops = [tp + k * P for k in range(int(L / P)) if tp + k * P < L]
        pops = sorted([p % L for p in pops])
        ts = echantillons(L, pops)
        kb, kp, ka = [], [], []
        for tt in ts:
            tau = (tt - tp) % P
            sx, sy = taille(tau, P, PHB[i])
            kb.append(kf("scale", tt, sx, sy, 1))
            # éclair : s'ouvre de 0,7 à 1,6 en D_POP, puis caché
            if tau < D_POP:
                u = tau / D_POP
                f = 0.7 + 0.9 * u ** 0.5
                kp.append(kf("scale", tt, f, f, 1))
                ka.append(kf("position", tt, -u ** 1.3, 0, 0))
            else:
                kp.append(kf("scale", tt, 0, 0, 1))
                ka.append(kf("position", tt, 0, 0, 0))
        piste(A, BUL[i], kb)
        piste(A, POP[i], kp)
        piste(A, POPA[i], ka)
        for lg, th in LAMS[i]:
            kl = []
            for tt in ts:
                tau = (tt - tp) % P
                if tau < D_LAM:
                    u = tau / D_LAM
                    d = R * (0.45 + 1.15 * (1 - (1 - u) ** 2.5))
                    sc = (1 - u) ** 0.8
                    kl.append(kf("position", tt, d * math.cos(th), d * math.sin(th) - 0.6 * R * u * u, 0))
                    kl.append(kf("scale", tt, sc, sc, 1))
                else:
                    kl.append(kf("position", tt, 0, 0, 0))
                    kl.append(kf("scale", tt, 0, 0, 1))
            piste(A, lg, kl)
    # un seul son : le pop de la grande bulle
    A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
        {"channel": "sound", "data_points": [{"effect": "pop_gomme", "file": ""}], "time": BULLES[0][6]}]}


def cacher_pops(A):
    for i in range(len(BULLES)):
        piste(A, POP[i], [kf("scale", 0, 0, 0, 1)])
        for lg, _ in LAMS[i]:
            piste(A, lg, [kf("scale", 0, 0, 0, 1)])


TAILLES = [0.9, 0.95, 0.85, 0.9, 0.8, 0.75, 0.8]


def etat(nom, L, halo=1.0, souffle=0.035, alpha=-0.15, a_amp=0.08, recul=0.0, sol=1.0, bul=1.0, b_pos=(0, 0, 0), etire=1.0,
         rebond=0.0, k_reb=2, seule=False, kb=1):
    A = {}
    for z in ZONES:
        sc = sinus(L, kb, PH[z], halo * souffle, halo)
        piste(A, ETAT[z], [kf("scale", 0, sc, sc, sc)])
        if recul:
            piste(A, ETAT[z], [kf("position", 0, 0, 0, recul)])
    for z in list(ZONES) + ["sol"]:
        piste(A, ALPHA[z], [kf("position", 0, sinus(L, kb, PH.get(z, 0) + 90, a_amp, alpha), 0, 0)])
    sc = sinus(L, kb, PH["sol"], sol * 0.03, sol)
    piste(A, ETAT["sol"], [kf("scale", 0, sc, 1 if sol else 0, sc)])
    py = sinus(L, k_reb, PH["bulles"], rebond, b_pos[1])
    piste(A, ETAT["bulles"], [kf("position", 0, b_pos[0], py, b_pos[2])])
    if nom == "idle":
        cycle_idle(A, L)
    else:
        cacher_pops(A)
        for i, g in enumerate(BUL):
            base = 0.0 if (seule and i > 0) else bul * TAILLES[i]
            if seule and i == 0:      # bulle de sommeil : respire lentement, sans éclater
                sx = sinus(L, 1, 0, 0.14, 0.68)
                sy = sinus(L, 1, 0, 0.12, 0.66)
                piste(A, g, [kf("scale", 0, sx, sy, 1)])
                continue
            if base == 0:
                piste(A, g, [kf("scale", 0, 0, 0, 1)])
                continue
            k = 1 + (i % 2)
            sx = sinus(L, k, PHB[i], 0.03 * base, base / etire ** 0.5)
            sy = sinus(L, k, PHB[i] + 180, 0.03 * base, base * etire)
            piste(A, g, [kf("scale", 0, sx, sy, 1)])
    return {"uuid": nuid(), "name": nom, "loop": "loop", "override": False, "length": L, "snapping": 24, "selected": nom == "idle",
            "animators": A}


STATES = [
    etat("idle", 20.0, kb=5),                                                                  # respiration de 4 s, cycle des bulles 20 s
    etat("walk", 1.6, recul=0.3, bul=0.85, b_pos=(0, 0, 1.0), rebond=0.25, k_reb=2),
    etat("run", 1.0, alpha=-0.05, a_amp=0.03, recul=0.8, bul=0.75, b_pos=(0, -0.5, 2.6), etire=0.94, rebond=0.35, k_reb=2),
    etat("sneak", 4.0, halo=0.9, alpha=-0.35, sol=0, bul=0.6, b_pos=(0, -2.0, 1.0)),
    etat("fly", 2.4, alpha=-0.1, recul=0.4, bul=0.95, b_pos=(0, 0.6, 1.2), etire=1.06, rebond=0.4, k_reb=1),
    etat("glide", 3.6, alpha=-0.15, sol=0, bul=0.55),
    etat("swim", 3.6, alpha=-0.3, sol=0, bul=0.5),
    etat("fall", 2.0, halo=1.04, alpha=-0.1, sol=0.8, bul=0.95, b_pos=(0, 1.0, 0), etire=1.12),
    etat("mount", 4.0, alpha=-0.25, sol=0, bul=0.85, rebond=0.2, k_reb=2),
    etat("sleep", 4.0, halo=0.85, souffle=0.02, alpha=-0.8, a_amp=0.05, sol=0, seule=True),
]

# event_equip : le sol s'ouvre, la lueur monte, puis les bulles naissent l'une après l'autre en « plop » ; un son.
LE = 1.4
TE = [round(j * LE / 28, 4) for j in range(29)]
A = {}
for g in DISQUES:
    t0 = 0.05 + (HAUT[g.uuid] / 33) * 0.45
    piste(A, g, [kf("scale", t, *([sm(t, t0, t0 + 0.35)] * 3)) for t in TE])
piste(A, AURA["sol"], [kf("scale", t, *([sm(t, 0.0, 0.4) * (1 + 0.12 * bump(t, 0.3, 0.4, 0.45, 0.7))] * 3)) for t in TE])
ORDRE = [0, 1, 3, 2, 4, 5, 6]
for r_, i in enumerate(ORDRE):
    t0 = 0.4 + 0.11 * r_
    def plop(t, t0=t0):
        u = (t - t0) / 0.42
        if u <= 0:
            return 0.0
        if u >= 1:
            return 1.0
        return 1.25 * math.sin(min(u / 0.45, 1) * math.pi / 2) if u < 0.45 else 1 + 0.25 * math.cos((u - 0.45) / 0.55 * math.pi * 1.5) * (1 - (u - 0.45) / 0.55)
    piste(A, NAIT[i], [kf("scale", t, plop(t), plop(t), 1) for t in TE])
A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "bloup", "file": ""}], "time": 0.38}]}
equip = {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": LE, "snapping": 24, "selected": False, "animators": A}

# event_unequip : les bulles se tendent et disparaissent en cascade, puis la lueur s'éteint (dernière image : tout à 0) ; un pop.
LU = 1.2
TU = [round(j * LU / 24, 4) for j in range(25)]
A = {}
for r_, i in enumerate(reversed(ORDRE)):
    t0 = 0.05 + 0.08 * r_
    piste(A, NAIT[i], [kf("scale", t, *(([(1 + 0.15 * sm(t, t0, t0 + 0.2)) * (1 - sm(t, t0 + 0.2, t0 + 0.26))] * 2) + [1])) for t in TU])
for g in DISQUES:
    piste(A, g, [kf("scale", t, *([1 - sm(t, 0.6, 1.1)] * 3)) for t in TU])
piste(A, AURA["sol"], [kf("scale", t, *([1 - sm(t, 0.7, 1.15)] * 3)) for t in TU])
A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "pop_gomme", "file": ""}], "time": 0.25}]}
unequip = {"uuid": nuid(), "name": "event_unequip", "loop": "once", "override": False, "length": LU, "snapping": 24, "selected": False, "animators": A}

# overlay_bulles : disques et sol qui tournent lentement (un tour en 48 s).
LO = 48.0
A = {}
for j, g in enumerate(DISQUES):
    piste(A, g, [kf("rotation", 0, 0, 0, f"q.anim_time*{s((1 if j % 2 else -1) * 360 / LO)}")])
piste(A, SOL, [kf("rotation", 0, 0, f"q.anim_time*{s(360 / LO)}", 0)])
overlay = {"uuid": nuid(), "name": "overlay_bulles", "loop": "loop", "override": False, "length": LO, "snapping": 24, "selected": False,
           "animators": A}

# Bullette : vacille doucement (échelle), sans rotation pour rester face caméra.
PF = 1.2
pt = [i * PF / 12 for i in range(13)]
p_fall = {"uuid": nuid(), "name": "particle_bullette_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24,
          "selected": False, "animators": {PART.uuid: {"name": PART.nom, "type": "bone", "keyframes":
              [kf("scale", t, 1 + 0.12 * math.sin(2 * math.pi * t / PF), 1 - 0.12 * math.sin(2 * math.pi * t / PF), 1) for t in pt]}}}

ANIMS = STATES + [equip, unequip, overlay, p_fall]
assert len(EMITS) <= 32
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": b64(tex)}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": b64(tex_e)})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
from ambiance import ajouter_ambiance
from reactions import retirer_reactions
from menu_aura import adapter_menu
embarquer_sons(model, {"pop_gomme": "sons/pop_gomme.ogg", "bloup": "sons/bloup.ogg"})
limiter_sons(model)
retirer_reactions(model)
adapter_menu(model)
ajouter_ambiance(model)
if not AVEC_E:
    model["textures"][:] = [t for t in model["textures"] if not os.path.splitext(t["name"])[0].endswith("_e")]
assert len(model["animations"]) <= 32, len(model["animations"])

os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


def ngroupes(n):
    return 1 + sum(ngroupes(c) for c in n.get("children", []) if isinstance(c, dict))


print(len(elements), "cubes ;", sum(ngroupes(n) for n in model["outliner"]), "groupes ; profondeur", max(depth(n) for n in model["outliner"]), ";",
      len(model["animations"]), "anims ;", sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()), "keyframes ;",
      os.path.getsize(OUT) // 1024, "Ko ;", len(EMITS), "emit_")
