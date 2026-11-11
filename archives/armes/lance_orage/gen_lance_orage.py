"""Lance d'orage : lance tenue à une main (right_arm), ensemble Orage (thème Éléments, .claude/styles/orage.md). Design original.
Écrit lance_orage.png, lance_orage_e.png et .build/lance_orage_brut.bbmodel à côté de ce script.

Repère (repris de lame_givre) : la lance vise -Z depuis la prise P0 sous le poing ; a = distance vers l'avant.
- Hampe de métal d'orage octogonale (deux cubes, l'un tourné de 45°), bagues d'or peintes ; gaine de cuir bleu nuit à bandes
  croisées et liserés d'or autour de la prise (rayon plus grand, bouts à 0,12 px des bouts de hampe) ; talon d'or.
- Anneau de tambour à trois virgules tomoe d'or (disque découpé perpendiculaire à la hampe, âme octogonale), collet d'or.
- Fer en cristal d'orage trans_ (alpha 170–215) : deux plaques croisées découpées en feuille coupée de deux crans en éclair, arêtes
  blanc bleuté, filet d'éclair en zigzag au milieu (seule source du calque _e, 120–205) ; âme opaque fine tournée de 45°.
`prise` porte la pose d'état, `coup` l'attaque et la blessure (jouées par-dessus).

Fonctions avancées (guide 4 bis, 5 ter, 6.3, 6.4, 6.5) :
- décharges : deux groupes cam_ sur le fer (deux formes d'éclair add_ + doubles trans_), flash de 0,13 s au hasard (recette Molang de
  familiers.md, hachage sinus, q.instance_seed), une toutes les 3 à 5 s au repos, plus en course (le mod oriente les cam_ dans le menu, guide 2026-11-06 soir : plus de cachette) ;
- attack (once 0,8 s) : armé (+25°), coupe (−40°) avec traînée en drapeau dans le plan du geste (add_ + double trans_ : tête claire
  et épaisse côté fer, queue fine qui s'efface d'abord : traînée entière 0,13–0,26 s puis tête seule 0,26–0,40 s), gel 0,06 s,
  étoile d'impact face caméra au bout du fer (≤ 5,5 px), les deux décharges claquent, gerbe d'étincelles (ctrl_emit) ; un son
  (son embarqué eclair_lance : crépitement et claquement, sons/eclair_lance.py). Les apparitions de l'attaque passent par l'échelle dans l'attaque elle-même (ctrl_alpha à +1 le temps de
  l'attaque, 0 à la fin) : l'aperçu de l'attaque seule les montre aux bons instants et l'état reste neutre après ;
- event_equip (1,4 s) : un éclair tombe dans la main (camy_), la gaine se forme, la hampe pousse des deux côtés, puis l'anneau et
  le fer ; les décharges claquent ; un son (block.copper_bulb.turn_on) ;
- particle_etincelle / emit_etincelle (pointe et milieu du fer) : étincelles qui montent, seulement aux décharges et à l'attaque.
États utiles d'une arme : idle, walk, run, sneak, fall (les autres retombent sur idle ou walk).
À juger en jeu : traînée vue de face (plaque dans le plan du geste), additif réel, trans_ avec shader, hasard des décharges, ctrl_*,
particules, _e de nuit. Contrôle : FLASH=1 (ou A, B) force les décharges visibles (.build/lance_orage_flash.bbmodel).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

NOM = "lance_orage"
TEX = 512
SS = 4
TAU = 2 * math.pi
FLASH = os.environ.get("FLASH", "")
P0 = np.array((6.0, 11.3, -0.6))


def lerp(a, b, k):
    return a + (b - a) * k


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


METAL = np.array([(22, 24, 36), (46, 52, 72), (70, 78, 104), (112, 122, 154), (170, 182, 214)], np.float32)
OR = np.array([(130, 90, 30), (176, 128, 44), (220, 170, 60), (255, 230, 140)], np.float32)
CRIS = np.array([(30, 30, 96), (50, 60, 160), (80, 104, 220), (130, 160, 255), (190, 208, 255), (232, 240, 255)], np.float32)


def g01(W, H):
    yy, xx = np.mgrid[0:H * SS, 0:W * SS]
    return (xx + 0.5) / (W * SS), (yy + 0.5) / (H * SS)


def red(col, W, H, mask=None):
    im = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = im
    out[..., 3] = 255 if mask is None else (np.array(Image.fromarray(mask.astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110) * 255
    return out


def hampe(W=504, H=16):
    """u le long de la hampe (a de -9 à 12), v en travers : arête claire, bagues d'or."""
    x, y = g01(W, H)
    q = np.abs(y - 0.5) * 2
    col = METAL[np.clip((3.3 * (1 - q ** 1.3) + 0.8 * (q < 0.16)).astype(int), 0, 4)]
    a = -9 + 21 * x
    gold = ((a > -3.6) & (a < -3.0)) | ((a > 3.0) & (a < 3.6)) | ((a > 7.4) & (a < 7.8)) | (a > 11.4)
    col = np.where(gold[..., None], OR[np.clip((2.6 * (1 - q ** 1.4) + 0.8 * (q < 0.2)).astype(int), 0, 3)], col)
    return red(col, W, H)


def gaine(W=160, H=16):
    x, y = g01(W, H)
    q = np.abs(y - 0.5) * 2
    cuir = lerp(np.array((18, 22, 48), np.float32), np.array((52, 62, 112), np.float32), (1 - q ** 1.5)[..., None])
    band = np.mod(x * 12 + y * 0.9, 1) < 0.16
    col = np.where(band[..., None], cuir * 0.55, cuir)
    gold = (x < 0.05) | (x > 0.95)
    col = np.where(gold[..., None], OR[2], col)
    return red(col, W, H)


def or_tile(W=32, H=16):
    x, y = g01(W, H)
    q = np.abs(y - 0.5) * 2
    return red(OR[np.clip((3.2 * (1 - q ** 1.4) + 0.6 * (q < 0.2)).astype(int), 0, 3)], W, H)


def medaillon(N=96):
    x, y = g01(N, N)
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
    shade = np.clip(0.5 + 0.35 * y - 0.25 * r, 0, 1)[..., None]
    col = lerp(METAL[1], METAL[3], shade)
    col = np.where(((r < 0.80) & (r > 0.74))[..., None], METAL[0], col)
    col = np.where(rim[..., None], lerp(OR[1], OR[3], shade), col)
    col = np.where(tom[..., None], lerp(OR[0], OR[3], np.clip(shade + 0.1, 0, 1)), col)
    return red(col, N, N, disc)


FER_L, FER_H = 8.4, 3.4


def fer(W=256, H=96):
    """Feuille de cristal : u de la base (0) à la pointe (1), b en travers (-1..1). Deux crans en éclair sur chaque bord."""
    x, y = g01(W, H)
    b = 1 - 2 * y
    u = x
    prof = np.interp(u, [0, 0.06, 0.28, 0.46, 0.62, 0.80, 1.0], [0.18, 0.62, 1.0, 0.86, 0.70, 0.42, 0.0])
    k1 = 0.30 * np.clip(1 - (u - 0.40) / 0.13, 0, 1) * (u >= 0.40)
    k2 = 0.22 * np.clip(1 - (u - 0.64) / 0.12, 0, 1) * (u >= 0.64)
    hw = np.clip(prof - k1 - k2, 0, None)
    mask = np.abs(b) < hw
    s = np.abs(b) / np.maximum(hw, 1e-3)
    v = 1.2 + 2.6 * u + 0.8 * (b > 0) - 1.2 * s
    col = CRIS[np.clip(v.astype(int), 0, 5)]
    edge = (s > 0.80) & mask
    col = np.where(edge[..., None], CRIS[5], col)
    zz = 0.12 * (2 * np.abs(2 * (u * 7 - np.floor(u * 7 + 0.5))) - 1) * np.clip(hw * 2, 0, 1)
    fil = (np.abs(b - zz) < 0.07) & mask & (u > 0.08) & (u < 0.93)
    col = np.where(fil[..., None], np.array((214, 228, 255), np.float32), col)
    a = np.where(mask, np.clip(170 + 30 * u + 25 * edge + 20 * fil, 170, 215), 0)
    im = np.array(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(a.astype(np.uint8), "L").resize((W, H), Image.BOX))
    m = np.array(Image.fromarray(mask.astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = im
    out[..., 3] = np.where(m, np.clip(al, 170, 215), 0)
    out[~m, :3] = 0
    fl = np.array(Image.fromarray(fil.astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110
    e = np.zeros_like(out)
    ec = lerp(np.array((120, 150, 235)), np.array((185, 210, 255)), ((np.arange(W) + 0.5) / W)[None, :, None])
    e[..., :3] = np.where(fl[..., None], ec, 0).astype(np.uint8)
    e[..., 3] = (fl & m) * 255
    e[~(fl & m), :3] = 0
    return out, e


def ame(W=64, H=8):
    x, y = g01(W, H)
    return red(CRIS[np.clip((1.0 + 2.0 * x).astype(int), 0, 5)], W, H)


WHITE, BLUE, VIOLET = np.array((250, 250, 240), np.float32), np.array((150, 210, 255), np.float32), np.array((120, 80, 255), np.float32)


def couches(best):
    """Distance normalisée au canal -> (add, trans) : cœur blanc, halo bleu, bord violet ; double trans_ alpha 120–180."""
    core = np.clip((0.34 - best) / 0.12, 0, 1)
    g1, g2 = np.exp(-(best / 1.45) ** 2), np.exp(-(best / 2.8) ** 2)
    rgb = np.maximum.reduce([VIOLET * 0.62 * g2[..., None], BLUE * 0.92 * g1[..., None], WHITE * core[..., None]])
    return rgb


def finir(rgb, best, W, H):
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


def _segd(X, Y, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = max(vx * vx + vy * vy, 1e-9)
    t = np.clip(((X - a[0]) * vx + (Y - a[1]) * vy) / L2, 0, 1)
    return np.hypot(X - a[0] - t * vx, Y - a[1] - t * vy)


def bolt(seed, W, H, n=5, w0=4.0, w1=2.6, ss=4):
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
    return finir(couches(best), best, W, H)


# Traînée : secteur d'anneau dans le plan du geste, centré sur la prise ; angle θ depuis l'avant (+ = vers le haut).
TR_A0, TR_A1, TR_Y0, TR_Y1 = 0.0, 23.0, -16.0, 10.0          # étendue de la plaque : a (avant), dy (hauteur)
TH_TAIL, TH_HEAD, R_IN, R_OUT = 25.0, -40.0, 13.0, 22.0


def trainee(W, H, th_min, ss=4):
    x, y = g01(W, H)
    a = TR_A0 + (TR_A1 - TR_A0) * x
    dy = TR_Y1 - (TR_Y1 - TR_Y0) * y
    r = np.hypot(a, dy)
    th = np.degrees(np.arctan2(dy, a))
    k = np.clip((TH_TAIL - th) / (TH_TAIL - TH_HEAD), 0, 1)          # 0 queue, 1 tête
    inner = R_OUT - (R_OUT - R_IN) * k ** 0.8                          # drapeau : la bande s'épaissit vers la tête
    band = (r < R_OUT) & (r > inner) & (th <= TH_TAIL) & (th >= max(TH_HEAD - 2, th_min))
    d = np.clip((R_OUT - r) / np.maximum(R_OUT - inner, 1e-3), 0, 1)   # 0 au bord d'attaque (extérieur), 1 au bord intérieur
    f = band * (1 - d) ** 1.2 * (0.35 + 0.65 * k)
    rgb = np.maximum.reduce([VIOLET * 0.5 * np.clip(f * 2.2, 0, 1)[..., None], BLUE * 0.6 * f[..., None] ** 1.2,
                             WHITE * 0.85 * np.clip((f - 0.8) / 0.12, 0, 1)[..., None]])
    im = np.array(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    add = np.zeros((H, W, 4), np.uint8)
    lum = im.max(axis=2)
    add[..., :3] = np.where((lum > 16)[..., None], im, 0)
    add[..., 3] = (lum > 16) * 255
    # double trans_ : bord d'attaque fin et clair (alpha 160), corps bleu léger (alpha 70–110) plus épais vers la tête
    fa = np.where(band & (d < 0.12) & (k > 0.25), 150, np.where(band & (d < 0.2 + 0.35 * k), 40 + 40 * k, 0))
    col = np.where((d < 0.16)[..., None], np.array((230, 238, 255), np.float32), np.array((120, 150, 240), np.float32))
    tr = np.zeros((H, W, 4), np.uint8)
    tr[..., :3] = np.array(Image.fromarray(col.astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray(fa.astype(np.uint8), "L").resize((W, H), Image.BOX)).astype(np.float32)
    al = np.where(al >= 25, np.clip(al, 40, 150), 0)
    tr[..., 3] = al.astype(np.uint8)
    tr[al == 0, :3] = 0
    return add, tr


def etoile(N=64, branches=4):
    x, y = g01(N, N)
    x, y = (x * 2 - 1) * 1.0, (1 - y * 2)
    d = np.abs(x) ** 0.45 + np.abs(y) ** 0.45
    d2 = np.abs((x + y) / 1.414) ** 0.45 + np.abs((x - y) / 1.414) ** 0.45
    best = np.minimum(np.clip(d - 0.2, 0, None) * 1.4, np.clip(d2 - 0.2, 0, None) * 2.6) / 0.35
    return finir(couches(best), best, N, N)


def etincelle(N=16):
    x, y = g01(N, N)
    x, y = x * 2 - 1, y * 2 - 1
    d = np.abs(x) ** 0.5 + np.abs(y) ** 0.5
    m = np.array(Image.fromarray(((d < 0.95) * 255).astype(np.uint8), "L").resize((N, N), Image.LANCZOS)) > 110
    c = np.array(Image.fromarray(((d < 0.55) * 255).astype(np.uint8), "L").resize((N, N), Image.LANCZOS)) > 110
    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = (150, 200, 255)
    out[c, :3] = (245, 248, 255)
    out[..., 3] = m * 255
    return out


fer_im, fer_e = fer()
TILES = [("hampe", hampe(), None), ("gaine", gaine(), None), ("or", or_tile(), None), ("medal", medaillon(), None),
         ("fer", fer_im, fer_e), ("ame", ame(), None), ("spark", etincelle(), None)]
for i, sd in enumerate((31, 47, 83)):
    a_, t_ = bolt(sd, 48, 84)
    TILES += [(f"boltA{i}", a_, None), (f"boltT{i}", t_, None)]
for nm, thm in (("trF", -90.0), ("trH", -12.0)):
    a_, t_ = trainee(144, 162, thm)
    TILES += [(nm + "A", a_, None), (nm + "T", t_, None)]
a_, t_ = etoile()
TILES += [("starA", a_, None), ("starT", t_, None)]
UV = {}
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
_x = _y = _sh = 0
for n, im, em in sorted(TILES, key=lambda it: -it[1].shape[0]):
    h, w = im.shape[:2]
    if _x + w + 1 > TEX:
        _x, _y, _sh = 0, _y + _sh + 1, 0
    UV[n] = (_x, _y, _x + w, _y + h)
    tex[_y:_y + h, _x:_x + w] = im
    if em is not None:
        tex_e[_y:_y + h, _x:_x + w] = em
    _x += w + 1
    _sh = max(_sh, h)
assert _y + _sh <= TEX, "atlas"
for n in UV:
    if not (n.endswith("T") or n.startswith("boltT") or n == "fer"):
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
    if part:
        a, b, c, d = part
        u0, u1, v0, v1 = u0 + (u1 - u0) * a, u0 + (u1 - u0) * b, v0 + (v1 - v0) * c, v0 + (v1 - v0) * d
    return [u1 if fu else u0, v1 if fv else v0, u0 if fu else u1, v0 if fv else v1]


X0, Y0, Z0 = P0
zz = lambda a: Z0 - a                          # a vers l'avant -> z


def octo(g, nom, a0, a1, r, tile, part_u=None, ends=None):
    """Tronçon octogonal le long de la hampe (a0 < a1) ; faces longues texturées (u le long), bouts selon ends."""
    for j, rz in enumerate((0, 45)):
        rr = r * (1 if j == 0 else 0.97)
        e0, e1 = (a0, a1) if j == 0 else (a0 + 0.15, a1 - 0.15)
        pu = part_u or (0, 1)
        lng = uvr(tile, part=(pu[0], pu[1], 0, 1))
        f = {"east": lng, "west": lng, "up": uvr(tile, part=(pu[0], pu[1], 0, 1)), "down": lng}
        if ends and j == 0:
            f.update({"north": ends, "south": ends})
        cube(g, f"{nom}{'o' if j else ''}", (X0 - rr, Y0 - rr, zz(e1)), (X0 + rr, Y0 + rr, zz(e0)), (X0, Y0, zz((a0 + a1) / 2)), f, rot=(0, 0, rz))


BRAS = G("right_arm", (5, 22, 0))
PRISE = G("prise", P0, BRAS)
COUP = G("coup", P0, PRISE)
uh = lambda a: (a + 9) / 21
GAINE = G("gaine", P0, COUP)
octo(GAINE, "gaine", -2.5, 2.5, 0.56, "gaine", ends=uvr("or", part=(0, 0.5, 0, 1)))
for k, a_ in enumerate((-1.7, 0.0, 1.7)):          # bagues d'or en relief sur la gaine (0,1 px au-dessus de ses faces)
    octo(GAINE, f"bague{k}", a_ - 0.18, a_ + 0.18, 0.68, "or", ends=uvr("or", part=(0, 0.5, 0, 1)))
H_AV = G("hampe_av", (X0, Y0, zz(2.5)), COUP)
octo(H_AV, "hampe_av", 2.62, 12.15, 0.42, "hampe", part_u=(uh(2.62), uh(12.15)))
H_AR = G("hampe_ar", (X0, Y0, zz(-2.5)), COUP)
octo(H_AR, "hampe_ar", -8.88, -2.62, 0.42, "hampe", part_u=(uh(-8.88), uh(-2.62)))
octo(H_AR, "talon", -9.5, -9.0, 0.6, "or", ends=uvr("or", part=(0, 0.5, 0, 1)))
TRT = G("trans_talon", (X0, Y0, zz(-9.5)), H_AR)      # éclat de cristal au talon : petite feuille croisée, vers l'arrière
_fu = uvr("fer")
for j, rz in enumerate((0, 90)):
    cube(TRT, f"talon_c{j}", (X0 - 0.15, Y0 - 0.65, zz(-9.45)), (X0 + 0.15, Y0 + 0.65, zz(-12.3)), (X0, Y0, zz(-9.5)),
         {"east": [_fu[2], _fu[1], _fu[0], _fu[3]], "west": _fu}, rot=(0, 0, rz))
TETE = G("tete", (X0, Y0, zz(12.15)), COUP)
MR = 1.65
cube(TETE, "anneau", (X0 - MR, Y0 - MR, zz(12.75)), (X0 + MR, Y0 + MR, zz(12.27)), (X0, Y0, zz(12.5)), {"north": uvr("medal"), "south": uvr("medal", fu=True)})
for j, rz in enumerate((0, 45)):
    rr = MR * 0.68 * (1 if j == 0 else 0.985)
    m_ = uvr("hampe", part=(0.0, 0.25, 0, 1))
    cube(TETE, f"anneau_k{j}", (X0 - rr, Y0 - rr, zz(12.69)), (X0 + rr, Y0 + rr, zz(12.33)), (X0, Y0, zz(12.5)), {"up": m_, "down": m_, "east": m_, "west": m_}, rot=(0, 0, rz))
octo(TETE, "collet", 12.87, 13.6, 0.5, "or", ends=uvr("or", part=(0, 0.5, 0, 1)))
FA0 = 13.3
TRF = G("trans_fer", (X0, Y0, zz(FA0)), TETE)
fu = uvr("fer")
cube(TRF, "fer_v", (X0 - 0.15, Y0 - FER_H / 2, zz(FA0 + FER_L)), (X0 + 0.15, Y0 + FER_H / 2, zz(FA0)), (X0, Y0, zz(FA0)),
     {"east": fu, "west": [fu[2], fu[1], fu[0], fu[3]]})
# seconde lame, plus étroite, croisée à 90° autour de la hampe (même plaque tournée : la texture reste le long de la hampe)
cube(TRF, "fer_h", (X0 - 0.15, Y0 - FER_H * 0.32, zz(FA0 + FER_L * 0.92)), (X0 + 0.15, Y0 + FER_H * 0.32, zz(FA0)), (X0, Y0, zz(FA0)),
     {"east": fu, "west": [fu[2], fu[1], fu[0], fu[3]]}, rot=(0, 0, 90))
am = uvr("ame")
cube(TETE, "fer_ame", (X0 - 0.2, Y0 - 0.2, zz(FA0 + FER_L * 0.7)), (X0 + 0.2, Y0 + 0.2, zz(FA0 + 0.1)), (X0, Y0, zz(FA0)),
     {"up": am, "down": am, "east": am, "west": am}, rot=(0, 0, 45))
TIP = (X0, Y0, zz(FA0 + FER_L))

# décharges sur le fer (cam_, enfants de la tête)
BOLTS, EMITS = [], []
for i, (a, w, h) in enumerate(((FA0 + 2.4, 2.2, 3.8), (FA0 + 6.2, 2.0, 3.4))):
    p = (X0, Y0 - 0.3, zz(a))
    cam = G(f"cam_eclair{i + 1}", p, TETE)
    forms = []
    for j, dz in enumerate((0.0, 0.45)):
        fg = G(f"eclair{i + 1}{'ab'[j]}", p, cam)
        G("ctrl_alpha", p, fg)
        ga, gt = G(f"add_eclair{i + 1}{'ab'[j]}", p, fg), G(f"trans_eclair{i + 1}{'ab'[j]}", p, fg)
        ti = (i + j) % 3
        cube(ga, f"eclair{i + 1}{'ab'[j]}", (p[0] - w / 2, p[1] - h, p[2] + dz + 0.85), (p[0] + w / 2, p[1], p[2] + dz + 1.15), p, {"south": uvr(f"boltA{ti}")})
        cube(gt, f"eclair{i + 1}{'ab'[j]}t", (p[0] - w / 2, p[1] - h, p[2] + dz - 0.05), (p[0] + w / 2, p[1], p[2] + dz + 0.25), p, {"south": uvr(f"boltT{ti}")})
        forms.append(fg)
    BOLTS.append((forms[0], forms[1], 0.41 + 3.17 * i))
    e = G("emit_etincelle" + (str(i + 1) if i else ""), p, TETE)
    G("ctrl_emit", p, e)
    EMITS.append((e, 0.41 + 3.17 * i))
e = G("emit_etincelle3", TIP, TETE)
G("ctrl_emit", TIP, e)
EMITS.append((e, BOLTS[1][2]))

# étoile d'impact au bout du fer
CAM_S = G("cam_impact", TIP, TETE)
IMPACT = G("impact", TIP, CAM_S)
G("ctrl_alpha", TIP, IMPACT)
for nm, dz, t_ in (("add_impact", 0.0, "starA"), ("trans_impact", -0.9, "starT")):
    g = G(nm, TIP, IMPACT)
    cube(g, nm[nm.index("_") + 1:] + ("t" if "trans" in nm else ""), (TIP[0] - 2.7, TIP[1] - 2.7, TIP[2] + dz - 0.15), (TIP[0] + 2.7, TIP[1] + 2.7, TIP[2] + dz + 0.15), TIP, {"south": uvr(t_)})

# traînée : plan du geste (x = 6,9, à côté de la lance), enfant de la prise (elle reste dans l'air pendant que la lance tourne)
XT = X0 + 0.9
TRAINS = []
for k, nm in enumerate(("trF", "trH")):
    g = G(f"trainee_{'entiere' if k == 0 else 'tete'}", P0, PRISE)
    G("ctrl_alpha", P0, g)
    for kind, dx in (("A", 0.0), ("T", 0.45)):
        sub = G(f"{'add' if kind == 'A' else 'trans'}_trainee{k}", P0, g)
        x = XT + dx + 0.9 * k
        u = uvr(nm + kind)
        cube(sub, f"trainee{k}{kind}", (x - 0.15, Y0 + TR_Y0, zz(TR_A1)), (x + 0.15, Y0 + TR_Y1, zz(TR_A0)), P0, {"east": u, "west": [u[2], u[1], u[0], u[3]]})
    TRAINS.append(g)

# éclair de l'apparition : camy_ qui tombe dans la main
FC = (X0, 30.0, Z0)
FOUDRE = G("foudre", FC, BRAS)
CAMY = G("camy_foudre", FC, FOUDRE)
CA_F = G("ctrl_alpha", FC, CAMY)
FAd, FTr = G("add_foudre", FC, CAMY), G("trans_foudre", FC, CAMY)
for j in range(3):
    y1 = 46.0 - 11.0 * j
    cube(FAd, f"foudre{j}", (X0 - 2.4, y1 - 11.0, -0.15), (X0 + 2.4, y1, 0.15), FC, {"south": uvr(f"boltA{j}", fu=j == 1)})
    cube(FTr, f"foudre{j}t", (X0 - 2.45, y1 - 11.1, -1.05 - 0.3 * j), (X0 + 2.45, y1 + 0.1, -0.75 - 0.3 * j), FC, {"south": uvr(f"boltT{j}", fu=j == 1)})

PART = G("particle_etincelle", (0, 0, 0))
cube(PART, "etincelle", (-0.25, 0.3, -0.15), (0.25, 0.8, 0.15), (0, 0.55, 0), {"south": uvr("spark")})
outliner = [BRAS.json(), PART.json()]


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


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def pose(rise, inward, roll):
    return rise, inward, -roll


def etat(nom, L, rise, inward, roll, amp, cycles, rate, fps=12):
    A = {}
    n = max(6, int(round(L * fps)))
    for i in range(n + 1):
        t = i * L / n
        ph = TAU * cycles * t / L
        piste(A, PRISE, [kf("rotation", t, *pose(rise + amp * math.sin(ph), inward + 0.35 * amp * math.sin(ph + 1.2), roll + 0.25 * amp * math.sin(ph + 0.6)))])
    P, p = rate
    for fa, fb, c in BOLTS:
        for j, fg in enumerate((fa, fb)):
            w0, w1 = ((0.0, 0.06), (0.06, 0.13))[j]
            piste(A, fg.enfants[0], [kf("position", 0, f"{vis(P, p, c, w0, w1)}-1", 0, 0)])
    for g, c in EMITS:
        piste(A, g.enfants[0], [kf("position", 0, f"8*{vis(P, p, c, 0.0, 0.22)}-1", 0, 0)])
    for g in [CA_F, IMPACT.enfants[0]] + [t.enfants[0] for t in TRAINS]:
        piste(A, g, [kf("position", 0, -1, 0, 0)])
    return {"uuid": nuid(), "name": nom, "loop": "loop", "override": False, "length": L, "snapping": 24, "selected": nom == "idle", "animators": A}


STATES = [etat("idle", 8.0, 0.0, 0.0, 0.0, 0.8, 2, (7.0, 0.45), fps=6), etat("walk", 1.6, 2.0, 0.5, 0.0, 2.0, 1, (5.0, 0.45)),
          etat("run", 1.0, 10.0, 2.0, 2.0, 3.0, 1, (3.0, 0.55), fps=16), etat("sneak", 3.0, -18.0, 2.0, -3.0, 0.8, 1, (10.0, 0.3)),
          etat("fall", 2.0, 6.0, 0.0, 0.0, 1.5, 1, (5.0, 0.45))]


def fen_val(t, fen):
    return 1.0 if any(a <= t < b for a, b in fen) else 0.0


def cles(ch, fen, L, on=1.0, off=0.0, fin=None, axes="xyz"):
    """Clés à bords francs (5 ms) ; fin : valeur à la toute dernière clé (retour neutre de l'état)."""
    ts = {0.0, L}
    for a, b in fen:
        ts |= {max(0.0, a - 0.005), a, max(0.0, b - 0.005), b}
    out = []
    for t in sorted(ts):
        v = (on if fen_val(t if t < L else L - 1e-6, fen) else off) if not (t >= L and fin is not None) else fin
        out.append(kf(ch, t, *[(v if c in axes else (1.0 if ch == "scale" else 0.0)) for c in "xyz"]))
    return out


def apparition(A, g_ctrl, g_scale, fen, L):
    """Pièce cachée par l'état (ctrl_alpha −1) : +1 pendant tout l'événement (0 à la fin), échelle 0/1 par fenêtre (1 à la fin).
    En jeu : visible dans les fenêtres seulement ; aperçu de l'événement seul : idem ; après : l'état reprend la main."""
    piste(A, g_ctrl, cles("position", [(0.0, L)], L, 1.0, 0.0, fin=0.0, axes="x"))
    piste(A, g_scale, cles("scale", fen, L, 1.0, 0.0, fin=1.0))


AT = 0.8


def coup_attack(t):
    up = bump(t, 0.0, 0.09, 0.09, 0.15)
    cut = sm(t, 0.13, 0.20) * (1 - sm(t, 0.30, 0.70))             # gel de 0,06 s à −40° (0,20–0,26), puis retour
    return pose(25 * up - 40 * cut, 4 * cut, 6 * cut)


A = {}
T_ = [round(i * AT / 40, 4) for i in range(41)]
piste(A, COUP, [kf("rotation", t, *coup_attack(t)) for t in T_])
apparition(A, TRAINS[0].enfants[0], TRAINS[0], [(0.13, 0.26)], AT)
apparition(A, TRAINS[1].enfants[0], TRAINS[1], [(0.26, 0.40)], AT)
apparition(A, IMPACT.enfants[0], IMPACT, [(0.19, 0.29)], AT)
for fa, fb, c in BOLTS:
    apparition(A, fa.enfants[0], fa, [(0.20, 0.26), (0.40, 0.44)], AT)
    apparition(A, fb.enfants[0], fb, [(0.26, 0.33)], AT)
for g, c in EMITS:
    piste(A, g.enfants[0], cles("position", [(0.19, 0.42)], AT, 8.0, 0.0, fin=0.0, axes="x"))
piste(A, CA_F, cles("position", [(0.0, AT)], AT, -1.0, 0.0, fin=0.0, axes="x"))
A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [{"channel": "sound", "data_points": [{"effect": "eclair_lance", "file": ""}], "time": 0.0}]}
attack = {"uuid": nuid(), "name": "attack", "loop": "once", "override": False, "length": AT, "snapping": 24, "selected": False, "animators": A}

HU = 0.8


def coup_hurt(t):
    env = sm(t, 0.0, 0.05) * (1 - sm(t, 0.45, 0.75))
    trem = math.sin(TAU * t / 0.1) * math.exp(-4.0 * t)
    return pose(env * (-6 + 3.5 * trem), env * 1.5, env * 4 * trem)


A = {}
piste(A, COUP, [kf("rotation", t, *coup_hurt(t)) for t in T_])
apparition(A, BOLTS[0][0].enfants[0], BOLTS[0][0], [(0.04, 0.10)], HU)
piste(A, CA_F, cles("position", [(0.0, HU)], HU, -1.0, 0.0, fin=0.0, axes="x"))
for g in [IMPACT.enfants[0]] + [t.enfants[0] for t in TRAINS]:
    piste(A, g, cles("position", [(0.0, HU)], HU, -1.0, 0.0, fin=0.0, axes="x"))
hurt = {"uuid": nuid(), "name": "hurt", "loop": "once", "override": False, "length": HU, "snapping": 24, "selected": False, "animators": A}

for an in (attack, hurt):
    for b in an["animators"].values():
        if b.get("type") == "effect":
            continue
        for k in [k for k in b["keyframes"] if k["time"] >= an["length"] - 1e-6]:
            d = k["data_points"][0]
            neutre = 1.0 if k["channel"] == "scale" else 0.0
            assert all(abs(float(d[a]) - neutre) < 0.02 for a in "xyz"), (an["name"], b["name"], d)

# event_equip 1,4 s : l'éclair tombe dans la main, la gaine se forme, la hampe pousse des deux côtés, puis l'anneau et le fer
EQ = 1.4
T_ = [round(i * EQ / 42, 4) for i in range(43)]
A = {}
apparition(A, CA_F, CAMY, [(0.04, 0.12), (0.15, 0.24)], EQ)


def grow(t, a, b, over=0.08):
    return 0.02 + 0.98 * sm(t, a, b) + over * bump(t, b - 0.05, b, b + 0.03, b + 0.16) * (t < EQ - 0.05)


piste(A, GAINE, [kf("scale", t, *([1.0 if t >= EQ else grow(t, 0.16, 0.36)] * 3)) for t in T_])
for g in (H_AV, H_AR):
    piste(A, g, [kf("scale", t, 1, 1, 1.0 if t >= EQ else grow(t, 0.3, 0.7, 0.0)) for t in T_])
piste(A, TETE, [kf("scale", t, *([1.0 if t >= EQ else grow(t, 0.62, 0.95)] * 3)) for t in T_])
for fa, fb, c in BOLTS:
    apparition(A, fa.enfants[0], fa, [(1.0, 1.06)], EQ)
    apparition(A, fb.enfants[0], fb, [(1.06, 1.13)], EQ)
A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [{"channel": "sound", "data_points": [{"effect": "block.copper_bulb.turn_on", "file": ""}], "time": 0.04}]}
equip = {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": EQ, "snapping": 24, "selected": False, "animators": A}

PF = 0.4
p_fall = {"uuid": nuid(), "name": "particle_etincelle_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24, "selected": False,
          "animators": {PART.uuid: {"name": PART.nom, "type": "bone", "keyframes":
                        [kf("scale", t, *([1 + 0.35 * math.cos(TAU * t / PF)] * 3)) for t in [i * PF / 8 for i in range(9)]]}}}

ANIMS = STATES + [attack, hurt, equip, p_fall]
assert 30 <= len(elements) <= 130, len(elements)
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner,
         "textures": [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": _b64[0]},
                      {"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": _b64[1]}],
         "animations": ANIMS}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons, embarquer_sons
embarquer_sons(model, {"eclair_lance": "sons/eclair_lance.ogg"})   # son original synthétisé (tools/synthe.py)
limiter_sons(model, attaque=True)
from reactions import retirer_reactions
retirer_reactions(model, garder=("attack",))
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
