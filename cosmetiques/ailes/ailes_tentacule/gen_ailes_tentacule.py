"""Ailes tentaculaires (ensemble Tentacule, thème Démoniaque), refonte du 2026-11-08 (« tentacule a revoir »).

Une paire d'ailes faites chacune de trois tentacules de chair qui sortent du haut du dos, de part et d'autre d'un nœud de
chair central qui porte un œil d'ambre à fente (la créature accrochée au porteur, lore de l'ensemble). Aucune plaque ni sac :
les bases des tentacules plongent dans le dos, le nœud fait 4 px de large.

Documentation : .claude/references/creatures/cephalopodes-tentacules.md (anatomie d'un bras, ventouses, peau, onde de
flexion de la base vers la pointe, enroulement depuis la pointe), .claude/references/creatures/marines-mythiques.md,
.claude/styles/tentacule.md. Ce qui en est tiré :
- bras = hydrostat musculaire, sans os : il plie partout, s'effile en continu, s'enroule depuis la pointe vers la face des
  ventouses ; 14, 13 et 12 segments par tentacule (longueurs géométriques : segments courts au bout, pour une spirale serrée),
  rayon 1,75 → 0,32 px ;
- ventouses sur une seule face (l'intérieur de la courbe), deux rangées en quinconce de part et d'autre d'un sillon, de plus en
  plus petites vers la pointe, une seule rangée sur le dernier tiers ; anneau clair, cupule sombre, reflet humide ;
- peau : dos sombre (prune-noir) moucheté de chromatophores, flancs lie-de-vin, face orale chair pâle ; peau humide = traînées
  de reflet nettes (rose très pâle, froid, jamais dans le calque _e) sur les faces tournées vers le ciel ;
- mouvement : onde qui part de la base et court vers la pointe (retard de 35 à 55° de phase par segment, amplitude croissante),
  déphasée d'un tentacule à l'autre ; la pointe s'enroule et se déroule (étirement au repos, freinage en chute, traîne en
  course, enroulement serré en sneak et en sommeil).

Volume : tube octogonal continu (deux cubes à 45° autour de l'axe, comme les os des ailes abyssales), segments imbriqués qui
se chevauchent d'un demi-rayon pour rester continus dans les courbes ; décalage de 6° d'un segment à l'autre et rayon qui
décroît de 0,1 px : jamais deux faces parallèles confondues.

États : les 12 du mod (idle avec étirement et clignement de l'œil, walk, run, sneak, fly, glide, swim, fall, mount, sleep,
attack et hurt en once). Les boucles sont écrites en Molang (sinus de période fermée), les animations once échantillonnées.
event_equip (2 s) : le nœud gonfle, les tentacules sortent du dos roulés serrés, l'un après l'autre, et se déroulent de la
base vers la pointe ; event_unequip (1,6 s) : ils s'enroulent et rentrent, puis tout disparaît (échelle 0).
Fonctions avancées : event_equip, event_unequip, un son (à l'apparition, entity.slime.squish), calque _e (fente et iris de
l'œil seuls, point focal), overlay_ambiance (tools/ambiance.py), Molang (math.sin, math.pow, math.max). Aucune particule.
À juger en jeu : l'œil la nuit (_e), la lecture des ventouses à 4 blocs, l'enroulement vu de près, le repli en sneak contre
une armure.
Écrit ailes_tentacule.png, ailes_tentacule_e.png et .build/ailes_tentacule_brut.bbmodel.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
NOM = "ailes_tentacule"
AVEC_E = True
TEX = 256
SS = 4                                   # sur-échantillonnage de la peinture
RNG = np.random.default_rng(20261108)

# ====================================================================== textures
BIG = np.zeros((TEX * SS, TEX * SS, 3), np.float32)
E_BIG = np.zeros((TEX * SS, TEX * SS, 3), np.float32)
TW, TH = 32, 24                          # tuile de peau (texels) : u = le long du tentacule, v = en travers

PEAU = {   # catégorie : (couleur de fond, couleur des taches, nombre de traînées de reflet)
    "dorsal": ((58, 16, 40), (30, 6, 22), 1),
    "haut":   ((98, 26, 56), (52, 12, 34), 1),
    "flanc":  ((136, 38, 68), (82, 18, 46), 0),
    "bas":    ((184, 78, 100), (138, 44, 70), 0),
    "oral":   ((222, 152, 150), (196, 112, 118), 0),
    "noeud":  ((86, 22, 50), (40, 8, 28), 1),
}
CATS = list(PEAU)
REFLET = np.array((242, 204, 220), np.float32)   # rose très pâle et froid : pas d'éclat _e (tools/ambiance.py)


def blob(img, cx, cy, rad, col, force=1.0, dur=2.0):
    h, w = img.shape[:2]
    y, x = np.mgrid[0:h, 0:w]
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / max(rad, 1e-3)
    a = np.clip(1 - d ** dur, 0, 1)[..., None] * force
    img[:] = img * (1 - a) + np.array(col, np.float32) * a


def tuile_peau(cat):
    base, tache, nref = PEAU[cat]
    W, H = TW * SS, TH * SS
    img = np.zeros((H, W, 3), np.float32) + np.array(base, np.float32)
    # léger bruit de valeur (peau vivante, pas aplat)
    bruit = RNG.normal(0, 1, (H // 8 + 2, W // 8 + 2)).astype(np.float32)
    bruit = np.array(Image.fromarray(bruit).resize((W, H), Image.BICUBIC))
    img *= (1 + 0.06 * bruit)[..., None]
    # taches (chromatophores) : grandes et floues, puis petits points nets
    for _ in range(7):
        blob(img, RNG.uniform(0, W), RNG.uniform(0, H), RNG.uniform(2.5, 5) * SS, tache, 0.55, 1.6)
    for _ in range(26):
        blob(img, RNG.uniform(0, W), RNG.uniform(0, H), RNG.uniform(0.6, 1.2) * SS, tache, 0.85, 3)
    if cat in ("dorsal", "haut", "noeud"):           # papilles : petits reliefs clairs ombrés dessous
        clair = np.minimum(np.array(base) * 1.7 + 10, 255)
        for _ in range(9):
            cx, cy = RNG.uniform(0, W), RNG.uniform(0, H)
            blob(img, cx, cy + 0.6 * SS, 0.9 * SS, np.array(base) * 0.5, 0.8, 3)
            blob(img, cx, cy, 0.8 * SS, clair, 0.8, 3)
    if cat == "noeud":                               # veines lie-de-vin
        for _ in range(3):
            x0, y0 = RNG.uniform(0, W), RNG.uniform(0, H)
            for s in np.linspace(0, 1, 60):
                blob(img, x0 + s * W * 0.6, y0 + 6 * SS * math.sin(s * 5 + x0), 0.5 * SS, (150, 34, 66), 0.7, 3)
    # rides transversales fines
    for u in np.arange(RNG.uniform(0, 5), TW, RNG.uniform(4.5, 6.5)):
        xs = (u + 0.6 * np.sin(np.arange(H) / H * 6 + u)) * SS
        for yy, xx in enumerate(xs.astype(int)):
            if 0 <= xx < W:
                img[yy, max(0, xx - 1):xx + 1] *= 0.86
    # traînées de reflet humide : nettes, interrompues, le long du tentacule
    for k in range(nref):
        v = (k + 0.5 + RNG.uniform(-0.25, 0.25)) / nref * H
        on = np.array(Image.fromarray(RNG.normal(0, 1, (1, 9)).astype(np.float32)).resize((W, 1), Image.BICUBIC))[0]
        for xx in range(W):
            if on[xx] > 0.35:
                ep = (1.1 + 0.5 * math.sin(xx / W * 7 + k)) * SS
                y0, y1 = int(v - ep / 2), int(v + ep / 2)
                img[max(0, y0):max(0, y1), xx] = img[max(0, y0):max(0, y1), xx] * 0.25 + REFLET * 0.75
        for _ in range(3):                           # gouttes de reflet
            blob(img, RNG.uniform(0, W), v + RNG.uniform(-3, 3) * SS, 0.7 * SS, REFLET, 0.9, 3)
    return np.clip(img, 0, 255)


TUILES = {}                              # cat -> liste d'origines (u, v) en texels
for r, cat in enumerate(CATS):
    TUILES[cat] = []
    for c in range(8):
        u0, v0 = c * TW, r * TH
        BIG[v0 * SS:(v0 + TH) * SS, u0 * SS:(u0 + TW) * SS] = tuile_peau(cat)
        TUILES[cat].append((u0, v0))

# ventouses : disques 16 x 16 (ligne y = 144)
VY = len(CATS) * TH                      # 144
VENT = []


def disque(variante):
    n = 16 * SS
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2
    rr = np.sqrt((x - c) ** 2 + (y - c) ** 2) / (n / 2)
    ang = np.arctan2(y - c, x - c)
    img = np.zeros((n, n, 3), np.float32) + np.array((206, 128, 132), np.float32)       # coins : chair de la face orale

    def anneau(r0, r1, col):
        m = (rr >= r0) & (rr < r1)
        img[m] = col
    anneau(0.0, 0.92, (238, 194, 184))                                                   # bord clair
    stries = (np.sin(ang * 14 + variante) > 0.55) & (rr > 0.6) & (rr < 0.9)
    img[stries] = (214, 160, 156)                                                        # plis radiaux du bord
    anneau(0.0, 0.6, (176, 88, 102))                                                     # sillon
    cup = rr < 0.5
    t = (rr[cup] / 0.5)[:, None]
    img[cup] = np.array((70, 16, 34)) * (1 - t) + np.array((136, 52, 72)) * t           # cupule
    anneau(0.0, 0.17, (40, 8, 22))                                                       # orifice
    hl = (rr > 0.66) & (rr < 0.86) & (np.cos(ang + 2.3) > 0.55)
    img[hl] = REFLET                                                                     # reflet humide sur le bord
    return img


for k in range(6):
    u0 = k * 16
    BIG[VY * SS:(VY + 16) * SS, u0 * SS:(u0 + 16) * SS] = disque(k * 0.7)
    VENT.append((u0, VY))
# flanc de ventouse (bord clair, plus sombre vers la base) : 16 x 16 en u = 96
n = 16 * SS
g = np.linspace(0, 1, n, dtype=np.float32)[:, None, None]
BIG[VY * SS:(VY + 16) * SS, 96 * SS:112 * SS] = np.array((236, 188, 180)) * (1 - g) + np.array((172, 86, 100)) * g
FLANC_V = (96, VY)

# œil (ligne y = 160) : iris d'ambre 16 x 16, fente 8 x 16, paupière = tuile du nœud
OY = VY + 16
n = 16 * SS
y, x = np.mgrid[0:n, 0:n].astype(np.float32)
c = (n - 1) / 2
rr = np.sqrt(((x - c) / (n / 2)) ** 2 + ((y - c) / (n / 2)) ** 2)
iris = np.zeros((n, n, 3), np.float32)
t = np.clip(rr, 0, 1)[..., None]
iris[:] = np.array((252, 214, 96)) * (1 - t) + np.array((196, 96, 18)) * t
ray = (np.sin(np.arctan2(y - c, x - c) * 18) > 0.6) & (rr > 0.35)
iris[ray] *= 0.82
iris[rr > 0.96] = (90, 30, 10)
BIG[OY * SS:(OY + 16) * SS, 0:16 * SS] = iris
E_BIG[OY * SS:(OY + 16) * SS, 0:16 * SS] = np.where((rr < 0.96)[..., None], iris * 0.85, 0)
fente = np.zeros((n, n // 2, 3), np.float32) + np.array((14, 4, 8), np.float32)
fente[:, n // 4 - SS // 2:n // 4 + SS // 2] = (60, 10, 14)                               # fond rouge de la fente
BIG[OY * SS:(OY + 16) * SS, 16 * SS:24 * SS] = fente
IRIS, FENTE = (0, OY), (16, OY)


def vers_png(big):
    im = Image.fromarray(np.clip(big, 0, 255).astype(np.uint8), "RGB").resize((TEX, TEX), Image.LANCZOS)
    return np.dstack([np.array(im), np.full((TEX, TEX), 255, np.uint8)])


tex = vers_png(BIG)
tex_e = vers_png(E_BIG)
tex_e[..., 3] = np.where(tex_e[..., :3].max(axis=2) > 8, 255, 0)
tex_e[tex_e[..., 3] == 0] = 0


def b64png(arr, fn):
    im = Image.fromarray(arr, "RGBA")
    im.save(fn, optimize=True)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


# ====================================================================== géométrie
elements, groups = [], {}
D = 6.0                                  # densité : texels par px


def nuid():
    return str(_uuid.uuid4())


def uv_peau(cat, long_, larg, graine):
    u0, v0 = TUILES[cat][graine % 8]
    lu, lv = min(TW - 1, max(1.0, long_ * D)), min(TH - 1, max(1.0, larg * D))
    du = (graine * 7.31) % max(0.01, TW - 1 - lu)
    dv = (graine * 3.17) % max(0.01, TH - 1 - lv)
    return [u0 + 0.5 + du, v0 + 0.5 + dv, u0 + 0.5 + du + lu, v0 + 0.5 + dv + lv]


def cube(s, g, name, frm, to, origin, rot, faces):
    """s = +1 aile droite (+X), -1 aile gauche : miroir x -> -x, rotation (rx, -ry, -rz), faces est/ouest échangées."""
    frm, to, origin = list(frm), list(to), list(origin)
    rot = list(rot)
    if s < 0:
        frm[0], to[0] = -to[0], -frm[0]
        origin[0] = -origin[0]
        rot = [rot[0], -rot[1], -rot[2]]
        f2 = {}
        for k, uv in faces.items():
            k2 = {"east": "west", "west": "east"}.get(k, k)
            f2[k2] = [uv[2], uv[1], uv[0], uv[3]]
        faces = f2
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to],
         "origin": [round(v, 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(v, 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(v) > 1e-6 for v in rot):
        e["rotation"] = [round(v, 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])
    return e


def group(s, name, origin, parent, rotation=(0, 0, 0)):
    o = list(origin)
    r = list(rotation)
    if s < 0:
        o[0] = -o[0]
        r = [r[0], -r[1], -r[2]]
    assert name not in groups, name
    groups[name] = {"origin": [round(v, 3) for v in o], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(v, 2) for v in r]}
    return name


def angdist(a, b):
    d = abs((a - b) % 360)
    return min(d, 360 - d)


def cat_de(phi, phi_o):
    d = angdist(phi, phi_o)
    return "oral" if d < 22 else "bas" if d < 67 else "flanc" if d < 112 else "haut" if d < 157 else "dorsal"


PHI_LOCAL = {"down": 0, "south": 90, "up": 180, "north": 270}


def dvec(phi):
    p = math.radians(phi)
    return np.array((0.0, -math.cos(p), math.sin(p)))


def tvec(phi):
    p = math.radians(phi)
    return np.array((0.0, math.sin(p), math.cos(p)))


# Tentacules de l'aile droite. P : pivot de sortie (dans le dos) ; yaw < 0 : vers l'arrière ; alpha : montée au départ ;
# courbe : (montée des premiers segments, enroulement de la pointe vers la face des ventouses).
TENT = [
    dict(nom="t1", P=(4.2, 20.6, 3.3), yaw=-22, alpha=42, L=38.0, n=14, r0=2.1, r1=0.3, monte=(5, 4.5), enr=(1.5, 70.0), ph=0),
    dict(nom="t2", P=(4.7, 18.9, 3.3), yaw=-26, alpha=10, L=29.0, n=13, r0=1.7, r1=0.28, monte=(3, 1.5), enr=(1.5, 62.0), ph=110),
    dict(nom="t3", P=(4.2, 17.3, 3.2), yaw=-30, alpha=-26, L=21.0, n=12, r0=1.4, r1=0.26, monte=(3, 2.5), enr=(1.5, 56.0), ph=220),
]
PHI_O = 30.0                             # face des ventouses : vers le bas et l'arrière

for T in TENT:
    n = T["n"]
    q = 0.91
    a = T["L"] * (1 - q) / (1 - q ** n)
    T["Ls"] = [a * q ** j for j in range(n)]
    T["X"] = [sum(T["Ls"][:j]) for j in range(n + 1)]
    T["rs"] = [T["r1"] + (T["r0"] - T["r1"]) * (1 - j / (n - 1)) ** 1.25 for j in range(n)]   # effilé conique
    nm, am = T["monte"]
    kap = [0.0]
    for j in range(1, n):
        u = j / (n - 1)
        k = (am if j <= nm else 0.0) - (T["enr"][0] + T["enr"][1] * u ** 4)
        kap.append(k)
    T["kap"] = kap
    T["coil"] = [-(T["enr"][1] * (j / (n - 1)) ** 4) if j else 0.0 for j in range(n)]   # part « enroulement » (animée)
    T["w"] = [0.3 + 0.7 * (j / (n - 1)) ** 0.8 for j in range(n)]


def surface(r, l):
    """hauteur de la surface du tube (deux carrés à 45°, demi-côtés r et 0,94 r) à la distance latérale l, selon la normale orale."""
    b = 0.94 * r * math.sqrt(2)
    return max(r if abs(l) <= r else -1, b - abs(l))


nvent = 0
for s, tag in ((1, "r"), (-1, "l")):
    aile = group(s, f"aile_{tag}", (3.6, 19.5, 3.0), None)
    for ti, T in enumerate(TENT):
        P = np.array(T["P"])
        parent = aile
        for j in range(T["n"]):
            Lj, rj = T["Ls"][j], T["rs"][j]
            x0 = P[0] + T["X"][j]
            rot = (0, T["yaw"], T["alpha"]) if j == 0 else (0, 0, T["kap"][j])
            gname = group(s, f"{T['nom']}_{j + 1}_{tag}", (x0, P[1], P[2]), parent, rot)
            parent = gname
            dlt = 6.0 * (j % 2)
            phi_o = PHI_O + dlt
            xa = x0 - (2.4 if j == 0 else 0.25 * rj)          # la base plonge dans le dos
            xb = x0 + Lj + 0.5 * rj
            longueur = xb - xa
            for k, (beta, rr_) in enumerate(((-phi_o, rj), (-phi_o + 45, 0.94 * rj))):
                ins = 0.1 * k
                fa, fb = xa + ins, xb - ins
                faces = {}
                for fn, pl in PHI_LOCAL.items():
                    phi = (pl - beta) % 360
                    faces[fn] = uv_peau(cat_de(phi, phi_o), longueur, 2 * rr_, ti * 97 + j * 13 + k * 5 + (fn == "up") * 3 + s)
                faces["east"] = uv_peau("flanc", 2 * rr_, 2 * rr_, j + k)
                faces["west"] = uv_peau("flanc", 2 * rr_, 2 * rr_, j + k + 1)
                cube(s, gname, f"{T['nom']}_{j + 1}{'ab'[k]}_{tag}", (fa, P[1] - rr_, P[2] - rr_), (fb, P[1] + rr_, P[2] + rr_),
                     (x0, P[1], P[2]), (beta, 0, 0), faces)
            # ventouses : deux rangées en quinconce de part et d'autre du sillon, une seule sur le dernier tiers
            double = rj >= 0.7
            places = [(0.3, 0.45), (0.8, -0.45)] if double else [(0.55, 0.0)]
            if j == 0:
                places = [(0.62, 0.45)]
            for (fu, fl) in places:
                d = max(0.36, min(1.5, (0.72 if double else 1.15) * rj))
                l = fl * rj
                xc = x0 + fu * Lj
                hb = surface(rj, l) - 0.08
                htop = max(surface(rj, l + dd) for dd in np.linspace(-d / 2, d / 2, 9)) + 0.14 + 0.1 * rj
                hs = max(0.32, htop - hb)
                O = np.array((xc, P[1], P[2])) + hb * dvec(phi_o) + l * tvec(phi_o)
                gr = nvent % 6
                for k in range(2):
                    dd = d if k == 0 else d * 0.96
                    hh = hs if k == 0 else hs - 0.12
                    fac = {"east": [VENT[gr][0] + 0.5, VENT[gr][1] + 0.5, VENT[gr][0] + 15.5, VENT[gr][1] + 15.5]}
                    for fn in ("north", "south", "up", "down"):
                        fac[fn] = [FLANC_V[0] + 2, FLANC_V[1] + 0.5, FLANC_V[0] + 14, FLANC_V[1] + 0.5 + min(15, hh * 16)]
                    cube(s, gname, f"v{nvent}{'ab'[k]}_{tag}", (O[0] - 0.1, O[1] - dd / 2, O[2] - dd / 2),
                         (O[0] + hh, O[1] + dd / 2, O[2] + dd / 2), O, (45 * k, -phi_o, -90), fac)
                nvent += 1

# nœud de chair central et œil (groupe à la racine du corps, non mirroré)
group(1, "noeud", (0, 20.2, 2.4), None)
NO = groups["noeud"]
fn6 = lambda w, h, gr: {f: uv_peau("noeud", w, h, gr + i) for i, f in enumerate(("north", "south", "east", "west", "up", "down"))}
cube(1, "noeud", "noeud_a", (-2.1, 18.0, 2.3), (2.1, 22.4, 4.3), (0, 20.2, 3.3), (0, 0, 0), fn6(4.2, 4.4, 1))
cube(1, "noeud", "noeud_b", (-1.75, 17.75, 2.4), (1.75, 22.65, 4.15), (0, 20.2, 3.3), (0, 0, 45), fn6(3.5, 4.9, 9))
cube(1, "noeud", "noeud_c", (-2.6, 18.7, 2.35), (2.6, 21.7, 4.0), (0, 20.2, 3.3), (0, 0, 0), fn6(5.2, 3.0, 17))
group(1, "oeil", (0, 20.3, 4.3), "noeud")
iris_uv = [IRIS[0] + 0.5, IRIS[1] + 0.5, IRIS[0] + 15.5, IRIS[1] + 15.5]
cube(1, "oeil", "iris", (-0.95, 19.55, 4.15), (0.95, 21.05, 4.72), (0, 20.3, 4.4), (0, 0, 0),
     {"south": iris_uv, "east": iris_uv, "west": iris_uv, "up": iris_uv, "down": iris_uv})
group(1, "pupille", (0, 20.3, 4.72), "oeil")
fu = [FENTE[0] + 1, FENTE[1] + 1, FENTE[0] + 7, FENTE[1] + 15]
cube(1, "pupille", "fente", (-0.17, 19.7, 4.66), (0.17, 20.9, 4.86), (0, 20.3, 4.76), (0, 0, 0),
     {"south": fu, "east": fu, "west": fu, "up": fu, "down": fu})
group(1, "paupiere", (0, 21.12, 4.8), "oeil")
cube(1, "paupiere", "paupiere_h", (-1.1, 20.72, 4.6), (1.1, 21.12, 5.02), (0, 21.12, 4.8), (0, 0, 0), fn6(2.2, 0.42, 31))
cube(1, "oeil", "paupiere_b", (-1.05, 19.3, 4.35), (1.05, 19.62, 4.95), (0, 19.46, 4.6), (0, 0, 0), fn6(2.1, 0.3, 37))


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(nm) for nm, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(),
             "children": [bone("aile_r"), bone("aile_l"), bone("noeud")]}]

# ====================================================================== animations
# Valeurs écrites pour l'aile DROITE, dans la convention du mod (essentiel.md, Axes) :
#   x > 0 : le haut du groupe bascule vers l'arrière ; y > 0 : le côté droit avance (y < 0 : vers l'arrière) ;
#   z > 0 : le côté droit monte. Aux articulations, z < 0 enroule vers la face des ventouses.
# MIROIR : seul endroit qui donne le signe de l'aile gauche (réflexion x -> -x : y et z changent de signe).
def mirror(s, v):
    return (v[0], s * v[1], s * v[2])


class E:
    """Expression périodique : const + somme a·sin(360·k·t/L − ph) + somme a·max(0, sin(360·k·t/L − ph))^3 (« pic »)."""

    def __init__(self, c=0.0, sins=(), pics=()):
        self.c, self.sins, self.pics = c, list(sins), list(pics)

    def __add__(self, o):
        o = o if isinstance(o, E) else E(o)
        return E(self.c + o.c, self.sins + o.sins, self.pics + o.pics)

    __radd__ = __add__

    def __mul__(self, f):
        return E(self.c * f, [(a * f, k, p) for a, k, p in self.sins], [(a * f, k, p) for a, k, p in self.pics])

    __rmul__ = __mul__

    def molang(self, L):
        out = [f"{self.c:.2f}"] if abs(self.c) > 0.005 else []
        for a, k, p in self.sins:
            if abs(a) > 0.02:
                out.append(f"{a:+.2f}*math.sin(q.anim_time*{360 * k / L:.4g}-{p % 360:.0f})")
        for a, k, p in self.pics:
            if abs(a) > 0.02:
                out.append(f"{a:+.2f}*math.pow(math.max(0,math.sin(q.anim_time*{360 * k / L:.4g}-{p % 360:.0f})),3)")
        s = "".join(out).lstrip("+") or "0"
        assert len(s) <= 500, len(s)
        return s


def S(a, k, ph=0.0):
    return E(0, [(a, k, ph)])


def PIC(a, k, ph=0.0):
    return E(0, [], [(a, k, ph)])


def kf(ch, t, x, y, z):
    f = lambda v: v if isinstance(v, str) else str(round(v + 0.0, 3))
    return {"channel": ch, "data_points": [{"x": f(x), "y": f(y), "z": f(z)}], "time": round(t, 4), "interpolation": "linear"}


def gu(nm):
    return groups[nm]["uuid"]


def neg(e):
    return e * -1


def boucle(nom, L, aile, fan, onde, coil, oeil=None):
    """aile : (x, y, z) en E pour le groupe aile_ ; fan[i] : (x, y, z) ajoutés à la racine du tentacule i ;
    onde : dict(az, ay, k, dphi, k2, a2) ; coil : E (1 = enroulement du modèle, 0 = déroulé, > 1 = plus serré)."""
    A = {}
    for s, tag in ((1, "r"), (-1, "l")):
        ax, ay, az = aile
        A[gu(f"aile_{tag}")] = {"name": f"aile_{tag}", "type": "bone", "keyframes": [
            kf("rotation", 0, ax.molang(L), (ay * s).molang(L), (az * s).molang(L))]}
        for ti, T in enumerate(TENT):
            for j in range(T["n"]):
                w = T["w"][j]
                ph = T["ph"] + onde["dphi"] * j
                ez = S(onde["az"] * w, onde["k"], ph) + S(onde.get("a2", 0) * w, onde.get("k2", 1), ph * 0.6 + 40)
                ey = S(onde["ay"] * w, onde["k"], ph + 90)
                ez = ez + (coil + (-1)) * T["coil"][j]
                ex = E()
                if j == 0:
                    fx, fy, fz = fan[ti]
                    ex, ey, ez = ex + fx, ey + fy, ez + fz
                nm = f"{T['nom']}_{j + 1}_{tag}"
                A[gu(nm)] = {"name": nm, "type": "bone", "keyframes": [
                    kf("rotation", 0, ex.molang(L), (ey * s).molang(L), (ez * s).molang(L))]}
    if oeil:
        pup, lid = oeil
        A[gu("pupille")] = {"name": "pupille", "type": "bone", "keyframes": [kf("position", 0, pup.molang(L), "0", "0")]}
        A[gu("paupiere")] = {"name": "paupiere", "type": "bone", "keyframes": [kf("scale", 0, "1", lid.molang(L) if lid else "1", "1")]}
    return {"uuid": nuid(), "name": nom, "loop": "loop", "override": False, "length": L, "snapping": 24,
            "selected": nom == "idle", "animators": A}


Z3 = (E(), E(), E())


def lid_expr(L, k, ph):
    """paupière : 1 = ouverte (bandeau de 0,4 px), 3,7 = fermée ; clignement bref quand le sinus dépasse 0,93."""
    return f"1+2.7*math.pow(math.max(0,math.sin(q.anim_time*{360 * k / L:.4g}-{ph:.0f})-0.93)/0.07,2)"


idle_pic = lambda a: PIC(a, 1, 150)
idle = boucle("idle", 8.0,
              (E(), S(-1.0, 2, 90) + idle_pic(6), S(1.5, 2) + idle_pic(7)),
              [(E(), E(), idle_pic(6)), Z3, (E(), E(), idle_pic(-7))],
              dict(az=3.0, ay=1.6, k=2, dphi=38, a2=1.4, k2=1),
              E(1.0) + idle_pic(-0.6),
              oeil=(S(0.32, 1, 20) + S(0.14, 3, 60), None))
idle["animators"][gu("paupiere")]["keyframes"][0]["data_points"][0]["y"] = lid_expr(8.0, 2, 300)

walk = boucle("walk", 1.6, (E(4), E(-14), E(-4) + S(2, 2)), [Z3, Z3, Z3],
              dict(az=3.5, ay=2.5, k=1, dphi=45), E(0.85))
run = boucle("run", 1.0, (E(10), E(-40), E(-12) + S(2.5, 2)), [(E(), E(), E(-6)), Z3, (E(), E(), E(8))],
             dict(az=4.5, ay=3.0, k=1, dphi=55), E(0.45))
sneak = boucle("sneak", 4.0, (E(-4), E(-20), E(-42) + S(0.8, 1)), [(E(), E(), E(-30)), (E(), E(), E(-18)), (E(), E(), E(2))],
               dict(az=1.2, ay=0.8, k=1, dphi=40), E(1.8))
fly = boucle("fly", 2.4, (E(30), E(-8) + S(4, 1, 90), E(4) + S(16, 1)), [(E(), E(), E(6)), Z3, (E(), E(), E(-6))],
             dict(az=5.0, ay=2.0, k=1, dphi=35), E(0.85) + S(0.3, 1, 180))
glide = boucle("glide", 3.6, (E(), E(18), E(2) + S(3, 1)), [(E(), E(), E(8)), Z3, (E(), E(), E(-10))],
               dict(az=2.5, ay=1.5, k=1, dphi=30), E(0.5))
swim = boucle("swim", 3.6, (E(), E(10) + S(10, 2), E(-4) + S(6, 2)), [Z3, Z3, Z3],
              dict(az=6.0, ay=3.0, k=2, dphi=50), E(0.7))
fall = boucle("fall", 2.0, (E(18), E(-6), E(10) + S(2, 2)), [(E(), E(), E(10)), Z3, (E(), E(), E(-12))],
              dict(az=3.0, ay=1.5, k=2, dphi=40), E(0.4))
mount = boucle("mount", 4.0, (E(), E(-6), E(4) + S(2.5, 1)), [Z3, Z3, Z3],
               dict(az=2.5, ay=1.5, k=1, dphi=38), E(1.0))
sleep = boucle("sleep", 4.0, (E(), E(-24), E(-16) + S(1.2, 1)), [(E(), E(), E(-10)), Z3, (E(), E(), E(6))],
               dict(az=0.8, ay=0.5, k=1, dphi=35), E(1.5))
sleep["animators"][gu("paupiere")] = {"name": "paupiere", "type": "bone", "keyframes": [kf("scale", 0, 1, 3.7, 1)]}


# ---------------------------------------------------------------- animations once (échantillonnées)
def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def echant(nom, L, f, n=None, effets=None, loop="once"):
    """f(t) -> {nom de groupe: {"rotation": (x,y,z), "scale": (x,y,z)}} pour l'aile droite et le nœud ; l'aile gauche par mirror()."""
    n = n or int(round(L * 20))
    A = {}
    for q in range(n + 1):
        t = L * q / n
        for nm, ch in f(t).items():
            for s, tag in (((1, "r"), (-1, "l")) if nm.endswith("_X") else ((1, ""),)):
                g = nm[:-1] + tag if nm.endswith("_X") else nm
                a = A.setdefault(gu(g), {"name": g, "type": "bone", "keyframes": []})
                for c, v in ch.items():
                    v = mirror(s, v) if c == "rotation" else v
                    a["keyframes"].append(kf(c, t, *v))
    if effets:
        A["effects"] = {"name": "Effects", "type": "effect", "keyframes": effets}
    return {"uuid": nuid(), "name": nom, "loop": loop, "override": False, "length": L, "snapping": 24, "selected": False,
            "animators": A}


def att(t):
    """attack : anticipation (les tentacules se roulent et reculent), fouet vers l'avant qui court de la base à la pointe,
    gel bref, retour."""
    out = {"aile_X": {"rotation": (0, -12 * bump(t, 0, 0.14, 0.14, 0.22) + 24 * bump(t, 0.16, 0.26, 0.4, 0.78),
                                   4 * bump(t, 0.16, 0.26, 0.4, 0.78))}}
    for T in TENT:
        for j in range(T["n"]):
            r = 0.011 * j
            arme = 0.9 * bump(t, 0, 0.14, 0.14, 0.24 + r)                  # roulé
            fouet = bump(t, 0.17 + r, 0.24 + r, 0.4 + r, 0.78)            # déroulé brutal, au-delà de la pose
            z = T["coil"][j] * (0.9 * arme - 0.8 * fouet) + 3.5 * T["w"][j] * (fouet - arme)
            out[f"{T['nom']}_{j + 1}_X"] = {"rotation": (0, 2.5 * T["w"][j] * fouet, z)}
    return out


def blesse(t):
    """hurt : recul brusque, pointes qui se roulent pour se protéger, tremblement amorti ; l'œil se ferme."""
    rec = bump(t, 0, 0.06, 0.22, 0.7)
    out = {"aile_X": {"rotation": (0, -18 * rec, 5 * rec)}}
    for T in TENT:
        for j in range(T["n"]):
            tr = math.sin(2 * math.pi * (t - 0.012 * j) * 8) * (1 - sm(t, 0.05, 0.7)) * bump(t, 0, 0.04, 0.5, 0.75)
            out[f"{T['nom']}_{j + 1}_X"] = {"rotation": (0, 0, 0.6 * T["coil"][j] * rec + 3.0 * T["w"][j] * tr)}
    out["paupiere"] = {"scale": (1, 1 + 2.7 * bump(t, 0.02, 0.07, 0.35, 0.5), 1)}
    return out


SON = [{"channel": "sound", "data_points": [{"effect": "entity.slime.squish", "file": ""}], "time": 0.2}]
EQ, UQ = 2.0, 1.6


def equipe(t):
    """event_equip : le nœud gonfle, puis chaque tentacule sort du dos roulé serré et se déroule de la base vers la pointe."""
    k = 0.25 + 0.75 * sm(t, 0, 0.35) + 0.08 * bump(t, 0.3, 0.38, 0.42, 0.6)
    out = {"noeud": {"scale": (k, k, k)}}
    for i, T in enumerate(TENT):
        t0 = 0.15 + 0.14 * i
        e = 0.04 + 0.96 * sm(t, t0, t0 + 0.45)
        for j in range(T["n"]):
            tj = t0 + 0.3 + 0.045 * j
            roule = 1 - sm(t, tj, tj + 0.4)
            detente = bump(t, tj + 0.3, tj + 0.45, tj + 0.55, tj + 0.95)
            ch = {"rotation": (0, 0, -16 * roule + 0.35 * -T["coil"][j] * detente)}
            if j == 0:
                ch["scale"] = (e, e, e)
            out[f"{T['nom']}_{j + 1}_X"] = ch
    return out


def desequipe(t):
    """event_unequip : les tentacules s'enroulent, rentrent dans le dos l'un après l'autre, puis le nœud disparaît."""
    k = 1 - sm(t, 1.1, 1.5)
    out = {"noeud": {"scale": (k, k, k)}, "aile_X": {"scale": (1 if t < UQ - 0.01 else 0,) * 3}}
    for i, T in enumerate(TENT):
        t0 = 0.45 + 0.12 * (len(TENT) - 1 - i)
        e = 1 - 0.97 * sm(t, t0, t0 + 0.5)
        for j in range(T["n"]):
            tj = 0.04 * (T["n"] - 1 - j)
            ch = {"rotation": (0, 0, -16 * sm(t, tj, tj + 0.5))}
            if j == 0:
                ch["scale"] = (e, e, e)
            out[f"{T['nom']}_{j + 1}_X"] = ch
    return out


attack = echant("attack", 0.8, att)
hurt = echant("hurt", 0.8, blesse)
equip = echant("event_equip", EQ, equipe, effets=SON)
unequip = echant("event_unequip", UQ, desequipe)

ANIMS = [idle, walk, run, sneak, fly, glide, swim, fall, mount, sleep, attack, hurt, equip, unequip]

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": b64png(tex, f"{NOM}.png")}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": b64png(tex_e, f"{NOM}_e.png")})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures,
         "animations": ANIMS}

from sons import limiter_sons
from ambiance import ajouter_ambiance
limiter_sons(model)
ajouter_ambiance(model)
assert len(model["animations"]) <= 32

os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


def ngroupes(n):
    return 1 + sum(ngroupes(c) for c in n.get("children", []) if isinstance(c, dict))


print(len(elements), "cubes ;", sum(ngroupes(n) for n in outliner), "groupes ; profondeur", max(depth(n) for n in outliner), ";",
      len(model["animations"]), "anims ;", sum(len(b["keyframes"]) for a in model["animations"] for b in a["animators"].values()),
      "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;", nvent, "ventouses")
