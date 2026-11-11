"""Arbalète de givre : skin d'objet (guide 14) pour toutes les arbalètes du joueur, ensemble Givre (thème Éléments). Design original.
Écrit skin_arbalete_givre.png, skin_arbalete_givre_e.png et .build/skin_arbalete_givre_brut.bbmodel à côté de ce script.

Famille (.claude/styles/givre.md) : skin_arc_givre (branches de glace en vrai volume, reprises ici), épée, lance, pioche, hache.
Langage : glace = peau `trans_` mince sans faces internes autour d'une âme opaque de même forme (cœur cyan _e, chevrons,
fissures), argent froid, cuir bleu nuit clouté, cristaux hexagonaux pointus, flocon en relief à gemme hexagonale _e.
Anatomie d'une arbalète réelle (.claude/references/objets/arbaletes.md) traduite dans la glace du set, silhouette propre
(distincte de l'arc : arc court et trapu, arbrier long, nez de cristal) :
- arc court en glace taillée : deux branches = plaques biseautées fermées courbes (recette .claude/references/objets/volume-3d.md,
  classe Branche de gen_skin_arc_givre.py) : section hexagonale, pente unique 50°, amincies de 1,40 px au pied à 0,68 px,
  demi-largeur 0,92 -> 0,48 ; recourbées vers l'avant aux bouts ; cristal sur le dos, poupée d'argent et pointe de cristal,
  tenon d'argent où la corde s'attache ; branche gauche = droite tournée de 180° autour de l'axe de tir (mêmes tuiles) ;
- logement d'argent en travers, nez de trois cristaux devant, grappes au pied des branches, étrier d'argent en demi-flocon ;
- arbrier d'argent octogonal à deux rails, rainure lumineuse (_e) où glisse le carreau, noix en bague d'argent, détente et pontet ;
- crosse : médaillon d'argent à flocon en relief et gemme sur les deux faces (vu dans la case), prise de cuir bleu nuit cloutée
  entre deux bagues, talon de cristal.

Étapes (guide 14 ; le groupe `arbalete` est toujours dessiné) : `repos` (corde droite), `bande_1` à `bande_3` (les branches se
cintrent, la corde recule jusqu'à la noix), `chargee` (carreau de cristal : fût lumineux, trois pennes de glace, pointe en losange
de cristal ; **couvert de givre** : aiguilles en plumes et collier de givre), `chargee_fusee` (fusée bleu nuit cerclée d'argent,
coiffe de cristal, givre).
Repère : celui de skin_arbalete_steampunk (validé en jeu) et de l'arc : avant en HAUT À GAUCHE vu de +Z (S_ = (−1, 1, 0)/√2),
arc le long de H_ = (1, 1, 0)/√2, dessus du fût vers +Z ; Display vanilla item/crossbow (tools/objet.py), échelle gui à la case.

Objet vivant (guide 14), sobre :
- item_idle (8 s) : deux scintillements (étoiles _e qui sortent des gemmes du médaillon) ;
- item_use (0,5 s) : l'arbalète frémit avec la tension (Molang q.use_progress) ;
- event_charged (0,6 s) : le givre couvre le carreau (ou la fusée) d'un coup, étoile à la pointe ;
- event_release (0,8 s) : **nuage de flocons** (9 flocons trans_ qui jaillissent du logement, tournoient, pâlissent par
  ctrl_alpha), corde qui vibre, arc qui frissonne, rafale emit_mc_snowflake (ctrl_emit) ; **seul son** :
  block.amethyst_block.chime ;
- event_select (0,8 s) : la glace de l'arc repousse depuis le logement, la corde gèle, étoile au médaillon.
Flocons et étoiles cachés au repos : géométrie K fois plus petite enfouie dans le logement ou le médaillon, agrandie par
l'animation ; chaque groupe n'est déplié que par une seule animation (aucune échelle superposée).

Fonctions avancées : trans_, ctrl_alpha, emit_mc_snowflake + ctrl_emit, calque _e, scale animé, Molang q.use_progress,
item_idle, item_use, event_charged, event_release, event_select. À juger en jeu : la glace sur âme opaque avec et sans shader,
event_charged / event_release et le son (pas encore vérifiés par le développeur), le nuage de flocons (scale + ctrl_alpha sur un
objet), lecture de l'arc par la tranche en 1re personne.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet  # noqa: E402

NOM = "skin_arbalete_givre"
TEX = 512
TAU = 2 * math.pi
K = 12.0            # éclats et étoiles cachés : géométrie K fois plus petite

# ------------------------------------------------------------------ palette (fiche de style givre)
GL_C, GL_B, GL_O = (244, 253, 255), (120, 208, 238), (8, 34, 70)
GV_C, GV_B, GV_O = (255, 255, 255), (214, 238, 250), (150, 190, 214)
AR_C, AR_B, AR_O = (226, 236, 244), (160, 180, 200), (70, 86, 110)
LU_C, LU_B, LU_O = (210, 245, 255), (150, 226, 255), (40, 110, 170)
CUIR = (28, 40, 74)
C = lambda *c: np.array(c, np.float32)
G_DEEP, G_BODY, G_PALE, G_LIGHT = C(30, 96, 168), C(92, 186, 232), C(168, 226, 250), C(214, 244, 255)
BLANC = C(244, 253, 255)
LUEUR = C(150, 226, 255)
ARG_L, ARG_M, ARG_D = C(236, 244, 250), C(166, 186, 206), C(74, 90, 116)


def A(c):
    return np.array(c, np.float32)


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


def V(*a):
    return np.array(a, float)


# ------------------------------------------------------------------ tuiles
TILES, TRANS = {}, set()          # nom -> (rgba, rgba_e | None)


def tuile(nom, rgba, e=None, trans=False):
    assert nom not in TILES, nom
    TILES[nom] = (rgba, e)
    if trans:
        TRANS.add(nom)
    return nom


def e_of(level):
    """Calque _e : gris `level` (0–255) en RGB, alpha 255 où level > 0."""
    lv = np.asarray(level, np.float32)
    out = np.zeros(lv.shape + (4,), np.uint8)
    out[..., :3] = np.clip(lv, 0, 255)[..., None].astype(np.uint8)
    out[..., 3] = np.where(lv > 0.5, 255, 0)
    return out


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


def glace_tile(seed, W=96, H=24):
    """Glace (trans_) des petites pièces (fût, tessons) : bord givré blanc, corps cyan, chevrons, fissures."""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    q = np.abs((yy + 0.5) / H - 0.5) * 2
    col = lerp(A(GL_B)[None, None], A(LU_O)[None, None] * 1.25, ((1 - q) ** 1.6 * 0.5)[..., None])
    al = 150 + 30 * (1 - q) ** 2
    chev = ((xx + np.abs(yy - H / 2) * 1.1 + seed * 7) % 22) < 1.6
    col[chev] = lerp(col[chev], A(GV_B), 0.45)
    al = np.where(chev, al + 25, al)
    edge = q > 0.74
    col[edge] = lerp(A(GV_B), A(GV_C), 0.6)
    al = np.where(edge, 232, al)
    col *= (0.96 + 0.08 * r.random((H, W, 1))).astype(np.float32)
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(col, 0, 255)
    out[..., 3] = np.clip(al, 1, 254)
    return out


def glace_cap(n=16):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.maximum(np.abs(xx + 0.5 - n / 2), np.abs(yy + 0.5 - n / 2)) / (n / 2)
    col = lerp(A(GL_B)[None, None], A(GV_C)[None, None], (d ** 2)[..., None])
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = col
    out[..., 3] = np.clip(170 + 60 * d, 1, 254)
    return out


def ame_tile(W=64, H=8, lit=(205, 125)):
    yy = (np.mgrid[0:H, 0:W][0] + 0.5) / H
    q = np.abs(yy - 0.5) * 2
    col = lerp(A(LU_C)[None, None], A(GL_B)[None, None] * 0.9, (q ** 1.2)[..., None])
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = col
    out[..., 3] = 255
    return out, e_of(np.where(q < 0.4, lit[0], lit[1]))


def metal_tile(W=64, H=16, seed=5, grooves=True):
    r = np.random.default_rng(seed)
    yy = (np.mgrid[0:H, 0:W][0] + 0.5) / H
    q = np.abs(yy - 0.38) / 0.62
    col = lerp(A(AR_C)[None, None], A(AR_O)[None, None], (np.clip(q, 0, 1) ** 1.3)[..., None])
    col = lerp(col, A(AR_B)[None, None], 0.35)
    col *= (0.95 + 0.10 * r.random((1, W, 1))).astype(np.float32)      # brossé ±5 %
    if grooves:
        for y in (int(H * 0.22), int(H * 0.78)):
            col[y:y + 1] = A(AR_O) * 1.1
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(col, 0, 255)
    out[..., 3] = 255
    return out


def metal_cap(n=16):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) / (n / 2)
    col = lerp(A(AR_C)[None, None], A(AR_O)[None, None], np.clip(d, 0, 1)[..., None] ** 1.5)
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = col
    out[..., 3] = 255
    return out


def cuir_tile(W=64, H=16):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ph = (xx + yy * 0.7) % 8
    col = np.ones((H, W, 3), np.float32) * A(CUIR)
    col[ph < 1.4] = A(CUIR) * 0.55
    col[(ph > 1.4) & (ph < 3.2)] = A(CUIR) * 1.55
    q = np.abs((yy + 0.5) / H - 0.5) * 2
    col *= (1.05 - 0.3 * q ** 2)[..., None]
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(col, 0, 255)
    out[..., 3] = 255
    return out


def corde_tile(W=32, H=8):
    q = np.abs((np.mgrid[0:H, 0:W][0] + 0.5) / H - 0.5) * 2
    col = lerp(A((214, 244, 255))[None, None], A((120, 196, 232))[None, None], (q ** 1.5)[..., None])
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = col
    out[..., 3] = 255
    return out, e_of(np.where(q < 0.6, 215, 165))


def flocon_mask(n, ss=4, arm_w=0.1, branch=True):
    N = n * ss
    im = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(im)
    c = N / 2
    R = N * 0.47
    for k in range(6):
        a = math.radians(90 + 60 * k)
        ux, uy = math.cos(a), -math.sin(a)
        d.line([(c, c), (c + ux * R, c + uy * R)], fill=255, width=int(N * arm_w))
        if branch:
            for f, L in ((0.45, 0.24), (0.72, 0.16)):
                px, py = c + ux * R * f, c + uy * R * f
                for sg in (-1, 1):
                    b = a + sg * math.radians(55)
                    d.line([(px, py), (px + math.cos(b) * R * L, py - math.sin(b) * R * L)], fill=255, width=int(N * arm_w * 0.8))
    d.ellipse([c - N * 0.13, c - N * 0.13, c + N * 0.13, c + N * 0.13], fill=255)
    return np.array(im.resize((n, n), Image.LANCZOS), np.float32) / 255


def eclat_tile(n=64):
    """Éclat de tir (trans_) : flocon flou, blanc au centre."""
    m = flocon_mask(n, arm_w=0.13)
    g = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)), np.float32) / 255
    a = np.clip(np.maximum(m, g * 0.8), 0, 1)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.clip(np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) / (n / 2), 0, 1)
    col = lerp(A(GV_C)[None, None], A(LU_B)[None, None], (d ** 1.2)[..., None])
    al = np.where(a > 0.06, np.clip(40 + 200 * a, 1, 254), 0)
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = col
    out[..., 3] = al
    return out, e_of(np.where(al > 0, 60 + 160 * a, 0))


def etoile_tile(n=32):
    N = n * 4
    im = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(im)
    c = N / 2
    for a in (0, 90, 45, 135):
        L = N * (0.48 if a % 90 == 0 else 0.26)
        w = N * 0.06
        ra = math.radians(a)
        ux, uy = math.cos(ra), math.sin(ra)
        d.polygon([(c + ux * L, c + uy * L), (c - uy * w, c + ux * w), (c - ux * L, c - uy * L), (c + uy * w, c - ux * w)], fill=255)
    m = np.array(im.resize((n, n), Image.LANCZOS)) > 110
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = GV_C
    out[..., 3] = np.where(m, 255, 0)
    return out, e_of(np.where(m, 235, 0))


def penne_tile(W=48, H=24):
    """Plume d'empennage de glace (trans_, découpée) : trapèze à bord givré."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = (xx + 0.5) / W, (yy + 0.5) / H
    top = 0.15 + 0.75 * u
    inside = (v > top * 0.55) & (v < 1.0)
    col = lerp(A(GL_B)[None, None], A(GV_C)[None, None], (v ** 3)[..., None])
    edge = inside & ((v < top * 0.55 + 0.18) | (u < 0.08))
    col[edge] = A(GV_B)
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = col
    out[..., 3] = np.where(inside, np.where(edge, 228, 165), 0)
    return out


def fantome_tile(W=32, H=8):
    q = np.abs((np.mgrid[0:H, 0:W][0] + 0.5) / H - 0.5) * 2
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = lerp(A(GV_C)[None, None], A(GL_B)[None, None], q[..., None])
    out[..., 3] = np.clip(120 - 50 * q, 1, 254)
    return out


def t_unie(nom, W, H, c0, c1, ligne=None):
    yy, xx = np.mgrid[0:H, 0:W]
    q = (yy + 0.5) / H
    col = lerp(c0, c1, q[..., None]) * (1 + 0.04 * np.sin(xx * 0.7))[..., None]
    if ligne is not None:
        col[int(H * 0.4):int(H * 0.4) + 2] = ligne
    return tuile(nom, *finir(col, None, None, np.ones((H, W), bool)))


for i in range(3):
    tuile(f"glace{i}", glace_tile(11 + i), trans=True)
tuile("glace_cap", glace_cap(), trans=True)
tuile("ame_fl", *ame_tile(lit=(210, 175)))
tuile("argent", metal_tile())
tuile("argent_cap", metal_cap())
tuile("cuir", cuir_tile())
tuile("cuir_cap", metal_cap())
tuile("corde", *corde_tile())
tuile("eclat", *eclat_tile(), trans=True)
tuile("etoile", *etoile_tile())
tuile("penne", penne_tile(), trans=True)
tuile("fantome", fantome_tile(), trans=True)
tuile("tesson", glace_tile(29, 32, 16), trans=True)
BRAS_T = t_unie("bras", 32, 8, ARG_L, ARG_M, ligne=BLANC)
BRAS_CAP = t_unie("bras_bout", 8, 8, BLANC, ARG_M)

# ------------------------------------------------------------------ cubes différés (tuiles résolues après l'atlas)
CUBES = []          # dict(groupe, nom, c, R (colonnes), half, faces {face: tuile | (tuile, "flip") })
groups = {}
SIX = ("north", "south", "east", "west", "up", "down")


def nuid():
    return str(_uuid.uuid4())


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups and len(name) <= 64, name
    groups[name] = {"origin": [round(float(v), 4) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(float(v), 3) for v in rotation]}
    return name


def add(g, nom, c, R, half, faces):
    CUBES.append({"groupe": g, "nom": nom, "c": np.asarray(c, float), "R": np.asarray(R, float), "half": np.asarray(half, float),
                  "faces": faces})


def strip(tile, cap):
    return {"south": tile, "north": tile, "up": tile, "down": tile, "east": cap, "west": cap}


S_MID = -0.7                        # milieu de l'arbalète le long du fût (centrée dans le bloc)
S_ = V(-1, 1, 0) / math.sqrt(2)     # vers l'avant (pointe de la flèche, haut à gauche de l'image vanilla)
H_ = V(1, 1, 0) / math.sqrt(2)      # le long des branches (pointe haute en haut à droite)
Z_ = V(0, 0, 1)                     # côté vu dans l'inventaire
BW = np.column_stack([H_, S_, Z_])  # repère local direct de la branche : (x = h, y = s, z)
C0 = V(8.0, 8.0, 8.0) - S_ * S_MID


def P(s, h, z=0.0):
    return C0 + S_ * s + H_ * h + Z_ * z


def frame(X, ref):
    X = unit(X)
    Y = unit(ref - (ref @ X) * X)
    return X, Y, np.cross(X, Y)


def box(g, name, p, q, hy, hz, faces, ov=0.0, yref=None):
    """Boîte de p à q, demi-épaisseurs hy (dans le plan de l'arc, ou le long de yref) et hz."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    if yref is None:
        Zl = unit(Z_ - (Z_ @ X) * X) if abs(X @ Z_) < 0.99 else unit(np.cross(X, H_))
        Y = np.cross(Zl, X)
    else:
        X, Y, Zl = frame(X, np.asarray(yref, float))
    L = np.linalg.norm(q - p)
    add(g, name, (p + q) / 2, np.column_stack([X, Y, Zl]), ((L + 2 * ov) / 2, hy, hz), faces)


def octo(g, name, p, q, r, tile, cap, ov=0.05, rz=None):
    """Tronçon à section octogonale (deux boîtes, la seconde tournée de 45° sur l'axe, raccourcie de 0,11 px)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    Zl = unit(Z_ - (Z_ @ X) * X) if abs(X @ Z_) < 0.99 else unit(np.cross(X, H_))
    Y = np.cross(Zl, X)
    L = np.linalg.norm(q - p)
    rz = r if rz is None else rz
    f = strip(tile, cap)
    add(g, name, (p + q) / 2, np.column_stack([X, Y, Zl]), ((L + 2 * ov) / 2, r, rz), f)
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    Y2, Z2 = c * Y + s * Zl, -s * Y + c * Zl
    rr = 0.97 * min(r, rz)
    rec = 0.11 if L + 2 * ov > 0.5 else 0.0
    f2 = f if rec else dict(f, east=None, west=None)
    add(g, name + "o", (p + q) / 2, np.column_stack([X, Y2, Z2]), ((L + 2 * ov) / 2 - rec, rr, rr), f2)


def plaque(g, name, c, right, up, half_w, half_h, th, tile):
    """Plaque fine (tranches transparentes) : `tile` sur les deux grandes faces."""
    X, Y, Zl = frame(np.asarray(right, float), np.asarray(up, float))
    add(g, name, c, np.column_stack([X, Y, Zl]), (half_w, half_h, th / 2), {"south": tile, "north": (tile, "flip")})


def barre(g, nom, p, q, r, Rang, faces):
    """Barre de section carrée 2r tournée de Rang degrés autour de son axe (45 : section en losange)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = Z_ if abs(X @ Z_) < 0.9 else H_
    Y0 = unit(ref - (ref @ X) * X)
    Z0 = np.cross(X, Y0)
    a = math.radians(Rang)
    Y = math.cos(a) * Y0 + math.sin(a) * Z0
    add(g, nom, (p + q) / 2, np.column_stack([X, Y, np.cross(X, Y)]), (np.linalg.norm(q - p) / 2, r, r), faces)


# ------------------------------------------------------------------ tours (pièces rondes : couronnes de pans, skin_epee_givre)
TH = 0.3                         # épaisseur des cubes de surface
DF = 16.0                        # texels par px (peau)
DF_AME = 10.0                    # texels par px (âme, vue à travers la peau)
OVL, OVW = 0.04, 0.03


def p_argent(xn, t, ex):
    k = np.clip(0.45 + 0.3 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + ex.get("pointe", 0.0) * t, 0, 1)
    col = lerp(ARG_D, ARG_L, (k ** 1.2)[..., None]) * (1 + 0.03 * np.sin(t * 37 + xn * 3))[..., None]
    col = np.where((np.abs(xn) > 0.86)[..., None], np.minimum(col * 1.14 + 10, 255), col)        # arête claire
    if ex.get("givre"):
        col = np.where(((t > 0.82) & (np.abs(xn) < 0.75))[..., None], lerp(col, BLANC, 0.6), col)
    return col, None, None


def p_glace(xn, t, ex):
    """Âme d'un cristal (opaque) : cyan, arêtes blanches, filet _e au milieu de chaque pan."""
    k = np.clip(0.35 + 0.35 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + 0.25 * t, 0, 1)
    col = lerp(C(40, 110, 176), G_LIGHT, (k ** 1.1)[..., None])
    col = np.where((np.abs(xn) > 0.84)[..., None], BLANC, col)
    em = np.zeros(col.shape, np.float32)
    if ex.get("e"):
        ln = np.abs(xn) < 0.2
        col[ln] = lerp(col[ln], C(200, 248, 255), 0.7)
        em[ln] = LUEUR
    return col, em, None


def p_peau(xn, t, ex):
    """Peau d'un cristal (trans_) : glace claire, arêtes blanches plus denses, pointe plus pâle."""
    k = np.clip(0.45 + 0.3 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + 0.2 * t, 0, 1)
    col = lerp(C(110, 196, 236), C(214, 244, 255), k[..., None])
    al = 150 + 40 * t + 10 * (1 - np.abs(xn))
    ar = np.abs(xn) > 0.8
    col = np.where(ar[..., None], BLANC, col)
    al = np.where(ar, 224, al)
    return col, None, al


def p_gemme(xn, t, ex):
    k = np.clip(0.4 + 0.4 * (1 - np.abs(xn)) + 0.2 * t + ex.get("clair", 0.0), 0, 1)
    col = lerp(C(40, 130, 210), C(170, 236, 255), k[..., None])
    return col, np.clip(col * 0.8, 0, 200), None


PEINTRES = {"argent": p_argent, "glace": p_glace, "peau": p_peau, "gemme": p_gemme}


def tuile_pan(nom, mat, L, w0, w1, ex):
    if nom in TILES:
        return nom
    wm = max(w0, w1) + 2 * OVW
    Lf = L + 2 * OVL
    Wt, Ht = max(2, int(math.ceil(wm * DF))), max(2, int(math.ceil(Lf * DF)))
    yy, xx = np.mgrid[0:Ht, 0:Wt]
    x = ((xx + 0.5) / Wt - 0.5) * wm
    y = Lf * (1 - (yy + 0.5) / Ht) - OVL
    t = np.clip(y / max(L, 1e-6), 0, 1)
    hw = (w0 + (w1 - w0) * t) / 2 + OVW
    mask = np.abs(x) <= hw
    xn = np.clip(x / np.maximum(hw - OVW, 1e-3), -1, 1)
    col, em, al = PEINTRES[mat](xn, t, ex)
    return tuile(nom, *finir(col, al, em, mask), trans=al is not None)


def tour(g, nom, O, ax, ref, profil, n=8, phase=0.0, cle=None):
    """profil = [(b0, r0, b1, r1, [(mat, ex), ...]), ...] le long de ax (rayon = apothème) ; matières alternées par pan.
    Chaque pan : plaque de TH px, face extérieure (south) sur la surface, autres faces transparentes.
    cle : préfixe des tuiles (des tours de même forme partagent leurs tuiles)."""
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
            add(g, f"{nom}{i}_{k}", c, np.column_stack([X, Y, N]), (wm / 2, L / 2 + OVL, TH / 2), {"south": tiles[k % len(tiles)]})


def bague(b0, b1, ra, ro, rb, c=0.12, mat="argent"):
    return [(b0, ra, b0 + c, ro, [(mat, {"clair": 0.15})]), (b0 + c, ro, b1 - c, ro, [(mat, {}), (mat, {"clair": -0.08})]),
            (b1 - c, ro, b1, rb, [(mat, {"clair": -0.12})])]


def t_disque(nom, n, Ra, N=48):
    """Couvercle en polygone régulier (apothème Ra) : argent givré, anneau clair, découpé par l'alpha."""
    R = Ra / math.cos(math.pi / n)
    yy, xx = np.mgrid[0:N, 0:N]
    x = ((xx + 0.5) / N - 0.5) * 2 * R
    y = (0.5 - (yy + 0.5) / N) * 2 * R
    th = np.arctan2(y, x)
    sect = np.round(th / (TAU / n)) * (TAU / n)
    apo = x * np.cos(sect) + y * np.sin(sect)
    mask = apo <= Ra
    rr = apo / Ra
    col = lerp(ARG_L, ARG_M, rr[..., None] ** 1.5)
    col[(rr > 0.72) & (rr < 0.8)] = BLANC
    col[rr > 0.92] = ARG_D
    return tuile(nom, *finir(col, None, None, mask))


def disque(g, nom, c, Nrm, up, n, Ra, tile):
    Nrm = unit(Nrm)
    Y = unit(up - (up @ Nrm) * Nrm)
    X = np.cross(Y, Nrm)
    R = Ra / math.cos(math.pi / n)
    add(g, nom, np.asarray(c, float) - Nrm * TH / 2, np.column_stack([X, Y, Nrm]), (R, R, TH / 2), {"south": tile})


CRIS_PEAU = [("peau", {"clair": 0.06}), ("peau", {"clair": -0.08})]
CRIS_AME = [("glace", {"clair": 0.1, "e": True}), ("glace", {"clair": -0.1})]


def cristal(g_trans, g_ame, name, base, d, L, r, cle=None):
    """Cristal hexagonal à pointe : peau trans_ à 6 pans (pied enfoncé, prisme, pointe) + âme opaque à filet _e."""
    d = unit(np.asarray(d, float))
    ref = Z_ if abs(d @ Z_) < 0.9 else H_
    tl = min(L * 0.42, r * 2.0)
    cle = cle or name
    tour(g_trans, name, base, d, ref, [(0.0, r * 0.85, 0.15, r, CRIS_PEAU), (0.15, r, L - tl, r, CRIS_PEAU), (L - tl, r, L, 0.0, CRIS_PEAU)],
         n=6, phase=math.pi / 6, cle=cle + "_p")
    ra = max(r - 0.2, r * 0.45)
    tour(g_ame, name + "_ame", base, d, ref, [(0.0, ra, L - tl, ra, CRIS_AME), (L - tl, ra, L - 0.22, 0.0, CRIS_AME)],
         n=6, phase=math.pi / 6, cle=cle + "_a")


# ------------------------------------------------------------------ branches en vrai volume (repère local x = h, y = s, z)
Z_E = 0.10                       # demi-épaisseur au fil (0,20 px)
T_BIS = 1.19                     # pente unique des biseaux (50°)
AL = math.atan(T_BIS)
DELTA = 0.20                     # retrait de l'âme sous la peau (normal aux faces)
ZC_MIN = 0.05                    # demi-épaisseur de l'âme à son bord
RECOUV_AME = 0.08                # âme opaque : recouvrement libre
EPS_PEAU = 0.05                  # peau : partition le long de u, chaque tronçon déborde de 0,05 px sur le précédent seulement
#                                  (sans débord, les grilles de texels laissent une fente d'un texel où l'âme claire se voit :
#                                  traits blancs aux raccords ; un débord des deux côtés doublerait l'alpha sur 0,1 px)
D_OFF = (ZC_MIN - Z_E) / T_BIS + DELTA / math.sin(AL)          # bord de l'âme, depuis le fil
D_C_EXTRA = DELTA * (1 / math.cos(AL) - 1) / T_BIS             # l'arête biseau/plat de l'âme est un peu plus loin
NSEG = 16                        # tronçons de fil par côté
NBANDE = 8                       # bandes de plat le long de la branche
L_BR = 5.9
HW_R, HW_T = 0.92, 0.48          # demi-largeur dans le plan de l'arc : pied -> poupée
H_R, H_T = 0.70, 0.34            # demi-épaisseur du plat (z) : pied -> poupée
S_PIED, H_PIED = 4.4, 0.55       # pied des branches (dans le logement), symétriques autour de l'axe de tir
H_AXE = 0.0
PH0, CIN, REC = (6, 16), (16, 40), (-26, -12)


def hw_u(u):
    return lerp(HW_R, HW_T, np.clip(np.asarray(u, float) / L_BR, 0, 1) ** 0.9)


def h_u(u):
    return lerp(H_R, H_T, np.clip(np.asarray(u, float) / L_BR, 0, 1))


def wb_u(u):
    return (h_u(u) - Z_E) / T_BIS


class Branche:
    """Ligne médiane dense, fils (dos +N, ventre −N), contour, projection (u, db) d'un point du plan."""

    def __init__(self, d):
        phi0, cint, rec = lerp(PH0[0], PH0[1], d), lerp(CIN[0], CIN[1], d), lerp(REC[0], REC[1], d)
        s, h = S_PIED, H_PIED
        pts, phis = [(h, s)], []
        n = 440
        for i in range(n):
            u = (i + 0.5) / n
            phi = phi0 + cint * min(u / 0.76, 1.0) ** 1.15 + (rec * ((u - 0.76) / 0.24) ** 1.3 if u > 0.76 else 0.0)
            ds = L_BR / n
            s += -math.sin(math.radians(phi)) * ds
            h += math.cos(math.radians(phi)) * ds
            pts.append((h, s))
            phis.append(phi)
        self.cl = np.array(pts)
        self.phis = np.array([phis[0]] + [(phis[i] + phis[min(i + 1, n - 1)]) / 2 for i in range(n - 1)] + [phis[-1]])
        self.A, self.B = self.cl[:-1], self.cl[1:]
        self.AB = self.B - self.A
        self.len2 = (self.AB ** 2).sum(-1)
        self.U0 = np.concatenate([[0.0], np.cumsum(np.sqrt(self.len2))])[:-1]
        self.n = n

    def at(self, u):
        """Point, tangente, normale (côté dos, vers +S) à l'abscisse u."""
        i = int(np.clip(round(u / L_BR * self.n), 0, self.n))
        phi = math.radians(self.phis[i])
        t = np.array((math.cos(phi), -math.sin(phi)))
        return self.cl[i].copy(), t, np.array((math.sin(phi), math.cos(phi)))

    def proj(self, P2):
        sh = P2.shape[:-1]
        Pf = P2.reshape(-1, 2)
        t = np.clip(((Pf[:, None, :] - self.A[None]) * self.AB[None]).sum(-1) / self.len2[None], 0, 1)
        Q = self.A[None] + t[..., None] * self.AB[None]
        dd = ((Pf[:, None, :] - Q) ** 2).sum(-1)
        i = np.argmin(dd, axis=1)
        k = np.arange(len(Pf))
        u = self.U0[i] + t[k, i] * np.sqrt(self.len2[i])
        cr = self.AB[i, 0] * (Pf[:, 1] - self.A[i, 1]) - self.AB[i, 1] * (Pf[:, 0] - self.A[i, 0])
        db = np.sqrt(dd[k, i]) * np.sign(cr)
        return u.reshape(sh), db.reshape(sh)


def construire_fils(br):
    us = np.linspace(0, L_BR, NSEG + 1)
    dos, ventre = [], []
    for u in us:
        c, t, nrm = br.at(u)
        w = float(hw_u(u))
        dos.append(c + nrm * w)
        ventre.append(c - nrm * w)
    br.us = us
    br.poly = [tuple(p) for p in dos] + [tuple(p) for p in ventre[::-1]]
    br.segs = [(dos[i], dos[i + 1], us[i], us[i + 1]) for i in range(NSEG)] + [(ventre[i], ventre[i + 1], us[i], us[i + 1]) for i in range(NSEG)]


def in_poly(P, poly):
    x, y = P[..., 0], P[..., 1]
    ins = np.zeros(x.shape, bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1)
        ins ^= c
    return ins


def d_stack(P, segs):
    out = []
    for p, q, *_ in segs:
        ab = q - p
        t = np.clip(((P - p) @ ab) / (ab @ ab), 0, 1)
        out.append(np.linalg.norm(P - (p + t[..., None] * ab), axis=-1))
    return np.stack(out)


# --- motifs en coordonnées de matière (u le long de la branche, v = db / demi-largeur) : ils suivent la branche
MU, MV = 40.0, 48.0


def _motifs(seed):
    r = np.random.default_rng(seed)
    Wd, Hd = int(L_BR * MU) + 2, int(2 * MV)
    fis = Image.new("L", (Wd, Hd), 0)
    d = ImageDraw.Draw(fis)

    def px(u, v):
        return (u * MU, (1 - v) * MV)
    for k in range(6):
        u = lerp(0.8, L_BR - 1.2, (k + r.uniform(0.15, 0.85)) / 6)
        v = r.uniform(-0.45, 0.45)
        pl = [(u, v)]
        ang = r.uniform(0.4, 1.2) * r.choice([-1, 1])
        for j in range(3):
            ang += r.uniform(-0.6, 0.6)
            ln = r.uniform(0.22, 0.42)
            pl.append((pl[-1][0] + math.cos(ang) * ln * 0.9, float(np.clip(pl[-1][1] + math.sin(ang) * ln * 0.9, -0.8, 0.8))))
        d.line([px(*p) for p in pl], fill=255, width=3)
    nz = Image.fromarray((r.random((8, 50)) * 255).astype(np.uint8), "L").resize((Wd, Hd), Image.BICUBIC)
    return np.array(fis) > 127, np.array(nz, np.float32) / 255


MOTIFS = {sg: _motifs(41 + (sg > 0)) for sg in (1, -1)}


def motif(u, v, sg):
    fis, nz = MOTIFS[sg]
    i = np.clip(((1 - v) * MV).astype(int), 0, fis.shape[0] - 1)
    j = np.clip((u * MU).astype(int), 0, fis.shape[1] - 1)
    return fis[i, j], nz[i, j]


def chevrons(u, db):
    """Paliers de taille obliques (chevrons symétriques autour de l'axe), comme la lame de l'épée."""
    return (np.floor((u * 0.75 + 2.2 * np.abs(db)) / 1.2) % 2) * 2 - 1


def peau_plat(u, db, de, sg):
    un = np.clip(u / L_BR, 0, 1)[..., None]
    g = chevrons(u, db)[..., None]
    col = lerp(C(104, 192, 236), C(168, 226, 250), un) * (1 + 0.05 * g)
    al = 142 + 30 * un[..., 0] + 6 * g[..., 0]
    fis, nz = motif(u, db / hw_u(u), sg)
    frost = (un[..., 0] < 0.05 + 0.06 * nz) & (nz > 0.35)
    arete = de < wb_u(u) + 0.07
    for m, c, a in ((fis, BLANC, 215), (frost, C(236, 248, 255), 222), (arete, BLANC, 212)):
        col = np.where(m[..., None], c, col)
        al = np.where(m, a, al)
    return col, al, None


def peau_biseau(u, db, de, sg):
    f = de / wb_u(u)
    un = np.clip(u / L_BR, 0, 1)
    g = chevrons(u, db)
    col = lerp(C(196, 238, 255), C(140, 208, 242), np.clip(f, 0, 1)[..., None]) * (1 + 0.04 * g)[..., None]
    al = 170 + 20 * un + 8 * g
    vide = de < D_OFF + 0.03                     # pas d'âme derrière : glace plus dense (sinon un vide le long du fil)
    col = np.where(vide[..., None], lerp(col, C(170, 226, 250), 0.5), col)
    al = np.where(vide, 206, al)
    fis, nz = motif(u, db / hw_u(u), sg)
    frost = (un < 0.05 + 0.06 * nz) & (nz > 0.35)
    for m, c, a in ((frost, C(236, 248, 255), 222), (f > 0.88, BLANC, 212), (f < 0.14, BLANC, 225)):
        col = np.where(m[..., None], c, col)
        al = np.where(m, a, al)
    return col, al, None


def peau_fil(u, db, de, sg):
    return np.zeros(u.shape + (3,), np.float32) + BLANC, np.full(u.shape, 225.0), None


def ame_plat(u, db, de, sg):
    un = np.clip(u / L_BR, 0, 1)
    k1 = np.clip(un / 0.22, 0, 1)[..., None]
    k2 = np.clip((un - 0.22) / 0.78, 0, 1)[..., None]
    col = lerp(lerp(G_DEEP, G_BODY, k1), G_PALE, k2 * 0.6)
    hw = hw_u(u)
    adb = np.abs(db)
    col = col * (0.62 + 0.25 * np.clip(adb / hw, 0, 1))[..., None]
    col = col * (1 + 0.07 * chevrons(u, db))[..., None]
    em = np.zeros(col.shape, np.float32)
    cw = 0.13 * (1 - 0.35 * un)
    halo = adb < cw + 0.09
    col[halo] = lerp(col[halo], C(150, 226, 250), 0.55)
    coeur = adb < cw
    col[coeur] = lerp(C(200, 248, 255), C(120, 214, 246), np.clip(adb[coeur] / cw[coeur], 0, 1)[..., None])
    em[coeur] = LUEUR
    fis, _ = motif(u, db / hw, sg)
    col[fis & ~coeur] = lerp(col[fis & ~coeur], BLANC, 0.2)
    col[de < wb_u(u) + D_C_EXTRA + 0.05] = G_DEEP * 0.8                  # arête sombre : la facette se lit
    return col, None, em


def ame_biseau(u, db, de, sg):
    wb = wb_u(u) + D_C_EXTRA
    f = np.clip((de - D_OFF) / np.maximum(wb - D_OFF, 0.05), 0, 1)[..., None]
    col = lerp(G_PALE, G_BODY, f * 0.8) * (1 + 0.05 * chevrons(u, db))[..., None]
    col[f[..., 0] > 0.86] = G_DEEP * 0.8                                   # même arête sombre que le plat (trait continu)
    return col, None, None


def ame_fil(u, db, de, sg):
    return np.zeros(u.shape + (3,), np.float32) + G_BODY, None, None


def points_face(c, X, Y, Z, s, face, dens):
    sx, sy, sz = s
    dims = {"south": (sx, sy), "north": (sx, sy), "down": (sx, sz), "up": (sx, sz), "east": (sz, sy), "west": (sz, sy)}[face]
    W, H = max(2, int(round(dims[0] * dens))), max(2, int(round(dims[1] * dens)))
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    U_, V_ = np.meshgrid(u, v)
    if face == "south":
        x, y, z = -sx / 2 + U_ * sx, sy / 2 - V_ * sy, np.full_like(U_, sz / 2)
    elif face == "down":
        x, y, z = -sx / 2 + U_ * sx, np.full_like(U_, -sy / 2), sz / 2 - V_ * sz
    else:
        raise ValueError(face)
    return c + x[..., None] * X + y[..., None] * Y + z[..., None] * Z


def spec_local(g, nom, c, X, Y, s, peintures, trans, dens):
    """Cube du repère local de la branche ; peintures : {face: fn(P (H, W, 3) local) -> (col, alpha, em, masque)}."""
    X = unit(X)
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    Z = np.cross(X, Y)
    c = np.asarray(c, float)
    faces = {}
    for f, fn in peintures.items():
        if f"{nom}_{f}" in TILES:
            faces[f] = f"{nom}_{f}"
            continue
        Pp = points_face(c, X, Y, Z, s, f, dens)
        col, al, em, m = fn(Pp)
        if m.any():
            faces[f] = tuile(f"{nom}_{f}", *finir(col, al, em, m), trans=trans)
    add(g, nom, C0 + BW @ c, BW @ np.column_stack([X, Y, Z]), np.asarray(s, float) / 2, faces)


def own_peau(idx, u, db):
    """Peau : tronçon idx (côté dos si idx < NSEG) = bande [u_k − EPS, u_k+1) du bon côté de la ligne médiane."""
    side, k = divmod(idx, NSEG)
    lo = BR_US[k] - (EPS_PEAU if k > 0 else 9.0)
    hi = BR_US[k + 1] if k < NSEG - 1 else 99.0
    return ((db >= 0) == (side == 0)) & (u >= lo) & (u < hi)


BR_US = np.linspace(0, L_BR, NSEG + 1)


def volume(br, gp, cle, ame):
    """Peau (ame=False, trans_) ou âme opaque (ame=True, plans parallèles décalés de DELTA vers l'intérieur) d'une branche."""
    pb, pf, pp = (ame_biseau, ame_fil, ame_plat) if ame else (peau_biseau, peau_fil, peau_plat)
    dens = DF_AME if ame else DF
    pref = f"{cle}_{'a' if ame else 'p'}"
    for idx, (p, q, u0, u1) in enumerate(br.segs):
        d = unit(q - p)
        n = np.array((-d[1], d[0]))
        if not in_poly(np.array([(p + q) / 2 + n * 0.05]), br.poly)[0]:
            n = -n
        wmax = float(wb_u(min(u0, u1)))
        e0 = e1 = 0.12
        Ln = float(np.linalg.norm(q - p)) + e0 + e1
        mid = (p - d * e0 + q + d * e1) / 2
        d0 = D_OFF if ame else 0.0
        z0 = ZC_MIN if ame else Z_E
        sy = (wmax + (D_C_EXTRA if ame else 0.0) - d0 + 0.1) / math.cos(AL)
        for sg in (1, -1):
            Y = np.array((n[0] * math.cos(AL), n[1] * math.cos(AL), sg * math.sin(AL)))
            X = np.array((d[0], d[1], 0.0))
            if np.cross(X, Y)[2] * sg < 0:
                X = -X
            Z = np.cross(X, Y)
            c = np.array((mid[0] + n[0] * d0, mid[1] + n[1] * d0, sg * z0)) + Y * (sy / 2) - Z * (TH / 2)

            def haut(Pp, idx=idx, sg=sg):
                P2 = Pp[..., :2]
                D = d_stack(P2, br.segs)
                de = D.min(0)
                u, db = br.proj(P2)
                lim = wb_u(u) + (D_C_EXTRA if ame else 0.0) + 0.03
                own = (D[idx] <= de + RECOUV_AME) if ame else own_peau(idx, u, db)
                m = in_poly(P2, br.poly) & own & (de < lim) & (de >= d0 - 0.02)
                col, al, em = pb(u, db, de, sg)
                return col, al, em, m

            def fil(Pp, idx=idx, n=n, sg=sg):
                P2 = Pp[..., :2] + n * (d0 + 0.04)
                D = d_stack(P2, br.segs)
                u, db = br.proj(P2)
                own = (D[idx] <= D.min(0) + RECOUV_AME) if ame else own_peau(idx, u, db)
                m = in_poly(P2, br.poly) & own
                col, al, em = pf(u, db, D.min(0), sg)
                return col, al, em, m

            spec_local(gp, f"{pref}_bis{'pm'[sg < 0]}{idx}", c, X, Y, (Ln, sy, TH), {"south": haut, "down": fil}, not ame, dens)
    # plats : une plaque par bande et par face, inclinée pour suivre l'amincissement
    ub = np.linspace(0, L_BR, NBANDE + 1)
    dz = DELTA if ame else 0.0
    for k in range(NBANDE):
        ca, _, _ = br.at(ub[k])
        cb_, _, _ = br.at(ub[k + 1])
        t = unit(cb_ - ca)
        nn = np.array((-t[1], t[0]))
        ch = float(np.linalg.norm(cb_ - ca))
        sl = float((h_u(ub[k + 1]) - h_u(ub[k])) / ch)
        uu = np.linspace(ub[k] - 0.1, ub[k + 1] + 0.1, 12)
        pts = []
        for u in uu:
            c_, _, nr = br.at(float(np.clip(u, 0, L_BR)))
            w = float(hw_u(u)) + 0.05
            pts += [c_ + nr * w, c_ - nr * w]
        pts = np.array(pts) - ca
        ta, na = pts @ t, pts @ nn
        t0, t1, n0, n1 = ta.min(), ta.max(), na.min(), na.max()
        ctr = ca + t * (t0 + t1) / 2 + nn * (n0 + n1) / 2
        zc = float(h_u(ub[k])) + sl * (t0 + t1) / 2 - dz
        lo, hi = ub[k], ub[k + 1]
        for sg in (1, -1):
            X = unit(np.array((t[0], t[1], sg * sl)))
            Y = np.array((nn[0], nn[1], 0.0)) * sg
            Z = np.cross(X, Y)
            c = np.array((ctr[0], ctr[1], sg * zc)) - Z * (TH / 2)

            def plat(Pp, sg=sg, lo=lo, hi=hi, k=k):
                P2 = Pp[..., :2]
                de = d_stack(P2, br.segs).min(0)
                u, db = br.proj(P2)
                if ame:
                    band = (u >= lo - RECOUV_AME) & (u <= hi + RECOUV_AME)
                else:
                    band = ((u >= lo - EPS_PEAU) | (k == 0)) & ((u < hi) | (k == NBANDE - 1))
                m = in_poly(P2, br.poly) & band & (de >= wb_u(u) + (D_C_EXTRA if ame else 0.0) - 0.03)
                col, al, em = pp(u, db, de, sg)
                return col, al, em, m

            spec_local(gp, f"{pref}_plat{'pm'[sg < 0]}{k}", c, X, Y, ((t1 - t0) * math.sqrt(1 + sl * sl), n1 - n0, TH),
                       {"south": plat}, not ame, dens)




# ------------------------------------------------------------------ tuiles propres à l'arbalète
def p_givre(xn, t, ex):
    """Givre (trans_) : blanc mat en plumes, plus dense au bord."""
    k = np.clip(0.6 + 0.3 * np.abs(xn) + ex.get("clair", 0.0), 0, 1)
    col = lerp(C(170, 214, 238), BLANC, k[..., None]) * (1 + 0.04 * np.sin(t * 29 + xn * 7))[..., None]
    al = 196 + 30 * np.abs(xn)
    return col, None, al


PEINTRES["givre"] = p_givre
GIVRE_T = t_unie("givre", 16, 6, BLANC, C(176, 220, 244))
GIVRE_CAP = t_unie("givre_bout", 6, 6, BLANC, C(200, 232, 250))
FG = {f: GIVRE_T for f in ("south", "north", "up", "down")}
FG.update(east=GIVRE_CAP, west=GIVRE_CAP)
FA = strip("argent", "argent_cap")
FB_ = {f: BRAS_T for f in ("south", "north", "up", "down")}
FB_.update(east=BRAS_CAP, west=BRAS_CAP)

# ================================================================== fût (toujours dessiné)
arc = group("arbalete", P(0, 0))
tarc = group("trans_cristaux_fut", P(S_PIED, 0), parent=arc)
T_STR = 1.05                     # corde et axe du carreau
A_NOIX = -1.9
A_LATCH = -1.4                   # la corde s'accroche devant la noix
S_MED = -4.3                     # médaillon de la crosse
Z_FUT = -0.15

# arbrier d'argent (octogonal), rails, rainure lumineuse où glisse le carreau
octo(arc, "arbrier", P(-6.3, 0, Z_FUT), P(5.0, 0, Z_FUT), 0.6, "argent", "argent_cap", ov=0.0, rz=0.62)
for sg in (1, -1):
    octo(arc, f"rail_{'dg'[sg < 0]}", P(-1.7, sg * 0.42, 0.62), P(4.7, sg * 0.42, 0.62), 0.22, "argent", "argent_cap", ov=0.0)
box(arc, "rainure", P(-1.5, 0, 0.5), P(4.5, 0, 0.5), 0.14, 0.1, strip("ame_fl", "ame_fl"))
# noix : bague d'argent en travers, qui tient la corde
tour(arc, "noix", P(A_NOIX, -0.62, 0.5), H_, Z_, bague(0.0, 1.24, 0.44, 0.52, 0.44, c=0.1), n=8, phase=math.pi / 8)
# détente et pontet sous l'arbrier
barre(arc, "detente", P(-2.55, 0, -0.6), P(-2.95, 0, -1.75), 0.12, 45, FA)
for nm, a, b in (("pontet_av", (-1.9, -0.65), (-2.1, -1.95)), ("pontet_bas", (-2.1, -1.95), (-3.85, -1.95)),
                 ("pontet_ar", (-3.85, -1.95), (-4.0, -0.65))):
    barre(arc, nm, P(a[0], 0, a[1]), P(b[0], 0, b[1]), 0.11, 45, FA)

# logement de l'arc (bloc d'argent en travers), grappes de cristaux qui poussent devant
octo(arc, "logement", P(S_PIED, -1.6, 0), P(S_PIED, 1.6, 0), 1.05, "argent", "argent_cap", ov=0.0, rz=0.9)
for sg in (1, -1):          # bagues aux deux bouts du logement : il se lit comme un collier, pas comme une boîte
    tour(arc, f"bague_log_{'dg'[sg < 0]}", P(S_PIED, sg * 1.2, 0), H_ * sg, Z_, bague(0.0, 0.42, 1.08, 1.16, 1.08, c=0.1), n=8,
         phase=math.pi / 8, cle="bague_log")
tour(arc, "collet_av", P(5.0, 0, Z_FUT), S_, Z_, bague(0.0, 0.5, 0.62, 0.7, 0.55, c=0.1), n=8, phase=math.pi / 8)
cristal(tarc, arc, "nez", P(5.35, 0, 0), S_, 2.1, 0.44, cle="nez")
for sg in (1, -1):
    d = S_ * math.cos(math.radians(32)) + H_ * sg * math.sin(math.radians(32))
    cristal(tarc, arc, f"nez_{'dg'[sg < 0]}", P(5.15, sg * 0.35, 0.05), d, 1.35, 0.3, cle="nez2")
    cristal(tarc, arc, f"grappe_{'dg'[sg < 0]}", P(S_PIED + 0.55, sg * 1.3, 0.15),
            unit(S_ * 0.75 + H_ * sg * 0.55 + Z_ * 0.35), 1.1, 0.26, cle="grappe")
# étrier en demi-flocon (barres à section losange) devant le nez
ETR = [(5.1, 1.15), (6.5, 1.5), (7.6, 0.72), (7.6, -0.72), (6.5, -1.5), (5.1, -1.15)]
for k in range(len(ETR) - 1):
    a, b = ETR[k], ETR[k + 1]
    barre(arc, f"etrier{k}", P(a[0], a[1], -0.55), P(b[0], b[1], -0.55), 0.14, 45, FB_)
for sg in (1, -1):
    barre(arc, f"etrier_pied_{'dg'[sg < 0]}", P(4.75, sg * 1.0, -0.2), P(5.1, sg * 1.15, -0.55), 0.14, 45, FB_)
    barre(arc, f"etrier_epine_{'dg'[sg < 0]}", P(6.5, sg * 1.5, -0.55), P(7.05, sg * 1.95, -0.55), 0.1, 45, FB_)

# crosse : médaillon d'argent (flocon en relief et gemme sur les deux faces), bague, prise cloutée, talon de cristal
R_MED, B_MED = 1.15, 0.62
tour(arc, "medaillon", P(S_MED, 0, -B_MED), Z_, S_, [(0.0, R_MED - 0.08, 0.1, R_MED, [("argent", {"clair": 0.15})]),
                                                     (0.1, R_MED, 2 * B_MED - 0.1, R_MED, [("argent", {}), ("argent", {"clair": -0.08})]),
                                                     (2 * B_MED - 0.1, R_MED, 2 * B_MED, R_MED - 0.08, [("argent", {"clair": 0.15})])],
     n=8, phase=math.pi / 8, cle="med")
TD = t_disque("disque_med", 8, R_MED - 0.06)
ETOILES = []
for sz_, nm in ((1, "dessus"), (-1, "dessous")):
    cf = P(S_MED, 0, sz_ * B_MED)
    fl = group(f"flocon_{nm}", cf, parent=arc)
    disque(fl, f"couvercle_{nm}", cf, Z_ * sz_, S_, 8, R_MED - 0.06, TD)
    zc = cf + Z_ * sz_ * 0.1
    Rf = 0.98
    for k in range(3):
        th = math.radians(60 * k)
        e = math.cos(th) * S_ + math.sin(th) * H_
        barre(fl, f"bras_{nm}{k}", zc - e * Rf, zc + e * Rf, 0.1, 45, FB_)
    for k in range(6):
        th = math.radians(60 * k)
        e = math.cos(th) * S_ + math.sin(th) * H_
        for fr, ln in ((0.5, 0.34), (0.78, 0.24)):
            base = zc + Z_ * sz_ * 0.01 + e * Rf * fr
            for sg in (-1, 1):
                t2 = th + sg * math.radians(55)
                e2 = math.cos(t2) * S_ + math.sin(t2) * H_
                barre(fl, f"branche_{nm}{k}{'pm'[sg < 0]}{int(fr * 10)}", base - e2 * 0.04, base + e2 * ln, 0.07, 45, FB_)
    tour(fl, f"gemme_{nm}", cf + Z_ * sz_ * 0.04, Z_ * sz_, S_,
         [(0.0, 0.36, 0.2, 0.36, [("gemme", {"clair": 0.1}), ("gemme", {"clair": -0.1})]),
          (0.2, 0.36, 0.48, 0.0, [("gemme", {"clair": 0.2}), ("gemme", {})])], n=6, cle="gemme")
# étincelles du repos (item_idle) et de la sélection (event_select) : étoiles cachées dans le médaillon
for k, sz_ in enumerate((1, -1, 1)):
    ce = P(S_MED + 0.06 * (k == 2), 0, sz_ * (0.3 - 0.05 * (k == 2)))
    g = group(f"etoile_{k}", ce, parent=arc)
    plaque(g, f"etoile_{k}", ce, S_, H_ if sz_ > 0 else -H_, 0.9 / K, 0.9 / K, 0.3 / K, "etoile")
    ETOILES.append((g, sz_))
SORTIE = B_MED + 0.62

tour(arc, "bague_crosse", P(-6.35, 0, Z_FUT), -S_, Z_, bague(0.0, 0.45, 0.66, 0.78, 0.7, c=0.1), n=8, phase=math.pi / 8, cle="bg")
octo(arc, "prise", P(-6.75, 0, Z_FUT), P(-8.35, 0, Z_FUT), 0.68, "cuir", "cuir_cap", ov=0.0, rz=0.7)
for k in range(3):        # clous d'argent sur la prise (dessus et dessous)
    for sz_ in (1, -1):
        c = P(-7.05 - 0.5 * k, 0, Z_FUT + sz_ * 0.66)
        tour(arc, f"clou{k}{'pm'[sz_ < 0]}", c, Z_ * sz_, S_, [(0.0, 0.16, 0.12, 0.08, [("argent", {"clair": 0.2})])], n=6, cle="clou")
tour(arc, "bague_talon", P(-8.3, 0, Z_FUT), -S_, Z_, bague(0.0, 0.42, 0.72, 0.82, 0.62, c=0.1), n=8, phase=math.pi / 8, cle="bt")
cristal(tarc, arc, "talon", P(-8.6, 0, Z_FUT), -S_, 1.35, 0.46, cle="talon")

# nuage de flocons du tir (event_release) : flocons trans_ cachés K fois plus petits dans le logement
C_N = P(S_PIED + 0.2, 0, 0.35)
nuage = group("trans_nuage", C_N, parent=arc)
group("ctrl_alpha", C_N, parent=nuage)
FLOCONS = []
for k in range(9):
    a = math.radians(20 + 40 * k)
    radial = math.cos(a) * H_ + math.sin(a) * Z_
    g = group(f"trans_flocon_{k}", C_N, parent=nuage)
    sz = (1.3 if k % 3 == 0 else 0.95) / K
    plaque(g, f"flocon_{k}", C_N + H_ * 0.04 * (k - 4), H_, unit(S_ * 0.3 + Z_), sz, sz, 0.3 / K, "eclat")
    FLOCONS.append((g, radial, k))
EMIT = group("emit_mc_snowflake", P(7.2, 0, T_STR), parent=arc, rotation=(0, 0, 45))
group("ctrl_emit", P(7.2, 0, T_STR), parent=EMIT)


# ================================================================== arc (une version par étape)
ROT_BAS = 2 * np.outer(S_, S_) - np.eye(3)        # 180° autour de l'axe de tir (h = H_AXE)
O_BAS = P(0.0, H_AXE)


def vers_bas(p):
    return O_BAS + ROT_BAS @ (np.asarray(p, float) - O_BAS)


def branche(stage, d):
    """Branche droite (volume peau + âme, cristal du dos, poupée, pointe), puis sa copie tournée (branche gauche)."""
    br = Branche(d)
    construire_fils(br)
    cle = f"br{int(round(d * 100)):03d}"
    root = C0 + BW @ np.array((br.cl[0][0], br.cl[0][1], 0.0))
    i0 = len(CUBES)
    gb = group(f"branche_d_{stage}", root, parent=stage)
    gt = group(f"trans_branche_d_{stage}", root, parent=gb)
    volume(br, gb, cle, True)
    volume(br, gt, cle, False)

    def W(p2, z=0.0):
        return C0 + BW @ np.array((p2[0], p2[1], z))

    def Wd(v2):
        return BW @ np.array((v2[0], v2[1], 0.0))
    # cristal sur le dos (côté avant), penché vers la pointe
    u = 0.42 * L_BR
    c_, t, nr = br.at(u)
    base = W(c_ + nr * (float(hw_u(u)) - 0.24))
    cristal(gt, gb, f"ec_{stage}", base, Wd(nr) * math.cos(math.radians(48)) + Wd(t) * math.sin(math.radians(48)), 1.5, 0.3,
            cle="eclat_dos")
    c_, t, nr = br.at(L_BR)
    tip, dirb = W(c_), Wd(t)
    tour(gb, f"poupee_{stage}", tip - dirb * 0.42, dirb, Z_, bague(0.0, 0.7, 0.5, 0.58, 0.44, c=0.1), n=8, phase=math.pi / 8,
         cle="poupee")
    cristal(gt, gb, f"pointe_{stage}", tip + dirb * 0.22, dirb, 1.15, 0.3, cle="pointe")
    n_haut = len(CUBES)
    gbb = group(f"branche_g_{stage}", vers_bas(root), parent=stage)
    gtb = group(f"trans_branche_g_{stage}", vers_bas(root), parent=gbb)
    for cb in CUBES[i0:n_haut]:
        add(gbb if cb["groupe"] == gb else gtb, cb["nom"] + "_b", vers_bas(cb["c"]), ROT_BAS @ cb["R"], cb["half"], dict(cb["faces"]))
    # tenons d'argent verticaux où la corde s'attache (au-dessus de l'arc, à la hauteur du carreau)
    nks = []
    for g_, p in ((gb, tip - dirb * 0.08), (gbb, vers_bas(tip - dirb * 0.08))):
        barre(g_, f"tenon_{g_}", p - Z_ * 0.42, p + Z_ * (T_STR + 0.2), 0.15, 22.5, FA)
        nks.append(p + Z_ * T_STR)
    return nks[0], nks[1], gb, gbb, br


def corde(g, a, b, nm):
    box(g, nm, a, b, 0.11, 0.11, strip("corde", "corde"), ov=0.06)


def aiguilles(g, nm, s0, s1, z, r0, n=5, ln=0.42):
    """Givre en plumes : paires d'aiguilles (barres à section losange) qui partent du fût vers l'arrière, en trois rangs."""
    for i in range(n):
        s = lerp(s0, s1, i / max(n - 1, 1))
        for j, ang in enumerate((90, 210, 330)):
            rr = math.radians(ang + 25 * (i % 2))
            e = math.cos(rr) * Z_ + math.sin(rr) * H_
            b = P(s, 0, z) + e * (r0 - 0.04)
            d = unit(e * 0.8 - S_ * 0.6)
            barre(g, f"{nm}{i}{j}", b, b + d * ln * (0.8 + 0.3 * ((i + j) % 2)), 0.065, 45, FG)


# (nom, tension, recul de la corde 0..1, chargement)
ETAPES = [("repos", 0.0, 0.0, None), ("bande_1", 0.33, 0.33, None), ("bande_2", 0.66, 0.66, None),
          ("bande_3", 1.0, 1.0, None), ("chargee", 1.0, 1.0, "carreau"), ("chargee_fusee", 1.0, 1.0, "fusee")]
STAGE, BR, CORDE, GIVRE, ETOILE_C = {}, {}, {}, {}, {}
PROF_P = [(0.0, 0.2, 0.5, 0.5, CRIS_PEAU), (0.5, 0.5, 2.1, 0.0, CRIS_PEAU)]
PROF_A = [(0.1, 0.16, 0.55, 0.32, CRIS_AME), (0.55, 0.32, 1.8, 0.0, CRIS_AME)]
for nom_e, d, rec, charg in ETAPES:
    g = group(objet.etape(nom_e, "arbalete"), P(S_MED, 0))
    STAGE[nom_e] = g
    nd, ng, gh, gbas, br = branche(g, d)
    BR[nom_e] = (gh, gbas)
    if rec == 0:
        gc = group(f"corde_{nom_e}", (nd + ng) / 2, parent=g)
        corde(gc, nd, ng, f"corde_droite_{nom_e}")
        CORDE[nom_e] = gc
        print("repos : tenons à s =", round(float((nd - C0) @ S_), 2), "; envergure", round(float((nd - ng) @ H_), 2))
        continue
    a_rest = float((nd - C0) @ S_)
    nock = P(lerp(a_rest, A_LATCH, rec), 0, T_STR)
    gc = group(f"corde_{nom_e}", nock, parent=g)
    corde(gc, nd, nock, f"corde_d_{nom_e}")
    corde(gc, ng, nock, f"corde_g_{nom_e}")
    CORDE[nom_e] = gc
    tour(gc, f"tranchefil_{nom_e}", nock - H_ * 0.42, H_, Z_, bague(0.0, 0.84, 0.24, 0.3, 0.24, c=0.1), n=8, phase=math.pi / 8,
         cle="tranchefil")
    if charg == "carreau":
        # carreau de cristal : fût lumineux, encoche d'argent, trois pennes de glace, pointe en losange de cristal
        gfl = group(f"carreau_{nom_e}", nock, parent=g)
        octo(gfl, "carreau_fut", P(A_LATCH + 0.3, 0, T_STR), P(4.95, 0, T_STR), 0.15, "ame_fl", "ame_fl", ov=0.0)
        tour(gfl, "encoche", P(A_LATCH + 0.05, 0, T_STR), S_, Z_, bague(0.0, 0.42, 0.2, 0.25, 0.2, c=0.08), n=8, phase=math.pi / 8,
             cle="encoche")
        tour(gfl, "virole", P(4.6, 0, T_STR), S_, Z_, bague(0.0, 0.42, 0.2, 0.25, 0.22, c=0.08), n=8, phase=math.pi / 8, cle="virole")
        gp = group("trans_pennes", P(A_LATCH + 1.1, 0, T_STR), parent=gfl)
        for k, ang in enumerate((0, 120, -120)):
            rr = math.radians(ang)
            upv = Z_ * math.cos(rr) + H_ * math.sin(rr)
            plaque(gp, f"penne_{k}", P(A_LATCH + 1.1, 0, T_STR) + upv * 0.4, -S_, upv, 0.6, 0.25, 0.3, "penne")
        base = P(4.95, 0, T_STR)
        gt_ = group("pointe_carreau", base, parent=gfl)
        gtt = group("trans_pointe_carreau", base, parent=gt_)
        tour(gtt, "pointe_peau", base, S_, Z_, PROF_P, n=6, phase=math.pi / 6, cle="cr_p")
        tour(gt_, "pointe_coeur", base, S_, Z_, PROF_A, n=6, phase=math.pi / 6, cle="cr_a")
        ce = base + S_ * 1.0
        ge = group("etoile_carreau", ce, parent=gt_)
        plaque(ge, "etoile_carreau", ce, H_, S_, 1.1 / K, 1.1 / K, 0.3 / K, "etoile")
        ETOILE_C[nom_e] = ge
        # le givre couvre le carreau une fois chargé (groupe que event_charged fait pousser)
        gv = group("givre_carreau", P(1.8, 0, T_STR), parent=gfl)
        aiguilles(gv, "aig_c", A_LATCH + 2.2, 4.3, T_STR, 0.15, n=6)
        tgv = group("trans_givre_carreau", base, parent=gv)
        tour(tgv, "collier", base + S_ * 0.08, S_, Z_, [(0.0, 0.3, 0.32, 0.56, [("givre", {}), ("givre", {"clair": 0.1})])],
             n=6, phase=0.0, cle="collier")
        GIVRE[nom_e] = gv
    elif charg == "fusee":
        # fusée : papier bleu nuit cerclé d'argent, coiffe de cristal, givre en plumes
        gfu = group(f"fusee_{nom_e}", nock, parent=g)
        tf = T_STR + 0.22
        octo(gfu, "fusee_corps", P(A_LATCH + 0.1, 0, tf), P(A_LATCH + 3.45, 0, tf), 0.42, "cuir", "cuir_cap", ov=0.0)
        for k, a0 in enumerate((0.35, 1.65, 2.95)):
            tour(gfu, f"cercle{k}", P(A_LATCH + a0, 0, tf), S_, Z_, bague(0.0, 0.26, 0.46, 0.5, 0.46, c=0.06), n=8, phase=math.pi / 8,
                 cle="cercle")
        tgf = group("trans_coiffe_fusee", P(A_LATCH + 3.4, 0, tf), parent=gfu)
        cristal(tgf, gfu, "coiffe", P(A_LATCH + 3.4, 0, tf), S_, 1.4, 0.4, cle="coiffe")
        barre(gfu, "meche", P(A_LATCH + 0.12, 0, tf), P(A_LATCH - 0.3, 0, tf - 0.25), 0.06, 45, FG)
        ce = P(A_LATCH + 4.2, 0, tf)
        ge = group("etoile_fusee", ce, parent=gfu)
        plaque(ge, "etoile_fusee", ce, H_, S_, 1.1 / K, 1.1 / K, 0.3 / K, "etoile")
        ETOILE_C[nom_e] = ge
        gv = group("givre_fusee", P(A_LATCH + 1.8, 0, tf), parent=gfu)
        aiguilles(gv, "aig_f", A_LATCH + 0.7, A_LATCH + 3.1, tf, 0.42, n=4, ln=0.4)
        GIVRE[nom_e] = gv


# ================================================================== atlas
UV = {}
CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]


def atlas():
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, (im, ime) in sorted(TILES.items(), key=lambda it: (-it[1][0].shape[0], -it[1][0].shape[1])):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, f"atlas plein ({n}, y = {y})"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if ime is not None:
            tex_e[y:y + h, x:x + w] = ime
        x += w + 1
        shelf = max(shelf, h)
    tex[..., :3] &= 0xFC
    tex[tex[..., 3] == 0] = 0
    assert tex[TEX - 2, TEX - 2, 3] == 0
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    zone = np.zeros(semi.shape, bool)
    for n in TRANS:
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


# ================================================================== émission
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


def uv_face(v):
    if v is None:
        return CLEAR
    if isinstance(v, tuple):
        u0, v0, u1, v1 = UV[v[0]]
        return [u1, v0, u0, v1]
    return list(UV[v])


elements = []
for cb in CUBES:
    c, h, R = cb["c"], cb["half"], cb["R"]
    assert abs(np.linalg.det(R) - 1) < 1e-6, cb["nom"]
    assert h.min() * 2 >= 0.3 / K - 1e-6, cb["nom"]
    rot = euler(R)
    e = {"name": cb["nom"], "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in c - h],
         "to": [round(float(v), 4) for v in c + h], "origin": [round(float(v), 4) for v in c], "box_uv": False,
         "faces": {f: {"uv": uv_face(cb["faces"].get(f)), "texture": 0} for f in SIX}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[cb["groupe"]]["ids"].append(e["uuid"])


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node(arc)] + [bone_node(STAGE[e[0]]) for e in ETAPES]


# ================================================================== animations
def kf(t, x, y, z, ch="rotation"):
    def f(v):          # jamais de notation scientifique (« 1e-05 » serait lu comme une expression Molang)
        if isinstance(v, str):
            return v
        t = f"{round(float(v), 4) + 0.0:.4f}".rstrip("0").rstrip(".")
        return "0" if t in ("", "-0") else t
    return {"channel": ch, "data_points": [{"x": f(x), "y": f(y), "z": f(z)}], "time": round(t, 4), "interpolation": "linear"}


def anim(name, length, tracks, fps=24, loop="loop"):
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A_ = {}
    for (g, ch), f in tracks.items():
        ks = [kf(t, *f(t), ch=ch) for t in times] if callable(f) else [kf(0.0, *f, ch=ch), kf(length, *f, ch=ch)]
        A_.setdefault(groups[g]["uuid"], {"name": g, "type": "bone", "keyframes": []})["keyframes"] += ks
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": False, "animators": A_}


def le_long(v, d):
    w = np.asarray(d, float) * v
    return float(w[0]), float(w[1]), float(w[2])


def pop(t, t0, dur, kmax=K):
    """Échelle d'un élément caché : 1 (caché) -> kmax (montré) -> 1, montée rapide, descente plus lente."""
    w = sm(t, t0, t0 + dur * 0.25) * (1 - sm(t, t0 + dur * 0.45, t0 + dur))
    k = 1 + (kmax - 1) * w
    return k, k, k


# --- item_idle (8 s) : deux scintillements sur les flocons du médaillon, rien d'autre
L_IDLE = 8.0
POPS = [(1.8, 0.7), (5.6, 0.7)]
idle_tracks = {("ctrl_emit", "position"): (-1, 0, 0)}
for (g, sz_), (t0, du) in zip(ETOILES[:2], POPS):
    idle_tracks[(g, "scale")] = (lambda t, t0=t0, du=du: pop(t, t0, du))
    idle_tracks[(g, "position")] = (lambda t, t0=t0, du=du, sz_=sz_: le_long(SORTIE * sz_ * (sm(t, t0 - 0.05, t0 + 0.1) * (1 - sm(t, t0 + du, t0 + du + 0.05))), Z_))
item_idle = anim("item_idle", L_IDLE, idle_tracks, fps=20)

# --- item_use (boucle 0,5 s) : l'arbalète frémit avec la tension (q.use_progress)
TREM = "math.sin(q.anim_time * 360 * 14) * 0.7 * q.use_progress * q.use_progress"
use_tracks = {("ctrl_emit", "position"): (-1, 0, 0)}
for e in ("bande_1", "bande_2", "bande_3"):
    use_tracks[(STAGE[e], "rotation")] = (0, 0, TREM)
item_use = anim("item_use", 0.5, use_tracks)


# --- event_charged (0,6 s) : le givre couvre le carreau (ou la fusée) d'un coup, étoile à la pointe
def givre_scale(t):
    k = lerp(0.12, 1.0, sm(t, 0.02, 0.3)) + 0.12 * bump(t, 0.22, 0.3, 0.34, 0.5)
    return k, k, k


ch_tracks = {}
for e in ("chargee", "chargee_fusee"):
    ch_tracks[(GIVRE[e], "scale")] = givre_scale
    ch_tracks[(ETOILE_C[e], "scale")] = (lambda t: pop(t, 0.18, 0.36))
event_charged = anim("event_charged", 0.6, ch_tracks, fps=40, loop="once")


# --- event_release (0,8 s) : nuage de flocons devant l'arc, corde qui vibre, arc qui frissonne, flocons de Minecraft, un son
def alpha_nuage(t):
    return -sm(t, 0.35, 0.72), 0.0, 0.0


rel = {("ctrl_alpha", "position"): alpha_nuage,
       ("ctrl_emit", "position"): lambda t: (7 * bump(t, 0.0, 0.03, 0.14, 0.24) - 1, 0.0, 0.0),
       (CORDE["repos"], "position"): lambda t: le_long(0.35 * math.sin(TAU * 16 * t) * math.exp(-t / 0.14) * sm(t, 0.0, 0.02), S_)}
for g, radial, k in FLOCONS:
    def fs(t, k=k):
        w = sm(t, 0.0, 0.06) * (1 - sm(t, 0.5, 0.76))
        v = 1 + (K - 1) * w * (1 + 0.25 * sm(t, 0.06, 0.4))
        return v, v, v

    def fp(t, radial=radial, k=k):
        if t >= 0.78:
            return 0.0, 0.0, 0.0
        avance = (2.4 + 0.5 * (k % 3)) * (1 - math.exp(-t / 0.12))
        ecart = (1.5 + 0.35 * (k % 2)) * (1 - math.exp(-t / 0.2))
        w = S_ * avance + radial * ecart + Z_ * 0.6 * sm(t, 0.0, 0.05) - V(0, 1, 0) * 0.5 * sm(t, 0.25, 0.78) ** 2
        return float(w[0]), float(w[1]), float(w[2])
    rel[(g, "scale")] = lambda t, fs=fs: fs(t) if t < 0.78 else (1.0, 1.0, 1.0)
    rel[(g, "position")] = fp
    rel[(g, "rotation")] = lambda t, k=k: (0.0, 0.0, (160 + 30 * k) * sm(t, 0.0, 0.7) * (1 if k % 2 else -1)) if t < 0.78 else (0.0, 0.0, 0.0)
for j, g in enumerate(BR["repos"]):
    rel[(g, "rotation")] = (lambda t, j=j: (0.0, 0.0, (1.4 if j == 0 else -1.4) * math.sin(TAU * 11 * t) * math.exp(-t / 0.12) * sm(t, 0.0, 0.02)))
event_release = anim("event_release", 0.8, rel, fps=50, loop="once")
event_release["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "block.amethyst_block.chime", "file": ""}], "time": 0.02}]}


# --- event_select (0,8 s) : la glace de l'arc repousse depuis le logement, puis la corde gèle, étoile au médaillon
def grow(t):
    k = lerp(0.3, 1.0, sm(t, 0.0, 0.32)) + 0.06 * bump(t, 0.22, 0.32, 0.36, 0.5)
    return k, k, k


def corde_grow(t):
    k = sm(t, 0.3, 0.5)
    return max(k, 0.001), max(k, 0.001), max(k, 0.001)


sel = {(BR["repos"][0], "scale"): grow, (BR["repos"][1], "scale"): grow, (CORDE["repos"], "scale"): corde_grow}
g_sel, sz_sel = ETOILES[2]
sel[(g_sel, "scale")] = lambda t: pop(t, 0.48, 0.3)
sel[(g_sel, "position")] = lambda t: le_long(SORTIE * sz_sel * sm(t, 0.44, 0.5) * (1 - sm(t, 0.78, 0.8)), Z_)
event_select = anim("event_select", 0.8, sel, fps=40, loop="once")

ANIMS = [item_idle, item_use, event_charged, event_release, event_select]
ANIMS[0]["selected"] = True

# ================================================================== écriture
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]


def coins(ids=None):
    pts = []
    for e in elements:
        if ids is not None and e["uuid"] not in ids:
            continue
        lo, hi = np.array(e["from"]), np.array(e["to"])
        R = rotm(*e.get("rotation", (0, 0, 0)))
        o = np.array(e["origin"])
        for c in range(8):
            p = np.array([(lo, hi)[(c >> k) & 1][k] for k in range(3)])
            pts.append(R @ (p - o) + o)
    return np.array(pts)


def ids_de(name):
    g = groups[name]
    return set(g["ids"]).union(*[ids_de(n) for n, gg in groups.items() if gg["parent"] == name])


_P = coins(ids_de(arc) | ids_de(STAGE["repos"]))
_lo, _hi = _P[:, :2].min(0), _P[:, :2].max(0)
_c = (_lo + _hi) / 2
GUI_S = round(min(1.0, 15.4 / float(max(_hi - _lo))), 3)
GUI_T = [round(float((8 - _c[0]) * GUI_S), 2), round(float((8 - _c[1]) * GUI_S), 2), 0]
AFFICHAGE = objet.affichage("arbalete", gui={"scale": [GUI_S] * 3, "translation": GUI_T})
model = objet.modele(NOM, "arbalete", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


Pa = coins()
print("boîte :", Pa.min(0).round(2).tolist(), "->", Pa.max(0).round(2).tolist(), "; gui", GUI_S, GUI_T)
print(f"repos : longueur {float((_P @ S_).max() - (_P @ S_).min()):.1f} px le long du fût, envergure {float((_P @ H_).max() - (_P @ H_).min()):.1f} px")
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
