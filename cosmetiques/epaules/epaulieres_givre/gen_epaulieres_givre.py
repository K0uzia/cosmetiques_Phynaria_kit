"""Épaulières de givre v2 (refonte du 2026-11-08) : paire asymétrique d'écailles de glace et de cristaux, ensemble Givre. Design original.
Écrit epaulieres_givre.png, epaulieres_givre_e.png et .build/epaulieres_givre_brut.bbmodel à côté de ce script.
Ancienne version (coque d'argent à dentelle, « moche ») : .build/gen_avant.py, .build/avant_livrable.bbmodel.

Construction reprise de epaulieres_abyssales (la référence réussie selon l'utilisateur) : éventails de plaques à arête pleine,
éléments qui montent au-dessus de l'épaule, asymétrie (gauche plus grande), lumière dans les nervures.
Documentation (pauldrons réels, givre) : une épaulière est une coque à l'articulation de l'épaule, prolongée de lames à arête
médiane qui se recouvrent en s'éloignant de la plaque maîtresse (rang haut vers le cou, rangs bas sur le bras) ; le givre
pousse en aiguilles et en « plumes » blanches mates, la glace en prismes hexagonaux brillants.

Sur chaque épaule :
- rang haut (coque) : 5 écailles de glace en éventail sur le dessus de l'épaule, penchées vers l'extérieur ;
- rang bas : jupe de 4 (droite) ou 5 (gauche) écailles autour du haut du bras (avant, extérieur, arrière), l'extérieure la plus longue ;
- une écaille = peau translucide découpée (trans_, alpha 140–225 : cœur bleu nuit au pied, cyan, liseré givré blanc,
  chevrons de facettes, fissures) + arête pleine en losange (givre opaque, filet cyan au calque _e) : vrai volume par la tranche ;
- grappe de cristaux hexagonaux qui montent en rayonnant (gauche : 5, le plus grand 9,6 px ; droite : 3, 6,8 px), recette
  « cristal » de effet_givre : 6 facettes trans_ + pointe en 6 facettes + âme opaque cyan (calque _e 200–225) ;
- rosace de givre à six branches posée sur l'écaille maîtresse (rappel de la rosace de aura_givre), gemme centrale au _e ;
- crête de givre en aiguilles blanches mates côté cou.

Fonctions avancées (guide 4 bis, 5 ter, 6.4) ; à juger en jeu (/cosmetique apercu) :
- trans_ (écailles et cristaux) : semi-transparence validée en jeu sur l'ensemble Givre (alpha 140–220) ;
- calque _e : nervures des écailles, âmes des cristaux, rosace, gemmes (sources nettes 150–225) ;
- particle_scintille + emit_scintille* au bout des trois plus grands cristaux (reglages.json) ;
- overlay_givre : les âmes des cristaux respirent (échelle) ; overlay_ambiance (tools/ambiance.py) ;
- event_equip (1,5 s) : la coque pousse depuis l'épaule, les écailles basses tombent en place, les cristaux jaillissent un à un,
  la rosace se pose ; un carillon d'améthyste (seul son de la pièce).
États : idle (8 s), walk, run, sneak ; pas d'attack ni de hurt (pièce portée).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True
NOM = "epaulieres_givre"
TEX = 512
TAU = 2 * math.pi
SS = 4
RNG = np.random.default_rng(11)

RAMP = np.array([(10, 30, 66), (16, 48, 108), (24, 84, 150), (38, 132, 192), (70, 184, 226), (120, 208, 238),
                 (170, 230, 248), (214, 242, 252), (244, 253, 255)], np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


def ramp(v):
    v = np.clip(np.asarray(v, np.float32), 0, 0.999) * (len(RAMP) - 1)
    i = np.floor(v).astype(int)
    f = (v - i)[..., None]
    return RAMP[i] * (1 - f) + RAMP[np.minimum(i + 1, len(RAMP) - 1)] * f


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def grille(W, H, ss=SS):
    n_w, n_h = W * ss, H * ss
    return np.meshgrid((np.arange(n_w) + 0.5) / n_w * 2 - 1, 1 - (np.arange(n_h) + 0.5) / n_h * 2)


def lanczos(a, W, H):
    return np.array(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)).astype(np.float32)


def reduire(rgb, al, W, H, trans, lo=140, hi=225):
    """rgb, al au sur-échantillonnage -> RGBA ; opaque : alpha 0/255 (seuil 110) ; trans : alpha borné [lo, hi] dans la découpe."""
    c = np.stack([lanczos(rgb[..., k], W, H) for k in range(3)], axis=-1)
    m = lanczos((al > 0) * 255.0, W, H) > 110
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = np.clip(c, 0, 255)
    if trans:
        a = lanczos(al, W, H)
        arr[..., 3] = np.where(m, np.clip(a, lo, hi), 0)
    else:
        arr[..., 3] = m * 255
    arr[~m, :3] = 0
    return arr


def segment(x, y, p, q, w):
    px, py = p
    dx, dy = q[0] - px, q[1] - py
    L2 = dx * dx + dy * dy + 1e-12
    t = np.clip(((x - px) * dx + (y - py) * dy) / L2, 0, 1)
    d = np.hypot(x - px - t * dx, y - py - t * dy)
    return np.clip((w - d) / (w * 0.35), 0, 1)


def bruit(W, H, cells, seed):
    r = np.random.default_rng(seed)
    a = (r.random((cells, cells)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((W, H), Image.BICUBIC), np.float32) / 255


# ------------------------------------------------------------------ images (RGBA, et calque _e éventuel)
IMGS = {}        # nom -> (rgba, e_rgba ou None, trans)

# Écaille : gabarit en px (longueur LS, largeur WS), image couvrant [-M, LS + M] x [-WS/2 - M, WS/2 + M]
LS, WS, MS = 6.0, 3.2, 0.12
DS = 34          # texels par px


def ecaille_hw(t, var):
    """Demi-largeur relative (0..1) d'une écaille anguleuse : pied étroit, épaule au tiers, pointe en biseau."""
    j = [(0.0, 0.36), (0.30 + 0.03 * var, 1.0), (0.64 - 0.04 * var, 0.78 + 0.05 * var), (0.86, 0.36), (1.0, 0.0)]
    return np.interp(t, [p[0] for p in j], [p[1] for p in j])


def paint_ecaille(var):
    W, H = int((LS + 2 * MS) * DS), int((WS + 2 * MS) * DS)
    x, y = grille(W, H)
    px_ = (x + 1) / 2 * (LS + 2 * MS) - MS          # px le long (0 = pied)
    py_ = y * (WS / 2 + MS)                          # px en travers
    t = px_ / LS
    hw_l = ecaille_hw(np.clip(t, 0, 1), var) * WS / 2
    # dissymétrie : bord de fuite (y < 0) un peu plus creusé vers la pointe
    hw = np.where(py_ < 0, hw_l * (1 - 0.18 * np.clip(t - 0.4, 0, 1)), hw_l)
    dedans = (np.abs(py_) < hw) & (t >= 0) & (t <= 1)
    bord = hw - np.abs(py_)                          # px jusqu'au bord
    rng = np.random.default_rng(40 + var)
    val = 0.27 + 0.36 * smooth(t / 0.7)              # pied bleu nuit (ombre de recouvrement), cyan vers la pointe
    val = val + 0.10 * (py_ > 0)                     # deux facettes de part et d'autre de l'arête
    chev = t + 0.42 * np.abs(py_) / (WS / 2)
    bande = smooth((0.07 - np.abs((chev * 3.1 + 0.2 * var) % 1 - 0.5) * 2 * 0.5) / 0.03) * smooth((t - 0.12) / 0.1)
    val = val + 0.22 * bande
    refl = np.exp(-((py_ / (WS / 2) - 0.45 + 0.5 * t) / 0.12) ** 2) * smooth((t - 0.25) / 0.2) * smooth((0.85 - t) / 0.2)
    val = val + 0.25 * refl
    fiss = np.zeros_like(x)
    for _ in range(3):
        p = (rng.uniform(0.25, 0.7) * 2 - 1, rng.uniform(-0.6, 0.6))
        q = (p[0] + rng.uniform(0.1, 0.25), p[1] + rng.uniform(-0.35, 0.35))
        fiss = np.maximum(fiss, segment(x, y, p, q, 0.022))
    rim = smooth((0.20 - bord) / 0.08)               # liseré givré ≈ 6 texels
    givre = (bruit(W * SS, H * SS, 30, 7 + var) > 0.72) * smooth((0.45 - bord) / 0.25) * 0.6
    val = np.maximum(val, 0.97 * rim)
    val = np.maximum(val, 0.85 * np.maximum(fiss, givre))
    rgb = ramp(val)
    al = 215 - 55 * smooth(t / 0.8) + 30 * refl
    al = np.maximum(al, 225 * rim)
    al = np.maximum(al, 210 * np.maximum(fiss, givre))
    al = np.where(dedans, al, 0)
    IMGS[f"ecaille{var}"] = (reduire(rgb, al, W, H, True), None, True)


def paint_arete():
    """Arête d'écaille (opaque) : givre clair, filet cyan au milieu (calque _e)."""
    W, H = 192, 16
    v = np.abs((np.arange(H) + 0.5) / H * 2 - 1)[:, None] * np.ones((1, W))
    u = np.linspace(0, 1, W)[None, :] * np.ones((H, 1))
    rgb = lerp(np.array((228, 244, 252.0)), np.array((150, 196, 228.0)), (v ** 1.6)[..., None])
    filet = v < 0.30
    rgb = np.where(filet[..., None], np.array((150, 232, 255.0)), rgb)
    rgb = rgb * (0.98 + 0.02 * np.sin(u * 9))[..., None]
    a = np.dstack([rgb, np.full((H, W), 255.0)]).astype(np.uint8)
    e = np.zeros_like(a)
    e[filet] = (96, 196, 230, 255)
    e[filet & (u > 0.35)] = (130, 214, 240, 255)
    IMGS["arete"] = (a, e, False)


def paint_corps(var):
    """Facette du corps d'un cristal (trans_) : arêtes claires, pied plus dense et plus bleu, reflet oblique, fissures."""
    W, H = 40, 280
    rng = np.random.default_rng(60 + var)
    x, y = grille(W, H)
    v = (y + 1) / 2
    arete = smooth((np.abs(x) - 0.78) / 0.1)
    val = 0.30 + 0.20 * v + 0.06 * np.sin(2.3 * x + var)
    c0 = rng.uniform(-0.4, 0.1)
    refl = np.exp(-((x - c0 - 0.9 * (v - 0.5)) / 0.14) ** 2) * smooth((0.9 - v) / 0.3) * smooth((v - 0.15) / 0.2)
    val = val + 0.34 * refl
    fiss = np.zeros_like(x)
    for _ in range(3):
        p = (rng.uniform(-0.6, 0.6), rng.uniform(0.1, 0.7))
        q = (p[0] + rng.uniform(-0.5, 0.5), p[1] + rng.uniform(0.06, 0.16))
        fiss = np.maximum(fiss, segment(x, v * 2 - 1, (p[0], p[1] * 2 - 1), (q[0], q[1] * 2 - 1), 0.05))
    givre = smooth((0.12 - v) / 0.08)
    val = np.maximum(val, 0.96 * np.maximum(arete, givre))
    val = np.maximum(val, 0.8 * fiss)
    al = 205 - 60 * v + 30 * refl
    al = np.maximum(al, 225 * np.maximum(arete, givre))
    al = np.maximum(al, 210 * fiss)
    IMGS[f"corps{var}"] = (reduire(ramp(val), np.maximum(al, 1), W, H, True), None, True)


def paint_pointe(var):
    """Facette triangulaire de pointe (base en bas, sommet en haut)."""
    W, H = 40, 72
    x, y = grille(W, H)
    v = (y + 1) / 2
    demi = 0.985 * (1 - v)
    dedans = (np.abs(x) < demi) & (v < 0.985)
    bord = demi - np.abs(x)
    val = 0.42 + 0.22 * v + 0.10 * (x < 0) + 0.2 * np.exp(-(x / 0.06) ** 2)
    lis = smooth((0.12 - bord) / 0.06)
    val = np.maximum(val, 0.96 * lis)
    al = 150 + 50 * v
    al = np.maximum(al, 225 * lis)
    IMGS[f"pointe{var}"] = (reduire(ramp(val), np.where(dedans, al, 0), W, H, True), None, True)


def paint_ame():
    W, H = 8, 40
    v = np.linspace(1, 0, H)[:, None] * np.ones((1, W))
    u = np.linspace(-1, 1, W)[None, :] * np.ones((H, 1))
    val = 0.55 + 0.35 * v + 0.06 * (u < 0)
    a = np.zeros((H, W, 4), np.uint8)
    a[..., :3] = ramp(val)
    a[..., 3] = 255
    e = np.zeros_like(a)
    e[..., :3] = (lerp(np.array((110, 200, 232.0)), np.array((176, 236, 255.0)), v[..., None])).astype(np.uint8)
    e[..., 3] = 255
    IMGS["ame"] = (a, e, False)


def flocon_mask(x, y, R=0.95, w=0.085):
    f = np.zeros_like(x)
    for k in range(6):
        a = math.radians(90 + 60 * k)
        ca, sa = math.cos(a), math.sin(a)
        f = np.maximum(f, segment(x, y, (0, 0), (R * ca, R * sa), w))
        for r0, l in ((0.42, 0.30), (0.68, 0.20)):
            p = (r0 * ca, r0 * sa)
            for sg in (-1, 1):
                b = a + sg * math.radians(55)
                f = np.maximum(f, segment(x, y, p, (p[0] + l * math.cos(b), p[1] + l * math.sin(b)), w * 0.8))
    hexa = np.maximum(np.abs(x), np.abs(x) * 0.5 + np.abs(y) * 0.866) < 0.30
    return np.maximum(f, hexa * 1.0), hexa


def paint_rosace():
    N = 112
    x, y = grille(N, N)
    f, hexa = flocon_mask(x, y)
    m = f > 0.5
    ombre = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(SS * 2)), np.float32) / 255
    rgb = lerp(np.array((120, 170, 214.0)), np.array((240, 250, 255.0)), (np.clip(ombre * 1.6 - 0.3, 0, 1))[..., None])
    f2, _ = flocon_mask(x, y, R=0.86, w=0.028)
    filet = (f2 > 0.5) | hexa
    rgb = np.where(filet[..., None], np.array((150, 232, 255.0)), rgb)
    a = reduire(rgb, m * 255.0, N, N, False)
    fm = lanczos(filet * 255.0, N, N) > 100
    e = np.zeros_like(a)
    e[fm & (a[..., 3] > 0)] = (150, 226, 250, 255)
    IMGS["rosace"] = (a, e, False)


def paint_gemme():
    W = H = 16
    u, v = np.meshgrid(np.linspace(-1, 1, W), np.linspace(-1, 1, H))
    val = 0.62 + 0.25 * (u + v < 0) + 0.12 * (np.abs(u) + np.abs(v) < 0.6)
    a = np.zeros((H, W, 4), np.uint8)
    a[..., :3] = ramp(val)
    a[..., 3] = 255
    e = np.zeros_like(a)
    e[..., :3] = (lerp(np.array((120, 210, 240.0)), np.array((200, 244, 255.0)), (np.abs(u) + np.abs(v) < 0.6)[..., None] * 1.0)).astype(np.uint8)
    e[..., 3] = 255
    IMGS["gemme"] = (a, e, False)


def paint_crete():
    """Crête de givre : aiguilles et plumes blanches mates, pied plus bleu (opaque)."""
    W, H = 176, 64
    x, y = grille(W, H)
    rng = np.random.default_rng(5)
    m = (y < -0.45) * 1.0
    xs = np.linspace(-0.92, 0.92, 15)
    for i, x0 in enumerate(xs):
        h = rng.uniform(0.35, 0.95) if i % 2 else rng.uniform(0.75, 1.0)
        lean = rng.uniform(-0.08, 0.08)
        top = (x0 + lean, -1 + 2 * h * 0.98)
        m = np.maximum(m, segment(x, y, (x0, -0.9), top, 0.075 * (1.0 if i % 2 == 0 else 0.8)))
        for k in range(2):
            t = 0.45 + 0.25 * k
            p = (x0 + lean * t, -0.9 + (top[1] + 0.9) * t)
            for sg in (-1, 1):
                m = np.maximum(m, segment(x, y, p, (p[0] + sg * 0.05, p[1] + 0.2), 0.04))
    mk = m > 0.5
    v = (y + 1) / 2
    rgb = lerp(np.array((150, 196, 226.0)), np.array((246, 252, 255.0)), smooth(v / 0.6)[..., None])
    rgb = rgb * (0.95 + 0.05 * bruit(W * SS, H * SS, 40, 3))[..., None]
    IMGS["crete"] = (reduire(rgb, mk * 255.0, W, H, False), None, False)


def paint_argent():
    W, H = 128, 28
    u, v = np.meshgrid(np.linspace(0, 1, W), np.linspace(-1, 1, H))
    rgb = lerp(np.array((160, 180, 200.0)), np.array((214, 228, 240.0)), (0.5 + 0.5 * np.cos(v * 2.2))[..., None])
    bord = np.abs(v) > 0.72
    rgb = np.where(bord[..., None], np.array((226, 236, 244.0)), rgb)
    chev = (np.abs(((u * 12 + np.abs(v) * 0.6) % 1) - 0.5) < 0.06) & ~bord
    rgb = np.where(chev[..., None], np.array((84, 104, 132.0)), rgb)
    rgb = np.where(((np.abs(v) > 0.6) & ~bord)[..., None], np.array((70, 86, 110.0)), rgb)
    a = np.dstack([rgb, np.full((H, W), 255.0)]).astype(np.uint8)
    IMGS["argent"] = (a, None, False)


def paint_star():
    N = 16
    u, v = np.meshgrid(np.linspace(-1, 1, N), np.linspace(-1, 1, N))
    st = (np.abs(u) * np.abs(v) < 0.035) & (np.hypot(u, v) < 0.95) | (np.hypot(u, v) < 0.3)
    a = np.zeros((N, N, 4), np.uint8)
    a[st] = (236, 250, 255, 255)
    a[np.hypot(u, v) < 0.18] = (255, 255, 255, 255)
    IMGS["star"] = (a, None, False)


for i in range(3):
    paint_ecaille(i)
for i in range(2):
    paint_corps(i)
    paint_pointe(i)
paint_arete(); paint_ame(); paint_rosace(); paint_gemme(); paint_crete(); paint_star()

UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def pack():
    items = sorted(IMGS.items(), key=lambda it: -it[1][0].shape[0])
    x = y = shelf = 0
    for n, (im, _, _) in items:
        h, w = im.shape[:2]
        if x + w + 2 > TEX:
            x, y, shelf = 0, y + shelf + 2, 0
        assert y + h <= TEX - 6, "atlas plein"
        UV[n] = (x, y, x + w, y + h)
        x += w + 2
        shelf = max(shelf, h)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, (im, e, _) in IMGS.items():
        u0, v0, u1, v1 = UV[n]
        tex[v0:v1, u0:u1] = im
        if e is not None:
            tex_e[v0:v1, u0:u1] = e
    tex_e[tex[..., 3] == 0] = 0
    out = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        out.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return out


tex_b64, tex_e_b64 = pack()

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx (ordre du mod et du renderer)."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def Rx(deg):
    a = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def Ry(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


def group(name, origin, parent=None):
    assert name not in groups and len(name) <= 64, name
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent}
    return name


def F(tile, flip=False):
    u0, v0, u1, v1 = UV[tile]
    return [u1, v0, u0, v1] if flip else [u0, v0, u1, v1]


def ocube(g, name, origin, R, lo, hi, faces):
    """Cube dans le repère R (colonnes = axes locaux), lo/hi = coins locaux depuis origin."""
    o = np.asarray(origin, float)
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in o + np.asarray(lo, float)],
         "to": [round(float(v), 3) for v in o + np.asarray(hi, float)], "origin": [round(float(v), 3) for v in o], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    rot = euler(R)
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    e["_R"] = R
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])
    return e


def frame(X, Y):
    X = unit(X)
    Y = unit(np.asarray(Y, float) - (np.asarray(Y, float) @ X) * X)
    return np.column_stack([X, Y, np.cross(X, Y)])


def plate(g, name, c, R, w, h, tile, th=0.3, both=True, flip=False):
    """Plaque fine dans le repère R (u suit X, haut de l'image = +Y) ; tranches transparentes."""
    fc = {"south": F(tile, flip), "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
    fc["north"] = F(tile, not flip) if both else CLEAR
    return ocube(g, name, c, R, (-w / 2, -h / 2, -th / 2), (w / 2, h / 2, th / 2), fc)


def bar(g, name, p, q, r, tile, up, ov=0.0, caps=(True, True)):
    """Tronçon en losange (section carrée à 45° de la référence up), texturé sur ses 4 faces longues."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    R0 = frame(q - p, up)
    R45 = R0 @ Rx(45)
    lg = F(tile)
    u0, v0, u1, v1 = UV[tile]
    end = [u0, v0, u0 + 3, v1]
    fc = {"south": lg, "north": lg, "up": lg, "down": lg, "east": end if caps[1] else CLEAR, "west": end if caps[0] else CLEAR}
    return ocube(g, name, p, R45, (-ov, -r, -r), (L + ov, r, r), fc)


# ------------------------------------------------------------------ pièces
LAMES, CRIST, EMITS, ROSACES = [], [], [], []


def ecaille(parent, name, root, d, nhint, L, W, var, ofs):
    """Écaille : peau trans_ découpée + arête opaque en losange le long du milieu, en saillie des deux côtés.
    Groupe propre (pivot au pied) pour l'animer."""
    X = unit(d)
    N = unit(np.asarray(nhint, float) - (np.asarray(nhint, float) @ X) * X)
    Y = np.cross(N, X)
    R = np.column_stack([X, Y, N])
    root = np.asarray(root, float) + N * ofs
    g = group(name, root, parent)
    tr = group(f"trans_{name}", root, g)
    sL, sW = L / LS, W / WS
    e = plate(tr, f"peau_{name}", root + X * (L / 2), R, (LS + 2 * MS) * sL, (WS + 2 * MS) * sW, f"ecaille{var % 3}", th=0.3)
    tt = np.linspace(0, 1, 41)
    hw = ecaille_hw(tt, var % 3) * WS / 2 * sW
    e["_pts"] = np.array([((t - 0.5) * L, sg * w, z) for t, w in zip(tt, hw) for sg in (-1, 1) for z in (-0.15, 0.15)])
    pts = [root + X * L * 0.10, root + X * L * 0.44, root + X * L * 0.74]
    bar(g, f"arete0_{name}", pts[0], pts[1], 0.24 * sW, "arete", N, caps=(True, False))
    bar(g, f"arete1_{name}", pts[1], pts[2], 0.15 * sW, "arete", N, caps=(False, True))
    return g, R, root


def cristal(parent, name, base, axis, h, ap, hp, var, spin=0.0, emit=False):
    """Cristal hexagonal (recette effet_givre) : 6 facettes trans_ + pointe en 6 facettes, âme opaque (calque _e)."""
    b = np.asarray(base, float)
    A = unit(axis)
    ref = V(0, 0, 1) if abs(A[2]) < 0.9 else V(1, 0, 0)
    Bx = unit(np.cross(A, ref))
    Rc = np.column_stack([Bx, A, np.cross(Bx, A)])
    g = group(name, b, parent)
    tr = group(f"trans_{name}", b, g)
    wg = 2 * ap * math.tan(math.radians(30)) + 0.06 + 0.02 * ap
    basc = math.degrees(math.atan2(ap, hp))
    lf = math.hypot(ap, hp) + 0.1
    for k in range(6):
        ang = k * 60 + spin
        Rk = Rc @ Ry(90 - ang)
        P = b + Rk @ V(0, h / 2, -(ap + 0.06))
        ocube(tr, f"f{k + 1}_{name}", P, Rk, (-wg / 2, -h / 2, -0.06), (wg / 2, h / 2, 0.06), {"north": F(f"corps{(var + k) % 2}", k % 2 == 1)})
        E = b + Rk @ V(0, h, -(ap + 0.06))
        ocube(tr, f"p{k + 1}_{name}", E, Rk @ Rx(basc), (-wg / 2, 0, -0.06), (wg / 2, lf, 0.06), {"north": F(f"pointe{k % 2}")})
    ga = group(f"ame_{name}", b, g)
    aw = ap * 0.30
    side = F("ame")
    u0, v0, _, _ = UV["ame"]
    cap = [u0, v0, u0 + 4, v0 + 4]
    ocube(ga, f"ame_{name}", b, Rc @ Ry(30 + 11 * var), (-aw, 0.05, -aw), (aw, h * 0.86, aw), {"north": side, "south": side, "east": side, "west": side, "up": cap, "down": CLEAR})
    tip = b + A * (h + hp * 0.85)
    CRIST.append(dict(g=g, ame=ga, h=h, base=b, axis=A, tip=tip))
    if emit:
        EMITS.append(group("emit_scintille" + (str(len(EMITS) + 1) if EMITS else ""), tip, g))
    return g


def epauliere(s, tag, sc, az_h, az_b, crist):
    arm = group("right_arm" if s > 0 else "left_arm", V(s * 5, 22, 0))
    armure = group(f"armure_{tag}", V(s * 6, 24.4, 0), arm)
    # rang bas : jupe d'écailles autour du haut du bras (avant, extérieur, arrière), sous le rang haut ; tangentes à un cylindre
    # autour de l'axe du bras, hors du carré de la seconde couche (2,25 px), un peu évasées vers le bas, l'extérieure la plus longue
    for i, th in enumerate(az_b):
        rr = V(s * math.cos(math.radians(th)), 0, math.sin(math.radians(th)))
        tg = np.cross(V(0, 1, 0), rr)
        sup = 2.25 * (abs(math.cos(math.radians(th))) + abs(math.sin(math.radians(th))))      # support du carré de la seconde couche
        hub = V(s * 6, 25.5, 0) + rr * (sup + 0.5 + 0.2 * (i % 2))
        d = V(0, -1, 0) + rr * 0.17 + tg * 0.06 * (1 if i % 2 else -1)
        L = (5.9 + 1.7 * math.cos(math.radians(th))) * sc
        g, R, root = ecaille(armure, f"bas{i}_{tag}", hub, d, rr, L, 3.9 * sc, i + 1, 0.0)
        LAMES.append(dict(g=g, s=s, rang="bas", i=i))
    # rang haut : coque sur le dessus de l'épaule, s'étale vers l'avant, l'extérieur et l'arrière
    hh = V(s * 5.95, 26.0, 0)
    mid = (len(az_h) - 1) / 2
    maitre = None
    for i, a in enumerate(az_h):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        d = V(s * ca, -0.62, sa * 1.05)
        L = (6.4 if abs(a) < 20 else 5.8 if abs(a) < 45 else 5.0) * sc
        g, R, root = ecaille(armure, f"haut{i}_{tag}", hh, d, V(s * 0.45, 1, sa * 0.45), L, 3.9 * sc, i, 0.16 * (len(az_h) - abs(i - mid)))
        LAMES.append(dict(g=g, s=s, rang="haut", i=i))
        if abs(a) < 1:
            maitre = (g, R, root, L)
    # rosace posée sur l'écaille maîtresse, à 42 % de sa longueur, 0,4 px au-dessus, tournée de 7° (jamais parallèle)
    g, R, root, L = maitre
    gr = group(f"rosace_{tag}", root + R[:, 0] * L * 0.60 + R[:, 2] * 0.42, g)
    Rr = R @ Rx(7) @ np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    c = np.array(groups[gr]["origin"])
    rs = 3.0 * sc
    plate(gr, f"rosace_{tag}", c, Rr, rs, rs, "rosace", th=0.3)
    ocube(gr, f"gemme_{tag}", c, Rr, (-0.42, -0.42, 0.0), (0.42, 0.42, 0.45), {f: F("gemme") for f in ("north", "south", "east", "west", "up", "down")})
    ROSACES.append(gr)
    # crête de givre côté cou : aiguilles blanches, penchées vers l'extérieur
    Rc = frame(V(0, 0, 1), V(s * math.sin(math.radians(14)), math.cos(math.radians(14)), 0))
    plate(armure, f"crete_{tag}", V(s * 5.22, 25.32, 0), Rc, 4.8, 1.75, "crete", th=0.3)
    # grappe de cristaux : (|x|, y, z) base, hauteur, apothème, pointe, bascule vers l'extérieur, dérive avant/arrière
    for k, (bx, by, bz, h, ap, hp, tilt, dz, em) in enumerate(crist):
        ax = V(s * math.sin(math.radians(tilt)), math.cos(math.radians(tilt)), dz)
        cristal(armure, f"cr{k}_{tag}", V(s * bx, by + 0.3, bz), ax, h, ap, hp, k + (1 if s > 0 else 0), spin=23 * k + 7, emit=em)
    return arm


# gauche : plus grande (5 cristaux, rang bas de 5) ; droite : plus sobre (3 cristaux, rang bas de 4)
epauliere(-1, "l", 1.0, (-64, -32, 0, 32, 64), (-80, -42, -4, 36, 76),
          [(6.8, 25.2, 0.2, 9.6, 1.05, 2.6, 12, -0.04, True),
           (7.3, 25.0, -1.5, 6.6, 0.82, 2.0, 30, -0.30, True),
           (7.3, 25.0, 1.6, 5.6, 0.75, 1.8, 34, 0.34, False),
           (7.7, 24.9, 0.6, 3.6, 0.58, 1.4, 48, 0.42, False),
           (6.3, 25.3, -1.0, 3.4, 0.55, 1.3, 6, -0.45, False)])
epauliere(1, "r", 0.9, (-60, -28, 0, 28, 60), (-74, -26, 22, 70),
          [(7.0, 25.0, -0.2, 6.8, 0.9, 2.2, 22, -0.10, True),
           (7.6, 24.9, 1.4, 4.6, 0.7, 1.6, 40, 0.30, False),
           (7.4, 24.9, -1.6, 3.6, 0.58, 1.4, 34, -0.36, False)])

PART = group("particle_scintille", V(0, 0, 0))
ocube(PART, "scintille", V(0, 0.75, 0), np.eye(3), (-0.35, -0.35, -0.15), (0.35, 0.35, 0.15),
      {"south": F("star"), "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


# ------------------------------------------------------------------ contrôle des distances au repos (seconde couche du skin)
def points(e, n=5):
    if "_pts" in e:
        return (e["_R"] @ e["_pts"].T).T + e["origin"]
    lo, hi = np.array(e["from"]) - e["origin"], np.array(e["to"]) - e["origin"]
    g = [np.linspace(lo[k], hi[k], n) for k in range(3)]
    P = np.array([(x, y, z) for x in g[0] for y in g[1] for z in g[2]
                  if x in (lo[0], hi[0]) or y in (lo[1], hi[1]) or z in (lo[2], hi[2])])
    return (e["_R"] @ P.T).T + e["origin"]


def dedans(P, lo, hi, m):
    return np.all((P > np.array(lo) - m) & (P < np.array(hi) + m), axis=1)


ERR = []
for e in elements:
    if e["name"] == "scintille":
        continue
    P = points(e)
    sx = 1 if P[:, 0].mean() > 0 else -1
    bras = dedans(P * [sx, 1, 1], (3.75, 12, -2.25), (8.25, 24.25, 2.25), 0.1)
    tete = dedans(P, (-4.5, 24, -4.5), (4.5, 32.5, 4.5), 0.15)
    torse = dedans(P, (-4.25, 12, -2.25), (4.25, 24.25, 2.25), 0.1)
    for nm, m in (("bras", bras), ("tete", tete), ("torse", torse)):
        if m.any():
            ERR.append(f"{e['name']} touche la seconde couche ({nm}) : {np.round(P[m][0], 2)}")
assert not ERR, " | ".join(ERR)
for e in elements:
    e.pop("_R")
    e.pop("_pts", None)


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [bone("right_arm"), bone("left_arm"), bone(PART)]


# ------------------------------------------------------------------ animations
# MIROIR D'AXES (guide 3) : +Z = le côté droit monte. Une écaille qui pend du côté s s'écarte du bras par une rotation Z de s * out.
def ecarte(s, out, back=0.0):
    return back, 0.0, s * out


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 3)), "y": str(round(y + 0.0, 3)), "z": str(round(z + 0.0, 3))}],
            "time": round(t, 3), "interpolation": "linear"}


def anim(name, length, tracks, loop="loop", fps=10):
    n = max(6, int(round(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A = {}
    for g, chans in tracks.items():
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(ch, t, *f(t)) for ch, f in chans for t in times]}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


def etat(name, L, cycles, rest, amp, tremble=0.0, frisson=None):
    """Écailles basses : écart au repos + battement au pas ; écailles hautes : un tiers ; cristaux : petits tremblements rigides."""
    tr = {}
    for la in LAMES:
        s, i = la["s"], la["i"]
        k = 1.0 if la["rang"] == "bas" else 0.3
        ph0 = 0.09 * i + (0.27 if s > 0 else 0) + (0.0 if la["rang"] == "bas" else 0.15)

        def f(t, s=s, k=k, ph0=ph0, i=i):
            ph = TAU * (cycles * t / L - ph0)
            fr = frisson(t, ph0) if frisson else 0.0
            return ecarte(s, k * (rest + amp * math.sin(ph) + fr), k * 0.4 * amp * math.cos(ph) * (1 if i % 2 else -1))
        tr[la["g"]] = [("rotation", f)]
    for j, c in enumerate(CRIST):
        s = 1 if c["base"][0] > 0 else -1
        ph0 = 0.21 * j

        def f(t, s=s, ph0=ph0):
            ph = TAU * (2 * cycles * t / L - ph0)
            fr = 1.4 * frisson(t, ph0 + 0.3) if frisson else 0.0
            return ecarte(s, tremble * math.sin(ph) + 0.6 * fr, 0.5 * tremble * math.sin(ph + 1.3))
        tr[c["g"]] = [("rotation", f)]
    return anim(name, L, tr, fps=10 if L > 3 else 16)


def frisson_idle(t, ph):
    """Deux frissons de givre brefs sur 8 s (3 Hz, 24 périodes : boucle fermée)."""
    w = bump(t, 2.4, 2.7, 3.2, 3.7) + 0.6 * bump(t, 6.0, 6.25, 6.6, 7.0)
    return 0.9 * w * math.sin(TAU * (3 * t - ph))


idle = etat("idle", 8.0, 2, 0.4, 0.45, tremble=0.0, frisson=frisson_idle)
idle_n = len(idle["animators"])
walk = etat("walk", 1.6, 2, 1.2, 1.4, tremble=0.5)
run = etat("run", 1.0, 2, 3.0, 2.6, tremble=1.0)
sneak = etat("sneak", 3.0, 1, -0.6, 0.35, tremble=0.0)


def overlay_anim():
    """4 s, permanente : les âmes des cristaux respirent (lumière qui pulse dans la glace), déphasées."""
    L = 4.0
    tr = {}
    for j, c in enumerate(CRIST):
        ph = 1.1 * j
        tr[c["ame"]] = [("scale", lambda t, ph=ph: (1 + 0.08 * math.sin(TAU * t / L + ph), 1 + 0.02 * math.sin(TAU * t / L + ph), 1 + 0.08 * math.sin(TAU * t / L + ph)))]
    return anim("overlay_givre", L, tr, fps=8)


def equip_anim():
    """1,5 s : la coque pousse depuis l'épaule (0–0,4 s), les écailles basses tombent en place avec un rebond (0,15–0,7 s),
    les cristaux jaillissent un à un, grands d'abord (0,35–1,2 s), la rosace se pose (0,9–1,3 s). Dernière image : repos."""
    L = 1.5
    tr = {}

    def pop(t0, d=0.4, ov=0.14):
        def f(t):
            u = (t - t0) / d
            if u <= 0:
                return (0.0,) * 3
            if u >= 1.5:
                return (1.0,) * 3
            g = 1 - math.exp(-5 * u) * math.cos(4.4 * u)
            g = g * (1 - sm(u, 1.1, 1.5)) + sm(u, 1.1, 1.5)
            g = max(0.0, g)
            return (g,) * 3
        return f
    for tag in ("l", "r"):
        tr[f"armure_{tag}"] = [("scale", lambda t: (0.15 + 0.85 * sm(t, 0.0, 0.4),) * 3)]
    for la in LAMES:
        if la["rang"] == "bas":
            s, i = la["s"], la["i"]
            t0 = 0.15 + 0.06 * i
            tr[la["g"]] = [("rotation", lambda t, s=s, t0=t0: ecarte(s, 26 * (1 - sm(t, t0, t0 + 0.35)) - 4 * bump(t, t0 + 0.3, t0 + 0.38, t0 + 0.42, t0 + 0.6)))]
    order = sorted(range(len(CRIST)), key=lambda j: -CRIST[j]["h"])
    for rank, j in enumerate(order):
        tr[CRIST[j]["g"]] = [("scale", pop(0.35 + 0.1 * rank))]
    for gr in ROSACES:
        tr[gr] = [("scale", pop(0.9, d=0.3))]
    a = anim("event_equip", L, tr, loop="once", fps=24)
    a["animators"]["effects"] = {"name": "Effects", "type": "effect",
                                 "keyframes": [{"channel": "sound", "data_points": [{"effect": "block.amethyst_block.chime", "file": ""}], "time": 0.4}]}
    return a


def particle_anim():
    L = 1.2
    return anim("particle_scintille_fall", L, {PART: [("scale", lambda t: (1 + 0.35 * math.sin(TAU * t / L),) * 3)]}, fps=10)


ANIMS = [idle, walk, run, sneak, overlay_anim(), equip_anim(), particle_anim()]
assert 2 <= len(EMITS) <= 4

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
from sons import limiter_sons
limiter_sons(model)
from reactions import retirer_reactions
retirer_reactions(model)
from ambiance import ajouter_ambiance
ajouter_ambiance(model, foyer=1.0)
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in model["outliner"]), ";", len(model["animations"]), "anims ;",
      sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      len(EMITS), "emit_")
