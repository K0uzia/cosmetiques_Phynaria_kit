"""Canne de banquise : skin d'objet (guide 14) pour toutes les cannes à pêche du joueur, ensemble Givre (thème Éléments).
Design original. Écrit skin_canne_givre.png, skin_canne_givre_e.png et .build/skin_canne_givre_brut.bbmodel à côté de ce script.

Idée : canne de pêche sur glace (pêche au trou dans la banquise), d'après de vraies cannes de glace
(`.claude/references/objets/cannes-a-peche.md`, section « Canne de glace ») : canne **courte et raide**, poignée trapue,
**moulinet en ligne** sous la canne (bobine à axe en travers, peu de pièces qui gèlent), **anneaux surdimensionnés** (la glace
ne les bouche pas), scion plein qui s'affine. Langage du set (`.claude/styles/givre.md`, épée et trident de givre) : glace =
peau `trans_` sur âme opaque à filet cyan `_e`, argent froid, flocons en relief à gemme hexagonale, cristaux hexagonaux
pointus, fusée de cuir bleu nuit cloutée.

Construction (du talon à la pointe) : pique de cristal hexagonale, bague d'argent, porte-moulinet d'argent fileté, **moulinet
à flocon** (flasques hexagonales d'argent, flocon en relief et gemme cyan `_e` sur chaque face, bobine de ligne blanche entre
deux parois, manivelle à bouton de cristal) suspendu sous la canne, fusée de cuir cloutée, bague d'arrêt, **scion de glace
hexagonal qui s'affine** (1,28 → 0,60 px ; peau `trans_` sur âme opaque, filet `_e`) en trois brins joints par des viroles
d'argent (pivots de flexion), trois **anneaux d'argent surdimensionnés** ligaturés + anneau de tête, ligne qui court du
moulinet au bout, virole de tête et **pointe de cristal** dont le bout est en (15 ; 15), là où le jeu fait partir sa ligne.
Au repos (`repos`), la ligne pend du bout comme sur l'image vanilla, avec une perle de cristal et une cuillère d'argent
(leurre de pêche sur glace) ; lancée (`lancee`), la ligne est partie (le jeu dessine la sienne, flotteur et ligne non
personnalisables) et **la pointe se givre** : cristal blanchi, onze aiguilles de givre qui poussent au lancer.

**Vrai volume** (recette `.claude/references/objets/volume-3d.md`, tours de `skin_canne_orage`) : toute pièce ronde est un tour
(profil (a, rayon), couronne de 6 ou 8 pans de 0,3 px posés sur la surface, face extérieure peinte et découpée en trapèze par
l'alpha, tranches transparentes) ; bagues biseautées ; anneaux = huit barres pleines ; flocons en barres à section losange.

Repère (catégorie objets, Recette) : comme `fishing_rod.png` vue de +Z, talon en bas à gauche, pointe en haut à droite ;
moulinet, anneaux et ligne du côté bas-droit (−b), qui est le **bas** en 3e personne. Poignée sur le poing calculé
(a = 0,5). 19,6 px du talon à la pointe (vanilla ≈ 17,7 ; canne courte de glace, plus trapue). Display : préréglage
`_CANNE` de `tools/objet.py`, `gui` ramené à la case.

Étapes : `repos` et `lancee` sont deux copies complètes (l'animation joue sur le groupe de l'étape dessinée, guide 14).

Objet vivant (guide 14), format free, glace rigide (petits frémissements, pas de fouet) :
- item_idle (6 s, boucle) : au repos, la ligne et la cuillère se balancent (la cuillère tourne), un scintillement à la
  pointe ; lancée, le bout frémit et le givre scintille au hasard (Molang q.life_time + q.instance_seed) ;
- event_enter_lancee (0,9 s) : petit coup sec du scion (amorti), le moulinet se dévide (2 tours), éclat à la pointe,
  les aiguilles de givre poussent en cascade ; **aucun son** (rejoué à chaque bascule repos/lancee ; le jeu joue déjà
  le lancer du flotteur) ;
- event_enter_repos (0,8 s) : le moulinet ramène (2 tours), la ligne et la cuillère retombent en se balançant ;
- event_select (0,7 s) : la glace pousse : la pointe de cristal grandit depuis sa virole, deux éclats courent le long du
  scion, la ligne sursaute ;
- event_swing (0,3 s) : petit frémissement du bout ; **seul son** block.amethyst_block.chime à 0,04 s (lancer et remontée
  déclenchent event_swing ; une clé à 0,0 s serait muette au premier passage).
Effets repliés à 1/10 sur des pivots cachés dans l'âme opaque (contrôlé à la génération) ; chaque groupe n'est mis à
l'échelle que par une seule animation.
Fonctions avancées : trans_, add_, calque _e, scale animé, Molang (q.life_time, q.instance_seed), étapes, son d'objet.
Pas de particules (une particule d'un groupe d'étape caché pourrait partir quand même : non documenté).
À juger en jeu : la ligne du jeu qui part de la pointe lancée, event_enter_* et event_swing (son), glace avec et sans
shader, la canne dans la case.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

AVEC_E = True
NOM = "skin_canne_givre"
TEX = 512
DENS = 16.0              # texels par px sur les pans
TH = 0.3                 # épaisseur d'un pan
TAU = 2 * math.pi
K = 0.1                  # repli des éclats au repos (échelle 1/10 autour d'un pivot caché dans l'âme)
KU = 1 / K


def C(*c):
    return np.array(c, np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ palette (fiche givre.md, comme les autres objets du set)
BLANC = C(244, 253, 255)
LUEUR = C(150, 226, 255)
G_LIGHT = C(214, 244, 255)
ARG_L, ARG_M, ARG_D = C(236, 244, 250), C(166, 186, 206), C(74, 90, 116)
ARG_0 = C(36, 46, 66)
NUIT0, NUIT1 = C(16, 20, 44), C(44, 56, 104)

# ------------------------------------------------------------------ tuiles (atlas rempli après la géométrie)
TUILES = {}              # nom -> (rgba, e ou None)
TRANS = set()


def tuile(nom, rgba, e=None, trans=False):
    if nom not in TUILES:
        TUILES[nom] = (rgba, e)
        if trans:
            TRANS.add(nom)
    return nom


def finir(col, al, em, mask):
    out = np.zeros(mask.shape + (4,), np.uint8)
    out[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    out[..., 3] = (np.clip(al, 1, 254).astype(np.uint8) if al is not None else 255) * mask
    out[~mask] = 0
    e = None
    if em is not None:
        m = mask & (em.max(axis=-1) > 0)
        if m.any():
            e = np.zeros_like(out)
            e[..., :3] = np.clip(em, 0, 225).astype(np.uint8)
            e[..., 3] = m * 255
            e[~m] = 0
    return out, e


# --- peintres des pans : xn en travers (-1..1), t le long (0 = P0, 1 = P1), y en px depuis P0, r le rayon ; -> (col, em, al)
def p_argent(xn, t, y, r, L, ex):
    k = np.clip(0.45 + 0.3 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    col = lerp(ARG_D, ARG_L, (k ** 1.2)[..., None]) * (1 + 0.03 * np.sin(y * 37 + xn * 3))[..., None]
    col = np.where((np.abs(xn) > 0.86)[..., None], np.minimum(col * 1.14 + 10, 255), col)
    if ex.get("givre"):                                           # givre blanc mat qui gagne la virole (étape lancée)
        g = (np.sin(xn * 9 + y * 23) + np.sin(xn * 17 - y * 31)) > 0.3
        col = np.where(g[..., None], lerp(col, BLANC, 0.75), col)
    return col, None, None


def p_siege(xn, t, y, r, L, ex):
    """Porte-moulinet : argent fileté (pas de vis sombres)."""
    col = lerp(ARG_D, ARG_L, (0.35 + 0.5 * (1 - np.abs(xn)))[..., None])
    filet = np.mod(y * 4.0, 1) < 0.28
    col = np.where(filet[..., None], col * 0.55, col)
    return col, None, None


def p_glace(xn, t, y, r, L, ex):
    """Âme d'un cristal (opaque) : cyan, arêtes blanches, filet _e au milieu du pan (si e), fissures blanches fines."""
    k = np.clip(0.35 + 0.35 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + 0.2 * t, 0, 1)
    col = lerp(C(40, 110, 176), G_LIGHT, (k ** 1.1)[..., None])
    col = np.where((np.abs(xn) > 0.84)[..., None], BLANC, col)
    em = np.zeros(col.shape, np.float32)
    if ex.get("e"):
        ln = np.abs(xn) < 0.22
        col[ln] = lerp(col[ln], C(200, 248, 255), 0.7)
        em[ln] = LUEUR
    if ex.get("chevrons"):                                        # chevrons de facettes vers la pointe
        ch = np.abs(np.mod(y * 1.6 - np.abs(xn) * 0.5, 1) - 0.5) < 0.05
        col = np.where((ch & (np.abs(xn) > 0.3))[..., None], lerp(col, BLANC, 0.6), col)
    return col, em, None


def p_peau(xn, t, y, r, L, ex):
    """Peau d'un cristal (trans_) : glace claire, arêtes blanches plus denses ; `givre` : blanchie et presque opaque."""
    k = np.clip(0.45 + 0.3 * (1 - np.abs(xn)) + ex.get("clair", 0.0) + 0.15 * t, 0, 1)
    col = lerp(C(110, 196, 236), G_LIGHT, k[..., None])
    al = 150 + 40 * t + 10 * (1 - np.abs(xn))
    ar = np.abs(xn) > 0.8
    col = np.where(ar[..., None], BLANC, col)
    al = np.where(ar, 224, al)
    if ex.get("givre"):
        fr = np.clip(0.35 + 0.65 * t, 0, 1) * (0.75 + 0.25 * np.sin(xn * 11 + y * 29) ** 2)
        col = lerp(col, BLANC, fr[..., None] * 0.85)
        al = np.maximum(al, 170 + 70 * fr)
    return col, None, al


def p_givre(xn, t, y, r, L, ex):
    """Aiguille de givre (opaque) : blanc bleuté, arêtes blanches."""
    k = np.clip(0.55 + 0.3 * (1 - np.abs(xn)) + 0.15 * t + ex.get("clair", 0.0), 0, 1)
    return lerp(C(120, 190, 230), BLANC, k[..., None]), None, None


def p_gemme(xn, t, y, r, L, ex):
    k = np.clip(0.4 + 0.4 * (1 - np.abs(xn)) + 0.2 * t + ex.get("clair", 0.0), 0, 1)
    col = lerp(C(40, 130, 210), C(170, 236, 255), k[..., None])
    return col, np.clip(col * 0.85, 0, 210), None


def p_poignee(xn, t, y, r, L, ex):
    """Cuir bleu nuit enroulé en biais, clous d'argent (fusée de l'épée de givre)."""
    f = np.mod(y * 2.2 + xn * 0.35, 1.0)
    col = lerp(NUIT1 * 1.25, NUIT0, f[..., None]) * (0.85 + 0.25 * (1 - np.abs(xn)))[..., None]
    col = np.where((f > 0.86)[..., None], C(8, 10, 24), col)
    if ex.get("clous", True):
        d = np.hypot(xn * ex["w"] / 2, np.mod(y, 0.75) - 0.375)
        col = np.where((d < 0.11)[..., None], lerp(ARG_M, ARG_L, np.clip(1 - d / 0.11, 0, 1)[..., None]), col)
        col = np.where(((d >= 0.11) & (d < 0.14))[..., None], C(8, 10, 24), col)
    return col, None, None


def p_mur(xn, t, y, r, L, ex):
    """Paroi de la bobine : argent sombre, lèvre claire + _e cyan au bord haut (rayon des flasques)."""
    k = np.clip((r - ex["rmin"]) / max(ex["rmax"] - ex["rmin"], 1e-6), 0, 1)
    col = lerp(ARG_0, ARG_M, (k ** 1.5)[..., None])
    em = np.zeros(xn.shape + (3,), np.float32)
    lev = r > ex["rmax"] - 0.09
    col = np.where(lev[..., None], C(200, 246, 255), col)
    em[lev] = LUEUR * 0.85
    return col, em, None


def p_bobine(xn, t, y, r, L, ex):
    """Bobine : ligne blanche enroulée en spires sur fond bleu nuit."""
    base = lerp(NUIT0, NUIT1, (0.3 + 0.5 * (1 - np.abs(xn)))[..., None])
    spire = np.mod(y * 6.5 + 0.15 * xn, 1) < 0.5
    col = np.where(spire[..., None], lerp(C(150, 190, 220), C(236, 248, 255), (1 - np.abs(xn))[..., None]), base)
    return col, None, None


PEINTRES = {"argent": p_argent, "siege": p_siege, "glace": p_glace, "peau": p_peau, "givre": p_givre, "gemme": p_gemme,
            "poignee": p_poignee, "mur": p_mur, "bobine": p_bobine}
OVL, OVW = 0.04, 0.03     # recouvrement en long et en travers entre pans voisins


def tuile_pan(nom, mat, L, w0, w1, r0, r1, ex):
    """Tuile d'un pan trapézoïdal : rangée 0 = bout P1 (haut de la face south), colonne 0 = côté -X."""
    if nom in TUILES:
        return nom
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
    col, em, al = PEINTRES[mat](xn, t, y, r, L, dict(ex, w=max(w0, w1)))
    return tuile(nom, *finir(col, al, em, mask), trans=al is not None)


def t_disque6(nom, Ra, N=56):
    """Face d'une flasque hexagonale (apothème Ra) : argent, liseré blanc, bord sombre, fond bleu nuit au centre."""
    R = Ra / math.cos(math.pi / 6)
    yy, xx = np.mgrid[0:N, 0:N]
    x = ((xx + 0.5) / N - 0.5) * 2 * R
    y = (0.5 - (yy + 0.5) / N) * 2 * R
    th = np.arctan2(y, x)
    sect = np.round(th / (TAU / 6)) * (TAU / 6)
    apo = (x * np.cos(sect) + y * np.sin(sect)) / Ra
    mask = apo <= 1.0 + 0.01
    sh = np.clip(0.6 + 0.25 * y / R, 0, 1)[..., None]
    col = lerp(NUIT0, NUIT1 * 1.2, np.clip(1 - apo, 0, 1)[..., None])           # fond nuit où le flocon se détache
    col = np.where((apo > 0.74)[..., None], lerp(ARG_D, ARG_L, sh), col)
    col = np.where(((apo > 0.8) & (apo < 0.86))[..., None], BLANC, col)
    col = np.where((apo > 0.95)[..., None], ARG_D, col)
    return tuile(nom, *finir(col, None, None, mask))


def t_bloc(nom, mat, W=16, H=16):
    """Tuile pleine d'une barre : dégradé en travers, bords sombres."""
    yy, xx = np.mgrid[0:H, 0:W]
    x = (xx + 0.5) / W * 2 - 1
    k = (1 - np.abs(x)) ** 0.8
    if mat == "argent":
        col = lerp(ARG_M, ARG_L, k[..., None])
        col = np.where((np.abs(x) > 0.8)[..., None], ARG_D, col)
    elif mat == "flocon":
        col = lerp(C(170, 220, 245), BLANC, k[..., None])
    elif mat == "ligne":
        col = lerp(C(170, 196, 220), C(240, 248, 255), k[..., None])
    else:
        col = lerp(ARG_D, ARG_M, k[..., None])
    return tuile(nom, *finir(col, None, None, np.ones(x.shape, bool)))


def t_star(nom="star", N=32, ss=4):
    """Scintillement additif cyan (noir = invisible)."""
    yy, xx = np.mgrid[0:N * ss, 0:N * ss]
    x, y = (xx + 0.5) / (N * ss) * 2 - 1, 1 - (yy + 0.5) / (N * ss) * 2
    r = np.hypot(x, y)
    ray = np.exp(-np.abs(x) * 14) * np.clip(1 - np.abs(y), 0, 1) + np.exp(-np.abs(y) * 14) * np.clip(1 - np.abs(x), 0, 1)
    diag = (np.exp(-np.abs(x - y) * 18) + np.exp(-np.abs(x + y) * 18)) * np.clip(1 - r * 1.6, 0, 1) * 0.5
    glow = np.clip(1 - r, 0, 1) ** 2.2
    core = np.clip(1 - r / 0.2, 0, 1)
    I = np.clip(0.5 * glow + 0.7 * ray + 0.4 * diag + 0.9 * core, 0, 1)
    img = np.clip(I[..., None] * np.array((170, 230, 255)) + (core[..., None] ** 0.7) * 40, 0, 255).astype(np.uint8)
    im = np.array(Image.fromarray(img, "RGB").resize((N, N), Image.LANCZOS))
    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = im
    out[..., 3] = (im.max(axis=2) > 12) * 255
    out[out[..., 3] == 0, :3] = 0
    return tuile(nom, out)


t_star()
for _m in ("argent", "flocon", "ligne"):
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
A_FIN = 15.2                     # bout de la pointe de cristal
TIP = V(15.0, 15.1, 8.0)         # coin d'où le jeu fait partir sa ligne
G0 = TIP - A_FIN * A_W
A_PRISE = 0.5                    # milieu de la poignée = point du poing (comme skin_canne_orage)


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
elements, groups = [], {}        # clé unique -> groupe
ETAPE = {"cur": None}
ELEM_ETAPE = {}                  # uuid -> étape


def nuid():
    return str(_uuid.uuid4())


def group(key, origin, parent=None, repli=None, k=K, name=None):
    """repli = pivot (monde) : tout le sous-groupe est replié à k autour de lui (éclat caché dans l'âme au repos)."""
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
    """Cube de centre c (monde), demi-tailles h, axes R (colonnes), faces {face: CLEAR | (tuile, (u0, v0, u1, v1))}."""
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
    ELEM_ETAPE[e["uuid"]] = ETAPE["cur"]
    return e


def T(tile, u0=0.0, v0=0.0, u1=1.0, v1=1.0):
    return (tile, (u0, v0, u1, v1))


SIX = ("north", "south", "east", "west", "up", "down")


def tour(g, nom, tnom, O, ax, ref, profil, n=8, phase=0.0):
    """profil = [(b0, r0, b1, r1, mats), ...] parcouru dans le sens +ax (rayon = apothème) ; mats = [(mat, ex), ...]
    alternées pan par pan. `tnom` nomme les tuiles (partagées entre étapes). Chaque pan : plaque de TH px, face south peinte."""
    O, ax = np.asarray(O, float), unit(np.asarray(ax, float))
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    for i, (b0, r0, b1, r1, mats) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        if L < 1e-4:
            continue
        tiles = [tuile_pan(f"{tnom}{i}{'abcd'[j]}", m, L, 2 * r0 * tn, 2 * r1 * tn, r0, r1, ex) for j, (m, ex) in enumerate(mats)]
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


ARG = [("argent", {}), ("argent", {"clair": -0.08})]
PEAU = [("peau", {"clair": 0.06}), ("peau", {"clair": -0.08})]
PEAU_G = [("peau", {"clair": 0.06, "givre": True}), ("peau", {"clair": -0.08, "givre": True})]
AME = [("glace", {"clair": 0.1, "e": True, "chevrons": True}), ("glace", {"clair": -0.1, "chevrons": True})]
GIVRE = [("givre", {"clair": 0.1}), ("givre", {"clair": -0.1})]
GEMME = [("gemme", {"clair": 0.1}), ("gemme", {"clair": -0.1})]


def bague(b0, b1, ra, rb, ro, c=0.12, mat="argent", ex=None):
    """Bague biseautée : du rayon ra (b0) monte à ro, palier, redescend à rb (b1)."""
    ex = ex or {}
    return [(b0, ra, b0 + c, ro, [(mat, dict(ex, clair=0.15))]), (b0 + c, ro, b1 - c, ro, [(mat, ex), (mat, dict(ex, clair=-0.08))]),
            (b1 - c, ro, b1, rb, [(mat, dict(ex, clair=-0.12))])]


def r_ame(r):
    return max(r - 0.2, r * 0.45)


AME_SEG = []                     # (a0, a1, r0, r1) des âmes le long de la canne (contrôle des éclats repliés)


def cristal(g_trans, g_ame, nom, tnom, base, d, ref, pts, L, peau=PEAU, phase=0.0, axe_canne=None):
    """Cristal hexagonal à section réelle : pts = [(b, r), ...] le long de d, pointe en L. Peau trans_ + âme opaque."""
    prof_p = [(b0, r0, b1, r1, peau) for (b0, r0), (b1, r1) in zip(pts[:-1], pts[1:])] + [(pts[-1][0], pts[-1][1], L, 0.0, peau)]
    tour(g_trans, nom, tnom + "p", base, d, ref, prof_p, n=6, phase=phase)
    pa = [(b, r_ame(r)) for b, r in pts]
    prof_a = [(b0, r0, b1, r1, AME) for (b0, r0), (b1, r1) in zip(pa[:-1], pa[1:])] + [(pa[-1][0], pa[-1][1], L - 0.22, 0.0, AME)]
    tour(g_ame, nom + "_a", tnom + "a", base, d, ref, prof_a, n=6, phase=phase)
    if axe_canne is not None:
        for b0, r0, b1, r1, _ in prof_a:
            AME_SEG.append((axe_canne + b0, axe_canne + b1, r0, r1))


def disque(g, nom, c, N, up, Ra, tile, n=6):
    """Disque à n pans (apothème Ra) : plaque dont seule la face extérieure (normale N) est peinte."""
    N = unit(np.asarray(N, float))
    Y = unit(up - (up @ N) * N)
    X = np.cross(Y, N)
    R = Ra / math.cos(math.pi / n)
    faces = {f: CLEAR for f in SIX}
    faces["south"] = T(tile)
    cube_c(g, nom, np.asarray(c, float) - N * TH / 2, (R, R, TH / 2), np.column_stack([X, Y, N]), faces)


def plaque(g, name, c, n, up, w, h, tile, th=0.3):
    """Plaque fine de normale n (image des deux côtés, tranches transparentes) : éclats additifs seulement."""
    n = unit(np.asarray(n, float))
    up = unit(up - (up @ n) * n)
    X = np.cross(up, n)
    cube_c(g, name, c, (w / 2, h / 2, th / 2), np.column_stack([X, up, n]),
           {"south": T(tile), "north": T(tile, 1, 0, 0, 1), "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def barre(g, name, a, b, s, tile, ov=0.0, Y=None, roll=0.0, bouts=True):
    """Barre pleine de section s × s de a à b (monde), quatre faces longues peintes ; roll = 45 : section en losange."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    X = unit(b - a)
    if Y is None:
        ref = Z_W if abs(X @ Z_W) < 0.9 else A_W
        Y = ref - (ref @ X) * X
    Y = unit(Y - (Y @ X) * X)
    Zc = np.cross(X, Y)
    if roll:
        rl = math.radians(roll)
        Y, Zc = math.cos(rl) * Y + math.sin(rl) * Zc, -math.sin(rl) * Y + math.cos(rl) * Zc
    L = float(np.linalg.norm(b - a))
    cap = T(tile, 0.3, 0.3, 0.7, 0.7) if bouts else CLEAR
    cube_c(g, name, (a + b) / 2, (L / 2 + ov, s / 2, s / 2), np.column_stack([X, Y, Zc]),
           {"north": T(tile), "south": T(tile), "up": T(tile), "down": T(tile), "east": cap, "west": cap})


def anneau(g, nom, c, ax, rg, s=0.2, n=8):
    """Anneau d'argent : n barres pleines en polygone (apothème rg) dans le plan perpendiculaire à `ax`."""
    ax = unit(np.asarray(ax, float))
    e1 = unit(B_W - (B_W @ ax) * ax)
    e2 = np.cross(ax, e1)
    side = 2 * rg * math.tan(math.pi / n)
    for k in range(n):
        th = TAU * k / n
        d = math.cos(th) * e1 + math.sin(th) * e2
        t = -math.sin(th) * e1 + math.cos(th) * e2
        m = np.asarray(c, float) + d * rg
        barre(g, f"{nom}_{k}", m - t * side / 2, m + t * side / 2, s, "bloc_argent", ov=s * 0.42, Y=d)


def flocon(g, nom, c, N, e0, Rf):
    """Flocon en relief posé sur une face de normale N : 3 bras (diamètres) + 12 branches, barres à section losange."""
    N = unit(N)
    e0 = unit(e0 - (e0 @ N) * N)
    e1 = np.cross(N, e0)
    c = np.asarray(c, float) + N * 0.06
    for k in range(3):
        th = math.radians(60 * k)
        e = math.cos(th) * e0 + math.sin(th) * e1
        barre(g, f"{nom}_bras{k}", c - e * Rf, c + e * Rf, 0.16, "bloc_flocon", Y=N, roll=45)
    for k in range(6):
        th = math.radians(60 * k)
        e = math.cos(th) * e0 + math.sin(th) * e1
        for fr, ln in ((0.5, 0.36), (0.78, 0.24)):
            base = c + e * Rf * fr
            for sg in (-1, 1):
                t2 = th + sg * math.radians(55)
                e2 = math.cos(t2) * e0 + math.sin(t2) * e1
                barre(g, f"{nom}_br{k}{'pm'[sg < 0]}{int(fr * 10)}", base - e2 * 0.05, base + e2 * ln, 0.1, "bloc_flocon", Y=N, roll=45)


def eclat(key, parent, pivot, c, r, tile="star"):
    """Éclat (étoile additive) replié autour de `pivot` : trois plaques croisées."""
    g = group(key, pivot, parent=parent, repli=np.asarray(pivot, float))
    ag = group(f"add_{key}", c, parent=g)
    for k_, (n, up) in enumerate(((Z_W, A_W), (A_W, B_W), (B_W, Z_W))):
        plaque(ag, f"{key}{k_}", np.asarray(c, float), n, up, 2 * r, 2 * r, tile, th=0.3 + 0.02 * k_)
    return g


# ---- cotes (repère local a, b, z ; px)
A_TALON = -4.4
A_BRIN = (2.45, 6.6, 10.2)       # départ des trois brins (pivots de flexion : bague d'arrêt, viroles)
A_TETE = 13.0                    # virole de tête
A_CRIS = 13.55                   # pied de la pointe de cristal
GUIDES = ((4.4, 0.66), (8.3, 0.56), (11.5, 0.46))   # (a, apothème de l'anneau) : anneaux surdimensionnés (canne de glace)
A_MOUL = -2.35                   # moulinet sous le porte-moulinet
R_PL, R_BOB = 1.55, 1.0          # flasques, bobine (apothèmes)
Z_PL, Z_GAP = 0.8, 0.42          # demi-épaisseur du moulinet, demi-largeur de la bobine
TIGE = 0.45                      # pied du moulinet
R_SIEGE = 0.78


def r_scion(a):
    return 0.64 + (0.30 - 0.64) * (a - A_BRIN[0]) / (A_TETE - A_BRIN[0])


PROFIL_BASE = (bague(-3.75, -3.3, 0.40, R_SIEGE, 0.92, c=0.14)
               + [(-3.3, R_SIEGE, -1.4, R_SIEGE, [("siege", {})])]
               + bague(-1.4, -0.95, R_SIEGE, 0.86, 0.98, c=0.14)
               + [(-0.95, 0.86, 1.95, 0.80, [("poignee", {}), ("poignee", {"clous": False})])]
               + bague(1.95, A_BRIN[0] + 0.12, 0.80, r_scion(A_BRIN[0]) + 0.02, 0.9, c=0.14))


def centre_anneau(a, rg):
    return W(a, -(r_scion(a) + 0.16 + rg + 0.1))


A_ANT = 13.28                                 # anneau de tête, sur la virole de tête
R_ANT = 0.24
C_ANT = W(A_ANT, -(0.52 + 0.12 + R_ANT + 0.08))
C_MOUL = W(A_MOUL, -(R_SIEGE + TIGE + R_PL))
P_BOB = C_MOUL + B_W * (R_BOB + 0.1)          # la ligne quitte la bobine par le haut
PIV_TETE = W(14.05)                           # pivot des éclats de la pointe (dans l'âme du cristal)
Y_BAS_LIGNE = 4.6                             # la ligne pendante descend jusqu'ici (image vanilla)
PROFIL_CRIS = [(0.0, 0.44), (0.55, 0.52)]
L_CRIS = A_FIN - A_CRIS


def brin(g_ame, g_trans, i, a0, a1, p):
    """Brin de glace hexagonal de a0 à a1 (peau trans_ + âme opaque), raccord caché sous les viroles."""
    pts = [(0.0, r_scion(a0)), (a1 - a0, r_scion(a1))]
    prof_p = [(0.0, pts[0][1], pts[1][0], pts[1][1], PEAU)]
    prof_a = [(0.0, r_ame(pts[0][1]), pts[1][0], r_ame(pts[1][1]), AME)]
    tour(g_trans, f"{p}sp{i}", f"sp{i}", W(a0), A_W, Z_W, prof_p, n=6)
    tour(g_ame, f"{p}sa{i}", f"sa{i}", W(a0), A_W, Z_W, prof_a, n=6)
    if p == "r":
        AME_SEG.append((a0, a1, r_ame(pts[0][1]), r_ame(pts[1][1])))


def aiguilles(g_parent, p, seed):
    """Givre de la pointe lancée : aiguilles sur le cristal (penchées vers la pointe) et sur la virole ; une par groupe."""
    rng = np.random.default_rng(seed)
    out = []
    e_z, e_w = Z_W, np.cross(A_W, Z_W)
    for j in range(11):
        if j < 8:
            s = A_CRIS + 0.15 + 1.0 * (j + rng.uniform(0.1, 0.9)) / 8
            r = float(np.interp(s - A_CRIS, [0, 0.55, L_CRIS], [0.44, 0.52, 0.0]))
            pente, Ln = 50, 0.75 + 0.45 * rng.uniform()
        else:
            s = A_TETE + 0.3
            r = 0.52
            pente, Ln = 62, 0.55 + 0.2 * rng.uniform()
        ph = math.radians(137.5 * j + rng.uniform(-12, 12))
        rad = math.cos(ph) * e_z + math.sin(ph) * e_w
        base = W(s) + rad * (r - 0.1)
        dirn = unit(rad * math.cos(math.radians(pente)) + A_W * math.sin(math.radians(pente)))
        gn = group(f"{p}_givre{j}", base, parent=g_parent)
        tour(gn, f"{p}aig{j}", f"aig{int(Ln * 10)}", base, dirn, A_W,
             [(0.0, 0.10, Ln * 0.55, 0.15, GIVRE), (Ln * 0.55, 0.15, Ln, 0.0, GIVRE)], n=6)
        out.append(gn)
    return out


def build(st):
    """Une copie complète de la canne dans le groupe d'étape `st` ; renvoie les groupes animés."""
    ETAPE["cur"] = st
    p = st[0]
    racine = group(objet.etape(st, "canne"), W(A_PRISE))
    base = group(f"{p}_canne", W(A_PRISE), parent=racine)
    tour(base, f"{p}b", "b", W(0), A_W, B_W, PROFIL_BASE, n=8, phase=math.pi / 8)
    # pique de cristal au talon (glace opaque, filet _e)
    tour(base, f"{p}pique", "pique", W(-3.65), -A_W, Z_W,
         [(0.0, 0.36, 0.2, 0.44, AME), (0.2, 0.44, A_TALON * -1 - 3.65 - 0.0, 0.0, AME)], n=6)
    # --- moulinet en ligne : semelle + tige, flasques hexagonales le long de z, bobine de ligne
    pied = W(A_MOUL, -R_SIEGE - 0.06)
    cube_c(base, f"{p}semelle", pied, (0.75, 0.12, 0.34), np.column_stack([A_W, B_W, Z_W]), {f: T("bloc_argent") for f in SIX})
    tour(base, f"{p}tige", "tige", W(A_MOUL, -R_SIEGE), -B_W, A_W, [(0.0, 0.28, TIGE + 0.12, 0.24, ARG)], n=6)
    moul = group(f"{p}_moulinet", C_MOUL, parent=base)
    prof_m = [(-Z_PL, R_PL - 0.18, -Z_PL + 0.15, R_PL, [("argent", {"clair": 0.15})]),
              (-Z_PL + 0.15, R_PL, -Z_GAP, R_PL, ARG),
              (-Z_GAP, R_PL, -Z_GAP, R_BOB, [("mur", {"rmin": R_BOB, "rmax": R_PL})]),
              (-Z_GAP, R_BOB, Z_GAP, R_BOB, [("bobine", {})]),
              (Z_GAP, R_BOB, Z_GAP, R_PL, [("mur", {"rmin": R_BOB, "rmax": R_PL})]),
              (Z_GAP, R_PL, Z_PL - 0.15, R_PL, ARG),
              (Z_PL - 0.15, R_PL, Z_PL, R_PL - 0.18, [("argent", {"clair": -0.12})])]
    tour(moul, f"{p}m", "m", C_MOUL, Z_W, A_W, prof_m, n=6, phase=math.pi / 6)
    face = t_disque6("flasque", R_PL - 0.18)
    for s, cs in ((1, "av"), (-1, "ar")):
        disque(moul, f"{p}fl_{cs}", C_MOUL + Z_W * s * Z_PL, Z_W * s, A_W, R_PL - 0.18, face)
        flocon(moul, f"{p}floc_{cs}", C_MOUL + Z_W * s * Z_PL, Z_W * s, A_W, 1.12)
        tour(moul, f"{p}gem_{cs}", "gemme", C_MOUL + Z_W * s * (Z_PL + 0.02), Z_W * s, A_W,
             [(0.0, 0.3, 0.16, 0.3, GEMME), (0.16, 0.3, 0.4, 0.0, GEMME)], n=6, phase=math.pi / 6)
    # manivelle : bras d'argent + bouton de cristal (sur la face avant, côté talon)
    d_m = unit(-A_W - 0.4 * B_W)
    zb = Z_PL + 0.36
    barre(moul, f"{p}bras", C_MOUL + Z_W * zb + d_m * 0.3, C_MOUL + Z_W * zb + d_m * 1.3, 0.26, "bloc_argent")
    tour(moul, f"{p}bouton", "bouton", C_MOUL + d_m * 1.18 + Z_W * (zb + 0.08), Z_W, A_W,
         [(0.0, 0.24, 0.35, 0.28, AME), (0.35, 0.28, 0.75, 0.0, AME)], n=6)
    tour(moul, f"{p}axe", "axe", C_MOUL + Z_W * Z_PL, Z_W, A_W, [(0.0, 0.18, 0.5, 0.18, ARG)], n=6)

    # --- scion : trois brins imbriqués (pivots aux viroles), anneaux ligaturés, ligne dans les anneaux
    brins, parent = [], base
    bornes = list(A_BRIN) + [A_TETE + 0.1]
    for i, a0 in enumerate(A_BRIN):
        g = group(f"{p}_brin{i + 1}", W(a0), parent=parent)
        ga = group(f"{p}_ame{i + 1}", W(a0), parent=g)
        gt = group(f"trans_{p}_brin{i + 1}", W(a0), parent=g)
        brin(ga, gt, i, a0 - (0.1 if i else 0.0), bornes[i + 1] + 0.05, p)
        if i:                                                  # virole d'argent au raccord (cache le joint du brin)
            tour(g, f"{p}vir{i}", f"vir{i}", W(0), A_W, Z_W,
                 bague(a0 - 0.32, a0 + 0.32, r_scion(a0 - 0.32) - 0.02, r_scion(a0 + 0.32) - 0.02, r_scion(a0) + 0.14, c=0.1), n=6)
        brins.append(g)
        parent = g
    pts_ligne = [P_BOB]
    for ga_, rg in GUIDES:
        i = sum(ga_ >= a0 for a0 in A_BRIN) - 1
        c = centre_anneau(ga_, rg)
        anneau(brins[i], f"{p}an{ga_:.0f}", c, A_W, rg)
        barre(brins[i], f"{p}pied{ga_:.0f}", W(ga_, -r_scion(ga_) + 0.1), c + B_W * (rg - 0.05), 0.2, "bloc_argent", Y=A_W)
        tour(brins[i], f"{p}lig{ga_:.0f}", f"lig{ga_:.0f}", W(0), A_W, Z_W,
             bague(ga_ - 0.3, ga_ + 0.3, r_scion(ga_ - 0.3) - 0.02, r_scion(ga_ + 0.3) - 0.02, r_scion(ga_) + 0.07, c=0.08), n=6)
        pts_ligne.append(c)
    tete = group(f"{p}_tete", W(A_TETE), parent=brins[-1])
    tour(tete, f"{p}vt", "vt" + p, W(0), A_W, Z_W, bague(A_TETE - 0.05, A_CRIS + 0.05, r_scion(A_TETE) - 0.02, 0.44, 0.52, c=0.12,
                                                          ex={"givre": st == "lancee"}), n=6)
    anneau(tete, f"{p}ant", C_ANT, A_W, R_ANT, s=0.2)
    barre(tete, f"{p}piedant", W(A_ANT, -0.45), C_ANT + B_W * (R_ANT - 0.05), 0.2, "bloc_argent", Y=A_W)
    pts_ligne.append(C_ANT)
    owners = [base] + brins
    for j in range(len(pts_ligne) - 1):
        g = owners[min(j, len(owners) - 1)]
        barre(g, f"{p}ligne{j}", pts_ligne[j], pts_ligne[j + 1], 0.14, "bloc_ligne", ov=0.05, Y=Z_W, bouts=False)
    # pointe de cristal (repos : claire ; lancée : givrée)
    gc = group(f"{p}_cristal", W(A_CRIS), parent=tete)
    gca = group(f"{p}_cristal_ame", W(A_CRIS), parent=gc)
    gct = group(f"trans_{p}_cristal", W(A_CRIS), parent=gc)
    cristal(gct, gca, f"{p}cris", "cr" + p, W(A_CRIS), A_W, Z_W, PROFIL_CRIS, L_CRIS,
            peau=PEAU_G if st == "lancee" else PEAU, axe_canne=A_CRIS if p == "r" else None)
    out = {"racine": racine, "moul": moul, "brins": brins, "tete": tete, "cristal": gc}

    if st == "repos":
        # --- ligne pendante (image vanilla), perle de cristal, cuillère d'argent, hameçon
        lg = group("r_ligne", C_ANT, parent=tete)
        bas = V(C_ANT[0], Y_BAS_LIGNE, C_ANT[2])
        barre(lg, "r_pend", C_ANT, bas, 0.2, "bloc_ligne", ov=0.05, Y=Z_W)
        le = group("r_leurre", bas, parent=lg)
        tour(le, "r_perle", "perle", bas + V(0, 0.08, 0), V(0, -1, 0), V(0, 0, 1),
             [(0.0, 0.2, 0.25, 0.27, AME), (0.25, 0.27, 0.62, 0.0, AME)], n=6)
        cu0 = bas + V(0, -0.7, 0)
        tour(le, "r_cuill", "cuill", cu0, V(0, -1, 0), V(0, 0, 1),
             [(0.0, 0.06, 0.25, 0.3, [("argent", {"clair": 0.15})]), (0.25, 0.3, 0.95, 0.42, ARG),
              (0.95, 0.42, 1.35, 0.0, [("argent", {"clair": -0.1})])], n=6)
        h0 = cu0 + V(0, -1.3, 0)
        croc = [h0, h0 + V(0.0, -0.5, 0), h0 + V(0.26, -0.8, 0), h0 + V(0.58, -0.66, 0), h0 + V(0.66, -0.24, 0)]
        for j in range(4):
            barre(le, f"r_croc{j}", croc[j], croc[j + 1], 0.18, "bloc_argent", ov=0.07, Y=Z_W)
        barre(le, "r_ardillon", croc[-1], croc[-1] + V(-0.2, -0.18, 0), 0.16, "bloc_argent", ov=0.05, Y=Z_W)
        # --- éclats repliés dans l'âme : scintillement (item_idle), éclat d'arrivée en main (event_select), course le long du scion
        bout = W(A_FIN - 0.15)
        out["scint"] = eclat("r_scint", tete, PIV_TETE, bout, 1.0)
        out["eclat_sel"] = eclat("r_eclat_sel", tete, PIV_TETE, bout + A_W * 0.1, 1.4)
        out["course"] = [eclat("r_course1", brins[0], W(4.0), W(4.0, 0, 0.55), 0.9),
                         eclat("r_course2", brins[1], W(7.6), W(7.6, 0, 0.48), 0.8)]
        out["ligne"], out["leurre"] = lg, le
    else:
        out["givre"] = aiguilles(group("l_givre", W(A_CRIS), parent=tete), "l", 7)
        bout = W(A_FIN - 0.15)
        out["scints"] = [eclat("l_scint0", tete, PIV_TETE, bout, 0.9),
                         eclat("l_scint1", tete, PIV_TETE, W(A_CRIS + 0.5, 0.3, 0.45), 0.7)]
        out["eclat_lan"] = eclat("l_eclat_lan", tete, PIV_TETE, bout + A_W * 0.1, 1.5)
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


def r_ame_a(a):
    """Rayon de l'âme opaque à l'abscisse a (-1 hors âme)."""
    best = -1.0
    for a0, a1, r0, r1 in AME_SEG:
        if a0 <= a <= a1 and a1 > a0:
            best = max(best, r0 + (r1 - r0) * (a - a0) / (a1 - a0))
    return best


# contrôle : chaque éclat replié reste dans l'âme opaque (scion ou cristal)
_hors, _noms = 0, set()
for e in elements:
    if e["uuid"] not in CACHES:
        continue
    for c in coins_de(e):
        a, rr = (c - G0) @ A_W, math.hypot((c - G0) @ B_W, (c - G0) @ Z_W)
        if not rr < r_ame_a(a) * 0.97 - 0.03:
            _hors += 1
            _noms.add(e["name"])
assert _hors == 0, f"{_hors} {sorted(_noms)[:8]} coins d'éclats repliés hors de l'âme"


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


def H(x):
    return f"math.mod(math.abs(math.sin(({x})*127.1))*437.585,1)"


def echant(L, n):
    return [L * i / n for i in range(n + 1)]


def pop(t0, t1, L, haut=KU):
    """Éclat qui s'ouvre vite (t0), pulse et se referme (t1)."""
    return [kf("scale", 0, 1), kf("scale", t0, 1), kf("scale", t0 + 0.03, haut * 1.1), kf("scale", (t0 + t1) / 2, haut * 0.75),
            kf("scale", t1, 1), kf("scale", L, 1)]


FLEX = (0.25, 0.35, 0.4)         # part de la flexion portée par chaque brin (cumulée le long du scion)
R_, L_ = F["repos"], F["lancee"]

# item_idle (6 s, boucle)
L_IDLE = 6.0
idle = anim("item_idle", L_IDLE)
piste(idle, R_["ligne"], [kf("rotation", t, 2.5 * math.sin(TAU * t / L_IDLE + 1.2), 0, 2.0 * math.sin(TAU * 2 * t / L_IDLE))
                          for t in echant(L_IDLE, 24)])
piste(idle, R_["leurre"], [kf("rotation", t, 3.0 * math.sin(TAU * 2 * t / L_IDLE + 0.4), 360 * t / L_IDLE,
                                3.0 * math.sin(TAU * t / L_IDLE - 0.9)) for t in echant(L_IDLE, 24)])
piste(idle, R_["scint"], [kf("scale", 0, 1), kf("scale", 2.4, 1), kf("scale", 2.45, KU), kf("scale", 2.62, KU * 0.6),
                          kf("scale", 2.7, 1), kf("scale", 4.9, 1), kf("scale", 4.95, KU * 0.8), kf("scale", 5.08, 1),
                          kf("scale", L_IDLE, 1)])
for i, g in enumerate(L_["scints"]):
    pr = 0.05                                     # ~0,8 scintillement/s chacun, 125 ms
    expr = f"({H(f'math.floor(q.life_time*8)*1.731+{0.37 + 17.3 * i:.2f}+q.instance_seed*17')}<{pr})?{KU:g}:1"
    assert len(expr) <= 512
    piste(idle, g, [kf("scale", 0.0, expr)])
piste(idle, L_["brins"][2], [kf("rotation", t, 0, 0, 0.35 * math.sin(TAU * 6 * t / L_IDLE) * math.sin(TAU * t / L_IDLE) ** 2)
                             for t in echant(L_IDLE, 48)])


# event_enter_lancee (0,9 s) : petit coup sec (la glace ne plie presque pas), le moulinet se dévide (2 tours)
def flex_lancer(t):
    if t < 0.16:
        return 4.0 * math.sin(math.pi / 2 * t / 0.16)
    if t < 0.26:
        u = (t - 0.16) / 0.1
        return 4.0 - 10.0 * (u * u * (3 - 2 * u))
    return -6.0 * math.exp(-(t - 0.26) / 0.1) * math.cos(TAU * (t - 0.26) / 0.16)


L_LAN = 0.9
lancer = anim("event_enter_lancee", L_LAN, "once")
ts = echant(L_LAN, 36)
for g, f_ in zip(L_["brins"], FLEX):
    piste(lancer, g, [kf("rotation", t, 0, 0, round(f_ * flex_lancer(t) * (1 if t < L_LAN - 1e-6 else 0), 3)) for t in ts])
piste(lancer, L_["moul"], [kf("rotation", t, 0, 0, -720 * (1 - (1 - t / L_LAN) ** 3) if t > 0.2 else
                              -720 * (1 - (1 - t / L_LAN) ** 3) * (t / 0.2) ** 2) for t in ts])
T_PART = 0.26
piste(lancer, L_["eclat_lan"], pop(T_PART, T_PART + 0.22, L_LAN))
for j, g in enumerate(L_["givre"]):            # le givre pousse en cascade, de la virole vers la pointe
    t0 = T_PART + 0.03 * ((j + 3) % 11)
    piste(lancer, g, [kf("scale", 0, 0.08), kf("scale", t0, 0.08), kf("scale", t0 + 0.16, 1.12), kf("scale", t0 + 0.24, 1.0),
                      kf("scale", L_LAN, 1.0)])

# event_enter_repos (0,8 s) : le moulinet ramène (2 tours), la ligne retombe en se balançant, petit à-coup du scion
L_REP = 0.8
ramene = anim("event_enter_repos", L_REP, "once")
ts = echant(L_REP, 32)
sm3 = lambda u: u * u * (3 - 2 * u)
piste(ramene, R_["moul"], [kf("rotation", t, 0, 0, 720 * sm3(t / L_REP)) for t in ts])
piste(ramene, R_["ligne"], [kf("rotation", t, 0, 0, 0 if t >= L_REP - 1e-6 else 45 * math.exp(-t / 0.16) * math.cos(TAU * t / 0.42))
                            for t in ts])
piste(ramene, R_["leurre"], [kf("rotation", t, 0, 0, 0 if t >= L_REP - 1e-6 else
                                 -25 * math.exp(-t / 0.2) * math.sin(TAU * t / 0.36)) for t in ts])
for g, f_ in zip(R_["brins"], FLEX):
    piste(ramene, g, [kf("rotation", t, 0, 0, 0 if t >= L_REP - 1e-6 else round(f_ * 3.0 * math.exp(-t / 0.1) * math.sin(TAU * t / 0.16), 3))
                      for t in ts])

# event_select (0,7 s) : la glace pousse : la pointe grandit depuis sa virole, deux éclats courent le long du scion
L_SEL = 0.7
sel = anim("event_select", L_SEL, "once")
piste(sel, R_["cristal"], [kf("scale", 0, 0.15), kf("scale", 0.3, 0.15), kf("scale", 0.44, 1.1), kf("scale", 0.52, 0.97),
                           kf("scale", 0.6, 1.0), kf("scale", L_SEL, 1.0)])
piste(sel, R_["course"][0], pop(0.04, 0.16, L_SEL, haut=KU * 0.9))
piste(sel, R_["course"][1], pop(0.16, 0.28, L_SEL, haut=KU * 0.9))
piste(sel, R_["eclat_sel"], pop(0.44, 0.66, L_SEL))
piste(sel, R_["ligne"], [kf("rotation", t, 0, 0, 0 if t >= L_SEL - 1e-6 else
                            round(8 * math.exp(-max(t - 0.44, 0) / 0.12) * math.sin(TAU * max(t - 0.44, 0) / 0.3), 3))
                         for t in echant(L_SEL, 28)])

# event_swing (0,3 s) : petit frémissement du bout ; seul son du modèle (lancer et remontée), à 0,04 s
L_SW = 0.3
swing = anim("event_swing", L_SW, "once")
for st_ in (R_, L_):
    piste(swing, st_["tete"], [kf("rotation", t, 0, 0, 0 if t >= L_SW - 1e-6 else round(1.2 * math.exp(-t / 0.08) * math.sin(TAU * t / 0.1), 3))
                               for t in echant(L_SW, 12)])

ANIMS = [idle, lancer, ramene, sel, swing]

# ------------------------------------------------------------------ atlas (tuiles des pans créées pendant la géométrie)
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_x = _y = _sh = 0
for n, (im, em) in sorted(TUILES.items(), key=lambda it: (-it[1][0].shape[0], -it[1][0].shape[1])):
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
semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
zone = np.zeros(semi.shape, bool)
for n in TRANS:
    u0, v0, u1, v1 = UV[n]
    zone[v0:v1, u0:u1] = True
assert not (semi & ~zone).any(), "semi-transparence hors des tuiles trans_"
assert set(np.unique(tex_e[..., 3])) <= {0, 255}
# les tuiles trans_ ne servent que dans des groupes trans_
_trans_ids = set()
for n_, g in groups.items():
    gg, inside = n_, False
    while gg:
        if groups[gg]["name"].startswith("trans_"):
            inside = True
            break
        gg = groups[gg]["parent"]
    if inside:
        _trans_ids.update(g["ids"])
for e in elements:
    for f, fc in e["faces"].items():
        if fc["uv"] == CLEAR:
            fc["uv"] = UV_CLEAR
        else:
            nom, (u0, v0, u1, v1) = fc["uv"]
            assert nom not in TRANS or e["uuid"] in _trans_ids, f"tuile trans_ {nom} hors d'un groupe trans_ ({e['name']})"
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
# Display : préréglage _CANNE (item/handheld_rod du jar) ; gui ramené à la case (étape repos, ligne comprise)
_bb = np.array([c for e in elements if e["uuid"] not in CACHES and ELEM_ETAPE[e["uuid"]] == "repos" for c in coins_de(e)])
_cb = (_bb.min(axis=0) + _bb.max(axis=0)) / 2
GUI = round(min(1.0, 15.6 / float(max(_bb.max(axis=0)[:2] - _bb.min(axis=0)[:2]))), 2)
GUI_T = [round(float(-(_cb[0] - 8) * GUI), 2), round(float(-(_cb[1] - 8) * GUI), 2), 0]
AFFICHAGE = objet.affichage("canne", gui={"translation": GUI_T, "scale": [GUI] * 3})
model = objet.modele(NOM, "canne", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son
limiter_sons(model)
# Un seul son, au lancer (event_swing, aussi joué à la remontée et à chaque coup) ; clé à 0,04 s (une clé à 0,0 est muette au
# premier passage) ; aucun son à event_enter_lancee (rejoué à chaque bascule repos/lancee, recette 4 de categories/objets.md).
swing["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "block.amethyst_block.chime")]}
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
