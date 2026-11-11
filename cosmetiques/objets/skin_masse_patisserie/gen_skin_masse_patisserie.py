"""Fouet chantilly : skin d'objet (guide 14) pour toutes les masses du joueur, ensemble Pâtisserie (thème Mignon). Design original.
Écrit skin_masse_patisserie.png, skin_masse_patisserie_e.png et .build/skin_masse_patisserie_brut.bbmodel à côté de ce script.

Un fouet ballon de pâtissier géant (référence : `.claude/references/objets/ustensiles-patisserie.md`) :
- manche en hêtre verni (grain, filet de vernis, farine aux doigts), embout et anneau d'accroche en silicone fraise ;
- virole crème-laiton à deux gorges, d'où partent 4 boucles = 8 brins gainés de silicone rouge fraise, en ballon (plus large
  aux deux tiers, comme la tête de la masse vanilla) qui se croisent au bout ;
- dans la cage, une grosse boule de chantilly vanille à filets de coulis, qui gonfle entre les brins, crème en nuage festonné
  qui dépasse entre les fils, une fraise entière nappée prise dans la crème (reflet net : seule source du calque _e).
Repère : construit le long de l'axe a (+X local), posé sur la diagonale du bloc (tête en haut à droite vue de +Z, comme mace.png),
centré dans le bloc. Display = item/handheld_mace du jar (3e personne échelle 1, 1re personne 0,9 ; tools/objet.py donne encore
item/handheld à la masse), gui réduit pour la case. Une seule étape : `repos`.
La crème (et la fraise) est construite dans un repère non tourné puis posée par la rotation de son groupe (Z = 45°) : le
squash-and-stretch se fait alors le long de l'axe du fouet.

Objet vivant (guide 14), format free :
- item_idle (6 s) : la chantilly respire à peine (étirement ±2 % à volume constant), la fraise frissonne ; ctrl_emit à −1 ;
- event_select (0,8 s) : « plop » : la crème sort de rien dans la cage (0 → 1,22 → 0,92 → 1), la fraise tombe dedans ensuite ;
- event_swing (0,4 s) : la crème prend du retard sur le geste (rotation dans le plan) puis revient, la cage vibre ;
- event_hit (0,7 s) : la crème s'écrase puis rebondit, nuage de farine (`emit_mc_poof`) et sucre glace qui monte
  (`particle_sucre`, 3 points `emit_sucre`), cadence par `ctrl_emit` ; **le seul son** : block.powder_snow.break.
Pas d'item_gui (figé dans l'inventaire), item_ground repli sur item_idle.
Fonctions avancées : calque _e (reflet de la fraise), particule modélisée `particle_sucre`, `emit_mc_poof`, `ctrl_emit`,
animations d'objet. Non simulés par l'aperçu : animations d'objet, particules, ctrl_emit (à juger en jeu, `/cosmetique apercu`).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

NOM = "skin_masse_patisserie"
TEX = 512
TAU = 2 * math.pi
RNG = np.random.default_rng(11)

# ------------------------------------------------------------------ dimensions (px, le long de l'axe a)
A_ANNEAU = -1.55        # bout de l'anneau d'accroche
A_VIR0, A_VIR1 = 9.0, 10.8      # virole
A_TIP = 22.9            # bout de la cage
RMAX = 3.5              # rayon du ballon
RW = 0.3                # demi-épaisseur d'un brin
N_BRINS = 8
A_CREME = 17.7          # centre de la chantilly


def lerp(a, b, k):
    return a + (b - a) * k


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def r_ballon(a):
    """Rayon de la cage : part de la virole à 0,55, plus large aux deux tiers, se referme au bout."""
    s = min(max((a - A_VIR1) / (A_TIP - A_VIR1), 0.0), 1.0)
    return 0.55 * (1 - s) ** 2 + RMAX * max(0.0, math.sin(math.pi * s ** 1.6)) ** 0.8


# ------------------------------------------------------------------ peinture
def bruit(shape, cells, seed):
    r = np.random.default_rng(seed).random((cells, cells)).astype(np.float32)
    return np.array(Image.fromarray((r * 255).astype(np.uint8)).resize(shape[::-1], Image.BICUBIC), np.float32) / 255


def C(*c):
    return np.array(c, np.float32)


def fini(c, al=None):
    rgb = np.clip(c, 0, 255).astype(np.uint8)
    a = np.full(rgb.shape[:2], 255, np.uint8) if al is None else al
    return np.dstack([rgb, a])


def p_bois(W=160, H=20):
    """Hêtre verni : ombre aux bords (cylindre), filet de vernis net, grain long, farine éparse."""
    jj, ii = np.mgrid[0:H, 0:W].astype(np.float32)
    v = (jj + 0.5) / H
    c = np.empty((H, W, 3), np.float32)
    c[...] = C(228, 152, 64)
    cyl = np.abs(v - 0.42) / 0.58
    c = lerp(c, C(138, 70, 24), (np.clip(cyl - 0.35, 0, 1) * 1.3)[..., None].clip(0, 1))
    grain = np.sin(ii / W * 38 + 9 * bruit((H, W), 6, 3) + v * 5)
    c = lerp(c, C(170, 92, 34), (np.clip(grain - 0.55, 0, 1) * 1.4)[..., None].clip(0, 1) * 0.7)
    c = lerp(c, C(246, 200, 120), (np.clip(1 - np.abs(v - 0.3) / 0.09, 0, 1))[..., None] * 0.85)
    c = lerp(c, C(255, 246, 222), (np.abs(v - 0.3) < 0.035)[..., None] * 0.9)
    n = RNG.random((H, W))
    c = lerp(c, C(255, 250, 240), ((n > 0.965) & (v > 0.15) & (v < 0.75))[..., None] * 0.9)
    return fini(c)


def p_silicone(W=96, H=10):
    """Silicone fraise : rouge franc, reflet blanc net, ombre framboise (jamais noire)."""
    jj = (np.mgrid[0:H, 0:W][0].astype(np.float32) + 0.5) / H
    c = np.empty((H, W, 3), np.float32)
    c[...] = C(222, 30, 52)
    c = lerp(c, C(132, 8, 34), (np.clip((jj - 0.55) / 0.45, 0, 1))[..., None])
    c = lerp(c, C(255, 120, 140), (np.clip(1 - np.abs(jj - 0.25) / 0.14, 0, 1))[..., None] * 0.8)
    c = lerp(c, C(255, 220, 228), (np.abs(jj - 0.22) < 0.05)[..., None] * 0.85)
    return fini(c)


def p_laiton(W=64, H=16):
    """Virole crème-laiton (vanille dorée) à deux gorges."""
    jj, ii = np.mgrid[0:H, 0:W].astype(np.float32)
    v, u = (jj + 0.5) / H, (ii + 0.5) / W
    c = np.empty((H, W, 3), np.float32)
    c[...] = C(252, 206, 104)
    c = lerp(c, C(176, 112, 36), (np.clip((v - 0.5) / 0.5, 0, 1))[..., None])
    c = lerp(c, C(255, 246, 210), (np.clip(1 - np.abs(v - 0.27) / 0.12, 0, 1))[..., None])
    for g in (0.3, 0.68):
        c = lerp(c, C(150, 92, 30), (np.abs(u - g) < 0.035)[..., None] * 0.9)
        c = lerp(c, C(255, 240, 200), (np.abs(u - g - 0.06) < 0.025)[..., None] * 0.8)
    return fini(c)


def p_creme(W=96, H=96, coulis=False, seed=5):
    """Chantilly vanille pochée : cannelures en biais (dessus éclairé, creux colorés), points de vanille, sucre glace,
    filets de coulis fraise (coulis=True)."""
    jj, ii = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = (ii + 0.5) / W, (jj + 0.5) / H
    c = np.empty((H, W, 3), np.float32)
    c[...] = C(255, 238, 196)
    n = bruit((H, W), 5, seed)
    stri = np.sin((u * 1.0 + v * 0.4) * TAU * 1.6 + 1.6 * n)
    c = lerp(c, C(246, 210, 166), (np.clip(-stri - 0.2, 0, 1) * 0.8)[..., None].clip(0, 1))
    c = lerp(c, C(255, 250, 236), (np.clip(stri - 0.3, 0, 1) * 1.4)[..., None].clip(0, 1))
    c = lerp(c, C(240, 190, 140), (np.clip((v - 0.75) / 0.25, 0, 1) * 0.45)[..., None])
    r = np.random.default_rng(seed)
    for _ in range(int(W * H / 520)):
        x, y = int(r.integers(1, W - 2)), int(r.integers(1, H - 2))
        c[y:y + 2, x:x + 2] = C(120, 72, 40) if r.random() < 0.5 else C(255, 255, 255)
    if coulis:
        for k in range(2):
            ph = r.random() * TAU
            yy = (0.3 + 0.38 * k) * H + 0.09 * H * np.sin(u * TAU * 1.3 + ph) + 2.5 * np.sin(u * TAU * 4 + ph)
            d = np.abs(jj - yy)
            c = lerp(c, C(150, 10, 36), (d < 3.6)[..., None])
            c = lerp(c, C(214, 40, 78), (d < 2.6)[..., None])
            c = lerp(c, C(255, 170, 190), ((jj - yy > -2.4) & (jj - yy < -1.2))[..., None] * 0.9)
    return fini(c)


def p_fraise(W=64, H=64):
    """Peau de fraise nappée : rouge à ombre framboise, graines jaunes en quinconce dans un petit creux, reflet fenêtre."""
    jj, ii = np.mgrid[0:H, 0:W].astype(np.float32)
    v = (jj + 0.5) / H
    c = np.empty((H, W, 3), np.float32)
    c[...] = C(222, 30, 52)
    c = lerp(c, C(120, 6, 28), (np.clip((v - 0.5) / 0.5, 0, 1) * 0.8)[..., None])
    c = lerp(c, C(255, 120, 140), (np.clip((0.3 - v) / 0.3, 0, 1) * 0.6)[..., None])
    for row in range(4):
        for col in range(4):
            x = int((col + 0.5 + 0.5 * (row % 2)) / 4.5 * W)
            y = int((row + 0.5) / 4 * H)
            c[y - 2:y + 1, x - 2:x + 2] = C(176, 16, 40)
            c[y - 1:y + 1, x - 1:x + 1] = C(255, 214, 84)
    e = np.zeros((H, W, 4), np.uint8)
    win = (ii > W * 0.18) & (ii < W * 0.34) & (jj > H * 0.14) & (jj < H * 0.3)
    dot = (np.hypot(ii - W * 0.42, jj - H * 0.22) < W * 0.04)
    c[win | dot] = C(255, 248, 250)
    e[win | dot] = (210, 180, 190, 255)
    return fini(c), e


def p_fraise_plaque(W=88, H=72):
    """Fraise entière de profil (u = de la collerette à la pointe) : épaules rondes, pointe arrondie, graines, reflet de nappage,
    sépales verts qui débordent à la base. Contour par l'alpha (sur-échantillonné puis seuil)."""
    ss = 3
    GW, GH = W * ss, H * ss
    jj, ii = np.mgrid[0:GH, 0:GW].astype(np.float32)
    u, y = (ii + 0.5) / GW, ((jj + 0.5) / GH - 0.5) * 2
    prof = (1 - u) ** 0.6 * np.clip((u + 0.04) / 0.26, 0, 1) ** 0.45
    corps = np.abs(y) < prof * 0.92 + 0.02
    sep = np.zeros_like(corps)
    for k, (yy, ln) in enumerate(((-0.75, 0.2), (-0.35, 0.26), (0.05, 0.28), (0.45, 0.24), (0.8, 0.18))):
        d = ((u - ln * 0.5) / (ln * 0.55)) ** 2 + ((y - yy * (1 - u / ln * 0.3)) / 0.2) ** 2
        sep |= d < 1
    c = np.empty((GH, GW, 3), np.float32)
    c[...] = C(222, 30, 52)
    c = lerp(c, C(128, 8, 30), (np.clip((y - 0.15) / 0.85, 0, 1) * 0.75)[..., None])
    c = lerp(c, C(255, 110, 130), (np.clip((-y - 0.25) / 0.6, 0, 1) * 0.55)[..., None])
    for row in range(5):
        for col in range(6):
            cu = 0.16 + col * 0.14 + 0.07 * (row % 2)
            cy = -0.8 + row * 0.4
            if abs(cy) > (1 - cu) ** 0.6 * 0.8:
                continue
            m = (np.abs(u - cu) < 0.018) & (np.abs(y - cy) < 0.05)
            c[m] = C(255, 214, 84)
            c[(np.abs(u - cu) < 0.03) & (np.abs(y - cy - 0.06) < 0.03) & ~m] = C(170, 14, 38)
    win = (np.abs(u - 0.4) < 0.11) & (np.abs(y + 0.45) < 0.11)
    dot = np.hypot((u - 0.56) / 0.035, (y + 0.42) / 0.06) < 1
    c[win | dot] = C(255, 248, 250)
    sepc = lerp(C(60, 140, 50), C(150, 214, 96), np.clip(1 - u / 0.2, 0, 1)[..., None])
    c = np.where(sep[..., None], sepc, c)
    al = corps | sep
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    a = np.array(Image.fromarray((al * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    out = np.dstack([rgb, a * 255]).astype(np.uint8)
    out[~a, :3] = (200, 30, 50)
    e = np.zeros((H, W, 4), np.uint8)
    g = np.array(Image.fromarray(((win | dot) & corps).astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 120
    e[g & a] = (215, 190, 200, 255)
    return out, e


def p_sepale(W=32, H=16):
    v = (np.mgrid[0:H, 0:W][0].astype(np.float32) + 0.5) / H
    c = np.empty((H, W, 3), np.float32)
    c[...] = C(96, 176, 64)
    c = lerp(c, C(36, 104, 40), (np.clip((v - 0.5) * 2, 0, 1))[..., None])
    c = lerp(c, C(170, 226, 110), (np.abs(v - 0.25) < 0.1)[..., None])
    return fini(c)


NU_A0, NU_A1 = A_VIR1 + 0.7, A_TIP - 0.35     # étendue de la plaque de chantilly le long de l'axe
NU_H = RMAX + 0.55                            # demi-hauteur de la plaque


def p_nuage(W=128, H=96, seed=3, coulis=True):
    """Plaque de chantilly (u le long de l'axe, v à travers) : contour en nuage festonné qui suit le ballon (rayon des fils
    + 0,25 px, festons de 0,45 px), dessus clair, creux de cannelures, ombre colorée vers les bords, filet de coulis."""
    ss = 3
    GW, GH = W * ss, H * ss
    jj, ii = np.mgrid[0:GH, 0:GW].astype(np.float32)
    a = NU_A0 + (ii + 0.5) / GW * (NU_A1 - NU_A0)
    y = ((jj + 0.5) / GH - 0.5) * 2 * NU_H
    rb_ = np.vectorize(r_ballon)(a[0]).astype(np.float32)[None, :]
    r = np.random.default_rng(seed)
    ph = r.random(3) * TAU
    feston = 0.28 * np.abs(np.sin((a - NU_A0) * 2.1 + ph[0] + (y > 0) * 1.3)) + 0.08 * np.sin(a * 5.3 + ph[1])
    bord = np.clip(rb_ + 0.05 + feston - 0.35 * np.clip((NU_A0 + 1.2 - a) / 1.2, 0, 1), 0, None)
    al = np.abs(y) < bord
    t = np.clip(np.abs(y) / np.maximum(bord, 0.2), 0, 1)
    c = np.empty((GH, GW, 3), np.float32)
    c[...] = C(255, 240, 200)
    c = lerp(c, C(238, 178, 112), (np.clip((t - 0.6) / 0.4, 0, 1) * 0.75)[..., None])
    c = lerp(c, C(255, 250, 232), (np.clip(1 - np.abs(y + 0.35 * bord) / (0.3 * np.maximum(bord, 0.3)), 0, 1) * 0.8)[..., None])
    sw = np.sin((a * 1.6 + np.abs(y) * 1.1) * 2.2 + ph[2])
    c = lerp(c, C(244, 196, 136), (np.clip(sw - 0.6, 0, 1) * 1.6)[..., None].clip(0, 1) * 0.7)
    if coulis:
        yy = -0.15 * bord + 0.35 * np.sin(a * 1.4 + ph[0])
        d = np.abs(y - yy)
        c = lerp(c, C(150, 10, 36), (d < 0.24)[..., None])
        c = lerp(c, C(214, 40, 78), (d < 0.17)[..., None])
        c = lerp(c, C(255, 170, 190), ((y - yy > -0.16) & (y - yy < -0.08))[..., None] * 0.9)
    for _ in range(int(W * H / 420)):
        x0, y0 = int(r.integers(2, GW - 6)), int(r.integers(2, GH - 6))
        c[y0:y0 + 3, x0:x0 + 3] = C(140, 84, 44) if r.random() < 0.3 else C(255, 255, 255)
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    m = np.array(Image.fromarray((al * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    out = np.dstack([rgb, m * 255]).astype(np.uint8)
    out[~m, :3] = (250, 236, 210)
    return out


def p_sucre(W=8, H=8):
    c = np.empty((H, W, 3), np.float32)
    c[...] = C(255, 252, 246)
    c[H // 2:, :] = C(240, 226, 236)
    return fini(c)


UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def atlas():
    fr, fre = p_fraise()
    items = [("bois", p_bois(), None), ("silicone", p_silicone(), None), ("laiton", p_laiton(), None),
             ("creme", p_creme(), None), ("coulis", p_creme(coulis=True, seed=9), None), ("creme2", p_creme(seed=13), None), ("nuage", p_nuage(), None), ("nuage2", p_nuage(seed=8, coulis=False), None),
             ("fraise", fr, None), ("fraise_plaque",) + p_fraise_plaque(), ("sepale", p_sepale(), None), ("sucre", p_sucre(), None)]
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, im, ime in sorted(items, key=lambda it: -it[1].shape[0]):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, "atlas plein"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None:
            tex_e[y:y + h, x:x + w] = ime
        x += w + 1
        shelf = max(shelf, h)
    tex[..., :3] &= 0xFC
    assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
    res = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        res.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return res


tex_b64, tex_e_b64 = atlas()

# ------------------------------------------------------------------ géométrie
elements, groups, EFF = [], {}, []        # EFF : coins effectifs (monde), pour la boîte


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


def euler(R):
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def rmat(rx, ry, rz):
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def rot_axe(axe, ang):
    """Rotation d'angle ang (rad) autour d'un axe unitaire (Rodrigues)."""
    k = unit(np.asarray(axe, float))
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K


THETA = math.radians(45)
RZ = rmat(0, 0, 45)
P0 = V(0, 0, 0)          # translation du repère local (a, b, c) vers le bloc, réglée après une première passe


def W(p):
    return RZ @ np.asarray(p, float) + P0


def group(name, origin_local, parent=None, nom=None, repere="monde", rotation=(0, 0, 0)):
    assert name not in groups
    groups[name] = {"origin": [round(float(v), 3) for v in W(origin_local)], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": list(rotation), "nom": nom or name, "repere": repere, "o_local": np.asarray(origin_local, float)}
    return name


def faces_de(tile, caps=True):
    u0, v0, u1, v1 = UV[tile]
    lg = [u0, v0, u1, v1]
    end = [u0, v0, min(u0 + (v1 - v0), u1), v1] if caps else CLEAR
    return {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end}


def boite(g, name, c, R, h, tile, caps=True, faces=None):
    """Cube de centre c (local), axes R (colonnes, local), demi-tailles h. Dans un groupe au repère « tourne », les cubes
    sont écrits sans la rotation du bloc : la rotation du groupe (Z = 45°) les pose."""
    c, h = np.asarray(c, float), np.asarray(h, float)
    rep = groups[g]["repere"]
    if rep == "monde":
        cw, Rw = W(c), RZ @ R
    else:
        piv = groups[rep]["o_local"]
        cw, Rw = W(piv) + (c - piv), R
    f = faces or faces_de(tile, caps)
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in cw - h], "to": [round(float(v), 3) for v in cw + h],
         "origin": [round(float(v), 3) for v in cw], "box_uv": False,
         "faces": {k: {"uv": [round(float(x), 2) for x in uv], "texture": 0} for k, uv in f.items()}}
    rot = euler(Rw)
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])
    Reff = RZ @ R
    for i in range(8):
        s = np.array([(-1, 1)[(i >> k) & 1] for k in range(3)], float)
        EFF.append(W(c) + Reff @ (s * h))


def barre(g, name, p, q, r, tile, ref=None, octo=True, ov=0.08, caps=True, tourne=0.0):
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = V(0, 0, 1) if ref is None else np.asarray(ref, float)
    if abs(ref @ X) > 0.95:
        ref = V(0, 1, 0)
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    R0 = np.column_stack([X, Y, Z_]) @ rmat(math.degrees(tourne), 0, 0)
    L = np.linalg.norm(q - p)
    c = (p + q) / 2
    boite(g, name, c, R0, (L / 2 + ov, r, r), tile, caps)
    if octo:
        boite(g, name + "o", c, R0 @ rmat(45, 0, 0), (L / 2 + ov - 0.1, r * 0.97, r * 0.97), tile, caps)


def radial(phi):
    return V(0, math.cos(phi), math.sin(phi))


def build():
    elements.clear(), groups.clear(), EFF.clear()
    racine = group("repos", V(8, 0, 0), nom=objet.etape("repos", "masse"))
    manche = group("manche", V(A_VIR1, 0, 0), parent=racine)
    # anneau d'accroche (silicone) : carré arrondi dans le plan (a, b)
    ra, rr = 0.85, 0.3
    ac = V(A_ANNEAU + ra + rr, 0, 0)
    pts = [ac + V(math.cos(k / 8 * TAU) * ra, math.sin(k / 8 * TAU) * ra, 0) for k in range(8)]
    for k in range(8):
        barre(manche, f"anneau{k}", pts[k], pts[(k + 1) % 8], rr, "silicone", ref=V(0, 0, 1), octo=False, ov=0.12)
    # embout de silicone, puis manche de bois au profil tourné
    barre(manche, "embout", V(0.05, 0, 0), V(1.25, 0, 0), 1.12, "silicone")
    barre(manche, "embout_bord", V(1.15, 0, 0), V(1.45, 0, 0), 1.2, "silicone", ov=0.0)
    prof = [(1.3, 0.96), (3.6, 0.84), (6.4, 0.86), (9.15, 0.98)]
    for k in range(len(prof) - 1):
        (a0, r0), (a1, r1) = prof[k], prof[k + 1]
        barre(manche, f"bois{k}", V(a0, 0, 0), V(a1, 0, 0), (r0 + r1) / 2, "bois", ov=0.06)
    # virole crème-laiton
    vir = [(A_VIR0 - 0.1, 1.06), (A_VIR0 + 0.7, 1.0), (A_VIR0 + 1.3, 0.86), (A_VIR1, 0.66)]
    for k in range(len(vir) - 1):
        (a0, r0), (a1, r1) = vir[k], vir[k + 1]
        barre(manche, f"virole{k}", V(a0, 0, 0), V(a1, 0, 0), (r0 + r1) / 2 + 0.04, "laiton", ov=0.04)
    barre(manche, "virole_bague", V(A_VIR0 + 0.25, 0, 0), V(A_VIR0 + 0.55, 0, 0), 1.16, "laiton", ov=0.0)

    # cage : 8 brins gainés de silicone (4 boucles qui se croisent au bout)
    cage = group("cage", V(A_VIR1, 0, 0), parent=racine)
    NS = 13
    aa = [lerp(A_VIR1 - 0.25, A_TIP, (k / NS) ** 0.92) for k in range(NS + 1)]
    for j in range(N_BRINS):
        phi = j / N_BRINS * TAU
        u = radial(phi)
        P = [V(a, 0, 0) + u * max(r_ballon(a), 0.12 + 0.02 * j) for a in aa]
        for k in range(NS):
            barre(cage, f"brin{j}_{k}", P[k], P[k + 1], RW, "silicone", ref=u, octo=False, ov=0.1)
    barre(cage, "noeud", V(A_TIP - 0.45, 0, 0), V(A_TIP + 0.15, 0, 0), 0.42, "silicone", ov=0.0)

    # chantilly (repère tourné : son groupe porte la rotation du bloc)
    creme = group("creme", V(A_CREME, 0, 0), parent=cage, rotation=(0, 0, 45))
    groups[creme]["repere"] = creme
    cc = V(A_CREME, 0, 0)
    tw = rmat(22.5, 0, 0)
    # chantilly : 4 plaques croisées autour de l'axe (silhouette de nuage festonné qui suit le ballon et dépasse un peu entre
    # les fils : plaques à 22,5° + k·45°, entre les brins) + une âme en deux pelures octogonales qui remplit le volume
    for k, h in enumerate((1.5, 2.25, 2.75)):
        aa_ = [a for a in np.linspace(A_VIR1 + 0.5, A_TIP - 0.4, 200) if r_ballon(a) >= h + 0.6]
        a0, a1 = max(min(aa_), A_VIR1 + 1.8), min(max(aa_), A_TIP - 1.2)
        c = V((a0 + a1) / 2, 0, 0)
        boite(creme, f"ame{k}", c, rmat(22.5, 0, 0), ((a1 - a0) / 2, h, h), ("creme", "creme2", "coulis")[k])
        boite(creme, f"ame{k}o", c, rmat(67.5, 0, 0), ((a1 - a0) / 2 - 0.05, h * 0.985, h * 0.985), ("creme2", "coulis", "creme")[k])
    pu0, pv0, pu1, pv1 = UV["nuage"]
    qu0, qv0, qu1, qv1 = UV["nuage2"]
    cc = V((NU_A0 + NU_A1) / 2, 0, 0)
    for k in range(4):
        rx = 22.5 + 45 * k
        t = (pu0, pv0, pu1, pv1) if k % 2 == 0 else (qu0, qv0, qu1, qv1)
        boite(creme, f"nuage{k}", cc + radial(math.radians(rx + 90)) * (0.04 * (k - 1.5)), rmat(rx, 0, 0),
              ((NU_A1 - NU_A0) / 2, NU_H, 0.15), "creme",
              faces={"south": [t[0], t[1], t[2], t[3]], "north": [t[2], t[1], t[0], t[3]], "east": CLEAR, "west": CLEAR,
                     "up": CLEAR, "down": CLEAR})

    # fraise entière nappée, prise dans la crème, côté vue (+Z) entre deux brins
    phi_f = 2.5 / N_BRINS * TAU
    uf = radial(phi_f)
    fb = V(A_CREME - 1.9, 0, 0) + uf * 2.5
    fd = unit(uf * 0.5 + V(1, 0, 0))
    fraise = group("fraise", fb, parent=creme)
    groups[fraise]["repere"] = creme
    Yf = unit(V(1, 0, 0) - (V(1, 0, 0) @ fd) * fd)
    Rf = np.column_stack([fd, Yf, np.cross(fd, Yf)])
    LF, WF = 5.0, 4.3                     # silhouette de la fraise (plaques croisées), âme en gradins à l'intérieur
    u0, v0, u1, v1 = UV["fraise_plaque"]
    for k, rx in enumerate((0, 90)):
        Rp = Rf @ rmat(rx, 0, 0)
        boite(fraise, f"fraise_plaque{k}", fb + fd * (LF / 2 - 0.25), Rp, (LF / 2, WF / 2, 0.15), "fraise",
              faces={"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
    off = 0.0
    for k, (l, w) in enumerate(((0.65, 1.0), (0.62, 0.9), (0.52, 0.65), (0.4, 0.36))):
        c = fb + fd * (off + l)
        boite(fraise, f"fraise{k}", c, Rf @ rmat(22.5, 0, 0), (l, w, w), "fraise")
        boite(fraise, f"fraise{k}o", c, Rf @ rmat(67.5, 0, 0), (l - 0.04, w * 0.97, w * 0.97), "fraise")
        off += 2 * l * 0.92
    boite(fraise, "queue", fb - fd * 0.35, Rf, (0.35, 0.13, 0.13), "sepale")

    # points de départ des particules (dans la cage, sans rotation de groupe : +Y du groupe = vers le haut du bloc)
    em = group("emit_mc_poof", V(A_CREME + 2.4, 0, 1.4), parent=cage)
    group("ctrl_emit@1", V(A_CREME + 2.4, 0, 1.4), parent=em, nom="ctrl_emit")
    for k, (da, ph) in enumerate(((0.0, 0.6), (2.6, 2.2), (-1.8, 4.1))):
        nm = "emit_sucre" if k == 0 else f"emit_sucre{k + 1}"
        p = V(A_CREME + da, 0, 0) + radial(ph) * 3.2
        e_ = group(nm, p, parent=cage)
        group(f"ctrl_emit@{k + 2}", p, parent=e_, nom="ctrl_emit")
    return {"racine": racine, "manche": manche, "cage": cage, "creme": creme, "fraise": fraise,
            "ctrl": ["ctrl_emit@1", "ctrl_emit@2", "ctrl_emit@3", "ctrl_emit@4"]}


def particule():
    """particle_sucre : un grain de sucre glace (0,5 px), une face par côté ; pivot dessous."""
    g = "particle_sucre"
    groups[g] = {"origin": [8, 1.0, 8], "uuid": nuid(), "ids": [], "parent": None, "rotation": [0, 0, 0], "nom": g, "repere": "monde",
                 "o_local": None}
    u0, v0, u1, v1 = UV["sucre"]
    f = {k: {"uv": [u0, v0, u1, v1], "texture": 0} for k in ("north", "south", "east", "west", "up", "down")}
    e = {"name": "grain", "type": "cube", "uuid": nuid(), "from": [7.75, 1.0, 7.75], "to": [8.25, 1.5, 8.25], "origin": [8, 1.0, 8],
         "box_uv": False, "faces": f, "rotation": [0, 45, 0]}
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])
    return g


def bone_node(name):
    g = groups[name]
    return {"name": g["nom"], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


build()
P = np.array(EFF)
P0 = V(8, 8, 8) - (P.min(axis=0) + P.max(axis=0)) / 2
F = build()
P = np.array(EFF)
D_ = np.array((1, 1, 0)) / math.sqrt(2)
LONGUEUR = float((P @ D_).max() - (P @ D_).min())
PART = particule()
outliner = [bone_node(F["racine"]), bone_node(PART)]


# ------------------------------------------------------------------ animations (objet vivant, guide 14)
def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 4)), "y": str(round(y + 0.0, 4)), "z": str(round(z + 0.0, 4))}],
            "time": round(t, 4), "interpolation": "linear"}


def anim(name, length, loop="loop"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "item_idle", "animators": {}}


def piste(an, g, keys):
    an["animators"].setdefault(groups[g]["uuid"], {"name": groups[g]["nom"], "type": "bone", "keyframes": []})["keyframes"] += keys


def echant(L, n):
    return [L * i / n for i in range(n + 1)]


def squash(t_s):
    """Étirement s le long de l'axe du fouet (x local du groupe crème), volume constant."""
    return t_s, 1 / math.sqrt(t_s), 1 / math.sqrt(t_s)


CR, FR, CG = F["creme"], F["fraise"], F["cage"]
CTRL = F["ctrl"]

# item_idle (6 s) : la chantilly respire, la fraise frissonne ; points d'émission coupés.
L_IDLE = 6.0
idle = anim("item_idle", L_IDLE)
piste(idle, CR, [kf("scale", t, *squash(1 + 0.022 * math.sin(TAU * t / L_IDLE * 2))) for t in echant(L_IDLE, 24)])
piste(idle, FR, [kf("rotation", t, 0, 0, 3.0 * math.sin(TAU * t / L_IDLE * 3 + 0.8)) for t in echant(L_IDLE, 24)])
for c in CTRL:
    piste(idle, c, [kf("position", 0, -1, 0, 0), kf("position", L_IDLE, -1, 0, 0)])

# event_select (0,8 s) : plop de la crème, puis la fraise tombe dedans et rebondit.
L_SEL = 0.8
sel = anim("event_select", L_SEL, "once")


def plop(t, t0=0.0, d=0.5):
    u = min(max((t - t0) / d, 0), 1)
    if u <= 0:
        return 0.02
    return 1 + (math.exp(-5.5 * u) * math.cos(u * 9.5) * -1 + (1 - u) * 0) * (1 - u) + 0.0 if u < 1 else 1.0


def plop_s(t):
    if t < 0.32:
        return 0.02 + 1.2 * sm(t, 0.0, 0.32)
    return 1 + 0.22 * math.exp(-7 * (t - 0.32)) * math.cos((t - 0.32) * 17)


piste(sel, CR, [kf("scale", t, *(lambda s: (s, s, s))(plop_s(t))) for t in echant(L_SEL, 32)])
piste(sel, FR, [kf("position", t, 0, 0, 0) if t >= 0.75 else
                kf("position", t, 0, 3.5 * (1 - sm(t, 0.3, 0.52)) - 0.35 * bump(t, 0.5, 0.56, 0.6, 0.75), 0) for t in echant(L_SEL, 32)])
piste(sel, FR, [kf("scale", t, *(lambda s: (s, s, s))(0.02 + 0.98 * sm(t, 0.28, 0.36))) for t in echant(L_SEL, 16)])
piste(sel, CG, [kf("scale", t, *(lambda s: (s, s, s))(1 + 0.05 * math.sin(TAU * 2.5 * t / 0.5) * (1 - sm(t, 0.0, 0.55)))) for t in echant(L_SEL, 24)])

# event_swing (0,4 s) : la crème prend du retard sur le geste puis revient ; la cage vibre.
L_SW = 0.4
sw = anim("event_swing", L_SW, "once")
piste(sw, CR, [kf("rotation", t, 0, 0, -7 * bump(t, 0.0, 0.08, 0.12, 0.3) + 2.5 * bump(t, 0.22, 0.3, 0.32, 0.4)) for t in echant(L_SW, 20)])
piste(sw, CG, [kf("scale", t, *(lambda s: (s, s, s))(1 + 0.035 * math.sin(TAU * 3 * t / L_SW) * (1 - sm(t, 0.0, L_SW)))) for t in echant(L_SW, 20)])

# event_hit (0,7 s) : écrasement puis rebond de la crème, nuage de farine et sucre glace qui monte ; le seul son.
L_HIT = 0.7
hit = anim("event_hit", L_HIT, "once")


def hit_s(t):
    if t < 0.06:
        return 1 - 0.2 * sm(t, 0.0, 0.06)
    return 1 - 0.2 * math.exp(-6 * (t - 0.06)) * math.cos((t - 0.06) * 15)


piste(hit, CR, [kf("scale", t, *squash(hit_s(t))) if t < L_HIT else kf("scale", t, 1, 1, 1) for t in echant(L_HIT, 28)])
piste(hit, FR, [kf("rotation", t, 0, 0, 14 * math.sin(TAU * 3 * t / 0.5) * (1 - sm(t, 0.0, 0.5))) for t in echant(L_HIT, 28)])
piste(hit, CTRL[0], [kf("position", t, 8 * bump(t, 0.0, 0.02, 0.12, 0.16), 0, 0) for t in echant(L_HIT, 28)])
for c in CTRL[1:]:
    piste(hit, c, [kf("position", t, 8 * bump(t, 0.02, 0.05, 0.25, 0.32), 0, 0) for t in echant(L_HIT, 28)])
SON_HIT = "block.powder_snow.break"

ANIMS = [idle, sel, sw, hit]

# ------------------------------------------------------------------ écriture
assert 80 <= len(elements) <= 1200, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
# item/handheld_mace (jar 26.1.2) : la masse vanilla n'a pas le Display de item/handheld
AFFICHAGE = objet.affichage(
    "masse",
    thirdperson_righthand={"rotation": [0, -90, 55], "translation": [0, 4.0, 1], "scale": [1, 1, 1]},
    thirdperson_lefthand={"rotation": [0, 90, -55], "translation": [0, 4.0, 1], "scale": [1, 1, 1]},
    firstperson_righthand={"rotation": [0, -90, 25], "translation": [0, 3, 0.8], "scale": [0.9, 0.9, 0.9]},
    firstperson_lefthand={"rotation": [0, 90, -25], "translation": [0, 3, 0.8], "scale": [0.9, 0.9, 0.9]},
    gui={"scale": [0.72, 0.72, 0.72]})
model = objet.modele(NOM, "masse", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
model["unhandled_root_fields"]["phynaria"]["particules"] = {
    "sucre": {"quand": "toujours", "nombre": 10, "duree": 3, "mouvement": "monte", "au_sol": "disparait", "rendu": "opaque",
              "sens": "libre", "fin_de_vie": "retrecit", "depart": "moyen", "dispersion": 45, "elan": 40, "variation": "forte",
              "rafale": "aucune", "limite": 64},
    "mc_poof": {"quand": "toujours", "nombre": 10, "depart": "lent", "dispersion": 45, "rafale": "aucune", "limite": 64}}
from sons import limiter_sons
limiter_sons(model)
# Un seul son, au coup qui touche (tools/sons.py ne connaît pas encore les événements d'objet) : on le remet ici.
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": SON_HIT, "file": ""}], "time": 0.04}]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
print(f"longueur sur la diagonale {LONGUEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)}")
