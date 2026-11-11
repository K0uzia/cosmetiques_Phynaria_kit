"""Aura abyssale (v3, revue du 2026-11-08) : la marque du chasseur de démons, faite de lumière violette et de traits vert acide.
Design original (ensemble Abyssal, thème Démoniaque, fiche .claude/styles/abyssal.md ; .claude/references/effets/auras.md).
Écrit aura_abyssale.png et .build/aura_abyssale_brut.bbmodel à côté de ce script.

Pourquoi une refonte : la v2 (volutes de fumée trans_ pourpre-noir, liseré vert, gardée dans .build/gen_avant.py) se lisait de jour
comme une tache grise et boueuse autour du joueur, et presque rien à 10 blocs (« les autre nul », 2026-11-08). Leçon de
aura_berenice (« bien ») : ce qui marche, ce sont des traits de lumière nets et fins sur un fond additif doux, une forme forte
derrière la tête, un anneau net au sol, des filets qui montent. Rien de sombre : le noir est invisible en additif.

Design (tout en add_, pas de calque _e, pas de trans_ : un trans_ cacherait l'additif placé derrière lui)
- Halo de silhouette : disques de lumière violette douce, en cam_ reculés derrière chaque partie du corps, vides au centre
  (recette aura_brasier v3 et aura_berenice) : le corps cache le reste, rien ne passe devant le visage.
- Couronne de crocs, derrière la nuque (cam_, recul 7 px) : 11 crocs de lumière vert acide qui partent de derrière la tête et
  se recourbent vers l'extérieur comme les cornes du bandeau, sur une lueur violette ; derrière eux, un cercle brisé en six
  arcs avec ses graduations et six losanges. Les deux couches tournent lentement en sens contraire (un tour en 48 s pour le
  cercle, un balancement de quelques degrés pour les crocs, qui gardent leur sens) et pulsent.
- Veines qui montent : 7 colonnes en camy_ derrière le joueur : lueur violette douce, et une veine vert acide ramifiée comme
  celles des ailes, parcourue d'impulsions de lumière qui montent (film de 8 images, ctrl_uv).
- Sceau au sol : double cercle vert acide, six crochets en croissant, six losanges, filet intérieur et fissures qui partent du
  centre, sur une lueur violette ; tourne lentement ; masqué quand le corps n'est pas debout.
- Braises : particle_braise, éclat vert acide de 0,6 px (un cube de 0,3 px, face south) qui monte et s'éteint, depuis 12 points.

Palette : violet (64, 18, 98) → (168, 92, 214) arrêté au lilas, vert acide (80, 190, 46) → (170, 250, 110) arrêté avant le blanc.
Cumul additif mesuré par .build/cumul.py (cible ≤ 255).

États : idle (respiration 4 s), walk et run (la lumière part vers l'arrière), sneak (contenue), fly, fall (étirée vers le haut),
glide et swim (corps couché : colonnes rentrées, couronne réduite), mount, sleep (presque éteinte). Pas d'attack ni de hurt
(pièce portée). event_equip (2,4 s) : le sceau s'ouvre au sol, la lumière monte des pieds vers la tête, la couronne s'ouvre en
dernier ; un seul son (block.sculk.spread). overlay_abysse : film des veines, rotation du cercle et du sceau, balancement des
crocs, rotation lente des disques. overlay_ambiance ajoutée par tools/ambiance.py.

Fonctions avancées (guide 4 bis, 5 ter, 6.4, 6.5) : add_, cam_, camy_, ctrl_alpha, ctrl_uv, particle_/emit_, overlay_,
event_equip, son, Molang (math.mod, math.floor, math.sin).

Ce qui se juge seulement en jeu (/cosmetique apercu) : le rendu additif réel de jour sur le ciel et de nuit, ctrl_alpha et ctrl_uv
(non simulés : le rendu montre l'image 0 du film à pleine opacité), les overlays (non joués par les rendus d'état), les braises.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "aura_abyssale"
AVEC_E = False      # tout est add_ : pas de calque _e (il doublait l'additif en jeu, leçon aura_berenice)
TEX = 512
SS = 4
RNG = np.random.default_rng(31)

# ------------------------------------------------------------------ palettes additives (intensité 0..1 -> couleur)
VIOLET = [(0.0, (0, 0, 0)), (0.2, (20, 6, 32)), (0.45, (64, 18, 98)), (0.7, (118, 44, 168)), (0.9, (160, 86, 208)), (1.0, (186, 126, 228))]
VERT = [(0.0, (0, 0, 0)), (0.2, (6, 26, 8)), (0.45, (28, 96, 24)), (0.7, (80, 190, 46)), (0.9, (132, 236, 76)), (1.0, (170, 250, 110))]


def pal(stops, f):
    f = np.clip(f, 0, 1)
    xs = [s_[0] for s_ in stops]
    return np.stack([np.interp(f, xs, [s_[1][c] for s_ in stops]) for c in range(3)], axis=-1)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def reduire(fv, fg, W, H, gv, gg, cutout=False):
    """fv : intensité violette, fg : intensité verte (sur-échantillonnées). RGBA W x H, alpha 0/255 ; presque noir = transparent."""
    rgb = pal(VIOLET, fv) * gv + pal(VERT, fg) * gg
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = np.array(im)
    if cutout:
        f = np.maximum(fv, fg)
        a = np.array(Image.fromarray((np.clip(f * 3, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
        arr[..., 3] = a * 255
        arr[~a, :3] = 0
    else:
        lum = arr[..., :3].max(axis=2)
        arr[..., 3] = (lum > 14) * 255
        arr[lum <= 14, :3] = 0
    return arr


def grille(W, H):
    n_w, n_h = W * SS, H * SS
    return np.meshgrid((np.arange(n_w) + 0.5) / n_w * 2 - 1, 1 - (np.arange(n_h) + 0.5) / n_h * 2)


def trait(x, y, pts, w0, w1, glow=3.5):
    """Trait le long d'une polyligne échantillonnée (pts : N x 2), largeur w0 -> w1 ; renvoie (cœur, lueur, t du point le plus proche)."""
    best = np.full(x.shape, 1e9)
    gl = np.full(x.shape, 1e9)
    tt = np.zeros(x.shape)
    n = len(pts)
    for i, (px, py) in enumerate(pts):
        t = i / (n - 1)
        w = w0 + (w1 - w0) * t
        d = np.hypot(x - px, y - py)
        q = d / w
        m = q < best
        best = np.where(m, q, best)
        tt = np.where(m, t, tt)
        gl = np.minimum(gl, d / (w0 * glow))
    return np.exp(-best ** 2), np.exp(-gl ** 2), tt


def losange(x, y, cx, cy, R, rot=0.0):
    u, v = x - cx, y - cy
    c, s_ = math.cos(rot), math.sin(rot)
    u, v = u * c + v * s_, -u * s_ + v * c
    d = np.abs(u) / R + np.abs(v) / (R * 1.7)
    return np.clip((1 - d) / 0.25, 0, 1)


CORE = 0.42
G_FORT, G_DOUX = 0.62, 0.46        # disques violets (cumul mesuré)
G_CV, G_CG = 0.45, 0.85            # couronne : lueur violette, crocs verts
G_RV, G_RG = 0.45, 0.72            # cercle brisé
G_SV, G_SG = 0.26, 0.85            # sceau
G_LV, G_LG = 0.55, 0.75            # colonnes : lueur, veine


def disque_f(seed, N=64):
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    wob = 1 + 0.05 * np.sin(5 * a + seed) + 0.035 * np.sin(9 * a + 2.3 * seed)
    s_ = np.clip((r / wob - CORE) / (0.97 - CORE), 0, 1)
    f = (1 - s_) ** 1.7 * 0.95 * smooth(r / wob / CORE) ** 1.3
    return f * smooth((1 - r) / 0.06)


R0 = 0.50            # début des crocs : juste au-delà du cercle brisé (r 6,6 px), qui les relie à la tête


def couronne_f(N):
    """Crocs recourbés vers l'extérieur, plus longs en haut, sur la moitié haute (et un peu au-delà) ; lueur violette."""
    x, y = grille(N, N)
    fg = np.zeros_like(x)
    fv = np.zeros_like(x)
    n = 11
    for k in range(n):
        ak = math.radians(-14 + k * (208 / (n - 1)))
        haut = math.sin(ak)                                    # -0.37 .. 1
        L = (0.76 + 0.22 * max(haut, 0) ** 1.3) * (0.86 if k % 2 else 1.0)
        sens = 1 if math.cos(ak) > 0.05 else (-1 if math.cos(ak) < -0.05 else 0)
        hook = 0.42 * sens * (1 - 0.5 * max(haut, 0))       # la pointe se redresse vers le haut : la lumière monte
        pts = []
        for i in range(44):
            t = i / 43
            rr = R0 + (L - R0) * t
            aa = ak + hook * t ** 2.2
            pts.append((rr * math.cos(aa), rr * math.sin(aa)))
        c, g, tt = trait(x, y, pts, 0.034 if k % 2 == 0 else 0.028, 0.004, glow=4.0)
        c = c * smooth((np.hypot(x, y) - R0) / 0.08) * (1 - 0.35 * tt)
        fg = np.maximum(fg, c)
        fv = np.maximum(fv, 0.55 * g * (1 - 0.6 * tt))
    r = np.hypot(x, y)
    fv = np.maximum(fv, 0.22 * np.exp(-((r - R0) / 0.16) ** 2) * smooth(r / R0) ** 2)
    return fv * smooth((1 - r) / 0.03), fg * smooth((1 - r) / 0.03)


def cercle_f(N):
    """Cercle brisé en six arcs, graduations et six losanges ; lueur violette."""
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    a6 = np.mod(a, np.pi / 3) / (np.pi / 3)                  # 0..1 dans chaque sixième
    arc = smooth((a6 - 0.06) / 0.03) * smooth((0.94 - a6) / 0.03)
    fg = np.exp(-((r - 0.44) / 0.012) ** 2) * arc
    fg = np.maximum(fg, 0.75 * np.exp(-((r - 0.405) / 0.006) ** 2) * arc)
    a24 = np.mod(a + np.pi / 24, np.pi / 12) - np.pi / 24     # 24 graduations
    tick = np.exp(-(r * a24 / 0.008) ** 2) * (r > 0.46) * (r < 0.52) * smooth((0.52 - r) / 0.02)
    fg = np.maximum(fg, 0.8 * tick * arc)
    for k in range(6):
        ak = k * np.pi / 3
        fg = np.maximum(fg, losange(x, y, 0.54 * math.cos(ak), 0.54 * math.sin(ak), 0.032, ak))
    fv = 0.45 * np.exp(-((r - 0.44) / 0.10) ** 2)
    return fv * smooth((1 - r) / 0.03), fg * smooth((1 - r) / 0.03)


def sceau_f(N):
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    fil = lambda rr, w: np.exp(-((r - rr) / w) ** 2)
    fg = np.maximum.reduce([fil(0.93, 0.010), 0.8 * fil(0.875, 0.006), 0.7 * fil(0.56, 0.006)])
    for k in range(6):
        ak = k * np.pi / 3 + np.pi / 6
        cx, cy = 0.72 * math.cos(ak), 0.72 * math.sin(ak)
        # croissant : disque moins un disque décalé vers l'extérieur (crochet ouvert vers l'extérieur)
        d1 = np.hypot(x - cx, y - cy)
        d2 = np.hypot(x - (cx + 0.035 * math.cos(ak)), y - (cy + 0.035 * math.sin(ak)))
        cr = smooth((0.085 - d1) / 0.012) * smooth((d2 - 0.075) / 0.012)
        fg = np.maximum(fg, cr)
        ab = ak + np.pi / 6
        fg = np.maximum(fg, losange(x, y, 0.72 * math.cos(ab), 0.72 * math.sin(ab), 0.03, ab))
        # fissure qui part du filet intérieur vers le centre (cachée sous les pieds au centre)
        pts = []
        for i in range(24):
            t = i / 23
            rr = 0.56 - 0.30 * t
            pts.append((rr * math.cos(ak + 0.12 * math.sin(7 * t + k)), rr * math.sin(ak + 0.12 * math.sin(7 * t + k))))
        c, _, _ = trait(x, y, pts, 0.016, 0.004)
        fg = np.maximum(fg, 0.85 * c)
    fv = 0.30 * smooth((r - 0.50) / 0.08) * smooth((0.96 - r) / 0.05) + 0.25 * fil(0.74, 0.14)
    m = smooth((1 - r) / 0.03)
    return fv * m, np.clip(fg, 0, 1) * m * (r > 0.20)


FR = 8


def colonne_f(W, H, seed, k):
    """Image k : lueur violette fine et fixe ; veine vert acide ramifiée, parcourue d'impulsions qui montent d'un tiers de
    hauteur sur FR images (période 1/3 : film fermé)."""
    x, y = grille(W, H)
    Y = (y + 1) / 2
    sig = 0.42 * (1 - Y) ** 0.6 + 0.14
    env = np.exp(-(x / sig) ** 2 * 1.6) * smooth(Y / 0.30) ** 0.8 * (1 - Y) ** 1.1
    env *= smooth((1 - np.abs(x)) / 0.15)
    rng = np.random.default_rng(int(seed * 100))
    pts = [(0.16 * math.sin(3.0 * t * math.pi + seed) * (1 - 0.5 * t), -0.85 + 1.7 * t) for t in np.linspace(0, 1, 40)]
    c, _, _ = trait(x, y, pts, 0.16, 0.07, glow=2.0)
    for (tb, cote) in ((0.35, 1), (0.6, -1)):
        bx, by = pts[int(tb * 39)]
        br = [(bx + cote * 0.5 * t, by + 0.55 * t + 0.08 * math.sin(5 * t + seed)) for t in np.linspace(0, 1, 16)]
        cb, _, _ = trait(x, y, br, 0.12, 0.05, glow=2.0)
        c = np.maximum(c, 0.85 * cb * smooth((y - by) / 0.05))
    ph = k / FR / 3
    pulse = 0.30 + 0.70 * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * (Y - ph))) ** 3
    vein = c * pulse * smooth(Y / 0.18) * smooth((1 - Y) / 0.25)
    return env * 0.9, vein


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
poser("doux0", reduire(disque_f(4.0), Z0, 64, 64, G_DOUX, 0), 128, 0)
poser("doux1", reduire(disque_f(5.7), Z0, 64, 64, G_DOUX, 0), 192, 0)
xb, yb = grille(16, 16)
braise = losange(xb, yb, 0, 0, 0.55) ** 0.8
poser("braise", reduire(braise * 0.5, braise, 16, 16, 0.6, 1.0, cutout=True), 256, 0)
CV, CG = couronne_f(192)
poser("couronne", reduire(CV, CG, 192, 192, G_CV, G_CG), 0, 64)
RV, RGc = cercle_f(192)
poser("cercle", reduire(RV, RGc, 192, 192, G_RV, G_RG), 192, 64)
SV, SG = sceau_f(128)
poser("sceau", reduire(SV, SG, 128, 128, G_SV, G_SG), 384, 64)
COL = {"A": (16, 128), "B": (12, 112)}
for (v, (w, h)), (x0, y0) in zip(COL.items(), ((0, 256), (128, 384))):
    for k in range(FR):
        fv, fg = colonne_f(w, h, 1.3 + 2.0 * (v == "B"), k)
        poser(f"col{v}{k}", reduire(fv, fg, w, h, G_LV, G_LG), x0 + k * w, y0)

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

# Hiérarchie d'une zone : membre > aura_z (event) > etat_z (états) > add_z > ctrl_alpha + cam_…
RECUL = {"tete": 4.5, "corps": 4.0, "bras_d": 3.4, "bras_g": 3.4, "jambe_d": 3.4, "jambe_g": 3.4}
ZONES = {   # zone : membre, centre, [(centre du disque, rayon, texture)]
    "tete": ("head", (0, 28, 0), [((0, 28.2, 0), 9.0, "fort")]),
    "corps": ("body", (0, 18, 0), [((0, 21.5, 0), 6.6, "fort"), ((0, 18, 0), 6.0, "doux"), ((0, 14.5, 0), 6.0, "doux")]),
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

# Couronne de crocs : centre derrière la nuque (repère de la tête) ; cercle brisé derrière, crocs devant.
GC = (0, 27.0, 0)
GR = 7.0
AURA["couronne"] = G("aura_couronne", GC, MEMBRES["head"])
ETAT["couronne"] = G("etat_couronne", GC, AURA["couronne"])
CAMG = G("cam_couronne", GC, ETAT["couronne"])
ADD["couronne"] = G("add_couronne", GC, CAMG)
ALPHA["couronne"] = G("ctrl_alpha", GC, ADD["couronne"])
TOURNE = {}
for nom, uvn, taille, dz in (("crocs", "couronne", 32, 0.0), ("cercle", "cercle", 30, 0.25)):
    g = G(f"tourne_{nom}", (GC[0], GC[1], GC[2] - GR - dz), ADD["couronne"])
    plaque(g, nom, (GC[0], GC[1], GC[2] - GR - dz), taille, taille, UV[uvn])
    TOURNE[nom] = g

# Colonnes : repère camy_ centré sur le torse ; z < 0 = derrière le joueur vu de la caméra.
FLUX_C = (0, 14, 0)
AURA["flux"] = G("aura_flux", FLUX_C, MEMBRES["body"])
ETAT["flux"] = G("etat_flux", FLUX_C, AURA["flux"])
MONTE = G("monte_flux", (0, 0, 0), ETAT["flux"])          # pivot au sol : la lumière s'allume en montant (event_equip)
CAMY = G("camy_flux", FLUX_C, MONTE)
ADD["flux"] = G("add_flux", FLUX_C, CAMY)
ALPHA["flux"] = G("ctrl_alpha", FLUX_C, ADD["flux"])
COLONNES = [  # (x, z, base y, hauteur, largeur, type)
    (0.0, -4.8, 17.0, 26.0, 7.0, "A"),
    (-4.8, -4.3, 12.0, 24.0, 6.0, "A"), (4.8, -4.45, 12.5, 23.0, 6.0, "A"),
    (-8.2, -3.7, 5.0, 22.0, 5.0, "B"), (8.2, -3.85, 4.5, 23.0, 5.0, "B"),
    (-6.0, -3.0, -0.5, 16.0, 3.6, "B"), (6.0, -3.15, -0.5, 15.0, 3.6, "B"),
]
COLS = []
for i, (x, zz, y0, h, w, t) in enumerate(COLONNES):
    base = (x, y0, zz)
    g = G(f"col{i}", base, ADD["flux"])
    plaque(g, f"veine{i}", (x, y0 + h / 2, zz), w, h, UV[f"col{t}0"])
    COLS.append((g, G("ctrl_uv", base, g), t, i))

# Sol : sceau à plat (additif) ; suit le torse, masqué quand le corps n'est pas debout.
SC = (0, 0.4, 0)
AURA["sol"] = G("aura_sol", SC, MEMBRES["body"])
ETAT["sol"] = G("etat_sol", SC, AURA["sol"])
SOL = G("sol_tourne", SC, ETAT["sol"])
ADD["sol"] = G("add_sol", SC, SOL)
ALPHA["sol"] = G("ctrl_alpha", SC, ADD["sol"])
plaque(ADD["sol"], "sceau", (0, 0.55, 0), 30, 30, UV["sceau"], face="up")

EMITS = []
BRAISES = [("tete", (0, 33, 0)), ("tete", (3.8, 31, 1.5)), ("tete", (-3.8, 31, 1.5)),
           ("corps", (2.5, 23, 2.6)), ("corps", (-2.5, 16, 2.6)),
           ("bras_d", (8.4, 23.5, 0)), ("bras_d", (6.5, 12.5, 0)), ("bras_g", (-8.4, 23.5, 0)), ("bras_g", (-6.5, 12.5, 0)),
           ("jambe_d", (4.3, 4, 0)), ("jambe_g", (-4.3, 4, 0)), ("jambe_d", (2, 1, 2.5))]
for k, (z, p) in enumerate(BRAISES):
    EMITS.append(G("emit_braise" + (str(k + 1) if k else ""), p, ETAT[z]))

PART = G("particle_braise", (0, 0, 0))
plaque(PART, "braise", (0, 0.75, 0), 0.6, 0.6, UV["braise"])

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


PH = {z: int(RNG.integers(0, 360)) for z in list(ZONES) + ["flux", "sol", "couronne"]}
PH_C = [(int(RNG.integers(0, 360)), int(RNG.integers(0, 360))) for _ in COLS]


def etat(nom, L, haut=1.0, larg=1.0, vac=0.06, halo=1.0, souffle=0.035, alpha=-0.15, a_amp=0.08, flux=(0, 0, 0), recul=0.0,
         sol=1.0, gl=1.0, g_alpha=0.0, g_recul=0.0, kv=2, kb=1):
    """haut/larg : colonnes ; vac : vacillement ; halo/souffle : disques ; alpha/a_amp : opacité (ctrl_alpha) ; flux : décalage
    des colonnes (+Z vers l'arrière) ; recul : halo vers l'arrière ; sol : sceau (0 masqué) ; gl, g_alpha, g_recul : couronne."""
    A = {}
    for z in ZONES:
        sc = sinus(L, kb, PH[z], halo * souffle, halo)
        piste(A, ETAT[z], [kf("scale", 0, sc, sc, sc)])
        if recul:
            piste(A, ETAT[z], [kf("position", 0, 0, 0, recul)])
    for z in list(ZONES) + ["flux", "sol"]:
        piste(A, ALPHA[z], [kf("position", 0, sinus(L, kb, PH.get(z, 0) + 90, a_amp, alpha), 0, 0)])
    sg = sinus(L, kb, PH["couronne"], gl * 0.03, gl)
    piste(A, ETAT["couronne"], [kf("scale", 0, sg, sg, sg)])
    if g_recul:
        piste(A, ETAT["couronne"], [kf("position", 0, 0, 0, g_recul)])
    piste(A, ALPHA["couronne"], [kf("position", 0, sinus(L, kb, PH["couronne"] + 90, 0.08, alpha * 0.5 + g_alpha), 0, 0)])
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
    etat("sneak", 4.0, haut=0, larg=0, halo=0.9, alpha=-0.35, flux=(0, -3.5, 1.5), sol=0, gl=0.8, g_alpha=-0.15, kv=1),
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


# event_equip : le sceau s'ouvre au sol, la lumière monte des pieds vers la tête, la couronne s'ouvre en dernier ; un son.
LE = 2.4
TE = [j * LE / 24 for j in range(25)]
A = {}
for g in DISQUES:
    t0 = 0.35 + (HAUT[g.uuid] / 33) * 0.9
    piste(A, g, [kf("scale", t, *([sm(t, t0, t0 + 0.5) * (1 + 0.12 * bump(t, t0 + 0.3, t0 + 0.5, t0 + 0.6, t0 + 1.0))] * 3)) for t in TE])
piste(A, MONTE, [kf("scale", t, 1, sm(t, 0.4, 1.5), 1) for t in TE])
piste(A, AURA["sol"], [kf("scale", t, *([sm(t, 0.0, 0.6) * (1 + 0.12 * bump(t, 0.4, 0.6, 0.7, 1.1))] * 3)) for t in TE])
piste(A, AURA["couronne"], [kf("scale", t, *([sm(t, 1.2, 1.7) * (1 + 0.14 * bump(t, 1.5, 1.7, 1.8, 2.3))] * 3)) for t in TE])
A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "block.sculk.spread", "file": ""}], "time": 0.1}]}
equip = {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": LE, "snapping": 24, "selected": False, "animators": A}

# overlay_abysse : film des veines, cercle et sceau qui tournent (un tour en 48 s), crocs qui se balancent, disques qui tournent.
LO = 48.0
A = {}
for (g, uvg, t, i) in COLS:
    w = COL[t][0]
    fps = 4 + (i % 3)                                 # 192, 240 ou 288 images par boucle : film fermé (multiple de FR)
    piste(A, uvg, [kf("position", 0, f"math.floor(math.mod(q.anim_time*{fps}+{i * 3},{FR}))*{w}", 0, 0)])
for j, g in enumerate(DISQUES):
    piste(A, g, [kf("rotation", 0, 0, 0, f"q.anim_time*{s((1 if j % 2 else -1) * 360 / LO)}")])
pul = f"1+0.05*math.sin(q.anim_time*{s(360 * 6 / LO)})"
piste(A, TOURNE["crocs"], [kf("rotation", 0, 0, 0, f"4*math.sin(q.anim_time*{s(360 * 4 / LO)})"), kf("scale", 0, pul, pul, 1)])
pul2 = f"1+0.04*math.sin(q.anim_time*{s(360 * 6 / LO)}+120)"
piste(A, TOURNE["cercle"], [kf("rotation", 0, 0, 0, f"q.anim_time*{s(-360 / LO)}"), kf("scale", 0, pul2, pul2, 1)])
piste(A, SOL, [kf("rotation", 0, 0, f"q.anim_time*{s(360 / LO)}", 0)])
overlay = {"uuid": nuid(), "name": "overlay_abysse", "loop": "loop", "override": False, "length": LO, "snapping": 24, "selected": False,
           "animators": A}

# Braise : vacille doucement (échelle), sans rotation pour rester face caméra.
PF = 1.2
pt = [i * PF / 12 for i in range(13)]
p_fall = {"uuid": nuid(), "name": "particle_braise_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24,
          "selected": False, "animators": {PART.uuid: {"name": PART.nom, "type": "bone", "keyframes":
              [kf("scale", t, *([1 + 0.2 * math.sin(2 * math.pi * t / PF)] * 3)) for t in pt]}}}

ANIMS = STATES + [equip, overlay, p_fall]
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
if not AVEC_E:      # ajouter_ambiance crée un calque _e s'il manque : retiré (il doublait l'additif en jeu)
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
