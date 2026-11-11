"""Fouet de cuir verni : skin d'objet (guide 14) pour toutes les cannes à pêche du joueur, ensemble Cuir (thème Fétiche).
Design original, rien d'explicite. Remplace l'arme portée `fouet_cuir` (archivée le 2026-11-08 : « ce qui est en arme doit
passer en objet » ; « fouet à améliorer en animation et sons »).
Écrit skin_canne_cuir.png et .build/skin_canne_cuir_brut.bbmodel à côté de ce script ; le son `sons/claquement_cuir.ogg`
est refait par `sons/claquement_cuir.py` s'il manque.

Pourquoi la canne à pêche : c'est le seul objet de Minecraft qui « se lance » au bout d'une ligne. L'image vanilla est une
perche en diagonale dont la ligne pend du bout : le fouet au repos reprend cette silhouette (manche en diagonale, lanière qui
monte, passe en crosse et pend). Lancée (étape `lancee`), la lanière est tendue jusqu'au coin du bloc, là où le jeu fait
partir sa ligne : la ligne de pêche continue le fouet, la mèche est « partie » avec le bouchon.

D'après un vrai fouet (.claude/references/objets/fouets.md) : manche court tressé, corps (thong) tressé qui s'effile, attache
(fall hitch), mèche lisse (fall) puis claquoir effiloché (cracker). Claquement : une boucle roule du manche vers la pointe et
accélère parce que le fouet s'effile (vitesse ×10 à ×30) ; le bang part quand la boucle s'ouvre au bout (bang ≈ 1–5 ms,
1–5 kHz). Ici cette physique est écrite (une simulation à contraintes, essayée, tourbillonnait) : le manche est piloté (armé puis coup
sec) ; chaque segment suit l'angle du manche avec un retard qui croît vers la pointe de moins en moins vite (la vague
accélère) et un gain qui grandit (le bout léger dépasse) ; quand la vague arrive au bout, la mèche se retourne d'un coup puis
oscille, amortie : c'est l'instant du claquement, où tombent l'éclat et le son. Écarts amortis jusqu'à 0 à la fin.

Repère : bloc 0..16, vu depuis +Z comme l'image `fishing_rod.png` (manche en bas à gauche, bout en haut à droite). Tout est
construit droit le long de +X (repère non tourné), un groupe par segment, pivot à la jointure ; la rotation de base des groupes
(autour de Z) donne la pose de repos, les clés sont des écarts. Réglages Display : `item/handheld_rod` lu dans le jar 26.1.2
(3e personne : translation (0 ; 4 ; 2,5), tools/objet.py garde (0 ; 7 ; 1) : valeurs du jar retenues ici).

Animations (objets vivants, guide 14) :
- item_idle (6 s, boucle) : la lanière vit, vague lente du manche vers la pointe, amplitude croissante, retard croissant ;
  lancée : petite vibration de ligne tendue.
- event_swing (0,9 s) : claquement complet (armé, coup, boucle qui roule, mèche qui claque, retombée) ; un son embarqué.
- event_enter_lancee (0,8 s) : le lancer : la lanière part enroulée en arrière, se déroule et claque ; pas de son (F6 : event_swing part aussi au lancer).
- event_enter_repos (0,9 s) : ramenée, la lanière retombe de tendue à pendante, vague amortie ; pas de son.
- event_select (0,9 s) : arrive en main enroulée et se déroule ; pas de son.
Sons : un seul son, `claquement_cuir` (synthèse originale, sons/claquement_cuir.py), une seule clé, sur event_swing (F6), rien en
boucle. tools/sons.py (limiter_sons) ne connaît pas les événements d'objet : appliqué d'abord, les deux clés sont posées après.
Fonctions avancées : objet vivant (item_idle, event_swing, event_enter_<étape>, event_select), étapes repos / lancee, add_
(éclat du claquement, caché au repos dans le nœud de la mèche et grandi par `scale` à l'instant du claquement), son embarqué.
Pas de `_e` (cuir et chrome : aucune source de lumière logique), pas de particules, pas de cam_ (non annoncé pour les objets).
À juger en jeu : la ligne de pêche qui part du bout de la lanière lancée, event_swing et event_enter_* (sons d'un objet pas
encore vérifiés par le développeur), l'éclat additif.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("..", "..", "..", "tools"))
import numpy as np
from PIL import Image

NOM = "skin_canne_cuir"
TEX = 256
TAU = 2 * math.pi
SON = "claquement_cuir"


def lerp(a, b, k):
    return a + (b - a) * k


def sm(x, a=0.0, b=1.0):
    u = min(max((x - a) / (b - a), 0.0), 1.0)
    return u * u * (3 - 2 * u)


def A(c):
    return np.array(c, np.float32)


# ------------------------------------------------------------------ palette (.claude/styles/cuir.md : latex noir, chrome)
CUIR = dict(hi=A((200, 204, 214)), base=A((12, 12, 16)), low=A((4, 4, 6)))
BRIN = A((38, 38, 46))
ARGENT = dict(hi=A((240, 242, 248)), base=A((168, 172, 184)), low=A((78, 80, 92)))
NACRE = dict(hi=A((236, 238, 244)), base=A((176, 180, 192)), low=A((96, 98, 110)))   # claquoir : brins pâles, point focal


def finish(col, mask=None):
    h, w = col.shape[:2]
    mask = np.ones((h, w), bool) if mask is None else mask
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    out[..., 3] = mask * 255
    out[~mask, :3] = 0
    return out


def braid_tile(W, H, period, reflet=False):
    """Tresse noire vue de côté : chevrons de brins à peine plus clairs, creux plus noirs ; reflet (face du dessus) : bande
    blanche nette et large coupée par les creux, comme du cuir verni. u le long de la pièce, v en travers."""
    u = (np.arange(W) + 0.5)[None, :]
    v = ((np.arange(H) + 0.5) / H * 2 - 1)[:, None]
    c_ = u / period + np.abs(v) * 1.6
    f = c_ - np.floor(c_)
    strand = np.sin(np.pi * f) ** 0.6
    col = lerp(CUIR["low"], BRIN, strand[..., None]) * np.ones((H, W, 1), np.float32)
    gap = np.broadcast_to((f < 0.12) | (f > 0.9), (H, W))
    if reflet:
        core = np.broadcast_to((v > -0.42) & (v < 0.22), (H, W))
        rim = np.broadcast_to(((v > -0.62) & (v <= -0.42)) | ((v >= 0.22) & (v < 0.38)), (H, W))
        col[rim] = lerp(CUIR["hi"], BRIN, 0.45)
        col[core] = CUIR["hi"]
        col[(core | rim) & gap] = lerp(CUIR["hi"], CUIR["low"], 0.6)
    else:
        col[gap] = CUIR["low"]
    return finish(col)


def latex_tile(W=32, H=8, reflet=False):
    """Mèche lisse (fall) : latex noir ; dessus avec une bande de reflet blanche nette."""
    v = ((np.arange(H) + 0.5) / H * 2 - 1)[:, None] * np.ones((1, W))
    c = lerp(CUIR["base"], CUIR["low"], np.clip(np.abs(v), 0, 1)[..., None])
    if reflet:
        c[(v > -0.5) & (v < 0.2)] = CUIR["hi"]
        c[((v > -0.75) & (v <= -0.5)) | ((v >= 0.2) & (v < 0.4))] = lerp(CUIR["hi"], CUIR["base"], 0.5)
    return finish(c)


def metal_tile(m, W=32, H=16):
    v = ((np.arange(H) + 0.5) / H * 2 - 1)[:, None] * np.ones((1, W))
    c = lerp(m["base"], m["low"], (np.clip(np.abs(v) - 0.45, 0, 1) / 0.55)[..., None])
    c[(v > -0.62) & (v < -0.22)] = m["hi"]
    c[(v > 0.15) & (v < 0.3)] = lerp(m["base"], m["hi"], 0.35)
    return finish(c)


def cap_tile(m, n=16):
    c = m["base"] * np.ones((n, n, 3), np.float32)
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2)
    c[r > n * 0.40] = m["low"]
    c[(r < n * 0.22) & (xx < yy)] = m["hi"]
    return finish(c)


def ring_tile(n=32, r_in=0.52):
    """Anneau en O chromé vu de face : découpé par alpha, éclat net en haut à gauche, ombre en bas à droite."""
    ss = 4
    N = n * ss
    yy, xx = np.mgrid[0:N, 0:N]
    dx, dy = (xx + 0.5) / N * 2 - 1, (yy + 0.5) / N * 2 - 1
    r = np.hypot(dx, dy)
    ang = np.arctan2(dy, dx)
    m = (r < 0.98) & (r > r_in)
    mid = (r - r_in) / (0.98 - r_in)
    col = lerp(ARGENT["low"], ARGENT["base"], np.clip(1 - np.abs(mid - 0.5) * 2, 0, 1)[..., None] * 1.2)
    lit = np.cos(ang + 2.36)
    col = np.where((lit > 0.55)[..., None] & (np.abs(mid - 0.45) < 0.25)[..., None], ARGENT["hi"], col)
    col = np.where((lit < -0.6)[..., None], lerp(col, ARGENT["low"], 0.6), col)
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((n, n), Image.LANCZOS))
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((n, n), Image.LANCZOS)) > 110
    return finish(rgb.astype(np.float32), al)


def meche_tile(W=64, H=32):
    """Claquoir effiloché : racine étroite (gauche), brins nacrés qui s'écartent, bouts ronds de longueurs inégales,
    cœur plus clair, ligature noire à la racine."""
    ss = 4
    w, h = W * ss, H * ss
    yy, xx = np.mgrid[0:h, 0:w]
    u = (xx + 0.5) / w
    v = (yy + 0.5) / h * 2 - 1
    hw = lerp(0.20, 0.32, np.clip(u / 0.4, 0, 1))
    body = (u < 0.45) & (np.abs(v) < hw)
    m = body.copy()
    shade = np.where(body, 1 - np.abs(v) / np.maximum(hw, 1e-3), 0.0)
    sx = W / (H / 2)
    for vy, ul in ((-0.66, 0.92), (-0.33, 0.99), (0.0, 0.89), (0.33, 0.97), (0.66, 0.87)):
        x0, y0, x1, y1 = 0.38, vy * 0.35, ul - 0.06, vy
        px, py = (u - x0) * sx, v - y0
        dx, dy = (x1 - x0) * sx, y1 - y0
        tt = np.clip((px * dx + py * dy) / (dx * dx + dy * dy), 0, 1)
        d = np.hypot(px - tt * dx, py - tt * dy)
        r_ = 0.15 * (1 - 0.3 * tt)
        mk = d < r_
        m |= mk
        shade = np.where(mk, np.maximum(shade, 1 - d / r_), shade)
    col = lerp(NACRE["low"], NACRE["base"], np.clip(shade * 1.5, 0, 1)[..., None])
    col[shade > 0.6] = NACRE["hi"]
    col[(u > 0.04) & (u < 0.12) & body] = CUIR["base"]
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110
    return finish(rgb.astype(np.float32), al)


def eclat_tile(n=32):
    """Éclat du claquement (add_ : noir = invisible) : étoile à 4 branches fines et 4 courtes, cœur blanc, halo très sombre."""
    yy, xx = np.mgrid[0:n, 0:n]
    dx, dy = (xx + 0.5) / n * 2 - 1, (yy + 0.5) / n * 2 - 1
    r = np.hypot(dx, dy) + 1e-6
    ang = np.arctan2(dy, dx)
    long_ = np.exp(-(np.abs(np.sin(2 * ang)) * r * 9) ** 2) * np.clip(1 - r, 0, 1) ** 1.2
    court = np.exp(-(np.abs(np.cos(2 * ang)) * r * 12) ** 2) * np.clip(1 - r * 1.8, 0, 1)
    I = np.clip(long_ + 0.6 * court + 0.9 * np.exp(-(r / 0.16) ** 2) + 0.12 * np.clip(1 - r, 0, 1) ** 3, 0, 1)
    col = np.stack([I * 235, I * 240, I * 255], -1)
    return finish(col)


TILES = {
    "tresse_manche": braid_tile(96, 24, 9.0), "tresse_manche_reflet": braid_tile(96, 24, 9.0, True),
    "tresse": braid_tile(48, 16, 8.0), "tresse_reflet": braid_tile(48, 16, 8.0, True),
    "latex": latex_tile(), "latex_reflet": latex_tile(reflet=True),
    "argent": metal_tile(ARGENT), "cap_argent": cap_tile(ARGENT), "cap_cuir": cap_tile(CUIR),
    "anneau": ring_tile(), "meche": meche_tile(), "meche_ame": finish(lerp(NACRE["low"], NACRE["base"], 0.4) * np.ones((8, 16, 3), np.float32)),
    "eclat": eclat_tile(),
}


def pack():
    items = sorted(((n, t.shape[1], t.shape[0]) for n, t in TILES.items()), key=lambda it: -it[2])
    uv, x, y, shelf = {}, 0, 0, 0
    for n, w, h in items:
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, f"atlas plein : {n}"
        uv[n] = (x, y, x + w, y + h)
        x += w + 1
        shelf = max(shelf, h)
    return uv


UV = pack()
tex = np.zeros((TEX, TEX, 4), np.uint8)
for n, im in TILES.items():
    u0, v0, u1, v1 = UV[n]
    tex[v0:v1, u0:u1] = im
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[tex[..., 3] == 0] = 0
assert set(np.unique(tex[..., 3])) <= {0, 255}
im = Image.fromarray(tex, "RGBA")
im.save(f"{NOM}.png", optimize=True)
_b = io.BytesIO()
im.save(_b, "PNG", optimize=True)
tex_b64 = "data:image/png;base64," + base64.b64encode(_b.getvalue()).decode()

# ------------------------------------------------------------------ géométrie (repère droit le long de +X)
elements, groups = [], {}
Z0 = 8.0
G = np.array((4.2, 4.2))            # prise (dans le poing), sur la diagonale du bloc
A_G = 3.4                           # abscisse de la prise le long du manche (0 = bout du pommeau)
L_H = 8.6                           # longueur du manche, pommeau compris
ANG_H = 45.0                        # manche en diagonale, comme la canne vanilla


def nuid():
    return str(_uuid.uuid4())


def PT(a):
    """Point de l'axe droit (repère non tourné) à l'abscisse a : la prise G est le pivot du manche."""
    return np.array((G[0] + a - A_G, G[1], Z0))


def group(name, origin, parent=None, rz=0.0):
    assert name not in groups, name
    groups[name] = {"origin": [round(float(v), 4) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [0.0, 0.0, round(float(rz), 4)]}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm],
         "to": [round(float(v), 3) for v in to], "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def full(t):
    return list(UV[t])


def along(tile, cap, up=None, bouts=True):
    t = full(tile)
    c = full(cap) if (cap and bouts) else CLEAR
    return {"north": t, "south": t, "up": full(up) if up else t, "down": t, "east": c, "west": c}


def octo(g, name, a0, a1, r, tile, cap, off=0.0, up=None, bouts=True):
    """Section octogonale : deux cubes le long de X, le second tourné de 45° et raccourci de 0,1 px à chaque bout."""
    o = PT(a0)
    f = along(tile, cap, up, bouts)
    cube(g, name, PT(a0) + (0, -r, -r), PT(a1) + (0, r, r), o, (off, 0, 0), f)
    r2 = r * 0.97
    cube(g, name + "o", PT(a0 + 0.1) + (0, -r2, -r2), PT(a1 - 0.1) + (0, r2, r2), o, (off + 45, 0, 0), f)


def plaque(g, name, c, demi, normale, tile):
    """Plaque fine découpée par alpha (anneau) : 0,3 px d'épaisseur, tranches transparentes."""
    c = np.asarray(c, float)
    d = np.array(demi, float)
    f = {k: CLEAR for k in ("north", "south", "east", "west", "up", "down")}
    t = full(tile)
    if normale == "z":
        f["south"] = t
        f["north"] = [t[2], t[1], t[0], t[3]]
    cube(g, name, c - d, c + d, c, (0, 0, 0), f)


def manche(P, parent):
    """Manche tressé : pommeau chrome, anneau en O au bout (dans le plan du bloc, lisible dans la case), viroles chrome."""
    h = group(P + "manche", (*G, Z0), parent, ANG_H)
    octo(h, P + "prise", 1.25, L_H - 0.75, 0.74, "tresse_manche", "cap_cuir", up="tresse_manche_reflet")
    octo(h, P + "pommeau", 0.2, 1.4, 0.9, "argent", "cap_argent", off=22.5)
    octo(h, P + "pommeau_bout", -0.25, 0.35, 0.56, "argent", "cap_argent")
    octo(h, P + "virole_pom", 1.4, 1.75, 0.84, "argent", "cap_argent", off=11.25)
    octo(h, P + "virole", L_H - 0.9, L_H + 0.05, 0.86, "argent", "cap_argent", off=33.75)
    plaque(h, P + "anneau", PT(-0.95), (0.95, 0.95, 0.15), "z", "anneau")
    return h


# Lanière : corps tressé qui s'effile (14 segments), mèche lisse (3), claquoir (1). Repos : 24 px, crosse et pendant.
NT = 14
SEG = [(lerp(1.55, 1.05, j / (NT - 1)), lerp(0.62, 0.34, j / (NT - 1)), "tresse") for j in range(NT)] \
    + [(1.1, 0.24, "latex"), (1.1, 0.23, "latex"), (1.1, 0.22, "latex"), (2.6, 0.0, "meche")]
# Lancée : corps tendu jusqu'au coin du bloc (là où le jeu fait partir sa ligne), attache chromée au bout, pas de mèche.
NT_L = 7
SEG_L = [(lerp(1.42, 1.22, j / (NT_L - 1)), lerp(0.62, 0.44, j / (NT_L - 1)), "tresse") for j in range(NT_L)] + [(0.7, 0.0, "attache")]


def chaine(P, segs, parent):
    """Groupes imbriqués (un par segment, pivot à la jointure, repère droit) ; renvoie les noms et les abscisses."""
    noms, a, g = [], L_H, parent
    for j, (l, r, kind) in enumerate(segs):
        g = group(f"{P}s{j:02d}", PT(a), g)
        o = PT(a)
        off = 22.5 if j % 2 == 0 else 0.0
        if kind == "tresse" or kind == "latex":
            t, up = (("tresse", "tresse_reflet") if kind == "tresse" else ("latex", "latex_reflet"))
            f = along(t, None, up, bouts=False)
            cube(g, f"{P}c{j:02d}", o + (-0.12, -r, -r), o + (l + 0.12, r, r), o, (off, 0, 0), f)
            r2 = r * 0.97
            cube(g, f"{P}c{j:02d}o", o + (-0.04, -r2, -r2), o + (l + 0.04, r2, r2), o, (off + 45, 0, 0), f)
            if kind == "latex" and segs[j - 1][2] == "tresse":            # attache de la mèche (fall hitch) : nœud tressé
                octo(g, f"{P}noeud", a - 0.05, a + 0.55, 0.47, "tresse", "cap_cuir", off=11.25, up="tresse_reflet")
        elif kind == "meche":
            plq = full("meche")
            cube(g, f"{P}meche_v", o + (-0.2, -0.7, -0.15), o + (l - 0.2, 0.7, 0.15), o, (22.5, 0, 0),
                 {"south": plq, "north": [plq[2], plq[1], plq[0], plq[3]], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
            cube(g, f"{P}meche_h", o + (-0.16, -0.15, -0.7), o + (l - 0.16, 0.15, 0.7), o, (22.5, 0, 0),
                 {"up": plq, "down": plq, "east": CLEAR, "west": CLEAR, "north": CLEAR, "south": CLEAR})
            cube(g, f"{P}meche_ame", o + (-0.1, -0.17, -0.17), o + (1.0, 0.17, 0.17), o, (67.5, 0, 0), along("meche_ame", "meche_ame"))
            # nœud de ligature noir à la racine du claquoir ; l'éclat y est caché au repos
            cube(g, f"{P}lig", o + (-0.5, -0.36, -0.36), o + (0.36, 0.36, 0.36), o, (11.25, 0, 0), along("latex", "cap_cuir", "latex_reflet"))
            cube(g, f"{P}ligo", o + (-0.4, -0.35, -0.35), o + (0.26, 0.35, 0.35), o, (56.25, 0, 0), along("latex", "cap_cuir", "latex_reflet"))
            eclat(P, g, o)
        elif kind == "attache":
            octo(g, f"{P}attache", a - 0.1, a + 0.45, 0.58, "argent", "cap_argent", off=11.25)
            plaque(g, f"{P}anneau_bout", PT(a + 1.05), (0.62, 0.62, 0.15), "z", "anneau")
            eclat(P, g, PT(a + 0.18))
        noms.append(g)
        a += l
    return noms


ECLATS = {}


def eclat(P, parent, o):
    """Éclat du claquement : deux plaques additives croisées de 0,3 px, cachées au repos dans le nœud ; event_* les grandit
    (×14 : 4,2 px) autour d'un pivot placé dans le nœud, centre de l'éclat décalé vers la pointe."""
    t = full("eclat")
    gv = group(f"add_eclat_{P}v", o, parent)
    c = o + (0.15, 0, 0)
    cube(gv, f"{P}eclat_v", c - (0.15, 0.15, 0.15), c + (0.15, 0.15, 0.15), o, (0, 0, 0),
         {"south": t, "north": [t[2], t[1], t[0], t[3]], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
    gh = group(f"add_eclat_{P}h", o, parent)
    cube(gh, f"{P}eclat_h", c - (0.14, 0.14, 0.14), c + (0.14, 0.14, 0.14), o, (0, 0, 0),
         {"up": t, "down": t, "east": CLEAR, "west": CLEAR, "north": CLEAR, "south": CLEAR})
    ECLATS[P] = (gv, gh)


import objet  # noqa: E402

REPOS = group(objet.etape("repos", "canne"), (*G, Z0))
LANCEE = group(objet.etape("lancee", "canne"), (*G, Z0))
H_R = manche("r_", REPOS)
H_L = manche("l_", LANCEE)
CH_R = chaine("r_", SEG, H_R)
CH_L = chaine("l_", SEG_L, H_L)
LEN_R = [s[0] for s in SEG]
LEN_L = [s[0] for s in SEG_L]


# ------------------------------------------------------------------ poses de repos (directions absolues dans le plan du bloc)
def repos_r():
    s, out = 0.0, []
    for l in LEN_R:
        out.append(58 - 158 * sm((s + l / 2 - 6.0) / 6.5))           # monte à 58°, passe en crosse, pend (−100°)
        s += l
    return np.array(out)


def repos_l():
    s, out = 0.0, []
    for l in LEN_L:
        out.append(48 - 4 * (s / sum(LEN_L)))                        # tendue, très légère flèche
        s += l
    return np.array(out)


TH_R, TH_L = repos_r(), repos_l()


def poser(noms, th):
    prev = ANG_H
    for g, t in zip(noms, th):
        groups[g]["rotation"][2] = round(float(t - prev), 4)
        prev = t


poser(CH_R, TH_R)
poser(CH_L, TH_L)


def points(th, lens, alpha=ANG_H):
    d = np.radians(alpha)
    p = G + (L_H - A_G) * np.array((math.cos(d), math.sin(d)))
    pts = [p]
    for t, l in zip(th, lens):
        p = p + l * np.array((math.cos(math.radians(t)), math.sin(math.radians(t))))
        pts.append(p)
    return np.array(pts)


# ------------------------------------------------------------------ cinématique de la lanière (plan du bloc)
# Une vraie simulation (essayée : chaîne à contraintes) tourbillonne et ne se règle pas ; ici la physique est écrite :
# chaque segment suit l'angle du manche avec un retard tau_j qui croît vers la pointe, mais de moins en moins vite (la
# vague accélère parce que le fouet s'effile), et un gain qui grandit vers la pointe (le bout léger dépasse) ; au bout,
# la mèche se retourne d'un coup (claquement) puis oscille, amortie.
def retard(u, total):
    return total * (1 - (1 - u) ** 2)


def deroule(x):
    """0 -> 1 avec un léger dépassement amorti (cuir souple mais tendu)."""
    if x <= 0:
        return 0.0
    return 1 - math.exp(-5 * x) * math.cos(6.5 * x)


def retourne(dt, w=0.03, tau=0.05, per=0.11):
    """Retournement de la mèche à dt = 0 : montée en w, puis oscillation amortie."""
    if dt < -w:
        return 0.0
    if dt < 0:
        return sm(dt, -w, 0)
    return math.exp(-dt / tau) * math.cos(TAU * dt / per)


def cinematique(th0, alpha_f, dev_f, L, fps=120):
    """(ts, angle du manche, angles absolus) : rel_j(t) = rel_j au repos + dev_f(t)[j]."""
    rel0 = np.diff(np.concatenate([[ANG_H], th0]))
    ts = np.arange(int(round(L * fps)) + 1) / fps
    als = np.array([alpha_f(t) for t in ts])
    ths = np.array([a + np.cumsum(rel0 + dev_f(t)) for t, a in zip(ts, als)])
    return ts, als, ths


def onde_coup(n, alpha_f, total, gain, tc, flip, boucle=(0.0, 0.2)):
    """Écarts relatifs d'une lanière de n segments qui suit le manche avec retard (vague) et se retourne au bout à tc.
    boucle = (courbure en degrés par jointure, départ) : une boucle serrée roule du manche (départ) au bout (tc), de plus en
    plus vite et de plus en plus courte."""
    us = np.linspace(0, 1, n)
    tb = boucle[1] + (tc - boucle[1]) * (1 - (1 - us) ** 2)
    wb = 0.05 * (1 - 0.6 * us)
    taus = retard(us, total)
    gains = lerp(1.0, gain, us ** 1.2)
    def dev(t):
        absd = np.array([(alpha_f(t - tau) - ANG_H) * g for tau, g in zip(taus, gains)])   # écart absolu du segment
        rel = np.diff(np.concatenate([[alpha_f(t) - ANG_H], absd]))
        for k, f in enumerate(flip):                                                      # les derniers segments
            rel[n - len(flip) + k] += f * retourne(t - tc)
        rel += boucle[0] * np.exp(-((t - tb) / wb) ** 2) * np.minimum(1, us * 4 + 0.3)
        return rel
    return dev

def coup(t, arme=0.13, frappe=0.24, retour=0.6, amp_a=24.0, amp_f=-20.0):
    """Angle du manche : armé (vers l'arrière), coup sec vers l'avant, arrêt, retour."""
    if t <= 0:
        return ANG_H
    if t < arme:
        return ANG_H + amp_a * sm(t / arme)
    if t < frappe:
        return ANG_H + lerp(amp_a, amp_f, sm((t - arme) / (frappe - arme)))
    return ANG_H + amp_f * (1 - sm((t - frappe) / (retour - frappe)))


def instant_claquement(ts, als, ths, lens, t_min=0.12):
    """Instant de la vitesse maximale de la pointe après le coup du manche (t >= t_min)."""
    vit = []
    pts = [points(th, lens, a) for th, a in zip(ths, als)]
    for i in range(1, len(ts)):
        vit.append(np.linalg.norm(pts[i][-1] - pts[i - 1][-1]) / (ts[i] - ts[i - 1]))
    vit = [v if ts[i + 1] >= t_min else 0.0 for i, v in enumerate(vit)]
    i = int(np.argmax(vit)) + 1
    return ts[i], max(vit)


# ------------------------------------------------------------------ animations
def kf(t, v, ch="rotation", interp="linear"):
    return {"channel": ch, "data_points": [{"x": str(round(float(v[0]) + 0.0, 3)), "y": str(round(float(v[1]) + 0.0, 3)),
                                            "z": str(round(float(v[2]) + 0.0, 3))}], "time": round(float(t), 4), "interpolation": interp}


def anim(name, L, loop="once"):
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": round(L, 4), "snapping": 60,
            "selected": name == "item_idle", "animators": {}}


def piste(an, g, keys):
    an["animators"].setdefault(groups[g]["uuid"], {"name": g, "type": "bone", "keyframes": []})["keyframes"] += keys


def depuis_sim(an, h, noms, th0, sim, L, fps=60, hors_plan=0.0):
    """Écarts de rotation (manche puis segments relatifs) à la pose de repos, amortis jusqu'à 0 sur la fin.
    hors_plan : petite rotation Y proportionnelle à la courbure (la boucle n'est jamais tout à fait plane)."""
    ts, als, ths = sim
    rel0 = np.diff(np.concatenate([[ANG_H], th0]))
    step = max(1, int(round(len(ts) / (L * fps))))
    idx = list(range(0, len(ts), step))
    if idx[-1] != len(ts) - 1:
        idx.append(len(ts) - 1)
    keys = {g: [] for g in [h] + noms}
    for i in idx:
        t = ts[i]
        fade = 1 - sm(t, L - 0.28, L - 0.02)
        keys[h].append(kf(t, (0, 0, (als[i] - ANG_H) * fade)))
        rel = np.diff(np.concatenate([[als[i]], ths[i]]))
        for j, g in enumerate(noms):
            d = ((rel[j] - rel0[j] + 180) % 360 - 180) * fade
            keys[g].append(kf(t, (0, hors_plan * d * (j / len(noms)), d)))
    for g, k in keys.items():
        piste(an, g, k)


def flash(an, P, tc):
    """Éclat : ×1 → ×14 en 0,02 s à l'instant du claquement, éteint en 0,04 s (les échelles se multiplient avec item_idle)."""
    gv, gh = ECLATS[P]
    for g, ax in ((gv, (1, 1, 0)), (gh, (1, 0, 1))):
        def sc(s):
            return tuple(s if a else 1 for a in ax)
        piste(an, g, [kf(0, (1, 1, 1), "scale"), kf(tc - 0.025, (1, 1, 1), "scale"), kf(tc, sc(14), "scale"),
                      kf(tc + 0.018, sc(10), "scale"), kf(tc + 0.04, (1, 1, 1), "scale")])


ANIMS = []

# item_idle : vague lente qui descend la lanière (retard et amplitude croissants vers la pointe) ; lancée : vibration tendue
LI = 6.0
idle = anim("item_idle", LI, "loop")
ki, n_r = [], len(CH_R)
for g in [H_R] + CH_R + [H_L] + CH_L:
    piste(idle, g, [])
for i in range(int(LI * 10)):
    t = i / 10
    w = TAU * t / LI
    piste(idle, H_R, [kf(t, (0, 0, 1.6 * math.sin(2 * w) + 0.6 * math.sin(3 * w + 1)))])
    for j, g in enumerate(CH_R):
        u = j / (n_r - 1)
        amp = 0.8 + 4.0 * u ** 1.3
        ph = 2.4 * u
        piste(idle, g, [kf(t, (1.4 * u * math.sin(w + 2 * u), 0, amp * math.sin(2 * w - ph) + 0.5 * amp * math.sin(3 * w - 1.5 * ph + 1)))])
    piste(idle, H_L, [kf(t, (0, 0, 0.5 * math.sin(2 * w)))])
    for j, g in enumerate(CH_L):
        u = j / (len(CH_L) - 1)
        piste(idle, g, [kf(t, (0, 0, 0.5 * u * math.sin(8 * w - 3 * u)))])
for b in idle["animators"].values():                 # boucle : dernière clé = première (interpolation linéaire)
    k0 = dict(b["keyframes"][0], time=LI)
    b["keyframes"].append(k0)
ANIMS.append(idle)

# event_swing : claquement complet de la lanière au repos
LS = 0.95
T_TRAJET = 0.2
coup_s = coup
tc_s = 0.24 + 0.85 * T_TRAJET                      # la vague du coup sec (0,13–0,24 s) arrive au bout
sim_s = cinematique(TH_R, coup_s, onde_coup(len(CH_R), coup_s, T_TRAJET, 2.6, tc_s, (20, 36, 55, 85), boucle=(-34.0, 0.2)), LS)
swing = anim("event_swing", LS)
depuis_sim(swing, H_R, CH_R, TH_R, sim_s, LS, hors_plan=0.25)
flash(swing, "r_", tc_s)
ANIMS.append(swing)

# event_enter_lancee : la lanière tendue part enroulée (vers le bas, jamais dans la tête), se déroule du manche à la pointe et claque au bout
LL = 0.8
n_l = len(CH_L)
taus_l = retard(np.linspace(0, 1, n_l), 0.2) + 0.04
tc_l = float(taus_l[-1] + 0.1)
lancer_a = lambda t: coup(t, 0.06, 0.16, 0.45, 10.0, -14.0)
def dev_lancer(t):
    d = np.array([-28.0 * (1 - deroule((t - tau) / 0.16)) for tau in taus_l])     # enroulée vers le bas : loin de la tête
    d[-2:] += np.array((20.0, 45.0)) * retourne(t - tc_l, per=0.09)
    return d
sim_l = cinematique(TH_L, lancer_a, dev_lancer, LL)
lancer = anim("event_enter_lancee", LL)
depuis_sim(lancer, H_L, CH_L, TH_L, sim_l, LL, hors_plan=0.2)
flash(lancer, "l_", tc_l)
ANIMS.append(lancer)

# event_enter_repos : ramenée, la lanière passe de tendue (droite dans l'axe du manche) à pendante, de la racine au bout
LR = 0.9
rel_r0 = np.diff(np.concatenate([[ANG_H], TH_R]))
taus_r = retard(np.linspace(0, 1, len(CH_R)), 0.3)
ramene_a = lambda t: ANG_H - 8 * math.sin(math.pi * sm(t, 0, 0.45))
sim_r = cinematique(TH_R, ramene_a, lambda t: np.array([-r * (1 - deroule((t - tau) / 0.3)) for r, tau in zip(rel_r0, taus_r)]), LR)
ramene = anim("event_enter_repos", LR)
depuis_sim(ramene, H_R, CH_R, TH_R, sim_r, LR, hors_plan=0.15)
ANIMS.append(ramene)

# event_select : arrive en main enroulée sur elle-même (spirale vers le bas), se déroule depuis le manche
LSel = 0.9
taus_s = retard(np.linspace(0, 1, len(CH_R)), 0.35)
select_a = lambda t: ANG_H + 10 * math.sin(math.pi * sm(t, 0, 0.4))
sim_sel = cinematique(TH_R, select_a, lambda t: np.array([-24.0 * (1 - deroule((t - tau) / 0.22)) for tau in taus_s]), LSel)
select = anim("event_select", LSel)
depuis_sim(select, H_R, CH_R, TH_R, sim_sel, LSel, hors_plan=0.2)
ANIMS.append(select)

_, v_s = instant_claquement(*sim_s, LEN_R)
_, v_l = instant_claquement(*sim_l, LEN_L)

# ------------------------------------------------------------------ modèle
def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node(REPOS), bone_node(LANCEE)]
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
AFFICHAGE = objet.affichage(
    "canne",
    thirdperson_righthand={"translation": [0, 4.0, 2.5]},     # item/handheld_rod du jar 26.1.2
    thirdperson_lefthand={"translation": [0, 4.0, 2.5]},
)
model = objet.modele(NOM, "canne", elements, outliner, textures, (TEX, TEX), affichage=AFFICHAGE, animations=ANIMS)

from sons import limiter_sons, embarquer_sons, cle_son  # noqa: E402
limiter_sons(model)                       # ne garde rien ici (aucun son en boucle) ; les deux gestes ont leur clé ci-dessous
embarquer_sons(model, {SON: f"sons/{SON}.ogg"})
AVANCE = 0.13                             # le bang est à 0,13 s dans le fichier (sifflement de la lanière avant)
# Correctif F6 (recette 4) : un seul claquement, sur event_swing (qui part aussi au lancer et à la remontée) ; plus rien à
# event_enter_lancee, rejoué à chaque bascule repos/lancee (son répété en jeu, deux claquements par lancer).
swing["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [cle_son(round(max(0.04, tc_s - AVANCE), 3), SON)]}

os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))
np.savez(".build/sims.npz", **{f"{k}_{n}": v for k, sim in (("swing", sim_s), ("lancer", sim_l), ("ramene", sim_r), ("select", sim_sel)) for n, v in zip(("t", "a", "th"), sim)}, lens_r=LEN_R, lens_l=LEN_L, th_r=TH_R, th_l=TH_L)
json.dump({"tc_swing": tc_s, "tc_lancer": tc_l, "v_swing": v_s, "v_lancer": v_l}, open(".build/claquements.json", "w"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


P_ = np.array([p for e in elements for p in (e["from"], e["to"])])
print(f"claquement : coup {tc_s:.3f} s (pointe {v_s:.0f} px/s), lancer {tc_l:.3f} s ({v_l:.0f} px/s)")
print("repos, bout de la mèche :", np.round(points(TH_R, LEN_R)[-1], 2), "; lancée, bout :", np.round(points(TH_L, LEN_L)[-1], 2))
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
