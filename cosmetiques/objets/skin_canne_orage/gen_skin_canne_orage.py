"""Canne du paratonnerre : skin d'objet (guide 14) pour toutes les cannes à pêche du joueur, ensemble Orage (thème Éléments).
Design original. Écrit skin_canne_orage.png, skin_canne_orage_e.png et .build/skin_canne_orage_brut.bbmodel à côté de ce script.

Construction (d'après une vraie canne à mouche, `.claude/references/objets/cannes-a-peche.md`) : talon (bouchon) d'or à pointe
de cristal, porte-moulinet d'acier serré entre deux bagues d'or, **moulinet = tambour d'or aux trois virgules** (flasques
cerclées d'or, médaillon à virgules sur chaque face, manivelle à bouton de cuir) suspendu sous la canne, poignée de cuir bleu
nuit lacée d'or, bague d'arrêt, **scion d'acier d'orage forgé qui s'affine en vraie section** (octogone de 1,2 px au talon,
0,5 px au bout) en trois brins joints par des viroles d'or, **anneaux d'or** (4 + un anneau de tête) ligaturés d'or, ligne
qui court du moulinet au bout dans les anneaux, tête d'or et **pointe de cristal-paratonnerre**. Sur la bobine du moulinet,
la ligne enroulée garde la foudre : gouttière entre les flasques, foudre couchée au fond (cœur + `_e`, gaine `add_`).
Au repos (`repos`), la ligne pend du bout comme sur l'image vanilla, avec un leurre d'or en éclair, une perle de cristal et
un hameçon ; lancée (`lancee`), la ligne est partie (le jeu dessine la sienne depuis le bout) et la pointe crépite.

**Vrai volume** (recette `.claude/references/objets/volume-3d.md`, technique des tours de `skin_masse_orage`) : toute pièce
ronde est un tour (profil (a, rayon), couronne de 8 ou 16 pans de 0,3 px posés sur la surface, face extérieure peinte et
découpée en trapèze par l'alpha, tranches transparentes) ; bagues biseautées à chaque changement de rayon ; anneaux = huit
barres pleines en octogone ; leurre et hameçon en barres pleines. Aucune plaque peinte empilée.

Repère (catégorie objets, Recette) : comme `fishing_rod.png` vue de +Z, talon en bas à gauche, pointe en haut à droite (15 ; 15),
là où le jeu fait partir sa ligne ; moulinet, anneaux et ligne du côté bas-droit (−b), qui est le **bas** en 3e personne
(calculé par `objet.matrice_main`). La poignée (a = 0,5) tombe sur le poing calculé. 21,8 px du talon à la pointe (vanilla
≈ 17,7). Display : préréglage `_CANNE` de `tools/objet.py` (`item/handheld_rod` du jar, 3e personne corrigée le 2026-11-08),
`gui` ramené à la case.

Étapes : `repos` et `lancee` sont deux copies complètes (l'animation joue sur le groupe de l'étape dessinée, guide 14).
Foudre (fiche `.claude/references/effets/foudre.md`) : traits en géométrie, cœur opaque blanc + `_e`, gaine `add_` ; éclairs
**repliés** au repos (1/10, 1/15 pour la foudre du ciel) sur des pivots cachés dans la tête de la canne (contrôlé à la
génération), dépliés par l'échelle, un seul dépliage par animation.

Objet vivant (guide 14), format free :
- item_idle (4 s, boucle) : au repos, la ligne et le leurre se balancent (le leurre tourne lentement), le cristal respire
  (ctrl_lumiere) ; lancée, la pointe crépite (arcs au hasard, Molang q.life_time + q.instance_seed, ~2 arcs/s), le bout
  frémit, le cristal pulse ;
- event_enter_lancee (0,9 s) : le lancer : le scion se charge puis fouette (trois brins pliés en cascade, oscillation
  amortie), le moulinet se dévide (3 tours), éclat et arcs à la pointe au moment où la ligne part ; **aucun son**
  (correctif F6 : rejoué à chaque bascule repos/lancee ; le jeu joue déjà le lancer du flotteur) ;
- event_enter_repos (0,8 s) : la ligne revient, le moulinet ramène (2 tours en sens inverse), la ligne et le leurre retombent
  en se balançant, petit à-coup du scion ;
- event_select (0,6 s) : la foudre tombe sur la pointe-paratonnerre (trois arcs en retour), éclat, la ligne sursaute, le
  cristal s'allume.
Fonctions avancées : add_, calque _e, ctrl_lumiere (non simulé), son embarqué, scale animé, Molang (q.life_time,
q.instance_seed). Pas de particules (une particule d'un groupe d'étape caché pourrait partir quand même : non documenté).
À juger en jeu : la ligne du jeu qui part de la pointe lancée, event_enter_* et le son d'objet, la canne dans la case.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

AVEC_E = True
NOM = "skin_canne_orage"
TEX = 512
DENS = 16.0              # texels par px sur les pans
TH = 0.3                 # épaisseur d'un pan
TAU = 2 * math.pi
K = 0.1                  # repli des éclairs au repos (échelle 1/10 autour d'un pivot caché dans la tête)
KU = 1 / K
K_CIEL = 1 / 15          # foudre du ciel (plus longue) : 1/15 (scale ≤ 16 fois)

# ------------------------------------------------------------------ palette (fiche orage.md, comme les autres objets d'orage)
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




def p_siege(xn, t, y, r, L, ex):
    """Porte-moulinet : acier sombre fileté d'or (pas de vis)."""
    col = lerp(METAL[1], METAL[3], (0.35 + 0.5 * (1 - np.abs(xn)))[..., None])
    filet = np.mod(y * 4.0, 1) < 0.3
    col = np.where(filet[..., None], lerp(OR[0], OR[2], (1 - np.abs(xn))[..., None]), col)
    return col, None


def p_bobine(xn, t, y, r, L, ex):
    """Bobine : ligne enroulée, spires claires sur fond bleu nuit ; les spires gardent la charge (_e faible)."""
    base = lerp(LAQUE0, LAQUE1, (0.3 + 0.5 * (1 - np.abs(xn)))[..., None])
    spire = np.mod(y * 6.0 + 0.15 * xn, 1) < 0.42
    col = np.where(spire[..., None], lerp(C((90, 110, 170)), C((190, 204, 236)), (1 - np.abs(xn))[..., None]), base)
    em = np.zeros(xn.shape + (3,), np.float32)
    em[spire] = (40, 60, 130)
    return col, em


PEINTRES.update({"siege": p_siege, "bobine": p_bobine})


def t_bloc(nom, mat, W=16, H=16):
    """Tuile pleine d'une barre (leurre, hameçon, anneaux, ligne) : dégradé en travers, bords sombres."""
    yy, xx = np.mgrid[0:H, 0:W]
    x = (xx + 0.5) / W * 2 - 1
    k = (1 - np.abs(x)) ** 0.8
    if mat == "or":
        col = lerp(OR[1], OR[3], k[..., None])
        col = np.where((np.abs(x) > 0.8)[..., None], OR[0], col)
    elif mat == "acier":
        col = lerp(METAL[2], METAL[4] * 1.1, k[..., None])
    elif mat == "ligne":
        col = lerp(C((150, 166, 206)), C((226, 234, 252)), k[..., None])
    else:
        col = lerp(METAL[1], METAL[3], k[..., None])
    return tuile(nom, *_rgba(col, np.ones(x.shape, bool)))


t_core(), t_halo(), t_star()
for _m in ("or", "acier", "ligne"):
    t_bloc(f"bloc_{_m}", _m)
CLEAR = "CLEAR"


# ------------------------------------------------------------------ repère
def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


A_W = unit(V(1, 1.08, 0))        # a : le long de la canne, du talon vers la pointe (haut à droite vue de +Z)
B_W = unit(V(-1.08, 1, 0))       # b : en travers ; −b = côté du moulinet et des anneaux (le bas en 3e personne)
Z_W = V(0, 0, 1)
A_FIN = 17.2                     # bout de la pointe de cristal
TIP = V(15.0, 15.1, 8.0)         # coin d'où le jeu fait partir sa ligne
G0 = TIP - A_FIN * A_W
A_PRISE = 0.5                    # milieu de la poignée = point du poing (inverse de objet.matrice_main, 3e personne)


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
elements, groups = [], {}        # clé unique -> groupe ({"name": nom affiché, ...})


def nuid():
    return str(_uuid.uuid4())


def group(key, origin, parent=None, repli=None, k=K, name=None):
    """repli = pivot (monde) : tout le sous-groupe est replié à k autour de lui (éclair caché dans la tête au repos)."""
    assert key not in groups, key
    name = name or key
    assert len(name) <= 64
    if repli is not None:
        ct, kk = np.asarray(repli, float), k
    elif parent:
        ct, kk = groups[parent]["ct"], groups[parent]["k"]
    else:
        ct, kk = None, 1.0
    o = np.asarray(origin, float)
    if repli is None and ct is not None:
        o = ct + kk * (o - ct)
    groups[key] = {"name": name, "origin": [round(float(v), 3) for v in o], "uuid": nuid(), "ids": [], "parent": parent,
                   "ct": ct, "k": kk}
    return key


def cube_c(g, name, c, h, R, faces):
    """Cube de centre c (monde), demi-tailles h, axes R (colonnes), faces {face: CLEAR | (tuile, (u0, v0, u1, v1) en fractions)}."""
    c, h = np.asarray(c, float), np.asarray(h, float)
    ct, kk = groups[g]["ct"], groups[g]["k"]
    if ct is not None:
        c, h = ct + kk * (c - ct), h * kk
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


def tour(g, nom, tnom, O, ax, ref, profil, n=16, phase=0.0):
    """profil = [(b0, r0, b1, r1, mat, ex), ...] parcouru dans le sens +ax, le plein du côté de l'axe (rayon = apothème).
    `tnom` nomme les tuiles (partagées par les deux copies d'étape). Chaque pan : plaque de TH px, face extérieure (south)."""
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
        tiles = [tuile_pan(f"{tnom}{i}{'ab'[j]}", m, L, 2 * r0 * tn, 2 * r1 * tn, r0, r1, exs[j]) for j, m in enumerate(mats)]
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


def barre(g, name, a, b, s, tile, ov=0.0, Y=None, bouts=True):
    """Barre pleine de section s × s de a à b (monde), quatre faces longues peintes."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    X = unit(b - a)
    if Y is None:
        ref = Z_W if abs(X @ Z_W) < 0.9 else A_W
        Y = ref - (ref @ X) * X
    Y = unit(Y - (Y @ X) * X)
    Zc = np.cross(X, Y)
    L = float(np.linalg.norm(b - a))
    cap = T(tile, 0.3, 0.3, 0.7, 0.7) if bouts else CLEAR
    cube_c(g, name, (a + b) / 2, (L / 2 + ov, s / 2, s / 2), np.column_stack([X, Y, Zc]),
           {"north": T(tile), "south": T(tile), "up": T(tile), "down": T(tile), "east": cap, "west": cap})


def anneau(g, nom, c, ax, rg, s=0.22, n=8):
    """Anneau d'or : n barres pleines en polygone (apothème rg) dans le plan perpendiculaire à `ax`, une barre face à +b."""
    ax = unit(np.asarray(ax, float))
    e1 = unit(B_W - (B_W @ ax) * ax)
    e2 = np.cross(ax, e1)
    side = 2 * rg * math.tan(math.pi / n)
    for k in range(n):
        th = TAU * k / n
        d = math.cos(th) * e1 + math.sin(th) * e2
        t = -math.sin(th) * e1 + math.cos(th) * e2
        m = np.asarray(c, float) + d * rg
        barre(g, f"{nom}_{k}", m - t * side / 2, m + t * side / 2, s, "bloc_or", ov=s * 0.42, Y=d)


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


def eclair(key, parent, pivot, pts, w0, w1, k=K):
    """Groupe d'éclair replié autour de `pivot` : cœur opaque (+ _e) dans `key`, gaine dans `add_<key>`."""
    g = group(key, pivot, parent=parent, repli=np.asarray(pivot, float), k=k)
    h = group(f"add_{key}", pivot, parent=g)
    trait(g, h, key, pts, w0, w1)
    return g


def eclat(key, parent, pivot, c, r):
    """Éclat (étoile additive) replié autour de `pivot` : trois plaques croisées (cam_ n'est pas annoncé pour les objets)."""
    g = group(key, pivot, parent=parent, repli=np.asarray(pivot, float))
    ag = group(f"add_{key}", c, parent=g)
    for k_, (n, up) in enumerate(((Z_W, A_W), (A_W, B_W), (B_W, Z_W))):
        plaque(ag, f"{key}{k_}", np.asarray(c, float), n, up, 2 * r, 2 * r, "star", th=0.3 + 0.02 * k_)
    return g


# ---- cotes (repère local a, b, z ; px)
A_TALON = -4.6
A_BRIN = (2.75, 7.62, 11.95)     # départ des trois brins (pivots de flexion : bague d'arrêt, viroles)
A_TETE = 15.2                    # début de la tête d'or
GUIDES = ((5.2, 0.44), (9.5, 0.38), (12.9, 0.33), (14.4, 0.29))   # (a, rayon de l'anneau)
A_MOUL = -2.65                   # moulinet sous le porte-moulinet
R_PL, R_BOB = 1.75, 1.15         # flasques, bobine
Z_PL, Z_GAP = 0.85, 0.48         # demi-épaisseur du tambour, demi-largeur de la bobine
TIGE = 0.5                       # pied du moulinet


def r_scion(a):
    return 0.60 + (0.27 - 0.60) * (a - A_BRIN[0]) / (A_TETE - A_BRIN[0])


def profil_brin(a0, a1, guides, virole):
    """Brin d'acier forgé de a0 à a1 qui s'affine, ligatures d'or aux anneaux, virole d'or au bout (sauf le dernier)."""
    out, a = [], a0
    marques = [(ga - 0.28, ga + 0.28, 0.07) for ga, _ in guides]
    if virole:
        marques.append((a1 - 0.36, a1 + 0.0, 0.13))
    for m0, m1, d in marques:
        out.append((a, r_scion(a), m0, r_scion(m0), "metal", {"clair": -0.14}))
        out += bague(m0, m1, r_scion(m0), r_scion(m1), r_scion((m0 + m1) / 2) + d, c=0.1)
        a = m1
    if a < a1:
        out.append((a, r_scion(a), a1, r_scion(a1), "metal", {"clair": -0.14}))
    return out


PROFIL_BASE = ([(A_TALON, 0.0, -4.1, 0.40, "cris", {"vers_p1": False}), (-4.1, 0.40, -3.9, 0.46, "cris", {})]
               + bague(-3.9, -3.35, 0.46, 0.80, 1.0, c=0.15)
               + [(-3.35, 0.80, -1.95, 0.80, "siege", {})]
               + bague(-1.95, -1.45, 0.80, 0.90, 1.02, c=0.15)
               + [(-1.45, 0.90, 2.35, 0.84, "poignee", {})]
               + bague(2.35, A_BRIN[0], 0.84, r_scion(A_BRIN[0]), 0.95))
PROFIL_TETE = (bague(A_TETE, 15.9, r_scion(A_TETE), 0.5, 0.62, c=0.15)
               + [(15.9, 0.5, 16.3, 0.5, "cris", {}), (16.3, 0.5, A_FIN, 0.0, "cris", {})])
PROFILS = [PROFIL_BASE, profil_brin(A_BRIN[0], A_BRIN[1], GUIDES[:1], True),
           profil_brin(A_BRIN[1], A_BRIN[2], GUIDES[1:2], True), profil_brin(A_BRIN[2], A_TETE, GUIDES[2:], False), PROFIL_TETE]


def r_canne(a):
    """Rayon (apothème) de la canne à l'abscisse a (contrôle des éclairs repliés)."""
    for pr in PROFILS:
        for b0, r0, b1, r1, *_ in pr:
            if b0 <= a <= b1 and b1 > b0:
                return r0 + (r1 - r0) * (a - b0) / (b1 - b0)
    return -1.0


def centre_anneau(a, rg):
    return W(a, -(r_scion(a) + 0.2 + rg + 0.11))


A_ANT = 15.5                                  # anneau de tête, sur la tête d'or
R_ANT = 0.26
C_ANT = W(A_ANT, -(0.62 + 0.15 + R_ANT + 0.11))
C_MOUL = W(A_MOUL, -(0.80 + TIGE + R_PL))
P_BOB = C_MOUL + B_W * (R_BOB + 0.11)         # la ligne quitte la bobine par le haut
PIV_TETE = W(15.85)                            # pivot des éclairs repliés (dans la tête d'or)
Y_BAS_LIGNE = 3.7                              # la ligne pendante descend jusqu'ici (image vanilla)


def build(st):
    """Une copie complète de la canne dans le groupe d'étape `st` ; renvoie les groupes animés."""
    p = st[0]
    racine = group(objet.etape(st, "canne"), W(A_PRISE))
    base = group(f"{p}_canne", W(A_PRISE), parent=racine)
    tour(base, f"{p}b", "b", W(0), A_W, B_W, PROFIL_BASE, n=8)
    # --- moulinet : pied (semelle d'or + tige), tambour à 16 pans le long de z
    pied = W(A_MOUL, -0.8 - 0.06)
    cube_c(base, f"{p}semelle", pied, (0.85, 0.12, 0.36), np.column_stack([A_W, B_W, Z_W]),
           {f: T("bloc_or") for f in SIX})
    tour(base, f"{p}tige", "tige", W(A_MOUL, -0.8), -B_W, A_W, [(0.0, 0.3, TIGE + 0.12, 0.26, "metal", {})], n=8)
    moul = group(f"{p}_moulinet", C_MOUL, parent=base)
    prof_m = ([(-Z_PL, 1.58, -0.72, R_PL, "or", {"clair": 0.12}), (-0.72, R_PL, -Z_GAP, R_PL, "or", {}),
               (-Z_GAP, R_PL, -Z_GAP, R_BOB, "mur", {"rmin": R_BOB, "rmax": R_PL}),
               (-Z_GAP, R_BOB, Z_GAP, R_BOB, "bobine", {}),
               (Z_GAP, R_BOB, Z_GAP, R_PL, "mur", {"rmin": R_BOB, "rmax": R_PL}),
               (Z_GAP, R_PL, 0.72, R_PL, "or", {}), (0.72, R_PL, Z_PL, 1.58, "or", {"clair": -0.1})])
    tour(moul, f"{p}m", "m", C_MOUL, Z_W, A_W, prof_m, n=16)
    med = t_medaillon(1.6)
    disque(moul, f"{p}med_av", C_MOUL + Z_W * Z_PL, Z_W, B_W, 1.6, med)
    disque(moul, f"{p}med_ar", C_MOUL - Z_W * Z_PL, -Z_W, B_W, 1.6, med)
    # moyeu de cristal (devant) et bouton d'axe (derrière)
    tour(moul, f"{p}moy", "moy", C_MOUL + Z_W * (Z_PL - 0.05), Z_W, A_W,
         [(0.0, 0.42, 0.25, 0.42, "or", {}), (0.25, 0.42, 0.35, 0.3, "cris", {}), (0.35, 0.3, 0.55, 0.0, "cris", {})], n=8)
    tour(moul, f"{p}moyar", "moyar", C_MOUL - Z_W * (Z_PL - 0.05), -Z_W, A_W, [(0.0, 0.4, 0.2, 0.4, "or", {}), (0.2, 0.4, 0.3, 0.0, "or", {})], n=8)
    # manivelle : bras d'or + bouton de cuir à chapeau d'or
    d_m = unit(-A_W - 0.35 * B_W)
    zb = Z_PL + 0.12
    barre(moul, f"{p}bras", C_MOUL + Z_W * zb + d_m * 0.3, C_MOUL + Z_W * zb + d_m * 1.25, 0.3, "bloc_or")
    tour(moul, f"{p}bouton", "bouton", C_MOUL + d_m * 1.15 + Z_W * (zb + 0.15), Z_W, A_W,
         [(0.0, 0.3, 0.75, 0.3, "poignee", {}), (0.75, 0.3, 0.85, 0.34, "or", {}), (0.85, 0.34, 0.95, 0.0, "or", {})], n=8)
    # foudre couchée sur la bobine, entre les flasques (cœur + _e, gaine add_)
    gout = group(f"{p}_foudre_bobine", C_MOUL, parent=moul)
    gaine = group(f"add_{p}_bobine", C_MOUL, parent=gout)
    rng = np.random.default_rng(9)
    NZ = 24
    pts = []
    for j in range(NZ):
        th = TAU * j / NZ
        e = math.cos(th) * A_W + math.sin(th) * B_W
        pts.append((e, (0.2 if j % 2 == 0 else -0.2) * (0.7 + 0.3 * rng.random())))
    pts.append(pts[0])
    for j in range(NZ):
        (e0, z0), (e1, z1) = pts[j], pts[j + 1]
        P0, P1 = C_MOUL + e0 * (R_BOB + 0.14) + Z_W * z0, C_MOUL + e1 * (R_BOB + 0.14) + Z_W * z1
        rad = unit(e0 + e1)
        seg(gout, f"{p}gc{j}", P0, P1, 0.22, "core", 0.05, Y=rad)
        seg(gaine, f"{p}gh{j}", P0, P1, 0.26, "halo", 0.03, Y=rad, wz=0.5)

    # --- scion : trois brins imbriqués (pivots aux viroles), anneaux ligaturés, ligne dans les anneaux
    brins, parent = [], base
    for i, a0 in enumerate(A_BRIN):
        g = group(f"{p}_brin{i + 1}", W(a0), parent=parent)
        tour(g, f"{p}s{i}", f"s{i}", W(0), A_W, B_W, PROFILS[1 + i], n=8)
        brins.append(g)
        parent = g
    pts_ligne = [P_BOB]
    for ga, rg in GUIDES:
        i = sum(ga >= a0 for a0 in A_BRIN) - 1
        c = centre_anneau(ga, rg)
        anneau(brins[i], f"{p}an{ga:.0f}", c, A_W, rg)
        barre(brins[i], f"{p}pied{ga:.0f}", W(ga, -r_scion(ga) + 0.1), c + B_W * (rg - 0.05), 0.22, "bloc_or", Y=A_W)
        pts_ligne.append(c)
    tete = group(f"{p}_tete", W(A_TETE), parent=brins[-1])
    tour(tete, f"{p}t", "t", W(0), A_W, B_W, PROFIL_TETE, n=8, phase=math.pi / 8)
    lum = group(f"{p}_ctrl_lumiere", W(16.3), parent=tete, name="ctrl_lumiere")
    anneau(tete, f"{p}ant", C_ANT, A_W, R_ANT, s=0.24)
    barre(tete, f"{p}piedant", W(A_ANT, -0.5), C_ANT + B_W * (R_ANT - 0.05), 0.24, "bloc_or", Y=A_W)
    pts_ligne.append(C_ANT)
    owners = [base] + brins[:3] + [brins[-1]]
    for j in range(len(pts_ligne) - 1):
        g = owners[min(j, len(owners) - 1)]
        barre(g, f"{p}ligne{j}", pts_ligne[j], pts_ligne[j + 1], 0.16, "bloc_ligne", ov=0.05, Y=Z_W, bouts=False)
    out = {"racine": racine, "moul": moul, "brins": brins, "tete": tete}

    if st == "repos":
        # --- ligne pendante (image vanilla), leurre d'or en éclair, perle de cristal, hameçon
        lg = group("r_ligne", C_ANT, parent=tete)
        bas = V(C_ANT[0], Y_BAS_LIGNE, C_ANT[2])
        barre(lg, "r_pend", C_ANT, bas, 0.26, "bloc_ligne", ov=0.05, Y=Z_W)
        le = group("r_leurre", bas, parent=lg)
        tour(le, "r_perle", "perle", bas + V(0, 0.05, 0), V(0, -1, 0), V(1, 0, 0),
             [(0.0, 0.0, 0.12, 0.26, "cris", {}), (0.12, 0.26, 0.42, 0.3, "cris", {}), (0.42, 0.3, 0.6, 0.0, "cris", {"vers_p1": False})],
             n=8)
        q0 = bas + V(0, -0.6, 0)
        zz = [q0, q0 + V(-0.55, -0.62, 0), q0 + V(0.12, -1.02, 0), q0 + V(-0.42, -1.75, 0)]
        for j in range(3):
            barre(le, f"r_eclair{j}", zz[j], zz[j + 1], 0.42, "bloc_or", ov=0.16, Y=Z_W)
        h0 = zz[-1]
        croc = [h0, h0 + V(0.0, -0.55, 0), h0 + V(0.28, -0.85, 0), h0 + V(0.62, -0.7, 0), h0 + V(0.7, -0.25, 0)]
        for j in range(4):
            barre(le, f"r_croc{j}", croc[j], croc[j + 1], 0.2, "bloc_acier", ov=0.08, Y=Z_W)
        barre(le, "r_ardillon", croc[-1], croc[-1] + V(-0.22, -0.2, 0), 0.18, "bloc_acier", ov=0.05, Y=Z_W)
        # --- event_select : la foudre du ciel tombe sur la pointe (repliée à 1/15 dans la tête)
        bout = W(A_FIN)
        ciel = zigzag(bout + V(-0.6, 5.4, 0.3), bout, 5, 0.6, 61)
        out["ciel"] = eclair("r_foudre_ciel", tete, PIV_TETE, ciel, 0.42, 0.3, k=K_CIEL)
        p1 = on_poly(ciel, 0.45)
        out["cielb"] = eclair("r_foudre_ciel_b", tete, PIV_TETE, zigzag(p1, p1 + unit(V(1, -0.4, 0.2)) * 1.8, 3, 0.3, 67), 0.3, 0.3,
                              k=K_CIEL)
        out["eclat_sel"] = eclat("r_eclat_sel", tete, PIV_TETE, bout, 1.2)
        out["ligne"], out["leurre"], out["lum"] = lg, le, lum
    else:
        # --- crépitement de la pointe (item_idle) : arcs courts du cristal vers l'air et vers la tête d'or
        bout = W(A_FIN - 0.1)
        dirs = [(0.6, 0.9, 0.3), (0.2, -1.0, 0.5), (1.0, 0.1, -0.6), (-0.3, 0.8, -0.8), (0.9, -0.5, 0.7)]
        arcs = []
        for i, dv in enumerate(dirs):
            d = unit(dv[0] * A_W + dv[1] * B_W + dv[2] * Z_W)
            arcs.append(eclair(f"l_arc{i}", tete, PIV_TETE, zigzag(bout, bout + d * (1.6 + 0.25 * i), 3, 0.35, 11 + i), 0.26, 0.24))
        arcs.append(eclair("l_arc_tete", tete, PIV_TETE, zigzag(bout, W(A_TETE + 0.4, -0.66, 0.3), 3, 0.3, 19), 0.24, 0.24))
        # --- event_enter_lancee : éclat et deux arcs quand la ligne part
        lan = [eclair(f"l_lancer{i}", tete, PIV_TETE,
                      zigzag(bout, bout + unit(A_W * 1.0 + B_W * s + Z_W * 0.3 * s) * 2.3, 4, 0.4, 31 + i), 0.32, 0.26)
               for i, s in enumerate((0.8, -0.7))]
        out["arcs"], out["lancer"] = arcs, lan
        out["eclat_lan"] = eclat("l_eclat_lan", tete, PIV_TETE, bout, 1.5)
        out["lum"] = lum
    return out


F = {st: build(st) for st in ("repos", "lancee")}


def node(key):
    g = groups[key]
    kids = [n for n, gg in groups.items() if gg["parent"] == key]
    return {"name": g["name"], "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0], "children": g["ids"] + [node(k) for k in kids]}


outliner = [node(F[st]["racine"]) for st in ("repos", "lancee")]


def coins_de(e):
    f, t, o = np.array(e["from"]), np.array(e["to"]), np.array(e["origin"])
    R = rmat(*e.get("rotation", (0, 0, 0)))
    return [R @ (np.array([(f, t)[(i >> k) & 1][k] for k in range(3)]) - o) + o for i in range(8)]


CACHES = set()
for n, g in groups.items():
    if g["ct"] is not None:
        CACHES.update(g["ids"])
P = np.array([c for e in elements if e["uuid"] not in CACHES for c in coins_de(e)])
LONGUEUR = float((P @ A_W).max() - (P @ A_W).min())

# contrôle : chaque éclair replié reste dans le volume fermé de la tête (tête d'or + cristal)
_hors, _noms = 0, set()
for e in elements:
    if e["uuid"] not in CACHES:
        continue
    for c in coins_de(e):
        a, rr = (c - G0) @ A_W, math.hypot((c - G0) @ B_W, (c - G0) @ Z_W)
        if not rr < r_canne(a) * 0.97 - 0.05:
            _hors += 1
            _noms.add(e["name"])
assert _hors == 0, f"{_hors} {sorted(_noms)[:8]} coins d'éclairs repliés hors du volume"


# ------------------------------------------------------------------ animations (objet vivant, guide 14)
def kf(ch, t, x, y=None, z=None, interp="linear"):
    y = x if y is None else y
    z = x if z is None else z
    f = lambda v: v if isinstance(v, str) else f"{float(v) + 0.0:.4f}"
    return {"channel": ch, "data_points": [{"x": f(x), "y": f(y), "z": f(z)}], "time": round(t, 4), "interpolation": interp}


def anim(name, length, loop="loop"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "item_idle", "animators": {}}


def piste(an, g, keys):
    an["animators"][groups[g]["uuid"]] = {"name": groups[g]["name"], "type": "bone", "keyframes": keys}


def creneaux(fen, L, haut=KU, bas=1.0, rampe=0.006, ch="scale"):
    """Échelle en créneaux : `fen` = [(t0, t1)] où l'éclair est déplié, replié ailleurs ; rampes de 6 ms."""
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


def H(x):
    return f"math.mod(math.abs(math.sin(({x})*127.1))*437.585,1)"


def echant(L, n):
    return [L * i / n for i in range(n + 1)]


FLEX = (0.22, 0.33, 0.45)        # part de la flexion portée par chaque brin (cumulée le long du scion)
R_, L_ = F["repos"], F["lancee"]

# item_idle (4 s, boucle)
L_IDLE = 4.0
idle = anim("item_idle", L_IDLE)
piste(idle, R_["ligne"], [kf("rotation", t, 3.0 * math.sin(TAU * t / L_IDLE + 1.2), 0, 2.2 * math.sin(TAU * t / L_IDLE))
                          for t in echant(L_IDLE, 16)])
piste(idle, R_["leurre"], [kf("rotation", t, 4.0 * math.sin(TAU * t / L_IDLE + 0.4), 360 * t / L_IDLE,
                                3.5 * math.sin(TAU * t / L_IDLE - 0.9)) for t in echant(L_IDLE, 16)])
piste(idle, R_["lum"], [kf("position", t, 0.2 * math.sin(TAU * t / L_IDLE), 0, 0) for t in echant(L_IDLE, 4)])
for i, g in enumerate(L_["arcs"]):
    pr = 0.035 if i < 5 else 0.025              # ~2 arcs/s en tout, 125 ms chacun
    expr = f"({H(f'math.floor(q.life_time*8)*1.731+{0.37 + 17.3 * i:.2f}+q.instance_seed*17')}<{pr})?{KU:g}:1"
    assert len(expr) <= 512
    piste(idle, g, [kf("scale", 0.0, expr)])
piste(idle, L_["lum"], [kf("position", t, 0.6 + 0.4 * math.sin(TAU * 2 * t / L_IDLE), 0, 0) for t in echant(L_IDLE, 8)])
piste(idle, L_["brins"][2], [kf("rotation", t, 0, 0, 0.5 * math.sin(TAU * 4 * t / L_IDLE) * math.sin(TAU * t / L_IDLE) ** 2)
                             for t in echant(L_IDLE, 32)])


# event_enter_lancee (0,9 s) : le scion se charge (+), fouette (−) puis oscille, amorti ; le moulinet se dévide (3 tours)
def flex_lancer(t):
    if t < 0.2:
        return 9.0 * math.sin(math.pi / 2 * t / 0.2)
    if t < 0.32:
        u = (t - 0.2) / 0.12
        return 9.0 - 23.0 * (u * u * (3 - 2 * u))
    return -14.0 * math.exp(-(t - 0.32) / 0.14) * math.cos(TAU * (t - 0.32) / 0.22)


L_LAN = 0.9
lancer = anim("event_enter_lancee", L_LAN, "once")
ts = echant(L_LAN, 36)
for g, f_ in zip(L_["brins"], FLEX):
    piste(lancer, g, [kf("rotation", t, 0, 0, round(f_ * flex_lancer(t) * (1 if t < L_LAN - 1e-6 else 0), 3)) for t in ts])
piste(lancer, L_["moul"], [kf("rotation", t, 0, 0, -1080 * (1 - (1 - t / L_LAN) ** 3) if t > 0.25 else
                              -1080 * (1 - (1 - t / L_LAN) ** 3) * (t / 0.25) ** 2) for t in ts])
T_PART = 0.32
for g in L_["lancer"]:
    piste(lancer, g, creneaux([(T_PART, T_PART + 0.07), (T_PART + 0.13, T_PART + 0.18)], L_LAN))
piste(lancer, L_["eclat_lan"], [kf("scale", 0, 1), kf("scale", T_PART, 1), kf("scale", T_PART + 0.02, KU * 1.1),
                                kf("scale", T_PART + 0.09, KU * 0.7), kf("scale", T_PART + 0.2, 1), kf("scale", L_LAN, 1)])
piste(lancer, L_["lum"], [kf("position", 0, 0, 0, 0), kf("position", T_PART, 0.4, 0, 0), kf("position", T_PART + 0.03, 1.6, 0, 0),
                          kf("position", L_LAN, 0.6, 0, 0)])

# event_enter_repos (0,8 s) : le moulinet ramène (2 tours), la ligne retombe en se balançant, à-coup du scion
L_REP = 0.8
ramene = anim("event_enter_repos", L_REP, "once")
ts = echant(L_REP, 32)
sm3 = lambda u: u * u * (3 - 2 * u)
piste(ramene, R_["moul"], [kf("rotation", t, 0, 0, 720 * sm3(t / L_REP)) for t in ts])
piste(ramene, R_["ligne"], [kf("rotation", t, 0, 0, 0 if t >= L_REP - 1e-6 else 55 * math.exp(-t / 0.16) * math.cos(TAU * t / 0.42))
                            for t in ts])
piste(ramene, R_["leurre"], [kf("rotation", t, 0, 0, 0 if t >= L_REP - 1e-6 else
                                 -30 * math.exp(-t / 0.2) * math.sin(TAU * t / 0.36)) for t in ts])
for g, f_ in zip(R_["brins"], FLEX):
    piste(ramene, g, [kf("rotation", t, 0, 0, 0 if t >= L_REP - 1e-6 else round(f_ * 6.0 * math.exp(-t / 0.12) * math.sin(TAU * t / 0.2), 3))
                      for t in ts])

# event_select (0,6 s) : la foudre tombe sur la pointe-paratonnerre, la ligne sursaute, le cristal s'allume
L_SEL = 0.6
sel = anim("event_select", L_SEL, "once")
KC = 1 / K_CIEL
piste(sel, R_["ciel"], creneaux([(0.04, 0.1), (0.16, 0.22), (0.28, 0.33)], L_SEL, haut=KC))
piste(sel, R_["cielb"], creneaux([(0.04, 0.1), (0.16, 0.2)], L_SEL, haut=KC))
piste(sel, R_["eclat_sel"], [kf("scale", 0, 1), kf("scale", 0.04, 1), kf("scale", 0.05, KU * 1.1), kf("scale", 0.12, KU * 0.8),
                             kf("scale", 0.2, KU * 0.9), kf("scale", 0.34, 1), kf("scale", L_SEL, 1)])
piste(sel, R_["ligne"], [kf("rotation", t, 0, 0, 0 if t >= L_SEL - 1e-6 else
                            round(9 * math.exp(-max(t - 0.05, 0) / 0.12) * math.sin(TAU * max(t - 0.05, 0) / 0.3), 3))
                         for t in echant(L_SEL, 24)])
piste(sel, R_["lum"], [kf("position", 0, -0.6, 0, 0), kf("position", 0.04, -0.6, 0, 0), kf("position", 0.06, 1.5, 0, 0),
                       kf("position", 0.36, 1.0, 0, 0), kf("position", L_SEL, 0, 0, 0)])

ANIMS = [idle, lancer, ramene, sel]

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
# Display : préréglage _CANNE (item/handheld_rod du jar) ; gui ramené à la case
_bb = np.array([c for e in elements if e["uuid"] not in CACHES and not e["name"].startswith("l") for c in coins_de(e)])
_cb = (_bb.min(axis=0) + _bb.max(axis=0)) / 2
GUI = round(min(1.0, 15.6 / float(max(_bb.max(axis=0)[:2] - _bb.min(axis=0)[:2]))), 2)
GUI_T = [round(float(-(_cb[0] - 8) * GUI), 2), round(float(-(_cb[1] - 8) * GUI), 2), 0]
AFFICHAGE = objet.affichage("canne", gui={"translation": GUI_T, "scale": [GUI] * 3})
model = objet.modele(NOM, "canne", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons
limiter_sons(model)
# Correctif F6 : aucun son (recette 4) ; event_enter_lancee est rejoué à chaque bascule repos/lancee (son répété en jeu)
# et le jeu joue déjà entity.fishing_bobber.throw. Son embarqué lancer_canne retiré (rangé dans .build/sons_retires).
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      len(TUILES), "tuiles ; gui", GUI)
print(f"longueur {LONGUEUR:.1f} px ; boîte visible {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)} ; bout {W(A_FIN).round(2)}")
