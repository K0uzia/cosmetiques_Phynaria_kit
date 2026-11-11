"""Capuche lapin-nuage (ensemble Kawaii, tête) : remplace « Oreilles de lapin-nuage » (archives/chapeaux/oreilles_kawaii,
« les trucs kawaii sont tous bof », « revois les têtes », 2026-11-08). Design original.

Idée : une capuche de peluche lilas, dodue comme un nuage, bordée de bouffées de nuage crème qui encadrent le visage (le
visage reste entièrement dégagé), deux grandes oreilles de lapin molles (intérieur rose bonbon, la gauche pliée à mi-hauteur),
un petit cœur de sucre au front et deux cordons à pompons de nuage qui pendent sous les joues.
Pourquoi une capuche : les oreilles seules (deux plaques pâles posées sur la tête) se lisaient blanches et minuscules en
jeu ; la capuche donne une vraie masse ronde et colorée autour de la tête (schéma du bébé : tête plus grosse et plus ronde),
change de type de pièce (fini les accessoires posés, tete.md) et garde les oreilles, qui portent l'expression.

Recherche (sources dans .claude/styles/kawaii.md et .claude/references/animaux/lapins-rongeurs.md) :
- capuches et bonnets de lapin réels : corps de capuche + oreilles en deux pièces (extérieur, intérieur cousu), oreilles
  légèrement rembourrées mais souples, cordons à pompons sous les joues, bordure duveteuse autour du visage ;
- oreilles = baromètre de l'humeur du lapin : dressées (joie, écoute), une pliée (perplexité), tombantes (tristesse),
  plaquées en arrière (peur, vent, pluie) ; frémissements brefs et irréguliers ;
- animation : action secondaire et suivi (follow-through) : le bout des oreilles suit avec retard et continue après l'arrêt.
Leçon du set (avis mochi/arc-en-ciel) : des pastels très clairs se lisent blancs en jeu → couleurs franches (lilas moyen,
rose bonbon), le crème réservé à la bordure, volumes doux.

Volume : chaque bouffée est un polyèdre convexe circonscrit à un ellipsoïde (plans tangents en spirale de Fibonacci, recette
de familier_kawaii_mochi), facettes = peaux de 0,3 px découpées par alpha autour d'une âme pleine ; les texels d'une bouffée
fixe qui entrent dans une autre bouffée fixe sont transparents (on ne voit que la surface de l'union). Chaque bouffée de la
capuche est coupée par un plan qui la garde hors de la tête : face intérieure à x, z ≥ 4,62, dessous du dôme à y 32,62,
coins par |x|+|z| ≥ 9,24 (tete.md) ; plans décalés de 0,08 à 0,25 px d'une bouffée à l'autre (pas de faces coplanaires).
Peinture en espace monde depuis la normale lissée de l'ellipsoïde, compensée de l'éclairage par face : on lit des boules.

Animations (pièce portée : pas d'attack ni de hurt) : idle 8 s (respiration des oreilles, frémissement de l'oreille droite,
la pliée qui se relève et retombe, écoute), walk, run, sneak (oreilles basses sur les côtés), fly, glide, fall (oreilles
soulevées), swim, sleep (tombantes) ; overlay_oreilles (Molang) : oreilles qui tombent quand la vie baisse (sous 60 %, en
douceur), plaquées sous la pluie, petits frémissements au hasard (q.life_time, q.instance_seed) ;
event_jump / event_land : les oreilles suivent avec retard et rebondissent ; event_equip (1 s) : la capuche gonfle comme une
guimauve, la bordure fait « plop », les oreilles poussent et le bout plié retombe, le cœur en dernier (un son) ;
event_unequip : petite inspiration, puis tout rétrécit.
Fonctions avancées : phys_pompon_*_g100 (cordons qui pendent, gravité du mod), overlay_, event_*, calque _e (cœur de sucre).
À juger en jeu : phys_ (non simulé), overlay Molang (vie, pluie, hasard), _e de nuit, casque porté (Armure).
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
from reactions import retirer_reactions

AVEC_E = True
NOM = "capuche_kawaii"
TEX = 512
SS = 3
TAU = 2 * math.pi

# ------------------------------------------------------------------ palette (couleurs franches, ombres froides)
LILAS = [(124, 98, 196), (170, 142, 234), (206, 188, 250)]      # ombre, base, clair : corps de la capuche, dos des oreilles
ROSE = [(208, 86, 146), (240, 128, 178), (255, 178, 208)]       # intérieur des oreilles, cordons
CREME = [(184, 176, 222), (222, 218, 238), (234, 234, 246)]     # bordure de nuage, pompons (blanc ×1,1 au plus : marge de compensation)
DOUBLURE = (132, 104, 200)                                       # dessous et intérieur de la capuche (doublure rose)
COEUR = [(196, 40, 104), (250, 92, 150), (255, 196, 220)]
E_COEUR = (236, 96, 156)


def lerp(a, b, k):
    return a + (b - a) * k


def col(c):
    return np.array(c, np.float32)


def mix(base, c, k):
    return lerp(base, col(c), np.clip(k, 0, 1)[..., None])


def rampe(pal, k):
    """3 couleurs (ombre, base, clair) ; k 0..1 (base à 0,55)."""
    k = np.clip(k, 0, 1)[..., None]
    a, b, c = (col(p) for p in pal)
    lo = lerp(a, b, np.clip(k / 0.55, 0, 1))
    return np.where(k < 0.55, lo, lerp(b, c, np.clip((k - 0.55) / 0.45, 0, 1)))


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
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def Rx(a):
    a = math.radians(a)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def Rz(a):
    a = math.radians(a)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def Ry(a):
    a = math.radians(a)
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


# ------------------------------------------------------------------ bouffées
def fib(n):
    ga = math.pi * (3 - math.sqrt(5))
    out = []
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - y * y)
        out.append(V(r * math.cos(ga * i), y, r * math.sin(ga * i)))
    return out


def hors(c, n, v):
    """Contrainte « n·P ≥ v » (côté opposé à la tête) → plan (normale sortante, distance au centre)."""
    nn = float(np.linalg.norm(n))
    n = np.asarray(n, float) / nn
    d = float(n @ c) - v / nn
    assert d > 0.05, ("centre hors de la contrainte", c, n, v)
    return (-n, d)


I3 = np.eye(3)
BOSSES = []


def bosse(nom, grp, c, R, extra=(), n=56, mat="lilas", M=I3, t=V(0, 0, 0), fixe=True, dens=1.0, p=None, tete=False):
    """Polyèdre circonscrit à un ellipsoïde (p = None) ou à un superellipsoïde |x/a|^p + |y/b|^p + |z/c|^p = 1 (boîte arrondie).
    tete : texels dans la zone de la tête (TETE) transparents (corps de la capuche, découpé autour de la tête)."""
    c = V(*c)
    R = V(*R)
    b = dict(nom=nom, grp=grp, c=c, R=R, extra=[hors(c, nn, v) for nn, v in extra], n=n, mat=mat, M=M, t=t, fixe=fixe, dens=dens, p=p, tete=tete)
    if p is None:
        pl = [(u, float(np.linalg.norm(R * u))) for u in fib(n)]
    else:
        dirs = np.array(fib(8000))
        pts = dirs * (np.sum(np.abs(dirs / R) ** p, axis=1) ** (-1 / p))[:, None]
        pl = [(u, float((pts @ u).max())) for u in fib(n)]
    pl = pl + b["extra"]
    b["N"] = np.array([p[0] for p in pl])
    b["D"] = np.array([p[1] for p in pl])
    b["planes"] = pl
    b["rmax"] = float(R.max())
    BOSSES.append(b)
    return b


EX, EY, EZ = V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)
Y_TOP = 32.62
# --- corps de la capuche (lilas) : une seule boîte arrondie dodue, découpée autour de la tête (ouverte devant et dessous)
XI, ZI = 4.62, 4.62
CORPS = bosse("capuche", "corps", (0, 29.0, 0.9), (6.3, 6.8, 6.0), [(EY, 24.2)], n=240, p=3.0, tete=True)


def dans_tete(P, marge=0.0):
    """Zone de la tête (et tout ce qui est devant le visage) : |x| < 4,62, y < 32,62, z < 4,62."""
    return (np.abs(P[..., 0]) < XI - marge) & (P[..., 1] < Y_TOP - marge) & (P[..., 2] < ZI - marge)

# --- bordure de nuage (crème) autour du visage : plans décalés vers l'extérieur (pas de faces coplanaires avec le corps)
TRIM = []
for i, x in enumerate((-4.0, -2.0, 0.0, 2.0, 4.0)):
    y = 33.3 + (0.12 if i % 2 else 0.0)
    TRIM.append(bosse(f"bord_h{i}", "bordure", (x, y, -4.9), (1.35, 1.25, 1.15), [(EY, Y_TOP + 0.1)], n=90, mat="creme", dens=1.5))
for s, tg in ((-1, "l"), (1, "r")):
    TRIM.append(bosse(f"bord_c{tg}", "bordure", (s * 4.95, 33.0, -4.9), (1.35, 1.35, 1.15), [(V(s, 1, 0), 4.62 + Y_TOP + 0.22)], n=90, mat="creme", dens=1.5))
    for j, y in enumerate((31.1, 29.2, 27.3, 25.6)):
        ex = [(s * EX, 4.70 + 0.04 * (j % 2))]
        if j == 3:
            ex.append((EY, 24.95))
        TRIM.append(bosse(f"bord_{tg}{j}", "bordure", (s * (5.15 + 0.08 * (j % 2)), y, -4.85), (1.2, 1.3, 1.1), ex, n=90, mat="creme", dens=1.5))

# --- oreilles : deux segments ; repos cuit dans la géométrie (groupes sans rotation)
EARS = {}
EL1_C, EL1_R = V(0, 2.9, 0), V(1.75, 3.3, 0.78)
JOINT = V(0, 4.5, 0)
EL2_C, EL2_R = V(0, 2.5, 0), V(1.95, 3.55, 0.72)
for s, tg in ((-1, "l"), (1, "r")):
    base = V(s * 2.6, 35.0, 0.9)
    M1 = Rz(-s * 14) @ Rx(8) @ Ry(s * 8)                    # écartée, un peu en arrière, intérieur tourné vers l'avant
    B = (Rz(-s * 78) @ Rx(-12)) if s < 0 else (Rx(-22) @ Rz(-s * 8))   # gauche pliée sur le côté, droite au bout qui tombe en avant
    j_w = base + M1 @ JOINT
    b1 = bosse(f"oreille_{tg}1", f"oreille_{tg}", EL1_C, EL1_R, n=52, mat="oreille", M=M1, t=base, fixe=False)
    b2 = bosse(f"oreille_{tg}2", f"oreille_{tg}2", EL2_C, EL2_R, n=56, mat="oreille", M=M1 @ B, t=j_w, fixe=False)
    EARS[tg] = dict(s=s, base=base, joint=j_w, b1=b1, b2=b2)

# --- pompons au bout des cordons (sous les joues)
POMP = {}
for s, tg in ((-1, "l"), (1, "r")):
    att = V(s * 5.05, 25.0, -4.5)
    pc = att + V(0, -3.45, 0)
    POMP[tg] = dict(att=att, pc=pc, b=bosse(f"pompon_{tg}", f"phys_pompon_{tg}_g100", pc, (0.95, 0.9, 0.95), n=72, mat="creme", dens=1.5, fixe=False))

FIXES = [b for b in BOSSES if b["fixe"]]


def dedans(P, b, marge):
    """P (..., 3) en coordonnées locales de b : dans le polyèdre, à plus de `marge` des faces ?"""
    q = P - b["c"]
    return (q @ b["N"].T - b["D"]).max(axis=-1) < -marge


def clip(poly, n, d):
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        da, db = a @ n - d, b @ n - d
        if da <= 0:
            out.append(a)
        if da * db < 0:
            out.append(a + (b - a) * (da / (da - db)))
    return out


def facettes(b):
    pl = b["planes"]
    out = []
    nextra = len(b["extra"])
    for i, (n, d) in enumerate(pl):
        a = unit(np.cross(n, V(0, 1, 0) if abs(n[1]) < 0.9 else V(1, 0, 0)))
        bb = np.cross(n, a)
        o = n * d
        poly = [o + 30 * (sa * a + sb * bb) for sa, sb in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        for j, (m, e) in enumerate(pl):
            if j != i and poly:
                poly = clip(poly, m, e)
        if len(poly) < 3:
            continue
        q = [poly[0]]
        for p in poly[1:]:
            if np.linalg.norm(p - q[-1]) > 1e-4:
                q.append(p)
        if np.linalg.norm(q[0] - q[-1]) < 1e-4:
            q.pop()
        if len(q) < 3:
            continue
        area = 0.5 * np.linalg.norm(sum(np.cross(q[k], q[(k + 1) % len(q)]) for k in range(len(q))))
        if area < 0.012:
            continue
        out.append((n, q, i >= len(pl) - nextra))
    return out


# ------------------------------------------------------------------ peinture
L_RB = unit(V(-0.4, 1.0, 0.6))
L_PEINT = unit(V(-0.3, 1.0, -0.6))


def eclairage(n):
    return 0.55 + 0.45 * np.abs(n @ L_RB)


def normale_lisse(Pl, b):
    if b["p"]:
        q = Pl - b["c"]
        q = np.sign(q) * np.abs(q / b["R"]) ** (b["p"] - 1) / b["R"]
    else:
        q = (Pl - b["c"]) / (b["R"] * b["R"])
    n = q / np.linalg.norm(q, axis=-1, keepdims=True)
    return n @ b["M"].T


def voisins(b):
    if "vois" not in b:
        cw = b["M"] @ b["c"] + b["t"]
        b["vois"] = [o for o in FIXES if o is not b and np.linalg.norm(o["c"] - cw) < o["rmax"] + b["rmax"] + 0.5]
    return b["vois"]


def ombre_contact(Pw, b):
    o = np.zeros(Pw.shape[:-1])
    for bb in voisins(b):
        if bb["p"]:
            q = np.sum(np.abs((Pw - bb["c"]) / bb["R"]) ** bb["p"], axis=-1) ** (1 / bb["p"])
        else:
            q = np.linalg.norm((Pw - bb["c"]) / bb["R"], axis=-1)
        o = np.maximum(o, np.clip((1.05 - q) / 0.08, 0, 1) ** 1.5 * (q > 0.985))
    return o


def couleur(Pw, Pl, b, nf, interieur):
    if interieur:
        c = np.zeros(Pw.shape, np.float32)
        c[...] = DOUBLURE
        return c * np.clip(0.75 + 0.2 * (Pw[..., 1] - 24) / 10, 0.7, 1.0)[..., None]
    n = normale_lisse(Pl, b)
    lum = np.clip(0.5 + 0.5 * (n @ L_PEINT), 0, 1)
    hgt = np.clip((Pw[..., 1] - 24.0) / 14.0, 0, 1)
    k = 0.62 * lum + 0.38 * hgt
    mat = b["mat"]
    if mat == "lilas":
        c = rampe(LILAS, k)
    elif mat == "creme":
        c = rampe(CREME, 0.42 + 0.58 * k)
    else:                                                        # oreille : dos lilas, intérieur rose bonbon
        c = rampe(LILAS, k)
        q = Pl - b["c"]
        seg2 = b["nom"].endswith("2")
        vc, rv = (3.4, 3.0) if not seg2 else (1.4, 3.7)
        e = np.hypot(q[..., 0] / (0.74 * b["R"][0]), (Pl[..., 1] - vc) / rv)
        front = (q[..., 2] / b["R"][2]) < -0.15
        pink = rampe(ROSE, np.clip(0.35 + 0.7 * e ** 2 + 0.2 * (lum - 0.5), 0, 1))
        k_in = np.clip((1.0 - e) / 0.08, 0, 1) * front
        c = c * (1 - k_in[..., None]) + pink * k_in[..., None]
        if not seg2:
            c = mix(c, LILAS[0], np.clip((0.9 - Pl[..., 1]) / 1.0, 0, 1) * 0.5)   # ombre de la base, dans le dôme
    rim = np.clip(1 - np.abs(n @ unit(V(0, 0.25, -1))) * 1.3, 0, 1) ** 2 * 0.25
    c = mix(c, (255, 255, 255), rim * (mat != "lilas") + rim * 0.4 * (mat == "lilas"))
    if b["fixe"]:
        c = mix(c, LILAS[0] if mat == "lilas" else CREME[0], ombre_contact(Pw, b) * (0.15 if mat == "lilas" else 0.0))
    comp = np.clip(eclairage(n) / eclairage(np.broadcast_to(nf, n.shape)), 0.7, 1.45)
    if mat == "creme":                      # marge sous 255 : sinon la compensation sature et les facettes se voient (dentelle)
        comp = np.clip(comp, 0.8, 1.1)
    return np.clip(c * comp[..., None], 0, 255)


def finir(c, inside, em, W, H_):
    rgb = np.array(Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), "RGB").resize((W, H_), Image.LANCZOS))
    al = (np.array(Image.fromarray((inside * 255).astype(np.uint8), "L").resize((W, H_), Image.LANCZOS)) > 110) * 255
    out = np.dstack([rgb, al]).astype(np.uint8)
    if (al > 0).any():
        out[al == 0, :3] = rgb[al > 0].mean(axis=0).astype(np.uint8)
    oe = np.zeros((H_, W, 4), np.uint8)
    if em is not None:
        er = np.array(Image.fromarray(np.clip(em, 0, 255).astype(np.uint8), "RGB").resize((W, H_), Image.LANCZOS))
        on = (al > 0) & (er.max(axis=2) > 20)
        oe[on, :3] = er[on]
        oe[on, 3] = 255
    return out, oe


def grille(W, H_, w, h):
    yy, xx = np.mgrid[0:H_ * SS, 0:W * SS]
    return (xx + 0.5) / (W * SS) * w - w / 2, h / 2 - (yy + 0.5) / (H_ * SS) * h


def sd_poly(pts2):
    edges = []
    for i in range(len(pts2)):
        a, b = pts2[i], pts2[(i + 1) % len(pts2)]
        t = unit(b - a)
        edges.append((a, np.array([t[1], -t[0]])))

    def f(X, Y):
        return np.max([(X - a[0]) * nn[0] + (Y - a[1]) * nn[1] for a, nn in edges], axis=0)
    return f


TUILES = {}         # nom -> dict(w, h, painter, fixe, dens)
PLATES = []         # (groupe, nom de tuile, centre de la plaque, X, Y, n)
DEBORD = 0.12                       # recouvrement des facettes voisines (densité ~12 texels/px : le seuil alpha ronge ~0,04 px)


def peintre_facette(sp):
    def f(W, H_):
        X, Y = grille(W, H_, sp["w"], sp["h"])
        inside = sp["sd"](X, Y) < DEBORD
        Pw = sp["o"] + X[..., None] * sp["X"] + Y[..., None] * sp["Y"]
        b = sp["b"]
        Pl = (Pw - b["t"]) @ b["M"]                              # M orthogonale : inverse = transposée
        for o in sp["coupe"]:
            inside &= ~dedans(Pw, o, 0.02)
        if b["tete"] and not sp["int"]:
            inside &= ~dans_tete(Pw)
        return finir(couleur(Pw, Pl, b, sp["n"], sp["int"]), inside, None, W, H_)
    return f


NFAC = {"omis": 0}
for b in BOSSES:
    coupe = [o for o in voisins(b)] if b["fixe"] else []
    for k, (nl, poly, interieur) in enumerate(facettes(b)):
        Pl = [p + b["c"] for p in poly]
        P = [b["M"] @ p + b["t"] for p in Pl]
        n = b["M"] @ nl
        if coupe and any(all(dedans(p[None], o, 0.05)[0] for p in P) for o in coupe):
            NFAC["omis"] += 1
            continue
        if b["tete"] and all(dans_tete(p, 0.02) for p in P):
            NFAC["omis"] += 1
            continue
        ctr = np.mean(P, axis=0)
        Xa = unit(P[1] - P[0])
        Ya = np.cross(n, Xa)
        p2 = [np.array([(p - ctr) @ Xa, (p - ctr) @ Ya]) for p in P]
        lo, hi = np.min(p2, axis=0) - DEBORD - 0.02, np.max(p2, axis=0) + DEBORD + 0.02
        if coupe:                                    # recadrer la plaque sur sa partie visible (union) : place dans l'atlas
            sd0 = sd_poly(p2)
            gx, gy = np.meshgrid(np.linspace(lo[0], hi[0], 28), np.linspace(lo[1], hi[1], 28))
            Pg = ctr + gx[..., None] * Xa + gy[..., None] * Ya
            vis = sd0(gx, gy) < DEBORD
            for o in coupe:
                vis &= ~dedans(Pg, o, 0.02)
            if b["tete"]:
                vis &= ~dans_tete(Pg)
            if not vis.any():
                NFAC["omis"] += 1
                continue
            cx, cy = (hi[0] - lo[0]) / 27, (hi[1] - lo[1]) / 27
            lo = np.maximum(lo, [gx[vis].min() - cx - 0.03, gy[vis].min() - cy - 0.03])
            hi = np.minimum(hi, [gx[vis].max() + cx + 0.03, gy[vis].max() + cy + 0.03])
        mid = (lo + hi) / 2
        o = ctr + Xa * mid[0] + Ya * mid[1]
        tn = f"{b['nom']}_{k}"
        sp = dict(w=hi[0] - lo[0], h=hi[1] - lo[1], sd=sd_poly([q - mid for q in p2]), o=o, X=Xa, Y=Ya, b=b, coupe=coupe, n=n, int=interieur)
        TUILES[tn] = dict(w=sp["w"], h=sp["h"], painter=peintre_facette(sp), fixe=None, dens=0.3 if interieur else b["dens"])
        PLATES.append((b["grp"], tn, o - n * 0.15, Xa, Ya, n))


# --- doublure : les quatre faces de la découpe (parois à x = ±4,62, dos à z = 4,62, plafond à y = 32,62) ferment la capuche
def doublure(nom, n_in, p0, ax1, ax2, bornes):
    p0 = V(*p0)
    poly = [p0 + 20 * (sa * ax1 + sb * ax2) for sa, sb in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    for nn, dd in zip(CORPS["N"], CORPS["D"]):
        poly = clip(poly, nn, dd + nn @ CORPS["c"])
    for nn, dd in bornes:
        poly = clip(poly, V(*nn), dd)
    n = V(*n_in)
    ctr = np.mean(poly, axis=0)
    Xa = unit(np.cross(n, ax2)) if abs(n @ ax1) < 0.5 else ax2
    Xa = unit(ax1 - (ax1 @ n) * n)
    Ya = np.cross(n, Xa)
    p2 = [np.array([(q - ctr) @ Xa, (q - ctr) @ Ya]) for q in poly]
    lo, hi = np.min(p2, axis=0) - 0.04, np.max(p2, axis=0) + 0.04
    mid = (lo + hi) / 2
    o = ctr + Xa * mid[0] + Ya * mid[1]
    sp = dict(w=hi[0] - lo[0], h=hi[1] - lo[1], sd=sd_poly([q - mid for q in p2]), o=o, X=Xa, Y=Ya, b=CORPS, coupe=[], n=n, int=True)
    TUILES[nom] = dict(w=sp["w"], h=sp["h"], painter=peintre_facette(sp), fixe=None, dens=0.35)
    PLATES.append(("corps", nom, o - n * 0.15, Xa, Ya, n))


for s_, tg in ((-1, "l"), (1, "r")):
    doublure(f"doublure_{tg}", (-s_, 0, 0), (s_ * XI, 29, 0), EY, EZ, [((0, 1, 0), Y_TOP), ((0, 0, 1), ZI)])
doublure("doublure_dos", (0, 0, -1), (0, 29, ZI), EX, EY, [((1, 0, 0), XI), ((-1, 0, 0), XI), ((0, 1, 0), Y_TOP)])
doublure("doublure_haut", (0, -1, 0), (0, Y_TOP, 0), EX, EZ, [((1, 0, 0), XI), ((-1, 0, 0), XI), ((0, 0, 1), ZI)])


# --- cœur de sucre au front, cordons, âmes
HW, HH = 2.2, 1.95
H_C = V(0, 34.25, -6.2)


def peint_coeur(face):
    def f(W, H_):
        X, Y = grille(W, H_, HW, HH)
        x, y = X / (HW * 0.5) * 1.12, (Y + 0.08) / (HH * 0.5) * 1.15 + 0.12
        F = (x * x + y * y - 1) ** 3 - x * x * y ** 3
        inside = F < 0
        dist = np.clip(-F * 3, 0, 1)
        c = rampe(COEUR, 0.3 + 0.5 * np.clip(Y / HH + 0.5, 0, 1) + 0.15 * dist)
        em = None
        if face == "f":
            hl = np.hypot((X + 0.38) / 0.22, (Y - 0.28) / 0.14) < 1
            c = mix(c, (255, 255, 255), hl * 1.0)
            c = mix(c, (255, 230, 240), (np.hypot((X - 0.42) / 0.08, (Y - 0.3) / 0.08) < 1) * 1.0)
            em = np.zeros(c.shape, np.float32)
            em[...] = E_COEUR
            em = em * (0.55 + 0.45 * np.clip(dist * 2, 0, 1))[..., None] * inside[..., None]
            em = np.where(hl[..., None], col((255, 236, 246)), em)
        else:
            c = c * 0.85
        return finir(c, inside, em, W, H_)
    return f


def uni(rgb, em=None):
    def f(W, H_):
        c = np.zeros((H_ * SS, W * SS, 3), np.float32)
        c[...] = rgb
        e = None
        if em is not None:
            e = np.zeros_like(c)
            e[...] = em
        return finir(c, np.ones(c.shape[:2], bool), e, W, H_)
    return f


def peint_cordon(W, H_):
    X, Y = grille(W, H_, 1.0, 1.0)
    c = rampe(ROSE, 0.45 + 0.25 * np.cos(X * 3.0) + 0.1 * np.sin(Y * 40))
    return finir(c, np.ones(X.shape, bool), None, W, H_)


TUILES["coeur_f"] = dict(w=HW, h=HH, painter=peint_coeur("f"), fixe=None, dens=1.6)
TUILES["coeur_b"] = dict(w=HW, h=HH, painter=peint_coeur("b"), fixe=None, dens=0.6)
TUILES["coeur_ame"] = dict(w=1, h=1, painter=uni(COEUR[1], (150, 52, 96)), fixe=(6, 6), dens=1)
TUILES["cordon"] = dict(w=1, h=1, painter=peint_cordon, fixe=(8, 24), dens=1)
for m, rgb in (("lilas", LILAS[1]), ("creme", CREME[1]), ("oreille", LILAS[1])):
    TUILES[f"ame_{m}"] = dict(w=1, h=1, painter=uni(rgb), fixe=(6, 6), dens=1)

UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def atlas():
    def pack(dens):
        items = []
        for n, t in TUILES.items():
            w, h = t["fixe"] if t["fixe"] else (max(2, int(math.ceil(t["w"] * dens * t["dens"]))), max(2, int(math.ceil(t["h"] * dens * t["dens"]))))
            items.append((n, w, h))
        items.sort(key=lambda it: (-it[2], -it[1]))
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
    for n, t in TUILES.items():
        u0, v0, u1, v1 = UV[n]
        tex[v0:v1, u0:u1], tex_e[v0:v1, u0:u1] = t["painter"](u1 - u0, v1 - v0)
    assert tex[TEX - 3, TEX - 3, 3] == 0
    assert not ((tex[..., 3] > 0) & (tex[..., 3] < 255)).any(), "semi-transparence hors trans_"
    b64 = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        bb = io.BytesIO()
        im.save(bb, "PNG", optimize=True)
        b64.append("data:image/png;base64," + base64.b64encode(bb.getvalue()).decode())
    return dens, b64


# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def rot_matrix(rx, ry, rz):
    return Rz(rz) @ Ry(ry) @ Rx(rx)


def euler(R):
    sy = -R[2, 0]
    if abs(sy) > 0.99999:
        ry = math.copysign(math.pi / 2, sy)
        ang = (math.degrees(math.atan2(R[0, 1], R[0, 2])) if sy > 0 else math.degrees(math.atan2(-R[0, 1], -R[0, 2]))), math.degrees(ry), 0.0
    else:
        ang = math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(math.asin(sy)), math.degrees(math.atan2(R[1, 0], R[0, 0]))
    assert np.allclose(rot_matrix(*ang), R, atol=1e-4), "euler"
    return ang


def group(name, origin, parent=None, nm=None):
    assert name not in groups and len(nm or name) <= 64
    groups[name] = {"origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "name": nm or name}
    return name


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 3) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])
    return e


def plate(g, name, c, X, Y, out, tile, th=0.3):
    X, Y = unit(X), unit(Y)
    w, h = TUILES[tile]["w"], TUILES[tile]["h"]
    u0, v0, u1, v1 = UV[tile]
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    south, north = [u0, v0, u1, v1], [u1, v0, u0, v1]
    if R_[:, 2] @ out > 0:
        north = CLEAR
    else:
        south = CLEAR
    c = np.asarray(c, float)
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
         {"south": south, "north": north, "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR})


def ame(b):
    """Âme pleine : boîte (repère local de la bouffée) la plus grande à plus de 0,36 px des faces."""
    lo, hi = 0.05, 0.75
    c, R = b["c"], b["R"]
    for _ in range(30):
        s = (lo + hi) / 2
        pts = np.array([c + np.array([sx, sy, sz]) * s * R for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
        if dedans(pts, b, 0.36).all():
            lo = s
        else:
            hi = s
    h = lo * R * 0.92
    return c, h


def bone_node(name):
    g = groups[name]
    return {"name": g["name"], "origin": g["origin"], "uuid": g["uuid"], "rotation": [0, 0, 0],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


group("head", V(0, 24, 0))
group("capuche", V(0, Y_TOP, 0.5), "head")
group("corps", V(0, Y_TOP, 0.5), "capuche")
group("bordure", V(0, 30.5, -4.9), "capuche")
group("coeur", H_C, "capuche")
for tg, E in EARS.items():
    group(f"oreille_{tg}", E["base"], "capuche")
    group(f"oreille_{tg}2", E["joint"], f"oreille_{tg}")
for tg, P in POMP.items():
    group(f"phys_pompon_{tg}_g100", P["att"], "capuche")

DENS, (tex_b64, tex_e_b64) = atlas()

AMES_CORPS = [((-XI - 0.3, Y_TOP + 0.4, -3.2), (XI + 0.3, 35.2, ZI + 0.3)),            # dessus
              ((XI + 0.38, 24.7, -3.2), (6.0, Y_TOP + 0.3, ZI + 0.3)), ((-6.0, 24.7, -3.2), (-XI - 0.38, Y_TOP + 0.3, ZI + 0.3)),
              ((-XI - 0.3, 24.6, ZI + 0.38), (XI + 0.3, Y_TOP + 0.3, 6.6))]                  # flancs, dos


def reduire(lo, hi, marge=0.36):
    lo, hi = V(*lo), V(*hi)
    m = (lo + hi) / 2
    for _ in range(40):
        pts = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        if dedans(pts, CORPS, marge).all():
            return lo, hi
        lo, hi = m + (lo - m) * 0.96, m + (hi - m) * 0.96
    raise AssertionError("âme")


ta = UV["ame_lilas"]
for k, (lo, hi) in enumerate(AMES_CORPS):
    lo, hi = reduire(lo, hi)
    assert not dans_tete(np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]), -0.05).any()
    cube("corps", f"ame_capuche{k}", lo, hi, (lo + hi) / 2, (0, 0, 0), {f: list(ta) for f in ("north", "south", "east", "west", "up", "down")})
for b in BOSSES:
    if b is CORPS:
        continue
    c, h = ame(b)
    if h.min() < 0.06:
        continue
    t = UV[f"ame_{b['mat']}"]
    uvf = {k: list(t) for k in ("north", "south", "east", "west", "up", "down")}
    cw = b["M"] @ c + b["t"]
    cube(b["grp"], f"ame_{b['nom']}", cw - h, cw + h, cw, euler(b["M"]) if b["M"] is not I3 else (0, 0, 0), uvf)
for g, tn, o, Xa, Ya, n in PLATES:
    plate(g, tn, o, Xa, Ya, n, tn)

# cœur : face avant, dos, âme
plate("coeur", "coeur_f", H_C, EX, EY, -EZ, "coeur_f")
plate("coeur", "coeur_b", H_C + V(0, 0, 0.5), EX, EY, EZ, "coeur_b")
ta = UV["coeur_ame"]
cube("coeur", "coeur_ame", H_C + V(-0.42, -0.35, 0.12), H_C + V(0.42, 0.35, 0.4), H_C, (0, 0, 0), {k: list(ta) for k in ("north", "south", "east", "west", "up", "down")})
# cordons : de la bordure jusqu'au pompon
tc = UV["cordon"]
for tg, P in POMP.items():
    a, pc = P["att"], P["pc"]
    cube(f"phys_pompon_{tg}_g100", f"cordon_{tg}", V(a[0] - 0.19, pc[1] + 0.5, a[2] - 0.19), V(a[0] + 0.19, a[1] + 0.2, a[2] + 0.19), a, (0, 0, 0),
         {k: list(tc) for k in ("north", "south", "east", "west", "up", "down")})

outliner = [bone_node("head")]


# ------------------------------------------------------------------ animations
# Intention sur un côté s (-1 gauche, +1 droite) : back > 0 = le haut part vers l'arrière ; out > 0 = le haut s'écarte vers
# l'extérieur (pour le bout plié de gauche : il tombe davantage ; out < 0 le relève) ; sweep > 0 = l'extérieur part en arrière.
# MIROIR D'AXES (essentiel.md, Axes) : +X = le haut bascule vers l'arrière ; +Y = le côté droit avance ; +Z = le côté droit
# monte, donc le haut d'une pièce verticale part vers -X. Seul endroit à toucher si la convention change.
SX, SY, SZ = +1, -1, -1


def mirror(s, back, out, sweep=0.0):
    return SX * back, s * SY * sweep, s * SZ * out


def fmt(v):
    return v if isinstance(v, str) else str(round(v + 0.0, 3))


def kf(t, ch, x, y, z):
    return {"channel": ch, "data_points": [{"x": fmt(x), "y": fmt(y), "z": fmt(z)}], "time": round(t, 4), "interpolation": "linear"}


def anim(name, L, tracks, n_kf=None, loop="loop", son=None):
    """tracks : (groupe, canal) -> f(t) -> (x, y, z) ; échantillonné, dernière clé = première pour une boucle."""
    n = n_kf or max(8, int(round(L * 10)))
    times = [i * L / n for i in range(n + 1)]
    A = {}
    for (g, ch), f in tracks.items():
        A.setdefault(groups[g]["uuid"], {"name": groups[g]["name"], "type": "bone", "keyframes": []})["keyframes"] += [kf(t, ch, *f(t)) for t in times]
    if son:
        A["effects"] = {"name": "Effects", "type": "effect", "keyframes": [{"channel": "sound", "data_points": [{"effect": son[0], "file": ""}], "time": son[1]}]}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": L, "snapping": 24, "selected": name == "idle", "animators": A}


def etat(name, L, back, out, tip, bob=(0.0, 1), flut=(0.0, 0), extra=None, n_kf=None):
    """back, out : pose des racines ; tip[tag] = (back, out) du bout ; bob : rebond (cycles entiers, le bout suit avec retard) ;
    flut : frémissement au vent. Le bout plié de gauche rebondit de haut en bas (out), le bout droit d'avant en arrière (back).
    extra(t, tag) -> (d_back, d_out, d_tip_back, d_tip_out, d_sweep)."""
    tr = {}
    ba, bc = bob
    fa, fc = flut
    for tg, E in EARS.items():
        s = E["s"]
        ph = 0.0 if s < 0 else 0.6

        def root_f(t, s=s, ph=ph, tg=tg):
            w = TAU * bc * t / L + ph
            fl = fa * math.sin(TAU * fc * t / L + 2 * ph)
            ex = extra(t, tg) if extra else (0, 0, 0, 0, 0)
            return mirror(s, back + ba * math.sin(w) + fl + ex[0], out + 0.35 * ba * math.sin(w + 0.7) + ex[1], ex[4])

        def tip_f(t, s=s, ph=ph, tg=tg):
            w = TAU * bc * t / L + ph - 0.9
            fl = fa * 1.6 * math.sin(TAU * fc * t / L + 2 * ph - 1.0)
            ex = extra(t, tg) if extra else (0, 0, 0, 0, 0)
            tb, to = tip[tg]
            if s < 0:
                return mirror(s, tb + 0.4 * ba * math.sin(w) + ex[2], to + 2.2 * ba * math.sin(w) + fl + ex[3])
            return mirror(s, tb + 1.3 * ba * math.sin(w) + 0.6 * fl + ex[2], to + 0.5 * ba * math.sin(w + 0.5) + ex[3])
        tr[(f"oreille_{tg}", "rotation")] = root_f
        tr[(f"oreille_{tg}2", "rotation")] = tip_f
    return anim(name, L, tr, n_kf=n_kf)


def idle_extra(t, tg):
    """Frémissement de l'oreille droite vers 2,4 s ; écoute vers 4,2 s (les deux se dressent et pivotent vers la droite) ;
    le bout plié de la gauche se relève et retombe vers 6 s."""
    ec = bump(t, 3.9, 4.2, 4.9, 5.4)
    if tg == "r":
        k = bump(t, 2.3, 2.45, 2.75, 3.2)
        sh = math.sin(TAU * 7 * t) * bump(t, 2.35, 2.5, 2.8, 3.15)
        return (8 * k - 7 * ec, 3 * sh - 4 * ec, 6 * k - 4 * ec, 5 * sh, -10 * ec)
    k = bump(t, 5.8, 6.0, 6.25, 6.9)
    sh = math.sin(TAU * 6 * t) * bump(t, 6.2, 6.3, 6.5, 6.9)
    return (2 * k - 6 * ec, -4 * ec, 0, -26 * k + 8 * sh - 6 * ec, 10 * ec)


Z2 = {"l": (0, 0), "r": (0, 0)}
STATES = [
    etat("idle", 8.0, 0, 0, Z2, bob=(1.3, 2), extra=idle_extra, n_kf=96),
    etat("walk", 1.6, 6, 2, {"l": (0, 6), "r": (5, 0)}, bob=(4.0, 2), n_kf=24),
    etat("run", 1.0, 34, 4, {"l": (4, -30), "r": (12, 0)}, bob=(5.0, 2), flut=(2.0, 4), n_kf=20),
    etat("sneak", 3.0, 6, 30, {"l": (0, 16), "r": (-4, 22)}, bob=(1.2, 1), n_kf=24),
    etat("fly", 2.4, 42, 6, {"l": (4, -45), "r": (12, 0)}, bob=(2.0, 1), flut=(3.0, 8), n_kf=48),
    etat("glide", 3.6, 52, 8, {"l": (4, -50), "r": (10, 0)}, bob=(1.5, 1), flut=(3.0, 12), n_kf=72),
    etat("fall", 1.2, -10, -8, {"l": (0, -42), "r": (-16, -6)}, bob=(2.0, 1), flut=(4.0, 4), n_kf=24),
    etat("swim", 3.6, 58, 6, {"l": (4, -48), "r": (10, 0)}, bob=(1.8, 2), n_kf=48),
    etat("sleep", 4.0, 18, 30, {"l": (0, 14), "r": (-6, 22)}, bob=(0.8, 1), n_kf=24),
]

# --- overlay_oreilles : vie basse (sous 60 %, en douceur), pluie, frémissements au hasard (Molang, jugé en jeu)
VIE = "math.clamp((q.max_health*0.6-q.health)/math.max(q.max_health*0.4,0.1),0,1)"


def hasard(P, c):
    x = f"(q.life_time/{P:g}+q.instance_seed*13+{c:g})"
    k = f"math.mod(math.abs(math.sin(math.floor({x})*127.1))*437.585,1)"
    f = f"math.mod({x},1)"
    return f"({k}<0.55)*({f}<0.1)*math.sin({f}*10800)"


def overlay():
    A = {}
    for tg, E in EARS.items():
        s = E["s"]
        fr = hasard(3.4 if s > 0 else 4.1, 0.3 if s > 0 else 0.71)
        tremble = f"v.vie*1.5*math.sin(q.life_time*{700 + 90 * (s > 0)})"
        rx = f"v.vie={VIE};22*v.vie+12*q.is_in_rain+5*{fr}+{tremble}"
        rz = f"{-s}*(30*{VIE}+8*q.is_in_rain)"
        ry = f"{-s}*6*{fr}"
        for e in (rx, rz, ry):
            assert len(e) <= 512, len(e)
        tx = f"18*{VIE}+6*q.is_in_rain"
        tz = f"{-s}*24*{VIE}+{-s}*9*{hasard(3.4 if s > 0 else 4.1, 0.3 if s > 0 else 0.71)}"
        for g, (x, y, z) in ((f"oreille_{tg}", (rx, ry, rz)), (f"oreille_{tg}2", (tx, "0", tz))):
            A[groups[g]["uuid"]] = {"name": g, "type": "bone", "keyframes": [kf(0, "rotation", x, y, z), kf(1.0, "rotation", x, y, z)]}
    return {"uuid": nuid(), "name": "overlay_oreilles", "loop": "loop", "override": False, "length": 1.0, "snapping": 24, "selected": False, "animators": A}


def courbe(pts):
    def f(t):
        if t <= pts[0][0]:
            return pts[0][1]
        for (t0, a), (t1, b) in zip(pts, pts[1:]):
            if t <= t1:
                return a + (b - a) * sm(t, t0, t1)
        return pts[-1][1]
    return f


def plop(t0, t1, pic=1.22):
    d = t1 - t0
    return courbe([(t0, 0.0), (t0 + 0.55 * d, pic), (t0 + 0.8 * d, 0.93), (t1, 1.0)])


def amorti(t, t0, f=2.2, k=5.0):
    u = max(0.0, t - t0)
    return math.sin(TAU * f * u) * math.exp(-k * u) * (t > t0)


def sc3(f):
    return lambda t: (max(0.0, f(t)),) * 3


def ev_oreilles(L, f_root, f_tip):
    tr = {}
    for tg, E in EARS.items():
        s = E["s"]
        tr[(f"oreille_{tg}", "rotation")] = (lambda s: lambda t: mirror(s, *f_root(t, s)))(s)
        tr[(f"oreille_{tg}2", "rotation")] = (lambda s: lambda t: mirror(s, *f_tip(t, s)))(s)
    return tr


# event_equip (1,0 s) : la capuche gonfle depuis le dessus de la tête, la bordure fait « plop », les oreilles poussent avec un
# dépassement et le bout plié retombe en rebondissant, puis le cœur ; un son (« plop » doux).
EQ = 1.0
tr = {("corps", "scale"): sc3(plop(0.0, 0.42, 1.12)), ("bordure", "scale"): sc3(plop(0.16, 0.52, 1.25)),
      ("coeur", "scale"): sc3(plop(0.68, 0.94, 1.35))}
for tg, E in EARS.items():
    d = 0.06 * (E["s"] > 0)
    tr[(f"oreille_{tg}", "scale")] = sc3(plop(0.28 + d, 0.7 + d, 1.2))
for tg in POMP:
    tr[(f"phys_pompon_{tg}_g100", "scale")] = sc3(plop(0.45, 0.8, 1.2))
tr.update(ev_oreilles(EQ, lambda t, s: (0, 0, 0), lambda t, s: (0, (-22 if s < 0 else 10) * amorti(t, 0.62) * (1 - sm(t, 0.93, 1.0)), 0)))
equip = anim("event_equip", EQ, tr, n_kf=40, loop="once", son=("entity.chicken.egg", 0.3))

# event_unequip (1,0 s) : petite inspiration, oreilles qui rentrent, bordure qui fond, puis la capuche ; fin à l'échelle 0.
UQ = 1.0
fin = lambda f: (lambda t: 0.0 if t >= UQ - 1e-6 else f(t))
tr = {("coeur", "scale"): sc3(fin(courbe([(0.0, 1.0), (0.08, 1.1), (0.3, 0.0)]))),
      ("bordure", "scale"): sc3(fin(courbe([(0.0, 1.0), (0.35, 1.08), (0.7, 0.0)]))),
      ("corps", "scale"): sc3(fin(courbe([(0.0, 1.0), (0.45, 1.08), (0.95, 0.0)])))}
for tg in EARS:
    tr[(f"oreille_{tg}", "scale")] = sc3(fin(courbe([(0.0, 1.0), (0.15, 1.1), (0.55, 0.0)])))
for tg in POMP:
    tr[(f"phys_pompon_{tg}_g100", "scale")] = sc3(fin(courbe([(0.0, 1.0), (0.5, 0.0)])))
unequip = anim("event_unequip", UQ, tr, n_kf=40, loop="once")

# event_jump (0,5 s) : en montant, les oreilles restent en retard (elles s'abaissent sur les côtés) puis se redressent.
JL = 0.5
jump = anim("event_jump", JL, ev_oreilles(JL, lambda t, s: (4 * bump(t, 0, 0.1, 0.22, 0.48), 12 * bump(t, 0, 0.1, 0.22, 0.48), 0),
                                         lambda t, s: (6 * bump(t, 0.03, 0.14, 0.26, 0.5), 18 * bump(t, 0.03, 0.14, 0.26, 0.5), 0)), n_kf=15, loop="once")
# event_land (0,8 s) : à l'arrivée, elles continuent vers le bas (« flop »), rebondissent deux fois et se calment.
LL = 0.8
lk = lambda t: (sm(t, 0.0, 0.07) * math.exp(-4.2 * t) * math.cos(TAU * 2.4 * t)) * (1 - sm(t, 0.7, 0.8))
land = anim("event_land", LL, ev_oreilles(LL, lambda t, s: (6 * lk(t), 18 * lk(t), 0), lambda t, s: (8 * lk(max(0.0, t - 0.05)), 26 * lk(max(0.0, t - 0.05)), 0)),
            n_kf=24, loop="once")

ANIMS = STATES + [overlay(), equip, unequip, jump, land]
assert len(ANIMS) <= 32

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
limiter_sons(model)
retirer_reactions(model)
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


# contrôle : aucune âme ni plaque opaque de la capuche dans la zone de la tête (|x|,|z| < 4,62, y < 32,62) au repos
viol = 0
for b in FIXES:
    if b is CORPS:
        continue
    c, h = ame(b)
    pts = np.array([c + np.array([sx, sy, sz]) * h for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    viol += int(((np.abs(pts[:, 0]) < 4.6) & (np.abs(pts[:, 2]) < 4.6) & (pts[:, 1] < 32.6) & (pts[:, 1] > 23.9)).any())
print(len(elements), "cubes ;", len(groups), "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      f"densité {DENS:.2f} texels/px ; facettes omises {NFAC['omis']} ; âmes dans la tête : {viol}")
