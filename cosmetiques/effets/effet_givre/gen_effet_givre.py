"""Tempête de givre (v2) : effet de téléportation de l'ensemble Givre (guide 15). Design original (fiche .claude/styles/givre.md,
section de l'effet ; références .claude/references/effets/ : principes-fx-anime, elements « Glace », impacts-attaques).
Écrit effet_givre.png, effet_givre_e.png et .build/effet_givre_brut.bbmodel.

Retours : v1 « manque de particules et d'animation » ; « s'inspirer des animes, sons custom » ; « un cristal un peu incliné qui
nous gèle pour la disparition, qui éclate ; l'apparition, une formation de cristaux qui apparaît comme une explosion, chaque
cristal pousse vite et on apparaît dedans, pour finir en poussière de petites particules, comme une dissipation de sort ».

Pièces (posées au sol, pieds du joueur à l'origine, face à -Z ; aucun groupe du corps)
- Cercle de givre lisible (traits de 8 à 12 texels, motif invariant par miroir et transposition) : deux couches trans_ (+ même
  dessin au calque _e) et add_ qui tournent en sens contraire (overlay), 12 runes add_ allumées en vague (ctrl_alpha).
- cristal() : prisme hexagonal de glace, 6 facettes trans_ en éventail (arêtes claires, reflet peint), pointe en 6 facettes,
  âme opaque (_e). Couronne de 8 petits cristaux ; cristal du départ (apothème 9,4, 56 px, incliné de 12°) avec givre qui
  grimpe dedans, 18 fissures add_, cœur camy_ add_, 3 satellites ; formation de 11 cristaux de l'arrivée.
- 16 gros éclats (prismes et tessons croisés), flash en deux temps et traits de vitesse (add_ cam_), onde, givre au sol,
  bouffées de neige (camy_), tempête de rubans en spirale.
- Particules (30 points emit_, ctrl_emit chacun) : flocon, poudre, eclat (modélisées) ; snowflake, item_snowball, poof,
  dust_bfeaff_12 (Minecraft).

Animations : charge (loop 3 s), depart (3,6 s : pousse, gèle, se fend, gel d'image, éclate), arrivee (3,6 s : formation qui
explose, le joueur apparaît dedans, dissolution en poussière), overlay_givre, particle_*_fall.
Sons embarqués originaux (sons/*.py, tools/synthe.py) : givre_forme (la glace se forme : départ et arrivée), givre_eclate (fissure) ; bris : block.glass.break du jeu ; aucun pendant la charge.
Hasard (guide 6.3) : bascule ±12° et lacet du gros cristal, ±12° et rotation propre des petits, tirés au début de chaque animation (v.gd, v.ga) et gardés.

Ce qui se juge seulement en jeu (onglet Effets, « Essayer ») : particules et cadences, additif réel, tri trans_ du cristal
autour de la copie du joueur avec et sans shader, orientation des UV des faces horizontales, volume des sons.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "effet_givre"
TEX = 512
SS = 4
RNG = np.random.default_rng(31)

# ------------------------------------------------------------------ palettes (fiche Givre)
STOPS = [(0.0, (0, 0, 0)), (0.15, (3, 14, 28)), (0.35, (12, 50, 88)), (0.6, (36, 112, 162)),
         (0.85, (92, 176, 218)), (1.0, (140, 206, 236))]
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


def reduire_add(f, W, H, gain):
    """Additif : image RGBA, alpha 0/255 ; le presque noir est transparent."""
    rgb = lanczos(palette(f) * gain, W, H)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = rgb
    a = arr[..., :3].max(axis=2) > 12
    arr[..., 3] = a * 255
    arr[~a, :3] = 0
    return arr


def reduire_trans(rgb, al, W, H, seuil=6):
    c = np.stack([lanczos(rgb[..., k], W, H) for k in range(3)], axis=-1)
    a = lanczos(al, W, H)
    arr = np.zeros((H, W, 4), np.uint8)
    a = np.where(a > seuil, np.clip(a, 1, 254), 0)
    arr[..., :3] = c
    arr[..., 3] = a
    arr[a == 0, :3] = 0
    return arr


def segment(x, y, p, q, w):
    px, py = p
    dx, dy = q[0] - px, q[1] - py
    L2 = dx * dx + dy * dy + 1e-12
    t = np.clip(((x - px) * dx + (y - py) * dy) / L2, 0, 1)
    d = np.hypot(x - px - t * dx, y - py - t * dy)
    return np.clip((w - d) / (w * 0.35), 0, 1)


def anneau(r, r0, w):
    return np.clip((w - np.abs(r - r0)) / (w * 0.35), 0, 1)


def flocon_f(x, y, R=1.0, w=0.05, rot=math.pi / 6, cotes=((0.38, 0.30), (0.62, 0.22), (0.82, 0.12))):
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


def lignes_trans(f, N, a_max=228, voile=None):
    """Dessin de lumière en trans_ : cœur presque blanc, bord cyan ; alpha selon l'intensité du trait."""
    rgb = ramp(0.62 + 0.37 * np.clip(f, 0, 1))
    al = f * a_max
    if voile is not None:
        al = np.maximum(al, voile)
    return reduire_trans(rgb, al, N, N, seuil=20)


# ------------------------------------------------------------------ peinture
def cercle_a_f():
    """Couche extérieure, lisible en jeu (retour sur effet_berenice : traits fins effacés par les mipmaps) : traits de 8 à 12
    texels sur 224, peu de détails. Double anneau épais, 12 losanges, bande de 12 glyphes de givre inventés (0,755-0,895)."""
    x, y = grille(224, 224)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    f = np.maximum(anneau(r, 0.955, 0.050), anneau(r, 0.875, 0.034))
    f = np.maximum(f, anneau(r, 0.705, 0.040))
    rng = np.random.default_rng(7)
    for k in range(12):                                      # losanges pleins entre les deux anneaux extérieurs
        ph = k * math.pi / 6 + math.pi / 12
        c = np.array([0.915 * math.cos(ph), 0.915 * math.sin(ph)])
        t_ = np.array([-math.sin(ph), math.cos(ph)])
        r_ = np.array([math.cos(ph), math.sin(ph)])
        u, v = (x - c[0]) * t_[0] + (y - c[1]) * t_[1], (x - c[0]) * r_[0] + (y - c[1]) * r_[1]
        f = np.maximum(f, np.clip((1 - np.abs(u) / 0.05 - np.abs(v) / 0.04) / 0.25, 0, 1))
    for j in range(12):                                      # glyphes : tige épaisse + deux traits de givre
        ph = j * 2 * math.pi / 12
        c = np.array([0.79 * math.cos(ph), 0.79 * math.sin(ph)])
        tg = np.array([-math.sin(ph), math.cos(ph)])
        rd = np.array([math.cos(ph), math.sin(ph)])
        S = 0.062

        def P(u, v):
            return c + S * (u * tg + v * rd)
        traits = [((0, -0.9), (0, 0.9))]
        h = 0.1                                          # tous les glyphes identiques et symétriques : motif invariant par miroir
        ch = 0                                           # et transposition (orientation des UV « up » non calibrée en jeu)
        if ch == 0:
            traits += [((0, h), (-0.7, h + 0.6)), ((0, h), (0.7, h + 0.6))]
        elif ch == 1:
            traits += [((-0.65, -0.35), (0.65, -0.35)), ((-0.5, 0.45), (0.5, 0.45))]
        else:
            traits += [((0, 0.4), (0.55, 0.0)), ((0, 0.4), (-0.55, 0.0))]
        for p, q in traits:
            f = np.maximum(f, segment(x, y, P(*p), P(*q), 0.036))
    voile = 34 * smooth((r - 0.705) / 0.01) * smooth((0.875 - r) / 0.01)
    f = f * (r < 0.995)
    return f, voile


def cercle_b_f():
    """Couche intérieure, traits épais (≥ 8 texels sur 160) : anneau, hexagramme, six nœuds ronds, grand flocon central."""
    x, y = grille(160, 160)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    f = anneau(r, 0.955, 0.055)
    V = 0.90
    for k0 in (0, 1):
        pts = [(V * math.cos(math.pi / 2 + k0 * math.pi / 3 + i * 2 * math.pi / 3),
                V * math.sin(math.pi / 2 + k0 * math.pi / 3 + i * 2 * math.pi / 3)) for i in range(4)]
        for p, q in zip(pts, pts[1:]):
            f = np.maximum(f, segment(x, y, p, q, 0.045))
    for i in range(6):
        ph = math.pi / 2 + i * math.pi / 3
        cx, cy = V * math.cos(ph), V * math.sin(ph)
        d = np.hypot(x - cx, y - cy)
        f = np.where(d < 0.10, 0, f)
        f = np.maximum(f, anneau(d, 0.085, 0.040))
    f = np.maximum(f, anneau(r, 0.50, 0.045))
    f = np.maximum(f, flocon_f(x, y, R=0.40, w=0.050, cotes=((0.45, 0.32), (0.75, 0.2))))
    f = np.maximum(f, np.clip((0.07 - r) / 0.02, 0, 1))
    voile = 26 * smooth((0.5 - r) / 0.02)
    return f * (r < 0.995), voile



def flou(f, N):
    """Version floue pour la lueur additive (réduite puis agrandie)."""
    im = Image.fromarray(np.clip(f * 255, 0, 255).astype(np.uint8))
    im = im.resize((N // 2, N // 2), Image.BILINEAR).resize((N, N), Image.BILINEAR)
    g = np.asarray(im).astype(np.float32) / 255
    return np.clip(g * 1.6, 0, 1)


def cristal_tex(W, H, seed):
    """Peau d'un cristal (reprise de aura_givre) : prisme pointu, facettes en paliers, arêtes givrées, fissures. RGBA trans_."""
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
        ch = np.exp(-((v - vc - 0.18 * np.abs(x - apex * 0.5)) / 0.018) ** 2)
        val = val + 0.16 * ch
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


def gangue_tex(W, H, seed, pointes=True):
    """Paroi de glace translucide en facettes verticales, givre au pied, fissures ; sommet en pointes ou droit (cristal géant)."""
    rng = np.random.default_rng(seed)
    x, y = grille(W, H)
    v = (y + 1) / 2
    # sommet découpé : 3 pointes de hauteurs différentes
    pics = np.full_like(x, 0.80)
    for cx, hp, lw in ((-0.55, rng.uniform(0.90, 0.95), 0.5), (0.05, rng.uniform(0.95, 0.99), 0.55), (0.62, rng.uniform(0.86, 0.92), 0.45)):
        pics = np.maximum(pics, hp - (hp - 0.80) * np.abs(x - cx) / lw)
    if not pointes:
        pics = np.full_like(x, 0.985)
    dedans = (v < pics) & (np.abs(x) < 0.985)
    bord_h = pics - v
    cols = np.sort(rng.uniform(-0.8, 0.8, 3))
    val = 0.40 + 0.10 * np.sin(3.1 * x + seed) + 0.18 * v
    for c in cols:
        val = val + 0.16 * np.exp(-((x - c) / 0.04) ** 2)
    val = np.where((x > cols[0]) & (x < cols[1]), val + 0.08, val)
    fiss = np.zeros_like(x)
    for j in range(4):
        p = (rng.uniform(-0.7, 0.7), rng.uniform(0.05, 0.75))
        pts = [p]
        for _ in range(4):
            p = (np.clip(p[0] + rng.uniform(-0.3, 0.3), -0.9, 0.9), p[1] + rng.uniform(0.04, 0.10))
            pts.append(p)
        for a_, b_ in zip(pts, pts[1:]):
            fiss = np.maximum(fiss, segment(x, v * 2 - 1, (a_[0], a_[1] * 2 - 1), (b_[0], b_[1] * 2 - 1), 0.03))
    givre_bas = smooth((0.12 - v) / 0.08)
    lisere = smooth((0.035 - bord_h) / 0.025)
    val = np.maximum(val, 0.95 * np.maximum(lisere, givre_bas))
    val = np.maximum(val, 0.92 * fiss)
    rgb = ramp(np.clip(val, 0, 0.999))
    al = 112 + 40 * v + 20 * np.sin(5 * x + 2 * seed)
    al = np.maximum(al, 220 * np.maximum(lisere, givre_bas))
    al = np.maximum(al, 215 * fiss)
    al = np.where(dedans, np.clip(al, 100, 225), 0)
    out = reduire_trans(rgb, al, W, H, seuil=50)
    m = lanczos(dedans * 255.0, W, H) > 110
    out[~m] = 0
    out[m, 3] = np.clip(out[m, 3], 100, 225)
    return out


def ruban_tex(W, H, seed):
    """Ruban de tempête : traînées de neige fines en diagonale, flocons, dense en bas, effiloché en haut. trans_."""
    rng = np.random.default_rng(seed)
    x, y = grille(W, H)
    v = (y + 1) / 2
    f = np.zeros_like(x)
    for _ in range(3):                                       # bandes de vent larges et douces
        u0, pente = rng.uniform(-0.8, 0.8), rng.uniform(-0.4, 0.4)
        c = u0 + pente * v + 0.12 * np.sin(6 * v + rng.uniform(0, 6))
        f = np.maximum(f, 0.45 * np.exp(-((x - c) / 0.22) ** 2) * smooth((0.9 - v) / 0.4))
    for _ in range(10):
        u0, pente, lw = rng.uniform(-1.2, 1.2), rng.uniform(-0.5, 0.5), rng.uniform(0.04, 0.10)
        v0, v1 = sorted(rng.uniform(0.0, 1.0, 2))
        v1 = max(v1, v0 + 0.3)
        c = u0 + pente * v + 0.08 * np.sin(9 * v + rng.uniform(0, 6))
        long_ = smooth((v - v0) / 0.12) * smooth((v1 - v) / 0.2)
        f = np.maximum(f, rng.uniform(0.55, 1.0) * np.exp(-((x - c) / lw) ** 2) * long_)
    dots = np.zeros_like(x)
    for _ in range(22):
        cx, cy, rr = rng.uniform(-0.9, 0.9), rng.uniform(0.02, 0.95), rng.uniform(0.03, 0.06)
        dots = np.maximum(dots, np.clip((rr - np.hypot((x - cx) * 1.0, (v - cy) * (H / W))) / (rr * 0.4), 0, 1))
    dens = 0.55 + 0.45 * smooth((0.85 - v) / 0.6)
    fond = 0.18 * smooth((0.75 - v) / 0.6) * (0.6 + 0.4 * np.sin(5 * x + 11 * v + seed))
    f = np.clip(np.maximum(f * dens, fond), 0, 1) * smooth((1 - np.abs(x)) / 0.12) * smooth(v / 0.04) * smooth((1 - v) / 0.15)
    rgb = np.zeros(x.shape + (3,), np.float32)
    rgb[:] = (226, 241, 252)
    rgb = rgb * (0.82 + 0.18 * f[..., None])
    al = np.maximum(f * 190, dots * 225 * smooth((1 - np.abs(x)) / 0.12))
    rgb = np.where(dots[..., None] > 0.5, np.array((244, 252, 255), np.float32), rgb)
    return reduire_trans(rgb, al, W, H, seuil=10)


def nappe_tex(W, H, seed):
    x, y = grille(W, H)
    v = (y + 1) / 2
    n = (0.5 + 0.25 * np.sin(7 * x + seed) + 0.15 * np.sin(17 * x + 2 * seed + 9 * v) + 0.10 * np.sin(31 * x - seed + 14 * v))
    haut = 0.5 + 0.35 * n
    f = smooth((haut - v) / 0.35) * smooth((1 - np.abs(x)) / 0.35) * smooth(v / 0.05)
    rgb = np.zeros(x.shape + (3,), np.float32)
    rgb[:] = (214, 236, 250)
    return reduire_trans(rgb, f * 185, W, H, seuil=5)


def anneau_brume_tex(N=128):
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    tour = 0.6 + 0.25 * np.sin(5 * a + 3 * r) + 0.15 * np.sin(11 * a - 7 * r)
    f = smooth((r - 0.55) / 0.2) * smooth((1 - r) / 0.2) * tour
    rgb = np.zeros(x.shape + (3,), np.float32)
    rgb[:] = (210, 234, 248)
    return reduire_trans(rgb, f * 120, N, N, seuil=5)


def onde_f(N):
    """Onde de choc : anneau net + pointes de givre radiales vers l'extérieur."""
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    f = anneau(r, 0.86, 0.035) + 0.5 * np.exp(-((r - 0.80) / 0.06) ** 2)
    for k in range(18):
        ph = k * 2 * math.pi / 18 + 0.1 * math.sin(k * 3.7)
        l = 0.08 + 0.06 * ((k * 7) % 3) / 2
        f = np.maximum(f, segment(x, y, (0.86 * math.cos(ph), 0.86 * math.sin(ph)), ((0.86 + l) * math.cos(ph), (0.86 + l) * math.sin(ph)), 0.016))
    return np.clip(f, 0, 1) * (r < 0.995)


def flash_f(N=64):
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    f = 0.85 * np.exp(-(r / 0.22) ** 2) + 0.35 * np.exp(-(r / 0.5) ** 2)
    ray = np.abs(np.cos(3 * a)) ** 40 * np.clip(1 - r / 0.98, 0, 1) ** 1.2
    ray2 = np.abs(np.cos(3 * a + math.pi / 2)) ** 60 * np.clip(1 - r / 0.55, 0, 1)
    f = np.maximum(f, np.maximum(ray, 0.6 * ray2))
    return np.clip(f, 0, 1) * smooth((1 - r) / 0.05)


def colonne_add_f(W=32, H=128):
    x, y = grille(W, H)
    v = (y + 1) / 2
    f = (0.7 * np.exp(-(x / 0.22) ** 2) + 0.35 * np.exp(-(x / 0.55) ** 2)) * (0.35 + 0.65 * smooth((0.95 - v) / 0.9))
    return f * smooth((1 - np.abs(x)) / 0.1) * smooth((1 - v) / 0.06) * smooth(v / 0.12)   # deux bouts doux (colonne et cœur du cristal)


def colonne_trans(W=32, H=128):
    rng = np.random.default_rng(3)
    x, y = grille(W, H)
    v = (y + 1) / 2
    f = np.zeros_like(x)
    for _ in range(7):
        c, lw = rng.uniform(-0.6, 0.6), rng.uniform(0.04, 0.09)
        v0 = rng.uniform(0, 0.5)
        f = np.maximum(f, rng.uniform(0.5, 1) * np.exp(-((x - c) / lw) ** 2) * smooth((v - v0) / 0.1) * smooth((v0 + 0.55 - v) / 0.2))
    f = f * smooth((1 - np.abs(x)) / 0.2) * smooth((1 - v) / 0.1)
    rgb = np.zeros(x.shape + (3,), np.float32)
    rgb[:] = (230, 244, 253)
    return reduire_trans(rgb, f * 170, W, H, seuil=10)


def flocon_tex(N=16):
    x, y = grille(N, N)
    f = flocon_f(x, y, R=0.95, w=0.13, cotes=((0.55, 0.32),))
    rgb = ramp(0.80 + 0.19 * np.clip(f, 0, 1))
    m = lanczos(f * 255, N, N) > 100
    arr = np.zeros((N, N, 4), np.uint8)
    arr[..., :3] = np.stack([lanczos(rgb[..., k], N, N) for k in range(3)], -1)
    arr[..., 3] = m * 255
    arr[~m, :3] = 0
    return arr


def ame_tex(W=8, H=32):
    v = np.linspace(1, 0, H)[:, None] * np.ones((1, W))
    u = np.linspace(-1, 1, W)[None, :] * np.ones((H, 1))
    val = 0.12 + 0.30 * v + 0.10 * (u < 0) - 0.05 * (u > 0.5)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = ramp(val)
    arr[..., 3] = 255
    return arr



# ------------------------------------------------------------------ peinture (v2)
def facette_tex(W, H, seed):
    """Facette triangulaire de la pointe du cristal géant (base en bas, sommet en haut) : glace trans_, arête centrale,
    liseré givré, fissures."""
    rng = np.random.default_rng(seed)
    x, y = grille(W, H)
    v = (y + 1) / 2
    demi = 0.985 * (1 - v)
    dedans = (np.abs(x) < demi) & (v < 0.985) & (v > 0.0)
    bord = demi - np.abs(x)
    val = 0.40 + 0.20 * v + 0.10 * (x < 0) + 0.18 * np.exp(-(x / 0.05) ** 2)
    fiss = np.zeros_like(x)
    for j in range(2):
        p = (rng.uniform(-0.4, 0.4), rng.uniform(0.05, 0.3))
        pts = [p]
        for _ in range(3):
            p = (np.clip(p[0] + rng.uniform(-0.3, 0.3), -0.7, 0.7), p[1] + rng.uniform(0.08, 0.16))
            pts.append(p)
        for a_, b_ in zip(pts, pts[1:]):
            fiss = np.maximum(fiss, segment(x, v * 2 - 1, (a_[0], a_[1] * 2 - 1), (b_[0], b_[1] * 2 - 1), 0.035))
    lisere = smooth((0.07 - bord) / 0.05)
    val = np.maximum(val, 0.95 * lisere)
    val = np.maximum(val, 0.92 * fiss)
    rgb = ramp(np.clip(val, 0, 0.999))
    al = 118 + 55 * v
    al = np.maximum(al, 222 * lisere)
    al = np.maximum(al, 215 * fiss)
    al = np.where(dedans, np.clip(al, 100, 225), 0)
    out = reduire_trans(rgb, al, W, H, seuil=50)
    m = lanczos(dedans * 255.0, W, H) > 110
    out[~m] = 0
    out[m, 3] = np.clip(out[m, 3], 100, 225)
    return out


def fissure_add(W, H, seed, gain):
    """Fissure lumineuse (add_) qui court du bas au haut d'une paroi : trait anguleux, branches, halo doux."""
    rng = np.random.default_rng(seed)
    x, y = grille(W, H)
    k = H / W
    Y = y * k                                                   # coordonnées isotropes
    f = np.zeros_like(x)
    halo = np.zeros_like(x)
    p = (rng.uniform(-0.3, 0.3), -k)
    pts = [p]
    while p[1] < k:
        p = (float(np.clip(p[0] + rng.uniform(-0.5, 0.5), -0.8, 0.8)), p[1] + rng.uniform(0.35, 0.7))
        pts.append(p)
    for a_, b_ in zip(pts, pts[1:]):
        f = np.maximum(f, segment(x, Y, a_, b_, 0.06))
        halo = np.maximum(halo, segment(x, Y, a_, b_, 0.30))
    for q in pts[1:-1]:
        if rng.uniform() < 0.7:
            ang = math.radians(rng.choice((-1, 1)) * rng.uniform(30, 60) + 90)
            L = rng.uniform(0.3, 0.6)
            r_ = (q[0] + L * math.cos(ang), q[1] + L * math.sin(ang))
            f = np.maximum(f, 0.8 * segment(x, Y, q, r_, 0.04))
            halo = np.maximum(halo, 0.6 * segment(x, Y, q, r_, 0.2))
    f = np.maximum(f, 0.32 * halo) * smooth((1 - np.abs(x)) / 0.08) * (0.25 + 0.75 * smooth((y + 1) / 0.16))   # pied atténué (cercle dessous)
    return reduire_add(f, W, H, gain)


def rune_f(N=32):
    x, y = grille(N, N)
    r = np.hypot(x, y)
    f = 0.70 * np.exp(-(r / 0.34) ** 2) + 0.9 * flocon_f(x, y, R=0.62, w=0.07, cotes=((0.5, 0.3),))
    return np.clip(f, 0, 1) * smooth((1 - r) / 0.12)


def traits_f(N=96, seed=5):
    """Traits de vitesse radiaux (anime) : lignes fines qui partent du centre, plus claires vers l'extérieur."""
    rng = np.random.default_rng(seed)
    x, y = grille(N, N)
    r = np.hypot(x, y)
    f = np.zeros_like(x)
    for _ in range(26):
        ph = rng.uniform(0, 2 * math.pi)
        r0, r1 = rng.uniform(0.32, 0.55), rng.uniform(0.78, 0.97)
        w = rng.uniform(0.016, 0.03)
        seg = segment(x, y, (r0 * math.cos(ph), r0 * math.sin(ph)), (r1 * math.cos(ph), r1 * math.sin(ph)), w)
        f = np.maximum(f, seg * rng.uniform(0.55, 1.0) * smooth((r - r0) / 0.2))
    return f * smooth((1 - r) / 0.04)


def givre_sol_tex(N=112, seed=9):
    """Givre qui court au sol : dendrites qui rayonnent depuis le centre, branches à 60°. trans_."""
    rng = np.random.default_rng(seed)
    x, y = grille(N, N)
    r = np.hypot(x, y)
    f = np.zeros_like(x)
    for k in range(9):
        ang = k * 2 * math.pi / 9 + rng.uniform(-0.15, 0.15)
        p = (0.16 * math.cos(ang), 0.16 * math.sin(ang))
        for j in range(4):
            ang += rng.uniform(-0.25, 0.25)
            L = rng.uniform(0.16, 0.22)
            q = (p[0] + L * math.cos(ang), p[1] + L * math.sin(ang))
            w = 0.022 * (1 - 0.18 * j)
            f = np.maximum(f, segment(x, y, p, q, w))
            for sg in (-1, 1):
                if rng.uniform() < 0.8:
                    b = ang + sg * math.pi / 3
                    lb = rng.uniform(0.06, 0.12) * (1 - 0.15 * j)
                    m = (p[0] + 0.5 * (q[0] - p[0]), p[1] + 0.5 * (q[1] - p[1]))
                    f = np.maximum(f, 0.85 * segment(x, y, m, (m[0] + lb * math.cos(b), m[1] + lb * math.sin(b)), w * 0.7))
            p = q
    f = f * smooth((0.98 - r) / 0.08)
    rgb = ramp(0.70 + 0.29 * np.clip(f, 0, 1))
    al = f * 215
    return reduire_trans(rgb, al, N, N, seuil=24)


def tesson_tex(W, H, seed):
    """Tesson de la paroi du cristal : polygone irrégulier découpé, glace trans_, arêtes givrées, fissure."""
    rng = np.random.default_rng(seed)
    x, y = grille(W, H)
    angs = np.sort(rng.uniform(0, 2 * math.pi, 6))
    rads = rng.uniform(0.72, 0.98, 6)
    P = [(rads[i] * math.cos(angs[i]), rads[i] * math.sin(angs[i])) for i in range(6)]
    d = np.full_like(x, 9.0)
    for i in range(6):
        (ax, ay), (bx, by) = P[i], P[(i + 1) % 6]
        nx, ny = by - ay, -(bx - ax)
        ln = math.hypot(nx, ny)
        d = np.minimum(d, -((x - ax) * nx + (y - ay) * ny) / ln)   # > 0 dedans (sommets tournant dans le sens direct)
    dedans = d > 0
    val = 0.42 + 0.14 * y + 0.12 * (x + y < 0)
    fiss = segment(x, y, (rng.uniform(-0.5, 0.5), -0.8), (rng.uniform(-0.5, 0.5), 0.7), 0.05)
    lisere = smooth((0.12 - d) / 0.08)
    val = np.maximum(np.maximum(val, 0.95 * lisere), 0.9 * fiss)
    rgb = ramp(np.clip(val, 0, 0.999))
    al = np.maximum(np.maximum(150 + 30 * y, 225 * lisere), 220 * fiss)
    al = np.where(dedans, np.clip(al, 140, 228), 0)
    out = reduire_trans(rgb, al, W, H, seuil=60)
    m = lanczos(dedans * 255.0, W, H) > 110
    out[~m] = 0
    out[m, 3] = np.clip(out[m, 3], 140, 228)
    return out


def petite_tex(f, N, clair):
    """Petite particule opaque découpée (alpha 0/255)."""
    rgb = ramp(clair + (0.999 - clair) * np.clip(f, 0, 1))
    m = lanczos(f * 255, N, N) > 100
    arr = np.zeros((N, N, 4), np.uint8)
    arr[..., :3] = np.stack([lanczos(rgb[..., k], N, N) for k in range(3)], -1)
    arr[..., 3] = m * 255
    arr[~m, :3] = 0
    return arr


def eclat_part_tex(N=16):
    x, y = grille(N, N)
    f = np.clip((1 - (np.abs(x) / 0.5 + np.abs(y) / 0.96)) / 0.12, 0, 1)
    f = f * np.where(x < 0, 1.0, 0.72)
    return petite_tex(f, N, 0.55)


def poudre_tex(N=8):
    x, y = grille(N, N)
    r = np.hypot(x, y)
    f = np.maximum(np.exp(-(r / 0.35) ** 2), np.maximum(segment(x, y, (-0.95, 0), (0.95, 0), 0.16), segment(x, y, (0, -0.95), (0, 0.95), 0.16)))
    return petite_tex(f, N, 0.85)


def corps_tex(W, H, seed):
    """Facette du corps d'un cristal (trans_) : arêtes claires de chaque côté (≥ 4 texels), plus dense et plus bleue au pied,
    reflet peint en bande oblique, plans de fracture internes, givre au pied."""
    rng = np.random.default_rng(seed)
    x, y = grille(W, H)
    v = (y + 1) / 2
    arete = smooth((np.abs(x) - 0.80) / 0.08)
    val = 0.34 + 0.16 * v + 0.06 * np.sin(2.3 * x + seed)
    c0 = rng.uniform(-0.4, 0.1)
    refl = np.exp(-((x - c0 - 0.9 * (v - 0.5)) / 0.12) ** 2) * smooth((0.9 - v) / 0.3) * smooth((v - 0.15) / 0.2)
    refl2 = 0.6 * np.exp(-((x - c0 - 0.35 - 0.9 * (v - 0.5)) / 0.05) ** 2) * smooth((0.85 - v) / 0.3) * smooth((v - 0.2) / 0.2)
    val = val + 0.34 * refl + 0.3 * refl2
    fiss = np.zeros_like(x)
    for j in range(3):
        p = (rng.uniform(-0.6, 0.6), rng.uniform(0.1, 0.7))
        q = (p[0] + rng.uniform(-0.5, 0.5), p[1] + rng.uniform(0.08, 0.2))
        fiss = np.maximum(fiss, segment(x, v * 2 - 1, (p[0], p[1] * 2 - 1), (q[0], q[1] * 2 - 1), 0.03))
    givre = smooth((0.10 - v) / 0.08)
    val = np.maximum(val, 0.96 * np.maximum(arete, givre))
    val = np.maximum(val, 0.8 * fiss)
    rgb = ramp(np.clip(val, 0, 0.999))
    al = 196 - 70 * v + 40 * refl
    al = np.maximum(al, 226 * np.maximum(arete, givre))
    al = np.maximum(al, 200 * fiss)
    return reduire_trans(rgb, np.clip(al, 110, 228), W, H, seuil=50)


def rime_tex(W, H, seed=12):
    """Givre qui grimpe sur la paroi intérieure : dentelle blanche dense au pied, fougères qui montent, effilochée en haut."""
    rng = np.random.default_rng(seed)
    x, y = grille(W, H)
    k = H / W
    Y = (y + 1) / 2 * 2 * k - k
    f = np.zeros_like(x)
    for _ in range(7):
        p = (rng.uniform(-0.8, 0.8), -k)
        ang = math.pi / 2 + rng.uniform(-0.3, 0.3)
        for j in range(6):
            L = rng.uniform(0.4, 0.8)
            q = (p[0] + L * math.cos(ang), p[1] + L * math.sin(ang))
            f = np.maximum(f, segment(x, Y, p, q, 0.06 * (1 - 0.1 * j)))
            for sg in (-1, 1):
                b = ang + sg * math.pi / 3
                m_ = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                f = np.maximum(f, 0.85 * segment(x, Y, m_, (m_[0] + 0.25 * math.cos(b), m_[1] + 0.25 * math.sin(b)), 0.04))
            p, ang = q, ang + rng.uniform(-0.3, 0.3)
    v = (y + 1) / 2
    f = np.maximum(f, smooth((0.12 - v) / 0.1)) * smooth((1 - np.abs(x)) / 0.1) * smooth((0.97 - v) / 0.25)
    rgb = ramp(0.80 + 0.19 * np.clip(f, 0, 1))
    return reduire_trans(rgb, f * 210, W, H, seuil=24)



# ------------------------------------------------------------------ atlas (rangement en étagères)
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_A_POSER = []


def a_poser(nom, im):
    _A_POSER.append((nom, im))


def ranger(pas=8):
    """Rangement « première place libre » sur une grille de 8 texels, des plus grandes images aux plus petites."""
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


# gains additifs (cumul mesuré par .build/cumul.py, voir la fiche de style)
G_CERCLE_A, G_CERCLE_B, G_ONDE, G_FLASH, G_COL = 0.36, 0.27, 0.30, 0.50, 0.30
G_FISS, G_RUNE, G_TRAITS = 0.22, 0.26, 0.40
fa, va = cercle_a_f()
a_poser("cercle_a", lignes_trans(fa, 224, voile=va))
a_poser("cercle_a_add", reduire_add(flou(lanczos(fa * 255, 128, 128) / 255, 128), 128, 128, G_CERCLE_A))
fb, vb = cercle_b_f()
a_poser("cercle_b", lignes_trans(fb, 160, voile=vb))
a_poser("cercle_b_add", reduire_add(flou(lanczos(fb * 255, 96, 96) / 255, 96), 96, 96, G_CERCLE_B))
NCR = 6
for k in range(NCR):
    a_poser(f"cristal{k}", cristal_tex(24, 84, 100 + k))
for k in range(2):
    a_poser(f"corps{k}", corps_tex(48, 200, 40 + k))
    a_poser(f"facette{k}", facette_tex(48, 48, 70 + k))
    a_poser(f"fissure{k}", fissure_add(32, 128, 80 + k, G_FISS))
for k in range(3):
    a_poser(f"tesson{k}", tesson_tex(32, 48, 90 + k))
    a_poser(f"ruban{k}", ruban_tex(40, 128, 60 + k))
fo = onde_f(128)
a_poser("onde", lignes_trans(fo, 128, a_max=200))
a_poser("onde_add", reduire_add(flou(lanczos(fo * 255, 64, 64) / 255, 64), 64, 64, G_ONDE))
a_poser("anneau_brume", anneau_brume_tex(96))
a_poser("flash", reduire_add(flash_f(), 64, 64, G_FLASH))
a_poser("traits", reduire_add(traits_f(128), 128, 128, G_TRAITS))
a_poser("rune", reduire_add(rune_f(), 32, 32, G_RUNE))
a_poser("col_add", reduire_add(colonne_add_f(), 32, 128, G_COL))
a_poser("rime", rime_tex(32, 128))
a_poser("nappe0", nappe_tex(64, 32, 1.0))
a_poser("nappe1", nappe_tex(64, 32, 4.0))
a_poser("givre_sol", givre_sol_tex())
a_poser("flocon", flocon_tex())
a_poser("eclat_p", eclat_part_tex())
a_poser("poudre", poudre_tex())
for k in range(2):
    a_poser(f"ame{k}", ame_tex())
ranger()


def sous_uv(nom, v0, v1):
    """Bande horizontale (fractions de hauteur, 0 = haut) d'une région."""
    x0, y0, x1, y1 = UV[nom]
    h = y1 - y0
    return (x0, y0 + round(v0 * h), x1, y0 + round(v1 * h))


for k in range(NCR):
    UV[f"pointe{k}"] = sous_uv(f"cristal{k}", 0, 35 / 84)
    UV[f"cr{k}"] = sous_uv(f"cristal{k}", 35 / 84, 1)

# calque _e : âmes opaques des cristaux (cœur cyan) et dessin trans_ du cercle (lisible de nuit) ; rien sur l'additif
for nom_, f_ in (("cercle_a", fa), ("cercle_b", fb)):
    x0, y0, x1, y1 = UV[nom_]
    g_ = lanczos(np.clip(f_, 0, 1) * 255, x1 - x0, y1 - y0) / 255
    for c_, v_ in enumerate((26, 84, 118)):
        tex_e[y0:y1, x0:x1, c_] = (v_ * g_).astype(np.uint8)
    tex_e[y0:y1, x0:x1, 3] = np.where(tex[y0:y1, x0:x1, 3] > 0, 255, 0)
for k in range(2):
    x0, y0, x1, y1 = UV[f"ame{k}"]
    g = np.linspace(0.5, 1.0, y1 - y0)[:, None]
    tex_e[y0:y1, x0:x1, 0] = (16 * g).astype(np.uint8)
    tex_e[y0:y1, x0:x1, 1] = (52 * g).astype(np.uint8)
    tex_e[y0:y1, x0:x1, 2] = (72 * g).astype(np.uint8)
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
        self.rotation = [round((float(v) + 180) % 360 - 180, 3) for v in rotation] if rotation is not None else None   # dans [-180, 180]
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


def inv(uv):
    return [uv[2], uv[1], uv[0], uv[3]]


def plaque(g, nom, c, w, h, uv, face="south", ep=0.3, rot=None, origine=None):
    c = np.asarray(c, float)
    if face in ("south", "north"):
        a, b = c - (w / 2, h / 2, ep / 2), c + (w / 2, h / 2, ep / 2)
    else:
        a, b = c - (w / 2, ep / 2, h / 2), c + (w / 2, ep / 2, h / 2)
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": r3(a), "to": r3(b), "origin": r3(c if origine is None else origine),
         "box_uv": False, "faces": {face: {"uv": [round(float(v), 2) for v in uv], "texture": 0}}}
    if rot is not None:
        e["rotation"] = r3(rot)
    elements.append(e)
    g.enfants.append(e["uuid"])
    return e


def cube(g, nom, a, b, faces):
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": r3(a), "to": r3(b), "origin": r3((np.asarray(a) + b) / 2),
         "box_uv": False, "faces": faces}
    elements.append(e)
    g.enfants.append(e["uuid"])


def prisme(parent, nom, base, h, w, tilt, yaw, var):
    """Prisme de glace (recette aura_givre) : peau trans_ 4 faces, pointe en deux plaques croisées, âme opaque (_e).
    Renvoie le groupe « pousse » (pivot à la base) à animer en échelle et en bascule."""
    g = G(f"{nom}", base, parent, rotation=(0, yaw, 0))
    p = G(f"pousse_{nom}", base, g, rotation=(tilt, 0, 0))
    tr = G(f"trans_{nom}", base, p)
    bx, by, bz = base
    uvc = UV[f"cr{var % NCR}"]
    y0 = by + 0.05
    hb = h * 49 / 84
    cube(tr, f"peau_{nom}", (bx - w / 2, y0, bz - w / 2), (bx + w / 2, y0 + hb, bz + w / 2),
         {"north": {"uv": list(uvc), "texture": 0}, "south": {"uv": inv(uvc), "texture": 0},
          "east": {"uv": inv(uvc), "texture": 0}, "west": {"uv": list(uvc), "texture": 0}})
    pu = UV[f"pointe{var % NCR}"]
    wd = w * 1.41
    for j, ang in enumerate((45, -45)):
        e = {"name": f"pointe_{nom}_{j + 1}", "type": "cube", "uuid": nuid(),
             "from": r3((bx - wd / 2, y0 + hb, bz - 0.15)), "to": r3((bx + wd / 2, y0 + h, bz + 0.15)),
             "origin": r3((bx, y0 + hb, bz)), "rotation": [0, ang, 0], "box_uv": False,
             "faces": {"north": {"uv": list(pu), "texture": 0}, "south": {"uv": inv(pu), "texture": 0}}}
        elements.append(e)
        tr.enfants.append(e["uuid"])
    aw = w * 0.17
    ua = UV[f"ame{var % 2}"]
    side = {"uv": list(ua), "texture": 0}
    capu = {"uv": [ua[0], ua[1], ua[0] + 4, ua[1] + 4], "texture": 0}
    cube(p, f"ame_{nom}", (bx - aw, y0 + 0.02, bz - aw), (bx + aw, y0 + h * 0.62, bz + aw),
         {"north": side, "south": side, "east": side, "west": side, "up": capu, "down": capu})
    return p


def Ry(deg):
    """Rotation Y de Blockbench (même convention que tools/render_bbmodel.py, rot_matrix)."""
    a = math.radians(deg)
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


O = (0, 0, 0)
EFFET = G("effet", O)                      # racine de tout ce qui se voit (échelle 0 à la fin de depart et arrivee)
JOUEUR = G("joueur", O)                    # groupe vide : position et échelle du joueur (guide 15)
ALPHA = {}

# --- cercle de givre : deux couches (trans_ dessin + add_ lueur), qui tournent en sens contraire ; hauteurs fixes
# (faces texturées « up » à 0,35 / 0,49 / 0,63 / 0,77 / 0,885 (runes) / 1,00 et 1,15 (onde) / 1,30 (brume) / 1,45 (givre))
CERCLE = G("cercle", O, EFFET)
RA, RB = 12.0, 12.0 * 0.775
COUCHES = {}
for nom, R, y_t, y_a in (("a", RA, 0.30, 0.44), ("b", RB, 0.58, 0.72)):
    vite = G(f"vite_{nom}", O, CERCLE)
    tourne = G(f"tourne_{nom}", O, vite)
    tr = G(f"trans_cercle_{nom}", O, tourne)
    ALPHA[f"cercle_{nom}"] = G("ctrl_alpha", O, tr)
    plaque(tr, f"cercle_{nom}", (0, y_t, 0), 2 * R, 2 * R, UV[f"cercle_{nom}"], face="up", ep=0.1)
    ad = G(f"add_cercle_{nom}", O, tourne)
    ALPHA[f"cercle_{nom}_add"] = G("ctrl_alpha", O, ad)
    plaque(ad, f"lueur_cercle_{nom}", (0, y_a, 0), 2 * R * 1.02, 2 * R * 1.02, UV[f"cercle_{nom}_add"], face="up", ep=0.1)
    COUCHES[nom] = (vite, tourne)
# runes : 12 lueurs posées sur un glyphe sur deux de la couche extérieure (elles tournent avec elle), allumées en vague
RUNES = []
for j in range(12):
    ph = math.radians(j * 30)
    g = G(f"add_rune{j + 1}", O, COUCHES["a"][1])
    RUNES.append(G("ctrl_alpha", O, g))
    plaque(g, f"rune{j + 1}", (0.79 * RA * math.cos(ph), 0.835, 0.79 * RA * math.sin(ph)), 3.3, 3.3, UV["rune"], face="up", ep=0.1)
TR_BR = G("trans_brume", O, CERCLE)
ALPHA["brume"] = G("ctrl_alpha", O, TR_BR)
TOURNE_BR = G("tourne_brume", O, TR_BR)
plaque(TOURNE_BR, "anneau_brume", (0, 1.25, 0), 30, 30, UV["anneau_brume"], face="up", ep=0.1)

# --- givre qui court au sol (échelle en x et z seulement)
GIVRE = G("givre_sol", O, EFFET)
TR_GV = G("trans_givre_sol", O, GIVRE)
ALPHA["givre"] = G("ctrl_alpha", O, TR_GV)
plaque(TR_GV, "givre_sol", (0, 1.40, 0), 40, 40, UV["givre_sol"], face="up", ep=0.1)

def Rx(deg):
    a = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def axe(tilt, yaw):
    """Direction de l'axe d'un cristal basculé de tilt (vers l'extérieur local +z) puis tourné de yaw (Rz·Ry·Rx de Blockbench)."""
    return Ry(yaw) @ Rx(tilt) @ np.array([0, 1.0, 0])


CRISTAUX = {}                                        # nom -> (pousse, ctrl_alpha, base, axe, h, ap)


def cristal(parent, nom, base, h, ap, hp, tilt, yaw, corps=0, ame=True, decal=0.0):
    """Cristal de glace hexagonal : 6 facettes de corps trans_ en éventail autour de l'axe (arêtes claires, reflet peint),
    pointe en 6 facettes triangulaires, âme opaque fine (_e). Pivot à la base ; le groupe « pousse » porte la bascule."""
    g = G(nom, base, parent, rotation=(0, yaw, 0))
    al = G(f"alea_{nom}", base, g)                   # inclinaison tirée au hasard à chaque téléportation (animation)
    p = G(f"pousse_{nom}", base, al, rotation=(tilt, 0, 0))
    tr = G(f"trans_{nom}", base, p)
    ca = G("ctrl_alpha", base, tr)
    b = np.asarray(base, float)
    wg = 2 * ap * math.tan(math.radians(30)) + 0.06 + 0.02 * ap
    basc = math.degrees(math.atan2(ap, hp))
    lf = math.hypot(ap, hp) + 0.12
    for k in range(6):
        ang = k * 60 + decal
        P = b + Ry(90 - ang) @ np.array([0, h / 2, -(ap + 0.06)])
        gr = G(f"{nom}_f{k + 1}", P, tr, rotation=(0, 90 - ang, 0))
        uv = UV[f"corps{(corps + k) % 2}"]
        plaque(gr, f"{nom}_f{k + 1}", P, wg, h, uv if k % 2 else inv(uv), face="north", ep=0.12)
        E = b + Ry(90 - ang) @ np.array([0, h, -(ap + 0.06)])
        gp = G(f"{nom}_p{k + 1}", E, tr, rotation=(0, 90 - ang, 0))
        e = {"name": f"{nom}_p{k + 1}", "type": "cube", "uuid": nuid(), "from": r3(E - (wg / 2, 0, 0.06)), "to": r3(E + (wg / 2, lf, 0.06)),
             "origin": r3(E), "rotation": [round(basc, 3), 0, 0], "box_uv": False,
             "faces": {"north": {"uv": list(UV[f"facette{k % 2}"]), "texture": 0}}}
        elements.append(e)
        gp.enfants.append(e["uuid"])
    if ame:
        aw = ap * 0.26
        ua = UV[f"ame{corps % 2}"]
        side = {"uv": list(ua), "texture": 0}
        capu = {"uv": [ua[0], ua[1], ua[0] + 4, ua[1] + 4], "texture": 0}
        cube(p, f"ame_{nom}", (b[0] - aw, b[1] + 0.05, b[2] - aw), (b[0] + aw, b[1] + h * 0.85, b[2] + aw),
             {"north": side, "south": side, "east": side, "west": side, "up": capu, "down": capu})
    CRISTAUX[nom] = (p, ca, b, axe(tilt, yaw), h, ap, al, tr)
    return p


# --- couronne de la charge et du départ : 8 petits cristaux sur le cercle, penchés vers l'extérieur
COURONNE = G("couronne", O, EFFET)
CR = []
for i in range(8):
    th = i * 45 + 22.5 + RNG.uniform(-5, 5)
    c, s_ = math.cos(math.radians(th)), math.sin(math.radians(th))
    rr = 16.2 + RNG.uniform(-0.3, 0.3)              # hors de portée du gros cristal, quelle que soit sa bascule
    h = (6.0 + (2.0 if i % 2 == 0 else 0.0)) * RNG.uniform(0.92, 1.08)
    tilt = RNG.uniform(12, 18)
    CR.append((cristal(COURONNE, f"cr{i + 1}", (rr * c, -0.5, rr * s_), h, 1.0 + 0.08 * h / 6, 2.6, tilt, 90 - th + RNG.uniform(-8, 8), i, decal=15 * i), th, tilt))

# --- tempête : deux cylindres de rubans inclinés (spirale), qui tournent en sens contraire
TEMPETE = G("tempete", O, EFFET)
CYL = {}
for nom, N, R, H, tilt, var0 in (("int", 10, 12.6, 30.0, 26.0, 0), ("ext", 12, 14.6, 34.0, -22.0, 1)):
    spin = G(f"tempete_{nom}", O, TEMPETE)
    tr = G(f"trans_tempete_{nom}", O, spin)
    ALPHA[f"tempete_{nom}"] = G("ctrl_alpha", O, tr)
    w = 2 * R * math.sin(math.pi / N) * 1.35
    for k in range(N):
        yaw = k * 360 / N + (0 if nom == "int" else 15)
        P = Ry(yaw) @ np.array([0, H / 2 + 0.2, -R])          # plaque posée à sa place, tournée autour de son centre
        gr = G(f"ruban_{nom}{k + 1}", P, tr, rotation=(0, yaw, 0))
        uv = UV[f"ruban{(k + var0) % 3}"]
        plaque(gr, f"ruban_{nom}{k + 1}", P, w, H, uv if k % 2 else inv(uv), face="north", ep=0.12, rot=(0, 0, tilt))
    CYL[nom] = spin

# --- cristal du départ : un vrai cristal hexagonal (apothème 8,8, corps 40 px, pointe 16 px), incliné de 12°, dont l'axe passe
# par le torse du joueur (0, 18, 0) ; base enterrée à y = -3. Givre qui monte à l'intérieur, cœur add_, 18 fissures add_.
CRISTAL = G("cristal", O, EFFET)
PIV_G = (0, 16.0, 0)                                # pivot de la bascule au hasard : la tête reste dedans à ±12°
ALEA_G = G("bascule_geant", PIV_G, CRISTAL)
AP, HC, HP = 9.4, 42.0, 16.0
D_G = np.array([0, 1.0, 0])
BASE_G = np.array([0, -4.0, 0])
GEANT = cristal(ALEA_G, "geant", BASE_G, HC, AP, HP, 0.0, 0.0, corps=0, ame=False)
ALPHA["cristal"] = CRISTAUX["geant"][1]
GIVRE_M = G("givre_monte", BASE_G, GEANT)                  # échelle y depuis la base : le givre grimpe
TR_GM = G("trans_givre_monte", BASE_G, GIVRE_M)
ALPHA["givre_monte"] = G("ctrl_alpha", BASE_G, TR_GM)
WGI = 2 * (AP - 0.35) * math.tan(math.radians(30)) + 0.1
for k in range(6):
    ang = k * 60
    P = BASE_G + Ry(90 - ang) @ np.array([0, HC * 0.42, -(AP - 0.35)])
    gr = G(f"givre_m{k + 1}", P, TR_GM, rotation=(0, 90 - ang, 0))
    plaque(gr, f"givre_m{k + 1}", P, WGI, HC * 0.84, UV["rime"] if k % 2 else inv(UV["rime"]), face="north", ep=0.1)
FISS = []                                          # (ctrl_alpha, paroi, tronçon) ; tronçon 0 = pied
for k in range(6):
    ang = k * 60
    for b_ in range(3):
        yb = HC / 6 + b_ * HC / 3
        P = BASE_G + Ry(90 - ang) @ np.array([0, yb, -(AP + 0.4)])
        gr = G(f"add_fissure{k + 1}_{b_ + 1}", P, GEANT, rotation=(0, 90 - ang, 0))
        FISS.append((G("ctrl_alpha", P, gr), k, b_))
        uv = sous_uv(f"fissure{k % 2}", 1 - (b_ + 1) / 3, 1 - b_ / 3)
        plaque(gr, f"fissure{k + 1}_{b_ + 1}", P, (2 * AP * math.tan(math.radians(30))) * 0.85, HC / 3, uv if (k // 2) % 2 else inv(uv), face="north", ep=0.1)
COEUR = G("coeur", BASE_G, GEANT)
PC = BASE_G + np.array([0, 23.0, 0])
CAMY_K = G("camy_coeur", PC, COEUR)
AD_K = G("add_coeur", PC, CAMY_K)
ALPHA["coeur"] = G("ctrl_alpha", PC, AD_K)
plaque(AD_K, "coeur", PC + (0, 0, -1.1), 12, 40, [UV["col_add"][0], UV["col_add"][3], UV["col_add"][2], UV["col_add"][1]], ep=0.1)
SATS = []
for i, (th, h, ap, lean) in enumerate(((135, 15, 2.6, 30), (270, 11, 2.0, 38), (0, 9, 1.7, 44))):
    c, s_ = math.cos(math.radians(th)), math.sin(math.radians(th))
    SATS.append(cristal(ALEA_G, f"sat{i + 1}", (9.6 * c, -1.0, 9.6 * s_), h, ap, ap * 1.8, lean, 90 - th, i + 1, decal=20 * i))


def sur_geant(s, a, r):
    """Point du cristal géant à la fraction s de sa longueur, décalé de r dans la direction horizontale a (rad)."""
    return BASE_G + D_G * (3 + s * (HC + HP - 6)) + r * np.array([math.cos(a), 0, math.sin(a)])


# --- morceaux du cristal : 8 prismes et 8 tessons croisés, posés sur le cristal (cachés jusqu'à l'éclatement)
MORCEAUX = G("morceaux", O, ALEA_G)
INV = []                                             # (contre-bascule, contre-lacet) de chaque morceau
MC = []
for k in range(16):
    a = math.radians(k * 22.5 + 11 + RNG.uniform(-6, 6))
    s_ = ((k * 7) % 16) / 15
    r0 = (AP - 0.8) * (1 if s_ < 0.72 else max(0.3, (1 - s_) / 0.28))
    p0 = sur_geant(s_, a, r0)
    ix = G(f"inv_x{k + 1}", p0, MORCEAUX)
    iy = G(f"inv_y{k + 1}", p0, ix)
    INV.append((ix, iy))
    gm = G(f"morceau{k + 1}", p0, iy)
    if k % 2 == 0:
        h = RNG.uniform(6.5, 9.0)
        prisme(gm, f"mc{k + 1}", p0 - (0, h / 2, 0), h, RNG.uniform(1.9, 2.5), RNG.uniform(-40, 40), RNG.uniform(0, 360), k)
    else:
        tr = G(f"trans_tesson{k + 1}", p0, gm, rotation=(RNG.uniform(-30, 30), 0, RNG.uniform(-30, 30)))
        y1 = 21 + (k * 17) % 18
        uv = UV[f"tesson{k % 3}"]
        for j, yw in enumerate((y1, y1 + 90)):
            plaque(tr, f"tesson{k + 1}_{j + 1}", p0, 4.4 * (1 - 0.15 * j), 6.8 * (1 - 0.15 * j), uv if j else inv(uv), face="north", ep=0.12, rot=(0, yw, 0))
    MC.append((gm, p0, a, k))

# --- formation de l'arrivée : 11 cristaux qui jaillissent du centre, penchés vers l'extérieur, autour du joueur
FORM = G("formation", O, EFFET)
FO = []
for i in range(11):
    grand = i % 2 == 0                               # six grands tout autour (le joueur apparaît derrière eux), cinq petits entre
    th = i * 360 / 11 + RNG.uniform(-9, 9)
    c, s_ = math.cos(math.radians(th)), math.sin(math.radians(th))
    rr = 17.6 + RNG.uniform(0, 1.0)                  # hors de portée du gros cristal basculé au hasard (≤ 14,4 px au sol)
    h = RNG.uniform(14, 20) if grand else RNG.uniform(7, 12)
    ap = RNG.uniform(2.0, 2.6) if grand else RNG.uniform(1.3, 1.9)
    lean = RNG.uniform(18, 30) if grand else RNG.uniform(38, 62)
    p = cristal(FORM, f"fo{i + 1}", (rr * c, -1.0, rr * s_), h, ap, ap * RNG.uniform(1.5, 2.0), lean, 90 - th + RNG.uniform(-10, 10), i, decal=11 * i)
    FO.append((p, f"fo{i + 1}", i))

# --- flash : étoile de givre add_ en cam_, au centre du corps ; traits de vitesse radiaux derrière
FLASH = G("flash", (0, 17, 0), EFFET)
ADD_F = G("add_flash", (0, 17, 0), FLASH)
CAM_F = G("cam_flash", (0, 17, 0), ADD_F)
plaque(CAM_F, "flash", (0, 17, -1.5), 22, 22, UV["flash"], ep=0.1)
TRAITS = G("traits", (0, 17, 0), EFFET)
ADD_T = G("add_traits", (0, 17, 0), TRAITS)
CAM_T = G("cam_traits", (0, 17, 0), ADD_T)
plaque(CAM_T, "traits", (0, 17, -4.0), 30, 30, UV["traits"], ep=0.1)

# --- onde de choc au sol (échelle en x et z seulement)
ONDE = G("onde", O, EFFET)
TR_O = G("trans_onde", O, ONDE)
ALPHA["onde"] = G("ctrl_alpha", O, TR_O)
plaque(TR_O, "onde", (0, 0.95, 0), 20, 20, UV["onde"], face="up", ep=0.1)
AD_O = G("add_onde", O, ONDE)
ALPHA["onde_add"] = G("ctrl_alpha", O, AD_O)
plaque(AD_O, "lueur_onde", (0, 1.10, 0), 21, 21, UV["onde_add"], face="up", ep=0.1)

# --- bouffées de neige (camy_) : deux derrière, deux devant, plus basses
SOUFFLE = G("souffle", O, EFFET)
CAMY_S = G("camy_souffle", O, SOUFFLE)
TR_S = G("trans_souffle", O, CAMY_S)
ALPHA["souffle"] = G("ctrl_alpha", O, TR_S)
for k, (x, zz, w, h) in enumerate(((0.0, -4.2, 26, 7.0), (2.5, -4.7, 20, 5.5), (-3.0, 4.2, 18, 3.6), (3.4, 4.7, 14, 3.0))):
    plaque(TR_S, f"bouffee{k + 1}", (x, h / 2 + 0.1, zz), w, h, UV[f"nappe{k % 2}"])

# --- points de départ des particules (+Y du groupe = direction de départ), chacun avec son ctrl_emit
EMG = G("emetteurs", O, EFFET)
EMC = G("emetteurs_cristal", O, ALEA_G)            # poudre et éclats : suivent le cristal tourné
EMITS, CTRL = [], {}


def emit(nom, pos, sorte, parent=EMG, rot=None):
    ge = G(nom, pos, parent, rotation=rot)
    CTRL.setdefault(sorte, []).append(G("ctrl_emit", pos, ge))
    EMITS.append((ge, sorte))


def dehors(th, a):
    """Rotation qui tourne +Y de a degrés vers l'extérieur, dans la direction th (Rz·Ry·Rx de Blockbench)."""
    return (a, 90 - th, 0)


for k in range(6):
    th = k * 60 + 30
    emit("emit_flocon" + (str(k + 1) if k else ""), (8.6 * math.cos(math.radians(th)), 0.8, 8.6 * math.sin(math.radians(th))), "flocon")
for k in range(6):
    th = k * 60 + 10
    emit("emit_poudre" + (str(k + 1) if k else ""), sur_geant(0.08 + 0.15 * k, math.radians(th), AP + 0.8), "poudre", parent=EMC)
for k in range(6):
    th = k * 60 + 40
    emit("emit_eclat" + (str(k + 1) if k else ""), sur_geant(0.2 + 0.15 * (k % 3), math.radians(th), 4.0), "eclat", parent=EMC, rot=dehors(th, 55))
for y in (1.5, 24.0):
    emit("emit_mc_snowflake", (0, y, 0), "snowflake")
for k in range(4):
    th = k * 90 + 45
    emit("emit_mc_item_snowball", (6.5 * math.cos(math.radians(th)), 0.6, 6.5 * math.sin(math.radians(th))), "snowball", rot=dehors(th, 35))
for y in (6.0, 24.0):
    emit("emit_mc_poof", (0, y, 0), "poof")
for k in range(4):                                   # au bout de 4 cristaux de la formation : poussière du sort qui s'éteint
    p, nom, i = FO[k * 2 + (1 if k else 0)]
    _, _, b, d, h, ap, _, _ = CRISTAUX[nom]
    emit("emit_mc_dust_bfeaff_12", b + np.array([0, h * 0.9, 0]), "dust", parent=p)

# --- particules modélisées (modèles, à la racine, jamais dessinées par le joueur)
PART_F = G("particle_flocon", O)
plaque(PART_F, "flocon", (0, 0.75, 0), 0.8, 0.8, UV["flocon"])
PART_E = G("particle_eclat", (3, 0, 0))
plaque(PART_E, "eclat", (3, 0.7, 0), 0.6, 1.0, UV["eclat_p"])
PART_P = G("particle_poudre", (-3, 0, 0))
plaque(PART_P, "poudre", (-3, 0.6, 0), 0.5, 0.5, UV["poudre"])

outliner = [EFFET.json(), JOUEUR.json(), PART_F.json(), PART_E.json(), PART_P.json()]



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


def net(v, seuil=0.12):
    """Fin nette d'un fondu par l'échelle : sous le seuil, 0 (pas de plaques minuscules qui se confondent)."""
    return v if v >= seuil else 0.0


def ressort(t, t0, amp, f=6.0, k=10.0):
    """Oscillation amortie qui part de t0 (dépassement, rebond)."""
    if t <= t0:
        return 0.0
    u = t - t0
    return amp * math.exp(-k * u) * math.sin(2 * math.pi * f * u)


def saccades(t, marches, dur=0.05, ov=0.35):
    """Paliers atteints par à-coups : [(instant, valeur)], montée en dur s puis dépassement amorti (ov x la marche)."""
    v, prev = 0.0, 0.0
    for ti, vi in marches:
        d = vi - prev
        v += d * sm(t, ti, ti + dur) + ressort(t, ti + dur * 0.5, ov * d, 7.0, 13.0)
        prev = vi
    return v


class Anim:
    def __init__(self, nom, L, loop, fps=12, extra=()):
        self.nom, self.L, self.loop, self.A = nom, L, loop, {}
        ts = set(round(i / fps, 4) for i in range(int(L * fps) + 1)) | {round(L, 4)} | {round(e, 4) for e in extra if 0 <= e <= L}
        self.T = sorted(ts)

    def piste(self, g, ch, fn, T=None):
        """fn(t) -> (x, y, z) échantillonné ; une constante -> une seule clé."""
        if not callable(fn):
            keys = [kf(ch, 0, *fn)]
        else:
            ts = list(T or self.T)
            vals = [fn(t) for t in ts]
            keys = []
            for k_, (t, v) in enumerate(zip(ts, vals)):
                if ch == "scale" and k_ and (not any(vals[k_ - 1])) != (not any(v)):
                    keys.append(kf(ch, t - 0.002, *vals[k_ - 1]))     # apparition / disparition nette : pas d'échelle intermédiaire
                keys.append(kf(ch, t, *v))
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += keys

    def cacher(self, *gs):
        for g in gs:
            self.piste(g, "scale", (0, 0, 0))

    def emettre(self, sorte, fn):
        """Cadence ctrl_emit des points d'une sorte : fn(t, i) -> x (−1 coupé, 0 réglage du staff, +7 au plus)."""
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


def xz(v):
    return (v, 1, v)


def tremble(t, k, amp, f=11.0):
    return amp * math.sin(2 * math.pi * f * t + 1.7 * k)


def vol(t, t0, p0, a, vr, vy, g=110.0, yr=1.4):
    """Morceau projeté à t0 : vol balistique, petit rebond, glissade. Renvoie (décalage, temps depuis l'atterrissage)."""
    u = t - t0
    if u <= 0:
        return (0.0, 0.0, 0.0), -1.0
    ul = (vy + math.sqrt(vy * vy + 2 * g * max(p0[1] - yr, 0.0))) / g
    if u < ul:
        d, y = vr * u, vy * u - 0.5 * g * u * u
        w = -1.0
    else:
        w = u - ul
        vb = 0.22 * abs(vy - g * ul)
        d = vr * ul + 0.35 * vr * 0.15 * (1 - math.exp(-w / 0.15))
        y = yr - p0[1] + max(0.0, vb * w - 0.5 * g * w * w)
    return (d * math.cos(a), y, d * math.sin(a)), w


def atterrissage(t0, p0, vy, g=110.0, yr=1.4):
    return t0 + (vy + math.sqrt(vy * vy + 2 * g * max(p0[1] - yr, 0.0))) / g


def morceaux(an, T0, L):
    """Les 16 morceaux du cristal volent à T0, tournent, retombent, glissent, puis fondent avant L - 0,08."""
    for gm, p0, a, k in MC:
        hauteur = (p0[1] - 5) / 40
        vr = 15 - 6 * hauteur + 2.5 * ((k * 5) % 4) / 3
        vy = 7 + 9 * ((k * 3) % 5) / 4
        yr = 1.4 + 0.3 * (k % 4)                               # hauteurs de repos différentes : deux morceaux posés au même endroit ne se confondent pas
        tl = atterrissage(T0, p0, vy, yr=yr)
        fonte = min(max(tl + 0.12, T0 + 0.75), L - 0.42)
        wx, wy = (520 + 90 * (k % 4)) * (1 if k % 2 else -1), 380 + 60 * (k % 3)

        def pos(t, p0=p0, a=a, vr=vr, vy=vy, fonte=fonte, yr=yr):
            o, _ = vol(t, T0, p0, a, vr, vy, yr=yr)
            return (o[0], o[1] - 0.8 * sm(t, fonte, fonte + 0.3), o[2])

        def rot(t, tl=tl, wx=wx, wy=wy):
            u = max(0.0, t - T0)
            uu = min(u, tl - T0) + 0.12 * (1 - math.exp(-max(0.0, t - tl) / 0.12))
            return (wx * uu, wy * uu, 0)

        def sc(t, fonte=fonte):
            v = step(t, T0) * net(1 - sm(t, fonte, fonte + 0.3), 0.4)
            smear = 1 + 0.45 * (1 - sm(t, T0, T0 + 0.09)) * step(t, T0)
            return (v, v * smear, v)
        an.piste(gm, "position", pos)
        an.piste(gm, "rotation", rot)
        an.piste(gm, "scale", sc)


ORDRE = [3, 0, 4, 1, 5, 2]                                  # ordre dans lequel les parois se fendent


def fissures(an, t0, t_gel, t_fin, pas=(0.07, 0.10)):
    """Les fissures courent du pied au sommet, paroi après paroi, scintillent, puis tiennent pendant le gel."""
    for c, k, b in FISS:
        tk = t0 + pas[0] * ORDRE[k] + pas[1] * b
        an.piste(c, "position", lambda t, tk=tk, k=k: (-1 + sm(t, tk, tk + 0.05) * (1 - 0.35 * (0.5 + 0.5 * math.sin(2 * math.pi * 9 * t + k))
                                                                                    * (1 - step(t, t_gel))) * (1 - step(t, t_fin)), 0, 0))


def frappe(an, T0, centre=True):
    """Image d'impact en deux temps (anime) : grande étoile 0,05 s, puis étoile qui tourne et s'éteint ; traits de vitesse."""
    an.piste(FLASH, "scale", lambda t: u3(step(t, T0) * ((1.7 if t < T0 + 0.05 else 1.0) if centre else 0.6) * net(1 - sm(t, T0 + 0.07, T0 + 0.4))))
    an.piste(CAM_F, "rotation", lambda t: (0, 0, 80 * max(0.0, t - T0)))
    an.piste(TRAITS, "scale", lambda t: u3(step(t, T0) * (0.55 + 1.25 * sm(t, T0, T0 + 0.14)) * net(1 - sm(t, T0 + 0.14, T0 + 0.36))))
    an.piste(CAM_T, "rotation", lambda t: (0, 0, -25 * max(0.0, t - T0)))


def onde(an, T0, gros=1.1):
    an.piste(ONDE, "scale", lambda t: xz(step(t, T0) * (0.35 + gros * sm(t, T0, T0 + 0.5)) * (1 - step(t, T0 + 0.62))))
    an.piste(ALPHA["onde"], "position", lambda t: (-sm(t, T0 + 0.15, T0 + 0.58), 0, 0))
    an.piste(ALPHA["onde_add"], "position", lambda t: (-sm(t, T0 + 0.1, T0 + 0.5), 0, 0))


# ---- tirage au hasard (guide 6.3) : une variable mémorisée par animation, tirée pendant les 0,04 premières secondes
# (math.random change à chaque image), puis gardée ; + q.instance_seed pour un repli propre si le tirage manquait.
# Chaque cristal en dérive ses angles par des sinus de fréquences différentes (une seule variable, aucune limite atteinte).
def hasard(var, k, amp):
    a, b = 7919 * (k + 1) % 9973 + 997, (137 * k) % 360
    return (f"v.{var} = q.anim_time < 0.04 ? math.random(0, 1) : v.{var}; "
            f"return {amp} * math.sin((v.{var} + q.instance_seed) * {a} + {b});")


def neg(e):
    return e.replace("return ", "return -")


def tirer(an, var, petits):
    """Gros cristal : bascule ±12° et lacet libre (contre-rotation des morceaux) ; petits : ±12° en plus de leur évasement,
    et rotation propre autour de leur axe."""
    bx, by = hasard(var, 0, 12), hasard(var, 1, 180)
    an.piste(ALEA_G, "rotation", (bx, by, 0))
    for ix, iy in INV:
        an.piste(ix, "rotation", (neg(bx), 0, 0))
        an.piste(iy, "rotation", (0, neg(by), 0))
    for j, nom in enumerate(petits):
        _, _, _, _, _, _, al, tr = CRISTAUX[nom]
        an.piste(al, "rotation", (hasard(var, 2 + 2 * j, 12), 0, 0))
        an.piste(tr, "rotation", (0, hasard(var, 3 + 2 * j, 180), 0))


# ---- charge (loop 3 s) : le givre se forme au sol, le cercle bat, runes en vague, petits cristaux qui pointent par à-coups
LC = 3.0
W1 = 2 * math.pi / LC
an = Anim("charge", LC, "loop", fps=16)
an.piste(CERCLE, "scale", lambda t: xz(1 + 0.022 * math.sin(W1 * t) + 0.018 * max(0.0, math.sin(2 * W1 * t)) ** 6))
for nom in ("a", "b"):
    an.piste(ALPHA[f"cercle_{nom}_add"], "position", lambda t, nom=nom: (-0.3 + 0.15 * math.sin(W1 * t + (0 if nom == "a" else 2)), 0, 0))
for j, c in enumerate(RUNES):
    an.piste(c, "position", lambda t, j=j: (-0.85 + 0.85 * max(0.0, math.cos(2 * W1 * t - j * math.pi / 6)) ** 4, 0, 0))
for i, (p, th, tilt) in enumerate(CR):
    ph = i * 0.37

    def croit(t, ph=ph):
        u = ((t / LC + ph) % 1.0) * LC                       # secondes dans le cycle de ce cristal
        return 0.5 + saccades(u, [(0.25, 0.1), (0.75, 0.2), (1.25, 0.3)]) - 0.3 * sm(u, 1.9, 2.9)
    an.piste(p, "scale", lambda t, croit=croit: u3(croit(t)))
an.piste(GIVRE, "scale", lambda t: xz(0.6 + 0.06 * math.sin(W1 * t) + 0.04 * math.sin(2 * W1 * t + 1)))
an.piste(ALPHA["givre"], "position", lambda t: (-0.35 + 0.15 * math.sin(W1 * t + 1.5), 0, 0))
rafale = lambda t: 0.5 + 0.5 * math.sin(W1 * t - 1.2)
an.piste(TEMPETE, "scale", lambda t: (1.0, 0.18 + 0.16 * rafale(t), 1.0))
an.piste(CYL["int"], "rotation", lambda t: (0, 720 * t / LC + 60 * math.sin(W1 * t), 0))
an.piste(CYL["ext"], "rotation", lambda t: (0, -360 * t / LC - 45 * math.sin(W1 * t + 1), 0))
for nom in ("int", "ext"):
    an.piste(ALPHA[f"tempete_{nom}"], "position", lambda t: (-0.5 + 0.2 * rafale(t), 0, 0))
an.piste(SOUFFLE, "scale", lambda t: u3(0.4 + 0.08 * math.sin(W1 * t)))
an.piste(ALPHA["souffle"], "position", lambda t: (-0.55 + 0.12 * math.sin(W1 * t + 2), 0, 0))
an.cacher(CRISTAL, MORCEAUX, FLASH, TRAITS, ONDE, FORM)
an.emettre("flocon", lambda t, i: -1 + 4.5 * max(0.0, math.cos(W1 * t - i * math.pi / 3)) ** 3)
an.emettre("snowflake", lambda t, i: 0.5 * math.sin(W1 * t) if i == 0 else -1)
for so in ("poudre", "eclat", "snowball", "poof", "dust"):
    an.emettre(so, -1)
charge = an.json()

# ---- depart (once 3,6 s) : anticipation, tempête, le cristal pousse incliné et gèle le joueur, givre qui monte, fissures,
# gel d'image, éclatement en gros éclats
LD, TG, TB = 3.6, 1.95, 2.1                                   # durée, début du gel d'image, éclatement
EX = [TB - 0.01, TB, TB + 0.01, TB + 0.05, TB + 0.06, TG - 0.01, TG] + [0.5 + 0.25 * i + d for i in range(3) for d in (0, 0.02, 0.05)]
an = Anim("depart", LD, "once", fps=20, extra=EX)
an.piste(CERCLE, "scale", lambda t: xz((1 - 0.14 * sm(t, 0.0, 0.28) + 0.14 * sm(t, 0.28, 0.36) + ressort(t, 0.36, 0.08, 4, 7)
                                     + 0.12 * bump(t, TB, TB + 0.06, TB + 0.12, TB + 0.45)) * (1 - sm(t, 2.6, 3.4))))
for nom in ("a", "b"):
    an.piste(ALPHA[f"cercle_{nom}_add"], "position", lambda t: (-0.3 + 0.25 * sm(t, 0.3, 0.9) - 0.6 * sm(t, TB + 0.3, 3.0), 0, 0))
    an.piste(ALPHA[f"cercle_{nom}"], "position", lambda t: (-0.6 * sm(t, 2.7, 3.4), 0, 0))
an.piste(COUCHES["a"][0], "rotation", lambda t: (0, 30 * t * t, 0))          # le cercle s'emballe
an.piste(COUCHES["b"][0], "rotation", lambda t: (0, -42 * t * t, 0))
for j, c in enumerate(RUNES):
    tj = 0.3 + 0.035 * j
    an.piste(c, "position", lambda t, tj=tj, j=j: (-1 + sm(t, tj, tj + 0.06) * (1 - 0.25 * (0.5 + 0.5 * math.sin(2 * math.pi * 5 * t + j)))
                                                   * (1 - sm(t, 1.15, 1.35)), 0, 0))   # éteintes quand le cristal se fend (cumul additif)
for i, (p, th, tilt) in enumerate(CR):
    d = 0.04 * i
    an.piste(p, "scale", lambda t, d=d: u3((0.5 - 0.12 * bump(t, 0, 0.15, 0.25, 0.33) + saccades(t, [(0.35 + d, 0.2), (0.6 + d, 0.35), (0.85 + d, 0.5)]))
                                           * (1 - step(t, TB))))
    an.piste(p, "rotation", lambda t, i=i, tilt=tilt, d=d: (-(tilt + 4) * sm(t, 0.5 + d, 1.1 + d), 0,
                                                         tremble(t, i, 1.6 * sm(t, 1.3, 1.5) * (1 - step(t, TG)))))
an.piste(TEMPETE, "scale", lambda t: ((1 - 0.1 * bump(t, 0, 0.15, 0.25, 0.35) - 0.15 * sm(t, 0.9, 1.7)) * (1 - step(t, 1.95)),
                                      (0.18 - 0.05 * bump(t, 0, 0.15, 0.25, 0.35) + 0.9 * sm(t, 0.3, 1.0) + ressort(t, 1.0, 0.08, 3, 6)) * (1 - step(t, 1.95)),
                                      (1 - 0.1 * bump(t, 0, 0.15, 0.25, 0.35) - 0.15 * sm(t, 0.9, 1.7)) * (1 - step(t, 1.95))))
an.piste(CYL["int"], "rotation", lambda t: (0, 120 * t + 150 * t * t, 0))
an.piste(CYL["ext"], "rotation", lambda t: (0, -(100 * t + 120 * t * t), 0))
for nom in ("int", "ext"):
    an.piste(ALPHA[f"tempete_{nom}"], "position", lambda t: (-0.45 + 0.3 * sm(t, 0.3, 1.0) - 0.85 * sm(t, 1.2, 1.8), 0, 0))
an.piste(GIVRE, "scale", lambda t: xz(0.6 + saccades(t, [(0.45, 0.2), (0.7, 0.35), (0.95, 0.45)], dur=0.08) + 0.2 * sm(t, TB, TB + 0.3)))
an.piste(ALPHA["givre"], "position", lambda t: (-0.35 * (1 - sm(t, 0.5, 1.2)) - 0.65 * sm(t, 2.8, 3.45), 0, 0))
cy = lambda t: net(saccades(t, [(0.5, 0.36), (0.75, 0.7), (1.0, 1.0)], dur=0.06, ov=0.3), 0.1)
an.piste(CRISTAL, "scale", lambda t: u3(1 - step(t, TB)))
an.piste(GEANT, "scale", lambda t: u3(0) if cy(t) == 0 else (0.82 + 0.18 * sm(t, 0.5, 1.1), cy(t), 0.82 + 0.18 * sm(t, 0.5, 1.1)))
for i, sp in enumerate(SATS):
    an.piste(sp, "scale", lambda t, i=i: u3(net(saccades(t, [(0.62 + 0.12 * i, 0.6), (0.9 + 0.1 * i, 1.0)], dur=0.05, ov=0.35), 0.15)))
an.piste(CRISTAL, "position", lambda t: (0.3 * sm(t, 1.3, 1.9) * math.sin(2 * math.pi * 17 * t) * (1 - step(t, TG)), 0,
                                         0.22 * sm(t, 1.3, 1.9) * math.sin(2 * math.pi * 13 * t + 1) * (1 - step(t, TG))))
an.piste(GIVRE_M, "scale", lambda t: (1, net(sm(t, 0.95, 1.75) + 0.04 * math.sin(2 * math.pi * 3 * t) * bump(t, 1.0, 1.1, 1.6, 1.75), 0.06), 1))
an.piste(ALPHA["coeur"], "position", lambda t: (-1 + 0.9 * sm(t, 0.9, 1.9) - 0.15 * (0.5 + 0.5 * math.sin(2 * math.pi * 7 * t)) * sm(t, 0.9, 1.3) * (1 - step(t, TG))
                                                + 0.1 * step(t, TG), 0, 0))
fissures(an, 1.3, TG, TB)
an.piste(JOUEUR, "scale", lambda t: u3(1 - step(t, TB)))
frappe(an, TB)
morceaux(an, TB, LD)
onde(an, TB)
an.piste(SOUFFLE, "scale", lambda t: u3(step(t, TB) * (0.5 + 0.85 * sm(t, TB, TB + 0.8)) * (1 - step(t, 3.4))))
an.piste(SOUFFLE, "position", lambda t: (0, 2.5 * sm(t, TB, 3.3), 0))
an.piste(ALPHA["souffle"], "position", lambda t: (-0.05 - 0.95 * sm(t, TB + 0.35, 3.35), 0, 0))
an.piste(EFFET, "scale", lambda t: u3(1 - step(t, LD - 0.04)))
an.cacher(FORM)
fin = lambda t: 1 - step(t, 3.2)
an.emettre("flocon", lambda t, i: (-1 + 4 * sm(t, 0.3, 0.6) - 1.5 * sm(t, 1.5, 1.9) + 3 * bump(t, TB, TB + 0.03, TB + 0.3, TB + 0.9)) * fin(t) - (1 - fin(t)))
an.emettre("snowflake", lambda t, i: (0.5 + 2.5 * sm(t, 0.3, 0.8) - 2 * sm(t, 1.5, 1.9) + 4 * bump(t, TB, TB + 0.03, TB + 0.25, TB + 0.8)) * fin(t) - (1 - fin(t)))
an.emettre("poudre", lambda t, i: -1 + 1.5 * bump(t, 1.0 + 0.12 * i, 1.1 + 0.12 * i, TG, TB) + 8 * bump(t, TB, TB + 0.02, TB + 0.25, TB + 0.7))
an.emettre("eclat", lambda t, i: -1 + 8 * bump(t, TB, TB + 0.02, TB + 0.3, TB + 0.6) + 2 * bump(t, TB + 0.5, TB + 0.6, 2.9, 3.1))
an.emettre("poof", lambda t, i: -1 + 7 * bump(t, TB, TB + 0.02, TB + 0.12, TB + 0.2))
an.emettre("snowball", lambda t, i: -1 + 5 * bump(t, TB + 0.35, TB + 0.4, TB + 0.75, TB + 0.95))
an.emettre("dust", -1)
tirer(an, "gd", [f"sat{i + 1}" for i in range(3)])
an.son(0.5, "givre_forme")                      # la glace se forme autour du joueur
an.son(TB - 0.62, "givre_eclate")                  # la glace se fend (son embarqué, validé en jeu)
an.son(TB, "block.glass.break")                    # bris de vitre du jeu à l'éclatement (brisure synthétisée refusée en jeu)
depart = an.json()

# ---- arrivee (once 3,6 s) : le gros cristal incliné jaillit au centre avec une couronne de 11 cristaux ; le joueur apparaît
# dedans, visible à travers la glace ; le gros cristal se fend et éclate pour le libérer pendant que les petits se dissolvent
# en poussière (un sort qui s'éteint)
LA, T0, TGA, TBA = 3.6, 0.06, 1.33, 1.45                   # durée, éclosion, gel d'image, éclatement du gros cristal
ORD = sorted(range(len(FO)), key=lambda i: (FO[i][2] % 2, (FO[i][2] * 5) % 11))   # les grands d'abord, puis les petits
POUSSE = {i: T0 + 0.05 + 0.025 * r for r, i in enumerate(ORD)}
DISS = {i: 1.45 + 0.07 * r for r, i in enumerate(ORD[::-1])}            # les petits se dissolvent les premiers
EX = ([T0 - 0.01, T0, T0 + 0.02, T0 + 0.05, TBA - 0.01, TBA, TBA + 0.01, TBA + 0.05, TBA + 0.06, TGA - 0.01, TGA]
      + [v + d for v in POUSSE.values() for d in (-0.01, 0, 0.03, 0.06)])
an = Anim("arrivee", LA, "once", fps=20, extra=EX)
an.piste(CERCLE, "scale", lambda t: xz(net(sm(t, 0.0, 0.12) + ressort(t, 0.1, 0.12, 4, 7) + 0.1 * bump(t, TBA, TBA + 0.06, TBA + 0.12, TBA + 0.45), 0.1)
                                      * (1 - sm(t, 2.8, 3.45))))
for nom in ("a", "b"):
    an.piste(ALPHA[f"cercle_{nom}_add"], "position", lambda t: (-0.2 + 0.2 * bump(t, T0, T0 + 0.05, T0 + 0.15, T0 + 0.6) - 0.7 * sm(t, 2.6, 3.4), 0, 0))
    an.piste(ALPHA[f"cercle_{nom}"], "position", lambda t: (-0.6 * sm(t, 2.9, 3.45), 0, 0))
an.piste(COUCHES["a"][0], "rotation", lambda t: (0, -90 * (1 - math.exp(-4 * t)) - 30 * sm(t, 1.5, 2.6), 0))
an.piste(COUCHES["b"][0], "rotation", lambda t: (0, 120 * (1 - math.exp(-4 * t)) + 40 * sm(t, 1.5, 2.6), 0))
for j, c in enumerate(RUNES):                        # vague à l'éclosion, éteintes pendant les fissures (cumul additif)
    an.piste(c, "position", lambda t, j=j: (-1 + sm(t, 0.2 + 0.03 * j, 0.25 + 0.03 * j) * (1 - sm(t, 0.7, 0.85)), 0, 0))
# gros cristal : pousse d'un coup (0,1 s, dépassement), givre qui prend, cœur allumé, fissures courtes, gel, éclatement
cya = lambda t: net(step(t, T0) * (sm(t, T0, T0 + 0.1) + ressort(t, T0 + 0.08, 0.16, 5, 9)), 0.1)
an.piste(CRISTAL, "scale", lambda t: u3(1 - step(t, TBA)))
an.piste(GEANT, "scale", lambda t: u3(0) if cya(t) == 0 else (0.85 + 0.15 * sm(t, T0, T0 + 0.25), cya(t), 0.85 + 0.15 * sm(t, T0, T0 + 0.25)))
for i, sp in enumerate(SATS):
    an.piste(sp, "scale", lambda t, i=i: u3(net(sm(t, T0 + 0.06 + 0.03 * i, T0 + 0.13 + 0.03 * i) + ressort(t, T0 + 0.1 + 0.03 * i, 0.25, 6, 10), 0.15)))
an.piste(CRISTAL, "position", lambda t: (0.3 * sm(t, 0.95, 1.3) * math.sin(2 * math.pi * 17 * t) * (1 - step(t, TGA)), 0,
                                         0.22 * sm(t, 0.95, 1.3) * math.sin(2 * math.pi * 13 * t + 1) * (1 - step(t, TGA))))
an.piste(GIVRE_M, "scale", lambda t: (1, net(sm(t, T0 + 0.1, 0.7), 0.06), 1))
an.piste(ALPHA["coeur"], "position", lambda t: (-1 + 0.5 * sm(t, T0, T0 + 0.15) + 0.4 * sm(t, 0.85, TGA) + 0.1 * step(t, TGA), 0, 0))
fissures(an, 0.85, TGA, TBA, pas=(0.035, 0.05))
for p, nom, i in FO:
    d0, ds = POUSSE[i], DISS[i]

    def sc(t, d0=d0, ds=ds):
        y = net(sm(t, d0, d0 + 0.07) + ressort(t, d0 + 0.05, 0.3, 5, 8), 0.2)
        x = net(sm(t, d0, d0 + 0.05), 0.2)
        m = net(1 - 0.75 * sm(t, ds + 0.15, ds + 0.95), 0.4)
        if y * m == 0 or x == 0:
            return (0, 0, 0)
        return (x * (0.6 + 0.4 * m), y * m, x * (0.6 + 0.4 * m))
    an.piste(p, "scale", sc)
    an.piste(p, "rotation", lambda t, i=i, d0=d0, ds=ds: (tremble(t, i, 2.0 * bump(t, d0 + 0.08, d0 + 0.1, d0 + 0.25, d0 + 0.45)), 0,
                                                       tremble(t, i + 3, 1.2 * bump(t, ds - 0.1, ds, ds + 0.3, ds + 0.6), 9)))
    an.piste(p, "position", lambda t, ds=ds: (0, 1.6 * sm(t, ds + 0.1, ds + 1.0), 0))
    an.piste(CRISTAUX[nom][1], "position", lambda t, ds=ds: (-0.15 * (0.5 + 0.5 * math.sin(2 * math.pi * 2.3 * t)) * sm(t, 0.4, 0.6) - 0.85 * sm(t, ds, ds + 0.7), 0, 0))
an.piste(JOUEUR, "scale", lambda t: u3(step(t, T0 + 0.07)))           # il apparaît dans le gros cristal, déjà poussé à mi-hauteur
# flash au sol à l'éclosion, puis image d'impact au centre à l'éclatement
an.piste(FLASH, "position", lambda t: (0, -11.5 if t < TBA - 0.1 else 0, 0))
an.piste(FLASH, "scale", lambda t: u3(step(t, T0) * 0.9 * net(1 - sm(t, T0 + 0.07, T0 + 0.3))
                                      + step(t, TBA) * (1.7 if t < TBA + 0.05 else 1.0) * net(1 - sm(t, TBA + 0.07, TBA + 0.4))))
an.piste(CAM_F, "rotation", lambda t: (0, 0, 80 * max(0.0, t - T0)))
an.piste(TRAITS, "scale", lambda t: u3(step(t, TBA) * (0.55 + 1.25 * sm(t, TBA, TBA + 0.14)) * net(1 - sm(t, TBA + 0.14, TBA + 0.36))))
an.piste(CAM_T, "rotation", lambda t: (0, 0, -25 * max(0.0, t - TBA)))
morceaux(an, TBA, LA)
an.piste(ONDE, "scale", lambda t: xz(step(t, T0) * (0.35 + 1.3 * sm(t, T0, T0 + 0.5)) * (1 - step(t, T0 + 0.62))
                                     + step(t, TBA) * (0.35 + 1.1 * sm(t, TBA, TBA + 0.5)) * (1 - step(t, TBA + 0.62))))
an.piste(ALPHA["onde"], "position", lambda t: (-sm(t, T0 + 0.15, T0 + 0.58) * (1 - step(t, TBA)) - sm(t, TBA + 0.15, TBA + 0.58), 0, 0))
an.piste(ALPHA["onde_add"], "position", lambda t: (-sm(t, T0 + 0.1, T0 + 0.5) * (1 - step(t, TBA)) - sm(t, TBA + 0.1, TBA + 0.5), 0, 0))
an.piste(GIVRE, "scale", lambda t: xz(saccades(t, [(T0, 0.6), (T0 + 0.12, 1.0), (T0 + 0.3, 1.1)], dur=0.06) + 0.1 * sm(t, TBA, TBA + 0.3)))
an.piste(ALPHA["givre"], "position", lambda t: (-sm(t, 2.4, 3.3), 0, 0))
an.piste(SOUFFLE, "scale", lambda t: u3(step(t, T0) * (0.5 + 0.8 * sm(t, T0, T0 + 0.7) + 0.3 * sm(t, TBA, TBA + 0.6)) * (1 - step(t, 3.4))))
an.piste(SOUFFLE, "position", lambda t: (0, 3.0 * sm(t, T0, 3.3), 0))
an.piste(ALPHA["souffle"], "position", lambda t: (-0.3 - 0.35 * sm(t, 0.4, 1.3) + 0.25 * sm(t, TBA, TBA + 0.2) - 0.6 * sm(t, 1.9, 3.35), 0, 0))
an.piste(EFFET, "scale", lambda t: u3(1 - step(t, LA - 0.04)))
an.cacher(COURONNE, TEMPETE)
fin = lambda t: 1 - step(t, 3.2)
an.emettre("flocon", lambda t, i: (-1 + 4 * bump(t, T0, T0 + 0.03, T0 + 0.3, T0 + 0.8) + 4 * bump(t, TBA, TBA + 0.03, 2.4, 2.9)) * fin(t) - (1 - fin(t)))
an.emettre("snowflake", lambda t, i: (-1 + 5 * bump(t, T0, T0 + 0.03, T0 + 0.3, T0 + 0.7) + 4 * bump(t, TBA, TBA + 0.03, 2.4, 2.9)) * fin(t) - (1 - fin(t)))
an.emettre("snowball", lambda t, i: -1 + 6 * bump(t, T0, T0 + 0.02, T0 + 0.25, T0 + 0.45) + 5 * bump(t, TBA + 0.35, TBA + 0.4, TBA + 0.75, TBA + 0.95))
an.emettre("poudre", lambda t, i: -1 + 4 * bump(t, T0 + 0.05, T0 + 0.08, T0 + 0.3, T0 + 0.6) + 1.5 * bump(t, 0.85 + 0.05 * i, 0.9 + 0.05 * i, TGA, TBA)
           + 8 * bump(t, TBA, TBA + 0.02, TBA + 0.25, TBA + 0.6) + 5 * bump(t, 1.9, 2.0, 2.5, 2.9))
an.emettre("dust", lambda t, i: -1 + 7 * bump(t, DISS[2 * i + (1 if i else 0)], DISS[2 * i + (1 if i else 0)] + 0.1, DISS[2 * i + (1 if i else 0)] + 0.7, DISS[2 * i + (1 if i else 0)] + 0.95))
an.emettre("eclat", lambda t, i: -1 + 8 * bump(t, TBA, TBA + 0.02, TBA + 0.3, TBA + 0.6) + 2 * bump(t, TBA + 0.5, TBA + 0.6, 2.4, 2.6))
an.emettre("poof", lambda t, i: -1 + 6 * bump(t, T0, T0 + 0.02, T0 + 0.12, T0 + 0.2) + 7 * bump(t, TBA, TBA + 0.02, TBA + 0.12, TBA + 0.2))
tirer(an, "ga", [f"sat{i + 1}" for i in range(3)] + [nom for _, nom, _ in FO])
an.son(T0, "givre_forme")                       # la glace se forme (jaillissement)
an.son(TBA, "block.glass.break")                    # bris de vitre du jeu au moment exact de l'éclatement
arrivee = an.json()

# ---- overlay_givre (24 s) : rotation lente des couches du cercle et de l'anneau de brume (ne saute pas entre animations)
LO = 24.0
A = {}
for g, e in ((COUCHES["a"][1], f"q.anim_time*{s(360 / LO)}"), (COUCHES["b"][1], f"q.anim_time*{s(-720 / LO)}"),
             (TOURNE_BR, f"q.anim_time*{s(-360 / LO)}")):
    A[g.uuid] = {"name": g.nom, "type": "bone", "keyframes": [kf("rotation", 0, 0, e, 0)]}
overlay = {"uuid": nuid(), "name": "overlay_givre", "loop": "loop", "override": False, "length": LO, "snapping": 24,
           "selected": False, "animators": A}


# ---- animations des particules (guide 5 ter §3) : rotation fermée sur la boucle, scintillement
def anim_particule(nom, L, g, rot=None, pulse=None):
    a_ = Anim(nom, L, "loop", fps=16)
    if rot:
        a_.piste(g, "rotation", lambda t: tuple(r * 360 * t / L for r in rot))
    if pulse:
        a_.piste(g, "scale", lambda t: u3(1 + pulse * max(0.0, math.sin(2 * math.pi * t / L)) ** 3))
    return a_.json()


p_flocon = anim_particule("particle_flocon_fall", 2.0, PART_F, rot=(0, 0, 1))
p_eclat = anim_particule("particle_eclat_fall", 0.8, PART_E, rot=(1, 2, 0))
p_poudre = anim_particule("particle_poudre_fall", 0.5, PART_P, rot=(0, 0, 1), pulse=0.7)

ANIMS = [charge, depart, arrivee, overlay, p_flocon, p_eclat, p_poudre]
assert len(EMITS) <= 32, len(EMITS)
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures,
         "animations": ANIMS}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
embarquer_sons(model, {"givre_forme": "sons/givre_forme.ogg", "givre_eclate": "sons/givre_eclate.ogg"})   # sons originaux (tools/synthe.py)
limiter_sons(model, max_effet=3)                          # effet : fissure ou jaillissement + bris de vitre (demande de l'utilisateur)
for a_ in ANIMS:
    eff = a_["animators"].get("effects")
    assert not eff or len(eff["keyframes"]) <= 3, a_["name"]

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
