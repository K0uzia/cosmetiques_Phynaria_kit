"""Fouet de cuir : fouet de dompteur tenu dans la main droite, ensemble Cuir (thème Fétiche). Design original, rien d'explicite.
Écrit fouet_cuir.png, fouet_cuir_e.png (noir, par ajouter_ambiance) et .build/fouet_cuir_brut.bbmodel à côté de ce script.

Révision du 2026-11-04 (.claude/styles/cuir.md : « trop gothique ») : latex / cuir noir brillant, plus de rouge.
Manche tressé noir profond (12, 12, 16), section octogonale (deux cubes, le second tourné de 45°) ; la face du dessus de chaque
cube porte une bande de reflet blanc net et large ((200, 204, 214) au cœur), coupée par les creux de la tresse. Rivets ronds plats
de chrome aux deux bouts de la prise et sur le pommeau, pommeau chrome avec un anneau en D d'où pend une dragonne courte (sangle
noire à reflet, couture noire à peine plus claire). Bague chrome à la jonction manche-lanière. Lanière : chaîne de 14 segments
imbriqués (un groupe par segment, pivot au bout du précédent), section 1,0 → 0,4 px, 24,7 px, même tresse noire à reflet.
Mèche (claquoir) noire brillante effilochée, reflet blanc au cœur de chaque brin, ligature chrome : deux plaques croisées
découpées par alpha (brins à bouts ronds) autour d'une âme pleine en losange.

Repère : tout est construit droit le long de +X (repère du groupe `fouet`, pivot P0 sous le poing). La forme de chaque état est
décrite par la direction monde de chaque segment (angle de pente phi, cap h : 0 vers l'avant, + vers l'extérieur), transportée
de segment en segment sans torsion, puis convertie en rotations relatives. Rotation de base des groupes = pose de repos (idle à t=0),
les clés = écart à cette base. La profondeur de pendaison de chaque état est réglée par dichotomie pour que la lanière ne touche pas
le sol, bras du joueur pris à toutes les phases du balancement (le jeu ne cale pas le pas sur l'animation).
La lanière part vers l'extérieur (+X) : elle reste à x > 5 sous la hanche, loin de la jambe droite (x de 0 à 4).

Attaque (once, 0,8 s, par-dessus l'état, en écarts) : la lanière part en arrière, une boucle roule de la racine à la mèche, la mèche
claque à 0,42 s (secousse rapide), puis tout retombe ; retour exact à 0. Le bras est animé par le jeu (coup vanilla, 0,3 s).
Son : un seul, `entity.player.attack.crit` au claquement (limiter_sons, attaque=True).
Remise aux règles du 2026-11-05 (.claude/references/procedures/remise-aux-regles.md, effets/impacts-attaques.md) :
- Traînée façon anime au coup : croissant en drapeau sur le vrai trajet de la mèche (0,25 à 0,42 s), tête épaisse et claire,
  queue fine, en trois sections qui s'éteignent de la queue vers la tête (0,06 / 0,13 / 0,22 s après le claquement) ; étoile
  d'impact de 4 px face caméra au bout de la mèche (0,1 s). Blanc argenté, add_ doublé en trans_ (visible avec shader).
  Cachées hors attaque par ctrl_alpha -1 dans chaque état ; l'attaque ajoute +1 (positions additionnées, supposé pour attack).
- event_equip : le fouet arrive enroulé et se déroule (1,1 s), un son de cuir.
- Faces à moins de 0,1 px corrigées (rivets contre les bouts du manche et du pommeau, bout du pommeau, âme de la mèche).
Fonctions avancées : add_, trans_, cam_, ctrl_alpha, event_equip, son ; ambiance (tools/ambiance.py : ctrl_teinte, ctrl_lumiere,
overlay_ambiance ; calque `_e` noir). Pas de `emit_mc_`, pas de particules, pas de `_r`. À juger en jeu : la traînée (ctrl_alpha
additionné entre l'état et l'attaque), sa lecture vue de côté et de dos, l'étoile avec et sans shader.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

AVEC_E = False      # révision latex : plus de lueur rouge ; ajouter_ambiance ne garde qu'un calque _e noir
NOM = "fouet_cuir"
TEX = 512
TAU = 2 * math.pi

P0 = np.array((6.3, 11.3, -0.6))     # prise sous le poing (bras x 4..8, bas du bras y = 12)
A_GRIP = -4.6                        # abscisse de la prise le long du manche (a = 0 : jonction manche-lanière)
N = 14                               # segments de lanière
SEG_L = [2.3 + (1.5 - 2.3) * j / (N - 1) for j in range(N)]
SEG_R = [0.5 + (0.2 - 0.5) * j / (N - 1) for j in range(N)]
MECHE_L, MECHE_W = 3.2, 1.3
JOINTS = [0.0]
for L_ in SEG_L:
    JOINTS.append(JOINTS[-1] + L_)
L_LASH = JOINTS[-1]


def lerp(a, b, k):
    return a + (b - a) * k


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def A(c):
    return np.array(c, np.float32)


# ------------------------------------------------------------------ palette (.claude/styles/cuir.md)
CUIR = dict(hi=A((200, 204, 214)), base=A((12, 12, 16)), low=A((4, 4, 6)))     # latex / cuir noir brillant (révision du 2026-11-04)
BRIN = A((34, 34, 40))            # relief d'un brin de tresse, couture : noir à peine plus clair
ARGENT = dict(hi=A((236, 238, 244)), base=A((168, 172, 184)), low=A((78, 80, 92)))
ROUGE = dict(hi=A((214, 52, 64)), base=A((150, 22, 36)), low=A((82, 10, 20)))


def finish(col, mask=None):
    h, w = col.shape[:2]
    mask = np.ones((h, w), bool) if mask is None else mask
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    out[..., 3] = mask * 255
    out[~mask, :3] = 0
    return out


def braid_tile(W, H, period, seed, reflet=False):
    """Tresse noire brillante vue de côté : chevrons (brins) à peine plus clairs que le fond, creux plus noirs.
    reflet : face du dessus, avec la bande de lumière blanche nette et large qui fait la matière (latex), coupée par les creux
    de la tresse. u le long de la pièce (largeur de l'image), v en travers."""
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


def cap_tile(m, n=16, ring=True):
    c = m["base"] * np.ones((n, n, 3), np.float32)
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2)
    if ring:
        c[r > n * 0.40] = m["low"]
    c[(r < n * 0.22) & (xx < yy)] = m["hi"]
    return finish(c)


def silver_tile(W=32, H=16):
    """Argent chromé : bande claire nette au tiers haut, base, ombre aux bords."""
    v = ((np.arange(H) + 0.5) / H * 2 - 1)[:, None] * np.ones((1, W))
    c = lerp(ARGENT["base"], ARGENT["low"], (np.clip(np.abs(v) - 0.45, 0, 1) / 0.55)[..., None])
    band = (v > -0.62) & (v < -0.22)
    c[band] = ARGENT["hi"]
    c[(v > 0.15) & (v < 0.3)] = lerp(ARGENT["base"], ARGENT["hi"], 0.35)
    return finish(c)


def strap_tile(W=48, H=14):
    """Sangle de latex noir : reflet blanc net en haut, coutures noires à peine plus claires de chaque côté, en tirets."""
    c = CUIR["base"] * np.ones((H, W, 3), np.float32)
    c[2:5] = CUIR["hi"]
    c[1] = c[5] = lerp(CUIR["hi"], CUIR["base"], 0.5)
    c[-2:] = CUIR["low"]
    c[0] = CUIR["low"]
    for y0 in (7, H - 4):
        for x0 in range(2, W, 6):
            c[y0:y0 + 2, x0:x0 + 4] = BRIN
    return finish(c)


def edge_tile(W=48, H=4):
    c = CUIR["low"] * np.ones((H, W, 3), np.float32)
    c[:1] = CUIR["base"]
    return finish(c)


def meche_tiles(W=64, H=32):
    """Claquoir effiloché : racine étroite (gauche), brins qui s'écartent en éventail, bouts ronds de longueurs inégales.
    Rouge sang, plus sombre à la racine. Calque _e très léger sur les brins."""
    ss = 4
    w, h = W * ss, H * ss
    yy, xx = np.mgrid[0:h, 0:w]
    u = (xx + 0.5) / w
    v = (yy + 0.5) / h * 2 - 1
    m = np.zeros((h, w), bool)
    # tronc : demi-largeur 0.16 à la racine → 0.30 à u = 0.45
    hw = lerp(0.17, 0.30, np.clip(u / 0.45, 0, 1))
    m |= (u < 0.5) & (np.abs(v) < hw)
    # brins : capsules du point de séparation à leur bout rond
    strands = ((-0.62, 0.93), (-0.30, 0.99), (0.02, 0.90), (0.33, 0.97), (0.64, 0.88))
    sep = (0.42, 0.0)
    rad = 0.085
    shade = np.zeros((h, w), np.float32)
    for k, (vy, ul) in enumerate(strands):
        x0, y0 = sep[0], sep[1] + vy * 0.35
        x1, y1 = ul - rad * 0.6, vy
        # distance au segment, en unités de v (u mis à l'échelle de l'image)
        sx = W / (H / 2)
        px, py = (u - x0) * sx, v - y0
        dx, dy = (x1 - x0) * sx, y1 - y0
        tt = np.clip((px * dx + py * dy) / (dx * dx + dy * dy), 0, 1)
        d = np.hypot(px - tt * dx, py - tt * dy)
        r_ = rad * 1.7 * (1 - 0.35 * tt)
        mk = d < r_
        m |= mk
        shade = np.where(mk, np.maximum(shade, 1 - d / r_), shade)
    body = (u < 0.5) & (np.abs(v) < hw)
    shade = np.where(body, np.maximum(shade, 1 - np.abs(v) / np.maximum(hw, 1e-3)), shade)
    col = lerp(CUIR["low"], BRIN, np.clip(shade * 1.6, 0, 1)[..., None])
    col[shade > 0.62] = CUIR["hi"]                                           # reflet blanc net au cœur de chaque brin
    col[(shade > 0.45) & (shade <= 0.62)] = lerp(CUIR["hi"], BRIN, 0.5)
    # ligature chrome à la racine (3 texels)
    lig = (u > 0.06) & (u < 0.13) & body
    col[lig] = ARGENT["base"]
    rgb = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(m.astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    out[~al, :3] = 0
    uu = (np.arange(W) + 0.5)[None, :] / W * np.ones((H, 1))
    e = np.zeros((H, W, 4), np.uint8)
    glow = al & (uu > 0.2)
    e[glow] = 0                          # plus de lueur (révision latex)
    return out, e


TILES = {}
TILES["tresse_manche"] = braid_tile(128, 24, 10.0, 1)
TILES["tresse_manche_reflet"] = braid_tile(128, 24, 10.0, 1, reflet=True)
TILES["tresse_laniere"] = braid_tile(48, 16, 8.0, 2)
TILES["tresse_laniere_reflet"] = braid_tile(48, 16, 8.0, 2, reflet=True)
TILES["cap_cuir"] = cap_tile(CUIR)
TILES["argent"] = silver_tile()
TILES["cap_argent"] = cap_tile(ARGENT)
TILES["sangle"] = strap_tile()
TILES["sangle_bord"] = edge_tile()
def rivet_tile(n=12):
    """Rivet rond plat vu de dessus : disque chrome découpé par alpha, bord sombre, éclat net."""
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) / (n / 2)
    c = ARGENT["base"] * np.ones((n, n, 3), np.float32)
    c[r > 0.72] = ARGENT["low"]
    c[np.hypot(xx + 0.5 - n * 0.38, yy + 0.5 - n * 0.38) < n * 0.18] = ARGENT["hi"]
    return finish(c, r < 0.98)


TILES["rivet"] = rivet_tile()
TILES["rivet_bord"] = finish(ARGENT["low"] * np.ones((4, 12, 3), np.float32))
MECHE, MECHE_E = meche_tiles()
TILES["meche"] = MECHE
TILES["meche_ame"] = finish(BRIN * np.ones((8, 16, 3), np.float32))


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
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
for n, im in TILES.items():
    u0, v0, u1, v1 = UV[n]
    tex[v0:v1, u0:u1] = im
u0, v0, u1, v1 = UV["meche"]
tex_e[v0:v1, u0:u1] = MECHE_E
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC
tex[tex[..., 3] == 0] = 0
assert set(np.unique(tex[..., 3])) <= {0, 255}
assert set(np.unique(tex_e[..., 3])) <= {0, 255}


def b64(arr, fn):
    im = Image.fromarray(arr, "RGBA")
    im.save(fn, optimize=True)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


tex_b64 = b64(tex, f"{NOM}.png")
tex_e_b64 = b64(tex_e, f"{NOM}_e.png")

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


def rotm(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def euler(R):
    if abs(R[2, 0]) < 0.99999:
        ry = math.asin(-R[2, 0])
        e = (math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0])))
    elif R[2, 0] < 0:
        e = (math.degrees(math.atan2(R[0, 1], R[0, 2])), 90.0, 0.0)
    else:
        e = (math.degrees(math.atan2(-R[0, 1], -R[0, 2])), -90.0, 0.0)
    assert np.allclose(rotm(*e), R, atol=1e-6), "euler"
    return e


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups, name
    groups[name] = {"origin": [round(float(v), 4) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(float(v), 4) for v in rotation]}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def full(tile):
    return list(UV[tile])


def along(tile, cap, up=None):
    """Cube allongé sur X : les 4 côtés portent la tuile (longueur = largeur de l'image), les bouts le capuchon.
    up : tuile de la face du dessus (reflet du latex), sinon la même."""
    t = full(tile)
    c = full(cap) if cap else CLEAR
    return {"north": t, "south": t, "up": full(up) if up else t, "down": t, "east": c, "west": c}


def PT(a):
    """Point de l'axe du fouet (repère non tourné) à l'abscisse a."""
    return P0 + V(a - A_GRIP, 0, 0)


def octo(g, name, a0, a1, r, tile, cap, off=0.0, up=None):
    """Section octogonale : deux cubes le long de X, le second tourné de 45° et raccourci de 0,1 px à chaque bout
    (bouts jamais à moins de 0,1 px l'un de l'autre)."""
    o = PT(a0)
    f = along(tile, cap, up)
    cube(g, name, PT(a0) + (0, -r, -r), PT(a1) + (0, r, r), o, (off, 0, 0), f)
    r2 = r * 0.97
    cube(g, name + "o", PT(a0 + 0.1) + (0, -r2, -r2), PT(a1 - 0.1) + (0, r2, r2), o, (off + 45, 0, 0), f)


def bar_pq(g, name, p, q, r, tile, cap, ov=0.05):
    """Barreau en losange de p à q (section carrée tournée de 45° sur son axe)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    X = unit(q - p)
    ref = V(0, 0, 1) if abs(X[2]) < 0.9 else V(0, 1, 0)
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R45 = np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])
    cube(g, name, p + (-ov, -r, -r), p + (L + ov, r, r), p, euler(R45), along(tile, cap))


def oriented(g, name, c, X, Y, size, faces):
    X = unit(np.asarray(X, float))
    Y = np.asarray(Y, float)
    Y = unit(Y - (Y @ X) * X)
    Z_ = np.cross(X, Y)
    c = np.asarray(c, float)
    cube(g, name, c - size, c + size, c, euler(np.column_stack([X, Y, Z_])), faces)


def stud(g, name, a, ang, r_base):
    """Rivet rond plat de chrome : pastille de 0,4 px posée sur le manche (dessus peint en disque découpé), 0,12 px au-dessus
    de la surface (jamais à moins de 0,1 px d'une face du manche), le reste enfoui."""
    n = V(0, math.cos(math.radians(ang)), math.sin(math.radians(ang)))
    ctr = PT(a) + n * (r_base + 0.04)
    oriented(g, name, ctr, V(1, 0, 0), n, np.array((0.2, 0.08, 0.2)),
             {"up": full("rivet"), "down": CLEAR, "north": full("rivet_bord"), "south": full("rivet_bord"),
              "east": full("rivet_bord"), "west": full("rivet_bord")})


bras = group("right_arm", [5, 22, 0])
fouet = group("fouet", P0, parent=bras)          # rotation de base posée plus bas (pose de repos)

# Manche tressé, pommeau, bague
A_BACK = -7.4
octo(fouet, "manche", A_BACK, 0.25, 0.6, "tresse_manche", "cap_cuir", up="tresse_manche_reflet")
octo(fouet, "pommeau", -8.1, -7.0, 0.78, "argent", "cap_argent", off=22.5)
octo(fouet, "pommeau_bout", -8.6, -7.8, 0.46, "argent", "cap_argent")      # 2026-11-05 : -7,85 -> -7,8 (faces à 0,05 px)
octo(fouet, "bague", -0.45, 0.45, 0.74, "argent", "cap_argent", off=11.25)
octo(fouet, "virole", -1.95, -1.65, 0.67, "argent", "cap_argent", off=11.25)
for k in range(4):
    stud(fouet, f"rivet_av{k}", -1.15, 90 * k + 45, 0.6)
    stud(fouet, f"rivet_ar{k}", -6.65, 90 * k, 0.6)          # 2026-11-05 : rivets à 0,1 px des bouts du manche et du pommeau
    stud(fouet, f"rivet_pom{k}", -7.7, 90 * k + 45, 0.78)

# Anneau en D au bout du pommeau (dans le plan vertical du manche) et dragonne qui pend
A_D = -8.72
anneau = group("anneau_d", PT(-8.6), parent=fouet)
RD = 0.55
pts = [PT(A_D) + V(-RD * math.sin(math.radians(th)), RD * math.cos(math.radians(th)), 0) for th in (0, 36, 72, 108, 144, 180)]
bar_pq(anneau, "d_droit", PT(A_D) + V(0, RD, 0), PT(A_D) + V(0, -RD, 0), 0.11, "argent", "cap_argent", ov=0.08)
for i in range(5):
    bar_pq(anneau, f"d_arc{i}", pts[i], pts[i + 1], 0.11, "argent", "cap_argent", ov=0.06)
DR_O = PT(A_D) + V(-RD, 0, 0)
drag = group("dragonne", DR_O, parent=anneau)
sangle = {"up": full("sangle"), "down": full("sangle"), "north": full("sangle_bord"), "south": full("sangle_bord"),
          "east": full("sangle_bord"), "west": full("sangle_bord")}
bot_a, bot_b = DR_O + V(0.55, -2.9, 0), DR_O + V(-0.55, -2.9, 0)
# demi-largeurs 0,32 / 0,21 / 0,42 : les tranches des trois brins ne sont jamais à moins de 0,1 px l'une de l'autre
for nm, p, q, hw in (("dragonne_av", DR_O + V(0.08, 0.05, 0), bot_a, 0.32), ("dragonne_ar", DR_O + V(-0.08, 0.05, 0), bot_b, 0.21)):
    X = unit(q - p)
    Yn = np.cross(V(0, 0, 1), X)          # normale des grandes faces, dans le plan vertical
    oriented(drag, nm, (p + q) / 2, X, Yn, np.array((np.linalg.norm(q - p) / 2 + 0.12, 0.15, hw)), sangle)
oriented(drag, "dragonne_bas", (bot_a + bot_b) / 2 + V(0, -0.05, 0), V(1, 0, 0), V(0, 1, 0), np.array((0.72, 0.16, 0.42)), sangle)

# Lanière : un groupe par segment, pivot à la jointure. Décalage de l'octogone alterné (0 / 22,5°) : jamais deux faces parallèles
# entre voisins, même lanière tendue.
SEGS = []
parent = fouet
for j in range(N):
    gname = group(f"seg{j:02d}", PT(JOINTS[j]), parent=parent)
    off = 22.5 if j % 2 == 0 else 0.0
    o = PT(JOINTS[j])
    r = SEG_R[j]
    f = along("tresse_laniere", "cap_cuir", "tresse_laniere_reflet")
    cube(gname, f"lan{j:02d}", o + (-0.15, -r, -r), o + (SEG_L[j] + 0.15, r, r), o, (off, 0, 0), f)
    r2 = r * 0.97
    fo = dict(f, east=CLEAR, west=CLEAR)      # bouts cachés dans le segment voisin (2026-11-05 : face à face à 0,09 px)
    cube(gname, f"lan{j:02d}o", o + (-0.05, -r2, -r2), o + (SEG_L[j] + 0.05, r2, r2), o, (off + 45, 0, 0), fo)
    SEGS.append(gname)
    parent = gname

# Mèche : deux plaques croisées (peau découpée), âme pleine en losange (tournée de 45° : aucune face parallèle aux plaques)
meche = group("meche", PT(L_LASH), parent=parent)
mo = PT(L_LASH)
a0, a1 = -0.3, MECHE_L - 0.3
plq = full("meche")
plq_back = [plq[2], plq[1], plq[0], plq[3]]
cube(meche, "meche_v", mo + (a0, -MECHE_W / 2, -0.15), mo + (a1, MECHE_W / 2, 0.15), mo, (22.5, 0, 0),
     {"south": plq, "north": plq_back, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
cube(meche, "meche_h", mo + (a0 + 0.04, -0.15, -MECHE_W / 2), mo + (a1 + 0.04, 0.15, MECHE_W / 2), mo, (22.5, 0, 0),
     {"up": plq, "down": plq, "east": CLEAR, "west": CLEAR, "north": CLEAR, "south": CLEAR})
cube(meche, "meche_ame", mo + (-0.2, -0.17, -0.17), mo + (1.15, 0.17, 0.17), mo, (67.5, 0, 0), along("meche_ame", "meche_ame"))
# nœud de cuir à la racine de la mèche (ligature)
cube(meche, "noeud", mo + (-0.42, -0.3, -0.3), mo + (0.12, 0.3, 0.3), mo, (11.25, 0, 0), along("tresse_laniere", "cap_cuir", "tresse_laniere_reflet"))
cube(meche, "noeudo", mo + (-0.32, -0.29, -0.29), mo + (0.02, 0.29, 0.29), mo, (56.25, 0, 0), along("tresse_laniere", "cap_cuir", "tresse_laniere_reflet"))

# ------------------------------------------------------------------ cinématique : forme d'un état → rotations des groupes
CHAIN = [fouet] + SEGS + [meche]          # meche = dernier « segment », longueur MECHE_L
LENS = SEG_L + [MECHE_L]
RADS = SEG_R + [0.6]


def dvec(phi, h):
    p, hh = math.radians(phi), math.radians(h)
    return V(math.sin(hh) * math.cos(p), math.sin(p), -math.cos(hh) * math.cos(p))


def rot_between(a, b):
    k = np.cross(a, b)
    s, c = np.linalg.norm(k), float(a @ b)
    if s < 1e-12:
        return np.eye(3)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]]) / s
    ang = math.atan2(s, c)
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K


def frames(dirs):
    """dirs[0] : direction du manche ; dirs[1..] : segments puis mèche. Repères monde sans torsion."""
    X = dirs[0]
    up = V(0, 1, 0)
    Y = unit(up - (up @ X) * X)
    M = [np.column_stack([X, Y, np.cross(X, Y)])]
    for d in dirs[1:]:
        M.append(rot_between(M[-1][:, 0], d) @ M[-1])
    return M


def fk(M):
    """Points (centre, rayon) le long du manche et de la lanière, bras au repos."""
    pts = []
    for a in np.linspace(-9.7, 0, 12):
        pts.append((P0 + M[0] @ V(a - A_GRIP, 0, 0), 0.8))
    p = P0 + M[0] @ V(-A_GRIP, 0, 0)
    for j in range(1, len(M)):
        q = p + M[j][:, 0] * LENS[j - 1]
        for k in np.linspace(0, 1, 4)[1:]:
            pts.append((p + (q - p) * k, RADS[j - 1]))
        p = q
    return pts


def arm(alpha, dy=0.0):
    R = rotm(alpha, 0, 0)
    piv = V(5, 22, 0)
    return lambda p: R @ (p - piv) + piv + V(0, dy, 0)


def prof(s, knots):
    """Interpolation douce (cosinus) entre nœuds (s, valeur)."""
    ss = [k[0] for k in knots]
    if s <= ss[0]:
        return knots[0][1]
    if s >= ss[-1]:
        return knots[-1][1]
    i = max(i for i in range(len(ss) - 1) if ss[i] <= s)
    u = (s - ss[i]) / (ss[i + 1] - ss[i])
    w = (1 - math.cos(math.pi * u)) / 2
    return lerp(knots[i][1], knots[i + 1][1], w)


S_MID = [JOINTS[j] + SEG_L[j] / 2 for j in range(N)] + [L_LASH + MECHE_L / 2]


def shape(phi_h, h_h, phik, hk, wave=lambda s, u: (0.0, 0.0)):
    dirs = [dvec(phi_h, h_h)]
    for s in S_MID:
        u = s / (L_LASH + MECHE_L)
        dp, dh = wave(s, u)
        dirs.append(dvec(prof(s, phik) + dp, prof(s, hk) + dh))
    return frames(dirs)


def min_y(Mt, arms):
    pts = fk(Mt)
    return min(f(p)[1] - r for f in arms for p, r in pts)


def min_x_low(Mt, arms):
    """Plus petit x de la lanière sous la hanche (y < 13), où passe la jambe droite (x de 0 à 4)."""
    xs = [f(p)[0] - r for f in arms for p, r in fk(Mt)[12:] if f(p)[1] < 13]
    return min(xs) if xs else 99.0


class Etat:
    def __init__(self, name, L, build, arms, target, lo, hi, fps=24):
        """build(t, lam) -> repères ; lam = profondeur de pendaison, réglée par dichotomie pour que min y = target."""
        self.name, self.L, self.build, self.arms, self.fps = name, L, build, arms, fps
        ts = np.linspace(0, L, 25)
        f = lambda lam: min(min_y(build(t, lam), arms) for t in ts)
        a, b = lo, hi
        for _ in range(30):
            m = (a + b) / 2
            if f(m) > target:
                a = m
            else:
                b = m
        self.lam = a
        self.miny = f(a)
        self.minx = min(min_x_low(build(t, a), arms) for t in ts)

    def at(self, t):
        return self.build(t, self.lam)


W_ = lambda L, k=1: TAU * k / L          # pulsation d'une boucle fermée

ARMS_REPOS = [arm(0)]
ARMS_WALK = [arm(a) for a in np.linspace(-22.4, 22.4, 9)]       # renderer : bras droit = -0,8 × 28° × sin, toutes phases
ARMS_RUN = [arm(a) for a in np.linspace(-44, 44, 11)]
ARMS_SNEAK = [arm(23, -3.2)]


def b_idle(t, lam):
    w = W_(8.0, 2)

    def wave(s, u):
        hang = 1 - sm(s, lam, lam + 6)
        return (3.0 * math.sin(w * t / 2 - 2.2 * u) * hang + 1.2 * math.sin(w * t - 3 * u),
                4.0 * math.sin(w * t / 2 - 2.6 * u + 0.8) * (0.25 + u))
    return shape(12 + 1.5 * math.sin(w * t / 2), 8 + 1.5 * math.sin(w * t / 2 + 1),
                 [(0, 0), (3.5, -78), (lam, -86), (lam + 6, -6), (L_LASH, 2), (L_LASH + 3, 8)],
                 [(0, 10), (lam, 18), (lam + 6, 28), (L_LASH + 3, 33)], wave)


def b_walk(t, lam):
    w = W_(1.6)

    def wave(s, u):
        return (5.0 * math.sin(w * t - 1.5 - 2.4 * u) * (0.3 + u), 9.0 * math.sin(w * t - 2.0 * u) * (0.2 + u))
    return shape(8 + 3 * math.sin(w * t), 10 + 2 * math.sin(w * t + 0.6),
                 [(0, 0), (3.5, -76), (lam, -86), (lam + 5, -20), (L_LASH + 3, 12)],
                 [(0, 12), (lam, 50), (lam + 4, 100), (L_LASH + 3, 132)], wave)


def b_run(t, lam):
    w = W_(1.0)

    def wave(s, u):
        return (7.0 * math.sin(2 * w * t - 3.2 * u - 1.0) * u, 7.0 * math.sin(2 * w * t - 3.0 * u) * u)
    return shape(4 + 2 * math.sin(w * t), 6, [(0, -10), (3, -lam), (8, -lam * 0.6), (13, 2), (L_LASH + 3, 14)],
                 [(0, 20), (3, 45), (8, 112), (13, 160), (L_LASH + 3, 172)], wave)


def b_sneak(t, lam):
    w = W_(4.0)

    def wave(s, u):
        hang = 1 - sm(s, lam, lam + 6)
        return (2.5 * math.sin(w * t - 2.0 * u) * hang, 3.5 * math.sin(w * t - 2.4 * u + 0.6) * (0.25 + u))
    return shape(4 + 1.5 * math.sin(w * t), 10, [(0, -8), (3.0, -78), (lam, -86), (lam + 6, -6), (L_LASH, 2), (L_LASH + 3, 8)],
                 [(0, 10), (lam, 24), (lam + 6, 40), (L_LASH + 3, 46)], wave)


def b_fly(t, lam):
    w = W_(2.4)

    def wave(s, u):
        return (9.0 * math.sin(w * t - 4.2 * u) * (0.25 + u), 6.0 * math.sin(w * t - 3.6 * u + 1.2) * (0.2 + u))
    return shape(8 + 2 * math.sin(w * t), 6, [(0, -lam), (4, -lam * 0.6), (10, -6), (L_LASH + 3, 6)],
                 [(0, 22), (4, 60), (10, 132), (16, 166), (L_LASH + 3, 176)], wave)


def b_fall(t, lam):
    w = W_(1.2)

    def wave(s, u):
        return (8.0 * math.sin(w * t - 3.8 * u) * (0.2 + u), 7.0 * math.sin(w * t - 3.0 * u + 0.9) * (0.2 + u))
    return shape(14 + 2 * math.sin(w * t), 6, [(0, 10), (4, -lam), (12, -lam + 18), (L_LASH + 3, -lam + 28)],
                 [(0, 20), (4, 70), (12, 140), (L_LASH + 3, 168)], wave)


ETATS = [Etat("idle", 8.0, b_idle, ARMS_REPOS, 0.85, 3.6, 16.0),
         Etat("walk", 1.6, b_walk, ARMS_WALK, 0.8, 3.6, 16.0),
         Etat("run", 1.0, b_run, ARMS_RUN, 2.0, -20.0, 45.0),
         Etat("sneak", 4.0, b_sneak, ARMS_SNEAK, 0.85, 3.1, 16.0),
         Etat("fly", 2.4, b_fly, ARMS_REPOS, 3.0, 22.0, 22.0),
         Etat("fall", 1.2, b_fall, ARMS_REPOS, 3.0, -8.0, -8.0)]
for e in ETATS:
    print(f"  {e.name:6s} lam = {e.lam:6.2f}  min y = {e.miny:5.2f}  min x (sous la hanche) = {e.minx:5.2f}")
    assert e.minx > 4.6, f"{e.name} : la lanière s'approche de la jambe"


def rel_eulers(M):
    """Rotations (Euler) de chaque groupe de la chaîne : manche relatif au bras, puis relatif au parent."""
    out = [euler(M[0])]
    for j in range(1, len(M)):
        out.append(euler(M[j - 1].T @ M[j]))
    return out


BASE = rel_eulers(ETATS[0].at(0.0))
for g, e in zip(CHAIN, BASE):
    groups[g]["rotation"] = [round(float(v), 4) for v in e]


def unwrap(seq):
    out = [np.array(seq[0], float)]
    for v in seq[1:]:
        v = np.array(v, float)
        v += 360 * np.round((out[-1] - v) / 360)
        out.append(v)
    return out


def kf(t, v, ch="rotation"):
    return {"channel": ch, "data_points": [{"x": str(round(float(v[0]) + 0.0, 3)), "y": str(round(float(v[1]) + 0.0, 3)),
                                            "z": str(round(float(v[2]) + 0.0, 3))}], "time": round(t, 4), "interpolation": "linear"}


def anim_from(name, L, values, fps, loop="loop", extra=None):
    """values(t) -> {groupe: (x, y, z)} (rotations, écart à la base)."""
    n = max(6, int(round(L * fps)))
    times = [i * L / n for i in range(n + 1)]
    samples = [values(t) for t in times]
    A_ = {}
    for g in samples[0]:
        seq = unwrap([s[g] for s in samples])
        A_[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(t, v) for t, v in zip(times, seq)]}
    for (g, ch), f in (extra or {}).items():
        A_.setdefault(groups[g]["uuid"], {"name": g, "type": "bone", "keyframes": []})["keyframes"] += [kf(t, f(t), ch) for t in times]
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": L, "snapping": 24, "selected": name == "idle",
            "animators": A_}


def pendule(amp, k, L, ph=0.0):
    """Anneau en D et dragonne : balancement amorti par rapport au manche (autour de l'axe Z du manche)."""
    return {("anneau_d", "rotation"): lambda t: (0, 0, amp * math.sin(TAU * k * t / L + ph)),
            ("dragonne", "rotation"): lambda t: (0, 0, amp * 0.8 * math.sin(TAU * k * t / L + ph - 1.0))}


PEND = {"idle": (5, 2), "walk": (12, 1), "run": (20, 2), "sneak": (5, 1), "fly": (10, 1), "fall": (16, 2)}


def state_anim(e):
    def values(t):
        eu = rel_eulers(e.at(t))
        return {g: np.array(v) - np.array(b) for g, v, b in zip(CHAIN, eu, BASE)}
    return anim_from(e.name, e.L, values, 24 if e.L > 2 else 30, extra=pendule(PEND[e.name][0], PEND[e.name][1], e.L))


ANIMS = [state_anim(e) for e in ETATS]

# ------------------------------------------------------------------ attaque et blessure (écarts, par-dessus l'état)
T_CRACK = 0.42
NC = len(SEGS) + 1


def attack_frames(t):
    """Forme de la lanière pendant le coup, dans le repère du bras (bras du jeu non compris) :
    repos → jetée en arrière par-dessus la main → une boucle roule de la racine à la mèche (front uf) → lanière tendue devant,
    claquement de la mèche → elle retombe vers la pose de repos."""
    Mi = ETATS[0].at(0.0)
    d_idle = [Mi[k][:, 0] for k in range(len(Mi))]
    uf = (t - 0.14) / (T_CRACK - 0.14)
    g_back = sm(t, 0.0, 0.13)
    g_fall = sm(t, 0.47, 0.76)
    dirs = [d_idle[0]]
    for k, s in enumerate(S_MID):
        u = s / (L_LASH + MECHE_L)
        back = dvec(lerp(40, 150, u ** 0.8), lerp(10, 4, u))                 # en arrière, par-dessus la main
        fwd = dvec(4 - 6 * u, 10)                                             # tendue devant, à peine plongeante
        roll = sm(uf - u, -0.07, 0.07)
        d = unit(lerp(back, fwd, roll))
        d = unit(lerp(d_idle[k + 1], d, g_back))
        d = unit(lerp(d, d_idle[k + 1], g_fall))
        dirs.append(d)
    return frames(dirs)


BASE_ATT = rel_eulers(ETATS[0].at(0.0))


def attack_vals(t):
    win = 1 - sm(t, 0.66, 0.79)
    eu = unwrap_list = rel_eulers(attack_frames(t))
    out = {fouet: (0, 0, (-12 * bump(t, 0.1, 0.2, 0.26, 0.5) + 7 * bump(t, 0.0, 0.08, 0.1, 0.2)) * win)}
    for j, g in enumerate(SEGS + [meche]):
        u = j / (NC - 1)
        d = np.array(eu[j + 1]) - np.array(BASE_ATT[j + 1])
        d = (d + 180) % 360 - 180
        crack = 0.0
        if j >= NC - 4:
            x = t - T_CRACK
            w_ = (j - (NC - 5)) / 4
            crack = 30 * w_ * math.sin(TAU * x / 0.055) * math.exp(-x / 0.035) if x > 0 else 0.0
        settle = -5 * math.sin(TAU * (t - 0.47 - 0.08 * u) / 0.22) * math.exp(-max(t - 0.47, 0) / 0.1) * sm(t, 0.45, 0.5) * (0.3 + u)
        out[g] = (d[0] * win, d[1] * win, (d[2] + crack + settle) * win)
    return out


attack = anim_from("attack", 0.8, attack_vals, 60, loop="once", extra={
    ("anneau_d", "rotation"): lambda t: (0, 0, (28 * bump(t, 0.05, 0.18, 0.2, 0.4) - 16 * bump(t, 0.3, 0.42, 0.45, 0.62)) * (1 - sm(t, 0.62, 0.78))),
    ("dragonne", "rotation"): lambda t: (0, 0, (24 * bump(t, 0.1, 0.24, 0.26, 0.46) - 14 * bump(t, 0.36, 0.48, 0.5, 0.66)) * (1 - sm(t, 0.64, 0.78)))})
attack["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "entity.player.attack.crit", "file": ""}], "time": T_CRACK}]}


def hurt_vals(t):
    win = sm(t, 0.0, 0.03) * (1 - sm(t, 0.55, 0.78))
    out = {fouet: (0, 0, 9 * math.sin(TAU * t / 0.32) ** 2 * math.exp(-t / 0.15) * win)}          # sursaut vers le haut seulement
    for j, g in enumerate(SEGS + [meche]):
        u = j / (NC - 1)
        out[g] = (0, 3 * math.sin(TAU * (t - 0.1 * u) / 0.3) * math.exp(-t / 0.22) * win * u,
                  7 * math.sin(TAU * (t - 0.12 * u) / 0.44) ** 2 * math.exp(-t / 0.2) * win * (0.4 + u))     # la lanière se soulève, ne plonge pas
    return out


hurt = anim_from("hurt", 0.8, hurt_vals, 40, loop="once", extra={
    ("anneau_d", "rotation"): lambda t: (0, 0, 20 * math.sin(TAU * t / 0.25) * math.exp(-t / 0.2) * (1 - sm(t, 0.55, 0.78)))})
ANIMS += [attack, hurt]


# ------------------------------------------------------------------ traînée et claquement (remise aux règles du 2026-11-05)
# Fiche .claude/references/effets/impacts-attaques.md : traînée en drapeau (tête épaisse et claire côté mèche, queue fine), née en
# entier au claquement (smear), effacée de la queue vers la tête en 0,25 s ; étoile d'impact brève au bout (≤ 6 px). Blanc
# argenté, pas de rouge (cuir.md). add_ (sans shader) doublé en trans_ discret (avec shader, add_ est invisible).
# Cachées hors attaque par ctrl_alpha à -1 dans chaque état ; l'attaque ajoute +1 pendant le coup (les positions s'ajoutent
# entre l'état et l'attaque : guide 6.4, supposé pour attack). La traînée suit le vrai trajet de la mèche (cinématique des
# clés d'attaque), dans le repère du bras.
T0_TR, T_TR = 0.25, T_CRACK                 # portion du trajet de la mèche peinte en traînée
D_TR = 5.0                                  # texels par px (lueur douce)


def bout_meche(t):
    vals = attack_vals(t)
    p = PT(L_LASH + MECHE_L - 0.4)
    for g in reversed(CHAIN):
        R = rotm(*(np.array(groups[g]["rotation"]) + np.array(vals.get(g, (0, 0, 0)))))
        o = np.array(groups[g]["origin"], float)
        p = R @ (p - o) + o
    return p


TT_TR = np.linspace(T0_TR, T_TR, 40)
CHEMIN = np.array([bout_meche(t) for t in TT_TR])
C_TR = CHEMIN.mean(0)
_u, _s, _vt = np.linalg.svd(CHEMIN - C_TR)
E1, E2, NTR = _vt[0], _vt[1], _vt[2]
if NTR[0] < 0:                              # face visible tournée vers l'extérieur du joueur (+X)
    NTR, E2 = -NTR, -E2
UV2 = np.stack([(CHEMIN - C_TR) @ E1, (CHEMIN - C_TR) @ E2], 1)
S_PATH = np.linspace(0, 1, len(UV2))        # 0 = queue (début du trajet), 1 = tête (claquement)
LARG = lambda s: 0.15 + 1.05 * s ** 1.4    # demi-largeur (px) : drapeau
SECTIONS = [(0.0, 0.42), (0.42, 0.74), (0.74, 1.0)]


def champ_trainee(x, y):
    """Distance au trajet et abscisse s du point le plus proche (x, y : coordonnées du plan, px)."""
    P = np.stack([x.ravel(), y.ravel()], 1)
    best_d, best_s = np.full(len(P), 9e9), np.zeros(len(P))
    for k in range(len(UV2) - 1):
        a, b = UV2[k], UV2[k + 1]
        ab = b - a
        tt = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
        d = np.linalg.norm(P - (a + tt[:, None] * ab), axis=1)
        m = d < best_d
        best_d[m], best_s[m] = d[m], (S_PATH[k] + (S_PATH[k + 1] - S_PATH[k]) * tt)[m]
    return best_d.reshape(x.shape), best_s.reshape(x.shape)


def peindre_section(k, trans=False):
    s0, s1 = SECTIONS[k]
    sel = (S_PATH >= s0 - 0.03) & (S_PATH <= s1 + 0.03)
    lo, hi = UV2[sel].min(0) - 1.4, UV2[sel].max(0) + 1.4
    W, H = int(math.ceil((hi[0] - lo[0]) * D_TR)), int(math.ceil((hi[1] - lo[1]) * D_TR))
    SSx = 3
    xs = lo[0] + (np.arange(W * SSx) + 0.5) / (W * SSx) * (hi[0] - lo[0])
    ys = hi[1] - (np.arange(H * SSx) + 0.5) / (H * SSx) * (hi[1] - lo[1])          # v vers le bas = y du plan vers le bas
    X, Y = np.meshgrid(xs, ys)
    d, s = champ_trainee(X, Y)
    w = LARG(s)
    f = np.clip(1 - d / w, 0, 1) ** 1.3 * (0.3 + 0.7 * s ** 0.9)
    f *= (s >= s0) & (s < s1 + (0.001 if k == 2 else 0))
    f *= smooth01(np.clip(s / 0.08, 0, 1))
    f = np.array(Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    out = np.zeros((H, W, 4), np.uint8)
    if trans:
        al = np.where(f > 0.12, np.clip(f * 150, 1, 254), 0)
        out[..., :3] = (232, 236, 244)
        out[..., 3] = al.astype(np.uint8)
        out[al == 0, :3] = 0
    else:
        coeur, bord = np.array((228, 232, 242), np.float32), np.array((120, 138, 178), np.float32)
        rgb = (bord + (coeur - bord) * f[..., None] ** 0.7) * f[..., None] ** 0.9
        lum = rgb.max(2)
        out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        out[..., 3] = (lum > 14) * 255
        out[lum <= 14, :3] = 0
    return out, lo, hi


def smooth01(x):
    return x * x * (3 - 2 * x)


def peindre_etoile(N=32, trans=False):
    g = (np.arange(N * 3) + 0.5) / (N * 3) * 2 - 1
    x, y = np.meshgrid(g, -g)
    r, a = np.hypot(x, y), np.arctan2(y, x)
    pointes = 0.55 + 0.45 * np.abs(np.cos(4 * a)) ** 6 * (0.75 + 0.25 * np.cos(8 * a + 0.7))   # 8 pointes inégales
    f = np.clip(1 - r / pointes, 0, 1) ** 1.6
    f = np.maximum(f, np.clip(1 - r / 0.28, 0, 1))
    f = np.array(Image.fromarray((f * 255).astype(np.uint8), "L").resize((N, N), Image.LANCZOS)).astype(np.float32) / 255
    out = np.zeros((N, N, 4), np.uint8)
    if trans:
        al = np.where(f > 0.12, np.clip(f * 140, 1, 254), 0)
        out[..., :3] = (240, 242, 248)
        out[..., 3] = al.astype(np.uint8)
        out[al == 0, :3] = 0
    else:
        rgb = np.array((236, 238, 246), np.float32) * f[..., None]
        lum = rgb.max(2)
        out[..., :3] = rgb.astype(np.uint8)
        out[..., 3] = (lum > 14) * 255
        out[lum <= 14, :3] = 0
    return out


# Peinture dans la partie libre de l'atlas (sous la ligne 50), rangée par rangée.
_x, _y, _h = 0, 52, 0
UV_TR = {}


def poser_tr(nom, im):
    global _x, _y, _h
    h, w = im.shape[:2]
    if _x + w > TEX:
        _x, _y, _h = 0, _y + _h + 1, 0
    assert _y + h <= TEX - 6 and not tex[_y:_y + h, _x:_x + w, 3].any(), f"atlas : {nom}"
    tex[_y:_y + h, _x:_x + w] = im
    UV_TR[nom] = [_x, _y, _x + w, _y + h]
    _x += w + 1
    _h = max(_h, h)


RECTS = {}
for k in range(3):
    for tr in (False, True):
        im, lo, hi = peindre_section(k, tr)
        poser_tr(f"tr{k}{'t' if tr else ''}", im)
        RECTS[k] = (lo, hi)
poser_tr("etoile", peindre_etoile())
poser_tr("etoilet", peindre_etoile(trans=True))
tex_b64 = b64(tex, f"{NOM}.png")

R_TR = np.column_stack([E1, E2, NTR])
TRAIN = group("trainee", C_TR, parent=bras)
CTRL_CACHE = []                             # groupes ctrl_alpha : -1 dans les états, +1 ajouté pendant le coup
for k in range(3):
    lo, hi = RECTS[k]
    cen2 = (lo + hi) / 2
    for tr in (False, True):
        g = group(f"{'trans' if tr else 'add'}_trainee{k + 1}", C_TR, parent=TRAIN)
        ca = group(f"ctrl_alpha_tr{k}{'t' if tr else ''}", C_TR, parent=g)
        CTRL_CACHE.append((ca, k))
        off = (-0.14 - 0.12 * k) if tr else 0.12 * k     # plaques jamais à moins de 0,1 px l'une de l'autre
        c3 = C_TR + R_TR @ np.array([cen2[0], cen2[1], off])
        half = np.array([(hi[0] - lo[0]) / 2, (hi[1] - lo[1]) / 2, 0.15])
        cube(g, f"trainee{k + 1}{'_voile' if tr else ''}", c3 - half, c3 + half, c3, euler(R_TR),
             {"south": UV_TR[f"tr{k}{'t' if tr else ''}"], "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})
        # cube() pose from/to autour de c3 dans le repère monde, tourné autour de c3 : la plaque est dans le plan du trajet

# Étoile d'impact au bout de la mèche (face caméra), 4 px.
P_TIP = PT(L_LASH + MECHE_L - 0.4)
ECL = group("claquement", P_TIP, parent=meche)
CAM = group("cam_claquement", P_TIP, parent=ECL)
for tr in (False, True):
    g = group(f"{'trans' if tr else 'add'}_eclat", P_TIP, parent=CAM)
    ca = group(f"ctrl_alpha_ecl{'t' if tr else ''}", P_TIP, parent=g)
    CTRL_CACHE.append((ca, "e"))
    z = -0.14 if tr else 0.0
    cube(g, f"eclat{'_voile' if tr else ''}", P_TIP + (-2.0, -2.0, z - 0.15), P_TIP + (2.0, 2.0, z + 0.15), P_TIP, (0, 0, 0),
         {"south": UV_TR["etoilet" if tr else "etoile"], "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})

# Noms des groupes de contrôle : le guide exige le nom exact « ctrl_alpha » (clé interne unique, nom affiché répété).
for ca, _ in CTRL_CACHE:
    groups[ca]["nom"] = "ctrl_alpha"


def piste_ctrl(anim, g, keys):
    anim["animators"].setdefault(groups[g]["uuid"], {"name": "ctrl_alpha", "type": "bone", "keyframes": []})["keyframes"] += keys


def kfp(t, x):
    return {"channel": "position", "data_points": [{"x": str(round(x, 3)), "y": "0", "z": "0"}], "time": round(t, 4), "interpolation": "linear"}


for an in ANIMS:
    if an["name"] in ("attack", "hurt"):
        continue
    for ca, _ in CTRL_CACHE:
        piste_ctrl(an, ca, [kfp(0, -1)])                  # caché dans tous les états

# Attaque : smear à T_CRACK - 0,01 (toute la traînée), effacement queue -> tête, étoile 0,1 s.
FIN = {0: T_CRACK + 0.06, 1: T_CRACK + 0.13, 2: T_CRACK + 0.22}
for ca, k in CTRL_CACHE:
    if k == "e":
        on, off = T_CRACK, T_CRACK + 0.1
    else:
        on, off = T_CRACK - 0.01, FIN[k]
    piste_ctrl(attack, ca, [kfp(0, 0), kfp(on - 0.012, 0), kfp(on, 1), kfp(off - 0.05, 1), kfp(off, 0.15), kfp(off + 0.01, 0)])
attack["animators"][groups[CAM]["uuid"]] = {"name": CAM, "type": "bone", "keyframes": [
    {"channel": "scale", "data_points": [{"x": "1", "y": "1", "z": "1"}], "time": 0, "interpolation": "linear"},
    {"channel": "scale", "data_points": [{"x": "0.5", "y": "0.5", "z": "0.5"}], "time": T_CRACK, "interpolation": "linear"},
    {"channel": "scale", "data_points": [{"x": "1.2", "y": "1.2", "z": "1.2"}], "time": T_CRACK + 0.035, "interpolation": "linear"},
    {"channel": "scale", "data_points": [{"x": "0.7", "y": "0.7", "z": "0.7"}], "time": T_CRACK + 0.1, "interpolation": "linear"}]}

# event_equip : le fouet arrive enroulé et se déroule de la racine à la mèche (1,1 s) ; un son de cuir.
LEQ = 1.1


def equip_vals(t):
    out = {fouet: (0, 0, 0)}
    for j, g in enumerate(SEGS + [meche]):
        u = j / (NC - 1)
        out[g] = (0, 0, 24 * (1 - sm(t, 0.1 + 0.6 * u, 0.4 + 0.6 * u)))
    return out


equip = anim_from("event_equip", LEQ, equip_vals, 30, loop="once")
equip["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
    {"channel": "sound", "data_points": [{"effect": "item.armor.equip_leather", "file": ""}], "time": 0.05}]}
ANIMS.append(equip)


def bone_node(name):
    g = groups[name]
    return {"name": g.get("nom", name), "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone_node(bras)]
assert 60 <= len(elements) <= 140, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model, attaque=True)   # arme : le claquement reste
from reactions import retirer_reactions
retirer_reactions(model, garder=("attack",))
from ambiance import ajouter_ambiance
ajouter_ambiance(model)
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(model["animations"]), "anims ;",
      sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
