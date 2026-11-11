"""Effet de téléportation « Porte des étoiles » (guide 15), ensemble Stellaire, pièce phare. Design original, étude par
analogie (.claude/references/effets/porte-etoiles.md : déroulé, formes, couleurs échantillonnées, spectrogrammes) ;
fiche de style .claude/styles/stellaire.md. Écrit effet_stellaire_porte.png, effet_stellaire_porte_e.png et
.build/effet_stellaire_porte_brut.bbmodel.

Pièces (pieds du joueur à l'origine, face à -Z ; aucun groupe du corps)
- **Porte** debout à 2 blocs devant le joueur (plan z = ZP), diamètre extérieur 62 px (3,9 blocs), ouverture 48 px, enfoncée
  de 6 px dans le sol. Cadre de pierre (72 segments, frise gravée : filet d'or incrusté, constellations de points, rainures)
  ; anneau intérieur d'or (72 segments) gravé de 36 glyphes inventés dont les rainures brillent en bleu (_e), qui tourne
  par à-coups ; 9 crans (deux bras d'or en V + lentille losangée d'ambre) qui se verrouillent d'un « clac » (les bras
  s'enfoncent de 0,9 px) et s'allument (lueur add_ devant la lentille, des deux côtés).
- **Eau** : disque trans_ assez opaque (alpha 228–240 : cache la copie), deux couches de reflets trans_ en vermicelles de
  chaque côté qui tournent en sens contraires, rides add_ concentriques **devant** chaque face (jamais derrière une face
  trans_), rides au point d'entrée, éclat add_ à l'ouverture, lueur add_ au sol devant la porte, calque _e (nuit).
- **Jaillissement** : bulbe d'eau en facettes (28 × 12, trans_ écume + _e) qui jaillit à l'horizontale vers l'avant (+Z, côté
  du joueur), gonfle, se rétracte (≈ 1 s), avec gouttes.
- Arrivée : la porte entière est tournée d'un demi-tour (groupe porte, pivot à l'origine) : elle est derrière le joueur et
  il en sort en marchant vers l'avant.

Animations (une courbe lisse par phase, arrêts adoucis seulement aux vrais arrêts, 30 clés/s)
- charge (loop 20 s ; v2 du 2026-11-07 : le compte à rebours du serveur dure 3 s) : la porte sort du sol en 0,5 s
  (poussière), l'anneau intérieur tourne par à-coups et 8 crans se verrouillent un par un, de 0,78 à 2,8 s (« clac » à chaque
  cran + grondement de l'anneau, exception demandée à la règle « rien pendant la charge ») ; puis porte levée, crans qui
  pulsent ; à 19–20 s seulement (jamais vu avec 3 s) les crans s'éteignent et la porte redescend (boucle fermée).
- depart (3,6 s) : commence là où la charge s'arrête : dernier cran en haut (0,23 s, plus marqué), éclat (0,27 s),
  jaillissement, surface qui ondule ; la copie marche dans la porte, coupée (échelle < 0,05) quand son dos a passé le plan,
  rides au point d'entrée ; coupure nette (2,66 s) ; la porte redescend.
- arrivee (4,4 s) : porte levée et 9 crans allumés dès t = 0, éclat et court jaillissement, surface ouverte à 0,25 s ; le
  joueur sort du plan (caché jusqu'à 0,62 s) et avance de 2 blocs ; coupure nette à 3,0 s ; la porte redescend.
Sons embarqués originaux v3 (sons/*.py, tools/synthe.py, recette dans .claude/references/effets/porte-etoiles.md) :
porte_cran, porte_cran_b, porte_cran_c (« ka-chunk » d'un cran, trois hauteurs en alternance dans la charge ; écrits par
sons/porte_cran.py), porte_cran_fin (dernier cran, au départ), porte_gronde (pierre qui sort + rotation : roulement,
cliquetis, sifflement), porte_jaillit (boum, rugissement d'eau, retour de la gerbe, surface qui ronronne), porte_coupe
(aspiration inversée + pierre qui redescend). Versions précédentes : sons/v2/. Particules : goutte, eclat (modélisées), emit_mc_splash,
emit_mc_glow, emit_mc_poof.

Fonctions avancées : add_, trans_, ctrl_alpha, ctrl_emit, particle_/emit_, emit_mc_, _e, groupe joueur, sons embarqués.
À juger en jeu (« Essayer », /cosmetique apercu) : eau de jour et de nuit (opacité, reflets), crans allumés de jour,
particules, coupe de la copie au passage du plan, porte qui sort du sol (cachée par le terrain), avec shader.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "effet_stellaire_porte"
TEX = 512
TAU = 2 * math.pi
FPS = 30
RNG = np.random.default_rng(83)

# ------------------------------------------------------------------ dimensions (px)
ZP = -32.0                      # plan de la porte (2 blocs devant le joueur)
YC = 25.0                       # centre (bas de l'ouverture à y = 1, bas du cadre enfoui à y = -6)
R_IN, R_MID, R_OUT = 24.0, 27.5, 31.0
D_PIERRE, D_OR = 6.0, 4.4       # profondeurs (z) du cadre de pierre et de l'anneau d'or
NSEG = 72
R_EAU = 24.6
NCRAN = 9
C = np.array((0.0, YC, ZP))
Y_SOUS = -64.0                  # porte enfouie (sommet à y = -8)

# ------------------------------------------------------------------ outils de peinture
def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def reduire(arr, taille):
    out = []
    for c in range(arr.shape[2]):
        im = Image.fromarray(np.clip(arr[..., c], 0, 255).astype(np.uint8), "L").resize(taille, Image.LANCZOS)
        out.append(np.asarray(im).astype(float))
    return np.stack(out, axis=-1)


def bruit(n, echelle, seed):
    """Bruit lisse n × n (interpolation bicubique d'une grille aléatoire)."""
    r = np.random.default_rng(seed)
    g = r.standard_normal((echelle + 3, echelle + 3))
    im = Image.fromarray(((g - g.min()) / (np.ptp(g) + 1e-9) * 255).astype(np.uint8), "L").resize((n * (echelle + 3) // echelle,) * 2, Image.BICUBIC)
    a = np.asarray(im).astype(float)[:n, :n] / 255
    return (a - a.mean()) / (a.std() + 1e-9)


def rgba(rgb, a=255):
    out = np.zeros(rgb.shape[:2] + (4,), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(a, 0, 255).astype(np.uint8) if np.ndim(a) else a
    return out


def rgba_e(rgb):
    out = rgba(rgb)
    out[rgb.max(axis=2) < 8] = 0
    return out


def add_rgba(rgb):
    """Additif : alpha 255 là où il y a de la lumière, noir transparent ailleurs."""
    out = rgba(rgb)
    lum = out[..., :3].max(axis=2)
    out[lum <= 6] = 0
    return out


UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)


def poser(nom, im, x, y, e=None):
    h, w = im.shape[:2]
    assert x + w <= TEX and y + h <= TEX and not tex[y:y + h, x:x + w, 3].any(), nom
    tex[y:y + h, x:x + w] = im
    if e is not None:
        tex_e[y:y + h, x:x + w] = e
    UV[nom] = (x, y, x + w, y + h)


# couleurs (fiche de style Stellaire)
OR_C, OR_B, OR_O = np.array((255, 222, 150)), np.array((204, 146, 64)), np.array((62, 34, 10))
PI_C, PI_B, PI_O = np.array((150, 150, 158)), np.array((104, 104, 114)), np.array((46, 46, 54))
BLEU_E = np.array((140, 215, 255))


def segments_tex(r0, r1, nseg, tw, th, f, SS=4):
    """Bande de nseg segments (tw × th texels chacun) d'un anneau r0..r1 : f(psi, r) -> (rgb, e) sur grilles."""
    w = 2 * r1 * math.tan(math.pi / nseg)
    W, H = tw * SS, th * SS
    u = ((np.arange(W) + 0.5) / W - 0.5) * w
    r = r1 - (np.arange(H) + 0.5) / H * (r1 - r0)
    U, Rr = np.meshgrid(u, r)
    im = np.zeros((th, tw * nseg, 3))
    em = np.zeros((th, tw * nseg, 3))
    for k in range(nseg):
        th_ = TAU * k / nseg
        x = U * math.cos(th_) - Rr * math.sin(th_)
        y = U * math.sin(th_) + Rr * math.cos(th_)
        psi = np.arctan2(-x, y) % TAU
        rr = np.hypot(x, y)
        c, e = f(psi, rr)
        im[:, tw * k:tw * (k + 1)] = reduire(c, (tw, th))
        em[:, tw * k:tw * (k + 1)] = reduire(e, (tw, th))
    return im, em, w


# 1. frise du cadre de pierre (72 × 12 × 16) : filet d'or incrusté, constellations de points, rainures entre les crans
G_PI = bruit(256, 24, 3)


def f_pierre(psi, r):
    n = G_PI[(r * 6).astype(int) % 256, (psi * 40).astype(int) % 256]
    base = PI_B[None, None] * (1 + 0.05 * n)[..., None] * (1 - 0.18 * smooth((r - 29.8) / 1.2))[..., None]
    rgb = base.copy()
    e = np.zeros_like(rgb)
    filet = np.abs(r - 28.4) < 0.33                                      # filet d'or intérieur
    rgb[filet] = OR_B
    a_cran = (psi % (TAU / NCRAN))                                        # rainure radiale entre deux crans
    mil = np.abs(a_cran - TAU / NCRAN / 2) * r < 0.3
    rgb[mil & (r > 28.9)] = PI_O
    e[mil & (r > 28.9)] = (60, 120, 170)
    # constellations : 3 points d'or par intervalle, placés par une graine fixe
    for j in range(NCRAN):
        for q, (da, rr_) in enumerate(((0.28, 29.9), (0.4, 29.3), (0.62, 30.1), (0.75, 29.5))):
            a0 = TAU / NCRAN * (j + da + 0.04 * ((j * 7 + q * 3) % 5 - 2))
            px, py = -rr_ * math.sin(a0), rr_ * math.cos(a0)
            x, y = -r * np.sin(psi), r * np.cos(psi)
            d = np.hypot(x - px, y - py)
            rgb[d < 0.42] = OR_C
            e[d < 0.42] = (255, 190, 90)
    return rgb, e


fr, fe, W_PI = segments_tex(R_MID, R_OUT, NSEG, 12, 16, f_pierre)
for j in range(2):
    poser(f"pierre{j}", rgba(fr[:, 432 * j:432 * (j + 1)]), 0, 16 * j, e=rgba_e(fe[:, 432 * j:432 * (j + 1)]))


# 2. anneau d'or : 36 glyphes inventés (rainures sombres, _e bleu vif dans les rainures)
def glyphe_masque(g, psi_l, r):
    """psi_l ∈ [0, 1] le long de la case (10°), r ∈ [24.3, 27.2] ; renvoie le masque de rainure."""
    x = (psi_l - 0.5) * (TAU / 36) * 25.8           # px, ±2,25
    y = r - 25.75                                   # px, ±1,45
    m = np.zeros_like(x, bool)
    k = g % 6
    if k == 0:
        m |= np.abs(np.hypot(x, y) - 0.95) < 0.28
        m |= np.hypot(x, y) < 0.3
    elif k == 1:
        m |= (np.abs(x) < 0.28) & (np.abs(y) < 1.2)
        m |= (np.abs(y - 0.9) < 0.28) & (np.abs(x) < 1.2)
    elif k == 2:
        for cx, cy in ((-1.1, -0.6), (0.0, 0.7), (1.1, -0.4)):
            m |= np.hypot(x - cx, y - cy) < 0.42
    elif k == 3:
        m |= np.abs(np.abs(x) * 0.9 - (y + 1.0)) < 0.3
        m &= y < 1.0
    elif k == 4:
        m |= (np.abs(y) < 0.28) & (np.abs(x) < 1.5)
        m |= np.hypot(x - 1.5, y) < 0.45
        m |= np.hypot(x + 1.5, y) < 0.45
    else:
        m |= np.abs(np.hypot(x, y + 1.6) - 1.9) < 0.28
        m &= y > -0.3
        m |= np.hypot(x, y + 0.2) < 0.35
    return m


def f_or(psi, r):
    case = (psi / (TAU / 36))
    g = np.floor(case).astype(int)
    pl = case - g
    lum = 1 + 0.10 * smooth((r - 25.0) / 2.0) - 0.12 * smooth((25.4 - r) / 1.0)
    rgb = OR_B[None, None] * lum[..., None]
    e = np.zeros_like(rgb)
    m = np.zeros(r.shape, bool)
    for gg in np.unique(g):
        sel = g == gg
        mm = glyphe_masque(int(gg) * 5 + int(gg) // 6, pl, r)
        m |= sel & mm
    sep = np.minimum(pl, 1 - pl) * (TAU / 36) * 25.8 < 0.18             # séparation entre deux glyphes
    rgb[sep] = OR_O * 1.6
    rgb[(np.abs(r - 24.45) < 0.2) | (np.abs(r - 27.05) < 0.2)] = OR_C   # bords clairs
    rgb[m] = OR_O
    e[m] = BLEU_E
    return rgb, e


gr, ge, W_OR = segments_tex(R_IN, R_MID - 0.1, NSEG, 12, 16, f_or)
for j in range(2):
    poser(f"or{j}", rgba(gr[:, 432 * j:432 * (j + 1)]), 0, 32 + 16 * j, e=rgba_e(ge[:, 432 * j:432 * (j + 1)]))


# 3. petites textures (bande y = 64..80, x 432.. ; et colonne de droite)
def uni_tex(rgb, n=16, var=0.04, seed=1, grad=0.0):
    r = np.random.default_rng(seed)
    v = np.linspace(-1, 1, n)[:, None]
    a = np.asarray(rgb, float)[None, None] * (1 + var * r.standard_normal((n, n)) + grad * -v)[..., None]
    return rgba(a)


poser("pierre_cote", uni_tex(PI_B * 0.8, 16, 0.05, 2), 432, 0)
poser("pierre_bord", uni_tex(PI_B * 1.05, 16, 0.06, 3), 448, 0)
poser("pierre_int", uni_tex(PI_O * 1.3, 16, 0.05, 4), 464, 0)
poser("or_int", uni_tex(OR_B * 0.75, 16, 0.04, 5, grad=0.15), 480, 0)
poser("or_cote", uni_tex(OR_B * 0.9, 16, 0.04, 6), 496, 0)
poser("or_bras", uni_tex(OR_B * 1.08, 16, 0.03, 7, grad=0.12), 432, 16)
# bras : face avant avec un filet ambré (_e) au milieu
bras = uni_tex(OR_B * 1.08, 16, 0.03, 8, grad=0.12)
bras[:, 6:10, :3] = (180, 110, 40)
be = np.zeros_like(bras)
be[:, 6:10] = (255, 170, 60, 255)
poser("bras_face", bras, 448, 16, e=be)
# lentille éteinte (ambre sombre, faible braise _e)
len_ = uni_tex((120, 66, 18), 16, 0.05, 9)
yy, xx = np.mgrid[0:16, 0:16]
d = np.hypot(xx - 7.5, yy - 7.5) / 8
len_[..., :3] = np.clip(len_[..., :3] * (1.3 - 0.6 * d)[..., None], 0, 255).astype(np.uint8)
le = rgba_e(np.dstack([90 * (1 - d), 45 * (1 - d), 10 * (1 - d)]).clip(0) * (d < 0.8)[..., None])
poser("lentille", len_, 464, 16, e=le)
CLEAR = [510, 30, 511, 31]                                            # texel transparent (x 496..512, y 16..32 libre)


# 4. eau : disque de base (trans_), reflets en vermicelles (trans_), rides (add_), écume du jaillissement (trans_)
def disque(N, SS=3):
    n = N * SS
    c = ((np.arange(n) + 0.5) / n * 2 - 1)
    x, y = np.meshgrid(c, -c)
    return x, y, np.hypot(x, y)


x, y, r = disque(128)
nb = bruit(384, 10, 11)
coul = (np.array((78, 150, 230))[None, None] * (1 - smooth(r / 0.98))[..., None]
        + np.array((26, 64, 140))[None, None] * smooth(r / 0.98)[..., None]) * (1 + 0.07 * nb)[..., None]
al = (165 + 70 * smooth((r - 0.2) / 0.75)) * (r < 0.985)
b = reduire(np.dstack([coul, al[..., None]]), (128, 128))
b_al = np.where(b[..., 3] > 110, np.clip(b[..., 3], 160, 240), 0)
eau = rgba(b[..., :3], b_al)
eau_e = rgba_e(reduire((np.array((24, 70, 140))[None, None] * (1.15 - 0.6 * r)[..., None]).clip(0) * (r < 0.985)[..., None], (128, 128)))
eau_e[b_al == 0] = 0
poser("eau", eau, 0, 320, e=eau_e)


def vermicelles(N, seed, niveaux, w):
    x, y, r = disque(N, 2)
    f = bruit(2 * N, 5, seed) + 0.35 * bruit(2 * N, 11, seed + 1)
    m = np.zeros_like(f)
    for lv in niveaux:
        m = np.maximum(m, 1 - smooth(np.abs(f - lv) / w))
    dens = (0.55 + 0.45 * (1 - smooth(r / 0.9))) * (r < 0.95)
    m *= dens
    m = reduire(m[..., None] * 255, (N, N))[..., 0] / 255
    a = np.where(m > 0.35, (120 + 120 * m).clip(0, 245), 0)
    rgb = np.array((150, 215, 255))[None, None] * (0.75 + 0.35 * m)[..., None]
    return rgba(rgb, a), rgba_e((np.array((110, 190, 240))[None, None] * m[..., None]) * (a > 0)[..., None])


va, vae = vermicelles(256, 21, (-0.8, 0.6), 0.16)
poser("reflets_a", va, 0, 64, e=vae)
vb, vbe = vermicelles(256, 37, (0.0,), 0.15)
poser("reflets_b", vb, 256, 64, e=vbe)

# ride : anneau à r = 0.92, profil gaussien ; cyan blanc qui sature de jour
x, y, r = disque(128)
p = np.exp(-((r - 0.9) / 0.045) ** 2) + 0.35 * np.exp(-((r - 0.8) / 0.03) ** 2)
ride = add_rgba(reduire(np.array((105, 170, 225))[None, None] * p[..., None], (128, 128)))
poser("ride", ride, 128, 320)
# éclat : disque blanc-cyan doux
p = np.exp(-(r / 0.45) ** 2) * (r < 1)
poser("flash", add_rgba(reduire(np.array((255, 255, 255))[None, None] * p[..., None] * 1.0
                                + np.array((0, 30, 60))[None, None] * 0, (64, 64))), 256, 320)
# lueur au sol : caustiques douces (add_), 64²
x, y, r = disque(64)
cs = bruit(192, 9, 51)
p = (0.8 + 0.2 * np.cos(cs * 1.2)) * np.exp(-(x / 0.75) ** 2 - ((y - 0.25) / 0.85) ** 2) * 1.2 * (1 - smooth((np.abs(x) - 0.55) / 0.45)) * (1 - smooth((np.abs(y) - 0.4) / 0.6))
poser("sol", add_rgba(reduire(np.array((55, 115, 190))[None, None] * p[..., None], (64, 64))), 320, 320)
# lueur des crans : losange ambré, cœur presque blanc
x, y, r = disque(32)
dl = (np.abs(x) + np.abs(y))
p = np.exp(-(dl / 0.42) ** 2) * 1.0 + 0.5 * np.exp(-(r / 0.8) ** 2)
cr = np.array((255, 160, 50))[None, None] * p[..., None] + np.array((0, 80, 120))[None, None] * (np.exp(-(dl / 0.2) ** 2))[..., None]
poser("cran_lueur", add_rgba(reduire(cr, (32, 32))), 384, 320)

# écume du jaillissement (384 × 64, azimut × longueur ; ≈ 3 texels/px) : corps bleu clair, crêtes blanches en traînées
EW, EH = 384, 64
n1 = bruit(EW * 2, 18, 61)[:EH * 2]
n2 = bruit(EW * 2, 40, 62)[:EH * 2]
v = np.linspace(0, 1, EH * 2)[:, None]
cre = smooth((0.75 * n1 + 0.45 * n2 - 0.35 + 0.5 * v) / 0.7)          # plus d'écume vers la tête
rgb = (np.array((112, 160, 228))[None, None] * (1 + 0.07 * n2)[..., None] * (1 - cre[..., None])
       + np.array((226, 240, 255))[None, None] * cre[..., None])
a = 205 + 40 * cre
ec = reduire(np.dstack([rgb, a]), (EW, EH))
poser("ecume", rgba(ec[..., :3], ec[..., 3].clip(200, 245)), 0, 448,
      e=rgba_e(reduire(np.array((40, 90, 160))[None, None] * (0.6 + 0.8 * cre)[..., None], (EW, EH))))

# profil de l'onde au sol (4 × 16, plein le long, gaussien en travers : rien à moyenner)
pv = np.exp(-((np.linspace(-1, 1, 16) / 0.45) ** 2))[:, None] * np.ones((1, 4))
poser("onde_profil", add_rgba(np.array((120, 195, 255))[None, None] * pv[..., None]), 256, 384)

# particules (8 × 8, opaques)
x, y, r = disque(8, 4)
gt = (np.array((200, 230, 255))[None, None] * (1.1 - 0.4 * r)[..., None])
gtm = reduire(np.dstack([gt, (r < 0.85) * 255.0]), (8, 8))
gt8 = rgba(gtm[..., :3], (gtm[..., 3] > 110) * 255)
poser("goutte", gt8, 448, 320, e=rgba_e(gtm[..., :3] * 0.5 * (gtm[..., 3:] > 110)))
st = np.maximum(np.exp(-(np.abs(x) / 0.12) ** 2) * (1 - np.abs(y)), np.exp(-(np.abs(y) / 0.12) ** 2) * (1 - np.abs(x)))
stm = reduire(np.dstack([np.array((190, 240, 255))[None, None] * np.ones_like(st)[..., None], (st > 0.3) * 255.0]), (8, 8))
st8 = rgba(stm[..., :3], (stm[..., 3] > 110) * 255)
poser("eclat", st8, 456, 320, e=rgba_e(stm[..., :3] * 0.8 * (stm[..., 3:] > 110)))

assert set(np.unique(tex[..., 3])) <= set(range(256))
tex_e[tex_e[..., 3] == 0, :3] = 0
assert not tex[30:32, 510:512, 3].any()


def b64(arr, chemin):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(chemin, optimize=True)
    bb = io.BytesIO()
    im_.save(bb, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(bb.getvalue()).decode()


tex_b64, tex_e_b64 = b64(tex, f"{NOM}.png"), b64(tex_e, f"{NOM}_e.png")


# ------------------------------------------------------------------ géométrie
def nuid():
    return str(_uuid.uuid4())


def rot180(a):
    return (a + 180.0) % 360.0 - 180.0


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
            d["rotation"] = [round(rot180(float(v)), 4) for v in self.rotation]
        return d


elements = []


def cube(g, nom, a, b, faces, origin=None, rotation=None):
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in a], "to": [round(float(v), 4) for v in b],
         "origin": [round(float(v), 4) for v in (origin if origin is not None else (np.add(a, b) / 2))], "box_uv": False,
         "faces": {k: {"uv": [round(float(v), 3) for v in uv], "texture": 0} for k, uv in faces.items()}}
    if rotation is not None and any(abs(v) > 1e-6 for v in rotation):
        e["rotation"] = [round(rot180(float(v)), 4) for v in rotation]
    for k in ("north", "south", "east", "west", "up", "down"):
        e["faces"].setdefault(k, {"uv": CLEAR, "texture": 0})
    elements.append(e)
    g.enfants.append(e["uuid"])


def flip(uv):
    return [uv[2], uv[1], uv[0], uv[3]]


def rot_matrix(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def euler(R):
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if abs(R[2, 0]) > 1 - 1e-9:
        rx, rz = 0.0, math.atan2(-R[0, 1], R[1, 1])
    else:
        rx = math.atan2(R[2, 1], R[2, 2])
        rz = math.atan2(R[1, 0], R[0, 0])
    e = tuple(math.degrees(v) for v in (rx, ry, rz))
    assert np.allclose(rot_matrix(*e), R, atol=1e-6)
    return e


def plaque_z(g, nom, centre, demi, uv, z, faces=("north", "south"), ep=0.2, rot=None):
    """Plaque verticale (plan XY) centrée en (centre.x, centre.y, z)."""
    cx, cy = centre[0], centre[1]
    cube(g, nom, (cx - demi, cy - demi, z - ep / 2), (cx + demi, cy + demi, z + ep / 2), {f: uv for f in faces},
         origin=(cx, cy, z), rotation=rot)


O = (0.0, 0.0, 0.0)
EFFET = G("effet", O)
JOUEUR = G("joueur", O)
PORTE = G("porte", O, EFFET)                 # demi-tour à l'arrivée (pivot à l'origine)
LEVE = G("leve", tuple(C), PORTE)            # sort du sol (position y)

# --- cadre de pierre : 72 segments, profondeurs alternées (faces avant jamais coplanaires)
CADRE = G("cadre", tuple(C), LEVE)
for k in range(NSEG):
    d = 0.14 if k % 2 else 0.0
    j, i = divmod(k, 36)
    uvf = [12 * i, 16 * j, 12 * i + 12, 16 * j + 16]
    cube(CADRE, f"p{k}", (-W_PI / 2, YC + R_MID, ZP - D_PIERRE / 2 - d), (W_PI / 2, YC + R_OUT, ZP + D_PIERRE / 2 + d),
         {"south": uvf, "north": flip(uvf), "up": UV["pierre_bord"], "down": UV["pierre_int"], "east": UV["pierre_cote"],
          "west": UV["pierre_cote"]}, origin=tuple(C), rotation=(0, 0, 360 * k / NSEG))

# --- anneau d'or (tourne autour de l'axe z)
TOURNE = G("tourne_or", tuple(C), LEVE)
for k in range(NSEG):
    d = 0.12 if k % 2 else 0.0
    j, i = divmod(k, 36)
    uvf = [12 * i, 32 + 16 * j, 12 * i + 12, 32 + 16 * j + 16]
    cube(TOURNE, f"o{k}", (-W_OR / 2, YC + R_IN, ZP - D_OR / 2 - d), (W_OR / 2, YC + R_MID - 0.1, ZP + D_OR / 2 + d),
         {"south": uvf, "north": flip(uvf), "down": UV["or_int"], "east": UV["or_cote"], "west": UV["or_cote"]},
         origin=tuple(C), rotation=(0, 0, 360 * k / NSEG))

# --- crans : bras d'or en V + lentille ; lueur add_ devant la lentille (des deux côtés). Chaque cran est dessiné en haut
# puis tourné de th autour de l'axe de la porte, rotation reportée sur ses cubes (pas de groupe tourné : le clac est une
# position radiale dans le repère de la porte).
def tourne_c(p, th):
    a = math.radians(th)
    dx, dy = p[0] - C[0], p[1] - C[1]
    return (C[0] + dx * math.cos(a) - dy * math.sin(a), C[1] + dx * math.sin(a) + dy * math.cos(a), p[2])


def cube_c(g, nom, a, b, faces, origin, rz, th):
    o2 = tourne_c(origin, th)
    d = np.subtract(o2, origin)
    cube(g, nom, np.add(a, d), np.add(b, d), faces, origin=o2, rotation=(0, 0, rz + th))


CRANS = []
for k in range(NCRAN):
    th = 360 * k / NCRAN
    top = (0.0, YC + 29.2, ZP)
    pt = tourne_c(top, th)
    gk = G(f"cran{k + 1}", pt, LEVE)
    bras_g = G(f"bras{k + 1}", pt, gk)                   # clac : position radiale
    for s_, nm in ((1, "d"), (-1, "g")):
        cx = 1.25 * s_
        cube_c(bras_g, f"bras{k + 1}{nm}", (cx - 0.65, YC + 27.0, ZP - 3.6), (cx + 0.65, YC + 32.4, ZP + 3.6),
               {"south": UV["bras_face"], "north": UV["bras_face"], "up": UV["or_bras"], "down": UV["or_bras"],
                "east": UV["or_bras"], "west": UV["or_bras"]}, (cx, YC + 27.0, ZP), 24 * s_, th)
    cube_c(bras_g, f"lentille{k + 1}", (-1.0, YC + 28.2, ZP - 3.75), (1.0, YC + 30.2, ZP + 3.75),
           {f: UV["lentille"] for f in ("north", "south", "east", "west", "up", "down")}, (0, YC + 29.2, ZP), 45, th)
    lu = G(f"add_cran{k + 1}", pt, bras_g)
    a_lu = G("ctrl_alpha", pt, lu)
    plaque_z(lu, f"lueur{k + 1}a", pt, 3.0, UV["cran_lueur"], ZP + 4.05, faces=("south",), ep=0.1, rot=(0, 0, th))
    plaque_z(lu, f"lueur{k + 1}b", pt, 3.0, UV["cran_lueur"], ZP - 4.05, faces=("north",), ep=0.1, rot=(0, 0, th))
    CRANS.append(dict(g=gk, bras=bras_g, lu=lu, a=a_lu, th=th))

# --- eau : base trans_, reflets trans_ (deux couches par côté), rides add_ devant chaque côté
EAU = G("eau", tuple(C), LEVE)               # ouverture : échelle (0 -> 1), coupure nette
TR_EAU = G("trans_eau", tuple(C), EAU)
plaque_z(TR_EAU, "eau", C, R_EAU, UV["eau"], ZP, ep=0.3)
REFLETS = []
for cote, s_ in (("av", 1), ("ar", -1)):
    for n_, (nom, dz) in enumerate((("reflets_a", 0.55), ("reflets_b", 1.05))):
        rg = G(f"tourne_{nom}_{cote}", tuple(C), EAU)
        tg = G(f"trans_{nom}_{cote}", tuple(C), rg)
        plaque_z(tg, f"{nom}_{cote}", C, R_EAU * (0.98 - 0.03 * n_), UV[nom], ZP + s_ * dz,
                 faces=("south",) if s_ > 0 else ("north",), ep=0.1)
        REFLETS.append((rg, s_, n_))
NRIDE = 4
RIDES = []                                   # (groupe, ctrl_alpha, côté)
for cote, s_ in (("av", 1), ("ar", -1)):
    for i in range(NRIDE):
        rg = G(f"ride_{cote}{i + 1}", tuple(C), EAU)
        ag = G(f"add_ride_{cote}{i + 1}", tuple(C), rg)
        ca = G("ctrl_alpha", tuple(C), ag)
        plaque_z(ag, f"ride_{cote}{i + 1}", C, R_EAU * 0.98, UV["ride"], ZP + s_ * (1.6 + 0.12 * i),
                 faces=("south",) if s_ > 0 else ("north",), ep=0.1)
        RIDES.append((rg, ca, s_))
# rides au point d'entrée (côté avant, +Z), centrées à hauteur de poitrine
P_ENT = np.array((0.0, 17.0, ZP))
ENTREE = []
for cote, s_ in (("av", 1), ("ar", -1)):
    for i in range(3):
        rg = G(f"ride_entree_{cote}{i + 1}", tuple(P_ENT), EAU)
        ag = G(f"add_ride_entree_{cote}{i + 1}", tuple(P_ENT), rg)
        ca = G("ctrl_alpha", tuple(P_ENT), ag)
        plaque_z(ag, f"ride_entree_{cote}{i + 1}", P_ENT, 14.0, UV["ride"], ZP + s_ * (2.3 + 0.1 * i),
                 faces=("south",) if s_ > 0 else ("north",), ep=0.1)
        ENTREE.append((rg, ca))
# éclat d'ouverture (devant les deux faces) et lueur au sol devant la porte
FLASH = G("flash", tuple(C), LEVE)
AD_FL = G("add_flash", tuple(C), FLASH)
plaque_z(AD_FL, "flash_av", C, 26.0, UV["flash"], ZP + 2.6, faces=("south",), ep=0.1)
plaque_z(AD_FL, "flash_ar", C, 26.0, UV["flash"], ZP - 2.6, faces=("north",), ep=0.1)
SOL = G("sol", (0, 0, ZP), PORTE)
AD_SOL = G("add_sol", (0, 0, ZP), SOL)
A_SOL = G("ctrl_alpha", (0, 0, ZP), AD_SOL)
cube(AD_SOL, "sol", (-28, 0.3, ZP + 2), (28, 0.4, ZP + 62), {"up": UV["sol"]})
# onde au sol : un anneau de lumière qui part du pied de la porte et balaie le sol à l'ouverture (vu en 1re personne)
OSOL = G("onde_sol", (0, 0.5, ZP), PORTE)
AD_OS = G("add_onde_sol", (0, 0.5, ZP), OSOL)
A_OS = G("ctrl_alpha", (0, 0.5, ZP), AD_OS)
R_OS, W_OS, N_OS = 90.0, 7.0, 72
L_OS = 2 * R_OS * math.tan(math.pi / N_OS) + 0.04
for k in range(N_OS):
    y0 = 0.5 + 0.12 * (k % 2)
    cube(AD_OS, f"onde_sol{k}", (-L_OS / 2, y0, ZP - R_OS - W_OS / 2), (L_OS / 2, y0 + 0.1, ZP - R_OS + W_OS / 2),
         {"up": UV["onde_profil"]}, origin=(0, 0.5, ZP), rotation=(0, 360 * k / N_OS, 0))

# --- jaillissement : bulbe de révolution autour de l'axe z (vers +Z), facettes
JAIL = G("jaillit", tuple(C), LEVE)
VIB = G("vibre", tuple(C), JAIL)
TR_J = G("trans_jaillit", tuple(C), VIB)
LJ, NA_, NL_ = 27.0, 36, 14
rj = np.random.default_rng(5)


def r_bulbe(u):
    corps = 19.0 * (0.86 + 0.24 * math.sin(math.pi * min(u, 0.8) / 0.8 * 0.6))
    tete = math.sqrt(max(0.0, 1 - max(0.0, (u - 0.62) / 0.38) ** 2))
    return corps * max(tete, 0.0)


bosses = 1 + 0.035 * rj.standard_normal((NL_ + 1, NA_ + 1))
bosses[:, -1] = bosses[:, 0]
PTS = []
for j in range(NL_ + 1):
    u = 0.94 * j / NL_
    rr = r_bulbe(u)
    PTS.append([np.array((rr * bosses[j, k] * math.cos(TAU * k / NA_), YC + rr * bosses[j, k] * math.sin(TAU * k / NA_),
                          ZP + 0.4 + LJ * u)) for k in range(NA_ + 1)])
ue0, ve0 = UV["ecume"][0], UV["ecume"][1]
for j in range(NL_):
    for k in range(NA_):
        a, b_, c_, d_ = PTS[j][k], PTS[j][k + 1], PTS[j + 1][k], PTS[j + 1][k + 1]
        ex = (b_ - a) + (d_ - c_)
        if np.linalg.norm(ex) < 1e-3:
            continue
        ey = (a + b_) / 2 - (c_ + d_) / 2
        h = float(np.linalg.norm(ey))
        if h < 1e-3:
            continue
        ex /= np.linalg.norm(ex)
        ey = ey - (ey @ ex) * ex
        ey /= np.linalg.norm(ey)
        ez = np.cross(ex, ey)
        m = (a + b_ + c_ + d_) / 4
        axe = np.array((0, YC, m[2]))
        uvf = [ue0 + EW * k / NA_, ve0 + EH * j / NL_, ue0 + EW * (k + 1) / NA_, ve0 + EH * (j + 1) / NL_]
        if ez @ (m - axe) < 0:
            ex, ez = -ex, -ez
            uvf = flip(uvf)
        w = max(np.linalg.norm(b_ - a), np.linalg.norm(d_ - c_)) * 1.02 + 0.05
        m = m + ez * (0.1 * (k % 2))
        cube(TR_J, f"j{j}.{k}", m + (-w / 2, -h / 2, -0.3), m + (w / 2, h / 2, 0), {"south": uvf}, origin=m,
             rotation=euler(np.column_stack((ex, ey, ez))))
# bout du bulbe : calotte ronde (disque d'eau découpé par alpha), un peu en retrait du dernier anneau
R_CAL = r_bulbe(0.94) * 1.04
plaque_z(TR_J, "calotte", C, R_CAL, UV["eau"], ZP + 0.4 + LJ * 0.94 - 0.15, faces=("south",), ep=0.2)

# --- particules : points d'émission (+Y du groupe = direction), chacun avec son ctrl_emit
EMIT = {}


def emit(sorte, pos, parent, rotation=None, nom=None):
    lst = EMIT.setdefault(sorte, [])
    n = nom or ("emit_" + sorte + (str(len(lst) + 1) if lst else ""))
    g = G(n, pos, parent, rotation=rotation)
    c = G("ctrl_emit", pos, g)
    lst.append((g, c))
    return g


TETE = G("tete_jaillit", (0, YC, ZP + LJ), JAIL)
for i, (dx, dy) in enumerate(((0, 6), (6, -3), (-6, -3), (0, -8))):
    emit("goutte", (dx, YC + dy, ZP + LJ * 0.7), TETE, rotation=(90 + 25 * (dy / 8), 0, -25 * dx / 6))
for i in range(4):
    a = TAU * (i + 0.5) / 4
    emit("goutte", (21 * math.cos(a), YC + 21 * math.sin(a), ZP + 3.0), EAU, rotation=(70, 0, 0))
for cote, s_ in (("av", 1), ("ar", -1)):
    for i in range(4):
        a = TAU * (i + 0.25) / 4
        emit("eclat", (13 * math.cos(a), YC + 13 * math.sin(a), ZP + s_ * 3.0), EAU, rotation=(90 * s_, 0, 0))
for x_ in (-8, 8):
    emit("mc_splash", (x_, 4.0, ZP + 4.0), EAU, rotation=(60, 0, 0), nom="emit_mc_splash")
for cote, s_ in (("av", 1), ("ar", -1)):
    for x_ in (-10, 10):
        emit("mc_glow", (x_, YC + 4, ZP + s_ * 3.5), EAU, rotation=(90 * s_, 0, 0), nom="emit_mc_glow")
for x_ in (-22, 22):
    for s_ in (1, -1):
        emit("mc_poof", (x_, 0.6, ZP + s_ * 4.5), PORTE, nom="emit_mc_poof")
NEMIT = sum(len(v) for v in EMIT.values())
assert NEMIT <= 32, NEMIT

PART = {}
PART["goutte"] = G("particle_goutte", O)
cube(PART["goutte"], "p_goutte", (-0.35, 0.4, -0.15), (0.35, 1.1, 0.15), {"south": UV["goutte"], "north": UV["goutte"]})
PART["eclat"] = G("particle_eclat", O)
cube(PART["eclat"], "p_eclat", (-0.5, 0.4, -0.15), (0.5, 1.4, 0.15), {"south": UV["eclat"], "north": UV["eclat"]})
outliner = [EFFET.json(), JOUEUR.json(), PART["goutte"].json(), PART["eclat"].json()]


# ------------------------------------------------------------------ animations
def s(v):
    return v if isinstance(v, str) else str(round(float(v) + 0.0, 4))


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": s(x), "y": s(y), "z": s(z)}], "time": round(t, 4), "interpolation": "linear"}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def lin(t, a, b):
    return min(max((t - a) / (b - a), 0.0), 1.0)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def temps(L, fps=FPS):
    n = max(2, int(round(L * fps)))
    return [round(L * i / n, 4) for i in range(n + 1)]


class Anim:
    def __init__(self, nom, L, loop):
        self.nom, self.L, self.loop, self.A, self.sons = nom, L, loop, {}, []
        self.T = temps(L)

    def piste(self, g, ch, f, T=None):
        T = self.T if T is None else T
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += [kf(ch, t, *f(t)) for t in T]

    def fixe(self, g, ch, v):
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"].append(kf(ch, 0, *v))

    def alpha(self, c, f):
        self.piste(c, "position", lambda t: (max(0.0, min(1.0, f(t))) - 1.0, 0, 0))

    def son(self, t, nom):
        self.sons.append({"channel": "sound", "data_points": [{"effect": nom, "file": ""}], "time": round(t, 3)})
        self.A["effects"] = {"name": "Effects", "type": "effect", "keyframes": self.sons}

    def cadence(self, sorte, f):
        for i, (g, c) in enumerate(EMIT[sorte]):
            self.piste(c, "position", lambda t, i=i: (max(-1.0, min(7.0, f(t, i))), 0, 0))

    def json(self):
        return {"uuid": nuid(), "name": self.nom, "loop": self.loop, "override": False, "length": self.L, "snapping": 30,
                "selected": self.nom == "depart", "animators": self.A}


uni = lambda v: (v, v, v)
Z3, UN = (0, 0, 0), (1, 1, 1)


def net(v, seuil=0.02):
    return v if v > seuil else 0.0


# ---- composition : l'anneau d'or tourne par à-coups, chaque arrêt verrouille un cran
def rotation_or(t, coups):
    """coups : [(t0, t1, angle)] ; angle cumulé, départ et arrêt adoucis (vrais arrêts de la mécanique)."""
    a = 0.0
    for t0, t1, da in coups:
        u = lin(t, t0, t1)
        a += da * (u * u * u * (u * (6 * u - 15) + 10))          # smootherstep : démarre et s'arrête en douceur
    return a


def clac(t, tl, fort=1.0):
    """Enfoncement des bras (px, vers le centre) : coup sec puis retour amorti."""
    if t < tl:
        return 0.0
    u = t - tl
    return -0.9 * fort * math.exp(-u / 0.07) * (1 if u < 0.04 else math.cos(TAU * 3.5 * (u - 0.04)))


def lueur_cran(t, tl, fort=1.0):
    """Allumage d'un cran (échelle de la lueur) : éclat au verrouillage puis lumière tenue."""
    if t < tl:
        return 0.0
    return 1.0 + 0.6 * fort * math.exp(-(t - tl) / 0.12)


def anim_crans(an, locks, fin=None, deja=(), fort_k=None):
    """locks : {indice cran : instant}. deja : crans allumés dès t = 0. fin : instant où tout s'éteint (coupure)."""
    for k, cr in enumerate(CRANS):
        tl = locks.get(k)
        fk = 1.8 if fort_k == k else 1.0
        dirx, diry = -math.sin(math.radians(cr["th"])), math.cos(math.radians(cr["th"]))
        an.piste(cr["bras"], "position", lambda t, tl=tl, fk=fk, dirx=dirx, diry=diry:
                 (lambda c: (dirx * c, diry * c, 0))(clac(t, tl, fk) if tl is not None else 0.0))
        def sc(t, tl=tl, k=k, fk=fk):
            v = 1.0 if k in deja else (lueur_cran(t, tl, fk) if tl is not None else 0.0)
            if fin is not None:
                v *= 1 - sm(t, fin, fin + 0.25)
            return uni(net(v, 0.03))
        an.piste(cr["lu"], "scale", sc)
        an.alpha(cr["a"], lambda t, tl=tl, k=k: (1.0 if (k in deja or (tl is not None and t >= tl)) else 0.0)
                 * (0.85 + 0.15 * math.sin(TAU * 0.8 * t + k)) * (1 - (sm(t, fin, fin + 0.25) if fin is not None else 0)))


def surface_vivante(an, ouvre, coupe, L):
    """Reflets qui tournent, rides concentriques (4 par côté, période 2,4 s), tant que la surface est ouverte."""
    for rg, s_, n_ in REFLETS:
        v = (14 if n_ == 0 else -9) * s_
        an.piste(rg, "rotation", lambda t, v=v: (0, 0, v * t))
        an.piste(rg, "scale", lambda t, n_=n_: uni(1 + 0.025 * math.sin(TAU * (0.45 + 0.2 * n_) * t)))
    P = 2.4
    for idx, (rg, ca, s_) in enumerate(RIDES):
        i = idx % NRIDE
        ph = i / NRIDE + (0.125 if s_ < 0 else 0)
        def ph_(t, ph=ph):
            return ((t - ouvre) / P + ph) % 1.0
        an.piste(rg, "scale", lambda t, ph_=ph_: uni(net((0.12 + 0.88 * ph_(t) ** 0.8) * (1 if ouvre <= t < coupe else 0), 0.05)))
        an.alpha(ca, lambda t, ph_=ph_: sm(ph_(t), 0.0, 0.15) * (1 - sm(ph_(t), 0.6, 1.0)) * sm(t, ouvre, ouvre + 0.4))


def jaillissement(an, t0, longueur, duree):
    """Bulbe : sort d'un élan (45 %), tient, se rétracte dans le plan ; vibration de la surface du bulbe."""
    tp, tr = t0 + 0.45 * duree, t0 + 0.6 * duree
    def sc(t):
        if t < t0 or t > t0 + duree:
            return Z3
        if t < tp:
            u = lin(t, t0, tp)
            z = longueur * (1 - (1 - u) ** 2.4) * (1 + 0.06 * math.sin(math.pi * u))
            xy = 0.62 + 0.38 * (1 - (1 - u) ** 2)
        elif t < tr:
            z, xy = longueur * (1 + 0.04 * math.sin(math.pi * lin(t, tp, tr))), 1.0
        else:
            u = sm(t, tr, t0 + duree)
            z, xy = longueur * (1 - u), 1.0 - 0.2 * u
        return (xy, xy, max(z, 0.02)) if z > 0.02 else Z3
    an.piste(JAIL, "scale", sc)
    an.piste(VIB, "scale", lambda t: (1 + 0.035 * math.sin(TAU * 4 * t), 1 + 0.035 * math.sin(TAU * 4 * t + 1.7), 1 + 0.03 * math.sin(TAU * 3 * t)))
    an.piste(VIB, "rotation", lambda t: (0, 0, 15 * (t - t0)))


def entree(an, t0):
    """Rides au point d'entrée (ou de sortie) : trois anneaux qui s'étalent en 1 s."""
    for i, (rg, ca) in enumerate(ENTREE):
        a = t0 + 0.12 * (i % 3)
        an.piste(rg, "scale", lambda t, a=a: uni(net(0.1 + 0.9 * (1 - (1 - lin(t, a, a + 1.0)) ** 2), 0.05) if a <= t < a + 1.0 else 0.0))
        an.alpha(ca, lambda t, a=a: (1 - sm(t, a + 0.3, a + 1.0)) if t >= a else 0.0)


def levee(t, t0, t1):
    """Montée hors du sol : vitesse continue, arrêt adouci, grondement (tremblement 6 Hz qui s'éteint)."""
    u = lin(t, t0, t1)
    y = Y_SOUS * (1 - (1 - (1 - u) ** 3) if u < 1 else 1) if False else Y_SOUS * (1 - u) ** 2.2 * (1 if u < 1 else 0)
    tremble = 0.3 * math.sin(TAU * 6 * t) * bump(t, t0, t0 + 0.1, t1 - 0.1, t1 + 0.2)
    return y + tremble


def descente(t, t0, t1):
    u = lin(t, t0, t1)
    return Y_SOUS * u ** 2.0 + 0.3 * math.sin(TAU * 6 * t) * bump(t, t0, t0 + 0.08, t1 - 0.1, t1)


def tremble_x(t, a, b):
    return 0.25 * math.sin(TAU * 7 * t + 1) * bump(t, a, a + 0.1, b - 0.1, b)


# ---- charge (loop 20 s) : compte à rebours du serveur = 3 s (retour en jeu du 2026-11-07). La porte sort du sol en
# 0,5 s, l'anneau tourne par à-coups et 8 crans se verrouillent un par un (le dernier à 2,8 s) ; ensuite la porte reste
# levée, crans allumés qui pulsent (compte à rebours plus long, lag) ; à la fin de la boucle (19–20 s, jamais vue avec
# 3 s) les crans s'éteignent et la porte redescend, pour que la boucle se referme sur la porte enfouie.
LC = 20.0
ORDRE = [1, 8, 2, 7, 3, 6, 4, 5, 0]                  # le dernier (0, en haut) se verrouille au départ
C_LOCKS = [0.78 + i * (2.8 - 0.78) / 7 for i in range(8)]   # mêmes instants que sons/porte_gronde.py
C_DA = (70, -55, 85, -60, 50, -80, 65, -75)           # somme nulle : l'anneau revient à 0 (départ et boucle)
C_COUPS = [(tl - 0.25, tl - 0.03, da) for tl, da in zip(C_LOCKS, C_DA)]
C_LOCK = {ORDRE[i]: C_LOCKS[i] for i in range(8)}
C_FIN = 19.0
ch = Anim("charge", LC, "loop")
ch.T = sorted(set(temps(3.6) + [round(3.6 + i * 0.1, 4) for i in range(int((C_FIN - 0.4 - 3.6) / 0.1) + 1)]
                  + [round(C_FIN - 0.4 + i / FPS, 4) for i in range(int((LC - C_FIN + 0.4) * FPS) + 1)] + [LC]))
ch.fixe(EFFET, "scale", UN)
ch.piste(LEVE, "position", lambda t: (tremble_x(t, 0, 0.6) + tremble_x(t, C_FIN + 0.2, LC),
                                      levee(t, 0.0, 0.5) if t < C_FIN + 0.2 else descente(t, C_FIN + 0.2, LC), 0))
ch.piste(TOURNE, "rotation", lambda t: (0, 0, rotation_or(t, C_COUPS)))
anim_crans(ch, C_LOCK, fin=C_FIN)
ch.fixe(EAU, "scale", Z3)
ch.fixe(JAIL, "scale", Z3)
ch.fixe(FLASH, "scale", Z3)
ch.fixe(SOL, "scale", Z3)
ch.fixe(OSOL, "scale", Z3)
ch.alpha(A_SOL, lambda t: 0)
for rg, ca in ENTREE:
    ch.fixe(rg, "scale", Z3)
ch.cadence("mc_poof", lambda t, i: -1 + 5 * bump(t, 0.0, 0.05, 0.4, 0.6) + 5 * bump(t, C_FIN + 0.2, C_FIN + 0.3, LC - 0.2, LC))
for sorte in ("goutte", "eclat", "mc_splash", "mc_glow"):
    ch.cadence(sorte, lambda t, i: -1)
ch.son(0.0, "porte_gronde")                           # pierre qui sort + grondement de rotation (exception demandée)
for i, tl in enumerate(C_LOCKS):                      # un « ka-chunk » par cran, trois hauteurs en alternance
    ch.son(tl - 0.005, ("porte_cran", "porte_cran_b", "porte_cran_c")[i % 3])

# ---- depart (once 3,6 s) : commence là où la charge s'arrête (porte levée, 8 crans allumés, anneau à 0) : dernier cran
# en haut, éclat et jaillissement tout de suite. Sans charge (/tp), la porte est déjà levée à t = 0.
LD = 3.6
D_COUPS = [(0.0, 0.2, 90)]
D_LOCK = {0: 0.23}
T_FL = 0.27                       # éclat d'ouverture
T_J, D_J = 0.33, 1.0              # jaillissement
T_OUV = 0.33                      # la surface s'étale sous l'éclat
T_W0, T_W1 = 1.06, 2.16           # la copie marche jusqu'à la porte
T_CACHE = None                    # calculé : l'avant de la tête a passé le plan de 1,5 px
T_CUT = 2.66                      # coupure nette
T_D0, T_D1 = 2.76, 3.56           # la porte redescend
de = Anim("depart", LD, "once")
de.piste(EFFET, "scale", lambda t: uni(1.0 if t < LD - 0.04 else 0.0), T=[0, round(LD - 0.05, 4), LD])
de.fixe(PORTE, "rotation", Z3)
de.piste(LEVE, "position", lambda t: (tremble_x(t, T_D0, T_D1), descente(t, T_D0, T_D1) if t >= T_D0 else 0.0, 0))
de.piste(TOURNE, "rotation", lambda t: (0, 0, rotation_or(t, D_COUPS)))
anim_crans(de, D_LOCK, fin=T_CUT, deja=tuple(ORDRE[:8]), fort_k=0)
de.piste(EAU, "scale", lambda t: uni(net(sm(t, T_OUV - 0.02, T_OUV + 0.22) * (1.0 + 0.04 * bump(t, T_OUV + 0.2, T_OUV + 0.3, T_OUV + 0.4, T_OUV + 0.7))
                                       * (1 if t < T_CUT else 0), 0.03)))
surface_vivante(de, T_OUV, T_CUT, LD)
jaillissement(de, T_J, 1.0, D_J)
de.fixe(JAIL, "rotation", (0, 180, 0))
de.piste(FLASH, "scale", lambda t: uni(net(1.1 * bump(t, T_FL - 0.04, T_FL + 0.04, T_FL + 0.1, T_FL + 0.4) + 0.7 * bump(t, T_CUT - 0.01, T_CUT, T_CUT + 0.03, T_CUT + 0.2), 0.05)))
de.piste(SOL, "scale", lambda t: (1, 1, net(sm(t, T_OUV, T_OUV + 0.5) * (1 if t < T_CUT else 0), 0.05)))
de.alpha(A_SOL, lambda t: (0.75 + 0.25 * math.sin(TAU * 1.3 * t)) * sm(t, T_OUV, T_OUV + 0.5))


def onde_sol(an, t0):
    an.piste(OSOL, "scale", lambda t: (lambda k: (k, 1, k))(net(0.04 + 0.96 * (1 - (1 - lin(t, t0, t0 + 1.4)) ** 1.5), 0.02) if t0 <= t < t0 + 1.4 else 0.0))
    an.alpha(A_OS, lambda t: (1 - sm(t, t0 + 0.6, t0 + 1.4)) if t >= t0 else 0.0)


onde_sol(de, T_OUV)


def copie_z(t):
    """Marche : départ du repos, s'avance d'un seul élan dans le plan (pas d'arrêt avant)."""
    u = lin(t, T_W0, T_W1)
    return (ZP - 6.0) * (u * u * (1.6 - 0.6 * u))           # accélère puis garde sa vitesse


T_CACHE = next(t / 1000 for t in range(int(T_W0 * 1000), int(T_W1 * 1000)) if copie_z(t / 1000) - 4.0 < ZP - 1.5)
print("copie coupée à", T_CACHE, "s")
entree(de, T_CACHE - 0.12)
de.piste(JOUEUR, "position", lambda t: (0, 1.0 * sm(copie_z(t), -24, -30) if False else 1.0 * lin(-copie_z(t), 24, 30), copie_z(t)))
de.piste(JOUEUR, "scale", lambda t: uni(1.0 if t < T_CACHE else 0.0), T=[0, round(T_CACHE - 0.01, 4), round(T_CACHE, 4), LD])
de.cadence("goutte", lambda t, i: (-1 + 8 * bump(t, T_J + 0.1, T_J + 0.2, T_J + 0.55, T_J + 0.8)) if i < 4 else
           (-1 + 6 * bump(t, T_J, T_J + 0.1, T_J + 0.5, T_J + 0.9) + 4 * bump(t, T_CACHE - 0.2, T_CACHE - 0.1, T_CACHE + 0.2, T_CACHE + 0.4)))
de.cadence("eclat", lambda t, i: -1 + 2.5 * bump(t, T_OUV + 0.3, T_OUV + 0.6, T_CUT - 0.1, T_CUT) + 5 * bump(t, T_CUT - 0.02, T_CUT, T_CUT + 0.05, T_CUT + 0.2))
de.cadence("mc_splash", lambda t, i: -1 + 7 * bump(t, T_J, T_J + 0.1, T_J + 0.6, T_J + 0.9) + 6 * bump(t, T_CACHE - 0.3, T_CACHE - 0.2, T_CACHE, T_CACHE + 0.2))
de.cadence("mc_glow", lambda t, i: -1 + 2 * bump(t, T_OUV + 0.4, T_OUV + 0.7, T_CUT - 0.1, T_CUT))
de.cadence("mc_poof", lambda t, i: -1 + 5 * bump(t, T_D0, T_D0 + 0.1, T_D1 - 0.2, T_D1))
de.son(D_LOCK[0] - 0.005, "porte_cran_fin")     # dernier cran, en haut : plus lourd
de.son(T_FL - 0.06, "porte_jaillit")
de.son(T_CUT - 0.28, "porte_coupe")       # aspiration 0,26 s, « thup » sur la coupure

# ---- arrivee (once 4,4 s) : porte levée derrière le joueur, 9 crans allumés, il en sort
LA = 4.4
A_FL, A_J, A_DJ = 0.0, 0.03, 0.62
A_OUV = 0.02
A_W0, A_W1 = 0.55, 1.65
A_CUT = 3.0
A_D0, A_D1 = 3.12, 4.1
Z_SORT = -ZP + 5.0                 # départ derrière le plan (repère du monde : la porte est à z = +32)
A_VIS = 0.62
ar = Anim("arrivee", LA, "once")
ar.piste(EFFET, "scale", lambda t: uni(1.0 if t < LA - 0.04 else 0.0), T=[0, round(LA - 0.05, 4), LA])
ar.fixe(PORTE, "rotation", (0, 180, 0))
ar.piste(LEVE, "position", lambda t: (tremble_x(t, A_D0, A_D1), descente(t, A_D0, A_D1) if t >= A_D0 else 0.0, 0))
ar.piste(TOURNE, "rotation", lambda t: (0, 0, -25 * (1 - math.exp(-3 * t))))
anim_crans(ar, {k: -1.0 for k in range(NCRAN)}, fin=A_CUT, deja=tuple(range(NCRAN)))
ar.piste(EAU, "scale", lambda t: uni(net(sm(t, A_OUV, A_OUV + 0.22) * (1 if t < A_CUT else 0), 0.03)))
surface_vivante(ar, A_OUV, A_CUT, LA)
jaillissement(ar, A_J, 0.7, A_DJ)
ar.fixe(JAIL, "rotation", Z3)
entree(ar, A_VIS - 0.05)
ar.piste(FLASH, "scale", lambda t: uni(net(1.1 * bump(t, -0.1, 0.0, 0.05, 0.35) + 0.7 * bump(t, A_CUT - 0.01, A_CUT, A_CUT + 0.03, A_CUT + 0.2), 0.05)))
ar.piste(SOL, "scale", lambda t: (1, 1, net(sm(t, 0.0, 0.4) * (1 if t < A_CUT else 0), 0.05)))
ar.alpha(A_SOL, lambda t: (0.75 + 0.25 * math.sin(TAU * 1.3 * t)) * sm(t, 0.0, 0.4))


onde_sol(ar, 0.02)


def sortie_z(t):
    u = lin(t, A_W0, A_W1)
    return Z_SORT * (1 - u * u * (3 - 2 * u))              # sort du plan et s'arrête en douceur à sa place


ar.piste(JOUEUR, "position", lambda t: (0, 1.0 * (1 - lin(sortie_z(t), 0, 8)) * 0 + 1.0 * lin(sortie_z(t), 24, 30), sortie_z(t)))
ar.piste(JOUEUR, "scale", lambda t: uni(0.0 if t < A_VIS else 1.0), T=[0, round(A_VIS - 0.01, 4), round(A_VIS, 4), LA])
ar.cadence("goutte", lambda t, i: (-1 + 7 * bump(t, A_J + 0.05, A_J + 0.15, A_J + 0.35, A_J + 0.55)) if i < 4 else
           (-1 + 5 * bump(t, 0.0, 0.1, 0.4, 0.7) + 5 * bump(t, A_VIS - 0.1, A_VIS, A_VIS + 0.3, A_VIS + 0.6)))
ar.cadence("eclat", lambda t, i: -1 + 2.5 * bump(t, 0.3, 0.6, A_CUT - 0.1, A_CUT) + 5 * bump(t, A_CUT - 0.02, A_CUT, A_CUT + 0.05, A_CUT + 0.2))
ar.cadence("mc_splash", lambda t, i: -1 + 7 * bump(t, 0.0, 0.08, 0.4, 0.7) + 6 * bump(t, A_VIS - 0.1, A_VIS, A_VIS + 0.2, A_VIS + 0.4))
ar.cadence("mc_glow", lambda t, i: -1 + 2 * bump(t, 0.3, 0.6, A_CUT - 0.1, A_CUT))
ar.cadence("mc_poof", lambda t, i: -1 + 5 * bump(t, A_D0, A_D0 + 0.1, A_D1 - 0.2, A_D1))
ar.son(0.0, "porte_jaillit")
ar.son(A_CUT - 0.28, "porte_coupe")


# ---- particules
def part_anim(sorte, L, ch_, f, n=12):
    a = Anim(f"particle_{sorte}_fall", L, "loop")
    a.piste(PART[sorte], ch_, f, T=[round(i * L / n, 4) for i in range(n + 1)])
    return a


pg = part_anim("goutte", 0.6, "scale", lambda t: (1 - 0.2 * math.sin(TAU * t / 0.6), 1 + 0.25 * math.sin(TAU * t / 0.6), 1), n=8)
pc = part_anim("eclat", 1.0, "rotation", lambda t: (0, 360 * t / 1.0, 0), n=12)

ANIMS = [ch.json(), de.json(), ar.json(), pg.json(), pc.json()]
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures,
         "animations": ANIMS}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
embarquer_sons(model, {n: f"sons/{n}.ogg" for n in ("porte_cran", "porte_cran_b", "porte_cran_c", "porte_cran_fin",
                                                    "porte_gronde", "porte_jaillit", "porte_coupe")})
limiter_sons(model, max_effet=3, max_charge=9)       # charge : grondement + 8 clacs (exception demandée, 2026-11-07)

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
