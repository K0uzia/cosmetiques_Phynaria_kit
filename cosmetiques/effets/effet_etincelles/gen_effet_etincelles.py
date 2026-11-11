"""Effet de téléportation « Cercle d'étincelles » (guide 15), pièce sans ensemble. Design original, fiche de référence
.claude/references/effets/anneaux-etincelles.md (déroulé, formes, couleurs échantillonnées, timing, sons).
Écrit effet_etincelles.png, effet_etincelles_e.png et .build/effet_etincelles_brut.bbmodel. v1 : .build/gen_v1.py.

v2 (retour en jeu du 2026-11-07, captures 16.44.14 à 16.44.16 : « le cercle d'étincelles est à améliorer ») : en jeu, un
fin anneau doré seul ; chevelure et gerbes peintes en traits de 1 à 2 texels sur des plaques à 26 texels/px, effacées par les
mipmaps à quelques blocs (cause mesurée avec .build/sim_jeu.py) ; porte en camy_ que la copie du joueur longeait sans la
traverser. v2 :
- **Porte fixe** dressée (plan XY, face à −Z), rayon 24 px (3 blocs de diamètre), centre à y = 25 (bas au ras du sol) : la
  copie la traverse vue de partout. Volume par la tranche : tube en géométrie et étincelles réparties sur ±1,5 px.
- **Tube** de 160 segments : âme opaque (calque _e plein, lisible de jour comme de nuit) dans une gaine add_ ; chaque segment
  apparaît quand la pointe passe (Molang) : la porte se trace en spirale depuis la main (charge), en grandissant.
- **Bord qui fourmille** : 5 couronnes de traits d'étincelles (360 poutres add_ de 0,5 à 0,8 px, visibles de tous côtés,
  texture pleine en travers : rien que les mipmaps puissent moyenner), qui tournent à des vitesses et des sens différents ;
  chaque trait palpite (Molang).
- **Gerbes tangentes** : 240 traits lancés le long de la tangente depuis 8 foyers, avec gravité (Molang, boucle sans fin).
- **Étincelles au sol** : 56 points qui tombent du bas de l'anneau et rebondissent trois fois en s'éteignant.
- Pointe-comète qui trace la spirale, nœud d'étincelles dans la main, voile chaud intérieur (add_, ctrl_alpha), éclairs cam_.
- Le joueur entre dans l'anneau (une seule courbe, élan croissant) et disparaît dans son plan en se resserrant vers son
  centre du corps, sous un éclair ; à l'arrivée il en sort en grandissant puis ralentit jusqu'à sa place.
- Charge : sceaux des mains agrandis (runes en traits de 0,4 à 0,6 px).
Mouvements : une courbe lisse par phase, 30 clés/s ; mouvements périodiques des étincelles en Molang (continus en jeu).

Particules (guide 5 ter ; cadence animée par ctrl_emit) : etincelle (trait vif 0,6 × 2,6 px), braise (point de 1 px qui se
pose), glyphe (rune de 1,6 px, charge), emit_mc_wax_on, emit_mc_small_flame, emit_mc_electric_spark. Pas d'end_rod.
Sons embarqués originaux (sons/) : etincelles_ouverture, etincelles_passage, etincelles_extinction (une étape chacun).

Fonctions : add_, _e, cam_, ctrl_alpha, ctrl_emit, particle_/emit_, emit_mc_, Molang (q.anim_time, math.mod), groupe joueur,
sons embarqués. À juger en jeu : densité et éclat des étincelles à 3–10 blocs, de jour ; Molang des étincelles ; ctrl_alpha du
voile ; particules et cadences ; avec shader.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "effet_etincelles"
TEX = 512
SS = 2
TAU = 2 * math.pi
FPS = 30

# ------------------------------------------------------------------ dimensions (px)
R = 24.0                 # rayon de la porte (3 blocs de diamètre)
YC = 25.0                # hauteur du centre (bas du tube à y ≈ 0,4)
ZD = -16.0               # porte du départ : 1 bloc devant le joueur
ZA = 15.0                # porte de l'arrivée : dans son dos
HHALO = R + 6.0          # demi-côté de la plaque de lueur
MAIN_D, MAIN_G = (9.5, 12.0, -4.0), (-9.5, 12.0, -4.0)   # devant et à côté des mains (hors du corps)
HSCEAU = 5.0             # demi-côté d'un sceau de main
NSEG = 160               # segments du tube
W_AME, W_GAINE = 1.3, 2.6

# ------------------------------------------------------------------ palette (échantillonnée sur la référence)
# lumière > 240 : (248, 172, 103) ; 200–240 : (217, 140, 77) ; 150–200 : (172, 110, 60) ; 100–150 : (121, 80, 55)
STOPS = [(0.0, (0, 0, 0)), (0.2, (70, 26, 6)), (0.45, (172, 92, 34)), (0.7, (232, 146, 66)), (0.88, (250, 196, 120)),
         (1.0, (255, 240, 205))]


def palette(f):
    f = np.clip(f, 0, 1)
    xs = [s_[0] for s_ in STOPS]
    return np.stack([np.interp(f, xs, [s_[1][c] for s_ in STOPS]) for c in range(3)], axis=-1)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def grille(N, demi):
    n = N * SS
    c = ((np.arange(n) + 0.5) / n * 2 - 1) * demi
    return np.meshgrid(c, -c)


def vers_add(f, N, gain):
    """Intensité f (sur-échantillonnée) -> RGBA additif : couleur de la palette × gain, noir transparent (alpha 0/255)."""
    taille = (N, N) if np.ndim(N) == 0 else N
    g = np.array(Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8), "L").resize(taille, Image.LANCZOS)).astype(float) / 255
    rgb = palette(g) / 255 * gain * np.clip(g * 1.4, 0, 1)[..., None]
    arr = np.zeros(g.shape + (4,), np.uint8)
    arr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    lum = arr[..., :3].max(axis=2)
    arr[..., 3] = (lum > 8) * 255
    arr[lum <= 8, :3] = 0
    return arr


def profil_add(prof, gain, w=4):
    """Texture w × len(prof) : intensité constante en travers (u), profil le long de v. Pleine en travers : les mipmaps ne
    la moyennent pas avec du noir (cause de la v1)."""
    f = np.repeat(np.asarray(prof, float)[:, None], w, axis=1)
    rgb = palette(f) / 255 * gain * np.clip(f * 1.6, 0, 1)[..., None]
    arr = np.zeros(f.shape + (4,), np.uint8)
    arr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    lum = arr[..., :3].max(axis=2)
    arr[..., 3] = (lum > 6) * 255
    arr[lum <= 6, :3] = 0
    return arr


def segment_d(x, y, a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    t = np.clip(((x - a[0]) * d[0] + (y - a[1]) * d[1]) / max(d @ d, 1e-12), 0, 1)
    return x - a[0] - t * d[0], y - a[1] - t * d[1]


def anneau(r, r0, w):
    return np.exp(-((r - r0) / w) ** 2)


# ------------------------------------------------------------------ textures
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


# 1. halo du bord (add_, deux faces) : lueur douce autour du tube, à 4,3 texels/px
x, y = grille(256, HHALO)
r = np.hypot(x, y)
poser("halo", vers_add(np.exp(-((r - R) / 1.6) ** 2) * 0.75 + np.exp(-((r - R) / 4.5) ** 2) * 0.3, 256, 120), 0, 0)

# 2. voile intérieur (add_, sombre et chaud) : air brûlant qui tourbillonne
x, y = grille(256, R)
r, phi = np.hypot(x, y), np.arctan2(y, x)
tourb = 0.5 + 0.5 * np.sin(3 * phi + r * 0.45)
f_v = smooth((R - 1.2 - r) / 1.5) * (0.22 + 0.5 * (r / R) ** 3 + 0.1 * tourb)
poser("voile", vers_add(f_v * 0.7, 256, 58), 256, 0)

# 3. âme du tube (opaque + _e plein) : bord orange, milieu jaune blanc ; profil le long de v
v_ = (np.arange(16) + 0.5) / 16
prof = 1 - np.abs(v_ - 0.5) * 2
col = palette(0.72 + 0.28 * prof ** 0.7)
ame = np.zeros((16, 4, 4), np.uint8)
ame[..., :3] = np.repeat(col[:, None, :], 4, axis=1).astype(np.uint8)
ame[..., 3] = 255
poser("ame", ame, 256, 256, e=ame)

# 4. gaine du tube (add_) : lueur en travers du tube
poser("gaine", profil_add(np.exp(-((np.arange(32) + 0.5) / 32 - 0.5) ** 2 / 0.05), 95), 264, 256)

# 5. traits d'étincelles (add_) : tête en haut de l'image (v = 0), queue qui s'éteint ; plein en travers
lg = (np.arange(32) + 0.5) / 32
poser("trait", profil_add(0.94 * (1 - lg) ** 1.4, 255), 272, 256)                      # vif
poser("trait_or", profil_add(0.8 * (1 - lg) ** 1.1, 235), 280, 256)            # plus orange
poser("point", profil_add(np.ones(8) * 0.95, 255, w=8), 288, 256)              # braise du sol (cube plein)
poser("p_eti", profil_add((1 - (np.arange(16) + 0.5) / 16) ** 1.2, 255), 296, 256)

# 6. étoile (pointe, nœud, éclair)
x, y = grille(32, 1.0)
r = np.hypot(x, y)
f_e = np.maximum(np.clip(1 - (np.abs(x) ** 0.5 + np.abs(y) ** 0.5), 0, 1) ** 0.9, np.exp(-(r / 0.35) ** 2) * 0.85)
poser("etoile", vers_add(f_e, 32, 255), 304, 256)
x, y = grille(128, 1.0)
r = np.hypot(x, y)
f_fl = np.maximum.reduce([np.exp(-(r / 0.28) ** 2), 0.55 * np.exp(-(r / 0.6) ** 2),
                          np.exp(-(np.abs(x) / 0.035) ** 2) * np.clip(1 - np.abs(y), 0, 1) ** 2,
                          np.exp(-(np.abs(y) / 0.035) ** 2) * np.clip(1 - np.abs(x), 0, 1) ** 2])
poser("flash", vers_add(f_fl, 128, 255), 0, 384)                              # éclair du passage (4,9 texels/px)
x, y = grille(16, 1.0)
r = np.hypot(x, y)
poser("braise", vers_add(smooth((0.8 - r) / 0.2) * (0.7 + 0.3 * np.exp(-(r / 0.4) ** 2)), 16, 250), 336, 256)
f_g = np.maximum(anneau(r, 0.66, 0.14), np.exp(-(np.hypot(*segment_d(x, y, (0, -0.55), (0, 0.55))) / 0.14) ** 2))
poser("glyphe", vers_add(f_g, 16, 255), 352, 256)


# 7. sceaux des mains (add_) : runes inventées, traits épais (0,4–0,6 px à l'échelle du sceau)
def rune(x, y, cx, cy, ang, k, s, w):
    c, sn = math.cos(ang), math.sin(ang)
    loc = lambda u, v: (cx + u * c - v * sn, cy + u * sn + v * c)
    seg = lambda p, q: np.exp(-(np.hypot(*segment_d(x, y, loc(*p), loc(*q))) / w) ** 2)
    forme = k % 5
    if forme == 0:
        q = loc(0, s * 0.9)
        return np.maximum(seg((-s, 0), (s, 0)), np.exp(-(np.hypot(x - q[0], y - q[1]) / (1.4 * w)) ** 2))
    if forme == 1:
        return np.maximum(seg((-s, -s * 0.7), (s, 0)), seg((s, 0), (-s, s * 0.7)))
    if forme == 2:
        return np.maximum.reduce([seg((-s, 0), (s, 0)), seg((s, 0), (s, s * 0.6)), seg((-s, 0), (-s, -s * 0.6))])
    if forme == 3:
        return np.maximum(seg((-s, -s * 0.5), (s, s * 0.5)), seg((-s * 0.3, s * 0.6), (s * 0.3, -s * 0.6)))
    f = np.zeros_like(x)
    for p in ((-s * 0.7, -s * 0.5), (-s * 0.7, s * 0.5), (s * 0.8, 0)):
        q = loc(*p)
        f = np.maximum(f, np.exp(-(np.hypot(x - q[0], y - q[1]) / (1.5 * w)) ** 2))
    return f


x, y = grille(128, 1.0)
r, phi = np.hypot(x, y), np.arctan2(y, x)
f_a = np.maximum.reduce([anneau(r, 0.92, 0.05), anneau(r, 0.62, 0.04)])
for k in range(8):                                   # couronne de huit runes, chacune différente de ses voisines
    a = TAU * k / 8 + 0.2
    f_a = np.maximum(f_a, rune(x, y, 0.77 * math.cos(a), 0.77 * math.sin(a), a, (k * 3) % 5, 0.095, 0.045))
for k in range(16):                                  # graduations sur le filet extérieur
    a = TAU * (k + 0.5) / 16
    f_a = np.maximum(f_a, np.exp(-(np.hypot(*segment_d(x, y, (0.92 * math.cos(a), 0.92 * math.sin(a)),
                                                     (0.99 * math.cos(a), 0.99 * math.sin(a)))) / 0.035) ** 2))
poser("sceau_a", vers_add(f_a, 128, 255), 0, 256)
f_b = anneau(r, 0.94, 0.05)
for sq in (0, 45):                                   # étoile à huit branches : deux carrés
    pts = [(0.9 * math.cos(math.radians(sq + 45 + 90 * k)), 0.9 * math.sin(math.radians(sq + 45 + 90 * k))) for k in range(4)]
    for k in range(4):
        f_b = np.maximum(f_b, np.exp(-(np.hypot(*segment_d(x, y, pts[k], pts[(k + 1) % 4])) / 0.045) ** 2))
f_b = np.maximum.reduce([f_b, anneau(r, 0.34, 0.045), np.exp(-(r / 0.13) ** 2)])
poser("sceau_b", vers_add(f_b, 128, 255), 128, 256)

CLEAR = [TEX - 2, TEX - 2, TEX - 1, TEX - 1]
assert not tex[TEX - 2:, TEX - 2:, 3].any()
assert set(np.unique(tex[..., 3])) <= {0, 255}        # aucune semi-transparence (pas de groupe trans_)
tex_e[tex_e[..., 3] == 0, :3] = 0


def b64(arr, chemin):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(chemin, optimize=True)
    b = io.BytesIO()
    im_.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


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


def cube(g, nom, a, b, faces, origin=None):
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in a], "to": [round(float(v), 4) for v in b],
         "origin": [round(float(v), 4) for v in (origin if origin is not None else (np.add(a, b) / 2))], "box_uv": False,
         "faces": {k: {"uv": [round(float(v), 3) for v in uv], "texture": 0} for k, uv in faces.items()}}
    elements.append(e)
    g.enfants.append(e["uuid"])


def plaque(g, nom, c, w, h, uv, faces=("south",), ep=0.15):
    c = np.asarray(c, float)
    cube(g, nom, c - (w / 2, h / 2, ep / 2), c + (w / 2, h / 2, ep / 2), {f: uv for f in faces}, origin=c)


def poutre(g, nom, p, w, L, uv):
    """Trait en poutre carrée (w × L × w) : de p (tête, haut de l'image) vers −Y local sur L ; quatre faces longues."""
    p = np.asarray(p, float)
    cube(g, nom, p - (w / 2, L, w / 2), p + (w / 2, 0, w / 2), {f: uv for f in ("north", "south", "east", "west")}, origin=p)


EMIT = {}


def emit(sorte, pos, parent, rotation=None, nom=None):
    lst = EMIT.setdefault(sorte, [])
    n = nom or ("emit_" + sorte + (str(len(lst) + 1) if lst else ""))
    g = G(n, pos, parent, rotation=rotation)
    c = G("ctrl_emit", pos, g)
    lst.append((g, c))
    return g


EFFET = G("effet", (0, 0, 0))
JOUEUR = G("joueur", (0, 0, 0))
CENTRE = np.array((0.0, YC, ZD))

# --- la porte : PORTE_POS (déplacement depuis la main) > PORTE (échelle) > contenu
PORTE_POS = G("porte_pos", CENTRE, EFFET)
PORTE = G("porte", CENTRE, PORTE_POS)

# tube : un groupe par segment (pivot au milieu du segment, tourné dans le plan), âme opaque + gaine add_
TUBE = G("tube", CENTRE, PORTE)
GAINE = G("add_gaine", CENTRE, PORTE)
SEGS = []
for i in range(NSEG):
    phi = 90.0 + 360.0 * (i + 0.5) / NSEG          # depuis le haut, sens direct (vu de −Z : sens horaire)
    pr = math.radians(phi)
    p = CENTRE + (R * math.cos(pr), R * math.sin(pr), 0)
    ch_a = 2 * (R - W_AME / 2) * math.sin(math.pi / NSEG)
    ch_g = 2 * (R - W_GAINE / 2) * math.sin(math.pi / NSEG)      # sans recouvrement (stries claires en v2 brouillon)
    ga = G(f"seg{i}", p, TUBE, rotation=(0, 0, phi - 90))
    cube(ga, f"ame{i}", p - (ch_a / 2, W_AME / 2, W_AME / 2), p + (ch_a / 2, W_AME / 2, W_AME / 2),
         {"north": UV["ame"], "south": UV["ame"], "up": UV["ame"], "down": UV["ame"]}, origin=p)
    gg = G(f"gai{i}", p, GAINE, rotation=(0, 0, phi - 90))
    cube(gg, f"gai{i}", p - (ch_g / 2, W_GAINE / 2, W_GAINE / 2), p + (ch_g / 2, W_GAINE / 2, W_GAINE / 2),
         {"north": UV["gaine"], "south": UV["gaine"]}, origin=p)      # faces du dessus/dessous : échelons visibles de 3/4
    SEGS.append((ga, gg, (phi - 90.0) / 360.0))     # fraction du tour où la pointe le dépasse

HALO = G("add_halo", CENTRE, PORTE)
A_HALO = G("ctrl_alpha", CENTRE, HALO)
plaque(HALO, "halo", CENTRE + (0, 0, 0), 2 * HHALO, 2 * HHALO, UV["halo"], faces=("south", "north"), ep=0.3)
VOILE = G("add_voile", CENTRE, PORTE)
A_VOILE = G("ctrl_alpha", CENTRE, VOILE)
plaque(VOILE, "voile", CENTRE + (0, 0, 0.45), 2 * (R - 0.4), 2 * (R - 0.4), UV["voile"], faces=("south", "north"), ep=0.15)

# bord qui fourmille : 5 couronnes qui tournent à des vitesses différentes (°/s, signe = sens)
COURONNES = [(150, 80, 1), (-95, 70, 2), (230, 70, 3), (60, 70, 4), (-175, 70, 5)]
_rc = np.random.default_rng(9)
CRINS, PLAN = [], None
for k, (om, n, gr) in enumerate(COURONNES):
    cg = G(f"add_crin{k}", CENTRE, PORTE)
    if k == 0:
        PLAN = cg
    sg = 1 if om > 0 else -1
    for i in range(n):
        th = TAU * (i + _rc.uniform(-0.45, 0.45)) / n
        dedans = _rc.random() < 0.22
        incl = math.radians(_rc.uniform(25, 65))
        # direction de la queue : en arrière de la rotation, penchée dehors (ou dedans)
        ang = th - sg * TAU / 4 + (sg * incl if not dedans else -sg * incl)
        L = (1.0 + 3.0 * _rc.random() ** 1.6) if dedans else (1.4 + 9.0 * _rc.random() ** 1.8)
        r0 = R + (_rc.uniform(-0.9, -0.3) if dedans else _rc.uniform(-0.2, 0.9))
        z0 = ZD + _rc.uniform(-1.5, 1.5)
        p0 = np.array((r0 * math.cos(th), YC + r0 * math.sin(th), z0))
        a_deg = math.degrees(ang) + 90.0                 # −Y local = direction de la queue
        g = G(f"crin{k}_{i}", p0, cg, rotation=(_rc.uniform(-28, 28), 0, a_deg))
        w = _rc.uniform(0.3, 0.5)
        poutre(g, f"crin{k}_{i}", p0, w, L, UV["trait" if _rc.random() < 0.6 else "trait_or"])
        CRINS.append((g, _rc.uniform(5, 13), _rc.uniform(0, 360), _rc.uniform(0.35, 0.6)))
    CRINS_K = None
COUR_G = [g for g in PORTE.enfants if isinstance(g, G) and g.nom.startswith("add_crin")]

# gerbes tangentes : 8 foyers sur le bord, traits lancés le long de la tangente (sens de la couronne 0), gravité
GERBES = G("add_gerbes", CENTRE, PORTE)
_rg = np.random.default_rng(5)
FOYERS = [_rg.uniform(0, 360) for _ in range(8)]
GERB = []
for i in range(240):
    th = math.radians(FOYERS[i % 8] + _rg.uniform(-9, 9))
    p0 = np.array((R * math.cos(th), YC + R * math.sin(th), ZD + _rg.uniform(-0.8, 0.8)))
    alpha = th + TAU / 4 - math.radians(_rg.uniform(4, 38))     # tangente (sens direct) penchée dehors
    d = np.array((math.cos(alpha), math.sin(alpha)))
    g = G(f"gerbe{i}", p0, GERBES, rotation=(0, 0, math.degrees(alpha) - 90))
    L = _rg.uniform(3.0, 8.0)
    poutre(g, f"gerbe{i}", p0 + (0, 0, 0), _rg.uniform(0.35, 0.55), L, UV["trait"])
    # la poutre va de la tête (pivot) vers −Y local ; tournée de alpha − 90 : +Y local = d, la queue suit derrière
    GERB.append(dict(g=g, d=d, v=_rg.uniform(24, 48), grav=_rg.uniform(26, 50), P=_rg.uniform(0.35, 0.7), ph=_rg.random(),
                     vz=_rg.uniform(-5, 5)))

# pointe-comète qui trace la spirale (tourne autour du centre)
TRACE = G("trace", CENTRE, PORTE)
P_TOP = CENTRE + (0, R, 0)
CAM_P = G("cam_pointe", P_TOP, TRACE)
ADD_P = G("add_pointe", P_TOP, CAM_P)
plaque(ADD_P, "pointe", P_TOP + (0, 0, 0.6), 6.0, 6.0, UV["etoile"])
QUEUE = G("add_queue", P_TOP, TRACE)
_rq = np.random.default_rng(3)
for i in range(14):                                   # queue de comète : traits tangents vers l'arrière (−X au sommet)
    a_ = math.radians(180 + _rq.uniform(-25, 25))
    p0 = P_TOP + (0, 0, _rq.uniform(-0.8, 0.8))
    g = G(f"queue{i}", p0, QUEUE, rotation=(0, 0, math.degrees(a_) + 90))
    poutre(g, f"queue{i}", p0, 0.45, _rq.uniform(3, 9), UV["trait"])

# étincelles au sol : tombent du bas de l'anneau et rebondissent (repère de la porte, sans son échelle)
SOL = G("add_sol", (0, 0, ZD), PORTE_POS)
_rs = np.random.default_rng(13)
SOLS = []
for i in range(56):
    th = math.radians(_rs.uniform(228, 312))
    x0 = R * math.cos(th)
    y0 = YC + R * math.sin(th)
    p0 = np.array((x0, 0.0, ZD + _rs.uniform(-1.2, 1.2)))
    g = G(f"sol{i}", p0, SOL)
    w = _rs.uniform(0.35, 0.5)
    cube(g, f"sol{i}", p0 - (w / 2, 0, w / 2), p0 + (w / 2, w, w / 2),
         {f: UV["point"] for f in ("north", "south", "east", "west", "up")}, origin=p0)
    SOLS.append(dict(g=g, h=max(1.0, y0 - 0.2), vx=math.copysign(_rs.uniform(3, 11), x0 if abs(x0) > 2 else _rs.uniform(-1, 1)),
                     vz=_rs.uniform(-6, 6), P=_rs.uniform(1.0, 1.6), ph=_rs.random()))

# points d'émission : dans la couronne 0 (tournent avec le bord), +Y = tangente penchée dehors
for k in range(12):
    th = 360 * k / 12
    p = CENTRE + (R * math.cos(math.radians(th)), R * math.sin(math.radians(th)), 0)
    emit("etincelle", p, PLAN, rotation=(0, 0, th - 25))
for k in range(6):
    th = 360 * (k + 0.5) / 6
    p = CENTRE + (R * math.cos(math.radians(th)), R * math.sin(math.radians(th)), 0)
    emit("braise", p, PLAN, rotation=(0, 0, th - 40))
for k in range(4):
    th = 360 * (k + 0.25) / 4
    p = CENTRE + (R * math.cos(math.radians(th)), R * math.sin(math.radians(th)), 0)
    emit("mc_wax_on", p, PLAN, rotation=(0, 0, th - 30), nom="emit_mc_wax_on")
for k in range(2):
    th = 250 + 40 * k
    p = CENTRE + (R * math.cos(math.radians(th)), R * math.sin(math.radians(th)), 0)
    emit("mc_small_flame", p, PORTE, nom="emit_mc_small_flame")

# --- nœud d'étincelles (suit la porte, garde sa taille) et éclairs
NOEUD = G("noeud", CENTRE, PORTE_POS)
CAM_N = G("cam_noeud", CENTRE, NOEUD)
ADD_N = G("add_noeud", CENTRE, CAM_N)
plaque(ADD_N, "noeud", CENTRE + (0, 0, 0.3), 7.0, 7.0, UV["etoile"])
NOEUD_T = G("add_noeud_traits", CENTRE, NOEUD)
_rn = np.random.default_rng(21)
for i in range(18):                                   # crachotis du nœud : traits dans toutes les directions
    a_, b_ = _rn.uniform(0, 360), _rn.uniform(-60, 60)
    g = G(f"nt{i}", CENTRE, NOEUD_T, rotation=(b_, 0, a_))
    poutre(g, f"nt{i}", CENTRE + (0, _rn.uniform(3.5, 6.5), 0), 0.6, _rn.uniform(1.5, 3.5), UV["trait"])
ECLAT = G("eclat", (0, 16, ZD), EFFET)
CAM_E = G("cam_eclat", (0, 16, ZD), ECLAT)
ADD_E = G("add_eclat", (0, 16, ZD), CAM_E)
plaque(ADD_E, "eclat", (0, 16, ZD + 6.0), 34.0, 34.0, UV["flash"])

# --- sceaux des mains (charge)
MAINS = G("mains", (0, 0, 0), EFFET)
SCEAUX = {}
for cote, P in (("d", MAIN_D), ("g", MAIN_G)):
    m = G(f"main_{cote}", P, MAINS)
    cam = G(f"cam_sceau_{cote}", P, m)
    a_ = G(f"add_sceau_{cote}", P, cam)
    ext = G(f"sceau_ext_{cote}", P, a_)
    plaque(ext, f"runes_{cote}", (P[0], P[1], P[2] + 0.2), 2 * HSCEAU, 2 * HSCEAU, UV["sceau_a"])
    inte = G(f"sceau_int_{cote}", P, a_)
    plaque(inte, f"etoile8_{cote}", (P[0], P[1], P[2] + 0.45), 2 * HSCEAU * 0.6, 2 * HSCEAU * 0.6, UV["sceau_b"])
    pt = G(f"pointe_{cote}", P, a_)
    plaque(pt, f"plume_{cote}", (P[0] + HSCEAU * 0.92, P[1], P[2] + 0.7), 2.6, 2.6, UV["etoile"])
    inc = G(f"orbite_{cote}", P, m, rotation=(55, 0, 25 if cote == "d" else -25))
    tour = G(f"add_orbite_{cote}", P, inc)
    for k in range(3):
        gk = G(f"orb_{cote}{k}", P, tour, rotation=(0, 0, 120 * k))
        poutre(gk, f"orb_{cote}{k}", (P[0] + 6.0 + 0.3 * k, P[1] + 1.6, P[2] + 0.12 * k), 0.6, 3.2 - 0.4 * k, UV["trait"])
    emit("etincelle", P, m)
    for k in range(2):
        emit("glyphe", (P[0] + (1.2 if k else -1.2), P[1] + 1.6, P[2]), m)
    emit("mc_electric_spark", (P[0], P[1] + 0.5, P[2]), m, nom="emit_mc_electric_spark")
    SCEAUX[cote] = dict(m=m, ext=ext, int=inte, pt=pt, tour=tour, a=a_)

# --- particules (une plaque chacune ; groupes à la racine)
PART = {}
PART["etincelle"] = G("particle_etincelle", (0, 0, 0))
plaque(PART["etincelle"], "p_etincelle", (0, 1.6, 0), 0.6, 2.6, UV["p_eti"], ep=0.3)
PART["braise"] = G("particle_braise", (0, 0, 0))
plaque(PART["braise"], "p_braise", (0, 0.9, 0), 1.0, 1.0, UV["braise"], ep=0.3)
PART["glyphe"] = G("particle_glyphe", (0, 0, 0))
plaque(PART["glyphe"], "p_glyphe", (0, 1.2, 0), 1.6, 1.6, UV["glyphe"], ep=0.3)
outliner = [EFFET.json(), JOUEUR.json()] + [PART[k].json() for k in ("etincelle", "braise", "glyphe")]
NEMIT = sum(len(v) for v in EMIT.values())
assert NEMIT <= 32, NEMIT


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


def ease_in(t, a, b, p=2.0):
    return 0.0 if t <= a else 1.0 if t >= b else ((t - a) / (b - a)) ** p


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

    def son(self, t, nom):
        self.sons.append({"channel": "sound", "data_points": [{"effect": nom, "file": ""}], "time": round(t, 3)})
        self.A["effects"] = {"name": "Effects", "type": "effect", "keyframes": self.sons}

    def cadence(self, sorte, f):
        """ctrl_emit (x) de chaque point de la sorte : f(t, i) -> −1 (coupé) … +7."""
        for i, (g, c) in enumerate(EMIT[sorte]):
            self.piste(c, "position", lambda t, i=i: (max(-1.0, min(7.0, f(t, i))), 0, 0))

    def json(self):
        return {"uuid": nuid(), "name": self.nom, "loop": self.loop, "override": False, "length": self.L, "snapping": 30,
                "selected": self.nom == "depart", "animators": self.A}


uni = lambda v: (v, v, v)
Z3 = (0, 0, 0)
QT = "q.anim_time"


def f3(v):
    return f"{v:.3f}"


def m_env(a, da, b, db, sauts=()):
    """Enveloppe Molang : monte de a à a+da, tient, descend de b−db à b ; sauts = [(t, ampleur, demi-largeur)]."""
    e = f"math.clamp(({QT}-{f3(a)})/{f3(da)},0,1)*math.clamp(({f3(b)}-{QT})/{f3(db)},0,1)"
    for tc, amp, w in sauts:
        e += f"*(1+{f3(amp)}*math.clamp(1-math.abs({QT}-{f3(tc)})/{f3(w)},0,1))"
    return e


def m_u(P, ph):
    return f"math.mod({QT}/{f3(P)}+{f3(ph)},1)"


def cacher(an, groupes):
    for g in groupes:
        an.fixe(g, "scale", Z3)


def angle_cumule(L, omega, n=3000):
    ts = np.linspace(0, L, n + 1)
    a = np.concatenate([[0], np.cumsum([(omega(ts[i]) + omega(ts[i + 1])) / 2 * (ts[1] - ts[0]) for i in range(n)])])
    return lambda t: float(np.interp(t, ts, a))


def porte_anim(an, P):
    """P : dictionnaire des temps de la porte (T0, T1 tracé ; TC0, TC1 fermeture ; TP passage ; main : départ depuis la main ;
    env : enveloppe des étincelles (a, da, b, db) ; sauts)."""
    T0, T1, TC0, TC1, TP = P["T0"], P["T1"], P["TC0"], P["TC1"], P["TP"]
    main = np.array(P["main"], float) - CENTRE if P.get("main") is not None else np.zeros(3)
    # tracé : une seule courbe (départ et arrêt réels) ; 1,08 tour
    trace = lambda t: sm(t, T0, T1)
    # échelle : nœud minuscule, grandit en un seul élan pendant le tracé (léger dépassement), se resserre en accélérant
    def ech(t):
        if t < T0:
            return 0.12
        g = 0.12 + 0.88 * sm(t, T0, T1) + 0.035 * bump(t, T1 - 0.15, T1, T1, T1 + 0.35)
        return g * (1 - ease_in(t, TC0, TC1, 2.2))
    an.piste(PORTE_POS, "position", lambda t: tuple(main * (1 - sm(t, T0 - 0.05, T1 - 0.1))))
    an.piste(PORTE, "scale", lambda t: uni(ech(t)))
    # couronnes : vitesse propre, × 3 à la fermeture, × 2 pendant le tracé
    for g, (om, n, gr) in zip(COUR_G, COURONNES):
        f = lambda t, om=om: om * (1 + 1.0 * (1 - sm(t, T0, T1 + 0.3)) + 2.0 * sm(t, TC0, TC1))
        ang = angle_cumule(an.L, f)
        an.piste(g, "rotation", lambda t, ang=ang: (0, 0, ang(t)))
    ang_g = angle_cumule(an.L, lambda t: 70 + 200 * sm(t, TC0, TC1))
    an.piste(GERBES, "rotation", lambda t: (0, 0, ang_g(t)))
    # pointe : tourne de 1,08 tour pendant le tracé puis s'éteint
    an.piste(TRACE, "rotation", lambda t: (0, 0, -360 * 1.08 * trace(t)))
    an.piste(TRACE, "scale", lambda t: uni((0 if t < T0 - 0.05 else 1.0) * (1 - sm(t, T1, T1 + 0.25))))
    # segments du tube : chacun apparaît quand la pointe le dépasse (sens horaire vu de −Z, comme la pointe)
    ts = np.linspace(T0, T1, 2001)
    fr = np.array([1.08 * trace(t) for t in ts])
    for ga, gg, f in SEGS:
        fi = 1.0 - f                                   # la pointe tourne en sens négatif
        ti = float(np.interp(fi, fr, ts))
        e = f"math.clamp(({QT}-{f3(ti)})*25,0,1)"
        an.A.setdefault(ga.uuid, {"name": ga.nom, "type": "bone", "keyframes": []})["keyframes"].append(kf("scale", 0, e, e, e))
        an.A.setdefault(gg.uuid, {"name": gg.nom, "type": "bone", "keyframes": []})["keyframes"].append(kf("scale", 0, e, e, e))
    # voile : monte après le tracé, s'éclaire au passage, s'éteint avant la fermeture
    an.piste(A_VOILE, "position", lambda t: (-1 + 0.8 * sm(t, T1 - 0.1, T1 + 0.5) + 0.2 * bump(t, TP - 0.2, TP, TP + 0.05, TP + 0.5)
                                             - 0.8 * sm(t, TC0 - 0.15, TC0 + 0.2), 0, 0))
    an.piste(A_HALO, "position", lambda t: (-1 + sm(t, T1 - 0.15, T1 + 0.2), 0, 0))           # fondu (l'échelle changerait le rayon)
    # étincelles en Molang : palpitation des crins, gerbes, sol
    env = m_env(*P["env"], sauts=P["sauts"])
    crin_env = f"math.clamp(({QT}-{f3(T1 - 0.2)})/0.35,0,1)"     # jaillit quand l'anneau se ferme ; la porte se ferme par son échelle
    for g, fq, ph, amp in CRINS:
        an.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"].append(
            kf("scale", 0, 1, f"{crin_env}*({f3(1 - amp)}+{f3(amp)}*math.abs(math.sin({QT}*{f3(fq * 180)}+{f3(ph)})))", 1))
    for gb in GERB:
        u = m_u(gb["P"], gb["ph"])
        tt = f"({u}*{f3(gb['P'])})"
        vx, vy = gb["d"] * gb["v"]
        pos = (f"{f3(vx)}*{tt}", f"{f3(vy)}*{tt}-{f3(gb['grav'] / 2)}*{tt}*{tt}", f"{f3(gb['vz'])}*{tt}")
        sc = f"{env}*math.clamp({u}*8,0,1)*(1-{u})"
        an.A.setdefault(gb["g"].uuid, {"name": gb["g"].nom, "type": "bone", "keyframes": []})["keyframes"] += [
            kf("position", 0, *pos), kf("scale", 0, sc, sc, sc)]
    env_sol = m_env(P["env"][0] + 0.3, 0.4, P["fin_sol"], 0.6)
    for so in SOLS:
        u = m_u(so["P"], so["ph"])
        tt = f"({u}*{f3(so['P'])})"
        sb = f"({u}*2.6+0.5)"                         # rebonds : arcs de hauteur divisée par 2,4 à chaque contact
        y = f"0.3+{f3(so['h'])}*math.abs(math.cos({sb}*180-90))*math.pow(0.42,math.floor({sb}))"
        pos = (f"{f3(so['vx'])}*{tt}", y, f"{f3(so['vz'])}*{tt}")
        sc = f"{env_sol}*(1-{u}*0.8)"
        an.A.setdefault(so["g"].uuid, {"name": so["g"].nom, "type": "bone", "keyframes": []})["keyframes"] += [
            kf("position", 0, *pos), kf("scale", 0, sc, sc, sc)]
    an.fixe(SOL, "scale", (1, 1, 1))


def sceaux_off(an):
    for sc in SCEAUX.values():
        an.fixe(sc["m"], "scale", Z3)
        an.fixe(sc["m"], "position", Z3)


def joueur_passe(an, z, s, vers_centre=True):
    """Le joueur : z(t), échelle s(t) ; vers_centre : il se resserre vers le centre de son corps (y = 16 (1 − s)).
    Au départ, le mod 1.4.0 dessine la copie à sa taille et ne lit l'échelle que comme seuil (< 0,05 : cachée) : pas de
    décalage y, la copie traverse le plan à pleine taille et disparaît d'un coup sous l'éclair."""
    an.piste(JOUEUR, "position", lambda t: (0, 16.0 * (1 - s(t)) if vers_centre else 0.0, z(t)))
    an.piste(JOUEUR, "scale", lambda t: uni(s(t)))


# ---- charge (loop 3 s) : les sceaux se tracent autour des mains, le joueur lévite
LC = 3.0
ch = Anim("charge", LC, "loop")
LEVE = lambda t: 0.8 * (1 - math.cos(TAU * t / LC))
ch.piste(JOUEUR, "position", lambda t: (0, LEVE(t), 0))
ch.fixe(JOUEUR, "scale", (1, 1, 1))
ch.fixe(EFFET, "scale", (1, 1, 1))
cacher(ch, [PORTE_POS, ECLAT])
for cote, ph, sg in (("d", 0.0, 1), ("g", 0.5, -1)):
    sc = SCEAUX[cote]
    U = lambda t, ph=ph: (t / LC + ph) % 1.0
    ch.piste(sc["m"], "position", lambda t: (0, LEVE(t), 0))
    ch.fixe(sc["m"], "scale", (1, 1, 1))
    ch.piste(sc["ext"], "scale", lambda t, U=U: uni(sm(U(t), 0.0, 0.2) * (1 + 0.08 * math.sin(math.pi * sm(U(t), 0.12, 0.3)))
                                                     * (1 - sm(U(t), 0.84, 0.98))))
    ch.piste(sc["ext"], "rotation", lambda t, sg=sg: (0, 0, sg * 360 * t / LC))
    ch.piste(sc["int"], "scale", lambda t, U=U: uni(sm(U(t), 0.12, 0.34) * (1 - sm(U(t), 0.8, 0.95))))
    ch.piste(sc["int"], "rotation", lambda t, sg=sg: (0, 0, -sg * 360 * t / LC))
    ch.piste(sc["pt"], "rotation", lambda t, U=U, sg=sg: (0, 0, sg * 360 * sm(U(t), 0.0, 0.25)))
    ch.piste(sc["pt"], "scale", lambda t, U=U: uni(bump(U(t), 0.0, 0.03, 0.22, 0.27) * (U(t) < 0.5)))
    ch.piste(sc["tour"], "rotation", lambda t, sg=sg: (0, 0, sg * 720 * t / LC))
    ch.piste(sc["tour"], "scale", lambda t, U=U: uni(0.3 + 0.7 * bump(U(t), 0.05, 0.25, 0.75, 0.95)))
CH_U = lambda t, i: (t / LC + (0.0 if i == 0 else 0.5)) % 1.0
ch.cadence("glyphe", lambda t, i: -1 + 3 * bump(CH_U(t, i // 2), 0.2, 0.3, 0.75, 0.85))
ch.cadence("etincelle", lambda t, i: -1 if i < 12 else -0.5 + 4 * bump(CH_U(t, i - 12), 0.0, 0.03, 0.2, 0.3)
           + 3 * bump(CH_U(t, i - 12), 0.82, 0.88, 0.95, 0.99))
ch.cadence("mc_electric_spark", lambda t, i: -1 + 3 * bump(CH_U(t, i), 0.0, 0.04, 0.16, 0.24))
for so in ("braise", "mc_wax_on", "mc_small_flame"):
    ch.cadence(so, lambda t, i: -1)

# ---- depart (once 4,6 s)
LD = 4.6
PD = dict(T0=0.45, T1=1.3, TP=2.45, TC0=3.2, TC1=3.75, main=MAIN_D, fin_sol=4.5)
PD["env"] = (PD["T1"] - 0.15, 0.3, PD["TC1"] + 0.1, 0.35)
PD["sauts"] = [(PD["TP"], 0.9, 0.3), (PD["TC0"] + 0.35, 0.7, 0.3)]
de = Anim("depart", LD, "once")
porte_anim(de, PD)
de.piste(NOEUD, "scale", lambda t: uni(bump(t, 0.05, 0.2, PD["T0"] + 0.05, PD["T0"] + 0.4) * (1 + 0.2 * math.sin(TAU * t * 6))
                                       + 0.7 * bump(t, PD["TC1"] - 0.08, PD["TC1"], PD["TC1"] + 0.05, PD["TC1"] + 0.45)))
de.piste(NOEUD_T, "rotation", lambda t: (0, 0, 400 * t))
de.piste(ECLAT, "scale", lambda t: uni(bump(t, PD["TP"] - 0.1, PD["TP"] + 0.02, PD["TP"] + 0.06, PD["TP"] + 0.4)))
de.fixe(ECLAT, "position", Z3)
# le joueur : un seul élan (part du repos, accélère), son centre atteint le plan au pic de l'éclair, sans s'arrêter
_TW0 = 1.75
_v_plan = 2 * ZD / (PD["TP"] - _TW0)                       # vitesse au plan (élan quadratique)
def ZJ_D(t):
    if t <= _TW0:
        return 0.0
    if t <= PD["TP"]:
        return ZD * ((t - _TW0) / (PD["TP"] - _TW0)) ** 2
    return ZD + _v_plan * (t - PD["TP"])
# échelle monotone 1 → 0 en 0,07 s quand le centre du corps passe le plan (au pic de l'éclair)
SJ_D = lambda t: 1.0 - sm(t, PD["TP"] - 0.02, PD["TP"] + 0.05)
joueur_passe(de, lambda t: ZJ_D(min(t, PD["TP"] + 0.12)), SJ_D, vers_centre=False)
for cote, sc in SCEAUX.items():
    de.fixe(sc["m"], "position", Z3)
    de.piste(sc["m"], "scale", (lambda t: uni((1 + 0.3 * sm(t, 0.0, 0.12)) * (1 - sm(t, 0.12, 0.4)))) if cote == "d"
             else (lambda t: uni(1 - sm(t, 0.0, 0.3))))
    de.fixe(sc["ext"], "scale", (1, 1, 1))
    de.fixe(sc["int"], "scale", (1, 1, 1))
    de.piste(sc["ext"], "rotation", lambda t: (0, 0, 360 * t))
    de.piste(sc["int"], "rotation", lambda t: (0, 0, -540 * t))
    de.fixe(sc["pt"], "scale", Z3)
    de.fixe(sc["tour"], "scale", (1, 1, 1))
    de.piste(sc["tour"], "rotation", lambda t: (0, 0, 720 * t))
de.fixe(EFFET, "scale", (1, 1, 1))
de.piste(EFFET, "scale", lambda t: uni(1.0 if t < LD - 0.04 else 0.0), T=[0, round(LD - 0.05, 4), LD])
TPD, TFD = PD["TP"], PD["TC1"]
de.cadence("etincelle", lambda t, i: ((-1 + 6 * bump(t, 0.08, 0.15, 0.4, 0.6)) if i == 12 else -1) if i >= 12 else
           (-1 if t < PD["T0"] or t > TFD + 0.05 else 1 + 3 * bump(t, PD["T0"], PD["T0"] + 0.2, PD["T1"], PD["T1"] + 0.3)
            + 6 * bump(t, TPD - 0.1, TPD, TPD + 0.1, TPD + 0.35) + 6 * bump(t, PD["TC0"], PD["TC0"] + 0.15, TFD - 0.1, TFD)))
de.cadence("braise", lambda t, i: -1 if t < PD["T1"] or t > TFD + 0.05 else 1 + 5 * bump(t, PD["TC0"], PD["TC0"] + 0.15, TFD - 0.1, TFD))
de.cadence("mc_wax_on", lambda t, i: -1 if t < PD["T0"] + 0.2 or t > TFD else 2 + 3 * bump(t, TPD - 0.1, TPD, TPD + 0.1, TPD + 0.3))
de.cadence("mc_small_flame", lambda t, i: -1 if t < PD["T1"] or t > PD["TC0"] + 0.2 else 1)
de.cadence("mc_electric_spark", lambda t, i: (-1 + 4 * bump(t, 0.05, 0.1, 0.4, 0.55)) if i == 0 else -1)
de.cadence("glyphe", lambda t, i: (-1 + 3 * bump(t, 0.0, 0.05, 0.2, 0.3)) if i < 2 else -1)
de.son(PD["T0"] - 0.1, "etincelles_ouverture")
de.son(TPD - 0.3, "etincelles_passage")
de.son(PD["TC0"] - 0.1, "etincelles_extinction")

# ---- arrivee (once 4,3 s) : la porte se trace dans le dos, le joueur en sort en grandissant puis ralentit
LA = 4.3
PA = dict(T0=0.15, T1=0.95, TP=1.35, TC0=2.75, TC1=3.3, main=None, fin_sol=4.2)
PA["env"] = (PA["T1"] - 0.15, 0.3, PA["TC1"] + 0.1, 0.35)
PA["sauts"] = [(PA["TP"], 0.9, 0.3), (PA["TC0"] + 0.35, 0.7, 0.3)]
ar = Anim("arrivee", LA, "once")
porte_anim(ar, PA)
ar.fixe(PORTE_POS, "position", (0, 0, ZA - ZD))       # remplace la piste du départ depuis la main
ar.A[PORTE_POS.uuid]["keyframes"] = [k for k in ar.A[PORTE_POS.uuid]["keyframes"] if k["time"] == 0][-1:]
ar.piste(NOEUD, "scale", lambda t: uni(bump(t, 0.0, 0.08, PA["T0"] + 0.05, PA["T0"] + 0.35) * (1 + 0.2 * math.sin(TAU * t * 6))
                                       + 0.7 * bump(t, PA["TC1"] - 0.08, PA["TC1"], PA["TC1"] + 0.05, PA["TC1"] + 0.45)))
ar.piste(NOEUD_T, "rotation", lambda t: (0, 0, 400 * t))
ar.piste(ECLAT, "scale", lambda t: uni(bump(t, PA["TP"] - 0.06, PA["TP"], PA["TP"] + 0.03, PA["TP"] + 0.35) * 0.9))
ar.fixe(ECLAT, "position", (0, 0, ZA - ZD))
_TS = 2.35                                             # le joueur s'arrête à sa place
def ZJ_A(t):
    if t <= PA["TP"] - 0.05:
        return ZA + 1.0
    u = min(1.0, (t - (PA["TP"] - 0.05)) / (_TS - PA["TP"] + 0.05))
    return (ZA + 1.0) * (1 - (1 - (1 - u) ** 2.4))     # sort lancé, ralentit jusqu'à l'arrêt (ease-out)
SJ_A = lambda t: 0.0 if t < PA["TP"] - 0.05 else smooth((ZA + 1.0 - ZJ_A(t)) / 4.2)
joueur_passe(ar, ZJ_A, SJ_A)
sceaux_off(ar)
ar.fixe(EFFET, "scale", (1, 1, 1))
ar.piste(EFFET, "scale", lambda t: uni(1.0 if t < LA - 0.04 else 0.0), T=[0, round(LA - 0.05, 4), LA])
TPA, TFA = PA["TP"], PA["TC1"]
ar.cadence("etincelle", lambda t, i: -1 if i >= 12 or t < PA["T0"] or t > TFA + 0.05 else
           1 + 3 * bump(t, PA["T0"], PA["T0"] + 0.2, PA["T1"], PA["T1"] + 0.3) + 6 * bump(t, TPA - 0.1, TPA, TPA + 0.1, TPA + 0.35)
           + 6 * bump(t, PA["TC0"], PA["TC0"] + 0.15, TFA - 0.1, TFA))
ar.cadence("braise", lambda t, i: -1 if t < PA["T1"] - 0.3 or t > TFA + 0.05 else 1 + 4 * bump(t, TPA, TPA + 0.2, 2.0, 2.3)
           + 4 * bump(t, PA["TC0"], PA["TC0"] + 0.15, TFA - 0.1, TFA))
ar.cadence("mc_wax_on", lambda t, i: -1 if t < PA["T0"] + 0.15 or t > TFA else 2 + 3 * bump(t, TPA - 0.2, TPA, 1.9, 2.3))
ar.cadence("mc_small_flame", lambda t, i: -1 if t < PA["T1"] or t > PA["TC0"] + 0.2 else 1)
ar.cadence("mc_electric_spark", lambda t, i: -1)
ar.cadence("glyphe", lambda t, i: -1)
ar.son(0.05, "etincelles_ouverture")
ar.son(TPA - 0.3, "etincelles_passage")
ar.son(PA["TC0"] - 0.1, "etincelles_extinction")


# ---- particules
def part_anim(sorte, L, ch_, f, n=12):
    a = Anim(f"particle_{sorte}_fall", L, "loop")
    a.piste(PART[sorte], ch_, f, T=[round(i * L / n, 4) for i in range(n + 1)])
    return a


pe = part_anim("etincelle", 0.3, "scale", lambda t: uni(1 + 0.3 * math.sin(TAU * t / 0.3)), n=8)
pb = part_anim("braise", 0.8, "scale", lambda t: uni(1 + 0.25 * math.sin(TAU * t / 0.8)), n=8)
pg = part_anim("glyphe", 1.5, "rotation", lambda t: (0, 360 * t / 1.5, 0), n=12)

ANIMS = [ch.json(), de.json(), ar.json(), pe.json(), pb.json(), pg.json()]
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures,
         "animations": ANIMS}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
embarquer_sons(model, {n: f"sons/{n}.ogg" for n in ("etincelles_ouverture", "etincelles_passage", "etincelles_extinction")})
limiter_sons(model, max_effet=3)

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
