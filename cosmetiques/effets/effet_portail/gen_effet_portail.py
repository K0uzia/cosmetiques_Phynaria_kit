"""Portail de passage (v2) : effet de téléportation sans ensemble (guide 15). Design original, étude par analogie
(.claude/references/effets/portails-passage.md ; principes-fx-anime, magie-cercles, failles-portails).
Écrit effet_portail.png, effet_portail_e.png et .build/effet_portail_brut.bbmodel. v1 gardée dans .build/gen_v1.py.

v2 (retour en jeu du 2026-11-07, captures 16.44.00 à 16.44.03, de nuit) : « le portail de passage est à améliorer ».
Constats : ovale en aplat bleu saturé et opaque (fond alpha 222 + spirales larges), plat, qui cache tout ; runes et éclats peu lisibles
(plaques 5 px, éclats sombres sur nuit) ; la copie du joueur reste à côté du portail : elle garde le lacet du vrai joueur (qui a tourné
après « Essayer ») alors que l'effet garde celui du clic ; le portail était à 14 px devant elle et elle s'arrêtait 5 px avant le plan.
Réponse : portail à 6 px devant le joueur (ZP), la copie marche, **traverse le plan** et rétrécit dans le tunnel (on la devine derrière
le fond translucide) ; à l'arrivée, elle sort du plan à 7 px derrière elle.

Pièces (posées au sol, pieds du joueur à l'origine, face à -Z ; aucun groupe du corps)
- Ovale (groupe « ouvre ») dessiné en espace cercle (rayon 15 px), étiré par l'animation (y × 1,6) : 30 × 48 px, centre à y = 32.
  Fond trans_ marine translucide (alpha 95 au centre, 175 au bord : on devine le décor) ; trois couches de tourbillon add_ à trois
  profondeurs, tailles et vitesses différentes ; tunnel de 6 anneaux add_ qui défilent en profondeur (aspirés au départ, soufflés à
  l'arrivée) ; éclat central (lueur add_ + étoile cam_) au fond du tunnel.
- Bord épais et vibrant : halo add_ en croissant qui tourne, deux anneaux de cœur add_ bruités qui tournent en sens contraire, filet
  trans_ blanc cerné de marine (lisible de jour) + _e ; deux couronnes de flammèches add_ ; 24 mèches add_ en géométrie qui vacillent
  (échelle au hasard) ; 8 filaments en géométrie (chaînes de cubes fins, profil lumineux) qui courent autour du bord et s'échappent.
- Fente add_ en zigzag (la déchirure), flash add_ cam_ (blanc à frange lavande), lueur add_ au sol.
- Cadre de 12 runes inventées en géométrie nette (traits de 0,8 px, cœur blanc trans_ cerné de marine + _e, halo add_), sur une
  ellipse 20 × 29 : la couronne tourne, chaque rune contre-tourne (traits dessinés 1,45 fois moins hauts).
- 12 éclats de pierre en orbite dans le plan du portail (veines _e vives, liseré clair).
- Fermeture : l'ovale se contracte en boule, trois anneaux add_ inclinés (gyroscope) se resserrent autour en tournant, point de lumière.
- Particules (emit_, ctrl_emit chacun) : etincelle, rune, poussiere (modélisées) ; portal, reverse_portal, electric_spark,
  dust_7fc8ff_12 (Minecraft).

Animations (30 clés/s, une courbe lisse par phase, arrêts adoucis seulement aux vrais arrêts) : charge (loop 12 s), depart (4 s :
fente qui se déchire, éclat, l'ovale s'ouvre et s'étire ; le joueur marche, traverse le plan, est aspiré ; anneaux qui se resserrent,
point), arrivee (3,6 s : flash, anneaux qui s'écartent, ouverture ; le joueur sort du plan et s'arrête ; fermeture en anneaux),
particle_*_fall. Sons embarqués originaux (sons/*.py, tools/synthe.py) : portail_ouvre, portail_passe, portail_ferme ; rien pendant la charge.

Fonctions avancées : add_, trans_, cam_, ctrl_alpha, ctrl_emit, emit_, emit_mc_, _e, groupe joueur, sons embarqués.
Ce qui se juge seulement en jeu (onglet Effets, « Essayer ») : particules et cadences, additif réel et tri trans_ du fond autour de
la copie du joueur (avec et sans shader), transparence du fond de jour, volume des sons, orientation de la copie (lacet du vrai joueur).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "effet_portail"
TEX = 512
SS = 4
RNG = np.random.default_rng(57)

# géométrie de l'ovale
R = 15.0            # rayon du fond (espace cercle)
E = 1.6             # étirement vertical de l'ovale
RR, ER = 20.0, 1.45  # rayon et étirement du cadre de runes
YC = 32.0           # hauteur du centre
ZP = -14.0          # plan du portail (devant le joueur) ; arrivée : + 28 (derrière lui)
DZ_ARR = 28.0

# ------------------------------------------------------------------ palette (échantillonnée, fiche portails-passage)
RAMP = np.array([(6, 10, 30), (14, 26, 74), (24, 46, 128), (40, 80, 196), (64, 124, 240), (104, 176, 255),
                 (156, 226, 255), (210, 242, 255), (246, 252, 255)], np.float32)


def ramp_c(f):
    f = np.clip(np.asarray(f, np.float32), 0, 1) * (len(RAMP) - 1)
    i = np.clip(f.astype(int), 0, len(RAMP) - 2)
    u = (f - i)[..., None]
    return RAMP[i] * (1 - u) + RAMP[i + 1] * u


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def grille(W, H, ss=SS):
    n_w, n_h = W * ss, H * ss
    return np.meshgrid((np.arange(n_w) + 0.5) / n_w * 2 - 1, 1 - (np.arange(n_h) + 0.5) / n_h * 2)


def lanczos(a, W, H):
    return np.array(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)).astype(np.float32)


def add_img(f, W, H, peak, teinte=None):
    """Additif : couleur de la rampe × intensité, crête « peak » ; le presque noir est transparent (alpha 0/255)."""
    f = np.clip(f, 0, 1)
    rgb = (ramp_c(f) if teinte is None else teinte(f)) * f[..., None] * (peak / 255.0)
    out = np.stack([lanczos(rgb[..., k], W, H) for k in range(3)], axis=-1)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = out
    a = arr[..., :3].max(axis=2) > 12
    arr[..., 3] = a * 255
    arr[~a, :3] = 0
    return arr


def trans_img(rgb, al, W, H, seuil=8):
    c = np.stack([lanczos(rgb[..., k], W, H) for k in range(3)], axis=-1)
    a = lanczos(al, W, H)
    arr = np.zeros((H, W, 4), np.uint8)
    a = np.where(a > seuil, np.clip(a, 1, 254), 0)
    arr[..., :3] = c
    arr[..., 3] = a
    arr[a == 0, :3] = 0
    return arr


def opaque_img(rgb, al, W, H):
    c = np.stack([lanczos(rgb[..., k], W, H) for k in range(3)], axis=-1)
    a = lanczos(al, W, H)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = c
    arr[..., 3] = np.where(a > 110, 255, 0)
    arr[arr[..., 3] == 0, :3] = 0
    return arr


def segment(x, y, p, q, w):
    px, py = p
    dx, dy = q[0] - px, q[1] - py
    L2 = dx * dx + dy * dy + 1e-12
    t = np.clip(((x - px) * dx + (y - py) * dy) / L2, 0, 1)
    d = np.hypot(x - px - t * dx, y - py - t * dy)
    return np.clip((w - d) / (w * 0.3), 0, 1)


def polaire(N):
    x, y = grille(N, N)
    return x, y, np.hypot(x, y), np.arctan2(y, x)




# ------------------------------------------------------------------ v2 : placement (la copie traverse le plan)
ZP = -9.0           # plan du portail au départ et pendant la charge (9 px devant le joueur)
DZ_ARR = 18.0       # arrivée : plan à ZP + 18 = +9 (derrière le joueur)
NAVY = np.array((22, 37, 93), np.float32)


def ease(u):
    """Arrêt adouci aux deux bouts (seulement pour un vrai départ et un vrai arrêt)."""
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def lin(t, a, b):
    return min(max((t - a) / (b - a), 0.0), 1.0)


def amorti(u, k=6.0, f=1.4):
    """0 -> 1 avec un dépassement amorti (ressort), vitesse continue."""
    if u <= 0:
        return 0.0
    return 1 - math.exp(-k * u) * (math.cos(2 * math.pi * f * u) + k / (2 * math.pi * f) * math.sin(2 * math.pi * f * u))


# ------------------------------------------------------------------ peinture
def fond_tex(N=64):
    """Fond marine translucide : alpha 95 au centre (on devine le décor), 175 vers le bord ; stries de tourbillon à peine visibles."""
    x, y, r, p = polaire(N)
    stri = 0.5 + 0.5 * np.cos(3 * p + 8 * np.log(r + 0.08))
    v = 0.09 + 0.10 * smooth((r - 0.3) / 0.7) + 0.03 * stri * smooth((r - 0.15) / 0.3)
    al = (95 + 80 * smooth((r - 0.25) / 0.6)) * smooth((0.985 - r) / 0.03)
    return trans_img(ramp_c(v), al, N, N, seuil=20), v


def spirale_f(N, bras, torsion, expo, r0, r1, seed):
    x, y, r, p = polaire(N)
    rng = np.random.default_rng(seed)
    u = bras * p + torsion * np.log(r + 0.05)
    band = (0.5 + 0.5 * np.cos(u)) ** expo
    casse = 0.45 + 0.55 * (0.5 + 0.5 * np.cos(3 * p + 5 * r + rng.uniform(0, 6))) * (0.6 + 0.4 * np.cos(7 * p + rng.uniform(0, 6)))
    w = smooth((r - r0) / 0.25) * smooth((r1 - r) / 0.1)
    return band * casse * w * (0.35 + 0.65 * np.clip(r, 0, 1) ** 1.2)


def anneau_f(N, r0, w, mod=0.4, k=2, ph=0.0):
    x, y, r, p = polaire(N)
    return np.exp(-((r - r0) / w) ** 2) * (1 - mod + mod * (0.5 + 0.5 * np.cos(k * p + ph)))


def croissant_f(N, r0, w, expo=2.0, base=0.3):
    x, y, r, p = polaire(N)
    return np.exp(-((r - r0) / w) ** 2) * (base + (1 - base) * (0.5 + 0.5 * np.cos(p)) ** expo)


def coeur_f(N, r0, seed):
    """Anneau de cœur bruité (épaisseur et éclat qui varient le long du bord) : deux copies tournent en sens contraire = vibration."""
    x, y, r, p = polaire(N)
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.28, 4)
    w = 0.05 * (1 + 0.35 * np.sin(7 * p + ph[0]) + 0.25 * np.sin(13 * p + ph[1]))
    e = 0.7 + 0.3 * np.sin(5 * p + ph[2]) * np.sin(3 * p + ph[3])
    return np.exp(-((r - r0) / np.maximum(w, 0.015)) ** 2) * e


def bord_net_tex(N=160, r0=0.81):
    """Filet net trans_ : cœur blanc bleuté de 0,8 px cerné de marine (lisible sur ciel clair), le reste transparent."""
    x, y, r, p = polaire(N)
    d = np.abs(r - r0)
    coeur = d < 0.024
    cerne = d < 0.042
    v = np.where(coeur, 0.95, 0.22)
    al = np.where(coeur, 235.0, np.where(cerne, 150.0, 0.0))
    return trans_img(ramp_c(v), al, N, N, seuil=40), coeur.astype(np.float32)


def flammes_f(N, r_b, seed, n=30):
    """Couronne de flammèches : langues de longueur et largeur au hasard qui partent du bord vers l'extérieur."""
    x, y, r, p = polaire(N)
    rng = np.random.default_rng(seed)
    f = np.zeros_like(r)
    for a0, L, w in zip(rng.uniform(-np.pi, np.pi, n), rng.uniform(0.06, 0.26, n), rng.uniform(0.04, 0.09, n)):
        dp = np.angle(np.exp(1j * (p - a0)))
        u = np.clip((r - r_b) / L, 0, 1)
        lang = np.exp(-(dp / (w * (1 - 0.7 * u))) ** 2) * (1 - u) ** 1.3 * smooth((r - r_b + 0.03) / 0.05)
        f = np.maximum(f, lang)
    return f


def meche_f(W=16, H=48):
    x, y = grille(W, H)
    u = (y + 1) / 2                                         # 0 à la base (bord du portail), 1 à la pointe
    larg = 0.55 * (1 - u) ** 0.7 + 0.04
    return np.exp(-(x / larg) ** 2) * (1 - u) ** 0.9 * smooth(u / 0.12)


def profil_f(W=4, H=16, coeur=0.25, glow=0.7, k=0.35):
    x, y = grille(W, H)
    return np.clip(np.exp(-(y / coeur) ** 2) + k * np.exp(-(y / glow) ** 2), 0, 1)


def trait_rune_tex(W=4, H=16):
    """Profil en travers d'un trait de rune : cœur blanc (60 %), cerne marine."""
    x, y = grille(W, H)
    v = np.where(np.abs(y) < 0.55, 0.95, 0.2)
    al = np.where(np.abs(y) < 0.55, 245.0, 215.0)
    return trans_img(ramp_c(v), al, W, H, seuil=8), (np.abs(y) < 0.55).astype(np.float32)


def etoile_f(N=48):
    x, y, r, p = polaire(N)
    br = np.exp(-(np.abs(x) / 0.06) ** 2) * np.clip(1 - np.abs(y), 0, 1) ** 2 + np.exp(-(np.abs(y) / 0.06) ** 2) * np.clip(1 - np.abs(x), 0, 1) ** 2
    return np.clip(br + np.exp(-(r / 0.22) ** 2), 0, 1) * smooth((0.98 - r) / 0.1)


def flash_couleur(f):
    lav = np.array((190, 176, 255), np.float32)
    bl = np.array((250, 252, 255), np.float32)
    k = smooth((f - 0.3) / 0.6)[..., None]
    return lav * (1 - k) + bl * k


def fente_f(W=24, H=128):
    """La déchirure : ligne de lumière en zigzag doux, cœur net + lueur, bouts effilés."""
    x, y = grille(W, H)
    x0 = 0.2 * np.sin(11 * y + 0.5) + 0.1 * np.sin(23 * y + 1.3)
    return np.clip(np.exp(-((x - x0) / 0.1) ** 2) + 0.4 * np.exp(-((x - x0) / 0.4) ** 2), 0, 1) * (1 - np.abs(y) ** 4)
# runes inventées : un fût + 2 à 3 traits (diagonales, barres, crochets, points) ; traits de 4 texels sur 32
TRAITS_R = {
    "fut": [((0, -0.7), (0, 0.7))],
    "diag_h": [((0, 0.7), (0.5, 0.25))], "diag_b": [((0, -0.7), (-0.5, -0.25))],
    "barre": [((-0.42, 0.05), (0.42, 0.05))], "chevron": [((-0.45, 0.45), (0, 0.15)), ((0, 0.15), (0.45, 0.45))],
    "croc_h": [((0, 0.7), (-0.4, 0.7))], "croc_b": [((0, -0.7), (0.4, -0.7))],
    "branche": [((0, -0.1), (0.48, -0.5))], "fourche": [((0, 0.3), (-0.45, 0.7)), ((0, 0.3), (0.45, 0.7))],
    "pied": [((-0.4, -0.7), (0.4, -0.7))], "boucle": [((0, 0.1), (0.4, 0.3)), ((0.4, 0.3), (0, 0.5))],
}
RUNES_DEF = [("fut", "diag_h", "barre"), ("fut", "chevron", "pied"), ("fut", "croc_h", "branche"), ("fut", "fourche", "point"),
             ("fut", "boucle", "croc_b"), ("fut", "diag_b", "diag_h"), ("fut", "barre", "point2"), ("fut", "branche", "fourche"),
             ("fut", "croc_b", "chevron"), ("fut", "pied", "boucle"), ("fut", "diag_h", "croc_b", "point"), ("fut", "chevron", "diag_b")]


def rune_f(defn, N=32, w=0.11):
    x, y = grille(N, N)
    f = np.zeros_like(x)
    for nom in defn:
        if nom.startswith("point"):
            cx = -0.4 if nom == "point" else 0.42
            f = np.maximum(f, np.clip((0.15 - np.hypot(x - cx, y + (0.2 if nom == "point" else -0.35))) / 0.05, 0, 1))
            continue
        for a, b in TRAITS_R[nom]:
            f = np.maximum(f, segment(x, y, a, b, w))
    return f


def rune_tex(f, N=32):
    """Glyphe blanc-cyan cerné de marine (lisible sur ciel clair comme de nuit)."""
    big = np.array(Image.fromarray((f * 255).astype(np.uint8)).filter(__import__("PIL.ImageFilter", fromlist=["x"]).MaxFilter(9))) / 255.0
    v = np.where(f > 0.5, 0.86, 0.22)
    al = np.where(f > 0.5, 240.0, np.where(big > 0.5, 215.0, 0.0))
    return trans_img(ramp_c(v), al, N, N, seuil=50)


def halo_rune_f(N=32):
    x, y, r, p = polaire(N)
    return np.exp(-(r / 0.55) ** 2) * smooth((0.98 - r) / 0.1)


def pierre_tex(N=32, seed=0):
    """Ardoise bleutée, arêtes plus claires, une veine de rune cyan (3 texels) ; opaque."""
    rng = np.random.default_rng(seed)
    x, y = grille(N, N)
    bruit = np.zeros_like(x)
    for k in range(4):
        fx, fy, ph = rng.uniform(2, 9, 2).tolist() + [rng.uniform(0, 6)]
        bruit += np.sin(fx * x * 3 + ph) * np.cos(fy * y * 3 + ph * 0.7) / (k + 1)
    v = 70 + 12 * bruit
    bord = np.maximum(np.abs(x), np.abs(y))
    v = v + 22 * smooth((bord - 0.8) / 0.2)
    rgb = np.stack([v * 0.82, v * 0.88, v * 1.05], axis=-1)
    a, b = rng.uniform(-0.7, 0.7, 2)
    veine = np.maximum(segment(x, y, (-0.8, a), (0.1, b), 0.1), segment(x, y, (0.1, b), (0.75, -a * 0.6), 0.1))
    rgb = rgb * (1 - veine[..., None]) + np.array((110, 210, 255)) * veine[..., None]
    return opaque_img(rgb, np.full_like(x, 255.0), N, N), veine


def etincelle_tex(N=16):
    x, y, r, p = polaire(N)
    f = np.maximum(np.clip(1 - np.abs(x) / 0.13 - np.abs(y), 0, 1), np.clip(1 - np.abs(y) / 0.13 - np.abs(x), 0, 1))
    f = np.maximum(f, np.clip(1 - r / 0.35, 0, 1))
    return opaque_img(ramp_c(0.6 + 0.4 * f), np.where(f > 0.12, 255.0, 0), N, N)


def point_tex(N=8):
    x, y, r, p = polaire(N)
    return opaque_img(ramp_c(0.7 + 0.3 * (1 - r)), np.where(r < 0.85, 255.0, 0), N, N)


UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_A_POSER = []


def a_poser(nom, im):
    _A_POSER.append((nom, im))


def ranger(pas=8):
    n = TEX // pas
    occ = np.zeros((n, n), bool)
    for nom, im in sorted(_A_POSER, key=lambda p: -p[1].shape[0] * p[1].shape[1]):
        h, w = im.shape[:2]
        gh, gw = -(-h // pas), -(-w // pas)
        place = next(((gy, gx) for gy in range(n - gh + 1) for gx in range(n - gw + 1) if not occ[gy:gy + gh, gx:gx + gw].any()), None)
        assert place is not None, f"atlas plein : {nom}"
        gy, gx = place
        occ[gy:gy + gh, gx:gx + gw] = True
        y, x = gy * pas, gx * pas
        tex[y:y + h, x:x + w] = im
        UV[nom] = (x, y, x + w, y + h)
    print(f"atlas : {occ.mean() * 100:.0f} % occupé")




def pierre_tex(N=32, seed=0):
    """Ardoise bleutée, liseré clair sur les arêtes, veine de rune cyan vive (au calque _e) ; opaque."""
    rng = np.random.default_rng(seed)
    x, y = grille(N, N)
    bruit = np.zeros_like(x)
    for k in range(4):
        fx, fy, ph = rng.uniform(2, 9, 2).tolist() + [rng.uniform(0, 6)]
        bruit += np.sin(fx * x * 3 + ph) * np.cos(fy * y * 3 + ph * 0.7) / (k + 1)
    v = 78 + 12 * bruit
    bord = np.maximum(np.abs(x), np.abs(y))
    v = v + 60 * smooth((bord - 0.78) / 0.16)
    rgb = np.stack([v * 0.8, v * 0.9, v * 1.08], axis=-1)
    a, b = rng.uniform(-0.7, 0.7, 2)
    veine = np.maximum(segment(x, y, (-0.85, a), (0.1, b), 0.13), segment(x, y, (0.1, b), (0.8, -a * 0.6), 0.13))
    rgb = rgb * (1 - veine[..., None]) + np.array((150, 230, 255)) * veine[..., None]
    return opaque_img(np.clip(rgb, 0, 255), np.full_like(x, 255.0), N, N), veine


# crêtes additives (cumul de face mesuré plus bas)
P = dict(spa=46, spb=36, spc=30, tunnel=44, halo=62, coA=92, coB=66, flA=70, flB=56, meche=120, fil=235, gyro=225, onde=60,
         flash=225, fente=230, sol=60, rune=80, lien=50, lueur=150, etoile=235)
fond_im, fond_v = fond_tex()
a_poser("fond", fond_im)
a_poser("spa", add_img(spirale_f(128, 3, 6.5, 6, 0.1, 0.95, 1), 128, 128, P["spa"]))
a_poser("spb", add_img(spirale_f(128, -4, 8.5, 8, 0.12, 0.95, 2), 128, 128, P["spb"]))
a_poser("spc", add_img(spirale_f(128, 5, 10.0, 10, 0.08, 0.95, 3), 128, 128, P["spc"]))
a_poser("tunnel", add_img(anneau_f(96, 0.9, 0.06, mod=0.55, k=3), 96, 96, P["tunnel"]))
HALO_D, CO_D, FL_D = 1.4 * R, 1.15 * R, 1.5 * R        # demi-côtés des plaques (px)
a_poser("halo", add_img(croissant_f(96, 0.97 * R / HALO_D, 0.13), 96, 96, P["halo"]))
a_poser("coA", add_img(coeur_f(128, 0.95 * R / CO_D, 7), 128, 128, P["coA"]))
a_poser("coB", add_img(coeur_f(128, 0.93 * R / CO_D, 8), 128, 128, P["coB"]))
bord_im, bord_coeur = bord_net_tex(160, 0.95 * R / CO_D)
a_poser("bord", bord_im)
a_poser("flA", add_img(flammes_f(128, 0.99 * R / FL_D, 4), 128, 128, P["flA"]))
a_poser("flB", add_img(flammes_f(128, 0.97 * R / FL_D, 5, n=24), 128, 128, P["flB"]))
a_poser("meche", add_img(meche_f(), 16, 48, P["meche"]))
a_poser("fil", add_img(profil_f(), 4, 16, P["fil"]))
tr_im, tr_coeur = trait_rune_tex()
a_poser("trait", tr_im)
a_poser("gyro", add_img(croissant_f(128, 0.92, 0.035, expo=1.5, base=0.35), 128, 128, P["gyro"]))
a_poser("onde", add_img(anneau_f(96, 0.9, 0.05, mod=0.3, k=3), 96, 96, P["onde"]))
x_, y_, r_, _ = polaire(64)
a_poser("flash", add_img(np.exp(-(r_ / 0.5) ** 2) * smooth((0.98 - r_) / 0.15), 64, 64, P["flash"], teinte=flash_couleur))
a_poser("lueur", add_img(np.exp(-(r_ / 0.4) ** 2) * smooth((0.98 - r_) / 0.15), 64, 64, P["lueur"], teinte=flash_couleur))
a_poser("etoile", add_img(etoile_f(), 48, 48, P["etoile"], teinte=flash_couleur))
a_poser("fente", add_img(fente_f(), 24, 128, P["fente"]))
a_poser("sol", add_img(np.exp(-(r_ / 0.55) ** 2) * smooth((0.98 - r_) / 0.2), 64, 64, P["sol"]))
a_poser("halo_rune", add_img(halo_rune_f(), 32, 32, P["rune"]))
a_poser("lien_runes", add_img(anneau_f(128, RR / (RR + 2.5), 0.04, mod=0.35, k=6), 128, 128, P["lien"]))
VEINES = []
for k in range(3):
    im, v = pierre_tex(32, 10 + k)
    a_poser(f"pierre{k}", im)
    VEINES.append(v)
a_poser("etincelle", etincelle_tex())
a_poser("p_rune", rune_tex(rune_f(RUNES_DEF[3], 16, w=0.16), 16))
a_poser("poussiere", point_tex())
ranger()


def vers_e(nom, f, couleur):
    x0, y0, x1, y1 = UV[nom]
    g = lanczos(np.clip(f, 0, 1) * 255, x1 - x0, y1 - y0) / 255
    for c, v in enumerate(couleur):
        tex_e[y0:y1, x0:x1, c] = np.maximum(tex_e[y0:y1, x0:x1, c], (v * g).astype(np.uint8))
    tex_e[y0:y1, x0:x1, 3] = np.where(tex[y0:y1, x0:x1, 3] > 0, 255, 0)


vers_e("bord", bord_coeur, (200, 235, 255))
vers_e("trait", tr_coeur, (190, 230, 255))
vers_e("fond", np.ones_like(fond_v), (10, 20, 56))
for k, v in enumerate(VEINES):
    vers_e(f"pierre{k}", v, (130, 220, 255))


def cumul():
    """Cumul additif vu de face, ovale ouvert au repos (une face par plaque), dans l'espace cercle ; tunnel : 6 anneaux répartis."""
    N = 256
    x, y = grille(N, N, ss=1)
    X, Y = x * R * 1.6, y * R * 1.6
    tot = np.zeros((N, N))

    def couche(nom, demi):
        x0, y0, x1, y1 = UV[nom]
        im = tex[y0:y1, x0:x1, :3].max(axis=2).astype(float)
        H, W = im.shape
        u = np.clip((X / demi + 1) / 2 * (W - 1), 0, W - 1).astype(int)
        v = np.clip((-Y / demi + 1) / 2 * (H - 1), 0, H - 1).astype(int)
        return np.where((np.abs(X) < demi) & (np.abs(Y) < demi), im[v, u], 0)
    tot += couche("spa", R * 0.97) + couche("spb", R * 0.8) + couche("spc", R * 0.6)
    tot += couche("halo", HALO_D) + couche("coA", CO_D) + couche("coB", CO_D) + couche("flA", FL_D) + couche("flB", FL_D)
    for fr in (1.0, 0.8, 0.62, 0.47, 0.34, 0.22):
        tot += couche("tunnel", R * 0.95 * fr) * 0.8
    r = np.hypot(X, Y)
    return tot[r < 0.85 * R].max(), tot.max()


print("cumul additif de face (dedans, bord) : %.0f, %.0f" % cumul())
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

    def __init__(self, nom, origin, parent=None, rotation=None):
        assert len(nom) <= 64
        self.nom, self.origin, self.uuid, self.enfants = nom, [round(float(v), 3) for v in origin], nuid(), []
        self.rotation = [round((float(v) + 180) % 360 - 180, 3) for v in rotation] if rotation is not None else None
        if parent is not None:
            parent.enfants.append(self)
        G.tous.append(self)

    def json(self):
        d = {"name": self.nom, "origin": self.origin, "uuid": self.uuid,
             "children": [c.json() if isinstance(c, G) else c for c in self.enfants]}
        if self.rotation and any(self.rotation):
            d["rotation"] = self.rotation
        return d


elements = []


def r3(v):
    return [round(float(a), 3) for a in v]


def ajouter(g, e):
    elements.append(e)
    g.enfants.append(e["uuid"])
    return e


def plaque(g, nom, c, w, h, uv, ep=0.3, faces=("north", "south"), face_h=None, rot=None, origine=None):
    """Plaque verticale (faces north/south) ou horizontale (face_h = 'up')."""
    c = np.asarray(c, float)
    if face_h:
        a, b = c - (w / 2, ep / 2, h / 2), c + (w / 2, ep / 2, h / 2)
        fs = {face_h: {"uv": [round(float(v), 2) for v in uv], "texture": 0}}
    else:
        a, b = c - (w / 2, h / 2, ep / 2), c + (w / 2, h / 2, ep / 2)
        fs = {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f in faces}
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": r3(a), "to": r3(b), "origin": r3(c if origine is None else origine),
         "box_uv": False, "faces": fs}
    if rot is not None:
        e["rotation"] = r3(rot)
    return ajouter(g, e)


def bloc(g, nom, c, taille, uv, rot):
    c, t = np.asarray(c, float), np.asarray(taille, float)
    f = {"uv": list(uv), "texture": 0}
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": r3(c - t / 2), "to": r3(c + t / 2), "origin": r3(c), "box_uv": False,
         "rotation": r3(rot), "faces": {k: dict(f) for k in ("north", "south", "east", "west", "up", "down")}}
    return ajouter(g, e)




def trait(g, nom, p, q, w, uv, z, ep=0.4, ext=None):
    """Trait fin en géométrie : un cube dans le plan du portail, tourné selon le segment p -> q, prolongé aux bouts."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    d = q - p
    L = float(np.hypot(*d)) + (w if ext is None else ext)
    ang = math.degrees(math.atan2(d[1], d[0]))
    ang = (ang + 90) % 180 - 90
    c = np.array(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, z))
    a, b = c - (L / 2, w / 2, ep / 2), c + (L / 2, w / 2, ep / 2)
    fs = {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f in ("north", "south")}
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": r3(a), "to": r3(b), "origin": r3(c), "box_uv": False, "faces": fs}
    if abs(ang) > 1e-3:
        e["rotation"] = r3((0, 0, ang))
    return ajouter(g, e)


O = (0, 0, 0)
C = (0, YC, ZP)
EFFET = G("effet", O)
JOUEUR = G("joueur", O)
ALPHA = {}
PORTAIL = G("portail", C, EFFET)

# --- ovale (espace cercle, étiré par l'animation)
OUVRE = G("ouvre", C, PORTAIL)
TR_F = G("trans_fond", C, OUVRE)
plaque(TR_F, "fond", C, 2 * R, 2 * R, UV["fond"], ep=0.3)
# trois couches de tourbillon à trois profondeurs (côté -Z au départ ; l'arrivée les passe de l'autre côté par position)
COUCHES, TOURNE_C = [], []
for k, (nom, fr, dz) in enumerate((("spa", 0.97, -0.9), ("spb", 0.8, -2.6), ("spc", 0.6, -4.4))):
    lk = G(f"couche{k + 1}", C, OUVRE)
    tk = G(f"tourne_couche{k + 1}", C, lk)
    ak = G(f"add_couche{k + 1}", C, tk)
    plaque(ak, f"tourbillon{k + 1}", (0, YC, ZP + dz), 2 * R * fr, 2 * R * fr, UV[nom], ep=0.4)
    COUCHES.append((lk, dz))
    TOURNE_C.append(tk)
# tunnel : 6 anneaux qui défilent en profondeur
TT = G("tourne_tunnel", C, OUVRE)
TUNNEL = []
for k in range(6):
    gk = G(f"tunnel{k + 1}", C, TT, rotation=(0, 0, 47 * k))
    ak = G(f"add_tunnel{k + 1}", C, gk)
    ALPHA[f"tun{k}"] = G("ctrl_alpha", C, ak)
    plaque(ak, f"anneau_tunnel{k + 1}", C, 2 * R * 0.95, 2 * R * 0.95, UV["tunnel"], ep=0.2 + 0.05 * k)
    TUNNEL.append(gk)
# bord : halo en croissant, deux anneaux de cœur, filet net, deux couronnes de flammèches
BORD = {}
for cle, uvn, demi, ep in (("halo", "halo", HALO_D, 2.5), ("coeur_a", "coA", CO_D, 1.4), ("coeur_b", "coB", CO_D, 1.7),
                           ("flammes_a", "flA", FL_D, 2.1), ("flammes_b", "flB", FL_D, 2.9)):
    tg = G(f"tourne_{cle}", C, OUVRE)
    ag = G(f"add_{cle}", C, tg)
    ALPHA[cle] = G("ctrl_alpha", C, ag)
    plaque(ag, cle, C, 2 * demi, 2 * demi, UV[uvn], ep=ep)
    BORD[cle] = tg
TB = G("tourne_bord", C, OUVRE)
TR_B = G("trans_bord", C, TB)
plaque(TR_B, "bord", C, 2 * CO_D, 2 * CO_D, UV["bord"], ep=1.1)
# mèches : 24 langues de lumière en géométrie, pivot sur le bord, qui vacillent
TM = G("tourne_meches", C, OUVRE)
MECHES = []
for j in range(24):
    a = 2 * math.pi * j / 24 + RNG.uniform(-0.08, 0.08)
    pj = np.array((R * 0.96 * math.cos(a), YC + R * 0.96 * math.sin(a), ZP + (0.3 if j % 2 else -0.3)))
    gj = G(f"add_meche{j + 1}", pj, TM, rotation=(0, 0, math.degrees(a) - 90))
    L, W = RNG.uniform(4.0, 7.5), RNG.uniform(2.0, 3.0)
    plaque(gj, f"meche{j + 1}", pj + (0, L / 2 - 0.8, 0), W, L, UV["meche"], ep=0.3)
    MECHES.append((gj, RNG.uniform(1.6, 3.4), RNG.uniform(2.3, 4.1), RNG.uniform(0, 6.28), RNG.uniform(0, 6.28)))
# filaments : 8 arcs en géométrie (cubes fins, profil lumineux) qui courent autour du bord et s'en échappent
FILS = []
for k in range(8):
    gk = G(f"fil{k + 1}", C, OUVRE)
    ak = G(f"add_fil{k + 1}", C, gk)
    ALPHA[f"fil{k}"] = G("ctrl_alpha", C, ak)
    a0, span, ph = 2 * math.pi * k / 8 + RNG.uniform(-0.3, 0.3), RNG.uniform(0.55, 1.05), RNG.uniform(0, 6.28)
    n = max(6, int(math.ceil(R * span * 1.1 / 1.2)))
    pts = []
    for i in range(n + 1):
        u = i / n
        th = a0 + span * u
        rad = R * (0.97 + 0.2 * u ** 1.4 + 0.035 * math.sin(2 * math.pi * 1.5 * u + ph))
        pts.append((rad * math.cos(th), YC + rad * math.sin(th), 0.75 * (1 - 0.65 * u)))
    zk = ZP + (0.55 if k % 2 else -0.55)
    for i in range(n):
        (x0, y0, w0), (x1, y1, w1) = pts[i], pts[i + 1]
        trait(ak, f"fil{k + 1}_{i + 1}", (x0, y0), (x1, y1), (w0 + w1) / 2, UV["fil"], zk + 0.03 * (i % 2), ep=0.3, ext=0.12)
    FILS.append((gk, RNG.uniform(0.5, 1.4) * (1 if k % 2 else -1), RNG.uniform(1.1, 2.2), RNG.uniform(0, 6.28)))
ONDE = G("onde", C, OUVRE)
AD_O = G("add_onde", C, ONDE)
ALPHA["onde"] = G("ctrl_alpha", C, AD_O)
plaque(AD_O, "onde", C, 36, 36, UV["onde"], ep=3.3)

# --- fente (la déchirure), flash, éclat central au fond du tunnel, lueur au sol
FENTE = G("fente", C, PORTAIL)
AD_FE = G("add_fente", C, FENTE)
plaque(AD_FE, "fente", C, 2.6, 2 * R * E, UV["fente"], ep=0.6)
FLASH = G("flash", C, PORTAIL)
AD_FL = G("add_flash", C, FLASH)
CAM_FL = G("cam_flash", C, AD_FL)
plaque(CAM_FL, "flash", C, 30, 30, UV["flash"], ep=0.1, faces=("south",))
COEUR = G("coeur", C, PORTAIL)
AD_LU = G("add_lueur", C, COEUR)
plaque(AD_LU, "lueur", C, 12, 12, UV["lueur"], ep=0.2)
AD_ET = G("add_etoile", C, COEUR)
CAM_ET = G("cam_etoile", C, AD_ET)
plaque(CAM_ET, "etoile", C, 8, 8, UV["etoile"], ep=0.1, faces=("south",))
SOL = G("sol", (0, 0, ZP), PORTAIL)
AD_S = G("add_sol", (0, 0, ZP), SOL)
plaque(AD_S, "lueur_sol", (0, 0.35, ZP), 34, 18, UV["sol"], ep=0.1, face_h="up")

# --- cadre de runes : couronne qui tourne, runes qui contre-tournent (droites) ; traits en géométrie, 1/ER moins hauts
CADRE = G("cadre", C, PORTAIL)
TRU = G("tourne_runes", C, CADRE)
AD_L = G("add_lien_runes", C, TRU)
plaque(AD_L, "lien_runes", C, 2 * (RR + 2.5), 2 * (RR + 2.5), UV["lien_runes"], ep=0.7)
SX, SY, W_T = 4.2, 4.6, 0.95
RUNES, CONTRE = [], []
for j in range(12):
    a = math.radians(90 - 30 * j)
    pos = (RR * math.cos(a), YC + RR * math.sin(a), ZP)
    gj = G(f"rune{j + 1}", pos, TRU)
    cj = G(f"contre_rune{j + 1}", pos, gj)
    CONTRE.append(cj)
    tj = G(f"trans_rune{j + 1}", pos, cj)
    ALPHA[f"rune{j}"] = G("ctrl_alpha", pos, tj)
    n_t = 0
    for nomt in RUNES_DEF[j]:
        if nomt.startswith("point"):
            cx, cy = (-0.4, -0.2) if nomt == "point" else (0.42, 0.35)
            p0 = (pos[0] + cx * SX - 0.7, pos[1] + cy * SY / ER)
            trait(tj, f"rune{j + 1}_point", p0, (p0[0] + 1.4, p0[1]), 1.4 / ER, UV["trait"], ZP + 0.02, ep=0.5, ext=0.0)
            continue
        for (ax, ay), (bx, by) in TRAITS_R[nomt]:
            p0 = (pos[0] + ax * SX, pos[1] + ay * SY / ER)
            p1 = (pos[0] + bx * SX, pos[1] + by * SY / ER)
            al_ = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            w_d = W_T * math.sqrt(math.cos(al_) ** 2 + (ER * math.sin(al_)) ** 2) / ER
            n_t += 1
            trait(tj, f"rune{j + 1}_t{n_t}", p0, p1, w_d, UV["trait"], ZP + 0.02 * (n_t % 3), ep=0.5)
    aj = G(f"add_rune{j + 1}", pos, cj)
    ALPHA[f"halo_rune{j}"] = G("ctrl_alpha", pos, aj)
    plaque(aj, f"halo_rune{j + 1}", pos, 10.0, 10.0 / ER, UV["halo_rune"], ep=0.9)
    RUNES.append(gj)

# --- éclats de pierre en orbite dans le plan du portail (ellipse par l'échelle y du groupe)
ORBITE = G("orbite", C, PORTAIL)
SPIN = G("spin_eclats", C, ORBITE)
ECLATS = []
for k in range(12):
    th = 2 * math.pi * k / 12 + RNG.uniform(-0.18, 0.18)
    rad = 24.0 + RNG.uniform(-1.5, 3.0)
    p0 = np.array((rad * math.cos(th), YC + rad * math.sin(th), ZP + RNG.uniform(-3.0, 3.0)))
    ge = G(f"eclat{k + 1}", p0, SPIN)
    tm = G(f"roule_eclat{k + 1}", p0, ge)
    t = 1.5 + 1.8 * RNG.uniform() ** 1.5
    bloc(tm, f"pierre{k + 1}", p0, (t, t * RNG.uniform(0.55, 0.85), t * RNG.uniform(0.45, 0.75)), UV[f"pierre{k % 3}"], RNG.uniform(-40, 40, 3))
    bloc(tm, f"pierre{k + 1}b", p0 + RNG.uniform(-0.45, 0.45, 3) * t, (t * 0.62, t * 0.48, t * 0.7), UV[f"pierre{(k + 1) % 3}"], RNG.uniform(-50, 50, 3))
    bloc(tm, f"pierre{k + 1}c", p0 + RNG.uniform(-0.4, 0.4, 3) * t, (t * 0.4, t * 0.65, t * 0.38), UV[f"pierre{(k + 2) % 3}"], RNG.uniform(-60, 60, 3))
    ECLATS.append((ge, tm, k))

# --- fermeture : trois anneaux inclinés (gyroscope) qui se resserrent en tournant
GYRO = G("gyro", C, PORTAIL)
ANNEAUX = []
for k, rot in enumerate(((72, 0, 28), (62, 0, -40), (-16, 0, 95))):
    ak = G(f"anneau{k + 1}", C, GYRO, rotation=rot)
    sk = G(f"tourne_anneau{k + 1}", C, ak)
    dk = G(f"add_anneau{k + 1}", C, sk)
    ALPHA[f"gyro{k}"] = G("ctrl_alpha", C, dk)
    plaque(dk, f"anneau{k + 1}", C, 2 * 1.25 * R, 2 * 1.25 * R, UV["gyro"], ep=0.15 + 0.1 * k)
    ANNEAUX.append((ak, sk))

# --- points de départ des particules (+Y du groupe = direction de départ), chacun avec son ctrl_emit
EMITS, CTRL = [], {}


def emit(nom, pos, sorte, parent, rot=None):
    ge = G(nom, pos, parent, rotation=rot)
    CTRL.setdefault(sorte, []).append(G("ctrl_emit", pos, ge))
    EMITS.append((ge, sorte))


for k in range(8):
    a = math.radians(22.5 + 45 * k)
    emit("emit_etincelle" + (str(k + 1) if k else ""), (15.6 * math.cos(a), YC + 15.6 * math.sin(a), ZP), "etincelle", OUVRE)
for k in range(4):
    a = math.radians(90 * k + 15)
    emit("emit_rune" + (str(k + 1) if k else ""), (RR * math.cos(a), YC + RR * math.sin(a), ZP), "rune", TRU)
for k, (dx, dy) in enumerate(((-3, 3), (3, -3), (-2, -4), (2, 4))):
    emit("emit_poussiere" + (str(k + 1) if k else ""), (dx, YC + dy, ZP), "poussiere", PORTAIL)
for pos in ((-17, YC, ZP), (17, YC, ZP), (0, YC + 27, ZP)):
    emit("emit_mc_portal", pos, "portal", PORTAIL)
for dz in (-0.6, 0.6):
    emit("emit_mc_reverse_portal", (0, YC, ZP + dz), "reverse", PORTAIL)
for k in range(3):
    a = math.radians(90 + 120 * k)
    emit("emit_mc_electric_spark", (15 * math.cos(a), YC + 15 * math.sin(a), ZP), "spark", OUVRE)
for dx in (-4, 4):
    emit("emit_mc_dust_7fc8ff_12", (dx, 0.6, ZP), "dust_portail", PORTAIL)
PIEDS = G("emetteurs_pieds", O, EFFET)
for dx in (-2.5, 2.5):
    emit("emit_mc_dust_7fc8ff_12", (dx, 0.6, 0), "dust_pieds", PIEDS)

# --- particules modélisées (à la racine)
PART_E = G("particle_etincelle", (0, 0, 40))
plaque(PART_E, "etincelle", (0, 0.8, 40), 0.8, 0.8, UV["etincelle"], ep=0.3, faces=("south",))
PART_R = G("particle_rune", (4, 0, 40))
plaque(PART_R, "rune_volante", (4, 0.9, 40), 1.1, 1.1, UV["p_rune"], ep=0.3, faces=("south",))
PART_P = G("particle_poussiere", (-4, 0, 40))
plaque(PART_P, "poussiere", (-4, 0.6, 40), 0.45, 0.45, UV["poussiere"], ep=0.3, faces=("south",))

outliner = [EFFET.json(), JOUEUR.json(), PART_E.json(), PART_R.json(), PART_P.json()]

# ------------------------------------------------------------------ animations
def s(v):
    return v if isinstance(v, str) else str(round(v + 0.0, 4))


def kf(ch, t, x, y, z, interp="linear"):
    return {"channel": ch, "data_points": [{"x": s(x), "y": s(y), "z": s(z)}], "time": round(t, 4), "interpolation": interp}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def step(t, t0):
    return 1.0 if t >= t0 else 0.0


def net(v, seuil=0.06):
    return v if v >= seuil else 0.0


def ressort(t, t0, amp, f=5.0, k=8.0):
    if t <= t0:
        return 0.0
    u = t - t0
    return amp * math.exp(-k * u) * math.sin(2 * math.pi * f * u)


class Anim:
    def __init__(self, nom, L, loop, fps=20, extra=()):
        self.nom, self.L, self.loop, self.A = nom, L, loop, {}
        ts = set(round(i / fps, 4) for i in range(int(round(L * fps)) + 1)) | {round(L, 4)} | {round(e, 4) for e in extra if 0 <= e <= L}
        self.T = sorted(ts)

    def piste(self, g, ch, fn):
        if not callable(fn):
            keys = [kf(ch, 0, *fn)]
        else:
            vals = [fn(t) for t in self.T]
            keys = []
            for k_, (t, v) in enumerate(zip(self.T, vals)):
                if ch == "scale" and k_ and (not any(vals[k_ - 1])) != (not any(v)):
                    keys.append(kf(ch, t - 0.002, *vals[k_ - 1]))
                keys.append(kf(ch, t, *v))
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += keys

    def cacher(self, *gs):
        for g in gs:
            self.piste(g, "scale", (0, 0, 0))

    def emettre(self, sorte, fn):
        for i, c in enumerate(CTRL[sorte]):
            if callable(fn):
                self.piste(c, "position", lambda t, i=i: (max(-1.0, min(7.0, fn(t, i))), 0, 0))
            else:
                self.piste(c, "position", (fn, 0, 0))

    def son(self, t, nom):
        self.A.setdefault("effects", {"name": "Effects", "type": "effect", "keyframes": []})["keyframes"].append(
            {"channel": "sound", "data_points": [{"effect": nom, "file": ""}], "time": round(t, 4)})

    def json(self):
        return {"uuid": nuid(), "name": self.nom, "loop": self.loop, "override": False, "length": self.L, "snapping": 24,
                "selected": self.nom == "charge", "animators": self.A}


def u3(v):
    return (v, v, v)




def runes_tour(an, theta):
    """Couronne tournée de theta(t) degrés (sens horaire vu de face = z négatif), chaque rune contre-tournée."""
    an.piste(TRU, "rotation", lambda t: (0, 0, -theta(t)))
    for c in CONTRE:
        an.piste(c, "rotation", lambda t: (0, 0, theta(t)))


def eclats_roulent(an, vit=1.0):
    for ge, tm, k in ECLATS:
        wx, wy = (90 + 25 * (k % 4)) * (1 if k % 2 else -1) * vit, (60 + 20 * (k % 3)) * vit
        an.piste(tm, "rotation", lambda t, wx=wx, wy=wy: (wx * t, wy * t, 0))


def vague_runes(an, base, amp, periode, extra=lambda t, j: 0.0):
    for j in range(12):
        f = lambda t, j=j: max(-1.0, min(0.0, base + amp * (0.5 + 0.5 * math.cos(2 * math.pi * (t / periode - j / 12))) ** 3 + extra(t, j)))
        an.piste(ALPHA[f"rune{j}"], "position", lambda t, f=f: (max(-0.35, f(t)), 0, 0))
        an.piste(ALPHA[f"halo_rune{j}"], "position", lambda t, f=f: (f(t), 0, 0))


def frac(v):
    return v - math.floor(v)


def portail_vivant(an, deep, inward, t_f0, t_pt, t_ev):
    """Vie de l'ovale ouvert : couches de tourbillon à trois vitesses, tunnel qui défile (aspiré si inward), bord qui vibre, mèches
    qui vacillent, filaments qui courent et s'échappent, éclat central au fond. deep = sens du fond (-1 : -Z, +1 : +Z)."""
    acc = lambda t: t + 1.3 * (t_pt - t_f0) * sm(t, t_f0, t_pt)          # tout accélère à la fermeture
    for (lk, dz), tk, w in zip(COUCHES, TOURNE_C, (55, -90, 140)):
        an.piste(lk, "position", (0, 0, 0 if deep < 0 else -2 * dz))
        an.piste(tk, "rotation", lambda t, w=w: (0, 0, w * acc(t) + 0.35 * w * (1 - math.exp(-3 * t))))
    an.piste(TT, "rotation", lambda t: (0, 0, 25 * acc(t)))
    for k, gk in enumerate(TUNNEL):
        g = lambda t, k=k: frac(t / 1.3 + k / 6) if inward else 1 - frac(t / 1.3 + k / 6)
        an.piste(gk, "scale", lambda t, g=g: u3(1 - 0.82 * g(t) ** 0.8))
        an.piste(gk, "position", lambda t, g=g: (0, 0, deep * 7.5 * g(t)))
        an.piste(ALPHA[f"tun{k}"], "position", lambda t, g=g: (sm(g(t), 0, 0.15) * (1 - sm(g(t), 0.7, 1.0)) - 1, 0, 0))
    for cle, w in (("halo", 35), ("coeur_a", -150), ("coeur_b", 210), ("flammes_a", 120), ("flammes_b", -170)):
        an.piste(BORD[cle], "rotation", lambda t, w=w: (0, 0, w * acc(t)))
    an.piste(TB, "rotation", lambda t: (0, 0, -20 * acc(t)))
    an.piste(TM, "rotation", lambda t: (0, 0, 45 * acc(t)))
    an.piste(ALPHA["halo"], "position", lambda t: (-0.2 + 0.12 * math.sin(2 * math.pi * 2.3 * t) + 0.2 * bump(t, t_ev, t_ev + 0.08, t_ev + 0.2, t_ev + 0.6), 0, 0))
    an.piste(ALPHA["flammes_a"], "position", lambda t: (-0.18 + 0.15 * math.sin(2 * math.pi * 3.1 * t), 0, 0))
    an.piste(ALPHA["flammes_b"], "position", lambda t: (-0.18 + 0.15 * math.sin(2 * math.pi * 2.6 * t + 1.7), 0, 0))
    for gj, f1, f2, p1, p2 in MECHES:
        an.piste(gj, "scale", lambda t, f1=f1, f2=f2, p1=p1, p2=p2: (1, 0.3 + 0.8 * (0.5 + 0.5 * math.sin(2 * math.pi * f1 * t + p1))
                                                                         * (0.6 + 0.4 * math.sin(2 * math.pi * f2 * t + p2)), 1))
    for k, (gk, sp, per, ph) in enumerate(FILS):
        vis = lambda t, per=per, ph=ph: max(0.0, math.sin(2 * math.pi * t / per + ph)) ** 2
        an.piste(gk, "rotation", lambda t, sp=sp: (0, 0, 70 * sp * acc(t)))
        an.piste(gk, "scale", lambda t, vis=vis: u3(1 + 0.1 * vis(t)))
        an.piste(ALPHA[f"fil{k}"], "position", lambda t, vis=vis: (vis(t) - 1, 0, 0))
    an.piste(CAM_ET, "rotation", lambda t: (0, 0, 40 * t))


def coeur_fond(an, deep, ouv, t_f0, t_pt, t_flare=-9.0):
    an.piste(COEUR, "position", lambda t: (0, 0, deep * 6.5 * (1 - sm(t, t_f0, t_pt))))
    an.piste(COEUR, "scale", lambda t: u3(net(ouv(t) * (0.9 + 0.1 * math.sin(2 * math.pi * 1.7 * t)) * (1 + 0.8 * sm(t, t_f0, t_pt - 0.1) + 0.9 * bump(t, t_flare - 0.08, t_flare, t_flare + 0.05, t_flare + 0.35))
                                              * (1 - step(t, t_pt)), 0.05)))


def gyro_ferme(an, t_g0, t_pt):
    """Anneaux inclinés qui apparaissent autour de l'ovale qui se contracte et se resserrent en tournant jusqu'au point."""
    an.piste(GYRO, "rotation", lambda t: (0, 220 * max(0.0, t - t_g0) + 260 * sm(t, t_g0, t_pt), 0))
    for k, (ak, sk) in enumerate(ANNEAUX):
        an.piste(sk, "rotation", lambda t, k=k: (0, 0, (520 + 140 * k) * (1 if k % 2 else -1) * max(0.0, t - t_g0)))
        an.piste(ak, "scale", lambda t: u3(net((1.2 * (1 - lin(t, t_g0, t_pt)) ** 1.3) * step(t, t_g0) * (1 - step(t, t_pt)), 0.04)))
        an.piste(ALPHA[f"gyro{k}"], "position", lambda t, k=k: (sm(t, t_g0 + 0.03 * k, t_g0 + 0.15 + 0.03 * k) - 1, 0, 0))


def gyro_ouvre(an, t0, t1):
    """Arrivée : les anneaux s'écartent depuis le flash et s'effacent."""
    an.piste(GYRO, "rotation", lambda t: (0, -260 * lin(t, t0, t1) - 60 * t, 0))
    for k, (ak, sk) in enumerate(ANNEAUX):
        an.piste(sk, "rotation", lambda t, k=k: (0, 0, (480 + 120 * k) * (1 if k % 2 else -1) * t))
        an.piste(ak, "scale", lambda t: u3(net((0.15 + 1.25 * (1 - (1 - lin(t, t0, t1)) ** 2)) * step(t, t0) * (1 - step(t, t1)), 0.04)))
        an.piste(ALPHA[f"gyro{k}"], "position", lambda t, k=k: (sm(t, t0, t0 + 0.06) * (1 - sm(t, t0 + 0.2 + 0.04 * k, t1)) - 1, 0, 0))


def ovale(ox, oy):
    ox, oy = net(ox, 0.03), net(oy, 0.03)
    return (0, 0, 0) if ox == 0 or oy == 0 else (ox, oy * E, 1)


# ---- charge (loop 12 s) : runes en cercle devant le joueur (tournent 1 tour, vague de lumière toutes les 1,5 s), fente qui palpite
LC = 12.0
an = Anim("charge", LC, "loop", fps=10)
an.piste(CADRE, "scale", (1, ER, 1))
runes_tour(an, lambda t: 30 * t)
vague_runes(an, -0.5, 0.5, 1.5)
an.piste(FENTE, "scale", lambda t: (1 + 0.4 * (0.5 + 0.5 * math.sin(2 * math.pi * t / 0.75)), 0.3 + 0.08 * math.sin(2 * math.pi * t / 1.5)
                                     + 0.04 * math.sin(2 * math.pi * t / 0.5), 1))
an.piste(SOL, "scale", lambda t: (0.7 + 0.08 * math.sin(2 * math.pi * t / 1.5), 1, 0.7 + 0.08 * math.sin(2 * math.pi * t / 1.5)))
an.cacher(OUVRE, ORBITE, FLASH, GYRO, COEUR)
an.emettre("etincelle", -0.4)
an.emettre("rune", lambda t, i: -0.5 + 0.5 * math.sin(2 * math.pi * (t / 3 + i / 4)))
an.emettre("portal", 0)
for s_ in ("poussiere", "reverse", "spark", "dust_portail", "dust_pieds"):
    an.emettre(s_, -1)
charge = an.json()


# ---- depart (once 4 s) : déchirure, éclat, l'ovale s'ouvre et s'étire ; le joueur marche, traverse le plan, est aspiré ;
#      l'ovale se contracte, les anneaux se resserrent, point de lumière
LD = 3.8
T_FE, T_OUV, T_F0, T_G0, T_PT = 0.02, 0.3, 2.45, 2.62, 3.25
EX = [T_PT - 0.01, T_PT, T_PT + 0.02, LD - 0.05, LD - 0.04]
an = Anim("depart", LD, "once", fps=30, extra=EX)


# joueur : marche vers le portail (départ adouci), traverse le plan sans s'arrêter, aspiré de plus en plus vite.
# Mod 1.4.0 : la copie du départ suit la position seulement (taille 1, échelle ignorée, cachée sous 0,05) : elle disparaît en
# touchant le plan : coupée quand l'avant de la tête l'a passé de 1,5 px (T_HIDE ; vue de l'autre côté, rien ne ressort), sous l'onde et l'éclat du tunnel ; clés d'échelle monotones 1 -> 0.
T_TOUCHE = 1.53                                   # l'avant de la tête touche le plan


def j_dist(t):
    tau, a, v = t - 0.75, 0.3, 8.0
    if tau <= 0:
        return 0.0
    d = v * tau * tau / (2 * a) if tau < a else v * a / 2 + v * (tau - a)
    return d + 0.5 * 34.0 * max(0.0, t - T_TOUCHE) ** 2


T_HIDE = next(i / 1000 for i in range(1000, 3000) if j_dist(i / 1000) >= -ZP - 2.5)   # l'avant de la tête a passé le plan de 1,5 px
T_PAS = T_HIDE - 0.05


def j_s(t):
    return 1 - lin(t, T_HIDE - 0.12, T_HIDE) ** 2


def j_pos(t):
    pas = 0.35 * math.sin(math.pi * 3.6 * max(0.0, t - 0.75)) ** 2 * lin(t, 0.75, 0.9) * (1 - lin(t, T_TOUCHE - 0.1, T_TOUCHE + 0.1))
    return (0, pas, -j_dist(t))


fy_d = lambda t: 1 - (1 - lin(t, T_FE, 0.28)) ** 2                         # la fente se trace (sort d'un élan, ralentit)


def ouv_d(t):
    """Ouverture (0..1) : la fente, puis l'ovale qui s'écarte avec dépassement, puis la fermeture."""
    if t < T_FE:
        return 0.0
    return min(1.0, fy_d(t)) * (1 - lin(t, T_F0, T_PT) ** 2.0)


def ovale_d(t):
    if t < T_FE or t >= T_PT:
        return (0, 0, 0)
    u = lin(t, T_F0, T_PT)
    puls = 1 + 0.06 * bump(t, T_HIDE - 0.1, T_HIDE, T_HIDE + 0.05, T_HIDE + 0.45)
    ox = (0.07 + 0.93 * amorti(t - T_OUV, 6.0, 1.4)) * (1 - u ** 1.6) * puls
    oy = fy_d(t) * (1 + 0.14 * math.sin(math.pi * lin(t, T_OUV, 1.0)) ** 2) * (1 - u ** 2.4) * puls
    return ovale(ox, oy)


an.piste(OUVRE, "scale", ovale_d)
portail_vivant(an, -1, True, T_F0, T_PT, T_OUV)
coeur_fond(an, -1, lambda t: lin(t, T_OUV, T_OUV + 0.5), T_F0, T_PT, T_HIDE)
gyro_ferme(an, T_G0, T_PT)
an.piste(ONDE, "scale", lambda t: u3(net(step(t, T_HIDE - 0.03) * (0.3 + 1.0 * sm(t, T_HIDE - 0.03, T_HIDE + 0.42)) * (1 - step(t, T_HIDE + 0.47)))))
an.piste(ALPHA["onde"], "position", lambda t: (-sm(t, T_HIDE + 0.07, T_HIDE + 0.45), 0, 0))
an.piste(FENTE, "scale", lambda t: (0, 0, 0) if t >= 0.6 or t < T_FE else (1 + 0.25 * math.sin(2 * math.pi * 6 * t) + 2.5 * sm(t, T_OUV, 0.6), max(0.02, fy_d(t)), 1))
an.piste(FLASH, "scale", lambda t: u3(net(0.6 * bump(t, T_OUV - 0.08, T_OUV, T_OUV + 0.04, T_OUV + 0.3)
                                          + step(t, T_PT) * (1.25 if t < T_PT + 0.04 else 1.0) * (1 - sm(t, T_PT + 0.04, T_PT + 0.45)), 0.08)))
an.piste(CAM_FL, "rotation", lambda t: (0, 0, 90 * t))
an.piste(SOL, "scale", lambda t: (lambda v: (v, 1, v))(net(0.7 + 0.4 * sm(t, T_OUV, T_OUV + 0.4) + 0.2 * bump(t, T_PAS, T_PAS + 0.1, T_PAS + 0.2, T_PAS + 0.7)
                                                       - 1.1 * sm(t, T_F0, T_PT), 0.08)) if t < T_PT else (0, 0, 0))
an.piste(CADRE, "scale", lambda t: (lambda c: (c, c * ER, 1) if c else (0, 0, 0))(net((1 + 0.12 * bump(t, T_OUV, T_OUV + 0.1, T_OUV + 0.2, T_OUV + 0.6)) * (1 - sm(t, T_F0 - 0.05, T_PT - 0.1)))))
runes_tour(an, lambda t: 30 * t + 160 * sm(t, T_OUV, T_OUV + 0.8) + 520 * sm(t, T_F0 - 0.1, T_PT))
vague_runes(an, -0.5, 0.5, 1.5, extra=lambda t, j: 0.6 * sm(t, T_OUV - 0.1, T_OUV + 0.1))
an.piste(ORBITE, "scale", lambda t: (lambda o: (o, o * 1.12, o) if o else (0, 0, 0))(net(sm(t, T_OUV, T_OUV + 0.6) * (1 - sm(t, T_F0, T_PT - 0.1)), 0.06)))
an.piste(ORBITE, "position", lambda t: (0, -20 * (1 - sm(t, T_OUV, T_OUV + 0.7)), 0))
an.piste(SPIN, "rotation", lambda t: (0, 0, -(40 * t + 200 * (1 - math.exp(-2.5 * max(0.0, t - T_OUV))) + 420 * sm(t, T_F0, T_PT))))
eclats_roulent(an)


an.piste(JOUEUR, "position", j_pos)
an.piste(JOUEUR, "scale", lambda t: u3(net(j_s(t), 0.05)))
an.piste(EFFET, "scale", lambda t: u3(1 - step(t, LD - 0.04)))
fin = lambda t: 1 - step(t, 3.6)
an.emettre("etincelle", lambda t, i: (-1 + 6 * bump(t, T_OUV, T_OUV + 0.03, T_OUV + 0.3, T_OUV + 0.6) + 0.9 * bump(t, T_OUV + 0.4, T_OUV + 0.6, T_F0, T_F0 + 0.1)
                                      + 3 * bump(t, T_PAS, T_PAS + 0.05, T_PAS + 0.25, T_PAS + 0.45)) * fin(t) - (1 - fin(t)))
an.emettre("rune", lambda t, i: (-0.3 + 1.2 * bump(t, T_OUV, T_OUV + 0.2, T_F0 - 0.3, T_F0)) * fin(t) - (1 - fin(t)) if t < T_PT - 0.1 else -1)
an.emettre("portal", lambda t, i: (0.5 + 1.5 * bump(t, T_OUV, T_OUV + 0.2, T_F0, T_F0 + 0.2)) if t < T_PT else -1)
an.emettre("poussiere", lambda t, i: -1 + 8 * bump(t, T_PT, T_PT + 0.02, T_PT + 0.2, T_PT + 0.4) + 6 * bump(t, T_HIDE - 0.03, T_HIDE, T_HIDE + 0.15, T_HIDE + 0.3))
an.emettre("reverse", lambda t, i: -1 + 5 * bump(t, T_OUV, T_OUV + 0.02, T_OUV + 0.2, T_OUV + 0.35) + 7 * bump(t, T_PT, T_PT + 0.02, T_PT + 0.2, T_PT + 0.35))
an.emettre("spark", lambda t, i: -1 + 4 * bump(t, T_FE, T_FE + 0.02, T_OUV + 0.1, T_OUV + 0.3) + 4 * bump(t, T_PAS, T_PAS + 0.05, T_PAS + 0.2, T_PAS + 0.35)
           + 1.2 * bump(t, T_OUV + 0.3, T_OUV + 0.5, T_F0 - 0.2, T_F0))
an.emettre("dust_portail", lambda t, i: -1 + 5 * bump(t, T_OUV, T_OUV + 0.03, T_OUV + 0.3, T_OUV + 0.55))
an.emettre("dust_pieds", -1)
an.son(0.0, "portail_ouvre")
an.son(T_HIDE - 0.1, "portail_passe")
an.son(T_PT - 0.45, "portail_ferme")        # le « whoum » du son tombe sur le point de lumière
depart = an.json()


# ---- arrivee (once 3,6 s) : flash, anneaux qui s'écartent, l'ovale s'ouvre derrière le joueur ; il sort du plan, avance et s'arrête ;
#      fermeture en anneaux
LA = 3.6
A_OUV, A_SORT, A_STOP, A_F0, A_G0, A_PT = 0.15, 0.55, 1.9, 2.25, 2.45, 3.05
EX = [A_PT - 0.01, A_PT, A_PT + 0.02, LA - 0.05, LA - 0.04]
an = Anim("arrivee", LA, "once", fps=30, extra=EX)
an.piste(PORTAIL, "position", (0, 0, DZ_ARR))


def ovale_a(t):
    if t < A_OUV or t >= A_PT:
        return (0, 0, 0)
    u = lin(t, A_F0, A_PT)
    puls = 1 + 0.05 * bump(t, A_SORT, A_SORT + 0.1, A_SORT + 0.15, A_SORT + 0.55)
    ox = (0.25 + 0.75 * amorti(t - A_OUV, 6.0, 1.4)) * (1 - u ** 1.6) * puls
    oy = (0.16 + 0.84 * amorti(t - A_OUV - 0.03, 5.5, 1.2)) * (1 - u ** 2.4) * puls
    return ovale(ox, oy)


an.piste(OUVRE, "scale", ovale_a)
portail_vivant(an, 1, False, A_F0, A_PT, A_OUV)
coeur_fond(an, 1, lambda t: lin(t, A_OUV, A_OUV + 0.4), A_F0, A_PT, A_SORT)
an.cacher(FENTE)
gyro_ouvre(an, 0.03, 0.6)
an.piste(ONDE, "scale", lambda t: u3(net(step(t, A_SORT) * (0.3 + 1.0 * sm(t, A_SORT, A_SORT + 0.45)) * (1 - step(t, A_SORT + 0.5)))))
an.piste(ALPHA["onde"], "position", lambda t: (-sm(t, A_SORT + 0.1, A_SORT + 0.48), 0, 0))
an.piste(FLASH, "scale", lambda t: u3(net(bump(t, 0.0, 0.08, 0.18, 0.4) * (0.6 + 0.6 * sm(t, 0, 0.2))
                                          + step(t, A_PT) * (1.2 if t < A_PT + 0.04 else 0.9) * (1 - sm(t, A_PT + 0.04, A_PT + 0.45)), 0.08)))
an.piste(CAM_FL, "rotation", lambda t: (0, 0, 90 * t))
an.piste(SOL, "scale", lambda t: (lambda v: (v, 1, v))(net(sm(t, A_OUV, A_OUV + 0.4) * 1.1 + 0.2 * bump(t, A_SORT, A_SORT + 0.1, A_SORT + 0.2, A_SORT + 0.7)
                                                           - 1.3 * sm(t, A_F0, A_PT), 0.08)))
an.piste(CADRE, "scale", lambda t: (lambda c: (c, c * ER, 1) if c else (0, 0, 0))(net((sm(t, A_OUV, A_OUV + 0.4) + ressort(t, A_OUV + 0.35, 0.07, 3, 6)) * (1 - sm(t, A_F0 - 0.05, A_PT - 0.1)))))
runes_tour(an, lambda t: 30 * t + 330 * (1 - math.exp(-3.5 * max(0.0, t - A_OUV))) + 520 * sm(t, A_F0 - 0.1, A_PT))
vague_runes(an, -0.5, 0.5, 1.5, extra=lambda t, j: 0.6 * bump(t, A_OUV + 0.1 + 0.02 * j, A_OUV + 0.2 + 0.02 * j, A_SORT + 0.3, A_SORT + 0.8))
an.piste(ORBITE, "scale", lambda t: (lambda o: (o, o * 1.12, o) if o else (0, 0, 0))(net(sm(t, A_OUV + 0.05, A_OUV + 0.5) * (1 - sm(t, A_F0, A_PT - 0.1)), 0.06)))
an.piste(SPIN, "rotation", lambda t: (0, 0, -(40 * t + 240 * (1 - math.exp(-2.5 * max(0.0, t - A_OUV))) + 420 * sm(t, A_F0, A_PT))))
eclats_roulent(an)


def ja_s(t):
    return 1 - (1 - lin(t, A_SORT, 1.15)) ** 2                           # grandit en sortant du plan, sans à-coup à la fin


def ja_pos(t):
    s_ = ja_s(t)
    z = (ZP + DZ_ARR + 4.0) * (1 - lin(t, A_SORT, A_STOP)) ** 2          # éjecté du plan, ralentit jusqu'à l'arrêt
    return (0, YC * (1 - s_), z)


an.piste(JOUEUR, "position", ja_pos)
an.piste(JOUEUR, "scale", lambda t: u3(net(ja_s(t), 0.05)))
an.piste(EFFET, "scale", lambda t: u3(1 - step(t, LA - 0.04)))
fin = lambda t: 1 - step(t, 3.4)
an.emettre("etincelle", lambda t, i: (-1 + 6 * bump(t, A_OUV, A_OUV + 0.03, A_OUV + 0.3, A_OUV + 0.6) + 0.9 * bump(t, A_OUV + 0.4, A_OUV + 0.6, A_F0, A_F0 + 0.1)
                                      + 3 * bump(t, A_SORT, A_SORT + 0.05, A_SORT + 0.25, A_SORT + 0.45)) * fin(t) - (1 - fin(t)))
an.emettre("rune", lambda t, i: (-0.3 + 1.2 * bump(t, A_OUV, A_OUV + 0.2, A_F0 - 0.3, A_F0)) if t < A_PT - 0.1 else -1)
an.emettre("portal", lambda t, i: (0.5 + 1.5 * bump(t, A_OUV, A_OUV + 0.2, A_F0, A_F0 + 0.2)) if t < A_PT else -1)
an.emettre("poussiere", lambda t, i: -1 + 8 * bump(t, A_PT, A_PT + 0.02, A_PT + 0.2, A_PT + 0.4) + 5 * bump(t, 0.0, 0.02, 0.15, 0.3))
an.emettre("reverse", lambda t, i: -1 + 7 * bump(t, 0.02, 0.04, 0.2, 0.35) + 7 * bump(t, A_PT, A_PT + 0.02, A_PT + 0.2, A_PT + 0.35))
an.emettre("spark", lambda t, i: -1 + 4 * bump(t, A_OUV, A_OUV + 0.02, A_OUV + 0.15, A_OUV + 0.3) + 4 * bump(t, A_SORT, A_SORT + 0.05, A_SORT + 0.2, A_SORT + 0.35)
           + 1.2 * bump(t, A_OUV + 0.3, A_OUV + 0.5, A_F0 - 0.2, A_F0))
an.emettre("dust_portail", lambda t, i: -1 + 3 * bump(t, A_OUV, A_OUV + 0.03, A_OUV + 0.3, A_OUV + 0.55))
an.emettre("dust_pieds", lambda t, i: -1 + 6 * bump(t, 1.12, 1.15, 1.3, 1.5))
an.son(0.0, "portail_ouvre")
an.son(A_SORT, "portail_passe")
an.son(A_PT - 0.45, "portail_ferme")
arrivee = an.json()

# ---- animations des particules (guide 5 ter §3)
def anim_particule(nom, L, g, rot=None, pulse=None):
    a_ = Anim(nom, L, "loop", fps=16)
    if rot:
        a_.piste(g, "rotation", lambda t: tuple(r * 360 * t / L for r in rot))
    if pulse:
        a_.piste(g, "scale", lambda t: u3(1 + pulse * max(0.0, math.sin(2 * math.pi * t / L)) ** 3))
    return a_.json()


p_et = anim_particule("particle_etincelle_fall", 0.6, PART_E, rot=(0, 0, 1), pulse=0.8)
p_ru = anim_particule("particle_rune_fall", 3.0, PART_R, rot=(0, 1, 0))
p_po = anim_particule("particle_poussiere_fall", 0.5, PART_P, pulse=0.6)

ANIMS = [charge, depart, arrivee, p_et, p_ru, p_po]
assert len(EMITS) <= 32, len(EMITS)
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures,
         "animations": ANIMS}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
embarquer_sons(model, {n: f"sons/{n}.ogg" for n in ("portail_ouvre", "portail_passe", "portail_ferme")})
limiter_sons(model, max_effet=3)                          # effet : une étape physique = un son (ouverture, passage, fermeture)
for a_ in ANIMS:
    eff = a_["animators"].get("effects")
    assert not eff or len(eff["keyframes"]) <= 3, a_["name"]
    assert a_["name"] != "charge" or not eff

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
