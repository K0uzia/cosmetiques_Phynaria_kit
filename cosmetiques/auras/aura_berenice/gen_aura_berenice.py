"""Aura de Bérénice : une lumière sacrée, blanche et dorée, qui enveloppe le joueur et s'élève. Design original (ensemble Bérénice,
thème Divin, fiche .claude/styles/berenice.md). Écrit aura_berenice.png, aura_berenice_e.png et .build/aura_berenice_brut.bbmodel.

Refus précédents (retours-en-jeu.md) : objets en orbite (« pas une aura », c'était l'ancienne version à 7 plumes), langues de feu
(« mec en feu »), plaques croisées dans les membres (« horriblement moche »). Base technique : aura_brasier v3 (« ok » en jeu
sans shader) : disques add_ en cam_ reculés derrière chaque partie du corps, colonnes add_ en camy_, anneau au sol.

Design
- Halo de silhouette : disques de lumière douce (noir au bord, or, cœur blanc chaud), chacun dans un groupe cam_ reculé derrière
  sa partie du corps et vide au centre : le corps cache le reste, rien ne passe devant le visage. Plus forts derrière la tête et
  les épaules, plus doux sur les jambes.
- Gloire : deux plaques de rayons fins et droits (« cheveux d'or » de la Chevelure de Bérénice) dans un groupe cam_ centré
  derrière la nuque, reculé de 7 px : 48 rayons longs et courts, dont 8 finis par une petite étoile à quatre branches, et 12
  rayons plus longs et plus fins par-dessus. Les deux couches tournent en sens contraire, très lentement (un tour en 48 s),
  et pulsent (8 s). Doublée par une gloire trans_ très discrète (alpha 20 à 95), pour qu'il reste des rayons avec shader.
- Colonnes : 7 colonnes fines de lumière qui montent (film de 8 images parcouru par ctrl_uv), dans un groupe camy_ derrière le
  joueur, plus calmes que le brasier (5 à 7 images/s, vacillement faible).
- Sol : anneau doré découpé (double filet, 8 étoiles à quatre branches, points de constellation, filet pointillé intérieur), qui
  tourne lentement ; doublé en trans_ ; masqué quand le corps n'est pas debout.
- Poussière d'étoiles : particule modélisée particle_etoile (un seul cube de 0,3 px, face south seule) depuis 12 points, et
  emit_mc_end_rod (4 points), rares, qui montent. Aucune particule qui tombe et se pose.
- Menu Apparence (pas de caméra) : q.is_in_menu cache les groupes cam_/camy_ et montre une gloire fixe derrière le dos, face
  au menu. Textures additives transparentes là où elles sont presque noires.

États : idle (respiration 4 s), walk et run (la lumière part vers l'arrière), sneak (contenue), fly, fall (s'élève), glide et swim
(corps couché : colonnes rentrées, gloire réduite, reste le halo), mount, sleep (presque éteinte), attack (éclat bref, once
0,8 s), hurt (vacille, once 0,8 s), event_equip (la lumière s'allume des pieds vers la tête, 2,4 s, son embarqué lueur_celeste, sons/lueur_celeste.py).
overlay_lumiere : film des colonnes, rotation des rayons, des disques et de l'anneau, pulsation de la gloire.
overlay_ambiance ajoutée par tools/ambiance.py.

Retour en jeu du 2026-11-04 (captures 21.37) : tête dans un disque blanc saturé, rayons et anneau blancs, grande étoile à 3 blocs.
Corrigé : plus de calque _e (il doublait l'additif), palette arrêtée à l'or clair, gains baissés (cumul additif mesuré < 255),
anneau plus fin, étoile de 0,6 px (réglage Élan 100 %, durée 2 s).

Fonctions avancées (guide 4 bis, 5 ter, 6.3, 6.4, 6.5) : add_, trans_, cam_, camy_, ctrl_alpha, ctrl_uv, particle_/emit_,
emit_mc_end_rod, overlay_, event_equip (pas de calque _e), son, Molang (math.mod, math.floor, math.sin, q.is_in_menu).

Ce qui se juge seulement en jeu (/cosmetique apercu) : le rendu additif réel (de jour sur le ciel), ctrl_alpha et ctrl_uv (non
simulés : le rendu montre l'image 0 du film à pleine opacité), les overlays (non joués par les rendus d'état), la gloire trans_
avec shader, les particules, le menu Apparence (q.is_in_menu non simulé).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "aura_berenice"
CACHER_MENU = False   # menu Apparence : True = ancien contournement (groupes cachés par q.is_in_menu, remplacement menu_seul) ;
                      # False = aura montrée, cam_/camy_ tournés vers la caméra du menu (tools/menu_aura.py, mod 1.4.0, 2026-11-05)
AVEC_E = False      # retour en jeu du 2026-11-04 : le calque _e s'ajoutait une seconde fois à l'additif (blanc saturé). Tout est add_ ou trans_ : pas de _e.
TEX = 512
SS = 4
E_GAIN = 0.4
RNG = np.random.default_rng(11)

# ------------------------------------------------------------------ palette « Lumière divine » (intensité 0..1 -> couleur additive)
# Retour en jeu du 2026-11-04 : « disque blanc saturé » autour de la tête. Les couches additives s'additionnent : la palette
# s'arrête à l'or clair (le bleu reste bas, rien ne tourne au blanc) et les gains sont choisis pour que le cumul mesuré reste
# sous 235 (mesure sans écrêtage, vue de face, de dos et de 3/4).
STOPS = [(0.0, (0, 0, 0)), (0.15, (30, 20, 6)), (0.35, (95, 66, 22)), (0.6, (180, 130, 50)),
         (0.85, (235, 198, 124)), (1.0, (250, 226, 168))]


def palette(f):
    f = np.clip(f, 0, 1)
    xs = [s[0] for s in STOPS]
    return np.stack([np.interp(f, xs, [s[1][c] for s in STOPS]) for c in range(3)], axis=-1)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def reduire(f, W, H, gain, cutout=False):
    """f : intensité sur-échantillonnée. Image RGBA W x H, alpha 0/255 ; le presque noir est transparent (menu Apparence)."""
    rgb = palette(f) * gain
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = np.array(im)
    if cutout:
        a = np.array(Image.fromarray((np.clip(f * 3, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
        arr[..., 3] = a * 255
        arr[~a, :3] = 0
    else:
        lum = arr[..., :3].max(axis=2)
        arr[..., 3] = (lum > 16) * 255
        arr[lum <= 16, :3] = 0
    return arr


def reduire_trans(f, W, H, a_max, couleur=(240, 196, 108)):
    """Version trans_ : couleur dorée unie, opacité 1..254 selon l'intensité (0 sous le seuil)."""
    a = np.array(Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = couleur
    al = np.where(a > 0.08, np.clip(a * a_max, 1, 254), 0)
    arr[..., 3] = al.astype(np.uint8)
    arr[al == 0, :3] = 0
    return arr


def grille(W, H):
    n_w, n_h = W * SS, H * SS
    return np.meshgrid((np.arange(n_w) + 0.5) / n_w * 2 - 1, 1 - (np.arange(n_h) + 0.5) / n_h * 2)


CORE = 0.42
G_FORT, G_DOUX, G_RAYA, G_RAYB, G_SOL, G_COL = 0.34, 0.24, 0.62, 0.50, 0.50, 0.42     # gains additifs (cumul < 235)


def disque_f(seed, N=64):
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    wob = 1 + 0.04 * np.sin(5 * a + seed) + 0.03 * np.sin(9 * a + 2.3 * seed)
    s = np.clip((r / wob - CORE) / (0.97 - CORE), 0, 1)
    f = (1 - s) ** 1.9 * 0.95 * smooth(r / wob / CORE) ** 1.3
    return f * smooth((1 - r) / 0.06)


def etoile4(x, y, cx, cy, R, w=0.18):
    """Étoile à quatre branches (astroïde adoucie) de rayon R centrée en (cx, cy)."""
    u, v = (x - cx) / R, (y - cy) / R
    d = np.abs(u) ** 0.5 + np.abs(v) ** 0.5
    return np.clip((1.0 - d) / w, 0, 1) ** 0.8


R0 = 0.30            # début des rayons (caché par la tête)


def rayons_f(N, n, longs, larg, seed, etoiles=0, lueur=0.30):
    """Gloire : n rayons fins et droits (largeur constante, effilés au bout), longueurs alternées ; lueur douce au centre."""
    rng = np.random.default_rng(seed)
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    f = np.zeros_like(r)
    pas = 2 * np.pi / n
    for k in range(n):
        ak = k * pas + pas / 2 * (seed % 2)
        L = longs[k % len(longs)] * rng.uniform(0.93, 1.0)
        d = np.abs(r * np.sin(a - ak))                         # distance perpendiculaire à la droite du rayon
        le_long = r * np.cos(a - ak)
        t = np.clip((le_long - R0) / (L - R0), 0, 1)
        w = larg * (1 - 0.65 * t)
        ray = np.exp(-(d / w) ** 2) * smooth((le_long - R0) / 0.12) * (1 - t) ** 0.55 * (le_long > 0)
        f = np.maximum(f, ray * (0.95 - 0.25 * t))
        if etoiles and k % (n // etoiles) == 0:
            f = np.maximum(f, etoile4(x, y, L * 0.98 * np.cos(ak), L * 0.98 * np.sin(ak), 0.075))
    f = np.maximum(f, lueur * np.exp(-((r - R0) / 0.22) ** 2) * smooth(r / R0) ** 2)
    return f * smooth((1 - r) / 0.03)


def anneau_f(N, avec_lueur=True):
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    fil = lambda rr, w: np.exp(-((r - rr) / w) ** 2)
    f = np.maximum.reduce([fil(0.93, 0.008), 0.8 * fil(0.885, 0.005), 0.7 * fil(0.60, 0.005)])
    # étoiles à quatre branches, alternées grandes et petites, et points de constellation entre elles
    for k in range(8):
        ak = k * np.pi / 4
        R = 0.06 if k % 2 == 0 else 0.04
        f = np.maximum(f, etoile4(x, y, 0.74 * np.cos(ak), 0.74 * np.sin(ak), R))
        if k % 2 == 0:                                       # constellation : deux points entre une grande et une petite étoile
            for dr, da in ((0.05, 0.27), (-0.04, 0.50)):
                px, py = (0.74 + dr) * np.cos(ak + da), (0.74 + dr) * np.sin(ak + da)
                f = np.maximum(f, 0.8 * np.exp(-(np.hypot(x - px, y - py) / 0.018) ** 2))
    if avec_lueur:
        f = np.maximum(f, 0.07 * np.exp(-((r - 0.74) / 0.16) ** 2))
    return np.clip(f, 0, 1) * smooth((1 - r) / 0.03) * (r > 0.45)


FR = 8


def colonne_f(W, H, seed, k):
    """Image k du film : enveloppe fixe fine, filets clairs qui montent d'une demi-hauteur sur FR images (film fermé)."""
    x, y = grille(W, H)
    Y = (y + 1) / 2
    ph = k / FR * 0.5
    sig = 0.48 * (1 - Y) ** 0.6 + 0.16
    env = np.exp(-(x / sig) ** 2 * 1.5) * smooth(Y / 0.35) ** 0.8 * (1 - Y) ** 1.2
    env *= smooth((1 - np.abs(x)) / 0.15)
    tr = 0.5 + 0.5 * np.sin(2 * np.pi * (2 * (Y - ph) + 0.15 * np.sin(2.1 * x + seed)))
    return env * (0.78 + 0.22 * tr)


UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)


def poser(nom, im, x, y):
    h, w = im.shape[:2]
    assert x + w <= TEX and y + h <= TEX and not tex[y:y + h, x:x + w, 3].any(), nom
    tex[y:y + h, x:x + w] = im
    UV[nom] = (x, y, x + w, y + h)


poser("fort0", reduire(disque_f(0.0), 64, 64, G_FORT), 0, 0)
poser("fort1", reduire(disque_f(2.1), 64, 64, G_FORT), 64, 0)
poser("doux0", reduire(disque_f(4.0), 64, 64, G_DOUX), 128, 0)
poser("doux1", reduire(disque_f(5.7), 64, 64, G_DOUX), 192, 0)
poser("etoile", reduire(etoile4(*grille(16, 16), 0, 0, 1.0, 0.25) * 0.85, 16, 16, 0.9, cutout=True), 256, 0)
RA = rayons_f(192, 48, (1.0, 0.62, 0.82, 0.62), 0.011, 1, etoiles=8, lueur=0.10)
RB = rayons_f(192, 12, (1.0,), 0.008, 2, lueur=0.0)
poser("rayonsA", reduire(RA, 192, 192, G_RAYA), 0, 64)
poser("rayonsB", reduire(RB, 192, 192, G_RAYB), 192, 64)
poser("anneau", reduire(anneau_f(128), 128, 128, G_SOL), 384, 64)
poser("rayonsT", reduire_trans(np.maximum(RA, RB * 0.8), 192, 192, 85), 0, 256)
poser("anneauT", reduire_trans(anneau_f(128, avec_lueur=False), 128, 128, 100), 192, 256)
COL = {"A": (16, 128), "B": (12, 112)}
for (v, (w, h)), (x0, y0) in zip(COL.items(), ((320, 256), (192, 384))):
    for k in range(FR):
        poser(f"col{v}{k}", reduire(colonne_f(w, h, 1.3 + 2.0 * (v == "B"), k) * 0.8, w, h, G_COL), x0 + k * w, y0)

tex_e = tex.copy()
tex_e[..., :3] = (tex[..., :3].astype(np.float32) * E_GAIN).astype(np.uint8)
_b64 = []
for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(fn, optimize=True)
    _buf = io.BytesIO()
    im_.save(_buf, "PNG", optimize=True)
    _b64.append("data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode())
tex_b64, tex_e_b64 = _b64


# ------------------------------------------------------------------ géométrie
def nuid():
    return str(_uuid.uuid4())


class G:
    tous = []

    def __init__(self, nom, origin, parent=None):
        assert len(nom) <= 64
        self.nom, self.origin, self.uuid, self.enfants = nom, [round(float(v), 3) for v in origin], nuid(), []
        if parent is not None:
            parent.enfants.append(self)
        G.tous.append(self)

    def json(self):
        return {"name": self.nom, "origin": self.origin, "uuid": self.uuid,
                "children": [c.json() if isinstance(c, G) else c for c in self.enfants]}


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

# Hiérarchie d'une zone : membre > aura_z (attack, hurt, event) > menu_z (caché dans le menu) > etat_z (états) > add_z > cam_…
RECUL = {"tete": 4.5, "corps": 4.0, "bras_d": 3.4, "bras_g": 3.4, "jambe_d": 3.4, "jambe_g": 3.4}
ZONES = {   # zone : membre, centre, [(centre du disque, rayon, texture)]
    "tete": ("head", (0, 28, 0), [((0, 28.2, 0), 10.0, "fort")]),
    "corps": ("body", (0, 18, 0), [((0, 21.5, 0), 6.6, "fort"), ((0, 18, 0), 6.0, "doux"), ((0, 14.5, 0), 6.0, "doux")]),
    "bras_d": ("right_arm", (6, 18, 0), [((6, 21.5, 0), 5.6, "doux"), ((6, 18, 0), 5.0, "doux"), ((6, 14.2, 0), 4.8, "doux")]),
    "bras_g": ("left_arm", (-6, 18, 0), [((-6, 21.5, 0), 5.6, "doux"), ((-6, 18, 0), 5.0, "doux"), ((-6, 14.2, 0), 4.8, "doux")]),
    "jambe_d": ("right_leg", (2, 6, 0), [((2, 10, 0), 5.0, "doux"), ((2, 6, 0), 4.8, "doux"), ((2, 2.2, 0), 4.6, "doux")]),
    "jambe_g": ("left_leg", (-2, 6, 0), [((-2, 10, 0), 5.0, "doux"), ((-2, 6, 0), 4.8, "doux"), ((-2, 2.2, 0), 4.6, "doux")]),
}
AURA, MENU, ETAT, ADD, DISQUES, ALPHA, HAUT = {}, {}, {}, {}, [], {}, {}
for z, (m, c, discs) in ZONES.items():
    AURA[z] = G(f"aura_{z}", c, MEMBRES[m])
    MENU[z] = G(f"menu_{z}", c, AURA[z])
    ETAT[z] = G(f"etat_{z}", c, MENU[z])
    ADD[z] = G(f"add_{z}", c, ETAT[z])
    ALPHA[z] = G("ctrl_alpha", c, ADD[z])
    for k, (p, R, t) in enumerate(discs):
        g = G(f"cam_{z}{k + 1}", p, ADD[z])
        plaque(g, f"lueur_{z}{k + 1}", (p[0], p[1], p[2] - RECUL[z] - 0.12 * k), 2 * R, 2 * R, UV[f"{t}{(k + len(DISQUES)) % 2}"])
        DISQUES.append(g)
        HAUT[g.uuid] = p[1]

# Gloire : centre derrière la nuque (repère de la tête), deux couches de rayons additifs et une couche trans_ discrète.
GC = (0, 26.5, 0)
GR = 7.0
AURA["gloire"] = G("aura_gloire", GC, MEMBRES["head"])
MENU["gloire"] = G("menu_gloire", GC, AURA["gloire"])
ETAT["gloire"] = G("etat_gloire", GC, MENU["gloire"])
CAMG = G("cam_gloire", GC, ETAT["gloire"])
ADD["gloire"] = G("add_gloire", GC, CAMG)
ALPHA["gloire"] = G("ctrl_alpha", GC, ADD["gloire"])
TOURNE = []
for nom, uvn, taille, dz, parent in (("rayons_or", "rayonsA", 34, 0.0, ADD["gloire"]), ("rayons_fins", "rayonsB", 38, 0.15, ADD["gloire"])):
    g = G(f"tourne_{nom}", (GC[0], GC[1], GC[2] - GR - dz), parent)
    plaque(g, nom, (GC[0], GC[1], GC[2] - GR - dz), taille, taille, UV[uvn])
    TOURNE.append(g)
TRANS_G = G("trans_gloire", GC, CAMG)
ALPHA["gloire_t"] = G("ctrl_alpha", GC, TRANS_G)
g = G("tourne_rayons_voile", (GC[0], GC[1], GC[2] - GR - 0.3), TRANS_G)
plaque(g, "rayons_voile", (GC[0], GC[1], GC[2] - GR - 0.3), 36, 36, UV["rayonsT"])
TOURNE.append(g)

# Gloire du menu Apparence (sans caméra) : fixe derrière le dos, face nord (vers l'avant du personnage) ; visible dans le menu seul.
MENU_SEUL = G("menu_seul", (0, 26.5, 5.5), MEMBRES["body"])
ADD_MENU = G("add_gloire_menu", (0, 26.5, 5.5), MENU_SEUL)
plaque(ADD_MENU, "rayons_menu", (0, 26.5, 5.5), 30, 30, UV["rayonsA"], face="north")

# Colonnes : repère camy_ centré sur le torse ; z < 0 = derrière le joueur vu de la caméra.
FLUX_C = (0, 14, 0)
AURA["flux"] = G("aura_flux", FLUX_C, MEMBRES["body"])
MENU["flux"] = G("menu_flux", FLUX_C, AURA["flux"])
ETAT["flux"] = G("etat_flux", FLUX_C, MENU["flux"])
MONTE = G("monte_flux", (0, 0, 0), ETAT["flux"])          # pivot au sol : la lumière s'allume en montant (event_equip)
CAMY = G("camy_flux", FLUX_C, MONTE)
ADD["flux"] = G("add_flux", FLUX_C, CAMY)
ALPHA["flux"] = G("ctrl_alpha", FLUX_C, ADD["flux"])
COLONNES = [  # (x, z, base y, hauteur, largeur, type)
    (0.0, -4.8, 18.0, 28.0, 7.5, "A"),
    (-4.6, -4.3, 13.0, 25.0, 6.0, "A"), (4.6, -4.45, 13.5, 24.0, 6.0, "A"),
    (-8.0, -3.7, 6.0, 22.0, 5.0, "B"), (8.0, -3.85, 5.5, 23.0, 5.0, "B"),
    (-6.0, -3.0, -0.5, 16.0, 3.5, "B"), (6.0, -3.15, -0.5, 15.0, 3.5, "B"),
]
COLS = []
for i, (x, zz, y0, h, w, t) in enumerate(COLONNES):
    base = (x, y0, zz)
    g = G(f"col{i}", base, ADD["flux"])
    plaque(g, f"colonne{i}", (x, y0 + h / 2, zz), w, h, UV[f"col{t}0"])
    COLS.append((g, G("ctrl_uv", base, g), t, i))

# Sol : anneau doré à plat (additif) et son double trans_ dessous ; suit le torse, masqué quand le corps n'est pas debout.
SC = (0, 0.4, 0)
AURA["sol"] = G("aura_sol", SC, MEMBRES["body"])
ETAT["sol"] = G("etat_sol", SC, AURA["sol"])
SOL = G("sol_tourne", SC, ETAT["sol"])
ADD["sol"] = G("add_sol", SC, SOL)
ALPHA["sol"] = G("ctrl_alpha", SC, ADD["sol"])
plaque(ADD["sol"], "anneau", (0, 0.65, 0), 28, 28, UV["anneau"], face="up")
TRANS_S = G("trans_sol", SC, SOL)
ALPHA["sol_t"] = G("ctrl_alpha", SC, TRANS_S)
plaque(TRANS_S, "anneau_voile", (0, 0.35, 0), 28, 28, UV["anneauT"], face="up")

# Points de départ (+Y du groupe = vers le haut).
EMITS = []


def emit(nom, p, parent):
    EMITS.append(G(nom, p, parent))


ETOILES = [("tete", (0, 33, 0)), ("tete", (3.6, 31, 1.5)), ("tete", (-3.6, 31, 1.5)),
           ("corps", (2.5, 23, 2.6)), ("corps", (-2.5, 16, 2.6)),
           ("bras_d", (8.4, 23.5, 0)), ("bras_d", (6.5, 12.5, 0)), ("bras_g", (-8.4, 23.5, 0)), ("bras_g", (-6.5, 12.5, 0)),
           ("jambe_d", (4.3, 4, 0)), ("jambe_g", (-4.3, 4, 0)), ("jambe_d", (2, 1, 2.5))]
for k, (z, p) in enumerate(ETOILES):
    emit("emit_etoile" + (str(k + 1) if k else ""), p, ETAT[z])
# emit_mc_end_rod retiré (2026-11-04, 21.49) : grosses étoiles vanilla de taille fixe qui dérivaient à 2-3 blocs.

# Particule : étoile à quatre branches, un seul cube de 0,3 px, face south seule (réglage conseillé : Face caméra).
PART = G("particle_etoile", (0, 0, 0))
plaque(PART, "etoile", (0, 0.75, 0), 0.6, 0.6, UV["etoile"])

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


CACHE_MENU = "1-q.is_in_menu"
MONTRE_MENU = "q.is_in_menu"
PH = {z: int(RNG.integers(0, 360)) for z in list(ZONES) + ["flux", "sol", "gloire"]}
PH_C = [(int(RNG.integers(0, 360)), int(RNG.integers(0, 360))) for _ in COLS]


def etat(nom, L, haut=1.0, larg=1.0, vac=0.06, halo=1.0, souffle=0.035, alpha=-0.15, a_amp=0.08, flux=(0, 0, 0), recul=0.0,
         sol=1.0, gl=1.0, g_alpha=0.0, g_recul=0.0, kv=2, kb=1):
    """haut/larg : colonnes ; vac : vacillement ; halo/souffle : disques ; alpha/a_amp : opacité (ctrl_alpha) ; flux : décalage
    des colonnes (+Z vers l'arrière) ; recul : halo vers l'arrière ; sol : anneau (0 masqué) ; gl, g_alpha, g_recul : gloire."""
    A = {}
    for z in ZONES:
        sc = sinus(L, kb, PH[z], halo * souffle, halo)
        piste(A, ETAT[z], [kf("scale", 0, sc, sc, sc)])
        if recul:
            piste(A, ETAT[z], [kf("position", 0, 0, 0, recul)])
    for z in list(ZONES) + ["flux", "sol", "sol_t"]:
        piste(A, ALPHA[z], [kf("position", 0, sinus(L, kb, PH.get(z, 0) + 90, a_amp, alpha), 0, 0)])
    sg = sinus(L, kb, PH["gloire"], gl * 0.03, gl)
    piste(A, ETAT["gloire"], [kf("scale", 0, sg, sg, sg)])
    if g_recul:
        piste(A, ETAT["gloire"], [kf("position", 0, 0, 0, g_recul)])
    for z in ("gloire", "gloire_t"):
        piste(A, ALPHA[z], [kf("position", 0, sinus(L, kb, PH["gloire"] + 90, 0.08, alpha * 0.5 + g_alpha), 0, 0)])
    for z in list(ZONES) + ["flux", "gloire"]:      # menu Apparence : pas de caméra, les groupes cam_/camy_ y sont cachés
        piste(A, MENU[z], [kf("scale", 0, CACHE_MENU, CACHE_MENU, CACHE_MENU)])
    piste(A, MENU_SEUL, [kf("scale", 0, MONTRE_MENU, MONTRE_MENU, MONTRE_MENU)])
    if any(flux):
        piste(A, ETAT["flux"], [kf("position", 0, *flux)])
    for (g, _, t, i), (p1, p2) in zip(COLS, PH_C):
        k1, k2 = kv + (i % 2), kv + 1 + (i % 3)
        sy = f"{s(haut)}*(1+{s(vac)}*math.sin(q.anim_time*{s(360 * k1 / L)}+{p1})+{s(vac * 0.5)}*math.sin(q.anim_time*{s(360 * k2 / L)}+{p2}))"
        sx = sinus(L, k2, p2 + 60, larg * vac * 0.3, larg)
        piste(A, g, [kf("scale", 0, sx, sy, 1)])
    sc = sinus(L, kb, PH["sol"], sol * 0.03, sol)
    piste(A, ETAT["sol"], [kf("scale", 0, sc, 1 if sol else 0, sc)])
    return {"uuid": nuid(), "name": nom, "loop": "loop", "override": False, "length": L, "snapping": 24, "selected": nom == "idle",
            "animators": A}


STATES = [
    etat("idle", 8.0, kv=2, kb=2),                                                               # respiration de 4 s
    etat("walk", 1.6, haut=1.04, flux=(0, 0, 1.5), recul=0.3, g_recul=0.6, kv=1),
    etat("run", 1.0, haut=1.15, larg=0.9, vac=0.08, alpha=-0.05, a_amp=0.03, flux=(0, -0.5, 3.5), recul=0.8, gl=1.05, g_recul=1.6, kv=1),
    etat("sneak", 4.0, haut=0, larg=0, halo=0.9, alpha=-0.35, flux=(0, -3.5, 1.5), sol=0, gl=0.78, g_alpha=-0.15, kv=1),
    etat("fly", 2.4, haut=1.1, larg=0.95, alpha=-0.1, flux=(0, 0, 2.0), recul=0.4, gl=1.05, g_recul=0.8, kv=1),
    etat("glide", 3.6, haut=0, larg=0, alpha=-0.15, sol=0, gl=0.6, g_alpha=-0.2, kv=1),
    etat("swim", 3.6, haut=0, larg=0, alpha=-0.3, sol=0, gl=0.5, g_alpha=-0.3, kv=1),
    etat("fall", 2.0, haut=1.2, larg=0.85, halo=1.04, alpha=-0.1, flux=(0, 1.0, 0), sol=0.8, gl=1.08, kv=1),
    etat("mount", 4.0, haut=0, larg=0, alpha=-0.25, flux=(0, -1.0, 0), sol=0, gl=0.9, kv=1),
    etat("sleep", 4.0, haut=0, larg=0, vac=0.03, halo=0.85, souffle=0.02, alpha=-0.8, a_amp=0.05, sol=0, gl=0.55, g_alpha=-0.35, kv=1),
]


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def ponctuel(nom, f_halo, f_flux, f_gloire, f_alpha, f_pos=None):
    L = 0.8
    T = [j * L / 16 for j in range(17)]
    A = {}
    for g in DISQUES:
        piste(A, g, [kf("scale", t, *([f_halo(t)] * 3)) for t in T])
    if f_pos:
        for z in list(ZONES) + ["gloire"]:
            piste(A, AURA[z], [kf("position", t, *f_pos(t, z)) for t in T])
    piste(A, AURA["flux"], [kf("scale", t, *([f_flux(t)] * 3)) for t in T])
    piste(A, AURA["gloire"], [kf("scale", t, *([f_gloire(t)] * 3)) for t in T])
    for z in list(ZONES) + ["flux", "gloire", "gloire_t"]:
        piste(A, ALPHA[z], [kf("position", t, f_alpha(t), 0, 0) for t in T])
    piste(A, MENU_SEUL, [kf("scale", 0, MONTRE_MENU, MONTRE_MENU, MONTRE_MENU)])   # joué par-dessus l'état : échelles multipliées
    return {"uuid": nuid(), "name": nom, "loop": "once", "override": False, "length": L, "snapping": 24, "selected": False, "animators": A}


attack = ponctuel("attack", lambda t: 1 + 0.22 * bump(t, 0, 0.07, 0.2, 0.7), lambda t: 1 + 0.2 * bump(t, 0, 0.1, 0.25, 0.75),
                  lambda t: 1 + 0.28 * bump(t, 0, 0.06, 0.2, 0.72), lambda t: 0.1 * bump(t, 0, 0.05, 0.2, 0.7))
tremb = lambda t: math.sin(2 * math.pi * t * 6 / 0.8) * (1 - sm(t, 0.05, 0.7))
hurt = ponctuel("hurt", lambda t: 1 - 0.08 * bump(t, 0, 0.05, 0.2, 0.7), lambda t: 1 - 0.12 * bump(t, 0, 0.05, 0.25, 0.75),
                lambda t: 1 - 0.1 * bump(t, 0, 0.05, 0.2, 0.7), lambda t: -0.5 * abs(tremb(t)),
                lambda t, z: (0.4 * tremb(t) * (1 if (list(ZONES) + ["gloire"]).index(z) % 2 else -1), 0, 0))

# event_equip : la lumière s'allume des pieds vers la tête (2,4 s), la gloire s'ouvre en dernier ; un carillon.
LE = 2.4
TE = [j * LE / 24 for j in range(25)]
A = {}
for g in DISQUES:
    t0 = 0.15 + (HAUT[g.uuid] / 33) * 0.9
    piste(A, g, [kf("scale", t, *([sm(t, t0, t0 + 0.5) * (1 + 0.12 * bump(t, t0 + 0.3, t0 + 0.5, t0 + 0.6, t0 + 1.0))] * 3)) for t in TE])
piste(A, MONTE, [kf("scale", t, 1, sm(t, 0.2, 1.4), 1) for t in TE])
piste(A, AURA["sol"], [kf("scale", t, *([sm(t, 0.0, 0.7) * (1 + 0.1 * bump(t, 0.5, 0.7, 0.8, 1.2))] * 3)) for t in TE])
piste(A, AURA["gloire"], [kf("scale", t, *([sm(t, 1.1, 1.7) * (1 + 0.12 * bump(t, 1.5, 1.7, 1.8, 2.3))] * 3)) for t in TE])
piste(A, MENU_SEUL, [kf("scale", 0, MONTRE_MENU, MONTRE_MENU, MONTRE_MENU)])
A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "lueur_celeste", "file": ""}], "time": 0.8}]}
equip = {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": LE, "snapping": 24, "selected": False, "animators": A}

# overlay_lumiere : film des colonnes, rayons qui tournent en sens contraire (un tour en 48 s) et pulsent (8 s), disques et anneau.
LO = 48.0
A = {}
for (g, uvg, t, i) in COLS:
    w = COL[t][0]
    fps = 5 + (i % 3)                                 # 240, 288 ou 336 images par boucle : film fermé (multiple de FR)
    piste(A, uvg, [kf("position", 0, f"math.floor(math.mod(q.anim_time*{fps}+{i * 3},{FR}))*{w}", 0, 0)])
for j, g in enumerate(DISQUES):
    piste(A, g, [kf("rotation", 0, 0, 0, f"q.anim_time*{s((1 if j % 2 else -1) * 360 / LO)}")])
for j, g in enumerate(TOURNE):
    sens = (1, -1, 1)[j]
    pul = f"1+{s(0.04 if j != 1 else 0.06)}*math.sin(q.anim_time*{s(360 * 6 / LO)}+{90 * j})"
    piste(A, g, [kf("rotation", 0, 0, 0, f"q.anim_time*{s(sens * 360 / LO)}"), kf("scale", 0, pul, pul, 1)])
piste(A, SOL, [kf("rotation", 0, 0, f"q.anim_time*{s(360 / LO)}", 0)])
overlay = {"uuid": nuid(), "name": "overlay_lumiere", "loop": "loop", "override": False, "length": LO, "snapping": 24, "selected": False,
           "animators": A}

# Étoile : scintille doucement (échelle), sans rotation pour rester face caméra.
PF = 1.2
pt = [i * PF / 12 for i in range(13)]
p_fall = {"uuid": nuid(), "name": "particle_etoile_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24,
          "selected": False, "animators": {PART.uuid: {"name": PART.nom, "type": "bone", "keyframes":
              [kf("scale", t, *([1 + 0.15 * math.sin(2 * math.pi * t / PF)] * 3)) for t in pt]}}}

ANIMS = STATES + [attack, hurt, equip, overlay, p_fall]
assert len(EMITS) <= 32
assert 20 <= len(elements) <= 150, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
from ambiance import ajouter_ambiance
embarquer_sons(model, {"lueur_celeste": "sons/lueur_celeste.ogg"})   # son original synthétisé (tools/synthe.py)
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
from menu_aura import adapter_menu
# Vue fixe du menu : reculs le long de l'axe de vue (invisibles en vue orthographique) qui écartent les plaques
# rendues coplanaires par cette vue pendant l'idle (mesure sur 8 instants, tools/menu_aura.py).
adapter_menu(model, cacher=CACHER_MENU, recul={"cam_bras_d1": 1.0, "cam_bras_d2": 0.75, "cam_corps1": 0.25})
ajouter_ambiance(model)
if not AVEC_E:      # ajouter_ambiance crée un calque _e s'il manque : retiré (il doublait l'additif en jeu)
    model["textures"][:] = [t for t in model["textures"] if not os.path.splitext(t["name"])[0].endswith("_e")]
    if os.path.exists(f"{NOM}_e.png"):
        os.remove(f"{NOM}_e.png")
assert len(model["animations"]) <= 16, len(model["animations"])

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
