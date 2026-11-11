"""Marteau du tonnerre : skin d'objet (guide 14) pour toutes les masses du joueur, ensemble Orage (thème Éléments). Design original.
Écrit skin_masse_orage.png, skin_masse_orage_e.png et .build/skin_masse_orage_brut.bbmodel à côté de ce script.

Construction (grammaire des marteaux de guerre, `.claude/references/objets/marteaux-masses.md`) :
- tête en **tambour** couchée en travers du manche (laque bleu nuit cloutée d'or, cerclée d'or à chaque bout) : rappelle les
  tambours des Dompteurs d'orage ;
- d'un côté, la **face de frappe** : fer évasé, chanfrein trempé (fil blanc, poli, cuivre, violet), médaillon aux trois
  virgules d'or, œil de cristal d'orage serti au centre (source de lumière) ; de l'autre, une **couronne-paratonnerre** de
  quatre dents à pointes de cristal (arcs entre elles) ;
- au-dessus, une **pointe-paratonnerre** (douille, bague d'or, tige, pointe de cristal) dans l'axe du manche ;
- manche de métal d'orage armé de quatre attelles sous la tête, bague d'or, fusée de cuir bleu nuit lacée d'or, pommeau
  d'or à pointe de cristal (famille des outils d'orage).
Silhouette en T épais, sans lame.

**Vrai volume** (retour en jeu du 2026-11-08 14 h 22 : « c'est des couches » ; recette `.claude/references/objets/volume-3d.md`,
validée sur l'épée) : la version d'avant faisait chaque pièce ronde de deux carrés croisés (une étoile à 8 pointes), et la tête
se lisait comme une pile de disques étoilés. Toute pièce ronde est maintenant un **tour** : un profil (b, rayon) dont chaque
tronçon est une couronne de pans (16 pour la tête, 8 pour le manche, les dents et la pointe), un pan = une plaque de 0,3 px
posée sur la surface (face extérieure peinte, découpée en trapèze par l'alpha, tranches transparentes). Le volume est fermé
par sa peau ; rien ne se voit à travers. Chanfreins à chaque changement de rayon (bagues d'or biseautées), **gouttière de
foudre creusée** tout autour du tambour (parois à lèvre claire + `_e`, fond sombre où la foudre est couchée : cœur opaque +
`_e`, gaine `add_`), face de frappe en tronc de cône à chanfrein trempé, pointes de cristal à facettes. Couleurs portées par
les faces (aucun décor peint sur une plaque flottante).

Repère (catégorie objets, Recette) : comme l'image vanilla de la masse (`mace.png`), en diagonale, tête en haut à droite vue
de +Z ; construit dans un repère local (a le long du manche, b en travers dans le plan de l'image, z vers le spectateur), puis
posé sur la diagonale. La prise (a = 3,5) tombe sur le point du poing calculé par l'inverse de `objet.matrice_main`. Display :
préréglage `_MASSE` de `tools/objet.py` (`item/handheld_mace` du jar), `gui` 0,76. Longueur ~27 px. Une étape : `repos`.

Foudre (fiche `.claude/references/effets/foudre.md`) : traits en géométrie, cœur **opaque** blanc à bord bleu + calque `_e`,
gaine `add_` bleu-violet. Les éclairs sont **repliés à 1/10 dans la tête** (pivots dans le volume fermé, contrôlé à la
génération) au repos et dépliés par l'échelle (×10) quand ils frappent ; chaque groupe n'est déplié que par une animation.

Objet vivant (guide 14), format free :
- item_idle (4 s, boucle) : arcs au hasard entre les dents de la couronne et sur le tambour (Molang sur q.life_time +
  q.instance_seed, 8 Hz, ~1,5 arc/s en tout, 125 ms chacun) ; l'œil respire (ctrl_lumiere) ; étincelles coupées ;
- event_select (0,6 s) : la pointe-paratonnerre appelle la foudre (trois arcs en retour à 60 ms), éclat à la pointe, la tête
  frémit, l'œil s'allume ;
- event_hit (0,55 s) : la décharge part de la face de frappe : trois éclairs ramifiés, éclat sur la face, gerbe d'étincelles
  (emit_mc_electric_spark + ctrl_emit), la tête recule d'un frisson ; **seul son** (embarqué original `decharge_masse`).
Pas d'item_swing (repli item_idle), pas d'item_gui (figé), item_ground = item_idle.
Fonctions avancées : add_, calque _e, ctrl_lumiere (non simulé), ctrl_emit + emit_mc_electric_spark (non simulés), son
embarqué, scale animé, Molang (q.life_time, q.instance_seed). À juger en jeu : event_hit et son son, la tête en volume de
près et dans la case, les étincelles quand les animations sont coupées (4/s, voir reglages.json).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

AVEC_E = True
NOM = "skin_masse_orage"
TEX = 512
DENS = 16.0              # texels par px sur les pans
TH = 0.3                 # épaisseur d'un pan
TAU = 2 * math.pi
K = 0.1                  # repli des éclairs au repos (échelle 1/10 autour d'un pivot dans la tête)
KU = 1 / K

# ------------------------------------------------------------------ palette (fiche orage.md)
METAL = np.array([(22, 24, 36), (46, 52, 72), (70, 78, 104), (112, 122, 154), (170, 182, 214)], np.float32)
OR = np.array([(130, 90, 30), (176, 128, 44), (220, 170, 60), (255, 230, 140)], np.float32)
CRIS = np.array([(40, 40, 120), (60, 76, 190), (100, 130, 240), (150, 180, 255), (200, 216, 255), (236, 242, 255)], np.float32)
LAQUE0, LAQUE1 = np.array((14, 18, 44), np.float32), np.array((44, 56, 112), np.float32)
LEVRE, LEVRE_E = np.array((214, 226, 250), np.float32), np.array((120, 156, 236), np.float32)
CUIVRE, VIOLET = np.array((190, 112, 62), np.float32), np.array((96, 62, 156), np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


def C(c):
    return np.asarray(c, np.float32)


# ------------------------------------------------------------------ tuiles (atlas rempli après la géométrie)
TUILES = {}              # nom -> (rgba, e ou None)


def tuile(nom, rgba, e=None):
    if nom not in TUILES:
        TUILES[nom] = (rgba, e)
    return nom


def _rgba(col, mask, em=None):
    H, W = mask.shape
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    out[..., 3] = mask * 255
    out[~mask, :3] = 0
    e = None
    if em is not None:
        m = mask & (em.max(axis=2) > 0)
        e = np.zeros((H, W, 4), np.uint8)
        e[..., :3] = np.clip(em, 0, 225).astype(np.uint8)
        e[..., 3] = m * 255
        e[~m, :3] = 0
    return out, e


# --- peintres des pans : xn en travers (-1..1, bords du pan), t le long (0 = P0, 1 = P1), y en px depuis P0, r le rayon
def p_metal(xn, t, y, r, L, ex):
    k = np.clip(0.42 + 0.3 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    col = lerp(METAL[1], METAL[4], (k ** 1.3)[..., None]) * (1 + 0.04 * np.sin(y * 41 + xn * 2))[..., None]
    col = np.where((np.abs(xn) > 0.88)[..., None], col * 1.12, col)          # arête claire entre deux pans
    return col, None


def p_or(xn, t, y, r, L, ex):
    k = np.clip(0.38 + 0.5 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    return lerp(OR[0], OR[3], (k ** 1.1)[..., None]), None


def p_sombre(xn, t, y, r, L, ex):
    return np.broadcast_to(METAL[0], xn.shape + (3,)).copy(), None


def p_laque(xn, t, y, r, L, ex):
    """Laque du tambour ; `levre` = bout côté gouttière ('p0'/'p1') : lèvre polie + _e puis liseré d'or ; `clou` : clou d'or."""
    col = lerp(LAQUE0, LAQUE1, (0.35 + 0.55 * (1 - np.abs(xn)) ** 0.8)[..., None]) * (1 + 0.04 * np.sin(y * 23))[..., None]
    col = np.where((np.abs(xn) > 0.9)[..., None], col * 1.25, col)
    dl = y if ex["levre"] == "p0" else L - y
    em = np.zeros(xn.shape + (3,), np.float32)
    lev = dl < 0.1
    col = np.where(lev[..., None], LEVRE, col)
    em[lev] = LEVRE_E
    col = np.where(((dl > 0.17) & (dl < 0.3))[..., None], lerp(OR[1], OR[3], (1 - np.abs(xn))[..., None] * 0.8), col)
    col = np.where((L - dl < 0.07)[..., None], col * 0.55, col)              # ombre au pied de la bague
    if ex.get("clou"):
        w = ex["w"]
        d = np.hypot(xn * w / 2, dl - 0.6 * L)
        col = np.where((d < 0.26)[..., None], METAL[0], col)
        col = np.where((d < 0.2)[..., None], lerp(OR[2], OR[3], np.clip(1 - d / 0.2, 0, 1)[..., None]), col)
    return col, em


def p_mur(xn, t, y, r, L, ex):
    """Paroi de la gouttière : sombre, lèvre claire + _e au bord haut (rayon du tambour)."""
    k = np.clip((r - ex["rmin"]) / max(ex["rmax"] - ex["rmin"], 1e-6), 0, 1)
    col = lerp(METAL[0], METAL[2], (k ** 1.5)[..., None])
    em = np.zeros(xn.shape + (3,), np.float32)
    lev = r > ex["rmax"] - 0.08
    col = np.where(lev[..., None], LEVRE, col)
    em[lev] = LEVRE_E * 0.8
    return col, em


def p_fond(xn, t, y, r, L, ex):
    col = lerp(METAL[0], C((26, 32, 70)), (1 - np.abs(t * 2 - 1))[..., None])
    return col, None


def p_trempe(xn, t, y, r, L, ex):
    """Chanfrein de la face de frappe, du fer (t = 0) au bord de la face (t = 1) : acier, violet, cuivre, poli, fil blanc."""
    acier = lerp(METAL[2], METAL[3], (1 - np.abs(xn))[..., None])
    col = acier
    col = np.where(((t > 0.28) & (t <= 0.47))[..., None], VIOLET, col)
    col = np.where(((t > 0.47) & (t <= 0.66))[..., None], CUIVRE, col)
    col = np.where(((t > 0.66) & (t <= 0.86))[..., None], C((196, 206, 228)), col)
    em = np.zeros(xn.shape + (3,), np.float32)
    fil = t > 0.86
    col = np.where(fil[..., None], C((246, 248, 255)), col)
    em[fil] = (170, 196, 250)
    return col, em


def p_cris(xn, t, y, r, L, ex):
    k = np.clip(0.3 + 0.55 * (t if ex.get("vers_p1", True) else 1 - t) + 0.25 * (1 - np.abs(xn)), 0, 1)
    col = CRIS[np.clip((k * 5.4).astype(int), 0, 5)]
    col = np.where((np.abs(xn) > 0.85)[..., None], col * 1.15, col)
    return col, np.clip(col * 0.82, 0, 225)


def p_poignee(xn, t, y, r, L, ex):
    """Cuir bleu nuit lacé d'or (y en px le long du manche)."""
    cuir = lerp(LAQUE1 * 0.75, LAQUE1 * 1.6, (0.25 + 0.6 * (1 - np.abs(xn)))[..., None])
    tours = np.mod(y * 3.2 + xn * 0.25, 1) < 0.14
    cuir = np.where(tours[..., None], cuir * 0.7, cuir)
    ph = y * 1.25
    lac = (np.abs(np.mod(ph + xn * 0.5, 1) - 0.5) < 0.09) | (np.abs(np.mod(ph - xn * 0.5, 1) - 0.5) < 0.09)
    col = np.where(lac[..., None], lerp(OR[1], OR[3], (1 - np.abs(xn))[..., None]), cuir)
    return col, None


PEINTRES = {"metal": p_metal, "or": p_or, "sombre": p_sombre, "laque": p_laque, "mur": p_mur, "fond": p_fond,
            "trempe": p_trempe, "cris": p_cris, "poignee": p_poignee}
OVL, OVW = 0.04, 0.03     # recouvrement en long et en travers entre pans voisins


def tuile_pan(nom, mat, L, w0, w1, r0, r1, ex):
    """Tuile d'un pan trapézoïdal : rangée 0 = bout P1 (haut de la face south), colonne 0 = côté -X."""
    wm = max(w0, w1) + 2 * OVW
    Lf = L + 2 * OVL
    Wt, Ht = max(2, int(math.ceil(wm * DENS))), max(2, int(math.ceil(Lf * DENS)))
    yy, xx = np.mgrid[0:Ht, 0:Wt]
    x = ((xx + 0.5) / Wt - 0.5) * wm
    y = Lf * (1 - (yy + 0.5) / Ht) - OVL
    t = np.clip(y / max(L, 1e-6), 0, 1)
    hw = (w0 + (w1 - w0) * t) / 2 + OVW
    mask = np.abs(x) <= hw
    xn = np.clip(x / np.maximum(hw - OVW, 1e-3), -1, 1)
    r = r0 + (r1 - r0) * t
    col, em = PEINTRES[mat](xn, t, y, r, L, dict(ex, w=max(w0, w1)))
    return tuile(nom, *_rgba(col, mask, em))


def t_medaillon(Ra, N=72):
    """Disque de la face de frappe, découpé en 16 pans (apothème Ra) : fer, liseré d'or, trois virgules d'or, logement sombre
    de l'œil. Coordonnées normalisées par la « norme » du polygone (les anneaux suivent les pans)."""
    R = Ra / math.cos(math.pi / 16)
    yy, xx = np.mgrid[0:N, 0:N]
    x, y = ((xx + 0.5) / N * 2 - 1) * R, (1 - (yy + 0.5) / N * 2) * R
    ph = np.mod(np.arctan2(y, x), TAU / 16) - TAU / 32
    rho = np.hypot(x, y) * np.cos(ph) / Ra                 # 1 sur le bord du 16-gone
    rr = np.hypot(x, y) / Ra
    disc = rho <= 1.0 + 0.01
    tom = np.zeros(x.shape, bool)
    xs, ys = x / Ra, y / Ra
    for kk in range(3):
        a0 = math.radians(90 + 120 * kk)
        tom |= np.hypot(xs - 0.5 * math.cos(a0), ys - 0.5 * math.sin(a0)) < 0.16
        for j in range(1, 16):
            aj, rj = a0 + math.radians(8 * j), 0.5 + 0.012 * j
            tom |= np.hypot(xs - rj * math.cos(aj), ys - rj * math.sin(aj)) < 0.16 * (1 - j / 16.5)
    sh = np.clip(0.55 + 0.3 * ys - 0.2 * rr, 0, 1)[..., None]
    col = lerp(METAL[1], METAL[3], sh)
    col = np.where(((rho > 0.86) & (rho <= 1.02))[..., None], lerp(OR[1], OR[3], sh), col)
    col = np.where(((rho > 0.8) & (rho <= 0.86))[..., None], METAL[0], col)
    col = np.where(tom[..., None], lerp(OR[0], OR[3], np.clip(sh + 0.1, 0, 1)), col)
    col = np.where((rr < 0.36)[..., None], METAL[0], col)
    return tuile("medaillon", *_rgba(col, disc))


def t_attelle(W=64, H=8):
    yy, xx = np.mgrid[0:H, 0:W]
    x, y = (xx + 0.5) / W, (yy + 0.5) / H
    col = lerp(METAL[2], METAL[4], np.clip(0.75 - 0.45 * y + 0.25 * (y < 0.12), 0, 1)[..., None])
    riv = np.zeros(x.shape, bool)
    for u in (0.12, 0.45, 0.8):
        riv |= np.hypot((x - u) * W / H, y - 0.5) < 0.3
    col = np.where(riv[..., None], OR[3], col)
    col = np.where((np.abs(y - 0.5) > 0.4)[..., None], METAL[0], col)
    return tuile("attelle", *_rgba(col, np.ones(x.shape, bool)))


CORE_C, CORE_B = (236, 244, 255), (96, 146, 255)
CORE_EC, CORE_EB = (205, 226, 255), (50, 84, 210)


def t_core():
    a = np.zeros((6, 16, 4), np.uint8)
    a[..., :3] = CORE_C
    a[0, :, :3] = a[5, :, :3] = CORE_B
    a[..., 3] = 255
    e = a.copy()
    e[..., :3] = CORE_EC
    e[0, :, :3] = e[5, :, :3] = CORE_EB
    return tuile("core", a, e)


def t_halo():
    a = np.zeros((8, 16, 4), np.uint8)
    for v in range(8):
        d = abs((v + 0.5) / 8 * 2 - 1)
        k = (1 - d) ** 1.4
        a[v, :, :3] = np.array((8, 7, 30)) + k * np.array((26, 44, 120))
    a[..., 3] = 255
    return tuile("halo", a)


def t_star(N=32, ss=4):
    yy, xx = np.mgrid[0:N * ss, 0:N * ss]
    x, y = (xx + 0.5) / (N * ss) * 2 - 1, 1 - (yy + 0.5) / (N * ss) * 2
    r = np.hypot(x, y)
    ray = np.exp(-np.abs(x) * 14) * np.clip(1 - np.abs(y), 0, 1) + np.exp(-np.abs(y) * 14) * np.clip(1 - np.abs(x), 0, 1)
    glow = np.clip(1 - r, 0, 1) ** 2.2
    core = np.clip(1 - r / 0.22, 0, 1)
    I = np.clip(0.55 * glow + 0.7 * ray + 0.9 * core, 0, 1)
    img = I[..., None] * np.array((150, 190, 255))
    img = np.clip(img + (core[..., None] ** 0.7) * np.array((100, 60, 0)), 0, 255).astype(np.uint8)
    im = np.array(Image.fromarray(img, "RGB").resize((N, N), Image.LANCZOS))
    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = im
    out[..., 3] = (im.max(axis=2) > 14) * 255
    out[out[..., 3] == 0, :3] = 0
    return tuile("star", out)


t_core(), t_halo(), t_star(), t_attelle()
CLEAR = "CLEAR"
# ------------------------------------------------------------------ repère
def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


A_W = unit(V(1, 1, 0))           # a : le long du manche, vers la tête (haut à droite vue de +Z)
B_W = unit(V(-1, 1, 0))          # b : en travers (côté +b = face de frappe, en haut à gauche)
Z_W = V(0, 0, 1)
RG = np.column_stack([A_W, B_W, Z_W])
A_PRISE = 3.5
POING = V(3.66, 3.74, 8.0)       # point du poing (inverse de objet.matrice_main, Display vanilla de la masse, bras au repos)
G0 = POING - A_PRISE * A_W


def W(a, b=0.0, z=0.0):
    return G0 + a * A_W + b * B_W + z * Z_W


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx (ordre du mod et du renderer)."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if abs(R[2, 0]) > 0.99999:                     # blocage de cardan (Y = ±90°) : Z = 0, tout l'angle sur X
        return math.degrees(math.atan2(-R[1, 2], R[1, 1])), math.degrees(ry), 0.0
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def rmat(rx, ry, rz):
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def group(name, origin, parent=None, repli=None, rotation=(0, 0, 0)):
    """repli = pivot (monde) : tout le sous-groupe est replié à K autour de lui (éclair caché dans la tête au repos)."""
    assert name not in groups, name
    assert len(name) <= 64
    ct = repli if repli is not None else (groups[parent]["ct"] if parent else None)
    o = np.asarray(origin, float)
    if repli is None and ct is not None:
        o = ct + K * (o - ct)
    groups[name] = {"origin": [round(float(v), 3) for v in o], "uuid": nuid(), "ids": [], "parent": parent, "ct": ct,
                    "rotation": list(rotation)}
    return name


def cube_c(g, name, c, h, R, faces):
    """Cube de centre c (monde), demi-tailles h, axes R (colonnes), faces {face: CLEAR | (tuile, (u0, v0, u1, v1) en fractions)}."""
    c, h = np.asarray(c, float), np.asarray(h, float)
    ct = groups[g]["ct"]
    if ct is not None:
        c, h = ct + K * (c - ct), h * K
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in c - h],
         "to": [round(float(v), 4) for v in c + h], "origin": [round(float(v), 4) for v in c], "box_uv": False,
         "faces": {f: {"uv": uv, "texture": 0} for f, uv in faces.items()}}
    rot = euler(R)
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])
    return e


def T(tile, u0=0.0, v0=0.0, u1=1.0, v1=1.0):
    return (tile, (u0, v0, u1, v1))


SIX = ("north", "south", "east", "west", "up", "down")


# --- tour : profil (b, rayon) autour d'un axe, une couronne de n pans par tronçon
def tour(g, nom, O, ax, ref, profil, n=16, phase=0.0):
    """profil = [(b0, r0, b1, r1, mat, ex), ...] parcouru dans le sens +ax, le plein du côté de l'axe (rayon = apothème).
    `mat` peut être une paire (pans alternés). Chaque pan : plaque de TH px, face extérieure (south) sur la surface."""
    O, ax = np.asarray(O, float), unit(np.asarray(ax, float))
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    for i, (b0, r0, b1, r1, mat, ex) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        if L < 1e-4:
            continue
        mats = mat if isinstance(mat, tuple) else (mat,)
        exs = ex if isinstance(ex, tuple) else (ex,) * len(mats)
        tiles = [tuile_pan(f"{nom}{i}{'ab'[j]}", m, L, 2 * r0 * tn, 2 * r1 * tn, r0, r1, exs[j]) for j, m in enumerate(mats)]
        db, dr = (b1 - b0) / L, (r1 - r0) / L
        wm = max(2 * r0 * tn, 2 * r1 * tn) + 2 * OVW
        for k in range(n):
            th = phase + TAU * k / n
            e = math.cos(th) * ref + math.sin(th) * w3
            P0, P1 = O + b0 * ax + r0 * e, O + b1 * ax + r1 * e
            Y = unit(P1 - P0)
            N = -dr * ax + db * e
            X = np.cross(Y, N)
            c = (P0 + P1) / 2 - N * TH / 2
            faces = {f: CLEAR for f in SIX}
            faces["south"] = T(tiles[k % len(tiles)])
            cube_c(g, f"{nom}{i}_{k}", c, (wm / 2, L / 2 + OVL, TH / 2), np.column_stack([X, Y, N]), faces)


def bague(b0, b1, ra, rb, ro, mat="or", c=0.13, ex=None):
    """Bague biseautée : du rayon ra (b0) monte à ro, palier, redescend à rb (b1)."""
    ex = ex or {}
    return [(b0, ra, b0 + c, ro, mat, dict(ex, clair=0.12)), (b0 + c, ro, b1 - c, ro, mat, ex), (b1 - c, ro, b1, rb, mat, dict(ex, clair=-0.1))]


def disque(g, nom, c, N, up, Ra, tile):
    """Disque à 16 pans (apothème Ra) : plaque dont seule la face extérieure (normale N) est peinte."""
    N = unit(np.asarray(N, float))
    Y = unit(up - (up @ N) * N)
    X = np.cross(Y, N)
    R = Ra / math.cos(math.pi / 16)
    faces = {f: CLEAR for f in SIX}
    faces["south"] = T(tile)
    cube_c(g, nom, np.asarray(c, float) - N * TH / 2, (R, R, TH / 2), np.column_stack([X, Y, N]), faces)


def plaque(g, name, c, n, up, w, h, tile, th=0.3):
    """Plaque fine de normale n (image des deux côtés, tranches transparentes) : éclats additifs seulement."""
    n = unit(np.asarray(n, float))
    up = unit(up - (up @ n) * n)
    X = np.cross(up, n)
    R = np.column_stack([X, up, n])
    cube_c(g, name, c, (w / 2, h / 2, th / 2), R, {"south": T(tile), "north": T(tile, 1, 0, 0, 1), "east": CLEAR, "west": CLEAR,
                                                 "up": CLEAR, "down": CLEAR})


# --- foudre
ROLLS = [18, 52, 31, 66, 9, 44, 75, 24]
_rc = [0]


def seg(g, name, a, b, w, tile, ov, Y=None, wz=None):
    a, b = np.asarray(a, float), np.asarray(b, float)
    X = unit(b - a)
    if Y is None:
        ref = Z_W if abs(X @ Z_W) < 0.9 else A_W
        Y = unit(ref - (ref @ X) * X)
        Zc = np.cross(X, Y)
        rl = math.radians(ROLLS[_rc[0] % len(ROLLS)])
        _rc[0] += 1
        Y, Zc = math.cos(rl) * Y + math.sin(rl) * Zc, -math.sin(rl) * Y + math.cos(rl) * Zc
    else:
        Y = unit(Y - (Y @ X) * X)
        Zc = np.cross(X, Y)
    L = float(np.linalg.norm(b - a))
    cap = T(tile, 2 / 16, 1 / 6, 4 / 16, 5 / 6) if tile == "core" else CLEAR
    cube_c(g, name, (a + b) / 2, (L / 2 + ov, w / 2, (w if wz is None else wz) / 2), np.column_stack([X, Y, Zc]),
           {"north": T(tile), "south": T(tile), "up": T(tile), "down": T(tile), "east": cap, "west": cap})


def zigzag(P0, P1, n, J, seed, zj=0.25):
    """Points d'un éclair de P0 à P1 (monde) : n tronçons irréguliers, écarts latéraux alternés (angles vifs)."""
    rng = np.random.default_rng(seed)
    P0, P1 = np.asarray(P0, float), np.asarray(P1, float)
    d = P1 - P0
    L = np.linalg.norm(d)
    X = d / L
    N1 = unit(np.cross(X, Z_W)) if abs(X @ Z_W) < 0.9 else A_W
    N2 = np.cross(X, N1)
    pts = [P0]
    sg = rng.choice((-1, 1))
    for i in range(1, n):
        along = (i + rng.uniform(-0.25, 0.25)) / n
        off = sg * rng.uniform(0.45, 1.0) * J * (1 - 0.3 * i / n)
        sg = -sg
        pts.append(P0 + d * along + N1 * off + N2 * rng.uniform(-zj, zj))
    pts.append(P1)
    return pts


def trait(gc, gh, name, pts, w0, w1, halo=2.2):
    n = len(pts) - 1
    for i in range(n):
        w = w0 + (w1 - w0) * i / max(1, n - 1)
        seg(gc, f"{name}c{i}", pts[i], pts[i + 1], w, "core", 0.1)
        seg(gh, f"{name}h{i}", pts[i], pts[i + 1], w * halo + 0.12, "halo", 0.04)


def on_poly(pts, t):
    P = [np.asarray(p, float) for p in pts]
    ls = [np.linalg.norm(P[i + 1] - P[i]) for i in range(len(P) - 1)]
    x = t * sum(ls)
    for i, l in enumerate(ls):
        if x <= l or i == len(ls) - 1:
            return P[i] + (P[i + 1] - P[i]) * min(1.0, x / max(l, 1e-9))
        x -= l


def eclair(nom, parent, pivot, pts, w0, w1):
    """Groupe d'éclair replié autour de `pivot` : cœur opaque (+ _e) dans `nom`, gaine dans `add_<nom>`."""
    g = group(nom, pivot, parent=parent, repli=np.asarray(pivot, float))
    h = group(f"add_{nom}", pivot, parent=g)
    trait(g, h, nom, pts, w0, w1)
    return g


def eclat(nom, parent, pivot, c, r):
    """Éclat (étoile additive) replié autour de `pivot` : trois plaques croisées (cam_ n'est pas annoncé pour les objets)."""
    g = group(nom, pivot, parent=parent, repli=np.asarray(pivot, float))
    ag = group(f"add_{nom}", c, parent=g)
    for k_, (n, up) in enumerate(((Z_W, A_W), (A_W, B_W), (B_W, Z_W))):
        plaque(ag, f"{nom}{k_}", np.asarray(c, float), n, up, 2 * r, 2 * r, "star", th=0.3 + 0.02 * k_)
    return g


# ---- cotes (repère local a, b, z ; px)
A_TETE = 18.0            # centre du tambour
R_TAMB = 2.25            # apothème du tambour
R_CER = 2.47             # cercles d'or
R_FOND = 1.85            # fond de la gouttière
G_B = 0.35               # demi-largeur de la gouttière
R_FACE = 1.85            # apothème de la face de frappe
B_FACE = 4.7
A_POINTE = A_TETE + 7.3

# profil de la tête le long de b (de la couronne à la face de frappe)
PROFIL_TETE = (
    [(-4.2, 0.0, -4.2, 1.3, "metal", {}),
     (-4.2, 1.3, -3.98, 1.72, "or", {"clair": 0.12}), (-3.98, 1.72, -3.66, 1.72, "or", {}),
     (-3.66, 1.72, -3.5, 1.95, "metal", {"clair": 0.1}), (-3.5, 1.95, -3.1, 1.95, "metal", {})]
    + bague(-3.1, -2.6, 1.95, R_TAMB, R_CER, c=0.15)
    + [(-2.6, R_TAMB, -G_B, R_TAMB, ("laque", "laque"), ({"levre": "p1", "clou": True}, {"levre": "p1"})),
       (-G_B, R_TAMB, -G_B, R_FOND, "mur", {"rmin": R_FOND, "rmax": R_TAMB}),
       (-G_B, R_FOND, G_B, R_FOND, "fond", {}),
       (G_B, R_FOND, G_B, R_TAMB, "mur", {"rmin": R_FOND, "rmax": R_TAMB}),
       (G_B, R_TAMB, 2.6, R_TAMB, ("laque", "laque"), ({"levre": "p0", "clou": True}, {"levre": "p0"}))]
    + bague(2.6, 3.1, R_TAMB, 1.95, R_CER, c=0.15)
    + [(3.1, 1.95, 3.8, 1.95, "metal", {}),
       (3.8, 1.95, 4.2, 2.3, "metal", {"clair": 0.12}),
       (4.2, 2.3, 4.35, 2.3, "or", {}),
       (4.35, 2.3, B_FACE, R_FACE, "trempe", {})])


def r_tete(b):
    """Rayon intérieur (apothème) de la tête à l'abscisse b (contrôle des éclairs repliés)."""
    for b0, r0, b1, r1, *_ in PROFIL_TETE:
        if b0 <= b <= b1 and b1 > b0:
            return r0 + (r1 - r0) * (b - b0) / (b1 - b0)
    return -1.0


def build():
    racine = group("repos", W(3.5))
    manche = group("manche", W(3.5), parent=racine)
    # --- manche : tour à 8 pans le long de a (pommeau à pointe de cristal, fusée lacée, bague, hampe, douille)
    prof_m = ([(-1.75, 0.0, -1.0, 0.42, "cris", {}), (-1.0, 0.42, -0.42, 0.5, "cris", {"vers_p1": False})]
              + [(-0.42, 0.5, -0.27, 0.95, "or", {"clair": 0.12}), (-0.27, 0.95, 0.3, 0.98, "or", {}),
                 (0.3, 0.98, 0.45, 0.82, "or", {"clair": -0.1}), (0.45, 0.82, 0.55, 0.68, "sombre", {}),
                 (0.55, 0.68, 6.55, 0.68, "poignee", {})]
              + bague(6.55, 7.2, 0.68, 0.56, 0.86)
              + [(7.2, 0.56, 14.5, 0.56, "metal", {})]
              + bague(14.5, 14.95, 0.56, 0.92, 1.02)
              + [(14.95, 0.92, 16.3, 0.92, "metal", {"clair": 0.12})])
    tour(manche, "m", W(0), A_W, B_W, prof_m, n=8)
    # attelles (langets) sur quatre pans de la hampe, rivetées
    for i, (db, dz) in enumerate(((0, 1), (0, -1), (1, 0), (-1, 0))):
        off = 0.56 + 0.11
        p, q = W(10.8, db * off, dz * off), W(14.6, db * off, dz * off)
        nrm = db * B_W + dz * Z_W
        X = unit(q - p)
        Yv = unit(np.cross(nrm, X))
        cube_c(manche, f"attelle{i}", (p + q) / 2, (np.linalg.norm(q - p) / 2, 0.22, 0.11), np.column_stack([X, Yv, np.cross(X, Yv)]),
               {k: T("attelle") for k in ("north", "south", "up", "down")} | {"east": T("attelle", 0, 0.4, 0.06, 0.6),
                                                                            "west": T("attelle", 0, 0.4, 0.06, 0.6)})

    tete = group("tete", W(A_TETE), parent=racine)
    # --- tambour, cercles, fer et face de frappe : un seul tour à 16 pans le long de b
    tour(tete, "t", W(A_TETE), B_W, A_W, PROFIL_TETE, n=16)
    disque(tete, "medaillon", W(A_TETE, B_FACE), B_W, A_W, R_FACE + 0.02, t_medaillon(R_FACE + 0.02))
    oeil = group("oeil", W(A_TETE, B_FACE), parent=tete)
    group("ctrl_lumiere", W(A_TETE, B_FACE), parent=oeil)
    tour(oeil, "o", W(A_TETE, B_FACE), B_W, A_W, [(-0.2, 0.62, 0.3, 0.62, "cris", {}), (0.3, 0.62, 0.48, 0.38, "cris", {}),
                                                  (0.48, 0.38, 0.48, 0.0, "cris", {})], n=8, phase=math.pi / 8)
    # --- couronne-paratonnerre (-b) : quatre dents qui s'écartent, pointes de cristal, cristal central
    TIPS = []
    for i, (da, dz) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        p = W(A_TETE + da * 1.1, -3.85, dz * 1.1)
        q = W(A_TETE + da * 1.5, -5.0, dz * 1.5)
        d = unit(q - p)
        Lq = float(np.linalg.norm(q - p))
        tour(tete, f"d{i}", p, d, Z_W, [(0, 0.46, Lq, 0.34, "metal", {"clair": 0.1}), (Lq, 0.34, Lq + 0.1, 0.38, "or", {}),
                                       (Lq + 0.1, 0.38, Lq + 0.2, 0.3, "or", {}), (Lq + 0.2, 0.3, Lq + 0.95, 0.0, "cris", {})],
             n=8, phase=math.pi / 8)
        TIPS.append(p + d * (Lq + 0.95))
    tour(tete, "cc", W(A_TETE, -4.2), -B_W, A_W, [(-0.1, 0.5, 0.55, 0.5, "cris", {}), (0.55, 0.5, 1.35, 0.0, "cris", {})],
         n=8, phase=math.pi / 8)
    # --- pointe-paratonnerre (+a) : douille, bague d'or, tige, cristal à facettes
    prof_p = ([(1.6, 1.2, 2.95, 1.2, "metal", {"clair": 0.12}), (2.95, 1.2, 3.1, 0.95, "metal", {"clair": 0.2})]
              + bague(3.1, 3.55, 0.95, 0.62, 1.08)
              + [(3.55, 0.62, 5.0, 0.52, "metal", {})]
              + bague(5.0, 5.35, 0.52, 0.46, 0.64)
              + [(5.35, 0.46, 6.3, 0.42, "cris", {}), (6.3, 0.42, 7.3, 0.0, "cris", {})])
    tour(tete, "p", W(A_TETE), A_W, B_W, prof_p, n=8, phase=math.pi / 8)

    # --- gouttière : la foudre couchée au fond, tout autour du tambour (cœur opaque + _e, gaine add_)
    gout = group("foudre_gouttiere", W(A_TETE), parent=tete)
    gaine = group("add_gouttiere", W(A_TETE), parent=gout)
    rng = np.random.default_rng(5)
    NZ = 40
    pts = []
    for j in range(NZ + 1):
        th = TAU * j / NZ
        e = math.cos(th) * A_W + math.sin(th) * Z_W
        bz = (0.15 if j % 2 == 0 else -0.15) * (0.75 + 0.25 * rng.random()) if j < NZ else pts[0][1]
        pts.append((e, bz))
    for j in range(NZ):
        (e0, b0), (e1, b1) = pts[j], pts[j + 1]
        P0, P1 = W(A_TETE) + e0 * 2.0 + B_W * b0, W(A_TETE) + e1 * 2.0 + B_W * b1
        rad = unit(e0 + e1)
        seg(gout, f"gc{j}", P0, P1, 0.26, "core", 0.06, Y=rad)
        seg(gaine, f"gh{j}", P0, P1, 0.3, "halo", 0.03, Y=rad, wz=0.6)

    # --- crépitement (item_idle) : arcs entre dents voisines, un arc en travers, deux arcs sur le tambour
    piv_c = W(A_TETE, -3.3)
    ARCS = []
    for i in range(4):
        pa, pb = TIPS[i], TIPS[(i + 1) % 4]
        ARCS.append(eclair(f"arc_dent{i}", tete, piv_c, zigzag(pa, pb, 3, 0.45, 11 + i), 0.3, 0.3))
    ARCS.append(eclair("arc_dent_x", tete, piv_c, zigzag(TIPS[0], TIPS[2], 4, 0.5, 21), 0.3, 0.3))
    piv_t = W(A_TETE)
    for j, s in enumerate((1, -1)):
        pa = W(A_TETE + 0.6 * s, -2.95, s * (R_TAMB + 0.35))
        pb = W(A_TETE - 0.7 * s, 2.95, s * (R_TAMB + 0.35))
        ARCS.append(eclair(f"arc_tambour{j}", tete, piv_t, zigzag(pa, pb, 5, 0.7, 31 + j, zj=0.0), 0.3, 0.3))

    # --- décharge (event_hit) : trois éclairs partent de la face de frappe, ramifiés ; pivot caché dans le tambour
    piv_f = W(A_TETE, 1.6)
    face_c = W(A_TETE, B_FACE + 0.35)
    DECH, BRAN = [], []
    specs = [(0.0, 0.0, 11.5, 6, 1.0, 41), (28.0, 0.9, 8.5, 5, 0.8, 43), (-31.0, -0.8, 8.0, 5, 0.8, 47)]
    for i, (ang, dz, L, n, J, sd) in enumerate(specs):
        th = math.radians(ang)
        d = math.cos(th) * B_W + math.sin(th) * A_W
        start = face_c + A_W * math.sin(th) * 0.6
        end = start + d * L + Z_W * dz * 2.2
        pts_ = zigzag(start, end, n, J, sd)
        DECH.append(eclair(f"decharge{i}", tete, piv_f, pts_, 0.58 if i == 0 else 0.5, 0.32))
        for k_, (tb, ba, bl) in enumerate(((0.45, 35, 3.6), (0.72, -40, 2.6))[: 2 if i == 0 else 1]):
            p0 = on_poly(pts_, tb)
            sgn = 1 if (i + k_) % 2 == 0 else -1
            bd = unit(math.cos(math.radians(ba)) * d + math.sin(math.radians(ba)) * sgn * (A_W if i == 0 else np.cross(Z_W, d)) + Z_W * 0.25)
            bpts = zigzag(p0, p0 + bd * bl, 3, 0.35, sd + 7 * k_ + 3)
            BRAN.append(eclair(f"branche{i}_{k_}", tete, piv_f, bpts, 0.34, 0.3))
    ECL_F = eclat("eclat_face", tete, piv_f, face_c + B_W * 0.3, 1.9)
    em = group("emit_mc_electric_spark", face_c + B_W * 0.4, parent=tete, rotation=(0, 0, 45))
    group("ctrl_emit", face_c + B_W * 0.4, parent=em)

    # --- foudre qui tombe sur la pointe (event_select)
    piv_p = W(A_TETE + 0.4)
    tip_c = W(A_POINTE)
    ciel = zigzag(W(A_POINTE + 10.5, 0.8, 0.5), tip_c, 6, 1.1, 61)
    CIEL = [eclair("foudre_ciel", tete, piv_p, ciel, 0.55, 0.36)]
    p0 = on_poly(ciel, 0.35)
    CIELB = [eclair("foudre_ciel_b0", tete, piv_p, zigzag(p0, p0 + unit(-A_W + 0.8 * B_W) * 3.2, 3, 0.35, 67), 0.34, 0.3)]
    p1 = on_poly(ciel, 0.6)
    CIELB.append(eclair("foudre_ciel_b1", tete, piv_p, zigzag(p1, p1 + unit(-A_W - 0.9 * B_W + 0.3 * Z_W) * 2.4, 3, 0.3, 71), 0.3, 0.3))
    ECL_P = eclat("eclat_pointe", tete, piv_p, tip_c, 1.4)
    return {"racine": racine, "tete": tete, "oeil": oeil, "arcs": ARCS, "dech": DECH, "bran": BRAN, "eclat_f": ECL_F, "emit": em,
            "ciel": CIEL, "cielb": CIELB, "eclat_p": ECL_P}


F = build()


def node(name):
    g = groups[name]
    kids = [n for n, gg in groups.items() if gg["parent"] == name]
    nd = {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"], "children": g["ids"] + [node(k) for k in kids]}
    return nd


outliner = [node(F["racine"])]


def coins_de(e):
    f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
    R = rmat(*e.get("rotation", (0, 0, 0)))
    return [R @ (np.array([(f, t)[(i >> k) & 1][k] for k in range(3)]) - o) + o for i in range(8)]


def coins(only_visible=True):
    P = []
    caches = set()
    for n, g in groups.items():
        if g["ct"] is not None:
            caches.update(g["ids"])
    for e in elements:
        if only_visible and e["uuid"] in caches:
            continue
        P += coins_de(e)
    return np.array(P), caches


P, CACHES = coins()
LONGUEUR = float((P @ A_W).max() - (P @ A_W).min())
LARGEUR = float((P @ B_W).max() - (P @ B_W).min())

# contrôle : chaque éclair replié reste dans le volume fermé de la tête (tambour) ou de la pointe-paratonnerre
_hors = 0
_noms = set()
for e in elements:
    if e["uuid"] not in CACHES:
        continue
    for c in coins_de(e):
        a, b, z = (c - G0) @ A_W - A_TETE, (c - G0) @ B_W, (c - G0) @ Z_W
        dans_tete = math.hypot(a, z) < r_tete(b) * 0.97 - 0.05
        dans_pointe = (1.6 <= a <= 2.9 and math.hypot(b, z) < 0.95) or (1.6 <= a <= 5.0 and math.hypot(b, z) < 0.5)
        if not (dans_tete or dans_pointe):
            _hors += 1
            _noms.add(e["name"])
assert _hors == 0, f"{_hors} {sorted(_noms)} coins d'éclairs repliés hors du volume"
# ------------------------------------------------------------------ animations (objet vivant, guide 14)
def kf(ch, t, x, y=None, z=None, interp="linear"):
    y = x if y is None else y
    z = x if z is None else z
    f = lambda v: v if isinstance(v, str) else str(round(float(v) + 0.0, 4))
    return {"channel": ch, "data_points": [{"x": f(x), "y": f(y), "z": f(z)}], "time": round(t, 4), "interpolation": interp}


def anim(name, length, loop="loop"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "item_idle", "animators": {}}


def piste(an, g, keys):
    an["animators"][groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": keys}


def piste_ctrl(an, parent, nom, keys):
    u = next(gg["uuid"] for n, gg in groups.items() if gg["parent"] == parent and n == nom)
    an["animators"][u] = {"name": nom, "type": "bone", "keyframes": keys}


def creneaux(fen, L, haut=KU, bas=1.0, rampe=0.006, ch="scale"):
    """Échelle en créneaux : `fen` = [(t0, t1)] où l'éclair est déplié (×KU), replié ailleurs ; rampes de 6 ms."""
    keys = [kf(ch, 0.0, bas)]
    for t0, t1 in fen:
        keys += [kf(ch, max(t0, 0.0), bas), kf(ch, t0 + rampe, haut), kf(ch, t1, haut), kf(ch, t1 + rampe, bas)]
    keys.append(kf(ch, L, bas))
    out, seen = [], set()
    for k in keys:
        if k["time"] in seen:
            out = [o for o in out if o["time"] != k["time"]]
        seen.add(k["time"])
        out.append(k)
    return sorted(out, key=lambda k: k["time"])


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def H(x):
    return f"math.mod(math.abs(math.sin(({x})*127.1))*437.585,1)"


# item_idle (4 s) : crépitement au hasard (tirage par tranche de 125 ms), œil qui respire, étincelles coupées
L_IDLE = 4.0
idle = anim("item_idle", L_IDLE)
for i, g in enumerate(F["arcs"]):
    p = 0.025 if "dent" in g else 0.015          # ~1,5 arc/s en tout, écarts irréguliers (0,1 à 1,5 s)
    expr = f"({H(f'math.floor(q.life_time*8)*1.731+{0.37 + 17.3 * i:.2f}+q.instance_seed*17')}<{p})?{KU:g}:1"
    assert len(expr) <= 512
    piste(idle, g, [kf("scale", 0.0, expr)])
piste_ctrl(idle, F["oeil"], "ctrl_lumiere", [kf("position", t, 0.25 * math.sin(TAU * t / L_IDLE), 0, 0) for t in (0, 1, 2, 3, 4)])
piste_ctrl(idle, F["emit"], "ctrl_emit", [kf("position", 0.0, -1, 0, 0)])

# event_hit (0,55 s) : traceur, trois arcs en retour (60 ms, séparés de 60 ms), branches éteintes en premier, éclat, gerbe
L_HIT = 0.55
hit = anim("event_hit", L_HIT, "once")
for i, g in enumerate(F["dech"]):
    d0 = 0.012 * i
    piste(hit, g, [kf("scale", 0, 1), kf("scale", d0, 1), kf("scale", d0 + 0.03, KU), kf("scale", 0.09, KU), kf("scale", 0.096, 1),
                   kf("scale", 0.15, 1), kf("scale", 0.156, KU), kf("scale", 0.21, KU), kf("scale", 0.216, 1), kf("scale", 0.27, 1),
                   kf("scale", 0.276, KU), kf("scale", 0.33, KU), kf("scale", 0.336, 1), kf("scale", L_HIT, 1)])
for g in F["bran"]:
    piste(hit, g, creneaux([(0.03, 0.09), (0.15, 0.2)], L_HIT))
piste(hit, F["eclat_f"], [kf("scale", 0, 1), kf("scale", 0.02, KU * 1.15), kf("scale", 0.08, KU), kf("scale", 0.15, 1),
                          kf("scale", 0.16, KU * 0.7), kf("scale", 0.22, 1), kf("scale", 0.28, KU * 0.5), kf("scale", 0.33, 1),
                          kf("scale", L_HIT, 1)])
piste(hit, F["tete"], [kf("rotation", t, 0, 0, round(-3.5 * math.exp(-t / 0.09) * math.sin(TAU * t / 0.16), 3))
                       for t in [i * L_HIT / 22 for i in range(23)]])
piste_ctrl(hit, F["emit"], "ctrl_emit", [kf("position", 0, 8, 0, 0), kf("position", 0.25, 8, 0, 0), kf("position", 0.26, 0, 0, 0)])
piste_ctrl(hit, F["oeil"], "ctrl_lumiere", [kf("position", 0, 0, 0, 0), kf("position", 0.02, 1.5, 0, 0), kf("position", 0.12, 1.2, 0, 0),
                                            kf("position", L_HIT, 0, 0, 0)])
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": []}

# event_select (0,6 s) : la foudre tombe sur la pointe-paratonnerre, puis l'œil s'allume
L_SEL = 0.6
sel = anim("event_select", L_SEL, "once")
piste(sel, F["ciel"][0], creneaux([(0.04, 0.1), (0.16, 0.22), (0.28, 0.33)], L_SEL))
for g in F["cielb"]:
    piste(sel, g, creneaux([(0.04, 0.1), (0.16, 0.2)], L_SEL))
piste(sel, F["eclat_p"], [kf("scale", 0, 1), kf("scale", 0.04, 1), kf("scale", 0.05, KU * 1.1), kf("scale", 0.12, KU * 0.8),
                          kf("scale", 0.2, KU * 0.9), kf("scale", 0.34, 1), kf("scale", L_SEL, 1)])
piste(sel, F["tete"], [kf("rotation", t, 0, 0, round(2.5 * math.exp(-max(t - 0.05, 0) / 0.1) * math.sin(TAU * max(t - 0.05, 0) / 0.14), 3))
                       for t in [i * L_SEL / 24 for i in range(25)]])
piste_ctrl(sel, F["oeil"], "ctrl_lumiere", [kf("position", 0, -0.6, 0, 0), kf("position", 0.3, -0.6, 0, 0), kf("position", 0.38, 1.2, 0, 0),
                                            kf("position", L_SEL, 0, 0, 0)])

ANIMS = [idle, hit, sel]

# ------------------------------------------------------------------ atlas (tuiles des pans créées pendant la géométrie)
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_x = _y = _sh = 0
for n, (im, em) in sorted(TUILES.items(), key=lambda it: -it[1][0].shape[0]):
    h, w = im.shape[:2]
    if _x + w + 1 > TEX:
        _x, _y, _sh = 0, _y + _sh + 1, 0
    UV[n] = (_x, _y, _x + w, _y + h)
    tex[_y:_y + h, _x:_x + w] = im
    if em is not None:
        tex_e[_y:_y + h, _x:_x + w] = em
    _x += w + 1
    _sh = max(_sh, h)
assert _y + _sh <= TEX - 4, f"atlas plein ({_y + _sh})"
UV_CLEAR = [TEX - 3, TEX - 3, TEX - 1, TEX - 1]
tex[..., :3] &= 0xFC
assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
for e in elements:
    for f, fc in e["faces"].items():
        if fc["uv"] == CLEAR:
            fc["uv"] = UV_CLEAR
        else:
            nom, (u0, v0, u1, v1) = fc["uv"]
            a, b, c, d = UV[nom]
            fc["uv"] = [round(lerp(a, c, u0), 3), round(lerp(b, d, v0), 3), round(lerp(a, c, u1), 3), round(lerp(b, d, v1), 3)]


def b64(arr, path):
    im = Image.fromarray(arr, "RGBA")
    im.save(path, optimize=True)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


tex_b64 = b64(tex, f"{NOM}.png")
tex_e_b64 = b64(tex_e, f"{NOM}_e.png")

# ------------------------------------------------------------------ écriture
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
# Display : préréglage _MASSE (item/handheld_mace du jar) ; gui ramené à la case (boîte de la masse plus grande que 16 px)
GUI = 0.76
_cb = (P.min(axis=0) + P.max(axis=0)) / 2
GUI_T = [round(float(-(_cb[0] - 8) * GUI), 2), round(float(-(_cb[1] - 8) * GUI), 2), 0]
AFFICHAGE = objet.affichage("masse", gui={"translation": GUI_T, "scale": [GUI] * 3})
model = objet.modele(NOM, "masse", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, embarquer_sons
limiter_sons(model)
embarquer_sons(model, {"decharge_masse": "sons/decharge_masse.ogg"})
# Un seul son, au coup qui touche (event_hit) : tools/sons.py ne connaît pas encore les événements d'objet et retire tout son
# hors attack/event_equip ; on le remet ici, un seul.
hit["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "decharge_masse", "file": ""}], "time": 0.04}]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      len(TUILES), "tuiles")
print(f"longueur {LONGUEUR:.1f} px, largeur de tête {LARGEUR:.1f} px ; boîte visible {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)}")
