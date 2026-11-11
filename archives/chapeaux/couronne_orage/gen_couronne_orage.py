"""Couronne d'orage : un cercle de métal d'orage autour du haut du crâne, d'où montent huit pointes en éclair (zigzag en vrai volume,
bout de cristal d'orage), un tambour du tonnerre au front (disque à trois virgules tomoe d'or), et des arcs électriques qui sautent
d'une pointe à l'autre, au hasard. Design original (ensemble Orage, .claude/styles/orage.md), assorti à ailes_orage et aura_orage.
Écrit couronne_orage.png, couronne_orage_e.png et .build/couronne_orage_brut.bbmodel à côté de ce script.

Placement : tout dans head. Seconde couche du skin à 4,5 px : le cercle a sa face intérieure à 4,68 px (y 30–31,6), les pointes
leur face intérieure à 4,78 px ; le tambour est posé 0,12 px devant le cercle, rien d'autre devant le visage.
Volumes : cercle de quatre côtés (bouts cachés sans face), pointes de trois tronçons pleins inclinés en zigzag (épaisseurs
différentes : aucune face parallèle commune), dernier tronçon en cristal trans_ (alpha 170–215, visible avec shader) ; tambour
= disque découpé + âme octogonale. Texture HD (32 texels/px sur le cercle).

Fonctions avancées (guide 4 bis, 5 ter, 6.3, 6.4) :
- arcs : 7 groupes cam_ entre deux pointes voisines (au-dessus du front, des tempes et de la nuque, y ≥ 33,2), deux formes
  d'éclair horizontales en add_ + double trans_ blanc bleuté ; flash de 0,13 s tiré au hasard (recette Molang de familiers.md,
  hachage sinus, q.instance_seed), une décharge toutes les 1,5 à 3 s au repos, plus en course, aucune en sommeil ; le mod
  oriente lui-même les cam_ dans le menu Apparence (guide du 2026-11-06 soir) : rien n'y est caché ;
- calque _e : bouts de cristal (150–205) et filet du zigzag gravé (sources nettes) ; ctrl_lumiere qui s'avive aux décharges ;
- particle_etincelle / emit_etincelle (4 points aux plus hautes pointes, ctrl_emit −1 sauf pendant un arc) : étincelles qui montent ;
- event_equip (1,6 s) : un éclair tombe sur la tête (camy_), le cercle se forme et les pointes poussent en cascade depuis le front ;
  un son (block.copper_bulb.turn_on) ; event_unequip (1,2 s) : les pointes rentrent, fin à l'échelle 0.
États utiles seulement (pièce de tête) : idle, walk, run, sneak, sleep (les autres retombent sur idle, guide 6.2) ; attack et hurt
sont retirés à l'écriture (retirer_reactions : pas de réaction sur une pièce portée).
À juger en jeu : additif réel, trans_ avec shader, hasard des arcs, ctrl_*, particules, _e de nuit.
Contrôle : FLASH=1 (ou A, B) force les arcs visibles (.build/couronne_orage_flash.bbmodel, jamais livré).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

NOM = "couronne_orage"
TEX = 512
SS = 4
FLASH = os.environ.get("FLASH", "")
TAU = 2 * math.pi


def lerp(a, b, k):
    return a + (b - a) * k


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


METAL = np.array([(22, 24, 36), (46, 52, 72), (70, 78, 104), (112, 122, 154), (170, 182, 214)], np.float32)
OR = np.array([(130, 90, 30), (176, 128, 44), (220, 170, 60), (255, 230, 140)], np.float32)


def grille01(W, H):
    yy, xx = np.mgrid[0:H * SS, 0:W * SS]
    return (xx + 0.5) / (W * SS), (yy + 0.5) / (H * SS)


def reduire(col, W, H, mask=None):
    im = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = im
    out[..., 3] = 255 if mask is None else (np.array(Image.fromarray(mask.astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110) * 255
    return out


def bande(W=340, H=52):
    """Face du cercle : métal d'orage bombé, liserés d'or haut et bas, gorges sombres, zigzag d'éclair gravé clair au milieu."""
    x, y = grille01(W, H)
    v = 2.6 - 2.2 * np.abs(y - 0.5) * 2 + 0.25 * (y < 0.5)
    col = METAL[np.clip(v.astype(int), 0, 4)]
    gold = (y < 0.09) | (y > 0.91)
    col = np.where(gold[..., None], lerp(OR[1], OR[3], np.clip(1 - np.abs(y - 0.5) * 2 + 0.6, 0, 1)[..., None] * 0.6), col)
    groove = ((y > 0.09) & (y < 0.15)) | ((y > 0.85) & (y < 0.91))
    col = np.where(groove[..., None], METAL[0], col)
    zz = 0.5 + 0.22 * (2 * np.abs(2 * (x * 14 - np.floor(x * 14 + 0.5))) - 1)
    zig = np.abs(y - zz) < 0.045
    col = np.where(zig[..., None], np.array((200, 214, 250), np.float32), col)
    out = reduire(col, W, H)
    e = np.zeros_like(out)
    zl = np.array(Image.fromarray((zig * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    e[zl, :3] = (120, 150, 230)
    e[zl, 3] = 255
    return out, e


def metal_long(W=32, H=96):
    """Tronçon de pointe : u en travers (arête claire au milieu), v le long."""
    x, y = grille01(W, H)
    q = np.abs(x - 0.5) * 2
    v = 3.3 * (1 - q ** 1.3) + 0.8 * (q < 0.14)
    col = METAL[np.clip(v.astype(int), 0, 4)]
    col = np.where((y > 0.9)[..., None], lerp(OR[1], OR[2], 1 - q[..., None]), col)    # bague d'or au pied
    return reduire(col, W, H)


CRIS = np.array([(40, 40, 120), (70, 90, 200), (130, 160, 255), (190, 208, 255), (232, 240, 255)], np.float32)


def cristal(W=32, H=64):
    x, y = grille01(W, H)
    q = np.abs(x - 0.5) * 2
    v = 1.0 + 2.6 * (1 - y) + 0.6 * (x < 0.5) - 0.8 * q
    col = CRIS[np.clip(v.astype(int), 0, 4)]
    tri_ = q < y * 1.02 + 0.03                                     # pointe : triangle, pointe en haut (v = 0), base en bas
    edge = (q > y * 1.02 - 0.14) | (q < 0.07)
    col = np.where(edge[..., None], CRIS[4], col)
    a = np.where(tri_, np.clip(170 + 40 * (1 - y) + 30 * edge, 170, 215), 0)
    im = np.array(Image.fromarray(col.astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = im
    out[..., 3] = np.array(Image.fromarray(a.astype(np.uint8), "L").resize((W, H), Image.BOX))
    e = np.zeros_like(out)
    ev = lerp(np.array((90, 110, 200)), np.array((160, 190, 255)), (1 - (np.arange(H) + 0.5) / H)[:, None, None])
    e[..., :3] = np.broadcast_to(ev, (H, W, 3)).astype(np.uint8)
    e[..., 3] = 255
    e[out[..., 3] == 0] = 0
    out[out[..., 3] == 0, :3] = 0
    return out, e


def medaillon(N=96):
    x, y = grille01(N, N)
    x, y = x * 2 - 1, 1 - y * 2
    r = np.hypot(x, y)
    disc, rim = r < 0.97, (r > 0.80) & (r < 0.97)
    tom = np.zeros(x.shape, bool)
    for k in range(3):
        a0 = math.radians(90 + 120 * k)
        tom |= np.hypot(x - 0.30 * math.cos(a0), y - 0.30 * math.sin(a0)) < 0.19
        for j in range(1, 16):
            aj, rj = a0 + math.radians(9 * j), 0.30 + 0.018 * j
            tom |= np.hypot(x - rj * math.cos(aj), y - rj * math.sin(aj)) < 0.19 * (1 - j / 16.5)
    dot = np.zeros(x.shape, bool)
    for k in range(12):
        ak = math.radians(15 + 30 * k)
        dot |= np.hypot(x - 0.885 * math.cos(ak), y - 0.885 * math.sin(ak)) < 0.035
    shade = np.clip(0.5 + 0.35 * y - 0.25 * r, 0, 1)[..., None]
    col = lerp(METAL[1], METAL[3], shade)
    col = np.where(((r < 0.80) & (r > 0.74))[..., None], METAL[0], col)
    col = np.where(rim[..., None], lerp(OR[1], OR[3], shade), col)
    col = np.where(dot[..., None], METAL[0], col)
    col = np.where(tom[..., None], lerp(OR[0], OR[3], np.clip(shade + 0.1, 0, 1)), col)
    return reduire(col, N, N, disc)


WHITE, BLUE, VIOLET = np.array((250, 250, 240), np.float32), np.array((150, 210, 255), np.float32), np.array((120, 80, 255), np.float32)


def _segd(X, Y, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = max(vx * vx + vy * vy, 1e-9)
    t = np.clip(((X - a[0]) * vx + (Y - a[1]) * vy) / L2, 0, 1)
    return np.hypot(X - a[0] - t * vx, Y - a[1] - t * vy)


def bolt(seed, W, H, n=5, w0=4.2, w1=2.8, ss=4):
    """Même éclair que les ailes d'orage : (tuile add_, tuile trans_), racine en haut au centre."""
    r = np.random.default_rng(seed)
    pts = [(0.5, 0.0)]
    side = 1 if r.random() < 0.5 else -1
    for i in range(1, n):
        pts.append((float(np.clip(0.5 + side * r.uniform(0.12, 0.26), 0.18, 0.82)), i / n + float(r.uniform(-0.04, 0.04))))
        side = -side
    pts.append((0.5 + float(r.uniform(-0.06, 0.06)), 1.0))
    chans = [(pts, w0, w1)]
    for i in r.choice(np.arange(1, n - 1), size=2, replace=False):
        bx, by = pts[int(i)]
        d = 1 if bx >= 0.5 else -1
        br = [(bx, by), (float(np.clip(bx + d * r.uniform(0.10, 0.16), 0.06, 0.94)), by + float(r.uniform(0.08, 0.12)))]
        br.append((float(np.clip(br[-1][0] - d * r.uniform(0.02, 0.06), 0.06, 0.94)), br[-1][1] + float(r.uniform(0.06, 0.10))))
        chans.append((br, w0 * 0.36, w0 * 0.2))
    yy, xx = np.mgrid[0:H * ss, 0:W * ss]
    X, Y = (xx + 0.5) / ss, (yy + 0.5) / ss
    best = np.full(X.shape, 1e9)
    for P, wa, wb in chans:
        for j in range(len(P) - 1):
            ww = lerp(wa, wb, j / max(1, len(P) - 2))
            best = np.minimum(best, _segd(X, Y, (P[j][0] * W, P[j][1] * H), (P[j + 1][0] * W, P[j + 1][1] * H)) / ww)
    core = np.clip((0.34 - best) / 0.12, 0, 1)
    g1, g2 = np.exp(-(best / 1.45) ** 2), np.exp(-(best / 2.8) ** 2)
    rgb = np.maximum.reduce([VIOLET * 0.62 * g2[..., None], BLUE * 0.92 * g1[..., None], WHITE * core[..., None]])
    im = np.array(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    add = np.zeros((H, W, 4), np.uint8)
    lum = im.max(axis=2)
    add[..., :3] = np.where((lum > 16)[..., None], im, 0)
    add[..., 3] = (lum > 16) * 255
    fa = np.array(Image.fromarray(np.where(best < 0.45, 180, np.where(best < 1.25, 120, 0)).astype(np.uint8), "L").resize((W, H), Image.BOX)).astype(np.float32)
    cc = np.array(Image.fromarray(((best < 0.45) * 255).astype(np.uint8), "L").resize((W, H), Image.BOX)).astype(np.float32) / 255
    tr = np.zeros((H, W, 4), np.uint8)
    tr[..., :3] = lerp(np.array((150, 185, 255), np.float32), np.array((236, 242, 255), np.float32), cc[..., None]).astype(np.uint8)
    al = np.where(fa >= 30, np.clip(fa, 120, 180), 0)
    tr[..., 3] = al.astype(np.uint8)
    tr[al == 0, :3] = 0
    return add, tr


def etincelle(N=16):
    x, y = grille01(N, N)
    x, y = x * 2 - 1, y * 2 - 1
    d = np.abs(x) ** 0.5 + np.abs(y) ** 0.5
    m = np.array(Image.fromarray(((d < 0.95) * 255).astype(np.uint8), "L").resize((N, N), Image.LANCZOS)) > 110
    c = np.array(Image.fromarray(((d < 0.55) * 255).astype(np.uint8), "L").resize((N, N), Image.LANCZOS)) > 110
    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = (150, 200, 255)
    out[c, :3] = (245, 248, 255)
    out[..., 3] = m * 255
    return out


UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)


def poser(nom, im, x, y, em=None):
    h, w = im.shape[:2]
    assert x + w <= TEX and y + h <= TEX and not tex[y:y + h, x:x + w, 3].any(), nom
    tex[y:y + h, x:x + w] = im
    if em is not None:
        tex_e[y:y + h, x:x + w] = em
    UV[nom] = (x, y, x + w, y + h)


b_, be_ = bande()
poser("bande", b_, 0, 0, be_)
poser("metal", metal_long(), 341, 0)
c_, ce_ = cristal()
poser("cristal", c_, 374, 0, ce_)
poser("medal", medaillon(), 407, 0)
poser("spark", etincelle(), 341, 97)
for i, sd in enumerate((31, 47, 83)):
    a_, t_ = bolt(sd, 64, 112)
    poser(f"boltV{i}", a_, 64 * i, 120)                      # vertical : éclair de l'apparition
    poser(f"boltVT{i}", t_, 192 + 64 * i, 120)
    a_, t_ = bolt(sd + 100, 48, 112)
    poser(f"boltH{i}", np.ascontiguousarray(np.transpose(a_, (1, 0, 2))), 112 * i, 240)     # horizontal : arcs
    poser(f"boltHT{i}", np.ascontiguousarray(np.transpose(t_, (1, 0, 2))), 112 * i, 290)
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
for n in UV:
    if not (n.startswith("boltVT") or n.startswith("boltHT") or n == "cristal"):
        u0, v0, u1, v1 = UV[n]
        assert set(np.unique(tex[v0:v1, u0:u1, 3])) <= {0, 255}, n
_b64 = []
for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
    im_ = Image.fromarray(arr, "RGBA")
    im_.save(fn, optimize=True)
    _buf = io.BytesIO()
    im_.save(_buf, "PNG", optimize=True)
    _b64.append("data:image/png;base64," + base64.b64encode(_buf.getvalue()).decode())


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


def cube(g, nom, a, b, origin, faces, rot=None):
    e = {"name": nom, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in a], "to": [round(float(v), 3) for v in b],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False, "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if rot is not None and any(rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    g.enfants.append(e["uuid"])


def uvr(n, fu=False, fv=False, part=None):
    u0, v0, u1, v1 = UV[n]
    if part:                                   # sous-bande (fractions de u et v)
        a, b, c, d = part
        u0, u1, v0, v1 = u0 + (u1 - u0) * a, u0 + (u1 - u0) * b, v0 + (v1 - v0) * c, v0 + (v1 - v0) * d
    return [u1 if fu else u0, v1 if fv else v0, u0 if fu else u1, v0 if fv else v1]


HEAD = G("head", (0, 24, 0))
COUR = G("couronne", (0, 31, 0), HEAD)
ALL = COUR
G("ctrl_lumiere", (0, 31, 0), COUR)
RI, RO, Y0, Y1 = 4.68, 5.32, 30.0, 31.6
BANDE = G("bande", (0, Y0, 0), COUR)
faceB = uvr("bande")
haut = uvr("bande", part=(0, 1, 0.2, 0.32))
# avant et arrière (x de -RI à RI, bouts cachés sans face), côtés (z de -RO à RO)
cube(BANDE, "bande_av", (-RI + 0.02, Y0, -RO), (RI - 0.02, Y1, -RI), (0, Y0, 0), {"north": faceB, "south": faceB, "up": haut, "down": haut})
cube(BANDE, "bande_ar", (-RI + 0.02, Y0, RI), (RI - 0.02, Y1, RO), (0, Y0, 0), {"north": faceB, "south": faceB, "up": haut, "down": haut})
cube(BANDE, "bande_d", (RI, Y0, -RO), (RO, Y1, RO), (0, Y0, 0), {"east": faceB, "west": faceB, "up": haut, "down": haut, "north": uvr("metal", part=(0, 1, 0, 0.3)), "south": uvr("metal", part=(0, 1, 0, 0.3))})
cube(BANDE, "bande_g", (-RO, Y0, -RO), (-RI, Y1, RO), (0, Y0, 0), {"east": faceB, "west": faceB, "up": haut, "down": haut, "north": uvr("metal", part=(0, 1, 0, 0.3)), "south": uvr("metal", part=(0, 1, 0, 0.3))})
# tambour du tonnerre au front : disque découpé (face nord), âme octogonale cachée dans son épaisseur
MED = G("tambour", (0, 31.2, -5.7), COUR)
MR, MZ0, MZ1 = 1.7, -6.02, -5.44
cube(MED, "tambour", (-MR, 31.2 - MR, MZ0), (MR, 31.2 + MR, MZ1), (0, 31.2, -5.7), {"north": uvr("medal"), "south": uvr("medal", fu=True)})
for j, rz in enumerate((0, 45)):
    rr = MR * 0.68 * (1 if j == 0 else 0.985)
    m_ = uvr("metal", part=(0, 1, 0.3, 0.6))
    cube(MED, f"tambour_k{j}", (-rr, 31.2 - rr, MZ0 + 0.06), (rr, 31.2 + rr, MZ1 - 0.06), (0, 31.2, -5.7), {"up": m_, "down": m_, "east": m_, "west": m_}, rot=(0, 0, rz))

# pointes en éclair : (nom, x, z, axe tangent, hauteur, sens du zigzag)
POINTES = [("av_d", 2.9, -5.0, "x", 4.4, 1), ("av_g", -2.9, -5.0, "x", 4.4, -1),
           ("cd_av", 5.0, -1.7, "z", 5.4, -1), ("cd_ar", 5.0, 2.3, "z", 3.9, 1),
           ("cg_av", -5.0, -1.7, "z", 5.4, 1), ("cg_ar", -5.0, 2.3, "z", 3.9, -1),
           ("ar_d", 2.4, 5.0, "x", 3.6, -1), ("ar_g", -2.4, 5.0, "x", 3.6, 1)]
PT, TIPS, EMITS, LEVEE = {}, {}, [], []
ZIG = [(0.0, 0.0), (0.9, 0.42), (-0.55, 0.58), (0.2, 1.0)]
SECT = [(0.95, 0.44), (0.80, 0.64), (1.3, 0.3)]          # largeur tangente, épaisseur radiale (0,1 px d'écart entre tronçons voisins)
for nom, x, z, ax, H, sg in POINTES:
    base = (x, Y1 - 0.15, z)
    g = G(f"pointe_{nom}", base, COUR)
    PT[nom] = g
    LEVEE.append(g)
    pts = [(sg * u, v * H) for u, v in ZIG]
    tg = G(f"trans_pointe_{nom}", base, g)
    for i in range(3):
        (u0, v0), (u1, v1) = pts[i], pts[i + 1]
        L = math.hypot(u1 - u0, v1 - v0) + SECT[i][0] * 0.5
        ang = math.degrees(math.atan2(u1 - u0, v1 - v0))                  # inclinaison depuis la verticale, vers +u
        um, vm = (u0 + u1) / 2, (v0 + v1) / 2
        w, th = SECT[i]
        if ax == "x":
            c = (x + um, base[1] + vm, z)
            a, b = (c[0] - w / 2, c[1] - L / 2, z - th / 2), (c[0] + w / 2, c[1] + L / 2, z + th / 2)
            rot = (0, 0, -ang)
            big, small = ("north", "south"), ("east", "west")
        else:
            c = (x, base[1] + vm, z + um)
            a, b = (x - th / 2, c[1] - L / 2, c[2] - w / 2), (x + th / 2, c[1] + L / 2, c[2] + w / 2)
            rot = (ang, 0, 0)
            big, small = ("east", "west"), ("north", "south")
        if i < 2:
            m_ = uvr("metal", part=(0, 1, 0, 0.6 + 0.4 * (i == 0)))
            cube(g, f"p_{nom}{i}", a, b, c, {**{f: m_ for f in big + small}, "up": uvr("metal", part=(0, 1, 0, 0.1))}, rot=rot)
        else:
            # pointe de cristal : deux plaques croisées (tangente et radiale), triangle découpé par alpha, base dans le tronçon
            cr = uvr("cristal")
            L2 = L + 0.2
            c2 = (c[0], c[1] + 0.45, c[2])
            if ax == "x":
                cube(tg, f"p_{nom}{i}", (c[0] - w / 2, c2[1] - L2 / 2, z - 0.15), (c[0] + w / 2, c2[1] + L2 / 2, z + 0.15), c, {"north": cr, "south": cr}, rot=rot)
                cube(tg, f"p_{nom}{i}r", (c[0] - 0.15, c2[1] - L2 / 2, z - w * 0.4), (c[0] + 0.15, c2[1] + L2 / 2, z + w * 0.4), c, {"east": cr, "west": cr}, rot=rot)
            else:
                cube(tg, f"p_{nom}{i}", (x - 0.15, c2[1] - L2 / 2, c[2] - w / 2), (x + 0.15, c2[1] + L2 / 2, c[2] + w / 2), c, {"east": cr, "west": cr}, rot=rot)
                cube(tg, f"p_{nom}{i}r", (x - w * 0.4, c2[1] - L2 / 2, c[2] - 0.15), (x + w * 0.4, c2[1] + L2 / 2, c[2] + 0.15), c, {"north": cr, "south": cr}, rot=rot)
    tip = pts[-1]
    TIPS[nom] = (x + tip[0], base[1] + tip[1], z) if ax == "x" else (x, base[1] + tip[1], z + tip[0])
    if H > 4.2:
        e = G("emit_etincelle" + (str(len(EMITS) + 1) if EMITS else ""), TIPS[nom], g)
        G("ctrl_emit", TIPS[nom], e)
        EMITS.append((e, 0.41 + 3.17 * len(EMITS)))

# arcs entre pointes voisines (y ≥ 33,2 : au-dessus du front)
VOISINS = [("av_g", "av_d"), ("av_d", "cd_av"), ("cd_av", "cd_ar"), ("cd_ar", "ar_d"), ("ar_d", "ar_g"), ("ar_g", "cg_ar"), ("cg_ar", "cg_av"), ("cg_av", "av_g")]
VOISINS = [v for v in VOISINS if v != ("ar_d", "ar_g")]        # nuque : pas d'arc (caché par la tête)
ARCS = []
ARC_GRP = G("arcs", (0, 34, 0), COUR)
for i, (a, b) in enumerate(VOISINS):
    pa, pb = np.array(PT[a].origin), np.array(PT[b].origin)
    ha, hb = TIPS[a][1] - Y1, TIPS[b][1] - Y1
    mid = (pa + pb) / 2
    yc = Y1 + 0.62 * min(ha, hb) + 0.4
    rad = math.hypot(mid[0], mid[2])
    p = (mid[0] * (rad + 0.6) / rad, max(yc, 34.2), mid[2] * (rad + 0.6) / rad)      # hors des plans des pointes
    w = float(np.hypot(*(pa - pb)[[0, 2]])) * 0.95
    cam = G(f"cam_arc{i + 1}", p, ARC_GRP)
    forms = []
    for j, dz in enumerate((0.0, 0.45)):
        fg = G(f"arc{i + 1}{'ab'[j]}", p, cam)
        G("ctrl_alpha", p, fg)
        ga, gt = G(f"add_arc{i + 1}{'ab'[j]}", p, fg), G(f"trans_arc{i + 1}{'ab'[j]}", p, fg)
        ti = (i + j) % 3
        cube(ga, f"arc{i + 1}{'ab'[j]}", (p[0] - w / 2, p[1] - 1.1, p[2] + dz - 0.15), (p[0] + w / 2, p[1] + 1.1, p[2] + dz + 0.15), p, {"south": uvr(f"boltH{ti}", fv=j == 1)})
        cube(gt, f"arc{i + 1}{'ab'[j]}t", (p[0] - w / 2, p[1] - 1.12, p[2] + dz - 1.05), (p[0] + w / 2, p[1] + 1.12, p[2] + dz - 0.75), p, {"south": uvr(f"boltHT{ti}", fv=j == 1)})
        forms.append(fg)
    ARCS.append((forms[0], forms[1], 0.41 + 3.17 * i))

# éclair de l'apparition : camy_ au-dessus de la tête, du ciel jusqu'au sommet du crâne ; caché dans les états
FC = (0, 42, 0)
FOUDRE = G("foudre", FC, HEAD)
CAMY = G("camy_foudre", FC, FOUDRE)
CA_F = G("ctrl_alpha", FC, CAMY)
FA, FT = G("add_foudre", FC, CAMY), G("trans_foudre", FC, CAMY)
for j in range(2):
    y1 = 53.0 - 10.0 * j                          # bas de l'éclair à y = 33, au-dessus de la seconde couche
    cube(FA, f"foudre{j}", (-2.6, y1 - 10, -0.15), (2.6, y1, 0.15), FC, {"south": uvr(f"boltV{j}", fu=j == 1)})
    cube(FT, f"foudre{j}t", (-2.65, y1 - 10.1, -1.05 - 0.3 * j), (2.65, y1 + 0.1, -0.75 - 0.3 * j), FC, {"south": uvr(f"boltVT{j}", fu=j == 1)})

PART = G("particle_etincelle", (0, 0, 0))
cube(PART, "etincelle", (-0.25, 0.3, -0.15), (0.25, 0.8, 0.15), (0, 0.55, 0), {"south": uvr("spark")})
outliner = [HEAD.json(), PART.json()]


# ------------------------------------------------------------------ animations
def s(v):
    return v if isinstance(v, str) else str(round(v + 0.0, 4))


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": s(x), "y": s(y), "z": s(z)}], "time": round(t, 4), "interpolation": "linear"}


def piste(A, g, keys):
    A.setdefault(g.uuid, {"name": g.nom, "type": "bone", "keyframes": []})["keyframes"] += keys


def vis(P, p, c, w0, w1):
    if FLASH:
        return "1" if FLASH == "1" or (FLASH == "A") == (w0 == 0) else "0"
    x = f"(q.life_time/{P:g}+q.instance_seed*17+{c:.3g})"
    k = f"math.mod(math.abs(math.sin(math.floor({x})*127.1))*437.585,1)"
    w = f"(math.mod({x},1)-0.05-{k}*{0.8 / p:.3g})"
    return f"({k}<{p:g})*({w}>{w0 / P:.3g})*({w}<{w1 / P:.3g})"


def etat(nom, L, rate, pulse=0.03):
    A = {}
    P, p = rate
    for fa, fb, c in ARCS:
        for j, fg in enumerate((fa, fb)):
            w0, w1 = ((0.0, 0.06), (0.06, 0.13))[j]
            e = "-1" if p == 0 else f"{vis(P, p, c, w0, w1)}-1"
            assert len(e) <= 512
            piste(A, fg.enfants[0], [kf("position", 0, e, 0, 0)])
    for g, c in EMITS:
        piste(A, g.enfants[0], [kf("position", 0, "-1" if p == 0 else f"8*{vis(P, p, c, 0.0, 0.22)}-1", 0, 0)])
    piste(A, CA_F, [kf("position", 0, -1, 0, 0)])
    c0 = ARCS[0][2]
    piste(A, COUR.enfants[0], [kf("position", 0, "-0.4" if p == 0 else f"1.2*{vis(P, p, c0, 0.0, 0.2)}-0.4", 0, 0)])
    for i, g in enumerate(LEVEE):                      # bouts de cristal qui respirent (pas de rotation : la tête reste nette)
        sc = f"1+{s(pulse)}*math.sin(q.anim_time*{s(360 * 2 / L)}+{45 * i})"
        piste(A, g, [kf("scale", 0, 1, sc, 1)])
    return {"uuid": nuid(), "name": nom, "loop": "loop", "override": False, "length": L, "snapping": 24, "selected": nom == "idle", "animators": A}


STATES = [etat("idle", 8.0, (5.0, 0.4)), etat("walk", 1.6, (4.0, 0.45)), etat("run", 1.0, (2.5, 0.6)),
          etat("sneak", 4.0, (9.0, 0.25), 0.015), etat("sleep", 4.0, (1.0, 0.0), 0.01)]


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
    """Flash forcé par-dessus l'état : ctrl_alpha +1 pendant toute l'animation (0 à la fin), échelle de la forme à 0 hors des
    fenêtres (1 à la fin). Visible dans ses fenêtres seulement, en jeu comme dans l'aperçu de l'animation seule."""
    piste(A, fg.enfants[0], [kf("position", 0, 1, 0, 0), kf("position", L - 0.005, 1, 0, 0), kf("position", L, 0, 0, 0)])
    ks = creneaux("position", fen, L)
    piste(A, fg, [kf("scale", k["time"], *([float(k["data_points"][0]["x"])] * 3)) for k in ks[:-1]] + [kf("scale", L, 1, 1, 1)])


def cache(A, g, L):
    piste(A, g, [kf("position", 0, -1, 0, 0), kf("position", L - 0.005, -1, 0, 0), kf("position", L, 0, 0, 0)])


def ponctuel(nom, fenA, fenB, quels, emit_fen, f_sc):
    L = 0.8
    A = {}
    for i, (fa, fb, c) in enumerate(ARCS):
        if i in quels:
            apparition(A, fa, fenA, L)
            apparition(A, fb, fenB, L)
    cache(A, CA_F, L)
    if emit_fen:
        for g, c in EMITS:
            piste(A, g.enfants[0], creneaux("position", emit_fen, L, 8.0))
    T = [j * L / 16 for j in range(17)]
    for i, g in enumerate(LEVEE):
        piste(A, g, [kf("scale", t, 1, f_sc(t, i), 1) for t in T])
    return {"uuid": nuid(), "name": nom, "loop": "once", "override": False, "length": L, "snapping": 24, "selected": False, "animators": A}


attack = ponctuel("attack", [(0.05, 0.11), (0.28, 0.32)], [(0.11, 0.18)], range(len(ARCS)), [(0.05, 0.3)],
                  lambda t, i: 1 + 0.10 * bump(t, 0.0, 0.06, 0.2, 0.6))
hurt = ponctuel("hurt", [(0.04, 0.10)], [(0.10, 0.16)], (0, 3), None,
                lambda t, i: 1 - 0.08 * bump(t, 0.0, 0.05, 0.2, 0.6) + 0.03 * math.sin(TAU * t * 6 / 0.8) * (1 - sm(t, 0.1, 0.6)))


def event(nom, L, g_bande, g_pointe, foudre, son=None):
    T = [round(j * L / 32, 4) for j in range(33)]
    A = {}
    piste(A, CA_F, creneaux("position", foudre, L))
    piste(A, BANDE, [kf("scale", t, *([g_bande(t)] * 3)) for t in T])
    piste(A, MED, [kf("scale", t, *([g_bande(t)] * 3)) for t in T])
    for i, g in enumerate(LEVEE):
        piste(A, g, [kf("scale", t, *([g_pointe(t, i)] * 3)) for t in T])
    a = {"uuid": nuid(), "name": nom, "loop": "once", "override": False, "length": L, "snapping": 24, "selected": False, "animators": A}
    if son:
        a["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [
            {"channel": "sound", "data_points": [{"effect": son, "file": ""}], "time": 0.04}]}
    return a


ORDRE = {g.nom: k for k, g in enumerate(LEVEE)}       # avant d'abord, puis côtés, puis nuque
EQ = 1.6
equip = event("event_equip", EQ, lambda t: 1.0 if t >= EQ else 0.02 + 0.98 * sm(t, 0.15, 0.55),
              lambda t, i: 1.0 if t >= EQ else 0.02 + 0.98 * sm(t, 0.45 + 0.09 * i, 0.8 + 0.09 * i) + 0.05 * bump(t, 0.7 + 0.09 * i, 0.8 + 0.09 * i, 0.85 + 0.09 * i, 1.0 + 0.09 * i),
              [(0.04, 0.12), (0.15, 0.24)], "block.copper_bulb.turn_on")
UQ = 1.2
unequip = event("event_unequip", UQ, lambda t: 0.0 if t >= UQ - 1e-6 else 1 - sm(t, 0.7, 1.15),
                lambda t, i: 0.0 if t >= UQ - 1e-6 else 1 - sm(t, 0.05 * i, 0.4 + 0.05 * i), [(0.0, 0.08)])

PF = 0.4
p_fall = {"uuid": nuid(), "name": "particle_etincelle_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24, "selected": False,
          "animators": {PART.uuid: {"name": PART.nom, "type": "bone", "keyframes":
                        [kf("scale", t, *([1 + 0.35 * math.cos(TAU * t / PF)] * 3)) for t in [i * PF / 8 for i in range(9)]]}}}

ANIMS = STATES + [attack, hurt, equip, unequip, p_fall]
assert len(ANIMS) <= 16
assert 40 <= len(elements) <= 150, len(elements)
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner,
         "textures": [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": _b64[0]},
                      {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": _b64[1]}],
         "animations": ANIMS}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel" if not FLASH else f".build/{NOM}_flash.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


def ngroupes(n):
    return 1 + sum(ngroupes(c) for c in n.get("children", []) if isinstance(c, dict))


print(len(elements), "cubes ;", sum(ngroupes(n) for n in outliner), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;", len(EMITS), "emit_")
