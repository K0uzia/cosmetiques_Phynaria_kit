"""Pelle à tarte nappée : skin d'objet (guide 14) pour toutes les pelles du joueur, ensemble Pâtisserie (thème Mignon). Design original.
Écrit skin_pelle_patisserie.png, skin_pelle_patisserie_e.png et .build/skin_pelle_patisserie_brut.bbmodel à côté de ce script.

D'après de vrais ustensiles de pâtissier (fiche .claude/styles/patisserie.md, Sources) : une **pelle à tarte** (lame triangulaire
à bout arrondi, un bord dentelé pour couper la croûte, col coudé qui met la lame plus bas que le manche pour glisser sous la part),
manche de hêtre à deux rivets, bout trempé dans le chocolat. La lame sort d'un bol de nappage fraise : le glaçage couvre le bout et
**coule vers le manche en gouttes rondes de longueurs inégales** (perle au bout), vermicelles posés sans se toucher.
Silhouette : plate et large en haut, manche fin (le rouleau du même ensemble, skin de masse, est un cylindre).

Repère (catégorie objets, Recette) : comme l'image vanilla de la pelle vue depuis +Z, lame en haut à droite, manche vers le bas à
gauche, sur la diagonale du bloc, centrée en (8, 8, 8) ; plat de la lame vers ±Z ; 20 px du bout du manche au bout de la lame
(pelle vanilla ≈ 18 px, +11 %). Display vanilla `item/handheld` (tools/objet.py), échelle `gui` réglée sur la boîte.
Une seule étape : groupe racine `repos`.

Objet vivant (guide 14), format free :
- item_idle (4 s) : les gouttes de nappage gonflent et se resserrent à peine, décalées (le glaçage est encore frais) ;
  tous les `ctrl_emit` à −1 (vermicelles coupés hors des événements) ;
- event_select (0,7 s) : « plop » du nappage (échelle 0,2 → 1,14 → 0,94 → 1), puis les gouttes descendent ;
- event_swing (0,4 s) : le nappage tremble comme une gelée, les gouttes ballottent en retard ; pas de particule (on mine vite) ;
- event_break (0,5 s, bloc cassé) : petite pluie de vermicelles qui **monte** puis rétrécit (ctrl_emit +8 pendant 0,4 s,
  3 sortes : menthe, citron, ciel ; Mouvement « Monte », Au sol « Disparaît ») + tremblement ;
- event_hit (0,45 s) : tremblement plus fort ; **seul son** de la pièce (block.honey_block.place, plop collant).
Fonctions avancées : calque _e (reflet du nappage seulement), particle_/emit_/ctrl_emit, animations d'objet. Non simulés par
l'aperçu : animations d'objet, particules, ctrl_emit. À juger en jeu : event_break et event_hit (pas encore vérifiés par le
développeur), les vermicelles, le son d'un objet.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

AVEC_E = True
NOM = "skin_pelle_patisserie"
TEX = 512
TAU = 2 * math.pi
SS = 4                      # sur-échantillonnage de la peinture
DENS = 30.0                 # texels par px sur les grandes plaques
rng = np.random.default_rng(11)

# ------------------------------------------------------------------ repère : a le long de l'objet (manche -> lame), b dans le plan
A_ = np.array((1.0, 1.0, 0.0)) / math.sqrt(2)
B_ = np.array((-1.0, 1.0, 0.0)) / math.sqrt(2)
N_ = np.cross(A_, B_)                                  # +Z
L_TOT = 20.15
P0 = np.array((8.0, 8.0, 8.0)) - A_ * (L_TOT / 2 + 1.22)   # boîte centrée en (8, 8)


def W(a, b=0.0, z=0.0):
    return P0 + a * A_ + b * B_ + z * N_


ZB = -0.9                   # plan de la lame (col coudé : la lame est plus bas que le manche)
BL_T = 0.25                 # demi-épaisseur de la plaque de lame
GL_T = 0.50                 # demi-épaisseur de la plaque de nappage (enveloppe la lame)
# lame : triangle intérieur arrondi d'un rayon R_OFF (bords et bout ronds)
TRI = np.array([(11.3, 2.45), (11.3, -2.45), (19.4, 0.0)])
R_OFF = 0.75
# rectangle de la plaque (a, b)
PA0, PA1, PB = 10.45, 20.25, 3.6
PW, PH = PA1 - PA0, 2 * PB


def front(b):
    """Limite du nappage côté manche (le glaçage couvre a > front)."""
    return 15.0 + 0.28 * np.sin(np.asarray(b) * 2.3 + 0.6) + 0.12 * np.sin(np.asarray(b) * 5.1)


# gouttes : (b, longueur, largeur)
GOUTTES = [(-1.75, 1.3, 0.95), (-0.5, 2.3, 1.1), (0.8, 1.0, 0.9), (1.75, 1.7, 0.85)]


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


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


# ------------------------------------------------------------------ formes 2D (numpy, en px du plan)
def dist_seg(pa, pb, p, q):
    """Distance des points (pa, pb) au segment p-q, et paramètre s (0..1)."""
    d = q - p
    s = np.clip(((pa - p[0]) * d[0] + (pb - p[1]) * d[1]) / (d @ d), 0, 1)
    return np.hypot(pa - (p[0] + s * d[0]), pb - (p[1] + s * d[1])), s


def tri_dist(pa, pb):
    """Distance au triangle intérieur (0 dedans)."""
    dmin = np.full(pa.shape, 1e9)
    neg = np.ones(pa.shape, bool)
    pos = np.ones(pa.shape, bool)
    for i in range(3):
        p, q = TRI[i], TRI[(i + 1) % 3]
        d, _ = dist_seg(pa, pb, p, q)
        dmin = np.minimum(dmin, d)
        cr = (q[0] - p[0]) * (pb - p[1]) - (q[1] - p[1]) * (pa - p[0])
        neg &= cr <= 0
        pos &= cr >= 0
    inside = neg | pos
    return np.where(inside, 0.0, dmin)


def blade_sd(pa, pb):
    """> 0 hors de la lame, < 0 dedans (px). Bord +b dentelé (festons ronds)."""
    sd = tri_dist(pa, pb) - R_OFF
    d, s = dist_seg(pa, pb, TRI[0], TRI[2])
    L = np.linalg.norm(TRI[2] - TRI[0])
    zone = (s > 0.08) & (s < 0.86) & (pb > 0) & (d < R_OFF + 0.5)
    feston = 0.2 * (0.5 + 0.5 * np.cos(TAU * s * L / 0.62))
    return np.where(zone, sd + feston, sd)


def glaze_sd(pa, pb):
    """Contour du nappage : la lame élargie de 0,1 px, côté bout de front(b) ; lobes ronds à la racine des gouttes."""
    sd = np.maximum(blade_sd(pa, pb) - 0.1, front(pb) - pa)
    for b, L, w in GOUTTES:
        a0 = float(front(b))
        lobe = np.hypot((pa - (a0 - 0.12)) / 1.0, pb - b) - (w / 2 + 0.12)
        d, _ = dist_seg(pa, pb, np.array((a0, b)), np.array((a0 - L, b)))
        coulee = d - w * 0.44                                   # coulée qui s'affine
        perle = np.hypot(pa - (a0 - L), pb - b) - w * 0.62         # perle ronde au bout
        sd = np.minimum(sd, np.maximum(np.minimum(np.minimum(lobe, coulee), perle), blade_sd(pa, pb) - 0.1))
    return sd


def half_width(a, sdf=blade_sd, b_lim=PB):
    """Demi-largeur (approx.) d'une forme en a : plus petit |b| hors forme."""
    bs = np.linspace(0, b_lim, 200)
    hp = bs[np.argmax(sdf(np.full(200, a), bs) > 0)] if (sdf(np.full(200, a), bs) > 0).any() else b_lim
    hn = bs[np.argmax(sdf(np.full(200, a), -bs) > 0)] if (sdf(np.full(200, a), -bs) > 0).any() else b_lim
    return float(min(hp, hn))


# ------------------------------------------------------------------ peinture
def grille(w, h):
    """Coordonnées (a, b) des texels sur-échantillonnés d'une plaque de PW × PH."""
    Wt, Ht = int(round(w * DENS)) * SS, int(round(h * DENS)) * SS
    i = (np.arange(Wt) + 0.5) / Wt
    j = (np.arange(Ht) + 0.5) / Ht
    pa = PA0 + i[None, :] * w
    pb = PB - j[:, None] * h
    return np.broadcast_to(pa, (Ht, Wt)).copy(), np.broadcast_to(pb, (Ht, Wt)).copy()


def finir(rgb, alpha, Wt, Ht):
    """Réduction LANCZOS + seuil alpha 0/255."""
    im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8), "RGBA")
    im = im.resize((Wt // SS, Ht // SS), Image.LANCZOS)
    a = np.array(im)
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    a[a[..., 3] == 0, :3] = 0
    return a


def col(c):
    return np.array(c, float)


def paint_blade():
    pa, pb = grille(PW, PH)
    sd = blade_sd(pa, pb)
    inside = sd < 0
    base, light, shade, line = col((198, 202, 214)), col((244, 245, 250)), col((128, 132, 150)), col((92, 96, 120))
    # lumière peinte d'en haut (dans le plan de l'image, +Y monde = (a + b)/√2)
    up = ((pa - 15) + pb) / 9.0
    rgb = base + (np.clip(up, -1, 1)[..., None] * 0.5 + 0.5) * 0 + 0
    k = np.clip(0.5 + 0.35 * up, 0, 1)[..., None]
    rgb = lerp(shade, light, k) * 0.5 + base * 0.5
    # brossé le long de a (±5 %)
    stries = np.sin(pb * 41.0 + np.sin(pb * 7.0) * 2) * 0.03 + np.sin(pb * 97.0) * 0.02
    rgb = rgb * (1 + stries[..., None])
    # bande de reflet en biais
    refl = np.exp(-((pa - 15.8) - 0.9 * pb) ** 2 / 0.35)
    rgb = lerp(rgb, light, 0.55 * refl[..., None])
    # biseau clair puis liseré foncé au bord
    e = -sd
    rgb = np.where(((e > 0.1) & (e < 0.26))[..., None], lerp(rgb, light, 0.6), rgb)
    rgb = np.where((e <= 0.1)[..., None], line, rgb)

    Ht, Wt = pa.shape
    return finir(rgb, inside, Wt, Ht)


def sprinkle_list(sd_fn, n, zone_a, seed, eviter=None):
    """Vermicelles : (a, b, angle, couleur), à ≥ 0,55 px l'un de l'autre, dedans à ≥ 0,3 px du bord."""
    r = np.random.default_rng(seed)
    cols = [(120, 222, 192), (120, 186, 248), (255, 226, 104), (186, 150, 248), (255, 252, 244), (255, 156, 112)]
    out = []
    tries = 0
    while len(out) < n and tries < 4000:
        tries += 1
        a, b = r.uniform(*zone_a), r.uniform(-3, 3)
        if sd_fn(np.array([a]), np.array([b]))[0] > -0.35:
            continue
        if eviter and eviter(a, b):
            continue
        if any(math.hypot(a - o[0], b - o[1]) < 0.62 for o in out):
            continue
        out.append((a, b, r.uniform(0, math.pi), cols[len(out) % len(cols)]))
    return out


def in_highlight(a, b):
    return (a - 18.3) ** 2 / 0.9 + (b - 0.45) ** 2 / 0.35 < 1.6


SPR_PEINTS = None


def paint_glaze():
    global SPR_PEINTS
    pa, pb = grille(PW, PH)
    sd = glaze_sd(pa, pb)
    inside = sd < 0
    base, light, shade, line = col((246, 108, 156)), col((255, 182, 210)), col((196, 52, 108)), col((146, 22, 74))
    up = ((pa - 16.5) + pb) / 5.0
    rgb = lerp(shade, light, np.clip(0.5 + 0.4 * up, 0, 1)[..., None]) * 0.55 + base * 0.45
    e = -sd
    # bourrelet : plus clair juste à l'intérieur du bord (le nappage est bombé), liseré framboise au bord
    rgb = np.where(((e > 0.12) & (e < 0.3))[..., None], lerp(rgb, light, 0.35), rgb)
    rgb = np.where((e <= 0.12)[..., None], line, rgb)
    # ombre colorée sous le bourrelet côté manche
    rgb = np.where(((pa - front(pb) > 0) & (pa - front(pb) < 0.35))[..., None], lerp(rgb, shade, 0.45), rgb)
    # vermicelles peints (≥ 4 texels de large)
    SPR_PEINTS = sprinkle_list(glaze_sd, 14, (15.3, 19.6), 5, eviter=in_highlight)
    for a, b, ang, c in SPR_PEINTS:
        ca, cb = math.cos(ang), math.sin(ang)
        u = (pa - a) * ca + (pb - b) * cb
        v = -(pa - a) * cb + (pb - b) * ca
        m = (np.clip(np.abs(u) - 0.24, 0, None) ** 2 + v ** 2) < 0.085 ** 2
        sh = (np.clip(np.abs(u) - 0.24, 0, None) ** 2 + (v + 0.05) ** 2) < 0.1 ** 2
        rgb = np.where((sh & ~m & inside)[..., None], lerp(rgb, shade, 0.5), rgb)
        rgb = np.where((m & inside)[..., None], col(c), rgb)
    # reflet net : fenêtre blanche arrondie + point (seule source du calque _e)
    ra, rb_ = (pa - 18.15), (pb - 0.55)
    ca, cb = math.cos(0.5), math.sin(0.5)
    u, v = ra * ca + rb_ * cb, -ra * cb + rb_ * ca
    fen = (np.clip(np.abs(u) - 0.45, 0, None) ** 2 + np.clip(np.abs(v) - 0.12, 0, None) ** 2) < 0.1 ** 2
    pt = np.hypot(pa - 17.25, pb - 0.95) < 0.17
    hl = (fen | pt) & inside
    rgb = np.where(hl[..., None], col((255, 250, 252)), rgb)
    Ht, Wt = pa.shape
    img = finir(rgb, inside, Wt, Ht)
    e_rgb = np.where(hl[..., None], col((225, 205, 215)), 0.0)
    img_e = finir(e_rgb, hl, Wt, Ht)
    return img, img_e


def paint_strip(W_, H_, base, light, shade, grain=0.0, seed=1, dots=None, line=None):
    r = np.random.default_rng(seed)
    y = (np.arange(H_) + 0.5) / H_
    k = np.clip(1 - np.abs(y - 0.35) * 1.6, 0, 1)                   # bande claire décalée vers le haut
    rgb = lerp(col(shade), col(light), k[:, None, None] * np.ones((H_, W_, 1)))
    rgb = rgb * 0.6 + col(base) * 0.4
    if grain:
        x = np.arange(W_)
        g = np.sin(np.arange(H_)[:, None] * 1.4 + np.sin(x[None, :] * 0.045) * 1.3) * grain     # fil du bois dans la longueur
        g += r.normal(0, grain * 0.3, (H_, W_))
        rgb = rgb * (1 + g[..., None])
    if line is not None:
        rgb[:1] = col(line)
        rgb[-1:] = col(line)
    if dots:
        for (dx, dy, c) in dots:
            yy, xx = np.mgrid[0:H_, 0:W_]
            rgb = np.where(((xx - dx) ** 2 + (yy - dy) ** 2 < 2.3 ** 2)[..., None], col(c), rgb)
    a = np.full((H_, W_, 1), 255.0)
    return np.dstack([np.clip(rgb, 0, 255), a]).astype(np.uint8)


def paint_rod(c, W_=32, H_=12):
    """Vermicelle (particule et cubes posés) : bâtonnet aux bouts ronds, reflet clair, sur fond transparent."""
    yy, xx = np.mgrid[0:H_ * SS, 0:W_ * SS] + 0.5
    u, v = xx / SS - W_ / 2, yy / SS - H_ / 2
    m = (np.clip(np.abs(u) - (W_ / 2 - H_ / 2), 0, None) ** 2 + v ** 2) < (H_ / 2 - 0.5) ** 2
    rgb = np.where((v < -1.2)[..., None], lerp(col(c), col((255, 255, 255)), 0.45), col(c))
    rgb = np.where((v > 2.0)[..., None], col(c) * 0.72, rgb)
    return finir(rgb, m, W_ * SS, H_ * SS)


def paint_plain(c, W_=16, H_=8):
    return paint_strip(W_, H_, c, lerp(col(c), col((255, 255, 255)), 0.4), col(c) * 0.7)


VERM = {"menthe": (120, 222, 192), "citron": (255, 226, 104), "ciel": (120, 186, 248)}
SPR_COLS = [(120, 222, 192), (120, 186, 248), (255, 226, 104), (186, 150, 248), (255, 252, 244), (255, 156, 112)]

UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def atlas():
    bl = paint_blade()
    gl, gle = paint_glaze()
    items = [("lame", bl, None), ("nappage", gl, gle),
             ("acier", paint_strip(128, 16, (196, 200, 212), (246, 247, 252), (120, 124, 142), grain=0.02, seed=2), None),
             ("bois", paint_strip(192, 24, (226, 164, 92), (246, 208, 140), (150, 90, 44), grain=0.07, seed=3), None),
             ("choco", paint_strip(96, 20, (104, 60, 40), (164, 108, 74), (58, 30, 22), seed=4,
                                   dots=[(12, 8, (120, 222, 192)), (37, 12, (255, 226, 104)), (60, 7, (255, 252, 244)), (82, 13, (120, 186, 248))]), None),
             ("glacage", paint_strip(64, 16, (246, 108, 156), (255, 186, 212), (196, 52, 108)), None),
             ("laiton", paint_strip(32, 12, (222, 178, 86), (255, 236, 160), (150, 104, 40)), None)]
    for n, c in VERM.items():
        items.append((f"verm_{n}", paint_rod(c), None))
    for i, c in enumerate(SPR_COLS):
        items.append((f"spr{i}", paint_plain(c), None))
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
    assert tex[TEX - 3, TEX - 3, 3] == 0
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
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def rmat(rx, ry, rz):
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def group(name, origin, parent=None, nom=None):
    assert name not in groups
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "rotation": [0, 0, 0],
                    "nom": nom or name}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


R_PLAN = np.column_stack([A_, B_, N_])
ROT_PLAN = euler(R_PLAN)


def plate(g, name, a0, a1, b0, b1, z, th, tile):
    """Plaque dans le plan de l'objet (u suit a, haut de l'image = +b), contour par l'alpha, tranches transparentes."""
    u0, v0, u1, v1 = UV[tile]
    c = W((a0 + a1) / 2, (b0 + b1) / 2, z)
    w, h = a1 - a0, b1 - b0
    cube(g, name, c - (w / 2, h / 2, th), c + (w / 2, h / 2, th), c, ROT_PLAN,
         {"south": [u0, v0, u1, v1], "north": [u1, v0, u0, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def strip(tile, u0=0.0, u1=1.0, caps=(True, True)):
    bu0, bv0, bu1, bv1 = UV[tile]
    ua = lerp(bu0, bu1, u0)
    ub = max(lerp(bu0, bu1, u1), ua + 2)
    lg = [ua, bv0, ub, bv1]
    end = [ua, bv0 + 3, ua + 2, bv0 + 5]
    return {"south": lg, "north": lg, "up": lg, "down": lg, "east": end if caps[1] else CLEAR, "west": end if caps[0] else CLEAR}


def block(g, name, a0, a1, hb, hz, z, tile, b=0.0, u0=0.0, u1=1.0):
    """Pavé plein dans le repère du plan : a0..a1, ±hb, z ± hz (âmes)."""
    c = W((a0 + a1) / 2, b, z)
    L = a1 - a0
    cube(g, name, c - (L / 2, hb, hz), c + (L / 2, hb, hz), c, ROT_PLAN, strip(tile, u0, u1))


def bar(g, name, p, q, r, tile, u0=0.0, u1=1.0, octo=True, ov=0.05, rz=None):
    """Barre de section octogonale (deux pavés croisés à 45°) de p à q ; section de référence vers +Z."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X = unit(q - p)
    ref = N_ if abs(X @ N_) < 0.9 else B_
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    rz = r if rz is None else rz
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R0 = np.column_stack([X, Y, Z_])
    R45 = np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])
    faces = strip(tile, u0, u1)
    cube(g, name, p + (-ov, -rz, -r), p + (L + ov, rz, r), p, euler(R0), faces)
    if octo:
        m = 0.97 * min(r, rz)
        cube(g, name + "o", p + (-ov + 0.06, -m, -m), p + (L + ov - 0.06, m, m), p, euler(R45), faces)


def bone_node(name):
    g = groups[name]
    return {"name": g["nom"], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


# --- arborescence
racine = group("repos", W(5.0), nom=objet.etape("repos", "pelle"))
manche = group("manche", W(5.0), racine)
lame = group("lame", W(10.5, 0, ZB), racine)
napp = group("nappage", W(16.8, 0, ZB), lame)

# --- manche : bout trempé dans le chocolat, hêtre bombé, deux rivets de laiton, virole d'acier
bar(manche, "choc_bout", W(-0.12), W(0.25), 0.72, "choco", 0.0, 0.1)
bar(manche, "choc", W(0.2), W(1.75), 1.08, "choco")
prof = [(1.7, 0.92), (3.2, 1.02), (5.0, 1.04), (6.6, 0.98), (8.1, 0.88)]
for i in range(len(prof) - 1):
    (a0, r0), (a1, r1) = prof[i], prof[i + 1]
    bar(manche, f"bois{i}", W(a0), W(a1), (r0 + r1) / 2, "bois", i / 4, (i + 1) / 4)
for i, a in enumerate((3.6, 6.0)):
    for sgn in (1, -1):
        c = W(a, 0, sgn * 1.0)
        cube(manche, f"rivet{i}{'av' if sgn > 0 else 'ar'}", c - (0.26, 0.26, 0.12), c + (0.26, 0.26, 0.12), c, ROT_PLAN, strip("laiton"))
bar(manche, "virole", W(8.0), W(9.0), 1.04, "acier")
bar(manche, "virole_anneau", W(8.15), W(8.4), 1.12, "acier")

# --- col coudé (la lame descend de 0,9 px pour glisser sous la part)
bar(lame, "col0", W(8.9), W(9.65), 0.5, "acier", octo=False, rz=0.24)
bar(lame, "col1", W(9.6), W(10.55, 0, ZB), 0.48, "acier", octo=False, rz=0.24)
bar(lame, "col2", W(10.5, 0, ZB), W(11.9, 0, ZB), 0.55, "acier", octo=False, rz=0.2)

# --- lame : plaque découpée + âme en gradins
plate(lame, "lame_plaque", PA0, PA1, -PB, PB, ZB, BL_T, "lame")
cuts = np.linspace(10.75, 19.75, 10)
for i in range(len(cuts) - 1):
    a0, a1 = cuts[i], cuts[i + 1]
    hb = min(half_width(a0 + 0.02), half_width(a1 - 0.02)) - 0.16
    if hb > 0.1:
        block(lame, f"lame_ame{i}", a0, a1, hb, BL_T - 0.12, ZB, "acier")

# --- nappage : plaque découpée qui enveloppe la lame, âme rose en gradins, gouttes en volume, vermicelles posés
plate(napp, "nappage_plaque", PA0, PA1, -PB, PB, ZB, GL_T, "nappage")
cuts = np.linspace(15.45, 19.85, 6)
for i in range(len(cuts) - 1):
    a0, a1 = cuts[i], cuts[i + 1]
    hb = min(half_width(a0 + 0.02, glaze_sd), half_width(a1 - 0.02, glaze_sd)) - 0.3
    if hb > 0.1:
        block(napp, f"nappage_ame{i}", a0, a1, hb, GL_T - 0.12, ZB, "glacage")

GOUT = []
for i, (b, L, w) in enumerate(GOUTTES):
    a_root = float(front(b)) + 0.1
    g = group(f"goutte{i}", W(a_root - 0.1 - L, b, ZB), napp)      # pivot sur la perle
    GOUT.append(g)
    for side, z in (("av", ZB + GL_T - 0.06), ("ar", ZB - GL_T + 0.06)):
        # la coulée est peinte dans la plaque ; la perle du bout est en relief (goutte bombée)
        a_end = a_root - 0.1 - L
        pr = w * 0.5
        bar(g, f"g{i}{side}_perle", W(a_end - pr * 0.75, b, z), W(a_end + pr * 0.75, b, z), pr, "glacage", 0.2, 0.5, rz=pr * 0.55)

# vermicelles en relief (posés sur le nappage, face avant), pris parmi des places libres
SPR3D = sprinkle_list(glaze_sd, 6, (15.6, 19.3), 17, eviter=lambda a, b: in_highlight(a, b) or
                      any(math.hypot(a - p[0], b - p[1]) < 0.55 for p in SPR_PEINTS))
for i, (a, b, ang, c) in enumerate(SPR3D):
    z = ZB + GL_T + 0.05
    R_ = R_PLAN @ rmat(0, 0, math.degrees(ang))
    p = W(a, b, z)
    cube(napp, f"verm{i}", p - (0.33, 0.1, 0.1), p + (0.33, 0.1, 0.1), p, euler(R_), strip(f"spr{SPR_COLS.index(c)}"))

# points de départ des vermicelles (particules) sur le nappage, chacun avec son ctrl_emit
CTRL = []
emits = [(17.4, -0.8), (16.2, 1.1), (18.7, 0.2), (16.4, -1.4), (17.6, 0.9), (15.9, -0.2)]
for i, (a, b) in enumerate(emits):
    sorte = list(VERM)[i % 3]
    nom = f"emit_vermicelle_{sorte}" + ("" if i < 3 else "2")
    e = group(f"E{i}", W(a, b, ZB + GL_T + 0.3), napp, nom=nom)
    c = group(f"C{i}", W(a, b, ZB + GL_T + 0.3), e, nom="ctrl_emit")
    CTRL.append(c)

# --- particules (à la racine, jamais dessinées en main) : un cube, face up seule, y ≥ 0,3 au-dessus du pivot
PARTS = {}
for k, n in enumerate(VERM):
    p = np.array((1.0 + 1.6 * k, 0.5, 8.0))
    g = group(f"P{k}", p, None, nom=f"particle_vermicelle_{n}")
    PARTS[n] = g
    u0, v0, u1, v1 = UV[f"verm_{n}"]
    cube(g, f"verm_{n}", p + (-0.4, 0.3, -0.15), p + (0.4, 0.6, 0.15), p, (0, 0, 0),
         {"up": [u0, v0, u1, v1], "down": CLEAR, "north": CLEAR, "south": CLEAR, "east": CLEAR, "west": CLEAR})

outliner = [bone_node(racine)] + [bone_node(PARTS[n]) for n in VERM]


def coins(els):
    P = []
    for e in els:
        f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
        R = rmat(*e.get("rotation", (0, 0, 0)))
        for i in range(8):
            c = np.array([(f, t)[(i >> k) & 1][k] for k in range(3)])
            P.append(R @ (c - o) + o)
    return np.array(P)


part_ids = {i for n in VERM for i in groups[PARTS[n]]["ids"]}
P = coins([e for e in elements if e["uuid"] not in part_ids])
LONGUEUR = float((P @ A_).max() - (P @ A_).min())
ETENDUE = float(max(P[:, 0].max() - P[:, 0].min(), P[:, 1].max() - P[:, 1].min()))

# ------------------------------------------------------------------ animations (objet vivant, guide 14)
def sckf(t, v, vy=None, vz=None):
    vy = v if vy is None else vy
    vz = v if vz is None else vz
    return {"channel": "scale", "data_points": [{"x": str(round(v, 3)), "y": str(round(vy, 3)), "z": str(round(vz, 3))}],
            "time": round(t, 4), "interpolation": "linear"}


def rotkf(t, z):
    return {"channel": "rotation", "data_points": [{"x": "0", "y": "0", "z": str(round(z + 0.0, 2))}], "time": round(t, 4),
            "interpolation": "linear"}


def rotkf3(t, x, y, z):
    return {"channel": "rotation", "data_points": [{"x": str(round(x, 2)), "y": str(round(y, 2)), "z": str(round(z, 2))}],
            "time": round(t, 4), "interpolation": "linear"}


def poskf(t, x):
    return {"channel": "position", "data_points": [{"x": str(round(x + 0.0, 3)), "y": "0", "z": "0"}], "time": round(t, 4),
            "interpolation": "linear"}


def anim(name, length, loop="loop"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "item_idle", "animators": {}}


def piste(an, g, keys):
    an["animators"][groups[g]["uuid"]] = {"name": groups[g]["nom"], "type": "bone", "keyframes": keys}


def echant(L, n):
    return [L * i / n for i in range(n + 1)]


# item_idle (4 s) : les gouttes gonflent et se resserrent à peine (décalées) ; vermicelles coupés (ctrl_emit −1)
L_IDLE = 4.0
idle = anim("item_idle", L_IDLE)
for j, g in enumerate(GOUT):
    piste(idle, g, [sckf(t, 1 + 0.07 * (0.5 - 0.5 * math.cos(TAU * (t / L_IDLE - 0.21 * j)))) for t in echant(L_IDLE, 16)])
for c in CTRL:
    piste(idle, c, [poskf(0.0, -1), poskf(L_IDLE, -1)])


def tremble(t, amp, f=3.0, dur=0.36, t0=0.0):
    """Gelée : oscillation amortie à volume à peu près constant."""
    if t < t0:
        return 0.0
    u = t - t0
    return amp * math.sin(TAU * f * u / dur) * (1 - sm(u, 0.0, dur))


def jiggle(an, L, amp, n=18):
    piste(an, napp, [sckf(t, 1 + tremble(t, amp), 1 - tremble(t, amp), 1) for t in echant(L, n)])
    for j, g in enumerate(GOUT):
        piste(an, g, [rotkf(t, tremble(t, 140 * amp, 2.0, L * 0.9, 0.03 + 0.02 * j)) for t in echant(L, n)])


# event_select (0,7 s) : plop du nappage puis les gouttes descendent
L_SEL = 0.7
sel = anim("event_select", L_SEL, "once")


def plop(t):
    if t < 0.22:
        return lerp(0.2, 1.14, sm(t, 0.0, 0.22))
    if t < 0.34:
        return lerp(1.14, 0.94, sm(t, 0.22, 0.34))
    if t < 0.46:
        return lerp(0.94, 1.02, sm(t, 0.34, 0.46))
    return lerp(1.02, 1.0, sm(t, 0.46, 0.6))


piste(sel, napp, [sckf(t, plop(t)) for t in echant(L_SEL, 28)])
for j, g in enumerate(GOUT):
    t0 = 0.26 + 0.04 * j
    piste(sel, g, [sckf(t, 0.05 + 0.95 * sm(t, t0, t0 + 0.24) + 0.08 * bump(t, t0 + 0.16, t0 + 0.24, t0 + 0.26, min(L_SEL, t0 + 0.38)))
                   for t in echant(L_SEL, 28)])

# event_swing (0,4 s) : tremblement de gelée, gouttes qui ballottent
L_SW = 0.4
sw = anim("event_swing", L_SW, "once")
jiggle(sw, L_SW, 0.05)

# event_break (0,5 s) : pluie de vermicelles qui monte (ctrl_emit −1 + 8 = +7 pendant 0,4 s) et tremblement
L_BR = 0.5
br = anim("event_break", L_BR, "once")
jiggle(br, L_BR, 0.06)
for c in CTRL:
    piste(br, c, [poskf(0.0, 0), poskf(0.02, 8), poskf(0.38, 8), poskf(0.42, 0), poskf(L_BR, 0)])

# event_hit (0,45 s) : tremblement plus fort ; seul son
L_HIT = 0.45
hit = anim("event_hit", L_HIT, "once")
jiggle(hit, L_HIT, 0.08)
SON_HIT = "block.honey_block.place"

# particules : le vermicelle tournoie en montant
PANIMS = []
for k, n in enumerate(VERM):
    pa_ = anim(f"particle_vermicelle_{n}_fall", 1.0)
    sens = (1, -1, 1)[k]
    piste(pa_, PARTS[n], [rotkf3(t, 360 * t, 0, sens * 720 * t) for t in echant(1.0, 8)])
    PANIMS.append(pa_)

ANIMS = [idle, sel, sw, br, hit] + PANIMS

# ------------------------------------------------------------------ écriture
assert 40 <= len(elements) <= 600, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
GUI = round(min(1.0, 15.2 / ETENDUE), 2)
AFFICHAGE = objet.affichage("pelle", gui={"scale": [GUI, GUI, GUI]})
model = objet.modele(NOM, "pelle", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons
limiter_sons(model)
# Un seul son, au coup qui touche (event_hit, rare avec une pelle) : tools/sons.py ne connaît pas encore les événements d'objet.
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
print(f"longueur {LONGUEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)} ; étendue {ETENDUE:.1f} ; gui {GUI}")
