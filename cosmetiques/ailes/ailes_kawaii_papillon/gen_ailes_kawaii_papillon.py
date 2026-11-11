"""Ailes papillon bonbon (refonte du 2026-11-08) — ensemble Kawaii, thème Mignon. Design original.

Retour de l'utilisateur (2026-11-08) : « les truc kawaii sont tous bof pas tres beau ou nul ». La v2 (vitrail de sucre pastel en
ovales, bourrelet crème perlé, lavande délavée) se lisait blanche et molle en jeu. Cette version :
- **vraie forme d'aile de papillon** (fiche .claude/references/animaux/insectes.md, section 7) : antérieure triangulaire (côte
  longue, apex arrondi, bord externe festonné, angle anal net), postérieure en éventail festonné avec une petite queue en goutte ;
  l'antérieure recouvre le bord de la postérieure, comme sur le vivant ;
- **nervation réelle simplifiée** : cellule discale fermée, nervures qui en rayonnent jusqu'au bord, côte épaissie ; nervures en vrai
  volume (baguettes losanges qui dépassent de la membrane des deux côtés) sur un tracé peint identique ;
- **motifs nets et colorés** (couleurs franches, pas de pastel en trans_ : il se lit blanc) : dégradé fraise → bonbon → lilas →
  ciel vers l'apex (reflet irisé peint, bande de brillance), bordure prune festonnée semée de pois blancs, frange blanche coupée
  aux nervures (écailles du bord), cœur blanc dans la cellule de l'antérieure, ocelle en cœur (prune, lilas, blanc) sur la
  postérieure, deux pois apicaux, un seul reflet « fenêtre » ; ombre de recouvrement sous l'antérieure ;
- **translucidité contrôlée** : membrane trans_ à alpha 205–235 (plus dense à la racine), bordure, nervures, frange, pois et cœurs
  opaques ;
- **vol de papillon** : en vol, trois battements « claque et lance » (les ailes se touchent presque derrière le dos puis se rouvrent,
  le lancer plus long que la claque) puis un plané ailes ouvertes en léger V ; au repos, ailes dressées en V, frisson de nervosité
  et bain de soleil (ouverture lente) ;
- **apparition = éclosion** (event_equip, 3,4 s) : une chrysalide menthe à points dorés apparaît dans le dos, frétille, se fend en
  deux ; les ailes en sortent petites et froissées, baissées, se gonflent par à-coups (pompage), se relèvent, puis premier « lancer » ;
  la chrysalide vide se referme sur elle-même et disparaît. Retrait : les ailes se serrent, frissonnent, rapetissent.

Fonctions avancées : trans_ (membranes), calque _e (cœurs, pois : sources nettes), particle_ + emit_ (paillettes qui montent),
event_equip (chrysalide cachée dans les états par échelle 0,1 + recul dans le torse, recette d'ailes_steampunk), event_unequip,
un son (entity.turtle.egg_hatch à l'éclosion, tools/sons.py), Molang en glide (battement à la fusée, constantes validées).
À juger en jeu (/cosmetique apercu) : tri des faces trans_ avec et sans shader, éclosion par-dessus l'état, paillettes, _e la nuit.
"""
import base64, io, json, math, os, sys, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

AVEC_E = True
TEX = 512
V0, DV = 26, 5      # battement à la fusée (glide) : constantes validées en jeu
TAU = 2 * math.pi
NOM = "ailes_kawaii_papillon"
R = 28              # texels de peinture par px modèle (sur-échantillonnage avant réduction)


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


def catmull(ctrl, n=40):
    """Spline fermée de Catmull-Rom ; renvoie aussi, pour chaque point, l'indice (fractionnaire) du point de contrôle."""
    out, par, m = [], [], len(ctrl)
    for i in range(m):
        p0, p1, p2, p3 = ctrl[i - 1], ctrl[i], ctrl[(i + 1) % m], ctrl[(i + 2) % m]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
            par.append(i + t)
    return out, par


def resample(pts, step, closed=False):
    pts = list(pts) + ([pts[0]] if closed else [])
    ls = [0.0]
    for a, b in zip(pts, pts[1:]):
        ls.append(ls[-1] + math.dist(a, b))
    n = max(2, int(round(ls[-1] / step)))
    if closed:
        n += n % 2
    out, j = [], 0
    for i in range(n if closed else n + 1):
        d = ls[-1] * i / n
        while j < len(ls) - 2 and ls[j + 1] < d:
            j += 1
        k = (d - ls[j]) / max(1e-9, ls[j + 1] - ls[j])
        out.append((lerp(pts[j][0], pts[j + 1][0], k), lerp(pts[j][1], pts[j + 1][1], k)))
    return out


def curve(p0, p1, bow, n):
    """Nervure légèrement courbe (bow : flèche en fraction de la longueur, signe = côté)."""
    L = math.dist(p0, p1)
    d = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
    nrm = (-d[1], d[0])
    return [(lerp(p0[0], p1[0], i / n) + nrm[0] * bow * L * math.sin(math.pi * i / n),
             lerp(p0[1], p1[1], i / n) + nrm[1] * bow * L * math.sin(math.pi * i / n)) for i in range(n + 1)]


# ------------------------------------------------------------------ formes (aile droite, x > 0, px du modèle, y vers le haut)
ZF, ZH = 4.0, 3.0                 # plans : l'antérieure (côté dos) recouvre la postérieure ; 1 px d'écart
PIV_F, PIV_H = (1.6, 22.8), (2.2, 21.8)   # pivots décalés en x ET en z (seul un décalage en z s'annule ailes fermées)

# Contour en points de contrôle, sens horaire (racine → côte → apex → bord externe → bord interne), avec la largeur de la bordure
# prune à chaque point (px). Le bord d'attaque reste sous y = 23,4 jusqu'à x ≈ 6,5 : rien près de la tête.
FORE_CTRL = [((1.8, 22.5), .22), ((4.4, 22.45), .22), ((6.5, 22.8), .25), ((8.6, 26.0), .3), ((11.6, 30.6), .34),
             ((15.2, 35.2), .4), ((19.2, 38.9), .55), ((22.8, 41.0), .85), ((25.6, 41.1), 1.15), ((27.6, 39.6), 1.3),
             ((28.6, 36.8), 1.3), ((28.7, 33.4), 1.3), ((28.0, 30.0), 1.25), ((26.8, 27.0), 1.15), ((24.8, 24.6), .9),
             ((21.0, 23.0), .4), ((15.0, 21.9), .26), ((9.0, 21.3), .22), ((4.6, 21.4), .22)]
HIND_CTRL = [((2.2, 21.6), .2), ((5.5, 22.0), .2), ((10.0, 21.8), .25), ((14.2, 20.6), .5), ((17.2, 18.0), 1.0),
             ((18.4, 14.6), 1.2), ((17.8, 11.4), 1.2), ((16.0, 8.8), 1.15), ((13.6, 7.0), 1.0), ((12.2, 6.4), .8),
             ((11.6, 4.8), .55), ((10.6, 3.9), .55), ((9.4, 4.2), .55), ((9.0, 5.4), .55), ((9.3, 6.8), .5),
             ((7.2, 8.8), .38), ((4.8, 11.8), .28), ((3.2, 15.2), .22), ((2.4, 18.6), .2)]

# Cellule discale (fermée) et nervures : (départ sur la cellule, cible sur le bord, flèche, festonné entre ce bord et le suivant)
FORE_CELL = [(3.0, 22.3), (7.5, 24.3), (12.6, 28.9), (15.6, 29.0), (16.4, 26.2), (13.0, 23.4), (6.5, 21.9)]
FORE_VEINS = [((12.6, 28.9), (18.4, 37.9), .03, False),   # R2
              ((14.4, 29.0), (23.0, 40.9), .02, False),   # R3
              ((15.6, 29.0), (26.4, 40.6), -.03, True),   # R4 → apex (début du feston)
              ((16.1, 27.8), (28.3, 37.6), -.03, True),   # M1
              ((16.4, 26.4), (28.7, 33.4), -.02, True),   # M2
              ((15.6, 25.0), (28.1, 30.2), .02, True),    # M3
              ((13.8, 24.0), (26.6, 26.9), .03, True),    # Cu1
              ((10.4, 22.9), (24.4, 24.4), .03, True)]    # Cu2 → angle anal (fin du feston)
HIND_CELL = [(3.0, 20.8), (7.6, 20.7), (11.4, 18.6), (12.0, 15.6), (9.6, 13.6), (5.8, 15.2), (3.4, 18.0)]
HIND_VEINS = [((6.8, 20.75), (14.2, 20.6), .02, False),   # Sc + R1 (sous l'antérieure)
              ((10.4, 19.4), (17.3, 18.2), .0, True),     # Rs (début du feston)
              ((11.8, 17.6), (18.4, 14.4), -.02, True),   # M1
              ((12.0, 15.8), (17.4, 10.8), -.03, True),   # M2
              ((11.2, 14.4), (15.5, 8.3), -.02, True),    # M3
              ((10.0, 13.9), (12.6, 6.6), .0, False),     # Cu1 (fin du feston)
              ((8.6, 14.1), (10.1, 4.4), .01, False),     # Cu2 → bout de la queue
              ((5.6, 15.0), (6.4, 9.9), .02, False)]      # A → bord interne

WINGS = {"fore": dict(ctrl=FORE_CTRL, cell=FORE_CELL, veins=FORE_VEINS, z=ZF, piv=PIV_F, root=(1.8, 22.3), depth=0.32),
         "hind": dict(ctrl=HIND_CTRL, cell=HIND_CELL, veins=HIND_VEINS, z=ZH, piv=PIV_H, root=(2.4, 21.2), depth=0.42)}


def prepare(w):
    """Contour festonné entre les bouts de nervures, bout des nervures, largeur de bordure et frange le long du contour."""
    ctrl = [p for p, _ in w["ctrl"]]
    bw_c = [b for _, b in w["ctrl"]]
    base, par = catmull(ctrl, 40)
    N = len(base)
    bw = np.array([lerp(bw_c[int(p) % len(bw_c)], bw_c[(int(p) + 1) % len(bw_c)], p - int(p)) for p in par])
    C = np.mean(np.array(ctrl), axis=0)
    B = np.array(base)
    ends, w["vpaths"], scal = [], [], []
    for (p0, tgt, bow, sc) in w["veins"]:
        i = int(np.argmin(np.hypot(B[:, 0] - tgt[0], B[:, 1] - tgt[1])))
        ends.append(i)
        scal.append(sc)
    # feston : lobes ronds vers l'extérieur entre deux bouts de nervures consécutifs de la zone festonnée (encoche à la nervure)
    out = B.copy()
    fringe = np.zeros(N, bool)
    zone = [ends[k] for k in range(len(ends)) if scal[k]]
    for k in range(len(ends)):
        if scal[k] and k + 1 < len(ends):
            zone.append(ends[k + 1])
    zone = sorted(set(zone))
    w["lobes"] = []
    for ia, ib in zip(zone, zone[1:]):
        for j in range(ia, ib + 1):
            u = (j - ia) / (ib - ia)
            v = B[j] - C
            v = v / np.linalg.norm(v)
            out[j] = B[j] + v * w["depth"] * math.sin(math.pi * u) ** 0.75
            fringe[j] = True
        w["lobes"].append((ia, ib))
    w["out"] = [tuple(p) for p in out]
    w["bw"], w["fringe"], w["C"] = bw, fringe, tuple(C)
    w["ends_idx"] = ends
    # bout des nervures : 0,12 px à l'intérieur de l'encoche
    for k, (p0, tgt, bow, sc) in enumerate(w["veins"]):
        e = out[ends[k]]
        v = np.array(C) - e
        e = e + v / np.linalg.norm(v) * 0.12
        w["vpaths"].append((p0, (float(e[0]), float(e[1])), 0.0))   # nervures droites : tracé peint = baguette
    w["cloop"], _ = catmull(w["cell"], 16)


for w in WINGS.values():
    prepare(w)

# ------------------------------------------------------------------ palette (fiche kawaii : couleurs franches dans trans_)
ROSE = (255, 88, 156)        # fraise vive à la racine
BONBON = (255, 140, 196)
LILAS = (192, 136, 255)
CIEL = (132, 192, 255)       # reflet irisé vers l'apex
PRUNE = (156, 44, 128)       # bordure (jamais de noir)
VEINE = (170, 54, 140)
BLANC = (255, 252, 250)
FRANGE = (255, 238, 246)
SHEEN = (236, 226, 255)


def ramp(t, stops):
    t = np.clip(t, 0, 1)
    out = np.zeros(t.shape + (3,), np.float32)
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        sel = (t >= a) & (t <= b)
        k = ((t - a) / (b - a))[..., None]
        out[sel] = (np.array(ca, np.float32) + (np.array(cb, np.float32) - np.array(ca, np.float32)) * k)[sel]
    return out


def heart(X, Y, cx, cy, r):
    u = (X - cx) / r
    v = (Y - cy) / r + 0.1
    return (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0


def disc(X, Y, cx, cy, r):
    return (X - cx) ** 2 + (Y - cy) ** 2 <= r * r


def on_path(path, t):
    """Point à la fraction t d'une nervure (droite entre ses bouts, la flèche est faible)."""
    (p0, p1, bow) = path
    pts = curve(p0, p1, bow, 12)
    return pts[int(round(t * 12))]


def paint(w, name):
    out = w["out"]
    xs, ys = [p[0] for p in out], [p[1] for p in out]
    x0, x1 = math.floor(min(xs) * 4 - 1) / 4, math.ceil(max(xs) * 4 + 1) / 4
    y0, y1 = math.floor(min(ys) * 4 - 1) / 4, math.ceil(max(ys) * 4 + 1) / 4
    GW, GH = int(round((x1 - x0) * R)), int(round((y1 - y0) * R))
    w["box"] = (x0, y0, x1, y1)
    gy, gx = np.mgrid[0:GH, 0:GW]
    X, Y = (x0 + (gx + 0.5) / R).astype(np.float32), (y1 - (gy + 0.5) / R).astype(np.float32)
    px = lambda p: ((p[0] - x0) * R, (y1 - p[1]) * R)

    def poly(loop):
        im = Image.new("L", (GW, GH), 0)
        ImageDraw.Draw(im).polygon([px(p) for p in loop], fill=255)
        return np.array(im) > 127

    M = poly(out)
    CELL = poly(w["cloop"])
    # distance au contour et point le plus proche (largeur de bordure, frange)
    O = np.array(resample(out, 0.06, closed=True), np.float32)
    Ob = np.array(out, np.float32)
    near_i = np.array([int(np.argmin(np.hypot(Ob[:, 0] - p[0], Ob[:, 1] - p[1]))) for p in O])
    dist = np.empty((GH, GW), np.float32)
    idx = np.empty((GH, GW), np.int32)
    for r0 in range(0, GH, 8):
        dx = X[r0:r0 + 8, :, None] - O[None, None, :, 0]
        dy = Y[r0:r0 + 8, :, None] - O[None, None, :, 1]
        d2 = dx * dx + dy * dy
        k = np.argmin(d2, axis=2)
        idx[r0:r0 + 8] = near_i[k]
        dist[r0:r0 + 8] = np.sqrt(np.take_along_axis(d2, k[..., None], 2)[..., 0])
    BW = w["bw"][idx]
    FR = w["fringe"][idx]

    # fond : dégradé depuis la racine
    rt = w["root"]
    rr = np.hypot(X - rt[0], Y - rt[1])
    rr = rr / rr[M].max()
    if name == "fore":
        col = ramp(rr, [(0, ROSE), (0.36, BONBON), (0.68, LILAS), (0.92, CIEL), (1.0, CIEL)])
    else:
        col = ramp(rr, [(0, ROSE), (0.45, BONBON), (0.85, LILAS), (1.0, LILAS)])
    # bande de brillance irisée (reflet des écailles), en travers de l'aile
    ax = np.array([0.62, 0.78]) if name == "fore" else np.array([0.75, -0.66])
    proj = ((X - rt[0]) * ax[0] + (Y - rt[1]) * ax[1]) / (rr[M].max() * 0 + 1)
    pm = proj[M].max()
    sheen = np.exp(-(((proj / pm) - (0.56 if name == "fore" else 0.5)) / 0.09) ** 2)
    col = lerp(col, np.array(SHEEN, np.float32), (0.30 * sheen)[..., None])
    # écailles : rangées très fines parallèles au bord (±3 %), invisibles de loin, du grain de près
    rows = 0.5 + 0.5 * np.sin(dist * TAU / 0.42) * np.sin((X * 1.7 + Y * 1.1) * TAU / 0.5 + dist * 9)
    col = col * (0.975 + 0.04 * rows)[..., None]
    # cellule discale : plus claire (la lumière passe)
    col[CELL] = lerp(col[CELL], np.array(BLANC, np.float32), 0.28)
    # ombre de recouvrement : la postérieure passe sous l'antérieure ; racine un peu plus sombre
    if name == "hind":
        col *= (1 - 0.16 * np.clip((Y - 19.8) / 1.2, 0, 1))[..., None]
    col *= (1 - 0.18 * np.clip(1 - rr / 0.14, 0, 1))[..., None]

    opaque = np.zeros((GH, GW), bool)
    E = np.zeros((GH, GW, 3), np.float32)

    # nervures peintes (sous les baguettes en volume), effilées
    vimg = Image.new("L", (GW, GH), 0)
    vd = ImageDraw.Draw(vimg)

    def taper(pts, w0, w1):
        n = len(pts) - 1
        for i in range(n):
            wd = lerp(w0, w1, (i + 0.5) / n) * R
            a, b = px(pts[i]), px(pts[i + 1])
            vd.line([a, b], fill=255, width=max(1, int(round(wd))))
            vd.ellipse([b[0] - wd / 2, b[1] - wd / 2, b[0] + wd / 2, b[1] + wd / 2], fill=255)
    for path in w["vpaths"]:
        taper(curve(path[0], path[1], path[2], 14), 0.46, 0.26)
    cl = w["cloop"] + [w["cloop"][0]]
    taper(cl, 0.42, 0.42)
    if name == "fore":
        taper(w["costa"], 0.5, 0.36)
    VN = (np.array(vimg) > 127) & M

    # bordure prune festonnée, frange blanche coupée aux nervures (écailles du bord)
    band = M & (dist < BW)
    col[band] = PRUNE
    col[band] = lerp(col[band], np.array((196, 76, 160), np.float32), np.clip(1 - (BW[band] - dist[band]) / 0.25, 0, 1)[..., None] * 0.55)
    opaque |= band
    ends = [w["out"][i] for i in w["ends_idx"]]
    near_end = np.zeros((GH, GW), bool)
    for e in ends:
        near_end |= disc(X, Y, e[0], e[1], 0.32)
    fr = M & FR & (dist < 0.2) & ~near_end
    col[fr] = FRANGE
    opaque |= fr

    # pois blancs dans la bordure : un par lobe, au milieu de la bande
    Ob2 = np.array(w["out"])
    for ia, ib in w["lobes"]:
        j = (ia + ib) // 2
        p = Ob2[j]
        v = np.array(w["C"]) - p
        v = v / np.linalg.norm(v)
        wb = w["bw"][j]
        if wb < 0.7:
            continue
        c = p + v * (wb * 0.55)
        rd = min(0.34, wb * 0.3)
        d = M & disc(X, Y, c[0], c[1], rd)
        col[d] = BLANC
        E[d] = (150, 130, 160)
        opaque |= d

    col[VN] = VEINE
    opaque |= VN

    # motifs : cœur blanc dans la cellule (antérieure), ocelle en cœur (postérieure), pois apicaux, reflet « fenêtre »
    if name == "fore":
        h1 = heart(X, Y, 13.5, 26.5, 1.12)
        h0 = heart(X, Y, 13.5, 26.5, 0.88)
        col[h1] = PRUNE
        col[h0] = BLANC
        E[h0] = (205, 170, 215)
        opaque |= h1
        V = w["vpaths"]
        for (a, b, t, k) in ((1, 2, 0.8, 0.30), (2, 3, 0.76, 0.24)):
            pa, pb = on_path(V[a], t), on_path(V[b], t)
            c = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            rd = k * math.dist(pa, pb)
            d = disc(X, Y, c[0], c[1], rd) & M
            col[d] = BLANC
            E[d] = (165, 145, 175)
            opaque |= d
        # reflet : ellipse blanche entre R2 et R3, petit point à côté (un seul par aile)
        pa, pb = on_path(V[0], 0.42), on_path(V[1], 0.42)
        c = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
        g = math.dist(pa, pb)
        ang = math.atan2(V[0][1][1] - V[0][0][1], V[0][1][0] - V[0][0][0])
        u = ((X - c[0]) * math.cos(ang) + (Y - c[1]) * math.sin(ang)) / (0.5 * g)
        vv = (-(X - c[0]) * math.sin(ang) + (Y - c[1]) * math.cos(ang)) / (0.17 * g)
        hl = (u * u + vv * vv <= 1) & M & ~VN
        hl |= disc(X, Y, c[0] + math.cos(ang) * 0.95 * g, c[1] + math.sin(ang) * 0.95 * g, 0.12 * g) & M & ~VN
        col[hl] = BLANC
        E[hl] = (130, 128, 140)
        opaque |= hl
    else:
        cx, cy = 8.0, 17.25
        r3 = heart(X, Y, cx, cy, 1.62)
        r2 = heart(X, Y, cx, cy, 1.30)
        r1 = heart(X, Y, cx, cy, 0.95)
        col[r3] = PRUNE
        col[r2] = LILAS
        col[r1] = BLANC
        hl = disc(X, Y, cx - 0.42, cy + 0.38, 0.2)
        col[hl & r1] = (255, 200, 228)
        E[r1] = (205, 170, 215)
        opaque |= r3
        # goutte de la queue : lilas cerclé, pois blanc
        tq = disc(X, Y, 10.05, 4.95, 0.55) & M
        col[tq] = CIEL
        tq2 = disc(X, Y, 10.0, 5.0, 0.24) & M
        col[tq2] = BLANC
        E[tq2] = (150, 130, 160)
        opaque |= tq

    # opacité du sucre (trans_) : dense à la racine, plus légère vers l'apex, cellule plus claire ; motifs opaques
    a = (236 - 30 * np.clip((rr - 0.25) / 0.6, 0, 1)).astype(np.float32)
    a[CELL] -= 12
    a = np.clip(a, 200, 236)
    a[opaque] = 255
    a[~M] = 0
    E[~M] = 0
    w.update(map_col=col, map_e=E, map_a=a, map_M=M)


# côte (nervure épaissie du bord d'attaque de l'antérieure) : le long du contour, 0,3 px à l'intérieur, de la racine à R3
def costa_path(w):
    ctrl = [p for p, _ in w["ctrl"]]
    base, _ = catmull(ctrl, 40)
    stop = w["ends_idx"][1]
    pts = []
    for j in range(4, stop - 4):
        a, b = np.array(base[j - 1]), np.array(base[j + 1])
        d = (b - a) / np.linalg.norm(b - a)
        nrm = np.array((d[1], -d[0]))           # sens horaire : intérieur à droite
        p = np.array(base[j]) + nrm * 0.3
        pts.append((float(p[0]), float(p[1])))
    return resample(pts, 1.9)


WINGS["fore"]["costa"] = costa_path(WINGS["fore"])
for n, w in WINGS.items():
    paint(w, n)


# ------------------------------------------------------------------ tuiles
def stick_tile(c_mid, c_edge, e_line=None, BW=96, BH=16):
    a = np.zeros((BH, BW, 4), np.uint8)
    ae = np.zeros((BH, BW, 4), np.uint8)
    for yy in range(BH):
        q = abs((yy + 0.5) / BH - 0.5) * 2
        c = lerp(np.array(c_mid, float), np.array(c_edge, float), q ** 1.5)
        a[yy, :, :3] = np.clip(c, 0, 255)
    a[..., 3] = 255
    ae[..., 3] = 255
    return a, ae


vein_tile, vein_e = stick_tile((190, 70, 156), (160, 50, 132))
costa_tile, costa_e = stick_tile((176, 60, 146), (150, 44, 124))
thor_tile, thor_e = stick_tile((214, 96, 172), (160, 52, 134), BW=64)


def cris_tile(dots):
    BW, BH = 64, 32
    t = np.zeros((BH, BW, 4), np.uint8)
    te = np.zeros((BH, BW, 4), np.uint8)
    yy, xx = np.mgrid[0:BH, 0:BW]
    q = np.abs((xx + 0.5) / BW - 0.5) * 2
    c = lerp(np.array((156, 236, 204), np.float32), np.array((84, 178, 150), np.float32), (q ** 1.4)[..., None])
    c = c * (1 + 0.05 * np.sin((yy / BH) * TAU * 2))[..., None]
    if dots:
        for cx in (8, 24, 40, 56):
            d = (xx - cx) ** 2 + (yy - 16) ** 2 <= 30
            c[d] = (255, 212, 84)
            te[d, :3] = (190, 150, 50)
    t[..., :3] = np.clip(c, 0, 255)
    t[..., 3] = 255
    te[..., 3] = 255
    return t, te


cris_t, cris_e = cris_tile(False)
crisor_t, crisor_e = cris_tile(True)


def star_tile(n=24):
    """Paillette : étoile à quatre branches arrondies, cœur blanc, bord rose (particule, une face)."""
    S4 = n * 4
    yy, xx = np.mgrid[0:S4, 0:S4]
    u, v = (xx + 0.5) / S4 * 2 - 1, (yy + 0.5) / S4 * 2 - 1
    r = np.hypot(u, v)
    ang = np.arctan2(v, u)
    lim = 0.36 + 0.58 * np.abs(np.cos(2 * ang)) ** 6
    m = (r < lim).astype(np.float32)
    c = lerp(np.array((255, 255, 255), np.float32), np.array((255, 130, 196), np.float32), np.clip(r / 0.9, 0, 1)[..., None] ** 1.2)
    rgb = np.array(Image.fromarray(c.astype(np.uint8), "RGB").resize((n, n), Image.LANCZOS))
    al = np.array(Image.fromarray((m * 255).astype(np.uint8), "L").resize((n, n), Image.LANCZOS)) > 110
    t = np.zeros((n, n, 4), np.uint8)
    t[..., :3] = rgb
    t[..., 3] = al * 255
    te = np.zeros_like(t)
    te[..., :3] = (rgb.astype(np.float32) * 0.7).astype(np.uint8)
    te[..., 3] = al * 255
    te[~al] = 0
    return t, te


star, star_e = star_tile()
TILES = (("vein", vein_tile, vein_e), ("costa", costa_tile, costa_e), ("thor", thor_tile, thor_e),
         ("cris", cris_t, cris_e), ("crisor", crisor_t, crisor_e), ("star", star, star_e))

# ------------------------------------------------------------------ atlas
DENS = 16.0


def pack(dens):
    uv, dims = {}, {}
    for n, w in WINGS.items():
        x0, y0, x1, y1 = w["box"]
        dims[n] = (int(math.ceil((x1 - x0) * dens)), int(math.ceil((y1 - y0) * dens)))
    Wf, Hf = dims["fore"]
    Wh, Hh = dims["hind"]
    uv["fore"] = (0, 0, Wf, Hf)
    uv["hind"] = (0, Hf + 1, Wh, Hf + 1 + Hh)
    tx, ty = Wh + 2, Hf + 2
    for n, im, _ in TILES:
        h, wd = im.shape[:2]
        uv[n] = (tx, ty, tx + wd, ty + h)
        ty += h + 2
    if Wf > TEX or Hf + 1 + Hh > TEX - 6 or tx + 96 > TEX or ty > TEX - 6:
        return None
    return uv


while (UV := pack(DENS)) is None:
    DENS -= 0.25
tex = np.zeros((TEX, TEX, 4), np.uint8)
tex_e = np.zeros((TEX, TEX, 4), np.uint8)
for n, im, ie in TILES:
    u0, v0, u1, v1 = UV[n]
    tex[v0:v1, u0:u1] = im
    tex_e[v0:v1, u0:u1] = ie
for n, w in WINGS.items():
    u0, v0, u1, v1 = UV[n]
    W, H = u1 - u0, v1 - v0
    x0, y0, x1, y1 = w["box"]
    w["box"] = (x0, y1 - H / DENS, x0 + W / DENS, y1)
    GWn, GHn = int(round(W / DENS * R)), int(round(H / DENS * R))
    pad = lambda arr: np.pad(arr, ((0, max(0, GHn - arr.shape[0])), (0, max(0, GWn - arr.shape[1]))) + ((0, 0),) * (arr.ndim - 2))[:GHn, :GWn]
    rgb = Image.fromarray(np.clip(pad(w["map_col"]), 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    erg = Image.fromarray(np.clip(pad(w["map_e"]), 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    al = np.array(Image.fromarray(pad(w["map_M"]).astype(np.uint8) * 255, "L").resize((W, H), Image.LANCZOS)) > 110
    aa = np.array(Image.fromarray(np.clip(pad(w["map_a"]), 0, 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)).astype(np.float32)
    c = np.array(rgb)
    c[~al] = c[al].mean(axis=0).astype(np.uint8)
    tex[v0:v1, u0:u1, :3] = c
    aa = np.where(aa > 242, 255, np.clip(aa, 200, 236))
    tex[v0:v1, u0:u1, 3] = np.where(al, aa, 0).astype(np.uint8)
    ce = np.array(erg)
    ce[~al] = 0
    tex_e[v0:v1, u0:u1, :3] = ce
    tex_e[v0:v1, u0:u1, 3] = al * 255

CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]
assert tex[TEX - 3, TEX - 3, 3] == 0
tex[..., :3] &= 0xFC
_semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
for _n, _, _ in TILES:
    u0, v0, u1, v1 = UV[_n]
    assert not _semi[v0:v1, u0:u1].any(), _n
assert set(np.unique(tex_e[..., 3])) <= {0, 255}


def b64(img, path):
    img.save(path, optimize=True)
    b = io.BytesIO()
    img.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


tex_b64 = b64(Image.fromarray(tex, "RGBA"), f"{NOM}.png")
tex_e_b64 = b64(Image.fromarray(tex_e, "RGBA"), f"{NOM}_e.png")

# ------------------------------------------------------------------ géométrie
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def cube(name, frm, to, origin, rot=(0, 0, 0), faces=None):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to],
         "origin": [round(v, 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(v, 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(rot):
        e["rotation"] = [round(v, 2) for v in rot]
    elements.append(e)
    return e["uuid"]


def group(name, origin, parent=None, rotation=(0, 0, 0)):
    assert name not in groups
    groups[name] = {"origin": [round(v, 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent,
                    "rotation": [round(v, 2) for v in rotation]}
    return name


def plate(s, g, name, w, uvname, th=0.3):
    u0, v0, u1, v1 = UV[uvname]
    x0, y0, x1, y1 = w["box"]
    ua, ub = (u0, u1) if s > 0 else (u1, u0)
    xa, xb = (x0, x1) if s > 0 else (-x1, -x0)
    z = w["z"]
    faces = {"south": [ua, v0, ub, v1], "north": [ub, v0, ua, v1], "east": CLEAR, "west": CLEAR, "up": CLEAR, "down": CLEAR}
    groups[g]["ids"].append(cube(name, [xa, y0, z - th / 2], [xb, y1, z + th / 2], [s * (x0 + x1) / 2, (y0 + y1) / 2, z], faces=faces))


def bar(s, g, name, x, y, z, L, q, phi, u0, u1, tile="vein", ov=0.0):
    """Tronçon de baguette en losange (cube tourné de 45° autour de son axe) : aucune face parallèle à la membrane."""
    bu0, bv0, bu1, bv1 = UV[tile]
    ua, ub = lerp(bu0, bu1, u0), max(lerp(bu0, bu1, u1), lerp(bu0, bu1, u0) + 2)
    long_ = [ua, bv0, ub, bv1]
    faces = {"south": long_, "north": long_, "up": long_, "down": long_, "east": CLEAR, "west": CLEAR}
    a, b = (x - ov, x + L + ov) if s > 0 else (-x - L - ov, -x + ov)
    groups[g]["ids"].append(cube(name, [a, y - q, z - q], [b, y + q, z + q], [s * x, y, z], rot=(45, 0, s * phi), faces=faces))


def chain(s, g, name, pts, r0, r1, z, tile="vein", ov=0.1, closed=False):
    if closed:
        pts = pts + [pts[0]]
    n = len(pts) - 1
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        L = math.dist(pts[i], pts[i + 1])
        phi = math.degrees(math.atan2(yb - ya, xb - xa))
        q = lerp(r0, r1, (i + 0.5) / n) + (0.05 if i % 2 == 0 else -0.05)   # rayons alternés : pas de faces jumelles
        bar(s, g, f"{name}{i}", xa, ya, z, L, q, phi, i / n, (i + 1) / n, tile=tile, ov=ov)


EMITS = []


def build(s):
    tag = "l" if s < 0 else "r"
    out = []
    for n, w in WINGS.items():
        g = group(f"{n}_{tag}", [s * w["piv"][0], w["piv"][1], w["z"]])
        tg = group(f"trans_{n}_{tag}", [s * w["piv"][0], w["piv"][1], w["z"]], parent=g)
        plate(s, tg, f"{n}_m_{tag}", w, n)
        chain(s, g, f"{n}_dc_{tag}", resample(w["cloop"], 1.7, closed=True), 0.2, 0.2, w["z"], closed=True)
        for k, (p0, p1, bow) in enumerate(w["vpaths"]):
            # une seule baguette droite par nervure (pas de jointure : pas de « perles » le long de la nervure)
            L = math.dist(p0, p1)
            bar(s, g, f"{n}_v{k}_{tag}", p0[0], p0[1], w["z"], L, 0.19, math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])), 0, 1)
        if n == "fore":
            chain(s, g, f"{n}_co_{tag}", w["costa"], 0.24, 0.17, w["z"], tile="costa")
        out.append(g)
    fo, hi = WINGS["fore"], WINGS["hind"]
    pts = ((out[0], fo["out"][fo["ends_idx"][2]], ZF), (out[0], fo["out"][fo["ends_idx"][4]], ZF), (out[1], (10.0, 4.6), ZH))
    for gname, pt, z in pts:
        EMITS.append(group("emit_paillette" + (str(len(EMITS) + 1) if EMITS else ""), [s * pt[0], pt[1], z], parent=gname))
    return out


GL, GR = build(-1), build(1)

# thorax duveteux au milieu du dos (racine commune des quatre ailes), octogone ; sommet à y = 23,15, sous la tête
TH = group("thorax", [0, 21.8, 3.35])
_tu0, _tv0, _tu1, _tv1 = UV["thor"]
_thf = {f: [_tu0, _tv0, _tu1, _tv1] for f in ("north", "south", "east", "west", "up", "down")}
groups[TH]["ids"].append(cube("thorax_a", [-1.25, 20.6, 2.45], [1.25, 23.1, 3.75], [0, 21.8, 3.35], faces=_thf))
groups[TH]["ids"].append(cube("thorax_b", [-0.8, 20.75, 2.39], [0.8, 22.95, 4.05], [0, 21.8, 3.35], rot=(0, 45, 0), faces=_thf))

# chrysalide (apparition seulement) : goutte menthe à ceinture de points dorés, en deux moitiés qui s'ouvrent ; cachée dans les
# états par une échelle K_CACHE et un recul dans le torse (recette d'ailes_steampunk) que event_equip annule
K_CACHE, CZ = 0.1, 4.3
CRIS_TOP = 23.05
CH = group("chrysalide", [0, CRIS_TOP, CZ])
NR = 8
for s, tag in ((-1, "l"), (1, "r")):
    hg = group(f"cris_{tag}", [0, CRIS_TOP, CZ], parent=CH)
    for i in range(NR):
        yb = 15.6 + i * (CRIS_TOP - 15.6) / NR
        yt = 15.6 + (i + 1) * (CRIS_TOP - 15.6) / NR + 0.1
        u = (i + 0.5) / NR
        r = max(0.55, 1.95 * math.sin(math.pi * u ** 0.85) ** 0.55)
        tl = "crisor" if i == 5 else "cris"
        uu = UV[tl]
        f = {k: list(uu) for k in ("north", "south", "east", "west", "up", "down")}
        xa, xb = (0.17, r * 0.74) if s > 0 else (-r * 0.74, -0.17)
        groups[hg]["ids"].append(cube(f"cris_{tag}{i}a", [xa, yb, CZ - r], [xb, yt, CZ + r], [0, CRIS_TOP, CZ], faces=f))
        xa, xb = (0.05, r) if s > 0 else (-r, -0.05)
        groups[hg]["ids"].append(cube(f"cris_{tag}{i}b", [xa, yb + 0.12, CZ - r * 0.74], [xb, yt - 0.12, CZ + r * 0.74],
                                      [0, CRIS_TOP, CZ], faces=f))

PL = group("particle_paillette", [0, 0, 0])
_su0, _sv0, _su1, _sv1 = UV["star"]
groups[PL]["ids"].append(cube("paillette", [-0.3, 0.3, -0.3], [0.3, 0.6, 0.3], [0, 0, 0], faces={"up": [_su0, _sv0, _su1, _sv1]}))


def bone(name):
    g = groups[name]
    return {"name": name, "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone(n) for n, gg in groups.items() if gg["parent"] == name]}


outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone(n) for n in GL + GR + [TH, CH]]}, bone(PL)]

# ------------------------------------------------------------------ animations
# Papillon : ailes rigides qui pivotent à la racine. Intention, aile GAUCHE :
#   fx > 0 : le plan bascule vers l'horizontale ; fy > 0 : l'aile se referme vers l'arrière (V) ; fz > 0 : la pointe monte.
# MIROIR D'AXES : seul endroit à toucher si la convention change (guide, section 3).
SX, SY, SZ = -1, -1, +1


def mirror(s, fx, fy, fz):
    return SX * fx, s * SY * fy, s * SZ * fz


def kf(ch, t, x, y, z):
    return {"channel": ch, "data_points": [{"x": str(round(x + 0.0, 3)), "y": str(round(y + 0.0, 3)), "z": str(round(z + 0.0, 3))}],
            "time": round(t, 3), "interpolation": "linear"}


def cacher(A):
    """Chrysalide cachée (échelle K_CACHE, reculée dans le torse) : dans chaque état et réaction, pour que l'aperçu seul soit juste."""
    A[groups[CH]["uuid"]] = {"name": CH, "type": "bone", "keyframes": [kf("scale", 0, K_CACHE, K_CACHE, K_CACHE),
                                                                        kf("position", 0, 0, 0, -CZ)]}


def anim(name, length, fore, lag=0.08, hind_amp=0.9, hind_off=(0, 0, 2), n_kf=None, loop="loop"):
    A = {}
    n = n_kf or max(8, int(round(length * 8)))
    times = [i * length / n for i in range(n + 1)]
    lag_s = lag * length if loop == "loop" else lag

    def hind(t):
        tt = (t - lag_s) % length if loop == "loop" else max(0.0, t - lag_s)
        fx, fy, fz = fore(tt)
        k = 1.0 if loop == "loop" else (1.0 if t > 0 else 0.0)
        return fx * 0.35, fy * hind_amp, fz * 0.4 + hind_off[2] * k

    for s, tag in ((-1, "l"), (1, "r")):
        A[groups[f"fore_{tag}"]["uuid"]] = {"name": f"fore_{tag}", "type": "bone",
                                            "keyframes": [kf("rotation", t, *mirror(s, *fore(t))) for t in times]}
        A[groups[f"hind_{tag}"]["uuid"]] = {"name": f"hind_{tag}", "type": "bone",
                                            "keyframes": [kf("rotation", t, *mirror(s, *hind(t))) for t in times]}
    cacher(A)
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
            "selected": name == "idle", "animators": A}


def sn(t, T, k=1, ph=0.0):
    return math.sin(TAU * k * t / T + math.radians(ph))


# idle 8 s : papillon posé, ailes dressées en V derrière le dos ; respiration (4 s) ; frisson de nervosité (1,0–1,8 s : trois
# petits battements) ; bain de soleil : ouverture lente 3,6–5,0 s, ouvertes, refermées 6,2–7,7 s
def idle_f(t):
    fl = 12 * math.sin(TAU * (t - 1.0) / 0.27) ** 2 * bump(t, 0.95, 1.1, 1.65, 1.85)
    return (6, 52 + 4 * sn(t, 8, 2) - 40 * bump(t, 3.6, 5.0, 6.2, 7.7) - fl, 4 + 2 * sn(t, 8, 2, -40))


idle = anim("idle", 8.0, idle_f, lag=0.02, n_kf=96)
walk = anim("walk", 1.6, lambda t: (6, 54 + 6 * sn(t, 1.6), 2 + 3 * sn(t, 1.6, 1, -40)), lag=0.08, n_kf=16)
run = anim("run", 1.0, lambda t: (10, 72 + 4 * sn(t, 1.0, 2), -16 + 2 * sn(t, 1.0, 2, -60)), lag=0.06, n_kf=16)
sneak = anim("sneak", 3.0, lambda t: (4, 82 + 1.5 * sn(t, 3.0), 8 + 1 * sn(t, 3.0, 1, -40)), lag=0.05, hind_amp=0.8, hind_off=(0, 0, 0), n_kf=12)


# fly 2,4 s : joueur debout, plan basculé ~40° ; trois battements « claque et lance » (0–1,35 s ; lancer = ouverture, plus long
# que la claque) puis plané ailes ouvertes en léger V (1,35–2,4 s), petites corrections
FB = 0.45


def fly_f(t):
    if t < 3 * FB:
        u = (t % FB) / FB
        ph = 0.5 - 0.5 * math.cos(TAU * (u ** 1.25))          # claque rapide (0 → 1), lancer plus long (1 → 0)
        fy = -6 + 70 * ph
        fz = 2 + 5 * math.sin(TAU * u - 0.9)
    else:
        fy = -6 + 8 * bump(t, 1.35, 1.7, 2.05, 2.4) + 2 * math.sin(TAU * (t - 1.35) / 1.05) * bump(t, 1.35, 1.6, 2.15, 2.4)
        fz = 2 + 5 * math.sin(-0.9) * (1 - bump(t, 1.35, 1.6, 2.1, 2.4)) + 5 * bump(t, 1.35, 1.6, 2.1, 2.4)
    return (40, fy, fz)


fly = anim("fly", 2.4, fly_f, lag=0.012, n_kf=96)
fall = anim("fall", 1.5, lambda t: (26, 14 + 9 * sn(t, 1.5, 3), 5 + 2 * sn(t, 1.5, 3, -60)), lag=0.05, n_kf=36)
swim = anim("swim", 2.0, lambda t: (4, 22 + 12 * sn(t, 2.0), -24 + 4 * sn(t, 2.0, 1, -60)), lag=0.1, n_kf=20)
mount = anim("mount", 3.0, lambda t: (6, 40 + 10 * sn(t, 3.0), 8 + 3 * sn(t, 3.0, 1, -40)), lag=0.05, n_kf=18)
sleep = anim("sleep", 4.0, lambda t: (2, 80 + 2 * sn(t, 4.0), -10 + 1.5 * sn(t, 4.0, 1, -40)), lag=0.05, n_kf=12)
# attack : claque puis lancer (montre l'ocelle, réflexe d'intimidation du papillon) ; jamais vers l'avant (bras)
attack = anim("attack", 0.8, lambda t: (6 * bump(t, 0, 0.1, 0.3, 0.7),
                                        26 * bump(t, 0, 0.1, 0.14, 0.3) - 10 * bump(t, 0.16, 0.3, 0.4, 0.72),
                                        7 * bump(t, 0, 0.12, 0.3, 0.7)),
              lag=0.04, hind_off=(0, 0, 0), n_kf=20, loop="once")
hurt = anim("hurt", 0.8, lambda t: (4 * bump(t, 0, 0.08, 0.22, 0.7),
                                    22 * bump(t, 0, 0.08, 0.22, 0.7) + 4 * math.sin(TAU * 5 * t / 0.8) * (1 - sm(t, 0.25, 0.7)),
                                    -4 * bump(t, 0, 0.08, 0.22, 0.7)),
            lag=0.04, hind_off=(0, 0, 0), n_kf=16, loop="once")

G = 3.6
BOOST = f"math.clamp((math.max(q.ground_speed,q.vertical_speed)-{V0})/{DV},0,1)*math.clamp((q.vertical_speed+8)/4,0,1)"


def term(amp, speed, ph):
    if not amp:
        return ""
    p = f"{ph:+g}" if ph else ""
    return f"{amp:+g}*math.sin(q.anim_time*{speed}{p})"


def mol(sign, base, slow=(0, 0), boost=(0, 0)):
    e = f"{sign * base:g}" + term(sign * slow[0], 100, slow[1])
    if boost[0]:
        e += f"{sign * boost[0]:+g}*{BOOST}*math.sin(q.anim_time*600{boost[1]:+g})"
    assert len(e) <= 256
    return e


def glide_anim():
    A = {}
    for s_, tag in ((-1, "l"), (1, "r")):
        sx, sy, sz = mirror(s_, 1, 1, 1)
        for g, ph, zoff in (("fore", 0, 4), ("hind", -30, -2)):
            A[groups[f"{g}_{tag}"]["uuid"]] = {"name": f"{g}_{tag}", "type": "bone", "keyframes": [
                {"channel": "rotation", "data_points": [{"x": mol(sx, 6, (1.5, 90 + ph)), "y": mol(sy, 8, (7, ph), (22, ph * 1.5)),
                                                         "z": f"{sz * zoff:g}"}], "time": 0, "interpolation": "linear"}]}
    cacher(A)
    return {"uuid": nuid(), "name": "glide", "loop": "loop", "override": False, "length": G, "snapping": 24, "selected": False, "animators": A}


glide = glide_anim()

PF = 2.0
paillette_fall = {"uuid": nuid(), "name": "particle_paillette_fall", "loop": "loop", "override": False, "length": PF, "snapping": 24,
                  "selected": False, "animators": {groups[PL]["uuid"]: {"name": PL, "type": "bone", "keyframes": [
                      kf("rotation", t, 20 * math.sin(TAU * t / PF), 360 * t / PF, 0) for t in [i * PF / 16 for i in range(17)]]}}}


def plop(t, t0, t1, over=1.15):
    if t <= t0:
        return 0.0
    if t >= t1:
        return 1.0
    u = (t - t0) / (t1 - t0)
    if u < 0.45:
        return over * sm(u, 0, 0.45)
    if u < 0.7:
        return lerp(over, 0.95, sm(u, 0.45, 0.7))
    return lerp(0.95, 1.0, sm(u, 0.7, 1.0))


# ---- event_equip 3,4 s : éclosion (joué par-dessus l'état : rotations ajoutées, échelles multipliées)
EQ = 3.4
T_CRACK = 1.0


def eq_chrys(t):
    """Échelle (relative à l'état, d'où le 1/K_CACHE) et recul annulé de la chrysalide, frétillement."""
    if t < 1.7:
        c = plop(t, 0.0, 0.45) * (1 - sm(t, 1.25, 1.7))
        return c / K_CACHE, CZ, 7 * math.sin(TAU * (t - 0.45) / 0.22) * bump(t, 0.45, 0.5, 0.85, 0.95)
    return 1.0, 0.0, 0.0


def eq_wing(t):
    """(sx, sy, ajout fy, ajout fz) : sortie froissée et pendante, gonflement par à-coups, relèvement, premier lancer."""
    if t < T_CRACK - 0.02:
        return 0.0, 0.0, 18.0, -38.0
    g = sm(t, T_CRACK, 2.45)
    pump = 0.07 * max(0.0, math.sin(TAU * (t - T_CRACK) / 0.42)) * (1 - g)
    sx = min(1.0, 0.14 + 0.86 * g + pump)
    sy = min(1.0, 0.1 + 0.9 * sm(t, T_CRACK + 0.1, 2.5) + pump)
    fy = 18 * (1 - sm(t, 2.6, 2.85)) - 12 * bump(t, 2.6, 2.85, 2.95, 3.35)
    fz = -38 * (1 - sm(t, 2.15, 2.7)) + 2.5 * math.sin(TAU * (t - T_CRACK) / 0.42) * (1 - g)
    if t >= EQ - 1e-6:
        return 1.0, 1.0, 0.0, 0.0
    return sx, sy, fy, fz


def build_equip():
    n = 68
    times = [round(i * EQ / n, 3) for i in range(n + 1)]
    A = {}
    A[groups[CH]["uuid"]] = {"name": CH, "type": "bone", "keyframes":
                             [kf("scale", t, *(eq_chrys(t)[0],) * 3) for t in times]
                             + [kf("position", t, 0, 0, eq_chrys(t)[1]) for t in times]
                             + [kf("rotation", t, 0, 0, eq_chrys(t)[2]) for t in times]}
    for s, tag in ((-1, "l"), (1, "r")):
        A[groups[f"cris_{tag}"]["uuid"]] = {"name": f"cris_{tag}", "type": "bone", "keyframes":
                                            [kf("rotation", t, 0, 0, s * 30 * sm(t, T_CRACK - 0.05, 1.3)) for t in times]}
        for gname in ("fore", "hind"):
            ks = []
            for t in times:
                sx, sy, fy, fz = eq_wing(t)
                ks.append(kf("scale", t, sx, sy, 1.0 if sx > 0 else 0.0))
                ks.append(kf("rotation", t, *mirror(s, 0, fy * (0.9 if gname == "hind" else 1.0), fz * (0.85 if gname == "hind" else 1.0))))
            A[groups[f"{gname}_{tag}"]["uuid"]] = {"name": f"{gname}_{tag}", "type": "bone", "keyframes": ks}
    A[groups[TH]["uuid"]] = {"name": TH, "type": "bone", "keyframes": [kf("scale", t, *(plop(t, 0.9, 1.4),) * 3) for t in times]}
    A["effects"] = {"name": "Effects", "type": "effect", "keyframes":
                    [{"channel": "sound", "data_points": [{"effect": "entity.turtle.egg_hatch", "file": ""}], "time": T_CRACK}]}
    return {"uuid": nuid(), "name": "event_equip", "loop": "once", "override": False, "length": EQ, "snapping": 24,
            "selected": False, "animators": A}


# ---- event_unequip 1,6 s : les ailes se serrent, frissonnent, retombent et rapetissent ; le thorax disparaît en dernier
UQ = 1.6


def build_unequip():
    n = 32
    times = [round(i * UQ / n, 3) for i in range(n + 1)]
    A = {}
    for s, tag in ((-1, "l"), (1, "r")):
        for gname in ("fore", "hind"):
            ks = []
            for t in times:
                sc = 0.0 if t >= UQ - 0.11 else lerp(1.0, 1.06, sm(t, 0.0, 0.35)) * (1 - sm(t, 0.5, 1.3))
                fy = 18 * sm(t, 0.0, 0.4) + 3 * math.sin(TAU * t / 0.12) * bump(t, 0.3, 0.4, 0.6, 0.75)
                fz = -20 * sm(t, 0.45, 1.2)
                ks.append(kf("scale", t, sc, sc, sc))
                ks.append(kf("rotation", t, *mirror(s, 0, fy, fz)))
            A[groups[f"{gname}_{tag}"]["uuid"]] = {"name": f"{gname}_{tag}", "type": "bone", "keyframes": ks}
    A[groups[TH]["uuid"]] = {"name": TH, "type": "bone", "keyframes":
                             [kf("scale", t, *((1.0 - sm(t, 1.1, 1.5)) if t < UQ - 1e-6 else 0.0,) * 3) for t in times]}
    return {"uuid": nuid(), "name": "event_unequip", "loop": "once", "override": False, "length": UQ, "snapping": 24,
            "selected": False, "animators": A}


equip, unequip = build_equip(), build_unequip()
ANIMS = [idle, walk, run, sneak, fly, glide, fall, swim, mount, sleep, attack, hurt, paillette_fall, equip, unequip]
assert len(ANIMS) <= 32

textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM,
         "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
from sons import limiter_sons
limiter_sons(model)
os.makedirs(".build", exist_ok=True)
OUT = f".build/{NOM}_brut.bbmodel"
with open(OUT, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(nd, d=1):
    return max([depth(c, d + 1) for c in nd.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", depth(outliner[0]), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(OUT) // 1024, "Ko ;",
      f"densité membrane {DENS:.2f} texels/px")
