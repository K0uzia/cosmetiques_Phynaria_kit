"""Familier nuage-mochi : petit nuage dodu à visage kawaii qui flotte à droite du joueur, un peu en arrière, à hauteur d'épaule.
Ensemble « Nuage Guimauve » (crème, rose, lavande ; pièce sœur : oreilles_lapin_nuage). Design original.
Écrit familier_nuage_mochi.png, familier_nuage_mochi_e.png et .build/familier_nuage_mochi_brut.bbmodel à côté de ce script.

Volume : chaque bosse du nuage est un polyèdre fermé et arrondi (rectangle chanfreiné sur ses 12 arêtes et ses 8 coins,
chanfrein propre à chaque axe). Chaque facette est une peau de 0,3 px découpée par alpha exactement à son polygone, tranches
transparentes ; les facettes se rejoignent arête contre arête (aucun jour), autour d'une âme pleine. La teinte de chaque
texel vient de la normale lissée de l'ellipsoïde de la bosse (dégradé continu d'une facette à l'autre : on lit une boule,
pas des plaques) et d'une ombre de contact là où une bosse touche sa voisine. Les facettes cachées dans une voisine sont omises.

Bosses : « ventre » (grande bosse avant qui porte le visage), deux bosses sur le dessus, deux bosses latérales qui servent de
petits bras (groupes bras_l / bras_r, pivot à l'attache).

Hiérarchie (body = torse du joueur) :
  fam_elan    (attack/hurt : position, jamais touché par les états)
  fam_pos     (position : flottement, rapprochement en sneak, perchoir en sleep)
  fam_regard  (rotation : inclinaison, coup d'oeil, bascule couchée en glide/swim/sleep)
  fam_snap    (attack/hurt : rotation et scale)
  fam_squash  (scale : squash-and-stretch, pivot sous le nuage)
    corps (ventre + bosses du dessus), oeil_l, oeil_r (scale y : clignement), bras_l, bras_r
"""
import base64, io, itertools, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

AVEC_E = True       # calque _e embarqué en seconde texture, jamais assigné aux faces (correctif annoncé le 2026-11-03, à vérifier en jeu)
NOM = "familier_nuage_mochi"
TEX = 512
TAU = 2 * math.pi

# ------------------------------------------------------------------ palette « Nuage Guimauve » (celle d'oreilles_lapin_nuage, base poussée vers le blanc)
CREME = (255, 250, 248)
BLANC = (255, 255, 255)
LAV = (212, 198, 248)
LAV_D = (168, 146, 228)
ROSE = (255, 158, 194)
ROSE_L = (255, 210, 228)
ROSE_D = (226, 102, 154)
PRUNE = (52, 30, 66)
OEIL_H = (24, 16, 38)
OEIL_B = (90, 62, 142)
E_FOND = (13, 10, 18)            # fond additif très sombre
E_REFLET = (128, 122, 160)       # reflets des yeux : légère lueur, point focal


def lerp(a, b, k):
    return a + (b - a) * k


def col(c):
    return np.array(c, np.float32)


def mix(base, c, k):
    return lerp(base, col(c), np.clip(k, 0, 1)[..., None])


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def V(*a):
    return np.array(a, float)


def unit(v):
    return v / np.linalg.norm(v)


# ------------------------------------------------------------------ bosses (repère du familier : centre C0, visage vers -Z)
T = 0.32            # peau : 0,3 px + 0,02 px d'écart
# nom, groupe, centre, demi-tailles extérieures, chanfreins (x, y, z), test d'omission d'une facette (direction s -> True : cachée)
BOSSES = [
    ("ventre", "corps", V(0.0, -0.42, 0.0), V(2.30, 1.62, 2.00), V(0.70, 0.62, 0.80), lambda s: False),
    ("haut", "corps", V(0.40, 1.02, 0.18), V(1.55, 1.22, 1.72), V(0.74, 0.74, 0.74), lambda s: s[1] < 0),
    ("haut_g", "corps", V(-1.38, 0.72, 0.30), V(1.08, 0.98, 1.52), V(0.58, 0.58, 0.64), lambda s: s[1] < 0 or s[0] > 0),
    ("bras_l", "bras_l", V(-2.42, -0.78, -0.12), V(0.98, 0.94, 1.42), V(0.56, 0.56, 0.62), lambda s: s[0] > 0),
    ("bras_r", "bras_r", V(2.42, -0.74, -0.12), V(0.98, 0.94, 1.42), V(0.56, 0.56, 0.62), lambda s: s[0] < 0),
]
YB0, YB1 = -2.04, 2.24              # bas et haut du nuage
EYE_Y, EYE_DX, EYE_CX = -0.05, 0.84, 0.0
EYE_W, EYE_H = 0.98, 1.2
FACE_Z = -2.0                       # face avant du ventre


def facettes(H, C):
    """Polyèdre arrondi : pour chaque direction s de {-1,0,1}^3, polygone de la facette (repère de la bosse)."""
    out = []
    for s in itertools.product((-1, 0, 1), repeat=3):
        if s == (0, 0, 0):
            continue
        nz = [i for i in range(3) if s[i]]
        z0 = [i for i in range(3) if not s[i]]
        pts = []
        if len(nz) == 1:
            i = nz[0]
            for a, b in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
                p = np.zeros(3)
                p[i] = s[i] * H[i]
                p[z0[0]] = a * (H[z0[0]] - C[z0[0]])
                p[z0[1]] = b * (H[z0[1]] - C[z0[1]])
                pts.append(p)
        elif len(nz) == 2:
            i, j = nz
            l = z0[0]
            for a in (1, -1):
                for (ci, cj) in ((0, 1), (1, 0)):
                    p = np.zeros(3)
                    p[i] = s[i] * (H[i] - ci * C[i])
                    p[j] = s[j] * (H[j] - cj * C[j])
                    p[l] = a * (H[l] - C[l])
                    pts.append(p)
        else:
            for m in range(3):
                p = np.array([s[k] * (H[k] - C[k]) for k in range(3)], float)
                p[m] = s[m] * H[m]
                pts.append(p)
        n = unit(np.array([s[k] / C[k] for k in range(3)], float))
        ctr = np.mean(pts, axis=0)
        ref = unit(pts[0] - ctr)
        ang = [math.atan2(np.cross(ref, p - ctr) @ n, ref @ (p - ctr)) for p in pts]
        pts = [p for _, p in sorted(zip(ang, pts), key=lambda q: q[0])]
        out.append((s, n, pts))
    return out


def plan_ok(H, C, p, marge):
    """p (repère de la bosse) est-il à au moins `marge` sous toutes les facettes ?"""
    for s in itertools.product((-1, 0, 1), repeat=3):
        if s == (0, 0, 0):
            continue
        g = np.array([s[k] / C[k] for k in range(3)])
        rhs = sum(abs(s[k]) * H[k] / C[k] for k in range(3)) - (sum(1 for k in range(3) if s[k]) - 1)
        if (g @ p - rhs) / np.linalg.norm(g) > -marge:
            return False
    return True


def ame_dims(H, C):
    """Âme : le plus grand pavé (H - T - k*C) qui reste sous les peaux."""
    lo, hi = 0.0, float(np.min((H - T - 0.06) / C))
    assert all(plan_ok(H, C, np.array(sg) * (H - T - hi * C), T + 0.01) for sg in itertools.product((-1, 1), repeat=3))
    for _ in range(40):
        k = (lo + hi) / 2
        h = H - T - k * C
        ok = all(plan_ok(H, C, np.array(sg) * h, T + 0.01) for sg in itertools.product((-1, 1), repeat=3))
        lo, hi = (lo, k) if ok else (k, hi)
    return H - T - hi * C


# ------------------------------------------------------------------ peinture
TUILES = {}
PLATES = []          # (groupe, nom, centre plaque (repère familier), X, Y, n, tuile)


def lum_boule(P, boss):
    """Éclairage peint d'après la normale lissée de l'ellipsoïde de la bosse ; P : (..., 3) repère du familier."""
    _, _, c, H, _, _ = boss
    q = (P - c) / (H * H)
    n = q / np.linalg.norm(q, axis=-1, keepdims=True)
    Lp = unit(V(-0.35, 1.0, -0.55))
    return np.clip(0.5 + 0.5 * (n @ Lp), 0, 1), n[..., 1]


def ombre_contact(P, boss):
    """Ombre de recouvrement : assombrit là où la surface passe juste sous / contre une autre bosse."""
    o = np.zeros(P.shape[:-1])
    for b in BOSSES:
        if b is boss or b[1] != "corps":          # les bras bougent : ils ne projettent pas d'ombre peinte
            continue
        _, _, c, H, _, _ = b
        q = np.linalg.norm((P - c) / H, axis=-1)
        o = np.maximum(o, np.clip((1.32 - q) / 0.32, 0, 1) * (q > 0.97))
    return o


def peint_facette(sp, W, H_):
    ss = 4
    GW, GH = W * ss, H_ * ss
    w, h = sp["w"], sp["h"]
    yy, xx = np.mgrid[0:GH, 0:GW]
    X = (xx + 0.5) / GW * w - w / 2
    Y = h / 2 - (yy + 0.5) / GH * h
    d = sp["sd"](X, Y)
    inside = d < 0
    if sp.get("oeil"):
        return peint_oeil(X, Y, d, W, H_, inside)
    P = sp["o"] + X[..., None] * sp["X"] + Y[..., None] * sp["Y"]
    boss = sp["boss"]
    lum, ny = lum_boule(P, boss)
    hgt = np.clip((P[..., 1] - YB0) / (YB1 - YB0), 0, 1)
    k = np.clip(0.62 * lum + 0.38 * hgt + 0.12, 0, 1.2)
    c = lerp(col(LAV_D), col(LAV), np.clip(k / 0.38, 0, 1)[..., None])
    c = mix(c, CREME, (k - 0.38) / 0.3)
    c = mix(c, BLANC, (k - 0.82) / 0.2)
    c = mix(c, LAV_D, ombre_contact(P, boss) * 0.75)
    em = np.zeros(X.shape, bool)
    if sp.get("visage"):
        c = peint_visage(P[..., 0], P[..., 1], c)
    return finir(c, inside, em, W, H_)


def peint_visage(X, Y, c):
    # joues : ovale rose, reflet clair, trois traits obliques (>= 4 texels)
    for s in (-1, 1):
        cx, cy = EYE_CX + s * 1.30, EYE_Y - 0.70
        q = np.hypot((X - cx) / 0.38, (Y - cy) / 0.25)
        c = mix(c, ROSE, (q < 1.0) * 1.0)
        c = mix(c, ROSE_L, (np.hypot((X - cx + 0.1 * s) / 0.14, (Y - cy - 0.08) / 0.07) < 1) * 0.9)
        for kk in (-1, 1):
            x0 = cx + kk * 0.13
            seg = (np.abs((X - x0) + (Y - cy) * 0.5 * s) < 0.06) & (np.abs(Y - cy) < 0.12)
            c = mix(c, ROSE_D, seg * 1.0)
    # yeux fermés (sous les plaques d'yeux) : arc « ︶ » prune, visible au clignement et en sleep
    for s in (-1, 1):
        cx = EYE_CX + s * EYE_DX
        u = (X - cx) / 0.42
        arc = (np.abs(u) < 1) & (np.abs((Y - EYE_Y) - (-0.16 * (1 - u * u) + 0.02)) < 0.075)
        c = mix(c, PRUNE, arc * 1.0)
    # bouche : petit sourire ouvert, intérieur rose
    mx, my = EYE_CX, EYE_Y - 0.74
    q = np.hypot((X - mx) / 0.27, (Y - my) / 0.24)
    bouche = (q < 1) & (Y < my + 0.02)
    c = mix(c, PRUNE, bouche * 1.0)
    c = mix(c, ROSE_D, ((np.hypot((X - mx) / 0.16, (Y - my + 0.14) / 0.08) < 1) & bouche) * 1.0)
    return c


def peint_oeil(X, Y, d, W, H_, inside):
    """Grand oeil noir-prune brillant : violet plus clair en bas, gros reflet blanc en haut (côté +X), petit reflet en bas (côté -X)."""
    t = np.clip((EYE_H / 2 - Y) / EYE_H, 0, 1)
    c = lerp(col(OEIL_H), col(OEIL_B), (t ** 1.8)[..., None])
    r1 = np.hypot((X - 0.17) / 0.215, (Y - 0.24) / 0.23) < 1
    r2 = np.hypot((X + 0.20) / 0.10, (Y + 0.28) / 0.10) < 1
    c = mix(c, BLANC, (r1 | r2) * 1.0)
    return finir(c, inside, r1 | r2, W, H_)


def finir(c, inside, em, W, H_):
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H_), Image.LANCZOS))
    al = np.array(Image.fromarray((inside * 255).astype(np.uint8), "L").resize((W, H_), Image.LANCZOS)) > 110
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    if al.any():
        out[~al, :3] = rgb[al].mean(axis=0).astype(np.uint8)
    e = np.array(Image.fromarray((em * 255).astype(np.uint8), "L").resize((W, H_), Image.LANCZOS)) > 110
    oe = np.zeros((H_, W, 4), np.uint8)
    oe[al, :3] = E_FOND
    oe[al, 3] = 255
    oe[e & al, :3] = E_REFLET
    return out, oe


def paint_ame(W=8, H_=16):
    a = np.zeros((H_, W, 4), np.uint8)
    a[..., :3] = LAV
    a[..., 3] = 255
    e = np.zeros_like(a)
    e[..., :3] = E_FOND
    e[..., 3] = 255
    return a, e


def sd_poly(pts2):
    """Distance signée à un polygone convexe (sens trigonométrique), négative dedans."""
    edges = []
    for i in range(len(pts2)):
        a, b = pts2[i], pts2[(i + 1) % len(pts2)]
        t = unit(b - a)
        edges.append((a, np.array([t[1], -t[0]])))        # normale sortante
    def f(X, Y):
        return np.max([(X - a[0]) * nn[0] + (Y - a[1]) * nn[1] for a, nn in edges], axis=0)
    return f


DEBORD = 0.015      # chaque facette déborde un peu sur ses voisines : pas de fente à l'arête

for boss in BOSSES:
    nom, g, c, H, C, cache = boss
    for s, n, pts in facettes(H, C):
        if cache(s):
            continue
        P = [p + c for p in pts]
        ctr = np.mean(P, axis=0)
        Xa = unit(P[1] - P[0])
        Ya = np.cross(n, Xa)
        p2 = [np.array([(p - ctr) @ Xa, (p - ctr) @ Ya]) for p in P]
        lo, hi = np.min(p2, axis=0) - DEBORD - 0.02, np.max(p2, axis=0) + DEBORD + 0.02
        mid = (lo + hi) / 2
        o = ctr + Xa * mid[0] + Ya * mid[1]
        p2c = [q - mid for q in p2]
        f = sd_poly(p2c)
        tn = f"{nom}_" + "".join("p" if v > 0 else ("m" if v < 0 else "o") for v in s)
        TUILES[tn] = dict(w=hi[0] - lo[0], h=hi[1] - lo[1], sd=(lambda f: lambda X, Y: f(X, Y) - DEBORD)(f), o=o, X=Xa, Y=Ya, boss=boss,
                          visage=(nom == "ventre" and s == (0, 0, -1)))
        PLATES.append((g, tn, o - n * 0.15, Xa, Ya, n, tn))

TUILES["oeil"] = dict(w=EYE_W, h=EYE_H, sd=lambda X, Y: (np.hypot(X / (EYE_W / 2), Y / (EYE_H / 2)) - 1) * EYE_W / 2, oeil=True)

UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
tex_b64 = tex_e_b64 = None


def atlas():
    global tex_b64, tex_e_b64
    ame_im, ame_e = paint_ame()
    fixed = [("ame", ame_im, ame_e)]

    def pack(dens):
        items = [(n, im.shape[1], im.shape[0]) for n, im, _ in fixed] + [(n, int(math.ceil(s["w"] * dens)), int(math.ceil(s["h"] * dens))) for n, s in TUILES.items()]
        items.sort(key=lambda it: -it[2])
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

    dens = 48.0
    while (uv := pack(dens)) is None:
        dens -= 0.5
    UV.update(uv)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, im, ie in fixed:
        u0, v0, u1, v1 = UV[n]
        tex[v0:v1, u0:u1], tex_e[v0:v1, u0:u1] = im, ie
    for n, s in TUILES.items():
        u0, v0, u1, v1 = UV[n]
        tex[v0:v1, u0:u1], tex_e[v0:v1, u0:u1] = peint_facette(s, u1 - u0, v1 - v0)
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


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx. Blocage de cardan (Y = ±90°) : Z = 0 et X tiré de la ligne 0."""
    if abs(R[2, 0]) > 1 - 1e-9:
        if R[2, 0] < 0:
            return math.degrees(math.atan2(R[0, 1], R[1, 1])), 90.0, 0.0
        return math.degrees(math.atan2(-R[0, 1], R[1, 1])), -90.0, 0.0
    ry = math.asin(-R[2, 0])
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def _check_euler(R):
    a, b, c = map(math.radians, euler(R))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    assert np.allclose(Rz @ Ry @ Rx, R, atol=1e-5), euler(R)


def group(name, origin, parent=None):
    assert name not in groups
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def plate(g, name, c, X, Y, out, tile, th=0.3):
    """Peau : contour par l'alpha, tranches transparentes, seule la face tournée vers out est peinte.
    u suit X, le haut de l'image est +Y : on peint dans le repère physique de la plaque."""
    X, Y = unit(X), unit(Y)
    w, h = TUILES[tile]["w"], TUILES[tile]["h"]
    u0, v0, u1, v1 = UV[tile]
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    _check_euler(R_)
    south, north = [u0, v0, u1, v1], [u1, v0, u0, v1]
    if R_[:, 2] @ out > 0:
        north = CLEAR
    else:
        south = CLEAR
    c = np.asarray(c, float)
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
         {"south": south, "north": north, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def ame(g, name, c, h):
    u0, v0, u1, v1 = UV["ame"]
    f = [u0, v0, u1, v1]
    cube(g, name, c - h, c + h, c, (0, 0, 0), {k: f for k in ("north", "south", "east", "west", "up", "down")})


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


C0 = V(12.5, 27.0, 3.0)        # centre du nuage au repos : à droite du joueur, un peu en arrière, hauteur d'épaule


def L(x, y, z):
    return C0 + V(x, y, z)


EX, EY, EZ = V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)
SQ_PIVOT = L(0, YB0 + 0.2, 0)
OFF = 0.17

g_elan = group("fam_elan", C0)
g_pos = group("fam_pos", C0, parent=g_elan)
g_reg = group("fam_regard", C0, parent=g_pos)
g_snap = group("fam_snap", C0, parent=g_reg)
g_sq = group("fam_squash", SQ_PIVOT, parent=g_snap)
group("corps", C0, parent=g_sq)
ARMS = {}
for tag in ("l", "r"):
    b = next(bb for bb in BOSSES if bb[0] == f"bras_{tag}")
    s = 1 if tag == "r" else -1
    ARMS[tag] = group(f"bras_{tag}", C0 + b[2] - V(s * 0.55 * b[3][0], 0, 0), parent=g_sq)

# yeux : plaque devant la face du ventre, pivot au centre de l'oeil (scale y = clignement)
EYES = {}
for s, tag in ((-1, "l"), (1, "r")):
    ec = L(EYE_CX + s * EYE_DX, EYE_Y, FACE_Z - OFF)
    EYES[tag] = group(f"oeil_{tag}", ec, parent=g_sq)

DENS = atlas()
for nom, g, c, H, C, cache in BOSSES:
    ame(g, f"ame_{nom}", C0 + c, ame_dims(H, C))
for g, tn, o, Xa, Ya, n, tile in PLATES:
    plate(g, tn, C0 + o, Xa, Ya, n, tile)
for s, tag in ((-1, "l"), (1, "r")):
    plate(EYES[tag], f"oeil_{tag}", L(EYE_CX + s * EYE_DX, EYE_Y, FACE_Z - OFF), EX, EY, -EZ, "oeil")

outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone_node(g_elan)]}]


# ------------------------------------------------------------------ animations
# Guide, section 3 : rotation +X = le haut bascule vers l'arrière (+Z) ; +Y = le côté droit (+X) avance ; +Z = le côté droit monte.
# Position +Y monte, +X vers la droite du joueur. Le visage regarde -Z : +Y le tourne vers le joueur (-X).
def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 4)), "y": str(round(v[1] + 0.0, 4)), "z": str(round(v[2] + 0.0, 4))}],
            "time": round(t, 3), "interpolation": "linear"}


def anim(name, length, tracks, n_kf=None, loop="loop"):
    n = n_kf or max(6, int(round(length * 10)))
    times = [i * length / n for i in range(n + 1)]
    A = {groups[g]["uuid"]: {"name": g, "type": "bone", "keyframes": [kf(ch, t, f(t)) for ch, f in chans.items() for t in times]} for g, chans in tracks.items()}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


def mirror(f):
    """Bras gauche : même intention que le droit, signes Y et Z inversés (le côté gauche est -X)."""
    return lambda t: (lambda v: (v[0], -v[1], -v[2]))(f(t))


def squash(k):
    """k > 0 : écrasé (plus large, moins haut) ; k < 0 : étiré. Volume à peu près conservé."""
    return (1 + 0.6 * k, 1 - k, 1 + 0.6 * k)


def clin(t, *ts, dur=0.24):
    """Clignement : fermeture rapide, réouverture un peu plus lente ; échelle y de l'oeil."""
    v = 1.0
    for a in ts:
        v -= 0.94 * bump(t, a, a + dur * 0.35, a + dur * 0.5, a + dur)
    return v


def etat(name, T_, pos, regard, sq, oeil, bras, n_kf=None):
    """pos(t), regard(t) : rotation, sq(t) : facteur squash, oeil(t) : échelle y, bras(t) : rotation du bras droit (gauche en miroir)."""
    tr = {g_pos: {"position": pos}, g_reg: {"rotation": regard}, g_sq: {"scale": lambda t: squash(sq(t))}}
    for tag in ("l", "r"):
        tr[EYES[tag]] = {"scale": (lambda t: (1, oeil(t), 1))}
    tr[ARMS["r"]] = {"rotation": bras}
    tr[ARMS["l"]] = {"rotation": mirror(bras)}
    return anim(name, T_, tr, n_kf=n_kf)


# idle (8 s) : flottement 4 s, petit saut joyeux (anticipation, étirement, atterrissage écrasé), coup d'oeil vers le joueur, 4 clignements
TI = 8.0


def hop(t, a):
    up = bump(t, a + 0.25, a + 0.6, a + 0.6, a + 1.0)
    k = 0.16 * bump(t, a, a + 0.2, a + 0.2, a + 0.32) - 0.12 * bump(t, a + 0.28, a + 0.45, a + 0.55, a + 0.8) + 0.14 * bump(t, a + 0.92, a + 1.02, a + 1.05, a + 1.3)
    return up, k


def idle_pos(t):
    up, _ = hop(t, 5.4)
    return (0.22 * math.sin(TAU * t / TI), 0.5 * math.sin(TAU * 2 * t / TI) + 1.3 * up, 0.2 * math.sin(TAU * t / TI + 1.0))


def idle_sq(t):
    _, k = hop(t, 5.4)
    return -0.035 * math.sin(TAU * 2 * t / TI + 0.5) + k


def idle_reg(t):
    coup = bump(t, 2.2, 2.7, 3.9, 4.5)
    return (2.5 * math.sin(TAU * 2 * t / TI), 20 * coup, 4 * math.sin(TAU * t / TI) - 6 * coup)


def idle_bras(t):
    up, _ = hop(t, 5.4)
    return (0, 0, 10 + 7 * math.sin(TAU * 2 * t / TI + 0.8) + 40 * up)


idle = etat("idle", TI, idle_pos, idle_reg, idle_sq, lambda t: clin(t, 1.3, 4.6, 4.9, 7.2), idle_bras, n_kf=96)

# walk (1,6 s) : sautille à chaque pas, un peu en retrait, bras qui se balancent en alternance
TW = 1.6


def walk_sq(t):
    k = math.cos(TAU * 2 * t / TW)        # 1 : au plus bas (atterrissage)
    return 0.09 * k ** 7 if k > 0 else -0.04 * (1 - k * k)


walk = etat("walk", TW,
            lambda t: (0.1 * math.sin(TAU * t / TW), -0.2 + 0.75 * abs(math.sin(TAU * t / TW)), 0.8),
            lambda t: (-4 + 2 * math.sin(TAU * 2 * t / TW), 4, 4 * math.sin(TAU * t / TW)),
            walk_sq,
            lambda t: clin(t, 0.9),
            lambda t: (0, -10 * math.sin(TAU * t / TW), 14 + 10 * math.sin(TAU * t / TW)),
            n_kf=24)

# run (1 s) : traîne derrière, étiré par le vent, penché en avant, bras rabattus vers l'arrière
TR = 1.0
run = etat("run", TR,
           lambda t: (0.3, -0.4 + 0.55 * abs(math.sin(TAU * t / TR)), 2.8),
           lambda t: (-12 + 2.5 * math.sin(TAU * 2 * t / TR), 6, 3 * math.sin(TAU * t / TR)),
           lambda t: 0.05 + 0.05 * math.cos(TAU * 2 * t / TR),
           lambda t: 0.85,
           lambda t: (0, -38, 22 + 9 * math.sin(TAU * 2 * t / TR)),
           n_kf=20)

# sneak (3 s) : se rapproche et descend, s'aplatit, yeux mi-clos, bras rentrés
TS = 3.0
sneak = etat("sneak", TS,
             lambda t: (-1.2, -2.6 + 0.18 * math.sin(TAU * t / TS), -0.4),
             lambda t: (-6 + 1.5 * math.sin(TAU * t / TS), 12, 2 * math.sin(TAU * t / TS + 1)),
             lambda t: 0.17 + 0.025 * math.sin(TAU * t / TS),
             lambda t: 0.55 - 0.5 * bump(t, 1.8, 1.88, 1.95, 2.1),
             lambda t: (0, 8, -28 + 3 * math.sin(TAU * t / TS)),
             n_kf=24)

# fly (2,4 s) : plus haut, bras qui battent comme de petites ailes, rebond étiré à chaque battement
TF = 2.4
fly = etat("fly", TF,
           lambda t: (0, 1.8 + 0.7 * math.sin(TAU * t / TF) + 0.25 * math.sin(TAU * 3 * t / TF + 2.4), 1.6),
           lambda t: (-6 + 3 * math.sin(TAU * t / TF + 0.5), 5, 4 * math.sin(TAU * t / TF + 1.2)),
           lambda t: -0.06 * math.sin(TAU * 3 * t / TF + 0.6),
           lambda t: 1.08 * clin(t, 1.5),
           lambda t: (0, -6, 28 + 30 * math.sin(TAU * 3 * t / TF)),
           n_kf=36)

# glide (3,6 s) : le joueur est couché et le torse avec lui : bascule +X pour garder le visage vers l'avant du vol, étiré, bras en ailes
TG = 3.6
glide = etat("glide", TG,
             lambda t: (0.6, 0.6 * math.sin(TAU * t / TG), 0.5),
             lambda t: (76 + 3 * math.sin(TAU * t / TG), 0, 4 * math.sin(TAU * t / TG + 1.2)),
             lambda t: -0.08 + 0.02 * math.sin(TAU * t / TG),
             lambda t: 1.0,
             lambda t: (0, -30, 38 + 6 * math.sin(TAU * t / TG)),
             n_kf=24)

# fall (1,2 s) : reste en arrière vers le haut, étiré, yeux grands ouverts, bras levés qui gigotent
TA = 1.2
fall = etat("fall", TA,
            lambda t: (0, 1.4 + 0.15 * math.sin(TAU * t / TA), 0.4),
            lambda t: (4 + 2 * math.sin(TAU * t / TA), 0, 5 * math.sin(TAU * t / TA)),
            lambda t: -0.11 + 0.025 * math.sin(TAU * 2 * t / TA),
            lambda t: 1.14,
            lambda t: (0, 0, 58 + 12 * math.sin(TAU * 2 * t / TA)),
            n_kf=18)

# swim (2,4 s) : couché comme en élytres, ondule comme une méduse, bras qui pagaient
TN = 2.4
swim = etat("swim", TN,
            lambda t: (0.4, 0.4 * math.sin(TAU * t / TN + 0.6), 0.4),
            lambda t: (70 + 4 * math.sin(TAU * t / TN), 0, 3 * math.sin(TAU * t / TN)),
            lambda t: 0.08 * math.sin(TAU * t / TN),
            lambda t: clin(t, 1.7),
            lambda t: (0, -10 + 18 * math.sin(TAU * t / TN + 1.2), 12 + 24 * math.sin(TAU * t / TN + 1.2)),
            n_kf=24)

# mount (3 s) : calme, bas, respiration ample
TM = 3.0
mount = etat("mount", TM,
             lambda t: (0, -0.6 + 0.3 * math.sin(TAU * t / TM), 0.4),
             lambda t: (1.5 * math.sin(TAU * t / TM), 8, 3 * math.sin(TAU * t / TM + 0.8)),
             lambda t: 0.05 * math.sin(TAU * t / TM + 0.4),
             lambda t: clin(t, 2.1),
             lambda t: (0, 0, 4 + 5 * math.sin(TAU * t / TM)),
             n_kf=24)

# sleep (4 s) : joueur couché sur le dos (supposé) : le familier se pose sur son ventre, côté droit, haut vers le ciel (-Z du torse),
# visage tourné vers la tête du joueur ; yeux fermés (arcs peints sous les yeux), respiration lente
TZ = 4.0
SD = V(6.6, 17.0, -4.6) - C0
sleep = etat("sleep", TZ,
             lambda t: (SD[0], SD[1], SD[2] - 0.15 * math.sin(TAU * t / TZ)),
             lambda t: (-88, 0, 180 + 4 * math.sin(TAU * t / TZ)),
             lambda t: 0.1 + 0.07 * math.sin(TAU * t / TZ),
             lambda t: 0.06,
             lambda t: (0, 0, -22 + 3 * math.sin(TAU * t / TZ)),
             n_kf=24)


# attack : élan vers l'avant, étirement puis écrasement ; hurt : recul, écrasement, tremblement. Une fois, retour à 0 ; fam_elan et fam_snap seulement.
def _elan(t):
    return bump(t, 0.06, 0.2, 0.3, 0.7)


attack = anim("attack", 0.8, {
    g_elan: {"position": lambda t: (-0.8 * _elan(t), 0.6 * _elan(t), -5.5 * _elan(t))},
    g_snap: {"rotation": lambda t: (8 * bump(t, 0.0, 0.08, 0.08, 0.18) - 14 * bump(t, 0.1, 0.22, 0.3, 0.7), 0, 0),
             "scale": lambda t: squash(0.14 * bump(t, 0.0, 0.07, 0.07, 0.15) - 0.12 * bump(t, 0.1, 0.2, 0.24, 0.36) + 0.12 * bump(t, 0.3, 0.38, 0.4, 0.6))},
}, n_kf=24, loop="once")

hurt = anim("hurt", 0.8, {
    g_elan: {"position": lambda t: (0.7 * bump(t, 0.0, 0.06, 0.2, 0.6) * math.sin(TAU * t * 7), 1.0 * bump(t, 0.0, 0.08, 0.16, 0.65), 3.0 * bump(t, 0.0, 0.08, 0.16, 0.65))},
    g_snap: {"rotation": lambda t: (16 * bump(t, 0.0, 0.08, 0.16, 0.65), 0, 8 * bump(t, 0.0, 0.05, 0.2, 0.66) * math.sin(TAU * t * 6)),
             "scale": lambda t: squash(0.24 * bump(t, 0.0, 0.05, 0.08, 0.2) - 0.08 * bump(t, 0.18, 0.28, 0.3, 0.45) + 0.04 * bump(t, 0.42, 0.5, 0.52, 0.65))},
}, n_kf=32, loop="once")

ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, attack, hurt]

assert 40 <= len(elements) <= 110, f"budget : {len(elements)} cubes"
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
      f"densité {DENS:.1f} texels/px")
