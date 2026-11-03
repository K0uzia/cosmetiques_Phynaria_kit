"""Oreilles de lapin-nuage : deux grandes oreilles molles et dodues, la gauche pliée à mi-hauteur, intérieur rose,
petit nœud lavande à la base de la droite, touffes de nuage qui cachent l'attache. Design original, thème kawaii.
Première pièce de l'ensemble « Nuage Guimauve » : elle fixe la palette (crème / blanc rosé, rose, lavande).
Écrit oreilles_lapin_nuage.png, oreilles_lapin_nuage_e.png et .build/oreilles_lapin_nuage_brut.bbmodel à côté de ce script.

Recette peau + âme (Aurelion) : chaque segment d'oreille = peau avant (rose) + peau arrière (crème), plaques découpées
par alpha à tranches transparentes, autour de deux noyaux pleins plus étroits (croix de section) qui remplissent l'épaisseur.
Ancrage sur le dessus de la tête au-dessus des tempes (z ≈ -0,3, recette « Corne »). Groupe de premier niveau head.
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

AVEC_E = True       # calque _e embarqué en seconde texture (bug du mod annoncé corrigé ; jamais assigné aux faces)
NOM = "oreilles_lapin_nuage"
TEX = 512
TAU = 2 * math.pi

# ------------------------------------------------------------------ palette « Nuage Guimauve » (base poussée vers le blanc : la lumière chaude la réchauffe)
CREME = (255, 249, 247)
CREME_OMB = (228, 218, 240)      # ombre froide (lavande grisée) : compense le saumon des lumières chaudes
BLANC = (255, 255, 255)
ROSE_L = (255, 210, 226)
ROSE_D = (246, 174, 204)
ROSE_LIS = (234, 152, 188)       # liseré de l'intérieur
LAV = (208, 192, 248)
LAV_D = (168, 146, 228)
LAV_LIS = (146, 124, 206)
LAV_HI = (242, 236, 255)
E_FOND = (13, 10, 18)            # fond additif très sombre
E_ROSE = (104, 52, 80)           # liseré rose doux
E_LAV = (118, 102, 172)          # reflet du nœud


def lerp(a, b, k):
    return a + (b - a) * k


def col(c):
    return np.array(c, np.float32)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def mix(base, c, k):
    """base : HxWx3 ; c : couleur ; k : HxW (0..1)."""
    return lerp(base, col(c), np.clip(k, 0, 1)[..., None])


# ------------------------------------------------------------------ forme de l'oreille (px du modèle ; v = de la racine vers la pointe)
EL1, ETOT = 4.4, 9.4      # longueur du segment bas, longueur totale
VMAX, HWMAX = 5.2, 1.75


def hw(v):
    """Demi-largeur : racine étroite, ventre dodu, pointe en demi-ellipse."""
    v = np.asarray(v, np.float64)
    lo = 0.85 + (HWMAX - 0.85) * smooth(np.clip(v, 0, VMAX) / VMAX)
    hi = HWMAX * np.sqrt(np.clip(1 - ((v - VMAX) / (ETOT - VMAX)) ** 2, 0, 1))
    return np.where(v <= VMAX, lo, hi)


CAP = float(hw(EL1))      # chaque segment finit au pli par un demi-disque centré sur l'articulation :
                          # le pli tourne autour de ce centre, le coude reste rond quel que soit l'angle


def hw_seg(v, seg):
    """Contour d'un segment (sur l'axe) : bas = demi-disque au-dessus de EL1, haut = en dessous."""
    v = np.asarray(v, np.float64)
    h = hw(v)
    cap = np.sqrt(np.clip(CAP ** 2 - (v - EL1) ** 2, 0, None))
    if seg == "lo":
        return np.where(v <= EL1, h, cap)
    return np.where(v >= EL1, h, cap)


# Pli de chaque oreille : (côté, pli dans le plan vers l'extérieur, bascule arrière) en degrés.
# La gauche retombe sur le côté ; la droite est à peine courbée.
BENDS = {"l": (-1, 108, 0), "r": (+1, 8, 0)}


def bendmap(X, Y, seg, phi):
    """Coordonnées (x le long de X de l'oreille, v) -> point à peindre. Le demi-disque d'un segment couvre la zone de l'autre :
    on y peint ce que l'autre segment, tourné de phi autour de l'articulation, montre à cet endroit. Coude sans couture."""
    c, s_ = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    dx, dv = X, Y - EL1
    if seg == "lo":      # point du bas, au-dessus du pli : coordonnées dans le segment haut déplié
        x2, v2 = dx * c + dv * s_, -dx * s_ + dv * c
        use = (Y > EL1) & (v2 > 0)
    else:                # point du haut, sous le pli : coordonnées dans le segment bas
        x2, v2 = dx * c - dv * s_, dx * s_ + dv * c
        use = (Y < EL1) & (v2 < 0)
    # secteur du coude couvert par les seuls demi-disques : motif radial (anneau crème, disque rose), le rose tourne avec le pli
    cap = (Y > EL1) if seg == "lo" else (Y < EL1)
    rad = cap & ~use
    r = np.hypot(dx, dv)
    return np.where(use, x2, np.where(rad, r, X)), np.where(use, v2 + EL1, np.where(rad, EL1, Y))


def hw_in(v):
    """Intérieur rose : plus étroit, fermé avant la pointe, bas arrondi."""
    v = np.asarray(v, np.float64)
    return np.maximum(0, hw(v + 0.55) * 0.64 - 0.12) * np.sqrt(smooth((v - 0.35) / 1.1))


SEG_V = {"lo": (-0.4, EL1 + CAP), "hi": (EL1 - CAP, ETOT + 0.05)}


# ------------------------------------------------------------------ images (fonctions de px du modèle, peintes au moment de l'atlas)
def ear_front(seg, phi):
    def f(X, Y):
        m = np.abs(X) <= hw_seg(Y, seg)
        X, Y = bendmap(-X, Y, seg, phi)      # peau avant : u de l'image croît vers -X de l'oreille
        a = np.abs(X)
        h, hi_ = hw(np.maximum(Y, 0)), hw_in(Y)
        c = np.empty(X.shape + (3,), np.float32)
        c[...] = CREME
        d_edge = hw(Y) - a
        c = mix(c, CREME_OMB, (0.17 - d_edge) / 0.08 * 0.9)                 # liseré d'ombre froide au contour (≥ 4 texels)
        inner = a < hi_
        q = a / np.maximum(hi_, 1e-3)
        ci = lerp(col(ROSE_D), col(ROSE_L), (np.clip(q, 0, 1) ** 0.8)[..., None])
        ci = mix(ci, ROSE_LIS, (np.abs(X) < 0.09) * 0.45 * smooth((Y - 0.8) / 1.5))   # pli central
        ci = mix(ci, ROSE_LIS, (q - 0.8) / 0.12)                              # liseré de l'intérieur
        c = np.where(inner[..., None], ci, c)
        c = mix(c, BLANC, ((a > hi_) & (a < hi_ + 0.18) & (Y > 0.6)) * 0.7)  # bourrelet clair autour du rose
        c = c * (1 + 0.025 * np.sin(X * 23 + Y * 4))[..., None]
        e = np.empty_like(c)
        e[...] = E_FOND
        e = mix(e, E_ROSE, inner & (q > 0.8) & (q < 0.97))
        return m, c, e
    return f


def ear_back(seg, phi):
    def f(X, Y):
        m = np.abs(X) <= hw_seg(Y, seg)
        X, Y = bendmap(X, Y, seg, phi)
        a = np.abs(X)
        h = hw(Y)
        q = a / np.maximum(hw(np.maximum(Y, 0)), 1e-3)
        c = np.empty(X.shape + (3,), np.float32)
        c[...] = CREME
        c = mix(c, CREME_OMB, smooth((q - 0.5) / 0.5) ** 1.4 * 0.85)
        c = mix(c, BLANC, (1 - q / 0.3) * 0.8)                               # arête claire au centre
        c = mix(c, (252, 232, 240), (1 - Y / 1.2) * 0.5)                    # pied légèrement rosé
        c = mix(c, CREME_OMB, (0.15 - (h - a)) / 0.07 * 0.8)
        c = c * (1 + 0.03 * np.sin(X * 6 + Y * 19 + np.sin(X * 3) * 2))[..., None]   # duvet
        e = np.empty_like(c)
        e[...] = E_FOND
        return m, c, e
    return f


def ellipse_val(X, Y, cx, cy, rx, ry, ang):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    dx, dy = X - cx, Y - cy
    a, b = dx * c + dy * s, -dx * s + dy * c
    return np.sqrt((a / rx) ** 2 + (b / ry) ** 2), b


def bow(X, Y):
    c = np.empty(X.shape + (3,), np.float32)
    c[...] = LAV
    e = np.empty_like(c)
    e[...] = E_FOND
    m = np.zeros(X.shape, bool)
    # rubans qui pendent
    for s in (-1, 1):
        ev, _ = ellipse_val(X, Y, s * 0.42, -0.55, 0.22, 0.55, s * 28)
        t = ev <= 1
        m |= t
        c = np.where(t[..., None], mix(mix(np.broadcast_to(col((196, 178, 242)), c.shape).copy(), LAV_LIS, (ev - 0.72) / 0.12), LAV_D, (Y + 0.15) * -0.6), c)
    # boucles
    for s in (-1, 1):
        ev, b = ellipse_val(X, Y, s * 0.86, 0.12, 0.82, 0.58, s * 12)
        t = ev <= 1
        m |= t
        cl = np.broadcast_to(col(LAV), c.shape).copy()
        cl = mix(cl, LAV_D, (1 - np.abs(X) / 0.9) * 0.8)                    # creux vers le nœud
        cl = mix(cl, LAV_LIS, (ev - 0.8) / 0.1)
        hi = (ev > 0.38) & (ev < 0.66) & (b > 0.12) & (np.abs(X) > 0.55)
        cl = mix(cl, LAV_HI, hi * 0.95)
        c = np.where(t[..., None], cl, c)
        e = np.where((t & hi)[..., None], mix(e, E_LAV, np.ones(X.shape)), e)
    # nœud central
    ev, b = ellipse_val(X, Y, 0, 0.06, 0.36, 0.40, 0)
    t = ev <= 1
    m |= t
    ck = np.broadcast_to(col((186, 166, 236)), c.shape).copy()
    ck = mix(ck, LAV_LIS, (ev - 0.75) / 0.12)
    spot = ellipse_val(X, Y, -0.08, 0.18, 0.13, 0.1, 0)[0] < 1
    ck = mix(ck, LAV_HI, spot * 1.0)
    c = np.where(t[..., None], ck, c)
    e = np.where((t & spot)[..., None], mix(e, E_LAV, np.ones(X.shape)), e)
    return m, c, e


CIRC_SIDE = [(-1.05, 0.62, 0.62), (-0.2, 1.02, 0.82), (0.85, 0.75, 0.7), (1.22, 0.45, 0.45)]
CIRC_TOP = [(-0.7, 0.2, 0.75), (0.5, 0.35, 0.8), (0.1, -0.45, 0.8), (1.0, -0.3, 0.55), (-1.05, -0.35, 0.5)]


def cloud(circles, base_rect=None, ground=True):
    def f(X, Y):
        sdf = np.full(X.shape, 9.0)
        for cx, cy, r in circles:
            sdf = np.minimum(sdf, np.hypot(X - cx, Y - cy) - r)
        if base_rect:
            x0, x1, y0, y1 = base_rect
            sdf = np.minimum(sdf, np.maximum(np.maximum(x0 - X, X - x1), np.maximum(y0 - Y, Y - y1)))
        m = sdf <= 0
        c = np.empty(X.shape + (3,), np.float32)
        c[...] = BLANC
        if ground:
            c = mix(c, CREME_OMB, (1 - Y / 0.8) * 0.75)
        c = mix(c, (236, 228, 246), (sdf + 0.14) / 0.06 * 0.9)
        # séparation des boules : fines ombres là où deux cercles se rencontrent
        st = np.sort(np.stack([np.hypot(X - cx, Y - cy) - r for cx, cy, r in circles]), axis=0)
        c = mix(c, (238, 232, 248), ((np.abs(st[0] - st[1]) < 0.06) & (st[1] < -0.05)) * 0.7)
        e = np.empty_like(c)
        e[...] = E_FOND
        return m, c, e
    return f


def tile(color, dark):
    def f(X, Y):
        c = np.empty(X.shape + (3,), np.float32)
        c[...] = color
        c = mix(c, dark, (np.abs(Y) / 0.5) ** 2 * 0.35)
        e = np.empty_like(c)
        e[...] = E_FOND
        return np.ones(X.shape, bool), c, e
    return f


# nom -> (x0, x1, y0, y1 en px du modèle, peintre, taille fixe en texels ou None)
IMAGES = {}
for tag, (s_, bend, _) in BENDS.items():
    for seg in ("lo", "hi"):
        v0, v1 = SEG_V[seg]
        IMAGES[f"av_{seg}_{tag}"] = ((-HWMAX - 0.05, HWMAX + 0.05, v0, v1), ear_front(seg, -s_ * bend), None)
        IMAGES[f"ar_{seg}_{tag}"] = ((-HWMAX - 0.05, HWMAX + 0.05, v0, v1), ear_back(seg, -s_ * bend), None)
IMAGES["noeud"] = ((-1.72, 1.72, -1.12, 0.74), bow, None)
IMAGES["nuage_f"] = ((-1.7, 1.7, 0.0, 1.86), cloud(CIRC_SIDE, (-1.45, 1.45, 0.02, 0.62)), None)
IMAGES["nuage_c"] = ((-1.3, 1.3, 0.0, 1.66), cloud([(-0.75, 0.6, 0.55), (0.05, 0.95, 0.7), (0.85, 0.6, 0.5)], (-1.15, 1.15, 0.02, 0.6)), None)
IMAGES["nuage_h"] = ((-1.62, 1.62, -1.27, 1.17), cloud(CIRC_TOP, ground=False), None)
IMAGES["t_creme"] = ((-0.5, 0.5, -0.5, 0.5), tile(CREME, CREME_OMB), 8)
IMAGES["t_blanc"] = ((-0.5, 0.5, -0.5, 0.5), tile(BLANC, CREME_OMB), 8)
IMAGES["t_lav"] = ((-0.5, 0.5, -0.5, 0.5), tile((184, 164, 234), LAV_LIS), 8)

UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
tex_b64 = tex_e_b64 = None


def render_image(box, painter, W, H, ss=3):
    x0, x1, y0, y1 = box
    jj, ii = np.mgrid[0:H * ss, 0:W * ss]
    X = x0 + (ii + 0.5) / (W * ss) * (x1 - x0)
    Y = y1 - (jj + 0.5) / (H * ss) * (y1 - y0)
    m, c, e = painter(X, Y)
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    erg = np.array(Image.fromarray(np.clip(e, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS))
    al = np.array(Image.fromarray((m * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110
    if al.any():
        rgb[~al] = rgb[al].mean(axis=0).astype(np.uint8)   # pas de frange sombre au filtrage
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    eo = np.dstack([erg, al * 255]).astype(np.uint8)
    eo[~al] = 0
    return out, eo


def atlas():
    """Range les images à la densité la plus haute qui tient, peint, écrit les deux PNG."""
    global tex_b64, tex_e_b64

    def sizes(dens):
        out = []
        for n, (box, _, fixed) in IMAGES.items():
            if fixed:
                out.append((n, fixed, fixed))
            else:
                out.append((n, int(math.ceil((box[1] - box[0]) * dens)), int(math.ceil((box[3] - box[2]) * dens))))
        return out

    def pack(dens):
        items = sorted(sizes(dens), key=lambda it: -it[2])
        uv, x, y, shelf = {}, 0, 0, 0
        for n, w, h in items:
            if x + w + 1 > TEX:
                x, y, shelf = 0, y + shelf + 1, 0
            if y + h > TEX - 6 or w > TEX:
                return None
            uv[n] = (x, y, x + w, y + h)
            x += w + 1
            shelf = max(shelf, h)
        return uv

    dens = 40.0
    while (uv := pack(dens)) is None:
        dens -= 0.25
    UV.update(uv)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, (box, painter, _) in IMAGES.items():
        u0, v0, u1, v1 = UV[n]
        im, ie = render_image(box, painter, u1 - u0, v1 - v0)
        tex[v0:v1, u0:u1], tex_e[v0:v1, u0:u1] = im, ie
    assert tex[TEX - 3, TEX - 3, 3] == 0
    assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
    b64 = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        b64.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    tex_b64, tex_e_b64 = b64
    return dens


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
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx, ordre du mod et du renderer."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def rodrigues(k, deg):
    k = unit(k)
    t = math.radians(deg)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) * math.cos(t) + math.sin(t) * K + (1 - math.cos(t)) * np.outer(k, k)


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(float(v), 2) for v in rotation]}
    return name


def box(g, name, c, R, size, faces):
    """Cube orienté : centre c, axes locaux = colonnes de R, dimensions size."""
    c, size = np.asarray(c, float), np.asarray(size, float)
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in c - size / 2],
         "to": [round(float(v), 3) for v in c + size / 2], "origin": [round(float(v), 3) for v in c], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    rot = euler(R)
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def frame(X, Y):
    X, Y = unit(X), unit(Y)
    return np.column_stack([X, Y, np.cross(X, Y)])


def plate(g, name, c, X, Y, img, th=0.3):
    """Plaque à une face (south = côté X × Y), contour par l'alpha, autres faces sur un texel transparent.
    Le haut de l'image est +Y, u croît vers X ; la taille vient de la boîte de l'image."""
    x0, x1, y0, y1 = IMAGES[img][0]
    u0, v0, u1, v1 = UV[img]
    faces = {"south": [u0, v0, u1, v1], "north": CLEAR, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
    box(g, name, c, frame(X, Y), (x1 - x0, y1 - y0, th), faces)


def solid(g, name, c, R, size, t="t_creme"):
    u0, v0, u1, v1 = UV[t]
    uv = [u0 + 1, v0 + 1, u1 - 1, v1 - 1]
    box(g, name, c, R, size, {f: uv for f in ("north", "south", "east", "west", "up", "down")})


def octo(g, name, p, q, r, t="t_creme"):
    """Barre à section octogonale (deux cubes à 45°) de p à q."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    X = unit(q - p)
    ref = V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0)
    Y = unit(ref - (ref @ X) * X)
    Z_ = np.cross(X, Y)
    L = np.linalg.norm(q - p)
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    solid(g, name, (p + q) / 2, np.column_stack([X, Y, Z_]), (L, 2 * r, 2 * r), t)
    solid(g, name + "o", (p + q) / 2, np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_]), (L - 0.06, 2 * r * 0.97, 2 * r * 0.97), t)


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


DENS = atlas()

SKIN, EMBED = 0.3, 0.12
T_LO, T_HI = 1.1, 1.0          # épaisseur totale de chaque segment (dodu)
EARS = {}


def segment(g, tag, seg, root, R, T, depth_ofs, pieces):
    """Un segment d'oreille : peau avant + peau arrière + noyaux en croix. R = [X largeur, u longueur, N vers le dos]."""
    X, u, N = R[:, 0], R[:, 1], R[:, 2]
    v0, v1 = SEG_V[seg]
    vc = (v0 + v1) / 2
    zf = -T / 2 + SKIN / 2 + depth_ofs
    zb = T / 2 - SKIN / 2 - depth_ofs
    # peau avant : vue de face, u croît vers -X pour que l'image se lise dans le bon sens
    plate(g, f"av_{seg}_{tag}", root + u * vc + N * zf, -X, u, f"av_{seg}_{tag}")
    plate(g, f"ar_{seg}_{tag}", root + u * vc + N * zb, X, u, f"ar_{seg}_{tag}")
    inner = T - 2 * SKIN + 2 * EMBED - 2 * depth_ofs
    K = 0.86
    for j, (a, b) in enumerate(pieces):
        # deux demi-noyaux dont le bord extérieur suit le contour (polyligne, pas de marches)
        for sg in (-1, 1):
            pa, pb = np.array([sg * K * float(hw(max(a, 0))), a]), np.array([sg * K * float(hw(max(b, 0))), b])
            e2 = (pb - pa) / np.linalg.norm(pb - pa)
            ew = unit(X * e2[0] + u * e2[1])
            Xp = np.cross(ew, N)                            # perpendiculaire au bord, dans le plan
            inward = -sg * np.sign(Xp @ X) * Xp
            W = K * float(hw(max((a + b) / 2, 0))) + 0.08
            mid = (pa + pb) / 2
            c = root + X * mid[0] + u * mid[1] + inward * (W / 2)
            solid(g, f"ame{j}{'g' if sg < 0 else 'd'}_{seg}_{tag}", c, np.column_stack([Xp, ew, N]),
                  (W, np.linalg.norm(pb - pa) + 0.12, inner - 0.03 * (sg > 0) - 0.02 * (j % 2)))

def ear(s, tag, root, bend, tilt):
    """bend : pli dans le plan de l'oreille, le bout part vers l'extérieur (degrés) ; tilt : puis bascule vers l'arrière (> 0) ou l'avant."""
    u = unit(V(s * 0.2, 1, 0.1))                         # s'écarte un peu et part à peine en arrière
    f = V(s * 0.35, 0, -1)                               # l'ouverture regarde vers l'avant et un peu dehors
    N = unit(-f - ((-f) @ unit(u)) * unit(u))
    X = np.cross(u, N)
    R = np.column_stack([X, u, N])
    g = group(f"oreille_{tag}", root)
    J = root + u * EL1
    segment(g, tag, "lo", root, R, T_LO, 0.0, [(-0.35, 0.6), (0.6, 1.5), (1.5, 2.4), (2.4, 3.4), (3.4, EL1)])
    # coude : galet octogonal d'axe N, centré sur l'articulation, entre les deux peaux (comble le pli vu de profil)
    h = (T_HI - 2 * SKIN + 2 * EMBED) / 2 - 0.03
    octo(g, f"coude_{tag}", J - N * h, J + N * h, CAP * 0.66)
    gb = group(f"bout_{tag}", J, parent=g)
    gp = group(f"pli_{tag}", J, parent=gb, rotation=euler(rodrigues(X, tilt) @ rodrigues(N, -s * bend)))
    segment(gp, tag, "hi", root, R, T_HI, 0.0, [(EL1, 5.6), (5.6, 6.5), (6.5, 7.3), (7.3, 8.0), (8.0, 8.6), (8.6, 9.0)])
    EARS[tag] = (g, gb, s)


def tuft(s, tag, c):
    """Touffe de nuage qui cache l'attache : noyau blanc, quatre nuages verticaux, un nuage posé dessus."""
    g = group(f"nuage_{tag}", c, parent=None)
    core = V(2.0, 0.95, 1.5)
    solid(g, f"coeur_{tag}", c + V(0, core[1] / 2, 0), np.eye(3), core, "t_blanc")
    y_bot = c[1]
    hf = IMAGES["nuage_f"][0][3]
    hc = IMAGES["nuage_c"][0][3]
    plate(g, f"nf_{tag}", V(c[0], y_bot + hf / 2, c[2] - core[2] / 2 - 0.12), V(-1, 0, 0), V(0, 1, 0), "nuage_f")
    plate(g, f"nd_{tag}", V(c[0] + 0.05 * s, y_bot + hf / 2 - 0.08, c[2] + core[2] / 2 + 0.12), V(1, 0, 0), V(0, 1, 0), "nuage_f")
    plate(g, f"ne_{tag}", V(c[0] + core[0] / 2 + 0.12, y_bot + hc / 2, c[2]), V(0, 0, -1), V(0, 1, 0), "nuage_c")
    plate(g, f"nw_{tag}", V(c[0] - core[0] / 2 - 0.12, y_bot + hc / 2 - 0.05, c[2] + 0.04), V(0, 0, 1), V(0, 1, 0), "nuage_c")
    plate(g, f"nh_{tag}", V(c[0], y_bot + core[1] + 0.13, c[2]), V(1, 0, 0), V(0, 0, -1), "nuage_h")
    return g


def bow_piece(c, s):
    """Nœud lavande : deux plaques découpées + noyaux pleins (nœud central, boucles)."""
    g = group("noeud", c)
    f = unit(V(s * 0.35, 0.0, -1))
    Xb = unit(np.cross(V(0, 1, 0), f))     # vu de face, u croît vers la droite de l'observateur
    Y = V(0, 1, 0)
    plate(g, "noeud_av", c + f * 0.3, Xb, Y, "noeud")
    plate(g, "noeud_ar", c - f * 0.3, -Xb, Y, "noeud")
    Rb = np.column_stack([Xb, Y, np.cross(Xb, Y)])
    solid(g, "noeud_c", c + Y * 0.06, Rb, (0.56, 0.6, 0.56), "t_lav")
    for k, sx in enumerate((-1, 1)):
        solid(g, f"boucle{k}", c + Xb * (sx * 0.85) + Y * 0.12, Rb, (0.5, 0.4, 0.4 + 0.02 * k), "t_lav")
    return g


# Racines sur le dessus de la tête, au-dessus des tempes ; la gauche (-X) est pliée vers l'avant, la droite à peine courbée.
ear(-1, "l", V(-2.3, 31.75, -0.3), *BENDS["l"][1:])
ear(+1, "r", V(2.3, 31.75, -0.3), *BENDS["r"][1:])
tuft(-1, "l", V(-2.3, 31.85, -0.3))
tuft(+1, "r", V(2.3, 31.85, -0.3))
bow_piece(V(2.75, 32.75, -1.75), +1)

top = ["nuage_l", "nuage_r", "oreille_l", "oreille_r", "noeud"]
outliner = [{"name": "head", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone_node(n) for n in top]}]


# ------------------------------------------------------------------ animations
# Intention sur un côté s (-1 gauche, +1 droite) : back > 0 = le haut part vers l'arrière ; out > 0 = le haut s'écarte vers
# l'extérieur (pour le bout plié de gauche, qui pend sur le côté : il tombe davantage ; out < 0 le relève) ;
# sweep > 0 = le côté extérieur part vers l'arrière (le bout plié est rabattu par le vent).
# MIROIR D'AXES : seul endroit à toucher si la convention change. Guide, section 3 : +X = le haut bascule vers l'arrière ;
# +Y = le côté droit avance ; +Z = le côté droit monte, donc le haut d'une pièce verticale part vers -X.
SX, SY, SZ = +1, -1, -1


def mirror(s, back, out, sweep=0.0):
    return SX * back, s * SY * sweep, s * SZ * out


def kf(t, x, y, z):
    return {"channel": "rotation", "data_points": [{"x": str(round(x + 0.0, 2)), "y": str(round(y + 0.0, 2)), "z": str(round(z + 0.0, 2))}],
            "time": round(t, 3), "interpolation": "linear"}


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    x = (t - a) / (b - a)
    return x * x * (3 - 2 * x)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def anim(name, length, tracks, n_kf=None, loop="loop"):
    """tracks : groupe -> fonction t -> (x, y, z) en valeurs de keyframe ; linéaire, dernière clé = première."""
    n = n_kf or max(8, int(round(length * 10)))
    times = [i * length / n for i in range(n + 1)]
    A = {groups[g]["uuid"]: {"name": g, "type": "bone", "keyframes": [kf(t, *f(t)) for t in times]} for g, f in tracks.items()}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "idle", "animators": A}


def state(name, L, back, out, tip, bob=0.0, bob_cyc=1, flut=0.0, flut_cyc=0, extra=None, n_kf=None):
    """back, out : pose des racines ; tip[tag] = (back, out, sweep) du bout ; bob : rebond (cycles entiers) ; flut : frémissement au vent.
    Le bout plié de gauche rebondit de haut en bas (out), le bout droit d'avant en arrière (back).
    extra(t, tag) -> (d_back, d_out, d_tip_back, d_tip_out) pour les tressaillements."""
    tr = {}
    for tag, (g, gb, s) in EARS.items():
        ph = 0.0 if s < 0 else 0.6

        def root_f(t, s=s, ph=ph, tag=tag):
            w = TAU * bob_cyc * t / L + ph
            fl = flut * math.sin(TAU * flut_cyc * t / L + 2 * ph)
            ex = extra(t, tag) if extra else (0, 0, 0, 0)
            return mirror(s, back + bob * math.sin(w) + fl + ex[0], out + 0.35 * bob * math.sin(w + 0.7) + ex[1])

        def tip_f(t, s=s, ph=ph, tag=tag):
            w = TAU * bob_cyc * t / L + ph - 0.9          # le bout suit avec retard
            fl = flut * 1.6 * math.sin(TAU * flut_cyc * t / L + 2 * ph - 1.0)
            ex = extra(t, tag) if extra else (0, 0, 0, 0)
            tb, to, tw = tip[tag]
            if tag == "l":
                return mirror(s, tb + 0.4 * bob * math.sin(w) + ex[2], to + 2.0 * bob * math.sin(w) + fl + ex[3], tw + 0.6 * fl)
            return mirror(s, tb + 1.2 * bob * math.sin(w) + 0.6 * fl + ex[2], to + 0.5 * bob * math.sin(w + 0.5) + ex[3], tw)
        tr[g], tr[gb] = root_f, tip_f
    return anim(name, L, tr, n_kf=n_kf)


def idle_extra(t, tag):
    """Tressaillement de l'oreille droite vers 2,5 s ; le bout plié de la gauche se relève et se secoue vers 6 s."""
    if tag == "r":
        k = bump(t, 2.4, 2.55, 2.85, 3.3)
        sh = math.sin(TAU * 7 * t) * bump(t, 2.45, 2.6, 2.9, 3.25)
        return (9 * k, 4 * sh, 6 * k, 5 * sh)
    k = bump(t, 5.8, 6.0, 6.25, 6.8)
    sh = math.sin(TAU * 6 * t) * bump(t, 5.85, 6.0, 6.3, 6.7)
    return (2 * k, 0, 3 * sh, -18 * k + 6 * sh)


Z3 = {"l": (0, 0, 0), "r": (0, 0, 0)}
idle = state("idle", 8.0, 0, 0, Z3, bob=1.4, bob_cyc=2, extra=idle_extra, n_kf=96)
walk = state("walk", 1.6, 6, 2, {"l": (0, 0, 8), "r": (4, 0, 0)}, bob=3.5, bob_cyc=2, n_kf=24)
run = state("run", 1.0, 32, 4, {"l": (2, -30, 10), "r": (10, 0, 0)}, bob=4.5, bob_cyc=2, n_kf=20)
sneak = state("sneak", 3.0, 4, 30, {"l": (0, 18, 0), "r": (-6, 24, 0)}, bob=1.2, bob_cyc=1, n_kf=24)
fly = state("fly", 2.4, 44, 6, {"l": (4, -45, 10), "r": (12, 0, 0)}, bob=2, bob_cyc=1, flut=3, flut_cyc=8, n_kf=48)
glide = state("glide", 3.6, 52, 8, {"l": (4, -50, 10), "r": (10, 0, 0)}, bob=1.5, bob_cyc=1, flut=3, flut_cyc=12, n_kf=72)
fall = state("fall", 1.2, 12, -4, {"l": (0, -30, 15), "r": (-8, -6, 0)}, bob=2, bob_cyc=1, flut=4, flut_cyc=4, n_kf=24)

# hurt : sursaut vers l'arrière + tremblement amorti, retour à zéro ; groupes concernés seuls
hu = lambda t: bump(t, 0.0, 0.07, 0.18, 0.66)
vib = lambda t: math.sin(TAU * t * 5 / 0.8) * (1 - sm(t, 0.2, 0.7))
tr_h = {}
for tag, (g, gb, s) in EARS.items():
    tr_h[g] = (lambda s: (lambda t: mirror(s, 16 * hu(t), 6 * vib(t) * hu(t))))(s)
    if s < 0:
        tr_h[gb] = lambda t: mirror(-1, 4 * hu(t), -22 * hu(t) + 8 * vib(t) * hu(t))
    else:
        tr_h[gb] = lambda t: mirror(1, 8 * hu(t), 8 * vib(t) * hu(t))
tr_h["noeud"] = lambda t: (0, 0, 10 * vib(t) * hu(t))
hurt = anim("hurt", 0.8, tr_h, n_kf=16, loop="once")

ANIMS = [idle, walk, run, sneak, fly, glide, fall, hurt]


def write():
    assert 40 <= len(elements) <= 200, f"budget : {len(elements)} cubes"
    textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
    if AVEC_E:
        textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
    model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
             "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
    os.makedirs(".build", exist_ok=True)
    out = f".build/{NOM}_brut.bbmodel"
    with open(out, "w") as fh:
        json.dump(model, fh, separators=(",", ":"))

    def depth(n, d=1):
        return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])

    print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
          sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
          f"densité {DENS:.2f} texels/px ; calque _e {'embarqué' if AVEC_E else 'non embarqué'}")


write()
