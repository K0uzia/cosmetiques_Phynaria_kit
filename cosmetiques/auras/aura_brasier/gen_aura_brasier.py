"""Aura du Brasier (version 4, revue du 2026-11-08) : une chaleur de braise qui enveloppe la silhouette et s'élève.
Design original. Écrit aura_brasier.png et .build/aura_brasier_brut.bbmodel à côté de ce script (pas de calque _e).

Demande (2026-11-08) : « revoir les aura sauf la bérénice qui es bien les autre nul ». But : braise et feu nettement plus
beaux et lisibles en jeu, de jour comme de nuit, sans feu à contour sombre ni objet en orbite.
v3 (gardée dans .build/gen_avant.py, avant_livrable.bbmodel) : disques flous rose-rouge et colonnes floues ; en mode « comme en
jeu », de jour, un halo rose délavé sur le ciel, rien qui dise « braise ». Ce qui reste de v3 (validé en jeu : « une fois
équipée, ok ») : la construction (disques add_ en cam_ reculés derrière chaque partie du corps, colonnes add_ en camy_
derrière le joueur, sol à plat). Ce qui change : la matière et le dessin.

Références (fiche .claude/references/effets/braises-chaleur.md, style .claude/styles/brasier.md) : couleur de corps noir des
braises (rouge sombre vers 800 K, orange vers 1 200 K, jaune blanc au plus chaud) ; en VFX, braises qui montent en S, du blanc
or vers l'orange puis le rouge en refroidissant ; chaleur montrée par des filets ondulés (mirage) plutôt que par des langues ;
codes de l'anime pour la chaleur : lignes de mirage au-dessus de la tête, sol qui rougeoie et se fend, braises détachées.

Design
- Liseré de chaleur (recette v3, palette braise) : disques add_ en cam_, reculés derrière tête, torse, bras et jambes. Le
  dégradé est serré : or clair au ras de la silhouette, orange, puis rouge sombre qui s'éteint ; bord haut un peu étiré
  (la chaleur monte). Rien devant le corps.
- Filets de chaleur : 11 colonnes add_ dans un camy_ derrière le joueur. Chaque colonne : un fond rouge très sombre, et 2 ou 3
  filets fins (2 texels) qui ondulent en S et montent (film de 8 images, ctrl_uv). C'est le « mirage » : la distorsion est
  suggérée par les ondulations, pas dessinée.
- Mirage au-dessus de la tête : une plaque add_ en camy_ derrière la tête, des arcs ondulés or pâle qui montent et s'effacent
  (film de 8 images, ctrl_uv).
- Braises : 36 braises modélisées (plaques add_ de 0,8 à 1,2 px dans le camy_, derrière le plan du joueur) qui montent en S
  d'un pied à l'épaule ou de l'épaule au-dessus de la tête, rapetissent et refroidissent (ctrl_uv : or blanc → or → orange →
  rouge). Elles ne tournent pas autour du joueur : elles montent et s'éteignent, puis renaissent en bas (overlay_braises).
  Plus la particule modélisée particle_braise (Monte, Fondu) lâchée par 14 points emit_braise.
- Sol : brûlure sombre trans_ légère (contraste de jour, sinon l'additif se délave sur le sol clair), fissures de braise
  add_ (réseau de Voronoï, traits de 3 texels, fixes, qui respirent) et un anneau de chaleur add_ qui tourne lentement.
- Doubles trans_ orangés discrets : colonnes, disques de la tête et du torse (couleur lisible de jour et sous shader).
  Tous plus loin de la caméra que les add_ (un trans_ cache les add_ qui sont derrière lui).

États : idle (respiration 4 s), walk et run (la chaleur part vers l'arrière, plus haute en course), sneak (contenue, basse),
fly (étirée vers le haut et l'arrière), glide et swim (corps couché : colonnes rentrées, braises réduites), fall (s'étire),
mount (plus bas), sleep (presque éteinte). Pas d'attack ni de hurt (pièce portée). event_equip : le sol se fend et rougeoie
d'abord, puis la chaleur gagne des pieds à la tête, les filets et les braises partent en dernier (2,4 s), un seul son
(crépitement de feu de camp). Aucun son en mouvement ni au repos (boucle de 8 s < 20 s).

Fonctions avancées (guide 4 bis, 5 ter, 6.3, 6.4) : add_, trans_ (sol, doubles), cam_ (disques), camy_ (colonnes, mirage,
braises), ctrl_alpha (respiration, sommeil), ctrl_uv (films, couleur des braises), particle_/emit_, overlay_, event_equip + son,
Molang (math.mod, math.floor, math.sin).
Ce qui se juge seulement en jeu (/cosmetique apercu) : ctrl_uv (aperçus figés sur l'image 0 : braises toutes or blanc, filets
immobiles), ctrl_alpha, l'additif réel de jour, la brûlure du sol sur l'herbe, les particules.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "aura_brasier"
TEX = 512
SS = 4
RNG = np.random.default_rng(11)

# ------------------------------------------------------------------ palette braise (intensité 0..1 -> couleur additive)
# corps noir : rouge sombre -> rouge -> orange -> or -> or blanc (arrêté avant le blanc pur : cumul additif)
STOPS = [(0.0, (0, 0, 0)), (0.12, (40, 6, 0)), (0.30, (120, 22, 4)), (0.50, (205, 60, 8)),
         (0.70, (245, 120, 20)), (0.86, (255, 180, 60)), (1.0, (255, 226, 150))]


def palette(f):
    f = np.clip(f, 0, 1)
    xs = [s_[0] for s_ in STOPS]
    return np.stack([np.interp(f, xs, [s_[1][c] for s_ in STOPS]) for c in range(3)], axis=-1)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def reduire(f, W, H, gain=1.0):
    """Additif : intensité sur-échantillonnée -> image W x H, alpha 255 où il y a de la lumière, 0 sur le noir."""
    rgb = palette(f * gain)
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = np.array(im)
    lum = arr[..., :3].max(axis=2)
    arr[..., 3] = (lum > 14) * 255
    arr[lum <= 14, :3] = 0
    return arr


def reduire_trans(f, W, H, a_max, couleur):
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


# ------------------------------------------------------------------ textures
CORE = 0.44


def disque_f(seed, N=64):
    """Liseré : vide au centre (caché par le membre), or clair au ras du bord du membre, orange, puis rouge qui s'éteint.
    Bord haut étiré (la chaleur monte), bord ondulé."""
    x, y = grille(N, N)
    yy = np.where(y > 0, y / 1.18, y)                 # étiré vers le haut
    r, a = np.hypot(x, yy), np.arctan2(yy, x)
    wob = 1 + 0.06 * np.sin(6 * a + seed) + 0.04 * np.sin(11 * a + 2.3 * seed)
    rr = r / wob
    s = np.clip((rr - CORE) / (0.84 - CORE), 0, 1)
    f = (1 - s) ** 1.7 * 0.95 * smooth(rr / CORE) ** 1.5
    f *= smooth((1 - np.hypot(x, y)) / 0.05)
    return f


FR = 8


def colonne_f(W, H, seed, k):
    """Image k : fond rouge très sombre (enveloppe fine) et 2 ou 3 filets ondulés de 2 texels qui montent d'une demi-hauteur
    sur FR images (film fermé)."""
    x, y = grille(W, H)
    Y = (y + 1) / 2
    ph = k / FR * 0.5
    sig = 0.42 * (1 - Y) ** 0.6 + 0.14
    env = np.exp(-(x / sig) ** 2 * 1.6) * smooth(Y / 0.35) ** 0.8 * (1 - Y) ** 1.0
    env *= smooth((1 - np.abs(x)) / 0.15)
    f = env * 0.17
    larg = 2.2 / W                                    # demi-largeur d'un filet en unités [-1,1] (≈ 2 texels)
    for j, (x0, amp, fq) in enumerate(((-0.28, 0.22, 1.5), (0.22, 0.18, 2.0), (0.0, 0.26, 1.2))[:3 if W > 18 else 2]):
        cx = x0 + amp * np.sin(2 * np.pi * (fq * (Y - ph)) + seed + j * 2.1) * (0.4 + 0.6 * Y)
        fil = np.exp(-((x - cx) / larg) ** 2)
        tirets = smooth((0.5 + 0.5 * np.sin(2 * np.pi * (2 * (Y - ph)) + j * 1.7 + seed) - 0.25) / 0.5)
        f = np.maximum(f, fil * tirets * env ** 0.35 * (0.85 - 0.40 * Y))
    return f


def mirage_f(W, H, k):
    """Arcs ondulés au-dessus de la tête : chaque arc monte d'un tiers de hauteur sur FR images et s'efface en haut."""
    x, y = grille(W, H)
    Y = (y + 1) / 2
    f = np.zeros_like(x)
    for j in range(3):
        y0 = ((j / 3 + k / FR / 3) % 1.0)
        yc = 0.08 + 0.8 * y0 + 0.05 * np.sin(np.pi * 3 * x + j * 1.3 + 4 * y0) + 0.04 * (1 - x ** 2)
        w = 1.3 / H
        arc = np.exp(-((Y - yc) / w) ** 2) * (1 - x ** 2) ** 1.5
        f = np.maximum(f, arc * smooth((1 - y0) / 0.5) * smooth(y0 / 0.15) * 0.42)
    return f * smooth((1 - np.abs(x)) / 0.1)


def voronoi_fissures(N, n=15, seed=3):
    """Fissures de braise : arêtes d'un réseau de Voronoï dans le disque, plus vives au centre ; lueur sombre sous les pieds."""
    rng = np.random.default_rng(seed)
    x, y = grille(N, N)
    r = np.hypot(x, y)
    pts = []
    while len(pts) < n:
        p = rng.uniform(-0.95, 0.95, 2)
        if np.hypot(*p) < 0.9:
            pts.append(p)
    pts.append((0.0, 0.0))
    d = np.stack([np.hypot(x - px, y - py) for px, py in pts])
    d.sort(axis=0)
    e = d[1] - d[0]
    larg = 3.0 / N                                   # ≈ 3 texels
    fis = np.exp(-(e / larg) ** 2)
    f = fis * (0.92 - 0.45 * r) * smooth((0.86 - r) / 0.2)
    f = np.maximum(f, 0.30 * np.exp(-(r / 0.45) ** 2))     # rougeoiement sous les pieds
    return f * smooth((1 - r) / 0.04)


def anneau_f(N):
    """Anneau de chaleur : un trait net, une onde de chaleur dentelée à l'extérieur, des points de braise entre les deux."""
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    fil = lambda rr, w: np.exp(-((r - rr) / w) ** 2)
    f = 0.85 * fil(0.80, 0.022)
    onde = 0.90 + 0.035 * np.sin(14 * a) + 0.012 * np.sin(31 * a + 1)
    f = np.maximum(f, 0.62 * np.exp(-((r - onde) / 0.014) ** 2))
    for k in range(16):
        ak = k * np.pi / 8 + 0.2
        R = 0.022 if k % 2 else 0.032
        f = np.maximum(f, 0.9 * np.exp(-(np.hypot(x - 0.855 * np.cos(ak), y - 0.855 * np.sin(ak)) / R) ** 2))
    f = np.maximum(f, 0.14 * np.exp(-((r - 0.84) / 0.10) ** 2))
    return np.clip(f, 0, 1) * smooth((1 - r) / 0.03)


def brulure_f(N):
    x, y = grille(N, N)
    r = np.hypot(x, y)
    return (1 - smooth((r - 0.45) / 0.5)) * (1 + 0.15 * np.sin(7 * np.arctan2(y, x)) * smooth((r - 0.4) / 0.3))


def braise_f(N, chaud):
    """Une braise : cœur rond net, petit halo ; chaud = intensité du cœur (1 or blanc ... 0.45 rouge)."""
    x, y = grille(N, N)
    r = np.hypot(x, y)
    return chaud * (np.clip(1.25 - r / 0.62, 0, 1) ** 0.6 * (r < 0.75) + 0.0)


UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
TRANS_ZONES = []


def poser(nom, im, x, y, trans=False):
    h, w = im.shape[:2]
    assert x + w <= TEX and y + h <= TEX and not tex[y:y + h, x:x + w, 3].any(), nom
    tex[y:y + h, x:x + w] = im
    UV[nom] = (x, y, x + w, y + h)
    if trans:
        TRANS_ZONES.append((x, y, w, h))


ORANGE_T = (246, 112, 34)
poser("disque0", reduire(disque_f(0.0), 64, 64, 0.95), 0, 0)
poser("disque1", reduire(disque_f(2.1), 64, 64, 0.95), 64, 0)
poser("disqueT", reduire_trans(disque_f(4.0), 64, 64, 90, ORANGE_T), 128, 0, trans=True)
CHAUD = (1.0, 0.86, 0.70, 0.52)                      # or blanc, or, orange, rouge (refroidissement)
for v in range(2):
    for j, c in enumerate(CHAUD):
        poser(f"braise{v}_{j}", reduire(braise_f(8, c * (1 - 0.06 * v)), 8, 8), 192 + j * 8, v * 8)
poser("particule", reduire(braise_f(16, 0.95), 16, 16), 240, 0)
poser("fissures", reduire(voronoi_fissures(128), 128, 128), 0, 64)
poser("anneau", reduire(anneau_f(128), 128, 128), 128, 64)
poser("brulure", reduire_trans(brulure_f(128), 128, 128, 95, (38, 14, 6)), 256, 64, trans=True)
COL = {"A": (24, 120), "B": (16, 120)}
A_COL = 95
for j, (v, (w, h)) in enumerate(COL.items()):
    y0 = 200 + j * 124
    for k in range(FR):
        f = colonne_f(w, h, 1.3 + 2.0 * j, k)
        poser(f"col{v}{k}", reduire(f, w, h), k * w, y0)
        poser(f"colT{v}{k}", reduire_trans(np.clip(f * 1.6, 0, 1), w, h, A_COL, ORANGE_T), 256 + k * w, y0, trans=True)
MW, MH = 64, 32
for k in range(FR):
    poser(f"mirage{k}", reduire(mirage_f(MW, MH, k), MW, MH), k * MW, 448)

_add = np.ones((TEX, TEX), bool)
for (x, y, w, h) in TRANS_ZONES:
    _add[y:y + h, x:x + w] = False
assert set(np.unique(tex[_add, 3])) <= {0, 255}, "semi-transparence hors des trans_"
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
    if face == "south":
        a, b = c - (w / 2, h / 2, ep / 2), c + (w / 2, h / 2, ep / 2)
    else:
        a, b = c - (w / 2, ep / 2, h / 2), c + (w / 2, ep / 2, h / 2)
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in a], "to": [round(float(v), 3) for v in b],
         "origin": [round(float(v), 3) for v in c], "box_uv": False, "faces": {face: {"uv": [round(float(v), 2) for v in uv], "texture": 0}}}
    elements.append(e)
    g.enfants.append(e["uuid"])


MEMBRES = {m: G(m, (0, 24, 0)) for m in ("head", "body", "right_arm", "left_arm", "right_leg", "left_leg")}

# Disques (recette v3 : centres, rayons et reculs gardés, plans écartés de 0,12 px au moins)
ZONES = {
    "tete": ("head", (0, 28, 0), [((0, 28.2, 0), 9.2)]),
    "corps": ("body", (0, 18, 0), [((0, 21.5, 0), 6.0), ((0, 18, 0), 5.8), ((0, 14.5, 0), 5.8)]),
    "bras_d": ("right_arm", (6, 18, 0), [((6, 21.5, 0), 5.0), ((6, 18, 0), 4.8), ((6, 14.2, 0), 4.8)]),
    "bras_g": ("left_arm", (-6, 18, 0), [((-6, 21.5, 0), 5.0), ((-6, 18, 0), 4.8), ((-6, 14.2, 0), 4.8)]),
    "jambe_d": ("right_leg", (2, 6, 0), [((2, 10, 0), 5.0), ((2, 6, 0), 4.8), ((2, 2.2, 0), 4.8)]),
    "jambe_g": ("left_leg", (-2, 6, 0), [((-2, 10, 0), 5.0), ((-2, 6, 0), 4.8), ((-2, 2.2, 0), 4.8)]),
}
RECULS = {"tete": [3.0], "corps": [4.0, 4.13, 4.26], "bras_d": [3.4, 3.53, 3.66], "bras_g": [3.4, 3.53, 3.66],
          "jambe_d": [3.4, 3.53, 3.66], "jambe_g": [3.28, 3.15, 3.78]}
RECULS_T = {"tete": [8.6], "corps": [8.9, 9.02, 9.14]}
DOUBLE_T = ("tete", "corps")
AURA, ETAT, ADD, DISQUES, ALPHA, HAUT = {}, {}, {}, [], {}, {}
for z, (m, c, discs) in ZONES.items():
    AURA[z] = G(f"aura_{z}", c, MEMBRES[m])
    ETAT[z] = G(f"etat_{z}", c, AURA[z])
    ADD[z] = G(f"add_{z}", c, ETAT[z])
    ALPHA[z] = G("ctrl_alpha", c, ADD[z])
    if z in DOUBLE_T:
        TR = G(f"trans_{z}", c, ETAT[z])
        ALPHA[z + "_t"] = G("ctrl_alpha", c, TR)
    for k, (p, R) in enumerate(discs):
        g = G(f"cam_{z}{k + 1}", p, ADD[z])
        plaque(g, f"lueur_{z}{k + 1}", (p[0], p[1], p[2] - RECULS[z][k]), 2 * R, 2 * R, UV[f"disque{(k + len(DISQUES)) % 2}"])
        DISQUES.append(g)
        HAUT[g.uuid] = p[1]
        if z in DOUBLE_T:
            gt = G(f"cam_{z}{k + 1}_t", p, TR)
            plaque(gt, f"voile_{z}{k + 1}", (p[0], p[1], p[2] - RECULS_T[z][k]), 2 * R * 1.1, 2 * R * 1.1, UV["disqueT"])
            DISQUES.append(gt)
            HAUT[gt.uuid] = p[1]

# Colonnes, mirage et braises : un camy_ centré sur le torse ; z < 0 = derrière le joueur vu de la caméra.
FLUX_C = (0, 14, 0)
AURA["flux"] = G("aura_flux", FLUX_C, MEMBRES["body"])
ETAT["flux"] = G("etat_flux", FLUX_C, AURA["flux"])
CAMY = G("camy_flux", FLUX_C, ETAT["flux"])
ADD["flux"] = G("add_flux", FLUX_C, CAMY)
ALPHA["flux"] = G("ctrl_alpha", FLUX_C, ADD["flux"])
TRANS_F = G("trans_flux", FLUX_C, CAMY)
ALPHA["flux_t"] = G("ctrl_alpha", FLUX_C, TRANS_F)
COLONNES = [
    (0.0, -4.6, 17.0, 23.0, 9.0, "A"),
    (-3.8, -4.38, 15.0, 22.0, 8.0, "A"), (3.8, -4.38, 15.5, 21.0, 8.0, "A"),
    (-6.0, -5.2, 21.0, 17.0, 6.0, "B"), (6.0, -5.1, 20.5, 18.0, 6.0, "B"),
    (-8.2, -3.78, 10.0, 20.0, 6.5, "B"), (8.2, -3.78, 10.5, 19.0, 6.5, "B"),
    (-8.6, -3.0, 2.0, 15.0, 7.0, "B"), (8.6, -3.1, 1.5, 16.0, 7.0, "B"),
    (-5.0, -2.6, -0.5, 9.0, 5.0, "B"), (5.0, -2.7, -0.5, 8.5, 5.0, "B"),
]
Z_T = [-9.0, -9.12, -9.12, -9.24, -9.24, -9.36, -9.36, -9.48, -9.48, -9.6, -9.6]
COLS = []
for i, (x, zz, y0, h, w, t) in enumerate(COLONNES):
    base = (x, y0, zz)
    g = G(f"col{i}", base, ADD["flux"])
    plaque(g, f"colonne{i}", (x, y0 + h / 2, zz), w, h, UV[f"col{t}0"])
    COLS.append((g, G("ctrl_uv", base, g), t, i))
    gt = G(f"col{i}_t", base, TRANS_F)
    plaque(gt, f"colonne{i}_voile", (x, y0 + h / 2, Z_T[i]), w, h, UV[f"colT{t}0"])
    COLS.append((gt, G("ctrl_uv", base, gt), t, i))
# mirage au-dessus de la tête (derrière elle)
MIR = G("mirage", (0, 33, -3.3), ADD["flux"])
plaque(MIR, "mirage", (0, 38, -3.3), 20, 10, UV["mirage0"])
MIR_UV = G("ctrl_uv", (0, 33, -3.3), MIR)

# Braises : (x, y de départ, hauteur de montée, amplitude du S, taille, cadence k : montées par seconde, phase)
BRAISES = []
ADD_B = G("add_braises", FLUX_C, CAMY)
ALPHA["braises"] = G("ctrl_alpha", FLUX_C, ADD_B)
KS = (0.375, 0.5, 0.625)                             # 2,67 s, 2 s, 1,6 s par montée (boucle de 8 s fermée)
for i in range(36):
    cote = -1 if i % 2 else 1
    if i < 12:                                       # des jambes aux hanches
        x, y0, H = cote * RNG.uniform(3.6, 6.5), RNG.uniform(0, 5), RNG.uniform(9, 14)
    elif i < 24:                                     # des bras aux épaules et au-dessus
        x, y0, H = cote * RNG.uniform(7.5, 10.5), RNG.uniform(10, 18), RNG.uniform(10, 16)
    else:                                            # des épaules au-dessus de la tête
        x, y0, H = cote * RNG.uniform(1.5, 7.5), RNG.uniform(24, 30), RNG.uniform(8, 14)
    z = -RNG.uniform(2.2, 3.6) - (0 if i >= 24 else 1.2)
    taille = RNG.uniform(1.2, 1.6) if i < 24 else RNG.uniform(1.0, 1.3)
    g = G(f"braise{i}", (x, y0, z), ADD_B)
    plaque(g, f"braise{i}", (x, y0, z), taille, taille, UV[f"braise{i % 2}_0"])
    BRAISES.append(dict(g=g, uv=G("ctrl_uv", (x, y0, z), g), H=H, amp=RNG.uniform(0.6, 1.6) * cote, k=KS[i % 3],
                        ph=round(float(RNG.uniform(0, 1)), 3), ph2=int(RNG.integers(0, 360))))

# Sol : brûlure trans_ (contraste de jour), fissures fixes qui respirent, anneau qui tourne. Suit le torse ; masqué hors debout.
AURA["sol"] = G("aura_sol", (0, 0.4, 0), MEMBRES["body"])
ETAT["sol"] = G("etat_sol", (0, 0.4, 0), AURA["sol"])
ADD["sol"] = G("add_sol", (0, 0.4, 0), ETAT["sol"])
ALPHA["sol"] = G("ctrl_alpha", (0, 0.4, 0), ADD["sol"])
plaque(ADD["sol"], "fissures", (0, 0.45, 0), 22, 22, UV["fissures"], face="up", ep=0.2)
SOL = G("sol_tourne", (0, 0.4, 0), ADD["sol"])
plaque(SOL, "anneau", (0, 0.75, 0), 26, 26, UV["anneau"], face="up", ep=0.2)
TRANS_S = G("trans_sol", (0, 0.4, 0), ETAT["sol"])
ALPHA["sol_t"] = G("ctrl_alpha", (0, 0.4, 0), TRANS_S)
plaque(TRANS_S, "brulure", (0, 0.15, 0), 28, 28, UV["brulure"], face="up", ep=0.2)

# Points de départ des braises en particules (+Y du groupe = vers le haut)
EMITS = []
ETINC = [("tete", (0, 32.6, 0)), ("tete", (3.5, 30, 2)), ("tete", (-3.5, 30, 2)),
         ("corps", (0, 22, 2.6)), ("corps", (2.5, 15, 2.6)), ("corps", (-2.5, 15, -2.6)),
         ("bras_d", (8.4, 23, 0)), ("bras_d", (6, 12.2, 0)), ("bras_g", (-8.4, 23, 0)), ("bras_g", (-6, 12.2, 0)),
         ("jambe_d", (4.3, 5, 0)), ("jambe_g", (-4.3, 5, 0)), ("jambe_d", (2, 1, 2.5)), ("jambe_g", (-2, 1, -2.5))]
for k, (z, p) in enumerate(ETINC):
    EMITS.append(G("emit_braise" + (str(k + 1) if k else ""), p, ETAT[z]))

PART = G("particle_braise", (0, 0, 0))
plaque(PART, "braise", (0, 1.1, 0), 0.7, 0.7, UV["particule"])

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


PH_Z = {z: int(RNG.integers(0, 360)) for z in list(ZONES) + ["flux", "sol", "braises"]}
PH_C = [(int(RNG.integers(0, 360)), int(RNG.integers(0, 360))) for _ in COLS]


def etat(nom, L, haut=1.0, larg=1.0, vac=0.08, halo=1.0, souffle=0.03, alpha=-0.15, a_amp=0.08, flux=(0, 0, 0), recul=0.0,
         sol=1.0, braises=1.0, kv=2, kb=1):
    A = {}
    for z in ZONES:
        sc = sinus(L, kb, PH_Z[z], halo * souffle, halo)
        piste(A, ETAT[z], [kf("scale", 0, sc, sc, sc)])
        if recul:
            piste(A, ETAT[z], [kf("position", 0, 0, 0, recul)])
    for z in list(ZONES) + ["flux", "sol", "braises"]:
        cle = kf("position", 0, sinus(L, kb, PH_Z[z] + 90, a_amp, alpha), 0, 0)
        piste(A, ALPHA[z], [cle])
        if z + "_t" in ALPHA:
            piste(A, ALPHA[z + "_t"], [dict(cle)])
    if any(flux):
        piste(A, ETAT["flux"], [kf("position", 0, *flux)])
    for (g, _, t, i), (p1, p2) in zip(COLS, PH_C):
        k1, k2 = kv + (i % 2), kv + 1 + (i % 3)
        sy = f"{s(haut)}*(1+{s(vac)}*math.sin(q.anim_time*{s(360 * k1 / L)}+{p1})+{s(vac * 0.5)}*math.sin(q.anim_time*{s(360 * k2 / L)}+{p2}))"
        sx = sinus(L, k2, p2 + 60, larg * vac * 0.4, larg)
        piste(A, g, [kf("scale", 0, sx, sy, 1)])
    m = min(haut, 1.2)
    piste(A, MIR, [kf("scale", 0, m, m, 1)])
    piste(A, ADD_B, [kf("scale", 0, braises, braises, braises)])
    sc = sinus(L, kb, PH_Z["sol"], sol * 0.04, sol)
    piste(A, ETAT["sol"], [kf("scale", 0, sc, 1 if sol else 0, sc)])
    return {"uuid": nuid(), "name": nom, "loop": "loop", "override": False, "length": L, "snapping": 24, "selected": nom == "idle",
            "animators": A}


STATES = [
    etat("idle", 8.0, kv=4, kb=2),
    etat("walk", 1.6, haut=1.05, alpha=-0.12, flux=(0, 0, 1.5), recul=0.3, kv=1),
    etat("run", 1.0, haut=1.22, larg=0.92, vac=0.11, alpha=-0.02, a_amp=0.02, flux=(0, -0.5, 4.0), recul=0.8, kv=1),
    etat("sneak", 4.0, haut=0.72, larg=1.2, halo=0.92, alpha=-0.35, flux=(0, -3.5, 1.5), sol=0, braises=0.8, kv=2),
    etat("fly", 2.4, haut=1.15, larg=0.95, alpha=-0.1, flux=(0, 0, 2.0), recul=0.4, kv=2),
    etat("glide", 3.6, haut=0, larg=0, alpha=-0.15, sol=0, braises=0.5, kv=3),
    etat("swim", 3.6, haut=0, larg=0, alpha=-0.3, sol=0, braises=0.0, kv=2),
    etat("fall", 2.0, haut=1.2, larg=0.85, vac=0.07, halo=1.04, alpha=-0.1, flux=(0, 1.0, 0), sol=0.8, kv=2),
    etat("mount", 4.0, haut=0.85, alpha=-0.22, flux=(0, -1.0, 0), sol=0, kv=2),
    etat("sleep", 4.0, haut=0.3, larg=0.8, vac=0.04, halo=0.85, souffle=0.02, alpha=-0.78, a_amp=0.06, sol=0, braises=0.0, kv=1),
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


# overlay_braises (8 s) : films des colonnes et du mirage, montée et refroidissement des braises, anneau qui tourne,
# fissures qui respirent (ctrl_alpha du sol est dans les états : ici une échelle douce).
LO = 8.0
A = {}
for (g, uvg, t, i) in COLS:
    w = COL[t][0]
    fps = 10 + (i % 3)
    piste(A, uvg, [kf("position", 0, f"math.floor(math.mod(q.anim_time*{fps}+{i * 3},{FR}))*{w}", 0, 0)])
piste(A, MIR_UV, [kf("position", 0, f"math.floor(math.mod(q.anim_time*7,{FR}))*{MW}", 0, 0)])
for b in BRAISES:
    u = f"math.mod(q.anim_time*{s(b['k'])}+{s(b['ph'])},1)"
    piste(A, b["g"], [kf("position", 0, f"{s(b['amp'])}*math.sin({u}*400+{b['ph2']})", f"{u}*{s(b['H'])}", 0),
                      kf("scale", 0, f"math.min(1,{u}*8)*(1-{u})*1.25", f"math.min(1,{u}*8)*(1-{u})*1.25", 1)])
    piste(A, b["uv"], [kf("position", 0, f"math.floor({u}*4)*8", 0, 0)])
for j, g in enumerate(DISQUES):
    sens = 1 if j % 2 else -1
    piste(A, g, [kf("rotation", 0, 0, 0, f"q.anim_time*{s(sens * 360 * (1 + j % 2) / LO)}")])
piste(A, SOL, [kf("rotation", 0, 0, "q.anim_time*45", 0)])
overlay = {"uuid": nuid(), "name": "overlay_braises", "loop": "loop", "override": False, "length": LO, "snapping": 24,
           "selected": False, "animators": A}

PF = 0.6
pt = [i * PF / 12 for i in range(13)]
p_fall = {"uuid": nuid(), "name": "particle_braise_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24,
          "selected": False, "animators": {PART.uuid: {"name": PART.nom, "type": "bone", "keyframes":
              [kf("scale", t, *([1 + 0.25 * math.sin(2 * math.pi * t / PF)] * 3)) for t in pt]}}}

# event_equip (2,4 s) : le sol se fend et rougeoie (0–0,7 s), la chaleur gagne des pieds à la tête (0,4–1,9 s), puis les
# filets, le mirage et les braises partent (1,1–2,2 s). Un son : crépitement de feu de camp.
LE = 2.4
TE = [j * LE / 24 for j in range(25)]
A = {}
for g in DISQUES:
    t0 = 0.4 + (HAUT[g.uuid] / 33) * 1.0
    piste(A, g, [kf("scale", t, *([sm(t, t0, t0 + 0.4) * (1 + 0.12 * bump(t, t0 + 0.2, t0 + 0.4, t0 + 0.5, t0 + 0.9))] * 3)) for t in TE])
piste(A, AURA["sol"], [kf("scale", t, *([sm(t, 0.0, 0.6) * (1 + 0.12 * bump(t, 0.35, 0.55, 0.65, 1.1))] * 3)) for t in TE])
piste(A, AURA["flux"], [kf("scale", t, 1, sm(t, 1.1, 2.2), 1) for t in TE])
A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "block.campfire.crackle", "file": ""}], "time": 0.1}]}
equip = {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": LE, "snapping": 24, "selected": False,
         "animators": A}

ANIMS = STATES + [overlay, equip, p_fall]
assert len(EMITS) <= 32
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures,
         "animations": ANIMS}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
from reactions import retirer_reactions
from menu_aura import adapter_menu
from ambiance import ajouter_ambiance
limiter_sons(model)
retirer_reactions(model)
adapter_menu(model, cacher=False)
ajouter_ambiance(model)
# pièce tout en add_ : pas de calque _e (il redoublerait l'additif en jeu, leçon aura_berenice)
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
