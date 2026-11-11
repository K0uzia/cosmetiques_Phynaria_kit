"""Aura de givre (v2, revue du 2026-11-08) : une lumière froide qui monte autour du joueur, comme les piliers de lumière d'une
nuit de grand froid. Design original (ensemble Givre, thème Éléments, fiche .claude/styles/givre.md). Écrit aura_givre.png,
aura_givre_e.png et .build/aura_givre_brut.bbmodel. Ancienne version : .build/gen_avant.py, .build/avant_livrable.bbmodel.

Retour de l'utilisateur (2026-11-08) : « revoir les aura sauf la bérénice qui es bien les autre nul ». La v1 portait tout au sol
(couronne de 18 cristaux, plaque de givre) avec un halo bleu sombre presque invisible : de loin, des cailloux bleus aux pieds.
La v2 garde la recette de aura_berenice (« bien ») : de la lumière autour de la silhouette, un grand signe derrière la nuque,
des colonnes qui montent derrière le joueur, un anneau au sol. Ce qui la rend propre au Givre (analogie physique, pas d'œuvre) :
- les piliers de lumière et la poussière de diamant (cristaux de glace hexagonaux en suspension qui reflètent la lumière en
  colonnes verticales et scintillent) : colonnes fines et nettes, parcourues de paillettes qui montent ;
- le cristal hexagonal : derrière la nuque, une rosace de givre à six branches ramifiées (plaques hexagonales au bout des
  branches, hexagone intérieur), qui tourne très lentement, devant un cercle de halo froid marqué de deux parhélies (points
  plus vifs à gauche et à droite, qui restent à l'horizontale) ;
- au sol, un hexagone de givre en dentelle et six petites grappes de cristaux trans_ à ses sommets (rien en orbite), une brume
  froide qui rampe autour des chevilles.

Construction (repris des pièces validées)
- Halo de silhouette : disques add_ bleu glacier en cam_, reculés derrière chaque partie du corps, vides au centre (recette
  aura_brasier v3 / aura_berenice). Plus forts derrière la tête et les épaules.
- Rosace : cam_ derrière la nuque (recul 7,5 px) ; couche add_ (flocon, 30 px) qui tourne (un tour en 60 s), couche add_ du
  cercle et des parhélies (36 px) qui ne tourne pas et pulse, doublée d'un flocon trans_ blanc glacé (alpha ≤ 150) placé
  DERRIÈRE l'additif (un trans_ devant un add_ le cacherait, fonctions-avancees.md, Pièges), pour les shaders et le plein jour.
- Piliers : 7 colonnes fines add_ dans un camy_ derrière le joueur, film de 8 images (ctrl_uv) où les paillettes montent.
- Sol : hexagone de givre trans_, lueur add_ au-dessus, six grappes de 3 cristaux (peau trans_ alpha 140–228, âme opaque dont
  le calque _e donne le cœur cyan, seul texel _e du modèle), éclats add_ en cam_ au bout des grands cristaux. Brume trans_
  basse (camy_, derrière les piliers pour ne pas les cacher) et anneau de brume à plat sous la lueur. Masqué quand le corps
  n'est pas debout et posé.
- Paillettes : particle_paillette (étoile à quatre branches de 0,6 px, une face), qui monte lentement, Élan 100 %. Pas d'end_rod.

Palette (fiche Givre) : lueur froide arrêtée au cyan pâle (205, 240, 252), jamais de blanc saturé ; glace bleu nuit -> cyan ->
blanc givré ; blanc pur seulement sur les arêtes et le givre. Gains additifs choisis sous ceux de aura_berenice (cumul < 240).

États : idle (respiration 8 s), walk et run (la lumière part vers l'arrière, cristaux de devant et de derrière rentrés en course),
sneak (contenue, sol masqué), fly, fall (s'élève), glide et swim (corps couché : piliers rentrés, rosace réduite), mount, sleep
(presque éteinte). Pas d'attack ni de hurt (pièce portée). event_equip (2,4 s) : le givre se répand, les cristaux poussent, les
piliers montent, le halo s'allume des pieds vers la tête, puis la rosace cristallise (un carillon d'améthyste à ce moment).
overlay_givre (60 s) : film des piliers, rotation de la rosace et des disques, éclats des cristaux, brume qui ondule.

Fonctions avancées (guide 4 bis, 5, 5 ter, 6.3, 6.4, 6.5) : add_, trans_, cam_, camy_, ctrl_alpha, ctrl_uv, calque _e limité aux
âmes des cristaux, particle_/emit_, overlay_, event_equip, son, Molang (math.sin, math.pow, math.max, math.mod, math.floor).

Ce qui se juge seulement en jeu (/cosmetique apercu) : l'additif réel de jour, ctrl_alpha et ctrl_uv (non simulés : le rendu
montre l'image 0 du film), les overlays (non joués par les rendus d'état), la glace trans_ avec shader, les particules.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "aura_givre"
AVEC_E = True       # _e noir partout sauf sur les âmes opaques des cristaux : il ne double jamais l'additif (leçon aura_berenice)
TEX = 512
SS = 4
RNG = np.random.default_rng(29)

# ------------------------------------------------------------------ palettes
# Lueur froide (additif, intensité 0..1 -> couleur) : arrêtée au cyan pâle.
STOPS = [(0.0, (0, 0, 0)), (0.15, (4, 18, 34)), (0.35, (22, 74, 118)), (0.6, (72, 162, 214)),
         (0.85, (160, 222, 246)), (1.0, (205, 240, 252))]
# Glace par paliers nets (fiche Givre) : bleu nuit -> cyan -> blanc givré.
RAMP = np.array([(10, 30, 66), (16, 48, 108), (24, 84, 150), (38, 132, 192), (70, 184, 226), (120, 208, 238),
                 (170, 230, 248), (214, 242, 252), (244, 253, 255)], np.float32)


def palette(f):
    f = np.clip(f, 0, 1)
    xs = [s[0] for s in STOPS]
    return np.stack([np.interp(f, xs, [s[1][c] for s in STOPS]) for c in range(3)], axis=-1)


def ramp(v):
    return RAMP[np.clip((np.asarray(v) * len(RAMP)).astype(int), 0, len(RAMP) - 1)]


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def grille(W, H, ss=SS):
    n_w, n_h = W * ss, H * ss
    return np.meshgrid((np.arange(n_w) + 0.5) / n_w * 2 - 1, 1 - (np.arange(n_h) + 0.5) / n_h * 2)


def lanczos(a, W, H):
    return np.array(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)).astype(np.float32)


def reduire_add(f, W, H, gain, cutout=False):
    """Additif : image RGBA, alpha 0/255 ; le presque noir est transparent."""
    rgb = np.stack([lanczos(c, W, H) for c in np.moveaxis(palette(f) * gain, -1, 0)], axis=-1)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = np.clip(rgb, 0, 255)
    if cutout:
        a = lanczos(np.clip(f * 3, 0, 1) * 255, W, H) > 110
    else:
        a = arr[..., :3].max(axis=2) > 12
    arr[..., 3] = a * 255
    arr[~a, :3] = 0
    return arr


def reduire_trans(rgb, al, W, H, seuil=6):
    """trans_ : couleur et opacité sur-échantillonnées -> RGBA, alpha 1..254 (0 sous le seuil)."""
    c = np.stack([lanczos(rgb[..., k], W, H) for k in range(3)], axis=-1)
    a = lanczos(al, W, H)
    arr = np.zeros((H, W, 4), np.uint8)
    a = np.where(a > seuil, np.clip(a, 1, 254), 0)
    arr[..., :3] = c
    arr[..., 3] = a
    arr[a == 0, :3] = 0
    return arr


# ------------------------------------------------------------------ peinture
CORE = 0.42


def disque_f(seed, N=64):
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    wob = 1 + 0.035 * np.sin(6 * a + seed) + 0.025 * np.sin(12 * a + 2.3 * seed)      # bord à six lobes discrets (cristal)
    s = np.clip((r / wob - CORE) / (0.97 - CORE), 0, 1)
    f = (1 - s) ** 1.9 * 0.95 * smooth(r / wob / CORE) ** 1.3
    return f * smooth((1 - r) / 0.06)


def etoile4(x, y, cx, cy, R, w=0.18):
    u, v = (x - cx) / R, (y - cy) / R
    d = np.abs(u) ** 0.5 + np.abs(v) ** 0.5
    return np.clip((1.0 - d) / w, 0, 1) ** 0.8


def segment(x, y, p, q, w, dur=0.35):
    """Intensité 0..1 d'un trait de largeur w de p à q (bouts arrondis)."""
    px, py = p
    dx, dy = q[0] - px, q[1] - py
    L2 = dx * dx + dy * dy + 1e-12
    t = np.clip(((x - px) * dx + (y - py) * dy) / L2, 0, 1)
    d = np.hypot(x - px - t * dx, y - py - t * dy)
    return np.clip((w - d) / (w * dur), 0, 1)


def hexagone(x, y, cx, cy, R, w, rot=0.0):
    """Contour d'hexagone (rayon R au sommet) : six segments."""
    f = np.zeros_like(x)
    pts = [(cx + R * math.cos(rot + k * math.pi / 3), cy + R * math.sin(rot + k * math.pi / 3)) for k in range(7)]
    for a_, b_ in zip(pts, pts[1:]):
        f = np.maximum(f, segment(x, y, a_, b_, w))
    return f


def flocon_f(x, y, R=1.0, w=0.05, rot=math.pi / 6, cotes=((0.38, 0.30), (0.62, 0.22), (0.82, 0.12))):
    """Flocon à six branches ramifiées (rayon R, centré en 0)."""
    f = np.zeros_like(x)
    for k in range(6):
        a = rot + k * math.pi / 3
        ux, uy = math.cos(a), math.sin(a)
        f = np.maximum(f, segment(x, y, (0, 0), (R * ux, R * uy), w))
        for t, l in cotes:
            bx, by = R * t * ux, R * t * uy
            for s_ in (-1, 1):
                b = a + s_ * math.pi / 3
                f = np.maximum(f, segment(x, y, (bx, by), (bx + R * l * math.cos(b), by + R * l * math.sin(b)), w * 0.8))
    return f


R0 = 0.30      # le centre de la rosace est caché par la tête


def rosace_f(N, w=0.026, lueur=0.22):
    """Rosace de givre : six grandes branches ramifiées (avec une plaque hexagonale au bout), six branches courtes entre elles,
    un hexagone intérieur ; une lueur douce le long des traits."""
    x, y = grille(N, N)
    r = np.hypot(x, y)
    trait = np.zeros_like(x)
    halo = np.zeros_like(x)
    for k in range(6):
        a = math.pi / 2 + k * math.pi / 3
        ux, uy = math.cos(a), math.sin(a)
        p0, p1 = (R0 * 0.9 * ux, R0 * 0.9 * uy), (0.86 * ux, 0.86 * uy)
        trait = np.maximum(trait, segment(x, y, p0, p1, w))
        halo = np.maximum(halo, segment(x, y, p0, p1, w * 5, dur=1.0))
        for t, l, ww in ((0.46, 0.20, 0.8), (0.62, 0.15, 0.75), (0.76, 0.09, 0.7)):
            bx, by = t * ux, t * uy
            for s_ in (-1, 1):
                b = a + s_ * math.pi / 3
                trait = np.maximum(trait, segment(x, y, (bx, by), (bx + l * math.cos(b), by + l * math.sin(b)), w * ww))
        trait = np.maximum(trait, hexagone(x, y, 0.91 * ux, 0.91 * uy, 0.055, w * 0.7, rot=a))
        trait = np.maximum(trait, 0.95 * etoile4(x, y, 0.91 * ux, 0.91 * uy, 0.035, 0.3))
        # branche courte, entre deux grandes
        a2 = a + math.pi / 6
        u2x, u2y = math.cos(a2), math.sin(a2)
        q0, q1 = (R0 * 1.15 * u2x, R0 * 1.15 * u2y), (0.56 * u2x, 0.56 * u2y)
        trait = np.maximum(trait, 0.85 * segment(x, y, q0, q1, w * 0.75))
        bx, by = 0.47 * u2x, 0.47 * u2y
        for s_ in (-1, 1):
            b = a2 + s_ * math.pi / 3
            trait = np.maximum(trait, 0.8 * segment(x, y, (bx, by), (bx + 0.08 * math.cos(b), by + 0.08 * math.sin(b)), w * 0.6))
    trait = np.maximum(trait, 0.85 * hexagone(x, y, 0, 0, 0.40, w * 0.7, rot=math.pi / 2))
    f = np.maximum(trait, lueur * halo * smooth((r - R0 * 0.8) / 0.1))
    f = np.maximum(f, 0.12 * np.exp(-((r - 0.36) / 0.16) ** 2))
    return np.clip(f, 0, 1) * smooth((1 - r) / 0.03), trait


def cercle_f(N):
    """Cercle de halo froid (un filet net, un filet pâle) et deux parhélies à gauche et à droite."""
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    fil = lambda rr, w: np.exp(-((r - rr) / w) ** 2)
    f = np.maximum.reduce([0.9 * fil(0.90, 0.010), 0.45 * fil(0.86, 0.006), 0.10 * np.exp(-((r - 0.88) / 0.07) ** 2)])
    for cx in (-0.90, 0.90):
        d = np.hypot(x - cx, y)
        f = np.maximum(f, np.exp(-(d / 0.045) ** 2))                          # parhélie : point vif
        f = np.maximum(f, 0.55 * np.exp(-((x - cx) / 0.16) ** 2 - (y / 0.02) ** 2))   # petite traînée horizontale
        f = np.maximum(f, etoile4(x, y, cx, 0, 0.10, 0.22))
    return np.clip(f, 0, 1) * smooth((1 - r) / 0.03)


FR = 8


def pilier_f(W, H, seed, k):
    """Image k du film d'un pilier de lumière : âme fine et nette, enveloppe douce, paillettes qui montent d'une demi-hauteur sur
    FR images (motif répété tous les 0,5 : film fermé)."""
    rng = np.random.default_rng(seed)
    x, y = grille(W, H)
    Y = (y + 1) / 2
    env_v = smooth(Y / 0.22) * (1 - Y) ** 0.9
    ame = np.exp(-(x / 0.16) ** 2) * 0.62
    enveloppe = np.exp(-(x / 0.55) ** 2) * 0.30
    f = (ame + enveloppe) * env_v
    ph = k / FR * 0.5
    for _ in range(7):
        px, py = rng.uniform(-0.45, 0.45), rng.uniform(0, 0.5)
        for rep in (0, 0.5, 1.0):
            yy = (py + ph) % 0.5 + rep - 0.5
            cy = yy * 2 - 1
            f = np.maximum(f, smooth(Y / 0.15) * smooth((1 - Y) / 0.12) * np.exp(-(((x - px) / 0.20) ** 2 + ((y - cy) / 0.035) ** 2)))
    f *= smooth((1 - np.abs(x)) / 0.12)
    return np.clip(f, 0, 1)


def cristal_tex(W, H, seed):
    """Peau d'un cristal : prisme pointu (pointe en biseau), facettes en paliers, arêtes givrées, fissures. RGBA trans_."""
    rng = np.random.default_rng(seed)
    x, y = grille(W, H)
    v = (y + 1) / 2
    v0 = 49 / 84
    apex = rng.uniform(-0.08, 0.08)
    vt = 0.975
    k = np.clip((v - v0) / (vt - v0), 0, 1)
    gauche = np.where(v < v0, -0.96, -0.96 + (apex - 0.07 + 0.96) * k)
    droite = np.where(v < v0, 0.96, 0.96 + (apex + 0.07 - 0.96) * k)
    dedans = (x > gauche) & (x < droite) & (v > 0.0) & (v < vt)
    bord = np.minimum(x - gauche, droite - x)
    c1, c2 = rng.uniform(-0.45, -0.25), rng.uniform(0.2, 0.4)
    val = np.where(x < c1, 0.62, np.where(x < c2, 0.48, 0.34))
    pan = np.where(x < apex, 0.66, 0.40)
    val = np.where(v > v0, pan + 0.06 * (x < c1 + (apex - c1) * k), val)
    val = val + 0.22 * v - 0.10
    for j in range(3):
        vc = rng.uniform(0.18, v0 - 0.05)
        val = val + 0.16 * np.exp(-((v - vc - 0.18 * np.abs(x - apex * 0.5)) / 0.018) ** 2)
    for c in (c1, c2):
        cc = np.where(v > v0, c + (apex - c) * k, c)
        val = val + 0.18 * np.exp(-((x - cc) / 0.05) ** 2)
    fiss = np.zeros_like(x)
    for j in range(2):
        p = (rng.uniform(-0.6, 0.6), rng.uniform(0.1, 0.5))
        pts = [p]
        for _ in range(3):
            p = (np.clip(p[0] + rng.uniform(-0.35, 0.35), -0.8, 0.8), p[1] + rng.uniform(0.08, 0.18))
            pts.append(p)
        for a_, b_ in zip(pts, pts[1:]):
            fiss = np.maximum(fiss, segment(x, v * 2 - 1, (a_[0], a_[1] * 2 - 1), (b_[0], b_[1] * 2 - 1), 0.045))
    givre_bas = smooth((0.13 - v) / 0.08)
    lisere = smooth((0.20 - bord) / 0.10)
    val = np.maximum(val, 0.95 * np.maximum(lisere, givre_bas))
    val = np.maximum(val, 0.9 * fiss)
    rgb = ramp(np.clip(val, 0, 0.999))
    al = 150 + 35 * (x > c1) * (x < c2) + 30 * v
    al = np.maximum(al, 225 * np.maximum(lisere, givre_bas))
    al = np.maximum(al, 230 * fiss)
    al = np.where(dedans, np.clip(al, 140, 228), 0)
    out = reduire_trans(rgb, al, W, H, seuil=60)
    m = lanczos(dedans * 255.0, W, H) > 110
    out[~m] = 0
    out[m, 3] = np.clip(out[m, 3], 140, 228)
    return out


def givre_sol_f():
    """Hexagone de givre (trans_) : double contour hexagonal en dentelle, flocon central fin, petits flocons semés, voile léger."""
    N = 256
    x, y = grille(N, N, 2)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    f = 0.75 * flocon_f(x, y, R=0.80, w=0.020, rot=0, cotes=((0.35, 0.18), (0.55, 0.20), (0.75, 0.12)))
    f = np.maximum(f, hexagone(x, y, 0, 0, 0.93, 0.024))
    f = np.maximum(f, 0.8 * hexagone(x, y, 0, 0, 0.86, 0.012))
    for k in range(6):                                                  # festons entre les deux contours
        a0 = k * math.pi / 3
        for j in range(1, 6):
            t = j / 6
            px = 0.895 * ((1 - t) * math.cos(a0) + t * math.cos(a0 + math.pi / 3))
            py = 0.895 * ((1 - t) * math.sin(a0) + t * math.sin(a0 + math.pi / 3))
            f = np.maximum(f, 0.9 * flocon_f(x - px, y - py, R=0.030, w=0.010, rot=a0, cotes=()))
    rng = np.random.default_rng(5)
    for _ in range(22):
        rr, aa = rng.uniform(0.45, 0.78), rng.uniform(0, 2 * math.pi)
        cx, cy, R = rr * math.cos(aa), rr * math.sin(aa), rng.uniform(0.03, 0.05)
        f = np.maximum(f, 0.75 * flocon_f(x - cx, y - cy, R=R, w=0.010, rot=rng.uniform(0, 1), cotes=()))
    hexr = r * np.cos((a % (math.pi / 3)) - math.pi / 6) / math.cos(math.pi / 6)   # « rayon » hexagonal
    voile = 0.10 * smooth((hexr - 0.12) / 0.25) * smooth((0.95 - hexr) / 0.10)
    rgb = np.zeros(x.shape + (3,), np.float32)
    rgb[:] = (226, 242, 252)
    al = np.maximum(f * 215, voile * 255) * (hexr < 0.97)
    return reduire_trans(rgb, al, N, N, seuil=8)


def lueur_sol_f(N=64):
    x, y = grille(N, N)
    r = np.hypot(x, y)
    f = 0.75 * np.exp(-((r - 0.80) / 0.14) ** 2) + 0.40 * np.exp(-((r - 0.5) / 0.22) ** 2)
    return f * smooth((0.98 - r) / 0.06)


def nappe_tex(W, H, seed):
    """Nappe de brume (trans_) : dense en bas, effilochée en haut, fondue aux deux bouts."""
    x, y = grille(W, H)
    v = (y + 1) / 2
    n = (0.5 + 0.25 * np.sin(7 * x + seed) + 0.15 * np.sin(17 * x + 2 * seed + 9 * v) + 0.10 * np.sin(31 * x - seed + 14 * v))
    haut = 0.45 + 0.35 * n
    f = smooth((haut - v) / 0.35) * smooth((1 - np.abs(x)) / 0.35) * smooth(v / 0.05)
    rgb = np.zeros(x.shape + (3,), np.float32)
    rgb[:] = (204, 230, 246)
    return reduire_trans(rgb, f * 150, W, H, seuil=5)


def anneau_brume_tex(N=64):
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    tour = 0.6 + 0.25 * np.sin(5 * a + 3 * r) + 0.15 * np.sin(11 * a - 7 * r)
    f = smooth((r - 0.45) / 0.25) * smooth((1 - r) / 0.25) * tour
    rgb = np.zeros(x.shape + (3,), np.float32)
    rgb[:] = (210, 234, 248)
    return reduire_trans(rgb, f * 120, N, N, seuil=5)


def ame_tex(W=8, H=32):
    v = np.linspace(1, 0, H)[:, None] * np.ones((1, W))
    u = np.linspace(-1, 1, W)[None, :] * np.ones((H, 1))
    val = 0.12 + 0.30 * v + 0.10 * (u < 0) - 0.05 * (u > 0.5)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = ramp(val)
    arr[..., 3] = 255
    return arr


UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)


def poser(nom, im, x, y):
    h, w = im.shape[:2]
    assert x + w <= TEX and y + h <= TEX and not tex[y:y + h, x:x + w, 3].any(), nom
    tex[y:y + h, x:x + w] = im
    UV[nom] = (x, y, x + w, y + h)


# Gains additifs : sous ceux de aura_berenice (validée en jeu), cumul estimé < 240 là où halo de tête et rosace se croisent.
G_FORT, G_DOUX, G_ROS, G_CER, G_PIL, G_SOL, G_ECLAT = 0.38, 0.28, 0.56, 0.48, 0.56, 0.30, 0.70
poser("fort0", reduire_add(disque_f(0.0), 64, 64, G_FORT), 0, 0)
poser("fort1", reduire_add(disque_f(2.1), 64, 64, G_FORT), 64, 0)
poser("doux0", reduire_add(disque_f(4.0), 64, 64, G_DOUX), 128, 0)
poser("doux1", reduire_add(disque_f(5.7), 64, 64, G_DOUX), 192, 0)
poser("paillette", reduire_add(etoile4(*grille(16, 16), 0, 0, 1.0, 0.25) * 0.95, 16, 16, 0.95, cutout=True), 256, 0)
poser("eclat", reduire_add(etoile4(*grille(16, 16), 0, 0, 1.0, 0.25) * 0.9, 16, 16, G_ECLAT, cutout=True), 288, 0)
for k in range(2):
    poser(f"ame{k}", ame_tex(), 272 + 8 * k, 0)
poser("nappe0", nappe_tex(128, 32, 1.0), 384, 0)
poser("nappe1", nappe_tex(128, 32, 4.0), 384, 32)
poser("nappe2", nappe_tex(128, 32, 7.0), 256, 32)
ROS, ROS_T = rosace_f(192)
poser("rosace", reduire_add(ROS, 192, 192, G_ROS), 0, 64)
_rgb = np.zeros(ROS_T.shape + (3,), np.float32)
_rgb[:] = (232, 246, 255)
poser("rosaceT", reduire_trans(_rgb, np.clip(ROS_T, 0, 1) * 150, 192, 192, seuil=20), 192, 64)
poser("cercle", reduire_add(cercle_f(128), 128, 128, G_CER), 384, 64)
COL = {"A": (12, 128), "B": (10, 112)}
for (v, (w, h)), (x0, y0) in zip(COL.items(), ((0, 256), (96, 256))):
    for k in range(FR):
        poser(f"pil{v}{k}", reduire_add(pilier_f(w, h, 3 + 4 * (v == "B"), k), w, h, G_PIL), x0 + k * w, y0)
poser("lueur_sol", reduire_add(lueur_sol_f(), 64, 64, G_SOL), 176, 256)
poser("anneau_brume", anneau_brume_tex(), 176, 320)
poser("givre", givre_sol_f(), 256, 256)
NCR = 6
for k in range(NCR):
    _c = cristal_tex(24, 84, 100 + k)
    poser(f"pointe{k}", _c[:35], 24 * k, 384)
    poser(f"cr{k}", _c[35:], 24 * k, 419)

# calque _e : seulement les âmes opaques des cristaux (cœur cyan) ; noir partout ailleurs (rien sur l'additif)
for k in range(2):
    x0, y0, x1, y1 = UV[f"ame{k}"]
    g = np.linspace(0.5, 1.0, y1 - y0)[:, None]
    tex_e[y0:y1, x0:x1, 0] = (22 * g).astype(np.uint8)
    tex_e[y0:y1, x0:x1, 1] = (120 * g).astype(np.uint8)
    tex_e[y0:y1, x0:x1, 2] = (170 * g).astype(np.uint8)
    tex_e[y0:y1, x0:x1, 3] = 255

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
        self.rotation = [round(float(v), 3) for v in rotation] if rotation is not None else None
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


def plaque(g, nom, c, w, h, uv, face="south", ep=0.3):
    c = np.asarray(c, float)
    if face in ("south", "north"):
        a, b = c - (w / 2, h / 2, ep / 2), c + (w / 2, h / 2, ep / 2)
    else:
        a, b = c - (w / 2, ep / 2, h / 2), c + (w / 2, ep / 2, h / 2)
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": r3(a), "to": r3(b), "origin": r3(c), "box_uv": False,
         "faces": {face: {"uv": [round(float(v), 2) for v in uv], "texture": 0}}}
    elements.append(e)
    g.enfants.append(e["uuid"])


def cube(g, nom, a, b, faces):
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": r3(a), "to": r3(b), "origin": r3((np.asarray(a) + b) / 2),
         "box_uv": False, "faces": faces}
    elements.append(e)
    g.enfants.append(e["uuid"])


MEMBRES = {m: G(m, (0, 24, 0)) for m in ("head", "body", "right_arm", "left_arm", "right_leg", "left_leg")}

# --- halo : membre > aura_z (événements) > etat_z (états) > add_z > ctrl_alpha, cam_…
RECUL = {"tete": 4.5, "corps": 4.0, "bras_d": 3.4, "bras_g": 3.4, "jambe_d": 3.4, "jambe_g": 3.4}
ZONES = {
    "tete": ("head", (0, 28, 0), [((0, 28.2, 0), 9.6, "fort")]),
    "corps": ("body", (0, 18, 0), [((0, 21.5, 0), 6.6, "fort"), ((0, 18, 0), 6.0, "doux"), ((0, 14.5, 0), 6.0, "doux")]),
    "bras_d": ("right_arm", (6, 18, 0), [((6, 21.5, 0), 5.6, "doux"), ((6, 18, 0), 5.0, "doux"), ((6, 14.2, 0), 4.8, "doux")]),
    "bras_g": ("left_arm", (-6, 18, 0), [((-6, 21.5, 0), 5.6, "doux"), ((-6, 18, 0), 5.0, "doux"), ((-6, 14.2, 0), 4.8, "doux")]),
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

# --- rosace derrière la nuque : head > aura_rosace > etat_rosace > cam_rosace > add_ (flocon qui tourne, cercle fixe) ; trans_ derrière
GC = (0, 26.5, 0)
GR = 7.5
AURA["rosace"] = G("aura_rosace", GC, MEMBRES["head"])
ETAT["rosace"] = G("etat_rosace", GC, AURA["rosace"])
CAMG = G("cam_rosace", GC, ETAT["rosace"])
ADD["rosace"] = G("add_rosace", GC, CAMG)
ALPHA["rosace"] = G("ctrl_alpha", GC, ADD["rosace"])
TOURNE_F = G("tourne_flocon", (GC[0], GC[1], GC[2] - GR), ADD["rosace"])
plaque(TOURNE_F, "rosace", (GC[0], GC[1], GC[2] - GR), 30, 30, UV["rosace"])
PULSE_C = G("pulse_cercle", (GC[0], GC[1], GC[2] - GR - 0.2), ADD["rosace"])
plaque(PULSE_C, "cercle", (GC[0], GC[1], GC[2] - GR - 0.2), 36, 36, UV["cercle"])
TRANS_R = G("trans_rosace", GC, CAMG)
ALPHA["rosace_t"] = G("ctrl_alpha", GC, TRANS_R)
TOURNE_T = G("tourne_voile", (GC[0], GC[1], GC[2] - GR - 0.5), TRANS_R)
plaque(TOURNE_T, "rosace_voile", (GC[0], GC[1], GC[2] - GR - 0.5), 30, 30, UV["rosaceT"])

# --- piliers : body > aura_flux > etat_flux > monte_flux (pivot au sol) > camy_flux > add_flux ; z < 0 = derrière le joueur
FLUX_C = (0, 14, 0)
AURA["flux"] = G("aura_flux", FLUX_C, MEMBRES["body"])
ETAT["flux"] = G("etat_flux", FLUX_C, AURA["flux"])
MONTE = G("monte_flux", (0, 0, 0), ETAT["flux"])
CAMY = G("camy_flux", FLUX_C, MONTE)
ADD["flux"] = G("add_flux", FLUX_C, CAMY)
ALPHA["flux"] = G("ctrl_alpha", FLUX_C, ADD["flux"])
PILIERS = [  # (x, z, base y, hauteur, largeur, type)
    (0.0, -4.8, 16.0, 30.0, 4.6, "A"),
    (-4.4, -4.3, 11.0, 27.0, 4.0, "A"), (4.4, -4.45, 11.5, 26.0, 4.0, "A"),
    (-8.2, -3.7, 3.5, 25.0, 3.4, "B"), (8.2, -3.85, 3.0, 24.0, 3.4, "B"),
    (-5.8, -3.0, -0.5, 18.0, 3.0, "B"), (5.8, -3.15, -0.5, 17.0, 3.0, "B"),
]
COLS = []
for i, (x, zz, y0, h, w, t) in enumerate(PILIERS):
    base = (x, y0, zz)
    g = G(f"pilier{i}", base, ADD["flux"])
    plaque(g, f"pilier{i}", (x, y0 + h / 2, zz), w, h, UV[f"pil{t}0"])
    COLS.append((g, G("ctrl_uv", base, g), t, i))

# --- sol : body > aura_sol (événements) > etat_sol (états : 0 = masqué) > secteurs > grappes ; givre, brume, lueur
SC = (0, 0.4, 0)
AURA["sol"] = G("aura_sol", SC, MEMBRES["body"])
ETAT["sol"] = G("etat_sol", SC, AURA["sol"])
SECT = {s_: G(f"secteur_{s_}", SC, ETAT["sol"]) for s_ in ("cotes", "diagonales")}
POSE_GIVRE = G("pose_givre", SC, ETAT["sol"])
TRANS_GIVRE = G("trans_givre", SC, POSE_GIVRE)
ALPHA["givre"] = G("ctrl_alpha", SC, TRANS_GIVRE)
TOURNE_G = G("tourne_givre", SC, TRANS_GIVRE)
plaque(TOURNE_G, "givre", (0, 0.25, 0), 22, 22, UV["givre"], face="up")
TRANS_AB = G("trans_anneau_brume", SC, POSE_GIVRE)
ALPHA["anneau_brume"] = G("ctrl_alpha", SC, TRANS_AB)
TOURNE_AB = G("tourne_anneau_brume", SC, TRANS_AB)
plaque(TOURNE_AB, "anneau_brume", (0, 0.5, 0), 25, 25, UV["anneau_brume"], face="up")
ADD["sol"] = G("add_lueur_sol", SC, POSE_GIVRE)          # au-dessus des trans_ (sinon ils la cacheraient vue d'en haut)
ALPHA["sol"] = G("ctrl_alpha", SC, ADD["sol"])
PULSE_SOL = G("pulse_lueur_sol", SC, ADD["sol"])
plaque(PULSE_SOL, "lueur_sol", (0, 0.75, 0), 22, 22, UV["lueur_sol"], face="up")

CRISTAUX = []      # (groupe pousse, angle, hauteur, secteur)
ECLATS = []
A_EL, B_EL = 7.6, 8.6       # demi-axes de l'hexagone des grappes : côtés (x), devant/derrière (z)
nc = 0
for j in range(6):
    th0 = j * 60.0                                        # 0 et 180 : côtés ; les autres : diagonales devant et derrière
    cote = j in (0, 3)
    for kk, (dth, dr, hh, tilt) in enumerate(((0, 0, 1.0, 12), (-13, -0.9, 0.5, 30), (12, -0.6, 0.62, 26))):
        th = th0 + dth + RNG.uniform(-3, 3)
        c, s_ = math.cos(math.radians(th)), math.sin(math.radians(th))
        rr = 1 / math.sqrt((c / A_EL) ** 2 + (s_ / B_EL) ** 2) + dr
        h = (4.4 if cote else 3.3) * hh * RNG.uniform(0.92, 1.08)
        w = (0.9 + 0.32 * h / 4) * RNG.uniform(0.94, 1.06)
        yaw = 90 - th + RNG.uniform(-10, 10)
        base = (rr * c, 0.0, rr * s_)
        nc += 1
        g = G(f"cristal{nc}", base, SECT["cotes" if cote else "diagonales"], rotation=(0, yaw, 0))
        p = G(f"pousse{nc}", base, g, rotation=(tilt + RNG.uniform(-3, 3), 0, 0))
        tr = G(f"trans_cristal{nc}", base, p)
        bx, by, bz = base
        var = UV[f"cr{nc % NCR}"]
        inv = [var[2], var[1], var[0], var[3]]
        y0 = by + 0.05
        hb = h * 49 / 84
        cube(tr, f"peau{nc}", (bx - w / 2, y0, bz - w / 2), (bx + w / 2, y0 + hb, bz + w / 2),
             {"north": {"uv": list(var), "texture": 0}, "south": {"uv": inv, "texture": 0},
              "east": {"uv": inv, "texture": 0}, "west": {"uv": list(var), "texture": 0}})
        pu = UV[f"pointe{nc % NCR}"]
        pinv = [pu[2], pu[1], pu[0], pu[3]]
        wd = w * 1.41
        for q, ang in enumerate((45, -45)):
            e = {"name": f"pointe{nc}_{q + 1}", "type": "cube", "uuid": nuid(),
                 "from": r3((bx - wd / 2, y0 + hb, bz - 0.15)), "to": r3((bx + wd / 2, y0 + h, bz + 0.15)),
                 "origin": r3((bx, y0 + hb, bz)), "rotation": [0, ang, 0], "box_uv": False,
                 "faces": {"north": {"uv": list(pu), "texture": 0}, "south": {"uv": pinv, "texture": 0}}}
            elements.append(e)
            tr.enfants.append(e["uuid"])
        aw = w * 0.17
        ua = UV[f"ame{nc % 2}"]
        side = {"uv": list(ua), "texture": 0}
        capu = {"uv": [ua[0], ua[1], ua[0] + 4, ua[1] + 4], "texture": 0}
        cube(p, f"ame{nc}", (bx - aw, y0 + 0.02, bz - aw), (bx + aw, y0 + h * 0.62, bz + aw),
             {"north": side, "south": side, "east": side, "west": side, "up": capu, "down": capu})
        CRISTAUX.append((p, th, h, "cotes" if cote else "diagonales"))
        if kk == 0:                                        # éclat au bout du grand cristal de chaque grappe
            tip = (bx, y0 + h * 0.95, bz)
            ad = G(f"add_eclat{len(ECLATS) + 1}", tip, p)
            ce = G(f"cam_eclat{len(ECLATS) + 1}", tip, ad)
            plaque(ce, f"eclat{len(ECLATS) + 1}", (tip[0], tip[1], tip[2] - 0.9), 2.0, 2.0, UV["eclat"])
            ECLATS.append(ce)

# --- brume basse : body > aura_brume > etat_brume > camy_brume > trans_brume ; plus loin que les piliers (z -5,6 à -6,4)
BC = (0, 0.0, 0)
AURA["brume"] = G("aura_brume", BC, MEMBRES["body"])
ETAT["brume"] = G("etat_brume", BC, AURA["brume"])
CAMYB = G("camy_brume", (0, 1, 0), ETAT["brume"])
TRANS_BRUME = G("trans_brume", (0, 1, 0), CAMYB)
ALPHA["brume"] = G("ctrl_alpha", (0, 1, 0), TRANS_BRUME)
NAPPES = []
for k, (x, zz, w, h) in enumerate(((0.0, -5.6, 26, 4.2), (-3.4, -6.0, 19, 3.2), (3.6, -6.4, 21, 3.6))):
    g = G(f"nappe{k + 1}", (x, 0, zz), TRANS_BRUME)
    plaque(g, f"nappe{k + 1}", (x, h / 2 + 0.1, zz), w, h, UV[f"nappe{k}"])
    NAPPES.append(g)

# --- points de départ (+Y du groupe = vers le haut)
EMITS = []


def emit(nom, p, parent):
    EMITS.append(G(nom, p, parent))


PAILLETTES = [("tete", (0, 33, 0)), ("tete", (3.8, 31, 1.5)), ("tete", (-3.8, 31, 1.5)), ("corps", (2.6, 22, 2.6)),
              ("corps", (-2.6, 16, 2.6)), ("bras_d", (8.4, 22, 0)), ("bras_d", (6.5, 12.5, 0)), ("bras_g", (-8.4, 22, 0)),
              ("bras_g", (-6.5, 12.5, 0)), ("jambe_d", (4.4, 4, 0)), ("jambe_g", (-4.4, 4, 0)), ("jambe_d", (2, 1, 2.5))]
for k, (z, p) in enumerate(PAILLETTES):
    emit("emit_paillette" + (str(k + 1) if k else ""), p, ETAT[z])

# --- particule : paillette de poussière de diamant, un seul cube de 0,3 px, face south seule (réglage : Face caméra)
PART = G("particle_paillette", (0, 0, 0))
plaque(PART, "paillette", (0, 0.75, 0), 0.6, 0.6, UV["paillette"])

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


PH = {z: int(RNG.integers(0, 360)) for z in list(ZONES) + ["flux", "sol", "rosace", "brume", "givre", "anneau_brume"]}
PH_C = [(int(RNG.integers(0, 360)), int(RNG.integers(0, 360))) for _ in COLS]


def etat(nom, L, haut=1.0, larg=1.0, vac=0.05, halo=1.0, souffle=0.035, alpha=-0.15, a_amp=0.08, flux=(0, 0, 0), recul=0.0,
         sol=1.0, diag=1.0, ros=1.0, r_alpha=0.0, r_recul=0.0, brume=1.0, b_pos=(0, 0, 0), b_larg=1.0, kv=2, kb=1):
    """haut/larg/vac : piliers ; halo/souffle : disques ; alpha/a_amp : opacité ; flux : décalage des piliers (+Z arrière) ;
    recul : halo vers l'arrière ; sol : sol entier (0 masqué) ; diag : grappes de devant et de derrière ; ros, r_alpha,
    r_recul : rosace ; brume, b_pos, b_larg : nappes."""
    A = {}
    for z in ZONES:
        sc = sinus(L, kb, PH[z], halo * souffle, halo)
        piste(A, ETAT[z], [kf("scale", 0, sc, sc, sc)])
        if recul:
            piste(A, ETAT[z], [kf("position", 0, 0, 0, recul)])
    for z in list(ZONES) + ["flux", "sol"]:
        piste(A, ALPHA[z], [kf("position", 0, sinus(L, kb, PH[z] + 90, a_amp, alpha), 0, 0)])
    sg = sinus(L, kb, PH["rosace"], ros * 0.03, ros)
    piste(A, ETAT["rosace"], [kf("scale", 0, sg, sg, sg)])
    if r_recul:
        piste(A, ETAT["rosace"], [kf("position", 0, 0, 0, r_recul)])
    for z in ("rosace", "rosace_t"):
        piste(A, ALPHA[z], [kf("position", 0, sinus(L, kb, PH["rosace"] + 90, 0.07, alpha * 0.5 + r_alpha), 0, 0)])
    if any(flux):
        piste(A, ETAT["flux"], [kf("position", 0, *flux)])
    for (g, _, t, i), (p1, p2) in zip(COLS, PH_C):
        k1, k2 = kv + (i % 2), kv + 1 + (i % 3)
        sy = f"{s(haut)}*(1+{s(vac)}*math.sin(q.anim_time*{s(360 * k1 / L)}+{p1})+{s(vac * 0.5)}*math.sin(q.anim_time*{s(360 * k2 / L)}+{p2}))"
        sx = sinus(L, k2, p2 + 60, larg * vac * 0.3, larg)
        piste(A, g, [kf("scale", 0, sx, sy, 1)])
    piste(A, ETAT["sol"], [kf("scale", 0, sol, sol, sol)])
    piste(A, SECT["diagonales"], [kf("scale", 0, diag, diag, diag)])
    piste(A, SECT["cotes"], [kf("scale", 0, 1, 1, 1)])
    piste(A, ALPHA["givre"], [kf("position", 0, sinus(L, kb, PH["givre"], 0.05, -0.05), 0, 0)])
    if brume:
        sb = sinus(L, kb, PH["brume"], 0.05 * brume, brume)
        piste(A, ETAT["brume"], [kf("scale", 0, f"({sb})*{s(b_larg)}", sb, f"({sb})*{s(b_larg)}")])
    else:
        piste(A, ETAT["brume"], [kf("scale", 0, 0, 0, 0)])
    if any(b_pos):
        piste(A, ETAT["brume"], [kf("position", 0, *b_pos)])
    for z in ("brume", "anneau_brume"):
        piste(A, ALPHA[z], [kf("position", 0, sinus(L, kb, PH[z] + 45, 0.1, -0.1), 0, 0)])
    return {"uuid": nuid(), "name": nom, "loop": "loop", "override": False, "length": L, "snapping": 24, "selected": nom == "idle",
            "animators": A}


STATES = [
    etat("idle", 8.0, kv=2, kb=1),                                                                 # respiration de 8 s
    etat("walk", 1.6, haut=1.04, flux=(0, 0, 1.5), recul=0.3, r_recul=0.6, b_pos=(0, 0, 2.0), b_larg=1.08, kv=1),
    etat("run", 1.0, haut=1.15, larg=0.9, vac=0.07, alpha=-0.05, a_amp=0.03, flux=(0, -0.5, 3.5), recul=0.8, diag=0, ros=1.04,
         r_recul=1.6, b_pos=(0, 0, 4.0), b_larg=1.22, kv=1),
    etat("sneak", 4.0, haut=0, larg=0, halo=0.9, alpha=-0.35, flux=(0, -3.5, 1.5), sol=0, ros=0.78, r_alpha=-0.15, brume=0, kv=1),
    etat("fly", 2.4, haut=1.1, larg=0.95, alpha=-0.1, flux=(0, 0, 2.0), recul=0.4, sol=0, ros=1.04, r_recul=0.8,
         brume=0.9, b_pos=(0, -1.0, 1.5), kv=1),
    etat("glide", 3.6, haut=0, larg=0, alpha=-0.15, sol=0, ros=0.6, r_alpha=-0.2, brume=0, kv=1),
    etat("swim", 3.6, haut=0, larg=0, alpha=-0.3, sol=0, ros=0.5, r_alpha=-0.3, brume=0, kv=1),
    etat("fall", 2.0, haut=1.2, larg=0.85, halo=1.04, alpha=-0.1, flux=(0, 1.0, 0), sol=0, ros=1.06, brume=0.9,
         b_pos=(0, 1.5, 0), kv=1),
    etat("mount", 4.0, haut=0, larg=0, alpha=-0.25, flux=(0, -1.0, 0), sol=0, ros=0.9, brume=0, kv=1),
    etat("sleep", 4.0, haut=0, larg=0, vac=0.03, halo=0.85, souffle=0.02, alpha=-0.8, a_amp=0.05, sol=0, ros=0.55,
         r_alpha=-0.35, brume=0, kv=1),
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


def ordre(th):
    """0 devant le joueur (-Z), 1 derrière : la cascade part de l'avant et fait le tour des deux côtés."""
    return abs(((th - 270) + 180) % 360 - 180) / 180


# event_equip (2,4 s) : le givre se répand (0-0,7 s), les cristaux poussent depuis l'avant (0,3-1,3 s), les piliers montent
# (0,5-1,5 s), le halo s'allume des pieds vers la tête (0,6-1,8 s), la rosace cristallise en tournant (1,4-2,2 s) ; un carillon.
LE = 2.4
TE = [j * LE / 24 for j in range(25)]
A = {}
piste(A, POSE_GIVRE, [kf("scale", t, sm(t, 0.0, 0.7), 1, sm(t, 0.0, 0.7)) for t in TE])
for p, th, h, sec in CRISTAUX:
    t0 = 0.3 + 0.7 * ordre(th)
    piste(A, p, [kf("scale", t, sm(t, t0, t0 + 0.3) ** 0.7, sm(t, t0, t0 + 0.4) * (1 + 0.12 * bump(t, t0 + 0.25, t0 + 0.4, t0 + 0.45, t0 + 0.75)),
                    sm(t, t0, t0 + 0.3) ** 0.7) for t in TE])
piste(A, MONTE, [kf("scale", t, 1, sm(t, 0.5, 1.5), 1) for t in TE])
piste(A, AURA["brume"], [kf("scale", t, 1, sm(t, 0.2, 1.0), 1) for t in TE])
for g in DISQUES:
    t0 = 0.6 + (HAUT[g.uuid] / 30) * 0.8
    piste(A, g, [kf("scale", t, *([sm(t, t0, t0 + 0.45)] * 3)) for t in TE])
piste(A, AURA["rosace"], [kf("scale", t, *([sm(t, 1.4, 1.95) * (1 + 0.1 * bump(t, 1.75, 1.95, 2.0, 2.35))] * 3)) for t in TE])
for g in (TOURNE_F, TOURNE_T):
    piste(A, g, [kf("rotation", t, 0, 0, -60 * (1 - sm(t, 1.4, 2.2))) for t in TE])
A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "block.amethyst_block.chime", "file": ""}], "time": 1.6}]}
equip = {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": LE, "snapping": 24, "selected": False,
         "animators": A}

# overlay_givre (60 s) : film des piliers, rosace qui tourne (un tour en 60 s, le voile avec elle), cercle qui pulse, disques
# qui tournent lentement, éclats brefs au bout des cristaux (déphasés), brume qui ondule, givre et anneau de brume qui tournent.
LO = 60.0
A = {}
for (g, uvg, t, i) in COLS:
    w = COL[t][0]
    fps = 5 + (i % 3)                                   # 300, 360 ou 420 images par boucle : film fermé (multiple de FR)
    piste(A, uvg, [kf("position", 0, f"math.floor(math.mod(q.anim_time*{fps}+{i * 3},{FR}))*{w}", 0, 0)])
for g in (TOURNE_F, TOURNE_T):
    piste(A, g, [kf("rotation", 0, 0, 0, f"q.anim_time*{s(360 / LO)}")])
pul = f"1+0.035*math.sin(q.anim_time*{s(360 * 8 / LO)})"
piste(A, PULSE_C, [kf("scale", 0, pul, pul, 1)])
for j, g in enumerate(DISQUES):
    piste(A, g, [kf("rotation", 0, 0, 0, f"q.anim_time*{s((1 if j % 2 else -1) * 360 / LO)}")])
for j, g in enumerate(ECLATS):
    ph = int(j * 360 / len(ECLATS) * 5 % 360)
    e = f"math.pow(math.max(0,math.sin(q.anim_time*{s(360 * 8 / LO)}+{ph})),14)"
    piste(A, g, [kf("scale", 0, e, e, e), kf("rotation", 0, 0, 0, f"q.anim_time*{s(360 * 2 / LO)}")])
for j, g in enumerate(NAPPES):
    k1, k2 = 3 + j, 5 + 2 * j
    piste(A, g, [kf("position", 0, sinus(LO, k1, 70 * j, 1.3), 0, 0), kf("scale", 0, 1, sinus(LO, k2, 110 * j + 30, 0.14, 1.0), 1)])
piste(A, TOURNE_AB, [kf("rotation", 0, 0, f"q.anim_time*{s(-360 / LO)}", 0)])
p_sol = sinus(LO, 8, 0, 0.03, 1.0)
piste(A, PULSE_SOL, [kf("scale", 0, p_sol, 1, p_sol)])
overlay = {"uuid": nuid(), "name": "overlay_givre", "loop": "loop", "override": False, "length": LO, "snapping": 24, "selected": False,
           "animators": A}

# Paillette : scintille (échelle), sans rotation pour rester face caméra.
PF = 1.2
pt = [i * PF / 12 for i in range(13)]
p_fall = {"uuid": nuid(), "name": "particle_paillette_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24,
          "selected": False, "animators": {PART.uuid: {"name": PART.nom, "type": "bone", "keyframes":
              [kf("scale", t, *([1 + 0.25 * math.sin(2 * math.pi * t / PF)] * 3)) for t in pt]}}}

ANIMS = STATES + [equip, overlay, p_fall]
assert len(EMITS) <= 32
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
from ambiance import ajouter_ambiance
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
from menu_aura import adapter_menu
adapter_menu(model, cacher=False)
ajouter_ambiance(model)
# contrôle : rien d'allumé dans _e hors des âmes opaques (ajouter_ambiance n'y touche que là où la texture est claire et chaude)
_te = next(t for t in model["textures"] if t["name"].endswith("_e.png"))
_e = np.array(Image.open(io.BytesIO(base64.b64decode(_te["source"].split(",", 1)[1]))).convert("RGBA"))
_hors = _e[..., :3].max(axis=2) > 0
for k in range(2):
    x0, y0, x1, y1 = UV[f"ame{k}"]
    _hors[y0:y1, x0:x1] = False
assert not _hors.any(), "calque _e allumé hors des âmes"
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
