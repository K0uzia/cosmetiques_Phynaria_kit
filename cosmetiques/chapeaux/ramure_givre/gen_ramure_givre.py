"""Ramure de givre : deux bois de cerf faits de glace, qui poussent sur le dessus de la tête au-dessus des tempes.
Design original, ensemble Givre (.claude/styles/givre.md), assorti à ailes_givre (cristaux taillés sur os de givre),
skin_epee_givre et familier_givre (bête du Nord). Remplace couronne_givre (« fixette sur des couronnes et bandeau », 2026-11-08).
Écrit ramure_givre.png, ramure_givre_e.png et .build/ramure_givre_brut.bbmodel à côté de ce script.

Anatomie (fiche .claude/references/animaux/cervides-equides.md, sources : NRA Women « antler terminology »,
Buckmasters ; ramure de renne : Rangifer, « asymmetry in antlers of barren-ground caribou ») traduite en glace :
- pivot + meule : une rosette de givre opaque posée sur le crâne (dessous à y ≥ 32,66, seconde couche du skin à 32,5),
  hérissée de petits éclats en pyramide, d'où sort le merrain ;
- merrain : quatre tronçons de prisme hexagonal translucide (trans_, alpha 150–220) à âme cyan lumineuse, qui montent vers
  l'extérieur puis se recourbent vers l'arrière en lyre ; chaque jointure est un nœud de givre opaque (l'« os de givre »
  des ailes) ;
- andouillers : un cristal pointu par embranchement, de la base au sommet : andouiller d'œil (vers l'avant et le haut, jamais
  devant le visage : z ≥ −2,6 et au-dessus du crâne), puis bez, trez (vers l'extérieur) et une empaumure de deux pointes
  au sommet. Légère asymétrie comme chez le renne : l'andouiller d'œil gauche est plus long et porte un éclat de plus.
Hauteur : la pointe monte à ≈ 8,5 px au-dessus de la tête (la fiche cervidés conseille 6 à 10), envergure ≈ 14 px.
Texture HD : 36 texels/px.

Volumes : cristal = peau + âme. Peau : six plaques de 0,3 px (une par facette) et six triangles pour la pointe, en groupes
trans_ ; âme : bâton cyan opaque tourné de 15° (aucune face parallèle aux facettes). Nœuds : cube opaque tourné de 15°.
La glace ne plie pas : seuls les andouillers vibrent d'un dixième de degré au pas, les tronçons restent fixes.

Fonctions avancées (guide 4 bis, 5 ter, 6.4, 6.5) :
- trans_<cristal> : peau de glace semi-transparente (validée en jeu sur l'ensemble Givre, avec et sans shader) ;
- calque _e : âmes des cristaux et cœur des nœuds (150 à 225 sur de petites surfaces), particule ;
- ctrl_lumiere : la ramure s'allume à l'équipement et respire en overlay (non simulé, à juger en jeu) ;
- overlay_scintille (6 s) : les âmes battent l'une après l'autre, de la base vers les pointes ;
- event_equip (1,6 s) : la ramure pousse depuis le crâne, tronçon par tronçon, chaque andouiller juste après son nœud ;
  un seul son (block.amethyst_cluster.place) ;
- particle_scintille / emit_scintille (6 points aux pointes) : petite étoile qui flotte et fond, rare (reglages.json).
Pas d'attack ni de hurt (pièce portée). Pas de reflets _r (REFLETS = False, tools/ambiance.py).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons

NOM = "ramure_givre"
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
    eo = np.minimum(np.array(Image.fromarray(np.clip(ec, 0, 225).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)), 225)
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



def knot_tile(W=40):
    """Nœud de givre : argent givré clair, dentelle et petite étoile ; cœur discret au calque _e."""
    u, v = grid(W, W)
    nz = noise(u.shape, 11, 5)
    cx, cy = (u - 0.5) * 2, (v - 0.5) * 2
    r = np.hypot(cx, cy)
    col = lerp(FROST_L, FROST, smooth(r / 1.2)[..., None])
    col = lerp(col, FROST_D, (np.clip(0.25 + 0.3 * nz, 0, 1) * smooth((r - 0.5) / 0.6))[..., None] * 0.8)
    th = np.arctan2(cy, cx)
    arms = (np.abs(np.sin(3 * th)) < 0.16 / np.maximum(r, 0.08)) & (r < 0.62)
    col = np.where(arms[..., None], lerp(C3(150, 226, 255), GLOW_L, 0.4), col)
    edge = np.maximum(np.abs(cx), np.abs(cy)) > 0.84
    col = np.where(edge[..., None], lerp(FROST, FROST_D, 0.35), col)
    ec = np.where(arms[..., None], C3(120, 190, 210), C3(0, 0, 0)) + np.zeros(col.shape, np.float32)
    out = down(col, W, W)
    return out, down_e(ec, out)


# ------------------------------------------------------------------ atlas (rempli à la demande pendant la géométrie)
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
EXT = 0.16           # un tronçon entre d'autant dans les nœuds à ses deux bouts
_seed = [31]


def tile_side(a, L, var, frost=0.10):
    key = f"side_{a:.2f}_{L:.2f}_{var}"
    if key not in UV:
        W = max(8, int(round(2 * a / math.sqrt(3) * D)))
        t = facet_side(W, int(round(L * D)), _seed[0] + var, var, base_frost=frost)
        _seed[0] += 3
        place(key, t, no_e(t))
    return key


def tile_tip(a, Lt):
    key = f"tip_{a:.2f}_{Lt:.2f}"
    if key not in UV:
        W = max(8, int(round(2 * a / math.sqrt(3) * D)))
        t = facet_tri(W, int(round(math.hypot(a, Lt) * D)), _seed[0])
        _seed[0] += 3
        place(key, t, no_e(t))
    return key


def tile_pyr(a, L, emb):
    key = f"pyr_{a:.2f}_{L:.2f}"
    if key not in UV:
        W = max(8, int(round(2 * a / math.sqrt(3) * D)))
        sl = math.hypot(a, L)
        t = facet_tri(W, int(round((sl + emb) * D)), _seed[0], vb=sl / (sl + emb), base_frost=0.12)
        _seed[0] += 3
        place(key, t, no_e(t))
    return key


place("coeur", *core_tile())
place("noeud", *knot_tile(40))
place("socle_top", *plain(64, 64, (226, 244, 252), (176, 206, 228), frost=True, seed=5))
place("socle_side", *plain(64, 16, (236, 244, 250), (130, 152, 176)))
place("spark", *sparkle())
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx, ordre du mod et du renderer."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if abs(R[2, 0]) > 0.99999:
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


CORNERS = []


def cube(g, name, c, size, X, Y, faces):
    """Cube centré en c, axes X, Y (orthonormés), Z = X × Y."""
    c, size = np.asarray(c, float), np.asarray(size, float)
    X, Y = unit(X), unit(Y)
    Z = np.cross(X, Y)
    R_ = np.column_stack([X, Y, Z])
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
    if not groups[g]["name"].startswith("particle_"):
        for i in (-1, 1):
            for j in (-1, 1):
                for k in (-1, 1):
                    CORNERS.append((name, c + X * size[0] / 2 * i + Y * size[1] / 2 * j + Z * size[2] / 2 * k))


def full(tile, flip=False):
    u0, v0, u1, v1 = UV[tile]
    return [u1, v0, u0, v1] if flip else [u0, v0, u1, v1]


def only(face, uv):
    f = {k: CLEAR for k in ("north", "south", "east", "west", "up", "down")}
    f[face] = uv
    return f


def every(tile):
    return {k: list(UV[tile]) for k in ("north", "south", "east", "west", "up", "down")}


def frame(Yp, ref):
    """Repère (Op, Tp) perpendiculaire à l'axe Yp, Op au plus près de ref."""
    Op = unit(ref - Yp * float(np.dot(ref, Yp)))
    return Op, np.cross(Yp, Op)


Y1, X1 = V(0, 1, 0), V(1, 0, 0)
ROOT_Y = 32.66
ROOT = group("ramure", [0, ROOT_Y, 0])
CTRL = group("ctrl_lumiere", [0, ROOT_Y, 0], parent=ROOT)
cu = list(UV["coeur"])
CORE_F = {"north": cu, "south": cu, "east": cu, "west": cu, "up": [cu[0], cu[1], cu[2], cu[1] + 4], "down": [cu[0], cu[3] - 4, cu[2], cu[3]]}

POUSSE, COEURS, EMITS, RANG, TREMBLE = {}, {}, [], {}, {}


def emit_name():
    return "emit_scintille" + (str(len(EMITS) + 1) if EMITS else "")


def core(g, B, Yp, Op, Tp, a, L0, L1):
    """Âme opaque du tronçon, de L0 à L1 le long de l'axe, tournée de 15°."""
    Xc = math.cos(math.radians(15)) * Op + math.sin(math.radians(15)) * Tp
    w = max(0.18, 0.5 * a)
    cube(g, f"{groups[g]['name']}.ame", B + Yp * (L0 + L1) / 2, (w, L1 - L0, w), Xc, Yp, CORE_F)


def prism(nm, parent, B, Yp, ref, a, Ls, Lt, rang, b_ext=EXT, e_ext=EXT, tip_emit=False, tremble=0.0):
    """Cristal hexagonal (peau trans_ + âme). Ls = longueur des faces depuis B ; Lt > 0 : pointe. Renvoie le bout de l'axe."""
    Yp = unit(Yp)
    Op, Tp = frame(Yp, ref)
    pg = group(f"pousse_{nm}", B, parent=parent)
    POUSSE[nm], RANG[nm] = pg, rang
    if tremble:
        TREMBLE[nm] = (tremble, Op, Tp)
    tg = group(f"trans_{nm}", B, parent=pg)
    s = 2 * a / math.sqrt(3)
    top = Ls if Lt > 0 else Ls + e_ext
    Lf = top + b_ext
    side = [tile_side(a, Lf, 0), tile_side(a, Lf, 1)]
    for k in range(6):
        ph = math.radians(60 * k)
        n = math.cos(ph) * Op + math.sin(ph) * Tp
        X = np.cross(Yp, n)
        c = B + Yp * (top - b_ext) / 2 + n * (a - SKIN / 2)
        cube(tg, f"{nm}.f{k}", c, (s, Lf, SKIN), X, Yp, only("south", full(side[k % 2], k >= 3)))
        if Lt > 0:
            M = B + Yp * Ls + n * a
            A = B + Yp * (Ls + Lt)
            dd = unit(A - M)
            Z = np.cross(X, dd)
            cube(tg, f"{nm}.p{k}", (M + A) / 2 - Z * SKIN / 2, (s, float(np.linalg.norm(A - M)), SKIN), X, dd,
                 only("south", full(tile_tip(a, Lt), k >= 3)))
    cg = group(f"coeur_{nm}", B, parent=pg)
    COEURS[nm] = cg
    core(cg, B, Yp, Op, Tp, a, -b_ext * 0.6, (Ls + 0.45 * Lt) if Lt > 0 else Ls + e_ext * 0.6)
    tip = B + Yp * (Ls + Lt)
    if tip_emit:
        EMITS.append(group(emit_name(), tip + Yp * 0.15, parent=pg))
    return tip


def shard(nm, parent, B, Yp, ref, a, L, emb, rang):
    """Petit éclat en pyramide hexagonale (peau trans_, âme courte), base enfoncée de emb."""
    Yp = unit(Yp)
    Op, Tp = frame(Yp, ref)
    pg = group(f"pousse_{nm}", B, parent=parent)
    POUSSE[nm], RANG[nm] = pg, rang
    tg = group(f"trans_{nm}", B, parent=pg)
    s = 2 * a / math.sqrt(3)
    A = B + Yp * L
    tl = tile_pyr(a, L, emb)
    for k in range(6):
        ph = math.radians(60 * k)
        n = math.cos(ph) * Op + math.sin(ph) * Tp
        X = np.cross(Yp, n)
        M = B + n * a
        dd = unit(A - M)
        Z = np.cross(X, dd)
        Lk = float(np.linalg.norm(A - M))
        cube(tg, f"{nm}.f{k}", (M + A) / 2 - dd * emb / 2 - Z * SKIN / 2, (s, Lk + emb, SKIN), X, dd, only("south", full(tl, k >= 3)))
    cg = group(f"coeur_{nm}", B, parent=pg)
    COEURS[nm] = cg
    cube(cg, f"{nm}.ame", B + Yp * (0.42 * L - emb) / 2, (0.2, 0.42 * L + emb, 0.2),
         math.cos(math.radians(15)) * Op + math.sin(math.radians(15)) * Tp, Yp, CORE_F)


def knot(nm, parent, J, d_in, d_out, a, rang):
    """Nœud de givre opaque à la jointure : carré de demi-côté 1,12·a (couvre la jointure), tourné de 15°, axe = bissectrice."""
    ax = unit(unit(d_in) + unit(d_out))
    Op, Tp = frame(ax, V(0, 0, -1) if abs(ax[2]) < 0.9 else X1)
    Xk = math.cos(math.radians(15)) * Op + math.sin(math.radians(15)) * Tp
    pg = group(f"pousse_{nm}", J, parent=parent)
    POUSSE[nm], RANG[nm] = pg, rang
    w = 2 * 1.12 * a
    cube(pg, nm, J, (w, 0.50, w), Xk, ax, every("noeud"))


# Ramure droite (x > 0) ; la gauche est le miroir en x, avec un andouiller d'œil plus long et un éclat de plus.
B0 = V(2.45, 33.18, -0.30)
BEAM = [  # (direction, longueur, apothème) : pivot court presque droit, puis le merrain part vers l'extérieur, monte et se referme en lyre
    (V(0.30, 1.00, 0.05), 1.30, 0.64),
    (V(1.00, 0.55, 0.15), 2.40, 0.58),
    (V(0.60, 1.00, 0.30), 2.30, 0.52),
    (V(0.05, 1.00, 0.25), 1.90, 0.46),
    (V(-0.32, 1.00, 0.12), 1.20, 0.40),
]
BEAM_TIP = 1.40
# andouillers : (nom, tronçon de départ, fraction le long du tronçon, direction, faces, pointe, apothème, rang de pousse)
TINES = [
    ("oeil", 1, 0.12, V(0.12, 1.00, -0.85), 1.50, 1.00, 0.38, 3),
    ("bez", 1, 0.78, V(0.10, 1.00, -0.40), 1.90, 1.10, 0.40, 4),
    ("trez", 2, 0.60, V(1.00, 0.90, -0.10), 1.60, 1.00, 0.36, 6),
    ("chand", 3, 0.00, V(0.90, 1.00, 0.40), 1.20, 0.90, 0.32, 7),
    ("emp1", 4, 0.00, V(0.60, 1.00, -0.30), 1.00, 0.90, 0.30, 9),
    ("emp2", 4, 0.00, V(-0.20, 1.00, 0.90), 0.90, 0.80, 0.28, 9),
]
# petits éclats de givre le long du merrain : (tronçon, fraction, direction)
GIVRE_M = [(1, 0.45, V(0.2, -0.2, 1.0)), (2, 0.30, V(0.3, 0.2, 1.0)), (3, 0.55, V(1.0, 0.2, 0.3))]
MEULE = [(math.radians(a_), tilt) for a_, tilt in ((-150, 52), (-75, 58), (0, 50), (70, 56), (145, 48))]


def M_(v, sx):
    return V(v[0] * sx, v[1], v[2])


for sx, tag in ((1, "r"), (-1, "l")):
    side_g = group(f"bois_{tag}", M_(B0, sx), parent=ROOT)
    # rosette (meule) : socle de givre opaque posé sur le crâne, éclats tout autour
    base = M_(B0, sx)
    sg = group(f"pousse_meule_{tag}", V(base[0], ROOT_Y, base[2]), parent=side_g)
    POUSSE[f"meule_{tag}"], RANG[f"meule_{tag}"] = sg, 0
    st, ss = list(UV["socle_top"]), list(UV["socle_side"])
    SH = base[1] - ROOT_Y
    # deux carrés croisés à 45° (rosette à huit pointes), le second 0,14 plus bas : aucun dessus commun
    for j, (ang, h) in enumerate(((0.26, SH), (0.26 + math.pi / 4, SH - 0.14))):
        cube(sg, f"socle{j}_{tag}", V(base[0], ROOT_Y + h / 2, base[2]), (1.62 - 0.12 * j, h, 1.62 - 0.12 * j),
             unit(V(math.cos(ang), 0, math.sin(ang))), Y1, {"north": ss, "south": ss, "east": ss, "west": ss, "up": st, "down": ss})
    for i, (ang, tilt) in enumerate(MEULE):
        o = V(math.cos(ang) * sx, 0, math.sin(ang))
        d = rodrigues(np.cross(Y1, o), math.radians(tilt)) @ Y1
        shard(f"givre{i}_{tag}", side_g, base + o * 0.62 + V(0, -0.05, 0), d, o, 0.20 + 0.03 * (i % 2), 0.62 + 0.12 * (i % 3), 0.18, 1)
    # merrain : tronçons + nœuds
    P = base.copy()
    joints = [P.copy()]
    dirs = []
    for k, (d, L, a) in enumerate(BEAM):
        dd = unit(M_(d, sx))
        dirs.append(dd)
        last = k == len(BEAM) - 1
        ref = V(0, 0, -1)
        P = prism(f"m{k}_{tag}", side_g, P, dd, ref, a, L, BEAM_TIP if last else 0.0, 1 + 2 * k,
                  b_ext=0.30 if k == 0 else EXT, tip_emit=last)
        joints.append(P if not last else joints[-1] + dd * L)
        if not last:
            knot(f"noeud{k}_{tag}", side_g, P, dd, unit(M_(BEAM[k + 1][0], sx)), BEAM[k][2], 2 + 2 * k)
    # andouillers
    for nm, k, f, d, Ls, Lt, a, rang in TINES:
        if tag == "l" and nm == "oeil":
            Ls, Lt = Ls + 0.35, Lt + 0.15
        dd = unit(M_(d, sx))
        J = joints[k] + dirs[k] * BEAM[k][1] * f
        tip_emit = nm in ("bez", "trez", "emp1") if tag == "r" else nm in ("oeil", "trez", "emp2")
        prism(f"{nm}_{tag}", side_g, J + dd * 0.05, dd, dirs[k], a, Ls, Lt, rang, b_ext=0.35, tip_emit=tip_emit, tremble=1.0 if nm != "oeil" else 0.7)
    for i, (k, f, d) in enumerate(GIVRE_M):
        J = joints[k] + dirs[k] * BEAM[k][1] * f
        dd = unit(M_(d, sx))
        shard(f"givrem{i}_{tag}", side_g, J + dd * (BEAM[k][2] - 0.1), dd, dirs[k], 0.2, 0.7, 0.2, 3 + 2 * k)
    if tag == "l":
        # éclat de plus sur l'andouiller d'œil gauche (asymétrie du renne)
        _n, k0, f0, d0, Ls0 = TINES[0][:5]
        J = joints[k0] + dirs[k0] * BEAM[k0][1] * f0 + unit(M_(d0, sx)) * 1.1
        shard(f"eclat_oeil_{tag}", side_g, J, unit(M_(V(-0.1, 1, -0.4), sx)), dirs[0], 0.17, 0.62, 0.22, 3)

# particule modélisée : petite étoile, à la racine (jamais portée)
PART = group("particle_scintille", [0, 0, 0])
cube(PART, "scintille", V(0, 0.65, 0), (0.7, 0.7, 0.3), X1, Y1, only("south", full("spark")))

# contrôles de distance : rien sous le dessus du crâne (32,62), rien devant le visage
ymin = min(p[1] for _, p in CORNERS)
zmin = min(p[2] for _, p in CORNERS)
assert ymin >= 32.62, f"trop bas : {ymin:.3f} ({min(CORNERS, key=lambda c: c[1][1])[0]})"
assert zmin >= -2.9, f"trop en avant : {zmin:.3f} ({min(CORNERS, key=lambda c: c[1][2])[0]})"
EXT_MAX = max(float(np.max(np.abs(p))) for _, p in CORNERS)

# textures
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


def bone(name):
    g = groups[name]
    return {"name": g["name"], "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "head", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone(ROOT)]}, bone(PART)]


# ------------------------------------------------------------------ animations
# Guide, section 3 : +X = le haut part vers l'arrière ; +Z = le côté droit monte (le haut part vers -X).
# Basculer le haut d'un groupe d'un angle t vers la direction horizontale o : rotation (t·o_z, 0, -t·o_x).
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


def anim(name, length, animators, loop="loop"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "idle", "animators": animators}


def tremble_state(name, length, amp, n_kf):
    """Andouillers rigides qui vibrent autour de leur base : amp(t, rang, i) en degrés, deux axes déphasés.
    Les tronçons du merrain ne bougent pas (la glace ne plie pas)."""
    times = [i * length / n_kf for i in range(n_kf + 1)]
    A = {}
    for i, (nm, (k, Op, Tp)) in enumerate(sorted(TREMBLE.items())):
        g = POUSSE[nm]
        r = RANG[nm]
        kfs = []
        for t in times:
            w0, w1 = amp(t, r, i)
            w0, w1 = w0 * k, w1 * k
            # vibration : le bout oscille dans la direction Op puis Tp (composantes horizontales)
            ox, oz = Op[0] * w0 + Tp[0] * w1, Op[2] * w0 + Tp[2] * w1
            kfs.append(kf(t, oz, 0, -ox))
        A[groups[g]["uuid"]] = {"name": groups[g]["name"], "type": "bone", "keyframes": kfs}
    return anim(name, length, A)


def vib(T, a, ph=0.9):
    return lambda t, r, i: (a * math.sin(TAU * t / T - r * ph - i * 0.7), 0.6 * a * math.cos(TAU * t / T - r * ph - i * 1.3))


# idle 8 s : un frisson de givre monte de la base aux pointes vers 5 s (tremblement amorti), sinon immobile
def idle_amp(t, r, i):
    t0 = 4.8 + 0.08 * r
    env = sm(t, t0, t0 + 0.08) * (1 - sm(t, t0 + 0.1, t0 + 0.9))
    return (1.1 * env * math.sin(TAU * (t - t0) * 7), 0.7 * env * math.cos(TAU * (t - t0) * 7 + i))


idle = tremble_state("idle", 8.0, idle_amp, 128)
walk = tremble_state("walk", 1.6, vib(0.8, 0.35), 24)          # un petit choc par pas
run = tremble_state("run", 1.0, vib(0.5, 0.7), 16)
fly = tremble_state("fly", 2.4, vib(0.6, 0.4), 32)             # le vent fait chanter les pointes
glide = tremble_state("glide", 3.6, vib(0.6, 0.55), 48)

# overlay_scintille (6 s, par-dessus tous les états) : les âmes battent l'une après l'autre, de la base vers les pointes
OV = 6.0
ov_t = [i * OV / 24 for i in range(25)]
ov_a = {}
for nm, cg in COEURS.items():
    ph = TAU * (RANG[nm] / 9.0)
    ov_a[groups[cg]["uuid"]] = {"name": groups[cg]["name"], "type": "bone",
                                "keyframes": [kf(t, *(1 + 0.07 * math.sin(TAU * t / OV * 2 - ph),) * 3, ch="scale") for t in ov_t]}
ov_a[groups[CTRL]["uuid"]] = {"name": "ctrl_lumiere", "type": "bone", "keyframes": [kf(t, 0.15 * math.sin(TAU * t / OV), 0, 0, ch="position") for t in ov_t]}
overlay = anim("overlay_scintille", OV, ov_a)

# event_equip (1,6 s) : la ramure pousse depuis le crâne, rang par rang (échelle uniforme depuis la base, léger dépassement)
EQ = 1.6
eq_t = [i * EQ / 48 for i in range(49)]
eq_a = {}
for nm, g in POUSSE.items():
    t0 = 0.04 + 0.12 * RANG[nm]
    sc = lambda t, t0=t0: max(0.0, sm(t, t0, t0 + 0.26) * (1 + 0.1 * bump(t, t0 + 0.16, t0 + 0.26, t0 + 0.3, t0 + 0.5)))
    eq_a[groups[g]["uuid"]] = {"name": groups[g]["name"], "type": "bone", "keyframes": [kf(t, *(sc(t),) * 3, ch="scale") for t in eq_t]}
lum = lambda t: -1 + sm(t, 0.2, 1.3) * 1.5 - 0.5 * sm(t, 1.3, 1.6)
eq_a[groups[CTRL]["uuid"]] = {"name": "ctrl_lumiere", "type": "bone", "keyframes": [kf(t, lum(t), 0, 0, ch="position") for t in eq_t]}
eq_a["effects"] = {"name": "Effects", "type": "effect", "keyframes": [{"channel": "sound", "data_points": [{"effect": "block.amethyst_cluster.place", "file": ""}], "time": 0.1}]}
equip = anim("event_equip", EQ, eq_a, loop="once")

# particule : l'étoile pulse et se balance pendant qu'elle flotte (boucle fermée)
PF = 1.0
pf_t = [i * PF / 8 for i in range(9)]
p_fall = anim("particle_scintille_fall", PF, {groups[PART]["uuid"]: {"name": "particle_scintille", "type": "bone",
              "keyframes": [kf(t, 0, 0, 20 * math.sin(TAU * t / PF)) for t in pf_t] +
                           [kf(t, *(1 + 0.25 * math.sin(TAU * t / PF * 2),) * 3, ch="scale") for t in pf_t]}})

ANIMS = [idle, walk, run, fly, glide, overlay, equip, p_fall]
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
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUTF) // 1024, "Ko ;",
      len(EMITS), "emit_ ; y min", round(ymin, 3), "; z min", round(zmin, 3), "; extension", round(EXT_MAX, 2))
