"""Aura brasier (version 3) : une aura d'énergie rouge façon anime, faite de lumière qui enveloppe la silhouette et s'élève.
Design original. Écrit aura_brasier.png, aura_brasier_e.png et .build/aura_brasier_brut.bbmodel à côté de ce script.

Refus précédents (retours-en-jeu.md) : objets en orbite (« pas une aura »), langues de feu à contour sombre (« mec en feu »),
liseré en plaques croisées fixes dans les membres (« horriblement moche », barre blanche devant le visage hors de face).

Design
- Halo de silhouette : des disques de lueur douce (noir au bord, rouge, cœur rose clair), chacun dans un groupe cam_ (face caméra)
  centré sur un point du squelette : 1 pour la tête, 3 pour le torse, 3 par bras, 3 par jambe. Un disque est invariant par
  rotation : quelle que soit la vue ou la pose (accroupi, couché en élytres), il reste un plan face à la caméra, reculé derrière
  le centre de la partie (RECUL, 3 à 4 px) pour rester derrière toute sa surface visible, même vue en biais ; le centre du disque
  est vide (zone cachée), pour qu'une arête qui traverse le plan n'y découpe pas de bande. Le joueur cache donc tout ce qui tombe dans sa silhouette : il reste une lueur autour de lui, et rien
  ne passe jamais devant le visage ou le corps. Les lueurs voisines s'additionnent : rose clair contre le corps, rouge plus loin.
- Énergie qui monte : 11 colonnes de lumière douces (dégradé gaussien, sans contour), dans un seul groupe camy_ (face caméra,
  debout) centré sur le torse. Elles sont placées dans ce repère *derrière* le pivot (z local < 0, côté opposé à la caméra) :
  sous tous les angles horizontaux, elles restent derrière le joueur et ne dépassent qu'autour de lui, hautes derrière la tête,
  basses à hauteur des jambes. Chaque colonne s'étire et vacille (scale en Molang). Sa texture est un petit film de 8 images
  (traînées qui montent) posées côte à côte dans l'atlas, parcourues par un ctrl_uv en pas entiers (math.floor/math.mod) :
  la forme de la colonne reste fixe, seules les traînées montent (un simple défilement couperait le haut de la colonne net).
- Sol : un anneau de lumière additif, à plat sous les pieds, qui tourne lentement et pulse (masqué quand le corps n'est pas debout).
- Étincelles : particule modélisée particle_etincelle (étoile claire, une face south de 0,3 px) et 14 points emit_etincelle sur
  le corps ; poussière rouge de Minecraft emit_mc_dust_ff3a28_10 (8 points, même nom). Aucune particule qui tombe et se pose.
- Palette : rose blanc près du corps, rouge vif, rouge profond aux extrémités ; le noir n'existe qu'en additif (invisible).
  Pas de pixel semi-transparent ; calque _e = même lueur atténuée (AVEC_E).

États : idle (respiration lente), walk et run (l'énergie part vers l'arrière, plus haute et plus vive en course), sneak
(contenue, plus basse et plus large), fly (étirée, vers l'arrière), glide et swim (corps couché : les colonnes, toujours
verticales en camy_, se rentrent ; il reste le halo, et la traîne vient des particules lâchées sans élan), fall (s'étire vers le haut), mount (repos plus bas), sleep (presque éteinte), attack
(embrasement bref, once 0,8 s), hurt (vacille et baisse, once 0,8 s). Couche overlay_flux : film des colonnes, rotation lente
des disques (bord ondulé qui frémit) et de l'anneau. overlay_ambiance ajoutée par tools/ambiance.py. Aucun son.

Fonctions avancées (guide 4 bis, 5 ter, 6.3, 6.4) : add_ (tout l'effet), cam_ (disques), camy_ (colonnes), ctrl_alpha
(opacité qui respire, baisse en sommeil, flash à l'attaque : valeurs « 1 + position »), ctrl_uv (film des colonnes),
particle_/emit_ (étincelles), emit_mc_dust (poussière rouge), overlay_ (flux continu), Molang (math.mod, math.floor, sin).

Ce qui se juge seulement en jeu (/cosmetique apercu) : le rendu additif réel (de jour, l'additif s'éclaircit sur le ciel),
ctrl_alpha et ctrl_uv (non simulés par nos aperçus : le rendu montre l'image 0 du film à pleine opacité), le sens du
défilement (supposé : décalage v positif = motif qui monte), les particules, et le menu Apparence (sans caméra, les plaques y
sont montrées telles quelles, face sud vers l'arrière : l'aura y est peu visible de face).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "aura_brasier"
AVEC_E = True       # correctif du clignotement annoncé le 2026-11-03, à vérifier en jeu.
TEX = 512
SS = 4
E_GAIN = 0.4        # _e = même lueur, atténuée (elle s'ajoute à la texture)
RNG = np.random.default_rng(7)

# ------------------------------------------------------------------ palette (intensité 0..1 -> couleur additive)
STOPS = [(0.0, (0, 0, 0)), (0.12, (46, 3, 9)), (0.32, (140, 12, 28)), (0.55, (220, 34, 48)),
         (0.75, (250, 82, 86)), (0.9, (255, 150, 148)), (1.0, (255, 214, 208))]


def palette(f):
    f = np.clip(f, 0, 1)
    xs = [s[0] for s in STOPS]
    return np.stack([np.interp(f, xs, [s[1][c] for s in STOPS]) for c in range(3)], axis=-1)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def reduire(f, W, H, gain, cutout=False):
    """f : intensité sur-échantillonnée (H*SS, W*SS). Retourne une image RGBA W x H, alpha 0/255.
    En additif, le noir est invisible : alpha 255 partout (pas de bord découpé)."""
    rgb = palette(f) * gain
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = np.array(im)
    if cutout:
        a = np.array(Image.fromarray((np.clip(f * 3, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
        arr[..., 3] = a * 255
        arr[~a, :3] = 0
    else:
        # noir presque pur : transparent. En additif il était déjà invisible ; dans le menu Apparence, qui ne dessine pas
        # l'additif (capture du 2026-11-03), il n'apparaît plus en carrés noirs.
        lum = arr[..., :3].max(axis=2)
        arr[..., 3] = (lum > 16) * 255
        arr[lum <= 16, :3] = 0
    return arr


def grille(W, H):
    n_w, n_h = W * SS, H * SS
    return np.meshgrid((np.arange(n_w) + 0.5) / n_w * 2 - 1, 1 - (np.arange(n_h) + 0.5) / n_h * 2)   # x, y dans [-1, 1], y vers le haut


CORE = 0.42         # part du rayon d'un disque où la lueur est pleine (cachée par le membre)


def paint_disque(seed, N=64):
    """Lueur ronde : nulle au centre, pleine à CORE (bord du membre), puis décroissance douce jusqu'au noir ; bord ondulé."""
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    wob = 1 + 0.07 * np.sin(5 * a + seed) + 0.05 * np.sin(9 * a + 2.3 * seed)
    s = np.clip((r / wob - CORE) / (0.97 - CORE), 0, 1)
    # creux au centre : cette zone est cachée par le membre ; là où une arête du joueur traverse le plan du disque (vue en
    # biais, membre vu dans sa longueur), la coupure tomberait sur une lueur pleine et ferait une bande nette.
    f = (1 - s) ** 2.1 * 0.92 * smooth(r / wob / CORE) ** 1.3
    f *= smooth((1 - r) / 0.06)        # noir garanti au bord de la plaque
    return reduire(f, N, N, 0.46)


FR = 8              # images du film d'une colonne


def paint_colonne(W, H, seed, k):
    """Image k du film d'une colonne de lumière : enveloppe fixe (gaussienne qui s'affine vers le haut, fondue en haut et en
    bas), traînées claires qui montent d'une demi-hauteur sur les FR images (film fermé)."""
    x, y = grille(W, H)
    Y = (y + 1) / 2                                  # 0 en bas, 1 en haut
    ph = k / FR * 0.5
    sway = 0.10 * np.sin(2 * np.pi * (1.0 * Y - 2 * ph) + seed) * Y
    sig = 0.50 * (1 - Y) ** 0.7 + 0.12
    env = np.exp(-((x - sway) / sig) ** 2 * 1.6) * smooth(Y / 0.4) ** 0.8 * (1 - Y) ** 1.15
    env *= smooth((1 - np.abs(x)) / 0.12)            # noir sur les bords de l'image (pas de fuite entre images)
    tr = 0.5 + 0.5 * np.sin(2 * np.pi * (2 * (Y - ph) + 0.35 * np.sin(3.1 * x + seed)))
    tr2 = 0.5 + 0.5 * np.sin(2 * np.pi * (4 * (Y - ph) - 0.6 * x + seed * 0.3))
    f = env * (0.72 + 0.2 * tr + 0.08 * tr2)
    return reduire(f, W, H, 0.78)


def paint_anneau(N=96):
    x, y = grille(N, N)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    w = 0.10 + 0.03 * np.sin(3 * a)
    f = np.exp(-((r - 0.72) / w) ** 2) * (0.75 + 0.25 * np.sin(6 * a) ** 2) + 0.25 * np.exp(-((r - 0.45) / 0.14) ** 2)
    f *= smooth((1 - r) / 0.08)
    return reduire(np.clip(f, 0, 1) * 0.8, N, N, 0.7)


def paint_etincelle(N=16):
    x, y = grille(N, N)
    r = np.abs(x) ** 0.5 + np.abs(y) ** 0.5
    f = np.clip(1.15 - r, 0, 1) ** 0.8
    return reduire(f, N, N, 1.0, cutout=True)


UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)


def poser(nom, im, x, y):
    h, w = im.shape[:2]
    assert x + w <= TEX and y + h <= TEX and not tex[y:y + h, x:x + w, 3].any(), nom
    tex[y:y + h, x:x + w] = im
    UV[nom] = (x, y, x + w, y + h)


poser("disque0", paint_disque(0.0), 0, 0)
poser("disque1", paint_disque(2.1), 64, 0)
poser("anneau", paint_anneau(), 128, 0)
poser("etincelle", paint_etincelle(), 228, 0)
COL = {"A": (24, 120), "B": (16, 120)}               # largeur d'une image, hauteur (texels)
for j, (v, (w, h)) in enumerate(COL.items()):
    y0 = 100 + j * 124
    for k in range(FR):
        poser(f"col{v}{k}", paint_colonne(w, h, 1.3 + 2.0 * j, k), k * w, y0)

assert set(np.unique(tex[..., 3])) <= {0, 255}, "semi-transparence"
tex_e = tex.copy()
tex_e[..., :3] = (tex[..., :3].astype(np.float32) * E_GAIN).astype(np.uint8)
_b64 = []
for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(fn, optimize=True)
    _buf = io.BytesIO()
    im_.save(_buf, "PNG", optimize=True)
    _b64.append("data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode())
tex_b64, tex_e_b64 = _b64


# ------------------------------------------------------------------ géométrie
def nuid():
    return str(_uuid.uuid4())


class G:
    """Groupe : nom affiché (peut se répéter pour ctrl_ et emit_mc_), pivot, enfants (cubes et groupes)."""
    tous = []

    def __init__(self, nom, origin, parent=None):
        assert len(nom) <= 64
        self.nom, self.origin, self.uuid, self.enfants = nom, [round(float(v), 3) for v in origin], nuid(), []
        if parent is not None:
            parent.enfants.append(self)
        G.tous.append(self)

    def json(self):
        return {"name": self.nom, "origin": self.origin, "uuid": self.uuid,
                "children": [c.json() if isinstance(c, G) else c for c in self.enfants]}


elements = []


def plaque(g, nom, c, w, h, uv, face="south", ep=0.3):
    """Plaque fine centrée en c, une seule face texturée (les autres ne sont pas dessinées)."""
    c = np.asarray(c, float)
    if face == "south":
        a, b = c - (w / 2, h / 2, ep / 2), c + (w / 2, h / 2, ep / 2)
    else:                                            # up : plaque à plat, w en x, h en z
        a, b = c - (w / 2, ep / 2, h / 2), c + (w / 2, ep / 2, h / 2)
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in a], "to": [round(float(v), 3) for v in b],
         "origin": [round(float(v), 3) for v in c], "box_uv": False, "faces": {face: {"uv": [round(float(v), 2) for v in uv], "texture": 0}}}
    elements.append(e)
    g.enfants.append(e["uuid"])


MEMBRES = {m: G(m, (0, 24, 0)) for m in ("head", "body", "right_arm", "left_arm", "right_leg", "left_leg")}

# Disques : zone, membre, centre de la zone, [(centre du disque, rayon total)] ; RECUL : plan reculé (z local) pour rester
# derrière toute la surface visible de la partie, même quand elle est vue en biais (sinon la lueur passe devant ses arêtes).
RECUL = {"tete": 3.0, "corps": 4.0, "bras_d": 3.4, "bras_g": 3.4, "jambe_d": 3.4, "jambe_g": 3.4}
ZONES = {
    "tete": ("head", (0, 28, 0), [((0, 28.2, 0), 9.6)]),
    "corps": ("body", (0, 18, 0), [((0, 21.5, 0), 6.2), ((0, 18, 0), 6.0), ((0, 14.5, 0), 6.0)]),
    "bras_d": ("right_arm", (6, 18, 0), [((6, 21.5, 0), 5.2), ((6, 18, 0), 5.0), ((6, 14.2, 0), 5.0)]),
    "bras_g": ("left_arm", (-6, 18, 0), [((-6, 21.5, 0), 5.2), ((-6, 18, 0), 5.0), ((-6, 14.2, 0), 5.0)]),
    "jambe_d": ("right_leg", (2, 6, 0), [((2, 10, 0), 5.2), ((2, 6, 0), 5.0), ((2, 2.2, 0), 5.0)]),
    "jambe_g": ("left_leg", (-2, 6, 0), [((-2, 10, 0), 5.2), ((-2, 6, 0), 5.0), ((-2, 2.2, 0), 5.0)]),
}
AURA, ETAT, ADD, DISQUES, ALPHA = {}, {}, {}, [], {}
for z, (m, c, discs) in ZONES.items():
    AURA[z] = G(f"aura_{z}", c, MEMBRES[m])
    ETAT[z] = G(f"etat_{z}", c, AURA[z])
    ADD[z] = G(f"add_{z}", c, ETAT[z])
    ALPHA[z] = G("ctrl_alpha", c, ADD[z])
    for k, (p, R) in enumerate(discs):
        g = G(f"cam_{z}{k + 1}", p, ADD[z])
        # plan légèrement derrière le pivot (z local < 0 : côté opposé à la caméra), décalé entre disques voisins
        plaque(g, f"lueur_{z}{k + 1}", (p[0], p[1], p[2] - RECUL[z] - 0.05 * k), 2 * R, 2 * R, UV[f"disque{(k + len(DISQUES)) % 2}"])
        DISQUES.append(g)

# Colonnes : repère camy_ centré sur le torse ; x = côté, z < 0 = derrière le joueur vu de la caméra, y = base, h = hauteur.
FLUX_C = (0, 14, 0)
AURA["flux"] = G("aura_flux", FLUX_C, MEMBRES["body"])
ETAT["flux"] = G("etat_flux", FLUX_C, AURA["flux"])
CAMY = G("camy_flux", FLUX_C, ETAT["flux"])
ADD["flux"] = G("add_flux", FLUX_C, CAMY)
ALPHA["flux"] = G("ctrl_alpha", FLUX_C, ADD["flux"])
COLONNES = [  # (x, z, base y, hauteur, largeur, type)
    (0.0, -4.6, 17.0, 27.0, 10.0, "A"),
    (-3.8, -4.2, 15.0, 23.0, 8.0, "A"), (3.8, -4.3, 15.5, 22.0, 8.0, "A"),
    (-6.0, -5.2, 21.0, 18.0, 6.0, "B"), (6.0, -5.1, 20.5, 19.0, 6.0, "B"),
    (-8.2, -3.6, 10.0, 21.0, 6.5, "B"), (8.2, -3.7, 10.5, 20.0, 6.5, "B"),
    (-8.6, -3.0, 2.0, 15.0, 7.0, "B"), (8.6, -3.1, 1.5, 16.0, 7.0, "B"),
    (-5.0, -2.6, -0.5, 13.0, 5.0, "B"), (5.0, -2.7, -0.5, 12.0, 5.0, "B"),
]
COLS = []
for i, (x, zz, y0, h, w, t) in enumerate(COLONNES):
    base = (x, y0, zz)
    g = G(f"col{i}", base, ADD["flux"])
    plaque(g, f"colonne{i}", (x, y0 + h / 2, zz), w, h, UV[f"col{t}0"])
    uvg = G("ctrl_uv", base, g)
    COLS.append((g, uvg, t, i))

# Sol : anneau à plat sous les pieds (suit le torse ; masqué quand le corps n'est pas debout).
AURA["sol"] = G("aura_sol", (0, 0.4, 0), MEMBRES["body"])
ETAT["sol"] = G("etat_sol", (0, 0.4, 0), AURA["sol"])
ADD["sol"] = G("add_sol", (0, 0.4, 0), ETAT["sol"])
ALPHA["sol"] = G("ctrl_alpha", (0, 0.4, 0), ADD["sol"])
SOL = G("sol_tourne", (0, 0.4, 0), ADD["sol"])
plaque(SOL, "anneau", (0, 0.45, 0), 26, 26, UV["anneau"], face="up")

# Points de départ des étincelles (+Y du groupe = vers le haut) et de la poussière de Minecraft.
EMITS = []


def emit(nom, p, parent):
    EMITS.append(G(nom, p, parent))


ETINC = [("tete", (0, 32.6, 0)), ("tete", (3.5, 30, 2)), ("tete", (-3.5, 30, 2)),
         ("corps", (0, 22, 2.6)), ("corps", (2.5, 15, 2.6)), ("corps", (-2.5, 15, -2.6)),
         ("bras_d", (8.4, 23, 0)), ("bras_d", (6, 12.2, 0)), ("bras_g", (-8.4, 23, 0)), ("bras_g", (-6, 12.2, 0)),
         ("jambe_d", (4.3, 5, 0)), ("jambe_g", (-4.3, 5, 0)), ("jambe_d", (2, 1, 2.5)), ("jambe_g", (-2, 1, -2.5))]
for k, (z, p) in enumerate(ETINC):
    emit("emit_etincelle" + (str(k + 1) if k else ""), p, ETAT[z])
for z, p in [("jambe_d", (4.5, 0.5, 2)), ("jambe_g", (-4.5, 0.5, -2)), ("jambe_d", (3, 0.5, -3)), ("jambe_g", (-3, 0.5, 3)),
             ("bras_d", (8.5, 18, 0)), ("bras_g", (-8.5, 18, 0)), ("corps", (0, 24.5, 3)), ("tete", (0, 33, -1))]:
    emit("emit_mc_dust_ff3a28_10", p, ETAT[z])

# Particule : étincelle, un seul cube de 0,3 px, face south seule (réglage conseillé : Face caméra).
PART = G("particle_etincelle", (0, 0, 0))
plaque(PART, "etincelle", (0, 1.1, 0), 1.6, 1.6, UV["etincelle"])

outliner = [MEMBRES[m].json() for m in MEMBRES] + [PART.json()]


# ------------------------------------------------------------------ animations
def s(v):
    return v if isinstance(v, str) else str(round(v + 0.0, 4))


def kf(ch, t, x, y, z, interp="linear"):
    return {"channel": ch, "data_points": [{"x": s(x), "y": s(y), "z": s(z)}], "time": round(t, 4), "interpolation": interp}


def piste(A, g, keys):
    A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += keys


def sinus(L, k, ph, amp, base=0.0):
    """base + amp * sin(q.anim_time * 360 k / L + ph) : période fermée sur la boucle."""
    if amp == 0:
        return base
    return f"{s(base)}+{s(amp)}*math.sin(q.anim_time*{s(360 * k / L)}+{int(ph)})"


PH_Z = {z: int(RNG.integers(0, 360)) for z in list(ZONES) + ["flux", "sol"]}
PH_C = [(int(RNG.integers(0, 360)), int(RNG.integers(0, 360))) for _ in COLS]


def etat(nom, L, haut=1.0, larg=1.0, vac=0.10, halo=1.0, souffle=0.03, alpha=-0.2, a_amp=0.08, flux=(0, 0, 0), recul=0.0,
         sol=1.0, kv=2, kb=1):
    """haut / larg : échelle des colonnes ; vac : vacillement ; halo : échelle des disques ; souffle : respiration des disques ;
    alpha / a_amp : opacité (ctrl_alpha, 0 normal, -1 invisible) et sa respiration ; flux : décalage du pivot des colonnes (px,
    repère du torse, +Z = vers l'arrière) ; recul : halo décalé vers l'arrière (+Z) ; sol : échelle de l'anneau (0 masqué) ;
    kv : vacillements par boucle ; kb : respirations par boucle."""
    A = {}
    for z in ZONES:
        sc = sinus(L, kb, PH_Z[z], halo * souffle, halo)
        piste(A, ETAT[z], [kf("scale", 0, sc, sc, sc)])
        if recul:
            piste(A, ETAT[z], [kf("position", 0, 0, 0, recul)])
    for z in list(ZONES) + ["flux", "sol"]:
        piste(A, ALPHA[z], [kf("position", 0, sinus(L, kb, PH_Z[z] + 90, a_amp, alpha), 0, 0)])
    if any(flux):
        piste(A, ETAT["flux"], [kf("position", 0, *flux)])
    for (g, _, t, i), (p1, p2) in zip(COLS, PH_C):
        k1, k2 = kv + (i % 2), kv + 1 + (i % 3)
        sy = f"{s(haut)}*(1+{s(vac)}*math.sin(q.anim_time*{s(360 * k1 / L)}+{p1})+{s(vac * 0.5)}*math.sin(q.anim_time*{s(360 * k2 / L)}+{p2}))"
        sx = sinus(L, k2, p2 + 60, larg * vac * 0.4, larg)
        piste(A, g, [kf("scale", 0, sx, sy, 1)])
    sc = sinus(L, kb, PH_Z["sol"], sol * 0.06, sol)
    piste(A, ETAT["sol"], [kf("scale", 0, sc, 1 if sol else 0, sc)])
    return {"uuid": nuid(), "name": nom, "loop": "loop", "override": False, "length": L, "snapping": 24, "selected": nom == "idle",
            "animators": A}


STATES = [
    etat("idle", 8.0, kv=4, kb=2),                                                   # respiration de 4 s
    etat("walk", 1.6, haut=1.05, alpha=-0.15, flux=(0, 0, 1.5), recul=0.3, kv=1),
    etat("run", 1.0, haut=1.25, larg=0.92, vac=0.13, alpha=-0.02, a_amp=0.02, flux=(0, -0.5, 4.0), recul=0.8, kv=1),
    etat("sneak", 4.0, haut=0.72, larg=1.3, halo=0.92, alpha=-0.35, flux=(0, -3.5, 1.5), sol=0, kv=2),
    etat("fly", 2.4, haut=1.15, larg=0.95, alpha=-0.1, flux=(0, 0, 2.0), recul=0.4, kv=2),
    etat("glide", 3.6, haut=0, larg=0, alpha=-0.15, sol=0, kv=3),          # couché : colonnes rentrées, la traîne vient des particules
    etat("swim", 3.6, haut=0, larg=0, alpha=-0.25, sol=0, kv=2),
    etat("fall", 2.0, haut=1.22, larg=0.85, vac=0.08, halo=1.04, alpha=-0.1, flux=(0, 1.0, 0), sol=0.8, kv=2),
    etat("mount", 4.0, haut=0.85, alpha=-0.25, flux=(0, -1.0, 0), sol=0, kv=2),
    etat("sleep", 4.0, haut=0.3, larg=0.8, vac=0.05, halo=0.85, souffle=0.02, alpha=-0.78, a_amp=0.06, sol=0, kv=1),
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


def ponctuel(nom, f_halo, f_flux, f_alpha, f_pos=None):
    L = 0.8
    T = [j * L / 16 for j in range(17)]
    A = {}
    for g in DISQUES:      # chaque disque grandit sur place (une échelle du groupe de zone écarterait les disques)
        piste(A, g, [kf("scale", t, *([f_halo(t)] * 3)) for t in T])
    for z in ZONES:
        if f_pos:
            piste(A, AURA[z], [kf("position", t, *f_pos(t, z)) for t in T])
    piste(A, AURA["flux"], [kf("scale", t, *([f_flux(t)] * 3)) for t in T])
    for z in list(ZONES) + ["flux"]:
        piste(A, ALPHA[z], [kf("position", t, f_alpha(t), 0, 0) for t in T])
    return {"uuid": nuid(), "name": nom, "loop": "once", "override": False, "length": L, "snapping": 24, "selected": False, "animators": A}


# attack : embrasement bref (halo et colonnes grandissent, opacité au maximum) ; hurt : l'aura vacille et baisse.
attack = ponctuel("attack", lambda t: 1 + 0.28 * bump(t, 0, 0.07, 0.2, 0.7), lambda t: 1 + 0.3 * bump(t, 0, 0.1, 0.25, 0.75),
                  lambda t: 0.2 * bump(t, 0, 0.05, 0.2, 0.7))
tremb = lambda t: math.sin(2 * math.pi * t * 6 / 0.8) * (1 - sm(t, 0.05, 0.7))
hurt = ponctuel("hurt", lambda t: 1 - 0.1 * bump(t, 0, 0.05, 0.2, 0.7), lambda t: 1 - 0.15 * bump(t, 0, 0.05, 0.25, 0.75),
                lambda t: -0.45 * abs(tremb(t)),
                lambda t, z: (0.5 * tremb(t) * (1 if list(ZONES).index(z) % 2 else -1), 0, 0))

# overlay_flux : film des colonnes (ctrl_uv, pas entiers d'une image), rotation lente des disques et de l'anneau.
LO = 8.0
A = {}
for (g, uvg, t, i) in COLS:
    w = COL[t][0]
    fps = 10 + (i % 3)                                # 80, 88 ou 96 images par boucle de 8 s : film fermé (multiple de FR)
    piste(A, uvg, [kf("position", 0, f"math.floor(math.mod(q.anim_time*{fps}+{i * 3},{FR}))*{w}", 0, 0)])
for j, g in enumerate(DISQUES):
    sens = 1 if j % 2 else -1
    piste(A, g, [kf("rotation", 0, 0, 0, f"q.anim_time*{s(sens * 360 * (1 + j % 2) / LO)}")])
piste(A, SOL, [kf("rotation", 0, 0, "q.anim_time*45", 0)])
overlay = {"uuid": nuid(), "name": "overlay_flux", "loop": "loop", "override": False, "length": LO, "snapping": 24, "selected": False,
           "animators": A}

# Étincelle : scintille (échelle), sans rotation pour rester face caméra.
PF = 0.6
pt = [i * PF / 12 for i in range(13)]
p_fall = {"uuid": nuid(), "name": "particle_etincelle_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24,
          "selected": False, "animators": {PART.uuid: {"name": PART.nom, "type": "bone", "keyframes":
              [kf("scale", t, *([1 + 0.3 * math.sin(2 * math.pi * t / PF)] * 3)) for t in pt]}}}

ANIMS = STATES + [attack, hurt, overlay, p_fall]
assert len(EMITS) <= 32
assert 20 <= len(elements) <= 150, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
# Particules Minecraft mal placées en jeu (bug du mod, 2026-11-04) : remplacées par une vapeur modélisée.
from particules import remplacer_emit_mc
remplacer_emit_mc(model, {"dust_ff3a28_10": None})
from sons import limiter_sons
from ambiance import ajouter_ambiance
limiter_sons(model)
ajouter_ambiance(model)
assert len(model["animations"]) <= 16, len(model["animations"])

os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


def ngroupes(n):
    return 1 + sum(ngroupes(c) for c in n.get("children", []) if isinstance(c, dict))


print(len(elements), "cubes ;", sum(ngroupes(n) for n in model["outliner"]), "groupes ; profondeur", max(depth(n) for n in model["outliner"]), ";",
      len(model["animations"]), "anims ;", sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()), "keyframes ;",
      os.path.getsize(OUT) // 1024, "Ko ;", len(EMITS), "emit_")
