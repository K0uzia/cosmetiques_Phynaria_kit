"""Écu de givre : skin de bouclier (guide 14, type `bouclier`), ensemble Givre (thème Éléments). Design original.
Écrit skin_bouclier_givre.png, skin_bouclier_givre_e.png et .build/skin_bouclier_givre_brut.bbmodel à côté de ce script.

Références (fiche `.claude/references/objets/boucliers.md`) : l'écu (bouclier en « fer à repasser » du XIIIe s. : haut droit,
flancs qui se referment en deux arcs jusqu'à une pointe, face bombée), l'umbo des boucliers à poignée centrale (bosse qui
protège le poing, poignée juste derrière), l'orle (bord renforcé de métal, roulé) et les traverses du dos ; la glace réelle
(glace claire taillée, givre en plumes et en aiguilles qui pousse sur les arêtes et les bords, fissures blanches).

Repère : celui du bouclier de Minecraft (modèle d'entité retourné (1, −1, −1), dessiné après le recentrage du bloc) : écu
centré sur l'origine du bloc, face vers +Z (vue de l'inventaire), poignée vers −Z (vanilla : plaque 12 × 22 × 1 de
z = 1 à 2, poignée 2 × 6 × 6 de z = −5 à 1). Réglages Display recopiés de `item/shield.json` du jar 26.1.2 : le skin est tenu,
posé et rangé exactement comme le bouclier vanilla.

**Vrai volume** (recette `.claude/references/objets/volume-3d.md`, glace de `skin_epee_givre` ; refonte du 2026-11-08 :
l'ancienne version, une plaque de glace flottant devant une plaque d'âme, se lisait en couches) :
- face bombée en trois pales (centre à plat, flancs repliés de 15° autour des arêtes avant) ; sur elles, la glace est
  **taillée en facettes** : une surface triangulée (umbo → arêtes → orle) dont chaque facette est une plaque inclinée qui
  passe par ses trois sommets, découpée par l'alpha (chaque facette déborde de 0,05 px sur les précédentes seulement) ; la
  glace s'épaissit de 0,65 px au bord à 1,55 px autour de l'umbo, les arêtes de repli sont des crêtes vives ;
- glace = **peau `trans_`** (facettes, alpha 150–228, givre en plumes le long de l'orle, arêtes blanches) sur une **âme
  opaque** bleu nuit (trois plaques, une par pale), le volume est fermé par l'orle et le dos ;
- orle **roulé** d'argent froid : barre octogonale (apothème 0,9 px) qui suit le contour et dépasse la glace de 0,45 px ;
- umbo **bombé** : tour hexagonale (collet d'argent, deux pentes de glace pâle, couvercle givré) portant un **flocon en
  relief** (6 bras en barres à section losange, 12 branches) et une gemme hexagonale cyan (`_e`) ;
- crête de cinq **cristaux hexagonaux** pointus sur le bord haut, un cristal sous la pointe, nervures de glace en losange
  sur les crêtes de repli ;
- dos : deux traverses d'argent, montants et poignée de cuir bleu nuit à la place de la poignée vanilla ;
- fissures : plaques blanches à âme cyan (`_e`) cachées dans l'âme ; elles sortent devant elle (et se voient à travers la
  glace) quand le coup touche, quand l'objet est très usé, ou quand le porteur est touché en parant.

Étapes (guide 14) : `repos` et `bloque` (deux copies de l'écu, mêmes tuiles). Le mod garde les réglages Display du repos
pendant la parade (ItemSkinRenderer.transform ne dépend pas de l'étape, javap du 2026-11-08) : `item_use` place donc l'écu
comme `item/shield_blocking` par un groupe `pose_bloque` (rotation et position en Molang selon `q.in_first_person` et
`q.hand`, calculées ici et contrôlées par matrices). En `bloque`, le givre se renforce : crête plus haute, huit aiguilles
hexagonales autour de l'orle.

Objet vivant (sobre) :
- item_idle (8 s) : frisson de la crête à 5 s ; fissures sorties selon l'usure (`q.item_durability` > 0,55) ;
- item_use : pose de parade (aussi dans item_idle, correctif F6) + fissures (usure, `q.hit_by_entity`) ;
- event_select (0,7 s) : la crête et le cristal de pointe poussent depuis leur base, le flocon se visse ;
- event_use_start (0,55 s) : les aiguilles de l'orle jaillissent en cascade, la crête grandit, éclat `add_` au cœur de l'umbo ;
  sans son (retiré le 2026-11-08 : son répété en jeu tant que le blocage saute, voir skin_bouclier_orage) ;
- event_hit (0,7 s) : les fissures s'ouvrent d'un coup puis se referment (rentrent dans l'âme) ;
- overlay_flocon (24 s) : le flocon de l'umbo fait un tour.
Fonctions avancées : `trans_` (glace), `add_` (éclat), calque `_e`, Molang `q.in_first_person`, `q.hand`, `q.item_durability`,
`q.hit_by_entity`. Se juge en jeu seulement : pose de parade (1re et 3e personne, main gauche ; logique de blocage en diagnostic), fissures, éclat,
la glace taillée avec et sans shader.
"""
import base64, io, json, math, os, re, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import numpy as np
from PIL import Image, ImageDraw
import objet

AVEC_E = True
NOM = "skin_bouclier_givre"
TEX = 512
TAU = 2 * math.pi
C = lambda *c: np.array(c, np.float32)
BLANC = C(244, 253, 255)
LUEUR = C(150, 226, 255)
G_LIGHT = C(214, 244, 255)
ARG_L, ARG_M, ARG_D = C(236, 244, 250), C(166, 186, 206), C(74, 90, 116)

# ------------------------------------------------------------------ forme de l'écu (vue de face, px du bloc, centre à l'origine)
W_HALF, Y_TOP, CH = 6.4, 10.2, 0.75       # demi-largeur, bord haut, chanfrein des coins
Y_SH, Y_PT = 1.4, -11.6                   # début des arcs, pointe
HINGE, ANG = 2.2, math.radians(15)        # arêtes des pales, repli des flancs
CA, SA = math.cos(ANG), math.sin(ANG)
U_S = (W_HALF - HINGE) / CA + 0.12        # largeur d'une pale de flanc (repère de la pale)
UMBO = np.array((0.0, 1.0))
# profondeurs le long de la normale de la pale (w = 0 : glace au bord ; la glace taillée monte au-dessus)
W_CORE = (-1.3, -0.65)                     # âme opaque
W_CRK = (-1.15, -0.85)                     # fissures cachées dans l'âme
CRACK_OUT = 0.4                            # sortie des fissures (devant l'âme, derrière la glace)
W_ORLE, R_ORLE, IN_ORLE = -0.45, 0.9, 0.1  # orle roulé : axe (profondeur), apothème, retrait vers l'intérieur
L_U = 0.9                                  # glace : surépaisseur autour de l'umbo
HEX_R = 2.05                               # sommets de l'anneau de l'umbo (rayon)
DENS = 11.0                                # âme, dos, fissures (texels / px)
DF_PEAU = 10.0                             # facettes de glace
TH = 0.3
EPS_PEAU = 0.05
Y0, Y1 = Y_PT - 0.1, Y_TOP + 0.1


def half_width(y):
    y = np.asarray(y, float)
    s = np.clip((Y_SH - y) / (Y_SH - Y_PT), 0, 1)
    arc = W_HALF * np.clip(1 - s ** 1.75, 0, 1) ** 0.6
    w = np.where(y > Y_SH, W_HALF, arc)
    w = np.where(y > Y_TOP - CH, W_HALF - (y - (Y_TOP - CH)), w)
    return np.where((y > Y_TOP) | (y < Y_PT), -1.0, w)


def outline_pts(n=900):
    """Contour fermé dense (sens horaire vu de face)."""
    ys = np.linspace(Y_TOP, Y_PT, n)
    right = np.stack([half_width(ys), ys], 1)
    left = right[::-1] * (-1, 1)
    top = np.stack([np.linspace(-W_HALF + CH, W_HALF - CH, 60), np.full(60, Y_TOP)], 1)
    return np.concatenate([top, right, left])


OUT = outline_pts()


def dist_outline(x, y):
    p = np.stack([np.ravel(x), np.ravel(y)], 1)
    d = np.full(len(p), 1e9)
    for k in range(0, len(OUT), 150):
        q = OUT[k:k + 150]
        d = np.minimum(d, np.sqrt(((p[:, None, :] - q[None]) ** 2).sum(-1)).min(1))
    return d.reshape(np.shape(x))


def hinge_y():
    lo, hi = Y_PT, Y_SH
    for _ in range(60):
        m = (lo + hi) / 2
        if half_width(m) > HINGE:
            hi = m
        else:
            lo = m
    return (lo + hi) / 2


Y_HINGE = hinge_y()

# pales : repère (O, X, N) ; un point (u, y, w) -> O + X u + Y y + N w
PANELS = {
    "c": (np.array((0.0, 0.0, 0.85)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 0.0, 1.0))),
    "d": (np.array((HINGE, 0.0, 0.85)), np.array((CA, 0.0, -SA)), np.array((SA, 0.0, CA))),
    "g": (np.array((-HINGE, 0.0, 0.85)), np.array((CA, 0.0, SA)), np.array((-SA, 0.0, CA))),
}
URANGE = {"c": (-HINGE, HINGE), "d": (0.0, U_S), "g": (-U_S, 0.0)}
URANGE_AME = {"c": (-HINGE - 0.12, HINGE + 0.12), "d": (-0.12, U_S), "g": (-U_S, 0.12)}   # l'âme passe sous l'arête
YV = np.array((0.0, 1.0, 0.0))


def P3(k, u, y, w):
    O, X, N = PANELS[k]
    return O + X * u + YV * y + N * w


def panel_of_x(x):
    return "c" if abs(x) <= HINGE + 1e-6 else ("d" if x > 0 else "g")


def surf(x, y, w):
    """Point du contour (x vu de face) sur la pale qui le porte, à la profondeur w."""
    k = panel_of_x(x)
    u = x if k == "c" else (abs(x) - HINGE) / CA * (1 if k == "d" else -1)
    return P3(k, u, y, w), k


def z_pale(x):
    """Profondeur z du plan w = 0 au-dessus de x (vu de face)."""
    return 0.85 - np.maximum(0.0, np.abs(x) - HINGE) * math.tan(ANG)


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


def noise(shape, cells, seed):
    r = np.random.default_rng(seed)
    a = (r.random((max(2, cells[0]), max(2, cells[1]))) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((shape[1], shape[0]), Image.BICUBIC), np.float32) / 255


_VN = {}


def vnoise(x, y, cell, seed):
    """Bruit de valeur continu en coordonnées de l'écu (les facettes voisines se raccordent)."""
    if (cell, seed) not in _VN:
        _VN[(cell, seed)] = np.random.default_rng(seed).random((int(40 / cell) + 4, int(40 / cell) + 4))
    V = _VN[(cell, seed)]
    gx, gy = (np.asarray(x) + 20) / cell, (np.asarray(y) + 20) / cell
    i, j = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - i, gy - j
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = lerp(V[i, j], V[i + 1, j], fx)
    b = lerp(V[i, j + 1], V[i + 1, j + 1], fx)
    return lerp(a, b, fy)


# ------------------------------------------------------------------ fissures (communes aux pales : tracées dans le plan de face)
def crack_lines():
    r = np.random.default_rng(41)
    lines = []
    for k, a0 in enumerate((95, 35, -20, -70, -110, -160, 150, 205)):
        a = math.radians(a0 + r.uniform(-8, 8))
        p = UMBO + 2.35 * np.array((math.cos(a), math.sin(a)))
        pl = [p.copy()]
        L = r.uniform(4.0, 7.5) if k not in (0,) else 4.0
        step = 0
        while step < L:
            a += r.uniform(-0.45, 0.45)
            ln = r.uniform(0.6, 1.1)
            p = p + ln * np.array((math.cos(a), math.sin(a)))
            pl.append(p.copy())
            step += ln
            if r.random() < 0.35:
                a2 = a + r.choice([-1, 1]) * r.uniform(0.6, 1.1)
                q = p + r.uniform(0.6, 1.2) * np.array((math.cos(a2), math.sin(a2)))
                lines.append(([p.copy(), q], 3))
        lines.append((pl, 4))
    return lines


CRACKS = crack_lines()


# ------------------------------------------------------------------ peinture des pales (âme, dos, fissures)
def panel_grid(kind, ss=3, ur=URANGE):
    u0, u1 = ur[kind if kind == "c" else "d"]
    Wt, Ht = int(math.ceil((u1 - u0) * DENS)), int(math.ceil((Y1 - Y0) * DENS))
    GW, GH = Wt * ss, Ht * ss
    jj, ii = np.mgrid[0:GH, 0:GW]
    u = u0 + (ii + 0.5) / GW * (u1 - u0)
    y = Y1 - (jj + 0.5) / GH * (Y1 - Y0)
    x = u if kind == "c" else HINGE + u * CA
    return Wt, Ht, ss, u, x, y, (u0, u1)


def reduce(c, al, inside, Wt, Ht, ss, fill):
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((Wt, Ht), Image.LANCZOS))
    ins = inside.reshape(Ht, ss, Wt, ss).mean(axis=(1, 3)) > 0.5
    alv = np.array(Image.fromarray(np.clip(al, 0, 255).astype(np.uint8), "L").resize((Wt, Ht), Image.BOX))
    out = np.dstack([rgb, np.where(ins, alv, 0)]).astype(np.uint8)
    out[~ins, :3] = fill
    return out


def paint_core(kind, back=False):
    Wt, Ht, ss, u, x, y, _ = panel_grid(kind, ur=URANGE_AME)
    inside = half_width(y) + 0.12 >= np.abs(x)
    r = np.hypot(x - UMBO[0], y - UMBO[1])
    d = dist_outline(x, y)
    nz = noise(x.shape, (int(x.shape[0] / 12), int(x.shape[1] / 6)), 21 if kind == "c" else 22)
    if not back:
        # âme vue à travers la glace : bleu nuit, lueur froide autour de l'umbo, veines plus sombres
        c = lerp(np.array((14, 34, 74.)), np.array((46, 112, 170.)), np.exp(-r / 3.2)[..., None])
        c *= (0.9 + 0.2 * nz)[..., None]
    else:
        # dos : glace sombre polie, plus claire au centre, liseré de givre près de l'orle, grain vertical
        c = lerp(np.array((70, 112, 158.)), np.array((28, 50, 90.)), (np.clip(r / 11, 0, 1) ** 1.2)[..., None])
        grain = noise(x.shape, (max(2, int(x.shape[0] / 60)), max(2, int(x.shape[1] / 4))), 23 if kind == "c" else 24)
        c *= (0.95 + 0.1 * grain)[..., None]
        fine = noise(x.shape, (int(x.shape[0] / 5), int(x.shape[1] / 5)), 25 if kind == "c" else 26)
        lace = d < 1.2 + 0.25 * nz
        plume = (d < 1.9 * nz + 0.9) & (fine > 0.64) & ~lace
        c = np.where(plume[..., None], lerp(c, np.array((206, 232, 248.)), 0.5), c)
        c = np.where(lace[..., None], np.array((214, 236, 250.)), c)
    return reduce(c, np.full(x.shape, 255.0), inside, Wt, Ht, ss, (20, 40, 80))


def paint_crack(kind):
    Wt, Ht, ss, u, x, y, (u0, u1) = panel_grid(kind)
    GW, GH = Wt * ss, Ht * ss

    def to_px(p):
        px, py = p
        uu = px if kind == "c" else (px - HINGE) / CA
        return ((uu - u0) / (u1 - u0) * GW, (Y1 - py) / (Y1 - Y0) * GH)
    m, core = Image.new("L", (GW, GH), 0), Image.new("L", (GW, GH), 0)
    dm, dc = ImageDraw.Draw(m), ImageDraw.Draw(core)
    for pl, wdt in CRACKS:
        pts = [to_px(p) for p in pl]
        dm.line(pts, fill=255, width=wdt * ss)
        if wdt >= 4:
            dc.line(pts, fill=255, width=ss)
    lines = np.array(m) > 127
    inside = half_width(y) - 1.05 >= np.abs(x)
    if kind != "c":
        inside &= u > 0.25
    else:
        inside &= np.abs(u) < HINGE - 0.15
    sel = lines & inside
    c = np.where((np.array(core) > 127)[..., None], np.array((200, 246, 255.)), np.array((236, 250, 255.)))
    out = reduce(c * np.ones(x.shape + (3,)), np.full(x.shape, 255.0), sel, Wt, Ht, ss, (220, 240, 255))
    ce = np.array(core.resize((Wt, Ht), Image.BOX)) > 60
    e = np.zeros_like(out)
    e[ce & (out[..., 3] > 0)] = (140, 222, 255, 255)
    return out, e


# ------------------------------------------------------------------ tuiles, cubes et groupes différés
TILES, TRANS_TILES = {}, set()
CUBES, GROUPES, NORMALE = [], [], {}
SIX = ("north", "south", "east", "west", "up", "down")


def tuile(nom, rgba, e=None, trans=False):
    if nom in TILES:
        return nom
    TILES[nom] = (rgba, e)
    if trans:
        TRANS_TILES.add(nom)
    return nom


def finir(col, al, em, masque):
    """alpha : None = opaque (0/255 par le masque), sinon 1..254 dans le masque (peau trans_)."""
    rgba = np.zeros(col.shape[:2] + (4,), np.uint8)
    rgba[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    rgba[..., 3] = (np.clip(al, 1, 254).astype(np.uint8) if al is not None else 255) * masque
    rgba[~masque] = 0
    e = None
    if em is not None:
        on = masque & (em.max(axis=-1) > 0)
        if on.any():
            e = np.zeros_like(rgba)
            e[..., :3] = np.clip(em, 0, 225).astype(np.uint8)
            e[..., 3] = on * 255
            e[~on] = 0
    return rgba, e


def grp(nom, pivot, parent):
    GROUPES.append((nom, np.asarray(pivot, float), parent))
    return nom


def add_cube(g, nom, c, R, half, faces):
    """faces : {face: tuile | (tuile, True) pour une tuile retournée} ; les autres faces sont transparentes."""
    CUBES.append({"groupe": g, "nom": nom, "c": np.asarray(c, float), "R": R, "half": np.asarray(half, float), "faces": faces})


def frame(X, Y):
    X = unit(X)
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    return np.column_stack([X, Y, np.cross(X, Y)])


def oriented(g, nom, c, X, Y, half, faces):
    add_cube(g, nom, c, frame(X, Y), half, faces)


def points_face(c, R, s, face, dens):
    X, Y, Z = R[:, 0], R[:, 1], R[:, 2]
    sx, sy, sz = s
    dims = {"south": (sx, sy), "north": (sx, sy), "down": (sx, sz), "up": (sx, sz), "east": (sz, sy), "west": (sz, sy)}[face]
    W, H = max(2, int(round(dims[0] * dens))), max(2, int(round(dims[1] * dens)))
    U_, V_ = np.meshgrid((np.arange(W) + 0.5) / W, (np.arange(H) + 0.5) / H)
    assert face == "south"
    x, y, z = -sx / 2 + U_ * sx, sy / 2 - V_ * sy, np.full_like(U_, sz / 2)
    return c + x[..., None] * X + y[..., None] * Y + z[..., None] * Z


# ------------------------------------------------------------------ tuiles unies (argent, glace, cuir)
def strip_tile(base, light, dark, W=96, H=24, seed=1, line=None):
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W]
    q = (yy + 0.5) / H
    c = lerp(np.array(light, np.float32), np.array(dark, np.float32), (q ** 1.1)[..., None])
    c = lerp(c, np.array(base, np.float32), 0.45)
    c *= (1 + 0.05 * np.sin(xx * 0.7 + r.uniform(0, 6)) * np.sin(yy * 0.4))[..., None]
    if line is not None:
        c[int(H * 0.38):int(H * 0.38) + 3] = line
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(c, 0, 255)
    out[..., 3] = 255
    return out


def cap_tile(light, dark, n=24):
    yy, xx = np.mgrid[0:n, 0:n]
    u, v = (xx + 0.5) / n - 0.5, (yy + 0.5) / n - 0.5
    k = np.where(np.abs(u) > np.abs(v), np.where(u < 0, 0.15, 0.7), np.where(v < 0, 0.0, 0.9))
    c = lerp(np.array(light, np.float32), np.array(dark, np.float32), k[..., None])
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = c
    out[..., 3] = 255
    return out


def t_orle(W=128, H=12):
    """Argent froid roulé : clair au milieu de chaque pan, arête claire, givre en points blancs."""
    r = np.random.default_rng(12)
    yy, xx = np.mgrid[0:H, 0:W]
    q = (yy + 0.5) / H
    c = lerp(ARG_M, ARG_L, np.clip(1 - np.abs(q - 0.45) * 2, 0, 1)[..., None] ** 0.8)
    c *= (1 + 0.035 * np.sin(xx * 0.5 + r.uniform(0, 6)))[..., None]
    c[(q < 0.12)] = ARG_D * 1.2
    gv = r.random((H, W)) > 0.93
    c[gv & (q > 0.2)] = lerp(c[gv & (q > 0.2)], BLANC, 0.7)
    return tuile("orle", *finir(c, None, None, np.ones((H, W), bool)))


def t_nervure(W=96, H=12):
    yy, xx = np.mgrid[0:H, 0:W]
    q = (yy + 0.5) / H
    c = lerp(G_LIGHT, C(110, 196, 236), np.abs(q - 0.5)[..., None] * 2)
    c[np.abs(q - 0.5) < 0.12] = BLANC
    em = np.zeros_like(c)
    em[np.abs(q - 0.5) < 0.12] = LUEUR
    return tuile("nervure", *finir(c, None, em, np.ones((H, W), bool)))


def cuir_tile(W=128, H=16):
    r = np.random.default_rng(5)
    yy, xx = np.mgrid[0:H, 0:W]
    f = ((xx + yy * 0.9) / 14.0) % 1.0
    c = lerp(np.array((44, 56, 104.)), np.array((16, 20, 44.)), f[..., None])
    c = np.where((f > 0.86)[..., None], np.array((8, 10, 24.)), c)
    c *= r.uniform(0.95, 1.05, (H, W))[..., None]
    for x in range(3, W - 4, 10):
        c[6:10, x:x + 5] = (176, 196, 220)
    return c


def eclat_tile(n=64):
    """Éclat additif : étoile à six rais, cœur blanc bleuté, fond noir (invisible en add_)."""
    yy, xx = np.mgrid[0:n, 0:n]
    u, v = (xx + 0.5) / n * 2 - 1, (yy + 0.5) / n * 2 - 1
    r = np.hypot(u, v)
    a = np.arctan2(v, u)
    rays = np.abs(np.cos(3 * a)) ** 24 * np.clip(1 - r, 0, 1) ** 1.2
    glow = np.exp(-(r / 0.28) ** 2)
    k = np.clip(rays * 0.9 + glow, 0, 1)
    return np.array((150, 226, 255.)) * k[..., None] + np.array((70, 30, 0.)) * glow[..., None]


# ------------------------------------------------------------------ tours (pièces rondes : couronnes de pans, skin_epee_givre)
OVL, OVW, DF_T = 0.04, 0.03, 16.0


def p_argent(xn, t, ex):
    k = np.clip(0.45 + 0.3 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + ex.get("pointe", 0.0) * t, 0, 1)
    col = lerp(ARG_D, ARG_L, (k ** 1.2)[..., None]) * (1 + 0.03 * np.sin(t * 37 + xn * 3))[..., None]
    col = np.where((np.abs(xn) > 0.86)[..., None], np.minimum(col * 1.14 + 10, 255), col)
    if ex.get("givre"):
        col = np.where(((t > 0.82) & (np.abs(xn) < 0.75))[..., None], lerp(col, BLANC, 0.6), col)
    return col, None


def p_glace(xn, t, ex):
    k = np.clip(0.35 + 0.35 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + 0.25 * t, 0, 1)
    col = lerp(C(40, 110, 176), G_LIGHT, (k ** 1.1)[..., None])
    col = np.where((np.abs(xn) > 0.84)[..., None], BLANC, col)
    em = np.zeros(col.shape, np.float32)
    if ex.get("e"):
        ln = np.abs(xn) < 0.16
        col[ln] = lerp(col[ln], C(200, 248, 255), 0.7)
        em[ln] = LUEUR
    return col, em


def p_pale(xn, t, ex):
    """Glace pâle de l'umbo : presque blanche, arêtes blanches, un peu plus sombre vers la base."""
    k = np.clip(0.55 + 0.3 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + 0.15 * t, 0, 1)
    col = lerp(C(96, 170, 214), C(238, 250, 255), (k ** 1.2)[..., None])
    col = np.where((np.abs(xn) > 0.86)[..., None], BLANC, col)
    return col, None


def p_gemme(xn, t, ex):
    k = np.clip(0.4 + 0.4 * (1 - np.abs(xn)) + 0.2 * t + ex.get("clair", 0.0), 0, 1)
    col = lerp(C(40, 130, 210), C(170, 236, 255), k[..., None])
    return col, np.clip(col * 0.8, 0, 200)


PEINTRES = {"argent": p_argent, "glace": p_glace, "pale": p_pale, "gemme": p_gemme}


def tuile_pan(nom, mat, L, w0, w1, ex):
    if nom in TILES:
        return nom
    wm = max(w0, w1) + 2 * OVW
    Lf = L + 2 * OVL
    Wt, Ht = max(2, int(math.ceil(wm * DF_T))), max(2, int(math.ceil(Lf * DF_T)))
    yy, xx = np.mgrid[0:Ht, 0:Wt]
    x = ((xx + 0.5) / Wt - 0.5) * wm
    y = Lf * (1 - (yy + 0.5) / Ht) - OVL
    t = np.clip(y / max(L, 1e-6), 0, 1)
    hw = (w0 + (w1 - w0) * t) / 2 + OVW
    mask = np.abs(x) <= hw
    xn = np.clip(x / np.maximum(hw - OVW, 1e-3), -1, 1)
    col, em = PEINTRES[mat](xn, t, ex)
    return tuile(nom, *finir(col, None, em, mask))


def tour(g, nom, O, ax, ref, profil, n=6, phase=0.0, cle=None):
    """profil = [(b0, r0, b1, r1, [(mat, ex), ...]), ...] le long de ax (rayon = apothème) ; matières alternées par pan.
    Chaque pan : plaque de TH px, face extérieure (south) sur la surface, autres faces transparentes. `cle` : nom des tuiles
    (partagées entre les copies et entre cristaux de même taille)."""
    O, ax = np.asarray(O, float), unit(ax)
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    cle = cle or nom
    for i, (b0, r0, b1, r1, mats) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        tiles = [tuile_pan(f"{cle}{i}{'abcd'[j]}", m, L, 2 * r0 * tn, 2 * r1 * tn, ex) for j, (m, ex) in enumerate(mats)]
        db, dr = (b1 - b0) / L, (r1 - r0) / L
        wm = max(2 * r0 * tn, 2 * r1 * tn) + 2 * OVW
        for k in range(n):
            th = phase + TAU * k / n
            e = math.cos(th) * ref + math.sin(th) * w3
            Pa, Pb = O + b0 * ax + r0 * e, O + b1 * ax + r1 * e
            Y = unit(Pb - Pa)
            N = -dr * ax + db * e
            X = np.cross(Y, N)
            c = (Pa + Pb) / 2 - N * TH / 2
            add_cube(g, f"{nom}{i}_{k}", c, np.column_stack([X, Y, N]), (wm / 2, L / 2 + OVL, TH / 2), {"south": tiles[k % len(tiles)]})


def t_disque(nom, n, Ra, N=48):
    """Couvercle en polygone régulier (apothème Ra) : glace pâle givrée, anneau blanc, bord d'argent, découpé par l'alpha."""
    if nom in TILES:
        return nom
    R = Ra / math.cos(math.pi / n)
    yy, xx = np.mgrid[0:N, 0:N]
    x = ((xx + 0.5) / N - 0.5) * 2 * R
    y = (0.5 - (yy + 0.5) / N) * 2 * R
    th = np.arctan2(y, x) - math.pi / 2
    sect = np.round(th / (TAU / n)) * (TAU / n) + math.pi / 6
    apo = x * np.cos(sect + math.pi / 2) + y * np.sin(sect + math.pi / 2)
    mask = apo <= Ra
    rr = apo / Ra
    col = lerp(C(236, 250, 255), C(150, 206, 236), rr[..., None] ** 1.5)
    col[(rr > 0.74) & (rr < 0.82)] = BLANC
    col[rr > 0.93] = ARG_M
    return tuile(nom, *finir(col, None, None, mask))


def disque(g, nom, c, Nrm, up, Ra, tile, n=6):
    Nrm = unit(Nrm)
    Y = unit(up - (up @ Nrm) * Nrm)
    X = np.cross(Y, Nrm)
    R = Ra / math.cos(math.pi / n)
    add_cube(g, nom, np.asarray(c, float) - Nrm * TH / 2, np.column_stack([X, Y, Nrm]), (R, R, TH / 2), {"south": tile})


def barre(g, nom, p, q, r, ref, faces, Rang=45.0):
    """Barre de section carrée 2r tournée de Rang degrés autour de son axe (45 : section en losange)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = np.asarray(ref, float)
    Y0 = unit(ref - (ref @ X) * X)
    Z0 = np.cross(X, Y0)
    a = math.radians(Rang)
    Y = math.cos(a) * Y0 + math.sin(a) * Z0
    add_cube(g, nom, (p + q) / 2, np.column_stack([X, Y, np.cross(X, Y)]), (np.linalg.norm(q - p) / 2, r, r), faces)


def bar8(g, nom, p, q, r, tile, ref, e0=0.03, e1=0.03, cap=None):
    """Octogone régulier d'apothème r : 4 plaques à 0, 45, 90, 135° ; bouts prolongés de e0 / e1 (onglets)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    p, q = p - X * e0, q + X * e1
    L = np.linalg.norm(q - p)
    ref = np.asarray(ref, float)
    Y0 = unit(ref - (ref @ X) * X)
    Z0 = np.cross(X, Y0)
    a_ = r * math.tan(math.pi / 8) * 1.02
    for k in range(4):
        gk = math.pi / 4 * k
        Yk = math.cos(gk) * Y0 + math.sin(gk) * Z0
        d = 0.02 * k
        f = {"up": tile, "down": tile}
        if cap:
            f.update(east=cap, west=cap)
        add_cube(g, nom + "abcd"[k], (p + q) / 2, np.column_stack([X, Yk, np.cross(X, Yk)]), ((L - 2 * d) / 2, r, a_), f)


GLACE_ALT = [("glace", {"clair": 0.12, "e": True}), ("glace", {"clair": -0.1})]


def cristal(g, nom, base, d, r, L, ref, cle):
    """Cristal hexagonal pointu (tour de 6 pans) : pied un peu rentré, fût, pointe."""
    tl = min(L * 0.45, r * 1.9)
    tour(g, nom, base, d, ref, [(0.0, r * 0.82, 0.22, r, GLACE_ALT), (0.22, r, L - tl, r, GLACE_ALT), (L - tl, r, L, 0.0, GLACE_ALT)],
         n=6, phase=math.pi / 6, cle=cle)


# ------------------------------------------------------------------ glace taillée : surface triangulée (umbo -> arêtes -> orle)
def outline_vertices():
    """Sommets de l'orle (x, y vus de face), sens horaire, avec un sommet sur chaque arête de pale (repli)."""
    right = [(W_HALF - CH, Y_TOP), (W_HALF, Y_TOP - CH), (W_HALF, Y_SH + 4.2), (W_HALF, Y_SH)]
    for s in (0.2, 0.38, 0.54, 0.68, 0.8):
        y = Y_SH - s * (Y_SH - Y_PT)
        right.append((float(half_width(y)), y))
    right.append((HINGE, Y_HINGE))
    yv = Y_PT + 0.45 * (Y_HINGE - Y_PT)
    right.append((float(half_width(yv)), yv))
    top = [(-W_HALF + CH, Y_TOP), (-HINGE, Y_TOP), (0.0, Y_TOP), (HINGE, Y_TOP)]
    left = [(-x, y) for x, y in reversed(right[1:])]
    return top + right + [(0.0, Y_PT)] + left


OUTV = outline_vertices()


def inside_shape(p):
    return half_width(p[1]) >= abs(p[0])


def rim_dist(ang):
    """Distance de l'umbo au contour dans la direction ang."""
    d = np.array((math.cos(ang), math.sin(ang)))
    lo, hi = 0.0, 30.0
    for _ in range(50):
        m = (lo + hi) / 2
        if inside_shape(UMBO + d * m):
            lo = m
        else:
            hi = m
    return lo


def hex_dist(ang):
    """Distance de l'umbo au bord de l'anneau hexagonal (sommets à 90 + 60k degrés)."""
    a = (math.degrees(ang) - 90) % 60 - 30
    return HEX_R * math.cos(math.radians(30)) / math.cos(math.radians(a))


def lift_of(p):
    v = np.asarray(p, float) - UMBO
    r = float(np.hypot(*v))
    if r < 1e-6:
        return L_U
    ang = math.atan2(v[1], v[0])
    h, R = hex_dist(ang), rim_dist(ang)
    s = np.clip((r - h) / max(R - h, 1e-3), 0, 1)
    return L_U * (1 - s ** 1.5)


VERTS, LIFT = [], []


def vtx(p, lift):
    for i, q in enumerate(VERTS):
        if math.hypot(q[0] - p[0], q[1] - p[1]) < 1e-6:
            return i
    VERTS.append((float(p[0]), float(p[1])))
    LIFT.append(float(lift))
    return len(VERTS) - 1


RIM = [vtx(p, 0.0) for p in OUTV]
CENTRE = vtx(UMBO, L_U)
HEXV = [vtx(UMBO + HEX_R * np.array((math.cos(math.radians(90 + 60 * k)), math.sin(math.radians(90 + 60 * k)))), L_U) for k in range(6)]
HY = (7.4, 4.6, 1.0, -2.6, -5.6, -8.2)
HINGE_V = {}
for sx in (1, -1):
    HINGE_V[sx] = [vtx((sx * HINGE, y), min(lift_of((sx * HINGE, y)) + 0.14, 0.8)) for y in HY]
STAR = []
for j, (a, f, dl) in enumerate(((90, 0.52, 0.10), (270, 0.42, 0.10), (0, 0.55, 0.1), (38, 0.55, -0.08), (-38, 0.5, -0.08),
                                (-68, 0.56, 0.06), (180, 0.55, 0.1), (142, 0.55, -0.08), (218, 0.5, -0.08), (248, 0.56, 0.06),
                                (64, 0.55, 0.0), (116, 0.55, 0.0))):
    ang = math.radians(a)
    h, R = hex_dist(ang), rim_dist(ang)
    p = UMBO + np.array((math.cos(ang), math.sin(ang))) * (h + f * (R - h))
    if abs(abs(p[0]) - HINGE) < 0.6:
        continue
    STAR.append(vtx(p, lift_of(p) + dl))


def incircle(a, b, c, d):
    m = np.array([[a[0] - d[0], a[1] - d[1], (a[0] - d[0]) ** 2 + (a[1] - d[1]) ** 2],
                  [b[0] - d[0], b[1] - d[1], (b[0] - d[0]) ** 2 + (b[1] - d[1]) ** 2],
                  [c[0] - d[0], c[1] - d[1], (c[0] - d[0]) ** 2 + (c[1] - d[1]) ** 2]])
    return np.linalg.det(m)


def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def delaunay(ids):
    """Bowyer-Watson sur les sommets ids (région convexe) ; triangles en sens direct."""
    P = [VERTS[i] for i in ids] + [(-300.0, -300.0), (300.0, -300.0), (0.0, 300.0)]
    n = len(ids)
    tris = [(n, n + 1, n + 2)]
    for i in range(n):
        p = P[i]
        bad = [t for t in tris if incircle(P[t[0]], P[t[1]], P[t[2]], p) > 1e-9]
        cnt = {}
        for t in bad:
            for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                k = tuple(sorted(e))
                cnt[k] = cnt.get(k, 0) + 1
        bord = [(a, b) for t in bad for (a, b) in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])) if cnt[tuple(sorted((a, b)))] == 1]
        tris = [t for t in tris if t not in bad] + [(a, b, i) for a, b in bord]
    out = []
    for t in tris:
        if max(t) >= n:
            continue
        a, b, c = (ids[k] for k in t)
        if orient(VERTS[a], VERTS[b], VERTS[c]) < 0:
            b, c = c, b
        out.append((a, b, c))
    return out


def poly_area(ids):
    pts = np.array([VERTS[i] for i in ids])
    return 0.5 * abs(np.dot(pts[:, 0], np.roll(pts[:, 1], -1)) - np.dot(pts[:, 1], np.roll(pts[:, 0], -1)))


FACETS = []
for nom_r, test in (("c", lambda p: abs(p[0]) <= HINGE + 1e-6), ("d", lambda p: p[0] >= HINGE - 1e-6), ("g", lambda p: p[0] <= -HINGE + 1e-6)):
    ids = [i for i, p in enumerate(VERTS) if test(p)]
    tr = delaunay(ids)
    bord = [i for i in RIM if test(VERTS[i])]
    if nom_r == "c":
        bord = bord + HINGE_V[1] + HINGE_V[-1]
    else:
        bord = bord + HINGE_V[1 if nom_r == "d" else -1]
    # aire du contour de la région (enveloppe convexe des sommets de bord)
    pts = np.array([VERTS[i] for i in ids])
    cen = pts.mean(0)
    ordre = sorted(bord, key=lambda i: math.atan2(VERTS[i][1] - cen[1], VERTS[i][0] - cen[0]))
    a_tri = sum(abs(orient(VERTS[a], VERTS[b], VERTS[c])) / 2 for a, b, c in tr)
    a_reg = poly_area(ordre)
    mins = min(abs(orient(VERTS[a], VERTS[b], VERTS[c])) / 2 for a, b, c in tr)
    print(f"région {nom_r} : {len(ids)} sommets, {len(tr)} facettes, aire {a_tri:.3f} / {a_reg:.3f} px², plus petite {mins:.3f}")
    assert abs(a_tri - a_reg) < 1e-3, "triangulation incomplète"
    assert mins > 0.02, "facette dégénérée"
    FACETS += tr

EDGES = {}
for fi, (a, b, c) in enumerate(FACETS):
    for e in ((a, b), (b, c), (c, a)):
        EDGES.setdefault(tuple(sorted(e)), []).append(fi)
assert all(len(v) <= 2 for v in EDGES.values())


def P_front(i):
    x, y = VERTS[i]
    return np.array((x, y, float(z_pale(x)) + LIFT[i]))


# contrôle : chaque arête de repli est une arête de la triangulation (la nervure suit la crête)
for sx in (1, -1):
    ch = [vtx((sx * HINGE, Y_TOP), 0)] + HINGE_V[sx] + [vtx((sx * HINGE, Y_HINGE), 0)]
    for a, b in zip(ch, ch[1:]):
        assert tuple(sorted((a, b))) in EDGES, "arête de repli absente"


def peau_facette(fi):
    """Peinture d'une facette (glace trans_) : fonction des points P (H, W, 3) -> (col, alpha, em, masque)."""
    a, b, c = FACETS[fi]
    tri = [np.array(VERTS[k]) for k in (a, b, c)]
    aretes = []
    for (i0, i1), (p, q) in zip(((a, b), (b, c), (c, a)), ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0]))):
        voisins = [f for f in EDGES[tuple(sorted((i0, i1)))] if f != fi]
        tol = 0.25 if not voisins else (EPS_PEAU if voisins[0] < fi else 0.0)
        aretes.append((p, q, tol, bool(voisins)))
    tint = 1.0 + 0.06 * math.sin(fi * 2.399)

    def f(P):
        x, y = P[..., 0], P[..., 1]
        m = np.ones(x.shape, bool)
        d_int = np.full(x.shape, 9.0)
        for p, q, tol, interne in aretes:
            t = q - p
            dd = (t[0] * (y - p[1]) - t[1] * (x - p[0])) / np.linalg.norm(t)
            m &= dd >= -tol
            if interne:
                d_int = np.minimum(d_int, np.abs(dd))
        dx, dy = x - UMBO[0], y - UMBO[1]
        r = np.hypot(dx, dy)
        kb = np.clip((UMBO[1] - y) / (UMBO[1] - Y_PT), 0, 1)[..., None]
        kt = np.clip((y - UMBO[1]) / (Y_TOP - UMBO[1]), 0, 1)[..., None]
        pale, body, deep, top = C(176, 232, 250), C(104, 198, 236), C(34, 98, 168), C(132, 212, 242)
        col = lerp(pale, body, np.clip(r / 4.0, 0, 1)[..., None])
        col = lerp(col, deep, kb ** 1.3 * 0.85)
        col = lerp(col, top, kt * 0.5)
        col = col * tint * (0.94 + 0.12 * vnoise(x, y, 1.4, 3))[..., None]
        al = 205 - 40 * np.clip(r / 11, 0, 1)
        # arêtes de la taille : filet blanc (au moins un texel)
        ed = d_int < 0.09
        col = np.where(ed[..., None], lerp(col, C(230, 248, 255), 0.45), col)
        al = np.where(ed, al + 18, al)
        # givre en plumes le long de l'orle (blanc mat, plus opaque), aiguilles vers l'intérieur
        d = dist_outline(x, y)
        nz = vnoise(x, y, 1.1, 7)
        fine = vnoise(x, y, 0.32, 9)
        lace = d < 1.12 + 0.3 * nz
        plume = (d < 1.8 * nz + 1.15) & (fine > 0.6) & ~lace
        col = np.where(plume[..., None], lerp(col, C(226, 244, 255), 0.75), col)
        al = np.where(plume, 212, al)
        col = np.where(lace[..., None], C(240, 251, 255), col)
        al = np.where(lace, 228, al)
        return col, np.clip(al, 150, 228), None, m
    return f


def facette(g, fi):
    a, b, c = FACETS[fi]
    A, B, Cc = P_front(a), P_front(b), P_front(c)
    n = unit(np.cross(B - A, Cc - A))
    assert n[2] > 0.5
    X = unit(np.array((1.0, 0.0, 0.0)) - n[0] * n)
    Y = np.cross(n, X)
    R = np.column_stack([X, Y, n])
    loc = np.array([[(P - A) @ X, (P - A) @ Y] for P in (A, B, Cc)])
    lo, hi = loc.min(0) - 0.3, loc.max(0) + 0.3
    mid = A + X * (lo[0] + hi[0]) / 2 + Y * (lo[1] + hi[1]) / 2
    s = (hi[0] - lo[0], hi[1] - lo[1], TH)
    cc = mid - n * TH / 2
    nom = f"facette{fi:03d}"
    if nom + "_south" not in TILES:
        col, al, em, m = peau_facette(fi)(points_face(cc, R, s, "south", DF_PEAU))
        tuile(nom + "_south", *finir(col, al, em, m), trans=True)
    add_cube(g, nom, cc, R, np.array(s) / 2, {"south": nom + "_south"})


# ------------------------------------------------------------------ tuiles de l'âme, du dos, des fissures, du flocon
for k in ("c", "s"):
    kk = "c" if k == "c" else "d"
    tuile(f"core_{k}", paint_core(kk))
    tuile(f"back_{k}", paint_core(kk, back=True))
    tuile(f"crk_{k}", *paint_crack(kk))
AL_, AM_, AD_ = (236, 244, 250), (166, 186, 206), (74, 90, 116)
tuile("argent_h", strip_tile(AM_, AL_, AM_, seed=2, line=(250, 253, 255)))
tuile("argent_b", strip_tile(AM_, AM_, AD_, seed=3))
tuile("argent_cap", cap_tile(AL_, AD_))
tuile("cuir", *finir(cuir_tile(), None, None, np.ones((16, 128), bool)))
tuile("cuir_cap", cap_tile((50, 62, 110), (14, 18, 40), 16))
tuile("eclat", *finir(eclat_tile(), None, None, np.ones((64, 64), bool)))
t_orle()
t_nervure()
BRAS = tuile("bras", *finir(lerp(ARG_L, ARG_M, np.linspace(0, 1, 8)[:, None, None] * np.ones((8, 32, 1))), None, None, np.ones((8, 32), bool)))
BRAS_B = tuile("bras_bout", *finir(np.ones((8, 8, 3)) * BLANC, None, None, np.ones((8, 8), bool)))


# ------------------------------------------------------------------ construction d'une copie de l'écu
def build_ecu(sfx, parent, bloque):
    G = {}
    ecu = grp(f"ecu_{sfx}", (0, 0, 0), parent)
    # glace taillée : facettes trans_
    gl = grp(f"trans_glace_{sfx}", (0, 0, 0), ecu)
    for fi in range(len(FACETS)):
        facette(gl, fi)
    # âme : une plaque par pale (face avant vue à travers la glace, dos) ; fissures cachées dans son épaisseur
    am = grp(f"ame_{sfx}", (0, 0, 0), ecu)
    G["fiss"] = []
    for k in ("c", "d", "g"):
        O, X, N = PANELS[k]
        t = "c" if k == "c" else "s"
        ym, hy = (Y0 + Y1) / 2, (Y1 - Y0) / 2
        u0, u1 = URANGE_AME[k]
        um, hu = (u0 + u1) / 2, (u1 - u0) / 2
        fr = (lambda n: n) if k != "g" else (lambda n: (n, True))
        bk = (lambda n: (n, True)) if k != "g" else (lambda n: n)
        oriented(am, f"ame_{k}", P3(k, um, ym, sum(W_CORE) / 2), X, YV, (hu, hy, (W_CORE[1] - W_CORE[0]) / 2),
                 {"south": fr(f"core_{t}"), "north": bk(f"back_{t}")})
        u0, u1 = URANGE[k]
        um, hu = (u0 + u1) / 2, (u1 - u0) / 2
        fg = grp(f"fissure_{k}_{sfx}", P3(k, um, ym, W_CRK[0]), ecu)
        NORMALE[fg] = N
        G["fiss"].append(fg)
        oriented(fg, f"fissure_{k}", P3(k, um, ym, sum(W_CRK) / 2), X, YV, (hu, hy, (W_CRK[1] - W_CRK[0]) / 2),
                 {"south": fr(f"crk_{t}")})
    # orle roulé : barre octogonale le long du contour (sommets rentrés de IN_ORLE, axe à la profondeur W_ORLE)
    orle = grp(f"orle_{sfx}", (0, 0, 0), ecu)
    n = len(OUTV)
    P2 = [np.array(p, float) for p in OUTV]
    pts3, nrm3 = [], []
    for i in range(n):
        a, b, c = P2[i - 1], P2[i], P2[(i + 1) % n]
        bis = unit(unit(a - b) + unit(c - b)) if abs(orient(a, b, c)) > 1e-6 else np.array((-(c - a)[1], (c - a)[0])) / np.linalg.norm(c - a)
        if not inside_shape(b + bis * 0.3):
            bis = -bis
        q = b + bis * IN_ORLE
        p3, k = surf(q[0], q[1], W_ORLE)
        pts3.append(p3)
        nrm3.append(PANELS[k][2])
    for i in range(n):
        p, q = pts3[i], pts3[(i + 1) % n]
        pp, qn = pts3[i - 1], pts3[(i + 2) % n]
        d = unit(q - p)
        t0 = math.acos(np.clip(unit(p - pp) @ d, -1, 1))
        t1 = math.acos(np.clip(d @ unit(qn - q), -1, 1))
        ref = unit(nrm3[i] + nrm3[(i + 1) % n])
        bar8(orle, f"orle{i:02d}", p, q, R_ORLE, "orle", ref, e0=R_ORLE * math.tan(t0 / 2) + 0.03,
             e1=R_ORLE * math.tan(t1 / 2) + 0.03, cap="argent_cap")
    # crêtes de repli : nervures de glace en losange posées sur l'arête de la taille
    for sx in (1, -1):
        ch = [vtx((sx * HINGE, Y_TOP), 0)] + HINGE_V[sx] + [vtx((sx * HINGE, Y_HINGE), 0)]
        fn = {f: "nervure" for f in ("south", "north", "up", "down")}
        for j, (a, b) in enumerate(zip(ch, ch[1:])):
            pa, pb = P_front(a), P_front(b)
            dd = unit(pb - pa)
            barre(ecu, f"nervure_{'d' if sx > 0 else 'g'}{j}", pa - dd * 0.1 + np.array((0, 0, 0.02)), pb + dd * 0.1 + np.array((0, 0, 0.02)),
                  0.17, (1, 0, 0), fn)
    # umbo bombé : tour hexagonale (collet d'argent, pentes de glace pâle), couvercle givré, flocon en relief, gemme
    z0 = 0.85 + L_U - 0.22
    O = np.array((UMBO[0], UMBO[1], z0))
    um_ = grp(f"umbo_{sfx}", O, ecu)
    A0 = HEX_R * math.cos(math.pi / 6) + 0.1
    PALE_ALT = [("pale", {"clair": 0.1}), ("pale", {"clair": -0.08})]
    B_CAP = 0.92
    tour(um_, "umbo", O, (0, 0, 1), (1, 0, 0),
         [(0.0, A0, 0.30, A0, [("argent", {"clair": 0.1, "givre": True}), ("argent", {"clair": -0.05, "givre": True})]),
          (0.30, A0, 0.42, A0 - 0.16, [("argent", {"clair": 0.2})]),
          (0.42, A0 - 0.16, 0.74, A0 - 0.40, PALE_ALT),
          (0.74, A0 - 0.40, B_CAP, 1.42, PALE_ALT)], n=6, phase=0.0, cle="umbo")
    disque(um_, "couvercle", O + np.array((0, 0, B_CAP)), (0, 0, 1), np.array((0, 1.0, 0)), 1.42, t_disque("couvercle", 6, 1.42))
    fl = grp(f"flocon_{sfx}", O, um_)
    G["flocon"] = fl
    zc = B_CAP + 0.1
    fb = {f: BRAS for f in ("south", "north", "up", "down")}
    fb.update(east=BRAS_B, west=BRAS_B)
    Rf = 1.5
    for k in range(3):
        th = math.radians(90 + 60 * k)
        e = np.array((math.cos(th), math.sin(th), 0.0))
        barre(fl, f"bras{k}", O + (0, 0, zc) - e * Rf, O + (0, 0, zc) + e * Rf, 0.13, (0, 0, 1), fb)
    for k in range(6):
        th = math.radians(90 + 60 * k)
        e = np.array((math.cos(th), math.sin(th), 0.0))
        for fr_, ln in ((0.5, 0.42), (0.78, 0.3)):
            base = O + (0, 0, zc + 0.01) + e * Rf * fr_
            for sg in (-1, 1):
                t2 = th + sg * math.radians(55)
                e2 = np.array((math.cos(t2), math.sin(t2), 0.0))
                barre(fl, f"branche{k}{'pm'[sg < 0]}{int(fr_ * 10)}", base - e2 * 0.05, base + e2 * ln, 0.08, (0, 0, 1), fb)
    tour(fl, "gemme", O + (0, 0, B_CAP), (0, 0, 1), (1, 0, 0),
         [(0.0, 0.44, 0.24, 0.44, [("gemme", {"clair": 0.1}), ("gemme", {"clair": -0.1})]),
          (0.24, 0.44, 0.62, 0.0, [("gemme", {"clair": 0.2}), ("gemme", {})])], n=6, phase=math.pi / 6, cle="gemme")
    if bloque:
        ec = grp(f"add_eclat_{sfx}", O + (0, 0, 0.35), um_)
        G["eclat"] = ec
        G["eclat_z"] = B_CAP + 0.9 - 0.35
        oriented(ec, "eclat", O + (0, 0, 0.35), (1, 0, 0), (0, 1, 0), (0.95, 0.95, 0.15), {"south": "eclat"})
    # crête : cinq cristaux hexagonaux sur le bord haut, pied dans l'orle ; en parade, le givre se renforce (plus longs)
    kL = 1.3 if bloque else 1.0
    G["crete"] = []
    CREST = [(0.0, 0.0, 3.3, 0.66), (2.75, 13.0, 2.3, 0.52), (-2.75, -13.0, 2.3, 0.52), (4.9, 28.0, 1.5, 0.42), (-4.9, -28.0, 1.5, 0.42)]
    for j, (x, tilt, L, r) in enumerate(CREST):
        base, k = surf(x, Y_TOP - IN_ORLE + 0.05, W_ORLE + 0.1)
        N = PANELS[k][2]
        side = np.cross(YV, N)
        d = unit(YV * math.cos(math.radians(tilt)) + side * math.sin(math.radians(tilt)) + N * 0.12)
        cg = grp(f"crete{j}_{sfx}", base, ecu)
        G["crete"].append((cg, j))
        cristal(cg, f"crete{j}", base - d * 0.55, d, r, L * kL + 0.55, N, f"crete{j}{sfx if bloque else ''}")
    base, _ = surf(0.0, Y_PT + 0.45, W_ORLE)
    pg = grp(f"pointe_{sfx}", base, ecu)
    G["pointe"] = pg
    cristal(pg, "pointe", base - unit((0, -1, 0.1)) * 0.3, unit((0, -1, 0.1)), 0.5, 1.9 * kL + 0.3, np.array((0, 0, 1.0)),
            f"pointe{sfx if bloque else ''}")
    # aiguilles de givre autour de l'orle (parade seulement)
    G["aiguilles"] = []
    if bloque:
        SP = [(Y_SH + 6.0, 1.6), (Y_SH + 2.0, 2.0), (Y_SH - 0.3 * (Y_SH - Y_PT), 2.1), (Y_SH - 0.62 * (Y_SH - Y_PT), 1.6)]
        for sx in (1, -1):
            for j, (y, L) in enumerate(SP):
                x = sx * (float(half_width(y)) - IN_ORLE)
                base, k = surf(x, y, W_ORLE)
                N = PANELS[k][2]
                dxy = np.array((float(half_width(y - 0.05)) - float(half_width(y + 0.05)), 0.1))
                nrm = unit(np.array((dxy[1], -dxy[0])))
                out_dir = np.array((sx * abs(nrm[0]), nrm[1] if j >= 2 else 0.18, 0.0))
                Xp = PANELS[k][1] if k != "c" else np.array((1.0, 0, 0))
                d3 = unit(Xp * out_dir[0] + YV * out_dir[1] + N * 0.35)
                ag = grp(f"aiguille_{'d' if sx > 0 else 'g'}{j}_{sfx}", base, ecu)
                G["aiguilles"].append((ag, j))
                cristal(ag, f"aiguille_{'d' if sx > 0 else 'g'}{j}", base - d3 * 0.5, d3, 0.34, L + 0.5, N, f"aiguille{j}")
    # dos : traverses d'argent (dans l'épaisseur de l'âme), montants, poignée de cuir
    dos = grp(f"dos_{sfx}", (0, 0, 0), ecu)
    fbar = {"south": "argent_b", "north": "argent_b", "up": "argent_b", "down": "argent_b", "east": "argent_cap", "west": "argent_cap"}
    for yb in (5.4, -3.6):
        for k in ("c", "d", "g"):
            O_, X, N = PANELS[k]
            if k == "c":
                u0, u1 = -HINGE - 0.05, HINGE + 0.05
            else:
                ue = (float(half_width(yb)) - HINGE) / CA - 0.35
                u0, u1 = (-0.2, ue) if k == "d" else (-ue, 0.2)
            wb0, wb1 = -1.95, -1.2
            oriented(dos, f"traverse_{k}{'h' if yb > 0 else 'b'}", P3(k, (u0 + u1) / 2, yb, (wb0 + wb1) / 2), X, YV,
                     ((u1 - u0) / 2, 0.5 if k == "c" else 0.44, (wb1 - wb0) / 2), fbar)
    fm = dict(fbar, south="argent_h", north="argent_h", up="argent_h", down="argent_h")
    for yp in (2.8, -2.8):
        p = np.array((0.0, yp, 0.85 - 1.85))
        q = np.array((0.0, yp, -4.6))
        oriented(dos, f"montant_{'h' if yp > 0 else 'b'}", (p + q) / 2, unit(q - p), (1, 0, 0), (np.linalg.norm(q - p) / 2, 0.4, 0.4), fm)
    bar8(dos, "poignee", (0, -3.25, -4.2), (0, 3.25, -4.2), 0.55, "cuir", (0, 0, 1), cap="cuir_cap")
    return G


racine_r = grp("repos", (0, 0, 0), None)
GR = build_ecu("r", racine_r, False)
racine_b = grp("bloque", (0, 0, 0), None)
pose = grp("pose_bloque", (0, 0, 0), racine_b)
GB = build_ecu("b", pose, True)


# ------------------------------------------------------------------ atlas
UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    cat = {}
    for n, (im, _) in TILES.items():
        k = re.sub(r"[0-9].*", "", n)
        cat[k] = cat.get(k, 0) + im.shape[0] * im.shape[1]
    print("texels :", sum(cat.values()), sorted(cat.items(), key=lambda kv: -kv[1])[:12])
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    sky = np.zeros(TEX, int)          # rangement en ligne d'horizon : chaque tuile au plus bas possible
    for n, (im, ime) in sorted(TILES.items(), key=lambda it: (-it[1][0].shape[0], -it[1][0].shape[1])):
        h, w = im.shape[:2]
        best = None
        for x in range(0, TEX - w + 1):
            yb = int(sky[x:x + w + 1].max()) if x + w + 1 <= TEX else int(sky[x:x + w].max())
            if best is None or yb < best[1]:
                best = (x, yb)
        x, y = best
        assert y + h <= TEX - 6, f"atlas plein ({n}, y = {y})"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None:
            tex_e[y:y + h, x:x + w] = ime
        sky[x:x + w + 1] = y + h + 1
    y, shelf = int(sky.max()), 0
    assert tex[TEX - 2, TEX - 2, 3] == 0
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    zone = np.zeros(semi.shape, bool)
    for n in TRANS_TILES:
        u0, v0, u1, v1 = UV[n]
        zone[v0:v1, u0:u1] = True
    assert not (semi & ~zone).any(), "semi-transparence hors des tuiles trans_"
    assert set(np.unique(tex_e[..., 3])) <= {0, 255}
    print(f"atlas : {len(TILES)} tuiles, rangées jusqu'à y = {y + shelf}")
    res = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        res.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return res


tex_b64, tex_e_b64 = atlas()


# ------------------------------------------------------------------ émission
def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def euler(R):
    """Angles (X, Y, Z) tels que R = Rz Ry Rx ; blocage de cardan (Y = ±90°) : Z = 0, tout l'angle sur X ; vérifié."""
    if abs(R[2, 0]) < 0.99999:
        e = (math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(math.asin(-R[2, 0])), math.degrees(math.atan2(R[1, 0], R[0, 0])))
    elif R[2, 0] < 0:
        e = (math.degrees(math.atan2(R[0, 1], R[0, 2])), 90.0, 0.0)
    else:
        e = (math.degrees(math.atan2(-R[0, 1], -R[0, 2])), -90.0, 0.0)
    assert np.allclose(rotm(*e), R, atol=1e-5), "euler"
    return e


def nuid():
    return str(_uuid.uuid4())


def uv_de(f):
    if isinstance(f, tuple):
        u0, v0, u1, v1 = UV[f[0]]
        return [u1, v0, u0, v1]
    return list(UV[f])


elements, groups = [], {}
for nom, piv, parent in GROUPES:
    assert nom not in groups and len(nom) <= 64, nom
    groups[nom] = {"origin": [round(float(v), 4) for v in piv], "uuid": nuid(), "ids": [], "parent": parent}
for cb in CUBES:
    c, h = cb["c"], cb["half"]
    R = cb["R"]
    assert abs(np.linalg.det(R) - 1) < 1e-6, cb["nom"]
    rot = euler(R)
    e = {"name": cb["nom"], "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in c - h],
         "to": [round(float(v), 4) for v in c + h], "origin": [round(float(v), 4) for v in c], "box_uv": False,
         "faces": {f: {"uv": uv_de(cb["faces"][f]) if f in cb["faces"] else CLEAR, "texture": 0} for f in SIX}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[cb["groupe"]]["ids"].append(e["uuid"])


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node(racine_r), bone_node(racine_b)]

# ------------------------------------------------------------------ réglages Display (item/shield.json et item/shield_blocking.json du jar 26.1.2)
VAN = {"thirdperson_righthand": ((0, 90, 0), (10, 6, -4), 1), "thirdperson_lefthand": ((0, 90, 0), (10, 6, 12), 1),
       "firstperson_righthand": ((0, 180, 5), (-10, 1.75, -10), 1.25), "firstperson_lefthand": ((0, 180, 5), (10, 0, -10), 1.25),
       "gui": ((15, -25, -5), (2, 3, 0), 0.65), "fixed": ((0, 180, 0), (-4.5, 4.5, -5), 0.55), "on_shelf": ((0, 0, 0), (11, 18.5, 8.7), 1.4),
       "ground": ((0, 0, 0), (2, 4, 2), 0.25)}
VAN_BLOQUE = {"thirdperson_righthand": ((45, 155, 0), (-3.49, 11, -2), 1), "thirdperson_lefthand": ((45, 155, 0), (11.51, 7, 2.5), 1),
              "firstperson_righthand": ((0, 180, -5), (-15, 3.25, -11), 1.25), "firstperson_lefthand": ((0, 180, -5), (5, 5, -11), 1.25)}
AFFICHAGE = objet.affichage("bouclier", **{c: {"rotation": list(r), "translation": list(t), "scale": [s] * 3} for c, (r, t, s) in VAN.items()})


def disp(v, gauche):
    """Display appliqué comme ItemTransform.apply : main gauche = rotation Y, Z et translation X inversées."""
    r, t, s = v
    r, t = list(r), list(t)
    if gauche:
        r[1], r[2], t[0] = -r[1], -r[2], -t[0]
    return objet.matrice_display({"rotation": r, "translation": t, "scale": [s] * 3})


# correction de parade par contexte : pose_bloque (pivot à l'origine) = D_repos⁻¹ · D_parade
CORR = {}
for c in VAN_BLOQUE:
    gauche = c.endswith("lefthand")
    H = np.linalg.inv(disp(VAN[c], gauche)) @ disp(VAN_BLOQUE[c], gauche)
    Rm = H[:3, :3]
    assert np.allclose(Rm @ Rm.T, np.eye(3), atol=1e-6)
    CORR[c] = (euler(Rm), H[:3, 3])
    e, t = CORR[c]
    for p in ((0, 0, 1.5), (6, 10, 2), (-6, -11, 1), (0, 3, -5)):
        a = disp(VAN[c], gauche) @ np.append(rotm(*e) @ np.array(p, float) + t, 1)
        b = disp(VAN_BLOQUE[c], gauche) @ np.append(np.array(p, float), 1)
        assert np.allclose(a, b, atol=1e-6), c
    print(f"parade {c:23s} rotation {np.round(e, 2).tolist()} position {np.round(t, 3).tolist()}")


def molang_combo(i, chan):
    """Valeur Molang : 1re/3e personne × main droite/gauche (q.hand : 0 droite, 1 gauche)."""
    v = {c: (CORR[c][0][i] if chan == "rot" else CORR[c][1][i]) for c in CORR}
    f = lambda x: f"({x:.3f})"
    return (f"q.in_first_person*(q.hand*{f(v['firstperson_lefthand'])}+(1-q.hand)*{f(v['firstperson_righthand'])})"
            f"+(1-q.in_first_person)*(q.hand*{f(v['thirdperson_lefthand'])}+(1-q.hand)*{f(v['thirdperson_righthand'])})")


# ------------------------------------------------------------------ animations (objet vivant, guide 14)
def kf(chan, t, x, y, z, interp="linear"):
    s = lambda v: v if isinstance(v, str) else f"{float(v) + 0.0:.4f}".rstrip("0").rstrip(".")
    return {"channel": chan, "data_points": [{"x": s(x), "y": s(y), "z": s(z)}], "time": round(t, 4), "interpolation": interp}


def anim(name, length, loop="loop"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "item_idle",
            "animators": {}}


def piste(an, g, keys):
    u = groups[g]["uuid"]
    if u in an["animators"]:
        an["animators"][u]["keyframes"] += keys
    else:
        an["animators"][u] = {"name": g, "type": "bone", "keyframes": keys}


def echant(L, n):
    return [L * i / n for i in range(n + 1)]


USURE = "math.clamp((q.item_durability-0.55)/0.35,0,1)"


def fiss_molang(an, fg, expr, L):
    N = NORMALE[fg] * CRACK_OUT
    vals = [f"{N[i]:.3f}*{expr}" if abs(N[i]) > 1e-6 else "0" for i in range(3)]
    piste(an, fg, [kf("position", 0, *vals), kf("position", L, *vals)])


# item_idle (8 s) : la glace ne plie pas ; frisson de la crête à 5 s ; fissures selon l'usure
L_IDLE = 8.0
idle = anim("item_idle", L_IDLE)
rot_m = [molang_combo(i, "rot") for i in range(3)]
pos_m = [molang_combo(i, "pos") for i in range(3)]
# Correctif F6 : la garde vit aussi dans item_idle (pose_bloque n'est dessiné qu'à l'étape bloque) ; si le mod voit « plus
# utilisé » une image, item_idle reprend sans fondu ni retombée (objets.md, « Retour en jeu 2026-11-08 soir », recette 2).
piste(idle, pose, [kf("rotation", 0, *rot_m), kf("rotation", L_IDLE, *rot_m), kf("position", 0, *pos_m), kf("position", L_IDLE, *pos_m)])
for cg, j in GR["crete"]:
    piste(idle, cg, [kf("rotation", t, 0, 0, (0.9 if j % 2 else -0.9) * math.sin(TAU * 7 * t) * bump(t, 4.9, 5.0, 5.15, 5.6))
                     for t in [i * 0.05 for i in range(int(L_IDLE / 0.05) + 1)]])
for fg in GR["fiss"]:
    fiss_molang(idle, fg, USURE, L_IDLE)

# item_use : pose de parade (vanilla shield_blocking), fissures (usure, coup reçu)
L_USE = 1.0
use = anim("item_use", L_USE)
piste(use, pose, [kf("rotation", 0, *rot_m), kf("rotation", L_USE, *rot_m), kf("position", 0, *pos_m), kf("position", L_USE, *pos_m)])
for fg in GB["fiss"]:
    fiss_molang(use, fg, f"math.max({USURE},q.hit_by_entity)", L_USE)

# event_select (0,7 s) : la crête et le cristal de pointe poussent depuis leur base (centre d'abord), le flocon se visse
L_SEL = 0.7
sel = anim("event_select", L_SEL, "once")
for G in (GR, GB):
    for cg, j in G["crete"]:
        d0 = 0.05 + 0.07 * ((j + 1) // 2)
        piste(sel, cg, [kf("scale", t, *([0.05 + 0.95 * sm(t, d0, d0 + 0.3) + 0.08 * bump(t, d0 + 0.22, d0 + 0.3, d0 + 0.32, d0 + 0.45)] * 3))
                        for t in echant(L_SEL, 28)])
    piste(sel, G["pointe"], [kf("scale", t, *([0.05 + 0.95 * sm(t, 0.15, 0.45)] * 3)) for t in echant(L_SEL, 28)])
    piste(sel, G["flocon"], [kf("rotation", t, 0, 0, -60 * (1 - sm(t, 0.0, 0.5))) for t in echant(L_SEL, 28)]
          + [kf("scale", t, *([0.4 + 0.6 * sm(t, 0.0, 0.4)] * 3)) for t in echant(L_SEL, 28)])

# event_use_start (0,55 s) : le givre se renforce : aiguilles qui jaillissent en cascade, crête qui grandit, éclat au cœur
L_US = 0.55
us = anim("event_use_start", L_US, "once")
for ag, j in GB["aiguilles"]:
    d0 = 0.02 + 0.05 * j
    piste(us, ag, [kf("scale", t, *([0.02 + 0.98 * sm(t, d0, d0 + 0.14) + 0.14 * bump(t, d0 + 0.1, d0 + 0.14, d0 + 0.16, d0 + 0.3)] * 3))
                   for t in echant(L_US, 22)])
for cg, j in GB["crete"]:
    piste(us, cg, [kf("scale", t, *([0.77 + 0.23 * sm(t, 0.0, 0.16) + 0.06 * bump(t, 0.12, 0.16, 0.18, 0.32)] * 3)) for t in echant(L_US, 22)])
ec = GB["eclat"]
piste(us, ec, [kf("position", t, 0, 0, GB["eclat_z"] * (sm(t, 0.0, 0.03) * (1 - sm(t, 0.4, 0.43)))) for t in echant(L_US, 22)]
      + [kf("scale", t, *([1 + 1.6 * sm(t, 0.0, 0.08) * (1 - sm(t, 0.1, 0.4))] * 3)) for t in echant(L_US, 22)])

# event_hit (0,7 s) : les fissures s'ouvrent d'un coup puis se referment (rentrent dans l'âme)
L_HIT = 0.7
hit = anim("event_hit", L_HIT, "once")
for G in (GR, GB):
    for fg in G["fiss"]:
        N = NORMALE[fg] * CRACK_OUT
        piste(hit, fg, [kf("position", t, *(N * (sm(t, 0.0, 0.03) * (1 - sm(t, 0.12, 0.62))))) for t in echant(L_HIT, 28)])

# overlay_flocon (24 s) : le flocon fait un tour
L_OV = 24.0
ov = anim("overlay_flocon", L_OV)
for G in (GR, GB):
    piste(ov, G["flocon"], [kf("rotation", t, 0, 0, -360 * t / L_OV) for t in echant(L_OV, 4)])

ANIMS = [idle, use, sel, us, hit, ov]

# ------------------------------------------------------------------ écriture
assert 300 <= len(elements) <= 3000, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = objet.modele(NOM, "bouclier", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons
limiter_sons(model)
# Aucun son (2026-11-08) : en jeu, le blocage du bouclier d'orage (même technique) se retire et se remet sans cesse et
# le son de event_use_start « spamme » ; son retiré en attendant le diagnostic de la logique de blocage.
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def coins():
    P = []
    for e in elements:
        f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
        R = rotm(*e.get("rotation", (0, 0, 0)))
        for i in range(8):
            c = np.array([(f, t)[(i >> k) & 1][k] for k in range(3)])
            P.append(R @ (c - o) + o)
    return np.array(P)


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


P = coins()
print("boîte (coins des cubes) :", P.min(0).round(2).tolist(), "->", P.max(0).round(2).tolist())
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
