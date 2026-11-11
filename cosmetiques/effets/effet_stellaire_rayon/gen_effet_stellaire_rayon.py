"""Effet de téléportation « Rayon de téléportation » (guide 15), ensemble Stellaire. Design original, fiche de référence
.claude/references/effets/rayon-teleportation.md (déroulé, formes, couleurs échantillonnées, timing, sons).
Écrit effet_stellaire_rayon.png, effet_stellaire_rayon_e.png et .build/effet_stellaire_rayon_brut.bbmodel.

v1 (2026-11-07) :
- **Colonne de lumière** de 18 blocs (288 px) qui **tombe du ciel** en 0,35 s (échelle y depuis son sommet, tête lumineuse
  cam_ qui descend), impact au sol (éclat, onde, cercle de lumière). Trois coques add_ concentriques à facettes (rayons 4,5 /
  8,5 / 13 px, faces extérieures seules) : un palier de lumière par couche, cœur clair (cumul de nuit ≤ 255), bord bleu net ;
  gaine trans_ bleutée (lisible de jour). Stries verticales (poutres pleines en travers) qui défilent en Molang, anneaux de
  lumière (40 segments) qui descendent le long du faisceau.
- **Silhouette de lumière** en géométrie : enveloppe add_ bleue en 17 tranches horizontales + 400 éclats sur la peau. Forme
  de **révolution** (jambes, épaules, tête) : la copie et le joueur gardent leur propre lacet (cause supposée,
  categories/effets.md), une silhouette en boîtes serait de biais dès qu'il tourne.
- Départ : la silhouette s'allume depuis le torse, la copie s'élève de 1,5 px puis est cachée (échelle < 0,05, le mod ignore
  son échelle au départ) au plus vif ; la silhouette se défait de bas en haut, ses éclats montent dans le faisceau ; le
  faisceau s'éteint d'un coup (resserrement en 0,12 s).
- Arrivée : les éclats descendent dans le faisceau et se posent de bas en haut, l'enveloppe se remplit, le joueur apparaît à
  sa taille au plus vif (échelle 0 → 1), descend de 1,5 px jusqu'au sol pendant que la silhouette s'efface de haut en bas.
- Charge : légère lueur de l'enveloppe, petits scintillements qui montent (stries écrasées), anneaux qui montent, cercle au
  sol, le joueur s'élève de 0,6 px.
v2 (2026-11-07, retour en jeu 18.23–18.24 : « beaucoup moins de visuel qu'au Vestiaire ») ; v1 dans .build/gen_v1.py.
- **Cause mesurée** (bytecode 1.4.0 : passes OPAQUE, TRANSLUCENT, ADDITIVE ; trans_ = entityTranslucent qui écrit la
  profondeur, add_ testé contre elle) : la gaine trans_ de v1 (rayon 13,6) entourait coques, stries, silhouette, éclats et
  points d'émission ; sa face avant cachait tout ce qui était add_ derrière elle, et les particules aussi. Restaient la gaine
  pâle, les anneaux (rayon 14,6) et le cercle au sol : exactement les captures. Le renderer ne l'écrivait pas (corrigé).
- Gaine retirée ; âme trans_ fine (rayon 2,4, alpha ≤ 150, calque _e) au centre ; coques add_ 2 à 3 fois plus vives (le
  faisceau sature en blanc sur un ciel gris clair, bord bleu de nuit) ; creux du faisceau à 25 % pendant la silhouette.
- Silhouette doublée en trans_ (bleu, contour de 0,7 px, _e) sous la lueur add_ : lisible sur un faisceau saturé ;
  260 éclats de 0,5 à 0,8 px (au lieu de 380 de 0,25 à 0,45) ; stries de 0,55 à 0,85 px, plus claires.
Mouvements : une courbe lisse par phase, 30 clés/s ; mouvements périodiques et éclats en Molang (continus en jeu).

Particules (guide 5 ter ; cadence animée par ctrl_emit) : eclat (carré de lumière 0,6 px qui monte), strie (trait 0,35 ×
3 px qui monte vite), emit_mc_electric_spark, emit_mc_firework, emit_mc_dust_b4c8ff_10. Pas d'end_rod.
Sons embarqués originaux (sons/) : stellaire_rayon_eclair (chute et impact), stellaire_rayon_montee (charge de la silhouette),
stellaire_rayon_extinction ; rien pendant la charge.
Sons v2 (2026-11-07, « plus proches de la vraie série ») : resynthétisés au caractère mesuré d'un faisceau de transport
(whoomp grave + nappe grésillante à partiels fixes, zip descendant 16 → 2,5 kHz au sommet, traîne 2–7 kHz ; fiche de
référence, Sons) ; briques dans sons/_faisceau.py, v1 dans sons/v1/. Instants des clés inchangés.

Fonctions : add_, trans_, cam_, ctrl_alpha, ctrl_emit, particle_/emit_, emit_mc_, Molang (q.anim_time, math.mod,
math.clamp, math.sin), groupe joueur, sons embarqués. À juger en jeu : éclat du faisceau de jour, cumul additif, âme et
silhouette trans_ qui cachent les add_ derrière elles, copie cachée au bon instant, Molang des éclats, particules.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "effet_stellaire_rayon"
TEX = 512
TAU = 2 * math.pi
FPS = 30
rng = np.random.default_rng(7)

# ------------------------------------------------------------------ dimensions (px)
H = 288.0                                  # hauteur de la colonne (18 blocs)
COQUES = [  # (nom, rayon, facettes, couleur par face (cumul de deux faces = palier))
    ("halo", 13.0, 28, (34, 52, 120)),
    ("milieu", 8.5, 22, (46, 58, 96)),
    ("coeur", 4.5, 14, (80, 88, 100)),
]
R_COEUR_T = 2.4                            # âme trans_ (v2) : petite, au centre ; une face trans_ cache tout add_ derrière elle
R_ANN = 14.6
N_ANN = 40
LEVE = 1.5                                 # la copie / le joueur s'élève de 1,5 px dans le faisceau



# ------------------------------------------------------------------ textures
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
_lib = {"x": 0, "y": 0, "h": 0}


def poser(nom, im):
    """Range im dans l'atlas (lignes de gauche à droite)."""
    h, w = im.shape[:2]
    if _lib["x"] + w > TEX:
        _lib["x"], _lib["y"], _lib["h"] = 0, _lib["y"] + _lib["h"] + 2, 0
    x, y = _lib["x"], _lib["y"]
    assert y + h <= TEX - 4, nom
    tex[y:y + h, x:x + w] = im
    UV[nom] = (x, y, x + w, y + h)
    _lib["x"] += w + 2
    _lib["h"] = max(_lib["h"], h)


def rgba(rgb, a=255):
    rgb = np.clip(np.asarray(rgb, float), 0, 255).astype(np.uint8)
    out = np.zeros(rgb.shape[:-1] + (4,), np.uint8)
    out[..., :3] = rgb
    lum = rgb.max(-1)
    out[..., 3] = np.where(lum > 3, a, 0)
    out[lum <= 3, :3] = 0
    return out


def uni(col, w=4, h=4):
    return rgba(np.tile(np.asarray(col, float), (h, w, 1)))


# 1. coques : profil vertical (haut de l'image = haut de la colonne), plein en travers
yv = (np.arange(256) + 0.5) / 256                    # 0 = haut, 1 = sol
prof_col = (0.62 + 0.38 * yv ** 1.5) * np.clip((yv - 0.0) / 0.18, 0, 1) ** 0.8 * (0.25 + 0.75 * np.clip(yv / 0.18, 0, 1))
prof_col = np.clip(prof_col * (1 + 0.04 * np.sin(yv * 61) + 0.03 * np.sin(yv * 137)), 0, 1)
for nom, r, n, col in COQUES:
    poser("coque_" + nom, rgba(prof_col[:, None, None] * np.asarray(col, float)[None, None, :] * np.ones((1, 4, 1))))
# 2. âme trans_ (v2, remplace la gaine de v1 qui entourait tout et cachait les add_ en jeu) : blanc bleuté, alpha ≤ 150
ame = np.zeros((256, 4, 4), np.uint8)
ame[..., :3] = (226, 236, 255)
ame[..., 3] = (np.clip(prof_col / prof_col.max(), 0, 1) * 150)[:, None].astype(np.uint8)
poser("ame", ame)
# 3. anneau (segment plein)
poser("anneau", uni((96, 118, 182)))
# 4. strie : profil le long (clair au milieu, s'éteint aux deux bouts), plein en travers
ys = (np.arange(48) + 0.5) / 48
f = np.sin(np.pi * ys) ** 1.2
poser("strie", rgba(f[:, None, None] * np.array([150, 175, 235])[None, None, :] * np.ones((1, 4, 1))))


def radial(N, fn, col):
    c = (np.arange(N) + 0.5) / N * 2 - 1
    x, y = np.meshgrid(c, c)
    rr = np.hypot(x, y)
    v = np.clip(fn(rr), 0, 1)
    rgb = v[..., None] * np.asarray(col, float)
    return rgba(rgb)


# 5. tête de colonne et éclats (cam_) : lueur ronde, cœur blanc froid, bord bleu
poser("lueur", radial(64, lambda r: np.exp(-(r / 0.45) ** 2) * (r < 1), (230, 236, 255)))
# 6. sol : disque de lumière + anneau au rayon de la colonne (13 / 24)
poser("sol", radial(128, lambda r: (0.55 * np.exp(-(r / 0.5) ** 2) + 0.9 * np.exp(-((r - 0.56) / 0.07) ** 2)) * (r < 0.98)
                     * np.clip((0.98 - r) / 0.08, 0, 1), (70, 92, 160)))
# 7. onde de choc au sol (anneau large, ≥ 8 texels)
poser("onde", radial(128, lambda r: np.exp(-((r - 0.84) / 0.07) ** 2) * (r < 0.99), (120, 140, 210)))
# 8. enveloppe et éclats de la silhouette
def dans_corps(x, y, marge=0.0):
    """Silhouette de face (Steve) : tête, torse, bras, jambes ; marge > 0 = un peu à l'intérieur."""
    rects = [(-4, 24, 4, 32), (-4, 12, 4, 24), (4, 12, 8, 24), (-8, 12, -4, 24), (-4, 0, 4, 12)]
    return any(x0 + marge <= x <= x1 - marge and y0 + marge <= y <= y1 - marge for x0, y0, x1, y1 in rects)


def dist_corps(X, Y):
    """Distance (px) au corps de face, 0 dedans (rectangles réunis)."""
    rects = [(-4, 24, 4, 32), (-4, 12, 4, 24), (4, 12, 8, 24), (-8, 12, -4, 24), (-4, 0, 4, 12)]
    d = np.full(X.shape, 1e9)
    for x0, y0, x1, y1 in rects:
        dx = np.maximum(np.maximum(x0 - X, X - x1), 0)
        dy = np.maximum(np.maximum(y0 - Y, Y - y1), 0)
        d = np.minimum(d, np.hypot(dx, dy))
    return d


def prof_corps(X, Y):
    """Profondeur (px) à l'intérieur du corps : distance au bord, approchée par décalages."""
    dedans = dist_corps(X, Y) == 0
    out = np.zeros(X.shape)
    for e in np.linspace(0.08, 1.2, 15):
        ok = dedans.copy()
        for dx, dy in ((e, 0), (-e, 0), (0, e), (0, -e)):
            ok &= dist_corps(X + dx, Y + dy) == 0
        out += ok * (1.2 / 15)
    return out


# silhouette : 22 × 36 px, 4 texels/px, sur-échantillonnée × 3 ; cœur clair à stries verticales, bord intérieur plus blanc,
# liseré bleu dehors (couleurs de la fiche de référence)
SIL_W, SIL_H, SIL_RES, ZF = 22, 36, 4, 5.0
_n = 3
xs_ = (np.arange(SIL_W * SIL_RES * _n) + 0.5) / (SIL_RES * _n) - SIL_W / 2
ys_ = SIL_H - (np.arange(SIL_H * SIL_RES * _n) + 0.5) / (SIL_RES * _n)
XX, YY = np.meshgrid(xs_, ys_)
dd = dist_corps(XX, YY)
pr = prof_corps(XX, YY)
strie = 0.82 + 0.18 * np.cos(XX * TAU / 1.6 + 0.6 * np.sin(XX * 3.1))
fill = (dd == 0) * (0.62 + 0.38 * np.exp(-(pr / 0.45) ** 2)) * np.where(pr > 0.4, strie, 1.0)
rim = (dd > 0) * np.exp(-(dd / 1.1) ** 2)
rgb = fill[..., None] * np.array([28, 34, 62]) + rim[..., None] * np.array([70, 100, 225])
sil = np.array(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").resize((SIL_W * SIL_RES, SIL_H * SIL_RES), Image.LANCZOS)).astype(float)
poser("silhouette", rgba(sil))
# v2 : silhouette trans_ (lisible de jour sur un faisceau saturé) : remplissage bleu pâle, contour bleu franc de 0,7 px
bord = (dd == 0) & (pr < 0.7)
coul = np.where(bord[..., None], np.array([36, 64, 196]), np.array([70, 112, 238]))
alp = np.where(dd == 0, np.where(bord, 240, 190), 0)
st = np.dstack([coul, alp]).astype(np.uint8)
st = np.array(Image.fromarray(st, "RGBA").resize((SIL_W * SIL_RES, SIL_H * SIL_RES), Image.NEAREST))
poser("silhouette_t", st)
TONS = [(150, 185, 255), (100, 140, 245), (225, 235, 255)]
for k, c in enumerate(TONS):
    poser(f"eclat{k}", uni(c))
# 9. particules modélisées
poser("p_eclat", uni((200, 214, 245)))
poser("p_strie", rgba(np.sin(np.pi * ((np.arange(16) + 0.5) / 16))[:, None, None] * np.array([190, 205, 240])[None, None, :]
                      * np.ones((1, 4, 1))))

# calque _e (v2) : l'âme et la silhouette trans_ éclairées de nuit (alpha 0/255, intensité dans la couleur)
tex_e = np.zeros_like(tex)
for nom_, k_ in (("ame", 0.8), ("silhouette_t", 0.7)):
    x0_, y0_, x1_, y1_ = UV[nom_]
    r_ = tex[y0_:y1_, x0_:x1_].astype(float)
    v_ = r_[..., :3] * (r_[..., 3:4] / 255.0) * k_ * 1.6
    tex_e[y0_:y1_, x0_:x1_, :3] = np.clip(v_, 0, 255).astype(np.uint8)
    tex_e[y0_:y1_, x0_:x1_, 3] = np.where(r_[..., 3] > 25, 255, 0)


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
            d["rotation"] = [round(float(v), 4) for v in self.rotation]
        return d


elements = []


def cube(g, nom, a, b, faces, origin=None, rotation=None):
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in a], "to": [round(float(v), 4) for v in b],
         "origin": [round(float(v), 4) for v in (origin if origin is not None else (np.add(a, b) / 2))], "box_uv": False,
         "faces": {k: {"uv": [round(float(v), 3) for v in uv], "texture": 0} for k, uv in faces.items()}}
    if rotation is not None and any(abs(v) > 1e-6 for v in rotation):
        e["rotation"] = [round(float((v + 180) % 360 - 180), 3) for v in rotation]
    elements.append(e)
    g.enfants.append(e["uuid"])


def facette(g, nom, r, n, k, y0, y1, uv, ep=0.15, faces=("south",)):
    """Plaque k d'un prisme de n facettes de rayon r (sommets), entre y0 et y1 ; face sud tournée vers l'extérieur."""
    apo, w = r * math.cos(math.pi / n), 2 * r * math.sin(math.pi / n)
    ang = 360.0 * k / n
    cube(g, nom, (-w / 2, y0, apo - ep), (w / 2, y1, apo), {f_: uv for f_ in faces}, origin=(0, y0, 0), rotation=(0, ang, 0))


def plaque(g, nom, c, w, h, uv, faces=("south",), ep=0.15):
    c = np.asarray(c, float)
    cube(g, nom, c - (w / 2, h / 2, ep / 2), c + (w / 2, h / 2, ep / 2), {f_: uv for f_ in faces}, origin=c)


def sol_plaque(g, nom, y, demi, uv, ep=0.15):
    cube(g, nom, (-demi, y - ep, -demi), (demi, y, demi), {"up": uv}, origin=(0, y, 0))


TOUT6 = ("north", "south", "east", "west", "up", "down")
LONG4 = ("north", "south", "east", "west")

EMIT = {}


def emit(sorte, pos, parent, nom=None):
    lst = EMIT.setdefault(sorte, [])
    n = nom or ("emit_" + sorte + (str(len(lst) + 1) if lst else ""))
    g = G(n, pos, parent)
    c = G("ctrl_emit", pos, g)
    lst.append((g, c))
    return g


EFFET = G("effet", (0, 0, 0))
JOUEUR = G("joueur", (0, 0, 0))

# --- colonne : pivot au sommet (échelle y = chute), coques add_ + gaine trans_
COL = G("colonne", (0, H, 0), EFFET)
COQ = G("add_coques", (0, H, 0), COL)
A_COQ = G("ctrl_alpha", (0, H, 0), COQ)
for nom, r, n, col in COQUES:
    for k in range(n):
        facette(COQ, f"{nom}_{k}", r, n, k + (0.5 if nom == "milieu" else 0.0), 0.0, H, UV["coque_" + nom])
AME = G("trans_ame", (0, H, 0), COL)
A_AME = G("ctrl_alpha", (0, H, 0), AME)
for k in range(12):
    facette(AME, f"ame_{k}", R_COEUR_T, 12, k + 0.5, 0.0, H, UV["ame"])

# --- tête de colonne (cam_), qui descend avec le bas du faisceau puis devient l'éclat d'impact
TETE = G("tete", (0, H, 0), EFFET)
CAM_T = G("cam_tete", (0, H, 0), TETE)
ADD_T = G("add_tete", (0, H, 0), CAM_T)
plaque(ADD_T, "tete", (0, H, 0), 34, 34, UV["lueur"])

# --- éclat du corps (cam_), au moment où la copie disparaît / le joueur apparaît
FLASH = G("flash", (0, 17, 0), EFFET)
CAM_F = G("cam_flash", (0, 17, 0), FLASH)
ADD_F = G("add_flash", (0, 17, 0), CAM_F)
plaque(ADD_F, "flash", (0, 17, 0), 30, 44, UV["lueur"])

# --- stries verticales (poutres pleines), défilent en Molang
STRIES = G("stries", (0, 0, 0), EFFET)
ADD_S = G("add_stries", (0, 0, 0), STRIES)
A_STR = G("ctrl_alpha", (0, 0, 0), ADD_S)
STR = []
for k in range(84):
    rr = math.sqrt(rng.uniform(0.1, 1.0)) * 12.4
    a = rng.uniform(0, TAU)
    x, z = rr * math.cos(a), rr * math.sin(a)
    L = rng.uniform(10, 36)
    w = rng.uniform(0.55, 0.85)
    g = G(f"strie_{k}", (x, 0, z), ADD_S)
    cube(g, "s", (x - w / 2, 0, z - w / 2), (x + w / 2, L, z + w / 2), {f_: UV["strie"] for f_ in LONG4}, origin=(x, 0, z))
    STR.append(dict(g=g, L=L, v=rng.uniform(0.7, 1.5), ph=rng.uniform(0, 1)))

# --- anneaux qui défilent le long du faisceau
ANN_G = G("anneaux", (0, 0, 0), EFFET)
ADD_A = G("add_anneaux", (0, 0, 0), ANN_G)
ANN = []
for j in range(4):
    g = G(f"anneau_{j}", (0, 0, 0), ADD_A)
    ca = G("ctrl_alpha", (0, 0, 0), g)
    w = 0.7
    ch = 2 * R_ANN * math.sin(math.pi / N_ANN)
    for k in range(N_ANN):
        ang = 360.0 * (k + 0.25 * j) / N_ANN
        cube(g, f"a{j}_{k}", (-ch / 2, -w / 2, R_ANN - w / 2), (ch / 2, w / 2, R_ANN + w / 2), {f_: UV["anneau"] for f_ in TOUT6},
             origin=(0, 0, 0), rotation=(0, ang, 0))
    ANN.append(dict(g=g, a=ca))

# --- sol : cercle de lumière et onde de choc
SOL = G("add_sol", (0, 0, 0), EFFET)
A_SOL = G("ctrl_alpha", (0, 0, 0), SOL)
sol_plaque(SOL, "sol", 0.32, 24.0, UV["sol"])
ONDE = G("add_onde", (0, 0, 0), EFFET)
A_ONDE = G("ctrl_alpha", (0, 0, 0), ONDE)
sol_plaque(ONDE, "onde", 0.5, 22.0, UV["onde"])

# --- silhouette de lumière (suit l'élévation du joueur) : camy_ (toujours de face, debout), avancée de ZF px vers la
# caméra pour passer devant la copie ; la copie et le joueur gardent leur propre lacet (cause supposée), une silhouette fixe
# serait de biais dès qu'il tourne ; une forme de révolution se lisait comme une boîte de conserve (rendu du 2026-11-07).
CORPS = G("corps", (0, 0, 0), EFFET)
CAMS = G("camy_silhouette", (0, 0, 0), CORPS)
ENV = G("add_enveloppe", (0, 0, 0), CAMS)
TR = []
x0u, y0v, x1u, y1v = UV["silhouette"]
for i in range(SIL_H // 2):
    y0, y1 = 2.0 * i, 2.0 * i + 2.0
    yc = (y0 + y1) / 2
    g = G(f"tranche_{i}", (0, yc, ZF), ENV)
    uv = (x0u, y0v + (SIL_H - y1) * SIL_RES, x1u, y0v + (SIL_H - y0) * SIL_RES)
    cube(g, f"t{i}", (-SIL_W / 2, y0, ZF - 0.15), (SIL_W / 2, y1, ZF), {"south": uv}, origin=(0, yc, ZF))
    TR.append(dict(g=g, y=yc, a=G("ctrl_alpha", (0, yc, ZF), g)))      # fondu par tranche (pas de bandes)
# v2 : même silhouette en trans_, 0,25 px derrière la lueur add_ (elle cache les add_ du faisceau derrière elle : contraste)
SILT = G("trans_silhouette", (0, 0, 0), CAMS)
x0u, y0v, x1u, y1v = UV["silhouette_t"]
for i in range(SIL_H // 2):
    y0, y1 = 2.0 * i, 2.0 * i + 2.0
    yc = (y0 + y1) / 2
    g = G(f"tranche_t_{i}", (0, yc, ZF - 0.25), SILT)
    uv = (x0u, y0v + (SIL_H - y1) * SIL_RES, x1u, y0v + (SIL_H - y0) * SIL_RES)
    cube(g, f"tt{i}", (-SIL_W / 2, y0, ZF - 0.4), (SIL_W / 2, y1, ZF - 0.25), {"south": uv}, origin=(0, yc, ZF - 0.25))
    TR[i]["gt"], TR[i]["at"] = g, G("ctrl_alpha", (0, yc, ZF - 0.25), g)
# éclats répartis dans la silhouette (plan de face), un peu devant elle
ECL = G("add_eclats", (0, 0, 0), CAMS)
EC = []
k = 0
while k < 260:
    x, y = rng.uniform(-8.4, 8.4), rng.uniform(0.2, 32.4)
    if not dans_corps(x, y, 0.4):
        continue
    p = (x, y, ZF + 0.3 + rng.uniform(0, 0.9))
    sz = rng.uniform(0.5, 0.8)
    g = G(f"ec_{k}", p, ECL)
    tone = int(rng.integers(0, 3))
    cube(g, "e", np.subtract(p, sz / 2), np.add(p, sz / 2), {f_: UV[f"eclat{tone}"] for f_ in TOUT6}, origin=p,
         rotation=tuple(rng.uniform(-40, 40, 3)))
    EC.append(dict(g=g, p=np.array(p), y=y))
    k += 1

# --- points d'émission (≤ 32)
for k in range(8):                                    # éclats : autour du corps
    a = TAU * k / 8 + 0.3
    emit("eclat", (6.0 * math.cos(a), 4 + 3.6 * k, 6.0 * math.sin(a)), CORPS)
for k in range(6):                                    # stries : cercle au sol sous le bord du faisceau
    a = TAU * k / 6
    emit("strie", (10.5 * math.cos(a), 1.0, 10.5 * math.sin(a)), EFFET)
for k in range(4):                                    # grésillement : autour des mains et des pieds
    emit("mc_electric_spark", ((6.5 if k % 2 else -6.5), (12.0 if k < 2 else 1.0), 0.0), CORPS, nom="emit_mc_electric_spark")
for k in range(4):                                    # gerbe à l'impact et à l'extinction
    a = TAU * k / 4 + 0.6
    emit("mc_firework", (8 * math.cos(a), 1.0, 8 * math.sin(a)), EFFET, nom="emit_mc_firework")
for k in range(6):                                    # poussière bleutée qui flotte dans le faisceau
    a = TAU * k / 6 + 0.2
    emit("mc_dust_b4c8ff_10", (9 * math.cos(a), 6 + 8 * k, 9 * math.sin(a)), EFFET, nom="emit_mc_dust_b4c8ff_10")

# --- particules modélisées (groupes à la racine)
PART = {}
PART["eclat"] = G("particle_eclat", (0, 0, 0))
cube(PART["eclat"], "p_eclat", (-0.3, 0.3, -0.3), (0.3, 0.9, 0.3), {f_: UV["p_eclat"] for f_ in TOUT6}, origin=(0, 0.6, 0))
PART["strie"] = G("particle_strie", (0, 0, 0))
cube(PART["strie"], "p_strie", (-0.175, 0.3, -0.175), (0.175, 3.3, 0.175), {f_: UV["p_strie"] for f_ in LONG4}, origin=(0, 0.3, 0))
outliner = [EFFET.json(), JOUEUR.json(), PART["eclat"].json(), PART["strie"].json()]
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


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def ease_in(t, a, b, p=2.0):
    return 0.0 if t <= a else 1.0 if t >= b else ((t - a) / (b - a)) ** p


def temps(L, fps=FPS):
    n = max(2, int(round(L * fps)))
    return [round(L * i / n, 4) for i in range(n + 1)]


class Anim:
    def __init__(self, nom, L, loop):
        self.nom, self.L, self.loop, self.A, self.sons = nom, L, loop, {}, []
        self.T = temps(L)
        if loop == "loop":
            self.T = self.T[:-1] + [L]

    def piste(self, g, ch, f, T=None):
        T = self.T if T is None else T
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += [kf(ch, t, *f(t)) for t in T]

    def fixe(self, g, ch, v):
        self.A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"].append(kf(ch, 0, *v))

    def son(self, t, nom):
        self.sons.append({"channel": "sound", "data_points": [{"effect": nom, "file": ""}], "time": round(t, 3)})
        self.A["effects"] = {"name": "Effects", "type": "effect", "keyframes": self.sons}

    def alpha(self, ca, f, T=None):
        """ctrl_alpha : x = −1 + a."""
        self.piste(ca, "position", lambda t: (f(t) - 1.0, 0, 0), T)

    def cadence(self, sorte, f):
        for i, (g, c) in enumerate(EMIT[sorte]):
            self.piste(c, "position", lambda t, i=i: (max(-1.0, min(7.0, f(t, i))), 0, 0))

    def json(self):
        return {"uuid": nuid(), "name": self.nom, "loop": self.loop, "override": False, "length": self.L, "snapping": 30,
                "selected": self.nom == "depart", "animators": self.A}


un3 = lambda v: (v, v, v)
Z3 = (0, 0, 0)
QT = "q.anim_time"


def f3(v):
    return f"{v:.3f}"


def cl(expr, a=0, b=1):
    return f"math.clamp({expr},{a},{b})"


def m_mod(P, ph):
    return f"math.mod({QT}/{f3(P)}+{f3(ph)},1)"


def colonne_anim(an, T_IMP, T_OFF, flick=True, creux=None):
    """Chute (0 → T_IMP, accélère), tenue, extinction d'un coup à T_OFF (resserrement 0,12 s)."""
    chute = lambda t: ease_in(t, 0.0, T_IMP, 1.8)
    serre = lambda t: 1.0 - ease_in(t, T_OFF, T_OFF + 0.12, 1.6)
    Tc = sorted(set(an.T + [round(T_IMP * i / 12, 4) for i in range(13)] + [round(T_OFF + 0.01 * i, 4) for i in range(16)]))
    an.piste(COL, "scale", lambda t: (max(serre(t), 0.0), max(chute(t), 0.0), max(serre(t), 0.0)), Tc)
    # éclat : plus vif à l'impact, puis tenue légèrement vibrante ; sursaut juste avant l'extinction
    a = lambda t: (0.0 if t < 0.02 else 0.75 + 0.45 * bump(t, T_IMP - 0.05, T_IMP, T_IMP + 0.05, T_IMP + 0.5)
                   + (0.05 * math.sin(TAU * 7 * t) + 0.03 * math.sin(TAU * 13.3 * t) if flick else 0.0)
                   + 0.3 * bump(t, T_OFF - 0.15, T_OFF, T_OFF + 0.05, T_OFF + 0.12))
    # creux : le faisceau baisse pendant la silhouette, pour qu'elle ressorte (surtout de jour)
    c = (lambda t: 1.0 - 0.75 * bump(t, creux[0], creux[0] + 0.35, creux[1] - 0.35, creux[1])) if creux else (lambda t: 1.0)
    an.alpha(A_COQ, lambda t: min(1.0, a(t)) * c(t), Tc)
    an.alpha(A_AME, lambda t: min(1.0, a(t)) * c(t), Tc)
    # tête : descend avec le bas du faisceau, devient l'éclat d'impact
    an.piste(TETE, "position", lambda t: (0, -H * chute(t), 0), Tc)
    an.piste(TETE, "scale", lambda t: un3(sm(t, 0.0, 0.05) * (1 + 1.1 * bump(t, T_IMP - 0.03, T_IMP + 0.02, T_IMP + 0.06, T_IMP + 0.4))
                                          * (1 - sm(t, T_IMP + 0.1, T_IMP + 0.45))), Tc)
    # sol : cercle qui s'allume à l'impact, s'éteint après l'extinction ; onde de choc
    an.fixe(SOL, "scale", (1, 1, 1))
    an.alpha(A_SOL, lambda t: sm(t, T_IMP - 0.02, T_IMP + 0.12) * (0.85 + 0.15 * math.sin(TAU * 1.3 * t)) * (1 - sm(t, T_OFF, T_OFF + 0.6)))
    an.piste(ONDE, "scale", lambda t: un3(0.0 if t < T_IMP else 0.25 + 1.6 * (1 - (1 - sm(t, T_IMP, T_IMP + 0.7)) ** 2)), Tc)
    an.alpha(A_ONDE, lambda t: bump(t, T_IMP, T_IMP + 0.04, T_IMP + 0.2, T_IMP + 0.7))
    # stries et anneaux : apparaissent avec le faisceau, se resserrent avec lui
    an.piste(STRIES, "scale", lambda t: (serre(t), 1.0, serre(t)), Tc)
    an.alpha(A_STR, lambda t: sm(t, T_IMP - 0.1, T_IMP + 0.2) * (1 - sm(t, T_OFF, T_OFF + 0.1)))
    an.piste(ANN_G, "scale", lambda t: (serre(t) if t > T_IMP else 0.0, 1.0, serre(t) if t > T_IMP else 0.0),
             sorted(set(Tc + [round(T_IMP - 0.001, 4)])))


def stries_flux(an, sens, P0=1.6):
    """Chaque strie défile sur 300 px (sens +1 monte, −1 descend), en Molang (une clé)."""
    for d in STR:
        u = m_mod(P0 / d["v"], d["ph"])
        y = f"{u}*{f3(H - d['L'] - 4)}+2" if sens > 0 else f"(1-{u})*{f3(H - d['L'] - 4)}+2"
        an.fixe(d["g"], "position", (0, y, 0))
        an.fixe(d["g"], "scale", (1, f"math.sin({u}*180)", 1))      # naît et s'éteint aux bouts (pas de saut)


def anneaux_flux(an, T0, P=1.15):
    """Anneaux qui descendent de 288 à 0 en P s, décalés d'un quart de période ; s'allument doucement en haut."""
    for j, d in enumerate(ANN):
        u = m_mod(P, -T0 / P + 0.25 * j)
        an.fixe(d["g"], "position", (0, f"(1-{u})*{f3(H - 2)}+0.6", 0))
        an.fixe(d["g"], "scale", (1, 1, 1))
        an.fixe(d["a"], "position", (f"{cl(f'(1-{u})*8')}*{cl(f'{u}*25')}-1", 0, 0))


# ---------- charge (loop 3 s) : lueur légère, scintillements qui montent, le joueur s'élève de 0,6 px
LC = 3.0
ch = Anim("charge", LC, "loop")
lev = lambda t: 0.3 * (1 - math.cos(TAU * t / LC))
ch.piste(JOUEUR, "position", lambda t: (0, lev(t), 0))
ch.fixe(JOUEUR, "scale", (1, 1, 1))
ch.fixe(EFFET, "scale", (1, 1, 1))
for g in (COL, TETE, FLASH, ONDE, ECL):
    ch.fixe(g, "scale", Z3)
ch.piste(CORPS, "position", lambda t: (0, lev(t), 0))
ch.fixe(CORPS, "scale", (1, 1, 1))
for d in TR:          # lueur légère qui respire (Molang, période 1,5 s et 3/7 s)
    for ga, aa in ((d["g"], d["a"]), (d["gt"], d["at"])):
        ch.fixe(ga, "scale", (1, 1, 1))
        ch.fixe(aa, "position", (f"0.22+0.1*math.sin({QT}*240)+0.05*math.sin({QT}*840+{d['y'] * 20:.0f})-1", 0, 0))
ch.alpha(A_SOL, lambda t: 0.4 + 0.12 * math.sin(TAU * t / LC))
ch.fixe(SOL, "scale", (0.8, 1, 0.8))
# scintillements : stries écrasées (× 0,13 en hauteur : 288 px → 37 px, traits de 1,3 à 4,7 px), autour du corps
ch.fixe(STRIES, "scale", (0.95, 0.13, 0.95))
ch.alpha(A_STR, lambda t: 0.75)
for d in STR:
    u = f"math.mod({QT}/{f3(LC / max(1, round(d['v'] * 2)))}+{f3(d['ph'])},1)"
    ch.fixe(d["g"], "position", (0, f"{u}*{f3(H - d['L'] - 4)}+2", 0))
    ch.fixe(d["g"], "scale", (1, f"math.sin({u}*180)", 1))
# anneaux : deux, en alternance, montent lentement des pieds à la tête (rayon 10,9 px), discrets
ch.fixe(ANN_G, "scale", (0.75, 1, 0.75))
for j, d in enumerate(ANN):
    u = f"math.mod({QT}/{f3(LC / 2)}+{f3(0.25 * j)},1)"
    ch.fixe(d["g"], "position", (0, f"{u}*34", 0))
    ch.fixe(d["g"], "scale", un3(1 if j % 2 == 0 else 0))          # deux anneaux seulement, en alternance
    ch.fixe(d["a"], "position", (f"math.sin({u}*180)*0.45-1", 0, 0))
ch.cadence("eclat", lambda t, i: 0.5)
ch.cadence("strie", lambda t, i: -1)
ch.cadence("mc_electric_spark", lambda t, i: -1 + 2.5 * bump((t / LC + 0.25 * i) % 1.0, 0.0, 0.05, 0.12, 0.2))
ch.cadence("mc_firework", lambda t, i: -1)
ch.cadence("mc_dust_b4c8ff_10", lambda t, i: -1 if i > 1 else 0)


# ---------- depart (once 4,4 s)
LD = 4.4
T_IMP, T_HIDE, T_DIS, DUR_DIS, T_OFF_D = 0.35, 1.5, 1.52, 0.85, 3.1
de = Anim("depart", LD, "once")
de.fixe(EFFET, "scale", (1, 1, 1))
de.piste(EFFET, "scale", lambda t: un3(1.0 if t < LD - 0.04 else 0.0), T=[0, round(LD - 0.05, 4), LD])
colonne_anim(de, T_IMP, T_OFF_D, creux=(0.6, T_DIS + DUR_DIS + 0.3))
stries_flux(de, +1)
anneaux_flux(de, T_IMP)
# la copie : s'élève doucement dans le faisceau, cachée au plus vif (échelle ignorée au départ, seuil 0,05)
lift_d = lambda t: LEVE * sm(t, 0.6, T_HIDE)
de.piste(JOUEUR, "position", lambda t: (0, lift_d(t), 0))
de.piste(JOUEUR, "scale", lambda t: un3(1.0 if t < T_HIDE else 0.0), T=[0, round(T_HIDE - 0.001, 4), T_HIDE])
de.piste(CORPS, "position", lambda t: (0, lift_d(min(t, T_HIDE)) + 0.6 * sm(t, T_HIDE, T_HIDE + 1.0), 0))
de.fixe(CORPS, "scale", (1, 1, 1))
# enveloppe : s'allume depuis le torse, plus vive avant la disparition, se défait de bas en haut
for d in TR:
    ton = 0.55 + 0.45 * abs(d["y"] - 18) / 16
    ti = T_DIS + d["y"] / 33 * DUR_DIS
    pic = f"(0.75+0.25*{cl(f'1-math.abs({QT}-{f3(T_HIDE - 0.05)})/0.35')})"
    for ga, aa in ((d["g"], d["a"]), (d["gt"], d["at"])):
        de.fixe(ga, "scale", (1, 1, 1))
        de.fixe(aa, "position", (f"{cl(f'({QT}-{f3(ton)})/0.3')}*(1-{cl(f'({QT}-{f3(ti)})/0.45')})*{pic}-1", 0, 0))
# éclats : s'allument depuis le torse, scintillent, puis montent en accélérant dans le faisceau (bas d'abord)
for k, d in enumerate(EC):
    x0, y0, z0 = d["p"]
    dist = math.hypot(x0 * 0.6, y0 - 18)
    ton = 0.5 + 0.5 * min(dist / 17, 1) + rng.uniform(0, 0.08)
    ti = T_DIS + y0 / 33 * DUR_DIS + rng.uniform(-0.06, 0.06)
    U = cl(f"{QT}-{f3(ti)}", 0, 3)
    A, B, kin = rng.uniform(55, 95), rng.uniform(10, 25), rng.uniform(0.4, 0.75)
    de.fixe(d["g"], "position", (f"-{f3(x0 * kin)}*{cl(f'{U}/1.1')}", f"{f3(A)}*{U}*{U}+{f3(B)}*{U}",
                                 0))
    w, ph = rng.uniform(900, 1700), rng.uniform(0, 360)
    de.fixe(d["g"], "scale", un3(f"{cl(f'({QT}-{f3(ton)})/0.15')}*(1-{cl(f'({QT}-{f3(ti + 0.15)})/{f3(rng.uniform(0.6, 1.0))}')})"
                                 f"*(0.85+0.2*math.sin({QT}*{w:.0f}+{ph:.0f}))"))
# éclat du corps : masque la disparition de la copie
de.piste(FLASH, "scale", lambda t: un3((0.4 + 0.7 * sm(t, T_HIDE - 0.12, T_HIDE)) * bump(t, T_HIDE - 0.14, T_HIDE - 0.02, T_HIDE + 0.03, T_HIDE + 0.22)))
de.fixe(FLASH, "position", Z3)
# particules : éclats depuis le corps pendant la dissolution, stries au sol tant que le faisceau tient
de.cadence("eclat", lambda t, i: -1 if t < 0.6 or t > T_DIS + DUR_DIS + 0.3 else 1 + 5 * bump(t, T_HIDE - 0.2, T_HIDE, T_DIS + DUR_DIS - 0.2, T_DIS + DUR_DIS + 0.2))
de.cadence("strie", lambda t, i: -1 if t < T_IMP or t > T_OFF_D else 1 + 3 * bump(t, T_HIDE - 0.1, T_HIDE + 0.1, 2.4, 2.8))
de.cadence("mc_electric_spark", lambda t, i: -1 if t < 0.55 or t > T_HIDE + 0.05 else 2 + 3 * sm(t, 0.8, T_HIDE))
de.cadence("mc_firework", lambda t, i: -1 + 6 * bump(t, T_IMP - 0.02, T_IMP, T_IMP + 0.08, T_IMP + 0.2)
           + 5 * bump(t, T_OFF_D - 0.02, T_OFF_D + 0.02, T_OFF_D + 0.1, T_OFF_D + 0.2))
de.cadence("mc_dust_b4c8ff_10", lambda t, i: -1 if t < T_IMP or t > T_OFF_D + 0.6 else 1)
de.son(0.0, "stellaire_rayon_eclair")
de.son(T_HIDE - 1.0, "stellaire_rayon_montee")
de.son(T_OFF_D - 0.03, "stellaire_rayon_extinction")


# ---------- arrivee (once 4,4 s)
LA = 4.4
T_IMP_A, T_APP, T_OFF_A = 0.35, 1.55, 2.95
ar = Anim("arrivee", LA, "once")
ar.fixe(EFFET, "scale", (1, 1, 1))
ar.piste(EFFET, "scale", lambda t: un3(1.0 if t < LA - 0.04 else 0.0), T=[0, round(LA - 0.05, 4), LA])
colonne_anim(ar, T_IMP_A, T_OFF_A, creux=(0.5, 2.5))
stries_flux(ar, -1)
anneaux_flux(ar, T_IMP_A)
# le joueur : apparaît à sa taille au plus vif de la silhouette, 1,5 px au-dessus du sol, et s'y pose
desc = lambda t: LEVE * (1 - sm(t, T_APP, T_APP + 0.9))
ar.piste(JOUEUR, "position", lambda t: (0, desc(t), 0))
ar.piste(JOUEUR, "scale", lambda t: un3(0.0 if t < T_APP else 1.0), T=[0, round(T_APP - 0.001, 4), T_APP])
ar.piste(CORPS, "position", lambda t: (0, desc(t), 0))
ar.fixe(CORPS, "scale", (1, 1, 1))
T_POSE0, DUR_POSE, T_EFF0, DUR_EFF = 0.75, 0.7, T_APP + 0.08, 0.8
for d in TR:
    tp = T_POSE0 + d["y"] / 33 * DUR_POSE + 0.1                 # se remplit de bas en haut
    tf = T_EFF0 + (1 - d["y"] / 33) * DUR_EFF                    # s'efface de haut en bas
    pic = f"(0.75+0.25*{cl(f'1-math.abs({QT}-{f3(T_APP - 0.05)})/0.35')})"
    for ga, aa in ((d["g"], d["a"]), (d["gt"], d["at"])):
        ar.fixe(ga, "scale", (1, 1, 1))
        ar.fixe(aa, "position", (f"{cl(f'({QT}-{f3(tp)})/0.4')}*(1-{cl(f'({QT}-{f3(tf)})/0.45')})*{pic}-1", 0, 0))
for k, d in enumerate(EC):
    x0, y0, z0 = d["p"]
    te = T_POSE0 + y0 / 33 * DUR_POSE + rng.uniform(-0.05, 0.05)    # arrivée (bas d'abord)
    du = rng.uniform(0.45, 0.7)
    ta = te - du
    D = rng.uniform(70, 150)
    kin = rng.uniform(0.4, 0.7)
    e = cl(f"({QT}-{f3(ta)})/{f3(du)}")
    ar.fixe(d["g"], "position", (f"-{f3(x0 * kin)}*(1-{e})*(1-{e})", f"{f3(D)}*(1-{e})*(1-{e})", 0))
    tf = T_EFF0 + (1 - y0 / 33) * DUR_EFF + rng.uniform(-0.08, 0.08)
    w, ph = rng.uniform(900, 1700), rng.uniform(0, 360)
    ar.fixe(d["g"], "scale", un3(f"{cl(f'({QT}-{f3(ta)})/0.12')}*(1-{cl(f'({QT}-{f3(tf)})/0.3')})"
                                 f"*(0.85+0.2*math.sin({QT}*{w:.0f}+{ph:.0f}))"))
ar.piste(FLASH, "scale", lambda t: un3((0.4 + 0.7 * sm(t, T_APP - 0.12, T_APP)) * bump(t, T_APP - 0.14, T_APP - 0.02, T_APP + 0.03, T_APP + 0.22)))
ar.fixe(FLASH, "position", Z3)
ar.cadence("eclat", lambda t, i: -1 if t < T_APP - 0.1 or t > T_EFF0 + DUR_EFF + 0.2 else 1 + 3 * bump(t, T_APP - 0.1, T_APP + 0.05, 2.0, 2.4))
ar.cadence("strie", lambda t, i: -1 if t < T_IMP_A or t > T_OFF_A else 1 + 2 * bump(t, 0.6, 0.8, 1.4, 1.7))
ar.cadence("mc_electric_spark", lambda t, i: -1 if t < T_APP - 0.05 or t > T_APP + 0.7 else 2)
ar.cadence("mc_firework", lambda t, i: -1 + 6 * bump(t, T_IMP_A - 0.02, T_IMP_A, T_IMP_A + 0.08, T_IMP_A + 0.2)
           + 5 * bump(t, T_OFF_A - 0.02, T_OFF_A + 0.02, T_OFF_A + 0.1, T_OFF_A + 0.2))
ar.cadence("mc_dust_b4c8ff_10", lambda t, i: -1 if t < T_IMP_A or t > T_OFF_A + 0.6 else 1)
ar.son(0.0, "stellaire_rayon_eclair")
ar.son(T_APP - 1.0, "stellaire_rayon_montee")
ar.son(T_OFF_A - 0.03, "stellaire_rayon_extinction")


# ---------- particules
def part_anim(sorte, L, ch_, f, n=12):
    a = Anim(f"particle_{sorte}_fall", L, "loop")
    a.piste(PART[sorte], ch_, f, T=[round(i * L / n, 4) for i in range(n + 1)])
    return a


pe = part_anim("eclat", 0.4, "scale", lambda t: un3(1 + 0.35 * math.sin(TAU * t / 0.4)), n=8)
ps = part_anim("strie", 0.5, "scale", lambda t: (1, 1 + 0.3 * math.sin(TAU * t / 0.5), 1), n=8)

ANIMS = [ch.json(), de.json(), ar.json(), pe.json(), ps.json()]
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64},
            {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64}]
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures,
         "animations": ANIMS}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
embarquer_sons(model, {n: f"sons/{n}.ogg" for n in ("stellaire_rayon_eclair", "stellaire_rayon_montee", "stellaire_rayon_extinction")})
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
