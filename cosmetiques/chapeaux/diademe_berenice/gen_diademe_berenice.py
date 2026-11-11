"""Diadème de Bérénice : fin bandeau d'or doux, pierre ivoire au front sur un soleil de rayons fins (« cheveux d'or »),
petites étoiles à quatre branches en vrai volume, ailettes de plumes ivoire en éventail aux tempes. Design original,
ensemble Bérénice (.claude/styles/berenice.md), assorti à ailes_berenice et aura_berenice.
Écrit diademe_berenice.png, diademe_berenice_e.png et .build/diademe_berenice_brut.bbmodel à côté de ce script.

Tout est dans le groupe de premier niveau head. Placement : la seconde couche du skin est à 4,5 px du centre ; le bandeau
a sa face intérieure à 4,65 px (face, tempes, nuque), ses coins sont laissés en biseau (aucun cube ne coupe le coin de la tête).
Les ailettes partent au-dessus des tempes (z de -1,9 à +0,1, y ≥ 31,2) et montent vers l'arrière : rien en porte-à-faux devant
le visage, hormis le bandeau, le soleil et la pierre (1 px devant le bandeau). Texture HD : 36 texels/px environ.

Volumes : bandeau en vrai volume (0,35 px), filet en relief sur les tempes et la nuque, biseaux et perlé peints ;
pierre, rosace et étoiles en peau + âme (plaque ronde découpée par alpha autour d'un noyau plein, invisible de face) ;
plumes en peau + âme (recette validée d'ailes_berenice). Faces parallèles qui se chevauchent : toutes à 0,1 px au moins
(mesuré par .build/mesure_faces.py).

Fonctions avancées (guide 4 bis, 5 ter, 6.4, 6.5) :
- calque _e : cœur de la pierre et des étoiles (150 à 225 sur de petites surfaces), fils des rayons, pointes des plumes ;
- ctrl_lumiere (groupe joyaux) : la pierre « s'allume » à l'équipement, pulsation lente en overlay (non simulé, à juger en jeu) ;
- overlay_scintille : les étoiles battent doucement (échelle), une boucle de 4 s jouée par-dessus tous les états ;
- event_equip (1,6 s) : les ailettes s'ouvrent, les étoiles apparaissent, la pierre s'allume, son embarqué carillon_celeste (sons/carillon_celeste.py) ;
- aucune particule : les points emit_mc_end_rod ont été retirés après le retour en jeu du 2026-11-04 (capture 21.49.32 :
  grosses étoiles blanches de taille fixe qui dérivent à 2 ou 3 blocs, boules lumineuses avec shader).
Sons : un seul, à l'équipement (tools/sons.py). Pas de reflets _r (REFLETS = False, tools/ambiance.py).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons

NOM = "diademe_berenice"
AVEC_E = True       # True : embarque le calque _e en seconde texture. Réactivé le 2026-11-03 (correctif du mod annoncé, à vérifier en jeu).
TEX = 512
SS = 4
TAU = 2 * math.pi
D = 36              # texels par px du modèle


# ------------------------------------------------------------------ peinture
def lerp(a, b, k):
    return a + (b - a) * k


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def C3(*c):
    return np.array(c, np.float32)


GOLD_D, GOLD_M, GOLD_L = C3(176, 138, 78), C3(232, 198, 122), C3(252, 232, 176)
GOLD_W = C3(255, 246, 216)          # éclat de l'or poli
IVORY_L, IVORY, IVORY_D = C3(255, 254, 250), C3(244, 238, 224), C3(150, 138, 116)
AUBE = C3(210, 228, 255)
PAL = {
    # racine, milieu, bout, liseré, ombre, couleur de pointe : mêmes valeurs qu'ailes_berenice
    "p": ((222, 216, 202), (252, 250, 243), (254, 251, 240), (176, 150, 104), (150, 138, 116), (238, 200, 116)),
    "l": ((240, 212, 148), (250, 232, 180), (254, 242, 204), (186, 148, 84), (176, 146, 96), (255, 244, 208)),
}
SHAPE = {
    # demi-largeur intérieure, extérieure, début de l'arrondi, courbure, début de pointe colorée, longueur d'ombre
    "p": (0.42, 0.34, 0.62, 0.10, 0.74, 0.24),
    "l": (0.46, 0.42, 0.44, 0.03, 0.86, 0.16),
}


def grid(W, H):
    """Coordonnées sur-échantillonnées 0..1 (u vers la droite, v vers le bas)."""
    w, h = W * SS, H * SS
    return np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)


def down(col, W, H, alpha=None):
    """Réduit la peinture sur-échantillonnée : alpha 0/255, couleur moyenne hors silhouette (ni frange, ni PNG lourd)."""
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = rgb
    if alpha is None:
        arr[..., 3] = 255
        return arr
    solid = np.array(Image.fromarray((alpha * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    if solid.any():
        arr[~solid, :3] = rgb[solid].mean(axis=0).astype(np.uint8)
    arr[..., 3] = solid * 255
    return arr


def down_e(ec, ref):
    """Calque _e réduit, même découpe que la texture."""
    H, W = ref.shape[:2]
    eo = np.array(Image.fromarray(np.clip(ec, 0, 225).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    return np.dstack([eo, ref[..., 3]]).astype(np.uint8)


def brush(n, seed, amp=0.035):
    """Brossé léger de l'or, le long de u (±3,5 % : métal propre, retours-en-jeu) : une valeur par ligne sur-échantillonnée."""
    rng = np.random.default_rng(seed)
    rows = np.convolve(rng.normal(0, 1, n), np.ones(9) / 3, mode="same")
    return (1 + amp * np.clip(rows, -1.5, 1.5))[:, None, None]


def paint(W, H, kind, seed):
    """Plume : base en haut, pointe en bas, côté extérieur à droite. Renvoie la texture et le calque lumineux."""
    rng = np.random.default_rng(seed)
    root, mid, tip, rim, shadow, gold = (C3(*c) for c in PAL[kind])
    hi, ho, te, curve, g0, shl = SHAPE[kind]
    te += rng.uniform(-0.03, 0.03)
    jitter = rng.uniform(0.97, 1.02)
    x, y = grid(W, H)
    t = y
    cx = 0.5 + curve * (t * t - 0.3)
    env = (0.28 + 0.72 * smooth(t / 0.20)) * np.where(t > te, np.sqrt(np.clip(1 - ((t - te) / (1 - te)) ** 2, 0, 1)), 1.0)
    d = x - cx
    lim = np.where(d >= 0, ho * env, hi * env)
    r = np.abs(d) / np.maximum(lim, 1e-4)
    alpha = r < 1
    col = lerp(lerp(root, mid, smooth(t / 0.5)[..., None]), tip, smooth((t - 0.5) / 0.5)[..., None]) * jitter
    col = col * (1.04 - 0.17 * (r ** 2))[..., None]
    col = col * (1 + 0.035 * np.sin((t * H - np.abs(d) * W * 1.4) * TAU / 7.0) * (r > 0.1))[..., None]
    gk = smooth((t - g0) / max(1e-3, 1 - g0))[..., None]
    col = lerp(col, gold, gk * 0.85)
    col = lerp(col, shadow, (np.clip(1 - t / shl, 0, 1) ** 1.25)[..., None] * 0.72)
    col = col * (1 - 0.20 * (np.clip((r - 0.45) / 0.55, 0, 1) * (d < 0))[..., None])
    dist = (1 - r) * lim * W
    col = lerp(col, rim, (np.clip(1 - dist / 4.0, 0, 1) * (t > 0.12))[..., None] * 0.72)
    ec = np.zeros(col.shape, np.float32)
    ec[...] = (14, 12, 8)
    ec = lerp(ec, C3(120, 96, 50), gk)                    # pointe dorée : lueur douce
    if kind == "p":
        ra = np.clip(1 - np.abs(d) * W / 1.8, 0, 1)[..., None] * (t < 0.93)[..., None]
        col = lerp(col, C3(255, 248, 226), ra * 0.75)      # rachis clair
        ec = lerp(ec, C3(70, 64, 48), ra)
    out = down(col, W, H, alpha)
    return out, down_e(ec, out)


def edge_strip(kind, W=8, H=48):
    """Bande opaque de l'âme d'une plume : suit le dégradé de la plume, assombrie pour dessiner le bord."""
    root, mid, tip, rim, shadow, gold = (C3(*c) for c in PAL[kind])
    g0 = SHAPE[kind][4]
    a = np.zeros((H, W, 4), np.float32)
    for yy in range(H):
        t = (yy + 0.5) / H
        c = lerp(root, mid, min(1, t * 2)) if t < 0.5 else lerp(mid, tip, (t - 0.5) * 2)
        c = lerp(c, gold, float(smooth((t - g0) / max(1e-3, 1 - g0))) * 0.85)
        a[yy, :, :3] = lerp(c, rim, 0.38)
    a[..., 3] = 255
    return a.astype(np.uint8)


def band_face(W, H, seed, perle=False):
    """Face visible du bandeau : or bombé, biseau clair en haut, ombre en bas, liserés sombres ; perlé en option."""
    u, v = grid(W, H)
    col = lerp(GOLD_L, GOLD_M, smooth((v - 0.18) / 0.5)[..., None])
    col = lerp(col, GOLD_D, smooth((v - 0.62) / 0.38)[..., None] * 0.85)
    col = lerp(col, GOLD_W, np.clip(1 - np.abs(v - 0.13) / 0.08, 0, 1)[..., None] * 0.8)       # arête du biseau haut
    col = lerp(col, C3(140, 104, 56), (np.minimum(v, 1 - v) < 0.05)[..., None] * 0.7)           # liserés
    col = col * brush(H * SS, seed)
    ec = np.zeros(col.shape, np.float32)
    ec[...] = (10, 8, 4)
    if perle:
        pas = 0.42 * D / W                  # une perle tous les 0,42 px
        k = (u / pas) % 1 - 0.5
        dx, dy = k * pas * W, (v - 0.48) * H
        rr = np.hypot(dx, dy) / (0.15 * D)
        ins = rr < 1
        pc = lerp(GOLD_M, GOLD_D, smooth(rr)[..., None])
        pc = lerp(pc, GOLD_W, np.clip(1 - np.hypot(dx + 1.2, dy + 1.2) / 2.2, 0, 1)[..., None])
        col = np.where(ins[..., None], pc, lerp(col, GOLD_D, (np.clip(1.25 - rr, 0, 0.25) * 2.4)[..., None] * (rr >= 1)[..., None]))
        ec = np.where(ins[..., None], lerp(ec, C3(40, 32, 16), (1 - rr)[..., None]), ec)
    out = down(col, W, H)
    return out, down_e(ec, out)


def band_top(W, H):
    """Dessus et dessous du bandeau : arrondi, clair au milieu, plus sombre aux deux arêtes."""
    u, v = grid(W, H)
    q = np.abs(v - 0.5) * 2
    col = lerp(GOLD_W, GOLD_M, smooth(q / 0.8)[..., None])
    col = lerp(col, GOLD_D, smooth((q - 0.7) / 0.3)[..., None] * 0.7)
    out = down(col, W, H)
    e = np.zeros_like(out)
    e[..., 3] = 255
    return out, e


def filet_face(W, H):
    """Filet en relief : or poli, jonc clair au centre."""
    u, v = grid(W, H)
    q = np.abs(v - 0.45) * 2
    col = lerp(GOLD_W, GOLD_L, smooth(q / 0.6)[..., None])
    col = lerp(col, GOLD_D, smooth((q - 0.6) / 0.4)[..., None] * 0.8)
    ec = np.zeros(col.shape, np.float32)
    ec[...] = lerp(C3(10, 8, 4), C3(70, 58, 30), np.clip(1 - q / 0.35, 0, 1)[..., None])
    out = down(col, W, H)
    return out, down_e(ec, out)


def flat(W, H, top, bot, e=(0, 0, 0)):
    """Petite tuile en dégradé (noyaux, bouts)."""
    a = np.zeros((H, W, 4), np.float32)
    for yy in range(H):
        a[yy, :, :3] = lerp(C3(*top), C3(*bot), (yy + 0.5) / H)
    a[..., 3] = 255
    em = np.zeros((H, W, 4), np.uint8)
    em[..., :3] = e
    em[..., 3] = 255
    return a.astype(np.uint8), em


# Bandeau, en px du modèle
BAND_Y, DIP = 30.6, 0.6          # hauteur du bandeau aux tempes ; descente au centre, vers la pierre
GEM_Y = BAND_Y - DIP
SUN_X, SUN_Y0, SUN_Y1 = 3.05, GEM_Y - 1.15, 32.75   # plaque du soleil : x = ±SUN_X, y de SUN_Y0 à SUN_Y1
ROS_R = 1.08                     # rayon de la rosace (sertissure)
NR = 13                          # rayons du soleil


def sun_plate():
    """Soleil : rosace à lobes biseautée (sertissure de la pierre) et rayons fins effilés, « cheveux d'or », vers le haut seulement."""
    W, H = int(round(2 * SUN_X * D)), int(round((SUN_Y1 - SUN_Y0) * D))
    u, v = grid(W, H)
    gx, gy = (u - 0.5) * 2 * SUN_X, SUN_Y1 - v * (SUN_Y1 - SUN_Y0) - GEM_Y       # px, centre de la pierre à l'origine
    r, th = np.hypot(gx, gy), np.arctan2(gx, gy)                               # th = 0 vers le haut
    col = np.zeros(gx.shape + (3,), np.float32)
    ec = np.zeros(gx.shape + (3,), np.float32)
    alpha = np.zeros(gx.shape, bool)
    # rayons
    for k in range(NR):
        a = math.radians(-60 + 120 * k / (NR - 1))
        longue = k % 2 == 0
        dx, dy = math.sin(a), math.cos(a)
        lmax = min((SUN_Y1 - 0.12 - GEM_Y) / max(dy, 1e-3), (SUN_X - 0.12) / max(abs(dx), 1e-3))
        L1 = lmax * (1.0 if longue else 0.72) - (0.0 if longue else 0.1)
        r0 = ROS_R - 0.1
        s = gx * dx + gy * dy                          # le long du rayon
        n = -gx * dy + gy * dx                         # en travers
        kk = np.clip((s - r0) / (L1 - r0), 0, 1)
        half = (0.085 if longue else 0.07) * (1 - kk) ** 0.8 + 0.035
        tipd = np.hypot(np.maximum(s - L1, 0), n)
        ins = ((s >= r0) & (s <= L1) & (np.abs(n) < half)) | ((s > L1) & (tipd < 0.035))     # bout arrondi, rien vers le centre
        q = np.clip(np.abs(n) / half, 0, 1)
        rc = lerp(GOLD_W, GOLD_M, smooth(q)[..., None])
        rc = lerp(rc, GOLD_D, smooth((q - 0.65) / 0.35)[..., None] * 0.8)
        rc = lerp(rc, GOLD_L, kk[..., None] * 0.4)
        col = np.where(ins[..., None], rc, col)
        ec = np.where(ins[..., None], np.maximum(ec, (C3(70, 58, 30) * (1 - q)[..., None]) * (1 - 0.5 * kk)[..., None]), ec)
        alpha |= ins
        if longue:
            # étincelle à quatre branches au bout du rayon
            px_, py_ = gx - dx * L1, gy - dy * L1
            sr = 0.2
            st = (np.abs(px_ / sr) ** 0.6 + np.abs(py_ / sr) ** 0.6) < 1
            col = np.where(st[..., None], lerp(GOLD_W, IVORY_L, np.clip(1 - np.hypot(px_, py_) / 0.1, 0, 1)[..., None]), col)
            ec = np.where(st[..., None], np.maximum(ec, C3(150, 136, 96) * np.clip(1 - np.hypot(px_, py_) / 0.16, 0, 1)[..., None]), ec)
            alpha |= st
    # rosace à lobes, biseautée : arête claire, gorge sombre où se pose la pierre
    rim = ROS_R * (0.94 + 0.06 * np.cos(th * 12))
    q = r / rim
    ros = q < 1
    rc = lerp(GOLD_M, GOLD_D, smooth((q - 0.80) / 0.20)[..., None])
    rc = lerp(rc, GOLD_W, np.clip(1 - np.abs(q - 0.88) / 0.07, 0, 1)[..., None] * 0.9 * (0.6 + 0.4 * np.cos(th + 0.8))[..., None])
    rc = lerp(rc, C3(150, 112, 60), np.clip(1 - np.abs(q - 0.74) / 0.05, 0, 1)[..., None])
    lobe = np.cos(th * 12) > 0.6
    rc = lerp(rc, GOLD_L, (lobe & (q > 0.8) & (q < 0.95))[..., None] * 0.35)
    col = np.where(ros[..., None], rc, col)
    ec = np.where(ros[..., None], C3(12, 10, 5), ec)
    alpha |= ros
    out = down(col, W, H, alpha)
    return out, down_e(ec, out)


def stone_disc(W=58):
    """Cabochon ivoire en dôme : nacre claire au centre, reflet haut à gauche, touche bleu d'aube, lèvre d'or fine."""
    u, v = grid(W, W)
    gx, gy = u * 2 - 1, v * 2 - 1
    r = np.hypot(gx, gy)
    col = lerp(IVORY_L, C3(226, 206, 160), smooth((r - 0.35) / 0.6)[..., None])
    col = lerp(col, AUBE, (np.clip(1 - np.hypot(gx - 0.35, gy - 0.42) / 0.45, 0, 1) * 0.35)[..., None])
    col = lerp(col, C3(255, 255, 255), np.clip(1 - np.hypot(gx + 0.32, gy + 0.36) / 0.22, 0, 1)[..., None])
    col = lerp(col, GOLD_D, smooth((r - 0.86) / 0.1)[..., None])
    ec = lerp(np.zeros(col.shape, np.float32) + C3(40, 34, 20), C3(225, 216, 180), np.clip(1 - r / 0.78, 0, 1)[..., None] ** 0.9)
    ec = np.where((r > 0.86)[..., None], C3(10, 8, 4), ec)
    out = down(col, W, W, r < 0.98)
    return out, down_e(ec, out)


def star(W=64):
    """Étoile à quatre branches taillée : chaque branche a une facette claire (haut, gauche) et une sombre ; cœur ivoire lumineux."""
    u, v = grid(W, W)
    gx, gy = u * 2 - 1, 1 - v * 2                      # gy vers le haut
    sh = np.abs(gx) ** 0.62 + np.abs(gy) ** 0.62
    ins = sh < 1
    r = np.hypot(gx, gy)
    vert = np.abs(gy) >= np.abs(gx)
    # facette éclairée : lumière venue d'en haut à gauche
    lit = np.where(vert, gx < 0, gy > 0)
    col = np.where(lit[..., None], lerp(GOLD_W, GOLD_L, smooth(r)[..., None]), lerp(GOLD_M, GOLD_D, smooth(r)[..., None] * 0.8))
    ridge = np.where(vert, np.abs(gx), np.abs(gy)) < 0.035
    col = np.where(ridge[..., None], lerp(GOLD_W, GOLD_M, smooth(r)[..., None] * 0.5), col)
    col = lerp(col, C3(140, 104, 56), smooth((sh - 0.86) / 0.14)[..., None] * 0.8)
    core = np.clip(1 - r / 0.2, 0, 1)[..., None]
    col = lerp(col, C3(255, 252, 238), core)
    ec = np.zeros(col.shape, np.float32)
    ec = np.maximum(ec, C3(225, 212, 168) * np.clip(1 - r / 0.3, 0, 1)[..., None] ** 1.3)
    ec = np.maximum(ec, C3(60, 50, 26) * ridge[..., None] * (1 - r)[..., None])
    out = down(col, W, W, ins)
    return out, down_e(ec, out)


# ------------------------------------------------------------------ atlas
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_cur = [0, 0, 0]


def place(name, im, em=None):
    h, w = im.shape[:2]
    if _cur[0] + w > TEX:
        _cur[:] = [0, _cur[1] + _cur[2] + 2, 0]
    x, y = _cur[0], _cur[1]
    assert y + h <= TEX - 6, "atlas plein"
    tex[y:y + h, x:x + w] = im
    if em is not None:
        tex_e[y:y + h, x:x + w] = em
    UV[name] = (x, y, x + w, y + h)
    _cur[0] += w + 2
    _cur[2] = max(_cur[2], h)


BL = 9.9                     # plus longue face du bandeau (tempe), en px
BH, BT = 0.8, 0.35           # hauteur, épaisseur du bandeau
FH, FT = 0.3, 0.31           # filet : hauteur, épaisseur (relief de 0,11 px devant le bandeau)
seed = 11
for i in range(4):
    place(f"p{i}", *paint(68, 216, "p", seed))
    seed += 1
place("sun", *sun_plate())
for i in range(3):
    place(f"l{i}", *paint(58, 94, "l", seed))
    seed += 1
place("star", *star())
place("disc", *stone_disc())
for kind in PAL:
    e = edge_strip(kind)
    em = np.zeros(e.shape, np.uint8)
    em[...] = (12, 11, 8, 255)
    place(f"edge_{kind}", e, em)
place("or_c", *flat(24, 24, (250, 226, 168), (190, 150, 86)))
place("ivoire_c", *flat(24, 24, (250, 244, 228), (214, 196, 156), (40, 34, 20)))
place("band_end", *flat(14, 28, (240, 212, 150), (180, 140, 80)))
place("band_p", *band_face(int(BL * D), int(BH * D), 3, perle=True))
place("band", *band_face(int(BL * D), int(BH * D), 4))
place("band_top", *band_top(int(BL * D), int(BT * D)))
place("filet", *filet_face(int(BL * D), int(FH * D) + 1))
place("filet_top", *band_top(int(BL * D), int(FT * D)))

CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC
assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
assert tex_e[..., :3].max() <= 225, "calque trop vif"
_b64 = []
for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(fn, optimize=True)
    _buf = io.BytesIO()
    im_.save(_buf, "PNG", optimize=True)
    _b64.append("data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode())
tex_b64, tex_e_b64 = _b64

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx, ordre du mod et du renderer."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    """Renvoie la clé du groupe ; emit_mc_ et ctrl_ peuvent porter le même nom (guide 5 ter, 4 bis), la clé reste unique."""
    key = name
    if name.startswith(("emit_mc_", "ctrl_")):
        key = f"{name}#{len(groups)}"
    assert key not in groups
    groups[key] = {"name": name, "origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "rotation": [round(float(v), 2) for v in rotation]}
    return key


def cube(g, name, c, size, X, Y, faces):
    """Cube centré en c, axes X, Y (orthonormés), Z = X × Y."""
    c, size = np.asarray(c, float), np.asarray(size, float)
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    rot = euler(R_)
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in c - size / 2], "to": [round(float(v), 3) for v in c + size / 2],
         "origin": [round(float(v), 3) for v in c], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def all_faces(tile):
    return {f: list(UV[tile]) for f in ("north", "south", "east", "west", "up", "down")}


def sub(tile, L, flip=False, v=None):
    """Portion de tuile pour une face de longueur L px (densité constante), retournée si flip."""
    u0, v0, u1, v1 = UV[tile]
    w = min(u1 - u0, L * D)
    a, b = u0 + (u1 - u0 - w) / 2, u0 + (u1 - u0 + w) / 2
    return [b, v0, a, v1] if flip else [a, v0, b, v1]


def only(face, uv, back=None):
    """Plaque fine : une face texturée (et son dos), tranches transparentes."""
    f = {k: CLEAR for k in ("north", "south", "east", "west", "up", "down")}
    f[face] = uv
    if back:
        f[back[0]] = back[1]
    return f


SKIN = 0.3       # épaisseur d'une peau de plume
EMBED = 0.12     # l'âme entre d'autant dans la peau : ni vide, ni face coplanaire


def feather(g, name, p, d, vane, L, w, tile, t0=0.62, t1=0.52, ncore=1, bow=0.2, skins=(1, -1)):
    """Plume peau + âme partant de p vers d ; vane = côté droit de l'image, Z = X × Y. t0, t1 : épaisseur totale à la base, à la pointe.
    Épaisseur presque constante (l’âme de 0,3 px reste à 0,1 px au moins des faces des peaux) ; bow : la pointe s'écarte du plan vers -Z. skins : peaux à poser, +1 côté +Z, -1 côté -Z."""
    p, d = np.asarray(p, float), unit(np.asarray(d, float))
    X0 = unit(vane - (vane @ d) * d)
    Y0 = -d
    Z0 = np.cross(X0, Y0)
    u0, v0, u1, v1 = UV[tile]
    tip = p + d * L
    for sg in skins:
        a = p + Z0 * (sg * (t0 / 2 - SKIN / 2))
        b = tip + Z0 * (-bow + sg * (t1 / 2 - SKIN / 2))
        ax = unit(b - a)
        X = unit(X0 - (X0 @ ax) * ax)
        faces = {"south": [u0, v0, u1, v1] if sg > 0 else CLEAR, "north": [u1, v0, u0, v1] if sg < 0 else CLEAR,
                 "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
        cube(g, f"{name}.{'d' if sg > 0 else 'v'}", (a + b) / 2, (w, float(np.linalg.norm(b - a)), SKIN), X, -ax, faces)
    kind = tile[0]
    e0, e1, e2, e3 = UV[f"edge_{kind}"]
    t_a, t_b = 0.16, 0.92
    for j in range(ncore):
        f0, f1 = lerp(t_a, t_b, j / ncore), lerp(t_a, t_b, (j + 1) / ncore)
        c0, c1 = p + d * (f0 * L) + Z0 * (-bow * f0), p + d * (f1 * L) + Z0 * (-bow * f1)
        ax = unit(c1 - c0)
        X = unit(X0 - (X0 @ ax) * ax)
        th = max(0.3, lerp(t0, t1, f1) - 2 * SKIN + 2 * EMBED)
        wc = w * 0.36 * (1 - 0.45 * (j + 0.5) / ncore)
        ov = 0.12 if j else 0.0
        ea, eb = lerp(e1, e3, f0), lerp(e1, e3, f1)
        fc = [e0, ea, e2, eb]
        cube(g, f"{name}.c{j}", (c0 + c1) / 2 - ax * ov / 2, (wc, float(np.linalg.norm(c1 - c0)) + ov, th), X, -ax,
             {"south": fc, "north": fc, "east": fc, "west": fc, "up": [e0, ea, e2, min(e3, ea + 1)], "down": [e0, max(e1, eb - 1), e2, eb]})
    return tip


# Profondeurs (valeur absolue de la coordonnée hors de la tête) : faces parallèles toujours à 0,1 px au moins.
BI, BO = 4.65, 5.00              # bandeau : face intérieure, extérieure
FB, FF = 4.80, 5.11              # filet en relief
PB, PF = 5.22, 5.56              # plaques des étoiles et du soleil
CB, CF = 4.82, 5.33              # noyaux sous les plaques (dos dans le bandeau, devant dans la plaque)
GB, GF = 5.45, 5.90              # noyau de la pierre
SB, SF = 5.68, 6.02              # dôme de la pierre
COIN = 4.88                      # bout des segments : le coin extérieur reste ouvert (biseau de 0,12 px)
FEND = 4.50                      # le filet s'arrête avant les coins

ROOT = group("diademe", [0, BAND_Y, 0])
BAND = group("bandeau", [0, BAND_Y, 0], parent=ROOT)
X1, Y1, Z1 = V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)
bt = list(UV["band_top"])
be = list(UV["band_end"])


def band_seg(name, c, L, X, Y, front_tile, outer, H=BH):
    """Segment de bandeau de longueur L le long de X ; outer = face qui regarde hors de la tête."""
    faces = {k: be for k in ("north", "south", "east", "west")}
    faces["up"] = sub("band_top", L)
    faces["down"] = sub("band_top", L)
    faces[outer] = sub(front_tile, L)
    faces[{"north": "south", "south": "north"}[outer]] = CLEAR       # face contre la tête : jamais vue
    cube(BAND, name, c, (L, H, BT), X, Y, faces)


def filet_seg(name, c, L, X, Y, outer):
    faces = {k: CLEAR for k in ("north", "south", "east", "west")}
    faces["up"] = sub("filet_top", L)
    faces["down"] = sub("filet_top", L)
    faces[outer] = sub("filet", L)
    cube(BAND, name, c, (L, FH, FT), X, Y, faces)


MID, MIDF = (BI + BO) / 2, (FB + FF) / 2
# face : deux segments qui descendent vers la pierre ; ils s'arrêtent à |x| = 0,5 sous la rosace (pas de chevauchement au centre)
for s, tag in ((-1, "l"), (1, "r")):
    A, B = V(s * COIN, BAND_Y, -MID), V(s * 0.5, GEM_Y + 0.5 * DIP / COIN, -MID)
    X_ = unit((A - B) * s)               # vers +x, le long de la pente
    band_seg(f"face_{tag}", (A + B) / 2, float(np.linalg.norm(A - B)), X_, V(-X_[1], X_[0], 0), "band_p", "north")
# tempes : le long de z ; X = -s·z pour que la face south regarde vers l'extérieur
for s, tag in ((-1, "l"), (1, "r")):
    Xs = V(0, 0, -s)
    band_seg(f"tempe_{tag}", V(s * MID, BAND_Y, 0), 2 * COIN, Xs, Y1, "band", "south")
    # filet en deux morceaux, coupé sous l'agrafe étoilée de la tempe
    for z0, z1, k in ((-FEND, -1.62, "av"), (-0.38, FEND, "ar")):
        filet_seg(f"filet_{tag}_{k}", V(s * MIDF, BAND_Y, (z0 + z1) / 2), z1 - z0, Xs, Y1, "south")
# nuque : 0,15 px plus bas que les tempes (dessus et dessous jamais coplanaires dans les coins)
NY = BAND_Y - 0.15
band_seg("nuque", V(0, NY, MID), 2 * COIN, X1, Y1, "band", "south")
for x0, x1, k in ((-FEND, -0.62, "l"), (0.62, FEND, "r")):
    filet_seg(f"filet_nuque_{k}", V((x0 + x1) / 2, NY, MIDF), x1 - x0, X1, Y1, "south")

# joyaux : pierre, soleil, étoiles ; ctrl_lumiere (calque _e) piloté par l'équipement et l'overlay
JOY = group("joyaux", [0, GEM_Y, -BO], parent=ROOT)
CTRL = group("ctrl_lumiere", [0, GEM_Y, -BO], parent=JOY)
SUN = group("soleil", [0, GEM_Y, -BO], parent=JOY)
su = UV["sun"]
cy_sun = (SUN_Y0 + SUN_Y1) / 2
cube(SUN, "soleil", V(0, cy_sun, -(PB + PF) / 2), (2 * SUN_X, SUN_Y1 - SUN_Y0, PF - PB), X1, Y1,
     only("north", [su[0], su[1], su[2], su[3]], ("south", [su[2], su[1], su[0], su[3]])))
R45 = (unit(V(1, 1, 0)), unit(V(-1, 1, 0)))
cube(SUN, "serti", V(0, GEM_Y, -(CB + CF) / 2), (1.30, 1.30, CF - CB), *R45, all_faces("or_c"))
STONE = group("pierre", [0, GEM_Y, -SF], parent=JOY)
cube(STONE, "pierre_noyau", V(0, GEM_Y, -(GB + GF) / 2), (0.86, 0.86, GF - GB), *R45, all_faces("ivoire_c"))
du = UV["disc"]
SR = 0.80
cube(STONE, "pierre", V(0, GEM_Y, -(SB + SF) / 2), (2 * SR, 2 * SR, SF - SB), X1, Y1, only("north", [du[0], du[1], du[2], du[3]]))
EMITS = []      # aucune particule : end_rod retiré après le retour en jeu du 2026-11-04 (grosses étoiles blanches qui dérivent)

STARS = []
stu = UV["star"]


def star_at(name, c, n, R):
    """Étoile peau + âme : plaque découpée face à n, noyau en losange (invisible de face) qui donne l'épaisseur de profil."""
    n = unit(n)
    g = group(name, c - n * (PF - PB), parent=JOY)      # pivot au dos de la plaque : l'échelle ne la rapproche pas du bandeau
    STARS.append(g)
    X_ = unit(np.cross(Y1, n))           # Z = X × Y = n
    k = float(np.abs(c @ n))
    base = c - n * k                     # point de la tête sous l'étoile
    cube(g, f"{name}.peau", base + n * (PB + PF) / 2, (2 * R, 2 * R, PF - PB), X_, Y1, only("south", [stu[0], stu[1], stu[2], stu[3]]))
    a = 0.30 * R * math.sqrt(2)
    cube(g, f"{name}.noyau", base + n * (CB + CF) / 2, (a, a, CF - CB), unit(X_ + Y1), unit(Y1 - X_), all_faces("or_c"))


SY = (GEM_Y + BAND_Y) / 2
for s, tag in ((-1, "l"), (1, "r")):
    # petite étoile sur le front, de part et d'autre du soleil
    xs = s * 3.72
    ys = BAND_Y - DIP * (COIN - abs(xs)) / COIN + 0.0
    star_at(f"etoile_{tag}", V(xs, ys, -PF), V(0, 0, -1), 0.5)
    # agrafe de la tempe : l'éventail part de là
    star_at(f"agrafe_{tag}", V(s * PF, BAND_Y, -1.0), V(s, 0, 0), 0.86)
star_at("etoile_nuque", V(0, NY, PF), V(0, 0, 1), 0.6)

# Ailettes : éventail qui part au-dessus de la tempe, de la verticale vers l'arrière ; écartement vers l'extérieur et roulis.
NF = 5
FAN_A = [2, 18, 34, 50, 66]                  # 0° = vertical, 90° = vers l'arrière
FAN_L = [4.5, 5.4, 5.8, 5.5, 4.7]
FAN_W = [1.72, 1.86, 1.92, 1.86, 1.72]
SPLAY = 0.36                                 # tangente de l'écartement vers l'extérieur
ROLL = [0.62, 0.52, 0.42, 0.32, 0.22]        # le bord avant passe à l'extérieur ; roulis varié : jamais toutes par la tranche
ANCH_Y, ANCH_Z = BAND_Y + 0.6, -0.9
FANS = []


def build(s):
    tag = "l" if s < 0 else "r"
    fan = group(f"fan_{tag}", [s * BO, ANCH_Y, ANCH_Z], parent=ROOT)
    FANS.append(fan)
    for i in range(NF):
        a = math.radians(FAN_A[i])
        d = unit(V(s * SPLAY, math.cos(a), math.sin(a)))
        back = V(0, -math.sin(a), math.cos(a))
        vane = back - V(s * ROLL[i], 0, 0)
        p = V(s * (5.12 + 0.03 * i), ANCH_Y + 0.05 - 0.06 * i, ANCH_Z - 0.95 + 0.42 * i)
        g = group(f"d{i}_{tag}", p, parent=fan)
        tip = feather(g, f"d{i}{tag}", p, d, vane, FAN_L[i], FAN_W[i], f"p{(i + (0 if s < 0 else 2)) % 4}", ncore=1, bow=0.22 * (i + 1) / NF)
    # couvertures d'or : petites plumes qui couvrent la naissance de l'éventail, derrière l'agrafe
    for i, (ang, L_, w_, dz) in enumerate(((14, 2.4, 1.45, -0.7), (40, 2.6, 1.55, 0.05), (64, 2.3, 1.4, 0.75))):
        a = math.radians(ang)
        d = unit(V(s * (SPLAY + 0.2), math.cos(a), math.sin(a)))
        back = V(0, -math.sin(a), math.cos(a))
        p = V(s * (5.3 + 0.03 * i), ANCH_Y - 0.1, ANCH_Z + dz)
        feather(fan, f"cv{i}{tag}", p, d, back - V(s * 0.25, 0, 0), L_, w_, f"l{i}", t0=0.6, t1=0.52, ncore=1, bow=0.05)


build(-1)
build(1)


def bone(name):
    g = groups[name]
    return {"name": g["name"], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "head", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone(ROOT)]}]


# ------------------------------------------------------------------ animations
# Repères du guide, section 3 : +X = le haut part vers l'arrière ; +Z = le côté droit (+X) monte, donc une plume dressée part vers la gauche.
# Pour une ailette de côté s (-1 gauche, +1 droite) : « s'ouvrir vers l'extérieur » = Z de signe -s.
def kf(t, x, y, z, ch="rotation"):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 3)), "y": str(round(y + 0.0, 3)), "z": str(round(z + 0.0, 3))}],
            "time": round(t, 3), "interpolation": "linear"}


def S(T, amp, ph=0.0, off=0.0):
    return lambda t: off + amp * math.sin(TAU * t / T + math.radians(ph))


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


WEIGHT = [(i / (NF - 1) - 0.35) for i in range(NF)]     # poids d'écartement : l'avant reste presque fixe, l'arrière s'ouvre


def fan_tracks(length, back, open_, spread, times, per, lag):
    A = {}
    for s, tag in ((-1, "l"), (1, "r")):
        A[groups[f"fan_{tag}"]["uuid"]] = {"name": f"fan_{tag}", "type": "bone", "keyframes": [kf(t, back(t), 0, -s * open_(t)) for t in times]}
        for i in range(NF):
            dl = lag * length * i / (NF - 1)
            g = f"d{i}_{tag}"
            A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(t, WEIGHT[i] * spread(per(t - dl)), 0, 0) for t in times]}
    return A


def anim(name, length, back, open_, spread, n_kf=None, loop="loop", lag=0.05):
    """back : l'éventail bascule vers l'arrière ; open_ : s'ouvre vers l'extérieur ; spread : éventail, > 0 ouvert. Léger retard en cascade."""
    n = n_kf or max(8, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]
    per = (lambda t: t % length) if loop == "loop" else (lambda t: max(0.0, t))
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle",
            "animators": fan_tracks(length, back, open_, spread, times, per, lag)}


# idle 8 s : respiration (4 s) et étirement ample de 4,6 à 7,2 s
st = lambda t: bump(t, 4.6, 5.4, 6.0, 7.2)
idle = anim("idle", 8.0, S(4, 0.8, 0, 0.8), lambda t: S(4, 0.8)(t) + 3 * st(t), lambda t: S(4, 1.2)(t) + 7 * st(t), n_kf=48)
# walk 1,6 s : légèrement ramené en arrière, balancement au pas
walk = anim("walk", 1.6, S(1.6, 1.4, 0, 4), S(1.6, 1.0), S(1.6, 1.6, 40, -1))
# run 1,0 s : couché en arrière, serré
run = anim("run", 1.0, S(1.0, 1.6, 0, 16), S(1.0, 0.8, 0, -1), S(1.0, 1.6, 40, -6))
# sneak 3 s : un peu refermé vers l'arrière, sans se rabattre sur la tête (elle penche déjà en avant)
sneak = anim("sneak", 3.0, S(3, 0.6, 0, 6), S(3, 0.5, 0, 0.5), S(3, 0.8, 40, -6))
# fly 2,4 s : éventail grand ouvert, battement lent
fly = anim("fly", 2.4, S(2.4, 2.0, 0, 10), S(2.4, 4.0, 0, 4), S(2.4, 3.0, -40, 7), n_kf=24)
# glide 3,6 s : traîne vers l'arrière, ondulation douce
glide = anim("glide", 3.6, S(3.6, 1.6, 0, 22), S(3.6, 2.0, 0, 2), S(3.6, 2.4, -40, -3), n_kf=24)
# attack et hurt : une fois, dernière image à zéro
atk = lambda t: bump(t, 0.0, 0.12, 0.28, 0.72)
attack = anim("attack", 0.8, lambda t: -2 * atk(t), lambda t: 7 * atk(t), lambda t: 12 * atk(t), n_kf=16, loop="once", lag=0.02)
hu = lambda t: bump(t, 0.0, 0.07, 0.2, 0.72)
tr = lambda t: 3.0 * math.sin(TAU * t * 5 / 0.8) * (1 - sm(t, 0.2, 0.7))
hurt = anim("hurt", 0.8, lambda t: 8 * hu(t) + tr(t) * 0.5, lambda t: tr(t), lambda t: -5 * hu(t), n_kf=16, loop="once", lag=0.02)

# overlay_scintille (4 s, par-dessus tous les états) : les étoiles battent doucement, la lumière de la pierre respire
OV = 4.0
ov_t = [i * OV / 16 for i in range(17)]
ov_a = {}
for k, g in enumerate(STARS):
    ph = 360 * k / len(STARS) * 1.7
    ov_a[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(t, *(1 + 0.07 * math.sin(TAU * t / OV + math.radians(ph)),) * 3, ch="scale") for t in ov_t]}
ov_a[groups[CTRL]["uuid"]] = {"name": "ctrl_lumiere", "type": "bone", "keyframes": [kf(t, 0.2 * math.sin(TAU * t / OV), 0, 0, ch="position") for t in ov_t]}
overlay = {"uuid": nuid(), "name": "overlay_scintille", "loop": "loop", "override": False, "length": OV, "snapping": 24, "selected": False, "animators": ov_a}

# event_equip (1,6 s) : les ailettes s'ouvrent depuis un repli, les étoiles apparaissent l'une après l'autre, la pierre s'allume
EQ = 1.6
eq_t = [i * EQ / 32 for i in range(33)]
ouvre = lambda t: 1 - sm(t, 0.15, 1.05)
rebond = lambda t: bump(t, 0.75, 0.95, 1.05, 1.45)
eq_a = fan_tracks(EQ, lambda t: 14 * ouvre(t), lambda t: -3 * ouvre(t) + 1.5 * rebond(t), lambda t: -12 * ouvre(t) + 3 * rebond(t), eq_t, lambda t: max(0.0, t), 0.04)
for k, g in enumerate(STARS):
    t0 = 0.45 + 0.12 * k
    sc = lambda t, t0=t0: sm(t, t0, t0 + 0.3) * (1 + 0.18 * bump(t, t0 + 0.2, t0 + 0.3, t0 + 0.35, t0 + 0.55))
    eq_a[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(t, *(sc(t),) * 3, ch="scale") for t in eq_t]}
pz = lambda t: lerp(0.4, 1.0, sm(t, 0.55, 0.95)) + 0.1 * bump(t, 0.85, 0.95, 1.0, 1.3)
eq_a[groups[STONE]["uuid"]] = {"name": STONE, "type": "bone", "keyframes": [kf(t, *(pz(t),) * 3, ch="scale") for t in eq_t]}
lum = lambda t: -1 + sm(t, 0.6, 0.95) * 1.6 - 0.6 * sm(t, 1.05, 1.6)
eq_a[groups[CTRL]["uuid"]] = {"name": "ctrl_lumiere", "type": "bone", "keyframes": [kf(t, lum(t), 0, 0, ch="position") for t in eq_t]}
eq_a["effects"] = {"name": "Effects", "type": "effect", "keyframes": [{"channel": "sound", "data_points": [{"effect": "carillon_celeste", "file": ""}], "time": 0.9}]}
equip = {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": EQ, "snapping": 24, "selected": False, "animators": eq_a}

ANIMS = [idle, walk, run, sneak, fly, glide, attack, hurt, overlay, equip]
assert len(EMITS) == 0 and 60 <= len(elements) <= 150, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
embarquer_sons(model, {"carillon_celeste": "sons/carillon_celeste.ogg"})   # son original synthétisé (tools/synthe.py)
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;", len(EMITS), "emit_")
