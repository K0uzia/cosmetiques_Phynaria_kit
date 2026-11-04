"""Familier hibou mécanique : petit hibou automate en laiton qui flotte à droite du joueur, un peu en arrière, à hauteur d'épaule.
Ensemble Steampunk (thème Mécanique), fiche .claude/styles/steampunk.md. Design original.
Écrit familier_hibou_mecanique.png, familier_hibou_mecanique_e.png et .build/familier_hibou_mecanique_brut.bbmodel à côté de ce script.

Volume : corps en oeuf et tête ronde en polyèdres (8 fuseaux) dont chaque facette est une PEAU de laiton riveté de 0,3 px,
peinte en 3D (joints, rivets, disque facial), autour d'une ÂME pleine (prismes octogonaux). Plastron en écailles de cuivre
rondes découpées par alpha, ailes repliées en lames de laiton à nervure pleine, queue en éventail de lames, aigrettes en lames.
Yeux : tube d'acier creux, verre ambre (calque _e), pupille (scale : diaphragme), iris d'acier à 3 crans (rotation),
paupière-volet (scale y depuis le haut : ferme l'oeil par crans), bague de laiton. Clé de remontage au dos (rotation par
crans, 360° x k par boucle), hélice carénée sous le corps (rotation continue, 360° x k), soupape sur la tête.

Mouvement : paliers d'automate (réponse de servo amortie : arrivée sèche, léger dépassement, rappel), tics réguliers
de la clé, battements par à-coups ; seuls le flottement et l'hélice sont continus. Les paliers d'une boucle comptent
aussi la fin des paliers de la boucle précédente : la boucle se referme sans saut.

Fonctions avancées (guide, sections 4 bis, 5 ter §4, 6.3 à 6.5 ; .claude/rules/fonctions-avancees.md) :
  - emit_mc_white_smoke (particule de Minecraft à la soupape, direction +Y ; cadence réglée par le staff) ;
  - trans_vapeur (bouffée modélisée : 2 plaques croisées en dégradé d'opacité ; se lit aussi en cutout) ;
  - overlay_mecanisme (couche permanente) : hélice en rotation continue (360° x 4 par 1,2 s, ne saute plus entre
    deux états) et tete_suivi qui suit le regard du joueur par crans de 22,5° (math.floor sur q.head_y_rotation,
    limité à ±45°) ; la clé de remontage, par crans, reste dans les états (immobile en sommeil) ;
  - son : un sifflement de vapeur (block.fire.extinguish) à la décharge de fin de boucle idle, rien d'autre.

Hiérarchie (body = torse du joueur) :
  fam_elan    (attack/hurt uniquement : position)
  fam_pos     (position d'état : flottement, rapprochement)
  fam_regard  (rotation d'état : penché, bascule couchée en glide/swim)
  fam_snap    (attack/hurt uniquement : rotation)
  corps       (peaux, âmes, cou, écailles, carénage)
    tete_suivi (overlay : regard du joueur) > tete (rotation par paliers) > oeil_l/oeil_r (base tournée sur l'axe de la lentille) > iris_*, pupille_*, paupiere_* ;
         aigrette_l/r ; soupape > soupape_cap > emit_mc_white_smoke ; trans_vapeur
    aile_l/aile_r > lame_*0..2 ; queue > queue_l, queue_r ; cle ; rotor
"""
import base64, io, json, math, os, zlib, uuid as _uuid
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AVEC_E = True       # calque _e embarqué en seconde texture (correctif du clignotement annoncé le 2026-11-03, à vérifier en jeu)
NOM = "familier_hibou_mecanique"
TEX = 512
TAU = 2 * math.pi
SS = 3

# ------------------------------------------------------------------ palette (fiche de style Steampunk)
BRASS = dict(hi=(236, 196, 112), base=(190, 142, 64), low=(112, 76, 32))
COPPER = dict(hi=(232, 150, 96), base=(176, 92, 52), low=(98, 46, 26))
STEEL = dict(hi=(136, 140, 150), base=(78, 82, 92), low=(38, 40, 48))
PATINA = np.array((132, 186, 160), np.float32)
PATINA_D = np.array((82, 138, 116), np.float32)
AMBRE_C = np.array((255, 210, 120), np.float32)
AMBRE = np.array((220, 150, 50), np.float32)
E_AMBRE = np.array((214, 132, 48), np.float32)      # lueur chaude et douce : couleur moyenne, pas vive

C0 = np.array((8.0, 27.0, 1.5))    # perchoir : épaule droite, un peu en arrière (le carénage repose sur l'épaule, y = 24 ; loin de la tête qui tourne)


def A(c):
    return np.array(c, np.float32)


def lerp(a, b, k):
    return a + (b - a) * k


def sm(t, a, b):
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    u = (t - a) / (b - a)
    return u * u * (3 - 2 * u)


def smv(x, a, b):
    u = np.clip((x - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


def bump(t, a, b, c, d):
    return sm(t, a, b) * (1 - sm(t, c, d))


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def V(*a):
    return np.array(a, float)


def seg_dist(px, py, pts):
    d = np.full(px.shape, 1e9, np.float32)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        vx, vy = bx - ax, by - ay
        t = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy), 0, 1)
        d = np.minimum(d, np.hypot(px - ax - t * vx, py - ay - t * vy))
    return d


def rodrigues(v, k, ang):
    k = unit(k)
    a = math.radians(ang)
    return v * math.cos(a) + np.cross(k, v) * math.sin(a) + k * (k @ v) * (1 - math.cos(a))


# ------------------------------------------------------------------ polyèdres : corps (oeuf) et tête
class Ovo:
    """Surface de révolution facettée : rh(lat) = rh * cos(lat) * (1 - taper * sin(lat)), y = rv * sin(lat). Repère local, avant = -Z."""

    def __init__(self, tag, rh, rv, lats, nlon=8, taper=0.0):
        self.tag, self.rh, self.rv, self.lats, self.nlon, self.taper = tag, rh, rv, lats, nlon, taper
        self.dlon = 360.0 / nlon
        self.facets = []
        for j in range(len(lats) - 1):
            for k in range(nlon):
                p0, p1, l0, l1 = k * self.dlon, (k + 1) * self.dlon, lats[j], lats[j + 1]
                v = [self.P(p0, l0), self.P(p1, l0), self.P(p1, l1), self.P(p0, l1)]
                X = unit(v[1] - v[0])
                Y = (v[2] + v[3]) / 2 - (v[0] + v[1]) / 2
                Y = unit(Y - (Y @ X) * X)
                n = np.cross(X, Y)
                cen = sum(v) / 4
                if n @ cen < 0:
                    X, n = -X, -n
                pts = [((q - cen) @ X, (q - cen) @ Y) for q in v]
                xs, ys = [a for a, _ in pts], [b for _, b in pts]
                bx, by = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
                cout = cen + X * bx + Y * by
                w, h = max(xs) - min(xs) + 0.08, max(ys) - min(ys) + 0.08
                poly = [(a - bx, b - by) for a, b in pts]
                self.facets.append(dict(name=f"{tag}_{j}_{k}", cout=cout, X=X, Y=Y, n=n, w=w, h=h, poly=poly, band=j, gore=k))

    def k(self, lat):
        return 1 - self.taper * math.sin(math.radians(lat))

    def P(self, phi, lat, s=1.0):
        p, l = math.radians(phi), math.radians(lat)
        r = self.rh * math.cos(l) * self.k(lat)
        return V(r * math.sin(p), self.rv * math.sin(l), -r * math.cos(p)) * s

    def normal(self, p):
        """Normale lissée (ellipsoïde approché) : sert à la peinture continue d'une facette à l'autre."""
        return p / np.array((self.rh ** 2, self.rv ** 2, self.rh ** 2), np.float32)

    def facet(self, band, gore):
        return next(f for f in self.facets if f["band"] == band and f["gore"] == gore % self.nlon)


BODY = Ovo("corps", 1.9, 2.1, [-66.0, -30.0, 5.0, 42.0], taper=0.10)
HEAD = Ovo("tete", 1.95, 1.55, [-48.0, -12.0, 24.0, 58.0])
HY = 2.4                 # centre de la tête au-dessus du centre du corps
NECK_Y = 1.45            # pivot du cou
TH = 0.3                 # épaisseur d'une peau

# yeux : centre de la facette avant de la bande médiane de la tête
EYES = {}
for s, tag in ((1, "r"), (-1, "l")):
    f = HEAD.facet(1, 0 if s > 0 else 7)
    axe = unit(f["n"] + V(0, 0, -1.0) * 1.1)        # entre la normale et l'avant : regard franc, léger écart
    EYES[tag] = dict(s=s, c=f["cout"].copy(), axe=axe)
EX, EY = abs(EYES["r"]["c"][0]), EYES["r"]["c"][1]

LUM = unit(V(-0.45, 0.85, -0.45)).astype(np.float32)


# ------------------------------------------------------------------ outils de peinture
def grid(W, H, w, h, ss=SS):
    gx = ((np.arange(W * ss) + 0.5) / (W * ss) - 0.5) * w
    gy = (0.5 - (np.arange(H * ss) + 0.5) / (H * ss)) * h
    return np.meshgrid(gx, gy)


def down_mask(m_ss, W, H):
    return np.array(Image.fromarray((np.clip(m_ss, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)) > 110


def inset(mask, n):
    im = Image.fromarray(mask.astype(np.uint8) * 255, "L")
    d = np.zeros(mask.shape, np.float32)
    for _ in range(n):
        im = im.filter(ImageFilter.MinFilter(3))
        d += np.array(im) > 127
    return d


def noise(H, W, cells, seed):
    r = np.random.default_rng(seed)
    a = (r.random((max(2, int(cells * H / max(H, W))) + 2, max(2, int(cells * W / max(H, W))) + 2)) * 255).astype(np.uint8)
    return np.array(Image.fromarray(a, "L").resize((W, H), Image.BICUBIC), np.float32) / 255


def finish(col, mask, e=None):
    H, W = mask.shape
    out = np.zeros((H, W, 4), np.uint8)
    c = np.clip(col, 0, 255)
    if mask.any():
        c[~mask] = c[mask].mean(axis=0)
    out[..., :3] = c.astype(np.uint8)
    out[..., 3] = mask * 255
    oe = np.zeros((H, W, 4), np.uint8)
    if e is not None:
        on = mask & (e.max(axis=2) > 2)
        oe[on, :3] = np.clip(e[on], 0, 255).astype(np.uint8)
        oe[on, 3] = 255
    return out, oe


def metal_shade(metal, lam, streak):
    """lam : éclairage 0..1. Laiton moyen dominant, clair sur les bombés, sombre dans les creux."""
    c = lerp(A(metal["low"]), A(metal["base"]), np.clip(0.30 + lam * 0.95, 0, 1)[..., None])
    c = lerp(c, A(metal["hi"]), (smv(lam, 0.70, 0.98) * 0.85)[..., None])
    return c * (1 + 0.10 * streak)[..., None]


def rivet(col, px, py, x, y, r, metal):
    """Rivet peint en coordonnées modèle : anneau sombre, tête, éclat en haut à gauche."""
    d = np.hypot(px - x, py - y)
    col[d <= r * 1.35] = A(metal["low"]) * 0.6
    col[d <= r] = A(metal["base"])
    col[np.hypot(px - x + r * 0.35, py - y - r * 0.35) <= r * 0.5] = A(metal["hi"])


def bevel(col, mask, metal, joint=True):
    d = inset(mask, 6)
    if joint:
        k = (d >= 3) & (d < 5)
        col[k] = col[k] * 0.55
    col[d < 3] = A(metal["hi"]) * 0.92
    return col


# ------------------------------------------------------------------ peaux des polyèdres
def peint_facette(ovo, f):
    est_tete = ovo is HEAD

    def painter(W, H):
        px, py = grid(W, H, f["w"], f["h"], 1)
        m = Image.new("L", (W * SS, H * SS), 0)
        d_ = W * SS / f["w"]
        ImageDraw.Draw(m).polygon([((a + f["w"] / 2) * d_, H * SS / 2 - b * d_) for a, b in f["poly"]], fill=255)
        m = m.filter(ImageFilter.MaxFilter(2 * max(1, int(round(0.03 * d_))) + 1))
        mask = down_mask(np.array(m, np.float32) / 255, W, H)
        P3 = f["cout"][None, None, :] + f["X"][None, None, :] * px[..., None] + f["Y"][None, None, :] * py[..., None]
        x, y, z = P3[..., 0], P3[..., 1], P3[..., 2]
        nr = ovo.normal(P3)
        nr = nr / np.linalg.norm(nr, axis=2, keepdims=True)
        lam = np.clip(nr @ LUM, 0, 1) * 0.85 + 0.15 * smv(y, -ovo.rv, ovo.rv)
        streak = noise(H, W, 14, zlib.crc32(f["name"].encode()) % 1000) - 0.5
        col = metal_shade(BRASS, lam, streak)
        poly = f["poly"]
        d_bas = seg_dist(px, py, [poly[0], poly[1]])
        d_haut = seg_dist(px, py, [poly[2], poly[3]])
        d_cote = np.minimum(seg_dist(px, py, [poly[1], poly[2]]), seg_dist(px, py, [poly[3], poly[0]]))
        facial = np.zeros(x.shape, bool)
        if est_tete:
            de = np.minimum(np.hypot(x - EX, y - EY), np.hypot(x + EX, y - EY))
            avant = z < -0.35
            facial = avant & (de < 1.08)
            rim = avant & (de >= 1.08) & (de < 1.26)
            # disque facial : laiton clair, plumes rayonnantes autour de chaque lentille
            ex = np.where(x > 0, EX, -EX)
            ang = np.degrees(np.arctan2(y - EY, x - ex))
            ray = (np.mod(ang, 15.0) < 4.5) & (de > 0.62)
            cf = lerp(A(BRASS["base"]), A(BRASS["hi"]), np.clip(0.35 + 0.55 * lam, 0, 1)[..., None])
            cf = np.where(ray[..., None], cf * 0.8, cf)
            col = np.where(facial[..., None], cf, col)
            col = np.where(rim[..., None], lerp(A(COPPER["low"]), A(COPPER["base"]), 0.5 * lam[..., None]), col)
        else:
            plastron = (z < -0.45) & (y < 1.05) & (y > -1.95) & (np.abs(x) < 1.55)
            col = np.where(plastron[..., None], lerp(A(COPPER["low"]), A(COPPER["base"]), (0.25 + 0.5 * lam)[..., None]), col)
        # joints de plaques : horizontaux appuyés (rivetés), verticaux discrets
        hj = np.minimum(d_bas, d_haut)
        joint = ~facial & (hj < 0.07)
        biseau = ~facial & (hj >= 0.07) & (hj < 0.15)
        col = np.where(biseau[..., None], lerp(col, A(BRASS["hi"]), 0.55), col)
        col = np.where(joint[..., None], A(BRASS["low"]) * 0.7, col)
        col = np.where((~facial & (d_cote < 0.045))[..., None], col * 0.72, col)
        # vert-de-gris dans les creux bas, en plaques nettes
        nz = noise(H, W, 9, 7 + zlib.crc32(f["name"].encode()) % 97)
        pat = ~facial & (nz > 0.90 - 0.12 * smv(-y, 0.0, ovo.rv)) & (hj < 0.22)
        col = np.where(pat[..., None], PATINA_D, col)
        # rivets le long du joint du bas
        for fr in (0.25, 0.75):
            a0 = np.array(poly[0]) + (np.array(poly[1]) - np.array(poly[0])) * fr
            a3 = np.array(poly[3]) + (np.array(poly[2]) - np.array(poly[3])) * fr
            q = a0 + (a3 - a0) * min(0.22, 0.26 / max(0.4, np.linalg.norm(a3 - a0)))
            p3 = f["cout"] + f["X"] * q[0] + f["Y"] * q[1]
            if est_tete:
                if min(math.hypot(p3[0] - EX, p3[1] - EY), math.hypot(p3[0] + EX, p3[1] - EY)) < 1.3 and p3[2] < -0.2:
                    continue
            rivet(col, px, py, q[0], q[1], 0.085, BRASS if est_tete else COPPER if (p3[2] < -0.45 and p3[1] < 1.05) else BRASS)
        return finish(col, mask)
    return painter


def peint_calotte(W, H):
    """Calotte octogonale du dessus de la tête (vue du dessus)."""
    r_ = HEAD.P(22.5, HEAD.lats[-1])
    R = math.hypot(r_[0], r_[2]) / math.cos(math.radians(22.5))
    w = 2 * R + 0.1
    px, py = grid(W, H, w, w, SS)
    ang = np.degrees(np.arctan2(py, px))
    rr = np.hypot(px, py) * np.cos(np.radians(np.mod(ang - 22.5, 45.0) - 22.5)) / math.cos(math.radians(22.5))
    mask = down_mask((rr < R * math.cos(math.radians(22.5)) + 0.05).astype(np.float32), W, H)
    px, py = grid(W, H, w, w, 1)
    r = np.hypot(px, py)
    streak = noise(H, W, 10, 31) - 0.5
    col = metal_shade(BRASS, np.clip(0.95 - 0.35 * r / R, 0, 1), streak)
    col = bevel(col, mask, BRASS)
    col[(r > 0.42) & (r < 0.5)] *= 0.6
    for a in range(8):
        aa = math.radians(a * 45 + 22.5)
        rivet(col, px, py, 0.72 * R * math.cos(aa), 0.72 * R * math.sin(aa), 0.085, BRASS)
    return finish(col, mask)


# ------------------------------------------------------------------ pièces découpées par alpha
def peint_metal(w, h, forme, metal, seed, rivets=(), r_riv=0.08, nervure=False, bout=None, patine=0.25, racine=False, lum=None, extra=None):
    """Plaque de métal : forme(px, py) -> bool en coordonnées modèle (x vers la droite de l'image, y vers le haut)."""
    def painter(W, H):
        gx, gy = grid(W, H, w, h, SS)
        mask = down_mask(forme(gx, gy).astype(np.float32), W, H)
        px, py = grid(W, H, w, h, 1)
        streak = noise(H, W, 12, seed) - 0.5
        l = lum(px, py) if lum else np.clip(0.55 + 0.4 * py / h + 0.1 * px / w, 0, 1)
        col = metal_shade(metal, l, streak)
        if bout is not None:
            x0, tm = bout
            band = px > x0
            col = np.where(band[..., None], metal_shade(tm, l, streak), col)
            col = np.where((band ^ (px > x0 - 0.06))[..., None], A(tm["low"]) * 0.7, col)
        if nervure:
            col = np.where((np.abs(py) < 0.05)[..., None], A(metal["low"]), col)
        if patine:
            nz = noise(H, W, 10, seed + 1)
            col = np.where((nz > 0.92 - patine * 0.12)[..., None], PATINA_D, col)
        col = bevel(col, mask, metal)
        if racine:
            col *= (0.55 + 0.45 * smv(px, -w / 2, -w / 2 + 0.6))[..., None]
        e = None
        if extra:
            col, e = extra(col, px, py, mask)
        for (rx, ry) in rivets:
            rivet(col, px, py, rx, ry, r_riv, STEEL if metal is not STEEL else BRASS)
        return finish(col, mask, e)
    return painter


def lame_forme(w, h, k_racine=0.62):
    """Lame : racine plus étroite, bout arrondi en demi-ellipse (pas de pointe fine)."""
    def f(px, py):
        u = (px + w / 2) / w
        hw = h / 2 * (k_racine + (1 - k_racine) * np.clip(u / 0.45, 0, 1))
        tip = px > w / 2 - h / 2
        ell = ((px - (w / 2 - h / 2)) / (h / 2)) ** 2 + (py / (h / 2)) ** 2 < 1
        return (np.abs(py) < hw) & (px > -w / 2) & (~tip | ell)
    return f


def ecaille_forme(w, h):
    def f(px, py):
        top = (py > 0) & (np.abs(px) < w / 2 - 0.02)
        ell = (px / (w / 2)) ** 2 + (py / (h / 2)) ** 2 < 1
        return (top | ell) & (py < h / 2 - 0.02)
    return f


def disque(rout, rin=0.0):
    def f(px, py):
        r = np.hypot(px, py)
        return (r < rout) & (r >= rin)
    return f


def strip(W, H, fn):
    u, v = np.meshgrid((np.arange(W) + 0.5) / W, (np.arange(H) + 0.5) / H)
    c = fn(u, v)
    return finish(c, np.ones(u.shape, bool))


def barre(metal, gorges=3):
    def fn(u, v):
        q = np.abs(v - 0.5) * 2
        c = lerp(A(metal["hi"]) * 0.9, A(metal["low"]), (q ** 1.2)[..., None])
        c = lerp(c, A(metal["base"]), 0.35)
        for k in range(gorges):
            c = np.where((np.abs(u - (k + 0.5) / gorges) < 0.03)[..., None], A(metal["low"]) * 0.8, c)
        return c
    return lambda W, H: strip(W, H, fn)


def plein(metal, k=0.7):
    return lambda W, H: strip(W, H, lambda u, v: lerp(A(metal["low"]), A(metal["base"]), k) * (1 - 0.1 * np.abs(v - 0.5))[..., None])


def bande_carenage(interieur=False):
    def fn(u, v):
        q = np.abs(v - 0.5) * 2
        c = lerp(A(COPPER["hi"]), A(COPPER["low"]), (q ** 1.4)[..., None])
        c = lerp(c, A(COPPER["base"]), 0.4)
        if interieur:
            return c * 0.55
        c = np.where(((v < 0.16) | (v > 0.84))[..., None], A(BRASS["base"]), c)
        c = np.where(((np.abs(v - 0.16) < 0.04) | (np.abs(v - 0.84) < 0.04))[..., None], A(BRASS["low"]) * 0.7, c)
        for x in (0.2, 0.5, 0.8):
            d = np.hypot((u - x) * 4.2, (v - 0.5))
            c = np.where((d < 0.16)[..., None], A(BRASS["low"]) * 0.6, c)
            c = np.where((d < 0.11)[..., None], A(BRASS["hi"]), c)
        return c
    return lambda W, H: strip(W, H, fn)


# ------------------------------------------------------------------ yeux
RING_D, GLASS_D = 1.5, 1.26
LID_TOP, LID_H0 = 0.68, 0.062           # paupière : mince lame logée sous la bague, agrandie par scale y depuis le haut
LID_FERME = 2 * LID_TOP / LID_H0


def peint_bague(W, H):
    R = RING_D / 2
    gx, gy = grid(W, H, RING_D, RING_D, SS)
    mask = down_mask(disque(R, R * 0.80)(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, RING_D, RING_D, 1)
    r = np.hypot(px, py)
    lam = np.clip(0.6 + 0.5 * (py - px) / RING_D, 0, 1)
    col = metal_shade(BRASS, lam, noise(H, W, 10, 401) - 0.5)
    col = np.where((np.abs(r - R * 0.90) < 0.018)[..., None], A(BRASS["low"]) * 0.7, col)
    col = bevel(col, mask, BRASS, joint=False)
    for a in range(6):
        aa = math.radians(a * 60 + 30)
        rivet(col, px, py, R * 0.90 * math.cos(aa), R * 0.90 * math.sin(aa), 0.05, STEEL)
    return finish(col, mask)


def peint_verre(W, H):
    R = GLASS_D / 2
    gx, gy = grid(W, H, GLASS_D, GLASS_D, SS)
    mask = down_mask(disque(R)(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, GLASS_D, GLASS_D, 1)
    r = np.hypot(px, py) / R
    col = lerp(AMBRE_C, AMBRE, smv(r, 0.2, 1.0)[..., None])
    col = lerp(col, A((150, 84, 26)), smv(r, 0.85, 1.0)[..., None])
    hl = np.hypot(px + 0.30, py - 0.30) < 0.09
    col = np.where(hl[..., None], A((255, 246, 220)), col)
    e = lerp(E_AMBRE, E_AMBRE * 0.55, smv(r, 0.3, 1.0)[..., None])
    e = np.where(hl[..., None], A((200, 170, 120)), e)
    return finish(col, mask, e)


def peint_pupille(W, H):
    gx, gy = grid(W, H, 0.5, 0.5, SS)
    mask = down_mask(disque(0.25)(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, 0.5, 0.5, 1)
    col = np.zeros(px.shape + (3,), np.float32) + A((26, 18, 14))
    col = np.where((np.hypot(px, py) > 0.19)[..., None], A((58, 36, 20)), col)
    return finish(col, mask)


def peint_iris(W, H):
    """Iris d'acier : anneau intérieur et 3 crans qui rentrent dans le verre (on voit leur rotation)."""
    R = GLASS_D / 2

    def f(px, py):
        r = np.hypot(px, py)
        a = np.mod(np.degrees(np.arctan2(py, px)), 120.0)
        cran = (np.abs(a - 60) < 9) & (r > 0.33)
        return (r < R) & ((r > 0.47) | cran)
    gx, gy = grid(W, H, GLASS_D, GLASS_D, SS)
    mask = down_mask(f(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, GLASS_D, GLASS_D, 1)
    lam = np.clip(0.55 + 0.6 * (py - px) / GLASS_D, 0, 1)
    col = metal_shade(STEEL, lam, noise(H, W, 8, 402) - 0.5)
    col = bevel(col, mask, STEEL, joint=False)
    return finish(col, mask)


def peint_paupiere(W, H):
    """Volet de laiton : peint pour la taille fermée (le scale y l'étire depuis la lame logée sous la bague)."""
    R = GLASS_D / 2 + 0.02
    gx, gy = grid(W, H, 2 * R, 2 * R, SS)
    mask = down_mask(disque(R)(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, 2 * R, 2 * R, 1)
    col = metal_shade(BRASS, np.clip(0.75 + 0.3 * py, 0, 1), noise(H, W, 8, 403) - 0.5)
    for k in range(-2, 3):
        col = np.where((np.abs(py - k * 0.25 - 0.12) < 0.025)[..., None], A(BRASS["low"]) * 0.75, col)
    col = bevel(col, mask, BRASS, joint=False)
    return finish(col, mask)


# ------------------------------------------------------------------ clé, hélice, vapeur
KEY_W, KEY_H = 2.3, 1.15


def cle_forme(px, py):
    lob = np.zeros(px.shape, bool)
    for s in (-1, 1):
        d = np.hypot((px - s * 0.62) / 0.53, py / 0.55)
        trou = np.hypot((px - s * 0.66) / 0.22, py / 0.22) < 1
        lob |= (d < 1) & ~trou
    centre = (np.abs(px) < 0.32) & (np.abs(py) < 0.30)
    return lob | centre


def peint_cle(W, H):
    def extra(col, px, py, mask):
        col = np.where((np.hypot(px, py) < 0.17)[..., None], A(BRASS["low"]) * 0.8, col)
        return col, None
    return peint_metal(KEY_W, KEY_H, cle_forme, BRASS, 501, rivets=[(0.0, 0.0)], r_riv=0.1, patine=0.2,
                       lum=lambda px, py: np.clip(0.6 + 0.45 * py - 0.1 * px, 0, 1), extra=extra)(W, H)


PROP_D = 2.3


def peint_helice(W, H):
    R = PROP_D / 2

    def f(px, py):
        r = np.hypot(px, py)
        a = np.degrees(np.arctan2(py, px))
        pale = np.zeros(px.shape, bool)
        for k in range(3):
            da = (a - k * 120 - 12 * (r / R) + 180) % 360 - 180            # pales légèrement vrillées
            pale |= np.abs(da) < (14 + 18 * np.sin(np.clip(r / R, 0, 1) * math.pi) ** 0.8)
        return ((r < R) & pale & (r > 0.16)) | (r < 0.3)
    gx, gy = grid(W, H, PROP_D, PROP_D, SS)
    mask = down_mask(f(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, PROP_D, PROP_D, 1)
    r = np.hypot(px, py)
    col = metal_shade(STEEL, np.clip(0.4 + 0.5 * r / R, 0, 1), noise(H, W, 8, 502) - 0.5)
    col = np.where((r < 0.3)[..., None], metal_shade(BRASS, np.full(r.shape, 0.7), np.zeros(r.shape)), col)
    col = bevel(col, mask, STEEL, joint=False)
    return finish(col, mask)


VAP_W, VAP_H = 1.3, 1.8


def peint_vapeur(W, H):
    """Bouffée : bosses à bord net, opacité qui décroît vers le haut (trans_ ; la moitié opaque se lit en cutout)."""
    px, py = grid(W, H, VAP_W, VAP_H, 1)
    u, v = px / VAP_W + 0.5, py / VAP_H + 0.5
    dens = np.zeros(px.shape, np.float32)
    light = np.zeros(px.shape, np.float32)
    for x, y, r in ((0.5, 0.20, 0.20), (0.36, 0.40, 0.22), (0.64, 0.46, 0.21), (0.48, 0.64, 0.24), (0.58, 0.84, 0.15), (0.32, 0.78, 0.13)):
        d = np.hypot((u - x) * VAP_W, (v - y) * VAP_H) / (r * VAP_W)
        dens = np.maximum(dens, np.clip(1.6 * (1 - d), 0, 1))
        light = np.maximum(light, np.clip(1 - np.hypot((u - x + 0.25 * r) * VAP_W, (v - y - 0.3 * r) * VAP_H) / (r * VAP_W), 0, 1))
    alpha = np.clip(dens, 0, 1) * lerp(1.0, 0.25, smv(v, 0.15, 1.0))
    alpha = np.where(alpha < 0.08, 0.0, alpha)
    col = np.zeros(px.shape + (3,), np.float32) + A((214, 220, 226))
    col = np.where((light > 0.2)[..., None], A((236, 240, 244)), col)
    col = np.where((light > 0.5)[..., None], A((250, 250, 248)), col)
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = col.astype(np.uint8)
    out[..., 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    return out, np.zeros((H, W, 4), np.uint8)


# ------------------------------------------------------------------ atlas
TILES = {}


def tile(name, w, h, painter, fixed=False):
    TILES[name] = (w, h, painter, fixed)


for ovo in (BODY, HEAD):
    for f in ovo.facets:
        tile(f["name"], f["w"], f["h"], peint_facette(ovo, f))
_cr = HEAD.P(22.5, HEAD.lats[-1])
CAP_R = math.hypot(_cr[0], _cr[2]) / math.cos(math.radians(22.5))
tile("calotte", 2 * CAP_R + 0.1, 2 * CAP_R + 0.1, peint_calotte)
tile("bague", RING_D, RING_D, peint_bague)
tile("verre", GLASS_D, GLASS_D, peint_verre)
tile("pupille", 0.5, 0.5, peint_pupille)
tile("iris", GLASS_D, GLASS_D, peint_iris)
tile("paupiere", GLASS_D + 0.04, GLASS_D + 0.04, peint_paupiere)
ECW, ECH = 0.92, 1.0
tile("ecaille_a", ECW, ECH, peint_metal(ECW, ECH, ecaille_forme(ECW, ECH), COPPER, 301, rivets=[(0, 0.3)], r_riv=0.07, nervure=False, patine=0.3,
                                         lum=lambda px, py: np.clip(0.35 + 0.65 * (0.5 - py), 0, 1)))
tile("ecaille_b", ECW, ECH, peint_metal(ECW, ECH, ecaille_forme(ECW, ECH), COPPER, 302, rivets=[(0, 0.3)], r_riv=0.07, patine=0.5,
                                         lum=lambda px, py: np.clip(0.30 + 0.7 * (0.5 - py), 0, 1)))
WINGS = [(2.9, 0.95, 4.0), (2.5, 0.86, 22.0), (2.1, 0.78, 40.0)]       # longueur, largeur, angle d'éventail (vers l'arrière)
for i, (Lb, Wb, _) in enumerate(WINGS):
    tile(f"lame{i}", Lb, Wb, peint_metal(Lb, Wb, lame_forme(Lb, Wb), BRASS if i != 1 else COPPER, 311 + i,
                                         rivets=[(-Lb / 2 + 0.3, 0.0), (-Lb / 2 + 0.75, 0.0)], nervure=True, bout=(Lb / 2 - 0.55, COPPER if i != 1 else BRASS),
                                         racine=True, patine=0.3))
TAILS = [(1.9, 0.68, -24.0), (2.3, 0.78, 0.0), (1.9, 0.68, 24.0)]
tile("queue_c", 2.3, 0.78, peint_metal(2.3, 0.78, lame_forme(2.3, 0.78), BRASS, 321, rivets=[(-0.8, 0)], nervure=True, bout=(0.65, COPPER), racine=True))
tile("queue_s", 1.9, 0.68, peint_metal(1.9, 0.68, lame_forme(1.9, 0.68), COPPER, 322, rivets=[(-0.6, 0)], nervure=True, bout=(0.45, BRASS), racine=True))
TUFTS = [(1.45, 0.52), (1.05, 0.44)]
for i, (Lt, Wt) in enumerate(TUFTS):
    tile(f"aigrette{i}", Lt, Wt, peint_metal(Lt, Wt, lame_forme(Lt, Wt, 0.75), BRASS, 331 + i, nervure=True, bout=(Lt / 2 - 0.35, COPPER), racine=True, patine=0.1))
tile("moyeu", 1.0, 1.0, peint_metal(1.0, 1.0, lambda px, py: (np.hypot(px, py) < 0.48) & ((np.hypot(px, py) < 0.36) | (np.mod(np.degrees(np.arctan2(py, px)), 45) < 24)),
                                    BRASS, 341, rivets=[(0, 0)], r_riv=0.1, patine=0.1, lum=lambda px, py: np.clip(0.6 + 0.5 * (py - px), 0, 1)))
tile("bec", 0.56, 0.78, peint_metal(0.56, 0.78, lambda px, py: (np.abs(px) < 0.27 * np.clip((py + 0.40) / 0.55, 0.12, 1.0)) & (py < 0.37),
                                    STEEL, 351, patine=0.0, lum=lambda px, py: np.clip(0.75 + 0.3 * py - 0.4 * np.abs(px), 0, 1)))
tile("collier", 0.9, 0.9, peint_metal(0.9, 0.9, disque(0.44), COPPER, 361, rivets=[(0.27, 0), (-0.27, 0), (0, 0.27), (0, -0.27)], r_riv=0.06, patine=0.3))
tile("cle", KEY_W, KEY_H, peint_cle)
tile("helice", PROP_D, PROP_D, peint_helice)
tile("disque", 1.9, 1.9, peint_metal(1.9, 1.9, disque(0.94), BRASS, 371, rivets=[(0.62 * math.cos(a * TAU / 6), 0.62 * math.sin(a * TAU / 6)) for a in range(6)],
                                     patine=0.3, lum=lambda px, py: np.clip(0.75 - 0.2 * np.hypot(px, py), 0, 1)))
tile("vapeur", VAP_W, VAP_H, peint_vapeur)
HUB_D = 0.95


def peint_hublot(W, H):
    """Hublot du foyer : bague de laiton, grille de 3 barreaux, braises derrière (calque _e vif, petite surface)."""
    R_ = HUB_D / 2
    gx, gy = grid(W, H, HUB_D, HUB_D, SS)
    mask = down_mask(disque(R_)(gx, gy).astype(np.float32), W, H)
    px, py = grid(W, H, HUB_D, HUB_D, 1)
    r = np.hypot(px, py)
    rng_ = np.random.default_rng(77)
    braise = noise(H, W, 6, 78)
    col = lerp(A((70, 22, 8)), A((235, 120, 36)), np.clip(braise * 1.3 - 0.15 + 0.3 * smv(-py, -0.3, 0.3), 0, 1)[..., None])
    e = lerp(A((120, 40, 10)), A((220, 150, 60)), np.clip(braise * 1.4 - 0.2 + 0.3 * smv(-py, -0.3, 0.3), 0, 1)[..., None])
    barreau = (np.abs(np.abs(px) - 0.15) < 0.035) | (np.abs(px) < 0.035)
    anneau = r > R_ * 0.74
    col = np.where(barreau[..., None], metal_shade(BRASS, np.clip(0.6 + py, 0, 1), np.zeros(r.shape)), col)
    col = np.where(anneau[..., None], metal_shade(BRASS, np.clip(0.55 + 0.6 * py, 0, 1), noise(H, W, 6, 79) - 0.5), col)
    col = np.where((np.abs(r - R_ * 0.74) < 0.03)[..., None], A(BRASS["low"]) * 0.6, col)
    col = bevel(col, mask, BRASS, joint=False)
    e = np.where((barreau | anneau | (r > R_ * 0.70))[..., None], 0.0, e)
    for a in range(6):
        aa = math.radians(a * 60)
        rivet(col, px, py, R_ * 0.87 * math.cos(aa), R_ * 0.87 * math.sin(aa), 0.045, STEEL)
    return finish(col, mask, e)


def peint_lampe(W, H):
    """Lampe de pression : verre ambre bombé dans une cage (calque _e vif, petite surface)."""
    px, py = grid(W, H, 0.42, 0.42, 1)
    r = np.hypot(px, py) / 0.21
    col = lerp(A((255, 226, 150)), A((214, 120, 36)), smv(r, 0.1, 1.0)[..., None])
    e = lerp(A((230, 190, 110)), A((170, 90, 24)), smv(r, 0.1, 1.0)[..., None])
    cage = (np.abs(px) < 0.025) | (np.abs(py) < 0.025) | (r > 0.86)
    col = np.where(cage[..., None], A(BRASS["low"]), col)
    e = np.where(cage[..., None], 0.0, e)
    return finish(col, np.ones(px.shape, bool), e)


tile("hublot", HUB_D, HUB_D, peint_hublot)
tile("lampe", 0.42, 0.42, peint_lampe)
tile("bar_laiton", 48, 12, barre(BRASS), fixed=True)
tile("bar_acier", 48, 12, barre(STEEL, 4), fixed=True)
tile("bar_cuivre", 48, 12, barre(COPPER, 2), fixed=True)
tile("carenage", 64, 22, bande_carenage(), fixed=True)
tile("carenage_in", 64, 22, bande_carenage(True), fixed=True)
tile("rebord", 64, 8, barre(BRASS, 5), fixed=True)
tile("ame", 12, 12, plein(BRASS, 0.55), fixed=True)
tile("ame_acier", 12, 12, plein(STEEL, 0.8), fixed=True)
tile("cou", 48, 16, lambda W, H: strip(W, H, lambda u, v: np.where((np.mod(v * 4, 1) < 0.3)[..., None], A(STEEL["low"]), lerp(A(STEEL["base"]), A(STEEL["hi"]), 0.3) + 0 * u[..., None])), fixed=True)
tile("chapeau", 16, 16, lambda W, H: strip(W, H, lambda u, v: lerp(A(BRASS["hi"]), A(BRASS["low"]), np.clip(np.hypot(u - 0.4, v - 0.4) * 1.6, 0, 1)[..., None])), fixed=True)
tile("tube_fond", 12, 12, plein(STEEL, 0.2), fixed=True)

UV = {}
CLEAR = [TEX - 4, TEX - 4, TEX - 2, TEX - 2]


def atlas():
    def pack(dens):
        items = [(n, w, h) if fx else (n, int(math.ceil(w * dens)), int(math.ceil(h * dens))) for n, (w, h, _, fx) in TILES.items()]
        items.sort(key=lambda it: -it[2])
        uv, x, y, shelf = {}, 0, 0, 0
        for n, w, h in items:
            if x + w + 1 > TEX:
                x, y, shelf = 0, y + shelf + 1, 0
            if y + h > TEX - 6:
                return None
            uv[n] = (x, y, x + w, y + h)
            x += w + 1
            shelf = max(shelf, h)
        return uv

    dens = 56.0
    while (uv := pack(dens)) is None:
        dens -= 0.5
    UV.update(uv)
    tex, tex_e = np.zeros((TEX, TEX, 4), np.uint8), np.zeros((TEX, TEX, 4), np.uint8)
    for n, (w, h, painter, fx) in TILES.items():
        u0, v0, u1, v1 = UV[n]
        im, ie = painter(u1 - u0, v1 - v0)
        tex[v0:v1, u0:u1] = im
        tex_e[v0:v1, u0:u1] = ie
    assert tex[TEX - 3, TEX - 3, 3] == 0
    tex[..., :3] &= 0xFE
    semi = (tex[..., 3] > 0) & (tex[..., 3] < 255)
    u0, v0, u1, v1 = UV["vapeur"]
    semi[v0:v1, u0:u1] = False
    assert not semi.any() and set(np.unique(tex_e[..., 3])) <= {0, 255}, "semi-transparence hors de la vapeur (trans_)"
    b64 = []
    for arr, fn in ((tex, f"{NOM}.png"), (tex_e, f"{NOM}_e.png")):
        im = Image.fromarray(arr, "RGBA")
        im.save(fn, optimize=True)
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        b64.append("data:image/png;base64," + base64.b64encode(b.getvalue()).decode())
    return dens, b64


DENS, (tex_b64, tex_e_b64) = atlas()

# ------------------------------------------------------------------ cubes et groupes
elements, groups = [], {}


def nuid():
    return str(_uuid.uuid4())


def rot_matrix(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def euler(R):
    """Angles (X, Y, Z) en degrés tels que R = Rz Ry Rx (ordre du mod et du renderer)."""
    sy = -R[2, 0]
    if abs(sy) > 0.99999:
        ry = math.copysign(math.pi / 2, sy)
        ang = (math.degrees(math.atan2(R[0, 1], R[0, 2])) if sy > 0 else math.degrees(math.atan2(-R[0, 1], -R[0, 2]))), math.degrees(ry), 0.0
    else:
        ang = math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(math.asin(sy)), math.degrees(math.atan2(R[1, 0], R[0, 0]))
    assert np.allclose(rot_matrix(*ang), R, atol=1e-4), "euler : reconstruction fausse"
    return ang


def group(name, origin, parent=None, rotation=(0, 0, 0), uniq=None):
    """uniq : plusieurs groupes de même nom (emit_mc_, ctrl_) ; la clé interne est alors « nom#uniq »."""
    key = name if uniq is None else f"{name}#{uniq}"
    assert key not in groups
    groups[key] = {"name": name, "origin": [round(float(v), 3) for v in origin], "uuid": nuid(), "ids": [], "parent": parent, "rotation": [round(float(v), 2) for v in rotation]}
    return key


def cube(g, name, frm, to, origin, rot, faces):
    e = {"name": name, "type": "cube", "uuid": nuid(), "from": [round(float(v), 3) for v in frm], "to": [round(float(v), 3) for v in to],
         "origin": [round(float(v), 3) for v in origin], "box_uv": False,
         "faces": {f: {"uv": [round(float(v), 2) for v in uv], "texture": 0} for f, uv in faces.items()}}
    if any(abs(r) > 1e-3 for r in rot):
        e["rotation"] = [round(float(v), 2) for v in rot]
    elements.append(e)
    groups[g]["ids"].append(e["uuid"])


def plate(g, name, c, X, Y, tilename, w, h, th=TH, side="s", tranche=None):
    """Plaque fine (coordonnées absolues du modèle) : contour par l'alpha, tranches transparentes.
    side : 's' face X x Y seule, 'n' face opposée seule, 'b' les deux. tranche : tuile des faces up/down (rebord visible)."""
    X = unit(X)
    Y = unit(np.asarray(Y, float) - (np.asarray(Y, float) @ X) * X)
    u0, v0, u1, v1 = UV[tilename]
    R_ = np.column_stack([X, Y, np.cross(X, Y)])
    c = np.asarray(c, float)
    south = [u0, v0, u1, v1] if side in "sb" else CLEAR
    north = [u1, v0, u0, v1] if side in "nb" else CLEAR
    ud = list(UV[tranche]) if tranche else CLEAR
    cube(g, name, c - (w / 2, h / 2, th / 2), c + (w / 2, h / 2, th / 2), c, euler(R_),
         {"south": south, "north": north, "east": CLEAR, "west": CLEAR, "up": ud, "down": ud})


def frame_from_axis(X):
    ref = V(0, 1, 0) if abs(X[1]) < 0.9 else V(1, 0, 0)
    Y = unit(ref - (ref @ X) * X)
    return Y, np.cross(X, Y)


def bar(g, name, p, q, r, tilename, octo=True, ov=0.04, bouts=None):
    """Tronçon plein de section octogonale (deux cubes à 45°) ou carrée, de p à q (coordonnées absolues)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    Ln = np.linalg.norm(q - p)
    X = unit(q - p)
    Y, Z_ = frame_from_axis(X)
    c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
    R0 = np.column_stack([X, Y, Z_])
    R45 = np.column_stack([X, c * Y + s * Z_, -s * Y + c * Z_])
    lg = list(UV[tilename])
    end = list(UV[bouts]) if bouts else [lg[0], lg[1], lg[0] + 6, lg[3]]
    faces = {"south": lg, "north": lg, "up": lg, "down": lg, "east": end, "west": end}
    cube(g, name, p + (-ov, -r, -r), p + (Ln + ov, r, r), p, euler(R0), faces)
    if octo:
        cube(g, name + "o", p + (-ov + 0.03, -r * 0.97, -r * 0.97), p + (Ln + ov - 0.03, r * 0.97, r * 0.97), p, euler(R45), faces)


def bloc(g, name, c, size, R_, tilename, faces_tile=None):
    """Cube plein orienté (repère R_ en colonnes), même tuile sur les 6 faces."""
    c = np.asarray(c, float)
    hs = np.asarray(size, float) / 2
    t = list(UV[tilename])
    faces = {f: t for f in ("north", "south", "east", "west", "up", "down")}
    if faces_tile:
        faces.update({k: (list(UV[v]) if v else CLEAR) for k, v in faces_tile.items()})
    cube(g, name, c - hs, c + hs, c, euler(R_), faces)


def prisme_y(g, name, cy, y0, y1, a, tilename, top=None, bottom=None):
    """Prisme octogonal vertical (deux cubes, 0° et 45°), centré sur l'axe du corps."""
    for i, (k, ang) in enumerate(((1.0, 0.0), (0.97, 45.0))):
        d = 0.03 * i
        faces = {f: list(UV[tilename]) for f in ("north", "south", "east", "west")}
        faces["up"] = list(UV[top]) if top else list(UV[tilename])
        faces["down"] = list(UV[bottom]) if bottom else list(UV[tilename])
        c = cy + V(0, (y0 + y1) / 2, 0)
        cube(g, f"{name}{'o' if i else ''}", cy + V(-a * k, y0 + d, -a * k), cy + V(a * k, y1 - d, a * k), c, (0, ang, 0), faces)


def ame_max(ovo, y0, y1, marge=0.06):
    def ok(a):
        for ang in (0.0, 45.0):
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            for sx in (-a, a):
                for sz in (-a, a):
                    for yy in (y0, y1):
                        q = V(sx * ca + sz * sa, yy, -sx * sa + sz * ca)
                        if max(f["n"] @ q - f["n"] @ f["cout"] for f in ovo.facets) > -marge:
                            return False
        return True
    a = 0.2
    while ok(a + 0.02):
        a += 0.02
    return a


def bone_node(name):
    g = groups[name]
    return {"name": g["name"], "origin": g["origin"], "uuid": g["uuid"], "rotation": g["rotation"],
            "children": list(g["ids"]) + [bone_node(n) for n, gg in groups.items() if gg["parent"] == name]}


HC = C0 + V(0, HY, 0)          # centre de la tête (absolu)
g_elan = group("fam_elan", [0, 24, 0])
g_inert = group("fam_inertie", V(0, C0[1], 0), parent=g_elan)
g_orb = group("fam_orbite", V(0, C0[1], 0), parent=g_inert)
g_pos = group("fam_pos", C0, parent=g_orb)
g_vir = group("fam_virage", C0, parent=g_pos)
g_reg = group("fam_regard", C0, parent=g_vir)
g_snap = group("fam_snap", C0, parent=g_reg)
g_corps = group("corps", C0, parent=g_snap)

# --- corps : peaux, âmes, cou
for f in BODY.facets:
    plate(g_corps, f["name"], C0 + f["cout"] - f["n"] * TH / 2, f["X"], f["Y"], f["name"], f["w"], f["h"])
prisme_y(g_corps, "ame_c1", C0, -1.75, -0.45, ame_max(BODY, -1.75, -0.45), "ame")
prisme_y(g_corps, "ame_c2", C0, -0.55, 1.35, ame_max(BODY, -0.55, 1.35), "ame")
prisme_y(g_corps, "cou", C0, 1.05, 2.55, 1.06, "cou", top="ame_acier", bottom="ame_acier")

# plastron : écailles de cuivre, chaque rang recouvre celui du dessous
SCALES = [(14.0, (-21.0, 21.0), 0.22, 1.0), (-8.0, (-40.0, 0.0, 40.0), 0.15, 1.0), (-30.0, (-21.0, 21.0), 0.09, 0.92)]
for r_, (lat, phis, off, k) in enumerate(SCALES):
    for i, phi in enumerate(phis):
        p = BODY.P(phi, lat)
        n = unit(BODY.normal(p))
        T = unit(V(0, 1, 0) - (V(0, 1, 0) @ n) * n)
        T = unit(T - n * 0.22)                        # le bas de l'écaille se soulève : on lit le recouvrement
        X = np.cross(T, n)
        nn = np.cross(X, T)
        plate(g_corps, f"ecaille_{r_}_{i}", C0 + p + nn * (off + 0.15) - T * 0.18, X, T, "ecaille_a" if (r_ + i) % 2 else "ecaille_b", ECW * k, ECH * k, th=0.3)

# carénage et hélice sous le corps
Y_POLE = BODY.P(0, BODY.lats[0])[1]
R_POLE = math.hypot(*BODY.P(0, BODY.lats[0])[[0, 2]])
DUCT_Y, DUCT_R, DUCT_H = -2.62, 1.34, 0.6
plate(g_corps, "disque", C0 + V(0, Y_POLE - 0.07, 0), V(1, 0, 0), V(0, 0, -1), "disque", 1.9, 1.9, th=0.22, side="b")
for k in range(8):
    a = math.radians(k * 45 + 22.5)
    dr, dy = (0.03, -0.03) if k % 2 else (0.0, 0.0)
    nrm = V(math.sin(a), 0, -math.cos(a))
    X = V(-math.cos(a), 0, -math.sin(a))
    plate(g_corps, f"carenage{k}", C0 + V(0, DUCT_Y + dy, 0) + nrm * (DUCT_R + dr), X, V(0, 1, 0), "carenage", 2 * DUCT_R * math.tan(math.radians(22.5)) + 0.06, DUCT_H, th=0.22,
          side="s", tranche="rebord")
    # face intérieure sombre : même cube, face nord (vue de l'intérieur du carénage)
    elements[-1]["faces"]["north"] = {"uv": [round(float(v), 2) for v in [UV["carenage_in"][2], UV["carenage_in"][1], UV["carenage_in"][0], UV["carenage_in"][3]]], "texture": 0}
for s in (-1, 1):
    bar(g_corps, f"bras_carenage_{'r' if s > 0 else 'l'}", C0 + V(s * 0.72, Y_POLE - 0.1, 0), C0 + V(s * (DUCT_R - 0.05), DUCT_Y + DUCT_H / 2 - 0.05, 0), 0.11, "bar_acier", octo=False)
bar(g_corps, "axe_rotor", C0 + V(0, Y_POLE - 0.1, 0), C0 + V(0, DUCT_Y - 0.12, 0), 0.17, "bar_acier", bouts="chapeau")
g_rot = group("rotor", C0 + V(0, DUCT_Y, 0), parent=g_corps)
plate(g_rot, "helice", C0 + V(0, DUCT_Y, 0), V(1, 0, 0), V(0, 0, -1), "helice", PROP_D, PROP_D, th=0.16, side="b")
# souffle du rotor : 3 points de particules sous l'hélice, +Y du groupe vers le bas (rotation X = 180), qui tournent avec elle
for k in range(3):
    a = math.radians(k * 120 + 30)
    group("emit_mc_white_ash", C0 + V(0.72 * math.cos(a), DUCT_Y - 0.32, 0.72 * math.sin(a)), parent=g_rot, rotation=(180, 0, 0), uniq=k)

# foyer : hublot à grille au bas du ventre (sous le plastron) et lampe de pression au dos, au-dessus de la clé ;
# leur ctrl_lumiere suit la vitesse du rotor (plus de vapeur, plus de feu)
g_foyer = group("foyer", C0, parent=g_corps)
g_ctrl_l = group("ctrl_lumiere", C0, parent=g_foyer, uniq="foyer")
_ph = BODY.P(0.0, -46.0)
_nh = unit(BODY.normal(_ph))
_Th = unit(V(0, 1, 0) - (V(0, 1, 0) @ _nh) * _nh)
plate(g_foyer, "hublot", C0 + _ph + _nh * 0.08, np.cross(_Th, _nh), _Th, "hublot", HUB_D, HUB_D, th=0.24, side="s")
_pl = BODY.P(180.0, 30.0)
bloc(g_foyer, "lampe", C0 + _pl + V(0, 0, 0.12), (0.42, 0.42, 0.34), np.eye(3), "bar_laiton", {"south": "lampe"})

# --- tête
g_suivi = group("tete_suivi", C0 + V(0, NECK_Y, 0), parent=g_corps)
g_tete = group("tete", C0 + V(0, NECK_Y, 0), parent=g_suivi)
for f in HEAD.facets:
    plate(g_tete, f["name"], HC + f["cout"] - f["n"] * TH / 2, f["X"], f["Y"], f["name"], f["w"], f["h"])
Y_CAP = HEAD.P(0, HEAD.lats[-1])[1]
plate(g_tete, "calotte", HC + V(0, Y_CAP - 0.1, 0), V(1, 0, 0), V(0, 0, -1), "calotte", 2 * CAP_R + 0.1, 2 * CAP_R + 0.1, th=0.2, side="s")
prisme_y(g_tete, "ame_t", HC, -0.9, 0.95, ame_max(HEAD, -0.9, 0.95), "ame")

# bec : plaque d'acier + âme
BEC = HC + V(0, EY - 0.62, -1.86)
Rb = rot_matrix(-14, 180, 0)
plate(g_tete, "bec", BEC, Rb[:, 0], Rb[:, 1], "bec", 0.56, 0.78, th=0.3, side="s")
bloc(g_tete, "bec_ame", BEC + V(0, 0.08, 0.2), (0.3, 0.5, 0.36), rot_matrix(-14, 0, 0), "bar_acier")

# yeux : groupe de base tourné pour que son -Z local soit l'axe de la lentille ; pièces construites axe = -Z
EYEG = {}
for tag, ey in EYES.items():
    E = HC + ey["c"]
    Zl = -ey["axe"]
    Xl = unit(np.cross(V(0, 1, 0), Zl))
    Yl = np.cross(Zl, Xl)
    g_e = group(f"oeil_{tag}", E, parent=g_tete, rotation=euler(np.column_stack([Xl, Yl, Zl])))
    R_av = rot_matrix(0, 180, 0)                    # face visible vers -Z
    Xf, Yf = R_av[:, 0], R_av[:, 1]
    a = 0.70
    for i, (k, ang) in enumerate(((1.0, 0.0), (0.97, 45.0))):
        side = list(UV["bar_acier"])
        cube(g_e, f"tube_{tag}{'o' if i else ''}", E + V(-a * k, -a * k, -0.47 + 0.03 * i), E + V(a * k, a * k, 0.45 - 0.03 * i), E, (0, 0, ang),
             {"north": CLEAR, "south": CLEAR, "east": side, "west": side, "up": side, "down": side})
    plate(g_e, f"verre_{tag}", E + V(0, 0, -0.02), Xf, Yf, "verre", GLASS_D, GLASS_D, th=0.2, side="s")
    gp = group(f"pupille_{tag}", E + V(0, 0, -0.18), parent=g_e)
    plate(gp, f"pupille_{tag}", E + V(0, 0, -0.18), Xf, Yf, "pupille", 0.5, 0.5, th=0.1, side="s")
    gi = group(f"iris_{tag}", E + V(0, 0, -0.28), parent=g_e)
    plate(gi, f"iris_{tag}", E + V(0, 0, -0.28), Xf, Yf, "iris", GLASS_D, GLASS_D, th=0.1, side="s")
    gl = group(f"paupiere_{tag}", E + V(0, LID_TOP, -0.38), parent=g_e)
    plate(gl, f"paupiere_{tag}", E + V(0, LID_TOP - LID_H0 / 2, -0.38), Xf, Yf, "paupiere", GLASS_D + 0.04, LID_H0, th=0.1, side="s")
    plate(g_e, f"bague_{tag}", E + V(0, 0, -0.55), Xf, Yf, "bague", RING_D, RING_D, th=0.18, side="b")
    EYEG[tag] = dict(oeil=g_e, pupille=gp, iris=gi, paupiere=gl)

# aigrettes : deux lames par côté, nervure pleine
TUFTG = {}
for s, tag in ((1, "r"), (-1, "l")):
    base = HC + HEAD.P(s * 40.0, 44.0, 0.96)
    g_a = group(f"aigrette_{tag}", base, parent=g_tete)
    TUFTG[tag] = g_a
    for i, ((Lt, Wt), dvec, back) in enumerate(zip(TUFTS, (V(s * 0.42, 1.0, 0.22), V(s * 0.95, 0.85, 0.42)), (0.0, 0.16))):
        d = unit(dvec)
        Y_ = unit(np.cross(V(0, 0, -1), d))
        if Y_ @ V(0, 1, 0) < 0 and abs(d[0]) > 0.5:
            Y_ = -Y_
        n = np.cross(d, Y_)
        c = base + d * (Lt / 2 - 0.2) + V(0, 0, back)
        plate(g_a, f"aigrette_{tag}{i}", c, d, Y_, f"aigrette{i}", Lt, Wt, th=0.22, side="b")
        bloc(g_a, f"aigrette_{tag}{i}_n", base + d * (Lt * 0.4 - 0.2) + V(0, 0, back), (Lt * 0.62, 0.14, 0.3), np.column_stack([d, Y_, n]), "bar_laiton")

# soupape sur la tête, vapeur
VALVE = HC + V(0.0, Y_CAP - 0.05, 0.52)
g_sp = group("soupape", VALVE, parent=g_tete)
bar(g_sp, "soupape_tuyau", VALVE, VALVE + V(0, 0.5, 0), 0.16, "bar_cuivre", bouts="chapeau")
g_spc = group("soupape_cap", VALVE + V(0, 0.5, 0), parent=g_sp)
bloc(g_spc, "soupape_chapeau", VALVE + V(0, 0.62, 0), (0.48, 0.2, 0.48), np.eye(3), "bar_laiton", {"up": "chapeau", "down": "chapeau"})
g_emit = group("emit_mc_white_smoke", VALVE + V(0, 0.78, 0), parent=g_spc)
g_vap = group("trans_vapeur", VALVE + V(0, 0.74, 0), parent=g_tete)
VAP_K = 0.02          # bouffée modélisée à 2 % : invisible sans animation (attack, hurt, aperçus) ; les états l'agrandissent (scale / VAP_K)
plate(g_vap, "vapeur_a", VALVE + V(0, 0.74 + VAP_K * VAP_H / 2, 0), V(1, 0, 0), V(0, 1, 0), "vapeur", VAP_K * VAP_W, VAP_K * VAP_H, th=VAP_K * 0.12, side="b")
plate(g_vap, "vapeur_b", VALVE + V(VAP_K * 0.02, 0.74 + VAP_K * (VAP_H / 2 + 0.03), 0), V(0, 0, 1), V(0, 1, 0), "vapeur", VAP_K * VAP_W, VAP_K * VAP_H, th=VAP_K * 0.12, side="b")

# --- ailes repliées : 3 lames par aile, chacune dans son groupe (éventail), moyeu à l'épaule
WINGG = {}
for s, tag in ((1, "r"), (-1, "l")):
    SH = C0 + V(s * 1.52, 0.92, 0.32)
    g_w = group(f"aile_{tag}", SH, parent=g_corps)
    WINGG[tag] = [g_w]
    Rt = rot_matrix(0, 0, s * 9.0)
    for i, (Lb, Wb, fan) in enumerate(WINGS):
        g_l = group(f"lame_{tag}{i}", SH, parent=g_w)
        WINGG[tag].append(g_l)
        R_ = Rt @ rot_matrix(-fan, 0, 0)
        d = R_ @ V(0, -1, 0)
        w_ = R_ @ V(0, 0, 1)
        Y_ = -w_
        n = np.cross(d, Y_)
        if n @ V(s, 0, 0) < 0:
            n = -n
        off = 0.14 + 0.10 * (len(WINGS) - 1 - i)
        c = SH + d * (Lb / 2 - 0.25) + n * off
        plate(g_l, f"lame_{tag}{i}", c, d, Y_, f"lame{i}", Lb, Wb, th=0.22, side="b")
        bloc(g_l, f"lame_{tag}{i}_n", SH + d * (Lb * 0.42 - 0.25) + n * off, (Lb * 0.7, 0.16, 0.34), np.column_stack([d, Y_, np.cross(d, Y_)]), "bar_laiton")
    plate(g_w, f"moyeu_{tag}", SH + V(s, 0, 0) * (0.14 + 0.10 * len(WINGS) + 0.04), V(0, 0, -s), V(0, 1, 0), "moyeu", 1.0, 1.0, th=0.24, side="b")

# --- queue en éventail
TQ = C0 + V(0, -1.25, 1.32)
d0 = unit(V(0, -0.55, 1.0))
nt = unit(np.cross(d0, V(1, 0, 0)))
g_q = group("queue", TQ, parent=g_corps)
g_ql = group("queue_l", TQ, parent=g_q)
g_qr = group("queue_r", TQ, parent=g_q)
for i, (Lq, Wq, ang) in enumerate(TAILS):
    g = (g_ql, g_q, g_qr)[i]
    d = rodrigues(d0, nt, ang)
    Y_ = np.cross(nt, d)
    off = 0.10 if i == 1 else 0.0
    plate(g, f"queue{i}", TQ + d * (Lq / 2 - 0.2) + nt * off, d, Y_, "queue_c" if i == 1 else "queue_s", Lq, Wq, th=0.22, side="b")
    bloc(g, f"queue{i}_n", TQ + d * (Lq * 0.4 - 0.2) + nt * off, (Lq * 0.62, 0.15, 0.32), np.column_stack([d, Y_, nt]), "bar_laiton")

# --- clé de remontage au dos
KEY0 = C0 + V(0, 0.25, 1.80)
g_k = group("cle", KEY0, parent=g_corps)
plate(g_k, "cle_collier", KEY0 + V(0, 0, 0.12), V(1, 0, 0), V(0, 1, 0), "collier", 0.9, 0.9, th=0.2, side="s")
bar(g_k, "cle_tige", KEY0 + V(0, 0, 0.05), KEY0 + V(0, 0, 1.05), 0.16, "bar_acier")
KZ = KEY0 + V(0, 0, 1.30)                     # le panneton : plan qui contient l'axe, lobes de part et d'autre
Rk = np.column_stack([V(0, 1, 0), V(0, 0, 1), V(1, 0, 0)])
plate(g_k, "cle_anneau", KZ, Rk[:, 0], Rk[:, 1], "cle", KEY_W, KEY_H, th=0.26, side="b")
bloc(g_k, "cle_ame", KZ, (0.62, 0.55, 0.36), Rk, "bar_laiton")
bloc(g_k, "cle_barre", KZ, (2.05, 0.2, 0.32), Rk, "bar_laiton")

outliner = [{"name": "body", "origin": [0, 24, 0], "uuid": nuid(), "children": [bone_node(g_elan)]}]


# ------------------------------------------------------------------ animations
# Guide, section 3 : +X = le haut part vers l'arrière ; +Y = le côté droit (+X) avance ; +Z = le côté droit monte.
# Position +Y : monte ; +X : droite du joueur. Le hibou regarde -Z : une rotation +Y de la tête tourne son regard vers -X, donc vers le joueur.
def kf(ch, t, v):
    return {"channel": ch, "data_points": [{"x": str(round(v[0] + 0.0, 3)), "y": str(round(v[1] + 0.0, 3)), "z": str(round(v[2] + 0.0, 3))}], "time": round(t, 4), "interpolation": "linear"}


def servo(tau, w=24.0, z=0.5):
    """Réponse d'un servo à un échelon : arrivée sèche, dépassement (~16 % à z = 0,5), rappel."""
    if tau <= 0:
        return 0.0
    wd = w * math.sqrt(1 - z * z)
    return 1 - math.exp(-z * w * tau) * (math.cos(wd * tau) + z / math.sqrt(1 - z * z) * math.sin(wd * tau))


def paliers(T, seq, v0=0.0, w=24.0, z=0.5):
    """Cibles successives [(t, valeur)] atteintes par paliers de servo. Inclut la fin des paliers de la boucle
    précédente (t + T) : la courbe se referme exactement (à la dérive totale près, cible finale - v0)."""
    def f(t):
        v, prev = v0, v0
        for ti, vi in seq:
            dv = vi - prev
            v += dv * (servo(t - ti, w, z) + servo(t + T - ti, w, z) - 1)
            prev = vi
        return v
    return f


def cliquet(T, n, total=360.0, t0=0.05, w=34.0, z=0.42):
    """Échappement : n tics réguliers par boucle, total degrés (360 x k)."""
    return paliers(T, [(t0 + i * T / n, total * (i + 1) / n) for i in range(n)], 0.0, w, z)


def C(v):
    return lambda t: v


def S(T, k, ph=0.0):
    return lambda t: math.sin(TAU * k * t / T + ph)


def mir(s, x, y, z):
    """Intention écrite pour le côté droit (+X) ; s = -1 à gauche : Y et Z changent de signe."""
    return (x, s * y, s * z)


def anim(name, length, tracks, fps=30, loop="loop"):
    """tracks : {groupe: {canal: f(t) -> (x, y, z)}} ou {canal: ('tour', axe, degrés)} (2 clés linéaires : rotation continue)."""
    n = max(8, int(math.ceil(length * fps)))
    times = [i * length / n for i in range(n + 1)]
    A_ = {}
    for g, chans in tracks.items():
        kfs = []
        for ch, f in chans.items():
            if isinstance(f, tuple) and f[0] == "tour":
                v = [0.0, 0.0, 0.0]
                v[f[1]] = f[2]
                kfs += [kf(ch, 0.0, (0, 0, 0)), kf(ch, length, v)]
                continue
            vals = [f(t) for t in times]
            if loop == "loop":
                drift = [round(b - a) for a, b in zip(vals[0], vals[-1])]       # 360 x k sur la clé, 0 ailleurs
                vals[-1] = tuple(a + d for a, d in zip(vals[0], drift))
            kfs += [kf(ch, t, v) for t, v in zip(times, vals)]
        A_[groups[g]["uuid"]] = {"name": groups[g]["name"], "type": "bone", "keyframes": kfs}
    return {"uuid": nuid(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 30, "selected": name == "idle", "animators": A_}


def glisse(seq, v0=0.0):
    """Déplacement continu (vol) : [(t0, t1, cible)], fondu en douceur de t0 à t1 vers chaque cible."""
    def f(t):
        v, prev = v0, v0
        for t0, t1, vi in seq:
            v = v + (vi - prev) * sm(t, t0, t1)
            prev = vi
        return v
    return f


def glisse3(seq):
    fs = [glisse([(a, b, c[k]) for a, b, c in seq]) for k in range(3)]
    return lambda t: tuple(f(t) for f in fs)


def battements(t0, t1, demi, haut, bas, v_fin=0.0):
    """Battements par tics (gestes seulement : se lisser, s'ébrouer, sursauter, s'étirer)."""
    seq, k, t = [], 0, t0
    while t < t1 - 1e-6:
        seq.append((t, haut if k % 2 == 0 else bas))
        t += demi
        k += 1
    seq.append((t1, v_fin))
    return seq


_rng = np.random.default_rng(1871)


def corrections(t0, t1, base, amp, pas=0.45, fin=None):
    """Petites corrections de gouverne, par crans irréguliers autour de base ; fin : cible après t1."""
    seq, t = [], t0
    while t < t1 - 0.2:
        seq.append((round(t, 2), base + amp * float(_rng.uniform(-1, 1))))
        t += pas * float(_rng.uniform(0.7, 1.3))
    seq.append((t1, base if fin is None else fin))
    return seq


def boucle_corr(T, base, amp, pas=0.45):
    """Corrections périodiques d'une boucle d'état (dernière cible = base = v0)."""
    return corrections(0.1, T - 0.25, base, amp, pas)


def ailes(open_r, open_l=None, fan_r=C(0.0), fan_l=None, fwd=C(0.0)):
    """open_* (degrés) : la pointe monte vers l'extérieur ; fan_* : écart de l'éventail ; fwd : avance des ailes."""
    open_l, fan_l = open_l or open_r, fan_l or fan_r
    tr = {}
    for s, tag, op, fa in ((1, "r", open_r, fan_r), (-1, "l", open_l, fan_l)):
        gs = WINGG[tag]
        tr[gs[0]] = {"rotation": lambda t, s=s, op=op: mir(s, -fwd(t), 0, op(t))}
        for i, g in enumerate(gs[1:]):
            tr[g] = {"rotation": lambda t, i=i, fa=fa: (-fa(t) * (i * 0.5), 0, 0)}
    return tr


def yeux(pup=C(1.0), iris=C(0.0), lid=C(0.0)):
    tr = {}
    for tag, gs in EYEG.items():
        tr[gs["pupille"]] = {"scale": lambda t: (pup(t), pup(t), 1)}
        tr[gs["iris"]] = {"rotation": lambda t: (0, 0, iris(t))}
        tr[gs["paupiere"]] = {"scale": lambda t: (1, 1 + (LID_FERME - 1) * max(0.0, lid(t)), 1)}
    return tr


def vapeur(*bouffees):
    def sc(t):
        k, st = 0.01, 0.0
        for t0, f in bouffees:
            u = t - t0
            if 0 <= u < 0.75:
                g = sm(u, 0.0, 0.10) * (1 - sm(u, 0.40, 0.75))
                k = max(k, 0.01 + 0.99 * g * f)
                st = max(st, sm(u, 0.05, 0.6))
        k = k / VAP_K
        return (k * (1 + 0.25 * st), k * (1 + 0.6 * st), k * (1 + 0.25 * st))

    def pos(t):
        y = 0.0
        for t0, f in bouffees:
            y = max(y, 0.9 * f * sm(t - t0, 0.05, 0.7) * (1 if t - t0 < 0.75 else 0))
        return (0, y, 0)
    return {g_vap: {"scale": sc, "position": pos}}


def soupape(tremble=(), lifts=()):
    def rot(t):
        a = 0.0
        for t0, t1 in tremble:
            a += 6 * bump(t, t0, t0 + 0.05, t1 - 0.05, t1) * math.sin(TAU * 18 * (t - t0))
        return (a, 0, a * 0.6)

    def lift(t):
        return (0, max([0.0] + [0.18 * bump(t, t0 - 0.03, t0, t0 + 0.3, t0 + 0.45) for t0 in lifts]), 0)
    return {g_sp: {"rotation": rot}, g_spc: {"position": lift}}


def R3(fx=C(0.0), fy=C(0.0), fz=C(0.0)):
    return lambda t: (fx(t), fy(t), fz(t))


def rotor(T, vitesse):
    """Supplément de vitesse de l'hélice (tours/s, en plus des 1 tour/s de overlay_mecanisme), intégré puis ramené
    à un nombre entier de tours par boucle (360° x k exact). Renvoie (piste, tours, k_moyen) ; la lumière du foyer suit."""
    dt = 1 / 240
    ts = np.arange(0, T + dt / 2, dt)
    v = np.array([vitesse(t) for t in ts])
    cum = np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2 * dt)])
    k = max(1, int(round(cum[-1])))
    cum = cum * k / cum[-1]
    return (lambda t: (0, -360.0 * float(np.interp(t, ts, cum)), 0)), k


TRAJ = {}       # nom -> (T, elan(t), orbite(t), pos(t)) : test de collision avec le joueur


def etat(name, T, pos, regard, tete, ailes_, yeux_=None, cle_n=8, orbite=None, vap=(), trem=(), queue=None, aigrettes=None,
         vitesse=None, extra=None, fps=30):
    """pos : position de fam_pos (repère de l'orbite) ; orbite : rotation Y autour de l'axe du joueur ;
    vitesse(t) : supplément de vitesse de l'hélice (tours/s) ; la lumière du foyer en suit la forme."""
    tr = {g_pos: {"position": pos}, g_reg: {"rotation": regard}, g_tete: {"rotation": tete}}
    if orbite:
        tr[g_orb] = {"rotation": lambda t: (0, orbite(t), 0)}
    tr.update(ailes_)
    tr.update(yeux_ or yeux())
    if cle_n:
        tr[g_k] = {"rotation": (lambda f: lambda t: (0, 0, -f(t)))(cliquet(T, cle_n))}
    tr.update(vapeur(*vap))
    tr.update(soupape(trem, [t0 for t0, _ in vap]))
    if vitesse:
        piste, _k = rotor(T, vitesse)
        tr[g_rot] = {"rotation": piste}
        tr[g_ctrl_l] = {"position": lambda t: (min(1.2, 0.3 * vitesse(t)), 0, 0)}       # 1 + x : foyer plus vif quand l'hélice force
    if queue:
        tr[g_q] = {"rotation": lambda t: (queue(t), 0, 0)}
    if aigrettes:
        for s, tag in ((1, "r"), (-1, "l")):
            tr[TUFTG[tag]] = {"rotation": lambda t, s=s: mir(s, 0, 0, -aigrettes(t))}
    if extra:
        tr.update(extra)
    TRAJ[name] = (T, lambda t: (0.0, 0.0, 0.0), orbite or C(0.0), pos)
    return anim(name, T, tr, fps=fps)


def molang(an, g, ch, cles):
    a = an["animators"].setdefault(groups[g]["uuid"], {"name": groups[g]["name"], "type": "bone", "keyframes": []})
    a["keyframes"] = [k for k in a["keyframes"] if k["channel"] != ch] + [
        {"channel": ch, "data_points": [{"x": str(x), "y": str(y), "z": str(z)}], "time": round(t, 3), "interpolation": "linear"} for t, (x, y, z) in cles]


# ---------------------------------------------------------------- repères de la promenade
O_ORB = V(0, C0[1], 0)


def orbite_vers(p_from, p_to):
    best = min(np.arange(-180.0, 0.0, 0.05), key=lambda a: np.linalg.norm(rot_matrix(0, a, 0) @ (p_from - O_ORB) - (p_to - O_ORB)))
    return round(float(best), 2)


P_L = V(-C0[0], C0[1], C0[2])
ORB_L = orbite_vers(C0, P_L)
YAW_AV_L = -ORB_L
YAW_JOUEUR_L = -90.0 - ORB_L
LIFT_A, LIFT = (0.6, 3.2, 0.0), (1.8, 6.5, 0.0)

VERS_R = "math.floor(math.clamp((-q.head_y_rotation - 15) / 15, 0, 2))"
VERS_L = "math.floor(math.clamp((q.head_y_rotation - 15) / 15, 0, 2))"
SUIVI_R = ("0", f"{VERS_R} * 20", f"{VERS_R} * 9")
SUIVI_L = ("0", f"-{VERS_L} * 20", f"-{VERS_L} * 9")
ZERO3 = ("0", "0", "0")

# Logique de drone : l'hélice porte l'oiseau. Pour avancer il pique du nez (-X), pour freiner il se cabre (+X), avec un
# dépassement amorti aux arrêts (servo peu amorti). Les ailes, à demi ouvertes, servent de gouvernes (petites corrections,
# inclinées dans les virages), se déploient pour freiner avant le posé, et sont repliées au repos.
SERVO_VOL = dict(w=14.0, z=0.32)

# ---------------------------------------------------------------- idle (24 s)
# 0-11 perché à droite : regarde le joueur par paliers et penche la tête ; suit des yeux un point qui passe (tête par crans,
#   mise au point des iris) ; se retourne pour vérifier sa clé (tête à 180°, comme un hibou) ; se lisse les lames de l'aile ;
#   décharge de vapeur (le seul son de la boucle) et s'ébroue ; se recalibre (iris qui tournent, pupilles par crans, clignement).
# 10,8 l'hélice repart : il tressaille. 11,4-15,9 décolle, passe au-dessus et derrière la tête nez vers le bas, regarde le
#   joueur en passant, se cabre et déploie les ailes pour freiner, se pose sur l'épaule gauche (rebond amorti).
# 16-19,8 se tourne vers le joueur, deux coups de bec près de l'oreille, regarde devant, s'étire (ailes ouvertes par crans).
# 19,9 l'hélice repart, 20,3-23,7 retour par derrière, freinage, posé sur l'épaule droite.
TI = 24.0


def _v_idle(t):
    """Supplément de vitesse de l'hélice (tours/s) : relance, montée, croisière, descente, arrêt au posé."""
    v = 0.0
    for a in (10.8, 19.9):
        v += 4.0 * sm(t, a, a + 0.5) * (1 - sm(t, a + 1.2, a + 1.6)) + 2.6 * sm(t, a + 1.2, a + 1.6) * (1 - sm(t, a + 4.2, a + 4.9))
        v += 1.6 * sm(t, a + 4.2, a + 4.9) * (1 - sm(t, a + 5.0, a + 5.6))
    return v


_pos_idle = glisse3([(11.4, 12.0, LIFT_A), (12.0, 12.8, LIFT), (15.0, 15.9, (0, 0, 0)),
                     (17.6, 17.85, (-0.36, 0, 0)), (18.4, 18.7, (0, 0, 0)),
                     (20.3, 20.9, LIFT_A), (20.9, 21.6, LIFT), (23.0, 23.7, (0, 0, 0))])
_rebond = lambda t: 0.3 * (bump(t, 15.85, 15.95, 16.05, 16.35) + bump(t, 23.65, 23.75, 23.82, 23.98))
_orb_idle = glisse([(12.0, 15.0, ORB_L), (20.9, 23.0, 0.0)])
_corr1 = corrections(11.5, 15.0, 40, 6, fin=78)
_corr2 = corrections(20.4, 23.0, 40, 6, fin=78)
_etire = [(19.0, 30), (19.25, 58), (19.5, 86), (19.85, 40), (20.0, 0)]
_eb = [(8.55, 26), (8.7, 6), (8.85, 20), (9.0, 4), (9.2, 0)]
_lisse = [(6.6, 22), (6.75, 14), (6.9, 24), (7.1, 14), (7.25, 22), (7.6, 0)]
_vol1 = [(11.4, 40)] + _corr1 + [(15.95, 30), (16.1, 12), (16.25, 0)]           # demi-ouvertes, corrections, freinage, repli par tics
_vol2 = [(20.3, 40)] + _corr2 + [(23.75, 30), (23.85, 12), (23.95, 0)]
idle = etat("idle", TI,
            lambda t: tuple(a + b for a, b in zip(_pos_idle(t), (0, _rebond(t), 0))),
            R3(paliers(TI, [(10.9, 5), (11.05, -3), (11.2, 0), (12.0, -14), (14.6, -6), (15.0, 16), (15.9, 0),
                            (17.6, -16), (18.5, 0), (19.95, 4), (20.1, -2), (20.25, 0),
                            (20.9, -14), (22.6, -6), (23.0, 16), (23.7, 0)], **SERVO_VOL),
               paliers(TI, [(11.5, 90), (11.75, 170), (15.9, YAW_AV_L), (16.4, 115), (16.75, YAW_JOUEUR_L), (18.9, YAW_AV_L),
                            (20.35, 100), (20.6, -10), (23.6, 0)], w=24),
               paliers(TI, [(8.55, 9), (8.65, -9), (8.75, 8), (8.85, -7), (8.95, 5), (9.05, -3), (9.15, 0),
                            (10.9, -4), (11.05, 3), (11.2, 0), (12.3, 8), (14.8, 0), (21.2, 8), (22.8, 0)], w=40, z=0.45)),
            R3(paliers(TI, [(3.0, 8), (4.6, 0), (5.3, -18), (5.9, 0), (6.65, -22), (6.8, -8), (6.95, -24), (7.1, -8), (7.25, -24), (7.6, 0),
                            (13.2, -25), (14.0, 0), (17.7, -28), (17.85, -6), (18.0, -28), (18.15, -6), (18.3, -24), (18.5, 0)], w=40),
               paliers(TI, [(0.6, 45), (1.1, 90), (2.3, 45), (2.6, 0),
                            (2.9, -20), (3.2, -32), (3.5, -44), (3.8, -56), (4.1, -66), (4.6, 0),
                            (4.9, 90), (5.15, 150), (5.4, 180), (6.0, 90), (6.25, 0),
                            (6.45, -60), (6.6, -95), (7.5, -45), (7.8, 0),
                            (9.6, 30), (10.1, -30), (10.5, 0),
                            (13.2, 60), (14.0, 0), (19.3, -40), (19.8, 0)]),
               paliers(TI, [(1.5, 12), (1.85, 24), (2.3, 0), (9.7, -10), (10.0, 10), (10.4, 0)])),
            ailes(paliers(TI, _lisse + _eb + _vol1 + _etire + _vol2, w=30),
                  paliers(TI, _eb + _vol1 + _etire + _vol2, w=30),
                  paliers(TI, [(6.6, 20), (7.6, 0), (15.0, 24), (16.1, 0), (19.25, 12), (19.5, 26), (20.0, 0), (23.0, 24), (23.85, 0)], w=30),
                  paliers(TI, [(15.0, 24), (16.1, 0), (19.25, 12), (19.5, 26), (20.0, 0), (23.0, 24), (23.85, 0)], w=30)),
            yeux(paliers(TI, [(1.2, 0.78), (1.6, 0.56), (2.6, 1.0), (3.0, 0.8), (3.5, 0.6), (4.1, 0.75), (4.6, 1.0),
                              (9.6, 0.5), (9.9, 1.25), (10.2, 0.7), (10.5, 1.0), (10.9, 1.3), (11.6, 1.0),
                              (16.8, 0.7), (17.1, 0.5), (18.9, 1.0)], 1.0, w=30),
                 paliers(TI, [(1.2, 20), (1.6, 40), (2.6, 0), (3.2, 20), (3.8, 40), (4.6, 0),
                              (9.6, 40), (9.8, 80), (10.0, 120), (10.5, 0), (16.8, 20), (17.1, 40), (18.9, 0)], w=30, z=0.42),
                 paliers(TI, [(10.2, 0.5), (10.3, 1.0), (10.45, 0.45), (10.55, 0.0), (14.5, 0.5), (14.6, 1.0), (14.75, 0.4), (14.85, 0.0)], w=48, z=0.7)),
            cle_n=48, orbite=_orb_idle, vap=[(8.3, 1.0)], trem=[(7.8, 8.3)], vitesse=_v_idle,
            queue=paliers(TI, [(8.55, -14), (9.2, 0), (11.5, -8), (15.0, 12), (16.0, 0), (20.4, -8), (23.0, 12), (23.8, 0)], w=30),
            aigrettes=paliers(TI, [(8.55, 22), (9.2, 0), (10.85, 26), (11.1, 6), (11.4, 0), (19.95, 18), (20.2, 0)], w=40))
molang(idle, g_suivi, "rotation", [(0.0, SUIVI_R), (4.7, SUIVI_R), (4.8, ZERO3), (6.3, ZERO3), (6.4, SUIVI_R), (11.0, SUIVI_R), (11.2, ZERO3),
                                   (16.1, ZERO3), (16.3, SUIVI_L), (20.0, SUIVI_L), (20.2, ZERO3), (23.8, ZERO3), (23.95, SUIVI_R), (TI, SUIVI_R)])
idle["animators"]["effects"] = {"name": "Effects", "type": "effect", "keyframes": [         # le seul son : la décharge
    {"channel": "sound", "data_points": [{"effect": "block.fire.extinguish", "file": ""}], "time": 8.3}]}

# ---------------------------------------------------------------- états (vol : hélice plus rapide, nez vers le bas, ailes en gouvernes)
TW = 1.6       # marche : il vole à côté de l'épaule, nez un peu vers le bas, regarde le joueur
walk = etat("walk", TW,
            lambda t: (2.5 + 0.2 * S(TW, 1)(t), 3.0 + 0.25 * S(TW, 1, 0.5)(t), 2.0),
            R3(lambda t: -6 + 2.5 * S(TW, 1, 0.3)(t), C(0.0), lambda t: 2.5 * S(TW, 1, 0.6)(t)),
            R3(C(0.0), paliers(TW, [(0.3, 30), (1.1, 0)])),
            ailes(paliers(TW, boucle_corr(TW, 38, 5), 38, w=26), paliers(TW, boucle_corr(TW, 38, 5), 38, w=26), fan_r=C(8.0)),
            vitesse=C(2.0), queue=C(-6.0))

TR = 1.0       # course : il suit, en retrait (inertie de overlay_mecanisme), nettement piqué, ailes rentrées
run = etat("run", TR,
           lambda t: (3.0 + 0.15 * S(TR, 1)(t), 3.5 + 0.2 * S(TR, 1, 0.5)(t), 4.5),
           R3(lambda t: -14 + 3 * S(TR, 1, 0.3)(t), C(0.0), lambda t: 3.0 * S(TR, 1, 0.6)(t)),
           R3(C(10.0)),
           ailes(paliers(TR, boucle_corr(TR, 26, 4, 0.3), 26, w=30), fan_r=C(4.0), fwd=C(10.0)),
           vitesse=C(3.0), queue=C(-12.0))

TS = 3.0       # accroupi : posé, il se fait petit, ailes repliées, tête rentrée
_k = 0.86
sneak = etat("sneak", TS,
             C((0.0, -(1 - _k) * 2.95, 0.0)),
             R3(C(-4.0)),
             R3(C(0.0), paliers(TS, [(0.5, 40), (0.8, 70), (2.2, 35), (2.5, 0)])),
             ailes(C(-3.0)),
             yeux(paliers(TS, [(0.9, 0.6), (2.2, 1.0)], 1.0), paliers(TS, [(0.9, 30), (2.2, 0)]), C(0.4)),
             aigrettes=C(24.0),
             extra={g_corps: {"scale": C((_k, _k, _k))},
                    g_tete: {"rotation": R3(C(0.0), paliers(TS, [(0.5, 40), (0.8, 70), (2.2, 35), (2.5, 0)])), "position": C((0.0, -0.45, 0.0))}})

TF = 2.4       # vol créatif : il plane à côté (stationnaire), réagit au joueur : le regarde, penche la tête
fly = etat("fly", TF,
           lambda t: (3.0 + 0.15 * S(TF, 1)(t), 2.5 + 0.3 * S(TF, 1, -1.2)(t), 0.5),
           R3(lambda t: -6 + 3 * S(TF, 1, 0.4)(t), C(0.0), lambda t: 2.5 * S(TF, 1, 0.3)(t)),
           R3(lambda t: paliers(TF, [(0.6, -8), (1.8, 0)])(t), paliers(TF, [(0.5, 45), (0.8, 75), (1.8, 30), (2.1, 0)]),
              paliers(TF, [(0.9, 12), (1.6, 0)])),
           ailes(paliers(TF, boucle_corr(TF, 42, 6), 42, w=26), paliers(TF, boucle_corr(TF, 42, 6), 42, w=26), fan_r=C(10.0)),
           cle_n=12, vitesse=C(2.6), queue=C(-6.0))

TG = 3.6       # élytres : corps couché ; +X ~70° le remet debout, un peu piqué ; hélice à fond
glide = etat("glide", TG,
             lambda t: (5.0, -2.0 + 0.3 * S(TG, 1)(t), 3.5 + 0.4 * S(TG, 1, 0.8)(t)),
             R3(lambda t: 62 + 3 * S(TG, 1)(t), C(0.0), lambda t: 3 * S(TG, 1, 1.0)(t)),
             R3(lambda t: paliers(TG, [(0.4, -8), (2.6, 0)])(t), paliers(TG, [(1.2, 30), (2.2, 0)])),
             ailes(paliers(TG, boucle_corr(TG, 30, 5), 30, w=24), fan_r=C(6.0), fwd=C(10.0)),
             yeux(C(0.75)), cle_n=12, vitesse=C(4.0), queue=C(-12.0))

TN = 3.2
swim = etat("swim", TN,
            lambda t: (5.0, -1.0 + 0.4 * S(TN, 1)(t), 3.0 + 0.5 * S(TN, 1, 1.2)(t)),
            R3(lambda t: 62 + 5 * S(TN, 1)(t), C(0.0), lambda t: 4 * S(TN, 1, 1.4)(t)),
            R3(lambda t: paliers(TN, [(0.4, -10), (2.0, 0)])(t)),
            ailes(paliers(TN, boucle_corr(TN, 24, 5, 0.6), 24, w=18), fan_r=C(4.0)),
            yeux(C(1.2)), vitesse=C(1.5))

TA = 1.2       # en l'air : il décolle de l'épaule, hélice à fond, cabré, ailes déployées en aérofreins
fall = etat("fall", TA,
            lambda t: (1.5, 2.4 + 0.2 * S(TA, 1)(t), 0.5),
            R3(lambda t: 10 + 2 * S(TA, 1)(t), C(0.0), lambda t: 2 * S(TA, 1, 0.8)(t)),
            R3(C(-12.0)),
            ailes(paliers(TA, boucle_corr(TA, 70, 5, 0.3), 70, w=30), fan_r=C(22.0)),
            yeux(C(1.25)), cle_n=6, vitesse=C(3.5), queue=C(10.0), aigrettes=C(8.0))

TZ = 4.0       # sommeil : perché debout sur la poitrine du joueur couché, paupières qui retombent par crans, clé immobile
sleep = etat("sleep", TZ,
             C((-1.0, -6.0, -2.0 - 2.95 - C0[2])),
             R3(lambda t: -90 - 3 + 1.0 * S(TZ, 1)(t), C(0.0), lambda t: 1.5 * S(TZ, 1, 1.2)(t)),
             R3(paliers(TZ, [(1.2, -6), (2.0, -12), (2.6, -16), (3.2, -20)], -20), C(-10.0), paliers(TZ, [(1.2, 4), (2.6, 8)], 8)),
             ailes(C(-4.0)),
             yeux(C(1.0), C(0.0), paliers(TZ, [(1.2, 0.5), (2.0, 0.72), (2.6, 0.88), (3.2, 1.0)], 1.0, w=30, z=0.6)),
             cle_n=0, queue=C(6.0), aigrettes=C(-8.0),
             extra={g_ctrl_l: {"position": C((-0.5, 0.0, 0.0))}})        # foyer en veille


# ---------------------------------------------------------------- attack, hurt, événements (par-dessus : rotations et positions s'ajoutent)
def once(T, seq, w=26.0, z=0.5):
    def f(t):
        v, prev = 0.0, 0.0
        for ti, vi in seq:
            v += (vi - prev) * servo(t - ti, w, z)
            prev = vi
        return v * (1 - sm(t, T - 0.08, T))
    return f


def ponctuel(name, T, tracks, elan=None, tours=0):
    if elan:
        tracks[g_elan] = {"position": elan}
    if tours:                                   # sursaut de l'hélice (s'ajoute à sa rotation) : tours entiers, départ et arrivée en douceur
        tracks[g_rot] = {"rotation": lambda t: (0, -360.0 * tours * sm(t, 0.0, T), 0)}
    TRAJ[name] = (T, elan or (lambda t: (0.0, 0.0, 0.0)), None, None)
    return anim(name, T, tracks, loop="once")


def deux_ailes(f):
    return {WINGG["r"][0]: {"rotation": lambda t: mir(1, 0, 0, f(t))}, WINGG["l"][0]: {"rotation": lambda t: mir(-1, 0, 0, f(t))}}


# attack : il monte, pique du nez et fonce vers l'avant (ailes rentrées), se cabre ailes déployées pour freiner, revient
TAk = 0.8
attack = ponctuel("attack", TAk, {
    g_snap: {"rotation": lambda t: (once(TAk, [(0.06, -30), (0.34, 18), (0.55, 0)], w=30, z=0.4)(t), 0, 0)},
    g_tete: {"rotation": lambda t: (once(TAk, [(0.06, 14), (0.34, -10), (0.55, 0)], w=34)(t), 0, 0)},
    **deux_ailes(once(TAk, [(0.06, 12), (0.34, 75), (0.6, 0)], w=34)),
}, elan=lambda t: (0.0, 3.6 * sm(t, 0.0, 0.12) * (1 - sm(t, 0.52, 0.78)), -7.0 * sm(t, 0.1, 0.26) * (1 - sm(t, 0.36, 0.54))), tours=2)

# hurt : sursaut ; il s'envole d'un coup, affolé (le seul vrai battement : réflexe), hélice qui s'emballe, puis revient
THu = 1.4
_fuite = lambda t: sm(t, 0.0, 0.18) * (1 - sm(t, 0.75, 1.32))
_hu = once(THu, [(0.0, 1.0), (0.5, 0.0)], w=36, z=0.35)
hurt = ponctuel("hurt", THu, {
    g_snap: {"rotation": lambda t: (14 * _hu(t), 0, 8 * _fuite(t) * math.sin(TAU * 5 * t))},
    g_tete: {"rotation": lambda t: (0, once(THu, [(0.0, 115), (0.4, 0)], w=40, z=0.35)(t), -8 * _hu(t))},
    TUFTG["r"]: {"rotation": lambda t: mir(1, 0, 0, -30 * _hu(t))},
    TUFTG["l"]: {"rotation": lambda t: mir(-1, 0, 0, -30 * _hu(t))},
    g_q: {"rotation": lambda t: (-22 * _hu(t), 0, 0)},
    g_ql: {"rotation": lambda t: (0, -18 * _hu(t), 0)},
    g_qr: {"rotation": lambda t: (0, 18 * _hu(t), 0)},
    **deux_ailes(once(THu, battements(0.0, 0.55, 0.09, 85, 20) + [(0.6, 45), (1.15, 0)], w=60, z=0.45)),
    **{g: {"rotation": (lambda i: lambda t: (-14 * i * _hu(t), 0, 0))(i)} for tag in ("r", "l") for i, g in enumerate(WINGG[tag][1:])},
}, elan=lambda t: (0.0, 5.0 * _fuite(t) + 0.3 * _fuite(t) * math.sin(TAU * 6 * t), 3.5 * _fuite(t)), tours=5)

TJ = 0.6       # saut : il décolle d'un petit coup d'aile
event_jump = ponctuel("event_jump", TJ, {**deux_ailes(once(TJ, [(0.0, 40), (0.15, 10), (0.3, 0)], w=40))},
                      elan=lambda t: (0.0, 1.2 * bump(t, 0.0, 0.15, 0.25, 0.55), 0.0), tours=1)
TL = 0.6       # atterrissage : écrasé puis rebond, ailes en balancier
_sq = once(TL, [(0.0, 1.0), (0.12, -0.45), (0.3, 0.0)], w=40, z=0.4)
event_land = ponctuel("event_land", TL, {
    g_corps: {"scale": lambda t: (1 + 0.08 * _sq(t), 1 - 0.14 * _sq(t), 1 + 0.08 * _sq(t))},
    **deux_ailes(once(TL, [(0.0, 26), (0.2, 0)], w=40)),
}, elan=lambda t: (0.0, 0.5 * bump(t, 0.1, 0.22, 0.3, 0.5), 0.0))
TE = 1.8       # arrivée : il vient de derrière, au-dessus, nez vers le bas, se cabre ailes déployées et se pose
_arr = lambda t: 1 - sm(t, 0.0, 1.3)
event_equip = ponctuel("event_equip", TE, {
    g_snap: {"rotation": lambda t: (once(TE, [(0.0, -14), (1.0, 16), (1.4, 0)], **SERVO_VOL)(t), 0, 0)},
    **deux_ailes(once(TE, [(0.0, 40), (1.0, 78), (1.45, 30), (1.55, 12), (1.65, 0)], w=30)),
}, elan=lambda t: (6.0 * _arr(t), 10.0 * _arr(t) + 0.4 * bump(t, 1.3, 1.4, 1.5, 1.75), 7.0 * _arr(t)), tours=6)

# ---------------------------------------------------------------- couche permanente : hélice au ralenti, inertie, virages, flottement par joueur
TO = 4.0       # période du flottement (q.life_time * 90 : 4 s) ; hélice : 4 tours par boucle (1 tour/s, ralenti)
overlay = anim("overlay_mecanisme", TO, {g_rot: {"rotation": ("tour", 1, -360.0 * 4)}})
molang(overlay, g_inert, "position", [(0.0, ("0", "0.15 + 0.15 * math.sin(q.life_time * 90 + q.instance_seed * 360)",
                                             "v.retard = math.lerp(v.retard, math.clamp((q.ground_speed - 2) * 1.2, 0, 5), 0.05); v.retard"))])
molang(overlay, g_inert, "rotation", [(0.0, ("0", "v.lag = math.lerp(v.lag, math.clamp(-q.yaw_speed * 0.06, -14, 14), 0.06); v.lag", "0"))])
molang(overlay, g_vir, "rotation", [(0.0, ("v.tan = math.lerp(v.tan, math.clamp((q.ground_speed - 2) * -2.5, -10, 0), 0.06); v.tan", "0",
                                           "v.vir = math.lerp(v.vir, math.clamp(q.yaw_speed * 0.08, -18, 18), 0.1); v.vir"))])


# ---------------------------------------------------------------- test : jamais dans le joueur, jamais devant le visage
def centre(T_, elan, orb, pos, t):
    return np.asarray(elan(t)) + O_ORB + rot_matrix(0, orb(t), 0) @ (C0 - O_ORB + np.asarray(pos(t)))


def collisions(c):
    """c : centre du corps (repère du torse). Le hibou : capsule verticale de rayon 1,95, du carénage (-2,95) aux aigrettes (+4)."""
    bas, haut, r = c[1] - 2.95, c[1] + 4.0, 1.95
    err = []
    if haut > 24 and bas < 33 and math.hypot(c[0], c[2]) < 4 * math.sqrt(2) + r:      # tête du joueur, tournée dans tous les sens
        err.append("tête")
    if bas < 23.9 and haut > 12 and abs(c[0]) < 8 + r and abs(c[2]) < 2 + r:          # torse et bras
        err.append("corps")
    if haut > 22 and bas < 36 and abs(c[0]) < 4 + r + 0.5 and c[2] < -3.5:            # devant le visage
        err.append("visage")
    return err


_debout = ["idle", "walk", "run", "sneak", "fly", "fall"]
_fails, _marge = [], 1e9
for nom in _debout:
    T_, el, orb, pos = TRAJ[nom]
    for t in np.arange(0, T_, 0.05):
        c = centre(T_, el, orb, pos, t)
        if nom == "sneak":
            continue                                    # perché, tassé : même position que le perchoir
        _marge = min(_marge, math.hypot(c[0], c[2]) - 4 * math.sqrt(2) - 1.95 if c[1] + 4 > 24 and c[1] - 2.95 < 33 else 1e9)
        _fails += [(nom, round(t, 2), e) for e in collisions(c)]
        for ev in ("attack", "hurt", "event_jump", "event_land", "event_equip"):     # superposés à n'importe quel instant de l'état
            T2, el2, _, _ = TRAJ[ev]
            for t2 in np.arange(0, T2, 0.1):
                if ev == "event_equip" and t > 1.0:
                    continue                            # l'arrivée se joue quand la pièce apparaît : l'état commence en même temps
                c2 = c + np.asarray(el2(t2))
                _fails += [(f"{nom}+{ev}", round(t, 2), e) for e in collisions(c2)]
_fails = sorted(set(_fails))
assert not _fails, f"collisions avec le joueur : {_fails[:12]} ({len(_fails)})"
print(f"test de collision : aucune ; marge minimale à la tête {_marge:.2f} px")

ANIMS = [idle, walk, run, sneak, fly, glide, swim, fall, sleep, attack, hurt, overlay, event_jump, event_land, event_equip]

assert 90 <= len(elements) <= 150, f"budget : {len(elements)} cubes"
textures = [{"name": f"{NOM}.png", "uv_width": TEX, "uv_height": TEX, "source": tex_b64}]
if AVEC_E:
    textures.append({"name": f"{NOM}_e.png", "uv_width": TEX, "uv_height": TEX, "source": tex_e_b64})
model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": NOM, "resolution": {"width": TEX, "height": TEX},
         "elements": elements, "outliner": outliner, "textures": textures, "animations": ANIMS}
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
# Particules Minecraft mal placées en jeu (bug du mod, 2026-11-04) : remplacées par une vapeur modélisée.
from particules import remplacer_emit_mc
remplacer_emit_mc(model, {"white_smoke": "vapeur", "white_ash": "souffle"})
from sons import limiter_sons
from ambiance import ajouter_ambiance
limiter_sons(model)
ajouter_ambiance(model)
os.makedirs(".build", exist_ok=True)
out = f".build/{NOM}_brut.bbmodel"
with open(out, "w") as fh:
    json.dump(model, fh, separators=(",", ":"))


def depth(n, d=1):
    return max([depth(c, d + 1) for c in n.get("children", []) if isinstance(c, dict)] + [d])


print(len(elements), "cubes ;", len(groups) + 1, "groupes ; profondeur", max(depth(n) for n in outliner), ";", len(ANIMS), "anims ;",
      sum(len(b["keyframes"]) for a in ANIMS for b in a["animators"].values()), "keyframes ;", os.path.getsize(out) // 1024, "Ko ;",
      f"densité {DENS:.1f} texels/px")
