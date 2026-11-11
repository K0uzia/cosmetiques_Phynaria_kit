"""Leurre de l'Abysse : skin d'objet (guide 14) pour toutes les cannes à pêche du joueur, ensemble Abyssal (thème Démoniaque).
Design original. Écrit skin_canne_abyssal.png, skin_canne_abyssal_e.png et .build/skin_canne_abyssal_brut.bbmodel.

Idée (approche par analogie, `.claude/references/objets/cannes-a-peche.md`) : les poissons des grands fonds pêchent avec
une épine dorsale devenue canne, au bout de laquelle pend un leurre qui luit. La canne des Chasseurs est cette épine :
- talon en **griffe** conique à pointe verte, porte-moulinet d'os bagué de violet, poignée de cuir pourpre-noir en spirale à
  trois clous d'os pâle, bague d'arrêt violacée ;
- **moulinet-vertèbre** sous la canne (côté −b, le bas en 3e personne) : tambour à 16 pans, flasques d'os cerclées de violet,
  **couronne de 6 crocs** sur chaque flasque (pointes vertes), gouttière creusée entre les flasques où la ligne verte est
  enroulée (spires + `_e`), médaillon d'os à bossette en griffe, manivelle d'os à bouton de cuir ;
- **scion d'os** à 8 pans qui s'affine (0,62 → 0,27 px) en trois brins joints par des bagues violacées (pivots de flexion),
  **épines dorsales** recourbées vers le talon sur le dos (+b, le haut) à chaque brin, anneaux d'os violacés côté −b ;
- tête : collet d'os, **pointe en griffe** recourbée à bout vert + `_e` en (15 ; 15), d'où part la ligne du jeu ;
- ligne = fil de lueur verte (`_e`, comme la corde de l'arc du set) du moulinet au bout, dans les anneaux.
Au repos (`repos`), la ligne pend comme sur l'image vanilla et porte le **leurre** : bulbe d'os en goutte fendu de huit
gouttières vertes (`_e`), pointe verte, hameçon d'os en croc. Lancée (`lancee`), ligne et leurre sont partis (le jeu dessine
sa ligne et son flotteur, non personnalisables) ; la pointe luit.

Vrai volume (`.claude/references/objets/volume-3d.md`, tours de `skin_canne_orage`) : toute pièce ronde est un tour (profil
(a, rayon), couronne de pans de 0,3 px posés sur la surface, face extérieure peinte et découpée par l'alpha, tranches
transparentes) ; griffes en tronçons coniques ; anneaux = barres pleines en octogone. Aucune plaque peinte empilée.

Repère : comme `fishing_rod.png` vue de +Z, talon en bas à gauche, pointe en haut à droite (15 ; 15) ; moulinet, anneaux
et ligne côté −b (bas en 3e personne). Display : préréglage `_CANNE` de `tools/objet.py`, `gui` ramené à la case.

Objet vivant (guide 14), format free :
- item_idle (4 s, boucle) : la ligne et le leurre se balancent (le leurre tourne lentement), le leurre et la pointe
  respirent (`ctrl_lumiere`), les épines ondulent ; lancée : la pointe pulse, le bout frémit ;
- event_enter_lancee (0,9 s) : le scion se charge puis fouette (trois brins en cascade), le moulinet se dévide (3 tours),
  la pointe s'allume ; **aucun son** (recette 4 de `categories/objets.md`) ;
- event_enter_repos (0,8 s) : le moulinet ramène (2 tours), la ligne et le leurre retombent en se balançant ;
- event_select (0,6 s) : la pointe-griffe sort du collet (**seul dépliage par `scale`**), les épines se dressent l'une après
  l'autre, la ligne sursaute, le leurre s'allume ;
- event_swing (0,4 s) : les épines se hérissent, la lueur s'avive ; **seul son du modèle** `block.sculk.break` à 0,04 s
  (event_swing part au lancer, à la remontée et à chaque coup).
Fonctions avancées : calque `_e`, `ctrl_lumiere` (non simulé), `scale` animé, son d'objet. Pas de particules.
À juger en jeu : la ligne du jeu qui part de la pointe lancée, le son d'event_swing (lancer et remontée), la canne dans la case.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import objet
import numpy as np
from PIL import Image

AVEC_E = True
NOM = "skin_canne_abyssal"
TEX = 512
DENS = 16.0              # texels par px sur les pans
TH = 0.3                 # épaisseur d'un pan
TAU = 2 * math.pi


def lerp(a, b, k):
    return a + (b - a) * k


def C(*c):
    return np.asarray(c, np.float32)


# ------------------------------------------------------------------ palette du set (sets-objets-2026-11-08.md, Abyssal)
OS_CLAIR, OS_BASE, OS_SOMBRE = C(58, 50, 72), C(30, 25, 40), C(14, 10, 20)
ARETE, REFLET = C(126, 92, 170), C(98, 68, 126)
AURA, VEIN, VCORE, FIL = C(22, 66, 40), C(96, 200, 44), C(150, 244, 70), C(190, 255, 96)
E_COL = C(82, 211, 53)
CUIR0, CUIR1 = C(84, 44, 98), C(38, 18, 48)

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
        if m.any():
            e = np.zeros((H, W, 4), np.uint8)
            e[..., :3] = np.clip(em, 0, 225).astype(np.uint8)
            e[..., 3] = m * 255
            e[~m, :3] = 0
    return out, e


# --- peintres des pans : xn en travers (-1..1, bords du pan), t le long (0 = P0, 1 = P1), y en px depuis P0, r le rayon
def p_os(xn, t, y, r, L, ex):
    k = np.clip(0.35 + 0.45 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    yy = y + ex.get("y0", 0.0)
    col = lerp(OS_SOMBRE, OS_CLAIR, k[..., None]) * (1 + 0.06 * np.sin(yy * 23 + xn))[..., None]
    col = np.where((np.abs(xn) < 0.22)[..., None], lerp(col, REFLET, 0.45), col)
    return col, None


def p_bague(xn, t, y, r, L, ex):
    k = np.clip(0.4 + 0.5 * (1 - np.abs(xn)) + ex.get("clair", 0.0), 0, 1)
    return lerp(OS_BASE, ARETE, k[..., None] * 0.8), None


def p_cuir(xn, t, y, r, L, ex):
    f = (((y + ex.get("y0", 0.0)) / 0.62 + xn * 0.16) % 1.0)[..., None]
    col = lerp(CUIR0, CUIR1, f)
    col = np.where(f > 0.82, C(14, 7, 18), col)
    return col * (1 + 0.04 * np.sin(xn * 3 + y * 11))[..., None], None


def p_clou(xn, t, y, r, L, ex):
    k = (1 - np.abs(xn))[..., None]
    return lerp(C(150, 132, 160), C(214, 200, 218), k), None


def p_griffe(xn, t, y, r, L, ex):
    """Griffe d'os : sombre aux bords, reflet violacé au milieu, bagues de croissance, pointe vert acide + _e."""
    tg = ex["t0"] + (ex["t1"] - ex["t0"]) * t
    q = np.abs(xn)
    col = lerp(C(54, 48, 66), C(26, 22, 34), (q ** 1.2)[..., None])
    col = lerp(col, C(132, 98, 176), (np.clip(1 - q * 2.4, 0, 1) * 0.45)[..., None])
    col = col * (1 - 0.18 * (np.sin(tg * 40.0) > 0.85))[..., None]
    col = lerp(col, C(132, 240, 58), np.clip((tg - 0.62) / 0.25, 0, 1)[..., None])
    em = np.zeros(col.shape, np.float32)
    on = tg > 0.74
    em[on] = lerp(C(44, 110, 26), C(96, 230, 58), np.clip((tg[on] - 0.74) / 0.2, 0, 1)[..., None])
    return col, em


def p_mur(xn, t, y, r, L, ex):
    """Paroi de la gouttière du moulinet : os sombre, liseré violacé en haut, halo vert sombre au fond."""
    k = np.clip((r - ex["rmin"]) / max(ex["rmax"] - ex["rmin"], 1e-6), 0, 1)
    col = lerp(OS_SOMBRE, OS_BASE, (k ** 1.2)[..., None])
    col = np.where((r < ex["rmin"] + 0.14)[..., None], AURA, col)
    col = np.where((r > ex["rmax"] - 0.1)[..., None], ARETE, col)
    return col, None


def p_bobine(xn, t, y, r, L, ex):
    """Ligne verte enroulée dans la gouttière : spires vives + _e sur fond vert très sombre."""
    base = lerp(OS_SOMBRE, AURA, (0.3 + 0.5 * (1 - np.abs(xn)))[..., None])
    spire = np.mod(y * 6.0 + 0.15 * xn, 1) < 0.5
    col = np.where(spire[..., None], lerp(VEIN, FIL, (1 - np.abs(xn))[..., None]), base)
    em = np.zeros(xn.shape + (3,), np.float32)
    em[spire] = E_COL * 0.8
    return col, em


def p_leurre(xn, t, y, r, L, ex):
    """Bulbe du leurre : os sombre fendu d'une gouttière verte par pan (huit en tout), halo vert sombre autour."""
    k = np.clip(0.3 + 0.5 * (1 - np.abs(xn)), 0, 1)
    col = lerp(OS_SOMBRE, OS_CLAIR, k[..., None])
    q = np.abs(xn)
    g0, g1 = ex.get("g", (0.0, 1.0))
    tg = g0 + (g1 - g0) * t
    fente = (q < 0.26) & (tg > 0.12) & (tg < 0.9)
    halo = (q < 0.5) & (tg > 0.06) & (tg < 0.96)
    col = np.where(halo[..., None], AURA, col)
    col = np.where((halo & ~fente & (q > 0.4))[..., None], ARETE, col)
    col = np.where(fente[..., None], lerp(VEIN, FIL, np.clip(1 - q / 0.26, 0, 1)[..., None]), col)
    em = np.zeros(xn.shape + (3,), np.float32)
    em[fente] = E_COL
    return col, em


PEINTRES = {"os": p_os, "bague": p_bague, "cuir": p_cuir, "clou": p_clou, "griffe": p_griffe, "mur": p_mur, "bobine": p_bobine,
            "leurre": p_leurre}
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
    col, em = PEINTRES[mat](xn, t, y, r, L, dict(ex, w=max(w0, w1)))
    return tuile(nom, *_rgba(col, mask, em))


def t_disque(nom, n, Ra, N=56):
    """Face d'os d'un médaillon : os marbré, cercle violacé, bord sombre (découpée au polygone de n pans)."""
    R = Ra / math.cos(math.pi / n)
    yy, xx = np.mgrid[0:N, 0:N]
    x = ((xx + 0.5) / N - 0.5) * 2 * R
    y = (0.5 - (yy + 0.5) / N) * 2 * R
    th = np.arctan2(y, x)
    sect = np.round(th / (TAU / n)) * (TAU / n)
    apo = x * np.cos(sect) + y * np.sin(sect)
    mask = apo <= Ra
    rr = apo / Ra
    col = lerp(OS_CLAIR, OS_BASE, rr[..., None] ** 1.3) * (1 + 0.05 * np.sin(np.hypot(x, y) * 14))[..., None]
    col[(rr > 0.66) & (rr < 0.78)] = ARETE
    col[rr > 0.92] = OS_SOMBRE
    return tuile(nom, *_rgba(col, mask))


def t_bloc(nom, mat, W=16, H=16):
    """Tuile pleine d'une barre (anneaux, pieds, hameçon, ligne) : dégradé en travers."""
    yy, xx = np.mgrid[0:H, 0:W]
    x = (xx + 0.5) / W * 2 - 1
    k = (1 - np.abs(x)) ** 0.8
    em = None
    if mat == "os":
        col = lerp(OS_BASE, OS_CLAIR * 1.1, k[..., None])
        col = np.where((np.abs(x) > 0.8)[..., None], OS_SOMBRE, col)
    elif mat == "bague":
        col = lerp(OS_BASE, ARETE, k[..., None])
    elif mat == "ligne":
        col = lerp(VEIN, FIL, k[..., None])
        em = np.broadcast_to(E_COL, col.shape).copy()
    elif mat == "vert":
        col = lerp(VCORE, FIL, k[..., None])
        em = np.broadcast_to(E_COL, col.shape).copy()
    else:
        col = lerp(OS_SOMBRE, OS_BASE, k[..., None])
    return tuile(nom, *_rgba(col, np.ones(x.shape, bool), em))


for _m in ("os", "bague", "ligne", "vert"):
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
A_FIN = 17.2                     # bout de la pointe
TIP = V(15.0, 15.1, 8.0)         # coin d'où le jeu fait partir sa ligne
G0 = TIP - A_FIN * A_W
A_PRISE = 0.5                    # milieu de la poignée = point du poing


def W(a, b=0.0, z=0.0):
    return G0 + a * A_W + b * B_W + z * Z_W


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx (ordre du mod et du renderer)."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if abs(R[2, 0]) > 0.99999:
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
ELEM_ETAPE = {}


def nuid():
    return str(_uuid.uuid4())


def group(key, origin, parent=None, name=None):
    assert key not in groups, key
    name = name or key
    assert len(name) <= 64
    groups[key] = {"name": name, "origin": [round(float(v), 3) for v in np.asarray(origin, float)], "uuid": nuid(), "ids": [],
                   "parent": parent}
    return key


_ETAPE = ["repos"]


def cube_c(g, name, c, h, R, faces):
    """Cube de centre c (monde), demi-tailles h, axes R (colonnes), faces {face: CLEAR | (tuile, (u0, v0, u1, v1))}."""
    c, h = np.asarray(c, float), np.asarray(h, float)
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 4) for v in c - h],
         "to": [round(float(v), 4) for v in c + h], "origin": [round(float(v), 4) for v in c], "box_uv": False,
         "faces": {f: {"uv": uv, "texture": 0} for f, uv in faces.items()}}
    rot = euler(R)
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])
    ELEM_ETAPE[e["uuid"]] = _ETAPE[0]
    return e


def T(tile, u0=0.0, v0=0.0, u1=1.0, v1=1.0):
    return (tile, (u0, v0, u1, v1))


SIX = ("north", "south", "east", "west", "up", "down")


def tour(g, nom, tnom, O, ax, ref, profil, n=16, phase=0.0):
    """profil = [(b0, r0, b1, r1, mat, ex), ...] parcouru dans le sens +ax (rayon = apothème). `tnom` nomme les tuiles
    (partagées par les deux copies d'étape). Chaque pan : plaque de TH px, face extérieure (south) peinte."""
    O, ax = np.asarray(O, float), unit(np.asarray(ax, float))
    ref = unit(np.asarray(ref, float) - (np.asarray(ref, float) @ ax) * ax)
    w3 = np.cross(ax, ref)
    tn = math.tan(math.pi / n)
    for i, (b0, r0, b1, r1, mat, ex) in enumerate(profil):
        L = math.hypot(b1 - b0, r1 - r0)
        if L < 1e-4:
            continue
        tile = tuile_pan(f"{tnom}{i}", mat, L, 2 * r0 * tn, 2 * r1 * tn, r0, r1, ex)
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
            faces["south"] = T(tile)
            cube_c(g, f"{nom}{i}_{k}", c, (wm / 2, L / 2 + OVL, TH / 2), np.column_stack([X, Y, N]), faces)


def bague(b0, b1, ra, rb, ro, mat="bague", c=0.13, ex=None):
    """Bague biseautée : du rayon ra (b0) monte à ro, palier, redescend à rb (b1)."""
    ex = ex or {}
    return [(b0, ra, b0 + c, ro, mat, dict(ex, clair=0.12)), (b0 + c, ro, b1 - c, ro, mat, ex), (b1 - c, ro, b1, rb, mat, dict(ex, clair=-0.1))]


def disque(g, nom, c, N, up, Ra, tile, n=16):
    """Disque à n pans (apothème Ra) : plaque dont seule la face extérieure (normale N) est peinte."""
    N = unit(np.asarray(N, float))
    Y = unit(up - (up @ N) * N)
    X = np.cross(Y, N)
    R = Ra / math.cos(math.pi / n)
    faces = {f: CLEAR for f in SIX}
    faces["south"] = T(tile)
    cube_c(g, nom, np.asarray(c, float) - N * TH / 2, (R, R, TH / 2), np.column_stack([X, Y, N]), faces)


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


def anneau(g, nom, c, ax, rg, s=0.22, n=8, tile="bloc_bague"):
    """Anneau : n barres pleines en polygone (apothème rg) dans le plan perpendiculaire à `ax`."""
    ax = unit(np.asarray(ax, float))
    e1 = unit(B_W - (B_W @ ax) * ax)
    e2 = np.cross(ax, e1)
    side = 2 * rg * math.tan(math.pi / n)
    for k in range(n):
        th = TAU * k / n
        d = math.cos(th) * e1 + math.sin(th) * e2
        t = -math.sin(th) * e1 + math.cos(th) * e2
        m = np.asarray(c, float) + d * rg
        barre(g, f"{nom}_{k}", m - t * side / 2, m + t * side / 2, s, tile, ov=s * 0.42, Y=d)


def griffe(g, nom, tnom, p, X, Y, L, rmax, curve=0.30, nseg=6, n=6, cap=0.15):
    """Griffe recourbée en tronçons coniques : part de p (monde) vers X, se recourbe vers Y ; pointe verte + _e."""
    p, X = np.asarray(p, float), unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    nz = np.cross(X, Y)
    centre = lambda t: p + X * (L * (t - 0.12 * t * t)) + Y * (curve * L * t ** 2.1)
    ray = lambda t: rmax * (max(0.0, 1 - t) ** 0.8 + 0.06) / 1.06
    for i in range(nseg):
        t0, t1 = i / nseg, (i + 1) / nseg
        a, b = centre(t0), centre(t1)
        prof = [(0.0, ray(t0), float(np.linalg.norm(b - a)), ray(t1) if i < nseg - 1 else 0.0, "griffe", {"t0": t0, "t1": t1})]
        if i == 0 and cap > 0:
            prof.insert(0, (-cap, 0.0, 0.0, ray(0.0), "griffe", {"t0": 0.0, "t1": 0.0}))
        tour(g, f"{nom}{i}_", f"{tnom}{i}_", a, b - a, nz, prof, n=n)
    return centre(1.0)


# ---- cotes (repère local a, b, z ; px)
A_TALON = -4.3
A_BRIN = (2.75, 7.62, 11.95)     # départ des trois brins (pivots de flexion : bague d'arrêt, bagues violacées)
A_TETE = 15.2                    # début du collet de tête
GUIDES = ((5.2, 0.44), (9.5, 0.38), (12.9, 0.33), (14.4, 0.29))   # (a, rayon de l'anneau)
A_MOUL = -2.75                   # moulinet sous le porte-moulinet
R_PL, R_BOB = 1.7, 1.12          # flasques, bobine
Z_PL, Z_GAP = 0.85, 0.46         # demi-épaisseur du tambour, demi-largeur de la gouttière
TIGE = 0.5                       # pied du moulinet
A_POINTE = 15.85                 # naissance de la pointe-griffe (dans le collet)


def r_scion(a):
    return 0.62 + (0.27 - 0.62) * (a - A_BRIN[0]) / (A_TETE - A_BRIN[0])


def profil_brin(a0, a1, guides, virole, y0):
    """Brin d'os de a0 à a1 qui s'affine, ligatures violacées aux anneaux, bague violacée double au bout (sauf le dernier)."""
    out, a = [], a0
    marques = [(ga - 0.24, ga + 0.24, 0.06) for ga, _ in guides]
    if virole:
        marques.append((a1 - 0.42, a1 + 0.0, 0.14))
    for m0, m1, d in marques:
        out.append((a, r_scion(a), m0, r_scion(m0), "os", {"clair": -0.05, "y0": y0 + a}))
        out += bague(m0, m1, r_scion(m0), r_scion(m1), r_scion((m0 + m1) / 2) + d, c=0.1)
        a = m1
    if a < a1:
        out.append((a, r_scion(a), a1, r_scion(a1), "os", {"clair": -0.05, "y0": y0 + a}))
    return out


PROFIL_BASE = ([(A_TALON - 0.05, 0.3, A_TALON + 0.1, 0.58, "os", {"clair": 0.1})]
               + bague(A_TALON + 0.1, -3.6, 0.58, 0.78, 0.92, c=0.15)
               + [(-3.6, 0.78, -1.95, 0.78, "os", {"y0": 3.0})]
               + bague(-1.95, -1.45, 0.78, 0.90, 1.0, c=0.15)
               + [(-1.45, 0.90, 2.35, 0.86, "cuir", {})]
               + bague(2.35, A_BRIN[0], 0.86, r_scion(A_BRIN[0]), 0.96))
PROFIL_TETE = bague(A_TETE, 16.05, r_scion(A_TETE), 0.34, 0.6, c=0.15)
PROFILS = [PROFIL_BASE, profil_brin(A_BRIN[0], A_BRIN[1], GUIDES[:1], True, 0.0),
           profil_brin(A_BRIN[1], A_BRIN[2], GUIDES[1:2], True, 5.0), profil_brin(A_BRIN[2], A_TETE, GUIDES[2:], False, 9.0),
           PROFIL_TETE]


def centre_anneau(a, rg):
    return W(a, -(r_scion(a) + 0.2 + rg + 0.11))


A_ANT = 15.55                                 # anneau de tête, sur le collet
R_ANT = 0.26
C_ANT = W(A_ANT, -(0.6 + 0.12 + R_ANT + 0.11))
C_MOUL = W(A_MOUL, -(0.78 + TIGE + R_PL))
P_BOB = C_MOUL + B_W * (R_BOB + 0.11)         # la ligne quitte la bobine par le haut
Y_BAS_LIGNE = 4.4                             # la ligne pendante descend jusqu'ici (image vanilla)
# épines dorsales (côté +b) : (a, longueur, rayon)
EPINES = ((A_BRIN[0] + 0.35, 1.75, 0.38), (A_BRIN[1] + 0.25, 1.45, 0.32), (A_BRIN[2] + 0.2, 1.15, 0.26))


def build(st):
    """Une copie complète de la canne dans le groupe d'étape `st` ; renvoie les groupes animés."""
    _ETAPE[0] = st
    p = st[0]
    racine = group(objet.etape(st, "canne"), W(A_PRISE))
    base = group(f"{p}_canne", W(A_PRISE), parent=racine)
    tour(base, f"{p}b", "b", W(0), A_W, B_W, PROFIL_BASE, n=8, phase=math.pi / 8)
    # clous d'os pâle sur la poignée (trois, en spirale)
    for k, (a, ang) in enumerate(((-0.6, 0.0), (0.5, 2.1), (1.6, 4.2))):
        d = math.cos(ang) * B_W + math.sin(ang) * Z_W
        tour(base, f"{p}clou{k}_", "clou", W(a) + d * 0.72, d, A_W,
             [(0.0, 0.0, 0.14, 0.2, "clou", {}), (0.14, 0.2, 0.3, 0.2, "clou", {}), (0.3, 0.2, 0.42, 0.0, "clou", {})], n=6)
    # griffe du talon (pointe verte), dans l'axe, un peu recourbée vers le bas (−b)
    griffe(base, f"{p}gt", "gt", W(A_TALON + 0.05), -A_W, -B_W, 1.05, 0.5, curve=0.18, nseg=6, n=8)
    # --- moulinet-vertèbre : pied (semelle d'os + tige), tambour à 16 pans le long de z
    cube_c(base, f"{p}semelle", W(A_MOUL, -0.78 - 0.06), (0.85, 0.12, 0.36), np.column_stack([A_W, B_W, Z_W]),
           {f: T("bloc_bague") for f in SIX})
    tour(base, f"{p}tige", "tige", W(A_MOUL, -0.78), -B_W, A_W, [(0.0, 0.3, TIGE + 0.12, 0.26, "os", {})], n=8)
    moul = group(f"{p}_moulinet", C_MOUL, parent=base)
    prof_m = ([(-Z_PL, 1.5, -0.7, R_PL, "bague", {"clair": 0.1}), (-0.7, R_PL, -Z_GAP, R_PL, "os", {}),
               (-Z_GAP, R_PL, -Z_GAP, R_BOB, "mur", {"rmin": R_BOB, "rmax": R_PL}),
               (-Z_GAP, R_BOB, Z_GAP, R_BOB, "bobine", {}),
               (Z_GAP, R_BOB, Z_GAP, R_PL, "mur", {"rmin": R_BOB, "rmax": R_PL}),
               (Z_GAP, R_PL, 0.7, R_PL, "os", {}), (0.7, R_PL, Z_PL, 1.5, "bague", {"clair": -0.1})])
    tour(moul, f"{p}m", "m", C_MOUL, Z_W, A_W, prof_m, n=16)
    med = t_disque("medaillon", 16, 1.5)
    for s, cs in ((1, "av"), (-1, "ar")):
        disque(moul, f"{p}med_{cs}", C_MOUL + Z_W * s * Z_PL, Z_W * s, B_W, 1.5, med)
        # bossette en griffe sur l'axe (pointe verte)
        griffe(moul, f"{p}bos{cs}", "bos", C_MOUL + Z_W * s * (Z_PL - 0.08), Z_W * s, A_W, 0.62, 0.36, curve=0.0, nseg=3, n=8)
        # couronne de 6 crocs sur le bord de la flasque, recourbés dans le sens du dévidage
        for j in range(6):
            th = TAU * j / 6 + (0 if s > 0 else TAU / 12)
            e = math.cos(th) * A_W + math.sin(th) * B_W
            tg = -math.sin(th) * A_W + math.cos(th) * B_W
            griffe(moul, f"{p}cr{cs}{j}_", "cr", C_MOUL + e * (R_PL - 0.12) + Z_W * s * (Z_PL - 0.22), e, tg, 0.55, 0.2,
                   curve=0.35, nseg=3, n=6, cap=0.1)
    # manivelle : bras d'os + bouton de cuir à chapeau d'os pâle
    d_m = unit(-A_W - 0.35 * B_W)
    zb = Z_PL + 0.12
    barre(moul, f"{p}bras", C_MOUL + Z_W * zb + d_m * 0.35, C_MOUL + Z_W * zb + d_m * 1.25, 0.3, "bloc_os")
    tour(moul, f"{p}bouton", "bouton", C_MOUL + d_m * 1.15 + Z_W * (zb + 0.15), Z_W, A_W,
         [(0.0, 0.28, 0.7, 0.28, "cuir", {}), (0.7, 0.28, 0.8, 0.32, "clou", {}), (0.8, 0.32, 0.9, 0.0, "clou", {})], n=8)

    # --- scion : trois brins imbriqués (pivots aux bagues), épines dorsales, anneaux, ligne dans les anneaux
    brins, epines, parent = [], [], base
    for i, a0 in enumerate(A_BRIN):
        g = group(f"{p}_brin{i + 1}", W(a0), parent=parent)
        tour(g, f"{p}s{i}", f"s{i}", W(0), A_W, B_W, PROFILS[1 + i], n=8, phase=math.pi / 8)
        a_e, L_e, r_e = EPINES[i]
        pe = W(a_e, r_scion(a_e) - 0.12)
        ge = group(f"{p}_epine{i + 1}", pe, parent=g)
        griffe(ge, f"{p}ep{i}_", f"ep{i}", pe, unit(0.82 * B_W - 0.57 * A_W), -A_W, L_e, r_e, curve=0.32, nseg=6, n=6)
        epines.append(ge)
        brins.append(g)
        parent = g
    pts_ligne = [P_BOB]
    for ga, rg in GUIDES:
        i = sum(ga >= a0 for a0 in A_BRIN) - 1
        c = centre_anneau(ga, rg)
        anneau(brins[i], f"{p}an{ga:.0f}", c, A_W, rg)
        barre(brins[i], f"{p}pied{ga:.0f}", W(ga, -r_scion(ga) + 0.1), c + B_W * (rg - 0.05), 0.22, "bloc_os", Y=A_W)
        pts_ligne.append(c)
    tete = group(f"{p}_tete", W(A_TETE), parent=brins[-1])
    tour(tete, f"{p}t", "t", W(0), A_W, B_W, PROFIL_TETE, n=8, phase=math.pi / 8)
    lum = group(f"{p}_ctrl_lumiere", W(16.3), parent=tete, name="ctrl_lumiere")
    anneau(tete, f"{p}ant", C_ANT, A_W, R_ANT, s=0.24)
    barre(tete, f"{p}piedant", W(A_ANT, -0.5), C_ANT + B_W * (R_ANT - 0.05), 0.24, "bloc_os", Y=A_W)
    pointe = group(f"{p}_pointe", W(A_POINTE), parent=tete)
    bout = griffe(pointe, f"{p}pt", "pt", W(A_POINTE), A_W, -B_W, (A_FIN - A_POINTE) / 0.88, 0.42, curve=0.1, nseg=7, n=8, cap=0.0)
    pts_ligne.append(C_ANT)
    owners = [base] + brins[:3] + [brins[-1]]
    for j in range(len(pts_ligne) - 1):
        g = owners[min(j, len(owners) - 1)]
        barre(g, f"{p}ligne{j}", pts_ligne[j], pts_ligne[j + 1], 0.14, "bloc_ligne", ov=0.05, Y=Z_W, bouts=False)
    out = {"racine": racine, "moul": moul, "brins": brins, "tete": tete, "lum": lum, "epines": epines, "pointe": pointe,
           "bout": bout}

    if st == "repos":
        # --- ligne pendante (image vanilla) et leurre : bulbe d'os fendu de gouttières vertes, pointe verte, hameçon en croc
        lg = group("r_ligne", C_ANT, parent=tete)
        bas = V(C_ANT[0], Y_BAS_LIGNE, C_ANT[2])
        barre(lg, "r_pend", C_ANT, bas, 0.16, "bloc_ligne", ov=0.05, Y=Z_W)
        le = group("r_leurre", bas, parent=lg)
        group("r_ctrl_lumiere_leurre", bas, parent=le, name="ctrl_lumiere")
        dn = V(0, -1, 0)
        tour(le, "r_bulbe", "bulbe", bas + V(0, 0.08, 0), dn, V(1, 0, 0),
             [(0.0, 0.0, 0.08, 0.16, "bague", {}), (0.08, 0.16, 0.2, 0.16, "bague", {}),
              (0.2, 0.16, 0.42, 0.5, "leurre", {"g": (0.0, 0.25)}), (0.42, 0.5, 0.95, 0.62, "leurre", {"g": (0.25, 0.6)}),
              (0.95, 0.62, 1.45, 0.34, "leurre", {"g": (0.6, 0.95)}), (1.45, 0.34, 1.6, 0.2, "bague", {})], n=8,
             phase=math.pi / 8)
        b0 = bas + V(0, -1.45, 0)
        griffe(le, "r_goutte", "goutte", b0, dn, V(1, 0, 0), 0.45, 0.22, curve=0.0, nseg=3, n=8, cap=0.0)
        h0 = bas + V(0, -1.75, 0)
        croc = [h0, h0 + V(0.0, -0.7, 0), h0 + V(0.32, -1.05, 0), h0 + V(0.72, -0.88, 0), h0 + V(0.82, -0.38, 0)]
        for j in range(4):
            barre(le, f"r_croc{j}", croc[j], croc[j + 1], 0.22, "bloc_os", ov=0.08, Y=Z_W)
        barre(le, "r_ardillon", croc[-1], croc[-1] + V(-0.26, -0.24, 0), 0.2, "bloc_vert", ov=0.05, Y=Z_W)
        out["ligne"], out["leurre"] = lg, le
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


P = np.array([c for e in elements for c in coins_de(e)])
LONGUEUR = float((P @ A_W).max() - (P @ A_W).min())


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


def echant(L, n):
    return [L * i / n for i in range(n + 1)]


sm3 = lambda u: u * u * (3 - 2 * u)
FLEX = (0.22, 0.33, 0.45)        # part de la flexion portée par chaque brin
R_, L_ = F["repos"], F["lancee"]

# item_idle (4 s, boucle)
L_IDLE = 4.0
idle = anim("item_idle", L_IDLE)
piste(idle, R_["ligne"], [kf("rotation", t, 3.0 * math.sin(TAU * t / L_IDLE + 1.2), 0, 2.2 * math.sin(TAU * t / L_IDLE))
                          for t in echant(L_IDLE, 16)])
piste(idle, R_["leurre"], [kf("rotation", t, 4.0 * math.sin(TAU * t / L_IDLE + 0.4), 360 * t / L_IDLE,
                                3.5 * math.sin(TAU * t / L_IDLE - 0.9)) for t in echant(L_IDLE, 16)])
lum_leurre = [k for k, g in groups.items() if k == "r_ctrl_lumiere_leurre"][0]
piste(idle, lum_leurre, [kf("position", t, 0.35 + 0.35 * math.sin(TAU * 2 * t / L_IDLE), 0, 0) for t in echant(L_IDLE, 8)])
for S in (R_, L_):
    piste(idle, S["lum"], [kf("position", t, 0.25 * math.sin(TAU * t / L_IDLE + (0 if S is R_ else 1.0)), 0, 0)
                           for t in echant(L_IDLE, 8)])
    for i, g in enumerate(S["epines"]):
        piste(idle, g, [kf("rotation", t, 0, 0, 3.0 * math.sin(TAU * t / L_IDLE - 0.9 * i)) for t in echant(L_IDLE, 12)])
piste(idle, L_["brins"][2], [kf("rotation", t, 0, 0, 0.5 * math.sin(TAU * 4 * t / L_IDLE) * math.sin(TAU * t / L_IDLE) ** 2)
                             for t in echant(L_IDLE, 32)])


# event_enter_lancee (0,9 s) : le scion se charge (+), fouette (−) puis oscille, amorti ; le moulinet se dévide (3 tours)
def flex_lancer(t):
    if t < 0.2:
        return 9.0 * math.sin(math.pi / 2 * t / 0.2)
    if t < 0.32:
        u = (t - 0.2) / 0.12
        return 9.0 - 23.0 * sm3(u)
    return -14.0 * math.exp(-(t - 0.32) / 0.14) * math.cos(TAU * (t - 0.32) / 0.22)


L_LAN = 0.9
lancer = anim("event_enter_lancee", L_LAN, "once")
ts = echant(L_LAN, 36)
for g, f_ in zip(L_["brins"], FLEX):
    piste(lancer, g, [kf("rotation", t, 0, 0, round(f_ * flex_lancer(t) * (1 if t < L_LAN - 1e-6 else 0), 3)) for t in ts])
piste(lancer, L_["moul"], [kf("rotation", t, 0, 0, -1080 * (1 - (1 - t / L_LAN) ** 3) if t > 0.25 else
                              -1080 * (1 - (1 - t / L_LAN) ** 3) * (t / 0.25) ** 2) for t in ts])
T_PART = 0.32
piste(lancer, L_["lum"], [kf("position", 0, 0, 0, 0), kf("position", T_PART, 0.3, 0, 0), kf("position", T_PART + 0.03, 1.4, 0, 0),
                          kf("position", L_LAN, 0.0, 0, 0)])

# event_enter_repos (0,8 s) : le moulinet ramène (2 tours), la ligne retombe en se balançant, à-coup du scion
L_REP = 0.8
ramene = anim("event_enter_repos", L_REP, "once")
ts = echant(L_REP, 32)
piste(ramene, R_["moul"], [kf("rotation", t, 0, 0, 720 * sm3(t / L_REP)) for t in ts])
piste(ramene, R_["ligne"], [kf("rotation", t, 0, 0, 0 if t >= L_REP - 1e-6 else 55 * math.exp(-t / 0.16) * math.cos(TAU * t / 0.42))
                            for t in ts])
piste(ramene, R_["leurre"], [kf("rotation", t, 0, 0, 0 if t >= L_REP - 1e-6 else
                                 -30 * math.exp(-t / 0.2) * math.sin(TAU * t / 0.36)) for t in ts])
for g, f_ in zip(R_["brins"], FLEX):
    piste(ramene, g, [kf("rotation", t, 0, 0, 0 if t >= L_REP - 1e-6 else round(f_ * 6.0 * math.exp(-t / 0.12) * math.sin(TAU * t / 0.2), 3))
                      for t in ts])

# event_select (0,6 s) : la pointe-griffe sort du collet (seul dépliage par scale), les épines se dressent en cascade,
# la ligne sursaute, le leurre s'allume
L_SEL = 0.6
sel = anim("event_select", L_SEL, "once")
piste(sel, R_["pointe"], [kf("scale", 0.0, 0.12), kf("scale", 0.05, 0.12), kf("scale", 0.2, 1.15), kf("scale", 0.3, 0.95),
                          kf("scale", 0.4, 1.02), kf("scale", L_SEL, 1.0)])
for i, g in enumerate(R_["epines"]):
    t0 = 0.12 + 0.07 * i
    keys = [kf("rotation", 0.0, 0, 0, 38)]
    for t in echant(L_SEL, 24):
        if t <= 0:
            continue
        u = max(0.0, t - t0)
        v = 38.0 if t < t0 else 38.0 * math.exp(-u / 0.06) * math.cos(TAU * u / 0.3) if t < L_SEL - 1e-6 else 0.0
        keys.append(kf("rotation", t, 0, 0, round(v, 3)))
    piste(sel, g, keys)
piste(sel, R_["ligne"], [kf("rotation", t, 0, 0, 0 if t >= L_SEL - 1e-6 else
                            round(9 * math.exp(-max(t - 0.2, 0) / 0.12) * math.sin(TAU * max(t - 0.2, 0) / 0.3), 3))
                         for t in echant(L_SEL, 24)])
piste(sel, lum_leurre, [kf("position", 0, -0.6, 0, 0), kf("position", 0.18, -0.6, 0, 0), kf("position", 0.24, 1.4, 0, 0),
                        kf("position", L_SEL, 0, 0, 0)])
piste(sel, R_["lum"], [kf("position", 0, -0.6, 0, 0), kf("position", 0.2, 1.2, 0, 0), kf("position", L_SEL, 0, 0, 0)])

# event_swing (0,4 s) : les épines se hérissent (rotation seulement), la lueur s'avive ; seul son du modèle
L_SW = 0.4
swing = anim("event_swing", L_SW, "once")
for S in (R_, L_):
    for i, g in enumerate(S["epines"]):
        piste(swing, g, [kf("rotation", t, 0, 0, round(0.0 if t >= L_SW - 1e-6 else -16 * math.sin(math.pi / 2 * t / 0.08) if t < 0.08
                                                      else -16 * math.exp(-(t - 0.08) / 0.1), 3)) for t in echant(L_SW, 16)])
    piste(swing, S["lum"], [kf("position", 0, 0, 0, 0), kf("position", 0.05, 1.1, 0, 0), kf("position", L_SW, 0, 0, 0)])

ANIMS = [idle, lancer, ramene, sel, swing]

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
# Display : préréglage _CANNE (item/handheld_rod du jar) ; gui ramené à la case (étape repos, ligne et leurre compris)
_bb = np.array([c for e in elements if ELEM_ETAPE[e["uuid"]] == "repos" for c in coins_de(e)])
_cb = (_bb.min(axis=0) + _bb.max(axis=0)) / 2
GUI = round(min(1.0, 15.6 / float(max(_bb.max(axis=0)[:2] - _bb.min(axis=0)[:2]))), 2)
GUI_T = [round(float(-(_cb[0] - 8) * GUI), 2), round(float(-(_cb[1] - 8) * GUI), 2), 0]
AFFICHAGE = objet.affichage("canne", gui={"translation": GUI_T, "scale": [GUI] * 3})
model = objet.modele(NOM, "canne", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)
from sons import limiter_sons, cle_son
limiter_sons(model)
# Un seul son : event_swing (lancer, remontée, coup), clé à 0,04 s ; rien à event_enter_* (recette 4 de categories/objets.md).
swing["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(0.04, "block.sculk.break")]}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(nd) for nd in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      len(TUILES), "tuiles ; gui", GUI)
print(f"longueur {LONGUEUR:.1f} px ; boîte {P.min(axis=0).round(2)} .. {P.max(axis=0).round(2)} ; bout {np.round(F['repos']['bout'], 2)}")
