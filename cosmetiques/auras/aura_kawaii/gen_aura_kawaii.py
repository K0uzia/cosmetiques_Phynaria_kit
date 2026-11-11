"""Aura cœur de guimauve (v3, revue du 2026-11-08) : un cœur de sucre rose qui encadre la tête, dans une lumière rose et lavande.
Design original (ensemble Kawaii, thème Mignon, fiche .claude/styles/kawaii.md ; .claude/references/effets/auras.md).
Écrit aura_kawaii.png et .build/aura_kawaii_brut.bbmodel à côté de ce script.

Pourquoi une refonte : la v2 (contour de cœur additif pâle, colonnes et tapis de nuage pastel, gardée dans .build/gen_avant.py)
se lisait comme un anneau blanchâtre autour de la tête et une flaque pâle au sol (« les truc kawaii sont tous bof », « revoir
les aura sauf la bérénice », 2026-11-08). Pastels très clairs : lus blancs (avis familier_kawaii_mochi). Leçon de aura_berenice
(« bien ») et aura_abyssale v3 : une forme forte derrière la tête, des traits de lumière nets, un anneau net au sol, des filets
qui montent ; couleurs franches.

Design
- Cœur de sucre (le motif fort de la pièce) : un gros cœur dodu de 20 px, en sucre translucide rose franc (trans_, alpha
  215-240), bord framboise plus opaque, une grande fenêtre de reflet blanche en haut à gauche et un petit contre-reflet ; dans un
  groupe cam_ reculé de 7 px derrière la nuque : ses deux lobes encadrent la tête, sa pointe se cache derrière le dos. Il bat
  doucement (« toc-toc » toutes les 1,5 s, ±5 %) et se balance de quelques degrés. Le trans_ se lit rose de jour sur le ciel,
  là où un additif blanchit.
- Lumière de sucre : devant le cœur, un add_ doux (cœur de lumière vide au bord, fenêtre de reflet) qui compense l'ombre du
  monde sur le trans_ : de jour il reste rose bonbon (sans lui, framboise sombre), de nuit il brille doucement.
- Liseré de lumière : juste derrière le cœur, un add_ qui fait un filet rose vif collé au bord du cœur et un halo doux autour ;
  le sucre le cache là où il est (passe TRANSLUCENT avant ADDITIVE) : la lumière ne se voit qu'autour du cœur, et de nuit il
  reste un cœur cerné de lumière.
- Gloire de nuage : derrière le cœur, un anneau festonné (10 bosses de nuage) de lumière lavande, avec 8 étincelles kira à
  quatre branches arrondies ; il tourne lentement (un tour en 48 s).
- Halo de silhouette : disques de lumière rose (tête, torse) et lavande (membres), en cam_ reculés derrière chaque partie du corps,
  vides au centre (recette aura_brasier v3 et aura_berenice) : rien ne passe devant le visage.
- Filets qui montent : 7 colonnes en camy_ derrière le joueur, lueur lavande douce où montent de petits cœurs roses (film de
  8 images, ctrl_uv).
- Sol : 8 petits cœurs de sucre (rose et lavande en alternance, trans_) posés en rond, cernés d'un anneau festonné de lumière
  (add_, au-dessus, vide sur les cœurs) ; tourne lentement ; masqué quand le corps n'est pas debout.
- Particules : petit cœur rose (0,6 px) et étincelle lavande (0,5 px) qui montent et fondent (un cube de 0,3 px, face south).

Palette (franche, pas pastel) : rose (232, 64, 138) -> framboise (184, 32, 102), reflet (255, 244, 250) ; lumière rose
(200, 50, 120) -> (255, 150, 200), lavande (110, 70, 210) -> (190, 160, 255). Pas de calque _e : tout ce qui brille est add_
(le guide : _e ne s'ajoute qu'aux parties opaques). Cumul additif mesuré par .build/cumul.py : 280-400 sur les bords où disques du torse et des bras se superposent (aura_berenice,
validée « bien », mesure 340-370 avec le même outil).

États : idle (respiration 4 s), walk et run (la lumière part vers l'arrière), sneak (contenue), fly, fall (étirée), glide et swim
(corps couché : colonnes rentrées, cœur réduit), mount, sleep (presque éteinte). Pas d'attack ni de hurt (pièce portée).
event_equip (2,4 s) : le rond de cœurs s'ouvre au sol, la lumière monte des pieds vers la tête, le cœur apparaît en « plop »
(0 -> 1,25 -> 0,92 -> 1) ; un seul son (block.amethyst_block.chime). event_unequip (1,2 s) : le cœur prend une inspiration puis
se referme, la lumière s'éteint de la tête vers les pieds. overlay_guimauve : film des colonnes, battement et balancement du cœur,
rotation de la gloire, des disques et du sol. overlay_ambiance ajoutée par tools/ambiance.py.

Fonctions avancées (guide 4 bis, 5 ter, 6.4, 6.5) : add_, trans_, cam_, camy_, ctrl_alpha, ctrl_uv, particle_/emit_, overlay_,
event_equip, event_unequip, son, Molang (math.mod, math.floor, math.sin, math.pow).

Ce qui se juge seulement en jeu (/cosmetique apercu) : le rendu additif réel de jour sur le ciel et de nuit, le cœur trans_ de
nuit (éclairé par le monde seulement), ctrl_alpha et ctrl_uv (non simulés : le rendu montre l'image 0 du film), les overlays,
les particules.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "aura_kawaii"
AVEC_E = False
TEX = 512
SS = 4
RNG = np.random.default_rng(17)

# ------------------------------------------------------------------ palettes additives (intensité 0..1 -> couleur)
ROSE = [(0.0, (0, 0, 0)), (0.2, (30, 4, 16)), (0.45, (110, 18, 62)), (0.7, (200, 50, 120)), (0.9, (245, 100, 165)), (1.0, (255, 150, 200))]
LAV = [(0.0, (0, 0, 0)), (0.2, (14, 8, 32)), (0.45, (56, 30, 120)), (0.7, (110, 70, 210)), (0.9, (140, 105, 225)), (1.0, (172, 140, 240))]
# sucre (trans_) : base, clair, bord
SUCRE_ROSE = ((250, 96, 162), (255, 158, 204), (214, 52, 128))
SUCRE_LAV = ((168, 116, 245), (206, 168, 255), (124, 76, 214))
REFLET = (255, 244, 250)


def pal(stops, f):
    f = np.clip(f, 0, 1)
    xs = [s_[0] for s_ in stops]
    return np.stack([np.interp(f, xs, [s_[1][c] for s_ in stops]) for c in range(3)], axis=-1)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def reduire(fr, fl, W, H, gr, gl, cutout=False):
    """fr : intensité rose, fl : intensité lavande (sur-échantillonnées). RGBA W x H, alpha 0/255 ; presque noir = transparent."""
    rgb = pal(ROSE, fr) * gr + pal(LAV, fl) * gl
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = np.array(im)
    if cutout:
        f = np.maximum(fr, fl)
        a = np.array(Image.fromarray((np.clip(f * 3, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
        arr[..., 3] = a * 255
        arr[~a, :3] = 0
    else:
        lum = arr[..., :3].max(axis=2)
        arr[..., 3] = (lum > 14) * 255
        arr[lum <= 14, :3] = 0
    return arr


def grille(W, H, ss=SS):
    n_w, n_h = W * ss, H * ss
    return np.meshgrid((np.arange(n_w) + 0.5) / n_w * 2 - 1, 1 - (np.arange(n_h) + 0.5) / n_h * 2)


# ------------------------------------------------------------------ cœur : profondeur radiale (0 au centre, 1 au bord)
def _dans(X, Y):
    return (X * X + Y * Y - 1) ** 3 - X * X * Y ** 3 <= 0


def coeur_d(X, Y):
    """X, Y en coordonnées du cœur (x ±1,14, y -1..1,23). Renvoie s tel que le point est sur le bord du cœur réduit à s
    (le cœur est étoilé autour de l'origine) : s < 1 dedans."""
    lo, hi = np.full(X.shape, 1e-3), np.full(X.shape, 4.0)
    for _ in range(22):
        mid = (lo + hi) / 2
        ins = _dans(X / mid, Y / mid)
        hi = np.where(ins, mid, hi)
        lo = np.where(ins, lo, mid)
    return hi


def etoile(x, y, cx, cy, R, w=0.16):
    """Étincelle kira à quatre branches arrondies (plus un point rond au centre)."""
    u, v = (x - cx) / R, (y - cy) / R
    b = np.maximum(np.exp(-(u / w) ** 2 - (v / 1.0) ** 2 * 2.2), np.exp(-(v / w) ** 2 - (u / 1.0) ** 2 * 2.2))
    return np.clip(np.maximum(b, np.exp(-(u * u + v * v) / 0.09)), 0, 1)


def sucre(X, Y, cols, rgba=None, reflet=True):
    """Peint un cœur de sucre (rgb 0..255, alpha 0..1) dans rgba (H x W x 4, float) aux coordonnées du cœur X, Y."""
    base, clair, bord = (np.array(c, float) for c in cols)
    d = coeur_d(X, Y)
    a = smooth((1.0 - d) / 0.035)
    # du centre (un peu haut) vers le bord : clair -> base -> bord framboise
    rr = np.hypot(X + 0.05, Y - 0.25)
    t_cl = smooth(1 - rr / 0.75)
    rgb = base + (clair - base) * t_cl[..., None] * 0.8
    t_b = smooth((d - 0.80) / 0.16)
    rgb = rgb + (bord - rgb) * t_b[..., None]
    al = 0.84 + 0.10 * t_b
    if reflet:
        # fenêtre de reflet : ellipse inclinée dans le lobe gauche, et un petit contre-reflet en bas à droite
        c, s_ = math.cos(math.radians(-38)), math.sin(math.radians(-38))
        u, v = X + 0.50, Y - 0.62
        u, v = u * c + v * s_, -u * s_ + v * c
        h = smooth((1 - np.hypot(u / 0.26, v / 0.13)) / 0.18)
        h2 = smooth((1 - np.hypot((X - 0.42) / 0.075, (Y + 0.05) / 0.075)) / 0.3) * 0.85
        h = np.maximum(h, h2)
        rgb = rgb + (np.array(REFLET, float) - rgb) * h[..., None]
        al = al + (0.98 - al) * h
    if rgba is None:
        rgba = np.zeros(X.shape + (4,))
    a = a * al
    m = a > rgba[..., 3]
    rgba[..., :3] = np.where(m[..., None], rgb, rgba[..., :3])
    rgba[..., 3] = np.maximum(rgba[..., 3], a)
    return rgba, d


def vers_png(rgba, W, H):
    """Réduit un RGBA float sur-échantillonné : couleur prémultipliée pour des bords propres ; alpha < 10 -> 0."""
    a = rgba[..., 3]
    pm = np.concatenate([rgba[..., :3] * a[..., None], (a * 255)[..., None]], axis=-1)
    im = np.array(Image.fromarray(np.clip(pm, 0, 255).astype(np.uint8), "RGBA").resize((W, H), Image.LANCZOS)).astype(float)
    out = np.zeros((H, W, 4), np.uint8)
    al = im[..., 3]
    ok = al >= 10
    out[..., :3] = np.where(ok[..., None], np.clip(im[..., :3] / np.maximum(al[..., None], 1) * 255, 0, 255), 0).astype(np.uint8)
    out[..., 3] = np.where(ok, np.clip(al, 10, 254), 0).astype(np.uint8)
    return out


CORE = 0.42
G_FORT, G_DOUX = 0.36, 0.30        # disques (rose, lavande)
G_LIS = 0.60                       # liseré du cœur
G_GL, G_GR = 0.50, 0.55            # gloire : lavande, étincelles roses
G_SL, G_SR = 0.50, 0.60            # sol : nuage lavande, filet rose
G_CL, G_CR = 0.30, 0.50            # colonnes : lueur lavande, cœurs roses

HX = 1.30          # échelle plaque -> coordonnées du cœur
HY0 = 0.12


def disque_f(seed, N=64):
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    wob = 1 + 0.05 * np.abs(np.cos(4 * a + seed)) ** 0.6 + 0.03 * np.sin(9 * a + 2.3 * seed)
    s_ = np.clip((r / wob - CORE) / (0.97 - CORE), 0, 1)
    f = (1 - s_) ** 1.7 * 0.95 * smooth(r / wob / CORE) ** 1.3
    return f * smooth((1 - r) / 0.06)


def coeur_lum_f(N):
    """Lumière de sucre, devant le cœur : un cœur de lumière doux (vide au bord framboise) et la fenêtre de reflet, qui
    compensent l'ombre du monde sur le trans_ (de jour il reste rose bonbon, de nuit il brille doucement)."""
    x, y = grille(N, N)
    X, Y = x * HX, y * HX + HY0
    d = coeur_d(X, Y)
    f = 0.42 * smooth((0.93 - d) / 0.25) * (0.75 + 0.25 * smooth(1 - np.hypot(X + 0.05, Y - 0.25) / 0.8))
    c, s_ = math.cos(math.radians(-38)), math.sin(math.radians(-38))
    u, v = X + 0.50, Y - 0.62
    u, v = u * c + v * s_, -u * s_ + v * c
    h = smooth((1 - np.hypot(u / 0.26, v / 0.13)) / 0.25)
    h2 = smooth((1 - np.hypot((X - 0.42) / 0.075, (Y + 0.05) / 0.075)) / 0.4) * 0.8
    return np.maximum(f, 0.95 * np.maximum(h, h2))


def coeur_tex(N):
    x, y = grille(N, N, 2)
    rgba, _ = sucre(x * HX, y * HX + HY0, SUCRE_ROSE)
    return vers_png(rgba, N, N)


K_LIS = 26.0 / 20.0     # la plaque du liseré (26 px) est plus grande que celle du cœur (20 px)


def lisere_f(N):
    x, y = grille(N, N)
    X, Y = x * HX * K_LIS, y * HX * K_LIS + HY0
    d = coeur_d(X, Y)
    fil = np.exp(-((d - 1.035) / 0.028) ** 2)
    halo = 0.42 * np.exp(-((d - 1.0) / 0.22) ** 2) * (d > 1.0)
    f = np.maximum(fil, halo) * smooth((1 - np.maximum(np.abs(x), np.abs(y))) / 0.06)
    return f


def gloire_f(N):
    """Anneau festonné de nuage (10 bosses) en lavande, 8 étincelles roses-blanches."""
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    nb = 10
    a_l = np.mod(a, 2 * np.pi / nb) - np.pi / nb
    bord = 0.74 + 0.085 * np.sqrt(np.clip(1 - (a_l / (np.pi / nb)) ** 2, 0, 1))    # bosses rondes
    fl = np.exp(-((r - bord) / 0.018) ** 2)
    fl = np.maximum(fl, 0.55 * np.exp(-((r - 0.64) / 0.010) ** 2))
    fl = np.maximum(fl, 0.16 * smooth((r - 0.50) / 0.14) * smooth((bord - r) / 0.03) * (r < bord))
    fr = np.zeros_like(x)
    for k in range(8):
        ak = k * np.pi / 4 + np.pi / 8
        R = 0.085 if k % 2 == 0 else 0.06
        fr = np.maximum(fr, etoile(x, y, 0.93 * math.cos(ak), 0.93 * math.sin(ak), R))
    for k in range(10):            # petits points ronds dans les creux du feston
        ak = (k + 0.5) * 2 * np.pi / nb
        fr = np.maximum(fr, 0.8 * np.exp(-(np.hypot(x - 0.70 * math.cos(ak), y - 0.70 * math.sin(ak)) / 0.018) ** 2))
    m = smooth((1 - r) / 0.03)
    return fr * m, fl * m


SOL_N, SOL_R, SOL_H = 8, 0.76, 0.10


def sol_coeurs():
    """Positions, sens (pointe vers le centre) et couleurs des cœurs du sol."""
    out = []
    for k in range(SOL_N):
        ak = k * 2 * np.pi / SOL_N
        out.append((SOL_R * math.cos(ak), SOL_R * math.sin(ak), ak, SUCRE_ROSE if k % 2 == 0 else SUCRE_LAV))
    return out


def sol_local(x, y, cx, cy, ak):
    nx, ny = math.cos(ak), math.sin(ak)            # vers l'extérieur = haut du cœur
    tx, ty = -ny, nx
    u = (x - cx) * tx + (y - cy) * ty
    v = (x - cx) * nx + (y - cy) * ny
    return -u / SOL_H, v / SOL_H + HY0


def sol_trans(N):
    x, y = grille(N, N, 2)
    rgba = np.zeros(x.shape + (4,))
    for cx, cy, ak, cols in sol_coeurs():
        X, Y = sol_local(x, y, cx, cy, ak)
        sucre(X, Y, cols, rgba)
    return vers_png(rgba, N, N)


def sol_add(N):
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    nb = 12
    a_l = np.mod(a, 2 * np.pi / nb) - np.pi / nb
    bord = 0.88 + 0.07 * np.sqrt(np.clip(1 - (a_l / (np.pi / nb)) ** 2, 0, 1))
    fl = np.exp(-((r - bord) / 0.014) ** 2)
    fl = np.maximum(fl, 0.35 * smooth((r - 0.50) / 0.10) * smooth((bord - r) / 0.04) * (r < bord))
    fr = 0.85 * np.exp(-((r - 0.585) / 0.009) ** 2)
    dmin = np.full(x.shape, 9.0)
    for cx, cy, ak, _ in sol_coeurs():
        X, Y = sol_local(x, y, cx, cy, ak)
        dmin = np.minimum(dmin, coeur_d(X, Y))
    fr = np.maximum(fr, np.exp(-((dmin - 1.08) / 0.07) ** 2))          # filet rose autour de chaque cœur
    vide = smooth((dmin - 1.0) / 0.05)                                    # rien sur le sucre
    m = smooth((1 - r) / 0.03) * (r > 0.22) * vide
    return fr * m, fl * m


FR = 8


def colonne_f(W, H, seed, k):
    """Image k : lueur lavande douce et fixe ; 3 petits cœurs roses qui montent d'un tiers de hauteur sur FR images."""
    x, y = grille(W, H)
    Y = (y + 1) / 2
    sig = 0.42 * (1 - Y) ** 0.6 + 0.14
    env = np.exp(-(x / sig) ** 2 * 1.6) * smooth(Y / 0.30) ** 0.8 * (1 - Y) ** 1.1
    env *= smooth((1 - np.abs(x)) / 0.15)
    fr = np.zeros_like(x)
    asp = 3.8          # rapport hauteur / largeur des plaques (en px, pas en texels) : cœurs non écrasés
    for j in range(3):
        yc = ((j / 3 + k / FR / 3 + 0.1 * seed) % 1.0)
        xc = 0.22 * math.sin(2 * math.pi * (yc * 3) + seed + j)
        hs = 0.48 * (1 - 0.30 * yc)
        X = (x - xc) / hs
        Yh = (y - (2 * yc - 1)) * asp / hs + HY0
        d = coeur_d(X * 1.0, Yh)
        fr = np.maximum(fr, smooth((1.0 - d) / 0.18) * smooth(yc / 0.15) * smooth((1 - yc) / 0.25))
    return fr, env * 0.9


UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)


def poser(nom, im, x, y):
    h, w = im.shape[:2]
    assert x + w <= TEX and y + h <= TEX and not tex[y:y + h, x:x + w, 3].any(), nom
    tex[y:y + h, x:x + w] = im
    UV[nom] = (x, y, x + w, y + h)


Z0 = np.zeros((64 * SS, 64 * SS))
poser("fort0", reduire(disque_f(0.0), Z0, 64, 64, G_FORT, 0), 0, 0)
poser("fort1", reduire(disque_f(2.1), Z0, 64, 64, G_FORT, 0), 64, 0)
poser("doux0", reduire(Z0, disque_f(4.0), 64, 64, 0, G_DOUX), 128, 0)
poser("doux1", reduire(Z0, disque_f(5.7), 64, 64, 0, G_DOUX), 192, 0)
xb, yb = grille(16, 16)
pc = smooth((1.0 - coeur_d(xb * 1.25, yb * 1.25 + HY0)) / 0.1)
poser("p_coeur", reduire(pc, pc * 0.2, 16, 16, 1.0, 0.5, cutout=True), 256, 0)
pe = etoile(xb, yb, 0, 0, 0.9, 0.22)
poser("p_etincelle", reduire(pe * 0.45, pe, 16, 16, 0.6, 1.0, cutout=True), 272, 0)
poser("coeur", coeur_tex(160), 0, 64)
poser("lisere", reduire(lisere_f(176), np.zeros((176 * SS, 176 * SS)), 176, 176, G_LIS, 0), 160, 64)
GRr, GLl = gloire_f(176)
poser("gloire", reduire(GRr, GLl, 176, 176, G_GR, G_GL), 336, 64)
poser("sol_sucre", sol_trans(192), 0, 240)
poser("coeur_lum", reduire(coeur_lum_f(80), np.zeros((80 * SS, 80 * SS)), 80, 80, 0.55, 0), 0, 432)
SRr, SLl = sol_add(192)
poser("sol_lum", reduire(SRr, SLl, 192, 192, G_SR, G_SL), 192, 240)
COL = {"A": (16, 128), "B": (12, 112)}
for (v, (w, h)), (x0, y0) in zip(COL.items(), ((384, 240), (384, 368))):
    for k in range(FR):
        fr_, fl_ = colonne_f(w, h, 1.3 + 2.0 * (v == "B"), k)
        poser(f"col{v}{k}", reduire(fr_, fl_, w, h, G_CR, G_CL), x0 + k * w, y0)

im_ = Image.fromarray(tex, "RGBA")
im_.save(f"{NOM}.png", optimize=True)
_buf = io.BytesIO()
im_.save(_buf, "PNG", optimize=True)
tex_b64 = "data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode()


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

# Hiérarchie d'une zone : membre > aura_z (événements) > etat_z (états) > add_z > ctrl_alpha + cam_…
RECUL = {"tete": 4.5, "corps": 4.0, "bras_d": 3.4, "bras_g": 3.4, "jambe_d": 3.4, "jambe_g": 3.4}
ZONES = {   # zone : membre, centre, [(centre du disque, rayon, texture)]
    "tete": ("head", (0, 28, 0), [((0, 28.2, 0), 7.6, "fort")]),
    "corps": ("body", (0, 18, 0), [((0, 21.5, 0), 6.6, "fort"), ((0, 18, 0), 6.0, "fort"), ((0, 14.5, 0), 6.0, "doux")]),
    "bras_d": ("right_arm", (6, 18, 0), [((6, 21.5, 0), 5.4, "doux"), ((6, 18, 0), 5.0, "doux"), ((6, 14.2, 0), 4.8, "doux")]),
    "bras_g": ("left_arm", (-6, 18, 0), [((-6, 21.5, 0), 5.4, "doux"), ((-6, 18, 0), 5.0, "doux"), ((-6, 14.2, 0), 4.8, "doux")]),
    "jambe_d": ("right_leg", (2, 6, 0), [((2, 10, 0), 5.0, "doux"), ((2, 6, 0), 4.8, "doux"), ((2, 2.2, 0), 4.6, "doux")]),
    "jambe_g": ("left_leg", (-2, 6, 0), [((-2, 10, 0), 5.0, "doux"), ((-2, 6, 0), 4.8, "doux"), ((-2, 2.2, 0), 4.6, "doux")]),
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

# Cœur : centre derrière la nuque (repère de la tête). Vu de la caméra : cœur de sucre (recul 7), liseré (7,25), gloire (7,55).
GC = (0, 28.2, 0)
HC = (0, 29.8, 0)    # centre du cœur, plus haut que la tête : les lobes la dépassent
GR = 7.0
AURA["coeur"] = G("aura_coeur", GC, MEMBRES["head"])
ETAT["coeur"] = G("etat_coeur", GC, AURA["coeur"])
CAMG = G("cam_coeur", GC, ETAT["coeur"])
BAT = G("battement", (HC[0], HC[1] - 1.5, HC[2] - GR), CAMG)          # le cœur bat et se balance autour de son centre
TRANS_C = G("trans_coeur", GC, BAT)
ALPHA["sucre"] = G("ctrl_alpha", GC, TRANS_C)
plaque(TRANS_C, "coeur", (HC[0], HC[1], HC[2] - GR), 20, 20, UV["coeur"])
ADD["coeur"] = G("add_coeur", GC, BAT)
ALPHA["coeur"] = G("ctrl_alpha", GC, ADD["coeur"])
plaque(ADD["coeur"], "lumiere_sucre", (HC[0], HC[1], HC[2] - GR + 0.3), 20, 20, UV["coeur_lum"])
plaque(ADD["coeur"], "lisere", (HC[0], HC[1], HC[2] - GR - 0.25), 26, 26, UV["lisere"])
ADD["gloire"] = G("add_gloire", GC, CAMG)
ALPHA["gloire"] = G("ctrl_alpha", GC, ADD["gloire"])
GLOIRE = G("tourne_gloire", (HC[0], HC[1], HC[2] - GR - 0.55), ADD["gloire"])
plaque(GLOIRE, "gloire", (HC[0], HC[1], HC[2] - GR - 0.55), 35, 35, UV["gloire"])

# Colonnes : repère camy_ centré sur le torse ; z < 0 = derrière le joueur vu de la caméra.
FLUX_C = (0, 14, 0)
AURA["flux"] = G("aura_flux", FLUX_C, MEMBRES["body"])
ETAT["flux"] = G("etat_flux", FLUX_C, AURA["flux"])
MONTE = G("monte_flux", (0, 0, 0), ETAT["flux"])          # pivot au sol : la lumière s'allume en montant (event_equip)
CAMY = G("camy_flux", FLUX_C, MONTE)
ADD["flux"] = G("add_flux", FLUX_C, CAMY)
ALPHA["flux"] = G("ctrl_alpha", FLUX_C, ADD["flux"])
COLONNES = [  # (x, z, base y, hauteur, largeur, type)
    (-5.6, -4.3, 12.0, 22.0, 6.0, "A"), (5.6, -4.45, 12.5, 21.0, 6.0, "A"),
    (-8.6, -3.7, 5.0, 21.0, 5.0, "B"), (8.6, -3.85, 4.5, 22.0, 5.0, "B"),
    (-5.0, -3.0, -0.5, 15.0, 3.6, "B"), (5.0, -3.15, -0.5, 14.0, 3.6, "B"),
    (0.0, -3.4, -0.5, 13.0, 4.0, "B"),
]
COLS = []
for i, (x, zz, y0, h, w, t) in enumerate(COLONNES):
    base = (x, y0, zz)
    g = G(f"col{i}", base, ADD["flux"])
    plaque(g, f"filet{i}", (x, y0 + h / 2, zz), w, h, UV[f"col{t}0"])
    COLS.append((g, G("ctrl_uv", base, g), t, i))

# Sol : cœurs de sucre (trans_) et, au-dessus, anneau de lumière vide sur les cœurs (add_) ; masqué quand le corps n'est pas debout.
SC = (0, 0.4, 0)
AURA["sol"] = G("aura_sol", SC, MEMBRES["body"])
ETAT["sol"] = G("etat_sol", SC, AURA["sol"])
SOL = G("sol_tourne", SC, ETAT["sol"])
TRANS_S = G("trans_sol", SC, SOL)
ALPHA["sol_sucre"] = G("ctrl_alpha", SC, TRANS_S)
plaque(TRANS_S, "sol_sucre", (0, 0.45, 0), 30, 30, UV["sol_sucre"], face="up")
ADD["sol"] = G("add_sol", SC, SOL)
ALPHA["sol"] = G("ctrl_alpha", SC, ADD["sol"])
plaque(ADD["sol"], "sol_lum", (0, 0.72, 0), 30, 30, UV["sol_lum"], face="up")

EMITS = []
POINTS = [("tete", (0, 33, 0), "coeur"), ("tete", (3.8, 31, 1.5), "etincelle"), ("tete", (-3.8, 31, 1.5), "coeur"),
          ("corps", (2.5, 23, 2.6), "etincelle"), ("corps", (-2.5, 16, 2.6), "coeur"),
          ("bras_d", (8.4, 23.5, 0), "coeur"), ("bras_d", (6.5, 12.5, 0), "etincelle"),
          ("bras_g", (-8.4, 23.5, 0), "etincelle"), ("bras_g", (-6.5, 12.5, 0), "coeur"),
          ("jambe_d", (4.3, 4, 0), "etincelle"), ("jambe_g", (-4.3, 4, 0), "coeur"), ("jambe_d", (2, 1.2, 2.5), "etincelle")]
compte = {}
for z, p, sorte in POINTS:
    n = compte.get(sorte, 0)
    compte[sorte] = n + 1
    EMITS.append(G(f"emit_{sorte}" + (str(n + 1) if n else ""), p, ETAT[z]))

PARTS = {}
for sorte, taille in (("coeur", 0.6), ("etincelle", 0.5)):
    PARTS[sorte] = G(f"particle_{sorte}", (0, 0, 0))
    plaque(PARTS[sorte], sorte, (0, 0.75, 0), taille, taille, UV[f"p_{sorte}"])

outliner = [MEMBRES[m].json() for m in MEMBRES] + [PARTS[s_].json() for s_ in PARTS]


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


PH = {z: int(RNG.integers(0, 360)) for z in list(ZONES) + ["flux", "sol", "coeur"]}
PH_C = [(int(RNG.integers(0, 360)), int(RNG.integers(0, 360))) for _ in COLS]


def etat(nom, L, haut=1.0, larg=1.0, vac=0.06, halo=1.0, souffle=0.035, alpha=-0.15, a_amp=0.08, flux=(0, 0, 0), recul=0.0,
         sol=1.0, gl=1.0, g_alpha=0.0, g_recul=0.0, kv=2, kb=1):
    """haut/larg : colonnes ; vac : vacillement ; halo/souffle : disques ; alpha/a_amp : opacité (ctrl_alpha) ; flux : décalage
    des colonnes (+Z vers l'arrière) ; recul : halo vers l'arrière ; sol : rond de cœurs (0 masqué) ; gl, g_alpha, g_recul : cœur."""
    A = {}
    for z in ZONES:
        sc = sinus(L, kb, PH[z], halo * souffle, halo)
        piste(A, ETAT[z], [kf("scale", 0, sc, sc, sc)])
        if recul:
            piste(A, ETAT[z], [kf("position", 0, 0, 0, recul)])
    for z in list(ZONES) + ["flux", "sol"]:
        piste(A, ALPHA[z], [kf("position", 0, sinus(L, kb, PH.get(z, 0) + 90, a_amp, alpha), 0, 0)])
    sg = sinus(L, kb, PH["coeur"], gl * 0.025, gl)
    piste(A, ETAT["coeur"], [kf("scale", 0, sg, sg, sg)])
    if g_recul:
        piste(A, ETAT["coeur"], [kf("position", 0, 0, 0, g_recul)])
    for z in ("coeur", "gloire"):
        piste(A, ALPHA[z], [kf("position", 0, sinus(L, kb, PH["coeur"] + 90, 0.08, alpha * 0.5 + g_alpha), 0, 0)])
    piste(A, ALPHA["sucre"], [kf("position", 0, s(min(0.0, g_alpha * 0.8)), 0, 0)])
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
    etat("walk", 1.6, haut=1.04, flux=(0, 0, 1.5), recul=0.3, g_recul=0.5, kv=1),
    etat("run", 1.0, haut=1.15, larg=0.9, vac=0.08, alpha=-0.05, a_amp=0.03, flux=(0, -0.5, 3.5), recul=0.8, gl=1.03, g_recul=1.4, kv=1),
    etat("sneak", 4.0, haut=0, larg=0, halo=0.9, alpha=-0.35, flux=(0, -3.5, 1.5), sol=0, gl=0.8, g_alpha=-0.15, kv=1),
    etat("fly", 2.4, haut=1.1, larg=0.95, alpha=-0.1, flux=(0, 0, 2.0), recul=0.4, gl=1.03, g_recul=0.8, kv=1),
    etat("glide", 3.6, haut=0, larg=0, alpha=-0.15, sol=0, gl=0.6, g_alpha=-0.2, kv=1),
    etat("swim", 3.6, haut=0, larg=0, alpha=-0.3, sol=0, gl=0.5, g_alpha=-0.3, kv=1),
    etat("fall", 2.0, haut=1.2, larg=0.85, halo=1.04, alpha=-0.1, flux=(0, 1.0, 0), sol=0.8, gl=1.05, kv=1),
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


def plop(t, t0, d=0.6):
    """Plop de guimauve : 0 -> 1,25 -> 0,92 -> 1,03 -> 1."""
    return float(np.interp((t - t0) / d, [0, 0.4, 0.65, 0.85, 1.0], [0, 1.25, 0.92, 1.03, 1.0]))


# event_equip : le rond de cœurs s'ouvre au sol, la lumière monte des pieds vers la tête, le cœur apparaît en « plop » ; un son.
LE = 2.4
TE = [j * LE / 48 for j in range(49)]
A = {}
for g in DISQUES:
    t0 = 0.35 + (HAUT[g.uuid] / 33) * 0.9
    piste(A, g, [kf("scale", t, *([sm(t, t0, t0 + 0.5) * (1 + 0.12 * bump(t, t0 + 0.3, t0 + 0.5, t0 + 0.6, t0 + 1.0))] * 3)) for t in TE])
piste(A, MONTE, [kf("scale", t, 1, sm(t, 0.4, 1.5), 1) for t in TE])
piste(A, AURA["sol"], [kf("scale", t, *([plop(t, 0.0, 0.7)] * 3)) for t in TE])
piste(A, AURA["coeur"], [kf("scale", t, *([plop(t, 1.35, 0.65)] * 3)) for t in TE])
A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "block.amethyst_block.chime", "file": ""}], "time": 1.45}]}
equip = {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": LE, "snapping": 24, "selected": False, "animators": A}

# event_unequip : le cœur prend une inspiration puis se referme ; la lumière s'éteint de la tête vers les pieds.
LU = 1.2
TU = [j * LU / 24 for j in range(25)]
A = {}
piste(A, AURA["coeur"], [kf("scale", t, *([float(np.interp(t, [0, 0.25, 0.7], [1, 1.12, 0]))] * 3)) for t in TU])
for g in DISQUES:
    t0 = 0.15 + (1 - HAUT[g.uuid] / 33) * 0.5
    piste(A, g, [kf("scale", t, *([1 - sm(t, t0, t0 + 0.35)] * 3)) for t in TU])
piste(A, MONTE, [kf("scale", t, 1, 1 - sm(t, 0.1, 0.8), 1) for t in TU])
piste(A, AURA["sol"], [kf("scale", t, *([float(np.interp(t, [0, 0.7, 0.85, 1.2], [1, 1, 1.08, 0]))] * 3)) for t in TU])
unequip = {"uuid": nuid(), "name": "event_unequip", "loop": "once", "override": False, "length": LU, "snapping": 24, "selected": False,
           "animators": A}

# overlay_guimauve : film des colonnes, cœur qui bat (toc-toc toutes les 1,5 s) et se balance, gloire, disques et sol qui tournent.
LO = 48.0
A = {}
for (g, uvg, t, i) in COLS:
    w = COL[t][0]
    fps = 4 + (i % 3)                                 # 192, 240 ou 288 images par boucle : film fermé (multiple de FR)
    piste(A, uvg, [kf("position", 0, f"math.floor(math.mod(q.anim_time*{fps}+{i * 3},{FR}))*{w}", 0, 0)])
for j, g in enumerate(DISQUES):
    piste(A, g, [kf("rotation", 0, 0, 0, f"q.anim_time*{s((1 if j % 2 else -1) * 360 / LO)}")])
bat = ("1+0.05*math.pow(0.5+0.5*math.sin(q.anim_time*240),14)+0.03*math.pow(0.5+0.5*math.sin(q.anim_time*240-70),14)")
piste(A, BAT, [kf("rotation", 0, 0, 0, f"3*math.sin(q.anim_time*{s(360 * 4 / LO)})"), kf("scale", 0, bat, bat, 1)])
pul2 = f"1+0.03*math.sin(q.anim_time*{s(360 * 6 / LO)}+120)"
piste(A, GLOIRE, [kf("rotation", 0, 0, 0, f"q.anim_time*{s(-360 / LO)}"), kf("scale", 0, pul2, pul2, 1)])
piste(A, SOL, [kf("rotation", 0, 0, f"q.anim_time*{s(360 / LO)}", 0)])
overlay = {"uuid": nuid(), "name": "overlay_guimauve", "loop": "loop", "override": False, "length": LO, "snapping": 24, "selected": False,
           "animators": A}

# Particules : vacillent doucement (échelle), sans rotation pour rester face caméra.
P_ANIMS = []
for sorte, g in PARTS.items():
    PF = 1.2 if sorte == "coeur" else 0.8
    pt = [i * PF / 12 for i in range(13)]
    P_ANIMS.append({"uuid": nuid(), "name": f"particle_{sorte}_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24,
                    "selected": False, "animators": {g.uuid: {"name": g.nom, "type": "bone", "keyframes":
                        [kf("scale", t, *([1 + 0.18 * math.sin(2 * math.pi * t / PF)] * 3)) for t in pt]}}})

ANIMS = STATES + [equip, unequip, overlay] + P_ANIMS
assert len(EMITS) <= 32
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
from ambiance import ajouter_ambiance
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
from menu_aura import adapter_menu
adapter_menu(model)
ajouter_ambiance(model)
if not AVEC_E:      # ajouter_ambiance crée un calque _e s'il manque : retiré (tout ce qui brille est add_)
    model["textures"][:] = [t for t in model["textures"] if not os.path.splitext(t["name"])[0].endswith("_e")]
    if os.path.exists(f"{NOM}_e.png"):
        os.remove(f"{NOM}_e.png")
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
