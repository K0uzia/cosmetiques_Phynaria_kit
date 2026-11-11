"""Aura d'orage v2 « feu de Saint-Elme » : la charge d'un orage qui s'allume sur le joueur. Design original (ensemble Orage,
thème Éléments, fiche .claude/styles/orage.md). Écrit aura_orage.png et .build/aura_orage_brut.bbmodel (pas de calque _e :
l'additif ne se double pas, leçon aura_berenice). Ancienne version : .build/gen_avant.py, .build/avant_livrable.bbmodel.

Retour de l'utilisateur (2026-11-08) : « revoir les aura sauf la bérénice qui es bien les autre nul » ; « la foudre revoir tout ».
La v1 se lisait à peine en jeu : halo bleu très faible, décharges de 2,5 x 4,4 px tirées au hasard (presque jamais visibles),
nuage gris trans_ qui faisait fumée (et qui, en trans_, cachait l'additif derrière lui).

Ce qui rend aura_berenice réussie (« bien ») et qu'on reprend : une grande forme lumineuse fine et nette derrière la tête
(la gloire de rayons), lisible de jour comme de nuit, posée sur un halo discret ; des colonnes calmes qui montent ; un anneau
au sol net ; un seul point focal clair, tout le reste doux ; cumul additif ≤ 255.

Analogie (phénomène réel, .claude/references/effets/auras.md, « Feu de Saint-Elme ») : dans un champ d'orage, le champ se
concentre sur les pointes (mâts, cornes, bouts d'ailes) et y allume une décharge couronne continue, bleu-violet, en
« pinceaux » de filaments qui grésillent ; de vrais éclairs ne partent qu'au hasard. Traduction : une lumière continue qui
grésille (couronne et halo) + des décharges brèves et nettes aux pointes du corps.

Design
- Couronne de Saint-Elme (point focal, l'équivalent électrique de la gloire) : plaque add_ de 32 px dans un groupe cam_
  derrière la nuque (recul 7 px) : 11 pinceaux de foudre en zigzag (angles vifs de 20 à 40°, fourches fines au quart de
  l'épaisseur), longs au-dessus de la tête, courts au-dessus des épaules, cœur blanc bleuté, halo bleu, bord violet. Film de
  4 images (ctrl_uv) tirées au hasard 7 fois par seconde : la couronne grésille sur place sans tourner (une couronne reste
  accrochée à ses pointes). Doublée par une version trans_ discrète (alpha 22 à 70), plus loin derrière (jamais devant
  l'additif), pour les shaders.
- Halo de silhouette : 13 disques add_ creux en cam_ reculés derrière tête, torse, bras et jambes (recette aura_brasier v3) :
  lueur bleue douce et une frange de petits filaments au bord, qui tournent lentement (sens alternés).
- Décharges aux pointes : 8 points (dessus de la tête, épaules, mains, pieds), chacun deux formes d'éclair ramifié de 5 x 10 px
  (add_) en cam_ derrière sa partie du corps. Flash de 0,13 s (forme A 0,06 s puis forme B 0,07 s), tiré au hasard
  (hachage sinus sur q.life_time + q.instance_seed) : environ une décharge par seconde sur l'ensemble du corps au repos, plus
  en course, presque rien en sommeil. Une gerbe d'étincelles part du point à chaque flash (ctrl_emit −1, +7 pendant le flash).
- Filets qui montent : 4 filaments de foudre fins et verticaux dans un groupe camy_ derrière le joueur ; des impulsions
  lumineuses y montent (film de 8 images, ctrl_uv). Rentrés en sneak, glide, swim, mount, sleep.
- Cercle de sol « tambour du tonnerre » : double filet, six virgules tomoe, et un arc électrique en zigzag qui fait le tour ;
  add_ net au-dessus, double trans_ dessous ; il tourne (un tour en 24 s) ; masqué quand le corps n'est pas debout.
- Vie : l'aspect suit la vie en douceur (q.health / q.max_health, guide 6.3) : vie basse = couronne qui grésille plus vite
  (7 → 13 images/s), décharges deux fois plus fréquentes, halo qui vacille. Jamais de changement de forme.
- event_equip (2,4 s) : un éclair tombe derrière le joueur jusqu'au sol (0,04–0,24 s, un son), le cercle s'ouvre depuis le
  point d'impact, les filets montent, le halo s'allume des pieds vers la tête, la couronne s'ouvre en dernier avec une
  décharge à toutes les pointes à la fois.
- Particules : particle_etincelle (un cube de 0,5 px, une face, Face caméra) qui monte ; rien qui tombe et se pose.

États : idle, walk, run, sneak, fly, glide, swim, fall, mount, sleep (boucles), event_equip, overlay_orage (film de la
couronne et des filets, rotation du halo et du cercle). Pas d'attack ni de hurt (pièce portée). Un seul son (équipement).

Fonctions avancées : add_, trans_, cam_, camy_, ctrl_alpha, ctrl_uv, ctrl_emit, particle_/emit_, overlay_, event_equip,
son, Molang (q.life_time, q.anim_time, q.instance_seed, q.health, q.max_health, math.floor, math.mod, math.sin, ?:).
À juger en jeu (/cosmetique apercu) : additif réel de jour, couronne trans_ avec shader, hasard des décharges (rendu : certains
instants seulement), ctrl_uv (le rendu montre l'image 0 du film), suivi de la vie, ctrl_emit, overlay, particules.
Contrôle : FLASH=1 (ou A, B) force les décharges visibles (fichier .build/aura_orage_flash.bbmodel, jamais livré).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "aura_orage"
TEX = 512
SS = 4
FLASH = os.environ.get("FLASH", "")
RNG = np.random.default_rng(7)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ couleurs (foudre : cœur blanc bleuté, halo bleu, bord violet)
WHITE = np.array((232, 242, 255), np.float32)
BLUE = np.array((105, 165, 255), np.float32)
VIOLET = np.array((110, 70, 235), np.float32)
STOPS = [(0.0, (0, 0, 0)), (0.2, (14, 12, 48)), (0.45, (36, 48, 140)), (0.7, (70, 115, 225)), (0.9, (120, 170, 250)), (1.0, (150, 195, 255))]


def palette(f):
    f = np.clip(f, 0, 1)
    xs = [s_[0] for s_ in STOPS]
    return np.stack([np.interp(f, xs, [s_[1][c] for s_ in STOPS]) for c in range(3)], axis=-1)


def _segd(X, Y, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = max(vx * vx + vy * vy, 1e-9)
    t = np.clip(((X - a[0]) * vx + (Y - a[1]) * vy) / L2, 0, 1)
    return np.hypot(X - a[0] - t * vx, Y - a[1] - t * vy)


def champ(W, H, chans):
    """Distance normalisée (distance / largeur locale) au plus proche canal ; chans = [(points en texels, largeur début, fin)]."""
    yy, xx = np.mgrid[0:H * SS, 0:W * SS]
    X, Y = (xx + 0.5) / SS, (yy + 0.5) / SS
    best = np.full(X.shape, 1e9, np.float32)
    for P, wa, wb in chans:
        for j in range(len(P) - 1):
            ww = lerp(wa, wb, j / max(1, len(P) - 2))
            best = np.minimum(best, _segd(X, Y, P[j], P[j + 1]) / ww)
    return best


def foudre_rgb(best, halo=1.0, large=1.0):
    """Couleur additive sur-échantillonnée : cœur blanc net, halo bleu serré, bord violet léger."""
    core = np.clip((0.42 - best) / 0.14, 0, 1)
    g1, g2 = np.exp(-(best / (1.25 * large)) ** 2), np.exp(-(best / (2.3 * large)) ** 2)
    return np.maximum.reduce([VIOLET * 0.42 * halo * g2[..., None], BLUE * 0.85 * halo * g1[..., None], WHITE * core[..., None]])


def reduire(rgb, W, H, gain=1.0):
    im = np.array(Image.fromarray(np.clip(rgb * gain, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    arr = np.zeros((H, W, 4), np.uint8)
    lum = im.max(axis=2)
    arr[..., :3] = np.where((lum > 14)[..., None], im, 0)
    arr[..., 3] = (lum > 14) * 255
    return arr


def reduire_trans(best, W, H, a_lo=40, a_hi=120, couleur=(200, 220, 255)):
    f = np.clip(1.25 - best / 1.6, 0, 1)
    a = np.array(Image.fromarray((f * 255).astype(np.uint8), "L").resize((W, H), Image.BOX)).astype(np.float32) / 255
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = couleur
    al = np.where(a > 0.12, np.clip(a_lo + (a_hi - a_lo) * a, 1, 254), 0)
    arr[..., 3] = al.astype(np.uint8)
    arr[al == 0, :3] = 0
    return arr


def zig(r, p0, ang, L, n, dev=(20, 40)):
    """Zigzag à angles vifs depuis p0 (texels) dans la direction ang (degrés, y vers le bas de l'image), longueur L."""
    pts = [p0]
    side = 1 if r.random() < 0.5 else -1
    seg = L / n
    x, y = p0
    for i in range(n):
        a = math.radians(ang + side * r.uniform(*dev))
        l = seg * r.uniform(0.55, 1.45)
        x, y = x + l * math.cos(a), y - l * math.sin(a)
        pts.append((x, y))
        side = -side if r.random() < 0.7 else side
    return pts


def pinceau(r, p0, ang, L, w0, forks=2):
    """Pinceau de décharge : canal principal effilé + fourches fines au quart de l'épaisseur."""
    P = zig(r, p0, ang, L, int(r.integers(4, 7)), dev=(12, 34))
    chans = [(P, w0, w0 * 0.45)]
    for i in r.choice(np.arange(1, len(P) - 1), size=min(forks, len(P) - 2), replace=False):
        d = 1 if r.random() < 0.5 else -1
        Q = zig(r, P[int(i)], ang + d * r.uniform(28, 50), L * r.uniform(0.25, 0.42), 2, dev=(15, 35))
        chans.append((Q, w0 * 0.42, w0 * 0.25))
    return chans


def grille(W, H):
    n_w, n_h = W * SS, H * SS
    return np.meshgrid((np.arange(n_w) + 0.5) / n_w * 2 - 1, 1 - (np.arange(n_h) + 0.5) / n_h * 2)


# Couronne : 11 pinceaux (angle mathématique, longueur relative). Longs au-dessus, courts vers les épaules.
COURONNE = [(90, 1.0), (68, 0.86), (112, 0.9), (47, 0.74), (133, 0.76), (26, 0.62), (154, 0.6), (6, 0.5), (174, 0.52),
            (-14, 0.36), (194, 0.38)]
CN = 128
CR0 = 15.0        # départ des pinceaux (texels, caché par la tête)


def couronne_best(seed):
    r = np.random.default_rng(seed)
    chans = []
    for ang, lr in COURONNE:
        if r.random() < 0.12 and lr < 0.95:        # un pinceau éteint de temps en temps : ça grésille
            continue
        a = ang + r.uniform(-5, 5)
        L = (CN / 2 - CR0 - 2) * lr * r.uniform(0.78, 1.0)
        p0 = (CN / 2 + CR0 * math.cos(math.radians(a)), CN / 2 - CR0 * math.sin(math.radians(a)))
        chans += pinceau(r, p0, a, L, 0.95 if lr > 0.7 else 0.8, forks=2 if lr > 0.55 else 1)
    return champ(CN, CN, chans)


def couronne_add(best):
    x, y = grille(CN, CN)
    rr = np.hypot(x, y) * CN / 2
    lueur = np.exp(-((rr - CR0 - 1) / 5.0) ** 2) * smooth((rr - CR0 + 3) / 4)
    rgb = foudre_rgb(best, large=0.8) + palette(lueur * 0.5) * 0.35
    return rgb * smooth((CN / 2 - rr) / 3)[..., None]


def disque(seed, N=64):
    """Disque creux : lueur bleue douce + frange de filaments courts au bord."""
    r = np.random.default_rng(int(seed * 10))
    x, y = grille(N, N)
    rad, an = np.hypot(x, y), np.arctan2(y, x)
    wob = 1 + 0.05 * np.sin(6 * an + seed) + 0.03 * np.sin(11 * an + 2.3 * seed)
    s_ = np.clip((rad / wob - 0.42) / 0.55, 0, 1)
    f = (1 - s_) ** 2.0 * 0.95 * smooth(rad / wob / 0.42) ** 1.3 * smooth((1 - rad) / 0.06)
    chans = []
    for k in range(9):
        a = k * 40 + r.uniform(-12, 12)
        p0 = (N / 2 + 0.5 * N / 2 * math.cos(math.radians(a)), N / 2 - 0.5 * N / 2 * math.sin(math.radians(a)))
        P = zig(r, p0, a, N / 2 * r.uniform(0.28, 0.42), 3)
        chans.append((P, 0.75, 0.4))
    best = champ(N, N, chans)
    return palette(f) * 0.62 + foudre_rgb(best, halo=0.6) * 0.42 * smooth((1 - rad) / 0.1)[..., None]


def eclair(seed, W=64, H=128, w0=3.0):
    """Éclair ramifié vertical : racine en bas au centre (on le retourne pour le faire descendre)."""
    r = np.random.default_rng(seed)
    P = [(W / 2, H - 2.0)]
    side = 1 if r.random() < 0.5 else -1
    n = 6
    for i in range(1, n):
        P.append((float(np.clip(W / 2 + side * r.uniform(0.06, 0.26) * W, 0.16 * W, 0.84 * W)), H - 2 - (H - 6) * (i / n + r.uniform(-0.06, 0.06))))
        side = -side if r.random() < 0.75 else side
    P.append((W / 2 + r.uniform(-0.08, 0.08) * W, 4.0))
    chans = [(P, w0, w0 * 0.55)]
    for i in r.choice(np.arange(1, n - 1), size=3, replace=False):
        bx, by = P[int(i)]
        d = 1 if bx < W / 2 else -1
        Q = [(bx, by), (float(np.clip(bx + d * r.uniform(0.14, 0.24) * W, 3, W - 3)), by - r.uniform(0.08, 0.12) * H)]
        Q.append((float(np.clip(Q[-1][0] + d * r.uniform(0.02, 0.1) * W, 3, W - 3)), Q[-1][1] - r.uniform(0.05, 0.09) * H))
        chans.append((Q, w0 * 0.4, w0 * 0.22))
    return champ(W, H, chans)


def tomoe_mask(x, y, cx, cy, R, sens=1):
    m = np.hypot(x - cx, y - cy) < R
    rr = math.hypot(cx, cy)
    ac = math.atan2(cy, cx)
    for j in range(1, 14):
        aj = ac + sens * math.radians(4.2 * j)
        m |= np.hypot(x - (rr + 0.004 * j) * math.cos(aj), y - (rr + 0.004 * j) * math.sin(aj)) < R * (1 - j / 14.5)
    return m


RN = 128


def anneau():
    """(rgb additif, champ trans_) du cercle de sol : filets, tomoe, arc électrique en zigzag qui fait le tour."""
    x, y = grille(RN, RN)
    rad = np.hypot(x, y)
    fil = lambda rr, w: np.exp(-((rad - rr) / w) ** 2)
    f = np.maximum.reduce([fil(0.94, 0.012), 0.85 * fil(0.885, 0.008), 0.6 * fil(0.5, 0.008)])
    t = np.zeros(rad.shape, bool)
    for k in range(6):
        a = math.radians(60 * k + 15)
        t |= tomoe_mask(x, y, 0.75 * math.cos(a), 0.75 * math.sin(a), 0.075)
    f = np.maximum(f, 0.95 * t)
    r = np.random.default_rng(4)
    P = []
    for i in range(49):
        a = 2 * math.pi * i / 48
        rr = (0.62 + (0.035 if i % 2 else -0.035) * r.uniform(0.5, 1.0)) * RN / 2
        P.append((RN / 2 + rr * math.cos(a), RN / 2 - rr * math.sin(a)))
    P[-1] = P[0]
    best = champ(RN, RN, [(P, 0.9, 0.9)])
    rgb = palette(f * 0.95) + foudre_rgb(best, halo=0.7) * 0.85
    rgb *= ((rad < 0.99) * (rad > 0.44))[..., None]
    ftr = np.maximum(f, np.clip(1.2 - best / 1.4, 0, 1) * 0.8) * (rad < 0.99) * (rad > 0.44)
    return rgb, ftr


FR = 8
CW, CH = 16, 128


def filet(seed, k):
    """Image k du film d'un filet qui monte : zigzag fixe, impulsions qui montent d'une demi-hauteur sur FR images."""
    r = np.random.default_rng(seed)
    P, x = [], CW / 2
    for i in range(11):
        P.append((x, CH - 1 - (CH - 2) * i / 10))
        x = float(np.clip(CW / 2 + (1 if i % 2 else -1) * r.uniform(1.5, 4.0), 3, CW - 3))
    best = champ(CW, CH, [(P, 1.0, 0.6)])
    Y = 1 - (np.mgrid[0:CH * SS, 0:CW * SS][0] + 0.5) / (CH * SS)
    ph = k / FR * 0.5
    puls = 0.5 + 0.5 * np.cos(2 * np.pi * 2 * (Y - ph))
    env = smooth(Y / 0.2) * (1 - Y) ** 1.1
    return foudre_rgb(best, halo=0.8) * (env * (0.3 + 0.7 * puls ** 2))[..., None]


def etincelle(N=16):
    x, y = grille(N, N)
    d = np.abs(x) ** 0.5 + np.abs(y) ** 0.5
    m = np.array(Image.fromarray(((d < 0.95) * 255).astype(np.uint8), "L").resize((N, N), Image.LANCZOS)) > 110
    c = np.array(Image.fromarray(((d < 0.55) * 255).astype(np.uint8), "L").resize((N, N), Image.LANCZOS)) > 110
    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = (140, 190, 255)
    out[c, :3] = (240, 246, 255)
    out[..., 3] = m * 255
    return out


UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)


def poser(nom, im, x, y):
    h, w = im.shape[:2]
    assert x + w <= TEX and y + h <= TEX and not tex[y:y + h, x:x + w, 3].any(), nom
    tex[y:y + h, x:x + w] = im
    UV[nom] = (x, y, x + w, y + h)


G_CR, G_FORT, G_DOUX, G_SOL, G_FIL, G_ECL = 0.72, 0.16, 0.26, 0.52, 0.95, 0.85     # gains additifs (cumul mesuré, .build/cumul.py)
CB = [couronne_best(s_) for s_ in (11, 23, 37, 59)]
for k, b in enumerate(CB):
    poser(f"cour{k}", reduire(couronne_add(b), CN, CN, G_CR), CN * k, 0)
poser("courT", reduire_trans(CB[0], CN, CN, 22, 70, couleur=(170, 200, 255)), 0, 128)
RA, RT = anneau()
poser("anneau", reduire(RA, RN, RN, G_SOL), 128, 128)
fa = np.array(Image.fromarray((RT * 255).astype(np.uint8), "L").resize((RN, RN), Image.LANCZOS)).astype(np.float32) / 255
an_t = np.zeros((RN, RN, 4), np.uint8)
an_t[..., :3] = (80, 110, 200)          # sombre et léger : l'additif posé dessus ne sature pas (cumul mesuré)
an_t[..., 3] = np.where(fa > 0.25, np.clip(30 + 70 * fa, 30, 100), 0).astype(np.uint8)
an_t[an_t[..., 3] == 0, :3] = 0
poser("anneauT", an_t, 256, 128)
for k, sd in enumerate((1.0, 2.6, 4.1, 5.7)):
    poser(f"{'fort' if k < 2 else 'doux'}{k % 2}", reduire(disque(sd), 64, 64, G_FORT if k < 2 else G_DOUX), 384 + 64 * (k % 2), 128 + 64 * (k // 2))
for i, sd in enumerate((31, 47, 83, 97)):
    poser(f"ecl{i}", reduire(foudre_rgb(eclair(sd), large=0.9), 64, 128, G_ECL), 64 * i, 256)
for v, sd in enumerate((5, 9)):
    for k in range(FR):
        poser(f"fil{v}{k}", reduire(filet(sd, k), CW, CH, G_FIL), 256 + v * 128 + k * CW, 256)
poser("spark", etincelle(), 0, 384)
for n in UV:
    if not n.endswith("T"):
        u0, v0, u1, v1 = UV[n]
        assert set(np.unique(tex[v0:v1, u0:u1, 3])) <= {0, 255}, n
im_ = Image.fromarray(tex, "RGBA")
im_.save(f"{NOM}.png", optimize=True)
_buf = io.BytesIO()
im_.save(_buf, "PNG", optimize=True)
tex_b64 = "data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode()


# ------------------------------------------------------------------ géométrie
def nuid():
    return str(_uuid.uuid4())


class G:
    def __init__(self, nom, origin, parent=None):
        assert len(nom) <= 64
        self.nom, self.origin, self.uuid, self.enfants = nom, [round(float(v), 3) for v in origin], nuid(), []
        if parent is not None:
            parent.enfants.append(self)

    def json(self):
        return {"name": self.nom, "origin": self.origin, "uuid": self.uuid, "children": [c.json() if isinstance(c, G) else c for c in self.enfants]}


elements = []


def plaque(g, nom, c, w, h, uv, face="south", ep=0.3, anchor="center"):
    c = np.asarray(c, float)
    dy = {"center": 0.0, "top": -h / 2, "bottom": h / 2}[anchor]
    if face in ("south", "north"):
        a, b = c + (-w / 2, -h / 2 + dy, -ep / 2), c + (w / 2, h / 2 + dy, ep / 2)
    else:
        a, b = c - (w / 2, ep / 2, h / 2), c + (w / 2, ep / 2, h / 2)
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in a], "to": [round(float(v), 3) for v in b],
         "origin": [round(float(v), 3) for v in c], "box_uv": False, "faces": {face: {"uv": [round(float(v), 2) for v in uv], "texture": 0}}}
    elements.append(e)
    g.enfants.append(e["uuid"])


def uvf(n, fu=False, fv=False):
    u0, v0, u1, v1 = UV[n]
    return [u1 if fu else u0, v1 if fv else v0, u0 if fu else u1, v0 if fv else v1]


MEMBRES = {m: G(m, (0, 24, 0)) for m in ("head", "body", "right_arm", "left_arm", "right_leg", "left_leg")}
RECUL = {"tete": 4.5, "corps": 4.0, "bras_d": 3.4, "bras_g": 3.4, "jambe_d": 3.4, "jambe_g": 3.4}
ZONES = {
    "tete": ("head", (0, 28, 0), [((0, 28.4, 0), 9.4, "fort")]),
    "corps": ("body", (0, 18, 0), [((0, 21.5, 0), 6.4, "fort"), ((0, 18, 0), 5.8, "doux"), ((0, 14.5, 0), 5.8, "doux")]),
    "bras_d": ("right_arm", (6, 18, 0), [((6, 21.5, 0), 5.4, "doux"), ((6, 18, 0), 4.8, "doux"), ((6, 14.2, 0), 4.6, "doux")]),
    "bras_g": ("left_arm", (-6, 18, 0), [((-6, 21.5, 0), 5.4, "doux"), ((-6, 18, 0), 4.8, "doux"), ((-6, 14.2, 0), 4.6, "doux")]),
    "jambe_d": ("right_leg", (2, 6, 0), [((2, 9.5, 0), 4.8, "doux"), ((2, 4.5, 0), 4.6, "doux")]),
    "jambe_g": ("left_leg", (-2, 6, 0), [((-2, 9.5, 0), 4.8, "doux"), ((-2, 4.5, 0), 4.6, "doux")]),
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

# Couronne de Saint-Elme : derrière la nuque (repère de la tête), film add_ + double trans_ plus loin derrière.
GC = (0, 28.5, 0)
GR = 7.0
AURA["couronne"] = G("aura_couronne", GC, MEMBRES["head"])
ETAT["couronne"] = G("etat_couronne", GC, AURA["couronne"])
CAMC = G("cam_couronne", GC, ETAT["couronne"])
ADD["couronne"] = G("add_couronne", GC, CAMC)
ALPHA["couronne"] = G("ctrl_alpha", GC, ADD["couronne"])
UV_COUR = G("ctrl_uv", GC, ADD["couronne"])
plaque(ADD["couronne"], "couronne", (GC[0], GC[1], GC[2] - GR), 32, 32, UV["cour0"])
TRANS_C = G("trans_couronne", GC, CAMC)
ALPHA["couronne_t"] = G("ctrl_alpha", GC, TRANS_C)
plaque(TRANS_C, "couronne_voile", (GC[0], GC[1], GC[2] - GR - 0.6), 32, 32, UV["courT"])

# Décharges aux pointes : (zone, point, largeur, hauteur, vers le haut)
POINTS = [("tete", (-1.8, 32.2, 0), 5.0, 10.0, True), ("tete", (2.2, 32.0, 0), 4.6, 9.0, True),
          ("bras_d", (7.2, 24.0, 0), 4.6, 9.0, True), ("bras_g", (-7.2, 24.0, 0), 4.6, 9.0, True),
          ("bras_d", (6.6, 12.0, 0), 4.6, 9.5, False), ("bras_g", (-6.6, 12.0, 0), 4.6, 9.5, False),
          ("jambe_d", (3.4, 1.5, 0), 4.0, 7.0, True), ("jambe_g", (-3.4, 1.5, 0), 4.0, 7.0, True)]
BOLTS, EMITS, EMITS_LIBRES = [], [], []
for i, (z, p, w, h, up) in enumerate(POINTS):
    cam = G(f"cam_eclair{i + 1}", p, ETAT[z])
    forms = []
    for j, dz in enumerate((0.0, 0.4)):
        ti = (i + 2 * j) % 4
        fg = G(f"add_eclair{i + 1}{'ab'[j]}", p, cam)
        G("ctrl_alpha", p, fg)
        anc = "bottom" if up else "top"
        plaque(fg, f"eclair{i + 1}{'ab'[j]}", (p[0], p[1], p[2] - 2.2 - dz), w, h, uvf(f"ecl{ti}", (p[0] < 0) != (j == 1), not up), anchor=anc)
        forms.append(fg)
    cc = 0.41 + 3.17 * i
    BOLTS.append((forms[0], forms[1], cc))
    e = G("emit_etincelle" + (str(len(EMITS) + 1) if EMITS else ""), p, ETAT[z])
    G("ctrl_emit", p, e)
    EMITS.append((e, cc))

# Filets qui montent : camy_ centré sur le torse, z local < 0 = derrière le joueur vu de la caméra.
FLUX_C = (0, 14, 0)
AURA["flux"] = G("aura_flux", FLUX_C, MEMBRES["body"])
ETAT["flux"] = G("etat_flux", FLUX_C, AURA["flux"])
MONTE = G("monte_flux", (0, 0, 0), ETAT["flux"])
CAMY = G("camy_flux", FLUX_C, MONTE)
ADD["flux"] = G("add_flux", FLUX_C, CAMY)
ALPHA["flux"] = G("ctrl_alpha", FLUX_C, ADD["flux"])
FILETS = [(-5.2, -4.4, 10.0, 24.0, 3.2, 0), (5.0, -4.55, 10.5, 23.0, 3.2, 1), (-8.6, -3.8, 2.0, 22.0, 2.8, 1),
          (8.6, -3.95, 1.5, 22.0, 2.8, 0)]          # aucun filet derrière la tête : il doublerait la couronne (cumul)
COLS = []
for i, (x, zz, y0, hh, ww, v) in enumerate(FILETS):
    g = G(f"filet{i}", (x, y0, zz), ADD["flux"])
    plaque(g, f"filet{i}", (x, y0 + hh / 2, zz), ww, hh, uvf(f"fil{v}0", i % 2 == 1))
    COLS.append((g, G("ctrl_uv", (x, y0, zz), g), v, i))

# Cercle de sol : add_ net au-dessus, trans_ dessous ; tourne dans overlay_orage ; masqué hors de la station debout.
SC = (0, 0.4, 0)
AURA["sol"] = G("aura_sol", SC, MEMBRES["body"])
ETAT["sol"] = G("etat_sol", SC, AURA["sol"])
SOL = G("sol_tourne", SC, ETAT["sol"])
ADD["sol"] = G("add_sol", SC, SOL)
ALPHA["sol"] = G("ctrl_alpha", SC, ADD["sol"])
plaque(ADD["sol"], "anneau", (0, 0.75, 0), 26, 26, UV["anneau"], face="up")
TRANS_S = G("trans_sol", SC, SOL)
plaque(TRANS_S, "anneau_voile", (0, 0.35, 0), 26, 26, UV["anneauT"], face="up")
for k in range(4):
    a = math.radians(45 + 90 * k)
    EMITS_LIBRES.append(G(f"emit_etincelle{len(EMITS) + len(EMITS_LIBRES) + 1}", (9.6 * math.cos(a), 0.9, 9.6 * math.sin(a)), SOL))

# Éclair de l'apparition : camy_ derrière le joueur, du ciel au sol (3 plaques bout à bout), caché dans les états.
FC = (0, 24, 0)
FOUDRE = G("foudre", FC, MEMBRES["body"])
CAMY_F = G("camy_foudre", FC, FOUDRE)
ADD_F = G("add_foudre", FC, CAMY_F)
ALPHA["foudre"] = G("ctrl_alpha", FC, ADD_F)
for j in range(3):
    y1 = 50.0 - 16.6 * j
    plaque(ADD_F, f"foudre{j}", (0, y1 - 8.3, -5.5), 8.3, 16.6, uvf(f"ecl{j}", j % 2 == 1, True))

PART = G("particle_etincelle", (0, 0, 0))
plaque(PART, "etincelle", (0, 0.55, 0), 0.5, 0.5, UV["spark"])
outliner = [MEMBRES[m].json() for m in MEMBRES] + [PART.json()]


# ------------------------------------------------------------------ animations
def s(v):
    return v if isinstance(v, str) else str(round(v + 0.0, 4))


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": s(x), "y": s(y), "z": s(z)}], "time": round(t, 4), "interpolation": "linear"}


def piste(A, g, keys):
    A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += keys


def sinus(L, k, ph, amp, base=0.0):
    if amp == 0:
        return base
    return f"{s(base)}+{s(amp)}*math.sin(q.anim_time*{s(360 * k / L)}+{int(ph)})"


VIE = "(q.max_health>0?q.health/q.max_health:1)"     # 1 = pleine vie (et dans les aperçus)
MANQUE = f"(1-{VIE})"


def _x(P, c):
    return f"(q.life_time/{P:g}+q.instance_seed*17+{c:.3g})"


def vis(P, p, c, w0, w1):
    """1 pendant la fenêtre [w0, w1[ s d'une tranche de P s tirée avec la probabilité p (plus haute quand la vie baisse)."""
    if FLASH:
        return "1" if FLASH == "1" or (FLASH == "A") == (w0 == 0) else "0"
    x = _x(P, c)
    k = f"math.mod(math.abs(math.sin(math.floor({x})*127.1))*437.585,1)"
    w = f"(math.mod({x},1)-0.05-{k}*{0.8 / p:.3g})"
    return f"({k}<{p:g}*(1+{MANQUE}))*({w}>{w0 / P:.3g})*({w}<{w1 / P:.3g})"


PH = {z: int(RNG.integers(0, 360)) for z in list(ZONES) + ["couronne", "sol", "flux"]}
PH_C = [(int(RNG.integers(0, 360)), int(RNG.integers(0, 360))) for _ in COLS]


def etat(nom, L, rate, halo=1.0, souffle=0.035, alpha=-0.15, a_amp=0.08, recul=0.0, sol=1.0, flux=1.0, fpos=(0, 0, 0),
         cour=1.0, c_alpha=0.0, c_recul=0.0, kb=1):
    A = {}
    vac = f"-{MANQUE}*0.3*math.abs(math.sin(q.life_time*1130))"          # vie basse : le halo vacille
    for z in ZONES:
        sc = sinus(L, kb, PH[z], halo * souffle, halo)
        piste(A, ETAT[z], [kf("scale", 0, sc, sc, sc)])
        if recul:
            piste(A, ETAT[z], [kf("position", 0, 0, 0, recul)])
        piste(A, ALPHA[z], [kf("position", 0, sinus(L, kb, PH[z] + 90, a_amp, alpha) + vac, 0, 0)])
    sg = sinus(L, kb, PH["couronne"], cour * 0.03, cour)
    piste(A, ETAT["couronne"], [kf("scale", 0, sg, sg, sg)])
    if c_recul:
        piste(A, ETAT["couronne"], [kf("position", 0, 0, 0, c_recul)])
    for z in ("couronne", "couronne_t"):
        piste(A, ALPHA[z], [kf("position", 0, sinus(L, kb, PH["couronne"] + 90, 0.06, alpha * 0.5 + c_alpha) + vac, 0, 0)])
    P, p = rate
    for fa_, fb_, c in BOLTS:
        for j, fg in enumerate((fa_, fb_)):
            w0, w1 = ((0.0, 0.06), (0.06, 0.13))[j]
            e = f"{vis(P, p, c, w0, w1)}-1"
            assert len(e) <= 512, len(e)
            piste(A, fg.enfants[0], [kf("position", 0, e, 0, 0)])
    for g, c in EMITS:
        piste(A, g.enfants[0], [kf("position", 0, f"8*{vis(P, p, c, 0.0, 0.22)}-1", 0, 0)])
    piste(A, ALPHA["foudre"], [kf("position", 0, -1, 0, 0)])
    piste(A, ALPHA["flux"], [kf("position", 0, sinus(L, kb, PH["flux"], 0.06, alpha), 0, 0)])
    if any(fpos):
        piste(A, ETAT["flux"], [kf("position", 0, *fpos)])
    for (g, _, v, i), (p1, p2) in zip(COLS, PH_C):
        sy = f"{s(flux)}*(1+0.05*math.sin(q.anim_time*{s(360 * (1 + i % 2) / L)}+{p1}))"
        piste(A, g, [kf("scale", 0, s(flux), sy, 1)])
    sc = sinus(L, kb, PH["sol"], sol * 0.03, sol)
    piste(A, ETAT["sol"], [kf("scale", 0, sc, 1 if sol else 0, sc)])
    return {"uuid": nuid(), "name": nom, "loop": "loop", "override": False, "length": L, "snapping": 24, "selected": nom == "idle", "animators": A}


STATES = [
    etat("idle", 8.0, (6.0, 0.55), kb=2),
    etat("walk", 1.6, (4.5, 0.55), recul=0.3, fpos=(0, 0, 1.5), c_recul=0.5),
    etat("run", 1.0, (3.0, 0.65), alpha=-0.05, a_amp=0.03, recul=0.8, fpos=(0, -0.5, 3.5), cour=1.06, c_recul=1.4),
    etat("sneak", 4.0, (10.0, 0.3), halo=0.9, alpha=-0.35, sol=0, flux=0, cour=0.8, c_alpha=-0.15),
    etat("fly", 2.4, (4.0, 0.55), alpha=-0.1, recul=0.4, sol=0, fpos=(0, 0, 2.0), cour=1.05, c_recul=0.8),
    etat("glide", 3.6, (4.0, 0.5), alpha=-0.15, sol=0, flux=0, cour=0.6, c_alpha=-0.2),
    etat("swim", 3.6, (8.0, 0.3), alpha=-0.3, sol=0, flux=0, cour=0.5, c_alpha=-0.3),
    etat("fall", 2.0, (4.0, 0.55), halo=1.04, alpha=-0.1, sol=0.8, fpos=(0, 1.0, 0), cour=1.08),
    etat("mount", 4.0, (8.0, 0.4), alpha=-0.25, sol=0, flux=0, cour=0.9),
    etat("sleep", 4.0, (16.0, 0.15), halo=0.85, souffle=0.02, alpha=-0.8, a_amp=0.05, sol=0, flux=0, cour=0.55, c_alpha=-0.35),
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


def creneaux(ch, fen, L, val=1.0):
    ts = {0.0, L}
    for a, b in fen:
        ts |= {max(0.0, a - 0.005), a, max(0.0, b - 0.005), b}
    out = []
    for t in sorted(ts):
        tt = t if t < L else L - 1e-6
        out.append(kf(ch, t, val if any(a <= tt < b for a, b in fen) else 0.0, 0, 0))
    return out


def apparition(A, fg, fen, L):
    """Flash forcé par-dessus l'état : ctrl_alpha +1 pendant toute l'animation (0 à la fin), échelle 0 hors des fenêtres."""
    piste(A, fg.enfants[0], [kf("position", 0, 1, 0, 0), kf("position", L - 0.005, 1, 0, 0), kf("position", L, 0, 0, 0)])
    ks = creneaux("position", fen, L)
    piste(A, fg, [kf("scale", k["time"], *([float(k["data_points"][0]["x"])] * 3)) for k in ks[:-1]] + [kf("scale", L, 1, 1, 1)])


# event_equip : l'éclair tombe, le cercle s'ouvre depuis le point d'impact, les filets montent, le halo s'allume des pieds
# vers la tête, la couronne s'ouvre en dernier avec une décharge à toutes les pointes ; un son au coup de foudre.
LE = 2.4
TE = [j * LE / 48 for j in range(49)]
A = {}
piste(A, ALPHA["foudre"], creneaux("position", [(0.04, 0.12), (0.15, 0.24)], LE))
for g in DISQUES:
    t0 = 0.45 + (HAUT[g.uuid] / 33) * 0.9
    piste(A, g, [kf("scale", t, *([sm(t, t0, t0 + 0.45) * (1 + 0.12 * bump(t, t0 + 0.3, t0 + 0.45, t0 + 0.55, t0 + 0.9))] * 3)) for t in TE])
piste(A, AURA["sol"], [kf("scale", t, *([sm(t, 0.12, 0.7) * (1 + 0.08 * bump(t, 0.55, 0.7, 0.8, 1.2))] * 3)) for t in TE])
piste(A, MONTE, [kf("scale", t, 1, sm(t, 0.3, 1.3), 1) for t in TE])
piste(A, AURA["couronne"], [kf("scale", t, *([sm(t, 1.35, 1.75) * (1 + 0.12 * bump(t, 1.6, 1.75, 1.85, 2.3))] * 3)) for t in TE])
for fa_, fb_, c in BOLTS:
    apparition(A, fa_, [(1.72, 1.79)], LE)
    apparition(A, fb_, [(1.79, 1.86)], LE)
for g, c in EMITS:
    piste(A, g.enfants[0], creneaux("position", [(1.72, 1.95)], LE, 8.0))
A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "block.copper_bulb.turn_on", "file": ""}], "time": 0.04}]}
equip = {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": LE, "snapping": 24,
         "selected": False, "animators": A}

# overlay_orage : la couronne grésille (images tirées au hasard, plus vite quand la vie baisse), les filets montent, le halo
# et le cercle tournent.
LO = 24.0
A = {}
cad = f"(7+6*{MANQUE})"
piste(A, UV_COUR, [kf("position", 0, f"{CN}*math.floor(math.mod(math.abs(math.sin(math.floor(q.anim_time*{cad})*91.7+q.instance_seed*13))*43.758,1)*4)", 0, 0)])
for (g, uvg, v, i) in COLS:
    fps = 5 + (i % 3)                                   # 120, 144 ou 168 images par boucle de 24 s : film fermé (multiple de FR)
    piste(A, uvg, [kf("position", 0, f"math.floor(math.mod(q.anim_time*{fps}+{i * 3},{FR}))*{CW}", 0, 0)])
piste(A, SOL, [kf("rotation", 0, 0, f"q.anim_time*{s(360 / LO)}", 0)])
for j, g in enumerate(DISQUES):
    piste(A, g, [kf("rotation", 0, 0, 0, f"q.anim_time*{s((1 if j % 2 else -1) * 360 / LO)}")])
overlay = {"uuid": nuid(), "name": "overlay_orage", "loop": "loop", "override": False, "length": LO, "snapping": 24, "selected": False, "animators": A}

PF = 0.4
p_fall = {"uuid": nuid(), "name": "particle_etincelle_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24, "selected": False,
          "animators": {PART.uuid: {"name": PART.nom, "type": "bone", "keyframes":
                        [kf("scale", t, *([1 + 0.35 * math.cos(2 * math.pi * t / PF)] * 3)) for t in [i * PF / 8 for i in range(9)]]}}}

ANIMS = STATES + [equip, overlay, p_fall]
assert len(ANIMS) <= 32 and len(EMITS) + len(EMITS_LIBRES) <= 32
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}],
         "animations": ANIMS}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
from menu_aura import adapter_menu
adapter_menu(model, cacher=False)
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel" if not FLASH else f".build/{NOM}_flash.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


def ngroupes(n):
    return 1 + sum(ngroupes(c) for c in n.get("children", []) if isinstance(c, dict))


print(len(elements), "cubes ;", sum(ngroupes(n) for n in outliner), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      len(EMITS) + len(EMITS_LIBRES), "emit_")
