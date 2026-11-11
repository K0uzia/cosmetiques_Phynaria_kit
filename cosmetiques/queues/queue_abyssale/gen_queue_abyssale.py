"""Queue abyssale v2 : queue-fouet de chasseur démoniaque, à porter avec ailes_abyssales et bandeau_abyssal. Design original.
Écrit queue_abyssale.png, queue_abyssale_e.png et .build/queue_abyssale_brut.bbmodel à côté de ce script.

Tube lisse et effilé (11 segments imbriqués, pivots aux jointures), veine vert acide unique sous toute la longueur,
3 anneaux de cuir cousu à clous d'os, fine lame en cœur allongé à tranchant vert. Modèle au repos droit vers +Z : tout le galbe vient des animations.

Remise aux règles du 2026-11-05 (.claude/references/procedures/remise-aux-regles.md) ; design, palette, proportions et animations d'état inchangés.
- Faces proches (« texture qui clipe ») : paires opaques à moins de 0,1 px mesurées par .build/mesure_noms.py (pose de base et
  poses). Les demi-tronçons d'un segment se touchent bout à bout (même groupe, jamais pliés) ; les segments sont tordus
  alternativement de +6° et -6° autour de leur axe (12° entre voisins : aucune face parallèle quand la queue plie,
  quel que soit l'angle), veine comprise ; aux jointures, un bouchon plus étroit à 0° ferme le coin qui s'ouvre au pli.
  Culots des tubes transparents (cachés par le collier et la lame), anneaux chanfreinés, clous tournés de 67,5°, veine noyée à
  0,12 px sous la peau et à 0,1 px au moins des flancs.
- Texture HD : une image de peau par segment (32 texels/px au lieu de 7), reflet satiné dans la longueur.
- Lumière : calque _e (veine et tranchant seulement) baissé à (34, 88, 22) : multiplié par tools/ambiance.py il donne
  (82, 211, 53), vert franc ; l'ancien (132, 255, 72) blanchissait une fois écrêté à 225.
- Apparition : event_equip (2 s) : la queue sort enroulée du bas du dos et se déroule de la base à la pointe ; pas de son.
- overlay_ambiance ajoutée par tools/ambiance.py (pluie, nuit).
Fonction phys_ (ressort) proposée par .claude/references/creatures/demons.md : pas ajoutée, jamais essayée dans le dépôt.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # True : embarque le calque _e en seconde texture. Réactivé le 2026-11-03 (correctif du mod annoncé, à vérifier en jeu).
NOM = "queue_abyssale"
TEX = 512
TAU = 2 * math.pi
V0, DV = 26, 5      # battement à la fusée (glide) : mêmes constantes que gen_ailes_abyssales.py, validées en jeu

# ------------------------------------------------------------------ matières (teintes d'ailes_abyssales et du cuir de bandeau_abyssal)
C_AURA = np.array((22, 66, 40), np.float32)
C_VEIN = np.array((96, 200, 44), np.float32)
C_VCORE = np.array((150, 244, 70), np.float32)
CUIR_BASE, CUIR_HIGH, CUIR_RIM, CUIR_OMBRE, COUTURE = [np.array(c, np.float32) for c in ((24, 12, 30), (60, 28, 72), (100, 56, 112), (8, 4, 11), (176, 156, 186))]


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


def paint_skin(W=96, H=32, s0=0.0, s1=1.0):
    """Peau tendue, lisse : charbon à reflet violacé dans le sens de la longueur, sans bague ni écaille. u = de la base à la pointe.
    s0, s1 : portion de la queue couverte par cette image (une image par segment, 32 texels/px)."""
    uu = np.linspace(s0, s1, W)[None, :, None]
    q = np.abs((np.arange(H) + 0.5) / H - 0.5)[:, None, None] * 2
    c = lerp(np.array((46, 24, 62), np.float32), np.array((22, 12, 30), np.float32), uu)        # plus noir vers la pointe
    c = np.broadcast_to(c, (H, W, 3)).copy()
    c = lerp(c, np.array((88, 48, 120), np.float32), np.clip(1 - q * 1.4, 0, 1) * lerp(0.42, 0.26, uu))
    r = np.random.default_rng(7)
    grain = np.array(Image.fromarray((r.random((3, 16)) * 255).astype(np.uint8), "L").resize((W, H), Image.BICUBIC), np.float32) / 255
    c = c * (0.96 + 0.08 * grain)[..., None]
    c = lerp(c, np.array((126, 84, 156), np.float32), np.exp(-((q - 0.18) / 0.07) ** 2) * 0.22)     # reflet satiné, fin
    return np.dstack([np.clip(c, 0, 255), np.full((H, W), 255.0)]).astype(np.uint8)


def paint_vein(W=96, H=16):
    q = np.abs((np.arange(H) + 0.5) / H - 0.5)[:, None, None] * 2
    c = np.where(q < 0.55, C_VCORE, C_VEIN) * np.ones((H, W, 3), np.float32)
    return np.dstack([c, np.full((H, W), 255.0)]).astype(np.uint8)


def paint_ring(W=64, H=32):
    """Cuir cousu : bords clairs, deux rangs de points de couture en travers. u = le long de la queue."""
    r = np.random.default_rng(3)
    blot = np.array(Image.fromarray((r.random((4, 6)) * 255).astype(np.uint8), "L").resize((W, H), Image.BICUBIC), np.float32) / 255
    c = lerp(CUIR_BASE, CUIR_HIGH, np.clip((blot - 0.3) * 2, 0, 1)[..., None] * 0.9)
    e = np.minimum(np.arange(W) + 0.5, W - np.arange(W) - 0.5)[None, :, None]
    c = lerp(c, CUIR_RIM, (e < 5) * 0.9)
    im = Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    for u_ in (12, W - 13):
        for k in range(4):
            y = int((k + 0.15) * H / 4)
            d.rectangle([u_ - 2, y, u_ + 2, y + int(H / 4 * 0.55)], fill=tuple(int(v) for v in COUTURE))
    return np.dstack([np.array(im), np.full((H, W), 255)]).astype(np.uint8)


def paint_nail(W=12):
    c = np.empty((W, W, 3), np.float32)
    c[...] = (214, 200, 206)
    yy, xx = np.mgrid[0:W, 0:W]
    e = np.minimum.reduce([xx, yy, W - 1 - xx, W - 1 - yy])
    c[e < 2] = (140, 120, 146)
    return np.dstack([c, np.full((W, W), 255.0)]).astype(np.uint8)


LENS = [3.4, 3.2, 3.0, 2.9, 2.7, 2.5, 2.3, 2.2, 2.0, 1.8, 1.5]   # longueurs des 11 segments (px)
E_COL = (34, 88, 22)    # calque _e : tools/ambiance.py le multiplie par 2,4 (plafond 225) -> (82, 211, 53), vert franc sans blanchir
BL, BW = 5.6, 2.7       # longueur, largeur de la lame (px)
KL, KH = 4.3, 1.5       # longueur, hauteur de la crête verticale (px)
BLADE_RES = (280, 140)  # 50 texels/px : un tranchant de 0,18 px y fait 9 texels


def blade_hw(t, W_):
    """Demi-largeur du cœur allongé au paramètre t (0 base, 1 pointe) : lobes ronds, pointe effilée, un peu concave."""
    t = np.asarray(t, np.float32)
    grow = np.clip(t / 0.2, 0, 1)
    grow = np.sqrt(1 - (1 - grow) ** 2)
    fall = (1 - np.clip((t - 0.2) / 0.8, 0, 1)) ** 1.35
    return W_ / 2 * grow * fall


def paint_blade(res, L_, W_, under=False, notch=True, ew=0.2):
    """Noir, reflet violacé près de l'arête centrale, tranchant vert. En dessous, la veine continue sur l'axe jusqu'à la pointe."""
    w, h = res
    ss = 4
    jj, ii = np.mgrid[0:h * ss, 0:w * ss]
    t = (ii + 0.5) / (w * ss)
    b = ((jj + 0.5) / (h * ss) - 0.5) * W_
    hw = blade_hw(t, W_)
    d = hw - np.abs(b)                       # distance au bord, en px
    in_ = d > 0
    if notch:
        in_ &= ~((np.abs(b) < 0.34 * (1 - t / 0.13)) & (t < 0.13))   # encoche du cœur, où entre la queue
    c = np.empty(t.shape + (3,), np.float32)
    c[...] = (15, 9, 20)
    k = np.clip(1 - np.abs(b) / (0.32 + 0.3 * hw), 0, 1)
    c = lerp(c, np.array((70, 40, 96), np.float32), (k ** 1.6 * 0.85)[..., None])
    c = lerp(c, C_AURA, (np.clip(1 - (d - ew) / 0.22, 0, 1) * (t > 0.1) * 0.9)[..., None])
    edge = (d < ew) & (t > 0.1)
    c[edge] = C_VEIN
    c[(d < ew / 2) & (t > 0.1)] = C_VCORE
    c[t > 0.86] = C_VCORE
    if under:
        c[(np.abs(b) < 0.12)] = C_VCORE
    rgb = np.array(Image.fromarray(c.astype(np.uint8), "RGB").resize((w, h), Image.LANCZOS))
    al = np.array(Image.fromarray((in_ * 255).astype(np.uint8), "L").resize((w, h), Image.LANCZOS)) > 110
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    out[~al, :3] = (15, 9, 20)
    ee = np.array(Image.fromarray(((edge | (t > 0.86)) * 255).astype(np.uint8), "L").resize((w, h), Image.LANCZOS)) > 127
    return out, np.dstack([ee[..., None] * np.array(E_COL), (ee & al) * 255]).astype(np.uint8)


def paint_braise(PT=48):
    """Éclat irrégulier : cœur vif, liseré sombre, une seule silhouette."""
    m = Image.new("L", (PT * 4, PT * 4), 0)
    shard = [(0.58, 0.02), (0.72, 0.30), (0.66, 0.42), (0.86, 0.60), (0.60, 0.98), (0.50, 0.70), (0.30, 0.80), (0.38, 0.46), (0.20, 0.34), (0.46, 0.26)]
    ImageDraw.Draw(m).polygon([(x * PT * 4, y * PT * 4) for x, y in shard], fill=255)
    f = np.array(m.filter(ImageFilter.GaussianBlur(PT * 0.2)), np.float32) / 255
    c = np.empty(f.shape + (3,), np.float32)
    c[...] = (28, 74, 30)
    c = lerp(c, np.array((120, 232, 52), np.float32), np.clip((f - 0.32) * 2.6, 0, 1)[..., None])
    c = lerp(c, np.array((206, 255, 118), np.float32), np.clip((f - 0.66) * 4.5, 0, 1)[..., None])
    i = np.array(Image.fromarray(c.astype(np.uint8), "RGB").resize((PT, PT), Image.LANCZOS))
    al = np.array(m.resize((PT, PT), Image.LANCZOS)) > 110
    out = np.dstack([i, al * 255]).astype(np.uint8)
    out[~al, :3] = i[al].mean(axis=0).astype(np.uint8)
    return out


UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def atlas():
    """Range les images en rangées et écrit les deux PNG. Le calque _e est écrit, il n'est embarqué que si AVEC_E."""
    lame, lame_e = paint_blade(BLADE_RES, BL, BW)
    lame_u, lame_ue = paint_blade(BLADE_RES, BL, BW, under=True)
    KRES = (int(KL * 50), int(KH * 50))
    crete, crete_e = paint_blade(KRES, KL, KH, notch=False, ew=0.09)
    vein = paint_vein()
    fixed = {"lame": lame, "lame_u": lame_u, "crete": crete, "vein": vein, "ring": paint_ring(), "nail": paint_nail(), "braise": paint_braise()}
    zz = np.concatenate([[0.0], np.cumsum(LENS)]) / sum(LENS)
    for i in range(len(LENS)):
        fixed[f"skin{i}"] = paint_skin(s0=zz[i], s1=zz[i + 1])
    glow = {"lame": lame_e, "lame_u": lame_ue, "crete": crete_e}
    x, y, shelf = 0, 0, 0
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, im in sorted(fixed.items(), key=lambda it: -it[1].shape[0]):
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, "atlas plein"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        if n in glow:
            tex_e[y:y + h, x:x + w] = glow[n]
        x += w + 1
        shelf = max(shelf, h)
    # calque _e : veine et tranchant seulement
    u0, v0, u1, v1 = UV["vein"]
    tex_e[v0:v1, u0:u1] = (*E_COL, 255)
    tex[TEX - 4:TEX - 2, TEX - 4:TEX - 2] = 0
    tex[..., :3] &= 0xFC
    assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
    out = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        out.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return out


TEX_B64, TEX_E_B64 = atlas()

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx, ordre du mod et du renderer."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if abs(R[2, 0]) > 0.99999:      # blocage de cardan (axe local X sur Z) : tout le roulis passe sur X
        return math.degrees(math.atan2(-R[0, 1] if R[2, 0] > 0 else R[0, 1], R[1, 1])), math.degrees(ry), 0.0
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def group(name, origin, parent=None):
    assert name not in groups
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


AX = V(0, 0, 1)                                    # axe de la queue au repos
Y_ = V(0, 1, 0)
Z_ = np.cross(AX, Y_)
R0 = np.column_stack([AX, Y_, Z_])                 # le X local suit la queue : u suit la longueur sur les 4 faces longues
_c = math.cos(math.pi / 4)
R45 = np.column_stack([AX, _c * Y_ + _c * Z_, -_c * Y_ + _c * Z_])   # un coin en bas, un coin en haut


def spans(tile, u0, u1, caps=(True, True)):
    """caps : culot de départ (west) et de bout (east) visibles, ou transparents."""
    bu0, bv0, bu1, bv1 = UV[tile]
    ua = lerp(bu0, bu1, u0)
    ub = max(lerp(bu0, bu1, u1), ua + 2)
    lg = [ua, bv0, ub, bv1]
    h = bv1 - bv0
    end = [ua, bv0 + h * 0.2, ua + 2, bv1 - h * 0.2]
    return {"south": lg, "north": lg, "up": lg, "down": lg, "east": end if caps[1] else CLEAR, "west": end if caps[0] else CLEAR}


def Rturn(deg):
    """Repère de la queue tourné de deg autour de son axe."""
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.column_stack([AX, c * Y_ + s_ * Z_, -s_ * Y_ + c * Z_])


def box(g, name, p, q, hy, hz, tile, u0=0.0, u1=1.0, R=R0, caps=(True, True)):
    """Pavé de p à q (points sur l'axe de la queue), demi-sections hy et hz. Tourne autour de son propre axe."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = q[2] - p[2]
    cube(g, name, p + (0, -hy, -hz), p + (L, hy, hz), p, euler(R), spans(tile, u0, u1, caps))


def tube(g, name, p, q, D, u0, u1, tile, turn=0.0, k=1.0):
    """Tronçon de section octogonale (deux pavés à 45°), culots transparents : les demi-tronçons d'un segment se touchent bout
    à bout. D = épaisseur ; k réduit la section (bouchon de jointure) ; turn la tourne autour de l'axe."""
    a = 0.45 * D * k
    box(g, name, p, q, a, a, tile, u0, u1, R=Rturn(turn), caps=(False, False))
    box(g, name + "o", p, q, a * 0.97, a * 0.97, tile, u0, u1, R=Rturn(45 + turn), caps=(False, False))


def vein_box(g, name, p, q, a, y_low, w, caps=(False, False), top=None, turn=0.0):
    """Veine sous la pointe basse : dessus noyé à 0,12 px sous le plat du tube (demi-côté a), dessous à 0,06 px sous la pointe
    basse y_low, côtés à 0,11 px au moins des flancs."""
    top, bot = (a - 0.12) if top is None else top, y_low + 0.06
    w = min(w, 2 * (a - 0.11))
    Rv = Rturn(turn)
    c = -Rv[:, 1] * (top + bot) / 2
    box(g, name, p + c, q + c, (bot - top) / 2, w / 2, "vein", 0.1, 0.9, caps=caps, R=Rv)


def plate(g, name, p, L_, W_, normal_y, tile_top, tile_bot, dy=0.0, th=0.3):
    """Plaque qui part de p le long de la queue. normal_y : plaque à plat, faces vers le haut et le bas ; sinon plaque debout."""
    p = np.asarray(p, float)
    t0, t1 = UV[tile_top], UV[tile_bot]
    if normal_y:
        X, Yp = AX, V(1, 0, 0)        # image : u vers la pointe, haut de l'image vers +X
    else:
        X, Yp = AX, Y_
    n = np.cross(X, Yp)
    R = np.column_stack([X, Yp, n])
    c = p + AX * (L_ / 2) + Y_ * dy
    cube(g, name, c - (L_ / 2, W_ / 2, th / 2), c + (L_ / 2, W_ / 2, th / 2), c, euler(R),
         {"south": list(t0), "north": [t1[2], t1[1], t1[0], t1[3]], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


# Queue : 11 segments, 27,5 px de tube + 5,6 px de lame hors recouvrement
N = len(LENS)
TUBE = sum(LENS)
P0 = V(0, 13.6, 2.6)      # pivot racine, juste au-dessus de la hanche. Marge de 0,5 px : au-dessous de y = 12,5, tout reste à z ≥ 2,5.
PTS = [P0]
for L_ in LENS:
    PTS.append(PTS[-1] + AX * L_)
GAP_J = 0.0
TW = [6.0 if i % 2 == 0 else -6.0 for i in range(len(LENS))]   # torsion alternée : 12° entre voisins, jamais de faces parallèles aux plis
VW = lambda j: min(max(0.3, lerp(0.5, 0.3, j / (N - 1))), 2 * (0.45 * D_at(PTS[j + 1][2]) - 0.11))   # largeur de la veine du segment j
RINGS = [(None, P0 - AX * 0.6 + AX * 0.02, 1.2), (3, PTS[3] - AX * 0.5, 1.0), (7, PTS[7] - AX * 0.4, 0.8)]
SEG, parent = [], None
for i in range(N):
    parent = group(f"tail{i}", PTS[i], parent=parent)
    SEG.append(parent)


def D_at(z):
    return lerp(1.6, 0.4, (float(np.clip((z - P0[2]) / TUBE, 0, 1))) ** 0.9)


for i in range(N):
    g, a_, b_ = SEG[i], PTS[i], PTS[i + 1]
    m_ = (a_ + b_) / 2
    # segments bout à bout ; torsion alternée de ±11,25° (TW)
    a2 = a_ + AX * (GAP_J / 2 if i else 0.0)
    b2 = b_ - AX * (GAP_J / 2 if i < N - 1 else 0.0)
    for j, (p, q) in enumerate(((a2, m_), (m_, b2))):
        zc = (p[2] + q[2]) / 2
        D = D_at(zc)
        tube(g, f"peau{i}_{j}", p, q, D, 0.5 * j, 0.5 * j + 0.5, f"skin{i}", turn=TW[i])
    if i < N - 1:   # bouchon de jointure : plus étroit, tourné de 22,5°, il ferme le coin qui s'ouvre quand le segment suivant plie
        tube(g, f"joint{i}", b_ - AX * 0.05, b_ + AX * 0.3, D_at(b_[2]), 0.9, 1.0, f"skin{i}", turn=0.0, k=0.78)
    # veine : une seule par segment, sur la pointe basse de la section, bout à bout avec la suivante
    D = D_at((a_[2] + b_[2]) / 2)
    w = max(0.3, lerp(0.5, 0.3, i / (N - 1)))
    # coupée sous les anneaux (la veine de l'anneau la recouvre) et sous la lame : pas de fond parallèle à leurs faces
    za, zb = a2[2], min(b2[2], PTS[-1][2] - 0.25)
    cuts = sorted((p_[2], p_[2] + L_) for idx, p_, L_ in RINGS if idx is not None)
    pieces, z0 = [], za
    for c0, c1 in cuts:
        if c1 <= z0 or c0 >= zb:
            continue
        if c0 > z0:
            pieces.append((z0, c0))
        z0 = max(z0, c1)
    if zb > z0:
        pieces.append((z0, zb))
    for k_, (z0, z1) in enumerate(pieces):
        if z1 - z0 > 0.05:
            vein_box(g, f"veine{i}" + "abc"[k_], V(0, P0[1], z0), V(0, P0[1], z1), 0.45 * D_at(b_[2]), 0.45 * D * 0.97 * math.sqrt(2), w, turn=TW[i])

# Anneaux de cuir cousu : collier fixe contre le dos, puis deux jointures. Clous d'os sur le dessus et les flancs ; la veine passe sur le cuir.
base = group("queue_base", P0)
for k, (idx, p, L_) in enumerate(RINGS):
    g = SEG[idx] if idx is not None else base
    q = p + AX * L_
    a = 0.45 * D_at(max(P0[2], p[2])) + 0.13        # 0,13 px au-dessus du plat le plus large qu'il recouvre
    box(g, f"anneau{k}", p, q, a, a, "ring")
    box(g, f"anneau{k}o", p + AX * 0.12, q - AX * 0.12, a * 0.97, a * 0.97, "ring", R=R45)   # chanfrein : culots à 0,12 px
    rp = a * 0.97 * math.sqrt(2)
    s = 0.16
    for tag, d_ in (("h", Y_), ("g", V(-1, 0, 0)), ("d", V(1, 0, 0))):
        c_ = p + AX * (L_ / 2) + d_ * (rp - 0.02)
        box(g, f"clou{k}{tag}", c_ - AX * s, c_ + AX * s, s, s, "nail", R=Rturn(67.5))
    if idx is not None:     # le collier reste au-dessus de la marge : la veine sort juste derrière lui
        a_in = 0.45 * D_at(p[2] + L_ / 2)
        w_in = min(max(0.3, lerp(0.5, 0.3, idx / (N - 1))), 2 * (a_in - 0.11))
        # plus étroite de 0,11 px par côté que la veine qu'elle prolonge, dessus 0,12 px sous le sien : jamais parallèles de près
        top_a = min(0.45 * D_at(PTS[j_][2]) - 0.12 for j_ in (idx, idx + 1)) - 0.12
        vein_box(g, f"veine_a{k}", p - AX * 0.12, q + AX * 0.12, a, rp, max(0.14, min(VW(idx - 1), VW(idx)) - 0.24), caps=(True, True), top=top_a)

# Lame : peau découpée à plat + âme pleine plus étroite + fine crête debout, pour qu'elle se lise aussi de profil
tip_g, TIP = SEG[-1], PTS[-1]
BS = TIP - AX * 0.25
plate(tip_g, "lame", BS, BL, BW, True, "lame", "lame_u")
plate(tip_g, "crete", BS + AX * 0.3, KL, KH, False, "crete", "crete", th=0.3)
for j, (t0, t1, hy, hz) in enumerate(((0.0, 0.3, 0.3, 0.42), (0.3, 0.55, 0.27, 0.33), (0.55, 0.75, 0.26, 0.27))):
    box(tip_g, f"ame{j}", BS + AX * BL * t0, BS + AX * BL * t1, hy, hz, f"skin{N - 1}", 0.9, 1.0, caps=(j == 0, True))

EMITS = []
for at in (BS + AX * BL * 0.98, BS + AX * BL * 0.45 + V(BW * 0.3, 0, 0), BS + AX * BL * 0.45 - V(BW * 0.3, 0, 0)):
    EMITS.append(group("emit_braise" + (str(len(EMITS) + 1) if EMITS else ""), at, parent=tip_g))


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


# Particule (guide, section 5 ter ; recette validée en jeu) : une plaque, face up seule, au-dessus du pivot.
PG = group("particle_braise", [0, 0, 0])
_w = 3.2
cube(PG, "braise", [-_w / 2, 0.3, -_w / 2], [_w / 2, 0.6, _w / 2], [0, 0, 0], (0, 0, 0), {"up": list(UV["braise"])})

outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "rotation": [0, 0, 0], "children": [bone_node(base), bone_node(SEG[0])]}, bone_node(PG)]


# ------------------------------------------------------------------ animations
# Intention, pour la queue qui part vers +Z : pitch > 0 relève la pointe, yaw > 0 la porte vers +X (droite du joueur).
# MIROIR D'AXES : seul endroit à toucher si la convention du mod change. Guide, section 3 : +X = le haut part vers l'arrière, donc ce qui pointe
# vers +Z descend ; +Y = le côté droit avance, donc ce qui pointe vers +Z part vers +X.
SX, SY = -1, +1


def mirror(pitch, yaw):
    return SX * pitch, SY * yaw, 0


def kf(t, x, y, z):
    return {"channel": "rotation", "data_points": [{"x": str(round(x + 0.0, 2)), "y": str(round(y + 0.0, 2)), "z": str(round(z + 0.0, 2))}],
            "time": round(t, 3), "interpolation": "linear"}


def anim(name, length, tracks, n_kf=None, loop="loop"):
    n = n_kf or max(8, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]
    A = {groups[g]["uuid"]: {"name": g, "type": "bone", "keyframes": [kf(t, *f(t)) for t in times]} for g, f in tracks.items()}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


SS = [i / (N - 1) for i in range(N)]            # position relative de chaque segment


def curve(*pts):
    """Courbe par points (s, degrés), lissée entre les points."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    def f(s):
        for a, b, u, v in zip(xs, xs[1:], ys, ys[1:]):
            if s <= b:
                return lerp(u, v, sm(s, a, b))
        return ys[-1]
    return f


def state(name, L, pitch, yaw_arc=None, ya=0.0, pa=0.0, k=1.0, cycles=1, n_kf=None):
    """Cap ABSOLU de chaque segment : courbe de pose + onde qui court de la base à la pointe. Les clés sont les différences entre segments voisins.
    La cascade vient de k : déphasage total, en cycles, entre la base et la pointe."""
    def head(i, t):
        s = SS[i]
        ph = TAU * (cycles * t / L - k * s)
        w = 0.3 + 0.7 * s
        return pitch(s) + pa * w * math.sin(ph + 1.2), (yaw_arc(s) if yaw_arc else 0.0) + ya * w * math.sin(ph)
    tr = {}
    for i, g in enumerate(SEG):
        def f(t, i=i):
            p1, y1 = head(i, t)
            p0, y0 = head(i - 1, t) if i else (0.0, 0.0)
            return mirror(p1 - p0, y1 - y0)
        tr[g] = f
    return anim(name, L, tr, n_kf=n_kf)


idle = state("idle", 8.0, curve((0, -30), (0.3, -16), (0.62, 10), (0.88, 26), (1, 12)), ya=22, pa=4, k=1.0, cycles=2, n_kf=56)
walk = state("walk", 1.6, curve((0, -6), (0.4, 0), (1, 14)), ya=15, pa=4, k=0.75)
run = state("run", 1.0, curve((0, 7), (0.3, 5), (1, 2)), ya=4.5, pa=2.5, k=0.9)
sneak = state("sneak", 3.0, curve((0, -44), (0.35, -40), (0.8, -24), (1, -14)), ya=6, pa=2, k=0.9, n_kf=24)
fly = state("fly", 2.4, curve((0, -18), (0.35, -46), (0.65, -44), (1, -26)), ya=10, pa=5, k=0.9, n_kf=20)
fall = state("fall", 1.5, curve((0, 26), (0.3, 20), (0.7, 34), (1, 44)), ya=7, pa=7, k=1.2)
swim = state("swim", 2.0, curve((0, -22), (0.4, -70), (1, -60)), ya=26, pa=3, k=1.0, n_kf=20)
mount = state("mount", 3.0, curve((0, -12), (0.35, -8), (0.7, 6), (1, 16)), curve((0, 0), (0.3, 10), (0.7, 36), (1, 58)), ya=2.2, pa=1.2, k=0.7)
sleep = state("sleep", 4.0, curve((0, -20), (0.45, -66), (1, -62)), curve((0, 0), (0.3, 12), (0.7, 40), (1, 62)), ya=1.2, pa=0.6, k=0.6)

# glide : joueur couché, la queue file dans le prolongement du torse et des jambes. Battement à la fusée : mêmes conditions qu'ailes_abyssales.
BOOST = f"math.clamp((math.max(q.ground_speed,q.vertical_speed)-{V0})/{DV},0,1)*math.clamp((q.vertical_speed+8)/4,0,1)"
G = 3.6
G_P = curve((0, -22), (0.4, -74), (1, -70))


def glide_anim():
    A = {}
    for i, g in enumerate(SEG):
        rel = G_P(SS[i]) - (G_P(SS[i - 1]) if i else 0.0)
        w = 0.5 + 0.8 * SS[i]
        ph = -34 * i
        x = f"{SX * rel:.2f}{SX * 0.7 * w:+.2f}*math.sin(q.anim_time*100{ph + 70:+d})"
        y = f"{SY * 2.6 * w:.2f}*math.sin(q.anim_time*100{ph:+d}){SY * 8.5 * w:+.2f}*{BOOST}*math.sin(q.anim_time*600{ph:+d})"
        assert max(len(x), len(y)) <= 256
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [{"channel": "rotation", "time": 0, "interpolation": "linear", "data_points": [{"x": x, "y": y, "z": "0"}]}]}
    return {"uuid": nuid(), "name": "glide", "loop": "loop", "override": False, "length": G, "snapping": 24, "selected": False, "animators": A}


glide = glide_anim()


# attack, hurt : une fois par-dessus l'état, seulement des différences entre segments, dernière image à zéro.
def impulse(name, cur, pitch_a, yaw_a, lag):
    tr = {}
    for i, g in enumerate(SEG):
        def f(t, i=i):
            v = cur(t - lag * i)
            return mirror(pitch_a(i) * v, yaw_a(i) * v)
        tr[g] = f
    return anim(name, 0.8, tr, n_kf=20, loop="once")


whip = lambda t: bump(t, 0.0, 0.07, 0.09, 0.2) - 0.75 * bump(t, 0.09, 0.17, 0.22, 0.52)
attack = impulse("attack", whip, lambda i: 1.5 + 0.35 * i, lambda i: 5 + 0.7 * i, 0.012)
sur = lambda t: bump(t, 0.0, 0.06, 0.14, 0.56) * (1 + 0.25 * math.sin(TAU * t * 6 / 0.8))
hurt = impulse("hurt", sur, lambda i: 4.5 + 0.2 * i, lambda i: 2.2 * math.sin(i * 1.4), 0.012)

def equip_anim():
    """event_equip (2 s, jouée par-dessus l'état) : la queue pousse du bas du dos (échelle 0,1 → 1 en 0,7 s, pointe relevée), puis
    un coup de fouet qui court de la base à la pointe et s'amortit. Dernière image : zéro. (Un enroulement a été essayé : la
    boucle montait dans la tête.)"""
    LE = 2.0
    times = [j * LE / 40 for j in range(41)]
    A = {}
    for i, g in enumerate(SEG):
        def f(t, i=i):
            s_ = SS[i]
            env = sm(t, 0.45, 0.75) * (1 - sm(t, 1.2, 1.95))
            rel = lambda tt: 16 * (0.3 + 0.7 * s_) * math.sin(TAU * (1.6 * tt - 0.9 * s_))
            yaw = env * (rel(t) - (16 * (0.3 + 0.7 * SS[i - 1]) * math.sin(TAU * (1.6 * t - 0.9 * SS[i - 1])) if i else 0.0))
            lift = 6 * (1 - sm(t, 0.3, 1.1)) * (1 if i else 0)
            return mirror(lift, yaw)
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(t, *f(t)) for t in times]}
    sc = lambda t: 0.1 + 0.9 * sm(t, 0.0, 0.7)
    for g in (SEG[0], base):
        keys = [{"channel": "scale", "data_points": [{"x": str(round(sc(t), 3)), "y": str(round(sc(t), 3)), "z": str(round(sc(t), 3))}],
                 "time": round(t, 3), "interpolation": "linear"} for t in times]
        A.setdefault(groups[g]["uuid"], {"name": g, "type": "bone", "keyframes": []})["keyframes"] += keys
    return {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": LE, "snapping": 24, "selected": False, "animators": A}


PF, PR = 3.0, 6.0
ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, attack, hurt, equip_anim(),
         anim("particle_braise_fall", PF, {PG: lambda t: (24 * math.sin(TAU * t / PF), 360 * t / PF, 18 * math.cos(2 * TAU * t / PF))}, n_kf=24),
         anim("particle_braise_rest", PR, {PG: lambda t: (0, 0, 1.2 * math.sin(TAU * t / PR))}, n_kf=12)]

assert 60 <= len(elements) <= 160, f"budget : {len(elements)} cubes"
assert 2 <= len(EMITS) <= 3
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": TEX_B64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": TEX_E_B64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
# Particules qui tombent et se posent : réservées aux ailes (.claude/rules/retours-en-jeu.md).
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from particules import retirer_particules
from sons import limiter_sons
from ambiance import ajouter_ambiance
retirer_particules(model)
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
ajouter_ambiance(model)
assert len(model["animations"]) <= 16
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;", len(EMITS), "emit_")
