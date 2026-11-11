"""Couronne de givre : un cercle fin d'argent froid posé sur le haut de la tête, d'où montent des prismes de glace hexagonaux
pointus, taillés, le plus haut au milieu du front, qui décroissent vers les tempes et la nuque en s'inclinant vers l'extérieur.
Dentelle de givre blanc peinte sur le cercle, cœur cyan lumineux dans chaque prisme, flocon à six branches au front.
Design original, ensemble Givre (.claude/styles/givre.md), assorti à ailes_givre.
Écrit couronne_givre.png, couronne_givre_e.png et .build/couronne_givre_brut.bbmodel à côté de ce script.

Tout est dans le groupe de premier niveau head. Placement : la seconde couche du skin est à 4,5 px du centre (dessus à y = 32,5) ;
le cercle a sa face intérieure à 4,65 px (face, tempes, nuque), des chatons en biseau ferment les coins à 4,63 px au plus près.
Les prismes reposent sur des socles d'argent posés sur le haut du cercle (y ≥ 32,68) : leur moitié intérieure passe au-dessus de
la tête, jamais dedans. Rien devant le visage hormis le cercle et le flocon (0,4 px devant le cercle, au haut du front).
Texture HD : 36 texels/px.

Volumes : cristal = peau + âme. La peau : six plaques de 0,3 px, une par facette, et six plaques triangulaires pour la pointe,
translucides (groupes trans_, alpha 150 à 220, arêtes et givre de la base plus opaques) ; l'âme : un bâton cyan opaque, tourné
de 15° pour qu'aucune face ne soit parallèle aux facettes. Petits éclats en pyramide hexagonale (même recette).
Faces parallèles qui se chevauchent : mesurées par cosmetiques/chapeaux/diademe_berenice/.build/mesure_faces.py.

Fonctions avancées (guide 4 bis, 5 ter, 6.4, 6.5) :
- trans_<cristal> : peau de glace semi-transparente (vue en jeu avec shader) ;
- calque _e : âmes des cristaux (150 à 225 sur de petites surfaces), cœur du flocon, particule ; sans shader seulement ;
- ctrl_lumiere : les âmes s'allument à l'équipement et respirent en overlay (non simulé, à juger en jeu) ;
- overlay_scintille (6 s) : les âmes battent doucement l'une après l'autre ;
- event_equip (1,5 s) : les prismes poussent depuis le cercle en cascade, le flocon tourne, un carillon d'améthyste ;
- particle_scintille / emit_scintille (5 points aux pointes) : petite étoile qui flotte et fond, rare (réglages.json).
Sons : un seul, à l'équipement (tools/sons.py). Pas de reflets _r (REFLETS = False, tools/ambiance.py).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons

NOM = "couronne_givre"
AVEC_E = True
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


ICE_L, ICE, ICE_D = C3(244, 253, 255), C3(120, 208, 238), C3(8, 34, 70)
FROST_L, FROST, FROST_D = C3(255, 255, 255), C3(214, 238, 250), C3(150, 190, 214)
SIL_L, SIL, SIL_D = C3(226, 236, 244), C3(160, 180, 200), C3(70, 86, 110)
GLOW_L, GLOW, GLOW_D = C3(210, 245, 255), C3(150, 226, 255), C3(40, 110, 170)


def grid(W, H):
    w, h = W * SS, H * SS
    return np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)


def noise(shape, seed, k=9):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, shape)
    ker = np.ones(k) / k
    n = np.apply_along_axis(lambda r: np.convolve(r, ker, mode="same"), 0, n)
    n = np.apply_along_axis(lambda r: np.convolve(r, ker, mode="same"), 1, n)
    return n / (n.std() + 1e-6)


def down(col, W, H, alpha=None):
    """Opaque : alpha 0/255, couleur moyenne hors silhouette."""
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


def down_trans(col, op, mask, W, H):
    """Translucide (groupes trans_ seulement) : silhouette nette (0 dehors), opacité peinte 150–220 dedans."""
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    solid = np.array(Image.fromarray((mask * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    o = np.array(Image.fromarray(np.clip(op, 0, 255).astype(np.uint8), "L").resize((W, H), Image.BOX)).astype(int)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = rgb
    if solid.any():
        arr[~solid, :3] = rgb[solid].mean(axis=0).astype(np.uint8)
    arr[..., 3] = np.where(solid, np.clip(o, 150, 220), 0)
    return arr


def down_e(ec, ref):
    H, W = ref.shape[:2]
    eo = np.array(Image.fromarray(np.clip(ec, 0, 225).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    return np.dstack([eo, np.where(ref[..., 3] > 0, 255, 0)]).astype(np.uint8)


def no_e(ref):
    e = np.zeros_like(ref)
    e[..., 3] = np.where(ref[..., 3] > 0, 255, 0)
    return e


def cracks(shape, seed, n=2):
    """Fines fissures blanches : quelques segments brisés, renvoie un masque 0..1."""
    h, w = shape
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    m = np.zeros(shape, np.float32)
    for _ in range(n):
        x, y = rng.uniform(0.25, 0.75) * w, rng.uniform(0.15, 0.55) * h
        ang = rng.uniform(1.1, 2.0)
        for _s in range(3):
            L = rng.uniform(0.12, 0.22) * h
            x1, y1 = x + math.cos(ang) * L, y + math.sin(ang) * L
            # distance au segment
            vx, vy = x1 - x, y1 - y
            t = np.clip(((xx - x) * vx + (yy - y) * vy) / (vx * vx + vy * vy), 0, 1)
            d = np.hypot(xx - x - t * vx, yy - y - t * vy)
            m = np.maximum(m, np.clip(1 - d / (0.5 * SS), 0, 1))
            x, y = x1, y1
            ang += rng.uniform(-0.6, 0.6)
    return m


def facet_side(W, H, seed, variant, base_frost=0.16):
    """Facette d'un prisme : base en bas (v = 1). Arêtes blanches plus opaques, givre en dentelle à la base, chevrons de taille."""
    u, v = grid(W, H)
    nz = noise(u.shape, seed)
    col = lerp(C3(206, 238, 250), C3(150, 206, 234), smooth(v)[..., None])        # glace pâle : l'âme cyan se lit au travers
    col = lerp(col, ICE_D, (smooth((v - 0.55) / 0.45) * 0.16)[..., None])
    op = 150 + 12 * smooth(v)
    # chevrons de facettes : bandes claires obliques
    if variant == 0:
        ch = np.abs(((v * H / D) * 1.6 + np.abs(u - 0.5) * 1.4) % 1.0 - 0.5)
        band = np.clip(1 - ch / 0.07, 0, 1) * (v < 0.82)
    else:
        ch = np.abs(((v * H / D) * 1.1 - np.abs(u - 0.5) * 1.8) % 1.0 - 0.5)
        band = np.clip(1 - ch / 0.05, 0, 1) * (v < 0.82) * 0.7
    col = lerp(col, ICE_L, (band * 0.55)[..., None])
    op = op + 22 * band
    # reflet vertical doux, décalé
    col = lerp(col, ICE_L, (np.clip(1 - np.abs(u - (0.34 if variant else 0.62)) / 0.09, 0, 1) * 0.35 * (1 - v))[..., None])
    # arêtes du prisme : blanc givré, plus opaque
    ed = np.minimum(u, 1 - u) * W / D           # en px
    ek = np.clip(1 - ed / 0.085, 0, 1)
    col = lerp(col, ICE_L, ek[..., None] * 0.9)
    op = np.maximum(op, 170 + 50 * ek)
    # fissures
    ck = cracks(u.shape, seed + 7, 2)
    col = lerp(col, FROST_L, ck[..., None] * 0.85)
    op = np.maximum(op, 150 + 50 * ck)
    # givre de la base : bord dentelé
    lim = 1 - base_frost * (1 + 0.35 * np.sin(u * TAU * 3 + seed) + 0.25 * nz)
    fk = smooth((v - lim) / 0.05)
    fcol = lerp(FROST, FROST_L, np.clip(0.5 + 0.35 * nz, 0, 1)[..., None])
    col = lerp(col, fcol, fk[..., None])
    op = lerp(op, 214 + 6 * np.clip(nz, -1, 1), fk)
    mask = np.ones(u.shape, bool)
    return down_trans(col, op, mask, W, H)


def facet_tri(W, H, seed, vb=1.0, base_frost=0.0):
    """Triangle : pointe en haut (v = 0), base pleine largeur à v = vb (rectangle en dessous, enfoui dans le socle)."""
    u, v = grid(W, H)
    nz = noise(u.shape, seed)
    q = np.clip(v / vb, 0, 1)
    half = 0.5 * q
    mask = (np.abs(u - 0.5) <= half) | (v > vb)
    col = lerp(ICE_L, C3(120, 206, 240), smooth(q)[..., None])
    col = lerp(col, C3(70, 160, 214), (smooth((q - 0.6) / 0.4) * 0.5)[..., None])
    op = 186 - 26 * smooth(q)
    # arête médiane (faîte de la facette) un peu plus claire
    rid = np.clip(1 - np.abs(u - 0.5) * W / D / 0.06, 0, 1) * (q > 0.05)
    col = lerp(col, ICE_L, rid[..., None] * 0.35)
    # bords obliques : arêtes blanches opaques
    dist = (half - np.abs(u - 0.5)) * W / D / np.sqrt(1 + (0.5 * W / (vb * H)) ** 2)
    ek = np.clip(1 - dist / 0.08, 0, 1) * (v <= vb)
    col = lerp(col, ICE_L, ek[..., None] * 0.92)
    op = np.maximum(op, 172 + 48 * ek)
    ck = cracks(u.shape, seed + 3, 1)
    col = lerp(col, FROST_L, (ck * (q > 0.35))[..., None] * 0.8)
    if base_frost > 0:
        lim = 1 - base_frost * (1 + 0.35 * np.sin(u * TAU * 2 + seed) + 0.25 * nz)
        fk = smooth((v - lim) / 0.06)
        col = lerp(col, lerp(FROST, FROST_L, np.clip(0.5 + 0.35 * nz, 0, 1)[..., None]), fk[..., None])
        op = lerp(op, 214, fk)
    return down_trans(col, op, mask, W, H)


def core_tile(W=16, H=96):
    """Âme opaque : cyan vif au milieu, bleu plus profond aux deux bouts ; calque _e 150–225."""
    a = np.zeros((H, W, 4), np.float32)
    e = np.zeros((H, W, 4), np.float32)
    for yy in range(H):
        t = (yy + 0.5) / H
        k = math.sin(math.pi * min(1, t * 1.15)) ** 0.7
        a[yy, :, :3] = lerp(C3(20, 120, 200), C3(120, 236, 255), k)
        e[yy, :, :3] = lerp(C3(90, 160, 190), C3(160, 220, 225), k)
    for xx in range(W):
        f = 1 - 0.18 * abs((xx + 0.5) / W - 0.5) * 2
        a[:, xx, :3] *= f
    a[..., 3] = 255
    e[..., 3] = 255
    return a.astype(np.uint8), np.clip(e, 0, 225).astype(np.uint8)


def band_face(W, H, seed):
    """Face du cercle : argent froid bombé, biseau clair en haut, dentelle de givre blanche en festons sur la moitié basse."""
    u, v = grid(W, H)
    col = lerp(SIL_L, SIL, smooth((v - 0.12) / 0.45)[..., None])
    col = lerp(col, SIL_D, smooth((v - 0.7) / 0.3)[..., None] * 0.75)
    col = lerp(col, C3(250, 252, 255), np.clip(1 - np.abs(v - 0.1) / 0.06, 0, 1)[..., None] * 0.85)
    col = lerp(col, C3(52, 64, 86), (np.minimum(v, 1 - v) < 0.045)[..., None] * 0.7)
    rng = np.random.default_rng(seed)
    rows = np.convolve(rng.normal(0, 1, H * SS), np.ones(9) / 3, mode="same")
    col = col * (1 + 0.04 * np.clip(rows, -1.5, 1.5))[:, None, None]
    # dentelle : festons (arcs) tous les 0,48 px, une perle de givre dans chaque arc, filet clair au-dessus
    pas = 0.48 * D / W
    k = (u / pas) % 1 - 0.5
    dx, dy = k * pas * W / D, (v - 0.46) * H / D          # px
    arc = np.abs(np.hypot(dx, dy) - 0.2) < 0.035
    arc &= dy > -0.02
    perle = np.hypot(dx, dy - 0.2) < 0.055
    fil = np.abs(v - 0.36) * H / D < 0.022
    pic = (np.abs(dx) < 0.02) & (dy > 0.2) & (dy < 0.33)          # petite pique entre deux festons
    pic = (np.abs(np.abs(dx) - pas * W / D / 2) < 0.022) & (dy > -0.02) & (dy < 0.2)
    lace = arc | perle | fil | pic
    col = np.where(lace[..., None], lerp(FROST, FROST_L, 0.6), col)
    out = down(col, W, H)
    return out, no_e(out)


def plain(W, H, top, bot, frost=False, seed=0):
    u, v = grid(W, H)
    col = lerp(C3(*top), C3(*bot), smooth(v)[..., None])
    if frost:
        nz = noise(u.shape, seed, 5)
        star = np.zeros(u.shape, bool)
        cx, cy = (u - 0.5) * W / D, (v - 0.5) * H / D
        r, th = np.hypot(cx, cy), np.arctan2(cy, cx)
        arms = np.abs(np.sin(3 * th)) < 0.12 * (0.3 / np.maximum(r, 0.05))
        col = lerp(col, FROST_L, (np.clip(0.3 + 0.3 * nz, 0, 1))[..., None])
        col = lerp(col, FROST_L, (arms & (r < 0.42 * min(W, H) / D))[..., None] * 0.7)
    out = down(col, W, H)
    return out, no_e(out)


def bezel_tile(W, H):
    """Chaton d'angle : argent, losange gravé, givre en haut."""
    u, v = grid(W, H)
    col = lerp(SIL_L, SIL_D, smooth(v)[..., None] * 0.8)
    q = np.abs(u - 0.5) * 2 + np.abs(v - 0.52) * 2 * H / W
    col = np.where((np.abs(q - 0.55) < 0.06)[..., None], C3(60, 74, 98), col)
    col = np.where((q < 0.36)[..., None], lerp(FROST, FROST_L, 0.5), col)
    col = lerp(col, C3(250, 252, 255), np.clip(1 - np.abs(v - 0.07) / 0.05, 0, 1)[..., None] * 0.9)
    out = down(col, W, H)
    return out, no_e(out)


def flake(W=52):
    """Flocon à six branches : branches à barbes, bord givré, cœur cyan lumineux."""
    u, v = grid(W, W)
    gx, gy = u * 2 - 1, 1 - v * 2
    r, th = np.hypot(gx, gy), np.arctan2(gy, gx)
    ins = np.zeros(gx.shape, bool)
    body = np.zeros(gx.shape, np.float32)
    for k in range(6):
        a = math.radians(90 + 60 * k)
        dx, dy = math.cos(a), math.sin(a)
        s = gx * dx + gy * dy
        n = -gx * dy + gy * dx
        arm = (s > 0) & (s < 0.96) & (np.abs(n) < 0.085 * (1 - 0.5 * s))
        ins |= arm
        for b0 in (0.42, 0.68):
            for sg in (-1, 1):
                ba = a + sg * math.radians(55)
                bx, by = math.cos(ba), math.sin(ba)
                px, py = gx - dx * b0, gy - dy * b0
                bs = px * bx + py * by
                bn = -px * by + py * bx
                ins |= (bs > 0) & (bs < (0.3 if b0 < 0.5 else 0.22)) & (np.abs(bn) < 0.055)
        body = np.maximum(body, np.clip(1 - np.abs(n) / 0.05, 0, 1) * (s > 0))
    hexc = np.maximum(np.abs(gx) * 0.87 + np.abs(gy) * 0.5, np.abs(gy)) < 0.24
    ins |= hexc
    col = lerp(FROST, FROST_L, body[..., None])
    col = lerp(col, FROST_D, smooth((r - 0.7) / 0.3)[..., None] * 0.5)
    col = np.where(hexc[..., None], lerp(GLOW_L, GLOW, smooth(r / 0.24)[..., None]), col)
    ec = np.zeros(col.shape, np.float32)
    ec = np.where(hexc[..., None], C3(150, 215, 225) * (1 - 0.4 * smooth(r / 0.24))[..., None], ec)
    out = down(col, W, W, ins)
    return out, down_e(ec, out)


def sparkle(W=28):
    """Particule : petite étoile à quatre branches, blanche au centre, branches cyan."""
    u, v = grid(W, W)
    gx, gy = u * 2 - 1, v * 2 - 1
    sh = np.abs(gx) ** 0.55 + np.abs(gy) ** 0.55
    ins = sh < 1
    r = np.hypot(gx, gy)
    col = lerp(FROST_L, C3(150, 226, 255), smooth(r / 0.8)[..., None])
    ec = C3(200, 225, 225) * np.clip(1 - r / 0.7, 0, 1)[..., None] + np.zeros(col.shape, np.float32)
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
    tex_e[y:y + h, x:x + w] = em if em is not None else no_e(im)
    UV[name] = (x, y, x + w, y + h)
    _cur[0] += w + 2
    _cur[2] = max(_cur[2], h)


SKIN = 0.30          # épaisseur d'une plaque de peau
SOCK_H = 0.32        # épaisseur d'un socle
EMBED = 0.12         # la peau entre d'autant dans son socle

# Cristaux : (nom, forme, x, z, direction extérieure (x, z), inclinaison (rad), apothème, longueur des faces, longueur de la pointe, socle)
# Hauteurs décroissantes du front vers la nuque.
CRISTAUX = [
    ("c", "hex", 0.0, -4.83, (0, -1), 0.07, 0.90, 3.50, 1.60, "grappe"),
    ("gl", "pyr", -1.30, -5.28, (-1, -0.35), 0.30, 0.42, 2.20, 0, None),
    ("gr", "pyr", 1.30, -5.28, (1, -0.35), 0.30, 0.42, 2.20, 0, None),
    ("fl", "hex", -2.75, -4.83, (-0.5, -1), 0.16, 0.66, 2.30, 1.25, "own"),
    ("fr", "hex", 2.75, -4.83, (0.5, -1), 0.16, 0.66, 2.30, 1.25, "own"),
    ("kl", "hex", -4.755, -4.755, (-1, -1), 0.22, 0.58, 1.60, 1.05, "own"),
    ("kr", "hex", 4.755, -4.755, (1, -1), 0.22, 0.58, 1.60, 1.05, "own"),
    ("tl", "hex", -4.83, -0.90, (-1, 0), 0.26, 0.52, 1.20, 0.95, "own"),
    ("tr", "hex", 4.83, -0.90, (1, 0), 0.26, 0.52, 1.20, 0.95, "own"),
    ("nl", "pyr", -4.755, 4.755, (-1, 1), 0.30, 0.42, 1.50, 0, "own"),
    ("nr", "pyr", 4.755, 4.755, (1, 1), 0.30, 0.42, 1.50, 0, "own"),
]
PYR_EMBED = 0.24     # éclats de la grappe : inclinés sur le socle du cristal central, plus enfoncés

seed = 21
for nm, forme, x, z, o, th, a, Ls, Lt, so in CRISTAUX:
    if nm[0] in "lr" or (len(nm) == 2 and nm[1] == "r"):
        continue                                  # les deux côtés partagent leurs tuiles
    key = nm[0]
    s = 2 * a / math.sqrt(3)
    W = max(8, int(round(s * D)))
    if forme == "hex":
        Hs = int(round((Ls + EMBED) * D))
        place(f"side_{key}0", *(lambda t: (t, no_e(t)))(facet_side(W, Hs, seed, 0)))
        place(f"side_{key}1", *(lambda t: (t, no_e(t)))(facet_side(W, Hs, seed + 1, 1)))
        slant = math.hypot(a, Lt)
        Ht = int(round(slant * D))
        place(f"tip_{key}", *(lambda t: (t, no_e(t)))(facet_tri(W, Ht, seed + 2)))
    else:
        emb = PYR_EMBED if so is None else EMBED
        slant = math.hypot(a, Ls)
        Ht = int(round((slant + emb) * D))
        place(f"pyr_{key}", *(lambda t: (t, no_e(t)))(facet_tri(W, Ht, seed + 3, vb=slant / (slant + emb), base_frost=0.12)))
    seed += 5

place("coeur", *core_tile())
BL = 9.40
BH, BT = 0.90, 0.35
place("band", *band_face(int(round(BL * D)), int(round(BH * D)), 4))
place("band_top", *plain(int(round(BL * D)), int(round(BT * D)), (230, 240, 248), (150, 170, 192)))
place("bezel", *bezel_tile(36, 41))
place("sock_side", *plain(72, 12, (236, 244, 250), (120, 140, 164)))
place("sock_top", *plain(72, 72, (214, 238, 250), (176, 206, 228), frost=True, seed=5))
place("flake", *flake(60))
place("flake_c", *plain(16, 16, (240, 248, 255), (170, 200, 222)))
place("spark", *sparkle())

CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
_b64 = []
for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(fn, optimize=True)
    _buf = io.BytesIO()
    im_.save(_buf, "PNG", optimize=True)
    _b64.append("data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode())
tex_b64, tex_e_b64 = _b64
assert tex_e[..., :3].max() <= 225, "calque trop vif"

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
    if abs(R[2, 0]) > 0.99999:          # blocage de cardan (Y = ±90°) : Z = 0, tout l'angle restant en X
        sy = -R[2, 0]
        return math.degrees(math.atan2(sy * R[0, 1], R[1, 1])), math.degrees(ry), 0.0
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def rodrigues(k, th):
    k = unit(k)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K


def group(name, origin, parent=None):
    key = name
    if name.startswith(("emit_mc_", "ctrl_")):
        key = f"{name}#{len(groups)}"
    assert key not in groups, key
    groups[key] = {"name": name, "origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent}
    return key


def cube(g, name, c, size, X, Y, faces):
    """Cube centré en c, axes X, Y (orthonormés), Z = X × Y."""
    c, size = np.asarray(c, float), np.asarray(size, float)
    X, Y = unit(np.asarray(X, float)), unit(np.asarray(Y, float))
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    rot = euler(R_)
    rx, ry, rz = (math.radians(v) for v in rot)
    Rx = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Ry = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Rz = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    assert np.allclose(Rz @ Ry @ Rx, R_, atol=1e-4), f"angles faux : {name}"
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in c - size / 2], "to": [round(float(v), 3) for v in c + size / 2],
         "origin": [round(float(v), 3) for v in c], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def all_faces(tile):
    return {f: list(UV[tile]) for f in ("north", "south", "east", "west", "up", "down")}


def full(tile, flip=False):
    u0, v0, u1, v1 = UV[tile]
    return [u1, v0, u0, v1] if flip else [u0, v0, u1, v1]


def sub(tile, L):
    u0, v0, u1, v1 = UV[tile]
    w = min(u1 - u0, L * D)
    a = u0 + (u1 - u0 - w) / 2
    return [a, v0, a + w, v1]


def only(face, uv):
    f = {k: CLEAR for k in ("north", "south", "east", "west", "up", "down")}
    f[face] = uv
    return f


Y1, X1 = V(0, 1, 0), V(1, 0, 0)
RING_B, RING_T = 31.88, 32.80          # bas et haut du cercle
RING_Y = (RING_B + RING_T) / 2
BI, BO = 4.65, 5.00
MID = (BI + BO) / 2
SOCK_B = 32.68                          # dessous des socles : 0,18 au-dessus de la seconde couche (32,5)

ROOT = group("couronne", [0, RING_Y, 0])
RING = group("cercle", [0, RING_Y, 0], parent=ROOT)
CTRL = group("ctrl_lumiere", [0, RING_Y, 0], parent=ROOT)

be = list(UV["sock_side"])


def band_seg(name, c, L, X, outer):
    faces = {k: be for k in ("north", "south", "east", "west")}
    faces["up"] = sub("band_top", L)
    faces["down"] = sub("band_top", L)
    faces[outer] = sub("band", L)
    faces[{"north": "south", "south": "north"}[outer]] = CLEAR        # face contre la tête
    cube(RING, name, c, (L, RING_T - RING_B, BO - BI), X, Y1, faces)


# front et nuque : x de -4,70 à 4,70 ; tempes : z de -4,62 à 4,62 ; les coins sont fermés par les chatons (aucun recouvrement)
band_seg("front", V(0, RING_Y, -MID), 9.40, X1, "north")
band_seg("nuque", V(0, RING_Y, MID), 9.40, X1, "south")
for sx, tag in ((-1, "l"), (1, "r")):
    band_seg(f"tempe_{tag}", V(sx * MID, RING_Y, 0), 9.24, V(0, 0, -sx), "south")
# chatons d'angle : faces intérieure à 6,55 et extérieure à 6,90 sur la diagonale, 0,12 plus hauts et plus bas que le cercle
DI, DO = 6.55, 6.90
for sx in (-1, 1):
    for sz in (-1, 1):
        o = unit(V(sx, 0, sz))
        X_ = np.cross(Y1, o)
        c = o * (DI + DO) / 2 + V(0, RING_Y, 0)
        bz = list(UV["bezel"])
        f = {k: bz for k in ("south", "east", "west")}
        f["north"] = CLEAR                         # Z = X × Y = o : south regarde vers l'extérieur
        f["up"] = list(UV["sock_side"])
        f["down"] = list(UV["sock_side"])
        cube(RING, f"chaton_{'l' if sx < 0 else 'r'}{'av' if sz < 0 else 'ar'}", c, (1.0, RING_T - RING_B + 0.24, DO - DI), X_, Y1, f)

# flocon au front, 0,12 px devant le cercle, au haut du front
FLK_Y = 31.90
FLK = group("flocon", [0, FLK_Y, -5.27], parent=ROOT)
cube(FLK, "flocon", V(0, FLK_Y, -5.27), (1.66, 1.66, 0.30), X1, Y1, only("north", full("flake", True)))
cube(FLK, "flocon_ame", V(0, FLK_Y, -5.05), (0.46, 0.46, 0.40), unit(V(1, 1, 0)), unit(V(-1, 1, 0)), all_faces("flake_c"))

# cristaux
CRIS, POUSSE, COEURS, EMITS, OUT = {}, {}, {}, [], {}
cu = list(UV["coeur"])


def emit_name():
    return "emit_scintille" + (str(len(EMITS) + 1) if EMITS else "")


def build(nm, forme, x, z, o2, th, a, Ls, Lt, so, parent_grp=None, base_y=None):
    o = unit(V(o2[0], 0, o2[1]))
    Rm = rodrigues(np.cross(Y1, o), th) if th > 0 else np.eye(3)
    key = nm[0] if not (len(nm) == 2 and nm[1] in "lr" and nm[0] != "c") else nm[0]
    Yp = Rm @ Y1
    if so is not None:
        # socle (dans le groupe du cristal, incliné avec lui) ; pivot au milieu de son dessous
        piv = V(x, SOCK_B, z)
        T = np.cross(Y1, o)
        Op, Tp = Rm @ o, Rm @ T
        dr = 2 * a + 0.32                 # faces du socle à 0,16 px des facettes parallèles
        # pivot animé au bord intérieur du dessous du socle : un cristal qui bascule ne descend jamais vers la tête
        g = group(f"cristal_{nm}", piv - Op * dr / 2, parent=ROOT)
        wt = 2 * (2 * a / math.sqrt(3)) + 0.24
        if so == "grappe":
            wt = 3.6
        st = list(UV["sock_top"])
        ss = list(UV["sock_side"])
        cube(g, f"socle_{nm}", piv + Yp * SOCK_H / 2, (wt, SOCK_H, dr), Tp, Yp,
             {"north": ss, "south": ss, "east": ss, "west": ss, "up": st, "down": ss})
        B = piv + Yp * SOCK_H
        emb = EMBED
    else:
        g = parent_grp
        B = V(x, base_y, z)
        emb = PYR_EMBED
    CRIS[nm] = g
    OUT[nm] = o
    Op = Rm @ o
    Tp = Rm @ np.cross(Y1, o)
    pg = group(f"pousse_{nm}", B, parent=g)
    POUSSE[nm] = pg
    tg = group(f"trans_{nm}", B, parent=pg)
    s = 2 * a / math.sqrt(3)
    if forme == "hex":
        for k in range(6):
            ph = math.radians(60 * k)
            n = math.cos(ph) * Op + math.sin(ph) * Tp
            X = np.cross(Yp, n)
            c = B + Yp * (Ls - emb) / 2 + n * (a - SKIN / 2)
            cube(tg, f"{nm}.f{k}", c, (s, Ls + emb, SKIN), X, Yp, only("south", full(f"side_{key}{k % 2}", k >= 3)))
            M = B + Yp * Ls + n * a
            A = B + Yp * (Ls + Lt)
            dd = unit(A - M)
            Z = np.cross(X, dd)
            cube(tg, f"{nm}.p{k}", (M + A) / 2 - Z * SKIN / 2, (s, float(np.linalg.norm(A - M)), SKIN), X, dd, only("south", full(f"tip_{key}", k >= 3)))
        tip = B + Yp * (Ls + Lt)
        Lc = Ls + 0.45 * Lt
    else:
        A = B + Yp * Ls
        for k in range(6):
            ph = math.radians(60 * k)
            n = math.cos(ph) * Op + math.sin(ph) * Tp
            X = np.cross(Yp, n)
            M = B + n * a
            dd = unit(A - M)
            Z = np.cross(X, dd)
            L = float(np.linalg.norm(A - M))
            c = (M + A) / 2 - dd * emb / 2 - Z * SKIN / 2
            cube(tg, f"{nm}.f{k}", c, (s, L + emb, SKIN), X, dd, only("south", full(f"pyr_{key}", k >= 3)))
        tip = A
        Lc = 0.42 * Ls
    # âme : bâton opaque tourné de 15° autour de l'axe (aucune face parallèle à une facette)
    cg = group(f"coeur_{nm}", B, parent=pg)
    COEURS[nm] = cg
    wc = 0.5 * a if forme == "hex" else 0.22      # demi-diagonale sous la face intérieure de la peau (prismes) ou sous la face extérieure (éclats)
    Xc = math.cos(math.radians(15)) * Op + math.sin(math.radians(15)) * Tp
    cemb = 0.15 if so is not None else PYR_EMBED
    cube(cg, f"{nm}.ame", B + Yp * (Lc - cemb) / 2, (wc, Lc + cemb, wc), Xc, Yp,
         {"north": cu, "south": cu, "east": cu, "west": cu, "up": [cu[0], cu[1], cu[2], cu[1] + 4], "down": [cu[0], cu[3] - 4, cu[2], cu[3]]})
    if forme == "hex" or so is None:
        if nm[0] in "cfk" or nm in ("gl", "gr"):
            EMITS.append(group(emit_name(), tip + Yp * 0.15, parent=pg))
    return B


for nm, forme, x, z, o2, th, a, Ls, Lt, so in CRISTAUX:
    if so is None:
        continue
    B = build(nm, forme, x, z, o2, th, a, Ls, Lt, so)
    if nm == "c":
        for nm2, forme2, x2, z2, o22, th2, a2, Ls2, Lt2, so2 in CRISTAUX:
            if so2 is None:
                # base sur le dessus du socle central (incliné de 0,07 vers l'avant) : hauteur au point (x2, z2)
                Rm = rodrigues(np.cross(Y1, V(0, 0, -1)), th)
                Yp = Rm @ Y1
                piv = V(x, SOCK_B, z)
                top = piv + Yp * SOCK_H
                yb = top[1] - (Yp[2] / Yp[1]) * (z2 - top[2])
                build(nm2, forme2, x2, z2, o22, th2, a2, Ls2, Lt2, so2, parent_grp=CRIS["c"], base_y=yb)

# particule modélisée : petite étoile, à la racine (jamais portée)
PART = group("particle_scintille", [0, 0, 0])
cube(PART, "scintille", V(0, 0.65, 0), (0.7, 0.7, 0.3), X1, Y1, only("south", full("spark")))


def bone(name):
    g = groups[name]
    return {"name": g["name"], "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "head", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone(ROOT)]}, bone(PART)]


# ------------------------------------------------------------------ animations
# Guide, section 3 : +X = le haut part vers l'arrière (+Z) ; +Z = le côté droit (+X) monte, donc le haut part vers -X.
# Incliner le haut d'un cristal d'un angle t vers la direction horizontale o : rotation (t·o_z, 0, -t·o_x).
def kf(t, x, y, z, ch="rotation"):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 3)), "y": str(round(y + 0.0, 3)), "z": str(round(z + 0.0, 3))}],
            "time": round(t, 3), "interpolation": "linear"}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


ORDRE = ["c", "gl", "gr", "fl", "fr", "kl", "kr", "tl", "tr", "nl", "nr"]       # du front vers la nuque
RANG = {"c": 0, "gl": 1, "gr": 1, "fl": 2, "fr": 2, "kl": 3, "kr": 3, "tl": 4, "tr": 4, "nl": 5, "nr": 5}
TOP = ["c", "fl", "fr", "kl", "kr", "tl", "tr", "nl", "nr"]                    # groupes cristal_ (la grappe suit le central)
SIDE = {"gl": "gl", "gr": "gr"}


def state(name, length, outw, back, n_kf=None, loop="loop", extra=None):
    """outw(t, rang) : inclinaison vers l'extérieur (°) ; back(t, rang) : vers l'arrière (°). Rotations rigides des cristaux
    (groupes pousse_, pivot au milieu de la base) ; les socles restent fixes sur le cercle."""
    n = n_kf or max(8, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]
    A = {}
    for nm in TOP + ["gl", "gr"]:
        g = POUSSE[nm]           # le cristal pivote à sa base, sur son socle fixe : rien ne descend vers la tête
        o = OUT[nm]
        r = RANG[nm]
        kfs = []
        for t in times:
            w = outw(t, r)
            b = back(t, r)
            kfs.append(kf(t, w * o[2] + b, 0, -w * o[0]))
        A[groups[g]["uuid"]] = {"name": groups[g]["name"], "type": "bone", "keyframes": kfs}
    if extra:
        extra(A, times)
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


def P(T, amp, ph=0.0):
    return lambda t, r: amp * math.sin(TAU * t / T - r * ph)


Z0 = lambda t, r: 0.0
# idle 8 s : respiration à peine visible (4 s) et un frisson de givre qui court du front à la nuque vers 5 s
idle = state("idle", 8.0, lambda t, r: 0.25 * math.sin(TAU * t / 4 - r * 0.5) + 1.2 * bump(t, 4.8 + 0.12 * r, 5.0 + 0.12 * r, 5.15 + 0.12 * r, 5.7 + 0.12 * r), Z0, n_kf=64)
# walk 1,6 s : petit tremblement à chaque pas (deux par cycle)
walk = state("walk", 1.6, lambda t, r: 0.5 * math.sin(2 * TAU * t / 1.6 - r * 0.6), lambda t, r: 0.4 + 0.3 * math.sin(2 * TAU * t / 1.6 - r * 0.6 + 1), n_kf=24)
# run 1,0 s : vent de face, les cristaux se couchent un peu, tremblement plus net
run = state("run", 1.0, lambda t, r: 0.9 * math.sin(2 * TAU * t - r * 0.6), lambda t, r: 2.0 + 0.6 * math.sin(2 * TAU * t - r * 0.6 + 1), n_kf=16)
# sneak 3 s : presque immobile, resserré
sneak = state("sneak", 3.0, lambda t, r: -0.8 + 0.2 * math.sin(TAU * t / 3 - r * 0.5), Z0, n_kf=24)
# fly 2,4 s : vent, couchés vers l'arrière, frémissement
fly = state("fly", 2.4, lambda t, r: 0.6 * math.sin(TAU * t / 1.2 - r * 0.6), lambda t, r: 3.0 + 0.8 * math.sin(TAU * t / 1.2 - r * 0.6 + 1.2), n_kf=24)
# glide 3,6 s : vent plus fort (corps couché, la tête regarde devant)
glide = state("glide", 3.6, lambda t, r: 0.5 * math.sin(TAU * t / 1.2 - r * 0.6), lambda t, r: 5.0 + 0.8 * math.sin(TAU * t / 1.2 - r * 0.6 + 1.2), n_kf=24)


# attack 0,8 s : les cristaux s'ouvrent d'un coup (cascade du front vers la nuque), les âmes s'épaississent (jamais plus hautes : elles sortiraient des pointes) ; retour à 0
def atk_extra(A, times):
    for nm in ORDRE:
        r = RANG[nm]
        A[groups[COEURS[nm]]["uuid"]] = {"name": groups[COEURS[nm]]["name"], "type": "bone",
                                          "keyframes": [kf(t, 1 + 0.1 * bump(t, 0.02 * r, 0.1 + 0.02 * r, 0.25, 0.7), 1, 1 + 0.1 * bump(t, 0.02 * r, 0.1 + 0.02 * r, 0.25, 0.7), ch="scale") for t in times]}


attack = state("attack", 0.8, lambda t, r: 7 * bump(t, 0.03 * r, 0.1 + 0.03 * r, 0.25 + 0.03 * r, 0.72), Z0, n_kf=16, loop="once", extra=atk_extra)
# hurt 0,8 s : sursaut vers l'arrière, tremblement amorti
hurt = state("hurt", 0.8, lambda t, r: 1.6 * math.sin(TAU * t * 6 / 0.8 - r) * (1 - sm(t, 0.1, 0.7)),
             lambda t, r: 4 * bump(t, 0.0, 0.07, 0.15, 0.6), n_kf=24, loop="once")

# overlay_scintille (6 s, par-dessus tous les états) : les âmes battent l'une après l'autre, la lumière respire
OV = 6.0
ov_t = [i * OV / 24 for i in range(25)]
ov_a = {}
for i, nm in enumerate(ORDRE):
    ph = TAU * ((i * 0.37) % 1)
    ov_a[groups[COEURS[nm]]["uuid"]] = {"name": groups[COEURS[nm]]["name"], "type": "bone",
                                         "keyframes": [kf(t, *(1 + 0.06 * math.sin(TAU * t / OV + ph),) * 3, ch="scale") for t in ov_t]}
ov_a[groups[CTRL]["uuid"]] = {"name": "ctrl_lumiere", "type": "bone", "keyframes": [kf(t, 0.15 * math.sin(TAU * t / OV), 0, 0, ch="position") for t in ov_t]}
overlay = {"uuid": nuid(), "name": "overlay_scintille", "loop": "loop", "override": False, "length": OV, "snapping": 24, "selected": False, "animators": ov_a}

# event_equip (1,5 s) : les prismes poussent depuis le cercle, du front vers la nuque, avec un léger dépassement ; le flocon tourne
EQ = 1.5
eq_t = [i * EQ / 30 for i in range(31)]
eq_a = {}
for nm in ORDRE:
    r = RANG[nm]
    t0 = 0.05 + 0.12 * r
    gy = lambda t, t0=t0: sm(t, t0, t0 + 0.42) * (1 + 0.08 * bump(t, t0 + 0.3, t0 + 0.42, t0 + 0.46, t0 + 0.7))
    gxz = lambda t, t0=t0: 0.35 + 0.65 * sm(t, t0, t0 + 0.5)
    eq_a[groups[POUSSE[nm]]["uuid"]] = {"name": groups[POUSSE[nm]]["name"], "type": "bone",
                                         "keyframes": [kf(t, gxz(t), max(0.02, gy(t)), gxz(t), ch="scale") for t in eq_t]}
eq_a[groups[FLK]["uuid"]] = {"name": "flocon", "type": "bone", "keyframes": [kf(t, 0, 0, 180 * (1 - sm(t, 0.0, 0.8)), ch="rotation") for t in eq_t]}
lum = lambda t: -1 + sm(t, 0.3, 1.0) * 1.5 - 0.5 * sm(t, 1.0, 1.5)
eq_a[groups[CTRL]["uuid"]] = {"name": "ctrl_lumiere", "type": "bone", "keyframes": [kf(t, lum(t), 0, 0, ch="position") for t in eq_t]}
eq_a["effects"] = {"name": "Effects", "type": "effect", "keyframes": [{"channel": "sound", "data_points": [{"effect": "block.amethyst_block.chime", "file": ""}], "time": 0.55}]}
equip = {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": EQ, "snapping": 24, "selected": False, "animators": eq_a}

# particule : l'étoile pulse et se balance pendant qu'elle flotte (boucle fermée)
PF = 1.0
pf_t = [i * PF / 8 for i in range(9)]
p_fall = {"uuid": nuid(), "name": "particle_scintille_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24, "selected": False,
          "animators": {groups[PART]["uuid"]: {"name": "particle_scintille", "type": "bone",
                                               "keyframes": [kf(t, 0, 0, 20 * math.sin(TAU * t / PF)) for t in pf_t] +
                                                            [kf(t, *(1 + 0.25 * math.sin(TAU * t / PF * 2),) * 3, ch="scale") for t in pf_t]}}}

ANIMS = [idle, walk, run, sneak, fly, glide, attack, hurt, overlay, equip, p_fall]
assert 60 <= len(elements) <= 150, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
os.makedirs(".build", exist_ok=True)
OUTF = f".build/{NOM}_brut.bbmodel"
with open(OUTF, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUTF) // 1024, "Ko ;", len(EMITS), "emit_")
