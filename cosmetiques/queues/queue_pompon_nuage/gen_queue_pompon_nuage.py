"""Queue pompon nuage : pompon de lapin en petit nuage tout rond, ensemble « Nuage Guimauve » (pièce sœur : oreilles_lapin_nuage). Design original.
Écrit queue_pompon_nuage.png, queue_pompon_nuage_e.png et .build/queue_pompon_nuage_brut.bbmodel à côté de ce script.

7 lobes ronds (boules de coton) qui se chevauchent. Chaque lobe = touffes rondes découpées par alpha, posées tangentes sur sa sphère
et tournées vers l'extérieur (recette « écailles rondes »), autour d'une âme pleine plus petite (cubes croisés) qui bouche les creux.
Rond sous tous les angles, sans plan vu par la tranche au milieu. Crème-blanc, bords ombrés crème-lavande, creux lavande, un lobe bas
à pointe rose. Aucun élément bestial. (Essais écartés, voir le rapport : disques croisés par le centre = aspect cristal ; boules voxel = cubique.)
"""
import base64, io, json, math, os, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

AVEC_E = True       # calque _e embarqué en seconde texture, jamais assigné aux faces (correctif du clignotement annoncé le 2026-11-03, à vérifier en jeu)
NOM = "queue_pompon_nuage"
TEX = 512
TAU = 2 * math.pi

# ------------------------------------------------------------------ couleurs (mêmes teintes qu'oreilles_lapin_nuage)
CREME = np.array((255, 249, 247), np.float32)
CREME_OMB = np.array((228, 218, 240), np.float32)   # ombre froide : compense le saumon des lumières chaudes
BLANC = np.array((255, 255, 255), np.float32)
ROSE_L = np.array((255, 210, 226), np.float32)
LAV = np.array((208, 192, 248), np.float32)
E_FOND = (13, 10, 18)                               # fond additif très sombre
E_REFLET = np.array((58, 50, 82), np.float32)       # reflet doux du lobe central


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


# ------------------------------------------------------------------ textures
RES = 120           # une touffe = 120 texels de côté


def paint_tuft(nb, phase, seed, rose=0.0, reflet=False, tint=0.0):
    """Touffe de coton vue de face : disque à festons larges et peu profonds, blanc au centre, ombre lavande douce vers le bord
    (ombre de recouvrement : là où la touffe voisine passe dessus). Rose éventuel sur le haut des festons. Renvoie (rgba, rgba_e)."""
    ss = 4
    n = RES * ss
    yy, xx = np.mgrid[0:n, 0:n]
    x = (xx + 0.5) / n * 2 - 1
    y = (yy + 0.5) / n * 2 - 1
    rho = np.hypot(x, y)
    th = np.arctan2(y, x) + phase
    per = TAU / nb
    k = np.floor(th / per).astype(int) % nb
    loc = (th / per) - np.floor(th / per) - 0.5
    amp = np.random.default_rng(seed).uniform(0.75, 1.0, nb)[k]
    b = np.sqrt(np.clip(1 - (2 * loc) ** 2, 0, 1))
    R = 0.86 + 0.12 * b * amp
    inside = rho < R
    t = rho / R
    c = np.empty(x.shape + (3,), np.float32)
    c[...] = BLANC
    c = lerp(c, CREME, np.clip((t - 0.25) / 0.3, 0, 1)[..., None])
    c = lerp(c, LAV, tint)
    c = lerp(c, CREME_OMB, (np.clip((t - 0.55) / 0.4, 0, 1) * 0.8)[..., None])    # bord : ombre douce sur la touffe voisine
    if rose:
        c = lerp(c, ROSE_L, (np.clip((t - 0.45) / 0.25, 0, 1) * rose)[..., None])      # pointe de rose, sans liseré foncé
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((RES, RES), Image.LANCZOS))
    al = np.array(Image.fromarray((inside * 255).astype(np.uint8), "L").resize((RES, RES), Image.LANCZOS)) > 110
    out = np.dstack([rgb, al * 255]).astype(np.uint8)
    out[~al, :3] = LAV.astype(np.uint8)
    e = np.zeros((RES, RES, 4), np.uint8)
    e[al] = (*E_FOND, 255)
    if reflet:
        jj, ii = np.mgrid[0:RES, 0:RES]
        d = np.hypot((ii + 0.5) / RES - 0.42, (jj + 0.5) / RES - 0.4) / 0.2
        g = np.clip(1 - d, 0, 1) ** 1.5
        ec = lerp(np.array(E_FOND, np.float32), E_REFLET, g[..., None])
        e[..., :3] = np.where(al[..., None], ec.astype(np.uint8), e[..., :3])
    return out, e


def paint_core(seed, W=32):
    """Âme pleine : lavande grisée duveteuse, plus sombre que les touffes (elle ne se voit qu'au fond des creux, comme une ombre)."""
    r = np.random.default_rng(seed)
    blot = np.array(Image.fromarray((r.random((5, 5)) * 255).astype(np.uint8), "L").resize((W, W), Image.BICUBIC), np.float32) / 255
    c = lerp(CREME_OMB, LAV, np.clip(blot * 1.2 - 0.1, 0, 1)[..., None])
    return np.dstack([c, np.full((W, W), 255.0)]).astype(np.uint8)


UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def atlas():
    imgs, glow = {}, {}
    variants = {"d_centre": dict(nb=6, phase=0.1, seed=1, reflet=True), "d_haut": dict(nb=5, phase=0.0, seed=2),
                "d_dos": dict(nb=6, phase=0.4, seed=3, tint=0.22), "d_bas": dict(nb=5, phase=0.25, seed=4, tint=0.38),
                "d_rose": dict(nb=5, phase=0.15, seed=5, rose=0.7, tint=0.0)}
    for name, kw in variants.items():
        imgs[name], glow[name] = paint_tuft(**kw)
    for i in range(2):
        imgs[f"core{i}"] = paint_core(10 + i)
        glow[f"core{i}"] = np.dstack([np.broadcast_to(np.array(E_FOND, np.uint8), (32, 32, 3)), np.full((32, 32), 255, np.uint8)])
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    x, y, shelf = 0, 0, 0
    for n, im in imgs.items():
        h, w = im.shape[:2]
        if x + w + 1 > TEX:
            x, y, shelf = 0, y + shelf + 1, 0
        assert y + h <= TEX - 6, "atlas plein"
        UV[n] = (x, y, x + w, y + h)
        tex[y:y + h, x:x + w] = im
        tex_e[y:y + h, x:x + w] = glow[n]
        x += w + 1
        shelf = max(shelf, h)
    tex[TEX - 4:TEX - 2, TEX - 4:TEX - 2] = 0
    assert set(np.unique(tex[..., 3])) <= {0, 255} and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence"
    out = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        bb = io.BytesIO()
        im.save(bb, "PNG", optimize=True)
        out.append("data:image/png;base64," + base64.b64encode(bb.getvalue()).decode())
    return out


TEX_B64, TEX_E_B64 = atlas()

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def V(*a):
    return np.array(a, float)


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx, ordre du mod et du renderer."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if abs(R[2, 0]) > 0.99999:
        return math.degrees(math.atan2(-R[0, 1] if R[2, 0] > 0 else R[0, 1], R[1, 1])), math.degrees(ry), 0.0
    return math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(ry), math.degrees(math.atan2(R[1, 0], R[0, 0]))


def Rx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Ry(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def Rz(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


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


def disc(g, name, c, r, R, tile, th=0.3):
    """Plaque carrée 2r x 2r, épaisseur th, normale = 3e colonne de R. Disque festonné découpé par alpha, tranches transparentes."""
    t = UV[tile]
    cube(g, name, c - (r, r, th / 2), c + (r, r, th / 2), c, euler(R),
         {"south": list(t), "north": [t[2], t[1], t[0], t[3]], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def core(g, name, c, a, R, tile):
    t = list(UV[tile])
    cube(g, name, c - a, c + a, c, euler(R), {f: t for f in ("north", "south", "east", "west", "up", "down")})


def frame_from_normal(nrm, spin):
    """Repère dont le Z local suit nrm ; spin tourne le disque dans son plan (varie la place des touffes)."""
    nrm = nrm / np.linalg.norm(nrm)
    ref = V(0, 1, 0) if abs(nrm[1]) < 0.9 else V(1, 0, 0)
    ax = np.cross(ref, nrm)
    ax /= np.linalg.norm(ax)
    ay = np.cross(nrm, ax)
    return np.column_stack([ax, ay, nrm]) @ Rz(spin)


ATTACH = V(0, 13.0, 2.4)        # point d'attache sur le bas du dos (hanche à y = 12, dos à z = 2)
C = V(0, 13.0, 4.7)             # centre du pompon : bord avant à z ≈ 2,6 au centre (dos à 2), bas à y ≈ 10 ; un peu au-dessus de la hanche pour laisser passer les jambes
# (nom, décalage depuis C, rayon, variante des touffes)
LOBES = [("lobe_centre", V(0.0, 0.0, 0.0), 2.05, "d_centre"),
         ("lobe_haut_g", V(-1.25, 1.0, -0.1), 1.45, "d_haut"),
         ("lobe_haut_d", V(1.2, 1.05, 0.15), 1.4, "d_haut"),
         ("lobe_bas_g", V(-1.15, -0.95, 0.22), 1.35, "d_bas"),
         ("lobe_bas_d", V(1.25, -0.9, -0.05), 1.4, "d_rose"),
         ("lobe_dos", V(0.08, 0.17, 1.25), 1.45, "d_dos"),
         ("lobe_sommet", V(0.04, 1.42, 0.52), 1.2, "d_haut")]

base = group("pompon_base", ATTACH)                  # balancement de toute la queue autour de l'attache (états)
fx = group("pompon_fx", ATTACH, parent=base)         # attaque et blessure seulement, par-dessus l'état
pom = group("pompon", C, parent=fx)                  # écrasement / étirement et rebond, autour du centre
LOBE_G = []


def fibo(n):
    """n directions réparties régulièrement sur la sphère."""
    out = []
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(1 - y * y)
        a = i * math.pi * (3 - math.sqrt(5))
        out.append(V(rr * math.cos(a), y, rr * math.sin(a)))
    return out


CENTRES = [C + off + V(0.013, 0.017, 0.011) * k for k, (_, off, _, _) in enumerate(LOBES)]
for k, (name, off, r, tile) in enumerate(LOBES):
    c = CENTRES[k]
    g = group(name, c, parent=pom)
    LOBE_G.append(g)
    Rl = Ry(13 + 29 * k) @ Rx(7 + 17 * k)
    # touffes tangentes : chaque disque regarde vers l'extérieur, posé sur la sphère du lobe ; celles enfouies dans un voisin sont omises
    tr = 0.62 * r
    d = math.sqrt(r * r - tr * tr)
    n = 16 if k == 0 else 13
    j = 0
    for dv in fibo(n):
        dv = Rl @ dv
        p = c + dv * d
        if any(np.linalg.norm(p - CENTRES[m]) < LOBES[m][2] * 0.92 for m in range(len(LOBES)) if m != k):
            continue
        if p[2] < 2.7:          # touffe tournée vers le dos : jamais vue
            continue
        disc(g, f"{name}_t{j}", p, tr, frame_from_normal(dv, 37 * j + 11 * k), tile)
        j += 1
    # âme pleine : deux cubes croisés (trois pour le lobe central), sous les touffes ; visible seulement au fond des creux (lavande)
    core(g, f"{name}_ame", c, 0.46 * r, Rl, f"core{k % 2}")
    core(g, f"{name}_ame2", c, 0.45 * r, Rl @ Ry(45) @ Rx(35.26), f"core{(k + 1) % 2}")
    if k == 0:
        core(g, f"{name}_ame3", c, 0.44 * r, Rl @ Rz(45) @ Ry(20), "core0")


def bone_node(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "rotation": [0, 0, 0], "children": [bone_node(base)]}]

# ------------------------------------------------------------------ animations
# Intention pour la queue qui part vers +Z : lift > 0 relève le pompon, wag > 0 le porte vers +X (droite du joueur), roll > 0 monte le côté droit.
# MIROIR D'AXES : seul endroit à toucher si la convention change. Guide, section 3 : +X = le haut part vers l'arrière, donc ce qui pointe
# vers +Z descend ; +Y = le côté droit avance, donc ce qui pointe vers +Z part vers +X.
SX, SY = -1, +1


def mirror(lift, wag, roll=0.0):
    return SX * lift, SY * wag, roll


def squash(s, axis=1):
    """Étirement s le long d'un axe (1 = Y, 2 = Z), volume conservé."""
    o = 1 / math.sqrt(1 + s)
    v = [o, o, o]
    v[axis] = 1 + s
    return tuple(v)


def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 3)), "y": str(round(v[1] + 0.0, 3)), "z": str(round(v[2] + 0.0, 3))}],
            "time": round(t, 3), "interpolation": "linear"}


def anim(name, length, tracks, n_kf=None, loop="loop"):
    """tracks : {groupe: {canal: f(t) -> (x, y, z)}}, échantillonné de t = 0 à t = length inclus (linéaire)."""
    n = n_kf or max(10, int(round(length * 10)))
    times = [i * length / n for i in range(n + 1)]
    A = {}
    for g, chans in tracks.items():
        A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(ch, t, f(t)) for ch, f in chans.items() for t in times]}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24, "selected": name == "idle", "animators": A}


def mul(a, b):
    return tuple(x * y for x, y in zip(a, b))


def jiggle(amp, freq_cycles, L, lag=0.7, extra=None):
    """Petit gonflement déphasé de chaque lobe : effet duveteux, gélatineux. extra(t) module l'amplitude."""
    tr = {}
    for k, g in enumerate(LOBE_G):
        def f(t, k=k):
            m = extra(t) if extra else 1.0
            s = amp * m * math.sin(TAU * freq_cycles * t / L - lag * k)
            return (1 + s, 1 + s, 1 + s)
        tr[g] = {"scale": f}
    return tr


def state(name, L, base_rot, pom_scale, pom_pos, lobes=None, n_kf=None):
    tr = {base: {"rotation": lambda t: mirror(*base_rot(t))}, pom: {"scale": pom_scale, "position": pom_pos}}
    if lobes:
        tr.update(lobes)
    return anim(name, L, tr, n_kf=n_kf)


# idle 8 s : respiration (période 4 s) + frétillement occasionnel vers 5,2 s, revenu à zéro bien avant la fin
def fret(t):
    return bump(t, 5.15, 5.3, 5.85, 6.5)


def idle_rot(t):
    e = fret(t)
    w = math.sin(TAU * 7 * (t - 5.15))
    return 3 * e + 1.5 * math.sin(TAU * t / 8), 14 * e * w, 7 * e * math.sin(TAU * 7 * (t - 5.15) + 1.2)


idle = state("idle", 8.0, idle_rot,
             lambda t: mul((1 + 0.025 * math.sin(TAU * 2 * t / 8),) * 3, squash(0.07 * fret(t) * math.cos(TAU * 7 * (t - 5.15)))),
             lambda t: (0, 0.08 * math.sin(TAU * 2 * t / 8), 0),
             jiggle(0.03, 14, 8.0, extra=lambda t: 0.4 + 1.6 * fret(t)), n_kf=96)


def hop(L, A_pos, A_sq, lift0, A_lift, A_wag):
    """Rebond élastique au pas : 2 pas par cycle. Pompon au plus bas au contact (écrasé, avec un léger retard), étiré à la remontée."""
    ph = lambda t: TAU * 2 * t / L
    rot = lambda t: (lift0 + A_lift * math.cos(ph(t) - 0.5), A_wag * math.sin(TAU * t / L), 0.7 * A_wag * math.sin(TAU * t / L - 0.4))
    sc = lambda t: squash(-A_sq * math.cos(ph(t) - 0.9))
    pos = lambda t: (0, A_pos * (0.5 - 0.5 * math.cos(ph(t))), 0)
    return rot, sc, pos


walk = state("walk", 1.6, *hop(1.6, 0.28, 0.09, 0.0, 2.5, 5.0), lobes=jiggle(0.04, 2, 1.6, lag=0.5), n_kf=16)
run = state("run", 1.0, *hop(1.0, 0.42, 0.13, 6.0, 3.5, 3.5), lobes=jiggle(0.05, 2, 1.0, lag=0.5), n_kf=16)
# sneak : se plaque contre le dos (aplati en Z, un peu élargi), respiration discrète
sneak = state("sneak", 3.0, lambda t: (4 + 1.0 * math.sin(TAU * t / 3), 0, 0),
              lambda t: (1.09 + 0.015 * math.sin(TAU * t / 3), 1.07 + 0.015 * math.sin(TAU * t / 3), 0.76),
              lambda t: (0, 0, -0.7), jiggle(0.015, 1, 3.0), n_kf=24)
# fly : joueur debout, le pompon flotte et ondule doucement
fly = state("fly", 2.4, lambda t: (-5 + 3 * math.sin(TAU * t / 2.4), 5 * math.sin(TAU * t / 2.4 + 0.8), 3 * math.sin(TAU * t / 2.4)),
            lambda t: squash(0.05 * math.sin(TAU * 2 * t / 2.4)), lambda t: (0, 0.15 * math.sin(TAU * t / 2.4), 0),
            jiggle(0.03, 2, 2.4), n_kf=24)
# glide : corps couché, le pompon file vers les pieds (lift < 0) étiré dans le vent, frémit vite
glide = state("glide", 3.6, lambda t: (-12 + 1.5 * math.sin(TAU * t / 3.6), 3 * math.sin(TAU * 3 * t / 3.6), 0),
              lambda t: squash(0.1 + 0.03 * math.sin(TAU * 6 * t / 3.6)), lambda t: (0, -0.15, 0),
              jiggle(0.04, 9, 3.6, lag=1.1), n_kf=54)
# fall : le pompon reste en arrière du mouvement, donc monte et s'étire vers le haut
fall = state("fall", 1.5, lambda t: (12 + 3 * math.sin(TAU * t / 1.5), 2 * math.sin(TAU * 2 * t / 1.5), 0),
             lambda t: squash(0.1 + 0.04 * math.sin(TAU * 2 * t / 1.5)), lambda t: (0, 0.2, 0),
             jiggle(0.04, 3, 1.5), n_kf=18)
# swim : corps couché, ondulation latérale
swim = state("swim", 2.0, lambda t: (-8 + 2 * math.sin(TAU * 2 * t / 2.0), 8 * math.sin(TAU * t / 2.0), 3 * math.sin(TAU * t / 2.0 - 0.6)),
             lambda t: squash(0.06 + 0.03 * math.sin(TAU * 2 * t / 2.0), axis=2), lambda t: (0, 0, 0),
             jiggle(0.03, 2, 2.0), n_kf=20)
# mount : assis, un peu tassé, respiration ample
mount = state("mount", 3.0, lambda t: (2 * math.sin(TAU * t / 3), 0, 0),
              lambda t: mul((1 + 0.03 * math.sin(TAU * t / 3),) * 3, squash(-0.07)), lambda t: (0, 0.05 * math.sin(TAU * t / 3), 0),
              jiggle(0.02, 1, 3.0), n_kf=24)
# sleep : tassé, légèrement tombant, respiration très lente
sleep = state("sleep", 4.0, lambda t: (-4 + 1.0 * math.sin(TAU * t / 4), 0, 0),
              lambda t: mul((1 + 0.02 * math.sin(TAU * t / 4),) * 3, squash(-0.06)), lambda t: (0, -0.1, 0),
              n_kf=24)


# attack, hurt : une fois, par-dessus l'état, seul pompon_fx bouge, dernière image au neutre
def end_env(t):
    return 1 - sm(t, 0.55, 0.76)


def att_sc(t):
    v = 0.16 * math.sin(TAU * 3 * t) * math.exp(-4.5 * t) * end_env(t)
    return (1 + v, 1 + v, 1 + v)


attack = anim("attack", 0.8, {fx: {"scale": att_sc,
                                   "rotation": lambda t: mirror(8 * math.sin(TAU * 2.5 * t) * math.exp(-5 * t) * end_env(t), 0, 0)}},
              n_kf=24, loop="once")


def hurt_rot(t):
    e = math.exp(-4 * t) * end_env(t) * sm(t, 0, 0.03)
    return mirror(6 * e * math.sin(TAU * 4 * t), 12 * e * math.sin(TAU * 9 * t), 7 * e * math.sin(TAU * 9 * t + 1.1))


hurt = anim("hurt", 0.8, {fx: {"rotation": hurt_rot,
                               "scale": lambda t: squash(-0.12 * bump(t, 0.0, 0.05, 0.1, 0.45)),
                               "position": lambda t: (0.25 * math.exp(-4 * t) * end_env(t) * math.sin(TAU * 11 * t), 0, 0)}},
            n_kf=32, loop="once")

ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, attack, hurt]

assert 40 <= len(elements) <= 100, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": TEX_B64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": TEX_E_B64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko")
