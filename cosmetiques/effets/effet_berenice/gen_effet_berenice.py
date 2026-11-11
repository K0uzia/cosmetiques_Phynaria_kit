"""Effet de téléportation de Bérénice, v2 (guide 15) : le joueur est rappelé au ciel dans un cocon d'ailes de lumière qui éclate
en plumes, et en redescend ailes ouvertes. Design original (ensemble Bérénice, thème Divin, fiche .claude/styles/berenice.md).
Écrit effet_berenice.png et .build/effet_berenice_brut.bbmodel.

Retour v1 : « ça manque un peu de visuel de particules et d'animation » ; consigne : « être imaginatif et s'inspirer des animes ».

Design
- Cercle au sol (rayon 15 px, repris de la v1) : huit arcs `add_`, rosace, couches qui tournent en sens contraire (overlay_cercle),
  et huit étoiles `cam_` qui scintillent sur la constellation de chaque arc.
- Ailes de lumière : deux ailes `add_` (bras + main, 15 rémiges de lumière dorée par aile), qui jaillissent du dos au départ,
  se referment en cocon devant le joueur, et portent le joueur à l'arrivée. Lueur de cocon `cam_` devant lui.
- Colonne `camy_` (v1, plus claire et plus large au moment fort), six rayons qui tournent autour d'elle (vortex), traits de lumière
  qui filent, anneaux qui la parcourent, onde de choc (anneau horizontal qui s'élargit), éclat d'étoile `cam_`.
- Ciel ouvert (arrivée) : cercle magique horizontal à y = 50 (anneau d'étoiles + rosace), qui s'ouvre et tourne.
- Seize plumes ivoire opaques modélisées (recette de la plume-particule des ailes, « ok » en jeu), en gerbe et en spirale.
- Particules (guide 5 ter, émises tant que l'effet joue ; cadence animée par ctrl_emit, −1 coupé à +7) : plume (tombe en
  tournoyant), etoile (poussière d'or qui monte du cercle), etincelle (gerbes à l'éclat et à l'atterrissage), lueur (poussière de
  lumière qui monte dans la colonne), et emit_mc_dust_ffd27a_10 (poussière dorée de Minecraft).

Animations (anticipation → moment fort → dissipation)
- charge (loop 3 s, le compte à rebours du mod ; 4 s avant : la pose sautait au départ) : cercle qui respire, étoiles qui scintillent, anneaux qui montent du cercle, lueur basse qui pulse, six plumes
  en spirale ; poussière d'or et de lumière en continu. Tout est périodique : la boucle se referme sans s'éteindre.
- depart (once 3,6 s) : les ailes jaillissent du dos et s'ouvrent (0–0,5 s, le cercle se contracte puis s'embrase), se referment en
  cocon (0,5–1,1), le cocon flotte et s'illumine, la colonne et le vortex de rayons montent (1,1–1,3), le cocon s'élève en
  accélérant (1,3–2,1) et éclate : éclair, onde de choc, gerbe de seize plumes et d'étincelles, la copie du joueur disparaît ;
  les plumes retombent en tournoyant, la colonne s'amincit et monte, le cercle s'éteint. Son embarqué envol_celeste.
- arrivee (once 4,5 s) : le ciel s'ouvre (cercle magique à y = 50, éclair), la colonne et les rayons descendent, le joueur
  descend de y = 150 ; ailes de lumière ouvertes autour de lui dès y ≈ 22, battement lent ; le cercle se trace au sol ; il se
  pose à 3,0 s : les ailes se dissipent en plumes, onde dorée au sol, gerbe d'étincelles ; tout s'efface. Son descente_celeste.
- overlay_cercle (48 s) : rotation des couches du cercle.

Lumière (leçon aura_berenice) : tout en add_, sans calque _e, palette arrêtée à l'or clair, cumul additif mesuré sans plafond
(.build/cumul.py). Plumes opaques ivoire. Fonctions : add_, cam_, camy_, ctrl_alpha, ctrl_emit, particle_/emit_, emit_mc_dust,
overlay_, groupe joueur, sons embarqués. À juger en jeu : particules et leur cadence, ctrl_alpha (fondus), additif de jour,
faces simples des ailes vues de dos (supposées dessinées des deux côtés en add_), avec shader.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "effet_berenice"
TEX = 512
SS = 4

# ------------------------------------------------------------------ palette « Lumière divine » (or clair, jamais blanc pur)
STOPS = [(0.0, (0, 0, 0)), (0.15, (30, 20, 6)), (0.35, (95, 66, 22)), (0.6, (180, 130, 50)),
         (0.85, (235, 198, 124)), (1.0, (250, 226, 168))]


def palette(f):
    f = np.clip(f, 0, 1)
    xs = [s_[0] for s_ in STOPS]
    return np.stack([np.interp(f, xs, [s_[1][c] for s_ in STOPS]) for c in range(3)], axis=-1)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def lerp(a, b, k):
    return a + (b - a) * k


def reduire(f, W, H, gain, cutout=False):
    """f : intensité sur-échantillonnée (H*SS, W*SS). Image RGBA, alpha 0/255, presque noir transparent."""
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


def grille(W, H):
    """Coordonnées -1..1 (x vers la droite, y vers le haut de l'image)."""
    n_w, n_h = W * SS, H * SS
    return np.meshgrid((np.arange(n_w) + 0.5) / n_w * 2 - 1, 1 - (np.arange(n_h) + 0.5) / n_h * 2)


def etoile4(x, y, cx, cy, R, w=0.18):
    u, v = (x - cx) / R, (y - cy) / R
    d = np.abs(u) ** 0.5 + np.abs(v) ** 0.5
    return np.clip((1.0 - d) / w, 0, 1) ** 0.8


def segment(x, y, a, b, w):
    """Intensité d'un filet droit de a à b (demi-largeur w), mêmes unités que x, y."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    t = np.clip(((x - a[0]) * d[0] + (y - a[1]) * d[1]) / (d @ d), 0, 1)
    dist = np.hypot(x - a[0] - t * d[0], y - a[1] - t * d[1])
    return np.exp(-(dist / w) ** 2)


# ------------------------------------------------------------------ dimensions (px)
RO = 18.0                     # rayon extérieur du cercle (2,25 blocs de diamètre ; 15 en v2, trop petit en jeu)
A8 = math.radians(45)
WX, WZ = RO + 0.1, (RO + 0.1) * math.sin(A8)      # boîte d'un arc (x de 0 à WX, z de 0 à WZ)
RC = 10.0                     # demi-côté de la rosace
HC = 56.0                     # hauteur de la colonne
G_ARC, G_CEN, G_GLOW, G_CORE, G_VOILE, G_FIL, G_ANN, G_ECL = 0.20, 0.16, 0.22, 0.22, 0.10, 0.24, 0.14, 0.32


def bande(r, r0, hw, bord=0.1):
    """Filet plein de demi-largeur hw (px) autour du rayon r0, bord adouci sur 0,1 px."""
    return smooth((hw - np.abs(r - r0)) / bord + 0.5)


def disque(x, y, cx, cy, R, bord=0.1):
    return smooth((R - np.hypot(x - cx, y - cy)) / bord + 0.5)


# Retour en jeu du 2026-11-06 (« souci sur les cercles magiques ») : traits de 3–5 texels et additif sombre, effacés en jeu
# (mipmaps d'une plaque vue en biais, sol clair de jour). Cercle v3 : filets pleins de 8 à 17 texels, glyphes gros et simples,
# peints en trans_ or (visible de jour) + calque _e (de nuit), avec une lueur add_ douce et basse résolution par-dessus.
YG = 14.1                     # rayon de la bande des glyphes
RE = 18.0                     # demi-côté de la plaque du cercle extérieur


def cercle_f(N):
    """Cercle extérieur ENTIER sur une plaque carrée de 2·RE px (centre au milieu), motif invariant par miroir x, miroir z
    et transposition : l'orientation de l'UV d'une face up/down (non calibrée en jeu) ne peut pas le déformer.
    Retour en jeu du 2026-11-06 (v3 en 8 arcs : « nid » de courbes, arcs supposés retournés dans leur boîte)."""
    x, y = grille(N, N)
    x, y = x * RE, y * RE
    r = np.hypot(x, y)
    f = np.maximum.reduce([bande(r, 17.25, 0.42), 0.9 * bande(r, 16.15, 0.26), 0.9 * bande(r, 12.0, 0.3)])
    for k in range(8):                                   # huit grosses étoiles à 22,5° + 45°·k
        ak = math.radians(22.5 + 45 * k)
        e = etoile4(x, y, YG * math.cos(ak), YG * math.sin(ak), 1.55, 0.3)
        f = np.maximum(f, e ** 0.5 * (e > 0.12))
    for k in range(16):                                  # seize points à 8° + 45°·k et 37° + 45°·k (symétriques entre eux)
        ak = math.radians((8.0 if k % 2 == 0 else 37.0) + 45 * (k // 2))
        f = np.maximum(f, 0.95 * disque(x, y, YG * math.cos(ak), YG * math.sin(ak), 0.38))
    return np.clip(f, 0, 1) * (r < RE - 0.05) * (r > 11.2)


def rosace_f(N):
    x, y = grille(N, N)
    x, y = x * RC, y * RC
    r, a = np.hypot(x, y), np.arctan2(y, x)
    f = np.maximum(bande(r, 9.3, 0.45), 0.9 * bande(r, 4.2, 0.3))
    for k in range(8):                                    # huit rayons épais et effilés
        ak = k * math.pi / 4
        d = np.abs(r * np.sin(a - ak))
        le = r * np.cos(a - ak)
        t = np.clip((le - 4.6) / (8.6 - 4.6), 0, 1)
        f = np.maximum(f, 0.9 * smooth(((0.36 - 0.22 * t) - d) / 0.1 + 0.5) * (le > 4.5) * (le < 8.7))
    e = etoile4(x, y, 0, 0, 3.0, 0.3)
    f = np.maximum(f, e ** 0.5 * (e > 0.12))
    for k in range(8):                                    # nœuds pleins sur le grand filet
        ak = k * math.pi / 4 + math.pi / 8
        f = np.maximum(f, disque(x, y, 9.3 * math.cos(ak), 9.3 * math.sin(ak), 0.6))
    return np.clip(f, 0, 1) * (r < RC - 0.1)


def trace_or(f, W, H):
    """Version trans_ : or semi-opaque (alpha ≤ 230), cœur des filets plus clair. RGBA, alpha 0 ou 1–230."""
    pale, or_ = np.array((252, 228, 160), float), np.array((226, 172, 70), float)
    col = or_ + (pale - or_) * np.clip((f - 0.5) * 2, 0, 1)[..., None]
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(float)
    al = np.where(al < 20, 0, np.clip(al * 0.9, 1, 230)).astype(np.uint8)
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = al
    out[al == 0, :3] = 0
    return out


def lueur_douce(f, W, H, gain, flou=2.0):
    """Version add_ : la même forme floutée, réduite (basse résolution : rien de fin à perdre aux mipmaps)."""
    from PIL import ImageFilter
    im = Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)
    g = np.array(im.filter(ImageFilter.GaussianBlur(flou))).astype(float) / 255
    g = np.clip(g * 1.6, 0, 1)
    rgb = palette(0.35 + 0.6 * g) * gain * g[..., None] / np.maximum(g[..., None], 1e-6) * np.clip(g * 1.3, 0, 1)[..., None]
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    lum = arr[..., :3].max(axis=2)
    arr[..., 3] = (lum > 10) * 255
    arr[lum <= 10, :3] = 0
    return arr


def colonne_f(W, H, coeur=False):
    x, y = grille(W, H)
    Y = (y + 1) / 2                                       # 0 = sol, 1 = haut
    v = (0.35 + 0.65 * smooth(Y / 0.12)) * (1 - Y) ** 0.55 * smooth((1 - Y) / 0.3)
    if coeur:
        return np.exp(-(x / 0.5) ** 2) * v ** 0.7
    base = np.exp(-(x / 0.62) ** 2) * smooth((1 - np.abs(x)) / 0.3)
    hair = np.zeros_like(x)
    for i, (xi, g) in enumerate(((-0.62, 0.6), (-0.41, 0.8), (-0.2, 0.7), (0.05, 0.5), (0.24, 0.8), (0.46, 0.7), (0.66, 0.55))):
        xc = xi + 0.025 * np.sin(Y * 9 + 1.7 * i)
        hair = np.maximum(hair, g * np.exp(-((x - xc) / 0.022) ** 2) * (1 - Y) ** 0.4)
    return np.clip(0.8 * base * v + 0.45 * hair * v ** 0.7 * smooth((0.95 - np.abs(x)) / 0.2), 0, 1)


def fil_f(W, H):
    x, y = grille(W, H)
    Y = (y + 1) / 2
    return np.exp(-(x / 0.4) ** 2) * np.sin(np.pi * Y) ** 1.6


def anneau_f(N):
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    f = np.maximum(np.exp(-((r - 0.86) / 0.07) ** 2), 0.06 * np.exp(-((r - 0.80) / 0.12) ** 2))   # filet épais (≥ 8 texels)
    for k in range(8):                                    # huit étoiles à 45° : motif symétrique (miroirs, transposition)
        ak = k * math.pi / 4
        f = np.maximum(f, etoile4(x, y, 0.86 * math.cos(ak), 0.86 * math.sin(ak), 0.17, 0.3))
    return np.clip(f, 0, 1) * (r < 0.98)


def eclat_f(N):
    x, y = grille(N, N)
    r = np.hypot(x, y)
    ray = lambda u, v, L, w: np.exp(-(np.abs(v) / (w * np.clip(1 - np.abs(u) / L, 0, 1) + 1e-4)) ** 2) * np.clip(1 - np.abs(u) / L, 0, 1) ** 1.4
    f = np.maximum(ray(x, y, 0.98, 0.05), ray(y, x, 0.98, 0.05))
    d1, d2 = (x + y) / math.sqrt(2), (x - y) / math.sqrt(2)
    f = np.maximum(f, 0.6 * np.maximum(ray(d1, d2, 0.45, 0.03), ray(d2, d1, 0.45, 0.03)))
    f = np.maximum(f, 0.9 * np.exp(-(r / 0.13) ** 2))
    return np.clip(f, 0, 1) * smooth((1 - r) / 0.05)



def plume_l(W, H):
    """Rémige de lumière en trans_ (semi-transparente : pas de cumul additif quand les ailes se croisent), base en haut de
    l'image, pointe en bas : vexille or pâle très léger, liseré et rachis plus opaques, pointe dorée. RGBA, alpha 0 ou 1–235."""
    x, y = grille(W, H)
    t = (1 - y) / 2
    d = x * 0.5
    c = 0.05 * (np.sin(t * np.pi) - 0.5)
    v = np.clip((t - 0.03) / 0.97, 0, 1)
    env = 0.44 * np.sin(np.pi * v ** 0.8) ** 0.45
    dd = np.abs(d - c)
    rel = dd / np.maximum(env, 0.01)
    dans = (rel < 1) * smooth((1 - rel) / 0.06)
    barbe = 0.5 + 0.5 * np.sin((t * H - dd * W * 1.3) * 2 * np.pi / 7)
    rim = np.exp(-((1 - rel) / 0.13) ** 2)
    rach = np.exp(-(dd / 0.022) ** 2) * (t < 0.97)
    pointe = smooth((t - 0.7) / 0.3)
    a = dans * (0.30 + 0.08 * barbe + 0.35 * rim + 0.25 * pointe)
    a = np.maximum(a, 0.9 * rach)
    a = np.clip(a * smooth(t / 0.28), 0, 0.92)
    pale, or_ = np.array((255, 238, 196), float), np.array((236, 190, 96), float)
    k = np.clip(0.25 + 0.5 * pointe + 0.25 * (1 - rim) * dans, 0, 1)[..., None]
    col = pale * (1 - k) + or_ * k
    col = col * (1 - 0.12 * rach[..., None]) + np.array((255, 246, 222)) * 0.12 * rach[..., None]
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray((a * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(int)
    al = np.where(al < 14, 0, np.clip(al, 1, 235))
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = al
    out[al == 0, :3] = 0
    return out


def cocon_f(W, H):
    x, y = grille(W, H)
    r = np.hypot(x, y)
    return np.clip(0.8 * np.exp(-(r / 0.55) ** 2) * smooth((1 - r) / 0.25), 0, 1)


def onde_f(N):
    x, y = grille(N, N)
    r = np.hypot(x, y)
    f = np.maximum(np.exp(-((r - 0.88) / 0.06) ** 2), 0.35 * np.exp(-((r - 0.78) / 0.1) ** 2) * (r < 0.88))
    return np.clip(f, 0, 1) * (r < 0.98)


def disque_f(N, w):
    x, y = grille(N, N)
    r = np.hypot(x, y)
    return np.clip(np.exp(-(r / w) ** 2) * smooth((1 - r) / 0.2), 0, 1)


# ------------------------------------------------------------------ atlas
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)


def poser(nom, im, x, y):
    h, w = im.shape[:2]
    assert x + w <= TEX and y + h <= TEX and not tex[y:y + h, x:x + w, 3].any(), nom
    tex[y:y + h, x:x + w] = im
    UV[nom] = (x, y, x + w, y + h)


G_PL, G_COC, G_OND, G_SCI = 0.40, 0.18, 0.22, 0.30
AW, AH = 300, int(round(300 * WZ / WX))
_fa = cercle_f(212)
poser("cercle", trace_or(_fa, 212, 212), 0, 0)
poser("cercle_g", lueur_douce(_fa, 88, 88, G_ARC, 1.3), 212, 0)
poser("glow", reduire(colonne_f(64, 224), 64, 224, G_GLOW), 300, 0)
poser("voile", reduire(colonne_f(64, 224), 64, 224, G_VOILE), 364, 0)
poser("coeur", reduire(colonne_f(24, 224, coeur=True), 24, 224, G_CORE), 428, 0)
poser("fil", reduire(fil_f(8, 128), 8, 128, G_FIL), 452, 0)
poser("plume_l", plume_l(32, 128), 464, 0)
poser("cocon", reduire(cocon_f(40, 80), 40, 80, G_COC), 464, 136)
_fr = rosace_f(192)
poser("rosace", trace_or(_fr, 192, 192), 0, 224)
poser("rosace_g", lueur_douce(_fr, 96, 96, G_CEN, 1.4), 0, 416)
poser("anneau", reduire(anneau_f(128), 128, 128, G_ANN), 192, 224)
poser("onde", reduire(onde_f(128), 128, 128, G_OND), 192, 360)
poser("eclat", reduire(eclat_f(96), 96, 96, G_ECL), 320, 224)
poser("scint", reduire(eclat_f(24), 24, 24, G_SCI), 320, 324)
poser("etoile", reduire(etoile4(*grille(16, 16), 0, 0, 1.0, 0.25) * 0.85, 16, 16, 0.9, cutout=True), 416, 224)
poser("point", reduire(disque_f(16, 0.45), 16, 16, 1.0, cutout=True), 416, 240)
poser("lueur", reduire(disque_f(16, 0.6) * 0.8, 16, 16, 0.75, cutout=True), 416, 256)

# Plume ivoire à pointe dorée : image de la plume-particule des ailes de Bérénice (validée « ok »), opaque, alpha 0/255.
PLW, PLH = 40, 160
_y, _x = np.mgrid[0:PLH * SS, 0:PLW * SS]
_t_ = (_y + 0.5) / (PLH * SS)
_d = (_x + 0.5) / (PLW * SS) - 0.5
_c = 0.13 * (np.sin(_t_ * math.pi) - 0.5)
_v = np.clip((_t_ - 0.10) / 0.90, 0, 1)
_env = 0.34 * np.sin(math.pi * _v ** 0.85) ** 0.42
_dd = np.abs(_d - _c)
_a = (_dd < np.maximum(_env, 0.018 * (_t_ < 0.97)))
_col = np.empty(_a.shape + (3,), np.float32)
_col[...] = (248, 245, 234)
_col = _col * (1.0 - 0.14 * (_dd / np.maximum(_env, 0.02))[..., None] ** 2)
_col = _col * (1 + 0.03 * np.sin((_t_ * PLH - _dd * PLW * 1.4) * math.tau / 7))[..., None]
_col = lerp(_col, np.array((236, 202, 124), np.float32), smooth((_t_ - 0.78) / 0.22)[..., None] * 0.8)
_col = lerp(_col, np.array((205, 192, 165), np.float32), (_dd < 0.02)[..., None] * 0.8)
_pi = np.array(Image.fromarray(np.clip(_col, 0, 255).astype(np.uint8), "RGB").resize((PLW, PLH), Image.LANCZOS))
_pm = np.array(Image.fromarray(_a.astype(np.uint8) * 255, "L").resize((PLW, PLH), Image.LANCZOS)) > 110
_pl = np.zeros((PLH, PLW, 4), np.uint8)
_pl[..., :3] = _pi
_pl[~_pm, :3] = _pi[_pm].mean(axis=0).astype(np.uint8)
_pl[..., 3] = _pm * 255
poser("plume", _pl, 432, 224)
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert not tex[TEX - 4:TEX - 2, TEX - 4:TEX - 2, 3].any()
_hors = tex[..., 3].copy()
for _k in ("plume_l", "cercle", "rosace"):
    _x0, _y0, _x1, _y1 = UV[_k]; _hors[_y0:_y1, _x0:_x1] = 0
assert set(np.unique(_hors)) <= {0, 255}            # semi-transparence seulement sur les rémiges et le tracé du cercle (groupes trans_)

# Calque _e limité aux rémiges de lumière (trans_) et aux plumes ivoire : sans lui, de nuit, les ailes s'éteignent et les plumes
# deviennent des silhouettes. Rien sous les plaques add_ (leçon aura_berenice). Rémiges : couleur × alpha × 0,38 (≤ 90).
_e = np.zeros((TEX, TEX, 4), np.uint8)
_x0, _y0, _x1, _y1 = UV["plume_l"]
_w = tex[_y0:_y1, _x0:_x1].astype(float)
_e[_y0:_y1, _x0:_x1, :3] = np.clip(_w[..., :3] * (_w[..., 3:4] / 255) * 0.38, 0, 255).astype(np.uint8)
_e[_y0:_y1, _x0:_x1, 3] = (_w[..., 3] > 0) * 255
for _k, _ke in (("cercle", 0.26), ("rosace", 0.18)):   # tracé or du cercle : lisible de nuit (couleur × alpha × 0,26 ; rosace 0,18)
    _x0, _y0, _x1, _y1 = UV[_k]
    _w = tex[_y0:_y1, _x0:_x1].astype(float)
    _e[_y0:_y1, _x0:_x1, :3] = np.clip(_w[..., :3] * (_w[..., 3:4] / 255) * _ke, 0, 255).astype(np.uint8)
    _e[_y0:_y1, _x0:_x1, 3] = (_w[..., 3] > 0) * 255
_x0, _y0, _x1, _y1 = UV["plume"]
_p = tex[_y0:_y1, _x0:_x1]
_e[_y0:_y1, _x0:_x1, :3] = (_p[..., :3].astype(float) * 0.22).astype(np.uint8)
_e[_y0:_y1, _x0:_x1, 3] = (_p[..., 3] > 0) * 255
_e[_e[..., 3] == 0, :3] = 0
assert _e[..., :3].max() <= 100 and set(np.unique(_e[..., 3])) <= {0, 255}
tex_e = Image.fromarray(_e, "RGBA")
tex_e.save(f"{NOM}_e.png", optimize=True)
_b = io.BytesIO()
tex_e.save(_b, "PNG", optimize=True)
tex_e_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()

im_ = Image.fromarray(tex, "RGBA")
im_.save(f"{NOM}.png", optimize=True)
_buf = io.BytesIO()
im_.save(_buf, "PNG", optimize=True)
tex_b64 = "data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode()


# ------------------------------------------------------------------ géométrie
def nuid():
    return str(_uuid.uuid4())


class G:
    def __init__(self, nom, origin, parent=None, rotation=None):
        assert len(nom) <= 64
        self.nom, self.origin, self.uuid, self.enfants = nom, [round(float(v), 4) for v in origin], nuid(), []
        self.rotation = rotation
        if parent is not None:
            parent.enfants.append(self)

    def json(self):
        d = {"name": self.nom, "origin": self.origin, "uuid": self.uuid,
             "children": [c.json() if isinstance(c, G) else c for c in self.enfants]}
        if self.rotation:
            d["rotation"] = [round(float(v), 4) for v in self.rotation]
        return d


elements = []


def cube(g, nom, a, b, faces, origin=None):
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in a], "to": [round(float(v), 4) for v in b],
         "origin": [round(float(v), 4) for v in (origin if origin is not None else (np.add(a, b) / 2))], "box_uv": False,
         "faces": {k: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for k, uv in faces.items()}}
    elements.append(e)
    g.enfants.append(e["uuid"])


def plaque(g, nom, c, w, h, uv, face="south", ep=0.15):
    """Plaque à une seule face texturée : south (plan XY, w en x, h en y) ou up (plan XZ, w en x, h en z)."""
    c = np.asarray(c, float)
    if face in ("south", "north"):
        a, b = c - (w / 2, h / 2, ep / 2), c + (w / 2, h / 2, ep / 2)
    else:
        a, b = c - (w / 2, ep / 2, h / 2), c + (w / 2, ep / 2, h / 2)
    cube(g, nom, a, b, {face: uv}, origin=c)


EMIT = {}          # sorte -> [(groupe emit_, groupe ctrl_emit)]


def emit(sorte, pos, parent, nom=None):
    lst = EMIT.setdefault(sorte, [])
    n = nom or ("emit_" + sorte + (str(len(lst) + 1) if lst else ""))
    g = G(n, pos, parent)
    c = G("ctrl_emit", pos, g)
    lst.append((g, c))
    return g


EFFET = G("effet", (0, 0, 0))
JOUEUR = G("joueur", (0, 0, 0))

# --- cercle au sol : tracé or en trans_ (visible de jour, _e de nuit) sous une lueur add_ douce ; ctrl_alpha sur tout le cercle
SOL = G("sol", (0, 0, 0), EFFET)
A_SOL = G("ctrl_alpha", (0, 0, 0), SOL)
TOURNE = G("tourne_cercle", (0, 0, 0), SOL)
SCINT = []
EXT = G("cercle_ext", (0, 0, 0), TOURNE)          # cercle extérieur entier : grandit depuis le centre à l'apparition
A_EXT = G("ctrl_alpha", (0, 0, 0), EXT)
_gt = G("trans_cercle", (0, 0, 0), EXT)
plaque(_gt, "cercle", (0, 0.30, 0), 2 * RE, 2 * RE, UV["cercle"], face="up", ep=0.1)
_ga = G("add_cercle", (0, 0, 0), EXT)
plaque(_ga, "cercle_lueur", (0, 0.62, 0), 2 * RE, 2 * RE, UV["cercle_g"], face="up", ep=0.1)
for k in range(8):                                # étoiles qui scintillent dans la bande (cam_ : toujours de face)
    _as = math.radians(30 + 45 * k)
    sp = (YG * math.cos(_as), 1.8 + 0.3 * (k % 2), YG * math.sin(_as))
    sc = G(f"cam_scint{k}", sp, _ga)
    plaque(sc, f"scint{k}", (sp[0], sp[1], sp[2] - 0.8 - 0.12 * (k % 3)), 4.4, 4.4, UV["scint"])
    SCINT.append(sc)
CENTRE = G("centre", (0, 1.0, 0), SOL)
TOURNE_C = G("tourne_centre", (0, 1.0, 0), CENTRE)
_gt = G("trans_rosace", (0, 1.0, 0), TOURNE_C)
plaque(_gt, "rosace", (0, 1.0, 0), 2 * RC, 2 * RC, UV["rosace"], face="up")
_ga = G("add_rosace", (0, 1.0, 0), TOURNE_C)
plaque(_ga, "rosace_lueur", (0, 1.3, 0), 2 * RC, 2 * RC, UV["rosace_g"], face="up")
for k in range(8):                              # poussière d'or qui monte du cercle (+Y = vers le haut)
    ang = 2 * math.pi * (k + 0.5) / 8
    emit("etoile", (YG * math.cos(ang), 1.2, YG * math.sin(ang)), SOL)
for k in range(2):
    ang = 2 * math.pi * (k * 0.5 + 0.125)
    emit("mc_dust_ffd27a_10", (16.6 * math.cos(ang), 0.9, 16.6 * math.sin(ang)), SOL, nom="emit_mc_dust_ffd27a_10")
for k in range(2):                              # étincelles au ras du sol (atterrissage)
    ang = 2 * math.pi * (k * 0.5 + 0.3)
    emit("etincelle", (3.0 * math.cos(ang), 0.8, 3.0 * math.sin(ang)), SOL)

# --- colonne (camy_ : debout face caméra ; z local négatif = derrière le joueur vu de la caméra)
COL = G("colonne", (0, 0, 0), EFFET)
CAMY = G("camy_colonne", (0, HC / 2, 0), COL)
ADD_COL = G("add_colonne", (0, HC / 2, 0), CAMY)
A_COL = G("ctrl_alpha", (0, HC / 2, 0), ADD_COL)
plaque(ADD_COL, "lueur", (0, HC / 2, -3.3), 26, HC, UV["glow"])
plaque(ADD_COL, "coeur", (0, HC / 2, -2.9), 9, HC, UV["coeur"])
plaque(ADD_COL, "voile", (0, HC / 2, 3.0), 26, HC, UV["voile"])     # face à 3,075 : à 0,15 px des rémiges au repos
FILS = []
FX = [(-5.5, 10), (-2.6, 24), (3.0, 6), (5.8, 30), (0.8, 40), (-4.2, 46)]
for i, (x, y) in enumerate(FX):
    g = G(f"fil{i}", (x, y, 0), ADD_COL)
    plaque(g, f"fil{i}", (x, y, -2.5 + 0.25 * (i % 3)), 0.55, 13 - (i % 3) * 2, UV["fil"], ep=0.12)
    FILS.append(g)
LUEURS = G("lueurs", (0, 0, 0), EFFET)          # poussière de lumière dans la colonne
for i, (x, y, z) in enumerate(((1.5, 2.0, 0.8), (-1.2, 9.0, -1.4), (0.6, 17.0, 1.6), (-1.8, 26.0, 0.2))):
    emit("lueur", (x, y, z), LUEURS)

# --- rayons qui tournent autour de la colonne (vortex) : pivot bas pour monter du sol, pivot haut pour descendre du ciel
RAY_B = G("rayons_bas", (0, 0, 0), EFFET)
RAY_H = G("rayons_haut", (0, 44, 0), RAY_B)
ADD_R = G("add_rayons", (0, 22, 0), RAY_H)
A_RAY = G("ctrl_alpha", (0, 22, 0), ADD_R)
TOURNE_R = G("tourne_rayons", (0, 22, 0), ADD_R)
for k in range(6):
    g = G(f"rayon{k}", (0, 22, 0), TOURNE_R, rotation=(0, (60 * k + 7 * (k % 2) + 180) % 360 - 180, 0))      # rotations de groupe dans [-180, 180]
    rr = 6.6 + 0.9 * (k % 3)
    plaque(g, f"rayon{k}", (0, 21 + 2 * (k % 2), rr), 0.9, 38 - 4 * (k % 3), UV["fil"], ep=0.12)

# --- anneaux qui parcourent la colonne
ANNS = []
for i, (R, y) in enumerate(((6.5, 4.0), (4.4, 8.0))):
    g = G(f"anneau{i}", (0, y, 0), EFFET)
    ad = G(f"add_anneau{i}", (0, y, 0), g)
    plaque(ad, f"anneau{i}", (0, y, 0), 2 * R, 2 * R, UV["anneau"], face="up")
    ANNS.append(g)

# --- onde de choc (anneau horizontal qui s'élargit)
ONDE = G("onde", (0, 1.2, 0), EFFET)
ADD_O = G("add_onde", (0, 1.2, 0), ONDE)
plaque(ADD_O, "onde", (0, 1.2, 0), 16, 16, UV["onde"], face="up")

# --- ciel ouvert : cercle magique horizontal en l'air (arrivée)
YC = 50.0
CIEL = G("ciel", (0, YC, 0), EFFET)            # vu d'en dessous : faces down
A_CI = G("ctrl_alpha", (0, YC, 0), CIEL)
TOURNE_CI = G("tourne_ciel", (0, YC, 0), CIEL)
_ga = G("add_ciel", (0, YC, 0), TOURNE_CI)
plaque(_ga, "ciel_anneau", (0, YC + 0.3, 0), 30, 30, UV["anneau"], face="down")
TOURNE_CI2 = G("tourne_ciel2", (0, YC, 0), CIEL)
_gt = G("trans_ciel", (0, YC, 0), TOURNE_CI2)
plaque(_gt, "ciel_rosace", (0, YC, 0), 22, 22, UV["rosace"], face="down")
_ga = G("add_ciel2", (0, YC, 0), TOURNE_CI2)
plaque(_ga, "ciel_lueur", (0, YC - 0.3, 0), 24, 24, UV["rosace_g"], face="down")

# --- éclat d'étoile (cam_)
YE = 38.0
ECLAT = G("eclat", (0, YE, 0), EFFET)
CAME = G("cam_eclat", (0, YE, 0), ECLAT)
ADD_E = G("add_eclat", (0, YE, 0), CAME)
plaque(ADD_E, "eclat", (0, YE, 0), 13, 13, UV["eclat"])

# --- ailes de lumière (trans_ : or pâle semi-transparent, pas de cumul additif) : bras + main, rémiges qui pendent ; un seul plan de plaques par aile, couches à 0,25 px
AILES = G("ailes", (0, 0, 0), EFFET)
COCON = G("cocon", (0, 17, 0), AILES)
CAMC = G("cam_cocon", (0, 17, 0), COCON)
ADD_C = G("add_cocon", (0, 17, 0), CAMC)
A_COC = G("ctrl_alpha", (0, 17, 0), ADD_C)
# lueur du cocon à 11 px vers la caméra (8 avant) : devant les ailes trans_ refermées (≤ 8,5 px de face et de 3/4), qui écrivent
# la profondeur et cachaient l'add_ derrière elles (fonctions-avancees.md) ; de profil, les ailes (15–18 px) la cachent encore.
plaque(ADD_C, "cocon", (0, 17, 11.0), 15, 30, UV["cocon"])
ADD_AIL = G("trans_ailes", (0, 24, 3.5), AILES)        # échelle des ailes autour du haut du dos
A_AIL = G("ctrl_alpha", (0, 0, 0), ADD_AIL)
WR = (9.0, 7.0)                                  # poignet, depuis la racine (x vers l'extérieur, y vers le haut)
BRAS, MAIN, PLIE = {}, {}, {}
for s, t in ((1, "r"), (-1, "l")):
    R = (6.0 * s, 21.5, 4.3 + (0.12 if s < 0 else 0.0))
    bras = G(f"bras_{t}", R, ADD_AIL)
    Wp = (R[0] + WR[0] * s, R[1] + WR[1], R[2])
    main = G(f"main_{t}", Wp, bras)
    plie = G(f"plie_{t}", Wp, main)            # repli de l'éventail dans le plan de la main (appliqué avant main)
    BRAS[s], MAIN[s], PLIE[s] = bras, main, plie

    def rem(g, b, phi, L, w, nom, dzi):
        bx, by = R[0] + b[0] * s, R[1] + b[1]
        z = R[2] + 0.25 * dzi
        pg = G(nom, (bx, by, z), g, rotation=(0, 0, s * phi))
        cube(pg, nom, (bx - w / 2, by - L, z - 0.075), (bx + w / 2, by, z + 0.075), {"north": UV["plume_l"]}, origin=(bx, by, z))
        return bx + s * L * math.sin(math.radians(phi)), by - L * math.cos(math.radians(phi)), z

    for i in range(4):                           # couvertures, devant le plan des rémiges
        u = (i + 0.7) / 4.4
        rem(bras, (WR[0] * u, WR[1] * u + 0.6), 14 + 6 * i, 6.0 + 0.5 * i, 2.6, f"couv{i}_{t}", -(i + 1))
    for i in range(5):                           # secondaires sur l'avant-bras
        u = (i + 0.5) / 5.3
        rem(bras, (WR[0] * u, WR[1] * u), 6 + 4 * i, 12.0 + 0.7 * i, 3.2, f"sec{i}_{t}", i)
    for j in range(6):                           # primaires sur la main, en éventail
        tip = rem(plie, (WR[0] + 0.6 * j, WR[1] + 0.3 * j), 26 + 11 * j, 15.0 + (0, 1.5, 2.5, 3.0, 2.5, 1.0)[j], 3.0, f"prim{j}_{t}", 5 + j)
        if j in (2, 5):
            emit("plume", tip, plie)
    emit("mc_dust_ffd27a_10", (R[0] + 4 * s, R[1] + 3, R[2]), bras, nom="emit_mc_dust_ffd27a_10")
GERBE = G("gerbe", (0, 0, 0), EFFET)              # cœur du cocon : gerbe de plumes et d'étincelles à l'éclat (jamais à l'échelle 0)
for k in range(2):
    emit("plume", (1.5 * (1 - 2 * k), 18.0, 0.5), GERBE)
    emit("etincelle", (-1.0 * (1 - 2 * k), 19.0, -0.5), GERBE)

# --- plumes modélisées (opaques, deux faces, tranches transparentes)
PLUMES, REPOS = [], []
PW, PLEN, PTH = 2.2, 7.6, 0.3
NP = 16
for k in range(NP):
    ang = 2 * math.pi * k / NP
    p = (9.0 * math.cos(ang), 3.0 + 1.2 * k, 9.0 * math.sin(ang))
    g = G(f"plume{k}", p, EFFET)
    a = (p[0] - PW / 2, p[1] - PTH / 2, p[2] - PLEN / 2)
    b = (p[0] + PW / 2, p[1] + PTH / 2, p[2] + PLEN / 2)
    u0, v0, u1, v1 = UV["plume"]
    cube(g, f"plume{k}", a, b, {"up": [u0, v0, u1, v1], "down": [u0, v1, u1, v0], "north": CLEAR, "south": CLEAR,
                                 "east": CLEAR, "west": CLEAR})
    PLUMES.append(g)
    REPOS.append(np.array(p))

# --- particules (une plaque chacune ; groupes à la racine, jamais portés)
PART = {}
PART["etoile"] = G("particle_etoile", (0, 0, 0))
plaque(PART["etoile"], "p_etoile", (0, 0.75, 0), 0.6, 0.6, UV["etoile"])
PART["etincelle"] = G("particle_etincelle", (0, 0, 0))
plaque(PART["etincelle"], "p_etincelle", (0, 0.7, 0), 0.45, 0.45, UV["point"])
PART["lueur"] = G("particle_lueur", (0, 0, 0))
plaque(PART["lueur"], "p_lueur", (0, 0.8, 0), 0.7, 0.7, UV["lueur"])
PART["plume"] = G("particle_plume", (0, 0, 0))       # recette des ailes de Bérénice : face up seule, 0,3 px au-dessus du pivot
_u0, _v0, _u1, _v1 = UV["plume"]
cube(PART["plume"], "p_plume", (-1.2, 0.3, -3.5), (1.2, 0.6, 3.5), {"up": [_u0, _v0, _u1, _v1]}, origin=(0, 0, 0))

outliner = [EFFET.json(), JOUEUR.json()] + [PART[k].json() for k in ("plume", "etoile", "etincelle", "lueur")]
NEMIT = sum(len(v) for v in EMIT.values())
assert NEMIT <= 32, NEMIT


# ------------------------------------------------------------------ animations
def s(v):
    return v if isinstance(v, str) else str(round(float(v) + 0.0, 4))


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


def surg(t, a, b, over=0.12):
    u = sm(t, a, b)
    return u + over * math.sin(math.pi * u) * (u > 0.5)


def temps(L, fps=10):
    n = max(2, int(round(L * fps)))
    return [round(L * i / n, 4) for i in range(n + 1)]


class Anim:
    def __init__(self, nom, L, loop, fps=10):
        self.nom, self.L, self.loop, self.A = nom, L, loop, {}
        self.T = temps(L, fps)

    def piste(self, g, ch, f, T=None):
        T = self.T if T is None else T
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += [kf(ch, t, *f(t)) for t in T]

    def fixe(self, g, ch, v):
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"].append(kf(ch, 0, *v))

    def son(self, t, nom):
        self.A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
            {"channel": "sound", "data_points": [{"effect": nom, "file": ""}], "time": t}]}

    def cadence(self, sorte, f):
        """ctrl_emit (x) de chaque point de la sorte : f(t, i) -> −1 (coupé) … +7."""
        for i, (g, c) in enumerate(EMIT[sorte]):
            self.piste(c, "position", lambda t, i=i: (max(-1.0, min(7.0, f(t, i))), 0, 0))

    def json(self):
        return {"uuid": nuid(), "name": self.nom, "loop": self.loop, "override": False, "length": self.L, "snapping": 24,
                "selected": self.nom == "charge", "animators": self.A}


uni = lambda v: (v, v, v)
Z3 = (0, 0, 0)
TAU = 2 * math.pi


def eteint_a_la_fin(an):
    an.piste(EFFET, "scale", lambda t: uni(1.0 if t < an.L - 0.04 else 0.0), T=[0, round(an.L - 0.05, 4), an.L])


def plume_pose(an, k, f):
    """f(t) -> (position monde du centre, rotation (x, y, z), échelle) ; écrit les trois pistes de la plume k."""
    g, rp = PLUMES[k], REPOS[k]
    an.piste(g, "position", lambda t: tuple(f(t)[0] - rp))
    an.piste(g, "rotation", lambda t: f(t)[1])
    an.piste(g, "scale", lambda t: (f(t)[2], 1, f(t)[2]))


def cacher(an, groupes):
    for g in groupes:
        an.fixe(g, "scale", Z3)


def ailes_pose(an, f):
    """f(t) -> ((rx, ry, rz) du bras, (rx, ry, rz) de la main, repli z dans le plan) pour l'aile DROITE ; la gauche en miroir."""
    for sg in (1, -1):
        an.piste(BRAS[sg], "rotation", lambda t, sg=sg: (f(t)[0][0], sg * f(t)[0][1], sg * f(t)[0][2]))
        an.piste(MAIN[sg], "rotation", lambda t, sg=sg: (f(t)[1][0], sg * f(t)[1][1], sg * f(t)[1][2]))
        an.piste(PLIE[sg], "rotation", lambda t, sg=sg: (0, 0, sg * f(t)[2]))


def mix(a, b, k):
    return tuple(lerp(np.asarray(a, float), np.asarray(b, float), k))


OUVERT = ((0, -14, 14), (0, -6, -6), 0.0)            # grandes ouvertes, relevées
COCON_P = ((0, 34, -18), (0, 120, 0), -50.0)          # repliées devant le corps : les mains se croisent devant lui
REPLI = ((0, -40, -30), (0, -30, 20), -30.0)           # rentrées dans le dos (apparition)


def gerbe(t, tb, k, centre, R=15.0, chute=10.0, fin=1.25):
    """Plume k projetée depuis centre à tb, freinée, puis qui retombe en tournoyant ; (pos, rot, échelle)."""
    ga = k * 2.39996
    e = -0.25 + 0.75 * ((k * 7) % NP) / NP
    dirv = np.array((math.cos(ga) * math.sqrt(1 - e * e), e, math.sin(ga) * math.sqrt(1 - e * e)))
    u = max(0.0, t - tb)
    Rk = R * (0.75 + 0.25 * ((k * 5) % NP) / NP)
    p = np.asarray(centre, float) + dirv * Rk * (1 - math.exp(-u / 0.16))
    p[1] -= chute * max(0.0, u - 0.25) ** 1.3
    p[0] += 1.2 * math.sin(TAU * (u * 0.9 + k / 5)) * sm(u, 0.2, 0.6)
    rot = (35 * math.sin(TAU * (u * 0.8 + k / NP)), (1 if k % 2 else -1) * (300 * u + 25 * k), 30 * math.sin(TAU * (u * 0.6 + k / 7)))
    sc = sm(t, tb - 0.01, tb + 0.08) * (1 - sm(u, fin - 0.35 + 0.02 * (k % 5), fin))
    return p, rot, sc


# ---- charge (loop 3 s, la durée du compte à rebours du mod, guide 15) : tout est périodique, rien ne s'éteint ; la boucle
# se referme à 3 s sur sa pose de départ, donc le départ enchaîne sans saut. Respiration et scintillement : demi-période LC / 2.
LC = 3.0
P2 = LC / 2
ch = Anim("charge", LC, "loop", fps=12)
ch.fixe(EXT, "scale", (1, 1, 1))
ch.fixe(A_EXT, "position", Z3)
ch.fixe(CENTRE, "scale", (1, 1, 1))
ch.piste(SOL, "scale", lambda t: (1 + 0.03 * math.sin(TAU * t / P2), 1, 1 + 0.03 * math.sin(TAU * t / P2)))
ch.piste(A_SOL, "position", lambda t: (-0.08 + 0.08 * math.sin(TAU * t / P2), 0, 0))
for k, g in enumerate(SCINT):
    ch.piste(g, "scale", lambda t, k=k: uni(0.5 + 1.3 * max(0.0, math.sin(TAU * (t / P2 + k * 0.37))) ** 6))
    ch.piste(g, "rotation", lambda t, k=k: (0, 0, 360 * t / LC * (1 if k % 2 else -1)))
ch.piste(COL, "scale", lambda t: (1, 0.55 + 0.07 * math.sin(TAU * t / P2), 1))
ch.fixe(ADD_COL, "scale", (0.8, 1, 1))
ch.fixe(COL, "position", Z3)
ch.fixe(A_COL, "position", (0, 0, 0))
ch.piste(RAY_B, "scale", lambda t: (1, 0.45 + 0.05 * math.sin(TAU * t / P2), 1))
ch.fixe(RAY_H, "scale", (1, 1, 1))
ch.fixe(ADD_R, "scale", (1, 1, 1))
ch.piste(TOURNE_R, "rotation", lambda t: (0, 360 * t / LC, 0))
ch.fixe(A_RAY, "position", (-0.1, 0, 0))
for i, g in enumerate(ANNS):                     # anneaux qui montent du cercle, l'un après l'autre
    y0 = (4.0, 8.0)[i]
    k_ = (1.6, 2.2)[i]
    ch.piste(g, "position", lambda t, i=i, y0=y0: (0, 0.8 + 16 * ((t / P2 + i / 2) % 1.0) - y0, 0))
    ch.piste(g, "scale", lambda t, i=i, k_=k_: uni(k_ * (1 - 0.4 * ((t / P2 + i / 2) % 1.0)) * bump((t / P2 + i / 2) % 1.0, 0.0, 0.15, 0.55, 0.95)))
cacher(ch, FILS + [ECLAT, ONDE, CIEL, AILES])
ch.fixe(GERBE, "position", Z3)
def plume_charge(t, k):
    """Plume k (0–5) de la charge : spirale qui monte autour du cercle ; (pos, rot, échelle). Reprise au début du départ."""
    u = (t / LC + k / 6) % 1.0
    ang = TAU * k / 6 + 2.2 * u
    r = 11.0 + 1.2 * math.sin(TAU * u)
    pos = np.array((r * math.cos(ang), 1.2 + 24 * u, r * math.sin(ang)))
    rot = (25 * math.sin(TAU * (t / LC * 2 + k / 6)), (1 if k % 2 else -1) * 360 * t / LC + 60 * k,
           15 * math.cos(TAU * (t / LC + k / 3)))
    sc = 0.85 * bump(u, 0.04, 0.18, 0.7, 0.9)
    return pos, rot, sc


for k in range(NP):
    if k >= 6:
        ch.fixe(PLUMES[k], "scale", Z3)
        continue
    plume_pose(ch, k, lambda t, k=k: plume_charge(t, k))
ch.fixe(JOUEUR, "position", Z3)
ch.fixe(JOUEUR, "scale", (1, 1, 1))
ch.fixe(EFFET, "scale", (1, 1, 1))
ch.cadence("etoile", lambda t, i: 1 + 0.8 * math.sin(TAU * (t / P2 + i / 8)))
ch.cadence("lueur", lambda t, i: 0.5)
ch.cadence("mc_dust_ffd27a_10", lambda t, i: 0.0 if i < 2 else -1)
ch.cadence("plume", lambda t, i: -1)
ch.cadence("etincelle", lambda t, i: -1)

# ---- depart (once 3,6 s)
LD = 3.6
TB = 2.1                                          # l'éclat
de = Anim("depart", LD, "once", fps=20)
JY = lambda t: 1.5 * sm(t, 0.6, 1.2) + 18.5 * min(1.0, max(0.0, (t - 1.25) / 0.85)) ** 2.2
de.piste(JOUEUR, "position", lambda t: (0, JY(t), 0))
de.piste(JOUEUR, "scale", lambda t: uni(1.0 if t < TB - 0.02 else 0.0), T=[0, round(TB - 0.03, 4), round(TB + 0.01, 4), LD])


def ail_d(t):
    """Ailes : jaillissent du dos (0–0,4), s'ouvrent grand, se referment en cocon (0,55–1,1), frémissent, éclatent à TB."""
    a = sm(t, 0.0, 0.4)
    p = mix(REPLI[0], OUVERT[0], a), mix(REPLI[1], OUVERT[1], a), lerp(REPLI[2], OUVERT[2], a)
    c = sm(t, 0.55, 1.1)
    p = mix(p[0], COCON_P[0], c), mix(p[1], COCON_P[1], c), lerp(p[2], COCON_P[2], c)
    tremble = 1.5 * math.sin(TAU * t * 6) * bump(t, 1.1, 1.3, 1.9, 2.1)
    return (p[0][0], p[0][1], p[0][2] + tremble), p[1], p[2]


ailes_pose(de, ail_d)
de.piste(AILES, "position", lambda t: (0, JY(t), 0))
de.piste(GERBE, "position", lambda t: (0, JY(t), 0))
de.piste(ADD_AIL, "scale", lambda t: uni(sm(t, 0.0, 0.3) * (1 + 0.08 * bump(t, 0.3, 0.45, 0.5, 0.7)) * (1 - sm(t, TB - 0.02, TB + 0.1))))
de.piste(A_AIL, "position", lambda t: (-0.15 + 0.15 * bump(t, 1.0, 1.3, 2.0, 2.1), 0, 0))
de.piste(COCON, "scale", lambda t: (sm(t, 0.7, 1.2) * (1 + 0.12 * math.sin(TAU * t * 3) * sm(t, 1.2, 1.4)) * (1 - 0.3 * sm(t, 1.3, 2.0)),
                                    sm(t, 0.7, 1.2) * (1 + 0.2 * sm(t, 1.3, 2.0)) * (1 - sm(t, TB - 0.22, TB - 0.06)), 1))
# cercle : se contracte (anticipation), s'embrase, tient, s'éteint après l'éclat
de.fixe(EXT, "scale", (1, 1, 1))
de.fixe(A_EXT, "position", Z3)
de.fixe(CENTRE, "scale", (1, 1, 1))
de.piste(SOL, "scale", lambda t: uni((1 - 0.06 * bump(t, 0.0, 0.12, 0.15, 0.3) + 0.1 * bump(t, 0.2, 0.35, 0.45, 0.9)
                                      + 0.06 * bump(t, TB, TB + 0.08, TB + 0.15, TB + 0.6)) * (1 - sm(t, 3.0, 3.3))))
de.piste(A_SOL, "position", lambda t: (-0.9 * sm(t, 2.5, 3.2), 0, 0))
for k, g in enumerate(SCINT):
    de.piste(g, "scale", lambda t, k=k: uni((0.6 + 0.9 * max(0.0, math.sin(TAU * (t * 1.5 + k * 0.37))) ** 4) * (1 + 0.6 * bump(t, TB, TB + 0.1, TB + 0.2, TB + 0.6))))
    de.piste(g, "rotation", lambda t, k=k: (0, 0, 120 * t * (1 if k % 2 else -1)))
# colonne : basse, puis pilier plein quand le cocon se forme, faisceau qui suit l'ascension, flash, puis fil qui monte et s'efface
H_COL = lambda t: 0.55 + 0.45 * sm(t, 0.5, 0.9)
W_COL = lambda t: ((0.8 + 0.5 * sm(t, 0.5, 0.9) - 0.5 * sm(t, 1.3, 2.0) - 0.6 * bump(t, TB - 0.25, TB - 0.05, TB + 0.15, TB + 0.5))
                   * (1 - 0.85 * sm(t, 2.4, 3.1)) * (1 - sm(t, 3.1, 3.3)))
de.piste(COL, "scale", lambda t: (1, H_COL(t) * (1 - 0.4 * sm(t, 2.4, 3.1)), 1))
de.piste(ADD_COL, "scale", lambda t: (W_COL(t), 1, 1))
de.piste(COL, "position", lambda t: (0, HC * 0.4 * sm(t, 2.4, 3.1), 0))
de.piste(A_COL, "position", lambda t: (-0.85 * sm(t, 2.5, 3.1), 0, 0))
FPH = lambda t, i: (t * 1.2 + 0.6 * t * t / LD + i / len(FILS)) % 1.0
for i, g in enumerate(FILS):                     # traits de lumière qui filent vers le haut, de plus en plus vite
    de.piste(g, "position", lambda t, i=i: (0, 6 + 46 * FPH(t, i) - FX[i][1], 0))
    de.piste(g, "scale", lambda t, i=i: (1, bump(FPH(t, i), 0.05, 0.25, 0.7, 0.95) * bump(t, 0.6, 0.8, TB + 0.2, TB + 0.6), 1))
# rayons : montent du sol en tournant, s'accélèrent avec l'ascension, se dispersent à l'éclat
de.piste(RAY_B, "scale", lambda t: (1 + 0.8 * sm(t, TB, TB + 0.5), 0.45 + 0.55 * sm(t, 0.6, 1.1), 1 + 0.8 * sm(t, TB, TB + 0.5)))
de.fixe(RAY_H, "scale", (1, 1, 1))
de.piste(TOURNE_R, "rotation", lambda t: (0, 90 * t + 140 * t * t, 0))
de.piste(A_RAY, "position", lambda t: (-0.1 * (1 - sm(t, 0.4, 0.8)) - 0.9 * sm(t, TB, TB + 0.5), 0, 0))
de.piste(ADD_R, "scale", lambda t: uni(1 - sm(t, TB + 0.3, TB + 0.55)))
APH = lambda t, i: (t + i / 2) % 1.0
for i, g in enumerate(ANNS):                     # anneaux qui montent du cercle, puis accompagnent le cocon
    y0 = (4.0, 8.0)[i]
    de.piste(g, "position", lambda t, i=i, y0=y0: (0, (0.8 + 16 * APH(t, i)) * (1 - sm(t, 0.9, 1.3)) + sm(t, 0.9, 1.3) * (JY(t + 0.1 * (1 - i)) + 8 + 18 * i) - y0, 0))
    de.piste(g, "scale", lambda t, i=i: uni((1.4 - 0.5 * i) * (1 - sm(t, TB - 0.3, TB - 0.05))
                                            * (bump(APH(t, i), 0.0, 0.15, 0.55, 0.95) * (1 - sm(t, 0.9, 1.3)) + sm(t, 0.9, 1.3))))
# onde de choc et éclat d'étoile à l'éclat, à la hauteur du cocon
YB = JY(TB) + 18
de.piste(ONDE, "position", lambda t: (0, YB - 1.2, 0))
de.piste(ONDE, "scale", lambda t: uni(0.0 if t < TB else (0.3 + 2.3 * (1 - math.exp(-(t - TB) / 0.22))) * (1 - sm(t, TB + 0.45, TB + 0.75))))
de.piste(ECLAT, "position", lambda t: (0, YB - YE, 0))
de.piste(ECLAT, "scale", lambda t: uni(1.2 * bump(t, TB - 0.06, TB, TB + 0.05, TB + 0.55) + 0.25 * bump(t, 0.25, 0.35, 0.4, 0.7)))
de.piste(ECLAT, "rotation", lambda t: (0, 0, 60 * sm(t, TB - 0.1, TB + 0.6)))
cacher(de, [CIEL])
# plumes : six montent en spirale et sont aspirées dans le cocon ; toutes jaillissent à l'éclat et retombent en tournoyant
for k in range(NP):
    def f(t, k=k):
        if t < TB:
            if k >= 6:
                return np.array(REPOS[k]), (0, 0, 0), 0.0
            u = sm(t, 0.1 + 0.05 * k, 1.3)
            ang = TAU * k / 6 + 4.0 * u
            r = 11.0 * (1 - u) + 3.0 * u
            pos = np.array((r * math.cos(ang), 1.5 + 17 * u + JY(t) * u, r * math.sin(ang)))
            rot = (30 * math.sin(TAU * (t + k / 6)), (1 if k % 2 else -1) * 300 * t, 20 * math.sin(TAU * (t * 0.7 + k / 5)))
            sc = 0.9 * sm(t, 0.05 + 0.05 * k, 0.3 + 0.05 * k) * (1 - sm(t, 1.05, 1.3))
            # enchaînement sans saut : la plume part de sa pose de fin de charge (t = LC) et rejoint la spirale aspirée
            cp, cr, cs = plume_charge(LC, k)
            cr = (cr[0], (cr[1] + 180) % 360 - 180, cr[2])
            w = sm(t, 0.0, 0.4)
            return lerp(cp, pos, w), tuple(lerp(np.asarray(cr, float), np.asarray(rot, float), w)), lerp(cs, sc, w)
        return gerbe(t, TB, k, (0, YB, 0), R=15.0, chute=11.0, fin=LD - TB - 0.15)
    plume_pose(de, k, f)
eteint_a_la_fin(de)
de.son(0.4, "envol_celeste")
de.cadence("etoile", lambda t, i: (1 + 3 * bump(t, 0.2, 0.4, 0.9, 1.3) + 2 * bump(t, TB, TB + 0.1, TB + 0.3, TB + 0.8)) if t < 2.9 else -1)
de.cadence("lueur", lambda t, i: (1 + 3 * sm(t, 0.5, 0.9) - 4 * sm(t, TB + 0.2, TB + 0.8)) if t < 2.9 else -1)
de.cadence("mc_dust_ffd27a_10", lambda t, i: (1 + 3 * bump(t, 0.4, 0.6, TB, TB + 0.5)) if i < 2
           else (2 + 5 * bump(t, TB - 0.3, TB - 0.05, TB, TB + 0.05) if t < TB + 0.05 else -1))
de.cadence("plume", lambda t, i: (1 + 2 * bump(t, 0.2, 0.35, 0.5, 0.8) if t < 1.0 else -1) if i < 4
           else (7 if TB - 0.02 <= t <= TB + 0.4 else -1))
de.cadence("etincelle", lambda t, i: (7 if TB - 0.02 <= t <= TB + 0.3 else -1) if i >= 2 else (3 * bump(t, 0.15, 0.25, 0.35, 0.6) - 1))

# ---- arrivee (once 4,5 s)
LA = 4.5
TP = 3.0                                         # le joueur se pose
ar = Anim("arrivee", LA, "once", fps=20)
JYA = lambda t: 150 * max(0.0, 1 - t / TP) ** 2.6
YAIL = lambda t: min(JYA(t), 22.0)
ar.piste(JOUEUR, "position", lambda t: (0, JYA(t), 0))
ar.piste(JOUEUR, "scale", lambda t: uni(sm(t, 0.0, 0.3)))
# ciel qui s'ouvre : cercle en l'air, éclair, puis il s'efface en s'élargissant
ar.piste(CIEL, "scale", lambda t: uni(surg(t, 0.0, 0.45, 0.15) * (1 + 0.3 * sm(t, 2.3, 3.0)) * (1 - sm(t, 2.9, 3.0))))
ar.piste(A_CI, "position", lambda t: (-0.9 * sm(t, 2.3, 2.95), 0, 0))
ar.piste(TOURNE_CI, "rotation", lambda t: (0, 60 * t, 0))
ar.piste(TOURNE_CI2, "rotation", lambda t: (0, -90 * t, 0))
ar.piste(ECLAT, "position", lambda t: (0, YC - YE, 0))
ar.piste(ECLAT, "scale", lambda t: uni(1.4 * bump(t, 0.05, 0.15, 0.2, 0.75)))
ar.piste(ECLAT, "rotation", lambda t: (0, 0, -50 * sm(t, 0, 0.8)))
# colonne qui descend du ciel, flash au contact, remonte et s'efface
HA = lambda t: sm(t, 0.15, 0.7) * (1 - sm(t, 3.5, 4.2))
WA = lambda t: (1.1 + 0.5 * bump(t, TP - 0.05, TP, TP + 0.08, TP + 0.5)) * (1 - 0.85 * sm(t, 3.4, 4.1)) * (1 - sm(t, 4.1, 4.25))
ar.piste(COL, "scale", lambda t: (1, HA(t), 1))
ar.piste(ADD_COL, "scale", lambda t: (WA(t), 1, 1))
ar.piste(COL, "position", lambda t: (0, HC * (1 - HA(t)), 0))
ar.piste(A_COL, "position", lambda t: (-0.8 * sm(t, 3.6, 4.2), 0, 0))
for i, g in enumerate(FILS):                     # traits de lumière qui descendent
    ar.piste(g, "position", lambda t, i=i: (0, 52 - 46 * ((t * 1.4 + i / len(FILS)) % 1.0) - FX[i][1], 0))
    ar.piste(g, "scale", lambda t, i=i: (1, bump((t * 1.4 + i / len(FILS)) % 1.0, 0.05, 0.25, 0.7, 0.95) * bump(t, 0.3, 0.6, TP - 0.2, TP + 0.3), 1))
# rayons : descendent du ciel en tournant, s'effacent après le contact
ar.fixe(RAY_B, "scale", (1, 1, 1))
ar.piste(RAY_H, "scale", lambda t: (1 + 0.6 * sm(t, TP, TP + 0.5), sm(t, 0.25, 0.85), 1 + 0.6 * sm(t, TP, TP + 0.5)))
ar.piste(TOURNE_R, "rotation", lambda t: (0, -(220 * t - 18 * t * t), 0))
ar.piste(A_RAY, "position", lambda t: (-sm(t, TP, TP + 0.5), 0, 0))
ar.piste(ADD_R, "scale", lambda t: uni(1 - sm(t, TP + 0.35, TP + 0.6)))
# le cercle naît sous le joueur qui approche : la rosace d'abord, puis le cercle extérieur grandit depuis le centre en
# s'allumant (échelle 0,3 -> 1 avec dépassement, fondu ctrl_alpha), éclat des étoiles ; il s'embrase au contact
ar.piste(CENTRE, "scale", lambda t: uni(surg(t, 1.6, 2.0, 0.12)))
ar.piste(EXT, "scale", lambda t: uni(0.0 if t < 1.85 else (0.3 + 0.7 * surg(t, 1.85, 2.45, 0.08))))
ar.piste(A_EXT, "position", lambda t: (-1 + sm(t, 1.85, 2.2), 0, 0))
ar.piste(SOL, "scale", lambda t: uni((1 + 0.1 * bump(t, TP - 0.03, TP + 0.06, TP + 0.12, TP + 0.7)) * (1 - 0.1 * sm(t, 3.8, 4.3)) * (1 - sm(t, 4.3, 4.42))))
ar.piste(A_SOL, "position", lambda t: (-sm(t, 3.8, 4.35), 0, 0))
for k, g in enumerate(SCINT):
    ar.piste(g, "scale", lambda t, k=k: uni((0.5 + 0.9 * max(0.0, math.sin(TAU * (t * 1.2 + k * 0.37))) ** 4) * (1 + 0.7 * bump(t, TP, TP + 0.1, TP + 0.2, TP + 0.7)) + 1.4 * bump(t, 2.2 + 0.03 * k, 2.3 + 0.03 * k, 2.35 + 0.03 * k, 2.7 + 0.03 * k)))
    ar.piste(g, "rotation", lambda t, k=k: (0, 0, 100 * t * (1 if k % 2 else -1)))
for i, g in enumerate(ANNS):                     # deux anneaux descendent devant le joueur et se fondent dans le cercle
    y0 = (4.0, 8.0)[i]
    ar.piste(g, "position", lambda t, i=i, y0=y0: (0, max(1.0 + 1.5 * i, min(48.0 + 3 * i, JYA(t + 0.25 + 0.2 * i) + 4 + 6 * i)) - y0, 0))
    ar.piste(g, "scale", lambda t, i=i: uni(bump(t, 0.7 + 0.2 * i, 1.1 + 0.2 * i, TP - 0.2, TP + 0.15) * (1 + 0.3 * sm(t, 2.0, TP))))
# ailes de lumière : apparaissent quand le joueur est assez bas, battement lent, se relèvent au contact puis se dissipent
ar.piste(AILES, "position", lambda t: (0, YAIL(t), 0))
ar.piste(GERBE, "position", lambda t: (0, YAIL(t), 0))
ar.piste(ADD_AIL, "scale", lambda t: uni(sm(t, 1.55, 1.95) * (1 + 0.06 * bump(t, TP - 0.1, TP, TP + 0.05, TP + 0.2)) * (1 - sm(t, TP + 0.15, TP + 0.5))))
ar.piste(A_AIL, "position", lambda t: (-0.3 * sm(t, TP + 0.05, TP + 0.35), 0, 0))
ar.fixe(COCON, "scale", Z3)


def ail_a(t):
    b = math.sin(TAU * (t - 1.5) / 1.1) * (1 - sm(t, TP - 0.4, TP))
    b2 = math.sin(TAU * (t - 1.62) / 1.1) * (1 - sm(t, TP - 0.4, TP))
    br = (0, -10 + 4 * b, 6 + 16 * b + 18 * bump(t, TP - 0.3, TP, TP + 0.1, TP + 0.4))
    mn = (0, -4 + 3 * b, -6 - 10 * b2 + 10 * bump(t, TP - 0.2, TP + 0.05, TP + 0.1, TP + 0.4))
    return br, mn, -6 * b2


ailes_pose(ar, ail_a)
# onde dorée au sol au contact
ar.fixe(ONDE, "position", Z3)
ar.piste(ONDE, "scale", lambda t: uni(0.0 if t < TP else (0.4 + 2.2 * (1 - math.exp(-(t - TP) / 0.25))) * (1 - sm(t, TP + 0.5, TP + 0.85))))
# plumes : six tombent du ciel en spirale autour de la colonne ; au contact, les ailes se dissipent en une gerbe de plumes
for k in range(NP):
    def f(t, k=k):
        if k < 6:
            t0 = 0.4 + 0.12 * k
            d = sm(t, t0, TP + 0.3)
            ang = TAU * k / 6 - 3.0 * d
            r = 10.0 + 2 * math.sin(math.pi * d) + 3 * sm(t, TP, LA)
            y = 46 * (1 - d) + 3.0
            pos = np.array((r * math.cos(ang), y, r * math.sin(ang)))
            rot = (25 * math.sin(TAU * (t * 0.7 + k / 6)), (1 if k % 2 else -1) * 160 * t + 30 * k, 20 * math.sin(TAU * (t * 0.5 + k / 5)))
            return pos, rot, 0.9 * sm(t, t0, t0 + 0.3) * (1 - sm(t, 3.5 + 0.05 * k, 4.0))
        sg = 1 if k % 2 else -1
        j = (k - 6) // 2
        c = (sg * (8 + 2.6 * j), 22 + 1.5 * (j % 3), 3.0)
        p, r, sc = gerbe(t, TP + 0.05 + 0.02 * j, k, c, R=7.0, chute=7.5, fin=LA - TP - 0.25)
        p[1] = max(p[1], 1.5)
        return p, r, sc
    plume_pose(ar, k, f)
eteint_a_la_fin(ar)
ar.son(1.8, "descente_celeste")
ar.cadence("etoile", lambda t, i: (-1 if t < 2.0 else (1 + 5 * bump(t, TP - 0.05, TP + 0.05, TP + 0.3, TP + 0.8) - 2 * sm(t, 3.9, 4.2))) if t < 4.25 else -1)
ar.cadence("lueur", lambda t, i: (-1 + 4 * sm(t, 0.3, 0.8) - 4 * sm(t, TP + 0.2, TP + 0.7)) if t < 4.0 else -1)
ar.cadence("mc_dust_ffd27a_10", lambda t, i: (-1 + 4 * bump(t, TP - 0.4, TP, TP + 0.3, TP + 0.9)) if i < 2
           else (1 + 6 * bump(t, TP - 0.02, TP + 0.05, TP + 0.2, TP + 0.35) if 1.7 < t < TP + 0.4 else -1))
ar.cadence("plume", lambda t, i: (1 + 6 * bump(t, TP - 0.02, TP + 0.03, TP + 0.2, TP + 0.32) if 1.8 < t < TP + 0.35 else -1) if i < 4 else -1)
ar.cadence("etincelle", lambda t, i: 7 if TP - 0.02 <= t <= TP + 0.3 else -1)

# ---- overlay_cercle (48 s) : l'anneau un tour, la rosace un tour en sens contraire
LO = 48.0
ov = Anim("overlay_cercle", LO, "loop")
ov.fixe(TOURNE, "rotation", (0, f"q.anim_time*{s(360 / LO)}", 0))
ov.fixe(TOURNE_C, "rotation", (0, f"q.anim_time*{s(-360 / LO)}", 0))


# ---- particules
def part_anim(sorte, L, ch_, f, n=12):
    a = Anim(f"particle_{sorte}_fall", L, "loop")
    a.piste(PART[sorte], ch_, f, T=[round(i * L / n, 4) for i in range(n + 1)])
    return a


pp = part_anim("plume", 4.0, "rotation", lambda t: (20 * math.sin(TAU * t / 4), 360 * t / 4, 14 * math.cos(2 * TAU * t / 4)), n=24)
pa = part_anim("etoile", 1.2, "scale", lambda t: uni(1 + 0.2 * math.sin(TAU * t / 1.2)))
pe = part_anim("etincelle", 0.4, "scale", lambda t: uni(1 + 0.35 * math.sin(TAU * t / 0.4)), n=8)
pl = part_anim("lueur", 1.6, "scale", lambda t: uni(1 + 0.25 * math.sin(TAU * t / 1.6)))

ANIMS = [ch.json(), de.json(), ar.json(), ov.json(), pp.json(), pa.json(), pe.json(), pl.json()]
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures,
         "animations": ANIMS}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
# sons originaux (tools/synthe.py, sources dans sons/), en mi majeur comme les autres pièces de Bérénice
embarquer_sons(model, {"envol_celeste": "sons/envol_celeste.ogg", "descente_celeste": "sons/descente_celeste.ogg"})
limiter_sons(model)

os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


def ngroupes(n):
    return 1 + sum(ngroupes(c) for c in n.get("children", []) if isinstance(c, dict))


print(len(elements), "cubes ;", sum(ngroupes(n) for n in model["outliner"]), "groupes ; profondeur", max(depth(n) for n in model["outliner"]),
      ";", len(model["animations"]), "anims ;", sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()),
      "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;", NEMIT, "emit_ :", {k: len(v) for k, v in EMIT.items()})
